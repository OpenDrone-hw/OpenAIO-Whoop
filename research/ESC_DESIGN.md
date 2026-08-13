# Bluejay ESC, topology and sourcing research

Research trail behind the OpenAIO-Whoop ESC stage: what was measured, what was rejected, and why. The current decisions and their LCSC numbers live in [DESIGN.md](DESIGN.md); this file keeps the comparisons that produced them and does not restate the final part table. Competitive landscape and the class bar this research measured against: [MARKET-RESEARCH-2026-06.md](MARKET-RESEARCH-2026-06.md).

Scope of the work: rework the inherited AT32F421 / NSG2065Q ESC into a Bluejay (EFM8BB51, BB51 target) design for a 1S/2S whoop-class AIO with integrated ELRS and a digital video connector. Library import is done; no schematic or PCB work has been performed yet.

## Topology: no gate-driver IC (locked, 2026-06-12)

**The Bluejay ESC has no gate-driver IC, EFM8 GPIO direct drive only, there is no board space for one.** That locks the power stage to a complementary P+N pair per phase, because a high-side N-channel is impossible without a driver or a bootstrap. Consequences:

- 1S: clean direct drive, zero extra parts (the CrazyBee / tinyPEPPER pattern, confirmed by the teardowns below).
- 2S: the P-gate must reach VBAT (8.4 V) to turn OFF, so each phase needs a discrete level shift (2N7002, C8545, a JLC basic part, plus a pull-up: about 2 parts per phase, 24 per board). That is the only no-driver-IC option. If even that is too much board space, the design is 1S-only.
- The 12 A dual-N market tier (BetaFPV SiZ322DT boards) is off the table, because dual-N needs high-side drive. Honest rating for this topology is ~6-8 A continuous per phase, which covers 65-75 mm 1S whoops (real currents <=5 A per motor), not the 12 A spec-sheet war.

### Gate drive research that led there

Verified: small Bluejay/BLHeli_S whoop ESCs (for example **tinyPEPPER**, open hardware) drive the FET gates directly from the EFM8, with no gate-driver IC. That is correct **for 1S only**:

- At 1S (<=4.2 V) the 3.3 V GPIO can turn the high-side P-channel both ON (Vgs about -4 V) and OFF (the gate can be pulled to pack voltage). The MCU runs straight off the 1S pack.
- At 2S (8.4 V) direct drive breaks down: the P-channel source sits at 8.4 V and a 3.3 V GPIO cannot pull the gate up to 8.4 V to switch the high side **off**. tinyPEPPER author: *"For 2S one needs FET drivers and a proper voltage regulator for the CPUs."*

Open points that follow:

- At 2S the EFM8 needs its own 3.3 V regulator; it cannot run off the pack directly (abs max ~4.2 V).
- The low-side N can still be GPIO-driven through a gate resistor at 2S (source at GND, 3.3 V against Vgs(th) 1.6 V). Verify enhancement is adequate, consider a buffer if marginal.
- Pick gate resistors from Qg and the desired edge rate (tinyPEPPER reference: ~100 Ohm for ~50 nC / 500 ns).
- Rejected alternative: a proper 3-phase gate driver IC, which is what the inherited NSG2065Q did. Most robust, biggest BOM, no board space.

## What commercial whoop ESCs actually use (teardown research, verified)

- **CrazyBee F4 V2 class (5-10 A 1S, the architecture we are copying)**: 12x N+P complementary pairs marked "EGX87C" (full MPN never decoded, sold as repair parts under the marking), **driven directly by EFM8 GPIO, no driver**.
- **NewBeeDrone BLV1-4 / Hummingbird V2/V3**: the official replacement part is "N+P MOS" x12, same topology, MPN undisclosed.
- **BetaFPV F4 1S 12A (2022)**: 12x Vishay SiZ322DT dual-N 25 V PowerPAK1212 (3.3 x 3.3), EOL at DigiKey (successor SiZ350DT ~$2). Teardown identifies roughly 3-pin 0402-size parts plus 3 Schottkys and 3 bootstrap caps per motor, so the undocumented high-side drive is a **discrete bootstrap level shift per phase**: about 3 extra parts per phase, 9 per motor, 36 per board. Not for us.
- **NBD BLV5 / RaceSpec V2 "18A"**: "double N-channel", MPN undisclosed.
- **20 A+ toothpick tier**: Toshiba TPN2R203NC-class discrete N plus FD6288 drivers, that is the OpenESC-20x20 architecture, irrelevant here.
- **2025 Matrix 1S 5IN1 II (Air65 II, "12A/18A")** uses AGMSEMI **AGM210MAP, complementary P+N, GPIO direct drive: the same architecture we chose.** Datasheet verified locally: PDFN 3.3 x 3.3 (not 2 x 2; note that LCSC and BetaFPV listings say 25 V while the datasheet says **20 V**), N 10 typ / 14 max mOhm at 4.5 V (14/20 at 2.5 V), P 13 mOhm typ, Vgs(th) max 1.0 V, 25 A / 100 A pulsed, RthJC 3.5. C7431169, 10,623 stock, 20x the stock of AGM310MAP or AGM314MAP.
- Bluejay layout naming note: the middle letter (Z_**H**_30, A_**X**_5) is the MCU family (H = BB21, X = BB51), NOT the FET topology; only the deadtime digits hint at the stage.

Implications of the Matrix 1S 5IN1 II teardown:

- The flagship "12A/18A" 1S board is P+N direct drive, so our topology is the current market architecture, not the legacy one. Their 12 A claim on N 10 / P 13 mOhm dies works out to about 1.7 W per phase: spec-sheet optimistic, and consistent with our honest-rating stance.
- **AGM210MAP supersedes AGM310MAP and AGM314MAP as the AGMSEMI pick at the 3.3 x 3.3 tier** (better dies, field-proven on the Air65 II, real stock). Earmarked for the mid-tier 2S Bluejay concepts, not for this board: its 20 V rating means a 2-3S ceiling.
- Why 20-25 V parts on a 1S board? Voltage class is nearly free in trench processes; it buys avalanche margin against phase-node inductive spikes and lets one part cover 1S to 2S+ product lines. XR8G02M (20 V) follows the same logic.
- Also on that board: G473CEU6 (we use RP2354A), BB51F16G QFN-20 (the same EFM8 as ours), AT7456E analog OSD plus an RTC6705-class VTX (not applicable, we are digital-only), PUYA PY25Q128 16 MB blackbox flash, and a **2-Schottky diode-OR for 5 V/USB selection** instead of a power-mux IC. The diode-OR is a candidate to replace TPS2116 on the whoop: saves space and cost, costs ~0.3 V drop, trade accepted.

## Power stage sweep

Requirement from the layout: the package must fit a whoop board, so <=2.2 x 2.2 mm. AGM314MAP (3.3 x 3.3) is too big for this board and stays earmarked for the larger AM32 toothpick AIO. A full LCSC sweep at <=2.2 x 2.2 found **exactly one power-class complementary N+P family at 2 x 2: Diodes DMCxxxxUFDB (U-DFN2020-6)**. Everything else complementary at SOT-563 or SOT-363 is small-signal (>=350 mOhm). AGMSEMI has nothing below 3.3 x 3.3.

### Selected: XR8G02M (round 3)

**XR8G02M (XNRUSEMI, DFN2020-8L, 2 x 2)** was missed by both parametric sweeps because LCSC files it under "Single FETs". Datasheet verified against the listing:

- N: 12 typ / 15 max mOhm at 4.5 V, 16/23 at 2.5 V, Vgs(th) 0.5-1.5 V
- P: 17 typ / 25 max at 4.5 V, 24/30 at 2.5 V
- 20 V Vds (against SiA527DJ's 12 V, so proper spike margin at 1S), +/-12 V Vgs, 8 A continuous, 32 A (N) / 28 A (P) pulsed, avalanche-rated, PD 15/20 W
- Qg 15/19 nC at 10 V (roughly 6-9 nC at 3.3 V), slightly heavier gates than the alternatives. Fine at 24-48 kHz PWM with direct GPIO drive; do not run 96 kHz.
- Pinout: D1/G1/D2/G2 bottom row, S1 x2 / S2 x2 top, dual exposed pads. Die 1 is the N, die 2 is the P; verify the assignment in the schematic.
- Price $0.036-0.05, cheapest candidate by 3-6x.

It beats SiA527DJ (N 29 / P 41 max) and DMC1229UFDB (N 29 / P 61 max) on every electrical axis. **Supply is the only weakness: LCSC live stock 80 pcs, XNRUSEMI is a small single-source brand, standard reel 4000, so order or quote a reel up front** (consignment workflow accepted). SiA527DJ stays the qualified second source on its own footprint, with the AON2406 + YJQ1216A pair as the BOM-resilient fallback.

### Round 2: SiA527DJ is the dual-package ceiling

Second sweep covering Vishay PowerPAK SC-70-6, onsemi WDFN 2 x 2, Diodes 8-lead, and AOS / Toshiba / Nexperia / Chinese-brand 2 x 2-8L (DigiKey acceptable, consignment OK):

- **No <=2.3 mm complementary dual reaches N <=20 / P <=35 mOhm. The class ceiling is the Vishay SiA527DJ** (PowerPAK SC-70-6, 2.0 x 2.0 x 0.8): N 29 / P 41 mOhm max at 4.5 V, spec'd down to a 1.5 V gate, Vgs(th) <=1.0 V, +/-4.5 A continuous, 20 / -15 A pulsed, 12 V. LCSC C222486 (4.9k, ~$0.24) and DigiKey 11k, so dual-sourced. P-side 33% better than DMC1229UFDB, N-side a tie. NOT pin-compatible with U-DFN2020-6, different footprint, verify phase-leg orientation.
- Nexperia LFPAK22 is N-only (no P exists); AOS and Toshiba have no complementary part at <=2.3 mm; LCSC has zero Chinese-brand complementary duals in any 2 x 2-8L package (verified via API).
- **If Rds is the priority, the discrete pair wins decisively: AON2406** (N, 12.5 mOhm max at 4.5 V, C3277752, 6.5k stock) **+ YJQ1216A** (P, 19 max / 11 typ, C919545, 1.9k stock), both DFN2020-6, ~$0.21-0.25 per phase. That is 2.3x (N) and 3.2x (P) lower than the best dual, both spec'd at 2.5 V, and gives a true 5 A continuous per phase. Cost: 24 placements instead of 12, though total area (96 mm2) is still less than 12x AGM314MAP (131 mm2). BOM-resilient, because N and P substitutes at 2 x 2 are plentiful and independent. YJQ1216A is LCSC-only; DigiKey P alternates at 2 x 2 are thin (DMP1022UFDF, C155358, as a second source). Verify AON2406 low-Vgs behaviour (sister part AON2408, C2931064, has the documented 2.5 V spec).

All three imported into the `whoop` library (SIA527DJ-T1-GE3, AON2406, YJQ1216A); the SiA527DJ datasheet is held locally.

**Open choice if XR8G02M supply fails:** SiA527DJ dual (12 packages, simpler) against the AON2406 + YJQ1216A pair (24 packages, about half the conduction loss).

### Round 1: DMC1229UFDB-7, the fallback dual

**DMC1229UFDB-7 (C443653, U-DFN2020-6, 2.0 x 2.0 x 0.6 mm)**, imported into the `whoop` library, datasheet local.

- +/-12 V, N 29 / P 61 mOhm max at 4.5 V, spec'd down to a 1.8 V gate (true logic level, Vgs(th) max 1.0 V), so at 3.3 V worst case about N 31 / P 70 mOhm
- Id 5.6 / -3.8 A continuous, 20 / -15 A pulsed. Realistic on a dense whoop board: **~2.5 A continuous, ~5 A for seconds, 10 A+ pulses per phase**, which matches 0802/1002 motor reality (2-5 A peaks).
- Smaller and thermally better (leadless, RthJC 30) than the SOT-23-6-class "EGX87C" parts on commercial 5 A whoop boards, so not a downgrade.
- Caveat: 12 V Vds at 1S. Fine with a low-inductance layout plus per-phase ceramic bypass; watch switching spikes on the bench.
- Stock: LCSC 2,280 plus DigiKey backup; family stock swings hard, so dual-source reels.

Same-footprint variants (drop-in, U-DFN2020-6 Type B pinout): **DMC2041UFDB-7** (20 V, P 90 mOhm at 4.5 V, derate to ~2 A; LCSC 165 / DigiKey 5,840) if spike margin worries; **DMC1030UFDB-7** (best silicon: N 17 typ / P 59 max, IDM 35 A, RthJC 18; LCSC 0 / DigiKey 2,784, prototype via DigiKey).

### Superseded: the AGMSEMI 3.3 x 3.3 line

The first pass scoped the ESC around **AGM310MAP** (C5184858, PowerDI3333-8), imported into the `whoop` library on `POWERDI3333-8_L3.3-W3.3-P0.65-LS3.4-BL-EP_UXC`. Confirmed topology from the AGMSEMI datasheet, kept here because the pinout is shared across the family:

- Complementary pair: 1x P-channel (high side) + 1x N-channel (low side), common drain.
- 30 V Vds. N: 20 A, Rds(on) 11 mOhm at 10 V, Qg 16 nC. P: 18 A, Rds(on) 19 mOhm at 10 V, Qg 45 nC. Vgs(th): N 1.6 V, P 1.5 V.
- Pinout: FET1 = G2/D8/S1, FET2 = G4/D5/S3. Tie the two drains (D5, D8) for the phase output; P source to VBAT, N source to GND.
- Massively overspec for 2S (used at about 25% of Vds), so oversized but cool-running.

Why it was dropped:

- **Thermal, at the 12 A class floor.** P-channel Rds(on) is 19 mOhm. At 12 A phase current with ~50% high-side conduction, P = 12^2 x 0.019 x 0.5 = about **1.4 W per phase high side** (4.1 W total high side at full load) in 3.3 x 3.3 mm packages on a ~25 mm board. The complementary P+N topology is comfortable in the **5-8 A class**, marginal at 10 A, and not credible at 12 A continuous / 18 A burst.
- **Supply.** 166 JLC assembly / 515 LCSC retail at 12 per board is about 42 boards total, a production blocker.
- **Package.** 3.3 x 3.3 is too big for a whoop board.

**AGM314MAP (C17701056)** replaced it first: pinout verified IDENTICAL to AGM310MAP from both datasheets (Pin1 = S1, G1/S2/G2 bottom row, D1/D2 pads; FET1 = N 30 V / 10 mOhm at 10 V / 30 A, FET2 = P -30 V / 18.5 mOhm at 10 V / -20 A), same PDFN 3.3 x 3.3 package, strictly better dies, ~3k LCSC stock (against 166-515), **$0.074 at 500, 35% cheaper**. Imported into the `whoop` library. Caveat for direct 3.3 V drive: the datasheet specs Rds at 10 V and 4.5 V only, N 16 mOhm typ / P 27 mOhm typ at 4.5 V, and Vgs(th) max 2.2 V leaves only ~1.1 V of overdrive worst case at 3.3 V. **Bench-verify Rds and switching at a 3.3 V gate on a 1S pack** before committing to this part. (That is the same regime every CrazyBee-class board operates in.)

AGM210MAP then superseded both, see the Matrix teardown above. Hedges recorded at the time, still valid for anything built on the 3.3 x 3.3 tier:

- Diodes **DMC3025LDV-13**, same PowerDI3333-8 footprint class, Western brand, DigiKey 5.7k at $0.25/1k. But Vgs(th) 2.4 V and Rds spec'd at 4.5 V make it **not credible at 3.3 V direct drive**; it is a 2S-with-level-shift second source only.
- Discrete pair on a dual-pad footprint: AGM30P08AP (P, 11.5 mOhm at 4.5 V, 6k stock) + AGM310AS (N, DFN 2 x 2, $0.048) if the AGMSEMI duals dry up.
- AGM318MAP and AGM312MAP exist in the same package but are worse and lower-stock, ignore them.

### Rejected topology: N+N plus driver

N+N FETs with a 3-phase half-bridge driver per channel is what the 12 A+ commercial boards do (NBD "double-NMOS"). Driver candidates were the FD6288Q family clones (6288Q-MNS and similar, proven in the OpenESC-20x20 lineage). They need a >=10 V gate supply, so 2S-only or a small boost. Excluded by the no-driver-IC decision above. A hybrid (low-side N on direct GPIO, high-side N on a bootstrap driver) was considered and excluded for the same reason.

## Rating: honest numbers against the market

Market tier marketing is 12 A continuous / 18 A burst (BetaFPV Matrix dual-N SiZ322DT at about 5.3 + 6.35 mOhm, so roughly 0.84 W per phase at 12 A, only reachable with dual-N plus high-side drive, which the no-driver constraint excludes).

XR8G02M direct-drive P+N at a ~3.3 V gate (estimated ~14/20 mOhm typ) gives about 17 mOhm average conduction: 1.1 W per phase at 8 A, 2.4 W at 12 A.

**Honest spec target: ~8 A continuous / 15-20 A burst per motor** (IDM 32/28 A). Real 1S whoop flight currents are 2-5 A with brief 8-10 A punch-outs, so in practice this matches what "12 A" boards sustain on 65-75 mm 1S. Publish the measured rating, not the marketing one.

Package allocation across the family: **2 x 2 XR8G02M is this whoop board**; the AM32 toothpick AIO keeps its own 3.3 x 3.3 N-FET plus driver stage (DOY180N03T + NSG2065Q from OpenESC-20x20); **AGM210MAP** (3.3 x 3.3 complementary) is reserved for the mid-tier 2S Bluejay concepts (OpenAIO-Lite-HD/Analog), where its 20 V rating gives a 2-3S ceiling.

## Other stage decisions

**Blackbox flash.** The inherited TF-021B microSD slot goes, replaced by SPI NOR on a free RP2350 SPI bus; remove the slot and its associated parts. BY25Q64ESCIG (C50176394, 64 Mbit, DFN-8 3 x 2) was the first pick and is dead at retail (LCSC stock 1), so it is superseded by W25Q128JVPIQ. Sourcing rationale for the replacement: 16 MB is the market bar and the same capacity BetaFPV ships, and WSON-8 5 x 6 is the smallest stocked 3.3 V 128 Mbit package, because the 2 x 3 DFN class tops out at 64 Mbit with everything either dead or 1.8 V (W25Q64JV and ZD25Q64 were the 2 x 3 candidates checked). Stock at selection: 6.4k in WSON-8 plus 110k in the SOIC variant. Still a smaller package than BetaFPV's SOP-8. Part numbers in [DESIGN.md](DESIGN.md).

**RX MCU density option.** ESP8685H4 is the ESP32-C3 die with in-package 4 MB flash in a QFN-28 4 x 4, against the QFN-32 5 x 5 of the ESP32-C3FH4: the ESP8285 analog for the C3 generation. It runs the same ELRS ESP32-C3 targets and OpenRX already had the datasheet on file. Costs a new footprint and fewer GPIO, so the RX section needs a relayout. Stock at selection: 872 in the JLC assembly library. Imported into the `whoop` library.

**Current sense.** Drop the inherited 4x INA186 per-channel scheme on the top sheet. Bluejay commutates sensorless (BEMF), so per-phase sensing is not needed. If telemetry is wanted, use one total-current shunt on the pack return into a single amp into an FC ADC. Shunt candidate: 1 mOhm 1206 (C7467246); 0.625 W at 25 A is 63% of the 1 W rating, so use a 2010 WSLP for margin.

**Motor connectors.** JST/Molex 1.25 mm 3-pin is the canonical whoop motor plug: C293630 (Molex PicoBlade), with the C3029360 clone at a third of the price.

**HD video connector.** Add a standard HD-VTX connector, SH1.0 6-pin on the DJI O4 pinout. Pinout and BEC requirements: [MARKET-RESEARCH-2026-06.md](MARKET-RESEARCH-2026-06.md).

**Firmware.** EFM8BB51 is a BB51 target. Classic BLHeli_S predates BB51 and the Bluejay fork adds it, so the ESC ships Bluejay pre-flashed, never stock BLHeli_S.

**1.8 V gyro LDO (family-wide).** TPS7A2018PDQNR was chosen over LP5912-1.8 on actual PSRR curves: 75 dB spec'd at both 10 kHz and 100 kHz, where LP5912 dips to about 58 dB right in the 20-30 kHz MEMS gyro drive band, and the original NCV8187 collapses to about 35 dB at 300 kHz. Noise 7-10 uVrms. Trade-offs: the PG pin is lost (D8 LED net) and it is a new footprint, both accepted, since a re-route was needed anyway. Keep a ferrite or RC pole ahead of the LDO for the ~1 MHz buck band, where every candidate sits at 45-50 dB. Supply at selection: only 42 pcs LCSC retail against 25k at DigiKey at $0.136, so consign. The SOT-23-5 DBV part (C963430, 25k LCSC stock) is the large-package alternate. Imported into the `whoop` library here and into the `imports` library in OpenAIO; full comparison table in the OpenAIO repo, `docs/SOURCING-2026-06.md`.

## Sourcing snapshot (LCSC, 2026-06-12)

Point-in-time figures from the selection pass. The AGM310MAP and BY25Q64ESCIG rows are the reason those two parts were dropped; current parts and their stock position are in [DESIGN.md](DESIGN.md).

| Part | LCSC | JLC asm stock | LCSC retail | Verdict |
|---|---|---|---|---|
| EFM8BB51F16G-C-QFN20R | C6547511 | **not in JLC lib** | 17,124 | LCSC plentiful; verify JLCPCB assembly availability or consign |
| EFM8BB51F16I (alt) | C3232998 | 119 | 0 | G-grade is the buy |
| AGM310MAP | C5184858 | 166 | 515 | **Production blocker**, 12 per board is ~42 boards total. Second-source or change topology |
| BY25Q64ESCIG | C50176394 | 305 | **1** | Dead at retail. Swap to a stocked NOR part (W25Q64JV / ZD25Q64 class was checked first) |
| 2N7002 (level shift) | C8545 | **basic part** | 1.8M | OK |
| 1 mOhm 1206 shunt | C7467246 | - | 96k | OK (0.625 W at 25 A is 63% of the 1 W rating; 2010 WSLP for margin) |
| Motor plug 1.25 mm 3P | C293630 (Molex PicoBlade) | - | 29k | Canonical whoop motor connector; C3029360 clone at a third the price |

Whole-family supply flag (affects the FC sheets inherited from OpenFC-Lite-Mini): **NCV8187AMT180TAG (1.8 V gyro LDO, C893189) is effectively unobtainable** (62 JLC / 19 LCSC). Replacement decided, see the LDO note above.

## Library import notes

Symbols in `hardware/whoop.kicad_sym`, footprints in `hardware/whoop.pretty/`, 3D models in `hardware/whoop.3dshapes/`, all under the `whoop` lib-table nickname. 3D-model paths are `${KIPRJMOD}`-relative. The library holds the current picks alongside the second sources and the superseded candidates discussed above, so treat [DESIGN.md](DESIGN.md) as the list of what is actually current.

EFM8 grade: the imported symbol is `EFM8BB51F16G-C-QFN20R` on `QFN-20_L3.0-W3.0-P0.50-TL-EP1.7_SILICON_C8051F85X`, the **G** grade (commercial, -40 to +85 C). The I-grade `EFM8BB51F16I-C-QFN20R` (C3232998) is the wider-temp, pin-identical alternate if the G grade runs short.

## Open items for the first whoop spin

- [ ] Lock the pack voltage: 1S-only or 1S/2S. It gates the per-phase level shift and the BEC topology.
- [ ] Confirm the XR8G02M die assignment in the schematic: die 1 = N (low side), die 2 = P (high side).
- [ ] At 2S, power the EFM8 from a regulated 3.3 V rail; decoupling per datasheet, C2 debug header exposed.
- [ ] Bulk and phase caps rated for the pack voltage (>=16 V at 2S).
- [ ] Reverse-polarity protection on the pack input.
- [ ] Bluejay signal pins, one per channel, routed to the FC.

## Sources

- tinyPEPPER (fishpepper): https://fishpepper.de/projects/tinypepper/
- ckflight BLHeli_S ESC hardware: https://ckflight.github.io/ESC_BLDC_HARDWARE/
- BLHeli_S (bitdump): https://github.com/bitdump/BLHeli
- brushlesswhoop.com, anatomy of an all-in-one FC: https://brushlesswhoop.com/anatomy-of-an-all-in-one-fc/
- AGM310MAP: LCSC C5184858 (AGMSEMI), https://www.lcsc.com/product-detail/C5184858.html
