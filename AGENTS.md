# OpenAIO-Whoop

1S whoop-class all-in-one, 25.5 mm three-ear mounting pattern, 26.4 mm body: RP2354A flight controller running Betaflight, four EFM8BB51 ESC channels with twelve AGM210MAP half-bridges, an ExpressLRS 2.4 GHz receiver (ESP32-PICO-V3 and SX1281) and an analog VTX (RTC6705 and SE5004L) with a PIO framebuffer OSD. Every rail is derived from one cell; it is not a 2S board.

## Architecture

Sheets (root `OpenAIO-Whoop.kicad_sch`): `power`, four instances of `esc_channel` (ESC1 to ESC4), `rp2350a` (the RP2354A), `imu`, `blackbox`, `osd`, `rx_esp32_sx1281` (RX), `vtx`, `led`, `pads`.

- **Power:** battery pad J2 feeds the 0.5 mohm shunt R2 (INA186A3, gain 100, 50 mV/A, Kelvin taps SHUNT_SENSE_P/N) and then `+BATT`. `+BATT` feeds the ESCs, the SE5004L and the TPS61022 boost. The boost output `+5V_BST` feeds the VHD pad and the HD VTX plug directly and `+5V` through D10. USB VBUS joins `+5V` through D9.
- **ESC:** each EFM8BB51 (U6 to U9, supplied from `+BATT`) drives its three AGM210MAP half-bridges directly from `A/B/C_PWM` and `A/B/C_COM`; there is no gate driver. Phase sense uses resistors from the phase nodes to the MCU comparator inputs. The DShot line `MOTORn` runs from P0.5 through 1k to the RP2354A (GPIO4, 6, 18, 20 for motors 1 to 4). C2 debug lands are test points TP1 to TP8.
- **FC:** RP2354A with 2 MB in-package flash, 12 MHz oscillator X1 on XIN (XOUT open), internal regulator with L2 to `+1.1V`. BMI270 on SPI1 with its own 1.8 V rail (U12). Blackbox flash U13 (Puya PY25Q128HA, 16 MB) on SPI0. Battery voltage is divided by R45/R46 (1:2) to ADC1, shunt output goes through R47 to ADC0.
- **Receiver:** SX1281 (U18, LDO mode, 52 MHz TCXO X3) to FL1 to the wire antenna AE1. ESP32-PICO-V3 (U16) runs ExpressLRS and talks CRSF to the RP2354A on UART1 (GPIO8/9). Chip antenna AE2 for Wi-Fi mode feeds U16 pin 2 directly.
- **VTX:** the same ESP32 programs the RTC6705 (U19) over a separate SPI through 1k series resistors, enables the PA reference regulator U22 with `PA_EN`, sets RF drive with a PWM through R71/Q27 and reads the PA detector (`PA_DET`). Chain: U19 to C110 to U20 (SE5004L) to FL2 to U.FL J1. HD_EN (RP2354A GPIO19) enables the analog VTX supply U21.
- **OSD:** camera video (`VIDEO_IN`) passes through U14, which switches between video and the OSD level divider; U15 extracts sync to GPIO23. OSD writes use GPIO21, switch enable GPIO22.
- **Boot:** one button SW1 serves both MCUs through D8: `FC_BOOT` (to `QSPI_SS` through R44) and `RX_BOOT` (ESP32 IO0).

## Power

```
J2 (+) --> R2 0.5 mR shunt --> +BATT  (J3 = GND)
  +BATT --> ESC1-4: U6-U9 VDD, Q29-Q40 half-bridges
  +BATT --> U20 SE5004L VCC
  +BATT --> U2 TPS61022 + L1 0.68 uH --> +5V_BST --> J26 VHD pad, J35 pin 1 (HD VTX)
                                           +5V_BST --> D10 --> +5V
  VBUS (J31) --> D9 --> +5V
  +5V --> J21 pad, D4 WS2812
      +5V --> FB1 --> +5V_CAM --> J24 pad, J32 pin 3
      +5V --> U4 TLV75733 --> +3.3V (D11: +3.3V anode, +5V cathode)
      +5V --> U21 LP5912-3.3 (EN = HD_EN) --> +3.3V_VTX --> U19 RTC6705
                                                  +3.3V_VTX --> U22 TPS7A20285 (EN = PA_EN) --> PA_VREF --> U20 VREF
  +3.3V --> U10 IOVDD, U11, U13, U14, U15, U16, U18, X1, X3, LEDs D5/D6
      +3.3V --> U12 TPS7A2018 --> +1.8V_GYRO --> U11 VDD
      +3.3V --> U10 VREG_VIN --> L2 3.3 uH --> +1.1V (DVDD)
```

## Key parts

| Function | Ref | Part | LCSC | Note |
|---|---|---|---|---|
| MCU | U10 | RP2354A | C41378174 | 2 MB in-package flash |
| MCU clock | X1 | 12 MHz oscillator | C669076 | on XIN |
| IMU | U11 | BMI270 | C2836813 | SPI1 |
| IMU LDO | U12 | TPS7A2018 | C36996449 | 1.8 V |
| Blackbox | U13 | PY25Q128HA-DFH-IR | C53467986 | 16 MB, SPI0 |
| Boost | U2 | TPS61022 | C915088 | L1 0.68 uH C5832369 |
| 3.3 V LDO | U4 | TLV75733 | C2868428 | from +5V |
| Shunt | R2 | 0.5 mohm 2 W | C346511 | 4-pad Kelvin |
| Current amp | U1 | INA186A3 | C2058245 | gain 100 |
| ESC MCU x4 | U6 to U9 | EFM8BB51F16I | C3232998 | Bluejay layout A |
| Half-bridge x12 | Q29 to Q40 | AGM210MAP | C7431169 | three per ESC channel |
| RX MCU | U16 | ESP32-PICO-V3 | C967022 | ExpressLRS and VTX control |
| RX radio | U18 | SX1281 | C2151551 | X3 52 MHz TCXO C22434896 |
| RX filter | FL1 | 2450FM07D0034T | C2651081 | to AE1 |
| Wi-Fi antenna | AE2 | 2450AT07A0100001T | C17531353 | B.Cu |
| Video synth | U19 | RTC6705 | C913074 | X4 8 MHz C400090 |
| VTX PA | U20 | SE5004L | C210263 | on +BATT |
| VTX filter | FL2 | RFBPF1608060K98Q1C | C2442150 | to J1 |
| VTX LDOs | U21, U22 | LP5912-3.3, TPS7A20285 | C524780, C3748388 | analog rail, PA reference |
| OSD switch / sync | U14, U15 | SN74LVC1G3157, TLV7031 | C2673087, C2876045 | |
| Supply diodes | D9 to D11 | MS2A40LDF | C7380000 | |
| Status LED | D4 | XL-1010RGBC-2812B | C5349953 | RX status |

## Connectors and I/O

| Connector | Ref | Part | Function |
|---|---|---|---|
| Battery | J2, J3 | solder pads D1.7 mm PTH | J2 +, J3 GND |
| Motors M1 to M4 | J4, J7, J10, J13 | PicoBlade 1.25 mm 3-pin lands (header 53047-0310 optional) | pins 1/2/3 = phase C/B/A of ESC1 to ESC4 |
| USB | J31 | BM04B-SRSS-TB (C160390) on B.Cu | 1 GND, 2 D-, 3 D+, 4 VBUS; D7 TPD2EUSB30 |
| Camera plug | J32 | SM03B-SURS-TF (C265338) | 1 VIDEO_IN, 2 GND, 3 +5V_CAM |
| HD VTX plug | J35 | SM04B-SRSS-TB (C160404) on B.Cu | 1 +5V_BST, 2 GND, 3 UART0_TX, 4 UART0_RX |
| VTX antenna | J1 | U.FL (C88374) | 5.8 GHz out |
| RX antenna | AE1 | plated D0.5 wire hole | 2.4 GHz wire |
| Pads | J20 LED, J21 +5V, J22 BZ-, J23 CAM video, J24 +5V_CAM, J26 VHD (+5V_BST), J28 TX0, J29 RX0, J25/J27/J33 GND | 1.0 x 1.2 mm solder pads | J28 and J29 are UART0 TX and RX (GPIO16/17) |
| Test points | TP1 to TP8 | EFM8 C2D/C2CK per ESC | TP12 SWCLK (CLK), TP13 SWDIO (DIO) |

GPIO29 (`SBUS`) has no pad. Full RP2354A and ESP32 pin tables: [research/PINMAP.md](research/PINMAP.md).

## Layout rules

- **Stackup:** 8 layers, 0.997 mm, 35 um copper on all layers, 1080 prepreg 0.077 mm L1/L2, L2/L3, L6/L7, L7/L8, cores 0.127 mm L3/L4 and L5/L6, 2116 prepreg 0.125 mm L4/L5.
- **Planes:** In1 and In6 GND only, no tracks. In3 `+3.3V`, In4 `+BATT`, In5 `+5V` and `+5V_BST`. In2 and In5 carry digital signals, ESC gate and phase-sense escapes. Parts and RF sit on F.Cu and B.Cu.
- **Vias (HDI 1+6+1):** laser microvias F.Cu to In1 and In6 to B.Cu only (0.25 land, 0.10 drill), buried vias In1 to In6 (0.33 land, 0.15 drill), no through vias, no mechanical blind vias. A microvia may stack on a same-net buried via. Hole to hole 0.30 between different nets, 0.20 same net. `hdi_via_pass.py` rebuilds unbuildable vias after routing.
- **Board setup:** clearance and track 0.09 mm, annular ring 0.075 mm, copper to edge 0.20 mm. Parts keep 0.30 mm from the edge except edge solder pads.
- **RF:** class `RF` has no vias and 50 ohm width 0.100 to 0.110 mm with 0.15 mm gap on the outer layers, over unbroken GND on In1 or In6. Each chain stays on one face. Intent from the DRU (area rules, see the next item): only the `/RX/RF_RX_ANT` feed on F.Cu enters the D2.0 area around the AE1 hole, SPI0 and `FLASH_CS` stay 3 mm from it (blackbox harmonics fall in the ELRS band), and AE2 has a feed-only void on every layer.
- **Rule areas:** the DRU rules for `RF_RX_FEED`, `RF_VTX_STRIP`, `RF_RX_HOLE`, `RF_RX_ROOT`, `WIFI_VOID_V1`, `WIFI_FAR_F`, `WIFI_GND_LINK`, `SHUNT_CORRIDOR`, `BOOST_GND_L5`, `MOUNT_*` and `PART_EDGE_BAND` match by area name. The board file holds no rule areas, so those rules do not fire.
- **Current paths:** boost hot loop (U2, L1, its caps) on F.Cu with a direct ground return and no via in the loop. Each AGM210MAP keeps its 22 uF hot-loop caps directly across its supply pair. `+5V_BST` and `+5V` tracks at least 0.30 mm or pours. R2 sense taps stay Kelvin on the outer layers and off In2/In5.
- **USB:** `USB_D_P/N` skew at most 5 mm per segment, pair gap 0.10 to 0.20 mm.
- **Mechanical:** three D3.55 ear cut-outs on a 25.5 mm square pattern (5.2 mm grommet flange keep-out is an area rule, inactive). No tall connector within 1.0 mm of J31 (active).

## Firmware

- **Flight controller:** Betaflight target `OPENAIO_WHOOP` in `firmware/betaflight/`, built against Betaflight 2026.6.2 (pinned commit in its README). Not registered upstream. The build needs `OPENAIO_GYRO_ALIGN` and `OPENAIO_BOARD_YAW`. First flash over USB BOOTSEL: hold SW1 while connecting J31.
- **Receiver:** ExpressLRS pin binding `firmware/expresslrs/board-layout.json` for the ESP32-PICO-V3. It is a binding, not an installable target: power calibration arrays are absent. ESP32 boot is IO0 on SW1; its UART0 connects only to RP2354A GPIO8/9.
- **ESC:** Bluejay on the EFM8BB51, layout A, over C2 on TP1 to TP8. No ESC firmware is stored here.

## Repo

| | |
|---|---|
| Maintainer | OpenDrone-hw |
| Status | See the `status-*` topic on the repo. Never written here. |
| Designed in | KiCad 10 |
| KiCad project | `hardware/OpenAIO-Whoop.kicad_pro` |
| Root schematic | `hardware/OpenAIO-Whoop.kicad_sch` plus `power`, `esc_channel` (x4), `rp2350a`, `imu`, `blackbox`, `osd`, `rx_esp32_sx1281`, `vtx`, `led`, `pads` |
| Board | `hardware/OpenAIO-Whoop.kicad_pcb`, 8 layers, HDI 1+6+1, 0.997 mm |
| Local library | `hardware/lib.kicad_sym`, `hardware/lib.pretty/`, `hardware/lib.3dshapes/`, nickname `lib` |
| Shared library | `hardware/KiCad-Library/`, submodule of [OpenDrone-hw/KiCad-Library](https://github.com/OpenDrone-hw/KiCad-Library), nickname `OpenDrone`; 3D models and exact component datasheets resolve through the project text variable `OPENDRONE_LIB` |
| Design rules | `hardware/OpenAIO-Whoop.kicad_dru`, canonical block plus HDI via, layer-use, RF, antenna, USB and plated-hole rules |
| Fab config | `hardware/fabrication-toolkit-options.json` |
| Board setup | 8 layers, 0.09 mm clearance and track, microvia 0.25 on 0.10 drill, buried via 0.33 on 0.15 drill, annular 0.075 mm |
| License | CERN-OHL-S-2.0 |

A repository holds design files only. Sourcing (suppliers, prices, quotes, RFQs, contacts) is handled by Incutec and never lives in OpenDrone repositories.

## Parts and datasheets

- **Per-repository part index:** the root schematic and its listed sub-sheets
  are authoritative for what this board fits. Export the netlist with the
  command below when a script-readable board index is needed; do not maintain
  a second hand-written BOM.
- **Proven shared parts:**
  `hardware/KiCad-Library/PARTS-USED.md` is the catalogue index. Its `Boards`
  column identifies every repository using each LCSC part; filter that column
  for `OpenAIO-Whoop` to get this repository's proven shared-part view.
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
# clone with the pinned shared library, or fetch it into an existing clone
git clone --recurse-submodules https://github.com/OpenDrone-hw/OpenAIO-Whoop
git submodule update --init

# schematic and board checks
kicad-cli sch erc hardware/OpenAIO-Whoop.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones hardware/OpenAIO-Whoop.kicad_pcb

# netlist, for scripted analysis
kicad-cli sch export netlist --format kicadsexpr -o /tmp/OpenAIO-Whoop.net hardware/OpenAIO-Whoop.kicad_sch
```

On macOS `kicad-cli` is at
`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`, and `pcbnew` imports
only under KiCad's bundled Python. Reusable scripts for renders, STEP export,
and packaging art come from Incutec hardware tooling. The OpenDrone release
standard is
[RELEASES.md](https://github.com/OpenDrone-hw/.github/blob/main/RELEASES.md).
Board-specific scripts live in `hardware/tools/`; run the Python ones with `KPY`, KiCad's bundled Python
(`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`), and KiCad closed for any that write:

- Read-only checks: `check_rules.py`, `check_rule_behavior.py`, `check_board_setup.py`, `check_spacing.py`, `check_conventions.py --stage planned`, `loop_resistance.py`, `check_netlist.py` (compares the schematic with `bom_plan.json`, `sch_contract.json` and `research/PINMAP.md`).
- Board edits after routing: `hdi_via_pass.py` (via spans), `gnd_stitch.py`, `pad_vias.py`, `track_widen.py`, `track_to_pour.py`, `inner_router.py`, `via_declutter.py`. DRC after each.
- Stackup: `stackup.json` applied with `apply_stackup.py`.
- Readbacks: `export_bom_plan.py` and `export_interfaces.py` write `hardware/bom_plan.json` and `hardware/sch_contract.json`. They are exports, not a BOM source.
- Generators that predate the owner's edits: `sch_build.py`, `sch_root.py`, `sch_integrate.py`, `setup_board.py`, `floorplan.py` (inputs `floorplan.json`, `board_spec.json`), `sync_pcb.py`, `pcb_build.py`. They write schematic, board or rule files. Do not run them to overwrite the current files.

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

## Revisions

| Rev | Date | Change |
|---|---|---|
| none | 2026-10-16 | No release tag. Current state: complete schematic, routed 8-layer HDI board. |

## By task

Board-specific paths are in Environment above. `KPY` is KiCad's bundled
Python named there.

- Check the design: run the ERC and DRC commands in Environment before every pull request.
- Add a part: place it from the `OpenDrone` library if `hardware/KiCad-Library/PARTS-USED.md` lists it; otherwise import it into `lib` with `$KPY <hardware-tooling>/hardware/kicad/import_part.py` (read `--help` first), KiCad closed.
- Render the board for the README: `$KPY <hardware-tooling>/hardware/kicad/render_board.py hardware/OpenAIO-Whoop.kicad_pcb --outdir images`, KiCad closed, submodule initialised.
- Analyse the netlist: export it with the netlist command in Environment, then read it with a script; never hand-write a second BOM.
- Check lineup conventions: `$KPY hardware/tools/check_conventions.py --stage planned`.
- Update the shared library: `git submodule update --remote hardware/KiCad-Library`, run DRC, commit as its own reviewed change.
