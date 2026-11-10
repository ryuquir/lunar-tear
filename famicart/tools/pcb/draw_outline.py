#!/usr/bin/env python3
"""Draw the board of a design as two SVG drawings in FC_HW_DIR:
  outline.svg    the outline as seen from the front (label side) with its dimensions
  placement.svg  where the modules and connectors sit, front and back (the back as seen from the back)
  jlcpcb/rails.svg  the board with its edge rails (designs with RAILS), labelled in English for JLCPCB's support
The geometry comes from the same data the board generator uses (shells.py, gen_pcb.py) and from the board file, so
the drawings cannot drift from the fabrication data. Text is Japanese (font: IPAGothic or any CJK sans).
    FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg python3 draw_outline.py
Rasterise with any SVG renderer (a browser, rsvg-convert, Inkscape)."""
import os, sys, math, importlib
import pcbnew
from pcbnew import ToMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
import gen_pcb
HW = os.path.abspath(os.environ['FC_HW_DIR'])
SH = getattr(D, 'SHELL', None)
W, H, T = gen_pcb.BOARD_W, gen_pcb.BODY_H, gen_pcb.TOTAL_H
X0, X1, CH = gen_pcb.TAB_X0, gen_pcb.TAB_X0 + gen_pcb.TAB_W, gen_pcb.CHAMFER
S = 10.0                                    # px per mm
FONT = "IPAGothic, 'IPAexGothic', 'Noto Sans CJK JP', 'Yu Gothic', sans-serif"
INK, DIM, EDGE, FILL, GOLD, MUTED = '#1c2530', '#2f5f9e', '#14532d', '#e3f0e6', '#c9a227', '#6b7280'

def outline_points():
    body = SH['outline_body'] if SH else [(X0, H), (0, H), (0, 0), (W, 0), (W, H), (X1, H)]
    return list(body) + [(X1, T - CH), (X1 - CH, T), (X0 + CH, T), (X0, T - CH)]

def path(pts, fillets, r, ox, oy):
    """Closed SVG path; vertices listed in `fillets` are replaced by an arc of radius r tangent to both edges."""
    def near(p): return any(abs(p[0] - f[0]) < 1e-6 and abs(p[1] - f[1]) < 1e-6 for f in fillets)
    out, n = [], len(pts)
    for i in range(n):
        p0, p, p1 = pts[i - 1], pts[i], pts[(i + 1) % n]
        if r > 0 and near(p):
            d1 = (p[0] - p0[0], p[1] - p0[1]); l1 = math.hypot(*d1); d1 = (d1[0] / l1, d1[1] / l1)
            d2 = (p1[0] - p[0], p1[1] - p[1]); l2 = math.hypot(*d2); d2 = (d2[0] / l2, d2[1] / l2)
            a = (p[0] - d1[0] * r, p[1] - d1[1] * r); b = (p[0] + d2[0] * r, p[1] + d2[1] * r)
            sweep = 1 if d1[0] * d2[1] - d1[1] * d2[0] > 0 else 0
            out.append('%s%.2f,%.2f' % ('M' if not out else 'L', ox + a[0] * S, oy + a[1] * S))
            out.append('A%.2f,%.2f 0 0 %d %.2f,%.2f' % (r * S, r * S, sweep, ox + b[0] * S, oy + b[1] * S))
        else:
            out.append('%s%.2f,%.2f' % ('M' if not out else 'L', ox + p[0] * S, oy + p[1] * S))
    return ' '.join(out) + ' Z'

class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.e = w, h, []
    def add(self, s): self.e.append(s)
    def line(self, x1, y1, x2, y2, c=DIM, w=1.4, dash=None):
        self.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f"%s/>' % (x1, y1, x2, y2, c, w, ' stroke-dasharray="%s"' % dash if dash else ''))
    def text(self, x, y, s, size=20, c=INK, anchor='middle', weight='normal', rot=None):
        tr = ' transform="rotate(%d %.1f %.1f)"' % (rot, x, y) if rot is not None else ''
        self.add('<text x="%.1f" y="%.1f" font-size="%d" fill="%s" text-anchor="%s" font-weight="%s"%s>%s</text>' % (x, y, size, c, anchor, weight, tr, s))
    def arrow(self, x, y, dx, dy, c=DIM):
        """Arrow head with its tip at (x, y), pointing along (dx, dy)."""
        l = math.hypot(dx, dy); ux, uy = dx / l, dy / l; a, b = 11.0, 3.6
        self.add('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="%s"/>' % (x, y, x - ux * a - uy * b, y - uy * a + ux * b, x - ux * a + uy * b, y - uy * a - ux * b, c))
    def hdim(self, x1, x2, y, label, ext=None, size=20, below=False):
        """Horizontal dimension between x1 and x2 (px) on the line y; ext = y of the feature the extension lines start at."""
        if ext is not None:
            for x in (x1, x2): self.line(x, ext, x, y + (6 if y > ext else -6), w=1.0)
        self.line(x1, y, x2, y); self.arrow(x1, y, -1, 0); self.arrow(x2, y, 1, 0)
        self.text((x1 + x2) / 2, y + (size + 4 if below else -7), label, size, DIM)
    def vdim(self, y1, y2, x, label, ext=None, size=20, side='left'):
        if ext is not None:
            for y in (y1, y2): self.line(ext, y, x + (6 if x > ext else -6), y, w=1.0)
        self.line(x, y1, x, y2); self.arrow(x, y1, 0, -1); self.arrow(x, y2, 0, 1)
        if side == 'left': self.text(x - 8, (y1 + y2) / 2 + size * 0.35, label, size, DIM, anchor='end')
        else: self.text(x + 8, (y1 + y2) / 2 + size * 0.35, label, size, DIM, anchor='start')
    def save(self, name):
        p = os.path.join(HW, name)
        open(p, 'w').write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="%s">\n<rect width="100%%" height="100%%" fill="#ffffff"/>\n%s\n</svg>\n'
                           % (self.w, self.h, self.w, self.h, FONT, '\n'.join(self.e)))
        print('written', p)

def fingers(board):
    j1 = board.FindFootprintByReference('J1')
    return [(p.GetNumber(), ToMM(b.GetX()), ToMM(b.GetY()), ToMM(b.GetRight()), ToMM(b.GetBottom()), p.IsOnLayer(pcbnew.F_Cu))
            for p in j1.Pads() for b in [p.GetBoundingBox()]] if j1 else []

def board_shape(g, ox, oy, fill=FILL, stroke=EDGE, sw=2.6):
    fl, r = (SH['fillets'], SH['fillet_r']) if SH and SH.get('fillets') else ([], 0.0)
    g.add('<path d="%s" fill="%s" stroke="%s" stroke-width="%.1f" stroke-linejoin="round"/>' % (path(outline_points(), fl, r, ox, oy), fill, stroke, sw))
    for cut in (SH['cutouts'] if SH else []):
        g.add('<path d="%s" fill="#ffffff" stroke="%s" stroke-width="%.1f"/>' % (path(list(cut), fl, r, ox, oy), stroke, sw))

def draw_outline(board):
    ox, oy = 330.0, 190.0
    g = Svg(int(ox + W * S + 400), int(oy + T * S + 330))
    px = lambda x: ox + x * S
    py = lambda y: oy + y * S
    lo, hi = (SH.get('edge_x') or (0.0, W)) if SH else (0.0, W)
    g.text(ox - 290, 52, 'famicart %s　基板外形図' % D.REV, 34, INK, 'start', 'bold')
    g.text(ox - 290, 92, '表（ラベル面・1〜30 番端子の面）から見た図　単位 mm　設計値（製造公差: ルーター加工 ±0.2 mm）', 21, MUTED, 'start')
    # edge rails that JLCPCB adds for assembly (not part of the board)
    for x0, x1, lab in ((lo - 5.0, lo, '捨て基板'), (hi, hi + 5.0, '捨て基板')):
        g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#f3f4f6" stroke="#9ca3af" stroke-width="1.2" stroke-dasharray="7 5"/>' % (px(x0), py(0), (x1 - x0) * S, T * S))
        g.text(px((x0 + x1) / 2) + 7, py(34), lab + '（JLCPCB が付け、実装後に外す）', 17, MUTED, 'middle', rot=-90)
    board_shape(g, ox, oy)
    # tab base and centre line
    g.line(px(X0), py(H), px(X1), py(H), MUTED, 1.0, '4 5')
    g.line(px(W / 2), py(-3), px(W / 2), py(T + 2.5), MUTED, 1.0, '14 5 3 5')
    g.text(px(W / 2) + 8, py(-3) + 16, '中心線', 16, MUTED, 'start')
    for (num, a, b, c, d, front) in fingers(board):
        if front: g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#8a6d14" stroke-width="0.8"/>' % (px(a), py(b), (c - a) * S, (d - b) * S, GOLD))
    g.text(px(X0 + 3.2), py(H + 2.2), '1', 17, INK); g.text(px(X1 - 3.2), py(H + 2.2), '30', 17, INK)
    g.add('<rect x="%.1f" y="%.1f" width="520" height="24" fill="%s"/>' % (px(W / 2) - 260, py(H + 2.2) - 19, FILL))
    g.text(px(W / 2), py(H + 2.2), '金フィンガー 表 1〜30 番（裏 31〜60 番）　2.54 mm ピッチ', 18, INK)
    # ---- overall dimensions
    g.hdim(px(lo), px(hi), py(0) - 62, '%.1f（全幅）' % (hi - lo), ext=py(0))
    g.vdim(py(0), py(H), px(hi) + 100, '%.1f（本体）' % H, ext=px(hi), side='right')
    g.vdim(py(0), py(T), px(hi) + 250, '%.1f（全高）' % T, ext=px(hi), side='right')
    g.line(px(X1), py(T), px(hi) + 256, py(T), w=1.0)
    g.hdim(px(X0), px(X1), py(T) + 62, '%.1f（端子タブの幅）' % (X1 - X0), ext=py(T), below=True)
    if SH and SH.get('fillets'):
        body = SH['outline_body']
        xs = sorted({round(p[0], 3) for p in body}); ys = sorted({round(p[1], 3) for p in body})
        step_x = [x for x in xs if lo < x < X0][0]; notch_x = [x for x in xs if lo < x < X0 and x != step_x][0]
        step_y = max(y for y in ys if y < H); n0, n1 = [y for y in ys if 0 < y < step_y]
        g.hdim(px(step_x), px(W - step_x), py(T) + 128, '%.1f（下段の幅。左右とも %.1f 内側）' % (W - 2 * step_x, step_x - lo), ext=py(H), below=True)
        # chain on the left: top .. notch .. step .. tab base .. tab tip
        xc = px(lo) - 105
        for (a, b, lab) in ((0, n0, '%.1f' % n0), (n0, n1, '%.1f（切り欠き）' % (n1 - n0)), (n1, step_y, '%.1f' % (step_y - n1)), (step_y, H, '%.1f（下段）' % (H - step_y)), (H, T, '%.1f（端子タブ）' % (T - H))):
            g.vdim(py(a), py(b), xc, lab, ext=px(lo) - 54)
        g.line(px(lo) - 54, py(T), px(X0), py(T), w=1.0)
        # notch depth, slot, radii, chamfer
        g.hdim(px(lo), px(notch_x), py(n0) - 26, '%.2f' % (notch_x - lo), ext=py(n0), size=18)
        g.text(px(notch_x) + 10, py((n0 + n1) / 2) + 6, '左右の切り欠き（奥行き %.2f × 高さ %.1f）' % (notch_x - lo, n1 - n0), 18, INK, 'start')
        cut = SH['cutouts'][0]; cx0, cx1 = min(p[0] for p in cut), max(p[0] for p in cut); cy0, cy1 = min(p[1] for p in cut), max(p[1] for p in cut)
        g.hdim(px(cx0), px(cx1), py(cy0) - 26, '%.1f' % (cx1 - cx0), ext=py(cy0), size=18)
        g.text(px(hi) - 70, py(cy1) + 30, 'スリット %.1f × %.1f（中心線から右へ %.2f〜%.2f）' % (cx1 - cx0, cy1 - cy0, cx0 - W / 2, cx1 - W / 2), 18, INK, 'end')
        g.line(px(step_x) + 4, py(step_y) - 4, px(step_x) + 46, py(step_y) - 40, INK, 1.0)
        g.text(px(step_x) + 50, py(step_y) - 44, '内側の角は R%.1f（切り欠き・スリット・下段、計 %d か所）' % (SH['fillet_r'], len(SH['fillets'])), 18, INK, 'start')
    g.line(px(X1 - CH / 2) + 3, py(T - CH / 2) + 3, px(X1) + 34, py(T) + 30, INK, 1.0)
    g.text(px(X1) + 38, py(T) + 38, 'C%.1f' % CH, 18, INK, 'start')
    # ---- notes
    ny = py(T) + 190
    notes = ['板厚 %.1f mm・%d 層・FR-4。表面処理 ENIG（端子は金、先端 30° 面取り）。端子の銅は基板端の 1.0 mm 手前まで。' % (gen_pcb.THICKNESS, int(getattr(D, 'LAYERS', 2))),
             '任天堂の大型シェル（HVC-ExROM 系）用。左右の端は基準より 0.2 mm 内側の直線、切り欠きとスリットは角の丸みの分だけ 0.6 mm 広げてある。',
             'シェルの実物では未確認（最初はモジュールを付ける前に、基板だけをシェルに入れて確かめる）。']
    for i, s in enumerate(notes): g.text(ox - 290, ny + i * 32, '・' + s, 19, INK, 'start')
    g.save('outline.svg')

NAMES = {'U1': 'U1 Pico 2（CPU バス）', 'U2': 'U2 Pico 2（PPU バス）', 'U3': 'U3 XIAO（IRQ・音源）', 'U4': 'U4 Pico 2（増設・任意）', 'U5': 'U5 Pico 2（増設・任意）',
         'U6': 'U6 XIAO（ハブ）', 'U7': 'U7 フラッシュ', 'J3': 'J3 microSD（任意）', 'SW1': 'SW1', 'J2': 'J2', 'J4': 'J4'}
COLORS = {'Raspberry Pi Pico 2': '#bfe3c8', 'Seeed XIAO RP2350': '#c9dcf5'}

def draw_placement(board):
    gap, ox, oy = 150.0, 70.0, 170.0
    g = Svg(int(ox * 2 + 2 * W * S + gap), int(oy + T * S + 150))
    g.text(ox, 52, 'famicart %s　部品の配置' % D.REV, 34, INK, 'start', 'bold')
    g.text(ox, 92, '手はんだのモジュール・コネクタと、JLCPCB が実装する小さい部品（灰色）。裏面は裏から見た向き。単位 mm', 21, MUTED, 'start')
    for side, flip, bx, title in ((False, False, ox, '表（ラベル面）'), (True, True, ox + W * S + gap, '裏（裏から見た図。左右が入れ替わる）')):
        px = (lambda x, bx=bx, flip=flip: bx + ((W - x) if flip else x) * S)
        py = lambda y: oy + y * S
        g.text(bx + W * S / 2, oy - 22, title, 24, INK, 'middle', 'bold')
        pts = outline_points(); cuts = SH['cutouts'] if SH else []
        fl, r = (SH['fillets'], SH['fillet_r']) if SH and SH.get('fillets') else ([], 0.0)
        mir = (lambda p: (W - p[0], p[1])) if flip else (lambda p: p)
        g.add('<path d="%s" fill="%s" stroke="%s" stroke-width="2.4" stroke-linejoin="round"/>' % (path([mir(p) for p in pts][::-1] if flip else pts, [mir(f) for f in fl], r, bx, oy), FILL, EDGE))
        for cut in cuts:
            g.add('<path d="%s" fill="#ffffff" stroke="%s" stroke-width="2.4"/>' % (path([mir(p) for p in cut][::-1] if flip else list(cut), [mir(f) for f in fl], r, bx, oy), EDGE))
        for (num, a, b, c, d, front) in fingers(board):
            if front != side:
                xa, xb = sorted((px(a), px(c)))
                g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#8a6d14" stroke-width="0.6"/>' % (xa, py(b), xb - xa, (d - b) * S, GOLD))
        g.text(px(X0 + 3.0), py(H + 2.3), '31' if side else '1', 16, INK); g.text(px(X1 - 3.0), py(H + 2.3), '60' if side else '30', 16, INK)
        big = []
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            if ref == 'J1' or fp.IsFlipped() != side: continue
            cy = fp.GetCourtyard(pcbnew.B_CrtYd if side else pcbnew.F_CrtYd).BBox()
            if cy.GetWidth() == 0: cy = fp.GetBoundingBox(False, False)
            a, b, c, d = ToMM(cy.GetX()), ToMM(cy.GetY()), ToMM(cy.GetRight()), ToMM(cy.GetBottom())
            xa, xb = sorted((px(a), px(c)))
            if ref in NAMES:
                usb = None                      # modules: pads 1 and the last pad sit at the USB end
                ends = [q for q in fp.Pads() if q.GetNumber() in ('1', '40' if 'Pico' in fp.GetValue() else '14')]
                if len(ends) == 2 and ref.startswith('U') and ref != 'U7':
                    ex = sum(ToMM(q.GetPosition().x) for q in ends) / 2 - ToMM(fp.GetPosition().x)
                    ey = sum(ToMM(q.GetPosition().y) for q in ends) / 2 - ToMM(fp.GetPosition().y)
                    usb = ((-1 if flip else 1) * (1 if ex > 0 else -1), 0) if abs(ex) > abs(ey) else (0, 1 if ey > 0 else -1)
                big.append((ref, xa, py(b), xb - xa, (d - b) * S, fp.GetValue(), usb))
            else:
                g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#9aa3ad" stroke="#6b7280" stroke-width="0.6"/>' % (xa, py(b), xb - xa, (d - b) * S))
        for (ref, x, y, w, h, val, usb) in sorted(big, key=lambda t: -t[3] * t[4]):
            g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="5" fill="%s" fill-opacity="0.86" stroke="%s" stroke-width="1.8"/>' % (x, y, w, h, COLORS.get(val, '#f1e3b6'), INK))
            if usb:                             # connector end: a dark tab on that edge of the module
                uw, ud = 84.0, 26.0
                if usb[0]: ux, uy, tw, th = (x + w - ud if usb[0] > 0 else x), y + h / 2 - uw / 2, ud, uw
                else: ux, uy, tw, th = x + w / 2 - uw / 2, (y + h - ud if usb[1] > 0 else y), uw, ud
                g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="#374151"/>' % (ux, uy, tw, th))
                if usb[0]: g.text(ux + tw / 2 + 5, uy + th / 2, 'USB', 15, '#ffffff', 'middle', 'bold', rot=-90)
                else: g.text(ux + tw / 2, uy + th / 2 + 5, 'USB', 15, '#ffffff', 'middle', 'bold')
            lab = NAMES[ref]; units = sum(1.0 if ord(ch) > 0x2E7F else 0.52 for ch in lab)
            vertical = h > w * 1.3 and w < 90
            room = (h if vertical else w) - 14 - (30 if usb and bool(usb[0]) != vertical else 0)
            size = int(max(11, min(22, room / units)))
            cx, cy = x + w / 2, y + h / 2
            if usb and not vertical and usb[0]: cx -= usb[0] * 13
            if usb and usb[1]: cy -= usb[1] * 10
            if vertical: g.text(cx + size * 0.36, cy, lab, size, INK, 'middle', rot=-90)
            else: g.text(cx, cy + size * 0.36, lab, size, INK, 'middle', 'bold' if size >= 18 else 'normal')
    ly = oy + T * S + 70
    g.text(ox, ly, '・基本構成は U1・U2・U3・U6 の 4 個。U4・U5 は 512 KB 級の PRG・CHR やコプロセッサ用の増設で、載せなくても動く。', 19, INK, 'start')
    g.text(ox, ly + 32, '・USB: U1・U4 は左端、U5・U3 は右端、U6 と microSD は上端に向く。U2 は基板の中央なので、はんだ付けの前に書き込む。', 19, INK, 'start')
    g.save('placement.svg')

def draw_rails(board):
    """The board with its edge rails, labelled in English: the picture to show JLCPCB's support (jlcpcb/rails.svg)."""
    RA = getattr(D, 'RAILS', None)
    if not RA: return
    lo, hi = SH['edge_x']; gap, rw = RA['gap'], RA['width']
    ox, oy = 330.0 + (gap + rw) * S, 170.0
    g = Svg(int(ox + (W + gap + rw) * S + 330), int(oy + T * S + 300))
    px = lambda x: ox + x * S
    py = lambda y: oy + y * S
    RED = '#b42318'
    g.text(40, 52, 'famicart %s - board with edge rails for Standard PCBA (top side, gold fingers at the bottom)' % D.REV, 26, INK, 'start', 'bold')
    g.text(40, 88, 'Dimensions in mm. Rails are joined by mouse-bite tabs (routed, no V-cut). 2 layers, 1.2 mm, ENIG, 30 degree bevel on the gold-finger edge.', 19, MUTED, 'start')
    rails = {'L': (lo - gap - rw, lo - gap), 'R': (hi + gap, hi + gap + rw)}
    YE = T - RA.get('end_gap', 0.0); ypos = lambda y: y if y >= 0 else YE + y
    for side, (xa, xb) in rails.items():
        g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#d9dde3" stroke="%s" stroke-width="2.2"/>' % (px(xa), py(0), (xb - xa) * S, YE * S, EDGE))
        g.text(px((xa + xb) / 2) + 7, py(T / 2), 'EDGE RAIL %.0f mm - break off' % rw, 18, INK, 'middle', rot=-90)
    for (side, y) in RA.get('tooling', ()):
        xa, xb = rails[side]
        g.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ffffff" stroke="%s" stroke-width="1.2"/>' % (px((xa + xb) / 2), py(ypos(y)), RA['tooling_d'] / 2 * S, INK))
        for yc in RA['tabs'][side]:
            ta, tb = (lo - gap, lo) if side == 'L' else (hi, hi + gap)
            g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#d9dde3" stroke="%s" stroke-width="1.6"/>' % (px(ta), py(yc - RA['tab'] / 2), (tb - ta) * S, RA['tab'] * S, EDGE))
            xe = lo - RA['hole_out'] if side == 'L' else hi + RA['hole_out']
            for i in range(RA['holes']):
                g.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ffffff" stroke="%s" stroke-width="0.8"/>' % (px(xe), py(yc + (i - (RA['holes'] - 1) / 2) * RA['pitch']), RA['hole'] / 2 * S, INK))
    for (side, y) in RA['fiducials']:
        xa, xb = rails[side]; x = xa + RA['fid_inset'] if side == 'L' else xb - RA['fid_inset']; y = ypos(y)
        g.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ffffff" stroke="%s" stroke-width="0.8"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (px(x), py(y), 1.0 * S, MUTED, px(x), py(y), 0.5 * S, GOLD))
    board_shape(g, ox, oy)
    for (num, a, b, c, d, front) in fingers(board):
        if front: g.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#8a6d14" stroke-width="0.8"/>' % (px(a), py(b), (c - a) * S, (d - b) * S, GOLD))
    # the gold-finger edge
    g.line(px(X0), py(T) + 5, px(X1), py(T) + 5, RED, 5.0)
    g.text(px(W / 2), py(T) + 40, 'GOLD FINGERS on this edge only (60 fingers) - bevel 30 degrees', 22, RED, 'middle', 'bold')
    g.text(px(W / 2), py(T) + 70, 'This edge must stay a free routed edge: no rail, no V-cut, no mouse bites', 20, RED, 'middle')
    # labels
    yc = RA['tabs']['L'][1]
    g.line(px(lo - gap / 2), py(yc), px(lo) + 150, py(yc) - 60, INK, 1.0)
    g.text(px(lo) + 156, py(yc) - 64, 'mouse-bite tab %.1f mm wide: %d holes of %.1f mm, %.1f mm apart,' % (RA['tab'], RA['holes'], RA['hole'], RA['pitch'] - RA['hole']), 18, INK, 'start')
    g.text(px(lo) + 156, py(yc) - 40, 'touching the board edge line from outside (3 tabs on each side)', 18, INK, 'start')
    fs, fy = RA['fiducials'][0]; fx = rails[fs][0] + RA['fid_inset']
    g.line(px(fx), py(fy), px(lo) + 110, py(fy) + 46, INK, 1.0)
    g.text(px(lo) + 116, py(fy) + 52, 'fiducial (3 in total): copper 1 mm, solder mask opening 2 mm,', 18, INK, 'start')
    g.text(px(lo) + 116, py(fy) + 76, 'centre %.2f mm from the panel edges' % RA['fid_inset'], 18, INK, 'start')
    if RA.get('tooling'):
        ts, ty = RA['tooling'][0]; tx = (rails[ts][0] + rails[ts][1]) / 2
        g.line(px(tx), py(ypos(ty)), px(lo) + 110, py(ypos(ty)) + 60, INK, 1.0)
        g.text(px(lo) + 116, py(ypos(ty)) + 66, 'tooling hole %.1f mm, not plated (%d in total)' % (RA['tooling_d'], len(RA['tooling'])), 18, INK, 'start')
    g.text(px(W / 2), py(59), 'CARTRIDGE BOARD  %.1f x %.1f' % (hi - lo, T), 24, EDGE, 'middle', 'bold')
    g.text(px(W / 2), py(59) + 30, 'parts on this side are placed by JLCPCB', 18, EDGE, 'middle')
    # dimensions
    g.hdim(px(rails['L'][0]), px(rails['R'][1]), py(0) - 34, '%.1f (with rails)' % (hi - lo + 2 * (gap + rw)), ext=py(0))
    g.vdim(py(0), py(T), px(rails['R'][1]) + 60, '%.1f' % T, ext=px(rails['R'][1]), side='right')
    if RA.get('end_gap'):
        g.vdim(py(YE), py(T), px(rails['R'][0]) - 26, '%.1f' % RA['end_gap'], size=18, side='left')
        g.text(px(rails['R'][1]) + 80, py(YE) - 6, 'rails stop above', 16, MUTED, 'start'); g.text(px(rails['R'][1]) + 80, py(YE) + 14, 'the finger edge', 16, MUTED, 'start')
    g.hdim(px(rails['L'][0]), px(rails['L'][1]), py(T) + 110, '%.1f' % rw, ext=py(YE), size=18, below=True)
    g.hdim(px(rails['L'][1]), px(lo), py(T) + 150, '%.1f gap' % gap, ext=py(YE), size=18, below=True)
    ny = py(T) + 215
    g.text(40, ny, 'If JLCPCB adds the rails instead (Gerber without rails): please put them on the left and right edges (the two %.1f mm edges), panel %.1f x %.1f mm,' % (T, hi - lo + 2 * rw, T), 19, INK, 'start')
    g.text(40, ny + 28, 'not on the gold-finger edge and not on the opposite edge, although those are the longer edges.', 19, INK, 'start')
    os.makedirs(os.path.join(HW, 'jlcpcb'), exist_ok=True)
    g.save(os.path.join('jlcpcb', 'rails.svg'))

def main():
    board = pcbnew.LoadBoard(os.path.join(HW, 'famicart.kicad_pcb'))
    draw_outline(board); draw_placement(board); draw_rails(board)

if __name__ == '__main__':
    main()
