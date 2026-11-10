#!/usr/bin/env python3
"""Add break-off edge rails to the routed board (D.RAILS): writes <hw>/famicart_rails.kicad_pcb, Gerber and drill
files in <hw>/fab_rails/, the DRC report drc_report_rails.txt and jlcpcb/gerbers_rails.zip.

Why: JLCPCB's Standard PCBA needs two edge rails of at least 5 mm with fiducials. Rails that JLCPCB adds itself go on
the longer sides by default, which on this board are the top edge and the gold-finger edge; fingers that are not on the
outer edge cannot be bevelled. Here the rails are part of the data: on the left and right edges, 2 mm away from the
board, each held by three tabs with a row of 0.6 mm holes that touch the board's edge line from outside (snap off, file
the ridge of at most 0.3 mm down to the edge).
Everything is routed, there is no V-cut, and the gold-finger edge stays a free edge. Three fiducials (1 mm copper,
2 mm mask opening) sit on the rails, 3.5 mm from the outer edge (JLCPCB asks for 3.35 mm).

The cartridge board inside the rails is the routed board unchanged: same coordinates, so BOM and CPL are shared.
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

def chain(lc):
    """Vertices of a closed line chain in mm, collinear points removed."""
    pts = [(ToMM(lc.CPoint(i).x), ToMM(lc.CPoint(i).y)) for i in range(lc.PointCount())]
    out = []
    n = len(pts)
    for i, v in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        if abs((v[0] - a[0]) * (b[1] - v[1]) - (v[1] - a[1]) * (b[0] - v[0])) > 1e-9: out.append((round(v[0], 6), round(v[1], 6)))
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
    for side, (xa, xb) in rails.items():
        panel.BooleanAdd(rect(xa, 0.0, xb, T), PM)
        for yc in RA['tabs'][side]:
            ta, tb = (LO - gap - 0.5, LO + 0.5) if side == 'L' else (HI - 0.5, HI + gap + 0.5)       # overlaps rail and board
            panel.BooleanAdd(rect(ta, yc - RA['tab'] / 2, tb, yc + RA['tab'] / 2), PM)
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
    # ---- fiducials on the rails (top side: the side JLCPCB assembles)
    for i, (side, y) in enumerate(RA['fiducials']):
        xa, xb = rails[side]; x = xa + RA['fid_inset'] if side == 'L' else xb - RA['fid_inset']
        fp = pcbnew.FootprintLoad(os.path.join(gen_pcb.SYS_FP, 'Fiducial.pretty'), 'Fiducial_1mm_Mask2mm')
        fp.SetReference('FID%d' % (i + 1)); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetAttributes(pcbnew.FP_SMD | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS): fp.Remove(g)
        board.Add(fp); fp.SetPosition(gen_pcb.mm(x, y))
    for side in 'LR': gen_pcb.add_text(board, 'EDGE RAIL - BREAK OFF', rails[side][0] + (1.4 if side == 'L' else 3.6), T / 2, pcbnew.F_SilkS, 1.0, 0.15)
    for d in board.GetDrawings():
        if d.GetClass() == 'PCB_TEXT' and d.GetText().startswith('EDGE RAIL'): d.SetTextAngleDegrees(90)
    # ---- replace the outline drawing (last: after board.Remove() pcbnew hands out untyped objects for new footprints)
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts: board.Remove(d)
    nfil = 0
    for pts, hole in contours:
        fil = inner_corners(pts, hole); nfil += len(fil)
        gen_pcb.add_outline(board, pts, fil, R)
    pcbnew.SaveBoard(DST, board)
    board = pcbnew.LoadBoard(DST); board.BuildConnectivity()
    # ---- checks
    rep = os.path.join(HW, 'drc_report_rails.txt')
    pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rep).read(); errors = txt.count('Severity: error'); kinds = {}
    for kk in re.findall(r'^\[(\w+)\]', txt, re.M): kinds[kk] = kinds.get(kk, 0) + 1
    bb = board.GetBoardEdgesBoundingBox(); pw, ph = ToMM(bb.GetWidth()) - 0.1, ToMM(bb.GetHeight()) - 0.1
    print('panel %.1f x %.1f mm; contours %d (1 outer, %d cut-outs), %d rounded inner corners, %d break-off holes, %d fiducials'
          % (pw, ph, len(contours), len(contours) - 1, nfil, k, len(RA['fiducials'])))
    print('DRC of the railed board: errors', errors, kinds)
    # ---- fabrication files
    fab = os.path.join(HW, 'fab_rails'); shutil.rmtree(fab, ignore_errors=True); os.makedirs(fab)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts', '-o', fab + '/', DST], check=True, capture_output=True)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '-o', fab + '/', DST], check=True, capture_output=True)
    names = sorted(n for n in os.listdir(fab) if n.endswith(gen_jlc.FAB_SUFFIX))
    z = os.path.join(HW, 'jlcpcb', 'gerbers_rails.zip'); os.makedirs(os.path.dirname(z), exist_ok=True)
    if os.path.exists(z): os.remove(z)
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for n in names: zf.write(os.path.join(fab, n), n)
    print('written', z, ':', ', '.join(names))
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
