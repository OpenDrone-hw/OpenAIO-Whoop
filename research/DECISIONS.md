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
