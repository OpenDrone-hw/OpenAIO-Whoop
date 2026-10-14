"""Convert vias placed while routing into buildable HDI 1+6+1 stacks.

Run with KiCad closed, using KiCad's bundled Python:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
      hardware/tools/hdi_via_pass.py hardware/<board>.kicad_pcb [--allow-through] [--dry-run]

A via is kept when it is a microvia F.Cu-In1.Cu or In6.Cu-B.Cu at the net class microvia size,
a buried via In1.Cu-In6.Cu, or (with --allow-through) a through via. A via that already spans
F.Cu-In1.Cu or In6.Cu-B.Cu (a mechanical blind via from Option+V, or a microvia at the wrong
size) becomes a microvia in place. Every other via is replaced at the same position by
the smallest stack that joins the layers its tracks, pads and zones use: microvia F.Cu-In1.Cu,
buried In1.Cu-In6.Cu, microvia In6.Cu-B.Cu. Only copper on a layer the via spans counts. Sizes come from the board's net class
(read from the .kicad_pro, microvia and via size; a larger routed land is kept). Where the new stack is closer than the copper clearance to other-net
copper, it is moved up to 0.05 mm together with its track ends; larger conflicts are listed
and left for the owner. A stitching microvia (into its own net's L2/L7 plane, no track attached, not the
last via of a pad) that then sits within copper clearance or different-net hole spacing of
another net's via or track on a shared layer is removed. Zones are refilled. The script prints a report and saves the board unless --dry-run.
"""
import json
import math
import os
import sys


def quiet_import():
    saved, null = os.dup(2), os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 2)
    try:
        import pcbnew
        return pcbnew
    finally:
        os.dup2(saved, 2)
        os.close(saved)
        os.close(null)


pcbnew = quiet_import()
F, B, I1, I6 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In6_Cu
INNER = {pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.In5_Cu}
MAX_NUDGE = pcbnew.FromMM(0.05)
CLEARANCE = pcbnew.FromMM(0.09)
HOLE_GAP = pcbnew.FromMM(0.30)


def legal(v, allow_through, micro):
    t, top, bot = v.GetViaType(), v.TopLayer(), v.BottomLayer()
    if t == pcbnew.VIATYPE_MICROVIA:
        return (top, bot) in ((F, I1), (I6, B)) and v.GetWidth(top) >= micro[0] and v.GetDrillValue() == micro[1]
    if t == pcbnew.VIATYPE_BURIED:
        return (top, bot) == (I1, I6)
    if t == pcbnew.VIATYPE_THROUGH:
        return allow_through
    return False


def used_layers(board, v, tracks):
    # Copper overlap counts as a connection, as in KiCad's connectivity: a track end or body, a pad
    # edge or a zone fill touching the via land on a layer the via spans.
    p, r, layers = v.GetPosition(), v.GetWidth(v.TopLayer()) // 2, set()
    for t in tracks:
        if t.GetNetCode() == v.GetNetCode() and v.IsOnLayer(t.GetLayer()) and seg_dist(p, t.GetStart(), t.GetEnd()) <= r + t.GetWidth() / 2:
            layers.add(t.GetLayer())
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == v.GetNetCode() and pad.HitTest(p, int(r)):
                layers |= {l for l in (F, B) if pad.IsOnLayer(l) and v.IsOnLayer(l)}
    for z in board.Zones():
        if z.GetNetCode() == v.GetNetCode() and not z.GetIsRuleArea():
            layers |= {l for l in z.GetLayerSet().CuStack() if v.IsOnLayer(l) and z.HitTestFilledArea(l, p, int(r))}
    span = {v.TopLayer(), v.BottomLayer()}
    if not layers - {F, B}:
        layers |= span & INNER  # a via ending on an inner layer was placed to route there next
    return layers


def plan(layers):
    parts = []
    if F in layers:
        parts.append("micro_top")
    if layers & INNER or (F in layers and B in layers):
        parts.append("buried")
    if B in layers:
        parts.append("micro_bot")
    return parts or ["buried"]


def nearest_gap(board, pos, net, radius, layers):
    worst = None
    for t in board.GetTracks():
        if t.GetNetCode() == net or t.GetClass() == "PCB_VIA":
            continue
        if t.GetLayer() not in layers:
            continue
        a, b = t.GetStart(), t.GetEnd()
        dx, dy = b.x - a.x, b.y - a.y
        L = dx * dx + dy * dy
        u = max(0.0, min(1.0, ((pos.x - a.x) * dx + (pos.y - a.y) * dy) / L)) if L else 0.0
        nx, ny = a.x + u * dx, a.y + u * dy
        gap = math.dist((nx, ny), (pos.x, pos.y)) - radius - t.GetWidth() / 2
        if worst is None or gap < worst[0]:
            worst = (gap, nx, ny, t)
    return worst


def shared(a, b):
    return any(a.IsOnLayer(l) and b.IsOnLayer(l) for l in (F, I1, *sorted(INNER), I6, B))


def seg_dist(p, a, b):
    dx, dy = b.x - a.x, b.y - a.y
    L = dx * dx + dy * dy
    u = max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / L)) if L else 0.0
    return math.dist((a.x + u * dx, a.y + u * dy), (p.x, p.y))


def clear_stitching(board):
    """Remove track-free vias that collide with another net's via or track."""
    items = list(board.GetTracks())
    vias = [t for t in items if t.GetClass() == "PCB_VIA"]
    tracks = [t for t in items if t.GetClass() != "PCB_VIA"]
    planes = {(z.GetNetCode(), l) for z in board.Zones() if not z.GetIsRuleArea() for l in (I1, I6) if z.IsOnLayer(l)}
    pads = [pad for fp in board.GetFootprints() for pad in fp.Pads()]
    def on_pad(v):
        r = int(v.GetWidth(v.TopLayer()) // 2)
        return [pad for pad in pads if pad.GetNetCode() == v.GetNetCode() and pad.HitTest(v.GetPosition(), r)]
    def stitch(v):
        # A microvia into its own net's L2/L7 plane, with no track attached.
        r = v.GetWidth(v.TopLayer()) / 2
        inner = I1 if v.TopLayer() == F else I6
        if v.GetViaType() != pcbnew.VIATYPE_MICROVIA or (v.GetNetCode(), inner) not in planes:
            return False
        return not any(seg_dist(v.GetPosition(), t.GetStart(), t.GetEnd()) <= r + t.GetWidth() / 2
                       for t in tracks if t.GetNetCode() == v.GetNetCode() and v.IsOnLayer(t.GetLayer()))
    def last_on_pad(v):
        # Never strip the only via of a pad.
        return any(sum(1 for o in vias if id(o) not in gone and o.GetNetCode() == v.GetNetCode()
                       and pad.HitTest(o.GetPosition(), int(o.GetWidth(o.TopLayer()) // 2))) <= 1 for pad in on_pad(v))
    gone = set()
    for v in vias:
        if not stitch(v):
            continue
        p, r = v.GetPosition(), v.GetWidth(v.TopLayer()) / 2
        hit = False
        for o in vias:
            if o is v or id(o) in gone or o.GetNetCode() == v.GetNetCode() or not shared(v, o):
                continue
            d = (o.GetPosition() - p).EuclideanNorm()
            if d < r + o.GetWidth(o.TopLayer()) / 2 + CLEARANCE or d < (v.GetDrillValue() + o.GetDrillValue()) / 2 + HOLE_GAP:
                hit = True
                break
        if not hit:
            for t in tracks:
                if t.GetNetCode() != v.GetNetCode() and v.IsOnLayer(t.GetLayer()) and seg_dist(p, t.GetStart(), t.GetEnd()) < r + t.GetWidth() / 2 + CLEARANCE:
                    hit = True
                    break
        if hit and not last_on_pad(v):
            gone.add(id(v))
            board.Remove(v)
    return len(gone)


def main():
    args = sys.argv[1:]
    path = [a for a in args if not a.startswith("--")][0]
    allow_through, dry = "--allow-through" in args, "--dry-run" in args
    board = pcbnew.LoadBoard(path)
    # KiCad 10 Python does not wrap NETCLASS, so via sizes come from the project file.
    pro = json.load(open(os.path.splitext(path)[0] + ".kicad_pro"))
    classes = {c["name"]: c for c in pro["net_settings"]["classes"]}
    tracks = [t for t in board.GetTracks() if t.GetClass() != "PCB_VIA"]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    def sizes(v):
        cls = classes.get(v.GetNetClassName(), classes["Default"])
        return ((pcbnew.FromMM(cls["microvia_diameter"]), pcbnew.FromMM(cls["microvia_drill"])),
                (pcbnew.FromMM(cls["via_diameter"]), pcbnew.FromMM(cls["via_drill"])))
    bad = [v for v in vias if not legal(v, allow_through, sizes(v)[0])]
    print(f"{len(vias)} vias, {len(bad)} to convert")
    left, retyped = [], 0
    for v in bad:
        pos, net = v.GetPosition(), v.GetNet()
        micro, mech = sizes(v)
        # Keep the routed land when it is larger, so overlap connections made while routing survive.
        micro = (max(micro[0], v.GetWidth(v.TopLayer())), micro[1])
        mech = (max(mech[0], v.GetWidth(v.TopLayer())), mech[1])
        if (v.TopLayer(), v.BottomLayer()) in ((F, I1), (I6, B)):
            v.SetViaType(pcbnew.VIATYPE_MICROVIA)
            v.SetWidth(micro[0])
            v.SetDrill(micro[1])
            retyped += 1
            continue
        parts = plan(used_layers(board, v, tracks))
        new = []
        for p in parts:
            n = pcbnew.PCB_VIA(board)
            board.Add(n)
            n.SetPosition(pos)
            n.SetNet(net)
            if p == "buried":
                n.SetViaType(pcbnew.VIATYPE_BURIED)
                n.SetLayerPair(I1, I6)
                n.SetWidth(mech[0])
                n.SetDrill(mech[1])
            else:
                n.SetViaType(pcbnew.VIATYPE_MICROVIA)
                n.SetLayerPair(*((F, I1) if p == "micro_top" else (I6, B)))
                n.SetWidth(micro[0])
                n.SetDrill(micro[1])
            new.append(n)
        label = f"{v.GetNetname()} {board.GetLayerName(v.TopLayer())}-{board.GetLayerName(v.BottomLayer())}"
        board.Remove(v)
        if "buried" in parts:
            g = nearest_gap(board, pos, net.GetNetCode(), mech[0] / 2, INNER | {I1, I6})
            if g and g[0] < CLEARANCE:
                need = CLEARANCE - g[0] + pcbnew.FromMM(0.005)
                if need <= MAX_NUDGE:
                    d = math.dist((g[1], g[2]), (pos.x, pos.y)) or 1
                    newp = pcbnew.VECTOR2I(int(pos.x + (pos.x - g[1]) / d * need), int(pos.y + (pos.y - g[2]) / d * need))
                    for n in new:
                        n.SetPosition(newp)
                    for t in tracks:
                        if t.GetNetCode() == net.GetNetCode():
                            if (t.GetStart() - pos).EuclideanNorm() < 10:
                                t.SetStart(newp)
                            if (t.GetEnd() - pos).EuclideanNorm() < 10:
                                t.SetEnd(newp)
                    label += f" (moved {pcbnew.ToMM(need):.3f} mm)"
                else:
                    left.append(f"{label}: buried pad {pcbnew.ToMM(g[0]):.3f} mm from {g[3].GetNetname()} on {board.GetLayerName(g[3].GetLayer())}")
        print(f"  {label} -> {' + '.join(parts)}")
    print(f"{retyped} retyped in place to microvias")
    print(f"{clear_stitching(board)} stitching vias removed for clashing with another net")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    for item in left:
        print("OWNER:", item)
    if not dry:
        pcbnew.SaveBoard(path, board)
        print("saved")


if __name__ == "__main__":
    main()
