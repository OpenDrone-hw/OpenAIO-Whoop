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
- The board has parked parts and no tracks or vias: the 42 vias (38 microvias F.Cu-B.Cu, one F.Cu-In3.Cu, three 0.25 / 0.10 through vias) and 235 track segments of the 6-layer board were removed for the 8-layer conversion. Local rule areas and
  placement are unfinished; do not describe it as DRC-clean or manufactured.
- `bom_plan.json` and `sch_contract.json` are generated readbacks. Refresh them
  with `export_bom_plan.py` and `export_interfaces.py`; never use legacy circuit
  generators to overwrite the owner schematic from these exports.

## Layout rules

- 8 layers, HDI 1+6+1, 1.0 mm (0.997 mm stackup sum), 1 oz copper on every
  layer. L2 (In1) and L7 (In6) are solid GND planes with no tracks. L3 (In2) and
  L6 (In5) are signal layers; ESC gate and BEMF escapes go on them. L4 (In3) is the
  +BATT plane and L5 (In4) the regulated-rail plane. In2 and In5 carry no analog or
  RF; In3 and In4 carry no analog, RF, gate, gyro or VTX control nets. The DRU
  enforces the layer restrictions. Named local areas are absent until placement;
  create them using research/ROUTING.md before routing.
- HDI 1+6+1: laser microvias F.Cu-In1.Cu and In6.Cu-B.Cu only (0.25 / 0.10), buried
  vias In1.Cu-In6.Cu stacked on or staggered from them (0.33 / 0.15 in every
  net class, D126; stacking is priced as HDI II, D124), no through vias, no mechanical blind vias. Vias sit inside same-net
  pads; a free-standing via takes board space and is avoided. The stackup is
  `hardware/tools/stackup.json`, applied with `apply_stackup.py`. Decision D123
  (2026-10-13) in research/DECISIONS.md.
- `hardware/tools/setup_board.py`, `board_spec.json` and `freeroute.py` describe the
  pre-2026-10-13 6-layer board: do not run `setup_board.py` to write the project or
  rules; the 8-layer `.kicad_pro` and `.kicad_dru` are edited in KiCad Board Setup.
- RF nets carry no vias and keep 50 ohm width on the outer layers. Inside the
  `RF_VTX_STRIP` rule area (0.5 mm around the 5.8 GHz chain) only GND vias are
  allowed, so In1 (and In6 on the bottom face) stays solid under the line; `RF_PAD_CUTOUT` cuts In1 out
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
  symmetric; R2's sense taps stay Kelvin, on the outer layers.
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

- After a routing session, with KiCad closed, run `hardware/tools/hdi_via_pass.py` with KiCad's bundled
  Python: it replaces every unbuildable via (mechanical blind, multi-layer microvia, through via) with the
  minimum stack at the same spot (microvia, microvia + buried, microvia + buried + microvia), nudges
  up to 0.05 mm for clearance and lists bigger conflicts. Then run DRC.
- Edit form: `hdi_via_pass.py <board> --collapse` turns each stack into one via (front/inner/back padstack
  with the stack's lands and the buried drill), so a stack moves as one object. Move vias with Drag (D): the
  router holds clearance to other nets. Move (M) never checks DRC, and the router never checks same-net hole
  spacing. The `edit form:` rules in the .kicad_dru check an edit-form via as the stack it becomes; the next
  normal via pass rebuilds the stacks. Stacks whose microvia sits off the buried via to clear outer copper
  stay as stacks and are listed.
- Board cleanup tools (fab form, KiCad closed, DRC after each): `track_widen.py` widens tracks to the per-class
  targets in the script where clearance allows (never narrower; `--revert drc.json` undoes widened tracks DRC
  flags); `gnd_stitch.py` adds buried L2-L7 and outer microvia GND stitching where every layer has room (rerun
  adds only what is missing); then `via_declutter.py` on the DRC report removes any stitching via DRC flags.

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
