# Design spec (proposal, P0)

**Status: proposal for a board that has not been designed. P0 is open on one
gate: area (§9).** Nothing below exists as a schematic or a layout. This file
fixes the targets and the part choices for phase P0 of
[BUILD-PLAN.md](BUILD-PLAN.md). Every other P0 criterion has a primary part, a
calculation and a named bench gate; the area budget does not reach the 85 %
gate on any configuration that keeps the Matrix feature set (best 95.7 % top /
97.8 % bottom, §9.2), and the same method puts the Matrix II itself at about
88-96 %. Per orchestrator decision D12 (5), the P2 placement probe (real
footprints and keepouts, script-checked 0.2 mm rule) is the area proof; the
owner decides the scope levers of §9.3 only if that probe fails. Every number
here is a target, a datasheet value or a calculation, and each one says which.

Date 2026-10-07, revised the same day after review rounds 1 and 2 (electrical,
RF and firmware, manufacturing and lineup) and decision D12. Inputs: the owner
direction and owner rules (2026-10-06), [DECISIONS.md](DECISIONS.md), the
research tracks 00-09 (Matrix photo analysis, Matrix deep dive, landscape, ESC,
VTX/OSD, FC/RX/firmware, power/connectors/mechanics, NextPCB DFM, prior art,
OpenDrone reuse map) with their verification logs, the JLCPCB capability page
(read 2026-10-07), live LCSC and Digi-Key stock and temperature ratings
(2026-10-07) and [LINEUP-CONVENTIONS.md](LINEUP-CONVENTIONS.md). The competitor
material is in [COMPETITION.md](COMPETITION.md); the FC, RX and ESC pin plans
are in [PINMAP.md](PINMAP.md).

Status tags used below: **V** read from a primary source, **S** screened
(secondary source, distributor index, research track not re-derived), **I**
inferred (calculation or engineering judgement). Loss and thermal numbers come
from `calc/thermal_v2.py`, area numbers from `spec/budget_v3.py`, the key-package
floorplan from `spec/sketch_v3.py` (all scratchpad; earlier versions kept).

---

## 1. Scope and targets

Scope is fixed by the owner decision of 2026-10-06: **1S only, match the BetaFPV
Matrix 1S 5IN1 II** in envelope and features, beat it on measured and documented
ratings, blackbox, repairability and open documentation, not by adding scope.

| Item | Target (proposal) | Basis |
|---|---|---|
| Input | 1S LiPo / LiHV, 3.0-4.35 V operating; electronics regulate down to 2.5 V cell under sag (the VTX PA is rated from 3.0 V only); 2S not supported ("1S" silk at the battery pads) | owner decision; TPS61022 runs to 0.5 V once started, starts at 1.8 V (V, TI SLVSDX7D); SE5004L VCC 3.0-5.5 V (V) |
| Board body | 26.4 x 26.4 mm square (Matrix II: 26.35 mm, photo-measured) | V (01) |
| Orientation | Diamond mount like the Matrix: flight-forward points at a body corner. Front corner rounded with R 5.8 mm and carries no ear | V (01, photo); I (radius) |
| Ears and holes | 3 ears (left, right, rear corners), ring OD 4.8 mm. Holes **Ø 3.5 mm** on a **25.75 x 25.75 mm square**, non-plated cut-outs in P1; plated holes with a GND annulus are decided at P2 with the ball fit (O2, O16) | Matrix II holes Ø 3.48-3.57 on 26.0 mm, plated (V, 01). 25.75 mm halves the worst offset in 25.5 and 26.0 mm frames to 0.18 mm radial (I, from 06 §3.3) |
| Overall size | 30.55 x 30.55 mm including ears (Matrix II 30.9 mm); outline area 696.6 mm² net of holes | I (outline script, §9) |
| Mounting | 3-point soft mount with BetaFPV-type shock balls; 1.0 mm board matches the Matrix ball groove | V (01, 06 §3.3) |
| Thickness | 1.0 mm finished, 6 copper layers | §8 |
| Weight | **≤ 3.5 g** bare (solder-pad build, no battery pigtail, no antenna). Estimate 2.9-3.2 g (§6). Matrix II solder-required: 3.76 g | I (§6); V (Matrix, 01) |
| ESC | 4 channels, Bluejay on EFM8BB51 (I grade), P+N direct drive, bidirectional DShot, EDT. Stage per D12: TI CSD25310Q2 (P, 2x2) + CSD13202Q2 (N, 2x2) per phase, hot path 40.2 mΩ typ (Matrix AGM210MAP 34.1 mΩ) | §4.3, §4.4 |
| ESC rating to publish | **Measured only, by protocol V4 (§14)**: continuous A per channel (one channel loaded, others 2 A) and on all four, with the stated airflow, 25 °C ambient, VTX 25 mW, every part inside its own rating; burst duration at 12 A and 18 A from the measured hover steady state. No number above the model is claimed. Model (§4.3, PA-case term included): at h 80 W/m²K about 5 A on one channel and 3 A on all four; at h 55, 0-1.6 A and 1.3-1.9 A; at h 30 the board is out of rating at hover. With the heat levers of §5.4, 4.7 A / 2.9 A at h 55. Bursts: 12 A for 1.3-4.9 s, 18 A for under 1 s (model). The Matrix stage on the same model: 5.8 A / 3.3-3.8 A at h 80, 12 A for 3.3-7.4 s. The D12 stage is **not** better than the Matrix's; what the board offers is a published protocol, the same rig on a Matrix II, and the numbers | §4.3, §5.4 |
| VTX | RTC6705 + Skyworks SE5004L PA on the cell, U.FL. **Levels as ELRS pushes them** (five, fixed in `freqTable.h`, V): `0` (PA biased at minimum drive, not pit), `RCE` (pit at boot, then the 25 mW arrays), `25`, `100`, `400`. 25 and 100 mW are closed loop on the PA detector; `400` is open-loop full drive (ELRS YOLO setpoint) behind a hardware fault limit (§4.8) and is published as "max (measured)" per board until the closed-loop 400 mW patch exists (O6 gate 2). **Channels:** ELRS pushes 48; the patched firmware refuses the L band (5362-5621 MHz, below the RTC6705 VCO) and holds pit (O6 gate 5); the 40 channels from 5645 to 5945 MHz are supported, the 24 inside both datasheet bands (RTC6705 5725-5865, SE5004L 5150-5850 MHz) are rated, the other 16 published as measured. 400 mW is continuous only at high airflow (PA case ≤ 85 °C needs h ≥ 56-70 W/m²K at hover, §4.3) | §4.8 |
| OSD | Betaflight PIO framebuffer OSD on the RP2354A (no OSD chip). It overlays on the camera's sync and generates none: no camera, no OSD (the Matrix's AT7456E free-runs) | §4.5, §4.8 |
| RX | Serial ExpressLRS 2.4 GHz, ESP32-D0WD-V3 + SX1280, +13 dBm, no PA/LNA (Matrix parity), insulated wire monopole trimmed to resonance; Wi-Fi for ELRS updates through a minimal radiator (Matrix has a Wi-Fi chip antenna) | §4.7 |
| FC | RP2354A, Betaflight ≥ 2026.6.2, one gyro per revision published in the target (no lottery) | §4.5, §4.6 |
| Blackbox | 16 MB SPI NOR (W25Q128JVPIM), SPI0 | §4.9 |
| 5 V BEC | 5.15 V nominal (4.93-5.37 V worst case); calculated nominal peak 1.83 A at 2.8 V and 1.96 A at 3.0 V in (TI method, −30 % inductance, 0.68 µH); claim capped at 1.5 A and published per input voltage and board temperature from V1 (TPS61022 TJ ≤ 125 °C). Design load 0.70 A | §4.2, §5.3 |
| Current / voltage sense | 0.5 mΩ shunt (Kelvin land) + INA186A3 (50 mV/A, `ibata_scale` 500), VBAT 1:1 divider; scales measured and set in the target | §4.1 |
| Connectors | BT2.0 pigtail on two plated holes (user-fitted); 12 motor solder pads with plated wire-anchor holes; SH1.0 4-pin vertical USB (BetaFPV adapter style, bottom); SH1.0 3-pin vertical camera plug (top) plus CAM/5V/GND pads; U.FL for the VTX; RX antenna wire hole; one free UART on pads (TX1/RX1, as the Matrix II) | §4.10 |
| Fab / assembly | NextPCB turnkey (partial turnkey with consigned lines), DFM-compatible with JLCPCB except silk legibility (0.8 mm labels, D12); through vias only, OpenDrone 0.35/0.20 via (D6) | §8, §15 |

---

## 2. What to optimise, ranked

| Rank | Goal | Metric | Target | Bench measurement |
|---|---|---|---|---|
| 1 | Electronics rail that survives sag (no FC/RX brown-out; video to 3.0 V, the PA minimum) | +5V at full design load (0.70 A, and 1.25 A with the PA moved to 5 V) while the input is swept 4.35 → 2.6 V | ≥ 4.85 V at VIN ≥ 2.8 V (setpoint 5.15 V, worst-case low corner 4.93 V); ripple ≤ 50 mV p-p (forced PWM, 1 MHz); no reset of FC or RX down to VIN 2.5 V | bench supply + electronic load, scope at the camera pad |
| 2 | Honest ESC rating, measured on the same rig as a Matrix II | continuous A per channel with every part inside its rating, measured at the part (hottest FET ≤ 100 °C, EFM8 ≤ 125 °C, RTC6705 case ≤ 80 °C, RP2354A, gyro, SX1280, NOR, RX flash and SE5004L case ≤ 85 °C, X6S caps in the cells ≤ 105 °C) under V4; burst durations | published as measured with the airflow stated; no claim above the model (§1). Cost of D12 against the Matrix stage: path 40.2 mΩ typ (48.8 max) vs 34.1 (50.0 max); model −0.9 A continuous and about half the 12 A burst time at the same airflow | thermocouples per V4; same rig on a Matrix II |
| 3 | Weight | grams on a 0.01 g scale | ≤ 3.5 g bare (Matrix 3.76 g) | scale, first 5 prototypes |
| 4 | Measured VTX power and clean spectrum | output per channel at 25/100/max at 3.7 V; 2nd harmonic | 25 and 100 mW within ±3 dB unit to unit at 5850 MHz (±1.5 dB typical on the calibrated sample; ±1.5 dB unit to unit only with per-unit calibration, O6); at 5650/5750/5945 MHz ±3 dB on the sample after the ELRS interpolation fix; full per-channel table and the unit spread published; 2f ≤ −30 dBm (EN 300 440 limit) | calibrated power sensor + 30 dB attenuator; spectrum analyser to ≥ 18 GHz; ≥ 5 boards |
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
| FC | STM32G473 + AT7456E OSD | STM32G473CEU6 + AT7456E | RP2354A + PIO OSD (needs camera sync) |
| Gyro | 6-part lottery | BMI270, own supply | one part per revision (BMI270 or ICM-42688-P after fly-off) |
| ESC | 4x BB51, 12x AGM210MAP P+N (34 mΩ), "12 A cont / 18 A peak" | 4x BB51, 12x SiA517DJ, 5 A design target | 4x BB51, 12x CSD25310Q2 (P) + 12x CSD13202Q2 (N), 40 mΩ: a weaker stage than the Matrix's, rated by measurement only (V4) |
| RX | ESP8285 + SX1281 onboard | external | ESP32 + SX1280 onboard, ELRS 4.x mainline |
| VTX | RTC6705 + RFPA5542 (EOL) + MM32F003, 25-400 mW | RTC6705 + RTC6659-class PA, 25/100/250/MAX | RTC6705 + SE5004L, no VTX MCU (ELRS drives it), 0/RCE/25/100/max (400 closed loop after O6) |
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
OpenDrone board are marked **[PU]** (PARTS-USED.md). BOM symbols of parts with
no LCSC listing carry `LCSC = none (<distributor> <PN>)`, which the LINEUP A9
checker accepts as a filled field.

**Temperature grades** (V, LCSC/maker listings 2026-10-07, unless marked).
The board limit is set by the 85 °C parts at board temperature:

| Grade | Parts |
|---|---|
| 85 °C (bind the board) | RP2354A (ambient), BMI270, SX1280, W25Q128JVPIM, GD25Q32EEIGR (I grade, −40..85), SE5004L (case), RTC6705 (Tj −40..85, so case ≤ about 80 °C), YXC 12 MHz crystal and Yajingxin 8 MHz crystal (−40..85), YXC 52 MHz TCXO (−30..85), JSCJ 40 MHz crystal (range not listed: P3 reads the datasheet, swap if below 85), Walsin BPF and TDK LPF (−40..85), JST SH1.0 connectors (−25..85), XINGLIGHT LEDs (−40..85; RGB −20..85), X5R capacitors (only outside the ESC quarters and away from the PA) |
| 90 °C | Hirose U.FL |
| ≥ 105 °C | X6S capacitors in every ESC quarter and at the PA (Murata GRM033C81E104KE14D, GRM033C81A105ME05D, GRM188C80J226ME15D, GRM155C80J106ME11D; −55..105 °C, V maker data via distributors); ESP32-D0WD-V3 (LCSC lists −40..125, P3 confirms on the datasheet); EFM8BB51 I grade, TPS61022 and the LDOs (TJ 125); SN74LVC1G3157, TLV7031, INA186 (125); FETs, BC847QAS, diodes (150); resistors, NTC, ferrite (125-155) |

The TOGNJING 12 MHz crystal of the house FC sheet is rated −20..70 °C (V,
LCSC C37635340) and is replaced (§4.5).

### 4.1 Input and protection

| Option considered | Verdict |
|---|---|
| Reverse-polarity FET | **No.** The BT2.0 key protects the plug, not the user-fitted pigtail joint: a pigtail soldered reversed puts about −4 V on +BATT through the TVS, the 12 body-diode pairs, the INA186 and the TPS61022, which loses the board. An ideal-diode P-FET (1-2 mΩ, 3x3) costs about 12 mm² and 0.4-0.6 W at 20 A. Rev1 keeps user fit (Matrix-style pads) and states the risk: + and − silk at the pads and a polarity photo in the README. Factory fitting on NextPCB's THT line is priced as a P7 option |
| TVS at the pads | **Yes, for the FET drain-source ratings only.** Event: battery unplugged (or pigtail torn in a crash) while the props spin; Bluejay damping returns rotor energy (up to about 0.3 J per motor at 40,000 rpm, I; up to about 1.2 J for four) into a bus that then holds only the MLCCs. The SMF5.0A (VBR 6.40-7.07 V, VC 9.2 V at 21.7 A, 200 W 10/1000 µs, V) absorbs about 0.29 J per rated pulse (I), so it covers one motor's worth, not four; the rest goes into winding and body-diode losses (I). V3b measures TVS current, duration and clamp energy; the fallback is the 400 W Littelfuse SMAJ5.0A (SMA, S; +7 mm² bottom). The clamp keeps VDS of the 12 V N and 20 V P parts in rating. It does **not** protect: the FET gates (both CSD25310Q2 and CSD13202Q2 are ±8 V; the EFM8 drives them at VDD = bus, so 9.2 V exceeds them), EFM8 VDD (5.5 V abs max), SE5004L VCC3 (6 V), TPS61022 (7 V; its pass-through carries a surge onto +5V, where TLV755P allows 6.0 V), the 6.3 V MLCCs. A clamp per EFM8 is not possible in this topology (VDD must follow the P sources). Accepted as Matrix parity (same topology); risk in §15.4, surge measured in V3b |
| Bulk at the pads | 2x 22 µF 0603 16 V (X5R, at the battery pads outside the ESC quarters). Board total about 55-80 µF effective at 4.35 V (table below), which shares the PWM ripple with the 30-60 mΩ battery path (03 §11) |

Effective capacitance (I: typical DC-bias behaviour including −20 % tolerance;
replaced by the Murata/Samsung simulator curves in P3):

| Part | Use | At | Effective each |
|---|---|---|---|
| CL10A226MO7JZNC 22 µF 16 V 0603 X5R | pad bulk x2 | 4.35 V | about 9-13 µF |
| GRM188C80J226ME15D 22 µF 6.3 V 0603 X6S | ESC local bulk x4 (one per ESC), boost Cin x1 | 4.35 V | about 7-10 µF |
| GRM188C80J226ME15D | boost Cout x3 | 5.15 V | about 5-7 µF (15-21 µF for three) |
| GRM033C81A105ME05D 1 µF 10 V 0201 X6S | EFM8 VDD x4 | 4.35 V | about 0.4-0.6 µF |

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
`PWR_FLAG`); after the shunt the rail is **`+BATT`**. Everything that draws
current, including the boost VIN and the PA VCC, taps `+BATT` after the shunt,
so the INA186 sees it. Numbers: 0.5 mΩ x 100 V/V = 50 mV/A, full scale 66 A at
3.3 V, Betaflight `ibata_scale` 500 (0.1 mV/A units). Shunt loss 0.2 W at 20 A,
0.31 W at 25 A. VBAT 10k/10k puts 4.35 V at 2.18 V on the ADC. Current sense is
high side with Kelvin taps and the matched input RC network of the OpenESC
Rev3.2 / OpenAIO root sheet (values moved to 0201). The land is a four-pad
Kelvin pattern per the Stackpole HCS application note with the sense taps at the
inner pad edges; the scale is checked on every prototype and on a sample of each
production lot (±10-20 % unit to unit otherwise, I).

### 4.2 Power tree

```
BT2.0 -> +BATT_IN pads -- SMF5.0A, 2x22u -- shunt (Kelvin -> INA186) -- +BATT
  +BATT -> 4x ESC power stages; 4x EFM8 VDD on their own cluster's +BATT (1u + 100n X6S, no series R)
  +BATT -> SE5004L PA VCC (10u X6S + per-pin 1n/100p)   [3-pad 0 ohm selector: +BATT (default) or +5V]
  +BATT -> TPS61022 boost, 1 MHz, 0.68 uH -> +5V (5.15 V, 3x 22u X6S 0603)
             EN: 100k from VIN; AP1606 pulls EN low while +5V_USB is present.  MODE = VOUT: forced PWM
             +5V -> ferrite 0201 + 10u -> CAM 5V (plug + pad)
             +5V -> LED-strip 5V, buzzer +, user 5V pads
             +5V -> TLV75533 (EN = +5V) -> +3V3 (RP2354A, NOR, OSD front end, INA186, LEDs)
                                  +3V3 -> TPS7A2018 (EN = +3V3) -> +1V8 (gyro)
             +5V -> LP5912-3.3 (EN = +5V) -> +3V3_RX (ESP32, SX1280, RGB LED)
                                  +3V3_RX -> LP5907-2.85 (EN = ESP32 GPIO2, 10k pull-down) -> PA VREF
             +5V -> LP5912-3.3 (EN: 100k to +3V3_RX, ESP32 GPIO21 pulls low) -> +3V3_VTX (RTC6705, drive stage)
  +5V_USB (SH1.0 USB) -> PMEG2010AEH Schottky -> +5V   (bench: FC, RX, RTC6705, camera; boost off; PA and ESCs on the battery if fitted)
  RP2354A internal core SMPS -> +1V1 (3.3 uH 2016, per RPi guide)
```

Enables: no EN floats and no EN net is shared between rails (commons
checklist). TPS61022 MODE goes to VOUT, so forced PWM holds over the whole sag
range (VMODE_H 1.2 V valid with VOUT > 2.2 V, V). The TPS61022 passes VIN to
VOUT when VIN > VOUT (V): a bus surge reaches +5V (§4.1).

**USB with or without the battery.** In forced PWM the TPS61022 moves power from
VOUT to VIN when VOUT is above its setpoint ("the inductor current changes its
direction ... the power flow is from output side to input side", V, SLVSDX7D
§7.4.1), and no negative current limit is specified. With USB and a cell both
connected, +5V_USB − VF (up to 5.25 − 0.1-0.2 V at light current) can exceed a
low-corner setpoint (4.93 V), so an enabled boost would charge the cell from the
USB port through the Schottky. With USB only, DShot back-feed lifts +BATT past
the boost UVLO and an enabled boost collapses that weak source repeatedly
(PINMAP F16). Both are removed by holding the boost off while USB is present:
an ALLPOWER **AP1606** N-FET (gate on +5V_USB with a 100 kΩ pull-down,
drain on EN) pulls EN low against a 100 kΩ pull-up from VIN. In shutdown the
TPS61022 disconnects its output (V), so +5V runs from USB alone and the cell
sees only the PA (if enabled) and the EFM8 load. A P-FET ideal diode instead of
the Schottky would not help: it raises +5V towards +5V_USB and makes the
reverse case worse. V1 and V9 test it (+5V_USB at 5.25 V, cell 4.35 V and 3.7 V:
cell current, USB current, diode temperature).

**Setpoint.** TPS61022 VFB is 585/600/615 mV in PWM (±2.5 %, V Table 6.5); with
1 % divider resistors a 5.00 V nominal can sit at 4.80 V, below the rank-1 gate.
The nominal is set to **5.15 V**: worst case 4.93-5.37 V (I), so the 4.85 V gate
holds with the ripple trough, and the maximum stays inside TLV75533 (5.5 V
operating), LP5912 (6.5 V) and the SE5004L on the +5V selector position
(5.5 V).

Options weighed:

| Question | Options | Decision | Why (numbers) |
|---|---|---|---|
| 5 V converter | TPS61023 (SOT-563, 2.7 A valley, auto-PFM), TPS61022 (2x2, 6.5 A valley, forced-PWM pin), TPS63070 buck-boost (2S only), SY7088 (3 A peak) | **TPS61022RWUR + 0.68 µH 2520** | Forced PWM keeps the 1 MHz ripple fixed and out of the PFM range that shows as video bars. Calculated per TI §8.2.2.2 (inductance −30 %, peak at 80 % of Isat 6.5 A): 1.83 A at 2.8 V and 1.96 A at 3.0 V nominal peak, against 0.70 A design load and 1.25 A if the PA moves to 5 V. Ripple is 159 % of the inductor DC current at the design load (230 % with the earlier 0.47 µH; TI asks ≤ 40 % at full load), and the −20 % tolerance part stays above TI's 0.33 µH floor. Above 1.5 A the datasheet needs ≥ 20 µF effective Cout, so the claim stops at 1.5 A. Binding limit: TJ ≤ 125 °C (recommended operating, V §6.3), not the 150 °C shutdown: 1.5 A out from 2.8 V is about 1.3 W of loss, +40-48 K by ΨJB 36.7 K/W, so about 125 °C on an 80 °C board; the published BEC figure is per VIN and board temperature from V1 |
| 3.3 V supply path | 5 V boost + LDOs (as drawn) vs a cell-fed 3.6 V buck-boost (TPS63802 class, S) with post-LDOs | **as drawn**; heat lever (b) in §5.4 | All 3.3 V loads through boost + LDO cost about 0.65 W of overhead for 0.96 W delivered. A 3.6 V buck-boost would save about 0.45 W for 15-20 mm² on the bottom, which the bottom does not have (§9) |
| PA supply | 5 V boost + load switch (track 06 R6) vs cell (track 04) | **Cell (+BATT)**, 3-pad 0 Ω selector to +5V | SE5004L is rated 3.0-5.5 V; takes 0.3-0.55 A off the boost; VREF low = 0.5 µA so no load switch; on USB only the PA has no supply. The selector is a 3-pad land with one 0402 0 Ω fitted between the centre and one side: a solder blob across a 3-pad solder jumper would short the boost output to the cell, a single 0402 cannot bridge both sides. Below 3.0 V cell the PA is out of rating (V5 measures at 2.8 V). Bench test V5 decides (§14) |
| USB OR | two Schottkys into an LDO bus (OpenFC pattern) vs one Schottky +5V_USB → +5V with the boost held off on USB | **One Schottky + boost EN held low on USB** | the boost cannot back-feed the cell (above); saves a diode drop on the main path |
| 3.3 V rails | one LDO for all (about 0.29 A: 0.49 W, +82 K in X2SON) vs split | **Split into 3 + gyro LDO + PA reference** | Each LDO ≤ 0.19 W; the RTC6705 VCO gets its own low-noise rail; RX Wi-Fi bursts (up to 0.3 A, Wi-Fi mode only) go to a WSON-6 part |
| ESC MCU supply | VBAT direct vs 3.3/5 V rail | **VBAT direct**, each EFM8 on its own cluster's +BATT, 1 µF + 100 nF X6S, no series R | EFM8BB51 VDD 1.8-5.5 V (V); gate drive = cell voltage; motors survive a BEC fault. A series R (10 Ω x 1.1 µF) would leave most of the PWM ripple between P source and P gate; tied directly, VDD tracks the P sources (track 03 §8: at most 2.2-4.7 Ω). VDD peak and logic-high margin: §4.4 |
| USB ESD | 2-line ESD array at the SH1.0 vs none | **None** | House boards ship USB without an array; RP2350 pads are HBM 2 kV (V, §14.9.2) behind 27 Ω series resistors. Risk recorded (§15.4) |

On USB only: the bench loads are FC 0.09 A, RX 0.10 A (0.3 A in ELRS Wi-Fi mode),
RTC6705 0.10 A and the camera 0.12 A at 5 V. At 0.4 A the PMEG2010AEH drops about
0.23 V (V: 0.25 V typ at 0.5 A) and dissipates about 0.09 W (Tj 150 °C). With the
battery fitted as well, +5V still runs from USB (boost off): a PC port then
carries the +5V loads; the PA and the motors run from the cell. The OSD needs a
camera on the bench (§4.5). Bidirectional DShot idles high on USB and back-feeds
the unpowered EFM8s and +BATT through the 2.4 kΩ resistors; PINMAP §4.5
documents that case and V9 tests it.

Parts:

| Function | Primary (MPN, maker, package, stock) | Fallback | Reuse |
|---|---|---|---|
| Boost | TI **TPS61022RWUR**, VQFN-HR-7 2x2, C915088, 857 | TI TPS61023DRLR, SOT-563, C919459, 53,320 (new land, 1.6 A at 2.8 V) | new |
| Boost inductor | cjiang **FTC252012SR68MBCA**, 0.68 µH, 2.5x2.0x1.2, Isat 6.5 A, 17 mΩ, C5832369, 6,040 (V, LCSC parameters) | cjiang FTC252012S1R0MBCA, 1.0 µH, Isat 5.6 A, 35 mΩ, C5832370, 282,340 | new |
| Boost caps | Cin 1x, Cout 3x Murata **GRM188C80J226ME15D** 22 µF 6.3 V X6S 0603, C393031, 104,510 (the boost sits in the ESC1/ESC2 quarter, §10) | a 10 V X6S/X7R 22 µF 0603 found in P3 (better DC bias) | new |
| +5V_USB sense FET | ALLPOWER **AP1606**, DFN-3L 1.0x0.6, 20 V, C2849580, 2,000 [PU] | Nexperia PMZ250UN class (S), land check in P3 | OpenFC LED stage part |
| +3V3 LDO (FC) | TI **TLV75533PDQNR**, X2SON-4 1x1, C2861882, 2,025 [PU] | TI LP5912-3.3DRVR, WSON-6 2x2, C524780, 23,490 [PU] | OpenRX-Lite part |
| +3V3_RX LDO | TI **LP5912-3.3DRVR**, WSON-6 2x2, C524780, 23,490 [PU] | TLV75533PDQNR [PU] | OpenFC `power` back end |
| +3V3_VTX LDO | TI **LP5912-3.3DRVR** (D12: the part already on the BOM) | TI TPS7A2033PDQNR, X2SON-4 1x1 (commons-verified), once a NextPCB channel shows stock (−3.8 mm²) | BOM reuse |
| PA VREF reference | TI **LP5907SNX-2.85/NOPB**, X2SON-4 1x1, 2.85 V ±2 % (S, maker listing via Arrow) | a 2.8 V variant if V5 qualifies a lower VREF (lever (a), §5.4) | new |
| +1V8 gyro LDO | TI **TPS7A2018PDQNRM3**, X2SON-4 1x1, C36996449, 8,090 | TI LP5912-1.8DRVR, WSON-6 2x2, C2876234, 728 [PU] | OpenFC `imu` rule |
| USB OR diode | Nexperia **PMEG2010AEH**, 1 A 20 V, SOD-123F, C110921, 25,360 (V: VF 0.25 V typ at 0.5 A) | ROHM RB161QS-40T18R, SMD1006, C2837790 (−4 mm², 0.6 V at 1 A) | new |
| RP2354A core inductor | Abracon **AOTA-B201610S3R3-101-T**, 3.3 µH 2016, C42411119, 625 [PU] | external 1.1 V LDO with the SMPS bypassed (RPi guide option) | OpenFC `rp2350a` |
| Camera ferrite | Murata **BLM03PX121SN1D**, 0201, 0.9 A, 160 mΩ, −55..125 °C (S: Digi-Key/Element14 listings; TME 5,024 on 2026-10-07) | Murata BLM03PX220SN1D, 0201, 1.45 A (S) | commons |

### 4.3 ESC power stage

| Topology | Area (budget v3, 12 phases, both sides incl. cell vias) | Hot path at Vgs 3.6 V, typ (max) | Verdict |
|---|---|---|---|
| **Discrete P 2x2 + N 2x2 (CSD25310Q2 + CSD13202Q2), direct GPIO** | 12 + 12 SON 2x2 + 7 / 15 vias per phase (top / bottom) | **40.2 (48.8) mΩ** | **chosen (D12)** |
| P+N dual per phase, direct GPIO (Matrix: AGM210MAP) | 12 PDFN 3.3x3.3 + 7 source vias per phase both sides; board total within 1 % of D12 (§9.2 case b) | 34.1 (50.0) mΩ | case (b), O5: Matrix-proven at `A_X_5_96`, longer bursts; LCSC-only (4,795), so a consigned line |
| Discrete P 3.3x3.3 + N 2x2 (CSD25402Q3A + CSD13202Q2) | +106 mm² top, −26 mm² bottom against D12 | 23.1 (27.9) mΩ | round-1 choice; fails the area by more (top 112 %) |
| N+N + gate driver | +4-15 mm²/channel + boost rail | 11 mΩ (needs EG2134, 0 stock) / 22-30 mΩ (DRV8328) | no: no stocked 1S driver gains anything, adds a rail whose failure drops all four motors (03 §5c) |
| Level-shifted P (2S style) | +46 mm² | worse, DT 0.6-1.4 µs | no: 1S only |

Decision (D12): per phase one TI **CSD25310Q2** P-FET on the top (high side,
gate straight from the EFM8 COM pin, active low) and one TI **CSD13202Q2** N-FET
on the bottom (low side, PWM pin, active high). Bluejay BB51 layout A, unchanged
upstream (§12). D12 took it over the AGM210MAP for sourcing (genuine TI parts,
TI store stock) and because the continuous rating is set mostly by non-ESC heat;
the model shows the cost is real: about −0.9 A continuous against the Matrix
stage at the same airflow and about half its 12 A burst time (§1, table below).

**Cell from the real lands** (V, SLPS459C §4.2 figure: CSD25310Q2 drain on the
exposed pad, source on a pin and strip, gate pin; SLPS313A: CSD13202Q2 drain on
the centre pad and pins 1, 2, 5, 6, gate pin 3, source pin 4 plus a strip).
Per phase:

- the P drain pad is the phase node and carries the 8-via phase field in-pad
  (0.35/0.20, Type VII);
- the N sits on the bottom **beside** the P, offset outward under the
  motor-pad strip (no exposed pad over an exposed pad, §11); the phase vias land
  in a bottom phase pour that joins the N drain pad;
- the N source GND vias (3) and the P source +BATT vias (4) sit beside the
  lands; through vias occupy both sides: 7 via sites on the top, 15 on the
  bottom per phase (budget v3);
- the leg cap (100 nF X6S 0201) sits on the bottom between the N source and the
  P-source +BATT vias;
- the motor pad route leaves on L1 and L6, joined by the plated wire-anchor
  holes.

Commutation loop: P source strip → P die → drain pad → phase vias → N → N source
→ leg cap → +BATT via → P source: about 2.4 mm across through 1 mm of board,
target ≤ 4 mm², drawn with dimensions at P2 (BUILD-PLAN P2 deliverable).

| Part | Primary | Fallback |
|---|---|---|
| P-FET | TI **CSD25310Q2**, −20 V / ±8 V, 19.9 / 27.0 mΩ typ (23.9 / 32.5 max) at 4.5 / 2.5 V, Qg 3.6 nC typ / 4.7 max, Vth −0.55 / −0.85 / −1.10 V, RθJC 4.5 K/W (V, SLPS459C), SON 2x2; TI store 67,679 (track 03, 2026-10-06), LCSC C2871649 (250-pc reel) 696 | case (b) AGM210MAP dual (Matrix stage, different cell), O5 |
| N-FET | TI **CSD13202Q2**, 12 V / ±8 V, 7.5 / 9.1 mΩ typ (9.3 / 11.6 max) at 4.5 / 2.5 V, SON-6 2x2, RθJC 6.4 K/W, LCSC C187839 2,605; Digi-Key 8,235, TI store 294,349 (track 03) | AOS AON2408, 20 V, DFN 2x2 (S, LCSC index 3,512); land check in P3; about +25 % N loss |
| Leg cap | Murata **GRM033C81E104KE14D** 100 nF 25 V X6S 0201 (V via Farnell/Arrow listings), one per half-bridge | Murata GRM033C71E104KE14 class X7S (P3) |
| Local bulk | Murata **GRM188C80J226ME15D** 22 µF 6.3 V X6S 0603, C393031, 104,510, one per ESC (replaces 2x 0402 X5R: same area, more effective capacitance, 105 °C) | Samsung X6S 0603 equivalent (P3) |

**Loss math** (I, `calc/thermal_v2.py`). Layout A conducts through **two FETs in
series** at every instant: the high-side P of the driven phase plus either the
PWM'd low-side N or, in the damped off-time, the damping P. Conduction is
I²·(d·(Rp + Rn) + (1 − d)·2Rp), evaluated at d 0.8. Rds values are typical, hot
(x1.35) at Vgs 3.6 V (Rp 29.5, Rn 10.7 mΩ for D12); the max column uses the
datasheet maxima. Dead time adds 2·DT·f·0.8 V·I through body diodes for the start
build `A_X_10_96` (DT 204 ns at 96 kHz). Hard switching is on the N only. Phase
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
above the quarter is about 5-15 K/W (I, 06 §4.3 scaled to the 1/0.5 oz stack).

**Dead time, worst case** (I, datasheet limits). P turn-off is diode-commutated,
so it is an RC with no Miller plateau: t = τ·ln(VDD/|Vth|). Typical (30 Ω + 1.9 Ω,
Qg 3.6 nC / 4.5 V, |Vth| 0.85 V): 42 ns. Worst case (EFM8 high-drive VOH ≥ VDD −
0.6 V at 10 mA, so ≤ 60 Ω; RG max taken as 2x typ = 3.8 Ω, I; Qg 4.7 nC max, V;
|Vth| 0.55 V min at 25 °C and about 0.39 V hot, I): **138 ns cold, 161 ns hot** at
4.35 V. Hence the start build **`A_X_10_96`** (204 ns); `A_X_5_96` (102 ns, the
Matrix build) only after the extended V2 (§14). This assumes the EFM8 ports run
at high drive strength: Bluejay never writes PRTDRV (V, grep of `src/` at
0368d11), so the reset default applies. The EFM8BB51 reference manual could not
be fetched (Silicon Labs returned 403 on 2026-10-07); the Matrix shipping
`A_X_5_96` with a P-FET that models at 75-137 ns at high drive implies high drive
is the default (at low drive, about 200 Ω from VOH at 3 mA, it would shoot
through at DT 5) (I). P3 cites the PRTDRV reset value; if it is low drive, the
CSD25310Q2 worst case becomes about 0.5 µs (DT 25) and it is raised as a Bluejay
layout issue before V2. V2 records the drive mode.

**Thermal estimate** (I, `calc/thermal_v2.py`, track 03 §7 board model). One
motor quarter has about 0.65 J/K and 0.055 W/K lateral spreading; the whole board
sheds **0.042-0.11 W/K** (h 30-80 W/m²K over 13.9 cm², track 03 verification
#15; track 06 §4 gives 30-60 in flight). A whoop FC sits under a canopy above the
battery tray, not in the duct flow, so the low end is plausible; V8 measures h on
a board in a real frame. Limits, at 25 °C ambient: board rise ≤ 60 K for the
85 °C parts; PA case = board + k_PA·P_PA ≤ 85 °C with k_PA 6-12 K/W (I: the
spec's 10-20 K at 1.64 W; V8 measures it); RTC6705 = board + 15 K/W x 0.33 W
(I) ≤ 85 °C Tj; the loaded quarter = board + P_motor / 0.055 W/K ≤ 75 K (FET
100 °C; X6S caps in the cell are rated 105 °C, so the FET binds). Trunk = 0.5 mΩ
shunt + 0.7 mΩ supply copper + 0.5 mΩ GND return through L2/L5 and the pours at
the pack current.

| Case (25 °C ambient, VTX 25 mW unless stated; ranges are k_PA 6-12 K/W) | Heat | Board rise at 0.042-0.11 W/K | Local terms | Needed for every part in rating |
|---|---|---|---|---|
| Hover, 1 A per motor | 3.4 W | +31-81 K | PA +7-13 K | h ≥ 46-52 W/m²K |
| Hover, VTX 400 mW | 4.0 W | +36-95 K | PA +10-20 K | h ≥ 56-70 |
| 4 A one channel, others 2 A | 4.9 W | +44-116 K | quarter +17 K | h ≥ 65-74 |
| 6 A one channel, others 2 A | 5.9 W | +53-142 K | quarter +35 K | h ≥ 107 (outside the verified range) |
| 3 A on all four | 5.4 W | +48-128 K | quarter +10 K | h ≥ 72-82 |
| Rating at h 55 / h 80 | | | | one channel 0-1.6 A / 4.7-5.1 A; all four 1.3-1.9 A / 2.9-3.4 A; at 400 mW 0 A / 1.0-4.4 A one channel |
| 12 A burst, one motor, from the modelled hover steady state (69 °C at h 55, 56 °C at h 80) | 6.7 W | first order, τ 11.8 s | P-FET local +13-28 K | 1.3-3.0 s (h 55), 3.0-4.9 s (h 80) to FET 110 °C: **measured in V4** |
| 18 A, Vgs 3.0 V | 15.9 W | | P-FET local +33-68 K | under 1 s: **measured in V4** |

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

Per channel: VDD straight to its own cluster's +BATT copper (no series R), 1 µF
(Murata GRM033C81A105ME05D, X6S) + 100 nF (GRM033C81E104KE14D, X6S) at the pin,
returned to the ESC's GND. The off-state P-gate level then tracks the P sources;
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
at the pin under chops and braking on a fresh 4.35 V pack (pass ≤ 5.3 V including
spikes) and V9 counts ESC-side DShot errors at 4.35 V under load. Fallbacks, in
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
| 12 MHz crystal | YXC **X252012MMB4SI-24**, 2520, 10 pF, ±10 ppm, −40..85 °C, C2896601, 18,710 (V; HQ Online listing, S) | KYX K2C120001210, 2520, 12 pF, −40..85 °C, C2835952, 2,675 (V). Not the house TOGNJING part (−20..70 °C) |
| Status LEDs | XINGLIGHT **XL-1005UGC** green (C965793) and **XL-1005UBC** blue (C22355736), 0402, sinking into GPIO7/26 from +3V3 [PU] | none verified. Kept at 0402 for the house colours and parts (OpenFC-Lite-Mini LED0 green, LED1 blue). Red/orange 0201 AlInGaP parts (Vf about 2 V) would work at 3.3 V sink drive and save 1.2 mm²: a P2 lever, not required |

`rp2350a` sheet reuse, changes: remove USB-C, CC and I2C pull-ups; USB D+/D−
(27-30 Ω series) to the SH1.0 connector; VBAT divider 100k/10k → 10k/10k;
crystal swapped (above); GPIO map below; SWD to pads; boot button replaced by an
FCB pad (QSPI_SS) next to a GND pad.

**FC pin map (RP2354A, QFN-60; detail in PINMAP §2)**

| GPIO | Function | Peripheral |
|---|---|---|
| 0 / 1 | CRSF to ESP32 (ELRS RX; also serial passthrough) | UART0 TX/RX |
| 2 / 3 | spare, no-connect (Matrix II exposes one user UART) | - |
| 4 / 5 | user UART pads TX1 / RX1 | UART1 TX/RX |
| 6 | gyro pin 9 (CLKIN for TDK; INT2 on BMI270, unused) | PWM slice 3A (32 kHz CLKIN) |
| 7 | LED0 green (status) | GPIO |
| 8 | LED strip, through a non-inverting translator (PINMAP F1) | PIO1 (WS2812) |
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
`PIO_LEDSTRIP_INDEX 1`. PWM slices: 0B (beeper) and 3A (CLKIN) are the only PWM
users. DMA: 8 of 16 channels (DShot uses none, PINMAP F6).

### 4.6 Gyro

| Candidate | Stock | Note |
|---|---|---|
| **Bosch BMI270** | C2836813, 7,795, $2.66 [PU] | house current part; widely flown on 1S whoops; Betaflight 3.2 kHz ODR; house IMU study rates it "higher risk" for MEMS resonance on the 20x20 sister board; TA 85 °C |
| TDK ICM-42688-P (genuine) | C1850418, 3,029, $19.64 | house study's only "empirically proven" part; 8 kHz; CLKIN |
| ST LSM6DSV16X | 7,523 [PU] | rejected: house and Betaflight ecosystem call it unflyable |
| TDK ICM-45686 | 3 | no stock |

**Decision:** universal LGA-14 land of the OpenFC `imu` sheet (pins 2/3 GND,
10/11 NC, pin 9 to GPIO6), **BMI270 on the BOM**, ICM-42688-P qualified on the
same land. The prototype run is split 5 + 5 and a hover fly-off on the target
frame (noise metric §2 rank 6) picks the release population. One gyro per
revision, declared in the Betaflight target. Supply: own +1V8 from
TPS7A2018PDQNRM3 fed from +3V3, next to the gyro on the same side. Placement
(§10, sketch v3): top, rear quadrant, edge-to-edge distances §11.

### 4.7 Receiver

The house design is the OpenRX-Lite ESP32-C3 + SX1281 circuit. Two facts from
the research change the MCU:

1. Mainline ExpressLRS 4.0.0, 4.1.0 and master register the VTX SPI and MSP-VTX
   devices only under `PLATFORM_ESP32 && !PLATFORM_ESP32_C3` (V, track 05
   verification, `src/src/rx_main.cpp`). A C3 cannot drive the VTX on ELRS 4.x.
2. ESP32-C3FH4 has 0 LCSC stock (2026-10-07), 89 on HQ Online (track 07).

| Option | Area (placed) | VTX control | Sourcing | Verdict |
|---|---|---|---|---|
| ESP32-C3FH4 + SX1281 (OpenRX-Lite) + separate VTX MCU | 86 + 25 mm² | VTX MCU on a half-duplex PIOUART (new code) | C3FH4 0, GD32F130G6 broker-only | no |
| **ESP32-D0WD-V3 + 4 MB NOR + SX1280** | about 96 mm² | ELRS `devVTXSPI` + `MSPVTX` on the shipping code path; pin-compatible with ELRS layout `Generic 2400 Whoop Rx and VTx.json` | 583 / 1,129 / 767 (LCSC); ESP32 also listed at Digi-Key (S) | **chosen**, subject to the fine-pitch EQ (below) |
| ESP32-PICO-V3 (SiP) + SX1280 | about 109 mm² | same | to be quoted | fallback |
| SPI ELRS on the FC | 37 mm² | none | - | not available on RP2350 |
| ESP32-S3FH4R2 | 7x7 + crystal | same | 17 | no stock |

**Fine pitch.** ESP32-D0WD-V3 is QFN-48 5x5 at **0.35 mm pitch** (lead width
0.18 mm, Espressif datasheet). NextPCB publishes 0.38 mm as its fine-pitch
limit (track 07 S4) and JLC's PCBA floor is 0.35 mm, so the part is outside the
fab intersection. Action (O15): the EQ goes to NextPCB now. If accepted: 0.18 mm
pads, one ganged mask opening per side, and a scoped DRU exception for that
footprint. If not: ESP32-PICO-V3 becomes primary (+13 mm² bottom).

**Decision:** ESP32-D0WD-V3 with an external GD25Q32 flash and the CJ17 40 MHz
crystal, SX1280 radio. This deletes the VTX MCU, uses no FC UART for the VTX
and needs no Betaflight driver. The FC sees an MSP VTX over CRSF (`USE_VTX_MSP`,
in RP2350 releases from 2026.6.2). Pins follow `Generic 2400 Whoop Rx and
VTx.json` (V, ExpressLRS/targets 42ed776): CRSF on ESP32 GPIO1/3, radio
SCK/MOSI/MISO/NSS/RST 25/32/33/27/26, BUSY 36, DIO1 37, RGB LED 22, VTX
NSS/MOSI/MISO/SCK 19/18/23/5, PA bias PWM 12, PA detector 4, PA enable
(`vtx_amp_vref`) 2, button/boot 0. Two pins are added for the patched firmware
only (O6): GPIO21 = +3V3_VTX LDO enable (pulled up, so stock ELRS runs the VTX
as usual) and GPIO34 = PA NTC (ADC1). Straps: GPIO12 must read low at reset
(3.3 V flash) and GPIO2 low (pull-down), checked in P4; the first-flash
procedure (§12.1) burns the VDD_SDIO eFuse to 3.3 V, which removes the GPIO12
strap risk for good. ESP32 erratum 3.11 (powering SAR ADC1/ADC2 pulls GPIO36/39
low for about 80 ns) touches radio BUSY on GPIO36: stock ELRS reads the PA
detector only outside the hop window (`timeout()` returns early while
`hwTimer::isTick` is false, V, devVTXSPI.cpp at 8c51826); the NTC read must
follow the same rule (O6 gate 6).

The RF section is the OpenRX-Lite / OpenAIO `rx_esp32c3_sx1281` circuit reused
(TCXO, filter, match, LDO-mode radio), with these changes: MCU swap; SX1281 →
SX1280 (pin-compatible, same ELRS driver, stock); 15 µH DC-DC inductor deleted
(the ELRS layout has no `radio_dcdc`); ceramic antenna deleted, wire-antenna
plated hole instead; **fix the sheet defect: SX1281/SX1280 pin 5 is GND and is
unconnected on both sibling sheets** (09 verification). Sheet name
`rx_esp32_sx1280`.

**Wi-Fi (PINMAP F9).** The Matrix II has a Wi-Fi chip antenna, and ELRS users
configure and update over Wi-Fi, so the board keeps it: a minimal radiator on
ESP32 LNA_IN (net `RF_WIFI`), a short printed stub on L6 at the board edge with
a 0201 pi match and a 2 x 4 mm all-layer copper keepout (rule area `WIFI_STUB`;
about 1 m of range is the goal, measured in V7); Johanson 2450AT18B100E (S) is
the fallback. ELRS calls `disableVTxSpi()` when Wi-Fi starts (V, devWIFI.cpp
l. 1107 at 8c51826), and auto-Wi-Fi after the `wifi-on-interval` would leave the
VTX dark until the next reboot. That interval is a flash-time firmware option
(binary_configurator `--auto-wifi` / `--no-auto-wifi`, on by default in the
Configurator; V), not a hardware-layout key, so a target overlay cannot turn it
off: the published flashing instructions and the README use `--no-auto-wifi`,
and O6 adds a patch that keeps a VTX target's VTX in its last state when Wi-Fi
starts (or a hardware key that suppresses auto-start). ELRS flashing otherwise
goes through Betaflight serial passthrough; recovery is holding RXB at
power-up. There are no extra ESP32 UART pads (they would put a second driver
on the FC's UART0_TX net).

| Part | Primary | Fallback |
|---|---|---|
| RX MCU | Espressif **ESP32-D0WD-V3**, QFN-48 5x5 (0.35 mm pitch), C967021, 583; Digi-Key listing (S) | Espressif ESP32-PICO-V3, QFN-48 7x7, 0.5 mm pitch (S); crystal and flash inside, +13 mm² |
| RX flash | GigaDevice **GD25Q32EEIGR**, 32 Mbit, USON-8 2x3, I grade −40..85 °C, C2973794, 1,129 | Winbond W25Q32JVUUIQ, USON-8 3x4, C2999380, 3,575 |
| 40 MHz crystal | JSCJ **CJ17-400001010B20**, 1612, C2875272, 13,110 [PU]; operating range not listed (P3) | Kyocera CX1612DB40000D0WLLCC class, 1612 (S, Digi-Key); or the NextPCB quote names a global part |
| Radio | Semtech **SX1280IMLTRT**, QFN-24 4x4, C125969, 767 | Semtech SX1281IMLTRT, C2151551, 0 at LCSC, 146 HQ Online [PU] |
| 52 MHz TCXO | YXC **OW7EL89CENUNFAYLC-52M**, 2016, −30..85 °C, C22434896, 5,975 [PU] | 52 MHz 2016 crystal per the Matrix (MPN in P3) |
| 2.4 GHz LPF | TDK **DEA102700LT-6307A2**, 1005, C574024, 3,810 [PU] | Johanson 2450FM07D0034T, C2651081, 0 today [PU] (re-match) |
| RGB LED | XINGLIGHT **XL-1010RGBC-2812B**, 1x1 mm, C5349953, 364,820 [PU] | none (single source) |

Numbers: +13 dBm, no PA/LNA (Matrix ELRS layout `Generic 2400`,
`power_values [13]`, V). Radio in LDO mode costs about +6 mA. ESP32 ELRS load
about 0.07 A; rail average 0.10 A, 0.15 A peak in flight.

### 4.8 VTX and OSD

| Question | Options | Decision |
|---|---|---|
| Synthesiser | RTC6705/RTC6705A (QFN-40 6x6; Fc 5725-5865 MHz over −40..85 °C, V); MAX2871/LMX2572 discrete | **RTC6705 or RTC6705A**; no alternative exists (04 §2.4) |
| PA | RFPA5542 (Matrix, EOL 2023, 5 V only, Iq 150 mA), SKY85743-21 (4.2-5.5 V, LGA 3x5, Iq 190 mA), SE5004L (5.15-5.85 GHz, VCC 3.0-5.5 V, Icq 300 mA, case ≤ 85 °C), QPA9501 / TQP5525 (350 mA, low stock) | **SE5004L-R** on the cell; QFN-20 4x4 footprint shared by six PAs (04 §3.3). No lower-Iq PA exists on that footprint at a 1S supply |
| Control | separate VTX MCU (Matrix MM32F003), Betaflight RTC6705 driver (`#undef` on RP2350), ELRS RX MCU | **ELRS ESP32 `devVTXSPI` + `MSPVTX`** (§4.7) |
| OSD | AT7456E + 27 MHz crystal (40 mm², 50 mA, LGA 78 pcs); PIO FB OSD | **PIO FB OSD** (OpenFC `osd` sheet minus the COS8051 buffer), front end on the bottom; no OSD without camera sync |
| Harmonic filter | none (Matrix) vs LTCC BPF | **Walsin 1608 BPF**; guarantees 20 dB at 10.3-11.7 GHz, 12 dB at 7.25-7.8 GHz (V, Walsin PI V01); rated −40..85 °C, so it sits on the PA side away from the PA body; power handling to be confirmed with Walsin (O7) |
| Connector | U.FL, MHF4, soldered coax | **U.FL** |

Chain: camera CVBS → 75 Ω → SN74LVC1G3157 (camera / OSD level) → RTC6705 video
network (OpenOSD-X reference values) → RTC6705 PAOUT1 (+2 dBm) → 10 pF DC block
→ 50 Ω CPWG < 5 mm → SE5004L → match → BPF → U.FL. RTC6705 on +3V3_VTX. Net
names: `RF_PAOUT1`, `RF_PA_IN`, `RF_PA_OUT`, `RF_UFL` (class RF by pattern).

**PA drive stage (inverting, strap-safe; PINMAP F15).** ELRS raises output by
lowering the PWM count; the window is set by firmware constants, not target
keys: `MIN_PWM` 2000 = YOLO (maximum drive), `MAX_PWM` 3700 = pit, out of 4096,
written as `PWM.setDuty(ch, count*1000/4096)` (V, devVTXSPI.cpp l. 30-31, 164 at
8c51826). The usable range is therefore 49-90 % duty in 0.1 % steps (about 4
counts per real step), 1.6-3.0 V after the RC. Stage, specified against that
window: ESP32 GPIO12 (10 kHz) → two-pole RC (corner ≤ 100 Hz, ≥ 40 dB at 10 kHz)
→ **series base resistor** (keeps the RC linear; the base-emitter junction would
otherwise clamp the second node at about 0.65 V) → **base divider** sized so Q1
is just off at 1.6 V (YOLO: Q2 at the fault limit) and conducting at 3.0 V (pit:
PAOUT1 supply near 0 V) → Q1 NPN common emitter with **emitter degeneration**
that sets the slope → Q2 NPN emitter follower → RTC6705 PAOUT1 choke supply.
Both transistors are one Nexperia **BC847QASZ** (NPN/NPN, DFN1010B-6). Design
rule for P4 (hand calculation or SPICE): 25 and 100 mW land mid-window with at
least 20 real duty steps between them; V5 confirms and Re is the knob. Parts: 9
passives (RC 4, base R, base divider 1, Re, collector divider 2). The RC and the
base path hold GPIO12 low at reset.

**Hardware fault limit, not a power setting.** At a fixed drive the SE5004L
output spreads 6-8 dB across parts, channels, temperature and VCC (gain 30 min /
32 typ dB with no maximum, 3 dB variation within a band, less hot and at 3.0 V;
V datasheet; I spread). A single drive cap cannot both keep every part at or
below 400 mW and let every part reach it, so the cap has one role: Q1's
collector divider (top to +3V3_VTX, bottom to GND; PAOUT1 supply ≤ V_div −
0.65 V) is sized in V5 so that a **minimum-gain part, at 85 °C case and a 3.0 V
cell, just reaches 400 mW after the BPF loss**. A maximum-gain part at the limit
(YOLO, or a firmware fault) then runs into its own compression (about 29-31 dBm
at 3.7-4.35 V, I); the closed-loop 400 mW setpoint (O6 gate 2) is what holds
400 mW. Until that patch exists the top level is published as "max (measured)"
with the unit spread. Pit on boot (RCE), a README antenna warning and a
no-antenna run in V5 cover ruggedness: the datasheet gives only PIN −10 dBm CW
into 6:1 VSWR, and "VTX burns without antenna" is a known Matrix issue.

**PA enable and bias.** PA pin 5 (VREF/EN) is driven by a **switched 2.85 V
reference** (TI LP5907SNX-2.85, ±2 %, input +3V3_RX, EN = ESP32 GPIO2 with the
10 kΩ strap pull-down; active discharge when off). The SE5004L needs VREF
2.80-2.90 V at IEN about 10 mA (abs max 3.6 V, V); a GPIO through a series
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
between units, and the ESP32 ADC reference spans 1.0-1.2 V (about ±9 % in counts,
1-2 dB). Hence the ±3 dB unit-to-unit target (rank 4) and per-unit calibration
as an O6 item. PA VCC: 10 µF X6S (GRM155C80J106ME11D) shared, plus per-pin RF
decoupling (1 nF + 100 pF) at VCC pins 8/9 and 18/19/20 on both package sides,
following the Skyworks EK1 layout (six capacitors per the datasheet); no
ferrite: a 220 Ω power bead with the 10 µF resonates at 50-150 kHz, where the
ESCs put their ripple. The 3-pad selector sets PA VCC = +BATT (default) or +5V.
A 0201 NTC (Murata NCP03XH103F05RL, 10 kΩ 1 %, B 3380, −40..125 °C, C98098,
175,100) next to the PA with a Yageo RC0201FR-0710KL divider (C106225 [PU])
feeds ESP32 GPIO34 for the thermal derate (O6 gate 6).

**RF pads.** On the 77 µm L1-L2 dielectric the 50 Ω line is about 0.105 mm wide
(§8.2), while the U.FL signal pad and the DC-block, match and BPF pads are much
wider: over solid L2 a U.FL centre pad is about 0.3-0.5 pF, |Γ| about 0.26-0.40
at 5.8 GHz (I). So L2 is cut out under the U.FL signal pad and under every RF pad
wider than about 0.3 mm, with GND poured on L3 under that area as the local
reference (rule area `RF_PAD_CUTOUT`), verified with the KiCad calculator or an
EM solver at P5. No DNP filter footprint on the line. RTC6705 NC pads 1, 2, 3,
4, 12, 13, 14, 15, 16, 18, 34, 36, 37 (the verified OpenOSD-X list; pin 17 is
AVDD_6.5, a 3.3 V supply, and stays) may be removed from the land if P5 needs
the escape channels; the EP is never touched.

| Part | Primary | Fallback |
|---|---|---|
| Synthesiser | RichWave **RTC6705** (or RTC6705A), QFN-40 6x6. **0 authorised stock** (LCSC 0, HQ Online 0, Digi-Key none); brokers: Win Source 30,000 at $7.82-11.73 (findchips, 2026-10-06). **Consigned with traceability (§15)** | none exists |
| 8 MHz reference | Yajingxin **TAXM8M4RDBCCT2T**, 3225, 10 pF, ±10 ppm, −40..85 °C, C400090, 169,930. D12 asks for a 2520 part and the budget counts it (−3.4 mm²), but 8 MHz is rare in 2520 (those blanks usually start at 12-16 MHz; none found on 2026-10-07): P3 searches, else the 3225 stays (+3.4 mm² top) | YXC X322508MSB4SI, 3225 (S) |
| PA | Skyworks **SE5004L-R**, QFN-20 4x4, 3.0-5.5 V, 5.15-5.85 GHz, C210263, 1,339 (HQ Online 0; Digi-Key 21 wk) | Qorvo QPA9501TR13, same footprint (prototype only, 124); Skyworks SKY85743-21, LGA-24 3x5 (5 V, new footprint) |
| BPF | Walsin **RFBPF1608060K98Q1C**, 5150-5950 MHz, 1608, C2442150, 12,780 | TDK DEA165538BT-2263A1-H, C2835388, 3,975 (clips 5945 MHz) |
| U.FL | Hirose **U.FL-R-SMT-1(80)**, −40..90 °C, C88374, 65,950 [PU] | I-PEX 20279-001E-03 (S) |
| PAOUT1 choke | Murata **LQP03TN4N7H02D** 4.7 nH 0201, C86126, 148,100 | none verified |
| PA drive stage | Nexperia **BC847QASZ**, NPN/NPN, DFN1010B-6, C549491, 227,680 (V) | Nexperia BCM847QASZ (matched pair, S) |
| PA reference | TI **LP5907SNX-2.85/NOPB** (§4.2) | 2.8 V variant (lever a) |
| PA NTC | Murata **NCP03XH103F05RL** + Yageo RC0201FR-0710KL | none verified |
| OSD switch | TI **SN74LVC1G3157DTBR**, X2SON-6, −40..125 °C, C2673087, 1,540 [PU] | none (TI single source in X2SON) |
| OSD sync comparator | TI **TLV7031DPWR**, X2SON-5, C2876045, 6,236 [PU] | none verified |
| OSD clamp diode | Diodes **SDM02U30LP3-7B**, DFN0603, C151629, 16,740 [PU] | none verified |

`osd` sheet reuse, changes: drop COS8051 and its 3 resistors; scale the level
divider about 5x down (top about 750-820 Ω, Thevenin about 190 Ω), keeping the
OSD_W pin at ≤ 3 mA. OSD levels are absolute, so with AC-coupled cameras they
move against the picture's black level: V9 measures black and white on the
target cameras, and a sync-keyed clamp is added only if needed.

**Pit, disarm and heat** (I, 04 §6, 06 §4; V from the ELRS and Betaflight
source). PA at 400 mW draws about 0.55 A from the cell (2.0 W at 3.7 V, 1.64 W
heat); at 25 mW about 0.30 A (PA quiescent dominates, 1.09 W). Stock ELRS pit
drops VREF and sets the maximum PWM count but never powers the RTC6705 down
(`POWER_AMP_OFF` defined but unused), so pit keeps the RTC6705's 0.5 W on the
board and leaks its output through the off PA (V5). `vtx_low_power_disarm`
sends power index 1, which ELRS turns into "VPD setpoint 0, maximum count" with
VREF **on**: a disarmed quad that left pit keeps the PA biased at about
1.0-1.1 W. Release requirements (O6): index 1 handled as pit; pit and disarm
power the RTC6705 down (GPIO21, VTX SPI tri-stated, frequency re-sent) or write
`POWER_AMP_OFF`; a thermal derate from the PA NTC. Defaults: pit on boot (RCE),
25 mW, `vtx_low_power_disarm` ON (pit once the patch is in; until then the
README says to switch pit on before landing or benching). 400 mW is continuous
only at high airflow (PA case ≤ 85 °C needs h ≥ 56-70 W/m²K at hover, §4.3) and
time-limited otherwise (τ 26-69 s).

### 4.9 Blackbox

| Option | Body | Stock | Verdict |
|---|---|---|---|
| **W25Q128JVPIM**, WSON-8 6x5, on SPI0 | 30 mm² | C2441427, 24,670 | **chosen** (Matrix parity, deep stock) |
| GD25Q128EQIG / PY25Q128HA-QVH, USON-8 4x4 | 16 mm² | no distributor found | later (−16 mm² placed) |
| 8 MB (W25Q64JV class) in a smaller package | - | - | §9.3 lever (Matrix has 16 MB) |
| NOR on the RP2354A QSPI bus, CS1 | 1 GPIO instead of 4 | - | no: flight-unvalidated driver, XIP stall risk (05 §1.2) |

The W25Q128JVPIM is the "I" grade (−40..85 °C, V), one of the 85 °C parts. The
105 °C "J" grade (same land) would not raise the board limit, but is taken if the
P0 BOM quote shows stock. Fallback: Winbond W25Q128JVPIQ, C190862, 6,862. Placed
on the top in the rear quadrant (§10), away from the PA and the RTC6705.
`blackbox` sheet keeps its name, bus (SPI0, GPIO18-21) and CS pull-up; microSD
removed.

### 4.10 Connectors and pads

| Item | Decision | Part / geometry | Why |
|---|---|---|---|
| Battery | BT2.0 pigtail (22 AWG, 40 mm, user-fitted), two plated holes **Ø 1.1 mm finished** in 3.0 x 2.0 mm pads (long side along the edge), both sides, ≥ 12 power vias (0.40/0.20) per pad into the pours | no PCBA part | a wire through a PTH cannot peel the pad; Ø 1.1 keeps ≥ 1.025 mm for stranded 22 AWG with the ±0.075 mm PTH tolerance. The board check runs with `--min-hole 2.0` |
| Motors | 12 solder pads 1.0 x 1.8 mm on the top, each with a plated **Ø 0.5 mm wire-anchor hole** near the outer end, pitch 1.5 mm, at the board edge facing each motor | no PCBA part | Matrix "solder-required" equivalent. A 1.25 mm THT plug does not fit the fab-rule intersection (pitch ≥ 1.30 mm), and four SMD PicoBlade headers cost 173-212 mm² |
| USB | JST **BM04B-SRSS-TB(LF)(SN)**, SH1.0 4-pin vertical, bottom, right edge front (under the camera plug), C160390, 44,345; net `+5V_USB` | fallback BM04B-SRSS-TBT(LF)(SN), C495539, 2,334 (same land) | as on the Matrix; BetaFPV adapter pinout to be measured (O3) |
| Camera | JST **BM03B-SRSS-TB(LF)(SN)**, SH1.0 3-pin vertical, top, right edge front, C160389, 31,415, plus CAM / 5V / GND pads | fallback BM03B-SRSS-TBT(LF)(SN), C495538, 1,156 | Matrix CAM IN plug; first area lever if P2 does not close (§9.3) |
| VTX antenna | U.FL, top, front corner | §4.8 | |
| RX antenna | plated hole Ø 0.5 mm at the left edge, rear half, **(−12.3, +6.5)**; insulated λ/4 wire **trimmed to resonance** (about 28-29 mm for a jacketed wire, velocity factor 0.90-0.95; 30.7 mm only in free space), set by return loss in V7 | - | Matrix uses the same. The wire runs rearward or up the canopy, ≥ 10 mm from the motor leads (M3 leaves the left edge at y −7…−3) and from the pigtail; the hole pad edge is ≥ 5 mm from the battery pads (5.7 mm in sketch v3) |
| User pads | TX1 RX1 5V GND (UART1), LED 5V GND (LED strip), BZ+ BZ− (buzzer), CAM 5V GND (camera): 12 pads 1.0 x 1.2 mm, top, at the edges | - | Matrix II parity. Edge budget (§10): fits in total; the right edge is over-subscribed, resolved at P2 |
| Test pads | FCB (RP2354 QSPI_SS boot) + GND, RXB (ESP32 GPIO0), CLK / DIO (FC SWD), 8x C2D/C2CK (ESC) | Ø 0.8 mm, bottom | no tact switch; the C2 pads are also the production programming contacts (§12.1) |

---

## 5. Power budget

### 5.1 +5V rail loads (design)

| Load | A at 5 V | Note |
|---|---|---|
| Camera | 0.12 | allowance (BetaFPV C03: 100 mA at 5 V, V) |
| +3V3 (FC: RP2354A, NOR, OSD front end, LEDs, INA186, gyro via +1V8) | 0.09 | I (conservative; measured in V8) |
| +3V3_RX (ESP32 ELRS + SX1280 LDO mode + RGB LED + PA reference) | 0.11 | I, 0.16 peak |
| +3V3_VTX (RTC6705) | 0.10 | 95 mA datasheet figure for 13 dBm mode; the PAOUT1-only figure is "TBD" in the datasheet, so this is an upper bound (lever c) |
| LED strip | 0.20 | user allowance |
| Buzzer | 0.03 | |
| User 5 V pads | 0.05 | allowance |
| **Total** | **0.70 A (3.6 W)** | 0.42 A without the user allowances; 1.25 A if the PA is moved to +5V. USB only: 0.42 A with the camera |

### 5.2 Every load from the cell, at 3.0 V and 4.35 V

| Load | at 3.0 V in | at 4.35 V in | Basis |
|---|---|---|---|
| Boost input for 0.70 A at 5.15 V | 1.37 A (η 0.88) | 0.90 A (η 0.92) | TPS61022 efficiency curves (S) |
| SE5004L PA, pit / 25 / 100 / 400 mW | 0 / 0.30 / 0.35 / 0.55 A | same | I (Icq 300 mA spec, 04 §6.1); out of rating below 3.0 V |
| 4x EFM8BB51 at 49 MHz | 0.020 A | 0.020 A | V (55.5 µA/MHz), I (peripherals) |
| **Cell current (no motors), VTX pit** | **1.39 A / 4.17 W** | **0.92 A / 4.01 W** | |
| VTX 25 mW | 1.69 A / 5.07 W | 1.22 A / 5.31 W | |
| **VTX 400 mW** | **1.94 A / 5.82 W** | **1.47 A / 6.40 W** | |
| ESC per motor at hover / 6 A / 12 A | 0.09 / 1.93 / 7.23 W of loss on the board | same | §4.3 |

### 5.3 5 V margin (P0 gate)

TPS61022 with 0.68 µH (Isat 6.5 A), 1 MHz, η 0.88, per TI SLVSDX7D §8.2.2.2
(inductance −30 % = 0.48 µH; I): at 3.0 V in, D = 0.47, ripple 3.0 A, peak held
to 80 % of Isat → **1.96 A** nominal peak against 0.70 A (**+180 %**); at 2.8 V
in, **1.83 A (+161 %)**; with nominal inductance 2.20 A at 3.0 V. With the PA on
+5V (1.25 A): +57 % at 3.0 V. Gate "≥ 20 % margin at 3.0 V on datasheet
curves": **pass** on the calculation. Limits that keep it a calculation: Cout
(≥ 20 µF effective above 1.5 A; three X6S 0603 give about 15-21 µF at 5.15 V),
inductor ripple above TI's 40 % guidance, and heat: the binding limit is TJ ≤
125 °C (V §6.3); about 1.0-1.3 W of loss at 1.5 A from 2.8-3.0 V with ΨJB
36.7 K/W (V) puts TJ at 125 °C on a 77-85 °C board. So the published figure is
the V1 table of continuous current per VIN and board temperature, claim
≤ 1.5 A.

### 5.4 Thermal budget (on-board heat) and heat levers

| Source | Hover, VTX 400 mW, 3.7 V | Hover, VTX 25 mW | Bench, disarmed, pit (stock ELRS) | Bench, disarmed after leaving pit (stock ELRS) | Bench, pit, RTC6705 off (patched ELRS) | USB only |
|---|---|---|---|---|---|---|
| PA | 1.64 W | 1.09 W | 0 | 1.0-1.1 (Icq, VREF on) | 0 | 0 |
| RTC6705 + its LDO | 0.50 | 0.50 | 0.50 | 0.50 | about 0 | 0.50 |
| FC rail (LDO + loads) | 0.45 | 0.45 | 0.45 | 0.45 | 0.45 | 0.45 |
| RX rail (LDO + loads + PA reference) | 0.55 | 0.55 | 0.52 | 0.55 | 0.52 | 0.52 |
| Boost loss / OR diode | 0.36 | 0.36 | 0.24 | 0.24 | 0.24 | 0.09 |
| ESC MCUs | 0.07 | 0.07 | 0.07 | 0.07 | 0.07 | 0 |
| ESC FETs (1 A/motor) | 0.36 | 0.36 | 0 | 0 | 0 | 0 |
| Shunt + copper | 0.05 | 0.05 | 0 | 0 | 0 | 0 |
| **Total** | **4.0 W** | **3.4 W** | **1.8 W** | **2.8-2.9 W** | **1.3 W** | **1.6 W** |
| Board rise (flight G 0.042-0.11 W/K; bench still air 0.025-0.035 W/K) | +36-95 K | +31-81 K | +51-72 K | +80-116 K | +37-52 K | +46-64 K |

At 25 °C ambient the 85 °C parts allow +60 K and the PA case adds its local
6-12 K/W: hover needs h ≥ 46-52 W/m²K at 25 mW and 56-70 at 400 mW. On the bench
in still air only the patched pit case stays inside; until the ELRS patch is
merged the README requires a bench fan or short sessions. Camera, LED strip and
buzzer power is dissipated off the board. Time constant in flight about 26-69 s
(C about 2.9 J/K).

The continuous rating is set by about 3.0 W of non-ESC heat, not by the FET
path, so the heat levers carry more rating than the FET choice. **Decision gate
before P2:** (b) is decided on area before P2 (rejected for rev1 unless P2
frees ≥ 20 mm² on the bottom); (a) and (c) are measured on the first boards or
an SE5004L/RTC6705 bench setup (V5, V8) and adopted if they pass; the published
rating states which levers are in.

| Lever (`thermal_v2.py`, h 55, 25 mW, k_PA 12-6 K/W) | Heat | One channel / all four | Cost, status |
|---|---|---|---|
| none (baseline) | - | 0-1.6 A / 1.3-1.9 A | - |
| (a) PA bias: lower fixed VREF (Icq 300 → about 150 mA). VREF below 2.80 V is outside the datasheet window: gain and stability qualified in V5 before a 2.8 V or lower reference variant is fitted. No lower-Iq PA exists on the footprint at 1S | −0.55 W | 3.4-3.7 A / 2.4-2.5 A | bench item 2 |
| (b) 3.6 V buck-boost for the 3.3 V loads | −0.45 W | 1.3-3.2 A / 1.8-2.3 A | +15-20 mm² bottom; not in rev1 unless P2 frees it |
| (c) RTC6705 PAOUT1-only current (60 mA assumed instead of 95) | −0.17 W | 0-2.3 A / 1.5-2.0 A | measure (V8) |
| (d) 0.68 µH boost inductor | −0.04 W | 0-1.8 A / 1.3-1.9 A | **adopted** (§4.2) |
| (a)+(b)+(c)+(d) | −1.21 W | 4.7 A / 2.9-3.0 A | hover then needs h ≥ 29 |

---

## 6. Weight (detail of §1)

| Item | Estimate |
|---|---|
| PCB 6L 1.0 mm, 6.97 cm²: dielectric 1.07-1.17 g; copper outer 1 oz at 60 % (+ Type VII cap plating), L2/L4/L5 0.5 oz at 85 %, L3 0.5 oz at 40 %: 0.59-0.70 g; mask 0.03 g | 1.70-1.90 g |
| FETs 24x SON 2x2 (about 10 mg each, I) | 0.24 g |
| ICs, crystals, inductors | 0.60-0.70 g |
| Passives (about 225) | 0.06-0.08 g |
| Connectors (2x SH1.0 vertical, U.FL) | 0.13 g |
| Solder | 0.12 g |
| **Total** | **2.85-3.17 g, about 2.9-3.2 g** (target ≤ 3.5 g, margin 0.3-0.6 g) |

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
| Panel tabs | 4 tabs, 1.2-1.5 mm wide with mouse bites, each with a ≥ 1.0 mm part keepout (MLCC crack risk), at free edge segments between pad groups: T1 front-arc midpoint (direction 45°, 2.4 mm from the U.FL), T2 top edge x ≈ −8.9 (between the left flange and the M4 pads), T3 left edge y ≈ −8.9 (between the left flange and the M3 pads), T4 rear edge x ≈ −9.3 (between the rear flange and the B+ pad). Final positions with the P2 placement and the NextPCB panel EQ |
| Panel | ≥ 70 x 70 mm with rail fiducials (JLCPCB Standard PCBA minimum for a single design, capability page 2026-10-07; needed for 0201 and 0.35 mm pitch), board-level fiducials on both sides; the panel is its own project per LINEUP B16 |
| Guides | 25.5 and 26.0 mm frame patterns drawn on `User.Eco1`; front marked on `User.Eco2` |

---

## 8. Stackup and fab rules

**Owner rule: through vias only.** Filled-and-capped via-in-pad (IPC-4761 Type
VII, non-conductive epoxy) is a through via and is used in every pad that holds
a via. No blind, buried or laser vias. The via is the OpenDrone standard
**0.35/0.20** (D6: owner-confirmed buildable at NextPCB).

### 8.1 DFM intersection (NextPCB ∩ JLCPCB)

NextPCB values: track 07 (S1 standard capabilities, S2/S3 advanced and HDI pages,
S4 assembly, S12 stackup library, verified 2026-10-06). JLCPCB values:
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
| Fine-pitch IC | 0.38 mm pitch (S4) | 0.35 mm (PCBA floor) | **0.38**; ESP32-D0WD-V3 (0.35) only with a NextPCB EQ approval and a scoped exception (O15) |
| Copper to routed edge | 0.20 | 0.20 | **0.20** (components 0.30) |
| Mask expansion | ≥ 0.04 | 1:1 allowed (LDI) | **0.04** |
| Mask bridge, green | 0.089 | 0.10 | **0.10**; ganged opening on the 0.35 mm-pitch ESP32 sides |
| Silk line / text height | screen 0.127 / 0.76; inkjet 0.08 / 0.61 | 0.15 / 1.0 | **0.13 / 0.8** (D12, commons standard; meets NextPCB and LINEUP B11; below JLC's published legibility floor, so JLC silk legibility is not guaranteed: the one recorded exception to "DFM-compatible with both fabs") |
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
| **L1 F.Cu** | 0.035 (1 oz finished) | top parts (VTX, P-FETs, EFM8s, NOR, gyro, CAM plug), 5.8 GHz CPWG, video, VTX control, phase pours, local +5V/+3V3 pours |
| prepreg 1080 | 0.077 | εr 4.2 |
| **L2 In1.Cu** | 0.0175 | **solid GND** (RF and top-side reference, ESC return); cut only under wide RF pads (§4.8) |
| core | 0.30 | |
| **L3 In2.Cu** | 0.0175 | digital signals between the sides; references L4 (0.103 mm away) about three times more than L2 |
| prepreg 2313 | 0.103 | |
| **L4 In3.Cu** | 0.0175 | **+BATT plane** (ESC feed), one solid pour under every L3 route |
| core | 0.30 | |
| **L5 In4.Cu** | 0.0175 | **solid GND** (bottom-side reference, ESC return) |
| prepreg 1080 | 0.077 | |
| **L6 B.Cu** | 0.035 | bottom parts (FC, RX, power, N-FETs, OSD front end), 2.4 GHz feed, Wi-Fi stub, local +5V/+3V3 pours |
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
| Signal | 0.35 / 0.20 mm (annular 0.075) | default; every via in a pad (Type VII): the phase fields in the P drain pads, EP arrays, 0201 decoupling vias |
| Power | 0.40 / 0.20 mm (annular 0.10) | +BATT, GND and phase arrays outside pads |

0.20 mm via in 1.0 mm board: aspect ratio 5:1, about 1.4 mΩ each. Counts: ≥ 12
power vias per battery pad (25 A), 8 phase vias per P drain pad (in-pad), 4
+BATT and 3 GND vias per phase beside the lands, 9 in the PA EP, 4-9 in each QFN
EP. Array pitch ≥ 0.40 mm. Remove unused inner annular rings.

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

Net classes (names after OpenAIO; colours set through netclass directive
labels):

| Class | Nets | Track | Clearance | Via | Colour |
|---|---|---|---|---|---|
| Default | signals | 0.09 | 0.09 | 0.35/0.20 | - |
| VBAT | +BATT_IN, +BATT, shunt nodes | 0.50 (pours) | 0.15 | 0.40/0.20 | red |
| Phase | 12 motor phase nets (in-sheet `PHASE_A/B/C`) | 0.50 (pours) | 0.15 | 0.40/0.20 | orange |
| Gate | 24 FET gate nets (in-sheet `A_COM`, `A_PWM`, ...) | 0.15 | 0.10 | 0.35/0.20 | yellow |
| Power | +5V, +5V_USB, +3V3, +3V3_RX, +3V3_VTX, +1V8, +1V1 | 0.25 | 0.09 | 0.35/0.20 | magenta |
| Analog | video, OSD level/sync, VBAT/current sense, PA detector | 0.10 | 0.15 | 0.35/0.20 | cyan |
| RF | `RF_*` nets: 5.8 GHz chain, 2.4 GHz feed, Wi-Fi feed | 0.105 | 0.15 | 0.35/0.20 (fence) | green |
| USB | USB_D_P / USB_D_N | 0.12 (pair gap 0.12) | 0.12 | 0.35/0.20 | blue |
| GND | GND | 0.20 | 0.09 | 0.40/0.20 | - |

Power net names per the lineup decision and LINEUP A11: +BATT, +5V, +3V3, +1V8,
GND, with suffixed rails +BATT_IN, +5V_USB (the template name; `VBUS` would fail
A11), +3V3_RX, +3V3_VTX, +1V1.

Custom rules below the template marker: different-net hole to hole 0.30; PTH
pad hole to hole 0.45; PTH annular 0.20; PTH hole clearance 0.28; inner-layer PTH
hole to copper 0.30; NPTH to copper 0.20; SMD pad to track 0.13; disallow
micro/blind/buried vias; courtyards at max(body, land) + 0.10 with
`courtyards_overlap` raised to **error** and courtyard clearance 0; 0402-to-0402
+0.05; tall parts (U.FL, SH1.0, 2520 inductor) +0.5 mm to 0201/0402; user pads
and battery/motor pads ≥ 0.5 mm to any 0201/0402 (iron rework); classes Analog,
RF and Gate and the name-based sensitive set (`SPI1.*`, `GYRO_*`, `VTX_SPI.*`,
`PA_*`) disallowed on In2.Cu/In3.Cu; no non-GND via inside `RF_VTX_CHAIN` and
`RF_RX_FEED` (`A.NetName != 'GND' && A.intersectsArea(...)`); keepout rule
areas for the grommet flanges, the RF zones, `RF_PAD_CUTOUT` (In1.Cu, zone-fill
keepout), `RF_RX_FEED` (In4.Cu solid under the 2.4 GHz feed) and `WIFI_STUB`
(all layers, 2 x 4 mm); `RF_RX_EXIT` on B.Cu only (the wire's exit side); a
scoped mask exception for the ESP32 footprint if the EQ passes.

KiCad features (owner rule). Delivered in P1 by `setup_board.py`: the 16
template-ignored DRC checks re-enabled (D7), component classes `PASSIVE_0201`,
`PASSIVE_0402`, `TALL`, `SOLDER_PAD`, net-class priorities and colours, the DRU
self-test. Still to deliver: a design block (or multichannel placement) for
ESC1-4 (P2), the own checks that every copper item lies inside Edge.Cuts shrunk
by 0.20 mm and the cross-side X-ray and heat rules of §11 (P2), zone priorities
written down with the pours (P5), a jobset for the fab outputs (P7).

**Follow-ups for `setup_board.py` from this revision** (`board_spec.json`
already expects the board-level ones, so `check_board_setup.py --spec` fails
until they are in): minimum through hole 0.20 (it writes 0.15); `RX_ANT_HOLE`
(−12.3, +6.5) with `RF_RX_EXIT` on B.Cu only; rule areas `RF_PAD_CUTOUT`,
`RF_RX_FEED`, `WIFI_STUB`; USB patterns `*/USB_D_P`, `*/USB_D_N`; Gate patterns
`/ESC?/?_COM`, `/ESC?/?_PWM`; Phase pattern `/ESC?/PHASE_?`; Power pattern
`+5V_USB` instead of `VBUS`; the In2/In3 class and name rules and the
`RF_VTX_CHAIN` / `RF_RX_FEED` via rules above; silk minimum 0.8 / 0.13. Then
re-run `check_board_setup.py`, `check_rules.py` and ERC/DRC.

---

## 9. Area budget

### 9.1 Usable area per side

Outline (I, `outline.py`, 10 µm grid): body 697.0 mm² − front arc 7.2 + ears
35.7 − holes 28.9 = **696.6 mm²**. Usable for parts, per side: inside a 0.30 mm
edge band and outside Ø 5.2 mm grommet-flange keepouts around the 3 holes
(flange diameter assumed; measure a BetaFPV ball at P2) = **643.6 mm²**.

### 9.2 Placed area per block (0.2 mm body/land spacing, perfect tiling)

Method (I, `budget_v3.py`): each part counts (land L + 0.2) x (land W + 0.2).
Lands: 0201 0.80 x 0.35, 0402 1.30 x 0.55, 0603 2.10 x 0.90; leadless ICs with
toe pads at IPC density L (body + 0.4) or the datasheet land (EFM8BB51 Table 7.2:
4.0 mm); bottom-terminated parts (LGA, X2SON, FET SONs, crystals) at body size.
Labels count their Tokyo glyph box at 0.8 mm height plus 0.15 mm mask clearance.
Every keepout and spacing rule of §7, §8.4 and §10 is an explicit line. Vias come
from a counted list: 134 vias outside pads and outside the ESC cells (perimeter
stitching ≤ 3 mm 37, RF fences 19, ESC side changes 24, video 4, VTX control 8,
rails 6, FC to top pads 4, second vias of about 12 L3 routes 12, pour stitching
20) at 0.28 mm² on each side, plus 15 via sites per phase in the ESC cells (7 on
the top, 15 on the bottom: through vias occupy both sides); vias in pads use no
area. Configuration (a) = D12 with the NOR and the gyro on the top (sketch v3).

| Block | Parts | Top mm² | Bottom mm² | Notes |
|---|---|---|---|---|
| ESC x4 | 88 | 180.1 | 141.4 | 4x QFN-20 (4.0 land), 12x CSD25310Q2, 36x 0201 top; 12x CSD13202Q2, 12x 0201, 4x 0603 X6S, 8 C2 pads bottom; cell vias 7 top / 15 bottom per phase |
| Input, protection, sense | 15 | - | 31.9 | 2x 0603, SOD-123FL, 1206 Kelvin shunt, SC-70-6, 10x 0201 |
| FC core (RP2354A, beeper, LED-strip translator, LEDs, test pads) | 41 | - | 97.1 | QFN-60 (7.4 land), 2520 crystal, 2016 inductor, XSON6 translator, 5 test pads |
| Gyro + 1.8 V LDO | 7 | 13.7 | - | top (sketch v3) |
| PIO OSD front end | 12 | - | 8.1 | |
| Blackbox NOR | 3 | 38.1 | - | WSON-8 6x5, top (sketch v3) |
| RX (ESP32 + flash + SX1280 + LDO + Wi-Fi stub) | 41 | - | 105.9 | Wi-Fi stub keepout 8 mm² + 3x 0201 |
| VTX (RTC6705, PA, BPF, U.FL, LDO, PA reference, drive stage, NTC, selector) | 68 | 134.0 | - | BC847QAS + 9x 0201, LP5907 + 2x 0201, per-pin PA decoupling, 0402 selector |
| Power (boost, FC LDO, OR diode, USB sense FET, camera filter) | 19 | - | 38.0 | 4x 0603 X6S, AP1606 + 2x 0201 |
| Connectors | 2 | 28.8 | 33.6 | SH1.0-3 vertical (T), SH1.0-4 vertical (B) |
| **Components** | **296** | **394.7** | **455.9** | |
| Pads, labels, silk art | | 129.4 | 93.0 | T: motor pads 32.8; battery 17.5; 12 user pads 20.2 + labels 30.1; M1-M4, + −, 1S, ANT 22.9; connector names 6.0. B: motor PTH rings 17.3; battery 17.5; logo + OPEN/AIO/WHOOP + REV1 41.7; test-pad and USB labels 16.5 |
| Keepouts and spacing rules | | 54.0 | 42.9 | T: RX antenna copper keepout 6.0; 5.8 GHz 1 mm part-free band 13.0; panel tabs 12.0; tall-part halos 11.0; iron-rework halos 12.0. B: RX wire-exit area 18.8; tabs 12.0; tall-part halos 10.3; rework halo 1.8 |
| Via allowance | | 37.5 | 37.5 | 134 counted vias x 0.28 mm² |
| **Total** | | **615.6 mm²** | **629.3 mm²** | |
| **Share of 643.6 mm²** | | **95.7 %** | **97.8 %** | gate ≤ 85 %: **fail** |

Cases (same method; per side, then both sides of 1287 mm²):

| Case | Top | Bottom | Both |
|---|---|---|---|
| (a) D12, NOR and gyro on the top | 95.7 % | 97.8 % | 96.7 % |
| D12 with the round-1 allocation (NOR and gyro on the bottom) | 87.6 % | 105.8 % | 96.7 % |
| (a) without the camera plug (pads only) | 89.7 % | 97.8 % | 93.7 % |
| (a) without the Wi-Fi radiator | 95.7 % | 96.3 % | 96.0 % |
| (a) without plug and Wi-Fi | 89.7 % | 96.3 % | 93.0 % |
| (b) AGM210MAP dual, 8 top / 4 bottom (Matrix split) | 103.3 % | 91.6 % | 97.5 % |
| (b) AGM210MAP dual, 6 / 6 | 99.9 % | 95.7 % | 97.8 % |
| round-1 stage (CSD25402Q3A 3.3x3.3 P) | 112.1 % | 93.7 % | 102.9 % |
| (c) via sensitivity: (a) with 60 more vias | 98.3 % | 100.4 % | 99.3 % |

**Calibration on the reference board** (I, photo BOM of 00/01, passives
estimated as 180x 0201 + 20x 0402): the Matrix II's components score 842 mm² by
this method (this board 851 mm²); with this board's pads, labels, keepouts and
vias it would sit at 96.1 % of both sides, and at 88.4 % with three quarters of
them. The reference board exists at this density, so the 85 % perfect-tiling
gate rejects the board it is meant to match: the margin is not calibrated, and a
real placement nests parts, overlaps keepouts and puts tented vias under silk in
ways the sum does not credit. That is why D12 (5) makes the P2 probe the proof.
It does not make 96.7 % comfortable: routing closure with through vias is the
risk carried (§15.4).

### 9.3 What gives if P2 does not close

Levers, in order and cumulative, with the result per side from `budget_v3.py` (applied to (a)):

| Step | Lever | Top | Bottom | Status |
|---|---|---|---|---|
| 0 | (a) as above (D12 applied: CSD25310Q2, labels 0.8 mm, C2 pads unlabelled, LP5912 VTX LDO, 2520 8 MHz crystal) | 95.7 % | 97.8 % | P2 probe |
| 1 | camera pads only, no SH1.0 plug (Matrix has the plug) | 89.7 % | 97.8 % | owner, if P2 fails |
| 2 | USB on 4 pogo pads with a clip-on adapter (UD 4IN1 pattern; loses BetaFPV adapter compatibility) | 89.7 % | about 93 % | owner, if P2 fails |
| 3 | no Wi-Fi radiator (Matrix has Wi-Fi) | 89.7 % | about 91.5 % | owner, if P2 fails |
| 4 | HDI 1+N+1 (owner rejected HDI for OpenAIO): stitching and fence vias become one-sided microvias (about −10.6 mm² per side) and the N-source GND vias stop landing on the top (−10 mm² top) | about 86 % | about 90 % | owner |
| 5 | body 27.4 mm instead of 26.4 (about +52 mm² usable per side; frame fit and the Matrix envelope change) | about 80 % | about 83 % | owner waiver |
| - | 8 MB NOR in a smaller package (Matrix has 16 MB) | −2 to −3 points on its side | | owner |

No single lever reaches 85 % on both sides; steps 1-4 together leave the bottom
near 90 %. The owner decides between them only if the P2 probe does not close
(O14). The FET stage is not a lever any more: case (b) costs the same area as
D12 (§9.2), and the round-1 stage costs more.

---

## 10. Floorplan sketch

Key packages by their land extents (not centres), from `spec/sketch_v3.py`,
which checks: inside the usable area; 0.2 mm land gap per side; no exposed pad
on one side over an exposed pad or LGA land on the other; no heat source above
0.3 W over an 85 °C part (PA with a 2 mm margin); gyro, boost, antenna and ESP32
distances. **All checks pass for the parts listed; the passives fill is the P2
probe, which the budget says will not close on the bottom without nesting.**
Coordinates: KiCad top view, origin at the body centre, +x right, +y down.
Flight-forward points at the top-right corner. Motors: **M4 front-left beyond
the top edge, M2 front-right beyond the right edge, M1 rear-right beyond the
bottom edge, M3 rear-left beyond the left edge**.

| Block | Side | Land extent x / y (mm) | Notes |
|---|---|---|---|
| M4 / M3 motor pads | T | M4 x −7.0…−3.0 on the top edge; M3 y −7.0…−3.0 on the left edge | 3 pads each at 1.5 mm pitch |
| M1 / M2 motor pads | T | M1 x 4.0…8.0 on the bottom edge; M2 y 4.5…8.5 on the right edge | |
| ESC4 P-FETs / N-FETs | T / B | P −8.95…−2.25 / −9.35…−7.15; N −8.95…−2.25 / −11.75…−9.55 | N outward under the motor-pad strip; no overlap with the P lands |
| ESC3 P / N | T / B | P −9.35…−7.15 / −6.95…−0.25; N −11.75…−9.55 / −6.95…−0.25 | |
| ESC1 P / N | T / B | P 2.25…8.95 / 7.15…9.35; N 2.25…8.95 / 9.55…11.75 | |
| ESC2 P / N | T / B | P 7.15…9.35 / 0.25…6.95; N 9.55…11.75 / 0.25…6.95 | |
| EFM8 ESC4 / ESC3 / ESC1 / ESC2 | T | −6.4…−2.4 / −6.95…−2.95; −6.95…−2.95 / −2.75…1.25; 2.4…6.4 / 2.95…6.95; 2.95…6.95 / −1.25…2.75 | behind their P groups |
| RTC6705 | T | −2.05…4.35 / −7.85…−1.45 | centre front; nothing at 85 °C beneath |
| SE5004L PA | T | −1.0…3.4 / −12.4…−8.05 | PAOUT1 trace < 5 mm; ESP32 (125 °C) beneath, no EP overlap |
| BPF, U.FL | T | BPF 3.6…5.3 / −10.6…−9.7; U.FL 6.0…9.15 / −12.2…−8.2 | front corner; 5.8 GHz line on L1 over solid L2 |
| VTX LDO, PA reference, 8 MHz crystal, drive stage, NTC | T | 4.55…8.1 / −7.85…−1.45 | NTC at the PA edge |
| CAM plug | T | 8.3…12.9 / −6.0…−0.2 | right edge, front; cable from the front |
| NOR | T | −10.6…−5.2 / 1.45…7.85 | rear quadrant |
| Gyro + 1.8 V LDO | T | gyro −4.4…−1.8 / 2.7…5.8; LDO −1.6…0.4 / 2.7…4.6 | edge to edge: FET groups 4.0 mm, boost 7.2, PA 10.8, pad bulk 5.5 |
| RP2354A + 12 MHz crystal | B | MCU −2.6…4.8 / −1.2…6.2; crystal 5.0…7.1 / 0.3…2.4 | centre; only EFM8s and the gyro above, no EP overlap |
| ESP32 + RX flash + 40 MHz crystal | B | ESP32 2.0…7.4 / −12.6…−7.2; flash 5.6…8.0 / −5.9…−2.5; crystal 7.6…9.3 / −8.6…−7.3 | front; flash and crystal ≥ 2 mm from the PA. Radio SPI to the SX1280 about 10 mm (P2 item) |
| USB SH1.0 vertical | B | 8.3…12.9 / −6.8…0.0 | under the CAM plug, plug from below |
| SX1280 + TCXO + LPF | B | SX1280 −7.3…−2.9 / 1.6…6.0; TCXO −9.35…−7.5 / 0.0…1.4; LPF −8.6…−7.5 / 5.0…5.6 | feed about 5 mm to the antenna hole |
| Boost (TPS61022 + 2520 L + caps) | B | 5.4…9.3 / 4.6…8.6 | in the ESC1/ESC2 quarter (X6S caps), ≥ 5 mm from gyro, TCXO and the RTC6705 loop filter |
| Power entry: shunt, INA186, TVS / pad bulk | B | −8.0…−1.2 / 8.1…10.1; bulk −10.3…−8.2 / 9.8…12.1 | inboard of the battery pads; Kelvin taps; boost VIN after the shunt |
| OSD front end | B | P2 (near the video path, X2SON parts rated 125 °C) | |
| Battery pads B+ / B− | both (THT) | B+ −7.6…−4.6, B− −4.0…−1.0, y 10.4…12.4 | pigtail exits rearward |
| RX antenna hole | through | (−12.3, +6.5) | copper keepout r 1.6 all layers; wire-exit part keepout r 3.0 on the bottom |
| Test pads FCB, GND, RXB, CLK, DIO; ESC C2 pads | B | P2, near the MCU / at each EFM8 | |
| Silk art | B | P2: free patch, may cover tented vias | |

**Edge budget (top, solder pads and plugs).** Usable edge length about 77 mm
(top 17.7, left 20.6, rear 20.6, right 17.7, flanges and the front arc
excluded). Demand: motor pads 16, battery 7, TX1/RX1/5V/GND 5.5, LED/5V/GND 4,
BZ+/BZ− 2.5, CAM/5V/GND 4, CAM plug 5.8, RX hole keepout 3.2, 4 tabs with
keepouts 14, gaps 4: about 66 mm, so it fits in total. Planned: left edge M3,
TX1 RX1 5V GND (y −2…3.5), antenna hole; rear edge B+ B−, BZ+ BZ− (x −0.5…2.0),
M1; right edge CAM plug, one 3-pad group (y 0…4.3), M2. The right edge cannot
also take the second 3-pad group: P2 moves the PA off the top edge to free
x −2.5…+6 there for the LED group, or drops the CAM pads where the plug is
fitted (owner, parity).

RF keepouts:
- **5.8 GHz**: no copper on L1 within 0.15 mm (CPWG gap) of the line except the
  coplanar GND; L2 solid under the whole chain plus 1 mm (rule area
  `RF_VTX_CHAIN`, no non-GND via inside), except the `RF_PAD_CUTOUT` areas (L3
  GND as their reference); via fence ≤ 2.5 mm pitch both sides; no via in the RF
  path; U.FL ground tabs with ≥ 4 vias to L2; no other parts within 1 mm of the
  line on L1.
- **2.4 GHz**: CPWG on L6 over L5 from the LPF to the antenna hole, L5 solid
  under it (rule area `RF_RX_FEED`, no non-GND via); all-layer copper keepout
  r = 1.6 mm around the hole except the feed; no parts within 3 mm of the wire's
  exit on the bottom; Wi-Fi stub keepout 2 x 4 mm on all layers (`WIFI_STUB`).
- **Antenna separation**: VTX antenna (U.FL, front corner, up to the canopy) and
  RX wire (left-rear, rearward or up the canopy) ≥ 20 mm apart, orthogonal where
  possible.
- **Aggressors**: boost ≥ 5 mm from the TCXO and the 2.4 GHz feed; RP2350
  150 MHz x 16 = 2400 MHz and ESP32 40 MHz harmonics sit in band, so V7 runs with
  every aggressor active.

---

## 11. Layout rules specific to this board

- **Commutation loops**: one 100 nF X6S 0201 per half-bridge, on the bottom
  between the N source (GND) and a +BATT via from the P source; loop ≤ 4 mm²
  through 1 mm of board (drawn with dimensions at P2). Target N-FET VDS overshoot
  ≤ 9 V at 18 A turn-off (12 V part).
- **Phase copper**: P drain pad with 8 in-pad vias; bottom phase pour to the N
  drain pad beside it; N source GND vias and P source +BATT vias beside the
  lands; phase to motor pad ≥ 1.2 mm wide on L1 and repeated on L6, joined at the
  wire-anchor holes; solid pad connections (no thermal relief) on FET pads.
- **+BATT path**: battery pad (`+BATT_IN`) → shunt (Kelvin) → `+BATT` on L6 pour
  + L4 plane + L1 pours at the clusters; ≥ 12 power vias at each battery pad; 4
  +BATT vias per phase. Size the trunk for 25 A pack, each channel for 12 A
  bursts. Battery-to-shunt corridor in a rule area before routing.
- **GND**: L2 and L5 unbroken (the only L2 openings are the RF pad cut-outs);
  L1/L6 pours stitched every ≤ 3 mm at the perimeter and around the RF.
- **L3/L4**: L4 is one solid +BATT pour under every L3 route; L3 layer changes
  only within 2 mm of a +BATT capacitor; no Analog, RF, gate, gyro SPI, VTX
  control or video on L3 (§8.2).
- **Gyro isolation** (edge to edge): ≥ 4 mm from the FET groups on either side,
  ≥ 5 mm from the boost IC and inductor, ≥ 10 mm from the PA, ≥ 2 mm from any
  switch node on any layer, and no bulk MLCC carrying ESC ripple (pad bulk, ESC
  local bulk, boost Cin) within 5 mm (MLCC piezo emission couples into MEMS); its
  1.8 V LDO and decoupling on the same side. Sketch v3 meets these; P2 re-checks.
- **Video ground**: camera return enters L2 at the CAM plug; video traces on L1
  over L2 (or L6 over L5) with GND on both sides, never on L3; no ESC return
  current through the front quadrant; 100 pF shunts at video entry points;
  RTC6705 loop filter ≥ 5 mm from the boost.
- **Boost**: Cin at VIN, Cout–SW–GND hot loop < 3 mm, SW copper minimal, MODE
  tied to VOUT (forced PWM), EN via 100 kΩ from VIN with the +5V_USB sense FET,
  VIN from `+BATT` after the shunt, not through ESC copper.
- **Crystals**: 12, 40 and 8 MHz next to their ICs with GND guard, no signal on
  L2 under them; TCXO likewise.
- **Exposed pads, X-ray and heat across the sides**: EFM8, RTC6705, PA, SX1280,
  ESP32, RP2354A, FET and NOR exposed pads soldered with Type VII via-in-pad.
  NextPCB X-rays every QFN/LGA board, and 2D X-ray superimposes both sides: **no
  exposed pad on one side over an exposed pad or LGA land on the other**
  (script check at P2); other cross-side overlaps of bottom-terminated parts are
  allowed and the EQ requests angled or CT X-ray for them. No heat source above
  0.3 W over an 85 °C part on the other side (PA with a 2 mm margin; script check
  at P2).
- **Reflow order and second side**: both sides carry a vertical SH1.0 (about
  4.25 mm tall), plus the 2520 inductor on the bottom; the second-side print and
  placement need a support fixture or pallet: EQ item. Heaviest parts per pad
  area (SH1.0) at about 0.01 g/mm², below the 30 g/in² (0.047 g/mm²)
  second-side guideline (I).
- **0201 on planes**: thermal relief spokes 0.10-0.15 mm, equal copper on both
  pads (tombstoning); vias in 0201 pads per §8.3.
- **Hand-solder pads**: battery and motor pads get a copper neck so a 60-80 W
  iron can heat them; mask-defined edges.

---

## 12. Firmware targets

| Firmware | Plan |
|---|---|
| Betaflight | New board config `OPENAIO_WHOOP` in betaflight/config (manufacturer ID to request; proposal INCU), `FC_TARGET_MCU RP2350A`, derived from the house OPENFC_LITE_MINI_RP2350A target. Requires release ≥ 2026.6.2. Defines: SPI1 gyro (BMI270 or ICM42688P, one per revision), `ENABLE_FB_OSD` with OSD_W/EN/SYNC = GPIO14/15/16, `PIO_LEDSTRIP_INDEX 1`, UART0 = serial RX (CRSF), UART1 = pads, `USE_VTX_MSP`, `USE_FLASH` W25Q128 on SPI0 CS GPIO21, motors on PIO0 GPIO25/24/23/22 = M1-M4, bidirectional DShot, `DEFAULT_ALIGN_BOARD_YAW` ±45 (diamond mount; sign fixed in P4), current scale 500 and VBAT scale measured, beeper inverted. Full config in PINMAP §5 |
| Bluejay | Stock Bluejay ≥ 0.21, layout **BB51 "A"** (no custom layout). Start **`A_X_10_96`** (DT 204 ns covers the CSD25310Q2 worst-case P turn-off of 138-161 ns at high drive, §4.3; 96 kHz halves the bus ripple); `A_X_5_96` only after the extended V2. All are stock builds (Makefile `DEADTIMES` 0 5 10 15 20 25 30 40 50 70 90 120, `PWM_FREQS` 24 48 96, V). Published settings: **temperature protection on at 100 °C** (`DEFAULT_PGM_ENABLE_TEMP_PROT` is 0, i.e. off, in BluejaySettings.asm; options 80-140 °C read from the EFM8 die sensor; V4 correlates the die reading with the FET thermocouple), braking limits per V3c. Flash through Betaflight 4-way passthrough after the production C2 flash (§12.1); C2 pads for recovery |
| AM32 | not applicable (EFM8 MCU) |
| ExpressLRS | Day one: `Unified_ESP32_2400_RX` with the generic layout `Generic 2400 Whoop Rx and VTx.json` (pin-compatible), flashed with `--no-auto-wifi`. Release: a target entry in ExpressLRS/targets that uses that layout plus an overlay with this board's VPD/PWM calibration arrays (the 5950 MHz entry filled from a 5945 MHz measurement, since `VpdFreqArray` 5650/5750/5850/5950 is a code constant), LED index for the single RGB LED, `power_values [13]`, no `radio_dcdc`. ELRS ≥ 4.1. The levels are the five ELRS pushes (§1); no 200 mW level is proposed (it would change the vtxtable for every ELRS VTX board). **Release gates (upstream patches, O6; release blocked until (1)-(5) merge):** (1) fix `LinearInterpVpdSetPointArray()` / `LinearInterpSetPwm()` (missing `break`, and an integer slope that is 0 below 100 counts per 100 MHz); (2) closed-loop 400 mW VPD setpoint (YOLO 2250 counts is above the DET range, so `400` is open-loop full drive today); (3) power index 1 handled as pit (VREF off); (4) pit and disarm power the RTC6705 down (GPIO21, VTX SPI tri-stated, frequency re-sent) or write `POWER_AMP_OFF`; (5) refuse frequencies below 5645 MHz and hold pit (the L band commands the RTC6705 below its VCO range, and `rtc6705SetFrequency()` has no range check, so the PLL rails and an unlocked carrier meets full PA gain). **Further patches (not gating):** (6) thermal derate from the PA NTC on GPIO34, read only in the `hwTimer::isTick` window like the detector (ESP32 erratum 3.11: an ADC1 power-up glitches GPIO36 = radio BUSY); (7) a VTX target keeps its VTX in the last state when Wi-Fi starts automatically (or a hardware key that suppresses auto-start); (8) per-unit VPD calibration: `analogReadMilliVolts()` with the eFuse calibration plus a per-board offset in the ELRS config, and calibration frequencies inside the rated band (for example 5850/5865) as target keys |

### 12.1 Production programming

Blank EFM8BB51F16I parts from Digi-Key carry no BLHeli bootloader, so 4-way
passthrough cannot reach them; a blank ESP32 has to be strapped into download
mode for its first flash; the VDD_SDIO eFuse is burned in the same session.
Fixture: pogo pins on the 8 bottom C2 pads, FCB, RXB and GND, plus the battery
pads, through which the fixture feeds **+BATT at 3.3 V during C2** (EFM8 VIH =
0.7 x 3.3 = 2.31 V against a 3.3 V C2 adapter; at a 4.2-4.35 V cell it would be
2.94-3.05 V). Order:

1. RP2354A: Betaflight UF2 over USB (FCB held low at power-up).
2. ESP32: RXB held low at power-up, then esptool through Betaflight serial
   passthrough (U0RXD/U0TXD on UART0); burn VDD_SDIO = 3.3 V; flash ELRS
   (`--no-auto-wifi`).
3. EFM8 x4: C2 (Silicon Labs adapter or an open C2 programmer) writes the
   BLHeli bootloader and the chosen stock Bluejay build.
4. Verify: Betaflight 4-way passthrough reads all four ESCs; ELRS binds; VTX
   SPI register read.

O17 asks NextPCB whether they offer EFM8 C2 and ESP32 programming; otherwise it
is done at OpenDrone. Fixture and labour are budgeted in the NRE (§15.3).

---

## 13. Silkscreen plan

Per LINEUP-CONVENTIONS B2-B14 and the owner rules: no component silkscreen, no
reference designators, no "Drone" anywhere on a fabricated layer, Tokyo font
embedded, back text mirrored, bold upper-case pad codes of ≤ 3 characters, one
code table shared by schematic pad values, silk, pinout and README. Size (D12):
0.8 mm high, 0.6 wide, 0.13 stroke, the commons standard; it meets NextPCB and
LINEUP B11 and is below JLC's published 1.0 / 0.15 legibility floor (O11
decided by D12; the exception is recorded in §8.1).

| Side | Content |
|---|---|
| Top | pad labels: **TX1 RX1 5V GND**, **LED 5V GND**, **BZ+ BZ−**, **CAM 5V GND**; **M1 M2 M3 M4** at each motor pad group (Betaflight order: M4 front-left, M2 front-right, M3 rear-left, M1 rear-right); **+ −** (2.0 mm) and **1S** at the battery pads; **ANT** at the RX antenna hole; connector names **CAM** and **VTX** with pin-1 marks. No forward arrow unless the owner approves it (O12); the front is marked on `User.Eco2` and in the README |
| Bottom | incutec logo ≥ 6.1 x 1.4 mm; product name **OPEN / AIO / WHOOP** stacked in Tokyo; **REV1** (equal to the board title-block rev `rev1`); test-pad labels **FCB RXB CLK DIO GND**; connector name **USB** with pin-1 mark; ESC C2 pads unlabelled (flashing test points, LINEUP B7; D12), documented in the pinout diagram |
| Off-board | `User.Eco2` note marking the front; mounting-pattern guide on `User.Eco1`; grommet-flange keepouts as rule areas |

---

## 14. Validation plan

| # | Test | Pass / fail |
|---|---|---|
| V1 | 5 V rail: VIN 4.35 → 2.6 V, loads 0.70 A and 1.25 A; then the continuous load the boost holds for 10 min at board temperatures 50/65/80 °C and VIN 2.8/3.0/3.7 V, with the TPS61022 case temperature logged (TJ ≈ Tcase + ΨJT·P); USB + battery: +5V_USB at 5.25 V with the cell at 4.35 V and 3.7 V, cell current, USB current, diode temperature | +5V ≥ 4.85 V at VIN ≥ 2.8 V; ripple ≤ 50 mV p-p; no FC/RX reset to 2.5 V; cold start from 3.0 V; TJ ≤ 125 °C; no current into the cell with USB present; the published BEC table (current per VIN and board temperature, claim ≤ 1.5 A) |
| V2 | ESC dead time: scope P gate, N gate, phase node, per-ESC supply current; builds DT 10/5 at 96 kHz and DT 10 at 48 kHz; VIN 2.5, 3.0 and 4.35 V; FET case heated to 100 °C; all six gate pins of each EFM8; 3 boards x 4 ESCs; the port drive mode recorded (PRTDRV read over C2, or the gate edge against the high- and low-drive VOH) | no shoot-through spike > 2x the steady current; P fully off (Vgs > −0.3 V) before N on, at every corner. `A_X_10_x` is an acceptable outcome |
| V3 | N-FET overshoot at 18 A turn-off; EFM8 VDD peak at the same event | VDS ≤ 9 V; VDD ≤ 5.3 V |
| V3b | Unplug surge: battery pulled at hover throttle with props on the bench, scope on +BATT and on one EFM8 VDD, current probe on the TVS (current, duration, clamp energy), 10 repeats | peak recorded; TVS energy against the SMF5.0A curve (else SMAJ5.0A); if VDD exceeds 5.5 V the README warns against unplugging spinning |
| V3c | EFM8 VDD under regen: fresh 4.35 V pack, full-throttle-to-zero chops and prop-strike braking on all four motors; scope EFM8 VDD at the pin and the DShot pin against EFM8 GND | ≤ 5.3 V including spikes; else Bluejay braking limits, then the 2.2-4.7 Ω VDD resistor |
| V4 | ESC rating protocol: 1S from a real pack (or 3.7 V supply with the pack's resistance), stated; board in a frame under a canopy, motor + prop in propwash (stated airflow), 25 °C; VTX at 25 mW (and a 400 mW run); one channel stepped 2/3/4/5/6 A while others run 2 A, then all four at 2/3/4 A; bursts at 12 A and 18 A started from the measured hover steady state, timed to FET 110 °C | every part inside its rating, measured at the part: hottest FET ≤ 100 °C, EFM8 ≤ 125 °C, RTC6705 case ≤ 80 °C, RP2354A, gyro, SX1280, NOR, RX flash and SE5004L case ≤ 85 °C, worst X6S cap in a loaded cell ≤ 105 °C (thermocouples on each); Bluejay die temperature logged against the FET thermocouple. Publish the curve and the burst durations; same rig on a Matrix II |
| V5 | VTX power: 25/100/max at 5645, 5650, 5750, 5850, 5917, 5945 MHz and the full channel table, on ≥ 5 boards; VIN 2.8/3.0/3.7/4.35 V; PA case temperature logged; synthesiser lock at 5645 and 5945 MHz; 5362 MHz commanded (patched firmware must hold pit; output and frequency recorded on stock); pit leakage at the U.FL; VREF from the reference and Icq; Icq versus VREF 2.0-2.85 V (lever a); fault limit sized on the lowest-gain sample part at 85 °C case and 3.0 V; duty steps between 25 and 100 mW; no-antenna run at the top level | 25 and 100 mW within ±3 dB unit to unit at 5850 MHz (spread published); 100 mW reached at a 3.0 V cell with the PA case at 85 °C on the lowest-gain part; 400 mW reached by that part at the limit; ≥ 20 duty steps between 25 and 100 mW; PA case ≤ 85 °C; frequency error ≤ ±200 kHz; the board survives the no-antenna run; all values published |
| V5b | Video with motors loaded: SNR and PWM sidebands with all four motors at 4-6 A, PA on +BATT and on the +5V selector position | no visible bars; sidebands reported; selector default confirmed |
| V6 | VTX spurious with the BPF, on a spectrum analyser to ≥ 18 GHz | 2nd harmonic ≤ −30 dBm at every channel incl. 5880-5945 MHz; 3f reported; RTC6705 half-frequency leakage (2.8-2.97 GHz) reported |
| V7 | RX: antenna trimmed to resonance by return loss with its flight routing (rearward or up the canopy, ≥ 10 mm from motor leads); sensitivity and desense with every aggressor active (motors at hover and at the rated current, VTX at max, OSD on, blackbox logging, boost loaded, NTC derate reads active) incl. packet loss; Wi-Fi range with the stub | within 2 dB of the SX1280 figure; ≤ 3 dB desense; no packet-loss increase with the derate active; Wi-Fi works at 1 m |
| V8 | Thermal: board at 25/100/max in a real frame under a canopy (derives h); k_PA = PA case − board centre at 25 and 400 mW; RTC6705 case; bench still air and fan; cases of §5.4 incl. "disarmed after leaving pit" and patched pit; FC, RX and RTC6705 rail currents (levers c, e) | matches §5.4 within ±30 %; pit-on-boot verified; PA case and 85 °C parts logged |
| V9 | FC gates on RP2350 (2026.6.2+): bidirectional DShot with Bluejay BB51 at hover and full throttle (30 min) - RPM-filter notches track, no RPMFILTER arming block, decode error rate within upstream's band; ESC-side DShot errors counted at a fresh 4.35 V pack under load (EDT status or command echo) with EFM8 VDD and the DShot high level scoped; 4-way passthrough flash and settings of all 4 ESCs; MSP-VTX from ESP32 ELRS over CRSF; cold boot x 20 with and without the TX on (5 s MSP-VTX window); FB OSD with 2-3 target cameras PAL and NTSC (black and white levels) and with the camera unplugged; SPI NOR blackbox at 2 kHz with the ICM-42688-P at 8 kHz and FB OSD; ELRS flash through serial passthrough; USB only: +BATT voltage, EFM8 brown-out cycling, boost held off; power-up sequence on a scope (FT pads against the EFM8 pull-ups before IOVDD, against 3.63 V) | each passes, else its fallback (C2 pads, AT7456E/G473 respin, SPI NOR on another bus, 10 kΩ DShot series R, a 3.3 V-domain clamp or a DShot-path enable if the FT pads exceed 3.63 V) |
| V10 | Gyro fly-off BMI270 vs ICM-42688-P (5 + 5 boards) | release population has the lower pre-filter noise and no resonance peak in the motor band |
| V11 | Weight | ≤ 3.5 g bare |
| V12 | Crash: BetaFPV protocol, 4 boards, 20 hits | 0 failures, ears included |
| V13 | Outline and holes on Air65 II / Air75 II (25.5) and Meteor65 Pro II / Meteor75 Pro (26.0) frames with BetaFPV balls | fits all four without reaming |

---

## 15. Risks, open questions, sourcing

### 15.1 README design questions

| README question | Status | Answer / what is still open |
|---|---|---|
| VTX part | **proposed-resolved (sourcing risk open)** | RTC6705/RTC6705A stays (no equivalent exists); PA SE5004L-R; authorised RTC6705 stock is zero, so it is a consigned, traceable broker line with incoming tests |
| Power stage | **proposed-resolved (D12)** | P+N direct drive from the EFM8 (I grade) on the cell, CSD25310Q2 + CSD13202Q2, Bluejay layout A starting at `A_X_10_96`. The stage is weaker than the Matrix's (40 vs 34 mΩ); case (b) AGM210MAP is the documented alternative (O5) |
| Electronics rail | **proposed-resolved** | TPS61022 forced-PWM boost at 5.15 V, held off on USB; calculated 1.83 A nominal peak at 2.8 V against a 0.70 A load, published figure measured (V1); PA on the cell; split LDOs |
| Motor connection | **proposed-resolved for rev1; plugs open** | solder pads with wire-anchor holes |
| Antenna | **proposed-resolved** | RX wire monopole at the left-rear edge, trimmed to resonance; VTX U.FL at the front corner; 5.8 GHz BPF; Wi-Fi through a minimal printed stub |

README constraints this spec proposes to change once accepted (README is not
edited by this freeze): mounting 25.5 x 25.5 mm → 25.75 mm pattern with Ø 3.5 mm
grommet holes; "LCSC basic parts preferred" → NextPCB partial turnkey by MPN,
JLCPCB-compatible DFM; receiver "reusing OpenRX Lite" → OpenRX-Lite RF section
with an ESP32 MCU; "VTX dependency" → consigned traceable RTC6705.

### 15.2 Other open questions

| # | Question | Decided by |
|---|---|---|
| O1 | SE5004L output on the cell at 2.8-4.35 V (400 mW at sag) | bench V5 before P4 freeze; the +5V selector position is the fallback |
| O2 | Grommet flange diameter (keepout Ø 5.2 assumed) | calipers on a BetaFPV ball before P2 |
| O3 | BetaFPV SH1.0 USB adapter pinout | measure before P4 |
| O4 | JLC 6L 1.0 mm dielectric build and RF width; finished outer copper with Type VII cap plating and the min track/space at that copper, both fabs | JLC stackup selector, both impedance tools and the EQ before P5 |
| O5 | D12 stage vs case (b) AGM210MAP dual: equal area by budget v3, 34 vs 40 mΩ, model bursts about 2x longer, Matrix-proven at `A_X_5_96`; LCSC-only (4,795), a consigned line like SE5004L, RP2354A and ESP32 | orchestrator / owner (D12 stands until changed) |
| O6 | ELRS patches (§12: (1)-(5) gating, (6)-(8) further) | ELRS PRs; release blocked until (1)-(5) merge |
| O7 | Walsin BPF power handling at 400 mW | ask Walsin; VNA |
| O8 | RP2350 firmware gates (V9) | OpenFC-Lite-Mini + external whoop ESC bench before P5 |
| O9 | Matrix II physical teardown (layer count, HDI or not, BEC part, ball size) | buy one; it also calibrates §9 |
| O10 | 1 oz inner copper (+0.3 g, about −0.15 W at 25 A) | only if V4 misses |
| O11 | Pad-label size | **decided (D12)**: 0.8 / 0.6 / 0.13; JLC silk legibility given up (§8.1) |
| O12 | Forward arrow on silk (LINEUP B9 SHOULD, outside the owner silk list) | owner |
| O13 | ESC C2 pads unlabelled | **decided (D12)**, LINEUP B7 permits flashing test points without labels |
| O14 | Area gate: scope levers of §9.3 (camera plug, USB pogo pads, Wi-Fi, HDI, body size) | P2 placement probe (D12 (5)); owner only if it fails |
| O15 | ESP32-D0WD-V3 at 0.35 mm pitch (NextPCB 0.38 published) | NextPCB EQ now; else ESP32-PICO-V3 |
| O16 | Plated Ø 3.5 holes with a GND annulus (Matrix practice) | P2 with O2 and the ear-survival result of V12 |
| O17 | NextPCB BOM quote by exact MPN on the full BOM (HQ Online / Digi-Key stock per line), EFM8 C2 and ESP32 programming service | P0 close |

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
| ESP32-D0WD-V3 | LCSC stock; a Digi-Key listing exists (S), so the quote may fill it | 15 / 60 |
| GD25Q32EEIGR, SX1280IMLTRT | LCSC-only stock today | 15 / 60 each |
| CSD25310Q2, CSD13202Q2 | if the quote engine misses TI store / Digi-Key stock | 150 / 650 each |
| EFM8BB51F16I-C-QFN20R | only if the quote engine misses Digi-Key's 7,228 | 50 / 220 |
| LCSC-centric lines not yet checked at NextPCB channels: cjiang FTC252012SR68MBCA, Yajingxin TAXM8M4RDBCCT2T (or its 2520 successor), YXC X252012MMB4SI-24, JSCJ CJ17-400001010B20, YXC OW7EL89CENUNFAYLC-52M, XINGLIGHT LEDs, ALLPOWER AP1606, Ralec RTT012401FTH, Walsin RFBPF1608060K98Q1C; W25Q128JV (HQ Online showed 2 pcs of JVPIQ) | O17 decides per line: consign, or swap to a globally stocked equivalent | per BOM quantity + 20 % |
| Everything else | turnkey (HQ Online / Digi-Key / Mouser stock, confirmed by O17) | - |

NextPCB EQ list (one submission): ESP32 0.35 mm pitch (O15); finished outer
copper with Type VII and min track/space at it (O4); angled or CT X-ray for
cross-side overlaps of bottom-terminated parts (§11); second-side support
fixture or pallet for the vertical SH1.0 and the 2520 inductor (§11); panel
(§7); EFM8 C2 and ESP32 programming service (§12.1).

NRE estimate for 10 boards (I, track 07 prices): PCB 6L 1.0 mm with 0.20 mm
vias and Type VII about $220; double-sided assembly $105 plus joint and X-ray
fees (about $50-150); parts about $600 including the broker RTC6705s;
programming fixture (pogo plate for C2, boot pads and battery pads) and labour
about $150-300; freight $50-100: **about $1,150-1,500**. Lead time about 4 weeks
door to door (external parts case).

### 15.4 Risks carried

| Risk | Mitigation |
|---|---|
| Area: the budget is 95.7 % / 97.8 % against the 85 % gate (§9) | P2 placement probe is the proof (D12 (5)); levers with numbers; the owner decides scope only if P2 fails |
| Routing closure with through vias only at about 97 % placement | P2 channel-capacity probe; counted via allowance; HDI put to the owner with numbers if it does not close |
| ESC bursts shorter than the Matrix stage (D12: model 12 A for 1.3-4.9 s vs 3.3-7.4 s) | measured in V4 and published; case (b) documented (O5) |
| RTC6705 fake or remarked parts | traceable source, incoming tests, 10 spares from the same lot |
| Overvoltage on unplug with spinning props: FET gates (±8 V), EFM8, PA, boost, LDOs and 6.3 V MLCCs exceed their ratings above about 5.5-9 V; the TVS keeps only the FET drain-source ratings (Matrix parity) | V3b measures the surge and the TVS energy; README: disarm (props stopped) before unplugging |
| EFM8 VDD near its 5.5 V abs max under regen on a fresh LiHV pack | V3c; braking limits, then the VDD resistor |
| Reversed user-fitted pigtail loses the board | silk + README; factory fit priced at P7 |
| No USB ESD array (house practice) | 27 Ω series resistors; risk accepted |
| RP2350 Betaflight features weeks into a release; DShot decode error band; single core; camera-dependent OSD | V9 gates on existing house hardware before P5; G473 fallback documented; README: bench OSD needs a camera |
| ESP32 strap pins shared with VTX control (GPIO2, GPIO12) | pull-down on GPIO2 (the PA reference EN); GPIO12 held low by the RC and Q1 base path; VDD_SDIO eFuse burned at first flash |
| ESP32 0.35 mm pitch outside the NextPCB limit | EQ (O15); ESP32-PICO-V3 fallback |
| PA heat on the bench and when disarmed after leaving pit (stock ELRS biases the PA) | pit on boot, ELRS patches (O6), README bench-fan rule until merged |
| `400` level open loop until O6 gate 2: board-dependent output up to the PA's compression | fault limit sized for the lowest-gain part; "max (measured)" published per board |

---

## 16. Sources (load-bearing claims)

| Claim | Source | Status |
|---|---|---|
| Matrix II size, holes, thickness, weight, 3-point mount, crash test, pad set, Wi-Fi chip antenna | BetaFPV product page and JSON; photo measurements (01 §2-§3.5, 00) | V |
| Matrix II ESC: 4x EFM8BB51, 12x AGM210MAP, Bluejay A_X_5_96, "12 A / 18 A" | photos + product JSON + Bluejay source (01 §3.2, 03 §2) | V |
| CSD25310Q2: Rds, Qg 3.6/4.7 nC, Vth −0.55/−0.85/−1.10 V, Rg 1.9 Ω, RθJC 4.5 K/W, ±8 V, drain on the exposed pad | TI SLPS459C (local copy `dl/esc03/csd25310q2.pdf`) | V |
| CSD13202Q2 pinout and RθJC 6.4 K/W; AGM210MAP values | TI SLPS313A; AGM210MAP VER2.72 (track 01/03) | V |
| Two FETs in series, P+N conduction model, PA-case term, bursts, heat levers | `calc/thermal_v2.py` (inputs V, model I) | V / I |
| Convection h 30-80 W/m²K (0.042-0.11 W/K) | 03 verification #15; 06 §4 | I |
| EFM8BB51 VDD 1.8-5.5 V (abs max 5.5 V), VOH high/low drive, VIH 0.7 VDD, 50 mA per pin abs max, G/I grades, land 4.0 mm | EFM8BB51 data sheet Rev 1.0, Tables 4.1, 4.2, 4.18, 7.2 | V |
| Bluejay never writes PRTDRV; temperature protection default off | Bluejay 0368d11 `src/` grep, `BluejaySettings.asm` (round-2 review) | V |
| EFM8BB51F16I-C-QFN20R stock | Digi-Key product page, 2026-10-07 | S |
| SE5004L band, VCC, VREF 2.8-2.9 V at IEN 10 mA, ICQ 300 mA, case ≤ 85 °C, gain 30/32 dB, P1dB, detector, ruggedness at −10 dBm into 6:1 | Skyworks SE5004L datasheet 202393B (04 §3) | V |
| RTC6705 Fc 5725-5865 MHz, −40..85 °C, NC pad list, pin 17 AVDD_6.5 | RichWave RTC6705 datasheet V0.2; OpenOSD-X reference (track 04 log) | V |
| TPS61022 limits: L 0.33-2.9 µH, Cout ≥ 20 µF above 1.5 A, valley limit, MODE threshold, VFB 585/600/615 mV, TJ 125 °C recommended, ΨJB 36.7 K/W, pass-through, reverse power flow in forced PWM (§7.4.1), output disconnect in shutdown | TI SLVSDX7D §6.3-6.5, §7.3-7.4, §8.2.2.2 | V |
| FTC252012SR68MBCA / S1R0MBCA parameters; GRM188C80J226ME15D X6S; NCP03XH103F05RL; YXC X252012MMB4SI-24 and KYX K2C120001210 −40..85 °C; TOGNJING 12 MHz −20..70 °C; temperature ratings of the listed parts | LCSC product API, 2026-10-07 | V |
| GRM033C81E104KE14D, GRM033C81A105ME05D, GRM155C80J106ME11D (X6S, −55..105 °C); LP5907SNX-2.85 (±2 %); BLM03PX121SN1D (0.9 A); TXU/LVC1T45 packages | distributor listings (Farnell, Arrow, Future, Digi-Key, TME), 2026-10-07 | S |
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
| Area, outline, key-package floorplan and the Matrix calibration | scratchpad `spec/outline.py`, `spec/budget_v3.py`, `spec/sketch_v3.py` (v2 and v1 budgets kept) | I |
