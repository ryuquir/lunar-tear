#!/usr/bin/env python3
"""Placement check against the real cartridge shell (run after gen_pcb.py, before routing).

For every footprint it takes the PHYSICAL body (modules: the module board + 0.5 mm for solder fillets, Pico 2 with
its USB overhang; other parts: courtyard, else pads/graphics bounding box) and checks, on a 0.05 mm raster:
  - inside the board outline minus cut-outs, with FC_EDGE_MARGIN (0.3 mm) to every edge,
  - not on a shell rib / post keep-out of its own side (shells.py comp_keepouts),
  - not overlapping another part on the same side,
and for every pad (also the part of a module's pads that lies outside its body): same edge margin, off the keep-outs
of its side. Nothing but the card edge J1 may reach lower than shells.TAB_BAND above the shoulder (the shell closes
around the tab base): module bodies, USB connectors, courtyards and pads are all held to that line.
Outlines prepared for JLCPCB (shells.hvc_large with relief / side_inset, rev G on): the left and right edges carry the
assembly edge rails, normally joined by V-cut, and JLCPCB wants copper at least 0.4 mm from a V-cut edge, so bodies and
pads keep FC_SIDE_MARGIN (0.4 mm) from those two edges.
Exit status 1 when anything fails.   FC_DESIGN=design_reve2 FC_HW_DIR=... python3 check_place.py"""
import os, sys, importlib
import numpy as np
import pcbnew
from pcbnew import ToMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shells
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
HW = os.path.abspath(os.environ['FC_HW_DIR'])
SH = getattr(D, 'SHELL', None)
G = 0.05; MARGIN = float(os.environ.get('FC_EDGE_MARGIN', '0.3'))
SIDE = float(os.environ.get('FC_SIDE_MARGIN', '0.4'))                                # to a V-cut (edge rail) side edge
BODY = {'RPi_Pico_SMD': 1.6, 'RPi_Pico_SMD_Short': 1.6, 'XIAO-RP2350-Edge': 1.0}      # modules: USB connector overhang past the marked end (mm)

def pip(px, py, poly):
    """vectorised point-in-polygon (even-odd)"""
    inside = np.zeros(px.shape, bool); n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        c = ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / ((y2 - y1) if y2 != y1 else 1e-12) + x1)
        inside ^= c
    return inside

def main():
    b = pcbnew.LoadBoard(os.path.join(HW, 'famicart.kicad_pcb'))
    bb = b.GetBoardEdgesBoundingBox()
    X0, Y0 = ToMM(bb.GetX()) - 1, ToMM(bb.GetY()) - 1; X1, Y1 = ToMM(bb.GetRight()) + 1, ToMM(bb.GetBottom()) + 1
    xs = np.arange(X0, X1, G); ys = np.arange(Y0, Y1, G); PX, PY = np.meshgrid(xs, ys)
    if SH:
        T = SH['body_h'] + 10.7
        poly = [(84.2, SH['body_h']), (84.2, T), (5.8, T), (5.8, SH['body_h'])] + [tuple(p) for p in SH['outline_body'][1:-1]]
        board = pip(PX, PY, poly)
        for cut in SH['cutouts']: board &= ~pip(PX, PY, cut)
    else:
        board = (PX >= 0) & (PX <= 90) & (PY >= 0) & (PY <= getattr(D, 'BODY_H', 35.4) + 10.7)
    # erode by MARGIN
    k = int(round(MARGIN / G)); ok = board.copy()
    for dx in range(-k, k + 1):
        for dy in range(-k, k + 1):
            if dx * dx + dy * dy <= k * k: ok &= np.roll(np.roll(board, dy, 0), dx, 1)
    side_lo, side_hi = (SH.get('edge_x') or (0.0, 90.0)) if SH else (0.0, 90.0)
    sm = max(MARGIN, SIDE) if (SH and SH.get('fillets')) else MARGIN       # JLCPCB outline: wider margin to the side edges
    ok &= (PX >= side_lo + sm - 1e-9) & (PX <= side_hi - sm + 1e-9)
    ko = {'F': np.zeros(board.shape, bool), 'B': np.zeros(board.shape, bool)}
    for side, p in (SH['comp_keepouts'] if SH else []): ko[side] |= pip(PX, PY, p)
    occ = {'F': np.zeros(board.shape, int), 'B': np.zeros(board.shape, int)}
    owner = {'F': {}, 'B': {}}
    bad = []
    tab_y = (SH['body_h'] - shells.TAB_BAND) if SH else None        # lowest y anything but J1 may reach
    def box(x0, y0, x1, y1):
        """index slices of the raster cells whose centres lie in the rectangle"""
        i0 = max(0, int(np.ceil((x0 - X0) / G - 1e-9))); i1 = min(len(xs), int(np.floor((x1 - X0) / G + 1e-9)) + 1)
        j0 = max(0, int(np.ceil((y0 - Y0) / G - 1e-9))); j1 = min(len(ys), int(np.floor((y1 - Y0) / G + 1e-9)) + 1)
        return (slice(j0, max(j0, j1)), slice(i0, max(i0, i1)))
    fps = list(b.GetFootprints())
    for idx, fp in enumerate(fps):
        ref = fp.GetReference(); name = str(fp.GetFPIDAsString()).split(':')[-1]
        if 'CardEdge' in name or ref.startswith('H'): continue
        side = 'B' if fp.IsFlipped() else 'F'
        if name in BODY:
            # module body from its Fab outline (KiCad applies rotation / flip), USB overhang on the marked end, +0.5 mm fillets
            fab = pcbnew.B_Fab if side == 'B' else pcbnew.F_Fab
            rects = []
            for g in fp.GraphicalItems():
                if g.GetLayer() != fab or 'TEXT' in g.GetClass(): continue
                gb = g.GetBoundingBox(); rects.append((ToMM(gb.GetWidth()) * ToMM(gb.GetHeight()), ToMM(gb.GetX()), ToMM(gb.GetY()), ToMM(gb.GetRight()), ToMM(gb.GetBottom())))
            rects.sort(reverse=True)
            _, rx0, ry0, rx1, ry1 = rects[0]
            usb = None
            if len(rects) > 1:                                   # USB marker: the connector overhangs that end
                _, mx0, my0, mx1, my1 = rects[1]; over = BODY[name]
                dx, dy = (mx0 + mx1 - rx0 - rx1) / 2, (my0 + my1 - ry0 - ry1) / 2
                if abs(dx) > abs(dy): usb = (rx0 - over, my0, rx0, my1) if dx < 0 else (rx1, my0, rx1 + over, my1)
                else: usb = (mx0, ry0 - over, mx1, ry0) if dy < 0 else (mx0, ry1, mx1, ry1 + over)
            if tab_y is not None and ry1 > tab_y: bad.append(f'{ref} ({side}) module body reaches below the card-edge shoulder band: y {ry1:.2f} > {tab_y:.2f}')
            rx0 -= 0.5; ry0 -= 0.5; rx1 += 0.5; ry1 += 0.5
            if usb:   # the connector may stick out past the LEFT/RIGHT board edge (shell side clearance), and past the top
                      # edge where the shell says so (shells.py usb_top), nowhere else
                u = (PX >= usb[0]) & (PX <= usb[2]) & (PY >= usb[1]) & (PY <= usb[3])
                side_out = (PX < side_lo + sm + G) | (PX > side_hi - sm - G)
                if SH and SH.get('usb_top'): side_out |= (PY < MARGIN + G) & (PX >= SH['usb_top'][0]) & (PX <= SH['usb_top'][1])
                if (u & ~ok & ~side_out).any(): bad.append(f'{ref} ({side}) USB connector leaves the board other than past a side edge')
                if (u & ko[side]).any(): bad.append(f'{ref} ({side}) USB connector on a shell keep-out')
                if tab_y is not None and usb[3] > tab_y: bad.append(f'{ref} ({side}) USB connector reaches below the card-edge shoulder band')
                usb_m = u
            else: usb_m = None
        else:
            usb_m = None
            cy_layer = pcbnew.B_CrtYd if side == 'B' else pcbnew.F_CrtYd
            bx = []
            for g in fp.GraphicalItems():
                if g.GetLayer() != cy_layer: continue
                gb = g.GetBoundingBox(); bx.append((ToMM(gb.GetX()), ToMM(gb.GetY()), ToMM(gb.GetRight()), ToMM(gb.GetBottom())))
            if not bx:
                for pad in fp.Pads():
                    pb = pad.GetBoundingBox(); bx.append((ToMM(pb.GetX()), ToMM(pb.GetY()), ToMM(pb.GetRight()), ToMM(pb.GetBottom())))
            rx0, ry0 = min(v[0] for v in bx), min(v[1] for v in bx); rx1, ry1 = max(v[2] for v in bx), max(v[3] for v in bx)
            if tab_y is not None and ry1 > tab_y: bad.append(f'{ref} ({side}) reaches below the card-edge shoulder band: y {ry1:.2f} > {tab_y:.2f}')
        # pads: copper and solder, wherever they are (a module's pads stick out of its body)
        p_edge, p_ko, p_tab = [], [], []
        for pad in fp.Pads():
            pb = pad.GetBoundingBox(); pr = (ToMM(pb.GetX()), ToMM(pb.GetY()), ToMM(pb.GetRight()), ToMM(pb.GetBottom()))
            sl = box(*pr)
            sides = 'FB' if pad.GetDrillSize().x > 0 else side
            if (~ok[sl]).any(): p_edge.append(pad.GetNumber())
            if any(ko[s][sl].any() for s in sides): p_ko.append(pad.GetNumber())
            if tab_y is not None and pr[3] > tab_y: p_tab.append(pad.GetNumber())
        if p_edge: bad.append(f'{ref} ({side}) pads off the board / too close to an edge or cut-out: {",".join(p_edge)}')
        if p_ko: bad.append(f'{ref} ({side}) pads on a shell rib/post keep-out: {",".join(p_ko)}')
        if p_tab: bad.append(f'{ref} ({side}) pads reach below the card-edge shoulder band: {",".join(p_tab)}')
        m = (PX >= rx0) & (PX <= rx1) & (PY >= ry0) & (PY <= ry1)
        if (m & ~ok).any(): bad.append(f'{ref} ({side}) leaves the board / hits a cut-out or the edge margin: [{rx0:.2f},{ry0:.2f}]-[{rx1:.2f},{ry1:.2f}]')
        if (m & ko[side]).any(): bad.append(f'{ref} ({side}) sits on a shell rib/post keep-out: [{rx0:.2f},{ry0:.2f}]-[{rx1:.2f},{ry1:.2f}]')
        if usb_m is not None: m = m | usb_m
        hit = set(np.unique(occ[side][m])) - {0}
        for h in hit: bad.append(f'{ref} ({side}) overlaps {owner[side][h]}')
        occ[side][m] = idx + 1; owner[side][idx + 1] = ref
    print('placement check:', 'OK' if not bad else f'{len(bad)} problems')
    for x in bad: print('  ', x)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
