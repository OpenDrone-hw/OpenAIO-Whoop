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

### Floorplan v3 critique (2026-10-10, rxfix pass): BLOCKER fixed, MAJORs open

**BLOCKER, verified and FIXED: RX RF corner (rf-firmware).**

*The finding (it held on the board):* FL1 OUT had no exit that DRC accepts. F.Cu lay in RF_RX_ANT, and any via fell in
RF_RX_ANT or RF_RX_FEED. FL1 IN faced away from pin 22, and X3 pad 2 sat 0.35 mm over the pin 22 escape. The scripts are
in `p2v3/rxfix/work/` (`place5.py`, `areas.py`, `trial3.py`) and the checkpoint is `p2v3/fp_checkpoints/10_pre_rxfix`.

*What changed:*
- **FL1** moved to (103.55, 120.0), rot 180. IN (pin 1) faces U18 pin 22 and OUT (pin 3) faces AE1. It sits outside the
  ring, 0.2 mm above U18's courtyard.
- **X3** moved to (106.3, 119.65), above U18 to the right of the RF line. Its GND pad 1 faces the line and its OUT pad 3 is
  on the far side.
- **C85** (X3 VDD) moved to (104.6, 119.125).
- **C84** (XTA DC block) moved to (102.65, 123.25), at U18 pin 4.
- **R7** (+5V_USB / U3_PR1 divider) moved to (102.9, 122.2). It is the nearest legal site, but 7 mm from U3/R8.
- **D4** (RX LED) moved to (115.3, 123.6) at the rear edge. It shrinks the Q30 L1 power landing by about 1.9 mm².

*Rules (the net-aware antenna keep-out lesson; `setup_board.py` updated and its RX selftest cases pass):*
- RF_RX_ANT now keeps out pours, pads and parts only.
- A new DRU rule, `RF_RX_ANT: only the RF feed on L1`, uses `A.Type == 'Via' || A.NetName != '/RX/RF_RX_ANT' || A.Layer != 'F.Cu'`.
- RF_RX_FEED moves to In1 (L2 solid under the L1 feed) along FL1 OUT → AE1, with GND vias only.
- The "RF: no vias" comment now reads L1.

*Trial route, run on a scratch board with nets set on the pads:*
- RF_RFIO: pin 22 north 0.25 mm, then 45° to FL1.1. 2.2 mm.
- RF_RX_ANT: FL1.3 west and 45° into the AE1 pad. 2.4 mm.

Both are on L1 at 0.105 mm (50 ohm), with no via, 0.15 mm from every other pad. Neither gave a DRC finding.

XTA and TCXO_OUT:
- XTA runs from pin 4 to C84 on L1.
- TCXO_OUT runs C84 → via (102.375, 123.6) → In4, 6.3 mm → via (107.1, 119.45), which half-overlaps X3 pad 3 (filled
  and capped) → X3.
- It crosses under the RF line with L2 GND between them. The Analog class is barred from In2/In3. The trial gave 1
  warning ("In1 and In4 are solid GND planes"), which needs review at routing.
- The TCXO via keeps clear of the reserved RX GND fence via at (101.66, 122.91).

*Checks after the fix:*
- DRC: 0 errors, 14 warnings, 62 unconnected (all unchanged).
- check_spacing (`--d70`, AE\* owners): 0 / 0 / 0.
- check_rules: parsed.
- check_conventions: 37 ok, 0 FAIL.
- Empty patches: F 0, B 0 (F free 65.3 mm², B 54.6 mm²).

The renders are in `images/`, plus `p2v3/renders/corner_before.png` and `corner_after.png`.

*Left for routing:*
- The TCXO_OUT L5 segment, or an L6 path past J31's pads.
- The R7 → U3/R8 divider trace length.
- `setup_board.py --selftest` has 3 other failures in cases this pass did not touch: RF_VTX_CHAIN ×2 and the tall-parts
  0201 case. They are not caused by this change.

**MAJORs (critique round on v3), unfixed, for the owner:**
1. **Installed orientation undefined (layout-dfm-power).** J31 (B, vertical BM04B) works only if B faces up. The docs
   treat F as up (renders, U.FL coax "up into the canopy"), and the DNP motor headers are also on B. State the
   orientation. If F is up, move J31 and USB_MATING to F beside a hole. If B is up, re-check J1, J32, SW1 and the coax
   path, and flip the render labels.
2. **Battery corridor blocked; R1 via count (layout-dfm-power).** SHUNT_CORRIDOR holds U1, R2, R3, C5, C6 and R8. That
   leaves a 1.1 x 3.5 mm L1 neck (about 1.3 mOhm, 2 W at a 40 A burst). R1 pad 1 sits over Q36's drain EP, so it cannot
   take vias. R1 pad 4 fits about 4 vias, where the plan counts 16. Move the six parts out, move R1 or Q36, and reserve
   16 L4 sites.
3. **Hot-loop caps far from 7 of 12 cells (layout-dfm-power).** Distances: C41 6.0 mm, C29 4.5, C35 3.6, C32 3.6, C33 3.1,
   C38 2.6, C26 2.5. C29, C35, C38 and C41 are on the opposite side. Place one cap per cell across pins 1 and 3 on the lead
   side, add a separate EFM8 bulk cap where needed, and check per cell.
4. **D72 via budget not closed (layout-dfm-power).** About 190 power vias are needed and 20 sites are reserved. The pin 1
   via-in-pad is blocked on 10 of 12 cells and pin 3 on 8 of 12. Drain-EP sites free: Q35 0/16, Q38 0/16, Q39 2/16.
   "8 bottom cells need 0 vias" fails, because L6 cannot reach ESC1/2/4. Offset the stacked pairs, then reserve at least
   5 sites per cell pin and at least 5 L4 ties per quadrant in floorplan.json.
5. **BR-14/BR-09 preconditions broken (layout-dfm-power).** U21 is 12.3 mm from U4, and C13 is next to U4, so U21 IN has
   no input cap. U12 OUT is 6.1 mm from C62 and IN 4.4-4.7 mm from C61. Put U21 beside U4, or give it a local 1 µF on IN.
   Move U12 to the BMI270. Check decoupling per pin.
6. **Binding labels not proven (layout-dfm-power).** *OPEN (P4 critique round 4): the routing prep promoted `route/ckpt/28_candidate` at 03:03:28 over the round-3 labels, so the repo board lost them again (check_conventions 37 ok / 2 FAIL, B7 + B9). Round 4 re-applied them with `hardware/tools/silk_pad_labels.py` (the round-3 script moved into the repo, with a `--check` gate) on the repo board and on the route checkpoints that existed at 04:2x; this item stays open until the routing promote step runs `silk_pad_labels.py BOARD` and check_conventions (B7 / B9 ok) before every copy to the repo.* Round-3 text: *Labels fixed 2026-10-10 (P4 critique round 3): the LED / buzzer row labels sat one pad off (the column was reversed in step 5, the labels were not), so the BZ- pad read '5V'; the board now has one label per pad aligned with it (BZ- 5V LED GND) and M4 at J13 (`p2v3/p4/fix3/scripts/silk_fix3.py`, idempotent: re-run it on any routing checkpoint older than this); check_conventions B7 now requires each solder pad's nearest aligned silk label to equal its pad code (a shifted label FAILs). J33 GND sits 0.148 mm from U6's tented, filled+capped EP via ring (KiCad 'silkscreen over pad' 0.15: one silk_overlap warning, accepted, nothing to clip on a tented via). Still open below: the pin-1 dots and the name size.* Missing: the M4 (J13) and BZ- (J22) labels, and the pin-1 dots for
   J32 and J1. The product name fits only at 0.8 mm, against 1.4 mm in D59. Free the silk space, or log an owner decision
   for 0.8 mm.
7. **5.8 GHz interstage (rf-firmware).** U20 RFin (pin 3) faces the edge, while the RTC6705 and C110 sit on the inner side.
   The route is about 12 mm with a side change and no clean RF via site, and it passes R53, R63 and C26. Turn U20 so
   pins 1-5 face U19 pin 35, put C110 at pin 35, and use one RF via within 2-3 mm with 2-4 GND vias. Draw it on User.2
   with a scoped "RF: no vias" exception.
8. **RX wire path drawn toward M3 (rf-firmware).** The User.2 path runs -x for 8.9 mm from AE1, toward the rear-left
   motor. Its last 3 mm is inside the duct or prop disc, and it passes under the J31 shroud corner. Redraw it rearward
   along the (-1, +1) arm, or up into the canopy. Measure it against the M3 leads and duct, the battery pigtail and the
   USB plug, and put the numbers in the D75 table and the README.
9. **FC crystal X1 on the wrong side of U10 (rf-firmware).** XIN/XOUT are B-side pins. The traces run about 7.5 and 8.6 mm
   through the pin 23-37 escape field, R40 sits at the crystal end, and X1 is 0.6 mm from J1 and about 1.5 mm from FL2/PA.
   Move X1, C42, C43 and R40 below U10 at pins 21/22 (band x 110.4-116.0, y 110.7-113.1; shift the HD labels or pads
   about 0.6 mm), or rotate U10.
10. **Wi-Fi feed breaches D75 (rf-firmware).** RF_WIFI runs 15.6 mm past the RTC6705, through a 0.44 mm gap between U21
    and U19, likely on an inner layer. The pi match is split across sides (4 or more via transitions), C132 is 2.9 mm from
    the AE2 feed across the no-ground area, and X4 is 0.23 mm from AE2's pads. Put the whole pi on the bottom at the feed
    and run an L3 stripline with GND fences on User.2. Then either log a scoped D75 exemption (bench-only Wi-Fi, VTX off
    under F9) or re-site AE2/U16.
11. **RP2354A core SMPS on the far side (P4 critique round 3, digital-firmware MAJOR).** RP2350 DS 6.3.8.1: "Don't place
    any of CIN/LX/COUT on the opposite side of the PCB". U10 is on F at (112.0, 106.9); C58 (CIN, pin 49), L2 (pad 2 = LX,
    2.7 mm from pin 48), C56 (COUT, under the EP) and C57 (VREG_AVDD filter, pin 46) are on B. Move all four to F beside
    pins 46-50 (C58 across 49 / 47, L2 with pad 2 at pin 48 in the DS Fig. 26 / 28 orientation, C56 at pin 50, C57 at 46
    with its own GND via to the EP); SW1, now at (113.6, 102.3) F, moves together with D8. Routing: VREG_FB from the C56 pad,
    not under L2; CIN / COUT GND to VREG_PGND at one point with 2 vias; no copper under L2 / VREG_LX on In1. Scripted:
    `check_p5_conditions.py` SMPS (5 lines). If F cannot close: a scoped deviation in DECISIONS.md and a V9 bench item (DVDD
    ripple and load step at the Betaflight clock).
12. **More placement conditions scripted (P4 critique round 3, `check_p5_conditions.py` BOOT / USB / NOR / VTX):** R44 pad 1
    within 1.5 mm of U10 pin 60 on U10's side (now 7.4 mm, B; the 1k isolates the stub, low impact); D8 on SW1's side with
    BOOT_SW <= 3 mm (now B vs F, 3.3 mm); R43 <= 2 mm from pin 51 (2.3); C65 <= 1.5 mm from U13 pin 8 (2.1); C122 <= 1.5 mm
    from U22 IN, same side (meets it; C122 becomes a 4.7 uF 0402 in the schematic, LP5907 CIN > 0.7 uF effective: the next
    `sync_pcb.py` swaps the 0201 land for an 0402). Current board: 15 ok / 28 FAIL.
13. **Round-4 placement inputs (P4 critique round 4):** (a) **U5 → TPS22810DRVR WSON-6 2x2** (D83): the next `sync_pcb.py` swaps the land inside the DBV site; a scratch sync shows its EN/UVLO pad 5 on a GND via and its EP 7 on a +BATT via placed by the routing prep for the DBV body (2 shorting_items + hole clearances): move those two vias when syncing. (b) **RTC6705 bypass / crystal loads** (`check_p5_conditions.py` VTX): C103 100 pF (the BUFVDD / PAVDD pins 31/32 RF bypass) is on F under U19 (B) 3.3 mm away through a via, useless at 5.8 GHz: move it to B beside pins 31/32 (<= 1.0 mm); C95 4.5 mm from pin 25 and C94 2.0 mm from pin 24 (<= 1.5 mm). (c) U20 pin 1 (NU) is now on GND in the schematic: the sync clears the U20 pad 1 / pad 21 shorting_items error. Current board: 15 ok / 31 FAIL.
