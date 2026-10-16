#!/usr/bin/python3.12
"""Pad-function silk labels that the routing / placement checkpoints keep losing (P4 critique r3 + r4, B7 / B9).

    /usr/bin/python3.12 hardware/tools/silk_pad_labels.py BOARD.kicad_pcb [--dry] [--check]

The one table for these labels (commons rule: pad Value = silk = pinout = docs): the LED / buzzer row J22 J21 J20
J33 (top to bottom) gets one label per pad, its pad Value (BZ- 5V LED GND), aligned with the pad centre; the J13
motor land gets 'M4' like M1-M3. Every label is checked against F pads (0.15 mm from mask openings), other F silk
(0.10), Edge.Cuts and open holes (0.20). Idempotent; writes through a temp folder and copies only the .kicad_pcb.

--check   write nothing; exit 1 when a label is missing or sits off its pad (the promote gate).

PROMOTE GATE (FLOORPLAN.md open item 6): every write of hardware/OpenAIO-Whoop.kicad_pcb from a checkpoint runs
this script on the checkpoint first, then hardware/tools/check_conventions.py, and copies only with B7 and B9 ok.
(Checkpoints made before 2026-10-10 03:03, e.g. route ckpt/28_candidate, lack the labels.)"""
import math, os, shutil, sys, tempfile
import pcbnew
P = sys.argv[1]
DRY = "--dry" in sys.argv or "--check" in sys.argv
CHECK = "--check" in sys.argv
b = pcbnew.LoadBoard(P)
mm, MM = pcbnew.FromMM, pcbnew.ToMM
FP = {f.GetReference(): f for f in b.GetFootprints()}
MASK = MM(b.GetDesignSettings().m_SolderMaskExpansion)
ROW = ["J22", "J21", "J20", "J33"]                       # top to bottom: BZ- 5V LED GND (FLOORPLAN v3 step 5)
# J33 GND: no site keeps 0.15 mm from U6's tented, filled+capped EP via ring at (112.425, 120.125) (B-side part, no F
# mask opening) and 0.15 mm from the D7 / J33 mask openings; a kicad-cli DRC sweep over the label x gave a maximum of
# 0.148 mm at ink right edge 112.445 (one silk_overlap warning, accepted: nothing to clip on a tented via)
FALLBACK = {"J33": (-0.045, 0.0)}


def ink(t):
    bb = t.GetEffectiveTextShape().BBox()
    return [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())]


def box_gap(a, c):
    dx = max(0, max(a[0], c[0]) - min(a[2], c[2])); dy = max(0, max(a[1], c[1]) - min(a[3], c[3]))
    return math.hypot(dx, dy)


def bbox(item):
    bb = item.GetBoundingBox()
    return [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())]


silk = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_SilkS]
pads = {r: FP[r].Pads()[0] for r in ROW}
col_x0 = min(bbox(p)[0] for p in pads.values())
ys = [MM(p.GetPosition().y) for p in pads.values()]
old = [t for t in silk if ink(t)[2] <= col_x0 and min(ys) - 1.0 <= (ink(t)[1] + ink(t)[3]) / 2 <= max(ys) + 1.0
       and col_x0 - ink(t)[2] < 1.0]
want = {FP[r].GetValue(): MM(pads[r].GetPosition().y) for r in ROW}
span = {FP[r].GetValue(): (bbox(pads[r])[1], bbox(pads[r])[3]) for r in ROW}
done = all(any(t.GetText() == code and lo <= (ink(t)[1] + ink(t)[3]) / 2 <= hi and ink(t)[2] <= col_x0 for t in old)
           for code, (lo, hi) in span.items()) and len(old) == len(want)
style = old[0] if old else silk[0]
STY = (style.GetTextHeight(), style.GetTextWidth(), style.GetTextThickness())   # read before any Delete()
new = []


def make(text, x, y, just):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextHeight(STY[0]); t.SetTextWidth(STY[1])
    t.SetTextThickness(STY[2])
    t.SetHorizJustify(just); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetTextAngleDegrees(0)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    return t


ERR = mm(0.002)


def poly(item, layer, grow=0.0):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, mm(grow), ERR, pcbnew.ERROR_OUTSIDE)
    return ps


def hits(a, c):
    x = pcbnew.SHAPE_POLY_SET(a)
    x.BooleanIntersection(c)
    return x.OutlineCount() > 0 and x.Area() > 1e3            # > 0.001 mm2 in nm2 units


PADS_F = [(f, p) for f in b.GetFootprints() for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu)]


def pad_conflicts(t, gap=0.15):
    """(name, hard) for every F pad copper (plus mask expansion where it has an opening) closer than `gap` to the text
    strokes (KiCad rule 'silkscreen over pad'); hard = a solderable pad (front mask opening), soft = a tented
    filled+capped via-in-pad ring of a B-side part."""
    e = ink(t)
    tp = poly(t, pcbnew.F_SilkS, gap)
    out = []
    for f, p in PADS_F:
        pb = bbox(p)
        if box_gap(e, pb) > gap + 0.1:
            continue
        hard = p.IsOnLayer(pcbnew.F_Mask)
        pp = poly(p, pcbnew.F_Cu, MASK if hard else 0.0)
        if hits(tp, pp):
            out.append(("pad %s.%s" % (f.GetReference(), p.GetNumber()), hard))
    return out


if CHECK:
    m4 = any(t.GetText() == "M4" for t in silk)
    print("silk_pad_labels --check: LED row %s, M4 %s" % ("ok" if done else "MISSING/MISALIGNED", "ok" if m4 else "MISSING"))
    sys.exit(0 if done and m4 else 1)
report = []
if not done:
    for t in old:
        report.append("remove %r at (%.2f, %.2f)" % (t.GetText(), MM(t.GetPosition().x), MM(t.GetPosition().y)))
    right = col_x0 - MASK - 0.15 - 0.02                    # ink right edge: 0.15 mm from the pad mask opening
    placed = []
    for r in ROW:
        code, y = FP[r].GetValue(), MM(pads[r].GetPosition().y)
        py0, py1 = bbox(pads[r])[1], bbox(pads[r])[3]
        t = make(code, right, y, pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        e = ink(t)
        x0, y0 = right + (right - e[2]), y + (y - (e[1] + e[3]) / 2)
        # stay on the pad's span and 0.10 from the other labels; 0.15 from every F pad (KiCad 'silkscreen over pad');
        # if no such site exists, use the swept fallback (FALLBACK) and report the tented via ring it is near
        site = None
        for dy in [0] + [k * 0.05 * sg for k in range(1, 7) for sg in (1, -1)]:
            for dx in [-k * 0.01 for k in range(0, 31)]:
                t.SetPosition(pcbnew.VECTOR2I(mm(x0 + dx), mm(y0 + dy)))
                e = ink(t)
                if not (py0 <= (e[1] + e[3]) / 2 <= py1) or any(box_gap(e, ink(o)) < 0.1 for o in placed):
                    continue
                if not pad_conflicts(t):
                    site = (dx, dy)
                    break
            if site:
                break
        site = site or FALLBACK.get(r, (0.0, 0.0))
        t.SetPosition(pcbnew.VECTOR2I(mm(x0 + site[0]), mm(y0 + site[1])))
        placed.append(t)
        new.append((r, t))
if not any(t.GetText() == "M4" for t in silk):
    j = FP["J13"]
    t = make("M4", 103.0, 101.6, pcbnew.GR_TEXT_H_ALIGN_CENTER)   # free strip between the ear hole and pad 3
    new.append(("J13", t))
# clearance check of every new label
others = [t for t in silk if t not in old]
# open holes only: NPTH and drilled pads with a front mask opening; tented filled+capped via-in-pad drills (EP vias, D67
# test vias) are covered on F and take silk like the existing labels do
holes = [(MM(p.GetPosition().x), MM(p.GetPosition().y), MM(p.GetDrillSize().x) / 2) for f in b.GetFootprints()
         for p in f.Pads() if p.GetDrillSize().x > 0 and (p.IsOnLayer(pcbnew.F_Mask) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH)]
edges = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
bad = 0
for owner, t in new:
    e = ink(t)
    pc = pad_conflicts(t)
    worst = [c[0] for c in pc if c[1]]
    soft = [c[0] for c in pc if not c[1]]
    for o in others + [x for _, x in new if x is not t]:
        g = box_gap(e, ink(o))
        if g < 0.1:
            worst.append("silk %r %.2f" % (o.GetText(), g))
    for hx, hy, hr in holes:
        cx, cy = min(max(hx, e[0]), e[2]), min(max(hy, e[1]), e[3])
        if math.hypot(cx - hx, cy - hy) - hr < 0.2:
            worst.append("hole %.2f" % (math.hypot(cx - hx, cy - hy) - hr))
    for d in edges:
        sh = d.GetEffectiveShape()
        corners = [pcbnew.VECTOR2I(mm(x), mm(y)) for x in (e[0], e[2]) for y in (e[1], e[3])]
        rect = pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(mm(e[0]), mm(e[1])), mm(e[2] - e[0]), mm(e[3] - e[1]))
        if sh.Collide(rect, mm(0.2)):
            worst.append("edge < 0.2")
    bad += bool(worst)
    report.append("%s %r ink x %.2f-%.2f y %.2f-%.2f%s%s" % (owner, t.GetText(), e[0], e[2], e[1], e[3],
                  ("  CONFLICT " + ", ".join(worst)) if worst else "  clear",
                  ("  (over tented via-in-pad ring: " + ", ".join(soft) + ")") if soft else ""))
print("\n".join(report) or "silk_pad_labels: nothing to do")
if bad:
    sys.exit("silk_pad_labels: %d label(s) in conflict, board not written" % bad)
if new and not DRY:
    if not done:
        for t in old:
            b.Delete(t)
    for _, t in new:
        b.Add(t)
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, os.path.basename(P))
    b.Save(out)
    shutil.copyfile(out, P)
    print("silk_pad_labels: %d label(s) written to %s" % (len(new), P))
