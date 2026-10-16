# BOM reduction, track: passive standardisation and lean decoupling

Date 2026-10-09. Read-only study. No repo file was edited.
Inputs: `hardware/bom_plan.json` (329 entries, 282 BOM parts), `hardware/floorplan.json` (P2 positions and sides),
`research/DESIGN-SPEC.md`, `PINMAP.md`, `FLOORPLAN.md`, `LIBRARY.md`, `DECISIONS.md`, the CONTEXT owner rules
(lean rule D11, density rule D33, 0201 default, 0201 R = 25 V / 50 mW, DC bias from maker data).
Status marks: **V** = read from a primary source (datasheet, sibling netlist, firmware source); **S** = secondary
(distributor listing); **I** = inferred or calculated here.

Scripts (scratchpad, reproducible): `bomred/work/inv.py` (inventory), `bomred/work/apply.py` (applies the
proposals, recounts, computes area), `bomred/work/rset.py` (resistor value-set search). Sibling BOMs and netlists
exported with kicad-cli into `bomred/sib/`. Datasheet text extracted into `bomred/dl/`.

Area method: floorplan land extents plus the 0.2 mm body rule, as the P2 kernel measures them (LIBRARY.md
`_W` lands): 0201 (0.90 + 0.2) x (0.40 + 0.2) = **0.66 mm²**, 0402 (1.30 + 0.2) x (0.55 + 0.2) = **1.125 mm²**,
0603 (2.10 + 0.2) x (0.80 + 0.2) = **2.30 mm²**. Sides come from `floorplan.json`, not the bom_plan side. A removed
decoupling capacitor usually also frees one far-side via landing (about 0.28 mm² on the other side, spec §9.2).
That saving is not counted below.

---

## 0. Result

| | Passive placements | Passive lines (unique MPN) | Board BOM lines |
|---|---|---|---|
| `bom_plan.json` today | 218 | 52 | 88 |
| Corrected baseline: plan plus the 3 round-4 spec parts not yet in the plan plus the missing ESP32 CAP1 capacitor (§2) | 222 | 53 | 89 |
| **After the recommended set (PS-01 to PS-19)** | **209 (−13)** | **43 (−10)** | **79** |
| After the optional line merges PS-O1 and PS-O2 as well | 209 | 41 | 77 |

Area of the recommended set against the corrected baseline: **top −3.5 mm², bottom −4.6 mm²** (−8.1 mm² in
total), plus about 10 freed far-side via landings. Against the Matrix II reconstruction (01 §5.2: about 215-265
passives) the board stays at the low end, with the same function and ratings.

Things this pass found besides savings (details in §2):

1. **ESP32 CAP1 is missing.** Espressif says the 10 nF on CAP1 (pin 48) "is required for proper operation of
   ESP32". bom_plan, the spec and PINMAP have no capacitor there. The CAP2 RC (3.3 nF ∥ 20 kΩ) is optional:
   Espressif says it is only for Deep-sleep.
2. **The PA drive-stage start values cannot turn Q1 on.** The 36 kΩ of RC resistance sits in series with the
   16.2 kΩ base divider, so Vb = 0.119·V_PWM,avg, at most 0.39 V at 100 % duty. The PA would stay at maximum
   drive and ELRS would have no power control. PS-12 gives values that work, all from the standard set.
3. **The +3V3 rail carries more output capacitance than the LP5912 allows.** The LP5912 allows COUT 0.7-10 µF
   (DS §7.6). The rail sums to about 31 µF nominal, about 15 µF effective (I). PS-08 brings it to about 21 µF
   nominal, 10-11 µF effective. P4 must check the sum with maker curves (§7).
4. **Some LDO capacitors in 0201 fall below the effective minimum.**
   - LP5907 COUT C123 (0201 1 µF X5R at 2.85 V): the datasheet asks > 0.7 µF over all conditions. Fixed by PS-19.
   - LP5912 CIN C13 / C120 (0201 1 µF at 5.15 V): the datasheet asks > 0.5 µF. Fixed by PS-18.
5. bom_plan lags the spec on four items: the D24 VIN1 capacitor, the D34 1.5 MΩ, the D34 100 nF EN filter, and
   R9 = 90.9 kΩ (the plan has 80.6 kΩ).

### Proposals at a glance

Deltas are against the corrected baseline. Area is in mm²; negative means saved.

| ID | Change | Parts | Lines | Area T / B | Rec. |
|---|---|---|---|---|---|
| PS-00 | Baseline fixes: add ESP32 CAP1 10 nF; add the D24 / D34 spec parts | +4 vs plan | +1 vs plan | 0 / +3.1 | yes (fix) |
| PS-01 | One 100 nF line: all GRM033R61E104KE14D → GRM033C81E104KE14D (X6S 25 V) | 0 | −1 | 0 | yes |
| PS-02 | One 10 nF line: GRM033R61A103KA01J → GRM033R71C103KA01D (X7R 16 V) | 0 | −1 | 0 | yes |
| PS-03 | Retire the 2.2 µF line: EFM8 VDD → GRM155C80J106ME11D 10 µF X6S 0402; VIN1 → CL05A475MP5NRNC | 0 | −1 | 0 | yes |
| PS-04 | RP2354A: pins 53 and 54 share one 100 nF (drop C55) | −1 | 0 | 0 / −0.66 | yes |
| PS-05 | INA186: drop the common-mode input caps C3 and C4 | −2 | 0 | 0 / −1.32 | yes |
| PS-06 | Gyro: LDO COUT at VDD and CIN at VDDIO; drop C63 and C64 | −2 | 0 | −1.32 / 0 | yes, with placement condition |
| PS-07 | OSD: one 100 nF for U14 + U15 (drop C69, move C70 to the bottom) | −1 | 0 | −1.32 / +0.66 | yes |
| PS-08 | SX1280: drop C90 (10 nF) and C93 (10 µF); the Semtech minimum set stays | −2 | 0 | 0 / −1.79 | yes |
| PS-09 | ESP32: drop C77 (VDD3P3 10 nF); no LC filter, no CAP2 RC (no Wi-Fi TX, no Deep-sleep) | −1 | 0 | 0 / −0.66 | yes |
| PS-10 | TPS61022 EN tied to VIN (drop R6) | −1 | 0 | 0 / −0.66 | yes |
| PS-11 | Drop the PA_EN pull-down R69 (LP5907 has 1 MΩ inside; ESP32 GPIO2 45 kΩ strap pull-down) | −1 | 0 | −0.66 / 0 | yes |
| PS-12 | PA drive stage re-derived (fixes the bias error): 3.3k / 1 µF / 3.3k / 1 µF / 3.3k, R73 omitted, Re 75R | −1 | 0 (−1 without PS-15) | −0.66 / 0 | yes |
| PS-13 | Boost FB 909k / 120k → 47k / 6.2k (5.148 V) | 0 | −2 | 0 | yes |
| PS-14 | PR1 divider 27.4k / 10k → 3.3k / 1.2k (3.45-4.05 V) | 0 | −1 | 0 | yes |
| PS-15 | O4 EN network 33k / 18k / 510k instead of 90.9k / 49.9k / 1.5M | 0 | −2 | 0 | yes |
| PS-16 | HD_EN pull-down R11 4.7k → 3.3k | 0 | −1 | 0 | yes |
| PS-17 | VREG_AVDD R41 30R → 27R (shares the USB 27R line) | 0 | −1 | 0 | yes |
| PS-18 | One 4.7 µF 0402 shared by both LP5912 inputs instead of 2x 0201 1 µF (CIN compliance) | −1 | 0 | 0 / −0.20 | yes |
| PS-19 | LP5907 COUT C123 0201 1 µF → 0402 4.7 µF (COUT compliance) | 0 | 0 | +0.47 / 0 | yes (fix) |
| **Sum PS-01 to PS-19** | | **−13** | **−10** | **−3.50 / −4.62** | |
| PS-O1 | OSD level R54 287R → 270R (levels −1 to −5 %) | 0 | −1 | 0 | P4-10 decides |
| PS-O2 | Pad bulk CL10A226MO7JZNC → GRM188C80J226ME15D (only together with PS-03) | 0 | −1 | 0 | optional |
| PS-O3 | PA VCC selector R67 → fixed +BATT copper after V5 (production only) | −1 | −1 | about −1.5 / 0 | after V5 |
| PS-O4 to PS-O8 | Beeper pull-down, GPIO21 series R, radio 1 µF, BEMF resistor arrays, gyro CS pull-up | see §5 | | | no |

---

## 1. Inventory today (bom_plan.json, BOM parts only)

218 passive placements on 52 lines: 127 capacitors, 86 resistors (incl. the shunt and the 0R selector), 4
inductors / ferrite, 1 NTC.

- **By package:** 0201: 186 (100 C, 83 R, 2 L, 1 NTC). 0402: 18 (16 C, 51R, 0R selector). 0603: 11. Plus the
  1206 Kelvin shunt, the 2520 and 2016 inductors.
- **By block:** VTX 61, power 30, FC 29, RX 25, ESC 4 x 13, OSD 10, IMU 5, LED 4, blackbox 2.
- **By side (floorplan):** bottom 116, top 102.

### 1.1 Capacitors (18 lines)

| Value | Pkg | V / dielectric | MPN | Qty | Refs | Use |
|---|---|---|---|---|---|---|
| 100 nF | 0201 | 25 V X5R | GRM033R61E104KE14D | 41 | C3,C4,C6,C44-C55,C59,C60,C63-C65,C69,C70,C74-C76,C78,C79,C81,C83,C85,C89,C91,C97-C101,C124-C127 | general decoupling |
| 100 nF | 0201 | 25 V X6S | GRM033C81E104KE14D | 16 | C19-C22,C25-C28,C31-C34,C37-C40 | EFM8 VDD, leg caps |
| 10 nF | 0201 | 16 V X7R | GRM033R71C103KA01D | 1 | C16 | TPS22810 CT |
| 10 nF | 0201 | 10 V X5R | GRM033R61A103KA01J | 5 | C77,C86,C88,C90,C109 | RF HF bypass |
| 1 nF | 0201 | 50 V X7R | GRM033R71H102KA12D | 4 | C84,C112,C114,C116 | TCXO coupling, PA EK1 |
| 470 nF | 0201 | 6.3 V X5R | GRM033R60J474KE90D | 2 | C87,C96 | SX1280 VREG, RTC6705 REG1D8_1 |
| 470 pF | 0201 | 16 V X7R | CC0201JRX7R9BB471 | 1 | C67 | sync filter |
| 100 pF | 0201 | 50 V C0G | GRM0335C1H101JA01D | 7 | C66,C102,C103,C111,C113,C115,C117 | RF / video |
| 33 pF | 0201 | 50 V C0G | GRM0335C1H330JA01D | 1 | C104 | video network |
| 15 pF | 0201 | 50 V C0G | GRM0335C1H150JA01D | 6 | C42,C43,C71,C72,C94,C95 | crystal loads |
| 10 pF | 0201 | 50 V C0G | GRM0335C1H100JA01D | 2 | C110,C119 | PA DC blocks |
| 1 µF | 0201 | 10 V X5R | GRM033R61A105ME44D | 14 | C5,C13,C14,C17,C61,C62,C68,C73,C80,C92,C120-C123 | LDO in/out, misc |
| 1 µF | 0402 | 25 V X5R | CL05A105KA5NQNC | 1 | C106 | RTC6705 loop filter |
| 2.2 µF | 0402 | 10 V X6S | GRM155C81A225KE11D | 4 | C18,C24,C30,C36 | EFM8 VDD bulk |
| 4.7 µF | 0402 | 10 V X5R | CL05A475MP5NRNC | 5 | C56-C58,C105,C107 | RP2354A VREG, video coupling, loop filter |
| 10 µF | 0402 | 6.3 V X6S | GRM155C80J106ME11D | 6 | C12,C15,C82,C93,C108,C118 | rail bulk |
| 22 µF | 0603 | 16 V X5R | CL10A226MO7JZNC | 2 | C1,C2 | pad bulk |
| 22 µF | 0603 | 6.3 V X6S | GRM188C80J226ME15D | 9 | C7-C11,C23,C29,C35,C41 | boost, ESC bulk |

### 1.2 Resistors (29 lines incl. shunt; all Yageo RC0201FR-07 except as noted)

| Value | Qty | Refs | Value | Qty | Refs |
|---|---|---|---|---|---|
| 0R 0402 (RC0402JR-070RL) | 1 | R67 | 2.4k (Ralec RTT012401FTH) | 5 | R12,R19,R26,R33,R53 |
| 10R | 1 | R65 | 3.3k | 1 | R77 |
| 27R | 2 | R42,R43 | 4.7k | 1 | R11 |
| 30R | 1 | R41 | 6.2k | 1 | R74 |
| 51R 0402 (RC0402FR-0751RL) | 1 | R57 | 10k | 24 | R8,R13-R15,R20-R22,R27-R29,R34-R36,R45,R46,R49,R50,R56,R69,R70,R73,R78,R79,R84 |
| 75R | 1 | R51 | 18k | 2 | R71,R72 |
| 150R | 3 | R75,R85,R86 | 27.4k | 1 | R7 |
| 270R | 1 | R59 | 47k | 1 | R64 |
| 287R | 1 | R54 | 49.9k | 1 | R10 |
| 680R | 1 | R55 | 80.6k | 1 | R9 |
| 820R | 1 | R52 | 100k | 4 | R6,R48,R63,R68 |
| 1k | 23 | R2,R3,R16-R18,R23-R25,R30-R32,R37-R40,R44,R47,R66,R76,R80-R83 | 120k | 1 | R5 |
| 1.2k | 2 | R58,R60 | 510k / 560k / 909k | 1 / 1 / 1 | R61 / R62 / R4 |
| shunt HCS1206FTL500 | 1 | R1 | | | |

Other lines: FTC252012SR68MBCA (L1), AOTA-B201610S3R3-101-T (L2), LQP03TN4N7H02D (L3), BLM03PX121SN1D (FB1),
NCP03XH103F05RL (TH1).

### 1.3 Observations

- **100 nF** is split into an X5R and an X6S line. The X6S line is already required in the ESC quarters and at
  the PA (spec §4 temperature table), so the X5R line adds nothing.
- **10 nF** is split into X7R (CT only) and X5R (RF).
- **The 2.2 µF line serves only the EFM8.** Its 0402 land equals the 10 µF line's land.
- **Twelve resistor values are used once.** Six of them belong to dividers whose ratio, not the values,
  matters: FB 909k / 120k, PR1 27.4k, O4 EN 80.6k / 49.9k, HD pull-down 4.7k.
- **Everything that ratings allow is already 0201** (§5.1). Nothing is left to move.
- **Several decoupling caps are far from their pins** (FLOORPLAN.md item 10 and `floorplan.json`):
  - C69 / C70 sit on the top, 4.2 / 6.5 mm from U14 / U15 on the bottom;
  - C62 sits 5.3 mm from the gyro;
  - C89 / C90 sit 3.5 / 4.1 mm from the SX1280.

  Removing duplicates frees room to pull the remaining caps in, which is a quality gain as well as an area gain.

---

## 2. Corrected baseline (required before any saving is counted)

| Item | Status | Evidence |
|---|---|---|
| **ESP32 CAP1 10 nF missing** (pin 48 to GND, 10 % tolerance) | **V, missing** | ESP32 DS v5.3 Table 2-1, pins 47/48: "CAP1 … connects to a 10 nF series capacitor to ground"; Espressif ESP32 schematic checklist, "External Capacitor": "C5 (10 nF) that connects to CAP1 should be of 10% tolerance and is **required for proper operation of ESP32**"; the RC between CAP1 and CAP2 "may be omitted … If particular application of ESP32 is not using Deep-sleep mode … this circuit is not required". ELRS never deep-sleeps, so add only the 10 nF (the GRM033R71C103KA01D line after PS-02). +1 part, 0 lines. Not needed if the RX track moves to an SiP or ESP32-C3 without CAP pins. |
| TPS2116 VIN1 capacitor (D24) | in spec, not in plan | spec §4.2 parts table: GRM155C81A225KE11D 2.2 µF. PS-03 puts it on the 4.7 µF line |
| O4 EN 1.5 MΩ hysteresis + 100 nF filter (D34) | in spec, not in plan | spec §4.2, DECISIONS D34. PS-15 replaces the values |
| R9 = 90.9 kΩ (D34); plan still has 80.6 kΩ | in spec, plan stale | spec §4.2 |

Corrected baseline: 222 placements, 53 lines (adds the 1.5 MΩ line; 90.9k replaces 80.6k).

### 2.1 Circuit findings made while standardising (they also change values)

**F-A: the PA drive-stage start values never turn Q1 on.** (V netlist in bom_plan, I calculation.)

- Path: R71 18k → C124 100 nF → R72 18k → C125 100 nF → R73 10k → Q1_B, with R74 6.2k to GND.
- At DC: Vb = V_avg · 6.2 / (18 + 18 + 10 + 6.2) = **0.119 · V_avg**. That gives 0.19 V at the YOLO duty (49 %),
  0.35 V at pit (90 %) and 0.39 V at 100 %.
- Q1 never conducts, so PAOUT1 sits at the collector-divider ceiling all the time and the VPD loop has no
  authority.
- Cause: spec §4.8 sized the base divider against an unloaded RC node.
- PS-12 fixes it.

**F-B: the +3V3 LP5912 output capacitance is over the datasheet maximum.**

- LP5912 DS §7.6 "Output and Input Capacitors": COUT 0.7 min / 1 typ / **10 max µF**, ESR 5-500 mΩ. Table
  9-1 also says "Output capacitor 1 to 10 µF".
- The +3V3 rail today:

  | Caps | Nominal |
  |---|---|
  | C14 1 µF | 1 µF |
  | 22 x 100 nF | 2.2 µF |
  | C58 4.7 µF | 4.7 µF |
  | C61, C92, C122 1 µF | 3 µF |
  | C82, C93 10 µF | 20 µF |
  | **Total** | **31 µF nominal**, about 15 µF effective at 3.3 V (I) |

  C57 4.7 µF sits behind R41 (30 Ω) and is decoupled at loop frequencies.
- After PS-04/05/06/07/08/09 the rail is about 21 µF nominal, **about 10-11 µF effective (I)**, still at the
  limit.
- P4 sums it with maker curves. If it is still over:
  - apply PS-O6 (C92); or
  - the regulator track swaps U4 to **TI TLV75533PDRVR**. It has the same WSON-6 2x2 body and COUT 1-200 µF
    (V, TLV755P DS §6.3 and orderable addendum). The house part is TLV75533PDQNR [PU]. The track must recheck
    noise and PSRR against the LP5912.
- The +3V3_VTX LP5912 is inside the range: C121 1 µF + C108 10 µF + 4 x 100 nF is about 5.5 µF effective (I).

**F-C: the LP5907 COUT is below its effective minimum.**

- LP5907 DS §5.6 note 1: "The minimum capacitance must be greater than 0.7µF over the full range of operating
  conditions", with tolerance ≤ 30 % (V).
- C123 is GRM033R61A105ME44D (0201, 10 V X5R, ±20 %). At 2.85 V it gives about 0.6-0.7 µF typical and about
  0.45-0.55 µF after tolerance and temperature (I). It fails.
- PS-19 fixes it.

**F-D: the LP5912 input caps are below their effective minimum.**

- LP5912 DS §7.6 note 1 asks "> 0.5 µF over full range" (V).
- C13 and C120 (0201 1 µF X5R 10 V) at 5.15 V give about 0.4 µF typical (I).
- PS-18 fixes it.

**F-E (note for the RX track): the RGB LED runs below its rated supply.**

- XL-1010RGBC-2812B datasheet: chip supply 3.5-5.5 V (V, `p23/merge/od/txt/XL-1010RGBC-WS2812B.txt` l. 203).
- D4 runs from +3V3, inherited from OpenRX-Lite-UFL, where the same LED also sits on +3V3 (V, sibling netlist)
  and flies.
- This is not a passive item; it is recorded so the RX track decides it.

---

## 3. Decoupling per IC: plan against datasheet minimum and comparable boards

House = OpenDrone sibling netlists exported with kicad-cli (OpenFC-Lite-Mini, OpenRX-Lite-UFL, OpenAIO,
OpenESC-20x20). Matrix II = the photo reconstruction in research 01 §5.2 (ESC about 17-20 passives per channel,
RTC6705 about 20, ESP8285 + SX1281 about 30, PA about 12; I).

| IC | Plan | Datasheet minimum (V) | House / Matrix | Verdict |
|---|---|---|---|---|
| **EFM8BB51** x4 | 2.2 µF 0402 + 100 nF X6S per MCU | DS Rev 1.0 §5.1 Fig 5.1: "1 µF and 0.1 µF bypass capacitors required … as close to the pins as possible" | Matrix about 17-20 passives per channel (this board 13) | keep both; 2.2 µF → 10 µF line (PS-03) |
| ESC power stage x4 | 3 leg caps 100 nF + 22 µF bulk | spec §4.3 loop; Matrix has more 0603 bulk per FET group (photo) | Matrix more | keep |
| **RP2354A** | 12 x 100 nF + 3 x 4.7 µF + 30 Ω | RPi "Hardware design with RP2350" §2.2.1: "100 nF capacitor per power pin … pins 53 and 54 of RP2350A … share a single capacitor (C12)"; §2.1: C6, C7, C9 4.7 µF, R3 33 Ω | OpenFC-Lite-Mini (flown): 9 x 100 nF + 4 x 4.7 µF, 30 Ω | **−1** (PS-04) |
| **TPS61022** | Cin 1 x 22 µF, Cout 4 x 22 µF | DS §6.3: CIN ≥ 4.7 µF effective; COUT ≥ 20 µF effective for 1.5-3 A, ≥ 10 µF for ≤ 1.5 A; Fig 8-1 TI example 10 µF / 3 x 22 µF | - | keep (D15: HD load 1.43-1.48 A plus transients) |
| **TPS2116** | (spec: 2.2 µF VIN1) + C12 10 µF OUT | DS §9: "CIN of 1 μF is sufficient" | - | VIN1 on the 4.7 µF line (PS-03); keep C12 (switchover hold-up) |
| **TPS22810** | CT 10 nF + CIN 1 µF | DS §6.3 CIN 1 µF; §10.3 "1-μF … usually sufficient"; §9.3.4 CT pin ≤ 2.5 V | - | keep; CT on the X7R 10 nF line (PS-02) |
| **LP5912** (+3V3) | 1 µF in + 1 µF out | CIN ≥ 0.7, COUT 0.7-**10** µF, > 0.5 µF effective (§7.6) | - | CIN fix (PS-18); rail COUT sum over the maximum (F-B, PS-08) |
| **LP5912** (+3V3_VTX) | 1 µF in + 1 µF out + 10 µF at the RTC6705 | same | - | CIN shared with U4 (PS-18) |
| **LP5907** (PA_VREF) | 1 µF in + 1 µF out + 10k EN pull-down | CIN / COUT > 0.7 µF effective (§5.6); EN has an internal 1 MΩ pull-down (pin table, note 10) | - | COUT fix (PS-19); drop R69 (PS-11) |
| **TPS7A2018** | 1 µF in + 1 µF out | CIN 1 µF; COUT 0.47-200 µF effective (§6.3 note 3) | house LP5912-1.8 with 22 µF out | PS-06 shares these with the gyro pins |
| **BMI270** | 100 nF VDD + 100 nF VDDIO | DS BST-BMI270-DS000-08 §7.2: "It is recommended to use 100nF decoupling capacitors at pin 5 (VDDIO) and pin 8 (VDD)" | house 100 nF + 100 nF | 1 µF LDO caps at the pins meet it (PS-06) |
| **INA186A3** | 2 x 1k + 2 x 100 nF CM + 1 µF diff + 100 nF VS + 1k / 100 nF out | SBOS318B §8.1.3 Fig 8-2: 2 x RF + one differential CF + CBYPASS 0.1 µF; "If high-frequency, common-mode noise is a concern, add an RC filter from the OUT pin to ground"; Fig 8-1 note A: filter the output for a SAR ADC; capacitive load ≤ 1 nF | house OpenAIO root has the CM caps | **−2** (PS-05); keep the output RC |
| **W25Q128JV** | 100 nF + 10k /CS pull-up | /CS "must track the VCC supply level at power-up … If needed a pull-up resister on /CS can be used" (§4.1, §7.x) | house same | keep |
| **SN74LVC1G3157 + TLV7031** | 100 nF each | TLV7031 DS §7.4.1: 100 nF "when supply output impedance is high, supply traces are long, or when excessive noise is expected" | house 3 caps for 3 parts | **−1**, one shared at 2.5 mm (PS-07) |
| **74LVC1T45** | 100 nF VCCA + 100 nF VCCB | 0.1 µF per supply (usual practice) | - | keep (or drop the translator, cross-track §6) |
| **ESP32-D0WD-V3** | 5 x 100 nF + 10 nF + 1 µF VDD_SDIO + 10 µF + CHIP_PU 10k / 1 µF; **no CAP1** | Espressif checklist: 0.1 µF at digital pins; VDD3P3 "highly recommended to add a 10 μF capacitor"; "add an LC circuit to the VDD3P3 power rail to suppress high-frequency harmonics"; VDD_SDIO 3.3 V mode 1 µF; CHIP_PU R 10 kΩ, C 1 µF; **CAP1 10 nF required** | OpenRX-Lite-UFL (C3): 7 x 100 nF, 3 x 1 µF, 2 x 10 µF, LC 2.0 nH + 1 µF on VDD3P3 | +CAP1 (PS-00), −C77 (PS-09); LC filter omitted: no Wi-Fi radiator (D25), so no TX harmonics to suppress |
| **GD25Q32** | 100 nF | 0.1 µF | - | keep (goes away with in-package flash, §6) |
| **SX1280** (LDO mode) | 10n VR_PA, 470n + 10n VREG, 100n + 10n VBAT, 100n VBAT_IO, 1 µF + 10 µF local, TCXO 100n + 1n | Semtech DS Rev 3.2 §15.3 Fig 15-4 (LDO): C5 / C6 10 nF (VR_PA, VDD_IN), C9 470 nF (DCC_FB), C8 / C10 100 nF (VBAT_IO, VBAT); §15.2 Fig 15-3: TCXO 100 nF + 1 nF coupling | Matrix ESP8285 + SX1281 about 30 passives; this RX block has 25 | **−2** (PS-08) |
| **RTC6705** | 470n REG1D8_1, 100n REG1D8, 4 x 100n supplies, 2 x 100p, 10 µF | OpenOSD-X reference (C24 1u, C25 0.47u, C27 0.01u DNI, C32 / C36 / C16 1u, C39 / C33 4.7u, C31 100p); OpenVTX DESIGN: 100 nF per supply pin, REG1D8_1 470 nF, REG1D8 100 nF | Matrix about 20 | keep (parity, RF-adjacent) |
| **SE5004L** | 3 x 100 pF + 3 x 1 nF + 10 µF | "external decoupling capacitors are required" (DS p.1), EK1 layout | Matrix PA about 12 | keep (RF) |
| RGB LED | 100 nF | none stated | - | keep (low value; see F-E) |

---

## 4. Recommended proposals (detail)

### PS-01: one 100 nF line

- **Change:** every GRM033R61E104KE14D (X5R 25 V, 41 parts) becomes **Murata GRM033C81E104KE14D** (X6S 25 V
  0201, already on the BOM for the ESC). This includes the D34 EN filter.
- **Deltas:** parts 0; lines −1; area 0.
- **Risk:** X6S 0201 is less common than X5R: LCSC C181047 about 180,000 pcs, JLC extended (S, 2026-10-09);
  about +0.3 ¢ per part. One part grade for every quarter removes the "X5R only outside ESC quarters" placement
  constraint for 100 nF.
- **Evidence:** spec §4 temperature table already qualifies this MPN (V via Farnell / Arrow listings).

### PS-02: one 10 nF line

- **Change:** GRM033R61A103KA01J (X5R 10 V) becomes **Murata GRM033R71C103KA01D** (X7R 16 V 0201, the CT part)
  on C86, C88, C109 and the new CAP1. C77 and C90 go away in PS-08 and PS-09.
- **Deltas:** parts 0; lines −1.
- **Evidence:** TPS22810 §9.3.4: CT pin "can be as high as 2.5 V" (V), so either part fits the CT; X7R also
  covers C109 in the PA ring (125 °C). Semtech's reference BOM uses X7R 10 nF there (GRM155R71E103KA01D, V).

### PS-03: retire the 2.2 µF line

- **Change:**
  - C18, C24, C30, C36 (EFM8 VDD) become **GRM155C80J106ME11D** (10 µF 6.3 V X6S 0402, the board's 10 µF line,
    same land).
  - The spec D24 VIN1 capacitor becomes **Samsung CL05A475MP5NRNC** (4.7 µF 10 V X5R 0402, the RP2354A line).
- **Deltas:** parts 0; lines −1; area 0.
- **Why it is at least as good:**
  - The 10 µF X6S at 4.35-5.25 V keeps about 2.5-3.5 µF (I). The 2.2 µF part keeps 1.0-1.4 µF (spec §4.1 table).
    So the EFM8 still meets "1 µF required" with margin, and the +BATT bus gains about 6-8 µF for ripple.
  - The 6.3 V rating already sits on the same +BATT net in the ESC bulk.
  - VIN1: 4.7 µF at 5 V keeps about 1.8-2.2 µF (I), against TI's "CIN of 1 µF is sufficient" (TPS2116 §9).
    The nominal stays inside the 10 µF USB attach limit (4.7 µF +20 %).
- **Risk:** X5R at VIN1 needs the mux ≥ 2 mm from FET groups (H1). It sits at the front centre, bottom. P3
  confirms both DC-bias values on the maker curves.
- **Evidence:** EFM8BB51 DS Fig 5.1; TPS2116 SLVSFG1A §9.

### PS-04: RP2354A, one capacitor for pins 53 and 54

- **Change:** remove C55 (QSPI_IOVDD). C54 sits between USB_OTP_VDD pin 53 and QSPI_IOVDD pin 54. The two are
  0.6 mm apart in the floorplan.
- **Deltas:** parts −1; area −0.66 bottom.
- **Risk:** low. Raspberry Pi ships its reference this way.
- **Evidence:**
  - RPi "Hardware design with RP2350" §2.2.1: "pins 53 and 54 of RP2350A … share a single capacitor (C12)" (V).
  - House OpenFC-Lite-Mini (flown) uses 9 x 100 nF for the RP2350, against 12 here (V, netlist).

### PS-05: INA186, drop the common-mode input caps

- **Change:** remove C3 and C4 (100 nF from IN+ and IN− to GND). Keep R2 / R3 1 kΩ + C5 1 µF differential
  (f3dB = 1 / (4π·1k·1µ) = 80 Hz), C6 bypass and the R47 / C60 output RC at GPIO28.
- **Deltas:** parts −2; area −1.32 bottom.
- **Risk:** 48-96 kHz common-mode ripple on +BATT. TI moves common-mode filtering to the output RC, which the
  board keeps. Removing the caps also removes the mismatch path that turns common-mode ripple into a
  differential error. The V-test current-scale check stays.
- **Evidence:** INA186 SBOS318B §8.1.3, Fig 8-2 (input filter = 2 x RF + differential CF), the common-mode
  sentence quoted in §3, Fig 8-1 note A (V).

### PS-06: gyro supply caps shared with the LDO

- **Change:** remove C63 and C64.
  - **C62** (TPS7A2018 COUT, 1 µF) moves to BMI270 pin 8 (VDD). It is 5.3 mm away today; C63's spot is 1.9 mm.
  - **C61** (CIN, 1 µF) sits between U12 IN and gyro pin 5 (VDDIO). U12 and U11 are 2.6 mm apart.
- **Deltas:** parts −2; area −1.32 top.
- **Risk:** low-moderate. The D33 gyro basics stay: own LDO, same side, distances. Condition: each kept cap is
  ≤ 1.5 mm from both pins it serves; otherwise keep C64.
- **Evidence:**
  - BMI270 DS §7.2 asks 100 nF at pins 5 and 8; a 1 µF 0201 at the pin meets that, with the same ESL class.
  - TPS7A20 COUT 0.47-200 µF effective (V).
  - C62 at 1.8 V: about 0.6-0.85 µF effective (I), ≥ 0.47 µF.

### PS-07: one capacitor for the OSD switch and comparator

- **Change:** remove C69. Move C70 (100 nF) to the bottom between U14 and U15 (2.5 mm apart).
- **Deltas:** parts −1; area −1.32 top, +0.66 bottom.
- **Risk:** low. Today both caps sit on the other side, 4.2 and 6.5 mm away, so they decouple little.
- **Evidence:** TLV7031 DS §7.4.1 (conditional 100 nF); house OSD has 3 caps for 3 parts (with the COS8051,
  dropped here).

### PS-08: SX1280, keep only the Semtech set

- **Change:** remove **C90** (10 nF VBAT HF) and **C93** (10 µF radio bulk). Keep:
  - C86 10 nF VR_PA; C88 10 nF VDD_IN / VREG; C87 470 nF DCC_FB;
  - C89 100 nF VBAT; C91 100 nF VBAT_IO;
  - C92 1 µF local reservoir (about 12-14 mm from the ESP32 / LDO bulk);
  - TCXO C85 / C84.
- **Deltas:** parts −2; area −1.79 bottom.
- **Risk:** TX current pulses at the radio (LDO mode). The V7 desense / link test covers it. This is also the
  main lever for F-B (LP5912 COUT maximum).
- **Evidence:** Semtech SX1280/1 DS Rev 3.2 Fig 15-4 (LDO) and Fig 15-3 (TCXO) (V); LP5912 §7.6 (V).

### PS-09: ESP32, drop the VDD3P3 10 nF

- **Change:** remove **C77**. C76 100 nF stays at pins 3/4 and C82 10 µF stays at 3.8 mm. Do not add the
  Espressif VDD3P3 LC filter or the CAP2 RC.
- **Deltas:** parts −1; area −0.66 bottom. CAP1 is counted in PS-00.
- **Risk:** low. The LC filter exists "to suppress high-frequency harmonics" of Wi-Fi TX. D25 removed the
  radiator and ELRS runs `--no-auto-wifi`.
- **Evidence:** Espressif ESP32 schematic checklist, Analog Power Supply and External Capacitor (V, quoted in §3).

### PS-10: TPS61022 EN tied to VIN

- **Change:** remove R6 (100 kΩ). EN goes straight to VIN (+BATT).
- **Deltas:** parts −1; area −0.66 bottom.
- **Risk:** none. Abs max is the same for both pins, so a surge exposes EN no more than VIN. Behaviour is
  identical: enabled above UVLO, the USB back-feed case unchanged.
- **Evidence:** TPS61022 DS §6.1: "VIN, EN, FB, MODE, SW, VOUT −0.3 … 7 V"; §7.3: enables when EN > 1.2 V (V).

### PS-11: no external PA_EN pull-down

- **Change:** remove R69 (10 kΩ on the LP5907 EN node).
- **Deltas:** parts −1; area −0.66 top.
- **Why it is safe:**
  - The LP5907 EN "has an internal 1MΩ pulldown resistor to hold the regulator off by default" (DS pin table,
    note 10).
  - The ESP32 GPIO2 strap default is pull-down, value 0, RPD 45 kΩ (DS v5.3 Table 3-1, §5). It reads 0 through
    R83 1k as on every ESP32 board that leaves GPIO2 to its internal pull-down.
  - Qb leakage pulls the same way.
- **Risk:** low.

### PS-12: PA drive stage re-derived (fixes F-A)

- **Change:**
  - R71 = R72 = **3.3k**; C124 = C125 = **1 µF** (GRM033R61A105ME44D); R74 = **3.3k**;
  - **R73 omitted** (R72 is already the series element; base current about 15 µA);
  - R75 = **75R** (RC0201FR-0775RL, the R51 line).
- **Calculated response** (I, `bomred` calc):
  - f3dB = 45 Hz and −83 dB at 10 kHz (spec: ≤ 100 Hz, ≥ 40 dB);
  - Vb_open = V_avg / 3: 0.54 V at the 49 % YOLO duty (Q1 off) and 0.99 V at the 90 % pit duty;
  - Ie ≈ 3.7 mA (β 150), so Q1_C ≈ 0.2 V and PAOUT1 supply ≈ 0 (pit);
  - Thevenin 2.2 kΩ, so the result hardly depends on β;
  - GPIO12 strap: 9.9 kΩ DC path to GND, reads low.
- **Deltas:** parts −1; lines 0 (18k stays in PS-15; −1 if PS-15 is not taken); area −0.66 top.
- **Risk:** P4-5 / V5 still own the slope (≥ 20 duty steps between 25 and 100 mW). These are start values that
  at least work.
- **Evidence:** spec §4.8 criteria, PINMAP F15.

### PS-13: boost feedback divider from the value set

- **Change:** R4 909k → **47k** (RC0201FR-0747KL, the R64 line); R5 120k → **6.2k** (RC0201FR-076K2L).
- **Calculated values** (I):
  - 0.6 x (1 + 47/6.2) = **5.148 V**. Worst case 4.93-5.37 V with VFB 585-615 mV and 1 % resistors, identical
    to today.
  - R2 = 6.2 k < 300 k.
  - Divider current 97 µA (0.5 mW).
- **Deltas:** lines −2.
- **Evidence:** TPS61022 §8.2.2.1 "keep R2 smaller than 300 kΩ" (V); TI example 732k / 100k.

### PS-14: PR1 divider from the value set

- **Change:** R7 27.4k → **3.3k**; R8 10k → **1.2k** (the R58 / R60 line).
- **Calculated values** (I):
  - Ratio 3.75, so the threshold is **3.45-4.05 V** (was 3.44-4.04 V) against VREF 0.92-1.08 V.
  - VBUS load is 1.1 mA while USB is attached.
  - The AP1606 gate pull-down becomes 4.5 kΩ (stronger). The battery-only leakage error drops below 1 mV.
- **Deltas:** lines −1.
- **Risk:** none found. TI gives PR1 leakage ≤ 0.1 µA.
- **Evidence:** spec §4.2.

### PS-15: O4 EN network from the value set

- **Change:** R9 = **33k** (RC0201FR-0733KL, new); R10 = **18k** (RC0201FR-0718KL, existing); hysteresis =
  **510k** (RC0201FR-07510KL, the R61 line). This replaces D34's 90.9k / 49.9k / 1.5M. Keep the 100 nF EN filter
  (X6S line), the BAS16LD and the GPIO27 pull-down (3.3k, PS-16).
- **Calculated values** (I, same equations as spec §4.2):
  - shed at **2.80-3.09 V** falling; on again at **3.27-3.77 V** (spec 2.80-3.09 / 3.26-3.75 V);
  - resistor-only hysteresis 5.15·33/510 = **0.333 V** at the cell (spec asks ≥ 0.31 V);
  - Thevenin 11.4 kΩ;
  - EN filter τ 1.1 ms with 100 nF, inside D34's 1-10 ms band (470 nF from the existing line gives 5.4 ms);
  - PINIO clamp with GPIO27 in reset: EN ≤ 0.80 V against VENF ≥ 1.08 V (spec ≤ 0.75 V);
  - BAS16LD hot leakage error × 11.4 kΩ ≈ 11 mV (spec 31 mV).
- **Deltas:** lines −2 against the spec values, −1 against today's plan.
- **Risk:** cell drain 82 µA (spec 30 µA); V1 confirms the shed points. This is a D34 value change, so it goes
  into the decisions log if adopted.

### PS-16: HD_EN pull-down 4.7k → 3.3k

- **Change:** R11 → **RC0201FR-073K3L**.
- **Calculated values** (I):
  - GPIO27 high load = 1.0 + 0.53 (two 10k base resistors) = 1.5 mA, against the 4 mA default drive;
  - the reset clamp margin improves (see PS-15).
- **Deltas:** lines −1.

### PS-17: VREG_AVDD resistor 30R → 27R

- **Change:** R41 → **RC0201FR-0727RL** (the USB series line).
- **Calculated values** (I): RC corner 1.25 kHz (RPi 33 Ω → 1.03 kHz); 200 µA gives a 5 mV drop.
- **Deltas:** lines −1.
- **Alternative:** USB R42 / R43 27R → 30R, as on the flown OpenFC-Lite-Mini (R24 / R37 = 30R, V netlist). Not
  preferred: it adds 3 Ω to the USB FS driver impedance budget.
- **Evidence:** RPi HW design §2.1 ("an RC filter of 33 Ω and 4.7 μF is adequate", VREG_AVDD ≈ 200 µA) (V).

### PS-18: one input cap for both LP5912s (fixes F-D)

- **Change:** C13 + C120 (2 x 0201 1 µF) become one **CL05A475MP5NRNC** 4.7 µF 0402 between U4 and U21, which
  are 2.4 mm apart on the bottom.
- **Calculated value** (I): at 5.15 V about 1.6-2.0 µF effective, ≥ 0.5 µF for each LDO.
- **Deltas:** parts −1; area −0.20 bottom.
- **Evidence:** LP5912 §7.6 note 1 (V).

### PS-19: LP5907 output cap in 0402 (fixes F-C)

- **Change:** C123 0201 1 µF becomes **CL05A475MP5NRNC** 4.7 µF 0402 (about 2.6 µF effective at 2.85 V, I).
  Use GRM155C80J106ME11D instead if P5 places U22 within 2 mm of a FET group (X6S rule). Both lines exist, both
  stay ≤ 10 µF effective.
- **Deltas:** parts 0; lines 0; area +0.47 top.
- **Evidence:** LP5907 DS §5.6 note 1 (V).

---

## 5. Considered and not recommended (or deferred)

### 5.1 Moves to 0201: none left

| Part | Why it stays |
|---|---|
| R57 51R 0402 (LNA_IN dummy) | spec rates it at 63 mW; 0201 is 50 mW at 70 °C (owner rule) |
| R67 0R 0402 (PA VCC selector) | PA current up to 0.65 A; 0201 jumpers are rated about 0.5 A (S), 0402 about 1 A |
| C106 1 µF 0402 25 V | RTC6705 loop filter: a 0201 10 V part would vary about 2:1 with VT (0-3 V), changing PLL dynamics per channel |
| 4.7 µF / 10 µF 0402 | 0201 versions keep 30-40 % at 3.3 V (spec note) or are 4 V parts (below +5V / +BATT) |
| 22 µF 0603 | bulk; no 0402 X6S 22 µF ≥ 6.3 V with useful DC bias |
| D5 / D6 0402 LEDs | house colours (spec §4.5); LED track |

### 5.2 Pull-ups and pull-downs kept

| Part | Internal alternative | Decision |
|---|---|---|
| R50 FLASH_CS 10k | none: Winbond asks /CS to track VCC at power-up, "If needed a pull-up resister" (§4.1) | keep |
| R49 GYRO_CS 10k (PS-O8) | Betaflight `sensorsPreInit()` / `spiPreinit()` drive CS high before `spiInit` (V, bf `fc/init.c` l. 222-229, `drivers/bus_spi_config.c`); dedicated SPI1 bus | keep: house parity (OpenFC R49) and the RP2350 reset pull-down selects the chip; saves only 1 part |
| R48 beeper gate 100k (PS-O4) | RP2350 reset pull-down (35-189 kΩ) | keep: the gate floats while +5V is up and IOVDD is not (power-up chirp); house R23 has it |
| R56 + C73 CHIP_PU 10k / 1 µF | none | keep: Espressif "R = 10 kΩ and C = 1 μF" |
| R68 VTX_PWR_EN 100k | none | keep: default-on for stock ELRS |
| R84 GPIO21 10k (PS-O5) | open-drain firmware | keep: a push-pull high would fight the HD gate; spec D17 makes the hardware the authority |
| R78 / R79 HD gate base Rs | one shared base R | keep: separate base resistors per BJT |
| R80-R83 VTX SPI / GPIO2 series 1k | none | keep: back-power limit (F21) and HD gate priority |
| Already internal | EFM8 RSTb (F12), SX1280 NRESET, ESP32 GPIO0, GPIO12 via the RC path | - |

### 5.3 Other options

| ID | Option | Parts / lines / area | Why not now |
|---|---|---|---|
| PS-O1 | R54 287R → 270R (OSD level divider from the set, 820 / 2.4k / 270) | 0 / −1 / 0 | levels Hi-Z 0.334, white 1.011, black 0.258 V against the house 0.345 / 1.064 / 0.261 V (−1 to −5 %, I); start values (P4-10), V9 measures, so P4-10 may take it |
| PS-O2 | Pad bulk C1 / C2 CL10A226MO7JZNC → GRM188C80J226ME15D | 0 / −1 / 0 | costs about 4-6 µF effective on +BATT (spec §4.1 table), which eats into the EFM8 VIH margin (PINMAP F4); acceptable only together with PS-03, which adds about 6-8 µF |
| PS-O3 | PA VCC selector R67 → fixed +BATT copper | −1 / −1 / about −1.5 top | prototype needs the selector until V5 decides; take it for the production BOM |
| PS-O6 | Drop C92 (radio 1 µF) as well | −1 / 0 / −0.66 bottom | only if the F-B sum is still over 10 µF; V7 |
| PS-O7 | BEMF networks as 2x Yageo YC104-FR arrays per ESC (3x10k and 3x1k, 1 spare each; 1.40 x 0.60 mm, 31 mW per element, ±1 %; S, Digi-Key) | −16 / +2 / about −1.6 top in total | 0.35 mm convex-terminal pitch puts them in the O15 fine-pitch EQ with a ganged mask; adds 2 lines; area gain about 0.4 mm² per ESC; harder AOI and rework. Revisit at rev2 |
| - | VTX SPI 3x1k → YC104 | −2 / +1 / about −0.4 | R83 sits on another QFN side; little gain |
| - | C66 100 pF video-entry shunt | −1 / 0 / −0.66 | spec §11 layout rule with an onboard 5.8 GHz PA; the house OSD sheet has none, but its board has no VTX. Keep |
| - | Fewer boost Cout (3 instead of 4) | −1 / 0 / −2.3 | D15: TI asks ≥ 20 µF effective above 1.5 A; three caps give 15-21 µF (I) |
| - | Fewer +BATT bulk or EFM8 caps | - | EFM8 "required" pair; Matrix has more bulk per channel than this board |
| - | RTC6705 / PA / loop / video / crystal / TCXO / LPF / BPF / DC-block values | - | RF and PLL values kept exactly (task rule) |

---

## 6. Passive consequences of the other tracks (for the BOM-reduction summary)

**RX MCU with in-package flash** (owner: "ESP with external flash? Look at OpenRX-Lite-UFL"):

- Any in-package-flash part deletes U17 GD25Q32 and its C81.
- An SiP such as ESP32-PICO-V3 also integrates the 40 MHz crystal and "filter capacitors" (S, Espressif
  product description). That deletes X2, C71, C72 and very likely CAP1: about 3-5 passives plus 2 ICs.
- An ESP32-C3 has no CAP pins (OpenRX-Lite-UFL netlist, V), but the spec §4.7 says ELRS 4.x drives the VTX only
  on non-C3 ESP32.
- PS-08 and PS-09 apply unchanged.

**Other tracks:**

- **LED-strip translator dropped** (PINMAP F1 option a, direct 3.3 V drive): −U23, −C126, −C127.
- **Gyro LDO dropped** (BMI270 VDD 1.71-3.6 V runs on +3V3): −U12, −C61, −C62. **Not recommended:** house imu
  rule and the D33 "gyro supply basics".

---

## 7. Checks handed to P3 / P4

1. **Maker DC-bias values** (Murata SimSurfing / Samsung) for:
   - GRM155C80J106ME11D at 2.85 / 3.3 / 4.35 / 5.25 V;
   - CL05A475MP5NRNC at 2.85 / 3.3 / 5.15 V;
   - GRM033R61A105ME44D at 1.8 / 2.85 / 3.3 / 5.15 V.

   This report's effective values are I (typical curves); murata.com refused the automated fetch (403).
2. **Sum of effective capacitance on +3V3** ≤ 10 µF (LP5912 §7.6) after PS-04 to PS-09. If over: PS-O6 or
   TLV75533PDRVR (regulator track).
3. **Placement conditions:**
   - PS-06: C62 / C61 ≤ 1.5 mm from their pins;
   - PS-07: the shared cap on the bottom between U14 and U15;
   - PS-04: C54 between pins 53 and 54;
   - PS-18: the shared CIN between U4 and U21.
4. **Value changes** PS-13 to PS-17 go into the P4 schematic and DECISIONS.md. PS-15 changes D34 values, PS-12
   replaces the P4-5 start values.
5. **Add ESP32 CAP1** (pin 48, 10 nF X7R ±10 %) to the RX sheet and PINMAP.

---

## Sources

- bom_plan.json, floorplan.json, DESIGN-SPEC.md §4.1-§4.9, §9.2, §11; PINMAP.md (F1, F12, F15, F21, pin
  tables); FLOORPLAN.md; LIBRARY.md (`_W` land sizes); DECISIONS.md (D11, D15, D17, D24, D25, D33, D34).
- Sibling netlists and BOMs (kicad-cli 10 export, V):
  - OpenFC-Lite-Mini: RP2350A 9 x 100 nF, 30R USB / VREG_AVDD, imu, osd, blackbox;
  - OpenRX-Lite-UFL: ESP32-C3 + SX1281 decoupling, D1 on +3V3;
  - OpenAIO, OpenESC-20x20.
  - Files: `bomred/sib/*.csv`, `*.xml`.
- Matrix II: research 00 (photo analysis) and 01 §5.2 (passive counts, I).
- EFM8BB51 Data Sheet Rev 1.0 §5.1 Fig 5.1 (`dl/ds/efm8bb51.txt`).
- Raspberry Pi, Hardware design with RP2350 (RP-008280-DS-2) §2.1, §2.2.1:
  https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf
  (`bomred/dl/hw-rp2350.txt`).
- Espressif ESP32 Series Datasheet v5.3, Table 2-1 (CAP1 / CAP2), Table 3-1 (strapping), RPD 45 kΩ.
- Espressif ESP32 schematic checklist:
  https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/schematic-checklist.html
- Semtech SX1280/1 DS Rev 3.2 §15.1-15.3, Figs 15-1, 15-3, 15-4, Table 15-1 (`p23/staging/rx/dl/sx.txt`).
- TI datasheets:
  - TPS61022 (SLVSDX7D) §6.1, §6.3, §8.2.2;
  - TPS2116 (SLVSFG1A) §9, §10;
  - TPS22810 (SLVSDH0C) §6.3, §9.3.4, §10.3-10.4;
  - LP5912 (SNVSA77D) §7.6, Table 9-1;
  - LP5907 (SNVS798Q) §5.6, pin table note 10;
  - TPS7A20 (SBVS338H) §6.3 note 3;
  - TLV755P (SBVS320D) §6.3 and orderable addendum (TLV75533PDRVR);
  - INA186 (SBOS318B) §8.1.3, Figs 8-1 and 8-2;
  - TLV7031 §7.4.1.
- Bosch BMI270 datasheet BST-BMI270-DS000-08 rev 1.6 §7.2 (`bomred/dl/bmi270.txt`).
- Winbond W25Q128JV §4.1 /CS power-up text (`rv3dl/w25q.txt`).
- XINGLIGHT XL-1010RGBC-2812B datasheet (VDD 3.5-5.5 V).
- Betaflight source at 498430a: `src/main/fc/init.c` l. 222-229, `src/main/drivers/bus_spi_config.c`
  (spiPreinit).
- Distributor screens (S, 2026-10-09):
  - LCSC C181047 GRM033C81E104KE14D, about 180k: https://jlcpcb.com/partdetail/GRM033C81E104KE14D/C181047
  - Yageo YC104-FR (1.40 x 0.60 mm, 8 terminals, 31 mW per element):
    https://www.digikey.ie/en/products/detail/yageo/YC104-FR-0710KL/5951436
  - A TDK C1608X6S1A226M080AC (22 µF 10 V X6S 0603) could not be confirmed as a listed product, so no 10 V X6S
    22 µF line is proposed.

---

## Verification

Date 2026-10-09. Adversarial pass by a separate agent: each recommended proposal was checked against primary
sources (datasheets, the RP2350 datasheet and RPi guide, the Espressif checklist, ELRS source at `8c51826`),
the placed `floorplan.json` / `OpenAIO-Whoop.kicad_pcb` geometry, distributor pages and the spec's binding rules.
Scripts: `bomred/verify_geo.py` (2D edge distance from each part to the nearest FET group and the PA land),
`verify_pads.py`, `verify_near.py` (house board), `verify_pa.py` (drive-stage RC and Q1 bias). Downloaded
RP2350 datasheet text: `bomred/verify_dl/rp2350.txt`.

Verdicts: **CONFIRMED** = it survives as written. **AMEND** = the idea holds but the proposal as written breaks a
rule or names a bad MPN; the fix is given and keeps the stated part/line deltas. **REFUTED** = drop it.

### V.1 Verdict per recommended proposal

| ID | Verdict | One line of evidence |
|---|---|---|
| PS-00 | CONFIRMED | Espressif ESP32 checklist: "C5 (10 nF) that connects to CAP1 … is required for proper operation of ESP32"; the CAP1-CAP2 RC "is not required" if the application "is not using Deep-sleep mode" (ELRS source has no `esp_deep_sleep`/light-sleep call, grep). CAP1 sits by U16, which is inside the PA projection, so it must be X7R (H3): use the PS-02 amended part. The rx-vtx track's RV-0a (+3.3 nF ∥ 20 kΩ) is not needed |
| PS-01 | CONFIRMED (stock corrected) | Correct, and stronger than stated: 13 of today's X5R 100 nF / 10 nF caps sit within 2 mm of a FET group or the PA land (C3, C4, C49, C59, C69, C70, C75, C79, C81, C83, C88, C91, C109; `verify_geo.py`), which breaks spec line 145 / H1 / H3 ("X5R only outside the ESC quarters and away from the PA"). Stock: the live LCSC page for C181047 shows **14,900** (the 180k figure is a cached image page); element14 27,343. Enough for prototypes (about 50 per board after the removals), a P7 sourcing item for volume |
| PS-02 | AMEND (MPN) | The target **GRM033R71C103KA01D** has no listing: Digi-Key "did not return any results" (the same query finds GRM033R71A103KA01D with 7.37 M in stock), no LCSC number, bom_plan says "P3 confirms the MPN". Use **Murata GRM033R71A103KA01D** (10 nF 10 V X7R ±10 %, LCSC C76941, 408,700 on 2026-10-09; Digi-Key 7.37 M). All five uses stay ≤ 3.3 V (CT ≤ 2.5 V, TPS22810 §9.3.4). X7R is needed: CAP1 and C109 (0.91 mm from the PA) are in the PA zone. Same −1 line. This also settles the power track's opposite merge PE-9 (to X5R), which would leave CAP1/C109 in breach of H3 |
| PS-03 | AMEND (VIN1 part) | EFM8 half confirmed: EFM8BB51 Fig 5.1 asks "1 µF and 0.1 µF bypass capacitors required"; supply ramp has only a minimum (10 µs/V, §4 table), so more C is harmless; 6.3 V X6S already sits on +BATT. VIN1 half breaks H1: TPS2116 VIN1 is pin 3 on the **west** side of U3, and U3 is 1.62 mm from FET Q20 (C12 next to it is 0.83 mm), so an X5R CL05A475MP5NRNC at VIN1 sits < 2 mm from a FET group (the report's "front centre, ≥ 2 mm" premise is false as placed). Use **GRM155C80J106ME11D** (X6S, LCSC C237279) at VIN1: about 2-3 µF effective at 5 V (I), more damping of the cable LC; the nominal 10 µF equals the USB attach figure, but in USB-only mode the mux already connects far more downstream capacitance, so V1 measures inrush either way. Still −1 line |
| PS-04 | CONFIRMED | RPi guide §2.2.1: "pins 53 and 54 of RP2350A … share a single capacitor (C12)", and §1: the minimal design is used with RP2354 by omitting the flash. Flown house OpenFC-Lite-Mini (RP2354A) does exactly this: C12 is 1.13 mm from pin 53 and 0.98 mm from pin 54 (`verify_near.py` on `OpenFC.kicad_pcb`). Caveat from the RP2350 datasheet §14 (RP2354): "The internal flash is powered by the QSPI_IOVDD supply input … account for the increased high-frequency currents on this supply pin": keep C54 ≤ 1 mm from pin 54 (today C54 is about 2.9 mm away, so P5 must move it) |
| PS-05 | CONFIRMED | INA186 SBOS318B §8.1.3: "Filtering the input filters out differential noise … If high-frequency, common-mode noise is a concern, add an RC filter from the OUT pin to ground"; Fig 8-2 has 2 x RF + one differential CF. The HF-transient warning in the same section is about differential shunt voltage, which C5 still filters. C3/C4 are also X5R parts 0.6-0.75 mm from Q5 today (H1), so removal clears a rule breach |
| PS-06 | AMEND (placement condition fails as placed) | Datasheets allow it (BMI270 §7.2 "recommended to use 100nF … at pin 5 (VDDIO) and pin 8 (VDD)"; TPS7A20 §6.3: CIN "not required for LDO stability", COUT ≥ 0.47 µF effective). The C61→VDDIO half works (U12 IN pin 4 to gyro pin 5 is 2.5 mm; a 0201 between them is about 1.1 mm from each). The C62→VDD half fails its own ≤ 1.5 mm rule: U12 OUT (1.19, 2.26) and gyro pin 8 (−2.16, 2.30) are 3.35 mm apart with the BMI270 body between them; the best 0201 site is about 1.57 mm from each. P5 must rotate or move U12 so OUT faces pin 8; otherwise keep **C63** (the report's fallback names C64, the wrong cap) and take −1 part. The report's "C62 5.3 mm from the gyro" does not match floorplan.json (body gap 0.34 mm). The power track's PE-6 (drop C61, merge C62+C63 at pin 8) is the alternative; choose one |
| PS-07 | CONFIRMED | TLV7031 asks for 100 nF only for high supply impedance or long traces; U14 and U15 are 2.5 mm apart on the bottom (centres, floorplan.json). The shared cap lands over the ESC quarter (U14/U15 overlap Q8 in 2D), so it needs the X6S part: PS-07 depends on PS-01. Today's C69/C70 are X5R 0.22/0.78 mm from Q12 (H1 breach) |
| PS-08 | CONFIRMED | Semtech SX1280/1 DS Rev 3.2 Table 15-1 reference BOM: C5/C6 10 nF, C8/C10 100 nF, C9 470 nF, no 10 µF and one cap per VBAT pin; LP5912 SNVSA77D §7.6 COUT max 10 µF "verified by design". It is the right lever but may not close the +3V3 limit alone (P4 sum, PS-O6 or TLV75533 next) |
| PS-09 | CONFIRMED | Espressif checklist (Analog Power Supply): the 10 µF is "highly recommended" (C82 stays) and the LC filter is "to suppress high-frequency harmonics" of TX; no 10 nF is required at VDD3P3. D25 removed the radiator; LNA_IN ends in R57 |
| PS-10 | CONFIRMED | TPS61022 SLVSDX7D §6.1: "VIN, EN, FB, MODE, SW, VOUT −0.3 … 7 V"; §7.3.2: enabled above 1.2 V; BOOST_EN has no other connection in bom_plan (R6 only). EN = VIN also meets the commons "no EN > VIN" rule. Same as power track PE-3 |
| PS-11 | CONFIRMED | LP5907 SNVS798Q note 10: "There is a 1MΩ resistor between EN and ground on the device"; ESP32 DS v5.3 Table 3-1: GPIO2 default pull-down, RPD 45 kΩ; ELRS `devVTXSPI.cpp` l. 369-370 drives the VREF pin OUTPUT LOW at init, then controls it. Also compatible with the vtx track's V1 (which deletes R83) |
| PS-12 | CONFIRMED (caveat) | F-A is real: 6.2/(18+18+10+6.2) = 0.119, Vb 0.19-0.35 V over the ELRS window (`MIN_PWM` 2000, `MAX_PWM` 3700, `setDuty(count*1000/4096)`, 10 kHz; devVTXSPI.cpp l. 30-31, 164, 373). PS-12 reproduced: f3dB 44 Hz (63 Hz with 30 % DC-bias loss), −83 dB (−77 dB) at 10 kHz, Vb 0.54 / 0.99 V at 49 / 90 %; pit saturates Q1 at every corner checked (Ie 3.1-5.6 mA against 3.0 mA needed). Caveat: "Q1 off at YOLO" holds only for a typical-VBE part at 25 °C; a low-VBE BC847 or an 85 °C board conducts 0.2-1.1 mA at 49 % and pulls the YOLO ceiling down by 0.15-0.8 V (`verify_pa.py`), which V5 must see. Dropping R73 departs from the spec text "series base resistor" (the clamp it guards against does not occur with Re·β ≈ 11 kΩ), so log it. The vtx track's V2 (PNP stage) would supersede it; PS-12 is then the fallback |
| PS-13 | CONFIRMED | Reproduced 0.585-0.615 V × (1 + 47/6.2) with 1 % parts = 4.932 / 5.148 / 5.371 V (below VOVP 5.5 V min). TPS61022 §8.2.2.1: keep R2 < 300 kΩ, "lower value increases the immunity against noise injection". No feed-forward cap in the plan; if one is ever added (§8.2.2.4, > 40 µF effective) it scales to about 1.7 nF with R1 = 47k |
| PS-14 | CONFIRMED | Reproduced 0.92-1.08 V × 4.5/1.2 = 3.45-4.05 V; TPS2116 gives no divider-impedance limit (only IPR1 ≤ 0.1 µA, §6.5); battery-only leakage error drops to < 1 mV. Conflicts with the power track's PE-12 (49.9k/18k, which assumes PE-1 deletes the AP1606) |
| PS-15 | CONFIRMED | Reproduced with TPS22810 VENF 1.08-1.18 / VENR 1.13-1.30 V (SLVSDH0C table): shed 2.797-3.086 V, on 3.275-3.767 V, resistor hysteresis 0.333 V, Thevenin 11.4 kΩ, τ 1.14 ms (inside D34's 1-10 ms), drain 82 µA at 4.2 V. Clamp with GPIO27 in reset is **0.81 V** at VF 0.6 V and about 0.87 V cold (the report says ≤ 0.80), still below VENF min 1.08 V. Needs a D34 change entry |
| PS-16 | CONFIRMED | 1.0 mA + 2 × 0.26 mA = 1.5 mA against the RP2350 4 mA default drive; improves the PS-15 clamp. The power track's PE-10 picks 2.4k for the same reason; choose one (with the vtx track's V1 the base currents vanish) |
| PS-17 | CONFIRMED | RPi guide §2.1: "an RC filter of 33 Ω and 4.7 μF is adequate" (VREG_AVDD about 200 µA). The RP2350 datasheet §6.3.8.1 is stricter in wording ("must be RC filtered as per Figure 25", 33 Ω), but 27 Ω changes the corner from 1.03 to 1.25 kHz (−1.7 dB of filtering) and the flown house board uses 30 Ω |
| PS-18 | AMEND (dielectric) | LP5912 §7.6 note 1 (> 0.5 µF effective) and §9.2.2.2 ("at least 1 µF", "not more than 1 cm") are met by one shared cap. But both LP5912 IN pins (pin 6) face east toward the ESC2 FETs: U4/U21 are 1.2 mm from Q10/Q9, and the cap site east of the IN pins is about 0.5 mm from them, so an X5R CL05A475MP5NRNC breaks H1 (today's C13/C120 already do, at 0.0/0.09 mm). Use **GRM155C80J106ME11D** (X6S 6.3 V, the +5V C12 part) for the shared CIN: same land, same −1 part, 0 lines. The power track's PE-5 also chose an X6S part here |
| PS-19 | CONFIRMED | LP5907 §5.6: COUT 0.7 min / 10 max µF, note 1 "> 0.7µF over the full range"; U22 / C123 are 3.1 mm from Q16 and 16 mm from the PA, so X5R CL05A475MP5NRNC is allowed there. Its input C122 (0201 1 µF, about 0.5 µF at 3.3 V) is also under 0.7 µF, but C58 4.7 µF sits 7.3 mm away (inside the 1 cm of §7.2.2.4) once PS-08 removes C93 (5.0 mm) |

Not-recommended options (spot check): PS-O2 should be **upgraded** when PS-03 is taken: pad bulk C2 (X5R) is
1.75 mm from Q19, so the X6S part fixes an H1 breach as well as merging a line (the power track's PE-8 agrees).
PS-O1, PS-O3, PS-O4, PS-O5, PS-O6 and PS-O7 stand as written.

### V.2 Totals after the amendments

The amendments change MPNs, not counts. The recommended set stays at **−13 placements, −10 lines** against the
corrected baseline. PS-06 drops to −1 part if P5 cannot re-place U12. Line arithmetic was re-checked: PS-12 and
PS-15 share the 18k line, and PS-12 and PS-13 share the 6.2k line, so their attribution is combined.

Line changes from the amendments:

- The 10 nF line becomes GRM033R71A103KA01D.
- The 10 µF X6S line GRM155C80J106ME11D gains VIN1 and the shared LP5912 CIN.
- CL05A475MP5NRNC gains only C123.

### V.3 Additional findings from this pass

1. **X5R parts that still break the "outside the ESC quarters and away from the PA" rule after the recommended
   set** (spec line 145, H1, H3; 2D edge distance from `verify_geo.py`). P3 must give each one an X6S/X7R part,
   or P5 must move it.

   | Part | Value / function | Breach |
   |---|---|---|
   | C5 | 1 µF, INA186 differential | 0.88 mm from Q5 |
   | C14 | 1 µF, LP5912 COUT | 1.34 mm from Q10 |
   | C68 | 1 µF | 0.2 mm from Q9 |
   | C80 | 1 µF, ESP32 VDD_SDIO | inside the PA projection |
   | C56 | 4.7 µF, RP2354A | 1.15 mm from Q2 |
   | C57 | 4.7 µF, RP2354A | 1.02 mm from Q2 |
   | C105 | 4.7 µF | 0.52 mm from Q20 |
   | C87 | 470 nF, SX1280 DCC_FB | 1.82 mm from Q16 |
   | C2 | 22 µF, pad bulk | 1.75 mm from Q19 (PS-O2 fixes it) |

   A 1 µF X6S 0201 line (the spec's fallback GRM033C81A105ME05D, P3 to confirm) would cover the 1 µF group.
2. **MPN existence.** GRM155C80J106ME11D exists (LCSC C237279) but has no Digi-Key listing. GRM033R71C103KA01D
   was found nowhere (see PS-02). P3 should drop the "P3 confirms" MPNs that no distributor lists before the
   lines are merged onto them.
3. **Cross-track conflicts to settle in one D35+ entry:**

   | Topic | Proposals in conflict | Recommendation |
   |---|---|---|
   | 10 nF merge direction | PS-02 vs PE-9 | Merge onto the X7R part, per the H3 argument above |
   | EFM8 bulk | PS-03 (move to 10 µF) vs PE-7 (delete the 2.2 µF and move the 22 µF cell bulk to VDD, −4 parts) | PE-7 supersedes the EFM8 half of PS-03 if P5 finds the 0603 sites |
   | Gyro caps | PS-06 vs PE-6 | Choose one |
   | GPIO27 pull-down R11 | 3.3k (PS-16) vs 2.4k (PE-10) | Choose one |
   | PR1 divider | 3.3k/1.2k (PS-14) vs 49.9k/18k (PE-12, depends on PE-1) | Choose one |
   | PA drive stage | PS-12 vs vtx V2 (PNP stage) | V2 is P4's default; PS-12 is the fallback |
   | ESP32 CAP network | PS-00 (CAP1 only) vs RV-0a (full network) | PS-00 |
   | RX MCU | PS-00 / PS-09 vs RV-4 (ESP32-PICO-V3) | RV-4 makes CAP1 and C77 moot |

### V.4 Sources checked in this pass

- Espressif ESP32 schematic checklist (External Capacitor, Analog Power Supply):
  https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/schematic-checklist.html
- RP2350 datasheet §6.1.2, §6.3.8.1 and §14 (RP2354):
  https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf (`verify_dl/rp2350.txt` l. 27198-27260,
  27965-27980, 86057-86058).
- RPi "Hardware design with RP2350" §1, §2.1, §2.2.1 (`dl/hw-rp2350.txt` l. 163-164, 300-301, 372-374).
- House OpenFC-Lite-Mini `OpenFC.kicad_pcb`: C12 at pins 53/54, C9 at pins 44/45.
- Semtech SX1280/1 DS Rev 3.2 §15.1, Table 15-1 (`ds/sx1281.txt`).
- TI datasheets:
  - INA186 SBOS318B §8.1.3;
  - TPS61022 SLVSDX7D §6.1, §6.5, §7.3.2, §8.2.2.1, §8.2.2.4;
  - TPS2116 SLVSFG1A pin table and §6.5;
  - TPS22810 SLVSDH0C EN thresholds;
  - LP5912 SNVSA77D §7.6, §9.2.2;
  - LP5907 SNVS798Q §5.6, note 10, §7.2.2.4;
  - TPS7A20 SBVS338H §6.3.
- EFM8BB51 DS §5.1 and the reset table (`pwr/ds/efm8bb51.txt`).
- BMI270 DS §7.2.
- ESP32 DS v5.3 Table 3-1 and RPD.
- ELRS `src/lib/VTXSPI/devVTXSPI.cpp` at 8c51826 (l. 30-31, 164, 369-373); no sleep calls in `src/`.
- Distributors (2026-10-09):
  - LCSC C181047 (14,900): https://www.lcsc.com/product-detail/C181047.html
  - LCSC C76941 GRM033R71A103KA01D (408,700): https://www.lcsc.com/product-detail/C76941.html
  - Digi-Key searches for GRM033R71C103KA01D and GRM155C80J106ME11D (no results) and GRM033R71A103KA01D
    (7,365,722): https://www.digikey.com/en/products/result?keywords=GRM033R71A103KA01D
  - LCSC C237279 GRM155C80J106ME11D (S, search snippet).
