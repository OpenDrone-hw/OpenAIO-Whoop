#!/usr/bin/env python3
"""Check a KiCad project against the OpenDrone lineup conventions.

    /usr/bin/python3.12 hardware/tools/check_conventions.py [project.kicad_pro]
        [--stage planned|alpha] [--repo NAME] [--model-fixes model-fixes.json]

Runs under any Python that imports pcbnew (KPY on macOS, /usr/bin/python3.12 in
the agent container). Read-only: schematics are read as s-expressions, the
board is loaded with pcbnew and never saved, README.md and AGENTS.md are read
from the repo root one level above hardware/.

Rule ids are the numbers in research/LINEUP-CONVENTIONS.md; only the machine-
checkable ones are here. Every line is "<status>  <rule>  <message>":

    ok    the rule holds
    FAIL  a MUST rule is broken
    warn  a SHOULD rule is broken, or a MUST could only be checked in part
    skip  nothing to check yet (no symbols, no outline, wrong stage)

--stage alpha adds what a board needs once it is produced: DOC_* text
variables, renders, README without the planned-only sections. --model-fixes
points at OpenDrone-hw/.github engineering/model-fixes.json; without it rule
B17b is skipped.

Exit 0 when no MUST rule fails, 1 on any FAIL, 2 if the project cannot be read.
"""
import argparse, glob, json, os, re, sys

from check_board_setup import TOKEN, child, load_pcbnew_board, sexp_block, stackup

# Paper sizes in mm, landscape. KiCad's default frame has a 10 mm margin and
# the title block in the bottom-right corner.
PAPER = {"A5": (210, 148), "A4": (297, 210), "A3": (420, 297), "A2": (594, 420),
         "A1": (841, 594), "A0": (1189, 841), "A": (279.4, 215.9), "B": (431.8, 279.4),
         "USLetter": (279.4, 215.9), "USLegal": (355.6, 215.9)}
# Wordmark fills: shipped sheets use black + the retired gold; the current
# on-light artwork (OpenDrone-Brand wordmark/opendrone-wordmark-onlight.svg) is
# ink #1a1a1e + gold #ffb700. Same nine paths either way.
INK = {(0, 0, 0), (26, 26, 30)}
GOLD = {(200, 157, 46): "#c89d2e (deprecated light gold, as shipped)",
        (255, 183, 0): "#ffb700 (current brand gold)"}
REV = re.compile(r"^rev\d+(\.\d+)?$")                     # rev1, rev3.3
LABEL = re.compile(r"^[A-Z0-9_+\-./]+$")
BUS = re.compile(r"^[A-Z0-9_]*\{[A-Z0-9_, .]+\}$|^[A-Z0-9_]+\[\d+\.\.\d+\]$")
POWER_STYLE = re.compile(r"^(\+(BATT|\d+(\.\d+)?V(_[A-Z0-9]+)*)|GND)$")   # template net_colors
LIB_TABLE = re.compile(r'\(lib \(name "([^"]+)"\)\(type "[^"]*"\)\(uri "([^"]+)"\)')
# KiCad stock library nicknames, by family prefix. Not installed in the agent
# container, so this list stands in for the global tables.
STOCK = re.compile(r"^(power|Device|Connector(_\w+)?|Diode(_\w+)?|LED(_\w+)?|Transistor_\w+|"
                   r"Regulator_\w+|Power_\w+|MCU_\w+|Memory_\w+|Sensor(_\w+)?|Interface(_\w+)?|"
                   r"Amplifier_\w+|Analog(_\w+)?|Comparator|Logic_\w+|74x\w*|Switch|Jumper|"
                   r"Mechanical|Graphic|Oscillator|Crystal|Filter|Fuse|Inductor_\w+|"
                   r"Capacitor_\w+|Resistor_\w+|Package_\w+|TestPoint|MountingHole|Fiducial|"
                   r"RF(_\w+)?|Button_Switch_\w+|Buzzer_Beeper|Battery|Motor|Relay(_\w+)?|"
                   r"Converter_\w+|Driver_\w+|Isolator(_\w+)?|Reference_Voltage|Timer(_\w+)?|"
                   r"Display_\w+|Audio|Video|Symbol|Varistor|Ferrite\w*|Net[Tt]ie|Transformer\w*)$")
PROJECT_LIBS = {"lib", "OpenDrone"}
MODEL_PREFIXES = ("${KICAD10_3DMODEL_DIR}/", "${OPENDRONE_LIB}/3dmodel/", "${KIPRJMOD}/")
DOC_VARS = ["DOC_FIRMWARE", "DOC_HANDLE", "DOC_INPUT", "DOC_MCU", "DOC_NAME",
            "DOC_PROTOCOL", "DOC_RATING", "DOC_TAGLINE", "DOC_VARIANT"]
README_PLANNED = ["Why", "Specifications", "Constraints", "Prior art", "Design questions",
                  "In the line", "Contributing", "License"]
README_ALPHA = ["Specifications", "In the line", "Contributing", "License"]
AGENTS_ORDER = ["Architecture", "Power", "Key parts", "Connectors and I/O", "Layout rules",
                "Firmware", "Repo", "Parts and datasheets", "Environment", "Rules",
                "Revisions", "By task"]
RULE_LEADS = ["**Never text-edit**", "**Metadata yes, connections no.**",
              "**Close KiCad before any write to a KiCad file.**", "**Reuse before you draw.**",
              "**One person holds a board layout at a time.**",
              "**Run ERC and DRC before every pull request.**"]

results = []


def report(status, rule, message):
    results.append(status)
    print(f"{status:4}  {rule:5} {message}")


def verdict(rule, title, bad, must=True, ok_detail="", limit=6):
    """One line per rule: bad is a list of offenders, empty when the rule holds."""
    if not bad:
        report("ok", rule, title + (f": {ok_detail}" if ok_detail else ""))
    else:
        more = f" (+{len(bad) - limit} more)" if len(bad) > limit else ""
        report("FAIL" if must else "warn", rule, f"{title}: {'; '.join(map(str, bad[:limit]))}{more}")


# --- s-expressions ------------------------------------------------------------

def parse(text):
    stack = [[]]
    for t in (m.group() for m in TOKEN.finditer(text)):
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\") if t[0] == '"' else t)
    return stack[0][0]


def kids(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    found = kids(node, name)
    return found[0] if found else None


def props(node):
    return {p[1]: p[2] for p in kids(node, "property") if len(p) > 2}


def flag(node, name):
    k = kid(node, name)
    return k[1] == "yes" if k and len(k) > 1 else None


# --- the project ----------------------------------------------------------------

class Project:
    def __init__(self, pro, repo=None):
        self.pro = os.path.abspath(pro)
        self.dir = os.path.dirname(self.pro)
        self.root = os.path.dirname(self.dir)
        self.name = os.path.splitext(os.path.basename(self.pro))[0]
        self.repo = repo or os.path.basename(self.root)
        self.settings = json.load(open(self.pro, encoding="utf-8"))
        self.vars = self.settings.get("text_variables", {}) or {}
        self.sheets = self.load_sheets()            # [(instance path, file, tree)]
        self.files = {}                             # file -> tree, each file once
        for _, f, tree in self.sheets:
            self.files.setdefault(f, tree)

    def path(self, *parts):
        return os.path.join(self.dir, *parts)

    def load_sheets(self):
        root = self.name + ".kicad_sch"
        if not os.path.isfile(self.path(root)):
            return []
        sheets, cache = [], {}

        def walk(fname, path, depth):
            if fname not in cache:
                cache[fname] = parse(open(self.path(fname), encoding="utf-8").read())
            tree = cache[fname]
            sheets.append((path, fname, tree))
            for s in kids(tree, "sheet"):
                sub = props(s).get("Sheetfile") or props(s).get("Sheet file")
                if sub and depth < 20 and os.path.isfile(self.path(sub)):
                    walk(sub, f"{path}/{kid(s, 'uuid')[1]}", depth + 1)

        tree = parse(open(self.path(root), encoding="utf-8").read())
        cache[root] = tree
        walk(root, "/" + kid(tree, "uuid")[1], 0)
        return sheets

    def symbols(self):
        """(file, symbol, props, [references at valid instance paths]) for placed symbols."""
        paths = {}
        for path, f, _ in self.sheets:
            paths.setdefault(f, set()).add(path)
        for f, tree in self.files.items():
            for s in kids(tree, "symbol"):
                p = props(s)
                refs = []
                for proj in kids(kid(s, "instances") or ["instances"], "project"):
                    refs += [(kid(i, "reference")[1], kid(i, "unit")[1] if kid(i, "unit") else "1")
                             for i in kids(proj, "path") if i[1] in paths[f] and kid(i, "reference")]
                yield f, s, p, refs or [(p.get("Reference", "?"), "1")]


# --- C: project files ---------------------------------------------------------

def check_project(prj, stage):
    expect = [prj.name + ext for ext in (".kicad_pro", ".kicad_sch", ".kicad_pcb", ".kicad_dru")] + \
             ["fp-lib-table", "sym-lib-table", "lib.kicad_sym", "lib.pretty", "lib.3dshapes",
              "fabrication-toolkit-options.json", "KiCad-Library"]
    missing = [f"hardware/{f}" for f in expect if not os.path.exists(prj.path(f))]
    missing += [f for f in ("README.md", "AGENTS.md", "CONTRIBUTING.md", "LICENSE", ".gitignore",
                            ".gitattributes") if not os.path.exists(os.path.join(prj.root, f))]
    if os.path.basename(prj.dir) != "hardware":
        missing.insert(0, f"project directory is {os.path.basename(prj.dir)}/, not hardware/")
    verdict("C1", "repository layout", missing)
    if not os.path.isdir(os.path.join(prj.root, "images")):
        report("warn", "C1", "no images/ directory (the template carries it; renders land there at alpha)")
    if os.path.isdir(prj.path("KiCad-Library")) and not os.listdir(prj.path("KiCad-Library")):
        report("warn", "C1", "hardware/KiCad-Library is empty: git submodule update --init")
    if prj.name != prj.repo:
        report("warn", "C1", f"project is named {prj.name}, repo {prj.repo}; newer boards use the repo name")

    lib = prj.vars.get("OPENDRONE_LIB")
    verdict("C2", "text variable OPENDRONE_LIB",
            [] if lib == "${KIPRJMOD}/KiCad-Library" else [f"is {lib!r}, want '${{KIPRJMOD}}/KiCad-Library'"],
            ok_detail=lib)
    if stage == "alpha":
        bad = [v for v in DOC_VARS if not str(prj.vars.get(v, "")).strip()]
        if prj.vars.get("DOC_NAME") not in (None, prj.repo):
            bad.append(f"DOC_NAME {prj.vars['DOC_NAME']!r} is not {prj.repo!r}")
        if prj.vars.get("DOC_HANDLE") not in (None, prj.repo.lower()):
            bad.append(f"DOC_HANDLE {prj.vars['DOC_HANDLE']!r} is not {prj.repo.lower()!r}")
        verdict("C3", "DOC_* text variables", bad)
    else:
        report("skip", "C3", "DOC_* text variables are added at alpha")

    bad = []
    for table in ("sym-lib-table", "fp-lib-table"):
        if os.path.isfile(prj.path(table)):
            libs = LIB_TABLE.findall(open(prj.path(table), encoding="utf-8").read())
            names = {n for n, _ in libs}
            if names != PROJECT_LIBS:
                bad.append(f"{table} names {sorted(names)}, want ['OpenDrone', 'lib']")
            bad += [f"{table} {n}: {u} not under ${{KIPRJMOD}}" for n, u in libs if not u.startswith("${KIPRJMOD}/")]
    verdict("C4", "project library tables", bad)

    dru = prj.path(prj.name + ".kicad_dru")
    if os.path.isfile(dru):
        text = open(dru, encoding="utf-8").read()
        bad = [what for what, needle in (("canonical silkscreen-over-pad rule", '(rule "silkscreen over pad"'),
                                         ("board-specific marker line", "# --- board-specific rules below this line"))
               if needle not in text]
        verdict("C5", "design rules file carries the canonical block", bad)

    fab = prj.path("fabrication-toolkit-options.json")
    if os.path.isfile(fab):
        name = json.load(open(fab, encoding="utf-8")).get("ARCHIVE_NAME", "")
        prj.archive = name
        verdict("C6", "fabrication toolkit archive name",
                [] if re.fullmatch(re.escape(prj.repo) + r"-rev\d+(\.\d+)?", name) else
                [f"ARCHIVE_NAME {name!r}, want '{prj.repo}-rev<N>'"], ok_detail=name)
    else:
        report("FAIL", "C6", "hardware/fabrication-toolkit-options.json missing (copy from hardware-template)")


# --- A: schematic -------------------------------------------------------------

def title_block_parts(tree):
    """Title, rev and date from the title_block fields, else from free text in
    the title-block corner, which is how the shipped boards type them."""
    paper = kid(tree, "paper")
    w, h = PAPER.get(paper[1], (297, 210)) if paper else (297, 210)
    if paper and "portrait" in paper:
        w, h = h, w
    corner = lambda at: float(at[1]) >= w - 125 and float(at[2]) >= h - 50
    tb = {c[0]: c[1] for c in (kid(tree, "title_block") or ["title_block"])[1:] if len(c) > 1}
    texts = [t[1].replace("\\n", " ").strip() for t in kids(tree, "text") if corner(kid(t, "at"))]
    rev = tb.get("rev") or next((t for t in texts if re.fullmatch(r"(?i)(rev\s*)?\d+(\.\d+)*", t)), "")
    date = tb.get("date") or next((t for t in texts if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}", t)), "")
    title = tb.get("title") or max((t for t in texts if t not in (rev, date)), key=len, default="")
    black = gold = 0
    golds = set()
    for pl in kids(tree, "polyline"):
        fill = kid(pl, "fill")
        colour = kid(fill, "color") if fill else None
        pts = [p for p in (kid(pl, "pts") or [])[1:] if p[0] == "xy"]
        if not colour or not pts or not all(corner(p) for p in pts[:1]):
            continue
        rgb = tuple(int(float(c)) for c in colour[1:4])
        black += rgb in INK
        if rgb in GOLD:
            gold += 1
            golds.add(GOLD[rgb])
    return title, rev, date, black >= 4 and gold >= 5, golds


def check_schematic(prj, brev):
    if not prj.sheets:
        report("FAIL", "A1", f"root schematic hardware/{prj.name}.kicad_sch missing")
        return
    report("ok", "A1", f"root schematic is {prj.name}.kicad_sch, {len(prj.files) - 1} sub-sheet file(s)")
    verdict("A2", "sub-sheet files are lower-case snake_case",
            [f for f in prj.files if f != prj.name + ".kicad_sch" and not re.fullmatch(r"[a-z0-9_]+\.kicad_sch", f)])
    layout = prj.settings.get("schematic", {}).get("page_layout_descr_file", "")
    verdict("A4", "KiCad default page layout", [f"custom page layout {layout}"] if layout else [])

    missing, stale, golds = [], [], set()
    for f, tree in prj.files.items():
        title, rev, date, wordmark, g = title_block_parts(tree)
        golds |= g
        missing += [f"{f}: {what}" for what, ok in (("OpenDrone wordmark", wordmark), ("title", title),
                                                     ("rev", rev)) if not ok]
        if not date:
            stale.append(f"{f}: no date")
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            stale.append(f"{f}: date {date} not ISO")
        num = lambda r: r.lower().replace("rev", "").strip()
        if rev and brev and num(rev) != num(brev):
            stale.append(f"{f}: rev {rev} vs board {brev}")
    verdict("A5", "every sheet carries the wordmark, a title and a rev", missing,
            ok_detail=", ".join(sorted(golds)))
    if any("deprecated" in x for x in golds):
        report("warn", "A5", "wordmark gold is the deprecated #c89d2e (OpenDrone-Brand standards/deprecations.json)")
    verdict("A6", "sheet rev matches the board and the date is ISO", sorted(set(stale)), must=False)

    faces = sorted({(f, kid(n, "face")[1]) for f, tree in prj.files.items() for n in walk(tree)
                    if n[0] == "font" and kid(n, "face")})
    verdict("A7", "schematic text uses the KiCad default font", [f"{f}: {face}" for f, face in faces])

    syms = list(prj.symbols())
    parts = [(f, s, p, r) for f, s, p, r in syms if not p.get("Reference", "").startswith("#")]
    if not parts:
        for rule in ("A8", "A9", "A10", "A15", "A16"):
            report("skip", rule, "no symbols placed yet")
    else:
        table = {n for n, _ in LIB_TABLE.findall(open(prj.path("sym-lib-table"), encoding="utf-8").read())} \
            if os.path.isfile(prj.path("sym-lib-table")) else set()
        bad = sorted({kid(s, "lib_id")[1].split(":")[0] for f, s, p, r in parts
                      if kid(s, "lib_id")[1].split(":")[0] not in PROJECT_LIBS
                      and (kid(s, "lib_id")[1].split(":")[0] in table
                           or not STOCK.match(kid(s, "lib_id")[1].split(":")[0]))})
        verdict("A8", "symbols come from OpenDrone, lib or KiCad stock libraries",
                [f"nickname {n}" for n in bad])

        # A bare pad is copper, not an orderable part: it belongs out of the BOM (A16), not in A9.
        is_pad = lambda p: re.search(r"small_pad|SolderPad|TestPoint", p.get("Footprint", ""))
        bom = [(f, p) for f, s, p, r in parts if flag(s, "in_bom") is not False and not flag(s, "dnp")]
        # MPN + Manufacturer must be filled; the LCSC field must exist and is filled where the part has an LCSC
        # number (D60: NextPCB turnkey sources by MPN, CONTRIBUTING "LCSC when available"; hardware/tools/
        # check_netlist.py N3 checks the LCSC values against bom_plan.json).
        empty = lambda p: [k for k in ("MPN", "Manufacturer") if p.get(k, "").strip() in ("", "~")] + \
            (["LCSC field"] if "LCSC" not in p else [])
        no_lcsc = sum(1 for f, p in bom if not is_pad(p) and not p.get("LCSC", "").strip())
        verdict("A9", "BOM fields MPN, Manufacturer (+ LCSC field) on every BOM part",
                [f"{p.get('Reference')} ({f}) lacks {', '.join(empty(p))}" for f, p in bom if empty(p) and not is_pad(p)],
                ok_detail=f"{len(bom)} BOM symbol(s), {no_lcsc} without an LCSC number (D60)")
        verdict("A16", "solder pads and test points excluded from the BOM",
                [f"{p.get('Reference')} ({f})" for f, p in bom if is_pad(p)], must=False)

        bad = []
        for f, s, p, r in parts:
            ds, lib = p.get("Datasheet", ""), kid(s, "lib_id")[1].split(":")[0]
            if re.match(r"(file:|/|[A-Za-z]:[\\/]|~/)", ds):
                bad.append(f"{p.get('Reference')}: absolute path {ds}")
            elif ("OPENDRONE_LIB" in ds or lib == "OpenDrone") and ds not in ("", "~") and \
                    not re.fullmatch(r"\$\{OPENDRONE_LIB\}/datasheet/[^/]+\.pdf", ds):
                bad.append(f"{p.get('Reference')}: {ds}")
            elif lib == "OpenDrone" and ds in ("", "~") and flag(s, "in_bom") is not False:
                bad.append(f"{p.get('Reference')}: OpenDrone part without its catalogue datasheet")
        verdict("A10", "datasheet links resolve through ${OPENDRONE_LIB}, no local paths", bad)

        seen, bad = {}, []
        for f, s, p, refs in parts:
            for ref, unit in refs:
                if "?" in ref:
                    bad.append(f"{ref} not annotated ({f})")
                elif (ref, unit) in seen and seen[(ref, unit)] != id(s):
                    bad.append(f"{ref} used twice")
                seen[(ref, unit)] = id(s)
        verdict("A15", "references annotated and unique", sorted(set(bad)),
                ok_detail=f"{len({r for r, _ in seen})} reference(s)")

    power = sorted({p.get("Value", "") for f, s, p, r in syms if p.get("Reference", "").startswith("#PWR")})
    if power:
        verdict("A11", "power nets are +rails or GND",
                [v for v in power if not (v.startswith("+") or re.fullmatch(r"GND\w*", v))], ok_detail=" ".join(power))
        verdict("A11b", "power net style +<V>V[_SUFFIX] as in the template",
                [v for v in power if not POWER_STYLE.match(v)], must=False)
    else:
        report("skip", "A11", "no power symbols yet")

    labels = [(f, kind, l[1]) for f, tree in prj.files.items()
              for kind in ("label", "global_label", "hierarchical_label") for l in kids(tree, kind)]
    labels += [(f, "sheet pin", pin[1]) for f, tree in prj.files.items() for s in kids(tree, "sheet")
               for pin in kids(s, "pin")]
    if labels:
        verdict("A12", "no global labels", [f"{n} ({f})" for f, k, n in labels if k == "global_label"])
        plain = lambda n: re.sub(r"~\{([^}]*)\}", r"\1", n)        # overbar markup
        verdict("A12b", "net labels upper case, buses NAME{A,B}",
                sorted({f"{n} ({f})" for f, k, n in labels if not (BUS.match(n) or LABEL.match(plain(n)))}))
    else:
        report("skip", "A12", "no labels yet")


def walk(node):
    yield node
    for c in node[1:]:
        if isinstance(c, list) and c:
            yield from walk(c)


# --- B: board -----------------------------------------------------------------

def board_rev(prj):
    """The board's title-block rev, read before pcbnew so the schematic can be compared to it."""
    path = prj.path(prj.name + ".kicad_pcb")
    if not os.path.isfile(path):
        return ""
    text = open(path, encoding="utf-8").read()
    start = text.find("(title_block")
    rev = child(sexp_block(text, start), "rev") if start >= 0 else None
    return rev[1] if rev and len(rev) > 1 else ""


def check_board(prj, model_fixes):
    path = prj.path(prj.name + ".kicad_pcb")
    if not os.path.isfile(path):
        report("FAIL", "B0", f"board hardware/{prj.name}.kicad_pcb missing")
        return None
    pcbnew, b = load_pcbnew_board(path)
    if b is None:
        raise IOError("not a KiCad board")
    mm = pcbnew.ToMM
    text = open(path, encoding="utf-8").read()
    rev = b.GetTitleBlock().GetRevision()
    verdict("B6", "board title block rev is rev<N>[.<M>]", [] if REV.match(rev) else [f"rev is {rev!r}"],
            ok_detail=rev)
    if getattr(prj, "archive", "") and REV.match(rev) and not prj.archive.endswith("-" + rev):
        report("FAIL", "C6", f"ARCHIVE_NAME {prj.archive} does not end in the board rev {rev}")

    tent = re.search(r"\(tenting\s*\(front (\w+)\)\s*\(back (\w+)\)", text)
    verdict("B14", "vias tented both sides", [] if tent and tent.groups() == ("yes", "yes") else
            [f"tenting {tent.groups() if tent else 'not set'}"])

    copper = {L["layer"]: L.get("copper_oz", 1.0) for L in stackup(path) if L.get("type") == "copper"}
    outer_oz = max(copper.get("F.Cu", 1.0), copper.get("B.Cu", 1.0))
    # NextPCB silkscreen minimum (height, line) by outer copper weight.
    min_h, min_t = (1.27, 0.30) if outer_oz >= 2.9 else (1.07, 0.18) if outer_oz >= 1.9 else (0.76, 0.12)
    rule_h = prj.settings.get("board", {}).get("design_settings", {}).get("rules", {}).get("min_text_height", 0.8)
    min_h = max(min_h, rule_h)

    edge = b.GetBoardEdgesBoundingBox()
    has_outline = any(g.GetLayer() == pcbnew.Edge_Cuts for g in
                      list(b.GetDrawings()) + [i for fp in b.GetFootprints() for i in fp.GraphicalItems()])
    fps = list(b.GetFootprints())

    def fid(fp):
        return fp.GetFPIDAsString()

    # Footprint libraries and 3D models need no outline.
    if fps:
        table = {n for n, _ in LIB_TABLE.findall(open(prj.path("fp-lib-table"), encoding="utf-8").read())} \
            if os.path.isfile(prj.path("fp-lib-table")) else set()
        nick = lambda fp: fid(fp).split(":")[0]
        verdict("B19", "footprints come from OpenDrone, lib or KiCad stock libraries",
                sorted({f"nickname {nick(fp)}" for fp in fps if nick(fp) not in PROJECT_LIBS
                        and (nick(fp) in table or not STOCK.match(nick(fp)))}))
        check_models(prj, fps, fid, model_fixes)
    else:
        for rule in ("B19", "B17"):
            report("skip", rule, "no footprints placed yet")

    if not has_outline or not fps:
        for rule in ("B2", "B3", "B4", "B5", "B7", "B8", "B9", "B10", "B11", "B13"):
            report("skip", rule, "no outline or no footprints yet")
        return

    silk = (pcbnew.F_SilkS, pcbnew.B_SilkS)
    fab_layers = set(silk) | {pcbnew.F_Mask, pcbnew.B_Mask} | {l for l in range(pcbnew.PCB_LAYER_ID_COUNT) if pcbnew.IsCopperLayer(l)}
    inside = lambda item: edge.Contains(item.GetPosition())
    texts = [d for d in b.GetDrawings() if d.GetClass() in ("PCB_TEXT", "PCB_TEXTBOX")]
    for fp in fps:
        texts += [t for t in fp.GraphicalItems() if t.GetClass() in ("PCB_TEXT", "PCB_TEXTBOX") and t.IsVisible()]
        texts += [t for t in fp.GetFields() if t.IsVisible()]
    shown = lambda t: t.GetShownText(True).replace("\n", " ").strip()
    fabbed = [t for t in texts if t.GetLayer() in fab_layers and inside(t)]
    silk_texts = [t for t in fabbed if t.GetLayer() in silk]

    verdict("B2", "no 'drone' on any fabricated layer",
            [f"{b.GetLayerName(t.GetLayer())} {shown(t)!r}" for t in fabbed if "drone" in shown(t).lower()])

    # OpenRX-Lite (10 x 11.5 mm) carries neither logo nor rev: below 15 mm they are SHOULD.
    tiny = max(mm(edge.GetWidth()), mm(edge.GetHeight())) < 15
    logo = find_logo(pcbnew, b, edge)
    verdict("B3", "incutec logo on silkscreen", [] if logo else ["no 8-polygon incutec artwork found"],
            must=not tiny, ok_detail=logo)
    words = [shown(t).lower() for t in fabbed if t.GetLayer() in silk + (pcbnew.F_Mask, pcbnew.B_Mask)]
    verdict("B4", "product name 'OPEN' + type on the board", [] if any(re.search(r"\bopen", w) for w in words)
            else ["no 'OPEN...' text inside the outline"])
    revs = [shown(t) for t in silk_texts if re.fullmatch(r"(?i)rev\s*\d+(\.\d+)*", shown(t))]
    verdict("B5", "revision printed on silkscreen and equal to the title block",
            [] if any(r.lower().replace(" ", "") == rev for r in revs) else [f"silk {revs or 'none'}, title block {rev!r}"],
            must=not tiny, ok_detail=", ".join(revs))

    labels = {pcbnew.F_Cu: [t for t in silk_texts if t.GetLayer() == pcbnew.F_SilkS],
              pcbnew.B_Cu: [t for t in silk_texts if t.GetLayer() == pcbnew.B_SilkS]}
    user_pads = [fp for fp in fps if re.search(r"small_pad|SolderPad", fid(fp))]
    bad = []
    for fp in user_pads:
        side = labels[pcbnew.B_Cu if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_Cu]
        near = min((gap(mm, p.GetBoundingBox(), t.GetBoundingBox()) for p in fp.Pads() for t in side
                    if t.GetClass() != "PCB_FIELD"), default=99)
        if near > 1.0:
            bad.append(f"{fp.GetReference()} ({near:.1f} mm)")
    if user_pads:
        verdict("B7", "every solder pad has a silkscreen label within 1 mm", bad,
                ok_detail=f"{len(user_pads)} pad(s)")
    else:
        report("skip", "B7", "no small_pad or SolderPad footprints")

    nets = [str(n) for n in b.GetNetsByName().keys()]
    tokens = {w for t in silk_texts for w in shown(t).upper().split()}
    if any(re.search(r"(^|/)\+?V?BATT?$", n) for n in nets):
        plus = tokens & {"+", "B+", "BAT+", "+BATT", "VBAT"}
        minus = tokens & {"-", "B-", "BAT-"}
        verdict("B8", "battery + and - labelled", [] if plus and minus else
                [f"found {sorted(plus | minus) or 'none'}"], ok_detail=" ".join(sorted(plus | minus)))
    else:
        report("skip", "B8", "no battery net")
    if any(re.search(r"(^|/)(MOTOR|M)[1-4]$|^/ESC[1-4]/", n) for n in nets):
        missing = [n for n in "1234" if not (tokens & {n, "M" + n})]
        verdict("B9", "motor outputs numbered 1-4 on silkscreen", [f"no {n} / M{n}" for n in missing])
    else:
        report("skip", "B9", "no motor outputs")

    verdict("B10", "reference designators hidden on silkscreen",
            [fp.GetReference() for fp in fps if fp.Reference().IsVisible() and fp.Reference().GetLayer() in silk])

    small = [f"{shown(t)!r} {mm(t.GetTextHeight()):.2f} mm" for t in silk_texts if mm(t.GetTextHeight()) < min_h - 1e-6]
    thin = [f"{shown(t)!r} {mm(t.GetTextThickness()):.2f} mm" for t in silk_texts
            if not t.GetFontName() and mm(t.GetTextThickness()) < min_t - 1e-6]
    verdict("B11", f"silk text >= {min_h} mm high, stroke font >= {min_t} mm ({outer_oz:g} oz outer)",
            small + thin, ok_detail=f"{len(silk_texts)} text(s), smallest "
            f"{min((mm(t.GetTextHeight()) for t in silk_texts), default=0):.2f} mm")
    fonts = sorted({t.GetFontName() or "KiCad" for t in silk_texts if t.GetClass() != "PCB_FIELD"})
    verdict("B12", "silkscreen font is Tokyo", [f for f in fonts if f != "Tokyo"], must=False,
            ok_detail="Tokyo")
    if any(t.GetFontName() for t in silk_texts) and "(embedded_fonts yes)" not in text:
        report("warn", "B12", "outline font not embedded: a machine without it plots a substitute")
    verdict("B13", "back silkscreen mirrored, front not",
            [f"{b.GetLayerName(t.GetLayer())} {shown(t)!r}" for t in silk_texts
             if t.IsMirrored() != (t.GetLayer() == pcbnew.B_SilkS)])


def gap(mm, a, b):
    dx = max(0, max(a.GetLeft(), b.GetLeft()) - min(a.GetRight(), b.GetRight()))
    dy = max(0, max(a.GetTop(), b.GetTop()) - min(a.GetBottom(), b.GetBottom()))
    return mm(max(dx, dy))


def find_logo(pcbnew, b, edge):
    """The incutec silkscreen logo on every shipped board is eight filled
    polygons with a 4.36:1 bounding box. Cluster silk polygons that sit within
    0.6 mm of each other and look for that signature."""
    mm = pcbnew.ToMM
    for layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        polys = [d for d in b.GetDrawings() if d.GetClass() == "PCB_SHAPE" and d.GetShapeStr() == "Polygon"
                 and d.GetLayer() == layer and edge.Contains(d.GetCenter())]
        polys += [i for fp in b.GetFootprints() for i in fp.GraphicalItems()
                  if i.GetClass() == "PCB_SHAPE" and i.GetShapeStr() == "Polygon" and i.GetLayer() == layer]
        boxes = [p.GetBoundingBox() for p in polys]
        group = list(range(len(polys)))

        def find(i):
            while group[i] != i:
                i = group[i]
            return i
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                if gap(mm, boxes[i], boxes[j]) < 0.6:
                    group[find(i)] = find(j)
        clusters = {}
        for i in range(len(polys)):
            clusters.setdefault(find(i), []).append(boxes[i])
        for members in clusters.values():
            box = pcbnew.BOX2I(members[0].GetPosition(), members[0].GetSize())
            for m in members[1:]:
                box.Merge(m)
            w, h = mm(box.GetWidth()), mm(box.GetHeight())
            if 7 <= len(members) <= 9 and 4.1 <= max(w, h) / max(min(w, h), 1e-3) <= 4.6:
                return f"{b.GetLayerName(layer)} {max(w, h):.1f} x {min(w, h):.1f} mm"
    return None


def check_models(prj, fps, fid, model_fixes):
    lib = prj.vars.get("OPENDRONE_LIB", "").replace("${KIPRJMOD}", prj.dir)
    roots = {"${OPENDRONE_LIB}/": lib, "${KIPRJMOD}/": prj.dir}
    bad_prefix, missing, unverified, none = [], [], 0, []
    for fp in fps:
        models = list(fp.Models())
        if not models and not (fp.IsDNP() or fp.IsExcludedFromBOM() or fp.IsBoardOnly()
                               or re.search(r"small_pad|SolderPad|TestPoint", fid(fp))):
            none.append(fp.GetReference())
        for m in models:
            name = m.m_Filename
            if not name.startswith(MODEL_PREFIXES):
                bad_prefix.append(f"{fp.GetReference()} {name}")
                continue
            root = next((v for k, v in roots.items() if name.startswith(k)), None)
            if root and os.path.isdir(root) and os.listdir(root):
                rel = name.split("}/", 1)[1]
                if not os.path.isfile(os.path.join(root, rel)):
                    missing.append(f"{fp.GetReference()} {name}")
            else:
                unverified += 1
    verdict("B17", "3D model paths use ${KICAD10_3DMODEL_DIR}, ${OPENDRONE_LIB} or ${KIPRJMOD}", bad_prefix)
    verdict("B17", "3D model files exist", missing,
            ok_detail=f"{unverified} model(s) not verifiable here (stock or uninitialised library)")
    if none:
        report("warn", "B17", f"{len(none)} BOM footprint(s) without a 3D model: {', '.join(none[:8])}")
    if not model_fixes:
        report("skip", "B17b", "no --model-fixes given")
        return
    fixes = json.load(open(model_fixes, encoding="utf-8"))["fixes"]
    bad = []
    for fp in fps:
        name = fid(fp).split(":")[-1]
        for m in fp.Models():
            base = os.path.splitext(os.path.basename(m.m_Filename))[0]
            for fix in fixes:
                if re.search(fix["footprint"], name) and re.search(fix["model"], base):
                    got = [m.m_Rotation.x, m.m_Rotation.y, m.m_Rotation.z], [m.m_Offset.x, m.m_Offset.y, m.m_Offset.z]
                    if any(abs(g - w) > 1e-3 for g, w in zip(got[0] + got[1], fix["rotation"] + fix["offset"])):
                        bad.append(f"{fp.GetReference()} {name}: rotation {got[0]} offset {got[1]}, "
                                   f"want {fix['rotation']} {fix['offset']}")
    verdict("B17b", "3D model fixes from model-fixes.json applied", bad)


def check_renders(prj, stage):
    if stage != "alpha":
        report("skip", "B18", "renders are required from alpha")
        return
    verdict("B18", "README renders images/front.png and images/back.png",
            [f"images/{n}" for n in ("front.png", "back.png") if not os.path.isfile(os.path.join(prj.root, "images", n))])


# --- D: docs --------------------------------------------------------------------

def headings(path):
    return [l[3:].strip() for l in open(path, encoding="utf-8").read().splitlines() if l.startswith("## ")]


def in_order(found, order):
    known = [h for h in found if h in order]
    return known == sorted(known, key=order.index)


def check_docs(prj, stage):
    readme = os.path.join(prj.root, "README.md")
    if os.path.isfile(readme):
        text = open(readme, encoding="utf-8").read()
        found = headings(readme)
        order = README_ALPHA if stage == "alpha" else README_PLANNED
        bad = [f"missing ## {h}" for h in order if h not in found and not (stage == "planned" and h in ("Constraints", "Prior art", "Design questions"))]
        if not in_order(found, README_PLANNED):
            bad.append(f"sections out of template order: {found}")
        if stage == "alpha":
            bad += [f"planned-only ## {h} still present" for h in README_PLANNED if h in found and h not in README_ALPHA]
        verdict("D1", "README sections in template order", bad)
        extra = [h for h in found if h not in README_PLANNED]
        if extra:
            report("warn", "D1", f"README sections not in the template: {extra}")

        spec = re.search(r"^## Specifications\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        rows = [l for l in (spec.group(1) if spec else "").splitlines() if l.startswith("|")]
        bad = []
        if not rows:
            bad.append("no table under ## Specifications")
        else:
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            if any(len(c) != 2 for c in cells):
                bad.append("first table is not two columns")
            bad += [f"non-ASCII cell {c!r}" for row in cells for c in row if not c.isascii()]
        verdict("D2", "Specifications table: two columns, plain ASCII", bad, ok_detail=f"{max(len(rows) - 2, 0)} row(s)")
        verdict("D4", "status badge names the repo",
                [] if f"opendrone.be/api/status/{prj.repo}.json" in text else [f"no opendrone.be/api/status/{prj.repo}.json"])
        if stage == "alpha":
            verdict("D4", "alpha badges: shop and OSHWA", [b for b in ("badge/shop-opendrone.be", "OSHWA") if b not in text])
    agents = os.path.join(prj.root, "AGENTS.md")
    if os.path.isfile(agents):
        found = headings(agents)
        text = open(agents, encoding="utf-8").read()
        need = ["Repo", "Rules"] + (["Revisions"] if stage == "alpha" else [])
        bad = [f"missing ## {h}" for h in need if h not in found]
        if not in_order(found, AGENTS_ORDER):
            bad.append(f"sections out of template order: {found}")
        verdict("D3", "AGENTS.md sections in template order", bad)
        extra = [h for h in found if h not in AGENTS_ORDER]
        if extra:
            report("warn", "D3", f"AGENTS.md sections not in the template: {extra}")
        verdict("D3", "AGENTS.md Rules section carries the six template rules",
                [r for r in RULE_LEADS if r not in text])


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project", nargs="?", help="default: the one .kicad_pro in hardware/")
    ap.add_argument("--stage", choices=("planned", "alpha"), default="planned",
                    help="project stage; alpha adds DOC_* variables, renders and alpha README shape")
    ap.add_argument("--repo", help="repository name (default: the directory above hardware/)")
    ap.add_argument("--model-fixes", metavar="JSON", help="OpenDrone-hw/.github engineering/model-fixes.json")
    args = ap.parse_args()
    found = [args.project] if args.project else glob.glob(os.path.join(here, "..", "*.kicad_pro"))
    if len(found) != 1 or not os.path.isfile(found[0]):
        print(f"need exactly one project file, found {found or 'none'}", file=sys.stderr)
        return 2
    try:
        prj = Project(found[0], args.repo)
    except Exception as e:  # unreadable JSON or s-expression
        print(f"cannot read {found[0]}: {e}", file=sys.stderr)
        return 2
    print(f"project  {os.path.relpath(prj.pro)}  repo {prj.repo}  stage {args.stage}")
    check_project(prj, args.stage)
    check_schematic(prj, board_rev(prj))
    try:
        check_board(prj, args.model_fixes)
    except IOError as e:
        print(f"cannot read the board: {e}", file=sys.stderr)
        return 2
    check_renders(prj, args.stage)
    check_docs(prj, args.stage)
    counts = {s: results.count(s) for s in ("ok", "FAIL", "warn", "skip")}
    print(f"{counts['ok']} ok, {counts['FAIL']} FAIL, {counts['warn']} warn, {counts['skip']} skip")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
