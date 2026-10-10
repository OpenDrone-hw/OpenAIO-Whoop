# Review pack: routing prep (zones, via budget, critical nets) (route step 2, 2026-10-10)

This pass compares the board against checkpoint `p2v3/route/ckpt/20_pre_prep`, which is the repo board after the sync
step (`12_candidate`). That step's pack is saved there as `CHANGES_sync.md`. No footprint moved: `diff-top.png` and
`diff-bottom.png` are all grey, and `check_spacing --d70` gives 0 / 0 / 0. All new content is copper, shown in
`copper-top.png` and `copper-bottom.png`. Those are `render.sh` fab plots with F.Cu or B.Cu; the bottom view is mirrored.
The old board had no copper, so these renders are the geometric diff.

## What was added (scripts in `p2v3/route/prep/tools`, chain `chain.sh`)

The order is chosen so that critical routes and supply taps get their space before via fields close it up:

1. **RF lines** (L1, 0.105 mm CPWG over solid L2, locked), each with a GND fence on both sides (offset 0.45 mm,
   pitch 0.8 mm or less):

   | Net | Path | Length |
   |---|---|---|
   | RF_PA_OUT | U20.13 to FL2.1 | 1.26 mm |
   | RF_UFL | FL2.3 to J1.1 | 1.18 mm |
   | RF_RFIO | U18.22 to FL1.1 | 1.73 mm |
   | RF_RX_ANT | FL1.3 to the AE1 hole | 1.95 mm |

   The fence uses 12 vias.
2. **Cell supply taps:** 23 of the 24 AGM supply pins get a track and via to their plane. P-source pin 3 goes to +BATT
   on L4 and N-source pin 1 goes to GND on L2/L5. Each tap is up to 2.5 mm long and 0.25 mm wide.
3. **Critical nets** use a scripted grid router with exact shapely clearances, 0.03 mm over the DRU, silk-aware, on
   L1 and L6 only (spec 8.2: no gate, analog or sensitive nets on L3/L4).
   - 13 of 66 nets are routed:
     - gates: ESC1 A_COM and A_PWM, ESC2 A_PWM and C_PWM, ESC4 B_COM
     - BEMF: ESC3 BEMF_B and ESC4 BEMF_B
     - crystals: XIN, XOUT_X, XTA and TCXO_OUT
     - U2_FB and OSD_SYNC
   - The other 53 have no legal path (see Open).
4. **Zones** (53 copper zones):
   - L2 and L5: solid GND.
   - L4: solid +BATT. It is the only zone on that layer, so no holes were needed.
   - L3: a GND reference patch under the U.FL pad cut-out.
   - L1 and L6: GND fill at priority 1.
   - +BATT_IN pour in SHUNT_CORRIDOR (J2 to R1), and the R1 output pour.
   - Per cell: +BATT and GND pours on the lead side, and phase pours from the drains to the motor land. Phase copper is
     kept 0.45 mm off each cell's own gate and supply pins.
   - Boost: SW, VIN, VOUT and GND pours.
   - All pours are solid (D21). Planes are single islands.
5. **Via fields** for the D72 transitions, then GND stitching: via-in-pad on IC, connector and 0402 GND pads, and an
   edge GND fence. Finally, plane taps for the remaining unconnected GND and +BATT pads.

## Via count by transition (298 total, all 0.35/0.20 through vias, tented, Type VII)

Assumed current per via: 1.0 A continuous, 2.5 A burst up to 2 s. That is 20 µm plating, about 0.6 mOhm L1 to L4 and
1.24 mOhm full length (FLOORPLAN §Power). The burst case is 12 A per cell and 40 A in total.

| Transition | Vias | D72 need at 2.5 A | Note |
|---|---|---|---|
| L4 +BATT to cell pin 3 | 28 field + 3 in pad + 12 taps (43) | 5 per cell (60) | per cell 1-7, see Open |
| Cell pin 1 to GND L2/L5 | 47 field + 3 in pad + 11 taps (61) | 5 per cell (60) | Q34, Q37 and Q39 are short |
| Phase drains to far-side phase pour | 46 in pad | 5 per cell | Q36 has 0 |
| Hot-loop caps (+BATT / GND) | 1 / 2 | 2 per cap | |
| R1 +BATT side to L4 | 2 in pad + 3 beside (5) | 16 | R1 sits over the Q35/Q36 drains: BLOCKER for 40 A |
| J3 GND to planes | barrel + 8 | barrel + 8 | ok |
| Boost U2/L1 | 1 (cap GND) | 4 VIN + 4 GND + 2 VOUT | U2 is under top parts; VIN/GND go through pours |
| GND via-in-pad (IC, connector, 0402) | 60 + 13 + 2 | | stitching L2-L5 |
| Edge GND fence | 28 | 2.5 mm pitch or less | 12 gaps over 2.5 mm (cells and pads at the edge, antenna keep-outs) |
| RF fences | 12 | 1 mm pitch or less | met on the 4 routed RF lines |
| Plane taps (other pads) | 10 | | |
| Router layer changes | 6 | | |

## Checks (repo board)

- **DRC** (`kicad-cli pcb drc --schematic-parity --refill-zones`):
  - **1 error, the same one as before:** shorting_items at U20 pad 1 (NU) against the EP. The schematic fix (tie pin 1 to
    GND) is pending.
  - **Unconnected:** 690 to 391 (pcbnew).
  - **Warnings:** 13 (mask-bridge 9, lib mismatch 2, 1 copper sliver, 1 isolated copper).
  - Zone fills are saved with the project rules, so DRC gives the same result with or without refill.
- **Parity 25:** the 21 footprint_filters_mismatch items come from the schematic. The schematic was also re-saved at
  02:59 by the review workflow: C122 is now 1 uF 0402 (it was 0201), and the D1 description changed. The starting board
  gives the same 25 against the current schematic. A re-sync is due once SCHEMATIC_DONE exists; the marker was absent at
  hand-off.
- **silk_check:** 8 violations, the same as before (LOGO1 library graphics). The via checker and the router keep copper
  out from under silk.
- **setup_board.py --check:** up to date.

## Rule change (logged for DECISIONS.md)

`setup_board.py` "RF: no vias" now exempts `/VTX/RF_PA_IN` only. The RTC6705 is on the bottom and the PA on the top, so
this net needs the one RF via (FLOORPLAN Open). The DRU was regenerated by the script and is a named, scoped exception
(D21). The RF_PA_IN route itself is not placed yet (see Open).

## Open (for the next routing / placement loop, D74)

- **Shunt R1 to L4:** only 5 vias (16 needed). R1 is stacked over the Q35/Q36 drain lands, so there is no via room.
  Move R1, or offset the cells.
- **Cell +BATT vias below 5:** Q30 (1), Q31 (1), Q33 (2), Q37 (2), Q38 (2), Q39 (3), Q40 (1).
- **Cell GND vias short:** Q34, Q37 and Q39.
- **Q39 pin 1 has no plane tap:** it is boxed in by a B-silk label, the Q37 drain above it (F) and the Q35 drain.
- **No legal path for 53 critical nets.** These are placement problems, not router limits:
  - **Gyro SPI and the 6 other U11 nets:** the BMI270's bottom pad row sits 0.30 mm from the X1 pad on F, with the
    RTC6705 pad row under it on B.
  - **ESC3/ESC4 gates and BEMF:** EFM8 pins are boxed in by far-side cell lands.
  - **USB:** J31 to D7 to R42/R43 to U10 is about 18 mm across the board.
  - **Video chain, U19 crystal, RF_PAOUT1/RF_PA_IN:** C110 sits on the far side of U19's pad 35; the PA input needs a
    via next to C26 and C118.
- **Wi-Fi feed:** RF_WIFI needs a via between R88 (F) and C133 (B), plus the inner-layer 50 ohm line.
- **Long routes:** ESC2 C_PWM (11.5 mm) and TCXO_OUT (11.3 mm) are long detours. Review them when parts move.
- **Thermal relief on 0201 pads:** pours are solid for now. The tombstone check is pending.
