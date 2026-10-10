# OpenAIO-Whoop schematic (P4 integration, 2026-10-09)

Status: the eleven sheet files written by the P4 shards are merged into one hierarchy and pass every scripted
check. P4 critique round 1 (4 MAJOR, 22 MINOR) is applied: 25 fixed, 1 rejected (section "P4 critique round 1"
below); the loop (D22: no BLOCKER / MAJOR left) continues with round 2. The board was **not** synced: floorplan
v3 is placed in parallel and `sync_pcb.py` runs after it. `OpenAIO-Whoop.kicad_pcb` is unchanged.

| Check | Result |
|---|---|
| `kicad-cli sch erc` (all severities) | **0 errors, 2 warnings** (both justified below); baseline before integration: 2 errors, 105 warnings |
| `hardware/tools/check_netlist.py` | **7 ok, 0 FAIL** (N1-N6, N5 run for the FC and the RX; N6 Analog 25 after the VTX patterns) |
| `hardware/tools/check_conventions.py` | **37 ok, 0 FAIL**, 4 warn, 5 skip |
| `sch_visual_check.py` (commons, KiCad 10 hide fix: `p2v3/p4/fix1/scripts/svc_k10.py`) | **0 hits on all 11 sheets**; the unpatched commons copy still reports 9223 hidden-field false hits |
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
| 21 | MINOR | OSD level note assumed no DC load | fixed | recomputed: 1.47 kΩ DC / ~0.27 kΩ HF load, black 0.234-0.236 V, white 0.920-0.927 V, edges x0.57; V9b check |
| 22 | MINOR | VTX analog nets in Default | fixed | Analog patterns `*/VT_MOD*`, `*/RTC_*`, `*/U19_XTAL*`, `*/TCXO_OUT`, `*/XTA` (setup_board.py, .kicad_pro, check_netlist N6; the In2 / In3 Analog DRU rule covers them) |
| 23 | MINOR | LP5907 abs max and VREF window margins | fixed | deviations recorded in the PA REFERENCE note; V5c / V9b |
| 24 | MINOR | R84, R80-R82 position, SE5004L "match" | fixed | notes (R84 1k, R80-R82 at the ESP32 end), spec §4.8 |
| 25 | MINOR | VTX / RX sheet style | fixed | framed blocks with titles, notes inside each frame, Q27_C -> R65 one wire (drive stage beside the PAOUT1 feed), net `PA_BIAS_PWM` -> `VTX_AMP_PWM` |
| 26 | MINOR | +3V3_VTX budget 0.10 A | fixed | root table "0.10 A typ, about 0.17 A at max PA", spec §5.1 |

Placements 269 -> 275 in bom_plan (+8 hot-loop caps, -C30, -C17), 82 lines unchanged.

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
| N3 | footprint on every part; MPN + Manufacturer + LCSC field on BOM parts, LCSC = bom_plan | 268 symbols, 230 BOM placements ok |
| N4 | refs, values, footprints, symbols, MPN, Manufacturer, DNP, BOM flag = bom_plan.json | 268 equal; LOGO1 board-only; H1-H3 not on the board (outline holes) |
| N5 | U10 RP2354A and U16 ESP32-PICO-V3 pin -> net = PINMAP.md §2/§3/§6 | 61 + 49 pins equal |
| N6 | net classes from patterns + directive labels match each net's role; contract directive labels present | Analog 15, Gate 24, Phase 12, Power 11, RF 8, USB 2, VBAT 2, GND 1, Default 115; 19 / 19 directive labels |

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

1. **P4 critique loop** (D22) still to run on the merged schematic; the sheet notes carry the P4 items for it.
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
   (out-of-spec sources only); user UART pads TP0/RP0 are PIO UART, 8N1, 3.3 V logic; 5 V BEC 1.5 A continuous and
   the LED-strip limit in HD mode (D79); the optional PicoBlade motor plug carries Molex's 1.0 A contact rating, the
   published ESC ratings apply to soldered motor wires, plugged motors at the user's risk; the boot / ELRS recovery
   sequence (hold SW1 at power-up, write the UF2, esptool through passthrough; spec §12.1).
9. **Bench checks** carried by the sheet notes: V1 (+5V unplug dip, O4 EN thresholds), V5/V8 (R73 final value,
   RTC6705 pin 11 spur), V9 (MOTOR pads before +3V3, HD back-feed), V-LED (D4 on 3.3 V).
10. **Placement conditions for P5** (sheet notes): each ESC hot-loop cap across its AGM210MAP pins 3/1 at the lead side
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
