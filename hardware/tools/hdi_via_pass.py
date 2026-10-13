"""Convert vias placed while routing into buildable HDI 1+6+1 stacks.

Run with KiCad closed, using KiCad's bundled Python:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
      hardware/tools/hdi_via_pass.py hardware/<board>.kicad_pcb [--allow-through] [--dry-run]

A via is kept when it is a microvia F.Cu-In1.Cu or In6.Cu-B.Cu, a buried via In1.Cu-In6.Cu,
or (with --allow-through) a through via. Every other via is replaced at the same position by
the smallest stack that joins the layers its tracks and pads use: microvia F.Cu-In1.Cu,
buried In1.Cu-In6.Cu, microvia In6.Cu-B.Cu. Sizes come from the board's net class
(read from the .kicad_pro, microvia and via size). Where the new stack is closer than the copper clearance to other-net
copper, it is moved up to 0.05 mm together with its track ends; larger conflicts are listed
and left for the owner. The script prints a report and saves the board unless --dry-run.
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


def legal(v, allow_through):
    t, top, bot = v.GetViaType(), v.TopLayer(), v.BottomLayer()
    if t == pcbnew.VIATYPE_MICROVIA:
        return (top, bot) in ((F, I1), (I6, B))
    if t == pcbnew.VIATYPE_BURIED:
        return (top, bot) == (I1, I6)
    if t == pcbnew.VIATYPE_THROUGH:
        return allow_through
    return False


def used_layers(board, v, tracks):
    p, r, layers = v.GetPosition(), v.GetWidth(F) // 2, set()
    for t in tracks:
        if t.GetNetCode() == v.GetNetCode() and any((e - p).EuclideanNorm() <= r for e in (t.GetStart(), t.GetEnd())):
            layers.add(t.GetLayer())
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == v.GetNetCode() and pad.HitTest(p):
                layers.add(B if fp.IsFlipped() else F)
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
    bad = [v for v in vias if not legal(v, allow_through)]
    print(f"{len(vias)} vias, {len(bad)} to convert")
    left = []
    for v in bad:
        pos, net = v.GetPosition(), v.GetNet()
        cls = classes.get(v.GetNetClassName(), classes["Default"])
        micro = (pcbnew.FromMM(cls["microvia_diameter"]), pcbnew.FromMM(cls["microvia_drill"]))
        mech = (pcbnew.FromMM(cls["via_diameter"]), pcbnew.FromMM(cls["via_drill"]))
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
    for item in left:
        print("OWNER:", item)
    if not dry:
        pcbnew.SaveBoard(path, board)
        print("saved")


if __name__ == "__main__":
    main()
