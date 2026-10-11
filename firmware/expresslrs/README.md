# ExpressLRS hardware binding

[board-layout.json](board-layout.json) records the schematic's ESP32-PICO-V3
GPIO assignments using ExpressLRS hardware-field names. It is a pin binding
for completing a firmware target, not an installable target: radio telemetry
power calibration and VTX detector/PWM calibration arrays are intentionally
absent. Loading it alone as a complete target would enable the VTX device
without the arrays its power-control code expects.

The source baseline is ExpressLRS
[`dd96654519249798707f011b7c79236350f246f8`](https://github.com/ExpressLRS/ExpressLRS/tree/dd96654519249798707f011b7c79236350f246f8).
The binding was checked against its
[hardware parser](https://github.com/ExpressLRS/ExpressLRS/blob/dd96654519249798707f011b7c79236350f246f8/src/lib/OPTIONS/hardware.cpp)
and [unified receiver definitions](https://github.com/ExpressLRS/ExpressLRS/blob/dd96654519249798707f011b7c79236350f246f8/src/include/target/Unified_ESP_RX.h).
No firmware binary or RF power calibration is supplied here.

| Function | ESP32 GPIO | Connection |
|---|---|---|
| CRSF RX / TX | 3 / 1 | RP2354 GPIO24 TX / GPIO25 RX |
| SX1281 SCK / MOSI / MISO | 27 / 14 / 13 | Dedicated radio SPI |
| SX1281 NSS / RESET | 26 / 25 | Active low |
| SX1281 BUSY / DIO1 | 39 / 34 | Input-only ESP32 pins |
| Boot and bind button | 0 | Shared button through D8 |
| Addressable status LED | 32 | One LED, index 0 |
| RTC6705 SCK / MOSI / NSS | 20 / 19 / 22 | Separate HSPI bus through R81 / R82 / R80 |
| RTC6705 MISO | None | Explicit `vtx_miso: -1` |
| PA reference enable | 21 | U22 EN, high enables PA_VREF |
| RTC6705 RF drive control | 33 | PWM through R71 / Q27 |
| PA detector | 36 | ADC1 through R66 / C117 |

The fitted XL-1010RGBC-WS2812B sends its 24-bit LED data in GRB order;
`led_rgb_isgrb: true` matches its datasheet's data-structure section.

`radio_dcdc: false` selects the SX1281 LDO configuration fitted in the
schematic. Its DCC_SW pin is unconnected. GPIO20 is physically available on
ESP32-PICO-V3; a generic ESP32 module pinout is not the package pinout of U16.
The VTX registration path in the audited
[receiver source](https://github.com/ExpressLRS/ExpressLRS/blob/dd96654519249798707f011b7c79236350f246f8/src/src/rx_main.cpp)
supports this classic ESP32 architecture; changing U16 to ESP8685 requires a
separate firmware port.

The [VTX driver](https://github.com/ExpressLRS/ExpressLRS/blob/dd96654519249798707f011b7c79236350f246f8/src/lib/VTXSPI/devVTXSPI.cpp)
uses decreasing PWM duty to increase RF drive, matching Q27's PNP stage.
Retain this polarity. Its four-point detector and initial PWM arrays require
measurements of the assembled RF path; values from another board are not
calibration for this board. The fitted RTC6705 uses an 8 MHz crystal.

## Analog and HD power states

RP2354 GPIO19, net `HD_EN`, directly controls U21 EN. High powers the analog
VTX; low switches it off. R68 makes analog power the reset default. This
signal is distinct from ESP32 GPIO19, which is RTC6705 MOSI.

| State | RP2354 GPIO19 | ESP32 requirements |
|---|---|---|
| Analog initialization | High | PA_EN low, minimum RF drive, initialize RTC6705, then apply calibrated settings |
| Analog operating | High | Normal VTX control |
| Fixed HD build | Low after FC initialization | `vtx_nss: -1`; PA_EN low; VTX SPI pins input with no pull-ups; no VTX PWM peripheral |
| Runtime transition to HD | Goes low only after receiver acknowledgement | Stop VTX updates, disable PA reference, stop SPI and PWM, hold GPIO20/19/22 low before acknowledging |

Upstream derives VTX presence from `vtx_nss != -1`; there is no
`has_vtx_spi` hardware JSON field. Disabling VTX registration does not itself
drive PA_EN low, so the HD startup policy must also establish that output.
On return to analog, raise U21 EN before initializing the SPI peripheral and
hold PA_EN low until the RTC6705 has initialized and settled.

Pit mode and `disableVTxSpi()` do not implement this coordinated rail shutdown:
they do not guarantee that SPI activity has stopped or that chip select is
low. R80/R81/R82 limit current but do not isolate an unpowered RTC6705.
The runtime handshake is a firmware requirement, not an implemented feature
in this binding. A fixed analog or fixed HD configuration avoids a runtime
mode transition while that protocol is absent.

## Validation

Validate JSON syntax with `python3 -m json.tool firmware/expresslrs/board-layout.json`.
Before incorporating it into an upstream target, compare every key with the
pinned hardware parser and compare GPIO assignments with a fresh KiCad XML
netlist. Complete the omitted RF calibration before producing an installable
target.
