#!/usr/bin/python3.12
"""Prototype: before/after review pack for a KiCad 10 board (pcbnew SWIG + PIL).

    board_diff.py OLD.kicad_pcb NEW.kicad_pcb OUTDIR [px_per_mm]

Footprints keyed by uuid, then by reference (sync_pcb/floorplan re-loads give new uuids).
Writes OUTDIR/diff-top.png, diff-bottom.png (courtyards + pads, red = old place / removed,
amber = new place / changed, green = added, grey = unchanged) and OUTDIR/changes.txt.
"""
import os
import sys
import pcbnew as P
from PIL import Image, ImageDraw

MM = 1e6


def fps(path):
    b = P.LoadBoard(path)
    out = {}
    for fp in b.GetFootprints():
        pos = fp.GetPosition()
        cy = fp.GetCourtyard(P.B_CrtYd if fp.IsFlipped() else P.F_CrtYd)
        polys = []
        for i in range(cy.OutlineCount()):
            o = cy.Outline(i)
            polys.append([(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())])
        pads = []
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            pads.append((bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM))
        out[fp.m_Uuid.AsString()] = dict(
            ref=fp.GetReference(), fpid=fp.GetFPIDAsString(), x=pos.x / MM, y=pos.y / MM,
            rot=fp.GetOrientationDegrees(), side="B" if fp.IsFlipped() else "F", cy=polys, pads=pads)
    edge = b.GetBoardEdgesBoundingBox()
    box = (edge.GetLeft() / MM, edge.GetTop() / MM, edge.GetRight() / MM, edge.GetBottom() / MM)
    counts = dict(tracks=sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"),
                  vias=sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA"),
                  zones=b.GetAreaCount(), footprints=len(out))
    return out, box, counts


def match(old, new):
    pairs, used = [], set()
    by_ref = {v["ref"]: k for k, v in new.items()}
    for k, o in old.items():
        if k in new:
            pairs.append((o, new[k])); used.add(k)
        elif o["ref"] in by_ref and by_ref[o["ref"]] not in old:
            pairs.append((o, new[by_ref[o["ref"]]])); used.add(by_ref[o["ref"]])
        else:
            pairs.append((o, None))
    pairs += [(None, v) for k, v in new.items() if k not in used]
    return pairs


def status(o, n):
    if n is None:
        return "removed", ""
    if o is None:
        return "added", ""
    what = []
    if o["fpid"] != n["fpid"]:
        what.append("footprint %s -> %s" % (o["fpid"], n["fpid"]))
    if o["side"] != n["side"]:
        what.append("side %s -> %s" % (o["side"], n["side"]))
    d = ((n["x"] - o["x"]) ** 2 + (n["y"] - o["y"]) ** 2) ** 0.5
    if d > 0.001:
        what.append("moved %.2f mm" % d)
    if abs((n["rot"] - o["rot"]) % 360) > 0.01:
        what.append("rot %g -> %g" % (o["rot"], n["rot"]))
    return ("changed" if what else "same"), ", ".join(what)


COL = dict(same=(110, 110, 120), removed=(230, 60, 60), changed=(255, 176, 0), added=(60, 200, 90), was=(230, 60, 60))


def draw(pairs, box, side, ppm, path):
    x0, y0, x1, y1 = box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1
    W, H = int((x1 - x0) * ppm), int((y1 - y0) * ppm)
    img = Image.new("RGB", (W, H), (22, 24, 28))
    d = ImageDraw.Draw(img)

    def tx(p):
        x = (p[0] - x0) * ppm
        return (W - x if side == "B" else x, (p[1] - y0) * ppm)   # bottom seen from below

    def one(f, kind, width=1):
        for poly in f["cy"]:
            if len(poly) > 2:
                d.polygon([tx(p) for p in poly], outline=COL[kind], width=width)
        if kind != "was":
            for a, b_, c, e in f["pads"]:
                q = sorted([tx((a, b_)), tx((c, e))])
                d.rectangle([q[0][0], min(q[0][1], q[1][1]), q[1][0], max(q[0][1], q[1][1])], fill=COL[kind])
    order = {"same": 0, "removed": 1, "changed": 2, "added": 3}
    for o, n, st, _ in sorted(pairs, key=lambda r: order[r[2]]):
        if st == "changed" and o["side"] == side:
            one(o, "was", 2)
        f = n if n is not None else o
        if f["side"] == side:
            one(f, st, 2 if st != "same" else 1)
    img.save(path)


def main():
    old, box, c0 = fps(sys.argv[1])
    new, box1, c1 = fps(sys.argv[2])
    out = sys.argv[3]
    ppm = float(sys.argv[4]) if len(sys.argv) > 4 else 40
    os.makedirs(out, exist_ok=True)
    rows = []
    for o, n in match(old, new):
        st, why = status(o, n)
        rows.append((o, n, st, why))
    box = (min(box[0], box1[0]), min(box[1], box1[1]), max(box[2], box1[2]), max(box[3], box1[3]))
    for s in "FB":
        draw(rows, box, s, ppm, os.path.join(out, "diff-%s.png" % ("top" if s == "F" else "bottom")))
    with open(os.path.join(out, "changes.txt"), "w") as fh:
        tally = {}
        for o, n, st, why in rows:
            tally[st] = tally.get(st, 0) + 1
        fh.write("footprints: %s\n" % ", ".join("%s %d" % kv for kv in sorted(tally.items())))
        fh.write("counts old %s\ncounts new %s\n" % (c0, c1))
        for o, n, st, why in sorted(rows, key=lambda r: (r[0] or r[1])["ref"]):
            if st != "same":
                f = n or o
                fh.write("%-8s %-7s %s %s\n" % (f["ref"], st, f["side"], why))
    print(open(os.path.join(out, "changes.txt")).read().splitlines()[0])


if __name__ == "__main__":
    main()
