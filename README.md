# OpenAIO-Whoop

An all-in-one board for 1S whoops, 65 to 85 mm class: flight controller, four
brushless ESC channels, an ExpressLRS receiver and an onboard analog VTX on a
25.5 x 25.5 mm board. The 1S sibling of
[OpenAIO](https://github.com/OpenDrone-hw/OpenAIO), which covers 2S to 6S on
the same mounting pattern.

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

## VTX dependency

RTC6705 has no LCSC listing, so an onboard analog VTX cannot be assembled at
JLCPCB today. This board waits on that part becoming orderable, or on a
sourceable equivalent. Nothing else about it is hard, and nothing has been
drawn.

## Specifications

Targets. The board does not exist yet.

| | |
|---|---|
| Target class | 1S whoops, 65 to 85 mm |
| Mounting | 25.5 x 25.5 mm |
| Input | 1S LiPo |
| Flight controller | RP2354A class, Betaflight target |
| ESC | 4 channels |
| Receiver | ExpressLRS 2.4 GHz, serial |
| Video | Onboard analog VTX and OSD |
| Blackbox | SPI NOR flash |
| Assembly | JLCPCB, LCSC basic parts preferred |

## Constraints

- 25.5 x 25.5 mm mounting pattern, shared with OpenAIO.
- 1S only. 2S and above is OpenAIO, and covering both here would mean a wider
  front end for a range another board already serves.
- FC section reuses the [OpenFC-Lite-Mini](https://github.com/OpenDrone-hw/OpenFC-Lite-Mini) RP2354A design; Betaflight target derived from its target.
- Receiver is serial ELRS 2.4 GHz, reusing the [OpenRX Lite](https://github.com/OpenDrone-hw/OpenRX-Lite) design.
- JLCPCB assembly from LCSC parts, basic parts preferred.

## Prior art

- [OpenFC-Lite-Mini](https://github.com/OpenDrone-hw/OpenFC-Lite-Mini) and [OpenRX Lite](https://github.com/OpenDrone-hw/OpenRX-Lite): the FC and RX stages this board reuses.
- [OpenAIO](https://github.com/OpenDrone-hw/OpenAIO): the 2-6S board, and the source of the ESC and power sheets that do not survive the drop to one cell.
- The class reference is the BetaFPV Matrix 1S 5IN1 II.
- An earlier stitched design was reset in August 2026 (see the git history before #9); reference for the thinking, not a design to continue from.

## Design questions

Resolve these only as part of user-requested design work:

- **VTX part.** Is there a sourceable RTC6705 equivalent on LCSC, or a
  different route to 25 mW to 200 mW on the 5.8 GHz band that JLCPCB can place?
- **Power stage.** At 1S the pack is 3.0 to 4.35 V. Driven half-bridge needs a
  boosted gate rail; direct-drive P+N needs no driver but costs dead time,
  which AM32's `USE_INVERTED_HIGH` F421 targets run at 120-140 against 22-75
  for driver-based targets. Which one, and what does it do to the copper?
- **Electronics rail.** Everything from +5V down has to come from a boost or
  buck-boost off one cell, and it has to hold up with the cell sagging under
  full throttle. That is the part existing 1S-2S AIOs get wrong.
- **Motor connection.** Solder pads or connectors, given the class usually
  means replaceable motors.
- **Antenna.** Where the RX antenna and the VTX antenna go on a board this
  size with a duct around it, without desensitising the receiver.

## In the line

What pairs with what, and what is available:
[opendrone.be](https://opendrone.be).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). KiCad files cannot be merged, so say
what you intend to change before you do, on
[Discord](https://discord.gg/v3sWmTcx3R).

## License

Hardware licensed under [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt),
see [LICENSE](LICENSE).
