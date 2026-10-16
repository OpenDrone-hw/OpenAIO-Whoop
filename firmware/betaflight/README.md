# OpenAIO-Whoop Betaflight target

This target uses the fitted BMI270 and onboard analog video by default. It
includes HD DisplayPort support for the external UART0 pads. It is compiled
against Betaflight **2026.6.2**, commit
`e0b7bb01b17b21351057e9ead2d1ab39dd44fa16`, with that commit's Pico SDK.
The target is not registered in the upstream config repository; `FOSS` is the
manufacturer identifier until an identifier is registered.

| Resource | Configuration |
| --- | --- |
| MCU / boot flash | RP2354A / 2MB in-package flash |
| BMI270 | SPI1: SCK14, MISO12, MOSI11, CS15, INT7 |
| Blackbox | SPI0: SCK2, MISO0, MOSI3, CS1; Puya 16MB |
| Motors 1 to 4 | GPIO4, 6, 18, 20; PIO0 bidirectional DShot |
| ExpressLRS | UART1: TX8, RX9; CRSF with MSP-VTX |
| HD pads | UART0: TX16, RX17; disabled in the default serial profile |
| Analog OSD | W21, EN22, SYNC23; PIO2 |
| Analog VTX permission | GPIO19; high permits power, low forces it off |
| LED strip | GPIO5; PIO1 |
| Status / beeper | LEDs10/24, beeper25 |
| Analog inputs | VBAT27, current26 |

`config.c` uses the supported `USE_TARGET_CONFIG` reset hook. It preserves
CRSF while adding MSP-VTX on UART1 and selects analog AUTO OSD, with SD
element positions, even though HD support is compiled. The defaults apply on
configuration reset; saved user settings remain authoritative on normal boot.
This avoids the 2026.6.2 `VTX_MSP_UART` assignment overwriting the receiver
function. It does not depend on display-default macros introduced after that
release.

## Build

Use a Betaflight checkout at the pinned commit with its submodules and the
supported GCC 13.3.1 toolchain installed. From that checkout:

```sh
make -j8 fwo CONFIG=OPENAIO_WHOOP \
  CONFIG_DIR=/absolute/path/to/OpenAIO-Whoop/firmware/betaflight \
  EXTRA_FLAGS='-DOPENAIO_GYRO_ALIGN=<alignment> -DOPENAIO_BOARD_YAW=<degrees>'
```

Replace both placeholders with values derived from the placement of U11 on the
routed board and the intended mount. The build intentionally rejects an omitted
orientation. The compilation check used `CW0_DEG` and `0` solely as explicit build inputs;
those values are not an approved flight configuration.

The MCU's 2MB flash size and 16KB font reservation are defined in `config.mk`
and `pico_flash_mem.ld`. The external 16MB part is only the blackbox device.
Keep all four target files together; `config.c` is required for the defaults.

For an ICM-42688-P population, add `-DOPENAIO_IMU_ICM42688P` only after fitting
its specified bypass parts and establishing its sensor orientation. This
selects its driver and GPIO13 clock input. The BMI270 build is the validated
compilation profile.

## Video profiles

The analog defaults use `pinio_config = 129,1,1,1`. Inversion makes GPIO19
high when PINIO1 is inactive. Activating PINIO1 drives it low and forces the
analog VTX off. GPIO19 does not control the VHD supply, which is powered from
the battery boost.

For a fixed HD setup, select MSP DisplayPort on UART0, set video system to HD
and OSD display device to MSP, and set `pinio_config = 1,1,1,1` so GPIO19 is
low after initialization. Adjust the OSD canvas and positions for the connected
HD system. Returning to analog requires AUTO video/display, no DisplayPort
function on UART0, and `pinio_config = 129,1,1,1`.

ExpressLRS owns the onboard VTX channel/power table. Its board layout and power
calibration are separate from this FC target. Verify that first receiver boot
imports the intended table before applying final VTX power defaults.

## Validation boundary

The target has been compiled, linked into the 2MB layout, and checked against
the schematic GPIO map. No UF2 is committed as a flight release. The PCB's
final IMU orientation, sensor axes, USB enumeration, flash read/write,
OSD waveform and motor telemetry require hardware validation.

The pinned RP2350 bidirectional DShot driver documents approximately 5–8%
telemetry decoding errors with spinning motors from timing jitter. A
successful build does not establish telemetry performance on this board.
