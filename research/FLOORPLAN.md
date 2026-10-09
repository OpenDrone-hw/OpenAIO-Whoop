# OpenAIO-Whoop floorplan (P2 proof)

Placed 2026-10-09 on `hardware/OpenAIO-Whoop.kicad_pcb`. It starts from the early preview's block plan
(`scratchpad/preview`) and uses the real P3 library footprints. Every number below comes from the runs listed
under Verification. The board has no schematic yet (P4), so it has no real nets and no routing.

## Result

| Item | Value |
|---|---|
| bom_plan parts | 329 |
| Placed | **326** (154 top, 172 bottom); H1-H3 deliberately not placed (the holes are the spec 7 Edge.Cuts cut-outs) |
| Parts on their bom_plan side | 311; 15 changed side (listed under Changes) |
| `check_spacing.py --min 0.20 --edge 0.20` | **0** pairs < 0.20 mm, **0** edge hits, nearest-neighbour median 0.200 mm; 3 keepout hits = AE1 inside its own antenna areas (D44 exemption, by design) |
| `kicad-cli pcb drc --refill-zones` (10.0.6) | **0 errors**, 4 warnings, 0 unconnected; courtyard 0, edge 0, silk 0 |
| Every part inside its floorplan region and on its side | 326 / 326 |
| Usable area per side, package / incl. 0.1 mm halo | top 628.5 mm²: 49.8 % / **70.9 %**; bottom 616.6 mm²: 53.2 % / **74.2 %** |
| X-ray (exposed pad over exposed pad or LGA field across the sides) | 0 |
| ESC via sites | P source 47/48, N phase 96/96, N source 36/36, gate 24/24, leg-cap 12/12 |
| IC GND / EP vias | 48 of 62 planned |
| Free through-via sites on both sides (0.55 mm lattice) | 108 |

The four DRC warnings are `solder_mask_bridge` at the RP2354A QFN-60 `_Dense` corner pad pairs (1/60, 15/16,
30/31, 45/46): the mask web between corner pads is below 0.10 mm, a library item for P3. The DRC is clean only
because of **temporary land nets**. Pads of one footprint whose copper overlaps carry a net named
`/FLOORPLAN/<ref>_<pads>`: these are the merged FET drain and source lands, the EP pieces and the in-land via pads
(29 nets). They apply to numbered copper pads only, so `sync_pcb.py` replaces them at P4. Without them, DRC
reports 105 `clearance` errors and 109 mask-bridge warnings, all between overlapping pads of one land ("no net"
against "no net").

Renders: `images/floorplan-top.png` and `images/floorplan-bottom.png` (kicad-cli 3D). A silk + mask plot and
block maps are in `scratchpad/p23/renders/` and `scratchpad/p23/fp/map05-*.png`.

## Method

`scratchpad/p23/fp/work/stages.py` is a hand-tuned placement script that rebuilds the board from the P1 board on
every run. Each stage saves a numbered checkpoint in `scratchpad/p23/fp_checkpoints/` (01_fixed, 02_esc,
03_escvias, 04_ics, 05_passives). The stages are:

1. **Fixed items**: motor, battery, user, HD, CAM and LED pads, the antenna hole, U.FL and pogo USB, then their
   silk labels, then the bottom art.
2. **ESC power stages**: four rotated copies of one cell, then the reserved cell via sites and the leg caps.
3. **Big ICs at hand positions**, then mid-size parts in hand-picked slots (`MIDFIX`) and the test pads with their
   labels.
4. **Every other part**, by a nearest-feasible search around an anchor, in an explicit priority order
   (`anchors.py`):
   - the RF chain and PA ring;
   - RTC6705 decoupling, crystal, loop filter and video network;
   - the boost hot loop;
   - LDO and O4 companions;
   - MCU, ESP32 and SX1280 decoupling at their pins;
   - gyro, NOR, ESC cells, the remaining mid parts, then the rest.

   The anchor is the IC pin named in the bom_plan notes where there is one.

The kernel (`fpk.py`) measures with check_spacing's package extents and with the real courtyards, so its result
matches both checkers. It enforces:

- 0.20 mm extent spacing, and 0.25 mm between two 0402s;
- the DRU courtyard rules, including the far-side courtyards of through-hole pads;
- 0.70 mm from TALL parts to 0201/0402 parts;
- the iron-rework halo on the pad's own side: 0.50 mm to any part, 0.70 mm to 0201/0402;
- courtyards outside the 0.30 mm edge band and every footprint keepout;
- reserved via sites;
- X-ray: no exposed pad over an exposed pad or LGA field on the other side;
- the spec 11 N1 and gyro distances as hard constraints.

`mkplan.py` writes `hardware/floorplan.json`, `verify.py` produces the checks below, and `occ.py` measures
utilisation.

## Regions (`hardware/floorplan.json`)

There are 44 regions. Each spec 10 block has a core region around its main part. Parts more than 3 mm from that
part go to a `<block>_outer_<side>` region, so spread-out parts show in the report instead of being hidden
(50 parts in total). The main areas, in mm from the body centre:

| Side | Block | Region (x0, y0, x1, y1) | Notes |
|---|---|---|---|
| T | ESC1 / ESC2 / ESC3 / ESC4 cells | P rows on lines ±8.095; columns at y −0.85…6.75 (ESC2) and −6.75…0.85 (ESC3); rows at x 3.0…10.6 (ESC1) and −10.6…−3.0 (ESC4) | EFM8s against their rows; 8 ESC4 passives in `esc4_outer_t` |
| T | VTX RF (PA, BPF, U.FL, chain) | 1.87, −12.7, 12.1, −5.25 | PA at (8.52, −9.2), rotated 90 |
| T | VTX RTC6705 | −2.58, −10.3, 4.7, 1.6 | RTC6705 at (1.4, −5.15), rotated 270 |
| T | VTX PA reference + drive stage | −12.85, 3.9, −8.65, 10.6 (plus outer) | moved around the NOR |
| T | NOR | −10.0, 4.1, −2.44, 9.95 | 3.04 mm from the antenna hole |
| T | gyro + LDO | −3.2, 1.1, 2.55, 5.55 | gyro at (−1.0, 3.05) |
| B | FC (RP2354A) | −6.55, −6.1, 7.2, 7.35 | MCU centred at (0, 0) |
| B | RX (ESP32, flash, crystal) | −0.45, −12.7, 10.8, −4.75 | ESP32 at (5.15, −9.9) |
| B | radio (SX1280, TCXO, LPF) | −10.4, −0.55, −2.6, 8.15 | SX1280 at (−6.7, 3.95) |
| B | boost | 5.3, −5.4, 12.45, 2.25 | U2 at (8.95, −2.45), L1 at (11.3, −3.0) |
| B | power entry | −10.7, 7.65, 1.6, 12.6 | shunt at (−5.4, 9.25) |
| B | O4 switch | −8.05, −4.95, −3.3, 1.5 | U5 at (−5.57, −2.35) |
| B | art | 3.65, 7.4, 9.95, 9.0 | logo; the name block is silk text at the rear centre |

## Block placement rationale

- **ESC cell**, from the spec 4.3 land facts:
  - Both FETs face outward with their 2.4 mm land axis along the row and the drain row (pin 4 + strip pad 7)
    toward the motor pads, so each row is 7.6 mm long (the sketch assumed 6.7).
  - The P row is on the line 8.095 mm from the centre on the top. The N row is on 10.125 mm on the bottom,
    offset outward with its drain land under the phase field. The 8 phase vias of the N footprint sit 0.2 mm
    from the P body.
  - The N row moved 0.5 mm inward of the sketch, so the 3 source-strip GND vias and the gate via land on the top
    0.15 mm inside the motor pads.
  - The cells are rotated copies: ESC2 at 90°, ESC4 at 180°, ESC3 at 270°.
  - The P source in-pad vias (2 x 2) and the gate vias land on the bottom; their sites are reserved.
- **Leg caps** sit on the bottom at the N source end (spec 4.3). The search along the row picks a spot whose
  +BATT via lands on the top clear of the motor pads. The offset from the source copper centre is 0 to 1.8 mm
  (C26 1.8, C21 / C39 1.5, C32 1.15 mm). This is why the motor-pad pitch is now 1.65 mm.
- **EFM8 position**. Each EFM8 sits 0.245 mm from its P row, so its 5 EP vias land on the bottom outside the
  RP2354A land. ESC2's EFM8 moved north of its column, into the front-right pocket at (7.1, −3.1), because there
  is no room behind the column. ESC4's EFM8 keeps a 1.0 mm gap to ESC3's for its VDD bulk.
- **RTC6705** is rotated 270° so PAOUT1 (pin 35) faces the PA. The chain runs PAOUT1 → C110 → PA RF in (south
  side); then PA RF out (north side) → C119 → BPF → U.FL.
  - On the real pinout the crystal and loop filter then face south. The spec's "loop filter west" cannot hold
    together with "PAOUT1 toward the PA".
  - The 8 MHz 3225 crystal sits at (2.1, 0.2), south of the RTC6705.
- **Gyro** sits at (−1.0, 3.05), clear of the RP2354A EP for X-ray. It is 4.09 mm from the FETs, 8.1 mm from the
  boost, 10.55 mm from the PA and 6.65 mm from ripple bulk caps.
- **Boost** sits at the right edge on the bottom. The PA moved 0.6 mm north so the boost keeps 2 mm from the PA
  projection. Cin and the first two Cout sit 0.2-0.25 mm from U2; Cout 3 and 4 sit 1.7 mm away.
- **FC, RX and radio**: the RP2354A is centred with its crystal at XIN / XOUT (north). The ESP32 is front-right,
  under the PA, with the EPs 0.32 mm apart. The SX1280 is rear-left, and its TCXO is south-east of it at
  (−4.6, 7.2).
- **Power entry**: shunt R1, INA186, TVS and pad bulk are inboard of the battery pads. The +3V3 and +3V3_VTX
  LP5912 regulators are on the bottom east of the MCU. The TPS2116 mux is at the front centre, between the pogo
  pads and the FC crystal.

## Keepouts and distances decided now

All distances are edge to edge, in 2D projection. The values are measured on the placed board (`verify.py`).

| Rule | Limit | Measured | Status |
|---|---|---|---|
| Crystals / TCXO / RF filters to phase copper (N1) | ≥ 3 mm | X1 3.57, X2 5.93, X3 6.26, X4 4.84, FL1 5.54, FL2 8.9 | pass (hard constraint) |
| Crystals / filters to boost switch node (N1) | ≥ 5 mm | X2 5.08, X4 5.10, others 7.8-17.8 | pass |
| RTC6705 loop filter to phase copper / boost SW | ≥ 3 / 5 mm | 4.85 / 5.94 | pass |
| Gyro to FET groups / boost / PA / ripple bulk / switch nodes | ≥ 4 / 5 / 10 / 5 / 2 mm | 4.09 / 8.13 / 10.55 / 6.65 / 5.0 | pass |
| Boost to FET groups (H2) | ≥ 2 mm | **0.4** (ESC2 N, Q13) | fail: see What did not fit |
| NOR to RX antenna hole | ≥ 3 mm | 3.04 | pass |
| Pad groups to RX antenna hole | ≥ 6 mm | HD 13.0, CAM 25.2, LED 12.6, **user 3.95** | user group: O20 option (b), V7 |
| Pogo holes to `RF_VTX_CHAIN` | ≥ 2.9 mm | 3.06 | pass |
| X-ray | none | 0 | pass |

**Rule areas** are written by `setup_board.py` from the placed positions:

- `TAB_T1` on the right edge at y −6.6, plus T3 and T4;
- `MOUNT_*`;
- `RF_VTX_CHAIN` along the real pad chain;
- `RF_VTX_UFL` and `RF_PAD_CUTOUT` at the U.FL;
- `RF_RX_FEED` from the LPF pin to the hole;
- `RF_RX_ANT`, `RF_RX_EXIT`, `RF_RX_ROOT`;
- `SHUNT_CORRIDOR` from B+ (J2) to the shunt;
- `PART_EDGE_BAND`.

**Video against SMPS.** The video parts stay 3.3-8.6 mm from the boost: R51 3.3, U14 4.8, C66 8.6 mm. One
exception: the CAM pad J23 (top) lies over the 2520 inductor L1 (bottom) in projection. The inductor is a molded
type, with the L2 and L5 planes in between. P5 checks this with the V5 video test, or shifts L1 and the CAM
pads.

## Via sites

Via sites are counted for 0.35/0.20 Type VII vias. A site counts when the drill sits inside the pad and the
far-side landing keeps 0.15 mm from other parts' pads, holes and the edge.

- **ESC cells**:
  - P source: 47 of 48. On Q16 (ESC3) the fourth in-pad via lands on a bottom pad; P5 nudges that part.
  - N phase field 96/96 (in the footprint). N source strip 36/36. Gate vias 24/24.
  - Leg-cap +BATT vias 12/12 land on the top clear of the motor pads.
- **IC exposed pads, fitting / planned**:

  | Part | Fit | Planned |
  |---|---|---|
  | U16 ESP32 | 9 | 9 |
  | U19 RTC6705 | 9 | 9 |
  | U20 PA | 9 | 9 |
  | U18 SX1280 | 4 | 4 |
  | U12 | 1 | 1 |
  | **U10 RP2354A** | **4** | **9** |
  | U4 LP5912 (+3V3) | 1 | 2 |
  | U21 LP5912 (+3V3_VTX) | 0 | 2 |
  | U22 LP5907 | 0 | 1 |
  | U17 GD25Q32 | 0 | 1 |

  - The RP2354A meets the spec 8.3 minimum of 4. Its other landings fall under the RTC crystal and the gyro LDO
    on the top.
  - The LP5912 and LP5907 EPs on the far side are under top parts: they need dog-bone vias (P6).
  - The U17 EP strip is 0.2 mm wide, so no drill fits in it.
- **GND pins**: 10 of 14 checked parts have an in-pad or adjacent via site. U5, U14, U15 and X1 need a short
  trace to a via (P6).
- **Free via sites on both sides**: 108 on a 0.55 mm lattice. The spec 9.2 allowance is 150 vias outside pads and
  cells, so stitching and side changes depend on via-in-pad in 0201 and QFN pads (D23). P6 confirms this.

## What changed against the spec, and what did not fit

1. **ESC rows are 7.6 mm long (sketch 6.7 mm)**, with the P and N lines at 8.095 / 10.125 mm.
   - ESC1 and ESC4 are centred at ±6.8. ESC2 and ESC3 columns are centred at ±2.95, which the corner with the
     rows forces.
   - As a result, the boost cannot keep **H2** (2 mm from the ESC2 FETs): it is 0.4 mm away. The band between
     the ESC2 column and the PA projection is about 1.7 mm with these columns.
   - Owner and P5 item: a thermal check in V8, or move the boost.
2. **Motor-pad pitch is 1.65 mm (spec 1.5 mm)**, so all 12 leg-cap +BATT vias land on the top. The pad groups
   are M1 x 4.85…9.15, M2 y 4.35…8.65, M3 y −7.15…−2.85, M4 x −9.15…−4.85.
3. **O20, the user UART group**, is a row on the top at the left centre: TP0, RP0, 5V, GND at x −12.3…−8.4,
   y 1.95, labels below. It is 3.95 mm from the RX antenna hole, against the 6 mm rule (option (b)); V7 checks
   return loss with wires attached.
4. **Side balancing** (spec 9.3 lever):
   - O4 switch block (U5, C16, C17, R9-R11, D2, Q1) to the bottom front-left; +5V_HD runs about 9 mm to the VHD
     pad.
   - +3V3_VTX LP5912 (U21, C120, C121) to the bottom, about 5 mm from the RTC6705.
   - 4 passives (R43, R44, C69, C70) moved to the top by the search.
5. **VTX power pocket.** The spec 10 pocket now holds ESC2's EFM8.
   - The PA reference LP5907 (U22) and the drive stage (Q27, R68-R77, C124, C125) moved to the top rear-left
     around the NOR, so PA_VREF and PA_BIAS run about 13 mm as DC lines.
   - P5 / V5 check them for noise.
6. **Product name OPEN / AIO / WHOOP in 1.4 mm rows**, against the 2.0 mm of LINEUP B4.
   - With the RP2354A at the centre, no 3-row 2.0 mm patch exists between the MCU and an N row (5.4 mm gap).
   - This is the spec 9.3 lever "owner / lineup exception". The owner signs off or picks the alternative of an
     off-centre MCU.
   - REV1 is 1.0 mm. The incutec logo is 6.1 x 1.4 mm on the bottom, in the ESC1 via-landing band (silk over
     tented vias).
7. **Silk details**:
   - The HD frame is not drawn: no room between the HD labels and the LED labels. VHD, GND, TX1 and RX1 are
     labelled.
   - The `-` sign sits between the B- pad and the rear edge; `+` is left of B+.
   - Pad codes use the KiCad stroke font (0.8 / 0.6 / 0.13). At 0.8 mm the TrueType face fails DRC
     `text_thickness`, and Tokyo is not installed so it cannot be embedded (B12 warn). Tokyo is kept for art of
     1.4 mm and up.
8. **Mounting holes** stay Edge.Cuts cut-outs (spec 7). H1-H3 are not placed: at P4 mark them "exclude from
   board" or drop them.
9. **Small moves**:
   - Pogo USB centred at x −0.35, because the ESC4 N row needs the room on its left.
   - B- moved 0.1 mm left.
   - HD column moved 0.3 mm rearward.
   - The shunt is rotated 180° (sense pads toward the battery pads); P5 may turn it back.
10. **Parts far from their anchor**: the median anchor distance is 2.55 mm, and 56 parts are more than 4 mm away.
    Capacitors more than 4 mm from their pin, for P5:

    | Group | Parts (mm from pin) |
    |---|---|
    | ESC4 EFM8 VDD bulk | C36 6.6 |
    | RTC6705 VCO | C103 5.4, C102 4.6 |
    | Loop filter | C106 / C107 4.3 |
    | ADC RC | C59 / C60 6-7 |
    | OSD | C66, C67, C68, C70 4.3-7.2 |
    | ESC bulk | C23, C29, C35, C41 4.4-5.1 |
    | Pad bulk | C2 7.5 (kept 5 mm from the gyro) |
    | LED translator | C126 / C127 4.4-4.6 |

## Rule and tool changes (`hardware/tools/setup_board.py`, logged as D45-D50)

- Tab T1 moved to the right edge at y −6.6, as spec 7 round 4 asked.
- The `TALL` class pattern now matches `*IND-SMD_L2.5-W2.0*`. The old `*L2.5-W2.0*` also caught the 12 MHz 2520
  crystal; spec 8.4 names the U.FL and the 2520 inductor only.
- `SOLDER_PAD` now includes `*MotorPad*` and `*BattPad*`, the P3 library names (spec 4.10 / 7 edge-pad
  exception).
- New class `MOTOR_PAD`, and new rule `D21 motor_pad_ring_side`: the 0.5 mm small-passive halo applies on the
  motor pad's own side, per spec 10 "from every part on its side". The far side is only the 0.9 mm anchor ring.
- `D21 footprint_via_pads` (3 rules) for vias drawn as Heatsink PTH pads (EFM8 EP, CSD13202Q2 phase field): via
  annular 0.075, hole clearance 0.20, same-net hole spacing 0.20. The rule "PTH pads, copper 0.40 apart" no longer
  applies to them. These come from the LIBRARY.md integration item.
- `VTX_CHAIN`, `UFL_ZONE`, `RF_PAD_CUT`, `RX_FEED` and `SHUNT_CORRIDOR` now follow the placed pads, as spec 15.6
  asked.
- `--selftest` now strips the placed parts from its temporary copy. Result: 68 cases, 0 failures.
- `setup_board.py --check` reports "project files are up to date".
- `check_conventions.py`: 27 ok, 1 FAIL, 4 warn. The FAIL is A5, the schematic wordmark, unchanged from the
  baseline. The warnings: B12 font and embedding, A6, D1.

## For P4 / P5 / P6

- P4: `sync_pcb.py` replaces the `/FLOORPLAN/*` land nets. Mark H1-H3 "exclude from board".
- P5:
  - boost H2;
  - the 5.8 GHz input line's 1 mm part-free band (PA VCC caps C114-C116 sit next to it);
  - pull the far capacitors listed above in;
  - check the PA_VREF and drive-stage DC lines;
  - CAM pad over L1;
  - the Q16 fourth source via.
- P6: dog-bone vias for the U4, U21 and U22 EPs; GND vias for U5, U14, U15 and X1; via-in-pad in decoupling
  pads to close the via count.
