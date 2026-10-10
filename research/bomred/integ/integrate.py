#!/usr/bin/env python3
"""Integrate the four BOM-reduction tracks: apply the confirmed proposals to bom_plan.json and recount
BOM placements, unique MPN lines and area per side (floorplan sides, fpinfo land extents).
Area metrics: 'halo' = land extent + 0.1 mm per side (FLOORPLAN.md 'occupied incl. 0.1 mm halo'),
'pkg' = land extent only (FLOORPLAN.md 'package area')."""
import copy
import itertools
import json
import sys

REPO = "/home/user/OpenAIO-Whoop/hardware"
FPI = "/tmp/claude-0/-home-user/84218be5-e7e2-573d-8ce2-dce426a96e71/scratchpad/p23/fp/work/fpinfo.json"
bp = json.load(open(f"{REPO}/bom_plan.json"))
fpl = {p["ref"]: p for p in json.load(open(f"{REPO}/floorplan.json"))["parts"]}
fi = json.load(open(FPI))

F0201 = "lib:C_0201_0603Metric_W"
F0402 = "lib:C_0402_1005Metric_W"
FDFN3 = "lib:DFN-3L_L1.0-W0.6-P0.65-BR_W"   # AP1606 land; BC857BM (SOT883) reuses it (vtx track V2 note 2)
EXT = {"PICO_7x7": (7.5, 7.5)}              # ESP32-PICO-V3 land about 7.5 mm square (rx-vtx §4)


def ext(fp):
    if fp in EXT:
        return EXT[fp]
    e = fi[fp]["ext"]
    return (e[2] - e[0], e[3] - e[1])


def area(fp, halo):
    w, h = ext(fp)
    return (w + 0.2) * (h + 0.2) if halo else w * h


def base():
    out = []
    for p in bp["parts"]:
        if p["exclude_from_bom"]:
            continue
        out.append(dict(ref=p["ref"], mpn=p["mpn"], fp=p["footprint"], side=fpl[p["ref"]]["side"],
                        block=p["block"], value=p["value"]))
    return out


class S:
    def __init__(self, parts):
        self.p = {q["ref"]: q for q in copy.deepcopy(parts)}

    def rm(self, *refs):
        for r in refs:
            assert r in self.p, r
            del self.p[r]

    def mpn(self, ref, mpn, fp=None, value=None):
        assert ref in self.p, ref
        self.p[ref]["mpn"] = mpn
        if fp:
            self.p[ref]["fp"] = fp
        if value:
            self.p[ref]["value"] = value

    def add(self, ref, mpn, fp, side, value=""):
        assert ref not in self.p, ref
        self.p[ref] = dict(ref=ref, mpn=mpn, fp=fp, side=side, block="new", value=value)

    def move(self, ref, side):
        self.p[ref]["side"] = side

    def stats(self):
        ps = list(self.p.values())
        r = dict(parts=len(ps), lines=len({q["mpn"] for q in ps}))
        for m in ("halo", "pkg"):
            for sd in "FB":
                r[f"{m}_{sd}"] = sum(area(q["fp"], m == "halo") for q in ps if q["side"] == sd)
        return r

    def copy(self):
        n = S([])
        n.p = copy.deepcopy(self.p)
        return n


def corrected(s):
    """Corrected baseline: D24/D34 spec parts not yet in bom_plan + ESP32 CAP1 (PS-00)."""
    s.add("C_VIN1", "GRM155C81A225KE11D", F0402, "B", "2.2uF")     # D24 TPS2116 VIN1
    s.add("R_HYS", "RC0201FR-071M5L", F0201, "B", "1.5M")           # D34 hysteresis
    s.add("C_ENF", "GRM033R61E104KE14D", F0201, "B", "100nF")       # D34 EN filter
    s.add("C_CAP1", "GRM033R61A103KA01J", F0201, "B", "10nF")       # ESP32 CAP1 (Espressif: required)
    s.mpn("R9", "RC0201FR-0790K9L", value="90.9k")                   # D34 value


# ---------------- proposals (functions mutate a state) ----------------
def BR_RV4(s):   # ESP32-PICO-V3 SiP
    s.rm("U17", "C81", "X2", "C71", "C72", "C80", "C74", "C75", "C77", "C78", "C79")
    if "C_CAP1" in s.p:
        s.rm("C_CAP1")
    s.mpn("U16", "ESP32-PICO-V3", fp="PICO_7x7")


def BR_FALLBACK_RX(s):   # no RV-4: PS-09 (C77); CAP1 stays; U17 relocation is placement only
    s.rm("C77")


def BR_PE7(s):
    s.rm("C18", "C24", "C36")


def BR_V2(s):
    s.rm("Q27", "R71", "R72", "R73", "R74", "R75", "R76", "R77", "C124", "C125")
    s.add("Q27n", "BC857BM,315", FDFN3, "F")
    s.add("R71n", "RC0201FR-071KL", F0201, "F")
    s.add("R72n", "RC0201FR-071KL", F0201, "F")
    s.add("C124n", "GRM033R61A105ME44D", F0201, "F")
    s.add("C125n", "GRM033R61A105ME44D", F0201, "F")
    s.add("R75n", "RC0201FR-0710RL", F0201, "F")     # Re 10-15 ohm per verification; 10R = R65 line


def BR_PS12(s):  # fallback drive stage values (fixes F-A)
    s.rm("R73")
    for r in ("R71", "R72", "R74"):
        s.mpn(r, "RC0201FR-073K3L", value="3.3k")
    for c in ("C124", "C125"):
        s.mpn(c, "GRM033R61A105ME44D", value="1uF")
    s.mpn("R75", "RC0201FR-0775RL", value="75R")


def BR_V1(s):
    s.rm("R78", "R79", "R83")
    s.mpn("Q28", "AP1606", fp=FDFN3)


def BR_F1(s):
    s.rm("U23", "C126", "C127")


def BR_PS05(s):
    s.rm("C3", "C4")


def BR_PS08(s):
    s.rm("C90", "C93")


def BR_F2(s):
    s.rm("C55", "C53")


def BR_GYRO(s):
    s.rm("C63", "C64")


def BR_V3(s):
    s.rm("C99")


def BR_V4(s):
    s.rm("C97")


def BR_V5(s):
    s.rm("C119")


def BR_PE1(s):
    s.rm("Q1")


def BR_PE3(s):
    s.rm("R6")


def BR_PS11(s):
    s.rm("R69")


def BR_PS07(s):
    s.rm("C69")
    s.move("C70", "B")


def BR_PS18(s):
    s.rm("C120")
    s.mpn("C13", "GRM155C80J106ME11D", fp=F0402, value="10uF")


def BR_RV1(s):
    s.mpn("U18", "SX1281IMLTRT")


def BR_PS01(s):
    for q in s.p.values():
        if q["mpn"] == "GRM033R61E104KE14D":
            q["mpn"] = "GRM033C81E104KE14D"


def BR_PS02(s):
    for q in s.p.values():
        if q["mpn"] in ("GRM033R61A103KA01J", "GRM033R71C103KA01D"):
            q["mpn"] = "GRM033R71A103KA01D"


def BR_PS03(s):
    for r in ("C18", "C24", "C30", "C36", "C_VIN1"):
        if r in s.p:
            s.mpn(r, "GRM155C80J106ME11D", value="10uF")


def BR_PS17(s):
    s.mpn("R41", "RC0201FR-0727RL", value="27R")


def BR_PS19(s):
    s.mpn("C123", "CL05A475MP5NRNC", fp=F0402, value="4.7uF")


# resistor value options (verified alternatives only)
def r11(s, v):
    if v == "3.3k":
        s.mpn("R11", "RC0201FR-073K3L", value="3.3k")      # PS-16
    elif v == "2.4k":
        s.mpn("R11", "RTT012401FTH", value="2.4k")         # PE-10


def pr1(s, v):
    if v == "3.3k/1.2k":                                   # PS-14
        s.mpn("R7", "RC0201FR-073K3L", value="3.3k")
        s.mpn("R8", "RC0201FR-071K2L", value="1.2k")
    elif v == "49.9k/18k":                                 # PE-12 PR1
        s.mpn("R7", "RC0201FR-0749K9L", value="49.9k")
        s.mpn("R8", "RC0201FR-0718KL", value="18k")


def o4en(s, v):
    if v == "PS-15":
        s.mpn("R9", "RC0201FR-0733KL", value="33k")
        s.mpn("R10", "RC0201FR-0718KL", value="18k")
        s.mpn("R_HYS", "RC0201FR-07510KL", value="510k")


def fb(s, v):
    if v == "47k/6.2k":                                    # PS-13 = PE-12 FB
        s.mpn("R4", "RC0201FR-0747KL", value="47k")
        s.mpn("R5", "RC0201FR-076K2L", value="6.2k")


APPLY = [  # ranked, in application order
    ("BR-01 RV-4", BR_RV4), ("BR-02 V2", BR_V2), ("BR-03 PE-7", BR_PE7), ("BR-04 V1", BR_V1),
    ("BR-05 F1", BR_F1), ("BR-06 PS-05", BR_PS05), ("BR-07 PS-08", BR_PS08), ("BR-08 F2", BR_F2),
    ("BR-09 GYRO", BR_GYRO), ("BR-10 PE-1", BR_PE1), ("BR-11 PE-3", BR_PE3), ("BR-12 PS-11", BR_PS11),
    ("BR-13 PS-07", BR_PS07), ("BR-14 PS-18", BR_PS18), ("BR-15 V3", BR_V3), ("BR-16 V4", BR_V4),
    ("BR-17 V5", BR_V5), ("BR-18 PS-01", BR_PS01), ("BR-19 PS-02", BR_PS02), ("BR-20 PS-03", BR_PS03),
    ("BR-21 PS-17", BR_PS17), ("BR-22 RV-1", BR_RV1), ("BR-23 PS-19", BR_PS19),
]


def fmt(st):
    return (f"parts {st['parts']:3d} lines {st['lines']:3d} | halo F {st['halo_F']:7.2f} B {st['halo_B']:7.2f}"
            f" | pkg F {st['pkg_F']:7.2f} B {st['pkg_B']:7.2f}")


def delta(a, b):
    return {k: round(b[k] - a[k], 2) for k in a}


def build(rx="RV4", drive="V2", vals=None, skip=()):
    s = S(base())
    corrected(s)
    for name, f in APPLY:
        if name in skip:
            continue
        if name.startswith("BR-01") and rx != "RV4":
            BR_FALLBACK_RX(s)
            continue
        if name.startswith("BR-02") and drive != "V2":
            BR_PS12(s)
            continue
        f(s)
    if vals:
        r11(s, vals["r11"]); pr1(s, vals["pr1"]); o4en(s, vals["o4"]); fb(s, vals["fb"])
    return s


def best_vals(rx, drive):
    res = []
    for a, b, c, d in itertools.product(["4.7k", "3.3k", "2.4k"], ["27.4k/10k", "3.3k/1.2k", "49.9k/18k"],
                                        ["D34", "PS-15"], ["909k/120k", "47k/6.2k"]):
        if c == "PS-15" and a == "4.7k":
            continue   # PS-15 clamp was verified with a stronger GPIO27 pull-down (3.3k / 2.4k)
        v = dict(r11=a, pr1=b, o4=c, fb=d)
        st = build(rx, drive, v).stats()
        res.append((st["lines"], v))
    res.sort(key=lambda x: x[0])
    return res


if __name__ == "__main__":
    s0 = S(base()); st0 = s0.stats()
    s1 = S(base()); corrected(s1); st1 = s1.stats()
    print("PLAN      ", fmt(st0))
    print("CORRECTED ", fmt(st1), delta(st0, st1))
    for rx, drive in (("RV4", "V2"), ("RV4", "PS12"), ("FB", "V2"), ("FB", "PS12")):
        r = best_vals(rx, drive)
        print(f"\n== {rx}/{drive}: line-minimal value sets (top 6 of {len(r)})")
        for n, v in r[:6]:
            print("  ", n, v)
    # chosen value set
    V = dict(r11="3.3k", pr1="3.3k/1.2k", o4="PS-15", fb="47k/6.2k")
    print("\nCHOSEN VALUES", V)
    for rx, drive in (("RV4", "V2"), ("RV4", "PS12"), ("FB", "V2"), ("FB", "PS12")):
        st = build(rx, drive, V).stats()
        print(f"AFTER {rx:3s}/{drive:4s}", fmt(st), "vs corrected", delta(st1, st))
    # incremental deltas in rank order (main scenario)
    print("\nINCREMENTAL (RV4/V2, chosen values at the end)")
    s = S(base()); corrected(s); prev = s.stats()
    for name, f in APPLY:
        f(s); cur = s.stats(); dd = delta(prev, cur)
        print(f"  {name:12s} parts {dd['parts']:+d} lines {dd['lines']:+d} halo F {dd['halo_F']:+.2f} B {dd['halo_B']:+.2f}"
              f" pkg F {dd['pkg_F']:+.2f} B {dd['pkg_B']:+.2f}")
        prev = cur
    for nm, fn, arg in (("R11", r11, V["r11"]), ("PR1", pr1, V["pr1"]), ("O4EN", o4en, V["o4"]), ("FB", fb, V["fb"])):
        fn(s, arg); cur = s.stats(); dd = delta(prev, cur)
        print(f"  {nm:12s} parts {dd['parts']:+d} lines {dd['lines']:+d}")
        prev = cur
    print("  FINAL", fmt(s.stats()))
    # standalone deltas vs corrected
    print("\nSTANDALONE vs corrected")
    for name, f in APPLY:
        t = S(base()); corrected(t); a = t.stats(); f(t); b = t.stats(); dd = delta(a, b)
        print(f"  {name:12s} parts {dd['parts']:+d} lines {dd['lines']:+d} halo F {dd['halo_F']:+.2f} B {dd['halo_B']:+.2f}")
    for nm, fn, arg in (("PS-16 R11", r11, "3.3k"), ("PE-10 R11", r11, "2.4k"), ("PS-14 PR1", pr1, "3.3k/1.2k"),
                        ("PE-12 PR1", pr1, "49.9k/18k"), ("PS-15 O4", o4en, "PS-15"), ("PS-13 FB", fb, "47k/6.2k")):
        t = S(base()); corrected(t); a = t.stats(); fn(t, arg); b = t.stats()
        print(f"  {nm:12s} lines {b['lines'] - a['lines']:+d}")
    for nm, f in (("PS-12", BR_PS12), ("PS-09", BR_FALLBACK_RX)):
        t = S(base()); corrected(t); a = t.stats(); f(t); b = t.stats(); dd = delta(a, b)
        print(f"  {nm:12s} parts {dd['parts']:+d} lines {dd['lines']:+d} halo F {dd['halo_F']:+.2f} B {dd['halo_B']:+.2f}")
    # owner calls on top of the main scenario
    print("\nOWNER CALLS (incremental on AFTER RV4/V2)")
    fin = build("RV4", "V2", V); a = fin.stats()

    def pe15(s):
        for q in list(s.p.values()):
            if q["mpn"] == "CSD13202Q2":
                s.rm(q["ref"])
        for q in s.p.values():
            if q["mpn"] == "CSD25310Q2":
                q["mpn"] = "AGM210MAP"

    def rv10(s):
        s.rm("TH1", "R70", "R84")

    def v6(s):
        s.rm("R67")
    allo = fin.copy()
    for nm, f in (("OC-1 PE-15", pe15), ("OC-2 RV-10", rv10), ("OC-3 V6", v6)):
        t = fin.copy(); f(t); dd = delta(a, t.stats())
        print(f"  {nm:12s} parts {dd['parts']:+d} lines {dd['lines']:+d} halo F {dd['halo_F']:+.2f} B {dd['halo_B']:+.2f} (PE-15 area: P2 rerun)")
        f(allo)
    print("  ALL OWNER CALLS", fmt(allo.stats()), "vs corrected", delta(st1, allo.stats()))
    json.dump(dict(plan=st0, corrected=st1, after=build("RV4", "V2", V).stats(),
                   after_fallback=build("FB", "V2", V).stats(), after_all_owner=allo.stats()),
              open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=1)
