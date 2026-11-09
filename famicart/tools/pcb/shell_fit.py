"""How many Raspberry Pi Pico 2 modules fit a Famicom shell? Exhaustive search over shells.py (outline, slot, rib and
post keep-outs) with summed-area tables (O(1) box tests), 0.25 mm placement grid, both sides, both USB directions.

  python3 shell_fit.py . small large                      # pads 1.0 mm outside the module (RPi_Pico_SMD)
  PAD_OUT=0.4 PAD_BELOW=0 python3 shell_fit.py . small large   # short pads (RPi_Pico_SMD_Short), no copper below the shoulder

Results (2026-11-09): standard shell 1 Pico (back, low band) in both cases; large shell 1 front + 2 back with long pads,
1 front + 3 back with short pads.
Pico model (horizontal; vertical is 51 mm, taller than any free band): body 51 x 21 + 0.5 fillet, must stay above the
card-edge shoulder; micro-USB 1.6 x 8 at one short end (may pass a side edge only); 40 pads, 20 per long edge, 2.54 pitch,
first centre 1.14 from the USB end, 1.7 wide, from 2.6 inside to 1.0 outside the body edge, at most 1.0 below the
shoulder. A pad may be dropped only if its pin is not used (GND/AGND/ADC_VREF/3V3/3V3_EN/VBUS)."""
import sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '.')
import numpy as np, shells
G = 0.1
import os
OUT = float(os.environ.get("PAD_OUT", "1.0")); MAXBELOW = float(os.environ.get("PAD_BELOW", "1.0"))
FREE = {3, 8, 13, 18, 23, 28, 33, 35, 36, 37, 38, 40}
def pip(px, py, poly):
    ins = np.zeros(px.shape, bool); n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if y1 == y2: continue
        ins ^= ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1)
    return ins
def run(sh, label):
    H = sh['body_h']; T = H + 10.7
    xs = np.arange(-3, 93, G); ys = np.arange(-2, T + 2, G); PX, PY = np.meshgrid(xs, ys)
    poly = [(84.2, H), (84.2, T), (5.8, T), (5.8, H)] + [tuple(p) for p in sh['outline_body'][1:-1]]
    board = pip(PX, PY, poly)
    for c in sh['cutouts']: board &= ~pip(PX, PY, c)
    k = 3; ok = board.copy()
    for dx in range(-k, k + 1):
        for dy in range(-k, k + 1):
            if dx * dx + dy * dy <= k * k: ok &= np.roll(np.roll(board, dy, 0), dx, 1)
    cu = board.copy()
    for r in sh['route_keepouts']: cu &= ~pip(PX, PY, r)
    ko = {s: np.zeros(board.shape, bool) for s in 'FB'}
    for s, p in sh['comp_keepouts']: ko[s] |= pip(PX, PY, p)
    side_out = (PX < 0.3 + G) | (PX > 89.7 - G)
    def sat(m):
        a = np.zeros((m.shape[0] + 1, m.shape[1] + 1), np.int32); a[1:, 1:] = m.astype(np.int32).cumsum(0).cumsum(1); return a
    S_bad_body = {s: sat(~ok | ko[s]) for s in 'FB'}
    S_bad_usb = {s: sat((~ok & ~side_out) | ko[s]) for s in 'FB'}
    S_bad_pad = {s: sat(~cu | ko[s]) for s in 'FB'}
    def q(Sa, x0, y0, x1, y1):
        i0 = max(0, int(np.floor((y0 - ys[0]) / G))); i1 = min(len(ys), int(np.ceil((y1 - ys[0]) / G)) + 1)
        j0 = max(0, int(np.floor((x0 - xs[0]) / G))); j1 = min(len(xs), int(np.ceil((x1 - xs[0]) / G)) + 1)
        return Sa[i1, j1] - Sa[i0, j1] - Sa[i1, j0] + Sa[i0, j0]
    feas = []
    for side in 'FB':
        for usb_left in (True, False):
            for top21 in (True, False):
                for cx in np.arange(24.0, 66.01, 0.25):
                    for cy in np.arange(10.5, H - 10.0, 0.25):
                        bx0, bx1, by0, by1 = cx - 25.5, cx + 25.5, cy - 10.5, cy + 10.5
                        if by1 + 0.5 > H: continue
                        if q(S_bad_body[side], bx0 - 0.5, by0 - 0.5, bx1 + 0.5, by1 + 0.5): continue
                        ux0, ux1 = (bx0 - 1.6, bx0) if usb_left else (bx1, bx1 + 1.6)
                        if q(S_bad_usb[side], ux0, cy - 4, ux1, cy + 4): continue
                        drop = []; bad = False
                        for kk in range(20):
                            d = 1.14 + 2.54 * kk; px = bx0 + d if usb_left else bx1 - d
                            for row_top in (True, False):
                                pin = (40 - kk) if (row_top == top21) else (kk + 1)
                                py0, py1 = (by0 - OUT, by0 + 2.6) if row_top else (by1 - 2.6, by1 + OUT)
                                if py1 > H + MAXBELOW or q(S_bad_pad[side], px - 0.85, py0, px + 0.85, py1):
                                    if pin in FREE: drop.append(pin)
                                    else: bad = True; break
                            if bad: break
                        if not bad: feas.append((side, usb_left, top21, round(cx, 2), round(cy, 2), tuple(sorted(set(drop)))))
    print(f'== {label} (body {H} mm): {len(feas)} feasible Pico placements')
    for side in 'FB':
        f = [p for p in feas if p[0] == side]
        if not f: print(f'   {side}: none'); continue
        hs = sorted(set(round(H - p[4], 2) for p in f))
        print(f'   {side}: {len(f)}; centre height above shoulder {hs[0]}..{hs[-1]} mm')
    # maximum packing per side: two placements conflict when their body+pad envelopes overlap
    def env(p):
        side, ul, t, cx, cy, _ = p
        return (cx - 25.5 - (1.6 if ul else 0) - 0.5, cy - 11.5, cx + 25.5 + (0 if ul else 1.6) + 0.5, cy + 11.5)
    def clash(a, b):
        A, B = env(a), env(b)
        return a[0] == b[0] and A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]
    for side in 'FB':
        f = sorted([p for p in feas if p[0] == side], key=lambda p: (-p[4], p[3]))
        best = []
        # exact for this shape: bands by height; try every first pick by height, greedy upward
        hs = sorted(set(p[4] for p in f), reverse=True)
        for start in hs[:40]:
            chosen = []
            for p in [p for p in f if p[4] <= start]:
                if all(not clash(p, c) for c in chosen): chosen.append(p)
            if len(chosen) > len(best): best = chosen
        print(f'   {side}: max non-overlapping found = {len(best)}', [(p[3], round(H - p[4], 2), 'USB-L' if p[1] else 'USB-R', p[5]) for p in best])
for name in sys.argv[2:]:
    run(shells.hvc_small() if name == 'small' else shells.hvc_large(75.0), name)
