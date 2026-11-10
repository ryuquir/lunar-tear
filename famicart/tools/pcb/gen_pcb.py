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
from gen_sch import symbol_uuid          # footprint <-> schematic symbol link (stable UUIDs)
HW_LIB = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'hardware'))   # custom symbols/footprints
HW = _os.path.abspath(_os.environ.get('FC_HW_DIR', HW_LIB))                                                        # outputs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HW, 'famicart.kicad_pcb')
SYS_FP = '/usr/share/kicad/footprints'
THICKNESS = float(getattr(D, 'THICKNESS', 1.2))      # Famicom card edge: 1.2 mm board (docs/04_hardware.md)

# 2-layer stack-up written into the board file after saving (the KiCad 7 Python API cannot set the finish or the
# edge-connector flags): the Gerber job file then carries the thickness, ENIG and the bevelled edge connector.
STACKUP_2L = '''    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "core") (thickness %(core).3f) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
      (edge_connector bevelled)
    )
'''

def write_stackup(path, layers):
    """Insert the stack-up block at the start of (setup ...). Only for 2-layer boards; idempotent."""
    if layers != 2: return False
    s = open(path).read()
    if '(stackup' in s: return False
    i = s.find('(setup')
    if i < 0: raise SystemExit('no (setup ...) section in ' + path)
    j = s.find('\n', i) + 1
    open(path, 'w').write(s[:j] + STACKUP_2L % dict(core=THICKNESS - 0.09) + s[j:])
    return True

# Board outline (mm): HVC-TGROM-01 measurements from nesdev "Famicom cartridge dimensions"
SHELL = getattr(D, 'SHELL', None)       # shells.hvc_small() / hvc_large(): real HVC outline, slot, rib keep-outs (rev E2/F2 on)
BOARD_W, BODY_H, TAB_W, TAB_H = 90.0, float(SHELL['body_h'] if SHELL else getattr(D, 'BODY_H', 35.4)), 78.4, 10.7
TAB_X0 = (BOARD_W - TAB_W) / 2          # 5.8
TOTAL_H = BODY_H + TAB_H                 # 46.1 (rev A-E)
CHAMFER = 1.0

def rules():
    """(track, clearance, via diameter, via drill) in mm: the FC_TRACK / FC_CLEAR / FC_VIA / FC_VIA_DRILL environment
    variables, else the design's TRACK / CLEAR / VIA_DIA / VIA_DRILL, else the values used up to rev F2."""
    g = lambda env, attr, d: float(os.environ.get(env, getattr(D, attr, d)))
    return g('FC_TRACK', 'TRACK', 0.15), g('FC_CLEAR', 'CLEAR', 0.15), g('FC_VIA', 'VIA_DIA', 0.5), g('FC_VIA_DRILL', 'VIA_DRILL', 0.25)

JLC = bool(getattr(D, 'JLC_RULES', False))      # rev G on: silk minimums, no paste on hand-soldered parts (see main)
SILK_MIN_LINE, SILK_MIN_TEXT = 0.15, 1.0        # JLCPCB: silkscreen line >= 0.15 mm, text height >= 1.0 mm

def mm(x, y): return VECTOR2I(FromMM(x), FromMM(y))

def um(x, y):
    """A drawing end point, snapped to the 0.001 mm grid. pcbnew.FromMM() cuts off instead of rounding, so a value such as
    5.8 - 0.5 = 5.299999999999999 would become 5.299999 mm and leave a step of 1 nm between two outline items."""
    return VECTOR2I(int(round(x * 1000.0)) * 1000, int(round(y * 1000.0)) * 1000)

def add_seg(board, x1, y1, x2, y2, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(um(x1, y1)); s.SetEnd(um(x2, y2)); s.SetLayer(layer); s.SetWidth(FromMM(w)); board.Add(s)

def add_arc(board, start, mid, end, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(um(*start), VECTOR2I(int(round(mid[0] * 1e6)), int(round(mid[1] * 1e6))), um(*end)); s.SetLayer(layer); s.SetWidth(FromMM(w)); board.Add(s)

def add_outline(board, pts, fillets=(), r=0.0):
    """Closed polygon on Edge.Cuts. Vertices listed in `fillets` (concave corners) are drawn as arcs of radius r:
    a router bit cannot cut a sharp inner corner, so the radius is part of the drawing."""
    import math
    pts = [tuple(p) for p in pts]
    if pts[0] == pts[-1]: pts = pts[:-1]
    n = len(pts); isf = lambda p: r > 0 and any(abs(p[0] - f[0]) < 1e-6 and abs(p[1] - f[1]) < 1e-6 for f in fillets)
    ends = []                      # per vertex: (point where the incoming edge ends, point where the outgoing edge starts)
    for i, v in enumerate(pts):
        if not isf(v): ends.append((v, v)); continue
        a, b = pts[i - 1], pts[(i + 1) % n]
        ua = ((a[0] - v[0]), (a[1] - v[1])); la = math.hypot(*ua); ua = (ua[0] / la, ua[1] / la)
        ub = ((b[0] - v[0]), (b[1] - v[1])); lb = math.hypot(*ub); ub = (ub[0] / lb, ub[1] / lb)
        assert abs(ua[0] * ub[0] + ua[1] * ub[1]) < 1e-9 and la > 2 * r and lb > 2 * r, 'fillets are for right-angle corners with room for the radius'
        A = (v[0] + r * ua[0], v[1] + r * ua[1]); B = (v[0] + r * ub[0], v[1] + r * ub[1])
        C = (v[0] + r * (ua[0] + ub[0]), v[1] + r * (ua[1] + ub[1])); k = r / math.sqrt(2.0)
        add_arc(board, A, (C[0] - k * (ua[0] + ub[0]), C[1] - k * (ua[1] + ub[1])), B)
        ends.append((A, B))
    for i in range(n):
        (_, p0), (p1, _) = ends[i], ends[(i + 1) % n]
        add_seg(board, p0[0], p0[1], p1[0], p1[1])

def add_text(board, text, x, y, layer, size=1.0, thick=0.15, mirror=False):
    t = pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(mm(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(thick)); t.SetMirrored(mirror); board.Add(t)

def add_rule_area(board, name, pts, layers, tracks=True, vias=True, pour=True, footprints=False):
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers: ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowCopperPour(pour); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(footprints)
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts: ol.Append(FromMM(x), FromMM(y))
    board.Add(z); return z

FINGER_KEEP = 4.0       # below (tab base + this) the tab carries nothing but the fingers: no tracks, no vias, no mask
FINGER_TOP = 3.0        # the finger pads start this far below the tab base (Famicom_CardEdge_60)
FINGER_HOLE = 1.0       # JLCPCB: no plated holes within 1.0 mm of the gold fingers
FINGER_SETBACK = 1.2    # finger copper ends this far before the tab edge. JLCPCB's bevel drawing: copper cutback 1.15 mm
                        # for boards up to 1.6 mm (30 degree bevel); the four long fingers of the footprint end at 1.0 mm

def add_finger_mask(board):
    """JLCPCB gold-finger rule: 'The gold finger area must have the solder mask fully opened' (mask left between the
    fingers wears off when the card is inserted). One mask window per side over the part of the tab that is reserved
    for the fingers, reaching past the board edge. The window belongs to J1, and J1 gets the 'allow solder mask
    bridges' attribute, so the DRC accepts one aperture over pads of different nets. Returns the number of windows
    added (0 when they are already there)."""
    fp = board.FindFootprintByReference('J1')
    if fp is None: return 0
    if any(g.GetLayer() in (pcbnew.F_Mask, pcbnew.B_Mask) for g in fp.GraphicalItems()): return 0
    x0, x1 = TAB_X0, TAB_X0 + TAB_W
    for layer in (pcbnew.F_Mask, pcbnew.B_Mask):
        s = pcbnew.FP_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_RECT); s.SetLayer(layer); s.SetFilled(True); s.SetWidth(0)
        s.SetStart(mm(x0 - 0.5, BODY_H + FINGER_KEEP)); s.SetEnd(mm(x1 + 0.5, TOTAL_H + 0.5)); s.SetLocalCoord()
        fp.Add(s)
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_ALLOW_SOLDERMASK_BRIDGES)
    return 2

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
    ds.SetBoardThickness(FromMM(THICKNESS))
    TRK, CLR, VIA, VDR = rules()
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
        role = getattr(D, 'ROLE', {}).get(ref)
        if role:
            # hand-soldered modules look alike but carry different firmware: print "U1 reve_cpu" on the silk under each
            # one (footprint-owned text, along the module's long axis; KiCad moves / flips it with the footprint)
            # (JLCPCB designs: capitals, because lower-case letters of a 1.1 mm text are under the 1.0 mm minimum height)
            t = pcbnew.FP_TEXT(fp); t.SetText(('%s %s' % (ref, role)).upper() if JLC else '%s %s' % (ref, role)); t.SetLayer(pcbnew.F_SilkS)
            ts = 1.5 if 'Pico' in fpname else 1.1
            t.SetTextSize(VECTOR2I(FromMM(ts), FromMM(ts))); t.SetTextThickness(FromMM(ts * 0.14))
            t.SetPosition(mm(0, 6.0 if 'Pico' in fpname else 2.0)); t.SetLocalCoord()
            t.SetTextAngleDegrees(90); t.SetKeepUpright(True)
            fp.Add(t)
            if JLC and 'XIAO' in fpname:        # a XIAO fits turned by 180 degrees: mark its USB end like the Pico footprints do
                u = pcbnew.FP_TEXT(fp); u.SetText('USB'); u.SetLayer(pcbnew.F_SilkS)
                u.SetTextSize(VECTOR2I(FromMM(1.0), FromMM(1.0))); u.SetTextThickness(FromMM(0.15))
                u.SetPosition(mm(0, -8.2)); u.SetLocalCoord(); fp.Add(u)
        if JLC:
            # JLCPCB silkscreen minimums (line 0.15 mm, text height 1.0 mm): KiCad's library footprints use 0.12 mm lines
            for g in fp.GraphicalItems():
                if g.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS): continue
                if 'TEXT' in g.GetClass():
                    ts = max(ToMM(g.GetTextSize().x), ToMM(g.GetTextSize().y), SILK_MIN_TEXT) if min(ToMM(g.GetTextSize().x), ToMM(g.GetTextSize().y)) < SILK_MIN_TEXT else None
                    if ts: g.SetTextSize(VECTOR2I(FromMM(ts), FromMM(ts)))
                    if ToMM(g.GetTextThickness()) < SILK_MIN_LINE: g.SetTextThickness(FromMM(SILK_MIN_LINE))
                elif ToMM(g.GetWidth()) < SILK_MIN_LINE: g.SetWidth(FromMM(SILK_MIN_LINE))
            # hand-soldered parts (no LCSC number: modules, card socket, wire pads) get no solder paste: JLCPCB cuts
            # stencil openings only for the parts it places, and a bare ENIG pad is what hand soldering wants anyway
            if val.split(' (')[0] not in getattr(D, 'LCSC', {}):
                for pad in fp.Pads():
                    ls = pad.GetLayerSet()
                    if ls.Contains(pcbnew.F_Paste) or ls.Contains(pcbnew.B_Paste):
                        ls.RemoveLayer(pcbnew.F_Paste); ls.RemoveLayer(pcbnew.B_Paste); pad.SetLayerSet(ls)
                    # ... and thermal reliefs into the GND pour: a pad that is one piece with the pour is hard to heat with an iron
                    if (ref, pad.GetNumber()) in getattr(D, 'SOLID_PADS', ()):      # mounting tabs: one piece with the pour
                        pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
                    elif 'CardEdge' not in fpname:
                        pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL); pad.SetThermalSpokeWidth(FromMM(0.4)); pad.SetThermalGap(FromMM(0.3))
        cy = getattr(D, 'COURTYARD', {}).get(val.split(' (')[0])
        if cy:      # a courtyard of the size given (x, y of the unrotated footprint) instead of the library's: parts that stand closer than the library allows
            lines = [g for g in fp.GraphicalItems() if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd) and hasattr(g, 'GetStart0')]
            ox = max(abs(v) for g in lines for v in (g.GetStart0().x, g.GetEnd0().x)); oy = max(abs(v) for g in lines for v in (g.GetStart0().y, g.GetEnd0().y))
            for g in lines:
                a, e = g.GetStart0(), g.GetEnd0()
                g.SetStart0(VECTOR2I(int(round(a.x * FromMM(cy[0] / 2) / ox)), int(round(a.y * FromMM(cy[1] / 2) / oy))))
                g.SetEnd0(VECTOR2I(int(round(e.x * FromMM(cy[0] / 2) / ox)), int(round(e.y * FromMM(cy[1] / 2) / oy)))); g.SetDrawCoord()
        if JLC and getattr(D, 'GUARD_PADS', None) and val.split(' (')[0] not in getattr(D, 'LCSC', {}):
            for pad in fp.Pads():       # guard pads under the modules: covered by mask, a little larger than the module's pad
                if pad.GetNumber() in D.GUARD_PADS and not D.NETS.get(ref, {}).get(pad.GetNumber()):
                    ls = pad.GetLayerSet(); ls.RemoveLayer(pcbnew.F_Mask); ls.RemoveLayer(pcbnew.B_Mask); pad.SetLayerSet(ls)
                    g = FromMM(2 * D.GUARD_PADS[pad.GetNumber()]); pad.SetSize(VECTOR2I(pad.GetSize().x + g, pad.GetSize().y + g))
        if JLC and 'CardEdge' in fpname:    # shorten the fingers that reach into JLCPCB's bevel cutback (footprint at 0, 0)
            for pad in fp.Pads():
                # mask opening = pad: above the mask window other tracks pass 0.19 mm beside the finger tops, and
                # JLCPCB wants 0.09 mm between a mask opening and a neighbouring track (the footprint's 0.1 mm margin left 0.088)
                pad.SetLocalSolderMaskMargin(0)
                over = ToMM(pad.GetPosition().y) + ToMM(pad.GetSize().y) / 2 - (TAB_H - FINGER_SETBACK)
                if over > 1e-6:
                    pad.SetSize(VECTOR2I(pad.GetSize().x, pad.GetSize().y - FromMM(over)))
                    np_ = VECTOR2I(pad.GetPosition().x, pad.GetPosition().y - FromMM(over / 2)); pad.SetPosition(np_); pad.SetPos0(np_)
        board.Add(fp)
        fp.SetPosition(mm(x, y)); fp.SetOrientationDegrees(rot)
        if side == 'B': fp.Flip(fp.GetPosition(), False)
        fp.SetPath(pcbnew.KIID_PATH('/' + symbol_uuid(ref)))
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
    body_pts = SHELL['outline_body'] if SHELL else getattr(D, 'OUTLINE_BODY', None)
    if body_pts:
        # shell-specific body: points from the left tab corner (x0, H) up, over the top and down to the right tab corner
        # (x1, H); the card-edge tab is always the standard one
        close = lambda a, b: abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6
        assert close(body_pts[0], (x0, H)) and close(body_pts[-1], (x1, H)), 'outline_body must run from (x0, H) to (x1, H)'
        pts = [(x1, H), (x1, T - CHAMFER), (x1 - CHAMFER, T), (x0 + CHAMFER, T), (x0, T - CHAMFER), (x0, H)] + [tuple(p) for p in body_pts[1:-1]] + [(x1, H)]
    fil, fr = (SHELL.get('fillets', []), SHELL.get('fillet_r', 0.0)) if SHELL else ([], 0.0)
    add_outline(board, pts, fil, fr)
    for cut in (SHELL['cutouts'] if SHELL else getattr(D, 'CUTOUTS', [])):          # internal cut-outs (shell slot)
        add_outline(board, list(cut), fil, fr)
    # shell screw / boss holes (NPTH): D.HOLES = [(x, y, diameter_mm), ...]
    for i, (hx, hy, hd) in enumerate(getattr(D, 'HOLES', [])):
        fp = pcbnew.FOOTPRINT(board); fp.SetReference('H%d' % (i + 1)); fp.SetValue('shell hole'); fp.SetPosition(mm(hx, hy))
        fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        pad = pcbnew.PAD(fp); pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(VECTOR2I(FromMM(hd), FromMM(hd))); pad.SetDrillSize(VECTOR2I(FromMM(hd), FromMM(hd))); pad.SetPosition(mm(hx, hy))
        pad.SetLayerSet(pcbnew.LSET.AllCuMask()); pad.SetNumber('')
        fp.Add(pad); board.Add(fp)
    # soldermask keepout line (fab note): 4 mm below the tab base nothing but fingers
    add_seg(board, x0, H + FINGER_KEEP, x1, H + FINGER_KEEP, layer=pcbnew.F_Fab, w=0.1)
    add_text(board, ('FAB: %.1f mm FR4, ENIG, gold fingers with 30 deg bevel, vias tented' if JLC else 'FAB: %.1f mm FR4, ENIG/hard gold fingers, 2 mm x 30 deg bevel, vias tented') % THICKNESS, 45, 34.0, pcbnew.F_Fab, 0.8, 0.12)
    # board-level silk text: D.SILK_TEXT = [(text, x, y, 'F'|'B', size_mm), ...] (must sit clear of pads: check the DRC
    # report for silk_over_copper); default = the revision on the back, top centre
    for (stxt, sx, sy, sside, ssize) in getattr(D, 'SILK_TEXT', [('famicart %s  (back)' % getattr(D, 'REV', 'rev B'), 45, 2.0, 'B', 1.2)]):
        add_text(board, stxt, sx, sy, pcbnew.B_SilkS if sside == 'B' else pcbnew.F_SilkS, ssize, ssize / 6.0, mirror=(sside == 'B'))

    # rule areas: no tracks/vias/pour on the card-edge tab (fingers only; traces may enter the top 1.1 mm of a pad).
    # Under the modules nothing is needed here: the Pico footprints carry no-net pads under the module's exposed test
    # points (TP1-TP7) and USB shell legs, which keep tracks and vias of other nets away; all other vias are tented.
    KEEP_Y = H + FINGER_KEEP    # = solder-mask boundary: fingers only below this line
    if JLC: add_finger_mask(board)
    CU = [pcbnew.F_Cu, pcbnew.B_Cu] + [pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu][:NL - 2]
    add_rule_area(board, 'card_edge_keepout', [(x0 - 0.5, KEEP_Y), (x1 + 0.5, KEEP_Y), (x1 + 0.5, T + 0.5), (x0 - 0.5, T + 0.5)], CU)
    if JLC:     # vias stay FINGER_HOLE above the finger tops (tracks may still run down to the fingers)
        vy = H + FINGER_TOP - FINGER_HOLE
        add_rule_area(board, 'finger_via_keepout', [(x0 - 0.5, vy), (x1 + 0.5, vy), (x1 + 0.5, KEEP_Y), (x0 - 0.5, KEEP_Y)], CU,
                      tracks=False, vias=True, pour=False)
    if SHELL:
        for i, poly in enumerate(SHELL['route_keepouts']):      # notches, corner cuts, slot (+ edge clearance): no copper
            add_rule_area(board, 'shell_cut_%d' % i, poly, CU)
        for i, (side, poly) in enumerate(SHELL['comp_keepouts']):   # shell ribs / posts: no components on that side
            add_rule_area(board, 'shell_rib_%s%d' % (side, i), poly, [pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu],
                          tracks=False, vias=False, pour=False, footprints=True)
    # tracks laid before routing (supply trunk, ground straps): the autorouter keeps them (dsn_export: "protect")
    for net, w, pts in getattr(D, 'PREROUTE', []):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board); t.SetStart(mm(ax, ay)); t.SetEnd(mm(bx, by)); t.SetWidth(FromMM(w))
            t.SetLayer(pcbnew.F_Cu); t.SetNet(netmap[net]); board.Add(t)
    # GND pours on both layers over the body (not the tab)
    body = [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]
    if NL >= 4:   # inner planes: In1 = GND, last inner = +3V3 (6 layers: In2/In3 are extra signal layers)
        add_zone(board, netmap['GND'], pcbnew.In1_Cu, body)
        add_zone(board, netmap['+3V3'], pcbnew.In2_Cu if NL == 4 else pcbnew.In4_Cu, body)
    else:
        add_zone(board, netmap['GND'], pcbnew.F_Cu, body)
        add_zone(board, netmap['GND'], pcbnew.B_Cu, body)

    pcbnew.SaveBoard(OUT, board)
    write_stackup(OUT, NL)
    print('board written:', OUT, 'footprints', len(board.GetFootprints()), 'nets', board.GetNetCount(), 'thickness', THICKNESS)

if __name__ == '__main__':
    main()
