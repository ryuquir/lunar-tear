"""Which microcontroller modules fit a Famicom shell? Exhaustive search over shells.py (outline, slot, rib and post
keep-outs), both sides, the four orientations of each module, on a 0.25 mm grid (summed-area tables, O(1) box tests).

  python3 shell_fit.py small large                 # how many Pico 2 / XIAO fit, and where
  PAD_OUT=1.0 python3 shell_fit.py small large     # Pico pads 1.0 mm outside the module (RPi_Pico_SMD) instead of 0.4 mm (.._Short)
  FIT_SET=pico:2,xiao:2 python3 shell_fit.py small large   # also search one arrangement of that module set

Rules (the same for every module and every column of the table in docs/04_hardware.md):
  * module body + 0.5 mm (solder fillets) on the board, 0.3 mm from every edge and cut-out, off the rib / post keep-outs
    of its side, and above the card-edge shoulder;
  * every pad on the board with the same edge margin, off the route keep-outs and the keep-outs of its side, and at
    least shells.TAB_BAND above the shoulder. A pad may be left out only if its pin is not used
    (Pico: GND / AGND / ADC_VREF / 3V3 / 3V3_EN / VBUS);
  * the USB connector overhang may leave the board only past the left or right edge.
Module models (mm): Pico 2 body 51 x 21, micro-USB 8 wide sticking out 1.6, 20 pads per long edge at 2.54, first pad
centre 1.37 from the USB end (datasheet), pad 1.7 wide from 2.6 inside to PAD_OUT outside the edge.
XIAO body 21 x 17.8, USB-C 9 wide sticking out 1.0, 7 pads per long edge, first centre 2.88 from the USB end, pad 2.0 wide
from 2.19 inside to 0.56 outside (famicart:XIAO-RP2350-Edge).
Pin rows follow the real module (no mirror-image modules): seen from above with the USB end up, pins 1..20 run down the
left edge and 40..21 down the right edge.

Results (2026-11-10, this rule set): see docs/04_hardware.md, "Pico 2 は何枚入るか"."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shells

G = 0.1
STEP = float(os.environ.get('FIT_STEP', '0.25'))
MARGIN = 0.3
PAD_OUT = float(os.environ.get('PAD_OUT', '0.4'))
MODULES = {
    'pico': dict(L=51.0, Wd=21.0, usb=1.6, usb_w=8.0, n=20, first=1.37, pad_w=1.7, pad_in=2.6, pad_out=PAD_OUT,
                 free={3, 8, 13, 18, 23, 28, 33, 35, 36, 37, 38, 40}),
    'xiao': dict(L=21.0, Wd=17.8, usb=1.0, usb_w=9.0, n=7, first=2.88, pad_w=2.0, pad_in=2.19, pad_out=0.56, free=set()),
}
# board (x, y) offset of a module-local point (lx across: -Wd/2 = pins 1..; ly along: -L/2 = USB end), per side and
# USB direction as seen from the FRONT of the board (y grows toward the card edge)
XF = {('F', 'U'): lambda lx, ly: (lx, ly), ('F', 'L'): lambda lx, ly: (ly, -lx), ('F', 'D'): lambda lx, ly: (-lx, -ly), ('F', 'R'): lambda lx, ly: (-ly, lx),
      ('B', 'U'): lambda lx, ly: (-lx, ly), ('B', 'L'): lambda lx, ly: (ly, lx), ('B', 'D'): lambda lx, ly: (lx, -ly), ('B', 'R'): lambda lx, ly: (-ly, -lx)}

def pip(px, py, poly):
    ins = np.zeros(px.shape, bool); n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if y1 == y2: continue
        ins ^= ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1)
    return ins

def local_rects(m):
    """body, usb overhang and pads [(pin, rect)] in module-local coordinates; rect = (x0, y0, x1, y1)"""
    L, Wd = m['L'], m['Wd']
    body = (-Wd / 2, -L / 2, Wd / 2, L / 2)
    usb = (-m['usb_w'] / 2, -L / 2 - m['usb'], m['usb_w'] / 2, -L / 2)
    pads = []
    for k in range(m['n']):
        y = -L / 2 + m['first'] + 2.54 * k
        pads.append((k + 1, (-Wd / 2 - m['pad_out'], y - m['pad_w'] / 2, -Wd / 2 + m['pad_in'], y + m['pad_w'] / 2)))
        pads.append((2 * m['n'] - k, (Wd / 2 - m['pad_in'], y - m['pad_w'] / 2, Wd / 2 + m['pad_out'], y + m['pad_w'] / 2)))
    return body, usb, pads

def place(rect, f, cx, cy):
    (ax, ay), (bx, by) = f(rect[0], rect[1]), f(rect[2], rect[3])
    return (cx + min(ax, bx), cy + min(ay, by), cx + max(ax, bx), cy + max(ay, by))

class Shell:
    def __init__(self, sh):
        self.sh = sh; H = self.H = sh['body_h']; T = H + 10.7
        self.xs = np.arange(-3, 93, G); self.ys = np.arange(-2, T + 2, G); PX, PY = np.meshgrid(self.xs, self.ys)
        poly = [(84.2, H), (84.2, T), (5.8, T), (5.8, H)] + [tuple(p) for p in sh['outline_body'][1:-1]]
        board = pip(PX, PY, poly)
        for c in sh['cutouts']: board &= ~pip(PX, PY, c)
        k = int(round(MARGIN / G)); ok = board.copy()
        for dx in range(-k, k + 1):
            for dy in range(-k, k + 1):
                if dx * dx + dy * dy <= k * k: ok &= np.roll(np.roll(board, dy, 0), dx, 1)
        cu = ok.copy()
        for r in sh['route_keepouts']: cu &= ~pip(PX, PY, r)
        ko = {s: np.zeros(board.shape, bool) for s in 'FB'}
        for s, p in sh['comp_keepouts']: ko[s] |= pip(PX, PY, p)
        side_out = (PX < MARGIN + G) | (PX > 90 - MARGIN - G)
        sat = lambda m: np.pad(m.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        self.bad_body = {s: sat(~ok | ko[s]) for s in 'FB'}
        self.bad_usb = {s: sat((~ok & ~side_out) | ko[s]) for s in 'FB'}
        self.bad_pad = {s: sat(~cu | ko[s]) for s in 'FB'}
        self.tab_y = H - shells.TAB_BAND

    def q(self, S, r):
        x0, y0, x1, y1 = r
        i0 = max(0, int(np.floor((y0 - self.ys[0]) / G))); i1 = min(len(self.ys), int(np.ceil((y1 - self.ys[0]) / G)) + 1)
        j0 = max(0, int(np.floor((x0 - self.xs[0]) / G))); j1 = min(len(self.xs), int(np.ceil((x1 - self.xs[0]) / G)) + 1)
        return S[i1, j1] - S[i0, j1] - S[i1, j0] + S[i0, j0]

    def feasible(self, kind):
        """every legal placement of one module: (kind, side, usb_dir, cx, cy, dropped_pins, envelope)"""
        m = MODULES[kind]; body, usb, pads = local_rects(m); out = []
        half = max(m['L'], m['Wd']) / 2
        for side in 'FB':
            for d in 'ULDR':
                f = XF[(side, d)]
                for cx in np.arange(half - 30, 90 - half + 30.01, STEP):
                    for cy in np.arange(0.0, self.H, STEP):
                        b = place(body, f, cx, cy)
                        if b[0] < 0 or b[2] > 90 or b[1] < 0 or b[3] + 0.5 > self.H: continue
                        if self.q(self.bad_body[side], (b[0] - 0.5, b[1] - 0.5, b[2] + 0.5, b[3] + 0.5)): continue
                        u = place(usb, f, cx, cy)
                        if u[3] > self.tab_y or self.q(self.bad_usb[side], u): continue
                        drop = []; bad = False; env = [min(b[0] - 0.5, u[0]), min(b[1] - 0.5, u[1]), max(b[2] + 0.5, u[2]), max(b[3] + 0.5, u[3])]
                        for pin, pr in pads:
                            p = place(pr, f, cx, cy)
                            if p[3] > self.tab_y or self.q(self.bad_pad[side], p):
                                if pin in m['free']: drop.append(pin); continue
                                bad = True; break
                            env = [min(env[0], p[0]), min(env[1], p[1]), max(env[2], p[2]), max(env[3], p[3])]
                        if not bad: out.append((kind, side, d, round(float(cx), 2), round(float(cy), 2), tuple(sorted(drop)), tuple(env)))
        return out

def clash(a, b):
    A, B = a[6], b[6]
    return a[1] == b[1] and A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]

def max_pack(cands, limit=12):
    """largest non-overlapping subset of one side's candidates (greedy from every ordering that matters; the free
    regions of these shells are bands and columns, so sweeping along each axis finds the maximum)"""
    best = []
    for key in (lambda p: (p[4], p[3]), lambda p: (-p[4], p[3]), lambda p: (p[3], p[4]), lambda p: (-p[3], p[4])):
        order = sorted(cands, key=key)
        starts = order[:: max(1, len(order) // 60)]
        for s in starts:
            chosen = [s]
            for p in order:
                if all(not clash(p, c) for c in chosen): chosen.append(p)
                if len(chosen) >= limit: break
            if len(chosen) > len(best): best = chosen
    return best

def describe(sh_obj, p):
    kind, side, d, cx, cy, drop, env = p
    return '%s %s USB-%s centre x=%.2f h=%.2f%s' % (kind, side, d, cx, sh_obj.H - cy, (' drop pins %s' % (drop,)) if drop else '')

def run(sh, label):
    S = Shell(sh); H = S.H
    feas = {k: S.feasible(k) for k in MODULES}
    print(f'== {label} (body {H} mm, Pico pads {PAD_OUT} mm outside)')
    best = {}
    for kind in MODULES:
        for side in 'FB':
            f = [p for p in feas[kind] if p[1] == side]
            byd = {d: sum(1 for p in f if p[2] == d) for d in 'ULDR'}
            b = max_pack(f) if f else []
            best[(kind, side)] = b
            print(f'   {kind} {side}: {len(f)} placements {byd}; max without overlap = {len(b)}')
            for p in b: print('        ' + describe(S, p))
    want = os.environ.get('FIT_SET')
    if want:
        need = [(k, int(n)) for k, n in (t.split(':') for t in want.split(','))]
        order = sorted(need, key=lambda t: -MODULES[t[0]]['L'])          # big modules first
        seq = [k for k, n in order for _ in range(n)]
        found = [None]; budget = [200000]
        def rec(i, chosen):
            if found[0] or budget[0] <= 0: return
            if i == len(seq): found[0] = list(chosen); return
            cands = feas[seq[i]][:: max(1, len(feas[seq[i]]) // 400)]     # thin out: neighbouring grid points are equivalent
            for p in cands:
                budget[0] -= 1
                if budget[0] <= 0: return
                if i and seq[i - 1] == seq[i] and (p[1], p[3], p[4]) <= (chosen[-1][1], chosen[-1][3], chosen[-1][4]): continue
                if all(not clash(p, c) for c in chosen):
                    chosen.append(p); rec(i + 1, chosen); chosen.pop()
                    if found[0]: return
        rec(0, [])
        if found[0]:
            print(f'   set {want}: FITS, for example')
            for p in found[0]: print('        ' + describe(S, p))
        else:
            cap = {k: len(best[(k, "F")]) + len(best[(k, "B")]) for k in MODULES}
            print(f'   set {want}: no arrangement found (per-module maximum, each kind alone: {cap})')
    return feas

if __name__ == '__main__':
    for name in sys.argv[1:]:
        if name == '.': continue
        sh = {'small': shells.hvc_small, 'large': lambda: shells.hvc_large(75.0),
              'large-jlc': lambda: shells.hvc_large(75.0, relief=0.6, side_inset=0.2)}[name]()     # large-jlc: the outline rev G is made with
        run(sh, name)
