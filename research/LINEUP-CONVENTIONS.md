# Lineup conventions

How an OpenDrone board looks and is laid out, extracted so OpenAIO-Whoop fits
the line exactly. Machine-checkable rules are enforced by
`hardware/tools/check_conventions.py` (rule ids match); the rest are for review.

**Sources** (shallow clones, 2026-10-06): `.github` 722af54 (CONTRIBUTING,
RELEASES, `engineering/*.json`), `OpenDrone-Brand` cd211e5, `hardware-template`
53209c1, and the boards OpenFC-Lite 11bd564, OpenFC-Lite-Mini 1cdcc32,
OpenESC-20x20 4ba8244, OpenESC-30x30 682268f, OpenRX-Lite d318788 (all rev3.3 or
rev2, alpha, OSHWA-certified) and OpenAIO 9968ebb (in progress). Schematics were
exported to PDF and boards read with pcbnew; README renders were inspected.

**Tags.** MUST / SHOULD as usual. **[R]** read in a written standard,
**[E]** empirical (what the shipped files do, with the count), **[I]** inferred.
Where boards disagree, the canonical choice is the newest written source
(template, CONTRIBUTING), then the boards that follow it most closely
(OpenFC-Lite and OpenFC-Lite-Mini, which also pass the checker almost clean).
**(c)** marks rules the checker enforces.

## A. Schematic

1. **Root sheet** MUST be `hardware/<project>.kicad_sch` (c). SHOULD hold only
   sheet symbols and the wiring between them, each sheet symbol carrying a bold
   2.54 mm list of what is inside (`5V BUCK / 10V BUCK / 3V3 LDO ...`).
   [E] FC boards: root has 0 parts, 6 sheets. ESC and OpenAIO also put shared
   parts on the root; the FC form is canonical.
2. **One sub-sheet per function**, files MUST be lower-case snake_case named for
   the function or the load-bearing IC (c): `power`, `pads`, `imu`, `osd`,
   `blackbox`, `rp2350a`, `esc_channel`, `rx_esp32c3_sx1281`. A repeated stage is
   one file instantiated N times (`ESC1`..`ESC4` -> `esc_channel.kicad_sch`).
   A sheet copied from another board keeps its file name. [E] 6/6 FC files,
   OpenAIO 5/5; ESC's `ESC.kicad_sch` is the one legacy exception.
3. **Sheet names** SHOULD be short function names, upper case on the FC family
   (`POWER`, `PADS`, `RP2350A`), numbered for instances (`ESC1`). [E] FC; OpenAIO
   mixes `Pads`/`RX Mono`.
4. **Paper** sized to the content per sheet (A5 IMU/blackbox, A4 power/pads,
   A3 OSD/RX, A2 MCU); KiCad's default page layout, no custom `.kicad_wks` (c).
   [E] all boards.
5. **Title block** MUST carry, on every sheet (c): the OpenDrone wordmark above
   the default KiCad title block, a one-line title describing the sheet, the
   date and the rev. [E] every sheet of every alpha board except
   OpenFC-Lite-Mini `blackbox` (a gap, see Conflicts). The wordmark is nine
   filled polylines (4 "Open", 5 "Drone"), 63.5 x 11.45 mm, its bottom-left
   corner about 88.6 mm left of and 20 mm above the frame's inner bottom-right
   corner (A4: x 198.4-262.0, y 168.3-179.9). Shipped sheets type title, date
   and rev as free text, 1.778 mm bold black, over empty `title_block` fields;
   company is empty because the wordmark fills that cell.
   - For a new board SHOULD use the `title_block` fields themselves (KiCad
     prints them in the same cells, and they are machine-readable) [I]; the
     checker accepts either.
   - Wordmark colour: shipped art uses black + `#c89d2e`, which
     `OpenDrone-Brand/standards/deprecations.json` retires. The current on-light
     artwork (`wordmark/opendrone-wordmark-onlight.svg`) has the same nine paths
     in `#1a1a1e` + `#ffb700`. SHOULD use the current values [R BRAND.md "use
     the supplied light/dark artwork"]; owner decision, see Conflicts.
6. **Sheet rev** SHOULD equal the board rev and the date SHOULD be ISO
   `YYYY-MM-DD` (c, warn). [I] Shipped sheets say `Rev 2` / `06/06/2026` on
   rev3.3 boards, i.e. never updated; the Revisions tables use ISO dates.
7. **Text**: KiCad default font only (c); body 1.27 mm (`default_text_size` 50
   mil in every `.kicad_pro`), block headings bold 2.54-5.08 mm. [E] no `face`
   in any schematic.
8. **Libraries**: symbols MUST come from `OpenDrone`, the local `lib`, or KiCad
   stock libraries; no PCM (`PCM_*`) or personal/legacy aliases (c).
   Generic R/C/L/LED use KiCad's `Device`. [R] CONTRIBUTING "Parts", template
   AGENTS "Reuse before you draw". FC boards comply; ESC (`ESCLibrary`,
   `components`, `PCM_*_AKL`), RX (`OpenRX-Shared`) and OpenAIO carry legacy names.
9. **BOM fields**: every BOM symbol MUST have `MPN`, `Manufacturer` and `LCSC`
   (c). [R] CONTRIBUTING ("every orderable component needs Manufacturer and
   MPN", LCSC when available) + README constraint (LCSC assembly). [E] 100% on
   all alpha boards. OpenAIO-Whoop (D60, NextPCB turnkey by MPN; P4 integration
   2026-10-09): `MPN` + `Manufacturer` MUST, the `LCSC` field MUST exist and is
   filled where the part has an LCSC number; `check_conventions.py` A9 checks the
   fields, `check_netlist.py` N3 checks the LCSC values against `bom_plan.json`.
10. **Datasheet**: symbols placed from `OpenDrone` keep
    `${OPENDRONE_LIB}/datasheet/<file>.pdf`; no absolute or user-local paths
    (c). Generic primitives need none; a `lib` part may link the LCSC/maker PDF
    URL. [R] CONTRIBUTING, KiCad-Library README "Path contract". Shipped boards
    predate it: their fields are empty or LCSC URLs.
11. **Power symbols**: power nets MUST be `+`-prefixed rails or `GND` (c); the
    battery rail is `+BATT`. SHOULD follow the template's `net_colors` style
    `+<volts>V[_SUFFIX]` with a decimal point: `+3.3V`, `+5V`, `+10V`,
    `+1.8V_GYRO`, `+5V_USB`, `+5V_BUCK`, `+1.1V` (c, warn). [R] template
    `board.kicad_pro`; [E] FC uses that style but also `+4v5`; ESC/RX use `+3V3`.
12. **Labels**: local and hierarchical only, MUST NOT use global labels (c);
    names upper case `[A-Z0-9_+-./]` (c): `UART1_TX`, `MOTOR1`, `GYRO_INT`,
    `10V_ENABLE`, `BUZZER-`, `D+`. Buses `SPI0{SCK,MOSI,MISO}` with members
    `SPI0.SCK`. [E] 0 global labels on any alpha board; FC and RX 100% upper case;
    ESC `dshot`, `MotorA`, `vdda` are the exceptions.
13. **PWR_FLAG** SHOULD sit on every externally fed rail (`+BATT`, `+5V_USB`,
    `GND`) so ERC is clean. [I] Only OpenRX-Lite does it; the FC boards carry
    approved `power_pin_not_driven` errors instead, and a new board has no
    approvals (C9).
14. **No-connect flags** on every unused pin. [E] FC `rp2350a` 9-23 flags; ERC.
15. **Annotation**: project-wide sequential, unique, fully annotated (c); no
    per-sheet number offsets; standard prefixes (C R L D U Q X, J connectors and
    solder pads, TP test points, AE antenna, FL filter). [E] KiCad annotation
    method 0, start 0 in every project; FC refs run C1..C46 across sheets.
16. **Solder pads** are `Connector_Generic:Conn_01x01`, ref `J<n>`, footprint
    `lib:small_pad` (or `OpenDrone:SolderPad_*`), excluded from BOM and DNP;
    test points `Connector:TestPoint` `TP<n>`, out of the BOM (c, warn). Pads are
    grouped under a small blue heading per function ("RX pads", "Camera + VTX",
    "Free UART (GPS)"). [E] FC `pads` sheet 50/50; OpenRX-Lite keeps its 5 pads
    in the BOM (exception).
17. **Notes on the sheet**: functional blocks boxed with a rectangle and a bold
    heading; design calculations written next to the parts (divider formulas,
    "LMR51430 = 3 A / LMR51420 = 2 A, pin compatible"). [E] FC `power`,
    `rp2350a`.

## B. Board

1. **Stackup and layers**: line standard by `check_board_setup.py` +
   `board_spec.example.json` (6 copper, 0.09/0.09, via 0.35/0.20). SHOULD use
   FC layer roles F sig / In1 GND / In2 sig / In3 PWR / In4 GND / B sig, written
   as a copper text per layer outside the outline (`LN1 = GROUND`). [R] template
   `info.html`; [E] FC boards.
2. **No "Drone" on anything fabricated**: copper, mask or silkscreen, resolved
   text (c). [R] every alpha board's Revisions, rev3.3: "Silkscreen rebranded
   OpenDrone -> incutec for export restriction reasons on flagging anything
   containing 'Drone'". Off-board notes on user layers ("front side of drone")
   are not fabricated and may stay.
3. **Logo**: the incutec logo MUST be on silkscreen (c): the same 8-polygon
   artwork, aspect 4.36:1, on F or B. Sizes shipped: 6.1 x 1.4 mm (Mini front),
   7.1 x 1.6 and 8.6 x 2.0 (ESC back), 15.0 x 3.4 (FC-Lite front). No OpenDrone
   wordmark or OD mark on the board [E + B2]; the brand's 25 mm print minimum
   for the wordmark could not be met at this size anyway [R BRAND.md]. Boards
   under 15 mm (OpenRX-Lite) omit logo and rev (checker: warn).
4. **Product name** MUST appear (c): `OPEN` plus the product word, in Tokyo, on
   the back: `OPEN / FC / LITE / MINI` stacked (2.0-4.0 mm), or `OPEN` in silk +
   the type as exposed gold through a mask opening (`ESC`, `RX` on B.Mask).
   [E] 4/5 alpha boards; OpenESC-30x30 has none (gap).
5. **Revision on silk** MUST equal the title-block rev (c): `REV3.3`, 1.0-1.8 mm,
   on the back. [E] 4/5 (not OpenRX-Lite).
6. **Board title block** MUST carry the rev as `rev<N>[.<M>]` (c), lower case,
   and nothing else is needed (title, company, date empty on all alpha boards).
   [E] `rev3.3` x4, `rev2`; matches tags and archive names (C6, C10).
7. **Pad labels**: every user solder pad MUST have a silk label within 1 mm (c),
   Tokyo bold upper case, 1.2 mm high (back 1.0 mm), on the pad's side:
   `GND 5V 4.5V 10V 3V3 TX1 RX1 TP0 RP0 SDA SCL LED CAM VTX BAT CUR M1-M4 B+ B-
   BOOT`. Component call-outs (`5V BUCK`, `GYRO`, `STATUS`) 0.9-1.2 mm. Flashing
   test points (ESC SWD) may stay unlabelled. [E] FC 34/34 and 53/53, RX 5/5.
8. **Battery** `+`/`-` (or `B+`/`B-`) MUST be labelled where a battery net
   exists (c); ESC style is a 4-6 mm `+` and `-` beside the pads. [E] all.
9. **Motors** MUST be numbered 1-4 on silk where there are motor outputs (c):
   `M1`..`M4` on FC pads, or 2.0 mm digits in silk circles at the corners on the
   ESC, mirrored copy on the back. Betaflight quad-X order with the connector at
   the front: 4 front-left, 2 front-right, 3 rear-left, 1 rear-right. SHOULD
   add the FC's forward arrow (0.3 mm silk lines) and a `User.Eco2` note marking
   the front. [E] ESC 20x20/30x30, FC.
10. **Reference designators** MUST be hidden on silkscreen (c); they stay on Fab.
    [E] 0 visible of 47-285 per board.
11. **Silk text size** MUST be at least the NextPCB minimum for the outer copper
    and the project's `min_text_height` (c): 1 oz 0.76 mm high / 0.12 mm line,
    2 oz 1.07 / 0.18 mm, 3 oz 1.27 / 0.30 mm ([NextPCB
    capabilities](https://mobile.nextpcb.com/pcb-capabilities)); pad clearance
    0.15 mm is the canonical `.kicad_dru` rule. [E] smallest shipped: 0.9 mm
    (Mini, 1 oz), 1.5 mm (ESC, 2 oz).
12. **Font**: silkscreen SHOULD be the Tokyo outline font (c, warn); pad labels
    bold. Tokyo is not embedded in any board and is not installed here (KiCad
    substitutes Inter): the whoop SHOULD embed it (KiCad 10 embedded fonts) so
    the Gerbers do not depend on one machine. [E] 100% of silk text; [I] embed.
13. **Back text mirrored**, front not (c). [E] KiCad DRC class; OpenESC-20x20
    carries one approved exception.
14. **Mask and finish**: vias tented both sides (c) [E all + template]. Mask
    green [R tokens `color.brand.green-deep`, "PCB solder-mask green"; E
    renders]; ENIG [E renders gold on all, ESC stackups say ENIG]. Neither is
    set in the KiCad stackup of most boards; SHOULD set both explicitly [I].
15. **Outline**: no sharp outside corners; fillets 0.3-0.9 mm, rounded-rect
    0.45 mm on the RX. Mounting holes 3.0 mm on 20 x 20 (and OpenAIO's 25.5 mm
    outline), 4.0 mm on 30.5 x 30.5: FC as non-plated Edge.Cuts circles with a
    2 mm silk ring, ESC/AIO as plated GND holes in the outline footprint
    (`4in1ESC`, `OpenDrone:AIO_outline`). User layers: `User.Eco1` mounting
    pattern guides, `User.1` hole keepouts. [E]
16. **No fiducials or rails** in the board file; panels are their own project
    (`OpenRX/panel/`, `OpenESC-30x30/hardware/4in1-panel`). [E] 0 fiducials.
17. **3D models** MUST resolve through `${KICAD10_3DMODEL_DIR}` (stock),
    `${OPENDRONE_LIB}/3dmodel/` (catalogue) or `${KIPRJMOD}/` (local), and exist
    (c) [R RELEASES step 2 "block missing or invalid 3D models"]. The fixes in
    `.github/engineering/model-fixes.json` (EasyEDA SOT-23 `-BL`/`-BR`, USB-C,
    TF card) MUST be applied (c, `--model-fixes`). OpenESC boards still point
    some models at `${KICAD9_3DMODEL_DIR}`.
18. **Renders** from alpha: `images/front.png`, `images/back.png`, 1568 x 1568
    RGBA, transparent, orthographic, made with Incutec's
    `render_board.py ... --outdir images` (c at alpha). [R template AGENTS
    "By task"; E all alpha repos]. Packaging board art in
    `OpenDrone-Brand/board-art/<repo-lower>-front|back.svg` is generated from the
    board by `packaging_art.py`; it is not drawn in the board repo.
19. **Footprints** from `OpenDrone`, `lib` or KiCad stock only (c). [R as A8]

## C. Project files

1. **Layout** MUST match CONTRIBUTING "Repository structure" (c): KiCad project
   exactly one level down in `hardware/`, `<project>.kicad_{pro,sch,pcb,dru}`,
   project-local `fp-lib-table`/`sym-lib-table`, `lib.kicad_sym`, `lib.pretty/`,
   `lib.3dshapes/`, `fabrication-toolkit-options.json`, the `KiCad-Library`
   submodule, `tools/`; root `README.md AGENTS.md CONTRIBUTING.md LICENSE
   .gitignore .gitattributes images/`. Project name SHOULD equal the repo name
   [E newest boards; the two `OpenFC` projects are the known hazard].
2. **`OPENDRONE_LIB`** text variable MUST be `${KIPRJMOD}/KiCad-Library` (c). [R]
3. **`DOC_*` text variables** MUST exist from alpha (c, `--stage alpha`):
   `DOC_NAME` (= repo), `DOC_HANDLE` (= repo, lower case), `DOC_TAGLINE`,
   `DOC_FIRMWARE`, `DOC_PROTOCOL`, `DOC_MCU`, `DOC_INPUT`, `DOC_RATING`,
   `DOC_VARIANT`. [E] all 5 alpha boards, none of the planned/in-progress ones.
4. **Library tables** MUST list exactly `lib` and `OpenDrone`, `${KIPRJMOD}`
   relative (c). [R CONTRIBUTING, template]
5. **`.kicad_dru`**: the canonical block byte-identical to the template, board
   rules only below the marker (c checks rule + marker). [R template]
6. **Fab config**: `fabrication-toolkit-options.json` MUST exist with
   `ARCHIVE_NAME = <Repo>-rev<N>` matching the board rev (c). [R CONTRIBUTING
   commit list; E all alpha boards consistent]
7. **Board setup**: line standard, verified by `check_board_setup.py`. [R]
8. **Net classes**: the template defines only `Default` (standardising is open
   work, `info.html`); if the whoop adds classes SHOULD reuse OpenAIO's names
   (`Power`, `VBAT`, `Phase`, `Gate`, `Analog`, `RF`, `USB`). [I]
9. **Approved findings**: a board's ERC/DRC findings are approved per board key
   `<Repo>/hardware/<project>` in `.github/engineering/approved-violations.json`;
   "approval is never inferred from an earlier board". OpenAIO-Whoop has no
   entry, so every finding type it reports needs a maintainer's review before
   release. Target ERC/DRC clean. [R RELEASES]
10. **Release outputs**: one revision = one `rev*` tag and release, assets
    `<Repo>-<rev>-fab.zip`, `<Repo>-<rev>.step`, `<Repo>-<rev>-schematic.pdf`;
    preparation order ERC/DRC compare, 3D model check, fab set, STEP, schematic
    PDF. Fab-ready production files live in Incutec's private repository.
    [R CONTRIBUTING, RELEASES, README]
11. `.gitignore`/`.gitattributes` copied from the template. [R]

## D. Docs

1. **README section order** MUST follow the template (c). Planned: title,
   paragraph, Status + Discord badges, `Why`, `Specifications`, `Constraints`,
   `Prior art`, `Design questions`, `In the line`, `Contributing`, `License`.
   Alpha: title, one paragraph ("..., part of the incutec OpenDrone line"),
   front/back renders at width 400, badges Status, Shop, Discord, Video, OSHWA,
   `Specifications` + "Technical write-up ...: AGENTS.md", `In the line`,
   `Contributing`, `License`; the planned-only sections go. Extra sections are
   flagged (warn). [R template README, CONTRIBUTING]
2. **Specifications** MUST be the first table under `## Specifications`, two
   columns, header `| | |`, plain ASCII, one fact per row (`2-6S`,
   `20 x 20 mm`, `4x DShot`) (c): the site imports it. [R CONTRIBUTING]
3. **AGENTS.md** sections MUST follow the template order, omitting what does
   not apply (c): Architecture, Power, Key parts, Connectors and I/O, Layout
   rules, Firmware, Repo, Parts and datasheets, Environment, Rules, Revisions,
   By task; the Rules section verbatim (c checks the six lead-ins). No status,
   plans, TODOs or sourcing. [R template AGENTS]
4. **Status badge** MUST point at `opendrone.be/api/status/<Repo>.json` (c);
   Shop and OSHWA badges from alpha (c). [R]
5. **Revisions**: table `| Rev | Date | Change |`, ISO dates, newest first; rev
   names `rev<N>[.<M>]` as in tags (shipped tables mix `Rev3.3`, `Rev 3.1`,
   `rev2`; OpenFC-Lite-Mini drops the Date column). [R template; E]

## Applying this to OpenAIO-Whoop

- **Schematic**: root `OpenAIO-Whoop.kicad_sch` with sheet symbols only.
  Sub-sheets keep the names of the sheets they reuse: `rp2350a`, `imu`, `osd`,
  `blackbox` (OpenFC-Lite-Mini), `rx_esp32c3_sx1281` (OpenAIO), `esc_channel`
  x4 as `ESC1`..`ESC4`; new ones `power`, `vtx`, `pads`. Every sheet gets the
  wordmark polylines copied from an FC sheet at the same offset from the title
  block, with title/date/rev in the `title_block` fields.
- **Clean up the copies** as they come in: rename `+3V3` to `+3.3V` and decide
  on `+4v5` -> `+4.5V` in copied sheets; upper-case `dshot`, `MotorA..C`,
  `vdda` in `esc_channel`; re-point `components`, `ESCLibrary`, `PCM_*`,
  `OpenRX-Shared`, `4in1ESC` symbols and footprints to `OpenDrone` or `lib`;
  fill `Manufacturer` (OpenAIO's `esc_channel` lacks it on 33 parts).
- **Project files now**: copy `fabrication-toolkit-options.json` with
  `ARCHIVE_NAME` `OpenAIO-Whoop-rev1`; set the board title-block rev to `rev1`
  (the scaffold has `0.1`); add `images/` with the template placeholders.
- **Silkscreen at whoop density.** The board is about the size of
  OpenFC-Lite-Mini (27.3 mm), so that board is the density reference.
  - Mandatory: every solder pad labelled (B+ B-, motor pads by motor number,
    5V/3V3/GND, CAM, LED, BZ, spare TX/RX, BOOT/bind), motor numbers 1-4 in
    Betaflight order with a forward arrow, `+`/`-` at the battery pads, `REV1`,
    the incutec logo, `OPEN` + `AIO` (+ `WHOOP`) in Tokyo, no "drone" anywhere.
    A `1S` mark beside the battery pads follows the ESC's cell-range marking
    (`2-6S`) and matters more here than anywhere [I].
  - Text height: 1.2 mm bold for pad labels, 1.0 mm floor on the back. NextPCB's
    floor is 0.76 mm at 1 oz and 1.07 mm at 2 oz outer copper; if the stackup
    goes to 2 oz, raise the project's `min_text_height` to 1.07 so DRC enforces
    it, and drop the 0.9 mm call-out size.
  - Logo: no smaller than 6.1 x 1.4 mm (the Mini's). At that size its thinnest
    feature, the stem of the i, is 0.23 mm (measured on OpenFC-Lite-Mini), above
    NextPCB's 0.18 mm line for 2 oz; smaller and it is not [I]. Put it on
    whichever side has a free 7 x 2 mm patch; the back takes the product name
    and REV.
  - Refdes off, back text mirrored, Tokyo embedded, mask green, ENIG, tented
    vias, rounded outline corners.
- **Gate**: `check_conventions.py` with no FAIL from P3 on;
  `--stage alpha --model-fixes <.github>/engineering/model-fixes.json` from
  the first produced revision.

## Conflicts between brand docs, standards and shipped boards

1. **Identity on the board.** BRAND.md makes the OpenDrone wordmark the primary
   identity; since rev3.3 every board carries only incutec on silk (export
   flagging of "Drone"). Schematics still carry the OpenDrone wordmark. Treated
   as: OpenDrone on schematics and docs, incutec on copper.
2. **Schematic wordmark gold** `#c89d2e` is retired in
   `standards/deprecations.json`; the current on-light artwork is `#1a1a1e` +
   `#ffb700`. Copying the shipped art matches the line, recolouring matches the
   brand. Needs the owner's call; the checker accepts both and warns on the old.
3. **CONTRIBUTING vs boards**: `${OPENDRONE_LIB}` datasheets, `lib`+`OpenDrone`
   only tables, and no global libraries are written policy that ESC, RX and
   OpenAIO files predate (legacy aliases, `PCM_*`, `${KICAD9_3DMODEL_DIR}`).
4. **Template vs boards on power names**: template `+3.3V`; ESC/RX `+3V3`;
   FC/OpenAIO `+4v5`.
5. **Schematic metadata is stale**: sheet revs say 2 (or 1) on rev3.3 (rev2)
   boards, dates are DD/MM/YYYY; the PCB title block and archives say `rev3.3`.
6. **Board gaps**: OpenFC-Lite-Mini `blackbox` sheet has no wordmark;
   OpenESC-30x30 has no product name on silk; OpenESC-20x20 has a mirrored
   front text (approved DRC warning); OpenRX-Lite keeps pads in the BOM.
7. **Docs vs files**: OpenFC-Lite and -Mini READMEs say 1.6 mm, both board files
   say 1.0 mm; OpenAIO AGENTS says 6 layers 2 oz outer, its board has 8 layers of
   1 oz. The template's `netclass_patterns` assign `/ELRS/...` nets to a `50Ohm`
   class it does not define.
8. **Tokyo font** is used for all silkscreen but not embedded anywhere, so a
   Gerber export on another machine silently changes the silkscreen.

## Checker results (2026-10-06)

`/usr/bin/python3.12 hardware/tools/check_conventions.py <pro> --stage alpha --model-fixes <.github>/engineering/model-fixes.json`

| Board | FAIL | What fails |
|---|---|---|
| OpenFC-Lite | 0 | warns only: old gold, stale sheet rev/date, `+4v5`, font not embedded |
| OpenFC-Lite-Mini | 1 | A5 `blackbox.kicad_sch` has no wordmark (real gap) |
| OpenRX-Lite | 4 | C1/C4/A8/B19 legacy `OpenRX-Shared` library instead of `lib` |
| OpenESC-20x20 | 8 | legacy libs and tables (C1 C4 A8 B19), `ESC.kicad_sch` (A2), lower-case labels (A12b), `${KICAD9_3DMODEL_DIR}` (B17), mirrored front text (B13) |
| OpenESC-30x30 | 8 | as 20x20 but no mirrored text; no product name on silk (B4) |
| OpenAIO (planned) | 13 | in progress: no silk art, empty rev, legacy libs, a global label, missing `Manufacturer` |
| OpenAIO-Whoop (empty) | 4 | no fab config (C1, C6), no schematic wordmark (A5), board rev `0.1` (B6) |

No failure on the shipped boards pointed at a wrong rule. Two rules were
corrected while validating: logo and rev on silk are SHOULD below 15 mm
(OpenRX-Lite), and bare pads are a BOM-exclusion question (A16), not missing
part numbers (A9).
