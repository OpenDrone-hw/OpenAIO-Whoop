#!/usr/bin/env python3
"""End-to-end check of the headless KiCad 10 pipeline on a toy board.

    $KPY hardware/tools/pipeline_selftest.py [--out DIR] [--freerouting JAR] [--render]

Runs under KiCad's Python (KPY, see AGENTS.md). Never touches the repo: the
project files in hardware/ are copied to DIR (default: a temp dir) and the toy
is built there. It is also the worked example for the real board:

  1. schematic: sch_build.py writes a root sheet (SM06B connector, power
     flags) + POWER (LP5912 LDO, caps) + MCU (AT32F421 QFN-28, decoupling)
     from OpenDrone symbols, with stub wires, local/global/hierarchical labels,
     power symbols, no-connects and sheet pins; ERC must have 0 errors and the
     netlist must contain the intended nets.
  2. geometry: one asymmetric symbol in all 12 rotation x mirror placements,
     every pin labelled; each label must land on its pin.
  3. board: sync_pcb.py loads footprints, paths, fields and nets; a second
     run must change nothing.
  4. layout: parts on both sides, hand-routed tracks and vias, GND and +3V3
     planes, zone fill; DRC must give 0 errors, 0 unconnected, 0 parity.
  5. optional: --freerouting deletes the inner-layer signal tracks and lets
     Freerouting re-route them around the protected fan-out (DRC again);
     --render writes top/bottom PNGs.

Generic R / C / power symbols are written into a throw-away "selftest"
library because the OpenDrone catalogue has none. Prints a timing table; exit
0 when every check passes.
"""
import argparse
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sch_build as sb  # noqa: E402

FONT = '(effects (font (size 1.27 1.27)))'
HIDDEN = '(hide yes) (effects (font (size 1.27 1.27)))'


def _props(ref, value, desc, ref_at="2.032 0 90", val_at="-2.032 0 90", ref_hidden=False):
    return ('(property "Reference" "%s" (at %s) %s) (property "Value" "%s" (at %s) %s) '
            '(property "Footprint" "" (at 0 0 0) %s) (property "Datasheet" "" (at 0 0 0) %s) '
            '(property "Description" "%s" (at 0 0 0) %s)'
            % (ref, ref_at, HIDDEN if ref_hidden else FONT, value, val_at, FONT, HIDDEN, HIDDEN, desc, HIDDEN))


def _pin(etype, x, y, a, length, name, number):
    return ('(pin %s line (at %s %s %s) (length %s) (name "%s" %s) (number "%s" %s))'
            % (etype, x, y, a, length, name, FONT, number, FONT))


def _poly(pts, width=0):
    return ('(polyline (pts %s) (stroke (width %s) (type default)) (fill (type none)))'
            % (" ".join("(xy %s %s)" % p for p in pts), width))


def generic_symbols():
    """Minimal R, C, GND, +3V3 and PWR_FLAG symbols in KiCad 10 syntax."""
    passive = '(pin_numbers (hide yes)) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)'
    power = ('(power global) (pin_numbers (hide yes)) (pin_names (offset 0) (hide yes)) '
             '(exclude_from_sim no) (in_bom yes) (on_board yes)')
    syms = [
        '(symbol "R" %s %s (symbol "R_0_1" (rectangle (start -1.016 -2.54) (end 1.016 2.54) '
        '(stroke (width 0.254) (type default)) (fill (type none)))) (symbol "R_1_1" %s %s))'
        % (passive, _props("R", "R", "Resistor"), _pin("passive", 0, 3.81, 270, 1.27, "~", 1),
           _pin("passive", 0, -3.81, 90, 1.27, "~", 2)),
        '(symbol "C" %s %s (symbol "C_0_1" %s %s) (symbol "C_1_1" %s %s))'
        % (passive, _props("C", "C", "Capacitor"), _poly([(-2.032, -0.762), (2.032, -0.762)], 0.508),
           _poly([(-2.032, 0.762), (2.032, 0.762)], 0.508), _pin("passive", 0, 3.81, 270, 3.048, "~", 1),
           _pin("passive", 0, -3.81, 90, 3.048, "~", 2)),
        '(symbol "GND" %s %s (symbol "GND_0_1" %s) (symbol "GND_1_1" %s))'
        % (power, _props("#PWR", "GND", "Ground", "0 -6.35 0", "0 -3.81 0", True),
           _poly([(0, 0), (0, -1.27), (1.27, -1.27), (0, -2.54), (-1.27, -1.27), (0, -1.27)]),
           _pin("power_in", 0, 0, 270, 0, "", 1)),
        '(symbol "+3V3" %s %s (symbol "+3V3_0_1" %s %s) (symbol "+3V3_1_1" %s))'
        % (power, _props("#PWR", "+3V3", "3.3 V rail", "0 -3.81 0", "0 3.556 0", True),
           _poly([(-0.762, 1.27), (0, 2.54)]), _poly([(0, 0), (0, 2.54), (0.762, 1.27)]),
           _pin("power_in", 0, 0, 90, 0, "", 1)),
        '(symbol "PWR_FLAG" %s %s (symbol "PWR_FLAG_0_1" %s) (symbol "PWR_FLAG_1_1" %s))'
        % (power.replace("(power global) ", "(power global) "),
           _props("#FLG", "PWR_FLAG", "Marks a net as driven", "0 1.905 0", "0 3.81 0", True),
           _poly([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)]),
           _pin("power_out", 0, 0, 90, 0, "", 1)),
    ]
    return ('(kicad_symbol_lib (version %s) (generator "pipeline_selftest") (generator_version "10.0") %s)\n'
            % (sb.SYM_VERSION, " ".join(syms)))


class Steps:
    def __init__(self):
        self.rows, self.ok = [], True

    def run(self, name, fn):
        t = time.time()
        try:
            ok, info = fn()
        except Exception as e:                      # report and keep going
            ok, info = False, "%s: %s" % (type(e).__name__, e)
        self.rows.append((name, ok, time.time() - t, info))
        self.ok &= ok
        print("%-4s %-34s %6.2fs  %s" % ("ok" if ok else "FAIL", name, time.time() - t, info), flush=True)
        return ok


def setup_project(hw, out):
    pro = [f for f in os.listdir(hw) if f.endswith(".kicad_pro")]
    if len(pro) != 1:
        raise SystemExit("need exactly one .kicad_pro in %s" % hw)
    name = pro[0][:-len(".kicad_pro")]
    os.makedirs(out, exist_ok=True)
    for ext in (".kicad_pro", ".kicad_dru", ".kicad_pcb", ".kicad_sch"):
        if os.path.exists(os.path.join(hw, name + ext)):
            shutil.copy(os.path.join(hw, name + ext), out)
    for f in ("fp-lib-table", "sym-lib-table", "lib.kicad_sym"):
        shutil.copy(os.path.join(hw, f), out)
    if os.path.isdir(os.path.join(hw, "lib.pretty")):
        shutil.copytree(os.path.join(hw, "lib.pretty"), os.path.join(out, "lib.pretty"), dirs_exist_ok=True)
    link = os.path.join(out, "KiCad-Library")
    if not os.path.exists(link):
        os.symlink(os.path.join(hw, "KiCad-Library"), link)
    with open(os.path.join(out, "selftest.kicad_sym"), "w") as f:
        f.write(generic_symbols())
    subprocess.run([sb.KICAD_CLI, "sym", "upgrade", "--force", os.path.join(out, "selftest.kicad_sym")],
                   capture_output=True, check=True)
    t = open(os.path.join(out, "sym-lib-table")).read().rstrip()
    t = t[:t.rindex(")")] + ('  (lib (name "selftest")(type "KiCad")(uri "${KIPRJMOD}/selftest.kicad_sym")'
                             '(options "")(descr "pipeline_selftest generic symbols"))\n)\n')
    open(os.path.join(out, "sym-lib-table"), "w").write(t)
    return os.path.join(out, name)


C100N = {"Footprint": "OpenDrone:C_0201_0603Metric", "MPN": "GRM033R61E104KE14D",
         "Manufacturer": "Murata Electronics", "LCSC": "C76939"}
C4U7 = {"Footprint": "OpenDrone:C_0402_1005Metric", "MPN": "CL05A475MP5NRNC",
        "Manufacturer": "Samsung Electro-Mechanics", "LCSC": "C23733"}
R10K = {"Footprint": "OpenDrone:R_0201_0603Metric", "MPN": "RC0201FR-0710KL",
        "Manufacturer": "YAGEO", "LCSC": "C106225"}


def build_schematic(base):
    prj = sb.Project(base + ".kicad_sch")
    d = os.path.dirname(base)
    prj.lib("OpenDrone", os.path.join(d, "KiCad-Library/symbol/OpenDrone.kicad_sym"))
    prj.lib("selftest", os.path.join(d, "selftest.kicad_sym"))
    GND, P3V3, FLAG = "selftest:GND", "selftest:+3V3", "selftest:PWR_FLAG"

    pwr = prj.sheet("power.kicad_sch", title="POWER", paper="A5")
    u1 = pwr.symbol("OpenDrone:LP5912-3.3DRVR", "U1", at=(101.6, 63.5))
    pwr.connect_many(u1, {"IN": ("VBAT", "hier"), "EN": "VBAT", "GND": (GND, "power"), "EP": (GND, "power"),
                          "OUT": (P3V3, "power"), "PG": ("PG_3V3", "global"), "NC": None})
    x, y, _ = u1.pin_xy("IN")
    pwr.label("VBAT", x + 2.54, y, 0)              # joins the hierarchical VBAT to the local one
    c1 = pwr.symbol("selftest:C", "C1", at=(124.46, 66.04), value="4.7uF", fields=C4U7)
    pwr.connect(c1, "1", "VBAT")
    pwr.connect(c1, "2", GND, kind="power")
    c2 = pwr.symbol("selftest:C", "C2", at=(76.2, 66.04), value="4.7uF", fields=C4U7)
    pwr.connect(c2, "1", P3V3, kind="power")
    pwr.connect(c2, "2", GND, kind="power")
    pwr.power(FLAG, 63.5, 50.8, angle=90)           # LP5912 pins are "unspecified": flag +3V3
    pwr.power(P3V3, 63.5, 50.8, angle=90)

    mcu = prj.sheet("mcu.kicad_sch", title="MCU")
    u2 = mcu.symbol("OpenDrone:AT32F421G8U7", "U2", at=(139.7, 88.9))
    mcu.connect_group(u2, ["VDDA", "VDD"], P3V3)
    mcu.connect_group(u2, ["16", "29"], GND)
    used = {"PA13": ("SWDIO", "hier"), "PA14": ("SWCLK", "hier"), "PA9": ("UART_TX", "hier"),
            "PA10": ("UART_RX", "hier"), "PA0": ("PG_3V3", "global"), "BOOT0": ("BOOT0", "label"),
            "NRST": ("NRST", "label")}
    for p in u2.pins():
        if p.name in ("VDD", "VDDA") or p.number in ("16", "29"):
            continue
        net = used.get(p.name)
        mcu.connect(u2, p.number, net[0] if net else None, kind=net[1] if net else "label")
    for i, ref in enumerate(("C3", "C4", "C5")):
        c = mcu.symbol("selftest:C", ref, at=(88.9 + 10.16 * i, 63.5), value="100nF", fields=C100N)
        mcu.connect(c, "1", "NRST" if ref == "C5" else P3V3, kind="label" if ref == "C5" else "power")
        mcu.connect(c, "2", GND, kind="power")
    r1 = mcu.symbol("selftest:R", "R1", at=(88.9, 109.22), value="10k", fields=R10K)
    mcu.connect(r1, "1", "BOOT0")
    mcu.connect(r1, "2", GND, kind="power")

    root = prj.root
    j1 = root.symbol("OpenDrone:SM06B-SRSS-TB(LF)(SN)", "J1", at=(50.8, 76.2),
                     fields={"Footprint": "OpenDrone:CONN-SMD_SM06B-SRSS-TB-LF-SN"})
    root.connect_many(j1, {"1": "VBAT", "2": (GND, "power"), "3": "SWDIO", "4": "SWCLK", "5": "UART_TX",
                           "6": "UART_RX", "7": (GND, "power"), "8": (GND, "power")})
    root.power(FLAG, 50.8, 50.8, angle=90)
    root.label("VBAT", 50.8, 50.8, 0)
    root.power(FLAG, 63.5, 50.8, angle=90)
    root.power(GND, 63.5, 50.8, angle=270)
    s_pwr = root.add_sheet(pwr, "POWER", at=(101.6, 50.8), size=(25.4, 12.7), pins=[("VBAT", "input")])
    s_mcu = root.add_sheet(mcu, "MCU", at=(101.6, 76.2), size=(25.4, 17.78),
                           pins=[("SWDIO", "bidirectional"), ("SWCLK", "input"), ("UART_TX", "output"),
                                 ("UART_RX", "input")])
    root.connect_sheet_pin(s_pwr, "VBAT", "VBAT")
    for p in ("SWDIO", "SWCLK", "UART_TX", "UART_RX"):
        root.connect_sheet_pin(s_mcu, p, p)
    prj.save()
    return prj


EXPECTED_NETS = {
    "+3V3": {("C2", "1"), ("C3", "1"), ("C4", "1"), ("U1", "1"), ("U2", "17"), ("U2", "5")},
    "/VBAT": {("C1", "1"), ("J1", "1"), ("U1", "4"), ("U1", "6")},
    "/SWDIO": {("J1", "3"), ("U2", "21")}, "/SWCLK": {("J1", "4"), ("U2", "22")},
    "/UART_TX": {("J1", "5"), ("U2", "19")}, "/UART_RX": {("J1", "6"), ("U2", "20")},
    "PG_3V3": {("U1", "3"), ("U2", "6")}, "/MCU/BOOT0": {("R1", "1"), ("U2", "1")},
    "/MCU/NRST": {("C5", "1"), ("U2", "4")},
    "GND": {("C1", "2"), ("C2", "2"), ("C3", "2"), ("C4", "2"), ("C5", "2"), ("J1", "2"), ("J1", "7"),
            ("J1", "8"), ("R1", "2"), ("U1", "5"), ("U1", "7"), ("U2", "16"), ("U2", "29")},
}


def check_netlist(base):
    comps, nets = sb.read_netlist(sb.export_netlist(base + ".kicad_sch"))
    got = {n: {(r, p) for r, p, _, _ in nodes} for n, nodes in nets.items()}
    bad = [n for n, pads in EXPECTED_NETS.items() if got.get(n) != pads]
    return not bad, "%d parts, %d nets%s" % (len(comps), len(nets), (", wrong: %s" % bad) if bad else "")


def check_geometry(out):
    d = os.path.join(out, "geometry")
    os.makedirs(d, exist_ok=True)
    prj = sb.Project(os.path.join(d, "geometry.kicad_sch"))
    prj.lib("OpenDrone", os.path.join(out, "KiCad-Library/symbol/OpenDrone.kicad_sym"))
    want = {}
    for i, (rot, mir) in enumerate(itertools.product((0, 90, 180, 270), (None, "x", "y"))):
        ref = "U%d" % (i + 1)
        s = prj.root.symbol("OpenDrone:LP5912-3.3DRVR", ref, at=(50.8 + (i % 4) * 50.8, 50.8 + (i // 4) * 50.8),
                            rot=rot, mirror=mir)
        for p in s.pins():
            prj.root.connect(s, p.number, "%s_%s" % (ref, p.name))
            want[(ref, p.number)] = "/%s_%s" % (ref, p.name)
    prj.save(upgrade=False)
    _, nets = sb.read_netlist(sb.export_netlist(prj.root_path))
    got = {(r, p): n for n, nodes in nets.items() for r, p, _, _ in nodes}
    bad = [k for k in want if got.get(k) != want[k]]
    return not bad, "%d pins in 12 orientations%s" % (len(want), (", wrong: %s" % bad[:5]) if bad else "")


def layout(board):
    import pcb_build as pb
    brd = pb.Board(board)
    brd.clear_tracks()
    brd.clear_zones()
    brd.outline_rect(100, 100, 120, 116, r=1.0)
    for ref, x, y, rot, side in (("U2", 110, 104, 0, "F"), ("J1", 110, 112.8, 0, "F"), ("C5", 106.3, 104, 180, "F"),
                                 ("R1", 106.3, 102.8, 180, "F"), ("U1", 104.5, 108.5, 0, "B"),
                                 ("C1", 106.0, 110.4, 0, "B"), ("C2", 103.0, 110.6, 0, "B"),
                                 ("C3", 108.3, 104.4, 0, "B"), ("C4", 113.7, 104.4, 0, "B")):
        brd.place(ref, x, y, rot, side)
    P, SIG, PWR = brd.pad_xy, 0.1, 0.25
    T, VIA = brd.track, brd.via
    T("/MCU/NRST", "F.Cu", P("U2", "4"), P("C5", "1"), width=SIG)
    T("/MCU/BOOT0", "F.Cu", P("U2", "1"), P("R1", "1"), width=SIG)
    for ref, y in (("C5", 104.0), ("R1", 102.8)):
        T("GND", "F.Cu", P(ref, "2"), (105.4, y), width=0.2)
        VIA("GND", 105.4, y)
    T("+3V3", "F.Cu", P("U2", "5"), (107.3, 104.4), width=0.15)
    VIA("+3V3", 107.3, 104.4)
    T("+3V3", "F.Cu", P("U2", "17"), (112.8, 104.4), width=0.15)
    VIA("+3V3", 112.8, 104.4)
    T("PG_3V3", "F.Cu", P("U2", "6"), (107.4, 104.8), (107.4, 105.5), width=SIG)
    VIA("PG_3V3", 107.4, 105.5)
    VIA("GND", 110, 104)                                        # via in the exposed pad
    T("GND", "F.Cu", P("U2", "16"), (111.0, 104.8), (110.8, 104.6), (110.4, 104.6), width=0.15)
    for net, pin, vx, vy in (("/SWDIO", "21", 112.9, 102.8), ("/UART_RX", "20", 113.6, 103.2),
                             ("/UART_TX", "19", 112.9, 103.6), ("/SWCLK", "22", 111.2, 101.4)):
        T(net, "F.Cu", P("U2", pin), (vx, vy), width=SIG)
        VIA(net, vx, vy)
    for net, pin, x in (("/SWDIO", "3", 109.5), ("/SWCLK", "4", 110.5), ("/UART_TX", "5", 111.5),
                        ("/UART_RX", "6", 112.5), ("GND", "2", 108.5)):
        VIA(net, x, 109.3)
        T(net, "F.Cu", (x, 109.3), P("J1", pin), width=SIG if net != "GND" else 0.25)
    VIA("/VBAT", 107.5, 109.15)
    T("/VBAT", "F.Cu", (107.5, 109.15), P("J1", "1"), width=PWR)
    for pin, x in (("7", 113.8), ("8", 106.2)):
        VIA("GND", x, 113.3)
        T("GND", "F.Cu", (x, 113.3), P("J1", pin), width=0.3)
    T("/SWCLK", "In2.Cu", (111.2, 101.4), (110.5, 102.1), (110.5, 109.3), width=SIG)
    T("/UART_TX", "In2.Cu", (112.9, 103.6), (111.5, 105.0), (111.5, 109.3), width=SIG)
    T("/UART_RX", "In2.Cu", (113.6, 103.2), (113.6, 106.0), (112.5, 107.1), (112.5, 109.3), width=SIG)
    T("/SWDIO", "In3.Cu", (112.9, 102.8), (109.0, 106.7), (109.0, 108.8), (109.5, 109.3), width=SIG)
    T("/VBAT", "B.Cu", (107.5, 109.15), (106.0, 109.15), width=PWR)
    T("/VBAT", "B.Cu", P("U1", "4"), (106.0, 107.85), (106.0, 109.15), P("U1", "6"), width=0.15)
    T("/VBAT", "B.Cu", P("C1", "1"), (105.52, 109.63), (106.0, 109.15), width=0.15)
    T("GND", "B.Cu", P("C1", "2"), (106.48, 111.1), width=0.2)
    VIA("GND", 106.48, 111.1)
    T("GND", "B.Cu", P("U1", "5"), P("U1", "7"), width=0.2)
    VIA("GND", 104.5, 108.5)
    T("+3V3", "B.Cu", P("U1", "1"), (102.52, 109.15), width=PWR)
    VIA("+3V3", 102.52, 109.15)
    T("+3V3", "B.Cu", P("C2", "1"), (102.52, 109.15), width=PWR)
    T("GND", "B.Cu", P("C2", "2"), (104.3, 110.6), width=0.2)
    VIA("GND", 104.3, 110.6)
    T("PG_3V3", "B.Cu", (107.4, 105.5), (105.25, 105.5), (103.6125, 107.1375), P("U1", "3"), width=SIG)
    T("+3V3", "B.Cu", (107.3, 104.4), P("C3", "1"), width=0.15)
    T("GND", "B.Cu", P("C3", "2"), (109.02, 104.0), (110.0, 104.0), width=0.15)
    T("+3V3", "B.Cu", (112.8, 104.4), P("C4", "1"), width=0.15)
    T("GND", "B.Cu", P("C4", "2"), (114.02, 105.1), width=0.15)
    VIA("GND", 114.02, 105.1)
    outline = brd.outline_points()
    brd.zone("GND", "In1.Cu", outline, name="GND plane", min_width=0.1, thermal_gap=0.15, spoke=0.15)
    brd.zone("+3V3", "In4.Cu", outline, name="3V3 plane", min_width=0.1, thermal_gap=0.15, spoke=0.15)
    brd.fill_zones()
    brd.save()
    return True, "%d tracks/vias, unrouted %d" % (len(list(brd.b.GetTracks())), brd.unrouted())


def drc_clean(board):
    import pcb_build as pb
    d = pb.drc(board)
    ok = d["errors"] == 0 and d["unconnected"] == 0 and d["parity"] == 0
    return ok, "%d errors, %d warnings, %d unconnected, %d parity%s" % (
        d["errors"], d["warnings"], d["unconnected"], d["parity"],
        "" if ok else " " + str(d["by_type"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--hardware", default=os.path.dirname(HERE), help="the repo's hardware/ directory")
    ap.add_argument("--out", help="work directory (default: a new temp dir)")
    ap.add_argument("--freerouting", metavar="JAR", help="also rip up and autoroute with this jar")
    ap.add_argument("--render", action="store_true", help="also render top/bottom PNGs (~25 s each)")
    a = ap.parse_args()
    out = os.path.abspath(a.out or tempfile.mkdtemp(prefix="kicad_selftest_"))
    print("work dir:", out)
    st = Steps()
    base = setup_project(os.path.abspath(a.hardware), out)
    board = base + ".kicad_pcb"
    tool = [sys.executable, os.path.join(HERE, "sync_pcb.py"), board, "--quiet"]

    st.run("schematic build + KiCad re-save", lambda: (build_schematic(base), (True, "3 sheets"))[1])

    def erc():
        e, w, v = sb.erc(base + ".kicad_sch")
        kinds = sorted({x["type"] for x in v})
        return e == 0, "%d errors, %d warnings %s" % (e, w, kinds)
    st.run("ERC", erc)
    st.run("netlist has the intended nets", lambda: check_netlist(base))
    st.run("pin geometry, all orientations", lambda: check_geometry(out))

    def sync(expect_zero=False):
        r = subprocess.run(tool, capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or ["?"])[-1]
        n = int(last.split(" changes")[0].split()[-1]) if " changes" in last else -1
        return r.returncode == 0 and (n == 0 if expect_zero else n > 0), last
    st.run("sync_pcb (first run)", sync)
    st.run("sync_pcb (second run: no changes)", lambda: sync(True))
    st.run("placement + routing + zones", lambda: layout(board))
    st.run("DRC + schematic parity", lambda: drc_clean(board))
    if a.freerouting:
        def fr():
            r = subprocess.run([sys.executable, os.path.join(HERE, "freeroute.py"), board, "--jar", a.freerouting,
                                "--strip-layers", "In2.Cu,In3.Cu", "--no-drc"], capture_output=True, text=True)
            return r.returncode == 0, (r.stdout.strip().splitlines() or ["?"])[-1]
        shutil.copy(board, base + "-handrouted.kicad_pcb")
        st.run("freerouting (inner layers)", fr)
        st.run("DRC after freerouting", lambda: drc_clean(board))
    if a.render:
        import pcb_build as pb
        for side in ("top", "bottom"):
            st.run("render %s" % side, lambda s=side: (True, pb.render(board, os.path.join(out, "render-%s.png" % s),
                                                                      side=s, width=1200, height=1000)))
    total = sum(r[2] for r in st.rows)
    print("%s in %.1fs, work dir %s" % ("PASS" if st.ok else "FAIL", total, out))
    return 0 if st.ok else 1


if __name__ == "__main__":
    sys.exit(main())
