# IO set (D63): the IO a 1S whoop AIO usually has

**Status (2026-10-10, P4 critique round 2): superseded in part; binding over the rows below.** The set was
final on 2026-10-09 (D63 / D64) and is part of the BOM plan and the floorplan, but later decisions changed it.
Anyone who regenerates `hardware/bom_plan.json` takes these, then bom_plan and the schematic, over the old rows:

- **D65 button:** one shared button **SW1 Alps SKUBAAE010** (2.4 x 1.4 mm) for FC BOOTSEL and RX boot through
  the dual Schottky **D8 SDM02M30CLP3** (common cathode on BOOT_SW: A1 = FC_BOOT via R44 1k, A2 = RX_BOOT, ESP32
  GPIO0). Not the TS2306A on GPIO0 only, and not 'in parallel with TP11 RXB' (rows 6/10, §1 note, §6 'FC BOOTSEL
  button ... not rev1' are reversed).
- **D65 motor plugs:** plug-ready motor lands (optional Molex PicoBlade header, DNP; solder wires by default):
  §6 'motor plug-ready holes: later revision' is reversed.
- **D67 test points:** TP10 (GND), TP11 (RXB), TP14 / TP15 (USB D±) are removed; TP1-TP8 (EFM8 C2), TP9 (FCB),
  TP12 / TP13 (SWD) are mask-open filled-via test points (no silk, no TestPoint_Pad_D0.8mm pads; rows 12/13).
- **D69:** H1 / H3 (85 °C halos) and gate G3 do not exist; §4.2 site rules and the H1/H3 wording are void.
- **D76 / final refs:** **J31 = USB**, vertical JST BM04B-SRSS-TB(LF)(SN) facing up next to a mounting hole;
  **J32 = camera plug** SM03B-SURS-TF(LF)(SN) (§3 calls it J31); **J33 = LED-strip GND pad** (§3 calls it J32).

Original status line: final for rev1, gated (G1-G3 in §5); no other repo file was edited in that pass.

Date 2026-10-09. Owner request: "add all the IO a board like this usually has" (D63). Inputs:
- the IO survey of 7 analog whoop AIOs, plus 4 reference boards (§7);
- the IO proposal, and the pin and area checks of that proposal;
- [PINMAP.md](PINMAP.md), [DESIGN-SPEC.md](DESIGN-SPEC.md), [FLOORPLAN.md](FLOORPLAN.md), [DECISIONS.md](DECISIONS.md) (D55-D63 are binding);
- the v3 staging of D56-D58 (AGM cell, JST USB, Wi-Fi).

Every BLOCKER or MAJOR from the checks is either fixed here or dropped (§6). The checks found no BLOCKER. The six MAJORs:
1. Pin: the UART net swap is not needed. Dropped: D16 copper stays.
2. Pin: SBUS on a hardware UART does not work on Betaflight 2026.6.2. It is regraded, and no copper change rests on it.
3. Pin: camera pitch and pin 1. The 0.8 mm plug becomes the default, and pin 1 is fixed in gate G1, before P4.
4. Area: the IO set has to fit the board budget left after D52-D58. The per-side table is in §4, and the IO set is placed in priority order (G2).
5. Area: the camera plug and the button are 85 °C parts, so H1/H3 apply. Each gets a reserved site that meets H1/H3 (G3).
6. Area: the trade ladder. It is re-ordered, and the button is moved rather than dropped.

Tags: **V** = verified this session from a primary source or a measurement, either in this pass or by the pin and area checks (sources in §9); **S** = secondary (distributor, forum); **I** = inferred.

---

## 0. Result

- **Already on the board (kept):** battery holes, 12 motor pads, CAM/5V/GND pads, a full user UART (TP0 RP0 5V GND), the O4 pads, the LED strip and buzzer outputs, the U.FL VTX connector, the RX wire hole, the Wi-Fi chip antenna (D58), the JST SH USB (D57), 2 FC LEDs plus the RGB RX LED, V + I sense, and the FCB/RXB/SWD/C2 pads.
- **Added:** (1) a **camera plug** in parallel with the CAM pads (MUST). (2) The **LED row becomes GND LED 5V BZ-**, so the strip gets its own trio (SHOULD, +1 pad). (3) An **RX boot/bind button** on ESP32 GPIO0 (SHOULD). (4) **USB D-/D+ pads** (COULD, only if the v3 bottom has room).
- **No MCU pin moves.** The RP2354A stays at 30 of 30 GPIOs. PIO, DMA and PWM are unchanged, and F5/V9 are unchanged. D16 copper stays. Two runtime (CLI) presets cover external receivers, SBUS and I2C (§2.3).
- **Free UARTs: 2 in analog builds, the class best** (X14, CBG and RS2 also have 2). They are the user pads (PIOUART0) and the HD pads (hardware UART1, free when no O4 is fitted). HD builds have 1, plus the UART0 remap if the onboard ELRS is not used.
- **Area:** about +34-47 mm² top with the 0.8 mm plug (+51-68 mm² with the 1.0 mm fallback) and 0 mm² bottom. The board has about 20-56 mm² left in total before the IO set (§4), so G2 decides in v3.

---

## 1. Final IO set

Area = occupied incl. the 0.1 mm halo, FLOORPLAN metric; "existing" = already in the v2 placement. Areas are I unless marked.

| # | Function | Connector / pads (Manufacturer + MPN) | Signals → MCU pin / rail | Firmware config | Side, area | Priority |
|---|---|---|---|---|---|---|
| 1 | Battery | J2 `+`, J3 `-`: lib:BattPad_3.0x2.0mm_PTH1.1, plated Ø1.1 mm. No PCBA part; the BT2.0 22 AWG pigtail is a boxed accessory | +BATT_IN, GND; the VBAT sense (GPIO29) is internal | none | both sides, existing (31.6 top / 17.5 bottom, V) | MUST, kept |
| 2 | Motor outputs | J4-J15: lib:MotorPad_1.0x1.8mm_PTH0.5 with an anchor hole. Pitch per the v3 AGM cell (2.0 mm, `p2v3/staging/agm/cell`) | /ESCn/PHASE_A/B/C; DShot from GPIO25/24/23/22 (PIO0) to the EFM8s | `MOTORn_PIN` (PINMAP §5.1), Bluejay | per cell, existing | MUST, kept |
| 3 | **Camera plug (new)** | **JST SM03B-SURS-TF(LF)(SN)**: SUR 0.8 mm, 3-pin, side entry (default until G1). Fallback if G1 measures 1.0 mm: JST SM03B-SRSS-TB(LF)(SN), SH, lineup part (PARTS-USED.md:121) | Pin 1 `VIDEO_IN` → TLV7031 + SN74LVC1G3157, OSD front end (PIO2, GPIO14-16). Pin 2 GND (video return into L2, spec §11). Pin 3 `+5V_CAM` (after FB1 + 10 µF). MP → GND. Pin order provisional (MX2 pads CAM/GND/5V, V diagram; C03 lead yellow/black/red, S); G1 freezes it | none | top, interior site (§4.2); 20-32 mm² SUR (land 17.8 mm², V), 37-53 mm² SH; 0 mm of edge | **MUST** (D63) |
| 4 | Camera pads | J23 CAM, J24 5V, J25 GND: lib:SolderPad_1.0x1.2mm | same nets as #3 | none | top, inside the plug zone; existing (16.1 mm², V) | MUST, kept |
| 5 | RF | J1 Hirose U.FL-R-SMT-1(80) (VTX); AE1 plated Ø0.5 mm wire hole (RX); Wi-Fi chip antenna per D58 (v3 staging: Johanson 2450AT07A0100001T) | RF_UFL; RF_RX_ANT; ESP32 LNA_IN | ELRS auto Wi-Fi on (D58) | top / edge, D58 block | MUST, kept |
| 6 | USB | JST BM04B-SRSS-TB(LF)(SN) (vertical; the v3 USB recommendation) or SM04B-SRSS-TB(LF)(SN) (side entry; the D57 lineup part) | 1 GND, 2 USB_D_N, 3 USB_D_P, 4 VBUS → SGM40661 OVP → +5V_USB; D± through TPD2EUSB30 + 27 Ω to pins 51/52 | VCP | bottom, D57 block (31-58 mm² incl. OVP, ESD and label) | MUST (D57; not an IO-set addition) |
| 7 | User UART | J16 TP0, J17 RP0, J18 5V, J19 GND: lib:SolderPad_1.0x1.2mm | TP0 = GPIO2 (pin 4), RP0 = GPIO3 (pin 5); +5V; GND | PIOUART0: 8N1, inversion, half duplex (GPS, MSP, SmartAudio, Tramp, SmartPort). The CLI remaps it to **hardware UART0** for SBUS/CRSF receivers, or to I2C1 (§2.3) | top, existing (20.9 mm², V); D46 site | MUST, kept (D16) |
| 8 | HD pads / 2nd UART | J26 VHD, J27 GND, J28 TX1, J29 RX1: lib:SolderPad_1.0x1.2mm | TX1 = GPIO4 (pin 7), RX1 = GPIO5 (pin 8), hardware UART1; VHD = +5V_HD (live only in HD mode) | HD builds: MSP DisplayPort to the O4. **Analog builds: a free hardware UART** (the analog preset leaves UART1 at 0, PINMAP §5.4); its device takes 5V from row 7 or row 9. No half duplex. The CLI can make it I2C0 | top, existing (21.4 mm², V) | MUST, kept; 2nd-UART role SHOULD (README) |
| 9 | **LED strip + buzzer row** | **GND LED 5V BZ-**: J20 LED, J21 5V (relabelled from BZ+, same net), J22 BZ-, plus 1 new GND pad. lib:SolderPad_1.0x1.2mm_Dense | LED = GPIO8 (PIO1 WS2812, driven directly, D52 BR-04); 5V = +5V; BZ- = AP1606 drain (gate on GPIO17) | unchanged: `LED_STRIP_PIN PA8`, `PIO_LEDSTRIP_INDEX 1`, `BEEPER_PIN PA17` + `BEEPER_INVERTED` | top, inboard (§4.2); +4.8-5.4 mm² (V method) | SHOULD (reverses D27) |
| 10 | **RX boot / bind button (new)** | SW1 **SHOU HAN TS2306A 240gf MSM 9** (LCSC C2976675; lineup part, PARTS-USED.md:20). 3.0 x 2.0 x 0.6 mm, DC 15 V 20 mA, -40..85 °C (V, datasheet §1) | `RX_BOOT` (ESP32 GPIO0, pin 23) to GND, in parallel with TP11 RXB | ELRS layout key `"button": 0` (already set). Hold 1.5 s = bind, 5 s = Wi-Fi, 12 s = reboot (V, devButton.cpp:19-22). Held at power-up = download mode. Ignored while linked (V, :92-95) | top preferred, at an edge (§4.2); about 9-10 mm², no silk | SHOULD (D63 names buttons; move, do not drop) |
| 11 | Status LEDs | D5 green (GPIO7), D6 blue (GPIO26), D4 XL-1010RGBC (ESP32 GPIO22) | sink from +3V3; WS2812 | `LED0_PIN`, `LED1_PIN`; ELRS `led_rgb` | existing | MUST, kept |
| 12 | Test / programming pads | TP9 FCB, TP10 GND, TP11 RXB, TP12 CLK, TP13 DIO, TP1-TP8 C2D/C2CK: lib:TestPoint_Pad_D0.8mm | BOOT (QSPI_SS via 1 k), RX_BOOT, SWD, EFM8 C2 | production flash (F18) | bottom, existing | MUST, kept (D54 OC-4/5) |
| 13 | USB D-/D+ pads (new) | TP14 D-, TP15 D+: lib:TestPoint_Pad_D0.8mm | USB_D_N / USB_D_P on the connector side of the TPD2EUSB30 | none. README: "battery required, connect GND" | bottom, beside the USB connector, near a GND pad; 7-9 mm² | **COULD**: only if G2 shows bottom room; first to drop |

FC boot stays on the FCB pad. The bootrom also enters BOOTSEL when it finds no valid image (V, RP2350 DS §5.2.8 p.344), and Betaflight reboots into BOOTSEL from the CLI or configurator (V, system.c:144-148 at 2026.6.2).

---

## 2. Pin and net changes for PINMAP

### 2.1 Copper (old → new)

| Item | Old (PINMAP / bom_plan today) | New | Grade |
|---|---|---|---|
| RP2354A GPIO0-29 | PINMAP §2 | **unchanged**: 30/30; PIO1 23/32 instr and 3/4 SMs; DMA 8/16; PWM unchanged | V |
| ESP32 GPIO0 (pin 23) `RX_BOOT` | pad RXB (+ GND) | pad RXB **+ SW1 to GND** | V (no new pin) |
| LED / buzzer row | `LED BZ+ BZ-` (D27: the strip borrows the user 5V/GND) | **`GND LED 5V BZ-`**. J21 net stays +5V; one GND pad added | V (nets) |
| User row J18/J19 | 5V/GND, shared with the LED strip | 5V/GND for the UART device only | - |
| Camera | pads only (D18 cut 1) | pads **+ plug in parallel**: P1 VIDEO_IN, P2 GND, P3 +5V_CAM, MP GND (order frozen at G1) | I until G1 |
| USB D± | no pads (D57) | TP14 `D-` / TP15 `D+` on the connector-side nodes (COULD) | - |

The proposal's net swap was rejected: user row to GPIO4/5 (UART1), O4 pads to GPIO2/3 (PIOUART0), amending D16 (§6, row 1).

### 2.2 Text in PINMAP (no pin change)

| Line | Old | New |
|---|---|---|
| PINMAP.md:35, :70, :286 | RP0 "also SBUS-in, inverted, for a DJI remote" | "RP0: SBUS/CRSF receivers through the UART0 remap preset (§5.4); 8E2 needs a release with the uart_hw.c fix" (applied 2026-10-09, P4 critique: PINMAP §2 pin 5 row and the §5.1 config.h comment) |
| §5.4 | - | add the presets of §2.3 (applied 2026-10-10, P4 critique round 3) |
| §6, GPIO0 row | "pad RXB (+ GND)" | "pad RXB + SW1 (TS2306A) to GND; ELRS button: bind / Wi-Fi / reboot" |
| §6, `led_rgb` row | `ledidx_rgb_vtx [0]` | no VTX indication: ELRS allocates `vtxStatusLEDs` but never writes them (V, devRGB.cpp:15, :356-360; only `statusLEDs` at :75-79) |
| §4.5 or §2 | - | "U10 stepping A3 or later": RP2350-E9 (pad leakage holds a floating input near 2.2 V against the pull-down) affects A2 only, fixed in A3 (V, DS D.5.1, C.2.1). The boot-state table and the inverted-RX pull-down (uart_hw.c:261-263) rely on it |

### 2.3 Runtime presets (CLI only, README and PINMAP §5.4)

| Preset | What it does | Resources | Notes |
|---|---|---|---|
| **EXT-HD-PADS** (analog builds) | external receiver on TX1/RX1 | none moved: RX_SERIAL on UART1, UART0 mask 0 | hardware UART, so CRSF at 420 kbaud is fine. Power from the user or LED row 5V |
| **EXT-USER-PADS** (any build; also O4 + DJI remote SBUS: yellow lead → RP0) | **hardware UART0 on the user pads** | UART0 TX A00→**A02**, RX A01→**A03**; PIOUART0 TX/RX → NONE; RX_SERIAL on UART0 | V: GPIO2/3 = UART0 TX/RX (F11, DS Table 677; uart_hw.c:59, :43; aux function picked at :252/:259). The exact `resource` lines are I and are checked in V9. ELRS passthrough needs the preset undone |
| **I2C-USER** / **I2C-HD** | baro or mag on the user pads / on the HD pads (analog) | I2C1 SDA A02, SCL A03 (PIOUART0 → NONE) / I2C0 SDA A04, SCL A05 | V: pin rule (bus_i2c_pico.c:116-121). Internal pull-ups only (:455-456; RPU 32-86 kΩ, DS Table 1683), so the **module needs its own 2.2-4.7 kΩ pull-ups** (5 V pull-ups are fine on these 5 V-tolerant pads), and the I2C clock goes to 100-400 kHz (default 800 kHz, common_defaults_post.h:28) |

Caveats for any external receiver (V):
- Betaflight controls the onboard VTX only through RX_SERIAL + VTX_MSP on the CRSF port (vtx_msp.c:100; `isCrsfPortConfig` on 2026.6.2, PINMAP §5.4).
- An onboard ELRS that never links starts Wi-Fi and calls `disableVTxSpi()` (devWIFI.cpp:1488-1495, :1107), so the VTX goes dark.
- The README therefore says: external-RX users flash the onboard ELRS with `--no-auto-wifi`, and the VTX then holds its last ELRS settings (I).

SBUS (8E2, inverted):
- PIO UARTs refuse even parity (uart_pio.c:275-277), so SBUS never runs on PIOUART0.
- Hardware UARTs invert through GPIO overrides. On **2026.6.2** they still run 8N1: `serialUART_hw` reads `s->port.options` (uart_hw.c:281-282) before `uartOpen` stores them, and `uartReconfigure_hw` calls `uart_init` (:308), which writes 8N1 (pico-sdk uart.c:42-66).
- Master 498430a fixes this. So SBUS is **V on master, I on 2026.6.2**, and V9 tests it.

---

## 3. bom_plan.json additions

Refs are hints; final numbers follow LINEUP A15 when the plan is regenerated. Add `SW` to `meta.conventions.refs`.

| Ref | Role | Manufacturer | MPN | Footprint | Symbol | Qty | Side | Nets | BOM |
|---|---|---|---|---|---|---|---|---|---|
| J31 | camera plug (default) | JST | SM03B-SURS-TF(LF)(SN) | `lib:JST_SUR_SM03B-SURS-TF_1x03-1MP_P0.80mm_Horizontal`, **new**: a copy of the KiCad stock part, land 5.40 x 3.30 mm, courtyard 6.45 x 4.35 mm (V, measured). Check it against eSUR at P3 | Connector_Generic_MountingPin:Conn_01x03_MountingPin | 1 | F | 1 VIDEO_IN, 2 GND, 3 +5V_CAM, MP GND | yes; LCSC null (D60) |
| J31 (alt, G1 = 1.0 mm) | camera plug | JST | SM03B-SRSS-TB(LF)(SN) (LCSC C160403) | `lib:CONN-SMD_SM03B-SRSS-TB-LF-SN-P_W`, **new _W copy**: the OpenDrone courtyard covers the body only (5.05 x 4.30 against a 6.10 x 5.65 land, V) | same | 1 | F | same | yes |
| J32 | LED-row GND pad | - | - | lib:SolderPad_1.0x1.2mm_Dense | Connector_Generic:Conn_01x01 | 1 | F (region `pads_ledbz`) | GND; silk `GND` | no (dnp, exclude_from_bom, LINEUP A16) |
| SW1 | RX boot / bind | SHOU HAN (Shenzhen Shouhan Technology) | TS2306A 240gf MSM 9 (LCSC C2976675) | `lib:SW-SMD_4P-L3.0-W2.0-P0.85-LS3.5_W`, **new _W copy**: the OpenDrone footprint has no courtyard (V, measured; lands 3.70 x 1.44) | OpenDrone:TS2306A240GFMSM9_C2976675 | 1 | F (preferred) | RX_BOOT, GND; no silk | yes |
| TP14, TP15 | USB D- / D+ (COULD) | - | - | lib:TestPoint_Pad_D0.8mm | Connector:TestPoint | 2 | B | USB_D_N / USB_D_P | no |

**Changes to existing lines:**
- J16 note: user UART TX (PIOUART0, GPIO2; UART0-remap and I2C1 capable).
- J17 note: drop "SBUS-in inverted"; add "SBUS/CRSF via the UART0 remap".
- J18/J19 notes: drop "also the LED-strip 5V/GND".
- J20 note: drop "from the 74LVC1T45"; it is driven directly by GPIO8 (BR-04).
- J21: value and silk `BZ+` → `5V`, net +5V. The row order is GND LED 5V BZ-.
- J23-J25 notes: in parallel with J31.
- J28/J29 notes: second hardware UART in analog builds. J29: "yellow → RP0 only with EXT-USER-PADS".
- TP11 note: in parallel with SW1.
- U10 note: order stepping A3 or later (E9).

---

## 4. Area and placement

### 4.1 Budget per side (mm² free at rule clearance)

The deltas use the FLOORPLAN occupied metric, first order, about ±15 mm².

| Step | Top | Bottom | Total | Grade / source |
|---|---|---|---|---|
| v2 free area | 38.5 | 51.5 | 90.0 | V, FLOORPLAN.md:99 |
| D52 BOM reduction against the placed plan | +11.3 | -2.4 | +8.9 | V, BOM-REDUCTION.md:68 |
| D56 AGM cells, default split (ESC2/ESC4 + EFM8 on the bottom) | +49.7 | -51.9 | -2.2 | I, `staging/agm/cell/geometry_compact.json` + v2 blocks |
| D57 SH USB + SGM40661 + 100 nF + TPD2EUSB30 + label, net of the pogo pads | +2.1 | -25 to -45 | -23 to -43 | I (lands V) |
| D58 Wi-Fi antenna, match and all-layer clearance | -9 to -17 | -9 to -17 | -18 to -34 | I, Johanson layout |
| **Before the IO set** | **85-93** | **-37 to -65** | **20-56** | I. A 3/1 cell split moves about 70 from the bottom to the top, but the total binds |
| IO set, final (SUR plug 20-32, GND pad 5, button 9-10 top; D± not fitted) | -34 to -47 | 0 | -34 to -47 | I |
| **After the IO set** | | | **-27 to +22** | the 1.0 mm SH plug instead: -48 to +5 |

**Levers not on the ladder:**
- Wi-Fi clearance laid over the nose arc, tab T1 and the RF zones: 10-20 mm² (I).
- BM04B instead of SM04B: -9.2 mm² land and no edge (V: 28.6 against 37.8 mm²), if v3 lands the SM04B.
- INA186 in DSBGA (PE-13, D55): -3.6 mm² bottom.
- Owner-gated: C2 programming by fixture instead of 8 pads, 18.8 mm² (spec §9.3; reverses D54 intent).

**Trade ladder, in order (G2), with the shortfall each covers:**
1. Camera pitch per G1. SUR is already the default; the SH fallback costs +17-21 mm². Vertical BM03B only after the canopy measurement (4.25 mm + mated about 6.3 mm, where the C03 sits).
2. D± pads not fitted: they are already COULD, so nothing is booked.
3. Keep the D27 LED sharing: row `LED 5V BZ-`, the strip takes its GND from the user row. Saves 5 mm².
4. Move the button to the other side or another edge. Drop it only with owner approval (about 10 mm²).

Never traded: the CAM pads, the user row, the HD pads, the battery holes, the motor pads and USB (7/7 items).

### 4.2 Site rules for v3 (H1, H3, RF)

- **Camera plug (85 °C):**
  - Heat: H1, at least 2 mm in 2D projection from every FET group, phase pour and motor pad on either side (DESIGN-SPEC.md:1935). H3: no heat source directly under it. The v2 CAM site fails both (0.3 mm from ESC2, over the boost inductor L1, FLOORPLAN.md:224-227). The area check's candidate is an interior site in the front-right region between the ESC4 and ESC2 zones and the nose; VTX passives that are not 85 °C parts move into the H1 zones to make room.
  - RF: at least 1 mm from the 5.8 GHz line on L1 and outside RF_VTX_UFL (DESIGN-SPEC.md:1872-1873). Outside the Wi-Fi clearance. At least 6 mm from AE1 (DESIGN-SPEC.md:1960-1961).
  - Plug zone: mating face toward the nose. A `CAM_PLUG_ZONE` rule area in front of the face, about plug width x 2 mm (I; take the SUR mated length from eSUR at P3), bars every footprint except the CAM pads (D29 halo 0.5 mm, 0.7 mm to 0201/0402). Silk `CAM` + pin-1 mark inside the zone.
  - Option B, if no site exists: the orchestrator logs a scoped H1 exemption for passive mechanical parts (connector body, switch), with a V8 thermocouple check.
- **LED row:** inboard, like the HD column. With the AGM phase islands the top edge is about 73-77 of 77 mm used (I; DESIGN-SPEC.md:1855-1857 + AGM geometry). Place it near the HD column, whose 5V/GND feed a device on TX1/RX1 in analog builds. At least 6 mm from AE1.
- **Button (85 °C):** H1-clear; top preferred, because the bottom is short. Put it at an edge that a toothpick reaches with the frame fitted (MX2 uses a bottom edge, V photo). At least 3 mm from LGA (SiP, gyro), WLCSP (SGM40661) and DSBGA parts, against 240 gf flex. Outside RF_RX_EXIT (3 mm, DESIGN-SPEC.md:1553) and the Wi-Fi clearance. Unlabelled (owner silk rule; documented in the pinout).
- **D± pads:** next to the USB connector, on the connector side of the ESD array, near a GND contact. Copper only, so they may sit in an H1 zone.

---

## 5. Gates and bench items

| # | Gate | Who / when | Pass condition |
|---|---|---|---|
| **G1** | Camera pitch and pin 1 | owner/bench, **before the P3 footprint freeze and P4** | Calipers on a BetaFPV C03 lead and on an MX2 CAM IN: pin 1 to pin 3 is 1.6 mm (SUR) or 2.0 mm (SH). Photograph the housing pin-1 mark and the wire colours. Footprint, schematic pin map and pin-1 silk are fixed from that photo. With GND in the middle, a mirrored footprint puts 5 V on the camera's video output |
| **G2** | Area | v3 board agent | re-run §4.1 on the real v3 board; place in order camera plug → LED-row GND pad + button → D± pads |
| **G3** | Heat sites | v3 board agent / orchestrator | camera plug and button meet H1/H3, or a logged exemption + V8 |
| V9+ | Firmware bench | P6 | (a) SBUS via EXT-USER-PADS on the shipping release: inverted 8E2 source, frame-loss count (2026.6.2 expected to fail). (b) CRSF receiver on TX1/RX1 at 420 kbaud with the FB OSD running. (c) LED strip on the new row. (d) The existing F5 set: LED strip + FB OSD + PIOUART0 device + O4 on UART1 |
| V-btn | Button | P6 | bind at 1.5 s, Wi-Fi at 5 s, download mode at power-up, no action while linked |

README items: the pad table (rows 7-9, half duplex only on TP0/RP0), the presets and caveats of §2.3, the camera pinout with pin 1, the button functions, the D± repair note (battery fitted, GND connected), and the O4 lead map (yellow → RP0 only with EXT-USER-PADS).

---

## 6. Considered and dropped

| Item | Why | Grade |
|---|---|---|
| **UART net swap** (user row to GPIO4/5 UART1, O4 to GPIO2/3 PIOUART0, amend D16) | Not needed: GPIO2/3 run hardware UART0 by CLI (§2.3). SBUS users have already given up the onboard ELRS (one serialrx provider, pg/rx.h:32). The swap would put the O4 (the HD product mode) on the unflown PIO1 share, remove the V9 fallback (DESIGN-SPEC.md:2067, :2170) and cost the user pads their half duplex (uart_hw.c:242-245) | V |
| SH 1.0 SM03B as the camera default | C03 = "JST-0.8" (V, betafpv.com C03 page), and C03 is the camera the Matrix page recommends (V). X14 plug 0.8 mm (V, survey). The 1.0 mm case rests only on a photo length estimate (I) | demoted to fallback |
| Camera plug on an edge | top edge 73-77 of 77 mm used (I) | not rev1 |
| ELRS RGB LED as "VTX LED" | ELRS never writes `vtxStatusLEDs` (devRGB.cpp) | V |
| FC BOOTSEL button, or one FC+RX button through a dual diode (MX2 style) | no bottom room. FC recovery through the FCB pad, CLI/configurator BOOTSEL and blank-flash BOOTSEL (§1) | not rev1 |
| Motor plug-ready holes (1.25 mm, Molex 53047-0310 class) | clash with the AGM cell (pads at 2.0 mm pitch, packages 4.15 mm from the edge). PTH ring 0.15 against the 0.20 mm rule (DESIGN-SPEC.md:1233, §8.1). 1.25 mm contacts are rated around 1 A per circuit (I) against 12 A | later revision |
| Button label `BND` | owner rule: no component silk | V |
| D± pads as SHOULD | the bottom is short. The frozen outline has no rear-ear neck (MX2 uses a separate rear tab, V photo) | demoted to COULD |
| I2C pads | 0/7. CLI remap instead (§2.3) | survey |
| 3V3 pad | 0/7 analog (GK1 only) | survey |
| Extra VBAT pad | 1/7 (X14); the B+ hole serves | survey |
| SBUS pad | 0/7 analog. The user pads with EXT-USER-PADS cover it (D16) | survey |
| PINIO / camera-control pad | 0/7; the only PINIO is the internal HD line (GPIO27) | survey |
| VOUT pad | Happymodel habit only (4/7). It would put a stub on the OSD-to-VTX video node | survey |
| HD SH1.0-6 plug | only on BetaFPV's separate HD board; the O4 pads cover it (D13) | survey |
| RX / VTX cut jumpers | the ESP32 drives both, so a jumper isolates neither. The HD line already holds the VTX off (D17) | I |
| Third UART | no free GPIO. PIO1 has one free SM (simplex only). Freeing GPIO18-20 through QSPI CS1 is unflown on RP2354A and shares the XIP bus | V (PINMAP §4.1) |
| ESP32 spare GPIOs (7-10, 20, 35, 38, 39) or EFM8 spare pins as user IO | RX-side only (lean rule) / would need a Bluejay fork | I |

---

## 7. Competitor IO matrix (condensed)

The 7 analog boards:
- MX2: BetaFPV Matrix 1S 5IN1 II
- X14: Happymodel X14 ELRS 5-in-1
- X12P: Happymodel X12 ELRS Pro v1.1
- CBG: Happymodel CrazybeeG473 V1.0
- SX: Happymodel SuperX ELRS V2
- RS2: NewBeeDrone Hummingbird RaceSpec V2
- UD: FusionFPV UD 4IN1

Sources: the IO survey of 2026-10-09 (data in `scratchpad/iosurvey/`). MX2 was re-read in this pass from its connection diagram and spec (V). Cells marked (I) are the survey's own inferences.

| IO | MX2 | X14 | X12P | CBG | SX | RS2 | UD | Count | **OpenAIO-Whoop rev1** |
|---|---|---|---|---|---|---|---|---|---|
| Camera plug | 3-pin 'CAM IN', interior | 0.8 mm 3-pin | Y | - | Y (I) | Y | - | 4-5/7 | **Y** (SUR 0.8 default, G1) |
| Camera pads | Y | Y | Y | Y | Y | Y | Y | 7/7 | Y |
| Free full UARTs (+5V/GND) | 1 (UART1, hw) | 2 | 1 | 2 | 1 | 2 | 1 | - | **2 analog** / 1 HD |
| LED strip pad | 5V LED GND | Y | - | Y | - | - | Y | 4/7 | **Y** (GND LED 5V) |
| Buzzer pads | BZ- BZ+ (bottom) | Y | Y | Y | Y | - | - | 5/7 | Y (5V BZ-) |
| USB | SH1.0-4 vertical | SH1.0-4 | USB-C | SH1.0-4 | USB-C | pads + adapter | pads + adapter | 7/7 | SH1.0-4 (D57) |
| USB D± pads | Y (rear tab) | - | - | - | - | - | - | 1/7 | COULD |
| Boot / bind button | 1, shared FC+RX | pads | Y (I) | pads | pads | Y | Y (I) | 3-4/7 | **RX button** + FCB pad |
| Wi-Fi antenna | chip | n/s | n/s | n/s | n/s | n/s | n/s | 1/7 | chip (D58) |
| Motor plugs | variant | Y | Y | - | Y (V2) | - | - | 4/7 | pads + anchor holes |
| SWD / ESC programming pads | SWD | - | - | - | - | - | SWD + ESC | 2/7, 1/7 | SWD + 8 C2 |
| VBAT / VOUT / 3V3 / I2C / SBUS pads | - | VBAT, VOUT | VOUT | VOUT | VOUT | - | - | 1/7, 4/7, 0, 0, 0 | none (presets) |

n/s = not seen in the survey. Reference boards outside the 7: BetaFPV F4 1S 5A (F45A), F4 1S 12A (F412), Flywoo GOKU F405 HD 1S 5A V2 (GK1), BetaFPV Matrix 1S 3IN1 HD. They are the only ones with SBUS, 3V3 or a third UART. GK1 has BOOT + FC-BOOT buttons and BZ- next to +5V (V, Flywoo diagram).

---

## 8. Stale text to fix when this lands

D16 copper stays, so the list is short:
- PINMAP.md:35, :70, :286; §5.4 presets; §6 GPIO0 and `led_rgb` rows.
- DESIGN-SPEC.md:1235 (camera row: plug in parallel, D63), :1238 (user/HD row: SBUS text, LED group, pad count), :1239 ("no tact switch"), :1803 (D27 sharing), :1842 and :1859 (pad groups and edge demand), :158 and :1964 ("no SH1.0 part remains": SH/SUR parts now sit on both sides, so the second-side reflow EQ item changes), :1655 (connector area row), :2046 (§13 silk: GND LED 5V BZ-, CAM plug name, button unlabelled).
- DECISIONS: log D27 as superseded by D63/IO-SET. D16 and F5 stay.
- bom_plan lines in §3.

USB and pogo text (DESIGN-SPEC.md:91, :126, :1234, :1993, :2100; PINMAP.md:102-103) belongs to the D57 update.

---

## 9. Sources

- Repo files:
  - DECISIONS.md:23-26 (D15-D18), :35 (D27), :37 (D29), :56 (D46), :64 (D54), :66-71 (D56-D61), :73 (D63).
  - PINMAP.md:35, :69-72, :84, :286, §4.1, §5.4, §6, F5, F9, F20.
  - DESIGN-SPEC.md:1233-1239 (§4.10), :1553, :1855-1857, :1872-1873, :1935 (H1), :1960-1964, :2046.
  - FLOORPLAN.md:65-66, :99, :224-227. BOM-REDUCTION.md:68.
  - hardware/bom_plan.json J2-J29, TP1-TP13, U10.
  - hardware/KiCad-Library/PARTS-USED.md:20, :121; datasheet/TS2306A240GFMSM9-C2976675.pdf §1.2-1.3.
- Footprints measured this pass with pcbnew (`scratchpad/ioset_final/work/fpm3.py`):
  - KiCad stock `Connector_JST.pretty/JST_SUR_SM03B-SURS-TF_1x03-1MP_P0.80mm_Horizontal.kicad_mod` (fetched 2026-10-09 from gitlab.com/kicad/libraries/kicad-footprints).
  - KiCad stock JST_SH SM03B, BM03B and BM04B.
  - OpenDrone `CONN-SMD_SM03B-SRSS-TB-LF-SN-P` and `SW-SMD_4P-L3.0-W2.0-P0.85-LS3.5`.
- Betaflight 2026.6.2 (e0b7bb0), https://github.com/betaflight/betaflight/tree/2026.6.2:
  - read in this pass: `src/platform/PICO/uart/uart_hw.c:43, 59, 86, 102, 242-263, 281-282, 308`; `uart_pio.c:275-277, 288`; `bus_i2c_pico.c:116-121, 455-456`.
  - checked by the pin check: `serial.c:69-140`; `vtx_msp.c:100`; `system.c:144-148`; `common_defaults_post.h:28`; `pg/rx.h:32`; `config.c:568-580`.
  - master 498430a: the uart_hw.c options fix.
  - pico-sdk ee68c78 `uart.c:42-66`.
- ExpressLRS 15c7899: `src/lib/BUTTON/devButton.cpp:14-23, 92-95` (https://github.com/ExpressLRS/ExpressLRS/blob/15c78990e7eac43c110fd43cd9823ec70fa8220d/src/lib/BUTTON/devButton.cpp#L14-L23); `devRGB.cpp:15, 75-79, 356-360`; `devWIFI.cpp:1107, 1488-1495`.
- RP2350 datasheet (local copy `research/05-dl/ds/rp2350.txt`): Table 677 (GPIO functions); Table 1683 (RPU); §5.2.8 p.344; D.5.1 and C.2.1 (E9).
- BetaFPV:
  - Matrix 1S 5IN1 II spec, connection diagram and photos: betafpv.com/products/matrix-1s-5in1-ii-brushless-flight-controller; cdn.shopify.com/s/files/1/1778/6615/files/Matrix_1S_5IN1_II_Brushless_Flight_Controller_{connection_diagram, top_front_gyro_update, bottom_front, solder-free_and_solder_required}.jpg.
  - C03 camera ("features a JST-0.8 connector"): betafpv.com/products/c03-fpv-micro-camera.
  - Air65 II (Matrix II + C03): betafpv.com/products/air65-ii-brushless-whoop-quadcopter.
- Other boards:
  - Happymodel product pages (`iosurvey/hm/*.json`).
  - NBD RaceSpec V2 and GOKU F405 HD 1S pages (`iosurvey/nbd/`).
  - FusionFPV UD 4IN1 (https://fusionfpv.com/aio/).
  - Flywoo GOKU diagram img-va.myshopline.com/image/store/1673593876355/5-80.jpg (`iosurvey/fw/goku1s_diag.png`).
- JST SUR SM03B-SURS-TF(LF)(SN): futureelectronics.com listing (S); eSUR.pdf (`scratchpad/ioprop/dl/`).
- Area figures: the area check (`scratchpad/ioarea/`), the v3 staging (`scratchpad/p2v3/{agm_work, usb, wifi_work}/STATE.md`, `staging/usb/parts.json`).
