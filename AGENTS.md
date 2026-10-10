# OpenAIO-Whoop

All-in-one board for 1S whoops, the 1S sibling of
[OpenAIO](https://github.com/OpenDrone-hw/OpenAIO). `hardware/` holds the
KiCad project, still empty as created from hardware-template, and the pinned
`KiCad-Library` submodule. Product intent, targets, constraints, prior art and
the open design questions are in [README.md](README.md). They are targets, not
specifications; do not restate them here and do not describe the board as
designed.

## Repo

| | |
|---|---|
| Status | See the `status-*` topic on the repo. Never written here. |
| Designed in | KiCad 10 |
| KiCad project | `hardware/OpenAIO-Whoop.kicad_pro` |
| Shared library | `hardware/KiCad-Library/`, submodule of [OpenDrone-hw/KiCad-Library](https://github.com/OpenDrone-hw/KiCad-Library), nickname `OpenDrone`; 3D models and exact component datasheets resolve through the project text variable `OPENDRONE_LIB` |
| License | CERN-OHL-S-2.0 |

## Environment

```sh
# schematic and board checks
kicad-cli sch erc hardware/OpenAIO-Whoop.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones hardware/OpenAIO-Whoop.kicad_pcb

# netlist, for scripted analysis
kicad-cli sch export netlist --format kicadsexpr -o /tmp/OpenAIO-Whoop.net hardware/OpenAIO-Whoop.kicad_sch

# board setup report (layers, stackup, rules, presets, net classes, outline, holes)
$KPY hardware/tools/check_board_setup.py [--spec <spec.json>]
```

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
Board-specific scripts, where a board has any, live in `hardware/tools/`.

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
- Update the shared library: `git submodule update --remote hardware/KiCad-Library`, commit as its own reviewed change; run DRC once a board exists.
- Answer a design question: the open ones are listed in README "Design questions". Resolve one only as part of requested design work, then move the answer into README Constraints or Specifications.
