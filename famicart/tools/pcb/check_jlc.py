#!/usr/bin/env python3
"""Check a finished board against JLCPCB's published limits (run after route_pcb.py; with the package: after gen_jlc.py).

The limits are the ones quoted in docs/12_rev_g_plan.md ("JLCPCB で作るための条件") from JLCPCB's capability pages
(2026-11-10): 2-layer FR-4, 1 oz.
  tracks            width >= 0.10 mm (the design rule itself is 0.15 mm; KiCad DRC checks the clearances)
  vias              hole >= 0.30 mm (smaller holes cost extra), diameter >= hole + 0.10 mm, hole to hole >= 0.20 mm
  copper to edge    >= 0.20 mm to a routed edge, >= 0.40 mm to the left / right edges (edge rails, V-cut)
  slots             non-plated slot / notch width >= 1.0 mm, inner corners drawn with a radius
  silkscreen        line >= 0.15 mm, text height >= 1.0 mm
  gold fingers      finger copper ends >= 0.6 mm before the tab edge, board >= 50 x 50 mm
  Standard PCBA     board >= 70 x 70 mm, all assembled parts on the top side, every part number a Basic part
  paste             only on pads of parts that JLCPCB places
  gerbers.zip       fabrication layers and drill files only
Exit status 1 when anything fails.   FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg python3 check_jlc.py"""
import os, sys, math, csv, zipfile, importlib
import pcbnew
from pcbnew import ToMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
HW = os.path.abspath(os.environ['FC_HW_DIR'])
SH = getattr(D, 'SHELL', None)

MIN_TRACK, MIN_DRILL, MIN_RING2, HOLE_HOLE = 0.10, 0.30, 0.10, 0.20
EDGE_ROUTED, EDGE_VCUT, MIN_SLOT = 0.20, 0.40, 1.0
SILK_LINE, SILK_TEXT = 0.15, 1.0
FINGER_TO_EDGE = 0.6
TOL = 0.002

def main():
    bad, info = [], []
    def need(cond, msg):
        if not cond: bad.append(msg)
    b = pcbnew.LoadBoard(os.path.join(HW, 'famicart.kicad_pcb'))
    ds = b.GetDesignSettings()
    need(b.GetCopperLayerCount() == 2, 'copper layers: %d (2 expected)' % b.GetCopperLayerCount())
    need(abs(ToMM(ds.GetBoardThickness()) - 1.2) < 1e-6, 'board thickness %.2f mm (1.2 expected)' % ToMM(ds.GetBoardThickness()))
    bb = b.GetBoardEdgesBoundingBox(); bw, bh = ToMM(bb.GetWidth()) - 0.1, ToMM(bb.GetHeight()) - 0.1      # minus the 0.1 mm outline pen
    info.append('board %.1f x %.1f mm' % (bw, bh))
    need(bw >= 70 and bh >= 70, 'Standard PCBA needs a board of at least 70 x 70 mm (%.1f x %.1f)' % (bw, bh))

    # ---- tracks and vias
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']; vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    if tracks:
        wmin = min(ToMM(t.GetWidth()) for t in tracks); info.append('%d track segments, narrowest %.3f mm' % (len(tracks), wmin))
        need(wmin >= MIN_TRACK - TOL, 'track width %.3f mm < %.2f' % (wmin, MIN_TRACK))
    else: info.append('no tracks (board not routed)')
    if vias:
        dmin = min(ToMM(v.GetDrillValue()) for v in vias); rmin = min(ToMM(v.GetWidth(pcbnew.F_Cu) if hasattr(v, 'GetFrontWidth') else v.GetWidth()) - ToMM(v.GetDrillValue()) for v in vias)
        info.append('%d vias, smallest hole %.2f mm, smallest (diameter - hole) %.2f mm' % (len(vias), dmin, rmin))
        need(dmin >= MIN_DRILL - TOL, 'via hole %.2f mm < %.2f (extra charge below 0.3 mm)' % (dmin, MIN_DRILL))
        need(rmin >= MIN_RING2 - TOL, 'via diameter - hole = %.2f mm < %.2f' % (rmin, MIN_RING2))
        pts = sorted((ToMM(v.GetPosition().x), ToMM(v.GetPosition().y), ToMM(v.GetDrillValue())) for v in vias)
        worst = 9.0
        for i, (x, y, d) in enumerate(pts):
            for (x2, y2, d2) in pts[i + 1:]:
                if x2 - x > 2.0: break
                g = math.hypot(x2 - x, y2 - y) - (d + d2) / 2
                if g < worst: worst = g
        info.append('closest via holes: %.2f mm apart (wall to wall)' % worst)
        need(worst >= HOLE_HOLE - TOL, 'via holes %.2f mm apart < %.2f' % (worst, HOLE_HOLE))

    # ---- copper against the left / right edges (edge rails by V-cut) and the top edge
    lo, hi = (SH.get('edge_x') or (0.0, 90.0)) if SH else (0.0, 90.0)
    vcut = bool(SH and SH.get('fillets'))
    side = EDGE_VCUT if vcut else EDGE_ROUTED
    xs = []
    for t in tracks:
        w = ToMM(t.GetWidth()) / 2
        for p in (t.GetStart(), t.GetEnd()): xs += [ToMM(p.x) - w, ToMM(p.x) + w]
    for v in vias:
        r = ToMM(v.GetWidth()) / 2 if not hasattr(v, 'GetFrontWidth') else ToMM(v.GetWidth(pcbnew.F_Cu)) / 2
        xs += [ToMM(v.GetPosition().x) - r, ToMM(v.GetPosition().x) + r]
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            pb = pad.GetBoundingBox(); xs += [ToMM(pb.GetX()), ToMM(pb.GetRight())]
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(layer): continue
            poly = z.GetFilledPolysList(layer)
            for i in range(poly.OutlineCount()):
                o = poly.Outline(i)
                for k in range(o.PointCount()): xs.append(ToMM(o.CPoint(k).x))
    if xs:
        info.append('copper x range %.2f .. %.2f mm (side edges at %.2f / %.2f)' % (min(xs), max(xs), lo, hi))
        need(min(xs) >= lo + side - TOL, 'copper %.2f mm from the left edge < %.2f' % (min(xs) - lo, side))
        need(max(xs) <= hi - side + TOL, 'copper %.2f mm from the right edge < %.2f' % (hi - max(xs), side))

    # ---- outline: inner corners drawn with a radius, slot / notch width
    arcs = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_ARC]
    if SH and SH.get('fillets') is not None:
        need(len(arcs) == len(SH['fillets']), 'outline has %d corner arcs, %d expected' % (len(arcs), len(SH['fillets'])))
        if arcs:
            rr = [ToMM(a.GetRadius()) for a in arcs]; info.append('%d inner corners drawn with R %.2f..%.2f mm' % (len(arcs), min(rr), max(rr)))
            need(min(rr) >= 0.5 - TOL, 'corner radius %.2f mm < 0.5 (a 1.0 mm router bit cannot cut it)' % min(rr))
        for cut in SH['cutouts']:
            w = min(max(p[0] for p in cut) - min(p[0] for p in cut), max(p[1] for p in cut) - min(p[1] for p in cut))
            need(w >= MIN_SLOT - TOL, 'cut-out %.2f mm wide < %.1f' % (w, MIN_SLOT))

    # ---- silkscreen minimums
    lmin, tmin = 9.0, 9.0
    items = list(b.GetDrawings()) + [g for fp in b.GetFootprints() for g in fp.GraphicalItems()] + [fp.Reference() for fp in b.GetFootprints()] + [fp.Value() for fp in b.GetFootprints()]
    for g in items:
        if g.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS): continue
        if 'TEXT' in g.GetClass():
            if not g.IsVisible(): continue
            tmin = min(tmin, ToMM(g.GetTextSize().y)); lmin = min(lmin, ToMM(g.GetTextThickness()))
        else: lmin = min(lmin, ToMM(g.GetWidth()))
    info.append('silkscreen: thinnest line %.3f mm, smallest text %.2f mm' % (lmin, tmin))
    need(lmin >= SILK_LINE - TOL, 'silkscreen line %.3f mm < %.2f' % (lmin, SILK_LINE))
    need(tmin >= SILK_TEXT - TOL, 'silkscreen text %.2f mm < %.1f' % (tmin, SILK_TEXT))

    # ---- assembly: placed parts on the top side only, paste only where JLCPCB places a part
    lcsc = getattr(D, 'LCSC', {})
    placed = {ref for ref, (lib, sym, val, fp, _) in D.PARTS.items() if val.split(' (')[0] in lcsc}
    for fp in b.GetFootprints():
        ref = fp.GetReference(); has_paste = any(p.GetLayerSet().Contains(pcbnew.F_Paste) or p.GetLayerSet().Contains(pcbnew.B_Paste) for p in fp.Pads())
        if ref in placed: need(not fp.IsFlipped(), '%s is assembled by JLCPCB but sits on the back' % ref)
        elif has_paste and getattr(D, 'JLC_RULES', False): bad.append('%s is hand-soldered but has solder paste' % ref)
    info.append('%d parts for JLCPCB (%d types), all on the top side; %d footprints without paste' % (len(placed), len({D.PARTS[r][2].split(' (')[0] for r in placed}), len(D.PARTS) - len(placed)))

    # ---- gold fingers: copper must end before the bevel
    j1 = b.FindFootprintByReference('J1')
    if j1:
        bottom = ToMM(bb.GetBottom()) - 0.05
        gap = min(bottom - ToMM(p.GetBoundingBox().GetBottom()) for p in j1.Pads())
        info.append('finger copper ends %.2f mm before the tab edge' % gap)
        need(gap >= FINGER_TO_EDGE - TOL, 'finger copper %.2f mm from the tab edge < %.1f (bevel)' % (gap, FINGER_TO_EDGE))
        need(bw >= 50 and bh >= 50, 'gold-finger boards must be at least 50 x 50 mm')

    # ---- order package (present only after gen_jlc.py)
    z = os.path.join(HW, 'jlcpcb', 'gerbers.zip')
    if os.path.exists(z):
        names = zipfile.ZipFile(z).namelist()
        extra = [n for n in names if 'Fab' in n or n.endswith('.gbrjob')]
        if getattr(D, 'JLC_RULES', False): need(not extra, 'gerbers.zip carries non-fabrication files: %s' % extra)
        for k in ('F_Cu.gtl', 'B_Cu.gbl', 'F_Mask.gts', 'B_Mask.gbs', 'Edge_Cuts.gm1', 'PTH.drl'):
            need(any(n.endswith(k) for n in names), 'gerbers.zip lacks %s' % k)
        info.append('gerbers.zip: %d files' % len(names))
        cpl = list(csv.DictReader(open(os.path.join(HW, 'jlcpcb', 'cpl_jlc.csv'))))
        need({r['Designator'] for r in cpl} == placed, 'CPL designators differ from the parts JLCPCB places: %s' % sorted({r['Designator'] for r in cpl} ^ placed)[:8])
        need(all(r['Layer'] == 'Top' for r in cpl), 'CPL has bottom-side placements')
        pc = os.path.join(HW, 'jlcpcb', 'parts_check.csv')
        if os.path.exists(pc):
            rows = list(csv.DictReader(open(pc)))
            need(all(r['Library'] == 'Basic' and r['Result'] == 'OK' for r in rows), 'parts_check.csv: not every part is a Basic part in stock')
            info.append('parts_check.csv: %d part numbers, all Basic' % len(rows))
    else: info.append('no jlcpcb/gerbers.zip yet (run gen_jlc.py)')

    print('JLCPCB check:', 'OK' if not bad else '%d problems' % len(bad))
    for x in info: print('   ', x)
    for x in bad: print('  FAIL', x)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
