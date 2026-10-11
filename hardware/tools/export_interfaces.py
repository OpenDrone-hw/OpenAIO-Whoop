#!/usr/bin/env python3
"""Export the schematic interface index from KiCad source; never rebuild the circuit.

The legacy sch_contract.json filename is retained for check_netlist.py.
Old circuit-generation scripts are not compatible with this readback schema.
"""
import argparse
import hashlib
import json
from pathlib import Path

import sch_build as sb
from sch_build import find, findall


def generate(hw):
    root = hw / "OpenAIO-Whoop.kicad_sch"
    tree = sb.parse(root.read_text())
    sheets = []
    for sheet in findall(tree, "sheet"):
        props = {p[1]: p[2] for p in findall(sheet, "property")}
        sheets.append({
            "name": props["Sheetname"], "file": props["Sheetfile"],
            "uuid": find(sheet, "uuid")[1],
            "ports": [{"name": p[1], "direction": p[2]}
                      for p in findall(sheet, "pin")],
        })
    files = [root.name] + sorted({s["file"] for s in sheets})
    directives = []
    for filename in files:
        doc = sb.parse((hw / filename).read_text())
        for flag in findall(doc, "netclass_flag"):
            props = {p[1]: p[2] for p in findall(flag, "property")}
            directives.append({"sheet": "root" if filename == root.name else filename,
                               "class": props["Netclass"]})
    return {
        "meta": {"schema": "schematic-readback-v1", "board": "OpenAIO-Whoop",
                 "generator": "hardware/tools/export_interfaces.py",
                 "authority": "KiCad root schematic and hierarchical sheets",
                 "source_sha256": {f: hashlib.sha256((hw / f).read_bytes()).hexdigest()
                                   for f in files}},
        "sheets": sheets,
        "netclasses": {"defined_in": "OpenAIO-Whoop.kicad_pro",
                       "directive_labels": directives},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hw", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    path = args.hw / "sch_contract.json"
    data = json.dumps(generate(args.hw), indent=2) + "\n"
    if args.check:
        if not path.is_file() or path.read_text() != data:
            print("FAIL: schematic interface index is stale")
            return 1
        print("ok: schematic interface index is current")
    else:
        path.write_text(data)
        print("Exported schematic interface index to", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
