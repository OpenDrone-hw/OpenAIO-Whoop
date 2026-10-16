# BOM reduction track: VTX chain, FC support and misc

Date 2026-10-09. Read-only review; no repo file edited.

**Inputs.**
- `hardware/bom_plan.json` (329 entries, 282 BOM parts, 88 lines).
- `hardware/OpenAIO-Whoop.kicad_pcb` (placed floorplan: sides and land extents through pcbnew).
- `research/DESIGN-SPEC.md` §4.5-4.8, §8.1, PINMAP §2, §3, §6, F15, F18, F21; FLOORPLAN.md; LIBRARY.md; DECISIONS.md (D17, D26, D38, D43, D47).
- The parallel reports `bomred/passives.md` (PS-xx) and `bomred/rx-vtx.md` (RV-xx). This report does not count their items twice (§6).

**Primary sources read for this track.**
- OpenOSD-X reference schematics `043_OpenOSD-X_REFERENCE.pdf` (RTC6671 PA) and `..._RFPA5512.pdf` (ver 1.01, 15 Sep 2025), rendered from the cached clone.
- RichWave RTC6705 datasheet V0.2 (pin table, abs max).
- Skyworks SE5004L 202393B.
- TI LP5907 SNVS798.
- Raspberry Pi "Hardware design with RP2350" (RP-008280-DS-2).
- ExpressLRS `8c51826`: `src/lib/VTXSPI/devVTXSPI.cpp`, `src/python/UnifiedConfiguration.py`.
- ExpressLRS targets `42ed776`.
- OpenVTx `20dee4e` (Generic_GD32F130 target: EWRF E7082VM, Happymodel OVX30x, BETAFPV A03).
- OpenFC-Lite-Mini netlist (kicad-cli export).
- Nexperia BC857BM product page.
- Cleanflight/Betaflight LedStrip doc.

**Labels.** V = read from a primary source, S = secondary (distributor, product page), I = inferred or calculated here.

**Area method.** As passives.md: placed land extent plus the 0.2 mm body rule.
- Per part: 0201 0.66 mm², 0402 LED 0.98 mm², SOT1216 (BC847QASZ) 1.68 mm², SOT1202 (74LVC1T45GS) 1.47 mm², DFN1006-3 (AP1606, BC857BM) 1.17 mm², 3-pad 0402 selector 1.76 mm², test pad D0.8 1.0 mm² (plus its silk label).
- Sides come from the placed board.

---

## 0. Bottom line

1. **There is a real drive-stage simplification, and production firmware points to it.**
   - Commercial VTXs (OpenVTx GD32 targets) and the Happymodel ELRS AIO calibration both run their RTC6705 bias PWM in a window **0.55-1.1 V below the 3.3 V rail**. That is the signature of one rail-referenced PNP, not two NPNs (I, §1.2).
   - One Nexperia **BC857BM** plus a 2-pole RC and an emitter resistor replaces the BC847QASZ pair and its 9 passives.
   - Saving: **−4 parts**, −3.2 mm² on the top.
   - Condition: the PWM pin moves off the GPIO12 strap through the target overlay, or the eFuse is burned before the first flash.
2. **The HD gate shrinks to one AP1606**, a line the BOM already has.
   - Feed the LP5907 PA reference from +3V3_VTX instead of +3V3. The gated LDO then removes PA_VREF by itself.
   - LP5907 VEN is rated to 6 V independent of VIN (V), so GPIO2 needs no 1 kΩ series resistor.
   - Saving: **−3 parts**, −2.5 mm² on the bottom.
3. **The LED-strip translator is not needed.**
   - Betaflight/Cleanflight document the LED pad as "always between 0v to ~3.3v" straight from the CPU.
   - The Matrix II drives its "L" pad from PB2.
   - Saving: **−3 parts, −1 line**, −2.8 mm² on the bottom.
4. **Three RTC6705/PA parts the reference itself does not use:**
   - pin 17 AVDD_6.5 (audio VCO) decoupling: OpenOSD-X does not tie the pin to 3.3 V, and our audio is unused;
   - the REG1D8 capacitor: OpenOSD-X fits it as DNI;
   - the PA output DC block: the SE5004L RFOUT has an internal DC shunt, and only RFin "requires" a block.
   - Saving: **−3 parts**, −2.0 mm² on the top.
5. **RP2354A decoupling to the flown house count on +3V3.**
   - Share 53/54 (RPi guide) and 44/45 (adjacent pins). OpenFC-Lite-Mini flies 7 caps for these 9 pins.
   - Saving: **−2 parts** (−1 beyond PS-04).
6. **Kept, with numbers:**
   - LP5907 PA reference: a divider or a GPIO cannot hold 2.80-2.90 V at 10 mA.
   - 12 MHz crystal network: RPi guide minimum.
   - RP2350 SMPS inductor.
   - Gyro LDO: D33.
   - OSD front-end topology.
   - BPF and U.FL.
   - C2, RXB and FCB pads.
   - Crystal sharing is impossible: the four references are fixed by silicon and firmware (12 / 40 / 52 / 8 MHz).

**Recommended set (V1-V5, F1, F2):**

| Measure | Result |
|---|---|
| BOM parts | **−15** vs bom_plan (−13 beyond the passives set, which already contains PS-04 and PS-12) |
| Lines | −1 standalone; up to −4 if V1+V2 are both taken and passives PS-13..16 are not |
| Area | **top −5.1 mm², bottom −6.6 mm²**, plus one test pad and label |

**DFM benefit.**
- The set removes all three small 0.35 mm-pitch leadless parts: 74LVC1T45GS and 2x BC847QASZ (D38).
- Together with RV-4 (ESP32-PICO-V3, 0.5 mm pitch), the **O15 NextPCB EQ and the D43 fine-pitch ganged-mask DRU exception go away entirely**.
- Without RV-4, only the ESP32 is left in the EQ.

---

## 1. VTX chain

### 1.1 What is planned (vtx block, 70 entries, 63 in BOM)

| Group | Refs | Parts |
|---|---|---|
| RTC6705, crystal | U19, X4, C94, C95 | 4 |
| RTC6705 supply/regulator caps | C96-C103, C108 | 9 |
| Video network, loop filter | R58-R64, C104-C107 | 11 |
| PAOUT1 choke, DC block | L3, R65, C109, C110 | 4 |
| PA + RF decoupling + DET + NTC | U20, C111-C118, R66, TH1 | 11 |
| Match, BPF, U.FL | C119, FL2, J1 | 3 |
| Power: PA VCC selector, +3V3_VTX LDO, PA reference | R67, U21, C120, C121, R68, U22, C122, C123, R69, R70 | 10 |
| Drive stage | Q27 BC847QASZ, R71-R77, C124, C125 | 10 |
| HD gate | Q28 BC847QASZ, R78, R79 | 3 |
| ESP32-side series Rs | R80-R84 | 5 |

### 1.2 Market and reference evidence for the drive stage

| Design | PAOUT1 / drive stage | PA enable | Evidence |
|---|---|---|---|
| OpenOSD-X ref (RTC6671 PA) | **No drive stage.** PAOUT1 bias is a fixed R34 10 Ω from +3.3 V, L4 4.7 nH, C40 10 nF; power is set by the PA's Vref (DAC) | DAC to Vref1,2/Vref3 | V, schematic render |
| OpenOSD-X ref (RFPA5512 PA, "the PA does not have variable gain control") | **One NPN emitter follower** (2SC2712, R15 4.7 kΩ from the DAC) → R34 10 Ω → L4. Non-inverting, because its own firmware has the polarity it needs | DAC | V |
| OpenVTx GD32F130 target (EWRF E7082VM, Happymodel OVX300/303/306, BETAFPV A03) | RTC_BIAS PWM at 12 kHz with `PWM_PERIOD 3000` (`gd32f1x0/pwm.c` l. 6). Power control 2000 (max) … 2500 (min), 3000 = off (`Generic_GD32F130.c` l. 166-208). That is 66.7-83.3 % duty, **2.20-2.75 V at the RC = 0.55-1.10 V below the 3.3 V rail**; 100 % = off | VREF straight from a GPIO (`gpio_out_setup(VREF,0)`, l. 153) | V (firmware) / I (topology) |
| ELRS Happymodel AIO RX+VTX (ESP32-PICO-D4) | Overlay: 25 mW at 3183-3263 counts, 100 mW at 3133-3153 (`targets.json` l. 2190-2195). That is 76.5-79.7 % duty, **2.52-2.63 V = 0.67-0.78 V below the rail**. Firmware comments: `MAX_PWM 3700 // above 3600 does nothing`, `MIN_PWM 2000 // could be even higher… depends on HW` (devVTXSPI.cpp l. 30-31) | GPIO2 digital | V (firmware) / I (topology) |
| Matrix 1S 5IN1 II | separate MM32F003 VTX MCU + RFPA5542 (5 V PA, EOL); circuit unknown | - | V/S (track 01) |
| Happymodel CrazybeeG473 / X14 | OpenVTx firmware on a VTX MCU over SmartAudio; "VTX powered only from the battery" | - | S (track 04) |
| This plan | two-NPN inverting stage: RC² → series R → base divider → Q1 CE with Re → collector divider (ceiling) → Q2 follower; 9 passives (spec §4.8, F15) | LP5907-2.85 switched by GPIO2 | V |

**Reading (I).** Both production firmware lines turn the stage fully off near 2.75-2.9 V and saturate it near 2.2 V, on a 3.3 V rail. That window is one base-emitter drop below the rail, which is how a PNP with its emitter on 3.3 V behaves. With a two-NPN stage, the window would sit wherever the base divider puts it.

The schematics of those products are not public, so the topology stays **I**. The model below shows that the topology works against the fixed ELRS window.

### 1.3 Proposals

#### V1. HD gate = one AP1606; PA reference fed from +3V3_VTX

**Change.**
- U22 **TI LP5907SNX-2.85/NOPB** VIN moves from +3V3 to **+3V3_VTX**. This is a net change; C122 stays as its input cap.
- Q28 **Nexperia BC847QASZ** (dual NPN) is replaced by **ALLPOWER AP1606** (DFN-3L 1.0x0.6, already 2 per board: Q1, Q26):
  - drain on VTX_PWR_EN (U21 LP5912 EN);
  - gate on HD_EN (GPIO27, R11 pull-down);
  - source on GND.
- Delete:
  - R78 and R79 (base resistors; a FET gate needs none);
  - R83 (1 kΩ GPIO2 → PA_EN series). Nothing fights GPIO2 any more.
- R69 goes as **PS-11** (LP5907 EN has an internal 1 MΩ pull-down). It is not counted here.

**How it works.**
- HD_EN high turns the FET on, which pulls the LP5912 EN low.
- +3V3_VTX collapses, so the RTC6705, the drive stage **and the PA reference** are all unpowered.
- PA_VREF = 0 V, so the PA is off whatever GPIO2 does. D17's "whatever ELRS does" still holds.

**Checks.**
- **LP5907 VEN abs max is −0.3 to 6 V, not referenced to VIN** (SNVS798 §5.1, V). With VIN = 0 and GPIO2 high, EN stays inside its rating, so no series resistor is needed.
- **Supply headroom.** LP5907 VIN min is 2.2 V. Dropout is 120 mV typical at full load and a few mV at the ~10 mA VREF load (V/I). 3.3 V in for 2.85 V out is fine.
- **LP5912 U21 load.** It rises by about 10 mA, adding about 18 mW in the LDO (I).
- **AP1606.** Vgs(th) 1.2 V (S, spec §4.5). It already switches from 3.3 V GPIO17 in the house beeper stage (flown).
- **HD_EN load.** It drops by 0.53 mA (no more base currents), which also helps PS-15/16.

**Deltas.**
- Parts −3 (R78, R79, R83; the Q swap is 0).
- Lines 0: AP1606 exists, and BC847QASZ stays for Q27 unless V2 is taken.
- Area bottom −2.49 mm².
- Removes one 0.35 mm-pitch part from the O15 EQ.

**Risk: low.** In HD mode the PA reference now depends on +3V3_VTX discharging. That is the LP5912 active discharge, plus the 10 mA VREF load pulling PA_VREF down in microseconds. V9 already measures +3V3_VTX < 0.5 V in HD mode; add PA_VREF < 0.5 V.

**Recommend: yes.**

#### V2. Drive stage = one rail-referenced PNP

**Change.** Delete Q27 BC847QASZ, R71-R77 and C124, C125 (10 parts). Add 6 parts:

| New part | MPN | Role |
|---|---|---|
| Q | **Nexperia BC857BM,315** (PNP 45 V / 100 mA, hFE 220-475, DFN1006-3 SOT883, 0.65 mm-class pad pitch; production, AEC-Q101, S) | emitter via Re to **+3V3_VTX**, collector → R65 10 Ω → L3 → PAOUT1 |
| R1, R2 | RC0201FR-071KL (2x 1 kΩ) | 2-pole RC from the PWM pin; R2 feeds the base |
| C1, C2 | GRM033R61A105ME44D (2x 1 µF) | RC poles |
| Re | RC0201FR-0727RL (27 Ω, the USB line) | sets the YOLO current ceiling and the slope; **V5 sets it**, replacing the collector-divider knob |

**PWM pin.** Move `vtx_amp_pwm` from GPIO12 to a free non-strap GPIO (GPIO13; GPIO16 or 17 on the D0WD) with the target **overlay**:
- `UnifiedConfiguration.py` l. 57-58 applies `hardware.update(config['overlay'])`, so any layout key can be overridden (V).
- The board already needs its own overlay (`ledidx_rgb_vtx`, VPD arrays).
- Alternative: keep GPIO12 and burn the VDD_SDIO eFuse **before** the first flash write. F18 burns it in the same session today, so only the order changes.

**Model** (I, `bomred/vfm/pnp.py`; 1k/1µF x2, Veb 0.65 V at 1 mA, 59.5 mV/dec, base current through the RC included):

| Re / hFE | Ic at YOLO (2000) | 2500 | 3000 | 3200 | 3300 | ≥ 3400 (incl. pit 3700) |
|---|---|---|---|---|---|---|
| 27 Ω / 220 | 52 mA | 30 | 9.7 | 2.6 | 0.5 | 0 |
| 27 Ω / 475 | 41 mA | 24 | 7.9 | 2.3 | 0.5 | 0 |
| 33 Ω / 220 | 39 mA | 23 | 7.6 | 2.2 | 0.5 | 0 |

- The 10-90 % span is about 1000 counts, about 250 real duty steps (spec asks ≥ 20 between 25 and 100 mW).
- Pinch-off at about 3300-3400 counts matches the Happymodel calibration (3133-3263).
- RC: dominant pole 61 Hz nominal (about 100 Hz with 0201 DC bias). About −70 dB at 10 kHz, against the spec's ≤ 100 Hz and ≥ 40 dB.
- PNP dissipation ≤ about 80 mW at 52 mA, against Ptot 250 mW (S). V8's PAOUT1 current measurement still applies, as in the spec.

**Strap analysis (why the pin moves).** A PNP on GPIO12 pulls the strap pin to (3.3 − 0.6) · 45k/(45k + 2k) ≈ **2.6 V at reset**, through its base current into the internal pull-down. So it is strap-unsafe unless the eFuse is burned first, or the pin moves. The current two-NPN stage is strap-safe by construction; that is the trade.

**Deltas.**
- Parts **−4** vs plan (−3 vs the PS-12 version, which drops R73).
- Lines vs plan:
  - standalone: +1 (BC857BM; BC847QASZ stays for Q28), and 18k, 6.2k and 3.3k lose their only uses (−3), so net −2;
  - with V1: −3;
  - if passives PS-13/14/15/16 reuse 18k/6.2k/3.3k: +1 standalone, 0 with V1.
- Area **top −3.15 mm²** (−7.62 removed, +4.47 added), all in the D47 rear-left pocket.

**Risk: medium.**
1. PAOUT1 is fed in current mode, whereas OpenOSD-X 5512 uses voltage mode. The RTC6705 gives the PAOUT1 current as "TBD". P4 SPICE plus V5/V8 confirm.
2. Veb tempco (−2 mV/K) moves the open-loop point. ELRS closes the loop on VPD at 25 and 100 mW. YOLO is current-limited by Re, so its ceiling moves only through hFE (±12 % in the model).
3. The pin moves away from the stock layout's GPIO12 (overlay only, no code).
- The two production lines above are evidence that this class of stage ships.

**Recommend: yes, as P4's default, with SPICE before the schematic freeze.** The fallback is the plan's stage with the PS-12 values.

#### V3. RTC6705 pin 17 (AVDD_6.5) no-connect like pin 13; delete C99

**Evidence.**
- Datasheet pin table: pin 13 "3.3V power supply for audio 6MHz VCO", pin 17 "3.3V power supply for audio 6.5Mz VCO" (V).
- OpenOSD-X **uses** 6.5 MHz audio (AOUT2/ACP2/AVT2/RF_VT2 networks). Even so, its pin 17 goes only to **R13 3.3 kΩ + C16 1 µF to GND, not to +3.3 V**, and pin 13 is NC (V, both variants).
- Our plan has no audio:
  - pins 11, 14-16 and 19-21 carry no network in bom_plan;
  - pin 13 is already NC (spec NC list);
  - yet C99 ties pin 17 to +3V3_VTX "as a 3.3 V supply".
- Spec §4.8 / §16 say "pin 17 is AVDD_6.5, a 3.3 V supply, and stays", citing the OpenOSD-X list. The reference does not show that.
- The OpenVTX sibling plan (unbuilt) powers 13 and 17 both, which is at least consistent. Our plan powers one and not the other.

**Change.** Pin 17 NC; the pad may be trimmed with the others. C99 GRM033R61E104KE14D deleted.

**Deltas.** −1 part, 0 lines, top −0.66 mm².

**Risk: low-moderate** (undocumented internals). V5 checks the video, the carrier and the absence of a 6.5 MHz subcarrier. If P4 prefers literal reference parity, the alternative is R13/C16 (+1 part vs today), not a 3.3 V tie.

**Recommend: yes.**

#### V4. RTC6705 REG1D8 (pin 26) capacitor removed, as in the reference

**Evidence.**
- OpenOSD-X v1.01: C27 0.01 µF on REG1D8 marked **(DNI)**; REG1D8_1 keeps C25 0.47 µF (V).
- The plan has C97 100 nF on REG1D8 (from the unbuilt OpenVTX sibling plan).

**Change.** Delete C97. Keep C96 470 nF on REG1D8_1 (reference C25).

**Deltas.** −1 part, 0 lines, top −0.66 mm².

**Risk: low-moderate.** This is an internal 1.8 V regulator output for the video path. Reference parity is the argument; V5 checks video SNR. No DNP pad (owner lean rule).

**Recommend: yes.**

#### V5. PA output DC block C119 removed

**Evidence.**
- SE5004L 202393B: "RFIN and RFOUT include DC shunt to Ground. External blocking capacitors are recommended."
- Pin table: only pin 3 RFin says "DC block required"; pin 13 RF OUT has no such note (V).
- RFOUT therefore sits at 0 V DC. The LTCC BPF and every whoop antenna carry no DC, so a series cap blocks nothing.
- C110 (RFin) stays: PAOUT1 is DC-biased through L3 and would short into the RFin shunt.
- Counter-evidence: OpenOSD-X fits C37 10 pF at its PA output (V).

**Change.** Delete C119 GRM0335C1H100JA01D. The PA RF OUT feeds the BPF directly; one less wide RF pad in `RF_PAD_CUTOUT`.

**Deltas.** −1 part, 0 lines (the 10 pF line stays for C110), top −0.66 mm².

**Risk: low.** If the P5 VNA shows the series element is needed as match, the 10 pF goes back (the spec allows no DNP footprint, so decide at P4/P5 from the EK1 layout).

**Recommend: yes, conditional on the P5 VNA.**

#### V6. PA VCC selector R67 → fixed +BATT copper

**Evidence.**
- The SE5004L is rated 3.0-5.5 V.
- Spec §4.8 default = +BATT, and §5.1 budgets the PA on +BATT.
- CrazybeeG473 "VTX powered only from the battery" (S).
- The selector exists only for the prototype A/B against +5V.

**Change.** Delete R67 RC0402JR-070RL and its 3-pad land; solid PA_VCC copper from +BATT.

**Deltas.** −1 part, **−1 line** (only use), top −1.76 mm², plus wider PA supply copper.

**Risk.** It gives up the bench comparison at 3.0 V sag (400 mW not guaranteed there, already accepted). Same as **PS-O3**.

**Recommend: no for rev1** (owner decision); yes at rev2 or after V5.

#### Rejected or kept, with reasons

| Idea | Why not |
|---|---|
| **PA bias (VREF) from a divider instead of the LDO** | SE5004L VREF H is 2.80-2.90 V at IEN 10 mA typical (internal 2 kΩ pull-down; no min/max for IEN; V). A series resistor from 3.3 V would be 45 Ω; IEN 7-13 mA and ±2 % on 3.3 V give 2.65-3.05 V, outside the window both ways. A divider stiff enough (< 8 Ω Thevenin) would burn about 0.4 A. It also needs a switch for pit (GPIO2). Keep the LP5907 (V1 makes it cheaper to gate) |
| VREF straight from GPIO2 (the OpenVTx practice with RFPA5542/RTC6659E-class logic-EN PAs) | Fine for a logic EN pin. The SE5004L needs a reference; the ESP32 driver is 25-45 Ω, so ±0.1 V (spec §4.8). It also loses D17's hardware hold-off of the PA bias. Revisit only with a logic-EN PA |
| QPA9501 / TQP5525 (logic PA_EN, same land) as primary | Would delete LP5907 + 2 caps (−3 parts, −1 line). But LCSC 124 / 25 pcs, recommended VCC ≥ 3.15 V (a sagging 1S cell goes below), Icq 350 mA. Keep as the documented same-land fallback; re-evaluate if stocked |
| **Remove the drive stage entirely** (OpenOSD-X RTC6671 style: fixed PAOUT1 bias, power from Vref) | ELRS has no analog Vref output, and its PWM is the power control. Fixed bias = one power level, which fails Matrix parity (25/100/400). The ESP32 DAC route is broken in stock ELRS: on GPIO25/26 `vtxMinPWM = 1`, `vtxMaxPWM = 250` and `dacWrite(pin, vtxSPIPWM >> 4)`, so DAC codes 0-15 only (devVTXSPI.cpp l. 166-168, 376-381; RV-9) |
| ESP32 LEDC 8 MHz instead of X4 | RV-8 (phase noise x725, 2.4 GHz harmonics, glitches on reset) |
| 8 MHz in 2520, or a 2520 oscillator | No exactly-8 MHz 2520 crystal found again (search). A 2520 oscillator saves at most 1 part, adds 2-5 mA, and RTC6705 XTAL1 external-clock drive is undocumented |
| Delete BPF FL2 (Matrix has none) | SE5004L 2f/3f at −45 dBm/MHz sits at the EN 300 440 limit (track 04); the lean rule allows parts that fix a real error. Keep |
| U.FL → coax solder pads | Whoop antennas ship with U.FL (market). Keep |
| Delete the 1 kΩ VTX SPI series resistors (R80-R82) | RTC6705 "Vlog −0.5 to +5 V" (V) hints at inputs without a VDD clamp, but the same 5 V is given for Vdd, and the SPI pins have internal pull-ups to VDD. VTX_SPI.CS idles high in HD mode. Keep (R81, CLK idle low, could go; −1 part, not worth the asymmetry) |
| TH1 NTC + R70, R84 GPIO21 series | O6 patch hooks, owner decision (RV-10). GPIO34 has no internal pull resistors (ESP32 GPIO34-39), so R70 cannot become an internal pull |
| DET RC (R66, C117) | The DET trace crosses sides from the PA to GPIO4. Keep the 1 kΩ / 100 pF isolation |
| RTC6705 video network, loop filter, PAOUT1 L/R/C, PA EK1 caps | Reference values (OpenOSD-X, Skyworks EK1). Keep |

#### Findings on the RTC6705 supply pins (no part-count change; for P4)

1. **Pin 40 (LDD2V5, "analog power supply for VCO").** OpenOSD-X feeds it through **R28 51 Ω + C24 1 µF**, a 3 kHz VCO-supply filter. The plan ties it straight to +3V3_VTX with C102 100 pF. Under the lean rule this stays as planned, but the deviation must be on P4's checklist: VCO supply noise shows up as video noise and spurs.
2. **The 100 pF RF bypass.** The reference's only 100 pF (C31) sits on **PAVDD/BUFVDD (31/32)**, the buffer and PA-bias supply. The plan has two 100 pF at the VCO (C102 "39/40", C103 "VCO supply") and only 100 nF (C101) on 30/31/32. P4: point C103 at 31/32. This is the same count and the reference placement.

---

## 2. PIO OSD front end (13 parts)

Every part was compared with the flown house `osd` sheet (OpenFC-Lite-Mini netlist, V) and the RTC6705 input:
- TLV7031 IN− = GND, IN+ = clamped VID_DC;
- the SN74LVC1G3157 B1 = camera, B2 = OSD level.

| Part | Keep? | Reason |
|---|---|---|
| U14 switch, U15 comparator | keep | The Betaflight PIO FB OSD drives OSD_EN (switch) and reads OSD_SYNC. A resistive overlay without the switch mixes the camera into the OSD pixels. RP2350 pads (VIL 0.8 / VIH 2.0 V) cannot see a 0.3 V sync step without the comparator |
| D3 + C68 (clamp), R55 + C67 (sync filter) | keep | the clamp sets the sync tips just below 0 V for the IN− = GND comparator; house parity (flown) |
| R51 75 Ω | keep | camera termination. The RTC6705 network presents about 1.47 kΩ at low frequency (R24 1.2k + R25 270), and the RTC6705 spec is "Zin_video 75 Ω (as reference design)" (V). Without R51 the video level roughly doubles (I) |
| R52/R53/R54 level network | keep 3 | black must sit about 0.3 V above sync with OSD_W low, so a bias to 3V3 plus a ratio to GND is needed: three resistors is the minimum for two levels with an offset |
| C66 100 pF | keep | RF shunt at the video entry next to a 5.8 GHz PA (passives also keeps it) |
| C69/C70 | one shared | **PS-07** (not counted here) |

**Result: no topology reduction.** The OSD block is already the house sheet minus the COS8051 buffer and its 3 resistors.

---

## 3. RP2354A support parts

Comparison: RPi "Hardware design with RP2350" against the house OpenFC-Lite-Mini (flown RP2354A, kicad-cli netlist, V) and the plan.

| Item | RPi guide | House (flown) | Plan | Verdict |
|---|---|---|---|---|
| 100 nF on IOVDD x6, ADC_AVDD, USB_OTP, QSPI_IOVDD (9 pins, +3V3) | "100 nF capacitor per power pin", except pins 53 and 54, which "share a single capacitor (C12)" → 8 | **7** (C5, C7, C8, C9, C11, C12, C13) | 9 | **7** (F2) |
| 100 nF on DVDD x3 (+1V1) | 3 | 2, plus 2x 4.7 µF on +1V1 | 3 + 1x 4.7 µF | keep 3: dropping one would go below both the guide and the house, which compensates with a second 4.7 µF |
| 4.7 µF VREG_VIN, VREG_AVDD (RC), +1V1 | C6, C7, C9 (3) | 4 | 3 | keep |
| VREG_AVDD R | 33 Ω | 30 Ω | 30 Ω (PS-17: 27 Ω) | keep |
| SMPS inductor | AOTA-B201610S3R3-101-T | same | same | keep: the RP2350 core regulator is a buck; no LDO mode at load |
| Crystal | ABM8-272-T3 + 2x 15 pF + **1 kΩ** ("prevent the crystal being over-driven"); "any deviation … will require extensive testing" | 2520 + 2x 20 pF + 1 kΩ | X252012MMB4SI + 2x 15 pF + 1 kΩ | keep (guide minimum) |
| QSPI_SS boot | R6 1 kΩ "important to include" | 10 kΩ + button | R44 1 kΩ to the FCB pad | keep |
| RUN | can tie high | tied to +3.3 V | tied to +3V3, 0 parts | already minimal |
| USB | "require 27 Ω series termination resistors" | 30 Ω | 27 Ω x2 | keep |
| Flash | RP2354: "U3 can safely be removed" | in-package | in-package, QSPI pins NC | already minimal |

### F2. RP2354A +3V3 decoupling 9 → 7

**Change.**
- Delete C55: QSPI_IOVDD pin 54 shares C54 at pin 53 (this is **PS-04**).
- Delete C53: ADC_AVDD pin 44 shares C49 at IOVDD pin 45. They are adjacent pins on the same +3V3 net, and the ADC only reads VBAT and current.

**Evidence.** RPi guide §2.2.1 (V); house netlist shows 7x 100 nF for the same 9 pins (V).

**Deltas.** −2 parts (−1 beyond PS-04), 0 lines, bottom −1.32 mm².

**Risk: low.** Place C49 between pins 44 and 45 (≤ 0.6 mm stub).

**Recommend: yes.**

### Crystal sharing and other clock ideas (rejected)

- **Frequencies are fixed:**
  - the RTC6705 needs exactly 8 MHz (ELRS R = 400, `SYNTH_REG_A_DEFAULT 0x0190`);
  - the SX1280 needs 52 MHz (FREQ_STEP);
  - the ESP32 needs 40 MHz;
  - the RP2350 BOOTSEL USB expects 12 MHz unless OTP is programmed.
- **No clock outputs are free.**
  - RP2350 GPOUT pins (GPIO21/23/24/25) carry FLASH_CS and the motors.
  - ESP32 CLK_OUT pins (GPIO0/1/3) carry RXB and UART0.
  - The FC must not depend on the RX MCU's clock or reset.
- **A 12 MHz oscillator into XIN** (allowed by the guide: "a clock source with a CMOS output … into the XIN pin") saves 2 parts, but adds an active part (mA, cost). Market and house practice is the crystal. Not recommended.

---

## 4. Misc: gyro LDO, LEDs, beeper, LED strip, test pads

### F1. LED-strip translator removed (direct drive from GPIO8)

**Change.** Delete U23 **Nexperia 74LVC1T45GS,132** and C126, C127. GPIO8 (PIO1 ws2812) goes straight to the LED pad.

**Evidence.**
- Betaflight/Cleanflight LedStrip doc: "The LED pin on the CPU will always be between 0v to ~3.3v". Its remedy for marginal strips is on the strip side: "drop the VIN to less than 4.7v … by using an inline diode" (V).
- Matrix II: LED pad "L" = PB2 in the BETAFPVG473_V2 config (V); no buffer was identified on the photos (I).
- BetaFPV LED board rated 3.3-5.2 V (S, GetFPV).
- RP2350 GPIO0-25 are FT pads.
- Market default: no translator.

**Deltas.**
- Parts −3, **lines −1**, bottom −2.79 mm².
- Removes a 0.35 mm-pitch part from the O15 EQ and the D43 rule scope.
- The 5 V decoupling at the pad area goes too.

**Risk: low-moderate.** A WS2812 at 5.15 V formally wants VIH 0.7·VDD = 3.6 V; some strips may glitch. README note (inline diode on the strip 5 V); V9 tests a BetaFPV whoop LED board and a WS2812B strip. PINMAP F1 already lists direct drive as option (a).

**Recommend: yes.**

### Kept

| Item | Plan | Reason |
|---|---|---|
| Gyro LDO U12 TPS7A2018 + C61, C62 | keep | D33 ("gyro supply basics" not sacrificed); house imu sheet uses its own LP5912-1.8; FusionFPV UD "BMI270 with dedicated low-noise supply". An RC filter from +3V3 would save 1 part, but its PSRR at ESC frequencies is far below an LDO. PS-06 shares the caps with the gyro pins |
| FC LEDs D5, D6 + R85, R86 | keep 2 | the Matrix II has 4 LEDs (FC green + blue, VTX, RX); this board has 3. Dropping LED1 (−2 parts, −1 line, frees GPIO26) is possible but loses parity. Two GPIO sinks cannot share a resistor. LED current without a resistor relies on pad impedance: out of rating |
| Beeper Q26 AP1606 + R48 | keep | Matrix uses a low-side transistor; the house has the same pair. An active buzzer draws 20-30 mA at 5 V, too much for a GPIO. R48: PS-O4 (keep) |

### F9. Test pads (out of the BOM: area and labels only, no placements)

| Pad | Verdict | Reason |
|---|---|---|
| TP10 GND (−6.2, −5.2) | **drop** | it serves only FCB (TP9 next to it). Place FCB next to the pogo GND (J30, 6 mm away) or a user GND pad; the fixture already contacts GND on J30 and the battery pad. −1 pad + label, about −1.0 mm² pad and −1.6 mm² silk keep-clear on the bottom |
| TP12/TP13 SWD (CLK/DIO) | keep for rev1, drop at rev2 | the house OpenFC-Lite-Mini leaves SWD unconnected, and UF2 + BOOTSEL (FCB) recovers any firmware. Rev1 is a bring-up board for a young Betaflight port; FusionFPV UD keeps SWD |
| TP9 FCB, TP11 RXB | keep | BOOTSEL and ESP32 download strap for the first flash (F18) |
| TP1-TP8 C2D/C2CK x4 | keep | blank EFM8s have no bootloader (F18). C2CK = RSTb cannot be shared: the EFM8 drives RSTb low on its own resets, so one ESC would reset all four |

---

## 5. Proposal table

Deltas are against `bom_plan.json` as it is, each proposal standalone. Area in mm² per side; negative = saved.

| ID | Change (MPNs) | Parts | Lines | Area | Risk | Rec. |
|---|---|---|---|---|---|---|
| V1 | Q28 BC847QASZ → ALLPOWER AP1606 on VTX_PWR_EN; LP5907SNX-2.85 VIN → +3V3_VTX; delete R78, R79, R83 (RC0201FR-0710KL x2, RC0201FR-071KL) | −3 | 0 | B −2.49 | low; V9 adds PA_VREF < 0.5 V in HD mode | **yes** |
| V2 | Q27 BC847QASZ + R71-R77 + C124, C125 → Nexperia BC857BM,315 + 2x RC0201FR-071KL + 2x GRM033R61A105ME44D + RC0201FR-0727RL (Re); `vtx_amp_pwm` to GPIO13 by target overlay (or eFuse before the first flash) | −4 | −2 (−3 with V1; 0 to +1 if PS-13..16 reuse 18k/6.2k/3.3k) | T −3.15 | medium: current-mode PAOUT1 drive; P4 SPICE, V5/V8 | **yes** (P4 default, SPICE first) |
| V3 | RTC6705 pin 17 NC (as pin 13); delete C99 GRM033R61E104KE14D | −1 | 0 | T −0.66 | low-moderate; V5 video check | **yes** |
| V4 | Delete C97 (REG1D8) GRM033R61E104KE14D, as OpenOSD-X C27 DNI | −1 | 0 | T −0.66 | low-moderate; V5 video SNR | **yes** |
| V5 | Delete PA output DC block C119 GRM0335C1H100JA01D (RFOUT has an internal DC shunt) | −1 | 0 | T −0.66 | low; P5 VNA | **yes** (conditional) |
| V6 | Delete PA VCC selector R67 RC0402JR-070RL → fixed +BATT copper (= PS-O3) | −1 | −1 | T −1.76 | loses the prototype +5V A/B | no for rev1 |
| F1 | Delete LED-strip translator 74LVC1T45GS,132 + C126, C127 (GRM033R61E104KE14D); direct GPIO8 drive | −3 | −1 | B −2.79 | low-moderate: strip VIH at 5 V; README diode note; V9 | **yes** |
| F2 | RP2354A: delete C55 (= PS-04) and C53 (ADC_AVDD shares IOVDD pin 45) | −2 | 0 | B −1.32 | low | **yes** |
| F9 | Delete TP10 GND test pad; FCB next to the pogo GND | 0 (pad) | 0 | B −1.0 + label | none | **yes** |
| F9b | Delete SWD pads TP12/TP13 | 0 (pads) | 0 | B −2.0 + labels | loses SWD debug | rev2 |

**Sum of the recommended set (V1-V5, F1, F2, F9):**
- **−15 BOM parts**;
- lines −1 standalone (−4 with V1+V2 and without the passives value merges);
- **top −5.13 mm², bottom −6.60 mm²**, plus −1 test pad.

The O15 EQ then holds only the ESP32; with RV-4 it is gone.

---

## 6. Interaction with the other tracks (do not double count)

| Here | Other track | Rule |
|---|---|---|
| F2 | PS-04 (C55) | F2 includes PS-04; incremental −1 |
| V2 | PS-12 (re-derived two-NPN values, −1) | V2 supersedes PS-12 if taken; PS-12 is the fallback and still fixes passives finding F-A (Q1 never turns on with the planned values) |
| V1 | PS-11 (R69) | R69 is counted in PS-11; V1 needs it gone or kept, either works |
| V1 | PS-19 (LP5907 COUT 0402) | still applies. With VIN on +3V3_VTX, C122 can merge with the +3V3_VTX bulk only if P5 places U22 within about 2 mm of C121/C108 (U21 sits on the other side today, D47): optional −1 |
| V1, V2 | PS-15/16 (HD_EN pull-down, O4 EN values) | V1 removes 0.53 mA of base current from GPIO27, so PS-16's 3.3k is not needed for drive. Check the reset clamp only |
| V2 | RV-4 (ESP32-PICO-V3 layout JSON) | both need the board's own target entry; with the PICO, GPIO16/17/18/23 are flash, so pick the PWM pin from the free ones (GPIO13 or 14) in the same JSON |
| V6 | PS-O3 | same item |
| (rejected) LEDC 8 MHz, DAC drive, NTC | RV-8, RV-9, RV-10 | same verdicts |

---

## 7. Checks handed to P4 / P5

1. **V2 SPICE.** PNP stage into a PAOUT1 load model, with the V8 PAOUT1 current. Set Re for the ≤ 27 dBm ceiling (V5); choose the overlay GPIO (13) and add it to PINMAP §6 and the target JSON.
2. **V1.** Redraw the D17 HD gate. PINMAP F21 text: "AP1606 pulls the +3V3_VTX LDO EN low; the PA reference is fed from +3V3_VTX". V9 adds PA_VREF < 0.5 V in HD mode.
3. **V3/V4.** RTC6705 pin table in the schematic: 13 and 17 NC, REG1D8 open, REG1D8_1 470 nF. Correct spec §4.8 / §16 "pin 17 … a 3.3 V supply".
4. **RTC6705 supply findings (§1.3).** Pin 40 LDD2V5 filter (reference 51 Ω / 1 µF) and the 100 pF at PAVDD/BUFVDD.
5. **F1.** README LED-strip note; V9 strip test.
6. **F9.** Move FCB next to a GND contact; update the fixture map (F18).

---

## Sources

**Cached clones and files:**
- OpenOSD-X `doc/043_OpenOSD-X_REFERENCE.pdf` and `043_OpenOSD-X_REFERENCE_RFPA5512.pdf` (ver 1.01, 2025-09-15), rendered to `bomred/vfm/`.
- ExpressLRS `8c51826`:
  - `src/lib/VTXSPI/devVTXSPI.cpp` l. 22, 27-31, 143-197, 251-279, 369-391;
  - `src/python/UnifiedConfiguration.py` l. 57-58.
- ExpressLRS targets `42ed776`:
  - `RX/Generic 2400 Whoop Rx and VTx.json`;
  - `targets.json` l. 2187-2201 (HappyModel AIO overlay).
- OpenVTx `20dee4e`:
  - `src/src/gd32f1x0/pwm.c` l. 6, 99-130;
  - `src/src/targets/Generic_GD32F130/Generic_GD32F130.c` l. 153-210;
  - `Generic_GD32F130.h` (VREF PA0, RTC_BIAS PB5).
- OpenFC-Lite-Mini netlist and BOM (kicad-cli 10 export, `bomred/sib/ofc.xml`, `OpenFC-Lite-Mini.csv`).

**Datasheets:**
- RichWave RTC6705-DST-001 V0.2: pin table (pins 13, 17, 23, 26, 40), abs max (`scratchpad/rtc.txt`).
- Skyworks SE5004L 202393B: front page note, pin table, VREF / IEN table (`elrev1/txt/se5004l.txt`).
- TI LP5907 SNVS798: §5.1 VEN −0.3 to 6 V, §5.3, pin table EN 1 MΩ pull-down (`bomred/pwr/ds/lp5907.txt`).
- Raspberry Pi, Hardware design with RP2350 (RP-008280-DS-2), §2.1, §2.2.1, §3.1, §4, §4.1, §5.4: https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf (`bomred/dl/hw-rp2350.txt`).

**Web:**
- Nexperia BC857BM: https://www.nexperia.com/product/BC857BM (PNP, SOT883, 45 V / 100 mA, production; search snippet: hFE 220-475, Ptot 250 mW, BC857BM,315; S).
- Cleanflight LedStrip doc (inherited by Betaflight): https://cleanflight.readthedocs.io/en/stable/LedStrip/
- BetaFPV LED board (3.3-5.2 V): https://www.getfpv.com/betafpv-led-board-2-pcs.html (S).

**Repo:** `hardware/bom_plan.json`, `hardware/OpenAIO-Whoop.kicad_pcb` (pcbnew land extents), `research/DESIGN-SPEC.md` §4.5-4.8, §8.1, `PINMAP.md` §2, §3, §6 (F1, F15, F18, F21), `DECISIONS.md` D17, D26, D38, D43, D47; `scratchpad/research/01-matrix-1s-5in1-ii.md`, `04-vtx-osd.md`.

**Model:** `bomred/vfm/pnp.py` (single-PNP transfer over the ELRS window, strap voltage).

---

## Verification

Date 2026-10-09. This is an adversarial pass over the §5 proposals against primary sources. It is read-only: no repo file was edited. Labels are as above (V/S/I).

**Re-read for this pass.**
- TI LP5907 SNVS798Q §5.1, §5.3, §6.3.1.
- TI LP5912 §7.6 and RAD.
- Skyworks SE5004L 202393B pp. 1-3.
- RichWave RTC6705 DST V0.2 pin table.
- OpenOSD-X ver 1.01: both PDFs, re-rendered at 300 dpi to `bomred/verify_vfm/r/`.
- ExpressLRS `8c51826`: `devVTXSPI.cpp`, `PWM_ESP32.cpp`, `UnifiedConfiguration.py`.
- ExpressLRS targets `42ed776`: `targets.json` and `RX/Generic 2400 Whoop Rx and VTx.json`.
- OpenVTx `20dee4e`: `gd32f1x0/pwm.c`, `Generic_GD32F130.c`.
- RP2350 datasheet §6.1.5 and the RPi hardware guide §2.2.1.
- OpenFC-Lite-Mini netlist and `OpenFC.kicad_pcb` (pcbnew pad distances).
- ESP32 datasheet strap table.
- betaflight/config `1e3f778` `BETAFPVG473_V2`.
- Nexperia BC857BM page and parametrics.
- Cleanflight LedStrip doc.
- `hardware/bom_plan.json` and `hardware/OpenAIO-Whoop.kicad_pcb`.

| ID | Verdict | Evidence (one line) |
|---|---|---|
| V1 | **confirmed** | LP5907 §5.1: VEN −0.3..6 V, "with respect to the GND pin", not VIN; §6.3.1: 1 MΩ EN pull-down (V). With +3V3_VTX at 0 V (LP5912 RAD 100 Ω, V), PA_VREF decays through the SE5004L internal 2 kΩ pull-down below VREF L 0.5 V (V). VTX_PWR_EN = R68 100k pull-up + R84 10k from GPIO21 (bom_plan), so an open-drain AP1606 is valid. House Q5 AP1606 is gated from GPIO17 (netlist, V) |
| V2 | **confirmed; model numbers wrong** | Firmware facts hold (V): ESP32 duty = count·1000/4096 at 10 kHz, YOLO 2000, pit 3700, VPD loop at 25/100 mW; OpenVTx PWM0 with polarity high, duty = val/3000; HM AIO overlay 3133-3263; overlay merge l. 57-58; GPIO13 is no ESP32 strap and is free in PINMAP. But `pnp.py` l. 12 reverses the base-current sign (PNP: Vb = Vpwm + Ib·Rb). Corrected YOLO at Re 27 Ω is **26-30 mA, not 41-52 mA**, and rises with hFE |
| V3 | **confirmed** | Both OpenOSD-X v1.01 variants: pin 17 → R13 3.3k → C16 1 µF → GND only, pin 13 NC (V, 300 dpi). A working reference puts no DC on pin 17, and this board has no audio networks. The datasheet still labels pin 17 "Supply IN 3.3 V" (V), so the deviation rests on the reference alone |
| V4 | **confirmed** | Both OpenOSD-X v1.01 variants: pin 26 REG1D8 → C27 0.01 µF "(DNI)"; pin 23 REG1D8_1 → C25 0.47 µF fitted (V) |
| V5 | **confirmed (conditional)** | SE5004L p. 1: "External blocking capacitors are recommended", not required; only pin 3 RFin says "DC block required"; RFOUT has an internal DC shunt (V). The OpenOSD-X counter-example does not transfer: RTC6671 pins 10-12 are "RF_OUT/Vcc3" (DC on the output, so the block is mandatory), and the RFPA5512 variant pairs C37 with a 0.75 pF shunt match (V) |
| V6 | not recommended; no objection | - |
| F1 | **confirmed** | Cleanflight: "The LED pin on the CPU will always be between 0v to ~3.3v", remedy "inline diode on the VIN" (V). `BETAFPVG473_V2` `LED_STRIP_PIN PB2` (V). The house AP1606 LED stage is not counter-evidence: it inverts, and Betaflight's PICO WS2812 driver cannot invert (PINMAP F1, V) |
| F2 | **confirmed** | House `OpenFC.kicad_pcb`: C9 sits 1.42/1.74 mm from pins 45/44 and C12 0.98/1.13 mm from 54/53, 7 caps for 9 pins (pcbnew, V). RP2350 DS §6.1.5: "ADC_AVDD should be decoupled with a 100nF capacitor close to the chip's ADC_AVDD pin", so C49 must sit at pin 44 (V) |
| F9 | **confirmed with a condition; risk understated** | Placed board: TP9-TP10 1.0 mm, TP11-TP10 16.2 mm, TP9-J30 8.5 mm (pcbnew, V). The fixture can take GND from J30 (spec §1780). But spec §687 and PINMAP pin 60 want FCB "next to a GND pad". J30's GND lies under the clip-on USB adapter, and every user GND pad (J3, J19, J25, J27) is on the top side |
| F9b | not recommended; no objection | - |

**Corrections to carry into P4.**

1. **V2 model.** The sign error is fixed in `bomred/verify_vfm/pnp_fix.py`. Ic in mA per PWM count:

   | Re / hFE | 2000 | 2500 | 3000 | 3200 | 3300 | ≥ 3400 |
   |---|---|---|---|---|---|---|
   | 27 Ω / 220 | 26.4 | 15.6 | 5.3 | 1.7 | 0.4 | 0 |
   | 27 Ω / 475 | 30.4 | 18.0 | 6.0 | 1.8 | 0.5 | 0 |
   | 15 Ω / 220 | 39.1 | 23.0 | 7.5 | 2.2 | 0.5 | 0 |
   | 15 Ω / 475 | 48.8 | 28.6 | 9.2 | 2.5 | 0.5 | 0 |
   | 10 Ω / 220 | 49.1 | 28.8 | 9.2 | 2.5 | 0.5 | 0 |
   | 10 Ω / 475 | 65.5 | 38.1 | 12.0 | 3.1 | 0.6 | 0 |

   - Pinch-off (≥ 3400) and the 10-90 % span (counts 2121-3141, about 255 duty steps) do not change.
   - The 41-52 mA ceiling quoted in §1.3 needs Re of about 10-15 Ω. 10 Ω reuses the R65 line (RC0201FR-0710RL), so V2's line delta is unchanged.
   - Ic rises with hFE: about ±7 % at 27 Ω and ±14 % at 10 Ω. The "±12 %" in §1.3 has the wrong sign.
2. **V2 part.**
   - BC857BM: production, SOT883, 45 V / 100 mA, hFE 220-475, Ptot 250 mW (S, Nexperia parametrics); VEBO −5 V (S, older NXP series sheet).
   - In HD mode (+3V3_VTX at 0 V, GPIO13 high) both junctions are reverse biased, EB at 3.3 V < 5 V, so the PWM pin cannot back-power +3V3_VTX.
   - The part can reuse the AP1606 land (Nexperia SOT883 reflow, LIBRARY.md).
3. **V2 inference.** The Happymodel AIO stock layout drives `vtx_amp_pwm` on GPIO12. Either its stage is not a bare rail-referenced PNP, or its eFuse is burned. The "PNP signature" in §1.2 stays I, and the pin move (or eFuse first) is required.
4. **V1 capacitance.** LP5912 §7.6 gives COUT 0.7-10 µF (max, verified by design).
   - +3V3_VTX already carries C108 10 µF + C121 1 µF + 4x 100 nF, about 11.4 µF nominal (pre-existing).
   - V1 adds C122 (1 µF). The effective total at 3.3 V bias is roughly 5-6 µF (I).
   - P4 checks the effective value against 10 µF, or drops C121 when C108 sits at U21.
5. **V1 turn-off.** At HD turn-off PA_VREF may briefly exceed VIN + 0.3 V (LP5907 §5.1 note 2) until C123 drains through the PA's 10 mA bias. The body-diode current is small (I). V9's PA_VREF < 0.5 V check stands.
6. **V3.** Correct spec §4.8/§16. Because the datasheet still labels pin 17 a supply, V5 also confirms no 6.5 MHz spur with pin 17 open.
7. **V5 decision timing.** A "P5 VNA" cannot run before hardware exists: P5 is placement, and the spec's P5 tool is an EM solver. The spec also forbids a DNP footprint on the RF line, so the call is made at P4 from the datasheet plus EM. The physics favours deletion: a 10 pF 0201 at 5.8 GHz is above its self-resonance (about 3 GHz at 0.25 nH ESL) and acts as a small series inductance, not a match element (I).
8. **F1 series resistor.** PINMAP option (a) reads "direct 3.3 V drive through a 0201 series resistor"; F1 drops the resistor. That matches the other user pads (TP0, RP0, TX1 and RX1 are direct GPIO nets in bom_plan), so −3 stands. Keeping the resistor would make it −2.
9. **F9 condition.** Keep TP10 unless one of these holds:
   - FCB moves beside the J30 GND pad, and the README recovery reads "battery first: hold FCB to J30 GND, connect the battery, release, then clip on USB". This relies on the RP2350 bootrom staying in BOOTSEL until reset (I; V9 checks it).
   - FCB moves to the top beside a user GND pad, which takes it off the bottom-side fixture.

   Risk is low, not none. The saving is 1 mm² and a label; there is no BOM change.

**Result.**
- No proposal is refuted. The recommended set (V1-V5, F1, F2, F9) stands at **−15 BOM parts, top −5.13 mm², bottom −6.60 mm²**.
- V2 needs Re re-derived (about 10-15 Ω, P4 SPICE).
- F9 needs its recovery condition.
- V1 adds a P4 check on the LP5912 output capacitance.
