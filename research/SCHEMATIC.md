# OpenAIO-Whoop schematic (P4 integration, 2026-10-09)

Status: the eleven sheet files written by the P4 shards are merged into one hierarchy and pass every scripted
check. P4 critique round 1 (4 MAJOR, 22 MINOR: 25 fixed, 1 rejected) and round 2 (2 MAJOR, 19 MINOR: 19 fixed,
2 fixed in part, 0 rejected; section "P4 critique round 2") are applied; the loop (D22: no BLOCKER / MAJOR
left) continues with round 3. The board was **not** synced (`OpenAIO-Whoop.kicad_pcb` unchanged); the P5
placement conditions the schematic relies on are now scripted (`hardware/tools/check_p5_conditions.py`) and
fail 20 of 32 on floorplan v3 (open item 10).

| Check | Result |
|---|---|
| `kicad-cli sch erc` (all severities) | **0 errors, 2 warnings** (both justified below); baseline before integration: 2 errors, 105 warnings |
| `hardware/tools/check_netlist.py` | **7 ok, 0 FAIL** (N1-N6, N5 run for the FC and the RX; N6 now also checks each net's class through the .kicad_pro patterns, D82) |
| `hardware/tools/check_conventions.py` | **37 ok, 0 FAIL**, 4 warn, 5 skip |
| `sch_visual_check.py` (commons, KiCad 10 hide fix: `p2v3/p4/fix2/scripts/svc_k10.py`) | **0 hits on all 11 sheets**; it has no frame-to-frame check, so round 2 added `p2v3/p4/fix2/scripts/frame_check.py`: 0 frame overlaps on the RX and VTX sheets (was 1 on the RX) |
| `hardware/tools/check_p5_conditions.py` (new, board placement conditions) | 12 ok, **20 FAIL** on floorplan v3: P5 input, not a schematic error (open item 10) |
| `hardware/tools/check_footprint.py` R_0402_Selector_3Pad | PASS, 0 WARN (pad 3 paste-free by spec) |
| bom_plan parity (refs, values, footprints, symbols, MPN, Manufacturer, LCSC, DNP, BOM flag) | 274 of 274 symbols equal (check_netlist N4); LOGO1 is a board-only footprint |
| Netlist | 271 board parts (H1-H3 are schematic-only); 236 BOM placements, 82 BOM lines; 73 no-connect pins, 0 auto-named nets |

PDF: `hardware/OpenAIO-Whoop-schematic.pdf` (14 pages).

## Sheets

| Page | Sheet (file) | Paper | Refs | Reused from | Generator (scratchpad `p2v3/p4/`) |
|---|---|---|---|---|---|
| 1 | Root (`OpenAIO-Whoop.kicad_sch`) | A3 | - | OpenAIO root layout, signal flow left to right; power table | `hardware/tools/sch_root.py` from `sch_contract.json` |
| 2 | POWER (`power.kicad_sch`) | A3 | 38 | OpenFC-Lite-Mini power (LP5912 block), OpenAIO battery shunt + INA186; TPS61022, SGM40661, TPS2116, TPS22810 from TI/SGMICRO datasheets | `integrate/gens/power_sheet.py` |
| 3-6 | ESC1-ESC4 (`esc_channel.kicad_sch`, one file x4) | A4 | 17 x4 | OpenAIO esc_channel (BEMF network, C2 test points); EFM8BB51 + AGM210MAP stage new (D56) | `esc/build_esc.py` |
| 7 | RP2350A (`rp2350a.kicad_sch`) | A2 | 34 | OpenFC-Lite-Mini rp2350a (core, crystal, SMPS, USB series, VBAT divider, beeper FET) | `integrate/gens/build_rp2350a.py` |
| 8 | IMU (`imu.kicad_sch`) | A5 | 5 | OpenFC-Lite-Mini imu; commons blocks LDO_IMU_TPS7A2033 / IMU_ICM42688P_SPI | `imu/build_imu.py` |
| 9 | BLACKBOX (`blackbox.kicad_sch`) | A5 | 3 | OpenFC-Lite-Mini blackbox frame + SPI0 interface; PY25Q128HA NOR (D66) | `blackbox/build_blackbox.py` |
| 10 | OSD (`osd.kicad_sch`) | A4 | 12 | OpenFC-Lite-Mini osd (SN74LVC1G3157 + TLV7031 + SDM02U30), levels scaled (P4-10) | `osd/build_osd.py` |
| 11 | RX (`rx_esp32_sx1281.kicad_sch`) | A3 | 25 | OpenRX-Lite-UFL (SX1281 LDO mode, 52 MHz TCXO, Wi-Fi chip-antenna pi match, WS2812), ESP32-PICO-V3 DS Fig. 11 | `rx/build_rx.py` |
| 12 | VTX (`vtx.kicad_sch`) | A2 | 58 | OpenOSD-X v1.01 reference (video network, loop filter, PAOUT1 feed), Skyworks SE5004L EK1; no sibling sheet exists | `integrate/gens/gen_vtx.py` |
| 13 | LED (`led.kicad_sch`) | A5 | 4 | OpenFC-Lite-Mini rp2350a status-LED block (sink drive) | `integrate/gens/build_led.py` |
| 14 | PADS (`pads.kicad_sch`) | A3 | 27 | OpenFC-Lite-Mini pads (Conn_01x01 groups), OpenFC-Lite JST SH plug frame; camera plug, motor lands, ESD array new | `integrate/gens/build_pads.py` |

`integrate/gens/*` are the shard generators patched for the integration (`integrate/scripts/patch_gens.py` applies
the edits to the shard originals). After any generator run, `hardware/tools/sch_integrate.py` must run once.

## What the integration changed

- **Library pin types.** Twelve OpenDrone catalogue symbols typed every pin `unspecified`, which caused 105 ERC
  warnings and both errors (U13 SCLK and AE1 not driven). Per the ruling they are now project copies in
  `lib.kicad_sym` with datasheet pin types (list in research/LIBRARY.md); `bom_plan.json` `symbol` points at the
  copies. Pin-name cosmetics fixed on the copies: INA186, AP1606, SDM02U30, SDM02M30 (D8) names hidden, AOTA numbers
  hidden, BMI270 pins 2/3 lengthened so they reach the body.
- **PWR_FLAGs.** Regulator outputs are now `power_out` pins, so the flags on +3V3 (POWER) and +3V3_VTX (VTX) were
  removed (a flag next to a power output is an ERC error). Flags stay where the only source is passive or a
  connector: +BATT_IN, GND, +BATT, +5V_CAM, VBUS, +1V1, PA_VCC, plus a new one on VREG_AVDD (R41 RC filter, ERC asked).
  Contract rule 7 updated.
- **Rulings applied.** R84 10k -> 1k (RC0201FR-071KL; LP5912 EN 0.03-0.04 V with GPIO21 low). New **C134** 4.7 uF
  (CL05A475MP5NRNC, same line as C56) on +1V1 at DVDD pin 23. Net class pattern `*ADC_CURR*` -> Analog and `/VBUS` ->
  Power (setup_board.py NETCLASS_PATTERNS and .kicad_pro, same order). bom_plan net notes synced to the netlist for
  35 parts (U1 / C5 on SHUNT_SENSE_P_RC / N_RC, R64 on RTC_VT, R59 shunt, U22 from +3V3_VTX, O4_EN = U5_EN, ...).
  +3V3 Wi-Fi peak (0.48 A, bench-only mode) in the root power table.
- **Local labels on every multi-pin net** (contract rule 8): the 19 auto-named nets now carry labels named after the
  driving pin or the contract name: VTX RTC_CP / RTC_VT / RTC_LF, VT_MOD / VT_MOD_N1 / VT_MOD_N2, U19_XTAL1 / XTAL2,
  U19_REG1D8, U19_SPILE / SPICLK / SPIDATA, PA_RC1, Q27_B, Q27_E; RP2350A VREG_LX; POWER U5_CT; LED D5_K, D6_K.
- **Fields.** LCSC made consistent per MPN (GRM033C81E104KE14D = C181047, GRM155C80J106ME11D = C237279, sources in
  BOM-REDUCTION.md), so C12 / C15 and the other parts of those lines carry it.
- **Power-symbol references** numbered once over the hierarchy (#PWR01-#PWR247, #FLG01-#FLG08); the shards used
  colliding per-shard ranges.
- **Contract text** (sch_contract.json): J31 pinout (1 GND, 2 D-, 3 D+, 4 VBUS), USB block and PADS sheet source
  attribution, IMU pins 2/3/10/11 NC, R84, C134, VTX net names, PWR_FLAG rule, A9 decided, VBUS / ADC_CURR patterns.
- **A9 (LCSC) decided.** check_conventions A9 requires MPN + Manufacturer and an LCSC field; the LCSC value is
  required where the part has one (D60, NextPCB sources by MPN) and check_netlist N3 compares it to bom_plan. 63 BOM
  placements (25 lines) have no LCSC number. LINEUP-CONVENTIONS rule 9 carries the note.
- **Docs synced.** PINMAP §2/§3/§6 net columns use the schematic names (underscore buses, pin-side nets
  U10_USB_DM/DP, QSPI_SS, ADC_CURR, VTX_PWR_CTL, Wi-Fi AE2 row, GPIO0 button row) and list every ESP32 pin;
  DESIGN-SPEC R84 1 kOhm, IMU pins 2/3 NC, Wi-Fi paragraph marked superseded by D58. PADS sheet note follows D76
  (vertical BM04B), not the withdrawn D72 side-entry plug.
- **Tools.** New `hardware/tools/sch_integrate.py` (project-wide lib refresh, field sync, power references) and
  `hardware/tools/check_netlist.py`. `sch_build.py` no longer copies stock `property private` entries (kicad-cli
  refused those files); `sch_root.py` gives the power table a deterministic uuid.

## P4 critique round 1 (2026-10-09)

Single-writer fix pass `p2v3/p4/fix1` (scripts there; decisions D77-D80). Each item was checked against the
datasheet or file first.

| # | Sev | Item | Verdict | What changed |
|---|---|---|---|---|
| 1 | MAJOR | ESC commutation loop closed through planes (one shared 22 µF per ESC) | fixed (D77) | one 10 µF X6S 0402 GRM155C80J106ME11D per AGM210MAP, pin 3 S2 to pin 1 S1 at the lead side, via-in-pad: C20 / C23 / C21 per ESC (x4); 22 µF 0603 cell bulk out; ESC sheet note, bom_plan, DESIGN-SPEC §4.3 corrected |
| 2 | MAJOR | X1 ESR 150 Ω vs RP2350 Table 629 50 Ω | fixed (D78) | Abracon ABM8-272-T3 (C20625731, 3225 Dense land), C42 / C43 15 pF and R40 1k kept |
| 3 | MAJOR | FL1 TDK DEA 50 Ω LPF without the Semtech match / DC block | fixed (D80) | Johanson 2450FM07D0034T (house part, matched + DC blocked), lib:2450FM07D0034T + lib:FILTER-SMD_4P-L1.0-W0.5-L_W, IN at RFIO |
| 4 | MAJOR | R67 selector anchor on pad 2 (CPL centres the 0402 between lands) | fixed | footprint origin at the pad 1-2 midpoint, land spec updated, check_footprint PASS |
| 5 | MINOR | DESIGN-SPEC / PINMAP not synced to D56 / D57 | fixed | spec P4-status block, §1, §3, §4.1-4.3, §4.10, §15; PINMAP §7.1 / §7.3 |
| 6 | MINOR | root +5V row shows the HD figure of +5V_BST | fixed | +5V "0.70 A analog, about 0.25 A HD"; +5V_BST "0.70 A analog / 1.48 A HD (BEC 1.5 A cont.)" |
| 7 | MINOR | C30 redundant | fixed (D77) | deleted; ESC3's C35 carries BR-05 |
| 8 | MINOR | C17 adds little next to C8-C11 | fixed (D79) | deleted; P5 condition U5 VIN within 3 mm of C8-C11 / U3 VIN2 |
| 9 | MINOR | TPS61022 COUT ≥ 20 µF above 1.5 A not guaranteed | fixed (D79) | BEC published 1.5 A continuous; V1b 1.7 A step as characterisation |
| 10 | MINOR | PicoBlade 1.0 A contact rating | fixed | PADS note; README text owed (open item 8) |
| 11 | MINOR | J31 pin 1 inferred | fixed | V-plan gate V0-USB before the P5 freeze (spec §14), PADS note |
| 12 | MINOR | BR-05 3 mm vs 3.4-3.9 mm site | fixed | BR-05 amended to 4 mm through the +BATT plane (notes, bom_plan) |
| 13 | MINOR | U24 description quoted the page-1 surge claim | fixed | lib description: IN 28 V abs max, 2.7-20 V recommended |
| 14 | MINOR | Ralec 2.4k vs Yageo | **rejected** | RC0201FR-072K4L has no LCSC / JLC listing, 0 stock and 28 weeks at Future, obsolete at IC-Direct; the Ralec RTT012401FTH is a genuine standard part with stock |
| 15 | MINOR | L1 Manufacturer 'cjiang' | fixed | 'Changjiang Microelectronics (CJiang)' |
| 16 | MINOR | PINMAP RP0 SBUS text | fixed | PINMAP §2 pin 5 row and §5.1 comment (IO-SET row marked applied) |
| 17 | MINOR | boot / recovery sequence after D65 / D67 | fixed | spec §12.1, PINMAP F18, RX sheet button note |
| 18 | MINOR | PINMAP §7.1 / §7.3 still TI | fixed | AGM210MAP gate pins and routing; first power-up `A_X_10_96`, then `A_X_5_96` |
| 19 | MINOR | D0WD fallback and "no Wi-Fi" text | fixed | spec and PINMAP marked withdrawn (D55 / D61), F9 per D58 |
| 20 | MINOR | stale texts (PINMAP status, W25Q128JV, R84 10k, '4.7k') | fixed | all four |
| 21 | MINOR | OSD level note assumed no DC load | fixed | recomputed: 1.47 kΩ DC load, black 0.234-0.236 V, white 0.920-0.927 V; V9b check (the HF load / edge figures were corrected in round 2, item 18) |
| 22 | MINOR | VTX analog nets in Default | fixed | Analog patterns `*/VT_MOD*`, `*/RTC_*`, `*/U19_XTAL*`, `*/TCXO_OUT`, `*/XTA` (setup_board.py, .kicad_pro, check_netlist N6; the In2 / In3 Analog DRU rule covers them) |
| 23 | MINOR | LP5907 abs max and VREF window margins | fixed | deviations recorded in the PA REFERENCE note; V5c / V9b |
| 24 | MINOR | R84, R80-R82 position, SE5004L "match" | fixed | notes (R84 1k, R80-R82 at the ESP32 end), spec §4.8 |
| 25 | MINOR | VTX / RX sheet style | fixed | framed blocks with titles, notes inside each frame, Q27_C -> R65 one wire (drive stage beside the PAOUT1 feed), net `PA_BIAS_PWM` -> `VTX_AMP_PWM` |
| 26 | MINOR | +3V3_VTX budget 0.10 A | fixed | root table "0.10 A typ, about 0.17 A at max PA", spec §5.1 |

Placements 269 -> 275 in bom_plan (+8 hot-loop caps, -C30, -C17), 82 lines unchanged.

## P4 critique round 2 (2026-10-10)

Single-writer fix pass `p2v3/p4/fix2` (scripts there; decisions D81-D82). Each item was checked against the
datasheet, the source code or the board first. No part added or removed: 275 placements, 236 BOM, 82 lines.

| # | Sev | Item | Verdict | What changed |
|---|---|---|---|---|
| 1 | MAJOR | ELRS `vtx_miso` 'unset' keeps the stock 23 (PICO flash DI) under an overlay | fixed (D81) | verified: `UnifiedConfiguration.py` `hardware.update(overlay)`, `hardware.cpp` absent key → -1, arduino-esp32 2.0.17 `spiAttachMISO` → `pinMode(miso, INPUT)` (-1 → HSPI GPIO12, NC here); `"vtx_miso": -1` written explicitly in the RX note, PINMAP §6 / F8 / row 25, spec §4.7 / §12 / P4-6, contract; V9 bring-up check |
| 2 | MAJOR | PA_VCC Power only by directive label: Default on the board | fixed (D82) | verified on the netlist vs the patterns (only PA_VCC differed); `/VTX/PA_VCC` → Power in setup_board.py and .kicad_pro; contract text; check_netlist N6 resolves every net through the .kicad_pro patterns (tested: fails on the old .kicad_pro) |
| 3 | MINOR | P5 placement conditions not met on floorplan v3 | fixed in part | new `tools/check_p5_conditions.py` (D77, BR-05, D79, BR-14 with the LP5912 1 cm rule of DS 9.2.2.2, BR-08, C108, R80-R82, USB inlet, boost COUT): 12 ok / 20 FAIL; bom_plan BR-05 claim corrected (2.6-5.0 mm), U5 / U21 fallbacks named (1 µF 0201 / 10 µF 0402). Moving parts is the board stage's (no board change in this pass) |
| 4 | MINOR | R67 pad 3 carries paste (+5V bridge risk) | fixed | F.Paste removed from pad 3; land spec `no_paste`; check_footprint `no_paste` key (additive); spec §4.2 row |
| 5 | MINOR | U2_SW in Default | fixed (D82) | `/POWER/U2_SW` → Phase (0.50 mm; short U2 SW-L1 pour) pattern + directive label on POWER; N6 rule; spec net-class table |
| 6 | MINOR | TPS61022 4.8 V start-up limit (VOUT pre-bias < 0.7 V) missing | fixed | verified SLVSDX7D §6.3; POWER battery note, spec §4.1 hot-plug row, V3c pass criterion |
| 7 | MINOR | R73 / R65 34 mW at the top step vs RC0201 derating | fixed | verified (RC0201 −55..125 °C, 36 mW at 85 °C); V8 pass criterion, levers (ELRS top-count cap Ic ≤ 45 mA, Re 27R); VTX note, bom_plan; R73 stays 10R (ruling 2026-10-09) |
| 8 | MINOR | 'Cout < 40 µF' ignores C12/C13 and the O4 input | fixed | verified TI §8.2.2.4 (C3 ≈ 1.7 nF with 47k); POWER note restated; V1b steps the load in HD mode with a real O4; FF cap only if it rings |
| 9 | MINOR | stale texts | fixed | spec C17 (D79) and ESC MCU supply (D77) rows; SGM40661 description 3 A continuous / 4 A abs max; bom_plan U2 / C16 / U6-U9 notes. D1 note: TPS2116 **kept** with its path named (the TPS61022 pass-through carries a cell surge to +5V_BST = VIN2, spec §4.1 / §4.2) |
| 10 | MINOR | blackbox reads at 75 MHz, not 50 | fixed | verified (`spiCalculateDivider` even prescale ≥ 2; {133, 80} → 75 MHz; tCLQV 6-7 ns); BLACKBOX note, spec §4.9 / §10, PINMAP F7, V9 read-back CRC gate, fallback |
| 11 | MINOR | IO-SET predates D65/D67/D69/D76 | fixed | status block at the top (button, motor plugs, test vias, D69, final refs J31 / J32 / J33) |
| 12 | MINOR | RX1 5 V-logic device at power-up | fixed | RP2350A P4-11 and PADS HD notes; README item (open item 8) |
| 13 | MINOR | R44 / U16 / J32 notes, V-btn 'pressed' | fixed | RPi guide R6 = 1k; H1/H3 wording dropped (D69); Wi-Fi peak ruling cited; V-btn 'while released' |
| 14 | MINOR | check_netlist table stale | fixed | table below from the current run |
| 15 | MINOR | root POWER block lists 'ESC3 BULK' | fixed | contract content, root regenerated |
| 16 | MINOR | RX frames overlap; notes outside frames | fixed | SX1281 frame right edge 203.2; NOTES band on top, BOOT / BIND and ESP32 frames span the right column with their notes inside |
| 17 | MINOR | VTX sheet sparse (A2) | fixed in part | RTC6705 and PA blocks moved up 30.48 mm (band under the frame title closed); A2 kept: the four block columns need about 567 mm of width, an A3 re-flow means redrawing the RTC6705 and PA blocks |
| 18 | MINOR | VIDEO_OUT HF load / edge figures | fixed | 0.95 kΩ at 5 MHz, 0.60 kΩ at 10 MHz; OSD edges x0.86 / x0.80, camera x0.97 (OSD and VTX notes, spec V9b, round-1 #21 row) |
| 19 | MINOR | PNP numbers disagree (spec / PINMAP vs ngspice) | fixed | spec §4.8 and PINMAP §6 from the ngspice table (copied to `research/bomred/verify/pnp_spice/`); Q27 ≤ 114 mW vs 130 mW at 85 °C; Q27 case temperature in V5 |
| 20 | MINOR | X4 250 Ω ESR, start-up margin untested | fixed | verified (LCSC C400090); V5 start-up margin test, lower-ESR 3225 fallback (bom_plan, VTX bench note) |
| 21 | MINOR | AE1 value 'ANT 2.4G wire' ≠ pad code | fixed | value `ANT` (bom_plan + schematic); wording in the notes |


## ERC: the two remaining warnings

| Sheet | Warning | Why it stays |
|---|---|---|
| BLACKBOX | U13 pin 3 WP#/IO2 (bidirectional) on +3V3, driven by U4 OUT (power output) | Deliberate tie: WP# high disables write protection; Betaflight drives the NOR in 1-bit SPI only and the status/config registers ship as 00h, so IO2 never drives. KiCad flags every bidirectional pin on a power rail. |
| BLACKBOX | U13 pin 7 HOLD#/RESET#/IO3 (bidirectional) on +3V3, same | PY25Q128HA: HOLD#/RESET# must not float; tied high as on the house blackbox sheet. Same reasoning. |

No ERC exclusions and no severity changes are used (D7 / D21).

## check_netlist.py

| Id | Check | Result |
|---|---|---|
| N1 | single-pin nets only on no-connect pins or test points | 73 single-pin nets, all on flagged no-connect pins |
| N2 | every supply input shares its net with a capacitor to GND | 59 power-input pins on 13 supply nets, all decoupled |
| N3 | footprint on every part; MPN + Manufacturer + LCSC field on BOM parts, LCSC = bom_plan | 274 symbols, 236 BOM placements ok (63 without an LCSC number, D60) |
| N4 | refs, values, footprints, symbols, MPN, Manufacturer, DNP, BOM flag = bom_plan.json | 274 equal; LOGO1 board-only; H1-H3 not on the board (outline holes) |
| N5 | U10 RP2354A and U16 ESP32-PICO-V3 pin -> net = PINMAP.md §2/§3/§6 | 61 + 49 pins equal |
| N6 | net classes from patterns + directive labels match each net's role; contract directive labels present; each net's .kicad_pro pattern class = its netlist class (D82) | Analog 25, Gate 24, Phase 13, Power 11, RF 8, USB 2, VBAT 2, GND 1, Default 104; 20 / 20 directive labels; 0 pattern mismatches |

## check_conventions.py warnings and skips

A5 deprecated wordmark gold (the lineup decision is to copy the shipped artwork exactly); A11b `+1V1 +1V8 +3V3
+3V3_VTX +BATT_IN` (LINEUP A11 names chosen for this board); B12 x2 silkscreen font / embedding (board stage);
D1 README section "VTX dependency" (README). Skips: C3 and B18 (alpha stage), B17b (no model-fixes file), B8 / B9
(no battery or motor labels on the board yet).

## Closed deferred items

- POWER: U1 net names synced to bom_plan; O4_EN / PR1 aliases recorded as U5_EN / U3_PR1; C12 / C15 LCSC; R7 note;
  #PWR numbering; INA186 pin names; unspecified pins; P4-1/2/3/7/9/12/17/19 drawn with the accepted rulings.
- VTX: R84 1k; bom_plan nets for R64 / R59 / R60 / U22 / R65 / Q27; +3V3_VTX flag removed, PA_VCC flag kept; sch_build
  `private` bug fixed in the tool; PNP drive SPICE passed (P4-5); P4-18 (C119 deleted) noted on the sheet.
- RX: FL1 / X3 / D4 pin types (AE1 error gone); PA_NTC error gone with the VTX sheet present; D8 pin names; Wi-Fi peak
  in the power table; PINMAP LNA_IN and GPIO0 rows; D4 stays on +3V3 (ruling, bench V-LED).
- OSD: library pin types and the SDM02U30 names; cross-sheet items gone.
- RP2350A: ADC_CURR pattern; C134 fitted; +1V1 flag kept, VREG_AVDD flag added; AP1606 / AOTA cosmetics; TP9 / TP12 /
  TP13 bom_plan sheet = rp2354a.
- PADS: contract J31 pinout and source text; J31 note per D76; H1-H3 notes on the D73 25.5 mm square; VBUS flag.
- ESC: 4-instance netlist clean in the merged project (the standalone +BATT / GND errors came from the missing POWER).
- BLACKBOX: U13 SCLK now driven (typed RP2354A GPIO); WP / HOLD warnings justified above.
- IMU: pins 2/3 NC propagated to contract, bom_plan and DESIGN-SPEC; BMI270 pin types and pin length.
- All: A9 decided; #PWR collisions; commons sch_visual_check run with the KiCad 10 hide fix (the ruling's patched copy).

## Open items

1. **P4 critique loop** (D22): rounds 1 and 2 applied; round 3 to run.
2. **Board sync (after floorplan v3):** `sync_pcb.py` will add C134 (needs a site at RP2354A DVDD pin 23), drop the GND
   net from BMI270 pads 2/3, rename 19 nets (new labels), change R84's value, and must not expect H1-H3 (no board
   footprint). bom_plan.json changed (C134, symbols, R84, LCSC, nets): a floorplan run that rewrites bom_plan must merge.
   Round 1 adds: new C20/C21, C26/C27, C32/C33, C38/C39 (0402 at each AGM210MAP's lead side, pin 3 to pin 1);
   C23/C29/C35/C41 0603 -> 0402; C17 and C30 removed; X1 -> 3225 Dense land (+3 mm²); FL1 -> FILTER-SMD_4P-L1.0-W0.5-L_W
   (same pad set); R67's pads move 0.425 mm against its origin (new anchor); net PA_BIAS_PWM -> VTX_AMP_PWM; 10 more
   Analog nets.
3. **DRU net patterns** (routing stage): `*SPI0.*`, `*SPI1.*`, `*VTX_SPI.*` in OpenAIO-Whoop.kicad_dru /
   setup_board.py match no net (the nets are `SPI0_*`, `SPI1_*`, `VTX_SPI_*`): the 3 mm antenna keep-out and the
   In2/In3 sensitive-net rule miss them. Use `*SPI0_*`, `*SPI1_*`, `*VTX_SPI_*` and re-apply.
4. **R54 PS-O1** (OSD proposal: 287R -> 270R RC0201FR-07270RL, -1 BOM line, levels still inside P4-10): orchestrator decision.
5. **Camera gate G1** (J32 pitch and pin 1) and **J31 pin 1 = GND**: gate V0-USB before the P5 freeze (spec §14).
6. **ESC dead time:** closed in round 1 (first power-up `A_X_10_96`, `A_X_5_96` after V2; spec §4.3 / §12, PINMAP §7.3).
7. **ICM-42688-P** VDD 1.8 V with VDDIO 3.3 V: confirm in TDK DS-000347 before the TDK half of the V10 fly-off.
8. **README notes owed** (rulings): ELRS Wi-Fi is a bench-only mode (+3V3 0.48 A peak); SGM40661 OVP 5.75-6.12 V
   (out-of-spec sources only); user UART pads TP0/RP0 are PIO UART, 8N1, 3.3 V logic, and so are TX1/RX1 when used as the second hardware UART in analog builds (5V pads come up before +3V3; FT pads take 3.63 V unpowered); 5 V BEC 1.5 A continuous and
   the LED-strip limit in HD mode (D79); the optional PicoBlade motor plug carries Molex's 1.0 A contact rating, the
   published ESC ratings apply to soldered motor wires, plugged motors at the user's risk; the boot / ELRS recovery
   sequence (hold SW1 at power-up, write the UF2, esptool through passthrough; spec §12.1).
9. **Bench checks** carried by the sheet notes: V1 (+5V unplug dip, O4 EN thresholds), V5/V8 (R73 final value,
   RTC6705 pin 11 spur), V9 (MOTOR pads before +3V3, HD back-feed), V-LED (D4 on 3.3 V).
10. **Placement conditions for P5**, scripted in `hardware/tools/check_p5_conditions.py` (run it on the board;
    floorplan v3: 12 ok, 20 FAIL: 9 of 12 hot-loop caps off their AGM210MAP's side or > 1.5 mm from pins 1-3;
    BR-05 ESC1 / ESC2 bulk 5.0 / 4.7 mm and C19 / C31 100 nF > 1.2 mm; U5 VIN 6.1 mm from C8-C11 (> 3 mm);
    U21 IN 14.8 mm from C13 (> 1 cm, LP5912 DS 9.2.2.2); C108 2.7 mm from RTC6705 pins 39/40; R81 at the
    RTC6705 end; U24 12.5 mm and D7 5.9 mm (other side) from J31; boost C10 / C11 5.3 / 7.2 mm from VOUT).
    Fallbacks if P5 cannot meet U5 / U21: a 1 µF 0201 (GRM033R61A105ME44D) at U5 VIN, a 10 µF 0402
    (GRM155C80J106ME11D) at U21 IN (decision). The conditions (sheet notes): each ESC hot-loop cap across its AGM210MAP pins 3/1 at the lead side
    with via-in-pad (D77); BR-05 (amended) phase-B cap within 4 mm of EFM8 VDD through the +BATT plane; U5 VIN within
    3 mm of C8-C11 / U3 VIN2 (D79); BR-14 C13 between the U4 and U21 IN pins, BR-08 C49 / C54 at pins 44 / 54, C108 at
    RTC6705 pins 39/40; R80-R82 at the ESP32 end.
11. **Cosmetic / tooling:** TPS22810 pin names "EN/UVLO" and "GND" touch inside the small body (not flagged by the
    checker); the commons `sch_visual_check.py` still needs the KiCad 10 `(hide yes)` fix upstream; .kicad_pro
    `sheets` lists only Root until a GUI save; reference gaps (C3, C4, ...) kept so the parallel floorplan's refs stay
    valid (the "P4 annotation closes gaps" step is deferred).

## Integration decisions to log (DECISIONS.md)

- A9: MPN + Manufacturer required, LCSC where the part has one (D60); checked by check_conventions A9 and check_netlist N3.
- OpenDrone symbols with unspecified pins are used through typed project copies (lib:), not ERC exclusions.
- Every multi-pin net carries a local label (no auto-named nets on the board).
- C134 takes the next free number after C133; references stay stable (no gap closing during the parallel floorplan).
- `sch_integrate.py` is a mandatory step after any sheet generator.

## Reproduce

Round 2 (scratchpad `p2v3/p4/fix2`, generators in `fix2/gens` copied from fix1, `OAW_HW` selects the hardware dir):

```
scripts/bom_fix2.py HW/bom_plan.json ; scripts/lib_fix2.py HW/lib.kicad_sym ; scripts/contract_fix2.py HW
scripts/patterns_fix2.py HW ; scripts/blackbox_fix2.py HW/blackbox.kicad_sch
scripts/regen.sh (esc rx osd vtx rp2350a power led pads + sch_integrate) ; scripts/root_build.py HW ; HW/tools/sch_integrate.py HW
scripts/{spec,pinmap,ioset,decisions,bomred,schematic_md}_fix2.py research/<file>.md
checks: kicad-cli sch erc ; check_netlist.py ; check_conventions.py ; svc_k10.py ; frame_check.py ; check_p5_conditions.py
```

Round 1 (scratchpad `p2v3/p4/fix1`, generators in `fix1/gens`, `OAW_HW` selects the hardware dir):

```
scripts/lib_fix.py HW ; kicad-cli sym upgrade --force HW/lib.kicad_sym
scripts/bom_fix.py HW/bom_plan.json ; scripts/contract_fix.py HW ; scripts/pro_patterns_fix1.py HW/OpenAIO-Whoop.kicad_pro
OAW_HW=HW: gens/build_esc.py --root HW/OpenAIO-Whoop.kicad_sch ; gens/power_sheet.py HW ; gens/build_rp2350a.py --hw HW
  gens/build_rx.py HW/OpenAIO-Whoop.kicad_sch ; gens/gen_vtx.py HW ; gens/build_osd.py --out-root HW ; gens/build_pads.py
scripts/root_build.py HW ; HW/tools/sch_integrate.py HW
scripts/spec_fix1.py research/DESIGN-SPEC.md ; scripts/pinmap_fix1.py research/PINMAP.md ; scripts/decisions_fix1.py research/DECISIONS.md
```

P4 integration (first build):

```
# scratchpad p2v3/p4/integrate (HW = /home/user/OpenAIO-Whoop/hardware)
scripts/retype_lib.py HW && kicad-cli sym upgrade --force HW/lib.kicad_sym
scripts/bomplan_p4i.py HW fields ; scripts/contract_p4i.py HW
gens/gen_vtx.py HW ; gens/build_rp2350a.py --hw HW ; gens/power_sheet.py HW ; gens/build_led.py HW ; gens/build_pads.py
scripts/root_build.py HW ; HW/tools/sch_integrate.py HW ; scripts/pro_patterns.py HW/OpenAIO-Whoop.kicad_pro
kicad-cli sch export netlist ... ; scripts/bomplan_p4i.py HW nets NETLIST ; scripts/docs_p4i.py research/PINMAP.md research/DESIGN-SPEC.md
kicad-cli sch erc ; HW/tools/check_netlist.py ; HW/tools/check_conventions.py ; sch_visual_check (KiCad 10 hide fix)
```
