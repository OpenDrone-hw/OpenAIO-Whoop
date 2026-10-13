# OpenAIO-Whoop pin map

This map describes the fitted schematic. Package pin numbers include exposed pads.
The KiCad netlist and the checked-in firmware targets are the implementation sources.
`hardware/tools/check_netlist.py` compares every RP2354A and ESP32 pin below.

## 1. Firmware interfaces

| Function | Binding |
| --- | --- |
| Flight controller | [Betaflight target](../firmware/betaflight/README.md), pinned 2026.6.2 |
| Motor signals | GPIO4/6/18/20 through U24, bidirectional 3.3 V to battery-level DShot |
| Analog video | W21, EN22, active-low SYNC23; PIO2 |
| Analog permission | GPIO19 high enables U21, low disables it; PINIO default 129 |
| HD port | UART0 GPIO16/17; VHD remains battery-boost powered |
| Receiver | UART1 GPIO8/9, CRSF plus MSP-VTX; ESP32 controls the RTC6705 and PA |
| Gyro | BMI270 default; final physical orientation must be set after placement |

## 2. RP2354A signal pins

| Pin | Package function | Net |
| --- | --- | --- |
| 2 | GPIO0 | `SPI0_MISO` |
| 3 | GPIO1 | `FLASH_CS` |
| 4 | GPIO2 | `SPI0_SCK` |
| 5 | GPIO3 | `SPI0_MOSI` |
| 7 | GPIO4 | `MOTOR1_FC` |
| 8 | GPIO5 | `LED_STRIP` |
| 9 | GPIO6 | `MOTOR2_FC` |
| 10 | GPIO7 | `GYRO_INT` |
| 12 | GPIO8 | `UART1_TX` |
| 13 | GPIO9 | `UART1_RX` |
| 14 | GPIO10 | `LED0` |
| 15 | GPIO11 | `SPI1_MOSI` |
| 16 | GPIO12 | `SPI1_MISO` |
| 17 | GPIO13 | `GYRO_CLKIN` |
| 18 | GPIO14 | `SPI1_SCK` |
| 19 | GPIO15 | `GYRO_CS` |
| 27 | GPIO16 | `UART0_TX` |
| 28 | GPIO17 | `UART0_RX` |
| 29 | GPIO18 | `MOTOR3_FC` |
| 31 | GPIO19 | `HD_EN` |
| 32 | GPIO20 | `MOTOR4_FC` |
| 33 | GPIO21 | `OSD_W` |
| 34 | GPIO22 | `OSD_EN` |
| 35 | GPIO23 | `OSD_SYNC` |
| 36 | GPIO24 | `LED1` |
| 37 | GPIO25 | `BEEPER` |
| 40 | GPIO26_ADC0 | `ADC_CURR` |
| 41 | GPIO27_ADC1 | `ADC_VBAT` |
| 42 | GPIO28_ADC2 | - |
| 43 | GPIO29_ADC3 | - |

## 3. RP2354A power and system pins

| Pin | Package function | Net |
| --- | --- | --- |
| 1 | IOVDD | `+3.3V` |
| 6 | DVDD | `+1.1V` |
| 11 | IOVDD | `+3.3V` |
| 20 | IOVDD | `+3.3V` |
| 21 | XIN | `XIN` |
| 22 | XOUT | - |
| 23 | DVDD | `+1.1V` |
| 24 | SWCLK | `SWCLK` |
| 25 | SWDIO | `SWDIO` |
| 26 | RUN | `+3.3V` |
| 30 | IOVDD | `+3.3V` |
| 38 | IOVDD | `+3.3V` |
| 39 | DVDD | `+1.1V` |
| 44 | ADC_AVDD | `+3.3V` |
| 45 | IOVDD | `+3.3V` |
| 46 | VREG_AVDD | `VREG_AVDD` |
| 47 | VREG_PGND | `GND` |
| 48 | VREG_LX | `VREG_LX` |
| 49 | VREG_VIN | `+3.3V` |
| 50 | VREG_FB | `+1.1V` |
| 51 | USB_DM | `U10_USB_D_N` |
| 52 | USB_DP | `U10_USB_D_P` |
| 53 | USB_OTP_VDD | `+3.3V` |
| 54 | QSPI_IOVDD | `+3.3V` |
| 55 | QSPI_SD3 | - |
| 56 | QSPI_SCLK | - |
| 57 | QSPI_SD0 | - |
| 58 | QSPI_SD2 | - |
| 59 | QSPI_SD1 | - |
| 60 | QSPI_SS | `QSPI_SS` |
| 61 | EP | `GND` |

## 4. Power and reset behavior

U24 isolates the motor interfaces when either supply is absent. Its VCCA and OE
use +3.3V; VCCB uses +BATT. Each ESC signal has 22 ohms in series. The gate outputs of the four
EFM8BB51 controllers are actively driven during normal Bluejay operation.
The translator does not replace firmware dead time or reset qualification.

R68 pulls HD_EN high for analog operation. Q28 and R11 are removed. U21 controls
the analog synthesizer supply; U22 controls the PA reference. VHD is independent.

## 5. Peripheral allocation

PIO0 serves the four motor state machines. PIO1 drives the LED strip. PIO2
serves the analog OSD. SPI0 serves the external 16 MB blackbox, while SPI1
serves the IMU. The RP2354A boot flash is the separate 2 MB in-package device.

## 6. Receiver MCU pin plan

| ESP32 GPIO | Pin | Package function | Net |
| --- | --- | --- | --- |
| supply/system | 1 | VDDA | `+3.3V` |
| supply/system | 2 | LNA_IN | `RF_WIFI` |
| supply/system | 3 | VDDA3P3 | `+3.3V` |
| supply/system | 4 | VDDA3P3 | `+3.3V` |
| 36 | 5 | SENSOR_VP/I36 | `PA_DET` |
| 37 | 6 | SENSOR_CAPP/I37 | - |
| 38 | 7 | SENSOR_CAPN/I38 | - |
| 39 | 8 | SENSOR_VN/I39 | `RADIO_BUSY` |
| supply/system | 9 | EN | `RX_EN` |
| 34 | 10 | VDET_1/I34 | `RADIO_DIO1` |
| 35 | 11 | VDET_2/I35 | - |
| 32 | 12 | 32K_XP/IO32 | `RX_LED` |
| 33 | 13 | 32K_XN/IO33 | `VTX_AMP_PWM` |
| 25 | 14 | IO25 | `RADIO_RST` |
| 26 | 15 | IO26 | `RADIO_NSS` |
| 27 | 16 | IO27 | `RADIO_SCK` |
| 14 | 17 | MTMS/IO14 | `RADIO_MOSI` |
| 12 | 18 | MTDI/IO12 | - |
| supply/system | 19 | VDD3P3_RTC | `+3.3V` |
| 13 | 20 | MTCK/IO13 | `RADIO_MISO` |
| 15 | 21 | MTDO/IO15 | - |
| 2 | 22 | IO2 | - |
| 0 | 23 | IO0 | `RX_BOOT` |
| 4 | 24 | IO4 | - |
| supply/system | 25 | NC | - |
| supply/system | 26 | VDD_SDIO | - |
| 20 | 27 | IO20 | `VTX_SPI_CLK` |
| 9 | 28 | SD2/IO9 | - |
| 10 | 29 | SD3/IO10 | - |
| 11 | 30 | CMD/IO11_FLASH | - |
| 6 | 31 | CLK/IO6_FLASH | - |
| 7 | 32 | SD0/IO7 | - |
| 8 | 33 | SD1/IO8 | - |
| 5 | 34 | IO5 | - |
| supply/system | 35 | NC | - |
| supply/system | 36 | NC | - |
| supply/system | 37 | VDD3P3_CPU | `+3.3V` |
| 19 | 38 | IO19 | `VTX_SPI_DATA` |
| 22 | 39 | IO22 | `VTX_SPI_CS` |
| 3 | 40 | U0RXD/IO3 | `UART1_TX` |
| 1 | 41 | U0TXD/IO1 | `UART1_RX` |
| 21 | 42 | IO21 | `PA_EN` |
| supply/system | 43 | VDDA | `+3.3V` |
| supply/system | 44 | NC | - |
| supply/system | 45 | NC | - |
| supply/system | 46 | VDDA | `+3.3V` |
| supply/system | 47 | NC | - |
| supply/system | 48 | NC | - |
| supply/system | 49 | GND | `GND` |

## 7. ESC and motor interface

| Motor | FC GPIO | U24 A / B pins | ESC MCU | MCU DShot pin |
| --- | --- | --- | --- | --- |
| 1 | 4 | 3 / 12 | U6 | 17 |
| 2 | 6 | 4 / 11 | U7 | 17 |
| 3 | 18 | 5 / 10 | U8 | 17 |
| 4 | 20 | 6 / 9 | U9 | 17 |

The shared ESC sheet is instantiated four times. The following table shows
ESC1 local nets; the same pins apply to U7, U8 and U9.

Bluejay BB51 layout A senses phase X on the BEMF_X comparator input while it
drives X_PWM / X_COM (P1.2 Bp, P1.4 Cp, P0.1 Bm, P0.2 Cm). The half-bridge on
X_PWM must therefore sit on the phase node that the BEMF_X series resistor
taps. `check_netlist.py` rule N7 checks this per ESC. The netlist at the
base of the review fails N7: B_PWM drives Q31 (PHASE_C) and C_PWM drives Q30
(PHASE_B), while R14 (PHASE_B) feeds BEMF_B and R15 (PHASE_C) feeds BEMF_C. The
fix is to swap the two BEMF labels in `esc_channel.kicad_sch` (R14 to BEMF_C,
R15 to BEMF_B); it is a manual Eeschema edit listed in the pull request. The
MCU pin table below does not change. Motor pads J4 pins 1/2/3 are
PHASE_C/B/A.

| Pin | Package function | Net |
| --- | --- | --- |
| 1 | P0.1 | `BEMF_B` |
| 2 | P0.0 | - |
| 3 | GND | `GND` |
| 4 | VDD | `+BATT` |
| 5 | RSTb/C2CK | `C2CK` |
| 6 | P2.0/C2D | `C2D` |
| 7 | P1.6 | - |
| 8 | P1.5 | `C_COM` |
| 9 | P1.4 | `C_PWM` |
| 10 | P1.3 | `B_COM` |
| 11 | P1.2 | `B_PWM` |
| 12 | GND | `GND` |
| 13 | P1.1 | `A_COM` |
| 14 | P1.0 | `A_PWM` |
| 15 | P0.7 | - |
| 16 | P0.6 | - |
| 17 | P0.5 | `RTX` |
| 18 | P0.4 | `NEUTRAL` |
| 19 | P0.3 | `BEMF_A` |
| 20 | P0.2 | `BEMF_C` |
| 21 | GND | `GND` |

## 8. Implementation constraints

- Use Bluejay BB51 layout A. Establish dead time and telemetry performance on the prototype; a Matrix firmware filename is not validation of this PCB.
- Keep the OSD GPIOs consecutive. The hardware sync polarity is active low.
- Configure SX1281 for LDO mode. Keep the separate VTX SPI MISO disabled.
- Keep the ESP32-PICO-V3 population. ESP8685/C3 requires an integrated-VTX firmware port.
- Do not assign the RP2354A in-package flash pins to board peripherals.
- Final gyro orientation, RF power calibration and motor-to-frame ordering are set after placement and bench checks.
