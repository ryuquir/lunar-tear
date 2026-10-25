"""Minimal Specctra DSN exporter for a pcbnew BOARD (2-layer, SMD/THT pads, outline, nets, rules)."""
import math, os
import pcbnew
from pcbnew import ToMM

RES = 10  # units per micrometre -> coordinates in 0.1 um
def U(mm): return int(round(mm * 1000 * RES))
LAYERS = [(pcbnew.F_Cu, 'F.Cu'), (pcbnew.B_Cu, 'B.Cu')]
PLANE_NETS = ()
POWER_NETS = ()
def set_layers(board):
    """Signal layers offered to the autorouter. On 4-layer boards the inner layers are solid GND/+3V3 planes that
    the router must not touch (FC_DSN_INNER=1 offers them anyway), and the plane nets are left out of the netlist:
    gen_pcb already gave every plane pad a fixed via stub."""
    global LAYERS, PLANE_NETS, POWER_NETS
    ncu = board.GetCopperLayerCount()
    stubs = os.environ.get('FC_STUBS', '0') == '1'
    if ncu == 6:      # F sig | In1 GND | In2 sig | In3 sig | In4 +3V3 | B sig  -> the router only sees the 4 signal layers
        LAYERS = [(pcbnew.F_Cu, 'F.Cu'), (pcbnew.In2_Cu, 'In2.Cu'), (pcbnew.In3_Cu, 'In3.Cu'), (pcbnew.B_Cu, 'B.Cu')]
    elif ncu == 4:
        inner = (os.environ.get('FC_DSN_INNER', '1') == '1') and not stubs
        LAYERS = [(pcbnew.F_Cu, 'F.Cu')] + ([(pcbnew.In1_Cu, 'In1.Cu'), (pcbnew.In2_Cu, 'In2.Cu')] if inner else []) + [(pcbnew.B_Cu, 'B.Cu')]
        if stubs: LAYERS = [(pcbnew.F_Cu, 'F.Cu'), (pcbnew.In1_Cu, 'In1.Cu'), (pcbnew.In2_Cu, 'In2.Cu'), (pcbnew.B_Cu, 'B.Cu')]
    else:
        LAYERS = [(pcbnew.F_Cu, 'F.Cu'), (pcbnew.B_Cu, 'B.Cu')]
    PLANE_NETS = ('GND', '+3V3') if (ncu >= 4 and stubs) else ()      # stubs: pads that already have a via stub are left out of the netlist
    POWER_NETS = ('GND', '+3V3') if ncu == 4 else ()                   # 4 layers: power nets may use the plane layers, signals may not
def lname_of(lid): return dict(LAYERS).get(lid, 'F.Cu')

def q(s): return '"' + s.replace('"', '') + '"'

def pad_padstack(pad, fp_flipped):
    """Return (name, definition_lines) for a pad's padstack."""
    sx, sy = ToMM(pad.GetSize().x), ToMM(pad.GetSize().y)
    if pad.GetShape() == pcbnew.PAD_SHAPE_CUSTOM:        # custom pads (e.g. rounded solder-jumper pads): use the real extent
        bb = pad.GetBoundingBox(); sx, sy = ToMM(bb.GetWidth()), ToMM(bb.GetHeight())
        rot_fix = True
    else: rot_fix = False
    rot = pad.GetOrientationDegrees() - pad.GetParent().GetOrientationDegrees()
    if not rot_fix and abs(((rot + 90) % 180) - 90) > 1e-3 and abs(((rot) % 180) - 90) < 1e-3: sx, sy = sy, sx  # 90/270 deg pad (bbox already oriented)
    shape = pad.GetShape()
    layers = []
    ls = pad.GetLayerSet()
    for lid, lname in LAYERS:
        if ls.Contains(lid): layers.append(lname)
    if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,) : layers = [l for _, l in LAYERS]
    tag = ''.join('T' if l == 'F.Cu' else 'B' for l in layers) if len(layers) == 1 else 'A'
    hx, hy = U(sx) // 2, U(sy) // 2
    if shape == pcbnew.PAD_SHAPE_CIRCLE:
        name = f'Round[{tag}]Pad_{U(sx)}_um'
        shapes = [f'(shape (circle {l} {U(sx)}))' for l in layers]
    elif shape == pcbnew.PAD_SHAPE_OVAL:
        name = f'Oval[{tag}]Pad_{U(sx)}x{U(sy)}_um'
        if sx >= sy: w = U(sy); d = (U(sx) - w) // 2; shapes = [f'(shape (path {l} {w} {-d} 0 {d} 0))' for l in layers]
        else: w = U(sx); d = (U(sy) - w) // 2; shapes = [f'(shape (path {l} {w} 0 {-d} 0 {d}))' for l in layers]
    else:  # rect / roundrect / others -> rectangle
        name = f'Rect[{tag}]Pad_{U(sx)}x{U(sy)}_um'
        shapes = [f'(shape (rect {l} {-hx} {-hy} {hx} {hy}))' for l in layers]
    return name, f'(padstack {q(name)} ' + ' '.join(shapes) + ' (attach off))'

def export(board, path, outline_mm, via_dia=0.6, via_drill=0.3, track=0.25, clearance=0.2, pad_clearance=0.25, via_via=0.3, planes=False):
    set_layers(board)
    padstacks = {}
    images = {}
    placements = []
    npth_keepouts = []
    # footprints: image per footprint-library-id (+ side), pins in local unrotated coords
    for fp in board.GetFootprints():
        fpid = fp.GetFPIDAsString() or fp.GetReference()
        flipped = fp.IsFlipped()
        img_name = fpid.replace(':', '_') + ('_B' if flipped else '')
        pos = fp.GetPosition(); rot = fp.GetOrientationDegrees()
        ox, oy = ToMM(pos.x), -ToMM(pos.y)
        placements.append((img_name, fp.GetReference(), U(ox), U(oy), 'front', rot))
        for pad in fp.Pads():                             # NPTH mounting holes of EVERY instance (also the ones sharing an image)
            if pad.GetNumber() == '':
                pp = pad.GetPosition(); d = max(ToMM(pad.GetDrillSize().x), ToMM(pad.GetSize().x)) + 2 * 0.5
                npth_keepouts.append(f'    (keepout "npth_{fp.GetReference()}_{len(npth_keepouts)}" (circle signal {U(d)} {U(ToMM(pp.x))} {-U(ToMM(pp.y))}))')
        if img_name in images: continue
        # image-local pin coordinates derived from the actual pad positions:
        #   P = O + R(rot) * L  (for 'back' placement Freerouting applies the mirror itself)
        th = math.radians(rot); c_, s_ = math.cos(-th), math.sin(-th)
        pins = []
        edge = 'CardEdge' in fpid
        seen_ids = {}
        for pad in fp.Pads():
            if pad.GetNumber() == '':                     # NPTH mounting hole (keepout emitted above)
                continue
            pp = pad.GetPosition(); dx, dy = ToMM(pp.x) - ox, -ToMM(pp.y) - oy
            lx, ly = dx * c_ - dy * s_, dx * s_ + dy * c_
            if edge:
                w = ToMM(pad.GetSize().x); h = ToMM(pad.GetSize().y)
                layer = 'B.Cu' if pad.GetLayerSet().Contains(pcbnew.B_Cu) else 'F.Cu'
                name = f'Finger[{layer[0]}]_{U(w)}x{U(1.0)}_um'
                padstacks[name] = f'(padstack {q(name)} (shape (rect {layer} {-U(w)//2} {-U(0.5)} {U(w)//2} {U(0.5)})) (attach off))'
                ly = ly + h / 2 - 0.5     # top 1.0 mm strip (DSN y is up; pad extends downward)
            else:
                name, defn = pad_padstack(pad, flipped)
                padstacks[name] = defn
            pid = pad.GetNumber(); n = seen_ids.get(pid, 0); seen_ids[pid] = n + 1
            if n: pid = f'{pid}@{n}'
            pins.append(f'(pin {q(name)} {q(pid)} {U(lx)} {U(ly)})')
        images[img_name] = f'(image {q(img_name)} ' + ' '.join(pins) + ')'
    via_name = f'Via[0-1]_{U(via_dia)}:{U(via_drill)}_um'
    padstacks[via_name] = f'(padstack {q(via_name)} ' + ' '.join(f'(shape (circle {l} {U(via_dia)}))' for _, l in LAYERS) + ' (attach off))'
    # nets (pads that already carry a fixed power stub are not handed to the router)
    stubbed = set()
    if PLANE_NETS:
        ends = {}
        for t in board.GetTracks():
            if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in PLANE_NETS:
                ends.setdefault((t.GetStart().x, t.GetStart().y), t.GetNetname()); ends.setdefault((t.GetEnd().x, t.GetEnd().y), t.GetNetname())
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() in PLANE_NETS and ends.get((pad.GetPosition().x, pad.GetPosition().y)) == pad.GetNetname():
                    stubbed.add((fp.GetReference(), pad.GetPosition().x, pad.GetPosition().y))
    nets = {}
    for fp in board.GetFootprints():
        seen_ids = {}
        for pad in fp.Pads():
            pid = pad.GetNumber()
            if pid == '': continue
            k = seen_ids.get(pid, 0); seen_ids[pid] = k + 1
            if k: pid = f'{pid}@{k}'
            n = pad.GetNetname()
            if n in PLANE_NETS and (fp.GetReference(), pad.GetPosition().x, pad.GetPosition().y) in stubbed: continue
            # through-hole pads of the plane nets (QFN exposed-pad thermal vias, connector shells, headers) reach the
            # inner planes by themselves; handing them to the router only creates unroutable targets inside pin rings
            if n in PLANE_NETS and pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            if n in PLANE_NETS and pad.GetShape() == pcbnew.PAD_SHAPE_RECT and ToMM(pad.GetSize().x) > 2.5 and ToMM(pad.GetSize().y) > 2.5: continue   # QFN exposed pad itself
            if n: nets.setdefault(n, []).append(f'{fp.GetReference()}-{pid}')
    boundary = ' '.join(f'{U(x)} {-U(y)}' for x, y in outline_mm)
    out = []
    out.append(f'(pcb {q(os.path.basename(path))}')
    out.append('  (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "7.0.11"))')
    out.append(f'  (resolution um {RES})')
    out.append('  (unit um)')
    out.append('  (structure')
    for i, (_, l) in enumerate(LAYERS): out.append(f'    (layer {l} (type signal) (property (index {i})))')
    out.append(f'    (boundary (path pcb 0 {boundary}))')
    out.append(f'    (via {q(via_name)})')
    out.append(f'    (rule (width {U(track)}) (clearance {U(clearance)}) (clearance {U(pad_clearance)} (type default_smd)) (clearance {U(0.1)} (type smd_smd)) (clearance {U(via_via)} (type via_via)))')
    # copper zones -> Specctra planes: always for inner layers (4-layer stack), for B.Cu only when planes=True
    for z in board.Zones():
        if z.GetIsRuleArea(): continue
        zl = z.GetFirstLayer()
        if planes and zl == pcbnew.B_Cu:
            ol = z.Outline().Outline(0)
            pts = ' '.join(f'{U(ToMM(ol.CPoint(i).x))} {-U(ToMM(ol.CPoint(i).y))}' for i in range(ol.PointCount()))
            out.append(f'    (plane {q(z.GetNetname())} (polygon {lname_of(zl)} 0 {pts}))')
    out.extend(npth_keepouts)
    # rule areas -> Specctra keepouts (all signal layers)
    for z in board.Zones():
        if not z.GetIsRuleArea(): continue
        ol = z.Outline().Outline(0)
        pts = ' '.join(f'{U(ToMM(ol.CPoint(i).x))} {-U(ToMM(ol.CPoint(i).y))}' for i in range(ol.PointCount()))
        kind = 'keepout' if z.GetDoNotAllowTracks() else 'via_keepout'
        out.append(f'    ({kind} {q(z.GetZoneName())} (polygon signal 0 {pts}))')
    out.append('  )')
    out.append('  (placement')
    by_img = {}
    for img, ref, x, y, side, rot in placements: by_img.setdefault(img, []).append(f'(place {ref} {x} {y} {side} {rot:g})')
    for img, pl in by_img.items(): out.append(f'    (component {q(img)} ' + ' '.join(pl) + ')')
    out.append('  )')
    out.append('  (library')
    for im in images.values(): out.append('    ' + im)
    for ps in padstacks.values(): out.append('    ' + ps)
    out.append('  )')
    out.append('  (network')
    for n, pins in nets.items(): out.append(f'    (net {q(n)} (pins ' + ' '.join(pins) + '))')
    sig = [n for n in nets if n not in POWER_NETS]; pwr = [n for n in nets if n in POWER_NETS]
    outer = ' '.join(l for _, l in LAYERS if l in ('F.Cu', 'B.Cu')); alll = ' '.join(l for _, l in LAYERS)
    if pwr:
        sig_layers = alll if os.environ.get('FC_SIG_INNER', '0') == '1' else outer     # FC_SIG_INNER=1: signals may also use the inner layers
        out.append(f'    (class kicad_default ' + ' '.join(q(n) for n in sig) + f' (circuit (use_via {q(via_name)}) (use_layer {sig_layers})) (rule (width {U(track)}) (clearance {U(clearance)})))')
        out.append(f'    (class power ' + ' '.join(q(n) for n in pwr) + f' (circuit (use_via {q(via_name)}) (use_layer {alll})) (rule (width {U(max(track, 0.2))}) (clearance {U(clearance)})))')
    else:
        out.append(f'    (class kicad_default ' + ' '.join(q(n) for n in nets) + f' (circuit (use_via {q(via_name)})) (rule (width {U(track)}) (clearance {U(clearance)})))')
    out.append('  )')
    # existing tracks/vias -> fixed ("protect") wiring so the autorouter keeps them
    wires = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            wires.append(f'    (via {q(via_name)} {U(ToMM(t.GetPosition().x))} {-U(ToMM(t.GetPosition().y))} (net {q(t.GetNetname())}) (type protect))')
        elif t.GetClass() == 'PCB_TRACK':
            if t.GetLayer() not in dict(LAYERS): continue
            lname = lname_of(t.GetLayer())
            s_, e_ = t.GetStart(), t.GetEnd()
            wires.append(f'    (wire (path {lname} {U(ToMM(t.GetWidth()))} {U(ToMM(s_.x))} {-U(ToMM(s_.y))} {U(ToMM(e_.x))} {-U(ToMM(e_.y))}) (net {q(t.GetNetname())}) (type protect))')
    out.append('  (wiring')
    out.extend(wires)
    out.append('  )')
    out.append(')')
    with open(path, 'w') as f: f.write('\n'.join(out) + '\n')
    return len(nets)
