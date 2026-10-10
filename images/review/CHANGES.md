# Review pack: schematic sync of the v3 floorplan (route step 1, 2026-10-10)

This pass compares the board against checkpoint `p2v3/route/ckpt/10_pre_sync`, which is the repo board at commit
6655d7b (floorplan v3 after the rxfix pass). The rxfix pack that was here before is backed up in that checkpoint under
`review_rxfix/`. There is no copper on either board, so the diff covers footprints only.

**Why:** routing needs the real netlist. `sync_pcb.py` read the current integrated schematic (271 symbols, 263 nets;
the SCHEMATIC_DONE marker was not set yet, and no sheet was edited). It gave every footprint its schematic path, fields
and real pad nets. All 41 temporary `/FLOORPLAN/` land nets are gone. Every part kept its placement except the moves
listed below. LOGO1 is the only board-only footprint.

**Footprints swapped by the schematic (centre and side kept):**

| Part | Change | Note |
|---|---|---|
| C23, C29, C35, C41 | 0603 22 uF to 0402 10 uF (GRM155C80J106ME11D) | ESC cell caps; pad centres move 0.275 mm inward |
| FL1 | renamed to the generic 2450FM07D0034T land | pads identical; Johanson part per the schematic |
| X1 | 2520 to 3225 (Abracon ABM8-272-T3, RP2350 DS Table 629) | +0.7 x 0.5 mm; needed a new site (below) |

The swapped footprints got back their D75 `Function` field on Fab, and their references are hidden as before.

**Moved to fit the 3225 crystal (check_spacing at 0.20 mm body to body: 0 / 0 / 0):**

| Part | Move | Reason |
|---|---|---|
| X1 | centre (117.30, 107.20) to (117.55, 107.45) | 3.3 x 2.6 mm extent between U10 (0.20), C48/U11 (0.20) and C103 (0.20) |
| C42 (XIN load) | to (116.35, 109.15) | new row under X1 pad 1, 0.35 mm above J1 and outside RF_VTX_UFL |
| R40 (XOUT series) | to (117.45, 109.15), rot 180 | same row; its XOUT_X pad faces C43 |
| C43 (XOUT_X load) | to (118.55, 109.15), rot 0 | no room beside pad 3 any more |
| C103, C104 | +0.05 mm in x | 0.20 mm from the wider X1 |
| LOGO1 | +0.02 mm in x | keeps C103/C104 at 0.20 mm |
| J3 (battery -) | +0.085 mm in y | J2 (+BATT_IN) to J3 (GND) PTH copper 0.32 to 0.405 mm (NextPCB 0.40 rule; it showed once the pads had nets) |

X1 is still on the east side of U10, with XIN/XOUT on U10's south pins 21/22. That is floorplan critique MAJOR #9, and
it is still open. Its fix (crystal into the band under U10) needs the HD pads J26-J29 moved about 0.4 mm down and a new
place for their VHD/GND/TX1/RX1 labels, so it is left to the routing/placement loop.

**Rules (`setup_board.py`, re-applied; check_rules: parsed; selftest 72 pass (66 before, +6 real-name cases), 3 old failures unchanged):**
- `SPI0 3 mm from the RX antenna hole` now also matches `*SPI0_*`. This was the P4 ruling. The schematic names the bus
  /SPI0_MISO, /SPI0_MOSI and /SPI0_SCK, and the old `*SPI0.*` pattern matched none of them.
- `In2 and In3: no gyro, VTX control or Kelvin nets` had the same defect. It now also matches `*SPI1_*`, `*VTX_SPI_*`
  and `*/U19_SPI*`.
- New `D21 Analog X2SON land gaps (U14, U15)`: clearance 0.09 between pads inside the X2SON footprints of U14
  (SN74LVC1G3157, land gap 0.10) and U15 (TLV7031, 0.11). Without it the Analog class clearance (0.15) flagged 5
  pad pairs inside the manufacturer lands.
- New selftest cases cover the real net names. The 3 failing cases (VTX chain x2, SH1.0/0201) failed the same way on the
  pre-sync script.

**Checks on the repo board (`kicad-cli pcb drc --schematic-parity --refill-zones`):**

| Check | Result |
|---|---|
| Errors other than unconnected | 1: `shorting_items` U20 pad 1 (NU) / pad 21 (GND), schematic side, see below |
| Unconnected | 690 (pcbnew count; kicad-cli caps the list at 499); no copper yet |
| Parity | 0 errors, 22 warnings (`footprint_filters_mismatch`, schematic side, see below) |
| Warnings | 9 solder_mask_bridge (U10 QFN corner pairs, U24 CSP, U20 pin 1/EP), 2 lib_footprint_mismatch (R67, J33) |
| Other checks | check_spacing 0 / 0 / 0; sync_pcb re-run: 0 changes; setup_board --check: up to date |

**Needs a schematic edit (blocked until SCHEMATIC_DONE; no sheet was touched):**
1. **U20 SE5004L pin 1 (NU) to GND.** The land follows SE5004L DS Fig. 5: pin 1 sits inside the ground metal (pad 21),
   and the footprint description says "tie it to GND". The schematic leaves pin 1 open, so DRC reports a short.
2. **Symbol footprint filters (22 parity warnings).** The stock filters do not match the project footprints:
   - Device:D_Zener (D1) and Device:D (D2): `D_*`
   - Device:L (L1): `L_*`
   - Device:R_Shunt (R1): `R_*Shunt*`
   - Connector_Generic:Conn_01x01 (J2, J3, J16-J29, J33): `Connector*:*_1x??_*`
   - lib:TPD2EUSB30DRTR (D7): `*DRT*SOT*9X3*`, against the footprint `TI_SOT-9X3-3_DRT`

   The fix is to clear or extend the filters on these symbols.
