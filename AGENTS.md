# OpenAIO-Whoop

All-in-one board for 1S whoops, 65 to 85 mm class: a Betaflight flight
controller on an RP2354A, four Bluejay ESC channels (EFM8BB51 driving
AGM210MAP half-bridges), an onboard ExpressLRS 2.4 GHz receiver
(ESP32-PICO-V3 and SX1281) and an onboard analog VTX (RTC6705 and SE5004L)
with a PIO framebuffer OSD. A 26.4 mm body on the 25.5 x 25.5 mm whoop
pattern, the 1S sibling of [OpenAIO](https://github.com/OpenDrone-hw/OpenAIO).
It is not a 2S board: every rail is boosted or regulated from one cell.

## Design sources

- Open `hardware/OpenAIO-Whoop.kicad_pro` in KiCad 10. The root schematic and
  its hierarchical sheets are authoritative for connections, values and BOM.
- Read [research/DESIGN-SPEC.md](research/DESIGN-SPEC.md) for the fitted circuit,
  [research/PINMAP.md](research/PINMAP.md) for pins, and
  [research/ROUTING.md](research/ROUTING.md) for placement, layers and file paths.
- Firmware bindings live in `firmware/betaflight/` and `firmware/expresslrs/`.
  Do not copy obsolete configuration snippets from historical design proposals.
- The board has parked parts and inherited escape vias. Local rule areas and
  placement are unfinished; do not describe it as DRC-clean or manufactured.
- `bom_plan.json` and `sch_contract.json` are generated readbacks. Refresh them
  with `export_bom_plan.py` and `export_interfaces.py`; never use legacy circuit
  generators to overwrite the owner schematic from these exports.

## Layout rules

- In1 is a solid GND plane. In4 is a GND pour that carries only ESC gate and BEMF
  routing (D121). In2 carries no analog or RF; In3 carries no analog, RF, gate,
  gyro or VTX control nets. The DRU enforces the global layer restrictions. Named local areas are absent
  until placement; create them using research/ROUTING.md before routing.
- HDI 1+4+1: laser microvias L1-L2 and L5-L6 only, buried vias L2-L5 staggered
  from them, no stacking. Vias sit inside same-net pads; a free-standing via
  takes board space and is avoided.
- RF nets carry no vias and keep 50 ohm width on the outer layers. Inside the
  `RF_VTX_STRIP` rule area (0.5 mm around the 5.8 GHz chain) only GND vias are
  allowed, so In1 stays solid under the line; `RF_PAD_CUTOUT` cuts In1 out
  under the U.FL signal pad.
- AE1, the RX wire, leaves through a plated D0.5 hole. Inside the D2.0
  `RF_RX_HOLE` area pours are kept out on all layers and the only copper is the
  2.4 GHz feed on L1. AE2 has no all-layer keep-out but minimal copper around
  it, with parts on the opposite side.
- The 5 V boost hot loop closes on the component layer with a direct ground
  return: no via in the loop, unbroken GND under it, a small switch node, away
  from the gyro, the crystals and the antennas.
- Each AGM210MAP keeps its 22 uF hot-loop cap directly across its supply pair.
  The battery path from the pads through R2 to each ESC cell stays short and
  symmetric; R2's sense taps stay Kelvin, off In2 and In3.
- The motor plugs, the twelve half-bridges, the USB plug at the rear hole, the
  battery pads and the camera plug sit where the BetaFPV Matrix 1S 5IN1 II has
  them, so motor leads, battery lead and camera cable reach as they do on that
  board. Moving them breaks that fit.

## Parts and datasheets

- **Per-repository part index:** the root schematic and its listed sub-sheets
  are authoritative for what this board fits. Export the netlist with the
  command below when a script-readable board index is needed; do not maintain
  a second hand-written BOM.
- **Symbols and footprints:** every footprint is in `hardware/lib.pretty/`.
  Symbols come from `hardware/lib.kicad_sym` or KiCad 10's stock `Device`,
  `power`, `Connector` and `Mechanical` libraries.
- **Proven shared parts:**
  `hardware/KiCad-Library/PARTS-USED.md` is the catalogue index. Its `Boards`
  column identifies every repository using each LCSC part.
- **Exact datasheets:**
  `hardware/KiCad-Library/datasheet/manifest.json` maps shared symbols to the
  committed PDFs and their SHA-256 hashes. The PDFs live in
  `hardware/KiCad-Library/datasheet/`, and symbol links resolve there through
  `OPENDRONE_LIB`.
- **Local-only parts:** inspect `hardware/lib.kicad_sym`,
  `hardware/lib.pretty/`, and `hardware/lib.3dshapes/`, then verify supplier
  fields in the board schematic. Do not duplicate a shared part or datasheet.

## Environment

```sh
# clone with the pinned shared library (symbols, footprints, 3D models)
git clone --recurse-submodules https://github.com/OpenDrone-hw/OpenAIO-Whoop
git submodule update --init   # existing clone, hardware/KiCad-Library empty

# schematic and board checks
kicad-cli sch erc hardware/OpenAIO-Whoop.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones hardware/OpenAIO-Whoop.kicad_pcb

# component/interface exports and schematic checks
python3 hardware/tools/export_bom_plan.py
python3 hardware/tools/export_interfaces.py
python3 hardware/tools/check_netlist.py -v
$KPY hardware/tools/check_rules.py hardware/OpenAIO-Whoop.kicad_pcb
$KPY hardware/tools/check_rule_behavior.py hardware/OpenAIO-Whoop.kicad_pcb

# netlist, for scripted analysis
kicad-cli sch export netlist --format kicadsexpr -o /tmp/OpenAIO-Whoop.net hardware/OpenAIO-Whoop.kicad_sch

# board setup report and lineup conventions
$KPY hardware/tools/check_board_setup.py [--spec <spec.json>]
$KPY hardware/tools/check_conventions.py --stage planned
```

3D models of catalogue parts (every passive, the RP2354A, the SX1281 and
more) resolve through `OPENDRONE_LIB` = `${KIPRJMOD}/KiCad-Library` only with
the submodule initialised; without it the 3D view shows bare pads.

On macOS `kicad-cli` is at
`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`, and `pcbnew` imports
only under KiCad's bundled Python, `KPY`:
`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`.
On Linux, `bash hardware/tools/setup-agent-env.sh` installs KiCad 10 with
`kicad-cli` on `PATH`; `KPY` is `/usr/bin/python3.12`, and
`/opt/kicad-agent-venv/bin/python` is the same with kicad-skip added.
Reusable scripts for renders, STEP export, and packaging art come from Incutec
hardware tooling. The OpenDrone release standard is
[RELEASES.md](https://github.com/OpenDrone-hw/.github/blob/main/RELEASES.md).
Board-specific scripts live in `hardware/tools/`.

## Rules

Identical in every OpenDrone board repo. Do not edit here; edit the template.

- **Never text-edit** `.kicad_sch`, `.kicad_pcb` or `.kicad_dru`. Use KiCad, or
  kicad-skip / the pcbnew API for scripted changes. `.kicad_pro` is JSON and may
  be edited directly for metadata.
- **Metadata yes, connections no.** An agent may write BOM and documentation
  fields (MPN, Manufacturer, LCSC, Cost, Datasheet, text variables). An agent
  may not change nets, wiring, routing, placement, footprint assignment, or any
  value that changes the circuit.
- **Close KiCad before any write to a KiCad file.** KiCad caches library tables
  at process start and overwrites files on save.
- **Reuse before you draw.** Check the `OpenDrone` library and its
  `PARTS-USED.md` first. If the part is there we have already sourced,
  footprinted and shipped it, and its symbol links to the exact committed
  datasheet: place it from `OpenDrone`. Draw a new part into `lib` only when
  the catalogue has nothing that fits, imported with
  `easyeda2kicad` from its LCSC number. Pulling a newer catalogue is a
  deliberate, reviewed commit: `git submodule update --remote
  hardware/KiCad-Library`, then DRC.
- **One person holds a board layout at a time.** KiCad files do not merge. Say
  on Discord that you are taking it. See [CONTRIBUTING.md](CONTRIBUTING.md).
- **Run ERC and DRC before every pull request.** Existing approved findings
  may remain; a new type or increased count must be reviewed before merge.
  Commands are in Environment above.

## By task

Board-specific paths are in Environment above. `KPY` is KiCad's bundled
Python named there.

- Check the design: run the ERC and DRC commands in Environment before every pull request.
- Add a part: place it from the `OpenDrone` library if `hardware/KiCad-Library/PARTS-USED.md` lists it; otherwise import it into `lib` with `$KPY <hardware-tooling>/hardware/kicad/import_part.py` (read `--help` first), KiCad closed.
- Render the board for the README: `$KPY <hardware-tooling>/hardware/kicad/render_board.py hardware/OpenAIO-Whoop.kicad_pcb --outdir images`, KiCad closed, submodule initialised.
- Analyse the netlist: export it with the netlist command in Environment, then read it with a script; never hand-write a second BOM.
- Check lineup conventions: run `check_conventions.py` from Environment; the stage is `planned` until the repo topic says otherwise.
- Update the shared library: `git submodule update --remote hardware/KiCad-Library`, run DRC, commit as its own reviewed change.
