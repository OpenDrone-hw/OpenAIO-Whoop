#!/usr/bin/env python3
"""Placement conditions that the schematic relies on (P4 deletions / sharing), checked on the board.

    prlimit --as=5368709120 -- /usr/bin/python3.12 hardware/tools/check_p5_conditions.py [--board FILE] [-v]

check_netlist N2 sees only that a supply pin shares a net with a capacitor; it cannot see distance. Several P4
decisions removed or shared a capacitor on the condition that P5 places a part next to a pin (D77 hot-loop caps,
D79 C17 deleted, BR-05 EFM8 VDD bulk, BR-14 shared LP5912 CIN, BR-08, the USB inlet parts, the boost COUT), and the
sheet notes / bom_plan carry datasheet placement rules (P4 critique round 3): the RP2354A core SMPS on U10's side
(RP2350 DS 6.3.8.1), the BOOTSEL strap R44 + D8 / SW1, the USB series resistors, the NOR VCC cap and the LP5907 CIN.
Routing-stage conditions that need copper (VREG_FB taken from the C56 pad and not under L2, one CIN/COUT GND point
with 2 vias, no copper under L2 / VREG_LX on In1) are listed in research/FLOORPLAN.md, not checked here.
This script turns each condition into a pass/fail number on the board: distances are centre to centre in mm
(part centre to pad centre where a pin is named), sides from the footprint layer.

Statuses: ok / FAIL / n/a (a part the condition names is not on the board yet, e.g. before sync_pcb.py).
Exit 1 on any FAIL. If P5 cannot meet the U5 or U21 input condition, the fallback is a CIN back at that pin
(U5: 1 uF 0201 GRM033R61A105ME44D; U21: 10 uF 0402 GRM155C80J106ME11D; both existing lines), logged as a decision.
"""
import argparse
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--board", default=os.path.join(os.path.dirname(HERE), "OpenAIO-Whoop.kicad_pcb"))
ap.add_argument("-v", action="store_true")
args = ap.parse_args()

board = pcbnew.LoadBoard(args.board)
FP = {f.GetReference(): f for f in board.GetFootprints()}
MM = 1e-6


def side(ref):
    return "B" if FP[ref].IsFlipped() else "F"


def centre(ref):
    p = FP[ref].GetPosition()
    return (p.x * MM, p.y * MM)


def pad(ref, num):
    for p in FP[ref].Pads():
        if p.GetNumber() == str(num):
            q = p.GetPosition()
            return (q.x * MM, q.y * MM)
    raise KeyError("%s pad %s" % (ref, num))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


results = []


def report(status, cond, msg):
    results.append(status)
    if status != "ok" or args.v:
        print("%-4s  %-6s %s" % (status, cond, msg))


def need(cond, refs):
    miss = [r for r in refs if r not in FP]
    if miss:
        report("n/a", cond, "not on the board: " + ", ".join(miss))
    return not miss


# ESC instances: (EFM8, phase A/B/C cells, hot-loop caps A/B/C, EFM8 100 nF) - stride from sch_contract.json
ESC = []
for i in range(4):
    q = 29 + 3 * i
    c = 6 * i
    ESC.append({"esc": "ESC%d" % (i + 1), "mcu": "U%d" % (6 + i),
                "cells": [("Q%d" % q, "C%d" % (20 + c)), ("Q%d" % (q + 1), "C%d" % (23 + c)),
                          ("Q%d" % (q + 2), "C%d" % (21 + c))],
                "bulk": "C%d" % (23 + c), "bypass": "C%d" % (19 + c)})

# D77: hot-loop cap on its AGM210MAP's side, across pins 3 (S2, +BATT) and 1 (S1, GND) at the lead side
for e in ESC:
    for q, c in e["cells"]:
        if not need("D77", [q, c]):
            continue
        d = dist(centre(c), mid(pad(q, 1), pad(q, 3)))
        ok = side(q) == side(c) and d <= 1.5
        report("ok" if ok else "FAIL", "D77", "%s %s: %s cap on %s, %.1f mm from the pin 1-3 midpoint (<= 1.5, same side)"
               % (e["esc"], q, c, side(c) + ("" if side(c) == side(q) else " vs " + side(q)), d))

# BR-05 (amended, D77): phase-B cap within 4 mm of EFM8 VDD pin 4 (either side, +BATT plane); 100 nF at pin 4
for e in ESC:
    m, b, y = e["mcu"], e["bulk"], e["bypass"]
    if need("BR-05", [m, b]):
        d = dist(centre(b), pad(m, 4))
        report("ok" if d <= 4.0 else "FAIL", "BR-05", "%s %s to %s VDD pin 4: %.1f mm (<= 4.0)" % (e["esc"], b, m, d))
    if need("BR-05", [m, y]):
        d = dist(centre(y), pad(m, 4))
        ok = d <= 1.2 and side(y) == side(m)
        report("ok" if ok else "FAIL", "BR-05", "%s %s 100 nF to %s pin 4: %.1f mm (<= 1.2, same side)" % (e["esc"], y, m, d))

# D79: C17 deleted; U5 VIN (pin 1) within 3 mm of C8-C11 or U3 VIN2 (pin 6)
if need("D79", ["U5", "C8", "C9", "C10", "C11", "U3"]):
    cands = [(dist(pad("U5", 1), centre(c)), c) for c in ("C8", "C9", "C10", "C11")]
    cands.append((dist(pad("U5", 1), pad("U3", 6)), "U3 VIN2"))
    d, w = min(cands)
    report("ok" if d <= 3.0 else "FAIL", "D79", "U5 VIN pin 1 to nearest input cap (%s): %.1f mm (<= 3.0; else 1 uF 0201 back)" % (w, d))

# BR-14: one shared C13 for U4 IN and U21 IN (pin 6 each). LP5912 DS 9.2.2.2: CIN >= 1 uF (7.6: 0.7 uF min) "not
# more than 1 cm from the input pin"; C12 / C13 are the only +5V capacitors. Fallback for a pin that misses it: its own
# CIN (10 uF 0402 GRM155C80J106ME11D, existing line: a 0201 1 uF X5R keeps only about half its value at 5 V)
if need("BR-14", ["C13", "U4", "U21"]):
    for u in ("U4", "U21"):
        d = dist(centre("C13"), pad(u, 6))
        report("ok" if d <= 10.0 else "FAIL", "BR-14", "C13 to %s IN pin 6: %.1f mm (<= 10, LP5912 DS 9.2.2.2; else own CIN)" % (u, d))

# BR-08: shared RP2354A bypass caps
for c, pin, lim in (("C49", 44, 1.5), ("C54", 54, 1.0)):
    if need("BR-08", [c, "U10"]):
        d = dist(centre(c), pad("U10", pin))
        report("ok" if d <= lim else "FAIL", "BR-08", "%s to U10 pin %d: %.1f mm (<= %.1f)" % (c, pin, d, lim))

# VTX: C108 at RTC6705 pins 39/40; R80-R82 at the ESP32 end
if need("VTX", ["C108", "U19"]):
    d = dist(centre("C108"), mid(pad("U19", 39), pad("U19", 40)))
    report("ok" if d <= 2.0 else "FAIL", "VTX", "C108 to U19 pins 39/40: %.1f mm (<= 2.0)" % d)
for r in ("R80", "R81", "R82"):
    if need("VTX", [r, "U16", "U19"]):
        a, b = dist(centre(r), centre("U16")), dist(centre(r), centre("U19"))
        report("ok" if a < b else "FAIL", "VTX", "%s: %.1f mm to U16, %.1f mm to U19 (ESP32 end)" % (r, a, b))

# USB inlet (D57): U24 and D7 at J31, D7 on J31's side next to pins 2/3 (TPD2EUSB30 DS 10.1)
if need("USB", ["U24", "J31"]):
    d = dist(centre("U24"), pad("J31", 4))
    report("ok" if d <= 3.0 else "FAIL", "USB", "U24 to J31 VBUS pin 4: %.1f mm (<= 3.0)" % d)
if need("USB", ["D7", "J31"]):
    d = dist(centre("D7"), mid(pad("J31", 2), pad("J31", 3)))
    ok = d <= 3.0 and side("D7") == side("J31")
    report("ok" if ok else "FAIL", "USB", "D7 to J31 pins 2/3: %.1f mm, %s vs J31 %s (<= 3.0, same side)" % (d, side("D7"), side("J31")))

# Boost COUT (TPS61022 DS 11.1: output caps close to VOUT / GND): nearest <= 2 mm, all four <= 5 mm
if need("BOOST", ["U2", "C8", "C9", "C10", "C11"]):
    ds = sorted((dist(centre(c), pad("U2", 3)), c) for c in ("C8", "C9", "C10", "C11"))
    ok = ds[0][0] <= 2.0 and ds[-1][0] <= 5.0
    report("ok" if ok else "FAIL", "BOOST", "C8-C11 to U2 VOUT pin 3: " + ", ".join("%s %.1f" % (c, d) for d, c in ds)
           + " mm (nearest <= 2.0, all <= 5.0)")

# SMPS (RP2350 DS 6.3.8.1, binding: "Don't place any of CIN/LX/COUT on the opposite side of the PCB"; sheet note RP2350A):
# C58 CIN at VREG_VIN pin 49, L2 LX pad (2) at VREG_LX pin 48, C56 COUT at VREG_FB pin 50, C57 CFILT at VREG_AVDD
# pin 46, all on U10's side within 3 mm. L2 pad 2 = VREG_LX and pad 1 = +1V1 as on the flown house board (DS Fig. 26 /
# 28 orientation; a part on the far side mirrors the field direction, which the side check catches).
for ref, pin, lim in (("C58", 49, 3.0), ("L2", 48, 3.0), ("C56", 50, 3.0), ("C57", 46, 3.0)):
    if need("SMPS", [ref, "U10"]):
        a = pad(ref, 2) if ref == "L2" else centre(ref)
        d = dist(a, pad("U10", pin))
        ok = side(ref) == side("U10") and d <= lim
        report("ok" if ok else "FAIL", "SMPS", "%s%s to U10 pin %d: %.1f mm, %s vs U10 %s (<= %.1f, same side)"
               % (ref, " LX pad" if ref == "L2" else "", pin, d, side(ref), side("U10"), lim))
if need("SMPS", ["L2"]):
    nets = {p.GetNumber(): p.GetNetname() for p in FP["L2"].Pads()}
    ok = nets.get("2", "").endswith("VREG_LX") and nets.get("1", "").endswith("+1V1")
    report("ok" if ok else "FAIL", "SMPS", "L2 pad 1 %s, pad 2 %s (pad 2 = VREG_LX, pad 1 = +1V1)" % (nets.get("1"), nets.get("2")))

# BOOT (sheet notes RP2350A / RX, bom_plan R44 / D8): R44 pad 1 at QSPI_SS pin 60 (stub <= 1 mm, RPi guide R6 'close to
# the flash' = the RP2354A package), D8 on SW1's side with BOOT_SW <= 3 mm
if need("BOOT", ["R44", "U10"]):
    d = dist(pad("R44", 1), pad("U10", 60))
    ok = side("R44") == side("U10") and d <= 1.5
    report("ok" if ok else "FAIL", "BOOT", "R44 pad 1 to U10 pin 60: %.1f mm, %s vs U10 %s (<= 1.5, same side)" % (d, side("R44"), side("U10")))
if need("BOOT", ["D8", "SW1"]):
    d = dist(pad("D8", 3), pad("SW1", 1))
    ok = side("D8") == side("SW1") and d <= 3.0
    report("ok" if ok else "FAIL", "BOOT", "D8 K (BOOT_SW) to SW1 pin 1: %.1f mm, %s vs SW1 %s (<= 3.0, same side)" % (d, side("D8"), side("SW1")))

# USB series resistors (RPi hardware design 5.1: 27R within 1-2 mm of the pins; sheet note RP2350A)
for r, pin in (("R42", 52), ("R43", 51)):
    if need("USB", [r, "U10"]):
        d = dist(centre(r), pad("U10", pin))
        report("ok" if d <= 2.0 else "FAIL", "USB", "%s to U10 pin %d: %.1f mm (<= 2.0)" % (r, pin, d))

# NOR (blackbox sheet, bom_plan C65): VCC 100 nF at U13 pin 8, same side
if need("NOR", ["C65", "U13"]):
    d = dist(centre("C65"), pad("U13", 8))
    ok = side("C65") == side("U13") and d <= 1.5
    report("ok" if ok else "FAIL", "NOR", "C65 to U13 VCC pin 8: %.1f mm, %s vs U13 %s (<= 1.5, same side)" % (d, side("C65"), side("U13")))

# LP5907 CIN (DS SNVS798Q 7.2.2.4 / 9.1: > 0.7 uF effective within 1 cm, same side best): C122 4.7 uF at U22 IN pin 4
if need("VTX", ["C122", "U22"]):
    d = dist(centre("C122"), pad("U22", 4))
    ok = side("C122") == side("U22") and d <= 1.5
    report("ok" if ok else "FAIL", "VTX", "C122 to U22 IN pin 4: %.1f mm, %s vs U22 %s (<= 1.5, same side)" % (d, side("C122"), side("U22")))

n = {s: results.count(s) for s in ("ok", "FAIL", "n/a")}
print("%d ok, %d FAIL, %d n/a" % (n["ok"], n["FAIL"], n["n/a"]))
sys.exit(1 if n["FAIL"] else 0)
