# Review pack: routing loop 2, promotion 2 (2026-10-10 08:50)

Compared against `p2v3/route/ckpt/loop2_repo_before_promote2.kicad_pcb` (= loop 2 promotion 1, md5 8e30ed8e). The
promotion 1 pack is archived in `p2v3/route/ckpt/review_loop2_promote1/`. Nothing is committed.

## What changed (copper only; no footprint moved: `diff-top.png` / `diff-bottom.png` show no change)
- **11 GND stitching vias removed** (red dots in `copper-diff-top.png`). These are the GND vias that a soft-obstacle
  router (`p2v3/route/loop2/tools/blame.py`) found on the cheapest path of an unrouted edge. A via was removed only when
  the pcbnew unconnected count did not rise. Vias inside RF rule areas (+1 mm) and within 1.2 mm of FET, boost or
  inductor pads were not touched (D33 hot loops, D72 budgets).
- **The D85 inner-layer rules are in the repo DRU now** (applied at 07:57 outside this loop). The edge router now
  uses In2 for Gate, gyro bus, VTX SPI and digital PA control nets. Analog, RF, SHUNT_SENSE, PA_DET, PA_NTC and the
  crystal nets stay off In2.
- **Edge router passes** (`erouter.py`, exact clearance checker, F/B/In2). Pass windows were widened to 3 mm and up to
  5 vias were allowed. Result: +5 vias, F +8.3 mm, B +2.0 mm, In2 +20.9 mm (`copper-diff-*.png`).
- A router-made 0.12 mm +BATT_IN In2 sliver was deleted again. It counted as a connection, but it is not a real
  battery path. +BATT_IN is now excluded from the edge router.
- 3 router track ends were snapped onto the centres of existing vias.

## Numbers (kicad-cli DRC in the repo dir, refill, schematic parity, repo project rules incl. D85)
| | loop 2 promotion 1 | **loop 2 promotion 2** |
|---|---|---|
| DRC errors | 0 | **0** |
| unconnected | 258 | **251** |
| parity | 0 | **0** |
| vias | 344 | **338** |
| track | 556 mm | **591 mm** (F 246 / In2 153 / B 193) |
| warnings | 19 | **21** (+1 connection_width: a 0.02 mm +3V3 router stub at U10 pin 45; +1 track_not_centered_on_via) |
check_spacing --d70: 0 pairs below 0.20 mm, 0 parts within 0.20 mm of the edge. The 3 keepout overlaps are AE1 in its
own antenna areas, the same as before. Edge check: 0 new items outside Edge.Cuts.

## Where the 251 are (`unrouted-map.png`, F + In2 + B)
Unconnected pad ends per sheet: VTX 84, RP2350A 73, RX 38, ESC3 35, POWER 31, ESC4 27, ESC2 26, ESC1 25, OSD 24,
PADS 15, IMU 9, LED 6, BLACKBOX 3.

## Why most of the rest needs placement work (loop 2 analysis, tools in `p2v3/route/loop2/tools`)
- **Via sites are the scarce resource.** `viamap.py` / `viawhy2.py` find only about 9 mm2 of legal through-via sites
  for a generic signal net on the whole board. Stripping all signal copper only doubles that. The main blockers are
  pads on F (1629 grid points blocked by F pads alone) and B (911), GND vias (605), rule areas (530) and F silk (411).
- **The rest of the routing is blocked by placement.** `blame.py` routes each failing edge with movable items made
  passable at a penalty. Movable items are 2-pad passives, test vias, and other nets' tracks and vias.
  - 168 of 241 edges have a path through movable items only.
  - 54 edges are blocked by fixed items (IC, FET and connector pads, rule areas).
  - Only 18 edges are blocked by copper alone. Ripping those nets and routing them again gave no gain (258 -> 259).
  - Most paths are blocked by passives (top: L2 14, C52 12, C117/R16/R14/C108/R20/R25 9).
  - `relocate.py` (radius 1.6 mm, 4 rotations) found no legal site for 11 of the 14 passives that carry no copper.
  - The board has no room for local moves. The next step is a re-placement of the U10 ring, the EFM8 sides and the
    VTX R/C network with reserved escape channels and via sites.
- **D71 pin map (proposal, not applied).** U10 pin use is scrambled. The gyro on the right is fed from left and
  bottom pins, the flash on the bottom left from right pins, and M3/M4 on the left from right pins.
  - `pinopt.py` checks firmware-legal sets (PINMAP 4.4), the EXT-USER-PADS / I2C-USER / I2C-HD presets and the OSD
    triple. It cuts escape-aware length from 333 to about 201 (`p2v3/route/loop2/an/pinmap_A.json`).
  - A PCB-only trial routed only +2 to +3 more edges, so the schematic, PINMAP and Betaflight-config swap is deferred.
    Re-plan it together with the U10 re-placement.
