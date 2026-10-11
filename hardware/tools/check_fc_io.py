#!/usr/bin/env python3
"""Check FC schematic GPIOs against the firmware and RP2350 peripheral mux.

The schematic remains authoritative. This check reads actual netlist pin
functions and target macros, rather than maintaining a second numeric pin map.
Mux tables: RP2350 datasheet Table 3; Betaflight 2026.6.2 bus_spi_pico.c and
uart/uart_hw.c. OSD ordering: osd/osd_pico.c:137-156.
"""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

import sch_build as sb


SIGNALS = {
    "SPI0_SDI_PIN": "SPI0_MISO", "FLASH_CS_PIN": "FLASH_CS",
    "SPI0_SCK_PIN": "SPI0_SCK", "SPI0_SDO_PIN": "SPI0_MOSI",
    "SPI1_SDI_PIN": "SPI1_MISO", "GYRO_1_CS_PIN": "GYRO_CS",
    "SPI1_SCK_PIN": "SPI1_SCK", "SPI1_SDO_PIN": "SPI1_MOSI",
    "GYRO_1_EXTI_PIN": "GYRO_INT", "GYRO_1_CLKIN_PIN": "GYRO_CLKIN",
    **{f"MOTOR{i}_PIN": f"MOTOR{i}_FC" for i in range(1, 5)},
    **{f"UART{i}_{d}_PIN": f"UART{i}_{d}" for i in (0, 1) for d in ("TX", "RX")},
    "LED_STRIP_PIN": "LED_STRIP", "LED0_PIN": "LED0", "LED1_PIN": "LED1",
    "PINIO1_PIN": "HD_EN", "BEEPER_PIN": "BEEPER",
    "OSD_W_PIN": "OSD_W", "OSD_EN_PIN": "OSD_EN", "OSD_SYNC_PIN": "OSD_SYNC",
    "ADC_CURR_PIN": "ADC_CURR", "ADC_VBAT_PIN": "ADC_VBAT",
}
SPI_PINS = {
    0: {"SDI": {0, 4, 16, 20}, "SCK": {2, 6, 18, 22}, "SDO": {3, 7, 19, 23}},
    1: {"SDI": {8, 12, 24, 28}, "SCK": {10, 14, 26}, "SDO": {11, 15, 27}},
}
UART_PINS = {
    # Include the UART_AUX function, selected by the Pico SDK on these pins.
    0: {"TX": {0, 2, 12, 14, 16, 18, 28}, "RX": {1, 3, 13, 15, 17, 19, 29}},
    1: {"TX": {4, 6, 8, 10, 20, 22, 24, 26}, "RX": {5, 7, 9, 11, 21, 23, 25, 27}},
}


def check(netlist, config):
    _, nets = sb.read_netlist(str(netlist))
    defines = dict(re.findall(r"^#define[ \t]+(\w+)[ \t]+(\S+)", config.read_text(), re.M))
    errors = []
    actual = {}
    for name, nodes in nets.items():
        for ref, pin, function, _ in nodes:
            # KiCad appends the package pad to pinfunction, e.g. GPIO10_14.
            match = re.fullmatch(r"GPIO(\d+)(?:_ADC\d+)?(?:_\d+)?", function)
            if ref == "U10" and match and not name.startswith("unconnected-"):
                actual[name.rsplit("/", 1)[-1]] = int(match[1])
    pins = {}
    for macro, net in SIGNALS.items():
        match = re.fullmatch(r"PA(\d+)", defines.get(macro, ""))
        if not match:
            errors.append(f"{macro}: missing or unsupported GPIO definition")
            continue
        gpio = int(match[1])
        pins[macro] = gpio
        if actual.get(net) != gpio:
            errors.append(f"{net}: schematic GPIO{actual.get(net)}, firmware GPIO{gpio}")
        if gpio not in range(30):
            errors.append(f"{macro}: GPIO{gpio} unavailable on RP2354A")
    if len(set(pins.values())) != len(pins):
        errors.append("firmware assigns multiple signals to one GPIO")
    if set(actual) != set(SIGNALS.values()):
        errors.append(f"unexpected/missing schematic GPIO nets: {set(actual) ^ set(SIGNALS.values())}")
    for prefix, table in (("SPI", SPI_PINS), ("UART", UART_PINS)):
        for bus, functions in table.items():
            for function, allowed in functions.items():
                macro = f"{prefix}{bus}_{function}_PIN"
                if pins.get(macro) not in allowed:
                    errors.append(f"{macro}: invalid RP2350 peripheral mux pin")
    if defines.get("GYRO_1_SPI_INSTANCE") != "SPI1" or defines.get("FLASH_SPI_INSTANCE") != "SPI0":
        errors.append("gyro/blackbox SPI instances differ from the schematic buses")
    for macro in ("ADC_CURR_PIN", "ADC_VBAT_PIN"):
        if pins.get(macro) not in {26, 27, 28, 29}:
            errors.append(f"{macro}: not an ADC pin")
    osd = [pins.get(f"OSD_{name}_PIN", -100) for name in ("W", "EN", "SYNC")]
    if osd != list(range(osd[0], osd[0] + 3)):
        errors.append("PIO OSD requires consecutive W, EN, SYNC in that order")
    pios = [defines.get(name) for name in ("PIO_DSHOT_INDEX", "PIO_LEDSTRIP_INDEX", "PIO_OSD_INDEX")]
    if set(pios) != {"0", "1", "2"}:
        errors.append("DShot, LED strip and OSD require separate PIO blocks in this target")
    # A QFN60 device's GPIO0-29 all fit a single RP2350 PIO GPIO window.
    motors = [pins.get(f"MOTOR{i}_PIN", -100) for i in range(1, 5)]
    if max(motors) - min(motors) >= 32:
        errors.append("motor pins exceed one PIO GPIO window")
    if defines.get("BEEPER_PWM_HZ", "0") != "0":
        clkin = pins.get("GYRO_1_CLKIN_PIN", -100)
        beeper = pins.get("BEEPER_PIN", -200)
        if ((clkin >> 1) & 7) == ((beeper >> 1) & 7):
            errors.append("optional gyro clock and PWM beeper share a PWM slice")
    for error in errors:
        print("FAIL:", error)
    if not errors:
        print(f"ok: {len(pins)} FC signals match schematic and target; SPI/UART mux, ADC and PIO constraints pass")
    return bool(errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hw", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--netlist", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    config = args.config or args.hw.parent / "firmware/betaflight/configs/OPENAIO_WHOOP/config.h"
    if args.netlist:
        return check(args.netlist, config)
    with tempfile.TemporaryDirectory(prefix="whoop-io-") as temp:
        netlist = Path(temp) / "board.net"
        subprocess.run([sb.KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr",
                        "-o", str(netlist), str(args.hw / "OpenAIO-Whoop.kicad_sch")], check=True)
        return check(netlist, config)


if __name__ == "__main__":
    raise SystemExit(main())
