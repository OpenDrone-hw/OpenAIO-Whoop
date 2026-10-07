#!/usr/bin/env python3
"""Footprint against the datasheet land pattern.

    $KPY hardware/tools/check_footprint.py SPEC.json [FOOTPRINT] [--project DIR]
                                           [--tol 0.02] [--crtyd-tol 0.01] [--silk-pin1-ok]
                                           [--json] [-v]

Runs under KiCad's Python (KPY, see AGENTS.md). Read-only: nothing is saved.

FOOTPRINT is a .kicad_mod path or Lib:Name. Lib:Name resolves through the
project fp-lib-table (--project, default: the hardware/ directory above this
script), then the user's global fp-lib-table, then $KICAD10_FOOTPRINT_DIR.
Without FOOTPRINT the spec's "footprint" field is used.

Spec: JSON, millimetres, TOP view, origin at the package centre, KiCad axes
(+x right, +y DOWN). Copy the numbers from the datasheet's land-pattern table.

  {
    "footprint": "OpenDrone:QFN-20_...",          Lib:Name or .kicad_mod path
    "datasheet": "file/url, page, table",          required: where the numbers come from
    "derivation": "...",                           optional: how numbers were derived when the
                                                   datasheet gives no land pattern
    "pads": [ {"number": "1", "x": -1.25, "y": -1.25, "w": 0.30, "h": 0.30,
               "shape": "rect|roundrect|oval|circle|custom", "rot": 0},
              {"number": "3", "shape": "custom",   custom land = union of rectangles
               "rects": [{"x": .., "y": .., "w": .., "h": ..}, ...]} ],
    "removed_nc": [{"number": "7", "reason": "NC (DS table 6.1), trimmed for density, D21"}],
    "exposed": ["21"],                             optional; else auto (>= 0.5 mm2 and >= 3x median pad)
    "paste": {"ratio_min": 0.50, "ratio_max": 0.80, "min_windows": 2},
    "body": {"w": 3.0, "h": 3.0, "x": 0, "y": 0},
    "courtyard_margin": 0.10,
    "pin1": "1",
    "y_axis": "down", "view": "top", "frame_rot": 0   optional: spec y up / bottom view (mirror x) /
                                                   rotation (deg, KiCad sense) into the footprint frame
  }

w/h are the land extents along x/y for rot 0/90/180/270 (rot only matters
for other angles, then w/h are in the pad frame). Pads are matched by number
(nearest position among equal numbers, so S/S/S pads with one number work).
Copper-less pads (paste or mask apertures) are not lands and are never extra.

Checks (FAIL unless noted):
  pads        per pad dx, dy, dw, dh > --tol; custom lands: bounding box edges
              > --tol or mean boundary deviation (XOR area / perimeter) > --tol;
              shape class mismatch (rect <-> roundrect is only a WARN); spec pads
              missing from the footprint unless listed in removed_nc WITH a reason;
              footprint copper pads that are not in the spec (extra)
  body        F.Fab outline bounding box vs spec body (each edge within --tol);
              no F.Fab outline is a FAIL
  courtyard   F.CrtYd = max(body, land extents) + courtyard_margin, each edge
              within --crtyd-tol (rectangle), or the rectilinear union of
              body + every land, each grown by the margin (polygon); missing,
              open or B.CrtYd on a top-side SMD part fails / warns
  paste       every exposed pad: paste inside the pad 50-80 % of its area
              (spec paste.ratio_min/max) in >= min_windows apertures (default
              2 above 1 mm2), no paste outside the pad; other SMD lands without
              paste: WARN
  pin1        a pin-1 marker on F.Fab (dot/circle, chamfer or small filled shape
              in pin 1's quadrant); a silkscreen-only marker is a FAIL because
              component silk is stripped (owner rule) unless --silk-pin1-ok
  silk        component silkscreen present: WARN (owner rule: no component silk)

Exit 0 when every check passes, 1 on any FAIL, 2 if spec or footprint cannot be read.
"""
import argparse
import contextlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT = os.path.dirname(HERE)
MAXERR = 1000            # nm, polygon approximation of arcs (1 um)
pcbnew = None


@contextlib.contextmanager
def quiet_stderr():
    """pcbnew prints wx asserts on stderr while loading; keep the report clean."""
    try:
        fd = os.dup(2)
        dn = os.open(os.devnull, os.O_WRONLY)
        os.dup2(dn, 2)
    except OSError:
        yield
        return
    try:
        yield
    finally:
        os.dup2(fd, 2)
        os.close(fd)
        os.close(dn)


def import_pcbnew():
    global pcbnew
    if pcbnew is None:
        with quiet_stderr():
            import pcbnew as _p
        pcbnew = _p
    return pcbnew


def nm(v):
    return int(round(v * 1e6))


def mm(v):
    return v / 1e6


# ---------------------------------------------------------------- resolution
def _expand(uri, project_dir):
    def rep(m):
        var = m.group(1)
        if var == "KIPRJMOD":
            return project_dir
        if var in os.environ:
            return os.environ[var]
        if var.endswith("FOOTPRINT_DIR"):
            return "/usr/share/kicad/footprints"
        return m.group(0)
    return re.sub(r"\$\{([^}]+)\}", rep, uri)


def parse_lib_table(path, project_dir):
    libs = {}
    if not os.path.isfile(path):
        return libs
    txt = open(path, encoding="utf-8").read()
    for m in re.finditer(r"\(lib\s+(.*?)\)\s*(?=\(lib\s|\)\s*$)", txt, re.S):
        body = m.group(1)
        name = re.search(r'\(name\s+"?([^")]+?)"?\)', body)
        uri = re.search(r'\(uri\s+"?([^")]+?)"?\)', body)
        if name and uri:
            libs[name.group(1)] = _expand(uri.group(1), project_dir)
    return libs


def resolve_footprint(arg, project_dir=DEFAULT_PROJECT):
    """Return (library directory, footprint name, how it was found)."""
    if arg.endswith(".kicad_mod"):
        path = os.path.abspath(arg)
        return os.path.dirname(path), os.path.basename(path)[:-len(".kicad_mod")], "path"
    if ":" not in arg:
        raise ValueError(f"footprint '{arg}' is neither a .kicad_mod path nor Lib:Name")
    lib, name = arg.split(":", 1)
    tables = [os.path.join(project_dir, "fp-lib-table")]
    cfg = os.environ.get("KICAD_CONFIG_HOME", os.path.expanduser("~/.config/kicad"))
    tables += [os.path.join(cfg, v, "fp-lib-table") for v in ("10.0", "9.0")]
    for t in tables:
        libs = parse_lib_table(t, project_dir)
        if lib in libs:
            return libs[lib], name, t
    for base in (os.environ.get("KICAD10_FOOTPRINT_DIR"), "/usr/share/kicad/footprints"):
        if base and os.path.isdir(os.path.join(base, lib + ".pretty")):
            return os.path.join(base, lib + ".pretty"), name, base
    raise ValueError(f"library '{lib}' not found in {', '.join(tables)} or the stock footprint dir")


def kicad_io():
    P = import_pcbnew()
    return P.PCB_IO_MGR.FindPlugin(P.PCB_IO_MGR.KICAD_SEXP)


def load_footprint(lib_dir, name):
    if not os.path.isfile(os.path.join(lib_dir, name + ".kicad_mod")):
        raise ValueError(f"{name}.kicad_mod not found in {lib_dir}")
    with quiet_stderr():
        fp = kicad_io().FootprintLoad(lib_dir, name)
    if fp is None:
        raise ValueError(f"pcbnew could not load {lib_dir}/{name}")
    return fp


# ---------------------------------------------------------------- geometry
def rect_poly(x0, y0, x1, y1):
    """SHAPE_POLY_SET rectangle from mm coordinates."""
    P = import_pcbnew()
    s = P.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        s.Append(nm(x), nm(y))
    return s


def poly_from_points(pts):
    P = import_pcbnew()
    s = P.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in pts:
        s.Append(nm(x), nm(y))
    return s


def bbox(poly):
    b = poly.BBox()
    return (mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom()))


def area(poly):
    return poly.Area() / 1e12


def union(polys):
    P = import_pcbnew()
    out = P.SHAPE_POLY_SET()
    for p in polys:
        out.BooleanAdd(p)
    out.Simplify()
    return out


def intersect(a, b):
    P = import_pcbnew()
    c = P.SHAPE_POLY_SET(a)
    c.BooleanIntersection(b)
    return c


def xor_area(a, b):
    P = import_pcbnew()
    c = P.SHAPE_POLY_SET(a)
    c.BooleanXor(b)
    return area(c)


def perimeter(poly):
    total = 0.0
    for i in range(poly.OutlineCount()):
        o = poly.COutline(i)
        n = o.PointCount()
        for k in range(n):
            a, b = o.CPoint(k), o.CPoint((k + 1) % n)
            total += math.hypot(b.x - a.x, b.y - a.y)
    return total / 1e6


def outline_points(poly, i=0):
    o = poly.COutline(i)
    return [(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())]


def grow_bbox(b, m):
    return (b[0] - m, b[1] - m, b[2] + m, b[3] + m)


def bbox_union(boxes):
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def edge_dev(a, b):
    """Signed edge deviations (left, top, right, bottom) of a against b, outward positive."""
    return (b[0] - a[0], b[1] - a[1], a[2] - b[2], a[3] - b[3])


# ---------------------------------------------------------------- footprint data
PAD_SHAPES = {0: "circle", 1: "rect", 2: "oval", 3: "trapezoid", 4: "roundrect", 5: "chamfered", 6: "custom"}


def pad_polygon(pad, layer):
    P = import_pcbnew()
    s = P.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(s, layer, 0, MAXERR, P.ERROR_INSIDE)
    return s


def copper_side(pad):
    P = import_pcbnew()
    ls = pad.GetLayerSet()
    if ls.Contains(P.F_Cu):
        return P.F_Cu
    if ls.Contains(P.B_Cu):
        return P.B_Cu
    return None


def pad_records(fp):
    """Copper lands and copper-less apertures of a library footprint (origin 0, orientation 0)."""
    P = import_pcbnew()
    lands, apertures = [], []
    for pad in fp.Pads():
        side = copper_side(pad)
        pos = pad.GetPosition()
        rec = {"number": pad.GetNumber(), "x": mm(pos.x), "y": mm(pos.y),
               "shape": PAD_SHAPES.get(pad.GetShape(P.F_Cu), str(pad.GetShape(P.F_Cu))),
               "rot": pad.GetOrientationDegrees() % 360.0, "pad": pad}
        size = pad.GetSize(P.F_Cu)
        rec["sw"], rec["sh"] = mm(size.x), mm(size.y)
        if side is None:
            apertures.append(rec)
            continue
        rec["side"] = "F" if side == P.F_Cu else "B"
        rec["poly"] = pad_polygon(pad, side)
        rec["bbox"] = bbox(rec["poly"])
        rec["area"] = area(rec["poly"])
        lands.append(rec)
    return lands, apertures


def paste_polygon(rec):
    """The pad's paste opening on F.Paste including its paste margin, or None."""
    P = import_pcbnew()
    pad = rec["pad"]
    if not pad.GetLayerSet().Contains(P.F_Paste):
        return None
    base = pad_polygon(pad, P.F_Paste)
    try:
        mg = pad.GetSolderPasteMargin(P.F_Paste)
        mx, my = mg.x, mg.y
    except Exception:
        mx = my = 0
    if mx == 0 and my == 0:
        return base
    if rec["shape"] in ("rect", "roundrect") and rec["rot"] % 90 == 0:
        x0, y0, x1, y1 = bbox(base)
        return rect_poly(x0 - mm(mx), y0 - mm(my), x1 + mm(mx), y1 + mm(my))
    m = min(mx, my)
    base.Inflate(m, P.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, MAXERR)
    return base


def shape_points(g):
    """Centre-line points of a footprint graphic (arcs and circles sampled)."""
    P = import_pcbnew()
    st = g.GetShape()
    if st == P.SHAPE_T_SEGMENT:
        a, b = g.GetStart(), g.GetEnd()
        return [(mm(a.x), mm(a.y)), (mm(b.x), mm(b.y))]
    if st == P.SHAPE_T_RECT:
        try:
            return [(mm(c.x), mm(c.y)) for c in g.GetRectCorners()]
        except Exception:
            a, b = g.GetStart(), g.GetEnd()
            return [(mm(a.x), mm(a.y)), (mm(b.x), mm(a.y)), (mm(b.x), mm(b.y)), (mm(a.x), mm(b.y))]
    if st == P.SHAPE_T_POLY:
        ps = g.GetPolyShape()
        pts = []
        for i in range(ps.OutlineCount()):
            pts += outline_points(ps, i)
        return pts
    if st == P.SHAPE_T_CIRCLE:
        c, r = g.GetCenter(), g.GetRadius()
        return [(mm(c.x + r * math.cos(t)), mm(c.y + r * math.sin(t)))
                for t in (k * math.pi / 18 for k in range(36))]
    if st == P.SHAPE_T_ARC:
        c, r = g.GetCenter(), g.GetRadius()
        a0 = math.atan2(g.GetStart().y - c.y, g.GetStart().x - c.x)
        am = math.atan2(g.GetArcMid().y - c.y, g.GetArcMid().x - c.x)
        a1 = math.atan2(g.GetEnd().y - c.y, g.GetEnd().x - c.x)
        sweep = (a1 - a0) % (2 * math.pi)
        if (am - a0) % (2 * math.pi) > sweep:      # mid not on the ccw path: go the other way
            sweep -= 2 * math.pi
        n = max(4, int(abs(sweep) / (math.pi / 36)))
        return [(mm(c.x + r * math.cos(a0 + sweep * k / n)), mm(c.y + r * math.sin(a0 + sweep * k / n)))
                for k in range(n + 1)]
    try:
        return [(mm(p.x), mm(p.y)) for p in g.GetBezierPoints()]
    except Exception:
        b = g.GetBoundingBox()
        return [(mm(b.GetLeft()), mm(b.GetTop())), (mm(b.GetRight()), mm(b.GetBottom()))]


def graphics(fp, layer):
    P = import_pcbnew()
    return [g for g in fp.GraphicalItems() if isinstance(g, P.PCB_SHAPE) and g.GetLayer() == layer]


def pts_bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def fab_body_bbox(fp, layer=None):
    """Body outline from F.Fab: segments, rectangles, polygons and arcs (circles are markers)."""
    P = import_pcbnew()
    layer = P.F_Fab if layer is None else layer
    pts = []
    for g in graphics(fp, layer):
        if g.GetShape() == P.SHAPE_T_CIRCLE:
            continue
        pts += shape_points(g)
    return pts_bbox(pts) if pts else None


def _chain(segs, tol=1e-4):
    """Chain segment/arc point lists into closed loops; returns (loops, open_count)."""
    segs = [list(s) for s in segs if len(s) >= 2]
    loops, open_count = [], 0
    while segs:
        cur = segs.pop(0)
        progress = True
        while progress and math.dist(cur[0], cur[-1]) > tol:
            progress = False
            for i, s in enumerate(segs):
                if math.dist(cur[-1], s[0]) <= tol:
                    cur += s[1:]
                elif math.dist(cur[-1], s[-1]) <= tol:
                    cur += s[::-1][1:]
                elif math.dist(cur[0], s[-1]) <= tol:
                    cur = s[:-1] + cur
                elif math.dist(cur[0], s[0]) <= tol:
                    cur = s[::-1][:-1] + cur
                else:
                    continue
                segs.pop(i)
                progress = True
                break
        if math.dist(cur[0], cur[-1]) <= tol and len(cur) >= 4:
            loops.append(cur[:-1])
        else:
            open_count += 1
    return loops, open_count


def courtyard_poly(fp, layer):
    """(SHAPE_POLY_SET or None, number of open chains, number of items)."""
    P = import_pcbnew()
    items = graphics(fp, layer)
    if not items:
        return None, 0, 0
    closed, segs = [], []
    for g in items:
        st = g.GetShape()
        if st in (P.SHAPE_T_RECT, P.SHAPE_T_POLY, P.SHAPE_T_CIRCLE):
            closed.append(poly_from_points(shape_points(g)))
        else:
            segs.append(shape_points(g))
    loops, open_count = _chain(segs)
    closed += [poly_from_points(l) for l in loops]
    return (union(closed) if closed else None), open_count, len(items)


# ---------------------------------------------------------------- spec handling
def load_spec(path):
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    if not isinstance(spec.get("pads"), list) or not spec["pads"]:
        raise ValueError("spec has no pads")
    return spec


def _xf(spec):
    """Point transform spec frame -> footprint frame, and whether w/h swap."""
    flip_y = spec.get("y_axis", "down") == "up"
    mirror = spec.get("view", "top") == "bottom"
    rot = float(spec.get("frame_rot", 0)) % 360.0
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def f(x, y):
        if flip_y:
            y = -y
        if mirror:
            x = -x
        return (x * c + y * s, -x * s + y * c)
    swap = abs(round(rot / 90.0)) % 2 == 1 and abs(rot - 90 * round(rot / 90.0)) < 1e-6
    return f, swap, rot


def spec_pads(spec):
    f, swap, frot = _xf(spec)
    out = []
    for i, p in enumerate(spec["pads"]):
        num = str(p.get("number", ""))
        shape = p.get("shape", "rect")
        rot = (float(p.get("rot", 0)) + frot) % 360.0
        if shape == "custom":
            rects = p.get("rects") or []
            if not rects:
                raise ValueError(f"spec pad {num}: custom shape needs 'rects'")
            polys = []
            for r in rects:
                x, y = f(r["x"], r["y"])
                w, h = (r["h"], r["w"]) if swap else (r["w"], r["h"])
                polys.append(rect_poly(x - w / 2, y - h / 2, x + w / 2, y + h / 2))
            poly = union(polys)
            b = bbox(poly)
            out.append({"i": i, "number": num, "shape": "custom", "poly": poly, "bbox": b,
                        "x": (b[0] + b[2]) / 2, "y": (b[1] + b[3]) / 2,
                        "w": b[2] - b[0], "h": b[3] - b[1], "rot": 0.0})
            continue
        x, y = f(p["x"], p["y"])
        w, h = p["w"], p["h"]
        if rot % 90 < 1e-6 or 90 - rot % 90 < 1e-6:     # axis aligned: compare extents along x/y
            if round(rot / 90) % 2 == 1:
                w, h = h, w
            rot_cmp = 0.0
        else:
            rot_cmp = rot
        out.append({"i": i, "number": num, "shape": shape, "x": x, "y": y, "w": w, "h": h, "rot": rot_cmp,
                    "poly": rect_poly(x - w / 2, y - h / 2, x + w / 2, y + h / 2) if rot_cmp == 0.0 else None})
    return out


def fp_extent(rec):
    """Footprint land in the comparison frame: (cx, cy, w, h, rot)."""
    r = rec["rot"]
    if rec["shape"] == "custom" or r % 90 < 1e-6 or 90 - r % 90 < 1e-6:
        b = rec["bbox"]
        if rec["shape"] == "custom":
            return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b[2] - b[0], b[3] - b[1], 0.0)
        w, h = (rec["sh"], rec["sw"]) if round(r / 90) % 2 == 1 else (rec["sw"], rec["sh"])
        return (rec["x"], rec["y"], w, h, 0.0)
    return (rec["x"], rec["y"], rec["sw"], rec["sh"], r)


def natural_key(n):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(n))]


def compress(nums):
    """'2,3,4,5,7' -> '2-5,7' for numeric pad numbers, else a plain list."""
    if len(set(nums)) < len(nums):          # repeated numbers (S/S/S): '1x3,2'
        seen = sorted(set(nums), key=natural_key)
        return ",".join(n + (f"x{nums.count(n)}" if nums.count(n) > 1 else "") for n in seen)
    if not all(n.isdigit() for n in nums):
        return ",".join(nums)
    v = [int(n) for n in nums]
    out, i = [], 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[j + 1] == v[j] + 1:
            j += 1
        out.append(f"{v[i]}-{v[j]}" if j > i else str(v[i]))
        i = j + 1
    return ",".join(out)


def match_pads(sp, lands):
    """Greedy nearest matching inside each pad number."""
    pairs, missing, extra = [], [], []
    nums = sorted({p["number"] for p in sp} | {l["number"] for l in lands})
    for n in nums:
        a = [p for p in sp if p["number"] == n]
        b = [l for l in lands if l["number"] == n]
        cand = sorted(((math.hypot(p["x"] - fp_extent(l)[0], p["y"] - fp_extent(l)[1]), i, j)
                       for i, p in enumerate(a) for j, l in enumerate(b)))
        ua, ub = set(), set()
        for d, i, j in cand:
            if i in ua or j in ub:
                continue
            ua.add(i)
            ub.add(j)
            pairs.append((a[i], b[j]))
        missing += [p for i, p in enumerate(a) if i not in ua]
        extra += [l for j, l in enumerate(b) if j not in ub]
    return pairs, missing, extra


# ---------------------------------------------------------------- checks
class Report:
    def __init__(self):
        self.lines, self.fails, self.warns, self.data = [], 0, 0, {}

    def add(self, status, text):
        if status == "FAIL":
            self.fails += 1
        elif status == "WARN":
            self.warns += 1
        self.lines.append(f"{status:4} {text}")


def check_pads(spec, lands, tol, rep, verbose):
    sp = spec_pads(spec)
    pairs, missing, extra = match_pads(sp, lands)
    removed = {}
    for r in spec.get("removed_nc", []) or []:
        if isinstance(r, dict):
            removed.setdefault(str(r.get("number", "")), []).append(r.get("reason", "").strip())
        else:
            removed.setdefault(str(r), []).append("")
    rows, worst, groups = [], (0.0, None, None), {}
    bad = 0
    pairs.sort(key=lambda sl: natural_key(sl[0]["number"]))
    for s, l in pairs:
        cx, cy, w, h, r = fp_extent(l)
        err = {"dx": cx - s["x"], "dy": cy - s["y"], "dw": w - s["w"], "dh": h - s["h"]}
        if s["rot"] or r:
            err["drot"] = ((r - s["rot"] + 90) % 180) - 90
        if s["shape"] == "custom" or l["shape"] == "custom":
            if s.get("poly") is not None:
                err["dev"] = xor_area(l["poly"], s["poly"]) / max(perimeter(s["poly"]), 1e-9)
        mag = max(abs(v) for k, v in err.items() if k != "drot")
        if mag > worst[0]:
            worst = (mag, s["number"], max((k for k in err if k != "drot"), key=lambda k: abs(err[k])))
        shape_note = ""
        if s["shape"] != l["shape"]:
            pair = {s["shape"], l["shape"]}
            shape_note = f" shape {l['shape']} (spec {s['shape']})"
            if pair == {"rect", "roundrect"}:
                if verbose:
                    rep.add("WARN", f"pad {s['number']}: shape {l['shape']}, datasheet {s['shape']}")
            else:
                rep.add("FAIL", f"pad {s['number']}: shape {l['shape']}, spec {s['shape']}")
        failed = mag > tol + 1e-9 or abs(err.get("drot", 0.0)) > 0.5
        bad += failed
        rows.append({"number": s["number"], "spec": {k: round(s[k], 4) for k in ("x", "y", "w", "h")},
                     "fp": {"x": round(cx, 4), "y": round(cy, 4), "w": round(w, 4), "h": round(h, 4),
                            "shape": l["shape"]},
                     "err": {k: round(v, 4) for k, v in err.items()}, "fail": failed})
        if failed or verbose:
            txt = " ".join(f"{k} {v:+.3f}" for k, v in err.items()) + shape_note
            groups.setdefault(("FAIL" if failed else "ok", txt), []).append(s["number"])
    for (status, txt), nums in groups.items():     # one line per identical error vector
        rep.add(status, f"pad{'s' if len(nums) > 1 else ''} {compress(nums)}: {txt}")
    rr_mismatch = sum(1 for s, l in pairs if {s["shape"], l["shape"]} == {"rect", "roundrect"})
    if rr_mismatch and not verbose:
        rep.add("WARN", f"{rr_mismatch} pads roundrect vs rect in the datasheet (extents compared, corners ignored)")
    for p in missing:
        reasons = removed.get(p["number"])
        if reasons is not None:
            if reasons and reasons[0]:
                rep.add("ok", f"pad {p['number']}: removed NC pad, documented: {reasons.pop(0)}")
            else:
                rep.add("FAIL", f"pad {p['number']}: removed without a documented reason in removed_nc")
        else:
            rep.add("FAIL", f"pad {p['number']} missing (spec x {p['x']:+.3f} y {p['y']:+.3f})")
    for l in extra:
        rep.add("FAIL", f"extra copper pad '{l['number']}' at x {l['x']:+.3f} y {l['y']:+.3f} (not in the spec)")
    kept = [n for n in removed if any(l["number"] == n for _, l in pairs)]
    if kept:
        rep.add("WARN", f"pads listed in removed_nc but still present: {', '.join(kept)}")
    summ = (f"pads: spec {len(sp)}, footprint lands {len(lands)}, matched {len(pairs)}, "
            f"missing {len(missing)}, extra {len(extra)}; out of tol {bad}/{len(pairs)}")
    if worst[1] is not None:
        summ += f"; worst {worst[0]:.3f} mm (pad {worst[1]} {worst[2]})"
    rep.add("FAIL" if (bad or extra or any(p['number'] not in removed for p in missing)) else "ok", summ)
    rep.data["pads"] = rows
    return sp


def spec_body(spec):
    b = spec.get("body")
    if not b:
        return None
    f, swap, _ = _xf(spec)
    x, y = f(b.get("x", 0.0), b.get("y", 0.0))
    w, h = (b["h"], b["w"]) if swap else (b["w"], b["h"])
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def check_body(spec, fp, tol, rep):
    sb = spec_body(spec)
    fb = fab_body_bbox(fp)
    rep.data["body"] = {"spec": sb, "fab": fb}
    if sb is None:
        rep.add("WARN", "body: no body in the spec (courtyard uses the F.Fab outline)")
        return fb
    if fb is None:
        rep.add("FAIL", f"body: no F.Fab outline (spec {sb[2]-sb[0]:.2f} x {sb[3]-sb[1]:.2f})")
        return sb
    d = edge_dev(fb, sb)
    mag = max(abs(v) for v in d)
    rep.add("FAIL" if mag > tol + 1e-9 else "ok",
            f"body: F.Fab {fb[2]-fb[0]:.3f} x {fb[3]-fb[1]:.3f} vs spec {sb[2]-sb[0]:.3f} x {sb[3]-sb[1]:.3f}"
            f" (edge dev max {mag:.3f})")
    return sb


CLOSE_GAP = 0.15        # mm: a polygon courtyard bridges notches narrower than 2x this


def snap_out(b, grid):
    """Grow a bbox outward to the grid (exact integer nm arithmetic)."""
    g = nm(grid)
    x0, y0, x1, y1 = (nm(v) for v in b)
    return (mm(math.floor(x0 / g) * g), mm(math.floor(y0 / g) * g),
            mm(math.ceil(x1 / g) * g), mm(math.ceil(y1 / g) * g))


def rectilinear_hull(boxes, margin, grid=None, close=CLOSE_GAP):
    """Union of the boxes grown by margin (optionally snapped out to grid), closed with a square
    element of 2*close so the courtyard has no comb notches between neighbouring lands."""
    P = import_pcbnew()
    grown = [grow_bbox(b, margin) for b in boxes]
    if grid:
        grown = [snap_out(b, grid) for b in grown]
    u = union([rect_poly(*grow_bbox(b, close)) for b in grown])
    if close > 0:
        u.Deflate(nm(close), P.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS, MAXERR)
        u.Simplify()
    return u


def expected_courtyard(body, lands, margin):
    """(rectangle bbox, rectilinear polygon) for courtyard = max(body, lands) + margin."""
    boxes = [l["bbox"] for l in lands]
    if body:
        boxes.append(body)
    rect = grow_bbox(bbox_union(boxes), margin)
    return rect, rectilinear_hull(boxes, margin)


def courtyard_status(fp, body, lands, margin, ctol):
    """Shared with normalise_courtyard.py: (ok, text, data)."""
    P = import_pcbnew()
    front = [l for l in lands if l["side"] == "F"]
    back = [l for l in lands if l["side"] == "B"]
    smd_top = not back and all(not l["pad"].HasHole() for l in lands)
    rect, epoly = expected_courtyard(body, front or lands, margin)
    data = {"expected_rect": rect, "margin": margin}
    cpoly, open_count, n = courtyard_poly(fp, P.F_CrtYd)
    bpoly, _, nb = courtyard_poly(fp, P.B_CrtYd)
    notes = []
    if nb and smd_top:
        notes.append(f"B.CrtYd present ({nb} items) on a top-side SMD footprint")
    if cpoly is None:
        if open_count:
            return False, f"courtyard: F.CrtYd not closed ({open_count} open chains)", data, notes
        return False, f"courtyard: no F.CrtYd (expected {rect[2]-rect[0]:.2f} x {rect[3]-rect[1]:.2f})", data, notes
    if open_count:
        notes.append(f"F.CrtYd has {open_count} open chains")
    ab = bbox(cpoly)
    is_rect = cpoly.OutlineCount() == 1 and abs(area(cpoly) - (ab[2] - ab[0]) * (ab[3] - ab[1])) < 1e-4
    d_rect = max(abs(v) for v in edge_dev(ab, rect))
    dev_poly = xor_area(cpoly, epoly) / max(perimeter(epoly), 1e-9)
    d_pbox = max(abs(v) for v in edge_dev(ab, bbox(epoly)))
    data.update({"actual_bbox": ab, "rect": is_rect, "rect_edge_dev": d_rect, "poly_mean_dev": dev_poly})
    ok_rect = is_rect and d_rect <= ctol + 1e-6
    ok_poly = dev_poly <= ctol + 1e-6 and d_pbox <= ctol + 1e-6
    kind = "rect" if is_rect else f"polygon ({cpoly.COutline(0).PointCount()} pts)"
    text = (f"courtyard: F.CrtYd {kind} {ab[2]-ab[0]:.3f} x {ab[3]-ab[1]:.3f}, expected "
            f"{rect[2]-rect[0]:.3f} x {rect[3]-rect[1]:.3f} (margin {margin:.2f}); "
            + (f"edge dev max {d_rect:.3f}" if is_rect else f"mean dev vs rectilinear {dev_poly:.3f}"))
    if not is_rect and not ok_poly:
        text += f", vs rectangle {d_rect:.3f}"
    return ok_rect or ok_poly, text, data, notes


def check_courtyard(spec, fp, lands, body, ctol, rep):
    margin = float(spec.get("courtyard_margin", 0.10))
    ok, text, data, notes = courtyard_status(fp, body, lands, margin, ctol)
    rep.add("ok" if ok else "FAIL", text)
    for n in notes:
        rep.add("WARN", n)
    rep.data["courtyard"] = data


def exposed_pads(spec, lands):
    if "exposed" in spec:
        want = {str(n) for n in spec["exposed"]}
        return [l for l in lands if l["number"] in want]
    areas = sorted(l["area"] for l in lands)
    if len(areas) < 3:
        return []
    med = areas[len(areas) // 2]
    return [l for l in lands if l["area"] >= 0.5 and l["area"] >= 3 * med]


def paste_shapes(fp, lands, apertures):
    """All F.Paste openings: pad openings (with margins), aperture pads, F.Paste graphics."""
    P = import_pcbnew()
    polys = []
    for rec in lands + apertures:
        if "side" in rec and rec["side"] != "F":
            continue
        pp = paste_polygon(rec)
        if pp is not None and area(pp) > 0:
            polys.append(pp)
    for g in graphics(fp, P.F_Paste):
        s = P.SHAPE_POLY_SET()
        g.TransformShapeToPolygon(s, P.F_Paste, 0, MAXERR, P.ERROR_INSIDE)
        polys.append(s)
    return union(polys) if polys else P.SHAPE_POLY_SET()


def check_paste(spec, fp, lands, apertures, rep):
    P = import_pcbnew()
    cfg = spec.get("paste", {}) or {}
    rmin, rmax = float(cfg.get("ratio_min", 0.50)), float(cfg.get("ratio_max", 0.80))
    paste = paste_shapes(fp, lands, apertures)
    eps = exposed_pads(spec, lands)
    rep.data["paste"] = []
    for ep in eps:
        inside = intersect(paste, ep["poly"])
        a_in = area(inside)
        ratio = a_in / ep["area"] if ep["area"] else 0.0
        windows = inside.OutlineCount()
        # paste that touches this pad's opening but leaves the pad
        touching = P.SHAPE_POLY_SET()
        for i in range(paste.OutlineCount()):
            o = P.SHAPE_POLY_SET()
            o.AddOutline(paste.COutline(i))
            if area(intersect(o, ep["poly"])) > 0:
                touching.BooleanAdd(o)
        outside = area(touching) - a_in
        minw = int(cfg.get("min_windows", 2 if ep["area"] > 1.0 else 1))
        ok = rmin - 1e-6 <= ratio <= rmax + 1e-6 and windows >= minw and outside < 1e-4
        rep.add("ok" if ok else "FAIL",
                f"paste: exposed pad {ep['number']} ({ep['area']:.2f} mm2) paste {ratio*100:.0f} % "
                f"(want {rmin*100:.0f}-{rmax*100:.0f} %) in {windows} windows (want >= {minw})"
                + (f", {outside:.3f} mm2 outside the pad" if outside >= 1e-4 else ""))
        rep.data["paste"].append({"pad": ep["number"], "ratio": round(ratio, 4), "windows": windows,
                                  "outside_mm2": round(outside, 4), "ok": ok})
    epset = {id(e) for e in eps}
    nopaste = [l["number"] for l in lands if id(l) not in epset and l["side"] == "F"
               and not l["pad"].HasHole() and area(intersect(paste, l["poly"])) < 0.05 * l["area"]]
    if nopaste:
        rep.add("WARN", f"paste: {len(nopaste)} SMD lands without paste: {', '.join(nopaste[:12])}")
    if not eps:
        rep.add("ok", "paste: no exposed pad")


def _markers(fp, layer, p1, body):
    """Pin-1 marker candidates on one layer: dots/circles, diagonal (chamfer) edges, small filled shapes."""
    P = import_pcbnew()
    half = (max(body[2] - body[0], 0.2) / 2, max(body[3] - body[1], 0.2) / 2) if body else (0.5, 0.5)
    cx = (body[0] + body[2]) / 2 if body else 0.0
    cy = (body[1] + body[3]) / 2 if body else 0.0
    q = (p1[0] - cx, p1[1] - cy)

    def in_quadrant(m):
        mx, my = m[0] - cx, m[1] - cy
        for qa, ma, h in ((q[0], mx, half[0]), (q[1], my, half[1])):
            if abs(qa) > 0.05:
                if ma * qa <= 0 or abs(ma) < 0.1 * h:
                    return False
        d1 = math.dist(m, p1)
        d2 = math.dist(m, (2 * cx - p1[0], 2 * cy - p1[1]))
        return d1 < d2 - 0.05

    found = []
    for g in graphics(fp, layer):
        st = g.GetShape()
        pts = shape_points(g)
        if st == P.SHAPE_T_CIRCLE:
            c = g.GetCenter()
            m = (mm(c.x), mm(c.y))
            if in_quadrant(m):
                found.append(("dot", m))
            continue
        filled = False
        try:
            filled = g.IsFilled()
        except Exception:
            pass
        bb = pts_bbox(pts)
        if filled and max(bb[2] - bb[0], bb[3] - bb[1]) < 1.2 * min(half):
            m = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
            if in_quadrant(m):
                found.append(("filled", m))
                continue
        edges = list(zip(pts, pts[1:] + ([pts[0]] if st in (P.SHAPE_T_POLY, P.SHAPE_T_RECT) else [])))
        for a, b in edges:
            dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
            if dx < 1e-4 or dy < 1e-4:
                continue
            ang = math.degrees(math.atan2(dy, dx))
            if 20 <= ang <= 70:
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                if in_quadrant(m):
                    found.append(("chamfer", m))
    return found


def check_pin1(spec, fp, lands, body, rep, silk_ok):
    P = import_pcbnew()
    n = str(spec.get("pin1", "1"))
    p1s = [l for l in lands if l["number"] == n]
    if not p1s:
        rep.add("FAIL", f"pin1: no land numbered '{n}'")
        return
    cx = (body[0] + body[2]) / 2 if body else 0.0
    cy = (body[1] + body[3]) / 2 if body else 0.0
    p1 = max(p1s, key=lambda l: math.hypot(l["x"] - cx, l["y"] - cy))
    pos = (p1["x"], p1["y"]) if p1["shape"] != "custom" else \
        ((p1["bbox"][0] + p1["bbox"][2]) / 2, (p1["bbox"][1] + p1["bbox"][3]) / 2)
    fab = _markers(fp, P.F_Fab, pos, body)
    silk = _markers(fp, P.F_SilkS, pos, body)
    rep.data["pin1"] = {"fab": [k for k, _ in fab], "silk": [k for k, _ in silk]}
    if fab:
        rep.add("ok", f"pin1: F.Fab marker ({', '.join(sorted({k for k, _ in fab}))}) at pin {n}")
    elif silk:
        rep.add("WARN" if silk_ok else "FAIL",
                f"pin1: marker on silkscreen only ({', '.join(sorted({k for k, _ in silk}))}); "
                "component silk is stripped (owner rule) -> add an F.Fab chamfer or dot")
    else:
        rep.add("FAIL", f"pin1: no pin-1 marker near pin {n} on F.Fab or silkscreen")


def check_silk(fp, rep):
    P = import_pcbnew()
    n = sum(1 for g in fp.GraphicalItems() if g.GetLayer() in (P.F_SilkS, P.B_SilkS))
    ref = fp.Reference()
    vis_ref = ref.IsVisible() and ref.GetLayer() in (P.F_SilkS, P.B_SilkS)
    if n or vis_ref:
        rep.add("WARN", f"silk: {n} silkscreen graphics{' + visible reference' if vis_ref else ''} "
                        "(owner rule: components carry no silkscreen)")


def run(spec_path, fp_arg=None, project=DEFAULT_PROJECT, tol=0.02, ctol=0.01, silk_ok=False, verbose=False):
    rep = Report()
    spec = load_spec(spec_path)
    target = fp_arg or spec.get("footprint")
    if not target:
        raise ValueError("no footprint given (argument or spec 'footprint')")
    lib_dir, name, how = resolve_footprint(target, project)
    fp = load_footprint(lib_dir, name)
    rep.data.update({"spec": os.path.abspath(spec_path), "footprint": f"{lib_dir}/{name}.kicad_mod",
                     "resolved_via": how, "tol": tol, "crtyd_tol": ctol})
    if not str(spec.get("datasheet", "")).strip():
        rep.add("WARN", "spec: no 'datasheet' source")
    sname = str(spec.get("footprint", ""))
    if sname and fp_arg and sname.split(":")[-1].replace(".kicad_mod", "") != name and ":" in sname:
        rep.add("WARN", f"spec names footprint {sname}, checking {name}")
    lands, apertures = pad_records(fp)
    check_pads(spec, lands, tol, rep, verbose)
    body = check_body(spec, fp, tol, rep)
    check_courtyard(spec, fp, lands, body, ctol, rep)
    check_paste(spec, fp, lands, apertures, rep)
    check_pin1(spec, fp, lands, body, rep, silk_ok)
    check_silk(fp, rep)
    return rep, name


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec")
    ap.add_argument("footprint", nargs="?")
    ap.add_argument("--project", default=DEFAULT_PROJECT, help="directory holding fp-lib-table (KIPRJMOD)")
    ap.add_argument("--tol", type=float, default=0.02, help="pad and body tolerance, mm")
    ap.add_argument("--crtyd-tol", type=float, default=0.01, help="courtyard tolerance, mm")
    ap.add_argument("--silk-pin1-ok", action="store_true", help="accept a silkscreen-only pin-1 marker")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true", help="list every pad")
    a = ap.parse_args(argv)
    try:
        rep, name = run(a.spec, a.footprint, a.project, a.tol, a.crtyd_tol, a.silk_pin1_ok, a.verbose)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"check_footprint: {e}", file=sys.stderr)
        return 2
    verdict = "FAIL" if rep.fails else "PASS"
    if a.json:
        out = dict(rep.data)
        out.update({"result": verdict, "fails": rep.fails, "warns": rep.warns, "lines": rep.lines})
        print(json.dumps(out, indent=1, default=lambda o: None))
    else:
        print(f"check_footprint: {name}  vs  {os.path.basename(a.spec)}")
        for ln in rep.lines:
            print("  " + ln)
        print(f"RESULT {verdict}: {rep.fails} FAIL, {rep.warns} WARN")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())
