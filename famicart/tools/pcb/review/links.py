#!/usr/bin/env python3
"""Chip-to-chip links of a routed famicart board (rev H on): routed length, skew, layers, vias, reference planes, stubs,
the load each driver charges and the clock rate each link supports; also QSPI, USB, microSD, SWD and the long static
lines nRST / VSEL_S.

What it checks and why
  docs/13_rev_h_plan.md "チップ間の接続" defines the links between the eight RP2350B: WLINK (U1 -> U2, U5, hub; clock +
  2 data, 25 MHz, 40 MHz only with every end at 240 MHz), XLINK-H1 / -H2 / -14 / -25 (40 MHz option likewise) and
  -48 / -59 / -89 (25 MHz), one clock + 2 data per direction; SWD from the hub to the seven other chips (bit-banged, a
  few MHz); LINK / PLINK (single wires through 250 / 500 ohm). Each chip has a W25Q128 on QSPI CS0, the hub a second one
  (U7) on CS1 of the same bus; the hub also has the USB-C (27 ohm near pins 66 / 67) and the microSD (SPI0 at 25 MHz, or
  4-bit through PIO). Links drive 4 mA with slow slew by default (docs/13), so on long or multi-drop nets the driver
  charging the net capacitance, not the flight time, sets how fast a link can run. docs/13 also wants WLINK, XLINK, SWD
  and USB on F.Cu / B.Cu next to a GND plane ("配線の決まり"), estimates XLINK-48 / -59 at about 10-20 mm and XLINK-89
  at about 75 mm, and puts the 27 ohm resistors within about 3 mm of the hub's USB pins.

Method
  * Nets, drivers and receivers from the design module (xl(), WL, the pin tables G, NETS, PARTS, ROLE); the copper
    from the board. Every pad of every analysed net is checked against the design netlist.
  * A copper graph per wire: tracks split at T-junctions and where they pass a via or a pad, ends joined within half
    a track width, vias joining the layers they span, pads by KiCad's own hit test, series resistor elements as
    bridges (LINK, PLINK, USB). Dijkstra gives each receiver's path from the driver pad centre; copper that several
    receivers share is reported by the exact set of receivers that use it, copper on no path as stubs (test pads,
    pull-ups, the other flash). An unrouted wire is closed by a minimum spanning tree of straight lines (the ratsnest);
    its length is then a ratsnest estimate and only the straight driver-receiver distance is a lower bound.
  * Delay, impedance and capacitance per (layer, width) from a 2-D field solution of the board's own stack-up block
    (xsection.py): F.Cu / B.Cu microstrip over In1 / In4 GND under solder mask, In3 asymmetric stripline between In2
    (+3V3) and In4 (GND); coupled pairs for the USB pair and for crosstalk. Vias: barrel + Z0 C_via / 2 for the delay,
    Johnson's C_via for the load.
  * Load of a net: trace C (solver C per mm x all copper of the net) + vias + IC pins + other pads (parallel plate
    over the next plane x 1.25) + the microSD card's input. Driver: a linear resistor from the RP2350's VOH / VOL limits
    at the drive current (worst) or rev G's 40 ohm at 8 mA scaled by 1 / I (typ). Threshold crossings at a receiver:
    latest = flight + max(R_hi C ln(V / (V - VIH)), R_lo C ln(V / VIL)); earliest = flight + min(R_hi C ln(V / (V -
    VIL)), R_lo C ln(V / VIH)), with the same driver corner (clock and data come from one die and one drive setting).
  * Link budget (source-synchronous, PIO): data changes on one clock edge and is sampled after the receiver sees the
    other edge through its 2-flop input synchroniser, the `in` one cycle after the `wait`: the data pin is sampled 1 to
    2 receiver clocks (t_sys) after the clock crossing. Hold: T/2 >= t_late(CK) + 2 t_sys - t_early(D); set-up:
    T/2 >= t_late(D) - t_early(CK) - t_sys. A rate is supported when T/2 exceeds both by the guard;
    f_max = 1 / (2 (need + guard)); "PIO" = the highest f_sys / N (N even) that keeps the guard.
  * QSPI: the QMI launches SCLK and samples the data itself (pico-sdk default CLKDIV 2, RXDELAY 2), so the board's
    share is compared with a Pico-2-like reference net (10 mm on F.Cu, one flash, no via): the excess round trip (SCLK
    there + data back, flight and RC).
  * microSD: SPI-mode read set-up at the hub pin (card output delay tODLY after the falling edge it sees, back by the
    next rising edge), the 4-bit read window, and the card's input set-up / hold for writes, at 25 MHz.
  * SWD: lengths, stubs to the J6 / J5 pads, read round trip (RC + flight both ways) against a few-MHz half period.
  * Reference planes: the stored zone fills of In1 / In2 / In4 rasterised at 0.025 mm; every track of the analysed
    nets sampled every 0.05 mm against the plane(s) next to its layer (voids: via antipads and plane edges); "none" =
    no plane on either side. The stored fills are compared with a refill (child process).
  * Parallel runs: every same-layer segment of another net within 0.5 mm (edge to edge) and 5 deg of parallel to a
    victim segment; mutual capacitance per mm from the solver at that spacing. Bound for a victim held only by a pull
    resistor (charge sharing, every aggressor switching 3.3 V the same way): dV <= 3.3 V x sum(Cm L) / C(victim).

Assumptions (source in brackets; "assumed" = no measured value behind it)
  RP2350 VOH >= 2.62 V and VOL <= 0.5 V at the selected drive current, IOVDD 3.3 V [datasheet Table 1683, as quoted in
  the rev H reviews]; VIH 2.0 V [docs/13]; VIL 0.8 V [assumed, same table]; typ driver 40 ohm at 8 mA [rev G review,
  docs/12], scaled by 1 / I [assumed]; link drive 4 mA [docs/13]; slew-rate limiter not modelled, i.e. fast slew
  [assumed]; RP2350 pin 4 pF typ / 6 pF max [assumed, the datasheet gives none; as review/timing.py]; W25Q128JV pin
  6 pF (CS, CLK) / 8 pF (IO) [assumed from the Winbond capacitance table, not re-checked]; flash output 50 ohm
  [assumed]; QSPI SCLK 8 mA, fast slew, CLKDIV 2, RXDELAY 2 [pico-sdk 2.3.1 src/rp2350/boot_stage2/boot2_w25q080.S];
  Pico-2-like reference net 10 mm [assumed]; microSD card 10 pF per line, default-speed tODLY 14 ns, tISU / tIH 5 ns
  [assumed from the SD physical layer specification, not re-checked]; solder mask er 3.8, 10 um [assumed: the
  stack-up block gives no er]; pad fringe factor 1.25 [assumed]; PIO receiver program as in Method [assumed: docs/13
  has no link PIO yet]; guard 1 ns [assumed: slew limiter, threshold spread, ringing, crosstalk].

Limits
  Lumped RC with linear drivers (no IBIS / SPICE, no reflections or ringing; on these nets the RC time is several times
  the flight time); the worst-case linear driver is pessimistic at the start of an edge, and slow slew would add an
  unknown intrinsic edge. 2-D cross-sections (no 3-D fringe at bends, pads or via stubs); the via model is an
  approximation. The crosstalk bound ignores copper in between and assumes the worst (floating victim, all aggressors
  together); a driven line sees less. The QMI's and the SPI block's internal sampling points are not modelled
  (relative check for QSPI, pin-level slack for SPI). Open wires: estimates only.

Usage (any working folder; the design module comes from the tools folder, the parent of this script's folder)
    python3 tools/pcb/review/links.py --board B.kicad_pcb [--design design_revh] [--out DIR]
        [--calib-board revg.kicad_pcb] [--no-drc] [--fine]
    python3 tools/pcb/review/links.py --selftest            (field solver against closed forms only)
  --design defaults to $FC_DESIGN, then design_revh. --out defaults to a new temporary folder; nothing is written
  anywhere else: every board is copied there (with its .kicad_pro) before pcbnew opens it, and KiCad's rule check (with
  a zone refill) runs on that copy in a child process. Outputs: links_report.txt, links.json, drc_links.txt,
  refill_areas.json and the board copies. --calib-board: the rev G board; the path engine must reproduce docs/12's
  routed feed VSYS_D (128 mm). --fine: a finer solver grid (convergence check; several minutes, because every coupled
  pair of the crosstalk scan is solved again). Exit code 1 when a self-check fails.

Healthy result
  "SELF-CHECKS: all pass" (stack-up = gen_pcb, board pads = design netlist, copper sums = KiCad's track lengths, open
  counts = KiCad's, multi-drop copper conserved, loop-free paths = breadth-first search, solver within 1.5 % of the
  closed forms, stored fills = refilled, rev G VSYS_D = 128 mm); no open wire and no KiCad error; every link with
  slack >= the guard at its docs/13 rate and the drive the firmware uses; QSPI excess round trip well under 1 ns; no
  long track over a plane void; crosstalk bounds on nRST / VSEL_S far below their noise margins. FLAGS lists the rest."""
import os
import sys
sys.dont_write_bytecode = True            # set before xsection and the design module are imported: no __pycache__
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_v, '1')         # the solver's small dense blocks: threaded BLAS only adds contention
import re, ast, math, json, time, heapq, shutil, hashlib, argparse, tempfile, importlib, subprocess, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)                                   # famicart/tools/pcb: design modules, gen_pcb.py
sys.path.insert(0, HERE)
import xsection as XS

LNAME = {0: 'F.Cu', 1: 'In1.Cu', 2: 'In2.Cu', 3: 'In3.Cu', 4: 'In4.Cu', 31: 'B.Cu'}
LID = {v: k for k, v in LNAME.items()}
NM = 1e-6                                                       # KiCad internal unit (nm) -> mm
EPS0_PF_MM = 8.8541878128e-3
LEN_LIMIT_MM = 100.0
FAST_KINDS = ('WLINK', 'XLINK', 'SWD', 'USB')                   # docs/13: on F.Cu / B.Cu next to a GND plane
# docs/13 length estimates (mm) by XLINK name: "U8 は U4 の下、U9 は U5 の下にあり、XLINK は約 10〜20 mm" (基板, 配置の案);
# "U8⇔U9 は基板を横切る約 75 mm の線" (チップ間の接続). The other links have no estimate.
DOC13_EST = {'48': (10.0, 20.0), '59': (10.0, 20.0), '89': (None, 75.0)}
USB_R_MAX_MM = 3.0                                              # docs/13: 27 ohm within about 3 mm of pins 66 / 67

A = dict(                                                       # assumptions; see the module docstring for sources
    iovdd=3.3, vih=2.0, vil=0.8, voh_drop=0.68, vol=0.5, r_typ_8ma=40.0,
    c_pin_rp=(4.0, 6.0), c_flash_in=6.0, c_flash_io=8.0, c_card=10.0, pad_fringe=1.25, mask_er=3.8,
    link_ma=4, qspi_sclk_ma=8, r_flash=50.0, ref_len=10.0,
    sd_todly=14.0, sd_tisu=5.0, sd_tih=5.0, guard=1.0)
DRIVES = (('4 mA worst', 4, 'worst'), ('4 mA typ', 4, 'typ'), ('8 mA worst', 8, 'worst'), ('12 mA worst', 12, 'worst'))
K_RISE = math.log(A['iovdd'] / (A['iovdd'] - A['vih']))         # 0.93: rising edge to VIH
K_FALL = math.log(A['iovdd'] / A['vil'])                        # 1.42: falling edge to VIL
K_RISE_EARLY = math.log(A['iovdd'] / (A['iovdd'] - A['vil']))   # 0.28: the earliest a rising edge can cross a threshold
K_FALL_EARLY = math.log(A['iovdd'] / A['vih'])                  # 0.50: the earliest a falling edge can cross a threshold


def driver_r(mA, corner):
    """(R high side, R low side) of an RP2350 output at the drive current, ohm."""
    if corner == 'worst':
        return A['voh_drop'] / (mA * 1e-3), A['vol'] / (mA * 1e-3)
    r = A['r_typ_8ma'] * 8.0 / mA
    return r, r


def t_rc(c_pf, mA, corner):
    """Latest threshold crossing of a lumped RC (ns): the slower of rising to VIH and falling to VIL."""
    rh, rl = driver_r(mA, corner)
    return max(K_RISE * rh, K_FALL * rl) * c_pf * 1e-3


def t_rc_early(c_pf, mA, corner):
    """Earliest threshold crossing (ns) with the same driver: rising to VIL or falling to VIH, whichever is sooner."""
    rh, rl = driver_r(mA, corner)
    return min(K_RISE_EARLY * rh, K_FALL_EARLY * rl) * c_pf * 1e-3


# ----------------------------------------------------------------------------------------------- stack-up and models
def stackup_from_board(text):
    """The (stackup ...) block of the board file: [{name, type, t, material, er}] top to bottom."""
    i = text.find('(stackup')
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == '(':
            depth += 1
        elif text[j] == ')':
            depth -= 1
            if depth == 0:
                break
    out = []
    for m in re.finditer(r'\(layer "([^"]+)"((?:\s*\((?:[^()"]|"[^"]*")*\))*)\s*\)', text[i:j + 1]):
        a = {k: (v1 or v2) for k, v1, v2 in re.findall(r'\((\w+) (?:"([^"]*)"|([^()\s"]+))\)', m.group(2))}
        out.append(dict(name=m.group(1), type=a.get('type'), t=float(a['thickness']) if 'thickness' in a else None,
                        material=a.get('material'), er=float(a['epsilon_r']) if 'epsilon_r' in a else None))
    return out


def gen_pcb_stackup(name):
    """gen_pcb.py's STACKUPS[name], read from its source (no import, no side effects)."""
    src = open(os.path.join(TOOLS, 'gen_pcb.py')).read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'STACKUPS' for t in node.targets):
            return ast.literal_eval(node.value).get(name)
    return None


class Stack:
    """Physical stack from the board's stack-up block: copper and dielectric layers, z of each copper layer's middle."""
    def __init__(s, layers, plane_layers):
        s.mask = {l['name']: l for l in layers if (l['type'] or '').endswith('Solder Mask')}
        s.body = [l for l in layers if l['type'] in ('copper', 'core', 'prepreg')]
        z, s.z = 0.0, {}
        for l in s.body:
            if l['type'] == 'copper':
                s.z[l['name']] = z + l['t'] / 2
            z += l['t']
        s.thickness = z
        s.planes = set(plane_layers)
        diel = [l for l in s.body if l['type'] != 'copper']
        s.er_avg = sum(l['t'] * l['er'] for l in diel) / sum(l['t'] for l in diel)

    def neighbours(s, name):
        """(dielectrics between `name` and the next plane above, plane name or None) and the same below."""
        k = next(i for i, l in enumerate(s.body) if l['name'] == name)
        def walk(step):
            d, i = [], k + step
            while 0 <= i < len(s.body):
                l = s.body[i]
                if l['type'] == 'copper':
                    if l['name'] in s.planes:
                        return d, l['name']
                    d.append(dict(t=l['t'], er=None, copper=l['name']))
                else:
                    d.append(dict(t=l['t'], er=l['er'], type=l['type'], copper=None))
                i += step
            return d, None
        return walk(-1), walk(+1)

    def ref_planes(s, name):
        (_, pu), (_, pd) = s.neighbours(name)
        return [p for p in (pu, pd) if p]

    def outer_dielectric(s, name):
        """(thickness, er) between an outer copper layer and its plane (pads over the plane)."""
        (up, pu), (dn, pd) = s.neighbours(name)
        d = dn if pd else up
        return d[0]['t'], d[0]['er']


class Models:
    """Field-solver results per (copper layer, track width): t_pd, Z0, C per mm; coupled-pair tables; vias."""
    def __init__(s, stack, res, cpw_gap=None):
        s.st, s.res, s.cpw_gap, s.cache, s.pairs = stack, res, cpw_gap, {}, {}
        s.cu_t = {l['name']: l['t'] for l in stack.body if l['type'] == 'copper'}

    def _geom(s, layer):
        (up, pu), (dn, pd) = s.st.neighbours(layer)
        if pu and pd:
            assert len(up) == 1 and len(dn) == 1, 'one dielectric on each side expected'
            a, b = up[0], dn[0]
            below, above = (b, a) if (b.get('type') == 'core' or a.get('type') != 'core') else (a, b)
            return 'stripline', (pu, pd), below, above
        d, plane = (dn, pd) if pd else (up, pu)
        assert len(d) == 1, 'one dielectric to the plane expected'
        return 'microstrip', (plane,), d[0], None

    def mask_t(s, layer):
        mk = s.st.mask.get(('F' if layer == 'F.Cu' else 'B') + '.Mask')
        return mk['t'] if mk and mk['t'] else 0.0

    def model(s, layer, w, variants=False):
        key = (layer, round(w, 4), variants)
        if key in s.cache:
            return s.cache[key]
        kind, planes, d1, d2 = s._geom(layer)
        t = s.cu_t[layer]
        v = {}
        if kind == 'stripline':
            m = XS.stripline(w, t, d1['t'], d1['er'], d2['t'], d2['er'], res=s.res)
            if variants:
                v['prepreg thickness includes the copper'] = XS.stripline(w, t, d1['t'], d1['er'], d2['t'], d2['er'], embed='base', res=s.res)['tpd_ps_mm']
                for e in sorted({d1['er'], d2['er']}):
                    v['bound: all er %.2f' % e] = math.sqrt(e) / XS.C_MM_PER_NS * 1e3
            r = dict(kind=kind, planes=planes, **m)
        else:
            tm = s.mask_t(layer)
            m = XS.microstrip(w, t, d1['t'], d1['er'], mask_t=tm, mask_er=A['mask_er'], res=s.res)
            if variants:
                v['no solder mask'] = XS.microstrip(w, t, d1['t'], d1['er'], res=s.res)['tpd_ps_mm']
                v['mask er 3.3'] = XS.microstrip(w, t, d1['t'], d1['er'], mask_t=tm, mask_er=3.3, res=s.res)['tpd_ps_mm']
                v['Hammerstad-Jensen, no mask'] = XS.hammerstad_jensen(w, d1['t'], t, d1['er'])['tpd_ps_mm']
                if s.cpw_gap:
                    v['GND pour %.2f mm beside it' % s.cpw_gap] = XS.microstrip(w, t, d1['t'], d1['er'], mask_t=tm, mask_er=A['mask_er'],
                                                                               cpw_gap=s.cpw_gap, res=s.res)['tpd_ps_mm']
            r = dict(kind=kind, planes=planes, **m)
        r['variants'] = v
        s.cache[key] = r
        return r

    def tpd(s, layer, w):
        return s.model(layer, w)['tpd_ps_mm']

    def cpm(s, layer, w):
        return s.model(layer, w)['c_pf_mm']

    def pair(s, layer, w, sp):
        key = (layer, round(w, 4), round(sp, 4))
        if key not in s.pairs:
            kind, planes, d1, d2 = s._geom(layer)
            t = s.cu_t[layer]
            if kind == 'stripline':
                s.pairs[key] = XS.stripline_pair(w, sp, t, d1['t'], d1['er'], d2['t'], d2['er'], res=s.res)
            else:
                s.pairs[key] = XS.microstrip_pair(w, sp, t, d1['t'], d1['er'], mask_t=s.mask_t(layer), mask_er=A['mask_er'], res=s.res)
        return s.pairs[key]

    def via_c_pf(s):
        """Johnson's estimate C = 1.41 er T D1 / (D2 - D1) pF (inches): pad 0.5 mm, antipad 1.0 mm, T the stack."""
        D1, D2, T = 0.5 / 25.4, 1.0 / 25.4, s.st.thickness / 25.4
        return 1.41 * s.st.er_avg * T * D1 / (D2 - D1)

    def via_ps(s, la, lb, z0=50.0):
        """Via from la to lb: barrel |dz| at sqrt(er_avg) / c plus Z0 C_via / 2 (both approximations)."""
        barrel = abs(s.st.z[la] - s.st.z[lb]) * math.sqrt(s.st.er_avg) / XS.C_MM_PER_NS * 1e3
        lump = z0 * s.via_c_pf() / 2.0
        return barrel + lump, barrel, lump


# ----------------------------------------------------------------------------------------------- board -> plain data
def board_copy(path, out, tag):
    d = os.path.join(out, tag)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(path))
    shutil.copy2(path, dst)
    pro = os.path.splitext(path)[0] + '.kicad_pro'
    if os.path.exists(pro):
        shutil.copy2(pro, os.path.join(d, os.path.basename(pro)))
    return dst


def md5_of(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def _arc(p0, pm, p1):
    ax, ay, bx, by, cx_, cy_ = p0.x, p0.y, pm.x, pm.y, p1.x, p1.y
    d = 2 * (ax * (by - cy_) + bx * (cy_ - ay) + cx_ * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy_) + (bx * bx + by * by) * (cy_ - ay) + (cx_ * cx_ + cy_ * cy_) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx_ - bx) + (bx * bx + by * by) * (ax - cx_) + (cx_ * cx_ + cy_ * cy_) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(y - uy, x - ux) for x, y in ((ax, ay), (bx, by), (cx_, cy_)))
    sweep = (a1 - a0) % (2 * math.pi)
    if (am - a0) % (2 * math.pi) > sweep:
        sweep -= 2 * math.pi
    return ux, uy, r, a0, sweep


def read_board(pcbnew, b):
    """Plain data of every net: segments (nm, layer id, width nm), vias, pads (with the PAD object for hit tests and the
    pad's area), KiCad's own track length per net."""
    segs, vias, pads = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    kicad_len = collections.Counter()
    for t in b.GetTracks():
        n = t.GetNetname()
        cls = t.GetClass()
        if cls == 'PCB_VIA':
            v = t if hasattr(t, 'TopLayer') else pcbnew.Cast_to_PCB_VIA(t)
            p = t.GetPosition()
            vias[n].append(dict(x=p.x, y=p.y, r=t.GetWidth() / 2.0, top=v.TopLayer(), bot=v.BottomLayer()))
        elif cls == 'PCB_ARC':                       # a polyline of 16 pieces keeps the length within 0.1 %
            a = t if hasattr(t, 'GetMid') else pcbnew.Cast_to_PCB_ARC(t)
            cx, cy, r, a0, sweep = _arc(a.GetStart(), a.GetMid(), a.GetEnd())
            pts = [(cx + r * math.cos(a0 + sweep * k / 16), cy + r * math.sin(a0 + sweep * k / 16)) for k in range(17)]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                segs[n].append((x0, y0, x1, y1, t.GetLayer(), t.GetWidth()))
            kicad_len[n] += t.GetLength() * NM
        else:
            s0, s1 = t.GetStart(), t.GetEnd()
            segs[n].append((s0.x, s0.y, s1.x, s1.y, t.GetLayer(), t.GetWidth()))
            kicad_len[n] += t.GetLength() * NM
    for f in b.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            n = p.GetNetname()
            if not n:
                continue
            q, sz = p.GetPosition(), p.GetSize()
            sx, sy = sz.x * NM, sz.y * NM
            area = math.pi / 4 * sx * sy if p.GetShape() in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL) else 0.95 * sx * sy
            pads[n].append(dict(ref=ref, num=p.GetNumber(), x=q.x, y=q.y, layers=[l for l in LNAME if p.IsOnLayer(l)], obj=p,
                                area=area))
    return segs, vias, pads, kicad_len


def plane_fills(pcbnew, b, layers):
    """Filled polygons of the zones on `layers`: {layer name: [(+1 outline / -1 hole, [(x, y) mm])]}, and their nets."""
    out, nets = collections.defaultdict(list), collections.defaultdict(set)
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for l in z.GetLayerSet().Seq():
            ln = LNAME.get(l)
            if ln not in layers:
                continue
            ps = z.GetFilledPolysList(l)
            for i in range(ps.OutlineCount()):
                for sign, ch in [(1, ps.Outline(i))] + [(-1, ps.Hole(i, h)) for h in range(ps.HoleCount(i))]:
                    out[ln].append((sign, [(ch.CPoint(k).x * NM, ch.CPoint(k).y * NM) for k in range(ch.PointCount())]))
            nets[ln].add(z.GetNetname())
    return out, nets


def contour_area(contours):
    """Area (mm^2) of filled polygons: outlines minus holes."""
    tot = 0.0
    for sign, c in contours:
        p = np.asarray(c)
        if len(p) >= 3:
            tot += sign * abs(0.5 * (np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1))))
    return tot


class PlaneMap:
    """Plane presence rasters (even-odd scanline fill of pixel centres) of the plane layers' filled zones."""
    def __init__(s, fills, box, r=0.025):
        s.r = r
        s.x0, s.y0 = box[0] - 0.5, box[1] - 0.5
        s.nx, s.ny = int((box[2] - box[0] + 1.0) / r) + 1, int((box[3] - box[1] + 1.0) / r) + 1
        s.map = {}
        for ln, cs in fills.items():
            R = np.zeros((s.ny, s.nx), dtype=bool)
            s._poly(R, cs)
            s.map[ln] = R

    def _poly(s, R, contours):
        E = []
        for _, c in contours:
            if len(c) < 3:
                continue
            p = np.asarray(c, dtype=float)
            E.append(np.hstack([p, np.roll(p, -1, axis=0)]))
        if not E:
            return
        E = np.vstack(E)
        E = E[E[:, 1] != E[:, 3]]
        ylo = np.minimum(E[:, 1], E[:, 3]); yhi = np.maximum(E[:, 1], E[:, 3])
        order = np.argsort(ylo); E, ylo, yhi = E[order], ylo[order], yhi[order]
        j0 = max(0, int(math.floor((ylo.min() - s.y0) / s.r - 0.5)))
        j1 = min(s.ny - 1, int(math.ceil((yhi.max() - s.y0) / s.r)))
        for j in range(j0, j1 + 1):
            yc = s.y0 + (j + 0.5) * s.r
            k = np.searchsorted(ylo, yc, side='right')
            if k == 0:
                continue
            m = yhi[:k] > yc
            if not m.any():
                continue
            e = E[:k][m]
            xs = np.sort(e[:, 0] + (yc - e[:, 1]) * (e[:, 2] - e[:, 0]) / (e[:, 3] - e[:, 1]))
            for a, bq in zip(xs[0::2], xs[1::2]):
                i0 = max(0, int(math.ceil((a - s.x0) / s.r - 0.5))); i1 = min(s.nx - 1, int(math.floor((bq - s.x0) / s.r - 0.5)))
                if i1 >= i0:
                    R[j, i0:i1 + 1] ^= True

    def present(s, ln, x, y):
        i = np.clip(((np.asarray(x) - s.x0) / s.r).astype(int), 0, s.nx - 1)
        j = np.clip(((np.asarray(y) - s.y0) / s.r).astype(int), 0, s.ny - 1)
        return s.map[ln][j, i]


def plane_voids(segs_of_net, stack, planes, ds=0.05):
    """Track length (mm) of one net over a void of each plane next to its layer, and with no plane at all next to it
    ('none': for In3 both In2 and In4 missing); the longest run of each (where)."""
    miss, run_best = collections.Counter(), {}
    for (x0, y0, x1, y1, L, w) in segs_of_net:
        ln = LNAME[L]
        if ln not in ('F.Cu', 'B.Cu', 'In3.Cu'):
            continue
        a = np.array([x0, y0]) * NM; b_ = np.array([x1, y1]) * NM
        Ls = float(np.hypot(*(b_ - a)))
        if Ls <= 0:
            continue
        n = max(1, int(math.ceil(Ls / ds)))
        t = (np.arange(n) + 0.5) / n
        px, py = a[0] + t * (b_[0] - a[0]), a[1] + t * (b_[1] - a[1])
        refs = [pl for pl in stack.ref_planes(ln) if pl in planes.map]
        missing = {pl: ~planes.present(pl, px, py) for pl in refs}
        if refs:
            missing['none'] = np.logical_and.reduce([missing[pl] for pl in refs])
        for pl, gone in missing.items():
            if not gone.any():
                continue
            miss[pl] += gone.sum() * Ls / n
            # longest contiguous run of missing samples on this segment
            idx = np.flatnonzero(np.diff(np.concatenate([[0], gone.astype(int), [0]])))
            for s0, s1 in zip(idx[0::2], idx[1::2]):
                Lr = (s1 - s0) * Ls / n
                if Lr > run_best.get(pl, (0,))[0]:
                    k = (s0 + s1 - 1) // 2
                    run_best[pl] = (Lr, ln, float(px[k]), float(py[k]))
    return miss, run_best


# ----------------------------------------------------------------------------------------------- copper graph
def _proj(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x0, py - y0), 0.0, x0, y0
    t = ((px - x0) * dx + (py - y0) * dy) / L2
    tc = max(0.0, min(1.0, t))
    qx, qy = x0 + tc * dx, y0 + tc * dy
    return math.hypot(px - qx, py - qy), t, qx, qy


class Graph:
    """Copper graph of one or more nets. Nodes ('E', net, layer, x, y) at track ends and cuts, ('V', net, i) vias,
    ('PAD', ref, number) pads. Edges (node, length mm, kind, layer, width mm): trk, join, via, pad, R (series part
    bridging two pads), air (a missing connection, added by close_gaps())."""
    SLACK = 1000                                     # nm of tolerance in the geometric tests

    def __init__(s, pcbnew, data, nets, bridges=()):
        segs, vias, pads, _ = data
        s.adj = collections.defaultdict(list)
        s.xy = {}
        s.seg_total = 0.0
        s.layers_of_via = {}
        order = [0, 1, 2, 3, 4, 31]
        for net in nets:
            S, V, P = segs.get(net, []), vias.get(net, []), pads.get(net, [])
            for p in P:
                k = ('PAD', p['ref'], p['num'])
                s.xy[k] = (p['x'], p['y']); s.adj[k]
            vnode = []
            for i, v in enumerate(V):
                k = ('V', net, i)
                s.xy[k] = (v['x'], v['y']); s.adj[k]; vnode.append(k)
                i0, i1 = order.index(v['top']), order.index(v['bot'])
                s.layers_of_via[k] = set(order[min(i0, i1):max(i0, i1) + 1])
            ends = collections.defaultdict(list)
            for (x0, y0, x1, y1, L, w) in S:
                ends[L] += [(x0, y0), (x1, y1)]
            enodes = collections.defaultdict(dict)                   # layer -> node -> width
            for (x0, y0, x1, y1, L, w) in S:
                s.seg_total += math.hypot(x1 - x0, y1 - y0) * NM
                cuts = {0.0, 1.0}
                for (ex, ey) in ends[L]:
                    d, t, _, _ = _proj(ex, ey, x0, y0, x1, y1)
                    if d <= w / 2 + s.SLACK and 1e-9 < t < 1 - 1e-9:
                        cuts.add(t)
                for v in V:
                    d, t, _, _ = _proj(v['x'], v['y'], x0, y0, x1, y1)
                    if d <= w / 2 + v['r'] + s.SLACK and 1e-9 < t < 1 - 1e-9:
                        cuts.add(t)
                for p in P:
                    if L not in p['layers']:
                        continue
                    d, t, qx, qy = _proj(p['x'], p['y'], x0, y0, x1, y1)
                    if 1e-9 < t < 1 - 1e-9 and p['obj'].HitTest(pcbnew.VECTOR2I(int(round(qx)), int(round(qy))), 0):
                        cuts.add(t)
                cs = sorted(cuts)
                pts = [(x0 + t * (x1 - x0), y0 + t * (y1 - y0)) for t in cs]
                keys = [('E', net, L, int(round(px)), int(round(py))) for px, py in pts]
                for k, (px, py) in zip(keys, pts):
                    s.xy[k] = (px, py)
                    enodes[L][k] = min(w, enodes[L].get(k, w))
                for k0, k1, p0, p1 in zip(keys, keys[1:], pts, pts[1:]):
                    if k0 != k1:
                        s._edge(k0, k1, math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * NM, 'trk', L, w * NM)
            for L, ns in enodes.items():                             # copper ends on top of each other (within half a track)
                items = sorted(ns.items(), key=lambda kv: kv[0][3])
                for i, (u, wu) in enumerate(items):
                    for v, wv in items[i + 1:]:
                        if v[3] - u[3] > max(wu, wv):
                            break
                        d = math.hypot(u[3] - v[3], u[4] - v[4])
                        if 0 < d <= min(wu, wv) / 2 + s.SLACK:
                            s._edge(u, v, d * NM, 'join', L, min(wu, wv) * NM)
            for vk, v in zip(vnode, V):
                for L, ns in enodes.items():
                    if L not in s.layers_of_via[vk]:
                        continue
                    for k, w in ns.items():
                        d = math.hypot(k[3] - v['x'], k[4] - v['y'])
                        if d <= v['r'] + s.SLACK:
                            s._edge(vk, k, d * NM, 'via', L, w * NM)
            for p in P:
                pk = ('PAD', p['ref'], p['num'])
                for L in p['layers']:
                    for k, w in enodes.get(L, {}).items():
                        if p['obj'].HitTest(pcbnew.VECTOR2I(k[3], k[4]), 0):
                            s._edge(pk, k, math.hypot(k[3] - p['x'], k[4] - p['y']) * NM, 'pad', L, w * NM)
                for vk, v in zip(vnode, V):                           # via in pad
                    common = [L for L in p['layers'] if L in s.layers_of_via[vk]]
                    if common and p['obj'].HitTest(pcbnew.VECTOR2I(int(v['x']), int(v['y'])), 0):
                        s._edge(pk, vk, math.hypot(v['x'] - p['x'], v['y'] - p['y']) * NM, 'pad', common[0], 0.0)
        for ref, a, bnum in bridges:                                  # series resistor elements: pad a <-> pad b
            ka, kb = ('PAD', ref, a), ('PAD', ref, bnum)
            if ka in s.xy and kb in s.xy:
                s._edge(ka, kb, 0.0, 'R', None, 0.0)
        s.air = s.close_gaps()

    def _edge(s, u, v, L, kind, layer, w):
        s.adj[u].append((v, L, kind, layer, w))
        s.adj[v].append((u, L, kind, layer, w))

    def components(s):
        comp, out = {}, []
        for n in s.adj:
            if n in comp:
                continue
            st, cur = [n], [n]
            comp[n] = len(out)
            while st:
                for v, *_ in s.adj[st.pop()]:
                    if v not in comp:
                        comp[v] = len(out); st.append(v); cur.append(v)
            out.append(cur)
        return comp, out

    def close_gaps(s):
        """'air' edges: a minimum spanning tree over the copper islands that carry a pad (shortest straight line between
        two islands), as KiCad's ratsnest does. Returns the air edges [(node a, node b, mm)]."""
        comp, comps = s.components()
        live = [c for c in comps if any(n[0] == 'PAD' for n in c)]
        if len(live) < 2:
            return []
        pair = {}
        for i in range(len(live)):
            for j in range(i + 1, len(live)):
                best = None
                for a in live[i]:
                    ax, ay = s.xy[a]
                    for b in live[j]:
                        d = math.hypot(ax - s.xy[b][0], ay - s.xy[b][1])
                        if best is None or d < best[0]:
                            best = (d, a, b)
                pair[(i, j)] = best
        parent = list(range(len(live)))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        air = []
        for (i, j), (d, a, b) in sorted(pair.items(), key=lambda kv: kv[1][0]):
            if find(i) != find(j):
                parent[find(i)] = find(j)
                s._edge(a, b, d * NM, 'air', None, 0.0)
                air.append((a, b, d * NM))
        return air

    def trk_total(s):
        return sum(L for u in s.adj for (v, L, kind, layer, w) in s.adj[u] if kind == 'trk') / 2

    def path(s, src, dst):
        dist, prev, pq, n = {src: 0.0}, {}, [(0.0, 0, src)], 1
        while pq:
            d, _, u = heapq.heappop(pq)
            if u == dst:
                break
            if d > dist.get(u, 1e99):
                continue
            for v, L, kind, layer, w in s.adj[u]:
                nd = d + L + (1e-6 if kind == 'R' else 0.0)
                if nd < dist.get(v, 1e99):
                    dist[v] = nd; prev[v] = (u, L, kind, layer, w); heapq.heappush(pq, (nd, n, v)); n += 1
        if dst not in dist:
            return None
        edges, v = [], dst
        while v != src:
            u, L, kind, layer, w = prev[v]
            edges.append((u, v, L, kind, layer, w)); v = u
        return edges[::-1]

    def tree_path_len(s, src, dst):
        """Self-check: if the graph is a forest (no loop), the path is unique; find it by breadth-first search with
        parent links (independent of Dijkstra) and return its length, else None."""
        nodes = len(s.adj); edges = sum(len(v) for v in s.adj.values()) // 2
        if edges != nodes - len(s.components()[1]):
            return None
        par, q = {src: None}, collections.deque([src])
        while q:
            u = q.popleft()
            for v, L, *_ in s.adj[u]:
                if v not in par:
                    par[v] = (u, L); q.append(v)
        if dst not in par:
            return None
        tot, v = 0.0, dst
        while par[v] is not None:
            u, L = par[v]; tot += L; v = u
        return tot


# ----------------------------------------------------------------------------------------------- groups from the design
def hub_ref(D):
    return next((r for r, k in getattr(D, 'ROLE', {}).items() if k == 'hub'), 'U6')


def pins_of(D, ref, net):
    return sorted((p for p, n in D.NETS.get(ref, {}).items() if n == net), key=lambda x: (len(x), x))


def build_groups(D):
    """Groups of wires. A wire: name, nets (one graph), bridges, src (ref, pin), dsts [(ref, pin)]."""
    chips = sorted(D.G)
    chip_refs = ['U%d' % n for n in chips]
    hub = hub_ref(D)
    def on(net):
        return [r for r in chip_refs if pins_of(D, r, net)]
    def wire(net, src_ref, dst_refs, name=None):
        return dict(name=name or net, nets=[net], bridges=(), src=(src_ref, pins_of(D, src_ref, net)[0]),
                    dsts=[(r, pins_of(D, r, net)[0]) for r in dst_refs])
    G = []
    wl = list(D.WL)
    drv = 'U1'                                                  # docs/13: WLINK U1 -> U2, U5, hub
    rec = [r for r in on(wl[0]) if r != drv]
    G.append(dict(kind='WLINK', name='WLINK %s -> %s' % (drv, ', '.join(rec)), clock=wl[0], link='WLINK',
                  wires=[wire(n, drv, rec) for n in wl], rates=((25.0, 150.0), (40.0, 240.0))))
    ends = {'H1': ('1', 'H'), 'H2': ('2', 'H'), '14': ('1', '4'), '25': ('2', '5'), '48': ('4', '8'), '59': ('5', '9'), '89': ('8', '9')}
    for link, srcs in ends.items():
        for src in srcs:
            nets = D.xl(link, src)
            d = hub if src == 'H' else 'U' + src
            r = [x for x in on(nets[0]) if x != d]
            fast = link in ('H1', 'H2', '14', '25')
            G.append(dict(kind='XLINK', name='XLINK-%s %s -> %s' % (link, d, ', '.join(r)), clock=nets[0], link=link,
                          wires=[wire(n, d, r) for n in nets], rates=((25.0, 150.0),) + (((40.0, 240.0),) if fast else ())))
    for ref in chip_refs:
        n = ref[1:]
        sclk = 'QSPI%s_SCLK' % n
        flashes = sorted(r for r in D.NETS if r not in chip_refs and pins_of(D, r, sclk))
        for fl in flashes:
            ss = D.NETS[fl]['1']
            G.append(dict(kind='QSPI', name='QSPI%s %s -> %s (%s)' % (n, ref, fl, 'CS1' if ss.endswith('SS1') else 'CS0'),
                          clock=sclk, wires=[wire(x, ref, [fl]) for x in [sclk, ss] + ['QSPI%s_SD%d' % (n, k) for k in range(4)]]))
    for ref in chip_refs:
        n = ref[1:]
        ck, io = 'SWCLK' + n, 'SWDIO' + n
        if ref == hub:
            ext = next((r for r in D.NETS if r.startswith('J') and pins_of(D, r, ck)), None)
            if ext:
                G.append(dict(kind='SWD', name='SWD %s -> %s (external probe)' % (ext, hub), clock=ck,
                              wires=[wire(ck, ext, [hub]), wire(io, ext, [hub])]))
        else:
            G.append(dict(kind='SWD', name='SWD %s -> %s' % (hub, ref), clock=ck, wires=[wire(ck, hub, [ref]), wire(io, hub, [ref])]))
    card = next((r for r in D.NETS if pins_of(D, r, 'SD_CLK') and r != hub), None)
    if card:
        G.append(dict(kind='SD', name='microSD %s -> %s' % (hub, card), clock='SD_CLK',
                      wires=[wire(n, hub, [card]) for n in ('SD_CLK', 'SD_CMD', 'SD_DAT0', 'SD_DAT1', 'SD_DAT2', 'SD_DAT3')]))
    usb = []
    for pol, pin in (('DP', '67'), ('DM', '66')):
        rn, cn = 'USB_%s_R' % pol, 'USB_%s' % pol
        if D.NETS.get(hub, {}).get(pin) != rn:
            continue
        res = next(r for r in D.NETS if r != hub and pins_of(D, r, rn))
        conn = [(r, p) for r in D.NETS if r != res for p in pins_of(D, r, cn)]
        usb.append(dict(name='D+' if pol == 'DP' else 'D-', nets=[rn, cn], bridges=((res, '1', '2'),), src=(hub, pin), dsts=conn,
                        res=res))
    if usb:
        G.append(dict(kind='USB', name='USB %s -> 27 ohm -> J7' % hub, clock='D+', wires=usb))
    for net in ('nRST', 'VSEL_S'):
        rec = [r for r in on(net) if r != hub]
        if pins_of(D, hub, net) and rec:
            G.append(dict(kind='STATIC', name='%s %s -> %s' % (net, hub, ', '.join(rec)), clock=None, wires=[wire(net, hub, rec)]))
    # LINK / PLINK: one wire through the series arrays (each array element pin k <-> 9 - k)
    for name, nets, drv in (('LINK', ['LINK'] + ['LINK_%s' % c for c in 'ABCDEF'] + ['LINK_PU', 'LINK_T'], 'U1'),
                            ('PLINK', ['PLINK_F', 'PLINK_B', 'PLINK_E'], hub)):
        nets = [n for n in nets if any(n in m.values() for m in D.NETS.values())]
        arrays = sorted({r for r, m in D.NETS.items() if r.startswith('RN') and any(v in nets for v in m.values())
                         and all(v in nets or v is None for v in m.values())})
        bridges = tuple((r, str(i), str(9 - i)) for r in arrays for i in range(1, 5))
        src_net = next(n for n in nets if pins_of(D, drv, n))
        dsts = [(r, pins_of(D, r, n)[0]) for n in nets for r in chip_refs if r != drv and pins_of(D, r, n)]
        G.append(dict(kind=name, name='%s %s -> %s' % (name, drv, ', '.join(r for r, _ in dsts)), clock=None,
                      wires=[dict(name=name, nets=nets, bridges=bridges, src=(drv, pins_of(D, drv, src_net)[0]), dsts=dsts)]))
    return G


# ----------------------------------------------------------------------------------------------- analysis of a path
def analyse(graph, src, dst, M):
    edges = graph.path(src, dst)
    if edges is None:
        return dict(ok=False, reason='no copper or pad')
    per_layer = collections.Counter(); air = []
    for (u, v, L, kind, layer, w) in edges:
        if kind == 'air':
            air.append(dict(mm=L, a=u, b=v))
        elif kind != 'R':
            per_layer[(LNAME[layer], round(w, 4))] += L
    vias = []
    for i in range(1, len(edges)):
        if edges[i][0][0] == 'V':
            vias.append((LNAME.get(edges[i - 1][4], '?'), LNAME.get(edges[i][4], '?')))
    t = sum(L * M.tpd(ln, w if w > 0 else 0.12) for (ln, w), L in per_layer.items())
    tv = sum(M.via_ps(a, b)[0] for a, b in vias if a in LID and b in LID)
    air_mm = sum(a['mm'] for a in air)
    tpd_air = sum(M.tpd(l, 0.12) for l in ('F.Cu', 'In3.Cu', 'B.Cu')) / 3
    by_layer = collections.Counter()
    for (ln, w), L in per_layer.items():
        by_layer[ln] += L
    routed = sum(by_layer.values())
    straight = math.hypot(graph.xy[src][0] - graph.xy[dst][0], graph.xy[src][1] - graph.xy[dst][1]) * NM
    return dict(ok=True, edges=edges, length=routed + air_mm, routed=routed, air_mm=air_mm, air=air, by_layer=dict(by_layer),
                vias=vias, t_ps=t + tv + air_mm * tpd_air, open=bool(air), straight=straight,
                lower_bound=max(straight, routed) if air else routed + air_mm)


def n_open_paths(groups):
    return sum(1 for G in groups for w in G['wires'] for r in w['rows'] if r.get('ok') and r['open'])


def where(x_nm, y_nm, H):
    x, y = x_nm * NM, y_nm * NM
    return '(%.2f, %.2f; x\' %+.1f h %.1f)' % (x, y, x - 45.0, H - y)


class Ctx:
    """Everything the sections share: design, board data, models, graphs, report lines."""
    def __init__(s, D, pcbnew, data, M, stack, H):
        s.D, s.pcbnew, s.data, s.M, s.stack, s.H = D, pcbnew, data, M, stack, H
        s.graphs, s.lines, s.checks = {}, [], []
        chips = {'U%d' % n for n in D.G}
        s.chips = chips
        s.flashes = {r for r, p in D.PARTS.items() if str(p[2]).upper().startswith('W25Q')}

    def log(s, txt=''):
        print(txt)
        s.lines.append(txt)

    def graph(s, nets, bridges=()):
        key = (tuple(nets), tuple(bridges))
        if key not in s.graphs:
            s.graphs[key] = Graph(s.pcbnew, s.data, nets, bridges)
        return s.graphs[key]

    def check(s, family, ok, detail, item=''):
        s.checks.append((family, bool(ok), detail, item))

    def net_cap(s, nets, corner='max'):
        """Load of the copper of `nets` (pF): trace, vias, IC pins, other pads, card inputs."""
        segs, vias, pads, _ = s.data
        k = 1 if corner == 'max' else 0
        tr = sum(math.hypot(x1 - x0, y1 - y0) * NM * s.M.cpm(LNAME[L], round(w * NM, 4)) for n in nets for (x0, y0, x1, y1, L, w) in segs.get(n, []))
        nv = sum(len(vias.get(n, [])) for n in nets)
        pins = other = card = 0.0
        npins = 0
        for n in nets:
            for p in pads.get(n, []):
                if p['ref'] in s.chips:
                    pins += A['c_pin_rp'][k]; npins += 1
                elif p['ref'] in s.flashes:
                    pins += A['c_flash_in'] if p['num'] in ('1', '6') else A['c_flash_io']; npins += 1
                else:
                    for L in p['layers']:
                        if LNAME[L] in ('F.Cu', 'B.Cu'):
                            h, er = s.stack.outer_dielectric(LNAME[L])
                            other += A['pad_fringe'] * EPS0_PF_MM * er * p['area'] / h
                    if n.startswith('SD_') and str(s.D.PARTS.get(p['ref'], ('',) * 3)[2]).startswith('TF-'):
                        card += A['c_card']
        cv = nv * s.M.via_c_pf()
        return dict(trace=tr, vias=cv, nvias=nv, pins=pins, npins=npins, pads=other, card=card, total=tr + cv + pins + other + card)


def run_group(C, G):
    """Paths, per-layer lengths, vias, flight times and skew of every wire of a group; branches and stubs."""
    pads = C.data[2]
    for w in G['wires']:
        g = C.graph(w['nets'], w['bridges'])
        src = ('PAD',) + tuple(w['src'])
        w['rows'] = []
        for dst in w['dsts']:
            r = analyse(g, src, ('PAD',) + tuple(dst), C.M)
            r['dst'] = '%s.%s' % dst
            w['rows'].append(r)
        # copper by the exact set of receivers whose path uses it; copper on no path (stubs)
        sets = {}
        for dst, r in zip(w['dsts'], w['rows']):
            sets['%s.%s' % dst] = {frozenset((e[0], e[1])): e[2] for e in (r.get('edges') or []) if e[3] == 'trk'}
        users, elen = collections.defaultdict(set), {}
        for rcv, es in sets.items():
            for k, L in es.items():
                users[k].add(rcv); elen[k] = L
        pieces = collections.Counter()
        for k, us in users.items():
            pieces['+'.join(sorted(us))] += elen[k]
        tot = g.trk_total()
        on = sum(elen.values())
        endpoints = {'%s.%s' % tuple(w['src'])} | {'%s.%s' % d for d in w['dsts']}
        others = sorted({'%s.%s' % (p['ref'], p['num']) for n in w['nets'] for p in pads.get(n, [])} - endpoints)
        w['tree'] = dict(total=tot, on_path=on, off_path=tot - on, pieces=dict(pieces), other_pads=others)
        w['cap'] = C.net_cap(w['nets'], 'max')
        w['cap_typ'] = C.net_cap(w['nets'], 'typ')
        segs = C.data[0]
        byl = collections.Counter()
        for n in w['nets']:
            for (x0, y0, x1, y1, L, wd) in segs.get(n, []):
                byl[LNAME[L]] += math.hypot(x1 - x0, y1 - y0) * NM
        w['copper_by_layer'] = dict(byl)
        # self-checks on this wire's graph
        kl = sum(C.data[3].get(n, 0.0) for n in w['nets'])
        C.check('copper after splitting = KiCad track length, per wire', abs(tot - kl) < 1e-3, '%.4f vs %.4f mm' % (tot, kl), w['name'])
        if len(w['dsts']) > 1:
            # off-path copper counted independently over the graph's track edges: path pieces + the rest must be the whole
            # net (catches path edges that are not track edges, and duplicate tracks between the same two nodes)
            mult = collections.Counter()
            for u in g.adj:
                for (v, L, kind, layer, wd) in g.adj[u]:
                    if kind == 'trk':
                        mult[frozenset((u, v))] += 0.5
            off = sum(L for u in g.adj for (v, L, kind, layer, wd) in g.adj[u] if kind == 'trk' and frozenset((u, v)) not in users) / 2
            dup = sum((mult[k] - 1) * elen[k] for k in users)            # overlapping copper on a path (two tracks, same two nodes)
            per = max(abs(sum(L for k, L in pieces.items() if rcv in k.split('+')) - sum(e[2] for e in r.get('edges') or [] if e[3] == 'trk'))
                      for rcv, r in zip(sets, w['rows']))
            cons = abs(sum(pieces.values()) + dup + off - tot)
            w['tree']['overlap'] = dup
            C.check('multi-drop copper: shared + own pieces + overlaps + off-path = net copper; pieces of a receiver = its path',
                    cons < 1e-6 and per < 1e-6 and all(mult[k] >= 1 for k in users),
                    'sum %.6f, per receiver %.6f mm%s' % (cons, per, (', %.3f mm of overlapping track on the path' % dup) if dup > 1e-6 else ''), w['name'])
        for dst, r in zip(w['dsts'], w['rows']):
            if r.get('ok') and not r['open']:
                tl = g.tree_path_len(src, ('PAD',) + tuple(dst))
                if tl is not None:
                    dj = sum(e[2] for e in r['edges'] if e[3] != 'R')
                    C.check('path in a loop-free net: breadth-first search = Dijkstra', abs(tl - dj) < 1e-6, '%.6f vs %.6f mm' % (tl, dj),
                            '%s -> %s.%s' % (w['name'], dst[0], dst[1]))
    ck = next((w for w in G['wires'] if w['name'] == G['clock']), None)
    for w in G['wires']:
        for k, r in enumerate(w['rows']):
            r['skew_ps'] = None
            if ck is not None and w is not ck and r.get('ok') and ck['rows'][k].get('ok') and not r['open'] and not ck['rows'][k]['open']:
                r['skew_ps'] = r['t_ps'] - ck['rows'][k]['t_ps']


def print_group(C, G):
    C.log('\n%s' % G['name'])
    C.log('    %-10s %-8s %-9s %7s %6s %6s %6s %4s %6s %6s %5s  %s' % ('wire', 'from', 'to', 'len mm', 'F.Cu', 'In3', 'B.Cu', 'vias', 't ps', 'skew', 'In3%', 'notes'))
    for w in G['wires']:
        for r in w['rows']:
            if not r.get('ok'):
                C.log('    %-10s NO PATH: %s' % (w['name'], r.get('reason'))); continue
            bl = r['by_layer']
            notes = []
            if r['open']:
                notes.append('OPEN: routed %.1f + gaps %.1f mm (ratsnest estimate; lower bound %.1f mm, the straight distance)'
                             % (r['routed'], r['air_mm'], r['lower_bound']))
            vt = ','.join('%s%s' % ('3' if a == 'In3.Cu' else a[0], '3' if b == 'In3.Cu' else b[0]) for a, b in r['vias'])
            C.log('    %-10s %-8s %-9s %s%6.2f %6.2f %6.2f %6.2f %4d %6.0f %6s %4.0f%%  %s%s' % (
                w['name'], '%s.%s' % tuple(w['src']), r['dst'], '~' if r['open'] else ' ', r['length'], bl.get('F.Cu', 0), bl.get('In3.Cu', 0),
                bl.get('B.Cu', 0), len(r['vias']), r['t_ps'], '-' if r['skew_ps'] is None else '%+.0f' % r['skew_ps'],
                100 * bl.get('In3.Cu', 0) / max(1e-9, r['routed']), '; '.join(notes), ('[vias %s]' % vt) if vt else ''))
    for w in G['wires']:
        t = w['tree']; c = w['cap']
        extra = []
        if len(w['dsts']) > 1:
            extra.append('shared / own copper by receivers: ' + ', '.join('%s %.1f' % (k, v) for k, v in sorted(t['pieces'].items(), key=lambda kv: (-kv[0].count('+'), kv[0]))))
        if t.get('overlap', 0) > 1e-3:
            extra.append('%.2f mm of overlapping track on the paths' % t['overlap'])
        if t['off_path'] > 0.05 or t['other_pads']:
            op = t['other_pads']
            extra.append('off-path (stub) %.1f mm%s' % (t['off_path'], (' to ' + ', '.join(op[:6]) + (' and %d more pads' % (len(op) - 6) if len(op) > 6 else '')) if op else ''))
        C.log('    %-10s copper %.1f mm (%s), %d vias; load %.1f pF max = trace %.1f + vias %.1f + %d IC pins %.1f + pads %.2f%s%s' % (
            w['name'], t['total'], ', '.join('%s %.1f' % kv for kv in sorted(w['copper_by_layer'].items())), c['nvias'], c['total'], c['trace'],
            c['vias'], c['npins'], c['pins'], c['pads'], (' + card %.0f' % c['card']) if c['card'] else '', ('\n               ' + '; '.join(extra)) if extra else ''))


# ----------------------------------------------------------------------------------------------- timing of the links
def link_timing(C, G):
    """Source-synchronous budget per drive setting and receiver clock (see the module docstring)."""
    ck = next(w for w in G['wires'] if w['name'] == G['clock'])
    data = [w for w in G['wires'] if w is not ck]
    if any(not r.get('ok') or r['open'] for w in G['wires'] for r in w['rows']):
        return None
    res = dict(c_ck=ck['cap']['total'], c_d=max(w['cap']['total'] for w in data), rows=[])
    for label, mA, corner in DRIVES:
        rc_ck = t_rc(ck['cap']['total'], mA, corner)
        row = dict(drive=label, rc_ck=rc_ck, rc_d=max(t_rc(w['cap']['total'], mA, corner) for w in data), per_fsys={})
        for fsys in (150.0, 240.0):
            tsys = 1e3 / fsys
            need = 0.0
            for k in range(len(ck['rows'])):
                tck = ck['rows'][k]['t_ps'] * 1e-3
                tdl = max(w['rows'][k]['t_ps'] * 1e-3 + t_rc(w['cap']['total'], mA, corner) for w in data)
                tde = min(w['rows'][k]['t_ps'] * 1e-3 + t_rc_early(w['cap']['total'], mA, corner) for w in data)
                setup = tdl - (tck + t_rc_early(ck['cap']['total'], mA, corner)) - tsys
                hold = tck + rc_ck + 2 * tsys - tde
                need = max(need, setup, hold)
            fmax = 1e3 / (2 * (need + A['guard']))
            pio = [fsys / n for n in (2, 4, 6, 8, 10, 12, 16) if 1e3 / (2 * fsys / n) - need >= A['guard']]
            row['per_fsys'][fsys] = dict(need=need, fmax=fmax, pio=max(pio) if pio else None)
        res['rows'].append(row)
    res['slack'] = {}
    for f, fsys in G['rates']:
        for row in res['rows']:
            res['slack'][(f, fsys, row['drive'])] = 1e3 / (2 * f) - row['per_fsys'][fsys]['need']
    return res


def print_link_timing(C, G, T):
    if T is None:
        C.log('    timing: not computed (a wire is open)')
        return
    C.log('    budget (load: clock %.1f pF, data up to %.1f pF, max corner):' % (T['c_ck'], T['c_d']))
    for row in T['rows']:
        p1, p2 = row['per_fsys'][150.0], row['per_fsys'][240.0]
        sl = '; '.join('slack at %g MHz (%g MHz chips) %+.1f ns' % (f, fs, T['slack'][(f, fs, row['drive'])]) for f, fs in G['rates'])
        C.log('      %-11s RC clock %4.1f ns, data %4.1f ns | f_sys 150: need %4.1f ns, f_max %4.1f MHz, PIO %-5s | f_sys 240: need %4.1f, f_max %4.1f, PIO %-5s | %s' % (
            row['drive'], row['rc_ck'], row['rc_d'], p1['need'], p1['fmax'], '%g' % p1['pio'] if p1['pio'] else '-', p2['need'], p2['fmax'],
            '%g' % p2['pio'] if p2['pio'] else '-', sl))


# ----------------------------------------------------------------------------------------------- crosstalk scan
def net_class(n):
    if re.match(r'^(WL_|X(H1|H2|14|25|48|59|89)_)', n):
        return 'link'
    for pre, cls in (('QSPI', 'qspi'), ('SD_CD', 'static'), ('SD_', 'sd'), ('SWCLK', 'swd'), ('SWDIO', 'swd'), ('USB', 'usb'), ('XIN', 'crystal'),
                     ('XOUT', 'crystal'), ('SW_', 'converter switch node'), ('PWM', 'audio PWM'), ('LINK', 'LINK'), ('PLINK', 'PLINK')):
        if n.startswith(pre):
            return cls
    if re.match(r'^(C[AD]\d|P[AD]\d|X[D]\d|Y[D]\d|Z[AD]\d|CPU_|PPU_|M2|C_|Z_|ZM2|HM2|RD_D|P_WE|PWE_G|NCE_D|NA10_D|CIRAM|nROMSEL|RSEL_D|WS_D|PWS_D|M2n)', n):
        return 'console bus'
    return 'slow / static'


FAST_CLASSES = {'link', 'qspi', 'sd', 'swd', 'usb', 'crystal', 'converter switch node', 'audio PWM', 'console bus'}


def parallel_runs(C, victims, smax=0.5, max_angle_deg=5.0):
    """Same-layer parallel neighbours of each victim net: {victim: {(aggressor, layer): stats}}."""
    segs = C.data[0]
    power = set(getattr(C.D, 'POWER_NETS', set())) | {'GND'}
    rows = [(n, x0 * NM, y0 * NM, x1 * NM, y1 * NM, L, w * NM) for n, ss in segs.items() if n and n not in power
            for (x0, y0, x1, y1, L, w) in ss]
    names = [r[0] for r in rows]
    X0, Y0, X1, Y1, LL, WW = (np.array([r[k] for r in rows]) for k in range(1, 7))
    NN = np.array(names, dtype=object)
    sa = math.sin(math.radians(max_angle_deg))
    out = {}
    for v in victims:
        acc = {}
        for (x0, y0, x1, y1, L, w) in segs.get(v, []):
            vx0, vy0, vx1, vy1, wv = x0 * NM, y0 * NM, x1 * NM, y1 * NM, w * NM
            Lv = math.hypot(vx1 - vx0, vy1 - vy0)
            if Lv < 0.02:
                continue
            ux, uy = (vx1 - vx0) / Lv, (vy1 - vy0) / Lv
            reach = wv / 2 + smax + 0.5
            m = (LL == L) & (NN != v) & (np.minimum(X0, X1) <= max(vx0, vx1) + reach) & (np.maximum(X0, X1) >= min(vx0, vx1) - reach) \
                & (np.minimum(Y0, Y1) <= max(vy0, vy1) + reach) & (np.maximum(Y0, Y1) >= min(vy0, vy1) - reach)
            for i in np.flatnonzero(m):
                ax, ay, bx, by, wa = X0[i], Y0[i], X1[i], Y1[i], WW[i]
                La = math.hypot(bx - ax, by - ay)
                if La < 0.02 or abs(ux * (by - ay) - uy * (bx - ax)) / La > sa:
                    continue
                d0 = ux * (ay - vy0) - uy * (ax - vx0); d1 = ux * (by - vy0) - uy * (bx - vx0)
                t0 = ux * (ax - vx0) + uy * (ay - vy0); t1 = ux * (bx - vx0) + uy * (by - vy0)
                lo, hi = max(0.0, min(t0, t1)), min(Lv, max(t0, t1))
                ov = hi - lo
                gap = min(abs(d0), abs(d1)) - (wv + wa) / 2
                if ov < 0.05 or gap > smax:
                    continue
                cm = C.M.pair(LNAME[L], getattr(C.D, 'TRACK', 0.12), max(getattr(C.D, 'CLEAR', 0.12), round(gap / 0.02) * 0.02))['cm_pf_mm']
                k = (NN[i], LNAME[L])
                st = acc.setdefault(k, dict(len=0.0, gap=9.0, cml=0.0, best=(0.0, None)))
                st['len'] += ov; st['gap'] = min(st['gap'], gap); st['cml'] += cm * ov
                if ov > st['best'][0]:
                    st['best'] = (ov, (vx0 + lo * ux, vy0 + lo * uy, vx0 + hi * ux, vy0 + hi * uy))
        out[v] = acc
    return out


def print_crosstalk(C, runs, victims_detail, top=8):
    H = C.H
    res = {}
    for v, acc in runs.items():
        cap = C.net_cap([v], 'typ')
        tot = sum(s['cml'] for s in acc.values())
        fast = sum(s['cml'] for (a, _), s in acc.items() if net_class(a) in FAST_CLASSES)
        res[v] = dict(c=cap['total'], cml=tot, cml_fast=fast, ratio=tot / cap['total'] if cap['total'] else 0.0)
        if v not in victims_detail:
            continue
        C.log('  %s: load %.1f pF (typ); all parallel neighbours within 0.5 mm: sum Cm L = %.2f pF (fast ones %.2f pF) -> bound dV %.0f mV'
              ' (floating victim, every aggressor switching 3.3 V the same way)' % (v, cap['total'], tot, fast, 1e3 * A['iovdd'] * tot / cap['total']))
        for (a, ln), s in sorted(acc.items(), key=lambda kv: -kv[1]['cml'])[:top]:
            x0, y0, x1, y1 = s['best'][1]
            C.log('      %-12s %-21s %-6s parallel %5.1f mm, closest %.2f mm, Cm L %.3f pF; longest run %.1f mm from (%.1f, %.1f) to (%.1f, %.1f)'
                  ' [x\' %+.1f..%+.1f, h %.1f..%.1f]' % (a, net_class(a), ln, s['len'], s['gap'], s['cml'], s['best'][0], x0, y0, x1, y1,
                                                         x0 - 45, x1 - 45, H - y0, H - y1))
    return res


# ----------------------------------------------------------------------------------------------- KiCad in a child process
def child_main(board, out_json, rep):
    """(child process) refill the zones, record the plane areas, run KiCad's rule check on the unchanged board file."""
    import pcbnew
    b = pcbnew.LoadBoard(board)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    fills, _ = plane_fills(pcbnew, b, ('In1.Cu', 'In2.Cu', 'In4.Cu'))
    areas = {ln: contour_area(cs) for ln, cs in fills.items()}
    pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    json.dump(dict(areas=areas), open(out_json, 'w'))
    sys.stdout.flush()
    os._exit(0)


def kicad_check(board, out):
    rep = os.path.join(out, 'drc_links.txt')
    js = os.path.join(out, 'refill_areas.json')
    subprocess.run([sys.executable, os.path.abspath(__file__), '--_child', board, js, rep], check=True, capture_output=True, timeout=1800)
    text = open(rep).read()
    opens = collections.defaultdict(list)
    for blk in re.split(r'\n(?=\[)', text):
        if not blk.startswith('[unconnected_items]'):
            continue
        items = re.findall(r'@\(([-0-9.]+) mm, ([-0-9.]+) mm\): (.*)', blk)
        nets = re.findall(r'\[([^\]]+)\]', ' '.join(i[2] for i in items))
        if nets:
            opens[nets[0]].append(items)
    n_unc = re.search(r'\*\* Found (\d+) unconnected pads', text)
    sev = collections.Counter(re.findall(r'Severity: (\w+)', text))
    return opens, rep, json.load(open(js))['areas'], dict(sev), int(n_unc.group(1)) if n_unc else None


# ----------------------------------------------------------------------------------------------- rev G calibration
def calibrate_revg(pcbnew, path):
    """docs/12 publishes the rev G feed VSYS_D (diode cathode -> U4 VSYS) as 128 mm (power_drop.py); the path engine
    must reproduce it. Returns [(net, diode, ref, pin, path mm, vias, all copper mm)]."""
    b = pcbnew.LoadBoard(path)
    feeds = []
    for f in b.GetFootprints():
        if f.GetValue() != 'B5819W':
            continue
        nets = {p.GetNumber(): p.GetNetname() for p in f.Pads()}
        if nets.get('2') != '+5V':
            continue
        mod = [(g.GetReference(), p.GetNumber()) for g in b.GetFootprints() for p in g.Pads()
               if p.GetNetname() == nets['1'] and g.GetReference().startswith('U')]
        if mod:
            feeds.append((f.GetReference(), nets['1'], mod[0]))
    data = read_board(pcbnew, b)
    rows = []
    for d, net, (ref, num) in sorted(feeds, key=lambda r: int(r[0][1:])):
        g = Graph(pcbnew, data, [net])
        e = g.path(('PAD', d, '1'), ('PAD', ref, num))
        rows.append((net, d, ref, num, sum(x[2] for x in e if x[3] != 'R') if e else None, sum(1 for x in e if x[0][0] == 'V') if e else None,
                     data[3][net]))
    return rows


# ----------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board', help='routed board (.kicad_pcb); copied into --out before pcbnew opens it')
    ap.add_argument('--design', default=os.environ.get('FC_DESIGN', 'design_revh'), help='design module in the tools folder')
    ap.add_argument('--out', help='output folder (default: a new temporary folder)')
    ap.add_argument('--calib-board', help='rev G board: calibrate the path engine against docs/12 (VSYS_D 128 mm)')
    ap.add_argument('--no-drc', action='store_true', help="skip KiCad's rule check and zone refill (child process)")
    ap.add_argument('--fine', action='store_true', help='finer field-solver grid (convergence check)')
    ap.add_argument('--selftest', action='store_true', help='only the field solver against closed forms')
    ap.add_argument('--_child', nargs=3, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a._child:
        child_main(*a._child)
    res = (0.0005, 0.02, 1.1) if a.fine else XS.RES
    if a.selftest:
        bad = 0
        for r in XS.self_test(res):
            print('%-62s %9.4f %9.4f %+7.2f %%' % (r[0], r[1], r[2], 100 * r[3])); bad += abs(r[3]) > 0.015
        return 1 if bad else 0
    if not a.board:
        ap.error('--board is required')
    t_start = time.time()
    out = os.path.abspath(a.out) if a.out else tempfile.mkdtemp(prefix='links_')
    os.makedirs(out, exist_ok=True)
    if TOOLS not in sys.path:
        sys.path.insert(0, TOOLS)
    D = importlib.import_module(a.design)
    import pcbnew
    board = board_copy(a.board, out, 'board')
    text = open(board).read()
    stack = Stack(stackup_from_board(text), list(getattr(D, 'PLANES', {})) or ['In1.Cu', 'In2.Cu', 'In4.Cu'])
    b = pcbnew.LoadBoard(board)
    cpw_gap = next((z.GetLocalClearance() * NM for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() in (0, 31)), None)
    M = Models(stack, res, cpw_gap)
    data = read_board(pcbnew, b)
    H = float(getattr(D, 'H', 75.0))
    C = Ctx(D, pcbnew, data, M, stack, H)
    log = C.log
    log('famicart inter-chip links: lengths, skew, layers, vias, reference planes, loads, link budgets')
    log('board  %s (md5 %s; copy %s)' % (os.path.abspath(a.board), md5_of(a.board), board))
    log('design %s (%s, md5 %s); TRACK / CLEAR %.2f / %.2f mm' % (a.design, os.path.abspath(D.__file__), md5_of(D.__file__),
                                                                  getattr(D, 'TRACK', 0), getattr(D, 'CLEAR', 0)))
    log('output %s' % out)

    # ---------------------------------------------------------------- stack-up and models
    ref = gen_pcb_stackup(getattr(D, 'STACKUP', ''))
    same = bool(ref) and [(n, k, t, e) for n, k, t, _, e in ref] == [(l['name'], l['type'], l['t'], l['er']) for l in stack.body]
    C.check('stack-up of the board = gen_pcb.STACKUPS[%r]' % getattr(D, 'STACKUP', None), same, 'agrees' if same else 'DIFFERS')
    log('\nSTACK-UP (board file)')
    for l in stack.body:
        log('  %-13s %-8s %.4f mm%s' % (l['name'], l['type'], l['t'], '  er %.2f (%s)' % (l['er'], l['material']) if l['er'] else
                                        ('  plane' if l['name'] in stack.planes else '  signal')))
    log('  copper to copper %.4f mm; thickness-weighted er %.3f; solder mask %.3f mm, er %.1f (assumed)'
        % (stack.thickness, stack.er_avg, (stack.mask.get('F.Mask') or {}).get('t') or 0, A['mask_er']))

    groups = build_groups(D)
    nets = sorted({n for G in groups for w in G['wires'] for n in w['nets']})
    used = collections.Counter()
    for n in nets:
        for (x0, y0, x1, y1, L, w) in data[0].get(n, []):
            used[(LNAME[L], round(w * NM, 4))] += math.hypot(x1 - x0, y1 - y0) * NM
    log('\nMODELS (2-D field solution, xsection.py, grid hmin %.1f um); track widths on the analysed nets: %s'
        % (res[0] * 1e3, ', '.join('%s %.2f mm %.0f mm' % (k[0], k[1], v) for k, v in sorted(used.items()))))
    models = {}
    for (ln, w) in sorted(set(used) | {(l, getattr(D, 'TRACK', 0.12)) for l in ('F.Cu', 'In3.Cu', 'B.Cu')}):
        m = M.model(ln, w, variants=abs(w - getattr(D, 'TRACK', 0.12)) < 1e-6)
        M.cache[(ln, round(w, 4), False)] = m
        models['%s/%.3f' % (ln, w)] = {k: v for k, v in m.items()}
        log('  %-6s w %.3f: %-10s over %-15s eps_eff %.3f  t_pd %.3f ps/mm  Z0 %.1f ohm  C %.4f pF/mm%s'
            % (ln, w, m['kind'], '/'.join(m['planes']), m['eps_eff'], m['tpd_ps_mm'], m['z0'], m['c_pf_mm'],
               ('   [' + '; '.join('%s %.3f' % kv for kv in m['variants'].items()) + ']') if m['variants'] else ''))
    vz, vi, vb = M.via_ps('F.Cu', 'B.Cu'), M.via_ps('F.Cu', 'In3.Cu'), M.via_ps('In3.Cu', 'B.Cu')
    log('  via 0.5 / 0.3 mm: C %.3f pF (Johnson); delay F-B %.1f ps (barrel %.1f + lumped %.1f), F-In3 %.1f, In3-B %.1f (approximations)'
        % (M.via_c_pf(), vz[0], vz[1], vz[2], vi[0], vb[0]))
    log('  driver models: ' + '; '.join('%s R_hi %.0f / R_lo %.0f ohm' % ((lab,) + driver_r(mA, c)) for lab, mA, c in DRIVES)
        + '; crossing factors: rise to VIH %.2f RC, fall to VIL %.2f RC' % (K_RISE, K_FALL))
    st_rows = XS.self_test(res)
    worst_st = max(abs(r[3]) for r in st_rows)
    C.check('field solver within 1.5 % of the closed forms', worst_st < 0.015, 'largest %.2f %%' % (100 * worst_st))

    # ---------------------------------------------------------------- netlist check of every analysed net
    pads = data[2]
    mism = []
    for n in nets:
        for p in pads.get(n, []):
            if D.NETS.get(p['ref'], {}).get(p['num']) != n:
                mism.append('%s.%s board %s, design %s' % (p['ref'], p['num'], n, D.NETS.get(p['ref'], {}).get(p['num'])))
        on_board = {(p['ref'], p['num']) for p in pads.get(n, [])}
        for r, m in D.NETS.items():
            for pn, nn in m.items():
                if nn == n and (r, pn) not in on_board:
                    mism.append('%s.%s design %s, not on the board' % (r, pn, n))
    C.check('board pads = design netlist on all %d analysed nets' % len(nets), not mism, '%d mismatches%s' % (len(mism), (': ' + '; '.join(mism[:8])) if mism else ''))

    # ---------------------------------------------------------------- planes
    fills, fill_nets = plane_fills(pcbnew, b, ('In1.Cu', 'In2.Cu', 'In4.Cu'))
    bb = b.GetBoardEdgesBoundingBox()
    box = (bb.GetX() * NM, bb.GetY() * NM, (bb.GetX() + bb.GetWidth()) * NM, (bb.GetY() + bb.GetHeight()) * NM)
    t0 = time.time()
    planes = PlaneMap(fills, box)
    log('\nREFERENCE PLANES: stored fills %s rasterised at %.3f mm (%.0f s)' % (
        ', '.join('%s %s %.0f mm2' % (ln, '/'.join(sorted(fill_nets[ln])), contour_area(cs)) for ln, cs in sorted(fills.items())), planes.r, time.time() - t0))

    # ---------------------------------------------------------------- KiCad
    kopen, rep, refill, n_drc, n_unc = ({}, None, None, None, None)
    if not a.no_drc:
        t0 = time.time()
        kopen, rep, refill, n_drc, n_unc = kicad_check(board, out)
        log('KICAD (child process, zones refilled): rule check %s (report %s; this copy has no footprint library table, so library'
            ' lookups warn); %s unconnected items (%.0f s)' % (', '.join('%d %s' % (v, k) for k, v in sorted(n_drc.items())) or 'clean', rep, n_unc, time.time() - t0))
        dif = {ln: refill.get(ln, 0.0) / contour_area(fills[ln]) - 1 for ln in fills}
        C.check('stored plane fills = refilled', all(abs(v) < 5e-4 for v in dif.values()), ', '.join('%s %+.3f %%' % (ln, 100 * v) for ln, v in sorted(dif.items())))

    # ---------------------------------------------------------------- groups
    log('\nLENGTHS AND SKEW (pad centre to pad centre; t = flight time from the layer delays and the vias; skew = t(wire) - t(clock) at the same receiver;'
        ' load = all copper of the net + pins, max corner)')
    log('Link budget lines (WLINK, XLINK): per drive, the latest RC crossing of the clock and the data; "need" = the larger of hold'
        ' (t_late(CK) + 2 t_sys - t_early(D)) and set-up (t_late(D) - t_early(CK) - t_sys) at receiver clocks of 150 and 240 MHz;'
        ' f_max = 1 / (2 (need + %.0f ns guard)); PIO = the highest f_sys / N (N even) that keeps the guard; slack = T/2 - need at the docs/13'
        ' rates (supported when slack >= the guard)' % A['guard'])
    timings = {}
    for G in groups:
        run_group(C, G)
    for kind in ('WLINK', 'XLINK', 'QSPI', 'SD', 'SWD', 'USB', 'STATIC', 'LINK', 'PLINK'):
        for G in [g for g in groups if g['kind'] == kind]:
            print_group(C, G)
            if kind in ('WLINK', 'XLINK'):
                timings[G['name']] = link_timing(C, G)
                print_link_timing(C, G, timings[G['name']])

    # ---------------------------------------------------------------- reference planes under the analysed nets
    log('\nTRACK OVER A VOID OF ITS REFERENCE PLANE (sampled every 0.05 mm on the track centre line; F.Cu -> In1, B.Cu -> In4, In3 -> In2 and In4;'
        ' "none" = no plane on either side: an outer track over a void, an In3 track where In2 and In4 are both open)')
    void_rows = {}
    for G in groups:
        for w in G['wires']:
            if any(k[1] == w['name'] for k in void_rows):
                continue
            mm, best = collections.Counter(), {}
            for n in w['nets']:
                m, bst = plane_voids(data[0].get(n, []), stack, planes)
                mm.update(m)
                for pl, v in bst.items():
                    if v[0] > best.get(pl, (0,))[0]:
                        best[pl] = v
            void_rows[(G['name'], w['name'])] = (mm, best)
    void_kind = {}
    for kind in ('WLINK', 'XLINK', 'QSPI', 'SD', 'SWD', 'USB', 'STATIC', 'LINK', 'PLINK'):
        items = [k for k in void_rows if any(G['name'] == k[0] and G['kind'] == kind for G in groups)]
        tot = collections.Counter()
        for k in items:
            tot.update(void_rows[k][0])
        bad = [(k, void_rows[k]) for k in items if void_rows[k][0].get('none', 0) > 0.05]
        void_kind[kind] = dict(tot, longest=max((void_rows[k][1]['none'][0] for k in items if 'none' in void_rows[k][1]), default=0.0))
        log('  %-6s %d wires: %s' % (kind, len(items), ', '.join('%s %.1f mm' % (pl, v) for pl, v in sorted(tot.items())) or 'no track over a plane void'))
        for (gname, wname), (mm, best) in sorted(bad, key=lambda kv: -kv[1][0].get('none', 0))[:4]:
            log('      %-10s no plane under %.2f mm; longest %.2f mm on %s at %s' % (wname, mm['none'], best['none'][0], best['none'][1],
                                                                                  where(best['none'][2] / NM, best['none'][3] / NM, H)))

    # ---------------------------------------------------------------- QSPI: excess round trip against a Pico-2-like reference
    log('\nQSPI ROUND TRIP against a Pico-2-like reference (%.0f mm on F.Cu, one flash, no via; SCLK %d mA worst, flash output %.0f ohm):'
        ' excess = (SCLK there + data back) here - reference. SDK default (pico-sdk boot2_w25q080.S): CLKDIV 2, RXDELAY 2 = one system clock,'
        ' so at 150 MHz the pads, the board and the flash\'s clock-to-output must fit in 13.3 ns from the SCK edge' % (A['ref_len'], A['qspi_sclk_ma'], A['r_flash']))
    tw = getattr(D, 'TRACK', 0.12)
    c_ref_ck = A['ref_len'] * M.cpm('F.Cu', tw) + A['c_pin_rp'][1] + A['c_flash_in']
    c_ref_sd = A['ref_len'] * M.cpm('F.Cu', tw) + A['c_pin_rp'][1] + A['c_flash_io']
    t_ref = 2 * A['ref_len'] * M.tpd('F.Cu', tw) * 1e-3 + t_rc(c_ref_ck, A['qspi_sclk_ma'], 'worst') + K_FALL * A['r_flash'] * c_ref_sd * 1e-3
    qspi = []
    for G in [g for g in groups if g['kind'] == 'QSPI']:
        ck = G['wires'][0]
        rck = ck['rows'][0]
        worst = None
        for w in G['wires'][2:]:
            r = w['rows'][0]
            if not (r.get('ok') and rck.get('ok')):
                continue
            t = (rck['t_ps'] + r['t_ps']) * 1e-3 + t_rc(ck['cap']['total'], A['qspi_sclk_ma'], 'worst') + K_FALL * A['r_flash'] * w['cap']['total'] * 1e-3
            if worst is None or t > worst[0]:
                worst = (t, w['name'], w['cap']['total'])
        lens = [w['rows'][0]['length'] for w in G['wires'] if w['rows'][0].get('ok')]
        stubs = sum(w['tree']['off_path'] for w in G['wires'])
        exc = worst[0] - t_ref if worst else None
        qspi.append(dict(name=G['name'], lmin=min(lens), lmax=max(lens), stubs=stubs, sclk_c=ck['cap']['total'], excess=exc,
                         skew=max(abs(r['skew_ps']) for w in G['wires'] for r in w['rows'] if r.get('skew_ps') is not None)))
        log('  %-26s wires %5.1f-%5.1f mm, stubs %5.1f mm, SCLK load %5.1f pF, worst data %-10s %5.1f pF, max |skew| %3.0f ps, excess round trip %+5.2f ns'
            % (G['name'], min(lens), max(lens), stubs, ck['cap']['total'], worst[1] if worst else '-', worst[2] if worst else 0, qspi[-1]['skew'],
               exc if exc is not None else float('nan')))

    # ---------------------------------------------------------------- microSD
    sd = next((g for g in groups if g['kind'] == 'SD'), None)
    sd_res = None
    if sd and all(r.get('ok') and not r['open'] for w in sd['wires'] for r in w['rows']):
        ck = sd['wires'][0]
        log('\nmicroSD AT 25 MHz (hub drive per row; card tODLY %.0f ns, tISU / tIH %.0f / %.0f ns, card input %.0f pF; all assumed, SD spec default speed)'
            % (A['sd_todly'], A['sd_tisu'], A['sd_tih'], A['c_card']))
        sd_res = []
        for label, mA, corner in DRIVES:
            T2 = 20.0
            tck_late = ck['rows'][0]['t_ps'] * 1e-3 + t_rc(ck['cap']['total'], mA, corner)
            tck_early = ck['rows'][0]['t_ps'] * 1e-3 + t_rc_early(ck['cap']['total'], mA, corner)
            d0 = next(w for w in sd['wires'] if w['name'] == 'SD_DAT0')
            spi = T2 - (tck_late + A['sd_todly'] + d0['rows'][0]['t_ps'] * 1e-3)
            win = 2 * T2 - A['sd_todly'] - (tck_late - tck_early)
            wr = min(T2 + tck_early - (w['rows'][0]['t_ps'] * 1e-3 + t_rc(w['cap']['total'], mA, corner)) - A['sd_tisu'] for w in sd['wires'][1:])
            hd = min(T2 + w['rows'][0]['t_ps'] * 1e-3 + t_rc_early(w['cap']['total'], mA, corner) - tck_late - A['sd_tih'] for w in sd['wires'][1:])
            sd_res.append(dict(drive=label, spi=spi, win=win, wr_setup=wr, wr_hold=hd))
            log('  %-11s SPI read: DAT0 valid at the hub %.1f ns before the next rising SCK (before the SPI block\'s own input delay);'
                ' 4-bit read window %.1f ns (PIO needs >= 1 sysclk = 6.7 ns at 150 MHz); write at the card: set-up slack %+.1f ns, hold slack %+.1f ns'
                % (label, spi, win, wr, hd))

    # ---------------------------------------------------------------- SWD
    swd_res = []
    log('\nSWD (bit-banged by the hub; 4 mA worst): read round trip = SWCLK RC + flight there + SWDIO RC + flight back (the target\'s own'
        ' output delay not included); a stub matters when its round trip is not small against the edge (10-90 % = 2.2 RC)')
    for G in [g for g in groups if g['kind'] == 'SWD']:
        ck, io = G['wires']
        if not all(r.get('ok') and not r['open'] for w in G['wires'] for r in w['rows']):
            log('  %-30s open' % G['name']); continue
        rt = (ck['rows'][0]['t_ps'] + io['rows'][0]['t_ps']) * 1e-3 + t_rc(ck['cap']['total'], 4, 'worst') + t_rc(io['cap']['total'], 4, 'worst')
        stub = max(ck['tree']['off_path'], io['tree']['off_path'])
        edge = 2.2 * driver_r(4, 'worst')[0] * min(ck['cap']['total'], io['cap']['total']) * 1e-3
        srt = 2 * stub * M.tpd('In3.Cu', tw) * 1e-3
        swd_res.append(dict(name=G['name'], clk=ck['rows'][0]['length'], dio=io['rows'][0]['length'], stub=stub, rt=rt, edge=edge, stub_rt=srt))
        log('  %-32s SWCLK %5.1f mm, SWDIO %5.1f mm, stub up to %4.1f mm (round trip %.2f ns against an edge of %.1f ns); read round trip %.1f ns'
            % (G['name'], ck['rows'][0]['length'], io['rows'][0]['length'], stub, srt, edge, rt))
    if swd_res:
        log('  longest round trip %.1f ns: %.0f %% of the 100 ns half period at 5 MHz' % (max(x['rt'] for x in swd_res), max(x['rt'] for x in swd_res)))

    # ---------------------------------------------------------------- USB
    usb = next((g for g in groups if g['kind'] == 'USB'), None)
    usb_res = None
    if usb:
        log('\nUSB PAIR')
        dp, dm = usb['wires'][0], usb['wires'][1] if len(usb['wires']) > 1 else None
        usb_res = dict()
        for w in usb['wires']:
            g = C.graph(w['nets'], w['bridges'])
            src = ('PAD',) + tuple(w['src'])
            rpads = [p for p in pads.get(w['nets'][0], []) if p['ref'] == w['res']]
            e = g.path(src, ('PAD', w['res'], rpads[0]['num'])) if rpads else None
            lr = sum(x[2] for x in e) if e else None
            st = math.hypot(rpads[0]['x'] - g.xy[src][0], rpads[0]['y'] - g.xy[src][1]) * NM if rpads else None
            own = {d: w['tree']['pieces'].get(d, 0.0) for d in ('%s.%s' % x for x in w['dsts'])}
            stub = max(own.values()) if own else 0.0                   # with the plug one way round, the other row's own branch hangs
            usb_res[w['name']] = dict(to_res=lr, straight=st, rows=[(r['dst'], r['length'], r['t_ps']) for r in w['rows'] if r.get('ok')],
                                      stub=stub, layers=w['copper_by_layer'], vias=sum(len(r['vias']) for r in w['rows'] if r.get('ok')))
            log('  %s: %s pin %s -> %s pad %s: routed %.2f mm (straight %.2f mm; docs/13: within about %.0f mm); to J7: %s; copper %s, %d vias;'
                ' stub of the unused contact row up to %.1f mm'
                % (w['name'], w['src'][0], w['src'][1], w['res'], rpads[0]['num'] if rpads else '?', lr or float('nan'), st or float('nan'), USB_R_MAX_MM,
                   ', '.join('%s %.2f mm %.0f ps' % row for row in usb_res[w['name']]['rows']), ', '.join('%s %.1f' % kv for kv in sorted(w['copper_by_layer'].items())),
                   w['cap']['nvias'], stub))
        if dm:
            sk = [(a[0], b[0], a[2] - b[2]) for a, b in zip(usb_res['D+']['rows'], usb_res['D-']['rows'])]
            usb_res['skew'] = sk
            log('  skew D+ - D-: ' + ', '.join('%s / %s %+.1f ps' % s for s in sk))
            pr = parallel_runs(C, dp['nets'], smax=0.5)
            cpl = [(k, s) for v in pr.values() for k, s in v.items() if k[0] in dm['nets']]
            Lc = sum(s['len'] for _, s in cpl)
            if cpl:
                gmin = min(s['gap'] for _, s in cpl)
                lay = cpl[0][0][1]
                zp = M.pair(lay, tw, max(getattr(D, 'CLEAR', 0.12), round(gmin / 0.02) * 0.02))
                usb_res.update(coupled=Lc, gap=gmin, zdiff=zp['z_diff'])
                log('  D+ / D- run side by side for %.1f mm (closest %.2f mm edge to edge, %s): Z_diff %.0f ohm there (docs/13 aims at 90 ohm);'
                    ' apart, each line is %.0f ohm single-ended' % (Lc, gmin, lay, zp['z_diff'], M.model(lay, tw)['z0']))
            else:
                log('  D+ / D- never run side by side within 0.5 mm: each line %.0f ohm single-ended' % M.model('F.Cu', tw)['z0'])

    # ---------------------------------------------------------------- crosstalk: long static lines and the link clocks
    log('\nPARALLEL RUNS (same layer, within 0.5 mm edge to edge and 5 deg of parallel; Cm per mm from the pair solver at the closest spacing)')
    for ln in ('F.Cu', 'In3.Cu'):
        log('  Cm of two %.2f mm tracks on %s, pF/mm at a gap of: %s' % (tw, ln, ', '.join('%.2f mm %.4f' % (g_, M.pair(ln, tw, g_)['cm_pf_mm'])
                                                                                       for g_ in (0.12, 0.2, 0.3, 0.5))))
    statics = [w['name'] for G in groups if G['kind'] == 'STATIC' for w in G['wires']]
    clocks = sorted({G['clock'] for G in groups if G['kind'] in ('WLINK', 'XLINK', 'SD', 'SWD', 'QSPI') and G['clock']})
    t0 = time.time()
    runs = parallel_runs(C, statics + clocks)
    xt = print_crosstalk(C, runs, statics)
    worst_ck = sorted(((v, xt[v]) for v in clocks), key=lambda kv: -kv[1]['ratio'])[:4]
    log('  clocks of the links and buses, the largest coupling ratios sum(Cm L) / C (a driven line sees at most this share of an aggressor\'s swing):')
    for v, r in worst_ck:
        top = sorted(runs[v].items(), key=lambda kv: -kv[1]['cml'])[:3]
        log('    %-10s %4.1f %% (%.2f of %.1f pF): %s' % (v, 100 * r['ratio'], r['cml'], r['c'], '; '.join(
            '%s (%s) %s %.1f mm at %.2f mm' % (a, net_class(a), ln, st_['len'], st_['gap']) for (a, ln), st_ in top)))
    log('  (%.0f s)' % (time.time() - t0))

    # ---------------------------------------------------------------- docs/13 estimates
    log('\nAGAINST docs/13\'S ESTIMATES (XLINK-48 / -59 about 10-20 mm, XLINK-89 about 75 mm; no estimate for the others)')
    est_rows = []
    for G in [g for g in groups if g['kind'] == 'XLINK']:
        lens = [r['length'] for w in G['wires'] for r in w['rows'] if r.get('ok')]
        st = [r['straight'] for w in G['wires'] for r in w['rows'] if r.get('ok')]
        lo, hi = DOC13_EST.get(G['link'], (None, None))
        over = [w['name'] for w in G['wires'] for r in w['rows'] if r.get('ok') and hi and r['length'] > hi]
        est_rows.append(dict(name=G['name'], lmin=min(lens), lmax=max(lens), est=hi, over=over))
        log('  %-24s %5.1f-%5.1f mm (straight pad to pad %5.1f-%5.1f mm)  %s' % (G['name'], min(lens), max(lens), min(st), max(st),
            ('estimate %s%.0f mm: %s' % ('%.0f-' % lo if lo else 'about ', hi, ('ABOVE: ' + ', '.join(over)) if over else 'within')) if hi else
            ('no estimate%s' % ('; above 20 mm: %d of %d wires' % (sum(1 for x in lens if x > 20), len(lens))))))

    # ---------------------------------------------------------------- flags
    summ_pre = {k: sum(1 for G in groups if G['kind'] == k for w in G['wires'] for r in w['rows'] if r.get('ok') and r['by_layer'].get('In3.Cu', 0) > 0)
                for k in FAST_KINDS}
    flags = []
    long_ = sorted({(w['name'], r['dst'], r['length']) for G in groups if G['kind'] not in ('STATIC', 'LINK', 'PLINK') for w in G['wires'] for r in w['rows']
                    if r.get('ok') and r['length'] > LEN_LIMIT_MM})
    if n_open_paths(groups):
        flags.append('open wires: %d paths' % n_open_paths(groups))
    if long_:
        flags.append('link paths longer than %.0f mm: %s' % (LEN_LIMIT_MM, ', '.join('%s -> %s %.1f' % x for x in long_)))
    over = [w for r in est_rows for w in r['over']]
    if over:
        flags.append("above docs/13's estimate: %d wires (%s)" % (len(over), ', '.join(over)))
    for name, T in timings.items():
        if T is None:
            continue
        for (f, fs, drv), sl in T['slack'].items():
            if drv == '%d mA worst' % A['link_ma'] and sl < A['guard']:
                ok = [d for (f2, fs2, d), s2 in T['slack'].items() if (f2, fs2) == (f, fs) and s2 >= A['guard'] and 'worst' in d]
                flags.append('%s at %g MHz (%g MHz chips), %d mA worst: slack %+.2f ns < the guard; first worst-case drive that keeps it: %s'
                             % (name, f, fs, A['link_ma'], sl, ok[0] if ok else 'none of 4/8/12 mA'))
    for q in qspi:
        if q['excess'] is not None and q['excess'] > A['guard']:
            flags.append('%s: round trip %.2f ns longer than the Pico-2-like reference' % (q['name'], q['excess']))
    if sd_res and sd_res[0]['spi'] < 1e3 / 150:
        flags.append('microSD SPI read at 25 MHz, %s: DAT0 valid only %.1f ns before the sampling edge at the hub pin (less than one 150 MHz clock)'
                     % (sd_res[0]['drive'], sd_res[0]['spi']))
    if usb_res:
        for k in ('D+', 'D-'):
            if k in usb_res and usb_res[k]['to_res'] and usb_res[k]['to_res'] > USB_R_MAX_MM:
                flags.append('USB %s: 27 ohm %.1f mm from the hub pin (docs/13: about %.0f mm)' % (k, usb_res[k]['to_res'], USB_R_MAX_MM))
    for v in statics:
        dv = A['iovdd'] * xt[v]['cml'] / xt[v]['c']
        if dv > 0.3:
            flags.append('%s: crosstalk bound %.2f V' % (v, dv))
    for kind in FAST_KINDS:
        if kind in summ_pre and summ_pre[kind]:
            flags.append('%s paths with In3 copper (docs/13: outer layers): %d' % (kind, summ_pre[kind]))
    log('\nFLAGS')
    for f_ in flags:
        log('  ' + f_)
    if not flags:
        log('  none')

    # ---------------------------------------------------------------- summary and shares
    log('\nSUMMARY BY KIND (In3 share: path-weighted = each driver-receiver path counted; copper-weighted = each net\'s copper once)')
    summ = {}
    for kind in ('WLINK', 'XLINK', 'QSPI', 'SD', 'SWD', 'USB', 'STATIC', 'LINK', 'PLINK'):
        gs = [g for g in groups if g['kind'] == kind]
        rows = [r for g in gs for w in g['wires'] for r in w['rows'] if r.get('ok')]
        if not rows:
            continue
        Lp = sum(r['routed'] for r in rows); L3p = sum(r['by_layer'].get('In3.Cu', 0) for r in rows)
        cu = collections.Counter()
        seen = set()
        for g in gs:
            for w in g['wires']:
                for n in w['nets']:
                    if n in seen:
                        continue
                    seen.add(n)
                    for (x0, y0, x1, y1, L, wd) in data[0].get(n, []):
                        cu[LNAME[L]] += math.hypot(x1 - x0, y1 - y0) * NM
        Lc = sum(cu.values())
        on3 = sum(1 for r in rows if r['by_layer'].get('In3.Cu', 0) > 0)
        summ[kind] = dict(paths=len(rows), open=sum(1 for r in rows if r['open']), path_mm=Lp, path_in3=L3p, copper_mm=Lc, copper_in3=cu.get('In3.Cu', 0.0),
                          paths_on_in3=on3, longest=max(r['length'] for r in rows))
        log('  %-6s %3d paths (%d open, %d with In3 copper), longest %.1f mm; paths %.0f mm, In3 %.0f %%; copper %.0f mm, In3 %.0f %%'
            % (kind, len(rows), summ[kind]['open'], on3, summ[kind]['longest'], Lp, 100 * L3p / max(Lp, 1e-9), Lc, 100 * cu.get('In3.Cu', 0) / max(Lc, 1e-9)))

    # ---------------------------------------------------------------- opens against KiCad
    mine = {n: len(C.graph([n]).air) for n in nets}
    n_open = n_open_paths(groups)
    if not a.no_drc:
        diff = {n: (mine.get(n, 0), len(kopen.get(n, []))) for n in nets if mine.get(n, 0) != len(kopen.get(n, []))}
        C.check('open gaps per net = KiCad unconnected items, %d analysed nets' % len(nets), not diff,
                ('%d nets differ: %s' % (len(diff), diff)) if diff else '%d open gaps on the analysed nets, KiCad %d' % (sum(mine.values()), sum(len(v) for v in kopen.values() if v)))

    # ---------------------------------------------------------------- rev G calibration
    if a.calib_board:
        log('\nREV G CALIBRATION (docs/12: the rev G feed VSYS_D diode -> U4 is 128 mm, from power_drop.py)')
        cb = board_copy(a.calib_board, out, 'calib')
        rows = calibrate_revg(pcbnew, cb)
        for net, d, ref_, num, L, nv, kl in rows:
            log('  %-7s %s.1 -> %s.%s: %s mm, %s vias (all copper of the net %.1f mm)' % (net, d, ref_, num, '%.1f' % L if L else 'NO PATH', nv, kl))
        vd = next((r for r in rows if r[0] == 'VSYS_D'), None)
        C.check('rev G VSYS_D = docs/12 128 mm (within 1 mm)', vd is not None and vd[4] is not None and abs(vd[4] - 128.0) <= 1.0,
                '%.1f mm (board md5 %s)' % (vd[4], md5_of(a.calib_board)) if vd and vd[4] else 'not found')

    # ---------------------------------------------------------------- self-checks
    log('\nSELF-CHECKS')
    for row in st_rows:
        log('  solver: %-62s %9.4f vs %9.4f (%+.2f %%)' % (row[0], row[1], row[2], 100 * row[3]))
    fam = collections.OrderedDict()
    for family, ok, det, item in C.checks:
        fam.setdefault(family, []).append((ok, det, item))
    fails = 0
    for family, items in fam.items():
        bad = [x for x in items if not x[0]]
        fails += len(bad)
        if len(items) == 1:
            log('  %-4s %s: %s' % ('ok' if not bad else 'FAIL', family, items[0][1]))
        else:
            log('  %-4s %s: %d cases%s' % ('ok' if not bad else 'FAIL', family, len(items),
                                         (', failing: ' + '; '.join('%s (%s)' % (x[2], x[1]) for x in bad[:6])) if bad else ''))
    log('SELF-CHECKS: %s' % ('all pass' if not fails else '%d FAIL' % fails))
    log('\n%d paths, %d open; %.1f s' % (sum(len(w['rows']) for G in groups for w in G['wires']), n_open, time.time() - t_start))

    # ---------------------------------------------------------------- outputs
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items() if k not in ('edges', 'air')}
        if isinstance(o, (list, tuple)):
            return [clean(x) for x in o]
        if isinstance(o, float):
            return round(o, 4)
        if isinstance(o, (np.floating, np.integer)):
            return clean(o.item())
        return o
    js = dict(board=os.path.abspath(a.board), md5=md5_of(a.board), design=a.design, design_md5=md5_of(D.__file__), assumptions=A,
              models=models, groups=[{k: v for k, v in G.items()} for G in groups], timing={k: v and dict(v, slack={'%g MHz @%g / %s' % kk: vv for kk, vv in v['slack'].items()})
                                                                                         for k, v in timings.items()},
              qspi=qspi, sd=sd_res, usb=usb_res, swd=swd_res, plane_voids=void_kind, flags=flags, crosstalk={v: {'%s %s' % k: s for k, s in acc.items()} for v, acc in runs.items()}, crosstalk_summary=xt,
              estimates=est_rows, summary=summ, checks=C.checks, kicad=dict(drc=n_drc, unconnected=n_unc))
    json.dump(clean(js), open(os.path.join(out, 'links.json'), 'w'), indent=1, ensure_ascii=False)
    open(os.path.join(out, 'links_report.txt'), 'w').write('\n'.join(C.lines) + '\n')
    print('report: %s' % os.path.join(out, 'links_report.txt'))
    return 1 if fails else 0


if __name__ == '__main__':
    code = main()
    sys.stdout.flush()
    os._exit(code or 0)
