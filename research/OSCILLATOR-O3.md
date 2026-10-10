# O3 / D99(a): 12 MHz CMOS oscillator on RP2354A XIN instead of X1 + C42 + C43 + R40

Research only. No repo edits. Date 2026-10-10.

## Verdict

**Accepted.** The RP2350 datasheet, the hardware design guide, the bootrom source and pico-sdk all support a
single-ended 12 MHz CMOS clock on XIN with XOUT left open. BOOTSEL (USB and UART) works with it as it is, with no OTP
programming. The 48 MHz USB PLL setup is the same as with a crystal, and Betaflight needs no change.

## 1. Primary-source evidence

### RP2350 datasheet (Release 8, build 80d627281ed5, 01/10/2026)

| Where | What it says |
|---|---|
| §1 pin description (XIN and XOUT) | "XIN can also be used as a single-ended CMOS clock input, with XOUT disconnected. The USB bootloader defaults to a 12 MHz crystal **or 12 MHz clock input**, but this can be configured via OTP." |
| §8.2.1 Overview | "External signals can also be driven directly into XIN." / "If the user already has an accurate clock source, it is possible to drive an external clock directly into XIN (aka XI), and disable the oscillator circuit. In this mode XIN can be driven at up to 50 MHz." |
| §8.2.2 Note | "When using the XOSC XIN pin as a CMOS clock input from an external oscillator, the maximum is always 50 MHz. You **do not have to configure CTRL.FREQ_RANGE for the CMOS input case**. The CMOS input behaviour is the same as RP2040." |
| §8.2.3 / §8.2.4 | The XOSC is off at reset. Software sets CTRL.ENABLE. STATUS.STABLE is set after STARTUP.DELAY × 256 cycles **seen on the XOSC input**. A driven XIN supplies those cycles. |
| §8.2.7 Tables 631-634 | CTRL has only ENABLE and FREQ_RANGE. There is no bypass bit. STARTUP.DELAY and X4 reset to mask-programmed values. |
| §5.2.8.1 BOOTSEL clock requirements | "BOOTSEL mode requires either a crystal attached across the XIN and XOUT pins, **or a clock signal from an external oscillator driven into the XIN pin**." The bootrom assumes 12 MHz and sets the USB PLL to 48 MHz. OTP (BOOTSEL_PLL_CFG / BOOTSEL_XOSC_CFG) is needed only for a frequency other than 12 MHz. |
| §5.8.1 UART boot | "you must either provide a crystal or drive a stable clock into the crystal oscillator XIN pad". |
| §14.8.2 Table 1676 | XIN (QFN-60 pin 21): "XIN may also be driven by a square wave". XIN and XOUT are in the IOVDD domain. |
| §14.9 Table 1686 (Oscillator pin characteristics) | fosc 1 / 12 / 50 MHz. **VIH min 0.65 × IOVDD, max IOVDD + 0.3 V; VIL max 0.35 × IOVDD**, "Square Wave input. XIN only. XOUT floating". Note: "By default, USB Bootmode relies on a 12 MHz input being present." |
| Errata (RP2350-E1 to E31) | None mentions the XOSC, XIN or the crystal. |

XIN levels at IOVDD = 3.3 V: VIH ≥ 2.145 V, VIL ≤ 1.155 V, maximum 3.6 V. The oscillator below gives VOH ≥ 90 % VDD
(2.97 V) and VOL ≤ 10 % VDD (0.33 V). It runs from the same +3V3 rail as IOVDD, so it cannot exceed IOVDD + 0.3 V and
cannot back-power the chip during the power ramps.

### Hardware design with RP2350 (Release 3, build 06a7f75e58a1, 20/08/2026), §4 Crystal Oscillator

"Providing an external frequency source can be done in one of two ways: either by providing a clock source with a CMOS
output (square wave of IOVDD voltage) into the XIN pin, or by using a 12 MHz crystal connected between XIN and XOUT.
Using a crystal is the preferred option here, as they are both relatively cheap and very accurate."

The guide prefers the crystal for cost only, not because the CMOS input is a problem. The crystal text then asks for
"extensive testing" whenever the crystal circuit differs from the reference (crystal choice, the 1 kΩ, IOVDD). DS
§8.2.1.1 says the same: "test the circuit over a range of temperatures". An oscillator removes that whole
start-up-margin question, which was the D78 worry.

**Raspberry Pi reference design with an oscillator:** none found. The guide's minimal design and the Pico 2 both use
the ABM8-272-T3 crystal. The CMOS option is documented in text only (the DS rows above and guide §4), and DS §8.2.2
says it behaves the same as on RP2040.

### Bootrom source (github.com/raspberrypi/pico-bootrom-rp2350 @ c6cdb17, `src/main/arm/varm_nsboot.c`, `s_varm_nsboot_clock_setup`)

- With no OTP override, the bootrom writes only `xosc_hw->ctrl = XOSC_CTRL_ENABLE_VALUE_ENABLE << ...`. FREQ_RANGE and
  STARTUP keep their reset values. It then spins on `while (!(xosc_hw->status & XOSC_STATUS_STABLE_BITS));`.
  - STABLE counts input cycles, so a driven XIN satisfies it the same way a running crystal does.
  - DS §8.2.2 says FREQ_RANGE does not matter for a CMOS input.
- The default USB PLL setting is REFDIV 1, FBDIV 100 (VCO 1200 MHz), POSTDIV 5 × 5, giving 48 MHz for clk_sys and
  clk_usb. The bootrom accepts lock only after 255 consecutive LOCK reads. The comment explains why: "PLL may
  intermittently report lock when XOSC is just floating". A clean CMOS clock makes this easier to pass, not harder.
- The comment "This code attempts to not drop through if no crystal is present … Ideally XI should be grounded if no
  crystal is present" confirms the design intent: the gate is XIN edges, not a crystal.
- The flash-boot path does not touch the XOSC. Only BOOTSEL (nsboot) starts it.

**XOSC_STARTUP delay issue:** none.
- The YXC oscillator's start-up is 3 ms max. That is about the same as the "few milliseconds" a crystal needs (DS
  §8.2.3).
- The STABLE counter does not advance until edges arrive. If the oscillator is still starting, the bootrom and the SDK
  wait for it.
- The SDK delay is about 6 ms of input edges (below), which is longer than the oscillator's start-up.
- The one theoretical case is runt edges during the oscillator's own start-up being counted. Even then, the
  255-consecutive-lock gate in the bootrom and the SDK's PLL lock wait come after it. The bench gate in §5 closes it.

### pico-sdk (github.com/raspberrypi/pico-sdk)

Checked at master 079c6f3 (2026-09-04) and at ee68c78, the commit Betaflight pins.

- `hardware_xosc/include/hardware/xosc.h`:
  - `PICO_XOSC_STARTUP_DELAY_MULTIPLIER` defaults to 6.
  - The config note on `PICO_XOSC_FREQ_RANGE_MAX` reads: "(not required when using CMOS clock input instead of XOSC)".
- `hardware_xosc/xosc.c` `xosc_init()`:
  - sets FREQ_RANGE 1_15MHZ (12 MHz);
  - sets STARTUP = ((12000 + 128) / 256) × 6 = 282, which is 72 192 input cycles, about 6.0 ms;
  - sets ENABLE, then waits for STABLE.
  - It works unchanged with a driven XIN.
- `platform_defs.h`: XOSC_HZ defaults to 12 000 000.

### Board firmware (Betaflight master 4fc1520, 2026-10-09; repo research/PINMAP.md §5)

- `src/platform/PICO/mk/RP2350.mk` builds the SDK's `runtime_init_clocks.c` and `hardware_xosc/xosc.c`. It sets no
  `XOSC_*` or `PICO_XOSC_*` define, and `pico/config_autogen.h` includes no board header. So XOSC_HZ is 12 MHz and the
  startup multiplier is 6.
- `system.c` assumes "clk_ref (from XOSC) is at 12Mhz". That still holds with a 12 MHz oscillator.
- PINMAP.md §5 (config.h / config.mk) has no XOSC setting.

**Firmware change: none.**
- No config.h or config.mk define.
- No OTP programming. BOOT_FLAGS0.ENABLE_BOOTSEL_NON_DEFAULT_PLL_XOSC_CFG stays clear, because the clock is 12 MHz.
- Do not try to "bypass" or disable the XOSC. CTRL.ENABLE must stay set because the clock passes through the XOSC
  block. DS Table 631 warns that DISABLE can lock up a chip that runs from the XOSC.

## 2. Oscillator choice

**YXC OT201612MJBA4SL, LCSC C669076** (NextPCB turnkey through LCSC). Data from the LCSC product API on 2026-10-10 and
the linked YXC YSO110TR "Wide Voltage" family datasheet, pages 1-4:

| Parameter | Value |
|---|---|
| Package | SMD2016-4P, 2.0 × 1.6 × 0.9 mm max |
| Frequency / output | 12 MHz, CMOS, 15 pF load |
| Supply | 1.8-3.3 V |
| Current | 4 mA max at 1-40 MHz in 2016/1612, 3.3 V, 15 pF (family table); LCSC lists 4 mA |
| Tolerance / stability | ±10 ppm at 25 °C; ±20 ppm over −40..+85 °C; aging ±3 ppm/year |
| Output levels | VOH ≥ 90 % VDD, VOL ≤ 10 % VDD, duty 45-55 %, tr/tf 4 ns max |
| Start-up | 3 ms max |
| Pin 1 tri-state | enable = high or floating (≥ 70 % VDD); disable ≤ 30 % VDD |
| Pinout (top view, counter-clockwise from bottom-left) | 1 tri-state/EN, 2 GND, 3 OUT, 4 VDD |
| Decoupling | Datasheet note 1: "A capacitor value 0.01uf~0.1uf or higher between Vdd and GND is required." |
| Stock | 3751 at LCSC (2026-10-10) |

- **USB accuracy:** about ±33 ppm worst case in the first year, against USB full speed's ±2500 ppm (0.25 %). It also
  beats the ABM8-272-T3 (±30 ppm + ±30 ppm).
- **1612 size:** no 12 MHz 1612 CMOS oscillator was found on LCSC or JLC (the LCSC search API refused access; web
  search only). 2016 is the smallest stocked option.
- **No second 2016 source was found at LCSC.**
  - The SiTime SiT8008BI-71-25E-12.000000 (C806734) is a 2016 part, but it is the 2.5 V ±10 % version and has 0
    stock. Not suitable.
  - Fallback in the same family: YXC **OT322512MJBA4SL (C725989)**, 3225, same specs, 8031 in stock. It would fit an
    area close to the present X1 site, but it gives up most of the area saving.

### Land

**Reuse the library's `lib:OSC-SMD_4P-L2.0-W1.6-BL_TXC_7Z_Dense`.**
- It is already in the repo for X3, a YXC 2016 4-pad TCXO. LIBRARY.md says: "YXC YSO510TP land trimmed to 2.1x1.7".
- Pads: 0.50 × 0.65 at (±0.80, ±0.525).
- Pad 1 at (−0.8, +0.525) is bottom-left, and numbering runs counter-clockwise. That matches the YSO110TR pin
  numbering.
- Courtyard 2.30 × 1.90 = 4.37 mm².

Re-run `hardware/tools/check_footprint.py` against the YSO110TR 2016 package on datasheet p2:
- package pads about 0.57 × 0.475, inner gaps 0.7 (X) and 0.5 (Y);
- YXC recommended land: 0.9 × 0.8 pads, 0.5 X-gap, 0.3 Y-gap, 2.3 × 1.9 overall.

The Dense land covers the outer ~0.37 mm of each 0.57 mm package pad in X and the full pad in Y. If the check asks for
more, widen the pads inward to the YXC 0.5 mm gap. The outline stays 2.1 × 1.7.

## 3. Schematic change (rp2350a sheet, "12 MHz crystal" block of sch_contract.json)

**Remove:**
- X1 ABM8-272-T3 (C20625731, `lib:CRYSTAL-SMD_4P-L3.2-W2.5-BL_Dense`);
- C43 15 pF GRM0335C1H150JA01D (XOUT_X–GND);
- R40 1 kΩ RC0201FR-071KL (XOUT–XOUT_X);
- C42's 15 pF value (the ref is reused below);
- nets XOUT_X and XOUT.

**Add or change:**

| Ref | Part | Footprint | Connections |
|---|---|---|---|
| X1 (ref kept) | YXC OT201612MJBA4SL, C669076, 12 MHz CMOS oscillator | `lib:OSC-SMD_4P-L2.0-W1.6-BL_TXC_7Z_Dense` | pin 1 EN → **+3V3** (tied directly; do not float, even though the datasheet allows it), pin 2 → GND, pin 3 OUT → **XIN** (U10 pin 21), pin 4 VDD → **+3V3** |
| C42 (ref kept, new value) | 100 nF GRM033C81E104KE14D (house 0201 100 nF, 29 already in the BOM) | `lib:C_0201_0603Metric_W` | +3V3 – GND at X1 pin 4, its GND pad next to X1 pin 2 |
| U10 pin 22 XOUT | — | — | **no-connect flag**, no trace, pad only (the XOSC amplifier still drives XOUT, so a stub would radiate) |

**Symbol:** copy `lib:OW7EL89CENUNFAYLC-52M` to `lib:OT201612MJBA4SL`, with pin 1 = EN (input), 2 GND (power_in),
3 OUT (output), 4 VDD (power_in). Update:
- the sch_contract block notes to "X1 OUT → XIN; XOUT NC";
- the bom_plan rows;
- PINMAP rows 21 / 22;
- the DESIGN-SPEC crystal rows (§2, §802 table, temperature list);
- D78 ("superseded by D99(a)").

**Counts:**
- 4 parts become 2 (−2 placements, −1 unique MPN: the 15 pF and the unlisted 1 kΩ go; the 100 nF is already stocked).
- Nets: 3 crystal nets become 1 (XIN), XOUT becomes no-connect.
- Courtyard: about 11.8 mm² (9.80 + 3 × 0.66) becomes about 5.0 mm² (4.37 + 0.66), so about **−6.8 mm²** at the U10
  pin ring.

**Placement:**
- X1 within about 3 mm of pin 21, on the XOSC side (north, P5).
- OUT pad (pin 3) toward XIN; pins 1 and 4 share one side, so the EN tie is a short F-layer stub.
- Keep XIN away from the DShot and ESC lines.
- No series resistor is needed for a run of a few mm with 4 ns edges.

## 4. Risks

1. **Power and level margin.**
   - +4 mA max on +3V3, minus the XOSC amplifier's crystal-mode current.
   - The family sheet gives "1.8-3.3 V" with no explicit ±10 % or absolute maximum. Confirm 3.3 V +10 % with
     YXC/LCSC, or check the board's +3V3 LDO tolerance (nominal 3.3 V is within the stated range).
2. **Part identity.** The LCSC-linked document is the YSO110TR family datasheet. It does not decode the OT201612MJBA4SL
   code. The specs come from LCSC's parameters and the family's 2016 column.
3. **Single 2016 source.** The fallback is the 3225 OT322512MJBA4SL, which gives up most of the area saving.
4. **No Raspberry Pi reference board uses an oscillator.**
   - The CMOS input is datasheet-documented and the bootrom is source-verified, but it is not proven on hardware here.
   - Bench gate on V1: BOOTSEL USB enumerates cold (−20 °C) and hot (+85 °C), and after a fast +3V3 ramp (oscillator
     start-up race).
   - Scope XIN: VIH ≥ 2.15 V, no runts after start-up.
5. **Noise.** The oscillator adds a 12 MHz square wave and its harmonics. The crystal had a sine-like swing. Keep a short
   XIN trace over solid GND and away from the SX1281 and RTC6705 inputs.
6. **Not a firmware risk.** Betaflight, the pico-sdk and the bootrom need no change and no OTP write.

## Sources

- RP2350 datasheet: https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
  - Release 8, build 80d627281ed5.
  - §1 pin table, §5.2.8.1, §5.8.1, §8.2.1-8.2.8 (Tables 629, 631-634), §13.10 BOOTSEL_XOSC_CFG (Table 1515),
    §14.8.2 Table 1676, §14.9 Table 1686, errata appendix.
- Hardware design with RP2350: https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
  - Release 3, build 06a7f75e58a1, §4 and §4.1.
- pico-bootrom-rp2350 @ c6cdb1711f32c3e34faaebd58618a6d096dbd52e: `src/main/arm/varm_nsboot.c` L45-175.
- pico-sdk @ 079c6f39023649b154152db30f1d781e884879bc and @ ee68c78d0afae2b69c03ae1a72bf5cc267a2d94c (Betaflight
  submodule):
  - `src/rp2_common/hardware_xosc/xosc.c`
  - `src/rp2_common/hardware_xosc/include/hardware/xosc.h`
  - `src/rp2350/hardware_regs/include/hardware/platform_defs.h`
  - `src/rp2_common/pico_runtime_init/runtime_init_clocks.c`
- Betaflight @ 4fc1520c5a5decddc8ef07ad57c0e766ea8747ba:
  - `src/platform/PICO/mk/RP2350.mk`
  - `src/platform/PICO/system.c`
  - `src/platform/PICO/pico/config_autogen.h`
  - `.gitmodules` / `lib/modules/pico-sdk`
- LCSC product API:
  - https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C669076 (also C725989, C806734, C20625731)
  - YXC YSO110TR datasheet linked from C669076: https://datasheet.lcsc.com/datasheet/pdf/b336a5b52993e15e0134a8f3d7decec7.pdf?productCode=C669076
  - JLC listing: https://jlcpcb.com/partdetail/YXC-OT201612MJBA4SL/C669076
- Repo:
  - research/DECISIONS.md D78, D99
  - research/PINMAP.md rows 21-22 and §5
  - research/FLOORPLAN-V4.md §16
  - research/LIBRARY.md (X3 row)
  - research/bomred/vtx-fc-misc.md §3
  - hardware/bom_plan.json, hardware/floorplan.json, hardware/sch_contract.json
  - hardware/lib.pretty/OSC-SMD_4P-L2.0-W1.6-BL_TXC_7Z_Dense.kicad_mod

## Independent check (2026-10-10) - binding corrections
- The conclusion holds: a 12 MHz CMOS clock on RP2350A XIN (pin 21) with XOUT (pin 22) open works for flash boot,
  USB / UART BOOTSEL and the 48 MHz USB PLL, with no OTP and no firmware change. Keep XOSC CTRL.ENABLE set.
- BOM: the 15 pF (C94/C95) and the 1k (23 refs) stay in the BOM; only parts drop, not MPNs.
- Supply: the YXC YSO110TR family sheet states VDD "1.8-3.3 V" with no tolerance or absolute maximum, while +3V3 comes
  from an LP5912-3.3. Before release, either confirm 3.3 V +10 % with YXC, or use a part with an explicit 3.6 V rating
  in the same 2016 land (for example an Epson SG-210STF or a SiTime SiT8008 3.3 V grade, if NextPCB can source it).
- Footprint: re-run check_footprint against the 2016 package drawing (required, not optional); widen the pads inward
  if the package pad is not covered.
- Start-up: the output behaviour during the 3 ms start is not specified; bench gate on V1 (cold / hot / fast-ramp
  BOOTSEL enumeration, scope XIN for VIH >= 2.15 V and no runt pulses).
