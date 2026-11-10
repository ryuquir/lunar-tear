#!/bin/bash
# Everything that follows the routing, in the one order that keeps board, archives, notes and drawings in step:
#   widen the supply tracks, add ground stitching, rule check and Gerber files, placement check, BOM, order package,
#   board with edge rails, the two checks of the package, drawings, supply drop.
# Usage (in tools/pcb):  FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg ./finish_package.sh [width in mm wanted for +5V and GND tracks, default 0.5]
# Stops at the first step that fails. check_cpl.py and gen_jlc.py need the network (JLCPCB part catalogue, EasyEDA footprints).
set -e
cd "$(dirname "$0")"
: "${FC_DESIGN:?set FC_DESIGN}" "${FC_HW_DIR:?set FC_HW_DIR}"
B="$FC_HW_DIR/famicart.kicad_pcb"
python3 widen_tracks.py "$B" --net +5V="${1:-0.5}" --net GND="${1:-0.5}"
python3 stitch_gnd.py "$B"
python3 route_pcb.py export
python3 check_place.py
python3 gen_bom.py
python3 gen_jlc.py
python3 make_rails.py
python3 check_jlc.py
python3 check_cpl.py
python3 draw_outline.py
python3 power_drop.py "$B"
