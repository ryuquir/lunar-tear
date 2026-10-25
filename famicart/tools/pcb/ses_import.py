"""Import a Specctra session (.ses) produced by Freerouting into a pcbnew BOARD: tracks and vias."""
import pcbnew
from pcbnew import VECTOR2I, FromMM
from sexp import parse, find, find_all, Sym

def import_ses(board, path, res=10, via_dia_mm=0.6, via_drill_mm=0.3):
    ses = parse(open(path).read())
    routes = find(ses, 'routes')
    # Freerouting writes coordinates in its own internal units regardless of the declared resolution;
    # derive the units-per-mm scale from a placed component whose position we know.
    scale = None
    pl = find(ses, 'placement')
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if pl:
        for comp in find_all(pl, 'component'):
            for place in find_all(comp, 'place'):
                ref = str(place[1]); fp = fps.get(ref)
                if fp is None: continue
                xmm = pcbnew.ToMM(fp.GetPosition().x)
                if abs(xmm) > 1.0: scale = float(place[2]) / xmm; break
            if scale: break
    if not scale:
        r = find(routes, 'resolution'); res = int(r[2]) if r else res
        scale = res * 1000.0
    def P(v): return FromMM(float(v) / scale)
    layer_id = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'In1.Cu': pcbnew.In1_Cu, 'In2.Cu': pcbnew.In2_Cu}
    netmap = {board.GetNetInfo().GetNetItem(i).GetNetname(): board.GetNetInfo().GetNetItem(i) for i in range(board.GetNetCount())}
    ntracks = nvias = 0
    # pre-routed (fixed) items come back in the session as well: do not add them twice
    have_vias = {(t.GetPosition().x // 1000, t.GetPosition().y // 1000) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA'}
    have_trk = {(t.GetStart().x // 1000, t.GetStart().y // 1000, t.GetEnd().x // 1000, t.GetEnd().y // 1000, t.GetLayer()) for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK'}
    have_trk |= {(e, f, a, b, l) for (a, b, e, f, l) in have_trk}
    for net in find_all(find(routes, 'network_out'), 'net'):
        name = str(net[1]); ni = netmap.get(name)
        if ni is None: continue
        for w in find_all(net, 'wire'):
            p = find(w, 'path'); layer = layer_id[str(p[1])]; width = P(p[2])
            pts = [(P(p[i]), P(p[i + 1])) for i in range(3, len(p) - 1, 2)]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if (int(x1) // 1000, int(-y1) // 1000, int(x2) // 1000, int(-y2) // 1000, layer) in have_trk: continue
                t = pcbnew.PCB_TRACK(board); t.SetStart(VECTOR2I(int(x1), int(-y1))); t.SetEnd(VECTOR2I(int(x2), int(-y2)))
                t.SetWidth(int(width)); t.SetLayer(layer); t.SetNet(ni); board.Add(t); ntracks += 1
        for v in find_all(net, 'via'):
            name_ps = str(v[1]); x, y = P(v[2]), P(v[3])
            if (int(x) // 1000, int(-y) // 1000) in have_vias: continue
            dia, drill = FromMM(via_dia_mm), FromMM(via_drill_mm)   # single via class, sizes known from the DSN export
            via = pcbnew.PCB_VIA(board); via.SetPosition(VECTOR2I(int(x), int(-y))); via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetWidth(int(dia)); via.SetDrill(int(drill)); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(ni); board.Add(via); nvias += 1
    return ntracks, nvias
