#!/usr/bin/env python3
"""Give every power island of a plane layer at least one via of its own net (designs with PLANES, rev H on).

The design's PLANES map puts islands of other nets into a plane layer (rev H, In2: a +1V1 island under each chip, one at
the +1V1 converter output, V5_IN islands at the converter inputs). The router joins a pin to such an island only where it
happens to drop a via inside it; it may instead join the pins with tracks (rev H, 0.12 mm board: the +1V1 pins of U1, U3
and U9 are joined on B.Cu under the chip). An island without a via of its net is a floating piece of copper: it does not
carry the current it was drawn for, and it still cuts a hole into the plane around it.

For every filled piece of such an island that holds no via of its net, this tool looks for a spot on a track of that net
(any signal layer) that lies inside the piece (the via's copper at least 0.1 mm inside the fill) where a via of the
design's size keeps the clearance to the copper of every other net on every layer and the hole spacing to every other
hole; it takes the spot with the most room and adds the via there. The zones are filled again and the design rules
checked; a new via that takes part in a violation is removed and the next spot is tried (3 rounds). A via joins a piece
when its copper touches the fill (its centre may lie outside).
KiCad removes an isolated piece of a zone only when another piece of that zone is joined; a zone none of whose pieces is
joined keeps its whole fill. With --drop-isolated, such zones (no spot for a via anywhere in them) are taken off the
board, so no floating copper is left on the plane layer; the plane around them fills the space at the next zone fill.
    FC_DESIGN=design_revh python3 island_vias.py board.kicad_pcb [--dry] [--drop-isolated]"""
import os, sys, re, math, argparse, tempfile, importlib
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--dry', action='store_true'); ap.add_argument('--rounds', type=int, default=3)
ap.add_argument('--drop-isolated', action='store_true', help='remove island zones that end up without any joined piece')
args = ap.parse_args()
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
VR, DR = float(getattr(D, 'VIA_DIA', 0.5)) / 2, float(getattr(D, 'VIA_DRILL', 0.3)) / 2
C = float(getattr(D, 'CLEAR', 0.15))
HOLE_GAP = 0.25            # hole edge to hole edge (the value finish_route.py keeps)
INSIDE = 0.10              # the via's copper this far inside the island's fill
STEP = 0.05                # spacing of the spots tried along a track

def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

def box_dist(px, py, x0, y0, x1, y1):
    return math.hypot(max(x0 - px, 0.0, px - x1), max(y0 - py, 0.0, py - y1))

def islands(board):
    """[(zone, layer id, piece index, SHAPE_POLY_SET of the piece)] for the zones of PLANES that are not board-wide."""
    out = []
    planes = getattr(D, 'PLANES', None) or {}
    for lname, entries in planes.items():
        lid = board.GetLayerID(lname); main = {net for net, shape in entries if shape == 'board'}
        for z in board.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(lid) or z.GetNetname() in main: continue
            polys = z.GetFilledPolysList(lid)
            for k in range(polys.OutlineCount()):
                piece = pcbnew.SHAPE_POLY_SET(); piece.AddOutline(polys.Outline(k))
                for h in range(polys.HoleCount(k)): piece.AddHole(polys.Hole(k, h))
                out.append((z, lid, k, piece))
    return out

def obstacles(board, net):
    """Copper of other nets as (kind, params, all_layers?, layer) in mm, and every hole as (x, y, r)."""
    obs, holes = [], []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            x, y = ToMM(t.GetPosition().x), ToMM(t.GetPosition().y)
            holes.append((x, y, ToMM(t.GetDrillValue()) / 2))
            if t.GetNetname() != net: obs.append(('circ', (x, y, ToMM(t.GetWidth()) / 2), None))
        elif t.GetNetname() != net:
            obs.append(('seg', (ToMM(t.GetStart().x), ToMM(t.GetStart().y), ToMM(t.GetEnd().x), ToMM(t.GetEnd().y), ToMM(t.GetWidth()) / 2), t.GetLayer()))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            x, y = ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
            if p.GetDrillSize().x > 0: holes.append((x, y, ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2))
            if p.GetNetname() == net and p.GetNetname() != '': continue
            bb = p.GetBoundingBox()
            box = (ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))
            if p.GetDrillSize().x > 0: obs.append(('box', box, None))
            else:
                for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if p.IsOnLayer(lid): obs.append(('box', box, lid))
    for z in list(board.Zones()) + [z for fp in board.GetFootprints() for z in fp.Zones()]:
        if z.GetIsRuleArea() and z.GetDoNotAllowVias():
            bb = z.GetBoundingBox(); obs.append(('keepout', (ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())), None))
    return obs, holes

def room(x, y, obs, holes):
    """Smallest copper gap (mm) a via at (x, y) would leave to other nets, or the hole gap if that is the tighter rule
    (expressed in the same scale: gap - required)."""
    worst = 9.0
    for kind, prm, lay in obs:
        if kind == 'seg':
            ax, ay, bx, by, hw = prm
            if min(ax, bx) - 1.5 > x or max(ax, bx) + 1.5 < x or min(ay, by) - 1.5 > y or max(ay, by) + 1.5 < y: continue
            g = seg_dist(x, y, ax, ay, bx, by) - hw - VR - C
        elif kind == 'circ':
            cx, cy, r = prm
            if abs(cx - x) > 1.5 or abs(cy - y) > 1.5: continue
            g = math.hypot(cx - x, cy - y) - r - VR - C
        elif kind == 'box':
            x0, y0, x1, y1 = prm
            if x0 - 1.5 > x or x1 + 1.5 < x or y0 - 1.5 > y or y1 + 1.5 < y: continue
            g = box_dist(x, y, x0, y0, x1, y1) - VR - C
        else:
            x0, y0, x1, y1 = prm
            g = box_dist(x, y, x0, y0, x1, y1) - VR
            if g >= 0: continue
        worst = min(worst, g)
    for hx, hy, hr in holes:
        if abs(hx - x) > 1.5 or abs(hy - y) > 1.5: continue
        worst = min(worst, math.hypot(hx - x, hy - y) - hr - DR - HOLE_GAP)
    return worst

def candidates(board, net, piece, skip):
    """Spots on the net's tracks inside the piece, best room first: [(room, x, y)]."""
    inner = pcbnew.SHAPE_POLY_SET(piece); inner.Deflate(FromMM(VR + INSIDE), 16)
    obs, holes = obstacles(board, net)
    seen, out = set(), []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA' or t.GetNetname() != net: continue
        ax, ay, bx, by = ToMM(t.GetStart().x), ToMM(t.GetStart().y), ToMM(t.GetEnd().x), ToMM(t.GetEnd().y)
        n = max(1, int(math.hypot(bx - ax, by - ay) / STEP))
        for s in range(n + 1):
            x, y = round(ax + (bx - ax) * s / n, 3), round(ay + (by - ay) * s / n, 3)
            if (x, y) in seen or (x, y) in skip: continue
            seen.add((x, y))
            if not inner.Contains(VECTOR2I(FromMM(x), FromMM(y))): continue
            g = room(x, y, obs, holes)
            if g >= 0.005: out.append((g, x, y))
    out.sort(reverse=True)
    return out

def drc_vias(path, ours):
    """Positions (from `ours`) of new vias named in a rule error, after a fresh zone fill."""
    b = pcbnew.LoadBoard(path); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
    rep = os.path.join(tempfile.mkdtemp(prefix='island_vias_'), 'drc.txt')
    pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    bad = set()
    for blk in re.split(r'\n(?=\[)', open(rep).read()):
        if 'Severity: error' not in blk or blk.startswith('[unconnected_items]'): continue
        for x, y in re.findall(r'@\(([0-9.\-]+) mm, ([0-9.\-]+) mm\): Via', blk):
            for (vx, vy) in ours:
                if abs(vx - float(x)) < 0.002 and abs(vy - float(y)) < 0.002: bad.add((vx, vy))
    return bad

def main():
    skip = set(); added = {}
    for rnd in range(args.rounds):
        board = pcbnew.LoadBoard(args.pcb); pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
        todo = []
        for z, lid, k, piece in islands(board):
            net = z.GetNetname()
            has = [v for v in vias if v.GetNetname() == net and piece.Collide(v.GetPosition(), v.GetWidth() // 2)]
            if not has: todo.append((z, lid, k, piece))
        name = lambda z, lid, k: '%s %s piece %d at (%.1f, %.1f)' % (z.GetNetname(), board.GetLayerName(lid), k,
                                                                   ToMM(z.GetBoundingBox().GetCenter().x), ToMM(z.GetBoundingBox().GetCenter().y))
        if rnd == 0: print('island_vias: %d island pieces without a via of their net' % len(todo))
        if not todo: break
        ours = []
        for z, lid, k, piece in todo:
            cand = candidates(board, z.GetNetname(), piece, skip)
            if not cand: print('  %s: no spot on a track of its net with room for a via' % name(z, lid, k)); continue
            g, x, y = cand[0]
            print('  %s: via at (%.3f, %.3f), %.3f mm to spare' % (name(z, lid, k), x, y, g))
            if args.dry: continue
            v = pcbnew.PCB_VIA(board); v.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetWidth(FromMM(2 * VR)); v.SetDrill(FromMM(2 * DR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(z.GetNet()); board.Add(v)
            ours.append((x, y))
        if args.dry or not ours: break
        pcbnew.SaveBoard(args.pcb, board)
        bad = drc_vias(args.pcb, ours)
        if not bad:
            for p in ours: added[p] = True
            break
        board = pcbnew.LoadBoard(args.pcb)
        for t in list(board.GetTracks()):
            if t.GetClass() == 'PCB_VIA' and (round(ToMM(t.GetPosition().x), 3), round(ToMM(t.GetPosition().y), 3)) in bad: board.Remove(t)
        pcbnew.SaveBoard(args.pcb, board)
        skip |= bad
        for p in ours:
            if p not in bad: added[p] = True
        print('  round %d: %d new vias in a rule error, removed; trying the next spots' % (rnd, len(bad)))
    print('island_vias: %d vias added' % len(added))
    if args.drop_isolated and not args.dry:
        board = pcbnew.LoadBoard(args.pcb); pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
        joined = {}
        for z, lid, k, piece in islands(board):
            joined.setdefault(z.m_Uuid.AsString(), [z, False])
            if any(v.GetNetname() == z.GetNetname() and piece.Collide(v.GetPosition(), v.GetWidth() // 2) for v in vias):
                joined[z.m_Uuid.AsString()][1] = True
        drop = [z for z, ok in joined.values() if not ok]
        for z in drop:
            bb = z.GetBoundingBox()
            print('  dropped: %s zone on %s at (%.1f, %.1f)-(%.1f, %.1f), no piece joined' % (z.GetNetname(), board.GetLayerName(z.GetFirstLayer()),
                  ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
            board.Remove(z)
        if drop:
            pcbnew.ZONE_FILLER(board).Fill(board.Zones()); pcbnew.SaveBoard(args.pcb, board)
        print('island_vias: %d island zones dropped' % len(drop))
    sys.stdout.flush(); os._exit(0)

if __name__ == '__main__':
    main()
