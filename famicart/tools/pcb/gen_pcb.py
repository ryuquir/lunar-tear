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
    NL = getattr(D, 'LAYERS', 2)
    ds.SetCopperLayerCount(NL)
    TRK = float(os.environ.get('FC_TRACK', '0.15')); CLR = float(os.environ.get('FC_CLEAR', '0.15'))
    VIA = float(os.environ.get('FC_VIA', '0.5')); VDR = float(os.environ.get('FC_VIA_DRILL', '0.25'))
    ds.m_TrackMinWidth = FromMM(TRK); ds.m_ViasMinSize = FromMM(VIA); ds.m_MinThroughDrill = FromMM(VDR)
    ds.m_MinClearance = FromMM(CLR); ds.m_HoleToHoleMin = FromMM(0.25); ds.m_ViasMinAnnularWidth = FromMM((VIA - VDR) / 2 - 0.005)
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
    CU = [pcbnew.F_Cu, pcbnew.B_Cu] + ([pcbnew.In1_Cu, pcbnew.In2_Cu] if NL == 4 else [])
    add_rule_area(board, 'card_edge_keepout', [(x0 - 0.5, KEEP_Y), (x1 + 0.5, KEEP_Y), (x1 + 0.5, T + 0.5), (x0 - 0.5, T + 0.5)], CU)
    ux, uy, _, _ = D.PARTS['U1'][4]
    # (vias under the Pico are allowed: they are tented by the solder mask; the Pico's own test points sit on our TP pads)
    # GND pours on both layers over the body (not the tab)
    body = [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]
    if NL == 4:   # inner planes: In1 = GND, In2 = +3V3 (outer layers stay free for routing)
        add_zone(board, netmap['GND'], pcbnew.In1_Cu, body)
        add_zone(board, netmap['+3V3'], pcbnew.In2_Cu, body)
    else:
        add_zone(board, netmap['GND'], pcbnew.F_Cu, body)
        add_zone(board, netmap['GND'], pcbnew.B_Cu, body)

    pcbnew.SaveBoard(OUT, board)
    print('board written:', OUT, 'footprints', len(board.GetFootprints()), 'nets', board.GetNetCount())

if __name__ == '__main__':
    main()
