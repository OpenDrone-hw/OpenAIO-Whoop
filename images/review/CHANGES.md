# Floorplan v3 compaction pass (D66), 2026-10-10

Diff against checkpoint `p2v3/fp_checkpoints/09_pre_compact` (`diff-top.png`, `diff-bottom.png`, `changes.txt`).

- **Moved 3 footprints:**
  - C23, the hot-loop cap of Q30, moved from 3.86 mm to 0.1 mm from the cell's pin 1/3 midpoint.
  - C20, the hot-loop cap of Q29, moved from 2.19 mm to 0.82 mm.
  - R87 moved into the empty patch at the rear.
- **Reverted:** C35, C15 and R32. The placer had let C35 overlap R1 and R8, and C15 and R32 then filled its old site; check_spacing caught both.
- **Added on User.3, not copper:**
  - 20 reserved through-via sites: power landings at the cells, GND vias for U2, U11 and 5 others, the edge and RF fence, and stitching.
  - 5 reserved power and GND copper landings, over far-side cell pads where a via cannot go.
- **Empty patches over 1.0 mm²:**
  - top: 9 patches, 40.1 mm² before; 0 after
  - bottom: 5 patches, 12.2 mm² before; 0 after
  - Empty maps: `images/floorplan-empty-top.png` and `images/floorplan-empty-bottom.png`.
- **Checks:** DRC 0 errors (14 warnings, unchanged); 62 unconnected, all on temporary /FLOORPLAN/ nets; check_spacing 0; check_rules parses; check_conventions 0 FAIL.
