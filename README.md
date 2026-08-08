# OpenAIO-Whoop

Open-source whoop-class AIO board with a 25.5 x 25.5 mm mounting pattern, part of the incutec OpenDrone line. One board combines an RP2354A flight controller (LSM6DSV16X IMU, Betaflight custom target), four Bluejay (EFM8BB51) brushless ESC channels on an XR8G02M direct-drive P+N power stage, a serial ExpressLRS 2.4 GHz receiver (ESP32-C3 + SX1281) and a W25Q128JVPIQ 16 MB SPI NOR blackbox flash. Digital video only: SH1.0 6-pin HD-VTX port, no onboard analog VTX or OSD. Target class is 1S/2S whoops (65-85 mm). Designed in KiCad 10.

Full specification, part-level detail (LCSC numbers, power stage rationale, second sources) and current design state: [hardware/docs/DESIGN.md](hardware/docs/DESIGN.md).

## Status

**Prototype pending**, early design, 2026-08-05.
Forked from OpenAIO and being adapted for whoop class. FC and RX schematic sheets are imported from sibling designs and ESC parts are selected, but the ESC channel sheet and the board layout still carry the inherited donor design. Sheet-by-sheet state: [Design state](hardware/docs/DESIGN.md#design-state).

## Repository layout

| Path | Contents |
|---|---|
| `hardware/` | KiCad 10 project: top sheet, sub-sheets, project-local libraries |
| `hardware/docs/` | Design documentation ([DESIGN.md](hardware/docs/DESIGN.md), [ESC_DESIGN.md](hardware/docs/ESC_DESIGN.md), [MARKET-RESEARCH-2026-06.md](hardware/docs/MARKET-RESEARCH-2026-06.md)) |
| `libs/KiCad-Library` | Shared Incutec symbol/footprint/3D library (git submodule) |

## Design entry points

- Top schematic: `hardware/OpenAIO-Whoop.kicad_sch`
- FC sheets: `hardware/schematics/fc/` (rp2350a, power, imu, blackbox, pads; from OpenFC-Lite-Mini rev 2, no OSD sheet)
- ESC sheet: `hardware/schematics/esc/esc_channel.kicad_sch`, instantiated 4 times
- RX sheet: `hardware/schematics/elrs/elrs.kicad_sch` (OpenRX-Lite)
- Board: `hardware/OpenAIO-Whoop.kicad_pcb`

Project-local libraries: `hardware/lib.*` (FC), `hardware/whoop.*` (Bluejay ESC parts), `hardware/components.kicad_sym` with `hardware/4in1ESC.pretty` (ESC donor parts), `hardware/OpenRX-Shared.*` (RX). The project lib tables also reference the shared `Incutec` library from the `libs/KiCad-Library` submodule, used for new parts; KiCad standard libraries are the only other external references.

## Build and export

```
git clone --recursive https://github.com/OpenDrone-hw/OpenAIO-Whoop.git
```

Open `hardware/OpenAIO-Whoop.kicad_pro` in KiCad 10. Production exports (gerbers, BOM, CPL) are generated with the [KiCad Fabrication Toolkit](https://github.com/bennymeg/Fabrication-Toolkit) plugin into `hardware/production/` (gitignored). Headless checks use `kicad-cli`:

```
kicad-cli sch erc --exit-code-violations hardware/OpenAIO-Whoop.kicad_sch
kicad-cli pcb drc --exit-code-violations hardware/OpenAIO-Whoop.kicad_pcb
```

## Manufacturing

No production exports exist yet and no hardware has been fabricated.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Hardware licensed under [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt). See [LICENSE](LICENSE). Referenced firmware projects (Betaflight, Bluejay, ExpressLRS) remain under their own upstream licenses.
