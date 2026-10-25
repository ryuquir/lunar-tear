#!/usr/bin/env python3
"""Build hardware/famicart.kicad_pcb from design.py: footprints, nets, placement, outline, GND pours.
Routing is done afterwards by route_pcb.py (Freerouting)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
import os as _os, importlib as _il
_DESIGN = _os.environ.get('FC_DESIGN', 'design')
D = _il.import_module(_DESIGN)
HW_LIB = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'hardware'))   # custom symbols/footprints
HW = _os.path.abspath(_os.environ.get('FC_HW_DIR', HW_LIB))                                                        # outputs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HW, 'famicart.kicad_pcb')
SYS_FP = '/usr/share/kicad/footprints'

# Board outline (mm): HVC-TGROM-01 measurements from nesdev "Famicom cartridge dimensions"
BOARD_W, BODY_H, TAB_W, TAB_H = 90.0, 35.4, 78.4, 10.7
TAB_X0 = (BOARD_W - TAB_W) / 2          # 5.8
TOTAL_H = BODY_H + TAB_H                 # 46.1
CHAMFER = 1.0

def mm(x, y): return VECTOR2I(FromMM(x), FromMM(y))

def add_seg(board, x1, y1, x2, y2, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(mm(x1, y1)); s.SetEnd(mm(x2, y2)); s.SetLayer(layer); s.SetWidth(FromMM(w)); board.Add(s)

def add_text(board, text, x, y, layer, size=1.0, thick=0.15, mirror=False):
    t = pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(mm(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(thick)); t.SetMirrored(mirror); board.Add(t)

def add_rule_area(board, name, pts, layers, tracks=True, vias=True, pour=True):
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers: ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowCopperPour(pour); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts: ol.Append(FromMM(x), FromMM(y))
    board.Add(z); return z

def add_zone(board, net, layer, pts, clearance=0.25):
    z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNetCode(net.GetNetCode())
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts: ol.Append(FromMM(x), FromMM(y))
    z.SetLocalClearance(FromMM(clearance)); z.SetMinThickness(FromMM(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(FromMM(0.3)); z.SetThermalReliefSpokeWidth(FromMM(0.3)); z.SetIsFilled(False)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z); return z

def main():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    NL = int(os.environ.get('FC_LAYERS', getattr(D, 'LAYERS', 2)))     # 2, 4 or 6 copper layers
    ds.SetCopperLayerCount(NL)
    TRK = float(os.environ.get('FC_TRACK', '0.15')); CLR = float(os.environ.get('FC_CLEAR', '0.15'))
    VIA = float(os.environ.get('FC_VIA', '0.5')); VDR = float(os.environ.get('FC_VIA_DRILL', '0.25'))
    ds.m_TrackMinWidth = FromMM(TRK); ds.m_ViasMinSize = FromMM(VIA); ds.m_MinThroughDrill = FromMM(VDR)
    ds.m_MinClearance = FromMM(CLR); ds.m_HoleToHoleMin = FromMM(0.25); ds.m_ViasMinAnnularWidth = FromMM((VIA - VDR) / 2 - 0.005); ds.m_HoleClearance = FromMM(0.2)
    ds.m_SolderMaskMinWidth = FromMM(0.0); ds.m_SolderMaskExpansion = FromMM(0.0); ds.m_CopperEdgeClearance = FromMM(0.3)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetTrackWidth(FromMM(TRK)); nc.SetClearance(FromMM(CLR)); nc.SetViaDiameter(FromMM(VIA)); nc.SetViaDrill(FromMM(VDR))

    # nets
    names = sorted({n for pins in D.NETS.values() for n in pins.values() if n})
    netmap = {}
    for name in names:
        n = pcbnew.NETINFO_ITEM(board, name); board.Add(n); netmap[name] = n

    # footprints
    for ref, (lib, sym, val, fpid, (x, y, rot, side)) in D.PARTS.items():
        libname, fpname = fpid.split(':')
        libdir = os.path.join(HW_LIB, 'famicart.pretty') if libname == 'famicart' else os.path.join(SYS_FP, libname + '.pretty')
        fp = pcbnew.FootprintLoad(libdir, fpname)
        if fp is None: raise SystemExit(f'footprint not found: {fpid}')
        fp.SetReference(ref); fp.SetValue(val); fp.SetFPIDAsString(fpid)
        board.Add(fp)
        fp.SetPosition(mm(x, y)); fp.SetOrientationDegrees(rot)
        if side == 'B': fp.Flip(fp.GetPosition(), False)
        for pad in fp.Pads():
            net = D.NETS.get(ref, {}).get(pad.GetNumber())
            if net: pad.SetNet(netmap[net])
        # smaller reference text
        fp.Reference().SetTextSize(VECTOR2I(FromMM(0.7), FromMM(0.7))); fp.Reference().SetTextThickness(FromMM(0.1)); fp.Reference().SetLayer(pcbnew.B_Fab if side == 'B' else pcbnew.F_Fab)
        fp.Value().SetVisible(False)

    # USB-C: pre-route the A6<->B6 (D+) and A7<->B7 (D-) pad pairs. Pads interleave at 0.5 mm pitch, so one
    # bridge runs behind the pad row and the other in front; exported as fixed wires for the autorouter.
    def track(x1, y1, x2, y2, net, w=0.15):
        t = pcbnew.PCB_TRACK(board); t.SetStart(mm(x1, y1)); t.SetEnd(mm(x2, y2)); t.SetWidth(FromMM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(netmap[net]); board.Add(t)
    for (ra, pa, rb, pb, net, layer, w) in getattr(D, 'FIXED_LINKS', []):
        fa, fb = board.FindFootprintByReference(ra), board.FindFootprintByReference(rb)
        pB = [p for p in fb.Pads() if p.GetNumber() == pb][0].GetPosition()
        pA = min((p for p in fa.Pads() if p.GetNumber() == pa and p.GetDrillSize().x > 0), key=lambda p: (p.GetPosition() - pB).EuclideanNorm()).GetPosition()
        t = pcbnew.PCB_TRACK(board); t.SetStart(pA); t.SetEnd(pB); t.SetWidth(FromMM(w)); t.SetLayer(board.GetLayerID(layer)); t.SetNet(netmap[net]); board.Add(t)
    for j in [f for f in board.GetFootprints() if 'USB_C_Receptacle' in f.GetFPIDAsString()]:
        def padpos(n): p = j.FindPadByNumber(n).GetPosition(); return (ToMM(p.x), ToMM(p.y))
        dp, dm = j.FindPadByNumber('A6').GetNetname(), j.FindPadByNumber('A7').GetNetname()
        (ax, ay), (bx, by) = padpos('A6'), padpos('B6')
        sign = 1 if ToMM(j.GetPosition().y) < ay else -1
        yb = ay + sign * (1.45 / 2 + 0.33)
        track(ax, ay, ax, yb, dp); track(ax, yb, bx, yb, dp); track(bx, yb, bx, by, dp)
        (ax, ay), (bx, by) = padpos('A7'), padpos('B7')
        yf = ay - sign * (1.45 / 2 + 0.33)
        track(ax, ay, ax, yf, dm); track(ax, yf, bx, yf, dm); track(bx, yf, bx, by, dm)

    # 4-layer boards: GND / +3V3 are inner planes. Give every SMD pad of those nets a fixed via stub so the
    # autorouter never has to route them (dsn_export drops these nets); the KiCad zone fill does the rest.
    PLANE_NETS = {'GND': pcbnew.In1_Cu, '+3V3': (pcbnew.In2_Cu if NL == 4 else pcbnew.In4_Cu)} if (NL >= 4 and os.environ.get('FC_STUBS', '0') == '1') else {}   # FC_STUBS=1: fixed via stubs; default: the router fans out power on the inner layers
    stub_groups = []
    def add_via(x, y, net):
        v = pcbnew.PCB_VIA(board); v.SetPosition(mm(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(FromMM(VIA)); v.SetDrill(FromMM(VDR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(netmap[net]); board.Add(v); return v
    def add_track(x1, y1, x2, y2, net, layer, w=0.2):
        t = pcbnew.PCB_TRACK(board); t.SetStart(mm(x1, y1)); t.SetEnd(mm(x2, y2)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(netmap[net]); board.Add(t); return t
    import math
    # obstacles for stub-via placement: every pad (any layer: vias go through the board) and every via placed so far
    obstacles = []   # (x, y, radius_mm, net)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            r = math.hypot(ToMM(pad.GetSize().x), ToMM(pad.GetSize().y)) / 2          # half diagonal: safe for rectangles
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: r = max(r, ToMM(pad.GetDrillSize().x) / 2 + 0.3)
            obstacles.append((ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y), r, pad.GetNetname(), pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD, pad.GetLayerSet().Contains(pcbnew.B_Cu)))
    def via_margin(x, y, net):
        """Smallest (distance - required) over all obstacles; >= 0 means the via fits."""
        if not (0.8 <= x <= BOARD_W - 0.8 and 0.8 <= y <= BODY_H - 0.6): return -9.0
        worst = 9.0
        for (ox, oy, r, onet, smd, onb) in obstacles:
            if r > 5: continue
            d = math.hypot(x - ox, y - oy)
            if onet == 'VIA': need = VIA + 0.15                              # via to via (hole-to-hole 0.25)
            elif onet.startswith('TRK:'): need = 0.0 if onet[4:] == net else VIA / 2 + r + CLR + 0.03
            else: need = VIA / 2 + r + (0.0 if onet == net else CLR + 0.05)
            worst = min(worst, d - need)
        return worst
    def via_ok(x, y, net, layer_b): return via_margin(x, y, net) >= 0.0
    def track_margin(x1, y1, x2, y2, w, net, layer_b):
        """Clearance margin of a straight stub track (same outer layer as the pad) against other-net items."""
        worst = 9.0; n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.15) + 1)
        for i in range(1, n):
            t = i / n; x = x1 + (x2 - x1) * t; y = y1 + (y2 - y1) * t
            for (ox, oy, r, onet, smd, onb) in obstacles:
                if r > 5 or onet == net: continue
                if onet.startswith('TRK:'):
                    if onet[4:] == net or onb != layer_b: continue                        # same net, or on the other side
                elif smd and onb != layer_b: continue                                     # SMD pad on the other side
                d = math.hypot(x - ox, y - oy) - (w / 2 + r + CLR + 0.03)
                if d < worst: worst = d
        return worst
    def note_track(x1, y1, x2, y2, w, net, layer_b=False):
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.1) + 1)
        for i in range(n + 1):
            t = i / n; obstacles.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, w / 2 + 0.05, 'TRK:' + net, False, layer_b))
    def place_stub(fp, n, pads, pad0):
        cx, cy = ToMM(fp.GetPosition().x), ToMM(fp.GetPosition().y)
        xs = [p[0] for p in pads]; ys = [p[1] for p in pads]
        gx, gy = sum(xs) / len(xs), sum(ys) / len(ys)
        dx, dy = gx - cx, gy - cy
        if abs(dx) < 0.05 and abs(dy) < 0.05: dx = 1.0
        ux, uy = ((1.0 if dx > 0 else -1.0), 0.0) if abs(dx) >= abs(dy) else (0.0, (1.0 if dy > 0 else -1.0))
        bb = pad0.GetBoundingBox(); hx, hy = ToMM(bb.GetWidth()) / 2, ToMM(bb.GetHeight()) / 2
        half = hx if ux else hy
        layer_b = pad0.GetLayerSet().Contains(pcbnew.B_Cu)
        layer = pcbnew.B_Cu if layer_b else pcbnew.F_Cu
        w = 0.2 if len(pads) == 1 else 0.15
        # two-segment stub: pad -> P1 (straight out of the pad, in its own lane) -> via. Candidate vias on a grid.
        p1d = half + 0.38
        p1 = [(px + ux * p1d, py + uy * p1d) for (px, py) in pads]
        p1x, p1y = sum(q[0] for q in p1) / len(p1), sum(q[1] for q in p1) / len(p1)
        cands = []
        for extra in (VIA / 2 + CLR + 0.05, 0.6, 0.9, 1.2, 1.6, 2.0, 2.5):
            for lat in (0.0, 0.45, -0.45, 0.9, -0.9, 1.35, -1.35, 1.8, -1.8):
                cands.append((p1x + ux * extra - uy * lat, p1y + uy * extra + ux * lat))
        best = None; bestm = -99
        for (vx, vy) in cands:
            m = via_margin(vx, vy, n)
            if m >= 0:
                m2 = min(track_margin(px, py, qx, qy, w, n, layer_b) for (px, py), (qx, qy) in zip(pads, p1))
                m3 = min(track_margin(qx, qy, vx, vy, w, n, layer_b) for (qx, qy) in p1)
                m = min(m, m2, m3)
            if m >= 0: best = (vx, vy); bestm = m; break
            if m > bestm: bestm = m; best = (vx, vy)
        vx, vy = best
        if bestm < 0: print('stub skipped (router will do it):', fp.GetReference(), n, 'at', round(gx, 2), round(gy, 2), 'margin', round(bestm, 2)); return False
        items = []
        for (px, py), (qx, qy) in zip(pads, p1):
            items.append(add_track(px, py, qx, qy, n, layer, w)); note_track(px, py, qx, qy, w, n, layer_b)
            items.append(add_track(qx, qy, vx, vy, n, layer, w)); note_track(qx, qy, vx, vy, w, n, layer_b)
        items.append(add_via(vx, vy, n)); obstacles.append((vx, vy, VIA / 2, 'VIA', False, layer_b))
        stub_groups.append(items); return True
    STUB_SKIP = set(os.environ.get('FC_STUB_SKIP', 'U1,U2').split(','))
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference() == 'J1'):
        if not PLANE_NETS: break
        if fp.GetReference() in STUB_SKIP: continue
        if fp.GetReference() == 'J1':
            for pad in fp.Pads():
                if pad.GetNetname() in PLANE_NETS:          # finger: short stub up into the body, then a via into the plane
                    px = ToMM(pad.GetPosition().x); layer = pcbnew.B_Cu if pad.GetLayerSet().Contains(pcbnew.B_Cu) else pcbnew.F_Cu
                    cands = [(px + dx, BODY_H - dy) for dy in (0.9, 1.3, 1.7) for dx in (0.0, 0.6, -0.6, 1.2, -1.2, 1.8, -1.8, 2.4)]
                    vx, vy = max(cands, key=lambda c: via_margin(c[0], c[1], pad.GetNetname()))
                    add_track(px, BODY_H + 3.5, px, BODY_H - 0.3, pad.GetNetname(), layer, 0.4); add_track(px, BODY_H - 0.3, vx, vy, pad.GetNetname(), layer, 0.4)
                    add_via(vx, vy, pad.GetNetname()); obstacles.append((vx, vy, VIA / 2, 'VIA', False, False))
                    note_track(px, BODY_H + 3.5, px, BODY_H - 0.3, 0.4, pad.GetNetname(), layer == pcbnew.B_Cu); note_track(px, BODY_H - 0.3, vx, vy, 0.4, pad.GetNetname(), layer == pcbnew.B_Cu)
            continue
        groups = {}
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n not in PLANE_NETS or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            px, py = ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y)
            placed = False
            for g in groups.setdefault(n, []):
                if abs(g['x'] - px) + abs(g['y'] - py) < 0.9: g['pads'].append((px, py)); placed = True; break
            if not placed: groups[n].append({'x': px, 'y': py, 'pads': [(px, py)], 'pad': pad})
        for n, gl in groups.items():
            for g in gl: place_stub(fp, n, g['pads'], g['pad'])

    # DRC-driven cleanup: every pre-routed stub item (track/via) involved in a clearance/hole violation is removed,
    # together with the rest of its stub chain, so the autorouter fans out that pad instead.
    if PLANE_NETS:
        import re as _re, tempfile
        pcbnew.SaveBoard(OUT, board); board = pcbnew.LoadBoard(OUT)          # netclasses only resolve on a loaded board
        netmap = {name: board.FindNet(name) for name in names}
        for _round in range(6):
            rep = os.path.join(tempfile.gettempdir(), 'famicart_stub_drc.txt')
            board.BuildConnectivity(); pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, False)
            txt = open(rep).read()
            if _round == 0: open(os.path.join(HW, 'stub_drc_round0.txt'), 'w').write(txt)
            pts = set()
            for blk in txt.split('\n['):
                if not blk.startswith(('clearance]', 'hole_clearance]', 'hole_near_hole]')): continue   # (no outline or zones yet: edge and dangling checks happen later)
                for a_, b2 in _re.findall(r'@\(([0-9.]+) mm, ([0-9.]+) mm\)', blk): pts.add((round(float(a_), 2), round(float(b2), 2)))
            if not pts: break
            doomed = []; doomed_ids = set()
            def uid(t): return t.m_Uuid.AsString()
            for t in list(board.GetTracks()):
                poss = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
                if any((round(ToMM(p_.x), 2), round(ToMM(p_.y), 2)) in pts for p_ in poss): doomed.append(t); doomed_ids.add(uid(t))
            # follow the stub chain (same net, touching end points), but never into a pad centre
            padpos = {(round(ToMM(pd.GetPosition().x), 2), round(ToMM(pd.GetPosition().y), 2)) for fp in board.GetFootprints() for pd in fp.Pads()}
            grow = True
            while grow:
                grow = False
                ends = set()
                for t in doomed:
                    for p_ in ([t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]):
                        k = (round(ToMM(p_.x), 2), round(ToMM(p_.y), 2))
                        if k not in padpos: ends.add((k, t.GetNetname()))
                for t in list(board.GetTracks()):
                    if uid(t) in doomed_ids: continue
                    for p_ in ([t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]):
                        if ((round(ToMM(p_.x), 2), round(ToMM(p_.y), 2)), t.GetNetname()) in ends: doomed.append(t); doomed_ids.add(uid(t)); grow = True; break
            if not doomed: print('stub cleanup: DRC points not on stubs:', sorted(pts)[:6]); break
            for t in doomed: board.Remove(t)
            print('stub cleanup round', _round, ': removed', len(doomed), 'stub items for', len(pts), 'DRC points')

    # outline: body + card-edge tab with 1 mm chamfers at the tab tip
    W, H, T = BOARD_W, BODY_H, TOTAL_H
    x0, x1 = TAB_X0, TAB_X0 + TAB_W
    pts = [(0, 0), (W, 0), (W, H), (x1, H), (x1, T - CHAMFER), (x1 - CHAMFER, T), (x0 + CHAMFER, T), (x0, T - CHAMFER), (x0, H), (0, H), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]): add_seg(board, ax, ay, bx, by)
    # soldermask keepout line (fab note): 4 mm below the tab base nothing but fingers
    add_seg(board, x0, H + 4.0, x1, H + 4.0, layer=pcbnew.F_Fab, w=0.1)
    add_text(board, 'FAB: 1.2 mm FR4, ENIG/hard gold fingers, 2 mm x 30 deg bevel, vias tented', 45, 34.0, pcbnew.F_Fab, 0.8, 0.12)
    add_text(board, 'famicart %s  (back)' % getattr(D, 'REV', 'rev B'), 45, 2.0, pcbnew.B_SilkS, 1.2, 0.2, mirror=True)

    # rule areas: no tracks/vias/pour on the card-edge tab (fingers only; traces may enter the top 1.1 mm of a pad),
    # and no vias under the Pico module (its underside carries exposed test pads)
    KEEP_Y = H + 4.0            # = solder-mask boundary: fingers only below this line
    CU = [pcbnew.F_Cu, pcbnew.B_Cu] + [pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu][:NL - 2]
    add_rule_area(board, 'card_edge_keepout', [(x0 - 0.5, KEEP_Y), (x1 + 0.5, KEEP_Y), (x1 + 0.5, T + 0.5), (x0 - 0.5, T + 0.5)], CU)
    ux, uy, _, _ = D.PARTS['U1'][4]
    # (vias under the Pico are allowed: they are tented by the solder mask; the Pico's own test points sit on our TP pads)
    # GND pours on both layers over the body (not the tab)
    body = [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]
    if NL >= 4:   # inner planes: In1 = GND, last inner = +3V3 (6 layers: In2/In3 are extra signal layers)
        add_zone(board, netmap['GND'], pcbnew.In1_Cu, body)
        add_zone(board, netmap['+3V3'], pcbnew.In2_Cu if NL == 4 else pcbnew.In4_Cu, body)
    else:
        add_zone(board, netmap['GND'], pcbnew.F_Cu, body)
        add_zone(board, netmap['GND'], pcbnew.B_Cu, body)

    pcbnew.SaveBoard(OUT, board)
    print('board written:', OUT, 'footprints', len(board.GetFootprints()), 'nets', board.GetNetCount())

if __name__ == '__main__':
    main()
