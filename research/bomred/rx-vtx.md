# BOM reduction track: RX + VTX integration

Date 2026-10-09. Read-only review, no repo files edited.

**Inputs.** `hardware/bom_plan.json` (329 entries, 282 BOM parts, 88 lines), part positions from the placed floorplan
`hardware/OpenAIO-Whoop.kicad_pcb`, `research/DESIGN-SPEC.md` §4.7, §4.8 and §11, `PINMAP.md`, `FLOORPLAN.md`, and the
sibling `OpenRX-Lite-UFL` schematics (kicad-cli BOM and netlist export).

**Firmware sources.**
- ExpressLRS (ELRS) at `8c51826` (cached clone) and `origin/master` `15c7899` (2026-10-08), plus tags 3.5.6, 4.0.1 and 4.1.0.
- ELRS targets at `42ed776`.
- Betaflight at `03abf1e` (2026-10-07).

**Labels.** V = verified (primary source read), S = screened (distributor or aggregator), I = inferred.

## 0. Bottom line

1. **The owner is right that the ESP32 + external flash is the heavy part of the RX, and the plan under-counts it.**
   - The plan's ESP32-D0WD-V3 has CAP2 (pin 47) and CAP1 (pin 48) in our own symbol, but `bom_plan.json` has no network on them.
   - The ESP32 datasheet requires that network, so the real D0WD block is **3 parts larger** than planned and has **2 more lines** (§1.2).
   - The external GD25Q32EEIGR is an 85 °C part placed **inside the PA shadow** on the floorplan, which breaks rule H3 (§1.3).
2. **The ESP32-C3 cannot drive the VTX on ELRS 4.x (V).** The claim holds, with file and line evidence in §2.
   - The cause is more than a one-line guard: the C3 has only one general-purpose SPI controller, so the RTC6705 would have
     to share the radio's bus in the radio's own execution context.
   - Pins are also short: 15 usable GPIO against 15 needed, and none left for the patched functions.
   - So the OpenRX-Lite-UFL block (ESP32-C3FH4 + SX1281) cannot replace the RX + VTX controller "as is". The FC cannot
     drive the VTX either: Betaflight compiles the RTC6705 driver out on RP2350 and the FC has no free GPIO.
3. **The real in-package-flash lever is the classic ESP32 SiP, ESP32-PICO-V3.**
   - It integrates the flash, the 40 MHz crystal, the CAP network and most bypass capacitors.
   - Result: **−11 parts and −2 lines against the plan (−14 parts and −4 lines against the corrected baseline)**, at
     **about +11 mm² on the bottom**.
   - It runs the stock ELRS ESP32 build, with a JSON-only layout change.
   - Cost: it is an 85 °C part (in-package flash), so it must leave the PA shadow. That needs a P2 re-placement of the
     bottom front quadrant.
   - The ESP32-U4WDH (same land as the D0WD, in-package flash) saves only 2 parts, still needs the CAP network, has the
     same 85 °C problem and has thin stock: not worth it.
4. **Low-risk cuts that hold whichever MCU is kept:**
   - SX1280 → SX1281: the house part, cheaper, and stocked at HQ Online (NextPCB's distributor).
   - 52 MHz TCXO + 2 capacitors → 52 MHz crystal: Semtech reference, internal foot capacitors, −2 parts.
   - Radio decoupling trimmed to the Semtech reference: −2 parts.

## 1. Baseline as planned, and two defects

### 1.1 Parts in the RX block (bom_plan `rx` block, 33 entries) plus the ESP32 side of the VTX interface

| Group | Refs | Count |
|---|---|---|
| ESP32 + flash | U16 ESP32-D0WD-V3, U17 GD25Q32EEIGR, C81 (flash VCC) | 3 |
| 40 MHz crystal | X2 CJ17-400001010B20, C71, C72 | 3 |
| ESP32 enable | R56, C73 | 2 |
| ESP32 decoupling | C74-C79 (6x 0201), C80 (VDD_SDIO 1 µF), C82 (10 µF 0402) | 8 |
| ESP32 misc | R57 (51 Ω LNA_IN dummy, 0402), D4 RGB LED, C83 | 3 |
| SX1280 + reference | U18 SX1280IMLTRT, X3 52 MHz TCXO, C84 (1 nF coupling), C85 (TCXO VCC) | 4 |
| SX1280 decoupling | C86-C93 | 8 |
| RF out | FL1 LPF, AE1 wire hole (DNP, not in BOM) | 2 |
| VTX interface at the ESP32 (vtx block) | R80-R82 (SPI series), R83 (PA_EN series), R84 (GPIO21 series) | 5 |
| **Total** | | **38** (37 in BOM) |

### 1.2 Defect: the ESP32 CAP1/CAP2 network is missing (V)

- **Requirement.** ESP32 Series Datasheet v5.3, Table 2-1:
  - CAP2 (pin 47): "Connects to a 3.3 nF (10%) capacitor and 20 kΩ resistor in parallel to CAP1".
  - CAP1 (pin 48): "Connects to a 10 nF series capacitor to ground".
- **Espressif's own SiP has it.** The ESP32-PICO-V3 internal schematic (PICO Series Datasheet v1.3, Figure 8) holds the
  same R 20 kΩ, C 3.3 nF and C 10 nF.
- **Our side.** `hardware/lib.kicad_sym` ESP32-D0WD-V3 has pins 47 CAP2 and 48 CAP1. No bom_plan entry carries those nets,
  and no 3.3 nF or 20 kΩ line exists.
- **Fix, if any bare ESP32 die (D0WD-V3 or U4WDH) stays:** +3 parts, +2 lines, about +2.0 mm² on the bottom.
  - 10 nF on the existing `GRM033R71...103` line (the plan uses GRM033R61A103KA01J).
  - 3.3 nF 0201 X7R, for example Murata GRM033R71E332KA01D [PU].
  - 20 kΩ 0201, for example Yageo RC0201FR-0720KL [PU].
- **Consequence.** This +3 belongs in every comparison below. It is the reason the SiP option gains more than the plan
  suggests.

### 1.3 Defect: an 85 °C part sits in the PA shadow (V, floorplan geometry)

- **Geometry.**
  - U17 GD25Q32EEIGR ("I grade −40..85 °C", bom_plan note) sits on the bottom at pad extent x 8.81…10.59, y −9.60…−6.20.
  - The PA U20 (top) has pad extent x 6.32…10.72, y −11.40…−7.00.
  - They overlap directly.
- **Rule.** Spec §11 H3: "no heat source ≥ 0.5 W (FET groups, PA, boost) over an 85 °C or TJ-binding part on the other
  side; the PA keeps a 2 mm margin".
- **Why the ESP32 itself is allowed there.** The D0WD-V3 is a −40..125 °C part (datasheet v5.3 §5 note 3).
- **Fix (0 parts).** Move U17 ≥ 2 mm out of the PA projection, or use a 105 °C flash grade (P3).
- **Same constraint for the in-package options.** It decides where the U4WDH or PICO options can go (§4).

## 2. Claim check: "the C3 cannot drive the VTX" (ELRS 4.x)

### 2.1 Evidence

| Item | Evidence | Status |
|---|---|---|
| The VTX devices are registered only for non-C3 ESP32 | `src/src/rx_main.cpp` l. 91-95 (master 15c7899 and 8c51826): `#if defined(PLATFORM_ESP32) && !defined(PLATFORM_ESP32_C3)` around `VTxSPI_device`, `MSPVTx_device` and `Thermal_device`. Same guard at tags 4.0.1 and 4.1.0, l. 90-94 | V |
| The library still compiles for the C3; it is only never started | `src/python/lib_exclusions.py` l. 26-29: an RX build excludes `VTXSPI` only on esp8266 | V |
| ELRS 3.5.x had it enabled for the C3 | 3.5.6 `include/target/Unified_ESP_RX.h` l. 137-141 defines `HAS_VTX_SPI` and `HAS_MSP_VTX` under `PLATFORM_ESP32`, and the C3 env extends the ESP32 env (`-D PLATFORM_ESP32=1`, common.ini l. 54, 116-123) | V |
| When and how the exclusion appeared | Merge commit `4816fc0b` (Paul Kendall, 2025-09-06, "Merge branch '3.x.x-maintenance' into merge"). Its master parent `0c66442` had `#if defined(PLATFORM_ESP32)` only. No commit message states a reason | V (history), reason unknown |
| Market | 6 ELRS RX targets with `vtx_nss`, all classic ESP32 except one DIY ESP32-S3 (HappyModel "AIO 2.4GHz RX+VTX" uses `Generic 2400 Whoop Rx and VTx.json`). None of the **37** `esp32-c3` rx_2400 targets has VTX pins (targets 42ed776) | V |

### 2.2 Technical reasons beyond the guard

- **One general-purpose SPI controller on the C3 (V).** The C3 has SPI0/1 for flash and SPI2 as its only
  general-purpose SPI (ESP32-C3 datasheet v2.4 §4.2.1.2); the classic ESP32 has four SPI interfaces. On the C3 the RTC6705
  must therefore share the radio bus.
  - ELRS supports a shared bus: `devVTXSPI.cpp` l. 87-113 handles NSS and LSB-first, and l. 355-366 uses `&SPI` when
    `vtx_sck == radio_sck`.
  - On a dual-core ESP32 the VTX device runs on core 0 (`lib/DEVICE/device.cpp` l. 24 `MULTICORE (SOC_CPU_CORES_NUM > 1)`,
    l. 70 `xTaskCreatePinnedToCore(... 0)`).
  - On the single-core C3 it runs in the same context as the radio's DIO1 interrupt and SPI traffic. A VTX write with
    LSB-first bit order can collide with a packet read (I). This is the most plausible reason for the exclusion.
  - Re-enabling it is an upstream code change plus a timing validation, not a one-line patch.
- **Pins.**
  - The C3FH4X, C3FH4 and ESP8685H4 each have 15 usable GPIO: 0-10 and 18-21. GPIO11-17 go to the in-package flash or are
    not bonded (C3 datasheet Table 1-1 and note 6; ESP8685 datasheet "15 programmable GPIOs").
  - The RX needs 10: radio SCK, MOSI, MISO, NSS, RST, BUSY and DIO1, CRSF TX and RX, and the LED. Add the BOOT strap
    (GPIO9).
  - The VTX needs 4: NSS on the shared bus, PWM, VPD on ADC1 (GPIO0-4) and VREF.
  - That totals 15, the full budget.
  - The spec's patched functions (GPIO21 = +3V3_VTX LDO enable, GPIO34 = PA NTC) do not fit unless GPIO9 doubles as VTX
    NSS (I).
  - GPIO19 has the USB pull-up at reset, so it cannot carry PA_EN.
- **The sibling cannot be reused "as is" anyway.**
  - Its GPIO10 is tied to GND (netlist: `U1.16 GPIO10` on GND).
  - It carries a Wi-Fi chip antenna and match (AE1, L2, C21, C22), which D18/D25 removed here.
  - It has a 15 µH DC-DC inductor (L4), which the spec deleted.
  - It has its own 5 V → 3.3 V LDO with 3x 10 µF (U2, C8, C10, C11/C16).

**Verdict:** the C3 path (C3FH4X or ESP8685H4) is blocked for the RX + VTX role on ELRS 4.x. It is worth an upstream issue
(ask why 4816fc0b dropped the C3), because the **ESP8685H4 would be the ideal part** if the support returns:
- 4x4 QFN-28 at 0.4 mm pitch, inside NextPCB's 0.38 mm limit;
- −40..105 °C ambient (V, ESP8685 datasheet v1.6 Table 1-1), so it could stay in the PA shadow;
- in-package flash;
- DigiKey 2,830 in stock.

## 3. FC-driven VTX (Betaflight RP2350)

| Item | Evidence | Status |
|---|---|---|
| RTC6705 driver | `src/platform/PICO/target/common/target_RP2350.h` l. 152-153: `#undef USE_VTX_RTC6705`, `#undef USE_VTX_RTC6705_SOFTSPI` (defined for other targets in `common_pre.h` l. 311-312) | V |
| SPI ELRS on the FC (would delete the ESP32 entirely) | same file l. 118-123: `#undef USE_RX_SPI`, `#undef USE_RX_EXPRESSLRS`, `#undef USE_RX_SX1280` | V |
| MSP VTX (the planned path) | `USE_VTX_MSP` in `common_pre.h` l. 348, not undefined for RP2350 | V |
| Pins | PINMAP F14: "no spare GPIO left" (all 30 RP2354A GPIO used); the RTC6705 needs 3 SPI lines + PA bias + PA enable | V |
| Function | The Betaflight RTC6705 driver has no external-PA bias or detector loop. This board's SE5004L needs both | I |

**Verdict:** not available. A separate VTX MCU (the Matrix uses an MM32F003) adds parts and needs a UART the FC no longer
has; the spec already rejected it (§4.7).

## 4. (a) ESP32 variants with in-package flash

| Option | What it removes vs plan | Parts / lines vs plan | vs corrected baseline (with CAP network) | Area (bottom) | Temp | Pitch | ELRS | Stock 2026-10-09 |
|---|---|---|---|---|---|---|---|---|
| ESP32-D0WD-V3 + GD25Q32 (plan) | - | 0 / 0 | +3 / +2 (CAP network missing) | 0 | 125 °C (flash 85 °C) | 0.35 mm (O15 EQ) | stock `Unified_ESP32_2400_RX`, layout `Generic 2400 Whoop Rx and VTx` | LCSC C967021 562; HQ 111 |
| **ESP32-U4WDH** | U17, C81 | −2 / −1 | −2 / −1 (still needs CAP network) | −7.8 mm² | **85 °C** | 0.35 mm, same land | Same build and layout. Datasheet: dual-core since PCN-2021-021 (V). The layout uses neither GPIO16 nor GPIO17, which the flash takes (Table 2-5, V) | **LCSC C20622217 0**; HQ 90; DigiKey 0 (5,000 past due) |
| ESP32-D0WDR2-V3 | nothing: R2 = 2 MB **PSRAM**, not flash; EOL, replaced by D0WDRH2-V3 (Table 1-1 note 7) | - | - | - | - | - | - | not applicable |
| **ESP32-PICO-V3** (SiP 7x7) | U17, C81, X2, C71, C72, C80 (VDD_SDIO is internal), 5 of C74-C79 (Espressif's peripheral schematic Fig. 11 uses only 10 µF + 0.1 µF on VDD33), and the CAP network | **−11 / −2** | **−14 / −4** | **+11 mm²** (land about 7.5 sq. vs 48.2 mm² removed; +9 vs corrected) | **85 °C** | **0.5 mm**: drops out of the O15 EQ (BC847QASZ and 74LVC1T45GS still need it) | Same `Unified_ESP32_2400_RX` build. Needs **its own layout JSON** because GPIO18/23 drive the in-package flash (Fig. 8) and `vtx_mosi` = 18 moves (to GPIO13/14/15). JSON only, the house OpenRX precedent. ELRS has run on ESP32-PICO since #1526 (bd4f4e7f, 2022) | LCSC C967022 335; DigiKey 4,812 (); HQ: V3-02 only, 443 |
| ESP32-PICO-V3-02 | as V3 (8 MB flash + 2 MB PSRAM, 1.11 mm thick) | as V3 | as V3 | as V3 | 85 °C | 0.5 mm | as V3 | LCSC C908392 0; HQ 443 (4-7 days) |
| ESP32-PICO-D4 | as V3 | - | - | - | 85 °C | 0.5 mm | - | NRND (datasheet), LCSC C193707 1,450: no new design |

Notes:

- **Single-core U4WDH question (V/I).**
  - The datasheet now lists the U4WDH as dual-core (PCN-2021-021). The ELRS ESP32 build is a multi-core build (device task
    pinned to core 0).
  - A pre-PCN single-core part would not boot that image: ESP-IDF aborts a multi-core app on a single-core chip (I).
  - Goods-in rule if the part is used: `esptool chip_id` must report a dual-core v3.x chip.
- **The 85 °C limit is binding.** U4WDH and PICO are −40..85 °C ambient because of the in-package flash (ESP32 datasheet
  v5.3 §5 note 3; PICO datasheet "Operating ambient temperature −40 ~ 85 °C").
  - Under the PA they would run at the PA's own 85 °C case limit by construction, and H3 forbids it.
  - On the placed board the only H3-free strip in the bottom front quadrant (x ≤ 4.3 mm, ≥ 2 mm from the ESC4 N row) holds
    the pogo USB J30 (x −2.76…2.05, y −12.8…−10.4), the TPS2116 U3 and the 12 MHz crystal X1.
  - So either option needs a P2 re-placement of that quadrant. The spec (§4.7) already estimated "+17 mm², re-plan" for the
    PICO fallback.
- **PICO strap and flash rules are the same as the D0WD's.** MTDI/GPIO12 must read low at reset for the 3.3 V flash (Fig.
  11 note), which the planned RC already does. The LNA_IN dummy load R57 stays.

## 5. (b) OpenRX-Lite-UFL block, exact BOM (kicad-cli export, 42 parts)

| Function | Refs (MPN) |
|---|---|
| MCU | U1 ESP32-C3FH4 (C2858491, QFN-32 5x5 0.5 mm, land 5.70 sq.) |
| 40 MHz crystal | X1 CJ17-400001010B20; C1, C3 15 pF; L1 24 nH LQP03TN24NH02D (XTAL_P series) |
| RF supply filter | L3 2.0 nH LQP03TN2N0B02D + C25 1 µF (VDD3P3) |
| Enable, straps | R5 10k + C28 1 µF (CHIP_EN); R4 10k (GPIO9/BOOT); R3 10k (GPIO8/LED); R2 10k (GPIO2/radio RST) |
| Wi-Fi | AE1 2450AT18A100E; L2 2.5 nH; C21, C22 1.2 pF |
| LDO | U2 TLV75533PDQNR; C8, C10 (10 µF, +5V); C11/C16 10 µF |
| Radio | U3 SX1281IMLTRT; OSC1 OW7EL89CENUNFAYLC-52M + C19 1 nF; C20 470 nF + C26 10 nF (VREG); C27 10 nF (VR_PA); L4 15 µH MLZ2012M150WT000 (DC-DC) |
| RF out | FL1 2450FM07D0034T; J1 U.FL-R-SMT-1(80) |
| +3V3 bypass | C4, C15, C23 (1 µF); C5, C6, C9, C12, C13, C14, C17 (100 nF); C24 10 nF |
| LED | D1 XL-1010RGBC-2812B |

Firmware: `Unified_ESP32C3_2400_RX`, layout `OpenRX Lite-UFL 2400.json`. The RX side carries no VTX keys.

**What the C3 path would cost here if ELRS allowed it.** A C3FH4X or ESP8685H4 replacing D0WD + flash would be −U17 −C81,
then +3 parts:

- the GPIO8 pull-up;
- the house XTAL_P 24 nH series inductor;
- the house VDD3P3 2.0 nH filter inductor.

| Variant | Parts vs plan | Parts vs corrected | Lines | Area (bottom) |
|---|---|---|---|---|
| ESP32-C3FH4X | +1 | −2 | +1 | −3 mm² |
| ESP8685H4 | +1 | −2 | +1 | −16 mm² |

Radio RST on GPIO2 needs no resistor, because SX1280 NRESET has an internal 50 kΩ pull-up (datasheet pin table, V).

**Stock.**
- C3FH4: LCSC 0, HQ 89.
- C3FH4X (recommended successor, v1.1 silicon): DigiKey 2,214. It needs ESP-IDF ≥ 4.4.7 (Espressif AR2024-009); ELRS uses
  espressif32@6.12.0 (I: Arduino 2.0.17 / IDF 4.4.7).
- ESP8685H4: DigiKey 2,830, LCSC 0, HQ none.

**Blocked by §2.**

## 6. (c) SX1280 vs SX1281

- **Parity (V).** One datasheet (SX1280/SX1281 Rev 3.2), same QFN-24 4x4 and pinout. Table 1-1: both have LoRa, FLRC and
  GFSK; only the SX1280 has the Ranging and Advanced Ranging engines.
- **ELRS (V).** One driver (`SX1280Driver`); it uses no ranging.
- **Market.** The Matrix II and the house OpenRX use the SX1281.
- **Library.** The OpenDrone library holds SX1281IMLTRT with symbol, footprint and datasheet (PARTS-USED: OpenAIO,
  OpenRX). The spec's pin-5 GND fix still applies to that symbol.

Stock and price on 2026-10-09:

| Part | LCSC | HQ Online | DigiKey |
|---|---|---|---|
| SX1281 | C2151551, 238 | 146 | 2,757 |
| SX1280 | C125969, 757 | no result | 12,706 |

The spec chose the SX1280 only because the SX1281 showed 0 at LCSC on 2026-10-07. With NextPCB turnkey (HQ Online is its
distributor) the SX1281 is the better-stocked and cheaper part.

**Proposal:** SX1281IMLTRT primary, SX1280IMLTRT as the drop-in alternate on the same line note. Parts, lines and area are
all 0. It is a house-part reuse and a cost cut.

## 7. (d) Other integration

| Idea | Change | Parts / lines / area | Evidence | Verdict |
|---|---|---|---|---|
| **TCXO → crystal** | X3 OW7EL89CENUNFAYLC-52M + C84 + C85 → one 52 MHz 2016 crystal on XTA (pin 4) / XTB (pin 6), no load caps | −2 / 0 / −1.3 mm² B | Semtech Rev 3.2 §15.1: the "external crystal reference oscillator exploits internally integrated foot capacitances"; §15.2: the TCXO is optional; the reference BOM uses NDK NX2016SA-52.000000MHz (EXS00A-CS07103, ±10 ppm, CL 10 pF); Table 3-9 CLOAD 10 pF, C0 ≤ 5 pF, ESR ≤ 50 Ω. ELRS SX128x frequency correction spans ±200 kHz (`lib/FHSS/FHSS.h` l. 8-9) = ±82 ppm at 2.44 GHz, against ±10 ppm + temperature drift. Matrix II: 52 MHz 2016 part "BN52.0" (crystal or TCXO not determined); Matrix v1: 3225 crystal. The TCXO and crystal 2016 pinouts differ (no dual land) | **yes**, if P3 finds a stocked −40..85 °C 52 MHz 2016 CL 10 pF part (the NDK reference part showed 0 at LCSC per search, S) |
| **Radio decoupling to the Semtech reference** | drop C93 (10 µF 0402 bulk) and C90 (10 nF VBAT HF) | −2 / 0 / −1.8 mm² B | The Semtech reference BOM (Table 15-1) has 100 nF VBAT, 100 nF VBAT_IO, 10 nF x2 VR_PA and 470 nF VREG: no 10 µF and no second VBAT capacitor. Owner rule "minimal justified capacitance". The +3V3 is a plane with its bulk at the LP5912. The house standalone RX needs its 10 µF only because of its own LDO | **yes**; V7 checks TX droop; C92 1 µF stays as the local reservoir |
| ESP32 LEDC 8 MHz as the RTC6705 reference | X4 (3225) + C94 + C95 deleted; 80 MHz APB / 10 on spare GPIO23 | −3 / −1 / −11 mm² top | Needs an ELRS patch. The PLL-derived square wave has worse phase noise than a crystal, and the RTC6705 multiplies it by about 725 (57 dB). An 8 MHz rail-to-rail trace puts harmonics in the 2.4 GHz band (8 MHz x 300). The clock stops on every ESP32 reset | **no** for rev1 |
| ESP32 DAC (GPIO25/26) instead of PWM + 2-pole RC | delete R71, C124, R72, C125 | −4 / −1 (18 k) / −2.6 mm² top | `devVTXSPI.cpp` l. 27-28, 168, 182, 189-196, 256-273, 375-380: DAC mode clamps to MIN_DAC 1 / MAX_DAC 250 but writes `vtxSPIPWM >> 4`. Pit = 250 → DAC code 15 (0.19 V) while 25 mW = PWM-scale 3300 → 206. On this inverting stage, pit would mean near-maximum drive. Only the DIY "Frank" layout uses it | **no** (firmware defect; re-check if fixed upstream) |
| Share the 40 MHz with another clock | - | - | The ESP32 needs 40 MHz for its PLL and ROM timing; the SX1280 needs 52 MHz (FREQ_STEP = XTAL/2^18, `SX1280_Regs.h` l. 13); the RTC6705 needs exactly 8 MHz (`SYNTH_REG_A_DEFAULT 0x0190`, devVTXSPI.cpp l. 22); the RP2350 needs 12 MHz (USB) | **no** |
| Parts used only by the O6 patch | TH1 + R70 (PA NTC → GPIO34), R84 (GPIO21 series) | −3 / −1 (NTC) / −1.3 mm² top, −0.66 B | No released ELRS RX reads a thermistor: `devThermal.cpp` covers LM75A or a fan only, and `OPT_HAS_THERMAL_LM75A false` (`Unified_ESP_RX.h` l. 97). Stock ELRS never drives GPIO21. The spec makes the O6 patch a release requirement | **owner decision**; keep while O6 stays a release gate |
| Drop the ELRS RGB LED (D4 + C83) | - | −2 / −1 | The Matrix II has an RX LED (market evidence); bind and link status | **no** |

## 8. Proposal table

Areas are per side; negative = saved. "Plan" = bom_plan.json today.

| ID | Change (MPNs) | Parts | Lines | Area | Risk | Recommend |
|---|---|---|---|---|---|---|
| RV-0a | Add the missing ESP32 CAP network: 3.3 nF ∥ 20 kΩ CAP2-CAP1, 10 nF CAP1-GND (GRM033R71E332KA01D [PU], RC0201FR-0720KL [PU], GRM033R61A103KA01J) | +3 | +2 | +2.0 B | none (datasheet requirement) | **yes**, if a bare ESP32 die stays (moot with RV-4) |
| RV-0b | U17 GD25Q32EEIGR (85 °C) out of the PA projection by ≥ 2 mm (H3), or a 105 °C grade | 0 | 0 | 0 | placement only | **yes** (moot with RV-4) |
| RV-1 | SX1280IMLTRT → SX1281IMLTRT (OpenDrone part), SX1280 as alternate | 0 | 0 (−1 project library symbol) | 0 | none; ELRS identical | **yes** |
| RV-2 | X3 OW7EL89CENUNFAYLC-52M + C84 + C85 → 52 MHz 2016 crystal, CL 10 pF (Semtech ref. NDK NX2016SA-52M EXS00A-CS07103) | −2 | 0 | −1.3 B | crystal stock; ±82 ppm correction margin | **yes**, if a stocked part is found |
| RV-3 | Delete C93 (GRM155C80J106ME11D) and C90 (GRM033R61A103KA01J) at the SX1280 | −2 | 0 | −1.8 B | TX droop on the +3V3 plane; V7 checks | **yes** |
| RV-4 | ESP32-D0WD-V3 + GD25Q32EEIGR + X2 CJ17 + C71, C72, C80, C81 + 5 of C74-C79 → **ESP32-PICO-V3** (C967022); keep C82 10 µF, one 100 nF, R56/C73, R57 | **−11** (−14 vs corrected) | **−2** (−4) | **+11 B** | 85 °C → bottom front re-plan out of the PA shadow; JSON layout (no GPIO18/23); LCSC 335, DigiKey 4,812 | **yes, gated by a P2 placement trial** (place a 7.5 mm land ≥ 2 mm outside the PA projection, ≥ 2 mm from FET groups, check_spacing 0); else RV-0a + RV-0b |
| RV-5 | ESP32-D0WD-V3 + GD25Q32EEIGR + C81 → ESP32-U4WDH (same land) | −2 | −1 | −7.8 B | 85 °C (same re-plan as RV-4 for 1/5 of the gain); still 0.35 mm pitch and needs RV-0a; LCSC 0, HQ 90, DigiKey 0 | no |
| RV-6 | OpenRX-Lite-UFL block: ESP32-C3FH4X / ESP8685H4 + 40 MHz crystal + SX1281, VTX on the C3 | +1 (−2 vs corrected) | +1 | −3 (C3) / −16 (ESP8685) B | **ELRS 4.x has no C3 VTX** (rx_main.cpp l. 91); one GP-SPI; 15/15 GPIO | no (upstream issue: the ESP8685H4 is ideal if support returns) |
| RV-7 | VTX driven by the FC (Betaflight RTC6705) | - | - | - | `#undef USE_VTX_RTC6705` on RP2350; 0 spare GPIO; no PA loop | no |
| RV-8 | ESP32 LEDC 8 MHz to the RTC6705; delete X4 TAXM8M4RDBCCT2T + C94 + C95 | −3 | −1 | −11 F | ELRS patch, phase noise, 2.4 GHz harmonics, reset glitches | no |
| RV-9 | PA bias from the ESP32 DAC; delete R71, R72, C124, C125 | −4 | −1 | −2.6 F | ELRS DAC scaling defect: pit = high drive | no |
| RV-10 | Delete the O6-only parts TH1 NCP03XH103F05RL, R70, R84 | −3 | −1 | −1.3 F, −0.7 B | loses the planned thermal derate and RTC6705 power-down patch hooks | no (owner decision) |

**Recommended set.**

| Set | Parts vs plan | Lines vs plan | Bottom area | Note |
|---|---|---|---|---|
| RV-1 + RV-2 + RV-3 + RV-4 | **−15** | **−2** | about **+8 mm²** | −18 parts against the corrected baseline |
| Fallback: RV-0a + RV-0b + RV-1 + RV-2 + RV-3 | −1 | +2 | −1.1 mm² | −4 parts against the corrected baseline; use if the RV-4 trial fails |

## 9. Stock checked (2026-10-09)

| Part | LCSC (API) | HQ Online | DigiKey |
|---|---|---|---|
| ESP32-D0WD-V3 | C967021, 562 | 111 | listed |
| ESP32-U4WDH | C20622217, 0 | 90 | 0 (5,000 past due, est. 30-Sep-2026) |
| ESP32-PICO-V3 | C967022, 335 | - | 4,812, −40..85 °C |
| ESP32-PICO-V3-02 | C908392, 0 | 443 (4-7 d) | - |
| ESP32-PICO-D4 (NRND) | C193707, 1,450 | 365 | - |
| ESP32-C3FH4 | C2858491, 0 | 89 | - |
| ESP32-C3FH4X | not found | - | 2,214, −40..105 °C |
| ESP8685H4 | C4944062, 0 | 0 results | 2,830, −40..105 °C |
| ESP32-C3 (no flash) | C2838500, 3,588 | 312 | - |
| SX1281IMLTRT | C2151551, 238 | 146 | 2,757 |
| SX1280IMLTRT | C125969, 757 | 0 results | 12,706 |
| GD25Q32EEIGR | C2973794, 1,216 | 0 results | - |
| CJ17-400001010B20 | C2875272, 9,070 | - | - |
| OW7EL89CENUNFAYLC-52M | C22434896, 5,955 | 0 results | - |

## 10. Sources

**ExpressLRS** (https://github.com/ExpressLRS/ExpressLRS), at 8c51826 and 15c7899:
- `src/src/rx_main.cpp` l. 91-95; tags 4.0.1 and 4.1.0 l. 90-94; 3.5.6 l. 99-113.
- `src/lib/VTXSPI/devVTXSPI.cpp` l. 22, 27-31, 87-113, 157-196, 250-277, 346-391.
- `src/lib/DEVICE/device.cpp` l. 24, 37-71.
- `src/python/lib_exclusions.py` l. 19-30.
- `src/targets/esp32c3-rx.ini` l. 1-8; `src/targets/common.ini`.
- `src/lib/FHSS/FHSS.h` l. 6-15.
- `src/lib/THERMAL/devThermal.cpp` l. 4, 29-52.
- `src/include/target/Unified_ESP_RX.h` l. 97, and l. 137-141 at 3.5.6.
- History: `4816fc0b`, `0c66442`, `bd4f4e7f`.

**ExpressLRS targets** (https://github.com/ExpressLRS/targets) at 42ed776:
- `RX/Generic 2400 Whoop Rx and VTx.json`
- `targets.json`

**Betaflight** (https://github.com/betaflight/betaflight) at 03abf1e:
- `src/platform/PICO/target/common/target_RP2350.h` l. 118-123, 152-153
- `src/main/target/common_pre.h` l. 200-207, 311-312, 344-348

**Espressif datasheets:**
- ESP32 Series Datasheet v5.3 (https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf):
  Table 1-1, Table 2-1 (CAP1/CAP2), Table 2-5, §5 note 3.
- ESP32-C3 Series Datasheet v2.4: Table 1-1, notes 6/8/9, §4.2.1.2.
- ESP8685 Datasheet v1.6: Table 1-1, Table 2-1.
- ESP32-PICO Series Datasheet v1.3: comparison table, Fig. 8 (V3 internal), Fig. 11 (V3 peripheral), Table 5.
- Espressif AR2024-009 (C3 v1.1 and ESP-IDF versions): https://espressif.com/sites/default/files/advisory_downloads/ar2024-009_en.pdf

**Semtech** SX1280/SX1281 Datasheet Rev 3.2: Table 1-1, pin table, Table 3-9, §15.1-15.2, Table 15-1 (OpenDrone
KiCad-Library `datasheet/SX1281IMLTRT.pdf`).

**Stock pages:**
- LCSC product API `https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=<C>`
- HQ Online `https://www.hqonline.com/search/<MPN>`
- DigiKey:
  - https://www.digikey.com/en/products/detail/espressif-systems/ESP32-U4WDH/12153913
  - https://www.digikey.com/en/products/detail/espressif-systems/ESP8685H4/16676740
  - https://www.digikey.com/en/products/detail/espressif-systems/ESP32-C3FH4X/24366489
  - https://www.digikey.com/en/products/detail/espressif-systems/ESP32-PICO-V3/11613122
  - DigiKey searches for SX1281IMLTRT and SX1280IMLTRT.

**House and repo:**
- `siblings/OpenRX-Lite-UFL/hardware/*.kicad_sch` (kicad-cli export) and `firmware/OpenRX Lite-UFL 2400.json`.
- `hardware/bom_plan.json`, `hardware/lib.kicad_sym`, `hardware/OpenAIO-Whoop.kicad_pcb` (pcbnew pad extents).
- `research/DESIGN-SPEC.md` §4.7, §4.8, §11; `PINMAP.md` §2, F14; `FLOORPLAN.md`.
- `scratchpad/research/01-matrix-1s-5in1-ii.md` (Matrix RX parts).

## Verification

Adversarial check, 2026-10-09. Each proposal was tested against primary sources: the local Espressif and Semtech
datasheet text and figures in `bomred/ds/`, ELRS git at `15c7899` and tags 3.5.6, 4.0.1 and 4.1.0, Betaflight
`03abf1e` `target_RP2350.h` (fetched raw), `hardware/bom_plan.json`, and the placed board read with pcbnew. Stock was
re-read live from the LCSC product API. The test for each proposal: does it break a datasheet requirement, a rating,
firmware support, RF function or an owner rule?

### Verdicts

| ID | Verdict | Evidence (one line) |
|---|---|---|
| RV-0a | **confirmed** | ESP32 datasheet v5.3 Table 2-1 (text l. 944/952): "CAP2 ... 3.3 nF (10%) capacitor and 20 kΩ resistor in parallel to CAP1"; "CAP1 ... 10 nF series capacitor to ground". `lib.kicad_sym` l. 2892/2910 has the pins. No bom_plan part carries a CAP net, and no 20 k or 3.3 nF line exists (88 lines checked). PICO Fig. 8 shows the same R1 20K / C5 3.3nF / C6 10nF. +3 parts / +2 lines is correct (10 nF reuses GRM033R61A103KA01J). |
| RV-0b | **confirmed** | pcbnew on the placed board: U17 (B) pads x 8.81..10.59, y −9.60..−6.20; U20 SE5004L (F) pads x 6.32..10.72, y −11.40..−7.00, a direct overlap. Spec §11 H3 names the PA as a shadow source with a 2 mm margin. The D0WD-V3 beside it is legal there: datasheet §5 note 3 gives −40..125 °C, and 85 °C only for U4WDH/D0WDRH2. The keep-out with margin is x 4.32..12.72, y −13.4..−5.0, so U17 must go west of x 4.3 or south of y −5.0 (P2). |
| RV-1 | **confirmed** | SX1280/1 Rev 3.2 Table 1-1: identical except the Ranging Engine. ELRS `SX1280.cpp` l. 84-86 only checks that the firmware-version register is not 0 or 0xFFFF, and nothing in the driver branches on the variant. LCSC live: SX1281 C2151551 **283** (was 238) @100 vs SX1280 C125969 757 @100 (SX1280 is cheaper only at qty 1-10). HQ snippet: SX1281 146, SX1280 none. |
| RV-2 | **refuted** (as a low-risk recommendation) | The cited margin does not exist. Release ELRS sets SX1280 LoRa to `SX1280_LORA_PACKET_FIXED_LENGTH` (`SX1280.cpp` l. 168-171, also at 3.5.6/4.0.1/4.1.0), so `modeSupportsFei` is false (l. 315), and FLRC forces it false (l. 371). `HandleFreqCorr` (rx_main l. 1174) therefore never runs; `FreqCorrectionMax` is reached only with `-DDEBUG_FREQ_CORRECTION`, which is commented out in `user_defines.txt` l. 93. ELRS's own page agrees: "2.4GHz modules ... can't do online frequency correction". What remains is the modem's own tolerance. For LoRa BW 800 that is ±80 ppm per TX-RX pair (Table 6-3, FERR_L), so a crystal is fine. For FLRC (all 4 ELRS FLRC modes use 0.65 Mb/s, `common.cpp` l. 32-35), §6.3.3.1 says preamble detection drops to "±10 ppm ... for a single radio (so ±20 ppm for the total link)" below 1.04 Mb/s. Table 6-6 gives ±150 kHz instead, so the datasheet contradicts itself. A ±10 ppm crystal plus temperature drift on a board that binds parts at 85 °C cannot be shown to meet ±10 ppm. Keep the TCXO. Re-open only with a V7 hot/cold F500/F1000 link test of a crystal sample. ELRS docs do endorse a "52 MHz XO, 10 ppm, 10 pF" for LoRa rates. |
| RV-3 | **confirmed** | Semtech Table 15-1: C8 100 nF (VBAT_IO), C10 100 nF (VBAT), C5/C6 10 nF (VR_PA side), C9 470 nF (DCC_FB), and no 10 µF and no second VBAT cap. After the cut the plan still holds C86 10 nF, C87 470 nF, C88 10 nF, C89 100 nF, C91 100 nF and C92 1 µF, all at or above the reference. The radio draws 24 mA at 12.5 dBm (DC-DC, IDD_T13), about twice that in LDO mode. Against 1.2 µF local, a plane and the LP5912 (C93 is not its stability cap), droop is negligible (I). Both lines are shared (10 µF x6, 10 nF x5), so lines stay 0. |
| RV-4 | **confirmed**, gated as proposed, with one correction | PICO datasheet v1.3 Fig. 8: in-package 40 MHz crystal, CAP network, flash on GPIO6/11/16/17/18/23, C18 on VDD_SDIO, C19/C4 on RTC/CPU. Fig. 11: external parts are only C1 10 µF + C2 0.1 µF, the EN RC and the optional antenna match. Operating ambient −40..85 °C (l. 163, 2050). Table 4: pins 25, 35, 36, 44 and 45 are NC, so GPIO18 **and GPIO23** are not exposed. **Correction:** the new layout JSON must also move or unset `vtx_miso` (GPIO23, PINMAP §6), not only `vtx_mosi`. Free exposed pins remain: 13/14/15 for MOSI, and 35/38/39 as a dummy MISO. Line math holds: −2 vs plan, because the 15 pF line is shared with C42/C43/C94/C95. ELRS `bd4f4e7f` is "ESP32 PICO RX including the kitchen sink! (#1526)". The vendored esptool decodes package 5 rev3 as ESP32-PICO-V3. LCSC live: C967022 **335**. Bootloader handling of the PICO-V3 flash pins comes from ESP-IDF (I); confirm it at V1 bring-up. The gate (P2 placement ≥ 2 mm outside the PA shadow and ≥ 2 mm from the FET groups, check_spacing 0) stays mandatory. |
| RV-5 | **confirmed** (not recommended) | Datasheet v5.3 Table 1-1 note 3: dual core per PCN-2021-021. §5 note 3: U4WDH limited to 85 °C. LCSC live: C20622217 **0**. Still needs the RV-0a network and the 0.35 mm EQ. |
| RV-6 | **confirmed** (not recommended) | `rx_main.cpp` l. 91-95 at 15c7899: `#if defined(PLATFORM_ESP32) && !defined(PLATFORM_ESP32_C3)` around VTxSPI/MSPVTx/Thermal; the same guard opens `devThermal.cpp` l. 4. |
| RV-7 | **confirmed** (not recommended) | Betaflight `03abf1e` `target_RP2350.h` l. 152-153 `#undef USE_VTX_RTC6705` / `_SOFTSPI`, and l. 118-123 `#undef USE_RX_SPI`, `USE_RX_EXPRESSLRS`, `USE_RX_SX1280`. |
| RV-8 | **confirmed** (not recommended) | `devVTXSPI.cpp` l. 22 `SYNTH_REG_A_DEFAULT 0x0190` (R = 400, fixing an 8 MHz reference for 20 kHz steps). The phase-noise and harmonic arguments are inferred but sound. |
| RV-9 | **confirmed** (not recommended) | `devVTXSPI.cpp` l. 27-28 `MIN_DAC 1` / `MAX_DAC 250` against l. 168 `dacWrite(GPIO_PIN_RF_AMP_PWM, vtxSPIPWM >> 4)` on GPIO25/26: the count scale and the DAC clamps disagree, as stated. |
| RV-10 | **confirmed** (owner decision, not recommended) | `devThermal.cpp` l. 4-8 (`OPT_HAS_THERMAL_LM75A false`, fan pins only); no NTC path in stock ELRS. Deleting the parts removes the O6 hooks the spec makes a release gate. |

### Corrections to the report body

1. **§7 / §8, RV-2.** Delete "ELRS SX128x frequency correction spans ±200 kHz = ±82 ppm". `FreqCorrectionMax` exists in `FHSS.h`, but SX128x release builds never feed it: implicit header, no FEI in LoRa, none in FLRC. The binding limits are the SX1280 modem's: ±80 ppm per link in LoRa BW 800, and ±20 ppm per link in FLRC 0.65 Mb/s per §6.3.3.1 text (Table 6-6 says ±150 kHz). RV-2 moves to **no for rev1** (keep X3 TCXO + C84 + C85). A V7 crystal-sample test across temperature in F1000/F500 can re-open it.
2. **§4 / §8, RV-4.** "vtx_mosi = 18 moves" should read "`vtx_mosi` (GPIO18) and `vtx_miso` (GPIO23) move or are left unset". GPIO23 is the in-package flash DI (Fig. 8 U3 pin 5).
3. **§9.** SX1281 LCSC stock is now 283 (live API, 2026-10-09 PM).

### Revised recommended set (after verification)

| Set | Parts vs plan | Lines vs plan | Bottom area | Note |
|---|---|---|---|---|
| RV-1 + RV-3 + RV-4 | **−13** | **−2** | about **+9 mm²** | −16 parts against the corrected baseline; RV-4 still gated by the P2 trial |
| Fallback: RV-0a + RV-0b + RV-1 + RV-3 | +1 | +2 | +0.2 mm² | −2 parts against the corrected baseline; RV-0a and RV-0b are defect fixes and are mandatory if the D0WD-V3 stays |
