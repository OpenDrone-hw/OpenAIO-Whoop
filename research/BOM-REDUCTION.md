# OpenAIO-Whoop BOM reduction: integrated decision list

Date 2026-10-09. Read-only integration of four verified track reports. No repo file was edited.

**Track reports (each with its own Verification section):**
- `bomred/rx-vtx.md` (RV-xx): RX MCU, flash, radio, VTX control.
- `bomred/passives.md` (PS-xx): passive standardisation and lean decoupling.
- `bomred/power-esc.md` (PE-xx): power tree and ESC cells.
- `bomred/vtx-fc-misc.md` (V-xx, F-xx): VTX chain, FC support parts, misc.

Only proposals that survived verification are listed. Amendments from the verification passes are already applied
(corrected MPNs, corrected counts, corrected model numbers).

**Method.** `bomred/integ/integrate.py` and `bomred/integ/final_order.py` apply every proposal to
`hardware/bom_plan.json` and recount. Sides come from the placed floorplan (`hardware/floorplan.json`). Land extents
come from the P2 kernel (`p23/fp/work/fpinfo.json`). Numbers are in `bomred/integ/totals.json`.
- **Placements** = BOM placements (assembled parts). Pads, test points, logo and the antenna hole are out of the BOM.
- **Lines** = unique manufacturer part numbers (MPNs) in the BOM.
- **Area** uses the FLOORPLAN.md metric: land extent plus a 0.1 mm halo per side ("occupied"). Deltas come from the
  land extents and are added to the measured P2 baseline. Negative = saved. F = top, B = bottom.

**Labels.** V = verified from a primary source in the track reports, S = screened (distributor), I = inferred in
this integration.

---

## 0. The owner's question

> "I see an ESP with external flash? Look at OpenRX-Lite-UFL."

- **Yes.** The RX uses an ESP32-D0WD-V3 with an external GD25Q32EEIGR flash and an external 40 MHz crystal.
- The plan also missed a capacitor the ESP32 needs: CAP1, 10 nF, which Espressif calls "required for proper
  operation".
- **OpenRX-Lite-UFL cannot be reused as is.** It uses an ESP32-C3FH4 (in-package flash) with an SX1281, but on
  ExpressLRS (ELRS) 4.x the C3 cannot drive the VTX:
  - `rx_main.cpp` l. 91-95 compiles the VTX SPI device out on the C3 (V);
  - the C3 has a single general-purpose SPI;
  - it would use 15 of 15 usable GPIO.
- **The FC cannot take the VTX either.** Betaflight on the RP2350 has `#undef USE_VTX_RTC6705` (V), and the FC has
  no spare GPIO.
- **The in-package-flash part that works is the ESP32-PICO-V3 (BR-01).** It holds the flash, the 40 MHz crystal,
  the CAP network and most bypass capacitors inside the package.
  - It saves 12 placements.
  - It runs the stock `Unified_ESP32_2400_RX` build, with its own layout JSON.
  - With BR-06 and BR-25, the RX block goes from **32 to 19 placements**.
- **Board-wide, the "apply now" set is −41 placements and −13 lines** against the corrected baseline.

---

## 1. Totals

| | Plan (`bom_plan.json`, placed P2 board) | Corrected baseline (§2) | **After "apply now" (BR-01 to BR-26)** | "Apply now" without BR-01 (RX fallback) | "Apply now" + owner calls OC-1 to OC-3 |
|---|---|---|---|---|---|
| BOM placements | 282 (F 125 / B 157) | 286 (F 125 / B 161) | **245 (F 110 / B 135)** | 256 (F 110 / B 146) | 229 |
| of which passives | 218 | 222 | 185 | 194 | 181 |
| Unique BOM lines | 88 | 89 | **76** | 78 | 73 |
| Footprints incl. pads, test points, logo | 326 | 330 | 289 | 300 | 273 |
| Top, occupied incl. halo (usable 628.5 mm²) | 445.6 mm² (70.9 %) | 445.6 (70.9 %) | **434.3 (69.1 %)** | 434.3 (69.1 %) | 431.2 (68.6 %) + OC-1 P2 rerun |
| Bottom, occupied incl. halo (usable 616.6 mm²) | 457.5 mm² (74.2 %) | 460.6 (74.7 %) | **459.9 (74.6 %)** | 448.7 (72.8 %) | 459.2 (74.5 %) + OC-1 P2 rerun |
| Top, package only | 313.0 mm² (49.8 %) | 313.0 (49.8 %) | 306.4 (48.8 %) | 306.4 (48.8 %) | - |
| Bottom, package only | 328.0 mm² (53.2 %) | 329.8 (53.5 %) | 337.6 (54.7 %) | 322.7 (52.3 %) | - |

**Deltas of the "apply now" set**

| Against | Placements | Lines | Area, occupied incl. halo |
|---|---|---|---|
| Corrected baseline | **−41** | **−13** | **F −11.3 mm², B −0.7 mm²** |
| Plan | −37 | −12 | F −11.3, B +2.4 |

The bottom stays level because BR-01 adds 10.6 mm² there. The rest of the set frees 11.3 mm² on the bottom.

**Variants**

| Variant | Placements | Lines | Top | Bottom |
|---|---|---|---|---|
| BR-05 22 µF caps moved to the top (likely, §3 note) | 245 | 76 | 441.2 (70.2 %) | 453.0 (73.5 %) |
| BR-02 falls back to PS-12 | 248 | 76 | 436.8 (69.5 %) | unchanged |
| Worst case: BR-01 fails, BR-02 falls back, BR-17 kept | 260 | 78 | 437.4 (69.6 %) | 448.7 (72.8 %) |

The worst case is still −26 placements and −11 lines against the corrected baseline.

**Per block (plan → after)**

| Block | Plan | After |
|---|---|---|
| RX | 32 | 19 |
| VTX | 70 | 58 |
| Power | 38 | 34 (+3 corrected-baseline parts kept) |
| ESC | 20 per cell | 19 per cell (ESC3 stays at 20) |
| FC | 32 | 30 |
| IMU | 7 | 5 |
| OSD | 13 | 12 |
| LED | 7 | 4 |

---

## 2. Corrected baseline: defects, not savings

These parts are added before any saving is counted. They are not on the placed board yet.

| Item | Parts / lines | Area | Evidence |
|---|---|---|---|
| ESP32 CAP1 10 nF, pin 48 to GND, X7R ±10 % (PS-00). Only CAP1: the CAP1-CAP2 RC (RV-0a) "is not required" without Deep-sleep, and ELRS never sleeps (Espressif schematic checklist, V) | +1 / 0 | B +0.66 | ESP32 DS v5.3 Table 2-1; checklist "required for proper operation". Moot with BR-01 |
| D24 TPS2116 VIN1 capacitor | +1 / 0 | B +1.13 | spec §4.2; BR-20 sets the MPN |
| D34 O4 EN 1.5 MΩ hysteresis resistor | +1 / +1 | B +0.66 | DECISIONS D34; BR-22 sets the values |
| D34 O4 EN 100 nF filter | +1 / 0 | B +0.66 | DECISIONS D34 |
| R9 80.6k → 90.9k (D34; plan stale) | 0 / 0 | 0 | spec §4.2 |
| **Total** | **+4 / +1** | **B +3.1** | 286 placements, 89 lines |

Other baseline defects, all fixed inside the set:

| Defect | Fixed by |
|---|---|
| PA drive stage cannot turn Q1 on: Vb = 0.119 x V_PWM (PS F-A, V) | BR-02, or PS-12 if BR-02 falls back |
| LP5912 input capacitors below their effective minimum (F-D) | BR-14 |
| LP5907 output capacitor below its effective minimum (F-C) | BR-26 |
| U17 85 °C flash inside the PA shadow (RV-0b) | BR-01 removes U17; fallback §5 |

---

## 3. Apply now (no function loss, verified), ranked

**Column guide**
- **Parts** and **area** are additive.
- **Lines alone** = the proposal on its own against the corrected baseline.
- **Lines in order** = incremental in this rank order. That column sums to the total (−13).
- Area is in mm², occupied metric, F / B.

### 3.1 Placement savings

| Rank / ID | Source (verdict) | Change, exact MPNs | Parts | Lines alone / in order | Area F / B | Risk, gate |
|---|---|---|---|---|---|---|
| **BR-01** | RV-4 (confirmed, with correction); includes PS-09, PS-00 CAP1, RV-0a, RV-0b | Espressif ESP32-D0WD-V3 (U16), GigaDevice GD25Q32EEIGR (U17), CJ17-400001010B20 40 MHz (X2), C71/C72 GRM0335C1H150JA01D, C80 GRM033R61A105ME44D, C81/C74/C75/C78/C79 GRM033R61E104KE14D, C77 GRM033R61A103KA01J and CAP1 → **Espressif ESP32-PICO-V3** (LCSC C967022; alternate ESP32-PICO-V3-02). Keep C76 100 nF, C82 10 µF, R56/C73 (CHIP_PU RC), R57 (LNA_IN dummy) | **−12** (−11 vs plan) | −2 / −2 | 0 / **+10.6** | **Medium. Gate: a P2 placement trial.** The PICO is −40..85 °C (in-package flash), so under rule H3 it must sit ≥ 2 mm outside the PA projection (bottom keep-out x 4.32..12.72, y −13.4..−5.0 mm) and ≥ 2 mm from the FET groups, with check_spacing at 0. It needs its own ELRS layout JSON (§6 item 1) and a new P3 footprint and symbol. Stock: LCSC 335, DigiKey 4,812; HQ Online lists only V3-02 (443). Confirm the bootloader's handling of the in-package flash pins at V1 bring-up (I) |
| **BR-02** | V2 (confirmed; model corrected); supersedes PS-12 | Q27 Nexperia BC847QASZ, R71/R72 RC0201FR-0718KL, R73 RC0201FR-0710KL, R74 RC0201FR-076K2L, R75 RC0201FR-07150RL, R76 RC0201FR-071KL, R77 RC0201FR-073K3L, C124/C125 GRM033R61E104KE14D → **Nexperia BC857BM,315** PNP (emitter through Re to +3V3_VTX, collector to R65 → L3 → PAOUT1), 2-pole RC 2x RC0201FR-071KL + 2x GRM033R61A105ME44D, Re RC0201FR-0710RL. `vtx_amp_pwm` moves to ESP32 GPIO13 by target overlay | **−4** | −2 / −2 | **−3.2** / 0 | **Medium. Gate: P4 SPICE before schematic freeze, then V5/V8.** PAOUT1 is driven in current mode, and the RTC6705 gives that current as "TBD". Corrected model: YOLO ceiling 26-30 mA at Re 27 Ω, 49-66 mA at 10 Ω; pinch-off at ≥ 3400 counts; about 255 duty steps. Start Re at 10-15 Ω. Fixes PS F-A |
| **BR-03** | V1 (confirmed) | Q28 BC847QASZ → **ALLPOWER AP1606** (drain VTX_PWR_EN, gate HD_EN, source GND). TI LP5907SNX-2.85/NOPB (U22) VIN moves from +3V3 to **+3V3_VTX**. Delete R78/R79 RC0201FR-0710KL and R83 RC0201FR-071KL | **−3** | 0 / −1 (BC847QASZ line goes with BR-02) | 0 / −2.5 | Low. In HD mode the LDO collapse also removes PA_VREF. LP5907 VEN is rated −0.3..6 V to GND, so GPIO2 needs no series resistor. V9 adds a check for PA_VREF < 0.5 V in HD mode. See §6 item 9 for the LP5907 input |
| **BR-04** | F1 (confirmed) | Delete Nexperia 74LVC1T45GS,132 (U23) + C126/C127 GRM033R61E104KE14D. RP2350 GPIO8 drives the LED pad directly, with no series R, like the other user pads | **−3** | −1 / −1 | 0 / −3.0 | Low-moderate. A WS2812 at 5.15 V wants VIH 3.6 V. Add the Betaflight inline-diode note to the README; V9 tests a strip. Matrix II parity (`LED_STRIP_PIN PB2`, direct, V) |
| **BR-05** | PE-7 (partly refuted: −3, not −4) | Delete the EFM8 VDD 2.2 µF caps C18, C24, C36 (Murata GRM155C81A225KE11D, ESC1/2/4). Each cell's 22 µF GRM188C80J226ME15D (C23, C29, C41) moves ≤ 3 mm from EFM8 VDD pin 4. The 100 nF at the pin stays. ESC3 keeps C30 (gyro 5 mm bulk-MLCC rule) | **−3** | 0 / 0 | −3.4 / 0 | Medium-low. P5 must find the 0603 sites. The bottom under the EFM8s is taken, so the top variant is likely: F +3.5, B −6.9 instead. Bus capacitance drops 3.0-4.2 µF effective, so V3c (hot-plug test) checks it. Do not stack with PE-8 before V3c (§6 item 11) |
| **BR-06** | PS-08 = RV-3 (confirmed) | Delete C90 GRM033R61A103KA01J and C93 GRM155C80J106ME11D at the SX128x. The Semtech Table 15-1 set stays (C86, C87, C88, C89, C91), plus C92 1 µF | **−2** | 0 / 0 | 0 / −1.8 | Low. V7 checks TX droop. This is also the main lever on the LP5912 10 µF output limit |
| **BR-07** | PS-05 = PE-4 (confirmed) | Delete the INA186 common-mode caps C3, C4 (GRM033R61E104KE14D). Keep R2/R3 1k + C5 1 µF differential (80 Hz) and the R47/C60 output RC | **−2** | 0 / 0 | 0 / −1.3 | Low. The ibata_scale check catches any offset. Also removes two X5R parts that sit 0.6-0.75 mm from Q5 (H1) |
| **BR-08** | F2, includes PS-04 (confirmed) | Delete C55 (QSPI_IOVDD pin 54 shares C54 at pin 53) and C53 (ADC_AVDD pin 44 shares C49 at IOVDD pin 45) | **−2** | 0 / 0 | 0 / −1.3 | Low. P5 must put C54 ≤ 1 mm from pin 54: that pin powers the RP2354 in-package flash, and C54 is 2.9 mm away today. C49 goes at pin 44 (RP2350 DS §6.1.5). The house OpenFC-Lite-Mini flies 7 caps for these 9 pins |
| **BR-09** | PS-06 VDDIO half + PE-6 VDD half (both verified halves) | Delete C63 (+1V8 100 nF) and C64 (VDDIO 100 nF), both GRM033R61E104KE14D. C61 (1 µF, TPS7A2018 CIN) goes between U12 IN and BMI270 VDDIO pin 5. C62 (1 µF, TPS7A2018 COUT) goes at BMI270 VDD pin 8 | **−2** | 0 / 0 | −1.3 / 0 | Low. As placed, C62 lands about 3.4 mm from U12 OUT: a D33 MINOR, since the about 20 mΩ trace is under the 100 mΩ ESR limit. P5 rotates U12 so OUT faces pin 8 where it can. The gyro noise V-test stays |
| **BR-10** | PE-1 (confirmed) | TI TPS22810DBVR (U5) VIN moves from +5V to **+5V_BST** (TPS2116 VIN2 node). Delete Q1 AP1606 (the USB term of the O4 enable). C17 stays, re-netted to +5V_BST, because PE-2 was refuted | **−1** | 0 / 0 | 0 / −1.2 | Low. The mux's reverse-current blocking keeps USB off the O4 by topology. V1 checks USB + cell + HD mode. Changes D34. Side benefit: the O4 current no longer crosses the mux (0.05-0.07 W saved) |
| **BR-11** | PS-10 = PE-3 (confirmed) | Delete R6 RC0201FR-07100KL; TPS61022 EN ties to VIN (+BATT) | **−1** | 0 / 0 | 0 / −0.7 | None. EN and VIN share the −0.3..7 V absolute maximum |
| **BR-12** | PS-11 (confirmed) | Delete R69 RC0201FR-0710KL (PA_EN pull-down) | **−1** | 0 / 0 | −0.7 / 0 | Low. LP5907 EN has an internal 1 MΩ pull-down, GPIO2 has a 45 kΩ strap pull-down, and ELRS drives the pin low at init |
| **BR-13** | PS-07 (confirmed) | Delete C69. Move C70 (100 nF) to the bottom between U14 SN74LVC1G3157DTBR and U15 TLV7031DPWR (2.5 mm apart) | **−1** | 0 / 0 | −1.3 / +0.7 | Low. Needs the X6S part from BR-18, because the shared cap sits over an ESC quarter |
| **BR-14** | PS-18 amended = PE-5 | Replace C13 + C120 (2x GRM033R61A105ME44D) with one **Murata GRM155C80J106ME11D** (10 µF X6S 0402) between the U4 and U21 LP5912 IN pins (2.4 mm apart) | **−1** | 0 / 0 | 0 / −0.2 | Low. Fixes the LP5912 CIN effective minimum (> 0.5 µF) and an X5R H1 breach next to Q9/Q10 |
| **BR-15** | V4 (confirmed) | Delete C97 GRM033R61E104KE14D (RTC6705 REG1D8, pin 26), as on OpenOSD-X v1.01 C27 "(DNI)". REG1D8_1 keeps C96 470 nF | **−1** | 0 / 0 | −0.7 / 0 | Low-moderate. V5 checks video SNR |
| **BR-16** | V3 (confirmed) | RTC6705 pin 17 (AVDD_6.5, audio VCO) becomes no-connect like pin 13. Delete C99 GRM033R61E104KE14D | **−1** | 0 / 0 | −0.7 / 0 | Low-moderate. This rests on the reference only: OpenOSD-X puts 3.3k + 1 µF to GND on pin 17, not 3.3 V, while the datasheet labels it "Supply IN 3.3 V". V5 checks for no 6.5 MHz spur. Correct spec §4.8 / §16 |
| **BR-17** | V5 (confirmed, conditional) | Delete C119 GRM0335C1H100JA01D (PA output DC block). The SE5004L RFOUT has an internal DC shunt; only RFin is marked "DC block required" | **−1** | 0 / 0 | −0.7 / 0 | Low. **Gate: decided at P4 from the datasheet plus EM** (no DNP footprint is allowed on the RF line). A 10 pF 0201 at 5.8 GHz is above its self-resonance |

### 3.2 Line merges and fixes (0 placements)

| Rank / ID | Source (verdict) | Change, exact MPNs | Parts | Lines alone / in order | Area F / B | Risk, gate |
|---|---|---|---|---|---|---|
| **BR-18** | PS-01 = PE-11 (confirmed; stock corrected) | Every Murata GRM033R61E104KE14D (X5R) → **Murata GRM033C81E104KE14D** (100 nF 25 V X6S 0201) | 0 | −1 / −1 | 0 | Low. Also clears 13 X5R breaches of the ESC-quarter and PA-zone rules (H1/H3). Stock: LCSC C181047 14,900; element14 27,343. About 50 per board after the set |
| **BR-19** | PS-02 amended (PE-9 rejected) | GRM033R61A103KA01J and GRM033R71C103KA01D (listed by no distributor) → **Murata GRM033R71A103KA01D** (10 nF 10 V X7R) | 0 | −1 / −1 | 0 | None. X7R is needed for C109 (0.91 mm from the PA) and for CAP1 in the fallback. LCSC C76941 408,700; DigiKey 7.37 M |
| **BR-20** | PS-03 amended | Retire Murata GRM155C81A225KE11D. C30 (the EFM8 cap left by BR-05) and the D24 VIN1 cap → **Murata GRM155C80J106ME11D** (10 µF 6.3 V X6S 0402, same land) | 0 | −1 / −1 | 0 | Low. VIN1 must be X6S: U3 is 1.62 mm from FET Q20. **Condition:** the critique must accept a 10 µF EFM8 decoupling cap at ESC3 under the gyro 5 mm bulk-MLCC rule; the rule names pad bulk, ESC local bulk and boost Cin. If not, C30 stays at 2.2 µF and this saves 0 lines |
| **BR-21** | PS-17 (confirmed) | R41 VREG_AVDD RC0201FR-0730RL → **RC0201FR-0727RL** (the USB series line) | 0 | −1 / −1 | 0 | Low. The RC corner moves from 1.03 to 1.25 kHz |
| **BR-22** | PS-15 (confirmed) | O4 EN network: R9 / R10 / hysteresis (D34 values 90.9k / 49.9k / 1.5M) → **RC0201FR-0733KL** 33k (new line) / **RC0201FR-0718KL** 18k / **RC0201FR-07510KL** 510k | 0 | −2 / −1 (BR-02 deletes the other 18k uses) | 0 | Low. Verified: shed at 2.80-3.09 V, on again at 3.27-3.77 V, hysteresis 0.333 V, τ 1.1 ms with the 100 nF filter. Cell drain is 82 µA (spec 30 µA), negligible against a live board. Changes D34 values |
| **BR-23** | PS-13 = PE-12 feedback divider (confirmed) | Boost FB: R4 909k / R5 120k → **RC0201FR-0747KL** 47k / **RC0201FR-076K2L** 6.2k. Output 5.148 V, worst case 4.93-5.37 V, as today | 0 | −2 / −1 (BR-02 deletes R74, so 6.2k becomes R5's own line) | 0 | None. TI: keep R2 < 300 kΩ; a lower value improves noise immunity |
| **BR-24** | PE-10 (confirmed; PS-16 not taken) | R11 HD_EN pull-down RC0201FR-074K7L 4.7k → **Ralec RTT012401FTH** 2.4k (the DShot / OSD line) | 0 | −1 / −1 | 0 | None. BR-03 removes the base currents, so GPIO27 high carries about 1.4 mA. With BR-22 the reset clamp is below the 0.81-0.87 V verified with 3.3k, against VENF 1.08 V minimum; P4 recomputes it once |
| **BR-25** | RV-1 (confirmed) | Semtech SX1280IMLTRT → **Semtech SX1281IMLTRT** (OpenDrone library part). SX1280 stays on the line note as the drop-in alternate | 0 | 0 / 0 | 0 | None. One datasheet and one pinout; ELRS uses no ranging. LCSC 283, cheaper than the SX1280; HQ Online 146 vs none. The spec's pin-5 GND fix applies to the symbol |
| **BR-26** | PS-19 (confirmed, fix) | C123 (LP5907 COUT) 0201 1 µF → **Samsung CL05A475MP5NRNC** 4.7 µF 0402 | 0 | 0 / 0 | +0.5 / 0 | None. Fixes the LP5907 COUT minimum (> 0.7 µF effective). X5R is allowed there: 3.1 mm from Q16 and 16 mm from the PA |
| **Total** | | | **−41** | **−13** | **−11.3 / −0.7** | |

### 3.3 Line choices (§6 item 7)

- **R11.** 3.3k (PS-16) and 2.4k (PE-10) tie at 76 lines. 2.4k is chosen because its line survives any VTX-stage
  outcome.
- **PR1.** The PR1 merges are line-neutral once BR-02 lands:
  - PS-14 (3.3k / 1.2k) is taken only with the PS-12 fallback, where it saves 1 line;
  - PE-12's 49.9k / 18k version collapses because BR-22 removes 49.9k.

### 3.4 Lines

Lines removed (18):
- 74LVC1T45GS,132, BC847QASZ, CJ17-400001010B20, ESP32-D0WD-V3, GD25Q32EEIGR;
- GRM033R61A103KA01J, GRM033R61E104KE14D, GRM033R71C103KA01D, GRM155C81A225KE11D;
- RC0201FR-07120KL, -071M5L, -0730RL, -073K3L, -0749K9L, -074K7L, -07909KL, -0790K9L;
- SX1280IMLTRT.

Lines added (5): BC857BM,315, ESP32-PICO-V3, GRM033R71A103KA01D, RC0201FR-0733KL, SX1281IMLTRT.

---

## 4. Needs owner call (function or parity trade)

Each item is incremental on the "apply now" result.

| ID | Source (verdict) | Change, exact MPNs | Parts | Lines | Area F / B | Trade |
|---|---|---|---|---|---|---|
| **OC-1** | PE-15 (confirmed; track: not for rev1) | 12x TI CSD25310Q2 + 12x TI CSD13202Q2 → **12x AGMSEMI AGM210MAP** (P+N half-bridge, PDFN 3.3x3.3, the Matrix II stage) | **−12** | −1 | About board-neutral (spec §4.3 case b); the side split needs a P2 rerun | **For:** Matrix parity; 20 V N and P with a ±12 V gate, which removes the 12 V N-FET disconnect-surge exposure and the gate exposure to the 9.2 V TVS clamp; hot path 34.1 vs 40.2 mΩ; the CSD25310Q2 is already a consigned line (LCSC C2871649, 659). **Against:** LCSC-only (C7431169, 4,690; 0 at HQ Online), which re-opens D12, D23, D36, D45 and the P2 ESC cell; inconsistent Qg data. The track's advice: rev2, or the rev1 fallback if the CSD25310Q2 consigned buy fails |
| **OC-2** | RV-10 (confirmed; not recommended) | Delete TH1 Murata NCP03XH103F05RL and R70 / R84 RC0201FR-0710KL | −3 | −1 | −1.3 / −0.7 | Loses the O6 patch hooks: PA thermal derate and VTX power-down in pit. Stock ELRS reads no NTC and never drives GPIO21. Keep while O6 stays a release gate |
| **OC-3** | V6 = PS-O3 (no objection) | Delete R67 Yageo RC0402JR-070RL (3-pad PA VCC selector); PA_VCC becomes fixed +BATT copper | −1 | −1 | −1.8 / 0 | Loses the prototype +BATT / +5V comparison at sag. Take it after V5 or for production |
| **OC-4** | F9 (confirmed, with condition) | Delete the TP10 GND test pad (no BOM line) | 0 (−1 pad) | 0 | 0 / about −1.0 + label | Changes FCB recovery. Either FCB moves beside the J30 GND pad, which lies under the clip-on USB adapter ("battery first, hold FCB to J30 GND, release, then clip on USB"), or FCB moves to the top beside a user GND pad, which takes it off the bottom fixture |
| **OC-5** | F9b (no objection) | Delete the SWD pads TP12 / TP13 | 0 (−2 pads) | 0 | 0 / about −2.0 + labels | Loses SWD debug on a young Betaflight port. Rev2 |

OC-1 + OC-2 + OC-3 together: **229 placements, 73 lines**, F −3.1 / B −0.7 mm², plus the OC-1 P2 rerun.

---

## 5. Fallbacks and deferred items (not counted above)

### 5.1 Fallbacks for the gated items

**BR-01 trial fails** (keep the ESP32-D0WD-V3). Then these become mandatory:
- **PS-00 CAP1.** Already in the corrected baseline. It takes the BR-19 X7R part, because U16 sits in the PA
  projection.
- **RV-0b.** Move U17 GD25Q32EEIGR ≥ 2 mm out of the PA projection (west of x 4.3 or south of y −5.0 mm), or use a
  105 °C flash grade.
- **PS-09.** Delete C77 (−1 placement, B −0.7).

Result: **256 placements, 78 lines**, top 434.3 mm² (69.1 %), bottom 448.7 mm² (72.8 %).

**BR-02 fails SPICE.** Then PS-12 is mandatory, because it fixes F-A:
- R71 = R72 = R74 = RC0201FR-073K3L;
- C124 = C125 = GRM033R61A105ME44D;
- R73 omitted;
- R75 = RC0201FR-0775RL.

Add PS-14 (R7 RC0201FR-073K3L, R8 RC0201FR-071K2L) to hold 76 lines.

Result: **248 placements, 76 lines**, top 436.8 mm² (69.5 %).

### 5.2 Deferred to a test or design gate

| Item | Change | Parts / lines | Gate |
|---|---|---|---|
| PE-8 = PS-O2 | Pad bulk C1 / C2 Samsung CL10A226MO7JZNC → Murata GRM188C80J226ME15D | 0 / −1 | **After V3c.** Together with BR-05, the inferred hot-plug peak reaches 5.58-5.64 V against the EFM8 VDD absolute maximum of 5.5 V. It also fixes C2's H1 breach; otherwise P5 moves C2 ≥ 2 mm from Q19 |
| PS-O1 | R54 287R → RC0201FR-07270RL | 0 / −1 | P4-10 / V9 (OSD levels −1 to −5 %) |
| PS-O6 | Delete C92 (1 µF at the SX128x) | −1 / 0, B −0.7 | Only if the +3V3 sum stays above the LP5912 10 µF maximum (§7 item 1) |
| PE-13 | INA186A3IDCKR → INA186A3IYFDR (DSBGA-6) | 0 / 0, B −3.6 (track figure) | Area reserve if the BR-01 trial needs bottom room. 0.4 mm WCSP, surface fan-out only |
| RV-2 (refuted) | 52 MHz crystal instead of the TCXO | −2 / 0 | ELRS SX128x does no frequency correction, and FLRC needs ±20 ppm per link. Re-open only after a V7 hot / cold F500 / F1000 test of a crystal sample |
| PE-16 | Boost Cout 4x 22 µF 0603 → 2x 47 µF 0805 | −2 / +1 | No verified DC-bias curve (P3 search) |

---

## 6. Interactions between proposals

1. **RX choice vs ESP32 pins vs the PA drive pin (BR-01 x BR-02).**
   - The PICO-V3 uses GPIO16, 17, 18 and 23 for its in-package flash (Fig. 8; pins 25, 35, 36, 44, 45 NC, V).
   - So `vtx_mosi` (GPIO18) moves to GPIO14, or GPIO15 (MTDO strap), and the F8 3-wire production reads move with it.
   - `vtx_miso` (GPIO23) is left unset or put on an input-only pin (35/38/39). ELRS never reads it.
     **Superseded by D81:** written as `"vtx_miso": -1` explicitly; an omitted overlay key keeps the stock 23
     (the PICO flash DI), which SPIClass::begin() turns into an input.
   - BR-02 puts `vtx_amp_pwm` on **GPIO13**, which is free and not a strap pin on both MCUs (PINMAP §6: 13/14/16/17
     unused today). The BR-02 pin choice therefore does not depend on the BR-01 trial.
   - GPIO12 (MTDI) is then unconnected. Its internal pull-down holds the 3.3 V-flash strap, so the F18
     eFuse-before-flash order stops mattering.
   - Everything goes into the board's own layout JSON / overlay, which the board needs anyway
     (`ledidx_rgb_vtx`, VPD arrays).
2. **RX choice vs FC pins.** Neither RX option touches the FC.
   - CRSF stays on ESP32 GPIO1/3 to RP2354A GPIO0/1.
   - The FC has no spare GPIO (PINMAP F14), and Betaflight RP2350 compiles out the RTC6705 driver and SPI ELRS. No RX
     or VTX function can move to the FC (RV-7).
   - The C3 route (RV-6) is blocked by ELRS 4.x, not by FC pins.
   - BR-04 keeps the LED pad on RP2350 GPIO8, with no pin change.
3. **BR-01 vs area and H3.**
   - The PICO adds 10.6 mm² on the bottom and cannot reuse the U16 site, which is inside the PA shadow.
   - The rest of the set frees 11.3 mm² on the bottom, in scattered pockets.
   - BR-05's top variant moves another 6.9 mm² off the bottom.
   - PE-13 (−3.6 mm²) is the reserve.
   - The P2 trial must re-plan the bottom front quadrant. Its only H3-free strip holds J30, U3 and X1.
4. **BR-01 vs passives.** BR-01 makes PS-00 CAP1, PS-09 (C77), RV-0a and RV-0b moot. BR-19 still needs X7R for C109.
5. **DFM: the fine-pitch qualification goes away.**
   - BR-02, BR-03 and BR-04 remove all three 0.35 mm-pitch leadless parts (2x BC847QASZ, 74LVC1T45GS).
   - BR-01 replaces the 0.35 mm ESP32-D0WD-V3 with a 0.5 mm part.
   - Together they let the O15 NextPCB fine-pitch engineering query (EQ) and the D43 ganged-mask DRU exception be
     dropped. Without BR-01, only the ESP32 stays in the EQ.
6. **BR-02 x BR-03.**
   - The BC847QASZ line disappears only when both land (counted at BR-03).
   - Both put their loads on +3V3_VTX (the PNP emitter and the LP5907 input). HD mode then removes the VCO, the PA
     reference and the PA drive together, so D17 is intact.
7. **BR-02 vs the value merges.**
   - BR-02 deletes the other uses of 18k, 6.2k and 3.3k.
   - BR-22 and BR-23 then keep 18k and 6.2k alive as single uses, so each saves 1 line in the set instead of 2.
   - The line search over all verified value alternatives (`integrate.py`, 30 combinations per scenario) gives
     76 lines with BR-24 (2.4k) and BR-01, in both drive-stage outcomes once PS-14 is added to the PS-12 fallback.
8. **BR-03 x BR-10 (AP1606).** BR-10 deletes Q1 and BR-03 adds Q28, so the AP1606 line stays at two parts (Q26
   beeper, Q28 HD gate).
9. **BR-03 vs the LP5907 input and the +3V3_VTX rail** (I, this integration).
   - After BR-03, the LP5907 input is C122: 0201 1 µF, about 0.5 µF effective, below the 0.7 µF minimum.
   - The +3V3_VTX bulk C108 (10 µF) sits 6.5 mm from U22 on the same side (floorplan). That is inside the 1 cm
     guidance only if P5 routes +3V3_VTX directly from C108 to U22. Otherwise C122 becomes CL05A475MP5NRNC
     (0 lines, F +0.5).
   - +3V3_VTX also needs a branch of about 10 mm to the top rear-left (U22 + the drive stage), which D33 accepts.
   - The U21 output capacitance rises to about 12.3 µF nominal, about 5-6 µF effective (I). P4 checks it against the
     LP5912 10 µF maximum.
10. **GPIO27 (BR-03, BR-22, BR-24).**
    - With no base currents, the 2.4k pull-down is the only high-state load (about 1.4 mA).
    - The PS-15 clamp was verified at 0.81-0.87 V with 3.3k. A stronger 2.4k pull-down only lowers it.
11. **Hot-plug bus capacitance (BR-05 x BR-20 x PE-8).**
    - BR-05 removes 3.0-4.2 µF effective from +BATT.
    - BR-20 gives back about 1.5-2 µF at C30 (10 µF instead of 2.2 µF X6S) (I).
    - PE-8 would remove another 4-6 µF, so it waits for V3c.
12. **BR-05 x BR-20 x the gyro rule.** C30 must stay at ESC3. If the critique counts a 10 µF there as ESC bulk, C30
    stays at 2.2 µF and BR-20 saves 0 lines.
13. **BR-13 needs BR-18.** The shared OSD cap sits over an ESC quarter, so it needs the X6S part.
14. **+3V3 output capacitance (BR-01, BR-03, BR-06, BR-08, BR-09, BR-04, BR-13).**
    - The set removes C93 (10 µF), moves C122 (1 µF) to +3V3_VTX and removes about nine 100 nF caps from +3V3.
    - The rail goes from about 31 to about 19 µF nominal, about 9-10 µF effective (I). That is still at the LP5912
      10 µF limit.
    - P4 sums it with maker curves. The next levers are PS-O6, or a TLV75533PDRVR in place of U4.
15. **BR-10 x C17 x TPS2116.** C17 stays (PE-2 refuted), re-netted to +5V_BST. If P5 brings U3 VIN2 and U5 VIN within
    about 2 mm, one cap can serve both; TPS2116 VIN2 has no input cap nearby today (power track, incidental).
16. **Superseded and duplicate IDs (counted once).**

    | Kept here | Also covers |
    |---|---|
    | BR-08 (F2) | PS-04 |
    | BR-07 (PS-05) | PE-4 |
    | BR-06 (PS-08) | RV-3 |
    | BR-11 (PS-10) | PE-3 |
    | BR-18 (PS-01) | PE-11 |
    | BR-14 (PS-18) | PE-5, with the X6S MPN |
    | BR-23 (PS-13) | the PE-12 feedback half |
    | OC-3 (V6) | PS-O3 |
    | BR-02 (V2) | PS-12 (fallback) |
    | PS-O7 | PE-14 |
    | BR-09 | PS-06 and PE-6 (synthesis of their verified halves) |

    PS-11 (R69) is counted once, in BR-12, not in BR-03.

---

## 7. Open items for P3 / P4 / P5 (not reductions)

1. **+3V3 output capacitance** against the LP5912 maximum of 10 µF: sum it with maker DC-bias curves (§6 item 14).
2. **X5R parts still in the H1/H3 zones after the set:** C5, C14, C68, C56, C57, C105, C87 and C2 (C80 leaves with
   BR-01).
   - P3 gives them X6S/X7R parts, or P5 moves them.
   - A 1 µF X6S 0201 such as GRM033C81A105ME05D (P3 to confirm) replacing the whole 1 µF line keeps the line count.
3. **Orderability.**
   - GRM155C80J106ME11D (LCSC C237279 S, no DigiKey listing) now carries 8 parts.
   - BC857BM,315 and RC0201FR-0733KL stock was not checked.
   - HQ Online lists only the ESP32-PICO-V3-02.
   - TPS61022RWUR shows 0 at LCSC (O17 watch).
4. **D4 XL-1010RGBC-2812B** runs on +3V3, below its 3.5-5.5 V supply (passives F-E, inherited from
   OpenRX-Lite-UFL). Decide in P4.
5. **RTC6705 supply details (vtx track).** Pin 40 LDD2V5 lacks the reference's 51 Ω + 1 µF filter. Point C103's
   100 pF at PAVDD/BUFVDD (31/32), as in the reference.
6. **Decision log.** The apply-now items go in as **D52+**: CONTEXT says D35+, but D35-D51 are taken. They change:
   - the D17 implementation (BR-03);
   - D34 (BR-10, BR-22);
   - spec §4.8 / §16 (BR-02, BR-15, BR-16);
   - PINMAP §6 (BR-01, BR-02), F1 (BR-04) and F18 (eFuse order).
7. **BR-02 model.** Use `bomred/verify_vfm/pnp_fix.py`. The original `pnp.py` has the base-current sign reversed.
8. **Placement conditions collected from the set:**
   - BR-01 P2 trial;
   - BR-05 0603 sites ≤ 3 mm from EFM8 VDD;
   - BR-08 C54 ≤ 1 mm from pin 54, C49 at pin 44;
   - BR-09 U12 orientation;
   - BR-13 shared cap between U14 and U15;
   - BR-14 shared CIN between the U4 and U21 IN pins;
   - BR-03 C108-to-U22 path.

---

## 8. Rejected or refuted (verified)

| Item | Why not |
|---|---|
| RV-5 ESP32-U4WDH (same land, in-package flash) | Saves only 2 parts. 85 °C, so the same re-plan as BR-01. Still needs the CAP network and the 0.35 mm EQ. LCSC 0, DigiKey 0 |
| RV-6 OpenRX-Lite-UFL block (C3FH4X / ESP8685H4) | ELRS 4.x guard; one general-purpose SPI; 15/15 GPIO. Open an upstream issue: the ESP8685H4 would be ideal (105 °C, 4x4) if C3 VTX support returns |
| RV-7 VTX driven by the FC | `#undef USE_VTX_RTC6705` on RP2350, no spare GPIO, no PA loop |
| RV-8 ESP32 LEDC 8 MHz as the RTC6705 reference | Phase noise x725, 2.4 GHz harmonics, glitches on reset |
| RV-9 ESP32 DAC for the PA bias | ELRS DAC scaling defect: pit would mean high drive |
| RV-0a full CAP network | Superseded by PS-00 (CAP1 only); moot with BR-01 |
| PE-2 delete C17 | Refuted: TPS22810 recommended operating conditions give CIN ≥ 1 µF |
| PE-9 CT cap onto the X5R 10 nF | Opposite of BR-19; H3 needs X7R |
| PS-16 (R11 3.3k), PE-12 PR1 (49.9k / 18k), PS-14 (main case) | Ties or line-neutral (§3.3) |
| PE-14 / PS-O7 BEMF resistor arrays | ±5 % elements in the neutral star, fine pitch, +1 to +2 lines |
| PE-R1 to PE-R13 | Confirmed rejections: no gate resistors exist; each motor needs its own BEMF star (Bluejay V_Mux); leg caps protect the 12 V N hot loop; LP5912 merge overheats; gyro LDO kept (D33); MCU-ADC current sense fails; Schottky OR reverse-feeds the boost; O4 threshold, BAS16LD, DShot R, camera filter and C2 pads all have a job |
| VTX parts kept by the vtx track | PA VREF from a divider or GPIO, QPA9501 / TQP5525 as primary, removing the drive stage, 8 MHz 2520, deleting the BPF, U.FL → pads, VTX SPI series R, DET RC |
| Crystal sharing | 12 / 40 / 52 / 8 MHz are fixed by silicon and firmware |
| Drop RX RGB LED D4 + C83, or FC LED D6 + R86 (−2 / −1 each) | Matrix II parity (RX LED, 4 LEDs). Not proposed; the owner may ask |

---

## 9. Files

- Integration scripts: `bomred/integ/integrate.py` (scenarios, line search, owner calls) and
  `bomred/integ/final_order.py` (ranked incremental and standalone deltas).
- Numbers: `bomred/integ/totals.json`.
- Inputs: the four track reports listed at the top, `hardware/bom_plan.json`, `hardware/floorplan.json`,
  `research/FLOORPLAN.md` (usable area and measured occupancy), `research/PINMAP.md` §6, and `research/DECISIONS.md`
  (last entry D51).
