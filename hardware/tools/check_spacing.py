#!/usr/bin/env python3
"""Package-to-package spacing on a dense double-sided board.

    $KPY hardware/tools/check_spacing.py board.kicad_pcb [--min 0.20] [--edge 0.20] [--near 1.0]
                                         [--courtyard-margin 0.25] [--min-hole 1.0] [--hole-margin 0.5]
                                         [--json]

Runs under KiCad's Python (KPY, see AGENTS.md). Read-only: the board is never saved.

Courtyard DRC cannot hold parts 0.2 mm apart: KLC courtyards add 0.25 mm per
part, and easyeda2kicad parts draw the courtyard on the body, inside the lands.
This measures the package extent instead. Per footprint and side it is a set
of convex polygons:

  * every copper pad on that side's outer layer (pads can stick out past the
    body; through-hole pads count on both sides),
  * the body, from the first of:
      fab    convex hull of the Fab graphics on the footprint's side, when they
             outline a body (easyeda2kicad parts only carry a pin-1 dot there),
      crtyd  convex hull of the courtyard when pads cross it (easyeda2kicad
             draws the courtyard on the body),
      name   an LCSC-style name ...-L<len>-W<wid>[-LS<span>]..., centred on the
             pads and oriented from the pad layout,
      crtyd  a courtyard that encloses every pad, shrunk by its clearance to the
             pads, at most --courtyard-margin (KLC style),
      pads   no body, pads only.

Gaps are exact polygon distances, so rotated parts are measured right; an
overlap is negative (penetration depth). Reported per side: pairs closer than
--min with refs, gap and the midpoint of the closest points; a histogram of
gaps between neighbours (pairs closer than --near); parts closer than --edge to
the outline or its cut-outs, negative when they poke out (footprints with a
plated hole cut by the outline, castellations, are exempt and listed); parts
that overlap a keepout, which is a rule area
forbidding footprints, or a mounting hole (pad drilled >= --min-hole on a
MountingHole or H<n> footprint, or an NPTH-only one): its courtyard, else a
disc of drill/2 + --hole-margin, on both sides. Holes and footprints with
neither pads nor body (logos) are not paired.

Exit 0 when clean, 1 on any finding, 2 if the board cannot be read.
"""
import argparse
import json
import fnmatch
import math
import os
import re
import sys
from collections import Counter, namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcb_build as pb  # noqa: E402

P = pb.P
TOL = 1e-4                    # mm; KiCad stores nm, so an exact-gap placement can read 1 nm short
ERR = P.FromMM(0.005)         # pad arc approximation, polygon outside the true shape
NAME = re.compile(r"[_-]L(\d+(?:\.\d+)?)-W(\d+(?:\.\d+)?)(?:-[^_]*?LS(\d+(?:\.\d+)?))?")
Part = namedtuple("Part", "ref side polys boxes box")


# -- plane geometry (mm tuples) ----------------------------------------------
def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def hull(pts):
    """Convex hull, counter-clockwise in math axes (Andrew's monotone chain)."""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and cross(out[-2], out[-1], p) <= 1e-12:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(pts[::-1])


def area(poly):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def box_gap(a, b):
    dx, dy = max(a[0] - b[2], b[0] - a[2], 0), max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def edges(poly):
    return zip(poly, poly[1:] + poly[:1])


def width(poly):
    """Smallest caliper width of a convex polygon."""
    best = math.inf
    for a, b in edges(poly):
        ln = math.dist(a, b)
        if ln > 1e-9:
            best = min(best, max(abs(cross(a, b, p)) / ln for p in poly))
    return best if best < math.inf else 0.0


def seg_point(p, a, b):
    """Distance from p to segment ab and the closest point."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = dx * dx + dy * dy
    t = 0.0 if ln == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ln))
    q = (a[0] + t * dx, a[1] + t * dy)
    return math.dist(p, q), q


def penetration(a, b):
    """Overlap depth of convex polygons by the separating axis test; 0 when apart or touching."""
    depth = math.inf
    for poly in (a, b):
        for p, q in edges(poly):
            nx, ny = q[1] - p[1], p[0] - q[0]
            ln = math.hypot(nx, ny)
            if ln < 1e-12:
                continue
            pa = [(x * nx + y * ny) / ln for x, y in a]
            pb_ = [(x * nx + y * ny) / ln for x, y in b]
            o = min(max(pa) - min(pb_), max(pb_) - min(pa))
            if o <= 0:
                return 0.0
            depth = min(depth, o)
    return depth if depth < math.inf else 0.0


def poly_gap(a, b, ba=None, bb=None):
    """(gap, point) between convex polygons; negative penetration depth when they overlap."""
    ba, bb = ba or bbox(a), bb or bbox(b)
    if box_gap(ba, bb) == 0:
        pen = penetration(a, b)
        if pen > 0:
            return -pen, ((max(ba[0], bb[0]) + min(ba[2], bb[2])) / 2, (max(ba[1], bb[1]) + min(ba[3], bb[3])) / 2)
    best, at = math.inf, None
    for xs, ys in ((a, b), (b, a)):
        for p in xs:
            for s, t in edges(ys):
                d, q = seg_point(p, s, t)
                if d < best:
                    best, at = d, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    return best, at


def clip(poly, nx, ny, c):
    """Part of a convex polygon where nx*x + ny*y <= c (Sutherland-Hodgman, one half-plane)."""
    out = []
    for p, q in edges(poly):
        fp, fq = nx * p[0] + ny * p[1] - c, nx * q[0] + ny * q[1] - c
        if fp <= 0:
            out.append(p)
        if fp * fq < 0:
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def erode(poly, d):
    """Convex polygon shrunk by d on every side, or None when nothing is left."""
    out = poly
    for p, q in edges(poly):                 # poly is CCW: outward normal is (dy, -dx)
        nx, ny = q[1] - p[1], p[0] - q[0]
        ln = math.hypot(nx, ny)
        if ln < 1e-9:
            continue
        nx, ny = nx / ln, ny / ln
        out = clip(out, nx, ny, nx * p[0] + ny * p[1] - d)
        if len(out) < 3:
            return None
    return hull(out) if area(out) > 1e-6 else None


def inside_clearance(pts, poly):
    """Smallest distance from pts to the boundary of convex CCW poly; <= 0 if any point is outside."""
    best = math.inf
    for p in pts:
        for a, b in edges(poly):
            best = min(best, cross(a, b, p) / math.dist(a, b))
    return best


def disc(c, r, n=24):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def seg_cross(p1, p2, q1, q2):
    d1, d2, d3, d4 = cross(q1, q2, p1), cross(q1, q2, p2), cross(p1, p2, q1), cross(p1, p2, q2)
    return d1 * d2 < 0 and d3 * d4 < 0


def in_poly(p, poly):
    """Even-odd point in polygon (any simple polygon)."""
    c = False
    for a, b in edges(poly):
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            c = not c
    return c


def overlaps(convex, poly):
    """Convex polygon against any simple polygon: True when their interiors meet."""
    if any(seg_cross(a, b, c, d) for a, b in edges(convex) for c, d in edges(poly)):
        return True
    return any(in_poly(p, poly) for p in convex) or any(inside_clearance([p], convex) > 0 for p in poly)


# -- KiCad geometry -> polygons ---------------------------------------------
def mmxy(v):
    return (P.ToMM(v.x), P.ToMM(v.y))


def chain(c):
    return [mmxy(c.CPoint(i)) for i in range(c.PointCount())]


def shape_points(fp, layer):
    """Vertices of the footprint's graphic shapes on layer (line centres, text ignored)."""
    pts = []
    for g in fp.GraphicalItems():
        if g.GetClass() != "PCB_SHAPE" or g.GetLayer() != layer:
            continue
        k = g.GetShape()
        if k == P.SHAPE_T_SEGMENT:
            pts += [mmxy(g.GetStart()), mmxy(g.GetEnd())]
        elif k == P.SHAPE_T_RECTANGLE:
            pts += [mmxy(v) for v in g.GetRectCorners()]
        elif k == P.SHAPE_T_CIRCLE:
            pts += disc(mmxy(g.GetCenter()), P.ToMM(g.GetRadius()), 16)
        elif k == P.SHAPE_T_ARC:
            c, r = mmxy(g.GetCenter()), P.ToMM(g.GetRadius())
            a0, da = g.GetArcAngleStart().AsRadians(), g.GetArcAngle().AsRadians()
            pts += [(c[0] + r * math.cos(a0 + da * i / 8), c[1] + r * math.sin(a0 + da * i / 8)) for i in range(9)]
            pts += [mmxy(g.GetStart()), mmxy(g.GetEnd())]
        elif k == P.SHAPE_T_POLY:
            ps = g.GetPolyShape()
            for i in range(ps.OutlineCount()):
                pts += chain(ps.Outline(i))
        elif k == P.SHAPE_T_BEZIER:
            pts += [mmxy(g.GetStart()), mmxy(g.GetBezierC1()), mmxy(g.GetBezierC2()), mmxy(g.GetEnd())]
    return pts


# --d70 (owner D70, 2026-10-09): filled+capped tented via pads (plated, drill <= VIA_DRILL_MAX: EP via fields,
# test vias) may sit under the BODY of a part; only pads must clear them, which is copper clearance (DRC), not
# the package body rule. With the flag they are left out of the package extents. Default off (unchanged).
D70 = False
VIA_DRILL_MAX = 0.25
KEEPOUT_OWNERS = []          # --keepout-owner REF:AREA (fnmatch patterns): the part a keep-out is drawn around


def via_like(p):
    return p.GetAttribute() == P.PAD_ATTRIB_PTH and P.ToMM(p.GetDrillSizeX()) <= VIA_DRILL_MAX + 1e-6


def pad_polys(fp, cu, skip_vias=False):
    out = []
    for p in fp.Pads():
        if not p.IsOnLayer(cu) or (skip_vias and via_like(p)):
            continue
        ps = P.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(ps, cu, 0, ERR, P.ERROR_OUTSIDE)
        out += [h for h in (hull(chain(ps.Outline(i))) for i in range(ps.OutlineCount())) if len(h) >= 3]
    return out


def name_body(fp, pads):
    """Body rectangle from an LCSC-style footprint name, oriented by the pads (None if no match)."""
    m = NAME.search(str(fp.GetFPID().GetLibItemName()))
    pts = [p for poly in pads for p in poly]
    if not m or not pts:
        return None
    ln, wd = float(m.group(1)), float(m.group(2))
    span = float(m.group(3)) if m.group(3) else None
    ox, oy = mmxy(fp.GetPosition())
    a = fp.GetOrientation().AsRadians()
    ca, sa = math.cos(a), math.sin(a)
    # KiCad rotates with y down: board = pos + (x cos + y sin, -x sin + y cos); a mirror swaps no axes
    loc = [((x - ox) * ca - (y - oy) * sa, (x - ox) * sa + (y - oy) * ca) for x, y in pts]
    x0, y0, x1, y1 = bbox(loc)
    ex, ey, cx, cy = x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2
    if span:     # the pads span LS along the leads; the body side that way is at most about LS
        along_x = ex >= span - 0.1 and (ey < span - 0.1 or ex >= ey)   # (no-lead parts reach a bit
        across = ey if along_x else ex                                  # past it), the side across
        opts = [(a, c) for a, c in ((ln, wd), (wd, ln)) if a <= span + 0.3]   # covers the pin rows
        a_len, o_len = max([o for o in opts if o[1] >= across - 0.05] or opts or [(ln, wd)])
        bx, by = (a_len, o_len) if along_x else (o_len, a_len)
    else:
        bx, by = (max(ln, wd), min(ln, wd)) if ex >= ey else (min(ln, wd), max(ln, wd))
    rect = [(cx - bx / 2, cy - by / 2), (cx + bx / 2, cy - by / 2), (cx + bx / 2, cy + by / 2), (cx - bx / 2, cy + by / 2)]
    return hull([(ox + x * ca + y * sa, oy - x * sa + y * ca) for x, y in rect])


def body(fp, pads, margin):
    """(convex body polygon or None, source)."""
    back = fp.IsFlipped()
    ph = hull([p for poly in pads for p in poly])
    pad_area, pad_w = (area(ph), width(ph)) if len(ph) >= 3 else (0.0, 0.0)
    h = hull(shape_points(fp, P.B_Fab if back else P.F_Fab))
    if len(h) >= 3 and area(h) >= 0.3 * pad_area and width(h) >= max(0.1, 0.3 * pad_w):
        return h, "fab"
    h = hull(shape_points(fp, P.B_CrtYd if back else P.F_CrtYd))
    clear = (inside_clearance([p for poly in pads for p in poly], h) if pads else margin) if len(h) >= 3 else None
    if clear is not None and clear <= 0:
        return h, "crtyd"                    # pads cross it: drawn on the body (easyeda2kicad)
    nb = name_body(fp, pads)
    if nb:
        return nb, "name"
    e = erode(h, min(margin, clear)) if clear is not None else None
    return (e, "crtyd") if e else (None, "pads")


def extent(fp, side, margin=0.25):
    """Package extent of fp seen from side 'F' or 'B': (convex polygons, body source or None)."""
    far = fp.IsFlipped() != (side == "B")
    if D70:
        fpads = list(fp.Pads())
        if fpads and all(via_like(p) for p in fpads):
            return [], None                  # D70: a test-via footprint is a via, not a package
    pads = pad_polys(fp, P.F_Cu if side == "F" else P.B_Cu, skip_vias=D70 and far)
    if far:
        return pads, None                    # the other side's view: through-hole pads only
    b, src = body(fp, pads, margin)
    return ([b] if b else []) + pads, src


def make_part(ref, side, polys):
    boxes = [bbox(p) for p in polys]
    return Part(ref, side, polys, boxes, (min(b[0] for b in boxes), min(b[1] for b in boxes),
                                          max(b[2] for b in boxes), max(b[3] for b in boxes)))


def part_gap(a, b, limit=math.inf):
    """(gap, point) between two parts; pairs of polygons are tried nearest box first."""
    cand = sorted((box_gap(ba, bb), i, j) for i, ba in enumerate(a.boxes) for j, bb in enumerate(b.boxes))
    best, at = math.inf, None
    for lb, i, j in cand:
        if lb >= min(best, limit):
            break
        g, p = poly_gap(a.polys[i], b.polys[j], a.boxes[i], b.boxes[j])
        if g < best:
            best, at = g, p
    return best, at


def is_hole(fp, min_hole):
    pads = list(fp.Pads())
    big = [p for p in pads if p.GetDrillSizeX() >= P.FromMM(min_hole)]
    named = "mountinghole" in str(fp.GetFPID().GetLibItemName()).lower().replace("_", "") \
        or re.fullmatch(r"M?H\d+", fp.GetReference())
    npth = pads and all(p.GetAttribute() == P.PAD_ATTRIB_NPTH for p in pads)
    return bool(big) and bool(named or npth)


def keepouts(b, min_hole, hole_margin):
    """[(name, sides, polygon, convex, owner ref)] for holes and footprint-forbidding rule areas."""
    out = []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if is_hole(fp, min_hole):
            cy = hull(shape_points(fp, P.F_CrtYd) + shape_points(fp, P.B_CrtYd))
            if len(cy) >= 3:
                out.append(("hole " + ref, "FB", cy, True, ref))
            else:
                for p in fp.Pads():
                    if p.GetDrillSizeX() >= P.FromMM(min_hole):
                        r = P.ToMM(p.GetDrillSizeX()) / 2 + hole_margin
                        out.append(("hole " + ref, "FB", disc(mmxy(p.GetPosition()), r), True, ref))
    zones = [(z, None) for z in b.Zones()] + [(z, fp.GetReference()) for fp in b.GetFootprints() for z in fp.Zones()]
    for z, owner in zones:
        if z.GetIsRuleArea() and z.GetDoNotAllowFootprints() and z.Outline().OutlineCount():
            ls = z.GetLayerSet()
            sides = ("F" if ls.Contains(P.F_Cu) else "") + ("B" if ls.Contains(P.B_Cu) else "")
            poly = chain(z.Outline().Outline(0))
            name = "rule area " + (z.GetZoneName() or "(unnamed)") + (" of " + owner if owner else "")
            convex = len(hull(poly)) == len(set(poly))
            out.append((name, sides, hull(poly) if convex else poly, convex, owner))
    return out


def board_outline(b):
    """(SHAPE_POLY_SET, [ring point lists]) of the Edge.Cuts outline, or (None, [])."""
    cuts = [g for g in list(b.GetDrawings()) + [g for fp in b.GetFootprints() for g in fp.GraphicalItems()]
            if g.GetLayer() == P.Edge_Cuts]
    ps = P.SHAPE_POLY_SET()
    if not cuts or not b.GetBoardPolygonOutlines(ps, False) or not ps.OutlineCount():
        return None, []
    rings = []
    for i in range(ps.OutlineCount()):
        rings.append(chain(ps.Outline(i)))
        rings += [chain(ps.CHole(i, j)) for j in range(ps.HoleCount(i))]
    return ps, rings


def castellated(fp, segs):
    """True when a plated hole of fp is cut by the outline (castellation or edge pad by design)."""
    for p in fp.Pads():
        if p.GetProperty() == P.PAD_PROP_CASTELLATED:
            return True
        r = P.ToMM(p.GetDrillSizeX()) / 2
        if r > 0 and p.GetAttribute() == P.PAD_ATTRIB_PTH:
            c = mmxy(p.GetPosition())
            if any(seg_point(c, s, t)[0] < r for s, t in segs):
                return True
    return False


def edge_gap(part, ps, segs, limit):
    """(gap, point, outside) of a part to the outline; gap < 0 is how far it pokes out,
    None when it is farther than limit inside."""
    near = [s for s in segs if box_gap(part.box, bbox(s)) <= limit]
    out = [p for poly in part.polys for p in (poly if near else poly[:1]) if not ps.Contains(pb.V(*p))]
    if out:
        d, p = max((min(seg_point(p, s, t)[0] for s, t in segs), p) for p in out)
        return -d, p, True
    if not near:
        return None, None, False
    best, at = math.inf, None
    for poly in part.polys:
        for s, t in near:
            for p, q in edges(poly):
                if seg_cross(s, t, p, q):     # an outline corner pokes into the part
                    k = cross(p, q, s) / (cross(p, q, s) - cross(p, q, t))
                    return 0.0, (s[0] + k * (t[0] - s[0]), s[1] + k * (t[1] - s[1])), True
            for p in poly:
                d, q = seg_point(p, s, t)
                if d < best:
                    best, at = d, q
            for e in (s, t):
                for p, q in edges(poly):
                    d, _ = seg_point(e, p, q)
                    if d < best:
                        best, at = d, e
    return (best if best < limit else None), at, False


def analyse(b, min_gap=0.2, edge=0.2, near=1.0, margin=0.25, min_hole=1.0, hole_margin=0.5, refs=None):
    """Spacing report for a loaded BOARD as a dict (see module docstring). refs limits the parts checked."""
    parts, sources, holes = {"F": [], "B": []}, Counter(), []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if is_hole(fp, min_hole):
            holes.append(ref)
            continue
        for side in "FB":
            polys, src = extent(fp, side, margin)
            if src:
                sources[src] += 1
            if polys:
                parts[side].append(make_part(ref, side, polys))
    pairs = []
    for side, items in parts.items():
        items.sort(key=lambda p: p.box[0])
        for i, a in enumerate(items):
            for c in items[i + 1:]:
                if c.box[0] > a.box[2] + near:
                    break
                if a.ref == c.ref or box_gap(a.box, c.box) >= near:
                    continue
                if refs and a.ref not in refs and c.ref not in refs:
                    continue
                g, at = part_gap(a, c, near)
                if g < near:
                    pairs.append({"side": side, "a": a.ref, "b": c.ref, "gap": round(g, 4),
                                  "at": [round(at[0], 3), round(at[1], 3)]})
    pairs.sort(key=lambda p: p["gap"])
    nearest = {}
    for p in pairs:
        for r in ("%s:%s" % (p["side"], p["a"]), "%s:%s" % (p["side"], p["b"])):
            nearest[r] = min(nearest.get(r, math.inf), p["gap"])

    ps, rings = board_outline(b)
    segs = [s for r in rings for s in edges(r)]
    edge_hits, edge_parts = [], []
    if ps is not None:
        edge_parts = sorted(fp.GetReference() for fp in b.GetFootprints() if castellated(fp, segs))
        for side, items in parts.items():
            for prt in items:
                if (refs and prt.ref not in refs) or prt.ref in edge_parts:
                    continue
                g, at, out = edge_gap(prt, ps, segs, edge)
                if out or (g is not None and g < edge - TOL):
                    edge_hits.append({"side": side, "ref": prt.ref, "gap": None if g is None else round(g, 4),
                                      "outside": out, "at": at and [round(at[0], 3), round(at[1], 3)]})
    keep_hits = []
    for name, sides, poly, convex, owner in keepouts(b, min_hole, hole_margin):
        kb = bbox(poly)
        for side in sides:
            for prt in parts[side]:
                if prt.ref == owner or (refs and prt.ref not in refs) or box_gap(prt.box, kb) > 0:
                    continue
                if any(fnmatch.fnmatch(prt.ref, pat) and fnmatch.fnmatch(name, "rule area " + ar)
                       for pat, ar in KEEPOUT_OWNERS):
                    continue                 # the area's own part (as the scoped DRU exemption, e.g. AE* antennas)
                if convex:
                    depth = max(penetration(q, poly) for q in prt.polys)
                    hit = depth > TOL
                else:
                    depth, hit = None, any(overlaps(q, poly) for q in prt.polys)
                if hit:
                    keep_hits.append({"side": side, "ref": prt.ref, "keepout": name,
                                      "depth": None if depth is None else round(depth, 4)})
    viol = [p for p in pairs if p["gap"] < min_gap - TOL]
    return {"min": min_gap, "edge": edge, "near": near, "parts": {s: len(v) for s, v in parts.items()},
            "body_source": dict(sources), "holes": holes, "violations": viol, "pairs": pairs,
            "nearest": nearest, "histogram": histogram([p["gap"] for p in pairs], near),
            "outline": ps is not None, "edge_hits": edge_hits, "edge_exempt": edge_parts, "keepout_hits": keep_hits,
            "ok": not (viol or edge_hits or keep_hits)}


def histogram(gaps, near):
    edges_ = [0.05 * i for i in range(11)] + [x for x in (0.75, 1.0, 1.5, 2.0, 3.0, 5.0) if x <= near]
    if edges_[-1] < near:
        edges_.append(near)
    rows = [["overlap", sum(1 for g in gaps if g < -TOL)]]
    for lo, hi in zip(edges_, edges_[1:]):
        if lo >= near:
            break
        rows.append(["%.2f-%.2f" % (lo, hi), sum(1 for g in gaps if lo - TOL <= g < hi - TOL)])
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board")
    ap.add_argument("--min", type=float, default=0.20, help="minimum package gap, mm")
    ap.add_argument("--edge", type=float, default=0.20, help="minimum package distance to the outline, mm")
    ap.add_argument("--near", type=float, default=1.0, help="neighbour pairs for the histogram, mm")
    ap.add_argument("--courtyard-margin", type=float, default=0.25)
    ap.add_argument("--min-hole", type=float, default=1.0)
    ap.add_argument("--hole-margin", type=float, default=0.5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keepout-owner", action="append", default=[],
                    help="REF:AREA fnmatch pair, e.g. 'AE*:RF_RX_*' (the part the rule area is drawn for)")
    ap.add_argument("--d70", action="store_true", help="D70: tented filled via pads (drill <= 0.25) are copper, not package extent")
    a = ap.parse_args(argv)
    global D70
    D70 = D70 or a.d70
    KEEPOUT_OWNERS.extend(tuple(x.split(":", 1)) for x in a.keepout_owner)
    try:
        if not os.path.isfile(a.board):
            raise IOError("no such file")
        b = pb.Board(a.board).b
    except Exception as e:                     # noqa: BLE001  (pcbnew raises plain IOError/RuntimeError)
        print("cannot read %s: %s" % (a.board, e), file=sys.stderr)
        return 2
    r = analyse(b, a.min, a.edge, max(a.near, a.min), a.courtyard_margin, a.min_hole, a.hole_margin)
    if a.json:
        print(json.dumps(r, indent=1))
        return 0 if r["ok"] else 1
    print("check_spacing: %s" % a.board)
    print("parts  F %d  B %d   body from %s   holes %s" % (r["parts"]["F"], r["parts"]["B"], ", ".join(
        "%s %d" % kv for kv in sorted(r["body_source"].items())), " ".join(r["holes"]) or "none"))
    print("\npairs below %.2f mm: %d" % (a.min, len(r["violations"])))
    for p in r["violations"]:
        print("  %s  %-6s %-6s %7.3f mm  at (%.2f, %.2f)" % (p["side"], p["a"], p["b"], p["gap"], *p["at"]))
    print("\ngap histogram, neighbour pairs closer than %.2f mm (%d):" % (r["near"], len(r["pairs"])))
    top = max([n for _, n in r["histogram"]] + [1])
    for label, n in r["histogram"]:
        print("  %-10s %4d %s" % (label, n, "#" * round(40 * n / top)))
    nn = sorted(r["nearest"].values())
    if nn:
        print("nearest neighbour per part: min %.3f  median %.3f mm" % (nn[0], nn[len(nn) // 2]))
    print("\nedge closer than %.2f mm: %s" % (a.edge, len(r["edge_hits"]) if r["outline"] else "no outline"))
    if r["edge_exempt"]:
        print("  exempt, plated hole cut by the outline: %s" % " ".join(r["edge_exempt"]))
    for e in r["edge_hits"]:
        where = "%.3f mm%s" % (e["gap"], "  (outside the outline)" if e["outside"] else "")
        print("  %s  %-6s %s%s" % (e["side"], e["ref"], where, "  at (%.2f, %.2f)" % tuple(e["at"]) if e["at"] else ""))
    print("\nkeepout overlaps: %d" % len(r["keepout_hits"]))
    for k in r["keepout_hits"]:
        print("  %s  %-6s %s%s" % (k["side"], k["ref"], k["keepout"], "" if k["depth"] is None else "  by %.3f mm" % k["depth"]))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
