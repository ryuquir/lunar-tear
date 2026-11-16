#!/usr/bin/env python3
"""Reinforce track ends that only just reach their pad (run after routing, before widen_tracks.py).

A router may end a track a few hundredths of a millimetre inside a pad, at a rounded corner: KiCad counts that as
connected, but the copper joining track and pad is then a neck narrower than the track (0.08-0.10 mm was measured on
one such joint), which etching and the heat of hand soldering can open. For every track end that lies inside a pad of
its own net, closer to the pad's edge than --depth (default 0.20 mm), this tool adds a segment of the same width from
that end to the centre of the pad. The new copper lies inside the pad's own outline box, so no clearance changes;
the design rule check is run afterwards all the same. Ends on the gold fingers are left alone: the finger's centre
lies in the zone that is kept free of tracks. Vias get the same treatment (rev H on): a track end inside a via of its own
net, or with its round end over the via's rim, less than --depth from the via's edge, gets a segment to the via centre.
    python3 anchor_tracks.py board.kicad_pcb [--depth 0.20]"""
import sys, os, re, math, argparse, tempfile, subprocess
import pcbnew
from pcbnew import ToMM, FromMM
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--depth', type=float, default=0.20); ap.add_argument('--dry', action='store_true')
args = ap.parse_args()
DRC_CHILD = r'''
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
pcbnew.WriteDRCReport(b, sys.argv[2], pcbnew.EDA_UNITS_MILLIMETRES, True)
if len(sys.argv) > 3: pcbnew.SaveBoard(sys.argv[1], b)
sys.stdout.flush(); os._exit(0)
'''

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
    # the same for vias: a track end that only just reaches (or overlaps the rim of) a via of its own net joins it through
    # a neck narrower than the track (down to 0.03 mm measured on rev H); a segment to the via centre stays inside the
    # track's end and the via's copper
    vias = {}
    for v in board.GetTracks():
        if v.GetClass() == 'PCB_VIA': vias.setdefault(v.GetNetname(), []).append(v)
    for t in segs:
        for q in (t.GetStart(), t.GetEnd()):
            for v in vias.get(t.GetNetname(), ()):
                c = v.GetPosition(); r = v.GetWidth() // 2
                d = math.hypot(q.x - c.x, q.y - c.y)
                if d < 20000 or d >= r + t.GetWidth() // 2 or r - d >= depth: continue      # at the centre, apart, or deep inside
                key = (q.x, q.y, c.x, c.y, t.GetLayer())
                if key in have or (c.x, c.y, q.x, q.y, t.GetLayer()) in have or forbidden(q.x, q.y, c.x, c.y, t.GetLayer(), t.GetWidth()): continue
                have.add(key); todo.append((t, q.x, q.y, c.x, c.y, 'via', '', int(r - d)))
    for (t, x, y, cx, cy, ref, num, inset) in todo:
        what = 'the via' if ref == 'via' else 'the pad'
        print('  %-8s %s.%-3s track end (%.3f, %.3f) is %.3f mm inside %s -> segment to its centre (%.3f, %.3f)' % (t.GetNetname(), ref, num, ToMM(x), ToMM(y), ToMM(inset), what, ToMM(cx), ToMM(cy)))
        if args.dry: continue
        k = pcbnew.PCB_TRACK(board); k.SetStart(pcbnew.VECTOR2I(x, y)); k.SetEnd(pcbnew.VECTOR2I(cx, cy)); k.SetWidth(t.GetWidth()); k.SetLayer(t.GetLayer()); k.SetNet(t.GetNet()); board.Add(k)
    print('anchor_tracks: %d track ends reinforced%s' % (len(todo), ' (dry run)' if args.dry else ''))
    if args.dry or not todo: return 0
    def errors_of(path, save=False):
        """Error blocks of the rule check after a zone fill, in a child process (after a fill and a rule check this
        KiCad's Python binding cannot list tracks any more); save=True stores the filled board."""
        rep = os.path.join(tempfile.mkdtemp(prefix='anchor_'), 'drc.txt')
        subprocess.run([sys.executable, '-c', DRC_CHILD, path, rep] + (['save'] if save else []), capture_output=True, text=True)
        return [blk for blk in re.split(r'\n(?=\[)', open(rep).read()) if 'Severity: error' in blk]
    before = len(errors_of(args.pcb))                            # the board as it was (nothing is saved yet)
    pcbnew.SaveBoard(args.pcb, board)
    # a new segment fills the notch between a track end and its pad / via; where another net passes at the minimum
    # clearance right there, the segment comes too close: take such a segment out again (the joint stays as it was)
    new = {(round(ToMM(x), 3), round(ToMM(y), 3), round(ToMM(cx), 3), round(ToMM(cy), 3)) for (t, x, y, cx, cy, ref, num, inset) in todo}
    removed = 0
    for rnd in range(4):
        hit = set()
        for blk in errors_of(args.pcb):
            if blk.startswith('[unconnected_items]'): continue
            for px, py in re.findall(r'@\(([0-9.\-]+) mm, ([0-9.\-]+) mm\): Track', blk):
                px, py = float(px), float(py)
                hit |= {k for k in new if (abs(k[0] - px) < 0.002 and abs(k[1] - py) < 0.002) or (abs(k[2] - px) < 0.002 and abs(k[3] - py) < 0.002)}
        if not hit: break
        b2 = pcbnew.LoadBoard(args.pcb)
        for t in list(b2.GetTracks()):
            if t.GetClass() == 'PCB_VIA': continue
            k = (round(ToMM(t.GetStart().x), 3), round(ToMM(t.GetStart().y), 3), round(ToMM(t.GetEnd().x), 3), round(ToMM(t.GetEnd().y), 3))
            if k in hit: b2.Remove(t); removed += 1
        pcbnew.SaveBoard(args.pcb, b2); new -= hit
    after = len(errors_of(args.pcb, save=True))
    print('anchor_tracks: %d segments taken out again (rule errors next to them); design rule errors and open connections before %d, now %d' % (removed, before, after))
    return 1 if after > before else 0

if __name__ == '__main__':
    sys.exit(main())
