#!/usr/bin/env python3
"""Voltage drop of the 5 V supply on a routed board, from the copper that is really there.

The +5V net is solved as a resistor network (every track piece R = rho * length / (width * 35 um), every via 1.2 mOhm):
the cartridge finger of +5V is the source, each module draws its current at the anode of its Schottky diode. Printed:
  - the drop from the finger to every diode, to pin 31 (the second 5 V finger) and to its capacitor,
  - the largest current in a track of each width, against the current that width carries at a 10 K temperature rise
    (IPC-2221, outer layer, 35 um),
  - the drop of each module's own feed (diode cathode to the module's supply pin),
  - how the ground pours of the two layers are tied together (vias on GND).
Loads: Pico 2 150 mA, XIAO RP2350 100 mA, microSD up to 400 mA more through U6 (its 3.3 V regulator is linear).
    FC_DESIGN=design_revg python3 power_drop.py board.kicad_pcb"""
import sys, os, math, collections, heapq, importlib
import numpy as np
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))

RHO, T_CU, R_VIA = 1.72e-8, 35e-6, 1.2e-3          # ohm m (copper, 20 C); m (1 oz); ohm (0.3 mm hole, 18 um plating, 1.2 mm board)
I_PICO, I_XIAO, I_SD = 0.150, 0.100, 0.400

def r_track(L, w): return RHO * (L * 1e-3) / (w * 1e-3 * T_CU)

def ipc2221(w_mm, dT=10.0):
    """Current in A that an outer-layer track of 35 um carries for a temperature rise dT (IPC-2221: I = 0.048 dT^0.44 A^0.725, A in mil2)."""
    return 0.048 * dT ** 0.44 * ((w_mm / 0.0254) * 1.378) ** 0.725

def dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
    if L2 == 0: return math.hypot(p[0] - a[0], p[1] - a[1]), 0.0
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy)), t

class Net:
    """Track graph of one net. Nodes: (layer, x, y) in mm rounded to 1 um, and ('PAD', ref, number)."""
    def __init__(s, board, name):
        mm = lambda v: v / 1e6
        s.segs = [((mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth()), t.GetLayer())
                  for t in board.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetNetname() == name]
        s.vias = [((mm(t.GetPosition().x), mm(t.GetPosition().y)), mm(t.GetWidth())) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == name]
        s.pads = []
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() != name: continue
                bb = p.GetBoundingBox()
                s.pads.append((f.GetReference(), p.GetNumber(), (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())),
                               [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)]))
        s.adj = collections.defaultdict(list)
        key = lambda layer, p: (layer, round(p[0], 3), round(p[1], 3))
        ends = collections.defaultdict(list)
        for a, b, w, l in s.segs: ends[l] += [a, b]
        for p, d in s.vias: ends[pcbnew.F_Cu].append(p); ends[pcbnew.B_Cu].append(p)
        nodes = collections.defaultdict(set)
        for a, b, w, l in s.segs:                             # split at T junctions and where a pad is crossed
            cuts = {0.0, 1.0}
            for e in ends[l]:
                d, t = dist(e, a, b)
                if d <= w / 2 + 1e-4 and 1e-6 < t < 1 - 1e-6: cuts.add(round(t, 9))
            for ref, num, (x0, y0, x1, y1), layers in s.pads:
                if l not in layers: continue
                d, t = dist(((x0 + x1) / 2, (y0 + y1) / 2), a, b); c = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
                if x0 - 1e-3 <= c[0] <= x1 + 1e-3 and y0 - 1e-3 <= c[1] <= y1 + 1e-3 and 1e-6 < t < 1 - 1e-6: cuts.add(round(t, 9))
            cs = sorted(cuts)
            for t0, t1 in zip(cs, cs[1:]):
                p0 = (a[0] + t0 * (b[0] - a[0]), a[1] + t0 * (b[1] - a[1])); p1 = (a[0] + t1 * (b[0] - a[0]), a[1] + t1 * (b[1] - a[1]))
                u, v = key(l, p0), key(l, p1)
                if u != v: s.edge(u, v, math.hypot(p1[0] - p0[0], p1[1] - p0[1]), w, 'trk')
                nodes[l] |= {u, v}
        for l, ns in nodes.items():                           # ends that lie on top of each other within half a thin track
            ns = sorted(ns, key=lambda n: (n[1], n[2]))
            for i, u in enumerate(ns):
                for v in ns[i + 1:]:
                    if v[1] - u[1] > 0.08: break
                    if math.hypot(u[1] - v[1], u[2] - v[2]) <= 0.075: s.edge(u, v, 0.0, 0.0, 'join')
        for p, d in s.vias:
            f, k = key(pcbnew.F_Cu, p), key(pcbnew.B_Cu, p); s.edge(f, k, 0.0, 0.0, 'via')
            for l, n0 in ((pcbnew.F_Cu, f), (pcbnew.B_Cu, k)):
                for n in list(nodes[l]):
                    if n != n0 and math.hypot(n[1] - p[0], n[2] - p[1]) <= d / 2: s.edge(n0, n, 0.0, 0.0, 'join')
                nodes[l].add(n0)
        for ref, num, (x0, y0, x1, y1), layers in s.pads:
            pn = ('PAD', ref, num); s.adj[pn]
            for l in layers:
                for n in nodes[l]:
                    if x0 - 0.02 <= n[1] <= x1 + 0.02 and y0 - 0.02 <= n[2] <= y1 + 0.02: s.edge(pn, n, 0.0, 0.0, 'join')

    def edge(s, u, v, L, w, kind):
        s.adj[u].append((v, L, w, kind)); s.adj[v].append((u, L, w, kind))

    def res(s, L, w, kind): return R_VIA if kind == 'via' else r_track(L, w) if kind == 'trk' and L > 0 else 0.0

    def reach(s, src):
        seen = {src}; st = [src]
        while st:
            for v, *_ in s.adj[st.pop()]:
                if v not in seen: seen.add(v); st.append(v)
        return seen

    def path(s, src, dst):
        """Lowest-resistance path: (ohm, length mm, narrowest width mm, vias) or None."""
        best = {src: 0.0}; prev = {}; pq = [(0.0, 0, src)]; n = 1
        while pq:
            d, _, u = heapq.heappop(pq)
            if d > best.get(u, 1e99): continue
            if u == dst: break
            for v, L, w, kind in s.adj[u]:
                nd = d + s.res(L, w, kind)
                if nd < best.get(v, 1e99): best[v] = nd; prev[v] = (u, L, w, kind); heapq.heappush(pq, (nd, n, v)); n += 1
        if dst not in best: return None
        L = 0.0; wmin = 99.0; nv = 0; u = dst
        while u != src:
            u, l, w, kind = prev[u]
            if kind == 'trk': L += l; wmin = min(wmin, w)
            if kind == 'via': nv += 1
        return best[dst], L, wmin, nv

    def solve(s, src, loads):
        """DC solution with the source at 0 V: ({node: volts}, {width: largest current in a track of that width})."""
        comp = s.reach(src); nodes = [n for n in s.adj if n in comp]; idx = {n: i for i, n in enumerate(nodes)}
        G = np.zeros((len(nodes), len(nodes))); I = np.zeros(len(nodes))
        for u in nodes:
            for v, L, w, kind in s.adj[u]:
                r = s.res(L, w, kind); g = 1.0 / r if r > 0 else 1e7
                G[idx[u], idx[u]] += g; G[idx[u], idx[v]] -= g
        for n, a in loads.items():
            if n not in idx: raise SystemExit('%s is not connected to the source %s' % (n, src))
            I[idx[n]] -= a
        keep = [i for n, i in idx.items() if n != src]; V = np.zeros(len(nodes))
        V[keep] = np.linalg.solve(G[np.ix_(keep, keep)], I[keep])
        peak = collections.defaultdict(float)
        for u in nodes:
            for v, L, w, kind in s.adj[u]:
                if kind == 'trk' and L > 0: peak[round(w, 3)] = max(peak[round(w, 3)], abs(V[idx[u]] - V[idx[v]]) / r_track(L, w))
        return {n: V[idx[n]] for n in nodes}, dict(peak)

# ---- designs with PLANES (rev H on): every copper layer, filled zone islands as nodes, own supply topology ----
T_OUT, T_IN = 35e-6, 17.5e-6       # m: outer 1 oz, inner 0.5 oz (JLC06121H-3313)
# DVDD current of one RP2350B in A (docs/13 "電源", model A with the worst factor 2.1: 150 MHz 25 mA x 2.1; 240 MHz from
# the 200 MHz figure 31 mA scaled to 240 MHz, x 2.1, rounded up so 8 chips give the 0.64 A of the +1V1 budget)
I_DVDD = {240: 0.080, 150: 0.0525, 48: 0.017, 12: 0.0015}
DVDD_MIN, VSEL_HI_MIN = 1.05, 1.089   # V: DVDD recommended minimum; +1V1 with VSEL high, lowest in tolerance (docs/13)

def ipc2221_layer(w_mm, outer, dT=10.0):
    """IPC-2221 current for a dT rise: outer I = 0.048 dT^0.44 A^0.725, inner 0.024 (A in mil2, copper 35 / 17.5 um)."""
    return (0.048 if outer else 0.024) * dT ** 0.44 * ((w_mm / 0.0254) * ((T_OUT if outer else T_IN) * 1e6 / 25.4)) ** 0.725

class NetML:
    """Resistor network of one net on all copper layers. Nodes: (layer, x, y) in mm (1 um), ('PAD', ref, num),
    ('VIA', i) for a via barrel, ('ZONE', i, layer, k) for one filled island of a zone of the net."""
    def __init__(s, data, name):
        cu = data['cu']; outer = {cu[0], cu[-1]}
        s.segs = [g for g in data['segs'] if g[4] == name]
        s.vias = [v for v in data['vias'] if v[2] == name]
        s.pads = [q for q in data['pads'] if q[4] == name]
        s.adj = collections.defaultdict(list); s.outer = outer
        key = lambda layer, p: (layer, round(p[0], 3), round(p[1], 3))
        ends = collections.defaultdict(list)
        for a, b, w, l, _ in s.segs: ends[l] += [a, b]
        for p, d, _ in s.vias:
            for l in cu: ends[l].append(p)
        nodes = collections.defaultdict(set)
        for a, b, w, l, _ in s.segs:                          # split at T junctions and where a pad is crossed
            cuts = {0.0, 1.0}
            for e in ends[l]:
                d, t = dist(e, a, b)
                if d <= w / 2 + 1e-4 and 1e-6 < t < 1 - 1e-6: cuts.add(round(t, 9))
            for ref, num, (x0, y0, x1, y1), layers, _ in s.pads:
                if l not in layers: continue
                d, t = dist(((x0 + x1) / 2, (y0 + y1) / 2), a, b); c = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
                if x0 - 1e-3 <= c[0] <= x1 + 1e-3 and y0 - 1e-3 <= c[1] <= y1 + 1e-3 and 1e-6 < t < 1 - 1e-6: cuts.add(round(t, 9))
            cs = sorted(cuts)
            for t0, t1 in zip(cs, cs[1:]):
                p0 = (a[0] + t0 * (b[0] - a[0]), a[1] + t0 * (b[1] - a[1])); p1 = (a[0] + t1 * (b[0] - a[0]), a[1] + t1 * (b[1] - a[1]))
                u, v = key(l, p0), key(l, p1); L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                if u != v: s.edge(u, v, RHO * (L * 1e-3) / (w * 1e-3 * (T_OUT if l in outer else T_IN)), L, w, l, 'trk')
                nodes[l] |= {u, v}
        for l, ns in nodes.items():                           # ends on top of each other within half a thin track
            ns = sorted(ns, key=lambda n: (n[1], n[2]))
            for i, u in enumerate(ns):
                for v in ns[i + 1:]:
                    if v[1] - u[1] > 0.08: break
                    if math.hypot(u[1] - v[1], u[2] - v[2]) <= 0.075: s.edge(u, v, 0.0, 0, 0, l, 'join')
        for i, (p, d, _) in enumerate(s.vias):                # through vias: barrel node, half the via resistance to each layer
            bar = ('VIA', i)
            for l in cu:
                n0 = key(l, p); s.edge(bar, n0, R_VIA / 2, 0, 0, l, 'via')
                for n in list(nodes[l]):
                    if n != n0 and math.hypot(n[1] - p[0], n[2] - p[1]) <= d / 2: s.edge(n0, n, 0.0, 0, 0, l, 'join')
                nodes[l].add(n0)
        for ref, num, (x0, y0, x1, y1), layers, _ in s.pads:
            pn = ('PAD', ref, num); s.adj[pn]
            for l in layers:
                n_c = key(l, ((x0 + x1) / 2, (y0 + y1) / 2)); nodes[l].add(n_c); s.edge(pn, n_c, 0.0, 0, 0, l, 'join')
                for n in list(nodes[l]):
                    if x0 - 0.02 <= n[1] <= x1 + 0.02 and y0 - 0.02 <= n[2] <= y1 + 0.02: s.edge(pn, n, 0.0, 0, 0, l, 'join')
        s.zones = 0
        for zi, (l, inside) in enumerate(data['zones'].get(name, [])):   # filled islands: one node each (sheet resistance ignored)
            for n in list(nodes[l]):
                k = inside(n[1], n[2])
                if k is not None: s.edge(('ZONE', zi, l, k), n, 0.0, 0, 0, l, 'join'); s.zones += 1

    def edge(s, u, v, R, L, w, l, kind):
        s.adj[u].append((v, R, L, w, l, kind)); s.adj[v].append((u, R, L, w, l, kind))

    def reach(s, src):
        seen = {src}; st = [src]
        while st:
            for v, *_ in s.adj[st.pop()]:
                if v not in seen: seen.add(v); st.append(v)
        return seen

    def path(s, src, dst):
        """Lowest-resistance path: (ohm, track length mm, narrowest width mm, vias) or None."""
        best = {src: 0.0}; prev = {}; pq = [(0.0, 0, src)]; n = 1
        while pq:
            d, _, u = heapq.heappop(pq)
            if d > best.get(u, 1e99): continue
            if u == dst: break
            for v, R, L, w, l, kind in s.adj[u]:
                nd = d + R
                if nd < best.get(v, 1e99): best[v] = nd; prev[v] = (u, L, w, kind); heapq.heappush(pq, (nd, n, v)); n += 1
        if dst not in best: return None
        L = 0.0; wmin = 99.0; nv = 0; u = dst
        while u != src:
            u, l, w, kind = prev[u]
            if kind == 'trk': L += l; wmin = min(wmin, w)
            if kind == 'via': nv += 1
        return best[dst], L, wmin, nv // 2

    def solve(s, src, loads):
        """DC solution, source at 0 V: ({node: volts}, {(width, outer): largest track current})."""
        comp = s.reach(src); nodes = [n for n in s.adj if n in comp]; idx = {n: i for i, n in enumerate(nodes)}
        G = np.zeros((len(nodes), len(nodes))); I = np.zeros(len(nodes))
        for u in nodes:
            for v, R, L, w, l, kind in s.adj[u]:
                g = 1.0 / R if R > 0 else 1e7
                G[idx[u], idx[u]] += g; G[idx[u], idx[v]] -= g
        for n, a in loads.items():
            if n not in idx: raise SystemExit('%s is not connected to the source %s' % (n, src))
            I[idx[n]] -= a
        keep = [i for n, i in idx.items() if n != src]; V = np.zeros(len(nodes))
        V[keep] = np.linalg.solve(G[np.ix_(keep, keep)], I[keep])
        peak = collections.defaultdict(float)
        for u in nodes:
            for v, R, L, w, l, kind in s.adj[u]:
                if kind == 'trk' and R > 0: k = (round(w, 3), l in s.outer); peak[k] = max(peak[k], abs(V[idx[u]] - V[idx[v]]) / R)
        return {n: V[idx[n]] for n in nodes}, dict(peak)

def board_data(board):
    """Plain copies of the copper (read before the zone fill: this binding cannot list tracks after a fill + check)."""
    mm = lambda v: v / 1e6
    cu = [l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)][:board.GetCopperLayerCount() - 1] + [pcbnew.B_Cu]
    segs, vias, pads = [], [], []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA': vias.append(((mm(t.GetPosition().x), mm(t.GetPosition().y)), mm(t.GetWidth()), t.GetNetname()))
        else: segs.append(((mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y)), mm(t.GetWidth()), t.GetLayer(), t.GetNetname()))
    for f in board.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            pads.append((f.GetReference(), p.GetNumber(), (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())),
                         [l for l in cu if p.IsOnLayer(l)], p.GetNetname()))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    zones = collections.defaultdict(list)
    for z in board.Zones():
        if z.GetIsRuleArea(): continue
        for l in cu:
            if not z.IsOnLayer(l) or not z.HasFilledPolysForLayer(l): continue
            ps = z.GetFilledPolysList(l)
            if ps.OutlineCount() == 0: continue
            def inside(x, y, ps=ps):
                pt = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
                for k in range(ps.OutlineCount()):
                    if ps.Contains(pt, k): return k
                return None
            zones[z.GetNetname()].append((l, inside))
    return dict(cu=cu, segs=segs, vias=vias, pads=pads, zones=zones)

def main_planes(board):
    data = board_data(board); pad = lambda ref, num: ('PAD', ref, str(num))
    def part_pads(net): return [(q[0], q[1]) for q in data['pads'] if q[4] == net]
    def lname(l): return board.GetLayerName(l)
    def report_peaks(peak):
        out = []
        for (w, o), i in sorted(peak.items()):
            lim = ipc2221_layer(w, o); out.append('%.2f mm %s: %.0f mA (10 K %.0f mA)%s' % (w, 'outer' if o else 'inner', i * 1e3, lim * 1e3, ' OVER' if i > lim else ''))
        return ', '.join(out)
    schottky = {}
    for ref, q in D.PARTS.items():
        if q[2].split(' (')[0] != 'B5819W': continue
        nets = {num: net for r, num in [(ref, n) for n in ('1', '2')] for (rr, nn, bb, ll, net) in data['pads'] if rr == ref and nn == num}
        schottky[ref] = (nets.get('2'), nets.get('1'))       # (anode net, cathode net)
    conv = {}                                                 # converter -> (output net, VIN pad)
    for ref, q in D.PARTS.items():
        if q[2].split(' (')[0] != 'TLV62569DBVR': continue
        sw = next(net for (rr, nn, bb, ll, net) in data['pads'] if rr == ref and nn == '3')
        ind = next(rr for (rr, nn, bb, ll, net) in data['pads'] if net == sw and rr.startswith('L'))
        out = next(net for (rr, nn, bb, ll, net) in data['pads'] if rr == ind and net != sw)
        conv[ref] = (out, pad(ref, 4))
    # loads at the converter inputs for a total 5 V current: shared by output power (+1V1 0.64 A x 1.1 V, +3V3 0.56 A x 3.3 V)
    share = {r: (0.64 * 1.1 if o == '+1V1' else 0.56 * 3.3) for r, (o, _) in conv.items()}
    tot = sum(share.values()); share = {r: v / tot for r, v in share.items()}
    print('supply (designs with PLANES): converters %s; Schottky %s' % (', '.join('%s -> %s' % (r, o) for r, (o, _) in sorted(conv.items())),
          ', '.join('%s %s -> %s' % (r, a, k) for r, (a, k) in sorted(schottky.items()))))
    j1 = [num for (rr, num) in part_pads('+5V') if rr == 'J1']
    if j1:
        g = NetML(data, '+5V'); src = pad('J1', sorted(j1, key=int)[0])
        for d, (a, k) in sorted(schottky.items()):
            if a != '+5V': continue
            for amp in (0.30, 0.45):
                V, peak = g.solve(src, {pad(d, 2): amp})
                print('  +5V finger J1.%s -> %s anode at %d mA: %.1f mV; %s' % (src[2], d, amp * 1e3, -V[pad(d, 2)] * 1e3, report_peaks(peak)))
    for d, (a, k) in sorted(schottky.items()):
        g = NetML(data, k); src = pad(d, 1)
        for amp in (0.30, 0.45):
            V, peak = g.solve(src, {vin: amp * share[r] for r, (o, vin) in conv.items()})
            print('  %s from %s (%s) at %d mA: %s; %s' % (k, d, a, amp * 1e3, ', '.join('%s VIN %.1f mV' % (r, -V[vin] * 1e3) for r, (o, vin) in sorted(conv.items())), report_peaks(peak)))
    # +1V1: from the top of the feedback divider (the point the converter holds) to the DVDD pins of every chip
    sense = None
    for (rr, nn, bb, ll, net) in data['pads']:
        if net == '+1V1' and rr.startswith('R') and any(r2 == rr and n2 != nn and net2.startswith('FB_1V1') for (r2, n2, b2, l2, net2) in data['pads']): sense = pad(rr, nn)
    chips = sorted({rr for (rr, nn, bb, ll, net) in data['pads'] if net == '+1V1' and rr.startswith('U') and D.PARTS[rr][2].split(' (')[0].startswith('RP2350')}, key=lambda r: int(r[1:]))
    dv = {u: [nn for (rr, nn, bb, ll, net) in data['pads'] if rr == u and net == '+1V1'] for u in chips}
    g = NetML(data, '+1V1')
    print('  +1V1: sense %s.%s; %d tracks, %d vias, %d island contacts; chips %s' % (sense[1], sense[2], len(g.segs), len(g.vias), g.zones, ' '.join(chips)))
    cases = [('8 chips at 240 MHz', {u: 240 for u in chips}),
             ('Famicom game (U1-U3 240, U4 U5 48, U6 150, U8 U9 12 MHz)', {u: {'U1': 240, 'U2': 240, 'U3': 240, 'U4': 48, 'U5': 48, 'U6': 150}.get(u, 12) for u in chips})]
    for name, mhz in cases:
        loads = collections.defaultdict(float)
        for u in chips:
            for nn in dv[u]: loads[pad(u, nn)] += I_DVDD[mhz[u]] / len(dv[u])
        V, peak = g.solve(sense, dict(loads))
        worst = {u: max(-V[pad(u, nn)] for nn in dv[u]) * 1e3 for u in chips}
        total = sum(loads.values())
        print('  +1V1 %s, %d mA: drop to the worst DVDD pin %s; budget %.0f mV (VSEL high %.3f V min - %.2f V)' % (name, round(total * 1e3),
              ', '.join('%s %.1f mV' % (u, worst[u]) for u in chips), (VSEL_HI_MIN - DVDD_MIN) * 1e3, VSEL_HI_MIN, DVDD_MIN))
        print('      largest track current: ' + report_peaks(peak))
        if max(worst.values()) > (VSEL_HI_MIN - DVDD_MIN) * 1e3: print('      NOTE: the drop is over the budget')
    for u in chips:
        r = min((g.path(sense, pad(u, nn)) for nn in dv[u]), key=lambda x: x[0] if x else 1e9)
        print('    %s: path %.1f mm, narrowest %.2f mm, %d vias, %.1f mOhm' % (u, r[1], r[2], r[3], r[0] * 1e3) if r else '    %s: NO PATH' % u)
    gv = sum(1 for v in data['vias'] if v[2] == 'GND')
    print('  +3V3: plane on %s; GND: %d vias; GND planes %s' % (', '.join(sorted({lname(l) for (l, f) in data['zones'].get('+3V3', [])})), gv,
          ', '.join(sorted({lname(l) for (l, f) in data['zones'].get('GND', [])}))))

def main():
    board = pcbnew.LoadBoard(sys.argv[1]); pad = lambda ref, num: ('PAD', ref, str(num))
    if getattr(D, 'PLANES', None) is not None: return main_planes(board)
    j1 = board.FindFootprintByReference('J1')
    fingers = sorted((p.GetNumber() for p in j1.Pads() if p.GetNetname() == '+5V'), key=int)
    src = pad('J1', fingers[0])
    feeds = {}                                                 # diode -> (module net, module ref, module pad, current)
    for ref, q in D.PARTS.items():
        if q[2].split(' (')[0] != 'B5819W': continue
        fp = board.FindFootprintByReference(ref); nets = {p.GetNumber(): p.GetNetname() for p in fp.Pads()}
        if nets.get('2') != '+5V': continue
        mod = next(((f.GetReference(), p.GetNumber()) for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == nets['1'] and f.GetReference().startswith('U')), None)
        if mod: feeds[ref] = (nets['1'], mod[0], mod[1], I_XIAO if 'XIAO' in D.PARTS[mod[0]][3].upper() or 'XIAO' in D.PARTS[mod[0]][2].upper() else I_PICO)
    g = Net(board, '+5V')
    widths = collections.Counter(); length = collections.defaultdict(float)
    for a, b, w, l in g.segs: widths[round(w, 3)] += 1; length[round(w, 3)] += math.hypot(b[0] - a[0], b[1] - a[1])
    print('+5V: source finger J1.%s; tracks by width: %s; %d vias' % (fingers[0], ', '.join('%.2f mm x %.1f mm' % (w, length[w]) for w in sorted(length)), len(g.vias)))
    base = [d for d, f in feeds.items() if f[1] in getattr(D, 'BASE_MODULES', ('U1', 'U2', 'U3', 'U6'))]
    hub = next((d for d, f in feeds.items() if f[1] == 'U6'), None)
    cases = [('base set (%s)' % ', '.join(sorted(feeds[d][1] for d in base)), {d: feeds[d][3] for d in base}),
             ('all six modules', {d: f[3] for d, f in feeds.items()}),
             ('all six + microSD drawing 400 mA', {d: f[3] + (I_SD if d == hub else 0.0) for d, f in feeds.items()})]
    worst_all = 0.0
    for name, ld in cases:
        V, peak = g.solve(src, {pad(d, 2): a for d, a in ld.items()})
        drops = {d: -V[pad(d, 2)] * 1e3 for d in sorted(feeds, key=lambda r: int(r[1:]))}
        extra = ''.join('; %s %.1f mV' % (lab, -V[n] * 1e3) for lab, n in (('pin %s' % fingers[-1], pad('J1', fingers[-1])), ('C8', pad('C8', 1))) if n in V and n != src)
        print('  %s, %d mA: drop finger -> diode %s%s' % (name, round(sum(ld.values()) * 1e3), ', '.join('%s(%s) %.1f mV' % (d, feeds[d][1], v) for d, v in drops.items()), extra))
        print('      largest track current: ' + ', '.join('%.2f mm: %.0f mA (10 K limit %.0f mA)' % (w, i * 1e3, ipc2221(w) * 1e3) for w, i in sorted(peak.items())))
        worst_all = max(worst_all, max(drops.values()))
        for w, i in peak.items():
            if i > ipc2221(w) + 1e-6: print('      NOTE: a %.2f mm track carries %.0f mA, above its 10 K figure of %.0f mA' % (w, i * 1e3, ipc2221(w) * 1e3))
    print('module feeds (diode cathode -> module supply pin):')
    for d in sorted(feeds, key=lambda r: int(r[1:])):
        net, ref, num, cur = feeds[d]; r = Net(board, net).path(pad(d, 1), pad(ref, num))
        if not r: print('  %s: NO PATH %s.1 -> %s.%s' % (net, d, ref, num)); continue
        more = '; %.1f mV at %d mA (with microSD)' % (r[0] * (cur + I_SD) * 1e3, round((cur + I_SD) * 1e3)) if d == hub else ''
        print('  %-7s %s.1 -> %s.%s: %.1f mm, narrowest %.2f mm, %d vias, %.1f mOhm, %.1f mV at %d mA%s' % (net, d, ref, num, r[1], r[2], r[3], r[0] * 1e3, r[0] * cur * 1e3, round(cur * 1e3), more))
    gv = sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND')
    gf = [p.GetNumber() for p in j1.Pads() if p.GetNetname() == 'GND']
    gw = collections.Counter(round(t.GetWidth() / 1e6, 2) for t in board.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetNetname() == 'GND')
    print('GND: %d vias join the two pours; cartridge fingers %s; GND tracks by width: %s' % (gv, ', '.join(sorted(gf, key=int)), ', '.join('%.2f mm x %d' % (w, n) for w, n in sorted(gw.items()))))

if __name__ == '__main__':
    main()
