# OpenAIO-Whoop

An all-in-one board for 1S and 2S whoops, 65 to 85 mm class: flight
controller, four brushless ESC channels and an ExpressLRS receiver on a
25.5 x 25.5 mm board. Digital video only, no onboard analog VTX or OSD. The
whoop-class sibling of [OpenAIO](https://github.com/OpenDrone-hw/OpenAIO),
which is the 6S toothpick board on the same mounting pattern.

[![Status](https://img.shields.io/endpoint?url=https://opendrone.be/api/status/OpenAIO-Whoop.json)](https://github.com/OpenDrone-hw/.github/blob/main/CONTRIBUTING.md#the-life-of-a-project)
[![Discord](https://img.shields.io/badge/Discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/v3sWmTcx3R)

Nobody holds this board yet: claim it on Discord.

## Why

Whoops are where an AIO is not a convenience but the only option: there is no
room for a stack and no weight budget for connectors. The class has also moved
to digital video, which removes the analog VTX and OSD that used to dominate
the board area, so it is worth designing for digital from the start rather than
carrying analog circuitry nobody uses. Almost nothing from OpenAIO survives the
voltage difference: a 1S/2S whoop runs a direct-drive P+N power stage rather
than a driven half-bridge per channel, and the power tree starts from a cell
rather than from a pack. Treat them as two boards that happen to be the same
size.

## Specifications

Targets. The board does not exist yet.

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

## Constraints

- 25.5 x 25.5 mm mounting pattern, shared with OpenAIO.
- FC section reuses the [OpenFC-Lite-Mini](https://github.com/OpenDrone-hw/OpenFC-Lite-Mini) RP2354A design; Betaflight target derived from its target.
- ESC runs Bluejay on EFM8BB51 with GPIO direct drive: no gate-driver IC, so the power stage is a complementary P+N pair per phase.
- Receiver is serial ELRS 2.4 GHz, reusing the [OpenRX](https://github.com/OpenDrone-hw/OpenRX) Lite design.
- Digital video only: SH1.0 6-pin HD-VTX port, no analog VTX or OSD hardware.
- JLCPCB assembly from LCSC parts, basic parts preferred.

## Prior art

- [OpenFC-Lite-Mini](https://github.com/OpenDrone-hw/OpenFC-Lite-Mini) and [OpenRX](https://github.com/OpenDrone-hw/OpenRX): the FC and RX stages this board reuses.
- The class reference is the BetaFPV Matrix 1S 5IN1 II.
- An earlier stitched design was reset in August 2026 (see the git history before #9); reference for the thinking, not a design to continue from.

## Open questions

- **Power stage.** Direct drive at 1S means very low voltage and high current. Which FETs, and what does that do to the copper?
- **1S and 2S in one design**, or two variants? A boost for the electronics on 1S is a real cost, and 2S needs a level shift per phase to turn the P-FET off.
- **Motor connection.** Solder pads or connectors, given the class usually means replaceable motors.
- **Antenna.** Where it goes on a board this size with a duct around it.
- **Does it need an onboard receiver at all**, or is a serial ELRS module pad set better for a class where people swap protocols?

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
