#!/usr/bin/env python3
"""Prove that KiCad loaded the complete custom-rule file.

Run with KiCad's Python: check_rules.py board.kicad_pcb
The temporary board has one deliberate violation of a sentinel rule appended
after the board's rules. A parser failure, crashed process, missing report, or
missing sentinel is a failure. The source board and rules are never modified.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    args = parser.parse_args()
    source = args.board.resolve()
    rules = source.with_suffix(".kicad_dru")
    if not source.is_file() or not rules.is_file():
        parser.error("board and matching .kicad_dru must exist")
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli")
    if not cli:
        mac = Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
        cli = str(mac) if mac.is_file() else None
    if not cli:
        parser.error("kicad-cli unavailable; set KICAD_CLI")

    import pcbnew as pcb
    sentinel = "__complete_custom_rules_loaded__"
    with tempfile.TemporaryDirectory(prefix="whoop-rule-check-") as temp:
        target = Path(temp) / "probe.kicad_pcb"
        board = pcb.BOARD()
        board.SetCopperLayerCount(6)
        net = pcb.NETINFO_ITEM(board, sentinel)
        board.Add(net)
        track = pcb.PCB_TRACK(board)
        track.SetStart(pcb.VECTOR2I(pcb.FromMM(10), pcb.FromMM(10)))
        track.SetEnd(pcb.VECTOR2I(pcb.FromMM(11), pcb.FromMM(10)))
        track.SetLayer(pcb.F_Cu)
        track.SetWidth(pcb.FromMM(0.1))
        track.SetNet(net)
        board.Add(track)
        pcb.SaveBoard(str(target), board)
        project = source.with_suffix(".kicad_pro")
        if project.is_file():
            shutil.copy2(project, target.with_suffix(".kicad_pro"))
        # Emitted as a complete KiCad rule by this validation generator.
        probe_rule = ('\n(rule "' + sentinel + '"\n'
                      '  (constraint disallow track)\n'
                      '  (condition "A.NetName == \'' + sentinel + '\'"))\n')
        target.with_suffix(".kicad_dru").write_text(rules.read_text() + probe_rule)
        report = Path(temp) / "drc.json"
        result = subprocess.run(
            [cli, "pcb", "drc", "--format", "json", "-o", str(report), str(target)],
            capture_output=True, text=True, timeout=120)
        if result.returncode or not report.is_file():
            print("FAIL: KiCad did not complete the rule probe")
            print(result.stdout + result.stderr)
            return 1
        violations = json.loads(report.read_text()).get("violations", [])
        loaded = any(v.get("type") == "items_not_allowed"
                     and sentinel in v.get("description", "") for v in violations)
        if not loaded:
            print("FAIL: custom-rule sentinel absent; rules were not verified")
            print(result.stdout + result.stderr)
            return 1
        print("ok: KiCad loaded all custom rules and detected the deliberate probe")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
