# Design spec (proposal, P0)

**Status: proposal for a board that has not been designed.** Nothing below exists
as a schematic or a layout. This file freezes the targets and the part choices
for phase P0 of [BUILD-PLAN.md](BUILD-PLAN.md), so that P1 (project setup) and
P2 (floorplan proof) can start. Every number here is a target, a datasheet
value or a calculation, and each one says which. Where a choice may still move
after the P2 floorplan or a bench test, the gate that decides it is named.

Date 2026-10-07, revised the same day after review round 1 (electrical, RF and
firmware, manufacturing and lineup). Inputs: the owner direction and owner rules
(2026-10-06), [DECISIONS.md](DECISIONS.md), the research tracks 00-09 (Matrix
photo analysis, Matrix deep dive, landscape, ESC, VTX/OSD, FC/RX/firmware,
power/connectors/mechanics, NextPCB DFM, prior art, OpenDrone reuse map) with
their verification logs, the JLCPCB capability page (read 2026-10-07), live LCSC
and Digi-Key stock (2026-10-07) and [LINEUP-CONVENTIONS.md](LINEUP-CONVENTIONS.md).
The competitor material is in [COMPETITION.md](COMPETITION.md); the FC, RX and
ESC pin plans are in [PINMAP.md](PINMAP.md).

Status tags used below: **V** read from a primary source, **S** screened
(secondary source, distributor index, research track not re-derived), **I**
inferred (calculation or engineering judgement). Loss and thermal numbers come
from `calc/thermal.py`, area numbers from `spec/budget.py` (both scratchpad).

---

## 1. Scope and targets

Scope is fixed by the owner decision of 2026-10-06: **1S only, match the BetaFPV
Matrix 1S 5IN1 II** in envelope and features, beat it on measured ratings,
blackbox, repairability and open documentation, not by adding scope.

| Item | Target (proposal) | Basis |
|---|---|---|
| Input | 1S LiPo / LiHV, 3.0-4.35 V operating; electronics regulate down to 2.5 V cell under sag (the VTX PA is rated from 3.0 V only); 2S not supported ("1S" silk at the battery pads) | owner decision; TPS61022 runs to 0.5 V once started, starts at 1.8 V (V, TI SLVSDX7D); SE5004L VCC 3.0-5.5 V (V) |
| Board body | 26.4 x 26.4 mm square (Matrix II: 26.35 mm, photo-measured) | V (01) |
| Orientation | Diamond mount like the Matrix: flight-forward points at a body corner. Front corner rounded with R 5.8 mm (Matrix: about 2.4 mm set-back on the diagonal) and carries no ear | V (01, photo); I (radius) |
| Ears and holes | 3 ears (left, right, rear corners), ring OD 4.8 mm. Holes **Ø 3.5 mm** on a **25.75 x 25.75 mm square**, non-plated cut-outs in P1; plated holes with a GND annulus (Matrix practice, stiffer ears) are decided at P2 with the ball fit (O2, O16) | Matrix II holes Ø 3.48-3.57 on 26.0 mm, plated (V, 01). 25.75 mm halves the worst offset in both 25.5 mm (Air65 II/Air75 II, Happymodel) and 26.0 mm (Meteor65 Pro II, Meteor75 Pro) frames to 0.18 mm radial, which the rubber balls take up (I, from 06 §3.3) |
| Overall size | 30.55 x 30.55 mm including ears (Matrix II 30.9 mm); outline area 696.6 mm² net of holes | I (outline script, §9) |
| Mounting | 3-point soft mount with BetaFPV-type shock balls; 1.0 mm board matches the Matrix ball groove | V (01, 06 §3.3) |
| Thickness | 1.0 mm finished, 6 copper layers | §8 |
| Weight | **≤ 3.5 g** bare (solder-pad build, no battery pigtail, no antenna). Estimate 3.1-3.4 g: PCB 1.8-1.95 g, parts about 1.0 g, solder 0.12 g. Matrix II solder-required: 3.76 g | I (§6); V (Matrix, 01) |
| ESC | 4 channels, Bluejay on EFM8BB51 (I grade), P+N direct drive, bidirectional DShot, EDT | §4.3, §4.4 |
| ESC rating to publish | **Targets, to be measured by V4 (§14):** 6 A continuous per channel (one channel loaded, others 2 A), 4 A continuous on all four, 12 A for 10 s, 18 A for 3 s, at 25 °C ambient, VTX 25 mW, board in a frame under a canopy, every part inside its own rating. The model with the verified convection range (h 30-80 W/m²K) reaches 6 A on one channel only at h ≥ about 64 W/m²K; at mid h (55) it gives about 5 A on one channel and about 3 A on all four, and at the low end the 85 °C parts are out of rating already at hover (§4.3). The measured number is what gets published. The Matrix "12 A continuous" measured the same way would be lower than ours (34 vs 23 mΩ path) | §4.3 loss math |
| VTX | RTC6705 + Skyworks SE5004L PA on the cell, U.FL. Levels **pit / 25 / 100 / 400 mW**, controlled by the ELRS receiver (MSP-VTX over CRSF). **Channels:** ELRS pushes 48; this board supports the 40 from 5645 to 5945 MHz (A, B, E, F, R; the L band 5362-5621 MHz is unsupported: below the RTC6705 and Betaflight 5600 MHz limits). Only the 24 channels inside both datasheet bands (RTC6705 5725-5865 MHz, SE5004L 5150-5850 MHz) are rated; the other 16 are published as measured. **Power:** 25 and 100 mW closed loop on the PA detector, calibrated at one point (5850 MHz) until the ELRS interpolation fix (O6); 400 mW is full drive limited by a hardware cap (§4.8) and published as measured, until closed-loop 200/400 mW arrays exist (O6, release requirement). 400 mW is continuous only at high airflow (PA case ≤ 85 °C, §5.4) | §4.8 |
| OSD | Betaflight PIO framebuffer OSD on the RP2354A (no OSD chip) | §4.8 |
| RX | Serial ExpressLRS 2.4 GHz, ESP32-D0WD-V3 + SX1280, +13 dBm, no PA/LNA (Matrix parity), insulated wire monopole; Wi-Fi for ELRS updates through a minimal radiator (Matrix has a Wi-Fi chip antenna) | §4.7 |
| FC | RP2354A, Betaflight ≥ 2026.6.2, one gyro per revision published in the target (no lottery) | §4.5, §4.6 |
| Blackbox | 16 MB SPI NOR (W25Q128JVPIM), SPI0 | §4.9 |
| 5 V BEC | 5 V; calculated nominal peak 1.9 A at 2.8 V and 2.0 A at 3.0 V in (TI method with −30 % inductance); claim capped at 1.5 A continuous by the output capacitance; the published continuous figure is the V1 measurement at flight board temperature. Design load 0.69 A | §4.2, §5.3 |
| Current / voltage sense | 0.5 mΩ shunt (Kelvin land) + INA186A3 (50 mV/A, `ibata_scale` 500), VBAT 1:1 divider; scales measured and set in the target | §4.1 |
| Connectors | BT2.0 pigtail on two plated holes (user-fitted); 12 motor solder pads with plated wire-anchor holes; SH1.0 4-pin vertical USB (BetaFPV adapter style); SH1.0 3-pin vertical camera plug plus CAM/5V/GND pads; U.FL for the VTX; RX antenna wire hole; one free UART on pads (TX1/RX1, as the Matrix II) | §4.10 |
| Fab / assembly | NextPCB turnkey (partial turnkey with consigned lines), DFM-compatible with JLCPCB as well; through vias only, OpenDrone 0.35/0.20 via (D6) | §8, §15 |

---

## 2. What to optimise, ranked

| Rank | Goal | Metric | Target | Bench measurement |
|---|---|---|---|---|
| 1 | Electronics rail that survives sag (no FC/RX brown-out; video to 3.0 V, the PA minimum) | +5V at full design load (0.69 A, and 1.25 A with the PA moved to 5 V) while the input is swept 4.35 → 2.6 V | ≥ 4.85 V at VIN ≥ 2.8 V; ripple ≤ 50 mV p-p (forced PWM, 1 MHz); no reset of FC or RX down to VIN 2.5 V | bench supply + electronic load, scope at the camera pad |
| 2 | Honest, better ESC rating | continuous A per channel with every part inside its rating, measured at the part (hottest FET ≤ 100 °C, EFM8 ≤ 125 °C, RP2354A, gyro, SX1280, RTC6705, NOR and SE5004L case ≤ 85 °C) under protocol §14 V4; hot P+N path resistance | ≥ 6 A per channel target (model: needs h ≥ about 64 W/m²K); path 23 mΩ hot typ (28 max) vs 34 mΩ for the Matrix's AGM210MAP | thermocouples on the hottest FET, the loaded channel's EFM8, the PA case, the RTC6705, the RP2354A and the gyro; same rig on a Matrix II |
| 3 | Weight | grams on a 0.01 g scale | ≤ 3.5 g bare (Matrix 3.76 g) | scale, first 5 prototypes |
| 4 | Measured VTX power and clean spectrum | output per channel at 25/100/400 mW at 3.7 V; 2nd harmonic | 25 and 100 mW within ±1.5 dB at 5850 MHz (the calibration point); at 5650/5750/5917 MHz within ±3 dB until the ELRS interpolation fix, then ±1.5 dB; full per-channel table published; 2f ≤ −30 dBm (EN 300 440 limit) | calibrated power sensor + 30 dB attenuator; spectrum analyser to ≥ 18 GHz; published table |
| 5 | RX link | conducted sensitivity at 500 Hz packet rate; desense with every on-board aggressor active | within 2 dB of the SX1280 datasheet figure; ≤ 3 dB desense | ELRS link stats + attenuator chain |
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
| FC | STM32G473 + AT7456E OSD | STM32G473CEU6 + AT7456E | RP2354A + PIO OSD |
| Gyro | 6-part lottery | BMI270, own supply | one part per revision (BMI270 or ICM-42688-P after fly-off) |
| ESC | 4x BB51, 12x AGM210MAP P+N, "12 A cont / 18 A peak" | 4x BB51, 12x SiA517DJ, 5 A design target | 4x BB51, 12x CSD25402Q3A (P) + 12x CSD13202Q2 (N); 6 A continuous target, to be measured (V4); 23 mΩ modelled |
| RX | ESP8285 + SX1281 onboard | external | ESP32 + SX1280 onboard, ELRS 4.x mainline |
| VTX | RTC6705 + RFPA5542 (EOL) + MM32F003, 25-400 mW | RTC6705 + RTC6659-class PA, 25/100/250/MAX | RTC6705 + SE5004L, no VTX MCU (ELRS drives it), pit/25/100/400 |
| Blackbox | 16 MB | 16 MB | 16 MB |
| USB | SH1.0 vertical + adapter | 4 pogo pads + clip-on adapter | SH1.0 vertical (BetaFPV adapter compatible, pinout to be measured) |
| Openness | none | page only | schematic, layout, BOM, measured ratings |

---

## 4. Architecture per block

Each block gives the options weighed, the decision, the key parts and the
numbers. **Stock gate.** The P0 gate is "≥ 5x the 50-board quantity" (250 for a
part used once per board) **at the distributors NextPCB turnkey buys from**: HQ
Online plus its quote engine (Digi-Key, Mouser, Element14, Avnet, ...), not
LCSC (track 07 §3). The figures below are LCSC live reads on 2026-10-07 unless
marked; they are a first screen only. P0 closes with a NextPCB BOM quote by
exact MPN on the full BOM (O17); lines it cannot fill move to the consigned list
(§15.3) or to a globally stocked equivalent. Parts already manufactured on an
OpenDrone board are marked **[PU]** (PARTS-USED.md).

### 4.1 Input and protection

| Option considered | Verdict |
|---|---|
| Reverse-polarity FET | **No.** The BT2.0 key protects the plug, not the user-fitted pigtail joint: a pigtail soldered reversed puts about −4 V on +BATT through the TVS, the 12 body-diode pairs, the INA186 and the TPS61022, which loses the board. An ideal-diode P-FET (1-2 mΩ, 3x3) costs about 12 mm² and 0.4-0.6 W at 20 A. Rev1 keeps user fit (Matrix-style pads) and states the risk: + and − silk at the pads and a polarity photo in the README. Factory fitting on NextPCB's THT line, which removes the risk, is priced as a P7 option |
| TVS at the pads | **Yes, for the FETs only.** Event: battery unplugged (or pigtail torn in a crash) while the props spin; Bluejay damping returns rotor energy (up to about 0.3 J per motor at 40,000 rpm, I) into a bus that then holds only the MLCCs. The SMF5.0A (VBR 6.40-7.07 V, VC 9.2 V at 21.7 A, V) keeps the 12 V N-FETs and the ±12 V P gates out of avalanche. It does **not** protect EFM8 VDD (5.5 V abs max), SE5004L VCC3 (6 V), TPS61022 (7 V; its pass-through mode carries a surge onto +5V, where TLV755P allows 6.0 V and TPS7A20 6.5 V) or the 6.3 V MLCCs. A clamp per EFM8 is not possible in this topology: EFM8 VDD must follow the P-FET sources, and a VDD clamped below the bus turns the off P-FETs on. No small bus clamp holds ≤ 5.5 V at amps with acceptable leakage at 4.35 V. Accepted as Matrix parity (same topology); risk in §15.4, surge measured in V3b |
| Bulk at the pads | 2x 22 µF 0603 16 V. Board total about 50-80 µF effective at 4.35 V (table below), which shares the 48-96 kHz ripple with the 30-60 mΩ battery path (03 §11) |

Effective capacitance (I: typical X5R DC-bias behaviour including −20 %
tolerance; replaced by the Samsung/Murata simulator curves in P3, which were
not readable on 2026-10-07):

| Part | Use | At | Effective each |
|---|---|---|---|
| CL10A226MO7JZNC 22 µF 16 V 0603 | pad bulk x2, boost Cin x1 | 4.35 V | about 9-13 µF |
| CL10A226MO7JZNC | boost Cout x2 | 5.0 V | about 8.5-11 µF (17-22 µF for two) |
| CL05A226MQ5QUNC 22 µF 6.3 V 0402 | ESC local bulk x8 (69 % of rated V) | 4.35 V | about 4-7 µF |
| GRM033R61A105ME44D 1 µF 10 V 0201 | EFM8 VDD x4 | 4.35 V | about 0.4-0.6 µF |

Bus ripple, caps-only upper bound ΔV = I·D(1−D)/(f·C): one ESC at 12 A and D 0.5
(or four unsynchronised ESCs at 6 A, about 2x one) gives 0.8-1.25 V p-p at
48 kHz and 0.4-0.6 V at 96 kHz on 50-80 µF; the battery path in parallel roughly
halves it (track 03: 0.2-0.3 V RMS at 48 kHz). The ripple is common to the P-FET
source and gate because each EFM8 sits on its own cluster's +BATT (§4.4); it
matters for the PA supply (§4.8, V5b).

| Function | Primary | Fallback |
|---|---|---|
| TVS | Littelfuse **SMF5.0A**, SOD-123FL, C151296, 33,500 (V) | Vishay SMF5.0A-E3-08, same package (S) |
| Pad bulk | Samsung **CL10A226MO7JZNC** 22 µF 16 V 0603, C2762594, 457,735 [PU] | Murata GRM188R61C226ME15 (S) |
| Shunt | Stackpole **HCS1206FTL500**, 0.5 mΩ 2 W 1206, C346511, 1,717 | Yezhan ASR-S-3-0.2F 0.2 mΩ 2512, C695806, 1,020 [PU] (larger land, scale 200) |
| Current amp | TI **INA186A3IDCKR**, SC-70-6, gain 100, C2058245, 5,715 [PU] | TI INA186A3 DSBGA (YFD) (S, −4.8 mm²) |
| VBAT divider | 2x 10 kΩ 0201 (Yageo RC0201FR-0710KL, C106225 [PU]) + 100 nF | Uni-Royal 0201WMF1002TEE (S) |

Nets: the battery pads, TVS and pad bulk sit on **`+BATT_IN`** (net class VBAT,
`PWR_FLAG`); after the shunt the rail is **`+BATT`**. Everything that draws
current, including the boost VIN and the PA VCC, taps `+BATT` after the shunt,
so the INA186 sees it. Numbers: 0.5 mΩ x 100 V/V = 50 mV/A, full scale 66 A at
3.3 V, Betaflight `ibata_scale` 500 (0.1 mV/A units). Shunt loss 0.2 W at 20 A,
0.31 W at 25 A. VBAT 10k/10k puts 4.35 V at 2.18 V on the ADC (RP2354A ADC range
3.3 V). Current sense is high side with Kelvin taps and the matched input RC
network of the OpenESC Rev3.2 / OpenAIO root sheet (reused, values moved to
0201). A two-terminal 0.5 mΩ part makes the scale depend on where the taps sit
(±10-20 % unit to unit, I), so the land is a four-pad Kelvin pattern per the
Stackpole HCS application note with the sense taps at the inner pad edges, and
the scale is checked on every prototype and on a sample of each production lot.

### 4.2 Power tree

```
BT2.0 -> +BATT_IN pads -- SMF5.0A, 2x22u -- shunt (Kelvin -> INA186) -- +BATT
  +BATT -> 4x ESC power stages; 4x EFM8 VDD on their own cluster's +BATT (1u + 100n, no series R)
  +BATT -> SE5004L PA VCC (10u + 1n + 100p)   [one 3-pad solder jumper: +BATT (default) or +5V]
  +BATT -> TPS61022 boost (EN = VIN, MODE = VOUT: forced PWM), 1 MHz -> +5V (2x 22u 0603)
             +5V -> ferrite 0201 + 10u -> CAM 5V (plug + pad)
             +5V -> LED-strip 5V, buzzer +, user 5V pads
             +5V -> TLV75533 (EN = +5V) -> +3V3 (RP2354A, NOR, OSD front end, INA186, LEDs)
                                  +3V3 -> TPS7A2018 (EN = +3V3) -> +1V8 (gyro analog)
             +5V -> LP5912-3.3 (EN = +5V) -> +3V3_RX  (ESP32, SX1280, RGB LED)
             +5V -> TPS7A2033 (EN: 100k to +3V3_RX, ESP32 GPIO21 pulls low) -> +3V3_VTX (RTC6705 only)
  VBUS (SH1.0 USB) -> PMEG2010AEH Schottky -> +5V   (bench: FC, RX, RTC6705; PA and ESCs unpowered)
  RP2354A internal core SMPS -> +1V1 (3.3 µH 2016, per RPi guide)
```

Enables: every EN sits on its own regulator's input (or, for the VTX LDO, a
pull-up to a 3.3 V rail below its 5 V input), none floats and no EN net is shared
between rails (commons checklist). TPS61022 MODE goes to VOUT, so forced PWM
holds over the whole sag range (VMODE_H 1.2 V valid with VOUT > 2.2 V, V). The
TPS61022 passes VIN to VOUT when VIN > VOUT (V): a bus surge reaches +5V (§4.1).

Options weighed:

| Question | Options | Decision | Why (numbers) |
|---|---|---|---|
| 5 V converter | TPS61023 (SOT-563, 2.7 A valley, auto-PFM), TPS61022 (2x2, 6.5 A valley, forced-PWM pin), TPS63070 buck-boost (2S only), SY7088 (3 A peak) | **TPS61022RWUR + 0.47 µH 2520** | Forced PWM keeps the 1 MHz ripple fixed and out of the PFM range that shows as video bars. Calculated per TI §8.2.2.2 (inductance −30 %, peak at 80 % of Isat): 1.90 A at 2.8 V and 2.04 A at 3.0 V nominal peak, against 0.69 A design load and 1.25 A if the PA moves to 5 V. Ripple is 230 % of the inductor DC current at the design load (TI asks ≤ 40 % at full load), so η 0.88 is optimistic at light load. Above 1.5 A the datasheet needs ≥ 20 µF effective Cout (two 0603 give 17-22 µF), so the claim stops at 1.5 A. The inductor's 7.5 A Isat is below the valley limit maximum plus ripple (10 + 3-4.3 A): under overload this molded metal-powder part saturates softly (S) before the IC limits; the user 5 V loads are documented as a 0.25 A allowance. P3 compares a 0.68-1.0 µH 2520 metal-powder part (lower ripple and RMS loss) on its Isat. TPS61023 gives 1.83 A at 3.0 V (I) and has no forced PWM |
| 3.3 V supply path | 5 V boost + LDOs (as drawn) vs a cell-fed 3.6 V buck-boost (TPS63802 class, S) with post-LDOs for the 0.29 A of 3.3 V loads | **as drawn**, decided at P2 on area | All 3.3 V loads through boost + LDO cost about 0.65 W of overhead for 0.96 W delivered. A 3.6 V buck-boost (η about 0.92) would save about 0.45 W, i.e. 4-11 K of board rise at the verified h, and run to about 2.3 V, for about 15-20 mm² and 0.03 g on the bottom. The bottom does not have that area today (§9) |
| PA supply | 5 V boost + load switch (track 06 R6) vs cell (track 04) | **Cell (+BATT)**, one 3-pad solder jumper to +5V | SE5004L is rated 3.0-5.5 V; takes 0.3-0.55 A off the boost; EN low = 0.5 µA so no load switch; on USB only the PA has no supply and cannot cook. A single 3-pad jumper cannot short the boost output to the cell (two 0 Ω links could). Below 3.0 V cell the PA is out of rating (V5 measures at 2.8 V). Bench test V5 decides (§14) |
| Diode-OR | two Schottkys into an LDO bus (OpenFC pattern) vs one Schottky VBUS → +5V | **One Schottky**, VBUS → +5V | TPS61022 has true output disconnect, so +5V can be back-fed from USB without reaching the cell; saves a diode drop on the main path |
| 3.3 V rails | one LDO for all (about 0.29 A: 0.49 W, +82 K in X2SON) vs split | **Split into 3 + gyro LDO** | Each LDO ≤ 0.17 W; the RTC6705 VCO gets its own 7 µVrms rail; RX Wi-Fi bursts (up to 0.3 A, Wi-Fi mode only) go to a WSON-6 part with a better thermal path |
| ESC MCU supply | VBAT direct vs 3.3/5 V rail | **VBAT direct**, each EFM8 on its own cluster's +BATT, 1 µF + 100 nF, no series R | EFM8BB51 VDD 1.8-5.5 V (V, datasheet); gate drive = cell voltage; motors survive a BEC fault. A series R (10 Ω x 1.1 µF corner 14.5 kHz) would leave 96 % of the 48 kHz bus ripple between P source and P gate (0.7-1.0 V p-p against a hot P threshold of about −0.46 V); tied directly, VDD tracks the P sources (track 03 §8: at most 2.2-4.7 Ω) |
| USB ESD | 2-line ESD array at the SH1.0 vs none | **None** | House boards (OpenFC-Lite-Mini, OpenAIO BOMs) ship USB without an array; RP2350 pads are HBM 2 kV (V, §14.9.2) behind 27 Ω series resistors. Risk recorded (§15.4); a DFN1006 array costs about 1.5 mm² of bottom area the board does not have (§9) |

On USB only: the bench loads are FC 0.09 A, RX 0.10 A (0.3 A in ELRS Wi-Fi mode)
and RTC6705 0.10 A at 5 V. The camera is not budgeted on USB: without the
battery the PA has no supply, so OSD setup needs the battery anyway. At 0.3 A
the PMEG2010AEH drops about 0.22 V (V: 0.25 V typ at 0.5 A) and dissipates about
0.07 W (Tj 150 °C). Bidirectional DShot idles high on USB and back-feeds the
unpowered EFM8s and +BATT through the 2.4 kΩ resistors; PINMAP §4.5 documents
that case and V9 tests it.

Parts:

| Function | Primary (MPN, maker, package, stock) | Fallback | Reuse |
|---|---|---|---|
| Boost | TI **TPS61022RWUR**, VQFN-HR-7 2x2, C915088, 857 | TI TPS61023DRLR, SOT-563, C919459, 53,320 (new land, 1.6 A at 2.8 V) | new (power sheet rewritten; bucks of OpenFC `power` do not run at 1S) |
| Boost inductor | cjiang **FTC252012SR47MBCA**, 0.47 µH, 2.5x2.0x1.2, Isat 7.5 A, 13 mΩ, C5832368, 108,440 | cjiang FTC201610SR47MBCA, 2016, Isat 6.3 A (C5832340, 30,640); P3 also checks a 0.68-1.0 µH 2520 | new |
| Boost caps | Cout 2x CL10A226MO7JZNC 0603; Cin 1x CL10A226MO7JZNC 0603 (9-13 µF effective at 4.35 V against the 4.7 µF minimum) [PU] | Murata GRM188R61C226ME15 (S) | PU |
| +3V3 LDO (FC) | TI **TLV75533PDQNR**, X2SON-4 1x1, C2861882, 2,025 [PU] | TI LP5912-3.3DRVR, WSON-6 2x2, C524780, 23,490 [PU] | OpenRX-Lite part |
| +3V3_RX LDO | TI **LP5912-3.3DRVR**, WSON-6 2x2, C524780, 23,490 [PU] | TLV75533PDQNR [PU] | OpenFC `power` back end |
| +3V3_VTX LDO | TI **TPS7A2033PDBVR**, SOT-23-5, C2862740, 201,625 | TI TPS7A2033PDQNR, X2SON-4 1x1, C2871641, 0 at LCSC (commons-verified part): −7.9 mm² once a NextPCB channel shows stock; or the LP5912-3.3 already on the BOM (−3.8 mm², noise to compare in P3) | OpenVTX/04 choice |
| +1V8 gyro LDO | TI **TPS7A2018PDQNRM3**, X2SON-4 1x1, C36996449, 8,090 | TI LP5912-1.8DRVR, WSON-6 2x2, C2876234, 728 [PU] | OpenFC `imu` rule (separate 1.8 V) |
| USB OR diode | Nexperia **PMEG2010AEH**, 1 A 20 V, SOD-123F, C110921, 25,360 (V: VF 0.25 V typ at 0.5 A, Tj 150 °C) | ROHM RB161QS-40T18R, SMD1006, C2837790 (−4 mm², but 250 mW and 0.6 V at 1 A: only if P2 lacks the area) | new |
| RP2354A core inductor | Abracon **AOTA-B201610S3R3-101-T**, 3.3 µH 2016, C42411119, 625 [PU] | external 1.1 V LDO with the SMPS bypassed (RPi guide option); MPN chosen in P3 | OpenFC `rp2350a` |
| Camera ferrite | Murata **BLM03PX121SN1D**, 0201 (commons block `LDO_IMU_TPS7A2033`; current rating ≥ 0.3 A confirmed in P3, camera 0.12 A) | Murata BLM03PX220SN1D, 0201, 1.45 A (S, Digi-Key) | commons |

### 4.3 ESC power stage

| Topology | Area (12 phases + 4 MCUs) | Hot path at Vgs 3.6 V, typ (max) | Verdict |
|---|---|---|---|
| P+N dual per phase, direct GPIO (Matrix: AGM210MAP) | 147 mm² FETs | 34.1 mΩ | parity only; AGM210MAP is LCSC-only (not Digi-Key, not HQ Online) |
| **Discrete P 3.3x3.3 + N 2x2 per phase, direct GPIO** | 205 mm² FETs + 36 mm² top / 24 mm² bottom for the via tongues (below) | **23.1 (27.9) mΩ** (CSD25402Q3A) / 19.8 mΩ (CSD25404Q3) | **chosen**, subject to the area gate (§9) |
| Discrete P 2x2 + N 2x2 (CSD25310Q2 + CSD13202Q2) | 116 mm² | 40.2 mΩ | area fallback (−94 mm² top), about 5 A rating |
| N+N + gate driver | +4-15 mm²/channel + boost rail | 11 mΩ (needs EG2134, 0 stock) / 22-30 mΩ (DRV8328) | no: no stocked 1S driver gains anything, adds a rail whose failure drops all four motors (03 §5c) |
| Level-shifted P (2S style) | +46 mm² | worse, DT 0.6-1.4 µs | no: 1S only |

Decision: per phase one TI **CSD25402Q3A** P-FET on the top (high side, gate
straight from the EFM8 COM pin, active low) and one TI **CSD13202Q2** N-FET on
the bottom (low side, PWM pin, active high). Bluejay BB51 layout A, unchanged
upstream (§12).

**Cell construction from the real lands** (V, SLPS454B p.1 and p.9; SLPS313A).
The CSD25402Q3A exposed pad and pins 5-8 are the **source**; the **drain** is
only pins 1-3, three 0.3 x 0.6 mm leads at 0.65 mm pitch on one edge; gate
pin 4. The CSD13202Q2 has its drain on pins 1, 2, 5, 6 and the centre pad, gate
pin 3, source pin 4 plus a narrow strip. So:

- the P source pad sits on +BATT and holds the cluster's +BATT feed vias
  in-pad (Type VII, 0.35/0.20; they land on the bottom +BATT pour, shared with
  the leg cap's +BATT terminal);
- the three P drain leads fan into a copper tongue beside the package (about
  1.0 x 2.0 mm) that carries the phase via field (8x 0.35/0.20 at 0.40 mm pitch)
  down to the N drain pad on the bottom (Type VII where they land in that pad);
- the N sits under the tongue, offset from the P body so that the GND vias at
  its source pin land on free area on the top (D10: no stack that puts low-side
  source vias under the opposite FET's pads);
- the motor-pad route leaves the tongue on L1 and is repeated on L6.

Phase node about 0.5 mΩ tongue + 0.18 mΩ vias, about 0.7 mΩ (I), 0.1 W at 12 A
while the N conducts. Commutation loop: P source pad → P die → drain leads →
tongue → phase vias → N → N source → leg cap (bottom, to a +BATT via from the P
source pad) → back up: about 3-4 mm across through 1 mm of board, target
≤ 4 mm², re-measured on the drawn cell at P2. Area per phase about +3 mm² top
(tongue 2, N source via landing 1) and +2 mm² bottom (+BATT via landing): +36 mm²
top and +24 mm² bottom on the board (§9). The CSD25404Q3 fallback has the same
pad map (V), so the dual land (O5) survives.

Why CSD25402Q3A over the lower-Rds CSD25404Q3 as primary: 16,466 vs 3,297 at
LCSC (the gate needs 3,000 for 50 boards), $0.59 vs $1.09, a lighter gate (P
turn-off typ 88 vs 116 ns; datasheet worst case 276-326 vs 372-440 ns, below)
and a better Cdv/dt ratio (Crss/Ciss 0.028 vs 0.032), for a 17 % higher
conduction loss. Both beat the Matrix stage (03 §4, model re-run here).

| Part | Primary | Fallback |
|---|---|---|
| P-FET | TI **CSD25402Q3A**, −20 V / ±12 V, 7.7 / 13.3 mΩ typ (8.9 / 15.9 max) at 4.5 / 2.5 V, VSONP-8 3.3x3.3, RθJC 2.3 K/W, C111356, 16,466 (TI store 136,315, track 03) | TI CSD25404Q3, 5.5 / 10.1 mΩ, VSON-CLIP 3.3x3.3, RθJC 1.3 K/W, C2865523, 3,297. Same pad map; land outline (DNH vs DQG) checked in P3 |
| N-FET | TI **CSD13202Q2**, 12 V / ±8 V, 7.5 / 9.1 mΩ typ (9.3 / 11.6 max) at 4.5 / 2.5 V, SON-6 2x2, RθJC 6.4 K/W, LCSC C187839 2,605; Digi-Key 8,235, TI store 294,349 (track 03, 2026-10-06) | AOS AON2408, 20 V, DFN 2x2 (S, LCSC index 3,512); land check in P3; about +25 % N loss |
| Leg cap | Murata GRM033R61E104KE14D 100 nF 25 V 0201, C76939 [PU], one per half-bridge | Samsung CL03A104KQ3NNNC (S) |
| Local bulk | Samsung CL05A226MQ5QUNC 22 µF 6.3 V 0402, C105226, 112,076 [PU], 2 per ESC | Murata GRM155R60J226ME11 (S) |

**Loss math** (I, model of track 03 re-run with the review corrections). Layout A
conducts through **two FETs in series** at every instant: the high-side P of the
driven phase plus either the PWM'd low-side N or, in the damped off-time, the
damping P. Conduction is I²·(d·(Rp + Rn) + (1 − d)·2Rp), evaluated at d 0.8
(about 2-5 % above I²(Rp + Rn) at partial duty). Rds values are typical, hot
(x1.35) at Vgs 3.6 V (Rp 12.4, Rn 10.7 mΩ); the max-Rds column uses the datasheet
maxima (27.9 mΩ path). Dead time adds 2·DT·f·0.8 V·I through body diodes, for the
worst-case-safe build `A_X_20_48` (DT 408 ns at 48 kHz, the same loss as DT 10 at
96 kHz); `A_X_15_96` / `A_X_20_96` add +50 / +100 % to that column. Hard
switching is on the N only. Phase copper (motor pad route and tongue, about
1.5 mΩ per phase, two phases conducting) heats the board, not the FETs.

| Phase current | Conduction | Dead time | N switching | FETs per motor | Phase copper | **Per motor on board** | Max-Rds case | Matrix AGM210MAP FETs, same model (`A_X_5_96`) |
|---|---|---|---|---|---|---|---|---|
| 1 A (hover) | 0.02 W | 0.03 | 0.01 | 0.06 | 0.00 | **0.06 W** | 0.07 | - |
| 2 A | 0.09 | 0.06 | 0.01 | 0.17 | 0.01 | **0.18 W** | 0.20 | - |
| 4 A | 0.38 | 0.13 | 0.02 | 0.52 | 0.05 | **0.57 W** | 0.64 | - |
| **6 A (rating)** | 0.84 | 0.19 | 0.03 | 1.06 | 0.11 | **1.17 W** | 1.33 | 1.37 |
| 12 A | 3.38 | 0.38 | 0.06 | 3.81 | 0.43 | **4.24 W** | 4.92 | 5.20 |
| 18 A (Vgs 3.0 V, 26.1 mΩ) | 8.67 | 0.56 | 0.08 | 9.31 | 0.97 | **10.29 W** | 12.11 | - |

Per FET at full duty (each conducts one third of the electrical cycle; the P
carries the dead-time share): at 6 A, P 0.21 W and N 0.14 W; at 12 A, P 0.72 W
and N 0.53 W; at 18 A and Vgs 3.0 V (Rp about 15 mΩ hot), P 1.78 W and N 1.26 W
(3 x 3.04 = 9.1 W per motor). Junction above case (V, RθJC): P 2.3 K/W x 1.78 W
= +4 K, N 6.4 K/W x 1.26 W = +8 K. The FET-local spreading rise above the
quarter average is the larger term, about 5-15 K/W (I, 06 §4.3 scaled to the
1/0.5 oz stack).

**Dead time, worst case** (I, datasheet limits). P turn-off is diode-commutated,
so it is an RC with no Miller plateau: the gate rises from 0 to VDD − |Vth|
through the EFM8 high-side driver plus RG, t = τ·ln(VDD/|Vth|). Typical (30 Ω +
3.7 Ω, Qg 7.5 nC / 4.5 V = 1.67 nF, |Vth| 0.9 V): 88 ns. Datasheet worst case
(driver ≤ 60 Ω from VOH ≥ VDD − 0.6 V at 10 mA, RG 7.4 Ω max, Qg 9.7 nC max =
2.16 nF, τ 145 ns, |Vth| 0.65 V min at 25 °C and about 0.46 V hot): **276 ns
cold, 326 ns hot** at 4.35 V. The N reaches its threshold within 5-13 ns, which
buys almost nothing back. DT 10 (204 ns) does not cover the worst case and DT 5
(102 ns) leaves no margin over the typical case; DT 15 (306 ns) covers it cold
and DT 20 (408 ns) hot. Hence the start build `A_X_20_48` and the extended V2
(§14). The CSD25404Q3 fallback (Ciss 1630 pF, Qg 14.1 nC max) needs about
372-440 ns, i.e. DT 20-25.

**Thermal estimate** (I, 03 §7 with its verification corrections). One motor
quarter has about 0.65 J/K; lateral spreading about 0.055 W/K over all layers;
the whole board sheds **0.042-0.11 W/K** (h 30-80 W/m²K over 13.9 cm², track 03
verification #15; track 06 §4 gives 30-60 W/m²K in flight). A whoop FC sits
under a canopy above the battery tray, not in the duct flow, so the low end is
plausible; V8 measures h on a board in a real frame under a canopy. The limit is
every part's own rating measured at that part: the 85 °C parts at the board
centre (RP2354A, gyro, SX1280, RTC6705, NOR) and the SE5004L case (85 °C) bind
before the FETs (100 °C) and the I-grade EFM8 (125 °C). At 25 °C ambient that is
a board rise ≤ 60 K, and ≤ 75 K minus the local hot spot at the hottest FET.

| Case (25 °C ambient, VTX 25 mW unless stated) | Heat | Board rise at 0.042-0.11 W/K | Loaded-channel hot spot | Needed for every part in rating |
|---|---|---|---|---|
| Hover, 1 A per motor | 3.3 W | +30-79 K | - | h ≥ about 39 W/m²K |
| Hover, VTX 400 mW | 3.8 W | +34-91 K | PA case about +10-20 K above the board (I) | h ≥ about 55-60 W/m²K |
| 6 A one channel, others 2 A | 1.17 + 3 x 0.18 + 0.11 trunk + 3.03 rest = 4.8 W | +44-116 K | +21 K | h ≥ about 64 W/m²K (71 with VTX 400 mW) |
| 4 A on all four | 4 x 0.57 + 0.20 + 3.03 = 5.5 W | +49-132 K | +10 K | h ≥ about 66 W/m²K |
| At mid h (55 W/m²K) | | | | about 5.0 A on one channel (3.5 A with VTX 400 mW), about 3 A on all four |
| 12 A for 10 s, one motor, from the measured hover steady state T0 | 4.2 W into 0.65 J/K | quarter +65 K (adiabatic upper bound) | P-FET local +5-12 K | from T0 = 40 °C already 110-117 °C; from a realistic T0 (55-104 °C) higher: **target, measured in V4** |
| 18 A for 3 s, Vgs 3.0 V | 10.3 W | quarter +46 K | P-FET local +13-31 K | from 40 °C 99-117 °C: **target, measured in V4** |

"Rest of board" is the §5.4 hover total without its own 0.22 W of hover FET loss
and 0.05 W of shunt (no double count); "trunk" is the 0.5 mΩ shunt plus about
0.7 mΩ of trunk copper at the pack current (O10). The continuous rating is set by
the 85 °C parts, i.e. by airflow; bursts are set by the FET local rise. Both are
published only as measured.

The battery path is the practical limit before the ESC: BT2.0 is rated 9 A
continuous / 15 A burst (V, BetaFPV) and a 300 mAh 75C pack 22.5 A (marketing).
Four channels at 6 A would be 24 A of pack current; the rating is per channel.

### 4.4 ESC MCU and firmware

| Option | Verdict |
|---|---|
| **EFM8BB51F16I + Bluejay** | chosen: runs from the cell (VDD 1.8-5.5 V), QFN-20 3x3 (10.9 mm² placed), proven 1S at `A_X_5_96` on the Matrix/Air/CrazybeeG473 (G grade there). The **I grade** (TA and TJ to 125 °C, V Tables 4.1/4.2) is required here: the G grade is TA 85 °C / TJ 105 °C abs max, a few mm from FETs that may reach 100-110 °C |
| AT32F421 + AM32 | no: VDD 2.4-3.6 V, needs a rail and a level shift for the P gate; QFN-28 4x4 (+7-8 mm²/channel) |
| EFM8BB21 | no: VDD max 3.6 V operating, cannot sit on a 4.35 V cell |

| Part | Primary | Fallback |
|---|---|---|
| ESC MCU | Silicon Labs **EFM8BB51F16I-C-QFN20R**, QFN-20 3x3, I grade; Digi-Key 7,228 at $0.62/2,500 (2026-10-07, 24 wk factory lead) - a NextPCB quote-engine channel, so turnkey; no LCSC listing found | no drop-in part exists (BB21 cannot run on the cell); the G-grade EFM8BB51F16G-C-QFN20R (C6547511, 31,643) only with a 85 °C limit at the EFM8 |

Per channel: VDD straight to its own cluster's +BATT copper (no series R), 1 µF
(Murata GRM033R61A105ME44D, C76935 [PU]) + 100 nF at the pin, returned to the
ESC's GND. The off-state P-gate level then tracks the P sources; the residual Vgs
excursion is the IR and L·di/dt difference between the VDD pin and the three P
source pads of the same cluster (tens of mV DC, ns spikes; I) against a hot P
threshold of about −0.46 V. It also keeps the BEMF pins (phase = VBAT + Vf
during commutation, through 10 kΩ) near the VDD + 0.3 V limit only by
microamps. DShot series 2.4 kΩ (Ralec RTT012401FTH, C166281 [PU]) to limit
injection into an unpowered EFM8 when only USB is connected (VDD + 0.3 V abs max
on I/O, 06 §1.9; 10 kΩ is the fallback if V9 shows EFM8 brown-out cycling on
USB); RSTb 1 kΩ pull-up to VDD (datasheet Fig 5.2, PINMAP F12; Yageo
RC0201FR-071KL [PU]); BEMF network of 6x 0201 (3 series to the comparator mux
pins, 3 to the virtual neutral, values from tinyPEPPER and checked against
layout A in P4); C2D and C2CK test pads for recovery flashing. Layout A pin use
(V, Bluejay `src/Layouts/BB51/A.inc`): P0.1 B_Mux, P0.2 C_Mux, P0.3 A_Mux, P0.4
V_Mux (neutral), P0.5 DShot; P1.0 A_Pwm (N gate), P1.1 A_Com (P gate, active
low), P1.2 B_Pwm, P1.3 B_Com, P1.4 C_Pwm, P1.5 C_Com; P2.0 C2D. Unused P0.0,
P0.6, P0.7, P1.6.

No gate resistors, by field record: tinyPEPPER (V, `single_esc.sch`) drives its
P+N gates straight from the EFM8, as do the BB51 layout-A whoop boards. The
datasheet's ≤ 60 Ω is the VOH limit at 10 mA, not a gate resistance: with a
typical driver of about 25-30 Ω the edge current is 4.35 V / (25-30 Ω + RG),
about 0.13-0.17 A for nanoseconds, above the 50 mA per-pin absolute maximum
(Table 4.1), which is a DC rating. Accepted on that record; if P2 has room, the
N gates get 0 Ω-option 0201 footprints.

### 4.5 FC MCU

| Criterion | RP2354A (house, OpenFC-Lite-Mini) | STM32G473CEU6 (Matrix, UD 4IN1) |
|---|---|---|
| Placed area with OSD | 95 mm² (PIO OSD front end 8 mm²) | 113 mm² (AT7456ELAH) |
| OSD current | about 5 mA front end | +43 mA typ AT7456E |
| OSD part stock | n/a | AT7456ELAH LGA-16: 78 at LCSC (fails the gate); HTSSOP-28 adds about 30 mm² |
| Betaflight maturity | core feature set in a release only since 2026.6.2 (2026-09-16); house maintainer contributes upstream. Known limits: bidirectional DShot decode shows about 5-8 % errors with spinning motors (upstream note in `dshot_bidir_pico.c`); everything runs on core 0 (`USE_MULTICORE` off in `target_RP2350.h`) | mature (BETAFPVG473_V2) |
| VTX control | MSP-VTX from the ELRS RX (§4.8) | same |
| Stock | 14,698 (LCSC); not on HQ Online | 750 (LCSC), 45 HQ Online |

**Decision: RP2354A.** It is the README constraint, it reuses the flown
OpenFC-Lite-Mini `rp2350a`, `imu` and `osd` sheets, and with the VTX driven by
the receiver nothing on the critical path depends on missing Betaflight
features. Its cost is firmware age, handled by the bench gates V9 in §14. Fallback
(documented, no dual footprint): STM32G473CEU6 + AT7456E HTSSOP-28.

| Part | Primary | Fallback |
|---|---|---|
| FC MCU | Raspberry Pi **RP2354A**, QFN-60 7x7 0.4 mm, 2 MB in-package flash, C41378174, 14,698 [PU] | ST STM32G473CEU6 (C1342773, 750) with AT7456E (new sheet) |
| 12 MHz crystal | TOGNJING **XTM25012000JT00351001**, 2520, C37635340, 6,040 [PU] | Abracon ABM8-272-T3 (RPi recommended, S) |
| Status LEDs | XINGLIGHT **XL-1005UGC** green (C965793) and **XL-1005UBC** blue (C22355736), 0402, sinking into GPIO7/26 from +3V3 [PU] | none verified. Not 0201: the commons-verified Kingbright APG0201 blue and green reach Vf 3.4 V and need a +4V5 anode (OpenFC-H7 lesson), which does not fit a 3.3 V sink drive, and GPIO26 is not 5 V tolerant (+1.2 mm² for the pair) |

`rp2350a` sheet reuse, changes: remove USB-C, CC and I2C pull-ups; USB D+/D−
(27-30 Ω series) to the SH1.0 connector; VBAT divider 100k/10k → 10k/10k; GPIO
map below; SWD to pads; boot button replaced by an FCB pad (QSPI_SS) next to a
GND pad.

**FC pin map (RP2354A, QFN-60; detail in PINMAP §2)**

| GPIO | Function | Peripheral |
|---|---|---|
| 0 / 1 | CRSF to ESP32 (ELRS RX; also serial passthrough) | UART0 TX/RX |
| 2 / 3 | spare, no-connect (the second user UART was dropped: Matrix II exposes one) | - |
| 4 / 5 | user UART pads TX1 / RX1 | UART1 TX/RX |
| 6 | gyro pin 9 (CLKIN for TDK; INT2 on BMI270, unused) | PWM slice 3A (32 kHz CLKIN) |
| 7 | LED0 green (status) | GPIO |
| 8 | LED strip, through a non-inverting translator (PINMAP F1; the OpenFC FET stage inverts) | PIO1 (WS2812) |
| 9 | gyro INT | GPIO IRQ |
| 10 / 11 / 12 / 13 | gyro SCK / MOSI / MISO / CS | SPI1 |
| 14 / 15 / 16 | OSD_W / OSD_EN / OSD_SYNC (must be consecutive) | PIO2 (FB OSD) |
| 17 | beeper (low-side FET) | GPIO / PWM slice 0B |
| 18 / 19 / 20 / 21 | NOR SCK / MOSI / MISO / CS | SPI0 |
| 22 / 23 / 24 / 25 | M4 / M3 / M2 / M1 | PIO0 (bidirectional DShot) |
| 26 | LED1 blue | GPIO (ADC0 unused) |
| 27 | spare, no-connect | (ADC1) |
| 28 | current sense | ADC2 |
| 29 | VBAT sense | ADC3 |

Conflict check (I, V in PINMAP §4): PIO0 holds DShot (29 of 32 instructions, 4
state machines). PIO1 holds only the WS2812 program (4 instructions, 1 SM). PIO2
holds the FB OSD (31 instructions), so the LED strip moves to PIO1 with
`PIO_LEDSTRIP_INDEX 1` (upstream defaults it to PIO2). PWM slices: 0B (beeper)
and 3A (CLKIN) are the only PWM users; GPIO 0/1 and 7 share those slices but are
muxed to UART/GPIO, so no conflict. DMA: SPI0 2, SPI1 2, OSD 2, LED strip 1, ADC 1
= 8 of 16 channels (DShot uses none, PINMAP F6).

### 4.6 Gyro

| Candidate | Stock | Note |
|---|---|---|
| **Bosch BMI270** | C2836813, 7,748, $2.66 [PU] | house current part; widely flown on 1S whoops; Betaflight 3.2 kHz ODR; house IMU study rates it "higher risk" for MEMS resonance on the 20x20 sister board; TA 85 °C |
| TDK ICM-42688-P (genuine) | C1850418, 3,029, $19.64 | house study's only "empirically proven" part; 8 kHz; CLKIN |
| ST LSM6DSV16X | 7,523 [PU] | rejected: house and Betaflight ecosystem call it unflyable |
| TDK ICM-45686 | 3 | no stock |

**Decision:** universal LGA-14 land of the OpenFC `imu` sheet (pins 2/3 GND,
10/11 NC, pin 9 to GPIO6), **BMI270 on the BOM**, ICM-42688-P qualified on the
same land. The prototype run is split 5 + 5 and a hover fly-off on the target
frame (noise metric §2 rank 6) picks the release population. One gyro per
revision, declared in the Betaflight target. Supply: own +1V8 from
TPS7A2018PDQNRM3 fed from +3V3 (double filtering of the 1 MHz boost ripple).

### 4.7 Receiver

The house design is the OpenRX-Lite ESP32-C3 + SX1281 circuit. Two facts from
the research change the MCU:

1. Mainline ExpressLRS 4.0.0, 4.1.0 and master register the VTX SPI and MSP-VTX
   devices only under `PLATFORM_ESP32 && !PLATFORM_ESP32_C3` (V, track 05
   verification, `src/src/rx_main.cpp`). A C3 cannot drive the VTX on ELRS 4.x.
2. ESP32-C3FH4 has 0 LCSC stock (2026-10-07), 89 on HQ Online (track 07); ESP8685H4 0.

| Option | Area (placed) | VTX control | Sourcing | Verdict |
|---|---|---|---|---|
| ESP32-C3FH4 + SX1281 (OpenRX-Lite) + separate VTX MCU | 86 + 25 mm² | VTX MCU on a half-duplex PIOUART (new code) running OpenVTx on a GD32F130 | C3FH4 0, GD32F130G6 broker-only | no |
| **ESP32-D0WD-V3 + 4 MB NOR + SX1280** | about 88 mm² | ELRS `devVTXSPI` + `MSPVTX` on the shipping code path; pin-compatible with ELRS layout `Generic 2400 Whoop Rx and VTx.json` (separate VTX SPI bus, like every upstream VTX layout) | 583 / 1,129 / 767 | **chosen**, subject to the fine-pitch EQ (below) |
| ESP32-PICO-V3 (SiP, crystal + flash inside, 0.5 mm pitch) + SX1280 | about 101 mm² | same | to be quoted (the older PICO-D4, C193707 2,272, is NRND at Espressif) | fallback |
| SPI ELRS on the FC | 37 mm² | none | - | not available on RP2350; locks ELRS v3/v4 to the BF build |
| ESP32-S3FH4R2 | 7x7 + crystal | same | 17 | no stock |

**Fine pitch.** ESP32-D0WD-V3 is QFN-48 5x5 at **0.35 mm pitch** (lead width
0.18 mm, Espressif datasheet). NextPCB publishes 0.38 mm as its fine-pitch
limit (track 07 S4) and JLC's PCBA floor is 0.35 mm, so the part is outside the
fab intersection. The copper gap (0.15-0.17 mm) sits on the 0.15 mm pad-to-pad
rule and the mask web after 0.04 mm expansion is 0.07 mm. Action (O15): the EQ
goes to NextPCB now. If accepted: 0.18 mm pads, one ganged mask opening per
side, and a scoped DRU exception for that footprint. If not: ESP32-PICO-V3
becomes primary (+13 mm² bottom, no external flash and crystal).

**Decision:** ESP32-D0WD-V3 with an external GD25Q32 flash and the CJ17 40 MHz
crystal, SX1280 radio. This deletes the VTX MCU (the Matrix's MM32F003), uses no
FC UART for the VTX and needs no Betaflight driver. The FC sees an MSP VTX over
CRSF (`USE_VTX_MSP`, in RP2350 releases from 2026.6.2). Pins follow
`Generic 2400 Whoop Rx and VTx.json` (V, ExpressLRS/targets 42ed776): CRSF on
ESP32 GPIO1/3, radio SCK/MOSI/MISO/NSS/RST 25/32/33/27/26, BUSY 36, DIO1 37,
RGB LED 22, VTX NSS/MOSI/MISO/SCK 19/18/23/5, PA bias PWM 12, PA detector 4,
PA enable (vtx_amp_vref) 2, button/boot 0. Two pins are added for the patched
firmware only (O6): GPIO21 = +3V3_VTX LDO enable (pulled up, so stock ELRS runs
the VTX as usual) and GPIO34 = PA NTC (ADC1). So the board can be flashed with
the existing generic target on day one; our own target adds a calibration
overlay. Straps: GPIO12 must read low at reset (3.3 V flash) and GPIO2 low
(pull-down), checked in P4; the first-flash procedure also burns the ESP32
VDD_SDIO eFuse to 3.3 V, which removes the GPIO12 strap risk for good.

The RF section is the OpenRX-Lite / OpenAIO `rx_esp32c3_sx1281` circuit reused
(TCXO, filter, match, LDO-mode radio), with these changes: MCU swap; SX1281 →
SX1280 (pin-compatible, same ELRS driver, stock); 15 µH DC-DC inductor deleted
(the ELRS layout has no `radio_dcdc`, so the DC-DC is never enabled); ceramic
antenna deleted, wire-antenna plated hole instead; **fix the sheet defect:
SX1281/SX1280 pin 5 is GND and is unconnected on both sibling sheets** (09
verification). Sheet name `rx_esp32_sx1280` (new file, since the MCU changed).

**Wi-Fi (PINMAP F9, decided).** The Matrix II has a Wi-Fi chip antenna, and ELRS
users configure and update over Wi-Fi, so the board keeps it: a minimal radiator
on ESP32 LNA_IN, a short printed stub on L6 at the board edge with a 0201 pi
match and a 2 x 4 mm all-layer copper keepout (about 1 m of range is the goal,
measured in V7); Johanson 2450AT18B100E (3.2 x 1.6 mm chip antenna, Digi-Key, S)
is the fallback if the stub does not reach it. ELRS calls `disableVTxSpi()`
when Wi-Fi starts, so auto-Wi-Fi would leave the VTX dark until the next reboot:
the target overlay turns auto-Wi-Fi off, and Wi-Fi is started on demand (Lua,
bind button). ELRS flashing otherwise goes through Betaflight serial
passthrough; recovery is holding RXB at power-up (ROM download over
U0TXD/U0RXD, reachable through passthrough). There are no extra ESP32 UART pads:
they would put a second driver on the FC's UART0_TX net.

| Part | Primary | Fallback |
|---|---|---|
| RX MCU | Espressif **ESP32-D0WD-V3**, QFN-48 5x5 (0.35 mm pitch), C967021, 583 | Espressif ESP32-PICO-V3, QFN-48 7x7, 0.5 mm pitch (S; stock to quote); crystal and flash inside, +13 mm² |
| RX flash | GigaDevice **GD25Q32EEIGR**, 32 Mbit, USON-8 2x3, C2973794, 1,129 | Winbond W25Q32JVUUIQ, USON-8 3x4, C2999380, 3,575 |
| 40 MHz crystal | JSCJ **CJ17-400001010B20**, 1612, C2875272, 13,110 [PU] | none verified; the NextPCB quote names a global 1612 part or the line is consigned |
| Radio | Semtech **SX1280IMLTRT**, QFN-24 4x4, C125969, 767 | Semtech SX1281IMLTRT, C2151551, 0 at LCSC, 146 HQ Online [PU] |
| 52 MHz TCXO | YXC **OW7EL89CENUNFAYLC-52M**, 2016, C22434896, 5,975 [PU] | 52 MHz 2016 crystal per the Matrix (MPN in P3) |
| 2.4 GHz LPF | TDK **DEA102700LT-6307A2**, 1005, C574024, 3,810 [PU] | Johanson 2450FM07D0034T, C2651081, 0 today [PU] (re-match) |
| RGB LED | XINGLIGHT **XL-1010RGBC-2812B**, 1x1 mm, C5349953, 364,820 [PU] | none (single source; WS2812-class 1x1 parts differ in pinout) |

Numbers: +13 dBm, no PA/LNA (Matrix ELRS layout `Generic 2400`,
`power_values [13]`, V). Radio in LDO mode costs about +6 mA (20 mW). ESP32 ELRS
load about 0.07 A; rail average 0.10 A, 0.15 A peak in flight.

### 4.8 VTX and OSD

| Question | Options | Decision |
|---|---|---|
| Synthesiser | RTC6705/RTC6705A (QFN-40 6x6; Fc 5725-5865 MHz over −40..85 °C, V); MAX2871/LMX2572 discrete (9-10 mm square, unproven for video) | **RTC6705 or RTC6705A**; no alternative exists (04 §2.4) |
| PA | RFPA5542 (Matrix, EOL 2023, 5 V only), SKY85743-21 (4.2-5.5 V, LGA 3x5), SE5004L (5.15-5.85 GHz, VCC 3.0-5.5 V, case ≤ 85 °C), QPA9501 (to 5.9 GHz, 124 pcs), TQP5525 (to 5.925 GHz, 25 pcs) | **SE5004L-R** on the cell; QFN-20 4x4 footprint shared by six PAs (04 §3.3), so QPA9501/TQP5525 drop in if they reach the stock gate |
| Control | separate VTX MCU (Matrix MM32F003), Betaflight RTC6705 driver (2 levels, `#undef` on RP2350), FC-integrated new driver, ELRS RX MCU | **ELRS ESP32 `devVTXSPI` + `MSPVTX`** (§4.7) |
| OSD | AT7456E + 27 MHz crystal (40 mm², 50 mA, LGA 78 pcs); PIO FB OSD | **PIO FB OSD** (OpenFC `osd` sheet minus the COS8051 buffer), front end on the bottom |
| Harmonic filter | none (Matrix) vs LTCC BPF | **Walsin 1608 BPF**; guarantees 20 dB at 10.3-11.7 GHz, 12 dB at 7.25-7.8 GHz (V, Walsin PI V01); 2f of the channels above 5850 MHz (11.7-11.9 GHz) and 3f are unspecified; power handling must be confirmed with Walsin |
| Connector | U.FL, MHF4, soldered coax | **U.FL** (what whoop antennas ship with) |

Chain: camera CVBS → 75 Ω → SN74LVC1G3157 (camera / OSD level) → RTC6705 video
network (OpenOSD-X reference values) → RTC6705 PAOUT1 (+2 dBm) → 10 pF DC block
→ 50 Ω CPWG < 5 mm → SE5004L → match → BPF → U.FL. RTC6705 on +3V3_VTX.

**PA drive stage (inverting, strap-safe; PINMAP F15).** ELRS raises output by
lowering the PWM count (`VTxOutputIncrease` decrements; YOLO uses the minimum
count, pit the maximum; V, `devVTXSPI.cpp`), so a follower would turn the VPD
loop into positive feedback. Stage: ESP32 GPIO12 (10 kHz PWM) → two-pole RC
(corner ≤ 100 Hz, ≥ 40 dB at 10 kHz so no PWM ripple reaches the PAOUT1 supply
in the video band) → Q1 NPN common emitter (the RC and the base-emitter path
hold GPIO12 low at reset) → Q2 NPN emitter follower → RTC6705 PAOUT1 choke
supply. Both transistors are one Nexperia **BC847QASZ** (NPN/NPN, DFN1010B-6).
**Hardware cap:** Q1's collector load is a divider (top to +3V3_VTX, bottom to
GND) whose open-circuit voltage sets the highest Q2 base voltage, so PAOUT1
supply ≤ V_div − 0.65 V. V5 sizes the divider so that a maximum-gain SE5004L
(32 dB typ, 3 dB spread per band; P1dB up to 34 dBm) at cold and 4.35 V stays at
or below 400 mW; without it, YOLO drive (+2 dBm into 30-32 dB gain) would
saturate the PA anywhere between about 0.2 and over 1 W across parts, channels
and VCC. A DAC drive on ESP32 GPIO25/26 (ELRS supports it) would need the radio
SCK/RST moved and break the generic-layout pin compatibility: not used.

**PA enable and bias.** PA pin 5 (VREF/EN): GPIO2 through a 0201 series R with a
10 kΩ pull-down. The SE5004L needs VREF 2.80-2.90 V at IEN about 10 mA (abs max
3.6 V, V); an ESP32 GPIO (VOH ≥ 0.8 x VDD at rated drive) through 39 Ω lands at
about 2.6-2.85 V, so the series R is fitted from V5 (0-15 Ω) with the GPIO drive
strength fixed in the target, and VREF and Icq versus VREF are measured on the
first boards (track 04 bench item 2). If the window cannot be held, a 2.85 V
reference switched by GPIO2 replaces the resistor. Detector: PA DET → 1 kΩ /
100 pF → ESP32 GPIO4 (SE5004L DET 0.325-1.0 V fits the ELRS 0-1 V window; its
accuracy is specified only up to 5.85 GHz). PA VCC: 10 µF + 1 nF + 100 pF at the
pins, no ferrite: a 220 Ω power bead is about 0.3-1.5 µH below 10 MHz and with
the 10 µF it resonates at 50-150 kHz with Q 3-7, right where the ESCs put their
ripple (lean rule). The 3-pad jumper selects PA VCC = +BATT (default) or +5V. A
0201 NTC (Murata NCP03XH103F05RL, S) next to the PA feeds ESP32 GPIO34 for the
thermal derate (O6).

**RF pads.** On the 77 µm L1-L2 dielectric the 50 Ω line is about 0.105 mm wide
(§8.2), while the U.FL signal pad and the DC-block, match and BPF pads are much
wider: over solid L2 a U.FL centre pad is about 0.3-0.5 pF, |Γ| about 0.26-0.40 at
5.8 GHz (I). So L2 is cut out under the U.FL signal pad and under every RF pad
wider than about 0.3 mm, with GND poured on L3 under that area as the local
reference (named rule area `RF_PAD_CUTOUT`), verified with the KiCad calculator
or an EM solver at P5. No DNP filter footprint is added on the line: its empty
pads would be the same discontinuity. RTC6705 NC pads (1-4, 12-18, 36-37; 13 of
40 per the OpenOSD-X reference) may be removed from the land if P5 needs the
escape channels; the EP is never touched.

| Part | Primary | Fallback |
|---|---|---|
| Synthesiser | RichWave **RTC6705** (or RTC6705A), QFN-40 6x6. **0 authorised stock** (LCSC 0, HQ Online 0, Digi-Key none); brokers: Win Source 30,000 at $7.82-11.73 (findchips, 2026-10-06). **Fails the stock gate; consigned with traceability (§15)** | none exists |
| 8 MHz reference | Yajingxin **TAXM8M4RDBCCT2T**, 3225, 10 pF, ±10 ppm, C400090, 169,935 | YXC X322508MSB4SI, 3225 (S); P3 looks for a 2520 part (−3.4 mm²) |
| PA | Skyworks **SE5004L-R**, QFN-20 4x4, 3.0-5.5 V, 5.15-5.85 GHz, C210263, 1,339 (HQ Online 0; Digi-Key 21 wk) | Qorvo QPA9501TR13, same footprint, to 5.9 GHz, C2911573, 124 (prototype only; fails the 50-board gate); Skyworks SKY85743-21, LGA-24 3x5, C5348950, 568 (5 V, new footprint) |
| BPF | Walsin **RFBPF1608060K98Q1C**, 5150-5950 MHz, 1608, C2442150, 12,780 | TDK DEA165538BT-2263A1-H, C2835388, 3,975 (clips 5945 MHz) |
| U.FL | Hirose **U.FL-R-SMT-1(80)**, C88374, 65,975 [PU] | I-PEX 20279-001E-03 (MHF, mates U.FL plugs; S) |
| PAOUT1 choke | Murata **LQP03TN4N7H02D** 4.7 nH 0201, C86126, 37,747 | none verified (value re-tuned if the part changes) |
| PA drive stage | Nexperia **BC847QASZ**, NPN/NPN, DFN1010B-6, C549491, 227,680 (V) | Nexperia BCM847QASZ (matched pair, same package, S) |
| PA NTC | Murata **NCP03XH103F05RL** 10 kΩ 0201 (S) + 0201 divider R | none verified |
| OSD switch | TI **SN74LVC1G3157DTBR**, X2SON-6, C2673087, 1,545 [PU] | none (TI single source in X2SON) |
| OSD sync comparator | TI **TLV7031DPWR**, X2SON-5, C2876045, 6,241 [PU] | none verified |
| OSD clamp diode | Diodes **SDM02U30LP3-7B**, DFN0603, C151629, 16,750 [PU] | none verified |

`osd` sheet reuse, changes: drop COS8051 and its 3 resistors (the switch output
drives the RTC6705 network, about 1.47 kΩ, not a 75 Ω cable); scale the level
divider about 5x down (top about 750-820 Ω, Thevenin about 190 Ω). That keeps the
OSD_W pin at ≤ 3 mA (Betaflight leaves it at the default 4 mA drive and sets only
the slew rate, `osd_pico.c`) and loses about 11 % of the level into the 1.47 kΩ
network, trimmed in the ratio at P4. OSD levels are absolute, so with AC-coupled
cameras they move against the picture's black level: V9 measures black and white
on the target cameras, and a sync-keyed clamp is added only if needed.

**Pit, disarm and heat** (I, 04 §6, 06 §4; V from the ELRS and Betaflight source).
PA at 400 mW draws about 0.55 A from the cell (2.0 W at 3.7 V, 1.64 W heat); at
25 mW about 0.30 A (PA quiescent dominates). Stock ELRS pit drops VREF and sets
the maximum PWM count but never powers the RTC6705 down (`POWER_AMP_OFF` is
defined but unused), so pit still leaks the RTC6705's own output through the off
PA (measured in V5) and keeps its 0.5 W on the board. `vtx_low_power_disarm`
sends power index 1, which ELRS turns into "VPD setpoint 0, maximum count" with
VREF **on** (`checkOutputPower()` → `RfAmpVrefOn()`): a disarmed quad that left
pit keeps the PA biased at about 0.25-0.3 A, 1.0-1.1 W. Release requirements
(O6, ELRS patches): index 1 handled as pit (VREF off); pit and disarm power the
RTC6705 down (GPIO21 low on the +3V3_VTX LDO enable, VTX SPI pins tri-stated,
frequency re-sent at power-up) or at least write `POWER_AMP_OFF`; a thermal
derate from the PA NTC. Defaults: pit on boot (RCE), 25 mW,
`vtx_low_power_disarm` ON (pit once the patch is in; until then the README says
to switch pit on before landing or benching). 400 mW is continuous only at high
airflow (PA case ≤ 85 °C needs h ≥ about 55-60 W/m²K, §4.3) and is
time-limited otherwise (τ 26-69 s). 400 mW from a 3.0 V sagged cell is not
guaranteed on a minimum-P1dB SE5004L (about 25.2 dBm, 04 §3.4): published as
measured.

### 4.9 Blackbox

| Option | Body | Stock | Verdict |
|---|---|---|---|
| **W25Q128JVPIM**, WSON-8 6x5, on SPI0 | 30 mm² | C2441427, 24,670 | **chosen** (Matrix parity, deep stock) |
| GD25Q128EQIG / PY25Q128HA-QVH, USON-8 4x4 | 16 mm² | no distributor found | later (−16 mm² placed) |
| NOR on the RP2354A QSPI bus, CS1 | 1 GPIO instead of 4 | - | no: flight-unvalidated driver, XIP stall risk (05 §1.2) |

The W25Q128JVPIM is the "I" grade (−40..85 °C, V), one of the 85 °C parts that set
the board limit with the RP2354A. The 105 °C "J" grade W25Q128JVPJM/JVPJQ (same
land, V Winbond ordering table) would not raise that limit, but is taken if the
P0 BOM quote shows stock (none at Digi-Key on 2026-10-07). Fallback: Winbond
W25Q128JVPIQ, C190862, 6,862 (same land, also 85 °C). The NOR is not placed
under the PA (§10). `blackbox` sheet keeps its name, bus (SPI0, GPIO18-21) and CS
pull-up; microSD removed.

### 4.10 Connectors and pads

| Item | Decision | Part / geometry | Why |
|---|---|---|---|
| Battery | BT2.0 pigtail (22 AWG, 40 mm, user-fitted), two plated holes **Ø 1.1 mm finished** in 3.0 x 2.0 mm pads (long side along the edge), both sides, ≥ 12 power vias (0.40/0.20) per pad into the pours | no PCBA part | a wire through a PTH cannot peel the pad. Stranded 22 AWG is 0.75-0.8 mm before tinning and the PTH tolerance is ±0.075 mm, so Ø 1.1 keeps ≥ 1.025 mm. The board check runs with `--min-hole 2.0` (mounting holes are the outline cut-outs), so the hole size follows the wire, not the script |
| Motors | 12 solder pads 1.0 x 1.8 mm on the top, each with a plated **Ø 0.5 mm wire-anchor hole**, pitch 1.5 mm, at the board edge facing each motor | no PCBA part | Matrix "solder-required" equivalent. A Matrix-style 1.25 mm THT plug does not fit the fab-rule intersection (pad-with-hole to pad-with-hole 0.40 mm at NextPCB with a 0.20 mm PTH ring → pitch ≥ 1.30 mm), and four SMD PicoBlade headers cost 173-212 mm² |
| USB | JST **BM04B-SRSS-TB(LF)(SN)**, SH1.0 4-pin vertical, bottom, C160390, 44,655 | fallback BM04B-SRSS-TBT(LF)(SN), C495539, 2,334 (same land) | as on the Matrix; BetaFPV adapter pinout to be measured and matched |
| Camera | JST **BM03B-SRSS-TB(LF)(SN)**, SH1.0 3-pin vertical, top, front, C160389, 31,415, plus CAM / 5V / GND pads | fallback BM03B-SRSS-TBT(LF)(SN), C495538, 1,156 | Matrix CAM IN plug; first area lever if P2 does not close (§9.3) |
| VTX antenna | U.FL, top, front half | §4.8 | |
| RX antenna | plated hole Ø 0.5 mm for an insulated λ/4 wire (31 mm), left edge, rear half, bottom | - | Matrix uses the same; best radiator for the area |
| User pads | TX1 RX1 5V GND (UART1, left edge), LED 5V GND (LED strip, right edge), BZ+ BZ− (buzzer, rear edge), CAM 5V GND (camera, at the plug): 12 pads 1.0 x 1.2 mm, top | - | Matrix II parity (UART1 G/T1/R1/5V, LED 5V/L/GND, BZ+/BZ−, CAM/GND/5V) |
| Test pads | FCB (RP2354 QSPI_SS boot) + GND, RXB (ESP32 GPIO0), CLK / DIO (FC SWD), 8x C2D/C2CK (ESC) | Ø 0.8 mm | no tact switch (saves about 7 mm²) |

---

## 5. Power budget

### 5.1 +5V rail loads (design)

| Load | A at 5 V | Note |
|---|---|---|
| Camera | 0.12 | allowance (BetaFPV C03: 100 mA at 5 V, V) |
| +3V3 (FC: RP2354A, NOR, OSD front end, LEDs, INA186, gyro via +1V8) | 0.09 | I |
| +3V3_RX (ESP32 ELRS + SX1280 LDO mode + RGB LED) | 0.10 | I, 0.15 peak |
| +3V3_VTX (RTC6705) | 0.10 | 95 mA datasheet figure for 13 dBm mode, conservative for PAOUT1 only |
| LED strip | 0.20 | user allowance |
| Buzzer | 0.03 | |
| User 5 V pads | 0.05 | allowance |
| **Total** | **0.69 A (3.45 W)** | 0.41 A without the user allowances; 1.25 A if the PA is moved to +5V. USB only: 0.29 A (no camera, no PA) |

### 5.2 Every load from the cell, at 3.0 V and 4.35 V

| Load | at 3.0 V in | at 4.35 V in | Basis |
|---|---|---|---|
| Boost input for 0.69 A at 5 V | 1.31 A (η 0.88) | 0.86 A (η 0.92) | TPS61022 efficiency curves (S) |
| SE5004L PA, pit / 25 / 100 / 400 mW | 0 / 0.30 / 0.35 / 0.55 A | same | I (Icq 300 mA spec, 04 §6.1); out of rating below 3.0 V |
| 4x EFM8BB51 at 49 MHz | 0.020 A | 0.020 A | V (55.5 µA/MHz), I (peripherals) |
| VBAT divider | 0.0002 A | 0.0002 A | |
| **Cell current (no motors), VTX pit** | **1.33 A / 3.98 W** | **0.88 A / 3.84 W** | |
| VTX 25 mW | 1.63 A / 4.88 W | 1.18 A / 5.14 W | |
| VTX 100 mW | 1.68 A / 5.03 W | 1.23 A / 5.36 W | |
| **VTX 400 mW** | **1.88 A / 5.63 W** | **1.43 A / 6.23 W** | |
| ESC per motor at hover / 6 A / 12 A | 0.06 / 1.17 / 4.24 W of loss on the board | same | §4.3 |

### 5.3 5 V margin (P0 gate)

TPS61022 with 0.47 µH (Isat 7.5 A), 1 MHz, η 0.88, per TI SLVSDX7D §8.2.2.2
(inductance −30 % = 0.33 µH; I): at 3.0 V in, D = 0.47, ripple 4.3 A, peak held
to 80 % of Isat → **2.04 A** nominal peak against 0.69 A (**+196 %**); at 2.8 V
in, **1.90 A (+175 %)**; with nominal inductance 2.37 / 2.21 A. With the PA on
+5V (1.25 A): +63 % at 3.0 V. Gate "≥ 20 % margin at 3.0 V on datasheet
curves": **pass** on the calculation. Limits that keep it a calculation: Cout
(≥ 20 µF effective above 1.5 A; two 0603 give 17-22 µF at 5 V), inductor ripple
far above TI's 40 % guidance, inductor Isat below the valley limit plus ripple
(soft saturation, §4.2), and heat: 2.2 A out at 2.8 V is about 1-1.5 W of loss in
a package with ΨJB 36.7 K/W (V) on a 60-80 °C board, near the 150 °C thermal
shutdown. So the published figure is V1 measured continuous at flight board
temperature, claim ≤ 1.5 A.

### 5.4 Thermal budget (on-board heat)

| Source | Hover, VTX 400 mW, 3.7 V | Hover, VTX 25 mW | Bench, disarmed, pit (stock ELRS) | Bench, disarmed after leaving pit (stock ELRS) | Bench, pit, RTC6705 off (patched ELRS) | USB only |
|---|---|---|---|---|---|---|
| PA | 1.64 W | 1.09 W | 0 | 1.0-1.1 (Icq, VREF on) | 0 | 0 |
| RTC6705 + its LDO | 0.50 | 0.50 | 0.50 | 0.50 | about 0 | 0.50 |
| FC rail (LDO + loads) | 0.45 | 0.45 | 0.45 | 0.45 | 0.45 | 0.45 |
| RX rail (LDO + loads) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| Boost loss / OR diode | 0.38 | 0.38 | 0.25 | 0.25 | 0.25 | 0.07 |
| ESC MCUs | 0.07 | 0.07 | 0.07 | 0.07 | 0.07 | 0 |
| ESC FETs (1 A/motor) | 0.22 | 0.22 | 0 | 0 | 0 | 0 |
| Shunt + copper | 0.05 | 0.05 | 0 | 0 | 0 | 0 |
| **Total** | **3.8 W** | **3.3 W** | **1.8 W** | **2.8-2.9 W** | **1.3 W** | **1.5 W** |
| Board rise (flight G 0.042-0.11 W/K; bench still air 0.025-0.035 W/K) | +34-91 K | +30-79 K | +51-71 K | +79-115 K | +36-51 K | +43-61 K |

At 25 °C ambient the 85 °C parts allow +60 K. In flight that needs h ≥ about
39 W/m²K at 25 mW and about 55-60 at 400 mW (PA case). On the bench in still air
only the patched pit case (RTC6705 off) stays inside; until the ELRS patch is
merged the README requires a bench fan or short sessions, and "disarmed after
leaving pit" is the case that cooks the PA (V8 measures it). Camera, LED strip
and buzzer power is dissipated off the board. Time constant in flight about
26-69 s (C about 2.9 J/K).

---

## 6. Weight (detail of §1)

| Item | Estimate |
|---|---|
| PCB 6L 1.0 mm, 1 oz outer (60 % cover) / 0.5 oz inner (85 %), 6.97 cm² | 1.8-1.95 g |
| FETs 12x 3.3x3.3 + 12x 2x2 | 0.40 g |
| ICs and crystals | 0.52 g |
| Passives (about 220) | 0.08 g |
| Connectors (2x SH1.0 vertical, U.FL) | 0.13 g |
| Solder | 0.12 g |
| **Total** | **3.1-3.4 g** (target ≤ 3.5 g) |

1 oz inner copper would add about 0.3 g; 0.8 mm board would save 0.26 g but
BetaFPV moved from 0.8 to 1.0 mm for crash survival, so 1.0 mm stays.

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
| Panel | 4 tabs with mouse bites at the middle of the straight edges, clear of pads, with a ≥ 1.0 mm part keepout around each (MLCC crack risk near breakouts); positions fixed at P2 with the NextPCB panel EQ |
| Guides | 25.5 and 26.0 mm frame patterns drawn on `User.Eco1`; front marked on `User.Eco2` |

---

## 8. Stackup and fab rules

**Owner rule: through vias only.** Filled-and-capped via-in-pad (IPC-4761 Type
VII, non-conductive epoxy) is a through via and is used in every pad that holds
a via. No blind, buried or laser vias (the NextPCB track 07 recommendation of HDI
1+4+1 is overridden by the owner rule). The via is the OpenDrone standard
**0.35/0.20** (D6: owner-confirmed buildable at NextPCB).

### 8.1 DFM intersection (NextPCB ∩ JLCPCB)

NextPCB values: track 07 (S1 standard capabilities, S2/S3 advanced and HDI pages,
S4 assembly, S12 stackup library, verified 2026-10-06). JLCPCB values:
capabilities page read 2026-10-07 (https://jlcpcb.com/capabilities/pcb-capabilities).

| Rule | NextPCB | JLCPCB | **This board** |
|---|---|---|---|
| Min track / space, 1 oz outer | 0.08 / 0.08 mm | 0.09 / 0.09 mm (multilayer; 3 mil only in BGA fan-out) | **0.09 / 0.09** |
| Min track / space, 0.5 oz inner | 0.065 / 0.08 mm | 0.09 / 0.09 mm | **0.09 / 0.09** |
| Min mechanical drill | 0.15 mm (boards ≤ 1.2 mm) | 0.15 mm (0.10 only ≤ 1.0 mm, ENIG/OSP) | **0.20** (no smaller hole is planned; the DRC minimum enforces the standard via) |
| Via annular ring | 0.09 (1 oz table) / 0.10 (via-row image); owner: 0.35/0.20 builds (D6) | via dia ≥ hole + 0.10 (0.15 preferred) | **0.075 → via 0.35 / 0.20** (D6) |
| PTH (component) annular ring | 0.20 (image) | 0.15 abs min, 0.20 recommended | **0.20** |
| Hole to hole, same net | 0.20 | 0.20 (via) | **0.20** |
| Hole to hole, different nets (vias) | 0.30 (CAF) | 0.20 (via) | **0.30** |
| Pad-hole to pad-hole (PTH pads) | pad-with-hole to pad-with-hole copper 0.40 | 0.45 hole to hole | **0.45 hole edge, 0.40 copper** |
| Via hole to track | 0.18 | 0.20 | **0.20** |
| PTH hole to track | 0.23 | 0.28 (0.35 recommended) | **0.28** |
| NPTH to track | 0.20 | 0.20 | **0.20** |
| Inner-layer via hole to copper | (0.18) | 0.20 | **0.20** |
| Inner-layer PTH hole to copper | - | 0.30 | **0.30** |
| SMD pad to pad, different nets | 0.15 | 0.15 | **0.15** |
| SMD pad to track | 0.10 | 0.10, and ≥ 0.09 from a mask opening to a trace | **0.13** (0.04 mask expansion + 0.09) |
| Fine-pitch IC | 0.38 mm pitch (S4) | 0.35 mm (PCBA floor) | **0.38**; the ESP32-D0WD-V3 (0.35) only with a NextPCB EQ approval and a scoped exception (§4.7, O15) |
| Copper to routed edge | 0.20 | 0.20 | **0.20** (components 0.30) |
| Mask expansion | ≥ 0.04 (1.5 mil) | 1:1 allowed (LDI) | **0.04** |
| Mask bridge, green | 0.089 (copper gap) | 0.10 | **0.10** (green only; black 0.127/0.13); ganged opening on the 0.35 mm-pitch ESP32 sides |
| Silk line / text height | screen 0.127 / 0.76; inkjet 0.08 / 0.61 | 0.15 / 1.0 | **0.15 / 1.0** for every label, both sides (interim: the commons standard 0.8 / 0.13 is below JLC's floor; owner decision O11) |
| Pad to silk | 0.15 | 0.15 | **0.15** (template rule) |
| NPTH min | 0.40 | 0.50 | **0.50** |
| Plated slot min | 0.50 | 0.35 | **0.50** |
| Thickness options, 6L | 0.8 / 1.0 / 1.2 ..., ±0.1 mm below 1.0, ±10 % from 1.0 | 0.8 / 1.0 / 1.2 ..., same tolerance | **1.0 ± 0.1** |
| Copper | outer 1/2 oz, inner 0.5/1/2 oz | same | **1 oz outer, 0.5 oz inner** |
| Via-in-pad | non-conductive fill + cap, Type VII, +$12.55 per 10 pcs, +4 days | epoxy filled & capped, **default for 6L and up**, 0.15-0.55 mm holes | **Type VII on every via in a pad** |
| Impedance tolerance | ±10 % | ±10 % (±5 % on request) | **50 Ω ± 10 %** |
| Assembly spacing | 0201 0.20-0.25 mm, 0402 0.25-0.30 mm (NextPCB blog, June 2026) | no published rule | **0.20 body/land, 0.25 between two 0402**; JLCDFM check on the P2 floorplan |

### 8.2 Stackup

6 layers, 1.0 mm, from the NextPCB library entry `6L-1.0mm-0.5oz-1080` (V,
track 07 §1.4). JLCPCB builds 6L at 1.0 mm with 0.5 oz inner by default; its
exact 1.0 mm dielectric build was not readable (its stackup page lists only 1.6
mm builds), so the JLC equivalent and the RF width are confirmed with the JLC
stackup selector (EQ item, O4).

| Layer | Thickness | Role |
|---|---|---|
| F.Mask | 0.015 | green |
| **L1 F.Cu** | 0.035 (1 oz finished) | top parts (VTX, P-FETs, EFM8s, CAM plug), 5.8 GHz CPWG, video, VTX control, phase pours, local +5V/+3V3 pours |
| prepreg 1080 | 0.077 | εr 4.2 |
| **L2 In1.Cu** | 0.0175 | **solid GND** (RF and top-side reference, ESC return); cut only under wide RF pads (§4.8) |
| core | 0.30 | |
| **L3 In2.Cu** | 0.0175 | digital signals between the sides; **references L4** (0.103 mm away) about three times more than L2 (0.30 mm) |
| prepreg 2313 | 0.103 | |
| **L4 In3.Cu** | 0.0175 | **+BATT plane** (ESC feed), one solid pour under every L3 route: no islands or slots where L3 carries tracks |
| core | 0.30 | |
| **L5 In4.Cu** | 0.0175 | **solid GND** (bottom-side reference, ESC return) |
| prepreg 1080 | 0.077 | |
| **L6 B.Cu** | 0.035 | bottom parts (FC, RX, power, N-FETs, OSD front end), 2.4 GHz feed, Wi-Fi stub, local +5V/+3V3 pours |
| B.Mask | 0.015 | green |

Dielectric + copper = 0.997 mm; KiCad's sum including both masks is 1.027 mm
(that is the figure `board_spec.json` checks). Layer roles follow the line
standard F sig / In1 GND / In2 sig / In3 PWR / In4 GND / B sig (LINEUP B1). The
NextPCB 6L library builds are core-prepreg-core, so the thin prepreg always sits
between L3 and L4; the board lives with it: L4 stays an unbroken +BATT pour (an AC
reference through the distributed MLCCs) wherever L3 routes, the +5V/+3V3
distribution is local pours on L1/L6 (or L3 islands outside routing channels),
and **video, gyro SPI, analog sense and VTX control never route on L3**: they go
on L1 over L2 or L6 over L5. Where an L3 route changes layer, a GND via and a
+BATT decoupling cap within 2 mm carry the return. DRU encoding: classes Analog
and RF disallowed on In2.Cu/In3.Cu, and In3.Cu holds only the +BATT zone except
inside named rule areas that keep In2.Cu tracks out. Finish ENIG, green mask,
white legend, vias tented both sides except Type VII in pads.

Impedance (P1 field solver, `hardware/tools/impedance.json`): 50 Ω CPWG on L1
over L2 with a 0.15 mm gap and mask = **0.105 mm** (49.6 Ω at εr 4.2, 50.9 Ω at
3.91); the earlier 0.139 mm was a bare microstrip figure that this build does not
reproduce. 2.4 GHz feed on L6 over L5 has the same geometry. Each fab's
impedance tool confirms its width for the actual build before P5 RF routing;
if they differ, one common build or a width per fab is frozen (O4). USB FS:
nets `USB_D_P` / `USB_D_N` (KiCad diff-pair suffix), 0.12 / 0.12 mm pair,
length-matched, not impedance-critical at 12 Mb/s.

### 8.3 Vias

| Preset | Size | Use |
|---|---|---|
| Signal | 0.35 / 0.20 mm (annular 0.075) | default; every via in a pad (Type VII), including the GND/power vias of 0201 decoupling caps (drill inside the pad) |
| Power | 0.40 / 0.20 mm (annular 0.10, same drill) | +BATT, GND and phase arrays outside pads, where the wider ring helps inner-layer connection |

0.20 mm via in 1.0 mm board: aspect ratio 5:1, about 1.4 mΩ each (18 µm plating,
JLC average). Counts: ≥ 12 power vias per battery pad (25 A), ≥ 8 per ESC
cluster feed (in the P source pads), 8 per phase tongue, 9 in the PA EP, 4-9 in
each QFN EP. Array pitch ≥ 0.40 mm from the 0.20 mm same-net hole rule. Remove
unused inner annular rings.

### 8.4 Board setup values (P1, applied by `setup_board.py`)

Constraints: clearance 0.09, track 0.09, connection 0.09, via 0.35 / 0.20,
annular 0.075, minimum through hole 0.20, hole-to-hole 0.20, hole clearance 0.20,
copper-to-edge 0.20, microvia minimums left at the template values (0.20 / 0.10)
and microvias, blind and buried vias disallowed by a custom rule; solder mask
expansion 0.04, mask minimum web 0.10; silk minimum text 1.0 mm / 0.15 mm line.
Track presets 0.10, 0.105 (RF), 0.14, 0.20, 0.30, 0.50, 1.00.

Net classes (names after OpenAIO; colours set through netclass directive
labels):

| Class | Nets | Track | Clearance | Via | Colour |
|---|---|---|---|---|---|
| Default | signals | 0.09 | 0.09 | 0.35/0.20 | - |
| VBAT | +BATT_IN, +BATT, shunt nodes | 0.50 (pours) | 0.15 | 0.40/0.20 | red |
| Phase | 12 motor phase nets | 0.50 (pours) | 0.15 | 0.40/0.20 | orange |
| Gate | 24 FET gate nets | 0.15 | 0.10 | 0.35/0.20 | yellow |
| Power | +5V, VBUS, +3V3, +3V3_RX, +3V3_VTX, +1V8, +1V1 | 0.25 | 0.09 | 0.35/0.20 | magenta |
| Analog | video, OSD level/sync, VBAT/current sense, PA detector | 0.10 | 0.15 | 0.35/0.20 | cyan |
| RF | 5.8 GHz chain, 2.4 GHz feed | 0.105 | 0.15 | 0.35/0.20 (fence) | green |
| USB | USB_D_P / USB_D_N | 0.12 (pair gap 0.12) | 0.12 | 0.35/0.20 | blue |
| GND | GND | 0.20 | 0.09 | 0.40/0.20 | - |

Power net names per the lineup decision: +BATT, +5V, +3V3, +1V8, GND, with
suffixed rails +BATT_IN, +3V3_RX, +3V3_VTX, +1V1 and VBUS.

Custom rules below the template marker: different-net hole to hole 0.30; PTH
pad hole to hole 0.45; PTH annular 0.20; PTH hole clearance 0.28; inner-layer PTH
hole to copper 0.30; NPTH to copper 0.20; SMD pad to track 0.13; disallow
micro/blind/buried vias; courtyards at max(body, land) + 0.10 with
`courtyards_overlap` raised to **error** and courtyard clearance 0 (touching
courtyards = 0.20 mm); 0402-to-0402 +0.05; tall parts (U.FL, SH1.0, 2520
inductor) +0.5 mm to 0201/0402; user pads and battery/motor pads ≥ 0.5 mm to any
0201/0402 (iron rework); Analog/RF off In2.Cu/In3.Cu (§8.2); keepout rule areas
for the grommet flanges, the RF zones and `RF_PAD_CUTOUT` (§10); a scoped mask
exception for the ESP32 footprint if the EQ passes.

KiCad features (owner rule). Delivered in P1 by `setup_board.py`: the 16
template-ignored DRC checks re-enabled (D7), component classes `PASSIVE_0201`,
`PASSIVE_0402`, `TALL`, `SOLDER_PAD` driving the spacing rules, net-class
priorities and colours, the DRU self-test. Still to deliver: a design block (or
multichannel placement) for ESC1-4 (P2), the own check that every copper item
lies inside Edge.Cuts shrunk by 0.20 mm (P2), zone priorities written down with
the pours (P5: +BATT on L4 over the islands rule, GND fills last), a jobset for
the fab outputs (P7). Follow-ups for `setup_board.py` from this revision: minimum
through hole 0.20 (it writes 0.15), the USB class pattern `*/USB_D_P`,
`*/USB_D_N`, the In2/In3 class rule and `RF_PAD_CUTOUT`.

---

## 9. Area budget

### 9.1 Usable area per side

Outline (I, `outline.py`, 10 µm grid): body 697.0 mm² − front arc 7.2 + ears
35.7 − holes 28.9 = **696.6 mm²**. Usable for parts, per side: inside a 0.30 mm
edge band and outside Ø 5.2 mm grommet-flange keepouts around the 3 holes
(flange diameter assumed; measure a BetaFPV ball at P2) = **643.6 mm²**.

### 9.2 Placed area per block (0.2 mm body/land spacing, perfect tiling)

Method (I, `budget.py` v2): each part counts (land L + 0.2) x (land W + 0.2),
lands at IPC density L (0201 0.80 x 0.35, 0402 1.30 x 0.55, 0603 2.10 x 0.90,
leadless ICs body + 0.1). Labels count their Tokyo glyph box at 1.0 mm height
plus 0.15 mm mask clearance on each side (about 3.5 mm² for three characters).
Vias that cannot sit in a pad need free area on both sides: 150 such vias
(signal layer changes, stitching, fences, power arrays outside pads) x 0.28 mm²
on each side (I; 0201 decoupling vias sit in their pads, and tented vias may sit
under silk art, which the estimate does not credit). The margin to 100 % is for
outer-layer tracks and placement loss. v1 of this table read 79.3 % on the top;
its own script gave 81.4 % (a label line was copied as 20.0 instead of 33.2 mm²).

| Block | Parts | Top mm² | Bottom mm² | Notes |
|---|---|---|---|---|
| ESC x4 | 96 | 261.4 | 113.8 | 4x QFN-20, 12x SON 3.3x3.3, 40x 0201 top; 12x SON 2x2, 12x 0201, 8x 0402, 8 C2 pads bottom; via tongues +36 top / +24 bottom |
| Input, protection, sense | 15 | - | 31.9 | 2x 0603, SOD-123FL, 1206 Kelvin shunt, SC-70-6, 10x 0201 |
| FC core (RP2354A, beeper, LED-strip translator, LEDs, test pads) | 41 | - | 94.1 | QFN-60, 2520 crystal, 2016 inductor, X2SON-6 translator (F1), 5 test pads |
| Gyro + 1.8 V LDO | 7 | - | 13.7 | |
| PIO OSD front end | 12 | - | 8.1 | moved to the bottom (lever 1) |
| Blackbox NOR | 3 | - | 35.7 | WSON-8 6x5 |
| RX (ESP32 + flash + SX1280 + LDO + Wi-Fi stub) | 41 | - | 97.2 | Wi-Fi stub keepout 8 mm² + 3x 0201 (F9) |
| VTX (RTC6705, PA, BPF, U.FL, LDO, drive stage, NTC) | 60 | 127.6 | - | BC847QAS + 7x 0201 (F15), no PA ferrite |
| Power (boost, FC LDO, OR diode, camera filter) | 16 | - | 32.8 | SOD-123F OR diode, 0603 Cin |
| Connectors | 2 | 28.8 | 33.6 | SH1.0-3 vertical (T), SH1.0-4 vertical (B) |
| **Components** | **293** | **417.8** | **460.8** | |
| Pads, labels, silk art | | 152.2 | 124.0 | T: motor pads 32.8; battery 17.5; 12 user pads 20.2 + labels 43.3; M1-M4, + −, 1S, ANT 28.1; ANT hole 2.0; connector names 8.4. B: motor PTH rings 17.3; battery 17.5; ANT 2.0; logo + OPEN/AIO/WHOOP + REV1 41.7; test-pad and USB labels 23.7; C2 labels 21.8 |
| Via allowance | | 42.0 | 42.0 | 150 vias x 0.28 mm² |
| **Total** | | **612.0 mm²** | **626.8 mm²** | |
| **Share of 643.6 mm²** | | **95.1 %** | **97.4 %** | gate ≤ 85 %: **fail** |

Without the via allowance (the v1 method) the same parts give 88.6 % / 90.9 %.
The Matrix II reaches about 45-50 % package-body coverage per side (01 §5.2)
with 12 dual-FET packages where this board has 24 discrete FETs plus tongues.

### 9.3 What gives if P2 does not close

**The P0 area gate does not pass on the budget.** Levers, in order, with the
result per side (`budget.py` cases):

| Step | Lever | Top | Bottom |
|---|---|---|---|
| 0 | this freeze (OSD front end on the bottom, UART2 dropped, VDD resistors and PA ferrite removed) | 95.1 % | 97.4 % |
| 1 | owner: C2 pads exempt from labels (LINEUP 7), labels at the commons 0.8 mm (O11, O13) | 91.8 % | 92.9 % |
| 2 | P3: VTX LDO in X2SON (or LP5912-3.3), 2520 8 MHz crystal | 90.6 % | 92.9 % |
| 3 | camera pads only, no SH1.0 plug (Matrix has the plug) | 85.7 % | 92.9 % |
| 4 | P-FET to CSD25310Q2 2x2 (−94 mm² top, rating about 5 A = Matrix class), then NOR and input block to the top | about 82 % | about 82 % |
| 5 | HDI, put to the owner with these numbers (owner rejected HDI for OpenAIO) | | |

Without step 4 or 5 the bottom stays above 85 %; dropping Wi-Fi saves only
1.5 points. P2 proves the real placement (the via allowance is an estimate in
either direction) and the owner decides between steps 3-5 if P2 confirms this
budget (O14).

---

## 10. Floorplan sketch

Coordinates: KiCad top view, origin at the body centre, +x right, +y down,
body ±13.2 mm. Flight-forward points at the top-right corner (+x, −y).
Motors (Betaflight quad-X): **M4 front-left beyond the top edge, M2 front-right
beyond the right edge, M1 rear-right beyond the bottom edge, M3 rear-left beyond
the left edge**. Ears with holes at the left (−12.875, −12.875), rear
(−12.875, +12.875) and right (+12.875, +12.875) corners; front corner rounded.

| Block | Side | Region | Notes |
|---|---|---|---|
| ESC3 / ESC4 (M3, M4) | P + EFM8 top, N bottom (offset) | left-ear quadrant (x < −2, y < −2) | motor pad centres M4 on the top edge at x −8.5 / −7.0 / −5.5; M3 on the left edge at y −8.5 / −7.0 / −5.5 (clear of the r 2.6 flange); FETs inboard of their pads, EFM8 behind them |
| ESC1 / ESC2 (M1, M2) | P + EFM8 top, N bottom (offset) | right-ear quadrant (x > 2, y > 2) | M1 pads on the bottom edge at x +5.5 / +7.0 / +8.5; M2 on the right edge at y +5.5 / +7.0 / +8.5 |
| VTX: RTC6705, PA, BPF, U.FL | top | front half: RTC6705 near the centre, PA about (+5, −5), BPF + U.FL about (+7.5, −7.5) toward the front corner | 5.8 GHz chain on L1 over solid L2 (cut under wide pads); PA ≥ 10 mm from the gyro; NTC beside the PA |
| CAM plug + CAM/5V/GND pads | top | right edge upper half (front-right), about (+10.5, −4) | camera cable enters from the front; video path CAM → OSD switch (bottom) → RTC6705 stays in the front quadrant, away from ESC currents |
| OSD front end | bottom | under the CAM plug area, about (+9, −2) | not under the PA or RTC6705 EPs |
| User pads | top | TX1 RX1 5V GND on the left edge (y −4…+1.5); LED 5V GND on the right edge (y −1…+3.5); BZ+ BZ− on the rear edge (x −2…+1, clear of the B− pad) | spread over three edges (about 14 mm needed at 1.5 mm pitch is not free at the rear-left corner) |
| Battery pads B+ / B− | both (THT) | rear edge, centres about (−8.4, +11.4) and (−4.8, +11.4), 3.0 x 2.0 pads long side along the edge | pigtail exits rearward; inside the 13.0 copper line and outside the rear flange; "1S" and + − on top silk |
| Power entry: TVS, 2x 22 µF, shunt, INA186 | bottom | inboard of the battery pads (y +8…+10) | Kelvin taps from the shunt pads; boost VIN taps after the shunt |
| Boost (TPS61022 + 2520 L) | bottom | about (+1, +10.5) | ≥ 5 mm from the gyro, the TCXO and the 2.4 GHz feed; hot loop < 3 mm |
| FC: RP2354A + 12 MHz + 3.3 µH | bottom | centre, about (+1.5, −1.5) (body y −5…+2) | core SMPS layout per the RPi guide |
| Blackbox NOR | bottom | right of the MCU, about (+8, −1) | not under the PA (X-ray and heat) |
| Gyro (BMI270) + 1.8 V LDO | bottom | centre-rear, about (−1, +5.5) | clear of the MCU body; ≥ 10 mm from the PA (top front), ≥ 5 mm from the boost, ≥ 4 mm from FET clusters, ≥ 2 mm from switch nodes, re-checked at P2 |
| RX: ESP32 + flash + crystal | bottom | left of centre, about (−6, −3) | Wi-Fi stub at the nearest free edge with its keepout |
| SX1280 + TCXO + LPF | bottom | left edge, rear half, about (−7, +4) | 2.4 GHz feed ≤ 6 mm to the antenna hole |
| RX antenna hole | through | left edge about (−12.3, +7) | wire laid along the left/rear-left frame arm, away from the pigtail (≥ 5 mm from the battery pads) and from the VTX antenna |
| USB SH1.0 vertical | bottom | left edge, about (−10.5, +1) | plug from below |
| Test pads FCB, GND, RXB, CLK, DIO; ESC C2 pads | bottom | near the MCU / under each EFM8 | |
| Silk art: incutec logo, OPEN / AIO / WHOOP, REV1 | bottom | free patch in the front-right quadrant | |

RF keepouts:
- **5.8 GHz**: no copper on L1 within 0.15 mm (CPWG gap) of the line except the
  coplanar GND; L2 solid under the whole chain plus 1 mm, except the
  `RF_PAD_CUTOUT` areas under the U.FL signal pad and RF pads wider than about
  0.3 mm (L3 GND as their reference); via fence ≤ 2.5 mm pitch both sides; no via
  in the RF path; U.FL ground tabs with ≥ 4 vias to L2; no other parts within
  1 mm of the line on L1.
- **2.4 GHz**: CPWG on L6 over L5 from the LPF to the antenna hole; all-layer
  copper keepout r = 1.0 mm around the hole except the feed; no parts within
  3 mm on the wire's exit path; Wi-Fi stub keepout 2 x 4 mm on all layers.
- **Antenna separation**: VTX antenna (U.FL, front, up-rear to the canopy) and
  RX wire (left edge, along the frame) ≥ 20 mm apart, orthogonal where possible.
- **Aggressors**: boost ≥ 5 mm from the TCXO and the 2.4 GHz feed; RP2350
  150 MHz x 16 = 2400 MHz and ESP32 40 MHz harmonics sit in band, so V7 runs with
  every aggressor active.

---

## 11. Layout rules specific to this board

- **Commutation loops**: one 100 nF 0201 per half-bridge, on the bottom
  between the N source (GND) and a +BATT via from the P source pad; loop P source
  → P drain leads → tongue → phase vias → N → cap ≤ 4 mm² through 1 mm of board
  (re-measured on the drawn cell at P2). Target N-FET VDS overshoot ≤ 9 V at 18 A
  turn-off (12 V part).
- **Phase copper**: P drain leads into a tongue beside the P package; 8 Type VII
  0.35/0.20 vias from the tongue into the offset N drain pad; N source GND vias
  on free area on the top (D10); phase to motor pad ≥ 1.2 mm wide on L1 and
  repeated on L6 with stitching; solid pad connections (no thermal relief) on
  FET pads.
- **+BATT path**: battery pad (`+BATT_IN`) → shunt (Kelvin) → `+BATT` on L6 pour
  + L4 plane + L1 pours at the clusters; ≥ 12 power vias at each battery pad; per
  cluster ≥ 8 vias in the P source pads. Size the trunk for 25 A pack, each
  channel for 12 A bursts. Battery-to-shunt corridor in a rule area before
  routing.
- **GND**: L2 and L5 unbroken (no splits under any signal; the only L2 openings
  are the RF pad cut-outs), L1/L6 pours stitched every ≤ 3 mm at the board
  perimeter and around the RF.
- **L3/L4**: L4 is one solid +BATT pour under every L3 route; no Analog, RF or
  video on L3 (§8.2).
- **Gyro isolation**: no switch nodes (boost SW, phase nodes) on any layer within
  2 mm of the gyro; its 1.8 V LDO and decoupling on the same side; gyro centred
  away from the PA and boost as in §10.
- **Video ground**: camera return enters L2 at the CAM plug; video traces on L1
  over L2 (or L6 over L5) with GND on both sides, never on L3; no ESC return
  current through the front quadrant; 100 pF shunts at video entry points;
  RTC6705 loop filter ≥ 5 mm from the boost.
- **Boost**: Cin at VIN, Cout–SW–GND hot loop < 3 mm, SW copper minimal, MODE
  tied to VOUT (forced PWM), EN to VIN, VIN from `+BATT` after the shunt, not
  through ESC copper.
- **Crystals**: 12, 40 and 8 MHz next to their ICs with GND guard, no signal on
  L2 under them; TCXO likewise.
- **Exposed pads and X-ray**: EFM8, RTC6705, PA, SX1280, ESP32, RP2354A EPs
  soldered and Type VII via-in-pad. NextPCB X-rays every QFN/LGA board, and 2D
  X-ray cannot separate bottom-terminated packages that overlap between sides:
  no top/bottom overlap of QFN/SON/LGA/WSON footprints; where the offset P/N
  pairs still overlap partly, angled or CT X-ray is requested in the EQ. The
  bottom reflows first; the heaviest parts per pad area are the SH1.0 vertical
  connectors at about 0.01 g/mm², below the common 30 g/in² (0.047 g/mm²)
  second-side guideline (I).
- **0201 on planes**: thermal relief spokes 0.10-0.15 mm, equal copper on both
  pads (tombstoning).
- **Hand-solder pads**: battery and motor pads get a copper neck so a 60-80 W
  iron can heat them; mask-defined edges.

---

## 12. Firmware targets

| Firmware | Plan |
|---|---|
| Betaflight | New board config `OPENAIO_WHOOP` in betaflight/config (manufacturer ID to request; proposal INCU), `FC_TARGET_MCU RP2350A`, derived from the house OPENFC_LITE_MINI_RP2350A target. Requires release ≥ 2026.6.2. Defines: SPI1 gyro (BMI270 or ICM42688P, one per revision), `ENABLE_FB_OSD` with OSD_W/EN/SYNC = GPIO14/15/16, `PIO_LEDSTRIP_INDEX 1`, UART0 = serial RX (CRSF), UART1 = pads, `USE_VTX_MSP`, `USE_FLASH` W25Q128 (m25p16 driver) on SPI0 CS GPIO21, motors on PIO0 GPIO25/24/23/22 = M1-M4, bidirectional DShot, `DEFAULT_ALIGN_BOARD_YAW` ±45 (diamond mount; sign fixed in P4 with the gyro orientation), current scale 500 and VBAT scale measured, beeper inverted per driver. Full config in PINMAP §5 |
| Bluejay | Stock Bluejay ≥ 0.21, layout **BB51 "A"** (no custom layout). Start **`A_X_20_48`** (DT 408 ns covers the datasheet worst-case P turn-off, §4.3); step down to `A_X_15_x`, `A_X_10_x` or `A_X_5_96` only after the extended dead-time test (§14, V2). All are stock builds (Makefile `DEADTIMES` 0 5 10 15 20 25 30 40 50 70 90 120, `PWM_FREQS` 24 48 96, V). Flash through Betaflight 4-way passthrough; C2 pads for recovery. Publish the chosen build and the reasoning |
| AM32 | not applicable (EFM8 MCU) |
| ExpressLRS | Day one: `Unified_ESP32_2400_RX` with the generic layout `Generic 2400 Whoop Rx and VTx.json` (pin-compatible). Release: a target entry in ExpressLRS/targets that uses that layout plus an overlay with this board's VPD/PWM calibration arrays, LED index for the single RGB LED, `power_values [13]`, no `radio_dcdc`, auto-Wi-Fi off. ELRS ≥ 4.1. First flash also burns the VDD_SDIO eFuse to 3.3 V. **Release gates (upstream patches, O6):** (1) fix `LinearInterpVpdSetPointArray()` / `LinearInterpSetPwm()` (missing `break`, so the last segment always wins, and an integer slope that is 0 below 100 counts per 100 MHz: today every channel from 5651 to 5949 MHz gets the 5850 MHz values); (2) closed-loop 200 and 400 mW VPD setpoints (the detector is accurate at 23-27 dBm; the YOLO setpoint 2250 counts is above the DET range, so YOLO is open-loop full drive); (3) power index 1 handled as pit (VREF off); (4) pit and disarm power the RTC6705 down (GPIO21, VTX SPI tri-stated, frequency re-sent) or write `POWER_AMP_OFF`; (5) L band removed from the pushed table (or documented unsupported); (6) thermal derate from the PA NTC on GPIO34 |

---

## 13. Silkscreen plan

Per LINEUP-CONVENTIONS B2-B14 and the owner rules: no component silkscreen, no
reference designators, no "Drone" anywhere on a fabricated layer, Tokyo font
embedded, back text mirrored, bold upper-case pad codes of ≤ 3 characters, one
code table shared by schematic pad values, silk, pinout and README. Size: 1.0 mm
/ 0.15 mm line on both sides as the interim value that meets both fabs; the
commons standard (0.8 mm high, 0.6 wide, 0.13 stroke) is below JLC's published
1.0 / 0.15 floor, so that conflict goes to the owner (O11) and the outcome is
recorded in DECISIONS.md.

| Side | Content |
|---|---|
| Top | pad labels: **TX1 RX1 5V GND**, **LED 5V GND**, **BZ+ BZ−**, **CAM 5V GND**; **M1 M2 M3 M4** at each motor pad group (Betaflight order: M4 front-left, M2 front-right, M3 rear-left, M1 rear-right); **+ −** (2.0 mm; the 4-6 mm ESC style of LINEUP B8 does not fit at whoop density) and **1S** at the battery pads; **ANT** at the RX antenna hole; connector names **CAM** and **VTX** with pin-1 marks. No forward arrow: it is outside the owner's silk list (pad labels, connector name + pin-1, port group frames, board name/rev/logo), so the front is marked on `User.Eco2` and in the README unless the owner approves the arrow (O12) |
| Bottom | incutec logo ≥ 6.1 x 1.4 mm; product name **OPEN / AIO / WHOOP** stacked in Tokyo; **REV1** (equal to the board title-block rev `rev1`); test-pad labels **FCB RXB CLK DIO GND** (FCB = FC boot, replaces the 4-character BOOT); connector name **USB** with pin-1 mark; ESC C2 pads: owner exemption requested for flashing test points (LINEUP 7, O13), otherwise codes **D1-D4** (C2D) and **C1-C4** (C2CK) |
| Off-board | `User.Eco2` note marking the front; mounting-pattern guide on `User.Eco1`; grommet-flange keepouts as rule areas |

---

## 14. Validation plan

| # | Test | Pass / fail |
|---|---|---|
| V1 | 5 V rail: VIN 4.35 → 2.6 V, loads 0.69 A and 1.25 A; then the continuous load the boost holds for 10 min with the board at flight temperature (60-80 °C) | +5V ≥ 4.85 V at VIN ≥ 2.8 V; ripple ≤ 50 mV p-p; no FC/RX reset to 2.5 V; cold start from 3.0 V; the measured continuous figure is the published BEC rating (claim ≤ 1.5 A) |
| V2 | ESC dead time: scope P gate, N gate, phase node, per-ESC supply current; builds DT 20/15/10/5 at 48 and 96 kHz; VIN 2.5, 3.0 and 4.35 V; FET case heated to 100 °C; all six gate pins of each EFM8 (slowest pin found); 3 boards x 4 ESCs | no shoot-through spike > 2x the steady current; P fully off (Vgs > −0.3 V) before N on, at every corner. `A_X_15_x` and `A_X_20_x` are acceptable outcomes |
| V3 | N-FET overshoot at 18 A turn-off | VDS ≤ 9 V |
| V3b | Unplug surge: battery pulled at hover throttle with props on the bench, scope on +BATT and on one EFM8 VDD, 10 repeats | peak recorded; if it exceeds 5.5 V the README warns against unplugging spinning, and the risk stays in §15.4 |
| V4 | ESC rating protocol: 1S from a real pack (or 3.7 V supply with the pack's resistance), stated; board in a frame under a canopy, motor + prop in propwash (stated airflow), 25 °C; VTX at 25 mW (and a 400 mW run); one channel stepped 4/5/6/8 A while others run 2 A, then all four at 3/4 A; bursts started from the measured hover steady state | every part inside its rating, measured at the part: hottest FET ≤ 100 °C, EFM8 ≤ 125 °C, RP2354A, gyro, SX1280, RTC6705, NOR and SE5004L case ≤ 85 °C (thermocouples on the hottest FET, the loaded channel's EFM8, the PA case, the RTC6705, the RP2354A and the gyro); bursts ≤ 110 °C on the FET at the end of 12 A 10 s and 18 A 3 s. Publish the curve; same rig on a Matrix II |
| V5 | VTX power: 25/100/400 at 5645, 5650, 5750, 5850, 5917, 5945 MHz and the full channel table; VIN 2.8/3.0/3.7/4.35 V; calibrated power sensor; PA case temperature logged; synthesiser lock at 5645 and 5945 MHz; pit leakage at the U.FL; VREF and Icq versus VREF; the hardware cap sized on a max-gain part cold at 4.35 V | 25 and 100 mW within ±1.5 dB at 5850 MHz and ±3 dB elsewhere (±1.5 dB after the ELRS fix); 400 mW at the cap ≤ 400 mW on every part; PA case ≤ 85 °C; frequency error ≤ ±200 kHz; all values published |
| V5b | Video with motors loaded: SNR and 48/96 kHz sidebands with all four motors at 4-6 A, PA on +BATT and on the +5V jumper | no visible bars; sidebands reported; jumper default confirmed |
| V6 | VTX spurious with the BPF, on a spectrum analyser to ≥ 18 GHz | 2nd harmonic ≤ −30 dBm at every channel incl. 5880-5945 MHz; 3f reported; RTC6705 half-frequency leakage (2.8-2.97 GHz) reported |
| V7 | RX: sensitivity and desense with every aggressor active (motors at hover and at 6 A, VTX 400 mW, OSD on, blackbox logging, boost loaded); Wi-Fi range with the stub | within 2 dB of the SX1280 figure; ≤ 3 dB desense; Wi-Fi works at 1 m |
| V8 | Thermal: board at 25/100/400 mW in a real frame under a canopy (derives h); bench still air and fan; cases of §5.4 incl. "disarmed after leaving pit" (Icc and temperature) and patched pit | matches §5.4 within ±30 %; pit-on-boot verified; PA case and 85 °C parts logged |
| V9 | FC gates on RP2350 (2026.6.2+): bidirectional DShot with Bluejay BB51 at hover and full throttle (30 min) - RPM-filter notches track the motor lines in blackbox, no RPMFILTER arming block, decode error rate within upstream's stated band (about 5-8 % spinning, < 1 % at 0 rpm); DShot300 vs 600 compared; 4-way passthrough flash and settings of all 4 ESCs; MSP-VTX from ESP32 ELRS over CRSF (band/channel/power from OSD and Lua); cold boot x 20 with and without the TX on, timing VTX state restore against ELRS's 5 s MSP-VTX window; FB OSD with 2-3 target cameras PAL and NTSC (black and white levels); SPI NOR blackbox at 2 kHz with the ICM-42688-P at 8 kHz and FB OSD, task load and loop overruns (single core); ELRS flash through serial passthrough; USB only: +BATT voltage, EFM8 brown-out cycling, TPS61022 start attempts; power-up sequence on a scope (FT pads against the EFM8 pull-ups before IOVDD) | each passes, else its fallback (C2 pads, AT7456E/G473 respin, SPI NOR on another bus, 10 kΩ DShot series R) |
| V10 | Gyro fly-off BMI270 vs ICM-42688-P (5 + 5 boards) | release population has the lower pre-filter noise and no resonance peak in the motor band |
| V11 | Weight | ≤ 3.5 g bare |
| V12 | Crash: BetaFPV protocol, 4 boards, 20 hits | 0 failures, ears included |
| V13 | Outline and holes on Air65 II / Air75 II (25.5) and Meteor65 Pro II / Meteor75 Pro (26.0) frames with BetaFPV balls | fits all four without reaming |

---

## 15. Risks, open questions, sourcing

### 15.1 README design questions

| README question | Status | Answer / what is still open |
|---|---|---|
| VTX part | **proposed-resolved (sourcing risk open)** | RTC6705/RTC6705A stays (no equivalent exists); PA SE5004L-R; authorised RTC6705 stock is zero, so it is a consigned, traceable broker line with incoming tests; 24 of the 40 supported channels are inside both datasheet bands |
| Power stage | **proposed-resolved, area open** | P+N direct drive from the EFM8 (I grade) on the cell, CSD25402Q3A + CSD13202Q2 with the cell drawn from the real lands, Bluejay layout A starting at DT 20. The README premise that direct drive needs AM32-style 120-140 dead times holds only for 1-2S level-shifted designs; 1S direct drive ships at DT 5 (Bluejay) and DT 25 (AM32 SP8). The area gate may force the 2x2 P-FET (§9.3) |
| Electronics rail | **proposed-resolved** | TPS61022 forced-PWM boost, calculated 1.9 A nominal peak at 2.8 V against a 0.69 A load, published figure measured (V1); PA on the cell; split LDOs |
| Motor connection | **proposed-resolved for rev1; plugs open** | solder pads with wire-anchor holes; a 1.25 mm THT plug violates the fab-rule intersection and SMD plugs do not fit |
| Antenna | **proposed-resolved** | RX wire monopole at the left edge (bottom), VTX U.FL in the front half (top), 5.8 GHz BPF, Wi-Fi through a minimal printed stub |

README constraints this spec proposes to change once accepted (README is not
edited by this freeze): mounting 25.5 x 25.5 mm → 25.75 mm pattern with Ø 3.5 mm
grommet holes (fits 25.5 and 26.0 frames); "LCSC basic parts preferred" →
NextPCB partial turnkey by MPN, JLCPCB-compatible DFM; receiver "reusing OpenRX
Lite" → OpenRX-Lite RF section with an ESP32 MCU (ELRS 4.x VTX control);
"VTX dependency" → consigned traceable RTC6705.

### 15.2 Other open questions

| # | Question | Decided by |
|---|---|---|
| O1 | SE5004L output on the cell at 2.8-4.35 V (400 mW at sag) | bench V5 before P4 freeze; the +5V jumper is the fallback |
| O2 | Grommet flange diameter (keepout Ø 5.2 assumed) | calipers on a BetaFPV ball before P2 |
| O3 | BetaFPV SH1.0 USB adapter pinout | measure before P4 |
| O4 | JLC 6L 1.0 mm dielectric build and RF width (one build or a width per fab) | JLC stackup selector and both impedance tools before P5 |
| O5 | CSD25402Q3A vs CSD25404Q3 land compatibility | P3 |
| O6 | ELRS release gates (§12: interpolation fix, 200/400 mW closed loop, index 1 = pit, RTC6705 power-down in pit, L band, thermal derate) | ELRS PRs (firmware); release blocked until (1)-(4) merge |
| O7 | Walsin BPF power handling at 400 mW | ask Walsin; VNA |
| O8 | RP2350 firmware gates (V9) | OpenFC-Lite-Mini + external whoop ESC bench before P5 |
| O9 | Matrix II physical teardown (layer count, BEC part, ball size) | buy one |
| O10 | 1 oz inner copper (+0.3 g, about −0.15 W at 25 A) | only if V4 misses |
| O11 | Pad-label size: commons 0.8 / 0.6 / 0.13 vs JLC 1.0 / 0.15 floor | owner; recorded in DECISIONS.md |
| O12 | Forward arrow on silk (LINEUP B9 SHOULD, outside the owner silk list) | owner |
| O13 | ESC C2 flashing pads unlabelled (LINEUP 7) or coded D1-D4 / C1-C4 | owner |
| O14 | Area gate: camera plug, 2x2 P-FET or HDI if P2 confirms §9.3 | P2 result, then owner |
| O15 | ESP32-D0WD-V3 at 0.35 mm pitch (NextPCB 0.38 published) | NextPCB EQ now; else ESP32-PICO-V3 |
| O16 | Plated Ø 3.5 holes with a GND annulus (Matrix practice) | P2 with O2 and the ear-survival result of V12 |
| O17 | NextPCB BOM quote by exact MPN on the full BOM (HQ Online / Digi-Key stock per line) | P0 close |

### 15.3 Sourcing plan

Partial turnkey at NextPCB: NextPCB sources the lines its HQ Online stock and
quote engine (Digi-Key, Mouser, Element14, Avnet, ...) can fill; the lines below
are consigned (fee $50 per 50 consigned lines, parts must arrive within the
7-working-day window as cut tape with leaders, MSL parts in dry bags, marked "C"
in the BOM; V, track 04/07).

| Line | Why consigned | Buy (10-board prototype / 50-board run) |
|---|---|---|
| RTC6705 / RTC6705A | no authorised stock | 15 / 60 from a traceable broker or agent; incoming test on 3 (SPI register read 0x00 = 0x0190, frequency within ±200 kHz, PAOUT1 power) |
| SE5004L-R | not on HQ Online | 15 / 60 (LCSC 1,339) |
| RP2354A | not on HQ Online | 15 / 60 (LCSC 14,698) |
| ESP32-D0WD-V3, GD25Q32EEIGR, SX1280IMLTRT | LCSC-only stock today | 15 / 60 each |
| CSD25402Q3A, CSD13202Q2 | if the quote engine misses them | 150 / 650 each |
| EFM8BB51F16I-C-QFN20R | only if the quote engine misses Digi-Key's 7,228 | 50 / 220 |
| LCSC-centric lines not yet checked at NextPCB channels: cjiang FTC252012SR47MBCA, Yajingxin TAXM8M4RDBCCT2T, TOGNJING XTM25012000JT00351001, JSCJ CJ17-400001010B20, YXC OW7EL89CENUNFAYLC-52M, XINGLIGHT XL-1010RGBC-2812B, Ralec RTT012401FTH, Walsin RFBPF1608060K98Q1C; W25Q128JV (HQ Online showed 2 pcs of JVPIQ) | O17 decides per line: consign, or swap to a globally stocked equivalent (Murata, Abracon or Kyocera crystals; Murata or TDK inductors) | per BOM quantity + 20 % |
| Everything else | turnkey (HQ Online / Digi-Key / Mouser stock, confirmed by O17) | - |

NRE estimate for 10 boards (I, track 07 prices): PCB 6L 1.0 mm with 0.20 mm
vias and Type VII about $220; double-sided assembly $105 plus joint and X-ray
fees (about $50-150); parts about $600 including the broker RTC6705s; freight
$50-100: **about $1,000-1,200**. Lead time about 4 weeks door to door (external
parts case).

### 15.4 Risks carried

| Risk | Mitigation |
|---|---|
| RTC6705 fake or remarked parts | traceable source, incoming tests, 10 spares from the same lot |
| Area: the budget fails the 85 % gate on both sides (§9.3) | P2 placement proof first; levers with numbers; the owner decides camera plug / 2x2 P-FET / HDI |
| Routing closure with through vias only | P2 channel-capacity probe; via allowance in the budget |
| Overvoltage on unplug with spinning props: EFM8, PA, boost, LDOs and 6.3 V MLCCs exceed their ratings above about 5.5-7 V; the TVS keeps only the FETs (Matrix parity) | V3b measures the surge; README: disarm (props stopped) before unplugging |
| Reversed user-fitted pigtail loses the board | silk + README; factory fit priced at P7 |
| No USB ESD array (house practice) | 27 Ω series resistors; risk accepted |
| RP2350 Betaflight features three weeks into a release; DShot decode error band; single core | V9 gates on existing house hardware before P5; G473 fallback documented |
| ESP32 strap pins shared with VTX control (GPIO2, GPIO12) | pull-down on GPIO2; GPIO12 held low by the RC and Q1 base path; VDD_SDIO eFuse burned at first flash |
| ESP32 0.35 mm pitch outside the NextPCB limit | EQ (O15); ESP32-PICO-V3 fallback |
| PA heat on the bench and when disarmed after leaving pit (stock ELRS biases the PA) | pit on boot, ELRS patches as release gates (O6), README bench-fan rule until merged |

---

## 16. Sources (load-bearing claims)

| Claim | Source | Status |
|---|---|---|
| Matrix II size, holes, thickness, weight, 3-point mount, crash test, pad set, Wi-Fi chip antenna | BetaFPV product page and JSON; photo measurements (01 §2-§3.5, 00) | V |
| Matrix II ESC: 4x EFM8BB51, 12x AGM210MAP, Bluejay A_X_5_96, "12 A / 18 A" | photos + product JSON + Bluejay source (01 §3.2, 03 §2) | V |
| CSD25402Q3A / CSD25404Q3 pinout (source on the EP and pins 5-8, drain pins 1-3), RθJC 2.3 / 1.3 K/W, Qg, RG, Vth limits; CSD13202Q2 pinout and RθJC 6.4 K/W | TI SLPS454B, CSD25404Q3 and SLPS313A datasheets (local copies, track 03) | V |
| Two FETs in series, P+N conduction model, Rds fits | AGM210MAP VER2.72, TI datasheets; model `work/esc03/loss.py` re-run as `calc/thermal.py` with damping, copper and max-Rds terms | V (inputs) / I (model) |
| Convection h 30-80 W/m²K (0.042-0.11 W/K) | 03 verification #15; 06 §4 | I |
| EFM8BB51 VDD 1.8-5.5 V, GPIO VOH, 50 mA per pin abs max, G grade TA 85 / TJ 105 °C, I grade 125 °C | EFM8BB51 data sheet Rev 1.0, Tables 2.1, 4.1, 4.2, 4.18 | V |
| EFM8BB51F16I-C-QFN20R stock | Digi-Key product page, 2026-10-07 | S |
| SE5004L 5.15-5.85 GHz, VCC3 3.0-5.5 V (6 V abs), VREF 2.8-2.9 V at IEN 10 mA, IQC 300 mA, TCASE ≤ 85 °C, gain 30/32 dB, P1dB 30/34 dBm, detector accuracy to 5.85 GHz | Skyworks SE5004L datasheet 202393B; six-PA shared footprint from the QPA9501, TQP5525, GWQ5929A, RFPA5542, RTC5636H pin tables (04 §3) | V |
| RTC6705 Fc 5725-5865 MHz, −40..85 °C, register 0x07 pre-driver power-down | RichWave RTC6705 datasheet V0.2 | V |
| W25Q128JV I grade 85 °C, J grade 105 °C (JVPJQ/JVPJM) | Winbond W25Q128JV datasheet ordering table | V |
| RP2350 ambient −40..85 °C, HBM 2 kV, FT pads | RP2350 datasheet §14.9 | V |
| TPS61022 limits: L 0.33-2.9 µH effective, Cin ≥ 4.7 µF, Cout ≥ 20 µF above 1.5 A, valley limit 6.5/8/10 A, MODE threshold, UVLO, −30 % L sizing, ≤ 40 % ripple guidance, ΨJB 36.7 K/W, pass-through | TI SLVSDX7D §6.3-6.5, §7.3, §8.2.2.2 | V |
| PMEG2010AEH VF and Tj | Nexperia PMEG2010AEH datasheet | V |
| BC847QASZ stock | LCSC C549491, 2026-10-07 | V |
| ELRS: VTX SPI excluded on ESP32-C3; interpolation without `break`; index 1 keeps VREF on; `POWER_AMP_OFF` unused; YOLO setpoint 2250; 10 kHz PWM; 48-channel table incl. L band; 5 s MSP-VTX timeout | ExpressLRS `rx_main.cpp`, `devVTXSPI.cpp`, `devMSPVTX.cpp`, `freqTable.h` (master, fetched 2026-10-06/07) | V |
| Betaflight: `vtx_low_power_disarm` sends index 1; PICO bidir DShot 5-8 % decode errors spinning; `USE_MULTICORE` off; OSD pin slew only | `io/vtx_msp.c`, `dshot_bidir_pico.c`, `target_RP2350.h`, `dma_pico.c`, `osd_pico.c` (2026.6.2 / master) | V |
| Bluejay layout A pin map, DT steps 20.4 ns, stock DEADTIMES list | `src/Layouts/BB51/A.inc`, `src/Bluejay.asm`, `Makefile` (clone 0368d11) | V |
| ELRS whoop RX+VTX layout pins | ExpressLRS/targets `RX/Generic 2400 Whoop Rx and VTx.json` (clone 42ed776) | V |
| Betaflight RP2350: flash, VTX, passthrough only from 2026.6.2; RTC6705 driver and SPI ELRS undefined; FB OSD consecutive pins | Betaflight tags 2026.6.1/2026.6.2/master target headers, `osd_pico.c` (05, 04 verification) | V |
| PIO instruction budget | `osd_tx.pio.h`, `dshot_pio_programs.h`, UART programs (04 verification #13) | V |
| tinyPEPPER direct gate drive, no gate resistor | `single_esc.sch` (08 verification) | V |
| RTC6705 package and zero authorised stock | RichWave datasheet; LCSC, HQ Online, hqchip, ickey, Digi-Key searches; findchips (04 §2) | V / S (brokers) |
| Walsin BPF rejection figures | Walsin PI_RFBPF1608060K98Q1C V01 (04 verification #19) | V |
| NextPCB capabilities, fine pitch 0.38 mm, turnkey channels and prices | nextpcb.com capability pages, stackup DB, instant-quote endpoint (07 verification) | V |
| JLCPCB capabilities | https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-07 | V |
| Stock figures | LCSC product API (`wmsc.lcsc.com/ftps/wm/product/detail`), 2026-10-07; Digi-Key 2026-10-07 where marked; TI store / Digi-Key from track 03 (2026-10-06); HQ Online from tracks 04/06/07 | V (LCSC) / S (others) |
| Motor currents 9-12 A on fresh HV packs | BetaFPV and Happymodel load tables (02 §4) | V / I (scaling) |
| BT2.0 9 A / 15 A | betafpv.com BT2.0 page (06 verification #12) | V |
| House IMU risk ranking | OpenFC-Lite-Mini `hardware/research/imu-selection/README.md` (05 verification #11) | S |
| OpenDrone sheet reuse and the SX1281 pin-5 defect | sibling netlists via kicad-cli 10 (09 verification #10) | V |
| Area and outline numbers | scratchpad `spec/outline.py`, `spec/budget.py` v2 (v1 kept as `budget_v1_2026-10-07.py`) | I |
