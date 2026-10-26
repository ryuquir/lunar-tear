#!/usr/bin/env python3
"""Finish the last few connections Freerouting left open, directly on the routed KiCad board.

Grid maze router (A*, 0.05 mm, all signal layers, through vias): every other-net copper item is an obstacle
inflated by clearance + half the new track width; same-net copper of the target island is the goal. For the
plane nets (GND on In1, +3V3 on the last inner layer) an island may also be finished by dropping a via anywhere
the plane reliably covers. Re-runs zone fill + DRC after each round.

  python3 finish_route.py board.kicad_pcb [--track 0.12] [--clear 0.1] [--via 0.5 --drill 0.2]
"""
import sys, re, math, heapq, os, argparse, tempfile
import numpy as np
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I

ap = argparse.ArgumentParser()
ap.add_argument('pcb'); ap.add_argument('--track', type=float, default=0.12); ap.add_argument('--clear', type=float, default=0.1)
ap.add_argument('--via', type=float, default=0.5); ap.add_argument('--drill', type=float, default=0.2)
ap.add_argument('--grid', type=float, default=0.05); ap.add_argument('--rounds', type=int, default=10)
args = ap.parse_args()
G = args.grid; W = args.track; C = args.clear; VR = args.via / 2; DR = args.drill / 2
BW, BH = 90.0, 35.4             # routable body; the grid also covers the card-edge tab (46.1 mm) so finger tracks are representable
NX, NY = int(round(BW / G)) + 1, int(round(46.2 / G)) + 1
PLANES = {'GND': 'In1.Cu', '+3V3': None}   # +3V3 layer filled in from the board

def drc(board):
    rep = os.path.join(tempfile.gettempdir(), 'finish_route_drc.txt')
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, False)
    return open(rep).read()

def unconnected_pairs(txt):
    out = []
    for blk in txt.split('\n['):
        if not blk.startswith('unconnected_items]'): continue
        m = re.findall(r'@\(([0-9.]+) mm, ([0-9.]+) mm\): ([^\n]*)', blk)
        if len(m) == 2: out.append([(float(a), float(b), d) for a, b, d in m])
    return out

def item_at(board, x, y, desc):
    net = re.search(r'\[([^\]]*)\]', desc).group(1)
    best = None; bd = 1e9
    if desc.startswith('Pad') or desc.startswith('PTH pad'):
        num = re.search(r'[Pp]ad (\S+) \[', desc).group(1); ref = re.search(r' of (\S+)', desc).group(1)
        fp = board.FindFootprintByReference(ref)
        for p in fp.Pads():
            if p.GetNumber() == num:
                d = math.hypot(ToMM(p.GetPosition().x) - x, ToMM(p.GetPosition().y) - y)
                if d < bd: bd, best = d, p
        return best
    for t in board.GetTracks():
        if t.GetNetname() != net: continue
        if t.GetClass() == 'PCB_VIA': d = math.hypot(ToMM(t.GetPosition().x) - x, ToMM(t.GetPosition().y) - y)
        else: d = min(math.hypot(ToMM(p.x) - x, ToMM(p.y) - y) for p in (t.GetStart(), t.GetEnd()))
        if d < bd: bd, best = d, t
    return best

def shapes_of(item):
    """[(kind, params, layers)] in mm; kind 'seg' (x1,y1,x2,y2,hw), 'circ' (x,y,r), 'box' (x0,y0,x1,y1)."""
    cls = item.GetClass()
    if cls == 'PCB_VIA':
        return [('circ', (ToMM(item.GetPosition().x), ToMM(item.GetPosition().y), ToMM(item.GetWidth()) / 2), 'ALL')]
    if cls in ('PCB_TRACK', 'PCB_ARC'):
        s, e = item.GetStart(), item.GetEnd()
        return [('seg', (ToMM(s.x), ToMM(s.y), ToMM(e.x), ToMM(e.y), ToMM(item.GetWidth()) / 2), item.GetLayer())]
    if cls == 'PAD':
        bb = item.GetBoundingBox()
        box = (ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))
        if item.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
            sh = ('circ', (ToMM(item.GetPosition().x), ToMM(item.GetPosition().y), ToMM(item.GetSize().x) / 2))
        else: sh = ('box', box)
        if item.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,) or item.GetDrillSize().x > 0: return [(sh[0], sh[1], 'ALL')]
        return [(sh[0], sh[1], lid) for lid in (pcbnew.F_Cu, pcbnew.B_Cu) if item.GetLayerSet().Contains(lid)]
    return []

def raster(arr, kind, p, infl):
    """Set arr cells whose centre lies within `infl` of the shape."""
    if kind == 'seg':
        x1, y1, x2, y2, hw = p; r = hw + infl
        x0, x1b, y0, y1b = min(x1, x2) - r, max(x1, x2) + r, min(y1, y2) - r, max(y1, y2) + r
    elif kind == 'circ':
        cx, cy, rr = p; r = rr + infl; x0, x1b, y0, y1b = cx - r, cx + r, cy - r, cy + r
    else:
        bx0, by0, bx1, by1 = p; x0, x1b, y0, y1b = bx0 - infl, bx1 + infl, by0 - infl, by1 + infl
    i0, i1 = max(0, int(math.floor(x0 / G))), min(NX - 1, int(math.ceil(x1b / G)))
    j0, j1 = max(0, int(math.floor(y0 / G))), min(NY - 1, int(math.ceil(y1b / G)))
    if i0 > i1 or j0 > j1: return
    xs = np.arange(i0, i1 + 1) * G; ys = np.arange(j0, j1 + 1) * G
    X, Y = np.meshgrid(xs, ys)
    if kind == 'seg':
        dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
        t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1) if L2 > 0 else 0
        d = np.hypot(X - (x1 + t * dx), Y - (y1 + t * dy)) - hw
    elif kind == 'circ':
        d = np.hypot(X - cx, Y - cy) - rr
    else:
        ddx = np.maximum(np.maximum(bx0 - X, X - bx1), 0); ddy = np.maximum(np.maximum(by0 - Y, Y - by1), 0); d = np.hypot(ddx, ddy)
    arr[j0:j1 + 1, i0:i1 + 1] |= (d <= infl)

def net_islands(board, net, sig_layers):
    """Connected components of the net's copper (grid overlap on a common layer; plane zones join every via /
    through-hole pad they cover). Returns {id(item): comp} and {comp: (items, on_plane)}."""
    items = [t for t in board.GetTracks() if t.GetNetname() == net]
    items += [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() == net]
    LID = {lid: k for k, lid in enumerate(sig_layers)}; nl = len(sig_layers)
    parent = list(range(len(items)))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    owner = {}
    for idx, it in enumerate(items):
        for kind, prm, lay in shapes_of(it):
            ls = range(nl) if lay == 'ALL' else ([LID[lay]] if lay in LID else [])
            tmp = np.zeros((NY, NX), bool); raster(tmp, kind, prm, 0.0)
            js, is_ = np.nonzero(tmp)
            for k in ls:
                for j, i in zip(js.tolist(), is_.tolist()):
                    o = owner.setdefault((k, j, i), idx)
                    if o != idx: parent[find(o)] = find(idx)
    plane_members = set()
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net: continue
        lay = z.GetFirstLayer(); polys = z.GetFilledPolysList(lay)
        for idx, it in enumerate(items):
            through = it.GetClass() == 'PCB_VIA' or (it.GetClass() == 'PAD' and it.GetDrillSize().x > 0)
            if through and polys.Contains(it.GetPosition()): plane_members.add(idx)
    pm = list(plane_members)
    for a in pm[1:]: parent[find(a)] = find(pm[0])
    comps = {}
    for idx, it in enumerate(items): comps.setdefault(find(idx), []).append(it)
    plane_root = find(pm[0]) if pm else None
    by_item = {}
    for root, its in comps.items():
        for it in its: by_item[it.m_Uuid.AsString()] = root
    return by_item, {r: (its, r == plane_root) for r, its in comps.items()}

def route_job(board, sig_layers, src_items, dst_items, net, plane_goal):
    LID = {lid: k for k, lid in enumerate(sig_layers)}
    nl = len(sig_layers)
    blk = np.zeros((nl, NY, NX), bool); viab = np.zeros((NY, NX), bool)
    holes = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0: holes.append((ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), ToMM(p.GetDrillSize().x) / 2))
            if p.GetNetname() == net: continue
            for kind, prm, lay in shapes_of(p):
                ls = range(nl) if lay == 'ALL' else ([LID[lay]] if lay in LID else [])
                for k in ls: raster(blk[k], kind, prm, C + W / 2 + 0.01)
                if lay == 'ALL' or lay in LID: raster(viab, kind, prm, C + VR + 0.01)
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA': holes.append((ToMM(t.GetPosition().x), ToMM(t.GetPosition().y), ToMM(t.GetDrillValue()) / 2))
        if t.GetNetname() == net: continue
        for kind, prm, lay in shapes_of(t):
            ls = range(nl) if lay == 'ALL' else ([LID[lay]] if lay in LID else [])
            for k in ls: raster(blk[k], kind, prm, C + W / 2 + 0.01)
            raster(viab, kind, prm, C + VR + 0.01)
    for (hx, hy, hr) in holes: raster(viab, 'circ', (hx, hy, hr), 0.25 + DR + 0.01)    # hole-to-hole
    # board edge / tab: keep 0.35 mm from the body outline, never below the body
    edge = np.zeros((NY, NX), bool); m = int(math.ceil((0.3 + W / 2) / G))
    edge[:m, :] = True; edge[:, :m] = True; edge[:, -m:] = True; edge[int((BH - 0.3 - W / 2) / G):, :] = True
    blk |= edge[None]; viab |= np.zeros_like(viab) | edge
    vm = int(math.ceil((0.3 + VR) / G)); viab[:vm, :] = True; viab[:, :vm] = True; viab[:, -vm:] = True; viab[int((BH - 0.3 - VR) / G):, :] = True
    # sources / targets
    def cells_of(items, shrink):
        out = set()
        for it in items:
            if it.GetClass() == 'ZONE': continue
            for kind, prm, lay in shapes_of(it):
                if it.GetClass() in ('PCB_TRACK', 'PCB_ARC'):        # only track end points (T-junctions are not connections)
                    x1, y1, x2, y2, hw = prm
                    for (ex, ey) in ((x1, y1), (x2, y2)):
                        k = LID.get(lay)
                        if k is None: continue
                        out.add((k, int(round(ey / G)), int(round(ex / G))))
                    continue
                tmp = np.zeros((NY, NX), bool)
                if kind == 'box': prm = (prm[0] + shrink, prm[1] + shrink, prm[2] - shrink, prm[3] - shrink)
                if kind == 'circ': prm = (prm[0], prm[1], max(prm[2] - shrink, 0.0))
                raster(tmp, kind, prm, 0.0)
                js, is_ = np.nonzero(tmp)
                ls = range(nl) if lay == 'ALL' else ([LID[lay]] if lay in LID else [])
                for k in ls:
                    for j, i in zip(js, is_): out.add((k, int(j), int(i)))
        return out
    src = cells_of(src_items, 0.04); dst = cells_of(dst_items, 0.04) if dst_items else set()
    for (k, j, i) in src | dst: blk[k, j, i] = False                     # own copper is always enterable
    if not src: return None
    # plane goal: any via-able cell well inside the plane outline
    PM = 1.3
    def is_goal(k, j, i):
        if (k, j, i) in dst: return True
        if plane_goal and not viab[j, i] and PM / G <= i <= (BW - PM) / G and PM / G <= j <= (BH - 0.5 - PM) / G: return True
        return False
    # A* (heuristic: distance to the nearest destination cell; 0 for plane goals)
    dl = list(dst)
    def h(j, i):
        if plane_goal or not dl: return 0.0
        return min(math.hypot(j - dj, i - di) for (_, dj, di) in dl[:: max(1, len(dl) // 64)])
    VIA_COST = 30.0
    openq = []; gbest = {}; parent = {}
    for s in src:
        gbest[s] = 0.0; heapq.heappush(openq, (h(s[1], s[2]), 0.0, s))
    steps = [(0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    goal = None; it = 0
    while openq:
        f, g, cur = heapq.heappop(openq)
        if g > gbest.get(cur, 1e18) + 1e-9: continue
        k, j, i = cur
        if g > 0 and is_goal(k, j, i): goal = cur; break
        it += 1
        if it > 8_000_000: break
        for dj, di, c in steps:
            nj, ni = j + dj, i + di
            if not (0 <= nj < NY and 0 <= ni < NX) or blk[k, nj, ni]: continue
            if dj and di and (blk[k, j, ni] or blk[k, nj, i]): continue
            nxt = (k, nj, ni); ng = g + c
            if ng < gbest.get(nxt, 1e18): gbest[nxt] = ng; parent[nxt] = cur; heapq.heappush(openq, (ng + h(nj, ni), ng, nxt))
        if not viab[j, i]:
            for k2 in range(nl):
                if k2 == k or blk[k2, j, i]: continue
                nxt = (k2, j, i); ng = g + VIA_COST
                if ng < gbest.get(nxt, 1e18): gbest[nxt] = ng; parent[nxt] = cur; heapq.heappush(openq, (ng + h(j, i), ng, nxt))
    if goal is None:
        # report how boxed-in each end is (reachable cells), so the caller can rip up around the trapped end
        def reach(cells, cap=6000):
            seen = set(cells); q = list(cells)
            while q and len(seen) < cap:
                k, j, i = q.pop()
                for dj, di, _ in steps[:4]:
                    n = (k, j + dj, i + di)
                    if 0 <= n[1] < NY and 0 <= n[2] < NX and n not in seen and not blk[n]: seen.add(n); q.append(n)
                if not viab[j, i]:
                    for k2 in range(nl):
                        n = (k2, j, i)
                        if n not in seen and not blk[n]: seen.add(n); q.append(n)
            return len(seen)
        return ('fail', reach(src), reach(dst) if dst else 99999)
    path = [goal]
    while path[-1] in parent: path.append(parent[path[-1]])
    path.reverse()
    plane_via = plane_goal and goal not in dst
    return path, plane_via

def emit(board, path, plane_via, net, sig_layers):
    ni = board.FindNet(net); n_t = n_v = 0
    def P(j, i): return VECTOR2I(FromMM(i * G), FromMM(j * G))
    def add_via(j, i):
        v = pcbnew.PCB_VIA(board); v.SetPosition(P(j, i)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(FromMM(2 * VR)); v.SetDrill(FromMM(2 * DR))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); board.Add(v)
    run = [path[0]]
    def flush(run):
        nonlocal n_t
        if len(run) < 2: return
        pts = [run[0]]
        for a, b, c in zip(run, run[1:], run[2:]):
            if (b[1] - a[1], b[2] - a[2]) != (c[1] - b[1], c[2] - b[2]): pts.append(b)
        pts.append(run[-1])
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board); t.SetStart(P(a[1], a[2])); t.SetEnd(P(b[1], b[2])); t.SetWidth(FromMM(W)); t.SetLayer(sig_layers[a[0]]); t.SetNet(ni); board.Add(t); n_t += 1
    for a, b in zip(path, path[1:]):
        if b[0] != a[0]: flush(run); add_via(a[1], a[2]); n_v += 1; run = [b]
        else: run.append(b)
    flush(run)
    if plane_via: add_via(path[-1][1], path[-1][2]); n_v += 1
    return n_t, n_v

def main():
    board = pcbnew.LoadBoard(args.pcb)
    ncu = board.GetCopperLayerCount()
    sig_layers = {6: [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu], 4: [pcbnew.F_Cu, pcbnew.B_Cu]}.get(ncu, [pcbnew.F_Cu, pcbnew.B_Cu])
    plane_nets = {'GND', '+3V3'} if ncu >= 4 else set()
    for rnd in range(args.rounds):
        txt = drc(board); pairs = unconnected_pairs(txt)
        print(f'round {rnd}: {len(pairs)} unconnected')
        if not pairs: break
        done = 0
        for (ax, ay, ad), (bx, by, bd) in pairs:
            a = item_at(board, ax, ay, ad); b = item_at(board, bx, by, bd)
            if a is None or b is None: print('  cannot resolve items:', ad, '|', bd); continue
            net = a.GetNetname()
            by_item, comps = net_islands(board, net, sig_layers)
            ca, cb = by_item[a.m_Uuid.AsString()], by_item[b.m_Uuid.AsString()]
            if ca == cb: print(f'  {net}: already joined'); continue
            (ia, pa), (ib, pb) = comps[ca], comps[cb]
            jobs = []
            if net in plane_nets:
                if not pa: jobs.append((ia, None))
                if not pb: jobs.append((ib, None))
                if not jobs: jobs.append((ia, ib))
            else: jobs.append((ia, ib))
            for src, dst in jobs:
                res = route_job(board, sig_layers, src, dst or [], net, plane_goal=(net in plane_nets))
                for attempt, radius in enumerate((1.0, 1.6)):
                    if not (isinstance(res, tuple) and res and res[0] == 'fail'): break
                    _, rs, rd = res
                    trapped = [isl for isl, r in ((src, rs), (dst or [], rd)) if r < 6000]
                    if not trapped: break
                    centres = []
                    for isl in trapped:
                        for i in isl:
                            if i.GetClass() in ('PAD', 'PCB_VIA'): centres.append((ToMM(i.GetPosition().x), ToMM(i.GetPosition().y)))
                            elif i.GetClass() in ('PCB_TRACK', 'PCB_ARC'): centres += [(ToMM(q.x), ToMM(q.y)) for q in (i.GetStart(), i.GetEnd())]
                    doomed = []
                    for t in board.GetTracks():
                        if t.GetNetname() == net: continue
                        pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
                        if t.GetClass() != 'PCB_VIA':   # also catch long segments passing close to the pad
                            s_, e_ = t.GetStart(), t.GetEnd(); pts = [VECTOR2I(int(s_.x + (e_.x - s_.x) * f), int(s_.y + (e_.y - s_.y) * f)) for f in (0, .25, .5, .75, 1)]
                        if any(math.hypot(ToMM(p.x) - x, ToMM(p.y) - y) < radius for p in pts for (x, y) in centres): doomed.append(t)
                    nets_hit = sorted({t.GetNetname() for t in doomed})
                    for t in doomed: board.Remove(t)
                    print(f'  {net}: trapped end(s) {[round(r) for r in (rs, rd)]} -> ripped up {len(doomed)} items of {nets_hit} within {radius} mm')
                    res = route_job(board, sig_layers, src, dst or [], net, plane_goal=(net in plane_nets))
                if res is None or res[0] == 'fail': print(f'  {net}: no path'); continue
                path, pv = res
                nt, nv = emit(board, path, pv, net, sig_layers); done += 1
                print(f'  {net}: routed {len(path)} cells -> {nt} tracks, {nv} vias' + (' (to plane)' if pv else ''))
            pcbnew.SaveBoard(args.pcb, board); board = pcbnew.LoadBoard(args.pcb)
        if not done: break
    txt = drc(board)
    pcbnew.SaveBoard(args.pcb, board)
    errs = [l for l in re.findall(r'^\[([a-z_]+)\]', txt, re.M)]
    from collections import Counter
    print('final DRC:', Counter(errs))

if __name__ == '__main__':
    main()
