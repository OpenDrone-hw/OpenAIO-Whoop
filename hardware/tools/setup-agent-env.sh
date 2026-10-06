#!/usr/bin/env bash
# Installs the KiCad 10 toolchain an agent (or a person) needs to check and
# script this board headless on Ubuntu 24.04: kicad-cli, the pcbnew Python
# module, kicad-skip, kicad-python (IPC API) and easyeda2kicad.
# Idempotent. Run as root, e.g. as a cloud environment setup script.
#
#   bash hardware/tools/setup-agent-env.sh
#
# Afterwards:
#   kicad-cli version                     -> 10.0.x
#   KPY=/usr/bin/python3.12               (KiCad's Python on Linux; pcbnew imports here)
#   /opt/kicad-agent-venv/bin/python      (KPY plus kicad-skip, kipy, easyeda2kicad)
#
# macOS: install KiCad 10 from kicad.org, then
#   KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
#   $KPY -m pip install --user kicad-skip kicad-python easyeda2kicad
set -euo pipefail

PPA=kicad/kicad-10.0-releases
VENV=/opt/kicad-agent-venv
. /etc/os-release

if ! command -v kicad-cli >/dev/null 2>&1; then
  # add-apt-repository breaks when python3 is not the distro Python (no
  # apt_pkg), so add the PPA by hand from its Launchpad signing key.
  fp=$(curl -fsSL "https://api.launchpad.net/1.0/~${PPA%%/*}/+archive/ubuntu/${PPA##*/}" |
       python3 -c 'import json,sys; print(json.load(sys.stdin)["signing_key_fingerprint"])')
  curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x${fp}" |
    gpg --dearmor --yes -o /usr/share/keyrings/kicad-10.gpg
  echo "deb [signed-by=/usr/share/keyrings/kicad-10.gpg] https://ppa.launchpadcontent.net/${PPA}/ubuntu ${VERSION_CODENAME} main" \
    > /etc/apt/sources.list.d/kicad-10.list
  apt-get update -qq
  # No recommends: skips the stock symbol, footprint and 3D libraries
  # (several GB). Projects embed their symbols and use the OpenDrone library.
  # Set KICAD_FULL_LIBS=1 for renders that need stock 3D models.
  pkgs=(kicad python3.12-venv)
  [ "${KICAD_FULL_LIBS:-0}" = 1 ] && pkgs+=(kicad-footprints kicad-symbols kicad-packages3d)
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${pkgs[@]}"
fi

if [ ! -x "$VENV/bin/python" ]; then
  # --system-site-packages keeps KiCad's pcbnew importable inside the venv.
  /usr/bin/python3.12 -m venv --system-site-packages "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade kicad-skip kicad-python easyeda2kicad

kicad-cli version
"$VENV/bin/python" -c 'import pcbnew, skip, kipy; print("pcbnew", pcbnew.Version())' 2>/dev/null
