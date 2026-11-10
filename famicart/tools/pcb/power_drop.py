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

def main():
    board = pcbnew.LoadBoard(sys.argv[1]); pad = lambda ref, num: ('PAD', ref, str(num))
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
