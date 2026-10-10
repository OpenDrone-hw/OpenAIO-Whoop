# Floorplan v4 placement brief (binding)

Date 2026-10-10. Binding for the v4 placement stage. The machine-readable copy is
`p2v3/v4/brief.json` (scratchpad), built by `p2v3/v4/brief_work/mk_brief.py`.

- **Frame.** All positions are in mm, relative to the board centre (113.2, 113.2), on KiCad axes (+y down).
  The front corner is (+x, −y).
- **Holes.** LEFT (−12.75, −12.75), REAR (−12.75, +12.75), RIGHT (+12.75, +12.75).
- **Binding inputs.** D69/D70/D72/D75-D77, D85, D88, D89-D96, the owner's 10:30 notes and ANTENNA-WIFI §9.
- **Owner's 10:30 notes.** Through vias until proven impossible. Shortest connections, routed on L1/L6. No wasted
  space. GPIO and schematic remaps are allowed.
- **Sources.** The 13 lens results (`p2v3/v4/tricks/*`), the synthesis (`p2v3/v4/SYNTH.md`), the diet and its
  verifier (`diet/`, `dietchk/`), the outline and its verifier (`outline/`, `outline_verify/v2/`), the antenna verdict,
  the adversarial verdicts C1/C2 (`verify/`) and the v3 baseline (repo board, `route/loop2/STATE.md`).

## 1. Corrections to the synthesis (verdicts applied)

| Claim | Status | What the placement stage uses instead |
|---|---|---|
| C1: placer −40 % HPWL → fewer unconnected | **Did not hold** | The length cut is real: audit MST 1721 → 1102 (gp, −36 %) and 1205 (polish, −30 %). But the gp board had **63 hard DRC errors**: 33 courtyard, 16 in rule areas, 8 shorts, 5 clearance, 1 hole. One erouter pass gave ctl (v3) 308, gp 263, pol 282. gp *raised* the cross-side edges from 131 to 136; polish lowered them to 102. Fixes: exact legaliser (§9), term V = xside cross-side MST edges, seeds from both gp and polish. Claim no unconnected gain before T1 on a legal board. |
| C2: escape templates give 185/185 vias; diet ring sites ×5.4 | **Did not hold** | There are **183** real signal pins (U10 pins 4/5 are gone under D89). Vias-only DRC is clean on all 11 ICs: different-net via pitch 0.530-0.535, hole-to-hole 0.330-0.335. 3 sites break "RF: no vias" (U16-2, U18-22, U19-35), leaving 180. The 8 EFM8 corner sites (pins 1/11, diagonal in2) cannot take a stub (0.283 mm gap, 0.35 needed): use via-in-pad on the corner pad instead (DRC-clean on U6). 65 of the 180 are via-in-pad. Ring sites (all classes): ×3.4-3.7 inside the rings, ×2.3-2.5 over the windows. |
| Templates vs **D96** (new check, `brief_work/d96chk.py`) | **45 sites illegal** | Every in1/in2 site on U6-U9, U18 and U19 overlaps the *package* EP metal. The gap from EP metal to the terminals is EFM8 0.25, SX1281 0.30 and RTC6705 0.29 mm, below a 0.35 via. As generated, **135/183** pins have a D96- and DRC-legal site. 45 pins must be re-templated to vip/vipend/out. The 3 RF pins get no via. U10 (52/52 real pins) and U16 (28/28) pass. |
| Diet: paddle shrink frees ring sites | **Signal gain 0 under D96** | The package EP metal does not shrink, so smaller lands add only GND-via room. Clean signal sites (pads only, v3 positions, `dietchk/vs_*.json`): U10 21 → 28, U16 21 → 28, U18 10 → 11, U19 3 → 3. The signal gain comes from a clear far side, removed-land toe areas and the minimum RF set. |
| A3/G5: no-net lands as in-ring sites | **Narrowed** | Only toe sites outside the package outline count (D96). U10 spare lands qualify. U16 LGA lands removed under the body give none. |
| U16 V4b land set | **Fix** | V4b lacks lands 26/30/31, which D96 says stay (internal nodes). The STRICT map uses GPIO7-10 and GPIO38, whose lands V4b removed. U16's final land set is therefore V4b + 26/30/31 + the lands of every GPIO in the frozen map. |
| A1 runs | **Changed** | Legalise first (gap ≥ 0 on exact polygons; the place.py default is −0.1). Add polish seeds and S 25.6 runs (§9). |

## 2. Numbers to beat

| Metric (tool) | v3 | Best seen so far | v4 target |
|---|---|---|---|
| HPWL, placer metric | 1833.8 mm | 1105.7 (gp, illegal) | report |
| Octilinear MST (netlength `audit.py`) | 1721 mm (1687 without PIOUART0) | 1102 gp / 1205 pol (illegal) | **≤ 1300** on a legal board |
| Unconnected, multi-pass loop | 251 | — | **< 251 (T2), then 0** |
| Unconnected, 1 erouter pass from stripped copper | 308 (ctl) | 263 (gp, illegal) | **≤ 262 (T1)** |
| Legal via points (loop2 `viamap.py`), routed / stripped | ~917 / 2775 | 3231 (gp, stripped) | stripped **≥ 3200** |
| Boxed pads (`boxed.py`) | 143 of 343 | — | **≤ 70** |
| Escape sites legal in place (`tmpl.py place`) | 51 of 185 | 180/183 self-only, 135/183 D96 | **every pin that needs a layer change** |
| Cross-side MST edges (`xside.py`) | 131 | 102 (pol) | **≤ 83** |
| Side-crossing signal nets (`vip.py`) | 68 | — | **≤ 45** |
| Centre-band tiles: demand vs packable sites | 112 vs 10 | — | every tile **≤ 0.8 × supply** |
| Hot loops OK / phase vias / gate side-split vias | 4/12 / 50 / 8 | — | **12/12 / 0 / 0** |
| Boost hot loop | 7.7 mm | — | **≤ 3 mm** |
| L4 drop at 48 A (`plane_cg.py`) | worst 46-56 mV (ESC1/ESC2, v3 geometry) | — | **≤ 40 mV** (report if above) |
| Wi-Fi RF path / 5.8 GHz path / RX feed | ~15.7 / ~12.0 / — mm | — | **≤ 2 (no via) / ≤ 4.6 / ≤ 4** |

## 3. Outline (`outline_verify/v2/outline_v4.py`)

Parameters: `prims(S, ("chamfer", 3.35, 1.0), webs)`, HOLE_HALF 12.75, HOLE_D 3.5, ear ring R 2.4, WEB 1.0-4.0,
part band 0.30, copper-to-edge 0.20, flange D5.2 for bodies and D4.6 for pad copper.

| S | Role | Webs L / REAR / R | Board mm² | Parts per side mm² | Free after edge parts F / B mm² | Seed board |
|---|---|---|---|---|---|---|
| **26.4** | primary | 1.0 / 1.0 / 1.0 | 696.6 | 642.4 | 573.3 / 531.0 | `edge_S26.4_v2.kicad_pcb` |
| **25.6** | parallel runs; adopt if T1 is within 5 % of the 26.4 winner and every tile ≤ 0.8 | 3.6 / 1.0 / 3.6 | 664.1 | 609.7 | 540.9 / 498.2 | `edge_S25.6_v2.kicad_pcb` |
| 24.8 | rejected | — | 630.8 | 576.8 | — | 4 arc pads fail copper-to-edge |

Both v2 boards pass placement-level DRC with the patched rules (D96 note). The v3 placement uses 422.9 / 436.1 mm² of
courtyard on F / B.

## 4. Fixed edge parts (poses: x, y, rot, side; S 26.4, then S 25.6 if it differs)

| Ref | Function | S 26.4 | S 25.6 |
|---|---|---|---|
| J13 | M4 motor pad (ESC4) | 6.85, −11.95, 180, F | 6.45, −11.55 |
| J7 | M2 motor pad (ESC2) | 11.95, −6.85, 90, F | 11.55, −6.45 |
| J10 | M3 motor pad (ESC3) | −11.95, −6.05, −90, F | −11.55, −6.05 |
| J4 | M1 motor pad (ESC1) | 6.05, 11.95, 0, F | 6.05, 11.55 |
| J26 / J27 / J28 / J29 | VHD / GND / TX1 / RX1, LEFT web arc | (−9.663, −12.466, 84.8) / (−10.114, −11.119, 58.2) / (−11.119, −10.114, 31.8) / (−12.466, −9.663, 5.2), F | same |
| J20 / J21 / J22 / J33 | LED / 5V / BZ− / GND, RIGHT web arc | (10.114, 11.119, −121.8) / (11.119, 10.114, −148.2) / (12.466, 9.663, −174.8) / (9.663, 12.466, −95.2), F | same |
| J31 | USB BM04B vertical, 5.45 mm from the REAR hole (D91) | −8.896, 8.896, 135, B | −8.507, 8.507 (6.0 mm) |
| J32 | camera SM03B, mouth toward the front corner | 6.662, −6.662, 135, F | 6.262, −6.262 |
| J23 / J25 / J24 | CAM / GND / 5V row in front of the J32 mouth, pitch 1.6 | (9.631, −7.369) / (8.5, −8.5) / (7.369, −9.631), 45, F | each 0.4 mm closer to the centre on x and y |
| J2 / J3 | battery + / −, `BattPad_D1.7mm_PTH1.1_V4` | −12.0, ∓1.15, 0, F | −11.6, ∓1.15 |
| AE2 | Wi-Fi chip, `..._D90Void`; GND row toward the edge (y 12.55), feed row inboard (y 11.95) | −3.774, 12.25, 0, B | −3.385, 11.85 |
| AE1 | RX wire hole | −12.3, **y ∈ [5.3, 9.3]** (variable, M7) | −11.9, y |
| Boost site (B) | D92 | centre (−6.6, 0.4), 5.0 × 4.4 | same |

The edge parts are fixed in the placer (`--fixed`); only AE1 y moves.

## 5. Footprint set (26 refs; J16-J19 deleted under D89)

| Refs | Footprint | Source |
|---|---|---|
| U10 | `QFN-60_..._EP3.4_Dense_V4` (EP land 2.40; lands 4/5/55-59 off) | repo `hardware/lib.pretty`. **Provisional**: land set regenerated after the pin-map freeze (`gen_v4.py`) |
| U16 | `LGA-48_..._ESP32-PICO_V4b` | `dietchk/lib_v4b.pretty`. **Provisional**: + lands 26/30/31 (D96) + every GPIO land the frozen map uses |
| U19 | `QFN-40_..._RTC6705_Dense_V4b` (keeps 1, 11, 17, 26) | `dietchk/lib_v4b.pretty` |
| U6-U9 | `QFN-20_..._EFM8BB51_V4b` (EP 0.90, lands 2/7/15/16 off, paste 52 %) | `dietchk/lib_v4b.pretty` |
| U18 | `QFN-24_..._SX1281_V4` (EP 1.90, lands 6/9/10/14 off) | repo lib |
| U13 | `USON-8_..._PY25Q128HA_V4` (tab lands off) | repo lib |
| U4, U21 / U3 / J2, J3 | `WSON-6_..._LP5912_V4` / `TI_SOT-583_DRL_TPS2116_V4` / `BattPad_D1.7mm_PTH1.1_V4` | `dietchk/lib_cfix.pretty` (courtyard fixes) |
| J20-J29, J33 | `SolderPad_0.8x1.0mm_V4` | repo lib |
| AE2 | `ANT-SMD_4P-L1.0-W0.5_Johanson_2450AT07A0100_D90Void` | `outline_verify/v2/lib_v4.pretty` |
| BMI270, power parts (AGM, U2, U5, U12, U22, U20) | unchanged datasheet lands (D95) | — |

Parity: write project-lib symbol variants without the removed pins (D96). Never use DRC exclusions. Copy the V4b,
cfix and D90Void files into `hardware/lib.pretty`.

## 6. Hard constraints (the legaliser rejects any violation)

| ID | Rule |
|---|---|
| H1 | 0.2 mm body-to-body on exact courtyard polygons (gap ≥ 0; J31 at 135° exactly); PART_EDGE_BAND 0.30 (solder-pad class exempt); pad copper ≥ 0.20 from the edge; MOUNT D5.2 bars bodies; MOUNT_PAD D4.6 bars pad copper; TAB_T1/T3/T4; no part in a rule area that forbids it; no other-net pad overlap |
| H2 | Escape template sites (D96-legal kinds, §11): no other-net pad, hole or silk within 0.30 mm on either side. Behind a ring, only the IC's own core decaps or same-net copper. Never a ring on a ring. D70 stacking is allowed elsewhere (D88) |
| H3 | Every ESC cell single-sided; the D77 10 µF on the FET's side across pins 1-3; gates on one layer, 0 vias |
| H4 | RF: K1-K7 (§7). AE2 feed ≤ 2 mm on B, no via. V1 ≥ 3 mm from RTC6705/PA/BPF/U.FL, the boost loop and phase copper. F over V2: no IC, pour, EP, GND land ≥ 0.8 × 0.8 or U.FL tab. RX feed ≤ 4 mm with FL1 at U18-22. SPI0 ≥ 3 mm from AE1. U19/U20 EPs not stacked (Tj) |
| H5 | D92 boost on B at its site: loop ≤ 3 mm, no via in the loop, In4 unbroken (BOOST_GND_L5), GND vias outside, ≥ 3 mm from V1 |
| H6 | Side balance: F − B courtyard within ±30 mm² |
| H7 | Battery entry macro M6 at fixed geometry; L4 not cut between R1 and the cells |
| H8 | Mating zones (D72/D76): USB_MATING (B) clear; J32 mouth holds only the CAM/GND/5V row; DNP PicoBlade bodies over the ear necks (D65: courtyards may meet at the front corner) |
| H9 | D96: no other-net via or track under package EP metal or terminal metal |

## 7. Rule areas

| Action | Areas |
|---|---|
| Keep (from the v2 boards) | MOUNT_* / MOUNT_PAD_* ×3, PART_EDGE_BAND, TAB_T1/T3/T4, RF_RX_ROOT (K4), USB_MATING, BOOST_GND_L5, WIFI_VOID_V1 (B/In4/In3; 26.4: x −4.324..−1.724, y 11.6..13.2), WIFI_VOID_V2_L2 (In1 fills) / _L3 (In2 tracks) / WIFI_FAR_F (x −4.324..−3.224, y 11.45..13.05), WIFI_GND_LINK (B) |
| Delete | WIFI_ANT_KO, the WIFI_ANT_KEEPOUT footprint area, RF_RX_ANT, RF_RX_ANT_L6, RF_RX_EXIT, RF_VTX_CHAIN |
| Add | K2: circle D2.0 at AE1, all layers. K3: 0.6 mm half-width strip U18-22 → FL1 → AE1 (In1: no tracks; DRU: no non-GND via). K5: 0.5 mm strip around RF_PAOUT1/RF_PA_IN/RF_PA_OUT/RF_UFL. K6: keep RF_PAD_CUTOUT(_L3). K7: RF_VTX_UFL becomes a height check only (> 0.6 mm within 2.5 mm of J1) |
| DRU | `outline_verify/v2/gen_dru.py`: MOUNT flange; D90 void (feed nets only, no via, GND link inside WIFI_GND_LINK); D90 pads (AE2/C132/C133/R88 only); D90 far side (no SMD GND ≥ 0.8 × 0.8); D92 boost vias. Mirror all of it in `geo.py area_ok`. Re-anchor SHUNT_CORRIDOR, RF_PAD_CUTOUT*, K3 and K5 after placement |

## 8. Macros (rigid; the placer moves each as one)

| Macro | Content |
|---|---|
| **M1 ESC cell ×4** | EFM8 + 3 AGM210MAP + 3 × 0402 10 µF + 100 nF at pin 4 + VDD bulk (≤ 4 mm) + 6 × 0201 BEMF + RTX 2.4k (≤ 1 mm from pin 17) + C2 test vias at pins 6/5. **(a) Edge row:** AGMs along the edge from the motor pad, EFM8 gate corner (pins 8-14) toward the lead strip. **(b) L-wrap:** in the QFN frame AGM_C (0.6, 4.45), AGM_B (4.15, 4.45), AGM_A (4.45, −0.725), mirrored in x on B. Box 9.19 × 9.19 mm. The 0.85 mm gate channel fails at the 0.15 mm Gate width (C3 partial: 3 clearance errors; 0 at 0.12 mm), so use 0.95 mm or a scoped 0.12 mm intra-cell gate rule. Use (b) at the front pair M2/M4. Supply: 3 +BATT + 3 GND vias per AGM, via-in-pad. BEMF: phase pairs on one merged land, 1 filled via, NEUTRAL bar to pin 18. Phase: EP5+EP8 island on the cell layer to the PTH motor pad. Free: phase-letter-to-pad order. **Seed sides:** A = ESC1+ESC3 F, ESC2+ESC4 B (front pair on B); B = the swap |
| **M2 U10 core** | U10 on F with a clear ring far side. 0201 decaps on B in the 3.4 × 3.4 core: power pad ≤ 0.6 mm from its pin's template via, GND pad on a paddle GND via. VREG_LX/L2 loop on L1. Optional for U16 (4.9 core) and U19 (4.2 core). C88/C102/C103 stay on the IC side. EFM8/BMI270/SX1281/RTC6705 get tangential far-side 0201s on the pins' own vias |
| **M3 VTX** | U20 rotated so pins 1-5 face U19-35. L3/C110 ≤ 0.6 mm from pin 35. 1 RF via + 2-4 GND via-in-pad; U20-3 ≤ 1.5 mm from that via. FL2 → J1 on F ≤ 2.5 mm, J1 on the centre side of the PA. Re-place C111-C118, C123, R66. Variant: U19 on F (no RF via) when the front pair is on B |
| **M4 Wi-Fi** | U16 on B at the rotation that points pin 2 at AE2. C133/R88/C132 on B within 1 mm (R88 moves). Series 0201 0R + 1 DNP shunt. GND row → B.Cu link ≤ 0.3 mm → 2 GND vias just outside V1; each shunt gets its own In4 via outside V1. Pass gate: the bench 3 m upload test (realistic range 2-4 m) |
| **M5 Boost** | U2/L1 on B at the site; C8-C11 in an arc within 3 mm; C7 at L1's input; GND pour on B; 4 GND vias outside the loop; 0 input vias |
| **M6 Battery** | R1's +BATT_IN end butts J2; its +BATT end has a 3 × 4 field of 12 vias (0.40 pitch) into L4; R1 + pour on B; J3 solid on L2/L5 + 4 helper vias; C1/C2/D1 straight across J2-J3 |
| **M7 RX corner** | U18 with FL1 at pin 22, TCXO at the outer end, feed ≤ 4 mm. AE1 y scored by term W against USB_MATING and the rear flange. U18 ring never over J31 pads |
| **M8 5 V chain** | U24 ≤ 2 mm from J31; U3 between U24 and the boost output; U4/U21 at the edge of their load group, majority side; 1 via per rail pad group (2 for +5V_BST/+5V_HD) |

## 9. Placer objective (`tricks/placer/place.py`; weights in mm of equivalent length)

| Term | Definition | Weight | State |
|---|---|---|---|
| L | Class-weighted length: HPWL up to 8 pads, octilinear MST above. RF 4, USB/VBAT/Phase 2, Power/Gate 1.5, Analog 1.2, others 1. GND and +BATT skipped | 1 / mm | exists (MST proxy → octilinear) |
| V | Cross-side MST edges (**xside.py definition**) | 4 / edge; 6 if xside > 83 after anneal 1 | change (C1) |
| P | `rp_opt.py` (U10) + `esp_opt.py` STRICT=1 (U16), NOFIX=1, full re-opt every 20k steps | 1 / mm | build |
| S | 2-pad passive off its owning IC's side (core decaps and macros exempt) | 3 / part | build |
| D | Decap over its max distance: 1.0 mm (≤ 100 nF, from pin or template via), 2.5 mm bulk, 4 mm EFM8 VDD | 5 / mm over | build |
| G | Two caps' GND pads 0.3-0.6 mm apart | −0.5 / pair | build |
| W | AE1 to boost SW node and battery pads ≥ 5 mm; gyro and crystals to boost SW ≥ 5 mm | 2 / mm short | build |
| C | Block cohesion | 0.02 × block HPWL | exists |
| E | Pin needing a layer change with no D96-legal site; spare U10 land toe site next to such a pin −1 | 8 / pin | build |
| T | Anneal 2: per-tile transitions above 0.8 × packable supply (3 × 3 and 5 × 5) | 10 / excess | build |
| B | Anneal 2: boxed pads (`boxed.py`) | 8 / pad | build |

- **Moves:** shift, size-matched swap, 90° rotation, 180° rotation (2-pad passives and FETs; check LED polarity and the
  L1 SW end), side flip, pin swap, rigid macro move.
- **Legaliser:** exact KiCad courtyard polygons, gap ≥ 0, rule areas by layer and flag, other-net pad clearance,
  template keep-outs. `--gap −0.1` is forbidden.
- **Apply:** `verify/C1/apply.py`. It picks the orientation whose pads match `xf()` within 0.02 mm.
- **Anneal 1:** 24 runs, `--init gp --iters 1e6`:
  - S 26.4: seeds 1-4 × U18 F/B × seed sides A/B (16 runs);
  - S 25.6: seeds 1-4 × the best (U18, sides) pair (8 runs).
- **Anneal 2:** the best 4 per outline, `--init v3` on the applied legal board, T and B on, M1 and M3-M6 locked.

## 10. Pin-swap groups (live in the placer, frozen at pipeline step 7)

| Group | Allowed sets |
|---|---|
| G1 U10 RP2354A | UART0 TX {0,2,12,14,16,18,28} / RX {1,3,13,15,17,19,29}. CRSF stays on hardware UART0. UART1 TX {4,6,8,10,20,24} / RX {5,7,9,11,21,25}, (TX%4, RX%4) ∈ {(0,1),(2,3)}; Betaflight also lists 22/23, unused until C5 closes. SPI0 SCK {2,6,18,22} MOSI {3,7,19,23} MISO {0,4,16,20}; SPI1 SCK {10,14,26} MOSI {11,15,27} MISO {8,12,24,28}; flash and gyro may swap instances. ADC_CURR/VBAT {26-29} (R-side pins 40-43, the one fixed anchor). MOTOR1-4: any of 0-25, any order. OSD: 3 consecutive GPIOs. LED_STRIP: 0-25. GYRO_CS/FLASH_CS/GYRO_INT/LED0/LED1/BEEPER/HD_EN/CLKIN: any. 2 spares |
| G2 U16 ESP32-PICO-V3, STRICT | Fixed: GPIO0 (pin 23), GPIO3 (40), GPIO1 (41). Excluded: 2, 5, 12, 15, 20, 6, 11. OUT {4,7,8,9,10,13,14,19,21,22,25,26,27,32,33}; INONLY {34-39} only for RADIO_MISO/BUSY/DIO1 and PA_DET/PA_NTC (ADC1 preferred). Open: GPIO7-10 are in the VDD_SDIO domain; confirm they work on the -V3, or drop them |
| G3 EFM8 | Fixed, Bluejay BB51 layout A. Free: phase letter → package → motor pad |
| G4 Motor order | M1-M4 → ESC free (Betaflight resource remap) |
| G6 Passives | 180° flips |

| Remap of | Files touched at the freeze |
|---|---|
| U10 | `hardware/sch_contract.json` (pin → net, fw strings); `rp2350a.kicad_sch` via `gens/build_rp2350a.py` + `sch_integrate`; PINMAP §2, §4.3 (CLKIN PWM slice), §4.4, §5.1 config.h defines (SPIx, GYRO_1, FLASH_CS, MOTORn, UARTn, PINIO1, LED*, LED_STRIP, BEEPER, OSD_*, ADC_*), §5.4 presets |
| U16 | `sch_contract.json` U16 entries; `rx_esp32_sx1281.kicad_sch` + its text box (`gens/build_rx.py`); PINMAP §6 (F19, F8); `research/bomred/rx-vtx.md`; ELRS layout JSON (radio_*, led_rgb, vtx_nss/sck/mosi, vtx_amp_pwm/vpd/vref, patched VTX_PWR_CTL/PA_NTC keys; `vtx_miso: -1` written explicitly) |
| ESC/motors | PINMAP §5.1 MOTORn_PIN; esc_channel phase → pad nets if the ESC-to-pad map changes; PINMAP §7.3 → A_X_15_96 |
| Then | `gen_v4.py` land sets (U10/U16), symbol variants, `sync_pcb.py` (parity 0), `check_netlist.py` N5, `check_conventions.py` |

## 11. Escape templates (`tricks/escape/tmpl_self_d95.json`, `tmpl.py`)

| IC | Signal pins | D96-legal as generated | Allowed kinds (D96) | Far-side keep-out mm² / free core |
|---|---|---|---|---|
| U10 | 52 | 52 | in1/in2/in3/out/vip/vipend | 15.0 / 3.4 × 3.4 |
| U16 | 28 (pin 2 RF: no via) | 27 | in1/in2/vip/vipend/out | 7.7 / 4.9 × 4.9 |
| U18 | 14 (pin 22 RF) | 6 | vip/vipend/out | 3.9 / 2.25 × 2.25 |
| U19 | 18 (pin 35 RF) | 7 | vip/vipend/out | 4.9 / 4.2 × 4.2 |
| U6-U9 | 4 × 14 | 4 × 7 | vip/vipend/out (corner pins 1/11: via-in-pad) | 3.9 each / < 1 |
| U13 / U11 | 7 / 8 | not checked (tie-bar metal / Bosch handling note) | check before using in1/in2 | 2.0 / 2.2 |

- Re-run `tmpl.py self` with the allowed kinds on the placed rotations.
- About 110 of the 180 sites are filled+capped via-in-pad.
- Router candidate generator (escape P5): per-pin axis points (pad centre, pad end, +0.175, +0.275, +0.475); ≥ 0.51 mm
  between different-net vias; ≥ 0.345 mm from a stub to a via.

## 12. Through-via budget

| Purpose | v4 target | Rule |
|---|---|---|
| GND pad clusters | ≤ 110 | one filled via-in-pad per cluster (term G) |
| Edge fence | 46 at 2.5 mm, ≥ 30 via-in-pad | 1.25 mm within 5 mm of AE1/AE2/J1/U20 |
| RF fence / interior stitching | ~10 at 1.4 mm / ≤ 30 | stitching only where the 2.5 mm coverage check fails; ≥ 2 ties per L1/L6 island |
| Power | ~110 | AGM 72 (3+3 × 12), R1 12, J3 4, boost 4 GND, +5V_BST/+5V_HD 2 each, other rails 1 per pad group |
| Phase across sides | 0 | single-sided cells |
| Signal | ≤ 140 | reserved before any track |
| **Total** | **~480** | v3: 365 holes + 150 still needed, against 65 packable sites |

| Block | Budget |
|---|---|
| ESC cell (each) | 18 supply + 3 BEMF + 2 C2 + 1 EP + ≤ 2 signal = ≤ 26 |
| Battery M6 / boost M5 | 16 / 4 GND + 2 +5V_BST |
| U10 / U16 / U18 / U19 | 52 / 27 / 13 / 17 sites reserved (U19 + 1 RF via + 2-4 GND VIP; U16 + 2 AE2 GND + 1 per shunt) |

**Per tile:** demand ≤ 0.8 × packable supply on 3 × 3 and 5 × 5 grids (`via_economy` `sites.py` + `packall.py` +
`tiles.py`). Demand = side-crossing nets with pads in the tile + GND clusters + 3 per AGM supply pin.

v3 per tile, demand / supply:

| Tile | Blocks | Demand / supply |
|---|---|---|
| (1,0) | RP2350A/ESC4/RX | 30 / 3 |
| (2,0) | VTX/IMU | 12 / 6 |
| (0,1) | POWER/ESC3 | 21 / 0 |
| (1,1) | PADS/RP2350A/OSD | 38 / 4 |
| (2,1) | VTX/ESC2/OSD | 23 / 3 |
| (0,0) | — | 3 / 9 |
| (0,2) | — | 2 / 10 |
| (1,2) | — | 20 / 8 |
| (2,2) | ESC2 corner | 1 / 22 |

## 13. Stackup and rule status

| Item | Status |
|---|---|
| D85 inner-layer DRU | Applied in the repo (`.kicad_dru` md5 40a5db3d) |
| v4 DRU (MOUNT, D90 ×3, D92) + K1-K7 + MOUNT_PAD/TAB areas | Scratch only (`outline_verify/v2`). The placement stage applies it in `hardware/tools/setup_board.py` (check_rules + selftest). If blocked, it returns the patch to the orchestrator |
| Router L3 change filter | Router side. §8.2 applies to SPI clocks, gyro, VTX SPI and PA controls; slow nets get the D33 waiver; ESC hot-loop caps are the change points |
| Filled+capped via-in-pad | Already the fab spec |
| Layer roles L1 sig / L2 GND / L3 sig / L4 +BATT / L5 GND / L6 sig | Kept. No L4 rail islands for now |
| Stack reorder (thin L2-L3 / L4-L5 cores) | **Owner + fab query**; not assumed. New decision D97+ if adopted (D96 is taken) |
| 0201 → 01005 | **Owner** (assembly tier); not assumed |
| HDI 1+4+1 | Out (D95); only after the stop-rule evidence |

## 14. Pipeline

1. Work copy of the repo project. Run `sync_pcb` (D89 schematic). Delete J16-J19.
2. Swap footprints per §5.
3. Write the outline per candidate. Place the edge parts at the §4 poses. Apply the §7 rule areas and the v4 DRU.
4. Strip every track, every via and the v3 L1/L6 pours. C1 found the start unconnected count rose 444 → 499 because
   moved parts lost or shorted their F/B pour connections.
5. Run `extract.py`, anneal 1, `apply.py`, then legalise.
6. Score with the independent tools (§15). Run anneal 2 on the best 4.
7. Freeze the pin map: the §10 files, `gen_v4`, symbol variants, parity 0, N5.
8. Make reservations before any track, in this order: template vias, GND via-in-pad per cluster, power vias, fence
   via-in-pad. Then the silk label placer: labels only over via-illegal spots, logo on an ear or web.
9. Run T1, then T2. Write the review pack (`board_diff.py` + `images/review/CHANGES.md`).
10. Only if 26.4 won: once it reaches 0 unconnected with every tile ≤ 0.8, retry 25.6.

## 15. Acceptance

| Gate | Pass condition |
|---|---|
| Checkpoints (before routing) | Placement DRC: 0 courtyard / rule-area / short / clearance / hole errors. Every pin that needs a layer change has a legal site. xside ≤ 83. Side-crossing signal nets ≤ 45. Audit MST ≤ 1300. Every tile ≤ 0.8. Boxed ≤ 70. Stripped viamap ≥ 3200. Hot loops 12/12. Phase and gate vias 0. Boost loop ≤ 3 mm. RF lengths per §2. H4 distances measured. L4 drop ≤ 40 mV (report if above). Balance ≤ 30 mm² |
| T0 | `kicad-cli pcb drc --schematic-parity --refill-zones --severity-all` with the **repo** project files after the v4 rules are in the repo. State which files were used |
| T1 | One loop2 `erouter.py` pass from stripped copper: `--inner --margin 3 --maxvias 5 --maxlen 25`, D85 rules. Pass: **≤ 262** unconnected on a legal board (ctl 308) |
| T2 | Loop2 chain (erouter passes, snapvia, gndprune/gvprune) → **< 251** |
| T3 | 0 unconnected, 0 DRC errors, parity 0, with the repo files |
| Stop rule (owner 10:30) | If T2 stalls at 251 or above: write the evidence (per-tile demand vs supply, blame hard-fail edges with no legal site, levers used). Only then take stack reorder, 01005 or HDI to the owner |

## 16. Owner items (none blocks the plan)

- O1 stack reorder.
- O2 01005 passives.
- O3 12 MHz CMOS oscillator instead of X1 + C42 + C43 + R40. A reviewer must first confirm the RP2350 XIN CMOS wording
  and USB boot.
- O4 test vias become via-less SMD lands, and TP9 is deleted (changes D67).
- The EFM8 land of 0.90 is below the 40-50 % paddle guidance.
- Silk over filled vias (an owner-rule change; not assumed).
- Not recommended: removing the shunt + INA186, or the gyro LDO.

## 17. Pending verifications (the placement stage re-checks them on its own board)

| Check | State |
|---|---|
| C3 (L-wrap cell) | Partial: geometry fits; gate channel fails at 0.15 mm (see M1) |
| C4 (RF minimum set and AE2 distances) | No verdict yet |
| C5 (pin maps) | `verify/C5/legal.py` reports no violations. GPIO7-10 (VDD_SDIO domain) still to confirm |
| C6 (plane and via current) | Partial: 46-56 mV at 48 A on v3 geometry for ESC1/ESC2, so the 40 mV target is not met yet |
| Templates | U13 / U11 under-body sites: check against D96 and the Bosch handling note |

## 18. HDI addendum (D97 ADOPTED 12:50) - binding over sections 6, 9, 11, 12, 14, 15 where they differ

| Item | Through-via plan (above) | HDI plan (now) |
|---|---|---|
| Via set | 0.35 / 0.20 through only | laser micro 0.10 / 0.25 L1-L2, L6-L5 (copper filled, in pad); buried 0.20 / 0.35 L2-L5 (POFV), staggered 0.25 mm from its microvia; through vias for power / phase fields and where useful |
| Layer change L1 <-> L3 | through via (blocks both surfaces) | microvia in pad + buried via (blocks only F at the pad and L2-L5 at the buried site) |
| GND / +BATT pads | through via each | microvia in pad into L2 / L5 (GND); +BATT: microvia + buried into L4, or through-via arrays for current |
| H2 far-side keep-out | 0.30 mm disks around every template site | applies to through vias only; microvias need no far-side clearance; buried sites need clear L2-L5 copper (other buried vias, L3 / L4 tracks, plane antipads) |
| Escape templates (section 11) | template through-via sites | microvia in each signal pad (or 0.1 mm off the pad end where the pad is narrower than 0.25 mm), buried via staggered 0.25 mm toward free inner space; D96 still holds (never under other-net package metal) |
| Double-siding | ring-on-ring forbidden | ring-on-ring allowed (microvias do not reach the far side); back-to-back decaps directly under the IC power pins with microvias on both ends are preferred |
| Placer via term V | 4 mm per cross-side edge | per layer change: about 1 mm micro-only (to L2/L5 GND or a same-side neighbour via L3 with buried), 2 mm micro+buried; through vias 4 mm; the T / B tile and boxed terms drop out for HDI-legal pads |
| Density target | via-site limited | maximise density (owner: no wasted board space); outline candidates S 26.4 and 25.6; report the smallest outline whose T1 passes |
| T1 router | loop2 erouter, through vias | the HDI-capable router from scratchpad/p2v3/v4/hdirouter (micro + buried + through); erouter through-only as the lower-bound control |
| Acceptance | section 15 | same gates with H2 relaxed as above; T3 unchanged: 0 unconnected, 0 DRC errors, parity 0 with the repo project files |

## 19. Method change (D101, D102, 2026-10-10 15:00) - binding over sections 5, 8, 9, 14
The round-1 annealed placements scattered the AGM FETs and the blocks (cohesion weight 0.02) and left free area. The
placement now goes tile-first: each schematic block becomes a compact tile, tiles are arranged Matrix-style (ESC cell
tiles at their motor pads, symmetric), inter-tile wiring is minimised, then the outline shrinks. Full datasheet lands
on every IC (D101). Annealing only inside tiles. Acceptance: legal placement, HDI trial route (hdirouter ROUTER.md),
the smallest outline that still routes.

## 20. Constructive placement order (D105, 2026-10-10 15:15) - binding over section 19
1. Fixed frame: outline (start S 25.6), holes, motor pads, the 12 AGM210MAP at their motor pads with hot-loop caps,
   battery pads + shunt, USB J31 by its hole, IO pad groups on the edges; J32 placed for the CAM row / video path.
2. ICs by signal flow, GPIO map solved between interconnected ICs, partner ICs stacked back to back (D104).
3. Every passive next to the pin it connects to; passives fill the remaining space.
4. Compaction to no unused area beyond routing needs; shrink the outline while the HDI trial route closes.
