# Hand-off: routing OpenAIO-Whoop

State on 2026-10-10 (decision D111): the schematic is final and the board has an
initial layout. Every part and IO pad is placed, synced to the schematic, with
planes and rule areas in. Nothing is routed. Routing is the next step and is
yours.

## What is in the repo

| Item | Where | State |
|---|---|---|
| Schematic | `hardware/OpenAIO-Whoop.kicad_sch` + 10 sub-sheets, `hardware/OpenAIO-Whoop-schematic.pdf` | final; ERC 0 errors |
| Layout | `hardware/OpenAIO-Whoop.kicad_pcb` | placement, pours and rule areas; 0 tracks, 499 unrouted connections |
| Library | `hardware/lib.kicad_sym`, `hardware/lib.pretty` (114 footprints), `hardware/lib.3dshapes`, `hardware/KiCad-Library` submodule (fdf8319) | every symbol, footprint and 3D model resolves from a fresh clone; see `research/LIBRARY.md` |
| Rules | `hardware/OpenAIO-Whoop.kicad_pro` (net classes, HDI layer pairs), `hardware/OpenAIO-Whoop.kicad_dru` | both written by `hardware/tools/setup_board.py`; change the script and re-run it, do not hand-edit |
| Renders | `images/front.png`, `images/back.png` | 3D renders of this board (4f845ba5), with the optional motor headers shown fitted |

Placement facts (from the board, md5 4f845ba5):

- 266 footprints: 134 on the front, 132 on the back. 20 are DNP: the 4 motor
  headers J4/J7/J10/J13, the 13 battery and IO solder pads, the AE1 wire hole, and C132/C133
  (Wi-Fi tuning, 1.2 pF).
- Outline: 30.35 x 30.35 mm bounding box, 673.42 mm2. That is the 26.4 mm body,
  three D3.5 ear holes on the 25.5 mm pattern, and a 45-degree front chamfer
  with c = 3.0 mm (D112).
- Vias already placed (in a pad or under a part body, except the R1 field):
  - 211 microvias: 108 GND, 92 +BATT, and 11 on signal test lands (each in its own pad).
  - 104 buried vias: 88 +BATT, 16 GND.
  - 0 through vias.
  - Exceptions to D107 (open item 3): 18 +BATT microvias and 5 +BATT buried
    vias stand free in the R1 battery-feed field.
- Every RF net now has all its pads on one side (open item 0, done). The
  Wi-Fi pi network R88/C132/C133 is on the back with U16 and AE2. AE2 moved
  1.50 mm along the chamfer, and its five WIFI_* rule areas moved with it. C110
  is on the front with U19, L3 and U20. R44 and C117 (back) moved 0.32 and
  1.13 mm to make room. No other part, via or outline segment changed.

## Opening it

```
git clone --recursive https://github.com/OpenDrone-hw/OpenAIO-Whoop
```

Open `hardware/OpenAIO-Whoop.kicad_pro` in KiCad 10 (10.0.6 was used). The 3D
models resolve through the project text variable `OPENDRONE_LIB`
(`${KIPRJMOD}/KiCad-Library`) in the `.kicad_pro`.

**Scripting trap:** pcbnew's `SaveBoard()` rewrites the `.kicad_pro` next to
the board with empty `text_variables`. That drops `OPENDRONE_LIB` and with it
most 3D models. After any scripted save, restore the `.kicad_pro` from git.
`setup_board.py` already guards against this.

## Stack-up and via set

NextPCB 6L 1.0 mm, 1.027 mm with mask, FR-4 Dk 4.2. Outer copper is 1 oz
finished, inner copper 0.5 oz (`hardware/tools/stackup.json`).

| Layer | Copper | Role (DESIGN-SPEC.md 8.2, v4 DRU) | Pours on the board now |
|---|---|---|---|
| L1 F.Cu | 35 um | top parts, 5.8 GHz and 2.4 GHz RX lines, phase copper | GND x4, +BATT x5 local |
| prepreg 1080 | 77 um | | |
| L2 In1.Cu | 17.5 um | solid GND (RF and top reference, ESC return) | GND, +BATT islands x4 under FETs |
| core | 300 um | | |
| L3 In2.Cu | 17.5 um | digital signals between the sides | GND fill (cut back as you route) |
| prepreg 2313 | 103 um | | |
| L4 In3.Cu | 17.5 um | +BATT plane (ESC feed) | +BATT, 616.8 mm2 filled |
| core | 300 um | | |
| L5 In4.Cu | 17.5 um | solid GND (bottom reference, ESC return) | GND, +BATT islands x8 under FETs |
| prepreg 1080 | 77 um | | |
| L6 B.Cu | 35 um | bottom parts, Wi-Fi feed, Kelvin pair | GND x8, +BATT x8 local |

HDI 1+4+1 (D97, `research/FLOORPLAN-V4.md` section 18):

- Laser microvias 0.10 / 0.25 mm, L1-L2 and L6-L5, copper filled, in pad.
- Buried vias 0.20 / 0.35 mm, L2-L5, plated over (POFV), staggered 0.25 mm
  from their microvia. No stacking.
- Through vias are allowed but should be a last resort.
- D107: every microvia goes in a same-net pad and every buried via under a part
  body; there are no free-standing stitching vias.

## Checks and the files they used

| Check | Result | Files |
|---|---|---|
| `kicad-cli pcb drc --severity-all --schematic-parity`, with and without `--refill-zones` | 0 errors, parity 0, 499 unconnected. Warnings: isolated_copper 1 (the L3_UFL_REF island), lib_footprint_mismatch 2 (J31, J33), solder_mask_bridge 8, via_dangling 11. The zone fills are saved in the board, so the result is the same without a refill | board 4f845ba5, `.kicad_pro` 80000762, `.kicad_dru` 8462081f, sheets at 0ed1abd (root 25149953) |
| Same DRC and ERC in a clean `git clone` (offline submodule, empty HOME, KiCad's default symbol table) | identical: DRC 0 errors, parity 0; ERC 0 errors | board 4f845ba5, sheets at 0ed1abd |
| `kicad-cli sch erc --severity-all` | 0 errors, 2 pin_to_pin warnings (U13 WP and HOLD tied to the U4 LDO output, justified in `research/SCHEMATIC.md`) | sheets at 0ed1abd |
| `hardware/tools/check_conventions.py --stage planned` | 39 ok, 1 FAIL (B7: 6 pad labels, open item 9), 2 warn, 3 skip | board 4f845ba5 |
| `check_netlist.py`, `check_rules.py`, `setup_board.py --check` | 7 ok / 0 FAIL; custom rules parsed; project files up to date | board 4f845ba5 |
| ESC plane solve (`plane.py`, a work script that is not in the repo: In3 only, 0.5 oz at 80 C, 12 A per ESC) | ESC1 33.7, ESC2 38.8, ESC3 22.0, ESC4 31.5 mV (unchanged) | board 4f845ba5 with `.kicad_pro` 80000762 beside it |

## What the router has to do

1. **USB.** Route `/USB_D_P` and `/USB_D_N` (J31, then D7 ESD, then R42/R43 27R)
   as a pair. The USB class asks for a 0.12 / 0.12 mm pair with skew under
   0.5 mm. The MCU-side nets `/RP2350A/U10_USB_DP` and `/RP2350A/U10_USB_DM`
   (U10 pins 52/51 to R42/R43, 1.6 and 1.9 mm) are not in the class because
   KiCad only pairs names that end in `_P`/`_N`; route them as a pair by hand.
   R42 is on the front and R43 on the back, so give both lines the same number
   of layer changes.
2. **RF feeds.** The RF class takes no vias. The one exception in the DRU is
   `/VTX/RF_PA_IN`. Use 50 ohm CPWG, about 0.105 mm, on L1 over L2 or on L6
   over L5, with GND fence vias only in GND pads or pours.
   - RX 2.4 GHz, all on L1: U18 pin 22 (RFIO) to FL1 is 19.3 mm pad to pad
     (open item 7), then FL1 to the AE1 wire hole is 2.5 mm, inside the
     `RF_RX_FEED` / `RF_RX_HOLE` areas.
   - VTX 5.8 GHz, all on the front: U19 pin 35 to L3 is 0.65 mm, L3 to C110
     is 0.74 mm. C110 to the U20 PA is 2.8 mm pad to pad. Route it through
     the 0.49 mm channel between the U22 pads and the U19 pin column. That
     channel passes `/PA_EN` and `+3.3V_VTX` pins, so keep the 0.15 mm RF gap.
     It is too narrow for a GND fence, so fence the line above and below the
     channel. U20 to FL2 is 1.3 mm and FL2 to the J1 U.FL is
     2.6 mm. `/VTX/RF_PA_IN` keeps its DRU via exception but no longer needs
     a via. The DRU comment still says the RTC6705 is on the bottom; that is
     out of date. C110's pad is 0.05 mm inside the left edge of
     `RF_VTX_STRIP`.
   - Wi-Fi, all on the back (L6 over L5): U16 pin 2 to R88 is 0.95 mm, R88
     to the AE2 feed is 0.60 mm (pad centres). The C133 and C132 shunts sit
     0.60 and 0.52 mm from the R88 pads. Their GND pads are outside
     `WIFI_VOID_V1`.
3. **ESC power path** (D103). The path runs from the battery pads to the R1
   shunt, onto the L4 +BATT plane, through buried vias into the In1/In4
   islands, and up microvias into each AGM210MAP +BATT pad and its 22 uF cap.
   GND returns on L2/L5. The hot-loop caps are already across each AGM supply
   pair. Keep the phase copper from each AGM to its motor pads short and wide.
   Route the R1 Kelvin pair as a pair, never on In2/In3 (D85), and away from
   switching copper.
4. **Planes.** Keep L2 and L5 solid GND, cut only under wide RF pads. Keep L4
   solid +BATT under every L3 route. Respect the D85 layer limits in the DRU:
   In2 carries no analog or RF, and In3 carries no analog, RF or gate. Keep the
   24 rule areas (names in the DRU comments).
5. **Vias.** Follow D107 as above. Every via you add goes in a pad or under a
   body.

## Open items

0. **RF parts on the wrong side: done.** All three nets are now one-sided,
   with no new DRU exception:
   - `/VTX/RF_PAOUT1`: C110 moved to the front (112.925, 106.375), beside L3.
     The whole 5.8 GHz chain is now on the front. That leaves `/VTX/RF_PA_IN`
     with both pads on the front, so its via exception is no longer needed.
   - `/RX/RF_WIFI` and `/RX/RF_WIFI_ANT`: R88, C132 and C133 moved to the back,
     between U16 pin 2 and AE2.
     - There was only 0.73 mm between U16 pin 2 and the AE2 feed pad.
     - AE2 could not move toward the chamfer: its pads are 0.65 mm from the
       edge and the limit is 0.30 mm plus the edge band.
     - So AE2 moved 1.50 mm along the chamfer (down and right). The
       WIFI_VOID_V1, _V2_L2, _V2_L3, WIFI_FAR_F and WIFI_GND_LINK areas moved
       with it, so the D90 void keeps its shape.
     - R44 moved 0.32 mm and C117 1.13 mm to make room.
   - Lengths are pad centre to pad centre, before routing (the earlier
     numbers crossed sides):
     - Wi-Fi: 0.95 + 0.60 mm.
     - VTX: 0.65 + 0.74 mm, then 2.8 mm from C110 to U20.
1. **ESC power drop margin.** The worst ESC (ESC2) drops 38.8 mV against the
   40 mV budget, a 1.2 mV (3 %) margin with only L4 counted. Options:
   - Order 1 oz on In3. The same solve at 1 oz gives 19.4 mV.
   - Add a parallel +BATT pour on In2 (L3) wherever it carries no signals.
   - Widen the L1/L6 +BATT copper from R1.
   Re-run the plane solve after routing, because tracks on L4 cut the plane.
2. **Per-FET via current margin.** One high-side FET carries the full phase
   current: 12 A peak, about 6.9 A RMS in 6-step (12 / sqrt 3).
   - Microvias into each FET's +BATT node: FET pads 2 + cap pads 2-3 = 4-5.
   - Buried vias on the In1/In4 island feeding each FET: 3-7. Q30, Q33 and Q39
     have 3.
   - Against the 1 A per filled 0.10 mm microvia rule the polish pass used,
     4-5 A is short of 6.9 A RMS. At peak that is 2.4-3 A per microvia.
   - The buried vias (0.20 mm, about 20 um plating, around 1 A each by IPC-2152
     cross-section equivalence, conservative for a short plane-cooled barrel)
     fall short on islands with 3-6 of them. An island with 7 just meets
     6.9 A.
   - Options: add microvias in every +BATT pad and EP of each AGM and its cap,
     and buried vias under each FET body, up to at least 7 of each per FET. Or
     ask NextPCB for its rated current per filled microvia and buried via and
     size from that.
3. **R1 battery-feed via field.** 18 free-standing +BATT microvias (within
   3.8 mm of R1) and 5 buried vias outside any body. Put them inside a +BATT
   F.Cu pour from R1 pin 4 over the field. The 48 A path needs that copper
   anyway, and it makes the vias D107-legal.
4. **Passives far from their pin.** Measured as pad-centre distance to the
   nearest same-net IC pad, ignoring GND and +BATT: 23 of 147 are over 1.5 mm
   (mean 1.15 mm). The worst are:
   - R44 21.0, R11 9.4, C95 6.9, R73 5.0, C94 4.8, R68 4.7, R55 4.5,
     R48 3.3, C52 2.7, C50 2.5, L1 2.3, C8 2.2 mm.
   - Some of these serve a connector or test land rather than the nearest IC,
     so check each one.
   - C94/C95 (RTC6705 crystal loads) and C103 have `check_p5_conditions.py`
     limits.
5. **U18 over Q32 (not changed).** The SX1281 (front) still overlaps the
   AGM210MAP Q32 (back) by 0.47 mm2 of courtyard. The package bodies overlap
   by about 0.10 mm2. No legal nudge of 0.6 mm or less exists:
   - Clearing the courtyard overlap needs U18 to move up 0.58 mm, or left
     1.07 mm.
   - U18 already touches the U19 courtyard above it. Even a 0.15 mm move up
     overlaps U19, R62 and C88.
   - The J1 courtyard touches U18 on the left.
   - Q32 is a frame part.
   Two GND planes (L2, L5) sit between U18 and Q32. Fixing this means moving
   U19 or J1, which is a placement change for the owner.
6. **ESP32 behind the VTX chain.** U16 (back) sits under U19 (28.1 mm2), J1
   (4.4 mm2) and U20 (1.35 mm2). This goes back to the B4 placement. L2 and L5
   GND lie between them. Options:
   - Accept it, stitch GND densely around the 5.8 GHz chain and check
     desense on the bench.
   - Or swap U16 with a non-RF block at the next placement pass.
7. **RX feed length.** U18 RFIO to FL1 is 19.3 mm because FL1 sits at the AE1
   wire hole on the left edge, while U18 is near the right edge. A 50 ohm line
   on FR-4 at 2.4 GHz loses roughly 0.1 dB/cm, about 0.2 dB here, and the line
   crosses the board. Options:
   - Run it as CPWG on L1 over solid L2 with a GND fence.
   - Move FL1 next to U18 and run the filtered line to AE1.
   - Move the antenna exit closer to U18.
8. **USB J31 distance to the hole.** The J31 centre is 4.36 mm from the rear
   hole centre and its courtyard 1.38 mm from the hole edge. Its signal pads
   still face the hole, inside the D4.6 grommet flange keep-out. If the plug
   must sit closer (Matrix style), rotate J31 180 degrees so the leads face
   away and re-check the mating clearance rule `USB_MATING`.
9. **Pad labels (check_conventions B7): partly done.**
   - Every silk text outside the outline is deleted: 9 parked texts, `VTX`
     included. Two stray 0.29 mm silk circles about 40 mm left of the board
     are deleted too.
   - The Incutec logo LOGO1 (6.1 x 1.4 mm, F.Silkscreen) is still parked at
     (189.7, 142.2), about 61 mm right of the board, so it is not on the
     fabricated board. B3 passes because it only checks that the logo exists.
     A search of the front (0.025 mm grid, 0 and 90 degrees, 0.15 mm from
     pads, 0.20 mm from the edge and holes, 0.10 mm from other silk) found no
     legal spot, even under part bodies. Owner's call: a smaller logo, the
     back side, or room taken from the `OPENAIO WHOOP` / `REV1` texts. Do not
     plot Gerbers with it parked off the board.
   - J25 GND and J28 TX1 now have aligned 0.8 mm labels.
   - Six pads on the hole webs still have none: J21 5V, J22 BZ-, J33 GND
     (right hole) and J26 VHD, J27 GND, J29 RX1 (left hole).
   - A search tried every label position within 1 mm, at 0/45/90/135 degrees
     and the pad angle, with text widths 0.6/0.5/0.4 mm. Every position broke
     either the 0.20 mm silk-to-edge or hole rule or the 0.15 mm silk-to-pad
     rule (neighbour pads and motor headers J4/J7/J13).
   - B7 only counts labels on the pad's own side, so back silk does not help.
   - Options:
     - Shift these frame pads on their hole webs (owner's call).
     - Or relax B7 for hole-web pads in the lineup check.
10. **Tokyo font.** The silkscreen uses the KiCad font (B12 warns). The lineup
    font is Tokyo. Check that its licence allows embedding and redistribution
    in an open-hardware repo, then embed the font file (KiCad 10 embedded fonts)
    so the Gerbers do not depend on one machine.
11. **Wordmark colour.** The schematic title blocks carry the shipped wordmark
    in black + `#c89d2e`. The brand deprecations retire those colours for
    `#1a1a1e` + `#ffb700`. This is the owner's call
    (`research/LINEUP-CONVENTIONS.md` A5).
12. **Alpha stage.** The README and checks are at the planned stage. At alpha,
    run `check_conventions.py --stage alpha`. It adds the DOC_* variables, the
    alpha README shape, and the Status, Shop, Discord, Video and OSHWA badges.
    There is no shop listing or OSHWA certification yet, so those badges wait.
13. **Stale board spec.** `hardware/tools/board_spec.json` is still the P1
    spec: the pre-v4 outline (30.55 mm, 696.6 mm2, holes on 25.75 mm), a
    0.20 mm microvia land and the v3 rule areas. `check_board_setup.py --spec
    hardware/tools/board_spec.json` reports 24 of 31 keys. Without `--spec` it
    only reports and exits clean. Update the spec to the v4 outline and HDI
    via set, or retire it.

Not covered here: routing, the fabrication outputs (Gerbers, BOM, CPL), and
manufacturer quotes.
