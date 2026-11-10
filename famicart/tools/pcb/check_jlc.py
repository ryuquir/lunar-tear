#!/usr/bin/env python3
"""Check a finished board against JLCPCB's published limits (run after route_pcb.py; with the package: after gen_jlc.py).

The limits are the ones quoted in docs/12_rev_g_plan.md ("JLCPCB で作るための条件") from JLCPCB's capability pages
(2026-11-10): 2-layer FR-4, 1 oz.
  tracks            width >= 0.10 mm (the design rule itself is 0.15 mm; KiCad DRC checks the clearances)
  vias              hole >= 0.30 mm (smaller holes cost extra), diameter >= hole + 0.10 mm, hole to hole >= 0.20 mm
  copper to edge    >= 0.40 mm to the left / right edges (edge rails; a V-cut edge needs 0.4 mm) is measured here;
                    >= 0.20 mm to every other routed edge and >= 0.2 mm between a via hole and a foreign track are
                    design rules of the board (0.3 mm and 0.2 mm) that KiCad's DRC checks: this tool fails when
                    the DRC report next to the board lists an error or an unconnected pad
  slots             non-plated slot / notch width >= 1.0 mm, inner corners drawn with a radius
  silkscreen        line >= 0.15 mm, text height >= 1.0 mm
  gold fingers      finger copper ends >= 1.15 mm before the tab edge (JLCPCB's copper cutback for a 30 degree bevel on
                    boards up to 1.6 mm), board >= 50 x 50 mm, solder mask fully opened
                    over the finger area, no silkscreen and no plated hole within 1.0 mm of a finger
  Standard PCBA     board >= 70 x 70 mm, all assembled parts on the top side, every part number a Basic part
  paste             only on pads of parts that JLCPCB places
  gerbers.zip       fabrication layers and drill files only; the drill file has as many holes as the board has vias
  routed            a board without tracks, with open connections or with DRC errors is refused
  edge rails        (designs with RAILS) gerbers_rails.zip exists and the railed board passed its DRC
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
FINGER_TO_EDGE, FINGER_HOLE = 1.15, 1.0
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
    else: bad.append('the board has no tracks: it is not routed')
    b.BuildConnectivity(); nopen = b.GetConnectivity().GetUnconnectedCount(False)
    need(nopen == 0, '%d connections of the board are open' % nopen)
    rep = os.path.join(HW, 'drc_report.txt')
    if os.path.exists(rep):
        txt = open(rep).read(); nerr = txt.count('Severity: error')
        need(nerr == 0, 'drc_report.txt lists %d errors' % nerr)
        need(os.path.getmtime(rep) >= os.path.getmtime(os.path.join(HW, 'famicart.kicad_pcb')) - 2, 'drc_report.txt is older than the board file (run route_pcb.py export)')
        info.append('KiCad DRC report: %d errors, %d warnings' % (nerr, txt.count('Severity: warning')))
    else: bad.append('no drc_report.txt next to the board (run route_pcb.py export)')
    marks = [d.GetText() for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and 'JLCJLC' in d.GetText()]
    need(not marks, 'the silkscreen still carries the order-number marker %s (JLCPCB would print it literally)' % marks)
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
        rects = [(ToMM(r.GetX()), ToMM(r.GetY()), ToMM(r.GetRight()), ToMM(r.GetBottom())) for r in (p.GetBoundingBox() for p in j1.Pads())]
        fx0, fy0, fx1 = min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects)
        # solder mask: one window per side over everything below the track keep-out line (JLCPCB: "fully opened")
        import gen_pcb
        ytop = gen_pcb.BODY_H + gen_pcb.FINGER_KEEP
        for layer, name in ((pcbnew.F_Mask, 'front'), (pcbnew.B_Mask, 'back')):
            win = [g.GetBoundingBox() for g in j1.GraphicalItems() if g.GetLayer() == layer and g.IsFilled()]
            ok = any(ToMM(w.GetX()) <= fx0 + TOL and ToMM(w.GetRight()) >= fx1 - TOL and ToMM(w.GetY()) <= ytop + TOL and ToMM(w.GetBottom()) >= bottom - TOL for w in win)
            if getattr(D, 'JLC_RULES', False): need(ok, 'no solder mask window over the %s fingers (JLCPCB: the finger area must be fully opened)' % name)
        if getattr(D, 'JLC_RULES', False):
            need(bool(j1.GetAttributes() & pcbnew.FP_ALLOW_SOLDERMASK_BRIDGES), 'J1 lacks the "allow solder mask bridges" attribute')
            low = [t for t in tracks + vias if max(ToMM(t.GetStart().y), ToMM(t.GetEnd().y)) > ytop + TOL]
            need(not low, '%d tracks / vias inside the finger window' % len(low))
        # plated holes and silkscreen keep 1.0 mm from the fingers
        def gap(x, y, r):
            return min(math.hypot(max(a - x, 0.0, x - c), max(b - y, 0.0, y - d)) for (a, b, c, d) in rects) - r
        if vias:
            g = min(gap(ToMM(v.GetPosition().x), ToMM(v.GetPosition().y), ToMM(v.GetWidth()) / 2) for v in vias)
            info.append('closest via to a finger: %.2f mm' % g)
            need(g >= FINGER_HOLE - TOL, 'a via sits %.2f mm from a gold finger (< %.1f mm)' % (g, FINGER_HOLE))
        near = []
        for it in items:
            if it.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS): continue
            if 'TEXT' in it.GetClass() and not it.IsVisible(): continue
            ib = it.GetBoundingBox()
            if ToMM(ib.GetBottom()) > fy0 - FINGER_HOLE and ToMM(ib.GetRight()) > fx0 - FINGER_HOLE and ToMM(ib.GetX()) < fx1 + FINGER_HOLE: near.append(it)
        need(not near, '%d silkscreen items within %.1f mm of the gold fingers' % (len(near), FINGER_HOLE))

    # ---- order package (present only after gen_jlc.py)
    z = os.path.join(HW, 'jlcpcb', 'gerbers.zip')
    if os.path.exists(z):
        names = zipfile.ZipFile(z).namelist()
        extra = [n for n in names if 'Fab' in n or n.endswith('.gbrjob')]
        if getattr(D, 'JLC_RULES', False): need(not extra, 'gerbers.zip carries non-fabrication files: %s' % extra)
        for k in ('F_Cu.gtl', 'B_Cu.gbl', 'F_Mask.gts', 'B_Mask.gbs', 'Edge_Cuts.gm1', 'PTH.drl'):
            need(any(n.endswith(k) for n in names), 'gerbers.zip lacks %s' % k)
        info.append('gerbers.zip: %d files' % len(names))
        drl = [n for n in names if n.endswith('PTH.drl') and 'NPTH' not in n]
        hits = sum(1 for n in drl for line in zipfile.ZipFile(z).read(n).decode('ascii', 'replace').splitlines() if line.startswith('X'))
        need(hits == len(vias), 'the plated drill file in gerbers.zip has %d holes, the board has %d vias' % (hits, len(vias)))
        need(os.path.getmtime(z) >= os.path.getmtime(os.path.join(HW, 'famicart.kicad_pcb')) - 2, 'gerbers.zip is older than the board file')
        cpl = list(csv.DictReader(open(os.path.join(HW, 'jlcpcb', 'cpl_jlc.csv'))))
        need({r['Designator'] for r in cpl} == placed, 'CPL designators differ from the parts JLCPCB places: %s' % sorted({r['Designator'] for r in cpl} ^ placed)[:8])
        need(all(r['Layer'] == 'Top' for r in cpl), 'CPL has bottom-side placements')
        pc = os.path.join(HW, 'jlcpcb', 'parts_check.csv')
        if os.path.exists(pc):
            rows = list(csv.DictReader(open(pc)))
            need(all(r['Library'] == 'Basic' and r['Result'] == 'OK' for r in rows), 'parts_check.csv: not every part is a Basic part in stock')
            info.append('parts_check.csv: %d part numbers, all Basic' % len(rows))
    else: info.append('no jlcpcb/gerbers.zip yet (run gen_jlc.py)')
    # ---- board with edge rails (make_rails.py)
    RA = getattr(D, 'RAILS', None)
    if RA and os.path.exists(z):
        zr = os.path.join(HW, 'jlcpcb', 'gerbers_rails.zip'); rr = os.path.join(HW, 'drc_report_rails.txt'); rb = os.path.join(HW, 'famicart_rails.kicad_pcb')
        if not (os.path.exists(zr) and os.path.exists(rr) and os.path.exists(rb)): bad.append('no board with edge rails yet (run make_rails.py)')
        else:
            need(os.path.getmtime(rb) >= os.path.getmtime(os.path.join(HW, 'famicart.kicad_pcb')) - 2, 'famicart_rails.kicad_pcb is older than the board file (run make_rails.py)')
            nerr = open(rr).read().count('Severity: error'); need(nerr == 0, 'drc_report_rails.txt lists %d errors' % nerr)
            br = pcbnew.LoadBoard(rb); rbb = br.GetBoardEdgesBoundingBox(); pw, ph = ToMM(rbb.GetWidth()) - 0.1, ToMM(rbb.GetHeight()) - 0.1
            wantw = bw + 2 * (RA['gap'] + RA['width'])
            need(abs(pw - wantw) < 0.01 and abs(ph - bh) < 0.01, 'panel with rails is %.2f x %.2f mm, expected %.2f x %.2f' % (pw, ph, wantw, bh))
            nfid = sum(1 for f in br.GetFootprints() if f.GetReference().startswith('FID')); nmb = sum(1 for f in br.GetFootprints() if f.GetReference().startswith('MB'))
            need(nfid == len(RA['fiducials']), '%d fiducials on the rails, %d expected' % (nfid, len(RA['fiducials'])))
            need(nmb == RA['holes'] * sum(len(v) for v in RA['tabs'].values()), '%d break-off holes, expected %d' % (nmb, RA['holes'] * sum(len(v) for v in RA['tabs'].values())))
            same = all((t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y) == (u.GetStart().x, u.GetStart().y, u.GetEnd().x, u.GetEnd().y) for t, u in zip(b.GetTracks(), br.GetTracks())) and len(b.GetTracks()) == len(br.GetTracks())
            need(same, 'the tracks of the railed board differ from the board')
            info.append('with edge rails: panel %.1f x %.1f mm, %d fiducials, %d break-off holes, DRC errors %d, gerbers_rails.zip present' % (pw, ph, nfid, nmb, nerr))

    print('JLCPCB check:', 'OK' if not bad else '%d problems' % len(bad))
    for x in info: print('   ', x)
    for x in bad: print('  FAIL', x)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
