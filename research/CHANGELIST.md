# Schematic changelist (review 2026-10-19)

Open changes from Bastian's schematic review and an RTC6705 datasheet check (RTC6705-DST-001 v0.2, Sep 2007). Each item was verified against the netlist exported from the schematic on 2026-10-19. Tick an item when it lands on `main` and remove the list once it is empty.

Owner: **script** = edited with a full S-expression parser, then proved by ERC and a netlist diff. **Stan** = GUI redraw or layout work.

## Electrical

| # | Change | Why | Owner | Layout impact |
| --- | --- | --- | --- | --- |
| [ ] E1 | U19 pin 26 (REG1D8, video 1.8 V regulator output): add 100 nF 0201 (C181047) to GND | Pin 26 is unconnected today; only pin 23 (audio regulator) has C96. OpenVTX DESIGN.md also puts 100 nF on pin 26 | script (sch), Stan (place) | New 0201 next to U19 pin 26 |
| [ ] E2 | U19 pin 17 (AVDD_6.5): decide between keeping it and powering it from +3.3V_VTX with 100 nF | Today pin 17 goes through R90 3.3k + C136 1 uF to GND, with no DC feed. The datasheet lists pin 17 as a 3.3 V supply. Keep it only if a known-good source board does the same, and cite that board in the sheet note | decision, then script | Possibly R90/C136 change |
| [ ] E3 | U19 pin 13 (AVDD_6): decide between leaving it NC and connecting it to +3.3V_VTX with 100 nF | The datasheet lists it as a 3.3 V supply. Audio is unused, so NC is probably harmless, but it is undocumented | decision, then script | Possibly a new 0201 |
| [ ] E4 | Current sense U1: INA186A3 to INA186A4 (gain 200), keep R2 0.5 mOhm | A3 with 0.5 mOhm is 50 mV/A, so 3.3 V full scale is 66 A. A4 gives 100 mV/A and 33 A full scale, about 2x the 16 A burst. A 1 mOhm shunt would double the drop on 1S. Check LCSC stock of INA186A4IDCKR first | script | None (same SC-70-6) |
| [ ] E5 | Remove D11 (+3.3V to +5V bypass across U4) | +5V carries 20 uF against 4.7 uF on +3.3V, so +5V cannot collapse first except in a hard short | script (sch), Stan (pcb) | Footprint removed |
| [ ] E6 | Optional: tie U19 pin 1 (SPI_SE) to +3.3V_VTX | Floating works (internal pull-up, datasheet note 1); a wire removes the dependency | script | Short track |

## Labels, notes and consistency

| # | Change | Why | Owner |
| --- | --- | --- | --- |
| [ ] L1 | ESC sheet: swap the PHASE_B and PHASE_C labels so each PHASE_x is the bridge its X_PWM drives | No electrical change. Bluejay `Layouts/BB51/A.inc` puts B_Mux on P0.1 and C_Mux on P0.2, so the C-driven bridge is sensed on BEMF_C (correct), but its net is named PHASE_B | script |
| [ ] L2 | ESC sheet notes: delete "22R series damps DShot edges" and the U24 level-translator text box | Both are stale copies from OpenAIO. The board has 1k series (R69/R70/R57/R67) and no U24. The 1k limits back-feed into the unpowered EFM8 on USB-only power to about 2.7 mA per pin | script |
| [ ] L3 | ESC sheet note: state that COM drives the high-side P-FET (G2, active low) and PWM drives the low-side N-FET (G1, active high), per Bluejay layout A | Answers the A_COM question in the review | script |
| [ ] L4 | Delete the redundant `RTX` label on the ESC DSHOT net | ERC multiple_net_names (RTX and DSHOT) | script |
| [ ] L5 | MOTOR1-4_FC hierarchical labels and sheet pins: change input to bidirectional | Bidirectional DShot; the ESC side is already bidirectional | script |
| [ ] L6 | RP2350A sheet: replace the global `SBUS` label on GPIO29 with a no-connect flag | Single-pin net (ERC isolated_pin_label); the sheet note says GPIO28/29 are NC | script |
| [ ] L7 | RX sheet: keep one VTX_AMP_PWM hierarchical label on U16 pin 13, delete the duplicate stub and its local label | The same name appears three times on the sheet | script |
| [ ] L8 | Blackbox flash U14 EP (pin 9): join it to pin 4 under one GND symbol, or mark it NC | Two overlapping GND symbols; the symbol description says EP has no electrical role | script |
| [ ] L9 | Rename net HD_EN to VTX_EN, or explain it in the note | It switches the analog VTX supply (U21 EN), not an HD VTX | script |
| [ ] L10 | VTX sheet note: "C108 at VCO supply" should read "C108 at U21 output" | Wrong reference | script |
| [ ] L11 | Remove the RF_WIFI / RF_WIFI_ANT dual name on the RX sheet | ERC multiple_net_names | script |

## Visual redraw (Stan, GUI)

| # | Sheet | Change |
| --- | --- | --- |
| [ ] V1 | POWER | Draw the U2 FB pin wire to the R4/R5 node. It is connected by label only, so it looks open |
| [ ] V2 | POWER | Redraw the 5 V diode-OR (D9, D10, C12, C128) as one block |
| [ ] V3 | PADS | J35 HD VTX: separate the overlapping +5V_BST and GND symbols |
| [ ] V4 | RX | Shrink the ESP32 box, drop the empty NOTES box |
| [ ] V5 | RP2350A | Content fills the top-left third of an A2 sheet with 6-point notes; resize the sheet or rearrange |
| [ ] V6 | all | Fix about 20 off-grid wire and pin endpoints (ERC endpoint_off_grid) |

## Kept as is (answered in review)

| Remark | Answer |
| --- | --- |
| Ferrite bead FB1 | Correct use: it isolates camera noise on +5V_CAM (120 Ohm at 100 MHz, 0.9 A, then C15 10 uF). Fit 0 Ohm if it misbehaves |
| PHASE_B to BEMF_C | Intentional per Bluejay layout A; label cleanup in L1 |
| A_COM polarity | Matches layout A: PWM active high on N, COM active low on P |
| 1k DShot series | Kept: about 10 ns RC at DShot600, protects both domains |
| TI parts cost | Not priced yet; run an LCSC comparison before swapping |
| RTC6705 PAOUT2 NC | Intentional: PAOUT1 (+2 dBm) drives the SE5004L, under its 6 dBm input limit |

## Bench checks the datasheets cannot answer

| Check | Reason |
| --- | --- |
| Video deviation | VT_Mod sees about 185 mVpp after R58/R59. The datasheet gives no deviation figure; trim R59 on a spectrum analyser |
| PLL lock time and video tilt | The loop filter (R63, C106, R64, C107) is not in the datasheet |
| Pout and harmonics against VTX_AMP_PWM duty | 2 dBm into 32 dB of gain saturates the PA; FL2 is the only harmonic filter |
| PA at end of pack | SE5004L VCC minimum is 3.0 V, and the PA runs from +BATT |
