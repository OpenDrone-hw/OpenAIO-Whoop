# Build plan

How OpenAIO-Whoop goes from targets to a NextPCB order. Each phase has a
deliverable, pass criteria a script or a reviewer can check, and a gate. A
phase starts when the previous gate passes. Scope and part choices live in
[DESIGN-SPEC.md](DESIGN-SPEC.md); this file is only the path.

Target: match the BetaFPV Matrix 1S 5IN1 II envelope (1S, integrated serial
ELRS, analog VTX + OSD, 4x ESC, ~26.5 mm body, 3-4 ears) and beat it on
measured ratings, blackbox, repairability and open documentation. Fab and
turnkey assembly: NextPCB, staying DFM-compatible with JLCPCB too.

## Ground rules for the build

- The owner has given the build full authority (2026-10-06), including nets,
  placement and routing, which AGENTS.md otherwise reserves for people. Goal: a
  finished, clean, optimized board.
- The owner rules for every OpenDrone board (pcb-agent-commons
  `lessons/owner-rules.md`, 2026-10-06) apply. In short: no component
  silkscreen, every solder pad labelled, no "Drone" on the board, exact MPN on
  every BOM line, 0201 passives by default, minimal justified capacitance,
  through vias only unless the owner approves otherwise, KiCad features used
  properly (net-class directive labels, stackup with impedance, custom rules,
  keepouts, zone priorities, component classes, design blocks, jobsets),
  floorplan before schematic, and critique rounds until none finds a blocker
  or major.
- KiCad files are changed through KiCad, kicad-skip or the pcbnew / IPC API
  wherever one exists. Where none does (`.kicad_dru` custom rules, the
  stackup, generating schematic content), the file is written by a script, then
  loaded and re-saved by KiCad and passes `kicad-cli` ERC/DRC before it is
  committed.
- The board follows the lineup conventions in
  [LINEUP-CONVENTIONS.md](LINEUP-CONVENTIONS.md). `hardware/tools/check_conventions.py`
  with 0 FAIL is part of every gate from P3 on.
- Every number in a pass criterion is checked by a script in `hardware/tools/`
  or by an independent review, not by the author of the change.
- Every gate ends with critique agents from at least two perspectives
  (electrical, manufacturing, firmware, RF, lineup). The gate passes only when a
  round finds no BLOCKER or MAJOR.
- ERC and DRC run before every push. New violation types or counts are listed
  in the PR.
- At each gate: pull pcb-agent-commons, adopt other boards' lessons, append
  ours to `lessons/OpenAIO-Whoop.md`.

## Phases

| | Phase | Deliverable | Pass criteria |
|---|---|---|---|
| P0 | Spec freeze | `research/DESIGN-SPEC.md`, `research/COMPETITION.md` | Every block has a primary part (MPN, package, distributor stock >= 5x the 50-board quantity, checked date) and a fallback. Area budget per side <= 96 % of usable board area at 0.2 mm body spacing (the method scores the shipping Matrix II at about 96 %, D20); the P2 placement is the binding proof. 5 V rail holds all loads at 3.0 V in with >= 20 % margin on datasheet curves. Per-FET loss at the published ESC rating with a thermal estimate. NextPCB/JLCPCB stackup and rule table with cited capability numbers, through vias only. Draft FC pin map with timer/DMA conflicts checked. |
| P1 | Project setup | Project from hardware-template with outline, stackup, rules | `kicad-cli` ERC and DRC 0 errors. Outline, hole pattern and keepouts match the spec (`check_board_setup.py --spec`). Stackup with impedance, constraints, presets, net classes with colours, custom rules parsed (`check_rules.py`). |
| P2 | Floorplan proof | Board with every part placed roughly per block on its side, connectors, pads and labels final | Every block's parts fit their region with the 0.2 mm body rule (script). Every solder pad has its label at the minimum legible size. Connectors and pads match the frame and wiring direction. Renders. |
| P3 | Library | Symbols, footprints, 3D models for every BOM line | MPN, manufacturer, datasheet per part. Footprints checked against the datasheet land pattern within 0.02 mm (script). Courtyards normalised to max(body, land) + 0.10 mm so courtyard DRC enforces spacing. Dense variants list every change and why it is safe. |
| P4 | Schematic | Hierarchical sheets following the floorplan | ERC 0 errors, every warning justified. Netlist script: no single-pin nets, every IC supply pin decoupled, BOM fields complete. FC pin map matches the Betaflight target table (script). Net-class directive labels on power, motor and RF nets. |
| P5 | Placement | Final placement synced from the schematic | Parity 0. Body gap >= 0.20 mm (script). Courtyard DRC clean. RF keepouts, gyro placement and power loops per spec. |
| P6 | Routing | Routed board | DRC 0 errors, 0 unconnected, parity 0. Power path cross-section meets the spec current (script). RF lines at 50 ohm for the stackup. |
| P7 | Fab package | NextPCB Gerbers, drill, BOM, CPL, renders, jobset | Package passes NextPCB DFM. Every BOM line orderable by MPN through NextPCB turnkey (consigned parts listed). Quote attached. Owner places the order. |

## Risks carried through every phase

- RTC6705 is broker-only (no LCSC or HQ Online stock): plan a partial-turnkey
  order with consigned parts, and confirm traceability before P7.
- Routing density with through vias only: P6 is where a whoop AIO is won or
  lost. Filled and capped via-in-pad keeps through vias usable under parts on
  both sides; if the area budget still does not close, HDI is put to the owner
  as a decision, with the numbers.
- Stackup is copied from measurement only once a physical Matrix II board has
  been sectioned; until then it is the spec's estimate.
