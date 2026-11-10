#!/bin/bash
# Everything that follows the routing, in the one order that keeps board, archives, notes and drawings in step:
#   reinforce track ends that only just reach their pad, widen the supply tracks, add ground stitching, rule check
#   and Gerber files, placement check, BOM, order package,
#   board with edge rails, drawings (SVG and PNG), the two checks of the package, supply drop.
# Usage (in tools/pcb):  FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg ./finish_package.sh [width in mm wanted for +5V and GND tracks, default 0.5]
# Stops at the first step that fails. check_cpl.py and gen_jlc.py need the network (JLCPCB part catalogue, EasyEDA footprints).
set -e
cd "$(dirname "$0")"
: "${FC_DESIGN:?set FC_DESIGN}" "${FC_HW_DIR:?set FC_HW_DIR}"
B="$FC_HW_DIR/famicart.kicad_pcb"
python3 anchor_tracks.py "$B"
python3 widen_tracks.py "$B" --net +5V="${1:-0.5}" --net GND="${1:-0.5}"
python3 stitch_gnd.py "$B"
python3 route_pcb.py export
python3 check_place.py
python3 gen_bom.py
python3 gen_jlc.py
python3 make_rails.py
python3 draw_outline.py
# PNG copies of the three drawings (headless Chromium through Playwright; without it check_jlc.py reports the PNG files as old)
for f in outline placement jlcpcb/rails; do node svg2png.js "$FC_HW_DIR/$f.svg" "$FC_HW_DIR/$f.png" 2 || echo "not rendered: $f.png"; done
python3 check_jlc.py
python3 check_cpl.py
python3 power_drop.py "$B"
