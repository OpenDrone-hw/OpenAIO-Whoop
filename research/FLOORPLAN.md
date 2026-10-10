# OpenAIO-Whoop floorplan v3 (P2, 2026-10-10)

The v3 board is `hardware/OpenAIO-Whoop.kicad_pcb`, with the block regions in `hardware/floorplan.json` and the renders in
`images/floorplan-top.png` and `images/floorplan-bottom.png`. The review pack is in `images/review/` (diff against the v2
checkpoint `p2v3/fp_checkpoints/08_pre_v3`). The v2 text of this file is in git history and in that checkpoint.

## Result

- **Placement:** every part in the integrated bom_plan is placed: 272 footprints (275 parts minus the H1-H3 Edge.Cuts
  holes), on the D73 outline (holes 25.5 mm, body 26.4 mm). Real footprints are used for the pads, connectors, antennas
  and holes.
- **DRC** (`kicad-cli pcb drc --refill-zones`): 0 errors. 62 unconnected, all on temporary `/FLOORPLAN/` land nets (the
  AGM drain pins 5-8 and the GND exposed-pad groups, which are not yet joined by copper).
  - 12 warnings are solder-mask bridges between pads on different temporary nets.
  - 2 warnings are library mismatches: R67, whose library footprint the integrator changed, and J33. Both are for the sync
    step.
- **check_spacing.py --min 0.20 --edge 0.20 --d70 --keepout-owner 'AE\*:RF_RX_\*' --keepout-owner 'AE\*:WIFI_ANT_KO':**
  0 violations, 0 edge hits, 0 keep-out hits. The median nearest gap is 0.200 mm.
  - Without `--d70`, 16 pairs are reported. Each is a filled, tented EP or test via under a far-side body, which D70 allows.
- **Other checks:**
  - check_rules: rules parsed.
  - check_conventions: 37 ok, 0 FAIL.
  - Concept hard checks (`check_d.py`): Wi-Fi W1/W2 pass (straight edge, not mirrored), the USB mating zone is clear, the
    CAM pads are in the plug mouth, the RX ring is clear, and the motor lands sit at the ear necks. The only flags are AE1
    inside its own RF areas, which the DRU AE\* exemption covers.
- **Area** (package / package + 0.1 mm halo, of 640.8 mm² usable per side):
  - top: 51.4 / 67.7 %
  - bottom: 54.1 / 80.6 %
  - free after the halo: 214 mm² on top, 135 mm² on the bottom
- **Stacked exposed pads (D70, X-ray ordered):** U10 over U9 (both GND), plus four pairs of AGM cells. 8 cells are on the
  bottom and 4 on the top.

## Compaction pass (D66, 2026-10-10)

This pass closed the empty patches the owner saw. It started from checkpoint `p2v3/fp_checkpoints/09_pre_compact`, and the
scripts are in `p2v3/compact/work/`: `emptymap3.py`, `compact3.py`, `viafill3.py`, `finalize.py`, `gndvia.py`,
`gndfix.py` and `fence.py`.

**How empty area is measured (`emptymap3.py`):**
- **Usable area:** the Edge.Cuts outline shrunk by 0.40 mm.
  - Minus every rule area that forbids footprints: mounting flanges, tabs, the edge band, the RX ring and exit.
  - Minus the deliberate mating and RF zones from d6: motor-plug bodies, the camera plug zone, the RF feed lines, the RX
    antenna and the Wi-Fi keep-out.
- **Occupied area:** part extent + 0.20 mm (the D70 body rule, no iron halo), U.FL + 0.70 mm (mating tool), silk boxes and
  reserved via sites.
- **Empty patch:** free area that can hold a 1.0 x 1.0 mm square, measured on a 0.025 mm raster.

| Side | Usable | Before: free / patches > 1 mm² | After part moves | After via sites | After landings (final) |
|---|---|---|---|---|---|
| top | 595.8 mm² | 90.4 mm² free / **40.1 mm² in 9** | 36.7 in 8 | 17.9 in 3 | 63.7 mm² free / **0 in 0** |
| bottom | 536.6 mm² | 63.3 mm² free / **12.2 mm² in 5** | 12.2 in 5 | 3.2 in 2 | 54.6 mm² free / **0 in 0** |

The empty maps are `images/floorplan-empty-top.png` and `-bottom.png`; the before maps are in `p2v3/renders/`. In the maps,
red is an empty patch, blue a reserved site or landing, dark green a part and light green the 0.2 mm halo.

**What closed the patches:**
1. **Pulling parts toward their anchor pins** (D70 kernel, 0.2 mm body rule). The v3 placement was already at a median
   nearest gap of 0.200 mm, so only 3 moves held:
   - C23, the Q30 hot-loop cap: 3.86 mm to 0.1 mm from the pin 1/3 midpoint.
   - C20, the Q29 hot-loop cap: 2.19 mm to 0.82 mm.
   - R87, moved into the rear patch.

   The pass also moved C35 onto R1/R8, which the placer missed and check_spacing caught. C35 was reverted, along with C15
   and R32, which had filled its old site. C23 was then nudged 0.1 mm off the "5V" silk label. Pin-matched decoupling is
   unchanged: 37 caps, 7 more than 1.5 mm from their pin, 0 more than 2.5 mm.
2. **Reserved through-via sites (`viafill3.py` + `gndfix.py`):** 20 sites, each a 0.35/0.20 filled, capped, tented via.
   - Each keeps 0.15 mm to every pad on F.Cu and B.Cu and is body-free on at least one side (D70).
   - Each stays outside via-forbidding areas and the RF syn zones.
   - They are marked as 0.35 mm circles on User.3 and listed in `floorplan.json` → `compaction_d66.reserved_vias`.
3. **Power copper landings:** 5 patches sit over far-side cell pads or the USB area, where no via fits. They are reserved
   as copper landings, marked as rectangles on User.3 and listed in `compaction_d66.power_copper_landings`.
   - top, over the bottom cells Q32 and Q30: 8.4 mm² each, an L1 +BATT/GND pour fed through via-in-pad in the cell pads
   - top, beside Q34: 1.3 mm²
   - bottom, rear left beside the USB: 1.7 + 1.7 mm², L6 GND pour

**Via counts after the pass:**

| Item | Before | After |
|---|---|---|
| Free through-via sites (0.5 mm grid, `viasites.py`) | 168 (114 open, 54 under far-side bodies) | 171 (115 open, 56 under far-side bodies) |
| Reserved sites (new) | 0 | 20 |
| Via-in-pad | 587 sites in 291 pads | 587 sites in 291 pads |

The 20 reserved sites by transition:

| Transition | Reserved sites |
|---|---|
| +BATT cell feed | 3 (Q34 ×2, Q36) |
| GND at the cells | 4 (Q29, Q32, Q33, Q40) + 3 cell GND vias (Q30, Q36, Q38) |
| IC GND vias | 4 (U2, U11, U1, U24) |
| LDO | 1 |
| GND edge fence | 1 |
| GND RF fence | 1 |
| GND stitching | 3 |

**Per cell (pin 3 / pin 1 / drain):**
- 10 via-in-pad sites in the drain and phase pads.
- Free open sites within 2.5 mm: 1-5. Q32, Q34, Q35 and Q40 each have 1.
- The 6 + 6 per-cell budget in §Power still does not close with open sites. It needs the hot-loop cap pad via-in-pad and
  the L6/L1 pours (unchanged open item).

**Via-in-pad on IC GND and power pins** (netlist from the integrated schematic):
- 22 ICs carry 123 GND and power pins. 17 of those pads can take a via (smaller side ≥ 0.45 mm), with 160 sites, plus 16
  exposed-pad vias already in the footprints.
- The 12 AGM cells have 16 sites each: 192.

**GND via site per IC** (via-in-pad, exposed-pad vias, a free or reserved via within 1.0 mm, or via-in-pad in a
neighbouring GND cap pad within 1.5 mm):
- 30 of the 34 ICs and cells have one.
- **Open:** U14 and U15 (X2SON-6/-4) need a short GND trace to a neighbour. The cells Q32 and Q35 have their hot-loop caps
  C26 and C32 still 2.2 mm or more away, so pin 1 has no site within reach until those caps are pulled in during routing.

**GND edge fence:**
- 60 via sites lie within 1.0 mm of the edge (57 before) on a 116.8 mm outline: mean pitch 1.95 mm, median gap 0.5 mm.
- Where cells and motor lands sit on the edge, the largest gap is 8.5 mm. The 0.8 mm fence pitch in §Power holds only
  along the open edge runs. Along the cells the fence moves to the L2/L5 stitching inside the cell row.

**Checks after the pass:**
- DRC: 0 errors, 14 warnings (unchanged); 62 unconnected, all on temporary /FLOORPLAN/ nets.
- check_spacing (`--d70`, AE\* owners): 0 / 0 / 0.
- check_rules: parses.
- check_conventions: 37 ok, 0 FAIL.
- Every D72 mating zone (USB_MATING, camera plug zone, motor-plug bodies) and every rule area was kept. No part entered
  them, because they are registered as obstacles.

## Method

1. **Checkpoint:** `08_pre_v3` holds the pcb, pro, dru, floorplan.json, bom_plan, setup_board.py, renders and this file.
2. **Board setup:** `setup_board.py` HOLE_HALF 12.75 (D73), re-applied to the repo board.
3. **Placement source:** concept D run **d6**, a placer re-run of `p2v3/concepts/matrix-clone`. It carries the d5 fixes:
   - Wi-Fi antenna orientation (no mirror)
   - keep-out at x 2.05..7.05, 2.1 mm from Q38 (D75)
   - two-sided pin decoupling
   - pad groups placed early
   - the O4 switch U5 and D2 on extra sites

   d6 placed all 266 then-current parts and passed every hard check. d1, the prompt's base, still had the mirrored
   antenna, the keep-out 0.5 mm from Q38 and 31 caps more than 2 mm from their anchors.
4. **Transplant:** d6's positions, sides and rotations were copied onto the repo board by reference
   (`p2v3/v3/work/transplant.py`). Footprints with an unchanged FPID were kept; changed or new ones were replaced or added,
   and the v2 extras were deleted.
5. **Conflict fixes** (`fixplace.py`: nearest legal site plus a pad-over-far-side-via check plus courtyard and keep-out
   checks):
   - J18 moved 0.6 mm and J24 1.4 mm, off EFM8 EP vias on the far side. J24 is still in the J32 mouth.
   - The LED pad column was reversed to BZ- 5V LED GND (the D64 order read the other way), so GND J33 covers U6's EP vias.
6. **Integrated-BOM sync** (`place_new.py`):
   - C17 and C30 deleted.
   - 8 hot-loop caps placed at their cells' lead side: C20, C21, C26, C27, C32, C33, C38, C39. Their distance to the pin
     1/3 midpoint is 0.8-3.6 mm, and the routing loop should pull them in.
7. **Context, silk, nets** (`context.py`, `silk3.py` + `silk_name.py`, `groupnets3.py`): see D75 below.

The scripts are in `p2v3/v3/work/`, and `STATE.md` is one level up.

## D75 board context and RF coexistence

- **Context:**
  - User.1 carries 46 block outlines with names. Each outline is the union of its parts' courtyards; top-side outlines are
    drawn at 0.05 width, bottom-side at 0.03, and names carry [F] or [B].
  - Every footprint has a `Function` field on its F.Fab or B.Fab layer, for example "U20 SE5004L VTX PA".
  - There are 13 component classes, one per schematic sheet: POWER, ESC1-ESC4, RP2354A, IMU, OSD, BLACKBOX, RX, VTX, LED and
    PADS. `setup_board.py` assigns them by reference in the .kicad_pro, from bom_plan, so the board file is never
    text-edited.
- **RF paths** (User.2, with clearances to the parts of each aggressor block):

| Path | PA + VTX chain | Boost 5 V | ESC cells + motor lands |
|---|---|---|---|
| RX wire: hole AE1 (-12.3, 7.5) to the left edge, then 8 mm out along the frame arm | 17.2 mm | 3.4 mm | 6.1 mm |
| Wi-Fi chip antenna field: keep-out x 2.05..7.05 carried 6 mm past the top-front edge | 0.7 mm (an RTC6705-side part at the keep-out's inner edge) | 10.1 mm | 2.1 mm (Q38) |
| U.FL coax: 4 mm stub, best of 8 directions, then up into the canopy | 0.05 mm (adjacent PA-chain passives; the coax is shielded) | 6.8 mm | 2.5 mm |

The RX antenna (left rear) and the 5.8 GHz chain (right front) sit on opposite sides of the board. The Wi-Fi antenna is on the
bottom at the top-front edge, 22 mm from the RX hole. Both are bench-only modes.

## Connectors and mating zones (D72 / D76)

- **USB J31:** vertical JST BM04B-SRSS-TB on the bottom at (-7.7, 8.6), rotated 135°, beside the rear mounting hole
  (6.5 mm). The plug faces up from the bottom side.
  - Rule area USB_MATING (body + 1.0 mm) with a DRU rule: no other TALL-class connector within 1.0 mm. Parts up to 1.25 mm
    tall sit far below the 4.25 mm wall, which is what the plug is gripped above.
  - The shroud corner reaches the RX ring and exit strip. That is plastic only; it is a scoped DRU exemption and the ring
    stays a copper keep-out.
- **Camera plug J32:** SM03B-SURS-TF on the top, facing inward (+x). The CAM pads J23 (CAM) and J24 (5V) are in its mouth;
  J25 (GND) sits beside it.
- **Motor lands J4/J7/J10/J13:** at the ear necks, the PicoBlade header (DNP) facing out over the ears.
  - The header envelopes of neighbouring lands meet at two ear corners. The bodies keep 0.2 mm, so this is a scoped DRU
    exemption for MOTOR_PAD pairs.
- **Battery J2/J3:** PTH pads on the left edge, 1.7 mm from the edge.

## Power (D72 power-routing plan, counted via budget)

**Stackup and layers:**
- NextPCB 6L 1.0 mm (`tools/stackup.json`): L1/L6 1 oz finished (0.49 mOhm/sq), L2-L5 0.5 oz (0.98 mOhm/sq). The 1.0 mm
  six-layer library build has 0.5 oz inner copper, so the plan assumes it.
- L1: signal, plus the battery corridor J2 to the shunt R1 (rule area SHUNT_CORRIDOR, now on L1 because R1 is on the top),
  plus local pours at the 4 top cells.
- L2 and L5: GND planes, densely stitched together.
- L4: +BATT plane.
- L6: signal plus +BATT and GND pours under the 8 bottom cells.

**Path:** J2 PTH (+BATT_IN; the 1.1 mm plated barrel joins all six layers) → L1 corridor → R1 (0.5 mOhm Kelvin) → +BATT on
the L4 plane, in parallel with the L1 and L6 pours → each AGM pin 3 (P-source). The return runs from each pin 1 (N-source)
into L2, L5 and the L6 GND pour, then to J3 (GND PTH).

**Via assumption:**
- 0.35/0.20 Type VII via with 20 µm barrel plating: 0.0138 mm², 1.24 mOhm over the full length, 0.6 mOhm from L1 to L4.
- Current per via: 1.0 A continuous and 2.5 A for bursts up to 2 s. A short barrel is heat-sunk by two planes; the IPC-2152
  external-conductor equivalent is 1.3 A at +10 °C.
- Burst design case: 12 A per motor channel, 40 A battery total.

| Transition | Burst current | Vias at 2.5 A | Planned | Reserved sites (counted on the v3 board) |
|---|---|---|---|---|
| J2 / J3 PTH to the planes | 40 A | barrel ≈ 7 via-equivalents each | barrel + 8 stitching vias per pad | open sites beside the pads |
| R1 +BATT side to L4 | 40 A | 16 | 8 via-in-pad in the 1206 pads + 8 beside | via-in-pad + open sites; the L1 corridor carries the rest in parallel |
| L4 to the 4 top-side cells (pin 3) | 12 A each | 5 | 6 each = 24 | 1-5 free sites within 2.5 mm per cell + 1 via-in-pad per hot-loop cap pad + D70 vias under far-side bodies |
| 8 bottom-side cells (pin 3) | 12 A each | 0 (fed by the L6 pour from the plane stitching) | 2 each = 16 (plane tie) | as above |
| GND, 12 cells (pin 1) to L2/L5 | 12 A each | 5 | 6 each = 72 | as above; the cell-side GND pour to J3 carries part of it |
| Drains (phase) of far-side cells to the motor land | 12 A each | 5 | 6 each in the drain EPs (via-in-pad allowed, 10 sites per cell) | 10 via-in-pad sites per AGM |
| Boost U2/L1 hot loop | 3 A in / 1.8 A out | 2 / 1 | 4 VIN + 4 GND + 2 VOUT | via-in-pad in the cap and QFN pads (L1 has 6 sites) |
| LDOs U3/U4/U21/U22 | ≤ 0.5 A | 1 | 2 each | via-in-pad |
| EFM8 VDD and EP (4x) | < 0.05 A | 1 | 1 + the EP via field already in the footprint | footprint vias |
| Edge GND fence + RF fences (5.8 GHz chain, 2.4 GHz feed) | - | - | 0.8 mm pitch | open sites and GND pad via-in-pad |

**Totals:** 168 free through-via sites on a 0.5 mm grid (114 open, 54 under far-side bodies) and 587 via-in-pad sites in 291
pads. The plan needs about 190 power vias plus the fences.

**Gap:** the cell supply pins (single 0.35 x 0.65 leads) leave only 1-5 open sites within 2.5 mm of each cell. The budget
closes only with:
- the hot-loop cap pad via-in-pad sites,
- D70 vias under far-side bodies,
- the 8 bottom cells taking +BATT from the L6 pour rather than vias.

This is the first item for the routing loop (D74).

**Plane drop at the 40 A burst (estimate):**
- +BATT: L4 plus the pours, about 0.33 mOhm/sq effective over about 2 squares, ≈ 0.7 mOhm (28 mV).
- GND: L2 ‖ L5 ≈ 1.0 mOhm (40 mV).
- 6 cell vias in parallel ≈ 0.1 mOhm (1.2 mV at 12 A).
- Shunt: 20 mV.
- Total: about 90 mV from the battery pads to the farthest cell.

## Rule and tool changes (logged here; DECISIONS.md is not edited by this stage)

**`setup_board.py`:**
- HOLE_HALF 12.75 (D73).
- Rule-area positions follow the v3 parts: RX hole and feed, U.FL zone and pad cut, VTX chain, shunt corridor (now on L1),
  tabs at the ear tips.
- RX exit strip radius 1.4 (a D69 preference).
- New rule areas: WIFI_ANT_KO (copper keep-out on all layers: pads, vias, pours; DRU feed-only tracks; AE\* exemption) and
  USB_MATING.
- Halo rules for solder pads and tall parts at 0 mm (D69/D70; the body rule stays in check_spacing).
- Scoped exceptions:
  - D65 PicoBlade rings 0.35 apart. This is a NextPCB EQ item: their general value is 0.40, and the Matrix ships the same
    land.
  - D65 DNP header courtyards may meet.
  - D67 test vias keep the via hole spacing.
  - D76 J31 shroud corner at the RX ring.
- Component classes per sheet (D75).

**`check_spacing.py`:** additive, opt-in `--d70` (tented via pads are copper, not package extent) and `--keepout-owner`.

## Open items (for the routing loop and critique)

- **Silk not placed:**
  - pad labels BZ- (J22) and M4 (J13)
  - pin-1 dots for J32 and J1
  - the product name only fits at 0.8 mm ("OPENAIO WHOOP", bottom), not in 1.4 mm rows
  - REV1 is at 1.0 mm on the bottom
- **Hot-loop caps:** C26, C32, C33 and C38 still sit 2.2 mm or more from their cells' leads. The D66 pass moved C20
  to 0.82 mm and C23 to 0.1 mm. They need pulling in, or pin-side via-in-pad, before the Q32 and Q35 GND via sites close.
- **GND via sites:** U14 and U15 need a short GND trace to a neighbour (see §Compaction pass).
- **Placer kernel:** pfk/fpk `near()` accepted an overlapping site for C35 (R1/R8). Every compaction output must be
  re-checked with check_spacing, and offenders reverted, until the kernel is fixed.
- **RF via:** the 5.8 GHz path crosses sides (RTC6705 bottom, PA top), so PAOUT1 needs one RF via. The DRU rule "RF: no
  vias" needs a scoped exception with a GND via fence when routing starts.
- **Wi-Fi feed:** the ESP32-PICO LNA_IN to antenna feed is 13.5 mm Manhattan; 8 mm is the preference. It needs an inner-layer
  50 ohm feed.
- **Gyro and PA preferences:** 4.0 mm from the FETs and 3.2 mm from the PA. These are preferences under D69.
