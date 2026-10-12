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
        ("L2 sync digital", "track", "/OSD_SYNC", pcb.In1_Cu, True),
        ("L5 sync digital", "track", "/OSD_SYNC", pcb.In4_Cu, True),
        ("L3 sync forbidden", "track", "/OSD_SYNC", pcb.In2_Cu, False),
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
        ("sense ESC1 A", "track", "/ESC1/PHASE_A", pcb.In4_Cu, True),
        ("sense ESC1 B", "track", "/ESC1/PHASE_B", pcb.In4_Cu, True),
        ("sense ESC1 C", "track", "/ESC1/PHASE_C", pcb.In1_Cu, True),
        ("sense ESC4 A", "track", "/ESC4/PHASE_A", pcb.In1_Cu, True),
        ("sense wrong width", "track", "/ESC1/PHASE_A", pcb.In4_Cu, False),
        ("sense wrong net", "track", "/ESC1/PHASE_B", pcb.In4_Cu, False),
        ("sense outside area", "track", "/ESC1/PHASE_A", pcb.In4_Cu, False),
        ("sense wrong layer", "track", "/ESC1/PHASE_A", pcb.In1_Cu, False),
        ("sense B wrong layer", "track", "/ESC1/PHASE_B", pcb.In1_Cu, False),
        ("sense C wrong layer", "track", "/ESC1/PHASE_C", pcb.In4_Cu, False),
        ("sense phase zone", "zone", "/ESC1/PHASE_A", pcb.In4_Cu, False),
        ("OSD level bounded", "track", "/OSD/OSD_LVL", pcb.In1_Cu, True),
        ("OSD wrong width", "track", "/OSD/OSD_LVL", pcb.In1_Cu, False),
        ("OSD wrong net", "track", "/VIDEO_IN", pcb.In1_Cu, False),
        ("OSD outside area", "track", "/OSD/OSD_LVL", pcb.In1_Cu, False),
        ("OSD wrong layer", "track", "/OSD/OSD_LVL", pcb.In4_Cu, False),
        ("OSD analog zone", "zone", "/OSD/OSD_LVL", pcb.In1_Cu, False),
        ("PA detector In1", "track", "/PA_DET", pcb.In1_Cu, True),
        ("PA detector In4", "track", "/PA_DET", pcb.In4_Cu, True),
        ("PA wrong width", "track", "/PA_DET", pcb.In1_Cu, False),
        ("PA wrong net", "track", "/VIDEO_IN", pcb.In1_Cu, False),
        ("PA outside area", "track", "/PA_DET", pcb.In1_Cu, False),
        ("PA wrong layer", "track", "/PA_DET", pcb.In4_Cu, False),
        ("PA wrong area", "track", "/PA_DET", pcb.In1_Cu, False),
        ("PA analog zone", "zone", "/PA_DET", pcb.In1_Cu, False),
        ("HD bounded bridge", "track", "/HD_EN", pcb.In2_Cu, True),
        ("HD wrong width", "track", "/HD_EN", pcb.In2_Cu, False),
        ("HD wrong net", "track", "/UART0_TX", pcb.In2_Cu, False),
        ("HD outside area", "track", "/HD_EN", pcb.In2_Cu, False),
        ("HD wrong layer", "track", "/HD_EN", pcb.In3_Cu, False),
        ("HD signal zone", "zone", "/HD_EN", pcb.In2_Cu, False),
        ("UART bounded bridge", "track", "/UART0_TX", pcb.In2_Cu, True),
        ("UART wrong width", "track", "/UART0_TX", pcb.In2_Cu, False),
        ("UART wrong net", "track", "/UART0_RX", pcb.In2_Cu, False),
        ("UART outside area", "track", "/UART0_TX", pcb.In2_Cu, False),
        ("UART wrong layer", "track", "/UART0_TX", pcb.In3_Cu, False),
        ("UART signal zone", "zone", "/UART0_TX", pcb.In2_Cu, False),
        ("VIDEO bridge bounded", "track", "/VIDEO_IN", pcb.In1_Cu, True),
        ("VIDEO wrong width", "track", "/VIDEO_IN", pcb.In1_Cu, False),
        ("VIDEO wrong net", "track", "/OSD/VID_DC", pcb.In1_Cu, False),
        ("VIDEO outside area", "track", "/VIDEO_IN", pcb.In1_Cu, False),
        ("VIDEO wrong layer", "track", "/VIDEO_IN", pcb.In4_Cu, False),
        ("VIDEO analog zone", "zone", "/VIDEO_IN", pcb.In1_Cu, False),
        ("ADC VBAT In1", "track", "/RP2350A/ADC_VBAT", pcb.In1_Cu, True),
        ("ADC VBAT In4", "track", "/RP2350A/ADC_VBAT", pcb.In4_Cu, True),
        ("ADC CURR In1", "track", "/RP2350A/ADC_CURR", pcb.In1_Cu, True),
        ("ADC CURR In4", "track", "/RP2350A/ADC_CURR", pcb.In4_Cu, True),
        ("ADC wrong width", "track", "/RP2350A/ADC_VBAT", pcb.In1_Cu, False),
        ("ADC wrong net", "track", "/VIDEO_IN", pcb.In1_Cu, False),
        ("ADC outside area", "track", "/RP2350A/ADC_VBAT", pcb.In1_Cu, False),
        ("ADC wrong layer", "track", "/RP2350A/ADC_VBAT", pcb.In4_Cu, False),
        ("ADC plane layer", "track", "/RP2350A/ADC_VBAT", pcb.In2_Cu, False),
        ("ADC zone", "zone", "/RP2350A/ADC_VBAT", pcb.In1_Cu, False),
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
        if name.startswith("sense "):
            # Named areas bound the exact track, not any crossing or nearby track.
            suffix = {"sense ESC1 B": "ESC1_PHASE_B_SENSE",
                      "sense B wrong layer": "ESC1_PHASE_B_SENSE",
                      "sense C wrong layer": "ESC1_PHASE_C_SENSE",
                      "sense ESC1 C": "ESC1_PHASE_C_SENSE",
                      "sense ESC4 A": "ESC4_PHASE_A_SENSE"}.get(name, "ESC1_PHASE_A_SENSE")
            area = pcb.ZONE(board); area.SetIsRuleArea(True)
            area.SetZoneName(suffix)
            layers = pcb.LSET(); layers.AddLayer(pcb.F_Cu)
            layers.AddLayer(pcb.In4_Cu if suffix in ("ESC1_PHASE_A_SENSE", "ESC1_PHASE_B_SENSE") else pcb.In1_Cu)
            area.SetLayerSet(layers)
            area.SetNet(nets["GND"])
            area.SetDoNotAllowTracks(False); area.SetDoNotAllowVias(False)
            area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False)
            area.SetDoNotAllowZoneFills(False)
            outline = area.Outline(); outline.NewOutline()
            for dx, dy in [(-.2, -.2), (2.2, -.2), (2.2, .2), (-.2, .2)]:
                point = pos(dx, dy); outline.Append(point.x, point.y)
            board.Add(area)
            if kind == "track":
                item.SetWidth(pcb.FromMM(.20 if name == "sense wrong width" else .12))
                if name == "sense outside area": item.SetEnd(pos(3, 0))
        if name.startswith("OSD "):
            area = pcb.ZONE(board); area.SetIsRuleArea(True)
            area.SetZoneName("OSD_LVL_LOCAL")
            layers = pcb.LSET(); layers.AddLayer(pcb.F_Cu); layers.AddLayer(pcb.In1_Cu)
            area.SetLayerSet(layers)
            area.SetNet(nets["GND"])
            area.SetDoNotAllowTracks(False); area.SetDoNotAllowVias(False)
            area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False)
            area.SetDoNotAllowZoneFills(False)
            outline = area.Outline(); outline.NewOutline()
            for dx, dy in [(-.2, -.2), (2.2, -.2), (2.2, .2), (-.2, .2)]:
                point = pos(dx, dy); outline.Append(point.x, point.y)
            board.Add(area)
            if kind == "track":
                item.SetWidth(pcb.FromMM(.10 if name == "OSD wrong width" else .12))
                if name == "OSD outside area": item.SetEnd(pos(3, 0))
        if name.startswith("VIDEO "):
            area = pcb.ZONE(board); area.SetIsRuleArea(True)
            area.SetZoneName("VIDEO_IN_LOCAL_BRIDGE")
            layers = pcb.LSET(); layers.AddLayer(pcb.F_Cu); layers.AddLayer(pcb.In1_Cu)
            area.SetLayerSet(layers)
            area.SetNet(nets["GND"])
            area.SetDoNotAllowTracks(False); area.SetDoNotAllowVias(False)
            area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False)
            area.SetDoNotAllowZoneFills(False)
            outline = area.Outline(); outline.NewOutline()
            for dx, dy in [(-.2, -.2), (2.2, -.2), (2.2, .2), (-.2, .2)]:
                point = pos(dx, dy); outline.Append(point.x, point.y)
            board.Add(area)
            if kind == "track":
                item.SetWidth(pcb.FromMM(.10 if name == "VIDEO wrong width" else .15))
                if name == "VIDEO outside area": item.SetEnd(pos(3, 0))
        if name.startswith("HD "):
            area = pcb.ZONE(board); area.SetIsRuleArea(True)
            area.SetZoneName("HD_EN_IN2_BRIDGE")
            layers = pcb.LSET(); layers.AddLayer(pcb.F_Cu); layers.AddLayer(pcb.In2_Cu)
            area.SetLayerSet(layers)
            area.SetNet(nets["GND"])
            area.SetDoNotAllowTracks(False); area.SetDoNotAllowVias(False)
            area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False)
            area.SetDoNotAllowZoneFills(False)
            outline = area.Outline(); outline.NewOutline()
            for dx, dy in [(-.2, -.2), (2.2, -.2), (2.2, .2), (-.2, .2)]:
                point = pos(dx, dy); outline.Append(point.x, point.y)
            board.Add(area)
            if kind == "track":
                item.SetWidth(pcb.FromMM(.10 if name == "HD wrong width" else .09))
                if name == "HD outside area": item.SetEnd(pos(3, 0))
        if name.startswith("UART "):
            area = pcb.ZONE(board); area.SetIsRuleArea(True)
            area.SetZoneName("UART0_TX_IN2_LOCAL")
            layers = pcb.LSET(); layers.AddLayer(pcb.F_Cu); layers.AddLayer(pcb.In2_Cu)
            area.SetLayerSet(layers)
            area.SetNet(nets["GND"])
            area.SetDoNotAllowTracks(False); area.SetDoNotAllowVias(False)
            area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False)
            area.SetDoNotAllowZoneFills(False)
            outline = area.Outline(); outline.NewOutline()
            for dx, dy in [(-.2, -.2), (2.2, -.2), (2.2, .2), (-.2, .2)]:
                point = pos(dx, dy); outline.Append(point.x, point.y)
            board.Add(area)
            if kind == "track":
                item.SetWidth(pcb.FromMM(.10 if name == "UART wrong width" else .09))
                if name == "UART outside area": item.SetEnd(pos(3, 0))
        if name.startswith("PA "):
            suffix = "PA_DET_IN4_LOCAL" if name in ("PA detector In4", "PA wrong area") else "PA_DET_IN1_LOCAL"
            area = pcb.ZONE(board); area.SetIsRuleArea(True); area.SetZoneName(suffix)
            layers = pcb.LSET(); layers.AddLayer(pcb.F_Cu)
            layers.AddLayer(pcb.In4_Cu if suffix == "PA_DET_IN4_LOCAL" else pcb.In1_Cu)
            area.SetLayerSet(layers); area.SetNet(nets["GND"])
            area.SetDoNotAllowTracks(False); area.SetDoNotAllowVias(False)
            area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False)
            area.SetDoNotAllowZoneFills(False)
            outline = area.Outline(); outline.NewOutline()
            for dx, dy in [(-.2, -.2), (2.2, -.2), (2.2, .2), (-.2, .2)]:
                point = pos(dx, dy); outline.Append(point.x, point.y)
            board.Add(area)
            if kind == "track":
                item.SetWidth(pcb.FromMM(.10 if name == "PA wrong width" else .12))
                if name == "PA outside area": item.SetEnd(pos(3, 0))
        if name.startswith("ADC "):
            suffix = "ADC_CURR" if name.startswith("ADC CURR") else "ADC_VBAT"
            inner = "IN4" if name in ("ADC VBAT In4", "ADC CURR In4") else "IN1"
            area = pcb.ZONE(board); area.SetIsRuleArea(True)
            area.SetZoneName(suffix + "_" + inner + "_LOCAL")
            ls = pcb.LSET(); ls.AddLayer(pcb.F_Cu); ls.AddLayer(pcb.In4_Cu if inner == "IN4" else pcb.In1_Cu)
            area.SetLayerSet(ls); area.SetNet(nets["GND"])
            area.SetDoNotAllowTracks(False); area.SetDoNotAllowVias(False)
            area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False); area.SetDoNotAllowZoneFills(False)
            outline = area.Outline(); outline.NewOutline()
            for dx, dy in [(-.2, -.2), (2.2, -.2), (2.2, .2), (-.2, .2)]:
                point = pos(dx, dy); outline.Append(point.x, point.y)
            board.Add(area)
            if kind == "track":
                item.SetWidth(pcb.FromMM(.10 if name == "ADC wrong width" else .12))
                if name == "ADC outside area": item.SetEnd(pos(3, 0))
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
