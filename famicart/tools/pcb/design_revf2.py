"""famicart rev F2: the rev F circuit (Pico 2 x4 + XIAO RP2350, docs/10_rev_f_board.md) laid out for the Nintendo
LARGE Famicom shell (HVC-ExROM family -- Koei / Enix / Square large carts and the "でかカセット" reproduction shells),
using the real shell outline, slot and rib keep-outs from shells.py (docs/04_hardware.md, 基板外形の訂正).

  back  U2 (PPU)        below the notch band, centred between the two shell posts
        U5 (PPU copro)  above the notch band, USB at the right edge
        U1 (CPU)        top, USB at the left edge
  front U4 (CPU copro)  top, USB at the left edge
        U3 XIAO         middle (right of the centre post), USB-C to the right
        all JLCPCB parts (front only, one-sided assembly): CPU side left, PPU side right, near the card edge.
Netlist identical to rev F; only placement and outline change."""
from design_revf import *            # noqa: F401,F403  (PARTS, NETS, LCSC, HAND, POWER_NETS, helpers)
import design_revf as _base
import shells

REV = 'rev F2'
LAYERS = 2
SHELL = shells.hvc_large(75.0)
BODY_H = SHELL['body_h']
H = BODY_H

def at(xp, h):
    """x' (from the board centre line, + to the right seen from the front), h (height above the card-edge shoulder)"""
    return 45.0 + xp, H - h

def mv(ref, xp, h, rot, side='F'):
    lib, sym, val, fp, _ = PARTS[ref]
    x, y = at(xp, h)
    PARTS[ref] = (lib, sym, val, fp, (round(x, 3), round(y, 3), rot, side))

P('J1', 'famicart', 'Famicom_CardEdge_60', 'Famicom 60-pin edge', 'famicart:Famicom_CardEdge_60', 45.0, H) if False else None
lib, sym, val, fp, _ = PARTS['J1']; PARTS['J1'] = (lib, sym, val, fp, (45.0, H, 0, 'F'))

# ---- modules (hand-soldered) ----
# all four Picos use the short-pad footprint (pads 0.4 mm outside the module): the lowest one must keep every pad above
# the card-edge shoulder and below the slot keep-out (tools/pcb fit search: 1 front + 3 back fit the large shell)
for _r in ('U1', 'U2', 'U4', 'U5'):
    _l, _s, _v, _f, _p = PARTS[_r]; PARTS[_r] = (_l, _s, _v, 'famicart:RPi_Pico_SMD_Short', _p)
mv('U2', 0.0, 11.0, 270, 'B')        # body h 0.5-21.5, pads 0.1-21.9 (slot keep-out from 22.4), clear of the posts at x' +-31.75
mv('U5', 18.5, 37.3, 270, 'B')       # body h 26.8-47.8, x' -7.0..44.0, USB past the right edge
mv('U1', -18.3, 62.0, 90, 'B')       # body h 51.5-72.5, x' -43.8..7.2, USB past the left edge
mv('U4', -18.3, 63.0, 90, 'F')       # body h 52.5-73.5 (pads to 74.5), USB past the left edge
mv('U3', 22.5, 37.9, 270, 'F')       # XIAO body 21 x 17.8: x' 12..33, h 29.0-46.8; clear of the centre post at x' 0, h 39.45

# ---- JLCPCB parts: front only ----
cpu_arr = ['RN1', 'RN2', 'RN3', 'RN4', 'RN5', 'RN6', 'RN13', 'RN14']
ppu_arr = ['RN7', 'RN8', 'RN9', 'RN10', 'RN11', 'RN12', 'RN15', 'RN16']
for i, r in enumerate(cpu_arr): mv(r, -38.0 + 3.6 * i, 5.0, 0)      # courtyard 3.15 x 3.75 at 0 deg
for i, r in enumerate(ppu_arr): mv(r, 12.0 + 3.6 * i, 5.0, 0)
cpu_glue = ['Q1', 'R1', 'D1', 'D2', 'R2', 'R3', 'R4', 'R5']
for i, r in enumerate(cpu_glue): mv(r, -38.0 + (0 if i == 0 else 1.5 + 3.0 * i), 10.8, 0 if r.startswith('Q') else 90)
for i, r in enumerate(['R6', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12', 'R13']): mv(r, -38.0 + 3.0 * i, 16.3, 90)
ppu_glue = ['R14', 'Q2', 'R15', 'R16', 'C1', 'R17', 'C2', 'R18', 'R19']
for i, r in enumerate(ppu_glue): mv(r, 12.0 + (0 if i == 0 else 1.5 + 3.0 * i), 10.8, 0 if r.startswith('Q') else 90)
for i, r in enumerate(['D3', 'D4', 'D5', 'D6', 'D7', 'C3', 'C4']): mv(r, 13.0 + 3.6 * i, 16.3, 90)
for i, r in enumerate(['R20', 'R21', 'R22', 'R23', 'R24']): mv(r, -20.0 + 3.0 * i, 31.0, 90)
mv('SW1', -38.0, 38.0, 90)
mv('J2', 40.0, 33.0, 90)
