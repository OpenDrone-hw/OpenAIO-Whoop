# OpenAIO-Whoop Design Notes

Detailed design description of the OpenAIO-Whoop. The design is early stage: part selection is done, the ESC schematic and the whoop board layout are not. ESC topology research and sourcing history: [ESC_DESIGN.md](ESC_DESIGN.md). Competitive landscape: [MARKET-RESEARCH-2026-06.md](MARKET-RESEARCH-2026-06.md).

## Architecture

Three stages on one board with a 25.5 x 25.5 mm mounting pattern: flight controller, 4x brushless ESC, serial ExpressLRS 2.4 GHz receiver. Target class is 1S/2S whoops, 65-85 mm. Digital video only: an SH1.0 6-pin HD-VTX port, no analog VTX or OSD hardware.

| Stage | Basis | State |
|---|---|---|
| FC | OpenFC-Lite-Mini rev 2 sheets (RP2354A) | imported |
| ESC | New design: EFM8BB51 (Bluejay BB51) + XR8G02M direct-drive P+N power stage, SiA527DJ qualified second source | parts imported, schematic not drawn |
| RX | OpenRX-Lite (ESP32-C3 + SX1281, serial ELRS) | imported |

## Design state

- Pack voltage (1S vs 2S) is undecided. On top of the locked direct-drive P+N power stage, it decides the per-phase level-shift parts (2S adds a 2N7002 level shift per phase so the P-gate can reach VBAT) and the BEC topology (1S needs a boost to feed a DJI O4 Lite properly).
- ESC power stage is decided: XR8G02M, 2 x 2 mm complementary P+N, GPIO direct drive, no gate-driver IC, honest rating ~8 A continuous / 15-20 A burst per motor. The 12 A dual-N market tier is deliberately not pursued: dual-N needs high-side drive, excluded by the no-driver constraint. Earlier candidates (AGM310MAP, AGM314MAP, N+N plus driver) are superseded; full history in [ESC_DESIGN.md](ESC_DESIGN.md).
- Blackbox: W25Q128JVPIQ 16 MB SPI NOR replaces the microSD slot and the dead BY25Q64; the blackbox sheet still shows the microSD slot until redrawn.
- The ESC channel sheet (`esc_channel.kicad_sch`, instantiated 4x) still contains the inherited AT32/AM32 donor channel from the OpenESC lineage, not the EFM8BB51 + XR8G02M design.
- The board file (`OpenAIO-Whoop.kicad_pcb`) carries the inherited OpenAIO placement and routing, not a whoop layout. Its Edge.Cuts outline is still the donor 33 x 33 mm rounded rectangle around the 25.5 x 25.5 mm hole pattern; no whoop outline has been drawn.
- The 1.8 V gyro LDO on the inherited FC sheets, NCV8187 (effectively unobtainable), is replaced by TPS7A2018 (decided, imported); the sheets still show NCV8187.

## Key parts, Bluejay ESC (`whoop` library)

| Function | Part | LCSC | Note |
|---|---|---|---|
| ESC MCU x4 | EFM8BB51F16G-C-QFN20R (8051, 50 MHz) | C6547511 | Bluejay BB51 target; not in JLC assembly lib, verify or consign |
| Power stage | XR8G02M complementary N+P, DFN2020-8 (2 x 2 mm), x3 per channel, GPIO direct drive | C42457203 | 20 V, N 15 / P 25 mOhm max at 4.5 V (spec'd to 2.5 V), ~8 A cont / 15 A+ burst per motor. Single-source brand: reel-order up front. Second source: SiA527DJ (C222486) |
| 1.8 V gyro LDO | TPS7A2018PDQNR, X2SON-4 (1 x 1 mm) | C2878130 | 75 dB PSRR at 10k-100 kHz; LCSC stock thin, consign from DigiKey |
| Blackbox flash | W25Q128JVPIQ 128 Mbit SPI NOR, WSON-8 (5 x 6 mm) | C190862 | 16 MB is the market bar; replaces dead BY25Q64 |
| RX MCU option | ESP8685H4 (ESP32-C3 die, 4 MB flash), QFN-28 (4 x 4 mm) | C4944062 | 1 mm smaller each side than ESP32-C3FH4; same ELRS targets |

## Key parts, FC and RX (inherited from sibling designs)

RP2354A, LSM6DSV16XTR, 2x LMR51430, TPS2116, LP5912, NCV8187 (superseded by TPS7A2018, see above), TF-021B microSD (superseded by W25Q128JVPIQ, see above), ESP32-C3FH4 + SX1281 + TLV75533. Full part tables are in the [OpenAIO](https://github.com/OpenDrone-hw/OpenAIO) repo.

## Firmware targets

| Stage | Target |
|---|---|
| FC | Betaflight, derived from `OPENFC_LITE_MINI_RP2350A` (custom target) |
| ESC x4 | Bluejay BB51, 48 kHz (2S) / 96 kHz (1S), bidirectional DShot |
| RX | ExpressLRS `Unified_ESP32C3_2400_RX` (survives in ELRS 4.0 targets) |

## Market reference

Class reference board: BetaFPV Matrix 1S 3IN1 HD. Its specification, the class bar it sets, the full whoop-class table and the verified 2025-2026 trends: [MARKET-RESEARCH-2026-06.md](MARKET-RESEARCH-2026-06.md).

## Revisions

- **2026-08-04**: shared Incutec KiCad library wired in as the `libs/KiCad-Library` submodule.
- **2026-06-12**: ESC part selection: XR8G02M power stage (SiA527DJ second source), no-gate-driver topology locked, W25Q128JVPIQ blackbox flash, TPS7A2018 gyro LDO. Repo restructured under `hardware/`; FC and RX sheets imported; Bluejay part libraries and research docs added.
- **2026-06-01**: forked from OpenAIO as the whoop-class variant.
