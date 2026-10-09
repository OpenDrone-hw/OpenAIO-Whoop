#!/usr/bin/env python3
"""Root sheet and sheet scaffolding of OpenAIO-Whoop from hardware/sch_contract.json.

    /usr/bin/python3.12 hardware/tools/sch_root.py [--stubs]

Writes hardware/OpenAIO-Whoop.kicad_sch (sheet symbols, root wires and labels, netclass flags, power table, notes,
title block + wordmark) and, with --stubs, an empty file per sub-sheet (title block + wordmark only) so the hierarchy
loads; existing sub-sheets are left alone unless --stubs is given. Every file is re-saved by kicad-cli (sch_build).
The fixed uuids (root file, sheet files, sheet symbols, instance paths, pages) are written back into the contract.

Sheet scripts reuse this module:

    import sch_build as sb, sch_root as sr
    prj = sb.Project("hardware/OpenAIO-Whoop.kicad_sch")
    c = sr.load_contract()
    sheets = sr.build_root(prj, c)               # root + every sheet object, decorated (title block, wordmark)
    pwr = sheets["power.kicad_sch"]              # fill it: pwr.symbol(...), pwr.connect(...), sr.note(pwr, ...)
    sr.save_sheets(prj, ["power.kicad_sch"])     # write ONLY this shard's files (never prj.save() from a shard)

Root layout (A3, mm, all on the 2.54 grid): signal flow left to right, POWER | IMU, BLACKBOX, LED | RP2350A |
RX, OSD, ESC1-ESC4 | VTX | PADS. Pins that face each other share a row, so every root wire is straight except HD_EN
(top channel), VIDEO_IN (OSD bottom pin) and VBUS (bottom channel). Phase wires carry no root label: their net name
comes from the ESC sheet (/ESCn/PHASE_x); every other root wire carries a root label = the net name.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sch_build as sb  # noqa: E402
from sch_build import S, Atom  # noqa: E402

CONTRACT = os.path.join(HW, "sch_contract.json")
PAPER = {"A5": (210, 148), "A4": (297, 210), "A3": (420, 297), "A2": (594, 420), "A1": (841, 594)}
G = 2.54


def load_contract(path=CONTRACT):
    return json.load(open(path, encoding="utf-8"))


# ------------------------------------------------------------------------------------------------- decoration
def wordmark(prj, file, paper):
    """The shipped OpenDrone wordmark (9 filled polylines) in the title block's company cell of `paper`."""
    art = json.load(open(os.path.join(HERE, "opendrone_wordmark.json")))
    w, h = PAPER[paper]
    dx, dy = w - 297, h - 210
    out = []
    for i, pl in enumerate(art["polylines"]):
        pts = S("pts", *[S("xy", round(x + dx, 4), round(y + dy, 4)) for x, y in pl["pts"]])
        out.append(S("polyline", pts, S("stroke", S("width", -0.0001), S("type", Atom("solid"))),
                     S("fill", S("type", Atom("color")), S("color", *pl["fill"], 1)),
                     S("uuid", prj.uid(file, "wordmark", str(i)))))
    return out


def title_block(title, date, rev):
    return S("title_block", S("title", title), S("date", date), S("rev", rev))


def decorate(prj, sheet, title, paper, date, rev):
    """Paper, title block (company empty: the wordmark fills that cell) and the wordmark."""
    sheet.paper = paper
    sheet.title = title
    sheet.extra = [title_block(title, date, rev)]
    sheet.items[:0] = wordmark(prj, sheet.file, paper)


def bold_text(sheet, s, x, y, size=2.032, key=None):
    sheet.items.append(S("text", s, S("exclude_from_sim", False), S("at", x, y, 0),
                         S("effects", S("font", S("size", size, size), S("bold", True)),
                           S("justify", Atom("left"), Atom("top"))),
                         S("uuid", sheet.prj.uid(sheet.file, "btext", key or s))))


def note(sheet, s, x, y, w, h, key=None):
    """Borderless text box (house style for block notes)."""
    sheet.items.append(S("text_box", s, S("exclude_from_sim", False), S("at", x, y, 0), S("size", w, h),
                         S("margins", 0.9525, 0.9525, 0.9525, 0.9525),
                         S("stroke", S("width", -0.0001), S("type", Atom("solid"))), S("fill", S("type", Atom("none"))),
                         S("effects", S("font", S("size", 1.27, 1.27)), S("justify", Atom("left"), Atom("top"))),
                         S("uuid", sheet.prj.uid(sheet.file, "note", key or s[:40]))))


def netclass_flag(sheet, cls, x, y, key):
    """Netclass directive label on a wire point, flag pointing up."""
    sheet.items.append(S("netclass_flag", "", S("length", 2.54), S("shape", Atom("round")), S("at", x, y, 0),
                         S("fields_autoplaced", True),
                         S("effects", S("font", S("size", 1.27, 1.27)), S("justify", Atom("left"), Atom("bottom"))),
                         S("uuid", sheet.prj.uid(sheet.file, "netclass", key)),
                         S("property", "Netclass", cls, S("at", x, round(y - 3.81, 4), 0),
                           S("effects", S("font", S("size", 1.27, 1.27), S("italic", True)), S("justify", Atom("left"))))))


def table(sheet, x, y, col_w, row_h, rows, key):
    """KiCad table; rows[0] is the header (bold)."""
    cells = []
    yy = y
    for r, row in enumerate(rows):
        xx = x
        for c, txt in enumerate(row):
            font = S("font", S("size", 1.27, 1.27), S("bold", True)) if r == 0 else S("font", S("size", 1.27, 1.27))
            cells.append(S("table_cell", txt, S("exclude_from_sim", False), S("at", round(xx, 4), round(yy, 4), 0),
                           S("size", col_w[c], row_h), S("margins", 0.9525, 0.9525, 0.9525, 0.9525), S("span", 1, 1),
                           S("fill", S("type", Atom("none"))),
                           S("effects", font, S("justify", Atom("left"), Atom("top"))),
                           S("uuid", sheet.prj.uid(sheet.file, "cell", "%s|%d|%d" % (key, r, c)))))
            xx += col_w[c]
        yy += row_h
    stroke = S("stroke", S("width", 0.1524), S("type", Atom("solid")))
    sheet.items.append(S("table", S("column_count", len(col_w)),
                         S("border", S("external", True), S("header", True), stroke),
                         S("separators", S("rows", True), S("cols", True), stroke),
                         S("column_widths", *col_w), S("row_heights", *([row_h] * len(rows))),
                         S("uuid", sheet.prj.uid(sheet.file, "table", key)),   # else KiCad picks a random one
                         [Atom("cells")] + cells))


# ------------------------------------------------------------------------------------------------- root layout
# sheet instance -> (x, y, w, h); pins sit on rows shared with their partner
BOX = {
    "POWER": (17.78, 30.48, 45.72, 76.2),
    "IMU": (78.74, 30.48, 35.56, 20.32),
    "BLACKBOX": (78.74, 60.96, 35.56, 15.24),
    "LED": (78.74, 86.36, 35.56, 10.16),
    "RP2350A": (142.24, 30.48, 55.88, 165.1),
    "RX": (223.52, 30.48, 50.8, 27.94),
    "OSD": (223.52, 66.04, 50.8, 17.78),
    "ESC1": (223.52, 91.44, 50.8, 12.7),
    "ESC2": (223.52, 111.76, 50.8, 12.7),
    "ESC3": (223.52, 132.08, 50.8, 12.7),
    "ESC4": (223.52, 152.4, 50.8, 12.7),
    "VTX": (297.18, 30.48, 40.64, 50.8),
    "PADS": (360.68, 30.48, 40.64, 172.72),
}
ROW = {}
for i, n in enumerate(("UART0_TX", "UART0_RX", "FC_BOOT")):
    ROW[n] = 35.56 + i * G
for i, n in enumerate(("VTX_SPI_CS", "VTX_SPI_CLK", "VTX_SPI_DATA", "PA_BIAS_PWM", "PA_EN", "VTX_PWR_CTL", "PA_DET",
                       "PA_NTC")):
    ROW[n] = 35.56 + i * G
for i, n in enumerate(("OSD_W", "OSD_EN", "OSD_SYNC")):
    ROW[n] = 71.12 + i * G
ROW["VIDEO_OUT"] = 71.12
ROW["VIDEO_IN"] = 88.9                    # channel row (PADS left pin); the OSD pin is on its bottom edge
for k in range(4):
    y0 = 96.52 + k * 20.32
    ROW["MOTOR%d" % (k + 1)] = y0
    for j, ph in enumerate("ABC"):
        ROW["/ESC%d/PHASE_%s" % (k + 1, ph)] = y0 + j * G
for i, n in enumerate(("PIOUART0_TX", "PIOUART0_RX", "UART1_TX", "UART1_RX", "LED_STRIP", "BUZZER-", "USB_D_P",
                       "USB_D_N")):
    ROW[n] = 175.26 + i * G
ROW["VBUS"] = 198.12                      # channel row (PADS left pin); POWER pin is on its bottom edge
for i, n in enumerate(("SPI1_SCK", "SPI1_MOSI", "SPI1_MISO", "GYRO_CS", "GYRO_INT", "GYRO_CLKIN")):
    ROW[n] = 35.56 + i * G
for i, n in enumerate(("SPI0_SCK", "SPI0_MOSI", "SPI0_MISO", "FLASH_CS")):
    ROW[n] = 66.04 + i * G
ROW["LED0"], ROW["LED1"] = 91.44, 93.98
ROW["CURR_SENSE"] = 101.6
HD_Y = 22.86                              # HD_EN top channel
TOP_X = {"POWER": 55.88, "RP2350A": 170.18, "VTX": 327.66}     # HD_EN pins on the top edges
BOT_X = {"POWER": 45.72, "OSD": 269.24}                          # VBUS / VIDEO_IN pins on the bottom edges
# content text position inside each sheet symbol (dx, dy from the box corner)
CONTENT_AT = {"POWER": (2.54, 3.81), "IMU": (2.54, 3.81), "BLACKBOX": (2.54, 3.81), "LED": (2.54, 2.54),
              "RP2350A": (16.51, 10.16), "RX": (2.54, 12.7), "OSD": (12.7, 2.54), "VTX": (17.78, 27.94),
              "PADS": (17.78, 3.81)}
for k in range(1, 5):
    CONTENT_AT["ESC%d" % k] = (10.16, 2.54)


def _pin_xy(inst, name, side, net):
    x, y, w, h = BOX[inst]
    if side == "right":
        return (x + w, ROW[net], 0)
    if side == "left":
        return (x, ROW[net], 180)
    if side == "top":
        return (TOP_X[inst], y, 90)
    return (BOT_X[inst], y + h, 270)


def build_root(prj, c, stub_sheets=True):
    """Lay out the root from contract `c`; returns {file: Sheet}. Sub-sheets are decorated (title block + wordmark)."""
    meta = c["meta"]
    date, rev = meta["date"], meta["rev"]
    root = prj.root
    rinfo = c["root"]
    decorate(prj, root, rinfo["title"], rinfo["paper"], date, rev)
    sheets, uses = {}, {}
    page = 2
    for sh in c["sheets"]:
        child = prj.sheet(sh["file"], title=sh["title"], paper=sh["paper"])
        decorate(prj, child, sh["title"], sh["paper"], date, rev)
        sheets[sh["file"]] = child
        for inst in sh["instances"]:
            name = inst["name"]
            x, y, w, h = BOX[name]
            u = root.add_sheet(child, name, (x, y), (w, h), pins=(), ref_offset=inst.get("ref_offset") or 0)
            pins = []
            for p in sh["pins"]:
                netname = p["net"].replace("<n>", name[-1]) if "<n>" in p["net"] else p["net"]
                key = netname[1:] if netname.count("/") == 1 else netname
                px, py, a = _pin_xy(name, p["name"], p["side"], key)
                pins.append((p["name"], p["dir"], sb._r4(px), sb._r4(py), a))
            u.pins = pins
            uses[name] = u
            dx, dy = CONTENT_AT[name]
            bold_text(root, "\n".join(sh["content"]), x + dx, y + dy, key="content|" + name)
    # ---- wires and labels, net by net
    for n in c["nets"]:
        ends = [uses[p["sheet"]].pin_xy(p["pin"]) for p in n["pins"]]
        label = n["root_label"]
        name = n["net"][1:]
        if name == "HD_EN":
            xs = sorted(e[0] for e in ends)
            root.wire((xs[0], HD_Y), (xs[1], HD_Y), (xs[2], HD_Y))
            for ex, ey, _ in ends:
                root.wire((ex, HD_Y), (ex, ey))
            root.junction(xs[1], HD_Y)
            root.label(label, xs[1] + 2.54, HD_Y, 0)
            continue
        if name in ("VBUS", "VIDEO_IN"):
            (px, py, _), (bx, by, _) = sorted(ends, key=lambda e: -e[0])    # PADS pin first, bottom pin second
            mid = (px - 2.54, py)
            root.wire((px, py), mid, (bx, py), (bx, by))
            root.label(label, mid[0], mid[1], 180)
            if name == "VBUS":
                netclass_flag(root, "Power", bx + 7.62, py, "VBUS")
            continue
        (x1, y1, a1), (x2, y2, a2) = sorted(ends)
        if y1 != y2:
            raise ValueError("net %s: pins not on one row (%s, %s)" % (n["net"], ends[0], ends[1]))
        if label:
            # label 2.54 mm from the driving pin, text toward the receiver
            drv = next(p for p in n["pins"] if p["dir"] in ("output", "bidirectional"))
            dx_, dy_, _ = uses[drv["sheet"]].pin_xy(drv["pin"])
            if dx_ == x1:
                lp, ang = (x1 + 2.54, y1), 0
            else:
                lp, ang = (x2 - 2.54, y1), 180
            pts = sorted([(x1, y1), lp, (x2, y2)])
            root.wire(*pts)
            root.label(label, lp[0], lp[1], ang)
        else:
            root.wire((x1, y1), (x2, y2))
        if n["net"] == "/ESC1/PHASE_A":
            netclass_flag(root, "Phase", x1 + 10.16, y1, "PHASE")
        if n["net"] == "/CURR_SENSE":
            netclass_flag(root, "Analog", x1 + 57.15, y1, "CURR")
    # ---- power table + notes
    rails = c["power_rails"]
    rows = [["Rail", "Source", "Nominal", "Budget (spec 5)", "Feeds"]]
    rows += [[r["rail"]] + list(r["table"]) for r in rails]
    bold_text(root, "POWER TABLE", 17.78, 207.01, size=2.54, key="pt-head")
    table(root, 17.78, 212.09, [22.86, 55.88, 22.86, 50.8, 116.84], 3.81, rows, "power")
    note(root, "Generated from hardware/sch_contract.json by hardware/tools/sch_root.py: do not edit by hand.\n"
               "Root wires carry the project-wide net names (root label = net /NAME). Motor phases are named by the "
               "ESC sheets (/ESCn/PHASE_x). Rails are power symbols (table); VBUS is a hierarchical net.\n"
               "ESC1-ESC4 drive M1 rear right, M2 front right, M3 rear left, M4 front left (Betaflight quad-X); "
               "FC pin map: research/PINMAP.md.", 302.26, 212.09, 104.14, 30.48, key="root-note")
    return sheets


def save_sheets(prj, files, root=False):
    """Write (and kicad-cli re-save) only `files` (+ the root if root=True): a sheet shard must never overwrite the
    sheets of another shard or the root."""
    keep = prj.sheets
    prj.sheets = {f: s for f, s in keep.items() if f in files or (root and s is prj.root)}
    missing = set(files) - set(prj.sheets)
    if missing:
        prj.sheets = keep
        raise KeyError("unknown sheet files %s" % sorted(missing))
    try:
        return prj.save()
    finally:
        prj.sheets = keep


def write_uuids(prj, c, path=CONTRACT):
    insts = prj.instances()
    root_uuid = prj.root.uuid
    u = {"root_file": root_uuid, "namespace": "uuid5(root file uuid, '<file>|<kind>|<key>') (sch_build.Project.uid)",
         "files": {f: s.uuid for f, s in prj.sheets.items()}, "sheet_symbols": {}}
    for sheet, uuids, names, off, page in insts:
        if not names:
            continue
        u["sheet_symbols"][names[-1]] = {"uuid": uuids[-1], "file": sheet.file, "page": page,
                                         "instance_path": "/" + "/".join([root_uuid] + uuids)}
    c["uuids"] = u
    for sh in c["sheets"]:
        sh["file_uuid"] = u["files"][sh["file"]]
        for inst in sh["instances"]:
            s = u["sheet_symbols"][inst["name"]]
            inst["sheet_uuid"], inst["instance_path"], inst["page"] = s["uuid"], s["instance_path"], s["page"]
    c["root"]["uuid"] = root_uuid
    json.dump(c, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stubs", action="store_true", help="also (over)write every sub-sheet as an empty decorated file")
    a = ap.parse_args()
    c = load_contract()
    prj = sb.Project(os.path.join(HW, c["root"]["file"]))
    build_root(prj, c)
    if not a.stubs:
        missing = [f for f in prj.sheets if f != prj.root.file and not os.path.exists(os.path.join(HW, f))]
        if missing:
            sys.exit("sub-sheets missing (run with --stubs): %s" % missing)
        save_sheets(prj, [], root=True)          # keep the sub-sheets: write the root only
    else:
        prj.save()
    write_uuids(prj, c)
    print("root + %d sheet files, %d sheet symbols, %d root nets" %
          (len(prj.sheets) - 1, len(c["uuids"]["sheet_symbols"]), len(c["nets"])))


if __name__ == "__main__":
    main()
