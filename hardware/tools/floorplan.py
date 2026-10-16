#!/usr/bin/env python3
"""Area budget and a rough first packing for a floorplan.

    $KPY hardware/tools/floorplan.py plan.json [--place] [--write | -o OUT.kicad_pcb] [--json]

Runs under KiCad's Python (KPY, see AGENTS.md). The plan, paths relative to it,
coordinates in board mm (+y down):

    {"board": "OpenAIO-Whoop.kicad_pcb", "gap": 0.2,
     "regions": {"mcu": {"side": "F", "poly": [[x, y], ...]}, ...},
     "parts": [{"ref": "U1", "footprint": "OpenDrone:QFN-60_L7.0-W7.0-P0.40-TL-EP3.4",
                "region": "mcu"}, ...]}

Optional per part: "side" (must match the region's), "rot" (rotations to try,
default [0, 90]), "value" (for a footprint created here). A ref already on the
board keeps its footprint (a floorplan never reassigns one; a mismatch is
reported). Any other ref is loaded from the project's fp-lib-table, with
${KIPRJMOD} and project text variables such as ${OPENDRONE_LIB} resolved. It
gets no symbol path, so sync_pcb.py relinks it by reference later.

Each part's extent is check_spacing.py's package extent (body and pads) on its
side, as an axis-aligned box inflated by gap/2 on every side. Boxes that touch
are gap apart, and parts sit gap/2 inside their region.

Budget: per region and per side, the sum of package hulls and of inflated boxes
against the region area (utilisation %), and per side against the board outline.

--place packs each region greedily, largest box first. Candidate corners are the
region's vertices and edge crossings and the edges of boxes already placed,
tried top to bottom and left to right for every allowed rotation. The lowest
bottom edge wins, then the box slides up and left. Obstacles are footprints
on the board that the plan does not list (place connectors and holes first),
locked plan parts, mounting-hole keepouts and footprint keepout rule areas.
Parts that do not fit are reported. New ones are parked right of the outline,
existing ones are left where they were. The result is checked with
check_spacing.analyse(). The board is written to <board>-floorplan.kicad_pcb
(SaveBoard writes the matching .kicad_pro too) or to -o. Only --write
overwrites the input board.

Exit 0 when everything fits (or without --place), 1 when a part did not fit or
the spacing check fails, 2 on a bad plan.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_spacing as cs  # noqa: E402
import pcb_build as pb  # noqa: E402
import sync_pcb  # noqa: E402  (fp-lib-table and text variable resolution)

P = pb.P
EPS = 1e-6


def load_plan(path):
    plan = json.load(open(path, encoding="utf-8"))
    plan["board"] = os.path.join(os.path.dirname(os.path.abspath(path)), plan["board"])
    if not os.path.isfile(plan["board"]):
        raise ValueError("no board %s" % plan["board"])
    plan.setdefault("gap", 0.2)
    regions = plan["regions"]
    for name, r in regions.items():
        if r.get("side") not in ("F", "B") or len(r.get("poly", [])) < 3:
            raise ValueError("region %s needs side F|B and a poly of 3+ points" % name)
        r["poly"] = [tuple(map(float, p)) for p in r["poly"]]
    refs = set()
    for p in plan["parts"]:
        if p["ref"] in refs:
            raise ValueError("%s listed twice" % p["ref"])
        refs.add(p["ref"])
        if p.get("region") not in regions:
            raise ValueError("%s: unknown region %r" % (p["ref"], p.get("region")))
        side = regions[p["region"]]["side"]
        if p.setdefault("side", side) != side:
            raise ValueError("%s: side %s but region %s is on %s" % (p["ref"], p["side"], p["region"], side))
        p["rot"] = [float(a) for a in p.get("rot", [0, 90])]
    return plan


def libraries(board_path):
    d = os.path.dirname(board_path)
    tv = sync_pcb.text_vars(os.path.splitext(board_path)[0] + ".kicad_pro")
    return sync_pcb.fp_lib_paths(d, {k: v.replace("${KIPRJMOD}", d) for k, v in tv.items()})


def ensure(brd, libs, part, notes):
    """The plan part's footprint on the board, created from the library when missing: (fp, created)."""
    fp, want = brd.b.FindFootprintByReference(part["ref"]), part.get("footprint")
    if fp is not None:
        if want and fp.GetFPIDAsString() != want:
            notes.append("%s: board has %s, plan says %s; kept the board's" % (part["ref"], fp.GetFPIDAsString(), want))
        return fp, False
    if not want or ":" not in want:
        raise ValueError("%s is not on the board and has no Lib:Name footprint" % part["ref"])
    nick, name = want.split(":", 1)
    if nick not in libs:
        raise ValueError("%s: library %r not in fp-lib-table" % (part["ref"], nick))
    fp = P.FootprintLoad(libs[nick], name)
    if fp is None:
        raise ValueError("%s: footprint %s not found in %s" % (part["ref"], want, libs[nick]))
    fp.SetFPID(P.LIB_ID(nick, name))
    fp.SetReference(part["ref"])
    fp.SetValue(part.get("value", name))
    brd.b.Add(fp)                       # on the board before any Flip (orphan flips crash 10.0.6)
    return fp, True


def state(fp):
    x, y = pb.xy(fp.GetPosition())
    return x, y, fp.GetOrientationDegrees(), "B" if fp.IsFlipped() else "F", fp.IsLocked()


def measure(brd, ref, side, rot):
    """(extent box, package hull area, box of through-hole pads on the other side or None),
    relative to the footprint origin, at rotation rot on side."""
    fp = brd.place(ref, 0, 0, rot, side, lock=brd.fp(ref).IsLocked())
    pts = [p for q in cs.extent(fp, side)[0] for p in q]
    back = [p for q in cs.extent(fp, "B" if side == "F" else "F")[0] for p in q]
    return cs.bbox(pts), cs.area(cs.hull(pts)), cs.bbox(back) if back else None


def inflate(box, d):
    return (box[0] - d, box[1] - d, box[2] + d, box[3] + d)


def obstacles(b, side, skip, gap, region_box):
    """Inflated boxes of everything on this side that the packing must avoid."""
    out = []
    for fp in b.GetFootprints():
        if fp.GetReference() in skip or cs.is_hole(fp, 1.0):
            continue
        for q in cs.extent(fp, side)[0]:
            out.append(inflate(cs.bbox(q), gap / 2))
    for _, sides, poly, _, owner in cs.keepouts(b, 1.0, 0.5):
        if side in sides and owner not in skip:
            out.append(inflate(cs.bbox(poly), gap / 2))
    return [o for o in out if cs.box_gap(o, region_box) == 0]


# -- packing ----------------------------------------------------------------
def seg_hits_rect(a, b, r):
    """True when segment ab passes through the open rectangle r (Liang-Barsky)."""
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for p, q in ((-dx, a[0] - r[0]), (dx, r[2] - a[0]), (-dy, a[1] - r[1]), (dy, r[3] - a[1])):
        if p == 0:
            if q <= 0:
                return False
        elif p < 0:
            t0 = max(t0, q / p)
        else:
            t1 = min(t1, q / p)
    return t0 < t1


def free(r, boxes):
    return not any(r[0] < o[2] - EPS and o[0] < r[2] - EPS and r[1] < o[3] - EPS and o[1] < r[3] - EPS for o in boxes)


def fits(r, poly, placed):
    """Box r is inside the region and clear of every placed box."""
    if not free(r, placed):
        return False
    s = inflate(r, -EPS)
    if not all(cs.in_poly(c, poly) for c in ((s[0], s[1]), (s[2], s[1]), (s[2], s[3]), (s[0], s[3]))):
        return False
    return not any(seg_hits_rect(a, b, s) for a, b in cs.edges(poly))


def crossings(poly, *ys):
    """x where the region's edges cross the horizontal lines ys."""
    out = []
    for (x1, y1), (x2, y2) in cs.edges(poly):
        for y in ys:
            if min(y1, y2) <= y <= max(y1, y2) and y1 != y2:
                out.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return out


def first_fit(poly, rb, placed, w, h, ok, other=(), rel=None):
    """Top-most, then left-most position (x, y) of a w x h box where ok(x, y), or None.
    With rel, the edges of the other side's boxes give candidates too."""
    near = [(o[2] - rel[0], o[3] - rel[1]) for o in other] if rel else []
    for y in sorted({rb[1]} | {o[3] for o in placed} | {p[1] for p in poly} | {c[1] for c in near}):
        if y + h > rb[3] + EPS:
            break
        xs = {rb[0]} | {o[2] for o in placed} | {p[0] for p in poly} | {c[0] for c in near}
        xs |= set(crossings(poly, y, y + h, *[p[1] for p in poly if y < p[1] < y + h]))
        for x in sorted(xs):
            if x + w > rb[2] + EPS:
                break
            if ok(x, y):
                return x, y
    return None


def slide(x, y, ok, rb):
    """Move the box up, then left, as far as it stays valid (bisection keeps a valid end)."""
    for axis in (1, 0):
        lo, hi = rb[axis], (x, y)[axis]
        for _ in range(40):
            if hi - lo < 1e-7:
                break
            mid = (lo + hi) / 2
            if ok(*((mid, y) if axis == 0 else (x, mid))):
                hi = mid
            else:
                lo = mid
        x, y = (hi, y) if axis == 0 else (x, hi)
    return x, y


def shift(rel, x, y):
    return None if rel is None else (x + rel[0], y + rel[1], x + rel[2], y + rel[3])


def pack(poly, items, placed, other):
    """items: [(ref, {rot: (w, h, rel)})], largest first; rel is the box of the part's through-hole pads
    on the other side relative to its own box, checked against `other`.
    Returns ({ref: (x0, y0, rot)}, [refs that did not fit])."""
    rb, placed, other, done, unfit = cs.bbox(poly), list(placed), list(other), {}, []

    def valid(w, h, rel):
        return lambda x, y: fits((x, y, x + w, y + h), poly, placed) and (rel is None or free(shift(rel, x, y), other))
    for ref, sizes in items:
        best = None
        for rot, (w, h, rel) in sizes.items():
            at = first_fit(poly, rb, placed, w, h, valid(w, h, rel), other, rel)
            if at and (best is None or (at[1] + h, at[0]) < (best[1] + best[4], best[0])):
                best = (at[0], at[1], rot, w, h, rel)
        if best is None:
            unfit.append(ref)
            continue
        x, y, rot, w, h, rel = best
        x, y = slide(x, y, valid(w, h, rel), rb)
        placed.append((x, y, x + w, y + h))
        if rel is not None:
            other.append(shift(rel, x, y))
        done[ref] = (x, y, rot)
    return done, unfit


# -- main -------------------------------------------------------------------
def run(plan, place=False):
    brd = pb.Board(plan["board"])
    b, gap, notes = brd.b, plan["gap"], []
    libs = libraries(brd.path)
    orig, created, locked = {}, set(), set()
    for part in plan["parts"]:
        fp, new = ensure(brd, libs, part, notes)
        if new:
            created.add(part["ref"])
        else:
            orig[part["ref"]] = state(fp)
        if fp.IsLocked():
            locked.add(part["ref"])
            notes.append("%s: locked, left in place as an obstacle" % part["ref"])
    sizes, hulls, through = {}, {}, {}
    for part in plan["parts"]:
        ref = part["ref"]
        if ref in locked:
            continue
        sizes[ref], through[ref] = {}, {}
        for rot in part["rot"]:
            sizes[ref][rot], hulls[ref], through[ref][rot] = measure(brd, ref, part["side"], rot)
    for ref, s in orig.items():                  # measuring moved them; put them back
        brd.place(ref, s[0], s[1], s[2], s[3], lock=s[4])

    ps, _ = cs.board_outline(b)
    board_area = round(ps.Area() / 1e12, 2) if ps is not None else None
    budget = {"regions": {}, "sides": {}}
    for name, r in plan["regions"].items():
        refs = [p["ref"] for p in plan["parts"] if p["region"] == name and p["ref"] in sizes]
        boxes = [next(iter(sizes[ref].values())) for ref in refs]
        infl = sum((x1 - x0 + gap) * (y1 - y0 + gap) for x0, y0, x1, y1 in boxes)
        a = cs.area(r["poly"])
        budget["regions"][name] = {"side": r["side"], "area": round(a, 2), "parts": len(refs),
                                   "package": round(sum(hulls[x] for x in refs), 2), "inflated": round(infl, 2),
                                   "util": round(100 * infl / a, 1) if a else None}
        if ps is not None and not all(ps.Contains(pb.V(*p)) for p in r["poly"]):
            notes.append("region %s reaches outside the board outline" % name)
    for side in "FB":
        rs = [v for v in budget["regions"].values() if v["side"] == side]
        if rs:
            a, infl = sum(v["area"] for v in rs), sum(v["inflated"] for v in rs)
            budget["sides"][side] = {"regions": round(a, 2), "board": board_area, "parts": sum(v["parts"] for v in rs),
                                     "package": round(sum(v["package"] for v in rs), 2), "inflated": round(infl, 2),
                                     "util": round(100 * infl / a, 1) if a else None,
                                     "board_util": round(100 * infl / board_area, 1) if board_area else None}
    result = {"board": brd.path, "gap": gap, "budget": budget, "notes": notes}
    if not place:
        return brd, result

    movable = {p["ref"] for p in plan["parts"]} - locked
    placed, unfit = {}, []

    def item(ref):
        out = {}
        for rot, bx in sizes[ref].items():
            ob = through[ref][rot]          # through-hole pads also need room on the other side
            rel = ob and (ob[0] - bx[0], ob[1] - bx[1], ob[2] - bx[0] + gap, ob[3] - bx[1] + gap)
            out[rot] = (bx[2] - bx[0] + gap, bx[3] - bx[1] + gap, rel)
        return ref, out
    for name, r in plan["regions"].items():
        items = [item(p["ref"]) for p in plan["parts"] if p["region"] == name and p["ref"] in sizes]
        items.sort(key=lambda it: (-max(w * h for w, h, _ in it[1].values()), it[0]))
        # parts packed in earlier regions are obstacles too, so overlapping regions stay apart
        rb, todo = cs.bbox(r["poly"]), movable - set(placed)
        done, miss = pack(r["poly"], items, obstacles(b, r["side"], todo, gap, rb),
                          obstacles(b, "B" if r["side"] == "F" else "F", todo, gap, rb))
        for ref, (x, y, rot) in done.items():
            bx = sizes[ref][rot]
            brd.place(ref, x + gap / 2 - bx[0], y + gap / 2 - bx[1], rot, r["side"])
            placed[ref] = {"region": name, "x": round(x + gap / 2 - bx[0], 4), "y": round(y + gap / 2 - bx[1], 4),
                           "rot": rot, "side": r["side"]}
        unfit += [(ref, name) for ref in miss]
    _, top, right, _ = brd._edge_bbox() if ps is not None else (0, 0, 0, 0)
    for i, (ref, _) in enumerate(u for u in unfit if u[0] in created):
        brd.place(ref, right + 5 + (i % 6) * 6, top + (i // 6) * 6)       # parked off the board
    check = cs.analyse(b, min_gap=gap, edge=0.0, near=max(1.0, 2 * gap), refs=set(placed))
    gaps = [p["gap"] for p in check["pairs"]]          # every pair involves a placed part
    result.update(placed=placed, unfit=[{"ref": r, "region": n} for r, n in unfit],
                  check={"violations": check["violations"], "edge_hits": check["edge_hits"],
                         "keepout_hits": check["keepout_hits"], "min_gap": min(gaps) if gaps else None,
                         "ok": check["ok"]})
    return brd, result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plan")
    ap.add_argument("--place", action="store_true", help="pack the parts and write a board")
    ap.add_argument("--write", action="store_true", help="overwrite the input board")
    ap.add_argument("-o", "--output", help="board to write (default <board>-floorplan.kicad_pcb)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        plan = load_plan(a.plan)
        brd, r = run(plan, a.place)
    except (ValueError, KeyError, OSError) as e:
        print("floorplan: %s" % e, file=sys.stderr)
        return 2
    out = None
    if a.place:
        out = os.path.abspath(a.output) if a.output else plan["board"] if a.write else \
            os.path.splitext(plan["board"])[0] + "-floorplan.kicad_pcb"
        if os.path.realpath(out) == os.path.realpath(plan["board"]) and not a.write:
            print("floorplan: refusing to overwrite the input board without --write", file=sys.stderr)
            return 2
        brd.save(out)
        r["written"] = out
    bad = a.place and (r["unfit"] or not r["check"]["ok"])
    if a.json:
        print(json.dumps(r, indent=1))
        return 1 if bad else 0
    print("floorplan: %s  board %s  gap %.2f mm" % (a.plan, plan["board"], r["gap"]))
    print("\n%-12s side %9s %6s %12s %13s %7s" % ("region", "area mm2", "parts", "package mm2", "inflated mm2", "util %"))
    for name, v in r["budget"]["regions"].items():
        print("%-12s %-4s %9.1f %6d %12.1f %13.1f %7.1f" % (name, v["side"], v["area"], v["parts"], v["package"],
                                                          v["inflated"], v["util"] or 0))
    for side, v in r["budget"]["sides"].items():
        print("side %s: %d parts, package %.1f mm2, inflated %.1f mm2 = %.1f %% of its regions (%.1f mm2)%s" % (
            side, v["parts"], v["package"], v["inflated"], v["util"] or 0, v["regions"],
            ", %.1f %% of the board (%.1f mm2)" % (v["board_util"], v["board"]) if v["board"] else ""))
    for n in r["notes"]:
        print("note: " + n)
    if a.place:
        print("\nplaced %d of %d" % (len(r["placed"]), len(r["placed"]) + len(r["unfit"])))
        for u in r["unfit"]:
            print("  did not fit: %s in %s" % (u["ref"], u["region"]))
        c = r["check"]
        print("check_spacing on the placed parts: min gap %s, %d below %.2f mm, %d outside the outline, %d in keepouts" % (
            "%.3f mm" % c["min_gap"] if c["min_gap"] is not None else "-", len(c["violations"]), r["gap"],
            len(c["edge_hits"]), len(c["keepout_hits"])))
        print("wrote %s" % out)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
