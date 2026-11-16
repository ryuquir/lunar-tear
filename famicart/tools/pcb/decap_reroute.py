#!/usr/bin/env python3
"""Make room for the decoupling links decap_links.py cannot place, by moving a few signal tracks (designs with DECAP).

Why: on rev H most DVDD pins (+1V1, no plane) are on F.Cu, their 100 nF on B.Cu right behind them, and every spot for
the via between them is taken by In3 tracks and signal vias that pass under the QFN's pin rows. decap_links.py adds
copper only where there is room, so 20 of the 24 DVDD pins kept a pin-to-capacitor path of 6-91 mm. This tool routes
the link anyway and moves what is in its way, one pin at a time, as a transaction on a copy of the board:
  1 a maze route pin -> capacitor (0.2 mm, 0.15 mm where 0.2 does not fit; vias as needed) in which the tracks and vias
    of ordinary signal nets are not walls but cost (crossing one costs about as much as 3 mm of track), so the route
    crosses as few as it can; tracks and vias of plane nets, supply nets (NET_WIDTH, +5V), crystal, feedback, switch
    node and USB nets, --protect nets and the design's VIA_NUDGE vias, pads, rule areas and the board edge stay walls;
  2 the signal tracks and vias the route touches are taken out, the route is added;
  3 finish_route.py --no-rip --only <those nets> routes them again in the free room, then finish_route.py
    --cleanup-only takes out the stubs left over; if that leaves a connection open, a second try takes out every
    track and via of those nets and routes them again from their pads;
  4 the copy is kept only if the board has no open connection and no rule error, and every moved net grew by at most
    --grow mm (default 6) of track and the moved nets together by at most 2 x --grow; else it is thrown away, and the
    route is looked for again with the nets that could not be moved as walls (3 routes per pair at most).
Pairs: every DECAP capacitor of a net without a plane whose track path to its nearest pin is longer than --loop
(3.0 mm) and 1.6 x the straight distance + 1 mm; with --planes also the plane-net capacitors (their pin -> capacitor
link, for pins that got no plane via). Run it on the routed board before finish_package.sh (it changes the routing;
finish_package.sh's decap_links.py then finds these pairs short).
    FC_DESIGN=design_revh python3 decap_reroute.py board.kicad_pcb [--only U3.51,U4.32] [--grow 6] [--planes] [--dry]
Prints per pair what it moved and the result."""
import os, sys, math, heapq, json, shutil, argparse, tempfile, subprocess, importlib, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ap = argparse.ArgumentParser()
ap.add_argument('pcb'); ap.add_argument('--dry', action='store_true'); ap.add_argument('--planes', action='store_true')
ap.add_argument('--only', default='', help='pins REF.PAD to try, comma-separated (default: every long pair)')
ap.add_argument('--protect', default='', help='nets whose tracks are never moved, comma-separated')
ap.add_argument('--grow', type=float, default=6.0); ap.add_argument('--loop', type=float, default=3.0)
ap.add_argument('--max-nets', type=int, default=3, help='a route that would move more signal nets than this is not tried')
ap.add_argument('--one', default='', help='(internal) work on this one pin REF.PAD of the board in place; the driver runs one child per pair')
args = ap.parse_args() if __name__ == '__main__' else None
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I
import decap_links as DL
D = DL.D
C, VR, DR, G = DL.C, DL.VR, DL.DR, DL.G
CROSS = 3.0                 # mm of track a crossed signal track or via is worth
PROTECT = set(filter(None, args.protect.split(','))) if args else set()

def fixed_net(B, n):
    """Nets whose copper is never moved."""
    return (not n or n in B.plane_nets or n in getattr(D, 'NET_WIDTH', {}) or n in ('+5V',) or n in PROTECT
            or n.startswith(('XIN', 'XOUT', 'FB_', 'SW_', 'USB_')))

MEASURE = r'''
import sys, json, os
sys.path.insert(0, sys.argv[1]); sys.argv = sys.argv[:1] + sys.argv[2:]
q = json.load(open(sys.argv[2]))
import decap_reroute as R, decap_links as DL, pcbnew
out = {'len': dict(R.net_len(sys.argv[1], set(q['nets'])))}
if q.get('net'):
    B = DL.Board(pcbnew.LoadBoard(sys.argv[1]))
    out['path'] = DL.path_len(B, q['net'], B.pad(q['pin'][0], q['pin'][1]), B.pad(q['cap'], '1'))[0]
print('MEASURE ' + json.dumps(out)); sys.stdout.flush(); os._exit(0)
'''

def measure(path, nets, net=None, pin=None, cap=None):
    """(track length per net, pin -> capacitor path) of a board file, read in a child process."""
    q = os.path.join(tempfile.mkdtemp(prefix='dreroute_m_'), 'q.json')
    json.dump({'nets': sorted(nets), 'net': net, 'pin': pin, 'cap': cap}, open(q, 'w'))
    r = subprocess.run([sys.executable, '-c', MEASURE, HERE, path, q], capture_output=True, text=True, env=dict(os.environ))
    line = [l for l in r.stdout.splitlines() if l.startswith('MEASURE ')]
    if not line: raise SystemExit('decap_reroute: measuring failed: %s' % (r.stderr.strip().splitlines() or ['?'])[-1])
    m = json.loads(line[-1][8:])
    return collections.Counter(m['len']), m.get('path')

def net_len(path, nets):
    b = pcbnew.LoadBoard(path); out = collections.Counter()
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA' and t.GetNetname() in nets: out[t.GetNetname()] += ToMM(t.GetLength())
    return out

STATE = r'''
import sys, re, json, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
pcbnew.WriteDRCReport(b, sys.argv[2], pcbnew.EDA_UNITS_MILLIMETRES, True)
opens, errs = [], []
for blk in re.split(r'\n(?=\[)', open(sys.argv[2]).read()):
    if 'Severity: error' not in blk: continue
    (opens if blk.startswith('[unconnected_items]') else errs).append(blk.split('\n')[0][:120])
print(json.dumps([opens, errs])); sys.stdout.flush(); os._exit(0)
'''

def state(path):
    rep = os.path.join(tempfile.mkdtemp(prefix='dreroute_'), 'drc.txt')
    r = subprocess.run([sys.executable, '-c', STATE, path, rep], capture_output=True, text=True)
    return json.loads([l for l in r.stdout.splitlines() if l.startswith('[')][-1])

def soft_masks(B, W, rip, w):
    """Per rippable item: (layer index, 'all' (a via) or None (a layer the maze does not use), cells where a track of
    width w may not be, cells where a new via may not be, width of the track keep-out in cells)."""
    out = []
    tw = w / 2 + C + DL.EPS; vw = VR + C + DL.EPS
    for it in rip:
        if it[0] == 'track':
            ax, ay, bx, by, hw, ln, n = it[1]
            d = DL.seg_d(W.X, W.Y, ax, ay, bx, by)
            out.append((W.L.index(ln) if ln in W.L else None, d < hw + tw, d < hw + vw, 2 * (hw + tw) / G))
        else:
            vx, vy, r, dr, n = it[1]
            d = np.hypot(W.X - vx, W.Y - vy)
            out.append(('all', d < r + tw, (d < r + vw) | (d < dr + DR + DL.HOLE_GAP), 2 * (r + tw) / G))
    return out

def cap_copper(B, net, cap, reach=1.0):
    """End points (layer name or None for every layer, x, y, radius) of the copper of `net` joined to the capacitor pad
    within `reach` mm of track: the vias and the track ends. A link may end there instead of in the pad (on the
    capacitor's own via, typically), which spares it the last part of the way. Only via centres and track ends: a track
    that ended in the middle of another would join it in KiCad, but not in path_len()'s end-to-end model."""
    bx0, by0, bx1, by1 = cap['box']
    inpad = lambda x, y: bx0 - 0.002 <= x <= bx1 + 0.002 and by0 - 0.002 <= y <= by1 + 0.002
    segs = [t for t in B.tracks if t[6] == net]
    vias = [v for v in B.vias if v[4] == net]
    out, seen = [], set()
    todo = [((x, y), ln, 0.0) for t in segs if t[5] in cap['layers'] for (x, y), ln in (((t[0], t[1]), t[5]), ((t[2], t[3]), t[5])) if inpad(x, y)]
    todo += [((v[0], v[1]), None, 0.0) for v in vias if DL.box_d(np.array(v[0]), np.array(v[1]), bx0, by0, bx1, by1) < v[2]]
    while todo:
        (x, y), ln, d0 = todo.pop()
        key = (round(x, 3), round(y, 3), ln)
        if key in seen or d0 > reach: continue
        seen.add(key)
        for v in vias:                                   # a via at this point: every layer
            if math.hypot(v[0] - x, v[1] - y) <= v[2] and (round(v[0], 3), round(v[1], 3), None) not in seen:
                out.append((None, v[0], v[1], v[2] - 0.05)); seen.add((round(v[0], 3), round(v[1], 3), None))
                todo += [((t[0], t[1]), t[5], d0) for t in segs if math.hypot(t[0] - v[0], t[1] - v[1]) <= v[2]]
                todo += [((t[2], t[3]), t[5], d0) for t in segs if math.hypot(t[2] - v[0], t[3] - v[1]) <= v[2]]
        for t in segs:                                   # tracks that start here on this layer (or any layer from a via)
            if ln is not None and t[5] != ln: continue
            for (sx, sy), (ex, ey) in (((t[0], t[1]), (t[2], t[3])), ((t[2], t[3]), (t[0], t[1]))):
                if math.hypot(sx - x, sy - y) > 0.002 and not (ln is None and any(math.hypot(sx - v[0], sy - v[1]) <= v[2] and math.hypot(v[0] - x, v[1] - y) < 0.002 for v in vias)): continue
                L = math.hypot(ex - sx, ey - sy)
                if d0 + L <= reach:                      # the far end of the track (links join tracks at their ends only)
                    out.append((t[5], ex, ey, t[4] - 0.03)); todo.append(((ex, ey), t[5], d0 + L))
    return out

def route(B, net, a, b, limit, rip):
    """Maze route a -> b on the signal layers where the rippable items cost CROSS each (per cell: a cell inside an item's
    keep-out costs CROSS / the keep-out's width in cells; a via inside one costs CROSS). It may end in the capacitor pad or on
    the copper joined to it within 1 mm (cap_copper). Returns (items, width, the rippable items the route touches) or
    None."""
    for w in DL.LINK_W:
        m = max(3.0, (limit - math.hypot(a['x'] - b['x'], a['y'] - b['y'])) / 2 + 0.5)
        x0, x1 = min(a['x'], b['x']) - m, max(a['x'], b['x']) + m; y0, y1 = min(a['y'], b['y']) - m, max(a['y'], b['y']) + m
        W = DL.Window(B, net, x0, y0, x1, y1, w)
        near = [it for it in rip if (it[0] == 'track' and min(it[1][0], it[1][2]) < x1 + 1 and max(it[1][0], it[1][2]) > x0 - 1
                                     and min(it[1][1], it[1][3]) < y1 + 1 and max(it[1][1], it[1][3]) > y0 - 1)
                or (it[0] == 'via' and x0 - 1 < it[1][0] < x1 + 1 and y0 - 1 < it[1][1] < y1 + 1)]
        masks = soft_masks(B, W, near, w)
        nL = len(W.L)
        cost = np.zeros((nL, W.ny, W.nx)); vcost = np.zeros((W.ny, W.nx))
        for lay, mt, mv, band in masks:                 # a track crossing an item's keep-out passes about `band` cells of it
            per = CROSS / max(1.0, band)
            if lay == 'all': cost += per * mt[None]
            elif lay is not None: cost[lay] += per * mt
            vcost += CROSS * mv
        def cells(p):
            bx0, by0, bx1, by1 = p['box']; s = max(0.0, min(w / 2 - 0.02, (bx1 - bx0) / 2 - 0.01, (by1 - by0) / 2 - 0.01))
            mk = (W.X >= bx0 + s) & (W.X <= bx1 - s) & (W.Y >= by0 + s) & (W.Y <= by1 - s)
            out = set()
            for ln in p['layers']:
                if ln not in W.L: continue
                k = W.L.index(ln); js, is_ = np.nonzero(mk)
                out |= {(k, int(j), int(i)) for j, i in zip(js, is_) if W.ok(j, i)}
            return out
        src, dst = cells(a), cells(b)
        if not src or not dst: continue
        for (k, j, i) in src | dst: W.hard[k, j, i] = False
        snap = {}                                        # goal cell on the capacitor's own copper -> exact end point
        for lay, px, py, rr in cap_copper(B, net, b):
            j0, i0 = W.cell(px, py); rc = max(0, int(rr / G))
            for k in ([W.L.index(lay)] if lay in W.L else range(nL) if lay is None else []):
                for j in range(j0 - rc, j0 + rc + 1):
                    for i in range(i0 - rc, i0 + rc + 1):
                        if W.ok(j, i) and not W.hard[k, j, i] and math.hypot(W.X[j, i] - px, W.Y[j, i] - py) <= rr and (k, j, i) not in dst:
                            dst.add((k, j, i)); snap[(k, j, i)] = (px, py)
        gx, gy = b['x'], b['y']
        hfun = lambda j, i: math.hypot(W.X[j, i] - gx, W.Y[j, i] - gy)
        best = {}; parent = {}; pq = []
        for s_ in src: best[s_] = 0.0; heapq.heappush(pq, (hfun(s_[1], s_[2]), 0.0, 0.0, s_))
        steps = [(0, 1, G), (1, 0, G), (0, -1, G), (-1, 0, G), (1, 1, G * 1.4142), (1, -1, G * 1.4142), (-1, 1, G * 1.4142), (-1, -1, G * 1.4142)]
        found = None
        while pq:
            f, g, glen, cur = heapq.heappop(pq)
            if g > best.get(cur, 1e9) + 1e-9: continue
            if cur in dst: found = cur; break
            if glen > limit: continue
            k, j, i = cur
            for dj, di, c in steps:
                nj, ni = j + dj, i + di
                if not W.ok(nj, ni) or W.hard[k, nj, ni]: continue
                if dj and di and (W.hard[k, j, ni] or W.hard[k, nj, i]): continue
                nxt = (k, nj, ni); ng = g + c + cost[k, nj, ni]
                if ng < best.get(nxt, 1e9): best[nxt] = ng; parent[nxt] = cur; heapq.heappush(pq, (ng + hfun(nj, ni), ng, glen + c, nxt))
            if not W.hard_via[j, i]:
                for k2 in range(nL):
                    if k2 == k or W.hard[k2, j, i]: continue
                    nxt = (k2, j, i); ng = g + DL.VIA_COST + vcost[j, i]
                    if ng < best.get(nxt, 1e9): best[nxt] = ng; parent[nxt] = cur; heapq.heappush(pq, (ng + hfun(j, i), ng, glen + DL.VIA_COST, nxt))
        if found is None: continue
        path = [found]
        while path[-1] in parent: path.append(parent[path[-1]])
        path.reverse()
        path = path[max(n for n, c_ in enumerate(path) if c_ in src):]
        items = []
        def P(c_, end=None):
            if end is not None: return (end['x'], end['y']) if c_ not in snap else snap[c_]
            return W.xy(c_[1], c_[2])
        def flush(run, first, last):
            if len(run) < 2: return
            pts = [run[0]] + [q for p_, q, r_ in zip(run, run[1:], run[2:]) if (q[1] - p_[1], q[2] - p_[2]) != (r_[1] - q[1], r_[2] - q[2])] + [run[-1]]
            for n_, (p_, q) in enumerate(zip(pts, pts[1:])):
                ax, ay = P(p_, a if (n_ == 0 and first) else None); bx, by = P(q, b if (n_ == len(pts) - 2 and last) else None)
                items.append(('track', ax, ay, bx, by, w, W.L[p_[0]], net))
        run = [path[0]]; first = True
        for p_, q in zip(path, path[1:]):
            if q[0] != p_[0]:
                flush(run, first, False); first = False
                x, y = W.xy(p_[1], p_[2]); items.append(('via', x, y, net)); run = [q]
            else: run.append(q)
        flush(run, first, True)
        # which rippable items does the route really touch (exact geometry, the board's clearance)
        hit = set()
        for n_, it in enumerate(near):
            for nw in items:
                if conflict(nw, it, w): hit.add(id(it)); break
        return items, w, [it for it in near if id(it) in hit]
    return None

def conflict(nw, it, w):
    """True if new item nw (('track', x1, y1, x2, y2, w, layer, net) or ('via', x, y, net)) is closer than the clearance
    to rippable item it (('track', (ax, ay, bx, by, hw, layer, net)) or ('via', (x, y, r, dr, net)))."""
    def segseg(a1, a2, b1, b2):
        f = lambda p, s1, s2: float(DL.seg_d(np.array(p[0]), np.array(p[1]), s1[0], s1[1], s2[0], s2[1]))
        return min(f(a1, b1, b2), f(a2, b1, b2), f(b1, a1, a2), f(b2, a1, a2))
    if nw[0] == 'track':
        p1, p2, hw, ln = (nw[1], nw[2]), (nw[3], nw[4]), nw[5] / 2, nw[6]
        if it[0] == 'track':
            ax, ay, bx, by, hw2, ln2, _ = it[1]
            return ln == ln2 and segseg(p1, p2, (ax, ay), (bx, by)) < hw + hw2 + C - 0.001
        vx, vy, r, dr, _ = it[1]
        return float(DL.seg_d(np.array(vx), np.array(vy), p1[0], p1[1], p2[0], p2[1])) < hw + r + C - 0.001
    x, y = nw[1], nw[2]
    if it[0] == 'track':
        ax, ay, bx, by, hw2, ln2, _ = it[1]
        return float(DL.seg_d(np.array(x), np.array(y), ax, ay, bx, by)) < VR + hw2 + C - 0.001
    vx, vy, r, dr, _ = it[1]
    d = math.hypot(x - vx, y - vy)
    return d < VR + r + C - 0.001 or d < DR + dr + DL.HOLE_GAP - 0.001

APPLY = r'''
import sys, json, os
sys.path.insert(0, sys.argv[1]); sys.argv = sys.argv[:1] + sys.argv[2:]
spec = json.load(open(sys.argv[2]))
import decap_reroute as R
n = R.apply_here(sys.argv[1], [(k, tuple(v)) for k, v in spec['remove']], [tuple(a) for a in spec['add']])
print('removed', n); sys.stdout.flush(); os._exit(0)
'''

def apply(path, remove, add):
    """apply_here() in a child process (KiCad's python breaks after many board loads in one process)."""
    spec = os.path.join(tempfile.mkdtemp(prefix='dreroute_apply_'), 'spec.json')
    json.dump({'remove': [[k, list(v)] for k, v in remove], 'add': [list(a) for a in add]}, open(spec, 'w'))
    r = subprocess.run([sys.executable, '-c', APPLY, HERE, path, spec], capture_output=True, text=True, env=dict(os.environ))
    if 'removed' not in r.stdout: raise SystemExit('decap_reroute: applying the change failed: %s' % (r.stderr.strip().splitlines() or ['?'])[-1])

def apply_here(path, remove, add):
    """Remove the board items `remove` (('track', tuple) / ('via', tuple), matched by geometry and net) and add `add`."""
    b = pcbnew.LoadBoard(path)
    want_t = {(round(t[1][0], 4), round(t[1][1], 4), round(t[1][2], 4), round(t[1][3], 4), t[1][5], t[1][6]) for t in remove if t[0] == 'track'}
    want_v = {(round(v[1][0], 4), round(v[1][1], 4), v[1][4]) for v in remove if v[0] == 'via'}
    gone = 0
    for t in list(b.GetTracks()):
        if t.GetClass() == 'PCB_VIA':
            k = (round(ToMM(t.GetPosition().x), 4), round(ToMM(t.GetPosition().y), 4), t.GetNetname())
            if k in want_v: b.Remove(t); gone += 1
        else:
            k = (round(ToMM(t.GetStart().x), 4), round(ToMM(t.GetStart().y), 4), round(ToMM(t.GetEnd().x), 4), round(ToMM(t.GetEnd().y), 4),
                 b.GetLayerName(t.GetLayer()), t.GetNetname())
            if k in want_t: b.Remove(t); gone += 1
    DL.add_items(b, add)                 # on the same loaded board: a second LoadBoard after Remove() can break
    pcbnew.SaveBoard(path, b)
    return gone

def main():
    decap = getattr(D, 'DECAP', None)
    if not decap: print('decap_reroute: the design has no DECAP; nothing to do'); return 0
    only = set(filter(None, args.only.split(',')))
    work = os.path.join(tempfile.mkdtemp(prefix='dreroute_work_'), os.path.basename(args.pcb))
    shutil.copy(args.pcb, work)
    pro = os.path.splitext(args.pcb)[0] + '.kicad_pro'
    if os.path.exists(pro): shutil.copy(pro, os.path.splitext(work)[0] + '.kicad_pro')
    if args.one:                                         # child: one pair, on the board in place (the driver's working copy)
        work = args.pcb; only = {args.one}
    else:
        opens0, errs0 = state(work)
        if opens0 or errs0:
            print('decap_reroute: the board has %d open connections and %d rule errors already; fix them first' % (len(opens0), len(errs0))); return 1
    board = pcbnew.LoadBoard(work); B = DL.Board(board)
    pairs = []
    for cref, (pref, pins) in sorted(decap.items()):
        cp = B.pad(cref, '1'); net = cp['net']
        if net in B.plane_nets and not args.planes: continue
        pin = min((B.pad(pref, n) for n in pins), key=lambda p: math.hypot(p['x'] - cp['x'], p['y'] - cp['y']))
        tag = '%s.%s' % (pin['ref'], pin['num'])
        if only and tag not in only: continue
        L, nv = DL.path_len(B, net, pin, cp); straight = math.hypot(pin['x'] - cp['x'], pin['y'] - cp['y'])
        if L <= max(args.loop, 1.6 * straight + 1.0): continue
        pairs.append((L, tag, cref, pin, cp, net, straight, nv))
    pairs.sort(key=lambda p: -p[0])
    kept = 0
    if not args.one:
        # driver: one child process per pair (KiCad's python breaks after a board has been loaded, filled and changed many
        # times in one process: LoadBoard then returns a bare SwigPyObject)
        print('decap_reroute: %d long pairs' % len(pairs)); sys.stdout.flush()
        flags = ['--grow', str(args.grow), '--loop', str(args.loop), '--max-nets', str(args.max_nets)] + (['--planes'] if args.planes else []) \
            + (['--protect', args.protect] if args.protect else []) + (['--dry'] if args.dry else [])
        for L, tag, *_ in pairs:
            r = subprocess.run([sys.executable, os.path.abspath(__file__), work, '--one', tag] + flags, capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if line.startswith('  '): print(line)
                if line.startswith('KEPT'): kept += 1
            if r.returncode: print('  %s: the child stopped (%d): %s' % (tag, r.returncode, (r.stderr.strip().splitlines() or ['?'])[-1][:200]))
            sys.stdout.flush()
        if kept and not args.dry: shutil.copy(work, args.pcb)
        print('decap_reroute: %d of %d pairs rerouted%s' % (kept, len(pairs), ' (dry run)' if args.dry else ''))
        return 0
    for L, tag, cref, pin0, cp0, net, straight, nv in pairs:
        pin, cp = B.pad(pin0['ref'], pin0['num']), B.pad(cref, '1')
        if L <= max(args.loop, 1.6 * straight + 1.0): print('  %s-%s: short now (%.1f mm)' % (tag, cref, L)); continue
        nudge = [(n, x, y) for n, x, y, dx, dy, why in getattr(D, 'VIA_NUDGE', ())]      # nudge_vias.py finds these by position
        pinned = lambda v: any(v[4] == n and abs(v[0] - x) < 0.02 and abs(v[1] - y) < 0.02 for n, x, y in nudge)
        limit = max(2 * args.loop, 2 * straight + 2.0, min(0.25 * L, 15.0)) + 2 * DL.VIA_COST   # a long present path allows a longer link
        keep_out = set()                 # nets that could not be moved for this pair: walls in the next alternative
        done = False
        for alt in range(3):
            stays = lambda n: fixed_net(B, n) or n == net or n in keep_out
            rip = [('track', t) for t in B.tracks if not stays(t[6])] + [('via', v) for v in B.vias if not stays(v[4]) and not pinned(v)]
            fixedB = DL.Board.__new__(DL.Board); fixedB.__dict__.update(B.__dict__)       # the walls of the maze
            fixedB.tracks = [t for t in B.tracks if stays(t[6])]
            fixedB.vias = [v for v in B.vias if stays(v[4]) or pinned(v)]; fixedB.added = []
            r = route(fixedB, net, pin, cp, limit, rip)
            if r is None:
                print('  %s-%s %s (%.1f mm): no route%s' % (tag, cref, net, L, ' even moving signal tracks' if not keep_out else ' without moving %s' % ', '.join(sorted(keep_out))))
                break
            items, w, hit = r
            moved = sorted({it[1][6] if it[0] == 'track' else it[1][4] for it in hit})
            if len(moved) > args.max_nets:
                print('  %s-%s %s (%.1f mm): route %d would move %d nets (%s), more than --max-nets %d' % (tag, cref, net, L, alt + 1, len(moved), ', '.join(moved), args.max_nets))
                break
            if args.dry:
                print('  %s-%s %s (%.1f mm): route of %d items at %.2f mm, would move %d items of %s' % (tag, cref, net, L, len(items), w, len(hit), ', '.join(moved)))
                break
            before = measure(work, set(moved))[0]
            whole = [('track', t) for t in B.tracks if t[6] in moved] + [('via', v) for v in B.vias if v[4] in moved]
            # try 1: take out only what the link touches; try 2: take out every track and via of the moved nets and route
            # them again from their pads (more room for them than around the stubs try 1 leaves)
            failed = set()
            for attempt, remove in ((1, hit), (2, whole)) if moved else ((1, hit),):
                trial = os.path.join(tempfile.mkdtemp(prefix='dreroute_try_'), os.path.basename(work))
                shutil.copy(work, trial)
                if os.path.exists(os.path.splitext(work)[0] + '.kicad_pro'): shutil.copy(os.path.splitext(work)[0] + '.kicad_pro', os.path.splitext(trial)[0] + '.kicad_pro')
                apply(trial, remove, items)
                env = dict(os.environ)
                if moved:
                    subprocess.run([sys.executable, os.path.join(HERE, 'finish_route.py'), trial, '--no-rip', '--only', ','.join(moved), '--rounds', '6'],
                                   env=env, capture_output=True, text=True)
                    subprocess.run([sys.executable, os.path.join(HERE, 'finish_route.py'), trial, '--cleanup-only'], env=env, capture_output=True, text=True)
                opens, errs = state(trial)
                after, Ln = measure(trial, set(moved), net, (pin['ref'], pin['num']), cref)
                grow = {n: after[n] - before[n] for n in moved}
                ok = not opens and not errs and all(g <= args.grow for g in grow.values()) and sum(grow.values()) <= 2 * args.grow
                txt = '  %s-%s %s: %.1f -> %.1f mm; route %d try %d moved %d items of %s (growth %s); open %d, errors %d -> %s' % (
                    tag, cref, net, L, Ln, alt + 1, attempt, len(remove), ', '.join(moved) or 'nothing', ', '.join('%s %+.1f' % kv for kv in sorted(grow.items())) or '-',
                    len(opens), len(errs), 'kept' if ok else 'thrown away')
                print(txt); sys.stdout.flush()
                if ok:
                    shutil.copy(trial, work); kept += 1; done = True; print('KEPT'); break
                # the nets to keep still next time: the ones that grew too much, or all moved ones when a connection stayed open
                failed |= {n for n, g in grow.items() if g > args.grow} if not opens and not errs else set(moved)
            if done or args.dry or not failed: break
            keep_out |= failed
    return 0

if __name__ == '__main__':
    rc = main(); sys.stdout.flush(); os._exit(rc)
