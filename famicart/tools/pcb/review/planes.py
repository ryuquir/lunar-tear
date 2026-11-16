#!/usr/bin/env python3
"""Reference planes under the signal tracks of a routed board with inner plane layers (rev H: 6 layers; docs/13 "基板").

What it checks, and why
  A signal's return current flows in the plane next to its track. Where that plane has no copper (antipads, merged
  antipads, clearance gaps, the plane's edge) or changes net (the edge of a power island), the return current has to go
  round the gap, through the plane on the other side, or through a via or a capacitor to another plane: the current
  loop grows, and with it ringing, crosstalk and emission. docs/13 "配線の決まり" therefore puts the fast lines (WLINK,
  XLINK, SWD, USB) on the outer layers next to a whole GND plane and lets no In3 signal cross a boundary of the In2 power
  plane. For every signal layer against the plane nearest to it in the board's stack-up (rev H: F.Cu over In1 GND
  0.0994 mm; In3 over In2 +3V3 0.1164 mm with In4 GND 0.35 mm on its other side; B.Cu over In4 GND 0.0994 mm):
    1  per class and per net: the stretches off the reference plane's board-wide zone (over no copper or over an island)
       longer than --min-void, where they are and why the copper is missing, and how much of each has no copper on the
       second plane either, sampled along the whole stretch (In3: the plane on its other side, In4; F.Cu / B.Cu: the
       next plane beyond their reference); the length with copper on neither plane; the void runs of a stricter test in
       which either track edge (+-w/2) over no copper counts; on a plane with islands also the island-edge crossings,
       the net changes and the length over island copper;
    2  with islands: each island's copper, the vias of its net that join each piece, the tracks over it, its crossings;
    3  the plane copper: pieces; copper cut off by island removal; holes, and those longer than --slot (merged antipads);
       webs between two holes narrower than --web; the stitching vias (where their antipads go, whether a track runs over
       one), and the tracks over the antipads of the other vias of a plane net;
    4  the docs/13 rule: the length of every fast class on inner signal layers against its total; the tracks that cross
       the USB pair in plan view; every via where a fast net changes layer, with the distance to the nearest via of a
       plane net next to both layers and to the nearest capacitor between two different reference nets.
  Fast nets (FAST: XLINK, WLINK, PLINK, LINK, SWD, QSPI, USB, crystal, microSD) are listed one by one, the others
  ("slow") in summaries (--all-slow lists them one by one). Power nets (the design's POWER_NETS, switch nodes) are not
  checked.

Method (geometry on the track centrelines, board mm; no field solver)
  * The board and its .kicad_pro / .kicad_dru are copied into --out and only the copy is loaded; tracks, vias, pads,
    zones, rule areas and Edge.Cuts are read as plain data first. The zones are filled in child processes (KiCad's
    ZONE_FILLER: once by the board's rules, once with island removal off) that hand back every filled polygon (outline
    with holes) and never save.
  * Tracks: ends of one net on one layer are one node when they coincide or lie within 2 um of each other; a loose end
    that lies on another segment of its net is joined to it. Arcs become chords of 0.1 mm.
  * Each segment is cut exactly where its centreline crosses an edge of the plane's fill; each piece is classed by an
    even-odd point-in-polygon test of its midpoint (which zone's copper, or none). Pieces of one class that meet at a
    node form one run. A piece inside a pad of the track's own net is pad copper and not counted.
  * The antipads of the track's own vias (via pad / 2 + zone clearance + 0.01 mm) are not counted as missing copper:
    every layer change passes through one. A stretch is a run off the board-wide zone; the second plane is cut along
    all of it in the same exact way.
  * With islands: "edge x" counts every crossing of an island's drawn outline by the centreline (the docs/13 rule; it
    does not depend on the fill); "net x" every change of the plane net under the track, with or without a gap between.
    At a via of the track's own net the copper under the track is the net with most copper on two rings just outside
    the antipad, so a track that leaves a via standing in +3V3 and reaches island copper first has changed nets.
  * Causes of missing copper, looked up at points every 0.05 mm: rule areas, the plane outline, the clearance ring of an
    island, antipads of other vias, holes and pads, the board edge, else copper KiCad removed (minimum width, islands).
  * Holes: every hole of every fill piece is classed (ring round an island, antipads of n vias, a pad, hole or rule area
    inside); its length is its largest extent over 16 directions; a web is the smallest distance between two rings of
    one piece (vertex to edge, both ways).
  * Stitching vias: with --before, the plane-net vias that board lacks; else the plane-net vias at which no track of
    their net ends and that lie in no pad of their net.

Self-check (exit status 2 and "FAILED" in the report when one does not hold)
  The stored fill equals a fresh one; the .kicad_pro is there; every piece of the fill is also in the fill made with
  island removal off; every fast class matches nets of the board; the antipads measured at the vias of other nets are
  pad + zone clearance (the own-via rule rests on it); every class length of every net equals a re-measurement by
  sampling every 0.02 mm; with islands, every connected piece of track that touches copper of k plane nets has at
  least k - 1 net changes (a lower bound counted without the run logic), and the per-island table adds up to the total.
  Differences between the board and its design (PLANES, TRACK / CLEAR / VIA_DIA, unrouted items) are notes: they do not
  make the numbers wrong.

Assumptions
  * Signal layer -> reference: the plane layer with the least dielectric between (stack-up block of the board file;
    docs/13: JLC06121H-3313). Second plane: the plane on the other side if it is within 0.5 mm (assumed), else the next
    plane beyond the reference. A plane layer is an inner layer with a zone filled over at least half the area of the
    largest zone (assumed).
  * The fill is the one KiCad 7 makes from the board's .kicad_pro (checked against the fill stored in the file).
  * --min-void 1.0, --slot 3.0 and --web 0.2 mm are the review's thresholds, not a standard.
  * The copper round a via is judged on rings 0.15 and 0.30 mm outside its antipad, at least 24 of their 144 points
    over copper (assumed).
  * Fast / slow is decided by net name (FAST); docs/13 restricts only OUTER_ONLY to the outer layers.
  * A capacitor between two plane nets is a footprint C<n> with its two pads on those nets.

Limits
  * Centreline and +-w/2 only; pours on the signal layers themselves are not counted as a reference. Nothing is said
    about impedance, edge rates or crosstalk; the numbers are lengths and distances. As a scale: on In3 (er 4.16-4.6)
    a signal travels about 7 ps per mm, so a 3 mm gap is passed in about 20 ps.
  * Pads and via barrels are not checked as signals; the card-edge fingers lie over no plane by design.
  * A web inside one hole that folds back on itself is not measured. A track exactly along an outline is classed by
    rounding.
  * Without --before, a stitching via that happens to sit on a track end of its net is not recognised (rev H: 1 of 146).
  * Written for KiCad 7.0.11 (fill rules, island removal, Python API).

Usage (any working directory; the design module is looked up in the folder above this one)
    python3 review/planes.py BOARD.kicad_pcb [--design design_revh] [--out DIR] [--before OLD.kicad_pcb] [--drc]
            [--min-void 1.0] [--slot 3.0] [--web 0.2] [--all-slow] [--stored-fill] [--zoom X,Y[,W]] ...
  --design (or FC_DESIGN) names the design module: POWER_NETS, the coordinate origin (at), PLANES, TRACK / CLEAR / VIA_DIA.
  --out takes every file the tool writes (default: a fresh temporary folder, named in the report): planes.txt (the
  report, also on stdout), planes.json (every run, stretch, crossing, hole, layer change), one SVG per signal layer
  (plane fill, tracks, vias, stitching vias green, cut-off copper orange, long stretches red, island-edge crossings
  blue), zoom_*.svg for --zoom, drc.txt for --drc (KiCad's rule check of the copy), the copies of the boards.
  Exit status: 0; 2 when a self-check failed (the report then says which and cannot be relied on); 1 on usage errors.

A healthy result
  Self-check all ok. No fast net with an island-edge crossing or a net change; no fast stretch longer than --min-void,
  or, where a via field makes one, the second plane whole along it; no fast length with copper on neither plane beyond
  the chord of single antipads (about 0.5 mm at minimum clearance). Every island piece joined by two or more vias of
  its net. Every plane in one piece; no hole longer than --slot except via fields and rings round islands; no web
  narrower than the zone's minimum width; no track over the antipad of a stitching via. The fast classes of the docs/13
  rule with 0 mm on inner layers, and every layer change of a fast net within a few mm of a return via and, between
  planes of two nets, of a capacitor. A board without inner plane layers (rev G: 2 layers) has nothing to check and
  the tool says so.
"""
import os, sys
sys.dont_write_bytecode = True                     # before any import from the tools folder: nothing is written there
import re, json, math, time, shutil, hashlib, argparse, tempfile, importlib, subprocess, collections
import numpy as np

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # tools/pcb: the design modules
NM = 1e-6                          # mm per KiCad internal unit
OWN_TOL = 0.01                     # mm added to the own-via antipad radius (the fill approximates the circle by a polygon)
CAUSE_PAD = 0.15                   # mm: a void point within (copper item + zone clearance + this) is caused by that item
SAMPLE = 0.05                      # mm between cause sample points
JOIN_TOL = 0.002                   # mm: track ends this close to each other are one node
RINGS, RING_N, RING_MIN = (0.15, 0.30), 72, 24      # rings outside a via's antipad (mm), points per ring, least points over copper
CHECK_STEP = 0.02                  # mm: sampling step of the self-check that re-measures every class length

# Net classes by name. Fast first; everything else that is not a power net is slow.
FAST = [('XLINK', r'X(H[12]|\d\d)_(\d|H)_(CK|D[01])'), ('WLINK', r'WL_(CK|D[01])'), ('PLINK', r'PLINK_[A-Z]'),
        ('LINK', r'LINK(_[A-F])?'), ('SWD', r'SW(CLK|DIO)\d'), ('QSPI', r'QSPI\d_(SCLK|SD[0-3]|SS\d?)'),
        ('USB', r'USB_D[PM](_R)?'), ('XTAL', r'XIN\d|XOUT\d(_R)?'), ('SD', r'SD_(CLK|CMD|DAT[0-3])')]
POWER_EXTRA = r'SW_\d.*'           # converter switch nodes (SW_1V1, SW_3V3) count as power
OUTER_ONLY = ('WLINK', 'XLINK', 'SWD', 'USB')      # docs/13 配線の決まり: these run on F.Cu / B.Cu, next to a whole GND plane

def net_class(net, power):
    if net in power or re.fullmatch(POWER_EXTRA, net): return 'power'
    for name, pat in FAST:
        if re.fullmatch(pat, net): return name
    return 'slow'

# ---------------------------------------------------------------------------------------------------------- pcbnew side
def arc_points(s, m, e, step=0.1e6):
    """Chord points (nm) of the arc through s, m, e."""
    (ax, ay), (bx, by), (cx, cy) = s, m, e
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-6: return [s, e]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, m, e))
    def norm(a): return (a - a0) % (2 * math.pi)
    sweep = norm(a1)
    if norm(am) > sweep: sweep -= 2 * math.pi          # the arc runs the other way round
    n = max(2, int(abs(sweep) * r / step) + 1)
    pts = [(int(round(ux + r * math.cos(a0 + sweep * i / n))), int(round(uy + r * math.sin(a0 + sweep * i / n)))) for i in range(n + 1)]
    pts[0], pts[-1] = tuple(s), tuple(e)
    return pts

def chain_pts(ch):
    return [(ch.CPoint(j).x, ch.CPoint(j).y) for j in range(ch.PointCount())]

def poly_rings(ps):
    """SHAPE_POLY_SET -> [[outline, hole, ...], ...] in nm."""
    return [[chain_pts(ps.Outline(k))] + [chain_pts(ps.Hole(k, h)) for h in range(ps.HoleCount(k))] for k in range(ps.OutlineCount())]

def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()

def stage(src, folder):
    """Copy a board and its project files (.kicad_pro: the rules the zones are filled with) into `folder`."""
    os.makedirs(folder, exist_ok=True)
    dst = os.path.join(folder, os.path.basename(src)); shutil.copyfile(src, dst)
    found = []
    for ext in ('.kicad_pro', '.kicad_dru'):
        if os.path.exists(os.path.splitext(src)[0] + ext):
            shutil.copyfile(os.path.splitext(src)[0] + ext, os.path.splitext(dst)[0] + ext); found.append(ext)
    return dst, found

def read_board(path):
    """Everything the check needs from the board, as plain Python data (nm), read before any zone fill."""
    import pcbnew
    b = pcbnew.LoadBoard(path)
    cu = list(b.GetEnabledLayers().CuStack())
    lname = {l: str(b.GetLayerName(l)) for l in cu}
    tracks, vias = [], []
    for t in b.GetTracks():
        cls = t.GetClass()
        if cls == 'PCB_VIA':
            p = t.GetPosition()
            vias.append(dict(x=p.x, y=p.y, d=t.GetWidth(), net=str(t.GetNetname()), top=lname.get(t.TopLayer()), bot=lname.get(t.BottomLayer())))
            continue
        lay = lname.get(t.GetLayer())
        if lay is None: continue
        s, e = t.GetStart(), t.GetEnd()
        pts = arc_points((s.x, s.y), (t.GetMid().x, t.GetMid().y), (e.x, e.y)) if cls == 'PCB_ARC' else [(s.x, s.y), (e.x, e.y)]
        for a, c in zip(pts, pts[1:]): tracks.append((lay, str(t.GetNetname()), a[0], a[1], c[0], c[1], t.GetWidth()))
    pads, fps = [], []
    kinds = {pcbnew.PAD_ATTRIB_PTH: 'pth', pcbnew.PAD_ATTRIB_SMD: 'smd', pcbnew.PAD_ATTRIB_CONN: 'conn', pcbnew.PAD_ATTRIB_NPTH: 'npth'}
    for fp in b.GetFootprints():
        fps.append(dict(ref=str(fp.GetReference()), x=fp.GetPosition().x, y=fp.GetPosition().y))
        for p in fp.Pads():
            bb = p.GetBoundingBox(); attr = kinds.get(p.GetAttribute(), '?')
            shape = {}                                       # copper outline of the pad per layer (for "track inside its pad")
            for l in cu:
                if attr == 'npth' or not p.IsOnLayer(l): continue
                ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps, l, 0, pcbnew.FromMM(0.005))
                shape[lname[l]] = poly_rings(ps)
            pads.append(dict(ref=str(fp.GetReference()), num=str(p.GetNumber()), net=str(p.GetNetname()), attr=attr,
                             bbox=(bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()), layers=[lname[l] for l in cu if p.IsOnLayer(l)], shape=shape))
    zones, rules = [], []
    for i, z in enumerate(b.Zones()):
        polys = poly_rings(z.Outline()); layers = [lname[l] for l in z.GetLayerSet().CuStack() if l in lname]
        if z.GetIsRuleArea(): rules.append(dict(index=i, name=str(z.GetZoneName()), layers=layers, polys=polys, pour=z.GetDoNotAllowCopperPour()))
        else: zones.append(dict(index=i, net=str(z.GetNetname()), layers=layers, priority=z.GetAssignedPriority(), clearance=z.GetLocalClearance(),
                                min_width=z.GetMinThickness(), polys=polys))
    edges = []
    for d in b.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts or d.GetClass() != 'PCB_SHAPE': continue
        sh = d.GetShape()
        if sh == pcbnew.SHAPE_T_SEGMENT: pts = [(d.GetStart().x, d.GetStart().y), (d.GetEnd().x, d.GetEnd().y)]
        elif sh == pcbnew.SHAPE_T_ARC: pts = arc_points((d.GetStart().x, d.GetStart().y), (d.GetArcMid().x, d.GetArcMid().y), (d.GetEnd().x, d.GetEnd().y))
        elif sh == pcbnew.SHAPE_T_CIRCLE:
            c, r = d.GetCenter(), d.GetRadius(); pts = [(c.x + r * math.cos(a * math.pi / 32), c.y + r * math.sin(a * math.pi / 32)) for a in range(65)]
        elif sh == pcbnew.SHAPE_T_RECT:
            x0, y0, x1, y1 = d.GetStart().x, d.GetStart().y, d.GetEnd().x, d.GetEnd().y; pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        elif sh == pcbnew.SHAPE_T_POLY:
            pts = chain_pts(d.GetPolyShape().Outline(0)); pts.append(pts[0])
        else: continue
        edges += [(a[0], a[1], c[0], c[1]) for a, c in zip(pts, pts[1:])]
    ds = b.GetDesignSettings(); nc = ds.m_NetSettings.m_DefaultNetClass
    return dict(order=[lname[l] for l in cu], tracks=tracks, vias=vias, pads=pads, fps=fps, zones=zones, rules=rules, edges=edges,
                edge_clearance=ds.m_CopperEdgeClearance, hole_clearance=ds.m_HoleClearance,
                netclass=dict(clearance=nc.GetClearance() * NM, track=nc.GetTrackWidth() * NM, via=nc.GetViaDiameter() * NM))

def fill_worker(path, out, mode, drc):
    """Child process: fill every zone of the board at `path` ('fresh'; 'keep-islands': the same with island removal off;
    'stored': no fill) and write the filled polygons of every zone and layer as JSON to `out`; with `drc`, KiCad's rule
    check of that state goes into that file. Nothing is saved."""
    import pcbnew
    b = pcbnew.LoadBoard(path)
    zs = [(i, z) for i, z in enumerate(b.Zones()) if not z.GetIsRuleArea()]
    def stats():
        res = []
        for i, z in zs:
            for l in z.GetLayerSet().CuStack():
                if not z.HasFilledPolysForLayer(l): res.append([i, str(b.GetLayerName(l)), 0, 0, 0.0]); continue
                ps = z.GetFilledPolysList(l)
                res.append([i, str(b.GetLayerName(l)), ps.OutlineCount(), ps.TotalVertices(), ps.Area() * NM * NM])
        return res
    before = stats(); t0 = time.time()
    if mode == 'keep-islands':
        for i, z in zs: z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    if mode != 'stored': pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    dt = time.time() - t0; after = stats()
    b.BuildConnectivity(); open_ = b.GetConnectivity().GetUnconnectedCount(False)
    zones = []
    for i, z in zs:
        for l in z.GetLayerSet().CuStack():
            if not z.HasFilledPolysForLayer(l): continue
            ps = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(l)); ps.Unfracture(pcbnew.SHAPE_POLY_SET.PM_FAST)
            zones.append(dict(index=i, layer=str(b.GetLayerName(l)), polys=poly_rings(ps)))
    with open(out, 'w') as f: json.dump(dict(before=before, after=after, seconds=dt, mode=mode, unconnected=open_, zones=zones), f)
    if drc: pcbnew.WriteDRCReport(b, drc, pcbnew.EDA_UNITS_MILLIMETRES, False)

def run_fill(board, work, mode='fresh', drc=None):
    """fill_worker in a child process (pcbnew objects are not usable after a fill in the same process)."""
    tmp = os.path.join(work, 'fill_%s_%d.json' % (mode, os.getpid()))
    r = subprocess.run([sys.executable, '-B', os.path.abspath(__file__), '--fill-worker', board, tmp, mode, drc or '-'], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(tmp): raise SystemExit('planes.py: the zone-fill child failed:\n' + r.stdout + r.stderr)
    try:
        with open(tmp) as f: return json.load(f)
    finally:
        os.unlink(tmp)

def read_stackup(path):
    """[(layer name, type, thickness mm, epsilon_r)] from the board file's (stackup ...) block."""
    with open(path, encoding='utf-8') as f: txt = f.read()
    m = re.search(r'\(stackup\b(.*?)\(copper_finish', txt, re.S)
    out = []
    for name, typ, rest in re.findall(r'\(layer "([^"]+)" \(type "([^"]+)"\)([^\n]*)', m.group(1) if m else ''):
        th = re.search(r'\(thickness ([\d.]+)\)', rest); er = re.search(r'\(epsilon_r ([\d.]+)\)', rest)
        out.append((name, typ, float(th.group(1)) if th else 0.0, float(er.group(1)) if er else None))
    return out

# ---------------------------------------------------------------------------------------------------------- geometry
def pip_small(px, py, rings):
    """Even-odd point-in-polygon of points (arrays, mm) against a few rings (lists of (x, y) mm)."""
    px = np.asarray(px, float); py = np.asarray(py, float); inside = np.zeros(len(px), bool)
    for r in rings:
        a = np.asarray(r, float)
        if len(a) < 3: continue
        b = np.roll(a, -1, axis=0)
        x1, y1, x2, y2 = a[:, 0][None, :], a[:, 1][None, :], b[:, 0][None, :], b[:, 1][None, :]
        Y = py[:, None]; X = px[:, None]
        cond = (y1 > Y) != (y2 > Y)
        dy = np.where(y2 != y1, y2 - y1, 1.0)
        xi = x1 + (Y - y1) * (x2 - x1) / dy
        inside ^= (np.count_nonzero(cond & (xi > X), axis=1) & 1).astype(bool)
    return inside

def seg_dist(px, py, x1, y1, x2, y2):
    """Distance of points (m) to segments (n): (m, n) array."""
    px = np.asarray(px, float)[:, None]; py = np.asarray(py, float)[:, None]
    dx, dy = (x2 - x1)[None, :], (y2 - y1)[None, :]
    l2 = np.where(dx * dx + dy * dy > 0, dx * dx + dy * dy, 1.0)
    t = np.clip(((px - x1[None, :]) * dx + (py - y1[None, :]) * dy) / l2, 0.0, 1.0)
    return np.hypot(px - (x1[None, :] + t * dx), py - (y1[None, :] + t * dy))

def ring_edges(rings):
    xs1, ys1, xs2, ys2 = [], [], [], []
    for r in rings:
        a = np.asarray(r, float)
        if len(a) < 2: continue
        b = np.roll(a, -1, axis=0); xs1.append(a[:, 0]); ys1.append(a[:, 1]); xs2.append(b[:, 0]); ys2.append(b[:, 1])
    if not xs1: return (np.empty(0),) * 4
    return np.concatenate(xs1), np.concatenate(ys1), np.concatenate(xs2), np.concatenate(ys2)

def ring_area(r):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(r, r[1:] + r[:1]))) / 2

def poly_area(poly):
    return ring_area(poly[0]) - sum(ring_area(h) for h in poly[1:])

class Plane:
    """Copper of one layer as zones (net, label, priority, 'fill': polygons in mm, each [outline, hole, ...]): edge arrays
    with a horizontal strip index, for exact segment cuts and even-odd point location."""
    def __init__(self, zones, strip=0.25):
        self.zones, self.S = zones, strip
        X1, Y1, X2, Y2, Z = [], [], [], [], []
        for zi, z in enumerate(zones):
            for rings in z['fill']:
                x1, y1, x2, y2 = ring_edges(rings)
                X1.append(x1); Y1.append(y1); X2.append(x2); Y2.append(y2); Z.append(np.full(len(x1), zi))
        cat = lambda v: np.concatenate(v) if v else np.empty(0)
        self.x1, self.y1, self.x2, self.y2 = cat(X1), cat(Y1), cat(X2), cat(Y2)
        self.z = cat(Z).astype(int)
        self.prio = np.array([z['priority'] for z in zones], float)
        self.xlo, self.xhi = np.minimum(self.x1, self.x2), np.maximum(self.x1, self.x2)
        self.ylo, self.yhi = np.minimum(self.y1, self.y2), np.maximum(self.y1, self.y2)
        if not len(self.x1):
            self.y0, self.nk, self.start, self.eid = 0.0, 0, np.zeros(1, int), np.empty(0, int); return
        self.y0 = float(self.ylo.min()) - 1.0
        k0 = np.floor((self.ylo - self.y0) / strip).astype(int); k1 = np.floor((self.yhi - self.y0) / strip).astype(int)
        self.nk = int(k1.max()) + 2
        cnt = k1 - k0 + 1
        eid = np.repeat(np.arange(len(k0)), cnt)
        kid = np.repeat(k0, cnt) + (np.arange(int(cnt.sum())) - np.repeat(np.cumsum(cnt) - cnt, cnt))
        o = np.argsort(kid, kind='stable')
        self.eid, kid = eid[o], kid[o]
        self.start = np.searchsorted(kid, np.arange(self.nk + 1))

    def locate(self, px, py):
        """Zone index (into self.zones) of the copper under each point, -1 where there is none."""
        px = np.asarray(px, float); py = np.asarray(py, float); out = np.full(len(px), -1, int)
        if not self.nk: return out
        k = np.floor((py - self.y0) / self.S).astype(int)
        ok = (k >= 0) & (k < self.nk)
        for kk in np.unique(k[ok]):
            P_all = np.nonzero(k == kk)[0]
            E = self.eid[self.start[kk]:self.start[kk + 1]]
            if not len(E): continue
            x1, y1, x2, y2, z = self.x1[E], self.y1[E], self.x2[E], self.y2[E], self.z[E]
            dy = np.where(y2 != y1, y2 - y1, 1.0)
            zs = np.unique(z); ch = max(1, 2000000 // len(E))
            for c0 in range(0, len(P_all), ch):
                P = P_all[c0:c0 + ch]; X = px[P][:, None]; Y = py[P][:, None]
                hit = ((y1[None, :] > Y) != (y2[None, :] > Y)) & (x1[None, :] + (Y - y1[None, :]) * ((x2 - x1) / dy)[None, :] > X)
                best = np.full(len(P), -1); bp = np.full(len(P), -np.inf)
                for zz in zs:
                    ins = (np.count_nonzero(hit[:, z == zz], axis=1) & 1).astype(bool)
                    upd = ins & (self.prio[zz] > bp); best[upd] = zz; bp[upd] = self.prio[zz]
                out[P] = best
        return out

    def cuts(self, ax, ay, bx, by):
        """Parameters t in (0, 1) where the segment a -> b (mm) crosses an edge of this layer's copper."""
        if not self.nk: return np.empty(0)
        ylo, yhi = min(ay, by), max(ay, by); xlo, xhi = min(ax, bx), max(ax, bx)
        k0 = max(int(math.floor((ylo - self.y0) / self.S)), 0); k1 = min(int(math.floor((yhi - self.y0) / self.S)), self.nk - 1)
        if k1 < k0: return np.empty(0)
        E = np.unique(self.eid[self.start[k0]:self.start[k1 + 1]])
        eps = 1e-9
        E = E[(self.xhi[E] >= xlo - eps) & (self.xlo[E] <= xhi + eps) & (self.yhi[E] >= ylo - eps) & (self.ylo[E] <= yhi + eps)]
        if not len(E): return np.empty(0)
        dx, dy = bx - ax, by - ay
        ex, ey = self.x2[E] - self.x1[E], self.y2[E] - self.y1[E]
        qx, qy = self.x1[E] - ax, self.y1[E] - ay
        den = dx * ey - dy * ex
        ok = np.abs(den) > 1e-14
        den = np.where(ok, den, 1.0)
        t = (qx * ey - qy * ex) / den; u = (qx * dy - qy * dx) / den
        sel = ok & (t > 0.0) & (t < 1.0) & (u >= -1e-12) & (u <= 1.0 + 1e-12)
        return np.unique(t[sel])

class Both:
    """Two plane layers seen as one: class 0 where either has copper, -1 where neither has."""
    def __init__(self, p1, p2): self.p = (p1, p2)
    def cuts(self, ax, ay, bx, by): return np.unique(np.concatenate([p.cuts(ax, ay, bx, by) for p in self.p]))
    def locate(self, px, py):
        z = np.full(len(px), -1)
        for p in self.p: z = np.where(p.locate(px, py) >= 0, 0, z)
        return z

def profile(plane, parts):
    """Length of the straight pieces `parts` [((x0, y0), (x1, y1))] over each class of `plane` (zone index, -1 = no copper)
    and the longest void within one piece."""
    tot = collections.Counter(); longest = 0.0
    for (x0, y0), (x1, y1) in parts:
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-9: continue
        ts = np.concatenate([[0.0], plane.cuts(x0, y0, x1, y1), [1.0]]); tm = 0.5 * (ts[:-1] + ts[1:])
        z = plane.locate(x0 + tm * (x1 - x0), y0 + tm * (y1 - y0)); run = 0.0
        for k in range(len(tm)):
            d = (ts[k + 1] - ts[k]) * L; tot[int(z[k])] += d
            run = run + d if z[k] < 0 else 0.0; longest = max(longest, run)
    return tot, longest

def circle_span(ax, ay, bx, by, cx, cy, r):
    """[s0, s1] within [0, 1] of the segment a -> b that lies inside the circle (c, r), or None."""
    dx, dy = bx - ax, by - ay; fx, fy = ax - cx, ay - cy
    A = dx * dx + dy * dy
    if A <= 0: return None
    B = 2 * (fx * dx + fy * dy); C = fx * fx + fy * fy - r * r
    disc = B * B - 4 * A * C
    if disc <= 0: return None
    sq = math.sqrt(disc); s0, s1 = (-B - sq) / (2 * A), (-B + sq) / (2 * A)
    s0, s1 = max(s0, 0.0), min(s1, 1.0)
    return (s0, s1) if s1 > s0 else None

def complement(spans, lo, hi):
    """Parts of [lo, hi] not covered by spans."""
    out, x = [], lo
    for a, b in sorted(spans):
        a, b = max(a, lo), min(b, hi)
        if b <= a: continue
        if a > x: out.append((x, a))
        x = max(x, b)
    if hi > x: out.append((x, hi))
    return out

def caliper(ring):
    """(longest, narrowest) extent of a ring over 16 directions, mm; the longest is its diameter to within 0.5 %."""
    a = np.asarray(ring, float); th = np.arange(16) * math.pi / 16
    pr = a[:, 0][:, None] * np.cos(th)[None, :] + a[:, 1][:, None] * np.sin(th)[None, :]
    ext = pr.max(axis=0) - pr.min(axis=0)
    return float(ext.max()), float(ext.min())

def ring_gap(r1, r2, reach):
    """Smallest distance between two rings (vertex to edge, both ways) and where, when it is below `reach`; else None."""
    best = None
    for p, q in ((r1, r2), (r2, r1)):
        lo, hi = p.min(axis=0) - reach, p.max(axis=0) + reach
        q2 = np.roll(q, -1, axis=0)
        e = np.nonzero((np.maximum(q[:, 0], q2[:, 0]) >= lo[0]) & (np.minimum(q[:, 0], q2[:, 0]) <= hi[0]) &
                       (np.maximum(q[:, 1], q2[:, 1]) >= lo[1]) & (np.minimum(q[:, 1], q2[:, 1]) <= hi[1]))[0]
        if not len(e): continue
        d = seg_dist(p[:, 0], p[:, 1], q[e, 0], q[e, 1], q2[e, 0], q2[e, 1])
        k = np.unravel_index(np.argmin(d), d.shape)
        if d[k] < reach and (best is None or d[k] < best[0]): best = (float(d[k]), (float(p[k[0], 0]), float(p[k[0], 1])))
    return best

# ---------------------------------------------------------------------------------------------------------- tracks
def join_tracks(tracks, power):
    """Signal segments per layer in mm, each with the numbers of its end nodes (na, nb). Ends of one net on one layer are one
    node when they coincide or lie within JOIN_TOL of each other; a loose end that lies on the copper of a segment it does
    not touch otherwise is joined to it (the segment is cut there). Returns (segments per layer, degree per node, counts of
    what was done)."""
    groups = collections.defaultdict(list); note = collections.Counter()
    for lay, net, x0, y0, x1, y1, w in tracks:
        if not net or net_class(net, power) == 'power': continue
        if (x0, y0) == (x1, y1): note['segments of no length left out'] += 1; continue
        groups[(lay, net)].append((x0, y0, x1, y1, w))
    segs = collections.defaultdict(list); degree = collections.Counter(); base = 0
    for (lay, net), gs in sorted(groups.items()):
        pts = {}
        for g in gs:
            for p in (g[0:2], g[2:4]): pts.setdefault(p, len(pts))
        ia = [pts[g[0:2]] for g in gs]; ib = [pts[g[2:4]] for g in gs]
        par = list(range(len(pts))); deg = collections.Counter(ia + ib); own = collections.defaultdict(set)      # own: node -> segments ending there
        for j in range(len(gs)): own[ia[j]].add(j); own[ib[j]].add(j)
        def find(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        def union(i, j):
            i, j = find(i), find(j)
            if i != j: par[i] = j; deg[j] += deg.pop(i, 0); own[j] |= own.pop(i, set())
        P = np.array(list(pts), float) * NM
        A = np.array([g[0:2] for g in gs], float) * NM; B = np.array([g[2:4] for g in gs], float) * NM; W = np.array([g[4] for g in gs], float) * NM
        d = np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1])
        for i, j in zip(*np.nonzero(np.triu(d <= JOIN_TOL, 1))): union(i, j); note['ends within %g mm of each other made one node' % JOIN_TOL] += 1
        dx, dy = B[:, 0] - A[:, 0], B[:, 1] - A[:, 1]; L = np.hypot(dx, dy)
        t = np.clip(((P[:, None, 0] - A[None, :, 0]) * dx[None, :] + (P[:, None, 1] - A[None, :, 1]) * dy[None, :]) / (L * L)[None, :], 0.0, 1.0)
        off = np.hypot(P[:, None, 0] - (A[None, :, 0] + t * dx[None, :]), P[:, None, 1] - (A[None, :, 1] + t * dy[None, :]))
        cut = collections.defaultdict(list)                # segment -> [(t, loose end that lies on it)]
        for i, j in zip(*np.nonzero(off <= (W / 2)[None, :])):
            n = find(i)
            if deg[n] != 1: continue                       # only a loose end
            (mine,) = own[n]
            if j == mine or mine in own[find(ia[j])] or mine in own[find(ib[j])]: continue      # its own segment, or one it touches anyway
            if t[i, j] * L[j] <= JOIN_TOL: union(n, ia[j])
            elif (1.0 - t[i, j]) * L[j] <= JOIN_TOL: union(n, ib[j])
            else: cut[j].append((float(t[i, j]), i)); deg[n] += 2; own[n].add(j)
            note['loose ends joined to the segment they lie on'] += 1
        new = []
        for j in range(len(gs)):
            stops = [(0.0, ia[j])] + sorted(cut.get(j, [])) + [(1.0, ib[j])]
            for (t0, n0), (t1, n1) in zip(stops, stops[1:]):
                if (t1 - t0) * L[j] <= JOIN_TOL: union(n1, n0); continue
                new.append(dict(net=net, w=float(W[j]), na=n0, nb=n1, a=(A[j, 0] + t0 * dx[j], A[j, 1] + t0 * dy[j]), b=(A[j, 0] + t1 * dx[j], A[j, 1] + t1 * dy[j])))
        for x in new:
            for k in ('na', 'nb'): x[k] = base + find(x[k]); degree[x[k]] += 1
        segs[lay] += new; base += len(pts)
    return segs, degree, note

class Analysis:
    """Runs of signal segments over the classes of a plane: zone index of the copper under the track, -1 no copper, -2 inside
    a pad of the track's own net (pad copper: counted neither as void nor as copper). With `own` (net -> rows of via x, y,
    antipad radius + OWN_TOL, pad radius) the antipads of the track's own vias are taken out of the void runs; with `edges`
    a piece is void when the centreline or either track edge (+-w/2) is over no copper."""
    def __init__(self, plane, segs, own=None, pad_plane=None, edges=False):
        self.plane, self.segs = plane, segs
        offs = (0.0, 1.0, -1.0) if edges else (0.0,)
        seg, t0, t1 = [], [], []
        for i, s in enumerate(segs):
            (ax, ay), (bx, by) = s['a'], s['b']; L = math.hypot(bx - ax, by - ay)
            nx, ny = -(by - ay) / L * s['w'] / 2, (bx - ax) / L * s['w'] / 2
            ts = [np.array([0.0, 1.0])] + [plane.cuts(ax + o * nx, ay + o * ny, bx + o * nx, by + o * ny) for o in offs]
            if pad_plane is not None: ts.append(pad_plane.cuts(ax, ay, bx, by))
            ts = np.unique(np.concatenate(ts)); ts = ts[np.concatenate([[True], np.diff(ts) * L > 1e-7])]; ts[-1] = 1.0
            seg.append(np.full(len(ts) - 1, i)); t0.append(ts[:-1]); t1.append(ts[1:])
        cat = lambda v, typ: np.concatenate(v) if v else np.empty(0, typ)
        seg, t0, t1 = cat(seg, int), cat(t0, float), cat(t1, float)
        A = np.array([s['a'] for s in segs], float).reshape(-1, 2); B = np.array([s['b'] for s in segs], float).reshape(-1, 2)
        hw = np.array([s['w'] / 2 for s in segs], float)
        ax, ay, bx, by = A[seg, 0], A[seg, 1], B[seg, 0], B[seg, 1]; tm = 0.5 * (t0 + t1)
        L = np.hypot(bx - ax, by - ay); nx, ny = -(by - ay) / L * hw[seg], (bx - ax) / L * hw[seg]
        mx, my = ax + tm * (bx - ax), ay + tm * (by - ay)
        cls = plane.locate(mx, my)
        for o in offs[1:]: cls = np.where(plane.locate(mx + o * nx, my + o * ny) < 0, -1, cls)
        if pad_plane is not None and len(seg):
            pnet = np.array([z['net'] for z in pad_plane.zones] + [None], object)       # index -1 (no pad) -> None
            cls = np.where(pnet[pad_plane.locate(mx, my)] == np.array([segs[k]['net'] for k in seg], object), -2, cls)
        pieces = []                                    # [segment, t0, t1, class], consecutive pieces of one class joined
        for k in range(len(seg)):
            if pieces and pieces[-1][0] == seg[k] and pieces[-1][3] == cls[k] and abs(pieces[-1][2] - t0[k]) < 1e-12: pieces[-1][2] = float(t1[k])
            else: pieces.append([int(seg[k]), float(t0[k]), float(t1[k]), int(cls[k])])
        self.pieces = pieces
        par = list(range(len(pieces)))                 # union-find: pieces of one class that meet at a node are one run
        def find(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        at_node = collections.defaultdict(list)
        for k, (si, a, b, z) in enumerate(pieces):
            if a == 0.0: at_node[segs[si]['na']].append(k)
            if b == 1.0: at_node[segs[si]['nb']].append(k)
        self.at_node = at_node
        adj = set()
        for ks in at_node.values():
            for i in ks:
                for j in ks:
                    if i < j:
                        if pieces[i][3] == pieces[j][3]: par[find(i)] = find(j)
                        else: adj.add((i, j))
        for k in range(len(pieces) - 1):
            if pieces[k][0] == pieces[k + 1][0]: adj.add((k, k + 1))
        groups = collections.defaultdict(list)
        for k in range(len(pieces)): groups[find(k)].append(k)
        self.runs = []; rid = {}
        for root, ks in groups.items():
            rid[root] = len(self.runs)
            self.runs.append(dict(net=segs[pieces[ks[0]][0]]['net'], zone=pieces[ks[0]][3], pieces=ks, neighbours=set()))
        for i, j in adj:
            ri, rj = rid[find(i)], rid[find(j)]
            if ri != rj: self.runs[ri]['neighbours'].add(rj); self.runs[rj]['neighbours'].add(ri)
        for r in self.runs:
            tot, excess, subs, vias, xs, ys = 0.0, 0.0, [], set(), [], []
            for k in r['pieces']:
                pa, pb = self.ends(k); lp = math.hypot(pb[0] - pa[0], pb[1] - pa[1]); tot += lp
                xs += [pa[0], pb[0]]; ys += [pa[1], pb[1]]
                if r['zone'] != -1: continue
                spans = []; V = own.get(r['net']) if own else None
                if V is not None and len(V):
                    reach = float(V[:, 2].max())
                    near = V[(V[:, 0] >= min(pa[0], pb[0]) - reach) & (V[:, 0] <= max(pa[0], pb[0]) + reach) &
                             (V[:, 1] >= min(pa[1], pb[1]) - reach) & (V[:, 1] <= max(pa[1], pb[1]) + reach)]
                    for cx, cy, rr, rp in near:
                        sp = circle_span(pa[0], pa[1], pb[0], pb[1], cx, cy, rr)
                        if sp: spans.append(sp)
                        if circle_span(pa[0], pa[1], pb[0], pb[1], cx, cy, rp + segs[pieces[k][0]]['w'] / 2): vias.add((float(cx), float(cy), float(rr - OWN_TOL)))
                for c0, c1 in complement(spans, 0.0, 1.0):
                    q0 = (pa[0] + c0 * (pb[0] - pa[0]), pa[1] + c0 * (pb[1] - pa[1])); q1 = (pa[0] + c1 * (pb[0] - pa[0]), pa[1] + c1 * (pb[1] - pa[1]))
                    excess += (c1 - c0) * lp; subs.append((q0, q1))
            r['length'] = tot; r['excess'] = excess; r['subs'] = subs; r['vias'] = vias
            # where: the middle of the longest counted part (void) or of the longest piece
            q0, q1 = max(subs or [self.ends(k) for k in r['pieces']], key=lambda q: math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]))
            r['at'] = (0.5 * (q0[0] + q1[0]), 0.5 * (q0[1] + q1[1])); r['bbox'] = (min(xs), min(ys), max(xs), max(ys))

    def ends(self, k):
        si, a, b, z = self.pieces[k]; (ax, ay), (bx, by) = self.segs[si]['a'], self.segs[si]['b']
        return (ax + a * (bx - ax), ay + a * (by - ay)), (ax + b * (bx - ax), ay + b * (by - ay))

    def parts(self, r):
        return [self.ends(k) for k in r['pieces']]

    def piece_nodes(self, k):
        si, a, b, z = self.pieces[k]
        return ([self.segs[si]['na']] if a == 0.0 else []) + ([self.segs[si]['nb']] if b == 1.0 else [])

    def changes(self):
        """Every place where the class under the track changes: (x, y, classes that meet there, net)."""
        out = []
        for k in range(len(self.pieces) - 1):
            if self.pieces[k][0] == self.pieces[k + 1][0]:
                out.append(self.ends(k)[1] + ((self.pieces[k][3], self.pieces[k + 1][3]), self.segs[self.pieces[k][0]]['net']))
        for node, ks in self.at_node.items():
            cl = tuple(sorted(set(self.pieces[k][3] for k in ks)))
            if len(cl) > 1:
                si, a, b, z = self.pieces[ks[0]]
                out.append(self.ends(ks[0])[0 if a == 0.0 and self.segs[si]['na'] == node else 1] + (cl, self.segs[si]['net']))
        return out

class Causes:
    """Why a plane layer has no copper at a point: rule areas, plane outline, islands, other vias, holes, board edge."""
    def __init__(self, B, layer, P):
        clr = P['clearance']
        self.rules = [(r['name'], [ring for poly in r['outline'] for ring in poly]) for r in B['rules'] if layer in r['layers'] and r['pour']]
        self.ref_rings = [ring for poly in P['base']['outline'] for ring in poly]
        self.ref_ymax = max(p[1] for ring in self.ref_rings for p in ring)
        self.islands = [(z['label'], [ring for poly in z['outline'] for ring in poly]) for z in P['zones'] if z is not P['base']]
        self.island_edges = [(lab, ring_edges(rings)) for lab, rings in self.islands]
        V = [v for v in B['vias'] if layer in v['span']]
        self.v_xy = np.array([(v['x'], v['y']) for v in V], float).reshape(-1, 2)
        self.v_r = np.array([v['d'] / 2 for v in V], float); self.v_net = [v['net'] for v in V]
        self.pads = [p for p in B['pads'] if layer in p['layers'] or p['attr'] == 'npth']
        self.clr = clr; self.edge = np.array(B['edges'], float).reshape(-1, 4)
        self.edge_clr, self.hole_clr = B['edge_clearance'], B['hole_clearance']

    def explain(self, subs, net):
        px, py = sample_parts(subs)
        return self.explain_pts(px, py, net)

    def explain_pts(self, px, py, net):
        """{cause: number of points, or [(net, vias)] for antipads} for void points px, py (mm) under a track of `net`."""
        if not len(px): return {}
        res = collections.OrderedDict(); claimed = np.zeros(len(px), bool)
        for name, rings in self.rules:
            ins = pip_small(px, py, rings)
            if ins.any(): res['rule area ' + name] = int(ins.sum()); claimed |= ins
        out = ~pip_small(px, py, self.ref_rings)
        low = out & (py > self.ref_ymax - 1e-6)
        if low.any(): res['beyond the plane edge on the card-edge side (tab)'] = int(low.sum())
        if (out & ~low).any(): res['outside the plane outline'] = int((out & ~low).sum())
        claimed |= out
        for lab, (ex1, ey1, ex2, ey2) in self.island_edges:
            near = (seg_dist(px, py, ex1, ey1, ex2, ey2).min(axis=1) <= self.clr + CAUSE_PAD) & ~claimed
            if near.any(): res['clearance ring of ' + lab] = int(near.sum()); claimed |= near
        if len(self.v_xy):
            d = np.hypot(px[:, None] - self.v_xy[None, :, 0], py[:, None] - self.v_xy[None, :, 1])
            hit = (d <= (self.v_r + self.clr + CAUSE_PAD)[None, :]) & np.array([n != net for n in self.v_net])[None, :]
            ids = np.nonzero(hit.any(axis=0))[0]
            if len(ids):
                res['antipads of %d vias' % len(ids)] = collections.Counter(self.v_net[i] for i in ids).most_common()
                claimed |= hit.any(axis=1)
        for lab, rings in self.islands:
            ins = pip_small(px, py, rings) & ~claimed
            if ins.any(): res['unfilled part of ' + lab] = int(ins.sum()); claimed |= ins
        for p in self.pads:
            x0, y0, x1, y1 = p['bbox']; g = (self.hole_clr if p['attr'] == 'npth' else self.clr) + CAUSE_PAD
            near = (px >= x0 - g) & (px <= x1 + g) & (py >= y0 - g) & (py <= y1 + g)
            if near.any() and p['net'] != net:
                res['%s %s.%s' % ('hole' if p['attr'] == 'npth' else 'pad', p['ref'], p['num'])] = int(near.sum()); claimed |= near
        if len(self.edge):
            near = (seg_dist(px, py, self.edge[:, 0], self.edge[:, 1], self.edge[:, 2], self.edge[:, 3]).min(axis=1) <= self.edge_clr + CAUSE_PAD) & ~claimed
            if near.any(): res['board edge'] = int(near.sum()); claimed |= near
        if (~claimed).any(): res['other (copper removed: minimum width / island removal)'] = int((~claimed).sum())
        return res

def cause_text(c):
    out = []
    for k, v in c.items():
        if isinstance(v, list): out.append('%s (%s%s)' % (k, ', '.join('%s%s' % (n, ' x%d' % m if m > 1 else '') for n, m in v[:4]), ', ...' if len(v) > 4 else ''))
        else: out.append(k)
    return '; '.join(out)

# ---------------------------------------------------------------------------------------------------------- the board model
def prepare(data):
    """The board in mm: zone and rule outlines, vias with the layers they pass, pads, board edge."""
    order = data['order']; mm = lambda v: v * NM
    B = dict(order=order, edge_clearance=mm(data['edge_clearance']), hole_clearance=mm(data['hole_clearance']))
    B['fps'] = [dict(ref=f['ref'], x=mm(f['x']), y=mm(f['y'])) for f in data['fps']]
    for z in data['zones'] + data['rules']: z['outline'] = [[[(mm(x), mm(y)) for x, y in ring] for ring in poly] for poly in z['polys']]
    B['zones'], B['rules'] = data['zones'], data['rules']
    B['vias'] = []
    for v in data['vias']:
        i0, i1 = sorted((order.index(v['top']), order.index(v['bot']))) if v['top'] in order and v['bot'] in order else (0, len(order) - 1)
        B['vias'].append(dict(x=mm(v['x']), y=mm(v['y']), d=mm(v['d']), net=v['net'], span=set(order[i0:i1 + 1]), key=(v['x'], v['y'], v['net'])))
    B['pads'] = [dict(p, bbox=tuple(mm(c) for c in p['bbox'])) for p in data['pads']]
    B['edges'] = [tuple(mm(c) for c in e) for e in data['edges']]
    return B

def zone_label(z, fps):
    """A zone by the IC it serves: an IC (U<n>) inside its outline, else the IC whose centre is within 3 mm of the outline's
    box centre (the U-shaped core islands go round the QFN centre), else the parts inside it."""
    rings = [ring for poly in z['outline'] for ring in poly]
    refs = [f['ref'] for f in fps if pip_small([f['x']], [f['y']], rings)[0]]
    us = sorted(r for r in refs if re.fullmatch(r'U\d+', r))
    if us: return '%s %s' % (z['net'], '/'.join(us))
    xs = [p[0] for p in rings[0]]; ys = [p[1] for p in rings[0]]; cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    near = sorted((math.hypot(f['x'] - cx, f['y'] - cy), f['ref']) for f in fps if re.fullmatch(r'U\d+', f['ref']))
    if near and near[0][0] <= 3.0: return '%s %s' % (z['net'], near[0][1])
    return '%s at %s' % (z['net'], '/'.join(sorted(refs)[:3]) if refs else 'zone %d' % z['index'])

def make_planes(B, fill, plane_layers):
    """Per plane layer: its zones with their filled copper (mm), the board-wide zone ('base'), the islands, a Plane of the
    copper and one of the island outlines."""
    mm = lambda v: v * NM; planes = {}
    by_idx = {z['index']: z for z in B['zones']}
    for pl in plane_layers:
        zs = []
        for fz in fill['zones']:
            if fz['layer'] != pl: continue
            z = by_idx[fz['index']]
            zs.append(dict(index=z['index'], net=z['net'], priority=z['priority'], clearance=mm(z['clearance']), min_width=mm(z['min_width']), outline=z['outline'],
                           fill=[[[(mm(x), mm(y)) for x, y in ring] for ring in poly] for poly in fz['polys']]))
        base = max(zs, key=lambda z: (ring_area(z['outline'][0][0]), -z['priority']))      # the board-wide zone; the others are islands
        for z in zs:
            z['label'] = '%s plane' % z['net'] if z is base else zone_label(z, B['fps'])
            xs = [p[0] for poly in z['outline'] for p in poly[0]]; ys = [p[1] for poly in z['outline'] for p in poly[0]]
            z['box'] = (min(xs), min(ys), max(xs), max(ys))
        islands = [z for z in zs if z is not base]
        planes[pl] = dict(zones=zs, base=base, islands=islands, clearance=max(z['clearance'] for z in zs), plane=Plane(zs),
                          outlines=Plane([dict(net=z['net'], priority=z['priority'], fill=z['outline']) for z in islands]),
                          base_only=Plane([base]), multi=len(set(z['net'] for z in zs)) > 1)
    return planes

def own_vias(B, pl, clr):
    """net -> rows (x, y, antipad radius + OWN_TOL, pad radius) of its vias that pass plane layer pl."""
    d = collections.defaultdict(list)
    for v in B['vias']:
        if pl in v['span']: d[v['net']].append((v['x'], v['y'], v['d'] / 2 + clr + OWN_TOL, v['d'] / 2))
    return {n: np.array(v, float) for n, v in d.items()}

def sample_parts(parts, step=SAMPLE):
    """Points every `step` mm (cell centres) along straight pieces [((x0, y0), (x1, y1))]: two arrays."""
    pts = []
    for (x0, y0), (x1, y1) in parts:
        n = max(1, int(math.ceil(math.hypot(x1 - x0, y1 - y0) / step)))
        t = (np.arange(n) + 0.5) / n; pts.append(np.stack([x0 + t * (x1 - x0), y0 + t * (y1 - y0)], axis=1))
    P = np.concatenate(pts) if pts else np.empty((0, 2))
    return P[:, 0], P[:, 1]

def study(B, planes, s, pl, sec, segs, pad_plane, power, min_void, edges=False):
    """Signal layer s over its reference plane layer pl; sec is the plane on the other side of s (or the next plane
    beyond pl), measured along every stretch, or None. Per net: length, class lengths, void runs with their causes,
    stretches off the board-wide zone of pl and the length with copper on neither pl nor sec; with islands on pl also the
    island runs, the net changes and the island-edge crossings. With `edges`: the void runs only, a piece being void
    when the centreline or either track edge (+-w/2) is over no copper."""
    P = planes[pl]; Z = P['zones']; ref_net = P['base']['net']; multi = P['multi'] and not edges
    own = own_vias(B, pl, P['clearance'])
    an = Analysis(P['plane'], segs, own, pad_plane, edges)
    secp = planes[sec]['plane'] if sec else None
    C = Causes(B, pl, P)
    def under(parts):
        """(mm without copper on sec, longest such piece) along parts, or None without sec."""
        if secp is None: return None
        tot, longest = profile(secp, parts); return (tot[-1], longest)
    recs = collections.defaultdict(lambda: dict(cls=None, length=0.0, raw=collections.Counter(), crossings=[], island_runs=[], void_runs=[],
                                                edge_x=0, edge_by=collections.Counter(), stretches=[], noref=0.0, noref_longest=None))
    for x in segs: recs[x['net']]['length'] += math.hypot(x['b'][0] - x['a'][0], x['b'][1] - x['a'][1])
    for n in recs: recs[n]['cls'] = net_class(n, power)
    ring = collections.defaultdict(list); bare = 0     # void run -> [(via, copper counted on the rings round it)]
    jobs = [(ri, v) for ri, r in enumerate(an.runs) if multi and r['zone'] == -1 for v in sorted(r['vias'])]
    if jobs:
        ang = np.arange(RING_N) * (2 * math.pi / RING_N)
        px = np.concatenate([v[0] + (v[2] + d) * np.cos(ang) for _, v in jobs for d in RINGS])
        py = np.concatenate([v[1] + (v[2] + d) * np.sin(ang) for _, v in jobs for d in RINGS])
        for (ri, v), row in zip(jobs, P['plane'].locate(px, py).reshape(len(jobs), -1)):
            ring[ri].append((v, collections.Counter(int(c) for c in row if c >= 0)))
    for ri, r in enumerate(an.runs):
        rec = recs[r['net']]; seg0 = an.pieces[r['pieces'][0]][0]
        rec['raw'][Z[r['zone']]['label'] if r['zone'] >= 0 else ('void' if r['zone'] == -1 else 'own pad')] += r['length']
        if r['zone'] == -2: continue
        if r['zone'] >= 0:
            z = Z[r['zone']]
            if z['net'] != ref_net: rec['island_runs'].append(dict(length=r['length'], label=z['label'], at=r['at'], bbox=r['bbox'], under=under(an.parts(r))))
            for nb in r['neighbours'] if multi else ():     # copper of two nets touching with no gap between: a net change too
                q = an.runs[nb]
                if q['zone'] >= 0 and nb > ri and Z[q['zone']]['net'] != z['net']:
                    rec['crossings'].append(dict(between=sorted([z['label'], Z[q['zone']]['label']]), at=r['at'], gap=0.0, via=None, under=None, seg=seg0))
            continue
        if multi:
            nb_z = set(an.runs[nb]['zone'] for nb in r['neighbours'] if an.runs[nb]['zone'] >= 0)
            real = set(Z[z]['net'] for z in nb_z); virt = {}
            for v, cnt in ring.get(ri, []):
                if sum(cnt.values()) < RING_MIN: bare += 1; continue
                virt[cnt.most_common(1)[0][0]] = dict(at=v[:2], copper={Z[z]['label']: c for z, c in cnt.most_common()}, points=len(RINGS) * RING_N)
            nets = real | set(Z[z]['net'] for z in virt)
            ncross = len(nets) - 1 if len(nets) > 1 else 0
            at_via = ncross - max(len(real) - 1, 0)    # net changes that exist only through the copper round a via of the track
            for i in range(ncross):
                rec['crossings'].append(dict(between=sorted(set(Z[z]['label'] for z in nb_z | set(virt))), at=r['at'], gap=r['excess'],
                                             via=(list(virt.values()) if i >= ncross - at_via else None), under=under(r['subs']), seg=seg0))
        else: ncross = 0
        if r['excess'] > 1e-6:
            terminal = any(len(an.at_node[n]) <= 1 for k in r['pieces'] for n in an.piece_nodes(k)) or any(an.runs[nb]['zone'] == -2 for nb in r['neighbours'])
            rec['void_runs'].append(dict(length=r['excess'], raw=r['length'], at=r['at'], bbox=r['bbox'], terminal=terminal,
                                         cause=C.explain(r['subs'], r['net']), crossing=ncross > 0, under=under(r['subs'])))
    out = dict(layer=s, reference=pl, other=sec, multi=P['multi'], nets=recs, analysis=an, bare_vias=bare, ring_vias=len(jobs))
    if not edges:
        if multi:
            isl = P['islands']
            ax = Analysis(P['outlines'], segs)         # the drawn island outlines: edge crossings, length inside each
            out['edge_x'] = collections.Counter(); out['inside'] = collections.Counter(); out['edge_at'] = []
            for x, y, cl, net in ax.changes():
                for c in cl:
                    if c < 0: continue
                    recs[net]['edge_x'] += 1; recs[net]['edge_by'][isl[c]['label']] += 1
                    out['edge_x'][(isl[c]['label'], recs[net]['cls'] != 'slow')] += 1; out['edge_at'].append((x, y, recs[net]['cls'] != 'slow'))
            for r in ax.runs:
                if r['zone'] >= 0: out['inside'][(isl[r['zone']]['label'], recs[r['net']]['cls'] != 'slow')] += r['length']
        st_an = Analysis(P['base_only'], segs, own, pad_plane) if multi else an     # stretches: runs off the board-wide zone
        for r in st_an.runs:
            if r['zone'] != -1 or r['excess'] <= 1e-6: continue
            comp = collections.Counter()
            if multi:
                tot, _ = profile(P['plane'], r['subs'])
                for zi, L in tot.items(): comp['void' if zi < 0 else Z[zi]['label']] += L
            else: comp['void'] = r['excess']
            island = sum(L for k, L in comp.items() if k != 'void')
            if island > 1e-6 or r['excess'] > min_void:
                px, py = sample_parts(r['subs']); void = P['plane'].locate(px, py) < 0
                recs[r['net']]['stretches'].append(dict(length=r['excess'], island=island, void=comp['void'], over=dict(comp), at=r['at'], bbox=r['bbox'],
                                                        under=under(r['subs']), cause=C.explain_pts(px[void], py[void], r['net'])))
        if secp is not None:
            for r in Analysis(Both(P['plane'], secp), segs, own, pad_plane).runs:          # copper on neither plane
                if r['zone'] != -1 or r['excess'] <= 1e-6: continue
                rec = recs[r['net']]; rec['noref'] += r['excess']
                if rec['noref_longest'] is None or r['excess'] > rec['noref_longest'][0]: rec['noref_longest'] = (r['excess'], r['at'])
    for rec in recs.values():
        for k in ('void_runs', 'island_runs', 'stretches'): rec[k].sort(key=lambda v: -v['length'])
    return out

def net_change_floor(res, plane, segs, own, pad_plane):
    """Self-check of the net changes on a layer over a plane with islands: every connected piece of track of one net that
    touches copper of k nets of the plane (sampled every CHECK_STEP mm, plus the copper on the rings round each via of its
    net, judged as in study()) must have at least k - 1 net changes. Returns the pieces that have fewer."""
    an = res['analysis']; Z = plane['zones']; par = {}
    def find(i):
        par.setdefault(i, i)
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for x in segs: par[find(x['na'])] = find(x['nb'])
    touched = collections.defaultdict(set); have = collections.Counter()
    px, py = sample_parts([(x['a'], x['b']) for x in segs], CHECK_STEP)
    n = np.array([max(1, int(math.ceil(math.hypot(x['b'][0] - x['a'][0], x['b'][1] - x['a'][1]) / CHECK_STEP))) for x in segs], int)
    si = np.repeat(np.arange(len(segs)), n); z = plane['plane'].locate(px, py)
    if pad_plane is not None:
        pnet = np.array([q['net'] for q in pad_plane.zones] + [None], object)
        z = np.where(pnet[pad_plane.locate(px, py)] == np.array([x['net'] for x in segs], object)[si], -1, z)
    for k in np.nonzero(z >= 0)[0]: touched[find(segs[si[k]]['na'])].add(Z[z[k]]['net'])
    ang = np.arange(RING_N) * (2 * math.pi / RING_N)
    for i, x in enumerate(segs):
        V = own.get(x['net'])
        if V is None: continue
        for p in (x['a'], x['b']):
            for vx, vy, rr, rp in V[np.hypot(V[:, 0] - p[0], V[:, 1] - p[1]) <= V[:, 3] + x['w'] / 2]:
                q = plane['plane'].locate(np.concatenate([vx + (rr + d) * np.cos(ang) for d in RINGS]), np.concatenate([vy + (rr + d) * np.sin(ang) for d in RINGS]))
                cnt = collections.Counter(int(c) for c in q if c >= 0)
                if sum(cnt.values()) >= RING_MIN: touched[find(x['na'])].add(Z[cnt.most_common(1)[0][0]]['net'])
    for rec in res['nets'].values():
        for c in rec['crossings']: have[find(segs[c['seg']]['na'])] += 1
    return [(segs[next(i for i, x in enumerate(segs) if find(x['na']) == comp)]['net'], sorted(nets), have[comp])
            for comp, nets in touched.items() if have[comp] < len(nets) - 1]

def stitching_vias(data, plane_nets, old=None):
    """The stitching vias (stitch_gnd.py) as keys (x, y, net) in nm: with `old` (the via keys of the board before them)
    the vias of a plane net that board does not have; else the vias of a plane net at which no track of their net ends
    and that lie in no pad of their net (they join copper through the zones only)."""
    if old is not None: return set((v['x'], v['y'], v['net']) for v in data['vias'] if v['net'] in plane_nets and (v['x'], v['y'], v['net']) not in old)
    E = collections.defaultdict(list); Pd = collections.defaultdict(list); out = set()
    for lay, net, x0, y0, x1, y1, w in data['tracks']: E[net] += [(x0, y0), (x1, y1)]
    for p in data['pads']: Pd[p['net']].append(p['bbox'])
    E = {n: np.array(v, float) for n, v in E.items()}
    for v in data['vias']:
        if v['net'] not in plane_nets: continue
        r = v['d'] / 2; e = E.get(v['net'])
        if e is not None and (np.hypot(e[:, 0] - v['x'], e[:, 1] - v['y']) <= r).any(): continue
        if any(x0 - r <= v['x'] <= x1 + r and y0 - r <= v['y'] <= y1 + r for x0, y0, x1, y1 in Pd.get(v['net'], ())): continue
        out.add((v['x'], v['y'], v['net']))
    return out

def read_vias(path):
    """{(x, y, net)} in nm of every via of a board (--before); the board is only read."""
    import pcbnew
    return {(t.GetPosition().x, t.GetPosition().y, str(t.GetNetname())) for t in pcbnew.LoadBoard(path).GetTracks() if t.GetClass() == 'PCB_VIA'}

def cut_off(fill, kept, plane_layers, by_idx):
    """Copper that island removal took off the plane layers: the pieces of the fill made with island removal off that
    the normal fill does not have. Returns ({layer: [(zone net, area mm2, (x, y) mm, outline in mm)]}, pieces of the
    normal fill not found in the other one)."""
    def pieces(f, pl):
        out = []
        for fz in f['zones']:
            if fz['layer'] != pl: continue
            for poly in fz['polys']:
                r = [[(x * NM, y * NM) for x, y in ring] for ring in poly]; xs = [p[0] for p in r[0]]; ys = [p[1] for p in r[0]]
                out.append((fz['index'], poly_area(r), (min(xs), min(ys), max(xs), max(ys)), r))
        return out
    res, lost = {}, 0
    for pl in plane_layers:
        a, b = pieces(fill, pl), pieces(kept, pl); used = set()
        for zi, ar, bb, _ in a:
            k = next((k for k, (zj, br, bb2, _) in enumerate(b) if k not in used and zj == zi and abs(br - ar) < 1e-3 and max(abs(u - v) for u, v in zip(bb, bb2)) < 1e-3), None)
            if k is None: lost += 1
            else: used.add(k)
        res[pl] = [(by_idx[zi]['net'], ar, ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2), r) for k, (zi, ar, bb, r) in enumerate(b) if k not in used]
    return res, lost

def layer_changes(B, segs_by_layer, ref_net_of, shared_of, pads, power):
    """Every via where a signal net changes layer: the layers its tracks end on there, the reference-plane nets of those
    layers, the distance to the nearest via of a plane net that lies next to every one of those layers (shared_of: layer
    -> nets of the planes on both its sides; the return current's way between two planes of one net) and to the nearest
    capacitor between two different reference nets (its way between planes of two nets)."""
    by_net = collections.defaultdict(list)
    for i, v in enumerate(B['vias']): by_net[v['net']].append(i)
    VA = {n: np.array([(B['vias'][i]['x'], B['vias'][i]['y'], B['vias'][i]['d'] / 2) for i in idx]) for n, idx in by_net.items()}
    lay_at = collections.defaultdict(set)
    for l, ss in segs_by_layer.items():
        for x in ss:
            V = VA.get(x['net'])
            if V is None: continue
            for p in (x['a'], x['b']):
                d = np.hypot(V[:, 0] - p[0], V[:, 1] - p[1]); k = int(np.argmin(d))
                if d[k] <= V[k, 2] + JOIN_TOL: lay_at[by_net[x['net']][k]].add(l)
    nets = set(ref_net_of.values())
    caps = collections.defaultdict(list)                 # (net, net) -> pad centres of the capacitors between them
    fp_pads = collections.defaultdict(list)
    for p in pads: fp_pads[p['ref']].append(p)
    for ref, ps in fp_pads.items():
        pn = set(p['net'] for p in ps)
        if re.fullmatch(r'C\d+', ref) and len(pn) == 2 and pn <= nets:
            caps[tuple(sorted(pn))] += [((p['bbox'][0] + p['bbox'][2]) / 2, (p['bbox'][1] + p['bbox'][3]) / 2) for p in ps]
    caps = {k: np.array(v) for k, v in caps.items()}
    out = []
    for i, ls in lay_at.items():
        if len(ls) < 2: continue
        v = B['vias'][i]; refs = sorted(set(ref_net_of[l] for l in ls)); common = sorted(set.intersection(*(set(shared_of[l]) for l in ls)))
        near = {n: float(np.hypot(VA[n][:, 0] - v['x'], VA[n][:, 1] - v['y']).min()) if n in VA else None for n in common}
        cap = None
        if len(refs) == 2 and tuple(refs) in caps: cap = float(np.hypot(caps[tuple(refs)][:, 0] - v['x'], caps[tuple(refs)][:, 1] - v['y']).min())
        out.append(dict(net=v['net'], cls=net_class(v['net'], power), at=(v['x'], v['y']), layers=sorted(ls, key=B['order'].index), refs=refs, via=near, cap=cap))
    return out, {k: len(v) // 2 for k, v in caps.items()}

def hole_contents(ring, B, layer):
    """What a hole of a plane fill with no via inside is made by: pads or holes inside it, rule areas over it."""
    r = np.asarray(ring, float); what = []
    for p in B['pads']:
        if layer not in p['layers'] and p['attr'] != 'npth': continue
        cx, cy = (p['bbox'][0] + p['bbox'][2]) / 2, (p['bbox'][1] + p['bbox'][3]) / 2
        if pip_small([cx], [cy], [r])[0]: what.append('%s %s%s' % ('hole' if p['attr'] == 'npth' else 'pad', p['ref'], '.' + p['num'] if p['num'] else ''))
    for ra in B['rules']:
        if layer not in ra['layers'] or not ra['pour']: continue
        rings = [ring_ for poly in ra['outline'] for ring_ in poly]
        if any(pip_small([q[0] for q in rr], [q[1] for q in rr], [r]).any() for rr in rings) or pip_small([r[0, 0]], [r[0, 1]], rings)[0]: what.append('rule area ' + ra['name'])
    return ', '.join(what[:4]) + (' ...' if len(what) > 4 else '') if what else 'other (no via, pad or rule area inside)'

def integrity(P, vias, B, layer, slot, reach):
    """The copper of one plane layer: pieces per zone, every hole (what it is, how long), and the webs between two rings of
    one piece that are narrower than `reach`."""
    res = dict(zones=[], holes=[], webs=[])
    V = np.array([(v['x'], v['y']) for v in vias], float).reshape(-1, 2)
    over = P['plane'].locate(V[:, 0], V[:, 1]) if len(V) else np.empty(0, int)       # -1: the via has an antipad on this layer
    for z in P['zones']:
        res['zones'].append(dict(label=z['label'], net=z['net'], pieces=sorted((poly_area(p) for p in z['fill']), reverse=True)))
        for pi, poly in enumerate(z['fill']):
            rings = [np.asarray(r, float) for r in poly]
            bb = np.array([np.concatenate([r.min(axis=0), r.max(axis=0)]) for r in rings])
            first = len(res['holes'])
            for hi, r in enumerate(rings[1:], 1):
                inside = [i for i in np.nonzero((V[:, 0] >= bb[hi, 0]) & (V[:, 0] <= bb[hi, 2]) & (V[:, 1] >= bb[hi, 1]) & (V[:, 1] <= bb[hi, 3]))[0]
                          if over[i] < 0 and pip_small([V[i, 0]], [V[i, 1]], [r])[0]] if len(V) else []
                isl = [o['label'] for o in P['zones'] if o is not z and pip_small([o['outline'][0][0][0][0]], [o['outline'][0][0][0][1]], [r])[0]]
                length, width = caliper(r)
                res['holes'].append(dict(zone=z['label'], kind='ring round ' + ', '.join(isl) if isl else ('antipads' if inside else hole_contents(r, B, layer)),
                                         vias=[vias[i]['key'] for i in inside], nets=collections.Counter(vias[i]['net'] for i in inside).most_common(),
                                         length=length, width=width, at=(float(r[:, 0].mean()), float(r[:, 1].mean())), web=None))
            for i in range(len(rings)):
                for j in range(max(i + 1, 1), len(rings)):
                    if i and (max(bb[i, 0], bb[j, 0]) - min(bb[i, 2], bb[j, 2]) > reach or max(bb[i, 1], bb[j, 1]) - min(bb[i, 3], bb[j, 3]) > reach): continue
                    g = ring_gap(rings[j], rings[i], reach)
                    if g is None: continue
                    res['webs'].append(dict(zone=z['label'], width=g[0], at=g[1], holes=[first + k - 1 for k in (i, j) if k]))
                    for k in (i, j):
                        if k and (res['holes'][first + k - 1]['web'] is None or g[0] < res['holes'][first + k - 1]['web']): res['holes'][first + k - 1]['web'] = g[0]
    res['webs'].sort(key=lambda w: w['width'])
    res['slots'] = sorted((h for h in res['holes'] if h['length'] > slot and not h['kind'].startswith('ring')), key=lambda h: -h['length'])
    return res

def plan_crossings(segs_by_layer, pick):
    """Places where a track of another net crosses a track of the nets `pick` in plan view: (net, layer, other net, other
    layer, x, y)."""
    mine = [(l, s) for l, ss in segs_by_layer.items() for s in ss if s['net'] in pick]
    out = []
    for l2, ss in segs_by_layer.items():
        if not ss or not mine: continue
        A = np.array([s['a'] for s in ss], float); Bq = np.array([s['b'] for s in ss], float)
        ex, ey = Bq[:, 0] - A[:, 0], Bq[:, 1] - A[:, 1]
        for l1, m in mine:
            dx, dy = m['b'][0] - m['a'][0], m['b'][1] - m['a'][1]
            qx, qy = A[:, 0] - m['a'][0], A[:, 1] - m['a'][1]
            den = dx * ey - dy * ex; ok = np.abs(den) > 1e-14; den = np.where(ok, den, 1.0)
            t = (qx * ey - qy * ex) / den; u = (qx * dy - qy * dx) / den
            for k in np.nonzero(ok & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1))[0]:
                if ss[k]['net'] not in pick: out.append((m['net'], l1, ss[k]['net'], l2, m['a'][0] + t[k] * dx, m['a'][1] + t[k] * dy))
    return out

# ---------------------------------------------------------------------------------------------------------- SVG
def svg_write(path, bbox, layers):
    """layers: [(kind, items, style)], kind 'poly' (rings in mm), 'line' (x0, y0, x1, y1, w), 'dot' (x, y, r)."""
    x0, y0, x1, y1 = bbox; sc = 10.0 if x1 - x0 > 30 else 60.0
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.2f %.2f %.2f %.2f" width="%d" height="%d" style="background:#fff">'
           % (x0 * sc, y0 * sc, (x1 - x0) * sc, (y1 - y0) * sc, int((x1 - x0) * sc), int((y1 - y0) * sc))]
    for kind, items, style in layers:
        out.append('<g %s>' % style)
        for it in items:
            if kind == 'poly':
                out.append('<path fill-rule="evenodd" d="%s"/>' % ' '.join('M ' + ' L '.join('%.3f %.3f' % (x * sc, y * sc) for x, y in ring) + ' Z' for ring in it))
            elif kind == 'line':
                out.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke-width="%.3f"/>' % (it[0] * sc, it[1] * sc, it[2] * sc, it[3] * sc, it[4] * sc))
            elif kind == 'dot':
                out.append('<circle cx="%.3f" cy="%.3f" r="%.3f"/>' % (it[0] * sc, it[1] * sc, it[2] * sc))
        out.append('</g>')
    out.append('</svg>')
    with open(path, 'w') as f: f.write('\n'.join(out))

# ---------------------------------------------------------------------------------------------------------- main
def class_rows(res, res_e, min_void):
    """Per class (the FAST names, then 'slow'): sums over the nets of one signal layer."""
    rows = collections.OrderedDict((k, collections.Counter()) for k in [f[0] for f in FAST] + ['slow'])
    for n, rec in res['nets'].items():
        t = rows[rec['cls']]; st = [v for v in rec['stretches'] if v['length'] > min_void]
        t['nets'] += 1; t['len'] += rec['length']; t['edge_x'] += rec['edge_x']; t['net_x'] += len(rec['crossings'])
        t['at_via'] += sum(1 for c in rec['crossings'] if c['via']); t['isl'] += sum(v['length'] for v in rec['island_runs'])
        t['void'] += sum(v['length'] for v in rec['void_runs']); t['longv'] += sum(1 for v in rec['void_runs'] if v['length'] > min_void)
        t['st'] += len(st); t['st_mm'] += sum(v['length'] for v in st); t['st_max'] = max(t['st_max'], max([v['length'] for v in st] or [0.0]))
        t['st_open'] += sum(v['under'][0] for v in st if v['under']); t['st_whole'] += sum(1 for v in st if v['under'] and v['under'][0] < 1e-6)
        t['noref'] += rec['noref']
        e = res_e['nets'].get(n)
        t['edge_longv'] += sum(1 for v in e['void_runs'] if v['length'] > min_void) if e else 0
    return rows

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--fill-worker':
        path, out, mode, drc = sys.argv[2:6]
        fill_worker(path, out, mode, None if drc == '-' else drc)
        return 0
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog='The module docstring has method, assumptions and limits.')
    ap.add_argument('board')
    ap.add_argument('--design', default=os.environ.get('FC_DESIGN', 'design_revh'), help='design module in the tools folder (default: FC_DESIGN or design_revh)')
    ap.add_argument('--out', help='folder for everything the tool writes (default: a fresh temporary folder)')
    ap.add_argument('--before', metavar='OLD.kicad_pcb', help='the board before the stitching vias: the plane-net vias it lacks are the stitching vias (default: plane-net vias with no track end and no pad)')
    ap.add_argument('--drc', action='store_true', help="also write KiCad's rule check of the copy (drc.txt)")
    ap.add_argument('--min-void', type=float, default=1.0, help='stretches and void runs longer than this (mm) are listed (default 1.0)')
    ap.add_argument('--slot', type=float, default=3.0, help='holes in a plane longer than this (mm) are listed (default 3.0)')
    ap.add_argument('--web', type=float, default=0.2, help='webs between two holes narrower than this (mm) are listed (default 0.2)')
    ap.add_argument('--all-slow', action='store_true', help='list the slow nets one by one as well')
    ap.add_argument('--stored-fill', action='store_true', help='use the fill stored in the board file instead of filling')
    ap.add_argument('--zoom', action='append', default=[], metavar='X,Y[,W]', help='an extra SVG of W x W mm (default 8) round board point X, Y; may be repeated')
    a = ap.parse_args()
    t_start = time.time()
    out_dir = os.path.abspath(a.out) if a.out else tempfile.mkdtemp(prefix='planes_')
    os.makedirs(out_dir, exist_ok=True)
    sys.path.insert(0, TOOLS)
    D = importlib.import_module(a.design)
    XC, H = D.at(0.0, 0.0)                               # board coordinates of the design origin (centre line, shoulder)
    power = set(D.POWER_NETS)
    def place(x, y): return 'x %.2f y %.2f (x\' %+.2f, h %.2f)' % (x, y, x - XC, H - y)
    def short(l): return l.replace('.Cu', '')

    src = os.path.abspath(a.board)
    board, project = stage(src, os.path.join(out_dir, 'board'))
    data = read_board(board)
    old_vias = read_vias(stage(os.path.abspath(a.before), os.path.join(out_dir, 'before'))[0]) if a.before else None
    fill = run_fill(board, out_dir, 'stored' if a.stored_fill else 'fresh', drc=os.path.join(out_dir, 'drc.txt') if a.drc else None)
    stack = read_stackup(board)
    B = prepare(data); order = B['order']
    lines = []; checks = []; notes = []                  # report lines; self-check results (ok?, text); board-against-design notes
    def pr(*x): lines.append(' '.join(str(v) for v in x))
    def check(ok, text): checks.append((bool(ok), text))
    pr('planes.py: %s' % src)
    pr('  md5 %s, %d bytes; project files copied with it: %s' % (md5_of(src), os.path.getsize(src), ', '.join(project) or 'NONE'))
    pr('  design %s (x\' = x - %g, h = %g - y); outputs in %s' % (a.design, XC, H, out_dir))

    # plane layers: inner copper layers with a zone filled over at least half of the largest zone outline
    zarea = {z['index']: ring_area(z['outline'][0][0]) if z['outline'] and z['outline'][0] else 0.0 for z in B['zones']}
    amax = max(zarea.values() or [0.0])
    filled = collections.defaultdict(set)
    for fz in fill['zones']: filled[fz['layer']].add(fz['index'])
    plane_layers = [l for l in order if l not in (order[0], order[-1]) and any(zarea[i] >= 0.5 * amax for i in filled.get(l, ()))]
    segs_by_layer, degree, joined = join_tracks(data['tracks'], power)
    sig_layers = [l for l in order if segs_by_layer.get(l) and l not in plane_layers]
    if not plane_layers:
        pr('  %d copper layers (%s), no inner plane layer (no inner layer with a zone over half the board): nothing to check on this board' % (len(order), ', '.join(order)))
        return finish(lines, out_dir, 0)
    kept = run_fill(board, out_dir, 'keep-islands')
    pos, zc = {}, 0.0                                     # copper layer -> (z of its top face, z of its bottom face), mm
    for name, typ, th, er in stack:
        if typ == 'copper': pos[name] = (zc, zc + th)
        zc += th if typ in ('copper', 'core', 'prepreg') else 0.0
    def dist(l1, l2):
        """Dielectric between two copper layers (mm); without a stack-up block: the number of layers between them."""
        if l1 not in pos or l2 not in pos: return abs(order.index(l1) - order.index(l2))
        up, lo = sorted((pos[l1], pos[l2])); return lo[0] - up[1]
    def er_between(l1, l2):
        names = [s[0] for s in stack]
        if l1 not in names or l2 not in names: return []
        i0, i1 = sorted((names.index(l1), names.index(l2)))
        return [s[3] for s in stack[i0 + 1:i1] if s[1] in ('core', 'prepreg')]
    ref_of = {s: min(plane_layers, key=lambda p: dist(s, p)) for s in sig_layers}
    sec_of, sec_role = {}, {}                             # the plane on the other side (within 0.5 mm), else the next plane beyond the reference
    for s in sig_layers:
        side = lambda p: (order.index(p) - order.index(s)) * (order.index(ref_of[s]) - order.index(s))
        opp = sorted((p for p in plane_layers if side(p) < 0), key=lambda p: dist(s, p))
        beyond = sorted((p for p in plane_layers if side(p) > 0 and p != ref_of[s]), key=lambda p: dist(s, p))
        if opp and dist(s, opp[0]) < 0.5: sec_of[s], sec_role[s] = opp[0], 'other side'
        elif beyond: sec_of[s], sec_role[s] = beyond[0], 'next plane beyond %s' % short(ref_of[s])
        else: sec_of[s], sec_role[s] = None, None
    planes = make_planes(B, fill, plane_layers)
    pad_planes = {}                                       # pads of every signal layer (a track piece inside a pad of its own net is pad copper)
    for s in sig_layers:
        pz = [dict(net=p['net'], priority=0, fill=[[[(x * NM, y * NM) for x, y in ring] for ring in poly] for poly in p['shape'][s]])
              for p in data['pads'] if s in p['shape'] and p['net']]
        if pz: pad_planes[s] = Plane(pz)
    R = {s: study(B, planes, s, ref_of[s], sec_of[s], segs_by_layer[s], pad_planes.get(s), power, a.min_void) for s in sig_layers}
    RE = {s: study(B, planes, s, ref_of[s], sec_of[s], segs_by_layer[s], pad_planes.get(s), power, a.min_void, True) for s in sig_layers}
    multi = [s for s in sig_layers if R[s]['multi']]
    plane_nets = set(z['net'] for pl in plane_layers for z in planes[pl]['zones'])
    stitch = stitching_vias(data, plane_nets, old_vias)
    reach = max(a.web, 0.5) + 0.1
    integ = {pl: integrity(planes[pl], [v for v in B['vias'] if pl in v['span']], B, pl, a.slot, reach) for pl in plane_layers}
    lost, lost_n = cut_off(fill, kept, plane_layers, {z['index']: z for z in B['zones']})
    fast_names = [f[0] for f in FAST]
    def fast_first(names, recs): return sorted(names, key=lambda n: (recs[n]['cls'] == 'slow', fast_names.index(recs[n]['cls']) if recs[n]['cls'] != 'slow' else 99, n))
    def under_text(u, total, s):
        if u is None: return ''
        return '%s whole under it' % short(sec_of[s]) if u[0] < 1e-6 else '%s open under %.2f of %.2f mm (longest piece %.2f)' % (short(sec_of[s]), u[0], total, u[1])

    # ------------------------------------------------------------------ header: layers, planes, self-check
    for s in sig_layers:
        an = R[s]['analysis']; pl, sec = ref_of[s], sec_of[s]
        pr('  %s -> reference %s (%.4f mm, er %s)%s; %d signal segments, %d nets, %.1f mm' % (s, pl, dist(s, pl), '/'.join('%g' % e for e in er_between(s, pl) if e) or '?',
           (', %s %s (%.4f mm)' % (sec_role[s], sec, dist(s, sec))) if sec else '', len(an.segs), len(R[s]['nets']), sum(rec['length'] for rec in R[s]['nets'].values())))
    joins = {}                                            # plane layer -> zone label -> [(area, vias of its net touching the piece)] per piece
    for pl in plane_layers:
        P = planes[pl]; joins[pl] = {}
        for z in P['zones']:
            V = [v for v in B['vias'] if v['net'] == z['net'] and pl in v['span']]
            per = []
            for poly in z['fill']:
                ex1, ey1, ex2, ey2 = ring_edges(poly); n = 0
                for v in V:
                    if pip_small([v['x']], [v['y']], poly)[0] or seg_dist([v['x']], [v['y']], ex1, ey1, ex2, ey2).min() < v['d'] / 2: n += 1
                per.append((poly_area(poly), n))
            joins[pl][z['label']] = sorted(per, reverse=True)
        pr('  %s: %s' % (pl, '; '.join('%s %s' % (z['label'], ' + '.join('%.1f mm2 (%d via%s of its net)' % (ar, n, '' if n == 1 else 's') for ar, n in joins[pl][z['label']]) or 'NO COPPER') for z in P['zones'])))
    used = collections.Counter(t[0] for t in data['tracks'])
    if any(used.get(l) for l in plane_layers): pr('  note: tracks on plane layers (not checked; they cut the fill): ' + ', '.join('%s %d segments' % (l, used[l]) for l in plane_layers if used.get(l)))
    pr('  fast classes: ' + ', '.join('%s /%s/' % f for f in FAST) + '; power (not checked): ' + ', '.join(sorted(power)) + ', /%s/' % POWER_EXTRA)

    same = sorted(tuple(x[:4]) + (round(x[4], 3),) for x in fill['before']) == sorted(tuple(x[:4]) + (round(x[4], 3),) for x in fill['after'])
    if fill['mode'] == 'fresh': check(same, 'the fill stored in the file equals a fresh fill (outlines, points, area of every zone and layer)' if same else
                                      'the fill stored in the file DIFFERS from a fresh fill: the file was saved unfilled, or its rules (.kicad_pro) are not the ones it was filled with; the report uses the fresh fill')
    else: pr('  fill: the one stored in the file (--stored-fill), not checked against a fresh fill')
    check('.kicad_pro' in project, 'the board has its .kicad_pro (the clearances the zones are filled with)' if '.kicad_pro' in project else
          'NO .kicad_pro next to the board: KiCad fills with its default rules')
    check(lost_n == 0, 'every piece of the plane fill is also in the fill made with island removal off (the cut-off copper below is complete)' if lost_n == 0 else
          '%d pieces of the plane fill are NOT in the fill made with island removal off: the cut-off copper below is not reliable' % lost_n)
    nets_on_board = set(t[1] for t in data['tracks']) | set(p['net'] for p in data['pads'])
    empty = [name for name, pat in FAST if not any(re.fullmatch(pat, n) for n in nets_on_board)]
    check(not empty, 'every fast class matches nets of the board' if not empty else 'fast classes that match NO net of the board (renamed nets?): ' + ', '.join(empty))
    for pl in plane_layers:                                # the antipad the fill really gives a via of another net
        P = planes[pl]; ex1, ey1, ex2, ey2 = ring_edges([ring for z in P['zones'] for poly in z['fill'] for ring in poly])
        nets_pl = set(z['net'] for z in P['zones'])
        V = [v for v in B['vias'] if pl in v['span'] and v['net'] not in nets_pl]
        if not V or not len(ex1): continue
        gap = np.array([seg_dist([v['x']], [v['y']], ex1, ey1, ex2, ey2).min() - v['d'] / 2 for v in V])
        med = float(np.median(gap))
        check(abs(med - P['clearance']) <= 0.02, '%s: antipads as assumed (zone clearance %.3f mm; measured at %d vias of other nets: median %.3f, least %.3f mm)' % (pl, P['clearance'], len(V), med, gap.min())
              if abs(med - P['clearance']) <= 0.02 else '%s: the antipads are NOT pad + zone clearance (%.3f mm): measured median %.3f mm at %d vias; the own-via rule is off by the difference' % (pl, P['clearance'], med, len(V)))
    worst = (0.0, None)                                    # every class length again, by sampling the centreline
    for s in sig_layers:
        an = R[s]['analysis']; P = planes[ref_of[s]]; Z = P['zones']; segs = an.segs
        n = np.array([max(1, int(math.ceil(math.hypot(x['b'][0] - x['a'][0], x['b'][1] - x['a'][1]) / CHECK_STEP))) for x in segs])
        si = np.repeat(np.arange(len(segs)), n); px, py = sample_parts([(x['a'], x['b']) for x in segs], CHECK_STEP)
        A = np.array([x['a'] for x in segs], float); Bq = np.array([x['b'] for x in segs], float)
        z = P['plane'].locate(px, py); step = (np.hypot(Bq[:, 0] - A[:, 0], Bq[:, 1] - A[:, 1]) / n)[si]
        if s in pad_planes:
            pnet = np.array([q['net'] for q in pad_planes[s].zones] + [None], object)
            z = np.where(pnet[pad_planes[s].locate(px, py)] == np.array([x['net'] for x in segs], object)[si], -2, z)
        got = collections.defaultdict(collections.Counter)
        for k in np.unique(z):
            lab = Z[k]['label'] if k >= 0 else ('void' if k == -1 else 'own pad')
            w = np.bincount(si[z == k], weights=step[z == k], minlength=len(segs))
            for i in np.nonzero(w)[0]: got[segs[i]['net']][lab] += w[i]
        npieces = collections.Counter(segs[p[0]]['net'] for p in an.pieces)
        for net, rec in R[s]['nets'].items():
            for lab in set(rec['raw']) | set(got[net]):
                d = abs(rec['raw'][lab] - got[net][lab]) - CHECK_STEP * (1 + 0.5 * npieces[net])
                if d > worst[0]: worst = (d, '%s %s %s: cut %.3f, sampled %.3f mm' % (s, net, lab, rec['raw'][lab], got[net][lab]))
        tot_cut = sum(sum(rec['raw'].values()) for rec in R[s]['nets'].values()); tot_len = sum(rec['length'] for rec in R[s]['nets'].values())
        if abs(tot_cut - tot_len) > 1e-6: worst = (abs(tot_cut - tot_len), '%s: the pieces add up to %.4f mm, the tracks to %.4f mm' % (s, tot_cut, tot_len))
    check(worst[1] is None, 'the exact cuts agree with a re-measurement by sampling every %.2f mm, net by net and class by class; the pieces add up to the track lengths' % CHECK_STEP
          if worst[1] is None else 'the exact cuts DISAGREE with sampling: ' + worst[1])
    isl_rows = {}
    for s in multi:                                        # net changes: a lower bound counted another way, and the rows of the island table
        P = planes[ref_of[s]]
        short_of = net_change_floor(R[s], P, segs_by_layer[s], own_vias(B, ref_of[s], P['clearance']), pad_planes.get(s))
        check(not short_of, '%s: every track piece that touches copper of k nets of %s has at least k - 1 net changes (sampled every %.2f mm, rings round its vias)' % (s, ref_of[s], CHECK_STEP)
              if not short_of else '%s: %d track pieces have FEWER net changes than the nets they touch need (the net-change counts are too low): %s' % (
                  s, len(short_of), '; '.join('%s touches %s, %d changes' % (n, '/'.join(ns), h) for n, ns, h in short_of[:6])))
        recs = R[s]['nets']; rows = collections.OrderedDict()
        for z in P['islands']: rows[z['label']] = dict(zone=z, net_x=collections.Counter(), over=collections.Counter(), nets=collections.defaultdict(lambda: [0, 0.0]))
        shared = collections.defaultdict(collections.Counter)
        for n, rec in recs.items():
            f = rec['cls'] != 'slow'
            for c in rec['crossings']:
                isl = [l for l in c['between'] if l in rows]
                if len(isl) == 1: rows[isl[0]]['net_x'][f] += 1; rows[isl[0]]['nets'][n][0] += 1
                else: shared[' | '.join(isl)][f] += 1
            for v in rec['island_runs']: rows[v['label']]['over'][f] += v['length']; rows[v['label']]['nets'][n][1] += v['length']
        total = sum(len(rec['crossings']) for rec in recs.values())
        listed = sum(sum(r['net_x'].values()) for r in rows.values()) + sum(sum(c.values()) for c in shared.values())
        check(total == listed, '%s: the net changes listed per island add up to the total (%d)' % (s, total) if total == listed else
              '%s: the per-island net changes (%d) do NOT add up to the total (%d)' % (s, listed, total))
        isl_rows[s] = (rows, shared)
    # notes: the board against its design (they do not make the numbers wrong)
    if fill['unconnected']: notes.append('KiCad finds %d unconnected items: the board is not fully routed; the numbers cover the copper that is there' % fill['unconnected'])
    else: notes.append('KiCad finds no unconnected item')
    want = getattr(D, 'PLANES', None)
    if want is not None:
        diff = []
        for pl in sorted(set(want) | set(plane_layers)):
            have = [(z['net'], None if z is planes[pl]['base'] else z['box']) for z in planes[pl]['zones']] if pl in planes else []
            for net, shape in want.get(pl, []):
                box = None if shape == 'board' else tuple(f(p[k] for p in shape) for f in (min, max) for k in (0, 1))
                hit = next((h for h in have if h[0] == net and (h[1] is None) == (box is None) and (box is None or max(abs(u - v) for u, v in zip(h[1], box)) < 0.02)), None)
                if hit is None: diff.append('%s: no %s zone %s' % (pl, net, 'over the board' if box is None else 'at x %.2f-%.2f y %.2f-%.2f' % (box[0], box[2], box[1], box[3])))
                else: have.remove(hit)
            for h in have: diff.append('%s: a %s zone the design does not have' % (pl, h[0]))
        dc = collections.Counter(diff)
        notes.append('the zones of the plane layers are the design\'s PLANES (net and box of every zone)' if not diff else
                     'the zones of the plane layers DIFFER from the design\'s PLANES: %s' % '; '.join('%s%s' % (k, ' (x%d)' % m if m > 1 else '') for k, m in dc.items()))
    widths = collections.Counter(round(x['w'], 4) for ss in segs_by_layer.values() for x in ss)
    nc = data['netclass']; wmain = widths.most_common(1)[0][0] if widths else nc['track']
    rules_ok = all(not hasattr(D, k) or abs(getattr(D, k) - v) < 1e-6 for k, v in (('TRACK', nc['track']), ('TRACK', wmain), ('CLEAR', nc['clearance']), ('VIA_DIA', nc['via'])))
    notes.append(('track %.2f / clearance %.2f / via %.2f mm: the design, the board\'s rules and its commonest signal track agree' % (nc['track'], nc['clearance'], nc['via'])) if rules_ok else
                 'design TRACK / CLEAR / VIA_DIA %s, the board\'s rules %s and its commonest signal track %s mm DIFFER' % (
                     [getattr(D, k, None) for k in ('TRACK', 'CLEAR', 'VIA_DIA')], [round(nc[k], 4) for k in ('track', 'clearance', 'via')], wmain))
    loose = []                                             # track ends that are neither at a via nor in a pad of their net nor on another track
    for s in sig_layers:
        vs = collections.defaultdict(list)
        for v in B['vias']:
            if s in v['span']: vs[v['net']].append((v['x'], v['y'], v['d'] / 2))
        for x in segs_by_layer[s]:
            for nk, p in ((x['na'], x['a']), (x['nb'], x['b'])):
                if degree[nk] != 1: continue
                if any(math.hypot(p[0] - vx, p[1] - vy) <= vr + x['w'] / 2 for vx, vy, vr in vs.get(x['net'], ())): continue
                pp = pad_planes.get(s); zi = pp.locate([p[0]], [p[1]])[0] if pp else -1
                if zi >= 0 and pp.zones[zi]['net'] == x['net']: continue
                loose.append('%s %s at %s' % (x['net'], s, place(*p)))
    pr('  track joints: ' + ('; '.join('%d %s' % (v, k) for k, v in joined.items()) or 'all ends coincide exactly') +
       '; ends at no via, pad or track of their net: %d%s' % (len(loose), (' (' + '; '.join(loose[:6]) + (' ...' if len(loose) > 6 else '') + ')') if loose else ''))
    pr('')
    pr('== SELF-CHECK: %s ==' % ('all ok' if all(ok for ok, _ in checks) else 'FAILED - the numbers below cannot be relied on'))
    for ok, text in checks: pr('  %s  %s' % ('ok    ' if ok else 'FAILED', text))
    for text in notes: pr('  note    %s' % text)

    # ------------------------------------------------------------------ the numbers behind the summary
    CT = {s: class_rows(R[s], RE[s], a.min_void) for s in sig_layers}
    def in_tab(v): return any('tab' in k for k in v['cause'])
    lay_len = collections.defaultdict(collections.Counter)
    for l, ss in segs_by_layer.items():
        for x in ss: lay_len[x['net']][l] += math.hypot(x['b'][0] - x['a'][0], x['b'][1] - x['a'][1])
    inner_sig = [l for l in sig_layers if l not in (order[0], order[-1])]
    by_cls = collections.defaultdict(list)
    for n, c in lay_len.items(): by_cls[net_class(n, power)].append((sum(c[l] for l in inner_sig), n, sum(c.values())))
    ref_net_of = {s: planes[ref_of[s]]['base']['net'] for s in sig_layers}
    shared_of = {s: {ref_net_of[s]} | ({planes[sec_of[s]]['base']['net']} if sec_role[s] == 'other side' else set()) for s in sig_layers}
    changes, ncaps = layer_changes(B, segs_by_layer, ref_net_of, shared_of, B['pads'], power)
    st_vias = [v for v in B['vias'] if v['key'] in stitch]
    st_rep = {}                                            # plane layer -> what the stitching vias do there
    for pl in plane_layers:
        I = integ[pl]; P = planes[pl]; hole_of = {k: h for h in I['holes'] for k in h['vias']}
        here = [v for v in st_vias if pl in v['span']]
        anti = [v for v in here if P['plane'].locate([v['x']], [v['y']])[0] < 0]
        hs = [hole_of[v['key']] for v in anti if v['key'] in hole_of]
        rep = dict(n=len(here), joined=len(here) - len(anti), anti=len(anti), alone=sum(1 for h in hs if len(h['vias']) == 1),
                   merged=sum(1 for h in hs if len(h['vias']) > 1), open_=len(anti) - len(hs), longest=max([h['length'] for h in hs] or [0.0]),
                   slots=len(set(id(h) for h in hs if h['length'] > a.slot)), webs=sorted((h['web'], h['at']) for h in hs if h['web'] is not None), tracks={})
        others = [v for v in B['vias'] if pl in v['span'] and v['net'] in plane_nets and v['key'] not in stitch and P['plane'].locate([v['x']], [v['y']])[0] < 0]
        rep['others'] = len(others)
        for s, which, vv in [(s, w, vv) for s in sig_layers for w, vv in (('stitching', anti), ('other', others))]:
            if not (pl == ref_of[s] or (pl == sec_of[s] and sec_role[s] == 'other side')) or not vv: continue
            ss = segs_by_layer[s]; A = np.array([x['a'] for x in ss], float); Bq = np.array([x['b'] for x in ss], float); hw = np.array([x['w'] / 2 for x in ss])
            inside = 0.0; over = []; least = None
            for v in vv:
                ra = v['d'] / 2 + P['clearance']
                d = seg_dist([v['x']], [v['y']], A[:, 0], A[:, 1], Bq[:, 0], Bq[:, 1])[0] - hw
                k = int(np.argmin(d))
                if least is None or d[k] - ra < least[0]: least = (float(d[k] - ra), ss[k]['net'], v)
                for k in np.nonzero(d < ra)[0]:
                    sp = circle_span(A[k, 0], A[k, 1], Bq[k, 0], Bq[k, 1], v['x'], v['y'], ra)
                    L = (sp[1] - sp[0]) * math.hypot(Bq[k, 0] - A[k, 0], Bq[k, 1] - A[k, 1]) if sp else 0.0
                    inside += L; over.append((L, ss[k]['net'], v))
            rep['tracks'][(s, which)] = dict(role='reference' if ref_of[s] == pl else sec_role[s], inside=inside, over=over, least=least)
        st_rep[pl] = rep

    # ------------------------------------------------------------------ summary
    pr('')
    pr('== SUMMARY ==')
    for s in sig_layers:
        pl = ref_of[s]; P = planes[pl]; t = CT[s]; f = collections.Counter()
        for k in fast_names: f.update(t[k])
        f['st_max'] = max(t[k]['st_max'] for k in fast_names)
        top = max(((v, n) for n, rec in R[s]['nets'].items() if rec['cls'] != 'slow' for v in rec['stretches'] if v['length'] > a.min_void), key=lambda q: q[0]['length'], default=None)
        pr('1  %s over %s (%s%s)%s:' % (s, pl, P['base']['label'], ', %d islands' % len(P['islands']) if P['islands'] else ', no islands', ', %s %s' % (sec_role[s], sec_of[s]) if sec_of[s] else ''))
        if P['multi']:
            pr('   fast nets: %d island-edge crossings, %d net changes (%d at a via), %.2f mm over island copper' % (f['edge_x'], f['net_x'], f['at_via'], f['isl']))
        pr('   fast nets: %d stretches off the %s longer than %.1f mm, %.2f mm in all%s%s' % (f['st'], P['base']['label'], a.min_void, f['st_mm'],
           (' (longest %.2f mm: %s at %s)' % (top[0]['length'], top[1], place(*top[0]['at']))) if top else '',
           ('; %s whole under %d of them, open under %.2f mm of the other %d' % (short(sec_of[s]), f['st_whole'], f['st_open'], f['st'] - f['st_whole'])) if sec_of[s] and f['st'] else ''))
        sl = t['slow']; slow_st = [v for rec in R[s]['nets'].values() if rec['cls'] == 'slow' for v in rec['stretches'] if v['length'] > a.min_void]
        nl = max(((rec['noref_longest'], n) for n, rec in R[s]['nets'].items() if rec['cls'] != 'slow' and rec['noref_longest']), key=lambda q: q[0][0], default=None)
        pr('   slow nets: %d stretches longer than %.1f mm (%d of them in the card-edge tab); track edges: void runs > %.1f mm fast %d, slow %d' % (
            sl['st'], a.min_void, sum(1 for v in slow_st if in_tab(v)), a.min_void, f['edge_longv'], sl['edge_longv']))
        if sec_of[s]: pr('   copper on neither %s nor %s: fast %.2f mm%s, slow %.2f mm' % (short(pl), short(sec_of[s]), f['noref'],
                         (' (longest run %.2f mm: %s at %s)' % (nl[0][0], nl[1], place(*nl[0][1]))) if nl else '', sl['noref']))
    for s in multi:
        rows, shared = isl_rows[s]
        pr('2  islands of %s: %s  (island-edge crossings fast/slow)' % (ref_of[s], '; '.join('%s %d/%d' % (lab, R[s]['edge_x'][(lab, True)], R[s]['edge_x'][(lab, False)]) for lab in rows)))
        lone = ['%s (%s)' % (lab, ' + '.join(str(n) for _, n in joins[ref_of[s]][lab]) or 'no copper') for lab in rows if not joins[ref_of[s]][lab] or min(n for _, n in joins[ref_of[s]][lab]) < 2]
        if lone: pr('   island pieces joined by fewer than two vias of their net (they carry no current): ' + ', '.join(lone))
    for pl in plane_layers:
        I = integ[pl]; P = planes[pl]; narrow = [w for w in I['webs'] if w['width'] < a.web]; rep = st_rep[pl]
        pr('3  %s: %s in %d piece%s; cut off by island removal: %s; %d holes, %d longer than %.1f mm%s; webs under %.2f mm: %d%s; stitching vias: %d (%d with an antipad here)' % (
            pl, P['base']['label'], len(P['base']['fill']), '' if len(P['base']['fill']) == 1 else 's',
            ('%d pieces, %.2f mm2' % (len(lost[pl]), sum(q[1] for q in lost[pl]))) if lost[pl] else 'nothing', len(I['holes']), len(I['slots']), a.slot,
            ' (rings round islands apart)' if P['islands'] else '', a.web, len(narrow), (' (narrowest %.3f mm at %s)' % (narrow[0]['width'], place(*narrow[0]['at']))) if narrow else '', rep['n'], rep['anti']))
        for (s, which), q in rep['tracks'].items():
            if which == 'stitching' and ref_of[s] == pl:
                pr('   %s tracks over the antipads of the stitching vias in %s: %.2f mm%s; least margin from track copper to such an antipad %+.3f mm' % (
                    s, pl, q['inside'], (' (%s)' % ', '.join(sorted(set(n for _, n, _ in q['over'])))) if q['over'] else '', q['least'][0]))
    on_inner = [x for k in OUTER_ONLY for x in by_cls[k] if x[0] > 0]
    pr('4  docs/13 fast lines (%s) belong on %s / %s: %d of %d routed nets have %.1f mm of their %.1f mm on %s (%s)' % (
        ', '.join(OUTER_ONLY), order[0], order[-1], len(on_inner), sum(len(by_cls[k]) for k in OUTER_ONLY), sum(x[0] for x in on_inner),
        sum(x[2] for k in OUTER_ONLY for x in by_cls[k]), ' / '.join(inner_sig) or 'no inner signal layer',
        ', '.join('%s %.1f of %.1f mm' % (k, sum(x[0] for x in by_cls[k]), sum(x[2] for x in by_cls[k])) for k in OUTER_ONLY)))
    mixed = [c for c in changes if c['cls'] != 'slow' and len(c['refs']) > 1]
    if mixed:
        cd = [c['cap'] for c in mixed if c['cap'] is not None]
        pr('   fast-net vias where the reference changes net (%s): %d; nearest capacitor between those nets: median %.2f mm, farthest %.2f mm' % (
            ' / '.join(sorted(set('-'.join(c['refs']) for c in mixed))), len(mixed), float(np.median(cd)) if cd else float('nan'), max(cd) if cd else float('nan')))

    # ------------------------------------------------------------------ 1: every signal layer over its reference plane
    for s in sig_layers:
        pl = ref_of[s]; P = planes[pl]; recs = R[s]['nets']; base = P['base']['label']; isl = P['multi']; sec = sec_of[s]
        pr('')
        pr('== 1. %s over %s (%s%s)%s ==' % (s, pl, base, '; islands: ' + ', '.join(z['label'] for z in P['islands']) if isl else ', no islands',
                                           '; %s: %s' % (sec_role[s], sec) if sec else ''))
        pr('   stretch = a run of the centreline off the %s (over no %s copper%s), the antipads of the track\'s own vias left out;' % (base, short(pl), ' or over an island' if isl else ''))
        pr('   void = over no %s copper; no-plane = over copper of neither %s nor %s; edges = void runs where the centreline or a track edge (+-w/2) is over no copper.' % (
            short(pl), short(pl), short(sec) if sec else '-'))
        if isl: pr('   edge x = crossings of an island outline by the centreline (docs/13: "③ の信号は ④ の電源の境目をまたがない"); net x = changes of the %s net under the track (+n: at a via of the track, by the copper round it)' % short(pl))
        pr('')
        pr('   %-6s %4s %8s %s%8s %5s %4s %8s %7s %s%8s %5s' % ('class', 'nets', 'trk mm', '%6s %6s %9s ' % ('edge x', 'net x', 'island mm') if isl else '', 'void mm', '>%.1f' % a.min_void,
           'str', 'str mm', 'longest', '%9s ' % ('%s open' % short(sec)) if sec else '', 'no-plane', 'edges'))
        for k, t in CT[s].items():
            if not t['nets']: continue
            pr('   %-6s %4d %8.1f %s%8.2f %5d %4d %8.2f %7.2f %s%8.2f %5d' % (k, t['nets'], t['len'], '%6d %6s %9.2f ' % (t['edge_x'], '%d' % (t['net_x'] - t['at_via']) + ('+%d' % t['at_via'] if t['at_via'] else ''), t['isl']) if isl else '',
               t['void'], t['longv'], t['st'], t['st_mm'], t['st_max'], '%9.2f ' % t['st_open'] if sec else '', t['noref'], t['edge_longv']))
        for title, fast in (('FAST nets', True), ('SLOW nets', False)):
            names = fast_first([n for n in recs if (recs[n]['cls'] != 'slow') == fast], recs)
            def longs(n): return [v for v in recs[n]['stretches'] if v['length'] > a.min_void]
            def elongs(n): return [v for v in RE[s]['nets'][n]['void_runs'] if v['length'] > a.min_void] if n in RE[s]['nets'] else []
            bad = [n for n in names if longs(n) or recs[n]['edge_x'] or recs[n]['crossings'] or recs[n]['island_runs'] or elongs(n)]
            pr('')
            pr('-- %s on %s: %d nets, %d with a stretch longer than %.1f mm%s or an edges void run longer than %.1f mm --' % (title, s, len(names), len(bad), a.min_void, ', island copper' if isl else '', a.min_void))
            if not fast and not a.all_slow:
                tab = [(n, v) for n in bad for v in longs(n) if in_tab(v)]; rest = [(n, v) for n in bad for v in longs(n) if not in_tab(v)]
                pr('   stretches longer than %.1f mm: %d in the card-edge tab (%.2f mm; longest %s), %d elsewhere' % (a.min_void, len(tab), sum(v['length'] for _, v in tab),
                   ', '.join('%s %.2f' % (n, v['length']) for n, v in sorted(tab, key=lambda q: -q[1]['length'])[:3]) or '-', len(rest)))
                for n, v in sorted(rest, key=lambda q: -q[1]['length'])[:12]:
                    pr('     %-11s %.2f mm at %s: %s%s' % (n, v['length'], place(*v['at']), cause_text(v['cause']), ('; ' + under_text(v['under'], v['length'], s)) if sec else ''))
                if len(rest) > 12: pr('     ... %d more (--all-slow lists them)' % (len(rest) - 12))
                if isl:
                    t = CT[s]['slow']; pr('   island-edge crossings %d, net changes %d (%d at a via), %.2f mm over island copper' % (t['edge_x'], t['net_x'], t['at_via'], t['isl']))
                continue
            pr('   %-11s %-6s %8s %s%4s %7s %s%8s %5s  %s' % ('net', 'class', 'trk mm', '%6s %6s %9s ' % ('edge x', 'net x', 'island mm') if isl else '', 'str', 'longest',
               '%9s ' % ('%s open' % short(sec)) if sec else '', 'no-plane', 'edges', 'stretches, net changes, edges void runs'))
            for n in sorted(bad, key=lambda n: (-recs[n]['edge_x'], -len(recs[n]['crossings']), -max([v['length'] for v in longs(n)] or [0]))):
                rec = recs[n]; L = longs(n); txt = []
                for v in rec['stretches'] if isl else L:
                    txt.append('%.2f mm at %s: %s; %s%s' % (v['length'], place(*v['at']), ', '.join('%s %.2f' % (k, x) for k, x in sorted(v['over'].items(), key=lambda q: (q[0] == 'void', -q[1]))),
                                                          cause_text(v['cause']) or 'no void', ('; ' + under_text(v['under'], v['length'], s)) if sec else ''))
                for c in rec['crossings']:
                    if c['via']: txt.append('net change at a via: %s at %s (copper on the rings: %s)' % (' | '.join(c['between']), place(*c['via'][0]['at']),
                                            '; '.join(', '.join('%s %d' % kv for kv in q['copper'].items()) + ' of %d points' % q['points'] for q in c['via'])))
                for v in elongs(n):
                    if not any(abs(v['at'][0] - u['at'][0]) < 0.6 and abs(v['at'][1] - u['at'][1]) < 0.6 for u in L): txt.append('edges: %.2f mm at %s: %s' % (v['length'], place(*v['at']), cause_text(v['cause'])))
                pr('   %-11s %-6s %8.1f %s%4d %7.2f %s%8.2f %5d  %s' % (n, rec['cls'], rec['length'], '%6d %6s %9.2f ' % (rec['edge_x'], '%d' % (len(rec['crossings']) - sum(1 for c in rec['crossings'] if c['via'])) +
                   ('+%d' % sum(1 for c in rec['crossings'] if c['via']) if any(c['via'] for c in rec['crossings']) else ''), sum(v['length'] for v in rec['island_runs'])) if isl else '',
                   len(L), max([v['length'] for v in L] or [0.0]), '%9.2f ' % sum(v['under'][0] for v in L if v['under']) if sec else '', rec['noref'], len(elongs(n)), txt[0] if txt else ''))
                for t_ in txt[1:]: pr('   %s%s' % (' ' * (75 if isl else 51) + (' ' * 10 if sec else ''), t_))
        if isl: pr('   vias of a track standing in its void run: %d judged by the copper round them, %d with too little copper round them (in a larger void)' % (R[s]['ring_vias'] - R[s]['bare_vias'], R[s]['bare_vias']))

    # ------------------------------------------------------------------ 2: islands
    for s in multi:
        pl = ref_of[s]; rows, shared = isl_rows[s]; res = R[s]
        pr('')
        pr('== 2. Islands of %s under the %s tracks (fast / slow) ==' % (pl, s))
        pr('   copper = filled pieces with the vias of the island\'s net that touch each; inside = track length inside the drawn outline;')
        pr('   over copper = track length over the island\'s copper; edge x / net x as in section 1.')
        pr('   %-22s %-34s %13s %13s %9s %9s  %s' % ('island', 'copper: mm2 (vias) per piece', 'inside mm', 'over copper', 'edge x', 'net x', 'fast nets: edge x / net x / mm over copper'))
        for lab, r in rows.items():
            names = [n for n, rec in res['nets'].items() if rec['cls'] != 'slow' and (rec['edge_by'][lab] or n in r['nets'])]
            nets_txt = ', '.join('%s %d/%d/%.1f' % (n, res['nets'][n]['edge_by'][lab], r['nets'][n][0], r['nets'][n][1])
                                 for n in sorted(names, key=lambda n: (-res['nets'][n]['edge_by'][lab], -r['nets'][n][1])))
            pr('   %-22s %-34s %6.1f /%5.1f %6.1f /%5.1f %4d /%3d %4d /%3d  %s' % (lab, ' + '.join('%.1f (%d)' % q for q in joins[pl][lab]) or 'none', res['inside'][(lab, True)], res['inside'][(lab, False)],
               r['over'][True], r['over'][False], res['edge_x'][(lab, True)], res['edge_x'][(lab, False)], r['net_x'][True], r['net_x'][False], nets_txt or '-'))
        for lab, c in shared.items(): pr('   %-22s %-34s %13s %13s %9s %4d /%3d  (net changes between two islands, counted once here)' % (lab, '', '', '', '', c[True], c[False]))

    # ------------------------------------------------------------------ 3: the plane copper
    pr('')
    pr('== 3. Plane copper: pieces, cut-off copper, holes, webs, stitching vias ==')
    pr('   hole length = its largest extent; web = the narrowest copper between two holes of one piece (or a hole and the piece\'s outline)')
    pr('   stitching vias = %s: %d (%s)' % ('the plane-net vias that %s does not have' % os.path.basename(a.before) if a.before else 'vias of a plane net with no track end and no pad of their net (joined through the zones only)',
        len(stitch), ', '.join('%s %d' % kv for kv in collections.Counter(k[2] for k in stitch).most_common()) or '-'))
    for pl in plane_layers:
        I = integ[pl]; P = planes[pl]; rep = st_rep[pl]
        kinds = collections.Counter('ring round an island' if h['kind'].startswith('ring') else ('antipad of one via' if len(h['vias']) == 1 else 'merged antipads' if h['vias'] else h['kind']) for h in I['holes'])
        pr('')
        pr('   %s: %s' % (pl, '; '.join('%s %s mm2' % (z['label'], ' + '.join('%.2f' % x for x in z['pieces']) or '0') for z in I['zones'])))
        pr('      cut off by island removal (copper KiCad drops because no item of its net joins it): %s' % (', '.join('%s %.2f mm2 at %s' % (n, ar, place(*c)) for n, ar, c, _ in
           sorted(lost[pl], key=lambda q: -q[1])[:8]) + (' ...' if len(lost[pl]) > 8 else '') if lost[pl] else 'nothing'))
        pr('      holes: %d (%s); most vias in one hole: %d' % (len(I['holes']), ', '.join('%d %s' % (v, k) for k, v in kinds.most_common()), max([len(h['vias']) for h in I['holes']] or [0])))
        for h in I['slots']:
            pr('      hole %.2f x %.2f mm at %s: %s%s' % (h['length'], h['width'], place(*h['at']), ('%d vias (%s)' % (len(h['vias']), ', '.join('%s%s' % (n, ' x%d' % m if m > 1 else '') for n, m in h['nets'][:5])))
               if h['vias'] else h['kind'], (', %d of them stitching vias' % sum(1 for k in h['vias'] if k in stitch)) if any(k in stitch for k in h['vias']) else ''))
        for h in I['holes']:
            if h['kind'].startswith('ring'): pr('      %s: %.2f x %.2f mm, %d antipads of other vias merged into it' % (h['kind'], h['length'], h['width'], len(h['vias'])))
        for w in [w for w in I['webs'] if w['width'] < a.web] or I['webs'][:1]:
            hs = [I['holes'][k] for k in w['holes']]
            pr('      web %.3f mm at %s between %s%s' % (w['width'], place(*w['at']), ' and '.join('%s (%s)' % ('hole of %d via%s' % (len(h['vias']), '' if len(h['vias']) == 1 else 's') if h['vias'] else h['kind'],
               ', '.join(n for n, _ in h['nets'][:4])) for h in hs) + (' and the outline of the fill' if len(hs) < 2 else ''), '' if w['width'] < a.web else ' (narrowest; none under %.2f mm)' % a.web))
        if not I['webs']: pr('      no web under %.1f mm' % reach)
        pr('      stitching vias: %d pass this layer; %d join its copper, %d have an antipad: %d alone in its hole, %d merged with other antipads, %d open to the outline of the fill (a notch in its edge)' % (
            rep['n'], rep['joined'], rep['anti'], rep['alone'], rep['merged'], rep['open_']))
        if rep['anti']:
            pr('      holes with a stitching via: longest %.2f mm, %d longer than %.1f mm; narrowest web from such a hole %s' % (rep['longest'], rep['slots'], a.slot,
               ('%.3f mm at %s' % (rep['webs'][0][0], place(*rep['webs'][0][1]))) if rep['webs'] else 'none under %.1f mm' % reach))
        for (s, which), q in rep['tracks'].items():
            if which == 'stitching' or q['over']:
                pr('      %s tracks (%s) over the antipads of the %s vias: centreline %.2f mm on %d nets%s; nearest track copper to the rim of such an antipad: %+.3f mm (%s, via at %s)' % (
                    s, q['role'], which if which == 'stitching' else '%d other %s' % (rep['others'], '/'.join(sorted(plane_nets))), q['inside'], len(set(n for _, n, _ in q['over'])), (' (%s)' % ', '.join(sorted(set('%s at %s' % (n, place(v['x'], v['y'])) for L, n, v in q['over']))[:6])) if q['over'] else '',
                    q['least'][0], q['least'][1], place(q['least'][2]['x'], q['least'][2]['y'])))

    # ------------------------------------------------------------------ 4: the docs/13 rule: fast lines by layer, and their layer changes
    pr('')
    pr('== 4. Fast lines by layer (docs/13: %s on %s / %s, next to a whole GND plane) ==' % (', '.join(OUTER_ONLY), order[0], order[-1]))
    pr('   %-6s %5s %9s %10s %10s %6s   %s' % ('class', 'nets', 'on inner', 'inner mm', 'total mm', 'share', 'nets on %s: inner mm / total mm' % (' / '.join(inner_sig) or '-')))
    for k in fast_names:
        xs = sorted(by_cls[k], reverse=True); inn = [x for x in xs if x[0] > 0]; tot = sum(x[2] for x in xs)
        pr('   %-6s %5d %9d %10.1f %10.1f %5.0f%%   %s' % (k, len(xs), len(inn), sum(x[0] for x in inn), tot, 100.0 * sum(x[0] for x in inn) / tot if tot else 0.0,
           ', '.join('%s %.1f/%.1f' % (n, li, lt) for li, n, lt in inn) or '-') + ('' if k in OUTER_ONLY else '   (not named by the rule)'))
    usb = set(n for n in lay_len if net_class(n, power) == 'USB')
    if usb:
        xs = plan_crossings(segs_by_layer, usb)
        pr('   USB: %s' % '; '.join('%s %s' % (n, ', '.join('%s %.1f mm' % (short(l), L) for l, L in sorted(lay_len[n].items()))) for n in sorted(usb)))
        pr('   tracks of other nets that cross the USB tracks in plan view: %s' % (', '.join(sorted(set('%s (%s) over %s at %s' % (o, short(ol), n, place(x, y)) for n, l, o, ol, x, y in xs))) or 'none'))
    pr('')
    pr('   Layer changes of the fast nets: vias where the net\'s tracks end on two or more layers. The return current changes plane there: between two')
    pr('   planes of one net through the nearest via of that net, between planes of two nets through the nearest capacitor between them')
    pr('   (%s; capacitors found between plane nets: %s).' % (', '.join('%s -> %s' % (s, ref_net_of[s]) for s in sig_layers), ', '.join('%s %d' % ('-'.join(k), v) for k, v in ncaps.items()) or 'none'))
    pr('   %-6s %-14s %5s %-30s %21s' % ('class', 'reference nets', 'vias', 'nearest via of a shared plane net', 'nearest capacitor'))
    groups = collections.defaultdict(list)
    for c in changes:
        if c['cls'] != 'slow': groups[(c['cls'], '-'.join(c['refs']))].append(c)
    for (k, refs), cs in sorted(groups.items(), key=lambda q: (fast_names.index(q[0][0]), q[0][1])):
        vd = [min(d for d in c['via'].values() if d is not None) for c in cs if any(d is not None for d in c['via'].values())]
        cd = [c['cap'] for c in cs if c['cap'] is not None]; sh = sorted(set(n for c in cs for n in c['via']))
        pr('   %-6s %-14s %5d %-30s %21s' % (k, refs, len(cs), ('%s median %.2f, max %.2f' % ('/'.join(sh), np.median(vd), max(vd))) if vd else '-', ('median %.2f, max %.2f' % (np.median(cd), max(cd))) if cd else '-'))
    worst_cap = sorted((c for c in changes if c['cls'] != 'slow' and c['cap'] is not None), key=lambda c: -c['cap'])[:6]
    if worst_cap: pr('   farthest from a capacitor: ' + '; '.join('%s %s %.2f mm at %s' % (c['net'], '/'.join(short(l) for l in c['layers']), c['cap'], place(*c['at'])) for c in worst_cap))

    # ------------------------------------------------------------------ files
    js = dict(board=src, md5=md5_of(src), design=a.design, origin=[XC, H], min_void=a.min_void, self_check=[dict(ok=ok, text=t) for ok, t in checks], notes=notes,
              layers={}, planes={}, layer_changes=changes, stitching_vias=sorted(stitch))
    def clean(rec): return {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in rec.items()}
    for s in sig_layers:
        js['layers'][s] = dict(reference=ref_of[s], second=sec_of[s], second_role=sec_role[s], distance=dist(s, ref_of[s]), classes={k: dict(v) for k, v in CT[s].items()},
                               nets={n: clean(rec) for n, rec in R[s]['nets'].items()},
                               track_edges={n: dict(void_runs=rec['void_runs']) for n, rec in RE[s]['nets'].items() if rec['void_runs']})
    for pl in plane_layers:
        js['planes'][pl] = dict(zones=integ[pl]['zones'], holes=integ[pl]['holes'], webs=integ[pl]['webs'], joins=joins[pl],
                                cut_off=[dict(net=n, area=ar, at=c) for n, ar, c, _ in lost[pl]], stitching={k: v for k, v in st_rep[pl].items() if k != 'tracks'})
    with open(os.path.join(out_dir, 'planes.json'), 'w') as f: json.dump(js, f, indent=1, default=str)
    col = {'+3V3': '#f4c2c2', '+1V1': '#9ecae1', 'V5_IN': '#fdd0a2', 'GND': '#c7e9c0'}
    xs = [c for e in B['edges'] for c in (e[0], e[2])]; ys = [c for e in B['edges'] for c in (e[1], e[3])]
    views = [(None, (min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1))]
    for zm in a.zoom:
        q = [float(v) for v in zm.split(',')]; w = q[2] if len(q) > 2 else 8.0
        views.append(('zoom_%g_%g' % (q[0], q[1]), (q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2)))
    for s in sig_layers:
        pl = ref_of[s]; P = planes[pl]; an = R[s]['analysis']; big = []
        for n, rec in R[s]['nets'].items():
            for v in rec['stretches']:
                if v['length'] > a.min_void: big.append((v['at'][0], v['at'][1], 0.6 if rec['cls'] != 'slow' else 0.4))
        cross = [(x, y, 0.5 if f else 0.3) for x, y, f in R[s].get('edge_at', [])]
        for name, bb in views:
            layers = [('poly', [poly for poly in z['fill']], 'fill="%s" stroke="none"' % col.get(z['net'], '#ddd')) for z in P['zones']]
            layers += [('poly', [r for _, _, _, r in lost[pl]], 'fill="#fd8" stroke="#a60" stroke-width="0.5"')]
            layers.append(('line', [(x['a'][0], x['a'][1], x['b'][0], x['b'][1], x['w']) for x in an.segs], 'stroke="#555" stroke-linecap="round"'))
            layers.append(('dot', [(v['x'], v['y'], v['d'] / 2) for v in B['vias'] if pl in v['span']], 'fill="none" stroke="#333" stroke-width="0.6"'))
            layers.append(('dot', [(v['x'], v['y'], v['d'] / 2) for v in st_vias], 'fill="#2a2" stroke="none"'))
            layers.append(('dot', big, 'fill="none" stroke="#d00" stroke-width="2"'))
            layers.append(('dot', cross, 'fill="none" stroke="#00c" stroke-width="2"'))
            stem = '%s_over_%s' % (short(s).lower(), short(pl).lower())
            svg_write(os.path.join(out_dir, (stem if name is None else '%s_%s' % (name, stem)) + '.svg'), bb, layers)
    pr('')
    pr('files: planes.txt (this report), planes.json, %s; run time %.1f s' % (', '.join('%s_over_%s.svg' % (short(s).lower(), short(ref_of[s]).lower()) for s in sig_layers) +
       (', zoom_*.svg' if a.zoom else '') + (', drc.txt' if a.drc else ''), time.time() - t_start))
    return finish(lines, out_dir, 0 if all(ok for ok, _ in checks) else 2)

def finish(lines, out_dir, status):
    text = '\n'.join(lines) + '\n'
    with open(os.path.join(out_dir, 'planes.txt'), 'w') as f: f.write(text)
    sys.stdout.write(text)
    return status

if __name__ == '__main__':
    code = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)                                         # pcbnew's objects are not torn down (it prints leak notes when they are)
