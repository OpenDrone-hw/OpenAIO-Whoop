# FC pin map (proposal, P0/P1 input to P4)

**Status: synced to the P4 schematic** (`hardware/tools/check_netlist.py` N5 compares the
U10 RP2354A and U16 ESP32-PICO-V3 pin -> net tables of §2, §3 and §6 with the netlist).
This file fixes every MCU pin of the flight controller (FC), the resource allocation behind
it, the planned Betaflight board config, and the pin plans of the receiver MCU and the four
ESC MCUs; anything that moves later is named as an open item in §9 (pin swaps in the
routing loop follow D71).

Date 2026-10-07, revised the same day with DESIGN-SPEC review rounds 1-4 and decisions D13-D44
(round 3: DJI O4 Lite on UART1 with MSP DisplayPort, user UART pads on PIOUART0, GPIO27 = PINIO1 HD
line, USB/boost power mux instead of the Schottky and sense FET, one 3.3 V rail for FC and RX, no
Wi-Fi radiator, VTX defaults that survive ELRS's vtxtable push; P0 consolidation: GPIO27 drives the O4
switch EN through a BAS16LD PN diode with a 4.7 kΩ pull-down, PR1 divider 27.4k/10k; round 4: no
`VTX_MSP_UART` on 2026.6.2, firmware defaults per build type, P-FET gates leave pin 3 on L6); BOM
reduction D52-D54 applied 2026-10-09 ([BOM-REDUCTION.md](BOM-REDUCTION.md): ESP32-PICO-V3 receiver with
`vtx_mosi` on GPIO14, `vtx_miso` unset and `vtx_amp_pwm` on GPIO13, PNP PA drive, AP1606 HD gate,
LED pad driven direct, leaner decoupling, O4 EN values 33k/18k/510k with a 2.4 kΩ GPIO27 pull-down). Inputs:
[DESIGN-SPEC.md](DESIGN-SPEC.md) §4.4-4.10 and §12, research
tracks 01 (Matrix 1S 5IN1 II) and 05 (FC/RX/firmware), the house OpenFC-Lite-Mini
schematic (netlist exported with kicad-cli 10), and source code fetched fresh on
2026-10-07 (list in §11).

Tags: **V** read from a primary source (source code at a named commit, datasheet,
netlist), **S** screened (secondary), **I** inferred (my reasoning, given).

---

## 0. Summary

| Item | Decision |
|---|---|
| FC MCU (from the spec) | **RP2354A**, QFN-60 7x7, 2 MB flash inside the package. The spec picked it over the G473, so the Matrix's `BETAFPVG473_V2` config is **not** the base. Appendix A covers the documented G473 fallback |
| Base targets | No RP2350 whoop AIO exists upstream. The pin map is built from three sources: (1) the **house OpenFC-Lite-Mini RP2354A** GPIO map (flown, QFN-60; custom target `OPENFC_LITE_MINI_RP2350A`, not upstream); (2) **`RASP/RASPBERRY_PI_UAVFC`**, the only upstream config that runs the PIO framebuffer OSD, which also shows how to set flash size and font space; (3) **`BEFH/BETAFPVG473_V2`** (Matrix II) and `_V3` for the whoop feature set and defaults. The spec's draft GPIO map (§4.5) holds after checking each pin against the Betaflight source. **No GPIO moves**; the three spares of round 2 take the D13-D17 functions (PIOUART0, PINIO1) and UART1 serves the O4. Details in §9 |
| GPIO use | **30 of 30** GPIOs used (D16): GPIO2/3 = PIOUART0 user pads TP0/RP0, GPIO27 = PINIO1 HD line |
| Motors | PIO0, bidirectional DShot, GPIO25/24/23/22 = M1/M2/M3/M4 (pins 37/36/35/34). These are 5 V-tolerant pads. **No DMA** |
| UARTs | UART0 (GPIO0/1) = CRSF to the onboard ESP32 ELRS RX. UART1 (GPIO4/5) = DJI O4 Lite pads TX1/RX1, MSP DisplayPort (D16). PIOUART0 (PIO1, GPIO2/3) = user pads TP0/RP0. No SBUS pad |
| SPI | SPI1 = gyro (CS GPIO13, INT GPIO9, CLKIN GPIO6). SPI0 = 16 MB NOR blackbox (CS GPIO21). The OSD is a PIO framebuffer (PIO2, GPIO14/15/16), not SPI. The VTX SPI sits on the **ESP32**, not on the FC |
| DMA | 8 of 16 channels: SPI0 2, SPI1 2, OSD 2, LED strip 1, ADC 1. RP2350 claims channels at run time, and any channel serves any request, so streams cannot collide |
| Conflicts found | None blocks the layout. Flags in §9: the O4 integration needs `USE_OSD_HD` (no `USE_OSD_SD` define) and MSP never on UART0 (F20); the HD line holds the analog VTX off (F21); the VTX defaults must be applied after ELRS has pushed its vtxtable (F22); LED strip and PIOUART0 share PIO1 (F5); the OpenFC LED-strip stage inverts the signal, so GPIO8 drives the pad directly instead (F1, D52 BR-04); MSP-VTX over CRSF cannot be made the default in a config.h on 2026.6.2, and `VTX_MSP_UART` would delete the receiver default there (F2); a 2 MB flash layout is mandatory (F3); EFM8 logic-high margin is 0.04-0.11 V at a 4.35 V cell with the 96 kHz ripple, negative at 48 kHz (F4); the LED strip needs the PIO1 index override (F5); the ESP32 Wi-Fi pin gets a minimal radiator and auto-Wi-Fi is a flash option, not a target key (F9); the VTX drive stage inverts and is specified against the ELRS PWM window, one PNP on ESP32 GPIO13 after D52 (F15); USB-only back-feed and battery-first sequencing are bench items, with the USB/boost mux keeping +5V on USB (F16); production first flash (F18); ESP32 ADC erratum and radio BUSY (F19) |
| ESC MCU | EFM8BB51F16I (I grade, 125 °C) QFN-20, **stock Bluejay layout BB51 "A"**, pin plan in §7 |

---

## 1. Why these base targets

| Source | What it proves for this board | What it does not |
|---|---|---|
| OpenFC-Lite-Mini `rp2350a`/`imu`/`osd`/`blackbox` sheets (house, flown Rev2) | QFN-60 pin numbers and the GPIO map below (V, netlist). SPI1 gyro, PIO OSD on 14/15/16, motors 22-25, ADC 28/29 | Its custom target is not public, so its PIO/LED-strip/flash settings are unknown. Its SWD pins are unconnected. Its LED-strip stage inverts the signal (F1) |
| `RASP/RASPBERRY_PI_UAVFC` (betaflight/config 1e3f778) | `ENABLE_FB_OSD`, `OSD_W/EN/SYNC_PIN`, the font and pixel-mode defines, `config.mk` + `pico_flash_mem.ld` to set flash size and font space (V) | RP2350B board. It treats LED strip and FB OSD as **either/or** (both default to PIO2), and its PIO1 holds two PIOUARTs |
| `RASP/HELLBENDER_0001`, `TEBS/TBS_LUCID_RPI_FC`, `MADF/MADFLIGHT_FC3`, `RASP/PICO2_2350A` | `SPIx_*`, `UARTx_*`, `PIOUARTx_*`, `ADC_*`, `BEEPER_*`, `PINIO` define syntax on RP2350. CRSF on a UART/PIOUART. Descending motor order (UAVFC note) | None uses an SPI NOR blackbox (HELLBENDER and TBS use QSPI CS1; UAVFC and MADF use SD). TBS defines `UART2`-`UART5`, which do not exist on RP2350. Do not copy those lines |
| `BEFH/BETAFPVG473_V2` (Matrix II), `_V3` | Whoop defaults: CRSF RX, `BEEPER_INVERTED`, flash blackbox, current/voltage ADC, diamond `DEFAULT_ALIGN_BOARD_YAW -45` (V3), gyro CLKIN (V3) | STM32: timer, bitbang and DMA settings do not carry over (RP2350 Betaflight `#undef USE_TIMER`) |

Betaflight source checked: master `498430a` (2026-10-07) and tag `2026.6.2`. The PICO
files that set the constraints are identical in both, except for one AFATFS line:
`target_RP2350.h`, `dshot_pico.c`, `light_ws2811strip_pico.c` and `gyro_clkin_pico.c` (V).

---

## 2. RP2354A signal pins

> P4 integration sync (2026-10-09): the Net columns of §2, §3 and §6 carry the schematic net names (underscore bus names, pin-side nets), checked by `hardware/tools/check_netlist.py` N5.

Pin numbers come from the RP2350 datasheet Figure 2 (QFN-60, top view) and match
the OpenFC netlist (V). Package side, top view: **L** = pins 1-15, **B** = 16-30,
**R** = 31-45, **T** = 46-60. P5 may rotate the package. In Betaflight, `PAn` means GPIOn.
Net names follow LINEUP-CONVENTIONS rule 12.

| Pin | Pad | Net | Function | Betaflight define | HW block / mux | Parts on the net | Side |
|---|---|---|---|---|---|---|---|
| 2 | GPIO0 | `UART0_TX` | CRSF to ESP32 U0RXD (GPIO3, pin 40) | `UART0_TX_PIN PA0` | UART0 TX (F2) | none | L |
| 3 | GPIO1 | `UART0_RX` | CRSF from ESP32 U0TXD (GPIO1, pin 41) | `UART0_RX_PIN PA1` | UART0 RX (F2) | none | L |
| 4 | GPIO2 | `PIOUART0_TX` | user pad **TP0** | `PIOUART0_TX_PIN PA2` | PIO1 (uart_tx, 10 instr) (F5) | pad | L |
| 5 | GPIO3 | `PIOUART0_RX` | user pad **RP0** (PIOUART0, 8N1 only; SBUS/CRSF receivers via the EXT-USER-PADS preset (hardware UART0 on GPIO2/3; 8E2 needs a release with the uart_hw.c fix)) | `PIOUART0_RX_PIN PA3` | PIO1 (uart_rx, 9 instr) | pad | L |
| 7 | GPIO4 | `UART1_TX` | HD pad **TX1** → O4 RX (white) | `UART1_TX_PIN PA4` | UART1 TX (F20) | pad | L |
| 8 | GPIO5 | `UART1_RX` | HD pad **RX1** ← O4 TX (grey) | `UART1_RX_PIN PA5` | UART1 RX (F20) | pad | L |
| 9 | GPIO6 | `GYRO_CLKIN` | IMU pin 9: CLKIN on TDK parts (32 kHz), INT2 on BMI270 (left disabled) | `GYRO_1_CLKIN_PIN PA6` | PWM slice 3 A (F13), only with ICM-42688-P | none | L |
| 10 | GPIO7 | `LED0` | status LED, green | `LED0_PIN PA7` | SIO | LED + 0201 R from +3V3, pin sinks (Betaflight default: low = on) | L |
| 12 | GPIO8 | `LED_STRIP` | WS2812 data | `LED_STRIP_PIN PA8` | PIO1, 1 SM (ws2812, 4 instr) + 1 DMA | **pad LED driven directly**, no series resistor, like the other user pads (D52 BR-04, Matrix II parity; the round-4 74LVC1T45GS translator and its two caps are deleted) (F1) | L |
| 13 | GPIO9 | `GYRO_INT` | IMU INT1 (LGA pin 4) | `GYRO_1_EXTI_PIN PA9` | GPIO IRQ | none | L |
| 14 | GPIO10 | `SPI1_SCK` | IMU SCK (LGA pin 13) | `SPI1_SCK_PIN PA10` | SPI1 SCK (F1) | none | L |
| 15 | GPIO11 | `SPI1_MOSI` | IMU SDI (LGA pin 14) | `SPI1_SDO_PIN PA11` | SPI1 TX (F1) | none | L |
| 16 | GPIO12 | `SPI1_MISO` | IMU SDO (LGA pin 1) | `SPI1_SDI_PIN PA12` | SPI1 RX (F1); Betaflight sets the pull-up | none | B |
| 17 | GPIO13 | `GYRO_CS` | IMU CSB (LGA pin 12) | `GYRO_1_CS_PIN PA13` | SIO (software CS) | **10 kΩ pull-up** to +3V3 (OpenFC R49) | B |
| 18 | GPIO14 | `OSD_W` | OSD white-level drive | `OSD_W_PIN PA14` | PIO2 (FB OSD) | `osd` sheet | B |
| 19 | GPIO15 | `OSD_EN` | OSD switch select (must be W+1) | `OSD_EN_PIN PA15` | PIO2 | SN74LVC1G3157 S | B |
| 27 | GPIO16 | `OSD_SYNC` | sync comparator output (must be EN+1) | `OSD_SYNC_PIN PA16` | PIO2 input | TLV7031 output | B |
| 28 | GPIO17 | `BEEPER` | buzzer FET gate | `BEEPER_PIN PA17` + `BEEPER_INVERTED` | SIO (no `BEEPER_PWM_HZ`: active buzzer) | ALLPOWER AP1606 N-FET (DFN-3L 1.0x0.6, C2849580) [PU], 100 kΩ gate pull-down; drain to pad BZ-, BZ+ = +5V | B |
| 29 | GPIO18 | `SPI0_SCK` | NOR CLK | `SPI0_SCK_PIN PA18` | SPI0 SCK (F1) | none | B |
| 31 | GPIO19 | `SPI0_MOSI` | NOR DI | `SPI0_SDO_PIN PA19` | SPI0 TX (F1) | none | R |
| 32 | GPIO20 | `SPI0_MISO` | NOR DO | `SPI0_SDI_PIN PA20` | SPI0 RX (F1) | none | R |
| 33 | GPIO21 | `FLASH_CS` | NOR /CS | `FLASH_CS_PIN PA21` | SIO (software CS) | **10 kΩ pull-up**; NOR /WP and /HOLD to +3V3 | R |
| 34 | GPIO22 | `MOTOR4` | DShot M4, front-left | `MOTOR4_PIN PA22` | PIO0 SM | 2.4 kΩ series at the EFM8 end (§7) | R |
| 35 | GPIO23 | `MOTOR3` | DShot M3, rear-left | `MOTOR3_PIN PA23` | PIO0 SM | same | R |
| 36 | GPIO24 | `MOTOR2` | DShot M2, front-right | `MOTOR2_PIN PA24` | PIO0 SM | same | R |
| 37 | GPIO25 | `MOTOR1` | DShot M1, rear-right | `MOTOR1_PIN PA25` | PIO0 SM | same | R |
| 40 | GPIO26 | `LED1` | status LED, blue | `LED1_PIN PA26` | SIO (ADC0 unused) | LED + R from +3V3 (sink) | R |
| 41 | GPIO27 | `HD_EN` | HD line: high = O4 supply on and analog VTX held off (D15, D17) | `PINIO1_PIN PA27` | SIO (PINIO1; ADC1 unused) | TPS22810 EN/UVLO through a Nexperia BAS16LD PN diode (pull-down only; not a Schottky: its hot leakage would defeat the cell threshold, spec §4.2; the EN node also carries the 100 nF filter and the 510 kΩ hysteresis resistor from +5V_HD, which the diode discharges; divider 33k/18k, D53 BR-22); gate of the AP1606 HD gate (D53 BR-03, no resistor); a **2.4 kΩ pull-down** (Ralec RTT012401FTH, BR-24) keeps it low (analog) at reset, on USB and in SD builds (the RP2350's own reset pull-down is too weak against the EN divider current); about 1.4 mA when driven high, all of it in the pull-down (F21) | R |
| 42 | GPIO28 | `ADC_CURR` | INA186A3 output `CURR_SENSE`, 50 mV/A, through the 1 kΩ / 100 nF RC (R47 / C60) | `ADC_CURR_PIN PA28` | ADC ch 2 | 1 kΩ + 100 nF RC (OpenFC) | R |
| 43 | GPIO29 | `ADC_VBAT` | cell voltage, 10k/10k divider, 4.35 V gives 2.18 V | `ADC_VBAT_PIN PA29` | ADC ch 3 | 2x 10 kΩ + 100 nF | R |
| 21 | XIN | `XIN` | 12 MHz crystal (USB needs it) | - | XOSC | Abracon **ABM8-272-T3** (C20625731, 3225, 12 MHz, CL 10 pF, ESR ≤ 50 Ω, ±30 ppm, −40..85 °C; the crystal RP2350 DS §8.2.1.1 Table 629 specifies and names, D78) with 2x 15 pF C0G 0201 (about 2.5 pF stray) and the 1 kΩ XOUT resistor (RPi guide values for this crystal). Not the YXC 2520 (150 Ω ESR) or the house TOGNJING (120 Ω, −20..70 °C) | B |
| 22 | XOUT | `XOUT` | crystal drive | - | XOSC | **1 kΩ series** (RPi guide, OpenFC R5) | B |
| 24 | SWCLK | `SWCLK` | SWD clock, pad **CLK** | - | SWD | pad (OpenFC leaves this unconnected; we add pads) | B |
| 25 | SWDIO | `SWDIO` | SWD data, pad **DIO** | - | SWD | pad | B |
| 26 | RUN | `+3V3` | reset, active low (tied high, net +3V3) | - | - | tie to +3V3 (datasheet: "If RUN is not used, it should be tied high"); an optional RST pad + 10 kΩ pull-up lets a user enter BOOTSEL without unplugging | B |
| 51 | USB_DM | `U10_USB_DM` | USB D− (pin side of R43) | - | USB PHY | 27 Ω series near the pin (RPi guide; OpenFC 30 Ω) → `USB_D_N` → D7 ESD + J31 pin 2 (D57). `_P`/`_N` suffix so KiCad pairs the nets | T |
| 52 | USB_DP | `U10_USB_DP` | USB D+ (pin side of R42) | - | USB PHY | 27 Ω series → `USB_D_P` → D7 ESD + J31 pin 3 (D57) | T |
| 60 | QSPI_SS | `QSPI_SS` | boot strap: low at reset = BOOTSEL (UF2) | - | QMI CS0 (in-package flash) | **1 kΩ** (R44) to `FC_BOOT`: shared button SW1 through D8 (D65) and test via TP9 (D67) (RPi guide R6). Keep the stub short | T |
| 55-59 | QSPI_SD3, SCLK, SD0, SD2, SD1 | - | bonded to the stacked flash die | - | QMI | **no-connect** (NOR is on SPI0, not on QSPI CS1). SD1 is the UART-boot strap: leave it open | T |

Boot states (V, RP2350 datasheet §9.3): at power-up every bank-0 GPIO is high-Z
with its **pull-down** on. So the motor lines idle low, the beeper FET is off, the
LED strip is low, and the CS lines would sit low without the external pull-ups,
which is why the pull-ups are there. GPIO0-25 are 5 V-tolerant when IOVDD is up
("Digital IO (FT)"). GPIO26-29 are standard ADC pads and are not 5 V-tolerant (V,
§14.9). **Never move a motor line to GPIO26-29**: the EFM8 drives telemetry back
at VDD, which is the cell voltage, up to 4.35 V.

---

## 3. RP2354A power and system pins

| Pins | Pad | Net | Parts (from the OpenFC `rp2350a` sheet unless noted) |
|---|---|---|---|
| 1, 11, 20, 30, 38, 45 | IOVDD | +3V3 | 100 nF 0201 each (X6S GRM033C81E104KE14D, D52 BR-18); the pin-45 cap sits at ADC_AVDD pin 44 and serves both (BR-08) |
| 6, 23, 39 | DVDD | +1V1 | 100 nF each + 2x 4.7 µF on the rail (C56 at VREG_FB, C134 at pin 23: RP2350 DS 6.3.8, ruling 2026-10-09) |
| 44 | ADC_AVDD | +3V3 | shares the IOVDD pin-45 100 nF, placed at pin 44 (D52 BR-08; RP2350 DS §6.1.5: "decoupled with a 100nF capacitor close to the chip's ADC_AVDD pin"). The ADC measures relative to this pin, so keep boost ripple off it |
| 46 | VREG_AVDD | `VREG_AVDD` (RC from +3V3) | 27 Ω (RC0201FR-0727RL, the USB series line; D52 BR-21, OpenFC 30 Ω, RPi guide 33 Ω) + 4.7 µF; corner 1.25 kHz |
| 47 | VREG_PGND | GND | core-SMPS return, short loop |
| 48 | VREG_LX | `VREG_LX` (to L2) | Abracon AOTA-B201610S3R3 3.3 µH to +1V1; polarity-marked |
| 49 | VREG_VIN | +3V3 | 4.7 µF |
| 50 | VREG_FB | +1V1 | sense at the output cap |
| 53 | USB_OTP_VDD | +3V3 | one 100 nF shared with pin 54, placed ≤ 1 mm from pin 54 (D52 BR-08) |
| 54 | QSPI_IOVDD | +3V3 | the shared 100 nF of pin 53 (in-package flash supply, 2.7-3.6 V, so the cap sits at this pin; P5 condition, spec §15.5 P4-17). The house OpenFC-Lite-Mini flies 7 caps for these 9 supply pins (V, pcbnew) |
| 61 (EP) | GND | GND | Type VII via-in-pad array (spec §11) |

---

## 4. Resource allocation and conflict check

RP2350 Betaflight has **no hardware timers in the motor path** (`#undef USE_TIMER`,
`#undef USE_DSHOT_BITBANG`, `#undef USE_DMA_SPEC` in `target_RP2350.h`, V). The
STM32 checks ("timer free of other uses", "DMA stream/request unique") translate to
the resources below.

### 4.1 PIO blocks (3 blocks x 4 state machines x 32 instructions)

| Block | Owner (index define) | Instructions | SMs | Check |
|---|---|---|---|---|
| PIO0 | DShot, `PIO_DSHOT_INDEX 0` (default) | 29 (`dshot_600_bidir`) or 13 (unidirectional) | 4 of 4 | **dedicated to the motors.** Same program for all 4 motors. Any GPIO works; the GPIO base stays 0 because all pins are below 32 (V, `dshot_pico.c`) |
| PIO1 | LED strip, **`PIO_LEDSTRIP_INDEX 1` (override)**, and PIOUART0 (`PIO_UART_INDEX 1`, the default) | 4 + 10 + 9 = 23 | 3 of 4 | fits. Both drivers claim state machines with `pio_claim_unused_sm` and load with `pio_add_program`, and every pin is below 32, so the GPIO base stays 0 for both (V, `light_ws2811strip_pico.c`, `uart_pio.c`, `target_RP2350.h` L96-101 at 2026.6.2). No upstream board combines them: bench gate V9 (F5) |
| PIO2 | FB OSD, `PIO_OSD_INDEX 2` (default) | 31 (`osd_tx_pal` or `_ntsc`); 25 for the sync-count program, loaded and then removed during PAL/NTSC detection | 1 of 4 | full: 1 instruction free, so **the LED strip cannot stay on PIO2** (its upstream default), hence the override (V, `osd_tx.pio.h`, `osd_pico.c`) |

### 4.2 DMA (16 channels, claimed at run time with `dma_claim_unused_channel`, any channel serves any DREQ)

| User | Channels | Source |
|---|---|---|
| SPI0 (NOR) | 2 (TX, RX) | `bus_spi_pico.c` |
| SPI1 (gyro) | 2 | same |
| FB OSD | 2 (background → buffer A, buffer B → PIO2 FIFO) | `osd_pico.c` |
| LED strip | 1 (→ PIO1 TX FIFO) | `light_ws2811strip_pico.c` |
| ADC round-robin | 1 | `adc_pico.c` |
| DShot, UARTs, PIOUART, USB | 0: DShot frames are CPU writes to the PIO FIFO, UARTs run on IRQs | `dshot_pico.c`, `uart_*.c` |
| **Total** | **8 of 16** | spec §4.5 said "DShot 4-8 … ≤ 15": corrected (F6) |

There are no fixed stream/request pairs, so two features cannot collide on a stream;
the only limit is the count. `dma_pico.c` honours `DMA_IRQ_CORE_NUM` only under
`USE_MULTICORE`, which `target_RP2350.h` leaves commented out, so Betaflight on RP2350
runs entirely on core 0: gyro and PID, the CPU-side bidirectional DShot decode
(4 x 128 samples), FB OSD rendering and 2 kHz blackbox share one core. V9 checks task
load and loop overruns with the ICM-42688-P at 8 kHz, FB OSD and blackbox together (V).

### 4.3 PWM slices

| Slice/channel | User | Shared with | Verdict |
|---|---|---|---|
| 3 A (GPIO6) | gyro CLKIN, only when an ICM-42688-P is fitted (`accgyro_spi_icm426xx.c`) | GPIO7 (3 B, LED0 as SIO), GPIO22/23 (3 A/3 B, motors on PIO0) | no conflict while the motor protocol is DShot. A PWM/OneShot protocol would put M4 on the same slice and channel and overwrite CLKIN. Bluejay is DShot-only, so this cannot happen in use (I). `gyro_clkin_pico.c` refuses a slice that is already running (V) |
| 0 B (GPIO17) | beeper, **only if** `BEEPER_PWM_HZ` is defined (passive buzzer) | GPIO0/1 (UART0), GPIO16 (PIO2) | not used: active buzzer, GPIO mode |

### 4.4 Fixed peripherals

| Peripheral | Pins | Check against the allowed-pin tables in the source (V) |
|---|---|---|
| UART0 | TX GPIO0, RX GPIO1 | `uart_hw.c`: TX in {0,2,12,14,16,18,28,…}, RX in {1,3,13,15,17,19,29,…}: OK |
| UART1 | TX GPIO4, RX GPIO5 | TX in {4,6,8,10,20,…}, RX in {5,7,9,11,21,…}: OK |
| PIOUART0 | TX GPIO2, RX GPIO3 | PIO UART: any GPIO; `USE_PIOUART0` is defined for RP2350 (`target_RP2350.h` L32, V): OK |
| PINIO1 | GPIO27 | any GPIO; `USE_PINIO` unconditional (`common_pre.h`), MADFLIGHT_FC3 uses PINIO on RP2350 upstream: OK |
| SPI0 | SCK 18, MOSI 19, MISO 20 | `bus_spi_pico.c` SPI0 SCK {2,6,18,22}, MOSI {3,7,19,23}, MISO {0,4,16,20}: OK |
| SPI1 | SCK 10, MOSI 11, MISO 12 | SPI1 SCK {10,14,26}, MOSI {11,15,27}, MISO {8,12,24,28}: OK |
| ADC | ch2 GPIO28, ch3 GPIO29 | QFN-60 ADC is GPIO26-29 only: OK |
| FB OSD | 14, 15, 16 | consecutive W/EN/SYNC enforced in `osd_pico.c` lines 141-152: OK |
| QSPI CS1 | not used | the RP2350-E14 GPIO0 erratum only applies when CS1 is configured: no effect on UART0 (V) |

### 4.5 Electrical checks on the FC pins

| Check | Result |
|---|---|
| FC → EFM8 logic high | EFM8BB51 VIH = 0.7 x VDD (V, Table 4.18), and VDD is the cluster +BATT including its PWM ripple (spec §4.1, §4.4). DC: 3.05 V at a 4.35 V cell, 2.94 V at 4.2 V. At the ripple peaks of the 96 kHz builds (0.4-0.6 V p-p, VDD 4.55-4.65 V) VIH is 3.19-3.26 V; at 48 kHz (0.8-1.25 V p-p) it would reach 3.33-3.47 V. The RP2350 drives about IOVDD (3.27-3.3 V) into a µA load: margin 0.04-0.11 V at 96 kHz, negative at 48 kHz. Matrix parity (G473 at 3.3 V into BB51 on the cell, also at 96 kHz). The other direction of the same flag: EFM8BB51 Table 4.1 limits the GPIO pins to VDD + 0.3 V, so at a 2.5-2.8 V sag the 3.3 V DShot high sits 0.2-0.5 V over P0.5's absolute maximum; the 2.4 kΩ series resistor limits the injected current to below about 0.1 mA (I), which is benign and Matrix parity (its G473 also drives 3.3 V into a sagging BB51). Flag F4; V9 scopes the high level and counts checksum failures with a debug build |
| EFM8 → FC (bidirectional telemetry) | the EFM8 drives up to VDD = 4.35 V through 2.4 kΩ into FT pads (5.5 V tolerant with IOVDD up): OK |
| Unpowered-ESC case (USB only) | bidirectional DShot idles high (PIO drive, `gpio_set_pulls` up), so up to 4 x (3.3 V − VF) / 2.4 kΩ, about 5 mA, back-feeds +BATT through the EFM8 I/O diodes. With µA loads (20 kΩ divider, EFM8s below POR) +BATT rises towards about 2.5-2.8 V until the EFM8s start near their POR (1.71 V) and draw current, so the EFM8s may cycle at low energy (I). The boost (always enabled) may start and hiccup on that weak source, but the TPS2116 mux keeps +5V on USB (USB has priority, the boost output is not selected), so +5V and the FC are unaffected (spec §4.2). Bench check in V9 (measure +BATT, watch for brown-out cycling, confirm +5V stays on USB); the fallback is 10 kΩ DShot series R (no new part). Matrix parity: its G473 drives BB51 on the cell the same way (F16) |
| Battery first, IOVDD not yet up | the EFM8 weak pull-ups (70-220 kΩ to up to 4.35 V) reach the RP2350 FT pads through 2.4 kΩ before IOVDD is up, for the boost soft start plus LDO ramp (about 1-2 ms, I). With IOVDD = 0 the FT pads are limited to 3.63 V: a **voltage** limit, so this is an abs-max excursion if the pad floats up towards the cell voltage; the 10 kΩ fallback limits current, not voltage. Matrix parity: the G473's FT pins are limited to about 4 V with VDD = 0 (S). V9 scopes the pad against 3.63 V; if exceeded, a 3.3 V-domain clamp option or an enable on the DShot path (F16) |
| Motor line at power-up | RP2350 pull-down (35-189 kΩ) fights the EFM8 weak pull-up (70-220 kΩ to the cell), so the level is undefined. The Bluejay bootloader (`BLHeliBootLoad.inc`) loops while RTX is high and leaves after 250 ms of low or 250 failed sign-on attempts. Either way the application starts once DShot frames arrive (V code, I outcome). No extra resistor |
| Gyro CS / NOR CS at reset | the internal pull-down would select the chips. 10 kΩ external pull-ups give ≥ 2.75 V at the strongest pull-down: OK |
| VBAT ADC | 4.35 V → 2.18 V, inside the 3.3 V range, on a non-FT pad: OK |

---

## 5. Planned Betaflight board config (betaflight/config format, release ≥ 2026.6.2)

Folder `configs/INCU/OPENAIO_WHOOP/` with three files. Pin and define syntax follow the
upstream RP2350 configs in §1; every define name was checked against master `498430a`.

### 5.1 `config.h`

```c
/*
 * This file is part of Betaflight.
 *
 * Betaflight is free software. You can redistribute this software
 * and/or modify this software under the terms of the GNU General
 * Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later
 * version.
 *
 * Betaflight is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public
 * License along with this software.
 *
 * If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

// OpenAIO-Whoop rev1: 1S whoop AIO, RP2354A (RP2350A die + 2 MB stacked flash, see config.mk),
// onboard ESP32 ELRS RX on UART0 (CRSF + MSP-VTX), PIO framebuffer analog OSD, DJI O4 Lite pads on
// UART1 (MSP DisplayPort, HD builds), 4x EFM8BB51 Bluejay ESC (layout BB51 "A"), PY25Q128HA-DFH-IR blackbox.
// Open hardware (CERN-OHL-S).

#define FC_TARGET_MCU        RP2350A
#define BOARD_NAME           OPENAIO_WHOOP
#define MANUFACTURER_ID      INCU          // register in Manufacturers.md in the same PR (FOSS until then)

// ---- IMU: universal LGA-14 land; ONE population per board revision (README states which) ----
#define USE_GYRO
#define USE_ACC
#define USE_ACCGYRO_BMI270
#define USE_GYRO_SPI_ICM42688P
#define USE_ACC_SPI_ICM42688P
#define USE_GYRO_CLKIN                     // active only with ICM-42688-P (LGA pin 9 = CLKIN)

#define SPI1_SCK_PIN         PA10
#define SPI1_SDI_PIN         PA12          // MISO
#define SPI1_SDO_PIN         PA11          // MOSI
#define GYRO_1_SPI_INSTANCE  SPI1
#define GYRO_1_CS_PIN        PA13
#define GYRO_1_EXTI_PIN      PA9
#define GYRO_1_CLKIN_PIN     PA6           // PWM slice 3A
#define GYRO_1_ALIGN         CW0_DEG       // set at P5 from the placed LGA orientation
#define DEFAULT_ALIGN_BOARD_YAW  -45       // diamond mount (as BETAFPVG473_V3); sign confirmed at P4/P5

// ---- Blackbox: 16 MB SPI NOR (PY25Q128HA-DFH-IR, JEDEC 0x852018, m25p16 driver) on SPI0 ----
#define USE_FLASH
#define USE_FLASH_M25P16
#define SPI0_SCK_PIN         PA18
#define SPI0_SDI_PIN         PA20          // MISO
#define SPI0_SDO_PIN         PA19          // MOSI
#define FLASH_SPI_INSTANCE   SPI0
#define FLASH_CS_PIN         PA21
#define DEFAULT_BLACKBOX_DEVICE  BLACKBOX_DEVICE_FLASH

// ---- Motors: PIO0 bidirectional DShot, descending GPIO = M1..M4 ----
#define MOTOR1_PIN           PA25          // rear right
#define MOTOR2_PIN           PA24          // front right
#define MOTOR3_PIN           PA23          // rear left
#define MOTOR4_PIN           PA22          // front left
#define DEFAULT_DSHOT_TELEMETRY  DSHOT_TELEMETRY_ON   // Bluejay: RPM filter
// DShot speed left at the build default (DShot600); bench gate V9 decides 300 vs 600.

// ---- Serial ----
#define UART0_TX_PIN         PA0           // -> ESP32 GPIO3 (U0RXD)
#define UART0_RX_PIN         PA1           // <- ESP32 GPIO1 (U0TXD)
#define UART1_TX_PIN         PA4           // HD pad TX1 -> O4 RX (white)
#define UART1_RX_PIN         PA5           // HD pad RX1 <- O4 TX (grey)
#define PIOUART0_TX_PIN      PA2           // user pad TP0 (PIO1, shared with the LED strip)
#define PIOUART0_RX_PIN      PA3           // user pad RP0: PIOUART0, 8N1 only; SBUS/CRSF receivers via the EXT-USER-PADS preset (hardware UART0 on GPIO2/3; 8E2 needs a release with the uart_hw.c fix)
// MSP is never set on UART0 (CRSF): Betaflight picks the first port with VTX_MSP|MSP for DisplayPort (config.c).

// ---- HD line (D15, D17): high = O4 supply on (TPS22810) and analog VTX held off (AP1606 gate, D53) ----
#define PINIO1_PIN           PA27          // 2.4k pull-down = low = analog mode
// This file is read BEFORE target/common_pre.h (platform.h), so USE_OSD_HD is seen here only when the build
// passes it on the command line (cloud option "OSD (HD)"). Defaults per build type: see the table below.
#ifdef USE_OSD_HD
#define MSP_DISPLAYPORT_UART SERIAL_PORT_UART1   // O4 canvas
#define PINIO1_CONFIG        129           // HD build boots in HD mode (inverted = high at init)
#endif                                     // OSD (SD)-only build: PINIO1 default (low) = analog

#define DEFAULT_RX_FEATURE   FEATURE_RX_SERIAL
#define SERIALRX_PROVIDER    SERIALRX_CRSF
#define SERIALRX_UART        SERIAL_PORT_UART0
// No VTX_MSP_UART while 2026.6.x is the minimum release: its reset function ASSIGNS FUNCTION_VTX_MSP to the
// port after SERIALRX_UART assigned FUNCTION_RX_SERIAL (serial.c L316-321, L353-358), so UART0 would lose the
// receiver, and isSerialConfigValid() rejects a lone VTX_MSP and PG_RESETs to the same default (L541-544,
// config.c L230). MSP-VTX over CRSF comes from the serial CLI line in 5.4. Re-add only for a release with the
// master vtx_uart model, where the synthesized masks OR the functions.

// ---- PIO allocation (defaults: DShot PIO0, LED strip PIO2, OSD PIO2) ----
#define PIO_LEDSTRIP_INDEX   1             // PIO2 is full with the FB OSD (31/32 instructions)

// ---- LED strip, status LEDs, beeper ----
#define LED_STRIP_PIN        PA8           // pad LED driven directly (D52 BR-04)
#define LED0_PIN             PA7           // green, sink (low = on)
#define LED1_PIN             PA26          // blue, sink
#define USE_BEEPER
#define BEEPER_PIN           PA17
#define BEEPER_INVERTED                    // low-side N-FET: high = on; active buzzer, no BEEPER_PWM_HZ

// ---- Battery sensing ----
#define ADC_VBAT_PIN         PA29          // 10k/10k
#define ADC_CURR_PIN         PA28          // INA186A3 + 0.5 mOhm = 50 mV/A
#define DEFAULT_VOLTAGE_METER_SOURCE   VOLTAGE_METER_ADC
#define DEFAULT_CURRENT_METER_SOURCE   CURRENT_METER_ADC
#define DEFAULT_VOLTAGE_METER_SCALE    200 // ratio 2 x 100: 0.5 % trim steps instead of 5 % at divider 10
#define DEFAULT_VOLTAGE_METER_DIVIDER  100
#define DEFAULT_CURRENT_METER_SCALE    500 // 0.1 mV/A units; both scales re-measured on the first boards

// ---- Analog OSD: PIO framebuffer (needs W, EN = W+1, SYNC = EN+1) ----
// No USE_OSD_SD define: alone it leaves USE_OSD_HD undefined (common_pre.h) and displayport_msp.c then
// forces the O4 canvas back to SD (30 x 16). The cloud-build OSD option brings SD + HD.
#define ENABLE_FB_OSD        1
#define OSD_W_PIN            PA14
#define OSD_EN_PIN           PA15
#define OSD_SYNC_PIN         PA16
#define OSD_FB_PICO_FLASH_FONT             // font stays in flash (FONT_LENGTH in pico_flash_mem.ld)
#define OSD_FB_PICO_ENABLE_PIXEL_MODE  1
#define OSD_FB_PICO_POSTPROCESS        2
#define OSD_FB_ENABLE_SMALLFONT        1
#define OSD_BATTERY_PERCENT_WITH_SYMBOL
#define OSD_RSSI_WITH_SYMBOL
#define OSD_FRAMERATE_MAX_HZ           100
#define OSD_FRAMERATE_DEFAULT_HZ       50
#define OSD_DRAWSCREEN_TIME_LIMIT_US   20
```

**Defaults per build type** (V, 2026.6.2 / master 498430a: `platform.h` includes `config.h`
before `target/common_pre.h`, master L26 / L29; `pg/vcd.c` defaults the video system to HD and
`osd/osd.c` L418-427 the OSD device to MSP whenever `USE_OSD_HD` is compiled; `fc/init.c` L947
forces the MSP displayport when the video system is HD, and selects MSP even with no MSP port):

| Build | `USE_OSD_HD` at `config.h` | Boots in | Works out of the box |
|---|---|---|---|
| Cloud, **OSD (SD)** only (`-DUSE_OSD_SD`) | no, and never defined | video AUTO, OSD device AUTO → FB OSD, PINIO1 low | **analog** (the production build, spec §12.1); the O4 canvas is not compiled (`displayport_msp.c` resets HD to AUTO) |
| Cloud, **OSD (HD)** (with or without SD) | yes | video HD, OSD MSP on UART1, PINIO1 high (O4 on, analog VTX held off) | **HD**; analog only after the analog preset (5.4) |
| Cloud plain `OSD`, or a local / CI `make` | no, but `common_pre.h` defines SD + HD afterwards (L249-253 non-cloud, L452-455 for plain `USE_OSD`) | video HD, OSD MSP, but no MSP DisplayPort port and PINIO1 low | **neither**: no analog OSD (FB OSD never started) and no O4 canvas until a preset (5.4) is applied. Not a user build; the README says so |

The board defaults stay keyed on `USE_OSD_HD` (upstream precedent: `RASP/RASPBERRY_PI_UAVFC`), because
no define in `config.h` can move the OSD device default; the README states that an HD-capable firmware
boots in HD mode, with the analog VTX off, until the analog preset is applied.

Not in the config, by design: no `USE_MAX7456` (no OSD chip), no I2C, baro or mag, no
`USE_VTX_RTC6705` (undefined on RP2350, and not wanted), no `VTX_MSP_UART` (above). The only PINIO is the HD line:
the analog VTX's own power and pit stay with the ESP32 (§6); PINIO1 only forces it off in
HD mode. VTX, CRSF telemetry, OSD (SD + HD) and LED strip come from the cloud-build options
(`USE_VTX` brings `USE_VTX_MSP`; `common_pre.h`, V).

### 5.2 `config.mk` (mandatory: the RP2354A has 2 MB, the RP2350A build assumes 8 MB)

```make
# RP2354A: 2 MB in-package flash (W25Q16JV die on QSPI CS0)
TARGET_FLASH_SIZE = 2048

PICO_FLASH_DEFINES = \
                   -DPICO_FLASH_SPI_CLKDIV=2 \
                   -DPICO_FLASH_SIZE_BYTES=2097152 \
                   -DPICO_BOOT_STAGE2_CHOOSE_W25Q080=1
```

### 5.3 `pico_flash_mem.ld`

```ld
/* RP2354A primary flash and FB_OSD font allocation */
PRIMARY_FLASH_LENGTH = 2M;
FONT_LENGTH = 16K;
```

Without these two files the build uses `MCU_FLASH_SIZE 8192` and puts the 64 KB config
sector at 4 MB − 64 KB (`pico_flash_mem_defaults.ld`), beyond the 2 MB die. The die
ignores the upper address bits, so writes would alias to 2 MB − 64 KB: it might work
by accident, but it is not a defined layout. The UAVFC config uses the same mechanism
for its 4 MB flash (V, `RP2350.mk` lines 499-506 at 2026.6.2). The house OpenFC
target's setting is unknown (F3).

### 5.4 Defaults a config.h cannot set (README "first setup", or a fixed CLI dump)

| Setting | Value | Why |
|---|---|---|
| UART0 function mask on 2026.6.2 | `serial UART0 131136 115200 57600 0 115200` (RX_SERIAL 64 + VTX_MSP 131072) | 2026.6.2 `vtx_msp.c` sends VTX replies over CRSF only when the RX port carries both functions (`isCrsfPortConfig`, V). `VTX_MSP_UART` cannot do it on 2026.6.2: it overwrites the RX_SERIAL mask (5.1, F2), so the board config leaves it out. Production applies this line and saves **before** the first ELRS boot (spec §12.1 step 4): without it ELRS has no MSP-VTX reply, gives up after 5 s (`MSP_VTX_TIMEOUT_NO_CONNECTION`) and its vtxtable never lands. Never add MSP (1) here: DisplayPort would land on CRSF |
| VTX table | written by ELRS, then kept | Betaflight ships none. On the first ELRS session `devMSPVTX` finds a mismatch and runs `clearVtxTable()`: `MSP_SET_VTX_CONFIG` with power 3 (25 mW), pitmode 0, lowPowerDisarm 0, then an EEPROM write, all applied by Betaflight (`msp.c` l. 3829-3842; V). So production boots ELRS once with the FC **before** applying the defaults below (spec §12.1), or the shipped diff carries the exact ELRS table (6 bands x 8 channels; 5 levels, values 1, 2, 14, 20, 26, labels `0`, `RCE`, `25`, `100`, `400`) so nothing is cleared |
| `vtx` power | 2 (RCE) | ELRS forces pit at boot only on index 2 (`devMSPVTX.cpp` l. 211, `SET_RCE_PIT_MODE`); the README tells the user to re-enable pit after landing |
| `vtx_low_power_disarm` | `OFF` until ELRS patch (3) merges, then `ON` | Betaflight sends index 1 whenever disarmed with it ON (`vtx_msp.c` l. 110 at 2026.6.2), and ELRS turns index 1 into "setpoint `VPD_SETPOINT_0_MW`, maximum count" with VREF **on** (`devVTXSPI.cpp` l. 251-258, 289) and forces index 1 at boot when the flag is set (`devMSPVTX.cpp` l. 217): the PA stays biased at about 1 W and RCE is defeated. With patch (3) (index 1 = pit, spec §12) ON means pit when disarmed |
| HD preset (O4) | `serial UART1 131073 115200 57600 0 115200` (MSP 1 + VTX_MSP 131072), `set osd_displayport_device = MSP`, `set vcd_video_system = HD`, `set pinio_config = 129,1,1,1`, `save`, battery power cycle | the O4 canvas on UART1; the HD line on (O4 supply, analog VTX off). Needs a build with the OSD (HD) option, which defaults to it (5.1 table) |
| Analog preset | `serial UART1 0 115200 57600 0 115200`, `set osd_displayport_device = FBOSD`, `set vcd_video_system = AUTO`, `set pinio_config = 1,1,1,1`, `save` | FB OSD on PIO2; HD line off. Part of the shipped diff (spec §12.1 step 4) although the OSD (SD) production build defaults to the same values, so a defaults reset on any build type returns to analog with one paste |
| `motor_poles` | measured on the target motor (whoop 1102/0802 class: 12) | RPM filter |

---

## 6. Receiver MCU pin plan (ESP32-PICO-V3, QFN-48 7x7)

The VTX control path is ESP32 → RTC6705 over SPI (ELRS `devVTXSPI`) plus MSP-VTX over
CRSF to the FC. So the "VTX SPI" and "VTX power/enable" items of this pin map live on
the ESP32. The MCU is the **ESP32-PICO-V3** (D52 BR-01, owner D55; no fallback, D61): 4 MB flash, 40 MHz crystal and CAP network inside the package. Its flash
uses GPIO16/17/18/23 and GPIO6/11 (Espressif PICO series datasheet v1.3 Fig. 8; pins 30/31
are flash CMD/CLK, pins 25, 35, 36, 44, 45, 47, 48 are NC, Table 4; V), so GPIO18 and GPIO23
are not exposed. Pins otherwise follow the ExpressLRS layout `RX/Generic 2400 Whoop Rx and
VTx.json` (fetched 2026-10-07, identical to the 42ed776 copy; V), with three keys moved in the
board's own layout JSON (D53): `vtx_mosi` GPIO18 → **GPIO14**, `vtx_miso` GPIO23 → unset,
`vtx_amp_pwm` GPIO12 → **GPIO13** (PNP drive stage, BR-02). The stock
`Unified_ESP32_2400_RX` build runs with that JSON; ELRS has run on the ESP32-PICO since
bd4f4e7f (#1526, V). Package pins come from the PICO datasheet Table 4 (V); every used GPIO
has the same pin number on the ESP32-D0WD-V3 (the withdrawn BR-01 fallback; its library
parts are kept, not on the board).

| ESP32 GPIO | Pin | ELRS key | Net | To | Notes |
|---|---|---|---|---|---|
| GPIO3 (U0RXD) | 40 | `serial_rx` | `UART0_TX` | FC GPIO0 | CRSF 420 kbaud |
| GPIO1 (U0TXD) | 41 | `serial_tx` | `UART0_RX` | FC GPIO1 | ROM boot log at power-up; Betaflight ignores it |
| GPIO25 | 14 | `radio_sck` | `RADIO_SCK` | SX1281 SCK | |
| GPIO32 | 12 | `radio_mosi` | `RADIO_MOSI` | SX1281 MOSI | |
| GPIO33 | 13 | `radio_miso` | `RADIO_MISO` | SX1281 MISO | |
| GPIO27 | 16 | `radio_nss` | `RADIO_NSS` | SX1281 NSS | |
| GPIO26 | 15 | `radio_rst` | `RADIO_RST` | SX1281 NRESET | |
| GPIO36 | 5 | `radio_busy` | `RADIO_BUSY` | SX1281 BUSY | input only |
| GPIO37 | 6 | `radio_dio1` | `RADIO_DIO1` | SX1281 DIO1 | input only (SENSOR_CAPP) |
| GPIO22 | 39 | `led_rgb` | `RX_LED` | XL-1010RGBC (WS2812) DIN | one LED: the overlay sets `ledidx_rgb_vtx` to `[0]` (the layout assumes two). The LED runs on +3V3, below its 3.5-5.5 V supply range: decided at P4 (spec §15.5 P4-15) |
| GPIO19 | 38 | `vtx_nss` | `VTX_SPI_CS` | RTC6705 SPI LE through 1 kΩ | HSPI with hardware CS. The 1 kΩ series resistors on all three VTX SPI lines keep stock ELRS from back-powering the RTC6705 while the HD line holds +3V3_VTX off (F21) |
| GPIO14 (MTMS) | 17 | `vtx_mosi` | `VTX_SPI_DATA` | RTC6705 SPIDATA (bidirectional, 3-wire) through 1 kΩ | moved from GPIO18 (in-package flash on the PICO; D53); not a strap. Production reads use 3-wire half-duplex on this pin (F8) |
| GPIO5 | 34 | `vtx_sck` | `VTX_SPI_CLK` | RTC6705 SPICLK through 1 kΩ | strap pin (default pull-up), harmless into a CMOS input |
| - | - | `vtx_miso` | - | **unset** | ELRS only writes the RTC6705 (`transfer32`, no reads in `devVTXSPI.cpp`, V). GPIO23 is the in-package flash DI on the PICO (Fig. 8), so the key is left unset; if the layout loader insists on a pin, an input-only one (GPIO35/38/39, I). The production test application reads half-duplex on GPIO14 instead (F8) |
| GPIO13 (MTCK) | 20 | `vtx_amp_pwm` | `VTX_AMP_PWM` | two-pole RC (2x 1 kΩ + 2x 1 µF, ≤ 100 Hz, about −70 dB at 10 kHz) → base of the BC857BM PNP; emitter through Re (start 10-15 Ω) to +3V3_VTX, collector → 10 Ω → choke → RTC6705 PAOUT1 (spec §4.8, D52 BR-02). ELRS `MIN_PWM` 2000 / `MAX_PWM` 3700 are firmware constants, not target keys | **not a strap**, free on both the PICO and the D0WD. The stage **inverts** (lower duty = more drive, F15) and feeds PAOUT1 in current mode; Re sets the YOLO ceiling (26-30 mA at 27 Ω, 49-66 mA at 10 Ω; I, `research/bomred/verify/pnp_fix.py`). At reset the pin is an input, so the stage can conduct up to that ceiling into a PA held off by GPIO2: harmless, measured in V5. A PNP on GPIO12 would pull that strap to about 2.6 V at reset, hence the move (overlay, no code) |
| GPIO12 (MTDI) | 18 | - | - | **no-connect** | strap: must read low at reset (3.3 V VDD_SDIO for the flash); with nothing on the pin its internal pull-down holds it, so the VDD_SDIO eFuse burn is optional and its order no longer matters (F18) |
| GPIO4 | 24 | `vtx_amp_vpd` | `PA_DET` | SE5004L DET via 1 kΩ / 100 pF | ADC2_CH0: cannot be read while Wi-Fi is on, which is not a flight state (I); same pin on the Happymodel AIO target. ELRS reads raw `analogRead()` counts at the default 11 dB attenuation (range to about 3 V), without eFuse calibration (per-unit calibration is an O6 item) |
| GPIO2 | 22 | `vtx_amp_vref` | `PA_EN` | straight to the EN of the switched 2.85 V PA reference (TI LP5907SNX-2.85, ±2 %, from **+3V3_VTX**, D53 BR-03), whose output is SE5004L VREF/EN | **strap**: reads low at reset through its own 45 kΩ strap pull-down and the LP5907's internal 1 MΩ EN pull-down (no external pull-down and no series resistor: BR-03, BR-12; LP5907 VEN is rated −0.3..6 V to GND whatever VIN does, V). Low = reference off (active discharge) = PA off. ELRS holds it low at init and in pit mode, but drives it high at power index 1 (disarmed with `vtx_low_power_disarm`). In HD mode the reference loses its input with +3V3_VTX, whatever GPIO2 does. The reference, not the GPIO, sets VREF (2.79-2.91 V at ±2 %; SE5004L window 2.80-2.90 V, qualified in V5) at about 10 mA |
| GPIO0 | 23 | `button` | `RX_BOOT` | shared button SW1 through D8 (D65; the RXB pad is gone, D67) | strap, internal pull-up; GND at reset = download mode |
| GPIO21 | 42 | (patched ELRS: VTX power) | `VTX_PWR_CTL` | through 1 kΩ (R84, was 10 kΩ: ruling 2026-10-09, EN then stays < 0.3 V) to `VTX_PWR_EN`, the +3V3_VTX LDO (LP5912-3.3) EN, which has a 100 kΩ pull-up to +3V3 | default on, so stock ELRS runs the VTX unchanged; the patched firmware pulls it low (open-drain style) in pit and when disarmed, with the VTX SPI pins tri-stated, and re-sends the frequency at power-up (spec §12 gate 4). The HD gate (AP1606) pulls the EN low in HD mode whatever the ESP32 does (F21) |
| GPIO34 | 10 | (patched ELRS: PA temperature) | `PA_NTC` | Murata NCP03XH103F05RL next to the PA + Yageo RC0201FR-0710KL divider from +3V3 | ADC1, input only; thermal derate (spec §12 patch 6), read only in the `hwTimer::isTick` window like the detector: powering an ADC pulls GPIO36 (radio BUSY) low for about 80 ns (ESP32 erratum 3.11, F19) |
| EN (CHIP_PU) | 9 | - | `RX_EN` | 10 kΩ to +3V3 + 1 µF | the datasheet says never leave it floating |
| GPIO15 (MTDO) | 21 | - | - | no-connect | strap (boot log on) |
| CMD/IO11, CLK/IO6 | 30 / 31 | flash | - | **no-connect** | in-package flash (Table 4: "Used for connecting in-package flash") |
| GPIO7/8/9/10, GPIO20 | 32/33/28/29, 27 | - | - | no-connect | free GPIOs of the VDD_SDIO domain (on the ESP32-PICO-V3-02 alternate, pins 28/29 go to its PSRAM) |
| VDD_SDIO | 26 | - | - | no external part | its capacitor is inside the package (Fig. 8) |
| NC | 25, 35, 36, 44, 45, 47, 48 | - | - | no-connect | Table 4 |
| GPIO38 / GPIO39 / GPIO35 (SENSOR_CAPN, SENSOR_VN, VDET_2) | 7, 8, 11 | - | - | no-connect | input-only GPIOs, unused |
| GND (EP) | 49 | - | `GND` | via-in-pad array | exposed pad |
| VDDA, VDDA3P3, VDD3P3_RTC, VDD3P3_CPU | 1, 43, 46; 3, 4; 19; 37 | - | +3V3 | 10 µF + 100 nF (Espressif Fig. 11) | the BR-01 set keeps C82 10 µF and C76 100 nF |
| LNA_IN | 2 | Wi-Fi RF | `RF_WIFI` | R88 0 Ω + C132/C133 (DNP) pi match → `RF_WIFI_ANT` → AE2 Johanson 2450AT07A0100001T chip antenna (D58, Wi-Fi restored) | ELRS Wi-Fi update mode is a bench-only mode (+3V3 peaks at about 0.48 A, ruling 2026-10-09) |

**BR-01 fallback (ESP32-D0WD-V3): withdrawn** by the owner (D55: "use the SiP"; D61: never fall back). The D0WD-V3 / GD25Q32 / 40 MHz library parts stay in the project library, not in bom_plan or on the board.

The FC has no VTX pin. Power and pit mode go FC → (MSP-VTX over CRSF) → ESP32. Stock
ELRS pit only drops GPIO2 (PA VREF) and sets the maximum PWM count; it never writes
the RTC6705 power-down (`POWER_AMP_OFF` is defined but unused, V), so the RTC6705
keeps running and transmits its own output through the off PA (leakage at the U.FL
measured in V5). In analog mode there is no true hardware VTX OFF until the patched
firmware uses GPIO21. In HD mode there is one: the FC's HD line (GPIO27, PINIO1)
switches the +3V3_VTX LDO off through the AP1606 HD gate (D17, D53 BR-03), which takes the
RTC6705, the PNP drive stage and the PA reference (all on +3V3_VTX) down together, and the
1 kΩ series resistors on the three VTX SPI lines limit what the still-writing ESP32 can
push into the unpowered RTC6705 (≤ 3 mA per line into the LDO's active discharge;
V9 checks +3V3_VTX and PA_VREF < 0.5 V). Round 2 rejected an FC switch for exactly that back-feed;
the series resistors are the answer (F21).

---

## 7. ESC MCU pin plan (4x EFM8BB51F16I-C-QFN20, Bluejay layout BB51 "A")

Spec §4.4 chose EFM8BB51 + Bluejay, so AM32 does not apply. The layout file was
fetched 2026-10-07 from `bird-sanctuary/bluejay` (HEAD `0368d11`, identical to
track 05's copy): `PWM_ACTIVE_HIGH 1`, `COM_ACTIVE_HIGH 0`, `COMPARATOR_PORT 0`,
P1 push-pull for all six gate pins, `P1_INIT` = Com pins high (P-FETs off). The pin
numbers are from EFM8BB51 data sheet Rev 1.0, Table 6.1 (V).

### 7.1 Per channel (n = 1..4)

One `esc_channel` sheet is instanced four times (`ESC1`..`ESC4`), so its nets are
in-sheet local labels and KiCad names them `/ESCn/<label>`: the Net column gives the
in-sheet label, which the setup_board.py net-class patterns match (`/ESC?/PHASE_?`,
`/ESC?/?_COM`, `/ESC?/?_PWM`). "ESCn_..." elsewhere in the docs is shorthand.

| QFN-20 pin | Port | Layout A role | Net (in-sheet) | Connects to |
|---|---|---|---|---|
| 1 | P0.1 | `B_Mux` (CMP0.P0) | `BEMF_B` | phase B through series R (BEMF network) |
| 2 | P0.0 | unused | - | no-connect |
| 3 | GND | | GND | |
| 4 | VDD | | `+BATT` | its own cluster's +BATT copper, no series R (it must track the P sources); 100 nF X6S at the pin; the phase-B hot-loop cap (10 µF X6S 0402, C23 / C29 / C35 / C41) within 4 mm through the +BATT plane is the datasheet's 1 µF bulk (BR-05 amended, D77; C30 deleted) |
| 5 | RSTb / C2CK | reset | `C2CK` | C2CK test pad; internal pull-up only (F12: the 1 kΩ of datasheet Fig 5.2 is dropped, lean rule) |
| 6 | P2.0 / C2D | `DebugPin` (push-pull output in layout A) | `C2D` | C2D test pad only, nothing else on the net |
| 7 | P1.6 | unused | - | no-connect |
| 8 | P1.5 | `C_Com` (active low) | `C_COM` | AGM210MAP G2 (pin 4, P gate), phase C |
| 9 | P1.4 | `C_Pwm` (active high) | `C_PWM` | AGM210MAP G1 (pin 2, N gate), phase C |
| 10 | P1.3 | `B_Com` | `B_COM` | AGM210MAP G2 (P gate), phase B |
| 11 | P1.2 | `B_Pwm` | `B_PWM` | AGM210MAP G1 (N gate), phase B |
| 12 | GND | | GND | |
| 13 | P1.1 | `A_Com` | `A_COM` | AGM210MAP G2 (P gate), phase A |
| 14 | P1.0 | `A_Pwm` | `A_PWM` | AGM210MAP G1 (N gate), phase A |
| 15 | P0.7 | unused | - | no-connect |
| 16 | P0.6 | unused | - | no-connect |
| 17 | P0.5 | `RTX_PIN` | `RTX` | 2.4 kΩ (Ralec RTT012401FTH) to FC `MOTORn` (hierarchical pin) |
| 18 | P0.4 | `V_Mux` (CMP0.N1) | `NEUTRAL` | star point of three phase resistors |
| 19 | P0.3 | `A_Mux` (CMP0.P2) | `BEMF_A` | phase A through series R |
| 20 | P0.2 | `C_Mux` | `BEMF_C` | phase C through series R |
| EP | GND | | GND | Type VII via-in-pad |

There are no gate resistors, by field record (tinyPEPPER drives its gates directly, V). The
datasheet's ≤ 60 Ω is the VOH limit at 10 mA, not a gate resistance; edge currents of
about 0.13-0.17 A for nanoseconds are a transient exceedance of the 50 mA per-pin absolute
maximum (Table 4.1), accepted on field record (tinyPEPPER, Matrix parity; spec §4.4).
Gate nets are class Gate and stay off In2/In3. AGM210MAP stage (D56): each package carries
both gates on its lead side (pin 2 G1 = N gate = x_PWM, pin 4 G2 = P gate = x_COM; pin 1 S1 =
GND, pin 3 S2 = +BATT, pins 5-8 + the two drain EPs = phase), and the EFM8 sits on the same side
as its three packages (single-sided cells), so the six gate lines run 0.15 mm on the package
layer from EFM8 pins 8/9 (slot L, phase C), 10/11 (slot M, B) and 13/14 (slot R, A) without
vias or crossings; the phase copper leaves from the drain side to the motor land. One 10 µF
hot-loop cap per package sits across pins 3 and 1 at the lead side (D77). (The TI fallback's
P gate on the CSD25310Q2 drain row needed a Type VII via and an L6 run; spec §4.3.) Phase nets: in-sheet `PHASE_A/B/C` = motor pads `Mn` A/B/C. Bluejay
sets the direction, so pad order is free.

### 7.2 FC ↔ ESC map

| Motor (Betaflight quad-X) | Position | FC GPIO (pin) | ESC block (spec §10) | Motor pads |
|---|---|---|---|---|
| M1 | rear right | GPIO25 (37) | ESC1, right-ear quadrant | bottom edge, x +4…+8 |
| M2 | front right | GPIO24 (36) | ESC2, right-ear quadrant | right edge, y +4.5…+8.5 |
| M3 | rear left | GPIO23 (35) | ESC3, left-ear quadrant | left edge, y −7…−3 |
| M4 | front left | GPIO22 (34) | ESC4, left-ear quadrant | top edge, x −7…−3 |

All four motor pins sit on one side of the QFN (pins 34-37). Two lines therefore run
about 12-15 mm to the far quadrant. DShot is slow (≤ 750 kbit/s for telemetry), so
this is a placement fact for P5, not a signal-integrity problem (I).

### 7.3 Behaviour that sets the pin plan

- **Reset and bootloader state** (I, from the datasheet reset values + `BLHeliBootLoad.inc`):
  the bootloader enables the crossbar with weak pull-ups (`XBR2 = 40h`) and leaves
  the gate pins open-drain with their latches at 1. So all P gates are pulled high
  (off) and all N gates weakly high (on): the motor is braked and no current comes
  from the supply. There is no shoot-through path. Every BB51 layout A board
  (Matrix II) behaves the same.
- **Flashing:** blank EFM8s carry no BLHeli bootloader; NextPCB pre-programs the bootloader
  and the stock Bluejay build before reflow (D67), bench recovery over C2 on the 8 test vias
  with +BATT fed at 3.3 V (spec §12.1, F18). After that, Betaflight 4-way passthrough over
  `MOTORn` (2026.6.2+, untested with BB51 on RP2350: spec gate V9).
- **Firmware:** stock Bluejay BB51 "A". The release build is a V2 outcome (spec §4.3,
  §12), derived for the AGM210MAP stage (D56): DS VER2.73 gives td(off) + tf = 32 + 26 =
  58 ns for the N side (VGS 4.5 V, RGEN 3.3 Ω) and 74 + 10 = 84 ns for the P side (RGEN
  1 Ω), Qg 23 / 33 nC and Qgd 4.2 / 11 nC. The EFM8 port (VOH ≤ 60 Ω class at 10 mA) drives
  the gates harder than nothing but softer than the datasheet's 1-3.3 Ω, so the real
  turn-off is longer (I): first power-up on **`A_X_10_96`** (DT about 204 ns, 2.4x the P
  figure), then **`A_X_5_96`** (about 102 ns, the build the Matrix II ships on this stage)
  once V2 shows no shoot-through at every corner (FET case 100 °C, VIN 4.35 V plus regen,
  both current directions). `A_X_15_96` (306 ns) was sized for the TI fallback's
  CSD13202Q2 N turn-off. Temperature protection on at 100 °C in the published settings.
- **Unused pins** P0.0, P0.6, P0.7, P1.6 stay defined: Bluejay leaves them digital
  open-drain with the weak pull-up on. Trimming their pads off the footprint is
  allowed electrically. Solder balance on a 3x3 QFN decides it at P3 (I).

---

## 8. Mapping to the spec

The GPIO assignment equals DESIGN-SPEC §4.5's map, pin for pin. Each pin was checked
against the source constraints in §4. The corrections below were folded back into
DESIGN-SPEC in its review revision; the table stays as the record:

| Spec item | Here |
|---|---|
| §4.5 "LED strip (via level-shift FET, as OpenFC)" | the OpenFC stage inverts the signal. Replace it (F1): direct drive from GPIO8 since D52 BR-04 |
| §4.5 "DMA: DShot 4-8 … ≤ 15 of 16" | DShot uses none: 8 of 16 (F6) |
| §4.5 "`PIO_LEDSTRIP_INDEX` untested override" | code-checked; PIO1 now holds only the LED strip. Still a bench gate (F5) |
| §4.4 "SWD to pads" | pins 24/25 → pads CLK/DIO. OpenFC leaves them unconnected, so this is new on the sheet |
| §4.5 "BOOT pad (QSPI_SS)" | through 1 kΩ, per the RPi guide |
| §4.9 "CS pull-up" | on both CS lines (gyro and NOR) |
| §12 "VBAT scale measured" | `DEFAULT_VOLTAGE_METER_DIVIDER 100` for 0.5 % steps |
| §12 target | needs `config.mk` + `pico_flash_mem.ld` (F3) |
| §4.7 ESP32 pins | `vtx_miso` GPIO23 left unconnected (F8); D53: ESP32-PICO-V3, `vtx_mosi` GPIO14, `vtx_miso` unset, `vtx_amp_pwm` GPIO13 (§6). Wi-Fi radiator, auto-Wi-Fi off at flash time (F9) |
| §4.8 "PWM → RC → transistor follower" | must be an inverting stage for the ELRS loop (F15); D52: one PNP in current mode on GPIO13 |
| §4.5 "2 free UARTs" | round 2: one user UART (UART1), GPIO2/3 spare; round 3 (D16): UART1 = O4, user UART on PIOUART0 (GPIO2/3), PIO1 shared with the LED strip |
| §4.2 USB OR diode + boost sense FET | replaced by the TPS2116 mux, boost always on (round 3); F16 updated |
| D13-D17 O4 Lite | UART1 + MSP DisplayPort, PINIO1 on GPIO27, `USE_OSD_HD` defaults, HD gate (F20, F21) |

---

## 9. Conflicts and open items

| # | Item | Status | Resolution / owner |
|---|---|---|---|
| F1 | **LED strip driver.** The OpenFC LED stage (AP1606 N-FET, gate on GPIO8, drain to pad with 2.4 kΩ to +5V) **inverts** the data. Betaflight's PICO WS2812 driver has no inversion option (side-set, no `outover`; V) | **resolved: (a) direct drive (D52 BR-04)** | Do not copy it. GPIO8 drives the LED pad directly, with no series resistor, like the other user pads: the Matrix II does the same (`BETAFPVG473_V2` `LED_STRIP_PIN PB2`, no buffer seen on the photos; V / I). A WS2812 at 5.15 V wants VIH 3.6 V against the 3.3 V high (widely flown, I), so the README carries the Betaflight / Cleanflight inline-diode note ("inline diode on the VIN", V) and V9 tests a strip. The round-4 choice (b), the Nexperia 74LVC1T45GS (SOT1202, 0.35 mm pitch, in the O15 EQ) with two caps, is deleted (−3 parts, −1 line); its 0.5 mm-pitch sibling 74LVC1T45GM (SOT886) is the fallback if V9 fails. The OpenFC-Lite-Mini LED output should be checked for the same defect |
| F2 | **MSP-VTX over CRSF default.** On 2026.6.2 the RX port needs `FUNCTION_VTX_MSP` set by CLI. `VTX_MSP_UART` is **harmful on 2026.6.2**: `pgResetFn_serialConfig` assigns (not ORs) RX_SERIAL to `SERIALRX_UART` and then VTX_MSP to `VTX_MSP_UART` (`serial.c` L316-321, L353-358), so with both on UART0 the default has no receiver, and `isSerialConfigValid()` rejects a lone VTX_MSP and resets to the same default (L541-544, `config.c` L230): no CRSF link on a fresh flash, and ELRS's `devMSPVTX` times out after 5 s, so its vtxtable is never written | **resolved (config), firmware open** | `VTX_MSP_UART` removed from `config.h` (§5.1); production applies the §5.4 UART0 line and saves before the first ELRS boot (spec §12.1 step 4); the line ships in the README and the first-flash dump. Re-add the define only for a release with the master `vtx_uart` model |
| F3 | **Flash size.** RP2350A builds default to 8 MB / 4 MB layout; the RP2354A has 2 MB | resolved | `config.mk` + `pico_flash_mem.ld` (§5.2-5.3). Check what the house target does |
| F4 | **EFM8 VIH margin and VDD + 0.3 V.** VIH = 0.7 x VDD and VDD follows the cluster +BATT with its PWM ripple: 0.2 V at DC on a 4.35 V cell, 0.04-0.11 V at the ripple peaks of the 96 kHz builds, negative at 48 kHz; at a 2.5-2.8 V sag the 3.3 V high is 0.2-0.5 V over P0.5's VDD + 0.3 V absolute maximum, current-limited by the 2.4 kΩ to < 0.1 mA (§4.5) | accepted (Matrix parity, which also runs 96 kHz); 48 kHz builds not used | Stock Bluejay cannot report a rejected frame (checksum failures only bump an internal counter, no telemetry reply; EDT status carries no error count; no command echo; V, `Isrs.asm` l. 155-194, `Scheduler.asm` l. 212-248), so V9 scopes the DShot high level against 0.7·VDD at the EFM8 pin and counts failures with a non-release Bluejay debug build that pulses the layout-A DebugPin (P2.0 = the C2D pad) on each, on a fresh 4.35 V pack under load; V3c checks the VDD peak. No cheap fix: a translator per channel costs 4 parts and adds delay |
| F5 | **LED strip and PIOUART0 on PIO1** (`PIO_LEDSTRIP_INDEX 1`, `PIO_UART_INDEX 1`): 23 of 32 instructions, 3 of 4 SMs. No upstream config combines FB OSD + LED strip, or LED strip + PIOUART on one block | code-verified (2026.6.2 `target_RP2350.h`, `uart_pio.c`, `light_ws2811strip_pico.c`), hardware-untested | Bench gate V9: LED strip + FB OSD + PIOUART0 + the O4 on UART1 at the same time on the OpenFC-Lite-Mini; fallback: O4 on PIOUART0 and the user UART on UART1 |
| F6 | Spec DMA count wrong (DShot needs no DMA) | resolved | 8 of 16 |
| F7 | **SPI NOR blackbox on RP2350**: `USE_FLASH` only from 2026.6.2, and no upstream RP2350 config uses SPI NOR | open (gate V9) | Spec gate: 2 kHz logging without loop overrun |
| F8 | ESP32 `vtx_miso`; RTC6705 reads | resolved (D53) | `vtx_miso` unset: GPIO23 is the in-package flash DI on the ESP32-PICO-V3 (the D0WD fallback is withdrawn, D55 / D61). The RTC6705 SPI is 3-wire (SPIDATA bidirectional, read data on SPICLK falling edges, datasheet §4), so the production verify and counterfeit screen (register 0x00 = 0x0190) run an ESP32 test application from RAM that uses 3-wire half-duplex SPI on GPIO14 (`vtx_mosi`, moved from GPIO18 by D53), reading through its 1 kΩ series resistor (spec §4.8, §12.1) |
| F9 | ESP32 LNA_IN and ELRS Wi-Fi | **revised (D58)** | Wi-Fi restored: LNA_IN (pin 2) -> `RF_WIFI` -> R88 0 Ω series + C132 / C133 shunt (DNP) pi match -> `RF_WIFI_ANT` -> AE2 Johanson 2450AT07A0100001T chip antenna at a board edge with the maker's clearance (DRU `D21 wifi_antenna_edge_strip`); values from V7 tuning. ELRS Wi-Fi is a bench-only update mode (disarmed; +3V3 peaks at about 0.48 A on the LP5912, ruling 2026-10-09); `devWIFI.cpp` still calls `disableVTxSpi()` when Wi-Fi starts, so the VTX goes dark in Wi-Fi mode (O6 patch item). The round-3 "no radiator" call (D25) is reversed; flashing no longer uses `--no-auto-wifi` |
| F10 | Manufacturer ID: spec proposes INCU, house uses unregistered OPFC | open (lineup) | Register INCU in the config PR; FOSS is the registered fallback |
| F11 | `GYRO_1_ALIGN` and the sign of `DEFAULT_ALIGN_BOARD_YAW` | open, P5 | from the placed LGA orientation; the alternative is to rotate the gyro 45° on the PCB and drop the board yaw |
| F12 | EFM8 RSTb: datasheet Fig 5.2 shows 1 kΩ to VDD | resolved: dropped | Lean rule: most BB51 ESCs rely on the internal pull-up (S); the land is kept only if P2 has room |
| F13 | CLKIN slice shared with M4/M3 PWM slices | benign | DShot-only build in practice; documented |
| F14 | GPIO2, GPIO3, GPIO27 spare (round 2) | resolved (D16, D15) | GPIO2/3 = PIOUART0 user pads, GPIO27 = PINIO1 HD line; no spare GPIO left |
| F15 | **PA drive polarity (`vtx_amp_pwm`, ESP32 GPIO13 after D53; GPIO12 in the stock layout).** ELRS lowers the PWM count to raise output (`VTxOutputIncrease` decrements; `VTxOutputMinimum` sets the maximum count and drops GPIO2; calibration arrays have lower counts at 100 mW than at 25 mW; V, `devVTXSPI.cpp`). A follower would turn the VPD loop into positive feedback; a single common emitter with a collector pull-up has a resistive output that sags under the PAOUT1 load | **resolved (spec §4.8; D52 BR-02, gated by P4 SPICE)** | The usable ELRS window is 49-90 % duty (`MIN_PWM` 2000 = YOLO, `MAX_PWM` 3700 = pit, `setDuty(count*1000/4096)`, firmware constants; V at 8c51826), 1.6-3.0 V after the RC. Stage: two-pole RC (2x 1 kΩ + 2x 1 µF) → base of one Nexperia BC857BM PNP, emitter through Re to +3V3_VTX, collector → 10 Ω → choke → PAOUT1, in current mode. Lower duty pulls the base lower and drives more current, so it inverts as needed; Re (start 10-15 Ω) sets the YOLO ceiling and the slope (corrected model, `research/bomred/verify/pnp_fix.py`: 26-30 mA at 27 Ω, 49-66 mA at 10 Ω, pinch-off ≥ 3400 counts, about 255 duty steps in the 10-90 % span), and V5 sets it so the highest-output sample at 4.35 V and 25 °C stays ≤ 27 dBm at the U.FL; a minimum part never reaches 400 mW at 3.0 V (minimum P1dB scaled to 3.0 V is about 25.2-25.6 dBm), so 400 mW is not guaranteed at sag. The pin moves to GPIO13 because a PNP base on GPIO12 would pull that strap to about 2.6 V at reset (I). Fallback if SPICE fails: round 4's two-NPN stage (one BC847QASZ, strap-safe) with the PS-12 values (spec §4.8) |
| F16 | **Power sequencing.** USB only: DShot idle-high back-feeds +BATT (towards about 2.5-2.8 V with µA loads, EFM8s near POR); the always-enabled boost may hiccup on that weak source, but the TPS2116 mux keeps +5V on USB, so only the EFM8s can cycle. USB hot-plug or unplug with a cell fitted is a break-before-make mux switchover (8 µs) onto a running boost; on unplug +5V first follows VBUS down to the PR1 threshold (27.4k/10k: 3.44-4.04 V), so its minimum is about 3.1-3.7 V and +3V3 stays ≥ about 3.0 V (spec §4.2). Battery only: the mux's leakage into the USB input is typically 0.15 µA at 105 °C (no maximum published) into the 37.4 kΩ PR1 divider; nothing senses that node since D53 BR-10 removed the AP1606 USB term (the O4 switch now sits on `+5V_BST`, which USB never reaches), and round 2's Schottky leakage problem is gone with it. Battery first: EFM8 pull-ups reach unpowered FT pads for 1-2 ms, an abs-max (3.63 V) voltage excursion if the pad floats up | documented (§4.5), bench V1/V9 | Measure +BATT on USB only, watch for brown-out cycling, confirm +5V stays on USB; hot-plug USB with a cell fitted (no FC reset); battery only at 85/105 °C board; scope the FT pads against 3.63 V at power-up; fallbacks: 10 kΩ DShot series R (current), a 3.3 V-domain clamp or DShot-path enable (voltage) |
| F17 | **MSP-VTX boot window.** `devMSPVTX` stops for good if it has not reached MONITORING within 5 s of ESP32 boot (`MSP_VTX_TIMEOUT_NO_CONNECTION`, V); the VTX then stays in pit until the RX reboots. RP2350 Betaflight boot time (gyro config upload, FB OSD PAL/NTSC detection, USB) is unmeasured | open, bench V9 | Cold boot x 20 with and without the TX on, timing the VTX state restore |
| F18 | **Production first flash.** Blank EFM8s have no BLHeli bootloader (4-way passthrough cannot reach them); a blank ESP32 must be strapped into download mode for its first flash; the VDD_SDIO eFuse may be burned in the same session | resolved (spec §12.1, D65 / D67) | After D65 / D67 the only access to ESP32 GPIO0 is the shared button SW1 on BOOT_SW, which also pulls QSPI_SS low through D8: holding it at power-up puts the RP2354A in BOOTSEL too. Working sequence: (1) hold SW1 (or a fixture probe on BOOT_SW) while applying power: RP2354A BOOTSEL + ESP32 ROM download, each latched until that chip's next reset; (2) write the Betaflight UF2 (or `picotool reboot`): the RP2354A restarts into Betaflight while the ESP32 stays in download mode; (3) esptool through Betaflight serial passthrough, then ELRS with the board's layout JSON; (alternative: a blank ESP32's RTC-watchdog boot loop re-latches the straps at each system reset while SW1 is held). The same sequence recovers a bricked ELRS image (README). EFM8: NextPCB pre-programs Bluejay (D67); bench recovery over C2 on the test vias with +BATT at 3.3 V (VIH 2.31 V for a 3.3 V adapter). **D53:** GPIO12 is unconnected (`vtx_amp_pwm` moved to GPIO13), so its internal pull-down holds the 3.3 V-flash strap on its own: the eFuse burn is optional and its order no longer matters. The RXB / GND pads and the pogo fixture are gone (D67) |
| F19 | **ESP32 erratum 3.11**: powering SAR ADC1/ADC2 pulls GPIO36/39 low for about 80 ns; GPIO36 is radio BUSY | resolved in firmware rules | Stock ELRS reads the detector (ADC2) only in the `hwTimer::isTick` window; the planned NTC read (ADC1, GPIO34) must follow the same rule (spec §12 patch 6); V7 checks packet loss with the derate active |
| F20 | **DJI O4 Lite on UART1** (D13, D16): MSP DisplayPort needs the HD OSD in the build and a port with VTX_MSP + MSP | resolved in the config (§5.1, §5.4) | No `USE_OSD_SD` define (alone it leaves `USE_OSD_HD` undefined and `displayport_msp.c` forces the canvas to SD 30 x 16); `MSP_DISPLAYPORT_UART SERIAL_PORT_UART1` and `PINIO1_CONFIG 129` inside `#ifdef USE_OSD_HD`, which `config.h` sees only for a cloud OSD (HD) build (it is read before `common_pre.h`; behaviour per build type in the §5.1 table: OSD (SD)-only = analog, OSD (HD) = HD mode with the analog VTX off, plain OSD or local `make` = neither until a preset); MSP never on UART0 (Betaflight takes the first port with both bits, `config.c` L568-581). UART1 therefore carries VTX_MSP + MSP (DisplayPort needs both), while the MSP-VTX device binds UART0 first once the §5.4 UART0 line has set VTX_MSP there (`findSerialPortConfig` order VCP, UART0, UART1, ...), so ELRS keeps the analog-VTX control path; on a fresh HD flash before that line it binds the O4 port, which is harmless in HD mode. The O4 has dedicated pads (VHD GND TX1 RX1), so RX1 never has two drivers. On USB only the O4 has no usable supply: its switch sits on `+5V_BST` ahead of the mux, which USB never reaches (D53 BR-10), and the cell threshold holds it off at the back-fed 2.5-2.8 V; with USB and a cell both present it runs from the boost. V9 bench |
| F21 | **HD line (GPIO27, PINIO1)** enables the O4 supply (TPS22810 EN, wired-AND with the cell threshold: shed 2.80-3.09 V, re-enable 3.27-3.77 V with the 33k/18k divider, 510 kΩ hysteresis and 100 nF EN filter, D53 BR-22) and holds the analog VTX off (D17, D53 BR-03: one AP1606 pulls the +3V3_VTX LDO EN low; the PA reference and the PNP drive stage sit on +3V3_VTX and go off with the RTC6705) | resolved (spec §4.2, §4.8) | 2.4 kΩ pull-down = analog mode at reset (BR-24; EN ≤ 0.87 V through the BAS16LD); OSD (SD)-only build default low, OSD (HD) build default 129 (§5.1 table); HD preset 129. VTX SPI lines carry 1 kΩ series so the still-writing ESP32 cannot back-power the unpowered RTC6705; no ESP32 input senses the HD line (stock ELRS has no key for it), so the hardware hold-off is the authority. V5: no carrier above −80 dBm EIRP in HD mode; V9: +3V3_VTX and PA_VREF < 0.5 V |
| F22 | **VTX defaults vs ELRS's first session**: ELRS `clearVtxTable()` resets power, pit and low-power-disarm on the first connection (§5.4) | resolved in production (spec §12.1) | Boot ELRS once with the FC before applying the defaults (or ship the exact ELRS vtxtable in the diff); defaults vtx power 2 (RCE) and `vtx_low_power_disarm` OFF until ELRS patch (3); V8 checks the power-up PA current |

Nothing in the pin plan blocks the layout (the open gate is the board area, spec §9). F1, F15, F20, F21 and the PA reference add parts, all in the spec's area budget v4; F9 and F12 removed parts. D52 trims them again: F1 to direct drive, F15 to one PNP and five passives, F21 to one AP1606 (spec §9.4).

---

## Appendix A. G473 fallback (documented in spec §4.5, no dual footprint)

If the V9 gates fail and the owner switches to STM32G473CEU6 + AT7456E, adapt
**`BEFH/BETAFPVG473_V3`** ("SUPPORTED TARGET", 2025-12-01: diamond board, yaw −45,
CLKIN, all motors on GPIOB). V2 (Matrix II) is the alternative: it puts motors on 3 GPIO
ports and SmartAudio on UART2. Changes from V3: no baro/I2C; **no `PINIO1` on PA13**,
because V3 spends SWDIO on "VTX PWR" and we keep SWD; no SmartAudio (ESP32 MSP-VTX);
crystal-less `SYSTEM_HSE_MHZ 0` as on `BETAFPVG473` v1 (track 05 #6), or 8 if the
crystal stays. Package pin numbers come from ST DS Table 12 at P3, if this path is taken.

| Function | Pin | Timer option (occurrence in `timer_stm32g4xx.c`, V) |
|---|---|---|
| M1 / M2 | PB0 / PB1 | TIM3_CH3 / TIM3_CH4 (occ 1) |
| M3 / M4 | PB6 / PB9 | TIM4_CH1 / TIM4_CH4 (occ 2); occ 3 would be TIM8, which bitbang needs |
| LED strip | PB2 | TIM5_CH1 (occ 1), DMA opt 0 |
| Gyro CLKIN | PA1 | TIM2_CH2 (occ 1), no DMA |
| Beeper | PA8 | GPIO, inverted (TIM1_CH1 unused) |
| CRSF (ESP32) | UART3 PB10/PB11 | |
| Pads TX1/RX1 | UART1 PA9/PA10 (UART2 PA2/PA3 left unused) | |
| Gyro | SPI1 PA5/PA6/PA7, CS PC14, EXTI PC15 | |
| OSD AT7456E | SPI2 PB13/PB14/PB15, CS PB12 | |
| NOR | SPI3 PB3/PB4/PB5, CS PC13 | |
| VBAT / CURR | PA4 (ADC2) / PA0 (ADC1) | `ADC1_DMA_OPT 6`, `ADC2_DMA_OPT 7` |
| LED0 / LED1 | PC6 / PC4 | |
| USB, SWD, BOOT0, NRST | PA11/PA12, PA13/PA14, PB8-BOOT0, PG10-NRST | |

Timer/DMA check (I, from the V3 allocation and the bitbang source): DShot bitbang
(`DSHOT_BITBANG_ON`) takes TIM8 for the single GPIOB port, plus one auto-assigned DMA
channel. TIM3/TIM4 with DMA opts 1-4 are only the non-bitbang fallback. TIM5 = LED,
TIM2 = CLKIN, TIM1 unused. DMAMUX gives 16 channels: LED 0, ADC 6/7, motor fallback
1-4, and bitbang + SPI1/2/3 (6) auto-assigned from the rest. That is ≤ 12 in use and
no two features on one channel.

```c
#pragma once
#define FC_TARGET_MCU        STM32G474
#define BOARD_NAME           OPENAIO_WHOOP_G4
#define MANUFACTURER_ID      INCU

#define USE_ACC
#define USE_GYRO
#define USE_ACCGYRO_BMI270
#define USE_ACC_SPI_ICM42688P
#define USE_GYRO_SPI_ICM42688P
#define USE_GYRO_CLKIN
#define USE_FLASH
#define USE_FLASH_M25P16
#define USE_MAX7456

#define BEEPER_PIN           PA8
#define MOTOR1_PIN           PB0
#define MOTOR2_PIN           PB1
#define MOTOR3_PIN           PB6
#define MOTOR4_PIN           PB9
#define LED_STRIP_PIN        PB2
#define UART1_TX_PIN         PA9
#define UART1_RX_PIN         PA10
#define UART3_TX_PIN         PB10
#define UART3_RX_PIN         PB11
#define LED0_PIN             PC6
#define LED1_PIN             PC4
#define SPI1_SCK_PIN         PA5
#define SPI1_SDI_PIN         PA6
#define SPI1_SDO_PIN         PA7
#define SPI2_SCK_PIN         PB13
#define SPI2_SDI_PIN         PB14
#define SPI2_SDO_PIN         PB15
#define SPI3_SCK_PIN         PB3
#define SPI3_SDI_PIN         PB4
#define SPI3_SDO_PIN         PB5
#define ADC_VBAT_PIN         PA4
#define ADC_CURR_PIN         PA0
#define FLASH_CS_PIN         PC13
#define MAX7456_SPI_CS_PIN   PB12
#define GYRO_1_EXTI_PIN      PC15
#define GYRO_1_CS_PIN        PC14
#define GYRO_1_CLKIN_PIN     PA1

#define TIMER_PIN_MAPPING \
    TIMER_PIN_MAP( 0, LED_STRIP_PIN,    1,  0 ) \
    TIMER_PIN_MAP( 1, MOTOR1_PIN,       1,  1 ) \
    TIMER_PIN_MAP( 2, MOTOR2_PIN,       1,  2 ) \
    TIMER_PIN_MAP( 3, MOTOR3_PIN,       2,  3 ) \
    TIMER_PIN_MAP( 4, MOTOR4_PIN,       2,  4 ) \
    TIMER_PIN_MAP( 5, GYRO_1_CLKIN_PIN, 1, -1 )

#define ADC1_DMA_OPT         6
#define ADC2_DMA_OPT         7

#define SERIALRX_UART        SERIAL_PORT_USART3
#define SERIALRX_PROVIDER    SERIALRX_CRSF
#define VTX_MSP_UART         SERIAL_PORT_USART3
#define DEFAULT_BLACKBOX_DEVICE        BLACKBOX_DEVICE_FLASH
#define DEFAULT_DSHOT_BURST            DSHOT_DMAR_OFF
#define DEFAULT_DSHOT_BITBANG          DSHOT_BITBANG_ON
#define DEFAULT_DSHOT_TELEMETRY        DSHOT_TELEMETRY_ON
#define DEFAULT_CURRENT_METER_SOURCE   CURRENT_METER_ADC
#define DEFAULT_VOLTAGE_METER_SOURCE   VOLTAGE_METER_ADC
#define DEFAULT_CURRENT_METER_SCALE    500
#define DEFAULT_VOLTAGE_METER_SCALE    200
#define DEFAULT_VOLTAGE_METER_DIVIDER  100
#define BEEPER_INVERTED
#define SYSTEM_HSE_MHZ       0
#define MAX7456_SPI_INSTANCE SPI2
#define FLASH_SPI_INSTANCE   SPI3
#define GYRO_1_SPI_INSTANCE  SPI1
#define GYRO_1_ALIGN         CW180_DEG     // set at P5
#define DEFAULT_ALIGN_BOARD_YAW  -45
```

---

## 10. Verification log (2026-10-07)

| # | Claim | Evidence | Result |
|---|---|---|---|
| 1 | QFN-60 pin numbers | RP2350 datasheet Fig 2 (`05-dl/ds/rp2350.txt` l. 963-1060) and the OpenFC netlist (`kicad-cli sch export netlist`, U10) | match for all 61 pads |
| 2 | GPIO function mux (UART0 0/1, UART1 4/5, SPI1 10-13, SPI0 18-21, PWM 3A on 6) | datasheet Table 677 | confirmed |
| 3 | Allowed pins in Betaflight | `uart_hw.c`, `bus_spi_pico.c` (master 498430a) | all chosen pins listed |
| 4 | PIO budgets | `dshot_pio_programs.h` (13/29), `uart_*_program.c` (10/9), ws2812 (4), `osd_tx.pio.h` (31/31/25) | 23/32 on PIO1 (WS2812 + PIOUART0), 31/32 on PIO2 |
| 5 | DMA users | grep of `dma_claim_unused_channel`/`dmaGetFreeIdentifier` across `src/platform/PICO` | SPI, OSD, LED, ADC, QSPI (unused) only |
| 6 | 2026.6.2 = master for the PICO files used | raw.githubusercontent fetch at tag 2026.6.2 + diff | identical except `AFATFS_NUM_CACHE_SECTORS` |
| 7 | `VTX_MSP_UART` on 2026.6.2 | `io/vtx.c`, `io/vtx_msp.c` at both refs; **`io/serial.c` `pgResetFn_serialConfig` L316-321 / L353-358, `isSerialConfigValid()` L541-544, `config/config.c` L230 at 2026.6.2** (round 4; the first check missed `serial.c`) | **harmful on 2026.6.2**: it overwrites the RX_SERIAL mask of UART0 (plain assignment), leaving no receiver; removed from `config.h`; 2026.6.2 needs both port functions by CLI |
| 8 | Flash layout defaults 8 MB / 4 MB; override files honoured at 2026.6.2 | `target_RP2350.mk`, `pico_flash_mem_defaults.ld`, `mk/config.mk` l. 50-51, `RP2350.mk` l. 499-506 | confirmed |
| 9 | Beeper/LED polarity | `sound_beeper.c` l. 43, `beeper_dev.c`, `light_led.c` l. 88 | inverted beeper = high on; LED default = low on |
| 10 | Voltage scale formula and macros | `sensors/voltage.c` l. 104-165 at master and 2026.6.2 | scale/divider = 2 for 10k/10k |
| 11 | FT pads 0-25, ADC pads not FT, reset pull-downs, VOH/VIH, pull values | datasheet §9.3, §14.9 Table 1683, pin-type table | confirmed |
| 12 | EFM8BB51 QFN-20 pins, VIH 0.7 VDD, RPU 70-220 kΩ | data sheet Rev 1.0, Table 6.1, §4.1 port I/O table | confirmed |
| 13 | Bluejay layout A pin roles; bootloader RTX behaviour | `src/Layouts/BB51/A.inc`, `src/BLHeliBootLoad.inc` at 0368d11 | confirmed |
| 14 | ELRS whoop RX+VTX pins; no RTC6705 reads; vtxtable push | `RX/Generic 2400 Whoop Rx and VTx.json` (master), `devVTXSPI.cpp`, `devMSPVTX.cpp` (master) | confirmed |
| 15 | ESP32 QFN-48 pin numbers | ESP32 datasheet pin overview (documentation.espressif.com) | confirmed |
| 16 | LED-strip stage inverts on OpenFC | netlist: Q6 AP1606 gate = GPIO8, source GND, drain = LED_STRIP pad + R51 2.4 kΩ to +5V | confirmed |
| 16b | ELRS PA loop polarity | `devVTXSPI.cpp` l. 143-196 (`RfAmpVrefOn/Off`, `VTxOutputMinimum/Increase/Decrease`), l. 280-300 (`checkOutputPower`) | lower PWM = more output; pit mode = GPIO2 low + maximum count |
| 17 | G4 timer occurrences | `src/platform/STM32/timer_stm32g4xx.c` (master) | PB0/PB1 occ1 TIM3, PB6/PB9 occ2 TIM4, PB2 occ1 TIM5, PA1 occ1 TIM2 |
| 18 | DMA IRQ core | `dma_pico.c` l. 121-125, `target_RP2350.h` l. 24-28 | `DMA_IRQ_CORE_NUM` only with `USE_MULTICORE`, which is commented out: all on core 0 (corrects the first version) |
| 19 | Low-power disarm and pit behaviour | Betaflight `vtx_msp.c` l. 103-128; ELRS `devVTXSPI.cpp` l. 253-300, `devMSPVTX.cpp` l. 217-219, 385-388 | index 1 when disarmed; index 1 keeps VREF on; `POWER_AMP_OFF` unused; 5 s MSP-VTX timeout |
| 20 | Bidirectional DShot decode errors | `dshot_bidir_pico.c` l. 55-60 (2026.6.2 = master) | upstream expects about 5-8 % errors with spinning motors, < 1 % at 0 rpm |
| 21 | PIOUART0/1 and the PIO index defaults on RP2350 | `target_RP2350.h` 2026.6.2 l. 32-33 (`USE_PIOUART0/1`), l. 90-105 (`PIO_UART_INDEX 1`, `PIO_LEDSTRIP_INDEX 2`, `PIO_OSD_INDEX 2`); `serial.h` (`SERIAL_PORT_PIOUART0` = 70) | confirmed (round 3) |
| 22 | O4 DisplayPort selection, HD OSD build, PINIO | `config.c` L568-581, `common_pre.h`, `displayport_msp.c` l. 248-257, `pinio.c` l. 45-72 (study-1-2s digital-vtx §2) | confirmed: first port with VTX_MSP + MSP; SD-only build resets HD to AUTO; PINIO config 129 = high at init. Round 4: `platform.h` includes `config.h` before `target/common_pre.h` (master L26 / L29), `pg/vcd.c` and `osd/osd.c` L418-427 default to HD / MSP whenever `USE_OSD_HD` is compiled, `fc/init.c` L947 forces MSP in HD: defaults per build type in §5.1 |
| 23 | ELRS first-session vtxtable push, RCE and low-power-disarm handling | `devMSPVTX.cpp` l. 71-96 (`clearVtxTable`: power 3, pit 0, LPD 0, EEPROM write), l. 211-219; Betaflight `msp.c` l. 3829-3842 | confirmed (round 3) |
| 24 | ESP32-PICO-V3 pin numbers, NC pins, in-package flash pins (D52 BR-01, 2026-10-09) | Espressif PICO series datasheet v1.3 Table 4 and Fig. 8 (BOM study local copy) | GPIO14 = pin 17, GPIO13 = pin 20, GPIO12 = pin 18, every other used GPIO on the same pin as the D0WD; pins 30/31 flash, 25/35/36/44/45/47/48 NC; GPIO16/17/18/23 not exposed |
| 25 | Layout overlay and ESP32-PICO support in ELRS (D53) | `UnifiedConfiguration.py` l. 57-58 (`hardware.update(config['overlay'])`); commit bd4f4e7f (#1526) | any layout key can be overridden by the board JSON; PICO targets run `Unified_ESP32_2400_RX` |
| 26 | PNP drive model (D52 BR-02) | `research/bomred/verify/pnp_fix.py` (base-current sign corrected against the first `pnp.py`) | YOLO 26-30 mA at Re 27 Ω, 49-66 mA at 10 Ω; pinch-off ≥ 3400 counts; 10-90 % span counts 2121-3141. P4 SPICE is the gate |

Not verified: the house OpenFC-Lite-Mini custom target settings (not public); whether
the Matrix II buffers its LED-strip output; the EFM8BB51 reset-state wording for
crossbar-off pull-ups (the bootloader enables the crossbar within about 100 µs, so it
does not change the conclusion).

## 11. Sources

- Betaflight firmware, master `498430a` (2026-10-07) and tag `2026.6.2`: https://github.com/betaflight/betaflight — `src/platform/PICO/{target/common/target_RP2350.h, target/RP2350A/target.h, target/common/target_RP2350.mk, link/*.ld, mk/RP2350.mk, dshot_pico.c, dshot_bidir_pico.c, dshot_pio_programs.h, uart/*.c, light_ws2811strip_pico.c, osd/osd_pico.c, osd/osd_tx.pio.h, bus_spi_pico.c, adc_pico.c, dma_pico.c, gyro_clkin_pico.c, pwm_beeper_pico.c}`, `src/main/{target/common_pre.h, target/common_post.h, io/vtx.c, io/vtx_msp.c, io/serial.c, io/serial.h, pg/motor.c, pg/beeper_dev.c, pg/flash.c, drivers/sound_beeper.c, drivers/light_led.c, sensors/voltage.c, sensors/current.c, drivers/accgyro/accgyro_spi_icm426xx.c}`, `src/platform/STM32/{timer_stm32g4xx.c, dshot_bitbang.c}`, `mk/config.mk`
- betaflight/config `1e3f778` (2026-10-06, re-cloned 2026-10-07, unchanged): https://github.com/betaflight/config — `configs/RASP/{RASPBERRY_PI_UAVFC (config.h, config.mk, pico_flash_mem.ld), HELLBENDER_0001, PICO2_2350A}`, `TEBS/TBS_LUCID_RPI_FC`, `MADF/MADFLIGHT_FC3`, `BEFH/{BETAFPVG473, BETAFPVG473_V2, BETAFPVG473_V3}`, `HAMO/CRAZYBEE473`, `Manufacturers.md`
- Raspberry Pi RP2350 datasheet (copy built 2026-10-01): https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf ; Hardware design with RP2350: https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- OpenFC-Lite-Mini KiCad project (house, read-only sibling clone), netlist exported with kicad-cli 10: https://github.com/OpenDrone-hw/OpenFC-Lite-Mini
- Silicon Labs EFM8BB51 Data Sheet Rev 1.0 (local copy `scratchpad/dl/ds/efm8bb51.pdf`)
- Bluejay `0368d11` (2026-04-22): https://github.com/bird-sanctuary/bluejay — `src/Layouts/BB51/A.inc`, `src/BLHeliBootLoad.inc`
- ExpressLRS targets (master, 2026-10-07): https://github.com/ExpressLRS/targets — `RX/Generic 2400 Whoop Rx and VTx.json`, `targets.json`; ExpressLRS master: `src/lib/VTXSPI/devVTXSPI.cpp`, `src/lib/MSPVTX/devMSPVTX.cpp`, `src/lib/MSPVTX/freqTable.h` — https://github.com/ExpressLRS/ExpressLRS
- Betaflight 2026.6.2 for the O4 integration: `src/platform/PICO/target/common/target_RP2350.h`, `src/main/io/serial.h`, `src/main/config/config.c`, `src/main/target/common_pre.h`, `src/main/io/displayport_msp.c`, `src/main/drivers/pinio.c`, `src/platform/PICO/uart/uart_pio.c` (study-1-2s `digital-vtx.md` §2-3); round 4: `src/main/io/serial.c` (reset masks, validity check), `src/main/platform.h` (include order), `src/main/pg/vcd.c`, `src/main/osd/osd.c`, `src/main/fc/init.c` (OSD device defaults)
- TI TPS2116 (USB/boost power mux): https://www.ti.com/lit/ds/symlink/tps2116.pdf
- Espressif ESP32 Series Datasheet: https://documentation.espressif.com/esp32_datasheet_en.pdf
- Espressif ESP32-PICO Series Datasheet v1.3 (Table 4, Fig. 8, Fig. 11): https://espressif.com/sites/default/files/documentation/esp32-pico_series_datasheet_en.pdf
- [BOM-REDUCTION.md](BOM-REDUCTION.md) and its track reports in `research/bomred/` (D52-D54, 2026-10-09)
- [DESIGN-SPEC.md](DESIGN-SPEC.md), research tracks 01 and 05 (scratchpad)
