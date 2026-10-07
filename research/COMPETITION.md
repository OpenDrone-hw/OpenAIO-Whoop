# Competition: 1S whoop all-in-one boards (October 2026)

What OpenAIO-Whoop is measured against. The board itself is a proposal in
[DESIGN-SPEC.md](DESIGN-SPEC.md); nothing here describes it as built.

Date 2026-10-07, revised the same day after spec review rounds 2 and 3 (ESC
comparison on the D12 stage and model v3, §2.4; pogo USB adopted, §3; BEC
figures, the O4 Lite and the D20 model ratings, §8). Sources: maker pages and Shopify/WordPress product JSON,
Betaflight `betaflight/config` (1e3f778), Bluejay (0368d11), AM32 (5023414) and
ExpressLRS/targets (42ed776) source, datasheets, BetaFPV product photos measured
locally, NBD's published LionBee schematic, retailer and forum pages where no
primary source exists. Tags: **V** primary source, **S** secondary, **I**
inferred. "n/p" = not published.

---

## 1. The 1S class

### 1.1 1S analog 5-in-1 (FC + ESC + RX + VTX + OSD)

| Board (first listing) | Outline / mount | Weight | MCU / gyro | ESC (firmware build, rating) | RX | VTX / OSD | Price | St |
|---|---|---|---|---|---|---|---|---|
| **BetaFPV Matrix 1S 5IN1 II** (2026-01-29) | 26.35 mm body, 30.9 mm with 3 ears; 26 x 26 3-point | 3.76 g pads / 4.13 g plugs (no antenna) | STM32G473CEU6 / 6-part IMU lottery | 4x EFM8BB51, Bluejay `A_X_5_96`, 12x AGM210MAP P+N; "12 A cont / 18 A peak" | ESP8285 + SX1281 serial, +13 dBm | RTC6705 + RFPA5542 (EOL) + MM32F003, 25-400 mW / AT7456E | $54.99 | V |
| BetaFPV Air 1S 5IN1 (2024-07-11) | 26 x 26, 0.8 mm | 3.6 g | G473 / ICM42688P | BB51 `A_X_5_96`, 5 A | serial ELRS | RTC6705A + RFPA5542 + GD32F310 / "custom miniature OSD" | $49.99 | V |
| BetaFPV Matrix 1S 5IN1 gen 1 (2024-11-19) | 26 x 26, 1.0 mm | 3.92 g | G473 / ICM42688P, BMI270 from 2026-01 | BB51 `A_X_5_96`, 5 A / 8 A | ESP8285 + SX1281 | RTC6705 + RFPA5542 / AT7456E | $49.99 | V |
| Happymodel CrazybeeG473 V1.0 (2025-08-12) | 25.5 x 25.5 | 3.8 g | G473 / ICM42688P or LSM6DSV16X | BB51 `A_X_5_96` Bluejay 0.21, 5 A / 6 A | serial ELRS (EP1/EP2 target) | OpenVTx 10-400 mW, SA 2.1 on UART4 / AT7456E | $83.99 (S) | V |
| Happymodel SuperX ELRS V1/V2 (2024) | 25.5 x 25.5 | n/p | F411 + ESP32-PICO-D4 / BMI270 | BB21 `O_H_5_48`, 5 A / 6 A | ESP32 ELRS that **also drives the VTX** (MSP) | OpenVTx 0-400 mW / SPI OSD | n/p | V |
| NBD Hummingbird RaceSpec V2 (2025-07-09) | 29 x 29 x 7.6; 25.5 | 4.71 g incl. antennas, lead | AT32F435 / ICM42688 | Bluejay 0.19.2 48 kHz, **double N**, 18 A | ESP8285 UART, ceramic antenna | "SmartMax" 25-400 mW / NBD7456 | $59.99 | V |
| Emax Nanoscout AIO / Pro (2026) | "25 x 25" | n/p | F411 / G473 (Pro) | 6 A / 6-8 A | SPI ELRS (AIO) | 25-400 mW | in BNF | S |
| iFlight BLITZ F411 1S 5A | 29 x 29; 25.5 | 4.4-4.8 g | F411 / BMI270 | BLHeli_S `O_H_30`, 5 A / 6 A | SPI ELRS / CC2500 | 25/50 mW | n/p | S |
| T-Motor F411 1S 6A | 25.5 | n/p | F411 | Bluejay, 6 A | SPI ELRS | 50 mW | n/p | S |

### 1.2 1S without onboard analog VTX (HD, 3/4-in-1)

| Board | Outline / mount | Weight | MCU / gyro | ESC | RX | Note | St |
|---|---|---|---|---|---|---|---|
| BetaFPV Matrix 1S 3IN1 / 4IN1 (2025-01) | 25.5 x 25.5 | 3.8 / 3.6 g | G473 / ICM42688P | BB51 `A_X_5_96`, 12 A / 18 A | serial ELRS | BEC "over 3 A down to 2.85 V" (claim) | V |
| BetaFPV Matrix 1S AIO P1 HD (2026-08) | 30.5 x 30.5; 25.5 | 4.60 g | G473 | BB51 `A_X_5_96` | serial ELRS | ArtLynk P1 onboard | V |
| Flywoo GOKU F405 HD 1S 5A V2 | 30.5 x 30.5; 25.5 | 2.6 g (no plugs, BEC module possibly excluded) | F405 BGA | BB21 `O_H_5_48`, 5 A / 8 A | serial ELRS, TCXO | 5 V 3 A BEC to 2.6 V | V |
| Fractal Engineering SP8 Rev04 (2026-08) | 28 x 28; 25.5; two 0.6 mm boards joined | about 4 g | AT32F435 | **AM32 1S**, `SP8_AIO_F421`, DT 25, P high side, 8 A | serial ELRS | 5 V 2 A to 1.8 V; schematics "will be published" | V |
| Caddx AXON 1S V2.0 | n/p | n/p | G473 | "A-X-5", 12 A / 18 A | ELRS 3.5.0 | same claims as Matrix 3IN1 | V |
| JHEMCU F435 NEO 1S | 25.5 | 3.2 g | AT32F43x | Bluejay 5 A | serial ELRS, U.FL | < $30 | S |
| HDZero AIO5 | 25.5 | n/p | F411 | BLHeli_S 5 A | SPI ELRS | HDZero 25/200 mW | S |

### 1.3 1-2S boards (for contrast)

| Board | Weight | ESC build | Rating | Note | St |
|---|---|---|---|---|---|
| Happymodel X14 (2025-10) | n/p (8.3 g per retailer) | BB21 `Z_H_30_48` (DT about 612 ns) | 12 A / 15 A | OpenVTx, AT7456ELAH | V / S |
| NBD BeeBrain BLV5 (2025-10) | 5.8 g | BB21 `Z_H_40` (about 816 ns), double N | 18 A | diversity TCXO ELRS | V |
| TBS Lucid AIO 1-2S (2025-02) | 4 g | AM32, DT 120 (about 1.0 µs), P high side | 7 A / motor | Crossfire RX | V |
| BetaFPV F4 1S 12A V3 (1-2S) | 4.23 g | BB51 `C_X_70_48` (about 1.43 µs) | 12 A / 25 A | no OSD | V |
| Flywoo GOKU 1-2S 12A V2 | 4.9 g | BLHeli_S `Z_H_30` | 12 A | 9 V rail | V |

Same-family pairs put 2S capability at **+0.9 to +2.3 g** (V weights, I
reading), plus 0.3-0.75 W per motor of extra dead-time loss at 1S on the long
dead-time builds. The flagship tier (Matrix II, RaceSpec V2, CrazybeeG473, SP8,
Caddx) is 1S only.

---

## 2. Matrix 1S 5IN1 II deep dive

### 2.1 Photo measurements

Two independent measurements of BetaFPV's product photos (owner photos at about
35 px/mm; 1600 px shop photos at 28.86 px/mm calibrated on the 26.0 mm hole
pattern; ±3 %). Side naming differs between the two analyses: BetaFPV calls the
G473 side TOP; the first analysis called the BB51 side top. Below uses BetaFPV's
names.

| Item | Measured | St |
|---|---|---|
| Body | 26.25-26.41 mm square (26.35 ± 0.3) | V (photo) |
| Overall incl. ears | 30.9 x 30.9 mm along the body axes, 41.7 mm tip to tip on the diagonal | V |
| Mounting | holes on 26.0 mm (BetaFPV spec; photos cannot separate 25.5 from 26.0), square rotated 45° to the flight axis, holes at left, right and rear; front corner rounded (about 2.4 mm set-back) | V |
| Holes | Ø 3.48-3.57 mm, plated, on 4.8 mm OD ring ears | V |
| Outline area | 737 mm² incl. holes, about 709 mm² net per side | V |
| Thickness | 1.0 mm (Air: 0.8 mm) | V |
| Smallest passive | 0201 (0.6 x 0.3 mm); no 01005 seen at a resolution that would show it | V |
| Spacing | 0201 arrays 0.25-0.3 mm body to body; 0201 to QFN toe 0.15-0.25 mm; FET to FET 0.4-0.8 mm; parts to edge 0.2-0.3 mm | V |
| Coverage | about 45 % package body per side (about 50 % with pads); 270-310 placements, about 0.4 per mm² | I |
| Outer layers | almost no visible traces: routing is on inner layers; vias next to pads, consistent with through vias | V / I |
| Silkscreen | outline corners and pad labels only, no reference designators | V |

### 2.2 Blocks

| Block | Part | Package | St |
|---|---|---|---|
| FC | STM32G473CEU6, 8 MHz crystal (HSE 8 in the target) | UFQFPN-48 7x7 | V |
| IMU | lottery: ICM42688P, ICM42605, ICM42622P, LSM6DSK320X, LSM6DSV16X, BMI270 (the BMI270 build applies a −135° offset) | LGA-14 | V (BetaFPV notes) |
| Blackbox | PUYA PY25Q128HA, 16 MB | WSON-8 6x5 | V |
| OSD | AT7456ELAH (MAX7456 clone) + 27 MHz | LGA-16 4x6.8 | V / S |
| Current sense | "R001" 1 mΩ shunt + SOT-23-5 amp, scale 750 | 1206 class | V |
| BEC | "5V, Max 3A"; earlier boards TPS63070 ("3070"); Matrix II part unread ("3P78" on one photo set matches no TPS6307x code) | QFN 2.5x3 + 2520-3025 inductor | V / unknown |
| ESC MCU | 4x EFM8BB51F16G, Bluejay `A_X_5_96` V0.19.2 | QFN-20 3x3 | V |
| ESC FETs | 12x AGMSEMI AGM210MAP, one complementary pair per package per phase; 4 on TOP, 8 on BOTTOM | PDFN 3.3x3.3 | V |
| RX | ESP8285 + SX1281, 26 and 52 MHz references, no PA/LNA (ELRS `Generic 2400`, `power_values [13]`), wire antenna through "RX-ANT", separate Wi-Fi chip antenna | QFN-32 5x5 + QFN-24 4x4 | V |
| VTX | RTC6705 (marking sanded) + 8 MHz; Qorvo RFPA5542 PA (EOL 2023-10-18, LTB 2024-05-30); MM32F003 VTX MCU on SmartAudio (UART2); U.FL | QFN-40 6x6, QFN-20 4x4, QFN-20 3x3 | V / S (EOL dates) |
| USB | SH1.0 4-pin vertical + Type-C adapter in the box; no receptacle | | V |
| Motors | JST1.25 headers (solder-free) or large pads with small plated holes (solder-required) | | V |

### 2.3 Betaflight target BETAFPVG473_V2 (V, config.h 2025-12-01)

Motors PB0, PB1, PC6, PA4 (DShot bitbang); LED strip PB2; beeper PA8 inverted;
LEDs PB6, PC4; UART1 PA9/PA10 (pads), UART2 PA2/PA3 (VTX SmartAudio), UART3
PB10/PB11 (onboard ELRS), UART4 PC10/PC11 (not broken out); SPI1 gyro (CS PC14,
EXTI PC15, CW180), SPI2 OSD, SPI3 flash; ADC VBAT PA0, current PA1, scale 750.
BetaFPV tells owners not to flash official Betaflight because of the IMU
lottery; upstream config has listed all four production IMUs since 2026-05-14,
so that warning is now stale.

### 2.4 The honest-rating check

The ESC is a P+N half-bridge driven straight from the EFM8 GPIO, with the EFM8 on
the cell. In every commutation step the current flows through **two FETs in
series**: the high-side P for the whole step and either the PWM'd N or the
damping P. With AGM210MAP at the cell's gate voltage the hot path is about
34 mΩ.

| Motor current | Loss per motor (spec model, `thermal_v3.py`, typ Rds hot, `A_X_5_96`) | Four motors |
|---|---|---|
| 6 A | 1.5 W (2.1 W at max Rds) | 6.0 W |
| 12 A | 5.7 W (8.2 W at max Rds) | 23 W |
| 18 A (Vgs 3.0 V) | 13.8 W | seconds only |

A 4 g, 26 mm board cannot shed 20 W. The 03 §7 model put the stage near **5 A
continuous, 12 A for about 5-9 s, 18 A for about 2-4 s** at h ≈ 60 W/m²K. The spec's
model (DESIGN-SPEC §4.3, `thermal_v3.py`), which adds the PA-case term and the
rest-of-board heat of an OpenAIO-Whoop-class board, gives the AGM210MAP stage 5.7-5.9 A on
one channel and 3.2-3.8 A on all four at h 80, and 12 A for 3.3-4.7 s at h 55 and
5.5-7.3 s at h 80 (track 03's figures above come from its own model); the Matrix's own non-ESC heat
(RFPA5542 at 5 V, G473 + AT7456E, ESP8285) is unknown, so its real figure is for the
bench. With the verified in-flight range (h 30-80 W/m²K) the continuous figure moves
with airflow and drops well below 5 A at the low end. Either way "12 A continuous" is a
burst figure (I, 01 §3.2, 03 §7 and its verification #15).

No claim is made that OpenAIO-Whoop's stage is better: per D12 it uses TI CSD25310Q2 +
CSD13202Q2 (40 mΩ hot path against the AGM210MAP's 34 mΩ), and the model gives it
0.8-1.0 A less continuous and a quarter to a half of the 12 A burst time at the same
airflow (the SON 2x2 spreads heat worse than a PDFN 3.3). The comparison that counts is
protocol V4 run on both boards on the same rig.

### 2.5 Known issues

| Issue | St |
|---|---|
| IMU lottery and custom firmware ("do not flash official Betaflight") | V |
| Alpha Betaflight shipped on an RTF quad (Air65 II on 2026.6.0 master) | V / S |
| BetaFPV crash test: 2 of 4 Air75 II (Matrix II) boards failed within 20 wall hits | V |
| VTX burns if powered without an antenna; factory default 400 mW | V |
| Reflashing other Bluejay dead-time builds risks "stalling and burning" | V |
| UART3 tied to the onboard RX; freeing it needs a resistor removed | V |
| EOL PA: continuity depends on BetaFPV's stock | V / S |
| No onboard USB; losing the adapter means no configuration | S |
| Silent hardware revisions (V2.0 / V2.1 silkscreen) | V |

---

## 3. FusionFPV UD 4IN1 (public prototype)

From the public page, https://fusionfpv.com/aio/ (October 2026): 1S LiPo/LiHV
racing AIO for undermounting; PCB 39.32 x 25.76 mm, 4 layers, 0.8 mm high-Tg
FR-4; STM32G473CEU6; BMI270 with a dedicated low-noise supply; 4x EFM8BB51,
Bluejay 48 kHz; 12x Vishay SiA517DJ complementary pairs, 2 of 3 per motor on the
front (power stage split across both sides); design target 5 A continuous per
ESC; W25Q128 16 MB; RTC6705 + RTC6659-series PA with OpenVTX-based control,
hardware VTX OFF, 25/100/250/MAX levels, PA detector feedback; AT7456E OSD on
the back; U.FL; **external** serial receiver (reason given: board flex cracks
solder joints under an integrated RX chip); camera 5V/GND/video; USB through 4
pogo contacts and a clip-on USB-C adapter with two different-size alignment
holes; LED strip, SWD, 2 status LEDs, ESC programming points; vbat, current and
PA-detector sensing; open camera bay. (V, page)

Evaluation (I, 03 model with datasheet values): SiA517DJ is a 12 V / ±8 V part
with N 24/29 and P 50/61 mΩ at 4.5/2.5 V; the hot path is about 107 mΩ. At
1 W per motor that is about 3 A; 5 A dissipates about 2.7 W per motor, so the
5 A target is optimistic. Its P die Crss/Ciss (0.42) gives the lowest Cdv/dt
margin of the parts compared. Its other choices are data points we adopt or
reject in DESIGN-SPEC: external RX (rejected, Matrix parity needs onboard),
pogo USB (adopted in round 3: 4 pogo pads with two different-size alignment holes
and a clip-on adapter, D18, because the SH1.0 plug cost about 34 mm² on a bottom
side over budget; BetaFPV adapter compatibility is given up), RTC6659 PA (not
stocked), AT7456E (not needed on RP2354A), G473 (fallback only).

---

## 4. Other boards worth knowing

| Board | Why it matters | St |
|---|---|---|
| NBD LionBee (1S 18650 long-range AIO, 25.5 x 82 mm, 2025-12) | The only published 1S analog AIO schematic (Altium PDF, no layout, no BOM, no licence): RTC6705 + SE5003L PA, NBD7456 OSD, SX1280 SPI ELRS, ICM42688, 12x SiZ340DT N+N with one 1SS400G diode per phase (bootstrap, I), 2x TPS61022 boost, AD8605 current amp, 1 mΩ 1206 shunt. AM32 `LIONB_G_F421`, DT 60, N+N | V |
| NBD RaceSpec V2 | 1S **double-N** at 18 A: needs a gate rail above the cell even at 1S; trades parts for lower Rds | V / I |
| Happymodel SuperX / X12 Pro | The ELRS receiver MCU (ESP32-PICO-D4) drives the RTC6705 itself (ELRS `devVTXSPI` + `MSPVTX`), so there is no VTX MCU and no FC driver | V |
| Fractal SP8 | First 1S AM32 whoop-size board; P high side at DT 25 (about 208 ns) proves short dead time on AM32 too; two-board FC/ESC split for repair | V |
| TBS Lucid AIO 1-2S | AM32 level-shifted P at DT 120: why 1-2S boards are slow at 1S | V |
| fishpepper tinyPEPPER / tinyFISH / tinyFINITY (2017-2019, CERN-OHL v1.2) | The open ancestors: EFM8 + P+N direct drive 1S ESC (tinyPEPPER, 4.3 A), F3 FC with blackbox, RTC6705 + software OSD VTX. Same ESC topology as the Matrix, nine years earlier | V |
| OpenOSD-X (GPL-3.0, 2025-2026) | G431 software OSD + VTX controller reference schematics (RTC6705 + RTC6671 at 3.3 V, or RFPA5512) | V |

---

## 5. Architectures seen in teardowns and firmware

### 5.1 ESC power stage

| Architecture | Who | Extra parts vs P+N direct | Firmware signature | St |
|---|---|---|---|---|
| P+N direct GPIO, EFM8 on the cell, 1S only | BetaFPV Air/Matrix/P1, Happymodel CrazybeeG473/SuperX, Flywoo 1S, Caddx | 0 | Bluejay `A_X_5_96` (BB51) or `O_H_5_48` (BB21): low-side PWM, COM active low, DT about 102 ns | V / I |
| P+N direct, AM32, 1S | Fractal SP8 | LDO for the 3.3 V AT32 | `USE_INVERTED_HIGH`, DT 25 | V |
| N+N with bootstrap, 1S | NBD RaceSpec V2, NBD LionBee | gate rail + diode/cap per phase | Bluejay 48 kHz (layout n/p); AM32 DT 60 | V / I |
| P+N with level shift, 1-2S | TBS Lucid, NeutronRC 1-2S | 12 N-FET + pull-up, MCU LDO | AM32 DT 120-140 (about 1.0-1.3 µs) | V / I |
| N+N + bootstrap, 1-2S | BetaFPV F4 1S 12A 2022 (12x SiZ322DT + Schottky per phase), Happymodel/Flywoo 1-2S | about 36 parts + gate supply | Bluejay/BLHeli_S `C_X_30/70`, `Z_H_30/40` (0.6-1.4 µs) | S / V |
| N+N + driver IC, 2S+ | iFlight Defender (FD6288), BetaFPV 2-3S | 4 drivers + boost rail | `Q_H_50`, `C_X_70` | S |

No three-phase pre-driver in the surveyed set runs from a 3.0-4.35 V cell
(FD6288 needs 5-20 V with a 4.2-5.0 V UVLO; NSG2065Q 8-20 V; DRV8328 4.5 V min
and doubles to a 9 V gate rail).

### 5.2 VTX control

| Architecture | Who | Cost | St |
|---|---|---|---|
| Separate VTX MCU on SmartAudio | Matrix (MM32F003), Air (GD32F310), Happymodel CrazybeeG473/X14 (OpenVTx on GD32F130) | QFN-20/28 MCU + passives + an FC UART + a third firmware | V |
| ELRS RX MCU drives the VTX | Happymodel SuperX / X12 Pro (ESP32) | none; works only on ESP32/ESP32-S3 (ELRS 4.x excludes the C3) | V |
| FC-integrated driver | FusionFPV UD 4IN1 ("target in development") | new Betaflight code | V (page) |
| Betaflight RTC6705 driver | legacy SPRacing and others; no whoop | 2 power levels, no PA loop; undefined on RP2350 | V |

### 5.3 Power and RX

BEC: 1S boards use a boost (or buck-boost on 1-2S); makers now state the input
floor (BetaFPV 2.85 V, Flywoo 2.6 V, Fractal 1.8 V). Analog-OSD chips are all
MAX7456 clones (AT7456E, NBD7456). RX: serial ELRS on ESP8285 (Matrix, RaceSpec
V2) or ESP32/ESP32-C3; SPI ELRS survives on F411 boards only.

---

## 6. Real motor currents

Maker bench tables at about 3.8 V (BetaFPV) or a flat 3.7 V (Happymodel),
scaled with I ∝ V² for a fixed prop (exponent checked at about 2.0 on the
BetaFPV 1102 table). (V tables, I scaling)

| Motor / prop | Bench | → 4.35 V (fresh HV) | → 3.40 V (sagged) |
|---|---|---|---|
| BetaFPV 0702 36000KV, GF1207-3 (65 mm) | 7.17 A @ 3.84 V | 9.2 A | 5.6 A |
| BetaFPV 0702 30000KV | 6.03 A @ 3.86 V | 7.7 A | 4.7 A |
| BetaFPV 0702 25000KV | 3.86 A @ 3.88 V | 4.9 A | 3.0 A |
| Happymodel SE0702 28000KV, GF1219-3 | 4.74 A @ 3.7 V | 6.6 A | 4.0 A |
| BetaFPV 0802 28000KV, GF1614-3 (75 mm) | 9.00 A @ 3.81 V | 11.7 A | 7.2 A |
| BetaFPV 0802 25000KV | 8.15 A @ 3.82 V | 10.6 A | 6.5 A |
| BetaFPV 0802 22000KV | 5.90 A @ 3.86 V | 7.5 A | 4.6 A |
| Happymodel EX1002 20000KV (Mobula7 1S) | 5.99 A @ 3.7 V | 8.3 A | 5.1 A |
| BetaFPV 1102 21000KV, GF1811-3 (Meteor75 Pro II) | 9.18 A @ 3.81 V | **12.0 A** | 7.3 A |

Reading: full throttle on 65-75 mm 1S is 6-9 A per motor on the bench, 9-12 A on
a fresh HV pack, 5-7 A once the cell sags. Hover on a 22-28 g whoop is about
0.5-0.8 A per motor; measured average pack current in flight is about 3.6-4.8 A
(Air65 / Air65 II reviews, S). An honest 8 A continuous board covers 0702 and
the lower-KV 0802 builds; 1102 21000KV on fresh packs needs 12 A bursts, which
is what "12 A" should mean.

---

## 7. Pain points

| # | Pain point | Evidence | St |
|---|---|---|---|
| 1 | ESC burnout on 5 A boards, ratings that do not match the FETs | forum: "pretty all using the same 4,5a fets and write various numbers in the specs"; Fractal markets "No 4.5A mosfets" | S / V |
| 2 | Integrated analog VTX: heat, flicker, power spread | Air 5-in-1 VTX "flickers when hot" (forum); BetaFPV's own "Output Power anomaly" fix; NBD thermal "SmartMax" | S / V |
| 3 | Firmware fragmentation and the gyro lottery | Matrix II custom hex and "do not flash official"; Happymodel and NBD custom hexes; targets merged after launch | V |
| 4 | BEC claims and brown-outs with sag | "ALL the boards claim 5v 3A BEC"; aftermarket boosters exist because HD units brown out below 2.8 V | S / V |
| 5 | SPI ELRS lock-in (FC build fixes the ELRS major version) | Betaflight `USE_ELRSV4` build option; NBD ships separate v3/v4 hexes | V |
| 6 | Whole-board loss on one failure, no repair data | X12 owner had to ask the maker to identify a burnt LDO | S |
| 7 | 1-2S boards are weak at 1S | Happymodel: raise startup power to 1100-1200 on 1S | V |
| 8 | Current-sensor scale wrong or undocumented | forum requests for factory `ibata_scale` | S |
| 9 | Tiny pads and soldering damage | Happymodel: welding errors void warranty; BetaFPV: iron < 370 °C, 1-2 s | V |
| 10 | ESP8285 receivers ageing out of ELRS | NBD: ESP8285 "no longer part of the official ELRS guideline" | V |
| 11 | Mounting-pattern chaos (25.5 vs 26 vs 26.5) | BetaFPV 26 on Matrix, 25.5 on its own Air65 II frame | V |

---

## 8. The opening

| Axis | Bar today | Where an open board can beat it |
|---|---|---|
| Openness | no whoop-size maker publishes schematic + layout + BOM (NBD publishes one schematic PDF for a non-whoop board; Fractal promises) | full KiCad sources, BOM, repair map under CERN-OHL-S |
| ESC rating | "12 A" burst figures on 34 mΩ stages, no test conditions | a rating measured to a published protocol (V4) with every part inside its own rating and the airflow stated, run on a Matrix II on the same rig. Not a stronger stage: the D12 stage is 40 mΩ against 34 mΩ, and the model puts both near 5-6 A on one channel at h 80 and far lower at h 55. Model figures published beside the measurement (D20; 25 °C, VTX 25 mW, h 64-80): analog mode 4.3-5.2 A on one channel / 3.0-3.8 A on all four (4.7-5.1 / 2.8-3.3 A at h 80 with the PA-case limit, DESIGN-SPEC §1), HD mode 4.9-5.6 / 3.5-4.1 A; bursts measured only; 1S only |
| Firmware | custom hexes, IMU lottery | upstream Betaflight target, one gyro per revision, stock Bluejay build, ELRS target JSON |
| RX | ESP8285 | ESP32 on mainline ELRS 4.x that also drives the VTX (no VTX MCU) |
| VTX | EOL PA, sanded markings, no calibration data | in-production PA, harmonic filter, measured power table per channel |
| BEC | "5 V 3 A" with no input condition | a stated input condition: calculated nominal peak 1.67 A at 2.8 V, 1.82 A at 3.0 V, 1.98 A at 3.2 V (TI method, −30 % inductance, η 0.85-0.87; the same figures as DESIGN-SPEC §4.2 and §5.3), and the measured continuous curve per input voltage and board temperature as the published figure, for the analog and the HD load |
| Digital VTX | separate HD boards (Matrix 1S 3IN1 HD) | DJI O4 Lite pads with a switched, sag-shed supply on the same board as the analog VTX, one system at a time (D13-D17) |
| Mounting | 26 or 25.5 | 25.75 mm pattern with grommet holes fits both |
| Repair | none | C2 pads per ESC, SWD, boot pads, through-hole battery and motor wire anchors |
| Price | $50-60 | not credible to beat at prototype volume |

---

## Sources

- BetaFPV Matrix 1S 5IN1 II product page and JSON: https://betafpv.com/collections/flight-controllers/products/matrix-1s-5in1-ii-brushless-flight-controller ; https://betafpv.com/products/matrix-1s-5in1-ii-brushless-flight-controller.json (V)
- BetaFPV product photos (Shopify CDN), measured locally (V, photo)
- BetaFPV support article, firmware history and IMU list: https://support.betafpv.com/hc/en-us/articles/54655791332761 (V)
- BetaFPV Air65 II page (crash test): https://betafpv.com/products/air65-ii-brushless-whoop-quadcopter (V)
- BetaFPV Air, Matrix v1, Matrix 3IN1/4IN1, P1, F4 1S boards: betafpv.com product JSON (V)
- BetaFPV motor load tables (0702, 0802, 1102 2026): Shopify CDN images (V)
- betaflight/config `configs/BEFH/BETAFPVG473_V2/config.h` and the other targets cited: https://github.com/betaflight/config (V)
- Bluejay `src/Layouts/BB51/A.inc`, `src/Bluejay.asm`: https://github.com/bird-sanctuary/bluejay (V)
- AM32 `Inc/targets.h`: https://github.com/am32-firmware/AM32 (V)
- ExpressLRS targets and `src/src/rx_main.cpp`: https://github.com/ExpressLRS/targets , https://github.com/ExpressLRS/ExpressLRS (V)
- AGMSEMI AGM210MAP datasheet VER2.72 (LCSC C7431169) (V)
- Vishay SiA517DJ datasheet (LCSC C469328) (V)
- FusionFPV UD 4IN1 public page: https://fusionfpv.com/aio/ (V)
- Happymodel product posts (happymodel.cn WordPress REST): CrazybeeG473, X14, SuperX, X12 (V)
- NewBeeDrone RaceSpec V2, BLV5, LionBee product JSON and `LonBee_V1_Schematic.pdf`: https://newbeedrone.com (V)
- Fractal SP8: https://store.fractalengineering.net/sp8-aio/ ; Pyrodrone listing (V / S)
- TBS Lucid manual: https://www.team-blacksheep.com/media/files/tbs-lucid-manual.pdf (V)
- Flywoo GOKU pages: https://www.flywoo.net (V)
- fishpepper tinyPEPPER / tinyFISH / tinyFINITY: https://github.com/fishpepper (V)
- OpenOSD-X: https://github.com/OpenOSD-X/OpenOSD-X (V)
- OpenVTx: https://github.com/OpenVTx/OpenVTx (V)
- IntoFPV forum archive threads 27976, 28019, 27029, 26818 (S)
- Oscar Liang reviews (Air65, Air65 II) (S)
- Retailer pages for Emax, iFlight, T-Motor, GEPRC, HGLRC, JHEMCU, HDZero (S)
