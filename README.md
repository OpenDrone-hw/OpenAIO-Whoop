# OpenAIO-Whoop

**Planned.** No design exists yet. This page is the specification: what we want
built and why. If you want to design it, say so on
[Discord](https://discord.gg/v3sWmTcx3R).

An all-in-one board for 1S and 2S whoops, 65 to 85 mm class: flight controller,
four brushless ESC channels and an ExpressLRS receiver on a 25.5 x 25.5 mm
board. Digital video only, no onboard analog VTX or OSD.

## Why

Whoops are where an AIO is not a convenience but the only option: there is no
room for a stack and no weight budget for connectors. The class has also moved
to digital video, which removes the analog VTX and OSD that used to dominate
the board area, so it is worth designing for digital from the start rather than
carrying analog circuitry nobody uses.

## Requirements

| | |
|---|---|
| Target class | 1S and 2S whoops, 65 to 85 mm |
| Mounting | 25.5 x 25.5 mm |
| Flight controller | RP2354A class, Betaflight target |
| ESC | 4 channels, direct-drive P+N power stage, Bluejay |
| Receiver | ExpressLRS 2.4 GHz, serial |
| Video | Digital only, SH1.0 6-pin HD-VTX port |
| Blackbox | SPI NOR flash |
| Assembly | JLCPCB, LCSC basic parts preferred |

## How it differs from OpenAIO

[OpenAIO](https://github.com/OpenDrone-hw/OpenAIO) is the 6S toothpick version
and shares the mounting pattern, but almost nothing else survives the voltage
difference. A 1S/2S whoop runs a direct-drive P+N power stage rather than the
6-MOSFET half-bridge per channel the 6S boards use, and the power tree starts
from a cell rather than from a pack. Treat them as two boards that happen to be
the same size.

## Prior art in the line

- [OpenFC-Lite-Mini](https://github.com/OpenDrone-hw/OpenFC-Lite-Mini): the RP2354A flight controller
- [OpenRX](https://github.com/OpenDrone-hw/OpenRX): the ELRS receiver

## Open questions

- **Power stage.** Direct drive at 1S means very low voltage and high current.
  Which FETs, and what does that do to the copper?
- **1S and 2S in one design**, or two variants? A boost for the electronics on
  1S is a real cost.
- **Motor connection.** Solder pads or connectors, given the class usually
  means replaceable motors.
- **Antenna.** Where it goes on a board this size with a duct around it.
- **Does it need an onboard receiver at all**, or is a serial ELRS module pad
  set better for a class where people swap protocols?

## Research

Component and market work done so far is in [research/](research/). It is
reference, not decisions. `ESC_DESIGN.md` in particular is a real comparison of
whoop power-stage options and is worth reading before proposing one.

## Contributing

Issues and pull requests are welcome on any repo. KiCad files cannot be merged,
so say what you intend to change before you do, on
[Discord](https://discord.gg/v3sWmTcx3R).

How everything works: [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Hardware licensed under [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt),
see [LICENSE](LICENSE).
