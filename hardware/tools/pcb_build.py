"""Placement, routing and zone helpers over the KiCad 10 pcbnew API, plus Freerouting.

    import pcb_build as pb                 # run under KPY (/usr/bin/python3.12 on Linux)
    brd = pb.Board("hardware/OpenAIO-Whoop.kicad_pcb")       # after sync_pcb.py
    brd.outline_rect(100, 100, 125.5, 125.5, r=1.0)
    brd.place("U2", 110, 104)                       # front
    brd.place("U1", 104.5, 108.5, side="B")         # back (flipped)
    x, y = brd.pad_xy("U2", "21")
    brd.track("/SWDIO", "F.Cu", (x, y), (112.9, y), width=0.1)
    brd.via("/SWDIO", 112.9, y)                     # through via, netclass size
    brd.zone("GND", "In1.Cu", brd.outline_points())
    brd.fill_zones()
    brd.save()
    print(pb.drc(brd.path))                         # kicad-cli DRC + schematic parity summary

All coordinates are mm in board axes (+y down). Placement is idempotent: place()
sets absolute position, rotation and side, so re-running a layout script gives
the same board. clear_tracks() removes routing (keeps zones) before re-routing.
Net names are the netlist's ("/SWDIO", "/MCU/NRST", "GND").

KiCad 10.0.6 pitfalls handled here (each one cost a crash or a wrong board):
  * remove items with BOARD.Delete(); BOARD.Remove() orphans the SWIG proxy
    and later calls return unwrapped SwigPyObjects,
  * a footprint must be on the board before Flip() (orphan flip segfaults),
  * NETINFO_ITEM.GetNetClass() is unwrapped; use Board.netclass(name).
Close KiCad before writing a board. render() and drc() shell out to kicad-cli.

Freerouting: see freeroute.py (CLI) for the full, checked round trip;
export_dsn(protect_existing=True), freeroute(), import_ses(), enforce_min_width().
"""
import json
import math
import os
import subprocess


def _quiet_import():
    saved, null = os.dup(2), os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 2)
    try:
        import pcbnew
    finally:
        os.dup2(saved, 2)
        os.close(null)
        os.close(saved)
    return pcbnew


P = _quiet_import()
mm = P.FromMM
KICAD_CLI = os.environ.get("KICAD_CLI", "kicad-cli")


def V(x, y):
    return P.VECTOR2I(mm(x), mm(y))


def xy(v):
    return (round(P.ToMM(v.x), 4), round(P.ToMM(v.y), 4))


class Board:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.b = P.LoadBoard(self.path)
        self.ds = self.b.GetDesignSettings()

    # -- lookup ----------------------------------------------------------
    def layer(self, name):
        lid = self.b.GetLayerID(name)
        if lid < 0:
            raise KeyError("no layer %r" % name)
        return lid

    def fp(self, ref):
        f = self.b.FindFootprintByReference(ref)
        if f is None:
            raise KeyError("no footprint %s" % ref)
        return f

    def pad(self, ref, num):
        pads = [p for p in self.fp(ref).Pads() if p.GetNumber() == str(num)]
        if not pads:
            raise KeyError("%s has no pad %s" % (ref, num))
        return pads[0]

    def pad_xy(self, ref, num):
        return xy(self.pad(ref, num).GetPosition())

    def netclass(self, name):
        """Effective NETCLASS of a net (NETINFO_ITEM.GetNetClass() is an unwrapped pointer in 10.0)."""
        return self.ds.m_NetSettings.GetEffectiveNetClass(name)

    def net(self, name):
        n = self.b.FindNet(name)
        if n is None:
            raise KeyError("no net %r (run sync_pcb.py first)" % name)
        return n

    # -- outline ---------------------------------------------------------
    def clear_layer(self, name):
        lid = self.layer(name)
        for d in list(self.b.GetDrawings()):
            if d.GetLayer() == lid:
                self.b.Delete(d)          # Delete, not Remove: Remove orphans the SWIG proxy

    def outline_rect(self, x0, y0, x1, y1, r=0.0, width=0.05):
        """Replace Edge.Cuts with a rectangle, optionally with corner radius r."""
        self.clear_layer("Edge.Cuts")
        self._outline = (x0, y0, x1, y1)
        segs = [((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)),
                ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))]
        for a, b in segs:
            self._shape(P.SHAPE_T_SEGMENT, a, b, width)
        if r:
            for cx, cy, sx, sy in ((x0 + r, y0 + r, x0, y0 + r), (x1 - r, y0 + r, x1 - r, y0),
                                   (x1 - r, y1 - r, x1, y1 - r), (x0 + r, y1 - r, x0 + r, y1)):
                s = P.PCB_SHAPE(self.b)
                s.SetShape(P.SHAPE_T_ARC)
                s.SetLayer(P.Edge_Cuts)
                s.SetWidth(mm(width))
                s.SetCenter(V(cx, cy))
                s.SetStart(V(sx, sy))
                s.SetArcAngleAndEnd(P.EDA_ANGLE(90, P.DEGREES_T), True)
                self.b.Add(s)

    def _shape(self, kind, a, b, width, layer=None):
        s = P.PCB_SHAPE(self.b)
        s.SetShape(kind)
        s.SetLayer(layer if layer is not None else P.Edge_Cuts)
        s.SetStart(V(*a))
        s.SetEnd(V(*b))
        s.SetWidth(mm(width))
        self.b.Add(s)
        return s

    def outline_points(self, inset=0.0):
        x0, y0, x1, y1 = getattr(self, "_outline", None) or self._edge_bbox()
        return [(x0 + inset, y0 + inset), (x1 - inset, y0 + inset), (x1 - inset, y1 - inset), (x0 + inset, y1 - inset)]

    def _edge_bbox(self):
        bb = self.b.GetBoardEdgesBoundingBox()
        return (P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop()), P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom()))

    # -- placement -------------------------------------------------------
    def place(self, ref, x, y, rot=0.0, side="F", lock=False):
        """Absolute placement; idempotent. side 'B' flips the footprint to the back."""
        f = self.fp(ref)
        want_back = side.upper().startswith("B")
        if f.IsFlipped() != want_back:
            f.Flip(f.GetPosition(), P.FLIP_DIRECTION_TOP_BOTTOM)   # footprint must be on the board
        f.SetPosition(V(x, y))
        f.SetOrientationDegrees(rot)
        f.SetLocked(lock)
        return f

    # -- copper ----------------------------------------------------------
    def track(self, net, layer, *pts, width=None):
        """Track segments through pts on layer; width defaults to the netclass width."""
        n = self.net(net)
        w = mm(width) if width else self.netclass(net).GetTrackWidth()
        lid = self.layer(layer)
        out = []
        for a, b in zip(pts, pts[1:]):
            t = P.PCB_TRACK(self.b)
            t.SetStart(V(*a))
            t.SetEnd(V(*b))
            t.SetWidth(w)
            t.SetLayer(lid)
            t.SetNet(n)
            self.b.Add(t)
            out.append(t)
        return out

    def via(self, net, x, y, size=None, drill=None, kind="through", top="F.Cu", bottom="B.Cu"):
        """Via; kind through|blind|micro. Size/drill default to the netclass."""
        n = self.net(net)
        nc = self.netclass(net)
        v = P.PCB_VIA(self.b)
        v.SetPosition(V(x, y))
        v.SetViaType({"through": P.VIATYPE_THROUGH, "blind": P.VIATYPE_BLIND,
                      "micro": P.VIATYPE_MICROVIA}[kind])
        v.SetLayerPair(self.layer(top), self.layer(bottom))
        if kind == "micro":
            v.SetWidth(mm(size) if size else nc.GetuViaDiameter())
            v.SetDrill(mm(drill) if drill else nc.GetuViaDrill())
        else:
            v.SetWidth(mm(size) if size else nc.GetViaDiameter())
            v.SetDrill(mm(drill) if drill else nc.GetViaDrill())
        v.SetNet(n)
        self.b.Add(v)
        return v

    def route_pads(self, net, layer, a, b, width=None):
        """Track from pad a=(ref,num) to pad b, as straight or 45-degree-then-straight."""
        p1, p2 = self.pad_xy(*a), self.pad_xy(*b)
        return self.track(net, layer, *dogleg(p1, p2), width=width)

    def zone(self, net, layers, pts, name=None, priority=0, clearance=None, min_width=None,
             connect="thermal", thermal_gap=None, spoke=None):
        """Copper zone on one layer name or a list of layer names."""
        z = P.ZONE(self.b)
        if isinstance(layers, str):
            layers = [layers]
        ls = P.LSET()
        for l in layers:
            ls.AddLayer(self.layer(l))
        z.SetLayerSet(ls)
        z.SetNet(self.net(net))
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(mm(x), mm(y))
        z.SetAssignedPriority(priority)
        if name:
            z.SetZoneName(name)
        if clearance is not None:
            z.SetLocalClearance(mm(clearance))
        if min_width is not None:
            z.SetMinThickness(mm(min_width))
        z.SetPadConnection({"thermal": P.ZONE_CONNECTION_THERMAL, "solid": P.ZONE_CONNECTION_FULL,
                            "none": P.ZONE_CONNECTION_NONE}[connect])
        if thermal_gap is not None:
            z.SetThermalReliefGap(mm(thermal_gap))
        if spoke is not None:
            z.SetThermalReliefSpokeWidth(mm(spoke))
        self.b.Add(z)
        return z

    def fill_zones(self):
        self.b.BuildConnectivity()
        P.ZONE_FILLER(self.b).Fill(self.b.Zones())

    def clear_tracks(self):
        for t in list(self.b.GetTracks()):
            self.b.Delete(t)

    def clear_zones(self):
        for z in list(self.b.Zones()):
            self.b.Delete(z)

    # -- I/O -------------------------------------------------------------
    def save(self, path=None):
        self.b.BuildConnectivity()
        P.SaveBoard(path or self.path, self.b)

    def set_layer_type(self, name, kind):
        """kind: signal|power|mixed|jumper. Plane layers set to 'power' are exported to the
        Specctra DSN as power layers, so Freerouting keeps signals off them."""
        lt = {"signal": P.LT_SIGNAL, "power": P.LT_POWER, "mixed": P.LT_MIXED, "jumper": P.LT_JUMPER}[kind]
        self.b.SetLayerType(self.layer(name), lt)

    def export_dsn(self, path, protect_existing=False):
        """Specctra DSN for Freerouting. KiCad 10 exports every track and via as (type route),
        locked or not; protect_existing=True rewrites them to (type protect) so the router
        keeps the hand routing and only adds to it."""
        if not P.ExportSpecctraDSN(self.b, path):
            raise RuntimeError("ExportSpecctraDSN failed")
        if protect_existing:
            text = open(path, encoding="utf-8").read()
            head, sep, wiring = text.partition("(wiring")
            with open(path, "w", encoding="utf-8") as f:
                f.write(head + sep + wiring.replace("(type route)", "(type protect)"))

    def import_ses(self, path):
        if not P.ImportSpecctraSES(self.b, path):
            raise RuntimeError("ImportSpecctraSES failed")

    def enforce_min_width(self):
        """Widen tracks narrower than their netclass width (Freerouting necks some down). Returns count."""
        n = 0
        for t in self.b.GetTracks():
            if t.GetClass() != "PCB_TRACK":
                continue
            w = self.netclass(t.GetNetname()).GetTrackWidth()
            if t.GetWidth() < w:
                t.SetWidth(w)
                n += 1
        return n

    def unrouted(self):
        """Number of unrouted connections according to pcbnew's ratsnest."""
        self.b.BuildConnectivity()
        return self.b.GetConnectivity().GetUnconnectedCount(False)


def dogleg(p1, p2):
    """Points for a 45-degree-then-straight route from p1 to p2."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6:
        return [p1, p2]
    d = min(abs(dx), abs(dy))
    mid = (p1[0] + math.copysign(d, dx), p1[1] + math.copysign(d, dy))
    return [p1, mid, p2]


def drc(board, out_json=None, parity=True, refill=False):
    """kicad-cli DRC -> dict(errors, warnings, unconnected, parity, by_type, report)."""
    out_json = out_json or os.path.splitext(board)[0] + "-drc.json"
    cmd = [KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", out_json]
    if parity:
        cmd.append("--schematic-parity")
    if refill:
        cmd += ["--refill-zones", "--save-board"]
    subprocess.run(cmd + [board], capture_output=True, text=True)
    d = json.load(open(out_json))
    by = {}
    for key in ("violations", "unconnected_items", "schematic_parity"):
        for v in d.get(key, []):
            k = (v.get("severity", "?"), v["type"])
            by[k] = by.get(k, 0) + 1
    viol = d.get("violations", [])
    return {"errors": sum(1 for v in viol if v.get("severity") == "error"),
            "warnings": sum(1 for v in viol if v.get("severity") == "warning"),
            "unconnected": len(d.get("unconnected_items", [])),
            "parity": len(d.get("schematic_parity", [])),
            "by_type": by, "report": d}


def find_java(min_version=25):
    """Newest JVM at least min_version (Freerouting 2.5 needs 25; 2.1-2.3 run on 21)."""
    import glob
    import re
    best = None
    for j in glob.glob("/usr/lib/jvm/*/bin/java") + glob.glob("/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java"):
        m = re.search(r"(?:java-|jdk-?)(?:1\.)?(\d+)", j)
        if m and int(m.group(1)) >= min_version and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), j)
    return best[1] if best else "java"


def freeroute(jar, dsn, ses, passes=20, timeout=600, threads=1, extra=(), java=None,
              hole_clearance=None, neckdown=False):
    """Run Freerouting headless. Returns the CompletedProcess; raises if no SES appears."""
    if os.path.exists(ses):
        os.remove(ses)
    cmd = [java or find_java(), "-Djava.awt.headless=true", "-jar", jar, "-de", dsn, "-do", ses,
           "-mp", str(passes), "-mt", str(threads), "--gui.enabled=false"]
    if hole_clearance is not None:      # DSN has no hole-to-copper rule; KiCad DRC checks it
        cmd.append("--router.hole_clearance_um=%d" % round(hole_clearance * 1000))
    if not neckdown:                    # neck-down makes tracks thinner than the netclass minimum
        cmd.append("--router.automatic_neckdown=false")
    cmd += list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if not os.path.exists(ses):
        raise RuntimeError("freerouting produced no SES:\n" + r.stdout[-3000:] + r.stderr[-3000:])
    return r


def render(board, out_png, side="top", width=1600, height=1200, extra=()):
    """kicad-cli 3D render to PNG (side: top|bottom|left|right|front|back)."""
    cmd = [KICAD_CLI, "pcb", "render", "--side", side, "--width", str(width), "--height", str(height),
           "-o", out_png] + list(extra) + [board]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stdout + r.stderr)
    return out_png
