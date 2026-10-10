# Review pack: routing loop 1, promotion 3 (2026-10-10 06:30)

Compared against `p2v3/route/ckpt/loop1_repo_before_promote3.kicad_pcb` (= promotion 2). Earlier packs of this loop:
`p2v3/route/ckpt/review_promote1/` (v3-order copper + schematic sync vs repo ca603f3) and `review_promote2/`
(edge router, In2). Loop 1 overall: unconnected 391 (repo ca603f3) -> **259**, DRC errors 1 -> **0**, parity 39 -> **0**.

## What changed in this step
- **4 resistors moved on B.Cu** (no copper was attached to them; `diff-bottom.png`): R58 (VIDEO_OUT / VT_MOD_N1)
  1.45 mm, rot 90 -> 180; R59 (VT_MOD_N1 / GND) 1.24 mm, rot 90 -> -90; R64 (RTC_VT / RTC_LF) 1.10 mm, rot 90 -> 180;
  R85 (LED0 / D5_K) 0.05 mm. All stay inside their block (VTX, LED). Tool `p2v3/route/loop1/tools/relocate.py`: nearest
  site within 1.6 mm (4 rotations) where both pads can escape (0.09 mm track to 0.6 mm, exact clearances) with
  courtyards not overlapping and pads clear of copper, silk, edge and rule areas. check_spacing --d70 0 / 0 / 0.
- **Freerouting finish pass** (149 remaining nets, 2 x 300 s, repo layer rules, all copper locked): +63 tracks, 5 DRC
  errors repaired (2 +5V tracks narrowed 0.20 -> 0.17 mm at the U6 EP via holes, 1 +BATT_IN 0.50 -> 0.477 mm, 2
  +BATT_IN In2 segments removed) -> net +1 edge.
- **Edge router** pass on the result: +2 edges. Copper diff: +1 via, F.Cu +13.9 mm, B.Cu +7.4 mm, In2.Cu +3.1 mm
  (`copper-diff-*.png`).

## Numbers (kicad-cli DRC, refill, schematic parity, repo project rules)
| | repo ca603f3 | promotion 1 | promotion 2 | **promotion 3** |
|---|---|---|---|---|
| DRC errors | 1 | 0 | 0 | **0** |
| unconnected | 391 | 306 | 262 | **259** |
| parity | 39 | 0 | 0 | **0** |
| vias | 298 | 320 | 355 | **356** |
| track | 80 mm | 406 mm | 531 mm | **556 mm** (F 238 / In2 128 / B 190) |
| warnings | 14 | 16 | 20 | 20 |

## Where the 259 are (`unrouted-map.png`: black signal, orange rails, green GND, purple phase; red X = boxed pad)
- Endpoints per sheet (promotion 2): VTX 87 (B 59 / F 28), RP2350A 75, ESC1-4 ~113, RX 39, POWER 34, OSD 24, PADS 20.
- 146 of 349 unconnected SMD pads are **boxed**: no 0.09 mm escape to 0.6 mm on their own layer and no legal via.
  Blockers within 0.35 mm of those pads: other parts' pads 307, tracks 257, own-footprint pads 235, signal vias 65,
  pours 63, GND vias 54.
- Experiments that did NOT help (so they are not the limiters): SMD-pad-to-track 0.13 -> 0.10 (+2 edges); RF_VTX_CHAIN
  "GND vias only" limited to 0.6 mm around the RF copper (+0); exact-limit via-in-pin on 16 ICs (20 vias placed, +1);
  router margin 0.03 -> 0.012 mm and 0.09 mm tracks (+7).
- U10 RP2354A: B.Cu under its pin ring is populated (U9 EFM8, U16, U21, C66, 0201s), so 37 of 41 unconnected pins have
  no legal through via; F.Cu escape is closed by parts 0.2 mm off the pad ends.

## Next (placement, not routing)
1. Clear a 0.8-1.0 mm band on B.Cu under the U10 pin ring (move U9 / U21 / U16 edge parts out) for staggered
   via-in-pin (0.4 mm pitch takes vias only at the exact 0.20 hole-to-pad limit, alternate ends of the pad).
2. EFM8 (U6-U9) and BEMF divider grids: one 0.35-0.40 mm channel per QFN side and per divider row (rotate dividers so
   pads face the escape direction); today the 0.2 mm body grid leaves no track between 0201 pads.
3. VTX block: re-place the R/C network around U22 / U19 with escape directions (most boxed pads in the map).
4. D85 DRU (In2 for Gate / gyro / SPI1 / PA_EN) is not in the repo rules yet: 27 edges are on nets barred from In2.
