# Review pack: routing loop 1, promotion 2 (2026-10-10 06:05)

Compared against `p2v3/route/ckpt/loop1_repo_before_promote2.kicad_pcb` (= promotion 1 of this loop). The promotion 1
pack (v3-order copper + schematic sync vs repo ca603f3) is saved in `p2v3/route/ckpt/review_promote1/`.

## What changed
- **No footprint moved** (`diff-top.png`, `diff-bottom.png` all grey; check_spacing --d70 0 / 0 / 0).
- **Copper added** by a new edge router (`p2v3/route/loop1/tools/erouter.py`): for each unconnected edge from the DRC,
  grid A* from the copper of item A to item B on F.Cu / B.Cu and **In2.Cu (L3) for the nets the repo DRU allows there**
  (D85; no Analog/RF/Gate/gyro/VTX-SPI/Kelvin/crystal nets), vias checked by the prep exact checker (DRU clearances,
  holes, silk, rule areas, edge). Two passes (0.10 mm signal / 0.15 mm rail tracks with 0.03 mm margin, then
  0.09 / 0.12 mm with 0.012 mm margin). RF nets excluded. New items in DRC errors removed (cleanup), dangling trimmed,
  short centring segments added where a new track ended inside a via, 3 new vias re-centred onto track ends.
- Geometric diff: +35 vias; tracks F.Cu +11.0 mm, B.Cu +24.4 mm, **In2.Cu +87.0 mm** (`copper-diff-inner.png`);
  top/bottom in `copper-diff-top.png`, `copper-diff-bottom.png` (mirrored).

## Numbers (kicad-cli DRC, refill, schematic parity, repo project rules)
| | promotion 1 | promotion 2 |
|---|---|---|
| DRC errors | 0 | **0** |
| unconnected | 306 | **262** |
| parity | 0 | **0** |
| vias | 320 | 355 |
| track | 406 mm (In2 37) | 531 mm (In2 125) |
| warnings | 16 | 20 (+4 track_not_centered_on_via: router tracks ending off-centre in an existing via) |

## Why the rest does not route (analysis, loop 1)
- U10 (RP2354A, F) has 44 unconnected pin ends. Via-in-pin is DRU-legal on its 0.4 mm pitch only at exactly the
  0.20 hole-to-pad limit, and B.Cu under U10 is fully populated (U9 EFM8, U16, U21, C66, 0201s): 37 of 41 pins have no
  legal through via; F.Cu escape is closed by parts 0.2 mm off the pad ends and the +3V3 ring around the QFN.
- BEMF divider blocks (R13-R39) sit on a 0.2 mm body grid with GND vias between them: no 0.09 mm track fits between
  0201 pads under the 0.13 mm SMD-pad-to-track rule (needs >= 0.35 mm pad gap); 21 of 31 phase edges fail.
- 24 GND/+BATT pads have no legal plane via within 1.6-2.5 mm (s6_taps), mostly 0201 decoupling and EFM8 VDD pins.
