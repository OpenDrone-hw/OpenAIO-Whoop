# Design spec (proposal, P0)

**Status: proposal for a board that has not been designed.** Nothing below
exists as a schematic or a layout. This file fixes the targets and the part
choices for phase P0 of [BUILD-PLAN.md](BUILD-PLAN.md). Decisions D1-D44 of
[DECISIONS.md](DECISIONS.md) are applied, including the O4 Lite support
(D13-D17), the area cuts (D18), the P0 rule of D22, the real-placement area
evidence of D23 and the decisions of review rounds 3-4 logged as D24-D44 (the
named D21 rule breaks among them). The BOM reduction of 2026-10-09 (D52-D54,
[BOM-REDUCTION.md](BOM-REDUCTION.md) §3 items BR-01 to BR-26) is applied on top:
286 → 245 placements and 89 → 76 BOM lines against the corrected baseline
(§9.4). D54 kept the owner-call items at their conservative default (OC-1 "no
AGM210MAP in rev1" was reversed by the owner's D56; the PA NTC and VTX power-down
hook, the PA_VCC selector until V5 stay; the TP10 / SWD pads became test vias or
went with D67). D45-D51 (P2 floorplan and board setup) are in DECISIONS.md and
FLOORPLAN.md and are not restated here.

**P4 schematic status (2026-10-09, binding over older text in this file).** The schematic
(`hardware/*.kicad_sch`, research/SCHEMATIC.md) implements the later owner and
orchestrator decisions; where a paragraph below still describes an earlier
variant, these win:

- **ESC stage (D56, D77):** 12x AGMSEMI AGM210MAP P+N half-bridges (one per
  phase, the Matrix II stage) with **one 10 µF X6S 0402 hot-loop capacitor per
  AGM210MAP** from pin 3 S2 (+BATT) to pin 1 S1 (GND) at the cell's lead side
  (C20 / C23 / C21 per ESC, x4); the phase-B one is also the EFM8 VDD bulk within
  4 mm of VDD pin 4. The TI CSD25310Q2 + CSD13202Q2 text of §4.3 is the documented
  fallback. Bluejay first power-up `A_X_10_96`, then `A_X_5_96` after V2.
- **USB (D57, D76):** vertical JST SH 1.0 BM04B-SRSS-TB (J31: 1 GND, 2 D−, 3 D+,
  4 VBUS, pin 1 orientation gated by V0-USB), SGM40661 OVP load switch on VBUS
  (U24), TPD2EUSB30 D+/D− ESD at the plug (D7). Pogo pads, alignment holes and the
  clip-on adapter (O3) are gone.
- **RX (D55, D58, D61):** ESP32-PICO-V3 SiP, the D0WD-V3 fallback is withdrawn;
  ELRS Wi-Fi restored with the Johanson 2450AT07A0100001T chip antenna (AE2) and
  the R88 / C132 / C133 pi match (bench-only update mode). SX1281 RFIO feeds the
  house **Johanson 2450FM07D0034T** front-end filter (matched to the SX1281,
  internally DC blocked).
- **Parts:** blackbox Puya PY25Q128HA-DFH-IR (D66); 12 MHz crystal Abracon
  ABM8-272-T3 (D78, RP2350 Table 629 ESR ≤ 50 Ω); camera plug J32 + pads (D64);
  plug-ready motor lands (D65); shared boot button SW1 (D65); test vias (D67);
  holes on 25.5 mm (D73).
- **5 V BEC (D79):** published **1.5 A continuous**; the 1.67 / 1.82 / 1.98 A
  figures are converter capability, not a rating (§5.3).
- **Power table:** +5V carries 0.70 A analog / about 0.25 A HD (the O4 is on
  +5V_BST ahead of the mux, D53 BR-10); +3V3_VTX 0.10 A typical, about 0.17 A at
  the top PA step.
- **P4 critique round 2 (2026-10-10, D81):** ELRS layout `"vtx_miso": -1` written explicitly (the stock
  23 is the PICO's flash DI); board net classes come from the .kicad_pro patterns (PA_VCC Power, U2_SW
  Phase; N6 cross-check); TPS61022 4.8 V start-up limit in the hot-plug analysis (V3c); blackbox reads at
  75 MHz (F7 / V9 read-back gate); PNP-stage numbers from the P4 ngspice run (§4.8, V5 / V8); P5
  placement conditions scripted in `hardware/tools/check_p5_conditions.py`.

**P0-close items still open:**

1. **O15**: NextPCB EQ for the 0.35 mm-pitch leadless parts. Closed: D53 dropped
   it once BR-01 to BR-04 landed, and the ESP32-D0WD-V3 fallback that kept it is
   withdrawn (D55, D61).
2. **O17**: NextPCB BOM quote by exact MPN on the full BOM (stock gate per line).
3. **O20**: the user UART pad group (TP0 RP0 5V GND) has no compliant top site at
   real size (sketch v5, §10); P2 decides between the bottom, the left edge with a
   reduced antenna-root spacing, or an owner pad lever.

**Area** is settled by D23 on the real placement (floorplan preview: 342 of 345
parts at 0.2 mm, 0 violations). The budget method stays a P2 tracking tool:
`budget_v6.py` reads **100.5 % top / 92.5 % bottom** like-for-like after the
round-4 ESC cell correction (budget v5 before it: 97.15 / 97.04 %, 7.4 / 6.7 mm²
over the 96 % figure), §9. Round 4 corrected the CSD25310Q2 pinout (source, not
drain, on the exposed pad, §4.3); the preview was drawn with the old cell, so P2
re-places the ESC cells with the phase-via strips of §4.3.

The P1 board setup was applied to the round-3 revision (`setup_board.py`, §8.4:
board-spec check 31/31, DRC 0, rules parsed, self-test 0 failures); round 4
leaves it untouched and lists what the next P1 re-apply takes over (tab T1 on the
right edge, the iron-rework rule for all parts, the ganged-mask scope, the
RTC6705 chain start; §8.4, §15.6). Round-3 BLOCKER and MAJOR findings: 23 of 23
fixed (§15.7); round 4: 10 of 10 addressed, none rejected (§15.8).
Circuit-detail values for the schematic loop are listed in §15.5 (D22, owner
P4). Every number here is a target, a datasheet value or a calculation, and each
one says which.

Date 2026-10-07, revised the same day after review rounds 1-4 (electrical,
RF and firmware, manufacturing and lineup) and decisions D12-D44; BOM reduction
D52-D54 applied 2026-10-09. Inputs: the
owner direction and owner rules (2026-10-06), [DECISIONS.md](DECISIONS.md),
the 1-2S / O4 Lite study (scratchpad `study-1-2s/RECOMMENDATION.md`), the
research tracks 00-09 (Matrix photo analysis, Matrix deep dive, landscape, ESC,
VTX/OSD, FC/RX/firmware, power/connectors/mechanics, NextPCB DFM, prior art,
OpenDrone reuse map) with their verification logs, the JLCPCB and NextPCB
capability pages, live LCSC and Digi-Key stock and temperature ratings
(2026-10-07) and [LINEUP-CONVENTIONS.md](LINEUP-CONVENTIONS.md). The competitor
material is in [COMPETITION.md](COMPETITION.md); the FC, RX and ESC pin plans
are in [PINMAP.md](PINMAP.md).

Status tags used below: **V** read from a primary source, **S** screened
(secondary source, distributor index, research track not re-derived), **I**
inferred (calculation or engineering judgement). Loss and thermal numbers come
from `calc/thermal_v3.py`, area numbers from `spec/budget_v6.py`, the
key-package floorplan from `spec/sketch_v5.py` (all scratchpad; earlier
versions kept).

---

## 1. Scope and targets

Scope is fixed by the owner decision of 2026-10-06: **1S only, match the BetaFPV
Matrix 1S 5IN1 II** in envelope and features, beat it on measured and documented
ratings, blackbox, repairability and open documentation, not by adding scope.

| Item | Target (proposal) | Basis |
|---|---|---|
| Input | 1S LiPo / LiHV, 3.0-4.35 V operating; electronics regulate down to 2.5 V cell under sag (the VTX PA is rated from 3.0 V only); 2S not supported ("1S" silk at the battery pads; D14); 2S belongs on a separate future HD-only board with 20-30 V FETs, not this PCB (D19) | owner decision; TPS61022 runs to 0.5 V once started, starts at 1.8 V (V, TI SLVSDX7D); SE5004L VCC 3.0-5.5 V (V) |
| Board body | 26.4 x 26.4 mm square (Matrix II: 26.35 mm, photo-measured) | V (01) |
| Orientation | Diamond mount like the Matrix: flight-forward points at a body corner. Front corner rounded with R 5.8 mm and carries no ear | V (01, photo); I (radius) |
| Ears and holes | 3 ears (left, right, rear corners), ring OD 4.8 mm. Holes **Ø 3.5 mm** on a **25.75 x 25.75 mm square**, non-plated cut-outs in P1; plated holes with a GND annulus are decided at P2 with the ball fit (O2, O16) | Matrix II holes Ø 3.48-3.57 on 26.0 mm, plated (V, 01). 25.75 mm halves the worst offset in 25.5 and 26.0 mm frames to 0.18 mm radial (I, from 06 §3.3) |
| Overall size | 30.55 x 30.55 mm including ears (Matrix II 30.9 mm); outline area 696.6 mm² net of holes | I (outline script, §9) |
| Mounting | 3-point soft mount with BetaFPV-type shock balls; 1.0 mm board matches the Matrix ball groove | V (01, 06 §3.3) |
| Thickness | 1.0 mm finished, 6 copper layers | §8 |
| Weight | **≤ 3.5 g** bare (solder-pad build, no battery pigtail, no antenna). Estimate 2.8-3.1 g (§6). Matrix II solder-required: 3.76 g | I (§6); V (Matrix, 01) |
| ESC | 4 channels, Bluejay on EFM8BB51 (I grade), P+N direct drive, bidirectional DShot, EDT. Stage per D56: 12x AGMSEMI AGM210MAP P+N half-bridge (PDFN 3.3x3.3, one per phase, the Matrix II stage), hot path 34.1 mΩ typ, one 10 µF hot-loop cap per AGM210MAP (D77); TI CSD25310Q2 + CSD13202Q2 (40.2 mΩ) = documented fallback | §4.3, §4.4 |
| ESC rating to publish | **Measured only, by protocol V4 (§14)**: continuous A per channel (one channel loaded, others 2 A) and on all four, with the stated airflow, 25 °C ambient, VTX 25 mW, every part inside its own rating; burst duration at 12 A and 18 A from the measured hover steady state. No number above the model is claimed. Model (`thermal_v3.py`, PA-case term included), one channel / all four: h 80 W/m²K 4.7-5.1 / 2.8-3.3 A; h 64 1.8-3.7 / 1.9-2.5 A; h 55 0-1.4 / 1.2-1.8 A; at h 30 the board is out of rating at hover. The D20 figures (study model without the PA-case term, h 64-80) are 4.3-5.2 / 3.0-3.8 A. HD mode (analog VTX off, D17): 4.9-5.6 / 3.5-4.1 A at h 64-80. With the heat levers of §5.4: 4.7 / 2.9-3.0 A at h 55. Bursts to FET 110 °C: 12 A for 1.3-4.2 s at h 80 and 0-2.4 s at h 55; 18 A under 0.5 s. The Matrix stage on the same model: 5.7-5.9 / 3.2-3.8 A at h 80, 12 A for 5.5-7.3 s. The D12 stage is **not** better than the Matrix's; what the board offers is a published protocol, the same rig on a Matrix II, and the numbers | §4.3, §5.4 |
| VTX | RTC6705 + Skyworks SE5004L PA on the cell, U.FL. **Levels as ELRS pushes them** (five, fixed in `freqTable.h`, V): `0` (PA biased at minimum drive, not pit), `RCE` (pit at boot, then 25 mW), `25`, `100`, `400`. 25 and 100 mW are closed loop on the PA detector; `400` is open-loop full drive (ELRS YOLO setpoint) behind a hardware **power ceiling** of 27 dBm at the U.FL (§4.8) and is published as "max (measured, power-limited)" per board: 400 mW is **not** guaranteed at sag or hot, and the closed-loop 400 mW patch is O6 gate 2. **Channels:** ELRS pushes 48; the patched firmware refuses the L band (5362-5621 MHz) and holds pit (O6 gate 5); the 40 channels from 5645 to 5945 MHz are supported, the 24 inside both datasheet bands (RTC6705 5725-5865, SE5004L 5150-5850 MHz) are rated, the other 16 published as measured after the lock check of V5. "Max" is continuous only at high airflow (hover needs h ≥ 63-82 W/m²K, §4.3). In HD mode the analog VTX is held off in hardware (D17) | §4.8 |
| Digital VTX | DJI O4 Lite on solder pads **VHD GND TX1 RX1** (D13, D16): hardware UART1 with MSP DisplayPort, supply +5V_HD from the 5 V boost output `+5V_BST` (ahead of the USB mux, D53 BR-10) through a TPS22810 load switch enabled by FC PINIO1 (GPIO27) and a filtered cell threshold with hysteresis (on at a cell of 3.23-3.82 V, shed at 2.74-3.14 V with 1 % resistors and +5V_HD 4.93-5.37 V; POWER P4-1; D15, BR-22, §4.2); no SBUS pad. One video system at a time: the HD line also holds the RTC6705 and the PA reference off (D17) | §4.2, §4.8, PINMAP |
| OSD | Analog: Betaflight PIO framebuffer OSD on the RP2354A (no OSD chip). It overlays on the camera's sync and generates none: no camera, no OSD (the Matrix's AT7456E free-runs). HD: MSP DisplayPort canvas on the O4 | §4.5, §4.8 |
| RX | Serial ExpressLRS 2.4 GHz, ESP32-PICO-V3 (in-package flash and 40 MHz crystal; D52 BR-01, D55; the D0WD-V3 fallback is withdrawn, D61) + SX1281 (BR-25), +13 dBm, no PA/LNA (Matrix parity), Johanson 2450FM07D0034T front-end filter, insulated wire monopole trimmed to resonance. **ELRS Wi-Fi restored (D58):** Johanson 2450AT07A0100001T chip antenna (AE2) at a board edge with the R88 / C132 / C133 pi match; Wi-Fi is a bench-only update mode (disarmed, +3V3 peak 0.48 A); updates also through Betaflight serial passthrough | §4.7 |
| FC | RP2354A, Betaflight ≥ 2026.6.2, one gyro per revision published in the target (no lottery) | §4.5, §4.6 |
| Blackbox | 16 MB SPI NOR, Puya PY25Q128HA-DFH-IR (D66; JEDEC 0x852018 is in Betaflight's m25p16 table), SPI0 | §4.9 |
| 5 V BEC | 5.15 V nominal at the boost (4.93-5.37 V worst case). **Published: 1.5 A continuous (D79)**: above 1.5 A the TPS61022 needs ≥ 20 µF effective COUT (DS 6.3), which the four 22 µF 0603 meet only typically. Converter capability (not a rating), calculated nominal peak **1.67 A at 2.8 V, 1.82 A at 3.0 V, 1.98 A at 3.2 V** in (TI method, −30 % inductance, peak at 80 % of Isat, η 0.85 / 0.86 / 0.87). Design loads: analog 0.70 A; HD 1.43-1.48 A (O4 + FC + RX + buzzer; LED strip and user 5 V not budgeted in HD mode, 1.73 A with them). Published per VIN and board temperature from V1 (TPS61022 TJ ≤ 125 °C) | §4.2, §5.3 |
| Current / voltage sense | 0.5 mΩ shunt (four-pad Kelvin land, net-tie) + INA186A3 (50 mV/A, `ibata_scale` 500), VBAT 1:1 divider; scales measured and set in the target | §4.1 |
| Connectors | BT2.0 pigtail on two plated holes (user-fitted); 4 plug-ready motor lands (solder or optional Molex PicoBlade header, D65); **USB on a vertical JST SH 1.0 BM04B-SRSS-TB** (D57, D76) with SGM40661 VBUS OVP and TPD2EUSB30 D+/D− ESD on the board; **camera on CAM 5V GND pads plus a JST 0.8 mm SM03B-SURS-TF plug** (D64); U.FL for the VTX; RX antenna wire hole; user UART pads **TP0 RP0** (PIOUART0) with 5V GND (site open, O20); LED, BZ+ BZ-; O4 pads VHD GND TX1 RX1 | §4.10 |
| Fab / assembly | NextPCB turnkey (partial turnkey with consigned lines), DFM-compatible with JLCPCB except silk legibility (0.8 mm labels, D12; owner sign-off for this board pending, O11); through vias only, OpenDrone 0.35/0.20 via (D6); deliberate rule breaks as named, scoped DRU rules (D21) | §8, §15 |

---

## 2. What to optimise, ranked

| Rank | Goal | Metric | Target | Bench measurement |
|---|---|---|---|---|
| 1 | Electronics rail that survives sag (no FC/RX brown-out; video to 3.0 V, the PA minimum) | +5V at full design load (analog 0.70 A; HD 1.48 A) while the input is swept 4.35 → 2.6 V | analog: ≥ 4.85 V at VIN ≥ 2.8 V (setpoint 5.15 V, worst-case low corner 4.93 V less the mux drop); HD: ≥ 4.75 V down to the O4 shed threshold (2.74-3.14 V cell), the O4 shed before +5V drops further; ripple ≤ 50 mV p-p (forced PWM, 1 MHz); no reset of FC or RX down to VIN 2.5 V, on USB hot-plug or on unplug | bench supply + electronic load, scope at the camera pad and on +5V |
| 2 | Honest ESC rating, measured on the same rig as a Matrix II | continuous A per channel with every part inside its rating, measured at the part (hottest FET ≤ 100 °C, EFM8 ≤ 125 °C, RTC6705 case ≤ 80 °C, RP2354A, gyro, SX1281, NOR, ESP32-PICO-V3 (in-package flash), crystals, TCXO and SE5004L case ≤ 85 °C, TPS61022 TJ ≤ 125 °C, X6S caps in the cells ≤ 105 °C) under V4; burst durations | published as measured with the airflow stated; no claim above the model (§1). Cost of D12 against the Matrix stage: path 40.2 mΩ typ (48.8 max) vs 34.1 (50.0 max); model −0.8 to −1.0 A continuous and a quarter to a half of the 12 A burst time at the same airflow | thermocouples per V4; same rig on a Matrix II |
| 3 | Weight | grams on a 0.01 g scale | ≤ 3.5 g bare (Matrix 3.76 g) | scale, first 5 prototypes |
| 4 | Measured VTX power and clean spectrum | output per channel at 25/100/max at 3.7 V; 2nd harmonic | 100 mW within ±3 dB unit to unit at 5850 MHz without calibration; 25 mW: unit spread measured and published from V5 (the detector rise at 14 dBm is within the uncalibrated ADC error, so no uncalibrated tolerance is claimed); ±1.5 dB at both levels only with per-unit calibration (patch 8); max ≤ 27 dBm at the U.FL on every unit (power ceiling); at 5650/5750/5945 MHz ±3 dB on the sample after the ELRS interpolation fix; full per-channel table and the unit spread published; 2f ≤ −30 dBm (EN 300 440 limit) | calibrated power sensor + 30 dB attenuator; spectrum analyser to ≥ 18 GHz; ≥ 5 boards |
| 5 | RX link | conducted sensitivity at 500 Hz packet rate; desense with every on-board aggressor active | within 2 dB of the SX1281 datasheet figure; ≤ 3 dB desense | ELRS link stats + attenuator chain |
| 6 | Gyro noise | hover pre-filter gyro noise from blackbox | ≤ the Matrix II on the same frame and motors | 60 s hover logs, FFT |
| 7 | Crash survival | BetaFPV wall test (5 m run, 20 hits) | 0 of 4 boards damaged, ears included (Matrix II on Air75 II: 2 of 4) | BetaFPV protocol [01] |
| 8 | Repairability and openness | test access, documentation | C2 pads per ESC, SWD, FC and RX boot pads, full schematic/BOM/pinout, repair map | review at P7 |
| 9 | Upstream firmware | merged targets | Betaflight target in betaflight/config, ELRS target JSON, stock Bluejay build (no custom hex) before release | PR merge |

---

## 3. Class bars

| | BetaFPV Matrix 1S 5IN1 II | FusionFPV UD 4IN1 (prototype, [fusionfpv.com/aio](https://fusionfpv.com/aio/)) | OpenAIO-Whoop target |
|---|---|---|---|
| Size, mount | 26.35 mm body, 30.9 mm with 3 ears, 26 mm 3-point | 39.32 x 25.76 mm, undermount racer | 26.4 mm body, 30.55 mm with 3 ears, 25.75 mm 3-point |
| PCB | 1.0 mm, layers not published | 4 layers, 0.8 mm, high-Tg | 6 layers, 1.0 mm, through vias |
| Weight | 3.76 g (pads) / 4.13 g (plugs) | n/p | ≤ 3.5 g (pads) |
| FC | STM32G473 + AT7456E OSD | STM32G473CEU6 + AT7456E | RP2354A + PIO OSD (needs camera sync) |
| Gyro | 6-part lottery | BMI270, own supply | one part per revision (BMI270 or ICM-42688-P after fly-off) |
| ESC | 4x BB51, 12x AGM210MAP P+N (34 mΩ), "12 A cont / 18 A peak" | 4x BB51, 12x SiA517DJ, 5 A design target | 4x BB51, 12x AGM210MAP P+N (34 mΩ, D56) with one hot-loop cap each (D77), rated by measurement only (V4) |
| RX | ESP8285 + SX1281 onboard | external | ESP32-PICO-V3 + SX1281 onboard, ELRS 4.x mainline |
| VTX | RTC6705 + RFPA5542 (EOL) + MM32F003, 25-400 mW | RTC6705 + RTC6659-class PA, 25/100/250/MAX | RTC6705 + SE5004L, no VTX MCU (ELRS drives it), 0/RCE/25/100/max (power-limited; 400 closed loop after O6) |
| Digital VTX | separate 3IN1 HD board | n/p | O4 Lite pads + switched supply on the same board, one system at a time (D13-D17) |
| Blackbox | 16 MB | 16 MB | 16 MB |
| USB | SH1.0 vertical + adapter | 4 pogo pads + clip-on adapter | SH1.0 vertical (BetaFPV adapter compatible, D57 / D76) with VBUS OVP and D+/D− ESD on the board |
| Openness | none | page only | schematic, layout, BOM, measured ratings |

---

## 4. Architecture per block

Each block gives the options weighed, the decision, the key parts and the
numbers. **Stock gate.** The P0 gate is "≥ 5x the 50-board quantity" (250 for a
part used once per board) **at the distributors NextPCB turnkey buys from**: HQ
Online plus its quote engine (Digi-Key, Mouser, Element14, Avnet, ...), not
LCSC (track 07 §3). The figures below are LCSC live reads on 2026-10-07 unless
marked; they are a first screen only. P0 closes with a NextPCB BOM quote by
exact MPN on the full BOM (O17); lines it cannot fill get a per-line decision
(§15.3, D60: stock and consignment no longer block a part). Parts already manufactured on an
OpenDrone board are marked **[PU]** (PARTS-USED.md). BOM symbols of parts with
no LCSC listing carry `LCSC = none (<distributor> <PN>)`, which the LINEUP A9
checker accepts as a filled field.

**Temperature grades** (V, LCSC/maker listings 2026-10-07, unless marked).
The board limit is set by the 85 °C parts at their local board temperature. There
is no placement halo (D69: H1 / H3 are void), so a part next to a FET group or the
PA is rated at that local temperature; V4 places its thermocouples at the 85 °C
parts nearest the FET groups and the PA:

| Grade | Parts |
|---|---|
| 85 °C (bind the board) | RP2354A (ambient), BMI270, SX1281, Puya PY25Q128HA-DFH-IR (−40..85, D66), **ESP32-PICO-V3** (−40..85 ambient, set by its in-package flash; V, Espressif PICO series datasheet v1.3; D55, no placement halo, D69), SE5004L (case), RTC6705 (Tj −40..85, so case ≤ about 80 °C), Abracon ABM8-272-T3 12 MHz crystal (−40..85, D78) and Yajingxin 8 MHz crystal (−40..85), YXC 52 MHz TCXO (−30..85), Walsin BPF and Johanson 2450FM07D0034T LPF (−40..85, D80), XINGLIGHT LEDs (−40..85; RGB −20..85), JST BM04B-SRSS-TB USB and SM03B-SURS-TF camera plugs (−25..85, S, JST catalogue), X5R capacitors (no zone rule under D69; V4 logs the hottest) |
| 90 °C | Hirose U.FL |
| ≥ 105 °C | X6S capacitors in every ESC quarter and at the PA (Murata GRM033C81E104KE14D, GRM033C81A105ME05D, GRM188C80J226ME15D, GRM155C80J106ME11D; −55..105 °C, V/S maker data via distributors; D52 BR-18 moves every 100 nF to the X6S GRM033C81E104KE14D and BR-20 retires GRM155C81A225KE11D); X7R 10 nF GRM033R71A103KA01D (BR-19, −55..125); TPS2116 and TPS22810 (TA −40..105, V); EFM8BB51 I grade, TPS61022 and the LDOs (TJ 125); SN74LVC1G3157, TLV7031, INA186 (125); FETs, BC857BM (S), diodes (150); resistors, NTC, ferrite (125-155) |

The TOGNJING 12 MHz crystal of the house FC sheet is rated −20..70 °C (V,
LCSC C37635340) and is replaced (§4.5). The BR-01 fallback parts (ESP32-D0WD-V3,
GD25Q32EEIGR, 40 MHz crystal) are withdrawn (D55 / D61) and no longer rated here.

### 4.1 Input and protection

| Option considered | Verdict |
|---|---|
| Reverse-polarity FET | **No.** The BT2.0 key protects the plug, not the user-fitted pigtail joint. A pigtail soldered reversed forward-biases the unidirectional SMF5.0A and the 12 N/P body-diode pairs (GND → N body diode → phase → P body diode → +BATT), which clamp +BATT at about −1 to −1.4 V while they short the battery at tens of amps (I): the TVS, FETs or traces fail and the board is lost. An ideal-diode P-FET (1-2 mΩ, 3x3) costs about 12 mm² and 0.4-0.6 W at 20 A. Rev1 keeps user fit (Matrix-style pads) and states the risk: + and − silk at the pads and a polarity photo in the README. Factory fitting on NextPCB's THT line is priced as a P7 option |
| TVS at the pads | **Yes, for the FET drain-source ratings only.** Event: battery unplugged (or pigtail torn in a crash) while the props spin; Bluejay damping returns rotor energy (up to about 0.3 J per motor at 40,000 rpm, I; up to about 1.2 J for four) into a bus that then holds only the MLCCs. The SMF5.0A (VBR 6.40-7.07 V, VC 9.2 V at 21.7 A, 200 W 10/1000 µs, V) absorbs about 0.29 J per rated pulse (I), so it covers one motor's worth, not four; the rest goes into winding and body-diode losses (I). V3b measures TVS current, duration and clamp energy; the fallback is the 400 W Littelfuse SMAJ5.0A (SMA, S; +7 mm² bottom). The fitted AGM210MAP stage (D56; V, DS VER2.73 Table 1: VDS 20 / −20 V, VGS ±12 V, EAS 36 / 49 mJ for N / P) stays in rating at the 9.2 V clamp: 9.2 V plus 2-4 V of switching overshoot is ≤ 13.2 V against 20 V, and the gates, driven at VDD = bus, see ≤ 9.2 V against ±12 V. It does not protect the parts rated below the clamp (POWER sheet D1 note): EFM8 VDD (5.5 V abs max), SE5004L VCC3 (6 V), TPS61022 (7 V; its pass-through carries a surge onto `+5V_BST`), the TPS2116 (6 V abs max) and the LP5912s (7 V) behind it, and the 6.3 V MLCCs. TI fallback stage only (D12 pair, if the AGM210MAP is replaced): the clamp would not keep the 12 V CSD13202Q2 in rating (9.2 V plus overshoot can pass 12 V; EAS 20 mJ, V SLPS313A, far below a 0.3 J event) and a 9.2 V bus exceeds its ±8 V gates. A clamp per EFM8 is not possible in this topology (VDD must follow the P sources). Accepted as Matrix parity (same topology); risk in §15.4, surge measured in V3b |
| Bulk at the pads | 2x 22 µF 0603 16 V (X5R, at the battery pads outside the ESC quarters). Board total about 55-80 µF effective at 4.35 V (table below), which shares the PWM ripple with the 30-60 mΩ battery path (03 §11). **Hot plug** (I): the MLCC-only bus against the pack and pigtail (50-80 nH, 25-35 mΩ) has ζ about 0.4-0.5, so plugging a fresh 4.35 V pack overshoots 15-25 % to 5.0-5.4 V at the EFM8 VDD (abs max 5.5 V) and the 6.3 V MLCCs, and above the TPS61022's 4.8 V VIN limit for a start-up with its output pre-biased below 0.7 V (SLVSDX7D §6.3 recommended operating conditions; 5.5 V otherwise, 7 V abs max), which is exactly hot plug (EN = VIN, +5V_BST starts from 0 V); the TVS (VBR ≥ 6.4 V) does not act. V3c tests it; the damping fallback is a polymer or tantalum bulk with ESR near the bus impedance √(L/C) ≈ 30 mΩ (about 100 µF 6.3 V, +6-10 mm² bottom) at the pads |

Effective capacitance (I: typical DC-bias behaviour including −20 % tolerance;
replaced by the Murata/Samsung simulator curves in P3):

| Part | Use | At | Effective each |
|---|---|---|---|
| CL10A226MO7JZNC 22 µF 16 V 0603 X5R | pad bulk x2 | 4.35 V | about 9-13 µF |
| GRM188C80J226ME15D 22 µF 6.3 V 0603 X6S | boost Cin x1 (the 22 µF ESC cell bulk of D52 became three 10 µF 0402 per ESC, D77) | 4.35 V | about 7-10 µF |
| GRM188C80J226ME15D | boost Cout x4 (D15) | 5.15 V | about 5-7 µF (20-28 µF for four) |
| GRM155C80J106ME11D 10 µF 6.3 V 0402 X6S | ESC hot-loop caps x12 (D77: one per AGM210MAP, pin 3 to pin 1 at the lead side; the phase-B one per ESC is also the EFM8 VDD bulk within 4 mm of VDD pin 4); the ESC3-only C30 is deleted | 4.35-5.25 V | about 2.6-2.8 µF at 4.2 V (Murata curve: 3.5 µF at 3.3 V, 2.0 µF at 5 V; EFM8 datasheet asks 1 µF) |
| GRM033C81A105ME05D 1 µF 10 V 0201 X6S | round-2 EFM8 VDD part, now fallback | 4.35 V | about 0.4-0.6 µF |

D52 BR-05 deletes the 2.2 µF EFM8 VDD caps of ESC1, ESC2 and ESC4 (their 22 µF
local bulk moves next to VDD pin 4, the 100 nF stays at the pin): the bus loses
3.0-4.2 µF effective, BR-20 gives back about 1.5-2 µF at C30 (I). V3c (hot plug)
checks it; PE-8 (pad bulk → GRM188C80J226ME15D) waits for V3c, because with
BR-05 its inferred hot-plug peak reaches 5.58-5.64 V against the EFM8's 5.5 V
(BOM-REDUCTION §5.2, §6 item 11). D77 (P4 critique) then replaced each ESC's
22 µF 0603 by three 10 µF 0402, one at each AGM210MAP's lead side (3x 2.6-2.8 µF
= 7.8-8.4 µF against 7-10 µF effective: bus capacitance about equal, V3c unchanged),
and deleted C30.

Bus ripple, caps-only upper bound ΔV = I·D(1−D)/(f·C): one ESC at 12 A and D 0.5
gives 0.4-0.6 V p-p at 96 kHz (the D12 start build, §4.4) and 0.8-1.25 V at
48 kHz on 50-80 µF; the battery path in parallel roughly halves it. The ripple is
common to the P-FET source and gate because each EFM8 sits on its own cluster's
+BATT (§4.4); it sets the EFM8 VDD peak and logic-high margin (§4.4, PINMAP F4)
and matters for the PA supply (§4.8, V5b).

| Function | Primary | Fallback |
|---|---|---|
| TVS | Littelfuse **SMF5.0A**, SOD-123FL, C151296, 33,500 (V) | Littelfuse SMAJ5.0A, SMA, 400 W (S), if V3b exceeds the SMF5.0A curve |
| Pad bulk | Samsung **CL10A226MO7JZNC** 22 µF 16 V 0603, C2762594, 457,735 [PU] | Murata GRM188R61C226ME15 (S) |
| Shunt | Stackpole **HCS1206FTL500**, 0.5 mΩ 2 W 1206, C346511, 1,717 | Yezhan ASR-S-3-0.2F 0.2 mΩ 2512, C695806, 1,020 [PU] (larger land, scale 200) |
| Current amp | TI **INA186A3IDCKR**, SC-70-6, gain 100, C2058245, 5,715 [PU] | TI INA186A3 DSBGA (YFD) (S, −4.8 mm²) |
| VBAT divider | 2x 10 kΩ 0201 (Yageo RC0201FR-0710KL, C106225 [PU]) + 100 nF | Uni-Royal 0201WMF1002TEE (S) |

Nets: the battery pads, TVS and pad bulk sit on **`+BATT_IN`** (net class VBAT,
`PWR_FLAG`); after the shunt the rail is **`+BATT`**. The Kelvin taps are their
own nets **`SHUNT_SENSE_P` / `SHUNT_SENSE_N`** (class Analog), separated from
`+BATT_IN` / `+BATT` by a net-tie in the four-pad shunt footprint, routed as a
pair on L1 or L6 away from the power current and never on In2/In3. Everything that draws
current, including the boost VIN and the PA VCC, taps `+BATT` after the shunt,
so the INA186 sees it. Numbers: 0.5 mΩ x 100 V/V = 50 mV/A, full scale 66 A at
3.3 V, Betaflight `ibata_scale` 500 (0.1 mV/A units). Shunt loss 0.2 W at 20 A,
0.31 W at 25 A. VBAT 10k/10k puts 4.35 V at 2.18 V on the ADC. Current sense is
high side with Kelvin taps and the matched input RC network of the OpenESC
Rev3.2 / OpenAIO root sheet (values moved to 0201), less its two common-mode
capacitors (D52 BR-07): 1 kΩ + 1 kΩ series and 1 µF differential (80 Hz), plus
the output RC to the ADC; any offset shows in the `ibata_scale` check. The land is a four-pad
Kelvin pattern per the Stackpole HCS application note with the sense taps at the
inner pad edges (net-tie footprint); the scale is checked on every prototype and on a sample of each
production lot (±10-20 % unit to unit otherwise, I).

### 4.2 Power tree

```
BT2.0 -> +BATT_IN pads -- SMF5.0A, 2x22u -- shunt (Kelvin SHUNT_SENSE_P/N -> INA186) -- +BATT
  +BATT -> 4x ESC power stages; 4x EFM8 VDD on their own cluster's +BATT (100n X6S at the pin, no series R;
             one 10u X6S 0402 hot-loop cap per AGM210MAP (pin 3 S2 to pin 1 S1), the phase-B one within 4 mm of VDD; D77)
  +BATT -> SE5004L PA VCC (10u X6S + per-pin 1n/100p)   [3-pad 0 ohm selector: +BATT (default) or +5V]
  +BATT -> TPS61022 boost, 1 MHz, 0.68 uH -> +5V_BST (5.15 V: FB 47k/6.2k, 4x 22u X6S 0603)
             EN tied to VIN (enabled whenever the cell is above UVLO; BR-11).  MODE = VOUT: forced PWM
  VBUS (J31 JST SH pin 4, D57) -> SGM40661 OVP (U24, 100n at IN; trips 5.75-6.12 V) -> +5V_USB
  USB D+/D- -> TPD2EUSB30 (D7, at J31) -> 27R -> RP2354A
  +5V_USB -> TPS2116 VIN1 = MODE (10u X6S at VIN1, BR-20; priority while VBUS > 3.44-4.04 V; PR1 = 27.4k/10k from VIN1)
  +5V_BST             -> TPS2116 VIN2      -> +5V (10u X6S 0402)
  +5V_BST             -> TPS22810 load switch (CIN = boost Cout C8-C11, U5 VIN within 3 mm; C17 deleted), CT 10n -> +5V_HD -> pad VHD (O4 Lite)   [D53 BR-10: ahead of the mux]
                      EN/UVLO = +BATT divider 33k/18k + 510k from +5V_HD (hysteresis) + 100n to GND (filter; BR-22):
                                on at 3.23-3.82 V rising, shed at 2.74-3.14 V falling (1 % R, POWER P4-1)
                                AND PINIO1 (GPIO27 through a BAS16LD PN diode, pull-down only; 2.4k on GPIO27, BR-24)
                      (no USB term: the mux never back-feeds +5V_BST from USB, so USB cannot reach the O4)
             +5V -> ferrite 0201 + 10u -> CAM 5V pad
             +5V -> buzzer +, user 5V pad (also the LED-strip 5V; strip data driven direct from GPIO8, BR-04)
             +5V -> LP5912-3.3 (EN = +5V) -> +3V3 (RP2354A, NOR, OSD front end, INA186, LEDs, ESP32-PICO-V3, SX1281, RGB LED)
                      +3V3 -> TPS7A2018 (EN = +3V3) -> +1V8 (gyro)
             +5V -> LP5912-3.3 (EN: 100k to +3V3, ESP32 GPIO21 via 1k; HD gate AP1606 pulls it low) -> +3V3_VTX
                      +3V3_VTX -> RTC6705, PNP PA drive stage (BR-02)
                      +3V3_VTX -> LP5907-2.85 (EN = ESP32 GPIO2 direct, internal 1M pull-down; BR-03, BR-12) -> PA VREF
             (both LP5912 inputs share one 10u X6S 0402 between their IN pins, BR-14)
  RP2354A internal core SMPS -> +1V1 (3.3 uH 2016, per RPi guide)
```

Enables: no EN floats and no EN net is shared between rails (commons
checklist). TPS61022 MODE goes to VOUT, so forced PWM holds over the whole sag
range (VMODE_H 1.2 V valid with VOUT > 2.2 V, V). The TPS61022 passes VIN to
VOUT when VIN > VOUT (V): a bus surge reaches +5V_BST and, through the mux, +5V
(§4.1).

**USB, battery or both: a power mux, not a diode.** +5V comes from a TI
**TPS2116** 2:1 power mux in priority mode (V, SLVSFG1A §7.3.1, §7.6.1.1):
MODE is tied to VIN1 = `+5V_USB`, which is selected while VBUS is above
3.44-4.04 V (PR1 divider 27.4 kΩ / 10 kΩ against VREF 0.92-1.08 V); VIN2 = the
boost output `+5V_BST` otherwise. With no USB, MODE = VIN1 ≈ 0 V puts the part
in its "MODE ≤ 0.35 V, PR1 low" row, which passes the higher input, i.e. VIN2.
The mux blocks reverse current on both channels (RCB: an input is never back-fed
from VOUT; the unselected input stays off even when it is the higher one, the
priority row "VIN2 = X"), so USB and the boost output never meet, and the boost
stays enabled in every case:

- **Cell and USB:** +5V runs from USB; the boost idles on its own output. It
  cannot charge the cell from USB, because the forced-PWM reverse flow of
  §7.4.1 needs its output driven above the setpoint, which the mux prevents.
- **Plugging USB in with a cell fitted:** PR1 crosses VREF at VBUS 3.44-4.04 V;
  the break-before-make switchover (8 µs at 5 V, V) then waits until VBUS is
  within 42 mV of +5V before the USB channel closes (RCB, V §7.6.1), so +5V
  sags from 5.15 V until it meets the rising VBUS: a few tenths of a volt on a
  fast plug-in, down to about 3.5 V if VBUS takes 1 ms to rise (I). The O4 sits
  on `+5V_BST` ahead of the mux (D53 BR-10), so its current never crosses the
  mux and the load seen here is the analog 0.42-0.70 A.
- **Unplugging USB with a cell fitted:** +5V follows the collapsing VBUS through
  the closed USB channel until PR1 falls below VREF (VBUS 3.44-4.04 V), then
  the 8 µs gap adds I·t/C = 0.7 A x 8 µs / 20 µF ≈ 0.3 V: **+5V minimum about
  3.1-3.7 V for tens of µs** before the running boost takes over (I). The
  LP5912-3.3 drops at most 180 mV at 500 mA (V), so +3V3 stays ≥ about 3.0 V.
  Round 3's 232 kΩ / 100 kΩ divider switched at 3.05-3.58 V and let +5V fall to
  about 2.75 V. V1 case (b) scopes +5V and +3V3 on 20 unplugs: no FC or RX
  reset.
- **USB only:** DShot idle-high back-feeds +BATT to about 2.5-2.8 V (PINMAP
  F16). The boost may start and hiccup on that weak source, but its output is
  not selected while USB is present, so +5V is unaffected; the EFM8 brown-out
  cycling stays a V9 item.
- **Battery only:** VIN1 floats except for the mux's reverse leakage out of an
  unselected input (0.001 / 0.05 / 0.15 µA at 25 / 85 / 105 °C, **typical
  values; the datasheet gives no maximum**) and the MODE and PR1 pin leakage
  (≤ 0.1 µA each, V), all into the 37.4 kΩ PR1 divider: about 10 mV typical, and
  0.3 V even at 50 times the typical IREV (I). Nothing senses that node any
  more (the round-4 AP1606 USB term is gone, BR-10), so it only has to stay
  below the mux's own thresholds.

**O4 supply ahead of the mux (D53 BR-10).** The TPS22810 takes its VIN from
`+5V_BST`, the boost output at TPS2116 VIN2, not from `+5V`. The mux blocks
reverse current on both channels (above), so USB never reaches `+5V_BST` and
the O4 cannot load a PC port, by topology: on USB only `+5V_BST` carries at
most the hiccuping, back-fed boost (§4.2 USB only), and the cell threshold
below keeps the switch off at the back-fed 2.5-2.8 V. This
replaces round 4's USB term (an AP1606 on the EN, gate on `+5V_USB`), which is
deleted. With a cell and USB both present the O4 runs from the boost, as in
battery-only operation, and its 1.0-1.2 A no longer crosses the mux (about
0.05-0.07 W saved); V1 checks USB + cell + HD mode. The switch's own CIN
(C17) is deleted (D79): the boost output caps C8-C11 are its input capacitor under the P5
condition 'U5 VIN within 3 mm of C8-C11 or U3 VIN2' (TPS22810 DS 10.3: CIN optional, 1 µF usually
sufficient), checked by `hardware/tools/check_p5_conditions.py`; floorplan v3 misses it (6.1 mm), so P5
moves U5 or puts back a 1 µF 0201 (GRM033R61A105ME44D, existing line). The O4 switch's two EN terms (D15):

- **Cell threshold:** a +BATT divider on the TPS22810's own EN/UVLO comparator
  (VENF 1.08-1.18 V, VENR 1.13-1.30 V, EN leakage ≤ 0.1 µA, V SLVSDH0C). The
  comparator alone is not enough on this bus (round 4): its falling-edge
  deglitch is only 2.5 µs typical and TI asks for an EN-to-GND capacitor "when the
  supply is particularly noisy" (V, §9.3.3); +BATT carries the ESC ripple
  (0.4-0.6 V p-p for one ESC at 12 A, roughly halved by the battery path, §4.1),
  which the divider puts at EN as 0.08-0.23 V p-p against a typical comparator
  hysteresis of 0.10 V; the VENF and VENR ranges overlap, so no minimum
  hysteresis is guaranteed; and shedding the O4 removes about 2.3 A of cell
  current, so the cell rebounds by 0.17-0.31 V across the pack and pigtail
  resistance (I), as much as or more than the comparator's own hysteresis at
  the cell (about 0.13-0.31 V): without help the switch trips on ripple troughs 0.1-0.3 V
  early and cycles on and off at the threshold, each restart a new inrush. The
  network is therefore (values from D53 BR-22; round 4 had 90.9k / 49.9k / 1.5M
  for the same thresholds):
  - divider **33 kΩ / 18 kΩ** (Yageo RC0201FR-0733KL / RC0201FR-0718KL);
  - **510 kΩ** from `+5V_HD` to EN (Yageo RC0201FR-07510KL): with the switch on
    it adds 0.115 V at EN, about **0.333 V at the cell**, and with the switch off
    (+5V_HD discharged by QOD) it pulls the other way, so the hysteresis is at
    least the resistor's 0.333 V even for a part with no comparator hysteresis,
    which covers the 0.17-0.31 V rebound;
  - **100 nF** EN to GND (Murata GRM033C81E104KE14D, the leg-cap part): with the
    11.4 kΩ Thevenin source τ ≈ 1.1 ms (corner about 140 Hz), about 57 dB at
    96 kHz, so the ripple at EN falls below 0.4 mV; τ also sets how long a short
    punch sag rides through before the shed, a trade inside D15 that V1 confirms
    (1-10 ms).
  The divider draws 82 µA from a 4.2 V cell (round 4: 30 µA), negligible against
  a live board. The O4 is switched on at **3.23-3.82 V rising** and shed at **2.74-3.14 V
  falling** (V: TPS22810 VENR 1.13-1.30 V / VENF 1.08-1.18 V with R9 33k, R10 18k, R87 510k at 1 % and
  +5V_HD 4.93-5.37 V, POWER sheet P4-1; nominal resistors give 3.27-3.77 / 2.78-3.10 V; V1 sets the exact point):
  a shed stays latched until the resting cell has recovered (landing or low
  throttle), which the README states, and a fresh or storage-charged pack
  (≥ 3.8 V) always starts the O4. On USB only the back-fed 2.5-2.8 V puts EN at
  0.86-0.97 V, below VENR, as a second guard.
- **PINIO1 (GPIO27):** a Nexperia **BAS16LD** PN switching diode (anode on EN,
  cathode on GPIO27) can only pull EN down, and GPIO27 carries a **2.4 kΩ**
  pull-down (Ralec RTT012401FTH, the DShot line; D53 BR-24, was 4.7 kΩ).
  GPIO27 low or not yet driven (FC in reset, SD build, USB): EN ≤ VF (about
  0.6 V at the 80-90 µA the 11.4 kΩ divider source delivers; VF ≤ 715 mV at 1 mA, V)
  + about 0.2 V across the pull-down = **≤ 0.87 V against VENF ≥ 1.08 V** (the BOM
  study verified 0.81-0.87 V with a 3.3 kΩ pull-down; 2.4 kΩ only lowers it; P4
  recomputes it once, §15.5 P4-1). GPIO27 high:
  the diode is reverse-biased by ≥ 1.6 V and its leakage (≤ 30 nA at 25 V and
  25 °C, ≤ 30 µA at 150 °C, V Nexperia BAS16LD Table 7; about 1 µA or less at
  85-105 °C, I) moves EN by ≤ 0.012 V, the shed point by ≤ 0.04 V. The diode also
  discharges the 100 nF EN filter: GPIO27 driven low empties it in microseconds,
  the 2.4 kΩ pull-down (FC in reset) in about 0.3 ms; turning on from the clamped
  0.8-0.87 V takes about 1-3 ms (I). The round-3
  Schottky (SDM02U30LP3: IR ≤ 7 µA at 10 V and 25 °C, typical curve 10-100x
  higher at 85-125 °C, V Diodes Fig. 3) into a 61.8 kΩ source would have lifted
  EN by 0.6 V or more on a warm board, so the O4 would never have been shed: the
  same failure class as the round-2 USB OR diode. The RP2350's own reset
  pull-down (tens of kΩ) is not enough on its own: with the diode current it
  would let GPIO27 rise to about 0.7 V and EN to about 1.3 V, past VENF (the
  AP1606 HD gate of BR-03 has no base-emitter junction to clamp GPIO27); hence
  the 2.4 kΩ, which draws about 1.4 mA when GPIO27 drives high (the only
  high-state load: the AP1606 gate takes no current), inside the default 4 mA
  drive.

D14 also asked for a regulator power-good term; the TPS61022 has no PG pin, so
D15 replaces it with the PINIO instead of adding a supervisor IC: the FC drives
GPIO27 high only after it has booted on a good +5V, GPIO27 sits low through
reset, and the cell threshold sheds the O4 while the boost still has margin
(1.67 A at 2.8 V against the 1.43-1.48 A HD load).
Round 2's Schottky OR with an AP1606 on the boost EN is dropped: the Schottky's
reverse leakage (IR 15 µA typ / 50 µA max at 5 V and 25 °C, about 1 mA at
85 °C; V, Nexperia PMEG2010AEH Table 7 and Fig. 2) into the 100 kΩ gate
pull-down turned the sense FET on in battery-only operation and shut the boost
down whenever the board was warm. The TPS61022 EN is now tied straight to VIN
(`+BATT`; D52 BR-11 deletes round 4's 100 kΩ pull-up): EN and VIN share the
−0.3..7 V absolute maximum (VEN_H ≤ 1.2 V, VEN_L 0.35-0.45 V, V Table 6.5), and
nothing else touches it.

**Setpoint.** TPS61022 VFB is 585/600/615 mV in PWM (±2.5 %, V Table 6.5); with
1 % divider resistors a 5.00 V nominal can sit at 4.80 V, below the rank-1 gate.
The nominal is set to **5.15 V**: worst case 4.93-5.37 V at the boost (I).
Divider (D52 BR-23): **47 kΩ / 6.2 kΩ** (Yageo RC0201FR-0747KL /
RC0201FR-076K2L), 0.600 V x (1 + 47/6.2) = 5.148 V, the same window as round
4's 909k / 120k; TI asks for a bottom resistor below 300 kΩ, and the lower
impedance improves noise immunity at the FB pin. The
mux adds 37-60 mΩ (V): 0.04 V at the analog load, 0.06-0.10 V at the HD load, so
+5V stays ≥ 4.89 V (analog, the 4.85 V gate holds with the ripple trough) and
≥ 4.83 V (HD, gate 4.75 V); the maximum stays inside the LP5912 (6.5 V; the
TLV75533 fallback 5.5 V), TPS2116 (5.5 V operating), TPS22810 (18 V) and the
SE5004L on the +5V selector position (5.5 V).

**Inductor saturation and overload.** The TPS61022 limits the inductor
**valley** current (6.5 min / 8 typ / 10 max A, V Table 6.5), not its peak. Up
to the published loads the peak stays at or below 80 % of the 6.5 A Isat (5.2 A
worst case at 1.7 A from 2.8 V with −30 % inductance, I). In current limit the
peak is the valley limit plus the ripple, 9.5-13 A, which the
FTC252012SR68MBCA does not carry: as a metal-alloy molded part it saturates
softly (S), so its inductance falls, the ripple and the low-side FET current
grow, and only thermal shutdown (150 °C) ends it (I). TI's recommended
inductors are rated 11.5-28 A (V Table 8-2) and none comes near 2520. Hard
shorts are covered by the output short protection (current folds back below
VOUT 1.8 V to about 0.7 A at < 0.4 V, V §7.3.7). The exposure is an overload
between about 2 A and current limit with VOUT above 1.8 V, from a user-pad fault
or an O4 inrush; the TPS22810 slew (CT 10 nF: about 4.7 V/ms, V Eq. 3) keeps
the inrush to about C x 4.7 V/ms (0.2 A per 47 µF; the O4's input capacitance is
not published, V1). V1 adds an overload step to 2.5 A at 2.8 V for 10 s and a
short on the user 5V pad. Fallback if V1 fails: Coilcraft XGL4040-681 (0.68 µH,
Isat 8 A at 20 % drop, 4 x 4 x 4 mm, S; +10 mm² bottom).

Options weighed:

| Question | Options | Decision | Why (numbers) |
|---|---|---|---|
| 5 V converter | TPS61023 (SOT-563, 2.7 A valley, auto-PFM), TPS61022 (2x2, 6.5 A valley, forced-PWM pin), TPS63070 buck-boost, SY7088 (3 A peak) | **TPS61022RWUR + 0.68 µH 2520, 4 Cout (D15)** | Forced PWM keeps the 1 MHz ripple fixed and out of the PFM range that shows as video bars. Calculated per TI §8.2.2.2 (inductance −30 % = 0.48 µH, peak at 80 % of Isat 6.5 A, η 0.85 / 0.86 / 0.87 at 2.8 / 3.0 / 3.2 V, I from TI's curves at 1.5-2 A): **1.67 / 1.82 / 1.98 A**, against 0.70 A analog and 1.43-1.48 A HD (§5.1); ripple is 159 % of the inductor DC current at the analog load (TI asks ≤ 40 % at full load) and the −20 % tolerance part stays above TI's 0.33 µH floor. Above 1.5 A the datasheet needs ≥ 20 µF effective Cout: four X6S 0603 give about 20-28 µF at 5.15 V. Binding limit: TJ ≤ 125 °C (recommended operating, V §6.3), not the 150 °C shutdown: at the HD load from 3.0 V about 1.2-1.3 W of loss, 1.0-1.1 W in the IC, +37-40 K by ΨJB 36.7 K/W (V), so TJ 85-99 °C in HD hover (board 48-59 °C at h 80-55, `thermal_v3.py`) and 125 °C only on an 85-88 °C local board. The boost sits ≥ 2 mm from every FET group (rule H2, §10), so a loaded ESC quarter does not add to it. The TPS63070 (D14's alternative) gives 1.49-1.65 A at 2.8-3.0 V and is weaker at 1S (study, D15) |
| 3.3 V supply path | 5 V boost + LDOs (as drawn) vs a cell-fed 3.6 V buck-boost (TPS63802 class, S) with post-LDOs | **as drawn**; heat lever (b) in §5.4 | All 3.3 V loads through boost + LDO cost about 0.65 W of overhead for 0.96 W delivered. A 3.6 V buck-boost would save about 0.45 W for 15-20 mm² on the bottom, which the bottom does not have (§9) |
| PA supply | 5 V boost + load switch (track 06 R6) vs cell (track 04) | **Cell (+BATT)**, 3-pad 0 Ω selector to +5V (D54: kept until V5, fixed +BATT copper for production) | SE5004L is rated 3.0-5.5 V; takes 0.3-0.55 A off the boost; VREF low = 0.5 µA so no load switch; on USB only the PA has no supply. The selector is a 3-pad land with one 0402 0 Ω fitted between the centre and one side: a solder blob across a 3-pad solder jumper would short the boost output to the cell, a single 0402 cannot bridge both sides; the unfitted pad 3 carries no paste (a stencil deposit 0.40 mm from pad 2 could bridge +5V to PA_VCC in reflow; the 2-3 rework is hand-soldered). Below 3.0 V cell the PA is out of rating (V5 measures at 2.8 V). Bench test V5 decides (§14) |
| USB / boost source | Schottky OR + boost EN held off on USB (round 2); USB load switch with reverse-current blocking + boost held off on USB; 2:1 mux with the boost always on | **TPS2116 mux, boost always on** | the Schottky's reverse leakage defeats the USB sense in battery-only operation (above); a blocking switch with the boost held off drops +5V for the 0.7 ms soft start on every USB unplug; the mux switches in about 8 µs onto a running boost |
| 3.3 V rails | one LDO for all (about 0.29 A: 0.49 W, +82 K in X2SON) vs split | **FC and RX on one LP5912 (WSON-6), the RTC6705 on its own LP5912, + gyro LDO + PA reference** (D14 regulator consolidation; round 2 had a separate RX rail) | With no Wi-Fi radiator (§4.7) the RX rail peaks at 0.16 A; FC + RX is 0.20-0.25 A, 0.37-0.46 W in WSON-6 (RθJA 71.2 K/W on a JEDEC board, V: +26-33 K). The RTC6705 keeps its own rail for the VCO and for the D17 hold-off. Saves the TLV75533 and two caps (2.8 mm² bottom) |
| ESC MCU supply | VBAT direct vs 3.3/5 V rail | **VBAT direct**, each EFM8 on its own cluster's +BATT, 100 nF X6S at the pin; the 1 µF-class bulk is the slot-M hot-loop cap (one of three 10 µF X6S 0402 per ESC, D77) within 4 mm of VDD pin 4 through the +BATT plane (BR-05 as amended; C30 deleted, D77; P5 check `check_p5_conditions.py`), no series R | EFM8BB51 VDD 1.8-5.5 V (V); gate drive = cell voltage; motors survive a BEC fault. A series R (10 Ω x 1.1 µF) would leave most of the PWM ripple between P source and P gate; tied directly, VDD tracks the P sources (track 03 §8: at most 2.2-4.7 Ω). VDD peak and logic-high margin: §4.4 |
| USB ESD | 2-line ESD array at the connector vs none | **TI TPD2EUSB30 at J31 (D57)** | owner D57 puts D+/D− ESD on the board with the JST SH plug: 0.7 pF, IEC 61000-4-2 8 kV contact, VRWM 5.5 V and 6 V IO abs max, so a D+/D− short to VBUS survives; ahead of the 27 Ω series resistors. The round-4 'none' (house practice) is superseded |
| USB VBUS hot plug (round 4) | nothing on `+5V_USB` but the PR1 divider (round 3); VIN1 capacitor; board TVS; damping at the cable end | **SGM40661 OVP load switch on VBUS (D57: 28 V abs max at IN, trips at 5.75-6.12 V in 80 ns, 15 ms debounce, 2 ms soft turn-on; simulated cable ring ≤ 10.8 V at its IN, never at VIN1) + 10 µF X6S 0402 at VIN1** (the clip-on adapter of O3 is gone; text below is the round-4 analysis) | With the cell fitted the USB channel stays open until VBUS reaches +5V, so VIN1 is almost unloaded, and a cable's 0.5-1 µH can ring it toward twice VBUS on plug-in or pogo bounce, past the 6 V absolute maximum of VIN1, MODE and PR1 (V, SLVSFG1A §6.1); a failed mux takes +5V, the FC, RX and VTX down. The house OpenFC-Lite-Mini feeds VBUS into a 40 V DSK24 Schottky with 22 µF behind it (V, netlist); here a 6 V CMOS mux sits on the pad, so the house "no array" argument does not carry over. A board TVS would not protect it: 5 V parts break down at 6.4-7.5 V (SMF5.0A 6.40 V, TI TVS0500 7.5 V minimum; V), above 6 V. The VIN1 ceramic meets TI's "CIN of 1 µF is sufficient" (§9) and the layout rule (§10), but it also forms the LC with the cable, so the damping goes at the cable end: the adapter carries a 5 V VBUS TVS and a damped bulk (10 µF ceramic in series with about 1 Ω, or a polymer part with ESR near √(L/C)), sized with the board's VIN1 part (10 µF nominal, about 2.5-3.5 µF effective at 5 V, I) inside USB's 10 µF attach limit (O3, P4-3). Behind the adapter, the pogo contacts (a few nH, 30-100 mΩ each) leave ζ about 0.4-1.5 at VIN1 (I). V1 scopes VIN1 through the adapter, pass ≤ 6.0 V; board fallback: an RC snubber (1 Ω 0201 + 4.7 µF 0402) at the pogo +5V pad, +2.3 mm² bottom |

On USB only: the bench loads are FC 0.09 A, RX 0.10 A, RTC6705 0.10 A and the
camera 0.12 A at 5 V: 0.42 A. The mux drops 0.02 V there (V), so +5V is VBUS
less the adapter and cable drop, about 4.6-5.2 V (I), with ample LDO headroom;
below VBUS 3.05-3.58 V the mux stops selecting USB. With the battery fitted as
well, +5V still runs from USB and the boost idles; the PA and the motors run
from the cell, and so does the O4 when the HD line is on (its switch sits on
`+5V_BST`, BR-10). The OSD needs a camera on the bench (§4.5).
Bidirectional DShot idles high on USB and back-feeds the unpowered EFM8s and
+BATT through the 2.4 kΩ resistors; PINMAP §4.5 documents that case and V9
tests it.

Parts:

| Function | Primary (MPN, maker, package, stock) | Fallback | Reuse |
|---|---|---|---|
| Boost | TI **TPS61022RWUR**, VQFN-HR-7 2x2, C915088, 857 | TI TPS61023DRLR, SOT-563, C919459, 53,320 (new land, 1.6 A at 2.8 V) | new |
| Boost inductor | cjiang **FTC252012SR68MBCA**, 0.68 µH, 2.5x2.0x1.2, Isat 6.5 A, 17 mΩ, C5832369, 6,040 (V, LCSC parameters) | Coilcraft XGL4040-681, Isat 8 A at 20 % drop, 4x4x4 (S), if the V1 overload step fails; cjiang FTC252012S1R0MBCA (1.0 µH, Isat 5.6 A, C5832370) is not a fallback any more (1.71 A at 3.0 V) | new |
| Boost caps | Cin 1x, Cout 4x (D15) Murata **GRM188C80J226ME15D** 22 µF 6.3 V X6S 0603, C393031, 104,510 | a 10 V X6S/X7R 22 µF 0603 found in P3 (better DC bias) | new |
| USB / boost mux | TI **TPS2116DRLR**, SOT-583 (DRL) 2.1x1.6, 1.6-5.5 V (6 V abs max on VIN1, MODE, PR1), 2.5 A, 40 mΩ typ (≤ 60 mΩ), reverse-current blocking, TA −40..105 °C, C3235557, 77,966 (V) + PR1 divider 27.4k/10k Yageo RC0201FR-07 (threshold 3.44-4.04 V) + VIN1 input capacitor 10 µF 6.3 V X6S 0402 (Murata GRM155C80J106ME11D, D52 BR-20: about 2.5-3.5 µF effective at 5 V against TI's CIN 1 µF, SLVSFG1A §9, I; X6S because U3 sits 1.62 mm from a FET; if the critique keeps C30 at 2.2 µF, VIN1 may stay on the 2.2 µF GRM155C81A225KE11D, 1.0-1.4 µF effective) | TI TPS2121RUXR, VQFN-HR 2x2.5, 2.8-22 V, C485916 (S; new land) | new |
| O4 load switch (D15) | TI **TPS22810DBVR**, SOT-23-6, 2.7-18 V, 79 mΩ typ (≤ 115 mΩ), 2 A at TA 65 °C, EN/UVLO VENR 1.13-1.30 / VENF 1.08-1.18 V, CT slew, QOD, TA −40..105 °C, C205990, 14,998 (V); loss 0.11-0.17 W at 1.2 A | TI TPS22810DRVR (WSON-6 2x2, 3 A, −2.9 mm²): preferred by the smallest-package rule once a NextPCB channel shows stock (no LCSC listing on 2026-10-07; O17) | study |
| O4 EN parts | +BATT divider 33k/18k + 510 kΩ hysteresis from +5V_HD (Yageo RC0201FR-0733KL / -0718KL / -07510KL, D53 BR-22; on at 3.23-3.82 V rising, shed at 2.74-3.14 V falling with 1 % resistors, set at V1) + 100 nF EN filter (GRM033C81E104KE14D, τ 1.1 ms); Nexperia **BAS16LD,315** PN switching diode, SOD882D 1.0 x 0.6 (PINIO1, pull-down only; IR ≤ 30 nA at 25 V / 25 °C; V datasheet Rev. 1; LCSC C841775, about 900, and Farnell / RS listings, S: O17 confirms) + 2.4 kΩ 0201 pull-down on GPIO27 (Ralec RTT012401FTH, BR-24); CT 10 nF 0201 X7R (GRM033R71A103KA01D, BR-19); CIN 1 µF 0201 on `+5V_BST`; no USB term (the round-4 AP1606 is deleted, BR-10) | Nexperia BAS116 class low-leakage diode (S, larger package); not a Schottky (§4.2) | study; diode changed in consolidation; filter and hysteresis added in round 4 (TI SLVSDH0C §9.3.3); values and supply node D53 |
| +3V3 LDO (FC + RX, D14) | TI **LP5912-3.3DRVR**, WSON-6 2x2, C524780, 23,490 [PU]; CIN shared with the +3V3_VTX LDO: one Murata GRM155C80J106ME11D 10 µF X6S 0402 between the two IN pins, 2.4 mm apart (D52 BR-14, replaces 2x 1 µF 0201 that sat below the > 0.5 µF effective minimum and in an X5R H1 breach). COUT: the +3V3 sum falls from about 31 to about 19 µF nominal (9-10 µF effective, I) after D52, still at the LP5912 10 µF maximum: P4 sums it with maker curves (§15.5 P4-12) | TI TLV75533PDQNR (X2SON-4 1x1, C2861882, 2,025 [PU]) as a separate FC rail (round-2 split, +2.8 mm²) | OpenFC `power` back end |
| +3V3_VTX LDO | TI **LP5912-3.3DRVR** (D12: the part already on the BOM); also feeds the PA reference and the PNP drive stage after D52 (BR-02, BR-03): COUT about 12.3 µF nominal, 5-6 µF effective (I), P4 checks it against 10 µF | TI TPS7A2033PDQNR, X2SON-4 1x1 (commons-verified; LCSC 0 on 2026-10-07), −3.8 mm² once a NextPCB channel shows stock | BOM reuse |
| PA VREF reference | TI **LP5907SNX-2.85/NOPB**, X2SON-4 1x1, 2.85 V ±2 % (2.79-2.91 V, just outside the SE5004L's 2.80-2.90 V at both corners; S, maker listing via Arrow): V5 qualifies Icq and gain at 2.79 and 2.91 V (§4.8). VIN on `+3V3_VTX` (D53 BR-03); COUT Samsung **CL05A475MP5NRNC** 4.7 µF 0402 (BR-26: the 0201 1 µF was below the > 0.7 µF effective minimum; X5R allowed, 3.1 mm from a FET and 16 mm from the PA); CIN Samsung CL05A475MP5NRNC 4.7 µF 0402 (about 2.6 µF at 3.3 V; LP5907 DS 5.6 / 7.2.2.4: > 0.7 µF effective over all conditions within 1 cm; the 1 µF 0201 at about 0.45 µF missed it and C108 serves the RTC6705, P4 critique r3) | a 2.8 V variant if V5 qualifies a lower VREF (lever (a), §5.4) | new |
| +1V8 gyro LDO | TI **TPS7A2018PDQNRM3**, X2SON-4 1x1, C36996449, 8,090 | TI LP5912-1.8DRVR, WSON-6 2x2, C2876234, 728 [PU] | OpenFC `imu` rule |
| HD gate (D17) | ALLPOWER **AP1606**, DFN-3L 1.0x0.6 (D53 BR-03: drain on the +3V3_VTX LDO EN, gate on HD_EN, source GND; no resistors) [PU] | - | BOM reuse (beeper FET line) |
| RP2354A core inductor | Abracon **AOTA-B201610S3R3-101-T**, 3.3 µH 2016, C42411119, 625 [PU] | external 1.1 V LDO with the SMPS bypassed (RPi guide option) | OpenFC `rp2350a` |
| Camera ferrite | Murata **BLM03PX121SN1D**, 0201, 0.9 A, 160 mΩ, −55..125 °C (S: Digi-Key/Element14 listings; TME 5,024 on 2026-10-07) | Murata BLM03PX220SN1D, 0201, 1.45 A (S) | commons |

### 4.3 ESC power stage

**Current stage (D56, D77; the D12 text and tables below stay as the documented
TI fallback).** Per phase one AGMSEMI **AGM210MAP** (PDFN 3.3x3.3, DS VER2.73 p1
top view): 1 S1 N source = GND, 2 G1 N gate = x_PWM, 3 S2 P source = +BATT, 4 G2
P gate = x_COM, 5/6 + EP D2 and 7/8 + EP D1 = PHASE_x (the two drain pads joined
only by the phase island). Gates straight from the EFM8 (no gate resistors).
**Hot loop:** one 10 µF X6S 0402 (GRM155C80J106ME11D) per AGM210MAP from pin 3
to pin 1 at the cell's lead side with filled via-in-pad on both pads, so the
commutation loop (S2, P die, phase, N die, S1) closes at the pins and the edge
current stays out of the In3 / L4 planes near the gyro and VTX (D33; Matrix II:
one cap per FET, D73 / D76). The phase-B cap is also the EFM8 VDD bulk (BR-05
amended: within 4 mm of VDD pin 4 through the +BATT plane, 100 nF at the pin).
The 100 nF "leg cap" at the N source below belongs to the TI fallback.
**Switching** (AGM210MAP DS VER2.73, V): N td(off) 32 + tf 26 = 58 ns at VGS 4.5 V,
RGEN 3.3 Ω; P td(off) 74 + tf 10 = 84 ns at RGEN 1 Ω; Qg 23 / 33 nC, Qgd 4.2 /
11 nC (the Qg disagrees 3-5x with Ciss 950 pF, so V2 measures the gate edges). On
EFM8 port drive the edges are slower than at RGEN 1-3.3 Ω, so first power-up runs
**`A_X_10_96`** (about 204 ns) and V2 releases **`A_X_5_96`** (about 102 ns, the
Matrix II build) after the shoot-through check. **Ratings** stay measured only
(V4); the D56 model gives 34.1 mΩ typ hot path and 12 A bursts of 5.5-7.3 s at
h 80 (TI stage 1.3-4.2 s); the "−0.8 to −1.0 A against the Matrix stage" of the
D12 text does not apply to this stage.

| Topology | Area (budget v3, 12 phases, both sides incl. cell vias) | Hot path at Vgs 3.6 V, typ (max) | Verdict |
|---|---|---|---|
| **Discrete P 2x2 + N 2x2 (CSD25310Q2 + CSD13202Q2), direct GPIO** | 12 + 12 SON 2x2 + 13 / 6 via sites per phase (top / bottom, budget v6; round 3: 7 / 15 on the reversed P pinout) | **40.2 (48.8) mΩ** | **chosen (D12)** |
| P+N dual per phase, direct GPIO (Matrix: AGM210MAP) | 12 PDFN 3.3x3.3 + 7 source vias per phase both sides; board total within 1 % of D12 (`budget_v3.py` case b; the stage options are not re-run in v4) | 34.1 (50.0) mΩ | case (b), O5: Matrix-proven at `A_X_5_96`, longer bursts; LCSC-only (4,795), so a consigned line |
| Discrete P 3.3x3.3 + N 2x2 (CSD25402Q3A + CSD13202Q2) | +106 mm² top, −26 mm² bottom against D12 | 23.1 (27.9) mΩ | round-1 choice; fails the area by more (top 112 %) |
| N+N + gate driver | +4-15 mm²/channel + boost rail | 11 mΩ (needs EG2134, 0 stock) / 22-30 mΩ (DRV8328) | no: no stocked 1S driver gains anything, adds a rail whose failure drops all four motors (03 §5c) |
| Level-shifted P (2S style) | +46 mm² | worse, DT 0.6-1.4 µs | no: 1S only |

Decision (D12): per phase one TI **CSD25310Q2** P-FET on the top (high side,
gate straight from the EFM8 COM pin, active low) and one TI **CSD13202Q2** N-FET
on the bottom (low side, PWM pin, active high). Bluejay BB51 layout A, unchanged
upstream (§12). D12 took it over the AGM210MAP for sourcing (genuine TI parts,
TI store stock) and because the continuous rating is set mostly by non-ESC heat;
the model shows the cost is real: about −0.8 to −1.0 A continuous against the
Matrix stage at the same airflow and a quarter to a half of its 12 A burst time
(§1, table below).

**Cell from the real lands** (V, datasheet top views; round 4 corrected the P
pinout, which earlier revisions had reversed, D23). **CSD25310Q2 (SLPS459C page 1
Top View): SOURCE on the exposed pad (pad 8) and pins 1, 2, 5, 6; DRAIN on pin 4
and the strip pad 7; GATE pin 3**; the §4.2 thermal figure agrees (its 1 in²
copper is on the source). **CSD13202Q2 (SLPS313A page 1): DRAIN on pad 8 and pins
1, 2, 5, 6; SOURCE on pin 4 and the strip pad 7; GATE pin 3.** DQK land (both
parts, SLPS313A §7.1.1): pad 8 1.0 x 0.95 mm, strip pad 7 0.75 x 0.3 mm, pins
0.45 x 0.3 mm. The P's large pad is therefore +BATT, and its phase terminal is the
0.3 mm strip, which cannot hold a via field (a 0.35 mm via pad is wider than the
strip). Drawn the round-3 way, the P source would sit on the phase and its drain
on +BATT, and its body diode would conduct from +BATT to the phase whenever the N
pulls the phase low: shoot-through on every PWM cycle. Per phase:

- **P source = +BATT**: the merged land (pad 8 + pins 1/2/5/6) carries **4 +BATT
  vias in-pad** (0.35/0.20, Type VII, 2 x 2 at the 0.40 mm minimum pitch) into the
  L4 plane and the L1 +BATT cluster pour that joins the EFM8 VDD (§4.4);
- **P drain = phase**: pin 4 + pad 7 run into a **top phase pour** on the outward
  side (the drain row faces the motor pads), which carries the **8-via phase
  field outside the P land** (2 rows of 4 at 0.40 mm pitch, in a 0.2 + 0.95 mm
  strip outward of each P group, sketch v5) and continues to the motor pads;
- the N sits on the bottom **beside** the P, offset outward by about 2.2-2.4 mm
  centre to centre (the N row 0-0.2 mm beyond the P row in projection, sketch v5;
  no exposed pad over an exposed pad, §11), turned so that its merged drain land
  (pad 8 + pins 1/2/5/6, 2.4 x 0.95 mm) faces the P and lies under the phase field:
  the 8 phase vias land in-pad in it (Type VII; P3 draws the via positions and
  DRCs them) and join the bottom phase pour;
- **N source = GND**: pad 7 + pin 4 face outward and carry **3 GND vias in-pad**
  (drill inside the 0.3 mm pad, annulus under mask, as in 0201 pads, §8.3) into
  L5 and L2; if the EQ rejects vias in the strip, they move beside the land
  (+3 bottom sites per phase, +10 mm² bottom);
- the **leg cap** (100 nF X6S 0201) sits on the bottom at the N source end, its
  GND pad on the N source copper and its +BATT pad on its own Type VII via into
  L4;
- the **P gate** (pin 3, on the drain row) leaves through a Type VII via in pin 3,
  runs on L6 over L5 under the P land to the EFM8 side and comes up through one
  via to the COM pin (Gate class, never on In2/In3; PINMAP §7.1);
- via sites per phase (budget v6): **13 on the top** (8 phase vias, 3 GND and 1
  leg-cap landings, 1 gate via) and **6 on the bottom** (4 +BATT landings, the
  pin-3 landing, 1 gate via); round 3 counted 7 / 15 on the reversed pinout;
- the motor pad route leaves on L1 and L6, joined by the plated wire-anchor
  holes.

Commutation loop: P source pad (+BATT, L1) → P die → P drain strip → top phase
pour → phase vias → N drain land (L6) → N die → N source strip → leg cap → its
+BATT via → L4 plane → the P's in-pad +BATT vias → P source. About 3.5 mm along
the cell, with the return in the solid L4 plane 0.4-0.55 mm from the forward path
on L1 and L6: about 1.5-2 mm² (I), target ≤ 4 mm², drawn with dimensions at P2
(BUILD-PLAN P2 deliverable). P3 checks both symbol-to-footprint pin maps against
the datasheet top views (D23).

| Part | Primary | Fallback |
|---|---|---|
| P-FET | TI **CSD25310Q2**, −20 V / ±8 V, 19.9 / 27.0 mΩ typ (23.9 / 32.5 max) at 4.5 / 2.5 V, Qg 3.6 nC typ / 4.7 max, Vth −0.55 / −0.85 / −1.10 V, RθJC 4.5 K/W (V, SLPS459C), SON 2x2. Stock gate (3,000 for 50 boards x 12 x 5) not met at a NextPCB channel: LCSC C2871649 696; TI store 67,679 (track 03, 2026-10-06) is not a NextPCB channel, so it is a **consigned line now** (§15.3) | case (b) AGM210MAP dual (Matrix stage, different cell), O5 |
| N-FET | TI **CSD13202Q2**, 12 V / ±8 V, 7.5 / 9.1 mΩ typ (9.3 / 11.6 max) at 4.5 / 2.5 V, Qg 5.1 typ / 6.6 max nC, Vth 0.58 V min, RG 1.4 Ω max, EAS 20 mJ (V, SLPS313A), SON-6 2x2, RθJC 6.4 K/W; Digi-Key 8,235 (track 03, 2026-10-06: meets the 3,000 gate at a quote-engine channel; O17 confirms), LCSC C187839 2,605, TI store 294,349 | AOS AON2408, 20 V, DFN 2x2 (S, LCSC index 3,512); land check in P3; about +25 % N loss |
| Leg cap | Murata **GRM033C81E104KE14D** 100 nF 25 V X6S 0201 (V via Farnell/Arrow listings), one per half-bridge | Murata GRM033C71E104KE14 class X7S (P3) |
| Local bulk | Murata **GRM188C80J226ME15D** 22 µF 6.3 V X6S 0603, C393031, 104,510, one per ESC (replaces 2x 0402 X5R: same area, more effective capacitance, 105 °C); in ESC1/2/4 it sits ≤ 3 mm from EFM8 VDD pin 4 and replaces the 2.2 µF VDD cap (D52 BR-05; likely on the top, as the bottom under the EFM8s is taken); ESC3 keeps it away from the gyro (5 mm rule) and its EFM8 keeps its own 0402 (§4.4) | Samsung X6S 0603 equivalent (P3) |

**Loss math** (I, `calc/thermal_v3.py`; the per-motor figures equal v2's). Layout A conducts through **two FETs in
series** at every instant: the high-side P of the driven phase plus either the
PWM'd low-side N or, in the damped off-time, the damping P. Conduction is
I²·(d·(Rp + Rn) + (1 − d)·2Rp), evaluated at d 0.8. Rds values are typical, hot
(x1.35) at Vgs 3.6 V (Rp 29.5, Rn 10.7 mΩ for D12); the max column uses the
datasheet maxima. Dead time adds 2·DT·f·0.8 V·I through body diodes at DT 10 (the
target build `A_X_10_96`, 204 ns at 96 kHz; the first power-up build is DT 15,
below). Hard switching is on the N only. Phase
copper (motor pad route, about 1.5 mΩ per phase, two phases conducting) heats the
board, not the FETs. The per-FET split charges the dead time at d = 1, where no
complementary PWM runs: conservative.

| Phase current | Conduction | Dead time | N switching | FETs per motor | Phase copper | **Per motor on board** | Max-Rds case | Matrix AGM210MAP, same model (`A_X_5_96`) |
|---|---|---|---|---|---|---|---|---|
| 1 A (hover) | 0.04 W | 0.03 | 0.01 | 0.08 | 0.00 | **0.09 W** | 0.10 | 0.06 |
| 2 A | 0.18 | 0.06 | 0.02 | 0.26 | 0.01 | **0.27 W** | 0.30 | 0.20 |
| 4 A | 0.70 | 0.13 | 0.03 | 0.86 | 0.05 | **0.91 W** | 1.06 | 0.70 |
| 6 A | 1.58 | 0.19 | 0.05 | 1.82 | 0.11 | **1.93 W** | 2.26 | 1.51 |
| 12 A | 6.32 | 0.38 | 0.10 | 6.80 | 0.43 | **7.23 W** | 8.57 | 5.74 |
| 18 A (Vgs 3.0 V) | 15.54 | 0.56 | 0.15 | 16.26 | 0.97 | **17.23 W** | 20.55 | 13.78 |

Per FET at full duty (each conducts one third of the cycle; the P carries the
dead-time share): at 6 A, P 0.42 W and N 0.15 W; at 12 A, P 1.54 W and N 0.55 W;
at 18 A and Vgs 3.0 V, P 3.69 W and N 1.28 W. Junction above case (V, RθJC): P
4.5 K/W x 3.69 W = +17 K, N 6.4 K/W x 1.28 W = +8 K. The FET-local spreading rise
above the quarter is about 5-15 K/W for a 3.3 x 3.3 footprint (I, 06 §4.3 scaled
to the 1/0.5 oz stack) and scales with 1/√area, so 8-25 K/W for the SON 2x2:
junction to quarter 12.8-29.2 K/W for the CSD25310Q2, 8.5-18.5 K/W for the
AGM210MAP (RθJC 3.5 K/W, V). The P's heat enters the +BATT copper (TI's thermal
figure puts the 1 in² on the source): 4 in-pad vias into the solid L4 plane plus
the L1 cluster pour, about the vertical conductance of the round-3 8-via path
through the whole board (I) and a larger sheet than one phase pour, so the
footprint-scaled spreading term stays a conservative bound (`thermal_v3.py`
scales it by footprint only; its numbers do not change). V4's thermocouple on
the P case measures it.

**Dead time, worst case** (I, datasheet limits; `thermal_v3.py`). Same method
for both FETs: driver ≤ 60 Ω (EFM8 high-drive VOH ≥ VDD − 0.6 V / VOL at 10 mA),
τ = R·Qg/4.5 V, t = τ·ln(VDD/Vth).

- **P turn-off** (diode-commutated while motoring, an RC with no Miller
  plateau): CSD25310Q2, RG 3.8 Ω (2x typ, I), Qg 4.7 nC max, |Vth| 0.55 V min
  (about 0.39 V hot): **138 ns cold, 161 ns hot** at 4.35 V (typical 42 ns).
- **N turn-off**, the binding device (CSD13202Q2: Qg 6.6 nC max, RG 1.4 Ω max,
  Vth 0.58 V min, about 0.42 V hot, Crss 43-56 pF, V SLPS313A): with the phase
  current reversed (damped braking, the throttle-chop regen of §4.4) it is
  diode-commutated and needs **181 ns cold, 211 ns hot at 4.35 V and 227 ns at
  the 5.25 V regen peak**; motoring, it reaches the end of its Miller plateau
  after 179-219 ns.
- The P turns on about 9 ns after DT expires, so `A_X_10_96` (DT 204 ns) leaves
  about 213 ns: **zero or negative margin on the N side** at the datasheet
  corners. DT 10 covers the P side only.
- **Cdv/dt:** when the P turns on hard (regen, and a floating-to-COM
  commutation step) the off N gate, held by about 60 Ω, sees a kick of 0.24 V
  (Crss/Ciss divider) to 0.72 V (Qgd-based bound) against a hot Vth of 0.42 V:
  a partial turn-on is possible (I). The P gate sees 0.14-0.42 V against its hot
  |Vth| of 0.39 V when the N turns on.

The start build is therefore a **V2 outcome**, not a §4.3 conclusion. First
power-up and the V2 runs use **`A_X_15_96`** (DT 306 ns, stock `DEADTIMES`),
which covers the N-side worst case; V2 then steps to `A_X_10_96` (the target)
and `A_X_5_96` (102 ns, the Matrix build) only where every corner passes (§14
V2: FET case 100 °C, VIN 4.35 V plus regen, both directions of phase current).
The loss and thermal numbers use DT 10; DT 15 costs 0.06 W per motor at 4 A and
0.19 W at 12 A (−0.2 to −0.4 A on the h 80 one-channel model, −0.1-0.2 s of
12 A burst; I). This assumes the EFM8 ports run at high drive strength: Bluejay
never writes PRTDRV (V, grep of `src/` at 0368d11), so the reset default
applies. The EFM8BB51 reference manual could not be fetched (Silicon Labs
returned 403 on 2026-10-07); the Matrix shipping `A_X_5_96` with a P-FET that
models at 75-137 ns at high drive implies high drive is the default (at low
drive, about 200 Ω from VOH at 3 mA, it would shoot through at DT 5) (I). P3
cites the PRTDRV reset value; if it is low drive, the worst case grows about
3x (DT 25-40) and it is raised as a Bluejay layout issue before V2. V2 records
the drive mode.

**Thermal estimate** (I, `calc/thermal_v3.py`, track 03 §7 board model). One
motor quarter has about 0.65 J/K and 0.055 W/K lateral spreading; the whole board
sheds **0.042-0.11 W/K** (h 30-80 W/m²K over 13.9 cm², track 03 verification
#15; track 06 §4 gives 30-60 in flight). A whoop FC sits under a canopy above the
battery tray, not in the duct flow, so the low end is plausible; V8 measures h on
a board in a real frame. Limits, at 25 °C ambient: board rise ≤ 60 K for the
85 °C parts; PA case = board + k_PA·P_PA ≤ 85 °C with k_PA 6-12 K/W (I: the
spec's 10-20 K at 1.64 W; V8 measures it); RTC6705 = board + 15 K/W x 0.33 W
(I) ≤ 85 °C Tj; the loaded quarter = board + P_motor / 0.055 W/K ≤ 75 K (FET
100 °C; X6S caps in the cell are rated 105 °C, so the FET binds). The 85 °C
parts sit at board temperature only because the floorplan keeps each ≥ 2 mm
from every FET group and phase pour (rule H1, §11; sketch v5 meets it for all of
them); V4 puts thermocouples on the crystals, the TCXO, the RTC6705, the SX1281,
the ESP32-PICO-V3 and the boost to check that assumption. Trunk = 0.5 mΩ
shunt + 0.7 mΩ supply copper + 0.5 mΩ GND return through L2/L5 and the pours at
the pack current.

| Case (25 °C ambient, VTX 25 mW unless stated; ranges are k_PA 6-12 K/W) | Heat | Board rise at 0.042-0.11 W/K | Local terms | Needed for every part in rating |
|---|---|---|---|---|
| Hover, 1 A per motor | 3.4 W | +31-81 K | PA +7-13 K | h ≥ 46-53 W/m²K |
| Hover, VTX max (PA at the 27 dBm ceiling, about 1.9 W of PA + BPF heat) | 4.2 W | +38-100 K | PA +11-23 K | h ≥ 63-82 |
| Hover, HD mode (O4 at 1.2 A, analog VTX off) | 2.6 W | +24-62 K | - | h ≥ 31 |
| 4 A one channel, others 2 A | 4.9 W | +45-117 K | quarter +17 K | h ≥ 66-75 (HD 50) |
| 6 A one channel, others 2 A | 5.9 W | +54-140 K | quarter +35 K | h ≥ 107 (outside the verified range) |
| 3 A on all four | 5.4 W | +49-129 K | quarter +10 K | h ≥ 73-83 (HD 55) |
| Rating at h 55 / h 64 / h 80 | | | | one channel 0-1.4 / 1.8-3.7 / 4.7-5.1 A; all four 1.2-1.8 / 1.9-2.5 / 2.8-3.3 A; VTX max: 0 / 0 / 0-3.2 A one channel; HD: 4.3 / 4.9 / 5.6 A one, 3.0 / 3.5 / 4.1 A all four |
| 12 A burst, one motor, from the modelled hover steady state (70 °C at h 55, 63 °C at h 64, 56 °C at h 80) | 6.7 W | first order, τ 11.8 s | P-FET 1.41 W x 12.8-29.2 K/W = +18-41 K | 0-2.4 s (h 55), 0.5-3.2 s (h 64), 1.3-4.2 s (h 80) to FET 110 °C: **measured in V4** |
| 18 A, Vgs 3.0 V | 15.9 W | | P-FET 3.5 W: +45-102 K | under 0.5 s: **measured in V4** |

"Rest of board" is the §5.4 hover total without its own hover FET loss and
shunt (no double count). The continuous rating is set by the 85 °C parts and the
PA, i.e. by non-ESC heat and airflow (§5.4 heat levers); bursts are set by the
FET local rise. Both are published only as measured. If the X5R caps of the
earlier revision stayed in the cells, the 6 A case would need a board rise
≤ 25 K (h far above the verified range): hence X6S in every ESC quarter.

The battery path is the practical limit before the ESC: BT2.0 is rated 9 A
continuous / 15 A burst (V, BetaFPV) and a 300 mAh 75C pack 22.5 A (marketing).

### 4.4 ESC MCU and firmware

| Option | Verdict |
|---|---|
| **EFM8BB51F16I + Bluejay** | chosen: runs from the cell (VDD 1.8-5.5 V), QFN-20 3x3 (datasheet land 4.0 mm, Table 7.2), proven 1S at `A_X_5_96` on the Matrix/Air/CrazybeeG473 (G grade there). The **I grade** (TA and TJ to 125 °C, V Tables 4.1/4.2) is required: the G grade is TA 85 °C / TJ 105 °C abs max, a few mm from FETs that may reach 100-110 °C |
| AT32F421 + AM32 | no: VDD 2.4-3.6 V, needs a rail and a level shift for the P gate; QFN-28 4x4 |
| EFM8BB21 | no: VDD max 3.6 V operating, cannot sit on a 4.35 V cell |

| Part | Primary | Fallback |
|---|---|---|
| ESC MCU | Silicon Labs **EFM8BB51F16I-C-QFN20R**, QFN-20 3x3, I grade; Digi-Key 7,228 at $0.62/2,500 (2026-10-07, 24 wk factory lead) - a NextPCB quote-engine channel; no LCSC listing (BOM: `LCSC = none (Digi-Key)`) | no drop-in part exists; the G-grade EFM8BB51F16G-C-QFN20R (C6547511, 31,643) only with an 85 °C limit at the EFM8 |

Per channel: VDD straight to its own cluster's +BATT copper (no series R),
100 nF (GRM033C81E104KE14D, X6S) at the pin, returned to the ESC's GND, and the
datasheet's 1 µF from the phase-B hot-loop capacitor (D77): one Murata
GRM155C80J106ME11D 10 µF X6S 0402 per AGM210MAP from pin 3 (+BATT) to pin 1 (GND)
at the cell's lead side, and the phase-B one per ESC (C23 / C29 / C35 / C41) is
the EFM8 VDD bulk within 4 mm of VDD pin 4 through the +BATT plane (BR-05 as
amended, P5 condition in `tools/check_p5_conditions.py`); about 2.6-2.8 µF
effective at 4.2 V (Murata DC-bias curve), which meets the datasheet's "1 µF and
0.1 µF bypass capacitors required". The ESC3-only C30 is deleted (D77; the gyro
5 mm rule is a D69 preference). The round-2 0201 1 µF part gives only 0.4-0.6 µF
at bias and is the fallback only with a V3c ripple check at the pin. The off-state P-gate level then tracks the P sources;
the residual Vgs excursion is the IR and L·di/dt difference between the VDD pin
and the three P source pads (tens of mV DC, ns spikes; I) against a hot P
threshold of about −0.39 V. DShot series 2.4 kΩ (Ralec RTT012401FTH, C166281
[PU]) limits injection into an unpowered EFM8 when only USB is connected (10 kΩ
is the fallback if V9 shows EFM8 brown-out cycling); RSTb uses the internal
pull-up (most BB51 ESCs do; the 1 kΩ of datasheet Fig 5.2 is dropped by the lean
rule, PINMAP F12); BEMF network of 6x 0201 (values from tinyPEPPER, checked
against layout A in P4); C2D and C2CK test pads for production programming and
recovery (§12.1). Layout A pin use (V, Bluejay `src/Layouts/BB51/A.inc`): P0.1
B_Mux, P0.2 C_Mux, P0.3 A_Mux, P0.4 V_Mux (neutral), P0.5 DShot; P1.0 A_Pwm (N
gate), P1.1 A_Com (P gate, active low), P1.2 B_Pwm, P1.3 B_Com, P1.4 C_Pwm, P1.5
C_Com; P2.0 C2D. Unused P0.0, P0.6, P0.7, P1.6.

**VDD peak and logic-high margin** (I). EFM8BB51 VDD absolute maximum is
5.5 V, the same as the operating maximum (V, Tables 4.1/4.2). With no series R,
VDD follows the cluster +BATT: a fresh 4.35 V LiHV pack plus half the 96 kHz
ripple (0.2-0.3 V) gives 4.55-4.65 V; regen on a throttle chop in damped mode
(rotor energy pushed back through the 30-60 mΩ battery path, 5-10 A) adds
0.15-0.6 V, so 4.7-5.25 V before spikes. The guaranteed VIH (0.7·VDD, Table
4.18) rises to 3.19-3.26 V at the ripple peaks against the RP2350's ≤ 3.3 V drive
(PINMAP F4: 0.04-0.11 V margin at 96 kHz, negative at 48 kHz). V3c measures VDD
at the pin under chops, braking and battery hot-plug on a fresh 4.35 V pack (pass
≤ 5.3 V including spikes). Stock Bluejay cannot report a rejected DShot frame (a
checksum failure only increments an internal counter and produces no telemetry
reply; the EDT status frame carries no error count; V, `Isrs.asm`,
`Scheduler.asm`), so V9 scopes the DShot high level against 0.7·VDD at the EFM8
pin and counts checksum failures with a non-release Bluejay debug build that
pulses the layout-A DebugPin (P2.0, the C2D test pad) on each, logged by a
logic analyser at 4.35 V under load. Fallbacks, in
order: Bluejay braking limits in the published settings, then a 2.2-4.7 Ω VDD
resistor (inside track 03 §8's tracking bound; a 0201 position if P2 has room).

**No gate resistors**, by field record: tinyPEPPER (V, `single_esc.sch`) drives
its P+N gates straight from the EFM8, as do the BB51 layout-A whoop boards. With a
typical driver of about 25-30 Ω the gate-edge current is VDD / (25-30 Ω + RG),
about 0.13-0.17 A for nanoseconds: a transient exceedance of the 50 mA per-pin
absolute maximum (Table 4.1, not qualified as DC), accepted on field record
(tinyPEPPER, Matrix parity). If P2 has room, the N gates get 0 Ω-option 0201
footprints.

### 4.5 FC MCU

| Criterion | RP2354A (house, OpenFC-Lite-Mini) | STM32G473CEU6 (Matrix, UD 4IN1) |
|---|---|---|
| Placed area with OSD | about 97 mm² (PIO OSD front end 8 mm²) | about 115 mm² (AT7456ELAH) |
| OSD current | about 5 mA front end | +43 mA typ AT7456E |
| OSD without a camera | none: the PIO OSD overlays on detected camera sync (`osd_pico.c`) | AT7456E free-runs (warnings visible without a camera) |
| OSD part stock | n/a | AT7456ELAH LGA-16: 78 at LCSC (fails the gate); HTSSOP-28 adds about 30 mm² |
| Betaflight maturity | core feature set in a release only since 2026.6.2; bidirectional DShot decode shows about 5-8 % errors with spinning motors (upstream note in `dshot_bidir_pico.c`); everything runs on core 0 | mature (BETAFPVG473_V2) |
| VTX control | MSP-VTX from the ELRS RX (§4.8) | same |
| Stock | 14,698 (LCSC); not on HQ Online | 750 (LCSC), 45 HQ Online |

**Decision: RP2354A.** It is the README constraint, it reuses the flown
OpenFC-Lite-Mini `rp2350a`, `imu` and `osd` sheets, and with the VTX driven by
the receiver nothing on the critical path depends on missing Betaflight
features. Its costs are firmware age (bench gates V9) and the camera-dependent
OSD: OSD setup on the bench needs battery **and** camera, stated in the README;
V9 covers the camera-unplugged case. Fallback (documented, no dual footprint):
STM32G473CEU6 + AT7456E HTSSOP-28.

| Part | Primary | Fallback |
|---|---|---|
| FC MCU | Raspberry Pi **RP2354A**, QFN-60 7x7 0.4 mm, 2 MB in-package flash, C41378174, 14,698 [PU] | ST STM32G473CEU6 (C1342773, 750) with AT7456E (new sheet) |
| 12 MHz crystal | Abracon **ABM8-272-T3**, 3225, 12 MHz, CL 10 pF, ESR ≤ 50 Ω, ±30 ppm, −40..85 °C, C20625731, with C42 / C43 15 pF and R40 1 kΩ (D78: RP2350 DS §8.2.1.1 Table 629 names it; the RPi guide sized the 1 kΩ for it) | none staged; the earlier YXC X252012MMB4SI-24 (2520, ESR 150 Ω) is superseded by D78. Not the house TOGNJING part (−20..70 °C) |
| Status LEDs | XINGLIGHT **XL-1005UGC** green (C965793) and **XL-1005UBC** blue (C22355736), 0402, sinking into GPIO7/26 from +3V3 [PU] | Kept at 0402 for the house colours. The commons-verified Kingbright 0201 family was checked: the green APG0201ZGC-5MAV is InGaN with Vf 2.85 V typ at 5 mA (S, Digi-Key listing), and blue InGaN parts sit at or above that, which leaves 0.25-0.45 V for the resistor at 3.3 V sink drive, so the current is set by the Vf spread, not the resistor. Red/orange AlInGaP 0201 parts (Vf about 2 V) work and save 1.2 mm² but change the house colours: a P2 lever |
| LED-strip drive | **none: GPIO8 drives the LED pad directly**, no series resistor, like the other user pads (D52 BR-04; Matrix II parity: `LED_STRIP_PIN PB2` direct, V). A WS2812 at 5.15 V wants VIH 3.6 V, so the README carries the Betaflight inline-diode note and V9 tests a strip | Nexperia 74LVC1T45GM,115 (XSON6 SOT886, 0.5 mm pitch, VCCA +3V3 / VCCB +5V) if V9 fails on the target strips. The round-4 74LVC1T45GS (SOT1202, 0.35 mm pitch) and its two caps are deleted |
| Beeper FET | ALLPOWER **AP1606**, DFN-3L 1.0x0.6, 20 V, Vgs(th) 1.2 V, C2849580, 2,000 [PU] (also the HD gate, D53 BR-03; 2 per board: the round-4 USB term is deleted, BR-10) | Nexperia PMZ250UN class (S), land check in P3 |

`rp2350a` sheet reuse, changes: remove USB-C, CC and I2C pull-ups; USB D+/D−
(27 Ω series) to the JST SH J31 through the D7 ESD array (D57 / D76); VREG_AVDD RC 27 Ω + 4.7 µF (the USB
series value, D52 BR-21; corner 1.25 kHz); decoupling per PINMAP §3 (BR-08:
QSPI_IOVDD shares the USB_OTP_VDD cap, which sits ≤ 1 mm from pin 54, and
ADC_AVDD shares the IOVDD pin-45 cap, placed at pin 44); VBAT divider 100k/10k → 10k/10k;
crystal swapped (above); GPIO map below; SWD to the CLK / DIO test vias (D67); the boot
button is the shared SW1 + D8 on the RX sheet, R44 1k from QSPI_SS to FC_BOOT, FCB test via
(D65 / D67).

**FC pin map (RP2354A, QFN-60; detail in PINMAP §2)**

| GPIO | Function | Peripheral |
|---|---|---|
| 0 / 1 | CRSF to ESP32 (ELRS RX; also serial passthrough) | UART0 TX/RX |
| 2 / 3 | user UART pads TP0 / RP0 (D16) | PIOUART0 (PIO1) |
| 4 / 5 | DJI O4 Lite pads TX1 / RX1: MSP DisplayPort (D16) | UART1 TX/RX |
| 6 | gyro pin 9 (CLKIN for TDK; INT2 on BMI270, unused) | PWM slice 3A (32 kHz CLKIN) |
| 7 | LED0 green (status) | GPIO |
| 8 | LED strip, driven direct (PINMAP F1, D52 BR-04) | PIO1 (WS2812) |
| 9 | gyro INT | GPIO IRQ |
| 10 / 11 / 12 / 13 | gyro SCK / MOSI / MISO / CS | SPI1 |
| 14 / 15 / 16 | OSD_W / OSD_EN / OSD_SYNC (must be consecutive) | PIO2 (FB OSD) |
| 17 | beeper (low-side FET) | GPIO / PWM slice 0B |
| 18 / 19 / 20 / 21 | NOR SCK / MOSI / MISO / CS | SPI0 |
| 22 / 23 / 24 / 25 | M4 / M3 / M2 / M1 | PIO0 (bidirectional DShot) |
| 26 | LED1 blue | GPIO (ADC0 unused) |
| 27 | HD line: O4 switch enable and analog-VTX hold-off (D15, D17); 2.4 kΩ pull-down = analog mode at reset (BR-24) | PINIO1 |
| 28 | current sense | ADC2 |
| 29 | VBAT sense | ADC3 |

Conflict check (I, V in PINMAP §4): 30 of 30 GPIOs used. PIO0 holds DShot (29
of 32 instructions, 4 state machines). PIO2 holds the FB OSD (31 instructions),
so the LED strip moves to PIO1 with `PIO_LEDSTRIP_INDEX 1`. PIO1 then holds
WS2812 (4) + PIOUART0 tx (10) + rx (9) = 23 of 32 instructions and 3 of 4 state
machines; `PIO_UART_INDEX` defaults to 1 and both drivers claim state machines
and load programs dynamically, so they share the block by code (V, 2026.6.2
`target_RP2350.h` L96-101, `uart_pio.c`); no upstream board runs both, so V9
tests it with the O4 and the FB OSD. PWM slices: 0B (beeper) and 3A (CLKIN) are
the only PWM users. DMA: 8 of 16 channels (DShot and the UARTs use none, PINMAP
F6).

### 4.6 Gyro

| Candidate | Stock | Note |
|---|---|---|
| **Bosch BMI270** | C2836813, 7,795, $2.66 [PU] | house current part; widely flown on 1S whoops; Betaflight 3.2 kHz ODR; house IMU study rates it "higher risk" for MEMS resonance on the 20x20 sister board; TA 85 °C |
| TDK ICM-42688-P (genuine) | C1850418, 3,029, $19.64 | house study's only "empirically proven" part; 8 kHz; CLKIN |
| ST LSM6DSV16X | 7,523 [PU] | rejected: house and Betaflight ecosystem call it unflyable |
| TDK ICM-45686 | 3 | no stock |

**Decision:** universal LGA-14 land of the OpenFC `imu` sheet (P4: pins 2/3 NC, not GND - BMI270 DS Table 22; was: pins 2/3 GND,
10/11 NC, pin 9 to GPIO6), **BMI270 on the BOM**, ICM-42688-P qualified on the
same land. The prototype run is split 5 + 5 and a hover fly-off on the target
frame (noise metric §2 rank 6) picks the release population. One gyro per
revision, declared in the Betaflight target. Supply: own +1V8 from
TPS7A2018PDQNRM3 fed from +3V3, next to the gyro on the same side. Decoupling
(D52 BR-09): the LDO's two 1 µF capacitors double as the gyro's, with no extra
100 nF: CIN between U12 IN and BMI270 VDDIO (pin 5), COUT at BMI270 VDD (pin 8);
P5 rotates the LDO so OUT faces pin 8 where it can (as placed, COUT lands about
3.4 mm from U12 OUT, a D33 MINOR: about 20 mΩ of trace against the 100 mΩ ESR
limit). The gyro noise test (V10) stays. Placement
(§10, sketch v5): top, rear quadrant inboard of the NOR, rotated 90°, inside the
4 mm FET ring (4.04 mm from the ESC3 and ESC1 P groups); edge-to-edge distances
§11.

### 4.7 Receiver

The house design is the OpenRX-Lite ESP32-C3 + SX1281 circuit. Two facts from
the research change the MCU:

1. Mainline ExpressLRS 4.0.0, 4.1.0 and master register the VTX SPI and MSP-VTX
   devices only under `PLATFORM_ESP32 && !PLATFORM_ESP32_C3` (V, track 05
   verification, `src/src/rx_main.cpp` l. 91-95). A C3 cannot drive the VTX on
   ELRS 4.x; it also has a single general-purpose SPI and would use 15 of 15
   usable GPIO. This is why the owner's OpenRX-Lite-UFL lead (ESP32-C3FH4 with
   in-package flash) cannot be reused as is (BOM-REDUCTION §0, RV-6).
2. ESP32-C3FH4 has 0 LCSC stock (2026-10-07), 89 on HQ Online (track 07).

The FC cannot take the VTX either: Betaflight on the RP2350 has
`#undef USE_VTX_RTC6705`, and the FC has no spare GPIO (RV-7).

| Option | Area / parts (placed) | VTX control | Sourcing | Verdict |
|---|---|---|---|---|
| ESP32-C3FH4 + SX1281 (OpenRX-Lite) + separate VTX MCU | 86 + 25 mm² | VTX MCU on a half-duplex PIOUART (new code) | C3FH4 0, GD32F130G6 broker-only | no |
| OpenRX-Lite-UFL block (ESP32-C3FH4 / ESP8685H4, in-package flash) | 42 parts | none on ELRS 4.x (above) | - | no (RV-6); the ESP8685H4 (105 °C, 4x4) would be ideal if C3 VTX support returns upstream |
| **ESP32-PICO-V3 (SiP: flash, 40 MHz crystal and CAP network inside) + SX1281** | RX block 19 placements (plan: 32); +10.6 mm² bottom against the plan, in a new site | ELRS `devVTXSPI` + `MSPVTX` on the shipping code path, stock `Unified_ESP32_2400_RX` with the board's own layout JSON (three pins moved, below) | LCSC 335, Digi-Key 4,812; HQ Online only the V3-02 (443) | **chosen (D52 BR-01)**, gated by a P2 placement trial: **85 °C ambient** (in-package flash), so it must leave the PA shadow |
| ESP32-D0WD-V3 + 4 MB NOR + 40 MHz crystal + SX1281 | about 96 mm² (32 placements in the plan, which missed CAP1) | same; pin-compatible with ELRS layout `Generic 2400 Whoop Rx and VTx.json` | 583 / 1,129 (LCSC); ESP32 also listed at Digi-Key (S) | BR-01 fallback (BOM-REDUCTION §5.1), with the 0.35 mm-pitch EQ (below) |
| ESP32-U4WDH (D0WD land, in-package flash) | −2 parts | same | LCSC 0, Digi-Key 0 | no (RV-5): 85 °C like the PICO, still the CAP network and the 0.35 mm EQ |
| SPI ELRS on the FC | 37 mm² | none | - | not available on RP2350 |
| ESP32-S3FH4R2 | 7x7 + crystal | same | 17 | no stock |

**Fine pitch.** The ESP32-PICO-V3 is QFN-48 7x7 at 0.5 mm pitch, inside the
fab intersection, so it needs no EQ (D53). The ESP32-D0WD-V3 of the BR-01
fallback is QFN-48 5x5 at **0.35 mm pitch** (lead width 0.18 mm, Espressif
datasheet); NextPCB publishes 0.38 mm as its fine-pitch limit (track 07 S4) and
JLC's PCBA floor is 0.35 mm, so that part is outside the fab intersection. On
the fallback it alone goes to the NextPCB EQ (O15) with 0.18 mm pads, one
ganged mask opening per side and a scoped DRU exception for that footprint
(D21, D38, D43). The two other 0.35 mm-pitch leadless parts of round 4, the
74LVC1T45GS (SOT1202) and the BC847QASZ (SOT1216, twice), leave the BOM with
BR-02 to BR-04 (§4.5, §4.8).

**Decision (D52 BR-01, gated):** Espressif **ESP32-PICO-V3** with the SX1281
radio. The package holds the 4 MB flash, the 40 MHz crystal, the CAP1/CAP2
network and most bypass capacitors (V, Espressif PICO series datasheet v1.3
Fig. 8); outside it stay 10 µF + 100 nF on VDD33 (Fig. 11), the CHIP_PU RC
(10 kΩ + 1 µF) and the LNA_IN dummy load. Against the plan's ESP32-D0WD-V3 it
removes the GD25Q32 flash, the 40 MHz crystal and its two load caps, the
VDD_SDIO capacitor, six bypass capacitors and the CAP1 10 nF the plan had missed
(Espressif: "required for proper operation"): 12 placements and 2 lines, and
the RX block goes from 32 to 19 placements with BR-06 and BR-25. Like the
round-4 choice it deletes the VTX MCU, uses no FC UART for the VTX and needs no
Betaflight driver. The FC sees an MSP VTX over CRSF (`USE_VTX_MSP`, in RP2350
releases from 2026.6.2).

**Gate: P2 placement trial.** The PICO is rated −40..85 °C ambient (the
in-package flash sets it), so under rule H3 it sits ≥ 2 mm outside the PA
projection (bottom keep-out x 4.32..12.72, y −13.4..−5.0 mm) and ≥ 2 mm from
every FET group (H1), with check_spacing at 0; it cannot reuse the D0WD site
under the PA and adds 10.6 mm² on the bottom, against 11.3 mm² the rest of the
D52 set frees there in scattered pockets. The only H3-free strip of the bottom
front quadrant holds the pogo USB pads, the TPS2116 and the 12 MHz crystal, so
the trial re-plans that quadrant; reserves are the BR-05 top variant (−6.9 mm²
bottom) and the INA186 in DSBGA (PE-13, −3.6 mm²). It needs its own P3 symbol
and footprint. **Fallback** (BOM-REDUCTION §5.1, 256 placements / 78 lines):
keep the ESP32-D0WD-V3 with its GD25Q32EEIGR and CJ17 40 MHz crystal, move the
flash ≥ 2 mm out of the PA projection (west of x 4.3 or south of y −5.0 mm) or
take a 105 °C flash grade, add CAP1 (10 nF X7R GRM033R71A103KA01D, pin 48 to
GND; the CAP1-CAP2 RC is not needed without deep sleep, which ELRS never uses),
delete C77; the 0.35 mm EQ and the ganged-mask rule then stay for the ESP32
alone.

**Pins (D53).** The PICO's in-package flash uses GPIO16/17/18/23 and GPIO6/11
(Fig. 8; pins 30/31 are flash CMD/CLK, pins 25, 35, 36, 44, 45, 47 and 48 are
NC, Table 4, V), so GPIO18 and GPIO23 are not exposed and the stock layout
`Generic 2400 Whoop Rx and VTx.json` cannot be used as is. The board's own
layout JSON moves `vtx_mosi` to **GPIO14** (pin 17, MTMS, not a strap), writes **`"vtx_miso": -1` explicitly** (D81: an overlay only replaces keys, so an
omitted key keeps the stock GPIO23, the PICO's flash DI, which `SPIClass(HSPI).begin()` in Arduino-ESP32 2.0.x
turns into an input: flash data cut, crash at VTX init on every boot; with -1 the core attaches the HSPI
default GPIO12, unconnected here, as an input; ELRS only writes the RTC6705) and puts `vtx_amp_pwm` on **GPIO13**
(pin 20, MTCK, not a strap) for the PNP stage of §4.8 (BR-02). GPIO13 and
GPIO14 are free on the D0WD too, so the same JSON serves the fallback and the
pin plan does not fork. The rest follows the generic layout (V,
ExpressLRS/targets 42ed776): CRSF on ESP32 GPIO1/3, radio
SCK/MOSI/MISO/NSS/RST 25/32/33/27/26, BUSY 36, DIO1 37, RGB LED 22, VTX
NSS/SCK 19/5, PA detector 4, PA enable (`vtx_amp_vref`) 2, button/boot 0. Two
pins are added for the patched firmware only (O6): GPIO21 = +3V3_VTX LDO enable
(pulled up, so stock ELRS runs the VTX as usual) and GPIO34 = PA NTC (ADC1). The
board needs its own JSON and overlay anyway (`ledidx_rgb_vtx`, VPD arrays; the
house OpenRX precedent), and ELRS has run on the ESP32-PICO since bd4f4e7f
(#1526, V). Detail in PINMAP §6.

Straps: GPIO12 (MTDI) is now unconnected, and its internal pull-down holds the
3.3 V-flash strap at reset, so the VDD_SDIO eFuse burn of the first flash
(§12.1) no longer guards it and its place in the order stops mattering (PINMAP
F18); GPIO2 reads low through its own strap pull-down and the LP5907's internal
1 MΩ EN pull-down (BR-12), checked in P4. The bootloader's handling of the
in-package flash pins is confirmed at V1 bring-up (I). ESP32 erratum 3.11
(powering SAR ADC1/ADC2 pulls GPIO36/39 low for about 80 ns) touches radio
BUSY on GPIO36: stock ELRS reads the PA detector only outside the hop window
(`timeout()` returns early while `hwTimer::isTick` is false, V, devVTXSPI.cpp
at 8c51826); the NTC read must follow the same rule (O6 gate 6).

The RF section is the OpenRX-Lite / OpenAIO `rx_esp32c3_sx1281` circuit reused
(TCXO, filter, match, LDO-mode radio), with these changes: MCU swap; the radio
stays the house **SX1281** (D52 BR-25: the OpenDrone library part; the
SX1280/1 datasheet lists them as identical except for the ranging engine,
which ELRS does not use, and ELRS's driver does not branch on the variant;
SX1280IMLTRT stays the drop-in alternate on the BOM line); radio decoupling
per Semtech Table 15-1 plus 1 µF, the house sheet's extra 10 nF and 10 µF
deleted (BR-06; V7 checks TX droop); 15 µH DC-DC inductor deleted (the ELRS
layout has no `radio_dcdc`); 52 MHz TCXO kept (D53: a 2016 crystal is refuted
for rev1, ELRS SX128x does no frequency correction and FLRC needs ±20 ppm per
link); ceramic antenna deleted, wire-antenna plated hole instead; **fix the
sheet defect: SX1281/SX1280 pin 5 is GND and is unconnected on both sibling
sheets** (09 verification). Sheet file name `rx_esp32_sx1281` (D53; round 4
proposed `rx_esp32_sx1280` under D33): a lineup exception to A2 ("a copied
sheet keeps its file name"), because the MCU changed and the copied name
`rx_esp32c3_sx1281` would describe a part the sheet no longer has.

> **Superseded by D58 (owner, 2026-10-09):** ELRS Wi-Fi is restored with the Johanson 2450AT07A0100001T chip antenna AE2 behind R88 0 Ω and the C132/C133 (DNP) pi match on `RF_WIFI` / `RF_WIFI_ANT`; the schematic (`rx_esp32_sx1281.kicad_sch`, P4) follows D58 and Wi-Fi is a bench-only update mode (+3V3 peak about 0.48 A). The paragraph below is the pre-D58 record.

**Wi-Fi (PINMAP F9): no radiator** (D18 lever 2, logged as D25). The
round-2 printed stub needed a board edge next to ESP32 LNA_IN with a 2 x 4 mm
all-layer copper keepout. No edge segment exists: the RX MCU sits in the bottom
front quadrant, whose edge lies under the 5.8 GHz chain, where an all-layer keepout would
remove the L2 reference that `RF_VTX_CHAIN` requires and put a 2.4 GHz
radiator about 1 mm under the PA output and U.FL; the other bottom edges hold
the FET rows, the RX wire exit, the pogo USB pads and the battery block. The
Johanson 2450AT18B100E chip antenna needs the same edge and clearance. So
LNA_IN ends in a 0402 51 Ω dummy load (63 mW; the ESP32 never transmits into an
open pin if a user starts Wi-Fi from the Lua), ELRS is flashed with
`--no-auto-wifi`, and ELRS updates and configuration go through Betaflight
serial passthrough, the path the production flow uses anyway (§12.1). The
README says the board has no ELRS Wi-Fi (the Matrix II has a Wi-Fi chip
antenna: a recorded parity loss). ELRS calls `disableVTxSpi()` when Wi-Fi starts
(V, devWIFI.cpp l. 1107 at 8c51826), so a VTX target's Wi-Fi behaviour stays an
O6 patch item. Recovery: hold SW1 while powering, reboot the RP2354A into
Betaflight, then esptool through passthrough (§12.1). There are no extra ESP32
UART pads (they would put a second driver on the FC's UART0_TX net).

| Part | Primary | Fallback |
|---|---|---|
| RX MCU | Espressif **ESP32-PICO-V3**, SiP QFN-48 7x7, 0.5 mm pitch, 4 MB flash and 40 MHz crystal inside, −40..85 °C ambient (V, PICO datasheet v1.3), LCSC C967022 335, Digi-Key 4,812 (2026-10-09); alternate ESP32-PICO-V3-02 (8 MB flash + 2 MB PSRAM on pins 28/29, unused here; HQ Online 443) | BR-01 fallback: Espressif ESP32-D0WD-V3, QFN-48 5x5 (0.35 mm pitch, O15 EQ), C967021, 583, with the flash and crystal below and CAP1 10 nF X7R on pin 48 |
| RX flash | none (in the package) | fallback only: GigaDevice GD25Q32EEIGR, USON-8 2x3, I grade −40..85 °C, C2973794, ≥ 2 mm outside the PA projection (or a 105 °C grade); Winbond W25Q32JVUUIQ, USON-8 3x4, C2999380 |
| 40 MHz crystal | none (in the package) | fallback only: JSCJ CJ17-400001010B20, 1612, C2875272 [PU]; operating range not listed (P3) |
| Radio | Semtech **SX1281IMLTRT**, QFN-24 4x4, C2151551, LCSC 283, HQ Online 146 (2026-10-09) [PU] (D52 BR-25) | Semtech SX1280IMLTRT, C125969 (same pinout and driver; ranging engine only) |
| 52 MHz TCXO | YXC **OW7EL89CENUNFAYLC-52M**, 2016, −30..85 °C, C22434896, 5,975 [PU] (kept, D53) | a 52 MHz 2016 crystal only after a V7 hot / cold F500 / F1000 test of a sample (RV-2) |
| 2.4 GHz front-end filter | Johanson **2450FM07D0034T**, 1005, C2651081 [PU] (OpenRX-Lite, OpenRX-Lite-UFL, OpenAIO): input impedance-matched to the SX1280/SX1281 RFIO and internally DC blocked (Johanson detail spec p1), pin 1 IN toward the chip, 50 Ω out (P4 critique; D60 removed the stock gate that had moved it to the fallback) | TDK DEA102700LT-6307A2 (50 Ω LPF) only with the Semtech RFIO match (0.8 pF shunt + 3.0 nH series) and a 100 pF C0G DC block ahead of it (Semtech DS Rev 3.2 §15.1), tuned in V7 |
| RGB LED | XINGLIGHT **XL-1010RGBC-2812B**, 1x1 mm, C5349953, 364,820 [PU] | none (single source) |

Numbers: +13 dBm, no PA/LNA (Matrix ELRS layout `Generic 2400`,
`power_values [13]`, V). Radio in LDO mode costs about +6 mA. ESP32 ELRS load
about 0.07 A; RX share of the merged +3V3 rail 0.10 A average, 0.16 A peak in
flight.

### 4.8 VTX and OSD

| Question | Options | Decision |
|---|---|---|
| Synthesiser | RTC6705/RTC6705A (QFN-40 6x6; Fc 5725-5865 MHz over −40..85 °C, V); MAX2871/LMX2572 discrete | **RTC6705 or RTC6705A**; no alternative exists (04 §2.4) |
| PA | RFPA5542 (Matrix, EOL 2023, 5 V only, Iq 150 mA), SKY85743-21 (4.2-5.5 V, LGA 3x5, Iq 190 mA), SE5004L (5.15-5.85 GHz, VCC 3.0-5.5 V, Icq 300 mA, case ≤ 85 °C), QPA9501 / TQP5525 (350 mA, low stock) | **SE5004L-R** on the cell; QFN-20 4x4 footprint shared by six PAs (04 §3.3). No lower-Iq PA exists on that footprint at a 1S supply |
| Control | separate VTX MCU (Matrix MM32F003), Betaflight RTC6705 driver (`#undef` on RP2350), ELRS RX MCU | **ELRS ESP32 `devVTXSPI` + `MSPVTX`** (§4.7) |
| OSD | AT7456E + 27 MHz crystal (40 mm², 50 mA, LGA 78 pcs); PIO FB OSD | **PIO FB OSD** (OpenFC `osd` sheet minus the COS8051 buffer), front end on the bottom; no OSD without camera sync |
| Harmonic filter | none (Matrix) vs LTCC BPF | **Walsin 1608 BPF**; guarantees 20 dB at 10.3-11.7 GHz, 12 dB at 7.25-7.8 GHz (V, Walsin PI V01); rated −40..85 °C, so it sits on the PA side away from the PA body; power handling to be confirmed with Walsin (O7) |
| Connector | U.FL, MHF4, soldered coax | **U.FL** |

Chain: camera CVBS (CAM pad) → 75 Ω → SN74LVC1G3157 (camera / OSD level) →
RTC6705 video network (OpenOSD-X reference values) → RTC6705 PAOUT1 (+2 dBm) →
10 pF DC block → 50 Ω CPWG < 5 mm → SE5004L (output match inside the PA, DS
202393B p. 1) → BPF → U.FL. The PA output DC block (C119, 10 pF 0201) was
deleted at P4 (P4-18, D52 BR-17): the SE5004L RFOUT has an internal
DC shunt and only RFIN is marked "DC block required" (V, datasheet p. 1), and a
10 pF 0201 at 5.8 GHz sits above its self-resonance (about 3 GHz, I); no DNP
footprint is allowed on the RF line, so P4 decides fitted or deleted. RTC6705,
its PNP drive stage and the PA reference on +3V3_VTX. Net names: `RF_PAOUT1`, `RF_PA_IN`, `RF_PA_OUT`, `RF_UFL` (class RF by
pattern). Floorplan (sketch v5, §10): the PA is rotated so its VCC sides face
left and right, each with a 1.0 mm 0201 ring (the six EK1 capacitors, DET
1 kΩ / 100 pF, NTC); RF IN faces down to the RTC6705, whose PAOUT1 (pin 35) faces
right, over a 4.4 mm 45° CPWG inside a part-free band that holds only the DC
block and the 4.7 nH choke with its bypass at pin 35; RF OUT faces the top edge,
straight into the BPF and U.FL along the edge (no match parts; the 1.5 mm "match
zone" of the sketch is a layout-only reserve that P5 may drop). The 8 MHz reference
frequency is fixed by firmware: ELRS writes register A = 0x0190 (R = 400) and
computes N/A as 25·f/64 (V, devVTXSPI.cpp l. 22, 128-131 at 8c51826), so any
2520 replacement must be exactly 8 MHz.

**PA drive stage (inverting, one PNP in current mode; D52 BR-02, PINMAP F15).**
ELRS raises output by lowering the PWM count; the window is set by firmware
constants, not target keys: `MIN_PWM` 2000 = YOLO (maximum drive), `MAX_PWM`
3700 = pit, out of 4096, written as `PWM.setDuty(ch, count*1000/4096)` (V,
devVTXSPI.cpp l. 30-31, 164 at 8c51826). The usable range is therefore 49-90 %
duty in 0.1 % steps (about 4 counts per real step), 1.6-3.0 V after the RC.
Stage: ESP32 **GPIO13** (10 kHz; moved off the stock layout's GPIO12 by the
board's layout JSON, §4.7) → two-pole RC (2x 1 kΩ RC0201FR-071KL + 2x 1 µF
GRM033R61A105ME44D; dominant pole about 61 Hz nominal, about 100 Hz with DC
bias, about −70 dB at 10 kHz, I), whose second resistor feeds the base of one
Nexperia **BC857BM,315** PNP (45 V / 100 mA, hFE 220-475, Ptot 250 mW,
DFN1006-3 SOT883; S, Nexperia parametrics) → emitter through **Re** to
`+3V3_VTX`, collector → R65 10 Ω → the 4.7 nH choke → RTC6705 PAOUT1. A lower
duty pulls the base lower and drives more current, so the stage inverts as
ELRS needs (F15), and it feeds PAOUT1 in **current mode** (round 4's two-NPN
stage fed it in voltage mode through a follower). Re sets both the YOLO
current ceiling and the slope and replaces round 4's collector-divider knob.
P4 ngspice run (I; Nexperia BC857BM model, PAOUT1 sink model, hFE 220-475, −20..85 °C;
`research/bomred/verify/pnp_spice/`, which supersedes the BOM-study hand model `pnp_fix.py`): YOLO
ceiling (top step, count 2000) 20-31 mA at Re 27 Ω, 28-47 mA at 15 Ω, 32-59 mA at 10 Ω, rising with
hFE and temperature; pinch-off (< 0.1 mA) at 3240-3516 counts, which matches the Happymodel ELRS AIO calibration
(25 and 100 mW at 3133-3263 counts, V); the 10-90 % span covers counts
2121-3141, about 255 real duty steps (≥ 20 asked between 25 and 100 mW).
**Start Re at 10-15 Ω** (10 Ω reuses the R65 line, RC0201FR-0710RL); V5 sets
the final value. Q27 dissipates at most 114 mW (Re 10 Ω, hFE 475, 85 °C; 93 mW at 15 Ω, 64 mW at 27 Ω)
against Ptot 250 mW at 25 °C, i.e. 130 mW at 85 °C ambient (Rth(j-a) 500 K/W, S): a 12 % margin
at 10 Ω in the PA area, so V5 logs Q27 case temperature at the top step hot (lever: Re 15 / 27 Ω).
R73 and R65 carry the same 58.5 mA: about 34 mW each against the RC0201 derating (50 mW to 70 °C,
zero at 125 °C: 36 mW at 85 °C, 27 mW at 95 °C); V8 measures the top-step current and the local
temperature (levers: cap the ELRS power-table top count so Ic ≤ 45 mA, or Re 27 Ω). In HD mode `+3V3_VTX` is at 0 V while GPIO13 may sit
high: both junctions are reverse-biased (EB 3.3 V against VEBO 5 V, S), so the
PWM pin cannot back-power the rail. Why GPIO13: a PNP on GPIO12 would pull that
strap to about 2.6 V at reset through its base current into the internal
pull-down (I), unsafe for the 3.3 V-flash strap unless the eFuse were burned
first; GPIO13 is free and no strap on both the PICO and the D0WD, so the pin
does not depend on the BR-01 trial. Parts: 6 (PNP, RC 4, Re) against round 4's
BC847QASZ + 9 passives. **Gate: P4 SPICE before the schematic freeze** with a
PAOUT1 load model and the V8 PAOUT1 current (the RTC6705 datasheet gives that
current as "TBD", upper bound 95 mA for the whole chip in 13 dBm mode); V5 and
V8 confirm on the board. Field evidence for the class (I): OpenVTx GD32 targets
and the Happymodel ELRS AIO run their RTC6705 bias PWM 0.55-1.1 V below the
3.3 V rail, the signature of one rail-referenced PNP; their schematics are not
public. **Fallback if SPICE fails (PS-12):** round 4's two-NPN stage with
corrected values (R71 = R72 = R74 = 3.3 kΩ, C124 = C125 = 1 µF, R73 omitted,
R75 = 75 Ω), which also fixes the round-4 base divider that could never turn Q1
on (Vb = 0.119 x V_PWM, BOM study F-A), plus PS-14 (PR1 divider 3.3k / 1.2k,
same ratio) to hold 76 lines; it brings back the 0.35 mm-pitch BC847QASZ and
its EQ.

**Hardware power ceiling.** At a fixed drive the SE5004L output spreads 6-8 dB
across parts, channels, temperature and VCC (gain 30 min / 32 typ dB with no
maximum, 3 dB variation within a band, less hot and at 3.0 V; V datasheet; I
spread). Round 2 sized the limit so that a minimum-gain part at 85 °C and 3.0 V
"just reaches 400 mW", which cannot happen: the minimum P1dB is 30 dBm at 5 V
(V, 202393B), about 25.2-25.6 dBm scaled to VCC 3.0 V before the 85 °C derating
and the ≈1.5 dB BPF loss (track 04 verification), so that criterion would set
the limit to maximum drive. The limit is therefore a **ceiling**: the PNP
stage's Re (above; it sets the YOLO current into PAOUT1) is chosen in V5 so
that the highest-output sample at 4.35 V and 25 °C stays
**≤ 27 dBm at the U.FL** at YOLO drive (or a firmware fault). V5 publishes what
the lowest sample reaches at 3.0 V and 85 °C case (about 23-25 dBm expected, I).
`400` is therefore "max (measured, power-limited)" per board until the
closed-loop setpoint (O6 gate 2) exists, and 400 mW is not guaranteed at sag.
At the ceiling the PA delivers up to 28.5 dBm (0.71 W) into the BPF; with about
30 % PAE that is about 2.4 W from a 3.7 V cell and about 1.9 W of PA + BPF heat
on the board (I), the figure §4.3 and §5.4 now use (was 1.64 W at a 400 mW
setpoint); without the ceiling a high-gain part would saturate at 29-31 dBm and
dissipate 2-3 W. O7 asks Walsin about 0.71 W at the BPF input. Pit on boot (RCE,
below), a README antenna warning and a no-antenna run in V5 cover ruggedness:
the datasheet gives only PIN −10 dBm CW into 6:1 VSWR, and "VTX burns without
antenna" is a known Matrix issue.

**PA enable and bias.** PA pin 5 (VREF/EN) is driven by a **switched 2.85 V
reference** (TI LP5907SNX-2.85, ±2 %, input `+3V3_VTX` (D53 BR-03), EN = ESP32
GPIO2 directly: no series resistor and no external pull-down (BR-03, BR-12),
because the LP5907 EN is rated −0.3..6 V to GND whatever VIN does (V, SNVS798
§5.1) and has an internal 1 MΩ pull-down, GPIO2's own 45 kΩ strap pull-down
holds it low at reset and ELRS drives it low at init; active discharge when
off; COUT 4.7 µF 0402, BR-26; in HD mode its input collapses with
`+3V3_VTX`, §4.8 HD gate).
The SE5004L needs VREF 2.80-2.90 V at IEN about 10 mA (abs max 3.6 V, V); the
±2 % reference spans 2.79-2.91 V, just outside that window at both corners, so V5
qualifies Icq and gain at 2.79 V and 2.91 V on a lab supply and records VREF per
board (no tighter 2.85 V grade of the part was found); a GPIO through a series
resistor cannot hold that (ESP32 driver ≤ 16.5 Ω at 40 mA, default drive about
25-45 Ω, so ±0.1 V or more at 10 mA, and ELRS has no drive-strength key), so the
reference is the baseline. VREF and Icq are measured in V5; Icq versus a lower
VREF (2.0-2.85 V on a lab supply) is bench item 2 for heat lever (a) (§5.4). The
logic-EN PAs of the shared footprint (QPA9501, TQP5525) accept the 2.85 V level.
Detector: PA DET → 1 kΩ / 100 pF → ESP32 GPIO4 (ADC2). ELRS reads it with
`analogRead()` (raw counts, default 11 dB attenuation, range to about 3 V, no
eFuse calibration; the "max 1.0 V" comment in the code is stale; V,
devVTXSPI.cpp l. 291). SE5004L DET runs 0.325 V (no RF) to 1.0 V (27 dBm),
typical values only; its ±0.5 dB is accuracy versus frequency for one part, not
between units, and the ESP32 ADC reference spans 1.0-1.2 V (about ±9 % in counts:
±30-35 mV on a 0.35-0.4 V reading). At 14 dBm the detector rises only tens of mV
above its 0.325 V floor, inside that error, so the 25 mW unit spread is measured
and published (V5) rather than claimed; 100 mW holds ±3 dB unit to unit, and
±1.5 dB needs per-unit calibration (patch 8, not gating; rank 4). PA VCC: 10 µF X6S (GRM155C80J106ME11D) shared, plus per-pin RF
decoupling (1 nF + 100 pF) at VCC pins 8/9 and 18/19/20 on both package sides,
following the Skyworks EK1 layout (six capacitors per the datasheet); no
ferrite: a 220 Ω power bead with the 10 µF resonates at 50-150 kHz, where the
ESCs put their ripple. The 3-pad selector sets PA VCC = +BATT (default) or +5V.
A 0201 NTC (Murata NCP03XH103F05RL, 10 kΩ 1 %, B 3380, −40..125 °C, C98098,
175,100) next to the PA with a Yageo RC0201FR-0710KL divider (C106225 [PU])
feeds ESP32 GPIO34 for the thermal derate (O6 gate 6).

**HD gate: one video system at a time (D17, D53 BR-03).** GPIO27 (PINIO1, the
HD line; 2.4 kΩ pull-down = analog at reset) drives the gate of an ALLPOWER
**AP1606** on the bottom (Vgs(th) 1.2 V, S; the beeper FET part), drain on the
`+3V3_VTX` LP5912 EN (that EN has a 100 kΩ pull-up to +3V3 and the
patched-ELRS GPIO21 reaches it through 1 kΩ, R84), source on GND. In HD mode
`+3V3_VTX` collapses, and with it the RTC6705, the PNP drive stage and the
LP5907 PA reference, which BR-03 moved onto that rail: PA_VREF falls to 0 V
whatever GPIO2 does (LP5907 active discharge plus the PA's 10 mA VREF load), so
no 5.8 GHz carrier is left to desense the O4 and the PA cannot sit at Icq.
Round 4's BC847QASZ (Qa on the LDO EN, Qb on the LP5907 EN), its two base
resistors and the 1 kΩ GPIO2 series resistor are deleted. At HD turn-off
PA_VREF may briefly exceed the LP5907's VIN + 0.3 V until its 4.7 µF output
drains through the PA bias (small body-diode current, I); V9 checks PA_VREF
< 0.5 V as well as +3V3_VTX < 0.5 V in HD mode. The three VTX SPI lines (CS,
CLK, DATA) carry 1 kΩ series resistors at the ESP32 so stock ELRS, which keeps
writing, cannot back-power the unpowered RTC6705 through its ESD diodes
(≤ 3 mA per line into the LP5912's active discharge, I). Firmware contract:
the HD preset (§12) sets PINIO1 high, the MSP DisplayPort on UART1 and VTX pit,
so ELRS also holds pit; no ESP32 input senses the HD line (stock ELRS has no
key for it), so the hardware hold-off is the authority. Parts: AP1606 + 4x 0201
(3 SPI series, GPIO21 series). V5 and V8 add an HD case: PA current and
+3V3_VTX current with the O4 active, and no carrier above −80 dBm EIRP on
5725-5850 MHz.

**SPI read access.** The RTC6705 SPI is 3-wire: SPIDATA is bidirectional and
read data is clocked out on SPICLK falling edges (V, datasheet §4); ELRS only
writes. The production verify step and the counterfeit screen (register 0x00 =
0x0190, §12.1, §15.3) use a small ESP32 test application loaded into RAM over
esptool, which runs the SPI in 3-wire half-duplex mode on GPIO14 (`vtx_mosi`,
D53), reading through the 1 kΩ series resistor; `vtx_miso` is -1 in the layout (D81; GPIO23 is the PICO's in-package flash DI).

**Start-up and lock range.** After reset GPIO13 is an input with its internal
pull-down on (V, ESP32 datasheet IO_MUX table: MTCK "oe=0, ie=1, wpd", about
75 µA / 45 kΩ), not floating: the ngspice run (`research/bomred/verify/pnp_spice/pnp_spice.out.txt`,
case 4, 45 kΩ pull-down) gives Ic 10-19 mA at Re 10 Ω (about 50 mW in Q27), not
the 32-59 mA top-step ceiling. It flows from reset until ELRS `initialize()` sets
the pit count (stock `vtxSPIPWM = MAX_PWM`), and for as long as the ESP32 stays
in ROM download mode (SW1 held during the §12.1 recovery, minutes), while the
RTC6705 (powered by R68) sits at its power-up default channel (5865 MHz); the
channel can stay wrong for up to 5 s at pit drive until MSP-VTX sets it; VREF is
off (GPIO2 also resets with its pull-down), so this leaks through the off PA. V5
measures that leakage at the U.FL from power-up until the channel is set and in
download mode with SW1 held. The RTC6705's Fc is 5725-5865 MHz over −40..85 °C (V), and the plan uses
5645-5945 MHz: V5 checks lock at 5645 and 5945 MHz at RTC6705 case −10 °C and
80 °C, and gate (5) gains an upper bound (or a lock check) if hot lock fails at
the top channels.

**RF pads.** On the 77 µm L1-L2 dielectric the 50 Ω line is about 0.105 mm wide
(§8.2), while the U.FL signal pad and the DC-block, match and BPF pads are much
wider: over solid L2 a U.FL centre pad is about 0.3-0.5 pF, |Γ| about 0.26-0.40
at 5.8 GHz (I). So L2 is cut out under the U.FL signal pad and under every RF pad
wider than about 0.3 mm, with GND poured on L3 under that area as the local
reference (rule area `RF_PAD_CUTOUT`), verified with the KiCad calculator or an
EM solver at P5. No DNP filter footprint on the line. RTC6705 NC pads 1, 2, 3,
4, 12, 13, 14, 15, 16, 18, 34, 36, 37 (the verified OpenOSD-X list; pin 17,
AVDD_6.5, is unconnected after BR-16 but keeps its pad, which the reference
uses) may be removed from the land if P5 needs the escape channels; the EP is
never touched.

**RTC6705 supply pins (D52 BR-15, BR-16).** REG1D8 (pin 26) gets no
capacitor, as on OpenOSD-X v1.01 (C27 "DNI"); REG1D8_1 (pin 23) keeps its
470 nF; V5 checks video SNR. Pin 17 (AVDD_6.5, the audio 6.5 MHz VCO supply)
is left unconnected like pin 13 (audio 6 MHz VCO): both OpenOSD-X v1.01
variants put only 3.3 kΩ + 1 µF to GND on it and no 3.3 V, while the
datasheet labels it "Supply IN 3.3 V", so the deviation rests on the reference
and V5 checks for no 6.5 MHz spur. Two reference details go to P4 (§15.5
P4-16): pin 40 (LDD2V5) lacks the reference's 51 Ω + 1 µF filter, and the
100 pF (C103) belongs at PAVDD/BUFVDD (pins 31/32), as in the reference.

| Part | Primary | Fallback |
|---|---|---|
| Synthesiser | RichWave **RTC6705** (or RTC6705A), QFN-40 6x6. **0 authorised stock** (LCSC 0, HQ Online 0, Digi-Key none); brokers: Win Source 30,000 at $7.82-11.73 (findchips, 2026-10-06). **Consigned with traceability (§15)** | none exists |
| 8 MHz reference | Yajingxin **TAXM8M4RDBCCT2T**, 3225, 10 pF, ±10 ppm, −40..85 °C, C400090, 169,930. D12 asked for a 2520 part, but 8 MHz is rare in 2520 (those blanks usually start at 12-16 MHz; none found on 2026-10-07), so budget v4 books the 3225; P3 searches for an exactly-8 MHz 2520 (the frequency is fixed by firmware, above) | YXC X322508MSB4SI, 3225 (S) |
| PA | Skyworks **SE5004L-R**, QFN-20 4x4, 3.0-5.5 V, 5.15-5.85 GHz, C210263, 1,339 (HQ Online 0; Digi-Key 21 wk) | Qorvo QPA9501TR13, same footprint (prototype only, 124); Skyworks SKY85743-21, LGA-24 3x5 (5 V, new footprint) |
| BPF | Walsin **RFBPF1608060K98Q1C**, 5150-5950 MHz, 1608, C2442150, 12,780 | TDK DEA165538BT-2263A1-H, C2835388, 3,975 (clips 5945 MHz) |
| U.FL | Hirose **U.FL-R-SMT-1(80)**, −40..90 °C, C88374, 65,950 [PU] | I-PEX 20279-001E-03 (S) |
| PAOUT1 choke | Murata **LQP03TN4N7H02D** 4.7 nH 0201, C86126, 148,100 | none verified |
| PA drive stage | Nexperia **BC857BM,315**, PNP 45 V / 100 mA, hFE 220-475, DFN1006-3 SOT883 (S; may reuse the AP1606-class land, P3) + 2x 1 kΩ + 2x 1 µF + Re 10-15 Ω (D52 BR-02; gate: P4 SPICE, then V5 / V8) | PS-12: round 4's Nexperia BC847QASZ two-NPN stage with corrected values (§4.8; brings back the 0.35 mm EQ) |
| HD gate (D17) | ALLPOWER **AP1606**, DFN-3L 1.0x0.6 [PU] (D53 BR-03; no resistors) + the 1 kΩ VTX SPI series resistors and the 1 kΩ GPIO21 series resistor (R84, P4 ruling) | - |
| PA reference | TI **LP5907SNX-2.85/NOPB** (§4.2) | 2.8 V variant (lever a) |
| PA NTC | Murata **NCP03XH103F05RL** + Yageo RC0201FR-0710KL | none verified |
| OSD switch | TI **SN74LVC1G3157DTBR**, X2SON-6, −40..125 °C, C2673087, 1,540 [PU] | none (TI single source in X2SON) |
| OSD sync comparator | TI **TLV7031DPWR**, X2SON-5, C2876045, 6,236 [PU] | none verified |
| OSD clamp diode | Diodes **SDM02U30LP3-7B**, DFN0603, C151629, 16,740 [PU] | none verified |

`osd` sheet reuse, changes: drop COS8051 and its 3 resistors; scale the level
divider about 5x down (top about 750-820 Ω, Thevenin about 190 Ω), keeping the
OSD_W pin at ≤ 3 mA; one shared 100 nF X6S between the SN74LVC1G3157 and the
TLV7031 (2.5 mm apart on the bottom, over an ESC quarter, hence X6S; D52
BR-13 deletes the second cap). OSD levels are absolute, so with AC-coupled cameras they
move against the picture's black level: V9 measures black and white on the
target cameras, and a sync-keyed clamp is added only if needed.

**Pit, disarm, defaults and heat** (I, 04 §6, 06 §4; V from the ELRS and
Betaflight source). PA at the 27 dBm ceiling draws about 0.65 A from the cell
(about 2.4 W at 3.7 V, 1.9 W of heat with the BPF); at 25 mW about 0.30 A (PA
quiescent dominates, 1.09 W). Stock ELRS pit drops VREF and sets the maximum PWM
count but never powers the RTC6705 down (`POWER_AMP_OFF` defined but unused), so
pit keeps the RTC6705's 0.5 W on the board and leaks its output through the off
PA (V5). Betaflight sends power index 1 whenever disarmed with
`vtx_low_power_disarm` ON (`vtx_msp.c` l. 110 at 2026.6.2: `isLowPowerDisarmed()
? 1 : power`); ELRS turns index 1 into "VPD setpoint `VPD_SETPOINT_0_MW` (= `VPD_BUFFER`), maximum count" with VREF
**on** (devVTXSPI.cpp l. 289), and forces pit only on index 2 (RCE,
devMSPVTX.cpp l. 211) while the lowPowerDisarm flag also forces index 1 at boot
(l. 217). So low-power disarm ON defeats RCE and keeps a disarmed PA biased at
about 1.0-1.1 W from power-up.

**Defaults survive the first ELRS session only with this flow** (§12.1).
Betaflight ships no vtxtable; on the first ELRS session `devMSPVTX` finds a
mismatch and runs `clearVtxTable()`, which sends `MSP_SET_VTX_CONFIG` with
power 3 (25 mW), pitmode 0 and lowPowerDisarm 0 and then writes EEPROM;
Betaflight applies all three (msp.c l. 3829-3842; V, both sources). Production
therefore flashes ELRS, saves the UART0 RX_SERIAL + VTX_MSP mask first (without
it Betaflight 2026.6.2 sends no MSP-VTX replies over CRSF and ELRS gives up after
5 s), boots ELRS once with the FC so it writes its vtxtable, then applies the CLI
defaults and saves (alternatively the shipped diff carries
the exact ELRS vtxtable: 6 bands x 8 channels, 5 levels with values 1, 2, 14,
20, 26 and labels `0`, `RCE`, `25`, `100`, `400`, so the check matches and
nothing is cleared). **Defaults until ELRS patch (3) merges: vtx power 2 (RCE)
and `vtx_low_power_disarm` OFF**, so RCE forces pit at every boot through
`SET_RCE_PIT_MODE`; the README tells the user to re-enable pit after landing.
Once patch (3) treats index 1 as pit, low-power disarm returns to ON. V8 checks
the PA current at power-up after the production flow. Release requirements
(O6): index 1 handled as pit; pit and disarm power the RTC6705 down (GPIO21, VTX
SPI tri-stated, frequency re-sent) or write `POWER_AMP_OFF`; a thermal derate
from the PA NTC. "Max" is continuous only at high airflow (hover needs
h ≥ 63-82 W/m²K, §4.3) and time-limited otherwise (τ 26-69 s).

### 4.9 Blackbox

| Option | Body | Stock | Verdict |
|---|---|---|---|
| **Puya PY25Q128HA-DFH-IR**, USON-8 3x3x0.55, on SPI0 (D66) | 9 mm² | no distributor listing found (2026-10-10); the MPN is in the Puya DS Rev 2.0 ordering table, NextPCB sources it by MPN (D60); the quote must confirm it (§15.3) | **chosen** (smallest 16 MB SPI NOR with a published drawing; Matrix uses the same family) |
| PY25Q128HA-QVH-IR / GD25Q128EQIGR, USON-8 4x4 | 16 mm² | GD25Q128EQIGR C84018 | fallback, needs a 4x4 land and a placement change |
| W25Q128JVPIM, WSON-8 6x5 | 30 mm² | C2441427 | superseded by D66 (area) |
| 8 MB (W25Q64JV class) in a smaller package | - | - | §9.3 lever (Matrix has 16 MB) |
| NOR on the RP2354A QSPI bus, CS1 | 1 GPIO instead of 4 | - | no: flight-unvalidated driver, XIP stall risk (05 §1.2) |

The PY25Q128HA-DFH-IR is an "I" grade part (−40..85 °C, V, Puya DS Rev 2.0), one
of the 85 °C parts; JEDEC ID 85 20 18 is in Betaflight's m25p16 table (D66). Its
pad 9 is two exposed tie-bar tabs with no electrical function in the DS: no net,
no-connect flag, no vias in the tabs (blackbox sheet). Placed on SPI0 next to the
RP2354A, ≥ 3 mm from the RX antenna hole (floorplan v3). SPI0
runs at 75 MHz for writes and reads (clk_peri 150 MHz / 2: Betaflight's PICO SPI divider uses an even
prescale ≥ 2, so the table's 80 MHz read clock also gives 75 MHz; harmonics at 2400 and 2475 MHz, in the
ELRS band); the PY25Q128HA tCLQV of 6-7 ns against the 6.67 ns SCK half period leaves no read margin on
paper, so F7 / V9 read back and CRC a full log (fallback: a lower read clock for this JEDEC ID, upstreamed), so the NOR and its bus stay ≥ 3 mm from the antenna hole and
are a listed aggressor (§10); V7 measures desense with the blackbox writing.
`blackbox` sheet keeps its name, bus (SPI0, GPIO18-21) and CS pull-up; microSD
removed.

### 4.10 Connectors and pads

| Item | Decision | Part / geometry | Why |
|---|---|---|---|
| Battery | BT2.0 pigtail (22 AWG, 40 mm, user-fitted), two plated holes **Ø 1.1 mm finished** in 3.0 x 2.0 mm pads (long side along the edge), both sides, ≥ 12 power vias (0.40/0.20) per pad into the pours | no PCBA part | a wire through a PTH cannot peel the pad; Ø 1.1 keeps ≥ 1.025 mm for stranded 22 AWG with the ±0.075 mm PTH tolerance. The board check runs with `--min-hole 2.0` |
| Motors | 12 solder pads 1.0 x 1.8 mm on the top, each with a plated **Ø 0.5 mm wire-anchor hole** near the outer end, pitch 1.5 mm, at the board edge facing each motor | no PCBA part | Matrix "solder-required" equivalent. A 1.25 mm THT plug does not fit the fab-rule intersection (pitch ≥ 1.30 mm), and four SMD PicoBlade headers cost 173-212 mm² |
| USB | **JST SH 1.0 vertical BM04B-SRSS-TB(LF)(SN)** (J31, D57 / D76): 1 GND, 2 D−, 3 D+, 4 VBUS (BetaFPV 'USB(GND DM DP 5V)' order; pin 1 orientation gated by V0-USB), facing up next to a mounting hole, mating zone above the board clear of tall parts | SGM40661 OVP (U24) + TPD2EUSB30 ESD (D7) on the board | replaces the D18 pogo pads and clip-on adapter (O3 closed) |
| Camera | **CAM 5V GND pads** (1.2 x 1.0 mm, long side across the edge), top, right edge front between tab T1 and the ESC2 phase strip (sketch v5; D18 cut 1: no SH1.0 plug) | no PCBA part | the plug cost 38.3 mm² top; the camera lead is soldered like the motors |
| VTX antenna | U.FL, top, front edge left of the arc (sketch v4) | §4.8 | |
| RX antenna | plated hole Ø 0.5 mm at the left edge, rear half, **(−12.3, +6.5)**; insulated λ/4 wire **trimmed to resonance** (about 28-29 mm for a jacketed wire, velocity factor 0.90-0.95; 30.7 mm only in free space), set by return loss in V7 | - | Matrix uses the same. At its root the wire is only about 9 mm (edge to edge) from the nearest M3 pad (left edge, y −7…−3), so it is routed rearward along the rear arm or up the canopy, away from the motor leads and the pigtail; the hole pad edge is 5.7 mm from the battery pads, and no pad group sits within 6 mm of it (sketch v4) |
| User and HD pads | 14 pads with 0.8 mm labels, every pad ≥ 0.5 mm from every part (iron rework): **TP0 RP0 5V GND** (PIOUART0 user UART, D16; also the LED-strip 5V/GND, 1.0 x 1.2 mm): **site open (O20)**, no compliant top site at real size (sketch v5); **LED BZ+ BZ-** (1.0 x 1.0 mm, 1.3 mm pitch) at the rear edge between B- and the M1 pads; **CAM 5V GND** at the right edge front; **VHD GND TX1 RX1** (DJI O4 Lite, D13/D16; 1.2 x 1.0 mm at 1.3 mm pitch) in a column at the rear centre ("HD" frame), the O4 switch in the left-centre region | - | Matrix II parity plus the O4. D14 pad trimming: the LED group shares the user 5V/GND (two pads fewer). No SBUS pad (D16): a DJI remote's SBUS goes to RP0, inverted in Betaflight. Pad-to-wire map for the cut DJI cable: red → VHD, black + brown → GND, white → TX1, grey → RX1, yellow → unconnected |
| Test points | FCB (RP2354 QSPI_SS), CLK / DIO (FC SWD), 8x C2D/C2CK (ESC): mask-open 0.35/0.20 filled-via test points, no silk, listed in the pinout (D67); the RXB and GND pads are removed | via, bottom | boot straps by the shared button SW1 (D65); the C2 vias are the bench recovery contacts, NextPCB pre-programs the EFM8s (§12.1) |

---

## 5. Power budget

### 5.1 +5V rail loads (design)

| Load | Analog mode, A at 5 V | HD mode (O4, D17), A at 5 V | Note |
|---|---|---|---|
| Camera | 0.12 | 0 | allowance (BetaFPV C03: 100 mA at 5 V, V); in HD mode the O4 camera is on its own coax |
| +3V3 (one LP5912 for FC + RX: RP2354A, NOR, OSD front end, LEDs, INA186, gyro via +1V8, ESP32-PICO-V3, SX1281, RGB LED) | 0.20 | 0.20 | I (FC 0.09 conservative, RX 0.11 with 0.16 peak; measured in V8). The PA reference moved to +3V3_VTX (D53 BR-03); its 0.01 A stays inside this conservative figure |
| +3V3_VTX (RTC6705, PNP drive stage, PA reference) | 0.10 (about 0.17 at the top PA step) | 0 | 95 mA RTC6705 datasheet figure (13 dBm mode) as the typical; at the top PA step the PNP PAOUT1 feed adds 32-66 mA (SPICE, VTX sheet) and the SE5004L VREF about 10 mA through U22: about 0.17 A, inside the LP5912 500 mA. Held off in HD mode |
| O4 Lite on +5V_HD | 0 | 1.20 | S: 0.98 A at 25 mW, 1.20 A at 700 mW, 0.60 A in low-power mode (one reviewer; DJI publishes no current, only 3.7-13.2 V and "BEC ≥ 10 W") |
| LED strip | 0.20 | not budgeted | user allowance; in HD mode the README limits the strip (with it, see total) |
| Buzzer | 0.03 | 0.03 | |
| User 5 V pads | 0.05 | not budgeted | allowance |
| **Total** | **0.70 A (3.6 W)** | **1.43 A (7.4 W), 1.48 A at the RX peak** | analog: 0.42 A without the user allowances, 1.25 A if the PA is moved to +5V; HD with the LED-strip and user allowances 1.73-1.78 A; USB only: 0.42 A with the camera (the O4 is off on USB) |

Rail split (D53 BR-10): the O4 sits on `+5V_BST` ahead of the TPS2116 mux, so
the HD total above is the boost (`+5V_BST`) load; `+5V` itself carries 0.70 A in
analog mode and about 0.25 A in HD mode (root power table).

### 5.2 Every load from the cell, at 3.0 V and 4.35 V

| Load | at 3.0 V in | at 4.35 V in | Basis |
|---|---|---|---|
| Boost input for 0.70 A at 5.15 V | 1.37 A (η 0.88) | 0.90 A (η 0.92) | TPS61022 efficiency curves (S) |
| Boost input for the HD load (1.48 A) | 2.95 A (η 0.86) | 1.95 A (η 0.90) | same (I) |
| SE5004L PA, pit / 25 / 100 mW / max (27 dBm ceiling) | 0 / 0.30 / 0.35 / 0.65 A | same | I (Icq 300 mA spec, 04 §6.1; ceiling at about 30 % PAE); out of rating below 3.0 V; 0 in HD mode |
| 4x EFM8BB51 at 49 MHz | 0.020 A | 0.020 A | V (55.5 µA/MHz), I (peripherals) |
| **Cell current (no motors), VTX pit** | **1.39 A / 4.17 W** | **0.92 A / 4.01 W** | |
| VTX 25 mW | 1.69 A / 5.07 W | 1.22 A / 5.31 W | |
| **VTX max (ceiling)** | **2.04 A / 6.12 W** | **1.57 A / 6.83 W** | |
| **HD mode (O4 at 700 mW)** | **2.97 A / 8.91 W** | **1.97 A / 8.57 W** | |
| ESC per motor at hover / 6 A / 12 A | 0.09 / 1.93 / 7.23 W of loss on the board | same | §4.3 |

### 5.3 5 V margin (P0 gate)

TPS61022 with 0.68 µH (Isat 6.5 A), 1 MHz, per TI SLVSDX7D §8.2.2.2
(inductance −30 % = 0.48 µH, peak held to 80 % of Isat; η read conservatively
from TI's typical curves at 1.5-2 A: 0.85 at 2.8 V, 0.86 at 3.0 V, 0.87 at
3.2 V; I). At 3.0 V in: D = 0.50, ripple 3.15 A → **1.82 A** nominal peak; at
2.8 V **1.67 A**; at 3.2 V **1.98 A**; with nominal inductance about 2.0 A at
3.0 V. These are the only BEC figures in §1, §4.2 and COMPETITION §8 (round 2's
1.83 / 1.96 A came from η 0.90).

| Load | at 2.8 V | at 3.0 V | at 3.2 V |
|---|---|---|---|
| Analog 0.70 A | +139 % | **+160 %** | +183 % |
| PA moved to +5V, 1.25 A | +34 % | +46 % | +58 % |
| HD 1.43-1.48 A (as budgeted) | +13-17 % (the O4 is shed at 2.74-3.14 V before this) | **+23-27 %** | +34-38 % |
| HD with the LED-strip and user allowances, 1.73 A | −3 % | +5 % | +14 % |

Gate "≥ 20 % margin at 3.0 V on datasheet curves": **pass** for the analog load
and for the HD load as budgeted; the README limits the LED strip in HD mode.
**Published BEC (D79): 1.5 A continuous.** Above 1.5 A the TPS61022 needs
≥ 20 µF effective COUT (DS 6.3: ≥ 10 µF up to 1.5 A, ≥ 20 µF for 1.5-3 A); the
four GRM188C80J226ME15D give 20-28 µF typical at 5.15 V and fall below 20 µF at
−20 % tolerance and hot. The HD budget (1.43-1.48 A) stays under 1.5 A; the
1.73-1.78 A "HD with LED strip and user allowances" case is outside the published
rating (README limits the strip in HD mode); V1b runs a 1.7 A load step as
characterisation only.
Limits that keep it a calculation: Cout (≥ 20 µF effective above 1.5 A: four X6S
0603 give about 20-28 µF at 5.15 V, D15), inductor ripple above TI's 40 %
guidance, saturation in overload (§4.2), the mux drop (§4.2), and heat: the
binding limit is TJ ≤ 125 °C (V §6.3). At the HD load from 3.0 V the loss is
about 1.2-1.3 W, 1.0-1.1 W of it in the IC, +37-40 K by ΨJB 36.7 K/W (V): TJ
85-99 °C in HD hover (board 48-59 °C at h 80-55), 125 °C only on an 85-88 °C
local board. The ≥ 2 mm boost-to-FET distance (H2) is a D69 preference only: where
placement puts U2 / L1 closer to a FET group, a loaded ESC channel adds its quarter
rise to that local board temperature, and V1 (BEC with one ESC channel at 4 A,
case temperature logged) is the check. The published figure is the V1 table of continuous current per
VIN and board temperature, for both modes.

### 5.4 Thermal budget (on-board heat) and heat levers

Each bench column names the firmware and defaults it assumes (§4.8).

| Source | Hover, VTX max (27 dBm ceiling), 3.7 V | Hover, VTX 25 mW | Hover, HD mode (O4 at 1.2 A) | Bench, disarmed, RCE pit (production defaults, stock ELRS) | Bench, disarmed, VREF on (stock ELRS with low-power disarm ON, or after leaving pit) | Bench, pit, RTC6705 off (patched ELRS) | USB only |
|---|---|---|---|---|---|---|---|
| PA (+ BPF) | 1.90 W | 1.09 W | 0 | 0 | 1.0-1.1 (Icq) | 0 | 0 |
| RTC6705 + its LDO | 0.50 | 0.50 | 0 | 0.50 | 0.50 | about 0 | 0.50 |
| +3V3 rail, FC + RX (LDO + loads; PA reference counted here although BR-03 moved it to +3V3_VTX) | 1.00 | 1.00 | 0.97 | 0.97 | 1.00 | 0.97 | 0.97 |
| Boost loss + mux (+ O4 switch in HD) | 0.39 | 0.39 | 1.16 | 0.26 | 0.26 | 0.26 | 0.01 |
| ESC MCUs | 0.07 | 0.07 | 0.07 | 0.07 | 0.07 | 0.07 | 0 |
| ESC FETs (1 A/motor) | 0.36 | 0.36 | 0.36 | 0 | 0 | 0 | 0 |
| Shunt + copper | 0.05 | 0.05 | 0.05 | 0 | 0 | 0 | 0 |
| **Total** | **4.2 W** | **3.4 W** | **2.6 W** | **1.8 W** | **2.8-2.9 W** | **1.3 W** | **1.5 W** |
| Board rise (flight G 0.042-0.11 W/K; bench still air 0.025-0.035 W/K) | +38-100 K | +31-81 K | +24-62 K | +51-72 K | +80-116 K | +37-52 K | +43-60 K |

At 25 °C ambient the 85 °C parts allow +60 K and the PA case adds its local
6-12 K/W: hover needs h ≥ 46-53 W/m²K at 25 mW, 63-82 at max and 31 in HD mode.
The O4's own 3-6 W in the canopy a few millimetres above the board is not in
these numbers (V8 HD hover). On the bench in still air only the patched pit case
stays clearly inside and the RCE-pit case is marginal; until the ELRS patch is
merged the README requires a bench fan or short sessions. Camera, LED strip and
buzzer power is dissipated off the board. Time constant in flight about 26-69 s
(C about 2.9 J/K).

The continuous rating is set by about 3.0 W of non-ESC heat, not by the FET
path, so the heat levers carry more rating than the FET choice. **Decision gate
before P2:** (b) is decided on area before P2 (rejected for rev1 unless P2
frees ≥ 20 mm² on the bottom); (a) and (c) are measured on the first boards or
an SE5004L/RTC6705 bench setup (V5, V8) and adopted if they pass; the published
rating states which levers are in.

| Lever (`thermal_v3.py`, h 55, 25 mW, k_PA 12-6 K/W) | Heat | One channel / all four | Cost, status |
|---|---|---|---|
| none (baseline) | - | 0-1.4 A / 1.2-1.8 A | - |
| (a) PA bias: lower fixed VREF (Icq 300 → about 150 mA). VREF below 2.80 V is outside the datasheet window: gain and stability qualified in V5 before a 2.8 V or lower reference variant is fitted. No lower-Iq PA exists on the footprint at 1S | −0.55 W | 3.4-3.7 A / 2.4-2.5 A | bench item 2 |
| (b) 3.6 V buck-boost for the 3.3 V loads | −0.45 W | 1.2-3.1 A / 1.8-2.3 A | +15-20 mm² bottom; not in rev1 unless P2 frees it |
| (c) RTC6705 PAOUT1-only current (60 mA assumed instead of 95) | −0.17 W | 0-2.2 A / 1.4-2.0 A | measure (V8) |
| (d) 0.68 µH boost inductor | −0.04 W | 0-1.6 A / 1.3-1.9 A | **adopted** (§4.2) |
| (a)+(b)+(c)+(d) | −1.21 W | 4.7 A / 2.9-3.0 A | hover then needs h ≥ 29-30 |

---

## 6. Weight (detail of §1)

| Item | Estimate |
|---|---|
| PCB 6L 1.0 mm, 6.97 cm²: dielectric 1.07-1.17 g; copper outer 1 oz at 60 % (+ Type VII cap plating), L2/L4/L5 0.5 oz at 85 %, L3 0.5 oz at 40 %: 0.59-0.70 g; mask 0.03 g | 1.70-1.90 g |
| FETs 24x SON 2x2 (about 10 mg each, I) | 0.24 g |
| ICs, crystals, inductors | 0.60-0.70 g |
| Passives (about 185 after D52; the round-4 figure for 235 kept as margin) | 0.06-0.08 g |
| Connectors (U.FL only; camera on pads, USB on pogo pads) | 0.03 g |
| Solder | 0.12 g |
| **Total** | **2.75-3.07 g, about 2.8-3.1 g** (target ≤ 3.5 g, margin 0.4-0.7 g) |

Maker part weights replace the estimates in P3; V11 is the gate. 1 oz inner
copper would add about 0.3 g; 0.8 mm board would save about 0.26 g but BetaFPV
moved from 0.8 to 1.0 mm for crash survival, so 1.0 mm stays.

---

## 7. Mechanical outline (exact geometry for P1)

KiCad coordinates in mm, board body centred at (113.2, 113.2) so the body spans
100.0-126.4 on both axes. Relative to the centre:

| Feature | Geometry |
|---|---|
| Body | square ±13.2 |
| Front corner (+x, −y) | arc R 5.8, centre (+7.4, −7.4), tangent to the top and right edges; no ear |
| Ears | circles R 2.4 centred on the holes, unioned with the body; concave junctions filleted R 0.5 |
| Holes | Ø 3.5 Edge.Cuts circles (non-plated cut-outs) at (−12.875, −12.875) left, (−12.875, +12.875) rear, (+12.875, +12.875) right; plated with a GND annulus is the P2 candidate (O16) |
| Bounding box | ±15.275 → absolute 97.925-128.475 on both axes, 30.55 x 30.55 |
| Area net of holes | 696.6 mm² (grid estimate, ±3 mm² for fillets) |
| Copper keepout | 0.20 from every edge and hole (copper-to-edge rule) |
| Part keepout | 0.30 band inside the outline; Ø 5.2 grommet flange at each hole, both sides (rule areas `MOUNT_*`) |
| Panel tabs | 3 tabs, 1.2-1.5 mm wide with mouse bites, each with a part keepout on both sides (rule areas `TAB_*`, `setup_board.tab_rect()`: 1.5 mm each way along the edge, 1.3 mm inward from the edge, i.e. 1.0 mm beyond the 0.3 mm edge band; MLCC crack risk): **T1 right edge at y −6.6** (between the PA's VCC ring and the CAM pads; round 4 moved it off the front arc, where the SE5004L land and its right VCC ring sat inside the keepout at every arc position), T3 left edge y −8.9 (between the left flange and the M3 pads), T4 rear edge x −9.3 (between the rear flange and the B+ pad; the 22 µF pad bulk, which sits across +BATT_IN and GND with no fuse, moved 1.0 mm inboard to 2.1 mm from the edge with its long axes parallel to it, so a depanel crack cannot short the battery). The round-2 T2 on the top edge is dropped: the M4 pads moved left with ESC4 and the pogo USB pads take the rest of that edge (a clip-on adapter needs a clean edge). `sketch_v5.py` checks all three keepouts against every part, pad group and pad (0 fails) and the P2 placement script must keep them as hard checks; `setup_board.py` still writes T1 on the arc and takes the new position at the next P1 re-apply; final positions with the P2 placement and the NextPCB panel EQ |
| Panel | ≥ 70 x 70 mm with **rail fiducials only** (JLCPCB Standard PCBA minimum for a single design, capability page 2026-10-07); no fiducials in the board file (LINEUP B16: the panel is its own project). The EQ asks NextPCB and JLC whether rail fiducials suffice for 0201 and 0.35 mm pitch; if local fiducials are needed, that is a lineup exception for the owner and their area (about 8-12 mm² per side) is booked |
| Guides | 25.5 and 26.0 mm frame patterns drawn on `User.Eco1`; front marked on `User.Eco2` |

---

## 8. Stackup and fab rules

**Owner rule: through vias only.** Filled-and-capped via-in-pad (IPC-4761 Type
VII, non-conductive epoxy) is a through via and is used in every pad that holds
a via. No blind, buried or laser vias. The via is the OpenDrone standard
**0.35/0.20** (D6: owner-confirmed buildable at NextPCB).

### 8.1 DFM intersection (NextPCB ∩ JLCPCB)

NextPCB values: track 07 (S1 standard capabilities, S2/S3 advanced and HDI pages,
S4 assembly, S12 stackup library, verified 2026-10-06), re-read on the current
capability page https://www.nextpcb.com/pcb-capabilities on 2026-10-07 (round-3
review: 1 oz annular ring 3.5 mil, same-net hole to hole 8 mil, different-net
12 mil, mask dam 3.5 mil, silk 30 / 24 mil, as below; V). JLCPCB values:
capabilities page read 2026-10-07 (https://jlcpcb.com/capabilities/pcb-capabilities).

| Rule | NextPCB | JLCPCB | **This board** |
|---|---|---|---|
| Min track / space, 1 oz outer | 0.08 / 0.08 mm | 0.09 / 0.09 mm | **0.09 / 0.09** (re-checked at the finished outer copper with Type VII cap plating, EQ) |
| Min track / space, 0.5 oz inner | 0.065 / 0.08 mm | 0.09 / 0.09 mm | **0.09 / 0.09** |
| Min mechanical drill | 0.15 mm (boards ≤ 1.2 mm) | 0.15 mm | **0.20** (the DRC minimum enforces the standard via) |
| Via annular ring | 0.09 / 0.10; owner: 0.35/0.20 builds (D6) | via dia ≥ hole + 0.10 | **0.075 → via 0.35 / 0.20** (D6) |
| PTH (component) annular ring | 0.20 | 0.15 abs min, 0.20 recommended | **0.20** |
| Hole to hole, same net | 0.20 | 0.20 | **0.20** |
| Hole to hole, different nets (vias) | 0.30 (CAF) | 0.20 | **0.30** |
| Pad-hole to pad-hole (PTH pads) | copper 0.40 | 0.45 hole to hole | **0.45 hole edge, 0.40 copper** |
| Via hole to track | 0.18 | 0.20 | **0.20** |
| PTH hole to track | 0.23 | 0.28 | **0.28** |
| NPTH to track | 0.20 | 0.20 | **0.20** |
| Inner-layer via hole to copper | (0.18) | 0.20 | **0.20** |
| Inner-layer PTH hole to copper | - | 0.30 | **0.30** |
| SMD pad to pad, different nets | 0.15 | 0.15 | **0.15** |
| SMD pad to track | 0.10 | 0.10, and ≥ 0.09 from a mask opening | **0.13** |
| Fine-pitch IC | 0.38 mm pitch for fine-pitch ICs, and 0.25 mm for BGA / LGA / QFN (V, assembly capability page, re-read 2026-10-07: which one applies to leadless parts is not stated) | 0.35 mm (PCBA floor) | **0.38**; after D52 / D53 no 0.35 mm-pitch part is on the BOM (ESP32-PICO-V3 at 0.5 mm, BR-01; the 74LVC1T45GS and both BC847QASZ deleted, BR-02 to BR-04), so the O15 EQ and the ganged-mask exception are dropped. On the BR-01 fallback the ESP32-D0WD-V3 QFN-48 alone needs them (one NextPCB EQ approval, scoped exception); on the BR-02 fallback (PS-12) the BC847QASZ joins it, with BC847BV (0.5 mm) as its fallback |
| Copper to routed edge | 0.20 | 0.20 | **0.20** (components 0.30) |
| Mask expansion | ≥ 0.04 | 1:1 allowed (LDI) | **0.04** |
| Mask bridge, green | 0.089 | 0.10 | **0.10**; at 0.35 mm pitch the web falls below it (about 0.07 mm), so ganged openings on 0.35 mm-pitch leadless lands, needed only on the BR-01 / BR-02 fallbacks (ESP32-D0WD-V3 sides, BC847QASZ; D53) |
| Silk line / text height | screen 0.127 / 0.76; inkjet 0.08 / 0.61; 1.07 mm text at 2 oz finished copper | 0.15 / 1.0 | **0.13 / 0.8** (D12, commons standard; meets NextPCB at 1 oz and LINEUP B11; below JLC's published legibility floor, so JLC silk legibility is not guaranteed: the one recorded exception to the owner rule "DFM-compatible with both fabs", which D12 alone cannot waive: owner sign-off for this board is pending, O11. It also deviates from LINEUP B7's 1.2 mm front / 1.0 mm back pad-label size, recorded here. Type VII cap plating can push the finished outer copper past 1 oz, where NextPCB's floor rises towards 1.07 mm: EQ item) |
| Pad to silk | 0.15 | 0.15 | **0.15** |
| NPTH min | 0.40 | 0.50 | **0.50** |
| Plated slot min | 0.50 | 0.35 | **0.50** |
| Thickness options, 6L | 1.0 ± 0.1 mm | same | **1.0 ± 0.1** |
| Copper | outer 1/2 oz, inner 0.5/1/2 oz | same | **1 oz outer, 0.5 oz inner** |
| Via-in-pad | non-conductive fill + cap, Type VII, +$12.55 per 10 pcs, +4 days | epoxy filled & capped, default for 6L and up | **Type VII on every via in a pad**; cap plating can add 10-20 µm to the outer copper (EQ, O4) |
| Impedance tolerance | ±10 % | ±10 % | **50 Ω ± 10 %** |
| Assembly spacing | 0201 0.20-0.25 mm, 0402 0.25-0.30 mm | no published rule | **0.20 body/land, 0.25 between two 0402** |

### 8.2 Stackup

6 layers, 1.0 mm, from the NextPCB library entry `6L-1.0mm-0.5oz-1080` (V,
track 07 §1.4). The JLC equivalent and the RF width are confirmed with the JLC
stackup selector (EQ item, O4).

| Layer | Thickness | Role |
|---|---|---|
| F.Mask | 0.015 | green |
| **L1 F.Cu** | 0.035 (1 oz finished) | top parts (VTX, P-FETs, EFM8s, NOR, gyro, O4 switch, pads), 5.8 GHz CPWG, video, VTX control, phase pours, local +5V/+3V3 pours |
| prepreg 1080 | 0.077 | εr 4.2 |
| **L2 In1.Cu** | 0.0175 | **solid GND** (RF and top-side reference, ESC return); cut only under wide RF pads (§4.8) |
| core | 0.30 | |
| **L3 In2.Cu** | 0.0175 | digital signals between the sides; references L4 (0.103 mm away) about three times more than L2 |
| prepreg 2313 | 0.103 | |
| **L4 In3.Cu** | 0.0175 | **+BATT plane** (ESC feed), one solid pour under every L3 route |
| core | 0.30 | |
| **L5 In4.Cu** | 0.0175 | **solid GND** (bottom-side reference, ESC return) |
| prepreg 1080 | 0.077 | |
| **L6 B.Cu** | 0.035 | bottom parts (FC, RX, power, N-FETs, OSD front end, HD gate), 2.4 GHz feed, Kelvin pair, pogo USB pads, local +5V/+3V3 pours |
| B.Mask | 0.015 | green |

Dielectric + copper = 0.997 mm; KiCad's sum including both masks is 1.027 mm
(the figure `board_spec.json` checks). Layer roles follow LINEUP B1. The thin
prepreg sits between L3 and L4, so: L4 stays an unbroken +BATT pour wherever L3
routes; the +5V/+3V3 distribution is local pours on L1/L6; **video, gyro SPI,
analog sense, VTX control and the FET gate nets never route on L3** (they go on
L1 over L2 or L6 over L5; N gates on L6 over L5 after their via). About 74 % of
an L3 trace's return flows on L4 (I), so **an L3 route may change layer only
within 2 mm of an existing +BATT decoupling capacitor** (ESC clusters, PA, boost
input, pad bulk) next to a GND via: no extra capacitors, checked at P5 review.
DRU encoding in §8.4. Finish ENIG, green mask, white legend, vias tented both
sides except Type VII in pads.

Impedance (P1 field solver, `hardware/tools/impedance.json`): 50 Ω CPWG on L1
over L2 with a 0.15 mm gap and mask = **0.105 mm** (49.6 Ω at εr 4.2, 50.9 Ω at
3.91) at 35 µm outer copper. Type VII cap plating can raise the finished outer
copper to about 45-55 µm, which lowers Z0 by about 1-2 Ω and may raise a fab's
minimum track/space: the EQ asks both fabs for the finished thickness and the
field solver is re-run with it before P5. 2.4 GHz feed on L6 over L5 has the
same geometry. USB FS: nets `USB_D_P` / `USB_D_N`, 0.12 / 0.12 mm pair,
length-matched, not impedance-critical at 12 Mb/s.

### 8.3 Vias

| Preset | Size | Use |
|---|---|---|
| Signal | 0.35 / 0.20 mm (annular 0.075) | default; every via in a pad (Type VII): the +BATT vias in the P source lands, the phase-via landings in the N drain lands, the GND vias in the N source strips, the P gate vias in pin 3, EP arrays, 0201 decoupling vias |
| Power | 0.40 / 0.20 mm (annular 0.10) | +BATT, GND and phase arrays outside pads |

0.20 mm via in 1.0 mm board: aspect ratio 5:1, about 1.4 mΩ each. Counts: ≥ 12
power vias per battery pad (25 A); per phase (§4.3) 4 +BATT vias in the P source
land, 8 phase vias in the top phase pour outside the P land (landing in the N
drain land), 3 GND vias in the N source strip, 1 leg-cap via, 2 P-gate vias; 9 in
the PA EP, 4-9 in each QFN EP. Array pitch ≥ 0.40 mm. Remove unused inner annular
rings.

**Vias in 0201 pads.** A 0.35 mm via pad is wider than a 0201 pad (about
0.30 mm): the via sits centred with the drill fully inside the pad, the
annulus overhang under mask (mask-defined pad), and both pads of a decoupling
capacitor carry their via (power and GND) so the two joints see equal copper;
where only one pad goes to a plane, the other gets matching copper, or the via
moves just outside the pad (and into the via allowance).

### 8.4 Board setup values (P1, applied by `setup_board.py`)

Constraints: clearance 0.09, track 0.09, connection 0.09, via 0.35 / 0.20,
annular 0.075, minimum through hole 0.20, hole-to-hole 0.20, hole clearance 0.20,
copper-to-edge 0.20, microvia minimums left at the template values (0.20 / 0.10)
and microvias, blind and buried vias disallowed by a custom rule; solder mask
expansion 0.04, mask minimum web 0.10; silk minimum text 0.8 mm / 0.13 mm line
(D12). Track presets 0.10, 0.105 (RF), 0.14, 0.20, 0.30, 0.50, 1.00.

Net classes (names after OpenAIO; colours set through netclass directive labels). The board takes each
net's class from the .kicad_pro patterns only (`setup_board.py` NETCLASS_PATTERNS; `sync_pcb.py` carries no
directive labels), so every directive label has a matching pattern; `check_netlist.py` N6 fails on any net
whose netlist class differs from its pattern class (P4 critique round 2: PA_VCC and U2_SW were Default on
the board):

| Class | Nets | Track | Clearance | Via | Colour |
|---|---|---|---|---|---|
| Default | signals | 0.09 | 0.09 | 0.35/0.20 | - |
| VBAT | +BATT_IN, +BATT | 0.50 (pours) | 0.15 | 0.40/0.20 | red |
| Phase | 12 motor phase nets (in-sheet `PHASE_A/B/C`) and the boost switch node `/POWER/U2_SW` (2.8-3.4 A average, about 4.5 A peak; a short pour from U2 SW to L1, D33) | 0.50 (pours) | 0.15 | 0.40/0.20 | orange |
| Gate | 24 FET gate nets (in-sheet `A_COM`, `A_PWM`, ...) | 0.15 | 0.10 | 0.35/0.20 | yellow |
| Power | +5V, +5V_BST, +5V_USB, +5V_HD, +3V3, +3V3_VTX, +1V8, +1V1, VBUS, `/VTX/PA_VCC` (SE5004L VCC, 0.65-0.8 A) | 0.25 (+5V_BST and +5V_HD 0.50 or pours: 1.5-3 A) | 0.09 | 0.35/0.20 | magenta |
| Analog | video, OSD level/sync, VBAT/current sense, Kelvin pair `SHUNT_SENSE_P/N`, PA detector | 0.10 | 0.15 | 0.35/0.20 | cyan |
| RF | `RF_*` nets: 5.8 GHz chain, 2.4 GHz feed (`RF_WIFI` -> R88 -> AE2 chip antenna, D58; was a 51 Ω dummy load) | 0.105 | 0.15 | 0.35/0.20 (fence) | green |
| USB | USB_D_P / USB_D_N | 0.12 (pair gap 0.12) | 0.12 | 0.35/0.20 | blue |
| GND | GND | 0.20 | 0.09 | 0.40/0.20 | - |

Power net names per the lineup decision and LINEUP A11: +BATT, +5V, +3V3, +1V8,
GND, with suffixed rails +BATT_IN, +5V_BST, +5V_USB (the template name; `VBUS`
would fail A11), +5V_HD, +3V3_VTX, +1V1 (+3V3_RX is gone: FC and RX share +3V3,
D14).

Custom rules below the template marker (generated by `setup_board.py`, the
last matching rule wins in KiCad 10.0.6): different-net hole to hole 0.30; PTH
pad hole to hole 0.45; PTH pad copper 0.40; PTH annular 0.20; PTH hole clearance
0.28; inner-layer PTH hole to copper 0.30; NPTH ≥ 0.50; SMD pad to track and
pour 0.13; silk 0.20 from the edge and holes; disallow micro/blind/buried vias;
pads 0.30 and courtyards outside the 0.30 edge band (solder-pad footprints
exempt, scoped by footprint); courtyards at max(body, land) + 0.10 with
`courtyards_overlap` an **error** and courtyard clearance 0; 0402-to-0402
+0.05; tall parts (U.FL, 2520 inductor) +0.5 mm to 0201/0402; user pads and
battery/motor pads ≥ 0.5 mm to any 0201/0402 (iron rework; round 4 extends it to
every part, LGA and QFN ICs included, as `sketch_v5.py` checks: `setup_board.py`
writes the extended scope at the next P1 re-apply); In1/In4 tracks
warned (solid GND planes); classes Analog, RF and Gate and the name-based
sensitive set (`*SPI1.*`, `*GYRO_*`, `*VTX_SPI.*`, `*/PA_*`, `*SHUNT_SENSE_*`)
disallowed on In2.Cu/In3.Cu; RF: no vias, 50 Ω width 0.100-0.110 on the outer
layers; only RF and GND copper on L1 in `RF_VTX_UFL`; no non-GND via inside
`RF_VTX_CHAIN` and `RF_RX_FEED`; only the RF feed on L6 in `RF_RX_ANT_L6`; SPI0
(`*SPI0.*`, `*FLASH_CS*`) kept out of `RF_RX_ROOT` (r 3.0 around the antenna
hole) on every layer; `SHUNT_CORRIDOR` carries only VBAT-class nets, GND and the
Kelvin pair on L6; USB pair gap and skew. Rule areas (positions from sketch v4,
moved with the parts at P2; sketch v5 moves tab T1 to the right edge at y −6.6
and the RTC6705 0.4 mm left, which `setup_board.py` takes over at the next P1
re-apply): the grommet flanges (`MOUNT_*`) and
`PART_EDGE_BAND`; `RF_VTX_CHAIN` (In1.Cu track keepout along the 5.8 GHz path,
half-width 1.2 mm), `RF_VTX_UFL`, `RF_PAD_CUTOUT` (In1.Cu zone-fill keepout under
the U.FL signal pad; P5 adds the BPF and match pads) with `RF_PAD_CUTOUT_L3`
(In2.Cu track keepout; a GND zone there is the local reference); `RF_RX_ANT`
(L1-L5: tracks, vias, pads, footprints, zones kept out) and `RF_RX_ANT_L6` (L6:
vias, footprints, zones kept out, the feed track allowed) at (−12.3, +6.5)
r 1.6; `RF_RX_EXIT` (B.Cu, footprints: no parts within 3 mm of the wire exit);
`RF_RX_FEED` (In4.Cu track keepout under the 2.4 GHz feed); `RF_RX_ROOT`;
`SHUNT_CORRIDOR` (the battery-to-shunt path, D10); `TAB_T1/T3/T4` (part keepout
1.0 mm beyond the edge band at the panel tabs). The round-2 `WIFI_STUB` is
removed with the stub (§4.7).

**Deliberate rule breaks (D21).** The baseline is the true fab limit above;
every exception is a custom rule named `D21 <name>` with its justification in the
rule comment, never a global ignore or a severity downgrade of a whole check;
each is logged in DECISIONS.md (D39-D44) and checked by critique against the
fab capability:

| Rule | What it allows, and the scope | Why it is safe |
|---|---|---|
| `D21 same_net_via_array` | hole to hole 0.20 between vias of one net (phase fields, EP arrays, battery and power arrays); different nets keep 0.30 | the 0.30 is NextPCB's CAF figure for different nets; both fabs build 0.20 hole to hole |
| `D21 fet_solid_pads` | solid zone connection on pads of the `POWER_FET` and `SOLDER_PAD` component classes | power path and iron need the copper; reflow profile through the NextPCB EQ |
| `D21 via_in_pad_typeVII` | (comment block) vias in 0201, QFN, EP and FET pads, including the 0.3 mm FET strip (N source) and pin-3 (P gate) pads of the round-4 cell | every via is filled and capped (board setting, IPC-4761 Type VII ordered); KiCad 10.0.6 cannot test a via in a same-net pad, so nothing is relaxed |
| `D21 trimmed_footprint` | (comment block) RTC6705 NC pads and the NOR exposed pad removed | the trimmed lands are their own project-library footprints (P3), so `lib_footprint_mismatch` stays an error and never fires |
| `D21 esp32_ganged_mask` (to be renamed `D21 fine_pitch_ganged_mask` at the next P1 re-apply) | (comment block) one ganged mask opening per pad row of the 0.35 mm-pitch leadless lands, as the footprint's "allow soldermask bridges" attribute; round-4 scope: the ESP32-D0WD-V3, 74LVC1T45GS (SOT1202) and BC847QASZ (SOT1216) footprints. **D53: dropped once BR-01 to BR-04 land** (no 0.35 mm-pitch part left); kept only on a fallback, scoped to the ESP32-D0WD-V3 (BR-01 fallback) and, on the PS-12 fallback of BR-02, to the BC847QASZ unless the BC847BV (0.5 mm pitch) replaces it | only if the NextPCB EQ (O15) accepts the pitch; inactive until then |
| `D21 rx_antenna_hole` | the antenna-hole footprint (`AE*`) inside its own keepouts `RF_RX_ANT`, `RF_RX_ANT_L6`, `RF_RX_EXIT` (scoped `severity ignore` on the disallow constraint for that footprint and its pad only) | the keepouts exist to keep every other part away from the hole; the selftest shows the pad is flagged without the rule and clean with it |

No pad sits inside the 0.20 mm copper-to-edge band, so no copper-to-edge
exemption is needed; the edge solder pads are exempt only from the 0.30 parts
rule.

KiCad features (owner rule). Delivered in P1 by `setup_board.py`: stackup with
impedance (RF50 tuning profile at 0.105 mm on F.Cu over In1 and B.Cu over In4),
the 16 template-ignored DRC checks re-enabled (D7), component classes
`PASSIVE_0201`, `PASSIVE_0402`, `TALL`, `SOLDER_PAD`, `POWER_FET`, net-class
patterns, priorities and colours, the named rule areas above, and the DRU
self-test (`setup_board.py --selftest`: synthetic tracks, vias, pads and parts
for every rule and area above, plus the net-class pattern check). Still to
deliver: a design block (or multichannel placement) for ESC1-4 (P2), the own
checks that every copper item lies inside Edge.Cuts shrunk by 0.20 mm and the
X-ray, heat and noise rules of §11 on the real footprints (P2; `sketch_v5.py` is
their key-package version), zone priorities written down with the pours (P5), a
jobset for the fab outputs (P7).

**P1 re-applied in this revision** (2026-10-07): `setup_board.py` now writes
everything this section and `board_spec.json` ask for (minimum through hole
0.20, silk minimum and new-item defaults 0.8 / 0.13, the RF width 0.105 from
`impedance.json`, the net-class patterns above with `+5V_USB` instead of `VBUS`
and no `/ESC?/VDD`, the rule areas and rules above). Results:
`check_board_setup.py --min-hole 2.0 --spec board_spec.json` 31 of 31 keys,
`kicad-cli pcb drc --refill-zones` 0 violations and 0 unconnected,
`check_rules.py` parses the rules, `setup_board.py --selftest` 68 of 68 cases
pass, ERC on the empty schematic 0, and
`setup_board.py --check` reports the project files up to date (idempotent).

---

## 9. Area budget

### 9.1 Usable area per side

Outline (I, `outline.py`, 10 µm grid): body 697.0 mm² − front arc 7.2 + ears
35.7 − holes 28.9 = **696.6 mm²**. Usable for parts, per side: inside a 0.30 mm
edge band and outside Ø 5.2 mm grommet-flange keepouts around the 3 holes
(flange diameter assumed; measure a BetaFPV ball at P2) = **643.6 mm²**.

### 9.2 Placed area per block (0.2 mm body/land spacing, perfect tiling)

Method (I, `budget_v6.py` = v5 with the round-4 corrections: the ESC cell
re-derived from the datasheet top views, §4.3, the O4 EN filter and hysteresis
resistor and the TPS2116 VIN1 capacitor, §4.2; v5, v4 and v3 kept): each part
counts (land L + 0.2) x (land W + 0.2). Lands: 0201 0.80 x 0.35, 0402 1.30 x
0.55, 0603 2.10 x 0.90; leadless ICs with toe pads at IPC density L (body + 0.4)
or the datasheet land (EFM8BB51 Table 7.2: 4.0 mm); bottom-terminated parts (LGA,
X2SON, FET SONs, crystals) at body size. Labels count their Tokyo glyph box at
0.8 mm height plus 0.15 mm mask clearance; the product name at the LINEUP B4 size
(2.0 mm rows). Every keepout and spacing rule of §7, §8.4 and §10 is an explicit
line. Vias come from a counted list: 150 vias outside pads and outside the ESC
cells (perimeter stitching ≤ 3 mm 37, RF fences 16, ESC side changes 24, video 4,
VTX control 8, rails 6, FC to top pads 4, second vias of about 12 L3 routes 12,
pour stitching 20, NOR and gyro side changes 12, D13-D17 7) at 0.28 mm² on each
side, plus the ESC cell sites of §4.3: **13 on the top and 6 on the bottom per
phase** (round 3: 7 / 15 on the reversed P pinout). Round 3 added two allowances
the v3 method left out: **far-side landings** of the in-pad (Type VII) vias,
which occupy the other side too (100 from top pads, 120 from bottom pads,
counted per EP array and decoupling cap, at 0.28 mm²; P2 credits a landing under
a named same-net pad or pour), and **outer-layer channels** for the nets barred
from In2/In3 (§8.2): a 0.09 mm track between pads needs 0.13 + 0.09 + 0.13 =
0.35 mm against the 0.2 mm the tiling books, so 0.15 mm per mm of route (65 mm
on the top, 143 mm on the bottom; the P gates now run on L6, §4.3).
Configuration: D13-D18 and the D14 levers applied (camera pads, pogo USB, no
Wi-Fi radiator, one 3.3 V LDO for FC and RX, LED group sharing the user 5V/GND),
floorplan of sketch v5 (NOR, gyro and O4 switch on the top, HD gate on the
bottom). This is the round-4 configuration; the D52 BOM reduction is counted on
the placed P2 board in §9.4.

| Block | Parts | Top mm² | Bottom mm² | Notes |
|---|---|---|---|---|
| ESC x4 | 88 | 202.6 | 111.1 | 4x QFN-20 (4.0 land), 12x CSD25310Q2, 32x 0201 + 4x 0402 (EFM8 VDD 2.2 µF; D52 BR-05 keeps only ESC3's) top; 12x CSD13202Q2, 12x 0201, 4x 0603 X6S, 8 C2 pads bottom; cell via sites 13 top / 6 bottom per phase (§4.3) |
| Input, protection, sense | 15 | - | 31.9 | 2x 0603, SOD-123FL, 1206 Kelvin shunt (net-tie), SC-70-6, 10x 0201 |
| FC core (RP2354A, beeper, LED-strip translator, LEDs, test pads) | 41 | - | 97.4 | QFN-60 (7.4 land), 2520 crystal, 2016 inductor, XSON6 translator (deleted by D52 BR-04), 5 test pads |
| Gyro + 1.8 V LDO | 7 | 13.7 | - | top |
| PIO OSD front end | 12 | - | 8.1 | |
| Blackbox NOR | 3 | 38.1 | - | WSON-8 6x5 (no smaller 16 MB part stocked) |
| RX (ESP32 + flash + SX1280; D52: ESP32-PICO-V3 + SX1281, 19 placements, §9.4) | 36 | - | 89.5 | no Wi-Fi radiator: 0402 51 Ω on LNA_IN; the RX LDO merged into the +3V3 LDO (Power) |
| VTX (RTC6705, PA, BPF, U.FL, LDO, PA reference, drive stage, NTC, selector) | 68 | 147.4 | - | 3225 8 MHz crystal; PA ring, match and DC-block zones +10 mm² beyond the tiled PA passives (sketch zones 22.1 mm²) |
| HD / O4 (D13-D17) | 19 | 16.5 | 5.7 | top: TPS22810DBVR, CT, EN divider, 1.5 MΩ hysteresis, 100 nF EN filter, CIN, BAS16LD (SOD882D), GPIO27 4.7 kΩ, AP1606; bottom: HD gate BC847QASZ + 7x 0201 (D53: one AP1606; the AP1606 USB term deleted) |
| Power (boost, mux, +3V3 LDO, camera filter) | 22 | - | 46.5 | TPS61022 + 2520 L + 5x 0603 X6S, TPS2116 + divider + VIN1 2.2 µF 0402 (10 µF since D52 BR-20), +5V 10 µF, LP5912 + caps (one shared 10 µF CIN since BR-14), ferrite + 10 µF |
| Connectors | - | 4.8 | 10.6 | pogo USB: 4 pads + 2 NPTH (holes on both sides); no SH1.0 parts |
| **Components** | **311** | **423.1** | **400.8** | |
| Pads, labels, silk art | | 138.0 | 119.5 | T: motor pads 32.8; battery 17.5; 10 user pads 16.8 + labels 25.5; HD pads with labels and halo 19.5; M1-M4, + -, 1S, ANT 22.9; VTX name 3.0. B: motor PTH rings 17.3; battery 17.5; logo + OPEN/AIO/WHOOP at 2.0 mm + REV1 68.2; test-pad and USB labels 16.5 |
| Keepouts and spacing rules | | 43.5 | 33.1 | T: RX antenna copper keepout 6.0; 5.8 GHz 1 mm part-free band 13.0; 3 panel tabs 9.0; U.FL halo 4.5; iron-rework halos 11.0. B: RX wire-exit area 18.8; tabs 9.0; 2520 L halo 3.5; rework halo 1.8 |
| Via allowance | | 42.0 | 42.0 | 150 counted vias x 0.28 mm² |
| Far-side via landings | | 33.6 | 28.0 | 120 bottom-pad vias land on the top, 100 top-pad vias on the bottom |
| Outer-layer channels | | 9.8 | 21.4 | L3-barred nets |
| **Total** | | **689.9 mm²** | **644.9 mm²** | |
| **Share of 643.6 mm²** | | **107.2 %** | **100.2 %** | like-for-like with the Matrix calibration (without the two round-3 allowances) **100.5 % / 92.5 %** (646.5 / 595.5 mm²); budget v5 before the cell correction: 97.15 % / 97.04 % like-for-like (625.27 / 624.57 mm², 7.4 / 6.7 mm² over the 96 % figure), 104.2 % / 103.9 % corrected. P0 area gate: passed by D23 on the real placement (below) |

Steps from the round-2 configuration (same method, cumulative; left: corrected
v4-v6 method, right: v3 method = like-for-like with the Matrix calibration;
`budget_v6.py` output):

| Step | Top / bottom, v4 | Top / bottom, v3 basis |
|---|---|---|
| 0 Round 2 case (a), D12 | 95.7 / 97.8 % | 95.7 / 97.8 % |
| 1 + round-3 corrections (far-side landings, channels, side vias, 3225 crystal, PA zones, B4 product name, Wi-Fi keepout on both sides, EFM8 2.2 µF 0402) | 106.9 / 109.4 % | 99.8 / 102.5 % |
| 2 + D13-D17 (HD pads, O4 switch, HD gate, 4th Cout, USB mux) | 112.7 / 110.9 % | 105.6 / 104.0 % |
| 3 + camera pads only (D18 cut 1) | 106.7 / 110.9 % | 99.6 / 104.0 % |
| 4 + smaller 128 Mbit NOR (D18 cut 2): none stocked | no change | no change |
| 5 + USB on pogo pads, 3 tabs (D18 lever 1) | 107.0 / 105.8 % | 99.9 / 98.9 % |
| 6 + no Wi-Fi radiator (D18 lever 2) | 105.6 / 104.4 % | 98.5 / 97.5 % |
| 7 + one 3.3 V LDO for FC and RX (D14 regulator consolidation) | 105.6 / 103.9 % | 98.5 / 97.0 % |
| 8 + LED group shares the user 5V/GND (D14 pad trimming) | 104.2 / 103.9 % | 97.2 / 97.0 % |
| 9 + round 4: ESC cell from the datasheet top views (13 / 6 sites per phase), O4 EN filter + hysteresis, VIN1 capacitor | **107.2 / 100.2 %** | **100.5 / 92.5 %** |

The corrected cell moves about 20 mm² of via sites from the bottom to the top
(the phase field now sits beside the P land on the top and lands inside the N
land on the bottom), so the sides are unbalanced again: the top is 8 points
above the bottom. The side-balancing lever is the O4 switch block on the bottom
(97.9 % / 95.1 % like-for-like); sketch v5 keeps it on the top in the
left-centre region, where it fits, and P2 decides the side.

**Calibration on the reference board** (I, photo BOM of 00/01, passives
estimated as 180x 0201 + 20x 0402): the Matrix II's components score 842 mm² by
this method; this board's score 824 mm² (round 4). D20's 96 % came from budget v3,
where the Matrix components plus the **round-2** pads, labels, keepouts and vias
(394 mm²) gave 96.1 % of both sides. Since then this board's own overhead has
grown (HD pads, 2.0 mm product-name rows, 0.8 mm labels, rework halos, tabs: 418
mm² on the v3 basis today), and the "Matrix at 97.9 %" figure of round 3 gave the
Matrix that overhead, not its own: the gate number (96 %) and its rationale no
longer described the same thing (round-4 finding). **D23 (2026-10-07) settles
the P0 area gate on the real placement instead**: the floorplan preview placed
342 of 345 parts at 0.2 mm body spacing with 0 violations (package bodies 65 % /
59 %, occupied incl. a 0.1 mm halo 80 % / 79 %), so the budget method
overshoots; P2 must place every part (including the logo and product-name art
and the pogo USB pads, which the preview did not place) and close the through-via
site count with filled and capped via-in-pad. The preview was drawn with the
round-3 ESC cell; the corrected cell puts the phase fields beside the P groups on
the top (about +20 mm² of top sites, −30 mm² of bottom sites by this method), and
its sites are top-only or bottom-only rather than both-side sites, which eases
the preview's shortage of both-side sites (about 116 free against about 218
needed). The budget stays the tracking tool for P2; its gate role ends with D23.

### 9.3 What gives next

The D14 and D18 cuts are applied (steps 3-8 above) and the P0 area gate is
settled by D23. These levers stay available to P2 if the real placement does not
close (numbers from `budget_v6.py`, v3 basis = like-for-like):

| Lever | Top | Bottom | Status |
|---|---|---|---|
| (a) final configuration | 107.2 % (100.5 %) | 100.2 % (92.5 %) | v6 (v3 basis) |
| O4 switch block on the bottom (side balancing) | −16.5 mm² (97.9 %) | +16.5 mm² (95.1 %) | P2 floorplan choice |
| TPS22810 in WSON-6 2x2 (DRV) instead of SOT-23-6 | −0.45 point (−2.9 mm²) | - | sourcing: once a NextPCB channel stocks it (O17); smallest-package rule |
| C2 programming by a fixture on the EFM8 pins (no C2 pads) | - | −1.2 points | owner: production fixture cost |
| Product name in 1.4 mm rows instead of LINEUP B4's 2.0 mm | - | −4.1 points | owner / lineup exception (B4) |
| Relax the L3 ban for slow digital buses (gyro SPI, VTX SPI, PA control) with the existing layer-change rule | −1.0 point | −1.5 points | v4 basis only (channels); a §8.2 rule change |
| HD and user groups share one GND pad (study option P3) | −0.8 point | - | owner (D16 names four HD pads); would also ease the user-group site (O20) |
| 8 MB NOR in a smaller package (Matrix has 16 MB) | −2 to −3 points | - | owner |
| Body 27.4 mm instead of 26.4 (about +52 mm² usable per side) | −7 to −8 points | −7 to −8 points | owner waiver (frame fit, Matrix envelope) |
| HDI 1+N+1 | - | - | **not proposed** (D12 (5): the owner rejected HDI for OpenAIO) |

### 9.4 BOM reduction (D52-D54, 2026-10-09)

Counts and areas from the BOM study ([BOM-REDUCTION.md](BOM-REDUCTION.md) §1,
`bomred/integ/totals.json`), on the placed P2 floorplan with the FLOORPLAN.md
metric: land extent plus a 0.1 mm halo ("occupied"), against 628.5 mm² usable
on the top and 616.6 mm² on the bottom (the P2 usable area, not §9.1's budget
figure). Placements are assembled BOM parts (pads, test points, logo and the
antenna hole are not); lines are unique MPNs. The corrected baseline adds four
parts the placed board still lacks (ESP32 CAP1, the TPS2116 VIN1 capacitor, the
D34 hysteresis resistor and EN filter) before any saving is counted.

| | Plan (placed P2 board) | Corrected baseline | **After BR-01 to BR-26** | BR-01 fallback | + owner calls OC-1 to OC-3 (not taken, D54) |
|---|---|---|---|---|---|
| BOM placements | 282 (F 125 / B 157) | 286 (F 125 / B 161) | **245 (F 110 / B 135)** | 256 (F 110 / B 146) | 229 |
| of which passives | 218 | 222 | 185 | 194 | 181 |
| Unique BOM lines | 88 | 89 | **76** | 78 | 73 |
| Footprints incl. pads, test points, logo | 326 | 330 | 289 | 300 | 273 |
| Top, occupied incl. halo | 445.6 mm² (70.9 %) | 445.6 (70.9 %) | **434.3 (69.1 %)** | 434.3 (69.1 %) | 431.2 (68.6 %) + OC-1 P2 rerun |
| Bottom, occupied incl. halo | 457.5 mm² (74.2 %) | 460.6 (74.7 %) | **459.9 (74.6 %)** | 448.7 (72.8 %) | 459.2 (74.5 %) + OC-1 P2 rerun |
| Top, package only | 313.0 mm² (49.8 %) | 313.0 (49.8 %) | 306.4 (48.8 %) | 306.4 (48.8 %) | - |
| Bottom, package only | 328.0 mm² (53.2 %) | 329.8 (53.5 %) | 337.6 (54.7 %) | 322.7 (52.3 %) | - |

Against the corrected baseline the set saves 41 placements and 13 lines, top
−11.3 mm², bottom −0.7 mm²: the bottom stays level because the ESP32-PICO-V3
adds 10.6 mm² there in a new site (§4.7). Variants: BR-05's 22 µF caps on the
top (likely) give top 441.2 mm² (70.2 %) / bottom 453.0 mm² (73.5 %) at the
same counts; BR-02 on its PS-12 fallback gives 248 placements, 76 lines, top
436.8 mm²; the worst case (BR-01 and BR-02 on their fallbacks, BR-17 kept) is
260 placements and 78 lines, still −26 / −11 against the corrected baseline.

| Block | Plan | After D52 |
|---|---|---|
| RX | 32 | 19 |
| VTX | 70 | 58 |
| Power | 38 | 34 (+3 corrected-baseline parts kept) |
| ESC | 20 per cell | 19 per cell (ESC3 stays at 20) |
| FC | 32 | 30 |
| IMU | 7 | 5 |
| OSD | 13 | 12 |
| LED | 7 | 4 |

Lines removed (18): 74LVC1T45GS,132, BC847QASZ, CJ17-400001010B20,
ESP32-D0WD-V3, GD25Q32EEIGR, GRM033R61A103KA01J, GRM033R61E104KE14D,
GRM033R71C103KA01D, GRM155C81A225KE11D, RC0201FR-07120KL, -071M5L, -0730RL,
-073K3L, -0749K9L, -074K7L, -07909KL, -0790K9L, SX1280IMLTRT. Lines added (5):
BC857BM,315, ESP32-PICO-V3, GRM033R71A103KA01D, RC0201FR-0733KL, SX1281IMLTRT.
The §9.2 budget table above is the round-4 P0 record and is not re-run; the P2
placement stays the binding area proof (D23).

---

## 10. Floorplan sketch

Key packages by their land extents (not centres), from `spec/sketch_v5.py`
(sketch v4 and v3 kept). It checks: inside the usable area; 0.2 mm land gap per
side, including the PA zones and the pad groups; the X-ray rule on **real**
exposed pads (datasheet D2/E2 or the house footprint EP) and on the full land
field of LGA parts; the heat and noise rules H1-H3 and N1 of §11 on both sides
and on the same side, with the round-4 **phase-via strips** of the corrected ESC
cell (§4.3) as phase copper; gyro, boost, antenna, PAOUT1, NOR and ESP32
distances; pad groups ≥ 6 mm from the RX antenna hole; pogo holes clear of the
VTX chain. Round 4 added: **pad groups drawn from the real geometry** (pads,
0.8 mm labels at the budget glyph width 0.2 mm from the copper, i.e. the budget
`lab()` box; sketch v4's blocks were smaller than their contents); **iron
rework**: every solder pad (group, motor and battery pads) ≥ 0.5 mm from every
part on its side, extended from 0201/0402 to all parts including LGA/QFN (a
fine iron next to the gyro LGA or an EFM8/RTC6705 QFN at 0.2 mm would reflow
their joints); the **O4 switch block with the real SOT-23-6 land**; and the
**panel-tab keepouts as hard checks**, built exactly like `setup_board.tab_rect()`.
Result: **0 fails for the parts, zones, tabs and three of the four top pad
groups; the user UART group (TP0 RP0 5V GND) has no compliant top site** (a
free-site search over every position and orientation: the only 4-pad site is the
rear centre, which the HD group takes): open item **O20**, decided at P2 between
(a) the user group on the bottom (+20 mm² bottom, budget v3 basis 92.5 → 95.6 %;
the LED strip then takes 5V from BZ+ and needs a GND, which undoes part of the
D14 pad trimming), (b) the left edge below M3 as in the floorplan preview, with
the antenna-root spacing reduced from 6 mm to about 3.6 mm for that group and V7
measuring return loss and desense with wires on TP0/RP0, or (c) the owner lever
of a shared HD/user GND pad together with a smaller label set. Every 85 °C part
stays ≥ 2 mm from every FET group, phase strip and phase pad, so none is rated at
a quarter temperature. Moves against sketch v4: RTC6705 0.4 mm left (2.03 mm from
the ESC4 P row, PAOUT1 line 4.75 mm); VTX LDO / PA reference / drive stage from
the right edge into the pocket between the RTC6705, the DC-block band and the
CAM pads; CAM pads to the right edge front; ESC1 group, its N row and the M1 pads
1.0 mm right (the preview moved them 1.5 mm); HD pads to a column at the rear
centre; LED group to the rear edge with 1.0 x 1.0 mm pads; O4 switch to the
left-centre region (preview position); NOR 0.2 mm forward and the input block
0.2 mm forward (0.5 mm from the battery pads); pad bulk 1.0 mm inboard (tab T4);
panel tab T1 from the front arc to the right edge. The passives fill and the
routing channels are the P2 probe; D23 makes the P2 placement the binding
proof. Coordinates: KiCad top view, origin at the body centre, +x right, +y
down. Flight-forward points at the top-right corner. Motors: **M4 front-left
beyond the top edge, M2 front-right beyond the right edge, M1 rear-right beyond
the bottom edge, M3 rear-left beyond the left edge**.

| Block | Side | Land extent x / y (mm) | Notes |
|---|---|---|---|
| M4 / M3 motor pads | T | M4 x −8.58…−4.58 on the top edge (moved 1.58 mm left with ESC4); M3 y −7.0…−3.0 on the left edge | 3 pads each at 1.5 mm pitch |
| M1 / M2 motor pads | T | M1 x 5.0…9.0 on the bottom edge (1.0 mm right with ESC1, round 4); M2 y 4.5…8.5 on the right edge | |
| ESC4 P-FETs / N-FETs | T / B | P −10.53…−3.83 / −9.35…−7.15; N −10.53…−3.83 / −11.75…−9.55 | 1.58 mm further left than round 2 (the N row now touches the left flange keepout), so the RTC6705 clears it by 2.4 mm |
| ESC3 P / N | T / B | P −9.35…−7.15 / −6.95…−0.25; N −11.75…−9.55 / −6.95…−0.25 | |
| ESC1 P / N | T / B | P 3.25…9.95 / 7.15…9.35; N 3.25…9.95 / 9.55…11.75 | 1.0 mm right (round 4: rear-edge room for the LED group) |
| ESC2 P / N | T / B | P 7.15…9.35 / 0.25…6.95; N 9.55…11.75 / 0.25…6.95 | |
| Phase-via strips (corrected cell, §4.3) / leg-cap strips | T / B | 0.2 + 0.95 mm outward of each P group on the top (P4 y −10.5…−9.55, P3 x −10.5…−9.55, P1 y 9.55…10.5, P2 x 9.55…10.5); leg caps 0.2 + 0.6 mm outward of each N group on the bottom | phase copper for H1/N1; the 8 phase vias land in the N drain lands below |
| EFM8 ESC4 / ESC3 / ESC1 / ESC2 | T | −6.6…−2.6 / −6.95…−2.95; −6.95…−2.95 / −2.75…1.25; 2.4…6.4 / 2.95…6.95; 2.95…6.95 / −1.25…2.75 | behind their P groups |
| RTC6705 | T | −1.8…4.6 / −7.85…−1.45 | 0.4 mm left of sketch v4 (round 4); rotated so PAOUT1 (pin 35) faces the PA and the loop filter faces west, away from the boost (≥ 8 mm); 2.0 / 3.1 mm from the ESC4 / ESC2 P groups |
| SE5004L PA + zones | T | PA 6.32…10.72 / −10.8…−6.4; VCC rings 5.32…6.32 and 10.72…11.72; match zone 7.72…9.32 / −12.3…−10.8 (layout-only reserve, no parts); DC-block band 4.8…9.72 / −6.4…−4.0 | rotated: VCC sides left/right, RF IN down, RF OUT to the edge; PAOUT1 CPWG 4.75 mm (45° routing); round 4 put the ESP32-D0WD-V3 (125 °C) partly beneath, EPs 0.3 mm apart; the ESP32-PICO-V3 (85 °C) may not sit there (H3, D52 BR-01) |
| BPF, U.FL | T | BPF 5.82…7.52 / −12.5…−11.6; U.FL 1.97…5.12 / −12.5…−8.5 | along the top edge; 5.8 GHz line on L1 over solid L2 |
| 8 MHz crystal (3225) | T | −0.83…1.77 / −11.6…−8.3 | 3.0 mm from the ESC4 copper (N1), beside the RTC6705 |
| VTX LDO, PA reference, drive stage | T | 4.8…9.01 / −3.8…−1.45 plus 7.15…9.01 / −1.45…0.05 (L-shaped pocket; D47 later moved the +3V3_VTX LDO to the bottom and the PA reference + drive stage to the top rear-left, FLOORPLAN.md; D52 BR-02 shrinks the drive stage to one PNP + 5 passives) | between the RTC6705, the DC-block band, the ESC2 EFM8 and the CAM pads, next to PAOUT1 (round 4; the right edge front now holds the CAM pads and tab T1); NTC in the PA ring |
| NOR (rotated, exposed pad trimmed) | T | −9.3…−2.9 / 4.5…9.9 | rear quadrant, 3.0 mm from the RX antenna hole, 0.6 mm from the RP2354A across the board |
| Gyro (rotated) + 1.8 V LDO | T | gyro −3.48…−0.38 / 1.45…4.05; LDO −0.18…2.2 / 1.45…2.75 | edge to edge: FET groups 4.04 mm, phase strips 6.3, boost 8.0, PA 10.3, pad bulk 6.7; lands clear of the RP2354A and SX1280 pads |
| O4 switch block | T | −12.6…−7.4 / 0.15…3.35 | TPS22810DBVR (3.0 x 2.8 land) + EN network, 16.6 mm²; left-centre region (the floorplan preview's position), +5V_HD about 9 mm to the VHD pad on L1 / L6 pours; the bottom is the side-balancing alternative (§9.2) |
| Pad groups (real size, round 4) | T | CAM 5V GND 9.21…12.9 / −3.75…−0.15 (right edge front: pads 1.2 x 1.0 at 1.3 mm pitch, labels inboard); HD VHD GND TX1 RX1 −1.79…1.9 / 4.3…9.2 (rear centre column: pads 1.2 x 1.0 at 1.3 mm pitch, labels west); LED BZ+ BZ- −0.7…2.9 / 9.41…12.9 (rear edge: pads 1.0 x 1.0 at 1.3 mm pitch, rotated labels above); **user TP0 RP0 5V GND: no compliant top site (O20)** | blocks incl. labels; pads ≥ 0.5 mm from every part; ≥ 10.5 mm from the RX antenna hole |
| RP2354A + 12 MHz crystal | B | MCU −2.25…5.15 / −2.25…5.15; crystal −1.5…1.1 / −4.65…−2.55 | centre; XOSC side north (P5 rotation); 2.0 mm from the ESC1 and ESC2 P groups |
| ESP32 + RX flash + 40 MHz crystal (round 4) | B | ESP32 2.4…7.8 / −12.6…−7.2; flash −1.4…2.0 / −10.65…−8.25; crystal −0.6…1.1 / −7.9…−6.6 | front; flash and crystal ≥ 4.3 mm from the PA, ≥ 2.4 mm from the ESC4 groups. Radio SPI to the SX1281 about 11 mm (P2 item). **D52 BR-01:** the ESP32-PICO-V3 replaces all three and is placed by a P2 trial outside the PA projection plus 2 mm (bottom keep-out x 4.32…12.72, y −13.4…−5.0) and ≥ 2 mm from the FET groups; the site above is the BR-01 fallback's ESP32 site |
| HD gate | B | 1.3…3.5 / −7.0…−4.0 | under the RTC6705; after D53 one AP1606 (BR-03), a much smaller block |
| Power: boost (TPS61022 + 2520 L + 5 caps) | B | 7.0…12.65 / −4.4…−1.75 | out of the ESC quarters: 2.0 mm from the ESC2 groups (H2), 2.0 mm from the PA projection, ≥ 5 mm from every crystal and the SX1280 |
| Power: mux + VIN1 cap, +3V3 LDO, +5V cap, camera filter | B | 3.7…6.8 / −6.9…−2.45 | |
| SX1281 + TCXO + LPF | B | SX1281 −9.1…−4.7 / 1.75…6.15; TCXO −4.5…−2.4 / 5.35…7.05; LPF −9.9…−9.3 / 3.5…4.6 | SX1281 pad under no exposed pad (NOR pad trimmed); TCXO south-east of it, 4.7 mm from phase copper; feed about 5 mm to the antenna hole |
| Power entry: shunt, INA186, TVS / pad bulk | B | −8.0…−1.2 / 7.9…9.9; bulk −10.3…−8.2 / 8.8…11.1 (2.1 mm from the rear edge, clear of tab T4, long axes parallel to the edge) | inboard of the battery pads; Kelvin pair; boost VIN taps +BATT on L4 |
| USB J31 (superseded pogo pads: D57 / D76) | B | floorplan v3 | vertical JST BM04B-SRSS-TB next to a mounting hole, mating zone above it (D72 / D76) |
| OSD front end | B | P2 (near the video path, X2SON parts rated 125 °C) | |
| Battery pads B+ / B- | both (THT) | B+ −7.6…−4.6, B- −4.0…−1.0, y 10.4…12.4 | pigtail exits rearward |
| RX antenna hole | through | (−12.3, +6.5) | copper keepout r 1.6 on L1-L5 (L6 admits the feed); wire-exit part keepout r 3.0 on the bottom |
| Test vias FCB, CLK, DIO; ESC C2D / C2CK vias (D67: mask-open filled 0.35/0.20 vias, no silk; the RXB and GND pads are removed) | B | near the MCU / at each EFM8 | boot by the shared SW1 + D8 (D65) |
| Silk art | B | P2: free patch, may cover tented vias | |

**Edge budget (top, solder pads).** Usable edge length about 77 mm (top 17.7,
left 20.6, rear 20.6, right 17.7, flanges and the front arc excluded). Demand on
the top: motor pads 16, battery 7, LED/BZ+/BZ- 3.6, CAM/5V/GND 3.6, RX hole keepout
3.2, 3 tabs with keepouts 10.5, the VTX chain on the top edge (crystal, U.FL,
BPF) 8.4, gaps 4: about 57 mm. The edge has length to spare, but the free edge
segments lie in the ESC quarters (phase pours and via strips) or within 6 mm of
the RX antenna hole, which is why the fourth group has no top site (O20). The HD
group sits inboard (rear centre), and the bottom's top edge carries the pogo
pads (4.2 mm).

RF keepouts:
- **5.8 GHz**: no copper on L1 within 0.15 mm (CPWG gap) of the line except the
  coplanar GND; L2 solid under the whole chain plus 1 mm (rule area
  `RF_VTX_CHAIN`, no non-GND via inside), except the `RF_PAD_CUTOUT` areas (L3
  GND as their reference, no L3 tracks); via fence ≤ 2.5 mm pitch both sides; no
  via in the RF path; U.FL ground tabs with ≥ 4 vias to L2; no other parts within
  1 mm of the line on L1 except the DC block and the choke in the DC-block band.
- **2.4 GHz**: CPWG on L6 over L5 from the LPF to the antenna hole, L5 solid
  under it (rule area `RF_RX_FEED`, no non-GND via); copper keepout r = 1.6 mm
  around the hole on L1-L5 (tracks, vias, pads, footprints, zones) and on L6
  except the feed; no parts within 3 mm of the wire's exit on the bottom.
- **Antenna separation**: VTX antenna (U.FL, front edge, up to the canopy) and RX
  wire (left-rear, rearward or up the canopy) ≥ 20 mm apart, orthogonal where
  possible.
- **Aggressors** (listed and tested in V5b and V7): the ESC phase nodes (0-4.35 V
  in nanoseconds at 96 kHz, up to 12 A): FM sidebands on the video near the
  RTC6705 loop filter and VT net, reference spurs on the SX1281 LO near the
  TCXO, hence N1 (§11); the boost switch node (≥ 5 mm from every crystal, the
  TCXO, the SX1281 and the RTC6705 loop filter); the blackbox SPI0 bus (75 MHz writes and reads: harmonics at 2400 and 2475 MHz, NOR and bus ≥ 3 mm
  from the antenna hole); RP2350 150 MHz x 16 = 2400 MHz and ESP32 40 MHz
  harmonics. V7 runs with every aggressor active, including the blackbox
  writing and the O4 at 25 and 700 mW.

---

## 11. Layout rules specific to this board

- **Commutation loops**: one 100 nF X6S 0201 per half-bridge, on the bottom at
  the N source end, GND pad on the N source copper and +BATT pad on its own Type
  VII via into L4, so the loop closes through the solid L4 plane under the cell
  (§4.3); loop ≤ 4 mm² (about 1.5-2 mm² estimated; drawn with dimensions at P2). Target N-FET VDS overshoot
  ≤ 9 V at 18 A turn-off (12 V part).
- **Phase copper** (pinouts from the datasheet top views, §4.3): the P drain
  (pin 4 + strip pad 7) into a top phase pour carrying the 8-via phase field
  outside the P land; the vias land in the N's merged drain land (pad 8 + pins
  1/2/5/6) and the bottom phase pour; the P source land (pad 8 + pins 1/2/5/6)
  holds 4 in-pad +BATT vias; the N source strip holds 3 in-pad GND vias; phase
  to motor pad ≥ 1.2 mm wide on L1 and repeated on L6, joined at the wire-anchor
  holes; solid pad connections (no thermal relief) on FET pads; the P gate leaves
  pin 3 through a via to L6.
- **+BATT path**: battery pad (`+BATT_IN`) → shunt (Kelvin) → `+BATT` on L6 pour
  + L4 plane + L1 pours at the clusters; ≥ 12 power vias at each battery pad; 4
  +BATT vias per phase in the P source land plus the leg-cap via. Size the trunk for 25 A pack, each channel for 12 A
  bursts. Battery-to-shunt corridor in the `SHUNT_CORRIDOR` rule area before
  routing. The Kelvin pair `SHUNT_SENSE_P/N` leaves the shunt's inner pad edges
  as a pair on L1 or L6, away from the power current.
- **GND**: L2 and L5 unbroken (the only L2 openings are the RF pad cut-outs);
  L1/L6 pours stitched every ≤ 3 mm at the perimeter and around the RF.
- **L3/L4**: L4 is one solid +BATT pour under every L3 route; L3 layer changes
  only within 2 mm of a +BATT capacitor; no Analog, RF, gate, gyro SPI, VTX
  control or video on L3 (§8.2).
- **Gyro isolation** (edge to edge): ≥ 4 mm from the FET groups on either side,
  ≥ 5 mm from the boost IC and inductor, ≥ 10 mm from the PA, ≥ 2 mm from any
  switch node on any layer, and no bulk MLCC carrying ESC ripple (pad bulk, ESC
  local bulk, boost Cin) within 5 mm (MLCC piezo emission couples into MEMS); its
  1.8 V LDO and decoupling on the same side. Sketch v4 meets these; P2 re-checks.
- **Video ground**: camera return enters L2 at the CAM GND pad; video traces on L1
  over L2 (or L6 over L5) with GND on both sides, never on L3; no ESC return
  current through the front quadrant; 100 pF shunts at video entry points;
  RTC6705 loop filter ≥ 5 mm from the boost.
- **Boost**: Cin at VIN, Cout–SW–GND hot loop < 3 mm, SW copper minimal, MODE
  tied to VOUT (forced PWM), EN tied to VIN (always enabled, D52 BR-11; the
  TPS2116 mux selects USB or the boost), VIN from `+BATT` after the shunt (L4), not
  through ESC copper. Out of the ESC quarters: ≥ 2 mm from every FET group on
  either side (H2) and ≥ 2 mm from the PA projection.
- **Heat and noise distances** (edge to edge, 2D projection, same side or across
  the board; checked by `sketch_v5.py`, by script on the real footprints at P2):
  - **H1**: every 85 °C part ≥ 2 mm from every FET group, phase pour and motor
    pad. The quarter model of §4.3 is lumped; at 2 mm the FET-local spreading
    term has fallen by about 3-7 K at 4-6 A and much more in bursts (I, ln-decay
    in the 0.04 W/K copper sheet). A part closer than 2 mm is rated at its ESC
    quarter's temperature and binds that channel; V8 measures the gradient with
    a thermocouple 2 mm from a loaded group and the rule widens to 3 mm if the
    rise there exceeds half the quarter rise.
  - **H2**: TJ-binding converters (the boost) ≥ 2 mm from every FET group.
  - **H3**: no heat source ≥ 0.5 W (FET groups, PA, boost) over an 85 °C or
    TJ-binding part on the other side; the PA keeps a 2 mm margin. The RTC6705
    (0.31-0.33 W) is not a shadow source; its own case limit covers it.
  - **N1**: crystals, the TCXO and the RF filters ≥ 3 mm from phase copper on any
    layer and ≥ 5 mm from the boost switch node; the RTC6705 loop filter and VT
    net ≥ 3 mm from phase copper and ≥ 5 mm from the boost (loop-filter side
    oriented away from it).
- **Crystals**: 12 and 8 MHz next to their ICs with GND guard, no signal on
  L2 under them; TCXO likewise; distances per N1. The 40 MHz crystal is inside
  the ESP32-PICO-V3 (D52 BR-01) and returns only on the BR-01 fallback.
- **Exposed pads and X-ray across the sides**: EFM8, RTC6705, PA, SX1281,
  ESP32-PICO-V3, RP2354A and FET exposed pads soldered with Type VII via-in-pad; the NOR's
  unconnected metal pad has no land (§4.9). NextPCB X-rays every QFN/LGA board,
  and 2D X-ray superimposes both sides: **no exposed pad on one side over an
  exposed pad or LGA land on the other**, checked on the datasheet pad sizes and
  on the full land field of LGA parts (sketch v5; by script at P2); other
  cross-side overlaps of bottom-terminated parts are allowed and the EQ requests
  angled or CT X-ray for them.
- **RX antenna root**: the NOR, SPI0 and every pad group stay ≥ 3 mm and ≥ 6 mm
  respectively from the hole.
- **Reflow order and second side**: the tallest parts are the U.FL on the top and
  the 2520 inductor on the bottom (no SH1.0 parts remain); the second-side print
  and placement still need a support fixture or pallet for the first side's
  parts: EQ item. Heaviest part per pad area well below the 30 g/in²
  (0.047 g/mm²) second-side guideline (I).
- **0201 on planes**: thermal relief spokes 0.10-0.15 mm, equal copper on both
  pads (tombstoning); vias in 0201 pads per §8.3.
- **Hand-solder pads**: battery and motor pads get a copper neck so a 60-80 W
  iron can heat them; mask-defined edges.

---

## 12. Firmware targets

| Firmware | Plan |
|---|---|
| Betaflight | New board config `OPENAIO_WHOOP` in betaflight/config (manufacturer ID to request; proposal INCU), `FC_TARGET_MCU RP2350A`, derived from the house OPENFC_LITE_MINI_RP2350A target. Requires release ≥ 2026.6.2. Defines: SPI1 gyro (BMI270 or ICM42688P, one per revision), `ENABLE_FB_OSD` with OSD_W/EN/SYNC = GPIO14/15/16, `PIO_LEDSTRIP_INDEX 1`, UART0 = serial RX (CRSF), UART1 = DJI O4 Lite pads (MSP DisplayPort: `MSP_DISPLAYPORT_UART SERIAL_PORT_UART1` and `PINIO1_CONFIG 129` inside `#ifdef USE_OSD_HD`, which `config.h` sees only in a cloud OSD (HD) build because it is read before `common_pre.h`: an OSD (SD)-only build boots analog, an OSD (HD) build boots in HD mode with the analog VTX held off, and a plain-OSD or local `make` build gets neither until a preset is applied; PINMAP §5.1 table), PIOUART0 = user pads TP0/RP0 (GPIO2/3, PIO1), `PINIO1_PIN PA27` (HD line), no `USE_OSD_SD` define (it would leave `USE_OSD_HD` undefined and force the O4 to a 30 x 16 SD canvas; `common_pre.h`, `displayport_msp.c`), MSP never on UART0 (Betaflight 2026.6.2 `config.c` L568-581), `USE_VTX_MSP` with **no `VTX_MSP_UART`** (on 2026.6.2 it overwrites the UART0 RX_SERIAL default and the board boots without a receiver, PINMAP F2; MSP-VTX over CRSF comes from the CLI line of PINMAP §5.4), `USE_FLASH` W25Q128 on SPI0 CS GPIO21, motors on PIO0 GPIO25/24/23/22 = M1-M4, bidirectional DShot, `DEFAULT_ALIGN_BOARD_YAW` ±45 (diamond mount; sign fixed in P4), current scale 500 and VBAT scale measured, beeper inverted. Full config in PINMAP §5 |
| Bluejay | Stock Bluejay ≥ 0.21, layout **BB51 "A"** (no custom layout). The release build is a **V2 outcome** (§4.3): first power-up on **`A_X_10_96`** (DT about 204 ns against the AGM210MAP td(off) + tf of 58 ns N / 84 ns P at datasheet gate drive, longer on EFM8 port drive), then **`A_X_5_96`** (about 102 ns, the Matrix II build) after the V2 shoot-through check (`A_X_15_96` was the TI-fallback start build); 96 kHz halves the bus ripple. All are stock builds (Makefile `DEADTIMES` 0 5 10 15 20 25 30 40 50 70 90 120, `PWM_FREQS` 24 48 96, V). Published settings: **temperature protection on at 100 °C** (`DEFAULT_PGM_ENABLE_TEMP_PROT` is 0, i.e. off, in BluejaySettings.asm; options 80-140 °C read from the EFM8 die sensor; V4 correlates the die reading with the FET thermocouple), braking limits per V3c. Flash through Betaflight 4-way passthrough after the production C2 flash (§12.1); C2 pads for recovery |
| AM32 | not applicable (EFM8 MCU) |
| ExpressLRS | Day one: `Unified_ESP32_2400_RX` with the board's own layout JSON (the generic `Generic 2400 Whoop Rx and VTx.json` with `vtx_mosi` on GPIO14, `"vtx_miso": -1` written explicitly in the layout and in any overlay of the generic file (D81: the stock 23 is the PICO's flash DI) and `vtx_amp_pwm` on GPIO13, because the ESP32-PICO-V3 uses GPIO16/17/18/23 for its in-package flash and the PNP drive stage needs a non-strap pin; D53, PINMAP §6); ELRS Wi-Fi kept (D58). Release: a target entry in ExpressLRS/targets with that layout plus an overlay with this board's VPD/PWM calibration arrays (the 5950 MHz entry filled from a 5945 MHz measurement, since `VpdFreqArray` 5650/5750/5850/5950 is a code constant), LED index for the single RGB LED, `power_values [13]`, no `radio_dcdc`. ELRS ≥ 4.1. The levels are the five ELRS pushes (§1); no 200 mW level is proposed (it would change the vtxtable for every ELRS VTX board). **Release gates (upstream patches, O6; release blocked until (1)-(5) merge):** (1) fix `LinearInterpVpdSetPointArray()` / `LinearInterpSetPwm()` (missing `break`, and an integer slope that is 0 below 100 counts per 100 MHz); (2) closed-loop 400 mW VPD setpoint (YOLO 2250 counts is above the DET range, so `400` is open-loop full drive today); (3) power index 1 handled as pit (VREF off); (4) pit and disarm power the RTC6705 down (GPIO21, VTX SPI tri-stated, frequency re-sent) or write `POWER_AMP_OFF`; (5) refuse frequencies below 5645 MHz and hold pit (the L band commands the RTC6705 below its VCO range, and `rtc6705SetFrequency()` has no range check, so the PLL rails and an unlocked carrier meets full PA gain); an upper bound or a lock check as well if V5's hot lock fails at the top channels (5885-5945 MHz are equally outside the 5725-5865 MHz Fc spec). (Stock ELRS `initialize()` already drives GPIO13 to the pit count at device init, so patch (4) needs no GPIO13 part, §4.8 start-up.) **Further patches (not gating):** (6) thermal derate from the PA NTC on GPIO34, read only in the `hwTimer::isTick` window like the detector (ESP32 erratum 3.11: an ADC1 power-up glitches GPIO36 = radio BUSY); (7) a VTX target keeps its VTX in the last state when Wi-Fi starts automatically (or a hardware key that suppresses auto-start); (8) per-unit VPD calibration: `analogReadMilliVolts()` with the eFuse calibration plus a per-board offset in the ELRS config, and calibration frequencies inside the rated band (for example 5850/5865) as target keys; until it exists the 25 mW unit spread is published as measured (rank 4). **Defaults** (§4.8): vtx power 2 (RCE) and `vtx_low_power_disarm` OFF until patch (3) merges, applied after ELRS has written its vtxtable |

### 12.1 Production programming

Blank EFM8BB51F16I parts from Digi-Key carry no BLHeli bootloader, so 4-way
passthrough cannot reach them; a blank ESP32 has to be strapped into download
mode for its first flash; the VDD_SDIO eFuse may be burned in the same session
(optional after D53: GPIO12 is unconnected and its internal pull-down already
holds the 3.3 V-flash strap, so the burn no longer has to come before any
flash write; PINMAP F18).
Fixture (D67): pogo pins on the 8 C2 test vias and the BOOT_SW node (SW1 or a
probe on its pad), the JST SH USB plug J31, plus the battery pads,
through which the fixture feeds **+BATT at 3.3 V during C2** (EFM8 VIH = 0.7 x
3.3 = 2.31 V against a 3.3 V C2 adapter; at a 4.2-4.35 V cell it would be
2.94-3.05 V). Order:

1. Boot straps: hold SW1 (or the fixture probe on BOOT_SW) while power is
   applied. D8 pulls both straps: the RP2354A starts in USB BOOTSEL (QSPI_SS low
   through R44) and the ESP32 in ROM download mode (GPIO0 low); each mode stays
   latched until that chip's next reset, so SW1 may be released now.
2. RP2354A: write the Betaflight (≥ 2026.6.2) cloud build for `OPENAIO_WHOOP`
   with the **OSD (SD)** option and **without OSD (HD)** (plus the serial-RX
   CRSF, VTX, LED strip and blackbox options) as a UF2 over USB (or `picotool
   reboot` after a picotool load). The RP2354A restarts into Betaflight, which
   boots in analog mode (PINMAP §5.1 table), while the ESP32 stays in download
   mode. O4 users later flash a build with OSD (HD), which boots in HD mode; the
   README says so.
3. ESP32: esptool through Betaflight serial passthrough (U0RXD/U0TXD on UART0);
   optionally burn VDD_SDIO = 3.3 V (order free); run the VTX test application
   from RAM (RTC6705 register 0x00 = 0x0190 read in 3-wire half-duplex mode on
   GPIO14, §4.8); flash ELRS with the board's layout JSON. (Alternative: a blank
   ESP32's RTC-watchdog boot loop re-latches the straps at each system reset
   while SW1 is held after power-up.) The same sequence recovers a bricked ELRS
   image in the field (README).
4. EFM8 x4: NextPCB pre-programs Bluejay before reflow (D67); bench recovery by
   C2 (Silicon Labs adapter or an open C2 programmer) on the test vias writes the
   BLHeli bootloader and the first-power-up Bluejay build (`A_X_10_96` until V2
   releases `A_X_5_96`).
5. First apply and save the UART0 function mask (`serial UART0 131136 115200
   57600 0 115200`: RX_SERIAL + VTX_MSP, PINMAP §5.4) and the analog preset
   (`serial UART1 0 …`, `osd_displayport_device = FBOSD`, `vcd_video_system =
   AUTO`, `pinio_config = 1,1,1,1`). Without VTX_MSP on the CRSF port Betaflight
   2026.6.2 sends no MSP-VTX replies, ELRS's `devMSPVTX` gives up after 5 s and
   the vtxtable never lands. Then boot once on a battery with ELRS running, so
   `devMSPVTX` writes its vtxtable into Betaflight (otherwise its
   `clearVtxTable()` would reset the defaults on the user's first session,
   §4.8); then apply the VTX defaults (vtx power 2 = RCE, `vtx_low_power_disarm`
   OFF) and save. The shipped diff carries all of these lines, so a defaults
   reset on any build type is undone with one paste.
6. Verify: Betaflight 4-way passthrough reads all four ESCs; ELRS binds; the PA
   current after power-up is the pit value (VREF off); HD line toggled once
   (+5V_HD switches, +3V3_VTX drops).

O17 asks NextPCB whether they offer EFM8 C2 and ESP32 programming; otherwise it
is done at OpenDrone. Fixture and labour are budgeted in the NRE (§15.3).

---

## 13. Silkscreen plan

Per LINEUP-CONVENTIONS B2-B14 and the owner rules: no component silkscreen, no
reference designators, no "Drone" anywhere on a fabricated layer, Tokyo font
embedded, back text mirrored, bold upper-case pad codes of ≤ 3 characters, one
code table shared by schematic pad values, silk, pinout and README. Codes use
the **ASCII hyphen-minus** (`-`, `B-`, `BZ-`), never U+2212, so
`check_conventions.py` B8 matches and the Tokyo glyph exists. Size (D12):
0.8 mm high, 0.6 wide, 0.13 stroke, the commons standard; it meets NextPCB at
1 oz and LINEUP B11, deviates from LINEUP B7's 1.2 mm (1.0 mm back) and is below
JLC's published 1.0 / 0.15 legibility floor: owner sign-off for this board
pending (O11; §8.1).

| Side | Content |
|---|---|
| Top | pad labels (ASCII): **TP0 RP0 5V GND** (user UART, PIOUART0; side per O20), **LED BZ+ BZ-**, **CAM 5V GND**, **VHD GND TX1 RX1** in an "HD" frame (DJI O4 Lite); **M1 M2 M3 M4** at each motor pad group (Betaflight order: M4 front-left, M2 front-right, M3 rear-left, M1 rear-right); **+ -** (2.0 mm) and **1S** at the battery pads; **ANT** at the RX antenna hole; connector name **VTX** at the U.FL. No forward arrow unless the owner approves it (O12); the front is marked on `User.Eco2` and in the README |
| Bottom | incutec logo ≥ 6.1 x 1.4 mm; product name **OPEN / AIO / WHOOP** stacked in Tokyo at the LINEUP B4 size (2.0 mm rows; 1.4 mm only as a recorded lineup decision, §9.3); **REV1** (equal to the board title-block rev `rev1`); no test-point labels (D67: FCB, CLK, DIO and the C2 vias are unlabelled, listed in the pinout; the RXB and GND pads are gone); **USB** with a pin-1 mark at J31; ESC C2 pads unlabelled (flashing test points, LINEUP B7; D12), documented in the pinout diagram |
| Off-board | `User.Eco2` note marking the front; mounting-pattern guide on `User.Eco1`; grommet-flange keepouts as rule areas |

---

## 14. Validation plan

| # | Test | Pass / fail |
|---|---|---|
| V1 | 5 V rail: VIN 4.35 → 2.6 V at the analog load (0.70 A, 1.25 A) and at the HD load (1.43-1.48 A with an O4 or an electronic load on +5V_HD; O4 inrush with CT 10 nF); the continuous load the boost holds for 10 min at board temperatures 50/65/80 °C and VIN 2.8/3.0/3.2/3.7 V, with one ESC channel at 4 A, TPS61022 case temperature logged (TJ ≈ Tcase + ΨJT·P); overload step to 2.5 A at 2.8 V for 10 s and a short on the user 5V pad (inductor and IC temperature); **battery only at board 85 °C and 105 °C for 10 min** (+5V regulated, mux on VIN2); **USB hot-plug and unplug with a 4.2 V cell fitted**, scope on +5V, +3V3 and **TPS2116 VIN1**, 20 repeats, fast and slow (1 ms) VBUS rise, through the clip-on adapter with a 1 m and a 2 m cable, including fast and bouncing pogo contact; USB + battery: +5V_USB at 5.25 V with the cell at 4.35 and 3.7 V (cell and USB current), **USB + cell + HD mode** with an O4 (the O4 runs from `+5V_BST`, no USB current into it, D53 BR-10); USB only with the HD line high (O4 switch off); O4 shed and switch-on thresholds set and measured **with one ESC loaded at 6-12 A** (96 kHz ripple on +BATT), and a shed under load held for 10 s (no cycling); **TPS22810 EN** with GPIO27 low, undriven (FC held in reset) and high, at board 25 and 85 °C | +5V ≥ 4.85 V at VIN ≥ 2.8 V (analog) and ≥ 4.75 V down to the shed threshold (HD), the O4 shed before +5V drops further; ripple ≤ 50 mV p-p; no FC/RX reset to 2.5 V, on hot-plug or on unplug; cold start from 3.0 V; TJ ≤ 125 °C; no current into the cell with USB present; +5V ≥ 3.1 V and +3V3 ≥ 2.9 V through every USB switchover; VIN1 ≤ 6.0 V on every hot-plug (else the board RC snubber, §4.2); EN ≤ 0.9 V with GPIO27 low or undriven (≤ 0.87 V calculated, BR-24), shed point within 2.74-3.14 V and switch-on within 3.23-3.82 V at both temperatures, one shed per sag (no on/off cycling); the board survives the overload step; the published BEC table (current per VIN and board temperature, both modes) |
| V2 | ESC dead time: scope P gate, N gate, phase node, per-ESC supply current; builds DT 15/10/5 at 96 kHz; VIN 2.5, 3.0 and 4.35 V plus regen (throttle chops to 5.25 V); FET case heated to 100 °C; both directions of phase current (motoring and damped braking); all six gate pins of each EFM8; 3 boards x 4 ESCs; the port drive mode recorded (PRTDRV read over C2, or the gate edge against the high- and low-drive VOH) | no shoot-through spike > 2x the steady current; P fully off (Vgs > −0.3 V) before N on, and **N Vgs < 0.3 V before P on**, at every corner; **N gate kick < 0.3 V during P turn-on** (and P gate kick > −0.3 V during N turn-on). The release build is the shortest DT that passes; `A_X_15_96` is an acceptable outcome |
| V3 | N-FET overshoot at 18 A turn-off; EFM8 VDD peak at the same event | VDS ≤ 9 V; VDD ≤ 5.3 V |
| V3b | Unplug surge: battery pulled at hover throttle with props on the bench, scope on +BATT and on one EFM8 VDD, current probe on the TVS (current, duration, clamp energy), 10 repeats | peak recorded; TVS energy against the SMF5.0A curve (else SMAJ5.0A); N VDS against 12 V and the avalanche rating; if VDD exceeds 5.5 V the README warns against unplugging spinning |
| V3c | EFM8 VDD under regen and hot-plug: fresh 4.35 V pack, full-throttle-to-zero chops and prop-strike braking on all four motors; **hot-plug of a fresh 4.35 V pack, 20 repeats**, with the D52 bus (BR-05: no EFM8 2.2 µF in ESC1/2/4, 3.0-4.2 µF effective less); scope EFM8 VDD at the pin and the DShot pin against EFM8 GND, and the TPS61022 VIN together with the +5V_BST start-up on each plug-in; decides PE-8 (pad bulk swap) | ≤ 5.3 V including spikes; TPS61022 VIN ≤ 4.8 V until +5V_BST passes 0.7 V (DS §6.3); else Bluejay braking limits, then the 2.2-4.7 Ω VDD resistor; for hot-plug, the damping bulk at the pads (§4.1) |
| V4 | ESC rating protocol: 1S from a real pack (or 3.7 V supply with the pack's resistance), stated; board in a frame under a canopy, motor + prop in propwash (stated airflow), 25 °C; VTX at 25 mW (and a max run, and an HD run with an O4); one channel stepped 2/3/4/5/6 A while others run 2 A, on each of M1-M4 (the nearest 85 °C part differs per channel), then all four at 2/3/4 A; bursts at 12 A and 18 A started from the measured hover steady state, timed to FET 110 °C | every part inside its rating, measured at the part: hottest FET ≤ 100 °C, EFM8 ≤ 125 °C, RTC6705 case ≤ 80 °C, RP2354A, gyro, SX1281, NOR, ESP32-PICO-V3 (in-package flash), the 12/8 MHz crystals, the TCXO and SE5004L case ≤ 85 °C, TPS61022 case (TJ ≤ 125 °C), worst X6S cap in a loaded cell ≤ 105 °C (thermocouples on each); one thermocouple 2 mm from a loaded FET group (rule H1); Bluejay die temperature logged against the FET thermocouple. Publish the curve and the burst durations; same rig on a Matrix II |
| V5 | VTX power: 25/100/max at 5645, 5650, 5750, 5850, 5917, 5945 MHz and the full channel table, on ≥ 5 boards; VIN 2.8/3.0/3.7/4.35 V; PA case temperature logged; synthesiser lock at 5645 and 5945 MHz at RTC6705 case −10 °C and 80 °C; 5362 MHz commanded (patched firmware must hold pit; output and frequency recorded on stock); pit leakage at the U.FL; **boot leakage from power-up until the channel is set**; VREF from the reference per board, Icq and gain at VREF 2.79 and 2.91 V and versus VREF 2.0-2.85 V (lever a); **power ceiling** set on the highest-output sample at 4.35 V and 25 °C (the PNP stage's Re, D52 BR-02, starting at 10-15 Ω); duty steps between 25 and 100 mW; video SNR with REG1D8 (pin 26) undecoupled and no 6.5 MHz spur with pin 17 open (BR-15, BR-16); HD mode: no carrier above −80 dBm EIRP on 5725-5850 MHz with the O4 active; no-antenna run at max; **Q27 case temperature at the top PA-drive step** at hot ambient (12 % Ptot margin at Re 10 Ω, §4.8); **X4 start-up margin**: a series resistor of 3-5x the 250 Ω maximum ESR (TAXM8M4RDBCCT2T, LCSC C400090), cold start at −10 °C on several boards and a slow supply ramp (the RTC6705 datasheet gives no oscillator ESR or negative-resistance limit) | 100 mW within ±3 dB unit to unit at 5850 MHz, 25 mW spread published; max ≤ 27 dBm at the U.FL on every sample; what the lowest sample reaches at 3.0 V and 85 °C case published; ≥ 20 duty steps between 25 and 100 mW; PA case ≤ 85 °C; frequency error ≤ ±200 kHz and lock at both temperatures (else gate (5) gains an upper bound); the board survives the no-antenna run; Q27 inside its derated Ptot (else Re 15 / 27 Ω); X4 starts in every case with the added series resistor (else a lower-ESR 8 MHz 10 pF 3225 on the same land); all values published |
| V5b | Video with motors loaded: SNR and PWM sidebands with all four motors at 4-6 A, PA on +BATT and on the +5V selector position; boost loaded | no visible bars; sidebands reported; selector default confirmed |
| V6 | VTX spurious with the BPF, on a spectrum analyser to ≥ 18 GHz | 2nd harmonic ≤ −30 dBm at every channel incl. 5880-5945 MHz; 3f reported; RTC6705 half-frequency leakage (2.8-2.97 GHz) reported |
| V7 | RX: antenna trimmed to resonance by return loss with its flight routing (rearward or up the canopy, away from the motor leads); sensitivity and desense with every aggressor active (motors at hover and at the rated current, VTX at max, OSD on, **blackbox writing**, boost loaded, NTC derate reads active, **O4 at 25 and 700 mW** in HD mode) incl. packet loss, with spot checks at 2400 and 2450 MHz | within 2 dB of the SX1281 figure; ≤ 3 dB desense; no packet-loss increase with the derate active; no TX droop on the SX1281 supply with the D52 decoupling (BR-06) |
| V8 | Thermal: board at 25/100/max in a real frame under a canopy (derives h); k_PA = PA case − board centre at 25 mW and at max; RTC6705 case; bench still air and fan; cases of §5.4 incl. "VREF on" and patched pit; **HD hover with an O4 fitted** (RP2354A, gyro, NOR, SX1281, ESP32-PICO-V3); FC, RX and RTC6705 rail currents and the **PAOUT1 current at full drive** (levers c, e; sizes the PNP stage and its Re, BR-02) and the board temperature at R73 / R65 / Q27 at that step; **PA current at power-up after the production flow** | matches §5.4 within ±30 %; pit-on-boot verified with the RCE defaults; PA case and 85 °C parts logged; R73 / R65 inside the RC0201 derating at the measured local temperature (about 34 mW each at the Re 10 Ω top step vs 36 mW at 85 °C, 27 mW at 95 °C), else cap the ELRS power-table top count (Ic ≤ 45 mA) or Re 27 Ω |
| V9 | FC gates on RP2350 (2026.6.2+): bidirectional DShot with Bluejay BB51 at hover and full throttle (30 min) - RPM-filter notches track, no RPMFILTER arming block, decode error rate within upstream's band; **DShot at the EFM8 pin: high level scoped against 0.7·VDD and checksum failures counted with a Bluejay debug build pulsing the C2D pad (P2.0)**, fresh 4.35 V pack under load; 4-way passthrough flash and settings of all 4 ESCs; MSP-VTX from ESP32 ELRS over CRSF; ELRS boots with the VTX SPI active (layout `vtx_miso` -1, D81) and programs the RTC6705 (channel checked on a spectrum analyser); cold boot x 20 with and without the TX on (5 s MSP-VTX window); FB OSD with 2-3 target cameras PAL and NTSC (black and white levels) and with the camera unplugged; SPI NOR blackbox at 2 kHz with the ICM-42688-P at 8 kHz and FB OSD, plus erase / write / read-back with a CRC of a full log and status polling under load (reads run at 75 MHz, F7); **O4 + MSP DisplayPort on UART1 + PIOUART0 user port + LED strip on PIO1 together** (canvas refresh, arming exits the O4 low-power mode, no LED glitches); ELRS flash through serial passthrough; USB only: +BATT voltage, EFM8 brown-out cycling, +5V from USB through the mux while the back-fed boost hiccups; HD line: +3V3_VTX < 0.5 V and PA_VREF < 0.5 V with stock ELRS writing VTX SPI (BR-03); **LED strip driven direct from GPIO8** on the target strips at the 5.15 V strip supply (BR-04; README inline-diode note); power-up sequence on a scope (FT pads against the EFM8 pull-ups before IOVDD, against 3.63 V) | each passes, else its fallback (C2 pads, AT7456E/G473 respin, SPI NOR on another bus or a lower read clock for its JEDEC ID, 10 kΩ DShot series R, a 3.3 V-domain clamp or a DShot-path enable if the FT pads exceed 3.63 V, the O4 on PIOUART0 if UART1 + PIO1 conflict, a 74LVC1T45GM translator if the direct LED-strip drive fails) |
| V10 | Gyro fly-off BMI270 vs ICM-42688-P (5 + 5 boards) | release population has the lower pre-filter noise and no resonance peak in the motor band |
| V11 | Weight | ≤ 3.5 g bare |
| V12 | Crash: BetaFPV protocol, 4 boards, 20 hits | 0 failures, ears included |
| V13 | Outline and holes on Air65 II / Air75 II (25.5) and Meteor65 Pro II / Meteor75 Pro (26.0) frames with BetaFPV balls | fits all four without reaming |
| V0-USB | **Gate before the P5 freeze:** J31 pin 1 orientation by continuity on a BetaFPV SH1.0 USB adapter against the BM04B land (or a Matrix II close-up); a mirrored plug puts 5 V on board GND and −5 V on the SGM40661 IN (abs min −0.3 V) | pin 1 = GND, pin 4 = VBUS as drawn; else mirror the land before P5 |
| V1b | BEC above the published 1.5 A (D79): load step 0.7 → 1.7 A at VIN 3.0 V and 3.7 V, +5V_BST droop and recovery, loop stability with the four 22 µF COUT; the same step **in HD mode with a real O4 Lite on VHD** (its input capacitance, about 47 µF, and C12 / C13 behind the mux add to C8-C11, past TI's 40 µF feed-forward threshold, SLVSDX7D §8.2.2.4): ringing and overshoot | characterisation only; the published BEC stays 1.5 A continuous unless COUT is raised; if the HD step rings, 1.5-2.2 nF across R4 (fFFZ ≈ 2 kHz) |
| V5c | PA_VREF (LP5907-2.85, VIN 3.3 V, below its VOUT + 1 V accuracy condition) on ≥ 5 boards, cold and hot, against the SE5004L VREF H window 2.80-2.90 V | inside the window, else a VREF trim (divider) or another reference |
| V9b | HD switch-on with ELRS holding PA_EN high: PA_VREF and +3V3_VTX scoped (LP5907 VOUT ≤ VIN + 0.3 V abs max); OSD white / black level and edge sharpness against the camera picture (VIDEO_OUT loaded 1.47 kΩ DC, about 0.95 kΩ at 5 MHz and 0.60 kΩ at 10 MHz: OSD edges x0.86 / x0.80, camera x0.97; OSD sheet note) | excursion ≤ 0.7 V, < 1 ms, else C123 → 1 µF or the patched ELRS drops PA_EN on HD_EN; OSD legible, else rescale R52-R54 |

---

## 15. Risks, open questions, sourcing

### 15.1 README design questions

| README question | Status | Answer / what is still open |
|---|---|---|
| VTX part | **proposed-resolved (sourcing risk open)** | RTC6705/RTC6705A stays (no equivalent exists); PA SE5004L-R; authorised RTC6705 stock is zero, so it is a consigned, traceable broker line with incoming tests |
| Power stage | **resolved (D56, D77)** | P+N direct drive from the EFM8 (I grade) on the cell, 12x AGM210MAP (the Matrix II stage, 34 mΩ) with one 10 µF hot-loop cap per package, Bluejay layout A; release build a V2 outcome (first power-up `A_X_10_96`, then `A_X_5_96`). The TI CSD25310Q2 + CSD13202Q2 pair is the documented fallback |
| Electronics rail | **proposed-resolved** | TPS61022 forced-PWM boost at 5.15 V with 4 output caps (D15), always enabled; TPS2116 mux selects USB or the boost; calculated 1.67 / 1.82 / 1.98 A nominal peak at 2.8 / 3.0 / 3.2 V against 0.70 A analog and 1.43-1.48 A HD, published figure measured (V1); O4 on a TPS22810 switch (D15); PA on the cell; FC + RX on one LDO, RTC6705 on its own |
| Motor connection | **proposed-resolved for rev1; plugs open** | solder pads with wire-anchor holes |
| Antenna | **proposed-resolved** | RX wire monopole at the left-rear edge, trimmed to resonance; VTX U.FL at the front edge; 5.8 GHz BPF; no Wi-Fi radiator (D18 lever, §4.7) |

README constraints this spec proposes to change once accepted (README is not
edited by this freeze): mounting 25.5 x 25.5 mm → 25.75 mm pattern with Ø 3.5 mm
grommet holes; "LCSC basic parts preferred" → NextPCB partial turnkey by MPN,
JLCPCB-compatible DFM; receiver "reusing OpenRX Lite" → OpenRX-Lite RF section
with an ESP32-PICO-V3 MCU (D52); "VTX dependency" → consigned traceable RTC6705; USB → pogo
pads with a clip-on adapter (D18); digital VTX → O4 Lite pads (D13).

### 15.2 Other open questions

| # | Question | Decided by |
|---|---|---|
| O1 | SE5004L output on the cell at 2.8-4.35 V: what the lowest sample reaches at 3.0 V / 85 °C under the 27 dBm ceiling (400 mW not guaranteed at sag) | bench V5 before P4 freeze; the +5V selector position is the fallback |
| O2 | Grommet flange diameter (keepout Ø 5.2 assumed) | calipers on a BetaFPV ball before P2 |
| O3 | **Closed by D57** (JST SH USB on the board, OVP + ESD on the board). Was: clip-on USB adapter for the pogo pads (pinout, alignment-hole sizes, spring contacts; an OpenDrone accessory); it carries the VBUS hot-plug protection: a 5 V VBUS TVS and a damped bulk (≤ 10 µF at attach) at its USB-C receptacle (§4.2) | before P4 |
| O4 | JLC 6L 1.0 mm dielectric build and RF width; finished outer copper with Type VII cap plating, the min track/space and the silk minimum at that copper, both fabs | JLC stackup selector, both impedance tools and the EQ before P5 |
| O5 | **Closed by D56** (AGM210MAP chosen; D77 adds the per-package hot-loop caps). Was: D12 stage vs case (b) AGM210MAP dual: equal area by budget v3, 34 vs 40 mΩ, model 12 A bursts 5.5-7.3 s vs 1.3-4.2 s at h 80, Matrix-proven at `A_X_5_96`; LCSC-only (4,795), a consigned line like SE5004L, RP2354A and ESP32 | orchestrator / owner (D12 stands until changed); D54: not in rev1 (OC-1), stays the fallback if the CSD25310Q2 consigned buy fails |
| O6 | ELRS patches (§12: (1)-(5) gating, (6)-(8) further) | ELRS PRs; release blocked until (1)-(5) merge |
| O7 | Walsin BPF power handling at the ceiling (up to 28.5 dBm, 0.71 W at its input) | ask Walsin; VNA |
| O8 | RP2350 firmware gates (V9), including the O4 on UART1 with PIOUART0 and the LED strip on PIO1 | OpenFC-Lite-Mini + external whoop ESC bench before P5 |
| O9 | Matrix II physical teardown (layer count, HDI or not, BEC part, ball size) | buy one; it also calibrates §9 |
| O10 | 1 oz inner copper (+0.3 g, about −0.15 W at 25 A) | only if V4 misses |
| O11 | Pad-label size 0.8 / 0.6 / 0.13 (D12): breaks JLC's published 1.0 / 0.15 and LINEUP B7's 1.2 mm | **owner sign-off for this board** (the owner rule "DFM-compatible with both" is an owner rule; D12 recorded the OpenFC-H7 preference) |
| O12 | Forward arrow on silk (LINEUP B9 SHOULD, outside the owner silk list) | owner |
| O13 | ESC C2 pads unlabelled | **decided (D12)**, LINEUP B7 permits flashing test points without labels |
| O14 | Area gate | **decided (D23)**: passed on the real-placement evidence of the floorplan preview; P2 places every part and closes the via-site count. The budget (v6: 100.5 % / 92.5 % like-for-like, 107.2 % / 100.2 % corrected) and the levers of §9.3 stay P2 tools |
| O15 | 0.35 mm-pitch leadless parts: round 4 had the ESP32-D0WD-V3 (QFN-48), 74LVC1T45GS (SOT1202) and 2x BC847QASZ (SOT1216); NextPCB publishes 0.38 mm for fine-pitch ICs and 0.25 mm for BGA/LGA/QFN without saying which covers leadless parts. **D53:** BR-01 to BR-04 remove all four (ESP32-PICO-V3 at 0.5 mm, PNP drive stage, AP1606 HD gate, direct LED drive), so the EQ and the ganged-mask rule (D38, D43) are dropped once they land | **closed by D53** if the BR-01 P2 trial passes; on the BR-01 fallback a NextPCB EQ for the ESP32-D0WD-V3 alone (and the BC847QASZ on the PS-12 fallback), before P3 |
| O16 | Plated Ø 3.5 holes with a GND annulus (Matrix practice) | P2 with O2 and the ear-survival result of V12 |
| O17 | NextPCB BOM quote by exact MPN on the full BOM (HQ Online / Digi-Key stock per line, incl. TPS22810DRVR and the D52 lines: ESP32-PICO-V3 (HQ Online lists only the V3-02), SX1281IMLTRT, BC857BM,315 and RC0201FR-0733KL (stock not checked), GRM155C80J106ME11D (8 parts per board; LCSC only, S); TPS61022RWUR at 0 on LCSC is a watch item), EFM8 C2 and ESP32 programming service | **P0 close** |
| O18 | DJI O4 Wide (BetaFPV's 2026 whoops): input range and current not checked | before the README claims it |
| O19 | Decisions proposed in rounds 3-4 (TPS2116 mux, no Wi-Fi radiator, rail consolidation, LED pad sharing, floorplan moves, Bluejay start build, VTX defaults and ceiling, A2 sheet-name exception, O4 EN network, 3225 8 MHz crystal, corrected ESC cell, firmware build, leadless 0.35 mm parts, the six named D21 rules) | **logged** as D24-D44 in DECISIONS.md (round 4) |
| O20 | User UART pad group (TP0 RP0 5V GND) has no compliant top site at real size (sketch v5 free-site search; §10): (a) bottom (+20 mm² bottom; the LED strip then needs its own GND), (b) left edge below M3 as in the floorplan preview with the antenna-root spacing cut from 6 to about 3.6 mm and V7 measuring it with wires fitted, (c) owner lever: shared HD/user GND pad | P2 (with the owner if (c)) |

### 15.3 Sourcing plan

Full turnkey at NextPCB under D60: NextPCB sources every line that exists by exact
Manufacturer + MPN (genuine parts only) and builds the prototypes; stock gates and
consignment no longer block a part, and JLCPCB is a DFM target only. The NextPCB BOM
quote (O17) is therefore a **per-line check**, not a consignment list: each line is
either confirmed by MPN or gets a decision (substitute, land change or owner call)
before the board is frozen. Generated from `hardware/bom_plan.json` (P4 critique
round 3, 2026-10-10): 82 BOM lines, 236 placements.

| Line (quote check first) | Qty / board | Why it may stall | If the quote misses it |
|---|---|---|---|
| Puya PY25Q128HA-DFH-IR | 1 | MPN in the Puya DS Rev 2.0 ordering table (-DFH-IR / -DFH-KR) but no distributor listing found (LIBRARY.md, web 2026-10-10) | **resolve before the board freeze**: both fallbacks (PY25Q128HA-QVH-IR, GD25Q128EQIGR C84018) are USON-8 4x4 and need a fallback land plus a placement change (SCHEMATIC.md open item) |
| AGMSEMI AGM210MAP | 12 | LCSC-only (C7431169), the Matrix II stage | NextPCB buys it through LCSC / the AGMSEMI channel by MPN (D60); else the TI pair fallback stage (D12 / D56, schematic + layout change) |
| RichWave RTC6705 | 1 | no authorised stock (LCSC C913074 listing, zero stock) | traceable broker or agent; incoming test on 3 (SPI register read 0x00 = 0x0190, frequency within ±200 kHz, PAOUT1 power) |
| SG Micro SGM40661YG/TR | 1 | no LCSC number recorded; SG Micro channel | quote confirms the exact MPN (WLCSP-6 land) |
| Alps Alpine SKUBAAE010 | 1 | no LCSC number; Alps distributor listing | quote confirms (D65: the smallest tact switch NextPCB can source; any other part needs a land change) |
| Diodes Incorporated SDM02M30CLP3-7B | 1 | no LCSC number; distributor listing active (S) | quote confirms |
| Johanson Technology 2450AT07A0100001T | 1 | no LCSC number (Johanson channel) | quote confirms; the lineup reference 2450AT18A100E (OpenRX-Lite-UFL) is larger |
| Silicon Labs EFM8BB51F16I-C-QFN20R | 4 | no LCSC listing; Digi-Key, 24 wk factory lead | quote confirms; NextPCB pre-programs Bluejay before reflow (D67) |
| Texas Instruments LP5907SNX-2.85/NOPB | 1 | no LCSC listing (TI / Arrow) | quote confirms |
| Skyworks SE5004L-R | 1 | LCSC C210263, not on HQ Online (track 04) | quote confirms a channel |
| Raspberry Pi RP2354A | 1 | LCSC C41378174, not on HQ Online (track 04) | quote confirms a channel |
| Espressif ESP32-PICO-V3 | 1 | HQ Online lists only the ESP32-PICO-V3-02 (same pins for this board, P4-14) | the quote may fill either |
| Semtech SX1281IMLTRT | 1 | HQ Online stock was below the run quantity (2026-10-09) | quote confirms |
| Standard passives without an LCSC number recorded: BLM03PX121SN1D, GRM0335C1H101JA01D, GRM0335C1H330JA01D, RC0201FR-07150RL, RC0201FR-0718KL, RC0201FR-071K2L, RC0201FR-071KL, RC0201FR-07270RL, RC0201FR-0727K4L, RC0201FR-0727RL, RC0201FR-07287RL, RC0201FR-0733KL, RC0201FR-0747KL, RC0201FR-07510KL, RC0201FR-07560KL, RC0201FR-076K2L, RC0201FR-07820RL, RC0201JR-070RL | per BOM | Murata / Yageo catalogue parts | quote confirms the exact MPN (Yageo RC0201FR-07 of the same value is the same part) |
| DNP lines (not assembled: plug-ready motor headers, Wi-Fi pi-match shunts): Molex 53047-0310 (4 DNP); Murata GRM0335C1H1R2BA01D (2 DNP) | 0 | - | - |
| Everything else: 2450FM07D0034T, ABM8-272-T3, AOTA-B201610S3R3-101-T, AP1606, BAS16LD,315, BC857BM,315, BM04B-SRSS-TB(LF)(SN), BMI270, CC0201JRX7R9BB471, CL05A105KA5NQNC, CL05A475MP5NRNC, CL10A226MO7JZNC, FTC252012SR68MBCA, GRM0335C1H100JA01D, GRM0335C1H150JA01D, GRM033C81E104KE14D, GRM033R60J474KE90D, GRM033R61A105ME44D, GRM033R71A103KA01D, GRM033R71H102KA12D, GRM155C80J106ME11D, GRM188C80J226ME15D, HCS1206FTL500, INA186A3IDCKR, LP5912-3.3DRVR, LQP03TN4N7H02D, NCP03XH103F05RL, OW7EL89CENUNFAYLC-52M, RC0201FR-07100KL, RC0201FR-0710KL, RC0201FR-0710RL, RC0201FR-07680RL, RC0201FR-0775RL, RC0402JR-070RL, RFBPF1608060K98Q1C, RTT012401FTH, SDM02U30LP3-7B, SM03B-SURS-TF(LF)(SN), SMF5.0A, SN74LVC1G3157DTBR, TAXM8M4RDBCCT2T, TLV7031DPWR, TPD2EUSB30DRTR, TPS2116DRLR, TPS22810DBVR, TPS61022RWUR, TPS7A2018PDQNRM3, U.FL-R-SMT-1(80), XL-1005UBC, XL-1005UGC, XL-1010RGBC-2812B | per BOM | LCSC-listed, standard | turnkey; the quote confirms each MPN |

NextPCB EQ list (one submission): filled and capped via-in-pad (Type VII, through vias only) in
0201 / QFN / LGA / AGM210MAP pads (D34, §8.3); the min track/space and the silk minimum at the
finished outer copper (O4); 3D / CT X-ray for stacked exposed pads and LGA fields on opposite
sides (D70, §11); second-side support for the U.FL and the 2520 inductor (§11); panel rail
fiducials sufficient for 0201 (§7); the AGM210MAP two-EP land with the phase island joining both
drain pads (§4.3); EFM8BB51 pre-programming with Bluejay before reflow (D67, §12.1).

NRE estimate for 10 boards (I, track 07 prices): PCB 6L 1.0 mm with 0.20 mm vias and Type VII
about $220; double-sided assembly $105 plus joint and X-ray fees (about $50-150); parts about $600
including the broker RTC6705s; EFM8 pre-programming (a quote item); freight $50-100: **about
$1,050-1,250** plus the programming fee. No programming fixture: the RP2354A loads over USB
BOOTSEL, the ESP32 through Betaflight passthrough with SW1 held, and the C2 test vias are the bench
recovery contacts (D57 / D67, §12.1). Lead time about 4 weeks door to door (external parts case).

### 15.4 Risks carried

| Risk | Mitigation |
|---|---|
| Area: budget v6 100.5 % / 92.5 % like-for-like (107.2 % / 100.2 % with the round-3 allowances); the floorplan preview that passed D23 used the round-3 ESC cell | D23 (P2 real placement is the proof); the corrected cell's sites are top-only or bottom-only, which eases the preview's both-side via-site shortage; side balancing (O4 switch to the bottom) and the owner levers of §9.3 |
| Routing closure with through vias only at this density; about 45-50 nets barred from In2/In3 | P2 channel-capacity probe; counted vias, far-side landings and channels in budget v4; relaxing the L3 ban for slow digital buses is a lever |
| ESC bursts shorter than the Matrix stage (model 12 A for 1.3-4.2 s vs 5.5-7.3 s at h 80) | measured in V4 and published; case (b) documented (O5) |
| AGM210MAP dead time at EFM8 port drive and Cdv/dt on the N gate (§4.3) | first power-up on `A_X_10_96`; `A_X_5_96` (Matrix II) after the V2 shoot-through check |
| Boost overload between the published load and current limit saturates the 2520 inductor (no peak limit) | slew-limited O4 inrush; V1 overload step; Coilcraft XGL4040-681 fallback (+10 mm²) |
| HD mode: video drops at the shed threshold (2.74-3.14 V) on deep sag and stays off until the cell recovers to 3.23-3.82 V (hysteresis, no cycling); O4 inrush and canopy heat not published | V1 (thresholds with ESC ripple, inrush), V8 (HD hover); README |
| LED strip and PIOUART0 on PIO1 untested upstream | V9; fallback: the O4 on PIOUART0, user UART on UART1 (study option A) |
| RTC6705 fake or remarked parts | traceable source, incoming tests (register read by the test application), 10 spares from the same lot |
| Overvoltage on unplug with spinning props: EFM8 (5.5 V), SE5004L (6 V), TPS61022 (7 V), TPS2116 (6 V), LP5912 (7 V) and the 6.3 V MLCCs exceed their ratings above about 5.5-7 V; the AGM210MAP stage stays in rating at the 9.2 V clamp (VDS 20 V, VGS ±12 V, EAS 36 / 49 mJ; Matrix parity topology; the TI fallback pair's 12 V N and ±8 V gates would not) | V3b measures the surge, the TVS energy and the phase-node VDS; README: disarm (props stopped) before unplugging |
| EFM8 VDD near its 5.5 V abs max under regen or hot-plug of a fresh LiHV pack | V3c; braking limits, then the VDD resistor; damping bulk at the pads for hot-plug |
| Reversed user-fitted pigtail loses the board | silk + README; factory fit priced at P7 |
| USB ESD | closed by D57: TPD2EUSB30 at J31 + the 27 Ω series resistors |
| USB hot-plug ringing on VIN1 (6 V abs max mux) | SGM40661 OVP on VBUS (D57; simulated ring ≤ 10.8 V at its 28 V IN) + 10 µF X6S at VIN1; V1 VIN1 ≤ 6.0 V; a non-compliant 5.5-6.12 V source passes before the OVLO trips (README) |
| J31 pin 1 orientation inferred from the BetaFPV label | gate V0-USB before the P5 freeze (§14) |
| ELRS Wi-Fi (D58) peaks +3V3 at about 0.48 A (LP5912 500 mA) | bench-only update mode, disarmed (README) |
| RP2350 Betaflight features weeks into a release; DShot decode error band; single core; camera-dependent OSD | V9 gates on existing house hardware before P5; G473 fallback documented; README: bench OSD needs a camera |
| ESP32 strap pins near VTX control (GPIO2; GPIO12 after D53 unconnected) | GPIO2 drives the LP5907 EN directly and reads low at reset through its own strap pull-down and the LP5907's internal 1 MΩ (BR-12); `vtx_amp_pwm` moved to GPIO13 (no strap), so GPIO12's internal pull-down alone holds the 3.3 V-flash strap and the eFuse burn is optional (§4.7, §12.1) |
| ESP32-PICO-V3 (85 °C) needs a site outside the PA projection and the FET groups (D52 BR-01) | placed in floorplan v3 (D61); the ESP32-D0WD-V3 fallback is withdrawn (D55); D69 removed the 85 °C halo rule |
| PNP PA drive feeds PAOUT1 in current mode against a "TBD" datasheet current (D52 BR-02) | P4 SPICE with `research/bomred/verify/pnp_fix.py` and the V8 PAOUT1 current before the schematic freeze; Re starts at 10-15 Ω, V5 sets it; fallback PS-12 + PS-14 |
| LED strip driven at 3.3 V into a WS2812 on 5.15 V (VIH 3.6 V; D52 BR-04) | Matrix II parity (direct drive); README inline-diode note; V9 strip test; 74LVC1T45GM fallback |
| Leaner decoupling (D52 BR-05 to BR-17) and the LP5912 10 µF COUT maximum | each cut rests on a datasheet minimum or a shipped reference; P4 sums +3V3 and +3V3_VTX COUT with maker curves (§15.5 P4-12); V3c (bus), V5 (video SNR, 6.5 MHz spur), V7 (TX droop), V10 (gyro noise) |
| PA heat on the bench and when disarmed with VREF on (stock ELRS) | RCE defaults with low-power disarm OFF (§4.8), ELRS patches (O6), README bench-fan rule until merged |
| `400` level open loop until O6 gate 2 | 27 dBm hardware ceiling; "max (measured, power-limited)" published per board |

### 15.5 Deferred to P4 schematic review (D22)

D22: P0 passes with no BLOCKER and every decision applied; circuit-detail items
that need the drawn schematic are closed in the P4 schematic critique loop,
which must itself end with no BLOCKER or MAJOR. Every item below has its
topology and parts fixed in this spec; P4 settles the values against the
drawn sheet and runs the check. Owner: **P4** (schematic author, then the P4
critique round); a bench item named in the check is the confirmation, not the
decision. D52-D54 (BOM reduction) updated P4-1 to P4-10 and added P4-12 to
P4-19: the open items of BOM-REDUCTION §7 (its decision-log item is closed by
D52-D54) and the gated items BR-02 (P4-5), BR-17 and BR-20.

| # | Item (spec section) | From | Owner | Check to run at P4 (pass criterion) |
|---|---|---|---|---|
| P4-1 | O4 switch EN network: 33k/18k divider, 510 kΩ hysteresis from +5V_HD, 100 nF EN filter, BAS16LD (anode EN, cathode GPIO27), 2.4 kΩ on GPIO27, CT 10 nF, QOD tied to VOUT, CIN 1 µF on `+5V_BST`; no USB term (§4.2; D53 BR-10, BR-22, BR-24) | r3 #0/#34, #1/#17, consolidation, r4 (EN filter, hysteresis), D53 | P4 | hand calculation on the drawn net with 1 % resistors and +5V_HD 4.93-5.37 V: EN ≤ 0.87 V with GPIO27 low or undriven (recompute the reset clamp once with the 2.4 kΩ, BR-24) and on USB only at the back-fed 2.5-2.8 V plus 0.3 V ripple; shed 2.74-3.14 V falling (on 3.23-3.82 V rising) with BAS16LD leakage at 105 °C; resistor-only hysteresis ≥ the 0.31 V cell rebound (0.333 V calculated) and switch-on ≤ 3.8 V (a storage-charged pack starts the O4); 96 kHz ripple at EN ≤ 1 mV; the filter discharges through the diode and the 2.4 kΩ within 1 ms; τ (1.1 ms) inside 1-10 ms against the punch-sag ride-through; netlist script: the EN net holds exactly the divider, the hysteresis resistor, the filter, the diode and the TPS22810 pin. V1 confirms the shed and switch-on points with one ESC loaded (ripple present) and the absence of cycling |
| P4-2 | O4 supply ahead of the mux (D53 BR-10; replaces round 4's AP1606 USB term): TPS22810 VIN on `+5V_BST` at TPS2116 VIN2, so USB never reaches the O4 (§4.2) | r3 #0/#34, D53 | P4 | netlist script: `+5V_BST` holds only the boost output and its caps, the FB divider, TPS2116 VIN2, the TPS22810 VIN and its CIN; the TPS2116 reverse-current blocking on the unselected VIN2 read from SLVSFG1A for the USB + cell case; one shared CIN if P5 brings VIN2 and the switch VIN within about 2 mm. V1: USB + cell + HD mode, no current from +5V_USB into `+5V_BST` |
| P4-3 | TPS2116 sheet: MODE tied to VIN1, PR1 27.4k/10k (3.44-4.04 V; 3.3k/1.2k with the PS-12 fallback, PS-14), ST left open (open drain, unused), 10 µF X6S at VIN1 next to the pin (GRM155C80J106ME11D, D52 BR-20; TI CIN, §9-10), +5V hold-up (10 µF at the mux + the shared 10 µF LDO CIN of BR-14, recounted effective) for the unplug dip; adapter-side VBUS TVS and damped bulk in the O3 adapter spec (§4.2) | r3 #0/#34, consolidation, r4 (VIN1 transient), D52 | P4 | ERC; hand calculation of the switchover dip at 0.7 A: +5V ≥ 3.1 V, +3V3 ≥ 2.9 V; VIN1, MODE and PR1 peak on a 0.5-1 µH cable through the adapter and on pogo bounce ≤ 6.0 V (damping ratio stated with the 10 µF part); board VIN1 plus adapter bulk inside USB's 10 µF attach limit; RCB events interrupt only near-zero current here (switchover at plug and unplug, I), so no output clamp beyond the hold-up; V1 case (b) scopes the dip and the VIN1 peak |
| P4-4 | HD gate (D53 BR-03): AP1606 gate on HD_EN, drain on the +3V3_VTX LP5912 EN (100 kΩ to +3V3, GPIO21 through 1 kΩ: P4 ruling, EN < 0.3 V guaranteed), source GND; the 1 kΩ VTX SPI series resistors; the LP5907 on `+3V3_VTX` with EN straight from GPIO2 (§4.8) | r3 #36, D53 | P4 | hand calculation: AP1606 Vgs(th) minimum from the maker datasheet above the 0.2 V reset level on GPIO27 and its RDS(on) at 3.3 V holding the LP5912 EN below VEN low against the 100 kΩ and GPIO21's push-pull high through 10 kΩ; SPI edge (1 kΩ x pin and trace capacitance) inside the RTC6705 setup and hold times; LP5907 VIN + 0.3 V excursion at HD turn-off bounded; V9: +3V3_VTX and PA_VREF < 0.5 V with stock ELRS writing |
| P4-5 | PA drive stage (D52 BR-02): BC857BM PNP, emitter through Re to `+3V3_VTX`, collector → R65 10 Ω → choke → PAOUT1; two-pole RC 2x 1 kΩ / 2x 1 µF from GPIO13; Re starts at 10-15 Ω (§4.8) | r3 #19, #47, D52 | P4 (SPICE gate before the schematic freeze; V8 measures the PAOUT1 current) | SPICE against `research/bomred/verify/pnp_fix.py` (not the first `pnp.py`, whose base-current sign is reversed) with a PAOUT1 load model: 25 and 100 mW mid-window with ≥ 20 real duty steps between them; YOLO current against the 27 dBm ceiling across hFE 220-475 and the Veb tempco; PNP dissipation below Ptot derated at 85 °C; reset and boot behaviour with GPIO13 undriven; both junctions reverse-biased in HD mode. Fail: PS-12 values on the two-NPN stage plus PS-14 (§4.8). V5 sets Re |
| P4-6 | ESP32 straps and pins (D53): GPIO12 unconnected (internal pull-down holds the 3.3 V-flash strap), GPIO2 straight to the LP5907 EN (internal 1 MΩ, no external pull-down, BR-12), GPIO0 = RX_BOOT through D8 to the shared button SW1 (D65; the RXB pad is removed, D67); `vtx_amp_pwm` GPIO13 and `vtx_mosi` GPIO14 (no straps), `vtx_miso` -1 written explicitly (D81); ESP32-PICO-V3 pins 30/31 (in-package flash) and the NC pins left open; VDD_SDIO eFuse step optional (§4.7, §12.1) | r3 round-2 carry-over, D53 | P4 | netlist strap script: each strap's reset level from its pull network with the ESP32 internal pulls; the PICO symbol leaves pins 25, 30, 31, 35, 36, 44, 45, 47 and 48 unconnected; the board's ELRS layout JSON matches the drawn pins; production step 2 in the fixture plan |
| P4-7 | TPS61022 sheet: FB divider 47k / 6.2k for 5.148 V with 1 % parts against VFB 585/600/615 mV (D52 BR-23), MODE to VOUT, EN tied to VIN (BR-11), 4x Cout, Cin (§4.2, §5.3) | r3 #35, D52 | P4 | hand calculation: worst-case setpoint 4.93-5.37 V; bottom resistor < 300 kΩ (TI); MODE high above 1.2 V with VOUT > 2.2 V; EN on the VIN net and nothing else |
| P4-8 | EFM8 channel: VDD straight to the cluster +BATT with 100 nF X6S at the pin and the cell's 22 µF ≤ 3 mm from VDD pin 4 (ESC1/2/4, D52 BR-05); ESC3 with its own 0402 (P4-19); DShot 2.4 kΩ series, RSTb internal pull-up, BEMF 6x 0201 against Bluejay layout A, no gate resistors (0 Ω options if P2 has room) (§4.4) | r3 #45, #13, D52 | P4 | netlist against `Layouts/BB51/A.inc` pin use; the BR-05 placement condition as a sheet note; DC-bias curve of the ESC3 part (P3); DShot pin current at a 2.5 V cell (VDD + 0.3 V limit, 2.4 kΩ) stated in the sheet note |
| P4-9 | Current sense: four-pad Kelvin shunt land as a net-tie, `SHUNT_SENSE_P/N` only at the inner pad edges and the INA186 inputs, input RC from the OpenESC sheet moved to 0201 without its two common-mode caps (D52 BR-07: 1 kΩ + 1 kΩ, 1 µF differential, 80 Hz) (§4.1) | r3 #10, D52 | P4 | netlist script: the Kelvin nets touch only the shunt sense pads, the RC and the INA186; net class Analog; In2/In3 ban active (DRU); the `ibata_scale` check on the first boards catches any offset |
| P4-10 | OSD front end: level divider scaled about 5x down (top 750-820 Ω, Thevenin about 190 Ω, OSD_W ≤ 3 mA), sync comparator threshold, SDM02U30LP3 clamp, one shared 100 nF X6S between the switch and the comparator (D52 BR-13) (§4.8) | round-2 carry-over, D52 | P4 | hand calculation of the OSD levels against the RTC6705 video input; V9 black and white levels on the target cameras |
| P4-11 | FT pads and power-up sequence: DShot and UART pads driven before IOVDD, EFM8 pull-ups against 3.63 V (PINMAP F16) | r3 round-2 carry-over | P4 | sheet note with the worst-case pad voltage; V9 scope at power-up |
| P4-12 | +3V3 and +3V3_VTX output capacitance against the LP5912 COUT maximum of 10 µF (BOM-REDUCTION §7 item 1, §6 items 9 and 14): after D52 +3V3 holds about 19 µF nominal (9-10 µF effective, I) and +3V3_VTX about 12.3 µF nominal (5-6 µF effective, I) | D52 (§7) | P4 | sum each rail's effective capacitance at 3.3 V from the maker DC-bias curves with tolerance: inside 0.7-10 µF; next levers PS-O6 (delete the 1 µF at the SX1281), a TLV75533PDRVR in place of the +3V3 LP5912, or dropping the +3V3_VTX 1 µF when its 10 µF sits at the LDO |
| P4-13 | X5R parts still inside the H1/H3 zones after D52: C5, C14, C68, C56, C57, C105, C87 and C2 (C80 left with BR-01) (§7 item 2) | D52 (§7) | P4 (P3 parts, P5 positions) | each gets an X6S / X7R part (P3) or a position outside the zone (P5); one 1 µF X6S 0201 (GRM033C81A105ME05D, P3 confirms) for the whole 1 µF line keeps the line count; C2 moves ≥ 2 mm from its FET unless PE-8 lands after V3c |
| P4-14 | Orderability of the D52 lines (§7 item 3): GRM155C80J106ME11D now carries 8 parts (LCSC C237279, S; no Digi-Key listing); BC857BM,315 and RC0201FR-0733KL stock not checked; HQ Online lists only the ESP32-PICO-V3-02; TPS61022RWUR 0 at LCSC | D52 (§7) | P4 (with O17) | stock per line at NextPCB channels before the BOM freeze; a second source or the consigned list for each line that fails the gate; the PICO-V3-02 confirmed as the alternate for this pin use (pins 28/29 unused) |
| P4-15 | RX RGB LED XL-1010RGBC-2812B on +3V3, below its 3.5-5.5 V supply range (inherited from OpenRX-Lite-UFL; §7 item 4) | D52 (§7) | P4 | decide and record in the RX sheet note: keep on +3V3 with a datasheet or bench check of data and colour at 3.3 V, move it to +5V with a data level it accepts, or change the part |
| P4-16 | RTC6705 supply details (§7 item 5, §4.8): pin 40 (LDD2V5) without the reference's 51 Ω + 1 µF filter; the 100 pF (C103) at PAVDD/BUFVDD (pins 31/32); REG1D8 (pin 26) without a capacitor and pin 17 open as decided (BR-15, BR-16) | D52 (§7) | P4 | the drawn sheet against OpenOSD-X v1.01 pin by pin for pins 17, 23, 26, 31, 32 and 40; V5 video SNR and no 6.5 MHz spur confirm |
| P4-17 | Placement conditions of the D52 set, carried as sheet notes for P5 (§7 item 8): BR-01 P2 trial; BR-05 0603 sites ≤ 3 mm from EFM8 VDD; BR-08 the RP2354A pin-53/54 cap ≤ 1 mm from pin 54 and the pin-44/45 cap at pin 44; BR-09 LDO orientation (OUT toward BMI270 pin 8); BR-13 one cap between the OSD switch and the comparator; BR-14 one CIN between the two LP5912 IN pins; BR-03 the LP5907 CIN C122 is CL05A475MP5NRNC at U22 IN (applied in the P4 critique round 3, +0.3 mm² top; P5 condition: same side, ≤ 1.5 mm) | D52 (§7) | P4 (sheet notes); P5 places | every condition is a sheet note next to its part; the P5 check script lists each with its measured distance |
| P4-18 | PA output DC block C119 (D52 BR-17, gated): delete or keep (§4.8) | D52 | P4 | SE5004L datasheet (RFOUT internal DC shunt; only RFIN "DC block required") plus an EM check of the output match without the 10 pF; decided at P4, no DNP footprint on the RF line |
| P4-19 | ESC3 EFM8 cap C30 at 10 µF (D52 BR-20 condition; §4.4) | D52 | P4 critique | the critique rules whether a 10 µF EFM8 decoupling cap at ESC3 counts as ESC local bulk under the gyro 5 mm bulk-MLCC rule (§11); if it does, C30 stays the 2.2 µF GRM155C81A225KE11D and BR-20 saves 0 lines |

### 15.6 Carried to P2 and P3

| Item | Where it is settled |
|---|---|
| Pad-group interiors, passives fill, routing channels and far-side via landings; the area gate (O14) | P2 probe |
| Panel tab positions (sketch v5: T1 right edge y −6.6, T3 left edge y −8.9, T4 rear edge x −9.3; hard checks in the P2 placement script), pogo hole sizes and the adapter (O3); rule-area positions (`setup_board.py` uses the sketch v4 values; T1 and the VTX chain start follow sketch v5 at the next P1 re-apply) | P2 |
| Real-footprint X-ray, H1-H3, N1, iron-rework (0.5 mm, all parts), pad-group and tab checks (sketch v5 rules on the placed board); the user UART group site (O20) | P2 script |
| Merged FET lands (P source, N drain) with Type VII vias, vias in the strip and pin-3 pads; both FET symbol-to-footprint pin maps checked against the datasheet top views (D23) | P3 (land), EQ |
| DC-bias curves of the ESC3 EFM8 cap (10 µF GRM155C80J106ME11D or 2.2 µF GRM155C81A225KE11D, P4-19) and the other D52 capacitors (P4-12); an exactly-8 MHz 2520 crystal; the 40 MHz crystal's temperature range only on the BR-01 fallback | P3 |
| **BR-01 placement trial** (D52 gate): ESP32-PICO-V3 ≥ 2 mm outside the PA projection (bottom keep-out x 4.32..12.72, y −13.4..−5.0 mm) and ≥ 2 mm from the FET groups, check_spacing 0, bottom front quadrant re-planned; pass keeps BR-01, fail takes the §5.1 fallback of BOM-REDUCTION | P2 |
| D52 library parts: ESP32-PICO-V3 symbol and footprint (QFN-48 7x7, NC pins 25, 35, 36, 44, 45, 47, 48 and the flash pins 30/31 left open); BC857BM (SOT883; may share the AP1606-class land); SX1281 from the OpenDrone library with the pin-5 GND fix; the new passive lines GRM033R71A103KA01D and RC0201FR-0733KL (the other D52 values reuse existing lines) | P3 |
| Antenna-hole footprint named `AE*` so the scoped D21 rule applies; trimmed footprints as their own project-library footprints | P3 |

### 15.7 Round-3 BLOCKER and MAJOR findings: disposition

Round 3 (`r3_issues.json`, 3 BLOCKER and 20 MAJOR) against this revision. All
23 are fixed in the spec; three leave value checks in §15.5; none is rejected.

| Finding | Severity | Disposition |
|---|---|---|
| #0, #34 USB sense FET back-fed through the Schottky, boost shut down when warm | BLOCKER | fixed: TPS2116 mux, boost always on (§4.2); this revision also corrects the IREV "maximum" (typical only), lowers the PR1 divider to 37.4 kΩ, and replaces the PINIO Schottky on the O4 EN by a BAS16LD (same leakage failure class); values P4-1 to P4-3 |
| #33 D13-D20 not applied | BLOCKER | fixed: §1, §3, §4.2, §4.8, §4.10, §5, §9, §10, §13, PINMAP, COMPETITION, budget v5 |
| #1, #17 D13/D14 missing (O4 pads, UART, PINIO, load switch, HD load, `USE_OSD_SD`) | MAJOR | fixed: UART1 / PIOUART0 / PINIO1 (PINMAP §5.1), TPS22810 with cell threshold and PINIO, 4th Cout, HD load rows, inductor overload and V1 step |
| #2 D14 cuts not applied | MAJOR | fixed: camera pads, NOR (none stocked), regulator consolidation, pad trimming, then D18 pogo USB and no Wi-Fi (§9.2 steps); logging in DECISIONS.md is O19 |
| #3 N-side dead time and Cdv/dt | MAJOR | fixed: §4.3 both sides, start build `A_X_15_96`, V2 criteria |
| #4, #23, #37 X-ray check on 55 % cores | MAJOR | fixed: sketch v4 on datasheet pads and full LGA fields, NOR pad trimmed, 0 fails |
| #5, #21, #38 85 °C parts and the RTC6705 inside the ESC quarters; no same-side rule | MAJOR | fixed: rules H1-H3, N1 (§11) on both sides, sketch v4 0 fails, V4 thermocouples |
| #18 VTX defaults cleared by ELRS | MAJOR | fixed: production flow and RCE + low-power-disarm OFF defaults (§4.8, §12.1) |
| #19 "400 mW at the limit" criterion | MAJOR | fixed: 27 dBm power ceiling, 1.9 W heat rows, O7; divider set in V5 (P4-5) |
| #20 no room for the PA passives | MAJOR | fixed: PA ring, match and DC-block zones in sketch v4 and the budget |
| #22 Wi-Fi radiator without a place | MAJOR | fixed: no radiator (D18 lever 2), `WIFI_STUB` removed |
| #24 PICO-V3 fallback is an 85 °C part | MAJOR | fixed: rating stated, no place in sketch v4, O15 EQ required before P2 |
| #35 HD load overloads the BEC | MAJOR | fixed: HD column, LED strip and user 5 V not budgeted in HD mode, TJ at the real location, CT slew, V1 steps |
| #36 D17 circuit undefined | MAJOR | fixed: HD gate topology and firmware contract (§4.8); values P4-4 |
| #39 boost under the FET rows | MAJOR | fixed: moved out (rule H2, 2.0 mm) |
| #40 budget understated | MAJOR | fixed: far-side landings, channels, side vias, 3225 crystal, B4 name in budget v4/v5; the result fails D20 (status item 1) |
| #41 board fiducials against LINEUP B16 | MAJOR | fixed: rail fiducials only, EQ question (§7) |

### 15.8 Round-4 BLOCKER and MAJOR findings: disposition

Round 4 (3 BLOCKER, 7 MAJOR), each verified against its source before the fix.
None rejected; two circuit-detail MAJORs leave value checks in §15.5.

| Finding | Severity | Verified against | Disposition |
|---|---|---|---|
| CSD25310Q2 pinout reversed (source, not drain, on the exposed pad) | BLOCKER | SLPS459C page 1 Top View and §4.2 thermal figure (local copy) | fixed: §4.3 cell re-derived (P source land with 4 in-pad +BATT vias, phase field outside the P land landing in the N drain land, in-pad GND vias in the N source strip, leg cap with its own +BATT via, P gate via pin 3 on L6), loop through L4 about 1.5-2 mm², thermal term reasoned, §8.3, §11, §15.3 EQ, §15.6, §16; budget v6 13 / 6 sites per phase; sketch v5 phase strips; D36 |
| TPS22810 EN/UVLO unfiltered on the ESC ripple, no guaranteed hysteresis | MAJOR (circuit) | SLVSDH0C §9.3.3 and the VENR / VENF table | fixed: 100 nF EN filter, 1.5 MΩ hysteresis from +5V_HD, divider 90.9k/49.9k (shed 2.80-3.09 V, on again 3.26-3.75 V), §4.2; P4-1 and V1 extended; D34 |
| TPS2116 VIN1 without input capacitor or transient margin | MAJOR (circuit) | SLVSFG1A §6.1, §9, §10; OpenFC-Lite-Mini power sheet (DSK24, 22 µF) | fixed: 2.2 µF X6S at VIN1; the VBUS TVS and damped bulk go on the clip-on adapter (O3) because a 5 V TVS breaks down above the mux's 6 V; V1 VIN1 ≤ 6.0 V, board RC-snubber fallback; P4-3; D24 |
| `VTX_MSP_UART` overwrites the RX_SERIAL default on 2026.6.2 | MAJOR | Betaflight 2026.6.2 `serial.c` L316-321, L353-358, L541-544, `config.c` L230, `vtx_msp.c` | fixed: define removed (PINMAP §5.1, F2, verification #7); §12.1 applies the UART0 mask before the ELRS vtxtable boot; D37 |
| `USE_OSD_HD`-keyed defaults and the include order | MAJOR | `platform.h` (config.h before common_pre.h), `common_pre.h` L249-253 / L452-455, `pg/vcd.c`, `osd.c` L418-427, `init.c` L947 | fixed: defaults per build type (PINMAP §5.1 table), production build named (OSD (SD) only), analog preset in step 4 and the shipped diff, README statement; D37 |
| D20 gate not met, rationale inconsistent | BLOCKER | `budget_v5.py` rerun (625.27 / 624.57 mm², 7.42 / 6.72 over), `budget_v3.py` calibration (842 + 394 mm² = 96.1 %) | resolved by the orchestrator's D23 (real-placement evidence); §9.2 numbers and the calibration rationale corrected, budget v6 rerun, O14 closed. BUILD-PLAN's P0 row is outside this file and still cites D20 |
| D21 rules and proposed decisions not logged | BLOCKER | DECISIONS.md (ended at D23) | fixed: D24-D44 appended (one row per O19 item, one per named D21 rule, D35 superseding D12 item 3 for the 8 MHz crystal); status item removed |
| Panel-tab keepouts contain parts | MAJOR | `setup_board.py` TABS / `tab_rect()`, sketch v4 | fixed in the spec and sketch v5: T1 re-sited to the right edge (the PA land and ring sit inside every arc position), pad bulk 1.0 mm inboard of T4, tabs as hard checks (0 fails); `setup_board.py` takes T1 at the next P1 re-apply; D28 |
| Sketch blocks smaller than their contents; O4 land; iron-rework distance to ICs | MAJOR | budget `lab()`, TPS22810 DBV land, DRU iron rule | fixed: sketch v5 draws the groups from the real geometry and the O4 block with the DBV land (moved to the left-centre region), iron rule extended to all parts (D29); 0 fails for parts, tabs and three groups; the user UART group has no compliant top site, open as O20 |
| 74LVC1T45GS and BC847QASZ at 0.35 mm pitch outside the fine-pitch rule; wrong GN fallback | MAJOR | Nexperia package pages SOT1202, SOT1216, SOT1115, SOT886; NextPCB assembly page | fixed (option a): both in the O15 EQ and the ganged-mask rule, 0.5 mm-pitch fallbacks 74LVC1T45GM and BC847BV, GN fallback removed; D38, D43 |

---

## 16. Sources (load-bearing claims)

| Claim | Source | Status |
|---|---|---|
| Matrix II size, holes, thickness, weight, 3-point mount, crash test, pad set, Wi-Fi chip antenna | BetaFPV product page and JSON; photo measurements (01 §2-§3.5, 00) | V |
| Matrix II ESC: 4x EFM8BB51, 12x AGM210MAP, Bluejay A_X_5_96, "12 A / 18 A" | photos + product JSON + Bluejay source (01 §3.2, 03 §2) | V |
| CSD25310Q2: Rds, Qg 3.6/4.7 nC, Vth −0.55/−0.85/−1.10 V, Rg 1.9 Ω, RθJC 4.5 K/W, ±8 V; **source on the exposed pad (pad 8) and pins 1, 2, 5, 6, drain on pin 4 and the strip pad 7, gate pin 3** (page 1 Top View; the §4.2 thermal figure puts its 1 in² copper on the source; round 4 corrected the reversed pinout of earlier revisions) | TI SLPS459C (local copy `dl/esc03/csd25310q2.pdf`, page 1 re-read 2026-10-07) | V |
| CSD13202Q2 pinout (drain on pad 8 and pins 1, 2, 5, 6, source on pin 4 and strip pad 7, gate pin 3), RθJC 6.4 K/W, Qg 6.6 nC max, RG 1.4 Ω max, Vth 0.58 V min, Crss, EAS 20 mJ, DQK land pad 8 1.0 x 0.95, pad 7 0.75 x 0.3, pins 0.45 x 0.3 mm; AGM210MAP values incl. RθJC 3.5 K/W | TI SLPS313A; AGM210MAP VER2.72 (track 01/03) | V |
| Two FETs in series, P+N conduction model, PA-case term, bursts to 110 °C with footprint-scaled spreading, HD mode, VTX ceiling, heat levers, dead time both sides | `calc/thermal_v3.py` (inputs V, model I; v2 kept) | V / I |
| Convection h 30-80 W/m²K (0.042-0.11 W/K) | 03 verification #15; 06 §4 | I |
| EFM8BB51 VDD 1.8-5.5 V (abs max 5.5 V), VOH high/low drive, VIH 0.7 VDD, 50 mA per pin abs max, G/I grades, land 4.0 mm | EFM8BB51 data sheet Rev 1.0, Tables 4.1, 4.2, 4.18, 7.2 | V |
| Bluejay never writes PRTDRV; temperature protection default off | Bluejay 0368d11 `src/` grep, `BluejaySettings.asm` (round-2 review) | V |
| EFM8BB51F16I-C-QFN20R stock | Digi-Key product page, 2026-10-07 | S |
| SE5004L band, VCC, VREF 2.8-2.9 V at IEN 10 mA, ICQ 300 mA, case ≤ 85 °C, gain 30/32 dB, P1dB, detector, ruggedness at −10 dBm into 6:1 | Skyworks SE5004L datasheet 202393B (04 §3) | V |
| RTC6705 Fc 5725-5865 MHz, −40..85 °C, NC pad list, pin 17 AVDD_6.5 ("Supply IN 3.3 V" in the datasheet; OpenOSD-X v1.01 puts only 3.3 kΩ + 1 µF to GND on it, so D52 BR-16 leaves it open); REG1D8 pin 26 capacitor "(DNI)" on OpenOSD-X v1.01 (BR-15) | RichWave RTC6705 datasheet V0.2; OpenOSD-X reference (track 04 log; BOM study vtx-fc-misc V3, V4 verification) | V |
| TPS61022 limits: L 0.33-2.9 µH, Cout ≥ 20 µF above 1.5 A, valley limit, MODE threshold, VFB 585/600/615 mV, TJ 125 °C recommended, ΨJB 36.7 K/W, pass-through, reverse power flow in forced PWM (§7.4.1), output disconnect in shutdown | TI SLVSDX7D §6.3-6.5, §7.3-7.4, §8.2.2.2 | V |
| FTC252012SR68MBCA / S1R0MBCA parameters; GRM188C80J226ME15D X6S; NCP03XH103F05RL; YXC X252012MMB4SI-24 and KYX K2C120001210 −40..85 °C; TOGNJING 12 MHz −20..70 °C; temperature ratings of the listed parts | LCSC product API, 2026-10-07 | V |
| GRM033C81E104KE14D, GRM033C81A105ME05D, GRM155C80J106ME11D (X6S, −55..105 °C); LP5907SNX-2.85 (±2 %); BLM03PX121SN1D (0.9 A); TXU/LVC1T45 packages | distributor listings (Farnell, Arrow, Future, Digi-Key, TME), 2026-10-07 | S |
| Nexperia packages: SOT1202 (74LVC1T45GS) 1.0 x 1.0 mm, 0.35 mm pitch; SOT1216 = DFN1010B-6 (BC847QAS) 1.1 x 1.0 mm, 0.35 mm pitch; SOT1115 (74LVC1T45GN) 0.9 x 1.0 mm, 0.3 mm pitch; SOT886 (74LVC1T45GM) 1.45 x 1.0 mm, 0.5 mm pitch; BC847BV NPN/NPN in SOT666 | nexperia.com package and product pages, read 2026-10-07 | V |
| NextPCB assembly: fine-pitch ICs 0.38 mm, BGA/LGA/QFN 0.25 mm, X-ray for all BGA/QFN/LGA | https://www.nextpcb.com/pcb-assembly-capabilities, read 2026-10-07 | V |
| TPS22810 EN/UVLO deglitch 2.5 µs typical and the EN bypass-capacitor recommendation; TPS2116 CIN 1 µF and input capacitors close to the device, 6 V abs max | TI SLVSDH0C §9.3.3 (study-1-2s local copy); TI SLVSFG1A §6.1, §9, §10 (local copy) | V |
| Betaflight 2026.6.2 serial reset masks (`serial.c` L316-321, L353-358, L541-544; `config.c` L230), include order (`platform.h`), OSD defaults (`pg/vcd.c`, `osd/osd.c` L418-427, `fc/init.c` L947) | Betaflight tag 2026.6.2 / master 498430a local copies (round 4) | V |
| ELRS: VTX SPI excluded on ESP32-C3; `MIN_PWM`/`MAX_PWM` constants and `setDuty(count*1000/4096)`; raw `analogRead()` of VPD; `timeout()` skips outside `isTick`; `VpdFreqArray` constant; interpolation without `break`; index 1 keeps VREF on; `POWER_AMP_OFF` unused; YOLO 2250; five power levels; `wifi-on-interval` a firmware option; `disableVTxSpi()` on Wi-Fi start; no drive-strength hardware key | ExpressLRS 8c51826 (local clone): `devVTXSPI.cpp`, `devMSPVTX.cpp`, `freqTable.h`, `devWIFI.cpp`, `options.cpp`, `hardware.cpp`, `binary_configurator.py`; `rx_main.cpp` (track 05) | V |
| Betaflight: `vtx_low_power_disarm` sends index 1; PICO bidir DShot 5-8 % decode errors spinning; `USE_MULTICORE` off; OSD overlays on camera sync | `io/vtx_msp.c`, `dshot_bidir_pico.c`, `target_RP2350.h`, `osd_pico.c` (2026.6.2 / master) | V |
| Bluejay layout A pin map, DT steps 20.4 ns, stock DEADTIMES list | `src/Layouts/BB51/A.inc`, `src/Bluejay.asm`, `Makefile` (clone 0368d11) | V |
| ELRS whoop RX+VTX layout pins | ExpressLRS/targets `RX/Generic 2400 Whoop Rx and VTx.json` (clone 42ed776) | V |
| ESP32 erratum 3.11 (ADC power-up glitches GPIO36/39) | Espressif ESP32 errata (round-2 review) | S |
| tinyPEPPER direct gate drive, no gate resistor | `single_esc.sch` (08 verification) | V |
| RTC6705 package and zero authorised stock | RichWave datasheet; LCSC, HQ Online, Digi-Key searches; findchips (04 §2) | V / S (brokers) |
| Walsin BPF rejection figures | Walsin PI_RFBPF1608060K98Q1C V01 (04 verification #19) | V |
| NextPCB capabilities, fine pitch 0.38 mm, turnkey channels and prices | nextpcb.com capability pages, stackup DB, instant-quote endpoint (07 verification) | V |
| JLCPCB capabilities incl. 1.0 / 0.15 silk and 70 x 70 mm Standard PCBA panel minimum | https://jlcpcb.com/capabilities/pcb-capabilities and assembly page, read 2026-10-07 (round-2 review) | V |
| Stock figures | LCSC product API, 2026-10-07; Digi-Key 2026-10-07 where marked; TI store / Digi-Key from track 03 (2026-10-06); HQ Online from tracks 04/06/07 | V (LCSC) / S (others) |
| Motor currents 9-12 A on fresh HV packs | BetaFPV and Happymodel load tables (02 §4) | V / I |
| BT2.0 9 A / 15 A | betafpv.com BT2.0 page (06 verification #12) | V |
| House IMU risk ranking | OpenFC-Lite-Mini `hardware/research/imu-selection/README.md` (05 verification #11) | S |
| OpenDrone sheet reuse and the SX1281 pin-5 defect | sibling netlists via kicad-cli 10 (09 verification #10) | V |
| Area, outline, key-package floorplan and the Matrix calibration | scratchpad `spec/outline.py`, `spec/budget_v6.py`, `spec/sketch_v5.py` (budget v5, v4, v3, v2 and v1 kept) | I |
| TPS2116: 1.6-5.5 V, 2.5 A, RON 37-60 mΩ, priority mode (MODE = VIN1, PR1 vs VREF 0.92-1.08 V), truth table, ST, RCB (switchover waits for VOUT ≤ VIN + VRCB), IREV 0.001 / 0.05 / 0.15 µA typical at 25 / 85 / 105 °C (no maximum given), MODE and PR1 leakage ≤ 0.1 µA, tSW 8 µs, TA −40..105 °C | TI SLVSFG1A (https://www.ti.com/lit/ds/symlink/tps2116.pdf, read 2026-10-07); LCSC C3235557 live | V |
| TPS22810: 2.7-18 V, RON 79 mΩ typ / 115 mΩ max, VENR / VENF, CT slew SR = 46.62/Ct, 2 A DBV at TA 65 °C, TA −40..105 °C | TI SLVSDH0C (study-1-2s local copy) | V |
| TPS61022 valley limit 6.5/8/10 A, short-circuit fold-back, TSD 150 °C, recommended inductors 11.5-28 A, Cout table | TI SLVSDX7D §6.3, §6.5, §7.3, Table 8-2 | V |
| PMEG2010AEH VF 200/265/380 mV at 10 mA / 0.1 A / 1 A, IR 15 / 50 µA at 5 V (the round-2 USB OR diode) | Nexperia PMEG2010AEH Table 7, Fig. 2 | V |
| BAS16LD: SOD882D 1.0 x 0.6 mm, VF ≤ 715 mV at 1 mA, IR ≤ 30 nA at 25 V (25 °C), ≤ 30 µA at 25 V (Tj 150 °C), land 1.3 x 0.7 mm | Nexperia BAS16LD Rev. 1, Table 7, Fig. 9 (https://assets.nexperia.com/documents/data-sheet/BAS16LD.pdf, read 2026-10-07); stock LCSC C841775 via search index | V / S (stock) |
| SDM02U30LP3: IR ≤ 7 µA at 10 V (25 °C), typical reverse current 10-100x higher at 85-125 °C | Diodes SDM02U30LP3 datasheet (OpenDrone library copy), Electrical Characteristics, Fig. 3 | V |
| LP5912-3.3 dropout ≤ 180 mV at 500 mA | TI LP5912 datasheet (OpenDrone library copy), Electrical Characteristics | V |
| TPS61022 EN thresholds VEN_H ≤ 1.2 V, VEN_L 0.35-0.45 V | TI SLVSDX7D Table 6.5 | V |
| DJI O4 Lite input 3.7-13.2 V, BEC ≥ 10 W, wiring colours; current 0.98-1.20 A | DJI O4 Air Unit Series User Manual v1.0; Oscar Liang review | V / S |
| Betaflight O4 integration: MSP DisplayPort port selection, `USE_OSD_HD` / `USE_OSD_SD`, PINIO, PIOUART0/1 and `PIO_UART_INDEX` 1 | Betaflight 2026.6.2 `config.c` L568-581, `common_pre.h`, `displayport_msp.c`, `pinio.c`, `target_RP2350.h` L32-33, L96-101, `uart_pio.c` (study-1-2s digital-vtx §2-3) | V |
| ELRS `clearVtxTable()` (power 3, pitmode 0, lowPowerDisarm 0, EEPROM write), RCE pit forcing on index 2, lowPowerDisarm forcing index 1; Betaflight applying `MSP_SET_VTX_CONFIG`; register A 0x0190 and N/A = 25·f/64 | ExpressLRS `devMSPVTX.cpp` l. 71-96, 211-219, `devVTXSPI.cpp` l. 22, 128-131, 251-258, 289; Betaflight `msp.c` l. 3829-3842, `vtx_msp.c` l. 110 | V |
| Winbond WSON metal pad not connected internally, may float | W25Q128JV datasheet §10.3 note | V |
| Bluejay rejected-frame handling (no error report), EDT status content, layout-A DebugPin P2.0 | Bluejay `Isrs.asm` l. 155-194, `Scheduler.asm` l. 212-248, `Layouts/BB51/A.inc` (round-3 review) | V |
| NextPCB capability page (annular 3.5 mil, hole to hole 8 / 12 mil, mask dam 3.5 mil, silk 30 / 24 mil) | https://www.nextpcb.com/pcb-capabilities, read 2026-10-07 (round-3 review) | V |
| BOM reduction D52-D54: apply-now set BR-01 to BR-26, counts, areas, fallbacks, interactions and open items | [BOM-REDUCTION.md](BOM-REDUCTION.md) and its four track reports with verification sections (`research/bomred/`), 2026-10-09 | V / S / I as tagged there |
| ESP32-PICO-V3: in-package 4 MB flash on GPIO6/11/16/17/18/23, 40 MHz crystal and CAP network inside (Fig. 8), external parts 10 µF + 0.1 µF and the EN RC (Fig. 11), pins 25/35/36/44/45/47/48 NC and 30/31 flash (Table 4), −40..85 °C ambient | Espressif ESP32-PICO series datasheet v1.3 (BOM study local copy) | V |
| ESP32 CAP1 10 nF "required for proper operation"; CAP1-CAP2 RC not needed without deep sleep | ESP32 datasheet v5.3 Table 2-1; Espressif schematic checklist (BOM study rx-vtx) | V |
| ELRS: VTX SPI compiled out on ESP32-C3 (`rx_main.cpp` l. 91-95 at 15c7899); layout overlay merge (`UnifiedConfiguration.py` l. 57-58); ESP32-PICO support (bd4f4e7f, #1526); SX128x release builds do no frequency correction | ExpressLRS source (BOM study rx-vtx and vtx-fc-misc verification) | V |
| SX1280 / SX1281 identical except the ranging engine; Table 15-1 decoupling set; SX1281 stock | Semtech SX1280/1 datasheet Rev 3.2 Table 1-1, Table 15-1; LCSC live 2026-10-09 | V |
| PNP drive model (YOLO 26-30 mA at Re 27 Ω, 49-66 mA at 10 Ω, pinch-off ≥ 3400 counts, about 255 duty steps); Happymodel ELRS AIO calibration 3133-3263 counts; OpenVTx GD32 bias window | `research/bomred/verify/pnp_fix.py`; ExpressLRS `targets.json`; OpenVTx `Generic_GD32F130.c` (BOM study vtx-fc-misc) | I (model) / V (firmware) |
| BC857BM,315: PNP 45 V / 100 mA, hFE 220-475, Ptot 250 mW, SOT883 | Nexperia product page and parametrics (BOM study) | S |
| SE5004L RFOUT internal DC shunt, only RFIN "DC block required" (BR-17) | Skyworks SE5004L datasheet 202393B p. 1 | V |
| LP5907 VEN −0.3..6 V to GND independent of VIN, internal EN pull-down; LP5912 COUT 0.7-10 µF | TI SNVS798 §5.1; TI LP5912 datasheet §7.6 | V |
| TPS61022 FB bottom resistor < 300 kΩ; EN and VIN share the −0.3..7 V absolute maximum | TI SLVSDX7D (BOM study passives PS-10, PS-13 and power-esc PE-3, PE-12) | V |
| RP2350 ADC_AVDD "decoupled with a 100nF capacitor close to the chip's ADC_AVDD pin"; house OpenFC-Lite-Mini flies 7 caps for the 9 supply pins | RP2350 datasheet §6.1.5; `OpenFC.kicad_pcb` via pcbnew (BOM study vtx-fc-misc F2) | V |
| Matrix II LED strip driven direct (`LED_STRIP_PIN PB2`); "inline diode on the VIN" remedy for 3.3 V data | betaflight/config `BETAFPVG473_V2`; Cleanflight LED-strip docs (BOM study F1) | V |
