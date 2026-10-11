# ESP32 Wi-Fi antenna layout

AE2 is the ESP32-PICO-V3 Wi-Fi antenna. The SX1281 receiver uses the separate
AE1 wire through FL1. ExpressLRS documents Wi-Fi for receiver configuration and
firmware updates; this antenna layout does not replace the RC antenna.
[ExpressLRS receiver updates](https://www.expresslrs.org/quick-start/receivers/updating/).

## Component and manufacturer reference

Johanson **2450AT07A0100001T**, legacy 2450AT07A0100, is a 1.0 x 0.5 mm ceramic
antenna. Pins 1/4 are feed and pins 2/3 are ground. Revision 4.1 specifies
2400-2480 MHz and illustrates a 5 x 3 mm ground-clearance window at the centre
of a board edge. Its performance figures apply to the manufacturer's evaluation
board. The datasheet recommends provision for a shunt-series-shunt matching
network, whose values depend on the assembled PCB.
[Johanson datasheet, pages 1-3](https://www.johansontechnology.com/docs/4417/Antenna-2450AT07A0100001T.pdf).

## Compact prototype layout

The selected density trial keeps this antenna and reduces its reserved window.
It deliberately departs from the manufacturer's reference configuration.

| Item | Native PCB geometry, mm |
| --- | --- |
| AE2 | F.Cu, centre 111.75 / 124.00, rotation 270 degrees |
| Complete trial window | x 110.85-112.40, y 123.45-124.80 |
| F.Cu void | x 110.85-111.90, y 123.45-124.80 |
| F.Cu ground-terminal strip | x 111.90-112.40, y 123.45-124.80 |
| Inner/back void | Complete trial window, all five remaining copper layers |
| R88 series link | F.Cu, 111.10 / 122.80, rotation 90 degrees |
| C133 source-side shunt | F.Cu, 110.55 / 122.52, rotation 270 degrees, DNP |
| C132 antenna-side shunt | F.Cu, 111.85 / 123.10, rotation 0 degrees, DNP |

The reserved area decreases from 15 to **2.0925 mm2**, reclaiming 12.9075 mm2
per layer before accounting for the matching lands and feed. This is a reduction
in reserved routing area, not a reduction in the board's outline. The main feed,
including the series-link pad span and paired antenna-terminal connection,
measures **7.402 mm**, compared with 10.774 mm in the larger-window route proof.
No motor connector, ESC half-bridge or boost component moves for this change.

Use the saved native rule areas `WIFI_FULL_WINDOW`, `WIFI_FRONT_VOID`,
`WIFI_FRONT_GROUND` and `WIFI_INNER_BACK_VOID`. Both `/RX/RF_WIFI` and
`/RX/RF_WIFI_ANT` are permitted feed nets. Other copper, vias and component pads
remain excluded from the small window. Keep each shunt's ground connection
local. The antenna ground row reaches ground microvias outside the window,
then the continuous ground plane through staggered buried vias.

The feed's adjacent reference is In1.Cu. The nominal outer RF geometry is
0.105 mm width with a 0.15 mm coplanar ground gap, calculated for the recorded
stackup. Preserve that reference and inspect the actual filled coplanar copper.
The ESP fine-pitch launch has one-sided coplanar ground because of adjacent pads,
so the complete route is not a uniform 50 ohm coplanar line. In1 covers the full
trace width and matching pads outside the intentional antenna aperture. A local
route or clearance check does not measure impedance or radiation.

## Matching population and measurement

| Reference | Prototype population | Connection |
| --- | --- | --- |
| R88 | Yageo RC0201JR-070RL, 0 ohm, 0201 | Pin 2: ESP feed; pin 1: antenna feed |
| C133 | DNP, 0201 tuning land | ESP side of R88 to GND |
| C132 | DNP, 0201 tuning land | Antenna side of R88 to GND |

The series link's identity and 0.6 x 0.3 mm body are specified in the
[Yageo component sheet](https://www.yageogroup.com/component-documentation/download/specsheet/RC0201JR-070RL).
The DNP capacitors intentionally have no purchasing MPN or assigned capacitance.
Choose fitted C0G parts only from antenna measurements; do not populate arbitrary
values copied from another board.

Use the series position for a calibrated antenna measurement with the battery,
canopy and final leads installed. Then verify the ExpressLRS web interface and
complete firmware uploads at practical bench distances, including 1 m and 3 m.
Repeat with the VTX operating and the intended supply arrangement. Matching
alone does not demonstrate radiated efficiency or usable Wi-Fi performance.
A short off-board wire connected at the antenna-side series land is a prototype
fallback if the compact ceramic layout cannot meet the intended use. Its length,
position and strain relief require their own measurement and assembly check.

No range, efficiency or RF compliance result is established by this layout.
Earlier numerical range estimates and claims about hidden copper in competitor
photographs are not evidence for this prototype and are removed from this
reference. Sharing the SX1281 antenna would require separate isolation and
firmware work and is not part of the fitted circuit.
