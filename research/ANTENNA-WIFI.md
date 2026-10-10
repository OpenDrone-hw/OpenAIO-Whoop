# ELRS Wi-Fi antenna for the ESP32-PICO-V3 (D58, D90)

Date: 2026-10-10. Scope: the 2.4 GHz antenna that the ESP32-PICO-V3 (U16) uses in ELRS Wi-Fi mode. That mode is only used on the bench, for configuration and firmware updates. The SX1281 RC link keeps the AE1 wire antenna through FL1.

Tags: **V** = read from a primary source (datasheet, repo file, Gerber, owner photo measurement). **S** = secondary source (shop listing, distributor, search summary). **I** = inferred (engineering estimate, stated as such).

## 1. Answer in short

- **What BetaFPV does (Matrix 1S 5IN1 II):** the Wi-Fi antenna is a white ceramic chip of about **1.6 x 0.9 mm** (1608 class). It sits **mid-board**, 1.2 mm from the ESP8285 package edge, next to the vertical USB plug. Small passives surround it, and there is no edge clearance. BetaFPV's part is not physically smaller than ours. It is **larger** than the 1.0 x 0.5 mm Johanson. What makes it "smaller" on the board is that BetaFPV gives it **no clearance area**. (I: measured on the owner's photo; part identity not confirmed by a marking.)
- **Why that works:** config Wi-Fi has a huge link margin. ESP32 transmits +19.5 dBm, and its sensitivity is -93 dBm at 6 Mbps and -98 dBm at 1 Mbps. Even an antenna 25-30 dB worse than the datasheet figure still reaches a few metres indoors (§5).
- **Recommendation:** keep the **Johanson 2450AT07A0100001T** (1.0 x 0.5 x 0.37 mm). Digi-Key is **active with 213,248 in stock** (2026-10-10), so NextPCB can source it.
  - Move it **next to U16 pin 2 (LNA_IN), on the bottom, Matrix style**, with a feed of 2 mm or less. A board edge is optional.
  - Replace the 5.0 x 3.2 mm all-layer edge keep-out with the **D90 void**: about 2.6 x 1.6 mm on B.Cu, In4 and In3, plus 1.6 x 1.1 mm (body only) on In2 and In1. **F.Cu stays free for parts and ICs.**
  - Use a 0201 pi match at the antenna, tuned on the bench.
  - Expected config range: **about 4-10 m indoors**, at least 1-3 m in the worst case. That meets the "a few metres" target.
- **Not recommended:** sharing the SX1281 antenna through an RF switch or a passive tap. Stock ELRS has no control line for it, it costs dB on the RC link, and the SX1281 port gets exposed to +19.5 dBm. On this floorplan it would also need a 17 mm feed (§4.3).

## 2. What competitors use for Wi-Fi (task 1)

| Product | Wi-Fi antenna | Evidence | Tag |
|---|---|---|---|
| BetaFPV Matrix 1S 5IN1 II (ESP8285 + SX1281) | White 1608-class ceramic chip with a dark centre mark, about 0.93 x 1.63 mm. Centre about (-0.55, -5.13) mm in the board frame, 1.2 mm from the ESP8285 package edge (ESP centre (-1.70, -9.66)). Next to the vertical SH1.0 USB housing, mid-board, no edge. No copper-free window is visible on the top layer (black mask); inner layers cannot be seen. Two or three 0201 parts sit between it and the ESP (a pi match, I). | Owner photo `matrix_top_owner.png`, rectified at 80 px/mm by the matrix_re run (frame.json, 25.5 mm hole pitch). Measured 74 x 130 px, ±0.1 mm. Analysis only; no image was copied. | I |
| Matrix firmware target | "BETAFPV 2.4GHz AIO RX" uses `Generic 2400.json`: no `ant_ctrl`, no `power_txen` or `power_rxen`, `power_values [13]` dBm. So there is no antenna switch or FEM, and the Wi-Fi path is separate from the LoRa path. | [ExpressLRS/targets targets.json](https://github.com/ExpressLRS/targets/blob/master/targets.json), [RX/Generic 2400.json](https://github.com/ExpressLRS/targets/blob/master/RX/Generic%202400.json) | V |
| Matrix product page | Says nothing about Wi-Fi or its antenna. Lists "Serial ELRS 2.4GHz" V3.4.3 and a USB port. | [BetaFPV product page](https://betafpv.com/collections/flight-controllers/products/matrix-1s-5in1-ii-brushless-flight-controller), [NextFPV listing](https://www.nextfpv.com/products/betafpv-matrix-1s-brushless-flight-controller-5in1-ii) | S |
| BetaFPV ELRS Lite / Nano RX, Happymodel EP1/EP2, RadioMaster RP1/RP2 | All use the ESP8285 with `Generic 2400.json` (Lite, EP1/EP2, RP1/RP2) or `Generic 2400 PA.json` (BetaFPV Nano). Neither layout has a Wi-Fi/LoRa antenna-share line. Their Wi-Fi antenna design (chip, trace or none) was **not determined**: no teardown photos were obtained, and fccid.io and fcc.report return HTTP 403 to this agent. EP2, RP2 and the Lite use a ceramic chip for the 2.4 GHz **LoRa** link. | [targets.json](https://github.com/ExpressLRS/targets/blob/master/targets.json); [BetaFPV ELRS Lite](https://betafpv.com/collections/rx/products/elrs-lite-receiver); [getfpv EP2](https://www.getfpv.com/radios/receivers/happymodel-expresslrs-nano-2-4ghz-ep2-rx.html); [fpvracing RP2](https://fpvracing.ch/en/radio-system/3575-radiomaster-rp2-elrs-24ghz-nano-receiver.html) | V (targets) / S (antennas) / unknown (Wi-Fi antenna) |
| ELRS DIY Nano RX v1.0 / v1.1 | ESP-01F `ANT` pin **unconnected**, so there is no Wi-Fi antenna. | [RX_Nano schematic image](https://github.com/ExpressLRS/ExpressLRS-Hardware/blob/master/PCB/2400MHz/RX_Nano/img/schematic.PNG) | V |
| ELRS DIY Nano RX v1.2, Nano Ceramic v1.1C, Nano Diversity v1.1D | Changelog says "Adds WiFi antenna". In the v1.2 Gerber, a thin trace runs from the module's `ANT` pad along the board edge: a **PCB trace stub**. | [RX_Nano README](https://github.com/ExpressLRS/ExpressLRS-Hardware/tree/master/PCB/2400MHz/RX_Nano) (V). Gerber `Gerber_Nano_RX_SX1280_SMD_v1.2.zip` rendered locally (I: trace geometry) | V / I |
| ELRS DIY Nano Diversity | Its pSemi PE4259 RF switch selects between two **SX1280** antennas. It does not share an antenna with Wi-Fi. | [RX_Nano_Diversity README](https://github.com/ExpressLRS/ExpressLRS-Hardware/tree/master/PCB/2400MHz/RX_Nano_Diversity) | V |
| ELRS hardware field set | Of all RX layouts, 8 use `ant_ctrl` (LoRa diversity) and 1 uses `radio_rfsw_ctrl` (LR1121). **No layout has a field that routes the LoRa antenna to the ESP's Wi-Fi.** | grep over [ExpressLRS/targets RX/](https://github.com/ExpressLRS/targets/tree/master/RX), shallow clone 2026-10-10 | V |

Conclusion (I): production whoop RXs and AIOs give Wi-Fi either its own tiny chip antenna placed wherever there is room (Matrix), or a trace stub (DIY Nano). In both, the antenna sits close to the ESP and gets little or no clearance. No ELRS target shares the LoRa antenna with Wi-Fi.

## 3. The board today (repo `hardware/OpenAIO-Whoop.kicad_pcb`, read 2026-10-10)

- AE2 2450AT07A0100001T: B side, (119.3, 101.15), top edge. Its rule area `WIFI_ANT_KO` (115.25..120.25 x 100.0..103.2) blocks copper on all layers.
- U16 ESP32-PICO-V3: B side, (112.6, 113.7). LNA_IN (pin 2, net `/RX/RF_WIFI`) is at (115.97, 111.45), **about 10.5 mm from the AE2 feed**. FLOORPLAN.md §Open item 10 records that the feed (13.5-15.6 mm) runs past the RTC6705 (U19, (119.8, 108.1)). It also says the pi match is split across both sides: R88 is on F, C132/C133 on B.
- Stackup, measured from B.Cu: In4 GND at **0.077 mm**, In3 +BATT plane at 0.39 mm, In2 signals at 0.51 mm, In1 GND at 0.83 mm, F.Cu at 0.93 mm (εr 4.2).
- Boost U2 TPS61022 (106.9, 117.5) and L1 (109.3, 119.8), both B. They are about 9-10 mm from LNA_IN.

## 4. Options (task 2)

The antenna body is ≤ 1.0 x 0.5 mm for every chip option. "Area" means what the option takes from the board (land + void). Efficiency figures are **I** (engineering estimates) unless tagged otherwise.

### 4.1 Chip antennas at or below 1.0 x 0.5 mm

| Part | Size (mm) | Maker data | Maker clearance | Sourcing | Tag |
|---|---|---|---|---|---|
| **Johanson 2450AT07A0100001T** (legacy 2450AT07A0100T) | 1.00 x 0.50 x 0.37 max | Peak gain 1.0 dBi, average -1.5 dBi (XZ total), return loss 6.5 dB min, 50 Ω, 2 W. Pins: 1 and 4 feed, 2 and 3 GND. Datasheet recommends pi pads. | No-ground area 5 x 3 mm at the board edge on all layers (EVB 40 x 20 mm) | Digi-Key **active, 213,248 in stock**, USD 0.57 @1, 0.33 @5k, 18 wk lead (2026-10-10) | V ([datasheet](https://www.johansontechnology.com/), local copy p2v3/wifi_dl/2450AT07A0100.pdf, Ver 3.1; [Digi-Key](https://www.digikey.com/en/products/result?keywords=2450AT07A0100001T)) |
| Pulse ANT1005LL14R2400A | 1.00 x 0.50 x 0.37 max | Peak gain 2.21 dBi, VSWR 3.0 max, bandwidth 120 MHz, 1 W. Pins: P1 and P2 GND, P3 and P4 feed. | Eval-board drawing only, about 5 x 3 mm (prior survey) | Not checked today | V (local datasheet p2v3/wifi_dl/pulse_ANT1005.pdf) |
| Abracon AANI-CH-0070 | 1.0 x 0.5 x 0.4 | Not read | 5 x 3 mm (distributor summary) | Not checked | S ([novapart / Farnell](https://novapart.co/datasheet/farnell:4425994/)) |
| Antenova Weii | 1.0 x 0.5 x 0.5 | Antenova calls it its smallest so far | Large reference board | Not checked | S ([Mouser Weii page](https://www.mouser.fr/new/antenova/antenova-weii)) |

Nothing smaller than 1005 (0402) was found: no 0201 or 0.8 x 0.4 mm 2.4 GHz chip antenna. **The 1005 parts are the floor (S).** The Pulse part is **not** a drop-in for the Johanson land, because the feed and GND pin positions differ. Treat it as a second source only after drawing its own land.

How these parts radiate (I): each is a ground-clearance type. The chip is a loaded resonator that excites currents on the **edge of the ground plane**, and the radiation leaves through the copper-free area. Ground directly under the chip, such as In4 at 0.077 mm, turns it into a capacitor to ground with a tiny radiation resistance. A copper void is therefore needed **under the body and on the adjacent layers**. It is not needed through the whole stack or on the far outer layer.

### 4.2 Placement and copper variants for the chosen chip (efficiency vs. area)

| Variant | Area taken | Efficiency / average gain (I) | Notes |
|---|---|---|---|
| A. Today: maker 5.0 x 3.2 mm clearance, all layers, top edge | 16 mm² on all six layers | -3 to -5 dBi on a 26 mm board (datasheet -1.5 dBi on 40 x 20 EVB) | Conflicts with D90 and with the routing limit; the 10-15 mm feed crosses the VTX area (D75 finding) |
| B. D90 void (§6) at a board edge, feed ≤ 4 mm | about 4.2 mm² on B/In4/In3, 1.8 mm² on In2/In1, F free | -8 to -15 dBi | Best D90 choice if the v4 floorplan puts LNA_IN within about 4 mm of an edge |
| **C. D90 void (§6) mid-board next to LNA_IN (Matrix style)** | **same as B; no edge needed, feed ≤ 2 mm** | **-12 to -25 dBi** | **Recommended:** smallest total cost, no long RF line, no edge strip |
| D. Chip over unbroken ground (no void at all) | land only, about 1.5 mm² | -25 to -40 dBi, detuned; the pi cannot recover a near-zero radiation resistance | Most PA power is reflected. Espressif gives no PA load-mismatch (VSWR) ruggedness figure (unknown). Avoid |
| E. PCB trace stub instead of a chip (DIY Nano style) | 4-6 mm x 0.15 mm trace plus a similar void, about 5 x 1.2 mm | -15 to -30 dBi, tuning hard to predict | No BOM part, but no smaller than C, and range spread is larger |
| F. No antenna: LNA_IN into a 0201 load (D25) or open | 0.3 mm² | Leakage only, about 1 m or less | D25 used this. It fails the "Wi-Fi works" intent of D58 |

### 4.3 Sharing the SX1281 antenna (AE1 wire through FL1)

| Variant | Area | Wi-Fi | Cost to the ELRS link | Showstoppers |
|---|---|---|---|---|
| G. SPDT RF switch (e.g. pSemi PE4259 as in the ELRS DIY diversity RX; smaller 0.7 x 1.1 mm Infineon-class SPDTs exist) plus 2 DC-block caps and a control line | about 3 mm² + routing | Good: the wire antenna is about 0 to +2 dBi | 0.3-0.5 dB insertion loss on the **critical** RC link, permanently (I) | Stock ELRS has **no** layout field to switch an antenna to Wi-Fi (`ant_ctrl` is LoRa diversity and toggles in flight, V). If the switch is left in the wrong state, the ESP's +19.5 dBm hits the SX1281 RFIO. AE1 (100.9, 120.7, F) is about 17 mm from LNA_IN, so a long RF line crosses the board |
| H. Passive tap: about 0.3 pF (≈217 Ω at 2.44 GHz) from the ESP feed onto the SX1281 antenna line, no switch | 1 x 0201 + RF line | About -7.5 dB mismatch, then the wire antenna: works (I) | About 0.2-0.3 dB if the idle ESP port absorbs (I) | The sleeping SX1281 sees roughly +10 dBm. Its tolerance to that is not in what we read (unknown). Same 17 mm line. Neither datasheet supports this |

Verdict: **reject G and H.** Each costs more area or risk than option C, it degrades the link the quad depends on, and G needs firmware that ELRS does not have.

## 5. Range budget (why "small and poor" is good enough)

Inputs:
- ESP32 Table 5-6 (V, [ESP32 Series Datasheet v5.3](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)): TX 19.5 dBm in 11b mode. Sensitivity -98 dBm (11b 1 Mbps), -93 dBm (11g 6 Mbps), -73 dBm (11n MCS7).
- ELRS Wi-Fi sets `WIFI_POWER_19_5dBm`. V, read by the D58 agent in ELRS `src/lib/WIFI/devWIFI.cpp` at commit 8c51826.
- Phone: about +15 dBm EIRP, sensitivity about -90 dBm (S, typical).
- Margin for hand, frame, battery and indoor fading: 20 dB (assumption).

The phone-to-ESP uplink is the limit. Budget = 15 + G + 93 - 20 dB. Path loss at 2.44 GHz is 40.2 dB at 1 m, plus 20·log(d) in free space or 30·log(d) indoors.

| Average antenna gain G | Free space, 6 Mbps | Indoor (n = 3), 6 Mbps | Indoor (n = 3), 1 Mbps |
|---|---|---|---|
| -1.5 dBi (datasheet EVB) | > 100 m | 35 m | 51 m |
| -10 dBi (variant B) | 78 m | 18 m | 27 m |
| -20 dBi (variant C, mid estimate) | 25 m | 8 m | 12 m |
| -30 dBi (detuned or blocked) | 8 m | 4 m | 6 m |

**Expected config range for the recommendation: about 4-10 m indoors in practice, at least 1-3 m in the worst case (I).** This meets the owner's "a few metres". Firmware upload drops to the lower OFDM/11b rates on its own, so throughput stays usable.

## 6. Recommendation (task 3)

### 6.1 Part

- **AE2 = Johanson Technology 2450AT07A0100001T** (1.00 x 0.50 x 0.37 mm, 2.4-2.5 GHz). The MPN is already in bom_plan, the library and the schematic. Genuine part, sourceable at Digi-Key, so NextPCB turnkey can buy it (V).
- Second source: Pulse ANT1005LL14R2400A, with its own land (pin map differs).

### 6.2 Placement

1. Put AE2 on **B.Cu (same side as U16)** so its feed end is **≤ 2 mm from U16 pin 2 (LNA_IN)**. The feed is one 0.15 mm line on B.Cu over In4 (h 0.077 mm, about 50.7 Ω computed), with **no via**.
   - If the v4 floorplan (D91 outline) puts the LNA_IN corner of U16 within about 4 mm of a board edge, place the chip at that edge with its open end facing outward (variant B, about 5-10 dB better).
   - Otherwise place it mid-board like the Matrix (variant C).
2. Orientation: the long axis is parallel to the U16 edge. The GND end ties into the void edge; the free side faces away from the large copper (battery/ESC pours).
3. D75 coexistence: keep at least 3 mm from the RTC6705 / PA / U.FL chain and the SX1281 RF path. Keep at least 3 mm from the boost switch node and inductor (§6.5). Wi-Fi is bench-only.

### 6.3 Land and footprint

- Land: the Johanson 1005 4-pad land as used in the current footprint (pads 1/4 feed, 2/3 GND). New library footprint `ANT-SMD_4P-L1.0-W0.5_Johanson_2450AT07A0100_D90Void` replaces `..._Edge5.0x3.2`.
  - Drop the 5.0 x 3.2 edge strip and its "strip copper without paste" pad.
  - Draw the voids below as rule areas inside the footprint so they move with the part. KiCad 10 footprint rule areas are per-layer.
  - Courtyard: body + 0.10 mm, as the house rule.

### 6.4 D90 copper rules ("minimal copper, ICs on the other side")

| Layer | Distance from chip | Rule |
|---|---|---|
| B.Cu (antenna side) | 0 | **Void V1 = 2.6 x 1.6 mm**, covering the chip land plus about 0.5 mm on the feed side and about 1.0 mm past the free (non-feed) end. Allowed inside: only the AE2 pads, the feed and the pi parts. No pour, no other part, no other trace |
| In4 GND | 0.077 mm | Same V1 void (mandatory: at 77 µm a plane kills the antenna). Elsewhere solid; it is the feed reference up to the void edge |
| In3 +BATT plane | 0.39 mm | Same V1 void. Do not place it inside a battery-to-cell corridor (D85: the plane stays one island). A 2.6 x 1.6 mm hole costs no current capacity outside the corridors |
| In2 signals | 0.51 mm | **Body void V2 = 1.6 x 1.1 mm** (chip land + 0.3 mm): no trace crosses under the chip. Traces may cross the rest of V1 |
| In1 GND | 0.83 mm | V2 body void (preferred, worth an estimated 2-4 dB, I). Elsewhere solid. Keep it solid instead only if an F-side signal must cross V2's projection, and accept the loss |
| F.Cu (opposite side) | 0.93 mm | **Parts and ICs allowed** (D90). Inside V2's projection: no pour, no exposed pad or EP via field, no large GND pad. Small signal/passive pads are fine. Pull the F GND pour back to V2 |

Net-aware DRU for this, per the commons lesson: one named rule area per void with `disallow track via zone`, scoped by `A.NetName != '/RX/RF_WIFI_ANT' && A.NetName != '/RX/RF_WIFI'`, and a footprint exemption for AE2 and the pi parts. Log it as a D21 scoped exception (e.g. `D90 wifi_antenna_void`). The existing `WIFI_ANT_KO` all-layer rule area goes.

### 6.5 Antenna ground return

- **Antenna return.** The chip's GND pads (2/3) get **two filled 0.35/0.20 vias-in-pad to In4 and In1**, at the void edge. That puts the antenna's image current on one short ground edge. The two pi shunt caps return to the **same** via pair, not to a separate via several mm away.
- **Stitching fence.** Run In4-to-In1 GND vias at **≤ 2 mm pitch** around V1 on every side except the free end. The pitch is under λ/20 in FR-4 (λ_FR4 ≈ 60 mm). This makes the inner planes one ground edge rather than a cavity, and keeps U16 and boost return currents out of the antenna void. Use D70 tented vias under part bodies where free sites are scarce.
- **Never let the void interrupt a return path.** In particular, the 5 V boost (U2/L1) must keep its **unbroken In4/In1 ground under the hot loop and its direct return to the battery GND** (D92). Place the void at least 3 mm from the boost loop and outside the boost-to-battery return corridor. On the current board, U16 LNA_IN is about 9-10 mm from U2/L1: compatible.
- **The feed's reference** (In4) stays continuous from U16 pin 2 to the void edge. Do not route an In4 jumper (D85 ≤ 3 mm jumps) under the feed.

### 6.6 Matching network

- The ESP32-PICO-V3 already has its internal CLC match to 50 Ω (datasheet Fig. 8, read by the D58 agent). The external pi is for the antenna only.
- Pi = shunt C / series / shunt C in **0201, all on B, within 1 mm of the AE2 feed pad**. Keep the existing refs:
  - C133 on the SiP side, R88 series, C132 on the antenna side.
  - **Move R88 from F to B.** It sits on F today and forces two via transitions in the RF line.
- Population for the prototype:
  - Series 0R (RC0201FR-070RL class, existing line).
  - Shunts DNP, footprints kept. The current 1.2 pF values are placeholders: Johanson says the match "will vary depending on PCB design".
- Bench tuning (V-test):
  - Use a VNA through a pigtail at the series position, with the battery lead, AE1 wire and frame in place.
  - Target |S11| ≤ -6.5 dB across 2.412-2.472 GHz (the datasheet return-loss spec).
  - Then measure phone RSSI and run a web-UI firmware upload at 1, 3 and 5 m.
  - Pass: upload completes at 3 m.

### 6.7 Net area result vs today

- B/In4/In3: 4.2 mm² instead of 16 mm².
- In2/In1: 1.8 mm² instead of 16 mm².
- F: 0 instead of 16 mm².
- Plus the 10-15 mm RF feed line (and its fence vias) disappears, which frees routing channels on the board whose limit is via sites (D88, D89).

## 7. Fallbacks

1. Bench range under 3 m: first tune the shunts. Then grow V1 to 3.0 x 2.0 mm, void In1/In2 fully under V1, or move AE2 to the nearest edge (variant B).
2. Supply problem with the Johanson part: Pulse ANT1005LL14R2400A on its own land.
3. Variant C proves too weak and there is no room for B: a trace stub (variant E) in the same void. Not better on area; keep it as a last resort.

## 8. Open items / not verified

- Matrix antenna identity, and whether its inner layers are voided under it: unknown. Only the outer-layer photo was used, and no marking was readable (I).
- Wi-Fi antenna design of EP1/EP2, RP1/RP2 and the BetaFPV Lite/Nano: unknown (no teardown; FCC sites blocked).
- The efficiency numbers in §4.2 are estimates. The bench V-test in §6.6 decides.
- SX1281 RFIO tolerance to incoming RF while asleep: unknown (only matters for rejected option H).

## Sources

- Owner photo `matrix_re/matrix_top_owner.png` and the matrix_re frame/rectification (analysis only, not copied). V/I
- ExpressLRS hardware repo, RX_Nano / RX_Nano_Ceramic / RX_Nano_Diversity READMEs, `img/schematic.PNG`, Gerber v1.2: https://github.com/ExpressLRS/ExpressLRS-Hardware/tree/master/PCB/2400MHz. V
- ExpressLRS targets repo, `targets.json`, `RX/Generic 2400.json`, `RX/Generic 2400 Diversity PA.json`: https://github.com/ExpressLRS/targets. V
- Johanson 2450AT07A0100 detail specification Ver 3.1 (10/12/2020): https://www.johansontechnology.com/ (local copy `scratchpad/p2v3/wifi_dl/2450AT07A0100.pdf`). V
- Digi-Key 2450AT07A0100001T stock and price, 2026-10-10: https://www.digikey.com/en/products/result?keywords=2450AT07A0100001T. V
- Pulse ANT1005LL14R2400A datasheet (local copy `scratchpad/p2v3/wifi_dl/pulse_ANT1005.pdf`). V
- Abracon AANI-CH-0070 summary: https://novapart.co/datasheet/farnell:4425994/. S
- Antenova Weii: https://www.mouser.fr/new/antenova/antenova-weii. S
- ESP32 Series Datasheet v5.3, Table 5-6: https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf (local copy `scratchpad/dl_esp32/esp32.pdf`). V
- BetaFPV Matrix 1S 5IN1 II: https://betafpv.com/collections/flight-controllers/products/matrix-1s-5in1-ii-brushless-flight-controller and https://www.nextfpv.com/products/betafpv-matrix-1s-brushless-flight-controller-5in1-ii. S
- BetaFPV ELRS Lite: https://betafpv.com/collections/rx/products/elrs-lite-receiver; Happymodel EP2: https://www.getfpv.com/radios/receivers/happymodel-expresslrs-nano-2-4ghz-ep2-rx.html; RadioMaster RP2: https://fpvracing.ch/en/radio-system/3575-radiomaster-rp2-elrs-24ghz-nano-receiver.html. S
- Repo board and stackup: `hardware/OpenAIO-Whoop.kicad_pcb`, read with pcbnew 2026-10-10; `research/FLOORPLAN.md` §Open item 10; `research/DECISIONS.md` D25, D58, D75, D85, D90, D92. V


## 9. Independent check (2026-10-10) - binding over the sections above where they differ

An adversarial review found these problems; floorplan v4 applies the corrected version.

- MAJOR, ground return attribution (the relayed owner request). 'For the buck pls think about ground return' is D92. It is about the 5 V converter U2 TPS61022 + L1. The owner calls it the 'buck', but it is the 1S boost. The result labels the antenna's GND vias and fence 'the owner's point, applied here', but the owner did not ask for those. Only rule 11 touches D92 (keep the void at least 3 mm from the boost loop and out of its battery-return corridor). The boost's own ground return is not addressed anywhere: PGND, CIN-GND and COUT-GND joined on the component layer, no via in the loop, In4 unbroken under the loop, and a direct return to battery GND. The result must not be reported as answering the owner's point; that needs its own deliverable.
- MAJOR, placement conflict on the current board (pcbnew, repo board). U16 pin 2 LNA_IN (115.97, 111.45, B) is 0.5 mm from the RTC6705 U19 body (B). It sits directly under the VTX U.FL J1 (F; the bounding box overlaps). It is about 3.9 mm from the 5.8 GHz BPF FL2 and about 7.5 mm from the SE5004L PA U20. Rule 1 (antenna within 2 mm of LNA_IN, 'Matrix style') and rule 4 / D75 (at least 3 mm from the RTC6705/PA/U.FL chain) cannot both hold. The F side over V2 would also be J1's large GND tabs, which breaks the doc's own V2 rule. v4 must turn U16 so pin 2 faces away from the VTX chain, or move that chain. The doc states neither and presents mid-board as free.
- MAJOR, the antenna GND tie as written cannot be built and contradicts the datasheet. (a) The repo land is 0.20 x 0.30 mm pads at 0.30 mm pitch. A 0.35/0.20 via-in-pad does not fit in a 0.20 mm pad, and two such vias at 0.30 mm pitch break the hole-to-hole spacing. (b) V1 voids In4 and V2 voids In1 over the land, so vias in the land have no In4/In1 copper to land on. (c) The doc calls the non-feed end 'free' and runs V1 1.0 mm past it. Per Johanson DS Ver 3.1 p1/p2, pins 1/4 are feed and pins 2/3 are GND, so there is no free end. In the maker's pattern the GND row joins a ground strip at the void edge through a link of about 0.3 mm, and the void runs 4 mm sideways along the chip, not past its end. Fix: a short B.Cu link from the GND row to the void edge, two GND vias just outside V1 at that point, and the void lengthened beside the chip.
- MINOR, pi shunt return. Returning both shunts to 'the same via pair' at the antenna's GND end means a 1.5-2.5 mm path, about 1-2 nH, or about 15-30 ohm at 2.44 GHz in series with each shunt. That makes the bench tuning unpredictable. Give each shunt its own GND via at its pad, on In4 just outside V1.
- MINOR, via fence rationale and cost. The fence 'keeps return currents out of the void', but no current can flow in a void with no copper. Mid-board there is also no open 'free end' to leave unfenced. Each fence via is a through via that also lands on F (about 5-7 sites plus the GND ties). Via sites are the stated routing limit (D88), but the area claim counts F as 0 mm².
- MINOR, Matrix neighbour misidentified. The white housing beside the chip is the SH1.0 3-pin side-entry camera plug J2 (matrix_re side-esp map.json, confidence medium-high). It is not the vertical USB plug. The Matrix's vertical SH1.0 USB J5 is on the other side at the B ear, about 10 mm away.
- MINOR, 'no clearance' overclaims. Black solder mask hides copper and the inner layers are unseen. The photo supports only 'no edge or large clearance; parts 0.3-1.2 mm around it'. The far side was not checked. Mirroring the bottom map about y=x (checked against the battery and RX-antenna holes) shows EFM8 BEMF 0201s under the chip. The nearest ICs are EFM8BB51 U4 at 1.1 mm and AT7456E at 1.4 mm, beside the chip rather than under it. So the Matrix does not put an IC directly under its antenna (I). That matters for how D90's 'ICs on the other side' is read.
- MINOR, the efficiency estimate for variant C is unsupported and probably optimistic. With In1 GND at 0.83 mm and F-side IC copper at 0.93 mm, the mid-board D90 void is an antenna over ground at about λ/150. The -12 to -25 dBi estimate rests only on voiding the top 0.4 mm. -25 to -35 dBi is as plausible. The range table's arithmetic is correct (re-computed), so 4-10 m should be stated as the optimistic end, with about 2-4 m as the realistic floor. |S11| of -6.5 dB or better shows the match, not the efficiency (a lossy antenna can match well), so the 3 m upload test is the real pass gate.
- MINOR, source labels. The owner's 'a few metres' does not appear in DECISIONS.md or CONTEXT.md; D58 says only 'ELRS needs Wi-Fi, use the smallest'. The link from the Matrix to the 'BETAFPV 2.4GHz AIO RX' target has no citation. BetaFPV's Matrix 1S page names that target and says the RX updates over Wi-Fi, which is also evidence that its chip antenna works; cite it (S). '18-week lead (2026-10-10)' reads like a delivery date, but 2026-10-10 is the date the stock was checked.
- MINOR, alternatives missed. Datasheets already in p2v3/wifi_dl were left out of the table: Kyocera AVX 9005868 and 1005801 (1.00 x 0.58 x 0.35 mm, two terminals: feed plus floating, so a simpler 2-pad land and a real free end) and Abracon AANI-NI-0245 (1.0 x 0.5 x 0.5 mm, 6 x 4 mm clearance). None is smaller than 1005, so '1005 is the floor' still stands (S). A simpler option is also missed: by the doc's own range logic ('efficiency hardly matters'), one series 0201 plus one DNP shunt pad is enough, rather than a full 3-part pi with a VNA step.
- MINOR, datasheet revision. The land spec notes a Johanson Rev 4.0 (2024). The doc uses Ver 3.1 (2020) for the clearance and specs without checking the newer revision.
- Verified correct: Johanson 1.00 ± 0.10 x 0.50 ± 0.10 x 0.37 max mm, pins 1/4 feed and 2/3 GND, 5 x 3 mm no-ground area on top and bottom, pi recommended. Digi-Key: Active, 213,248 in stock, USD 0.57 @1 and 0.32999 @5k, 18 weeks. ESP32 datasheet: 19.5 dBm in 11b, -98 dBm at 1 Mbps, -93 dBm at 6 Mbps. Targets: BETAFPV 2.4GHz AIO RX uses Generic 2400.json (power_values [13], no ant_ctrl); 8 RX layouts use ant_ctrl and 1 uses radio_rfsw_ctrl (Radiomaster ER). Pulse ANT1005: P1/P2 GND, P3/P4 feed. Stackup: In4 0.077 mm, In3 0.395, In2 0.515, In1 0.833, F 0.927. AE2, U16 pin 2, R88 on F, C132/C133 on B, and the WIFI_ANT_KO coordinates all match the board. The 10.5 mm feed distance is right. The boost is actually about 10.7-11.7 mm away, not 9-10. Matrix chip about 0.93 x 1.63 mm, 1.2 mm from the ESP8285, consistent with the map. The source is about 20 px/mm, upsampled to 80, so ±0.1 mm equals about ±2 native px.

Corrected summary:

Recommendation: keep the Johanson 2450AT07A0100001T (1.00 ± 0.10 x 0.50 ± 0.10 x 0.37 max mm; pins 1/4 feed, 2/3 GND; Digi-Key active, 213,248 in stock, USD 0.57 @1 / 0.33 @5k, 18-week factory lead, checked 2026-10-10). Put it beside U16 LNA_IN on B with a feed of 2 mm or less and no vias, under a D90 partial void instead of the 5.0 x 3.2 mm all-layer keep-out. This works only once the v4 floorplan moves the RF corner. Today LNA_IN is 0.5 mm from RTC6705 U19 and directly under the VTX U.FL J1, so 'at most 2 mm from LNA_IN' and the D75 rule of at least 3 mm from the RTC6705/PA/U.FL/BPF chain cannot both hold. v4 must turn U16 so pin 2 faces away from the VTX chain (ideally toward an edge, which is variant B and about 5-10 dB better), or move the chain.

Copper (D90):
- V1 void on B, In4 (77 µm under the chip, so mandatory) and In3, about 2.6 x 1.6 mm. Lay it out like the maker's pattern: the GND row (pins 2/3) at the void edge with a link of 0.3 mm or less, the feed row toward the interior, and the void lengthened beside the chip rather than past its GND end.
- Body void V2 (about 1.6 x 1.1 mm) on In2 and preferably In1.
- F side: only small passives over V2; no IC, pour, exposed pad or U.FL tab. On the Matrix's far side, 0201 BEMF passives sit under its chip and the ICs sit 1.1-1.4 mm to the side.

Ground return, antenna:
- The GND row links on B.Cu to two GND through vias just outside V1. Vias inside the 0.20 x 0.30 mm lands are not buildable, and inside V1 they would reach no In4/In1 copper.
- Each pi shunt gets its own In4 via at its own pad.
- Optional In4-In1 stitching along the void edge. Count those vias against the through-via budget (D88).

Ground return, boost (the owner's actual point, D92; separate work, not solved by this antenna note):
- U2/L1 PGND, CIN and COUT GND joined on the component layer, no via in the hot loop.
- In4 unbroken under the loop, with a direct In4/In1 return to battery GND.
- The antenna void stays at least 3 mm from that loop and outside the boost-to-battery corridor. Today the boost is about 11 mm from LNA_IN.

Match: 0201 series 0R on B (move R88 from F) plus one DNP shunt, two at most. Tune on the bench.

Range (I): the link budget is correct. Expect 4-10 m indoors if the antenna lands at -10 to -25 dBi. The mid-board layout is effectively an antenna over ground at about 0.83 mm, so -25 to -35 dBi (about 2-4 m) is just as plausible. The real pass gate is the 3 m firmware upload at the bench; |S11| alone does not show efficiency.

BetaFPV: the Matrix uses a white chip of about 1.6 x 0.9 mm (1608 class, identity not confirmed) about 1.2 mm from the ESP8285, beside the SH1.0 3-pin camera plug (not the USB). It has no edge or large clearance. Inner layers, and copper under the black mask, are unknown. It is larger than ours: BetaFPV saves area by leaving out a large clearance, not by using a smaller part. Its target is BETAFPV 2.4GHz AIO RX → Generic 2400.json (no ant_ctrl, 13 dBm), and BetaFPV says the RX updates over Wi-Fi.

Rejected: sharing the SX1281 antenna through an SPDT or a passive tap. Stock ELRS has no field to control it, it costs the RC link dB, and it exposes the SX1281 to +19.5 dBm.

Smallest part: 1005 is the floor (S). Alternatives with datasheets on hand: Pulse ANT1005LL14R2400A (its own land), Kyocera AVX 9005868/1005801 (1.00 x 0.58 x 0.35 mm, feed plus floating, 2-pad land), Abracon AANI-NI-0245. Check Johanson datasheet Rev 4.0 (2024) against Ver 3.1.

Unknown: the Wi-Fi antennas of EP/RP/BetaFPV Lite/Nano, and all efficiency figures until the bench test.
