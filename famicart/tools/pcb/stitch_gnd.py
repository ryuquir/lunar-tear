#!/usr/bin/env python3
"""Add ground stitching vias to a routed 2-layer board (run after route_pcb.py / finish_route.py, before the export).

On a 2-layer board the two ground pours are cut into pieces by the tracks, and the autorouter joins them only where a
ground pad happens to need a via. This tool drops a ground via wherever both layers carry ground pour with room for
it, on a grid, so that every piece of pour is tied to the other layer in several places.

A position is used when, on BOTH layers, the via's copper stays inside the filled ground pour with 0.15 mm to spare
(the pour itself keeps its clearance to every other net), and it is at least
  0.45 mm (copper to copper) from every pad of any net or of no net (module pads, guard pads, gold fingers),
  1.0 mm (centre to centre) from every other via, and outside every rule area that forbids vias.
A piece of pour that this leaves without any via gets one on a finer search, where both layers allow it.
Afterwards the zones are filled again and the design rules checked; a via that takes part in a violation is removed.
    FC_DESIGN=design_revg python3 stitch_gnd.py board.kicad_pcb [--grid 2.0]"""
import os, sys, re, math, argparse, tempfile, importlib
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--grid', type=float, default=2.0); ap.add_argument('--net', default='GND')
args = ap.parse_args()
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
VIA, DRILL = float(getattr(D, 'VIA_DIA', 0.5)), float(getattr(D, 'VIA_DRILL', 0.3))
INSIDE, PAD_GAP, VIA_PITCH = 0.15, 0.45, 1.0
PM = pcbnew.SHAPE_POLY_SET.PM_FAST

def pour(board, layer, net):
    acc = pcbnew.SHAPE_POLY_SET()
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net or not z.IsOnLayer(layer): continue
        acc.BooleanAdd(pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(layer)), PM)
    acc.Deflate(FromMM(VIA / 2 + INSIDE), 16)
    return acc

def drc_points(board):
    rep = os.path.join(tempfile.gettempdir(), 'stitch_drc.txt')
    pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, False)
    txt = open(rep).read(); pts = []
    for blk in re.split(r'\n(?=\[)', txt):
        if 'Severity: error' not in blk or blk.startswith('[unconnected'): continue
        pts += [(float(a), float(b)) for a, b in re.findall(r'@\(([0-9.\-]+) mm, ([0-9.\-]+) mm\)', blk)]
    return txt.count('Severity: error'), pts

def main():
    board = pcbnew.LoadBoard(args.pcb)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    net = board.FindNet(args.net)
    regions = [pour(board, pcbnew.F_Cu, args.net), pour(board, pcbnew.B_Cu, args.net)]
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox(); pads.append((ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
    vias = [(ToMM(t.GetPosition().x), ToMM(t.GetPosition().y)) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    noviaz = [z.GetBoundingBox() for z in list(board.Zones()) + [z for fp in board.GetFootprints() for z in fp.Zones()] if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    noviaz = [(ToMM(b.GetX()), ToMM(b.GetY()), ToMM(b.GetRight()), ToMM(b.GetBottom())) for b in noviaz]
    bb = board.GetBoardEdgesBoundingBox(); r = VIA / 2
    added = []; mine_xy = []
    y = ToMM(bb.GetY()) + 1.0
    while y < ToMM(bb.GetBottom()) - 1.0:
        x = ToMM(bb.GetX()) + 1.0
        while x < ToMM(bb.GetRight()) - 1.0:
            pt = VECTOR2I(FromMM(x), FromMM(y))
            ok = all(reg.Contains(pt) for reg in regions)
            ok = ok and all(not (a - r <= x <= c + r and b - r <= y <= d + r) for (a, b, c, d) in noviaz)
            ok = ok and all(math.hypot(max(a - x, 0.0, x - c), max(b - y, 0.0, y - d)) >= r + PAD_GAP for (a, b, c, d) in pads)
            ok = ok and all(math.hypot(x - vx, y - vy) >= VIA_PITCH for (vx, vy) in vias)
            if ok:
                v = pcbnew.PCB_VIA(board); v.SetPosition(pt); v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetWidth(FromMM(VIA)); v.SetDrill(FromMM(DRILL)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net)
                board.Add(v); added.append(v); vias.append((x, y)); mine_xy.append((x, y))
            x += args.grid
        y += args.grid
    # second pass: a piece of pour that the grid gave no via at all (a narrow island between tracks) gets one, searched
    # on a 0.25 mm grid inside that piece. Without it such a piece hangs on one pad or track, or on nothing.
    pcbnew.SaveBoard(args.pcb, board); board = pcbnew.LoadBoard(args.pcb)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    net = board.FindNet(args.net); regions = [pour(board, pcbnew.F_Cu, args.net), pour(board, pcbnew.B_Cu, args.net)]
    vias = [(ToMM(t.GetPosition().x), ToMM(t.GetPosition().y)) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    gvias = [t.GetPosition() for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == args.net]
    extra = 0
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != args.net: continue
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(layer): continue
            polys = z.GetFilledPolysList(layer)
            for i in range(polys.OutlineCount()):
                piece = pcbnew.SHAPE_POLY_SET(); piece.AddOutline(polys.Outline(i))
                for h in range(polys.HoleCount(i)): piece.AddHole(polys.Hole(i, h))
                if any(piece.Contains(p) for p in gvias): continue
                pb = piece.BBox(); done = False; y = ToMM(pb.GetY()) + 0.3
                while y < ToMM(pb.GetBottom()) and not done:
                    x = ToMM(pb.GetX()) + 0.3
                    while x < ToMM(pb.GetRight()) and not done:
                        pt = VECTOR2I(FromMM(x), FromMM(y))
                        ok = piece.Contains(pt) and all(reg.Contains(pt) for reg in regions)
                        ok = ok and all(not (a - r <= x <= c + r and b - r <= y <= d + r) for (a, b, c, d) in noviaz)
                        ok = ok and all(math.hypot(max(a - x, 0.0, x - c), max(b - y, 0.0, y - d)) >= r + PAD_GAP for (a, b, c, d) in pads)
                        ok = ok and all(math.hypot(x - vx, y - vy) >= VIA_PITCH for (vx, vy) in vias)
                        if ok:
                            v = pcbnew.PCB_VIA(board); v.SetPosition(pt); v.SetViaType(pcbnew.VIATYPE_THROUGH)
                            v.SetWidth(FromMM(VIA)); v.SetDrill(FromMM(DRILL)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net)
                            board.Add(v); added.append(v); vias.append((x, y)); mine_xy.append((x, y)); gvias.append(pt); extra += 1; done = True
                        x += 0.25
                    y += 0.25
    print('pieces of pour without a via that got one:', extra)
    pcbnew.SaveBoard(args.pcb, board); board = pcbnew.LoadBoard(args.pcb)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    errors, pts = drc_points(board)
    removed = 0
    if errors:                 # take out stitching vias that sit at a violation, then check again
        mine = {(round(x, 3), round(y, 3)) for (x, y) in mine_xy}
        for t in list(board.GetTracks()):
            if t.GetClass() != 'PCB_VIA': continue
            k = (round(ToMM(t.GetPosition().x), 3), round(ToMM(t.GetPosition().y), 3))
            if k in mine and any(math.hypot(k[0] - px, k[1] - py) < 0.6 for px, py in pts): board.Remove(t); removed += 1
        pcbnew.SaveBoard(args.pcb, board); board = pcbnew.LoadBoard(args.pcb)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
        errors, pts = drc_points(board)
    pcbnew.SaveBoard(args.pcb, board)
    print('stitching vias added:', len(added) - removed, '(removed after DRC: %d)' % removed, '| DRC errors now:', errors,
          '| open connections:', board.GetConnectivity().GetUnconnectedCount(False))
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
