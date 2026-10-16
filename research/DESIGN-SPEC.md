# OpenAIO-Whoop electrical design reference

| Function | Fitted implementation |
| --- | --- |
| Input | 1S LiPo, 3.0 to 4.35 V intended operating range |
| FC | RP2354A, 2 MB in-package flash; 12 MHz oscillator |
| IMU | BMI270; 1.8 V VDD and 3.3 V VDDIO |
| Blackbox | Puya PY25Q128HA, 16 MB, single SPI |
| ESCs | Four EFM8BB51 layout-A controllers, twelve AGM210MAP half-bridges |
| Motor interface | FXMAR2104UMX bidirectional translator, 3.3 V to battery-level domain |
| Receiver | ESP32-PICO-V3 and SX1281, ExpressLRS serial receiver |
| Analog video | SN74LVC1G3157 overlay mux; TLV7031 sync comparator; RTC6705 and SE5004L VTX |
| Main supply | TPS61022 boost, diode OR with USB, TLV75733 3.3 V regulator |
| Analog supplies | LP5912 3.3 V VTX rail; TPS7A20285 PA reference; TPS7A2018 gyro rail |

The schematic defines exact values, connections and fitted/DNP states.
[PINMAP.md](PINMAP.md) and the checked-in firmware bindings define logical
interfaces. [ROUTING.md](ROUTING.md) defines placement and layer use. Earlier
floorplan and architecture proposals remain in Git history and are not
instructions to regenerate the present board.

## Supply and bypass details

The BMI270 has dedicated 100 nF capacitors C137/C138 at pins 5 and 8. C61/C62
are separate 4.7 uF capacitors at the gyro regulator input/output. Bosch's local
bypass recommendation and TI's regulator stability requirement are different
constraints. The former 1 uF 0201 output part had insufficient demonstrated
capacitance margin after voltage, tolerance and temperature effects. The chosen
4.7 uF part remains 0201 and provides substantially more margin.

For an ICM-42688-P population, use its own local network: 10 nF on VDDIO and
100 nF plus 2.2 uF on VDD, with the appropriate firmware driver/orientation.
The fitted BOM and target use BMI270. A shared land pattern does not make the
bypass population interchangeable.

C52 and C56 provide the RP core's two nominal 4.7 uF bulk positions; C50/C51
remain 100 nF. C52 belongs by DVDD pin 23. Do not reinstate the removed C134
merely because an old drawing mentions it.

U4 uses TLV75733PDRVR because the aggregate distributed +3.3 V capacitance no
longer has comfortable margin to the LP5912's 10 uF maximum. TLV757 supports
1 to 200 uF nominal output capacitance. Its pin 3 is GND and pin 5 is NC;
it is not pin-for-pin identical to LP5912 despite the matching package.
D11 bypasses reverse discharge from output to input as TI recommends:
anode to +3.3V, cathode to +5V. D9/D10 retain source isolation upstream.
U21 remains LP5912 for the quieter dedicated VTX supply.

U22 is TPS7A20285PDQNR. Its specified 1.5% accuracy under the relevant input
and load conditions gives 2.807 to 2.893 V, inside SE5004L's 2.8 to 2.9 V
reference range. Q28 and the associated R11 pull-down are removed. GPIO19
high enables the analog rail; low disables it. R68 retains the analog-on
reset default. The VHD supply is independent and remains battery-boost fed.

## Motor interfaces

The ESC gate outputs are actively driven by Bluejay during operation. The
schematic does not add speculative gate pull resistors. U24 addresses a
separate condition: the battery-powered ESC and the FC can be powered in
different orders. It translates all four bidirectional DShot lines and
isolates them when either supply is absent. R12/R19/R26/R33 are 22 ohms.

Use the correct BB51 layout-A firmware and qualify dead time, startup,
regeneration and telemetry on the assembled board. Neither the Matrix's
current rating nor its firmware timing is a measured rating for this PCB.
The shunt/INA186 path is nominally 50 mV/A. The shunt and thermal design set
additional current limits independently of the ADC scale.

## Camera and onboard VTX

The OpenFC-Lite OSD topology is retained: 75 ohm camera termination, a raw
camera/overlay analog switch and a separately filtered, AC-coupled,
Schottky-clamped sync comparator. Its demonstrated operation is not discarded
on the basis of a hypothetical comparator failure. Input common-mode margin
across cameras, startup and temperature remains a prototype qualification
item; it is not evidence that the existing circuit fails.

The camera interface expects nominal 1 Vpp composite video into 75 ohms,
with sync near ground and the main signal within the analog switch's
0 to 3.3 V operating range. The sync clamp does not DC-restore the main video
path. This is the same input-baseline assumption as OpenFC-Lite.

The onboard RTC6705 network presents approximately 1.47 kohms at low
frequency. With the fitted overlay divider and approximately 7 ohms mux
resistance, nominal black/white levels are about 0.23/0.89 V. These are circuit
calculations, not scope measurements. Do not add the OpenFC external-output
stage's gain of two and 75 ohm source resistor to this local connection.
C70 must locally bypass both U14 and U15 with short connections.

Retain X4 TAXM8M4RDBCCT2T, 8 MHz / 10 pF, 3.2 by 2.5 mm. No exact smaller
passive 8 MHz replacement was verified. A small active oscillator would be a
different circuit, not a footprint substitution.

ESP32-PICO-V3 remains fitted. ESP8685/C3 can drive SPI control electrically,
but the audited ExpressLRS source excludes integrated VTX registration on C3.
The PICO package also includes flash and its 40 MHz crystal. Replacing it is
a firmware and layout change, not an equivalent smaller part substitution.

RTC6705 and SE5004L do not establish a calibrated output-power table. Their
specified RF ranges overlap at 5725 to 5850 MHz; broader FPV channel tables
need characterization. The PA's recommended supply starts at 3.0 V.
Do not claim a fixed 400/500 mW output across all channels and battery levels
without measurements.

## Primary references

- [Bosch BMI270 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf), supply pins and reference bypass.
- [TDK ICM-42688-P datasheet](https://invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf), alternative operating circuit.
- [TI TPS7A20](https://www.ti.com/lit/ds/symlink/tps7a20.pdf), effective output capacitance and reference accuracy.
- [TI TLV757P](https://www.ti.com/lit/ds/symlink/tlv757p.pdf), pin mapping, capacitance range and reverse-current bypass.
- [TI LP5912](https://www.ti.com/lit/ds/symlink/lp5912.pdf), dedicated VTX regulator limits.
- [Raspberry Pi RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), RP2354A supplies and FT-pad limits.
- [onsemi FXMAR2104](https://www.onsemi.com/download/data-sheet/pdf/fxmar2104-d.pdf), bidirectional operation and supply sequencing.
- [TI SN74LVC1G3157](https://www.ti.com/lit/ds/symlink/sn74lvc1g3157.pdf) and [TLV7031](https://www.ti.com/lit/ds/symlink/tlv7031.pdf), video mux and sync comparator.
- [Skyworks SE5004L](https://www.skyworksinc.com/-/media/SkyWorks/Documents/Products/601-700/SE5004L_202393B.pdf), PA supply, reference and RF limits.
- [Espressif PICO series](https://documentation.espressif.com/esp32-pico_series_datasheet_en.pdf), integrated components and GPIO package mapping.
- [ExpressLRS audited source](https://github.com/ExpressLRS/ExpressLRS/tree/dd96654519249798707f011b7c79236350f246f8), receiver/VTX firmware integration.
- [BetaFPV Matrix II](https://betafpv.com/products/matrix-1s-5in1-ii-brushless-flight-controller), package grouping and mechanical inspiration only; its product claims do not validate this circuit.
