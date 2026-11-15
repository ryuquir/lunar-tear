#!/usr/bin/env python3
"""Add break-off edge rails to the routed board (D.RAILS): writes <hw>/famicart_rails.kicad_pcb, Gerber and drill
files in <hw>/fab_rails/, the DRC report drc_report_rails.txt and jlcpcb/gerbers_rails.zip.

Why: JLCPCB's Standard PCBA needs two edge rails of at least 5 mm with fiducials. Rails that JLCPCB adds itself go on
the longer sides by default, which on this board are the top edge and the gold-finger edge; fingers that are not on the
outer edge cannot be bevelled. Here the rails are part of the data: on the left and right edges, 2 mm away from the
board, each held by three tabs with a row of 0.6 mm holes that touch the board's edge line from outside (snap off, file
the ridge of at most 0.3 mm down to the edge).
Everything is routed, there is no V-cut, and the gold-finger edge stays a free edge: the rails stop above its line.
Three fiducials (1 mm copper, 2 mm mask opening, centred 3.85 mm from the panel edges) and four 2 mm tooling holes sit on
the rails, as JLCPCB's capabilities page asks for SMT assembly of mouse-bite panels.

The cartridge board inside the rails is the routed board unchanged: same coordinates, so BOM and CPL are shared; the
rounded inner corners inside the board must come out as the board's own (SHELL['fillets']), and the archive is written
only when the design rule check of the railed board has no error (check_jlc.py compares the two boards object by object).
Options (rev H on; a design without them gets exactly the panel it always got):
  RAILS['top'] = dict(tabs=(x, ...), width=RAILS['width'], gap=RAILS['gap'])   a third rail above the top edge, joined
      to the left and right rails into one frame and held by break-off tabs like the side rails (mouse bites: the
      holes touch the board's top edge from outside). The finger edge at the bottom stays free, so the frame is open
      there. No V-cut: a V-cut line runs straight across the whole panel, and every rail here is held by tabs.
      Tabs must keep clear of the parts that cross the top edge (D.EDGE_CONNECTORS: USB-C, microSD), whose mouths
      reach into the gap. Fiducials and tooling holes may sit on it: ('T', d), d mm from the panel's left end
      (d < 0: from its right end).
  D.ASSEMBLY == 'both' (parts on both sides): every fiducial is placed on both sides (JLCPCB needs fiducials on each
      side it assembles).
  Boards with inner copper layers: the inner layers are plotted and archived too (In1.Cu ... In4.Cu).
    FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg python3 make_rails.py"""
import os, sys, re, shutil, subprocess, zipfile, importlib
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
import gen_pcb, gen_jlc
HW = os.path.abspath(os.environ['FC_HW_DIR'])
SRC = os.path.join(HW, 'famicart.kicad_pcb'); DST = os.path.join(HW, 'famicart_rails.kicad_pcb')
RA = D.RAILS; SH = D.SHELL
W, H, T = gen_pcb.BOARD_W, gen_pcb.BODY_H, gen_pcb.TOTAL_H
X0, X1, CH = gen_pcb.TAB_X0, gen_pcb.TAB_X0 + gen_pcb.TAB_W, gen_pcb.CHAMFER
LO, HI = SH['edge_x']
R = SH['fillet_r']
PM = pcbnew.SHAPE_POLY_SET.PM_FAST

def poly(pts):
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    for x, y in pts: ps.Append(FromMM(x), FromMM(y))
    return ps

def rect(x0, y0, x1, y1): return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

def fab_layers(ncu):
    """--layers argument of the Gerber plot: every copper layer of an ncu-layer board (F.Cu, In1.Cu .. In(ncu-2).Cu,
    B.Cu), paste, silkscreen, mask, outline. 2 layers: the list used up to rev G."""
    cu = ['F.Cu'] + ['In%d.Cu' % i for i in range(1, ncu - 1)] + ['B.Cu']
    return ','.join(cu + ['F.Paste', 'B.Paste', 'F.SilkS', 'B.SilkS', 'F.Mask', 'B.Mask', 'Edge.Cuts'])

def top_tabs_clear(tabs, tab_w, parts, clear):
    """[(tab x, part reference)] for every top tab that comes within `clear` of the x range of a part that crosses the
    top edge (parts = [(reference, x0, x1)])."""
    return [(xc, ref) for xc in tabs for (ref, x0, x1) in parts if xc - tab_w / 2 - clear < x1 and xc + tab_w / 2 + clear > x0]

def edge_x_range(board, ref):
    """(x0, x1, y0) of the courtyard of part `ref` on the board (its pads when it has no courtyard), in mm."""
    fp = board.FindFootprintByReference(ref)
    if fp is None: raise SystemExit('EDGE_CONNECTORS: %s is not on the board' % ref)
    cy = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    bbs = [g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer() == cy] or [p.GetBoundingBox() for p in fp.Pads()]
    return (min(ToMM(b.GetX()) for b in bbs), max(ToMM(b.GetRight()) for b in bbs), min(ToMM(b.GetY()) for b in bbs))

def chain(lc):
    """Vertices of a closed line chain in mm, collinear points removed."""
    pts = [(ToMM(lc.CPoint(i).x), ToMM(lc.CPoint(i).y)) for i in range(lc.PointCount())]
    out = []
    n = len(pts)
    for i, v in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        if abs((v[0] - a[0]) * (b[1] - v[1]) - (v[1] - a[1]) * (b[0] - v[0])) > 1e-9: out.append((round(v[0], 3), round(v[1], 3)))
    return out

def area2(pts): return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))

def inner_corners(pts, hole):
    """The right-angle vertices where the cutter runs into a corner of the material: reflex vertices of an outer
    contour, convex vertices of a cut-out."""
    s = 1.0 if area2(pts) > 0 else -1.0; n = len(pts); out = []
    for i, v in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        cr = (v[0] - a[0]) * (b[1] - v[1]) - (v[1] - a[1]) * (b[0] - v[0])
        dot = (v[0] - a[0]) * (b[0] - v[0]) + (v[1] - a[1]) * (b[1] - v[1])
        if abs(dot) > 1e-9: continue                          # not a right angle (the 45 degree chamfers of the tab)
        if (cr * s > 0) == hole: out.append(v)
    return out

def main():
    board = pcbnew.LoadBoard(SRC)
    # ---- panel = board + rails + tabs, minus the board's own slot
    body = SH['outline_body']
    bpts = [(X1, H), (X1, T - CH), (X1 - CH, T), (X0 + CH, T), (X0, T - CH), (X0, H)] + [tuple(p) for p in body[1:-1]]
    panel = poly(bpts)
    gap, rw = RA['gap'], RA['width']
    rails = {'L': (LO - gap - rw, LO - gap), 'R': (HI + gap, HI + gap + rw)}
    YE = T - RA.get('end_gap', 0.0)                           # the rails stop short of the gold-finger edge line
    ypos = lambda y: y if y >= 0 else YE + y                  # negative: measured from the rail's lower end
    top = RA.get('top')
    if top:
        if top.get('vcut'): raise SystemExit('RAILS["top"]: no V-cut (a V-cut runs across the whole panel); the top rail is held by tabs')
        tgap, tw = top.get('gap', gap), top.get('width', rw)
        YT = -tgap - tw                                        # outer (upper) edge of the top rail = top edge of the panel
        PX0, PX1 = rails['L'][0], rails['R'][1]                # panel left / right end
        xpos = lambda d: PX0 + d if d >= 0 else PX1 + d       # along the top rail: from the panel's left end (< 0: right end)
        crossing = [(ref,) + edge_x_range(board, ref) for ref in getattr(D, 'EDGE_CONNECTORS', ())]
        crossing = [c[:3] for c in crossing if c[3] < 0.0]     # (ref, x0, x1) of the parts that reach past the top edge
        hit = top_tabs_clear(top['tabs'], RA['tab'], crossing, R + 0.5)
        if hit: raise SystemExit('RAILS["top"]: tabs in front of a part that reaches past the top edge: %s' % ', '.join('x %.1f (%s)' % h for h in hit))
    elif any(side == 'T' for side, _ in list(RA['fiducials']) + list(RA.get('tooling', ()))):
        raise SystemExit('RAILS: fiducials or tooling holes on the top rail (\'T\') but no RAILS["top"]')
    for side, (xa, xb) in rails.items():
        panel.BooleanAdd(rect(xa, YT if top else 0.0, xb, YE), PM)     # with a top rail: up to its upper edge (one frame)
        for yc in RA['tabs'][side]:
            ta, tb = (LO - gap - 0.5, LO + 0.5) if side == 'L' else (HI - 0.5, HI + gap + 0.5)       # overlaps rail and board
            panel.BooleanAdd(rect(ta, yc - RA['tab'] / 2, tb, yc + RA['tab'] / 2), PM)
    if top:
        rails['T'] = (YT, -tgap)                               # (y range: the top rail runs from PX0 to PX1)
        panel.BooleanAdd(rect(PX0, YT, PX1, -tgap), PM)
        for xc in top['tabs']:
            panel.BooleanAdd(rect(xc - RA['tab'] / 2, -tgap - 0.5, xc + RA['tab'] / 2, 0.5), PM)     # overlaps rail and board
    for cut in SH['cutouts']: panel.BooleanSubtract(poly(cut), PM)
    panel.Simplify(PM)
    assert panel.OutlineCount() == 1, 'board, rails and tabs must form one piece'
    contours = [(chain(panel.Outline(0)), False)] + [(chain(panel.Hole(0, k)), True) for k in range(panel.HoleCount(0))]
    # ---- break-off holes on the board's edge line
    k = 0
    for side, x in (('L', LO - RA['hole_out']), ('R', HI + RA['hole_out'])):       # hole centres just outside the board
        for yc in RA['tabs'][side]:
            for i in range(RA['holes']):
                y = yc + (i - (RA['holes'] - 1) / 2) * RA['pitch']; k += 1
                fp = pcbnew.FOOTPRINT(board); fp.SetReference('MB%d' % k); fp.SetValue('break-off hole'); fp.SetPosition(gen_pcb.mm(x, y))
                fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
                fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
                pad = pcbnew.PAD(fp); pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
                d = FromMM(RA['hole']); pad.SetSize(VECTOR2I(d, d)); pad.SetDrillSize(VECTOR2I(d, d)); pad.SetPosition(gen_pcb.mm(x, y))
                pad.SetLayerSet(pcbnew.LSET.AllCuMask()); pad.SetNumber('')
                fp.Add(pad); board.Add(fp)
    for xc in (top['tabs'] if top else ()):                    # top tabs: hole centres just above the board's top edge
        y = -RA['hole_out']
        for i in range(RA['holes']):
            x = xc + (i - (RA['holes'] - 1) / 2) * RA['pitch']; k += 1
            fp = pcbnew.FOOTPRINT(board); fp.SetReference('MB%d' % k); fp.SetValue('break-off hole'); fp.SetPosition(gen_pcb.mm(x, y))
            fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
            fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
            pad = pcbnew.PAD(fp); pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            d = FromMM(RA['hole']); pad.SetSize(VECTOR2I(d, d)); pad.SetDrillSize(VECTOR2I(d, d)); pad.SetPosition(gen_pcb.mm(x, y))
            pad.SetLayerSet(pcbnew.LSET.AllCuMask()); pad.SetNumber('')
            fp.Add(pad); board.Add(fp)
    # ---- tooling holes on the rail centre lines
    for i, (side, y) in enumerate(RA.get('tooling', ())):
        if side == 'T': x, y = xpos(y), (rails['T'][0] + rails['T'][1]) / 2
        else: xa, xb = rails[side]; x, y = (xa + xb) / 2, ypos(y)
        fp = pcbnew.FOOTPRINT(board); fp.SetReference('TH%d' % (i + 1)); fp.SetValue('tooling hole'); fp.SetPosition(gen_pcb.mm(x, y))
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
        pad = pcbnew.PAD(fp); pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        d = FromMM(RA['tooling_d']); pad.SetSize(VECTOR2I(d, d)); pad.SetDrillSize(VECTOR2I(d, d)); pad.SetPosition(gen_pcb.mm(x, y))
        pad.SetLayerSet(pcbnew.LSET.AllCuMask()); pad.SetNumber('')
        fp.Add(pad); board.Add(fp)
    # ---- fiducials on the rails (top side: the side JLCPCB assembles; with ASSEMBLY 'both' also the bottom side)
    def fid_xy(side, y):
        if side == 'T': return xpos(y), rails['T'][0] + RA['fid_inset']
        xa, xb = rails[side]; return (xa + RA['fid_inset'] if side == 'L' else xb - RA['fid_inset']), ypos(y)
    fids = [(side, y, False) for side, y in RA['fiducials']]
    if getattr(D, 'ASSEMBLY', 'top') == 'both': fids += [(side, y, True) for side, y in RA['fiducials']]
    for i, (side, y, back) in enumerate(fids):
        x, y = fid_xy(side, y)
        fp = pcbnew.FootprintLoad(os.path.join(gen_pcb.SYS_FP, 'Fiducial.pretty'), 'Fiducial_1mm_Mask2mm')
        fp.SetReference('FID%d' % (i + 1)); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetAttributes(pcbnew.FP_SMD | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS): fp.Remove(g)
        board.Add(fp); fp.SetPosition(gen_pcb.mm(x, y))
        if back: fp.Flip(fp.GetPosition(), False)          # the same fiducial on the bottom side
    for side in 'LR': gen_pcb.add_text(board, 'EDGE RAIL - BREAK OFF', rails[side][0] + (1.2 if side == 'L' else 3.8), T / 2, pcbnew.F_SilkS, 1.0, 0.15)
    for d in board.GetDrawings():
        if d.GetClass() == 'PCB_TEXT' and d.GetText().startswith('EDGE RAIL'): d.SetTextAngleDegrees(90)
    if top: gen_pcb.add_text(board, 'EDGE RAIL - BREAK OFF', W / 2, (rails['T'][0] + rails['T'][1]) / 2, pcbnew.F_SilkS, 1.0, 0.15)
    # ---- replace the outline drawing (last: after board.Remove() pcbnew hands out untyped objects for new footprints)
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts: board.Remove(d)
    nfil = 0; inboard = set()
    for pts, hole in contours:
        fil = inner_corners(pts, hole); nfil += len(fil)
        inboard |= {v for v in fil if LO + 0.001 < v[0] < HI - 0.001 and v[1] > 0.001}      # (y <= 0: where a top tab meets the board)
        gen_pcb.add_outline(board, pts, fil, R)
    # the rounded corners inside the board must be exactly the ones the board itself is drawn with (SHELL['fillets']):
    # the cartridge board in the panel has to be the same board, corner for corner
    want = {(round(x, 3), round(y, 3)) for x, y in SH['fillets']}
    assert inboard == want, 'rounded corners inside the board differ from SHELL fillets: %s' % sorted(inboard ^ want)
    pcbnew.SaveBoard(DST, board)
    board = pcbnew.LoadBoard(DST); board.BuildConnectivity()
    # ---- checks
    rep = os.path.join(HW, 'drc_report_rails.txt')
    pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rep).read(); errors = txt.count('Severity: error'); kinds = {}
    for kk in re.findall(r'^\[(\w+)\]', txt, re.M): kinds[kk] = kinds.get(kk, 0) + 1
    bb = board.GetBoardEdgesBoundingBox(); pw, ph = ToMM(bb.GetWidth()) - 0.1, ToMM(bb.GetHeight()) - 0.1
    print('panel %.1f x %.1f mm; contours %d (1 outer, %d cut-outs), %d rounded inner corners, %d break-off holes, %d tooling holes, %d fiducials'
          % (pw, ph, len(contours), len(contours) - 1, nfil, k, len(RA.get('tooling', ())), len(RA['fiducials'])))
    if top or len(fids) != len(RA['fiducials']) or board.GetCopperLayerCount() != 2:
        print('top rail: %s; fiducials on %s; copper layers plotted: %d'
              % ('%d tabs at x %s' % (len(top['tabs']), ', '.join('%.1f' % x for x in top['tabs'])) if top else 'none',
                 'both sides (%d)' % len(fids) if len(fids) != len(RA['fiducials']) else 'the top side', board.GetCopperLayerCount()))
    print('DRC of the railed board: errors', errors, kinds)
    z = os.path.join(HW, 'jlcpcb', 'gerbers_rails.zip'); os.makedirs(os.path.dirname(z), exist_ok=True)
    if os.path.exists(z): os.remove(z)
    if errors: raise SystemExit('the railed board has design rule errors: no archive written')
    # ---- fabrication files
    fab = os.path.join(HW, 'fab_rails'); shutil.rmtree(fab, ignore_errors=True); os.makedirs(fab)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', fab_layers(board.GetCopperLayerCount()), '-o', fab + '/', DST], check=True, capture_output=True)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '-o', fab + '/', DST], check=True, capture_output=True)
    names = sorted(n for n in os.listdir(fab) if n.endswith(gen_jlc.FAB_SUFFIX))
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for n in names: zf.write(os.path.join(fab, n), n)
    print('written', z, ':', ', '.join(names))

if __name__ == '__main__':
    main()
