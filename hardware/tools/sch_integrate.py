#!/usr/bin/env python3
"""Project-wide passes over the OpenAIO-Whoop schematic after the sheet generators have written their files.

    /usr/bin/python3.12 hardware/tools/sch_integrate.py [HW_DIR] [--check]

Sheet files are written by separate generators (one per sheet, P4 shards), each with its own sch_build Project, so
three things can only be done with every sheet loaded:

1. Symbols: every placed part uses the lib_id that bom_plan.json names ('symbol'), and the copy embedded in the
   sheet is refreshed from the project libraries (lib, OpenDrone). A library edit (e.g. the pin types of the
   project copies of OpenDrone symbols) therefore reaches every sheet without ERC lib_symbol_mismatch.
2. Fields: Value, Footprint, MPN, Manufacturer and LCSC equal bom_plan (LCSC '' where bom_plan has none). BOM parts
   get the three sourcing fields even if a generator left one out.
3. Power and flag references: #PWR / #FLG numbered once over the whole hierarchy (page order, then y, x), so the
   per-shard ranges (#PWR201.., #PWR701.., #PWR01.. twice) do not collide.

Then kicad-cli re-saves every file (proves it loads). Idempotent: a second run changes nothing. --check only
reports what would change. Re-run it after any sheet generator. Never touches the board.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sch_build as sb  # noqa: E402
from sch_build import S, Atom, find, findall  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
CHECK = "--check" in sys.argv
HW = os.path.abspath(ARGS[0]) if ARGS else os.path.dirname(HERE)
ROOT = os.path.join(HW, "OpenAIO-Whoop.kicad_sch")
STOCK = "/usr/share/kicad/symbols"
SOURCING = ("MPN", "Manufacturer", "LCSC")


def libpath(nick):
    return {"lib": os.path.join(HW, "lib.kicad_sym"),
            "OpenDrone": os.path.join(HW, "KiCad-Library/symbol/OpenDrone.kicad_sym")}.get(
        nick, os.path.join(STOCK, nick + ".kicad_sym"))


LIBS = {}


def lib_symbol(lib_id):
    nick, name = lib_id.split(":", 1)
    if nick not in LIBS:
        LIBS[nick] = sb.SymbolLib(nick, libpath(nick))
    return LIBS[nick].get(name)


def prop(node, name):
    return next((p for p in findall(node, "property") if p[1] == name), None)


def main():
    bom = {p["ref"]: p for p in json.load(open(os.path.join(HW, "bom_plan.json"), encoding="utf-8"))["parts"]}
    root = sb.parse(open(ROOT, encoding="utf-8").read())
    root_uuid = find(root, "uuid")[1]
    # sheet files in page order, and the page of every instance path
    pages, files = {"/" + root_uuid: 1}, ["OpenAIO-Whoop.kicad_sch"]
    for sh in findall(root, "sheet"):
        u = find(sh, "uuid")[1]
        f = next(p[2] for p in findall(sh, "property") if p[1] == "Sheetfile")
        inst = find(find(find(sh, "instances"), "project"), "path")
        pages["/%s/%s" % (root_uuid, u)] = int(find(inst, "page")[1])
        if f not in files:
            files.append(f)
    def first_page(f):
        if f == "OpenAIO-Whoop.kicad_sch":
            return 1
        return min(pg for k, pg in pages.items() if k != "/" + root_uuid and _file_of(root, root_uuid, k) == f)
    files.sort(key=first_page)

    trees = {f: sb.parse(open(os.path.join(HW, f), encoding="utf-8").read()) for f in files}
    stats = {"lib_id": 0, "embedded": 0, "fields": 0, "added": 0, "power_refs": 0}
    power = []   # (page, y, x, path node, symbol node)
    for f in files:
        t = trees[f]
        libsec = find(t, "lib_symbols")
        used = set()
        for s in findall(t, "symbol"):
            lid = find(s, "lib_id")[1]
            paths = findall(find(find(s, "instances"), "project"), "path")
            refs = [find(p, "reference")[1] for p in paths]
            at = find(s, "at")
            if lid.startswith("power:"):
                for p in paths:
                    power.append((pages[p[1]], float(at[2]), float(at[1]), p, s))
                used.add(lid)
                continue
            parts = [bom[r] for r in refs if r in bom]
            if not parts:
                used.add(lid)
                continue
            b = parts[0]
            for k in ("symbol", "value", "footprint", "mpn", "manufacturer", "lcsc"):
                vals = {(q[k] or "") for q in parts}
                if len(vals) > 1:
                    sys.exit("%s: instances %s disagree on %s in bom_plan: %s" % (f, refs, k, vals))
            want = b["symbol"] or lid
            if want != lid:
                find(s, "lib_id")[1] = want
                stats["lib_id"] += 1
                lid = want
            used.add(lid)
            fields = {"Value": b["value"], "Footprint": b["footprint"]}
            in_bom = not b["exclude_from_bom"]
            for k, bk in zip(SOURCING, ("mpn", "manufacturer", "lcsc")):
                if in_bom or prop(s, k) is not None:
                    fields[k] = b[bk] or ""
            for k, v in fields.items():
                p = prop(s, k)
                if p is None:
                    ref_at = find(prop(s, "Reference"), "at")
                    s.insert(s.index(prop(s, "Reference")) + 1,
                             S("property", k, v, S("at", ref_at[1], ref_at[2], 0), S("hide", True),
                               S("show_name", False), S("do_not_autoplace", False),
                               S("effects", S("font", S("size", 1.27, 1.27)))))
                    stats["added"] += 1
                elif p[2] != v:
                    p[2] = v
                    stats["fields"] += 1
        # embedded library copies: refresh project-library symbols, add missing, drop unused
        have = {n[1]: n for n in findall(libsec, "symbol")}
        new = []
        for lid in sorted(used):
            if lid.split(":", 1)[0] in ("lib", "OpenDrone") or lid not in have:
                emb = lib_symbol(lid).embedded()
                if have.get(lid) != emb:
                    stats["embedded"] += 1
                new.append(emb)
            else:
                new.append(have[lid])
        if set(have) - used:
            stats["embedded"] += len(set(have) - used)
        libsec[1:] = new
    # power / flag references over the whole hierarchy
    power.sort(key=lambda r: (r[0], r[1], r[2]))
    count = {}
    first = {}
    for page, y, x, p, s in power:
        pre = "#FLG" if find(s, "lib_id")[1] == "power:PWR_FLAG" else "#PWR"
        count[pre] = count.get(pre, 0) + 1
        ref = "%s%02d" % (pre, count[pre])
        r = find(p, "reference")
        if r[1] != ref:
            r[1] = ref
            stats["power_refs"] += 1
        first.setdefault(id(s), ref)
        rp = prop(s, "Reference")
        if rp[2] != first[id(s)]:
            rp[2] = first[id(s)]
    print("sch_integrate:", ", ".join("%s %d" % kv for kv in stats.items()),
          "| power symbols #PWR %d, #FLG %d" % (count.get("#PWR", 0), count.get("#FLG", 0)))
    if CHECK:
        return 1 if any(stats.values()) else 0
    for f in files:
        path = os.path.join(HW, f)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(sb.dump(trees[f]) + "\n")
        sb.kicad_resave(path)
    return 0


def _file_of(root, root_uuid, path):
    u = path.rsplit("/", 1)[1]
    for sh in findall(root, "sheet"):
        if find(sh, "uuid")[1] == u:
            return next(p[2] for p in findall(sh, "property") if p[1] == "Sheetfile")
    return None


if __name__ == "__main__":
    sys.exit(main())
