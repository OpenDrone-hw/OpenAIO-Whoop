#!/usr/bin/env python3
"""Check that KiCad can parse a board's .kicad_dru (kicad-cli pcb drc drops a broken
file silently and runs with no custom rules). Runs KiCad's DRC engine init through
pcbnew.WriteDRCReport in a child process; in 10.0.6 that call segfaults *after* a
successful rules load in standalone Python, so only the parse error line is trusted.
usage: /usr/bin/python3.12 check_rules.py board.kicad_pcb   -> exit 0 ok, 1 parse error"""
import subprocess, sys
child = ("import os,sys,pcbnew; b=pcbnew.LoadBoard(sys.argv[1]); "
         "pcbnew.WriteDRCReport(b, os.devnull, pcbnew.EDA_UNITS_MM, False)")
r = subprocess.run([sys.executable, "-c", child, sys.argv[1]], capture_output=True, text=True)
errs = [l for l in (r.stdout + r.stderr).splitlines() if "Init DRC engine: err" in l]
print("\n".join(errs) if errs else "custom rules parsed by KiCad")
sys.exit(1 if errs else 0)
