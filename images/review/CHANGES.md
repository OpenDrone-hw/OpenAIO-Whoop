# Review pack: RX RF corner fix (rxfix, 2026-10-10)

This pass compares the board against checkpoint `p2v3/fp_checkpoints/10_pre_rxfix` (the compaction-pass board). The
compaction pass's own pack is backed up in that checkpoint under `review_compact/`.

**Why:** a critique BLOCKER (rf-firmware) found that the SX1281 RFIO → FL1 → AE1 chain had no route that passes DRC. FL1
OUT had no legal exit, FL1 IN faced away from pin 22, and the TCXO X3 sat 0.35 mm over the pin 22 escape.

**Moved (6 parts, all on top):**

| Part | Move | Reason |
|---|---|---|
| FL1 | to (103.55, 120.0), rot 180 | IN now faces U18 pin 22 and OUT faces AE1 |
| X3 | to (106.3, 119.65) | TCXO off the pin 22 escape, right of the RF line |
| C85 | 2.3 mm | X3 VDD decoupling |
| C84 | to (102.65, 123.25) | XTA DC-block cap at U18 pin 4 |
| R7 | to (102.9, 122.2) | +5V_USB divider; no closer legal site |
| D4 | to (115.3, 123.6), rear edge | RX LED moved to free the X3 site |

**Rules:**
- RF_RX_ANT is now net-aware: the rule area keeps out pours, pads and parts, and the DRU rule
  `RF_RX_ANT: only the RF feed on L1` lets only /RX/RF_RX_ANT run on F.Cu.
- RF_RX_FEED moves to In1, along FL1 OUT → AE1, with GND vias only.
- `setup_board.py` is updated to match, and the RX selftest cases pass.

**Trial route (scratch board, not on the repo board):**
- RF_RFIO 2.2 mm and RF_RX_ANT 2.4 mm on L1 at 0.105 mm, with no via: 0 DRC findings.
- XTA: pin 4 → C84 on L1.
- TCXO_OUT: a via at (102.375, 123.6), then In4 for 6.3 mm, then a via beside X3 pad 3. This gives 1 warning: the
  "In4 solid plane" rule, a reviewed exception.

**Checks:**
- DRC: 0 errors, 14 warnings, 62 unconnected (all unchanged).
- check_spacing: 0 / 0 / 0.
- check_rules: parsed.
- check_conventions: 37 ok, 0 FAIL.
- Empty patches: F 0, B 0.
