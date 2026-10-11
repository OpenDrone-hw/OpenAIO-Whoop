#!/usr/bin/env python3
"""Exercise layer and HDI rules on a disposable board using the real KiCad DRC.

Run with KiCad's Python. The source board is never changed. Passing requires
both rejection of forbidden objects and acceptance of legal counterparts.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pcbnew as pcb


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("board", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    source = args.board.resolve()
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or \
        "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    tests = [
        ("L2 digital", "track", "/SPI0_SCK", pcb.In1_Cu, True),
        ("L2 gate", "track", "/ESC1/A_PWM", pcb.In1_Cu, True),
        ("L2 video", "track", "/OSD/VIDEO_IN", pcb.In1_Cu, False),
        ("L2 RF", "track", "/VTX/RF_PA_IN", pcb.In1_Cu, False),
        ("L2 GND zone", "zone", "GND", pcb.In1_Cu, True),
        ("L2 battery zone", "zone", "+BATT", pcb.In1_Cu, False),
        ("L5 phase zone", "zone", "/ESC1/PHASE_A", pcb.In4_Cu, False),
        ("L5 GND zone", "zone", "GND", pcb.In4_Cu, True),
        ("L5 gate escape", "track", "/ESC1/A_PWM", pcb.In4_Cu, True),
        ("L5 BEMF escape", "track", "/ESC1/BEMF_A", pcb.In4_Cu, True),
        ("L5 DShot", "track", "/ESC1/RTX", pcb.In4_Cu, True),
        ("L5 phase track", "track", "/ESC1/PHASE_A", pcb.In4_Cu, False),
        ("L3 gate", "track", "/ESC1/A_PWM", pcb.In2_Cu, False),
        ("L3 GND track", "track", "GND", pcb.In2_Cu, False),
        ("L3 GND zone", "zone", "GND", pcb.In2_Cu, True),
        ("L3 battery zone", "zone", "+BATT", pcb.In2_Cu, False),
        ("L4 gate", "track", "/ESC1/A_PWM", pcb.In3_Cu, False),
        ("L3 analog zone", "zone", "/OSD/VIDEO_IN", pcb.In2_Cu, False),
        ("L2 gyro", "track", "/SPI1_SCK", pcb.In1_Cu, True),
        ("L3 gyro", "track", "/SPI1_SCK", pcb.In2_Cu, False),
        ("L4 gyro", "track", "/SPI1_SCK", pcb.In3_Cu, False),
        ("L4 battery zone", "zone", "+BATT", pcb.In3_Cu, True),
        ("L4 regulated supply", "track", "+3.3V", pcb.In3_Cu, True),
        ("L4 switch node", "track", "/RP2350A/VREG_LX", pcb.In3_Cu, False),
        ("RF PA-input via", "micro", "/VTX/RF_PA_IN", (pcb.F_Cu, pcb.In1_Cu), False),
        ("top laser", "micro", "GND", (pcb.F_Cu, pcb.In1_Cu), True),
        ("bottom laser", "micro", "GND", (pcb.In4_Cu, pcb.B_Cu), True),
        ("illegal long laser", "micro", "GND", (pcb.F_Cu, pcb.In4_Cu), False),
        ("buried core", "buried", "GND", (pcb.In1_Cu, pcb.In4_Cu), True),
        ("illegal blind", "blind", "GND", (pcb.F_Cu, pcb.In4_Cu), False),
        ("through via", "through", "GND", (pcb.F_Cu, pcb.B_Cu), False),
    ]
    board = pcb.BOARD()
    board.SetCopperLayerCount(6)
    nets = {}
    objects = []
    for index, (name, kind, netname, layer, allowed) in enumerate(tests):
        if netname not in nets:
            nets[netname] = pcb.NETINFO_ITEM(board, netname)
            board.Add(nets[netname])
        x, y = 10 + index % 7 * 10, 10 + index // 7 * 10
        pos = lambda dx, dy: pcb.VECTOR2I(pcb.FromMM(x + dx), pcb.FromMM(y + dy))
        if kind == "track":
            item = pcb.PCB_TRACK(board)
            item.SetStart(pos(0, 0)); item.SetEnd(pos(2, 0))
            item.SetWidth(pcb.FromMM(0.1)); item.SetLayer(layer)
        elif kind == "zone":
            item = pcb.ZONE(board); item.SetLayer(layer)
            outline = item.Outline(); outline.NewOutline()
            for dx, dy in [(0, 0), (2, 0), (2, 2), (0, 2)]:
                p = pos(dx, dy); outline.Append(p.x, p.y)
        else:
            item = pcb.PCB_VIA(board); item.SetPosition(pos(0, 0))
            item.SetViaType({"micro": pcb.VIATYPE_MICROVIA,
                             "buried": pcb.VIATYPE_BURIED,
                             "blind": pcb.VIATYPE_BLIND,
                             "through": pcb.VIATYPE_THROUGH}[kind])
            item.SetLayerPair(*layer)
            item.SetWidth(pcb.FromMM(0.25 if kind == "micro" else 0.35))
            item.SetDrill(pcb.FromMM(0.10 if kind == "micro" else 0.15))
        item.SetNet(nets[netname]); board.Add(item)
        objects.append((name, str(item.m_Uuid.AsString()), allowed))
    stacked_ids = set()
    for kind, layers, width, drill in [
            (pcb.VIATYPE_MICROVIA, (pcb.F_Cu, pcb.In1_Cu), 0.25, 0.10),
            (pcb.VIATYPE_BURIED, (pcb.In1_Cu, pcb.In4_Cu), 0.35, 0.15)]:
        item = pcb.PCB_VIA(board)
        item.SetPosition(pcb.VECTOR2I(pcb.FromMM(10), pcb.FromMM(50)))
        item.SetViaType(kind); item.SetLayerPair(*layers)
        item.SetWidth(pcb.FromMM(width)); item.SetDrill(pcb.FromMM(drill))
        item.SetNet(nets["GND"]); board.Add(item)
        stacked_ids.add(str(item.m_Uuid.AsString()))
    with tempfile.TemporaryDirectory(prefix="whoop-rule-behavior-") as temp:
        path = Path(temp) / "probe.kicad_pcb"
        pcb.SaveBoard(str(path), board)
        for suffix in (".kicad_pro", ".kicad_dru"):
            shutil.copy2(source.with_suffix(suffix), path.with_suffix(suffix))
        report = Path(temp) / "drc.json"
        run = subprocess.run([cli, "pcb", "drc", "--format", "json", "-o",
                              str(report), str(path)], capture_output=True, text=True, timeout=120)
        if run.returncode or not report.is_file():
            print(run.stdout + run.stderr)
            raise SystemExit("FAIL: rule behavior probe did not complete")
        drc = json.loads(report.read_text())
    disallowed = {item["uuid"] for v in drc["violations"]
                  if v["type"] == "items_not_allowed" and v["severity"] == "error"
                  for item in v["items"]}
    result = [{"case": name, "expected_allowed": allowed,
               "rejected": uuid in disallowed, "pass": allowed == (uuid not in disallowed)}
              for name, uuid, allowed in objects]
    stacked_rejected = any(v["type"] == "holes_co_located" and v["severity"] == "error"
                           and stacked_ids.issubset({i["uuid"] for i in v["items"]})
                           for v in drc["violations"])
    result.append({"case": "stacked laser and buried drills", "expected_allowed": False,
                   "rejected": stacked_rejected, "pass": stacked_rejected})
    if args.report:
        args.report.write_text(json.dumps({"cases": result, "drc": drc}, indent=2) + "\n")
    for row in result:
        print(("ok  " if row["pass"] else "FAIL"), row["case"])
    return 0 if all(row["pass"] for row in result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
