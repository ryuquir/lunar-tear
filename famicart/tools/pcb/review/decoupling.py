#!/usr/bin/env python3
"""Supply delivery to every power pin of a routed board: the copper from each supply pin to its decoupling capacitor,
to the supply plane and to the converter, with its vias, track length and narrowest width (docs/13 "電源", "基板").

What it checks, and why
  A decoupling capacitor helps a pin only as far as the copper between them is short and wide: every mm of 0.12 mm
  track and every via adds inductance to the loop pin -> capacitor -> GND -> exposed pad, and a joint where a track
  merely grazes a pad, a via or another track (a "neck") can etch away or be the whole connection of a pin. docs/13
  puts 100 nF behind every 3.3 V and DVDD pin of the eight RP2350B (68 and 69 share one, 61 + 64 share the 4.7 uF),
  100 nF at every flash, 4.7 uF at the microSD socket, the +3V3 plane on In2, +1V1 and V5_IN as tracks. On the routed
  board the tool reports:
    Q1 every power pin (3.3 V pins, DVDD, VREG pins, flash VCC, microSD VDD, converter, inductor and Schottky pins)
       that no copper of its net touches or that touches it only through contacts narrower than --neck; every contact
       narrower than --neck on a checked net, with its place and its detour (the extra copper between the two items
       without it; none = it is their only joint); every path below that changes without such contacts;
    Q2 per chip and supply pin, the loop pin -> its own capacitor (track mm, mm crossed in a plane, vias, narrowest
       width), the ways of the pin and of the capacitor into the plane of their net, the nearest capacitor, and the
       straight-line floor (pin pad to capacitor pad: no routing can make the loop shorter); the pins over --limit-mm
       of track or --limit-vias vias, those whose floor is over the limit, those within --margin of the limit;
    Q3 the DVDD net (+1V1): per DVDD pin the least-resistance path from the top of the feedback divider (the point the
       converter holds; power_drop.py's start) with length, vias, resistance, narrowest width, the track under --trunk
       next to the pin and elsewhere, the vias and narrow tracks every path needs (cut vias, bridges), and the way to
       the nearest track of at least --trunk; the track length per width;
    Q4 each TLV62569: input loop (VIN pin -> input capacitor, its GND pad -> GND pin, against the straight-line floor),
       EN, switch-node copper (area, track, vias), feedback nets (track length, layers, vias, length from the FB pin to
       each divider pad, distance to the switch-node copper and to the inductor outline, track over the inductor),
       output capacitors (from the inductor; GND pad -> GND pin);
    Q5 flash and microSD +3V3 (from Q2), the connector -> Schottky anode feeds (VBUS, +5V) and Schottky cathode ->
       converter VIN (V5_IN): length, vias, resistance, narrowest width, length under the design's NET_WIDTH;
    GND every decoupling capacitor's GND pad -> first inner GND plane (outer copper and vias), the ring capacitors'
       return to their chip's exposed pad against the straight-line floor, the exposed-pad vias against EP_VIAS, pins
       62 / 65 and flash pin 4.

Method (board mm; KiCad 7.0.11 pcbnew; places also as x' = x - XC, h = H - y from the design's at())
  * The board and its .kicad_pro / .kicad_dru are copied into --out; only the copies are loaded. A child process (this
    file, --child) refills every zone on the copy, saves it and writes KiCad's rule check; the parent reads the filled
    copy and never fills (KiCad 7: GetTracks can fail after Fill + WriteDRCReport in one process).
  * Nets: the design's POWER_NETS, GND, the nets of every checked pin, of the converters (switch node, inductor output,
    feedback divider nodes) and of the Schottky diodes between power nets. One graph per net.
  * Which items touch is KiCad's connectivity (GetConnectedTracks / GetConnectedPads). Where and how wide is this tool's
    own geometry: tracks are stadiums, vias discs, pads KiCad's effective polygon. The gap between two shapes is exact.
    A contact has the full width of the narrower item when a track end's centre lies inside the other shape (the
    track then crosses its outline with its whole width), when centre lines cross, or a via lies inside a pad; else
    its neck is the largest extent of the overlap (Sutherland-Hodgman clipping, 16-segment half circles, 32-segment
    discs), at most the narrower width. Each contact under --neck gets its detour (shortest path between its two
    items without it). A zone piece is entered by a via whose ring overlaps the fill (contact: the arc of a circle
    5 um outside the ring that lies in the fill, 36 points; a piece wholly inside a via ring is that via's copper),
    a pad whose centre is in the fill or whose outline touches it (contact: the share of 32 points 10 um outside the
    outline in the fill times its length) or a track end in the fill (contact: the track width).
  * Copper length = track centre lines + in-pad / in-via offsets (centre to contact point; 0 inside an exposed pad)
    + via barrels between the layers used (copper centres from the board's stack-up) + plane crossings (straight line
    between entry and exit, a lower bound exact for a solid plane). "track mm" = centre lines + offsets (the measure
    of the loop limit); "plane mm" = crossings of inner planes; "outer" (GND) = track mm + crossings of F / B pours.
    Shortest paths: Dijkstra on that length, ties to fewer vias; a contact under --neck costs 1 um more, so that
    equal paths go through full contacts. Widths along a path: tracks, contact necks, zone contacts (not vias).
  * Resistance (Q3, Q5): rho L / (w t), t = 35 um on F / B and 17.5 um inside, 1.2 mOhm per via layer change
    (power_drop.py's model); joins as copper of the wider item; zones are not crossed in resistance searches.
  * Capacitors: a 2-pad C* with one pad on the net and the other on GND. The pin's own capacitor: for the RP2350B the
    design's RING / RING_POST entry found by position (pins from the comments of RING), for a flash or socket the
    nearest capacitor of its net that is no chip's, for a converter the nearest input capacitor and the output
    capacitors of at least 1 uF within 10 mm of the inductor's output pad. Cut vias / bridges: removed one at a time,
    the pin no longer reaches the divider.

Self-check (exit status 2 and "FAILED" in the report when one does not hold)
  The stored fill equals the fresh fill (outline count and area per zone and layer); KiCad's rule check has no
  unconnected pair on a checked net that the tool sees joined, and every checked net it finds whole is one component
  in the tool; every pair KiCad calls touching has an exact gap of at most 1 um (else the shapes are wrong); every via
  counted inside a zone has a contact arc outside its ring; an independent endpoint model (tracks joined only at
  coinciding ends, pads and vias by their outline) finds no shorter pin-to-capacitor track path than the tool and
  joins no pair the tool keeps apart; every chip pin has the net the design gives it and every ring capacitor sits
  where the design puts it. Paths that change without contacts under --neck are findings, not failures.

Assumptions
  * RP2350B power pins (datasheet pin table, Figure 3; design DVDD / V33): IOVDD 5 15 24 29 41 50 60 76, DVDD 10 32
    51, ADC_AVDD 59, USB_OTP_VDD 68, QSPI_IOVDD 69, VREG_AVDD 61, VREG_VIN 64, VREG_PGND 62 and VREG_FB 65 (GND),
    VREG_LX 63 (open), exposed pad 81 (the only GND terminal). W25Q128JVSIQ: VCC 8, GND 4. microSD: VDD pin 4.
    TLV62569DBV (TI SLVSDG1): EN 1, GND 2, SW 3, VIN 4, FB 5. Schottky: pad 1 cathode, pad 2 anode (KiCad Device:D).
  * --limit-mm 3.0 and --limit-vias 2 (the review's loop limits), --margin 0.3, --neck 0.12 (the board's track rule,
    docs/13; 0.09 mm, JLCPCB's multilayer minimum, is shown as a second mark) and --trunk 0.3 mm are review
    thresholds, not a standard.
  * Copper thickness (outer 1 oz, inner 0.5 oz, JLC06121H-3313, docs/13) and the via resistance are power_drop.py's.

Limits
  * Lengths, widths, via counts and DC resistance only: no inductance, impedance or current density. Planes and pours
    are crossed in a straight line; a track that runs through a zone without ending in it does not enter it there.
  * A neck is a geometric extent, not a current-crowding model; polygon approximation about 1 um.
  * The capacitor of a pin is the design's; if parts moved without the design changing, the position check fails.
  * Arc tracks and blind / buried vias are not handled (the tool stops on an arc of a checked net).

Usage (any working directory; the design module is looked up in the folder above this one)
    python3 review/decoupling.py BOARD.kicad_pcb [--design design_revh] [--out DIR] [--stored-fill] [--no-drc]
            [--limit-mm 3.0] [--limit-vias 2] [--margin 0.3] [--neck 0.12] [--trunk 0.3]
  --design (or FC_DESIGN) names the design module: POWER_NETS and at(); for RP2350B boards also CHIP_XY, RING,
  RING_POST, PARTS, NETS; EP_VIAS and NET_WIDTH where present.
  --out takes every file the tool writes (default: a fresh temporary folder, named in the report): decoupling.txt
  (the report, also on stdout), decoupling_pins.csv (one row per supply pin), decoupling.json (every row with its
  paths), drc.txt (KiCad's rule check of the copy), board/ (the copies and the fill record).
  Exit status: 0; 2 when a self-check failed; 1 on usage errors.

A healthy result
  Self-check all ok. No open or weak power pin, no contact under --neck that is a sole joint or used by a reported
  path. Every 3.3 V pin and its capacitor each one short track and one via from the plane, so that the loop is at
  most --limit-mm of track and --limit-vias vias (or within --margin of its floor where the floor is over the limit).
  Every DVDD pin on a track of at least --trunk within a few mm, no narrow bridge away from the pins, a resistance
  that keeps power_drop.py's drop inside the docs/13 budget, and DVDD loops as short as the 3.3 V ones. Converter
  input loops of a few mm with no via, the FB net a few mm long and away from the switch node and the inductor,
  output capacitor GND within a few mm of the GND pin. Every capacitor GND pad within a short way of a via into an
  inner GND plane. A board without RP2350B or converters (rev G) checks its flash and microSD supply only.
"""
import os, sys
sys.dont_write_bytecode = True                     # before any import from the tools folder: nothing is written there
import re, csv, json, math, time, heapq, shutil, hashlib, argparse, tempfile, importlib, subprocess
from collections import defaultdict, Counter
import numpy as np

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # tools/pcb: the design modules
CU_NAMES = {0: 'F.Cu', 1: 'In1.Cu', 2: 'In2.Cu', 3: 'In3.Cu', 4: 'In4.Cu', 31: 'B.Cu'}
CU_ORDER = [0, 1, 2, 3, 4, 31]                     # top to bottom
OUTER = (0, 31)
RHO, T_OUT, T_IN, R_VIA = 1.72e-8, 35e-6, 17.5e-6, 1.2e-3   # ohm m; m; m; ohm per via layer change (power_drop.py)
RP_SUPPLY = [(5, 'IOVDD'), (15, 'IOVDD'), (24, 'IOVDD'), (29, 'IOVDD'), (41, 'IOVDD'), (50, 'IOVDD'), (60, 'IOVDD'),
             (76, 'IOVDD'), (10, 'DVDD'), (32, 'DVDD'), (51, 'DVDD'), (59, 'ADC_AVDD'), (68, 'USB_OTP_VDD'),
             (69, 'QSPI_IOVDD'), (61, 'VREG_AVDD'), (64, 'VREG_VIN')]
RP_GND = [(62, 'VREG_PGND'), (65, 'VREG_FB'), (81, 'EP')]
RP_OPEN = [(63, 'VREG_LX')]
RING_PINS = [[5], [10], [15], [41], [50], [51], [59], [60], [76], [68, 69], [61, 64], [24], [29], [32]]   # RING comments
FLASH_VCC, FLASH_GND, SD_VDD = '8', '4', '4'
CONV = {'EN': '1', 'GND': '2', 'SW': '3', 'VIN': '4', 'FB': '5'}
GAP_OK = 0.001                                     # mm: KiCad contacts must have an exact gap of at most this


def median(v):
    """The median (mean of the two middle values for an even count); 0 for no values."""
    v = sorted(v); n = len(v)
    return 0.0 if not n else v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


# ============================================================================================ child: fill + rule check

def child(src, dst, drc, js, fill):
    import pcbnew
    b = pcbnew.LoadBoard(src)
    def areas():
        out = []
        for i, z in enumerate(b.Zones()):
            if z.GetIsRuleArea(): continue
            for l in CU_ORDER:
                if z.IsOnLayer(l):
                    f = z.GetFilledPolysList(l)
                    out.append([i, z.GetNetname(), CU_NAMES[l], f.OutlineCount(), round(f.Area() / 1e12, 4)])
        return out
    rec = {'stored': areas()}
    if fill:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        rec['fresh'] = areas()
    b.Save(dst)
    if drc: pcbnew.WriteDRCReport(b, drc, pcbnew.EDA_UNITS_MILLIMETRES, True)
    with open(js, 'w') as f: json.dump(rec, f)


def md5_of(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()


def stage(src, folder):
    """Copy the board and its project files into folder; returns (copy, [copied extensions])."""
    os.makedirs(folder, exist_ok=True)
    stem = os.path.join(folder, 'board'); dst = stem + '.kicad_pcb'
    shutil.copy2(src, dst); copied = []
    for ext in ('.kicad_pro', '.kicad_dru'):
        p = os.path.splitext(src)[0] + ext
        if os.path.exists(p): shutil.copy2(p, stem + ext); copied.append(ext)
    if md5_of(dst) != md5_of(src): raise SystemExit('copy %s differs from %s' % (dst, src))
    return dst, copied


# ============================================================================================ geometry
def seg_closest(p0, p1, q0, q1):
    """Closest points of segments p0p1 and q0q1: (s, t, distance), s / t in [0, 1] (Ericson, RTCD 5.1.9)."""
    d1 = (p1[0] - p0[0], p1[1] - p0[1]); d2 = (q1[0] - q0[0], q1[1] - q0[1]); r = (p0[0] - q0[0], p0[1] - q0[1])
    a = d1[0] * d1[0] + d1[1] * d1[1]; e = d2[0] * d2[0] + d2[1] * d2[1]; f = d2[0] * r[0] + d2[1] * r[1]
    eps = 1e-12
    if a <= eps and e <= eps: s = t = 0.0
    elif a <= eps: s = 0.0; t = min(1.0, max(0.0, f / e))
    else:
        c = d1[0] * r[0] + d1[1] * r[1]
        if e <= eps: t = 0.0; s = min(1.0, max(0.0, -c / a))
        else:
            b = d1[0] * d2[0] + d1[1] * d2[1]; den = a * e - b * b
            s = min(1.0, max(0.0, (b * f - c * e) / den)) if den > eps else 0.0
            t = (b * s + f) / e
            if t < 0.0: t = 0.0; s = min(1.0, max(0.0, -c / a))
            elif t > 1.0: t = 1.0; s = min(1.0, max(0.0, (b - c) / a))
    cp = (p0[0] + d1[0] * s, p0[1] + d1[1] * s); cq = (q0[0] + d2[0] * t, q0[1] + d2[1] * t)
    return s, t, math.hypot(cp[0] - cq[0], cp[1] - cq[1])


def point_param(p0, p1, q):
    """Parameter (0..1) of the point of segment p0p1 nearest to q, and the distance."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L2 = dx * dx + dy * dy
    t = 0.0 if L2 <= 1e-12 else min(1.0, max(0.0, ((q[0] - p0[0]) * dx + (q[1] - p0[1]) * dy) / L2))
    return t, math.hypot(p0[0] + dx * t - q[0], p0[1] + dy * t - q[1])


def in_poly(x, y, poly):
    """Even-odd point-in-polygon test."""
    inside = False; n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0): inside = not inside
    return inside


def edges(P): return zip(P, P[1:] + P[:1])


def signed_area(P): return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in edges(P))


def ccw(P): return P if signed_area(P) > 0 else P[::-1]


def boundary_dist(P, q):
    """Distance from q to the outline of polygon P."""
    return min(point_param(a, b, q)[1] for a, b in edges(P))


def seg_poly_gap(p0, p1, P):
    """0 if segment p0p1 touches or enters polygon P, else the distance between them."""
    if in_poly(p0[0], p0[1], P) or in_poly(p1[0], p1[1], P): return 0.0
    return min(seg_closest(p0, p1, a, b)[2] for a, b in edges(P))


def poly_poly_gap(P, Q):
    if in_poly(P[0][0], P[0][1], Q) or in_poly(Q[0][0], Q[0][1], P): return 0.0
    return min(seg_poly_gap(a, b, Q) for a, b in edges(P))


def circle_poly(x, y, r, n=32): return [(x + r * math.cos(2 * math.pi * k / n), y + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def stadium_poly(x0, y0, x1, y1, w, n=16):
    r = w / 2; a = math.atan2(y1 - y0, x1 - x0) if (x1, y1) != (x0, y0) else 0.0
    pts = [(x1 + r * math.cos(a - math.pi / 2 + math.pi * k / n), y1 + r * math.sin(a - math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]
    pts += [(x0 + r * math.cos(a + math.pi / 2 + math.pi * k / n), y0 + r * math.sin(a + math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]
    return pts


def hull(P):
    """Convex hull (monotone chain), counter-clockwise."""
    P = sorted(set(P))
    if len(P) < 3: return P
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0: h.pop()
            h.append(p)
        return h
    lo, hi = half(P), half(P[::-1])
    return lo[:-1] + hi[:-1]


def clip(subject, clipper):
    """Sutherland-Hodgman: subject polygon clipped by the convex counter-clockwise polygon clipper."""
    out = list(subject)
    for (ax, ay), (bx, by) in edges(clipper):
        if not out: break
        inp, out = out, []
        def side(p): return (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) >= 0
        def cut(p, q):
            d1 = (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax); d2 = (bx - ax) * (q[1] - ay) - (by - ay) * (q[0] - ax)
            t = d1 / (d1 - d2) if d1 != d2 else 0.0
            return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        s = inp[-1]; s_in = side(s)
        for p in inp:
            p_in = side(p)
            if p_in:
                if not s_in: out.append(cut(s, p))
                out.append(p)
            elif s_in: out.append(cut(s, p))
            s, s_in = p, p_in
    return out


def diameter(P):
    if len(P) < 2: return 0.0
    A = np.asarray(P); d = A[:, None, :] - A[None, :, :]
    return float(np.sqrt((d * d).sum(-1).max()))


def stackup_z(path):
    """{copper layer name: z of its centre (mm, from the top of F.Cu)} from the board's (stackup)."""
    s = open(path).read()
    i = s.find('(stackup')
    if i < 0: raise SystemExit('no (stackup) in ' + path)
    blk = s[i:s.find('(copper_finish', i)]
    rows = re.findall(r'\(layer "([^"]+)" \(type "([^"]+)"\)(?: \(thickness ([0-9.]+)\))?', blk)
    z = 0.0; zc = {}; started = False
    for name, typ, th in rows:
        if name.endswith('.Cu'): started = True
        if not started or not th: continue
        if name == 'B.Mask': break
        t = float(th)
        if name.endswith('.Cu'): zc[name] = z + t / 2
        z += t
    return zc


# ============================================================================================ extraction (pcbnew)
def extract(path, pick_nets):
    """Plain-Python copy of the board: footprints, then pads / tracks / vias / zone pieces of the nets pick_nets(fps)
    returns, and KiCad's adjacency between them. The zone fills stay pcbnew objects (fills, by zone record id)."""
    import pcbnew
    mm = lambda v: v / 1e6
    b = pcbnew.LoadBoard(path)
    b.BuildConnectivity(); conn = b.GetConnectivity()
    data = {'pads': [], 'tracks': [], 'vias': [], 'zones': [], 'adj': [], 'fps': {}, 'other_vias': [], 'counts': {}}
    enabled = [l for l in CU_ORDER if b.IsLayerEnabled(l)]       # a through-hole pad also names inner layers a 2-layer board lacks
    def cu(item): return [l for l in enabled if item.IsOnLayer(l)]
    for fp in b.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        data['fps'][fp.GetReference()] = dict(value=fp.GetValue(), fpid=fp.GetFPIDAsString(), x=mm(fp.GetPosition().x), y=mm(fp.GetPosition().y),
                                              rot=fp.GetOrientationDegrees(), side='F' if fp.GetLayer() == pcbnew.F_Cu else 'B',
                                              pads={p.GetNumber(): p.GetNetname() for p in fp.Pads()},
                                              bbox=(mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())))
    nets = pick_nets(data['fps'])
    uid = {}; objs = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() not in nets: continue
            ps = p.GetEffectivePolygon()
            pts = [(mm(ps.COutline(o).CPoint(k).x), mm(ps.COutline(o).CPoint(k).y)) for o in range(ps.OutlineCount()) for k in range(ps.COutline(o).PointCount())]
            poly = ccw(pts) if ps.OutlineCount() == 1 else hull(pts)
            i = len(data['pads'])
            data['pads'].append(dict(id=i, ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(), layers=cu(p), x=mm(p.GetPosition().x),
                                     y=mm(p.GetPosition().y), sx=mm(p.GetSize().x), sy=mm(p.GetSize().y), poly=poly, area=abs(signed_area(poly)),
                                     width=min(mm(p.GetSize().x), mm(p.GetSize().y)), smd=p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD))
            uid[p.m_Uuid.AsString()] = ('P', i); objs.append((('P', i), p))
    cnt = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
    for t in b.GetTracks():
        net = t.GetNetname()
        if t.Type() == pcbnew.PCB_VIA_T:
            if net not in nets:
                data['other_vias'].append(dict(net=net, x=mm(t.GetPosition().x), y=mm(t.GetPosition().y), dia=mm(t.GetWidth())))
                continue
            i = len(data['vias'])
            data['vias'].append(dict(id=i, net=net, x=mm(t.GetPosition().x), y=mm(t.GetPosition().y), dia=mm(t.GetWidth()),
                                     drill=mm(t.GetDrillValue()), layers=cu(t), locked=bool(t.IsLocked())))
            uid[t.m_Uuid.AsString()] = ('V', i); objs.append((('V', i), t))
        elif net in nets:
            if t.Type() != pcbnew.PCB_TRACE_T: raise SystemExit('arc track on %s: not handled' % net)
            i = len(data['tracks'])
            r = dict(id=i, net=net, layer=t.GetLayer(), x0=mm(t.GetStart().x), y0=mm(t.GetStart().y), x1=mm(t.GetEnd().x), y1=mm(t.GetEnd().y), w=mm(t.GetWidth()))
            data['tracks'].append(r)
            c = cnt[net][CU_NAMES[r['layer']]]; c[0] += 1; c[1] += math.hypot(r['x1'] - r['x0'], r['y1'] - r['y0'])
            uid[t.m_Uuid.AsString()] = ('T', i); objs.append((('T', i), t))
    rank = {CU_NAMES[l]: k for k, l in enumerate(CU_ORDER)}
    data['counts'] = {n: {l: (c[0], round(c[1], 1)) for l, c in sorted(v.items(), key=lambda kv: rank[kv[0]])} for n, v in cnt.items()}
    seen = set()
    for key, obj in objs:                           # KiCad's adjacency, kept between items of the picked nets only
        for nb in list(conn.GetConnectedTracks(obj)) + list(conn.GetConnectedPads(obj)):
            k2 = uid.get(nb.m_Uuid.AsString())
            if k2 is None or k2 == key: continue
            e = tuple(sorted([key, k2]))
            if e not in seen: seen.add(e); data['adj'].append(e)
    fills = {}
    for zi, z in enumerate(b.Zones()):
        if z.GetIsRuleArea() or z.GetNetname() not in nets: continue
        for layer in enabled:
            if not z.IsOnLayer(layer): continue
            fill = z.GetFilledPolysList(layer); zo = z.Outline().COutline(0)
            zr = dict(id=len(data['zones']), zone=zi, net=z.GetNetname(), layer=layer, inner=layer not in OUTER, pieces=[],
                      outline=[(mm(zo.CPoint(k).x), mm(zo.CPoint(k).y)) for k in range(zo.PointCount())])
            for oi in range(fill.OutlineCount()):
                ol = fill.COutline(oi); bb = ol.BBox()
                single = pcbnew.SHAPE_POLY_SET(); single.AddOutline(ol)
                for h in range(fill.HoleCount(oi)): single.AddHole(fill.CHole(oi, h))
                zr['pieces'].append(dict(idx=oi, area=single.Area() / 1e12, bbox=(mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()))))
            fills[zr['id']] = fill
            data['zones'].append(zr)
    data['unconnected_kicad'] = conn.GetUnconnectedCount(True)
    return data, fills, b


class Fill:
    """Point tests against one zone record's filled pieces (pcbnew SHAPE_POLY_SET.Contains, exact for the fill)."""
    def __init__(self, fill, zr):
        import pcbnew
        self.f, self.zr, self.V = fill, zr, pcbnew.VECTOR2I
    def inside(self, oi, x, y, tol=0.0):
        x0, y0, x1, y1 = self.zr['pieces'][oi]['bbox']
        if x < x0 - tol or x > x1 + tol or y < y0 - tol or y > y1 + tol: return False
        return self.f.Contains(self.V(int(round(x * 1e6)), int(round(y * 1e6))), oi, int(round(tol * 1e6)), False)


def zone_members(data, fills):
    """For every zone piece: the vias, pads and track ends of its net that enter it, each with its contact width."""
    for zr in data['zones']:
        F = Fill(fills[zr['id']], zr); net, layer = zr['net'], zr['layer']
        vias = [v for v in data['vias'] if v['net'] == net and layer in v['layers']]
        pads = [p for p in data['pads'] if p['net'] == net and layer in p['layers']]
        trks = [t for t in data['tracks'] if t['net'] == net and t['layer'] == layer]
        for pc in zr['pieces']:
            oi = pc['idx']; pc['vias'] = []; pc['pads'] = []; pc['track_ends'] = []; pc['inside_via'] = None
            x0, y0, x1, y1 = pc['bbox']
            for v in vias:
                R = v['dia'] / 2
                if not F.inside(oi, v['x'], v['y'], R): continue
                ring = sum(F.inside(oi, v['x'] + (R + 0.005) * math.cos(k * math.pi / 18), v['y'] + (R + 0.005) * math.sin(k * math.pi / 18)) for k in range(36)) / 36.0
                if ring == 0 and all(math.hypot(cx_ - v['x'], cy_ - v['y']) <= R + 0.01 for cx_ in (x0, x1) for cy_ in (y0, y1)):
                    pc['inside_via'] = v['id']; continue        # the piece lies within this via's ring: the via's own copper
                pc['vias'].append((v['id'], round(ring, 3), F.inside(oi, v['x'], v['y'])))
            for p in pads:
                P = p['poly']; per = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in edges(P)]; L = sum(per)
                pts = []
                for k in range(32):                 # 32 points evenly along the outline, 10 um outside it
                    s = (k + 0.5) * L / 32; j = 0
                    while s > per[j]: s -= per[j]; j += 1
                    (ax, ay), (bx, by) = P[j], P[(j + 1) % len(P)]; f = s / per[j]
                    nx, ny = (by - ay) / per[j], -(bx - ax) / per[j]     # outward normal of a counter-clockwise outline
                    pts.append((ax + (bx - ax) * f + 0.01 * nx, ay + (by - ay) * f + 0.01 * ny))
                touch = sum(F.inside(oi, x, y) for x, y in pts) / 32.0
                if touch > 0 or F.inside(oi, p['x'], p['y']): pc['pads'].append((p['id'], round(touch * L, 3)))
            for t in trks:
                for end, (x, y) in ((0, (t['x0'], t['y0'])), (1, (t['x1'], t['y1']))):
                    if F.inside(oi, x, y): pc['track_ends'].append((t['id'], end))


# ============================================================================================ contacts (necks)
def shape_of(data, key):
    k, i = key
    if k == 'T':
        t = data['tracks'][i]; return dict(kind='T', p0=(t['x0'], t['y0']), p1=(t['x1'], t['y1']), w=t['w'], width=t['w'])
    if k == 'V':
        v = data['vias'][i]; return dict(kind='V', c=(v['x'], v['y']), r=v['dia'] / 2, width=v['dia'])
    p = data['pads'][i]; return dict(kind='P', c=(p['x'], p['y']), poly=p['poly'], width=p['width'])


def poly_of(s):
    if s['kind'] == 'T': return ccw(stadium_poly(s['p0'][0], s['p0'][1], s['p1'][0], s['p1'][1], s['w']))
    if s['kind'] == 'V': return circle_poly(s['c'][0], s['c'][1], s['r'])
    return s['poly']


def gap_and_full(a, b):
    """Exact gap between the two shapes, and whether the contact has the full width of the narrower item: a track end
    whose centre lies inside the other shape (the track then crosses its outline with its whole width), crossing
    centre lines, a via disc inside a pad."""
    ka, kb = a['kind'], b['kind']
    if ka > kb: a, b, ka, kb = b, a, kb, ka               # order P < T < V
    if ka == 'T' and kb == 'T':
        s, t, d = seg_closest(a['p0'], a['p1'], b['p0'], b['p1'])
        full = d < 1e-9 or any(point_param(y['p0'], y['p1'], e)[1] <= y['w'] / 2 + 1e-9 for x, y in ((a, b), (b, a)) for e in (x['p0'], x['p1']))
        return d - (a['w'] + b['w']) / 2, full
    if ka == 'T' and kb == 'V':
        d = point_param(a['p0'], a['p1'], b['c'])[1]
        return d - a['w'] / 2 - b['r'], min(math.hypot(e[0] - b['c'][0], e[1] - b['c'][1]) for e in (a['p0'], a['p1'])) <= b['r'] + 1e-9
    if ka == 'P' and kb == 'T':
        g = seg_poly_gap(b['p0'], b['p1'], a['poly']) - b['w'] / 2
        full = any(in_poly(e[0], e[1], a['poly']) for e in (b['p0'], b['p1']))
        return g, full
    if ka == 'P' and kb == 'V':
        inside = in_poly(b['c'][0], b['c'][1], a['poly'])
        bd = boundary_dist(a['poly'], b['c'])
        return (-bd if inside else bd) - b['r'], inside and bd >= b['r'] - 1e-9
    if ka == 'P' and kb == 'P':
        return poly_poly_gap(a['poly'], b['poly']), False
    d = math.hypot(a['c'][0] - b['c'][0], a['c'][1] - b['c'][1])          # V-V
    return d - a['r'] - b['r'], d + min(a['r'], b['r']) <= max(a['r'], b['r'])


def measure_contacts(data):
    """Every KiCad adjacency pair with its exact gap, its neck and a place (contact centre)."""
    out = []
    for ka_, kb_ in data['adj']:
        a, b = shape_of(data, ka_), shape_of(data, kb_)
        net = (data['tracks'] if ka_[0] == 'T' else data['vias'] if ka_[0] == 'V' else data['pads'])[ka_[1]]['net']
        if a['kind'] == 'T' and b['kind'] == 'T' and data['tracks'][ka_[1]]['layer'] != data['tracks'][kb_[1]]['layer']: continue
        gap, full = gap_and_full(a, b)
        cap = min(a['width'], b['width'])
        PA, PB = poly_of(a), poly_of(b)
        if full:
            neck = cap; inter = None
        elif gap > 0:
            neck = 0.0; inter = None
        else:
            if b['kind'] != 'P': subject, convex = PA, PB          # tracks and vias are convex; a pad may not be
            elif a['kind'] != 'P': subject, convex = PB, PA
            else: subject, convex = PA, hull(PB)
            inter = clip(subject, ccw(convex))
            neck = min(cap, diameter(inter))
        if inter: cx, cy = sum(p[0] for p in inter) / len(inter), sum(p[1] for p in inter) / len(inter)
        else:
            s = a if a['kind'] == 'T' else b
            if s['kind'] == 'T':
                o = b if s is a else a
                q = o['c'] if 'c' in o else min((s['p0'], s['p1']), key=lambda e: seg_closest(e, e, o['p0'], o['p1'])[2])
                tt, _ = point_param(s['p0'], s['p1'], q); cx, cy = s['p0'][0] + (s['p1'][0] - s['p0'][0]) * tt, s['p0'][1] + (s['p1'][1] - s['p0'][1]) * tt
            else: cx, cy = (a['c'][0] + b['c'][0]) / 2, (a['c'][1] + b['c'][1]) / 2
        out.append(dict(a=ka_, b=kb_, net=net, gap=round(gap, 5), neck=round(neck, 4), full=bool(full), x=round(cx, 4), y=round(cy, 4)))
    return out


# ============================================================================================ graph
class Graph:
    def __init__(self, net):
        self.net = net; self.key2id = {}; self.keys = []; self.pos = []; self.lay = []; self.adj = []
        self.pieces = []; self.member_of = defaultdict(list); self.join_nodes = {}; self.prefer = 0.0

    def node(self, key, xy, layer):
        i = self.key2id.get(key)
        if i is None:
            i = len(self.keys); self.key2id[key] = i; self.keys.append(key); self.pos.append(xy); self.lay.append(layer); self.adj.append([])
        return i

    def edge(self, a, b, L, vias, kind, info, width, R):
        if a == b: return
        e = (L, vias, kind, info, width, R)
        self.adj[a].append((b,) + e); self.adj[b].append((a,) + e)

    def pad_node(self, pid):
        for l in CU_ORDER:
            n = self.key2id.get(('P', pid, l))
            if n is not None: return n
        return None


def r_track(L, w, layer): return RHO * (L * 1e-3) / (w * 1e-3 * (T_OUT if layer in OUTER else T_IN))


def build_graph(data, net, zc, contacts, labels, ep_pads):
    """Nodes ('P', pad, layer), ('T', track, t), ('V', via, layer). Edges 'trk' (along a track), 'join' (offset between
    touching items, width = the contact's neck), 'via' / 'tht' (barrel between two layers: 1 via). Zone pieces are
    crossed lazily in search() ('plane': straight line between two members, width = the smaller member contact)."""
    g = Graph(net)
    pads = {p['id']: p for p in data['pads'] if p['net'] == net}
    trks = {t['id']: t for t in data['tracks'] if t['net'] == net}
    vias = {v['id']: v for v in data['vias'] if v['net'] == net}
    params = defaultdict(set)
    for tid in trks: params[tid].update((0.0, 1.0))
    joins = []
    def get(k, i): return {'P': pads, 'T': trks, 'V': vias}[k].get(i)
    def wide(k, o): return o['w'] if k == 'T' else o['dia'] if k == 'V' else o['width']
    for ci, c in enumerate(contacts):
        if c['net'] != net: continue
        (ka, ia), (kb, ib) = c['a'], c['b']
        a, bb = get(ka, ia), get(kb, ib)
        ep = (ka == 'P' and ia in ep_pads) or (kb == 'P' and ib in ep_pads)
        if ka == 'T' and kb == 'T':
            s, t, d = seg_closest((a['x0'], a['y0']), (a['x1'], a['y1']), (bb['x0'], bb['y0']), (bb['x1'], bb['y1']))
            s, t = round(s, 9), round(t, 9); params[ia].add(s); params[ib].add(t)
            joins.append((('T', ia, s), ('T', ib, t), d, c['neck'], min(a['w'], bb['w']), a['layer'], ci))
        elif 'T' in (ka, kb):
            (kt, it), (ko, io) = ((ka, ia), (kb, ib)) if ka == 'T' else ((kb, ib), (ka, ia))
            t = trks[it]; o = get(ko, io)
            s, d = point_param((t['x0'], t['y0']), (t['x1'], t['y1']), (o['x'], o['y']))
            s = round(s, 9); params[it].add(s)
            joins.append((('T', it, s), (ko, io, t['layer']), 0.0 if ep else d, c['neck'], wide(ko, o), t['layer'], ci))
        else:
            common = [l for l in a['layers'] if l in bb['layers']]
            if not common: continue
            joins.append(((ka, ia, common[0]), (kb, ib, common[0]), 0.0 if ep else math.hypot(a['x'] - bb['x'], a['y'] - bb['y']), c['neck'],
                          max(wide(ka, a), wide(kb, bb)), common[0], ci))
    for tid, t in trks.items():
        L = math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']); prev = None
        for s in sorted(params[tid]):
            n = g.node(('T', tid, s), (t['x0'] + (t['x1'] - t['x0']) * s, t['y0'] + (t['y1'] - t['y0']) * s), t['layer'])
            if prev is not None: g.edge(prev[0], n, (s - prev[1]) * L, 0, 'trk', tid, t['w'], r_track((s - prev[1]) * L, t['w'], t['layer']))
            prev = (n, s)
    full_barrel = abs(zc['F.Cu'] - zc['B.Cu'])
    for kind, items in (('via', vias), ('tht', pads)):
        for i, o in items.items():
            ls = o['layers']; ns = {l: g.node(('V' if kind == 'via' else 'P', i, l), (o['x'], o['y']), l) for l in ls}
            for x in range(len(ls)):
                for y in range(x + 1, len(ls)):
                    Lb = abs(zc[CU_NAMES[ls[x]]] - zc[CU_NAMES[ls[y]]])
                    g.edge(ns[ls[x]], ns[ls[y]], Lb, 1, kind, i, math.inf, R_VIA * Lb / full_barrel if kind == 'tht' else R_VIA)
    def spec_node(sp):
        if sp[0] == 'T': return g.key2id[sp]
        k, i, l = sp; o = pads[i] if k == 'P' else vias[i]
        return g.key2id[(k, i, l if l in o['layers'] else o['layers'][0])]
    for sa, sb, d, neck, wr, layer, ci in joins:
        u, w = spec_node(sa), spec_node(sb); g.join_nodes[ci] = (u, w)
        g.edge(u, w, d, 0, 'join', ci, neck, r_track(d, wr, layer) if d > 0 else 0.0)
    for zr in data['zones']:
        if zr['net'] != net: continue
        for pc in zr['pieces']:
            L = zr['layer']; m = []
            m += [(g.key2id[('V', vi, L)], min(ring * math.pi * vias[vi]['dia'], vias[vi]['dia'])) for vi, ring, _ in pc['vias'] if ('V', vi, L) in g.key2id]
            m += [(g.key2id[('P', pi, L)], min(touch, pads[pi]['width']) if touch > 0 else pads[pi]['width']) for pi, touch in pc['pads'] if ('P', pi, L) in g.key2id]
            m += [(g.key2id[('T', ti, float(e))], trks[ti]['w']) for ti, e in pc['track_ends'] if ('T', ti, float(e)) in g.key2id]
            pk = (zr['id'], pc['idx'])
            nodes = np.array([n for n, _ in m], dtype=np.int64); necks = np.array([w for _, w in m], dtype=float)
            xy = np.array([g.pos[n] for n in nodes], dtype=float).reshape(-1, 2)
            label = labels[zr['id']] + ('' if len(zr['pieces']) == 1 else ' #%d' % pc['idx'])
            pi = len(g.pieces); g.pieces.append(dict(key=pk, zone=zr, piece=pc, nodes=nodes, necks=necks, xy=xy, label=label, inner=zr['inner']))
            for j, n in enumerate(nodes): g.member_of[int(n)].append((pi, j))
    return g


def search(g, sources, cost='len', planes=True, targets=None, min_neck=0.0, skip_joins=()):
    """Dijkstra from the node(s) sources. cost 'len' (copper mm) or 'res' (ohm); ties within 1e-9 go to fewer vias.
    planes: crossing a zone piece is allowed (straight line, lazily from each settled member; only with cost 'len').
    targets: stop once all are settled. Contacts narrower than min_neck
    are not used, nor the contacts skip_joins; a contact narrower than g.prefer costs 1 um (1 nOhm) more, so that equal
    paths go through full contacts. Returns (dist, vias, prev, settled order); dist includes those small extras."""
    N = len(g.keys); dist = np.full(N, np.inf); nv = np.zeros(N, dtype=np.int64); prev = [None] * N; done = np.zeros(N, dtype=bool)
    h = []
    for s in ([sources] if isinstance(sources, (int, np.integer)) else sources):
        s = int(s); dist[s] = 0.0; heapq.heappush(h, (0.0, 0, s))
    left = set(targets) if targets else None; order = []
    while h:
        d, v, u = heapq.heappop(h)
        if done[u]: continue
        done[u] = True; order.append(u)
        if left is not None:
            left.discard(u)
            if not left: break
        for (w, L, vc, kind, info, width, R) in g.adj[u]:
            if done[w] or (kind == 'join' and (width < min_neck or info in skip_joins)): continue
            nd = d + (L if cost == 'len' else R) + ((1e-3 if cost == 'len' else 1e-9) if kind == 'join' and width < g.prefer else 0.0); nvv = v + vc
            if nd < dist[w] - 1e-9 or (abs(nd - dist[w]) <= 1e-9 and nvv < nv[w]):
                dist[w] = nd; nv[w] = nvv; prev[w] = (u, L, vc, kind, info, width, R); heapq.heappush(h, (nd, nvv, w))
        if planes and cost == 'len':
            ux, uy = g.pos[u]
            for pi, j in g.member_of.get(u, ()):
                P = g.pieces[pi]
                if P['necks'][j] < min_neck: continue
                dd = d + np.hypot(P['xy'][:, 0] - ux, P['xy'][:, 1] - uy)
                cur = dist[P['nodes']]
                ok = ((dd < cur - 1e-9) | ((np.abs(dd - cur) <= 1e-9) & (v < nv[P['nodes']]))) & ~done[P['nodes']] & (P['necks'] >= min_neck)
                for k in np.nonzero(ok)[0]:
                    w = int(P['nodes'][k])
                    dist[w] = dd[k]; nv[w] = v
                    prev[w] = (u, float(dd[k] - d), 0, 'plane', pi, float(min(P['necks'][j], P['necks'][k])), 0.0); heapq.heappush(h, (float(dd[k]), v, w))
    return dist, nv, prev, order


def path_of(prev, dst):
    """Edges from the search source to dst: (from, to, L, vias, kind, info, width, R)."""
    out = []; u = dst
    while prev[u] is not None:
        p = prev[u]; out.append((p[0], u) + tuple(p[1:])); u = p[0]
    return out[::-1]


def reversed_path(path): return [(b, a) + tuple(e[2:]) for e in path[::-1] for a, b in [(e[0], e[1])]]


def reachable(g, src, dst, skip_nodes=(), skip_tracks=()):
    seen = {src}; stack = [src]; skip = set(skip_nodes); st = set(skip_tracks)
    while stack:
        u = stack.pop()
        if u == dst: return True
        for (w, L, vc, kind, info, width, R) in g.adj[u]:
            if w in seen or w in skip or (kind == 'trk' and info in st): continue
            seen.add(w); stack.append(w)
    return False


def components(g):
    parent = list(range(len(g.keys)))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for u in range(len(g.keys)):
        for e in g.adj[u]:
            ra, rb = find(u), find(e[0])
            if ra != rb: parent[ra] = rb
    for P in g.pieces:
        for a, b in zip(P['nodes'], P['nodes'][1:]):
            ra, rb = find(int(a)), find(int(b))
            if ra != rb: parent[ra] = rb
    return [find(i) for i in range(len(g.keys))]


# ============================================================================================ path summaries
class Ctx:
    """What summaries and reports need: data, graphs, the design's coordinate origin."""
    def __init__(self, data, graphs, XC, H, contacts):
        self.data, self.graphs, self.XC, self.H, self.contacts = data, graphs, XC, H, contacts
    def xh(self, x, y): return (round(x - self.XC, 2), round(self.H - y, 2))


def summarize(cx, g, path):
    s = dict(total=0.0, track=0.0, plane=0.0, barrel=0.0, vias=0, R=0.0, narrowest=math.inf, narrow_at=None, via_list=[], track_ids=[], joins=[],
             narrow_track=math.inf, narrow_contact=math.inf)
    for (a, b, L, vc, kind, info, width, R) in path:
        s['total'] += L; s['vias'] += vc; s['R'] += R
        if kind == 'join': s['joins'].append(info)
        if kind in ('trk', 'join'): s['track'] += L
        elif kind in ('via', 'tht'):
            s['barrel'] += L
            if kind == 'via' and info not in s['via_list']: s['via_list'].append(info)
        elif kind == 'plane': s['plane'] += L
        if kind == 'trk' and info not in s['track_ids']: s['track_ids'].append(info)
        if kind in ('trk', 'join', 'plane') and width < s['narrowest']:
            s['narrowest'] = width; s['narrow_at'] = cx.xh(*g.pos[b])
        if kind == 'trk': s['narrow_track'] = min(s['narrow_track'], width)
        elif kind in ('join', 'plane'): s['narrow_contact'] = min(s['narrow_contact'], width)
    for k in ('total', 'track', 'plane', 'barrel'): s[k] = round(s[k], 3)
    s['R'] = round(s['R'] * 1e3, 2)                     # mOhm
    for k in ('narrowest', 'narrow_track', 'narrow_contact'): s[k] = round(s[k], 4) if s[k] < math.inf else None
    s['text'] = describe(cx, g, path)
    return s


def describe(cx, g, path):
    parts = []; run = None
    def short(l): return CU_NAMES[l].replace('.Cu', '')
    def flush():
        nonlocal run
        if run: parts.append('%s %.2f%s' % (short(run[0]), run[1], '' if run[2] == math.inf else '/w%.2f' % run[2])); run = None
    for (a, b, L, vc, kind, info, width, R) in path:
        if kind in ('trk', 'join'):
            if run and run[0] == g.lay[a]: run[1] += L; run[2] = min(run[2], width)
            else: flush(); run = [g.lay[a], L, width]
        elif kind in ('via', 'tht'):
            flush(); x, y = g.pos[a]
            parts.append('%s(%.2f,%.2f)%s>%s' % ('via' if kind == 'via' else 'pth', *cx.xh(x, y), short(g.lay[a]), short(g.lay[b])))
        elif kind == 'plane':
            flush(); parts.append('[%s %.2f]' % (g.pieces[info]['label'], L))
    flush()
    return ' > '.join(parts) if parts else '(same pad)'


def outer(s):
    """A GND way into an inner plane: 'outer' = mm of copper on the way (tracks and outer pour crossings)."""
    s['outer'] = round(s['track'] + s['plane'], 3)
    return s


def mv(s, what='track'):
    """'mm/vias' of a path summary (what: 'track' = track mm, 'total' = copper mm with barrels and plane crossings)."""
    return '%.2f/%d' % (s[what], s['vias']) if s else '-'


def w_(x): return '-' if x is None else '%.3f' % x


# ============================================================================================ the design's view
def assigned_caps(D, fps, chips):
    """{(chip, pin): cap ref} from RING / RING_POST by position (KiCad B, QFN frame rotated with the chip), and notes."""
    out = {}; ring_used = {}; notes = []
    if not chips: return out, ring_used, notes
    XC, H = D.at(0.0, 0.0)
    bypos = {(round(x, 2), round(y, 2), side): ref for ref, (lib, sym, val, fpn, (x, y, rot, side)) in D.PARTS.items() if ref.startswith('C')}
    for chip in chips:
        xp, hc, rot = D.CHIP_XY[chip]
        def o(ox, oy):
            bx, by = (ox, oy) if rot == 0 else (-ox, -oy)
            return xp + bx, hc - by
        best = None
        for rname in ('RING', 'RING_POST'):
            ring = getattr(D, rname)
            refs = [bypos.get((round(XC + o(ox, oy)[0], 2), round(H - o(ox, oy)[1], 2), 'B')) for (ox, oy, a, fpn, val, net) in ring]
            if all(refs): best = (rname, ring, refs); break
        if not best: notes.append('%s: ring capacitors not found by position' % chip); continue
        rname, ring, refs = best; ring_used[chip] = rname
        for k, (entry, ref) in enumerate(zip(ring, refs)):
            for pin in RING_PINS[k]:
                out[(chip, str(pin))] = ref
                if D.NETS[chip][str(pin)] != entry[5]: notes.append('%s pin %d is %s, its ring capacitor %s %s' % (chip, pin, D.NETS[chip][str(pin)], ref, entry[5]))
    for ref in sorted(set(out.values())):
        f = fps.get(ref); x, y = D.PARTS[ref][4][:2]
        if not f or abs(f['x'] - x) > 0.01 or abs(f['y'] - y) > 0.01: notes.append('%s: board position differs from the design' % ref)
    return out, ring_used, notes


def farads(v):
    m = re.match(r'([0-9.]+)\s*([pnuµm]?)', v or '')
    return float(m.group(1)) * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6, 'm': 1e-3, '': 1.0}[m.group(2)] if m else 0.0


# ============================================================================================ analysis
def analyse(board, D, a, drc_path, fillrec):
    XC, H = D.at(0.0, 0.0)
    zc = stackup_z(board)
    power = set(getattr(D, 'POWER_NETS', ())) | {'GND'}
    parts = {}
    def pick_nets(fps):
        def num(r): return int(re.sub(r'\D', '', r) or 0)
        parts['chips'] = sorted((r for r, f in fps.items() if f['value'] == 'RP2350B'), key=num)
        parts['flashes'] = sorted((r for r, f in fps.items() if f['value'].startswith('W25Q')), key=num)
        parts['sockets'] = sorted((r for r, f in fps.items() if 'microSD' in f['fpid'] and f['pads'].get(SD_VDD) not in (None, '', 'GND')), key=num)
        parts['convs'] = sorted((r for r, f in fps.items() if f['value'].startswith('TLV62569')), key=num)
        parts['diodes'] = sorted((r for r, f in fps.items() if r.startswith('D') and len(f['pads']) == 2 and set(f['pads'].values()) <= power and '' not in f['pads'].values()
                                  and len(set(f['pads'].values())) == 2), key=num)
        nets = set(power)
        for u in parts['chips']: nets |= {fps[u]['pads'].get(str(p)) for p, _ in RP_SUPPLY}
        for u in parts['flashes']: nets.add(fps[u]['pads'].get(FLASH_VCC))
        for u in parts['sockets']: nets.add(fps[u]['pads'].get(SD_VDD))
        for u in parts['convs']:
            pn = fps[u]['pads']; nets |= {pn.get(v) for v in CONV.values()}
            for r, f in fps.items():                        # inductor output, divider nodes
                vals = set(f['pads'].values())
                if r.startswith('L') and pn.get(CONV['SW']) in vals: nets |= vals
                if r.startswith('R') and pn.get(CONV['FB']) in vals: nets |= vals
        nets.discard(None); nets.discard('')
        parts['nets'] = nets
        return nets
    data, fills, _board = extract(board, pick_nets)
    fps = data['fps']; chips, flashes, sockets, convs, diodes = parts['chips'], parts['flashes'], parts['sockets'], parts['convs'], parts['diodes']
    zone_members(data, fills)
    contacts = measure_contacts(data)
    labels = {zr['id']: '%s %s%s' % (zr['net'], CU_NAMES[zr['layer']].replace('.Cu', ''), ' plane' if zr['inner'] else ' pour') for zr in data['zones']}
    pads_by = {(p['ref'], p['num'], p['net']): p for p in data['pads']}
    def padrec(ref, num):
        net = fps.get(ref, {}).get('pads', {}).get(str(num))
        return pads_by.get((ref, str(num), net))
    ep_pads = {padrec(u, '81')['id'] for u in chips if padrec(u, '81')}
    nets = sorted(parts['nets'])
    graphs = {n: build_graph(data, n, zc, contacts, labels, ep_pads if n == 'GND' else ()) for n in nets}
    for g in graphs.values(): g.prefer = a.neck
    cx = Ctx(data, graphs, XC, H, contacts)
    def node(ref, num):
        p = padrec(ref, num)
        return (graphs[p['net']].pad_node(p['id']), p) if p and p['net'] in graphs else (None, p)
    checks = []; notes = []
    def check(ok, text): checks.append((bool(ok), text))
    lim_mm, lim_v, margin, neck_min, trunk_w = a.limit_mm, a.limit_vias, a.margin, a.neck, a.trunk
    res = {'limits': dict(mm=lim_mm, vias=lim_v, margin=margin, neck=neck_min, trunk=trunk_w), 'parts': {k: v for k, v in parts.items() if k != 'nets'},
           'nets': nets, 'stackup_z': zc}

    # ---------------------------------------------------------------- capacitors and their owners
    caps = {}
    for ref, f in fps.items():
        if not ref.startswith('C') or len(f['pads']) != 2: continue
        vals = list(f['pads'].values())
        if 'GND' in vals and len(set(vals)) == 2:
            net = [v for v in vals if v != 'GND'][0]
            if net in graphs:
                caps[ref] = dict(ref=ref, net=net, value=f['value'], side=f['side'], pad=[k for k, v in f['pads'].items() if v == net][0],
                                 gnd=[k for k, v in f['pads'].items() if v == 'GND'][0])
    assigned, ring_used, n2 = assigned_caps(D, fps, chips); notes += n2
    ring_refs = set(assigned.values())
    def nearest_cap(ref, num, net, exclude=(), min_f=0.0, within=None):
        p = padrec(ref, num)
        c = [(math.hypot(padrec(r, cc['pad'])['x'] - p['x'], padrec(r, cc['pad'])['y'] - p['y']), r) for r, cc in caps.items()
             if cc['net'] == net and r not in exclude and farads(cc['value']) >= min_f]
        c = [x for x in c if within is None or x[0] <= within]
        return [r for _, r in sorted(c)]
    for u in flashes:
        n = fps[u]['pads'].get(FLASH_VCC); c = nearest_cap(u, FLASH_VCC, n, ring_refs)
        if c: assigned[(u, FLASH_VCC)] = c[0]
    for u in sockets:
        n = fps[u]['pads'].get(SD_VDD); c = nearest_cap(u, SD_VDD, n, ring_refs | set(assigned.values()))
        if c: assigned[(u, SD_VDD)] = c[0]
    # design against board: the nets of the chip pins
    for u in chips:
        for p, name in RP_SUPPLY + RP_GND + RP_OPEN:
            dn = (D.NETS.get(u, {}).get(str(p)) or ''); bn = fps[u]['pads'].get(str(p), '')
            if dn != bn: notes.append('%s pin %d (%s): design %r, board %r' % (u, p, name, dn, bn))
    check(not [x for x in notes if 'board position differs' in x or 'not found by position' in x or ': design' in x],
          'design against board: every chip pin has the design net and every ring capacitor sits where the design puts it (%d chips)' % len(chips))

    # ---------------------------------------------------------------- one search per net from all inner-plane members
    to_plane = {}
    for n, g in graphs.items():
        src = [int(x) for P in g.pieces if P['inner'] for x in P['nodes']]
        if src:
            to_plane[n] = search(g, src, planes=True)
            to_plane[n + '@robust'] = search(g, src, planes=True, min_neck=neck_min)
    def plane_way(net, nd, robust=False):
        r = to_plane.get(net + ('@robust' if robust else ''))
        if r is None or nd is None or not np.isfinite(r[0][nd]): return None
        return summarize(cx, graphs[net], reversed_path(path_of(r[2], nd)))

    # ---------------------------------------------------------------- Q1: every power pin, its contacts
    pin_list = []
    for u in chips:
        for p, name in RP_SUPPLY: pin_list.append((u, str(p), name, 'supply'))
        for p, name in RP_GND: pin_list.append((u, str(p), name, 'gnd'))
        for p, name in RP_OPEN: pin_list.append((u, str(p), name, 'open'))
    for u in flashes: pin_list += [(u, FLASH_VCC, 'VCC', 'supply'), (u, FLASH_GND, 'GND', 'gnd')]
    for u in sockets: pin_list.append((u, SD_VDD, 'VDD', 'supply'))
    for u in convs: pin_list += [(u, v, k, 'conv') for k, v in CONV.items()]
    for u in convs:
        sw = fps[u]['pads'][CONV['SW']]
        for r, f in fps.items():
            if r.startswith('L') and sw in f['pads'].values(): pin_list += [(r, k, 'L ' + ('SW' if v == sw else 'OUT'), 'conv') for k, v in sorted(f['pads'].items())]
    for d in diodes: pin_list += [(d, '1', 'K', 'conv'), (d, '2', 'A', 'conv')]
    by_item = defaultdict(list)
    for ci, c in enumerate(contacts):
        by_item[c['a']].append(ci); by_item[c['b']].append(ci)
    zone_touch = defaultdict(list)
    for zr in data['zones']:
        for pc in zr['pieces']:
            for pi_, touch in pc['pads']: zone_touch[pi_].append((labels[zr['id']], touch))
    pins = []
    for ref, num, name, kind in pin_list:
        net = fps[ref]['pads'].get(num)
        p = padrec(ref, num)
        row = dict(ref=ref, pin=num, name=name, kind=kind, net=net or '')
        if kind == 'open':
            row['contacts'] = 0; row['status'] = 'no net (as the design wants)' if not net else 'net %s' % net
            pins.append(row); continue
        if p is None: row['status'] = 'pad not found'; pins.append(row); continue
        cs = [contacts[ci] for ci in by_item[('P', p['id'])]]
        zs = zone_touch.get(p['id'], [])
        row['xy'] = cx.xh(p['x'], p['y']); row['board_xy'] = (round(p['x'], 3), round(p['y'], 3))
        row['contacts'] = len(cs) + len(zs)
        row['widest_contact'] = max([c['neck'] for c in cs] + [min(t, p['width']) for _, t in zs] + [0.0])
        row['narrow_contacts'] = [dict(neck=c['neck'], at=cx.xh(c['x'], c['y'])) for c in cs if c['neck'] < neck_min]
        row['zones'] = [z for z, _ in zs]
        if row['contacts'] == 0: row['status'] = 'OPEN: no copper of %s touches the pad' % net
        elif row['widest_contact'] < neck_min: row['status'] = 'WEAK: widest contact %.3f mm' % row['widest_contact']
        else: row['status'] = 'ok'
        pins.append(row)
    res['pins'] = pins
    pin_row = {(r['ref'], r['pin']): r for r in pins}

    # ---------------------------------------------------------------- Q2: supply pins, loops to their capacitors and the plane
    supply_rows = []
    for ref, num, name, kind in pin_list:
        if kind != 'supply': continue
        row = pin_row[(ref, num)]
        if row['status'].startswith('OPEN') or row['net'] not in graphs: continue
        g = graphs[row['net']]; src, p = node(ref, num)
        asg = assigned.get((ref, num)); c = caps.get(asg) if asg else None
        cn, cp = node(asg, c['pad']) if c else (None, None)
        cap_nodes = {graphs[row['net']].pad_node(padrec(r, cc['pad'])['id']): r for r, cc in caps.items() if cc['net'] == row['net']}
        r = dict(ref=ref, pin=num, name=name, net=row['net'], cap=asg, cap_value=c['value'] if c else None, cap_side=c['side'] if c else None)
        dist, nv, prev, order = search(g, src, planes=True, targets=[cn] if cn is not None else None)
        settled_caps = [n for n in order if n in cap_nodes]
        if settled_caps:
            r['nearest'] = dict(cap=cap_nodes[settled_caps[0]], **summarize(cx, g, path_of(prev, settled_caps[0])))
        if cn is not None and np.isfinite(dist[cn]):
            r['loop'] = summarize(cx, g, path_of(prev, cn))
            d2, nv2, prev2, _ = search(g, src, planes=False, targets=[cn])
            r['loop_tracks_only'] = summarize(cx, g, path_of(prev2, cn)) if np.isfinite(d2[cn]) else None
            d3, nv3, prev3, _ = search(g, src, planes=True, targets=[cn], min_neck=neck_min)
            r['loop_robust'] = summarize(cx, g, path_of(prev3, cn)) if np.isfinite(d3[cn]) else None
            r['floor'] = round(math.hypot(p['x'] - cp['x'], p['y'] - cp['y']), 3)
            r['cap_plane'] = plane_way(row['net'], cn)
        r['plane'] = plane_way(row['net'], src)
        r['plane_robust'] = plane_way(row['net'], src, robust=True)
        L = r.get('loop')
        flags = []
        if not L: flags.append('no-loop')
        else:
            if L['track'] > lim_mm + 1e-9: flags.append('len')
            if L['vias'] > lim_v: flags.append('vias')
            if r['floor'] > lim_mm + 1e-9: flags.append('floor')
            if abs(L['track'] - lim_mm) <= margin: flags.append('marginal')
            if 'len' in flags and L['track'] - r['floor'] <= margin: flags.append('at-floor')
            if L['narrowest'] is not None and L['narrowest'] < neck_min: flags.append('neck')
            rb = r.get('loop_robust')
            if not rb or abs(rb['track'] - L['track']) > 0.001 or rb['vias'] != L['vias']: flags.append('neck-dependent')
        r['flags'] = flags
        supply_rows.append(r)
    res['supply'] = supply_rows

    # ---------------------------------------------------------------- Q3: +1V1 (the DVDD net): sense point, trunk, cut vias, bridges
    dv_net = fps[chips[0]]['pads'].get('10') if chips else None
    q3 = None
    if dv_net in graphs:
        g = graphs[dv_net]
        sense = None
        for r, f in fps.items():                             # the divider resistor between the output and FB
            if r.startswith('R') and dv_net in f['pads'].values() and any(fps[u]['pads'][CONV['FB']] in f['pads'].values() for u in convs):
                sense = (r, [k for k, v in f['pads'].items() if v == dv_net][0])
        src = node(*sense)[0] if sense else None
        trunk_nodes = [n for n in range(len(g.keys)) if any(e[3] == 'trk' and e[5] >= trunk_w - 1e-9 for e in g.adj[n])]
        dt = search(g, trunk_nodes, planes=False) if trunk_nodes else None
        ds = search(g, src, cost='res', planes=False) if src is not None else None
        dr = search(g, src, cost='res', planes=False, min_neck=neck_min) if src is not None else None
        widths = Counter()
        for t in data['tracks']:
            if t['net'] == dv_net: widths[round(t['w'], 2)] += math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0'])
        q3 = dict(net=dv_net, sense='%s.%s' % sense if sense else None, widths={'%.2f' % k: round(v, 1) for k, v in sorted(widths.items())}, pins=[])
        for u in chips:
            for p in ('10', '32', '51'):
                n, pp = node(u, p)
                row = dict(ref=u, pin=p)
                if n is None or ds is None or not np.isfinite(ds[0][n]): row['status'] = 'no track path from %s' % q3['sense']; q3['pins'].append(row); continue
                path = path_of(ds[2], n); s = summarize(cx, g, path)
                rev = path[::-1]; at_pin = 0.0; k = 0
                while k < len(rev) and not (rev[k][4] == 'trk' and rev[k][6] >= trunk_w - 1e-9):
                    if rev[k][4] == 'trk': at_pin += rev[k][2]
                    k += 1
                narrow = sum(e[2] for e in path if e[4] == 'trk' and e[6] < trunk_w - 1e-9)
                cut = []
                for vid in s['via_list']:
                    vn = [g.key2id[k2] for k2 in g.key2id if k2[0] == 'V' and k2[1] == vid]
                    if not reachable(g, src, n, skip_nodes=vn):
                        v = data['vias'][vid]; cut.append(cx.xh(v['x'], v['y']))
                bridges = []
                for tid in s['track_ids']:
                    t = data['tracks'][tid]
                    if t['w'] < trunk_w - 1e-9 and not reachable(g, src, n, skip_tracks=[tid]):
                        bridges.append((round(t['w'], 3), round(math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']), 2), CU_NAMES[t['layer']].replace('.Cu', ''),
                                        cx.xh((t['x0'] + t['x1']) / 2, (t['y0'] + t['y1']) / 2)))
                trunk = None
                if dt is not None and np.isfinite(dt[0][n]): trunk = summarize(cx, g, reversed_path(path_of(dt[2], n)))
                rob = summarize(cx, g, path_of(dr[2], n)) if np.isfinite(dr[0][n]) else None
                row.update(status='ok', length=s['track'], vias=s['vias'], R=s['R'], narrowest=s['narrowest'], narrow_at=s['narrow_at'],
                           R_robust=rob['R'] if rob else None, narrowest_robust=rob['narrowest'] if rob else None,
                           narrow_at_pin=round(at_pin, 2), narrow_elsewhere=round(narrow - at_pin, 2), cut_vias=cut,
                           narrow_bridges=[b for b in bridges], trunk=trunk, text=s['text'])
                q3['pins'].append(row)
        # narrowest pieces of the network away from the pins: tracks under the trunk width not within 3 mm of a DVDD pin
        dvdd_xy = [(padrec(u, p)['x'], padrec(u, p)['y']) for u in chips for p in ('10', '32', '51') if padrec(u, p)]
        far = Counter()
        for t in data['tracks']:
            if t['net'] != dv_net or t['w'] >= trunk_w - 1e-9: continue
            mid = ((t['x0'] + t['x1']) / 2, (t['y0'] + t['y1']) / 2)
            if min(math.hypot(mid[0] - x, mid[1] - y) for x, y in dvdd_xy) > 3.0: far[round(t['w'], 2)] += math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0'])
        q3['narrow_far_from_pins'] = {'%.2f' % k: round(v, 2) for k, v in sorted(far.items())}
    res['q3'] = q3

    # ---------------------------------------------------------------- Q4: converters
    gg = graphs.get('GND')
    def gnd_way(src_ref, src_num, dst_ref, dst_num, planes=True):
        s, _ = node(src_ref, src_num); d, _ = node(dst_ref, dst_num)
        if s is None or d is None: return None
        dist, nv, prev, _ = search(gg, s, planes=planes, targets=[d])
        return summarize(cx, gg, path_of(prev, d)) if np.isfinite(dist[d]) else None
    def way(net, s, d, cost='len'):
        if s is None or d is None or net not in graphs: return None
        dist, nv, prev, _ = search(graphs[net], s, cost=cost, planes=(cost == 'len'), targets=[d])
        return summarize(cx, graphs[net], path_of(prev, d)) if np.isfinite(dist[d]) else None
    def shapes_of_net(net, layers=None):
        out = []
        for t in data['tracks']:
            if t['net'] == net: out.append(('T', t['layer'], (t['x0'], t['y0']), (t['x1'], t['y1']), t['w']))
        for v in data['vias']:
            if v['net'] == net: out.append(('V', None, (v['x'], v['y']), v['dia'] / 2))
        for p in data['pads']:
            if p['net'] == net: out.append(('P', tuple(p['layers']), p['poly']))
        return out
    def sdist(A, B, same_layer):
        def lays(s): return {s[1]} if s[0] == 'T' else set(CU_ORDER) if s[0] == 'V' else set(s[1])
        if same_layer and not (lays(A) & lays(B)): return math.inf
        if A[0] > B[0]: A, B = B, A
        if A[0] == 'P' and B[0] == 'P': return poly_poly_gap(A[2], B[2])
        if A[0] == 'P' and B[0] == 'T': return max(0.0, seg_poly_gap(B[2], B[3], A[2]) - B[4] / 2)
        if A[0] == 'P' and B[0] == 'V': return max(0.0, (0.0 if in_poly(B[2][0], B[2][1], A[2]) else boundary_dist(A[2], B[2])) - B[3])
        if A[0] == 'T' and B[0] == 'T': return max(0.0, seg_closest(A[2], A[3], B[2], B[3])[2] - (A[4] + B[4]) / 2)
        if A[0] == 'T' and B[0] == 'V': return max(0.0, point_param(A[2], A[3], B[2])[1] - A[4] / 2 - B[3])
        return max(0.0, math.hypot(A[2][0] - B[2][0], A[2][1] - B[2][1]) - A[3] - B[3])
    def min_dist(S1, S2, same_layer):
        best = math.inf
        for A in S1:
            for B in S2: best = min(best, sdist(A, B, same_layer))
        return round(best, 3) if best < math.inf else None
    q4 = []
    for u in convs:
        pn = fps[u]['pads']; vin, gnd, sw, fb = pn[CONV['VIN']], pn[CONV['GND']], pn[CONV['SW']], pn[CONV['FB']]
        L = next((r for r, f in fps.items() if r.startswith('L') and sw in f['pads'].values()), None)
        lsw = [k for k, v in fps[L]['pads'].items() if v == sw][0]; lout = [k for k, v in fps[L]['pads'].items() if v != sw][0]; out = fps[L]['pads'][lout]
        cin = nearest_cap(u, CONV['VIN'], vin)
        cout = nearest_cap(L, lout, out, min_f=1e-6, within=10.0)
        c = dict(ref=u, value=fps[u]['value'], vin=vin, sw=sw, fb=fb, out=out, inductor=L, cin=cin[:1], cout=cout, xy=cx.xh(fps[u]['x'], fps[u]['y']))
        pv = padrec(u, CONV['VIN']); pg = padrec(u, CONV['GND'])
        if cin:
            ci = caps[cin[0]]; cpp, cgp = padrec(cin[0], ci['pad']), padrec(cin[0], ci['gnd'])
            c['cin_vin'] = way(vin, node(u, CONV['VIN'])[0], node(cin[0], ci['pad'])[0])
            c['cin_gnd'] = gnd_way(cin[0], ci['gnd'], u, CONV['GND'])
            c['cin_gnd_tracks'] = gnd_way(cin[0], ci['gnd'], u, CONV['GND'], planes=False)
            c['cin_floor'] = round(math.hypot(pv['x'] - cpp['x'], pv['y'] - cpp['y']) + math.hypot(pg['x'] - cgp['x'], pg['y'] - cgp['y']), 3)
        c['en_vin'] = way(vin, node(u, CONV['EN'])[0], node(u, CONV['VIN'])[0])
        swS = shapes_of_net(sw)
        area = Counter(); swlen = 0.0
        for t in data['tracks']:
            if t['net'] == sw:
                Lt = math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']); swlen += Lt
                area[CU_NAMES[t['layer']]] += Lt * t['w'] + math.pi * t['w'] ** 2 / 4
        for p in data['pads']:
            if p['net'] == sw:
                for l in p['layers']: area[CU_NAMES[l]] += p['area']
        swv = [v for v in data['vias'] if v['net'] == sw]
        c['sw'] = dict(track_mm=round(swlen, 2), widths=sorted({round(t['w'], 2) for t in data['tracks'] if t['net'] == sw}), vias=len(swv),
                       area={k: round(v, 2) for k, v in area.items()}, area_total=round(sum(area.values()), 2),
                       pads_only=round(sum(p['area'] for p in data['pads'] if p['net'] == sw), 2))
        x0, y0, x1, y1 = fps[L]['bbox']; Lbox = [('P', tuple(CU_ORDER), [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])]
        fbnets = [fb] + sorted({v for r, f in fps.items() if r.startswith('R') and fb in f['pads'].values() for v in f['pads'].values()} - {fb, out, 'GND', ''})
        c['fb_nets'] = []
        def no_conv(S): return [x for x in S if not (x[0] == 'P' and any(x[2] is p['poly'] for p in data['pads'] if p['ref'] == u))]
        c['fb_pin_to_sw_pin'] = min_dist([x for x in shapes_of_net(fb) if x[0] == 'P' and x[2] is padrec(u, CONV['FB'])['poly']],
                                         [x for x in swS if x[0] == 'P' and x[2] is padrec(u, CONV['SW'])['poly']], True)
        for n in fbnets:
            S = no_conv(shapes_of_net(n)); trk = [t for t in data['tracks'] if t['net'] == n]
            inL = 0.0
            for t in trk:                                     # track length over the inductor's outline (plan view, any layer)
                Lt = math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']); k = max(1, int(Lt / 0.05))
                inL += sum(Lt / k for j in range(k) for fx in [(j + 0.5) / k] if x0 <= t['x0'] + (t['x1'] - t['x0']) * fx <= x1 and y0 <= t['y0'] + (t['y1'] - t['y0']) * fx <= y1)
            fbpads = sorted('%s.%s' % (p['ref'], p['num']) for p in data['pads'] if p['net'] == n)
            reach = None
            if n == fb:
                s0 = node(u, CONV['FB'])[0]
                if s0 is not None:
                    dist, nv, prev, _ = search(graphs[n], s0, planes=False)
                    reach = {'%s.%s' % (p['ref'], p['num']): round(float(dist[graphs[n].pad_node(p['id'])]), 2) for p in data['pads'] if p['net'] == n and p['ref'] != u}
            c['fb_nets'].append(dict(net=n, track_mm=round(sum(math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']) for t in trk), 2),
                                     layers=sorted({CU_NAMES[t['layer']].replace('.Cu', '') for t in trk}), vias=sum(1 for v in data['vias'] if v['net'] == n),
                                     pads=fbpads, from_fb_pin=reach, to_sw_same_layer=min_dist(S, no_conv(swS), True), to_sw_any_layer=min_dist(S, no_conv(swS), False),
                                     to_inductor_outline=min_dist(S, Lbox, False), over_inductor_mm=round(inL, 2)))
        c['cout_detail'] = []
        for r in cout:
            cc = caps[r]; cpp = padrec(r, cc['pad'])
            c['cout_detail'].append(dict(cap=r, value=cc['value'], side=cc['side'], from_L=way(out, node(L, lout)[0], node(r, cc['pad'])[0]),
                                         gnd=gnd_way(r, cc['gnd'], u, CONV['GND']), gnd_tracks=gnd_way(r, cc['gnd'], u, CONV['GND'], planes=False),
                                         gnd_floor=round(math.hypot(padrec(r, cc['gnd'])['x'] - pg['x'], padrec(r, cc['gnd'])['y'] - pg['y']), 3)))
        q4.append(c)
    res['q4'] = q4

    # ---------------------------------------------------------------- Q5: feeds (connector -> diode anode, cathode -> converter VIN)
    q5 = []
    nw = getattr(D, 'NET_WIDTH', {})
    def feed(net, s, d, label):
        if s is None or d is None or net not in graphs: return
        dist, nv, prev, _ = search(graphs[net], s, cost='res', planes=False, targets=[d])
        if not np.isfinite(dist[d]): q5.append(dict(net=net, what=label, status='NO PATH')); return
        path = path_of(prev, d); sm = summarize(cx, graphs[net], path)
        under = sum(e[2] for e in path if e[4] == 'trk' and net in nw and e[6] < nw[net] - 1e-9)
        d2, nv2, prev2, _ = search(graphs[net], s, cost='res', planes=False, targets=[d], min_neck=neck_min)
        rob = summarize(cx, graphs[net], path_of(prev2, d)) if np.isfinite(d2[d]) else None
        q5.append(dict(net=net, what=label, status='ok', length=sm['track'], vias=sm['vias'], R=sm['R'], narrowest=sm['narrowest'],
                       narrow_track=sm['narrow_track'], narrow_contact=sm['narrow_contact'],
                       R_robust=rob['R'] if rob else None, narrowest_robust=rob['narrowest'] if rob else None,
                       narrow_at=sm['narrow_at'], design_width=nw.get(net), under_design_mm=round(under, 2), text=sm['text']))
    for d in diodes:
        k, an = fps[d]['pads']['1'], fps[d]['pads']['2']
        for r, f in sorted(fps.items()):
            if r.startswith('J'):
                for num, n in sorted(f['pads'].items()):
                    if n == an: feed(an, node(r, num)[0], node(d, '2')[0], '%s.%s -> %s anode' % (r, num, d))
        for u in convs:
            if fps[u]['pads'][CONV['VIN']] == k: feed(k, node(d, '1')[0], node(u, CONV['VIN'])[0], '%s cathode -> %s VIN' % (d, u))
    res['q5'] = q5

    # ---------------------------------------------------------------- GND side
    gnd = dict(caps={}, chips={}, flash_pin4={})
    if gg is not None:
        r = to_plane.get('GND')
        for ref, c in caps.items():
            n, p = node(ref, c['gnd'])
            if r is not None and n is not None and np.isfinite(r[0][n]): gnd['caps'][ref] = dict(plane=outer(summarize(cx, gg, reversed_path(path_of(r[2], n)))))
        epv_cfg = getattr(D, 'EP_VIAS', {})
        for u in chips:
            ep = padrec(u, '81'); hx, hy = ep['sx'] / 2, ep['sy'] / 2
            epv = [v for v in data['vias'] if abs(v['x'] - ep['x']) <= hx + 1e-6 and abs(v['y'] - ep['y']) <= hy + 1e-6]
            others = [v for v in data['other_vias'] if abs(v['x'] - ep['x']) <= hx + v['dia'] / 2 and abs(v['y'] - ep['y']) <= hy + v['dia'] / 2]
            src = [gg.key2id[('V', v['id'], 0)] for v in epv if v['net'] == 'GND' and ('V', v['id'], 0) in gg.key2id] + [gg.pad_node(ep['id'])]
            tgt = {}
            for (cu, pin), ref in assigned.items():
                if cu == u and ref in caps: tgt[node(ref, caps[ref]['gnd'])[0]] = ('cap', ref)
            for pin, name in RP_GND[:2]: tgt[node(u, str(pin))[0]] = ('pin', pin)
            dist, nv, prev, _ = search(gg, src, planes=True, targets=list(tgt))
            gp = {}
            for n, (k, what) in tgt.items():
                s = summarize(cx, gg, reversed_path(path_of(prev, n))) if np.isfinite(dist[n]) else None
                if k == 'cap':
                    cpd = padrec(what, caps[what]['gnd'])
                    floor = min(math.hypot(cpd['x'] - v['x'], cpd['y'] - v['y']) for v in epv) + abs(zc[CU_NAMES[cpd['layers'][0]]] - zc['F.Cu'])
                    gnd['caps'].setdefault(what, {})['ep'] = dict(path=s, floor=round(floor, 3), excess=round(s['total'] - floor, 3) if s else None, chip=u)
                else: gp[what] = s
            gnd['chips'][u] = dict(n=len(epv), nets=dict(Counter(v['net'] for v in epv)), dia=sorted({v['dia'] for v in epv}), drill=sorted({v['drill'] for v in epv}),
                                   offs=sorted({(round(v['x'] - ep['x'], 2), round(v['y'] - ep['y'], 2)) for v in epv}), locked=all(v['locked'] for v in epv),
                                   other_net_vias=len(others), expect=dict(epv_cfg), pins=gp)
        for u in flashes:
            n, p = node(u, FLASH_GND)
            if r is not None and n is not None and np.isfinite(r[0][n]): gnd['flash_pin4'][u] = outer(summarize(cx, gg, reversed_path(path_of(r[2], n))))
    res['gnd'] = gnd

    # ---------------------------------------------------------------- narrow contacts on the checked nets
    users = defaultdict(list)                          # contact -> the supply pins whose loop or way into the plane uses it
    for r in supply_rows:
        for key in ('loop', 'plane'):
            for ci in (r.get(key) or {}).get('joins', []): users[ci].append('%s.%s %s' % (r['ref'], r['pin'], key))
    narrow = []
    for ci, c in enumerate(contacts):
        if c['neck'] >= neck_min: continue
        g = graphs[c['net']]; u, w = g.join_nodes[ci]
        if u == w: detour = 0.0                         # both items meet in one node (e.g. a via in a pad): nothing to bypass
        else:
            dist, nv, prev, _ = search(g, u, planes=True, targets=[w], skip_joins={ci})
            L = next(e[1] for e in g.adj[u] if e[0] == w and e[3] == 'join' and e[4] == ci)
            detour = round(float(dist[w]) - L, 3) if np.isfinite(dist[w]) else None
        narrow.append(dict(net=c['net'], neck=c['neck'], gap=c['gap'], at=cx.xh(c['x'], c['y']), board=(c['x'], c['y']), detour=detour,
                           items=[item_name(data, c['a']), item_name(data, c['b'])], used_by=sorted(set(users.get(ci, [])))))
    res['narrow_contacts'] = sorted(narrow, key=lambda x: (x['net'] == 'GND', x['neck']))

    # ---------------------------------------------------------------- self-checks
    if fillrec:
        st = {(z[0], z[2]): z for z in fillrec['stored']}
        fr = {(z[0], z[2]): z for z in fillrec.get('fresh', fillrec['stored'])}
        diff = [k for k in set(st) | set(fr) if k not in st or k not in fr or st[k][3] != fr[k][3] or abs(st[k][4] - fr[k][4]) > 0.01]
        check(not diff, 'stored fill equals a fresh fill: %d zone layers, %s' % (len(fr), 'all equal' if not diff else 'differ: %s' % diff) if 'fresh' in fillrec else
              'fill as stored (--stored-fill): %d zone layers' % len(st))
    bad_gap = [c for c in contacts if c['gap'] > GAP_OK]
    check(not bad_gap, 'every KiCad contact has an exact gap of at most %g mm: %d contacts%s' % (GAP_OK, len(contacts),
          '' if not bad_gap else '; apart: ' + ', '.join('%s %s-%s %.4f' % (c['net'], item_name(data, c['a']), item_name(data, c['b']), c['gap']) for c in bad_gap[:8])))
    ringless = [(labels[zr['id']], vi) for zr in data['zones'] for pc in zr['pieces'] for vi, ring, ctr in pc['vias'] if ring <= 0]
    own = sum(1 for zr in data['zones'] for pc in zr['pieces'] if pc['inside_via'] is not None)
    check(not ringless, 'every via counted inside a zone has a contact arc outside its ring: %d via-zone entries; %d fill pieces lie wholly inside a via ring (not entries)%s'
          % (sum(len(pc['vias']) for zr in data['zones'] for pc in zr['pieces']), own, '' if not ringless else '; without arc: %s' % ringless[:6]))
    res['ring_only_vias'] = [dict(zone=labels[zr['id']], via=cx.xh(data['vias'][vi]['x'], data['vias'][vi]['y']), arc_fraction=ring)
                             for zr in data['zones'] for pc in zr['pieces'] for vi, ring, ctr in pc['vias'] if not ctr]
    ep_chk = endpoint_check(data, graphs, zc, assigned, caps, padrec, supply_rows)
    res['endpoint_check'] = ep_chk
    check(ep_chk['shorter'] == 0 and ep_chk['only_simple'] == 0,
          'endpoint model (tracks joined at coinciding ends only): %d pin-capacitor pairs, %d equal, %d longer in the model, %d shorter, %d joined only by the model, %d joined only by the tool'
          % (ep_chk['pairs'], ep_chk['equal'], ep_chk['longer'], ep_chk['shorter'], ep_chk['only_simple'], ep_chk['only_tool']))
    drc = parse_drc(drc_path)
    res['drc'] = None
    if drc is not None:
        comp_info = {}; bad = []
        for n, g in graphs.items():
            comp = components(g); with_items = {comp[i] for i in range(len(g.keys))}
            pairs = [(x, y) for x, y in drc['pairs'] if ('[%s]' % n) in x[0] and ('[%s]' % n) in y[0]]
            comp_info[n] = dict(drc_pairs=len(pairs), tool_components=len(with_items))
            if not pairs and len(with_items) > 1: bad.append('%s: DRC finds it whole, the tool has %d components' % (n, len(with_items)))
            for x, y in pairs:
                nx_, ny_ = drc_item_node(g, data, *x), drc_item_node(g, data, *y)
                if nx_ is not None and ny_ is not None and comp[nx_] == comp[ny_]: bad.append('%s: DRC pair %s / %s joined in the tool' % (n, x[0], y[0]))
        res['drc'] = dict(unconnected=drc['count'], nets=comp_info, isolated=len(drc['isolated']), problems=bad)
        check(not bad, "KiCad's rule check against the tool's components: %s unconnected items on the board; %s" % (drc['count'], 'consistent on every checked net' if not bad else '; '.join(bad[:6])))
    res['counts'] = {n: data['counts'].get(n, {}) for n in nets}
    res['vias_per_net'] = dict(Counter(v['net'] for v in data['vias']))
    res['notes'] = notes; res['checks'] = checks
    res['unconnected_kicad'] = data['unconnected_kicad']
    res['caps'] = caps; res['assigned'] = {'%s.%s' % k: v for k, v in assigned.items()}; res['ring_used'] = ring_used
    return res


def item_name(data, key):
    k, i = key
    if k == 'T':
        t = data['tracks'][i]; return 'track %s w%.2f' % (CU_NAMES[t['layer']].replace('.Cu', ''), t['w'])
    if k == 'V': return 'via'
    p = data['pads'][i]; return 'pad %s.%s' % (p['ref'], p['num'])


def endpoint_check(data, graphs, zc, assigned, caps, padrec, supply_rows):
    """Independent model of the track-only pin-to-capacitor paths: track ends that coincide (1 um) are one node, a track end
    inside a pad's outline or a via's disc joins it (offset from its centre), vias join their layers by the barrel."""
    res = dict(pairs=0, equal=0, longer=0, shorter=0, only_simple=0, only_tool=0, worst=[])
    for net in {r['net'] for r in supply_rows}:
        adj = defaultdict(list)
        def add(a, b, L): adj[a].append((b, L)); adj[b].append((a, L))
        def key(l, x, y): return (l, round(x, 3), round(y, 3))
        ends = defaultdict(list)
        for t in data['tracks']:
            if t['net'] != net: continue
            a, b = key(t['layer'], t['x0'], t['y0']), key(t['layer'], t['x1'], t['y1'])
            add(a, b, math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0'])); ends[t['layer']] += [a, b]
        for v in data['vias']:
            if v['net'] != net: continue
            for i, l in enumerate(v['layers']):
                n0 = ('V', v['id'], l)
                for l2 in v['layers'][i + 1:]: add(n0, ('V', v['id'], l2), abs(zc[CU_NAMES[l]] - zc[CU_NAMES[l2]]))
                for e in ends[l]:
                    d = math.hypot(e[1] - v['x'], e[2] - v['y'])
                    if d <= v['dia'] / 2 + 1e-6: add(n0, e, d)
        for p in data['pads']:
            if p['net'] != net: continue
            for l in p['layers']:
                for e in ends[l]:
                    if in_poly(e[1], e[2], p['poly']): add(('P', p['id'], l), e, math.hypot(e[1] - p['x'], e[2] - p['y']))
        def dj(src, dst):
            dist = {src: 0.0}; h = [(0.0, 0, src)]; k = 0
            while h:
                d, _, u = heapq.heappop(h)
                if u == dst: return d
                if d > dist.get(u, math.inf): continue
                for w, L in adj[u]:
                    if d + L < dist.get(w, math.inf) - 1e-12: k += 1; dist[w] = d + L; heapq.heappush(h, (d + L, k, w))
            return None
        for r in supply_rows:
            if r['net'] != net or not r.get('cap'): continue
            p = padrec(r['ref'], r['pin']); cp = padrec(r['cap'], caps[r['cap']]['pad'])
            simple = dj(('P', p['id'], p['layers'][0]), ('P', cp['id'], cp['layers'][0]))
            tool = r.get('loop_tracks_only'); res['pairs'] += 1
            if simple is None and tool is None: continue
            if simple is None: res['only_tool'] += 1; continue
            if tool is None: res['only_simple'] += 1; continue
            d = simple - tool['total']
            if abs(d) <= 0.005: res['equal'] += 1
            elif d > 0: res['longer'] += 1
            else: res['shorter'] += 1; res['worst'].append(('%s.%s' % (r['ref'], r['pin']), round(d, 3)))
    return res


def parse_drc(path):
    if not path or not os.path.exists(path): return None
    txt = open(path).read()
    i = txt.find('unconnected pads **')
    pairs = []
    if i >= 0:
        for m in re.finditer(r'\[unconnected_items\][^\n]*\n[^\n]*\n\s*@\(([-0-9.]+) mm, ([-0-9.]+) mm\): ([^\n]*)\n\s*@\(([-0-9.]+) mm, ([-0-9.]+) mm\): ([^\n]*)', txt[i:]):
            pairs.append(((m.group(3), float(m.group(1)), float(m.group(2))), (m.group(6), float(m.group(4)), float(m.group(5)))))
    iso = re.findall(r'\[isolated_copper\]', txt)
    m = re.search(r'\*\* Found (\d+) unconnected pads', txt)
    return {'count': int(m.group(1)) if m else None, 'pairs': pairs, 'isolated': iso}


def drc_item_node(g, data, desc, x, y):
    m = re.match(r'Pad (\S+) \[([^\]]+)\] of (\S+) on (\S+)', desc)
    if m:
        for p in data['pads']:
            if p['ref'] == m.group(3) and p['num'] == m.group(1) and p['net'] == g.net: return g.pad_node(p['id'])
        return None
    m = re.match(r'Track \[([^\]]+)\] on (\S+), length ([0-9.]+)', desc)
    if m:
        for t in data['tracks']:
            if t['net'] != g.net or CU_NAMES[t['layer']] != m.group(2): continue
            if abs(math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']) - float(m.group(3))) > 0.002: continue
            for e, (tx, ty) in ((0.0, (t['x0'], t['y0'])), (1.0, (t['x1'], t['y1']))):
                if abs(tx - x) < 0.002 and abs(ty - y) < 0.002: return g.key2id.get(('T', t['id'], e))
        return None
    m = re.match(r'Via \[([^\]]+)\]', desc)
    if m:
        for v in data['vias']:
            if v['net'] == g.net and abs(v['x'] - x) < 0.002 and abs(v['y'] - y) < 0.002: return g.key2id.get(('V', v['id'], v['layers'][0]))
        return None
    m = re.match(r'Zone \[([^\]]+)\] on (\S+)', desc)
    if m:
        for P in g.pieces:
            z = P['zone']
            if CU_NAMES[z['layer']] == m.group(2) and len(P['nodes']) and any(abs(px - x) < 0.002 and abs(py - y) < 0.002 for px, py in z['outline']): return int(P['nodes'][0])
    return None


# ============================================================================================ report
def fmt_report(res, info):
    L = []; lim = res['limits']
    def pr(*x): L.append(' '.join(str(v) for v in x))
    pr('decoupling.py: %s' % info['board'])
    pr('  md5 %s, %d bytes; project files copied with it: %s' % (info['md5'], info['bytes'], ', '.join(info['project']) or 'NONE'))
    pr('  design %s (%s, md5 %s, modified %s); x\' = x - %g, h = %g - y' % (info['design'], info['design_file'], info['design_md5'], info['design_mtime'], info['XC'], info['H']))
    pr('  zones: %s; KiCad rule check: %s; outputs in %s' % (info['fill'], info['drc'] or 'not run (--no-drc)', info['out']))
    pr('  parts: %d RP2350B (%s), flashes %s, microSD %s, converters %s, Schottky %s' % (len(res['parts']['chips']), ' '.join(res['parts']['chips']),
       ' '.join(res['parts']['flashes']) or '-', ' '.join(res['parts']['sockets']) or '-', ' '.join(res['parts']['convs']) or '-', ' '.join(res['parts']['diodes']) or '-'))
    pr('')
    pr('SELF-CHECK')
    for ok, text in res['checks']: pr('  %-6s %s' % ('ok' if ok else 'FAILED', text))
    if res['notes']: pr('  notes: ' + '; '.join(res['notes']))
    pr('')
    pr('COPPER OF THE CHECKED NETS (tracks per layer: count / mm; vias)')
    for n in res['nets']:
        c = res['counts'].get(n, {})
        pr('  %-9s %s; vias %d' % (n, ', '.join('%s %d / %.1f' % (l.replace('.Cu', ''), k, m) for l, (k, m) in c.items()) or 'no tracks', res['vias_per_net'].get(n, 0)))
    pr('')
    pr('Thresholds: loop over %.1f mm of track or %d vias; marginal within %.1f mm of the limit; contacts under %.2f mm; trunk %.2f mm.' % (lim['mm'], lim['vias'], lim['margin'], lim['neck'], lim['trunk']))
    pr('Path text: layer mm/wN (N = narrowest width on that run), via(x\',h)F>B, [zone mm] = crossed in a straight line.')

    pr('')
    pr('=' * 120)
    pr('Q1  POWER PINS: OPEN, OR JOINED ONLY THROUGH CONTACTS NARROWER THAN %.2f mm' % lim['neck'])
    P = res['pins']
    kinds = Counter(r['kind'] for r in P)
    pr('  %d pins checked (%s)' % (len(P), ', '.join('%s %d' % kv for kv in sorted(kinds.items()))))
    bad = [r for r in P if r.get('status', '').startswith(('OPEN', 'WEAK', 'pad not found', 'net '))]
    for r in bad: pr('  %s.%s %s (%s): %s' % (r['ref'], r['pin'], r['name'], r['net'], r['status']))
    if not bad: pr('  none: every power pin touches copper of its net with a contact of at least %.2f mm' % lim['neck'])
    op = [r for r in P if r['kind'] == 'open']
    if op: pr('  %s: %s' % (', '.join(sorted({r['name'] for r in op})), '; '.join('%s.%s %s' % (r['ref'], r['pin'], r['status']) for r in op[:3]) + ('; ... (%d pins)' % len(op) if len(op) > 3 else '')))
    sup = [r for r in P if r['kind'] in ('supply', 'conv') and 'widest_contact' in r]
    if sup:
        w = min(sup, key=lambda r: r['widest_contact'])
        pr('  narrowest "widest contact" of a supply or converter pin: %s.%s %s %.3f mm; pins with a narrow contact besides a wide one: %s' % (
            w['ref'], w['pin'], w['name'], w['widest_contact'], ', '.join('%s.%s' % (r['ref'], r['pin']) for r in sup if r['narrow_contacts']) or 'none'))
    nc = res['narrow_contacts']
    def cls(c): return 'sole' if c['detour'] is None else 'detour' if c['detour'] > 1.0 else 'bypassed'
    pr('  contacts narrower than %.2f mm on the checked nets (neck; detour = extra copper mm between the two items without this contact):' % lim['neck'])
    for grp in ('supply', 'GND'):
        cs = [c for c in nc if (c['net'] == 'GND') == (grp == 'GND')]
        k = Counter(cls(c) for c in cs)
        pr('    %s nets: %d (under 0.09 mm: %d); sole joint %d, detour over 1 mm %d, bypassed within 1 mm %d' % (grp, len(cs), sum(1 for c in cs if c['neck'] < 0.09),
           k['sole'], k['detour'], k['bypassed']))
    shown = [c for c in nc if c['net'] != 'GND' and (cls(c) != 'bypassed' or c['neck'] < 0.09 or c['used_by'])] + [c for c in nc if c['net'] == 'GND' and cls(c) != 'bypassed']
    for c in sorted(shown, key=lambda c: (cls(c) != 'sole', -(c['detour'] or 0), c['neck'])):
        pr('    %-7s %.3f mm at %s board (%.3f, %.3f): %s - %s; %s%s' % (c['net'], c['neck'], c['at'], c['board'][0], c['board'][1], c['items'][0], c['items'][1],
           'SOLE joint' if c['detour'] is None else 'detour %.2f mm' % c['detour'], ('; on ' + ', '.join(c['used_by'])) if c['used_by'] else ''))
    pr('    (not listed: supply contacts bypassed within 1 mm, at least 0.09 mm wide and on no reported path; GND contacts bypassed within 1 mm)')
    dep = ['%s.%s loop' % (r['ref'], r['pin']) for r in res['supply'] if 'neck-dependent' in r['flags']]
    dep += ['%s.%s plane' % (r['ref'], r['pin']) for r in res['supply'] if (r.get('plane') or {}).get('total') != (r.get('plane_robust') or {}).get('total')]
    dep += ['%s.%s +1V1' % (r['ref'], r['pin']) for r in (res['q3'] or {}).get('pins', []) if r['status'] == 'ok' and r['R_robust'] != r['R']]
    dep += [f['what'] for f in res['q5'] if f['status'] == 'ok' and f['R_robust'] != f['R']]
    pr('  pins whose loop, way into the plane, +1V1 path or feed changes without contacts under %.2f mm: %s' % (lim['neck'], ', '.join(dep) or 'none'))

    pr('')
    pr('=' * 120)
    pr('Q2  SUPPLY PINS: LOOP TO THE OWN CAPACITOR, WAY INTO THE PLANE')
    pr('  loop = pin -> its capacitor (planes crossed): track mm / vias, plane mm, narrowest; floor = straight line pin -> capacitor pad;')
    pr('  plane = pin -> first entry into an inner plane of its net (track mm / vias, narrowest); cap->plane the same from the capacitor.')
    pr('  flags: len / vias over the limit, floor (floor over %.1f mm), at-floor (over, but within %.1f mm of the floor), marginal, neck, neck-dependent.' % (lim['mm'], lim['margin']))
    rows = res['supply']; by = defaultdict(list)
    for r in rows: by[r['ref']].append(r)
    for u in list(dict.fromkeys(r['ref'] for r in rows)):
        pr('  %s' % u)
        pr('    %-4s %-11s %-5s | %-17s %11s %6s %6s %6s | %-24s | %-15s | %-15s | %s' % ('pin', 'name', 'net', 'own cap', 'loop', 'plane', 'narrow', 'floor', 'flags', 'pin->plane', 'cap->plane', 'nearest cap'))
        for r in by[u]:
            Lp = r.get('loop'); pl = r.get('plane'); cpl = r.get('cap_plane'); nr = r.get('nearest')
            pr('    %-4s %-11s %-5s | %-17s %11s %6s %6s %6s | %-24s | %-15s | %-15s | %s' % (
                r['pin'], r['name'], r['net'], ('%s %s %s' % (r['cap'], r['cap_value'], r['cap_side'])) if r['cap'] else '-', mv(Lp), ('%.2f' % Lp['plane']) if Lp else '-',
                w_(Lp['narrowest']) if Lp else '-', ('%.2f' % r['floor']) if 'floor' in r else '-', ','.join(r['flags']),
                ('%s w%s' % (mv(pl), w_(pl['narrowest']))) if pl else 'none', ('%s w%s' % (mv(cpl), w_(cpl['narrowest']))) if cpl else 'none',
                ('%s %s' % (nr['cap'], mv(nr))) if nr else '-'))
    over = [r for r in rows if 'len' in r['flags'] or 'vias' in r['flags']]
    floor = [r for r in rows if 'floor' in r['flags']]
    atf = [r for r in over if 'at-floor' in r['flags']]
    marg = [r for r in rows if 'marginal' in r['flags']]
    dep = [r for r in rows if 'neck-dependent' in r['flags']]
    pr('')
    pr('  %d supply pins with a loop; within the limits %d; over %d (len %d, vias %d); floor over the limit %d (of those over: %d at the floor); marginal %d; neck-dependent %d' % (
        sum(1 for r in rows if r.get('loop')), sum(1 for r in rows if r.get('loop') and not ({'len', 'vias'} & set(r['flags']))), len(over),
        sum(1 for r in rows if 'len' in r['flags']), sum(1 for r in rows if 'vias' in r['flags']), len(floor), len(atf), len(marg), len(dep)))
    pr('  over the limits, by chip (pin: loop track mm/vias, floor; path):')
    for u in by:
        o = [r for r in by[u] if r in over]
        if not o: continue
        pr('    %s: %d of %d' % (u, len(o), len(by[u])))
        for r in o: pr('      %-3s %-11s %s, floor %.2f%s  [%s]' % (r['pin'], r['name'], mv(r['loop']), r['floor'], ' (at the floor)' if 'at-floor' in r['flags'] else '', r['loop']['text']))
    pr('  floor over %.1f mm (no routing can bring the loop under the limit): %s' % (lim['mm'], ', '.join('%s.%s %.2f' % (r['ref'], r['pin'], r['floor']) for r in floor) or 'none'))
    pr('  marginal: %s' % (', '.join('%s.%s %.2f' % (r['ref'], r['pin'], r['loop']['track']) for r in marg) or 'none'))
    pr('  neck-dependent (loop changes without contacts under %.2f mm): %s' % (lim['neck'], ', '.join('%s.%s %s -> %s' % (r['ref'], r['pin'], mv(r['loop']), mv(r.get('loop_robust'))) for r in dep) or 'none'))
    pl_dep = [r for r in rows if (r.get('plane') or {}).get('total') != (r.get('plane_robust') or {}).get('total')]
    pr('  pin -> plane changes without contacts under %.2f mm: %s' % (lim['neck'], ', '.join('%s.%s %s -> %s' % (r['ref'], r['pin'], mv(r.get('plane')), mv(r.get('plane_robust'))) for r in pl_dep) or 'none'))

    q3 = res['q3']
    if q3:
        pr('')
        pr('=' * 120)
        pr('Q3  %s NETWORK: least-resistance path from the divider top %s to every DVDD pin' % (q3['net'], q3['sense']))
        pr('  track length by width (mm): %s' % ', '.join('%s: %.1f' % kv for kv in q3['widths'].items()))
        pr('  narrower than %.2f mm and more than 3 mm from every DVDD pin: %s' % (lim['trunk'], ', '.join('%s: %.2f mm' % kv for kv in q3['narrow_far_from_pins'].items()) or 'none'))
        pr('  %-7s %7s %4s %7s %7s %13s %11s %-24s %-20s %s' % ('pin', 'len', 'vias', 'mOhm', 'narrow', 'w/o necks', 'at pin/else', 'cut vias (x\',h)', 'narrow bridges w/len', 'to a >=%.2f mm track' % lim['trunk']))
        best = {}
        for r in q3['pins']:
            if r['status'] != 'ok': pr('  %s.%-4s %s' % (r['ref'], r['pin'], r['status'])); continue
            if r['ref'] not in best or r['R'] < best[r['ref']]['R']: best[r['ref']] = r
            pr('  %s.%-4s %7.1f %4d %7.1f %7s %13s %11s %-24s %-20s %s' % (r['ref'], r['pin'], r['length'], r['vias'], r['R'], w_(r['narrowest']),
               ('%.1f/%s' % (r['R_robust'], w_(r['narrowest_robust']))) if r['R_robust'] is not None else 'OPEN', '%.2f/%.2f' % (r['narrow_at_pin'], r['narrow_elsewhere']), ' '.join('(%.1f,%.1f)' % v for v in r['cut_vias']) or '-',
               ' '.join('%.2f/%.1f' % (b[0], b[1]) for b in r['narrow_bridges']) or '-', ('%s w%s [%s]' % (mv(r['trunk']), w_(r['trunk']['narrowest']), r['trunk']['text'])) if r['trunk'] else 'none'))
        pr('  (len = track mm; narrow = narrowest track or contact; w/o necks = mOhm / narrowest without contacts under %.2f mm; at pin/else = mm of track under %.2f mm' % (lim['neck'], lim['trunk']))
        pr('   from the pin to the first wider track / elsewhere; cut vias = vias every path from the divider to the pin passes; narrow bridges = such tracks under %.2f mm)' % lim['trunk'])
        pr('  per chip, the DVDD pin with the least resistance (compare power_drop.py, same start, same copper model):')
        for u, r in best.items(): pr('    %s: pin %s, %.1f mm, narrowest %s, %d vias, %.1f mOhm' % (u, r['pin'], r['length'], w_(r['narrowest']), r['vias'], r['R']))

    if res['q4']:
        pr('')
        pr('=' * 120)
        pr('Q4  CONVERTERS')
        for c in res['q4']:
            pr('  %s %s at %s: VIN %s, SW %s, FB %s, out %s via %s; input %s, output %s' % (c['ref'], c['value'], c['xy'], c['vin'], c['sw'], c['fb'], c['out'], c['inductor'],
               ', '.join(c['cin']) or 'NONE', ', '.join(c['cout']) or 'NONE'))
            if c['cin']:
                pr('    input loop: VIN pin -> %s %s [%s]; %s GND -> GND pin %s (tracks only %s) [%s]; straight-line floor %.2f mm' % (
                    c['cin'][0], mv(c.get('cin_vin'), 'total'), (c.get('cin_vin') or {}).get('text', '-'), c['cin'][0], mv(c.get('cin_gnd'), 'total'), mv(c.get('cin_gnd_tracks'), 'total'),
                    (c.get('cin_gnd') or {}).get('text', '-'), c['cin_floor']))
            pr('    EN -> VIN: %s [%s]' % (mv(c.get('en_vin'), 'total'), (c.get('en_vin') or {}).get('text', '-')))
            sw = c['sw']
            pr('    FB pin to SW pin (the package itself): %s mm; the distances below leave out the converter\'s own pins' % w_(c['fb_pin_to_sw_pin']))
            pr('    switch node: %.2f mm2 of copper (pads %.2f; per layer %s), %.2f mm of track (widths %s), %d vias' % (sw['area_total'], sw['pads_only'], sw['area'], sw['track_mm'], sw['widths'], sw['vias']))
            for f in c['fb_nets']:
                pr('    %-9s track %.2f mm on %s, %d vias, pads %s%s; to the switch node %s mm on a common layer, %s mm in plan view; to the inductor outline %s mm, %.2f mm of track over it' % (
                    f['net'], f['track_mm'], '/'.join(f['layers']) or '-', f['vias'], ' '.join(f['pads']), ('; from the FB pin: ' + ', '.join('%s %.2f' % kv for kv in f['from_fb_pin'].items())) if f['from_fb_pin'] else '',
                    w_(f['to_sw_same_layer']), w_(f['to_sw_any_layer']), w_(f['to_inductor_outline']), f['over_inductor_mm']))
            for o in c['cout_detail']:
                pr('    output %s %s %s: from %s %s; GND -> GND pin %s (tracks only %s), straight line %.2f [%s]' % (o['cap'], o['value'], o['side'], c['inductor'], mv(o['from_L'], 'total'),
                   mv(o['gnd'], 'total'), mv(o['gnd_tracks'], 'total'), o['gnd_floor'], (o['gnd'] or {}).get('text', '-')))

    pr('')
    pr('=' * 120)
    pr('Q5  FEEDS')
    fl = [r for r in rows if r['ref'] in res['parts']['flashes'] + res['parts']['sockets']]
    for r in fl:
        Lp = r.get('loop'); pl = r.get('plane')
        pr('  %-4s %s %s: own %s %s %s loop %s narrowest %s (floor %.2f) [%s]; pin -> plane %s narrowest %s [%s]' % (r['ref'], r['name'], r['net'], r['cap'], r['cap_value'], r['cap_side'],
           mv(Lp), w_(Lp['narrowest']) if Lp else '-', r.get('floor', 0.0), Lp['text'] if Lp else '-', mv(pl), w_(pl['narrowest']) if pl else '-', pl['text'] if pl else '-'))
    for f in res['q5']:
        if f['status'] != 'ok': pr('  %-6s %s: %s' % (f['net'], f['what'], f['status'])); continue
        pr('  %-6s %-24s %6.1f mm, %d vias, %5.1f mOhm, narrowest track %s, contact %s; narrowest at %s%s%s  [%s]' % (f['net'], f['what'], f['length'], f['vias'], f['R'],
           w_(f['narrow_track']), w_(f['narrow_contact']), f['narrow_at'],
           '' if f['R_robust'] == f['R'] else '; without contacts under %.2f mm: %s' % (lim['neck'], ('%.1f mOhm, narrowest %s' % (f['R_robust'], w_(f['narrowest_robust']))) if f['R_robust'] is not None else 'OPEN'),
           ('; %.2f mm under the design width %.2f' % (f['under_design_mm'], f['design_width'])) if f['design_width'] else '', f['text']))

    g = res['gnd']
    if g['caps']:
        pr('')
        pr('=' * 120)
        pr('GND SIDE: every decoupling capacitor\'s GND pad to the first inner GND plane (pours crossed), and the ring capacitors\' return to the exposed pad')
        caps = res['caps']; asg = res['assigned']
        cp = [(ref, v['plane']) for ref, v in g['caps'].items() if 'plane' in v]
        over = [(ref, s) for ref, s in cp if s['outer'] > lim['mm'] + 1e-9 or s['vias'] > lim['vias']]
        pr('  GND pad -> inner GND plane (outer = mm of track and pour crossed on F / B): %d capacitors; median %.2f mm; over %.1f mm or %d vias: %d; worst %s' % (
           len(cp), median([s['outer'] for _, s in cp]), lim['mm'], lim['vias'], len(over),
           ', '.join('%s %s [%s]' % (ref, mv(s, 'outer'), s['text']) for ref, s in sorted(over, key=lambda x: -x[1]['outer'])[:8]) or '-'))
        for u, ch in g['chips'].items():
            ring = sorted({v for k, v in asg.items() if k.split('.')[0] == u})
            ep = [(ref, g['caps'][ref]['ep']) for ref in ring if 'ep' in g['caps'].get(ref, {})]
            ex = [e for _, e in ep if e['excess'] is not None]
            pr('  %s: EP vias %d (%s, dia %s, drill %s, offsets %s, locked %s, other-net vias in the pad %d; design %s)' % (u, ch['n'], ch['nets'], ch['dia'], ch['drill'],
               sorted({o for xy in ch['offs'] for o in xy}), ch['locked'], ch['other_net_vias'], ch['expect']))
            if ex:
                worst = max(ep, key=lambda x: x[1]['excess'] if x[1]['excess'] is not None else -1)
                pr('      ring GND -> EP: %s mm (floor %s); excess over the floor median %.2f, max %.2f (%s %s [%s]); GND pad -> plane over the limit: %s' % (
                    '-'.join('%.2f' % v for v in (min(e['path']['total'] for e in ex), max(e['path']['total'] for e in ex))),
                    '-'.join('%.2f' % v for v in (min(e['floor'] for e in ex), max(e['floor'] for e in ex))), median([e['excess'] for e in ex]), worst[1]['excess'],
                    worst[0], mv(worst[1]['path'], 'total'), worst[1]['path']['text'], ', '.join('%s %s' % (ref, mv(g['caps'][ref]['plane'], 'outer')) for ref in ring if ref in dict(over)) or 'none'))
            pr('      pins 62 / 65 -> EP: %s' % ', '.join('%s %s' % (p, mv(s, 'total')) for p, s in sorted(ch['pins'].items())))
        if g['flash_pin4']:
            pr('  flash GND pin 4 -> inner GND plane (outer mm / vias): %s' % ', '.join('%s %s' % (u, mv(s, 'outer')) for u, s in g['flash_pin4'].items()))
    if res['ring_only_vias']:
        pr('  vias whose centre lies outside the zone they enter (ring only): %s' % ', '.join('%s %s %.0f %%' % (v['zone'], v['via'], 100 * v['arc_fraction']) for v in res['ring_only_vias']))
    pr('')
    pr('=' * 120)
    pr('SUMMARY')
    ok_rows = [r for r in rows if r.get('loop')]
    for title, sel in (('3.3 V pins', lambda r: r['net'] != (q3 or {}).get('net') and r['ref'] in res['parts']['chips']), ('DVDD pins', lambda r: r['net'] == (q3 or {}).get('net')),
                       ('flash / microSD', lambda r: r['ref'] not in res['parts']['chips'])):
        rs = [r for r in ok_rows if sel(r)]
        if not rs: continue
        tr = sorted(r['loop']['track'] for r in rs)
        pr('  %-15s %3d loops: within %d, over %d, floor over the limit %d; loop track mm median %.2f, max %.2f; vias max %d' % (title, len(rs),
           sum(1 for r in rs if not ({'len', 'vias'} & set(r['flags']))), sum(1 for r in rs if {'len', 'vias'} & set(r['flags'])), sum(1 for r in rs if 'floor' in r['flags']),
           median(tr), tr[-1], max(r['loop']['vias'] for r in rs)))
    pr('  open power pins %d; pins joined only through narrow contacts %d; narrow contacts that are a sole joint %d' % (
       sum(1 for r in P if r.get('status', '').startswith('OPEN')), sum(1 for r in P if r.get('status', '').startswith('WEAK')), sum(1 for c in nc if c['detour'] is None)))
    if q3: pr('  %s: worst DVDD path %s; tracks under %.2f mm away from the pins %s' % (q3['net'], max((('%s.%s %.1f mOhm' % (r['ref'], r['pin'], r['R']), r['R']) for r in q3['pins'] if r['status'] == 'ok'),
       key=lambda x: x[1])[0] if q3['pins'] else '-', lim['trunk'], q3['narrow_far_from_pins'] or 'none'))
    for c in res['q4']:
        pr('  %s: input loop VIN %s + GND %s mm (floor %.2f); FB track %.2f mm; output GND %s' % (c['ref'], mv(c.get('cin_vin'), 'total'), mv(c.get('cin_gnd'), 'total'),
           c.get('cin_floor', 0.0), c['fb_nets'][0]['track_mm'] if c['fb_nets'] else 0.0, ', '.join('%s %s' % (o['cap'], mv(o['gnd'], 'total')) for o in c['cout_detail'])))
    pr('')
    pr('files: decoupling.txt (this report), decoupling_pins.csv, decoupling.json%s; run time %.1f s' % (', drc.txt' if info['drc'] else '', info['seconds']))
    return '\n'.join(L) + '\n'


def write_csv(res, path):
    cols = ['ref', 'pin', 'name', 'net', 'contacts', 'widest_contact', 'own_cap', 'cap_value', 'cap_side', 'loop_track_mm', 'loop_plane_mm', 'loop_total_mm', 'loop_vias',
            'loop_narrowest', 'floor_mm', 'flags', 'plane_track_mm', 'plane_vias', 'plane_narrowest', 'cap_plane_track_mm', 'cap_plane_vias', 'nearest_cap',
            'nearest_total_mm', 'loop_tracks_only_mm', 'loop_path', 'plane_path']
    pins = {(r['ref'], r['pin']): r for r in res['pins']}
    with open(path, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(cols)
        for r in res['supply']:
            L = r.get('loop') or {}; P = r.get('plane') or {}; C = r.get('cap_plane') or {}; N = r.get('nearest') or {}; T = r.get('loop_tracks_only') or {}; p = pins[(r['ref'], r['pin'])]
            w.writerow([r['ref'], r['pin'], r['name'], r['net'], p.get('contacts'), p.get('widest_contact'), r['cap'], r['cap_value'], r['cap_side'], L.get('track'), L.get('plane'),
                        L.get('total'), L.get('vias'), L.get('narrowest'), r.get('floor'), ' '.join(r['flags']), P.get('track'), P.get('vias'), P.get('narrowest'),
                        C.get('track'), C.get('vias'), N.get('cap'), N.get('total'), T.get('total'), L.get('text'), P.get('text')])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        child(sys.argv[2], sys.argv[3], None if sys.argv[4] == '-' else sys.argv[4], sys.argv[5], sys.argv[6] == '1')
        return 0
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog='The module docstring has method, assumptions and limits.')
    ap.add_argument('board')
    ap.add_argument('--design', default=os.environ.get('FC_DESIGN', 'design_revh'), help='design module in the tools folder (default: FC_DESIGN or design_revh)')
    ap.add_argument('--out', help='folder for everything the tool writes (default: a fresh temporary folder)')
    ap.add_argument('--stored-fill', action='store_true', help='analyse the zone fill stored in the board file instead of a fresh fill')
    ap.add_argument('--no-drc', action='store_true', help="skip KiCad's rule check of the copy")
    ap.add_argument('--limit-mm', type=float, default=3.0, help='loop track length limit, mm (default 3.0)')
    ap.add_argument('--limit-vias', type=int, default=2, help='loop via limit (default 2)')
    ap.add_argument('--margin', type=float, default=0.3, help='"marginal" and "at the floor" band, mm (default 0.3)')
    ap.add_argument('--neck', type=float, default=0.12, help='contacts narrower than this are reported, mm (default 0.12)')
    ap.add_argument('--trunk', type=float, default=0.3, help='track width that counts as the DVDD supply trunk, mm (default 0.3)')
    a = ap.parse_args()
    t0 = time.time()
    out_dir = os.path.abspath(a.out) if a.out else tempfile.mkdtemp(prefix='decoupling_')
    os.makedirs(out_dir, exist_ok=True)
    sys.path.insert(0, TOOLS)
    D = importlib.import_module(a.design)
    XC, H = D.at(0.0, 0.0)
    src = os.path.abspath(a.board)
    board, project = stage(src, os.path.join(out_dir, 'board'))
    drc = None if a.no_drc else os.path.join(out_dir, 'drc.txt')
    filled = os.path.join(out_dir, 'board', 'board_filled.kicad_pcb')
    js = os.path.join(out_dir, 'board', 'fill.json')
    r = subprocess.run([sys.executable, '-B', os.path.abspath(__file__), '--child', board, filled, drc or '-', js, '0' if a.stored_fill else '1'], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(filled): raise SystemExit('fill / rule check child failed:\n' + r.stdout + r.stderr)
    fillrec = json.load(open(js))
    dfile = os.path.abspath(D.__file__)
    info = dict(board=src, md5=md5_of(src), bytes=os.path.getsize(src), project=project, design=a.design, design_file=dfile, design_md5=md5_of(dfile),
                design_mtime=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(os.path.getmtime(dfile))), XC=XC, H=H, out=out_dir,
                fill='stored fill (--stored-fill)' if a.stored_fill else 'refilled by KiCad on the copy', drc=drc)
    res = analyse(filled, D, a, drc, fillrec)
    info['seconds'] = time.time() - t0
    res['info'] = info
    text = fmt_report(res, info)
    with open(os.path.join(out_dir, 'decoupling.txt'), 'w') as f: f.write(text)
    write_csv(res, os.path.join(out_dir, 'decoupling_pins.csv'))
    def plain(o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, (set, tuple)): return list(o)
        return str(o)
    with open(os.path.join(out_dir, 'decoupling.json'), 'w') as f: json.dump(res, f, indent=1, default=plain)
    sys.stdout.write(text)
    return 0 if all(ok for ok, _ in res['checks']) else 2


if __name__ == '__main__':
    code = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)                                         # pcbnew's objects are not torn down (it prints leak notes when they are)
