#!/usr/bin/env python3
"""Short supply copper at every decoupling capacitor of a routed board (designs with DECAP, rev H on).

Why: the autorouter joins a capacitor to its net anywhere. On rev H it chained the 3.3 V pins of a chip and their 100 nF
on 0.12 mm track to a few vias (28 for the whole +3V3 net), and hung DVDD capacitors on the +1V1 trunk far from their
pins: a pin-to-capacitor loop had a median of 16 mm, up to 91 mm (tools/pcb/review/decoupling.py). A capacitor so far
away in copper does not decouple its pin. Routing again would not help: the router does not know which capacitor
belongs to which pin. The design knows (DECAP: capacitor -> part and power pins), and this tool adds, after routing,
the copper that makes the loops short. Nothing is moved or removed.

What it adds
  1 plane vias: every pad of a plane net (the design's PLANES; rev H: GND on In1 / In4, +3V3 on In2) that belongs to a
    capacitor of DECAP, or is a power pin of DECAP, gets a via of its net within --reach (1.0 mm) of the pad centre,
    unless a via of the net already touches the pad, its stub or (GND) the pour piece that holds the pad there. The new
    via sits in the pad (the order asks for filled and capped vias, docs/13), on a track that starts in the pad, or -
    GND only - in the GND pour piece that holds the pad. A pad where no via fits within --reach gets one up to 2 mm
    away, joined to the pad by a new track on the pad's layer (0.2 mm; 0.15 / 0.12 mm where 0.2 does not fit).
  2 direct links: a capacitor of a net without a plane (rev H: +1V1), or of a plane net whose pin or capacitor has no
    via after 1, whose track path to its nearest pin is longer than --loop (3.0 mm) and 1.6 x the straight distance +
    1 mm, gets a route of its own from the pin to the capacitor: a maze route on the signal layers (0.2 mm track; 0.15
    / 0.12 mm where 0.2 does not fit) with up to two vias, at most the longest of 2 x --loop, 2 x the straight
    distance + 2 mm and a fifth of the present path, and at least 1 mm shorter than the present path (a route that
    gains less is taken out again).
  3 the design's DECAP_EXTRA = {'vias': [(net, x, y, radius, why)], 'links': [(ref, pad, ref, pad, why)]} (KiCad mm):
    a via at the free spot nearest (x, y) within radius that touches copper of its net; a link as in 2.
  4 second vias: a via that is the only joint of a supply net of NET_WIDTH between two of its layers (removing it
    splits the net's pads) gets a twin 0.8-1.2 mm away, joined to it on every layer where it has a track, with the
    net's width (at most 0.4 mm).
Every addition keeps the board's clearance on every copper layer, 0.25 mm between hole walls, the rule areas and the
board edge. A new via may stand next to an In3 track: its antipad opens one of the track's two reference planes (a GND
via the +3V3 plane In2, a +3V3 via the GND plane In4), never both, and only for about 1 mm of the track.
Then the zones are filled and the rule check runs in a child process. If it finds more errors or open connections than
the board had, the additions within 0.8 mm of an error are taken out and the check runs again (3 rounds; after that the
board is left as it was, exit 1). The zones are not refilled in the saved board (the steps after it refill them).
    FC_DESIGN=design_revh python3 decap_links.py board.kicad_pcb [--dry] [--reach 1.0] [--loop 3.0]
Prints, per kind, what was added and what found no room."""
import os, sys, re, math, json, heapq, argparse, tempfile, subprocess, importlib, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('pcb'); ap.add_argument('--dry', action='store_true')
ap.add_argument('--reach', type=float, default=1.0); ap.add_argument('--loop', type=float, default=3.0)
args = ap.parse_args() if __name__ == '__main__' else None      # decap_reroute.py imports this file as a library
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I
import dsn_export
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
C = float(getattr(D, 'CLEAR', 0.15)); VR = float(getattr(D, 'VIA_DIA', 0.5)) / 2; DR = float(getattr(D, 'VIA_DRILL', 0.3)) / 2
HOLE_GAP, EDGE, G, EPS = 0.25, 0.3, 0.05, 0.01
STUB = 2.0                           # mm: longest new track from a pad to its plane via
LINK_W = (0.2, 0.15, 0.12)
VIA_COST = 1.0                       # mm of track a layer change is worth in the maze

# ---------------------------------------------------------------------------------------------- board as plain data
class Board:
    def __init__(self, b):
        self.b = b
        ncu = b.GetCopperLayerCount()
        self.sig, self.plane_of = dsn_export.layer_roles(ncu, getattr(D, 'PLANES', None))
        self.plane_nets = set(self.plane_of.values())
        self.inner_sig = [l for l in self.sig if l not in ('F.Cu', 'B.Cu')]
        tr = []
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA': continue
            ln = b.GetLayerName(t.GetLayer())
            tr.append((ToMM(t.GetStart().x), ToMM(t.GetStart().y), ToMM(t.GetEnd().x), ToMM(t.GetEnd().y), ToMM(t.GetWidth()) / 2, ln, t.GetNetname()))
        self.tracks = tr
        self.vias = [(ToMM(t.GetPosition().x), ToMM(t.GetPosition().y), ToMM(t.GetWidth()) / 2, ToMM(t.GetDrillValue()) / 2, t.GetNetname())
                     for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
        self.pads = []
        cu = [n for n in ['F.Cu'] + ['In%d.Cu' % k for k in range(1, ncu - 1)] + ['B.Cu']]
        for fp in b.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                layers = [n for n in cu if p.IsOnLayer(b.GetLayerID(n))]
                if not layers: continue
                circ = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
                self.pads.append(dict(ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(),
                                      x=ToMM(p.GetPosition().x), y=ToMM(p.GetPosition().y),
                                      box=(ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())),
                                      r=ToMM(p.GetSize().x) / 2 if circ else None, layers=layers,
                                      hole=ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2 if p.GetDrillSize().x > 0 else 0.0))
        self.areas = []
        for z in list(b.Zones()) + [z for fp in b.GetFootprints() for z in fp.Zones()]:
            if not z.GetIsRuleArea(): continue
            bb = z.GetBoundingBox()
            self.areas.append(((ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())),
                               [n for n in cu if z.IsOnLayer(b.GetLayerID(n))], z.GetDoNotAllowTracks(), z.GetDoNotAllowVias()))
        ol = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ol)
        self.edges = []                                    # closed chains of the outline and its holes, [(x, y), ...]
        for k in range(ol.OutlineCount()):
            for ch in [ol.Outline(k)] + [ol.Hole(k, h) for h in range(ol.HoleCount(k))]:
                self.edges.append([(ToMM(ch.CPoint(i).x), ToMM(ch.CPoint(i).y)) for i in range(ch.PointCount())])
        # GND (and any other plane net's) pour on the outer layers, filled: a GND via may sit in it
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        self.pour = collections.defaultdict(list)          # (net, layer) -> [SHAPE_POLY_SET piece]
        for z in b.Zones():
            if z.GetIsRuleArea(): continue
            for ln in ('F.Cu', 'B.Cu'):
                lid = b.GetLayerID(ln)
                if not z.IsOnLayer(lid): continue
                polys = z.GetFilledPolysList(lid)
                for k in range(polys.OutlineCount()):
                    piece = pcbnew.SHAPE_POLY_SET(); piece.AddOutline(polys.Outline(k))
                    for h in range(polys.HoleCount(k)): piece.AddHole(polys.Hole(k, h))
                    self.pour[(z.GetNetname(), ln)].append(piece)
        self.added = []                                    # ('via', x, y, net) / ('track', x1, y1, x2, y2, w, layer, net)

    def pad(self, ref, num):
        return next(p for p in self.pads if p['ref'] == ref and p['num'] == str(num))

    def add_via(self, x, y, net):
        self.vias.append((x, y, VR, DR, net)); self.added.append(('via', x, y, net))

    def add_track(self, x1, y1, x2, y2, w, layer, net):
        self.tracks.append((x1, y1, x2, y2, w / 2, layer, net)); self.added.append(('track', x1, y1, x2, y2, w, layer, net))

def undo(B, mark):
    """Take back every addition after the first `mark` ones."""
    for it in B.added[mark:]:
        if it[0] == 'via': B.vias.remove((it[1], it[2], VR, DR, it[3]))
        else: B.tracks.remove((it[1], it[2], it[3], it[4], it[5] / 2, it[6], it[7]))
    del B.added[mark:]

# ---------------------------------------------------------------------------------------------- local raster window
def seg_d(X, Y, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1) if L2 > 0 else 0.0
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy))

def box_d(X, Y, x0, y0, x1, y1):
    return np.hypot(np.maximum(np.maximum(x0 - X, 0), X - x1), np.maximum(np.maximum(y0 - Y, 0), Y - y1))

class Window:
    """Rasters of what a new track of width w (layer by layer) or a new via may not touch, around one place."""
    def __init__(self, B, net, x0, y0, x1, y1, w=0.2):
        self.B, self.net, self.w = B, net, w
        self.i0, self.j0 = int(math.floor(x0 / G)), int(math.floor(y0 / G))
        self.nx, self.ny = int(math.ceil(x1 / G)) - self.i0 + 1, int(math.ceil(y1 / G)) - self.j0 + 1
        xs = (self.i0 + np.arange(self.nx)) * G; ys = (self.j0 + np.arange(self.ny)) * G
        self.X, self.Y = np.meshgrid(xs, ys)
        L = B.sig; self.L = L
        self.hard = np.zeros((len(L), self.ny, self.nx), bool)
        self.hard_via = np.zeros((self.ny, self.nx), bool)
        lo_x, lo_y, hi_x, hi_y = x0 - 2, y0 - 2, x1 + 2, y1 + 2
        inside = lambda bx0, by0, bx1, by1: not (bx1 < lo_x or bx0 > hi_x or by1 < lo_y or by0 > hi_y)
        tw = w / 2 + C + EPS; vw = VR + C + EPS
        for (ax, ay, bx, by, hw, ln, n) in B.tracks:
            if not inside(min(ax, bx) - hw, min(ay, by) - hw, max(ax, bx) + hw, max(ay, by) + hw): continue
            d = seg_d(self.X, self.Y, ax, ay, bx, by)
            if n == net: continue
            if ln in L: self.hard[L.index(ln)] |= d < hw + tw
            self.hard_via |= d < hw + vw
        for (vx, vy, r, dr, n) in B.vias:
            if not inside(vx - r, vy - r, vx + r, vy + r): continue
            d = np.hypot(self.X - vx, self.Y - vy)
            self.hard_via |= d < dr + DR + HOLE_GAP                               # hole walls, own net too
            if n == net: continue
            self.hard |= (d < r + tw)[None]
            self.hard_via |= d < r + vw
        for p in B.pads:
            bx0, by0, bx1, by1 = p['box']
            if not inside(bx0, by0, bx1, by1): continue
            if p['hole'] > 0: self.hard_via |= np.hypot(self.X - p['x'], self.Y - p['y']) < p['hole'] + DR + HOLE_GAP
            if p['net'] == net and net: continue
            d = np.hypot(self.X - p['x'], self.Y - p['y']) - p['r'] if p['r'] else box_d(self.X, self.Y, bx0, by0, bx1, by1)
            for ln in p['layers']:
                if ln in L: self.hard[L.index(ln)] |= d < tw
            self.hard_via |= d < vw
        for (bx0, by0, bx1, by1), layers, no_tr, no_via in B.areas:
            if not inside(bx0, by0, bx1, by1): continue
            d = box_d(self.X, self.Y, bx0, by0, bx1, by1)
            if no_tr:
                for ln in layers:
                    if ln in L: self.hard[L.index(ln)] |= d < w / 2 + EPS
            if no_via: self.hard_via |= d < VR + EPS
        # board edge: cells outside the outline (even-odd over the outline and its holes) or nearer the edge than allowed
        inside = np.zeros(self.X.shape, bool); dmin = np.full(self.X.shape, np.inf)
        for ch in B.edges:
            for (ax, ay), (bx, by) in zip(ch, ch[1:] + ch[:1]):
                dmin = np.minimum(dmin, seg_d(self.X, self.Y, ax, ay, bx, by))
                if ay == by: continue
                cross = ((ay > self.Y) != (by > self.Y)) & (self.X < ax + (self.Y - ay) * (bx - ax) / (by - ay))
                inside ^= cross
        self.hard |= (~inside | (dmin < EDGE + w / 2))[None]
        self.hard_via |= ~inside | (dmin < EDGE + VR)

    def cell(self, x, y):
        return int(round(y / G)) - self.j0, int(round(x / G)) - self.i0

    def xy(self, j, i):
        return (self.i0 + i) * G, (self.j0 + j) * G

    def ok(self, j, i):
        return 0 <= j < self.ny and 0 <= i < self.nx

# ---------------------------------------------------------------------------------------------- copper path lengths
def path_len(B, net, a, b):
    """Shortest track path (mm, vias) between pads a and b of one net: Dijkstra over track ends, vias and pads."""
    nodes = {}; adj = collections.defaultdict(list)
    def nid(key):
        if key not in nodes: nodes[key] = len(nodes)
        return nodes[key]
    q = lambda x, y, ln: (round(x, 3), round(y, 3), ln)
    segs = [t for t in B.tracks if t[6] == net]
    for (ax, ay, bx, by, hw, ln, n) in segs:
        u, v = nid(q(ax, ay, ln)), nid(q(bx, by, ln)); L = math.hypot(bx - ax, by - ay)
        adj[u].append((v, L, 0)); adj[v].append((u, L, 0))
    ends = collections.defaultdict(list)                   # layer -> [(x, y, node)]
    for (x, y, ln), k in list(nodes.items()): ends[ln].append((x, y, k))
    def touching(x, y, r, layers):
        return [k for ln in layers for (ex, ey, k) in ends.get(ln, ()) if math.hypot(ex - x, ey - y) <= r + 0.002]
    for (vx, vy, r, dr, n) in B.vias:
        if n != net: continue
        hub = nid(('via', round(vx, 3), round(vy, 3)))
        for k in touching(vx, vy, r, B.sig): adj[hub].append((k, 0.0, 1)); adj[k].append((hub, 0.0, 1))
    def pad_node(p):
        hub = nid(('pad', p['ref'], p['num']))
        bx0, by0, bx1, by1 = p['box']
        for ln in p['layers']:
            for (ex, ey, k) in ends.get(ln, ()):
                if bx0 - 0.002 <= ex <= bx1 + 0.002 and by0 - 0.002 <= ey <= by1 + 0.002:
                    d = math.hypot(ex - p['x'], ey - p['y']) * 0      # entering the pad costs nothing
                    adj[hub].append((k, d, 0)); adj[k].append((hub, d, 0))
        return hub
    for p in B.pads:                                        # other pads of the net join the tracks that end in them
        if p['net'] == net: pad_node(p)
    s, t = nid(('pad', a['ref'], a['num'])), nid(('pad', b['ref'], b['num']))
    dist = {s: (0.0, 0)}; pq = [(0.0, 0, s)]
    while pq:
        d, nv, u = heapq.heappop(pq)
        if u == t: return d, nv
        if d > dist.get(u, (1e9, 0))[0] + 1e-9: continue
        for v, L, dv in adj[u]:
            nd = d + L
            if nd < dist.get(v, (1e9, 0))[0] - 1e-9: dist[v] = (nd, nv + dv); heapq.heappush(pq, (nd, nv + dv, v))
    return math.inf, 0

# ---------------------------------------------------------------------------------------------- vias
def via_near(B, net, pad, reach, stub_only=False):
    """A via of `net` within `reach` of `pad`: (x, y) of the best free spot (closest to the pad centre) that touches the
    pad, a track starting in it, or (GND) the pour piece that holds the pad; None when there is no room."""
    W = Window(B, net, pad['x'] - reach - 1, pad['y'] - reach - 1, pad['x'] + reach + 1, pad['y'] + reach + 1)
    bx0, by0, bx1, by1 = pad['box']
    touch = (box_d(W.X, W.Y, bx0, by0, bx1, by1) if pad['r'] is None else np.hypot(W.X - pad['x'], W.Y - pad['y']) - pad['r']) < VR - 0.05
    for (ax, ay, cx, cy, hw, ln, n) in B.tracks:
        if n != net or ln not in pad['layers']: continue
        if any(bx0 - 0.002 <= ex <= bx1 + 0.002 and by0 - 0.002 <= ey <= by1 + 0.002 for ex, ey in ((ax, ay), (cx, cy))):
            touch |= seg_d(W.X, W.Y, ax, ay, cx, cy) < hw + VR - 0.05
    if not stub_only:
        for piece in pad_pieces(B, net, pad):
            if True:
                inner = pcbnew.SHAPE_POLY_SET(piece); inner.Deflate(FromMM(VR + 0.03), 16)
                js, is_ = np.nonzero(np.hypot(W.X - pad['x'], W.Y - pad['y']) <= reach)
                for j, i in zip(js, is_):
                    if not touch[j, i] and inner.Contains(VECTOR2I(FromMM(float(W.X[j, i])), FromMM(float(W.Y[j, i])))): touch[j, i] = True
    ok = touch & ~W.hard_via & (np.hypot(W.X - pad['x'], W.Y - pad['y']) <= reach)
    if not ok.any(): return None
    d = np.where(ok, np.hypot(W.X - pad['x'], W.Y - pad['y']), np.inf)
    j, i = np.unravel_index(np.argmin(d), d.shape)
    return float(W.X[j, i]), float(W.Y[j, i])

def pad_pieces(B, net, pad):
    pt = VECTOR2I(FromMM(pad['x']), FromMM(pad['y']))
    return [piece for ln in pad['layers'] for piece in B.pour.get((net, ln), ()) if piece.Contains(pt)]

def via_at(B, net, x, y, rad):
    """DECAP_EXTRA via: the free spot nearest (x, y) within rad that touches a pad, track or outer pour of the net - on
    two layers or more for a net without a plane (a via that touches its net on one layer only joins nothing)."""
    W = Window(B, net, x - rad - 1, y - rad - 1, x + rad + 1, y + rad + 1)
    touch = collections.defaultdict(lambda: np.zeros(W.X.shape, bool))          # layer -> cells
    for p in B.pads:
        if p['net'] != net or math.hypot(p['x'] - x, p['y'] - y) > rad + 5: continue
        d = np.hypot(W.X - p['x'], W.Y - p['y']) - p['r'] if p['r'] else box_d(W.X, W.Y, *p['box'])
        for ln in p['layers']: touch[ln] |= d < VR - 0.05
    for (ax, ay, cx, cy, hw, ln, n) in B.tracks:
        if n == net: touch[ln] |= seg_d(W.X, W.Y, ax, ay, cx, cy) < hw + VR - 0.05
    for ln in ('F.Cu', 'B.Cu'):
        for piece in B.pour.get((net, ln), ()):
            inner = pcbnew.SHAPE_POLY_SET(piece); inner.Deflate(FromMM(VR + 0.03), 16)
            for j, i in zip(*np.nonzero(np.hypot(W.X - x, W.Y - y) <= rad)):
                if inner.Contains(VECTOR2I(FromMM(float(W.X[j, i])), FromMM(float(W.Y[j, i])))): touch[ln][j, i] = True
    layers = sum(m.astype(int) for m in touch.values()) if touch else np.zeros(W.X.shape, int)
    ok = (layers >= (1 if net in B.plane_nets else 2)) & ~W.hard_via & (np.hypot(W.X - x, W.Y - y) <= rad)
    if not ok.any(): return None
    d = np.where(ok, np.hypot(W.X - x, W.Y - y), np.inf)
    j, i = np.unravel_index(np.argmin(d), d.shape)
    return float(W.X[j, i]), float(W.Y[j, i])

def via_stub(B, net, pad, maxlen=STUB):
    """A via up to maxlen from the pad, joined to it by a new track on one of the pad's signal layers: the shortest
    such track (maze over the pad's layer, 8 directions). Returns (x, y, track length, width) or None."""
    for w in LINK_W:
        W = Window(B, net, pad['x'] - maxlen - 1, pad['y'] - maxlen - 1, pad['x'] + maxlen + 1, pad['y'] + maxlen + 1, w)
        bx0, by0, bx1, by1 = pad['box']
        inpad = (W.X >= bx0) & (W.X <= bx1) & (W.Y >= by0) & (W.Y <= by1)
        best = None
        for ln in pad['layers']:
            if ln not in W.L: continue
            k = W.L.index(ln); hard = W.hard[k] & ~inpad
            j0, i0 = W.cell(pad['x'], pad['y'])
            if not W.ok(j0, i0): continue
            dist = {(j0, i0): 0.0}; par = {}; pq = [(0.0, j0, i0)]
            while pq:
                g, j, i = heapq.heappop(pq)
                if g > dist[(j, i)] + 1e-9: continue
                if g > maxlen: break
                if not W.hard_via[j, i] and not inpad[j, i]:
                    if best is None or g < best[0]: best = (g, ln, (j, i), dict(par))
                    break
                for dj, di, c in ((0, 1, G), (1, 0, G), (0, -1, G), (-1, 0, G), (1, 1, G * 1.4142), (1, -1, G * 1.4142), (-1, 1, G * 1.4142), (-1, -1, G * 1.4142)):
                    nj, ni = j + dj, i + di
                    if not W.ok(nj, ni) or hard[nj, ni]: continue
                    if dj and di and (hard[j, ni] or hard[nj, i]): continue
                    if g + c < dist.get((nj, ni), 1e9): dist[(nj, ni)] = g + c; par[(nj, ni)] = (j, i); heapq.heappush(pq, (g + c, nj, ni))
        if best is None: continue
        g, ln, cell, par = best
        path = [cell]
        while path[-1] in par: path.append(par[path[-1]])
        path.reverse()
        pts = [path[0]] + [q for p, q, r in zip(path, path[1:], path[2:]) if (q[0] - p[0], q[1] - p[1]) != (r[0] - q[0], r[1] - q[1])] + [path[-1]]
        xy = [(pad['x'], pad['y'])] + [W.xy(*c) for c in pts[1:]]
        for (ax, ay), (cx, cy) in zip(xy, xy[1:]):
            if (ax, ay) != (cx, cy): B.add_track(ax, ay, cx, cy, w, ln, net)
        vx, vy = W.xy(*cell); B.add_via(vx, vy, net)
        return vx, vy, g, w
    return None

def has_via(B, net, pad, reach):
    """A via of the net that touches the pad or a track starting in it, within reach of the pad centre."""
    bx0, by0, bx1, by1 = pad['box']
    stubs = [t for t in B.tracks if t[6] == net and t[5] in pad['layers'] and
             any(bx0 - 0.002 <= ex <= bx1 + 0.002 and by0 - 0.002 <= ey <= by1 + 0.002 for ex, ey in ((t[0], t[1]), (t[2], t[3])))]
    pieces = None
    for (vx, vy, r, dr, n) in B.vias:
        if n != net or math.hypot(vx - pad['x'], vy - pad['y']) > reach + r: continue
        if box_d(np.array(vx), np.array(vy), bx0, by0, bx1, by1) < r: return True
        if any(seg_d(np.array(vx), np.array(vy), *t[:4]) < r + t[4] for t in stubs): return True
        if pieces is None: pieces = pad_pieces(B, net, pad)
        if any(pc.Contains(VECTOR2I(FromMM(vx), FromMM(vy))) for pc in pieces): return True
    return False

# ---------------------------------------------------------------------------------------------- direct links (maze)
def link(B, net, a, b, limit):
    """Route a track from pad a to pad b of `net`, not longer than `limit` (mm, vias counted VIA_COST each). Returns the
    list of added items or None."""
    for w in LINK_W:
        m = max(3.0, (limit - math.hypot(a['x'] - b['x'], a['y'] - b['y'])) / 2 + 0.5)
        x0, x1 = min(a['x'], b['x']) - m, max(a['x'], b['x']) + m; y0, y1 = min(a['y'], b['y']) - m, max(a['y'], b['y']) + m
        W = Window(B, net, x0, y0, x1, y1, w)
        def cells(p):
            bx0, by0, bx1, by1 = p['box']; s = max(0.0, min(w / 2 - 0.02, (bx1 - bx0) / 2 - 0.01, (by1 - by0) / 2 - 0.01))
            m = (W.X >= bx0 + s) & (W.X <= bx1 - s) & (W.Y >= by0 + s) & (W.Y <= by1 - s)
            out = set()
            for ln in p['layers']:
                if ln not in W.L: continue
                k = W.L.index(ln); js, is_ = np.nonzero(m)
                if not len(js): js, is_ = [W.cell(p['x'], p['y'])[0]], [W.cell(p['x'], p['y'])[1]]
                out |= {(k, int(j), int(i)) for j, i in zip(js, is_) if W.ok(j, i)}
            return out
        src, dst = cells(a), cells(b)
        for (k, j, i) in src | dst: W.hard[k, j, i] = False
        goal = {(j, i) for (_, j, i) in dst}
        gx, gy = b['x'], b['y']
        hfun = lambda j, i: math.hypot(W.X[j, i] - gx, W.Y[j, i] - gy)
        best = {}; parent = {}; pq = []
        for s in src: best[s] = 0.0; heapq.heappush(pq, (hfun(s[1], s[2]), 0.0, s))
        steps = [(0, 1, G), (1, 0, G), (0, -1, G), (-1, 0, G), (1, 1, G * 1.4142), (1, -1, G * 1.4142), (-1, 1, G * 1.4142), (-1, -1, G * 1.4142)]
        found = None
        while pq:
            f, g, cur = heapq.heappop(pq)
            if g > best.get(cur, 1e9) + 1e-9: continue
            if cur in dst: found = cur; break
            if f > limit: break
            k, j, i = cur
            for dj, di, c in steps:
                nj, ni = j + dj, i + di
                if not W.ok(nj, ni) or W.hard[k, nj, ni]: continue
                if dj and di and (W.hard[k, j, ni] or W.hard[k, nj, i]): continue
                nxt = (k, nj, ni); ng = g + c
                if ng < best.get(nxt, 1e9): best[nxt] = ng; parent[nxt] = cur; heapq.heappush(pq, (ng + hfun(nj, ni), ng, nxt))
            if not W.hard_via[j, i]:
                for k2 in range(len(W.L)):
                    if k2 == k or W.hard[k2, j, i]: continue
                    nxt = (k2, j, i); ng = g + VIA_COST
                    if ng < best.get(nxt, 1e9): best[nxt] = ng; parent[nxt] = cur; heapq.heappush(pq, (ng + hfun(j, i), ng, nxt))
        if found is None: continue
        path = [found]
        while path[-1] in parent: path.append(parent[path[-1]])
        path.reverse()
        path = path[max(n for n, c in enumerate(path) if c in src):]
        items = []
        def P(c, end=None):
            if end is not None: return end['x'], end['y']
            return W.xy(c[1], c[2])
        run = [path[0]]
        def flush(run, first, last):
            if len(run) < 2: return
            pts = [run[0]]
            for p, q, r in zip(run, run[1:], run[2:]):
                if (q[1] - p[1], q[2] - p[2]) != (r[1] - q[1], r[2] - q[2]): pts.append(q)
            pts.append(run[-1])
            for n_, (p, q) in enumerate(zip(pts, pts[1:])):
                (ax, ay) = P(p, a if (n_ == 0 and first) else None); (bx, by) = P(q, b if (n_ == len(pts) - 2 and last) else None)
                items.append(('track', ax, ay, bx, by, w, W.L[p[0]], net))
        first = True
        for p, q in zip(path, path[1:]):
            if q[0] != p[0]:
                flush(run, first, False); first = False
                x, y = W.xy(p[1], p[2]); items.append(('via', x, y, net)); run = [q]
            else: run.append(q)
        flush(run, first, True)
        for it in items:
            if it[0] == 'via': B.add_via(it[1], it[2], net)
            else: B.add_track(*it[1:])
        return items, w
    return None

# ---------------------------------------------------------------------------------------------- twins of single vias
def bridges(B, net):
    """Vias of `net` whose removal splits the pads of the net."""
    vias = [v for v in B.vias if v[4] == net]
    pads = [p for p in B.pads if p['net'] == net]
    segs = [t for t in B.tracks if t[6] == net]
    def comps(skip):
        parent = {}
        def f(x):
            parent.setdefault(x, x)
            while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
            return x
        def u(a, b): parent[f(a)] = f(b)
        keyed = [(('t', k), t) for k, t in enumerate(segs)]
        for k, t in keyed: f(k)
        def touches_seg(x, y, r, t): return seg_d(np.array(x), np.array(y), *t[:4]) <= r + t[4] + 0.002
        for k1, (k, t) in enumerate(keyed):                 # tracks that share an end on a layer
            for k2 in range(k1 + 1, len(keyed)):
                kk, s = keyed[k2]
                if s[5] != t[5]: continue
                if any(math.hypot(ex - fx, ey - fy) < 0.002 for ex, ey in ((t[0], t[1]), (t[2], t[3])) for fx, fy in ((s[0], s[1]), (s[2], s[3]))) \
                        or touches_seg(t[0], t[1], 0, s) or touches_seg(t[2], t[3], 0, s) or touches_seg(s[0], s[1], 0, t) or touches_seg(s[2], s[3], 0, t):
                    u(k, kk)
        for n, v in enumerate(vias):
            if n == skip: continue
            for k, t in keyed:
                if touches_seg(v[0], v[1], v[2], t): u(('v', n), k)
        for m, p in enumerate(pads):
            bx0, by0, bx1, by1 = p['box']
            for k, t in keyed:
                if t[5] in p['layers'] and any(bx0 - 0.002 <= ex <= bx1 + 0.002 and by0 - 0.002 <= ey <= by1 + 0.002 for ex, ey in ((t[0], t[1]), (t[2], t[3]))):
                    u(('p', m), k)
            if p['hole'] > 0:
                for n, v in enumerate(vias):
                    if n != skip and math.hypot(v[0] - p['x'], v[1] - p['y']) < v[2] + p['hole']: u(('p', m), ('v', n))
        return len({f(('p', m)) for m in range(len(pads))})
    base = comps(None)
    return [v for n, v in enumerate(vias) if comps(n) > base]

def twin(B, v, net, width):
    """A second via 0.8-1.2 mm from via v, joined to it by a track on each layer where v has a track."""
    vx, vy, r, dr, n = v
    layers = sorted({t[5] for t in B.tracks if t[6] == net and seg_d(np.array(vx), np.array(vy), *t[:4]) <= r + t[4] + 0.002})
    if len(layers) < 2: return None
    w = min(width, 0.4)
    W = Window(B, net, vx - 2, vy - 2, vx + 2, vy + 2, w)
    for dist in (0.8, 1.0, 1.2):
        for k in range(24):
            a = 2 * math.pi * k / 24; px, py = vx + dist * math.cos(a), vy + dist * math.sin(a)
            j, i = W.cell(px, py)
            if not W.ok(j, i) or W.hard_via[j, i]: continue
            px, py = W.xy(j, i); good = True
            for ln in layers:
                if ln not in W.L: good = False; break
                kk = W.L.index(ln)
                for s in np.linspace(0, 1, int(dist / (G / 2)) + 2):
                    x, y = vx + (px - vx) * s, vy + (py - vy) * s
                    if math.hypot(x - vx, y - vy) < r: continue
                    jj, ii = W.cell(x, y)
                    if not W.ok(jj, ii) or W.hard[kk, jj, ii]: good = False; break
                if not good: break
            if good:
                B.add_via(px, py, net)
                for ln in layers: B.add_track(vx, vy, px, py, w, ln, net)
                return px, py, layers
    return None

# ---------------------------------------------------------------------------------------------- rule check
DRC = r'''
import sys, os, re, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
pcbnew.WriteDRCReport(b, sys.argv[2], pcbnew.EDA_UNITS_MILLIMETRES, True)
pts, n, opens = [], 0, 0
for blk in re.split(r'\n(?=\[)', open(sys.argv[2]).read()):
    if 'Severity: error' not in blk: continue
    if blk.startswith('[unconnected_items]'): opens += 1; continue
    n += 1; pts += [(float(a), float(c)) for a, c in re.findall(r'@\(([0-9.\-]+) mm, ([0-9.\-]+) mm\)', blk)]
print(json.dumps([n, opens, pts])); sys.stdout.flush(); os._exit(0)
'''

def check(path):
    rep = os.path.join(tempfile.mkdtemp(prefix='decap_'), 'drc.txt')
    r = subprocess.run([sys.executable, '-c', DRC, path, rep], capture_output=True, text=True)
    return json.loads([l for l in r.stdout.splitlines() if l.startswith('[')][-1])

def write(path, added):
    b = pcbnew.LoadBoard(path); add_items(b, added); pcbnew.SaveBoard(path, b)

def add_items(b, added):
    """Add the items ('via', x, y, net) / ('track', x1, y1, x2, y2, w, layer, net) to a loaded board."""
    nets = {}
    for it in added:
        net = it[-1]
        ni = nets.setdefault(net, b.FindNet(net))
        if it[0] == 'via':
            v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(it[1]), FromMM(it[2]))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetWidth(FromMM(2 * VR)); v.SetDrill(FromMM(2 * DR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); b.Add(v)
        else:
            t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(FromMM(it[1]), FromMM(it[2]))); t.SetEnd(VECTOR2I(FromMM(it[3]), FromMM(it[4])))
            t.SetWidth(FromMM(it[5])); t.SetLayer(b.GetLayerID(it[6])); t.SetNet(ni); b.Add(t)

# ---------------------------------------------------------------------------------------------- main
def main():
    decap = getattr(D, 'DECAP', None)
    if not decap: print('decap_links: the design has no DECAP; nothing to do'); return 0
    board = pcbnew.LoadBoard(args.pcb); B = Board(board)
    groups = collections.defaultdict(list)                 # (kind, outcome) -> [text]
    # 1 plane vias at the capacitors and their pins
    for cref, (pref, pins) in sorted(decap.items(), key=lambda kv: kv[0]):
        cap_pads = [p for p in B.pads if p['ref'] == cref]
        for p in cap_pads + [B.pad(pref, n) for n in pins]:
            if p['net'] not in B.plane_nets: continue
            if has_via(B, p['net'], p, args.reach): continue
            spot = via_near(B, p['net'], p, args.reach)
            tag = '%s.%s %s' % (p['ref'], p['num'], p['net'])
            if spot: B.add_via(spot[0], spot[1], p['net']); groups[('plane via', 'added')].append('%s at (%.2f, %.2f)' % (tag, spot[0], spot[1])); continue
            res = via_stub(B, p['net'], p)
            if res: groups[('plane via', 'added with a track')].append('%s at (%.2f, %.2f), %.2f mm of %.2f mm track' % ((tag,) + res))
            else: groups[('plane via', 'no room')].append(tag)
    # 2 direct links where the copper loop is long
    for cref, (pref, pins) in sorted(decap.items(), key=lambda kv: kv[0]):
        cp = B.pad(cref, '1'); net = cp['net']
        cand = [B.pad(pref, n) for n in pins]
        pin = min(cand, key=lambda p: math.hypot(p['x'] - cp['x'], p['y'] - cp['y']))
        if net in B.plane_nets and has_via(B, net, cp, args.reach) and has_via(B, net, pin, args.reach): continue
        L, nv = path_len(B, net, pin, cp)
        straight = math.hypot(pin['x'] - cp['x'], pin['y'] - cp['y'])
        if L <= max(args.loop, 1.6 * straight + 1.0): continue
        # any route this short beats the one there; the maze counts a via as VIA_COST of track, and two are allowed for
        limit = min(L - 1.0, max(2 * args.loop, 2 * straight + 2.0, 0.2 * L)) + 2 * VIA_COST
        mark = len(B.added)
        res = link(B, net, pin, cp, limit)
        tag = '%s.%s-%s %s (was %.1f mm, %d vias)' % (pin['ref'], pin['num'], cref, net, L, nv)
        now = path_len(B, net, pin, cp)[0] if res else L
        if res and now > L - 1.0:                          # no real gain: take it out again
            undo(B, mark); res = None
        if res: groups[('link', 'added')].append(tag + ', now %.1f mm of %.2f mm track' % (now, res[1]))
        else: groups[('link', 'no room')].append(tag)
    # 3 the design's own additions
    extra = getattr(D, 'DECAP_EXTRA', {})
    for net, x, y, rad, why in extra.get('vias', ()):
        spot = via_at(B, net, x, y, rad)
        if spot: B.add_via(spot[0], spot[1], net); groups[('extra via', 'added')].append('%s at (%.2f, %.2f): %s' % (net, spot[0], spot[1], why))
        else: groups[('extra via', 'no room')].append('%s near (%.2f, %.2f): %s' % (net, x, y, why))
    for ra, pa, rb, pb, why in extra.get('links', ()):
        a, b = B.pad(ra, pa), B.pad(rb, pb)
        L, nv = path_len(B, a['net'], a, b); straight = math.hypot(a['x'] - b['x'], a['y'] - b['y'])
        lim = min(L - 1.0, max(2 * args.loop, 2 * straight + 2.0, 0.2 * L)) + 2 * VIA_COST
        res = link(B, a['net'], a, b, lim) if L > max(args.loop, 1.6 * straight + 1.0) else 'short'
        tag = '%s.%s-%s.%s %s (was %.1f mm): %s' % (ra, pa, rb, pb, a['net'], L, why)
        groups[('extra link', 'already short' if res == 'short' else 'added' if res else 'no room')].append(tag)
    # 4 twins of the single vias of the supply nets
    for net, wid in sorted(getattr(D, 'NET_WIDTH', {}).items()):
        if net in B.plane_nets: continue
        for v in bridges(B, net):
            res = twin(B, v, net, wid)
            tag = '%s via (%.2f, %.2f)' % (net, v[0], v[1])
            if res: groups[('twin via', 'added')].append(tag + ' -> (%.2f, %.2f) on %s' % (res[0], res[1], '/'.join(res[2])))
            else: groups[('twin via', 'no room')].append(tag)
    for (kind, out), items in sorted(groups.items()):
        print('%s, %s: %d' % (kind, out, len(items)))
        for t in items: print('   ', t)
    if args.dry or not B.added:
        print('decap_links: %d items%s' % (len(B.added), ' (dry run)' if args.dry else '')); sys.stdout.flush(); os._exit(0)
    n0, o0, _ = check(args.pcb)
    added = list(B.added)
    for rnd in range(3):
        trial = os.path.join(tempfile.mkdtemp(prefix='decap_'), os.path.basename(args.pcb))
        import shutil
        shutil.copy(args.pcb, trial)
        pro = os.path.splitext(args.pcb)[0] + '.kicad_pro'
        if os.path.exists(pro): shutil.copy(pro, os.path.splitext(trial)[0] + '.kicad_pro')
        write(trial, added)
        n1, o1, pts = check(trial)
        if n1 <= n0 and o1 <= o0:
            shutil.copy(trial, args.pcb); break
        def near(it):
            xs = [(it[1], it[2])] if it[0] == 'via' else [(it[1], it[2]), (it[3], it[4]), ((it[1] + it[3]) / 2, (it[2] + it[4]) / 2)]
            return any(math.hypot(x - px, y - py) < 0.8 for x, y in xs for px, py in pts)
        bad = [it for it in added if near(it)]
        print('  round %d: %d rule errors (were %d), %d open (were %d); taking out %d additions next to them' % (rnd, n1, n0, o1, o0, len(bad)))
        added = [it for it in added if it not in bad]
    else:
        print('decap_links: still rule errors after 3 rounds; board left as it was'); sys.stdout.flush(); os._exit(1)
    print('decap_links: %d vias and %d tracks added; rule errors %d, open %d' % (sum(1 for it in added if it[0] == 'via'),
          sum(1 for it in added if it[0] == 'track'), n1, o1))
    sys.stdout.flush(); os._exit(0)

if __name__ == '__main__':
    main()
