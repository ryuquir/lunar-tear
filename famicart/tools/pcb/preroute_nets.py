#!/usr/bin/env python3
"""Shortest routes for a few critical nets, found on the unrouted board before the autorouter runs, printed as design-file
PREROUTE / PREROUTE_VIAS entries (gen_pcb.py lays them and the router keeps them).

Why: Freerouting treats every net alike. On rev H it took crystal nets round the QFN fan-out (XOUT8 32 mm with 4 vias for
a 2.1 mm span), which no oscillator should see. Routed first, on an otherwise empty board, they are 1.5-2.8 mm with one via.

How: gen_pcb.py writes the unrouted board of FC_DESIGN into a work directory; every pad that is not on one of the chosen
nets loses its net (it stays an obstacle), so the rule check reports only the chosen nets (KiCad's report stops at 499
unconnected items, and the full board has more); finish_route.py --no-rip --only <nets> routes them; the result is copied
back onto a fresh unrouted board -- only items within 3 mm of a pad of their own net and no wider than 0.2 mm, because
saving the stripped board renumbers nets and other copper can come back under a chosen net's name -- and checked there:
no rule error that names a chosen net, and every chosen net joined.

    FC_DESIGN=design_revh python3 preroute_nets.py 'XIN\\d|XOUT\\d(_R)?' NAME > entries.py
NAME names the printed lists (PREROUTE_NAME, PREROUTE_NAME_VIAS); coordinates are the design's (x' = x - 45, h = H - y).
"""
import os, sys, re, math, shutil, subprocess, tempfile, collections, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew
from pcbnew import ToMM, FromMM

def log(*a): print(*a, file=sys.stderr, flush=True)

def gen_board(work):
    hw = os.path.join(work, 'hw'); os.makedirs(hw, exist_ok=True)
    env = dict(os.environ, FC_HW_DIR=hw)
    r = subprocess.run([sys.executable, '-c', 'import gen_pcb; gen_pcb.main()'], cwd=HERE, env=env, capture_output=True, text=True)
    if r.returncode: raise SystemExit('gen_pcb failed:\n' + r.stdout[-2000:] + r.stderr[-2000:])
    return os.path.join(hw, 'famicart.kicad_pcb')

def strip_other_nets(path, keep):
    b = pcbnew.LoadBoard(path); n = 0
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not keep.fullmatch(p.GetNetname()) and p.GetNetname() != '': p.SetNetCode(0); n += 1
    pcbnew.SaveBoard(path, b); return n

def copy_routes(src_path, dst_path, keep):
    src = pcbnew.LoadBoard(src_path); dst = pcbnew.LoadBoard(dst_path)
    pads = collections.defaultdict(list)
    for fp in dst.GetFootprints():
        for p in fp.Pads():
            if keep.fullmatch(p.GetNetname()): pads[p.GetNetname()].append((ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)))
    near = lambda net, pts: bool(pads[net]) and all(min(math.hypot(x - a, y - b) for a, b in pads[net]) < 3.0 for x, y in pts)
    nt = nv = skip = 0
    for t in list(src.GetTracks()):
        n = t.GetNetname(); via = t.GetClass() == 'PCB_VIA'
        if not keep.fullmatch(n): continue
        pts = [(ToMM(t.GetPosition().x), ToMM(t.GetPosition().y))] if via else \
              [(ToMM(t.GetStart().x), ToMM(t.GetStart().y)), (ToMM(t.GetEnd().x), ToMM(t.GetEnd().y))]
        if not near(n, pts) or (not via and t.GetWidth() > FromMM(0.2)): skip += 1; continue
        ni = dst.FindNet(n)
        if via:
            v = pcbnew.PCB_VIA(dst); v.SetPosition(t.GetPosition()); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(t.GetWidth())
            v.SetDrill(t.GetDrillValue()); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); dst.Add(v); nv += 1
        else:
            k = pcbnew.PCB_TRACK(dst); k.SetStart(t.GetStart()); k.SetEnd(t.GetEnd()); k.SetWidth(t.GetWidth()); k.SetLayer(t.GetLayer())
            k.SetNet(ni); dst.Add(k); nt += 1
    pcbnew.SaveBoard(dst_path, dst)
    log('copied %d tracks and %d vias (%d items of other copper left behind)' % (nt, nv, skip))

def check(path, keep, work):
    """(rule errors naming a chosen net, chosen-net connections still open) -- in child processes: after a zone fill and a
    rule check this KiCad's Python binding cannot list tracks any more."""
    code = r'''
import sys, re, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); keep = re.compile(sys.argv[2]); mode = sys.argv[3]
if mode == 'open':
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not keep.fullmatch(p.GetNetname()) and p.GetNetname() != '': p.SetNetCode(0)
else:
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
pcbnew.WriteDRCReport(b, sys.argv[4], pcbnew.EDA_UNITS_MILLIMETRES, True)
'''
    out = {}
    for mode in ('errors', 'open'):
        rep = os.path.join(work, 'drc_%s.txt' % mode)
        subprocess.run([sys.executable, '-c', code, path, keep.pattern, mode, rep], capture_output=True, text=True)
        blks = [blk for blk in re.split(r'\n(?=\[)', open(rep).read()) if blk.startswith('[')]
        if mode == 'errors':
            out[mode] = [blk.split('\n')[0] + ' ' + ' | '.join(l.strip() for l in blk.split('\n')[2:4]) for blk in blks
                         if 'Severity: error' in blk and not blk.startswith('[unconnected_items]') and
                         any(keep.fullmatch(n) for n in re.findall(r'\[([^\]]+)\] (?:on|of)', blk))]
        else:
            out[mode] = [blk for blk in blks if blk.startswith('[unconnected_items]') and
                         any(keep.fullmatch(n) for n in re.findall(r'\[([^\]]+)\] (?:on|of)', blk))]
    return out['errors'], out['open']

def entries(path, keep, name):
    D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
    b = pcbnew.LoadBoard(path); H = D.H
    segs = collections.defaultdict(list); vias = []
    for t in b.GetTracks():
        n = t.GetNetname()
        if not keep.fullmatch(n): continue
        if t.GetClass() == 'PCB_VIA': vias.append((n, ToMM(t.GetPosition().x), ToMM(t.GetPosition().y)))
        else:
            segs[(n, b.GetLayerName(t.GetLayer()), round(ToMM(t.GetWidth()), 3))].append(
                ((round(ToMM(t.GetStart().x), 3), round(ToMM(t.GetStart().y), 3)), (round(ToMM(t.GetEnd().x), 3), round(ToMM(t.GetEnd().y), 3))))
    def chains(ss):
        adj = collections.defaultdict(list)
        for i, (a, c) in enumerate(ss): adj[a].append(i); adj[c].append(i)
        used = set(); out = []
        for s0 in [p for p in adj if len(adj[p]) != 2] + list(adj):
            for i in adj[s0]:
                if i in used: continue
                pts = [s0]; cur = s0; j = i
                while j is not None and j not in used:
                    used.add(j); a, c = ss[j]; nxt = c if a == cur else a; pts.append(nxt); cur = nxt
                    j = next((k for k in adj[cur] if k not in used), None) if len(adj[cur]) == 2 else None
                out.append(pts)
        return out
    def simplify(pts):
        out = [pts[0]]
        for p, q in zip(pts[1:], pts[2:] + [None]):
            if q is None: out.append(p); break
            a = out[-1]
            if abs((p[0] - a[0]) * (q[1] - p[1]) - (p[1] - a[1]) * (q[0] - p[0])) < 1e-9: continue
            out.append(p)
        return out
    num = lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 0
    fmt = lambda x, y: '(%.3f, %.3f)' % (round(x - 45.0, 3), round(H - y, 3))
    lines = ['PREROUTE_%s = [' % name]
    for (n, lay, w), ss in sorted(segs.items(), key=lambda kv: (num(kv[0][0]), kv[0])):
        for pts in chains(ss):
            lines.append("    ('%s', %.2f, _poly([%s]), '%s')," % (n, w, ', '.join(fmt(*p) for p in simplify(pts)), lay))
    lines.append(']')
    lines.append('PREROUTE_%s_VIAS = [' % name + ', '.join("('%s',) + at(%.3f, %.3f)" % (n, round(x - 45.0, 3), round(H - y, 3))
                                                         for n, x, y in sorted(vias, key=lambda v: (num(v[0]), v))) + ']')
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 3: raise SystemExit(__doc__)
    keep = re.compile(sys.argv[1]); name = sys.argv[2]
    work = tempfile.mkdtemp(prefix='preroute_')
    board = gen_board(work)
    if getattr(importlib.import_module(os.environ.get('FC_DESIGN', 'design')), 'PREROUTE', None):
        # the design may already carry entries for these nets (a second run): start from a board without them
        b = pcbnew.LoadBoard(board)
        old = [t for t in list(b.GetTracks()) if keep.fullmatch(t.GetNetname())]
        for t in old: b.Remove(t)
        pcbnew.SaveBoard(board, b)
        if old: log('removed %d items the design already lays on these nets' % len(old))
    stripped = os.path.join(work, 'only.kicad_pcb'); shutil.copy(board, stripped)
    shutil.copy(os.path.splitext(board)[0] + '.kicad_pro', os.path.splitext(stripped)[0] + '.kicad_pro')
    log('pads taken off their net:', strip_other_nets(stripped, keep))
    nets = sorted({p.GetNetname() for fp in pcbnew.LoadBoard(board).GetFootprints() for p in fp.Pads() if keep.fullmatch(p.GetNetname())})
    r = subprocess.run([sys.executable, os.path.join(HERE, 'finish_route.py'), stripped, '--no-rip', '--rounds', '1', '--only', ','.join(nets)],
                       capture_output=True, text=True, env=dict(os.environ, TMPDIR=work))
    log('\n'.join(l for l in r.stdout.splitlines() if 'no path' in l or l.startswith('round')))
    copy_routes(stripped, board, keep)
    errors, opens = check(board, keep, work)
    for e in errors: log('rule error:', e[:200])
    log('%d nets, %d rule errors naming them, %d connections still open' % (len(nets), len(errors), len(opens)))
    print(entries(board, keep, name))
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(1 if errors or opens else 0)        # skip SWIG's leak notices at exit: they go to stdout and would land in the entries

if __name__ == '__main__':
    main()
