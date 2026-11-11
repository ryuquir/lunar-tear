#!/usr/bin/env bash
# Prepare a machine (Ubuntu 24.04) for building this project.
#   sudo tools/setup_env.sh
# It installs KiCad 10 (kicad-cli with the symbol and footprint libraries) and a small
# Python environment with kicad-sch-api, the library the schematic generator uses.
# Safe to run again: every step is skipped when it is already done.
set -euo pipefail

VENV="${FCJAMMA_VENV:-/opt/fcjamma-venv}"

if ! command -v kicad-cli >/dev/null 2>&1; then
  if [ ! -f /etc/apt/sources.list.d/kicad-ubuntu-kicad-10_0-releases-noble.sources ]; then
    # add-apt-repository needs the distribution's own Python (apt_pkg), not a newer one on PATH
    python3.12 /usr/bin/add-apt-repository -y ppa:kicad/kicad-10.0-releases
  fi
  apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints
fi
command -v pdftoppm >/dev/null 2>&1 || apt-get install -y --no-install-recommends poppler-utils

if [ ! -x "$VENV/bin/python" ]; then
  python3.12 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet "kicad-sch-api==0.5.6"

echo "kicad-cli $(kicad-cli version)"
echo "build with: $VENV/bin/python tools/build.py"
