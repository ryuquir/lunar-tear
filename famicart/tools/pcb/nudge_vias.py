#!/usr/bin/env python3
"""Move single vias of a routed board by a few hundredths of a millimetre (the design's VIA_NUDGE), with the track ends
that end in them.

Why: two vias of other nets whose antipads in a plane come within 0.22-0.25 mm of each other leave a copper web of
0.07 mm in the plane, because the zone fill's 0.25 mm minimum width pinches it instead of removing it
(tools/pcb/review/planes.py; rev H: VSEL_S and X89_8_D1 at x' -42.4, h 36.9, on In1, In2 and In4). JLCPCB's narrowest
inner copper is 0.09 mm. Moving one via by 0.03 mm away from the other keeps the web whole (0.25 mm); the planes'
holes and every track stay as they were.
    VIA_NUDGE = [(net, x, y, dx, dy, why)]      # KiCad mm: the via of `net` within 0.01 mm of (x, y) moves by (dx, dy)
    FC_DESIGN=design_revh python3 nudge_vias.py board.kicad_pcb [--dry]
Stops (exit 1) when a listed via is not found; the rule check of the later steps covers the clearances."""
import os, sys, argparse, importlib
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--dry', action='store_true')
args = ap.parse_args()
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))

def main():
    todo = getattr(D, 'VIA_NUDGE', ())
    if not todo: print('nudge_vias: the design has no VIA_NUDGE; nothing to do'); return 0
    board = pcbnew.LoadBoard(args.pcb)
    tracks = list(board.GetTracks())
    for net, x, y, dx, dy, why in todo:
        vias = [t for t in tracks if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net
                and abs(ToMM(t.GetPosition().x) - x) < 0.01 and abs(ToMM(t.GetPosition().y) - y) < 0.01]
        if len(vias) != 1:
            print('nudge_vias: %d vias of %s at (%.3f, %.3f), want 1' % (len(vias), net, x, y)); return 1
        v = vias[0]; old = v.GetPosition(); new = VECTOR2I(old.x + FromMM(dx), old.y + FromMM(dy))
        moved = 0
        for t in tracks:
            if t.GetClass() == 'PCB_VIA' or t.GetNetname() != net: continue
            if t.GetStart() == old: t.SetStart(new); moved += 1
            if t.GetEnd() == old: t.SetEnd(new); moved += 1
        v.SetPosition(new)
        print('  %s via (%.3f, %.3f) -> (%.3f, %.3f), %d track ends with it: %s' % (net, x, y, ToMM(new.x), ToMM(new.y), moved, why))
    print('nudge_vias: %d vias moved%s' % (len(todo), ' (dry run)' if args.dry else ''))
    if not args.dry: pcbnew.SaveBoard(args.pcb, board)
    return 0

if __name__ == '__main__':
    rc = main(); sys.stdout.flush(); os._exit(rc)
