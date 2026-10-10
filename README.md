# OpenAIO-Whoop

An all-in-one board for 1S whoops, 65 to 85 mm class: flight controller,
four brushless ESC channels, an ExpressLRS receiver and an onboard analog VTX
on the 25.5 x 25.5 mm whoop mounting pattern. The 1S sibling of
[OpenAIO](https://github.com/OpenDrone-hw/OpenAIO), which covers 2S to 6S on
the same mounting pattern.

<p>
<img src="images/front.png" width="400" alt="OpenAIO-Whoop top" />
<img src="images/back.png" width="400" alt="OpenAIO-Whoop bottom" />
</p>

[![Status](https://img.shields.io/endpoint?url=https://opendrone.be/api/status/OpenAIO-Whoop.json)](https://github.com/OpenDrone-hw/.github/blob/main/CONTRIBUTING.md#the-life-of-a-project)
[![Discord](https://img.shields.io/badge/Discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/v3sWmTcx3R)

## Why

Whoops are where an AIO is not a convenience but the only option: there is no
room for a stack and no weight budget for connectors. 2S and up is OpenAIO's
range, so what is left for a second board is 1S, where the power tree starts
from a single cell and everything below +5V has to be boosted rather than
bucked. That is the whole design problem, and it is worth solving once.

Analog is the reason this board is separate rather than a variant. A 1S whoop
is the last class still flying analog in volume, and an onboard VTX is what
makes the board worth building instead of pointing people at a digital AIO
with an HD port.

## Specifications

From the design files: the schematic and an initial placement. Not routed or
manufactured yet.

| | |
|---|---|
| Target class | 1S whoops, 65 to 85 mm |
| Mounting | 25.5 x 25.5 mm, three ear holes |
| Board | 26.4 mm body, 6-layer HDI 1+4+1, 1.0 mm |
| Input | 1S LiPo (3.0-4.35 V), solder pads |
| Firmware | Betaflight, Bluejay, ExpressLRS |
| MCU | RP2354A |
| IMU | BMI270 |
| Blackbox | 16 MB SPI NOR flash |
| ESC | 4 channels, EFM8BB51 + AGM210MAP half-bridges, DShot |
| Receiver | Onboard ExpressLRS 2.4 GHz, ESP32-PICO-V3 + SX1281, wire antenna |
| Video | Onboard analog VTX, RTC6705 + SE5004L PA, U.FL |
| OSD | Analog, PIO framebuffer |
| Digital video | DJI O4 Lite pads, switched 5 V and UART |
| Motors | Molex PicoBlade 1.25 mm 3-pin lands, plug or solder |
| USB | JST SH 1.0 mm 4-pin |
| Camera | JST SUR 0.8 mm 3-pin plug and solder pads |

Technical write-up, part list and layout constraints: [AGENTS.md](AGENTS.md).

## Constraints

- 25.5 x 25.5 mm mounting pattern, shared with OpenAIO.
- 1S only. 2S and above is OpenAIO, and covering both here would mean a wider
  front end for a range another board already serves.
- Motor plugs, USB, battery pads and camera plug sit where the BetaFPV Matrix
  1S 5IN1 II has them: motor plugs paired at the two side holes, USB at the
  rear hole.
- FC section reuses the [OpenFC-Lite-Mini](https://github.com/OpenDrone-hw/OpenFC-Lite-Mini) RP2354A design; Betaflight target derived from its target.
- Receiver reuses the [OpenRX-Lite-UFL](https://github.com/OpenDrone-hw/OpenRX-Lite-UFL)
  SX1281 design on an ESP32-PICO-V3 and talks CRSF to the FC; the same ESP32
  controls the VTX.
- Passives 0201 and up, no 01005, so the board stays hand-reworkable.
- Assembly house chosen per release. Fab-ready manufacturing files are kept in
  a private Incutec production repository and are not published.

## Prior art

- [OpenFC-Lite-Mini](https://github.com/OpenDrone-hw/OpenFC-Lite-Mini) and [OpenRX-Lite-UFL](https://github.com/OpenDrone-hw/OpenRX-Lite-UFL): the FC and RX stages this board reuses.
- [OpenAIO](https://github.com/OpenDrone-hw/OpenAIO): the 2-6S board, and the source of the ESC and power sheets that do not survive the drop to one cell.
- [OpenVTX](https://github.com/OpenDrone-hw/OpenVTX): the line's RTC6705 analog VTX.
- The class reference is the BetaFPV Matrix 1S 5IN1 II.
- An earlier stitched design was reset in August 2026 (see the git history before #9); reference for the thinking, not a design to continue from.

## In the line

What pairs with what, and what is available:
[opendrone.be](https://opendrone.be).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). KiCad files cannot be merged, so say
what you intend to change before you do, on
[Discord](https://discord.gg/v3sWmTcx3R).

Clone with the shared library and open `hardware/OpenAIO-Whoop.kicad_pro` in
KiCad 10:

```sh
git clone --recursive https://github.com/OpenDrone-hw/OpenAIO-Whoop
git submodule update --init      # after a plain git clone
```

Every footprint and 3D model comes from the project library
(`hardware/lib.pretty`, `lib.3dshapes`) or from the pinned
`hardware/KiCad-Library` submodule. Symbols come from `hardware/lib.kicad_sym`,
the submodule, or KiCad 10's stock `Device`, `power`, `Connector` and
`Mechanical` libraries, which a default KiCad install provides (lineup rule A8). Catalogue 3D models resolve through the
project text variable `OPENDRONE_LIB` (`${KIPRJMOD}/KiCad-Library`), so
without the submodule the 3D view shows bare pads.

A repository holds design files only. Sourcing (suppliers, prices, quotes, RFQs, contacts) is handled by Incutec and never lives in OpenDrone repositories.

## License

Hardware licensed under [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt),
see [LICENSE](LICENSE).
