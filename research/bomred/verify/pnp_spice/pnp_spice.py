#!/usr/bin/env python3
"""P4-5 SPICE gate for the VTX PA drive stage (D52 BR-02), ngspice 42 + Nexperia BC857BM model (week 19/2020).

Stage: PA_BIAS_PWM (ESP32 GPIO13, 10 kHz, ELRS count/4096) -> R71 1k -> C124 1u -> R72 1k -> C125 1u -> Q27 base;
Q27 emitter -> R73 Re -> +3V3_VTX; collector -> R65 10R -> PAOUT1_SUP (C109 10n) -> L3 4.7n -> PAOUT1.
PAOUT1 load model: internal RTC6705 output stage = current sink with a 0.25 V knee, I = Imax*tanh(V/0.25)
(the datasheet gives the PAOUT1 current as TBD; Imax swept, 95 mA = whole-chip upper bound).
hFE spread: BF scaled so hFE(-5 V, -2 mA, 25 C) = 220 / typ / 475 (datasheet group B limits).
"""
import os, re, subprocess, sys, math, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = open(os.path.join(HERE, "dl", "BC857BM.txt")).read()
VDD = 3.3


def model_bf(scale):
    """BC857BM subckt with BF scaled; subckt renamed per scale."""
    m = MODEL.replace(".SUBCKT BC857BM", ".SUBCKT BC857BM_%d" % int(scale * 1000))
    m = re.sub(r"\+ BF = ([0-9.Ee+-]+)", lambda g: "+ BF = %g" % (float(g.group(1)) * scale), m)
    m = m.replace(".MODEL MAIN PNP", ".MODEL MAIN%d PNP" % int(scale * 1000))
    m = re.sub(r"(Q[12] \S+ \S+ \S+) MAIN ", lambda g: g.group(1) + " MAIN%d " % int(scale * 1000), m)
    m = m.replace(".MODEL DIODE D", ".MODEL DIODE%d D" % int(scale * 1000)).replace("D1 1 2 DIODE",
                                                                                    "D1 1 2 DIODE%d" % int(scale * 1000))
    return m, "BC857BM_%d" % int(scale * 1000)


def run(net):
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False, dir=HERE) as f:
        f.write(net)
        p = f.name
    r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True, timeout=300)
    os.unlink(p)
    return r.stdout + r.stderr


def hfe(scale, temp=25):
    m, name = model_bf(scale)
    fn = os.path.join(HERE, "_hfe.dat")
    run("""* hfe
%s
.temp %g
VC c 0 -5
IB b 0 1u
XQ c b 0 %s
.control
dc IB 0.5u 40u 0.05u
wrdata %s -i(VC)
.endc
.end
""" % (m, temp, name, fn))
    rows = [tuple(float(x) for x in l.split()) for l in open(fn) if l.strip()]
    os.unlink(fn)
    # columns: ib, -i(VC) (collector current flowing out of the collector into VC is +i(VC) -> sign either way)
    best = min(rows, key=lambda r: abs(abs(r[1]) - 2e-3))
    return abs(best[1]) / best[0]


STAGE = """
VDD vdd 0 {vdd}
RE vdd e {re}
XQ c b e {q}
R65 c sup 10
C109 sup 0 10n
L3 sup pa 4.7n
BLOAD pa 0 I = {imax}*tanh(v(pa)/0.25)
RLEAK pa 0 100k
R71 pwm n1 1k
C124 n1 0 {cfx}
R72 n1 b 1k
C125 b 0 {cfx}
"""


def dc_sweep(re_, scale, temp, imax, counts):
    """Averaged-PWM DC: Vpwm = 3.3*duty, duty = int(count*1000/4096)/1000 (ELRS setDuty)."""
    m, name = model_bf(scale)
    lines = ["* dc", m, ".temp %g" % temp,
             STAGE.format(vdd=VDD, re=re_, q=name, imax=imax, cfx="1u"),
             "VPWM pwm 0 0", ".control"]
    for c in counts:
        d = (c * 1000 // 4096) / 1000.0
        lines += ["alter VPWM %g" % (VDD * d), "op", "echo @@%d" % c,
                  "print -i(VDD) v(pa) v(e)-v(c) v(e)-v(b)"]
    lines += [".endc", ".end"]
    out = run("\n".join(lines))
    res = {}
    for blk in out.split("@@")[1:]:
        c = int(blk.split()[0])
        try:
            g = lambda k: float(re.search(k + r" = ([-0-9.eE+]+)", blk).group(1))
            res[c] = (g(r"-i\(vdd\)"), g(r"v\(pa\)"), g(r"v\(e\)-v\(c\)"), g(r"v\(e\)-v\(b\)"))
        except AttributeError:
            pass
    return res


def main():
    out = []
    pr = lambda *a: (print(*a), out.append(" ".join(str(x) for x in a)))
    h_typ = hfe(1.0)
    s_lo, s_hi = 220.0 / h_typ, 475.0 / h_typ
    pr("model hFE(-5V,-2mA,25C) = %.1f; BF scale for hFE 220 / 475: %.3f / %.3f" % (h_typ, s_lo, s_hi))
    pr("hFE check: lo %.0f hi %.0f; at 85 C typ %.0f, at -20 C typ %.0f" %
       (hfe(s_lo), hfe(s_hi), hfe(1.0, 85), hfe(1.0, -20)))
    counts = list(range(2000, 3701, 4))
    # 1. YOLO ceiling + pinch-off, PNP-limited (Imax 95 mA = chip upper bound, so the PNP sets the current)
    pr("\n1. Ic (mA) vs ELRS count, PAOUT1 sink Imax 95 mA (PNP-limited)")
    pr("Re  hFE   T   | 2000  2500  3000  3133  3263  3300  3400  3500  3700 | pinch(<0.1mA) | P_Q max mW")
    table = {}
    for re_ in (10, 15, 27, 47):
        for sc, hl in ((s_lo, 220), (s_hi, 475)):
            for t in (-20, 25, 85):
                r = dc_sweep(re_, sc, t, 0.095, counts)
                table[(re_, hl, t)] = r
                ic = {c: r[c][0] * 1e3 for c in r}
                pinch = min((c for c in counts if ic[c] < 0.1), default=None)
                pq = max(r[c][0] * r[c][2] for c in r) * 1e3
                near = lambda k: ic[min(ic, key=lambda c: abs(c - k))]
                pr("%2d  %3d %4d  | %s | %s | %.0f" % (re_, hl, t, " ".join("%5.1f" % near(k) for k in
                   (2000, 2500, 3000, 3133, 3263, 3300, 3400, 3500, 3700)), pinch, pq))
    # 2. steps per 6 dB (I^2 law: P ~ Idc^2) at a given 25 mW current I25 -> count(I25) - count(2*I25), /4.096
    pr("\n2. real duty steps (0.1 %% each) between I25 and 2*I25 (6 dB, Pout ~ Idc^2), 25 C, PNP-limited")
    pr("Re  hFE | I25=0.5mA  1mA   2mA   4mA   8mA")
    for re_ in (10, 15, 27, 47):
        for hl in (220, 475):
            r = table[(re_, hl, 25)]
            ic = sorted(((c, r[c][0]) for c in counts), key=lambda x: x[0])

            def cnt_at(i):  # highest count where Ic >= i (Ic falls with count)
                cc = [c for c, x in ic if x >= i]
                return max(cc) if cc else None
            row = []
            for i25 in (0.5e-3, 1e-3, 2e-3, 4e-3, 8e-3):
                a, b = cnt_at(i25), cnt_at(2 * i25)
                row.append("%5s" % ("%.0f" % ((a - b) * 1000 / 4096) if a and b else "-"))
            pr("%2d  %3d | %s" % (re_, hl, "  ".join(row)))
    # 3. PAOUT1-limited case: sink wants only 10 mA -> PNP saturates at YOLO; check Vce, base current, PAOUT1 V
    pr("\n3. PAOUT1 sink Imax 10 mA (stage wants less than the PNP ceiling): YOLO count 2000")
    for re_ in (10, 47):
        for sc, hl in ((s_lo, 220), (s_hi, 475)):
            r = dc_sweep(re_, sc, 25, 0.010, [2000, 3000])
            pr("Re %2d hFE %3d: count 2000 Ie %.1f mA V(PAOUT1) %.2f V Vec %.2f V; count 3000 Ie %.1f mA V(PAOUT1) %.2f V"
               % (re_, hl, r[2000][0] * 1e3, r[2000][1], r[2000][2], r[3000][0] * 1e3, r[3000][1]))
    # 4. reset / boot (GPIO13 undriven) and HD mode
    pr("\n4. GPIO13 undriven at reset (Imax 95 mA, 25 C)")
    for re_ in (10, 47):
        for sc, hl in ((s_lo, 220), (s_hi, 475)):
            for rpull, lab in (("1G", "floating (1 GOhm)"), ("45k", "45 kOhm pull-down")):
                m, name = model_bf(sc)
                net = "\n".join(["* reset", m, ".temp 25", STAGE.format(vdd=VDD, re=re_, q=name, imax=0.095, cfx="1u"),
                                 "RPD pwm 0 %s" % rpull, ".control", "op", "print -i(VDD) v(b)", ".endc", ".end"])
                o = run(net)
                i = float(re.findall(r"-i\(vdd\) = ([-0-9.eE+]+)", o)[-1])
                pr("Re %2d hFE %3d %-18s: Ic %.2f mA" % (re_, hl, lab, i * 1e3))
    pr("\n5. HD mode: +3V3_VTX = 0 V, GPIO13 high 3.3 V, RTC6705 unpowered (PAOUT1 0 V)")
    for sc, hl in ((s_lo, 220), (s_hi, 475)):
        for t in (25, 85):
            m, name = model_bf(sc)
            net = "\n".join(["* hd", m, ".temp %g" % t,
                             STAGE.format(vdd=0, re=10, q=name, imax=0.0, cfx="1u").replace(
                                 "BLOAD pa 0 I = 0.0*tanh(v(pa)/0.25)", "RPA pa 0 1k"),
                             "VPWM pwm 0 3.3", ".control", "op", "print i(VPWM)", "print (-i(VDD))", "print v(e)-v(b)", "print v(c)-v(b)", ".endc", ".end"])
            o = run(net)
            ip = float(re.findall(r"i\(vpwm\) = ([-0-9.eE+]+)", o)[-1])
            ir = float(re.findall(r"\(-i\(vdd\)\) = ([-0-9.eE+]+)", o)[-1])
            veb = float(re.findall(r"v\(e\)-v\(b\) = ([-0-9.eE+]+)", o)[-1])
            vcb = float(re.findall(r"v\(c\)-v\(b\) = ([-0-9.eE+]+)", o)[-1])
            pr("hFE %3d %2d C: GPIO13 current %.2e A, into the rail %.2e A, Veb %.2f V (VEBO -5 V), Vcb %.2f V"
               % (hl, t, -ip, ir, veb, vcb))
    # 6. ripple: transient 10 kHz PWM at 3133 counts (about the 100 mW calibration point), Re 10, typ hFE
    pr("\n6. 10 kHz PWM ripple at count 3133 (76.4 %), Re 10, hFE typ, C124/C125 at 0.6 uF (DC bias)")
    m, name = model_bf(1.0)
    d = (3133 * 1000 // 4096) / 1000.0
    net = "\n".join(["* ripple", m, ".temp 25", STAGE.format(vdd=VDD, re=10, q=name, imax=0.095, cfx="0.6u"),
                     "VPWM pwm 0 PULSE(0 3.3 0 10n 10n %gu 100u)" % (100 * d - 0.02),
                     ".tran 1u 200m 150m 1u", ".control", "run",
                     "meas tran ibmin MIN i(VDD) from=150m to=200m", "meas tran ibmax MAX i(VDD) from=150m to=200m",
                     "meas tran vbmin MIN v(b) from=150m to=200m", "meas tran vbmax MAX v(b) from=150m to=200m",
                     ".endc", ".end"])
    o = run(net)
    g = lambda k: float(re.findall(k + r"\s*=\s*([-0-9.eE+]+)", o)[-1])
    imax, imin = -g("ibmin"), -g("ibmax")
    pr("Ic %.2f..%.2f mA (ripple %.2f %% p-p), base %.4f..%.4f V (%.2f mV p-p)" %
       (imin * 1e3, imax * 1e3, 100 * (imax - imin) / ((imax + imin) / 2), g("vbmin"), g("vbmax"),
        1e3 * (g("vbmax") - g("vbmin"))))
    # step response (averaged PWM): pit 3700 -> 3133, 99 % settling of Ic
    fn = os.path.join(HERE, "_step.dat")
    net = "\n".join(["* step", m, ".temp 25", STAGE.format(vdd=VDD, re=10, q=name, imax=0.095, cfx="0.6u"),
                     "VPWM pwm 0 PWL(0 %g 1m %g 1.0001m %g)" % (3.3 * 0.903, 3.3 * 0.903, 3.3 * d),
                     ".tran 10u 60m 0 10u", ".control", "run", "wrdata %s (-i(VDD))" % fn, ".endc", ".end"])
    run(net)
    rows = [tuple(float(x) for x in l.split()[:2]) for l in open(fn) if l.strip()]
    os.unlink(fn)
    fin = rows[-1][1]
    t99 = max(t for t, i in rows if abs(i - fin) > 0.01 * fin)
    pr("averaged step pit (3700) -> 3133: final %.2f mA, within 1 %% after %.1f ms" % (fin * 1e3, (t99 - 1e-3) * 1e3))
    open(os.path.join(HERE, "pnp_spice.out.txt"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
