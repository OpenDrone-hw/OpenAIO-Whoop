#!/usr/bin/env python3
"""Check the ExpressLRS layout against actual ESP32-PICO-V3 schematic pins.

Pin restrictions: Espressif ESP32-PICO Series v1.3, Tables 4, 5 and 8.
The runtime GPIO keys are defined by ExpressLRS Unified_ESP_RX.h/hardware.cpp.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

import sch_build as sb


SIGNALS = {
    'radio_sck': 'RADIO_SCK', 'radio_mosi': 'RADIO_MOSI',
    'radio_miso': 'RADIO_MISO', 'radio_nss': 'RADIO_NSS',
    'radio_rst': 'RADIO_RST', 'radio_busy': 'RADIO_BUSY',
    'radio_dio1': 'RADIO_DIO1', 'button': 'RX_BOOT', 'led_rgb': 'RX_LED',
    'vtx_sck': 'VTX_SPI_CLK', 'vtx_mosi': 'VTX_SPI_DATA',
    'vtx_nss': 'VTX_SPI_CS', 'vtx_amp_vref': 'PA_EN',
    'vtx_amp_pwm': 'VTX_AMP_PWM', 'vtx_amp_vpd': 'PA_DET',
}
INPUTS = {'radio_miso', 'radio_busy', 'radio_dio1', 'button',
          'vtx_amp_vpd', 'serial_rx'}


def check(netlist, layout, fc_config):
    _, nets = sb.read_netlist(str(netlist))
    target = json.loads(layout.read_text())
    errors, actual, package = [], {}, set()
    for name, nodes in nets.items():
        for ref, _, function, _ in nodes:
            match = re.search(r'(?:^|/)(?:GPIO|IO|I)(\d+)(?:_\d+)?$', function)
            if ref != 'U16' or not match:
                continue
            gpio = int(match[1])
            package.add(gpio)
            if not name.startswith('unconnected-'):
                actual[name.rsplit('/', 1)[-1]] = gpio
    receiver = re.search(r'^#define\s+SERIALRX_UART\s+SERIAL_PORT_UART([01])\s*$',
                         fc_config.read_text(), re.M)
    expected = dict(SIGNALS)
    if receiver:
        uart = receiver[1]
        expected.update(serial_rx=f'UART{uart}_TX', serial_tx=f'UART{uart}_RX')
    else:
        errors.append('Betaflight SERIALRX_UART must select UART0 or UART1')
    assigned = {}
    for key, net in expected.items():
        gpio = target.get(key)
        if type(gpio) is not int:
            errors.append(f'{key}: missing integer GPIO')
            continue
        if actual.get(net) != gpio:
            errors.append(f'{key}/{net}: schematic GPIO{actual.get(net)}, target GPIO{gpio}')
        if gpio not in package or gpio in {6, 11}:
            errors.append(f'{key}: GPIO{gpio} unavailable or used by the V3 in-package flash')
        if gpio in {0, 2, 5, 12, 15} and not (key == 'button' and gpio == 0):
            errors.append(f'{key}: GPIO{gpio} is a boot strap requiring an explicit circuit review')
        if key not in INPUTS and gpio in range(34, 40):
            errors.append(f'{key}: GPIO{gpio} is input-only')
        if gpio in assigned:
            errors.append(f'{key} and {assigned[gpio]} share GPIO{gpio}')
        assigned[gpio] = key
    if target.get('vtx_miso') != -1:
        errors.append('RTC6705 control is write-only; vtx_miso must be -1')
    if target.get('vtx_amp_vpd') not in range(32, 40):
        errors.append('PA detector must use ADC1 with Wi-Fi active')
    if target.get('serial_rx') != 3 or target.get('serial_tx') != 1:
        errors.append('the onboard receiver uses ESP U0RXD GPIO3 and U0TXD GPIO1')
    for error in errors:
        print('FAIL:', error)
    if not errors:
        print(f'ok: {len(expected)} receiver GPIO bindings match schematic and target; V3 pin restrictions pass')
    return bool(errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hw', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--netlist', type=Path)
    parser.add_argument('--layout', type=Path)
    parser.add_argument('--fc-config', type=Path)
    args = parser.parse_args()
    layout = args.layout or args.hw.parent / 'firmware/expresslrs/board-layout.json'
    fc = args.fc_config or args.hw.parent / 'firmware/betaflight/configs/OPENAIO_WHOOP/config.h'
    if args.netlist:
        return check(args.netlist, layout, fc)
    with tempfile.TemporaryDirectory(prefix='whoop-rx-io-') as temp:
        netlist = Path(temp) / 'board.net'
        subprocess.run([sb.KICAD_CLI, 'sch', 'export', 'netlist', '--format', 'kicadsexpr',
                        '-o', str(netlist), str(args.hw / 'OpenAIO-Whoop.kicad_sch')], check=True)
        return check(netlist, layout, fc)


if __name__ == '__main__':
    raise SystemExit(main())
