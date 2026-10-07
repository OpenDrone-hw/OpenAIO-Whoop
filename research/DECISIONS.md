# Decisions log

Build decisions with their reason, newest at the bottom. Owner statements are
quoted with their date. Lessons adopted from the other OpenDrone boards come
from the shared agent commons (`lessons/*.md`).

| # | Date | Decision | Reason |
|---|---|---|---|
| D1 | 2026-10-06 | 1S only; match the BetaFPV Matrix 1S 5IN1 II envelope and features | Owner: "go for 1S only, match the Matrix" |
| D2 | 2026-10-06 | NextPCB turnkey, extreme density (0.2 mm body-to-body, double-sided, trimmed footprints) | Owner direction 2026-10-06 |
| D3 | 2026-10-06 | Build authority for nets, placement and routing; goal a finished, clean, optimized board | Owner: "you have full permissions to do anything I want a finished clean optimized board by the end" |
| D4 | 2026-10-06 | Lineup conventions per LINEUP-CONVENTIONS.md: incutec logo, no "Drone" on fabricated layers, rev1, shipped wordmark art in schematics, power nets +BATT/+5V/+3V3/+1V8/GND, embedded Tokyo font | Shipped boards and brand repo; checker passes OpenFC-Lite |
| D5 | 2026-10-06 | Owner rules for every board adopted: no component silk, every pad labelled, exact MPNs, 0201 default, minimal capacitance, through vias only, KiCad features used properly, critique until no BLOCKER/MAJOR, floorplan first | owner-rules.md |
| D6 | 2026-10-07 | Keep the OpenDrone 0.35/0.20 via; filled and capped via-in-pad is the baseline in dense areas | Owner to OpenFC-H7: "nextpcb can do 0.2/0.35mm vias", "via in pad will defo be needed" |
| D7 | 2026-10-07 | Re-enable the template's ignored DRC checks before placement; scope intended exceptions with named DRU rules; own copper-inside-outline check | OpenAIO: the ignored checks hid copper routed past the board edge |
| D8 | 2026-10-07 | Bounded agents with STATE checkpoints, prlimit on heavy jobs, one heavy job at a time | OpenAIO: OOM restarts killed parallel routing agents; OpenFC-H7: a 650k-token agent |
| D9 | 2026-10-07 | Reuse commons tools: board_setup.py (stackup, impedance, DRU self-test), silk_check.py, sch_visual_check.py, fab packaging | Proven on OpenFC-H7 and OpenAIO |
| D10 | 2026-10-07 | Floorplan rules from the other boards: keep-out distances decided in the floorplan, GND stitching planned before routing, offset top/bottom FET stacks so low-side sources keep via room, shunt corridors in rule areas | OpenFC-H7 critique round 1; OpenAIO R3-2 |
| D11 | 2026-10-07 | Lean and market-evidence rules for trade-offs: no part unless it fixes a real error or comparable production whoop AIOs fit it | Owner to OpenFC-H7 (D76, D77): "just do market research", "don't inflate the schematic" |
| D12 | 2026-10-07 | Area gate: ESC to discrete TI CSD25310Q2 (P, 2x2) + CSD13202Q2 (N, 2x2) per phase; rating published as measured (model about 5 A continuous, Matrix's real class); pad labels 0.8 mm, C2 pads unlabelled; VTX LDO LP5912-3.3, 2520 crystal; camera plug kept unless P2 fails | P0 critique round 2: budget 95 %/97 % against the 85 % gate. Spec §9.3 levers 1, 2 and 4; genuine globally stocked parts over the LCSC-only AGM210MAP; continuous rating is set mostly by non-ESC heat, so the smaller FETs cost little in the published number |
| D13 | 2026-10-07 | Digital VTX (DJI O4 Lite) supported through solder pads (VCC, GND, TX, RX) on a PIO UART; VTX supply sized for an O4 Lite; onboard analog VTX kept | Owner: "vtx solder pads is good" |
| D14 | 2026-10-07 | Stay 1S only; O4 Lite from the 5 V regulator through a gated load switch; further area cuts (camera pads, smaller NOR, regulator consolidation) as needed | 1-2S study: all 2S options fail the area gate (+75-125 mm²) and 12 V N-FETs would clamp a 2S battery-disconnect surge (~0.3 J vs 20 mJ); production 2S boards use 25-30 V FETs |
| D15 | 2026-10-07 | O4 Lite powered from the existing TPS61022 5 V boost (4th 22 µF output cap) through a TPS22810 load switch gated by an FC GPIO and a ~2.9-3.0 V battery threshold | The boost gives 1.67-1.98 A at 2.8-3.2 V, more than a TPS63070 at 1S; the threshold sheds the O4 before a sagging cell resets the FC and RX |
| D16 | 2026-10-07 | O4 on UART1 (MSP DisplayPort); user UART pads on PIO UART0; HD pads VHD/GND/TX1/RX1, no SBUS pad | Pin budget per PINMAP; SBUS not needed with MSP DisplayPort and ELRS on the FC |
| D17 | 2026-10-07 | One video system at a time: analog VTX held off in HD mode | Avoids two 5.8 GHz carriers and saves heat |
| D18 | 2026-10-07 | Area cuts: camera pads instead of the plug, smaller NOR if stocked, side balancing; next levers pogo-pad USB (UD 4IN1 style), then no Wi-Fi stub | Budget still over after D12 |
| D19 | 2026-10-07 | 2S belongs on a separate future board (HD-only, 20-30 V FETs) | 1-2S study, D14 |
| D20 | 2026-10-07 | Area gate recalibrated to <= 96 % per side on the budget method; P2 real placement is the binding proof | The same budget method scores the shipping Matrix II at about 96 %: an 85 % gate was stricter than the board we are matching |
| D21 | 2026-10-07 | DRC must end at 0 errors / 0 unconnected / parity 0; deliberate rule breaks are named, scoped DRU rules with a justification, never global ignores | Owner: "I need DRC to be clean but you'll need to break some rules" |
