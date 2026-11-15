#!/usr/bin/env python3
"""Regenerate the five rev H footprints of famicart.pretty from their sources and check that the committed files are
exactly what comes out (default), or write them (--write):
  Famicom_CardEdge_60_M                         from famicart.pretty/Famicom_CardEdge_60 (mirrored, sides swapped)
  QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia   from famicart.pretty/QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm (holes out)
  USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC       from HRO's drawing of TYPE-C-31-M-12 (HRO_USB below), placed on the
                                                origin of JLCPCB's library footprint of C165948
  microSD_HRO_TF-01A, L_SXN_SMNR4020            from JLCPCB's library footprints of C91145 and C135262
and famicart.pretty/README.md, which explains them. The .kicad_mod files carry a short (descr ...) and no comment
lines: KiCad's footprint editor and "kicad-cli fp upgrade" drop comment lines when they save a footprint.
The JLCPCB / EasyEDA library data are <code>.json files as check_footprints_easyeda.py --fetch saves them; they are data
from the network, so run this with python3 -I.
    python3 -I tests/regen_footprints.py --cache DIR [--write] [--kicad /usr/share/kicad/footprints]"""
import json, math, os, re, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PRETTY = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'hardware', 'famicart.pretty'))
DL = SYS = None
NAMES = ('Famicom_CardEdge_60_M', 'QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia', 'USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC',
         'microSD_HRO_TF-01A', 'L_SXN_SMNR4020')
README = {}                 # footprint name -> its section of famicart.pretty/README.md (filled by the generators)

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
                 '31 on the right), pins 1-30 on B.Cu, pin N+30 behind pin N, every pad keeps its own size (1, 30, 31 wide, 16 long). '
                 'See famicart.pretty/README.md.")')
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
    README['Famicom_CardEdge_60_M'] = '''The Famicom card edge for a board drawn as seen from the BACK of the cartridge.

Why: rev H puts its main components on the back of the cartridge and draws the board from that side, so that the
back is KiCad's F.Cu and JLCPCB's "Top" (docs/13_rev_h_plan.md, "基板データの描き方"; shells.mirrored() does the
same to the shell outline and keep-outs).

Geometry, derived from Famicom_CardEdge_60 (drawn from the FRONT: pins 1-30 on F.Cu, pin 1 at x = -37.33 on the
left, pins 31-60 on B.Cu, pin N+30 directly behind pin N):
- seen from the back, left and right change places: every pad and Fab label x becomes -x (the footprint origin
  stays on the tab centre line at the shoulder; y is unchanged, so the fingers still hang below y = 0);
- the back is now the viewer's side: pins 31-60 move to F.Cu / F.Mask, pins 1-30 to B.Cu / B.Mask;
- so pin 31 is at x = +37.33 on F.Cu (the right end seen from the back) and pin 1 is directly behind it on B.Cu,
  pin 60 is at x = -36.83 on F.Cu with pin 30 behind it at x = -37.33 on B.Cu, and pin N+30 is behind pin N
  everywhere, exactly as in the original;
- every pad keeps its own size: 1, 30 and 31 are the wide 2.6 x 6.7 pads, 16 is the long 1.6 x 6.7 pad, 46 and 60
  are normal 1.6 x 5.7 pads (the original's pad 60 sits 0.5 mm inboard of pad 30 so that their inner edges line up).

Placed unflipped (side 'F') with the board drawn from the back, this is the same copper as Famicom_CardEdge_60
placed on a board drawn from the front. tests/test_geometry_gen.py checks every pad against the original.
'''
    return '\n'.join(out)

# ------------------------------------------------------------------ 2. QFN-80 without the vias in the exposed pad
def qfn_novia():
    src = open(os.path.join(PRETTY, 'QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm.kicad_mod')).read().split('\n')
    out = []
    for l in src:
        if l.startswith('(footprint '):
            l = l.replace('"QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm"', '"QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia"')
        elif l.strip().startswith('(descr'):
            l = ('  (descr "QFN-80 10x10 mm, 0.4 mm pitch, 3.4 mm exposed pad -- RP2350B recommended land pattern (datasheet Fig.150), '
                 'without the nine plated holes in the exposed pad: the vias are board vias placed by gen_pcb.py (design EP_VIAS). '
                 'See famicart.pretty/README.md.")')
        elif re.match(r'\s*\(pad "81" thru_hole ', l):
            continue
        out.append(l)
    README['QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia'] = '''QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm without the nine plated through-hole pads "81" (0.3 / 0.6 mm, 1.1 mm
grid) inside the exposed pad. Everything else is unchanged: pads 1-80, the 3.4 x 3.4 mm exposed pad "81" (no paste of
its own) and the four 1.3 x 1.3 mm paste windows on it.

Why (docs/13_rev_h_plan.md, "ツールの変更"): with the holes the footprint has 90 numbered pads where JLCPCB's library
footprint of the RP2350B (C42415655) has 81, so the CPL check cannot match it, and holes that belong to a footprint
may not be treated as vias (epoxy filling and capping of via-in-pad on 6-layer boards). gen_pcb.py puts real board
vias into the exposed pad instead when the design asks for it (EP_VIAS).
'''
    return '\n'.join(out)

# ------------------------------------------------------------------ 3. USB-C: HRO's land pattern on JLCPCB's origin
# HRO's drawing of TYPE-C-31-M-12: the datasheet LCSC / JLCPCB give for C165948 (lcsc_datasheet_2205251630_Korean-
# Hroparts-Elec-TYPE-C-31-M-12_C165948.pdf, drawing dated 2020-12-08), "RECOMMEND P.C.B LAYOUT (COMPONENT SIDE)",
# tolerance +-0.05 mm, read 2026-11-15. Along the connector, distances are from the line of the two peg holes, positive
# toward the mouth (+y in the footprint).
HRO_USB = dict(
    pad_x={'A1': -3.20, 'B12': -3.20, 'A4': -2.40, 'B9': -2.40, 'B8': -1.75, 'A5': -1.25, 'B7': -0.75, 'A6': -0.25,
           'A7': 0.25, 'B6': 0.75, 'A8': 1.25, 'B5': 1.75, 'B4': 2.40, 'A9': 2.40, 'B1': 3.20, 'A12': 3.20},
           # centre to centre 6.40 (A1/B12 - B1/A12), 4.80 (A4/B9 - B4/A9), 3.50 (B8 - B5), 2.50 (A5 - A8), 1.50 (B7 - B6), 0.50 (A6 - A7)
    pad_w={'A1': 0.60, 'B12': 0.60, 'A4': 0.60, 'B9': 0.60, 'B4': 0.60, 'A9': 0.60, 'B1': 0.60, 'A12': 0.60},     # "4-0.60"; the other eight "8-0.30"
    narrow=0.30,
    pad_y=(-1.64, -0.50),       # the signal pads run from 1.64 to 0.50 mm behind the peg line (dimensions "1.64" and "0.50")
    peg_x=5.78 / 2, peg_d=0.60, # "5.78" between the peg holes, holes "Φ0.60" (pegs "2-Φ0.50")
    leg_x=8.65 / 2,             # "8.65" between the shell legs
    rear_leg=(-0.50, 0.60, 1.70),          # centre on the line of the pads' front ends, slot 0.60 x 1.70 (copper 0.90 x 2.00)
    front_leg=(4.18 - 0.50, 0.60, 1.40),   # "4.18" from the pads' front ends, slot 0.60 x 1.40 (copper 0.90 x 1.70)
    body=(8.94, 7.35, 6.28))    # body width and length (top view), mouth "6.28" ahead of the peg line; PCB edge "5.79" ahead
RING = 0.20                     # shell-leg copper around the slot: JLCPCB's PTH annular ring >= 0.20 mm (HRO draws 0.15)
HOLE_CLEAR = 0.25               # peg hole to signal pad: HRO's land leaves 0.20 (JLCPCB's NPTH-to-copper minimum), keep 0.25

def pad_front(H, step=0.01):
    """Distance of the pads' front ends behind the peg line: HRO's 0.50, moved back in 0.01 mm steps until every pad is
    HOLE_CLEAR from both peg holes."""
    front = -H['pad_y'][1]
    def gap(front):
        g = 9.0
        for n, x in H['pad_x'].items():
            w = H['pad_w'].get(n, H['narrow']); x0, x1 = x - w / 2, x + w / 2
            for hx in (-H['peg_x'], H['peg_x']):
                dx = max(x0 - hx, 0.0, hx - x1); dy = front               # the pads end `front` behind the hole centre
                g = min(g, math.hypot(dx, dy) - H['peg_d'] / 2)
        return g
    while gap(front) < HOLE_CLEAR - 1e-9: front = round(front + step, 6)
    return front, gap(-H['pad_y'][1]), gap(front)

def usb_c():
    title, lp, holes, body = easyeda('C165948')
    H = HRO_USB
    yp = round(sum(h[1] for h in holes) / len(holes), 3)          # the peg line in JLCPCB's footprint (its origin is ours)
    # what the three sources say (for the README): pad row centre behind the pegs, legs, pad x of the outer pads
    kic = open(os.path.join(SYS, 'Connector_USB.pretty', 'USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod')).read()
    kp = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(r'\(pad "([AB]\d+)" smd rect \(at (-?[\d.]+) (-?[\d.]+)\)', kic)}
    kh = [(float(m.group(1)), float(m.group(2))) for m in re.finditer(r'\(pad "" np_thru_hole circle \(at (-?[\d.]+) (-?[\d.]+)\)', kic)]
    ks = [(float(m.group(1)), float(m.group(2))) for m in re.finditer(r'\(pad "S1" thru_hole oval \(at (-?[\d.]+) (-?[\d.]+)\)', kic)]
    ky = kh[0][1]
    sig = [p for p in lp if not p['num'].isdigit()]; legs = [p for p in lp if p['num'].isdigit()]
    cmp_ = dict(
        hro=(-sum(H['pad_y']) / 2, -H['rear_leg'][0], H['front_leg'][0], abs(H['pad_x']['A1']), abs(H['pad_x']['A4']), 2 * H['peg_x'], 2 * H['leg_x']),
        easyeda=(yp - sig[0]['y'], yp - min(p['y'] for p in legs), max(p['y'] for p in legs) - yp, max(abs(p['x']) for p in sig), sorted({round(abs(p['x']), 3) for p in sig})[-2],
                 2 * max(abs(h[0]) for h in holes), 2 * max(abs(p['x']) for p in legs)),
        kicad=(ky - kp['A1'][1], ky - min(y for x, y in ks), max(y for x, y in ks) - ky, abs(kp['A1'][0]), abs(kp['A4'][0]), 2 * abs(kh[0][0]), 2 * abs(ks[0][0])))
    front, g_hro, g_ours = pad_front(H)
    y0, y1 = yp + H['pad_y'][0], yp - front
    pcy, plen = (y0 + y1) / 2, y1 - y0
    bw, bl, mouth = H['body']; ym = yp + mouth; yr = ym - bl
    pads = sorted(H['pad_x'], key=lambda n: (n[0], int(n[1:])))
    legs_ = [(-H['leg_x'], yp + H['front_leg'][0], H['front_leg']), (-H['leg_x'], yp + H['rear_leg'][0], H['rear_leg']),
             (H['leg_x'], yp + H['rear_leg'][0], H['rear_leg']), (H['leg_x'], yp + H['front_leg'][0], H['front_leg'])]
    # courtyard: body, pads and leg copper plus 0.25 mm, outward to 0.01 mm
    xs = [bw / 2, H['leg_x'] + H['rear_leg'][1] / 2 + RING]
    ylo = min(yr, y0, yp + H['rear_leg'][0] - H['rear_leg'][2] / 2 - RING) - 0.25; yhi = ym + 0.25
    cx = math.ceil(round((max(xs) + 0.25) * 100, 6)) / 100
    cy0, cy1 = math.floor(round(ylo * 100, 6)) / 100, math.ceil(round(yhi * 100, 6)) / 100
    L = ['(footprint "USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC" (version 20221018) (generator famicart)', '  (layer "F.Cu")',
         ('  (descr "USB Type-C receptacle for USB 2.0, HRO TYPE-C-31-M-12 (LCSC C165948): HRO\'s recommended layout (drawing 2020-12-08) on the '
          'origin of JLCPCB\'s library footprint %s, whose peg holes and shell legs it matches; pads from %s (HRO 0.50) to 1.64 mm behind the '
          'peg holes, shell-leg copper with a 0.20 mm ring. KiCad pad names. See famicart.pretty/README.md.")' % (title, f3(front))),
         '  (tags "usb usb-c 2.0 pd")', '  (attr smd)',
         '  (fp_text reference "REF**" (at 0 %s) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))' % f3(cy0 - 0.8),
         '  (fp_text value "USB_C_Receptacle_HRO_TYPE-C-31-M-12" (at 0 %s) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % f3(ym + 1.2),
         '  (fp_text user "${REFERENCE}" (at 0 %s) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % f3((yr + ym) / 2),
         '  (fp_rect (start %s %s) (end %s %s) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))' % (f3(-bw / 2), f3(yr), f3(bw / 2), f3(ym)),
         '  (fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))' % (f3(-cx), f3(cy0), f3(cx), f3(cy1))]
    # silkscreen: the two long sides of the body, 0.2 mm + half the line from the leg copper, ending 0.5 mm before the
    # mouth (the mouth stands at the board's top edge, rev H)
    sx = bw / 2 + 0.11
    for x in (-sx, sx):
        cuts = sorted((ly - lh / 2 - RING - 0.275, ly + lh / 2 + RING + 0.275) for (lx, ly, (_, lw, lh)) in legs_ if abs(x - lx) < lw / 2 + RING + 0.275)
        a = yr - 0.11
        for c0, c1 in cuts + [(ym - 0.5, ym - 0.5)]:
            if c0 - a > 0.3: L.append('  (fp_line (start %s %s) (end %s %s) (stroke (width 0.15) (type default)) (layer "F.SilkS"))' % (f3(x), f3(a), f3(x), f3(min(c0, ym - 0.5))))
            a = max(a, c1)
    for (x, sign) in ((-H['peg_x'], 1), (H['peg_x'], 1)):
        L.append('  (pad "" np_thru_hole circle (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask"))' % (f3(x), f3(yp), f3(H['peg_d']), f3(H['peg_d']), f3(H['peg_d'])))
    for n in pads:
        L.append('  (pad "%s" smd rect (at %s %s) (size %s %s) (layers "F.Cu" "F.Paste" "F.Mask"))' % (n, f3(H['pad_x'][n]), f3(pcy), f3(H['pad_w'].get(n, H['narrow'])), f3(plen)))
    for (x, y, (_, dw, dh)) in legs_:
        L.append('  (pad "S1" thru_hole oval (at %s %s) (size %s %s) (drill oval %s %s) (layers "*.Cu" "*.Mask"))' % (f3(x), f3(y), f3(dw + 2 * RING), f3(dh + 2 * RING), f3(dw), f3(dh)))
    L += ['  (model "${KICAD6_3DMODEL_DIR}/Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.wrl"',
          '    (offset (xyz 0 %s 0))' % f3(-(yp - ky)), '    (scale (xyz 1 1 1))', '    (rotate (xyz 0 0 0))', '  )', ')']
    fmt = lambda t: '%.3f / %.2f / %.2f / +-%.2f / +-%.2f / %.2f / %.2f' % t
    README['USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC'] = '''HRO TYPE-C-31-M-12 USB-C receptacle (LCSC C165948, JLCPCB Extended) as JLCPCB places it.

JLCPCB places the part with ITS library footprint (EasyEDA "%(title)s") at the CPL position, so the footprint origin
must be that footprint's origin, and the copper must be where the real part's pegs, shell legs and contacts land.
Three sources were compared (HRO's own drawing: the datasheet LCSC gives for C165948, drawn 2020-12-08, "RECOMMEND
P.C.B LAYOUT (COMPONENT SIDE)"; JLCPCB's EasyEDA footprint; KiCad 7's USB_C_Receptacle_HRO_TYPE-C-31-M-12). Distances
along the connector are measured from the line of the two peg holes, in mm:

| | signal pad row centre behind the pegs / rear legs behind / front legs ahead / outer pads x / A4-B9 pads x / peg holes apart / legs apart |
|---|---|
| HRO drawing | %(hro)s |
| JLCPCB (EasyEDA) | %(easyeda)s |
| KiCad 7 | %(kicad)s |

Decision: JLCPCB's library footprint matches HRO's drawing in every mechanical feature (peg holes, the four shell
legs, the pad pitch) to 0.01 mm; KiCad's footprint has its pad row 0.375 mm further from the pegs than HRO's land, the
outer pads 0.05 mm further out and the legs 0.03 mm off. The pegs and the legs fix where the part sits, so this
footprint is drawn from HRO's numbers and placed on the EasyEDA origin (the peg line at y = %(yp)s, as in the EasyEDA
footprint): peg holes 0.60 mm at x +-2.89, shell legs at x +-4.325 (rear legs 0.50 mm behind the pegs, slot 0.60 x
1.70; front legs 3.68 mm ahead, slot 0.60 x 1.40), signal pads 0.30 / 0.60 wide up to 1.64 mm behind the pegs.
Three departures from the drawing: HRO's pads start 0.50 mm behind the pegs, which leaves %(g_hro).2f mm between a
peg hole and the outer pads, exactly JLCPCB's NPTH-to-copper minimum (0.20); here they start %(front)s mm behind
(%(g_ours).2f mm to the holes, %(plen)s mm long); they still cover the contact tails, which end 1.47 mm behind the
pegs (HRO's top view); the shell-leg copper has a 0.20 mm ring (JLCPCB: PTH annular ring at least 0.20 mm; HRO draws
0.15); and the pad names are KiCad's (A1 and B12 on one spot, every leg "S1"), so the CPL check uses a name map for
this part. The EasyEDA signal pads lie %(off).3f mm further back than these (check_cpl.py allows 0.40 mm). Body (Fab): 8.94 x 7.35
mm, the mouth 6.28 mm ahead of the pegs; HRO puts the board edge 5.79 mm ahead of the pegs, i.e. the mouth 0.49 mm
past it. Courtyard: body, pads and leg copper plus 0.25 mm. Silkscreen: the two long sides only, ending 0.5 mm before
the mouth (the mouth stands at the board's top edge in rev H). The 3D model is KiCad's, moved with the origin.
tests/check_footprints_easyeda.py compares the footprint with JLCPCB's library footprint (holes and legs within
0.02 mm), tests/regen_footprints.py rebuilds it from the numbers above.
''' % dict(title=title, yp=f3(yp), hro=fmt(cmp_['hro']), easyeda=fmt(cmp_['easyeda']), kicad=fmt(cmp_['kicad']), g_hro=g_hro, g_ours=g_ours, front=f3(front),
           plen=f3(plen), off=abs(sig[0]['y'] - pcy))
    return '\n'.join(L)

# ------------------------------------------------------------------ 4. microSD TF-01A
def tf01a():
    title, lp, holes, body = easyeda('C91145')
    bx0, by0, bx1, by1 = body
    L = []
    L.append('(footprint "microSD_HRO_TF-01A" (version 20221018) (generator famicart)')
    L.append('  (layer "F.Cu")')
    L.append('  (descr "microSD socket, push-push with card detect, HRO TF-01A (LCSC C91145): pads, holes and body from JLCPCB\'s library footprint %s. '
             'Pins 1-8 card contacts (1 DAT2, 2 CD/DAT3, 3 CMD, 4 VDD, 5 CLK, 6 VSS, 7 DAT0, 8 DAT1), 9 card detect, 10-13 shell (GND). Card mouth at +y. '
             'See famicart.pretty/README.md.")' % title)
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
    README['microSD_HRO_TF-01A'] = '''HRO TF-01A push-push microSD socket with card detect (LCSC C91145, JLCPCB Extended).
Drawn from JLCPCB's library footprint (EasyEDA "%s"), so that its origin, pad numbers and pads are the ones JLCPCB
places with: 13 SMD pads (1-8 card contacts at 1.1 mm pitch, 9 card detect, 10-13 shell tabs) and two 1.0 mm
non-plated locating holes, all taken over to 0.001 mm; the Fab outline is the library's body outline (%.2f x %.2f mm),
the courtyard is body and pads plus 0.25 mm, the card mouth is the +y edge. Pin functions as in the EasyEDA symbol
(not checked against the HRO drawing). tests/check_footprints_easyeda.py compares it with the library footprint.
''' % (title, bx1 - bx0, by1 - by0)
    return '\n'.join(L)

# ------------------------------------------------------------------ 5. 2.2 uH SMNR4020
def smnr4020():
    title, lp, holes, body = easyeda('C135262')
    bx0, by0, bx1, by1 = body
    L = ['(footprint "L_SXN_SMNR4020" (version 20221018) (generator famicart)', '  (layer "F.Cu")',
         '  (descr "Shielded power inductor 4.0 x 4.0 mm, SXN SMNR4020 (2.2 uH: LCSC C135262): pads and body from JLCPCB\'s library footprint %s. '
         'See famicart.pretty/README.md.")' % title,
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
    README['L_SXN_SMNR4020'] = '''Shielded SMD power inductor 4.0 x 4.0 mm, SXN SMNR4020 series (2.2 uH: LCSC C135262, JLCPCB Extended).
Drawn from JLCPCB's library footprint (EasyEDA "%s"): two 1.5 x 4.0 mm pads 3.6 mm apart (centres), origin in the
middle, body outline 4.0 x 4.0 mm on the Fab layer, courtyard pads and body plus 0.25 mm. No polarity.
tests/check_footprints_easyeda.py compares it with the library footprint.
''' % title
    return '\n'.join(L)

def readme():
    out = ['# famicart.pretty: notes on the rev H footprints', '',
           'The footprints below are generated by `tools/pcb/tests/regen_footprints.py`, which also writes this file; run it',
           'with `--cache DIR` (the JLCPCB / EasyEDA library data) to check that the committed files are what their sources give.',
           'The explanations are kept here and not as comment lines in the .kicad_mod files, because KiCad\'s footprint editor and',
           '`kicad-cli fp upgrade` drop such lines when they save a footprint.', '']
    for name in NAMES:
        out += ['## ' + name, '', README[name].rstrip('\n'), '']
    return '\n'.join(out)

def generate():
    """{file name in famicart.pretty: file text}"""
    fns = (card_edge_m, qfn_novia, usb_c, tf01a, smnr4020)
    out = {name + '.kicad_mod': fn().rstrip('\n') + '\n' for name, fn in zip(NAMES, fns)}
    out['README.md'] = readme()
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--cache', required=True); ap.add_argument('--write', action='store_true')
    ap.add_argument('--kicad', default='/usr/share/kicad/footprints'); a = ap.parse_args()
    DL, SYS = os.path.abspath(a.cache), a.kicad
    bad = 0
    for name, txt in generate().items():
        p = os.path.join(PRETTY, name)
        if a.write:
            open(p, 'w').write(txt); print('written', p)
        else:
            same = os.path.exists(p) and open(p).read() == txt
            print('%-58s %s' % (name, 'identical to the regenerated file' if same else 'DIFFERS from the regenerated file'))
            bad += not same
    sys.exit(1 if bad else 0)
