#!/usr/bin/env python3
"""Widen the supply tracks of a routed board where there is room (run after routing, before stitch_gnd.py).

The autorouter is given one track width for the nets of D.NET_WIDTH, but wiring that was routed earlier with the
signal width stays thin. This tool sets every track segment of those nets (and of the nets named with --net) to the
wanted width and lets KiCad's own design rule check decide: a segment that takes part in a violation is stepped down
(0.30 -> 0.25 -> 0.20 -> the width it had), the zones are filled again, and the check is repeated until no violation
is left. Nothing is moved and no connection changes; only widths grow.
    FC_DESIGN=design_revg python3 widen_tracks.py board.kicad_pcb [--net +5V=0.5] ..."""
import os, sys, re, argparse, tempfile, collections, importlib
import pcbnew
from pcbnew import ToMM, FromMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--net', action='append', default=[], help='NET=width_mm, in addition to D.NET_WIDTH')
args = ap.parse_args()
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
WANT = dict(getattr(D, 'NET_WIDTH', {}))
for item in args.net:
    n, w = item.split('='); WANT[n] = float(w)
STEP = 0.05

def violations(board):
    rep = os.path.join(tempfile.mkdtemp(prefix='widen_'), 'drc.txt')
    pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    out = []
    for blk in re.split(r'\n(?=\[)', open(rep).read()):
        if 'Severity: error' not in blk or blk.startswith('[unconnected'): continue
        out.append(re.findall(r'@\(([0-9.\-]+) mm, ([0-9.\-]+) mm\): Track \[([^\]]*)\] on (\S+?), length ([0-9.]+) mm', blk))
    return out

def main():
    board = pcbnew.LoadBoard(args.pcb)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    before = len(violations(board))
    if before: raise SystemExit('widen_tracks: the board has %d design rule violations already; fix them first' % before)
    mine = {}                                                  # id -> (track, original width)
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' or t.GetNetname() not in WANT: continue
        w = FromMM(WANT[t.GetNetname()])
        if t.GetWidth() < w: mine[id(t)] = (t, t.GetWidth()); t.SetWidth(w)
    print('widen_tracks: %d segments of %s set to the wanted width' % (len(mine), sorted(WANT)))
    for rnd in range(40):
        pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
        viol = violations(board)
        if not viol: break
        index = collections.defaultdict(list)
        for t, w0 in mine.values():
            for p in (t.GetStart(), t.GetEnd()): index[(t.GetNetname(), round(ToMM(p.x), 3), round(ToMM(p.y), 3))].append((t, w0))
        narrowed = 0; foreign = 0
        for items in viol:
            hit = False
            for (x, y, net, layer, length) in items:
                for t, w0 in index.get((net, round(float(x), 3), round(float(y), 3)), []):
                    if abs(ToMM(t.GetLength()) - float(length)) > 0.001 or t.GetWidth() <= w0: continue
                    t.SetWidth(max(w0, t.GetWidth() - FromMM(STEP))); narrowed += 1; hit = True
            if not hit: foreign += 1
        print('  round %d: %d violations, %d segments stepped down%s' % (rnd, len(viol), narrowed, ', %d violations without a widened segment' % foreign if foreign else ''))
        if not narrowed:                                       # violations that stepping down cannot cure: undo everything near them
            for t, w0 in mine.values(): t.SetWidth(w0)
            print('  giving up: all widths restored'); break
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    left = len(violations(board))
    by = collections.defaultdict(lambda: collections.defaultdict(float))
    for t in board.GetTracks():
        if t.GetClass() != 'PCB_VIA' and t.GetNetname() in WANT: by[t.GetNetname()][round(ToMM(t.GetWidth()), 2)] += ToMM(t.GetLength())
    for n in sorted(by): print('  %-8s %s' % (n, ', '.join('%.2f mm: %.1f mm' % (w, l) for w, l in sorted(by[n].items()))))
    print('widen_tracks: design rule violations now %d, open connections %d' % (left, board.GetConnectivity().GetUnconnectedCount(False)))
    pcbnew.SaveBoard(args.pcb, board)
    sys.exit(1 if left else 0)

if __name__ == '__main__':
    main()
