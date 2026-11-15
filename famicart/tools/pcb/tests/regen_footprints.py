#!/usr/bin/env python3
"""Regenerate the five rev H footprints of famicart.pretty from their sources and check that the committed files are
exactly what comes out (default), or write them (--write):
  Famicom_CardEdge_60_M                         from famicart.pretty/Famicom_CardEdge_60 (mirrored, sides swapped)
  QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia   from famicart.pretty/QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm (holes out)
  USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC       from KiCad's USB_C_Receptacle_HRO_TYPE-C-31-M-12 and the origin of
                                                JLCPCB's library footprint of C165948
  microSD_HRO_TF-01A, L_SXN_SMNR4020            from JLCPCB's library footprints of C91145 and C135262
The JLCPCB / EasyEDA library data are <code>.json files as check_footprints_easyeda.py --fetch saves them; they are data
from the network, so run this with python3 -I.
    python3 -I tests/regen_footprints.py --cache DIR [--write] [--kicad /usr/share/kicad/footprints]"""
import json, os, re, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'hardware', 'famicart.pretty'))
DL = SYS = None
NAMES = ('Famicom_CardEdge_60_M', 'QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia', 'USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC',
         'microSD_HRO_TF-01A', 'L_SXN_SMNR4020')

def easyeda(code):
    d = json.load(open(os.path.join(DL, code + '.json')))['result']
    data = d['packageDetail']['dataStr']; ox, oy = float(data['head']['x']), float(data['head']['y'])
    pads, holes, body = [], [], None
    for s in data['shape']:
        f = s.split('~')
        if f[0] == 'PAD' and f[8]:
            pads.append(dict(num=f[8], x=(float(f[2]) - ox) * 0.254, y=(float(f[3]) - oy) * 0.254, w=float(f[4]) * 0.254, h=float(f[5]) * 0.254,
                             shape=f[1], layer=f[6]))
        elif f[0] == 'HOLE':
            holes.append(((float(f[1]) - ox) * 0.254, (float(f[2]) - oy) * 0.254, 2 * float(f[3]) * 0.254))
        elif f[0] == 'SOLIDREGION' and f[1] == '99':
            nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', f[3])]
            xs, ys = nums[0::2], nums[1::2]
            body = ((min(xs) - ox) * 0.254, (min(ys) - oy) * 0.254, (max(xs) - ox) * 0.254, (max(ys) - oy) * 0.254)
    return d['packageDetail']['title'], pads, holes, body

def f3(v):
    v = round(v, 3)
    if v == 0: v = 0.0
    return ('%.3f' % v).rstrip('0').rstrip('.')

# ------------------------------------------------------------------ 1. card edge seen from the back
def card_edge_m():
    src = open(os.path.join(PRETTY, 'Famicom_CardEdge_60.kicad_mod')).read().split('\n')
    out = []
    for l in src:
        if l.startswith('(footprint "Famicom_CardEdge_60"'):
            l = l.replace('"Famicom_CardEdge_60"', '"Famicom_CardEdge_60_M"')
        elif l.strip().startswith('(descr'):
            l = ('  (descr "Famicom 60-pin card edge for a board drawn as seen from the BACK of the cartridge (rev H): the original '
                 'Famicom_CardEdge_60 mirrored in x, copper layers swapped. Pins 31-60 on F.Cu (left to right seen from the back: '
                 '31 on the right), pins 1-30 on B.Cu, pin N+30 behind pin N, every pad keeps its own size (1, 30, 31 wide, 16 long).")')
        elif l.strip().startswith('(pad '):
            m = re.match(r'(\s*\(pad "\d+" smd rect \(at )(-?[\d.]+)( [\d.]+\).*\(layers )"(F|B)\.Cu" "(F|B)\.Mask"(.*)$', l)
            assert m, l
            x = -float(m.group(2)); side = {'F': 'B', 'B': 'F'}[m.group(4)]
            l = '%s%.3f%s"%s.Cu" "%s.Mask"%s' % (m.group(1), x, m.group(3), side, side, m.group(6))
        elif l.strip().startswith('(fp_text user'):
            m = re.match(r'(\s*\(fp_text user "\d+" \(at )(-?[\d.]+)( [\d.]+\) \(layer )"(F|B)\.Fab"\)( \(effects \(font \(size 0\.8 0\.8\) \(thickness 0\.12\)\))( \(justify mirror\))?(\)\))$', l)
            assert m, l
            side = {'F': 'B', 'B': 'F'}[m.group(4)]
            l = '%s%g%s"%s.Fab")%s%s%s' % (m.group(1), -float(m.group(2)), m.group(3), side, m.group(5), ' (justify mirror)' if side == 'B' else '', m.group(7))
        out.append(l)
    head = '''# Famicom_CardEdge_60_M -- the Famicom card edge for a board drawn as seen from the BACK of the cartridge.
#
# Why: rev H puts its main components on the back of the cartridge and draws the board from that side, so that the
# back is KiCad's F.Cu and JLCPCB's "Top" (docs/13_rev_h_plan.md, "基板データの描き方"; shells.mirrored() does the
# same to the shell outline and keep-outs).
#
# Geometry, derived from Famicom_CardEdge_60 (drawn from the FRONT: pins 1-30 on F.Cu, pin 1 at x = -37.33 on the
# left, pins 31-60 on B.Cu, pin N+30 directly behind pin N):
#   * seen from the back, left and right change places: every pad and Fab label x becomes -x (the footprint origin
#     stays on the tab centre line at the shoulder; y is unchanged, so the fingers still hang below y = 0);
#   * the back is now the viewer's side: pins 31-60 move to F.Cu / F.Mask, pins 1-30 to B.Cu / B.Mask;
#   * so pin 31 is at x = +37.33 on F.Cu (the right end seen from the back) and pin 1 is directly behind it on B.Cu,
#     pin 60 is at x = -36.83 on F.Cu with pin 30 behind it at x = -37.33 on B.Cu, and pin N+30 is behind pin N
#     everywhere, exactly as in the original;
#   * every pad keeps its own size: 1, 30 and 31 are the wide 2.6 x 6.7 pads, 16 is the long 1.6 x 6.7 pad, 46 and 60
#     are normal 1.6 x 5.7 pads (the original's pad 60 sits 0.5 mm inboard of pad 30 so that their inner edges line up).
# Placed unflipped (side 'F') with the board drawn from the back, this is the same copper as Famicom_CardEdge_60
# placed on a board drawn from the front. tests/test_geometry_gen.py checks every pad against the original.
'''
    return head + '\n'.join(out)

# ------------------------------------------------------------------ 2. QFN-80 without the vias in the exposed pad
def qfn_novia():
    src = open(os.path.join(PRETTY, 'QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm.kicad_mod')).read().split('\n')
    out = []
    for l in src:
        if l.startswith('(footprint '):
            l = l.replace('"QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm"', '"QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia"')
        elif l.strip().startswith('(descr'):
            l = ('  (descr "QFN-80 10x10 mm, 0.4 mm pitch, 3.4 mm exposed pad -- RP2350B recommended land pattern (datasheet Fig.150), '
                 'without the nine plated holes in the exposed pad: the vias are board vias placed by gen_pcb.py (design EP_VIAS)")')
        elif re.match(r'\s*\(pad "81" thru_hole ', l):
            continue
        out.append(l)
    head = '''# QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia -- QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm without the nine plated
# through-hole pads "81" (0.3 / 0.6 mm, 1.1 mm grid) inside the exposed pad. Everything else is unchanged: pads 1-80,
# the 3.4 x 3.4 mm exposed pad "81" (no paste of its own) and the four 1.3 x 1.3 mm paste windows on it.
# Why (docs/13_rev_h_plan.md, "ツールの変更"): with the holes the footprint has 90 numbered pads where JLCPCB's library
# footprint of the RP2350B (C42415655) has 81, so the CPL check cannot match it, and holes that belong to a footprint
# may not be treated as vias (epoxy filling and capping of via-in-pad on 6-layer boards). gen_pcb.py puts real board
# vias into the exposed pad instead when the design asks for it (EP_VIAS).
'''
    return head + '\n'.join(out)

# ------------------------------------------------------------------ 3. USB-C with the origin of JLCPCB's library footprint
def usb_c():
    title, lp, holes, body = easyeda('C165948')
    src = open(os.path.join(SYS, 'Connector_USB.pretty', 'USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod')).read()
    kp = [(m.group(1), float(m.group(2)), float(m.group(3))) for m in re.finditer(r'\(pad "([A-Z0-9]+)" \w+ \w+ \(at (-?[\d.]+) (-?[\d.]+)\)', src)]
    names = lambda n: ['S1'] if n.isdigit() else re.findall(r'[AB]\d+', n)
    dx, dy = [], []
    for p in lp:            # one offset per EasyEDA pad (a pad named for two pins, e.g. A1B12, counts once)
        ks = [min((k for k in kp if k[0] == n), key=lambda k: (k[1] - p['x']) ** 2 + (k[2] - p['y']) ** 2) for n in names(p['num'])]
        dx.append(p['x'] - sum(k[1] for k in ks) / len(ks)); dy.append(p['y'] - sum(k[2] for k in ks) / len(ks))
    sx, sy = sum(dx) / len(dx), sum(dy) / len(dy)
    s = round(sy, 2)
    worst = 0.0
    for p in lp:
        for n in names(p['num']):
            k = min((k for k in kp if k[0] == n), key=lambda k: (k[1] - p['x']) ** 2 + (k[2] + s - p['y']) ** 2)
            worst = max(worst, ((k[1] - p['x']) ** 2 + (k[2] + s - p['y']) ** 2) ** 0.5)
    print('USB-C: worst pad distance after the move %.3f mm' % worst)
    print('USB-C: mean offset of KiCad -> EasyEDA pads x %.4f y %.4f (%d EasyEDA pads); origin moved by %.2f mm in y' % (sx, sy, len(dy), s))
    out = []
    for l in src.split('\n'):
        if 'tstamp' in l and l.strip().startswith('(tstamp'): continue
        if '(start -4.7 3.9) (end 4.7 3.9) (layer "F.SilkS")' in l: continue      # silk line across the mouth: dropped
        l = l.replace('(start -4.7 2) (end -4.7 3.9)', '(start -4.7 2) (end -4.7 3.15)').replace('(start 4.7 2) (end 4.7 3.9)', '(start 4.7 2) (end 4.7 3.15)')
        l = re.sub(r'\s*\(tstamp [0-9a-f-]+\)', '', l)
        l = re.sub(r'\((at|start|end) (-?[\d.]+) (-?[\d.]+)', lambda m: '(%s %s %s' % (m.group(1), m.group(2), f3(float(m.group(3)) + s)), l)
        l = l.replace('(footprint "USB_C_Receptacle_HRO_TYPE-C-31-M-12"', '(footprint "USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC"')
        l = l.replace('(version 20211014) (generator pcbnew)', '(version 20211014) (generator famicart)')
        if l.strip().startswith('(descr'):
            l = ('  (descr "USB Type-C receptacle for USB 2.0 and PD, HRO TYPE-C-31-M-12 (LCSC C165948): KiCad\'s '
                 'USB_C_Receptacle_HRO_TYPE-C-31-M-12 with its origin moved to the origin of JLCPCB\'s library footprint '
                 '(%s), all items %.2f mm further in +y; http://www.krhro.com/uploads/soft/180320/1-1P320120243.pdf")' % (title, s))
        if l.strip().startswith('(tedit'): continue
        l = l.replace('(offset (xyz 0 0 0))', '(offset (xyz 0 %s 0))' % f3(-s))
        out.append(l)
    head = '''# USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC -- KiCad's USB_C_Receptacle_HRO_TYPE-C-31-M-12 (KiCad 7 library) with
# the footprint origin moved to the origin of JLCPCB's library footprint of the part (LCSC C165948, EasyEDA
# "%s"). JLCPCB places the part with ITS footprint at the CPL position, so the two origins have
# to be the same point: every pad, hole, line and text is %.2f mm further in +y (toward the mouth) than in KiCad's
# footprint (pad sizes, holes and numbers are KiCad's). One change besides: the silkscreen line across the mouth is
# left out and the two side lines end 0.5 mm before the mouth (KiCad's run 0.25 mm past it), because the mouth stands
# at the board's top edge (rev H) and the board edge would cut them off.
# The offset is the mean y offset of the 16 EasyEDA pads from their KiCad pads: 12 signal pads, four of them named
# for two pins each ("A1B12" = KiCad's A1 and B12 on one spot), and the four shell pads "1"-"4" = KiCad's "S1". The
# signal pads alone are 1.57 mm off, the shell pads 1.42 mm. After the move every EasyEDA pad centre lies within
# %.2f mm of its KiCad pad centre (tests/check_footprints_easyeda.py; check_cpl.py allows 0.40 mm).
# The pin names stay KiCad's (A1, B12, S1, ...): the CPL check needs a name map for this part.
''' % (title, s, worst)
    return head + '\n'.join(out)

# ------------------------------------------------------------------ 4. microSD TF-01A
def tf01a():
    title, lp, holes, body = easyeda('C91145')
    bx0, by0, bx1, by1 = body
    L = []
    L.append('(footprint "microSD_HRO_TF-01A" (version 20221018) (generator famicart)')
    L.append('  (layer "F.Cu")')
    L.append('  (descr "microSD socket, push-push with card detect, HRO TF-01A (LCSC C91145): pads, holes and body from JLCPCB\'s library footprint %s. '
             'Pins 1-8 card contacts (1 DAT2, 2 CD/DAT3, 3 CMD, 4 VDD, 5 CLK, 6 VSS, 7 DAT0, 8 DAT1), 9 card detect, 10-13 shell (GND). Card mouth at +y.")' % title)
    L.append('  (tags "micro SD TF card socket push-push detect")')
    L.append('  (attr smd)')
    L.append('  (fp_text reference "REF**" (at 0 %s) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))' % f3(by0 - 2.0))
    L.append('  (fp_text value "TF-01A" (at 0 %s) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % f3((by0 + by1) / 2 + 1.5))
    L.append('  (fp_text user "${REFERENCE}" (at 0 %s) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % f3((by0 + by1) / 2))
    L.append('  (fp_rect (start %s %s) (end %s %s) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))' % (f3(bx0), f3(by0), f3(bx1), f3(by1)))
    # courtyard: body and pads, 0.25 mm around
    xs = [bx0, bx1] + [p['x'] - p['w'] / 2 for p in lp] + [p['x'] + p['w'] / 2 for p in lp]
    ys = [by0, by1] + [p['y'] - p['h'] / 2 for p in lp] + [p['y'] + p['h'] / 2 for p in lp]
    cx0, cy0, cx1, cy1 = (round(min(xs) - 0.25, 2), round(min(ys) - 0.25, 2), round(max(xs) + 0.25, 2), round(max(ys) + 0.25, 2))
    L.append('  (fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))' % (f3(cx0), f3(cy0), f3(cx1), f3(cy1)))
    # silkscreen: the two long sides between the shell pads (0.2 mm from any pad), and a pin-1 mark above pad 1
    def clear_span(x, lo, hi):
        """parts of the vertical line x = x, lo..hi that keep 0.2 mm + half the line from every pad"""
        cuts = []
        for p in lp:
            if abs(x - p['x']) < p['w'] / 2 + 0.275: cuts.append((p['y'] - p['h'] / 2 - 0.275, p['y'] + p['h'] / 2 + 0.275))
        spans, a = [], lo
        for c0, c1 in sorted(cuts):
            if c0 > a: spans.append((a, min(c0, hi)))
            a = max(a, c1)
        if a < hi: spans.append((a, hi))
        return [sp for sp in spans if sp[1] - sp[0] > 0.3]
    for x in (bx0 - 0.11, bx1 + 0.11):
        for a, b in clear_span(x, by0 - 0.11, by1 - 1.5):      # (the mouth end may stand at the board edge: no silk there)
            L.append('  (fp_line (start %s %s) (end %s %s) (stroke (width 0.15) (type default)) (layer "F.SilkS"))' % (f3(x), f3(a), f3(x), f3(b)))
    p1 = [p for p in lp if p['num'] == '1'][0]
    L.append('  (fp_line (start %s %s) (end %s %s) (stroke (width 0.15) (type default)) (layer "F.SilkS"))'
             % (f3(p1['x'] - 0.3), f3(p1['y'] - p1['h'] / 2 - 0.35), f3(p1['x'] + 0.3), f3(p1['y'] - p1['h'] / 2 - 0.35)))
    for p in sorted(lp, key=lambda p: int(p['num'])):
        assert p['shape'] == 'RECT' and p['layer'] == '1'
        L.append('  (pad "%s" smd rect (at %s %s) (size %s %s) (layers "F.Cu" "F.Paste" "F.Mask"))' % (p['num'], f3(p['x']), f3(p['y']), f3(p['w']), f3(p['h'])))
    for (x, y, d) in holes:
        L.append('  (pad "" np_thru_hole circle (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask"))' % (f3(x), f3(y), f3(d), f3(d), f3(d)))
    L.append(')')
    head = '''# microSD_HRO_TF-01A -- HRO TF-01A push-push microSD socket with card detect (LCSC C91145, JLCPCB Extended).
# Drawn from JLCPCB's library footprint (EasyEDA "%s"), so that its origin, pad numbers and pads are the ones JLCPCB
# places with: 13 SMD pads (1-8 card contacts at 1.1 mm pitch, 9 card detect, 10-13 shell tabs) and two 1.0 mm
# non-plated locating holes, all taken over to 0.001 mm; the Fab outline is the library's body outline (%.2f x %.2f mm),
# the courtyard is body and pads plus 0.25 mm, the card mouth is the +y edge. Pin functions as in the EasyEDA symbol
# (not checked against the HRO drawing). tests/check_footprints_easyeda.py compares it with the library footprint.
''' % (title, bx1 - bx0, by1 - by0)
    return head + '\n'.join(L)

# ------------------------------------------------------------------ 5. 2.2 uH SMNR4020
def smnr4020():
    title, lp, holes, body = easyeda('C135262')
    bx0, by0, bx1, by1 = body
    L = ['(footprint "L_SXN_SMNR4020" (version 20221018) (generator famicart)', '  (layer "F.Cu")',
         '  (descr "Shielded power inductor 4.0 x 4.0 mm, SXN SMNR4020 (2.2 uH: LCSC C135262): pads and body from JLCPCB\'s library footprint %s")' % title,
         '  (tags "inductor SMNR4020 4020")', '  (attr smd)',
         '  (fp_text reference "REF**" (at 0 %s) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))' % f3(by0 - 1.2),
         '  (fp_text value "SMNR4020" (at 0 %s) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % f3(by1 + 1.2),
         '  (fp_text user "${REFERENCE}" (at 0 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
         '  (fp_rect (start %s %s) (end %s %s) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))' % (f3(bx0), f3(by0), f3(bx1), f3(by1))]
    xs = [bx0, bx1] + [p['x'] - p['w'] / 2 for p in lp] + [p['x'] + p['w'] / 2 for p in lp]
    ys = [by0, by1] + [p['y'] - p['h'] / 2 for p in lp] + [p['y'] + p['h'] / 2 for p in lp]
    L.append('  (fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))'
             % (f3(round(min(xs) - 0.25, 2)), f3(round(min(ys) - 0.25, 2)), f3(round(max(xs) + 0.25, 2)), f3(round(max(ys) + 0.25, 2))))
    inner = min(abs(p['x']) - p['w'] / 2 for p in lp) - 0.3          # silk between the pads, 0.2 mm + half the line from them
    for y in (by0 - 0.15, by1 + 0.15):
        L.append('  (fp_line (start %s %s) (end %s %s) (stroke (width 0.15) (type default)) (layer "F.SilkS"))' % (f3(-inner), f3(y), f3(inner), f3(y)))
    for p in sorted(lp, key=lambda p: int(p['num'])):
        assert p['shape'] == 'RECT' and p['layer'] == '1'
        L.append('  (pad "%s" smd rect (at %s %s) (size %s %s) (layers "F.Cu" "F.Paste" "F.Mask"))' % (p['num'], f3(p['x']), f3(p['y']), f3(p['w']), f3(p['h'])))
    L.append(')')
    head = '''# L_SXN_SMNR4020 -- shielded SMD power inductor 4.0 x 4.0 mm, SXN SMNR4020 series (2.2 uH: LCSC C135262, JLCPCB Extended).
# Drawn from JLCPCB's library footprint (EasyEDA "%s"): two 1.5 x 4.0 mm pads 3.6 mm apart (centres), origin in the
# middle, body outline 4.0 x 4.0 mm on the Fab layer, courtyard pads and body plus 0.25 mm. No polarity.
# tests/check_footprints_easyeda.py compares it with the library footprint.
''' % title
    return head + '\n'.join(L)

def generate():
    """{footprint name: file text}"""
    fns = (card_edge_m, qfn_novia, usb_c, tf01a, smnr4020)
    return {name: fn().rstrip('\n') + '\n' for name, fn in zip(NAMES, fns)}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--cache', required=True); ap.add_argument('--write', action='store_true')
    ap.add_argument('--kicad', default='/usr/share/kicad/footprints'); a = ap.parse_args()
    DL, SYS = os.path.abspath(a.cache), a.kicad
    bad = 0
    for name, txt in generate().items():
        p = os.path.join(PRETTY, name + '.kicad_mod')
        if a.write:
            open(p, 'w').write(txt); print('written', p)
        else:
            same = os.path.exists(p) and open(p).read() == txt
            print('%-48s %s' % (name, 'identical to the regenerated file' if same else 'DIFFERS from the regenerated file'))
            bad += not same
    sys.exit(1 if bad else 0)
