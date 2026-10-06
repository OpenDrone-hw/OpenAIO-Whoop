# Build plan

How OpenAIO-Whoop goes from targets to a NextPCB order. Each phase has a
deliverable, pass criteria a script or a reviewer can check, and a gate. A
phase starts when the previous gate passes. Scope and part choices live in
[DESIGN-SPEC.md](DESIGN-SPEC.md); this file is only the path.

Target: match the BetaFPV Matrix 1S 5IN1 II envelope (1S, integrated serial
ELRS, analog VTX + OSD, 4x ESC, ~26.5 mm body, 3-4 ears) and beat it on
measured ratings, blackbox, repairability and open documentation. Fab and
turnkey assembly: NextPCB, at the limit of its published capabilities.

## Ground rules for the build

- The owner has given the build full authority (2026-10-06), including nets,
  placement and routing, which AGENTS.md otherwise reserves for people. Goal: a
  finished, clean, optimized board.
- KiCad files are changed through KiCad, kicad-skip or the pcbnew / IPC API
  wherever one exists. Where none does (`.kicad_dru` custom rules, the
  stackup, generating schematic content), the file may be written directly,
  and every such write is then loaded and re-saved by KiCad and passes
  `kicad-cli` ERC/DRC before it is committed.
- The board follows the lineup conventions in
  [LINEUP-CONVENTIONS.md](LINEUP-CONVENTIONS.md): schematic style, net names,
  title blocks, silkscreen and board art. `hardware/tools/check_conventions.py`
  passing is part of the P3, P4, P5 and P6 criteria.
- Every number in a pass criterion is checked by a script in `hardware/tools/`
  or by an independent review, not by the author of the change.
- ERC and DRC run before every push. New violation types or counts are listed
  in the PR.
- One person holds the layout. Announce on Discord before P4.

## Phases

| | Phase | Deliverable | Pass criteria | Gate |
|---|---|---|---|---|
| P0 | Spec freeze | `research/DESIGN-SPEC.md`, `research/COMPETITION.md` | Every block has a primary part (MPN, package, distributor stock >= 5x the 50-board quantity, checked date) and a fallback. Area budget per side <= 85 % of usable board area at 0.2 mm body spacing. 5 V rail holds all loads at 3.0 V in with >= 20 % margin on datasheet curves. Per-FET loss at the published ESC rating with a thermal estimate. NextPCB stackup and rule table with cited capability numbers. Draft FC pin map with timer/DMA conflicts checked. | Engineering review agent finds no blocker; owner reads it |
| P1 | Project scaffold | `hardware/OpenAIO-Whoop.kicad_{pro,sch,pcb}` from hardware-template | `kicad-cli` ERC and DRC run with 0 errors. Outline, hole pattern and keepouts match the spec (script). Stackup, constraints, track/via presets and net classes match the spec table (script reads the board). AGENTS.md Environment carries the template commands. | Script report clean |
| P2 | Library | Symbols, footprints, 3D models for every BOM line | Each part has MPN, manufacturer, distributor PN, datasheet. Every footprint checked against its datasheet land pattern (pad size, pitch, position within 0.02 mm, script). Dense variants (`*_Dense`: tight courtyard, NC pins removed) list every change and why it is safe. OpenDrone library parts used where present. | Footprint check script clean; review agent signs off pinouts |
| P3 | Schematic | Hierarchical sheets: power, fc, imu, blackbox, osd, vtx, rx, esc_channel x4, io | ERC 0 errors, every warning justified. Netlist script: no single-pin nets, every IC supply pin decoupled, every part has BOM fields. FC pin map in the netlist matches the Betaflight target table (script). BOM cost estimate. | Independent schematic review against datasheets, no blocker |
| P4 | Floorplan and placement | Placed board, both sides | All parts inside the outline on their planned side. Body-to-body gap >= 0.20 mm (script, from package bodies, not courtyards). Courtyard DRC clean under the custom rule. RF keepouts and gyro placement per spec. Power loop: FET to bulk cap <= spec distance. Top and bottom renders. | Placement review; owner sees renders |
| P5 | Routing | Routed board | DRC 0 errors, 0 unconnected, schematic parity. Power path copper cross-section meets the spec current per phase (script). RF lines at 50 ohm for the stackup. | DRC + review |
| P6 | Fab package | NextPCB Gerbers, drill, BOM, CPL, renders | Package passes NextPCB DFM (HQDFM or their review). BOM lines all orderable through NextPCB turnkey. Quote attached. | Owner places the order |

## Risks carried through every phase

- RTC6705 supply (no LCSC stock): turnkey sourcing must be confirmed by NextPCB before P6.
- Routing density: P5 is where a whoop AIO is won or lost. Power and RF routing
  are expected to need hand work in KiCad; the agent routes through the pcbnew
  API and reports what it could not close.
- Stackup is copied from measurement only once a physical Matrix II board has
  been sectioned; until then it is the spec's estimate.
