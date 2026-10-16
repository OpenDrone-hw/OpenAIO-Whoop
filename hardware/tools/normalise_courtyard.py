#!/usr/bin/env python3
"""Rewrite a footprint's courtyard to max(body, lands) + margin, through pcbnew.

    $KPY hardware/tools/normalise_courtyard.py FOOTPRINT (--out LIB.pretty | --in-place)
                                               [--spec SPEC.json] [--margin 0.10] [--body W,H[,X,Y]]
                                               [--polygon] [--grid 0.01] [--width 0.05]
                                               [--sides auto|F|B|FB] [--project DIR] [--dry-run]

Runs under KiCad's Python (KPY, see AGENTS.md). FOOTPRINT is a .kicad_mod path
or Lib:Name (same resolution as check_footprint.py). The footprint is loaded
and saved with pcbnew's KiCad S-expression plugin (PCB_IO FootprintLoad /
FootprintSave); its text is never edited by hand.

Body, first of: --body, the spec's "body", the F.Fab outline's bounding box,
none (lands only, warned). Margin: --margin, else the spec's
"courtyard_margin", else 0.10 mm. Lands: every copper pad on that side.

  rectangle (default)  bounding box of body and lands, grown by the margin
  --polygon            rectilinear union of the body and each land's bounding
                       box, each grown by the margin, notches narrower than
                       0.30 mm bridged (hugs parts whose lands stick out on two
                       sides only, e.g. SON/SOT)

Corners snap OUTWARD to --grid (0.01 mm, KLC), so the result stays within
0.01 mm of the exact value. Every existing F.CrtYd and B.CrtYd item is
deleted first; --sides auto draws F.CrtYd, plus B.CrtYd only for lands that
exist on B.Cu alone. Line width --width (0.05 mm, KLC).

--out writes a copy into LIB.pretty (created if missing); --in-place writes
back into the source library (refused for /usr/share; warned for the shared
KiCad-Library submodule, whose fixes belong upstream). After saving, the
footprint is reloaded from disk and its courtyard re-checked with
check_footprint's courtyard rule.

Exit 0 on success, 1 if the re-check fails, 2 on usage or load/save errors.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_footprint as cf  # noqa: E402


def drop_collinear(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
            out.append(b)
    return out


def courtyard_geometry(body, lands, margin, grid, polygon):
    """List of point loops (mm) for one side."""
    boxes = [l["bbox"] for l in lands] + ([body] if body else [])
    if not boxes:
        return []
    if not polygon:
        x0, y0, x1, y1 = cf.snap_out(cf.grow_bbox(cf.bbox_union(boxes), margin), grid)
        return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    u = cf.rectilinear_hull(boxes, margin, grid)
    return [drop_collinear(cf.outline_points(u, i)) for i in range(u.OutlineCount())]


def parse_body(text):
    v = [float(t) for t in text.split(",")]
    if len(v) not in (2, 4):
        raise ValueError("--body wants W,H or W,H,X,Y")
    w, h = v[0], v[1]
    x, y = (v[2], v[3]) if len(v) == 4 else (0.0, 0.0)
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("footprint")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--out", help="write into this .pretty directory")
    g.add_argument("--in-place", action="store_true", help="write back into the source library")
    ap.add_argument("--spec", help="land-pattern spec JSON (body, courtyard_margin)")
    ap.add_argument("--margin", type=float)
    ap.add_argument("--body", help="W,H[,X,Y] in mm, package centre frame")
    ap.add_argument("--polygon", action="store_true", help="rectilinear polygon instead of a rectangle")
    ap.add_argument("--grid", type=float, default=0.01)
    ap.add_argument("--width", type=float, default=0.05)
    ap.add_argument("--sides", default="auto", choices=("auto", "F", "B", "FB"))
    ap.add_argument("--project", default=cf.DEFAULT_PROJECT)
    ap.add_argument("--dry-run", action="store_true", help="compute and report, do not save")
    a = ap.parse_args(argv)

    P = cf.import_pcbnew()
    try:
        spec = cf.load_spec(a.spec) if a.spec else {}
        lib_dir, name, _ = cf.resolve_footprint(a.footprint, a.project)
        fp = cf.load_footprint(lib_dir, name)
    except (OSError, ValueError) as e:
        print(f"normalise_courtyard: {e}", file=sys.stderr)
        return 2

    if a.body:
        body, body_src = parse_body(a.body), "--body"
    elif spec.get("body"):
        body, body_src = cf.spec_body(spec), "spec"
    else:
        body, body_src = cf.fab_body_bbox(fp), "F.Fab"
        if body is None:
            body_src = "none (lands only)"
    margin = a.margin if a.margin is not None else float(spec.get("courtyard_margin", 0.10))

    lands, _ = cf.pad_records(fp)
    front = [l for l in lands if l["side"] == "F"]
    back_only = [l for l in lands if l["side"] == "B" and not l["pad"].GetLayerSet().Contains(P.F_Cu)]
    if a.sides == "auto":
        sides = (["F"] if front or not back_only else []) + (["B"] if back_only else [])
    else:
        sides = list(a.sides)

    old = [gi for gi in fp.GraphicalItems()
           if isinstance(gi, P.PCB_SHAPE) and gi.GetLayer() in (P.F_CrtYd, P.B_CrtYd)]
    old_f = cf.courtyard_poly(fp, P.F_CrtYd)[0]
    before = cf.bbox(old_f) if old_f is not None else None

    drawn = []
    for side in sides:
        sl = front if side == "F" else (back_only or lands)
        loops = courtyard_geometry(body, sl, margin, a.grid, a.polygon)
        layer = P.F_CrtYd if side == "F" else P.B_CrtYd
        for loop in loops:
            if len(loop) == 4 and not a.polygon:
                sh = P.PCB_SHAPE(fp, P.SHAPE_T_RECT)
                sh.SetStart(P.VECTOR2I(cf.nm(loop[0][0]), cf.nm(loop[0][1])))
                sh.SetEnd(P.VECTOR2I(cf.nm(loop[2][0]), cf.nm(loop[2][1])))
            else:
                sh = P.PCB_SHAPE(fp, P.SHAPE_T_POLY)
                sh.SetPolyShape(cf.poly_from_points(loop))
            sh.SetLayer(layer)
            sh.SetWidth(cf.nm(a.width))
            sh.SetFilled(False)
            drawn.append((side, sh, loop))

    bx = cf.bbox_union([cf.pts_bbox(l) for _, _, l in drawn]) if drawn else None
    print(f"normalise_courtyard: {name}  body {body_src}, margin {margin:.2f}, "
          f"{'polygon' if a.polygon else 'rectangle'}, sides {''.join(sides)}")
    print(f"  before: {len(old)} courtyard items"
          + (f", F.CrtYd {before[2]-before[0]:.3f} x {before[3]-before[1]:.3f}" if before else ", no F.CrtYd"))
    if bx:
        npts = sum(len(l) for _, _, l in drawn)
        print(f"  after : {len(drawn)} shapes ({npts} corners), {bx[2]-bx[0]:.3f} x {bx[3]-bx[1]:.3f} "
              f"[{bx[0]:+.3f} {bx[1]:+.3f} {bx[2]:+.3f} {bx[3]:+.3f}]")
    if a.dry_run:
        return 0

    for gi in old:
        fp.Delete(gi)
    for _, sh, _ in drawn:
        fp.Add(sh)

    if a.in_place:
        target = lib_dir
        if os.path.realpath(target).startswith("/usr/"):
            print("normalise_courtyard: refusing to write into a system library", file=sys.stderr)
            return 2
        if "KiCad-Library" in os.path.realpath(target):
            print("  WARN  writing into the shared KiCad-Library submodule: send the fix upstream too")
    else:
        target = os.path.abspath(a.out)
    io = cf.kicad_io()
    try:
        os.makedirs(target, exist_ok=True)       # an empty .pretty directory is a valid library
        with cf.quiet_stderr():
            io.FootprintSave(target, fp)
    except Exception as e:  # pcbnew raises IO_ERROR as RuntimeError
        print(f"normalise_courtyard: save failed: {e}", file=sys.stderr)
        return 2

    # re-check from disk with the checker's courtyard rule
    fp2 = cf.load_footprint(target, name)
    lands2, _ = cf.pad_records(fp2)
    ok, text, _, notes = cf.courtyard_status(fp2, body, lands2, margin, 0.01)
    print(f"  saved : {os.path.join(target, name + '.kicad_mod')}")
    print(f"  {'ok  ' if ok else 'FAIL'} {text}")
    for n in notes:
        print(f"  WARN {n}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
