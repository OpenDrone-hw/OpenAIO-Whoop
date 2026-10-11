# OpenAIO-Whoop

All-in-one board for 1S whoops, 65 to 85 mm class: a Betaflight flight
controller on an RP2354A, four Bluejay ESC channels (EFM8BB51 driving
AGM210MAP half-bridges), an onboard ExpressLRS 2.4 GHz receiver
(ESP32-PICO-V3 and SX1281) and an onboard analog VTX (RTC6705 and SE5004L)
with a PIO framebuffer OSD. A 26.4 mm body on the 25.5 x 25.5 mm whoop
pattern, the 1S sibling of [OpenAIO](https://github.com/OpenDrone-hw/OpenAIO).
It is not a 2S board: every rail is boosted or regulated from one cell.

## Architecture

One cell feeds everything. The battery pads, with a TVS across them, feed
`+BATT` through a Kelvin shunt (`power`). Each ESC channel (`esc_channel`,
one sheet placed four times as ESC1 to ESC4) is an EFM8BB51 running Bluejay
that drives three AGM210MAP P+N half-bridges straight from its port pins. There is no gate
driver, because at 1S the cell voltage is the gate drive. A BEMF divider per
phase feeds the EFM8 comparator, and the FC sends DShot to each EFM8 on one wire.

The RP2354A (`rp2350a`) runs Betaflight. It talks to the BMI270 on SPI1
(`imu`), which has its own 1.8 V LDO, and to a 16 MB SPI NOR blackbox on SPI0
(`blackbox`). The analog OSD is Betaflight's PIO framebuffer OSD: a TLV7031
sync comparator and an SN74LVC1G3157 switch put the OSD levels onto the camera
video (`osd`), and the result feeds the RTC6705 video input.

The ESP32-PICO-V3 + SX1281 (`rx_esp32_sx1281`) runs ExpressLRS and reaches the
FC as CRSF on hardware UART1. The same ESP32 also drives the VTX (`vtx`): the
RTC6705 over SPI, the RTC6705 output drive through a one-PNP current stage from
a PWM pin, the SE5004L PA enable and the PA power detector. Betaflight sets channel and power
over MSP-VTX through CRSF. The VTX hangs off the receiver because Betaflight
on RP2350 has no RTC6705 driver.

`HD_EN` (GPIO19) chooses the video path. High, it switches `+5V_HD` on to the
DJI O4 Lite pads and Q28 holds the analog VTX LDO off. Low, the analog VTX
runs. `pads` carries the plugs, motor lands, solder pads and USB ESD; `led`
carries the two status LEDs.

## Power

```
J2/J3 battery pads ─► D1 TVS ─► R1 0.5 mOhm Kelvin shunt (U1 INA186 ─► ADC_CURR) ─► +BATT
+BATT ─┬─► Q29-Q40 AGM210MAP half-bridges, U6-U9 EFM8 VDD
       ├─► R67 0R selector ─► SE5004L PA VCC (+5V position unfitted)
       └─► U2 TPS61022 boost ─► +5V_BST ─┬─► U5 TPS22810 (HD_EN) ─► +5V_HD ─► VHD pad
                                         └─► U3 TPS2116 VIN2
J31 VBUS ─► U24 SGM40661 inlet switch ─► +5V_USB ─► U3 TPS2116 VIN1 (priority)
U3 ─► +5V ─┬─► U4 LP5912-3.3 ─► +3.3V ─┬─► RP2354A ─► internal SMPS + L2 ─► +1.1V core
           │                           ├─► ESP32-PICO-V3, SX1281, NOR flash, OSD, INA186
           │                           └─► U12 TPS7A2018 ─► +1.8V_GYRO ─► BMI270 VDD
           ├─► U21 LP5912-3.3 (VTX_PWR_EN) ─► +3.3V_VTX ─┬─► RTC6705, PA drive stage
           │                                            └─► U22 LP5907-2.85 (PA_EN) ─► PA_VREF
           ├─► FB1 ─► +5V_CAM ─► camera plug J32 and pads
           └─► 5V pad J21 (LED strip, buzzer)
```

USB has priority on `+5V`, so a board on USB alone runs the FC, RX and OSD
without the boost. `+5V_HD` comes from the boost side only, so USB never
powers an O4. There is no reverse-polarity protection: a reversed battery
lead shorts the cell through the TVS and the FET body diodes.

## Key parts

| Function | Ref | Part | LCSC | Note |
|---|---|---|---|---|
| FC MCU | U10 | RP2354A, QFN-60, 2 MB in-package flash | C41378174 | X1 OT201612MJBA4SL 12 MHz CMOS oscillator on XIN |
| IMU | U11 | BMI270, LGA-14 | C2836813 | universal LGA-14 land, ICM-42688-P fits the same land |
| Blackbox | U13 | PY25Q128HA-DFH-IR, 16 MB SPI NOR | | SPI0 |
| ESC MCU | U6-U9 | EFM8BB51F16I-C-QFN20R | | Bluejay, layout BB51 "A" |
| Half-bridge | Q29-Q40 | AGM210MAP, P+N in PDFN-8 3.3 x 3.3 | C7431169 | one per phase, 22 uF 0603 cap across each supply pair |
| Battery shunt | R1 | HCS1206FTL500, 0.5 mOhm 1206 | C346511 | four-pad Kelvin land |
| Current amp | U1 | INA186A3, gain 100 | C2058245 | 50 mV/A |
| 5 V boost | U2 | TPS61022 | C915088 | 1 MHz forced PWM, L1 0.68 uH |
| USB inlet | U24 | SGM40661 | | VBUS hot-plug and over-voltage switch |
| 5 V mux | U3 | TPS2116 | C3235557 | USB over boost, priority mode |
| 3.3 V LDO | U4 | LP5912-3.3DRVR | C524780 | FC and RX rail |
| Gyro LDO | U12 | TPS7A2018 | C36996449 | +1.8V_GYRO |
| HD switch | U5 | TPS22810 | | +5V_HD for the O4 pads |
| RX MCU | U16 | ESP32-PICO-V3 SiP | C967022 | ELRS and VTX control |
| 2.4 GHz radio | U18 | SX1281 | C2151551 | LDO mode, X3 52 MHz TCXO, FL1 filter |
| VTX synthesiser | U19 | RTC6705, QFN-40 | C913074 | X4 8 MHz crystal |
| VTX PA | U20 | SE5004L | C210263 | FL2 harmonic band-pass, J1 U.FL |
| VTX LDOs | U21, U22 | LP5912-3.3, LP5907-2.85 | C524780 (U21) | +3.3V_VTX and PA_VREF, both switched |
| OSD | U14, U15, D3 | SN74LVC1G3157, TLV7031, SDM02U30LP3 | C2673087, C2876045, C151629 | level switch, sync comparator, clamp |
| Protection | D1, D7 | SMF5.0A, TPD2EUSB30 | C151296, C97502 | battery TVS, USB ESD |

Passives are 0201 and up, no 01005.

## Connectors and I/O

| Connector | Ref | Part | Function |
|---|---|---|---|
| Battery | J2 (+), J3 (-) | plated solder pads | 1S input |
| Motors | J4, J7, J10, J13 | Molex PicoBlade 53047-0310 land, header DNP | M1-M4 phases; solder the wires or fit the header |
| USB | J31 | JST SH 1.0 mm 4-pin, BM04B-SRSS-TB | USB full speed to the RP2354A |
| Camera | J32 | JST SUR 0.8 mm 3-pin, SM03B-SURS-TF | video in, GND, +5V_CAM; in parallel with pads J23-J25 |
| VTX antenna | J1 | U.FL | 5.8 GHz |
| RX antenna | AE1 | wire monopole in a plated D0.5 hole | ELRS 2.4 GHz |
| Wi-Fi antenna | AE2 | 2450AT07A0100001T chip antenna | ELRS Wi-Fi updates |
| Solder pads | J20-J22, J33 | pads | LED strip and buzzer: LED, 5V, BZ-, GND |
| Solder pads | J23-J25 | pads | camera: CAM, 5V, GND |
| Solder pads | J26-J29 | pads | DJI O4 Lite: VHD, GND, TX1, RX1 (Betaflight UART0) |
| Button | SW1 | SKUBAAE010 | shared boot and bind: RP2354A BOOTSEL and ESP32 boot through D8 |
| Test points | TP1-TP8, TP9, TP12, TP13 | mask-open filled vias | EFM8 C2D/C2CK, RP2354A boot (FCB), SWD CLK/DIO |

### GPIO map (RP2354A, U10)

| GPIO | Function |
|---|---|
| 0, 2, 3 | SPI0 MISO, SCK, MOSI (blackbox) |
| 1 | Blackbox CS |
| 4, 6, 18, 20 | Motors M1, M2, M3, M4 (DShot) |
| 5 | LED strip pad, driven directly |
| 7, 13, 15 | Gyro INT, CLKIN, CS |
| 8, 9 | UART1 TX, RX: CRSF to the ESP32 |
| 10, 24 | Status LED0, LED1 |
| 11, 12, 14 | SPI1 MOSI, MISO, SCK (gyro) |
| 16, 17 | UART0 TX, RX: pads TX1, RX1 |
| 19 | HD_EN (PINIO) |
| 21, 22, 23 | OSD W, EN, SYNC (consecutive, as the PIO OSD requires) |
| 25 | Beeper FET Q26 |
| 26, 27 | ADC: current sense, VBAT divider |
| Free | 28, 29 |

The ESP32 pin map (radio SPI, VTX SPI, PA control, boot) and the firmware
target are in [research/PINMAP.md](research/PINMAP.md); the pad set is in
[research/IO-SET.md](research/IO-SET.md).

## Layout rules

- In1 and In4 are solid GND planes. In2 carries no analog or RF; In3 carries no
  analog, RF, gate, gyro or VTX control nets. The DRU enforces this.
- HDI 1+4+1: laser microvias L1-L2 and L5-L6 only, buried vias L2-L5 staggered
  from them, no stacking. Vias sit inside same-net pads; a free-standing via
  takes board space and is avoided.
- RF nets carry no vias and keep 50 ohm width on the outer layers. Inside the
  `RF_VTX_STRIP` rule area (0.5 mm around the 5.8 GHz chain) only GND vias are
  allowed, so In1 stays solid under the line; `RF_PAD_CUTOUT` cuts In1 out
  under the U.FL signal pad.
- AE1, the RX wire, leaves through a plated D0.5 hole. Inside the D2.0
  `RF_RX_HOLE` area pours are kept out on all layers and the only copper is the
  2.4 GHz feed on L1. AE2 has no all-layer keep-out but minimal copper around
  it, with parts on the opposite side.
- The 5 V boost hot loop closes on the component layer with a direct ground
  return: no via in the loop, unbroken GND under it, a small switch node, away
  from the gyro, the crystals and the antennas.
- Each AGM210MAP keeps its 22 uF hot-loop cap directly across its supply pair.
  The battery path from the pads through R1 to each ESC cell stays short and
  symmetric; R1's sense taps stay Kelvin, off In2 and In3.
- The motor plugs, the twelve half-bridges, the USB plug at the rear hole, the
  battery pads and the camera plug sit where the BetaFPV Matrix 1S 5IN1 II has
  them, so motor leads, battery lead and camera cable reach as they do on that
  board. Moving them breaks that fit.

## Firmware

- FC: [Betaflight](https://github.com/betaflight/betaflight) 2026.6.2 or later
  on a custom target, `BOARD_NAME = OPENAIO_WHOOP` (target text in
  research/PINMAP.md). First flash: hold SW1 while powering up, which starts the
  RP2354A in USB BOOTSEL, then copy the UF2 onto it.
- RX: [ExpressLRS](https://github.com/ExpressLRS/ExpressLRS) stock
  `Unified_ESP32_2400_RX` with the board's layout JSON, flashed through
  Betaflight serial passthrough. SW1 at power-up also latches the ESP32 into
  download mode, which recovers a broken ELRS image.
- ESC: stock [Bluejay](https://github.com/bird-sanctuary/bluejay), layout BB51
  "A". The EFM8s are programmed over C2 before assembly; the C2 test points are
  the recovery path, and Betaflight 4-way passthrough updates them.

## Repo

| | |
|---|---|
| Status | See the `status-*` topic on the repo. Never written here. |
| Designed in | KiCad 10 |
| KiCad project | `hardware/OpenAIO-Whoop.kicad_pro` |
| Root schematic | `hardware/OpenAIO-Whoop.kicad_sch`; sub-sheets `power`, `esc_channel` (ESC1-ESC4), `rp2350a`, `imu`, `blackbox`, `osd`, `rx_esp32_sx1281`, `vtx`, `led`, `pads` |
| Board | `hardware/OpenAIO-Whoop.kicad_pcb`, 6 layers HDI 1+4+1, 1.0 mm (stackup `hardware/tools/stackup.json`); 26.4 mm body, three ear holes on 25.5 mm, chamfered front corner without a hole. Placed with in-pad vias, planes and rule areas; tracks not routed |
| Local library | `hardware/lib.kicad_sym`, `hardware/lib.pretty/`, `hardware/lib.3dshapes/`, nickname `lib` |
| Shared library | `hardware/KiCad-Library/`, submodule of [OpenDrone-hw/KiCad-Library](https://github.com/OpenDrone-hw/KiCad-Library), nickname `OpenDrone`; 3D models and exact component datasheets resolve through the project text variable `OPENDRONE_LIB` |
| Design rules | `hardware/OpenAIO-Whoop.kicad_dru`, canonical block plus HDI via rules, inner-layer net rules, RF areas and the motor-land and PTH rules |
| Fab config | `hardware/fabrication-toolkit-options.json` |
| Board setup | 6 layers, 0.09 mm clearance and track; through via 0.35 on 0.20; laser microvia 0.25 on 0.10; buried via 0.35 on 0.20 |
| Design notes | `research/`: DESIGN-SPEC.md, DECISIONS.md, PINMAP.md, IO-SET.md |
| License | CERN-OHL-S-2.0 |

A repository holds design files only. Sourcing (suppliers, prices, quotes, RFQs, contacts) is handled by Incutec and never lives in OpenDrone repositories.

## Parts and datasheets

- **Per-repository part index:** the root schematic and its listed sub-sheets
  are authoritative for what this board fits. Export the netlist with the
  command below when a script-readable board index is needed; do not maintain
  a second hand-written BOM.
- **Symbols and footprints:** every footprint is in `hardware/lib.pretty/`.
  Symbols come from `hardware/lib.kicad_sym` or KiCad 10's stock `Device`,
  `power`, `Connector` and `Mechanical` libraries.
- **Proven shared parts:**
  `hardware/KiCad-Library/PARTS-USED.md` is the catalogue index. Its `Boards`
  column identifies every repository using each LCSC part.
- **Exact datasheets:**
  `hardware/KiCad-Library/datasheet/manifest.json` maps shared symbols to the
  committed PDFs and their SHA-256 hashes. The PDFs live in
  `hardware/KiCad-Library/datasheet/`, and symbol links resolve there through
  `OPENDRONE_LIB`.
- **Local-only parts:** inspect `hardware/lib.kicad_sym`,
  `hardware/lib.pretty/`, and `hardware/lib.3dshapes/`, then verify supplier
  fields in the board schematic. Do not duplicate a shared part or datasheet.

## Environment

```sh
# clone with the pinned shared library (symbols, footprints, 3D models)
git clone --recurse-submodules https://github.com/OpenDrone-hw/OpenAIO-Whoop
git submodule update --init   # existing clone, hardware/KiCad-Library empty

# schematic and board checks
kicad-cli sch erc hardware/OpenAIO-Whoop.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones hardware/OpenAIO-Whoop.kicad_pcb

# netlist, for scripted analysis
kicad-cli sch export netlist --format kicadsexpr -o /tmp/OpenAIO-Whoop.net hardware/OpenAIO-Whoop.kicad_sch

# board setup report and lineup conventions
$KPY hardware/tools/check_board_setup.py [--spec <spec.json>]
$KPY hardware/tools/check_conventions.py --stage planned
```

3D models of catalogue parts (every passive, the RP2354A, the SX1281 and
more) resolve through `OPENDRONE_LIB` = `${KIPRJMOD}/KiCad-Library` only with
the submodule initialised; without it the 3D view shows bare pads.

On macOS `kicad-cli` is at
`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`, and `pcbnew` imports
only under KiCad's bundled Python, `KPY`:
`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`.
On Linux, `bash hardware/tools/setup-agent-env.sh` installs KiCad 10 with
`kicad-cli` on `PATH`; `KPY` is `/usr/bin/python3.12`, and
`/opt/kicad-agent-venv/bin/python` is the same with kicad-skip added.
Reusable scripts for renders, STEP export, and packaging art come from Incutec
hardware tooling. The OpenDrone release standard is
[RELEASES.md](https://github.com/OpenDrone-hw/.github/blob/main/RELEASES.md).
Board-specific scripts live in `hardware/tools/`.

## Rules

Identical in every OpenDrone board repo. Do not edit here; edit the template.

- **Never text-edit** `.kicad_sch`, `.kicad_pcb` or `.kicad_dru`. Use KiCad, or
  kicad-skip / the pcbnew API for scripted changes. `.kicad_pro` is JSON and may
  be edited directly for metadata.
- **Metadata yes, connections no.** An agent may write BOM and documentation
  fields (MPN, Manufacturer, LCSC, Cost, Datasheet, text variables). An agent
  may not change nets, wiring, routing, placement, footprint assignment, or any
  value that changes the circuit.
- **Close KiCad before any write to a KiCad file.** KiCad caches library tables
  at process start and overwrites files on save.
- **Reuse before you draw.** Check the `OpenDrone` library and its
  `PARTS-USED.md` first. If the part is there we have already sourced,
  footprinted and shipped it, and its symbol links to the exact committed
  datasheet: place it from `OpenDrone`. Draw a new part into `lib` only when
  the catalogue has nothing that fits, imported with
  `easyeda2kicad` from its LCSC number. Pulling a newer catalogue is a
  deliberate, reviewed commit: `git submodule update --remote
  hardware/KiCad-Library`, then DRC.
- **One person holds a board layout at a time.** KiCad files do not merge. Say
  on Discord that you are taking it. See [CONTRIBUTING.md](CONTRIBUTING.md).
- **Run ERC and DRC before every pull request.** Existing approved findings
  may remain; a new type or increased count must be reviewed before merge.
  Commands are in Environment above.

## By task

Board-specific paths are in Environment above. `KPY` is KiCad's bundled
Python named there.

- Check the design: run the ERC and DRC commands in Environment before every pull request.
- Add a part: place it from the `OpenDrone` library if `hardware/KiCad-Library/PARTS-USED.md` lists it; otherwise import it into `lib` with `$KPY <hardware-tooling>/hardware/kicad/import_part.py` (read `--help` first), KiCad closed.
- Render the board for the README: `$KPY <hardware-tooling>/hardware/kicad/render_board.py hardware/OpenAIO-Whoop.kicad_pcb --outdir images`, KiCad closed, submodule initialised.
- Analyse the netlist: export it with the netlist command in Environment, then read it with a script; never hand-write a second BOM.
- Check lineup conventions: run `check_conventions.py` from Environment; the stage is `planned` until the repo topic says otherwise.
- Update the shared library: `git submodule update --remote hardware/KiCad-Library`, run DRC, commit as its own reviewed change.
