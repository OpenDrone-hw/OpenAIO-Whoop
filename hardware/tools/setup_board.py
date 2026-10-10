#!/usr/bin/env python3
"""OpenAIO-Whoop board setup (phase P1): stackup, rules, net classes, custom DRC rules, outline, keepouts.

    /usr/bin/python3.12 hardware/tools/setup_board.py              apply everything (idempotent, re-runnable)
    /usr/bin/python3.12 hardware/tools/setup_board.py --check      build in a temp dir, compare, write nothing
    /usr/bin/python3.12 hardware/tools/setup_board.py --fd         recompute the field-solver impedance table first
    /usr/bin/python3.12 hardware/tools/setup_board.py --selftest   after applying, test the DRU on a synthetic board
    python3 hardware/tools/setup_board.py impedance [--fd]         impedance report only (no pcbnew needed)

Every board value lives in the SPEC section below, each with the research/DESIGN-SPEC.md section (or decision
D<n> in research/DECISIONS.md) it comes from; the layer stack is hardware/tools/stackup.json (spec 8.2). Change a
value there and re-run: the script rebuilds the same files from scratch, so a second run changes nothing.

What it writes (and nothing else):
  hardware/OpenAIO-Whoop.kicad_pcb   6 copper layers, stackup (impedance controlled), mask, via fill/cap, origins,
                                     Edge.Cuts outline (spec 7), named rule areas, User.Eco1/Eco2/User.1/Cmts.User
                                     guides. Every item the script owns carries a uuid starting 5e7b0a1d- and is
                                     regenerated on each run; anything else on the board is left alone.
  hardware/OpenAIO-Whoop.kicad_pro   design rules, the 16 template-ignored DRC checks re-enabled (D7), track / via /
                                     diff-pair presets, net classes with colours and patterns, the RF50 tuning
                                     profile, component classes.
  hardware/OpenAIO-Whoop.kicad_dru   the OpenDrone canonical block (byte-identical to hardware-template, checked)
                                     plus the board rules generated from RULES below.
  hardware/tools/impedance.json      50 ohm widths: 2-D field solver (cached; --fd recomputes) and closed forms.

Method (owner rule: KiCad files through KiCad): the .kicad_pro and .kicad_dru are written as JSON / text into a
temp project, the board is edited through pcbnew there (KiCad 10.0.6 has no Python binding for BOARD_STACKUP,
so the stackup node is spliced as text into the temp copy and then loaded and re-saved by pcbnew, as in
pcb-agent-commons tools/layout/board_setup.py), pcbnew re-saves board and project, the result is read back and
verified, and only then copied over the project files. KiCad must not have the project open.

The field solver needs numpy + scipy. KiCad's Python (3.12) has neither in the agent container, so the
impedance step runs in a child process under the first interpreter that has them (/usr/bin/python3 here) and
caches its result; without one the cached table is used, or the closed forms with a warning.
"""
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
PROJECT = "OpenAIO-Whoop"
PCB, PRO, DRU = (os.path.join(HW, PROJECT + e) for e in (".kicad_pcb", ".kicad_pro", ".kicad_dru"))
STACKUP_JSON = os.path.join(HERE, "stackup.json")
IMPEDANCE_JSON = os.path.join(HERE, "impedance.json")
UUID_PREFIX = "5e7b0a1d"          # marks every board item this script owns

# ==============================================================================================================
# SPEC.  Units mm.  Board coordinates are KiCad's (+y down); positions relative to the body centre.
# ==============================================================================================================
TITLE_REV = "rev1"                               # LINEUP B6, D4: title block rev stays rev1
CENTRE = (113.2, 113.2)                          # spec 7: body centred here; grid and drill/place origin
BODY_HALF = 13.2                                 # spec 7: body square +-13.2 (26.4 mm)
FRONT_R = 5.8                                    # spec 7: front corner (+x, -y) arc R 5.8, centre (+7.4, -7.4)
FRONT = (1, -1)
EAR_R = 2.4                                      # spec 7: ears = circles R 2.4 on the holes (ring OD 4.8)
EAR_FILLET = 0.5                                 # spec 7: concave junctions filleted R 0.5
HOLE_D = 3.5                                     # spec 7: non-plated Edge.Cuts cut-outs
HOLE_HALF = 12.75                                # D73: 25.5 x 25.5 mm pattern (Matrix measured 25.45 +- 0.05)
HOLES = {"LEFT": (-1, -1), "REAR": (-1, 1), "RIGHT": (1, 1)}     # spec 7 / 10: hole sign (x, y)
EDGE_LINE_W = 0.05                               # template board_outline_line_width
FLANGE_D = 5.2                                   # spec 7: grommet flange part keepout, both sides
PART_EDGE_BAND = 0.30                            # spec 7: part keepout band inside the outline (courtyards)
FRAME_PATTERNS = (25.5, 26.0)                    # spec 7: frame guides on User.Eco1

# spec 10 / sketch v4: RF, corridor and tab areas. Positions follow spec/sketch_v4.py (spec 10); P2 moves them
# with the real parts, so board_spec.json pins a bbox only for the RX antenna areas.
RX_ANT_HOLE = (-12.3, 7.5)                       # P2 v3 floorplan: RX antenna wire hole AE1, left edge, rear half
RX_ANT_KEEPOUT_R = 1.6                           # copper keepout L1-L5 (L6 admits the feed): 1.0 mm around a 1.2 mm pad
RX_ANT_EXIT_R = 1.4                              # v3 (D69 preference traded): 2.8 mm wide wire exit strip, hole to edge (ring 1.6 covers the hole)
RX_ROOT_R = 3.0                                  # spec 4.9 / 11: NOR and SPI0 >= 3 mm from the antenna hole
RX_FEED = ((-10.225, 6.8), RX_ANT_HOLE, 0.8)     # rxfix (BLOCKER): FL1 OUT pin 3 (rot 180) -> hole on L1, no via; L2 solid under it
UFL_VTX = (4.5, -1.5)                            # P2 v3 floorplan: U.FL J1 top, rot 90 (mid-board, Matrix-informed)
UFL_ZONE = ((3.25, -3.8), (6.7, 0.8))            # RF_VTX_UFL: U.FL land + 0.15 / 0.3 mm (only RF and GND on L1), P2 v3
RF_PAD_CUT = ((5.4, -2.1), (6.65, -0.9))         # RF_PAD_CUTOUT: under the U.FL signal pad + 0.1, P2 v3
# floorplan v3 (D58 / D75): Wi-Fi chip antenna AE2 maker keep-out, both sides, all copper layers: only the RF feed and
# AE2 itself inside (x 2.05..7.05 keeps it 2 mm from the ESC4 cell Q38, D75).
WIFI_KO = ((2.05, -13.4), (7.05, -10.0))
# floorplan v3 (D72 / D76): vertical JST BM04B USB J31 on the bottom; mating zone = header body + 1.0 mm finger margin
# (no TALL class part inside, DRU), drawn as a named rule area on B.Cu.
USB_J31 = (-7.7, 8.6, 135.0)                     # centre x, y, rotation of J31 (P2 v3 floorplan)
USB_BODY = (6.0, 4.25)                           # BM04B-SRSS-TB body (JST drawing), mating margin below
USB_MARGIN = 1.0
# 5.8 GHz chain (sketch v4): RTC6705 PAOUT1 (pin 35, right side) -> 45 deg CPWG -> PA RF IN (down) -> PA RF OUT (up)
# -> match zone -> BPF -> U.FL; half-width 1.2 = line + CPWG gap + 1 mm (spec 10: L2 solid under the chain + 1 mm).
VTX_CHAIN = ([(9.49, -5.35), (7.85, -1.5), (10.2, -2.1), (7.2, -1.8), (6.025, -1.5)], 1.2)   # P2 v3: PAOUT1 (U19 pin 35, bottom) -> C110 -> PA U20 (top) -> BPF FL2 -> U.FL pin 1
SHUNT_LAYER = "F.Cu"                             # P2 v3: shunt R1 sits on the top side, so the corridor is on L1
SHUNT_CORRIDOR = ((-12.9, -3.5), (-8.6, 3.4))    # D10 / spec 10: B+ pad J2 -> shunt R1 on L6 (P2 v3 box)
TAB_HALF, TAB_IN, TAB_OUT = 1.5, 1.3, 0.5        # spec 7: tab 1.2-1.5 wide + 1.0 mm part keepout beyond the 0.3 band
TABS = {"T1": ((14.447, 14.447), (0.7071, 0.7071)), "T3": ((-14.447, -14.447), (-0.7071, -0.7071)), "T4": ((-14.447, 14.447), (-0.7071, 0.7071))}   # P2 v3 (concept D): tabs at the three ear tips, inside the MOUNT flange keep-outs (no extra area)

# spec 8.1 / 8.4 + D6: board minimums (the .kicad_pro "rules" block).  Via 0.35 / 0.20 is the OpenDrone
# standard via (D6, owner-confirmed buildable at NextPCB), so the annular minimum is 0.075 and the minimum through
# hole is 0.20 (spec 8.4): DRC then enforces the standard via, although both fabs drill 0.15.
PRO_RULES = {
    "min_clearance": 0.09, "min_track_width": 0.09, "min_connection": 0.09,
    "min_via_diameter": 0.35, "min_via_annular_width": 0.075, "min_through_hole_diameter": 0.20,
    "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,            # template values; microvias disallowed (DRU)
    "min_hole_to_hole": 0.2, "min_hole_clearance": 0.2, "min_copper_edge_clearance": 0.2,
    "min_text_height": 0.8, "min_text_thickness": 0.13,                 # spec 8.1 / 13, D12: 0.8 / 0.13 labels
    "min_silk_clearance": 0.0, "solder_mask_to_copper_clearance": 0.005,
}
MASK_EXPANSION = 0.04                            # spec 8.1
MASK_MIN_WEB = 0.10                              # spec 8.1 (green)
VIA_FILL_CAP = True                              # spec 8: IPC-4761 type VII filled + capped (board setting)

# D7: the 16 checks hardware-template ignores, re-enabled before placement.
SEVERITIES = {
    "copper_edge_clearance": "error", "courtyards_overlap": "error", "missing_courtyard": "error",
    "malformed_courtyard": "error", "npth_inside_courtyard": "error", "pth_inside_courtyard": "error",
    "silk_edge_clearance": "error", "silk_over_copper": "error", "text_height": "error",
    "text_thickness": "error", "footprint_type_mismatch": "error", "tuning_profile_track_geometries": "error",
    "footprint_filters_mismatch": "warning", "silk_overlap": "warning", "track_not_centered_on_via": "warning",
    "via_dangling": "warning",
}

TRACK_PRESETS = [0.10, 0.14, 0.20, 0.30, 0.50, 1.00]       # spec 8.4 (+ the RF 50 ohm width, computed)
VIA_PRESETS = [(0.35, 0.20), (0.40, 0.20)]                 # D6 standard via; spec 8.3 power via
DIFF_PAIR_PRESETS = [(0.12, 0.12, 0.25)]                   # spec 8.2 USB FS pair: width, gap, via gap
TEXT_DEFAULTS = {"silk_line_width": 0.13, "silk_text_size_h": 0.8, "silk_text_size_v": 0.8,
                 "silk_text_thickness": 0.13}             # spec 8.4 / 13, D12: new silk items start at 0.8 / 0.13

# spec 8.4 net classes (names and colours after OpenAIO, LINEUP C8; Gate violet because OpenAIO's green sits on the
# default wire colour, P4 critique r3) + GND (orchestrator, spec 8.3 power-via arrays).
# (name, track, clearance, via dia, via drill, colour, priority, extra)  track None = computed RF width
NETCLASSES = [
    ("RF", None, 0.15, 0.35, 0.20, "rgb(200, 160, 0)", 0, {"tuning_profile": "RF50"}),
    ("USB", 0.12, 0.12, 0.35, 0.20, "rgb(30, 110, 255)", 1, {"diff_pair_width": 0.12, "diff_pair_gap": 0.12}),
    ("VBAT", 0.50, 0.15, 0.40, 0.20, "rgb(220, 40, 40)", 2, {}),
    ("Phase", 0.50, 0.15, 0.40, 0.20, "rgb(200, 0, 200)", 3, {}),
    ("Gate", 0.15, 0.10, 0.35, 0.20, "rgb(120, 60, 220)", 4, {}),
    ("Analog", 0.10, 0.15, 0.35, 0.20, "rgb(0, 160, 160)", 5, {}),
    ("Power", 0.25, 0.09, 0.35, 0.20, "rgb(255, 140, 0)", 6, {}),
    ("GND", 0.20, 0.09, 0.40, 0.20, "rgb(130, 130, 130)", 7, {}),
]
DEFAULT_CLASS = {"track_width": 0.09, "clearance": 0.09, "via_diameter": 0.35, "via_drill": 0.20,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25}
# Planned net names (D4 power names; PINMAP.md; OpenAIO esc_channel upper-cased per LINEUP). Root-sheet local
# labels appear as "/NAME", sub-sheet ones as "/SHEET/NAME", power nets bare.
NETCLASS_PATTERNS = [
    ("VBAT", ["+BATT", "+BATT_*"]),                                       # +BATT, +BATT_IN (spec 4.1)
    ("Phase", ["/ESC?/PHASE_?", "/POWER/U2_SW"]),                         # in-sheet PHASE_A/B/C (spec 8.4); boost switch
                                                                          # node U2_SW 2.8-3.4 A avg (P4 critique round 2)
    ("Gate", ["/ESC?/?_COM", "/ESC?/?_PWM"]),                              # Bluejay layout A names (spec 4.4)
    ("Power", ["+5V", "+5V_BST", "+5V_USB", "+5V_HD", "+3V3", "+3V3_VTX", "+1V8", "+1V1",
               "+5V_*", "+3V3_*", "+1V8_*", "+1V1_*", "/VBUS",             # LINEUP A11 names; EFM8 VDD is on +BATT; VBUS hier. net (P4)
               "/VTX/PA_VCC"]),                                         # SE5004L VCC feed 0.65-0.8 A: the board ignores the
                                                                          # schematic directive label (P4 critique round 2)
    ("GND", ["GND"]),
    ("Analog", ["*VIDEO*", "*/VID_*", "*/OSD_LVL*", "*/OSD_SYNC*", "*CURR_SENSE*", "*ADC_VBAT*", "*/CSA*",
                "*/PA_DET*", "*/VPD*", "*SHUNT_SENSE_*", "*ADC_CURR*",      # Kelvin pair SHUNT_SENSE_P/N (spec 4.1); ADC_CURR RC node (P4)
                "*/VT_MOD*", "*/RTC_*", "*/U19_XTAL*", "*/TCXO_OUT", "*/XTA"]),  # RTC6705 video input, PLL loop filter, 8/52 MHz refs (P4 critique)
    ("RF", ["*/RF_*", "*/ANT*", "*/RFIO*", "*/RFOUT*", "*/RFIN*"]),
    ("USB", ["*/USB_D_P", "*/USB_D_N"]),                                  # _P/_N: KiCad pairs them (spec 8.2)
]
# Component classes for the spec 8.4 spacing rules, by footprint name (P3 checks these against the real names).
COMPONENT_CLASSES = [
    ("PASSIVE_0201", ["*0201*"]),
    ("PASSIVE_0402", ["*0402*"]),
    ("TALL", ["*U.FL*", "*U_FL*", "*UFL*", "*SRSS*", "*IND-SMD_L2.5-W2.0*", "*_2520*"]),  # U.FL, 2520 L (spec 8.4; not the 2520 crystal)
    ("POWER_FET", ["*CSD25310Q2*", "*CSD13202Q2*", "*DQK*", "*AGM210*"]),            # D12 stage (P3 names), D21
    ("SOLDER_PAD", ["*small_pad*", "*SolderPad*", "*MotorPad*", "*BattPad*", "*motor_pad*", "*battery_pad*", "*BT2*"]),
    ("MOTOR_PAD", ["*MotorPad*", "*motor_pad*"]),                                  # top pad, far side is a 0.9 ring
]
def sheet_classes():
    """D75 (board context): component class per schematic sheet (POWER, ESC1..ESC4, RP2350A, IMU, OSD, BLACKBOX, RX,
    VTX, LED, PADS) from hardware/bom_plan.json, assigned by reference in the .kicad_pro (no board text edits)."""
    path = os.path.join(HW, "bom_plan.json")
    if not os.path.exists(path):
        return []
    out = {}
    for prt in json.load(open(path))["parts"]:
        sh = prt.get("sheet") or ""
        m = re.match(r"esc_channel \((ESC\d)\)", sh)
        cls = m.group(1) if m else {"rx_esp32_sx1281": "RX"}.get(sh, sh.upper())
        if cls and not prt["ref"].startswith("H"):
            out.setdefault(cls, []).append(prt["ref"])
    return [(k, sorted(v)) for k, v in sorted(out.items())]


SOLDER_PAD_FPIDS = ["*:small_pad*", "*:SolderPad*", "*:MotorPad*", "*:BattPad*", "*:motor_pad*", "*:battery_pad*",
                    "*:BT2*"]  # memberOfFootprint (P3 library names MotorPad_* / BattPad_*, spec 4.10)

# Impedance (spec 8.2): CPWG on L1 over L2 (and L6 over L5, same geometry), gap 0.15, target 50 ohm +- 10 %.
RF_GAP = 0.15
RF_TARGET = 50.0
ER_ALT = 3.91                  # 1080 prepreg in the NextPCB impedance finder model (resin-rich), sensitivity case
MASK_MODEL = {"er": 3.5, "t_on_cu": 0.0127, "t_on_sub": 0.0305}   # NextPCB finder solder-mask model
MASK_STACKUP = {"color": "Green", "epsilon_r": 3.5, "loss_tangent": 0.025}
SILK_COLOR = "White"

# ==============================================================================================================
# Custom DRC rules (written below the canonical marker).  KiCad 10.0.6: the LAST matching rule wins, so general
# rules come first and exceptions after.  @W_RF@ etc. are filled from the impedance step.
# (name, comment lines, body)  body None = comment block only.
# ==============================================================================================================
AE_EXEMPT = ("  (severity ignore)\n  (constraint disallow footprint pad)\n"
             "  (condition \"((A.Type == 'Footprint' && A.Reference == 'AE*') || (A.Type == 'Pad' && "
             "A.memberOfFootprint('AE*'))) && (A.intersectsArea('RF_RX_ANT') || A.intersectsArea('RF_RX_ANT_L6') || "
             "A.intersectsArea('RF_RX_EXIT') || A.intersectsArea('WIFI_ANT_KO'))\")")
RULES = [
    ("header",
     ["OpenAIO-Whoop board rules (research/DESIGN-SPEC.md 7, 8.1, 8.4, 10, 11; D6, D7, D21). Generated by",
      "hardware/tools/setup_board.py: change the script, not this file. Numbers that gate every fab live in the",
      ".kicad_pro (clearance 0.09, track 0.09, via 0.35 / 0.20 (D6), annular 0.075, through hole 0.20, hole to",
      "hole 0.20, hole clearance 0.20, copper to edge 0.20, silk text 0.8 / 0.13); the rules below are what this",
      "board needs on top of them, from the NextPCB and JLCPCB intersection in spec 8.1. D21: every deliberate",
      "break of a conservative rule is a rule named 'D21 <name>' with its reason; nothing is ignored globally."], None),

    ("through vias only",
     ["Owner rule and spec 8: no microvias, blind or buried vias. Filled and capped via-in-pad is a through via."],
     "  (constraint disallow micro_via blind_via buried_via)"),

    ("hole to hole, different nets 0.30",
     ["NextPCB 0.30 between holes of different nets (CAF); JLCPCB 0.20. Same net stays at the 0.20 minimum."],
     "  (constraint hole_to_hole (min 0.30mm))\n  (condition \"A.Net != B.Net\")"),

    ("D21 same_net_via_array",
     ["D21: the 0.30 CAF spacing above is for holes of different nets; via arrays of one net (phase fields, EP",
      "arrays, battery and power arrays) stay at the 0.20 board minimum, which both fabs build."],
     "  (constraint hole_to_hole (min 0.20mm))\n"
     "  (condition \"A.Net == B.Net && A.Type == 'Via' && B.Type == 'Via'\")"),

    ("PTH pad holes 0.45 apart",
     ["JLCPCB 0.45 hole to hole between plated pad holes (battery holes, motor wire anchors)."],
     "  (constraint hole_to_hole (min 0.45mm))\n"
     "  (condition \"A.Type == 'Pad' && B.Type == 'Pad' && A.isPlated() && B.isPlated()\")"),

    ("PTH pads, copper 0.40 apart",
     ["NextPCB 0.40 copper between pads with holes, different nets. Footprint vias (Heatsink pads, D21 below) are",
      "vias, not component holes, and keep the via clearances."],
     "  (constraint clearance (min 0.40mm))\n"
     "  (condition \"A.Type == 'Pad' && B.Type == 'Pad' && A.Pad_Type == 'Through-hole' && "
     "B.Pad_Type == 'Through-hole' && A.Net != B.Net && A.Fabrication_Property != 'Heatsink pad' && "
     "B.Fabrication_Property != 'Heatsink pad'\")"),

    ("D65 plug-ready motor land: PicoBlade rings 0.35 apart",
     ["D65 / D21: the Molex 53047 PicoBlade header fixes the 1.25 mm pitch; 0.90 rings (0.50 drill + 0.20 ring)",
      "leave 0.35 mm copper between neighbouring holes (NextPCB 0.40 general value; the BetaFPV Matrix 1S 5IN1 II",
      "ships the same 1.25 mm plated land). Scoped to MotorPad_PicoBlade pads (the four lands are far apart); NextPCB EQ item."],
     "  (constraint clearance (min 0.30mm))\n"
     "  (condition \"A.Type == 'Pad' && B.Type == 'Pad' && A.memberOfFootprint('*:MotorPad_PicoBlade*') && "
     "B.memberOfFootprint('*:MotorPad_PicoBlade*')\")"),

    ("PTH annular ring 0.20",
     ["Component holes: JLCPCB 0.15 absolute, 0.20 recommended; NextPCB 0.20. Vias keep the 0.075 of D6."],
     "  (constraint annular_width (min 0.20mm))\n  (condition \"A.Type == 'Pad' && A.isPlated()\")"),

    ("PTH hole to copper 0.28",
     ["JLCPCB 0.28 from a plated pad hole to other copper (NextPCB 0.23). Via holes keep the 0.20 minimum."],
     "  (constraint hole_clearance (min 0.28mm))\n  (condition \"A.Type == 'Pad' && A.isPlated()\")"),

    ("inner layers: PTH hole to copper 0.30",
     ["JLCPCB 0.30 on inner layers for plated pad holes."],
     "  (layer inner)\n  (constraint hole_clearance (min 0.30mm))\n  (condition \"A.Type == 'Pad' && A.isPlated()\")"),

    ("NPTH at least 0.50",
     ["JLCPCB 0.50 minimum non-plated hole (NextPCB 0.40). The mounting holes are Edge.Cuts cut-outs, not pads."],
     "  (constraint hole_size (min 0.50mm))\n  (condition \"A.Type == 'Pad' && !A.isPlated()\")"),

    ("SMD pad to track and pour 0.13",
     ["Spec 8.1: 0.04 mask expansion + JLCPCB 0.09 from a mask opening to copper. Pours are copper too, so the",
      "zone fill keeps the same distance (spec text names tracks; zones added for the same reason)."],
     "  (constraint clearance (min 0.13mm))\n"
     "  (condition \"A.Type == 'Pad' && A.Pad_Type == 'SMD' && (B.Type == 'Track' || B.Type == 'Arc' || "
     "B.Type == 'Zone') && A.Net != B.Net\")"),

    ("silk 0.20 from the edge and holes",
     ["Silk clipped at the routed edge or a hole is lost (line silk rule, pcb-agent-commons). KiCad 10.0.6",
      "tests silk against Edge.Cuts with the silk_clearance constraint, not edge_clearance."],
     "  (constraint silk_clearance (min 0.20mm))\n"
     "  (condition \"A.Layer == 'Edge.Cuts' && (B.Layer == 'F.Silkscreen' || B.Layer == 'B.Silkscreen')\")"),

    ("parts: pads 0.30 from the edge",
     ["Spec 7 / 8.1: components 0.30 from the routed edge and the mounting holes (copper 0.20 is the fab limit).",
      "Edge solder pads (user, motor and battery pads) are the intended exception, scoped by footprint: they",
      "keep the 0.20 copper-to-edge minimum (D7: exceptions as named, scoped rules)."],
     "  (constraint edge_clearance (min 0.30mm))\n"
     "  (condition \"A.Type == 'Pad' && !(@SOLDER_PAD_FPID@)\")"),

    ("parts: courtyards off the edge band",
     ["Spec 7 part keepout band (rule area PART_EDGE_BAND, @BAND@ mm inside the outline), tested on courtyards;",
      "solder-pad footprints (component class SOLDER_PAD) are exempt like above."],
     "  (constraint disallow footprint)\n"
     "  (condition \"A.Type == 'Footprint' && A.intersectsArea('PART_EDGE_BAND') && "
     "!A.hasComponentClass('SOLDER_PAD')\")"),

    ("courtyards: touching allowed, overlap is an error",
     ["Spec 8.4 / D2 body rule: courtyards are drawn at max(body, land) + 0.10 (P3 normalises the library), so",
      "touching courtyards are 0.20 mm body to body. courtyards_overlap is an error in the .kicad_pro."],
     "  (constraint courtyard_clearance (min 0mm))"),

    ("0402 to 0402: +0.05",
     ["Spec 8.1 / 8.4: NextPCB asks 0.25 between two 0402 (0.20 for 0201)."],
     "  (constraint courtyard_clearance (min 0.05mm))\n"
     "  (condition \"A.hasComponentClass('PASSIVE_0402') && B.hasComponentClass('PASSIVE_0402')\")"),

    ("tall parts: 0.5 to 0201 and 0402",
     ["Spec 8.4: the U.FL and the 2520 inductor (and any SH1.0 part) shadow small passives for paste, AOI and",
      "rework. D69 (owner): a preference traded for density; the 0.2 mm body rule (check_spacing.py) remains."],
     "  (constraint courtyard_clearance (min 0mm))\n"
     "  (condition \"A.hasComponentClass('TALL') && (B.hasComponentClass('PASSIVE_0201') || "
     "B.hasComponentClass('PASSIVE_0402'))\")"),

    ("solder pads: 0.5 to 0201 and 0402",
     ["Spec 8.4: user, battery and motor pads take a 60-80 W iron; keep small passives 0.5 mm away.",
      "D69 / D70 (owner): the iron halo is the 0.2 mm body rule (check_spacing.py); courtyards may touch."],
     "  (constraint courtyard_clearance (min 0mm))\n"
     "  (condition \"A.hasComponentClass('SOLDER_PAD') && (B.hasComponentClass('PASSIVE_0201') || "
     "B.hasComponentClass('PASSIVE_0402'))\")"),

    ("D21 motor_pad_ring_side",
     ["D21 / spec 10 (iron rework 'from every part on its side'): a motor pad is soldered on the top; its far side",
      "is only the 0.9 mm anchor-hole ring, so the 0.5 mm small-passive halo applies on the pad's side, and the far",
      "side keeps the plain courtyard rule (no overlap). Battery pads are pads on both sides and keep the halo there."],
     "  (constraint courtyard_clearance (min 0mm))\n"
     "  (condition \"A.hasComponentClass('MOTOR_PAD') && A.Layer != B.Layer\")"),

    ("D67 test vias are vias: hole spacing 0.20",
     ["D67: TP1-TP9, TP12, TP13 are mask-open filled 0.35/0.20 vias drawn as footprints (TestPoint_Via_*); the via",
      "hole spacing (0.20, pro minimum) applies, not the 0.45 component-hole value."],
     "  (constraint hole_to_hole (min 0.20mm))\n"
     "  (condition \"A.memberOfFootprint('*:TestPoint_Via*') && B.memberOfFootprint('*:TestPoint_Via*')\")"),

    ("D65 DNP motor headers: courtyards may meet at the ear corner",
     ["D65 / D21: the bottom-side courtyards of two neighbouring plug-ready motor lands (optional DNP PicoBlade",
      "header envelopes) meet at the ear corner; the header bodies keep the 0.2 mm body rule (check_spacing.py), so",
      "both headers can be fitted. Scoped to MOTOR_PAD pairs only."],
     "  (severity ignore)\n  (constraint courtyard_clearance (min 0mm))\n"
     "  (condition \"A.hasComponentClass('MOTOR_PAD') && B.hasComponentClass('MOTOR_PAD')\")"),

    ("D21 fet_solid_pads",
     ["D21 / spec 11: FET, battery, motor and user solder pads join their pours solid (no thermal relief): the",
      "power path and the iron need the copper; reflow is profiled for it (NextPCB EQ)."],
     "  (constraint zone_connection solid)\n"
     "  (condition \"A.Type == 'Pad' && (A.hasComponentClass('POWER_FET') || A.hasComponentClass('SOLDER_PAD'))\")"),

    ("D21 via_in_pad_typeVII",
     ["Spec 8 / 11 and D6: every via that sits in a pad is filled with non-conductive epoxy and capped",
      "(IPC-4761 type VII). The board setting fills and caps all vias (filling yes, capping yes), so no via",
      "is ever left open in a pad. KiCad 10.0.6 cannot test a via inside a same-net pad, so there is no rule",
      "for it; order the NextPCB via-in-pad option (spec 8.1) and keep the 0.35 / 0.20 via (0.40 / 0.20 in",
      "power arrays outside pads)."], None),

    ("D21 trimmed_footprint",
     ["Spec 4.8 / 4.9: footprints with NC pads removed (RTC6705) or the NOR exposed pad removed are saved as",
      "their own footprints in the project library (P3), so lib_footprint_mismatch stays an error and never",
      "fires for them; no rule is needed and none is relaxed."], None),

    ("D21 footprint_via_pads annular",
     ["D21 / spec 8.3: through vias drawn inside a footprint land as PTH pads with the Heatsink fabrication property",
      "(EFM8BB51 EP array, CSD13202Q2 merged-drain phase field) are 0.35/0.20 Type VII vias (D6), not component",
      "holes: the via annular ring 0.075 applies instead of the 0.20 PTH component-hole ring (LIBRARY.md item)."],
     "  (constraint annular_width (min 0.075mm))\n  (condition \"A.Type == 'Pad' && A.Fabrication_Property == 'Heatsink pad'\")"),

    ("D21 footprint_via_pads hole_clearance",
     ["D21: the same footprint vias keep the 0.20 via hole clearance, not the 0.28 / 0.30 component-hole values."],
     "  (constraint hole_clearance (min 0.20mm))\n  (condition \"A.Type == 'Pad' && A.Fabrication_Property == 'Heatsink pad'\")"),

    ("D21 footprint_via_pads same_net_holes",
     ["D21 / D39: same-net footprint vias keep the 0.20 hole spacing of a via array, not the 0.45 PTH pad value."],
     "  (constraint hole_to_hole (min 0.20mm))\n"
     "  (condition \"A.Type == 'Pad' && B.Type == 'Pad' && A.Fabrication_Property == 'Heatsink pad' && "
     "B.Fabrication_Property == 'Heatsink pad' && A.Net == B.Net\")"),

    ("D21 esp32_ganged_mask",
     ["Spec 4.7 / 8.1, only if the NextPCB EQ (O15) accepts 0.35 mm pitch: one ganged mask opening per side of",
      "the ESP32-D0WD-V3 land, set as the footprint attribute 'allow soldermask bridges' on that footprint only",
      "(P3). Not active until then."], None),

    ("In1 and In4 are solid GND planes",
     ["Spec 8.2 / 11: L2 and L5 unbroken under every signal. A track on them cuts the plane; warn so each one",
      "is reviewed (L2 under the 5.8 GHz chain is a hard keepout, rule area RF_VTX_CHAIN)."],
     "  (severity warning)\n  (constraint disallow track)\n"
     "  (condition \"A.Layer == 'In1.Cu' || A.Layer == 'In4.Cu'\")"),

    ("In2 and In3: no analog, RF or gate nets",
     ["Spec 8.2 / 11: In2 (L3) references the +BATT plane (L4) more than GND, so video and sense (Analog), RF and",
      "the FET gates (Gate) route on L1 over L2 or L6 over L5. In3 (L4) is the +BATT plane itself."],
     "  (constraint disallow track)\n"
     "  (condition \"(A.Layer == 'In2.Cu' || A.Layer == 'In3.Cu') && "
     "(A.NetClass == 'Analog' || A.NetClass == 'RF' || A.NetClass == 'Gate')\")"),

    ("In2 and In3: no gyro, VTX control or Kelvin nets",
     ["Spec 8.2 / 8.4: the name-based sensitive set (gyro SPI1, GYRO_*, VTX_SPI, PA_*, SHUNT_SENSE_*) stays off",
      "In2/In3 as well (net names compared with wildcards; '.' is literal). Route sync 2026-10-10: the integrated",
      "schematic names the buses /SPI1_*, /VTX_SPI_* and /VTX/U19_SPI* (underscore), so those forms are matched too."],
     "  (constraint disallow track)\n"
     "  (condition \"(A.Layer == 'In2.Cu' || A.Layer == 'In3.Cu') && (A.NetName == '*SPI1.*' || "
     "A.NetName == '*SPI1_*' || A.NetName == '*GYRO_*' || A.NetName == '*VTX_SPI.*' || "
     "A.NetName == '*VTX_SPI_*' || A.NetName == '*/U19_SPI*' || A.NetName == '*/PA_*' || "
     "A.NetName == '*SHUNT_SENSE_*')\")"),

    ("RF: no vias",
     ["Spec 10: no via in the 5.8 GHz path; the 2.4 GHz feed runs on L1 to the antenna hole without one.",
      "D21 / FLOORPLAN Open: the RTC6705 (bottom) feeds the PA (top), so RF_PA_IN carries the one RF via,",
      "fenced by GND vias at <= 1 mm (route/prep); every other RF net stays via-free."],
     "  (constraint disallow via)\n  (condition \"A.NetClass == 'RF' && A.NetName != '/VTX/RF_PA_IN'\")"),

    ("RF: 50 ohm width on the outer layers",
     ["Spec 8.2: CPWG, gap @GAP@ mm (the RF clearance), L1 over L2 and L6 over L5, 50 ohm +- 10 %.",
      "Width @W_RF@ mm from the 2-D field solver with solder mask (setup_board.py, impedance.json):",
      "@Z_NOTE@"],
     "  (layer outer)\n  (constraint track_width (min @W_MIN@mm) (opt @W_RF@mm) (max @W_MAX@mm))\n"
     "  (condition \"A.NetClass == 'RF'\")"),

    ("RF_VTX_UFL: only RF and GND copper on F.Cu",
     ["Spec 10: no other copper or parts next to the 5.8 GHz line and the U.FL (rule area RF_VTX_UFL)."],
     "  (layer \"F.Cu\")\n  (constraint disallow track via zone)\n"
     "  (condition \"A.intersectsArea('RF_VTX_UFL') && A.NetClass != 'RF' && A.NetName != 'GND'\")"),

    ("RF_VTX_CHAIN: GND vias only",
     ["Spec 8.4 / 10: no non-GND via inside the 5.8 GHz chain area, so L2 stays solid under the line."],
     "  (constraint disallow via)\n  (condition \"A.intersectsArea('RF_VTX_CHAIN') && A.NetName != 'GND'\")"),

    ("RF_RX_FEED: GND vias only",
     ["Spec 8.4 / 10: no non-GND via under the 2.4 GHz feed (L1, FL1 OUT to the hole), so L2 stays solid under it."],
     "  (constraint disallow via)\n  (condition \"A.intersectsArea('RF_RX_FEED') && A.NetName != 'GND'\")"),

    ("RF_RX_ANT: only the RF feed on L1",
     ["rxfix BLOCKER / OpenAIO lesson (net-aware antenna keepout): inside the RX antenna-hole ring (L1-L5; pours,",
      "pads and parts are kept out by the rule area) the only track is the 2.4 GHz feed /RX/RF_RX_ANT on L1, from",
      "FL1 OUT straight into the AE1 hole pad; no vias, no other tracks, no other layers."],
     "  (constraint disallow track via)\n"
     "  (condition \"A.intersectsArea('RF_RX_ANT') && (A.Type == 'Via' || A.NetName != '/RX/RF_RX_ANT' || A.Layer != 'F.Cu')\")"),

    ("RF_RX_ANT_L6: only the RF feed",
     ["Spec 10: on L6 the antenna-hole keepout admits only an RF-class track (vias, parts and pours are",
      "kept out by the rule area; L1-L5 by RF_RX_ANT and the rule above). rxfix: the feed now runs on L1."],
     "  (layer \"B.Cu\")\n  (constraint disallow track)\n"
     "  (condition \"A.intersectsArea('RF_RX_ANT_L6') && A.NetClass != 'RF'\")"),

    ("SPI0 3 mm from the RX antenna hole",
     ["Spec 4.9 / 11: the blackbox bus (75 MHz writes, 50 MHz reads) has harmonics in the ELRS band; SPI0 and",
      "the NOR chip select stay outside RF_RX_ROOT (r 3.0 around the hole) on every layer. Route sync 2026-10-10",
      "(P4 ruling 'add SPI0 to the 3 mm rule'): the schematic nets are /SPI0_MISO, /SPI0_MOSI, /SPI0_SCK."],
     "  (constraint disallow track via)\n"
     "  (condition \"A.intersectsArea('RF_RX_ROOT') && (A.NetName == '*SPI0_*' || A.NetName == '*SPI0.*' || "
     "A.NetName == '*FLASH_CS*')\")"),

    ("SHUNT_CORRIDOR: battery current only",
     ["D10 / spec 11: the battery-to-shunt corridor (on the shunt's layer, @SHUNT_LAYER@ in P2 v3) carries +BATT_IN, +BATT and GND; the Kelvin pair",
      "SHUNT_SENSE_P/N leaves at the shunt's inner pad edges. Everything else stays out before routing."],
     "  (layer \"@SHUNT_LAYER@\")\n  (constraint disallow track via)\n"
     "  (condition \"A.intersectsArea('SHUNT_CORRIDOR') && A.NetClass != 'VBAT' && A.NetName != 'GND' && "
     "A.NetName != '*SHUNT_SENSE_*'\")"),

    ("D21 rx_antenna_hole",
     ["D21 / spec 10: the antenna wire hole's own footprint (reference AE*) sits at the centre of RF_RX_ANT,",
      "RF_RX_ANT_L6 and RF_RX_EXIT, whose part keepouts are for every other footprint. Scoped to AE* inside",
      "those areas only."],
     AE_EXEMPT),

    ("D76 USB J31 shroud corner at the RX wire ring",
     ["D76 / D69: the vertical USB header J31 sits beside the rear mounting hole; its plastic shroud corner (courtyard,",
      "no copper) reaches into the RX antenna-hole ring / exit strip on the bottom. The ring stays a copper keep-out",
      "(RF_RX_ANT, L1-L5) and the wire exit runs away from J31 (toward the edge); scoped to J31 only."],
     "  (severity ignore)\n  (constraint disallow footprint)\n"
     "  (condition \"A.Type == 'Footprint' && A.Reference == 'J31' && (A.intersectsArea('RF_RX_EXIT') || "
     "A.intersectsArea('RF_RX_ANT_L6'))\")"),

    ("WIFI_ANT_KO: only the RF feed",
     ["D58 / D75 / OpenAIO lesson (net-aware antenna keepout): inside the Wi-Fi chip antenna keep-out only the",
      "RF-class feed track reaches AE2; no vias, no other tracks (pours and parts are kept out by the rule area,",
      "AE2 itself by the AE* exemption above)."],
     "  (constraint disallow track via)\n"
     "  (condition \"A.intersectsArea('WIFI_ANT_KO') && (A.Type == 'Via' || A.NetClass != 'RF')\")"),

    ("USB_MATING: no tall part next to J31",
     ["D72 / D76: the vertical USB plug and the fingers that push it need the space around J31 free of other",
      "connectors (TALL class J*: SH/SUR plugs, U.FL); parts <= 1.25 mm tall (2520 inductor, passives, ICs) sit far",
      "below the 4.25 mm BM04B wall the plug is gripped above, so they keep only the body rule."],
     "  (constraint courtyard_clearance (min 1.0mm))\n"
     "  (condition \"(A.Reference == 'J31' && B.hasComponentClass('TALL') && B.Reference == 'J*' && B.Reference != 'J31') || "
     "(B.Reference == 'J31' && A.hasComponentClass('TALL') && A.Reference == 'J*' && A.Reference != 'J31')\")"),

    ("USB: pair gap",
     ["Spec 8.2: USB FS pair 0.12 / 0.12. Inert until the nets end in _P/_N, P/N or +/- (KiCad 10.0.6 does",
      "not pair USB_DP/USB_DM): name them USB_D+ / USB_D- or USB_DP / USB_DN in P4."],
     "  (constraint diff_pair_gap (min 0.10mm) (opt 0.12mm) (max 0.20mm))\n  (condition \"A.NetClass == 'USB'\")"),

    ("USB: length match",
     ["Spec 8.2: length-matched pair; 0.5 mm is about 3 ps, far inside the 12 Mbit/s budget."],
     "  (constraint skew (max 0.5mm))\n  (condition \"A.NetClass == 'USB'\")"),

    ("D21 Analog X2SON land gaps (U14, U15)",
     ["D21 / route sync 2026-10-10: the Analog class clearance (0.15) also hits pad pairs inside the 1.0 x 0.8 X2SON",
      "video switch U14 (SN74LVC1G3157DTBR, land gap 0.10) and the 0.8 x 0.8 X2SON comparator U15 (TLV7031DPWR, 0.11).",
      "Those gaps are the manufacturer land pattern, above the 0.09 fab minimum; routed copper keeps the class clearance."],
     "  (constraint clearance (min 0.09mm))\n"
     "  (condition \"A.Type == 'Pad' && B.Type == 'Pad' && "
     "((A.memberOfFootprint('lib:X2SON-6_L1.0-W0.8-BL_Dense') && B.memberOfFootprint('lib:X2SON-6_L1.0-W0.8-BL_Dense')) || "
     "(A.memberOfFootprint('lib:X2SON-4_L0.8-W0.8-P0.48-TL-A_Dense') && B.memberOfFootprint('lib:X2SON-4_L0.8-W0.8-P0.48-TL-A_Dense')))\")"),
]

# ==============================================================================================================
# 1. Impedance: closed forms (always) and a 2-D field solver (numpy + scipy).
# ==============================================================================================================
def hj_microstrip(w, h, t, er):
    """Hammerstad-Jensen microstrip with thickness correction (Wadell 3.6), bare copper.  (Z0, Eeff)."""
    u = w / h
    th = math.tanh(math.sqrt(6.517 * u))
    du1 = (t / h) / math.pi * math.log(1 + 4 * math.e / ((t / h) / (th * th)))
    ur = u + 0.5 * du1 * (1 + 1 / math.cosh(math.sqrt(er - 1)))
    f = 6 + (2 * math.pi - 6) * math.exp(-((30.666 / ur) ** 0.7528))
    z01 = 60 * math.log(f / ur + math.sqrt(1 + (2 / ur) ** 2))
    a = 1 + math.log((ur ** 4 + (ur / 52) ** 2) / (ur ** 4 + 0.432)) / 49 + math.log(1 + (ur / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / ur) ** (-a * b)
    return z01 / math.sqrt(ee), ee


def _ellip_ratio(k):
    def K(m):
        a, b = 1.0, math.sqrt(1 - m * m)
        for _ in range(40):
            a, b = (a + b) / 2, math.sqrt(a * b)
        return math.pi / (2 * a)
    return K(k) / K(math.sqrt(1 - k * k))


def cpwg_closed(w, g, h, t, er):
    """Grounded coplanar waveguide, conformal mapping (Wadell 3.4.3) with the thickness correction of KiCad's
    calculator (pcb_calculator transline coplanar.cpp).  Bare copper.  (Z0, Eeff)."""
    k1 = w / (w + 2 * g)
    k3 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * g) / (4 * h))
    q1, q3 = _ellip_ratio(k1), _ellip_ratio(k3)
    qe = q1
    if t > 0:
        d = (t * 1.25 / math.pi) * (1 + math.log(4 * math.pi * w / t))
        qe = _ellip_ratio(k1 + (1 - k1 * k1) * d / (2 * g))
    qz = 1 / (qe + q3)
    ee = 1 + q3 * qz * (er - 1)
    if t > 0:
        ee -= (0.7 * (ee - 1) * t / g) / (q1 + 0.7 * t / g)
    return 60 * math.pi * qz / math.sqrt(ee), ee


def bisect(f, target, lo, hi):
    """x with f(x) = target for f falling in x."""
    for _ in range(60):
        m = (lo + hi) / 2
        if f(m) > target:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


FD_GRID = {"dx": 0.007 / 3, "X": 3.0, "air": 1.0, "ground_strip": 0.5}   # dx divides 0.077 and 0.035 exactly


def fd_z0(w, h, t, er, gap=None, mask=True, grid=FD_GRID):
    """2-D finite-difference Laplace solve (numpy + scipy sparse LU): node grid, cell permittivities, links
    weighted by the mean of the two cells they border; grounded plane at y = 0 and grounded walls.  Energy
    W = 1/2 sum eps (dphi)^2 in eps0 units; Z0 = eta0 / sqrt(C C0) with C = 2 W at 1 V (grid step cancels in 2-D).
    gap None = microstrip, else CPWG with ground strips of FD_GRID ground_strip at that gap.  Mask: Er, thickness
    on copper and on bare substrate as MASK_MODEL (NextPCB finder).  Validated: bare microstrip within 1 % of
    Hammerstad-Jensen for this stackup (see impedance.json)."""
    import numpy as np
    import scipy.sparse as sp
    import scipy.sparse.linalg as spl
    from scipy import ndimage
    dx, X, air = grid["dx"], grid["X"], grid["air"]
    nx, nh, nt = int(round(X / dx)), int(round(h / dx)), int(round(t / dx))
    ny = nh + int(round(air / dx))
    eps = np.ones((ny, nx))
    eps[:nh, :] = er
    NX, NY = nx + 1, ny + 1
    fixed = np.zeros((NY, NX), bool)
    volt = np.zeros((NY, NX))
    fixed[0, :] = fixed[-1, :] = True
    fixed[:, 0] = fixed[:, -1] = True
    cell = np.zeros((ny, nx), bool)
    strips = [(-w / 2, w / 2, 1.0)]
    if gap is not None:
        G = grid["ground_strip"]
        strips += [(-w / 2 - gap - G, -w / 2 - gap, 0.0), (w / 2 + gap, w / 2 + gap + G, 0.0)]
    for x0, x1, v in strips:
        i0, i1 = int(round((x0 + X / 2) / dx)), int(round((x1 + X / 2) / dx))
        fixed[nh:nh + nt + 1, i0:i1 + 1] = True
        volt[nh:nh + nt + 1, i0:i1 + 1] = v
        cell[nh:nh + nt, i0:i1] = True
    if mask:
        r = max(1, int(round(MASK_MODEL["t_on_cu"] / dx)))
        m = np.zeros_like(cell)
        m[nh:nh + int(round(MASK_MODEL["t_on_sub"] / dx)), :] = True
        m |= ndimage.binary_dilation(cell, structure=np.ones((2 * r + 1, 2 * r + 1), bool))
        m[:nh, :] = False
        m &= ~cell
        eps[m] = MASK_MODEL["er"]

    def energy(e):
        pad = np.zeros((ny + 2, nx + 2))
        pad[1:-1, 1:-1] = e
        wh = (pad[0:NY, 1:NX] + pad[1:NY + 1, 1:NX]) / 2
        wv = (pad[1:NY, 0:NX] + pad[1:NY, 1:NX + 1]) / 2
        idx = np.arange(NY * NX).reshape(NY, NX)
        a = np.concatenate([idx[:, :-1].ravel(), idx[:-1, :].ravel()])
        b = np.concatenate([idx[:, 1:].ravel(), idx[1:, :].ravel()])
        wl = np.concatenate([wh.ravel(), wv.ravel()])
        N = NY * NX
        L = sp.coo_matrix((np.concatenate([wl, wl, -wl, -wl]),
                           (np.concatenate([a, b, a, b]), np.concatenate([a, b, b, a]))), shape=(N, N)).tocsr()
        f = fixed.ravel()
        free = ~f
        phi = volt.ravel().copy()
        phi[free] = spl.spsolve(L[free][:, free].tocsc(), -L[free][:, f] @ phi[f])
        return 0.5 * float(phi @ (L @ phi))

    return 376.7303 / math.sqrt((2 * energy(eps)) * (2 * energy(np.ones_like(eps))))


def fd_width(target, h, t, er, gap=None, mask=True, w_guess=0.12):
    """Width for Z0 = target on grid-aligned widths, linear interpolation between the two bracketing cells."""
    dx = FD_GRID["dx"]
    cache = {}

    def z(k):
        if k not in cache:
            cache[k] = fd_z0(k * dx, h, t, er, gap, mask)
        return cache[k]
    k = max(2, int(round(w_guess / dx)))
    if z(k) > target:
        while z(k + 1) > target:
            k += 1
        lo = k
    else:
        while z(k - 1) <= target:
            k -= 1
        lo = k - 1
    zl, zh = z(lo), z(lo + 1)
    return round((lo + (zl - target) / (zl - zh)) * dx, 4), {round(kk * dx, 5): round(v, 2) for kk, v in sorted(cache.items())}


def rf_geometry():
    s = json.load(open(STACKUP_JSON))["layers"]
    return {"h": s["dielectric 1"]["thickness"], "t": s["F.Cu"]["thickness"], "er": s["dielectric 1"]["epsilon_r"],
            "h_b": s["dielectric 5"]["thickness"], "t_b": s["B.Cu"]["thickness"], "er_b": s["dielectric 5"]["epsilon_r"]}


def impedance_inputs():
    g = rf_geometry()
    return {"h": g["h"], "t": g["t"], "er": g["er"], "er_alt": ER_ALT, "gap": RF_GAP, "target": RF_TARGET,
            "mask": MASK_MODEL, "grid": FD_GRID, "solver": "setup_board.fd_z0 v1"}


def closed_forms(inp):
    h, t, g = inp["h"], inp["t"], inp["gap"]
    out = {}
    for er in (inp["er"], inp["er_alt"]):
        out["er %.2f" % er] = {
            "microstrip_hj_bare_w50": round(bisect(lambda w: hj_microstrip(w, h, t, er)[0], inp["target"], 0.02, 0.6), 4),
            "cpwg_kicad_calculator_bare_w50": round(bisect(lambda w: cpwg_closed(w, g, h, t, er)[0], inp["target"], 0.02, 0.6), 4),
        }
    return out


def compute_fd(inp):
    """Field-solver table: CPWG at the spec gap and microstrip, with mask, at the stackup Er and ER_ALT; the RF width
    is the 0.005-rounded mean of the two CPWG widths; its Z0 is solved at both Er."""
    h, t, g, T = inp["h"], inp["t"], inp["gap"], inp["target"]
    res = {"validation": {}}
    w0 = 0.139
    res["validation"]["microstrip_bare_w0.139_er%.2f" % inp["er"]] = {
        "fd": round(fd_z0(w0, h, t, inp["er"], None, False), 2), "hammerstad_jensen": round(hj_microstrip(w0, h, t, inp["er"])[0], 2)}
    for er in (inp["er"], inp["er_alt"]):
        key = "er %.2f" % er
        res[key] = {}
        guess = bisect(lambda w: hj_microstrip(w, h, t, er)[0], T, 0.02, 0.6) - 0.012
        for name, gap in (("cpwg_gap%.2f_mask" % g, g), ("microstrip_mask", None)):
            w, samples = fd_width(T, h, t, er, gap, True, guess)
            res[key][name] = {"w50": w, "samples_w_z0": samples}
            print("  fd %s %s: 50 ohm at w = %.4f mm" % (key, name, w), flush=True)
    wc = [res["er %.2f" % er]["cpwg_gap%.2f_mask" % g]["w50"] for er in (inp["er"], inp["er_alt"])]
    w_rf = round(round(sum(wc) / 2 / 0.005) * 0.005, 3)
    res["rf_width"] = {"w": w_rf, "rule": "0.005-rounded mean of the CPWG widths at the two Er",
                       "z0": {"er %.2f" % er: round(fd_z0(w_rf, h, t, er, g, True), 2) for er in (inp["er"], inp["er_alt"])}}
    print("  RF width %.3f mm: Z0 %s" % (w_rf, res["rf_width"]["z0"]), flush=True)
    return res


def have_scipy():
    try:
        import numpy, scipy.sparse.linalg, scipy.ndimage   # noqa: F401
        return True
    except Exception:
        return False


def impedance(recompute=False, write=True):
    """Return the impedance record, recomputing the field-solver part when asked or when its inputs changed."""
    inp = impedance_inputs()
    old = json.load(open(IMPEDANCE_JSON)) if os.path.isfile(IMPEDANCE_JSON) else {}
    fd = old.get("field_solver") if old.get("inputs") == inp and not recompute else None
    if fd is None:
        if have_scipy():
            print("impedance: running the field solver (a few minutes)", flush=True)
            fd = compute_fd(inp)
        else:
            py = next((p for p in ("/usr/bin/python3", shutil.which("python3") or "") if p and os.path.exists(p) and
                       subprocess.run([p, "-I", "-c", "import numpy, scipy.sparse.linalg, scipy.ndimage"],
                                      capture_output=True).returncode == 0), None)
            if py:
                print("impedance: field solver in a child process (%s)" % py, flush=True)
                r = subprocess.run([py, "-I", os.path.abspath(__file__), "impedance", "--fd", "--json-only"],
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    sys.exit("field solver failed:\n" + r.stdout[-2000:] + r.stderr[-2000:])
                return json.load(open(IMPEDANCE_JSON))
            print("WARNING: no numpy/scipy anywhere; RF width from the closed forms, field solver not run")
    rec = {"_comment": "Written by setup_board.py (impedance step). 50 ohm widths for the RF layers: L1 over L2 "
                       "and L6 over L5 have the same geometry (stackup.json). Widths in mm, Z0 in ohm.",
           "inputs": inp, "closed_forms": closed_forms(inp), "field_solver": fd}
    if fd:
        rec["rf_width_mm"] = fd["rf_width"]["w"]
    else:
        cf = rec["closed_forms"]["er %.2f" % inp["er"]]["microstrip_hj_bare_w50"]
        rec["rf_width_mm"] = round(round(cf / 0.005) * 0.005, 3)
    if write and json.dumps(rec, sort_keys=True) != json.dumps(old, sort_keys=True):
        with open(IMPEDANCE_JSON, "w") as f:
            f.write(json.dumps(rec, indent=2) + "\n")
    return rec


def rf_values(rec):
    w = rec["rf_width_mm"]
    fd = rec.get("field_solver") or {}
    z = fd.get("rf_width", {}).get("z0", {})
    note = ", ".join("%s ohm at Er %s" % (v, k.split()[1]) for k, v in z.items()) or "closed form only (no field solver)"
    return {"W_RF": "%.3f" % w, "W_MIN": "%.3f" % (w - 0.005), "W_MAX": "%.3f" % (w + 0.005),
            "GAP": "%.2f" % RF_GAP, "Z_NOTE": note, "w": w}


def impedance_report(rec):
    L = ["Impedance record (%s)" % os.path.relpath(IMPEDANCE_JSON, HW)]
    inp = rec["inputs"]
    L.append("  L1/L6: h %.3f mm, t %.3f mm, Er %.2f (stackup) / %.2f (alt), CPWG gap %.2f, mask %s"
             % (inp["h"], inp["t"], inp["er"], inp["er_alt"], inp["gap"], inp["mask"]))
    for k, v in rec["closed_forms"].items():
        L.append("  closed form %s: microstrip HJ bare w50 %.4f, CPWG (KiCad calculator model) bare w50 %.4f"
                 % (k, v["microstrip_hj_bare_w50"], v["cpwg_kicad_calculator_bare_w50"]))
    fd = rec.get("field_solver")
    if fd:
        for k, v in fd["validation"].items():
            L.append("  validation %s: field solver %.2f ohm, Hammerstad-Jensen %.2f ohm" % (k, v["fd"], v["hammerstad_jensen"]))
        for k in [k for k in fd if k.startswith("er ")]:
            for name, v in fd[k].items():
                L.append("  field solver %s %s: w50 %.4f" % (k, name, v["w50"]))
        L.append("  RF width %.3f mm -> %s" % (fd["rf_width"]["w"], fd["rf_width"]["z0"]))
    else:
        L.append("  field solver: not run")
    return "\n".join(L)


# ==============================================================================================================
# 2. Geometry (pure Python): outline primitives, rule-area polygons
# ==============================================================================================================
def outline_primitives():
    """Edge.Cuts primitives relative to the centre: ("line", a, b), ("arc", start, mid, end), ("circle", c, r)."""
    B, P, RE, RF = BODY_HALF, HOLE_HALF, EAR_R, EAR_FILLET
    dxf = math.sqrt((RE + RF) ** 2 - (B - P + RF) ** 2)    # fillet centre offset along the edge from the hole

    def ear(sx, sy):
        E = (sx * P, sy * P)
        Fh = (sx * P - sx * dxf, sy * (B + RF))            # fillet on the horizontal edge (y = sy B)
        Fv = (sx * (B + RF), sy * P - sy * dxf)            # fillet on the vertical edge (x = sx B)
        on = lambda F: (E[0] + RE * (F[0] - E[0]) / (RE + RF), E[1] + RE * (F[1] - E[1]) / (RE + RF))
        return {"E": E, "Fh": Fh, "Fv": Fv, "Th": (Fh[0], sy * B), "Tv": (sx * B, Fv[1]), "Uh": on(Fh), "Uv": on(Fv),
                "M": (E[0] + RE * sx / math.sqrt(2), E[1] + RE * sy / math.sqrt(2))}

    def minor_mid(C, r, a, b):
        a1, a2 = math.atan2(a[1] - C[1], a[0] - C[0]), math.atan2(b[1] - C[1], b[0] - C[0])
        d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        return (C[0] + r * math.cos(a1 + d / 2), C[1] + r * math.sin(a1 + d / 2))

    def ear_path(e, first):          # first: "h" when the path arrives along the horizontal edge
        if first == "h":
            seq = [("Th", "Uh", "Fh"), None, ("Uv", "Tv", "Fv")]
            arc = (e["Uh"], e["M"], e["Uv"])
        else:
            seq = [("Tv", "Uv", "Fv"), None, ("Uh", "Th", "Fh")]
            arc = (e["Uv"], e["M"], e["Uh"])
        out = []
        for s in seq:
            if s is None:
                out.append(("arc",) + arc)
            else:
                a, b, F = e[s[0]], e[s[1]], e[s[2]]
                out.append(("arc", a, minor_mid(e[s[2]], RF, a, b), b))
        return out

    L, R, Q = ear(-1, -1), ear(1, 1), ear(-1, 1)            # left, right, rear
    fc = B - FRONT_R
    C = (fc, -fc)
    prims = [("line", L["Th"], (fc, -B)),
             ("arc", (fc, -B), (C[0] + FRONT_R / math.sqrt(2), C[1] - FRONT_R / math.sqrt(2)), (B, -fc)),
             ("line", (B, -fc), R["Tv"])]
    prims += ear_path(R, "v")
    prims.append(("line", R["Th"], Q["Th"]))
    prims += ear_path(Q, "h")
    prims.append(("line", Q["Tv"], L["Tv"]))
    prims += ear_path(L, "v")
    for name, (sx, sy) in HOLES.items():
        prims.append(("circle", (sx * HOLE_HALF, sy * HOLE_HALF), HOLE_D / 2))
    return prims


def arc_points(a, m, e, sag=0.001):
    """Points from a to e (inclusive) on the circle through a, m, e, chords with at most `sag` mm sagitta."""
    ax, ay = a
    bx, by = m
    cx, cy = e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    t = lambda p: math.atan2(p[1] - uy, p[0] - ux)
    s0, de, dm = t(a), (t(e) - t(a)) % (2 * math.pi), (t(m) - t(a)) % (2 * math.pi)
    sweep = de if dm < de else de - 2 * math.pi
    n = max(2, math.ceil(abs(sweep) / (2 * math.acos(1 - sag / r))))
    return [(ux + r * math.cos(s0 + sweep * i / n), uy + r * math.sin(s0 + sweep * i / n)) for i in range(n + 1)]


def outline_points(sag=0.001):
    """The spec 7 outline as (outer contour, [hole contours]) of points, from the analytic primitives."""
    outer, holes = [], []
    for kind, *g in outline_primitives():
        if kind == "line":
            outer.append(g[0])
        elif kind == "arc":
            outer += arc_points(*g, sag=sag)[:-1]
        else:
            n = math.ceil(2 * math.pi / (2 * math.acos(1 - sag / g[1])))
            holes.append(circle_pts(g[0], g[1], n))
    return outer, holes


def circle_pts(c, r, n=72):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rect_along(a, b, hw):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    nx, ny = -dy / n * hw, dx / n * hw
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def stadium(a, b, r, n=36):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    pts = [(b[0] + r * math.cos(ang - math.pi / 2 + math.pi * i / n), b[1] + r * math.sin(ang - math.pi / 2 + math.pi * i / n)) for i in range(n + 1)]
    pts += [(a[0] + r * math.cos(ang + math.pi / 2 + math.pi * i / n), a[1] + r * math.sin(ang + math.pi / 2 + math.pi * i / n)) for i in range(n + 1)]
    return pts


CU = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]


def rect(p0, p1):
    return [(p0[0], p0[1]), (p1[0], p0[1]), (p1[0], p1[1]), (p0[0], p1[1])]


def tab_rect(name):
    """Part keepout at a panel tab: TAB_HALF along the edge each way, TAB_IN inward, TAB_OUT outward (clipped)."""
    t = TABS[name]
    if t == "front_arc_45":
        fc = BODY_HALF - FRONT_R
        n = (FRONT[0] / math.sqrt(2), FRONT[1] / math.sqrt(2))
        p = (fc + FRONT_R * n[0], -fc + FRONT_R * n[1])
    else:
        p, n = t
    tv = (-n[1], n[0])
    c = lambda a, d: (p[0] + a * tv[0] + d * n[0], p[1] + a * tv[1] + d * n[1])
    return [c(-TAB_HALF, TAB_OUT), c(TAB_HALF, TAB_OUT), c(TAB_HALF, -TAB_IN), c(-TAB_HALF, -TAB_IN)]


# (name, layers, keepout flags (footprints, tracks, vias, pads, zone fills), shape, clip to board, spec note)
# shape: ("poly", points) | ("path", points, half width) | ("band", width)
def keepouts():
    K = []
    for name, (sx, sy) in HOLES.items():
        K.append(("MOUNT_" + name, ["F.Cu", "B.Cu"], dict(footprints=True),
                  ("poly", circle_pts((sx * HOLE_HALF, sy * HOLE_HALF), FLANGE_D / 2)), True,
                  "spec 7: grommet flange D %.1f, no parts, both sides" % FLANGE_D))
    K.append(("PART_EDGE_BAND", ["F.Cu", "B.Cu"], {}, ("band", PART_EDGE_BAND), False,
              "spec 7: %.2f mm part keepout band (DRU 'parts: courtyards off the edge band')" % PART_EDGE_BAND))
    K.append(("RF_VTX_CHAIN", ["In1.Cu"], dict(tracks=True), ("path",) + VTX_CHAIN, True,
              "spec 10: L2 solid under the 5.8 GHz chain plus 1 mm; GND vias only (DRU)"))
    K.append(("RF_VTX_UFL", ["F.Cu"], {}, ("poly", rect(*UFL_ZONE)), True,
              "spec 10: U.FL zone, only RF and GND copper on L1 (DRU)"))
    K.append(("RF_PAD_CUTOUT", ["In1.Cu"], dict(zone_fills=True), ("poly", rect(*RF_PAD_CUT)), True,
              "spec 4.8: L2 cut under the wide RF pads (U.FL signal pad; P5 adds the others)"))
    K.append(("RF_PAD_CUTOUT_L3", ["In2.Cu"], dict(tracks=True), ("poly", rect(*RF_PAD_CUT)), True,
              "spec 4.8: no L3 track where L3 GND is the local RF reference"))
    ring = circle_pts(RX_ANT_HOLE, RX_ANT_KEEPOUT_R)
    K.append(("RF_RX_ANT", CU[:5], dict(footprints=True, pads=True, zone_fills=True),
              ("poly", ring), True, "spec 10: L1-L5 pour/pad/part keepout at the RX antenna hole; tracks and vias net-aware (DRU: only the RF_RX_ANT feed on L1)"))
    K.append(("RF_RX_ANT_L6", ["B.Cu"], dict(footprints=True, vias=True, zone_fills=True), ("poly", ring), True,
              "spec 10: L6 at the hole: only the 2.4 GHz feed track (DRU)"))
    edge_pt = (-BODY_HALF, RX_ANT_HOLE[1])
    K.append(("RF_RX_EXIT", ["B.Cu"], dict(footprints=True), ("poly", stadium(RX_ANT_HOLE, edge_pt, RX_ANT_EXIT_R)), True,
              "spec 10 / v3 (D69, D75): no parts on the antenna wire exit path, hole to edge, r %.1f (bottom)" % RX_ANT_EXIT_R))
    K.append(("RF_RX_FEED", ["In1.Cu"], dict(tracks=True), ("path", [RX_FEED[0], RX_FEED[1]], RX_FEED[2]), True,
              "spec 10: L2 solid under the 2.4 GHz L1 feed (FL1 OUT -> hole); GND vias only (DRU)"))
    K.append(("RF_RX_ROOT", CU, {}, ("poly", circle_pts(RX_ANT_HOLE, RX_ROOT_R)), True,
              "spec 4.9 / 11: SPI0 (blackbox) kept 3 mm from the antenna hole (DRU)"))
    K.append(("SHUNT_CORRIDOR", [SHUNT_LAYER], {}, ("poly", rect(*SHUNT_CORRIDOR)), True,
              "D10 / spec 11: battery-to-shunt corridor, battery current only on the shunt's layer (P2 v3: R1 on top, L1) (DRU)"))
    K.append(("WIFI_ANT_KO", CU, dict(pads=True, vias=True, zone_fills=True), ("poly", rect(*WIFI_KO)), True,
              "D58 / D75: Wi-Fi chip antenna maker copper keep-out, all layers: no pads but AE2's, no vias, no pours;"
              " tracks only the RF feed (DRU)"))
    ux, uy, ur = USB_J31
    hw, hh = USB_BODY[0] / 2 + USB_MARGIN, USB_BODY[1] / 2 + USB_MARGIN
    ca, sa = math.cos(math.radians(-ur)), math.sin(math.radians(-ur))      # KiCad rotation is CCW on screen (+y down)
    usb = [(ux + x * ca - y * sa, uy + x * sa + y * ca) for x, y in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
    K.append(("USB_MATING", ["B.Cu"], {}, ("poly", usb), True,
              "D72 / D76: vertical USB J31 mating zone (body + %.1f mm), no TALL class part inside (DRU)" % USB_MARGIN))
    for t in sorted(TABS):
        K.append(("TAB_" + t, ["F.Cu", "B.Cu"], dict(footprints=True), ("poly", tab_rect(t)), True,
                  "spec 7: panel tab %s, %.1f mm part keepout beyond the edge band" % (t, TAB_IN - PART_EDGE_BAND)))
    return K


def owned_uuid(key):
    h = hashlib.sha1(("OpenAIO-Whoop/setup_board/" + key).encode()).hexdigest()
    return "%s-%s-4%s-8%s-%s" % (UUID_PREFIX, h[0:4], h[4:7], h[7:10], h[10:22])


# ==============================================================================================================
# 3. .kicad_pro and .kicad_dru writers (JSON / text; KiCad re-saves the project afterwards)
# ==============================================================================================================
def write_pro(path, rf):
    p = json.load(open(path))
    ds = p["board"]["design_settings"]
    ds["rules"].update(PRO_RULES)
    ignored_before = sorted(k for k, v in ds["rule_severities"].items() if v == "ignore")
    ds["rule_severities"].update(SEVERITIES)
    ds["defaults"].update(TEXT_DEFAULTS)
    tracks = sorted(set(TRACK_PRESETS + [rf["w"]]))
    ds["track_widths"] = [0.0] + tracks
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}] + [{"diameter": d, "drill": h} for d, h in VIA_PRESETS]
    ds["diff_pair_dimensions"] = [{"gap": 0.0, "via_gap": 0.0, "width": 0.0}] + \
        [{"gap": g, "via_gap": vg, "width": w} for w, g, vg in DIFF_PAIR_PRESETS]
    ns = p["net_settings"]
    base = next(c for c in ns["classes"] if c["name"] == "Default")
    base.update(DEFAULT_CLASS)
    classes = [base]
    for name, tw, cl, vd, vh, col, prio, extra in NETCLASSES:
        c = dict(base)
        c.update({"name": name, "track_width": rf["w"] if tw is None else tw, "clearance": cl, "via_diameter": vd,
                  "via_drill": vh, "pcb_color": col, "schematic_color": col, "priority": prio, "tuning_profile": ""})
        c.update(extra)
        classes.append(c)
    ns["classes"] = classes
    ns["netclass_patterns"] = [{"netclass": n, "pattern": pat} for n, pats in NETCLASS_PATTERNS for pat in pats]
    ns["net_colors"] = {}            # template per-net colours (+3.3V, +10V, ...) would override the class colours
    wnm = int(round(rf["w"] * 1e6))
    p["tuning_profiles"]["tuning_profiles_impedance_geometric"] = [{
        "profile_name": "RF50", "type": 0, "target_impedance": RF_TARGET, "enable_time_domain_tuning": False,
        "via_prop_delay": 0,
        "layer_entries": [
            {"signal_layer": "F.Cu", "top_reference_layer": "UNDEFINED", "bottom_reference_layer": "In1.Cu",
             "width": wnm, "diff_pair_gap": 0, "delay": 0},
            {"signal_layer": "B.Cu", "top_reference_layer": "In4.Cu", "bottom_reference_layer": "UNDEFINED",
             "width": wnm, "diff_pair_gap": 0, "delay": 0}],
        "via_overrides": []}]
    asg = []
    for cls, pats in COMPONENT_CLASSES:
        cond = {("FOOTPRINT" if i == 0 else "FOOTPRINT-%d" % i): {"primary": pat} for i, pat in enumerate(pats)}
        asg.append({"component_class": cls, "conditions_operator": "ANY", "conditions": cond})
    for cls, refs in sheet_classes():                  # D75: one class per schematic sheet, by reference
        cond = {("REFERENCE" if i == 0 else "REFERENCE-%d" % i): {"primary": r} for i, r in enumerate(refs)}
        asg.append({"component_class": cls, "conditions_operator": "ANY", "conditions": cond})
    p["component_class_settings"]["assignments"] = asg
    with open(path, "w") as f:
        f.write(json.dumps(p, indent=2) + "\n")
    return ignored_before


CANONICAL = '''(version 1)

# OpenDrone canonical design rules.
#
# Copied from hardware-template into every board repo. Keep the block above the
# marker byte-identical across repos. Board-specific rules go
# below the marker, never in the middle.
#
# This file holds CUSTOM rules only. The fab numbers that gate a JLCPCB order
# live in the project file under board.design_settings.rules, and come from
# Board Setup > Import Settings from Another Board, pointed at
# kicad/templates/OpenDrone-6L. The line standard is:
#
#   clearance 0.09   track 0.09   via 0.35 / 0.20 drill
#   annular 0.075    hole-to-hole 0.20        edge clearance 0.20
#
# Do not restate those here. Two copies of a number drift, and the one you are
# not looking at is the one that is wrong.

(rule "silkscreen over pad"
  (constraint silk_clearance (min 0.15mm))
  (condition "A.Type == 'Pad'"))

# --- board-specific rules below this line ------------------------------------
'''
MARKER = "# --- board-specific rules below this line ------------------------------------\n"


def dru_text(rf, existing):
    head = existing[:existing.index(MARKER) + len(MARKER)] if MARKER in existing else None
    if head != CANONICAL:
        sys.exit("the canonical block of %s differs from hardware-template; not touching it" % DRU)
    sub = dict(rf)
    sub["SOLDER_PAD_FPID"] = " || ".join("A.memberOfFootprint('%s')" % p for p in SOLDER_PAD_FPIDS)
    sub["BAND"] = "%.2f" % PART_EDGE_BAND
    sub["SHUNT_LAYER"] = SHUNT_LAYER
    out = [CANONICAL]
    for name, comment, body in RULES:
        out.append("#\n" if name == "header" else "\n")
        for c in comment:
            for k, v in sub.items():
                c = c.replace("@%s@" % k, str(v))
            out.append(("# " + c).rstrip() + "\n")
        if body:
            for k, v in sub.items():
                body = body.replace("@%s@" % k, str(v))
            out.append('(rule "%s"\n%s)\n' % (name, body))
    text = "".join(out)
    if "@" in re.sub(r"#.*", "", text):
        sys.exit("unfilled @ marker in the DRU")
    return text


# ==============================================================================================================
# 4. Board (pcbnew)
# ==============================================================================================================
def quiet_pcbnew():
    saved, null = os.dup(2), os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 2)
    try:
        import pcbnew
    finally:
        os.dup2(saved, 2)
        os.close(saved)
        os.close(null)
    return pcbnew


def stackup_sexpr(indent):
    spec = json.load(open(STACKUP_JSON))
    L = spec["layers"]

    def fmt(v):
        return ("%.4f" % v).rstrip("0").rstrip(".")
    out = [indent + "(stackup"]
    rows = [("F.SilkS", "Top Silk Screen"), ("F.Paste", "Top Solder Paste"), ("F.Mask", "Top Solder Mask")]
    rows += [(n, None) for n in L if n not in ("F.Mask", "B.Mask")]
    rows += [("B.Mask", "Bottom Solder Mask"), ("B.Paste", "Bottom Solder Paste"), ("B.SilkS", "Bottom Silk Screen")]
    for name, typ in rows:
        v = L.get(name, {})
        out.append(indent + '\t(layer "%s"' % name)
        if name.endswith(".Cu"):
            out.append(indent + '\t\t(type "copper")')
        elif name.startswith("dielectric"):
            out.append(indent + '\t\t(type "%s")' % v["type"])
        else:
            out.append(indent + '\t\t(type "%s")' % typ)
        if name.endswith("SilkS"):
            out.append(indent + '\t\t(color "%s")' % SILK_COLOR)
        if name.endswith("Mask"):
            out.append(indent + '\t\t(color "%s")' % MASK_STACKUP["color"])
        if "thickness" in v:
            out.append(indent + "\t\t(thickness %s)" % fmt(v["thickness"]))
        if name.startswith("dielectric"):
            out.append(indent + '\t\t(material "%s")' % v["material"])
            out.append(indent + "\t\t(epsilon_r %s)" % fmt(v["epsilon_r"]))
            out.append(indent + "\t\t(loss_tangent %s)" % fmt(v["loss_tangent"]))
        if name.endswith("Mask"):
            out.append(indent + "\t\t(epsilon_r %s)" % fmt(MASK_STACKUP["epsilon_r"]))
            out.append(indent + "\t\t(loss_tangent %s)" % fmt(MASK_STACKUP["loss_tangent"]))
        out.append(indent + "\t)")
    out.append(indent + '\t(copper_finish "%s")' % spec.get("copper_finish", "ENIG"))
    out.append(indent + "\t(dielectric_constraints yes)")      # impedance controlled
    out.append(indent + ")")
    return "\n".join(out), round(sum(v.get("thickness", 0) for v in L.values()), 4)


def balanced_end(text, start):
    depth, i, instr = 0, start, False
    while i < len(text):
        c = text[i]
        if instr:
            if c == "\\":
                i += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced s-expression")


def splice_stackup(path):
    text = open(path).read()
    i = text.find("(stackup")
    if i < 0:
        raise SystemExit("pcbnew wrote no stackup node")
    j = balanced_end(text, i)
    ls = text.rfind("\n", 0, i) + 1
    sx, total = stackup_sexpr(text[ls:i])
    open(path, "w").write(text[:ls] + sx + text[j:])
    return total


def build_board(path, P):
    """All pcbnew edits on the temp board.  Returns a summary dict."""
    mm = P.FromMM
    cx, cy = CENTRE
    V = lambda p: P.VECTOR2I(mm(cx + p[0]), mm(cy + p[1]))
    b = P.LoadBoard(path)
    ds = b.GetDesignSettings()
    if b.GetCopperLayerCount() != 6:
        b.SetCopperLayerCount(6)
    for lname, kind in (("In1.Cu", P.LT_POWER), ("In4.Cu", P.LT_POWER), ("In3.Cu", P.LT_MIXED),
                        ("In2.Cu", P.LT_SIGNAL), ("F.Cu", P.LT_SIGNAL), ("B.Cu", P.LT_SIGNAL)):
        b.SetLayerType(b.GetLayerID(lname), kind)
    ds.m_HasStackup = True
    ds.m_SolderMaskExpansion = mm(MASK_EXPANSION)
    ds.m_SolderMaskMinWidth = mm(MASK_MIN_WEB)
    ds.m_TentViasFront = ds.m_TentViasBack = True
    ds.m_FillVias = ds.m_CapVias = VIA_FILL_CAP
    ds.SetGridOrigin(V((0, 0)))
    ds.SetAuxOrigin(V((0, 0)))
    tb = b.GetTitleBlock()
    tb.SetRevision(TITLE_REV)
    b.SetTitleBlock(tb)

    # remove everything this script owns, and any stray board-level outline
    removed = 0
    for item in list(b.GetDrawings()) + list(b.Zones()):
        own = item.m_Uuid.AsString().startswith(UUID_PREFIX + "-")
        if own or (item.GetClass() == "PCB_SHAPE" and item.GetLayer() == P.Edge_Cuts):
            if not own:
                print("  note: removing a board-level Edge.Cuts item the script did not draw")
            b.Delete(item)
            removed += 1

    def add_shape(kind, layer, key, *geo, width=EDGE_LINE_W):
        s = P.PCB_SHAPE(b)
        s.SetLayer(layer)
        s.SetWidth(mm(width))
        if kind == "line":
            s.SetShape(P.SHAPE_T_SEGMENT)
            s.SetStart(V(geo[0]))
            s.SetEnd(V(geo[1]))
        elif kind == "arc":
            s.SetShape(P.SHAPE_T_ARC)
            s.SetArcGeometry(V(geo[0]), V(geo[1]), V(geo[2]))
        elif kind == "circle":
            s.SetShape(P.SHAPE_T_CIRCLE)
            s.SetCenter(V(geo[0]))
            s.SetEnd(V((geo[0][0] + geo[1], geo[0][1])))
        s.SetUuid(P.KIID(owned_uuid(key)))
        b.Add(s)

    def add_text(layer, key, text, pos, size=1.0, thick=0.15, mirrored=False):
        t = P.PCB_TEXT(b)
        t.SetLayer(layer)
        t.SetText(text)
        t.SetPosition(V(pos))
        t.SetTextSize(P.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thick))
        t.SetMirrored(mirrored)
        t.SetUuid(P.KIID(owned_uuid(key)))
        b.Add(t)

    for i, (kind, *geo) in enumerate(outline_primitives()):
        add_shape(kind, P.Edge_Cuts, "edge/%d" % i, *geo)

    # guides (not fabricated): frame patterns, front marker, grommet flanges, layer roles
    eco1, eco2, u1, cmts = (b.GetLayerID(n) for n in ("User.Eco1", "User.Eco2", "User.1", "User.Comments"))
    for s in FRAME_PATTERNS:
        for qx in (-1, 1):
            for qy in (-1, 1):
                c = (qx * s / 2, qy * s / 2)
                k = "eco1/%.1f/%d%d" % (s, qx, qy)
                add_shape("circle", eco1, k + "/c", c, 0.5, width=0.05)
                add_shape("line", eco1, k + "/h", (c[0] - 0.8, c[1]), (c[0] + 0.8, c[1]), width=0.05)
                add_shape("line", eco1, k + "/v", (c[0], c[1] - 0.8), (c[0], c[1] + 0.8), width=0.05)
    add_text(eco1, "eco1/label", "FRAME 25.5 / 26.0", (0.0, -17.5), size=0.8, thick=0.1)
    a0, a1 = (12.5, -12.5), (16.5, -16.5)
    add_shape("line", eco2, "eco2/arrow", a0, a1, width=0.15)
    add_shape("line", eco2, "eco2/head1", a1, (a1[0] - 1.0, a1[1]), width=0.15)
    add_shape("line", eco2, "eco2/head2", a1, (a1[0], a1[1] + 1.0), width=0.15)
    add_text(eco2, "eco2/text", "FRONT", (17.0, -18.2), size=1.0, thick=0.15)
    for name, (sx, sy) in HOLES.items():
        add_shape("circle", u1, "user1/" + name, (sx * HOLE_HALF, sy * HOLE_HALF), FLANGE_D / 2, width=0.05)
    add_text(cmts, "cmts/layers", "F.Cu sig | In1 GND | In2 sig | In3 +BATT/PWR | In4 GND | B.Cu sig",
             (0.0, 18.5), size=0.8, thick=0.1)

    # outline polygon for clipping and the band, from the analytic geometry (deterministic: the board's own
    # polygon can still see the deleted arcs, whose re-loaded mid points differ by a nanometre)
    outer_pts, hole_pts = outline_points()
    poly = P.SHAPE_POLY_SET()
    poly.NewOutline()
    for p in outer_pts:
        v = V(p)
        poly.Append(v.x, v.y)
    for k, hp in enumerate(hole_pts):
        poly.NewHole(0)
        for p in hp:
            v = V(p)
            poly.Append(v.x, v.y, 0, k)

    def to_poly(pts):
        s = P.SHAPE_POLY_SET()
        s.NewOutline()
        for p in pts:
            v = V(p)
            s.Append(v.x, v.y)
        return s

    zones = []
    for name, layers, flags, shape, clip, note in keepouts():
        if shape[0] == "band":
            outer = P.SHAPE_POLY_SET(poly.COutline(0))       # outer contour only; holes have MOUNT_* areas
            inner = P.SHAPE_POLY_SET(outer)
            inner.Deflate(mm(shape[1]), P.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.002))
            area = P.SHAPE_POLY_SET()
            area.BooleanSubtract(outer, inner)
        elif shape[0] == "path":
            pts, hw = shape[1], shape[2]
            area = P.SHAPE_POLY_SET()
            for seg in [rect_along(p, q, hw) for p, q in zip(pts, pts[1:])] + [circle_pts(p, hw, 48) for p in pts]:
                area.BooleanAdd(to_poly(seg))
            area.Simplify()
            if clip:
                area.BooleanIntersection(poly)
        else:
            area = to_poly(shape[1])
            if clip:
                area.BooleanIntersection(poly)
        if area.OutlineCount() != 1:
            raise SystemExit("rule area %s has %d outlines (a zone keeps one)" % (name, area.OutlineCount()))
        z = P.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetZoneName(name)
        ls = P.LSET()
        for ln in layers:
            ls.AddLayer(b.GetLayerID(ln))
        z.SetLayerSet(ls)
        z.SetDoNotAllowFootprints(bool(flags.get("footprints")))
        z.SetDoNotAllowTracks(bool(flags.get("tracks")))
        z.SetDoNotAllowVias(bool(flags.get("vias")))
        z.SetDoNotAllowPads(bool(flags.get("pads")))
        z.SetDoNotAllowZoneFills(bool(flags.get("zone_fills")))
        z.Outline().RemoveAllContours()
        z.Outline().Append(area)
        z.SetUuid(P.KIID(owned_uuid("zone/" + name)))
        b.Add(z)
        zones.append((name, layers, sorted(k for k, v in flags.items() if v), round(area.Area() / 1e12, 2), note))
    if not P.SaveBoard(path, b):
        raise SystemExit("pcbnew could not save the temp board")
    return {"removed": removed, "zones": zones}


def verify_board(path, P):
    """Read the saved board back: stackup values, settings, outline, zones.  Returns report lines."""
    text = open(path).read()
    spec = json.load(open(STACKUP_JSON))
    i = text.find("(stackup")
    s = text[i:balanced_end(text, i)]
    bad = []
    for name, v in spec["layers"].items():
        m = re.search(r'\(layer "%s"(.*?)\n\t\t\t\)' % re.escape(name), s, re.S)
        if not m:
            bad.append("stackup layer %s missing" % name)
            continue
        blk = m.group(1)
        for key in ("thickness", "epsilon_r", "loss_tangent"):
            if key in v:
                mm_ = re.search(r"\(%s ([\d.]+)\)" % key, blk)
                if not mm_ or abs(float(mm_.group(1)) - v[key]) > 1e-6:
                    bad.append("%s %s" % (name, key))
        for key in ("material", "type"):
            if key in v and '(%s "%s")' % (key, v[key]) not in blk:
                bad.append("%s %s" % (name, key))
    for need in ('(copper_finish "%s")' % spec.get("copper_finish", "ENIG"), "(dielectric_constraints yes)",
                 '(color "%s")' % MASK_STACKUP["color"], '(color "%s")' % SILK_COLOR, "(filling yes)", "(capping yes)",
                 '(rev "%s")' % TITLE_REV):
        if need not in text:
            bad.append("missing " + need)
    b = P.LoadBoard(path)
    ds = b.GetDesignSettings()
    mm = lambda v: round(P.ToMM(v), 4)
    poly = P.SHAPE_POLY_SET()
    closed = b.GetBoardPolygonOutlines(poly, False)
    bb = poly.BBox()
    holes = [poly.CHole(0, j).BBox() for j in range(poly.HoleCount(0))] if closed else []
    rep = {
        "copper_layers": b.GetCopperLayerCount(), "thickness": mm(ds.GetBoardThickness()),
        "mask_expansion": mm(ds.m_SolderMaskExpansion), "mask_min_web": mm(ds.m_SolderMaskMinWidth),
        "outline_closed": closed, "outline_bbox": [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())],
        "outline_size": [mm(bb.GetWidth()), mm(bb.GetHeight())], "outline_area": round(poly.Area() / 1e12, 2),
        "holes": [(round(mm(h.Centre().x) - CENTRE[0], 3), round(mm(h.Centre().y) - CENTRE[1], 3), mm(h.GetWidth())) for h in holes],
        "grid_origin": [mm(ds.GetGridOrigin().x), mm(ds.GetGridOrigin().y)],
        "aux_origin": [mm(ds.GetAuxOrigin().x), mm(ds.GetAuxOrigin().y)],
        "zones": sorted((z.GetZoneName(), z.GetIsRuleArea()) for z in b.Zones()),
    }
    if rep["copper_layers"] != 6:
        bad.append("copper layers")
    if not closed or len(holes) != len(HOLES):
        bad.append("outline closed %s with %d holes" % (closed, len(holes)))
    if bad:
        raise SystemExit("board verification failed: " + "; ".join(bad))
    return rep


def verify_pro(path, rf):
    p = json.load(open(path))
    ds = p["board"]["design_settings"]
    bad = [k for k, v in PRO_RULES.items() if abs(ds["rules"].get(k, -1) - v) > 1e-9]
    bad += ["severity " + k for k, v in SEVERITIES.items() if ds["rule_severities"].get(k) != v]
    names = {c["name"]: c for c in p["net_settings"]["classes"]}
    bad += ["netclass " + n[0] for n in NETCLASSES if n[0] not in names]
    if names.get("RF", {}).get("tuning_profile") != "RF50":
        bad.append("RF tuning profile link")
    prof = p["tuning_profiles"]["tuning_profiles_impedance_geometric"]
    if not prof or prof[0]["layer_entries"][0]["width"] != int(round(rf["w"] * 1e6)):
        bad.append("tuning profile RF50")
    if len(p["component_class_settings"]["assignments"]) != len(COMPONENT_CLASSES) + len(sheet_classes()):
        bad.append("component classes")
    if len(p["net_settings"]["netclass_patterns"]) != sum(len(x[1]) for x in NETCLASS_PATTERNS):
        bad.append("netclass patterns")
    if bad:
        raise SystemExit(".kicad_pro verification failed (KiCad dropped or changed): " + ", ".join(bad))


# ==============================================================================================================
# 5. Self test: synthetic items on a copy of the generated board, kicad-cli DRC, expected hits / no hits
# ==============================================================================================================
def selftest(P, rf):
    mm = P.FromMM
    tmp = tempfile.mkdtemp(prefix="setup_board_selftest_")
    for src in (PCB, PRO, DRU):
        shutil.copy(src, os.path.join(tmp, os.path.basename(src)))
    for t in ("fp-lib-table", "sym-lib-table"):
        if os.path.exists(os.path.join(HW, t)):
            shutil.copy(os.path.join(HW, t), tmp)
    os.symlink(os.path.join(HW, "KiCad-Library"), os.path.join(tmp, "KiCad-Library"))
    pcb = os.path.join(tmp, os.path.basename(PCB))
    b = P.LoadBoard(pcb)
    for fp in list(b.GetFootprints()):          # the synthetic cases need an empty board (P2 placed parts)
        b.Delete(fp)
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (P.F_SilkS, P.B_SilkS) and not d.m_Uuid.AsString().startswith(UUID_PREFIX + "-"):
            b.Delete(d)
    cx, cy = CENTRE
    V = lambda x, y: P.VECTOR2I(mm(cx + x), mm(cy + y))
    nets, cases = {}, []
    lib = os.path.join(HW, "KiCad-Library", "footprint", "OpenDrone.pretty")

    def net(name):
        if name not in nets:
            n = P.NETINFO_ITEM(b, name)
            b.Add(n)
            nets[name] = n
        return nets[name]

    def trk(x1, y1, x2, y2, w, name, layer="F.Cu"):
        t = P.PCB_TRACK(b)
        t.SetStart(V(x1, y1))
        t.SetEnd(V(x2, y2))
        t.SetWidth(mm(w))
        t.SetLayer(b.GetLayerID(layer))
        t.SetNet(net(name))
        b.Add(t)

    def via(x, y, d, dr, name, kind=None):
        v = P.PCB_VIA(b)
        v.SetPosition(V(x, y))
        v.SetViaType(kind if kind is not None else P.VIATYPE_THROUGH)
        v.SetWidth(mm(d))
        v.SetDrill(mm(dr))
        if kind == P.VIATYPE_MICROVIA:
            v.SetLayerPair(P.F_Cu, b.GetLayerID("In1.Cu"))
        else:
            v.SetLayerPair(P.F_Cu, P.B_Cu)
        v.SetNet(net(name))
        b.Add(v)

    def fp(name, ref, x, y, rot=0, back=False, padnet=None, edge_gap=None):
        f = P.FootprintLoad(lib, name)
        f.SetFPID(P.LIB_ID("OpenDrone", name))
        f.SetReference(ref)
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)
        for g in list(f.GraphicalItems()):
            if g.GetLayer() in (P.F_SilkS, P.B_SilkS):
                f.Delete(g)
        f.SetPosition(V(x, y))
        f.SetOrientationDegrees(rot)
        b.Add(f)
        if back:
            f.Flip(f.GetPosition(), P.FLIP_DIRECTION_LEFT_RIGHT)
        for p in f.Pads():
            p.SetNet(net(padnet or "/T/%s_%s" % (ref, p.GetNumber())))
        if edge_gap is not None:          # move so the nearest pad edge is edge_gap from the top (-) or bottom (+) edge
            top = min(p.GetBoundingBox().GetTop() for p in f.Pads())
            bot = max(p.GetBoundingBox().GetBottom() for p in f.Pads())
            want = mm(cy - BODY_HALF + edge_gap) - top if y < 0 else mm(cy + BODY_HALF - edge_gap) - bot
            f.Move(P.VECTOR2I(0, want))
        return f

    def text(x, y, s, layer="F.SilkS", size=1.0, thick=0.15):
        t = P.PCB_TEXT(b)
        t.SetText(s)
        t.SetLayer(b.GetLayerID(layer))
        t.SetPosition(V(x, y))
        t.SetTextSize(P.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thick))
        b.Add(t)
        return t

    def case(tag, expect, xy, r=0.6):
        cases.append((tag, expect, (cx + xy[0], cy + xy[1]), r))

    # plated and non-plated holes in a synthetic footprint
    def tht(ref, x, y, pads, netname=None):
        f = P.FOOTPRINT(b)
        f.SetReference(ref)
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)
        f.SetPosition(V(x, y))
        b.Add(f)
        for i, (dx_, dia, drill, plated) in enumerate(pads):
            pd = P.PAD(f)
            pd.SetNumber(str(i + 1))
            pd.SetAttribute(P.PAD_ATTRIB_PTH if plated else P.PAD_ATTRIB_NPTH)
            pd.SetShape(P.PAD_SHAPE_CIRCLE)
            pd.SetSize(P.F_Cu, P.VECTOR2I(mm(dia), mm(dia)))
            pd.SetDrillSize(P.VECTOR2I(mm(drill), mm(drill)))
            pd.SetLayerSet(P.PAD.PTHMask() if plated else P.PAD.UnplatedHoleMask())
            pd.SetPosition(V(x + dx_, y))
            f.Add(pd)
            if plated:
                pd.SetNet(net(netname or "/T/%s_%d" % (ref, i + 1)))
        return f
    W = rf["w"]
    KEEPOUT_HIT = "items_not_allowed: Items not allowed |"      # rule-area keepouts carry no rule name
    # standard numbers
    via(-6, -9, 0.35, 0.20, "/T/V1"); case("via 0.35 / 0.20 (D6 standard)", None, (-6, -9))
    via(-6, -7, 0.30, 0.20, "/T/V2"); case("via 0.30 / 0.20", "min diameter 0.3500", (-6, -7))
    via(-4, -9, 0.35, 0.20, "/T/V3"); via(-3.55, -9, 0.35, 0.20, "/T/V4")
    case("vias of two nets, holes 0.25 apart", "rule 'hole to hole, different nets 0.30'", (-3.8, -9))
    via(-4, -7, 0.35, 0.20, "/T/V5"); via(-3.55, -7, 0.35, 0.20, "/T/V5")
    case("vias of one net, holes 0.25 apart", None, (-3.8, -7))
    via(-2, -9, 0.35, 0.15, "/T/V6", P.VIATYPE_MICROVIA); case("microvia", "through vias only", (-2, -9))
    via(-8, -7, 0.35, 0.15, "/T/V7"); case("via 0.35 / 0.15 (below the 0.20 minimum through hole)", "drill", (-8, -7))
    # RF
    trk(-1, -9, 1, -9, W, "/VTX/RF_OUT"); case("RF track at the 50 ohm width", None, (0, -9), r=1.1)
    trk(-1, -7, 1, -7, 0.14, "/VTX/RF_IN"); case("RF track 0.14 wide", "RF: 50 ohm width", (0, -7), r=1.1)
    via(2, -9, 0.35, 0.20, "/VTX/RF_X"); case("via on an RF net", "RF: no vias", (2, -9))
    ux, uy = UFL_VTX
    trk(ux - 0.5, uy, ux + 0.5, uy, 0.1, "/T/SIG1"); case("signal track in RF_VTX_UFL", "RF_VTX_UFL", (ux, uy))
    trk(ux - 0.5, uy + 1, ux + 0.5, uy + 1, 0.2, "GND"); case("GND track in RF_VTX_UFL", None, (ux, uy + 1), r=0.3)
    c0, c1 = max(zip(VTX_CHAIN[0], VTX_CHAIN[0][1:]), key=lambda pq: math.dist(*pq))   # longest chain segment
    trk(c0[0] - 0.4, c0[1] - 1.5, c0[0] + 0.4, c0[1] - 1.5, 0.1, "/T/SIG2", "In1.Cu")
    case("In1 track under the VTX chain (keepout RF_VTX_CHAIN)", KEEPOUT_HIT, (c0[0], c0[1] - 1.5), r=0.8)
    via(c0[0], c0[1] - 3.0, 0.35, 0.20, "/T/V8"); case("signal via in RF_VTX_CHAIN", "RF_VTX_CHAIN: GND vias only", (c0[0], c0[1] - 3.0), r=0.4)
    via(c1[0] + 0.6, c1[1], 0.35, 0.20, "GND"); case("GND via in RF_VTX_CHAIN", None, (c1[0] + 0.6, c1[1]), r=0.3)
    trk(-3, 3, -2, 3, 0.1, "/T/SIG3", "In4.Cu"); case("In4 track (plane warning)", "In1 and In4 are solid GND planes", (-2.5, 3))
    ax, ay = RX_ANT_HOLE
    trk(ax + 0.2, ay - 1.1, ax + 1.0, ay - 1.1, 0.1, "/T/SIG4", "B.Cu"); case("signal track in RF_RX_ANT_L6", "RF_RX_ANT_L6: only the RF feed", (ax + 0.6, ay - 1.1))
    trk(ax + 0.2, ay + 0.9, ax + 1.0, ay + 0.9, W, "/RX/ANT_FEED", "B.Cu"); case("RF feed in RF_RX_ANT_L6", None, (ax + 0.6, ay + 0.9), r=0.3)
    trk(ax + 0.2, ay + 1.2, ax + 0.8, ay + 1.2, W, "/RX/RF_X2", "F.Cu"); case("other RF track on L1 in RF_RX_ANT", "RF_RX_ANT: only the RF feed on L1", (ax + 0.5, ay + 1.2), r=0.6)
    trk(ax + 0.6, ay - 0.9, ax + 1.2, ay - 0.9, W, "/RX/RF_RX_ANT", "F.Cu"); case("RX feed on L1 in RF_RX_ANT", None, (ax + 0.9, ay - 0.9), r=0.3)
    tht("AE1", ax, ay, [(0, 1.0, 0.5, True)], netname="/RX/ANT_FEED"); case("antenna hole footprint AE1 at the hole", None, (ax, ay), r=0.45)
    trk(ax + 1.9, ay + 1.0, ax + 2.3, ay + 1.0, 0.1, "/FC/SPI0.SCK"); case("SPI0 track 2.3 mm from the antenna hole", "SPI0 3 mm from the RX antenna hole", (ax + 2.1, ay + 1.0), r=0.6)
    trk(6.0, 9.5, 7.0, 9.5, 0.1, "/FC/SPI0.MOSI"); case("SPI0 track far from the hole", None, (6.5, 9.5), r=0.6)
    trk(ax + 1.9, ay - 1.6, ax + 2.3, ay - 1.6, 0.1, "/SPI0_SCK"); case("schematic SPI0 net /SPI0_SCK 2.6 mm from the antenna hole", "SPI0 3 mm from the RX antenna hole", (ax + 2.1, ay - 1.6), r=0.6)
    trk(ax + 1.9, ay + 2.0, ax + 2.3, ay + 2.0, 0.1, "/FLASH_CS"); case("NOR chip select /FLASH_CS 2.9 mm from the antenna hole", "SPI0 3 mm from the RX antenna hole", (ax + 2.1, ay + 2.0), r=0.4)
    fx, fy = RX_FEED[0]
    via(fx - 0.3, fy + 0.15, 0.35, 0.20, "/T/V9"); case("signal via in RF_RX_FEED", "RF_RX_FEED: GND vias only", (fx - 0.3, fy + 0.15), r=0.4)
    # inner-layer bans (In2 / In3)
    trk(6.0, 1.0, 7.0, 1.0, 0.1, "/OSD/VIDEO_IN", "In2.Cu"); case("Analog track on In2", "In2 and In3: no analog, RF or gate nets", (6.5, 1.0), r=0.6)
    trk(6.0, 2.0, 7.0, 2.0, 0.15, "/ESC1/A_COM", "In3.Cu"); case("Gate track on In3", "In2 and In3: no analog, RF or gate nets", (6.5, 2.0), r=0.6)
    trk(6.0, 3.0, 7.0, 3.0, 0.1, "/FC/SPI1.SCK", "In2.Cu"); case("gyro SPI1 track on In2", "In2 and In3: no gyro, VTX control or Kelvin nets", (6.5, 3.0), r=0.6)
    trk(8.0, 1.0, 9.0, 1.0, 0.1, "/RX/VTX_SPI.CLK", "In2.Cu"); case("VTX SPI track on In2", "In2 and In3: no gyro, VTX control or Kelvin nets", (8.5, 1.0), r=0.6)
    trk(8.0, 2.0, 9.0, 2.0, 0.1, "/FC/SPI0.MISO", "In2.Cu"); case("blackbox SPI0 track on In2 (allowed)", None, (8.5, 2.0), r=0.6)
    trk(6.0, 4.0, 7.0, 4.0, 0.1, "/SPI1_SCK", "In3.Cu"); case("schematic gyro net /SPI1_SCK on In3", "In2 and In3: no gyro, VTX control or Kelvin nets", (6.5, 4.0), r=0.6)
    trk(8.0, 4.0, 9.0, 4.0, 0.1, "/VTX_SPI_CLK", "In2.Cu"); case("schematic VTX net /VTX_SPI_CLK on In2", "In2 and In3: no gyro, VTX control or Kelvin nets", (8.5, 4.0), r=0.6)
    trk(6.0, 5.0, 7.0, 5.0, 0.1, "/VTX/U19_SPICLK", "In2.Cu"); case("RTC6705-side VTX net /VTX/U19_SPICLK on In2", "In2 and In3: no gyro, VTX control or Kelvin nets", (6.5, 5.0), r=0.6)
    trk(8.0, 5.0, 9.0, 5.0, 0.1, "/SPI0_MISO", "In2.Cu"); case("schematic blackbox net /SPI0_MISO on In2 (allowed)", None, (8.5, 5.0), r=0.6)
    # battery-to-shunt corridor
    (sx0, sy0), (sx1, sy1) = SHUNT_CORRIDOR
    smx = (sx0 + sx1) / 2
    trk(smx - 0.5, sy0 + 0.8, smx + 0.5, sy0 + 0.8, 0.1, "/T/SIG9", SHUNT_LAYER); case("signal track in SHUNT_CORRIDOR", "SHUNT_CORRIDOR: battery current only", (smx, sy0 + 0.8), r=0.6)
    trk(smx - 0.5, sy0 + 1.8, smx + 0.5, sy0 + 1.8, 0.1, "/SHUNT_SENSE_P", SHUNT_LAYER); case("Kelvin track in SHUNT_CORRIDOR", None, (smx, sy0 + 1.8), r=0.6)
    trk(smx - 0.5, sy0 + 2.8, smx + 0.5, sy0 + 2.8, 0.5, "+BATT_IN", "B.Cu"); case("+BATT_IN track in SHUNT_CORRIDOR", None, (smx, sy0 + 2.8), r=0.6)
    # SMD pad to track 0.13, pads 0.30 from the edge, edge band, flange, courtyard classes
    f1 = fp("C_0402_1005Metric", "C1", -6, 4)
    p1 = [p for p in f1.Pads() if p.GetNumber() == "1"][0]
    px, py = P.ToMM(p1.GetPosition().x) - cx, P.ToMM(p1.GetPosition().y) - cy
    edge_y = py - P.ToMM(p1.GetSize(P.F_Cu).y) / 2
    trk(px - 0.6, edge_y - 0.11 - 0.05, px + 0.6, edge_y - 0.11 - 0.05, 0.1, "/T/SIG5")
    case("track 0.11 from an SMD pad", "SMD pad to track and pour 0.13", (px, edge_y - 0.16), r=0.8)
    fp("C_0402_1005Metric", "C2", 0, -BODY_HALF + 0.8, edge_gap=0.25)
    case("0402 near the top edge (pad 0.25 from it)", "parts: pads 0.30 from the edge", (0, -BODY_HALF + 0.6), r=0.9)
    case("0402 courtyard in the edge band", "parts: courtyards off the edge band", (0, -BODY_HALF + 0.6), r=0.9)
    fp("small_pad", "J1", 4, BODY_HALF - 1.0, edge_gap=0.25)
    case("small_pad solder pad 0.25 from the edge", None, (4, BODY_HALF - 0.8), r=0.6)
    hx, hy = HOLES["RIGHT"][0] * HOLE_HALF, HOLES["RIGHT"][1] * HOLE_HALF
    d = 2.6 / math.sqrt(2)
    fp("C_0201_0603Metric", "C3", hx - d, hy - d)
    case("0201 on the right grommet flange", "keepout area 'MOUNT_RIGHT'", (hx - d, hy - d), r=0.7)
    def crt_w(f):                     # courtyard width from the polygon vertices (BBox() adds a margin)
        c = f.GetCourtyard(P.F_CrtYd).COutline(0)
        xs = [c.CPoint(i).x for i in range(c.PointCount())]
        return P.ToMM(max(xs) - min(xs))
    fA = fp("C_0402_1005Metric", "C4", 2, 4)
    w402 = crt_w(fA)
    fp("C_0402_1005Metric", "C5", 2 + w402 + 0.02, 4)
    case("two 0402, courtyards 0.02 apart", "0402 to 0402: +0.05", (2 + w402 / 2, 4), r=w402 / 2 + 0.3)
    fB = fp("C_0201_0603Metric", "C6", 2, 7)
    w201 = crt_w(fB)
    fp("C_0201_0603Metric", "C7", 2 + w201 + 0.02, 7)
    case("two 0201, courtyards 0.02 apart", None, (2 + w201 / 2, 7), r=w201 / 2 + 0.3)
    fT = fp("CONN-SMD_SM03B-SRSS-TB-LF-SN-P", "J2", -4, -3)
    tb = fT.GetCourtyard(P.F_CrtYd).BBox()
    fp("C_0201_0603Metric", "C8", P.ToMM(tb.GetRight()) - cx + w201 / 2 + 0.2, -3)
    case("0201 0.2 mm from an SH1.0 courtyard", "tall parts: 0.5 to 0201 and 0402",
         (P.ToMM(tb.GetRight()) - cx + 0.1, -3), r=1.0)
    text(-6, -BODY_HALF + 0.3, "X"); case("silk text over the edge", "Silkscreen clipped by board edge", (-6, -BODY_HALF + 0.3), r=0.8)
    sl = P.PCB_SHAPE(b)
    sl.SetShape(P.SHAPE_T_SEGMENT)
    sl.SetLayer(P.F_SilkS)
    sl.SetWidth(mm(0.15))
    sl.SetStart(V(-3.5, -BODY_HALF + 0.10 + 0.075))
    sl.SetEnd(V(-2.5, -BODY_HALF + 0.10 + 0.075))
    b.Add(sl)
    case("silk line 0.10 inside the edge", "silk 0.20 from the edge", (-3, -BODY_HALF + 0.2), r=0.8)
    text(9.0, 5.0, "GND", size=0.8, thick=0.13); case("pad label 0.8 / 0.13 (D12)", None, (9.0, 5.0), r=0.8)
    text(9.0, 7.5, "GND", size=0.7, thick=0.13); case("silk text 0.7 high", "text_height", (9.0, 7.5), r=0.8)
    tht("J3", -9, -3, [(0, 1.0, 0.6, True), (1.3, 1.0, 0.6, True)])
    case("PTH pads 1.0 / 0.6 at 1.3 pitch (copper 0.30)", "PTH pads, copper 0.40 apart", (-8.35, -3), r=0.9)
    tht("J4", -9, 0, [(0, 0.9, 0.6, True)])
    case("PTH pad 0.9 / 0.6 (annular 0.15)", "PTH annular ring 0.20", (-9, 0), r=0.5)
    tht("H1", -9, 3, [(0, 0.4, 0.4, False)])
    case("NPTH 0.40", "NPTH at least 0.50", (-9, 3), r=0.5)
    # netclass patterns
    sample = {"+BATT": "VBAT", "+BATT_IN": "VBAT", "/ESC1/PHASE_A": "Phase", "/ESC3/B_COM": "Gate",
              "/ESC2/C_PWM": "Gate", "+3V3_VTX": "Power", "+5V": "Power", "+5V_USB": "Power", "+5V_BST": "Power",
              "+5V_HD": "Power", "+1V8": "Power", "GND": "GND", "/OSD/VIDEO_IN": "Analog", "/CURR_SENSE": "Analog",
              "/SHUNT_SENSE_P": "Analog", "/POWER/SHUNT_SENSE_N": "Analog", "/VTX/RF_OUT": "RF",
              "/RX/ANT_FEED": "RF", "/USB_D_P": "USB", "/USB_D_N": "USB", "/MOTOR1": "Default",
              "/SPI0.SCK": "Default", "/ESC1/VDD": "Default"}
    for n in sample:
        net(n)
    P.SaveBoard(pcb, b)
    shutil.copy(PRO, os.path.join(tmp, os.path.basename(PRO)))
    b2 = P.LoadBoard(pcb)
    nsets = b2.GetDesignSettings().m_NetSettings
    got = {n: nsets.GetEffectiveNetClass(n).GetName() for n in sample}
    rpt = os.path.join(tmp, "drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", rpt, pcb],
                   capture_output=True, text=True)
    viol = json.load(open(rpt))["violations"]
    results = []
    for tag, expect, (x, y), r in cases:
        near = []
        for v in viol:
            if any(abs(it["pos"]["x"] - x) < r and abs(it["pos"]["y"] - y) < r for it in v["items"]):
                near.append(v["type"] + ": " + v["description"] + " | " + " / ".join(i["description"] for i in v["items"]))
        if expect == KEEPOUT_HIT:
            near = [n for n in near if n.startswith(KEEPOUT_HIT)] or near
        ok = (not [n for n in near if not n.startswith(("track_dangling", "via_dangling", "unconnected", "isolated",
                                                       "solder_mask_bridge", "lib_footprint", "missing_courtyard"))]) \
            if expect is None else any(expect in n for n in near)
        results.append((ok, tag, expect, near))
    for n, want in sample.items():
        results.append((got[n].split(",")[0] == want, "net %s -> class %s" % (n, want), None,
                        ["got " + got[n]] if got[n].split(",")[0] != want else []))
    return tmp, results


# ==============================================================================================================
# 6. Main
# ==============================================================================================================
def run(check=False, recompute_fd=False, do_selftest=False):
    rec = impedance(recompute_fd, write=not check)
    rf = rf_values(rec)
    print(impedance_report(rec))
    P = quiet_pcbnew()
    tmp = tempfile.mkdtemp(prefix="setup_board_")
    try:
        t_pcb, t_pro, t_dru = (os.path.join(tmp, os.path.basename(x)) for x in (PCB, PRO, DRU))
        for s, d in ((PCB, t_pcb), (PRO, t_pro), (DRU, t_dru)):
            shutil.copy(s, d)
        ignored_before = write_pro(t_pro, rf)
        open(t_dru, "w").write(dru_text(rf, open(DRU).read()))
        summary = build_board(t_pcb, P)
        total = splice_stackup(t_pcb)
        b = P.LoadBoard(t_pcb)
        b.GetDesignSettings().SetBoardThickness(P.FromMM(total))
        if not P.SaveBoard(t_pcb, b):
            raise SystemExit("pcbnew could not re-save the board after the stackup splice")
        b = P.LoadBoard(t_pcb)                                  # final normalising round trip
        if not P.SaveBoard(t_pcb, b):
            raise SystemExit("pcbnew could not re-save the board")
        rep = verify_board(t_pcb, P)
        verify_pro(t_pro, rf)
        print("re-enabled DRC checks (%d): %s" % (len(SEVERITIES), ", ".join("%s=%s" % kv for kv in sorted(SEVERITIES.items()))))
        if ignored_before:
            still = sorted(set(ignored_before) - set(SEVERITIES))
            print("checks ignored before this run: %d%s" % (len(ignored_before), (", still ignored: " + ", ".join(still)) if still else ""))
        print("board: %d copper layers, thickness %.3f mm (stackup sum incl. masks), mask expansion %.2f, min web %.2f"
              % (rep["copper_layers"], rep["thickness"], rep["mask_expansion"], rep["mask_min_web"]))
        print("outline: closed %s, bbox %s, size %s, area %.2f mm2 net of holes" % (rep["outline_closed"], rep["outline_bbox"], rep["outline_size"], rep["outline_area"]))
        print("holes (relative to the centre): %s" % rep["holes"])
        print("grid origin %s, aux origin %s" % (rep["grid_origin"], rep["aux_origin"]))
        for z in summary["zones"]:
            print("rule area %-15s %-38s keepout %-22s %6.2f mm2  %s" % (z[0], ",".join(z[1]), ",".join(z[2]) or "named only", z[3], z[4]))
        changed = []
        for s, d in ((t_pcb, PCB), (t_pro, PRO), (t_dru, DRU)):
            if open(s, "rb").read() != open(d, "rb").read():
                changed.append(os.path.relpath(d, os.path.dirname(HW)))
                if not check:
                    shutil.copy(s, d)
        if check:
            print("check: %s" % ("would change " + ", ".join(changed) if changed else "project files are up to date"))
            return 1 if changed else 0
        print("wrote: %s" % (", ".join(changed) if changed else "nothing (already up to date)"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if do_selftest:
        st, results = selftest(P, rf)
        bad = 0
        for ok, tag, expect, near in results:
            print(("PASS " if ok else "FAIL ") + tag + ("  [expect: %s]" % expect if expect else "  [expect: no violation]"))
            if not ok:
                bad += 1
                for n in near:
                    print("      found:", n[:200])
        print("selftest scratch %s | failures: %d" % (st, bad))
        return 1 if bad else 0
    return 0


def main():
    a = sys.argv[1:]
    if "-h" in a or "--help" in a:
        print(__doc__)
        return 0
    if a and a[0] == "impedance":
        rec = impedance("--fd" in a, write=True)
        if "--json-only" not in a:
            print(impedance_report(rec))
        return 0
    return run(check="--check" in a, recompute_fd="--fd" in a, do_selftest="--selftest" in a)


if __name__ == "__main__":
    sys.exit(main())
