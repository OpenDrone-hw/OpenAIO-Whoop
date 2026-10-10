#!/usr/bin/env python3
"""Report a board's setup and optionally check it against a spec.

    $KPY hardware/tools/check_board_setup.py [board.kicad_pcb] [--spec spec.json] [--json]

Runs under KiCad's Python (KPY, see AGENTS.md). Read-only: the board is loaded
with pcbnew and never saved. KiCad 10 has no Python binding for the stackup,
so that one block is parsed from the file's (setup (stackup ...)).

Every report line is "<key>  <value>", and the key is what a spec names. A spec
is {"tolerance": 0.0005, "expect": {"<key>": value | {"value": v, "tol": t}}}.
Numbers match within the tolerance, strings and null exactly, lists element by
element, objects on the keys the spec lists. See board_spec.example.json.

Holes are pads drilled at least --min-hole mm and closed cut-outs in the
Edge.Cuts outline. Positions are relative to the outline's bounding-box centre
(KiCad axes, +y down), or absolute when there is no outline. Keepouts are the
board's rule areas by name: layers, the keepout flags set, area and bounding
box (relative like the holes).

Exit 0 when every spec key matches, 1 on any mismatch, 2 if the board cannot
be read.
"""
import argparse, glob, json, os, re, sys

TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def load_pcbnew_board(path):
    # KiCad 10 prints harmless C++ asserts on import; keep them off the report.
    saved, null = os.dup(2), os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 2)
    try:
        import pcbnew
        return pcbnew, pcbnew.LoadBoard(path)
    finally:
        os.dup2(saved, 2)
        os.close(saved)
        os.close(null)


def sexp_block(text, start):
    """Parse the balanced s-expression starting at text[start] into lists."""
    stack = []
    for t in (m.group() for m in TOKEN.finditer(text, start)):
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            if not stack:
                return node
            stack[-1].append(node)
        else:
            stack[-1].append(t[1:-1] if t[0] == '"' else t)


def child(node, name):
    return next((c for c in node[1:] if isinstance(c, list) and c[0] == name), None)


def stackup(path):
    text = open(path, encoding="utf-8").read()
    start = text.find("(setup")
    block = child(sexp_block(text, start), "stackup") if start >= 0 else None
    layers = []
    for layer in (c for c in (block or [])[1:] if isinstance(c, list) and c[0] == "layer"):
        item = {"layer": layer[1]}
        for key in ("type", "material", "thickness"):
            node = child(layer, key)
            if node:
                item[key] = node[1]
        if "thickness" in item:
            item["thickness_mm"] = float(item.pop("thickness"))
        if item.get("type") == "copper" and "thickness_mm" in item:
            item["copper_oz"] = round(item["thickness_mm"] / 0.035, 2)  # 1 oz = 35 um
        layers.append(item)
    return layers


def report(path, min_hole=1.0):
    pcbnew, b = load_pcbnew_board(path)
    if b is None:
        raise IOError("not a KiCad board")
    mm = lambda v: round(pcbnew.ToMM(v), 4)
    ds = b.GetDesignSettings()

    classes = {"Default": ds.m_NetSettings.GetDefaultNetclass()}
    # Names come back as wxString, which neither equals nor hashes like str: convert, or lookups miss.
    classes.update({str(k): v for k, v in ds.m_NetSettings.GetNetclasses().items()})
    fields = {"clearance": "Clearance", "track": "TrackWidth", "via_dia": "ViaDiameter",
              "via_drill": "ViaDrill", "uvia_dia": "uViaDiameter", "uvia_drill": "uViaDrill",
              "dp_width": "DiffPairWidth", "dp_gap": "DiffPairGap"}
    netclasses = {name: {k + "_mm": mm(getattr(nc, "Get" + f)()) if getattr(nc, "Has" + f)() else None
                         for k, f in fields.items()} for name, nc in classes.items()}

    # Outline: Edge.Cuts drawn on the board or carried by an outline footprint.
    graphics = list(b.GetDrawings()) + [g for fp in b.GetFootprints() for g in fp.GraphicalItems()]
    outline, centre, poly = None, (0, 0), pcbnew.SHAPE_POLY_SET()
    if any(g.GetLayer() == pcbnew.Edge_Cuts for g in graphics):
        closed = b.GetBoardPolygonOutlines(poly, False) and poly.OutlineCount() > 0
        # Polygon box is on the line centres; the edge box would add the line width.
        bb = poly.BBox() if closed else b.GetBoardEdgesBoundingBox()
        centre = (bb.Centre().x, bb.Centre().y)
        outline = {"closed": closed,
                   "bbox_mm": [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())],
                   "size_mm": [mm(bb.GetWidth()), mm(bb.GetHeight())],
                   "area_mm2": round(poly.Area() / 1e12, 2)}  # net of cut-outs

    # Mounting holes: pads drilled >= min_hole, and closed cut-outs in the outline.
    def hole(pos, dia, kind, ref):
        return {"ref": ref, "x_mm": mm(pos.x - centre[0]), "y_mm": mm(pos.y - centre[1]),
                "dia_mm": mm(dia), "kind": kind}

    holes = [hole(p.GetPosition(), p.GetDrillSizeX(),
                  "npth" if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "pth",
                  p.GetParentFootprint().GetReference())
             for p in b.GetPads() if p.GetDrillSizeX() >= pcbnew.FromMM(min_hole)]
    for i in range(poly.OutlineCount() if outline else 0):
        for j in range(poly.HoleCount(i)):
            bb = poly.CHole(i, j).BBox()  # dia is the width; a slot also gets its size
            holes.append(hole(bb.Centre(), bb.GetWidth(), "cutout", ""))
            if abs(bb.GetWidth() - bb.GetHeight()) > pcbnew.FromMM(0.01):
                holes[-1]["size_mm"] = [mm(bb.GetWidth()), mm(bb.GetHeight())]
    holes.sort(key=lambda h: (h["y_mm"], h["x_mm"]))

    # Rule areas (keepouts and named areas for custom rules), by name; bbox relative to the outline centre.
    keepouts = []
    for z in b.Zones():
        if not z.GetIsRuleArea():
            continue
        flags = [k for k, f in (("footprints", z.GetDoNotAllowFootprints), ("tracks", z.GetDoNotAllowTracks),
                                ("vias", z.GetDoNotAllowVias), ("pads", z.GetDoNotAllowPads),
                                ("zone_fills", z.GetDoNotAllowZoneFills)) if f()]
        zb = z.Outline().BBox()
        keepouts.append({"name": z.GetZoneName(), "layers": [b.GetLayerName(l) for l in z.GetLayerSet().Seq()],
                         "keepout": flags, "area_mm2": round(z.Outline().Area() / 1e12, 2),
                         "bbox_mm": [mm(zb.GetLeft() - centre[0]), mm(zb.GetTop() - centre[1]),
                                     mm(zb.GetRight() - centre[0]), mm(zb.GetBottom() - centre[1])]})
    keepouts.sort(key=lambda k: k["name"])

    return {
        "copper_layers": b.GetCopperLayerCount(),
        "thickness_mm": mm(ds.GetBoardThickness()),
        "stackup": stackup(path),
        "rules": {
            "clearance_mm": mm(ds.m_MinClearance),
            "track_mm": mm(ds.m_TrackMinWidth),
            "connection_mm": mm(ds.m_MinConn),
            "via_dia_mm": mm(ds.m_ViasMinSize),
            "via_drill_mm": mm(ds.m_MinThroughDrill),
            "via_annular_mm": mm(ds.m_ViasMinAnnularWidth),
            "microvia_dia_mm": mm(ds.m_MicroViasMinSize),
            "microvia_drill_mm": mm(ds.m_MicroViasMinDrill),
            "hole_to_hole_mm": mm(ds.m_HoleToHoleMin),
            "hole_clearance_mm": mm(ds.m_HoleClearance),
            "copper_edge_mm": mm(ds.m_CopperEdgeClearance),
        },
        # Index 0 of both preset lists is KiCad's "use netclass" slot.
        "presets": {"track_mm": [mm(w) for w in list(ds.m_TrackWidthList)[1:]],
                    "via_mm": [[mm(v.m_Diameter), mm(v.m_Drill)] for v in list(ds.m_ViasDimensionsList)[1:]]},
        "netclasses": netclasses,
        "outline": outline,
        "holes": holes,
        "keepouts": keepouts,
    }


def flatten(value, key=""):
    """Yield (dotted key, leaf) pairs; lists of objects get one line per item."""
    if isinstance(value, dict) and value:
        for k, v in value.items():
            yield from flatten(v, f"{key}.{k}" if key else k)
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        for i, v in enumerate(value):
            yield f"{key}.{i}", " ".join(f"{k}={x}" for k, x in v.items())
    else:
        yield key, "none" if value in (None, [], {}) else value


def lookup(data, key):
    for part in key.split("."):
        if isinstance(data, list) and part.isdigit() and int(part) < len(data):
            data = data[int(part)]
        elif isinstance(data, dict) and part in data:
            data = data[part]
        else:
            raise KeyError(key)
    return data


def matches(got, want, tol):
    if isinstance(want, bool) or want is None or isinstance(want, str):
        return got == want
    if isinstance(want, (int, float)):
        return isinstance(got, (int, float)) and not isinstance(got, bool) and abs(got - want) <= tol
    if isinstance(want, list):
        return isinstance(got, list) and len(got) == len(want) and all(map(matches, got, want, [tol] * len(want)))
    if isinstance(want, dict):
        return isinstance(got, dict) and all(k in got and matches(got[k], w, tol) for k, w in want.items())
    return False


def check(data, spec):
    failures = 0
    for key, want in spec["expect"].items():
        tol = spec.get("tolerance", 0.0005)
        if isinstance(want, dict) and set(want) == {"value", "tol"}:
            want, tol = want["value"], want["tol"]
        try:
            got = lookup(data, key)
            ok = matches(got, want, tol)
        except KeyError:
            got, ok = "<missing>", False
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  {key}: {json.dumps(got)}" + ("" if ok else f"  expected {json.dumps(want)} +/- {tol}"))
    print(f"{len(spec['expect']) - failures}/{len(spec['expect'])} spec keys match")
    return failures


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board", nargs="?", help="default: the one .kicad_pcb in hardware/")
    ap.add_argument("--spec", help="JSON of expected values; exit 1 on mismatch")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--min-hole", type=float, default=1.0, metavar="MM",
                    help="smallest pad drill reported as a mounting hole (default 1.0)")
    args = ap.parse_args()
    boards = [args.board] if args.board else [os.path.relpath(p) for p in glob.glob(os.path.join(here, "..", "*.kicad_pcb"))]
    if len(boards) != 1 or not os.path.isfile(boards[0]):
        print(f"need exactly one board file, found {boards or 'none'}", file=sys.stderr)
        return 2
    board = boards[0]
    try:
        data = report(board, args.min_hole)
    except Exception as e:  # pcbnew raises plain IOError/RuntimeError on a bad file
        print(f"cannot read {board}: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"board  {board}")
        if not data["stackup"]:
            print("note   no stackup in the file; KiCad builds its default at the board thickness")
        for key, value in flatten(data):
            print(f"{key:34} {json.dumps(value) if isinstance(value, list) else value}")
    if args.spec:
        print()
        return 1 if check(data, json.load(open(args.spec))) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
