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
  gerbers.zip       fabrication layers and drill files only; every file is compared with a fresh plot of the board
                    (so an archive that was made from another state of the board is refused)
  routed            a board without tracks, with open connections or with DRC errors is refused
  edge rails        (designs with RAILS) the railed board is measured, not the numbers of the design: the board inside
                    the rails is the routed board object for object, rails >= 5 mm, break-off tabs >= 5 mm with holes
                    of 0.5-0.8 mm that are 0.2-0.3 mm apart, 1 mm fiducials centred >= 3.85 mm from the panel edges,
                    2 mm tooling holes, rails that end above the gold-finger edge; its design rule check is run
                    here, and gerbers_rails.zip is compared with a fresh plot
  order notes       the track / via / open-connection counts printed in jlcpcb/README.md are those of the board
Exit status 1 when anything fails.   FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg python3 check_jlc.py"""
import os, sys, re, math, csv, zipfile, importlib, subprocess, tempfile
import pcbnew
from pcbnew import ToMM, FromMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
HW = os.path.abspath(os.environ['FC_HW_DIR'])
SH = getattr(D, 'SHELL', None)

MIN_TRACK, MIN_DRILL, MIN_RING2, HOLE_HOLE = 0.10, 0.30, 0.10, 0.20
EDGE_ROUTED, EDGE_VCUT, MIN_SLOT = 0.20, 0.40, 1.0
SILK_LINE, SILK_TEXT = 0.15, 1.0
FINGER_TO_EDGE, FINGER_HOLE = 1.15, 1.0
TOL = 0.002
RAIL_MIN, TAB_MIN, BITE_D, BITE_WEB, FID_EDGE, TOOL_D = 5.0, 5.0, (0.5, 0.8), (0.2, 0.3), 3.85, 2.0     # JLCPCB, 'Mouse bites Panel'
FAB_SUFFIX = ('_Cu.gtl', '_Cu.gbl', '_Paste.gtp', '_Paste.gbp', '_Silkscreen.gto', '_Silkscreen.gbo', '_Mask.gts', '_Mask.gbs', 'Edge_Cuts.gm1', 'PTH.drl')
PM = pcbnew.SHAPE_POLY_SET.PM_FAST

def undated(text):
    """A Gerber / drill file without the lines that carry the time of plotting."""
    return '\n'.join(l for l in text.splitlines() if 'CreationDate' not in l and ' date ' not in l)

def fresh_plot(pcb):
    """{file name: contents without dates} of the fabrication files, plotted now from the board file."""
    out = tempfile.mkdtemp(prefix='check_jlc_')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts', '-o', out + '/', pcb], check=True, capture_output=True)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '-o', out + '/', pcb], check=True, capture_output=True)
    return {n: undated(open(os.path.join(out, n), errors='replace').read()) for n in sorted(os.listdir(out)) if n.endswith(FAB_SUFFIX)}

def archive_differences(zpath, pcb):
    """Names of the archive members that are not what the board file plots today (missing, extra or different)."""
    zf = zipfile.ZipFile(zpath); have = {n: undated(zf.read(n).decode('utf-8', 'replace')) for n in zf.namelist()}
    want = fresh_plot(pcb)
    return sorted(n for n in set(have) | set(want) if have.get(n) != want.get(n)), len(want)

def copper_objects(b, skip=()):
    """Everything that makes the circuit of a board, as comparable tuples: tracks, vias, footprints with their pads, pours."""
    out = []
    for t in b.GetTracks():
        via = t.GetClass() == 'PCB_VIA'
        out.append(('via' if via else 'track', t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth(), t.GetDrillValue() if via else 0,
                    0 if via else t.GetLayer(), t.GetNetname()))
    for fp in b.GetFootprints():
        if fp.GetReference().startswith(skip): continue
        out.append(('part', fp.GetReference(), fp.GetPosition().x, fp.GetPosition().y, round(fp.GetOrientationDegrees(), 3), fp.IsFlipped()))
        for p in fp.Pads():
            out.append(('pad', fp.GetReference(), p.GetNumber(), p.GetPosition().x, p.GetPosition().y, p.GetSize().x, p.GetSize().y, p.GetDrillSize().x,
                        p.GetNetname(), p.GetLayerSet().FmtHex()))
    for z in b.Zones():
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if z.GetIsRuleArea() or not z.IsOnLayer(layer): continue
            poly = z.GetFilledPolysList(layer)
            out.append(('pour', z.GetNetname(), layer, poly.OutlineCount(), sum(poly.Outline(i).PointCount() for i in range(poly.OutlineCount())), round(poly.Area() / 1e9)))
    return sorted(out, key=repr)

def edge_items(b):
    """Edge.Cuts drawings as direction-independent tuples in micrometres."""
    out = []
    for d in b.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts: continue
        a, e = (round(d.GetStart().x / 1000), round(d.GetStart().y / 1000)), (round(d.GetEnd().x / 1000), round(d.GetEnd().y / 1000))
        out.append((d.GetShape(),) + tuple(sorted((a, e))))
    return out

def outline_polygon(b):
    ps = pcbnew.SHAPE_POLY_SET()
    if not b.GetBoardPolygonOutlines(ps): raise SystemExit('the outline of the board is not a closed contour')
    return ps

def rect(x0, y0, x1, y1):
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): ps.Append(FromMM(x), FromMM(y))
    return ps

def pieces(ps):
    """Bounding boxes (x0, y0, x1, y1) in mm of the separate pieces of a polygon set."""
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i); xs = [ToMM(o.CPoint(k).x) for k in range(o.PointCount())]; ys = [ToMM(o.CPoint(k).y) for k in range(o.PointCount())]
        out.append((min(xs), min(ys), max(xs), max(ys)))
    return sorted(out, key=lambda r: (r[0], r[1]))

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
    if tracks:                                   # the rule check itself, run now on the board file as it is
        rep_now = os.path.join(tempfile.mkdtemp(prefix='check_jlc_'), 'drc.txt')
        pcbnew.WriteDRCReport(b, rep_now, pcbnew.EDA_UNITS_MILLIMETRES, True); nnow = open(rep_now).read().count('Severity: error')
        need(nnow == 0, 'the design rule check of the board, run now, lists %d errors' % nnow)
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
    pcb = os.path.join(HW, 'famicart.kicad_pcb')
    z = os.path.join(HW, 'jlcpcb', 'gerbers.zip')
    if os.path.exists(z):
        names = zipfile.ZipFile(z).namelist()
        extra = [n for n in names if 'Fab' in n or n.endswith('.gbrjob')]
        if getattr(D, 'JLC_RULES', False): need(not extra, 'gerbers.zip carries non-fabrication files: %s' % extra)
        for k in ('F_Cu.gtl', 'B_Cu.gbl', 'F_Mask.gts', 'B_Mask.gbs', 'Edge_Cuts.gm1', 'PTH.drl'):
            need(any(n.endswith(k) for n in names), 'gerbers.zip lacks %s' % k)
        drl = [n for n in names if n.endswith('PTH.drl') and 'NPTH' not in n]
        hits = sum(1 for n in drl for line in zipfile.ZipFile(z).read(n).decode('ascii', 'replace').splitlines() if line.startswith('X'))
        need(hits == len(vias), 'the plated drill file in gerbers.zip has %d holes, the board has %d vias' % (hits, len(vias)))
        if getattr(D, 'JLC_RULES', False):
            diff, nplot = archive_differences(z, pcb)
            need(not diff, 'gerbers.zip is not what the board file plots today: %s (run route_pcb.py export and gen_jlc.py)' % diff)
            info.append('gerbers.zip: %d files, each identical to a fresh plot of the board' % len(names) if not diff else 'gerbers.zip: %d files' % len(names))
        else: info.append('gerbers.zip: %d files' % len(names))
        cpl = list(csv.DictReader(open(os.path.join(HW, 'jlcpcb', 'cpl_jlc.csv'))))
        need({r['Designator'] for r in cpl} == placed, 'CPL designators differ from the parts JLCPCB places: %s' % sorted({r['Designator'] for r in cpl} ^ placed)[:8])
        need(all(r['Layer'] == 'Top' for r in cpl), 'CPL has bottom-side placements')
        pc = os.path.join(HW, 'jlcpcb', 'parts_check.csv')
        if os.path.exists(pc):
            rows = list(csv.DictReader(open(pc)))
            need(all(r['Library'] == 'Basic' and r['Result'] == 'OK' for r in rows), 'parts_check.csv: not every part is a Basic part in stock')
            info.append('parts_check.csv: %d part numbers, all Basic' % len(rows))
        notes = os.path.join(HW, 'jlcpcb', 'README.md')
        m = re.search(r'配線 (\d+) 本・ビア (\d+) 個・未接続 (\d+)', open(notes).read()) if os.path.exists(notes) else None
        if m: need((int(m.group(1)), int(m.group(2)), int(m.group(3))) == (len(tracks), len(vias), nopen),
                   'jlcpcb/README.md was written for another board: it says %s tracks / %s vias / %s open, the board has %d / %d / %d (run gen_jlc.py)' % (m.group(1), m.group(2), m.group(3), len(tracks), len(vias), nopen))
        elif getattr(D, 'JLC_RULES', False): bad.append('jlcpcb/README.md does not state the track and via counts of the board')
    else: info.append('no jlcpcb/gerbers.zip yet (run gen_jlc.py)')
    offgrid = sum(1 for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts for q in (d.GetStart(), d.GetEnd()) if q.x % 1000 or q.y % 1000)
    need(not offgrid, '%d outline end points are not on the 0.001 mm grid' % offgrid)

    # ---- board with edge rails (make_rails.py): everything is measured on the railed board, not read from the design
    RA = getattr(D, 'RAILS', None)
    if RA and os.path.exists(z):
        zr = os.path.join(HW, 'jlcpcb', 'gerbers_rails.zip'); rb = os.path.join(HW, 'famicart_rails.kicad_pcb')
        if not (os.path.exists(zr) and os.path.exists(rb)): bad.append('no board with edge rails yet (run make_rails.py)')
        else:
            br = pcbnew.LoadBoard(rb); br.BuildConnectivity()
            # 1. the circuit inside the rails is the routed board, object for object
            from collections import Counter
            ca, cb = Counter(copper_objects(b)), Counter(copper_objects(br, skip=('FID', 'MB', 'TH')))
            diff = list((ca - cb).elements()) + list((cb - ca).elements())
            need(not diff, 'the board inside the rails differs from the routed board in %d objects, e.g. %s (run make_rails.py)' % (len(diff), diff[:2]))
            # 2. its contour: an outline item of the board may be missing in the panel only on the left / right edge lines
            #    (where the routed gaps and the tabs are), and the panel has no other outline item inside the board
            pe, qe = Counter(edge_items(b)), Counter(edge_items(br))
            on_side = lambda it: all(abs(q[0] / 1000.0 - lo) < 0.0015 or abs(q[0] / 1000.0 - hi) < 0.0015 for q in it[1:])
            inside = lambda it: all(lo + 0.0015 < q[0] / 1000.0 < hi - 0.0015 for q in it[1:])
            lost = [it for it in (pe - qe).elements() if not on_side(it)]; added = [it for it in (qe - pe).elements() if inside(it)]
            need(not lost and not added, 'the contour of the board inside the rails is not the contour of the board: %d items missing, %d added, e.g. %s' % (len(lost), len(added), (lost + added)[:2]))
            off2 = sum(1 for d in br.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts for q in (d.GetStart(), d.GetEnd()) if q.x % 1000 or q.y % 1000)
            need(not off2, '%d outline end points of the railed board are not on the 0.001 mm grid' % off2)
            # 3. the rails, measured on the panel polygon
            panel = outline_polygon(br); rbb = br.GetBoardEdgesBoundingBox()
            px0, py0, px1, py1 = ToMM(rbb.GetX()) + 0.05, ToMM(rbb.GetY()) + 0.05, ToMM(rbb.GetRight()) - 0.05, ToMM(rbb.GetBottom()) - 0.05
            pw, ph = px1 - px0, py1 - py0
            need(abs(ph - bh) < 0.01, 'the panel is %.2f mm high, the board %.2f mm: nothing may be added above the board or below the gold fingers' % (ph, bh))
            vx = sorted({round(ToMM(d.GetStart().x), 3) for d in br.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT
                         and d.GetStart().x == d.GetEnd().x})
            inner = {'L': [x for x in vx if px0 + TOL < x < lo - TOL], 'R': [x for x in vx if hi + TOL < x < px1 - TOL]}
            holes = [(ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), ToMM(p.GetDrillSize().x), f.GetReference()) for f in br.GetFootprints() for p in f.Pads()
                     if f.GetReference().startswith(('MB', 'TH'))]
            fids = [f for f in br.GetFootprints() if f.GetReference().startswith('FID')]
            rail_y, ntab, tabw, webs = {}, 0, [], []
            for side in 'LR':
                if len(inner[side]) != 1: bad.append('%s rail: no single inner edge found between the panel edge and the board (%s)' % (side, inner[side])); continue
                xi = inner[side][0]; xo = px0 if side == 'L' else px1; xb = lo if side == 'L' else hi
                rw_, gap_ = abs(xi - xo), abs(xb - xi)
                need(rw_ >= RAIL_MIN - TOL, '%s rail is %.2f mm wide (JLCPCB: at least %.0f mm)' % (side, rw_, RAIL_MIN))
                need(gap_ >= MIN_SLOT - TOL, '%s rail: the routed gap is %.2f mm wide (slots need %.1f mm)' % (side, gap_, MIN_SLOT))
                strip = pcbnew.SHAPE_POLY_SET(panel); strip.BooleanIntersection(rect(min(xo, xi) + rw_ / 2 - 0.05, py0 - 1, min(xo, xi) + rw_ / 2 + 0.05, py1 + 1), PM)
                pc_ = pieces(strip)
                if len(pc_) != 1: bad.append('%s rail is not one piece along its length' % side); continue
                ry0, ry1 = pc_[0][1], pc_[0][3]; rail_y[side] = (ry0, ry1, min(xo, xi), max(xo, xi))
                need(abs(ry0 - py0) < 0.01, '%s rail does not start at the top edge' % side)
                need(py1 - ry1 >= 2.0 - TOL, '%s rail ends %.2f mm above the gold-finger edge line (at least 2.0 mm wanted, so that the edge is free for bevelling)' % (side, py1 - ry1))
                gx = (xi + xb) / 2
                tabs = pcbnew.SHAPE_POLY_SET(panel); tabs.BooleanIntersection(rect(gx - 0.05, py0 - 1, gx + 0.05, py1 + 1), PM)
                tb = [(q[1], q[3]) for q in pieces(tabs)]
                need(len(tb) >= 2, '%s rail hangs on %d tabs' % (side, len(tb)))
                hx = sorted((y, d) for (x, y, d, ref) in holes if ref.startswith('MB') and abs(x - xb) < 1.0)
                for (x, y, d, ref) in holes:
                    if not ref.startswith('MB') or abs(x - xb) >= 1.0: continue
                    need(BITE_D[0] - TOL <= d <= BITE_D[1] + TOL, '%s: break-off hole of %.2f mm (JLCPCB: %.1f-%.1f mm)' % (ref, d, BITE_D[0], BITE_D[1]))
                    over = (x + d / 2 - xb) if side == 'L' else (xb - (x - d / 2))           # > 0: the hole cuts into the board
                    need(-0.05 - TOL <= over <= TOL, '%s: the hole edge is %.3f mm %s the edge line of the board (it must touch the line from outside)' % (ref, abs(over), 'inside' if over > 0 else 'outside'))
                for (ta, tb_) in tb:
                    ntab += 1; tabw.append(tb_ - ta)
                    need(tb_ - ta >= TAB_MIN - TOL, '%s rail: the tab at y %.1f mm is %.2f mm wide (JLCPCB: at least %.0f mm with mouse bites)' % (side, (ta + tb_) / 2, tb_ - ta, TAB_MIN))
                    cut = sorted((max(ta, y - d / 2), min(tb_, y + d / 2)) for (y, d) in hx if y + d / 2 > ta and y - d / 2 < tb_)
                    need(len(cut) >= 3, '%s rail: the tab at y %.1f mm has %d break-off holes' % (side, (ta + tb_) / 2, len(cut)))
                    solid = [(ta, cut[0][0])] + [(c0[1], c1[0]) for c0, c1 in zip(cut, cut[1:])] + [(cut[-1][1], tb_)] if cut else [(ta, tb_)]
                    wrong = []
                    for i, (s0, s1) in enumerate(solid):
                        w = s1 - s0
                        if w <= TOL: continue
                        webs.append(w); end = i in (0, len(solid) - 1)
                        if not (w <= BITE_WEB[1] + TOL and (end or w >= BITE_WEB[0] - TOL)): wrong.append(w)
                    need(not wrong, '%s rail, tab at y %.1f mm: %.2f..%.2f mm of material between break-off holes in %d places (JLCPCB: %.1f-%.1f mm)'
                         % (side, (ta + tb_) / 2, min(wrong, default=0), max(wrong, default=0), len(wrong), BITE_WEB[0], BITE_WEB[1]))
            need(len(fids) >= 3, '%d fiducials on the rails (JLCPCB: 3 or 4)' % len(fids))
            def rail_of(x, y):
                return next(((s, r) for s, r in rail_y.items() if r[2] - TOL <= x <= r[3] + TOL and r[0] - TOL <= y <= r[1] + TOL), (None, None))
            fmin = 99.0
            for f in fids:
                fx, fy = ToMM(f.GetPosition().x), ToMM(f.GetPosition().y); side, r = rail_of(fx, fy)
                if not r: bad.append('%s is not on a rail' % f.GetReference()); continue
                cu = [ToMM(p.GetSize().x) for p in f.Pads()]; mk = [ToMM(p.GetSize().x) + 2 * ToMM(p.GetSolderMaskExpansion()) for p in f.Pads()]
                need(len(cu) == 1 and abs(cu[0] - 1.0) < TOL and abs(mk[0] - 2.0) < TOL, '%s: copper %s mm, mask opening %s mm (JLCPCB: 1 mm, opening twice the copper)' % (f.GetReference(), cu, mk))
                dist = min(fx - px0 if side == 'L' else px1 - fx, fy - r[0], r[1] - fy); fmin = min(fmin, dist)
                need(dist >= FID_EDGE - TOL, '%s: centre %.2f mm from the nearest outer edge of the panel (JLCPCB: %.2f mm)' % (f.GetReference(), dist, FID_EDGE))
                need(min(fx - r[2], r[3] - fx) >= 1.0 - TOL, '%s: its 2 mm mask opening does not fit on the rail' % f.GetReference())
            nth = 0
            for (x, y, d, ref) in holes:
                if not ref.startswith('TH'): continue
                nth += 1; side, r = rail_of(x, y)
                need(abs(d - TOOL_D) < TOL, '%s: tooling hole of %.2f mm (JLCPCB: %.0f mm)' % (ref, d, TOOL_D))
                need(bool(r) and min(x - r[2], r[3] - x, y - r[0], r[1] - y) - d / 2 >= 1.0 - TOL, '%s: tooling hole is not on a rail with 1 mm of material around it' % ref)
            need(nth >= 2, '%d tooling holes on the rails (JLCPCB: 2 mm tooling holes for SMT assembly)' % nth)
            # 4. design rules of the railed board, checked now
            rep2 = os.path.join(tempfile.mkdtemp(prefix='check_jlc_'), 'drc_rails.txt')
            pcbnew.WriteDRCReport(br, rep2, pcbnew.EDA_UNITS_MILLIMETRES, True); nerr2 = open(rep2).read().count('Severity: error')
            need(nerr2 == 0, 'the design rule check of the railed board lists %d errors' % nerr2)
            # 5. the archive is what the railed board plots today
            diff, nplot = archive_differences(zr, rb)
            need(not diff, 'gerbers_rails.zip is not what famicart_rails.kicad_pcb plots today: %s (run make_rails.py)' % diff)
            info.append('with edge rails: panel %.1f x %.1f mm; the board inside is the routed board (%d objects compared); %d tabs of %.2f..%.2f mm, material between break-off holes %.2f..%.2f mm; '
                        '%d fiducials, nearest %.2f mm from a panel edge; %d tooling holes; rails end %.2f mm above the finger edge; DRC errors %d; gerbers_rails.zip %s'
                        % (pw, ph, sum(ca.values()), ntab, min(tabw, default=0), max(tabw, default=0), min(webs, default=0), max(webs, default=0), len(fids), fmin, nth,
                           min((py1 - r[1] for r in rail_y.values()), default=0), nerr2, 'identical to a fresh plot' if not diff else 'DIFFERS'))

    print('JLCPCB check:', 'OK' if not bad else '%d problems' % len(bad))
    for x in info: print('   ', x)
    for x in bad: print('  FAIL', x)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
