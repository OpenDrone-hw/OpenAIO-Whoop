#!/usr/bin/env python3
"""Check the OpenAIO-Whoop schematic netlist against bom_plan.json, PINMAP.md and the net-class plan.

    /usr/bin/python3.12 hardware/tools/check_netlist.py [--hw HW_DIR] [--netlist FILE] [-v]

Exports the netlist with kicad-cli (unless --netlist is given), reads every sheet file for the placed symbols
(including those that are not on the board, e.g. mounting holes) and runs these checks. Every line is
"<status>  <check>  <message>"; exit 1 on any FAIL.

  N1 single-pin nets      only on pins with a no-connect flag / no-connect pin type, or on test points
  N2 decoupling           every supply input (power_in pin, not GND) of every part shares its net with a
                          capacitor whose other pin is on GND
  N3 sourcing fields      every part has a footprint; every BOM part has MPN + Manufacturer and an LCSC field
                          equal to bom_plan (non-empty wherever bom_plan has an LCSC number)
  N4 bom_plan parity      same reference set; value, footprint, symbol, MPN, Manufacturer, DNP and BOM flags
                          equal to bom_plan.json for every reference (board-only footprints without a symbol
                          such as LOGO1 are skipped)
  N5 pin maps             RP2354A (U10) and ESP32-PICO-V3 (U16) pin -> net equal to research/PINMAP.md §2, §3, §6
                          (net names compared without the sheet path; '-' = no-connect)
  N6 net classes          every net resolves (patterns in .kicad_pro + netclass directive labels) to the class
                          its role needs (rails, phases, gates, RF, USB, analog), and every directive label the
                          contract lists is on its sheet; the class each net gets from the .kicad_pro patterns alone
                          (what the board sees: sync_pcb.py does not carry directive labels) equals its netlist class
"""
import argparse
import collections
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sch_build as sb  # noqa: E402
from sch_build import find, findall  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--hw", default=os.path.dirname(HERE))
ap.add_argument("--netlist")
ap.add_argument("--pinmap")
ap.add_argument("-v", action="store_true", help="list every finding, not the first few")
args = ap.parse_args()
HW = os.path.abspath(args.hw)
ROOT = os.path.join(HW, "OpenAIO-Whoop.kicad_sch")
PINMAP = args.pinmap or os.path.join(os.path.dirname(HW), "research", "PINMAP.md")
results = []


def report(status, check, msg, items=()):
    results.append(status)
    items = list(items)
    lim = len(items) if args.v else 8
    tail = (": " + "; ".join(items[:lim]) + (" (+%d more)" % (len(items) - lim) if len(items) > lim else "")) if items else ""
    print("%-4s  %-3s %s%s" % (status, check, msg, tail))


def verdict(check, msg_ok, bad, msg_bad=None):
    if bad:
        report("FAIL", check, (msg_bad or msg_ok) + " - %d problem(s)" % len(bad), bad)
    else:
        report("ok", check, msg_ok)


# ------------------------------------------------------------------------------------------------ inputs
if args.netlist:
    NET = args.netlist
else:
    NET = os.path.join(tempfile.mkdtemp(), "OpenAIO-Whoop.net")
    r = subprocess.run([sb.KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", NET, ROOT],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("netlist export failed: " + r.stdout + r.stderr)
comps, nets = sb.read_netlist(NET)
# net classes from the netlist (KiCad resolves patterns and directive labels)
CLASS = {}
_tree = sb.parse(open(NET, encoding="utf-8").read())
for n in findall(find(_tree, "nets"), "net"):
    c = find(n, "class")
    CLASS[find(n, "name")[1]] = c[1] if c else "Default"
bom_doc = json.load(open(os.path.join(HW, "bom_plan.json"), encoding="utf-8"))
BOM = {p["ref"]: p for p in bom_doc["parts"]}
contract = json.load(open(os.path.join(HW, "sch_contract.json"), encoding="utf-8"))

# placed symbols from the sheet files (every instance path), incl. parts that are not on the board
root_tree = sb.parse(open(ROOT, encoding="utf-8").read())
files = ["OpenAIO-Whoop.kicad_sch"] + sorted({next(p[2] for p in findall(s, "property") if p[1] == "Sheetfile")
                                              for s in findall(root_tree, "sheet")})
SYMS = {}          # ref -> dict
FLAGS = collections.Counter()   # (file, class) -> netclass directive labels
for f in files:
    t = sb.parse(open(os.path.join(HW, f), encoding="utf-8").read())
    for nf in findall(t, "netclass_flag"):
        cls = next((p[2] for p in findall(nf, "property") if p[1] == "Netclass"), "")
        FLAGS[(f, cls)] += 1
    for s in findall(t, "symbol"):
        lid = find(s, "lib_id")[1]
        if lid.startswith("power:"):
            continue
        props = {p[1]: p[2] for p in findall(s, "property") if isinstance(p[1], str)}
        flag = lambda k: (find(s, k) or [k, "yes"])[1] in ("yes", True)  # noqa: E731
        for p in findall(find(find(s, "instances"), "project"), "path"):
            ref = find(p, "reference")[1]
            SYMS[ref] = {"file": f, "lib_id": lid, "props": props, "dnp": flag("dnp"), "in_bom": flag("in_bom"),
                         "on_board": flag("on_board")}


def short(net):
    return None if net is None or net.startswith("unconnected-") else net.rsplit("/", 1)[-1]


pin_net = {}       # (ref, pin) -> net
for name, nodes in nets.items():
    for ref, pin, func, ptype in nodes:
        pin_net[(ref, pin)] = name

# ------------------------------------------------------------------------------------------------ N1
single = [(n, v[0]) for n, v in nets.items() if len(v) == 1]
bad = ["%s %s.%s (%s)" % (n, v[0], v[1], v[3]) for n, v in single
       if "no_connect" not in v[3] and not v[0].startswith("TP")]
nc = sum(1 for n, v in single if "no_connect" in v[3])
verdict("N1", "single-pin nets: %d, all on no-connect pins (%d) or test points (%d)"
        % (len(single), nc, len(single) - nc), bad, "single-pin nets on connected pins")

# ------------------------------------------------------------------------------------------------ N2
GROUND = {"GND"}
caps_on = collections.defaultdict(list)
for ref, c in comps.items():
    if not re.fullmatch(r"C\d+", ref):
        continue
    ns = [pin_net.get((ref, p)) for p in ("1", "2")]
    if None in ns:
        continue
    for a, b in (ns, ns[::-1]):
        if b in GROUND and a not in GROUND:
            caps_on[a].append(ref)
bad, nsup = [], 0
for name, nodes in nets.items():
    for ref, pin, func, ptype in nodes:
        if ptype != "power_in" or name in GROUND or ref.startswith("#"):
            continue
        nsup += 1
        if not caps_on.get(name):
            bad.append("%s pin %s (%s) on %s" % (ref, pin, func, name))
verdict("N2", "decoupling: %d supply input pins, each net has a capacitor to GND (%d supply nets)"
        % (nsup, len({n for n, nodes in nets.items() for r, p, f, t in nodes if t == "power_in" and n not in GROUND})),
        bad, "supply input pins without a capacitor to GND on their net")

# ------------------------------------------------------------------------------------------------ N3
bad, nbom = [], 0
for ref, s in sorted(SYMS.items()):
    p, pr = BOM.get(ref), s["props"]
    if s["on_board"] and not pr.get("Footprint"):
        bad.append(ref + " no footprint")
    if not s["in_bom"] or s["dnp"]:
        continue
    nbom += 1
    for k in ("MPN", "Manufacturer"):
        if not pr.get(k, "").strip():
            bad.append("%s no %s" % (ref, k))
    if "LCSC" not in pr:
        bad.append(ref + " no LCSC field")
    elif p is not None and pr["LCSC"] != (p["lcsc"] or ""):
        bad.append("%s LCSC %r, bom_plan %r" % (ref, pr["LCSC"], p["lcsc"]))
no_lcsc = sum(1 for r, s in SYMS.items() if s["in_bom"] and not s["dnp"] and not s["props"].get("LCSC"))
verdict("N3", "sourcing fields: %d placed parts with footprints; %d BOM parts with MPN + Manufacturer, LCSC = "
        "bom_plan (%d without an LCSC number, D60: NextPCB sources by MPN)" % (len(SYMS), nbom, no_lcsc), bad)

# ------------------------------------------------------------------------------------------------ N4
plan = {r: p for r, p in BOM.items() if p.get("symbol")}
board_only = sorted(r for r, p in BOM.items() if not p.get("symbol"))
bad = ["%s in bom_plan, not in the schematic" % r for r in sorted(set(plan) - set(SYMS))]
bad += ["%s in the schematic, not in bom_plan" % r for r in sorted(set(SYMS) - set(plan))]
for ref in sorted(set(plan) & set(SYMS)):
    p, s = plan[ref], SYMS[ref]
    want = {"Value": p["value"], "Footprint": p["footprint"]}
    if p["mpn"] or "MPN" in s["props"]:
        want["MPN"] = p["mpn"] or ""
    if p["manufacturer"] or "Manufacturer" in s["props"]:
        want["Manufacturer"] = p["manufacturer"] or ""
    for k, v in want.items():
        if s["props"].get(k, "") != (v or ""):
            bad.append("%s %s %r, bom_plan %r" % (ref, k, s["props"].get(k, ""), v))
    if s["lib_id"] != p["symbol"]:
        bad.append("%s symbol %s, bom_plan %s" % (ref, s["lib_id"], p["symbol"]))
    if s["dnp"] != bool(p["dnp"]):
        bad.append("%s dnp %s, bom_plan %s" % (ref, s["dnp"], p["dnp"]))
    if s["in_bom"] == bool(p["exclude_from_bom"]):
        bad.append("%s in_bom %s, bom_plan exclude_from_bom %s" % (ref, s["in_bom"], p["exclude_from_bom"]))
    if ref in comps and comps[ref]["value"] != p["value"]:
        bad.append("%s netlist value %r" % (ref, comps[ref]["value"]))
verdict("N4", "bom_plan parity: %d references equal (value, footprint, symbol, MPN, Manufacturer, DNP, BOM flag); "
        "board-only, no symbol: %s; not on the board: %s"
        % (len(set(plan) & set(SYMS)), ", ".join(board_only) or "-",
           ", ".join(sorted(r for r, s in SYMS.items() if not s["on_board"])) or "-"), bad)


# ------------------------------------------------------------------------------------------------ N5
def md_section(text, head):
    m = re.search(r"^## " + re.escape(head) + r".*?$(.*?)(?=^## )", text, re.S | re.M)
    if not m:
        sys.exit("PINMAP.md: section %r not found" % head)
    return m.group(1)


def rows(section):
    for line in section.splitlines():
        if not line.startswith("|") or re.match(r"^\|[-| ]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] in ("Pin", "Pins", "ESP32 GPIO"):
            continue
        yield cells


def pins_of(cell):
    out = []
    for a, b in re.findall(r"(\d+)(?:\s*-\s*(\d+))?", cell):
        out += [str(i) for i in range(int(a), int(b) + 1)] if b else [a]
    return out


def net_of(cell):
    tick = re.findall(r"`([^`]+)`", cell)
    if tick:
        return tick[0]
    if cell in ("-", ""):
        return None
    return cell if re.fullmatch(r"[+A-Z0-9_]+", cell) else "UNPARSED(%s)" % cell


text = open(PINMAP, encoding="utf-8").read()
expect = {"U10": {}, "U16": {}}
for cells in rows(md_section(text, "2. RP2354A signal pins")):
    for pn in pins_of(cells[0]):
        expect["U10"][pn] = net_of(cells[2])
for cells in rows(md_section(text, "3. RP2354A power and system pins")):
    for pn in pins_of(cells[0]):
        expect["U10"][pn] = net_of(cells[2])
for cells in rows(md_section(text, "6. Receiver MCU pin plan")):
    if cells[1] in ("-", ""):
        continue
    for pn in pins_of(cells[1]):
        expect["U16"][pn] = net_of(cells[3])
for ref, label in (("U10", "RP2354A"), ("U16", "ESP32-PICO-V3")):
    have = {p: short(n) for (r, p), n in pin_net.items() if r == ref}
    bad = ["pin %s: PINMAP %s, netlist %s" % (p, expect[ref][p] or "NC", have.get(p) or "NC")
           for p in sorted(expect[ref], key=int) if (expect[ref][p] or None) != have.get(p)]
    unlisted = sorted((p for p in have if p not in expect[ref]), key=lambda x: int(x) if x.isdigit() else 999)
    verdict("N5", "%s %s pin map = PINMAP.md (%d pins compared%s)"
            % (ref, label, len(expect[ref]), ", not in PINMAP: " + " ".join(unlisted) if unlisted else ""),
            bad, "%s %s pin map differs from PINMAP.md" % (ref, label))

# ------------------------------------------------------------------------------------------------ N6
RULES = [  # (net pattern, class) - first match wins; the role each class stands for (spec 8.2/8.4, setup_board)
    ("GND", "GND"), ("+BATT", "VBAT"), ("+BATT_*", "VBAT"), ("+*", "Power"),
    ("/VBUS", "Power"), ("/VTX/PA_VCC", "Power"),
    ("/ESC?/PHASE_?", "Phase"), ("/POWER/U2_SW", "Phase"), ("/ESC?/?_COM", "Gate"), ("/ESC?/?_PWM", "Gate"),
    # /POWER/U2_SW: boost switch node, 2.8-3.4 A average (P4 critique round 2)
    ("*/RF_*", "RF"), ("*/USB_D_P", "USB"), ("*/USB_D_N", "USB"),
    ("*CURR_SENSE*", "Analog"), ("*ADC_CURR*", "Analog"), ("*ADC_VBAT*", "Analog"), ("*SHUNT_SENSE*", "Analog"),
    ("*VIDEO*", "Analog"), ("*/VID_*", "Analog"), ("*/OSD_LVL", "Analog"), ("*/OSD_SYNC", "Analog"),
    ("*/PA_DET*", "Analog"),
    ("*/VT_MOD*", "Analog"), ("*/RTC_*", "Analog"), ("*/U19_XTAL*", "Analog"), ("*/TCXO_OUT", "Analog"),
    ("*/XTA", "Analog"),                     # RTC6705 video input, PLL loop filter, 8 / 52 MHz references (P4 critique)
]
# the board's view: KiCad assigns board net classes from the .kicad_pro patterns only (sync_pcb.py writes no
# netclass_assignments), so a class that only a schematic directive label gives would be lost on the board
_pro = json.load(open(os.path.join(HW, "OpenAIO-Whoop.kicad_pro"), encoding="utf-8"))["net_settings"]
PATS = [(x["netclass"], x["pattern"]) for x in _pro.get("netclass_patterns", [])]
ASSIGNED = _pro.get("netclass_assignments") or {}
bad, by_cls = [], collections.Counter()
for name in sorted(nets):
    if name.startswith("unconnected-"):
        continue
    want = next((c for pat, c in RULES if fnmatch.fnmatchcase(name, pat)), "Default")
    got = CLASS.get(name, "Default")
    by_cls[got] += 1
    if got != want:
        bad.append("%s is %s, needs %s" % (name, got, want))
    hits = sorted({c for c, pat in PATS if fnmatch.fnmatchcase(name, pat)})
    board = ASSIGNED.get(name) or (hits[0] if len(hits) == 1 else ("Default" if not hits else "/".join(hits)))
    if board != got:
        bad.append("%s: netlist %s, board patterns give %s" % (name, got, board))
want_flags = collections.Counter()
for d in contract["netclasses"]["directive_labels"]:
    want_flags[("OpenAIO-Whoop.kicad_sch" if d["sheet"] == "root" else d["sheet"], d["class"])] += 1
for k, n in sorted(want_flags.items()):
    if FLAGS[k] < n:
        bad.append("directive %s on %s: %d of %d" % (k[1], k[0], FLAGS[k], n))
verdict("N6", "net classes: %s; %d directive labels (contract %d)"
        % (", ".join("%s %d" % kv for kv in sorted(by_cls.items())), sum(FLAGS.values()), sum(want_flags.values())),
        bad, "net classes")

fails = results.count("FAIL")
print("%d ok, %d FAIL" % (results.count("ok"), fails))
sys.exit(1 if fails else 0)
