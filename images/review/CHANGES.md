# Review pack: routing loop 2, promotion 1 (2026-10-10 07:03, pack written 07:10)

Compared against `p2v3/route/ckpt/loop2_repo_before_promote1.kicad_pcb` (= loop 1 promotion 3, md5 5f6df5eb).
The loop 1 promotion 3 pack is archived in `p2v3/route/ckpt/review_loop1_promote3/`.

## What changed
- **14 GND stitching vias removed** next to boxed signal pads (`p2v3/route/loop2/tools/gndprune.py`: a GND via is
  removed only when the GND net keeps the same connectivity without it; red dots in `copper-diff-top.png`).
- **Edge router pass** (`erouter.py`, F/B/In2, exact checker): +2 vias, In2 +7.1 mm, B +0.5 mm -> +1 edge.
- **3 dead +BATT_IN In2 stub segments removed** (In2 -3.0 mm); this also removed one DRC warning.
- No footprint moved (`diff-top.png` / `diff-bottom.png` show no change).

## Numbers (kicad-cli DRC, refill, schematic parity, repo project rules)
| | loop 1 promotion 3 | **loop 2 promotion 1** |
|---|---|---|
| DRC errors | 0 | **0** |
| unconnected | 259 | **258** |
| parity | 0 | **0** |
| vias | 356 | **344** |
| warnings | 20 | **19** (8 solder_mask_bridge, 6 track_not_centered_on_via, 2 lib_footprint_mismatch, 1 copper_sliver, 1 silk_overlap, 1 isolated_copper) |

`unrouted-map.png` is still the loop 1 map (the unrouted set changed by one edge). copper-top.png / copper-bottom.png
are stale files from the prep pack.
