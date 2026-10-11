#!/usr/bin/env python3
"""Generate the legacy bom_plan.json index from the authoritative schematic.

The filename is retained for the existing validation and component-class tools.
It is an export, not a second source for circuit values or placement. Run after
schematic edits; --check detects a stale export without changing it.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

import sch_build as sb
from sch_build import find, findall


def generate(hw):
    root = hw / "OpenAIO-Whoop.kicad_sch"
    tree = sb.parse(root.read_text())
    files = [root.name] + sorted({
        next(p[2] for p in findall(s, "property") if p[1] == "Sheetfile")
        for s in findall(tree, "sheet")})
    paths = {}
    for sheet in findall(tree, "sheet"):
        props = {p[1]: p[2] for p in findall(sheet, "property")}
        paths[find(sheet, "uuid")[1]] = props["Sheetname"]
    with tempfile.TemporaryDirectory(prefix="whoop-bom-") as temp:
        netlist = Path(temp) / "board.net"
        subprocess.run([sb.KICAD_CLI, "sch", "export", "netlist", "--format",
                        "kicadsexpr", "-o", str(netlist), str(root)],
                       check=True, capture_output=True, text=True)
        _, nets = sb.read_netlist(netlist)
    refnets = defaultdict(set)
    for net, nodes in nets.items():
        for ref, *_ in nodes:
            if not net.startswith("unconnected-"):
                refnets[ref].add(net)
    parts = []
    for filename in files:
        doc = sb.parse((hw / filename).read_text())
        for symbol in findall(doc, "symbol"):
            lib_id = find(symbol, "lib_id")[1]
            if lib_id.startswith("power:"):
                continue
            props = {p[1]: p[2] for p in findall(symbol, "property")}
            def flag(key, default="yes"):
                return (find(symbol, key) or [key, default])[1] in ("yes", True)
            instances = findall(find(find(symbol, "instances"), "project"), "path")
            for instance in instances:
                ref = find(instance, "reference")[1]
                sheet = Path(filename).stem
                block = {"rp2350a": "fc", "rx_esp32_sx1281": "rx"}.get(sheet, sheet)
                if sheet == "esc_channel":
                    name = paths[instance[1].rstrip("/").split("/")[-1]]
                    sheet += " (" + name + ")"
                    block = name.lower()
                parts.append({
                    "ref": ref, "block": block, "sheet": sheet,
                    "value": props.get("Value", ""),
                    "manufacturer": props.get("Manufacturer", ""),
                    "mpn": props.get("MPN", ""), "lcsc": props.get("LCSC", ""),
                    "footprint": props.get("Footprint", ""), "symbol": lib_id,
                    "dnp": flag("dnp", "no"),
                    "exclude_from_bom": not flag("in_bom"),
                    "exclude_from_board": not flag("on_board"),
                    "nets": sorted(refnets[ref]),
                    "datasheet": props.get("Datasheet", ""),
                })
    def refkey(part):
        match = re.fullmatch(r"([A-Za-z]+)(\d+)", part["ref"])
        return (match[1], int(match[2])) if match else (part["ref"], 0)
    parts.sort(key=refkey)
    assert len({p["ref"] for p in parts}) == len(parts), "duplicate references"
    fitted = [p for p in parts if not p["dnp"] and not p["exclude_from_bom"]]
    return {
        "meta": {
            "board": "OpenAIO-Whoop",
            "generator": "hardware/tools/export_bom_plan.py",
            "authority": "Root schematic and hierarchical sheets; no placement is implied.",
            "source_sha256": {f: hashlib.sha256((hw / f).read_bytes()).hexdigest()
                              for f in files},
        },
        "parts": parts,
        "summary": {
            "parts_total": len(parts), "bom_parts": len(fitted),
            "bom_lines": len({(p["mpn"], p["footprint"]) for p in fitted}),
            "by_block": dict(sorted(Counter(p["block"] for p in parts).items())),
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hw", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    destination = args.hw / "bom_plan.json"
    text = json.dumps(generate(args.hw), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not destination.is_file() or destination.read_text() != text:
            print("FAIL: bom_plan.json is stale; run export_bom_plan.py")
            return 1
        print("ok: schematic component export is current")
    else:
        destination.write_text(text)
        print("Exported schematic component index to", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
