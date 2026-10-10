# BOM reduction track: power tree and ESC cells

Date 2026-10-09. Read-only review; no repo files edited.

**Inputs.**
- `hardware/bom_plan.json`: 329 entries, 282 BOM parts, 88 lines.
- Part positions from the placed floorplan `hardware/OpenAIO-Whoop.kicad_pcb` (pcbnew pad extents).
- `research/DESIGN-SPEC.md` §4.1-4.4, `DECISIONS.md` D12-D50, `FLOORPLAN.md`.
- The research reports in `scratchpad/research/`.
- Sibling and prior-art schematics:
  - OpenAIO, OpenESC-20x20 and OpenFC-Lite-Mini (kicad-cli BOM and netlist export);
  - fishpepper tinyPEPPER (pad nets read from `tinyPEPPER.kicad_pcb`);
  - the NBD LionBee 1S AIO schematic (the only published 1S analog AIO schematic, rendered and read).

**Labels.** V = verified (primary source read), S = screened (distributor or aggregator), I = inferred.

**Area metric.** Pad extent + 0.1 mm halo per side, the same metric the RX/VTX track used:

| Part | Area |
|---|---|
| 0201 | 0.66 mm² |
| 0402 | 1.12 mm² |
| 0603 | 2.30 mm² |
| AP1606 | 1.17 mm² |
| SC-70-6 | 4.94 mm² |

Negative = saved. F = top, B = bottom.

## 0. Bottom line

1. **The ESC cell is already lean.**
   - It has 20 placements per cell:
     - EFM8 + 6 FETs;
     - 0 gate R (already dropped, spec §4.4);
     - 6 BEMF R, 0 BEMF dividers, 0 filter caps;
     - 2 VDD caps, 3 leg caps, 1 bulk, 1 DShot R.
   - Comparison:
     - tinyPEPPER: 16 per cell;
     - LionBee: about 28 per cell (V);
     - Matrix II: about 21-24 (I, photo reconstruction).
   - One real cut is left: the EFM8's own 2.2 µF. Placed at the VDD pin, the cell's 22 µF bulk meets the datasheet's "1 µF" (tinyPEPPER layout). That saves −4 parts.
2. **The power tree has seven small, low-risk cuts.** Together they save **−8 parts**. The largest is structural:
   - Feed the O4 load switch from the boost output **`+5V_BST`** (before the TPS2116) instead of `+5V`.
   - USB then cannot reach the O4 by topology, so the AP1606 USB term goes.
   - The other cuts are datasheet-minimum decoupling: INA186 CM caps, gyro LDO caps, LDO input sharing, TPS22810 CIN, TPS61022 EN pull-up.
3. **Line consolidation gives −4 lines now, and −7 if two P4 value choices land.**
   - Unify the pad bulk, the CT cap and the 100 nF parts.
   - Replace the 4.7 kΩ with 2.4 kΩ.
   - Conditional: boost FB from existing values (47k/6.2k) and PR1 from 49.9k/18k.
4. **The biggest lever is an owner decision, not recommended for rev1:**
   - Matrix-stage AGM210MAP P+N duals: −12 parts, −1 line.
   - Note that the CSD25310Q2 is already a consigned line.
5. **Recommended set: −12 parts, −4 lines firm (−7 conditional), about −4.0 mm² B and −5.8 mm² F.**
   - Power + ESC go from 118 BOM parts to 106.
6. **The baseline has four defects worth fixing anyway** (§1.3):
   - The BOM is stale against D24/D34 (+3 parts).
   - The +3V3 rail exceeds the LP5912's 10 µF output-capacitance range.
   - Several 0201 1 µF LDO caps fall below the datasheet's effective minimum at bias.
   - The TPS61022RWUR shows 0 at LCSC today.

## 1. Baseline

### 1.1 Power block (bom_plan `power`, 38 entries)

| Group | Refs | Count |
|---|---|---|
| Input | D1 SMF5.0A, C1/C2 22 µF 16 V X5R (CL10A226MO7JZNC) | 3 |
| Current sense | R1 0.5 mΩ, U1 INA186A3IDCKR, R2/R3 1k, C3/C4 100 nF (CM), C5 1 µF (DM), C6 100 nF (VS) | 8 |
| Boost | U2 TPS61022, L1 0.68 µH, C7 Cin, C8-C11 4x Cout 22 µF X6S, R4/R5 909k/120k FB, R6 100k EN pull-up | 10 |
| Mux | U3 TPS2116, R7/R8 27.4k/10k PR1, C12 10 µF | 4 |
| +3V3 LDO | U4 LP5912-3.3, C13/C14 | 3 |
| Camera filter | FB1, C15 | 2 |
| O4 switch | U5 TPS22810, C16 CT 10 nF, C17 CIN, R9/R10 EN divider, D2 BAS16LD, R11 4.7k, Q1 AP1606 | 8 |
| **Total** | | **38** |

Related rails outside the block:

| Rail | Parts | Block |
|---|---|---|
| +1V8 | U12 TPS7A2018, C61, C62, C63 | imu |
| +3V3_VTX | U21 LP5912, C120, C121, R68 | vtx |
| PA_VREF | U22 LP5907-2.85, C122, C123, R69 | vtx |

### 1.2 ESC cell (×4, 20 BOM parts + 2 C2 test pads per cell)

| Item | Refs (ESC1) | Count |
|---|---|---|
| MCU | U6 EFM8BB51F16I | 1 |
| FETs | Q2-Q4 CSD25310Q2 (top), Q5-Q7 CSD13202Q2 (bottom), gates direct | 6 |
| EFM8 VDD | C18 2.2 µF X6S 0402, C19 100 nF X6S | 2 |
| DShot series | R12 2.4k | 1 |
| BEMF | R13-R15 10k series, R16-R18 1k neutral star | 6 |
| Leg caps | C20-C22 100 nF X6S | 3 |
| Local bulk | C23 22 µF X6S 0603 | 1 |
| **Total** | | **20** |

### 1.3 Baseline defects found on the way (not reductions, but they change the counts)

| # | Finding | Evidence | Effect |
|---|---|---|---|
| B1 | **bom_plan is stale against D24 and D34** | Spec §4.2 and D24/D34 add three parts: a VIN1 2.2 µF X6S, a 1.5 MΩ hysteresis R from +5V_HD, and a 100 nF EN filter. R9 should be 90.9k, but the BOM has 80.6k. None of the three is in bom_plan (grep: no 1.5M, no VIN1 cap) | Corrected power block = **41 parts, +1 line** (1.5 MΩ). The proposals below are counted against the plan; the corrected baseline adds +3 |
| B2 | **+3V3 output capacitance exceeds the LP5912 range** | LP5912 SNVSA77D §9.2.2.3: output capacitor "in the 1-µF to 10-µF range" (design table: 1 to 10 µF) (V). Caps on +3V3: 24x 100 nF, C58 4.7 µF 0402, C82 + C93 10 µF 0402, C14/C61/C92/C122 1 µF 0201. Effective at 3.3 V is about **14-17 µF** (I: DC-bias estimates as in spec §4.1; P3 checks the Murata curves) | Supports RX track RV-3 (delete C93: about 10-12 µF remains, still at the limit). P4 must close it: also drop C82, or switch U4 to TLV75533 (Cout 1-200 µF, V TLV755P table; RθJA 100 K/W in X2SON-4 DQN versus 71 K/W in WSON-6 for the LP5912, so +46 K at 0.46 W against +33 K) |
| B3 | **0201 1 µF X5R LDO caps fall below the effective minimum at bias** | LP5912 §7.6 note 1: CIN/COUT must stay "greater than 0.5 µF over full range" (V). LP5907 §5.6 note 1: "greater than 0.7 µF" (V). GRM033R61A105ME44D gives about 0.3-0.45 µF at 5.15 V and 0.4-0.55 µF at 2.85-3.3 V (I) | C13 and C120 (LP5912 inputs, 5.15 V) are fixed by PE-5. C122/C123 (LP5907) need the 2.2 µF 0402 X6S line in P4 (VTX track). This is also why PE-7 keeps that line |
| B4 | TPS61022RWUR stock | LCSC C915088: **0** on 2026-10-09 (spec read 857 on 10-07) (V, LCSC product API) | O17 watch; not a reduction item |

## 2. Market and prior-art evidence for the ESC cell

### 2.1 Per-cell count

| Design | MCU | FET pkgs | Gate R | BEMF R / div / C | VDD caps | Leg caps | Cell bulk | Signal R | Other | **Per cell** | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **This plan** | 1 | 6 (2x2) | 0 | 6 / 0 / 0 | 2 (2.2 µF + 100 nF) | 3 | 1 (22 µF) | 1 (2.4k) | - | **20** | bom_plan |
| This plan + PE-7 | 1 | 6 | 0 | 6 / 0 / 0 | 1 (100 nF; bulk at VDD) | 3 | 1 | 1 | - | **19** | §4 |
| tinyPEPPER (fishpepper, open, 1S BLHeli_S) | 1 EFM8BB21 | 6 SOT-23 (IRLML6244/2244, 20 V) | 0 | 6 / 0 / 0 (10k series, 1k star) | 1 (100 nF) | **0** | 1 (47 µF 0805, 2.9 mm from the MCU, other side) | 0 | RSTb 1k pull-up | **16** | V, pad nets of `tinyPEPPER.kicad_pcb` |
| NBD LionBee (1S AIO, AM32, N+N, integrated driver) | 1 QF32MTF4 | 3 SiZ340DT | 0 | 9 (10k series, 2k dividers, 10k star) | 2 | **0** | **0** (shared 10x 47 µF bank on +BAT) | 1 (1k) | 3 boot diodes, 3 boot caps, 3 LS gate pull-downs, NRST R, VBAT divider (2) | **about 28** | V, LonBee_V1_Schematic.pdf |
| BetaFPV Matrix 1S 5IN1 II (target) | 1 EFM8BB51 | 3 AGM210MAP (P+N dual 3.3x3.3) | ? | ? | ? | ? | ? | ? | 17-20 passives total | **about 21-24** | I, `01-matrix-1s-5in1-ii.md` §5.2 photo reconstruction |
| FusionFPV UD 4IN1, Happymodel X14 | EFM8BB51 / n.p. | 3 SiA517DJ / n.p. | n.p. | n.p. | n.p. | n.p. | n.p. | n.p. | UD: "ESC programming points" | unknown | no teardown in the research reports |

### 2.2 Readings

- **Gate resistors.** None on this plan, tinyPEPPER, or LionBee's low side. EFM8 drive against Qg (CSD25310Q2 3.6 / 4.7 nC, CSD13202Q2 5.1 / 6.6 nC, V SLPS459C / SLPS313A) was already accepted in spec §4.4. **Nothing left to remove.**
- **BEMF.** Stock Bluejay always compares a phase against the **V_Mux pin**:
  - `src/Layouts/Base.inc` l. 134/143/152: `mov CMP_MX, #((A_Mux SHL 4) + V_Mux)`;
  - `src/Layouts/BB51/A.inc` l. 54-57: V_Mux = P0.4 (V, Bluejay 0368d11).
  - So the per-motor 3-resistor neutral star is mandatory, and the EFM8's internal comparator DAC is unused.
  - The 10k series resistors limit pin injection: Table 4.17 limits the comparator input to 0..VDD, while the phase swings to VBAT + a diode drop.
  - No divider or filter cap exists to cut (1S, phase ≤ VDD).
- **Leg caps.** tinyPEPPER and LionBee have none, but both use 20-30 V FETs. This plan's N is a 12 V part, and the ESC hot loop is protected by D33. **Keep them.**
- **Bulk.** tinyPEPPER uses its cell bulk as the MCU's bulk. LionBee uses a shared bank. Either supports PE-7.

## 3. Power tree: datasheet checks behind the proposals

| Part | Datasheet fact (V) | Used by |
|---|---|---|
| TPS61022 (SLVSDX7D) | EN abs max −0.3..7 V, the same as VIN (§6.1); EN is a logic input, VEN_H 1.2 V (§6.5); enabled when VIN > UVLO and EN > 1.2 V (§7.3.1). Cout effective 20 µF min for 1.5 A < IOUT < 3 A, Cin 4.7 µF min effective (§6.3). Fig. 8-1: 3x 22 µF out, 732k/100k FB, R2 < 300 kΩ | PE-3, PE-12, PE-16 |
| TPS2116 (SLVSFG1A) | Priority mode needs the PR1 divider (§7.6.1.1); RCB blocks VOUT → VINx (§7.3.4); CIN 1 µF "sufficient" (§9); ST is low when VIN2 is used (§7.3.3), the wrong polarity for an O4 USB veto | PE-1, PE-R8 |
| TPS22810 (SLVSDH0C) | §10.3 "Input Capacitor (**Optional**)": a 1 µF CIN mainly limits the VIN dip from inrush, which the CT slew already limits. EN/UVLO VENR 1.13-1.30 / VENF 1.08-1.18 V. CT "can be left floating" (pin table), but the 10 nF sets 4.7 V/ms for O4 inrush, so keep it | PE-1, PE-2 |
| INA186 (SBOS318B) | Fig. 8-2 input filter = 2x RF + one **differential** CF (no CM caps). Max capacitive load 1 nF, and "filter or buffer the output before a SAR ADC" (Fig. 8-x note A), so R47/C60 stay. IIB 0.5 nA typ | PE-4, PE-R7 |
| LP5912 (SNVSA77D) | CIN ≥ 1 µF "not more than 1 cm from the input pin" (§9.2.2.2); C > 0.5 µF effective (§7.6 note 1); COUT 1-10 µF (§9.2.2.3) | PE-5, B2, B3 |
| TPS7A20 (SBVS) | "An input capacitor is not required for LDO stability", 0.47 µF effective recommended (§6.3 note 2); COUT 0.47-200 µF effective | PE-6 |
| EFM8BB51 data sheet Rev 1.0 | Fig. 5.1: "1 µF and 0.1 µF bypass capacitors required for the power pins placed as close to the pins as possible". Comparator VIN 0..VDD (Table 4.17) | PE-7 |
| BMI270 | "recommended to use 100nF decoupling capacitors at pin 5 (VDDIO) and pin 8 (VDD)"; VDD 1.71-3.6 V | PE-6, PE-R6 |

## 4. Proposals

### PE-1: O4 load switch fed from `+5V_BST`; delete the AP1606 USB term (Q1)

**What.**
- U5 TPS22810DBVR VIN moves from `+5V` (mux output) to `+5V_BST` (TPS2116 VIN2 node).
- Q1 AP1606 is deleted.
- R9/R10, the 1.5 MΩ and 100 nF (D34), D2 and R11 stay.

**Why it works.**
- USB can reach `+5V_BST` only by flowing backwards through the TPS2116. RCB blocks that (§7.3.4), so a PC port can never carry the O4, whatever HD_EN does.
- The case the AP1606 covered is "USB + cell, HD mode". With PE-1 the O4 simply runs from the cell through the boost, exactly as in battery-only use.
- USB only:
  - `+BATT` is back-fed to 2.5-2.8 V (PINMAP F16), so the threshold holds EN at 0.87-0.97 V, below VENR 1.13 V.
  - `+5V_BST` is a hiccuping boost on a 5 mA source in any case.
- Side benefits:
  - The 1.2 A O4 current no longer crosses the mux (37-60 mΩ). The mux saves 0.05-0.07 W and +5V sits 0.04-0.07 V higher in HD mode.
  - USB plug and unplug switchovers no longer carry the O4 (spec §4.2 already assumed it off).
- Routing is unchanged: `+5V_BST` already runs from the boost to the mux at front centre, and U5 taps it there.

**Numbers.** Parts −1, lines 0 (the AP1606 line stays for the beeper, Q26), area −1.2 mm² B.

**Risk.** Low.
- It edits D34 (the orchestrator logs it as D35+).
- The USB-port guard becomes topological instead of a sensed veto.
- V1 checks USB + cell + HD.

### PE-2: Delete C17 (TPS22810 CIN)

- **What.** Delete the C17 1 µF 0201.
- **Why.**
  - The datasheet calls CIN optional (§10.3).
  - The CT 10 nF slew limits inrush to about 0.2 A per 47 µF (spec §4.2).
  - The 0201 gives about 0.4 µF effective at 5.15 V, negligible against a 1.2 A load on the `+5V_BST` pour.
- **Numbers.** Parts −1, lines 0, area −0.7 mm² B.
- **Risk.** Low; V1 scopes VIN at O4 switch-on.

### PE-3: TPS61022 EN tied to VIN; delete R6 (100k)

- **What.** EN goes straight to VIN (+BATT).
- **Why.**
  - EN and VIN share the −0.3..7 V absolute maximum.
  - EN draws no current requirement.
  - Startup is still gated by UVLO.
  - The 100k is a leftover of the round-2 sense FET on EN, deleted in round 3 (spec §4.2).
- **Market.** LionBee uses a 10k pull-up, so production boards keep a resistor; the lean rule does not need one.
- **Numbers.** Parts −1, lines 0 (100k stays: R48, R63, R68), area −0.7 mm² B.
- **Risk.** None functional. A bus surge above 7 V already exceeds VIN itself (spec §4.1).

### PE-4: INA186 input filter in the datasheet form; delete C3 and C4 (CM 100 nF)

- **What.** Keep R2/R3 1k + C5 1 µF differential: f3dB = 1/(4π·1k·1µF) = 80 Hz.
- **Why.**
  - TI Fig. 8-2 has no common-mode caps.
  - With 1 µF differential and 100 nF CM, the CM caps' ±10 % mismatch is the main CM→DM conversion path, so removing them does not hurt.
  - The INA's own CM rejection plus the existing output RC (R47 1k / C60 100 nF, needed by the 1 nF CL limit and the SAR note) cover CM noise.
- **Note.** The house OpenAIO and OpenESC sheets carry 2x 100 nF CM (netlist export); that is house habit, not a datasheet requirement.
- **Numbers.** Parts −2, lines 0, area −1.3 mm² B.
- **Risk.** Low; the `ibata_scale` check on every prototype (spec §4.1) catches any offset.

### PE-5: One shared input cap for both LP5912s (U4 +3V3, U21 +3V3_VTX)

- **What.** Replace C13 + C120 (2x GRM033R61A105ME44D) with **one GRM155C81A225KE11D**, 2.2 µF X6S 0402, about 1.0-1.4 µF effective at 5 V (spec §4.1, S).
- **Placement.** Between the two IN pins: U4 pin 6 at (5.92, 1.05) and U21 pin 6 at (5.92, 3.45), both on the bottom, 2.4 mm apart.
- **Why.**
  - Both LDOs share `+5V`, and the datasheet asks for ≥ 1 µF within 1 cm of each input.
  - It also cures B3: each 0201 holds about 0.3-0.45 µF at 5.15 V, below the 0.5 µF minimum.
- **Numbers.** Parts −1, lines 0, area −0.2 mm² B.
- **Risk.** Low.

### PE-6: Gyro LDO decoupling at the datasheet minimum

- **What.**
  - Delete C61 (TPS7A2018 input). Its source is the `+3V3` plane, an LDO output with many caps; TI: an input cap is "not required for LDO stability".
  - Merge C62 (LDO output) and C63 (gyro VDD 100 nF) into **one 1 µF 0201 at the BMI270 VDD pin 8** (−2.16, 2.3).
- **Geometry.**
  - U12 OUT (pin 1) is at (1.19, 2.26), 3.4 mm from the gyro pin.
  - Today's C62 already sits 3 mm from OUT, on the far side.
  - 0201 1 µF at 1.8 V gives about 0.6-0.8 µF effective, which covers both TPS7A20 COUT ≥ 0.47 µF and the Bosch "100 nF at VDD" (a superset with the same ESL).
- **Numbers.** Parts −2, lines 0, area −1.3 mm² F.
- **Risk.** Low.
  - The gyro noise check in V-tests.
  - Keeps the dedicated gyro LDO (PE-R6).

### PE-7: The EFM8 2.2 µF goes; the cell's 22 µF moves to the EFM8 VDD pin

**What.**
- Delete C18, C24, C30 and C36 (GRM155C81A225KE11D).
- Place each cell's 22 µF X6S 0603 (C23, C29, C35, C41) ≤ 3 mm from its EFM8 VDD pin (pin 4), on the cluster `+BATT` copper.
- Either side works: on the top beside the EFM8, or on the bottom with in-pad vias.
- C19 100 nF stays at the pin.

**Why.**
- EFM8 Fig. 5.1 requires 1 µF + 0.1 µF "as close to the pins as possible". The 22 µF gives about 7-10 µF effective at 4.35 V, so it meets the 1 µF term, and 100 nF stays at the pin.
- tinyPEPPER does exactly this: its 47 µF 0805 cell bulk sits 2.9 mm from the EFM8 on the other side, with a single 100 nF at the pin (V, pcb file).
- Today the bulk caps sit **7.1-8.9 mm** from the VDD pins (measured on the board). PE-7 moves them closer, which also helps VDD track the P sources (spec §4.4).

**Numbers.** Parts −4.

| Variant | Top | Bottom | Net |
|---|---|---|---|
| 22 µF stays on the bottom | −4.5 mm² | 0 | −4.5 mm² |
| 22 µF moves to the top | +4.7 mm² | −9.2 mm² | −4.5 mm² |

The top variant also unloads the fuller bottom: 74.2 % against 70.9 %.

**Lines.** 0. The 2.2 µF line stays for the D24 VIN1 cap, PE-5 and the LP5907 fix (B3). It would be −1 if those parts take other lines.

**Risk.** Medium-low.
- Placement only: P5 must find a 0603 site within 3 mm. The bottom under each EFM8 is taken by U21, U2, U10 and U5, so the top variant is the likely one.
- Bus capacitance drops by the four 2.2 µF parts, about 4-5.6 µF of 55-80 µF effective (I). Hot-plug damping falls about 3 %; V3c covers it.

### PE-8: Pad bulk on the ESC bulk line

- **What.** Change C1/C2 from CL10A226MO7JZNC (16 V X5R) to **GRM188C80J226ME15D** (6.3 V X6S, already 9x on the board).
- **Why.**
  - The 6.3 V X6S parts already sit on the same bus 0.5 mΩ away (cells, boost Cin), so the 16 V rating protects nothing.
  - X6S is better for temperature.
- **Numbers.** Parts 0, lines −1, area 0.
- **Risk.** About −2-3 µF effective each at 4.35 V (9-13 → 7-10, spec §4.1 table). V3c hot-plug.

### PE-9: CT cap on the 10 nF line

- **What.** C16 GRM033R71C103KA01D (X7R, single use) → **GRM033R61A103KA01J** (X5R, used on rx and vtx).
- **Why.** CT sees ≤ 2.5 V; the slew tolerance is uncritical; the switch area is not in an ESC quarter.
- **Numbers.** Parts 0, lines −1, area 0.
- **Risk.** None.

### PE-10: GPIO27 pull-down R11 4.7k → 2.4k (RTT012401FTH, 5 uses)

- **What.** R11 becomes 2.4 kΩ.
- **Why.**
  - GPIO27 high: 1.38 mA + 0.52 mA for the two HD-gate bases = 1.9 mA, inside the 4 mA default drive.
  - GPIO27 low or in reset: EN ≤ VF + 0.07 V, more margin than 4.7k's +0.15 V against VENF 1.08 V.
- **Numbers.** Parts 0, lines −1, area 0.
- **Risk.** None.

### PE-11: One 100 nF line

- **What.** Unify GRM033R61E104KE14D (X5R, 41x) and GRM033C81E104KE14D (X6S, 16x) on the X6S part.
- **Why.** Same 25 V 0201 part; X6S is the technical superset.
- **Numbers.** Parts 0, lines −1, area 0.
- **Risk.** Sourcing: X6S has no LCSC listing. Use it only if the O17 NextPCB quote fills about 3,000 pcs; otherwise keep two lines. This is board-wide; the FC and RX tracks are affected.

### PE-12: Divider values from existing lines (P4 value pass)

**Boost FB.**
- Change R4/R5 909k/120k (two single-use lines) to **47k (RC0201FR-0747KL) / 6.2k (RC0201FR-076K2L)**: 0.6·(1 + 47/6.2) = **5.148 V**, the same 4.92-5.38 V worst case as today, with 97 µA divider current.
- TI says lower R2 "increases the immunity against noise injection".
- Only 47k/6.2k qualifies from the existing value set (search script `pwr/divsearch.py`).
- Lines −2.

**PR1 divider.**
- Change 27.4k/10k to **49.9k/18k**: threshold 3.47-4.07 V against 3.44-4.04 V.
- 49.9k is the O4 divider line; 18k is the drive-stage line.
- The low-impedance reason (AP1606 gate pull-down) disappears with PE-1.
- Lines −1.

**O4 EN network.** Checked as well: only the D34 values 90.9k / 49.9k / 1.5 MΩ meet "shed 2.75-3.15 V, on ≤ 3.8 V" (`pwr/ensearch.py`).

**Condition.** 6.2k (R74) and 18k (R71/R72) are VTX drive-stage start values (P4-5). Apply only if they survive P4-5.

**Numbers.** Parts 0, lines −3 conditional, area 0.

### PE-13 (optional, area): INA186A3IDCKR → INA186A3IYFDR (DSBGA-6)

- **What.** Same die and gain 100 in a 1.17 x 0.765 mm package.
- **Pins.**
  - The ENABLE ball B3 ties to VS on the adjacent ball A2.
  - REF is internal GND, the same as this plan (REF to GND).
- **Status.** Already the spec §4.1 fallback.
- **Numbers.** Parts 0, lines 0, area **−3.6 mm² B**.
- **Risk.** A 0.4 mm-pitch WCSP needs NextPCB EQ and via-in-pad. It replaces a house [PU] part.
- **Recommendation.** Only if bottom area is needed.

### PE-14 (not recommended): BEMF resistor arrays

**What.** Panasonic EXB-18V (4x 0201-size elements, 1.4 x 0.6 x 0.35 mm, 0.4 mm pitch, **±5 %**) (S, Avnet / Future listings):

| Variant | Arrays per cell | Parts | Lines |
|---|---|---|---|
| (a) series 10k only | EXB-18V103JX x1 | −8 | +1 |
| (b) star also 10k, as in LionBee | EXB-18V103JX x2 | −16 | +1 |

Area about −0.5 mm² F per cell.

**Why not.**
- ±5 % elements in the neutral star shift the virtual neutral.
- (b) leaves the tinyPEPPER/Bluejay-proven 1k star (V2 retest).
- One more fine-pitch EQ package.
- At a 50-board turnkey run a new line costs more than 8-16 placements.
- Revisit after V2.

### PE-15 (owner decision; not recommended for rev1): AGM210MAP P+N duals (the Matrix II stage)

**What.** Replace 12x CSD25310Q2 + 12x CSD13202Q2 with **12x AGMSEMI AGM210MAP** (PDFN 3.3x3.3, one half-bridge per package, 3 per motor, as on the Matrix II).

**Numbers.** Parts −12, lines −1.

**Area.**
- About board-neutral: spec §4.3 budget v3 case (b), "within 1 % of D12".
- The per-side split needs a P2 rerun: the Matrix puts 8 of 12 on one side.

**For.**
- Matrix parity (market evidence).
- Hot path 34.1 against 40.2 mΩ typ hot (spec §4.3).
- **20 V N and P and ±12 V gate**, against 12 V / ±8 V. This removes the spec §4.1 exposure of the gates to the 9.2 V TVS clamp and the 12 V N to disconnect surges.
- Shipped at DT 5.
- The P side is a consigned line today anyway (CSD25310Q2: LCSC C2871649 659 on 2026-10-09; spec §15.3). One consigned line would replace one consigned + one turnkey line.

**Against.**
- LCSC-only (C7431169: 4,690 on 2026-10-09; 0 hits at HQ Online per track 03).
- It re-opens D12, D23 and D36, and the P2 ESC cell (D45).
- The datasheet's Qg figures are inconsistent (track 03).

**Recommendation.** The largest single lever in this track. Rev2 candidate, or the rev1 fallback if the CSD25310Q2 consigned buy fails.

### PE-16 (not recommended now): boost Cout 4x 22 µF 0603 → 2x 47 µF 0805

- **What.** The LionBee pattern: 2x 47 µF 6.3 V per TPS61022 (V).
- **Numbers.** Parts −2, lines +1, area about +0.4 mm² B.
- **Why not.** It holds only if a 47 µF part keeps ≥ 10 µF effective each at 5.15 V and 105 °C (X6S/X7S) for the 20 µF TI minimum, and no curve was verified here. P3 search item.

## 5. Rejected, with reasons

| ID | Idea | Why not |
|---|---|---|
| PE-R1 | Remove gate resistors | There are none (spec §4.4, field record tinyPEPPER / BB51 layout A) |
| PE-R2 | Shared BEMF neutral, or the comparator DAC instead of the star | Each motor needs its own star. Stock Bluejay hard-codes the V_Mux pin (Base.inc l. 134-152). A custom layout is a firmware fork |
| PE-R3 | Fewer leg caps (one per cell or none) | D33 protects the ESC hot loop. The 12 V CSD13202Q2 needs the ≤ 4 mm² loop. Production boards without them use 20-30 V FETs |
| PE-R4 | Per-cell 22 µF → shared bank (LionBee) | PE-7 uses the cell bulk as the EFM8 bulk. A bank saves at most 2 parts. Less bus C lowers hot-plug damping (ζ about 0.45, spec §4.1) |
| PE-R5 | Merge +3V3_VTX into +3V3 (one LP5912) | 0.30-0.35 A x 1.85 V = 0.56-0.65 W, +40-46 K (RθJA 71.2 K/W), so TJ > 125 °C on an 85 °C board. The VCO shares the digital rail. D17 needs a switch on the RTC6705 rail anyway. LionBee also splits its VTX, PA-ref and gyro LDOs |
| PE-R6 | Gyro on +3V3 directly (drop TPS7A2018 + 2 caps) | BMI270 VDD allows 1.71-3.6 V, but the house OpenFC-Lite-Mini uses an LP5912-1.8 gyro LDO (netlist), the UD 4IN1 states "BMI270 with dedicated low-noise supply", and LionBee has an RT9013 gyro LDO with ferrites |
| PE-R7 | MCU ADC on a larger shunt instead of the INA186 | High side: CM 3-4.35 V is above the 3.3 V ADC. Low side: board GND sits above B−, so the ADC would see a negative voltage. Resolution: RP2350 ENOB about 9.2 bits gives about 5.7 mV noise, while 0.5 mΩ gives 0.5 mV/A (11 A per noise step). 1 A resolution needs about 5.7 mΩ: 2.3 W at 20 A and 13 W at 48 A. Matrix and UD both sense current |
| PE-R8 | Schottky OR from VBUS instead of TPS2116 + PR1 (LionBee: PMEG4030ER) | The boost runs forced PWM. With VBUS − Vf (up to about 5.0 V) above the 4.93 V setpoint minimum, the TPS61022 runs in reverse and USB charges the cell through it (spec §4.2 "forced-PWM reverse flow"). The mux's RCB is the protection. It would save 3 parts, but no |
| PE-R9 | Drop the O4 battery threshold, or the PR1 divider | The threshold is D15 (it keeps a sagging boost from resetting the FC/RX). PR1 sets the mux priority threshold (§7.6.1.1); the ST pin has the wrong polarity |
| PE-R10 | BAS16LD → resistor into the EN node | Lines −1. The Thevenin solve (EN = VENF at 2.95 V with GPIO27 high, EN < 1.0 V at 4.35 V with GPIO27 low) gives conductance shares R9 : R10 : Rx ≈ 0.22 : 0.63 : 0.15, so the shed point moves −0.66 V per volt of IOVDD. R11 stays for the reset case, and D34 re-opens. Not worth one line |
| PE-R11 | Drop the 2.4k DShot series R | USB-only back-feed of the unpowered EFM8s (PINMAP F16, V9). tinyPEPPER omits it only because it is a stand-alone ESC |
| PE-R12 | Drop the camera ferrite + 10 µF | Boost ripple into analog video, the board's key feature |
| PE-R13 | Drop the C2 pads (out of the BOM) | Production programming (spec §12.1). The UD 4IN1 has ESC programming points. Ganging C2CK across chips is not valid C2 practice |

## 6. Summary

**Recommended set.** PE-1 to PE-11, plus PE-12 if the drive-stage values survive P4-5.

| ID | Change | Parts | Lines | Area F / B (mm²) | Recommend |
|---|---|---|---|---|---|
| PE-1 | U5 VIN → `+5V_BST`; delete Q1 AP1606 | −1 | 0 | 0 / −1.2 | yes |
| PE-2 | Delete C17 (TPS22810 CIN, optional) | −1 | 0 | 0 / −0.7 | yes |
| PE-3 | TPS61022 EN = VIN; delete R6 | −1 | 0 | 0 / −0.7 | yes |
| PE-4 | INA186: delete CM caps C3, C4 | −2 | 0 | 0 / −1.3 | yes |
| PE-5 | C13 + C120 → one GRM155C81A225KE11D | −1 | 0 | 0 / −0.2 | yes |
| PE-6 | Delete C61; C62 + C63 → one 1 µF at gyro VDD | −2 | 0 | −1.3 / 0 | yes |
| PE-7 | Delete 4x EFM8 2.2 µF; cell 22 µF ≤ 3 mm from VDD | −4 | 0 (−1 if line freed) | −4.5 / 0, or +4.7 / −9.2 | yes (P5 site check) |
| PE-8 | Pad bulk → GRM188C80J226ME15D | 0 | −1 | 0 | yes |
| PE-9 | CT → GRM033R61A103KA01J | 0 | −1 | 0 | yes |
| PE-10 | R11 4.7k → 2.4k | 0 | −1 | 0 | yes |
| PE-11 | One 100 nF line (X6S) | 0 | −1 | 0 | yes, if O17 fills it |
| PE-12 | FB 47k/6.2k; PR1 49.9k/18k | 0 | −3 (cond.) | 0 | conditional |
| **Set** | | **−12** | **−4 (−7)** | **−5.8 / −4.0** | |
| PE-13 | INA186A3IYFDR DSBGA | 0 | 0 | 0 / −3.6 | optional |
| PE-14 | BEMF arrays EXB-18V | −8 / −16 | +1 | about −2 / 0 | no |
| PE-15 | AGM210MAP x12 | −12 | −1 | about 0 (P2 rerun) | owner; rev2 |
| PE-16 | Boost Cout 2x 47 µF 0805 | −2 | +1 | 0 / +0.4 | no (P3 curve) |

**Totals.**
- Power + ESC: 118 → **106** BOM parts.
- Corrected baseline (B1): 121 → 109.
- Per ESC cell: 20 → 19.
- Power block: 38 → 32 (corrected 41 → 35).
- The gyro rail (imu) loses 2.

## 7. Stock read (LCSC product API, 2026-10-09)

| Part | LCSC | Stock |
|---|---|---|
| AGM210MAP | C7431169 | 4,690 |
| CSD25310Q2T | C2871649 | 659 |
| CSD13202Q2 | C187839 | 2,595 |
| INA186A3IDCKR | C2058245 | 5,695 |
| TPS22810DBVR | C205990 | 16,584 |
| **TPS61022RWUR** | C915088 | **0** |
| GRM188C80J226ME15D | C393031 | 105,005 |
| CL10A226MO7JZNC | C2762594 | 49,940 |
| LP5912-3.3DRVR | C524780 | 23,284 |
| TPS7A2018PDQNRM3 | C36996449 | 7,970 |

The LCSC search API returned 403, so the arrays were screened through Avnet and Future listings.

## 8. Sources

**TI datasheets** (https://www.ti.com/lit/ds/symlink/<part>.pdf, read 2026-10-09):

| Part | Document | Sections |
|---|---|---|
| TPS61022 | SLVSDX7D | §6.1, 6.3, 6.5, 7.3.1, 8.2.2.1, 8.2.2.3, Fig. 8-1 |
| TPS2116 | SLVSFG1A | §7.3.1-7.3.4, 7.6.1, 9 |
| TPS22810 | SLVSDH0C | pin table, §6.3, 6.5, 10.3, 10.4 |
| INA186 | SBOS318B | §6.5, 7.3.2, 8.1.3, Fig. 8-2; orderable table: INA186A3IYFDR |
| LP5912 | SNVSA77D | §7.6, 9.2.2.2, 9.2.2.3 |
| TPS7A20 | - | §6.3 notes 2-3 |
| LP5907 | - | §5.6 |
| CSD25310Q2 | SLPS459C | - |
| CSD13202Q2 | SLPS313A | - |
| TLV755P | OpenDrone KiCad-Library copy | - |

**Other sources:**
- EFM8BB51 Data Sheet Rev 1.0, Fig. 5.1 and Table 4.17. LCSC copy: https://datasheet.lcsc.com/datasheet/pdf/439baa6a7b4a9d1075a73dd47b35c174.pdf (Silicon Labs returned 403).
- BMI270 datasheet (OpenDrone KiCad-Library copy): pin-connection notes, §4.3.
- Bluejay (https://github.com/bird-sanctuary/bluejay) at 0368d11: `src/Layouts/Base.inc` l. 109-152 and `src/Layouts/BB51/A.inc` l. 37-60.
- fishpepper tinyPEPPER (https://github.com/fishpepper/tinyPEPPER): `single_esc.sch` and `tinyPEPPER.kicad_pcb` pad nets and positions, U501/C501/C502/R501-R507.
- NBD LionBee V1 schematic: https://cdn.shopify.com/s/files/1/1126/9610/files/LonBee_V1_Schematic.pdf (POWER and ESC1 sheets rendered at 330-360 dpi).
- House sheets (kicad-cli export): OpenAIO, OpenESC-20x20 (INA186 network) and OpenFC-Lite-Mini (U12 LP5912-1.8 gyro LDO).
- Panasonic EXB-18V/EXB-14V screens:
  - https://www.avnet.com/americas/product/panasonic/exb-18v102jx/evolve-3910931/
  - https://www.futureelectronics.com/p/passives--resistors--resistor-networks-arrays/exb-18v102jx-panasonic-4105820
  - https://www.lcsc.com/product-detail/C1731102.html
- Repo and scratchpad: `hardware/bom_plan.json`, `hardware/OpenAIO-Whoop.kicad_pcb` (positions via `bomred/pwr/pos.py`, `vddpin.py`, `gy.py`), `research/DESIGN-SPEC.md` §4.1-4.4, `DECISIONS.md`, `FLOORPLAN.md`, `scratchpad/research/01`, `02`, `03`.
- Working files: `scratchpad/bomred/pwr/` (datasheet texts in `ds/`, divider searches `divsearch.py` and `ensearch.py`).

## Verification

Adversarial check, 2026-10-09, by a separate read-only agent. Each proposal was tested against the datasheet texts in `bomred/pwr/ds/` (TI SLVSFG1A, SLVSDH0C, SLVSDX7D, SBOS318B, SNVSA77D, TPS7A20, EFM8BB51 Rev 1.0), the BMI270 datasheet, Bluejay at 0368d11 (fetched from GitHub), the LCSC product API, the placed floorplan board (`hardware/OpenAIO-Whoop.kicad_pcb`, pad positions read with pcbnew; scripts in `bomred/verify_pe/`), the DESIGN-SPEC §4.1-4.4 and §11 rules, and the owner and orchestrator decisions (D11, D12, D33, D34). Labels: V = read from the primary source, I = inferred.

### Verdicts

| ID | Verdict | One line of evidence |
|---|---|---|
| PE-1 | **CONFIRMED** | TPS2116 §7.3.1: priority row VIN1 high gives VOUT = VIN1 with VIN2 "X". IREV out of an unselected VINx is 0.001-0.15 µA typ (§6.5), so USB cannot reach `+5V_BST` (V). USB only: EN = 2.5-2.8 V × 0.347 = 0.87-0.97 V, below VENR min 1.13 V (SLVSDH0C §7.5, V). Even a 3.0 V back-feed gives 1.04 V. D34 is an orchestrator decision (DECISIONS.md), so a D35+ entry may change it. Minor correction: U5 sits at (−5.6, −2.4) B, left of the boost-to-mux run, so it needs a `+5V_BST` branch about as long as today's `+5V` branch. "Routing unchanged" is approximately true |
| PE-2 | **REFUTED** | SLVSDH0C §7.3, Recommended Operating Conditions: "CIN Input capacitor MIN 1 µF". §12.1: "The VIN pin must be bypassed … 1-µF … placed as close to the device pins as possible". The VIN pin row says "Place ceramic bypass capacitor(s)". §10.3's "(Optional)" heading is overruled by the binding table (commons rule). With PE-1 the nearest `+5V_BST` capacitor (boost Cout C10) is about 10 mm from U5 pin 1 (board, V). Keep C17, re-netted to `+5V_BST`. It can go only if P5 puts U5 VIN within about 2 mm of a boost Cout |
| PE-3 | **CONFIRMED** | SLVSDX7D §6.1 gives VIN and EN the same −0.3..7 V. The pin table says "Enable logic input", with no pull-up or series-R requirement. §7.3.2: start-up when VIN > UVLO and EN > 1.2 V (V). BOOST_EN has no other driver (spec §4.2) |
| PE-4 | **CONFIRMED** | SBOS318B §8.1.3, Fig. 8-2: RF + RF + one differential CF only. "If high-frequency, common-mode noise is a concern, add an RC filter from the OUT pin to ground", which is R47/C60, kept (V). CL max 1 nF and the SAR-ADC note (Fig. 8-1) also kept |
| PE-5 | **CONFIRMED** | LP5912 pin 6 = IN (pin table). §9.2.2.2 and §10: ≥ 1 µF "not more than 1 cm from the input pin". §7.6 note 1: > 0.5 µF effective. U4.6 (5.92, 1.05) and U21.6 (5.92, 3.45), both B, 2.4 mm apart, both on `+5V` (board and bom_plan, V). The 2.2 µF X6S effective value at 5 V (1.0-1.4 µF) is S; the Murata curve was not reachable (403), so P3 confirms it |
| PE-6 | **CONFIRMED, evidence corrected** | TPS7A20 Recommended Operating Conditions note 2: "An input capacitor is not required for LDO stability". Note 3: COUT ≥ 0.47 µF effective, ESR ≤ 100 mΩ (V). One 0201 1 µF at 1.8 V is about 0.5-0.75 µF worst to typical (I). The BMI270 asks "100nF … at pin 8" (V). **Correction:** today's C62 sits 1.33 mm from U12 OUT (pin 1 at (1.19, 2.26), C62 pad at (0.92, 3.56)), not 3 mm. The merge moves the LDO's only COUT to about 3.4 mm, against the pin-table advice "as close to the OUT and GND pins as possible". The about 20 mΩ trace stays inside the 100 mΩ ESR limit, so this is a D33 MINOR, not a breach. Gyro noise V-test stays |
| PE-7 | **PARTLY REFUTED: −3, not −4** | EFM8BB51 Fig. 5.1 asks for 1 µF + 0.1 µF "as close to the pins as possible" (V). tinyPEPPER is verified: EFM8BB21 VDD on battery VCC, 47 µF 2.9 mm away, one 100 nF, no other VDD cap (pcb pad nets). **But** spec §11 Gyro isolation says "no bulk MLCC carrying ESC ripple (… ESC local bulk …) within 5 mm" (D33 protects gyro placement basics). ESC3's VDD pin (U8 pin 4 at (−3.3, −0.1)) is 2.0 mm from the gyro body: 0 of 5,630 sampled 0603 sites within 3 mm of the pin keep 5 mm (best 4.45 mm). ESC1 is constrained: 858 of 5,638 sites, best at (7.4, 3.3). ESC2 and ESC4 are free. Keep C30 (ESC3, 0.72 mm from its pin); delete C18, C24, C36 |
| PE-8 | **CONFIRMED on ratings; hold until V3c** | Nets: C1/C2 on `+BATT_IN`, the 6.3 V X6S parts on `+BATT`, one 0.5 mΩ shunt apart. At the hot-plug ring frequency (about 80 kHz) they see the same peak, so 16 V protects nothing (I). Cost: −4 to −6 µF at the hot-plug node. Together with PE-7 (−3.0 to −4.2 µF), bus C falls 13-19 % at the 55 µF end, so ζ 0.40 → 0.36-0.37. The inferred peak at 4.35 V rises from about 5.45 to 5.58-5.64 V against the EFM8BB51 VDD absolute maximum of 5.5 V (Table 4.1, V). The gain is one line only; revert it first if V3c margin is thin, or unify all 22 µF on a better-bias 10 V X6S 0603 from the P3 search |
| PE-9 | **CONFIRMED** | SLVSDH0C §9.3.4: "The voltage on the CT pin can be as high as 2.5 V"; no CT dielectric or voltage note (V). GRM033R61A103KA01J is already 5x (bom_plan); C16 is the only GRM033R71C103KA01D |
| PE-10 | **CONFIRMED** | R11 is the only 4.7k; 2.4k RTT012401FTH is 5x (bom_plan). GPIO27 high: 3.3/2.4k + 0.52 = 1.9 mA, under the 4 mA default drive. Reset: Thevenin 1.51 V / 31.5 kΩ gives 29 µA, so EN = VF + 0.07 V ≤ about 0.67 V, below VENF min 1.08 V (SLVSDH0C, V) |
| PE-11 | **CONFIRMED; sourcing risk overstated** | The report says "X6S has no LCSC listing". This is false: LCSC **C181047 = GRM033C81E104KE14D, 14,900 in stock** (LCSC product API, 2026-10-09, V), against about 2,850 + attrition for 57 per board x 50. Same 25 V 0201 KE14 series; X6S (105 °C) is the superset. The O17 condition reduces to an ordinary stock check |
| PE-12 | **CONFIRMED, conditional** | SLVSDX7D §8.2.2.1: "keep R2 smaller than 300 kΩ … lower value increases the immunity against noise injection" (V). 0.585-0.615 × (1 + 47/6.2 ± 1 %) = 4.93-5.37 V, the same as today. PR1 = VREF 0.92-1.08 × 3.772 = 3.47-4.07 V. Lines: R64 (47k), R74 (6.2k) and R71/R72 (18k) are the only uses, so the condition is real. Side effect: on battery only, the 67.9 kΩ divider lifts floating MODE from 0.3 to about 0.5 V at 50x typical IREV, past the 0.35 V row. PR1 stays at about 0.14 V, and both MODE rows with PR1 low select VIN2, so no functional change. Needs PE-1 (it removes the AP1606 gate pull-down job) |
| PE-13 | **CONFIRMED (not recommended)** | INA186A3IYFDR is "Active" in the orderable table, with no REF pin (internal GND) (V). VS is A2 and ENABLE is B3: diagonal, not adjacent balls. A 0.35 mm through via cannot sit in a 0.4 mm-pitch WCSP ball pad, so fan-out is surface only. Keep as an area fallback |
| PE-14 | **CONFIRMED (not recommended)** | EXB-18V: ±5 %, 0.4 mm pitch, mostly zero distributor stock with long lead times (Future, Farnell, Avnet listings, S). Strengthens "no" |
| PE-15 | **CONFIRMED (not recommended)** | D12 rejects the LCSC-only AGM210MAP in favour of genuine, globally stocked parts (DECISIONS.md, V). It stays an owner decision |
| PE-16 | **CONFIRMED (not recommended)** | SLVSDX7D §6.3: COUT effective 20 µF min for 1.5 A < IOUT < 3 A (V). No 47 µF 0805 bias curve |
| PE-R1 | **CONFIRMED** | No gate resistors in bom_plan: ESC1 = U6, Q2-Q7, C18-C23, R12-R18 (R12 DShot, R13-R15 10k, R16-R18 1k) |
| PE-R2 | **CONFIRMED, citation corrected** | Lines 134/143/152 are the **BB2** branch. The BB51 branch is l. 136/145/154, `mov CMP_MX, #(10h + X_Mux - 1)`: CMXN = 1 = CMP0.N1 = **P0.4** (EFM8BB51 Table 6.1, V), CMXP = the phase. Still hard-wired to the external neutral pin, so the star stays |
| PE-R3 | **CONFIRMED** | D33 keeps ESC hot loops. CSD13202Q2 is 12 V, EAS 20 mJ (spec §4.1/§4.3) |
| PE-R5 | **CONFIRMED** | LP5912 RθJA 71.2 °C/W (SNVSA77D §6.4, V). 0.30-0.35 A × 1.85 V = 0.56-0.65 W gives +40-46 K, so TJ > 125 °C at 85 °C board |
| PE-R6 | **CONFIRMED** | The house OpenFC-Lite-Mini uses U12 LP5912-1.8DRVR as the gyro LDO (kicad-cli BOM, V). D33 keeps gyro supply basics |
| PE-R7 | **CONFIRMED** | Reasoning sound (high-side CM above the 3.3 V ADC; 0.5 mV/A against ADC noise). The RP2350 ENOB figure is S here |
| PE-R8 | **CONFIRMED** | SLVSDX7D §7.4.1: in forced PWM "the inductor current changes its direction … The power flow is from output side to input side" (V). MODE = VOUT per spec §4.2 |

### Verified totals (replaces the §6 "Set" row)

| | Report | Verified |
|---|---|---|
| Parts | −12 | **−10**: PE-1 −1, PE-3 −1, PE-4 −2, PE-5 −1, PE-6 −2, PE-7 −3. PE-2 refuted |
| Lines, firm | −4 | **−3** (PE-9, PE-10, PE-11), plus PE-8 −1 after V3c |
| Lines, conditional | −7 | −6 / −7 (PE-12 adds −3) |
| Area, 22 µF on the bottom | F −5.8 / B −4.0 mm² | **F −4.7 / B −3.4 mm²** (PE-2 back; PE-7 at 3 x 1.12) |
| Power + ESC | 118 → 106 | **118 → 108** (corrected baseline 121 → 111) |

### Incidental findings (for P4, not verified in depth)

- **TPS2116 VIN2 has no nearby input capacitor.** It sits on `+5V_BST`; the nearest boost Cout (C10) is about 7.5 mm from U3 (board, I). SLVSFG1A §9-10 asks for CIN near the device. A re-netted C17 between U3 VIN2 and U5 VIN (with PE-1) could serve both if P5 brings them within about 2 mm of it.
- **The TPS7A20 DQN layout guide says not to put a thermal via under the EP** (wicking). This is moot for filled + capped via-in-pad (D41/D51), but it belongs in the NextPCB EQ note for U12.

### Verification sources

- TI datasheets as above (local copies in `bomred/pwr/ds/`, from https://www.ti.com/lit/ds/symlink/).
- EFM8BB51 Data Sheet Rev 1.0, Table 4.1, Fig. 5.1, Table 6.1.
- BMI270 datasheet pin-connection note.
- Bluejay: https://raw.githubusercontent.com/bird-sanctuary/bluejay/0368d11/src/Layouts/Base.inc and `.../BB51/A.inc`.
- LCSC product API: https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C181047 (also C76935, C2762594, C393031, C205990, C915088).
- LCSC page: https://www.lcsc.com/product-detail/C181047.html
- EXB-18V screens: https://www.futureelectronics.com/p/passives--resistors--resistor-networks-arrays/exb-18v102jx-panasonic-4105820 and https://www.avnet.com/americas/product/panasonic/exb-18v102jx/evolve-3910931/
- tinyPEPPER: `scratchpad/t08/dl/fishpepper_tinyPEPPER/tinyPEPPER.kicad_pcb`.
- Board geometry scripts: `bomred/verify_pe/pos2.py`, `gyro_pe7.py`, `c22.py`, `tp.py`.
