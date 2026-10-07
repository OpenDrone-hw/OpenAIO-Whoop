# Design spec (proposal, P0)

**Status: proposal for a board that has not been designed.** Nothing below exists
as a schematic or a layout. This file freezes the targets and the part choices
for phase P0 of [BUILD-PLAN.md](BUILD-PLAN.md), so that P1 (project setup) and
P2 (floorplan proof) can start. Every number here is a target, a datasheet
value or a calculation, and each one says which. Where a choice may still move
after the P2 floorplan or a bench test, the gate that decides it is named.

Date 2026-10-07. Inputs: the owner direction and owner rules (2026-10-06), the
research tracks 00-09 (Matrix photo analysis, Matrix deep dive, landscape, ESC,
VTX/OSD, FC/RX/firmware, power/connectors/mechanics, NextPCB DFM, prior art,
OpenDrone reuse map) with their verification logs, the JLCPCB capability page
(read 2026-10-07), live LCSC stock (2026-10-07) and
[LINEUP-CONVENTIONS.md](LINEUP-CONVENTIONS.md). The competitor material is in
[COMPETITION.md](COMPETITION.md).

Status tags used below: **V** read from a primary source, **S** screened
(secondary source, distributor index, research track not re-derived), **I**
inferred (calculation or engineering judgement).

---

## 1. Scope and targets

Scope is fixed by the owner decision of 2026-10-06: **1S only, match the BetaFPV
Matrix 1S 5IN1 II** in envelope and features, beat it on measured ratings,
blackbox, repairability and open documentation, not by adding scope.

| Item | Target (proposal) | Basis |
|---|---|---|
| Input | 1S LiPo / LiHV, 3.0-4.35 V operating; electronics regulate down to 2.5 V cell under sag; 2S not supported ("1S" silk at the battery pads) | owner decision; TPS61022 runs to 0.5 V once started, starts at 1.8 V (V, TI SLVSDX7D) |
| Board body | 26.4 x 26.4 mm square (Matrix II: 26.35 mm, photo-measured) | V (01) |
| Orientation | Diamond mount like the Matrix: flight-forward points at a body corner. Front corner rounded with R 5.8 mm (Matrix: about 2.4 mm set-back on the diagonal) and carries no ear | V (01, photo); I (radius) |
| Ears and holes | 3 ears (left, right, rear corners), ring OD 4.8 mm. Holes **Ø 3.5 mm non-plated cut-outs** on a **25.75 x 25.75 mm square** | Matrix II holes Ø 3.48-3.57 on 26.0 mm (V, 01). 25.75 mm halves the worst offset in both 25.5 mm (Air65 II/Air75 II, Happymodel) and 26.0 mm (Meteor65 Pro II, Meteor75 Pro) frames to 0.18 mm radial, which the rubber balls take up (I, from 06 §3.3) |
| Overall size | 30.55 x 30.55 mm including ears (Matrix II 30.9 mm); outline area 696.6 mm² net of holes | I (outline script, §9) |
| Mounting | 3-point soft mount with BetaFPV-type shock balls; 1.0 mm board matches the Matrix ball groove | V (01, 06 §3.3) |
| Thickness | 1.0 mm finished, 6 copper layers | §8 |
| Weight | **≤ 3.5 g** bare (solder-pad build, no battery pigtail, no antenna). Estimate 3.1-3.4 g: PCB 1.8-1.95 g, parts about 1.0 g, solder 0.12 g. Matrix II solder-required: 3.76 g | I (§6); V (Matrix, 01) |
| ESC | 4 channels, Bluejay on EFM8BB51, P+N direct drive, bidirectional DShot, EDT | §4.3, §4.4 |
| ESC rating to publish | **6 A continuous per channel** (one channel loaded, others ≤ 2 A), **4 A continuous on all four**, **12 A for 10 s, 18 A for 3 s**, all from a stated protocol (§14, V4). Model value 6.5-7 A at high airflow; if V4 measures less, the measured number is what gets published. The Matrix "12 A continuous" measured the same way would be about 5 A | §4.3 loss math |
| VTX | RTC6705 + Skyworks SE5004L PA on the cell, U.FL. Levels **pit / 25 / 100 / 400 mW**, 48 channels incl. Raceband, controlled by the ELRS receiver (MSP-VTX over CRSF). 25 and 100 mW closed-loop calibrated per frequency; 400 mW is maximum drive, capped in hardware and published as measured. 200 mW needs an ELRS change (open item) | §4.8 |
| OSD | Betaflight PIO framebuffer OSD on the RP2354A (no OSD chip) | §4.8 |
| RX | Serial ExpressLRS 2.4 GHz, ESP32-D0WD-V3 + SX1280, +13 dBm, no PA/LNA (Matrix parity), insulated wire monopole | §4.7 |
| FC | RP2354A, Betaflight ≥ 2026.6.2, one gyro per revision published in the target (no lottery) | §4.5, §4.6 |
| Blackbox | 16 MB SPI NOR (W25Q128JVPIM), SPI0 | §4.9 |
| 5 V BEC | 5 V, ≥ 2.2 A guaranteed at 2.8 V in (datasheet-limited); design load 0.69 A | §4.2, §5 |
| Current / voltage sense | 0.5 mΩ shunt + INA186A3 (50 mV/A, `ibata_scale` 500), VBAT 1:1 divider; scales measured and set in the target | §4.1 |
| Connectors | BT2.0 pigtail on two plated holes; 12 motor solder pads with plated wire-anchor holes; SH1.0 4-pin vertical USB (BetaFPV adapter style); SH1.0 3-pin vertical camera plug plus CAM/5V/GND pads; U.FL for the VTX; RX antenna wire hole; 2 free UARTs on pads (Matrix II exposes 1) | §4.10 |
| Fab / assembly | NextPCB turnkey (partial turnkey with consigned lines), DFM-compatible with JLCPCB as well; through vias only | §8, §15 |

---

## 2. What to optimise, ranked

| Rank | Goal | Metric | Target | Bench measurement |
|---|---|---|---|---|
| 1 | Electronics rail that survives sag (no video blackout, no FC/RX brown-out) | +5V at full design load (0.69 A, and 1.25 A with the PA moved to 5 V) while the input is swept 4.35 → 2.6 V | ≥ 4.85 V at VIN ≥ 2.8 V; ripple ≤ 50 mV p-p (forced PWM, 1 MHz); no reset of FC or RX down to VIN 2.5 V | bench supply + electronic load, scope at the camera pad |
| 2 | Honest, better ESC rating | continuous A per channel at hottest package ≤ 100 °C (protocol §14, V4); hot P+N path resistance | ≥ 6 A per channel (Matrix II same protocol: about 5 A modelled); path 23 mΩ hot vs 34 mΩ for the Matrix's AGM210MAP | thermocouple / IR on the hottest FET; same rig on a Matrix II |
| 3 | Weight | grams on a 0.01 g scale | ≤ 3.5 g bare (Matrix 3.76 g) | scale, first 5 prototypes |
| 4 | Measured VTX power and clean spectrum | output per channel at 25/100/400 mW at 3.7 V; 2nd harmonic | 25 and 100 mW within ±1.5 dB at 5650/5750/5850/5917 MHz; 2f ≤ −30 dBm (EN 300 440 limit) | tinySA Ultra + 30 dB attenuator; published table |
| 5 | RX link | conducted sensitivity at 500 Hz packet rate; desense with VTX at 400 mW | within 2 dB of the SX1280 datasheet figure; ≤ 3 dB desense | ELRS link stats + attenuator chain |
| 6 | Gyro noise | hover pre-filter gyro noise from blackbox | ≤ the Matrix II on the same frame and motors | 60 s hover logs, FFT |
| 7 | Crash survival | BetaFPV wall test (5 m run, 20 hits) | 0 of 4 boards damaged (Matrix II on Air75 II: 2 of 4) | BetaFPV protocol [01] |
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
| ESC | 4x BB51, 12x AGM210MAP P+N, "12 A cont / 18 A peak" | 4x BB51, 12x SiA517DJ, 5 A design target | 4x BB51, 12x CSD25402Q3A (P) + 12x CSD13202Q2 (N), 6 A cont measured |
| RX | ESP8285 + SX1281 onboard | external | ESP32 + SX1280 onboard, ELRS 4.x mainline |
| VTX | RTC6705 + RFPA5542 (EOL) + MM32F003, 25-400 mW | RTC6705 + RTC6659-class PA, 25/100/250/MAX | RTC6705 + SE5004L, no VTX MCU (ELRS drives it), pit/25/100/400 |
| Blackbox | 16 MB | 16 MB | 16 MB |
| USB | SH1.0 vertical + adapter | 4 pogo pads + clip-on adapter | SH1.0 vertical (BetaFPV adapter compatible, pinout to be measured) |
| Openness | none | page only | schematic, layout, BOM, measured ratings |

---

## 4. Architecture per block

Each block gives the options weighed, the decision, the key parts and the
numbers. Stock figures are LCSC live reads on 2026-10-07 unless marked; the P0
gate is "≥ 5x the 50-board quantity" (250 for a part used once per board).
Parts already manufactured on an OpenDrone board are marked **[PU]**
(PARTS-USED.md).

### 4.1 Input and protection

| Option considered | Verdict |
|---|---|
| Reverse-polarity FET | No: BT2.0 is keyed; costs a 3x3 FET and loss in a 25 A path. Matrix has none |
| TVS at the pads | **Yes**: the 12 V N-FETs and 6.3 V MLCCs need a clamp for hot-unplug with spinning props. It cannot protect the EFM8 (5.5 V abs max); the per-MCU RC does that (§4.4) |
| Bulk at the pads | 2x 22 µF 0603 16 V (about 30 µF effective at 4 V). With 8x 22 µF 0402 at the ESCs the board has about 100 µF effective, which shares the 48-96 kHz ripple with the 30-60 mΩ battery path (03 §11) |

| Function | Primary | Fallback |
|---|---|---|
| TVS | Littelfuse **SMF5.0A**, SOD-123FL, C151296, 33,500 (V) | Vishay SMF5.0A-E3-08, same package (S) |
| Pad bulk | Samsung **CL10A226MO7JZNC** 22 µF 16 V 0603, C2762594, 457,860 [PU] | Murata GRM188R61C226ME15 (S) |
| Shunt | Stackpole **HCS1206FTL500**, 0.5 mΩ 2 W 1206, C346511, 1,717 | Yezhan ASR-S-3-0.2F 0.2 mΩ 2512, C695806, 1,020 [PU] (larger land, scale 200) |
| Current amp | TI **INA186A3IDCKR**, SC-70-6, gain 100, C2058245, 5,715 [PU] | TI INA186A3 DSBGA (YFD) (S, −4.8 mm²) |
| VBAT divider | 2x 10 kΩ 0201 (Yageo RC0201FR-0710KL, C106225 [PU]) + 100 nF | - |

Numbers: 0.5 mΩ x 100 V/V = 50 mV/A, full scale 66 A at 3.3 V, Betaflight
`ibata_scale` 500 (0.1 mV/A units). Shunt loss 0.2 W at 20 A, 0.31 W at 25 A.
VBAT 10k/10k puts 4.35 V at 2.18 V on the ADC (RP2354A ADC range 3.3 V).
Current sense is high side with Kelvin taps from the shunt pads and the matched
input RC network of the OpenESC Rev3.2 / OpenAIO root sheet (reused, values
moved to 0201).

### 4.2 Power tree

```
BT2.0 -> +BATT pads -- SMF5.0A, 2x22u -- shunt (Kelvin -> INA186) -- +BATT plane
  +BATT -> 4x ESC power stages; 4x EFM8 VDD (10R + 1u + 100n each)
  +BATT -> SE5004L PA VCC (ferrite + 10u)   [0R option to +5V on the bench]
  +BATT -> TPS61022 boost, MODE = forced PWM, 1 MHz -> +5V (2x 22u 0603)
             +5V -> ferrite + 10u -> CAM 5V (plug + pad)
             +5V -> LED-strip 5V, buzzer +, user 5V pads
             +5V -> TLV75533  -> +3V3      (RP2354A, NOR, OSD front end, INA186, LEDs)
                                  +3V3 -> TPS7A2018 -> +1V8 (gyro analog)
             +5V -> LP5912-3.3 -> +3V3_RX  (ESP32, SX1280, RGB LED)
             +5V -> TPS7A2033  -> +3V3_VTX (RTC6705 only, 7 µVrms)
  VBUS (SH1.0 USB) -> RB161QS-40 Schottky -> +5V   (bench: FC, RX, RTC6705, camera; PA and ESCs unpowered)
  RP2354A internal core SMPS -> +1V1 (3.3 µH 2016, per RPi guide)
```

Options weighed:

| Question | Options | Decision | Why (numbers) |
|---|---|---|---|
| 5 V converter | TPS61023 (SOT-563, 2.7 A valley, auto-PFM), TPS61022 (2x2, 6.5 A valley, forced-PWM pin), TPS63070 buck-boost (2S only), SY7088 (3 A peak) | **TPS61022RWUR + 0.47 µH 2520** | Forced PWM keeps the 1 MHz ripple fixed and out of the PFM low-frequency range that shows as video bars. Guaranteed 2.21 A at 2.8 V and 2.37 A at 3.0 V with the inductor at 80 % of Isat, against 0.69 A design load (3.4x) and 1.25 A if the PA is moved to 5 V (1.9x). TPS61023 gives 1.83 A at 3.0 V (I) and has no forced PWM |
| PA supply | 5 V boost + load switch (track 06 R6) vs cell (track 04) | **Cell (+BATT)**, 0 Ω option to +5V | SE5004L is rated 3.0-5.5 V; takes 0.3-0.55 A off the boost; EN low = 0.5 µA so no load switch; on USB only the PA has no supply and cannot cook. Bench test V5 decides (§14) |
| Diode-OR | two Schottkys into an LDO bus (OpenFC pattern) vs one Schottky VBUS → +5V | **One Schottky**, VBUS → +5V | TPS61022 has true output disconnect, so +5V can be back-fed from USB without reaching the cell; saves a diode drop on the main path |
| 3.3 V rails | one LDO for all (about 0.29 A: 0.49 W, +82 K in X2SON) vs split | **Split into 3 + gyro LDO** | Each LDO ≤ 0.17 W; the RTC6705 VCO gets its own 7 µVrms rail; RX Wi-Fi bursts (bench only, up to 0.3 A) go to a WSON-6 part with a better thermal path |
| ESC MCU supply | VBAT direct vs 3.3/5 V rail | **VBAT direct** through 10 Ω + 1 µF + 100 nF | EFM8BB51 VDD 1.8-5.5 V (V, datasheet); gate drive = cell voltage; motors survive a BEC fault |

Parts:

| Function | Primary (MPN, maker, package, stock) | Fallback | Reuse |
|---|---|---|---|
| Boost | TI **TPS61022RWUR**, VQFN-HR-7 2x2, C915088, 857 | TI TPS61023DRLR, SOT-563, C919459, 53,320 (new land, 1.6 A at 2.8 V) | new (power sheet rewritten; bucks of OpenFC `power` do not run at 1S) |
| Boost inductor | cjiang **FTC252012SR47MBCA**, 0.47 µH, 2.5x2.0x1.2, Isat 7.5 A, 13 mΩ, C5832368, 108,420 | cjiang FTC201610SR47MBCA, 2016, Isat 6.3 A (S, C5832340) | new |
| Boost caps | 2x CL10A226MO7JZNC 0603 out, CL05A106MQ5NUNC 10 µF 0402 in [PU] | - | PU |
| +3V3 LDO (FC) | TI **TLV75533PDQNR**, X2SON-4 1x1, C2861882, 2,025 [PU] | TI LP5912-3.3DRVR, WSON-6 2x2, C524780, 23,490 [PU] | OpenRX-Lite part |
| +3V3_RX LDO | TI **LP5912-3.3DRVR**, WSON-6 2x2, C524780, 23,490 [PU] | TLV75533PDQNR [PU] | OpenFC `power` back end |
| +3V3_VTX LDO | TI **TPS7A2033PDBVR**, SOT-23-5, C2862740, 204,055 | TI TPS7A2033PDQNR, X2SON-4 1x1, C2871641, 0 today (HQ Online listed): −7.9 mm² when it returns | OpenVTX/04 choice |
| +1V8 gyro LDO | TI **TPS7A2018PDQNRM3**, X2SON-4 1x1, C36996449, 8,090 | TI LP5912-1.8DRVR, WSON-6 2x2, C2876234, 728 [PU] | OpenFC `imu` rule (separate 1.8 V) |
| USB OR diode | ROHM **RB161QS-40T18R**, 1 A 40 V, SMD1006, C2837790, 52,250 | Nexperia PMEG2010AEH, SOD-123F, C110921, 25,360 | new |
| RP2354A core inductor | Abracon **AOTA-B201610S3R3-101-T**, 3.3 µH 2016, C42411119, 625 [PU] | external 1.1 V LDO with the SMPS bypassed (RPi guide option); MPN chosen in P3 | OpenFC `rp2350a` |
| Ferrites (PA, camera) | Murata **BLM15PX221SN1D**, 0402, 1.4 A, 100 mΩ, C160973, 714,586 | Murata BLM15PX221SH1D, C7509803 (S) | new |

### 4.3 ESC power stage

| Topology | Area (12 phases + 4 MCUs) | Hot path at Vgs 3.6 V | Verdict |
|---|---|---|---|
| P+N dual per phase, direct GPIO (Matrix: AGM210MAP) | 147 mm² FETs | 34.1 mΩ | parity only; AGM210MAP is LCSC-only (not Digi-Key, not HQ Online) |
| **Discrete P 3.3x3.3 + N 2x2 per phase, direct GPIO** | 205 mm² FETs | **23.1 mΩ** (CSD25402Q3A) / 19.8 mΩ (CSD25404Q3) | **chosen** |
| Discrete P 2x2 + N 2x2 (CSD25310Q2 + CSD13202Q2) | 116 mm² | 40.2 mΩ | area fallback (−94 mm² top), about 5 A rating |
| N+N + gate driver | +4-15 mm²/channel + boost rail | 11 mΩ (needs EG2134, 0 stock) / 22-30 mΩ (DRV8328) | no: no stocked 1S driver gains anything, adds a rail whose failure drops all four motors (03 §5c) |
| Level-shifted P (2S style) | +46 mm² | worse, DT 0.6-1.4 µs | no: 1S only |

Decision: per phase one TI **CSD25402Q3A** P-FET (high side, source on +BATT,
gate straight from the EFM8 COM pin, active low) and one TI **CSD13202Q2** N-FET
(low side, PWM pin, active high). Bluejay BB51 layout A, unchanged upstream
(§12). The P-FET sits on the top side, the N-FET directly under its drain on the
bottom; the two drains are joined by 8 filled-and-capped 0.35/0.15 vias (phase
node 0.23 mΩ, 33 mW at 12 A).

Why CSD25402Q3A over the lower-Rds CSD25404Q3 as primary: 16,466 vs 3,297 at
LCSC (the gate needs 3,000 for 50 boards), $0.59 vs $1.09, faster P turn-off
(RC 90/171 ns vs 97/192 ns typ/worst pin) and a better Cdv/dt ratio (Crss/Ciss
0.028 vs 0.032), for a 17 % higher conduction loss. Both beat the Matrix stage
by a wide margin (03 §4, model re-run here).

| Part | Primary | Fallback |
|---|---|---|
| P-FET | TI **CSD25402Q3A**, −20 V / ±12 V, 7.7 / 13.3 mΩ typ at 4.5 / 2.5 V, VSONP-8 3.3x3.3, C111356, 16,466 (TI store 136,315, track 03) | TI CSD25404Q3, 5.5 / 10.1 mΩ, VSON-CLIP 3.3x3.3, C2865523, 3,297. Land patterns (DNH vs DQG) differ slightly: checked in P3, the footprint is drawn to accept both or the fallback becomes a footprint swap |
| N-FET | TI **CSD13202Q2**, 12 V / ±8 V, 7.5 / 9.1 mΩ typ at 4.5 / 2.5 V, SON-6 2x2, LCSC C187839 2,605; Digi-Key 8,235, TI store 294,349 (track 03, 2026-10-06) | AOS AON2408, 20 V, DFN 2x2 (S, LCSC index 3,512); land check in P3; about +25 % N loss |
| Leg cap | Murata GRM033R61E104KE14D 100 nF 25 V 0201, C76939 [PU], one per half-bridge | - |
| Local bulk | Samsung CL05A226MQ5QUNC 22 µF 6.3 V 0402, C105226 [PU], 2 per ESC | - |

**Loss math** (I, model of track 03 re-run: layout A conducts through **two FETs
in series** at every instant, the high-side P of the driven phase plus either the
PWM'd low-side N or, in the off-time, the damping P; conduction is therefore
I²·(Rp + Rn) at full duty; dead time adds 2·DT·f·0.8 V·I through body diodes;
hard switching is on the N only):

| Phase current | Conduction (23.1 mΩ hot) | Dead time (DT 10 = 204 ns, 96 kHz) | N switching | **Per motor** | Per motor at 48 kHz | Matrix AGM210MAP stage, same model |
|---|---|---|---|---|---|---|
| 1 A (hover) | 0.02 W | 0.03 W | 0.01 W | 0.06 W | 0.04 W | - |
| 4 A | 0.37 | 0.13 | 0.04 | 0.53 W | 0.45 W | - |
| **6 A (rating)** | 0.83 | 0.19 | 0.05 | **1.07 W** | 0.95 W | 1.37 W |
| 12 A (10 s) | 3.33 | 0.38 | 0.11 | **3.81 W** | 3.57 W | 5.20 W |
| 18 A (3 s, Vgs 3.0 V, 26.1 mΩ) | 8.46 | 0.56 | 0.16 | **9.18 W** | 8.82 W | - |

Per FET (each conducts one third of the electrical cycle; P carries the
dead-time share): at 6 A, P 0.21 W and N 0.16 W; at 12 A, P 0.72 W and N 0.56 W;
at 18 A, P about 1.4 W and N 1.3 W. Junction-to-case rise stays under 2 K
(RθJC 1.3-1.9 K/W, datasheets), so **board temperature, not the FET, sets the
rating**.

Thermal estimate (I, 03 §7 with its verification corrections): one motor
quarter has about 0.65 J/K; lateral spreading about 0.055 W/K over all layers;
the whole board sheds 0.07-0.14 W/K in propwash (h 50-100 W/m²K over 13.9 cm²).

| Case | Heat | Estimate | Limit |
|---|---|---|---|
| 6 A continuous, one channel, others 2 A, rest of board 3.8 W (hover, VTX 400 mW) | 1.07 + 3 x 0.2 + 3.8 = 5.5 W | board +39-79 K over ambient, channel hot spot +19 K above the board: ≤ 100 °C at 25 °C ambient only at the upper h; **so the published 6 A is conditional on the measured protocol** | 100 °C hottest package |
| 4 A on all four continuous | 4 x 0.53 + 3.8 = 5.9 W | +42-84 K | same |
| 12 A for 10 s from 40 °C | 3.81 W into 0.65 J/K | ≤ +59 K adiabatic upper bound: ≤ 99 °C | 110 °C |
| 18 A for 3 s from 40 °C | 9.18 W | ≤ +42 K: ≤ 82 °C | 110 °C |

The battery path is the practical limit before the ESC: BT2.0 is rated 9 A
continuous / 15 A burst (V, BetaFPV) and a 300 mAh 75C pack 22.5 A (marketing).
Four channels at 6 A would be 24 A of pack current; the rating is per channel.

### 4.4 ESC MCU and firmware

| Option | Verdict |
|---|---|
| **EFM8BB51F16G + Bluejay** | chosen: runs from the cell (VDD 1.8-5.5 V), QFN-20 3x3 (10.9 mm² placed), proven 1S at `A_X_5_96` on the Matrix/Air/CrazybeeG473 |
| AT32F421 + AM32 | no: VDD 2.4-3.6 V, needs a rail and a level shift for the P gate; QFN-28 4x4 (+7-8 mm²/channel) |
| EFM8BB21 | no: VDD max 3.6 V operating, cannot sit on a 4.35 V cell |

| Part | Primary | Fallback |
|---|---|---|
| ESC MCU | Silicon Labs **EFM8BB51F16G-C-QFN20R**, QFN-20 3x3, C6547511, 31,643 (Digi-Key 2,500, 24 wk) | no drop-in part exists (BB21 cannot run on the cell); fallback is the second channel, Digi-Key |

Per channel: VDD 10 Ω (C106226 is 0 today; any 10 Ω 0201 1 % from Yageo/UniOhm
in P3) + 1 µF (Murata GRM033R61A105ME44D, C76935 [PU]) + 100 nF; DShot series
2.4 kΩ (Ralec RTT012401FTH, C166281 [PU]) to limit injection into an unpowered
EFM8 when only USB is connected (VDD + 0.3 V abs max on I/O, 06 §1.9); BEMF
network of 6x 0201 (3 series to the comparator mux pins, 3 to the virtual
neutral, values from tinyPEPPER and checked against layout A in P4); C2D and
C2CK test pads for recovery flashing. Layout A pin use (V, Bluejay
`src/Layouts/BB51/A.inc`): P0.1 B_Mux, P0.2 C_Mux, P0.3 A_Mux, P0.4 V_Mux (neutral),
P0.5 DShot; P1.0 A_Pwm (N gate), P1.1 A_Com (P gate, active low), P1.2 B_Pwm,
P1.3 B_Com, P1.4 C_Pwm, P1.5 C_Com; P2.0 C2D. Unused P0.0, P0.6, P0.7, P1.6.
No gate resistors: the GPIO (≤ 60 Ω, datasheet) is the gate resistor.

### 4.5 FC MCU

| Criterion | RP2354A (house, OpenFC-Lite-Mini) | STM32G473CEU6 (Matrix, UD 4IN1) |
|---|---|---|
| Placed area with OSD | 95 mm² (PIO OSD front end 8 mm²) | 113 mm² (AT7456ELAH) |
| OSD current | about 5 mA front end | +43 mA typ AT7456E |
| OSD part stock | n/a | AT7456ELAH LGA-16: 78 at LCSC (fails the gate); HTSSOP-28 adds about 30 mm² |
| Betaflight maturity | core feature set in a release only since 2026.6.2 (2026-09-16); house maintainer contributes upstream | mature (BETAFPVG473_V2) |
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

`rp2350a` sheet reuse, changes: remove USB-C, CC and I2C pull-ups; USB D+/D−
(27-30 Ω series) to the SH1.0 connector; VBAT divider 100k/10k → 10k/10k; GPIO
map below; SWD to pads; boot button replaced by a BOOT pad (QSPI_SS) next to a
GND pad.

**Draft FC pin map (RP2354A, QFN-60)**

| GPIO | Function | Peripheral |
|---|---|---|
| 0 / 1 | CRSF to ESP32 (ELRS RX; also serial passthrough) | UART0 TX/RX |
| 2 / 3 | user UART 2 pads TX2 / RX2 | PIOUART0 on PIO1 |
| 4 / 5 | user UART 1 pads TX1 / RX1 | UART1 TX/RX |
| 6 | gyro pin 9 (CLKIN for TDK; INT2 on BMI270, unused) | PWM slice 3A (32 kHz CLKIN) |
| 7 | LED0 green (status) | GPIO |
| 8 | LED strip (via level-shift FET, as OpenFC) | PIO1 (WS2812) |
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

Conflict check (I): PIO0 holds DShot (29 of 32 instructions, 4 state machines).
PIO1 holds one PIOUART (RX 9 + TX 10 instructions, 2 SMs) and the WS2812 program
(4 instructions, 1 SM): 23 instructions, 3 SMs. PIO2 holds the FB OSD (31
instructions). So only one PIOUART fits next to the LED strip, which is why the
second user UART is the PIO one. The LED strip must be moved to PIO1 with
`PIO_LEDSTRIP_INDEX` (upstream defaults it to PIO2; untested override, 04 §5.2).
PWM slices: 0B (beeper) and 3A (CLKIN) are the only PWM users; GPIO 0/1 and 7
share those slices but are muxed to UART/GPIO, so no conflict. DMA: DShot 4-8,
SPI1 2, SPI0 2, OSD 2, ADC 1: ≤ 15 of 16 channels.

### 4.6 Gyro

| Candidate | Stock | Note |
|---|---|---|
| **Bosch BMI270** | C2836813, 7,748, $2.66 [PU] | house current part; widely flown on 1S whoops; Betaflight 3.2 kHz ODR; house IMU study rates it "higher risk" for MEMS resonance on the 20x20 sister board |
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
| **ESP32-D0WD-V3 + 4 MB NOR + SX1280** | about 88 mm² | ELRS `devVTXSPI` + `MSPVTX` on the shipping code path; pin-compatible with ELRS layout `Generic 2400 Whoop Rx and VTx.json` (separate VTX SPI bus, like every upstream VTX layout) | 581 / 1,129 / 767 | **chosen** |
| ESP32-PICO-D4 (SiP, crystal + flash inside) + SX1280 | about 101 mm² | same | 2,272 | fallback |
| SPI ELRS on the FC | 37 mm² | none | - | not available on RP2350; locks ELRS v3/v4 to the BF build |
| ESP32-S3FH4R2 | 7x7 + crystal | same | 17 | no stock |

**Decision:** ESP32-D0WD-V3 with an external GD25Q32 flash and the CJ17 40 MHz
crystal, SX1280 radio. This deletes the VTX MCU (the Matrix's MM32F003), uses no
FC UART for the VTX and needs no Betaflight driver. The FC sees an MSP VTX over
CRSF (`USE_VTX_MSP`, in RP2350 releases from 2026.6.2). Pins follow
`Generic 2400 Whoop Rx and VTx.json` (V, ExpressLRS/targets 42ed776): CRSF on
ESP32 GPIO1/3, radio SCK/MOSI/MISO/NSS/RST 25/32/33/27/26, BUSY 36, DIO1 37,
RGB LED 22, VTX NSS/MOSI/MISO/SCK 19/18/23/5, PA bias PWM 12, PA detector 4,
PA enable (vtx_amp_vref) 2, button/boot 0. So the board can be flashed with the
existing generic target on day one; our own target adds only a calibration
overlay. Strap care: GPIO12 must read low at reset (3.3 V flash) and GPIO2 low
(pull-down), checked in P4.

The RF section is the OpenRX-Lite / OpenAIO `rx_esp32c3_sx1281` circuit reused
(TCXO, filter, match, LDO-mode radio), with these changes: MCU swap; SX1281 →
SX1280 (pin-compatible, same ELRS driver, stock); 15 µH DC-DC inductor deleted
(the ELRS layout has no `radio_dcdc`, so the DC-DC is never enabled); ceramic and
Wi-Fi chip antennas deleted (flash through Betaflight serial passthrough or the
UART/BOOT pads); wire-antenna plated hole instead; **fix the sheet defect: SX1281/
SX1280 pin 5 is GND and is unconnected on both sibling sheets** (09 verification).
Sheet name `rx_esp32_sx1280` (new file, since the MCU changed).

| Part | Primary | Fallback |
|---|---|---|
| RX MCU | Espressif **ESP32-D0WD-V3**, QFN-48 5x5, C967021, 581 | Espressif ESP32-PICO-D4, QFN-48 7x7, C193707, 2,272 (crystal and flash inside; +13 mm²) |
| RX flash | GigaDevice **GD25Q32EEIGR**, 32 Mbit, USON-8 2x3, C2973794, 1,129 | Winbond W25Q32JVUUIQ, USON-8 3x4, C2999380, 3,575 |
| 40 MHz crystal | JSCJ **CJ17-400001010B20**, 1612, C2875272, 13,110 [PU] | - |
| Radio | Semtech **SX1280IMLTRT**, QFN-24 4x4, C125969, 767 | Semtech SX1281IMLTRT, C2151551, 0 at LCSC, 146 HQ Online [PU] |
| 52 MHz TCXO | YXC **OW7EL89CENUNFAYLC-52M**, 2016, C22434896, 5,975 [PU] | 52 MHz 2016 crystal per the Matrix (MPN in P3) |
| 2.4 GHz LPF | TDK **DEA102700LT-6307A2**, 1005, C574024, 3,810 [PU] | Johanson 2450FM07D0034T, C2651081, 0 today [PU] (re-match) |
| RGB LED | XINGLIGHT **XL-1010RGBC-WS2812B**, 1x1 mm, C5349953, 364,820 [PU] | - |

Numbers: +13 dBm, no PA/LNA (Matrix ELRS layout `Generic 2400`,
`power_values [13]`, V). Radio in LDO mode costs about +6 mA (20 mW). ESP32 ELRS
load about 0.07 A; rail average 0.10 A, 0.15 A peak in flight.

### 4.8 VTX and OSD

| Question | Options | Decision |
|---|---|---|
| Synthesiser | RTC6705/RTC6705A (QFN-40 6x6); MAX2871/LMX2572 discrete (9-10 mm square, unproven for video) | **RTC6705 or RTC6705A**; no alternative exists (04 §2.4) |
| PA | RFPA5542 (Matrix, EOL 2023, 5 V only), SKY85743-21 (4.2-5.5 V, LGA 3x5), SE5004L (3.0-5.5 V), QPA9501 (124 pcs), TQP5525 (25 pcs) | **SE5004L-R** on the cell; QFN-20 4x4 footprint shared by six PAs (04 §3.3) |
| Control | separate VTX MCU (Matrix MM32F003), Betaflight RTC6705 driver (2 levels, `#undef` on RP2350), FC-integrated new driver, ELRS RX MCU | **ELRS ESP32 `devVTXSPI` + `MSPVTX`** (§4.7) |
| OSD | AT7456E + 27 MHz crystal (40 mm², 50 mA, LGA 78 pcs); PIO FB OSD | **PIO FB OSD** (OpenFC `osd` sheet minus the COS8051 buffer) |
| Harmonic filter | none (Matrix) vs LTCC BPF | **Walsin 1608 BPF**; guarantees 20 dB at 10.3-11.7 GHz, 12 dB at 7.25-7.8 GHz (V, Walsin PI V01); power handling must be confirmed with Walsin |
| Connector | U.FL, MHF4, soldered coax | **U.FL** (what whoop antennas ship with) |

Chain: camera CVBS → 75 Ω → SN74LVC1G3157 (camera / OSD level) → RTC6705 video
network (OpenOSD-X reference values) → RTC6705 PAOUT1 (+2 dBm) → 10 pF DC block
→ 50 Ω CPWG < 5 mm → SE5004L → match → BPF → U.FL. RTC6705 on +3V3_VTX. PA drive
level: ESP32 PWM → RC → small-signal transistor follower → RTC6705 PAOUT1 choke
supply (OpenOSD-X pattern; polarity set by the ELRS calibration counts, as on the
Happymodel target). PA pin 5: GPIO2 through about 39 Ω with a 10 kΩ pull-down
(SE5004L VREF 2.80-2.90 V at about 10 mA; 0 Ω for logic-enable PAs). Detector:
PA DET → 1 kΩ / 100 pF → ESP32 GPIO4 (SE5004L DET 0.325-1.0 V fits the ELRS
0-1 V window). The 0 Ω pair selects PA VCC = +BATT (fitted) or +5V. RTC6705 NC
pads (1-4, 12-18, 36-37; 13 of 40 per the OpenOSD-X reference) may be removed
from the land if P5 needs the escape channels; the EP is never touched.

| Part | Primary | Fallback |
|---|---|---|
| Synthesiser | RichWave **RTC6705** (or RTC6705A), QFN-40 6x6. **0 authorised stock** (LCSC 0, HQ Online 0, Digi-Key none); brokers: Win Source 30,000 at $7.82-11.73 (findchips, 2026-10-06). **Fails the stock gate; consigned with traceability (§15)** | none exists |
| 8 MHz reference | Yajingxin **TAXM8M4RDBCCT2T**, 3225, 10 pF, ±10 ppm, C400090, 169,935 | YXC X322508MSB4SI, 3225 (S) |
| PA | Skyworks **SE5004L-R**, QFN-20 4x4, 3.0-5.5 V, C210263, 1,339 (HQ Online 0; Digi-Key 21 wk) | Qorvo QPA9501TR13, same footprint, C2911573, 124 (prototype only; fails the 50-board gate); Skyworks SKY85743-21, LGA-24 3x5, C5348950, 568 (5 V, new footprint) |
| BPF | Walsin **RFBPF1608060K98Q1C**, 5150-5950 MHz, 1608, C2442150, 12,780 | TDK DEA165538BT-2263A1-H, C2835388, 3,975 (clips 5945 MHz) |
| U.FL | Hirose **U.FL-R-SMT-1(80)**, C88374, 65,975 [PU] | - |
| PAOUT1 choke | Murata **LQP03TN4N7H02D** 4.7 nH 0201, C86126, 37,747 | - |
| Drive follower | Nexperia BC847BMB (NPN, DFN1006B-3) (S, MPN confirmed in P3) | any DFN1006 NPN with hFE ≥ 200 |
| OSD switch | TI **SN74LVC1G3157DTBR**, X2SON-6, C2673087, 1,545 [PU] | - |
| OSD sync comparator | TI **TLV7031DPWR**, X2SON-5, C2876045, 6,241 [PU] | - |
| OSD clamp diode | Diodes **SDM02U30LP3-7B**, DFN0603, C151629, 16,750 [PU] | - |

`osd` sheet reuse, changes: drop COS8051 and its 3 resistors (the switch output
drives the RTC6705 network, about 1.47 kΩ, not a 75 Ω cable); scale the level
divider about 10x down (390 Ω / 1.2 kΩ / 140 Ω, Thevenin about 93 Ω) so the OSD
level does not drop 39 % into that load (04 §5.2). P4 confirms black/white
levels with the target cameras.

Power and thermal (I, 04 §6, 06 §4): PA at 400 mW draws about 0.55 A from the
cell (2.0 W at 3.7 V, 1.6 W heat); at 25 mW about 0.30 A (PA quiescent
dominates). Defaults: pit on boot (RCE), 25 mW, `vtx_low_power_disarm` (ELRS
MSP-VTX honours it). In still air the board would settle 70-100 K above ambient
at 400 mW, so the PA must not run at power on the bench. 400 mW from a 3.0 V
sagged cell is not guaranteed on a minimum-P1dB SE5004L (about 25.2 dBm, 04
§3.4): published as measured. A thermal derate exists in neither ELRS nor
Betaflight (open item).

### 4.9 Blackbox

| Option | Body | Stock | Verdict |
|---|---|---|---|
| **W25Q128JVPIM**, WSON-8 6x5, on SPI0 | 30 mm² | C2441427, 24,670 | **chosen** (Matrix parity, deep stock) |
| GD25Q128EQIG / PY25Q128HA-QVH, USON-8 4x4 | 16 mm² | no distributor found | later (−16 mm² placed) |
| NOR on the RP2354A QSPI bus, CS1 | 1 GPIO instead of 4 | - | no: flight-unvalidated driver, XIP stall risk (05 §1.2) |

Fallback: Winbond W25Q128JVPIQ, C190862, 6,862 (same land). `blackbox` sheet
keeps its name, bus (SPI0, GPIO18-21) and CS pull-up; microSD removed.

### 4.10 Connectors and pads

| Item | Decision | Part / geometry | Why |
|---|---|---|---|
| Battery | BT2.0 pigtail (22 AWG, 40 mm, user-fitted), two plated holes Ø 0.9 mm finished in 2.0 x 3.0 mm pads, both sides, 6-10 stitching vias each | no PCBA part | a wire through a PTH cannot peel the pad; Ø 0.9 keeps the holes below the 1.0 mm mounting-hole threshold of `check_board_setup.py` |
| Motors | 12 solder pads 1.0 x 1.8 mm on the top, each with a plated **Ø 0.5 mm wire-anchor hole**, pitch 1.5 mm, at the board edge facing each motor | no PCBA part | Matrix "solder-required" equivalent. A Matrix-style 1.25 mm THT plug does not fit the fab-rule intersection (pad-with-hole to pad-with-hole 0.40 mm at NextPCB with a 0.20 mm PTH ring → pitch ≥ 1.30 mm), and four SMD PicoBlade headers cost 173-212 mm² |
| USB | JST **BM04B-SRSS-TB(LF)(SN)**, SH1.0 4-pin vertical, bottom, rear corner, C160390, 44,655 | fallback BM04B-SRSS-TBT(LF)(SN), C495539, 2,334 (same land) | as on the Matrix; BetaFPV adapter pinout to be measured and matched |
| Camera | JST **BM03B-SRSS-TB(LF)(SN)**, SH1.0 3-pin vertical, top, front, C160389, 31,415, plus CAM / 5V / GND pads | fallback BM03B-SRSS-TBT(LF)(SN), C495538, 1,156 | Matrix CAM IN plug |
| VTX antenna | U.FL, top, front half | §4.8 | |
| RX antenna | plated hole Ø 0.5 mm for an insulated λ/4 wire (31 mm), rear-left edge, bottom | - | Matrix uses the same; best radiator for the area |
| User pads | TX1 RX1 TX2 RX2 5V GND (UARTs), LED 5V GND (LED strip), BZ+ BZ− (buzzer), CAM 5V GND (camera): 14 pads 1.0 x 1.2 mm, top | - | 2 free UARTs |
| Test pads | BOOT (RP2354 QSPI_SS) + GND, RXB (ESP32 GPIO0), CLK / DIO (FC SWD), 8x C2D/C2CK (ESC) | Ø 0.8 mm | no tact switch (saves about 7 mm²) |

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
| **Total** | **0.69 A (3.45 W)** | 0.41 A without the user allowances; 1.25 A if the PA is moved to +5V |

### 5.2 Every load from the cell, at 3.0 V and 4.35 V

| Load | at 3.0 V in | at 4.35 V in | Basis |
|---|---|---|---|
| Boost input for 0.69 A at 5 V | 1.31 A (η 0.88) | 0.86 A (η 0.92) | TPS61022 efficiency curves (S) |
| SE5004L PA, pit / 25 / 100 / 400 mW | 0 / 0.30 / 0.35 / 0.55 A | same | I (Icq 300 mA spec, 04 §6.1) |
| 4x EFM8BB51 at 49 MHz | 0.020 A | 0.020 A | V (55.5 µA/MHz), I (peripherals) |
| VBAT divider | 0.0002 A | 0.0002 A | |
| **Cell current (no motors), VTX pit** | **1.33 A / 3.98 W** | **0.88 A / 3.84 W** | |
| VTX 25 mW | 1.63 A / 4.88 W | 1.18 A / 5.14 W | |
| VTX 100 mW | 1.68 A / 5.03 W | 1.23 A / 5.36 W | |
| **VTX 400 mW** | **1.88 A / 5.63 W** | **1.43 A / 6.23 W** | |
| ESC per motor at hover / 6 A / 12 A | 0.06 / 1.07 / 3.81 W of loss | same | §4.3 |

### 5.3 5 V margin (P0 gate)

TPS61022 with 0.47 µH (Isat 7.5 A), 1 MHz, η 0.88 (I, datasheet equations):
at 3.0 V in, D = 0.47, ripple 3.0 A, peak held to 80 % of Isat → **2.37 A**
available against 0.69 A (**+244 %**); at 2.8 V in, **2.21 A (+221 %)**. With
the PA on +5V (1.25 A): +90 % at 3.0 V. The valley limit (6.5 A min) does not
bind. Gate "≥ 20 % margin at 3.0 V on datasheet curves": **pass**.

### 5.4 Thermal budget (on-board heat)

| Source | Hover, VTX 400 mW, 3.7 V | Hover, VTX 25 mW | Bench, disarmed, pit |
|---|---|---|---|
| PA | 1.64 W | 1.09 W | 0 |
| RTC6705 + its LDO | 0.50 | 0.50 | 0.50 |
| FC rail (LDO + loads) | 0.45 | 0.45 | 0.45 |
| RX rail (LDO + loads) | 0.50 | 0.50 | 0.50 |
| Boost loss | 0.38 | 0.38 | 0.25 |
| ESC MCUs | 0.07 | 0.07 | 0.07 |
| ESC FETs (1 A/motor) | 0.22 | 0.22 | 0 |
| Shunt + copper | 0.05 | 0.05 | 0 |
| **Total** | **3.8 W** | **3.3 W** | **1.8 W** |
| Board rise (flight G 0.07-0.14 W/K; bench still air 0.025-0.035 W/K) | +27-54 K | +24-47 K | +51-72 K |

Camera, LED strip and buzzer power is dissipated off the board. The bench case
explains the pit-on-boot default and a bench-fan note in the README. Time
constant in flight about 20-40 s (C about 2.9 J/K).

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
| Holes | Ø 3.5 Edge.Cuts circles (non-plated cut-outs) at (−12.875, −12.875) left, (−12.875, +12.875) rear, (+12.875, +12.875) right |
| Bounding box | ±15.275 → absolute 97.925-128.475 on both axes, 30.55 x 30.55 |
| Area net of holes | 696.6 mm² (grid estimate, ±3 mm² for fillets) |
| Copper keepout | 0.20 from every edge and hole (copper-to-edge rule) |
| Part keepout | 0.30 band inside the outline; Ø 5.2 grommet flange at each hole, both sides (rule area on `User.1`) |
| Guides | 25.5 and 26.0 mm frame patterns drawn on `User.Eco1`; front marked on `User.Eco2` |

---

## 8. Stackup and fab rules

**Owner rule: through vias only.** Filled-and-capped via-in-pad (IPC-4761 Type
VII, non-conductive epoxy) is a through via and is used in every pad that holds
a via. No blind, buried or laser vias (the NextPCB track 07 recommendation of HDI
1+4+1 is overridden by the owner rule).

### 8.1 DFM intersection (NextPCB ∩ JLCPCB)

NextPCB values: track 07 (S1 standard capabilities, S2/S3 advanced and HDI pages,
S12 stackup library, verified 2026-10-06). JLCPCB values: capabilities page read
2026-10-07 (https://jlcpcb.com/capabilities/pcb-capabilities).

| Rule | NextPCB | JLCPCB | **This board** |
|---|---|---|---|
| Min track / space, 1 oz outer | 0.08 / 0.08 mm | 0.09 / 0.09 mm (multilayer; 3 mil only in BGA fan-out) | **0.09 / 0.09** |
| Min track / space, 0.5 oz inner | 0.065 / 0.08 mm | 0.09 / 0.09 mm | **0.09 / 0.09** |
| Min mechanical drill | 0.15 mm (boards ≤ 1.2 mm) | 0.15 mm (0.10 only ≤ 1.0 mm, ENIG/OSP) | **0.15** |
| Via annular ring | 0.09 (1 oz table) / 0.10 (via-row image) | via dia ≥ hole + 0.10 (0.15 preferred) | **0.10 → via 0.35 / 0.15** |
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
| Copper to routed edge | 0.20 | 0.20 | **0.20** (components 0.30) |
| Mask expansion | ≥ 0.04 (1.5 mil) | 1:1 allowed (LDI) | **0.04** |
| Mask bridge, green | 0.089 (copper gap) | 0.10 | **0.10** (green only; black 0.127/0.13) |
| Silk line / text height | screen 0.127 / 0.76; inkjet 0.08 / 0.61 | 0.15 / 1.0 | **0.15 / 1.0** (pad labels 1.2 front, 1.0 back) |
| Pad to silk | 0.15 | 0.15 | **0.15** (template rule) |
| NPTH min | 0.40 | 0.50 | **0.50** |
| Plated slot min | 0.50 | 0.35 | **0.50** |
| Thickness options, 6L | 0.8 / 1.0 / 1.2 ..., ±0.1 mm below 1.0, ±10 % from 1.0 | 0.8 / 1.0 / 1.2 ..., same tolerance | **1.0 ± 0.1** |
| Copper | outer 1/2 oz, inner 0.5/1/2 oz | same | **1 oz outer, 0.5 oz inner** |
| Via-in-pad | non-conductive fill + cap, Type VII, +$12.55 per 10 pcs, +4 days | epoxy filled & capped, **default for 6L and up**, 0.15-0.55 mm holes | **Type VII on every via in a pad** |
| Impedance tolerance | ±10 % | ±10 % (±5 % on request) | **50 Ω ± 10 %** |
| Assembly spacing | 0201 0.20-0.25 mm, 0402 0.25-0.30 mm (NextPCB blog, June 2026) | - | **0.20 body/land, 0.25 between two 0402** |

### 8.2 Stackup

6 layers, 1.0 mm, from the NextPCB library entry `6L-1.0mm-0.5oz-1080` (V,
track 07 §1.4). JLCPCB builds 6L at 1.0 mm with 0.5 oz inner by default; its
exact 1.0 mm dielectric build was not readable (its stackup page lists only 1.6
mm builds), so the JLC equivalent and the RF width are confirmed at P1 with the
JLC stackup selector (EQ item).

| Layer | Thickness | Role |
|---|---|---|
| F.Mask | 0.015 | green |
| **L1 F.Cu** | 0.035 (1 oz finished) | top parts (VTX, P-FETs, EFM8s, CAM plug), 5.8 GHz CPWG, VBAT/phase pours |
| prepreg 1080 | 0.077 | εr 4.2 |
| **L2 In1.Cu** | 0.0175 | **solid GND** (RF and top-side reference, ESC return) |
| core | 0.30 | |
| **L3 In2.Cu** | 0.0175 | signals between the sides, local pours |
| prepreg 2313 | 0.103 | |
| **L4 In3.Cu** | 0.0175 | **+BATT plane** (ESC feed), +5V / +3V3 islands, slow signals |
| core | 0.30 | |
| **L5 In4.Cu** | 0.0175 | **solid GND** (bottom-side reference, ESC return) |
| prepreg 1080 | 0.077 | |
| **L6 B.Cu** | 0.035 | bottom parts (FC, RX, power, N-FETs), 2.4 GHz feed, pours |
| B.Mask | 0.015 | green |

Dielectric + copper = 0.997 mm; KiCad's sum including both masks is 1.027 mm
(that is the figure `apply_stackup.py` writes and `board_spec.json` checks).
Layer roles follow the line standard F sig / In1 GND / In2 sig / In3 PWR / In4
GND / B sig (LINEUP B1). Finish ENIG, green mask, white legend, vias tented
both sides except Type VII in pads.

Impedance (NextPCB library, V): 50 Ω microstrip on L1 over L2 = 0.139 mm; for
CPWG with a 0.15 mm gap use **0.13-0.14 mm** (recompute in KiCad's calculator at
P1, target 50 Ω ± 10 %). 2.4 GHz feed on L6 over L5 has the same geometry. USB
FS: 0.12 / 0.12 mm pair, length-matched, not impedance-critical at 12 Mb/s.

### 8.3 Vias

| Preset | Size | Use |
|---|---|---|
| Signal | 0.35 / 0.15 mm (annular 0.10) | default; all vias in pads (Type VII) |
| Power | 0.40 / 0.20 mm | +BATT, GND and phase arrays outside pads |

0.15 mm via in 1.0 mm board: aspect ratio 6.7:1, about 1.8 mΩ each (18 µm
plating, JLC average); 0.20 mm: about 1.4 mΩ. Counts: ≥ 15 power vias per net
at the battery pads (25 A), ≥ 8 per ESC cluster feed, 8 per phase stack, 9 in
the PA EP, 4-9 in each QFN EP. Array pitch ≥ 0.35 mm (0.15 drill) / 0.40 mm (0.20
drill) from the 0.20 mm same-net hole rule. Remove unused inner annular rings.

### 8.4 Board setup values for P1

Constraints: clearance 0.09, track 0.09, connection 0.09, via 0.35 / 0.15,
annular 0.10, hole-to-hole 0.20, hole clearance 0.20, copper-to-edge 0.20,
microvia minimums left at the template values (0.20 / 0.10) and microvias,
blind and buried vias disallowed by a custom rule; solder mask expansion 0.04,
mask minimum web 0.10; silk minimum text 1.0 mm / 0.15 mm line. Track presets
0.10, 0.14, 0.20, 0.30, 0.50, 1.00.

Net classes (names after OpenAIO; colours set through netclass directive
labels):

| Class | Nets | Track | Clearance | Via | Colour |
|---|---|---|---|---|---|
| Default | signals | 0.09 | 0.09 | 0.35/0.15 | - |
| VBAT | +BATT, shunt nodes | 0.50 (pours) | 0.15 | 0.40/0.20 | red |
| Phase | 12 motor phase nets | 0.50 (pours) | 0.15 | 0.40/0.20 | orange |
| Gate | 24 FET gate nets | 0.15 | 0.10 | 0.35/0.15 | yellow |
| Power | +5V, VBUS, +3V3, +3V3_RX, +3V3_VTX, +1V8, +1V1 | 0.25 | 0.09 | 0.35/0.15 | magenta |
| Analog | video, OSD level/sync, VBAT/current sense, PA detector | 0.10 | 0.15 | 0.35/0.15 | cyan |
| RF | 5.8 GHz chain, 2.4 GHz feed | 0.14 | 0.15 | 0.35/0.15 (fence) | green |
| USB | D+ / D− | 0.12 (pair gap 0.12) | 0.12 | 0.35/0.15 | blue |

Power net names per the lineup decision: +BATT, +5V, +3V3, +1V8, GND, with
suffixed rails +3V3_RX, +3V3_VTX, +1V1 and VBUS.

Custom rules below the template marker (text for P1): different-net hole to
hole 0.30; PTH pad hole to hole 0.45; PTH hole clearance 0.28; inner-layer PTH
hole to copper 0.30; NPTH to copper 0.20; SMD pad to track 0.13; disallow
micro/blind/buried vias; courtyards at max(body, land) + 0.10 with
`courtyards_overlap` raised to **error** and courtyard clearance 0 (touching
courtyards = 0.20 mm); 0402-to-0402 +0.05; tall parts (U.FL, SH1.0, 2520
inductor) +0.5 mm to 0201/0402; user pads and battery/motor pads ≥ 0.5 mm to any
0201/0402 (iron rework); through via inside a courtyard flagged for Type VII;
keepout rule areas for the grommet flanges and RF zones (§10).

---

## 9. Area budget

### 9.1 Usable area per side

Outline (I, `outline.py`, 10 µm grid): body 697.0 mm² − front arc 7.2 + ears
35.7 − holes 28.9 = **696.6 mm²**. Usable for parts, per side: inside a 0.30 mm
edge band and outside Ø 5.2 mm grommet-flange keepouts around the 3 holes
(flange diameter assumed; measure a BetaFPV ball at P2) = **643.6 mm²**.

### 9.2 Placed area per block (0.2 mm body/land spacing, perfect tiling)

Method (I, `budget.py`): each part counts (land L + 0.2) x (land W + 0.2), lands
at IPC density L (0201 0.80 x 0.35, 0402 1.30 x 0.55, 0603 2.10 x 0.90, leadless
ICs body + 0.1). No routing allowance: the margin to 100 % is the routing and
via allowance.

| Block | Parts | Top mm² | Bottom mm² | Land items (count x package → mm² each) |
|---|---|---|---|---|
| ESC x4 | 96 | 225.4 | 89.8 | T: 4x QFN-20 3x3 → 10.89; 12x SON 3.3x3.3 → 13.32; 40x 0201. B: 12x SON 2x2 → 5.52; 12x 0201; 8x 0402 → 1.12; 8x C2 pads → 1.00 |
| Input, protection, sense | 15 | - | 31.9 | 2x 0603 → 2.53; SOD-123FL → 7.38; 1206 shunt → 8.20; SC-70-6 → 5.72; 10x 0201 |
| FC core (RP2354A, drivers, LEDs, test pads) | 39 | - | 92.3 | QFN-60 7x7 → 54.76; 2520 crystal → 6.44; 2016 inductor → 4.80; 24x 0201; 4x 0402; 2x DFN1006 → 1.17; 2x LED 0402; 4x test pads |
| Gyro + 1.8 V LDO | 7 | - | 13.7 | LGA-14 → 9.24; X2SON 1x1 → 1.69; 5x 0201 |
| PIO OSD front end | 12 | 8.1 | - | X2SON-6 → 1.43; X2SON-5 → 1.21; DFN0603 → 0.54; 9x 0201 |
| Blackbox NOR | 3 | - | 35.7 | WSON-8 6x5 → 34.56; 2x 0201 |
| RX (ESP32 + flash + SX1280 + LDO) | 38 | - | 87.5 | QFN-48 5x5 → 28.09; USON 2x3 → 7.59; 1612 → 2.85; QFN-24 4x4 → 18.49; TCXO 2016 → 4.37; LPF 1005 → 1.04; WSON-6 2x2 → 5.76; RGB LED → 1.69; 28x 0201; 2x 0402 |
| VTX (RTC6705, PA, BPF, U.FL, LDO) | 52 | 123.1 | - | QFN-40 6x6 → 39.69; 3225 → 9.80; SOT-23-5 → 9.60; QFN-20 4x4 → 18.49; BPF 1608 → 2.09; U.FL → 14.07; DFN1006 → 1.17; 39x 0201; 6x 0402 |
| Power (boost, FC LDO, OR diode, camera filter) | 16 | - | 27.4 | VQFN 2x2 → 5.29; 2520 → 6.96; 2x 0603; 3x 0402; DFN1006; X2SON 1x1; 7x 0201 |
| Connectors | 2 | 28.8 | 33.6 | SH1.0-3 vertical → 28.80 (T); SH1.0-4 vertical → 33.60 (B) |
| **Components** | **280** | **385.4** | **411.9** | |
| Pads, labels, silk art | | 125.0 | 84.4 | T: 12 motor pads 32.8; battery 17.5; 14 user pads 23.5 + labels 25.2; M1-M4 labels, arrow, 1S, +/− 20.0; ANT hole 2.0; connector labels 4.0. B: motor PTH rings 17.3; battery 17.5; ANT 2.0; logo + OPEN/AIO/WHOOP + REV1 41.7; test-pad labels 6.0 |
| **Total** | | **510.4 mm²** | **496.3 mm²** | |
| **Share of 643.6 mm²** | | **79.3 %** | **77.1 %** | gate ≤ 85 %: **pass** |

The Matrix II reaches about 45-50 % package-body coverage per side (01 §5.2);
this budget is about 45 % body coverage on the top, the same density class.

### 9.3 What gives if P2 does not close

In order, with the area each lever frees: (1) move OSD front end and connector
labels to the bottom (−12 mm² top); (2) drop the SH1.0 camera plug, pads only
(−28.8 top); (3) VTX LDO back to X2SON when stocked (−7.9 top); (4) USON-8 4x4
blackbox when sourced (−16.1 bottom); (5) P-FET to CSD25310Q2 2x2 (−93.6 top,
rating to about 5 A, Matrix-equivalent); (6) HDI, put to the owner with numbers
(not proposed).

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
| ESC3 / ESC4 (M3, M4) | P + EFM8 top, N bottom | left-ear quadrant (x < −2, y < −2) | motor pads M4 on the top edge, x −10 … −5; M3 on the left edge, y −10 … −5; FETs inboard of their pads, EFM8 behind them; clear of the left-ear flange |
| ESC1 / ESC2 (M1, M2) | P + EFM8 top, N bottom | right-ear quadrant (x > 2, y > 2) | M1 pads on the bottom edge, x +5 … +10; M2 on the right edge, y +5 … +10 |
| VTX: RTC6705, PA, BPF, U.FL | top | front half: RTC6705 near the centre, PA about (+5, −5), BPF + U.FL about (+7.5, −7.5) toward the front corner | 5.8 GHz chain on L1 over solid L2; PA ≥ 10 mm from the gyro |
| CAM plug + CAM/5V/GND pads, OSD front end | top | right edge upper half (front-right), about (+10.5, −4) | camera cable enters from the front; video path CAM → OSD switch → RTC6705 stays in the front quadrant, away from ESC currents |
| User pads TX1 RX1 TX2 RX2 5V GND, LED 5V GND, BZ+ BZ− | top | left edge lower half and bottom edge left half (rear corner area) | wiring leaves rearward |
| Battery pads B+ / B− | both (THT) | bottom edge near the rear corner, about x −8 and −5, y +11.6 | pigtail exits rearward; "1S" and +/− on top silk |
| Power entry: TVS, 2x 22 µF, shunt, INA186 | bottom | next to the battery pads | Kelvin taps from the shunt pads |
| Boost (TPS61022 + 2520 L) | bottom | rear quadrant about (−6.5, +8) | ≥ 5 mm from the gyro; hot loop < 3 mm |
| FC: RP2354A + 12 MHz + 3.3 µH | bottom | centre, about (+1.5, −1.5) | core SMPS layout per the RPi guide |
| Blackbox NOR | bottom | front-right of the MCU, about (+6, −6) | |
| Gyro (BMI270) + 1.8 V LDO | bottom | centre-rear, about (−1, +3) | ≥ 10 mm from the PA (top front), ≥ 5 mm from the boost, ≥ 4 mm from FET clusters |
| RX: ESP32 + flash + crystal | bottom | left of centre, about (−6, −3) | |
| SX1280 + TCXO + LPF | bottom | left edge lower half, about (−7, +5) | 2.4 GHz feed ≤ 6 mm to the antenna hole |
| RX antenna hole | through | about (−12.3, +9.5), rear-left edge | wire runs off the rear-left edge, away from the VTX antenna |
| USB SH1.0 vertical | bottom | left edge, about (−10.5, +2) | plug from below |
| Test pads BOOT, RXB, CLK, DIO; ESC C2 pads | bottom | near the MCU / under each EFM8 | |
| Silk art: incutec logo, OPEN / AIO / WHOOP, REV1 | bottom | free patch in the front-right quadrant (bottom side has no VTX parts) | |

RF keepouts:
- **5.8 GHz**: no copper on L1 within 0.15 mm (CPWG gap) of the line except the
  coplanar GND; L2 solid under the whole chain plus 1 mm; via fence ≤ 2.5 mm
  pitch both sides; no via in the RF path; U.FL ground tabs with ≥ 4 vias to L2;
  no other parts within 1 mm of the line on L1.
- **2.4 GHz**: CPWG on L6 over L5 from the LPF to the antenna hole; all-layer
  copper keepout r = 1.0 mm around the hole except the feed; no parts within
  3 mm on the wire's exit path; no Wi-Fi antenna, so no ESP32 keepout.
- **Antenna separation**: VTX antenna (U.FL, front, up-rear to the canopy) and
  RX wire (rear-left, along the frame) ≥ 20 mm apart, orthogonal where possible.

---

## 11. Layout rules specific to this board

- **Commutation loops**: one 100 nF 0201 per half-bridge, on the bottom
  between the N source (GND) and a +BATT via next to it; loop P source → drains
  → phase vias → N → cap ≤ 3 mm² through 1 mm of board. Target N-FET VDS
  overshoot ≤ 9 V at 18 A turn-off (12 V part).
- **Phase copper**: P drain (top) and N drain (bottom) stacked, 8 Type VII
  0.35/0.15 vias per phase; phase to motor pad ≥ 1.2 mm wide on L1 and repeated
  on L6 with stitching; solid pad connections (no thermal relief) on FET pads.
- **+BATT path**: battery pad → shunt (Kelvin) → L6 pour + L4 plane + L1 pours
  at the clusters; ≥ 15 power vias at each battery pad; per cluster ≥ 8 vias.
  Size the trunk for 25 A pack, each channel for 12 A bursts.
- **GND**: L2 and L5 unbroken (no splits under any signal), L1/L6 pours stitched
  every ≤ 3 mm at the board perimeter and around the RF.
- **Gyro isolation**: no switch nodes (boost SW, phase nodes) on any layer within
  2 mm of the gyro; its 1.8 V LDO and decoupling on the same side; gyro centred
  away from the PA and boost as in §10.
- **Video ground**: camera return enters L2 at the CAM plug; video traces on L1/L3
  with GND on both sides; no ESC return current through the front quadrant;
  100 pF shunts at video entry points; RTC6705 loop filter ≥ 5 mm from the boost.
- **Boost**: Cin at VIN, Cout–SW–GND hot loop < 3 mm, SW copper minimal, MODE
  tied high (forced PWM), feed VIN from the bulk-cap node, not through ESC copper.
- **Crystals**: 12, 40 and 8 MHz next to their ICs with GND guard, no signal on
  L2 under them; TCXO likewise.
- **Exposed pads**: EFM8, RTC6705, PA, SX1280, ESP32, RP2354A EPs soldered and
  Type VII via-in-pad; QFN exposed pads on opposite sides offset ≥ 1 mm (X-ray).
- **0201 on planes**: thermal relief spokes 0.10-0.15 mm, equal copper on both
  pads (tombstoning).
- **Hand-solder pads**: battery and motor pads get a copper neck so a 60-80 W
  iron can heat them; mask-defined edges.

---

## 12. Firmware targets

| Firmware | Plan |
|---|---|
| Betaflight | New board config `OPENAIO_WHOOP` in betaflight/config (manufacturer ID to request; proposal INCU), `FC_TARGET_MCU RP2350A`, derived from the house OPENFC_LITE_MINI_RP2350A target. Requires release ≥ 2026.6.2. Defines: SPI1 gyro (BMI270 or ICM42688P, one per revision), `ENABLE_FB_OSD` with OSD_W/EN/SYNC = GPIO14/15/16, `PIO_LEDSTRIP_INDEX 1`, PIOUART0 on GPIO2/3, UART0 = serial RX (CRSF), `USE_VTX_MSP`, `USE_FLASH` W25Q128 (m25p16 driver) on SPI0 CS GPIO21, motors on PIO0 GPIO25/24/23/22 = M1-M4, bidirectional DShot, `DEFAULT_ALIGN_BOARD_YAW` ±45 (diamond mount; sign fixed in P4 with the gyro orientation), current scale 500 and VBAT scale measured, beeper inverted per driver |
| Bluejay | Stock Bluejay ≥ 0.21, layout **BB51 "A"** (no custom layout). Start `A_X_10_48`; step to `A_X_5_96` only after the dead-time scope test (§14, V2). Flash through Betaflight 4-way passthrough; C2 pads for recovery. Publish the chosen build and the reasoning |
| AM32 | not applicable (EFM8 MCU) |
| ExpressLRS | Day one: `Unified_ESP32_2400_RX` with the generic layout `Generic 2400 Whoop Rx and VTx.json` (pin-compatible). Release: a target entry in ExpressLRS/targets that uses that layout plus an overlay with this board's VPD/PWM calibration arrays (25/100 mW at 4 frequencies), LED index for the single RGB LED, `power_values [13]`, no `radio_dcdc`. ELRS ≥ 4.1. Patch to propose upstream: 200/400 mW calibration arrays and a VTX thermal derate |

---

## 13. Silkscreen plan

Per LINEUP-CONVENTIONS B2-B14 and the owner rules: no component silkscreen, no
reference designators, no "Drone" anywhere on a fabricated layer, Tokyo font
embedded, back text mirrored, bold upper-case pad labels 1.2 mm on the top and
1.0 mm on the bottom (JLC floor 1.0 mm / 0.15 mm line).

| Side | Content |
|---|---|
| Top | pad labels: **TX1 RX1 TX2 RX2 5V GND**, **LED 5V GND**, **BZ+ BZ−**, **CAM 5V GND**; **M1 M2 M3 M4** at each motor pad group (Betaflight order: M4 front-left, M2 front-right, M3 rear-left, M1 rear-right); **+ −** (4-6 mm) and **1S** at the battery pads; **ANT** at the RX antenna hole; connector names **CAM** and **VTX** with pin-1 marks; forward arrow (0.3 mm lines) pointing at the front corner |
| Bottom | incutec logo ≥ 6.1 x 1.4 mm; product name **OPEN / AIO / WHOOP** stacked in Tokyo; **REV1** (equal to the board title-block rev `rev1`); test-pad labels **BOOT RXB CLK DIO**; connector name **USB** with pin-1 mark; ESC C2 pads unlabelled (flashing test points, LINEUP B7), documented in the README pinout |
| Off-board | `User.Eco2` note marking the front; mounting-pattern guide on `User.Eco1`; grommet-flange keepouts on `User.1` |

---

## 14. Validation plan

| # | Test | Pass / fail |
|---|---|---|
| V1 | 5 V rail: VIN 4.35 → 2.6 V, loads 0.69 A and 1.25 A | +5V ≥ 4.85 V at VIN ≥ 2.8 V; ripple ≤ 50 mV p-p; no FC/RX reset to 2.5 V; cold start from 3.0 V |
| V2 | ESC dead time: scope P gate, N gate, phase node, per-ESC supply current at DT 10 and DT 5, 48 and 96 kHz, VIN 4.35 and 3.0 V, worst EFM8 pin | no shoot-through spike > 2x the steady current; P fully off (Vgs > −0.3 V) before N on |
| V3 | N-FET overshoot at 18 A turn-off | VDS ≤ 9 V |
| V4 | ESC rating protocol: 1S 4.2 V stiff supply, motor + prop in propwash (fan, stated airflow), 25 °C, one channel stepped 4/6/8 A while others run 2 A, then all four at 4 A; bursts from 40 °C | hottest package ≤ 100 °C at steady state for the continuous figure; ≤ 110 °C at the end of 12 A 10 s and 18 A 3 s. Publish the curve; same rig on a Matrix II |
| V5 | VTX power: 25/100/400 at 5650/5750/5850/5917 MHz, VIN 3.0/3.7/4.35 V | 25 and 100 mW within ±1.5 dB; 400 mW published as measured; frequency error ≤ ±200 kHz |
| V6 | VTX spurious with the BPF | 2nd harmonic ≤ −30 dBm; RTC6705 half-frequency leakage (2.8-2.97 GHz) reported |
| V7 | RX: sensitivity and desense | within 2 dB of the SX1280 figure; ≤ 3 dB desense with VTX at 400 mW |
| V8 | Thermal: board at 25/100/400 mW, bench still air and fan | matches §5.4 within ±30 %; pit-on-boot verified |
| V9 | FC gates on RP2350 (2026.6.2+): bidirectional DShot300/600 with Bluejay BB51 (30 min hover, telemetry error rate < 1 %); 4-way passthrough flash and settings of all 4 ESCs; MSP-VTX from ESP32 ELRS over CRSF (band/channel/power from OSD and Lua); FB OSD with 2-3 target cameras PAL and NTSC; SPI NOR blackbox at 2 kHz without loop overrun; ELRS flash through serial passthrough | each passes, else its fallback (C2 pads, AT7456E/G473 respin, SPI NOR on another bus) |
| V10 | Gyro fly-off BMI270 vs ICM-42688-P (5 + 5 boards) | release population has the lower pre-filter noise and no resonance peak in the motor band |
| V11 | Weight | ≤ 3.5 g bare |
| V12 | Crash: BetaFPV protocol, 4 boards, 20 hits | 0 failures |
| V13 | Outline and holes on Air65 II / Air75 II (25.5) and Meteor65 Pro II / Meteor75 Pro (26.0) frames with BetaFPV balls | fits all four without reaming |

---

## 15. Risks, open questions, sourcing

### 15.1 README design questions

| README question | Status | Answer / what is still open |
|---|---|---|
| VTX part | **proposed-resolved (sourcing risk open)** | RTC6705/RTC6705A stays (no equivalent exists); PA SE5004L-R; authorised RTC6705 stock is zero, so it is a consigned, traceable broker line with incoming tests |
| Power stage | **proposed-resolved** | P+N direct drive from the EFM8 on the cell, CSD25402Q3A + CSD13202Q2, Bluejay layout A at DT 10 → 5. The README premise that direct drive needs AM32-style 120-140 dead times holds only for 1-2S level-shifted designs; 1S direct drive ships at DT 5 (Bluejay) and DT 25 (AM32 SP8) |
| Electronics rail | **proposed-resolved** | TPS61022 forced-PWM boost, 2.2 A guaranteed at 2.8 V against a 0.69 A load; PA on the cell; split LDOs |
| Motor connection | **proposed-resolved for rev1; plugs open** | solder pads with wire-anchor holes; a 1.25 mm THT plug violates the fab-rule intersection and SMD plugs do not fit |
| Antenna | **proposed-resolved** | RX wire monopole at the rear-left corner (bottom), VTX U.FL in the front half (top), 5.8 GHz BPF, no Wi-Fi antenna |

### 15.2 Other open questions

| # | Question | Decided by |
|---|---|---|
| O1 | SE5004L output on the cell at 3.0-4.35 V (400 mW at sag) | bench V5 before P4 freeze; 0 Ω to +5V is the fallback |
| O2 | Grommet flange diameter (keepout Ø 5.2 assumed) | calipers on a BetaFPV ball before P2 |
| O3 | BetaFPV SH1.0 USB adapter pinout | measure before P4 |
| O4 | JLC 6L 1.0 mm dielectric build and RF width | JLC stackup selector at P1 |
| O5 | CSD25402Q3A vs CSD25404Q3 land compatibility | P3 |
| O6 | 200 mW level and calibrated 400 mW in ELRS; VTX thermal derate | ELRS PR (firmware) |
| O7 | Walsin BPF power handling at 400 mW | ask Walsin; VNA |
| O8 | RP2350 firmware gates (V9) | OpenFC-Lite-Mini + external whoop ESC bench before P5 |
| O9 | Matrix II physical teardown (layer count, BEC part, ball size) | buy one |
| O10 | 1 oz inner copper (+0.3 g, about −0.15 W at 25 A) | only if V4 misses |

### 15.3 Sourcing plan

Partial turnkey at NextPCB: NextPCB sources the lines its HQ Online stock and
quote engine (Digi-Key, Mouser, Element14, Avnet, ...) can fill; the lines below
are consigned (fee $50 per 50 consigned lines, parts must arrive within the
7-working-day window, marked "C" in the BOM; V, track 04/07).

| Line | Why consigned | Buy (10-board prototype / 50-board run) |
|---|---|---|
| RTC6705 / RTC6705A | no authorised stock | 15 / 60 from a traceable broker or agent; incoming test on 3 (SPI register read 0x00 = 0x0190, frequency within ±200 kHz, PAOUT1 power) |
| SE5004L-R | not on HQ Online | 15 / 60 (LCSC 1,339) |
| EFM8BB51F16G-C-QFN20R | not on HQ Online | 50 / 220 (LCSC 31,643) |
| RP2354A | not on HQ Online | 15 / 60 (LCSC 14,698) |
| ESP32-D0WD-V3, GD25Q32EEIGR, SX1280IMLTRT | LCSC-only stock today | 15 / 60 each |
| CSD25402Q3A, CSD13202Q2 | if the quote engine misses them | 150 / 650 each |
| Everything else | turnkey (LCSC/HQ Online/Digi-Key stock above) | - |

NRE estimate for 10 boards (I, track 07 prices): PCB 6L 1.0 mm with 0.15 mm
vias and Type VII about $220; double-sided assembly $105 plus joint and X-ray
fees (about $50-150); parts about $600 including the broker RTC6705s; freight
$50-100: **about $1,000-1,200**. Lead time about 4 weeks door to door (external
parts case).

### 15.4 Risks carried

| Risk | Mitigation |
|---|---|
| RTC6705 fake or remarked parts | traceable source, incoming tests, 10 spares from the same lot |
| Routing closure with through vias only at 77-79 % placed area | P2 channel-capacity probe; levers in §9.3; HDI only as an owner decision with numbers |
| RP2350 Betaflight features three weeks into a release | V9 gates on existing house hardware before P5; G473 fallback documented |
| ESP32 strap pins shared with VTX control (GPIO2, GPIO12) | pull-down on GPIO2; GPIO12 follower input held low; checked in P4 |
| PA heat on the bench | pit on boot, low power disarmed, README warning |

---

## 16. Sources (load-bearing claims)

| Claim | Source | Status |
|---|---|---|
| Matrix II size, holes, thickness, weight, 3-point mount, crash test | BetaFPV product page and JSON; photo measurements (01 §2, 00) | V |
| Matrix II ESC: 4x EFM8BB51, 12x AGM210MAP, Bluejay A_X_5_96, "12 A / 18 A" | photos + product JSON + Bluejay source (01 §3.2, 03 §2) | V |
| Two FETs in series, P+N conduction model, Rds fits | AGM210MAP VER2.72, TI CSD25402Q3A/CSD25404Q3/CSD13202Q2 datasheets; model `work/esc03/loss.py` re-run (03 verification) | V (inputs) / I (model) |
| EFM8BB51 VDD 1.8-5.5 V, GPIO ≤ 60 Ω | EFM8BB51 data sheet Rev 1.0 (03 verification #3) | V |
| Bluejay layout A pin map, DT steps 20.4 ns | `src/Layouts/BB51/A.inc`, `src/Bluejay.asm` (clone 0368d11) | V |
| ELRS 4.x excludes VTX SPI / MSP-VTX on ESP32-C3 | ExpressLRS `src/src/rx_main.cpp` at 4.0.0/4.1.0/master (05 verification #13) | V |
| ELRS whoop RX+VTX layout pins | ExpressLRS/targets `RX/Generic 2400 Whoop Rx and VTx.json` (clone 42ed776) | V |
| Betaflight RP2350: flash, VTX, passthrough only from 2026.6.2; RTC6705 driver and SPI ELRS undefined; FB OSD consecutive pins | Betaflight tags 2026.6.1/2026.6.2/master target headers, `osd_pico.c` (05, 04 verification) | V |
| PIO instruction budget | `osd_tx.pio.h`, `dshot_pio_programs.h`, UART programs (04 verification #13) | V |
| RTC6705 package and zero authorised stock | RichWave datasheet; LCSC, HQ Online, hqchip, ickey, Digi-Key searches; findchips (04 §2) | V / S (brokers) |
| SE5004L ratings, six-PA shared footprint | Skyworks SE5004L datasheet 202393B; QPA9501, TQP5525, GWQ5929A, RFPA5542, RTC5636H pin tables (04 §3) | V |
| Walsin BPF rejection figures | Walsin PI_RFBPF1608060K98Q1C V01 (04 verification #19) | V |
| TPS61022 limits, forced PWM | TI SLVSDX7D (06 verification #4) | V |
| NextPCB capabilities and prices | nextpcb.com capability pages, stackup DB, instant-quote endpoint (07 verification) | V |
| JLCPCB capabilities | https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-07 | V |
| Stock figures | LCSC product API (`wmsc.lcsc.com/ftps/wm/product/detail`), 2026-10-07; TI store / Digi-Key from track 03 (2026-10-06); HQ Online from tracks 04/06/07 | V (LCSC) / S (others) |
| Motor currents 9-12 A on fresh HV packs | BetaFPV and Happymodel load tables (02 §4) | V / I (scaling) |
| BT2.0 9 A / 15 A | betafpv.com BT2.0 page (06 verification #12) | V |
| Thermal model numbers | 03 §7 and 06 §4 with their verification corrections | I |
| House IMU risk ranking | OpenFC-Lite-Mini `hardware/research/imu-selection/README.md` (05 verification #11) | S |
| OpenDrone sheet reuse and the SX1281 pin-5 defect | sibling netlists via kicad-cli 10 (09 verification #10) | V |
| Area and outline numbers | scratchpad `spec/outline.py`, `spec/budget.py` (this freeze) | I |
