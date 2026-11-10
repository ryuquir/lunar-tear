#!/usr/bin/env python3
"""Reinforce track ends that only just reach their pad (run after routing, before widen_tracks.py).

A router may end a track a few hundredths of a millimetre inside a pad, at a rounded corner: KiCad counts that as
connected, but the copper joining track and pad is then a neck narrower than the track (0.08-0.10 mm was measured on
one such joint), which etching and the heat of hand soldering can open. For every track end that lies inside a pad of
its own net, closer to the pad's edge than --depth (default 0.20 mm), this tool adds a segment of the same width from
that end to the centre of the pad. The new copper lies inside the pad's own outline box, so no clearance changes;
the design rule check is run afterwards all the same. Ends on the gold fingers are left alone: the finger's centre
lies in the zone that is kept free of tracks.
    python3 anchor_tracks.py board.kicad_pcb [--depth 0.20]"""
import sys, os, re, argparse, tempfile
import pcbnew
from pcbnew import ToMM, FromMM
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--depth', type=float, default=0.20); ap.add_argument('--dry', action='store_true')
args = ap.parse_args()

def main():
    board = pcbnew.LoadBoard(args.pcb); depth = FromMM(args.depth)
    pads = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname(): pads.setdefault(p.GetNetname(), []).append((fp.GetReference(), p))
    segs = [t for t in board.GetTracks() if t.GetClass() != 'PCB_VIA']
    notrack = [(z.GetBoundingBox(), z) for z in list(board.Zones()) + [z for fp in board.GetFootprints() for z in fp.Zones()] if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
    def forbidden(x, y, cx, cy, layer, w):      # would the new segment enter a rule area without tracks? (their outlines are boxes in this project)
        x0, x1, y0, y1 = min(x, cx) - w // 2, max(x, cx) + w // 2, min(y, cy) - w // 2, max(y, cy) + w // 2
        return any(z.IsOnLayer(layer) and bb.GetX() < x1 and bb.GetRight() > x0 and bb.GetY() < y1 and bb.GetBottom() > y0 for bb, z in notrack)
    have = {(t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetLayer()) for t in segs}
    todo = []
    for t in segs:
        for q in (t.GetStart(), t.GetEnd()):
            for ref, p in pads.get(t.GetNetname(), ()):
                if not p.IsOnLayer(t.GetLayer()): continue
                bb = p.GetBoundingBox()
                if not (bb.GetX() <= q.x <= bb.GetRight() and bb.GetY() <= q.y <= bb.GetBottom()): continue
                inset = min(q.x - bb.GetX(), bb.GetRight() - q.x, q.y - bb.GetY(), bb.GetBottom() - q.y)
                c = p.GetPosition()
                if inset >= depth or abs(q.x - c.x) + abs(q.y - c.y) < 20000: continue      # deep enough, or at the centre already
                key = (q.x, q.y, c.x, c.y, t.GetLayer())
                if key in have or (c.x, c.y, q.x, q.y, t.GetLayer()) in have or forbidden(q.x, q.y, c.x, c.y, t.GetLayer(), t.GetWidth()): continue
                have.add(key); todo.append((t, q.x, q.y, c.x, c.y, ref, p.GetNumber(), inset))
    for (t, x, y, cx, cy, ref, num, inset) in todo:
        print('  %-8s %s.%-3s track end (%.3f, %.3f) is %.3f mm inside the pad -> segment to the pad centre (%.3f, %.3f)' % (t.GetNetname(), ref, num, ToMM(x), ToMM(y), ToMM(inset), ToMM(cx), ToMM(cy)))
        if args.dry: continue
        k = pcbnew.PCB_TRACK(board); k.SetStart(pcbnew.VECTOR2I(x, y)); k.SetEnd(pcbnew.VECTOR2I(cx, cy)); k.SetWidth(t.GetWidth()); k.SetLayer(t.GetLayer()); k.SetNet(t.GetNet()); board.Add(k)
    print('anchor_tracks: %d track ends reinforced%s' % (len(todo), ' (dry run)' if args.dry else ''))
    if args.dry or not todo: return 0
    def errors_of(path):
        b = pcbnew.LoadBoard(path); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
        rep = os.path.join(tempfile.mkdtemp(prefix='anchor_'), 'drc.txt'); pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
        return b, sum(1 for blk in re.split(r'\n(?=\[)', open(rep).read()) if 'Severity: error' in blk)
    _, before = errors_of(args.pcb)                              # the board as it was (nothing is saved yet)
    pcbnew.SaveBoard(args.pcb, board)
    board, after = errors_of(args.pcb); pcbnew.SaveBoard(args.pcb, board)
    print('anchor_tracks: design rule errors and open connections before %d, now %d' % (before, after))
    return 1 if after > before else 0

if __name__ == '__main__':
    sys.exit(main())
