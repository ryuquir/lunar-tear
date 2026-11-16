#!/usr/bin/env python3
"""Console-bus timing of a routed famicart board, from the board's own copper with rev G's timing models
(docs/12_rev_g_plan.md "検証で分かった数値"; the rev G review's calculations are not in the repository, their results are).

What it checks and why
  The cartridge answers both Famicom buses through series resistors, so every pF behind them costs time, and docs/13
  ("本体側の回路", "時間について") asks for rev G's timing calculation to be redone with rev H's routing and 6-layer
  stack-up. The tool measures the capacitance the board really puts on every console node and runs rev G's models on it:
    - PPU read: /RD -> 1k -> RD_D node -> PIO -> data line through its series resistor, for U2 and for U5 driving,
      against the 186.24 ns /RD low time and docs/13's target (settled 30 ns before /RD rises: 156.2 ns).
    - CPU read chain: M2 -> 74LS139 /ROMSEL -> detection (raw /ROMSEL on its own 1k, or RSEL_D through Q4) -> PIO ->
      data bus settled at the console, against M2 falling (349.2 ns, RP2A03E/G/H) minus a 50 or 100 ns 6500 set-up.
    - Strobes RSEL_D, WS_D, PWS_D (2N7002 transients) and the write-capture window after WS_D, for every simulated
      FET / capacitance / console-level corner and every CPU version, against the firmware delays of docs/12.
    - The capacitance the cartridge adds to every console line (finger node, branches behind their resistors, FET
      gates), next to the rev G board's; RC delays of every branch; CIRAM /CE and A10 edges; open connections.

Method
  1. Netlist from the design module (NETS, PARTS, J1): each finger net, its series elements (an array element has the
     part's element value, e.g. '680 x4' -> 680 ohm; elements to the same far net are in parallel), pull resistors,
     clamps, FET pins, and the chip pins on each branch net.
  2. Copper from pcbnew, on a copy of the board in --out: tracks sampled every 0.05 mm, pads as strips, vias counted.
     At every sample: the reference plane really under it (zones refilled in a child process, plane coverage in a
     window about 3x the height) and the gap to the nearest foreign copper on both sides (net-code raster, 0.02 mm).
  3. C per mm: 2-D finite-volume Laplace solver on the stack-up (JLC06121H-3313: microstrip over In1 / In4 with 10 um
     of mask, over In2 where the adjacent plane is missing, asymmetric stripline on In3; rev G: FR4 1.11 mm), checked
     against Hammerstad-Jensen and IPC-2141; coplanar neighbours as a per-side increment.
  4. Node capacitance min / typ / max = copper (+-10 %) + vias + pins + clamps. Open connections are bounded by the
     straight distance x this board's own detour statistics.
  5. Models: EKV 2N7002 with rev G's corners and explicit 10 ps transients - RSEL_D with the 74LS139 totem pole, its
     2.2k pull-up and the console's own /ROMSEL capacitance on the gate node, the raw /ROMSEL branches as RC nodes
     behind their 1k; WS_D = NOR of Q1 / Q3 with each CPU version's M2 high time; PWS_D through Q6. PPU and CPU reads:
     rev G's lumped formula and an exact linear RC network (driver node - R - finger node - R - other branches); the
     network is the headline number. Other branches: single-pole RC.

Assumptions (all in the table A below with their source; --set overrides any of them)
  - RP2350B pin 3 / 4 / 6 pF: assumed, the datasheet gives none. Pico 2 / XIAO pin 4 / 5 / 8 pF (rev G review).
  - RP2350 output at the firmware's 8 mA drive: 40 ohm typ (rev G); worst 62.5 ohm low (VOL <= 0.5 V at 8 mA) and
    85 ohm high (VOH >= 2.62 V at 8 mA), RP2350 datasheet Table 1683.
  - PPU /RD source 40 ohm (rev G, no data; its sensitivity is printed). Console address / strobe drivers 40 / 120 ohm,
    console capacitance of /ROMSEL 5 / 10 / 20 pF and of M2 10 / 15 / 25 pF: assumed.
  - Console side of a PPU data line: rev G's undocumented total 35 / 60 pF, split against the rev G board three ways
    (A: console + finger copper, docs/13's reading; B: console alone; C: everything including U5's branch).
  - 74LS373 IIL 0.2 / 0.4 mA, input thresholds 1.4 / 0.8 V, PIO latency 13 / 33 ns, 2N7002 corners (rev G).
  - CPU read: console CPU data bus 45 / 65 pF (assumed), 6500 set-up 50 / 100 ns, 74LS139 M2 -> /ROMSEL 22 / 38 ns.
  - Vias 0.20 / 0.29 / 0.40 pF (Johnson, 0.5 / 0.3 mm via, 1.0 mm antipad); BAV99 1.0 / 1.5 / 3.0 pF.

Limits
  2-D cross-sections (no 3-D fringe at pad ends, bends or via stubs; side increments solved for a 0.15 mm track);
  neighbours count as grounded; lumped or few-node RC (no transmission lines, crosstalk, ground bounce); drivers are
  linear resistors. Pin capacitance, PIO latency, the console-side capacitances and the 2A03's set-up are not
  measured: the absolute PPU and CPU read numbers carry them (sensitivities are printed). --selftest shows that the
  port reproduces rev G's own simulation output (the review's NOR / RSEL runs, published in docs/12), not that
  rev G's inputs were right; on the rev G board only the copper share of a node is a check, the pins are assumptions
  on both sides. Open links are bounded, not measured. Not covered: LINK / XLINK / WLINK, audio, /IRQ release,
  power-up, and how the added load affects the console's own bus.

Usage (any working folder; the design module comes from the tools folder, the parent of this script's folder)
    python3 tools/pcb/review/timing.py --board B.kicad_pcb [--design design_revh] \
        [--calib-board revg.kicad_pcb [--calib-design design_revg]] [--out DIR] [--compare OLD_DIR/timing.json]
    python3 tools/pcb/review/timing.py --selftest
  --design defaults to $FC_DESIGN, then design_revh. --out defaults to a new temporary folder, and nothing is written
  anywhere else: the board (and its .kicad_pro) is copied there before pcbnew opens it, and the C/mm tables are solved
  once per --out (about 2 min) and cached in it. --compare lists every item that is slower than in an earlier run of
  this tool. --set KEY=v1,v2[,v3] overrides an assumption. Outputs: timing_report.txt, timing.json. Exit code 1 if a
  self-check warns (self-test against rev G, board against design, track width against the design's TRACK).

Healthy result
  "self-checks: all pass"; no open console net; PPU read worst case (network, reading A) below 156.2 ns for U2 and U5
  (at the very least below 186.2 ns); the CPU read chain via raw /ROMSEL inside "M2 fall - 100 setup" in the worst
  case (or inside "- 50" with that CPU grade stated); every capture-window corner contains the firmware delay; PWS_D
  above 2.0 V for >= 60 ns at typ caps; per-layer pF/mm close to the solver's values and node capacitances close to
  rev G's per console line."""
import sys, os, math, json, argparse, importlib, subprocess, time, re, hashlib, shutil, tempfile
sys.dont_write_bytecode = True                     # set before the design module is imported: no __pycache__ in tools/pcb
import numpy as np

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # famicart/tools/pcb (design modules)
EPS0_PF_MM = 8.8541878128e-3                       # vacuum permittivity in pF/mm
C_LIGHT = 299792458.0

# ====================================================================================== assumptions (all in one place)
# Each entry says where it comes from; "assumed" = no datasheet or measurement behind it.  --set KEY=v1,v2[,v3] overrides.
A = {
    # --- pin input capacitance (pF) as (min, typ, max). The RP2350 datasheet gives no value: assumed.
    'pin_qfn': (3.0, 4.0, 6.0),                    # RP2350B QFN-80 GPIO incl. package lead (assumed)
    'pin_module': (4.0, 5.0, 8.0),                 # Pico 2 / XIAO castellation: chip pin + module trace (rev G review:
                                                   # "about 5 pF each"; 8 pF reproduces its max-corner 24 pF)
    'bav99': (1.0, 1.5, 3.0),                      # clamp = two diodes, Cd <= 1.5 pF each at 0 V (BAV99 datasheet)
    'via_6l': (0.20, 0.29, 0.40),                  # through via 0.5/0.3 mm, 1.2 mm, antipad 1.0 mm (Johnson, see below)
    'via_2l': (0.05, 0.10, 0.15),                  # 2-layer via: two 0.5 mm rings in the pours, no planes (assumed)
    'copper_tol': 0.10,                            # +-10 % on the solved C/mm (epsilon_r, prepreg thickness, etch; assumed)
    'neighbour_min_share': 0.5,                    # min corner counts only half of the coplanar-neighbour increment
    # --- RP2350 output resistance as (typ, worst). The firmware sets 8 mA drive on the bus pins (src/reve_ppu/main.c,
    #     src/reve_cpu/main.c, src/pico/bus.c). typ 40 ohm = rev G; worst = datasheet Table 1683 at 8 mA:
    'r_drv': (40.0, 62.5),                         #   driving low:  VOL <= 0.5 V at 8 mA
    'r_drv_hi': (40.0, 85.0),                      #   driving high: VOH >= 2.62 V at 8 mA (IOVDD 3.3 V)
    # --- console side
    'r_rd_src': (40.0, 40.0),                      # PPU (2C02) /RD output resistance: rev G's 40 ohm, no data (sensitivity printed)
    'r_console': (40.0, 120.0),                    # console drivers of address / strobe lines (2A03, 2C02, 74LS139): assumed
    'ppu_bus_total': (35.0, 60.0),                 # rev G "Cbus" typ / worst (pF): no breakdown given (readings A / B / C)
    'iil': (0.2e-3, 0.4e-3),                       # 74LS373 input low current typ / max (A) (rev G)
    'console_vil': (1.4, 0.8),                     # console input threshold (PPU; used for the 2A03 too) typ / worst (V) (rev G)
    'rd_vth': (1.2, 0.8),                          # RP2350 sees /RD low: typ Schmitt / guaranteed VIL (V) (Table 1683)
    'pio': (13.0, 33.0),                           # PIO latency from the input pad to the output switching (ns) (rev G)
    'v_start_fall': 4.0, 'v_drv_low': 0.05, 'v_rise_from': 0.3, 'v_rise_to': 3.2, 'v_ih': 2.0,     # rev G
    'rd_from': 4.0, 'rd_final': 0.3,                                                                 # rev G
    'console_romsel': (5.0, 10.0, 20.0),           # console /ROMSEL: 74LS139 output + its track (pF), assumed
    'console_m2': (10.0, 15.0, 25.0),              # console M2: 2A03 pin, LS139 input, expansion port, track (pF), assumed
    # CPU data bus of the console (2A03 15 pF max, WRAM, PPU register port, '368, ~20 cm of track): NOT in rev G
    'cpu_bus_console': (45.0, 65.0),               # assumed; sets the absolute CPU-read numbers
    'tdsu': (50.0, 100.0),                         # 6500 data setup before phi2 falls: 2 MHz / 1 MHz grade (ns)
    'ls139_tphl': (22.0, 38.0),                    # M2 -> /ROMSEL falling, typ / max of the two possible paths (ns, 74LS139)
    'ppu_window': 186.24, 'ppu_target_margin': 30.0,     # /RD low time; docs/13 target: settled 30 ns before /RD rises
    'ciram_console': (10.0, 15.0),                 # console CIRAM /CE or A10 input + its track (pF), assumed
}
# CPU versions: M2 low share of the 558.73 ns cycle and the firmware's capture delay after WS_D (docs/12, WS_D row)
VERSIONS = {'E/G/H': (9 / 24, (160.0, 180.0)), '17/24': (7 / 24, (205.0, 230.0)), '18/24': (6 / 24, (205.0, 230.0))}
T_CYC = 558.73
# Johnson & Graham, "High-speed digital design", via capacitance C = 1.41 er T D1 / (D2 - D1) pF (T in inches):
#   er 4.4, T 1.2 mm = 0.0472 in, D1 0.5 mm (pad on every layer), D2 1.0 mm (0.25 mm plane clearance) -> 0.29 pF.

# rev G's published PPU read (docs/12 "検証で分かった数値"), typ / worst ns
PUBLISHED = {'ppu500': (60.0, 158.0), 'ppu1k': (85.0, 240.0)}

# ====================================================================================== stack-ups and C per mm
# 6-layer JLC06121H-3313 (gen_pcb.STACKUPS): F 0.035 / pp 3313 0.0994 er 4.1 / In1 0.0152 / core 0.35 er 4.6 / In2 /
# pp 2116 0.1164 er 4.16 / In3 / core 0.35 er 4.6 / In4 / pp 3313 0.0994 er 4.1 / B 0.035.
# 2-layer (gen_pcb.STACKUP_2L): 0.035 / FR4 1.11 er 4.5 / 0.035.  Solder mask 0.01 mm (stack-up file), er 3.8.
MASK = (0.01, 3.8)
def _slabs(spec):
    out, y = [], 0.0
    for t, er in spec: out.append((y, y + t, er)); y += t
    return out, y
CASES = {
    # name: (dielectric slabs from the reference conductor up to the track's base, copper thickness, track layer kind,
    #        plane above?, extra)
    'O6_plane': dict(below=[(0.0994, 4.1)], t=0.035, outer=True),
    'O6_far':   dict(below=[(0.35, 4.6), (0.0152, 4.1), (0.0994, 4.1)], t=0.035, outer=True),            # F.Cu over In2
    'O6_farB':  dict(below=[(0.1164, 4.16), (0.0152, 4.16), (0.35, 4.6), (0.0152, 4.1), (0.0994, 4.1)], t=0.035,
                     outer=True),                                                                       # B.Cu over In2
    'O6_opp':   dict(below=[(0.0994, 4.1), (0.0152, 4.1), (0.35, 4.6), (0.0152, 4.16), (0.1164, 4.16), (0.0152, 4.16),
                            (0.35, 4.6), (0.0152, 4.1), (0.0994, 4.1)], t=0.035, outer=True),
    'O6_air':   dict(below=[(0.0994, 4.1), (0.0152, 4.1), (0.35, 4.6), (0.0152, 4.16), (0.1164, 4.16), (0.0152, 4.16),
                            (0.35, 4.6), (0.0152, 4.1), (0.0994, 4.1)], t=0.035, outer=True, air_below=3.0),
    'I6_both':  dict(below=[(0.35, 4.6)], t=0.0152, outer=False, above=[(0.1164 + 0.0152, 4.16)]),
    'I6_in4':   dict(below=[(0.35, 4.6)], t=0.0152, outer=False, above=[(0.1164 + 0.0152, 4.16), (0.0152, 4.16), (0.35, 4.6)]),
    'I6_in2':   dict(below=[(0.0994, 4.1), (0.0152, 4.1), (0.35, 4.6)], t=0.0152, outer=False, above=[(0.1164 + 0.0152, 4.16)]),
    'O2_opp':   dict(below=[(1.11, 4.5)], t=0.035, outer=True),
    'O2_air':   dict(below=[(1.11, 4.5)], t=0.035, outer=True, air_below=3.0),
}
WIDTHS = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5]
GAPS = [0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5]

def _grid1d(keys, lo, hi, flo, fhi, hf, hc):
    pts = {round(k, 7) for k in keys if lo <= k <= hi} | {lo, hi}
    pts |= {round(float(v), 7) for v in np.arange(lo, hi, hc)}
    pts |= {round(float(v), 7) for v in np.arange(max(lo, flo), min(hi, fhi), hf)}
    g = sorted(pts); keep = [g[0]]
    for v in g[1:]:
        if v - keep[-1] > 1e-6: keep.append(v)
    return np.array(keep)

def fv_solve(eps_rects, conds, dom, fine, hf, hc, top_dirichlet=True):
    """2-D electrostatics on a rectilinear grid (finite volumes, nodes at the grid points, epsilon per cell).
    eps_rects: [(x0, x1, y0, y1, er)] (later ones win), conds: [(x0, x1, y0, y1, V)], Neumann on the open sides.
    Returns the capacitance per unit length between the V=1 conductor and the V=0 ones, pF/mm (energy method)."""
    import scipy.sparse as sp, scipy.sparse.linalg as spl
    xmin, xmax, ymin, ymax = dom
    rects = eps_rects + conds
    x = _grid1d([r[0] for r in rects] + [r[1] for r in rects], xmin, xmax, fine[0], fine[1], hf, hc)
    y = _grid1d([r[2] for r in rects] + [r[3] for r in rects], ymin, ymax, fine[2], fine[3], hf, hc)
    nx, ny = len(x), len(y)
    xc, yc = (x[:-1] + x[1:]) / 2, (y[:-1] + y[1:]) / 2
    E = np.ones((nx - 1, ny - 1))
    for (x0, x1, y0, y1, er) in eps_rects:
        E[np.ix_((xc >= x0) & (xc <= x1), (yc >= y0) & (yc <= y1))] = er
    V = np.full((nx, ny), np.nan)
    for (x0, x1, y0, y1, v) in conds:
        V[np.ix_((x >= x0 - 1e-9) & (x <= x1 + 1e-9), (y >= y0 - 1e-9) & (y <= y1 + 1e-9))] = v
    if top_dirichlet: V[:, -1] = np.where(np.isnan(V[:, -1]), 0.0, V[:, -1])
    dx, dy = np.diff(x), np.diff(y)
    Ep = np.zeros((nx - 1, ny + 1)); Ep[:, 1:-1] = E
    dyp = np.zeros(ny + 1); dyp[1:-1] = dy
    gh = (Ep[:, :-1] * dyp[:-1] / 2 + Ep[:, 1:] * dyp[1:] / 2) / dx[:, None]
    Eq = np.zeros((nx + 1, ny - 1)); Eq[1:-1, :] = E
    dxp = np.zeros(nx + 1); dxp[1:-1] = dx
    gv = (Eq[:-1, :] * dxp[:-1, None] / 2 + Eq[1:, :] * dxp[1:, None] / 2) / dy[None, :]
    free = np.isnan(V); nf = int(free.sum())
    idx = -np.ones((nx, ny), dtype=np.int64); idx[free] = np.arange(nf)
    rows, cols, vals = [], [], []
    rhs = np.zeros(nf); diag = np.zeros(nf)
    def edges(ia, ja, ib, jb, g):
        a, b = idx[ia, ja], idx[ib, jb]; fa, fb = a >= 0, b >= 0
        m = fa & fb
        rows.extend([a[m], b[m]]); cols.extend([b[m], a[m]]); vals.extend([-g[m], -g[m]])
        np.add.at(diag, a[fa], g[fa]); np.add.at(diag, b[fb], g[fb])
        m2 = fa & ~fb; np.add.at(rhs, a[m2], g[m2] * V[ib, jb][m2])
        m3 = fb & ~fa; np.add.at(rhs, b[m3], g[m3] * V[ia, ja][m3])
    I, J = np.meshgrid(np.arange(nx - 1), np.arange(ny), indexing='ij'); edges(I.ravel(), J.ravel(), I.ravel() + 1, J.ravel(), gh.ravel())
    I, J = np.meshgrid(np.arange(nx), np.arange(ny - 1), indexing='ij'); edges(I.ravel(), J.ravel(), I.ravel(), J.ravel() + 1, gv.ravel())
    rows.append(np.arange(nf)); cols.append(np.arange(nf)); vals.append(diag)
    Amat = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(nf, nf))
    P = V.copy(); P[free] = spl.spsolve(Amat, rhs)
    W = (gh * (P[1:, :] - P[:-1, :]) ** 2).sum() + (gv * (P[:, 1:] - P[:, :-1]) ** 2).sum()
    return EPS0_PF_MM * W

def section_c(case, w, gap=None, mask=True):
    """C per mm of a track of width w in stack-up case `case`, coplanar grounds at `gap` on both sides (None: none)."""
    c = CASES[case]
    slabs, yb = _slabs(c['below'])            # reference conductor at y <= 0, track base at yb
    t = c['t']; yt = yb + t
    big = yb > 0.6 or c.get('air_below')
    side = (6.0 if big else 2.0) + w / 2
    X = side
    eps = [(-X, X, y0, y1, er) for (y0, y1, er) in slabs]
    conds = [(-w / 2, w / 2, yb, yt, 1.0)]
    ybot = -0.05
    if c.get('air_below'):
        ybot = -c['air_below']; conds.append((-X, X, ybot - 0.05, ybot, 0.0))
    else:
        conds.append((-X, X, -0.05, 0.0, 0.0))
    if c['outer'] and mask:
        tm, em = MASK
        eps.append((-X, X, yb, yb + tm, em)); eps.append((-w / 2 - tm, w / 2 + tm, yb, yt + tm, em))
        if gap is not None:
            eps.append((-X, -w / 2 - gap + tm, yb, yt + tm, em)); eps.append((w / 2 + gap - tm, X, yb, yt + tm, em))
        ytop = yt + (6.0 if big else 2.0); top_d = True
    elif c['outer']:
        ytop = yt + (6.0 if big else 2.0); top_d = True
    else:
        aslabs, ya = _slabs(c['above'])
        eps += [(-X, X, yb + a0, yb + a1, er) for (a0, a1, er) in aslabs]
        ytop = yb + ya; conds.append((-X, X, ytop, ytop + 0.05, 0.0)); ytop += 0.05; top_d = False
    if gap is not None:
        conds.append((-X, -w / 2 - gap, yb, yt, 0.0)); conds.append((w / 2 + gap, X, yb, yt, 0.0))
    g = gap or 0.0
    fine = (-w / 2 - g - 0.15, w / 2 + g + 0.15, yb - 0.08, yt + 0.08)
    hf, hc = (0.005, 0.1) if big else (0.0025, 0.02)
    return fv_solve(eps, conds, (-X, X, ybot - 0.05 if c.get('air_below') else -0.05, ytop), fine, hf, hc, top_dirichlet=top_d)

def hammerstad_jensen(w, h, er, t):
    """Microstrip C per mm (Hammerstad & Jensen 1980 with their thickness correction; no mask)."""
    eta0 = 376.730313
    def z01(u): f = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u) ** 0.7528); return eta0 / (2 * math.pi) * math.log(f / u + math.sqrt(1 + 4 / u / u))
    def ee(u, er):
        a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
        b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
        return (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    u, tn = w / h, t / h
    du1 = tn / math.pi * math.log(1 + 4 * math.e / (tn * (1 / math.tanh(math.sqrt(6.517 * u))) ** 2))
    dur = 0.5 * (1 + 1 / math.cosh(math.sqrt(er - 1))) * du1
    u1, ur = u + du1, u + dur
    z0 = z01(ur) / math.sqrt(ee(ur, er)); eeff = ee(ur, er) * (z01(u1) / z01(ur)) ** 2
    return math.sqrt(eeff) / (C_LIGHT * z0) * 1e9, z0, eeff

def ipc2141_asym_stripline(w, t, h_near, h_far, er):
    z0 = 80 / math.sqrt(er) * math.log(1.9 * (2 * h_near + t) / (0.8 * w + t)) * (1 - h_near / (4 * (h_near + h_far + t)))
    return math.sqrt(er) / (C_LIGHT * z0) * 1e9, z0

def c_tables(cache_path, cases=None, log=print):
    """{case: {'w': [...], 'c': [...], 'gap': [...], 'dside': [...]}} - solved once, cached as JSON."""
    tab = {}
    if os.path.exists(cache_path):
        try: tab = json.load(open(cache_path))
        except Exception: tab = {}
    todo = [k for k in (cases or CASES) if k not in tab]
    for k in todo:
        t0 = time.time()
        cs = [section_c(k, w) for w in WIDTHS]
        c15 = cs[WIDTHS.index(0.15)]
        ds = [(section_c(k, 0.15, g) - c15) / 2 for g in GAPS]
        tab[k] = {'w': WIDTHS, 'c': cs, 'gap': GAPS, 'dside': ds}
        log(f'  solved {k}: C(0.15) = {c15:.4f} pF/mm, side increment at 0.25 mm {ds[GAPS.index(0.25)]:.4f} ({time.time() - t0:.0f} s)')
        json.dump(tab, open(cache_path, 'w'), indent=1)
    return tab

class CPerMM:
    def __init__(self, tab): self.tab = tab
    def iso(self, case, w):
        t = self.tab[case]; return float(np.interp(w, t['w'], t['c']))
    def side(self, case, g):
        """increment for ONE side with foreign copper at gap g (mm); 0 beyond the table"""
        t = self.tab[case]
        if g is None or not np.isfinite(g) or g >= t['gap'][-1]: return 0.0
        return float(np.interp(max(g, t['gap'][0]), t['gap'], t['dside']))

# ====================================================================================== board reading (pcbnew)
def _mm(v):
    import pcbnew
    return pcbnew.ToMM(v)

def board_copy(path, work):
    """copy the board (and its .kicad_pro) into the work folder: pcbnew only ever opens the copy"""
    d = os.path.join(work, 'board_' + hashlib.md5(os.path.abspath(path).encode()).hexdigest()[:8]); os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(path)); shutil.copy2(path, dst)
    pro = os.path.splitext(path)[0] + '.kicad_pro'
    if os.path.exists(pro): shutil.copy2(pro, os.path.join(d, os.path.basename(pro)))
    return dst

def read_board(path, log=print):
    """Plain-data copy of the board: tracks, vias, pads (with polygons), pad clusters of every net. Read BEFORE any
    zone fill (pcbnew quirk); the fills come from fill_zones_child()."""
    import pcbnew
    b = pcbnew.LoadBoard(path)
    if not hasattr(b, 'GetTracks'): raise SystemExit(f'pcbnew could not load {path}')
    cu = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
    names = {l: n for n, l in cu.items()}
    nets = {ni.GetNetname(): code for code, ni in b.GetNetsByNetcode().items() if code > 0}
    tracks, vias, pads = [], [], []
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            vias.append(dict(net=n, x=_mm(t.GetPosition().x), y=_mm(t.GetPosition().y), dia=_mm(t.GetWidth()), drill=_mm(t.GetDrillValue())))
        elif t.GetClass() == 'PCB_TRACK':
            s, e = t.GetStart(), t.GetEnd()
            tracks.append(dict(net=n, layer=names.get(t.GetLayer(), '?'), w=_mm(t.GetWidth()), x1=_mm(s.x), y1=_mm(s.y), x2=_mm(e.x), y2=_mm(e.y)))
        else:
            raise SystemExit('arc tracks are not handled: %s' % t.GetClass())
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            lays = [names[l] for l in p.GetLayerSet().CuStack() if l in names]
            polys = {}
            for ln in lays:
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, cu[ln], 0, pcbnew.FromMM(0.002))
                cs = []
                for i in range(ps.OutlineCount()):
                    ol = ps.Outline(i)
                    cs.append([(_mm(ol.CPoint(k).x), _mm(ol.CPoint(k).y)) for k in range(ol.PointCount())])
                polys[ln] = cs
            pads.append(dict(ref=ref, num=p.GetNumber(), net=p.GetNetname(), layers=lays, polys=polys,
                             x=_mm(p.GetPosition().x), y=_mm(p.GetPosition().y), sx=_mm(p.GetSize().x), sy=_mm(p.GetSize().y),
                             ang=p.GetOrientation().AsDegrees(), smd=p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD, shape=p.GetShape()))
    # pad clusters per net (BFS through the connectivity graph: tracks, vias, pads)
    b.BuildConnectivity(); conn = b.GetConnectivity()
    by_net = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname(): by_net.setdefault(p.GetNetname(), []).append(p)
    clusters = {}
    for n, pl in by_net.items():
        seen, cl = {}, []
        for p in pl:
            k = p.m_Uuid.AsString()
            if k in seen: continue
            comp, stack = [], [p]; seen[k] = len(cl)
            while stack:
                it = stack.pop()
                if it.GetClass() == 'PAD': comp.append(f'{it.GetParent().GetReference()}.{it.GetNumber()}')
                else:
                    if it.GetClass() == 'PCB_VIA': comp.append(('via', _mm(it.GetPosition().x), _mm(it.GetPosition().y)))
                    else: comp.append(('trk', _mm(it.GetStart().x), _mm(it.GetStart().y), _mm(it.GetEnd().x), _mm(it.GetEnd().y)))
                for q in list(conn.GetConnectedTracks(it)) + list(conn.GetConnectedPads(it)):
                    if q.GetNetname() != n: continue
                    kq = q.m_Uuid.AsString()
                    if kq not in seen: seen[kq] = len(cl); stack.append(q)
            cl.append(comp)
        clusters[n] = cl
    bb = b.GetBoardEdgesBoundingBox()
    box = (_mm(bb.GetX()), _mm(bb.GetY()), _mm(bb.GetX() + bb.GetWidth()), _mm(bb.GetY() + bb.GetHeight()))
    unconnected = b.GetConnectivity().GetUnconnectedCount(True)
    ncu = b.GetCopperLayerCount()
    whist = {}                                     # {layer: {width mm: length mm}} of all tracks
    for t in tracks:
        h = whist.setdefault(t['layer'], {}); w = round(t['w'], 3)
        h[w] = h.get(w, 0.0) + math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1'])
    return dict(path=path, md5=hashlib.md5(open(path, 'rb').read()).hexdigest(), layers=[names[l] for l in b.GetEnabledLayers().CuStack()],
                ncu=ncu, nets=nets, tracks=tracks, vias=vias, pads=pads, clusters=clusters, box=box, unconnected=unconnected, whist=whist)

def fill_zones_child(path, out_json):
    """(child process) refill every zone and dump the filled polygons as point lists."""
    import pcbnew
    b = pcbnew.LoadBoard(path)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    out = []
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        for l in z.GetLayerSet().Seq():
            ps = z.GetFilledPolysList(l)
            cs = []
            for i in range(ps.OutlineCount()):
                for ch in [ps.Outline(i)] + [ps.Hole(i, h) for h in range(ps.HoleCount(i))]:
                    cs.append([(pcbnew.ToMM(ch.CPoint(k).x), pcbnew.ToMM(ch.CPoint(k).y)) for k in range(ch.PointCount())])
            out.append(dict(net=z.GetNetname(), layer=b.GetLayerName(l), contours=cs))
    json.dump(out, open(out_json, 'w'))

def get_fills(path, work, log=print):
    out = os.path.join(work, 'fills_' + os.path.basename(path) + '.json')
    if not (os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(path)):
        t0 = time.time()
        subprocess.run([sys.executable, os.path.abspath(__file__), '--_fill', path, out], check=True)
        log(f'  zones refilled in a child process ({time.time() - t0:.0f} s)')
    return json.load(open(out))

# ====================================================================================== rasters
class Raster:
    """Net-code raster per copper layer (0 = no copper, -1 = copper without a net) and plane-presence rasters."""
    def __init__(self, bd, fills, r=0.02, log=print):
        t0 = time.time()
        self.r = r; x0, y0, x1, y1 = bd['box']
        self.x0, self.y0 = x0 - 1.0, y0 - 1.0
        self.nx, self.ny = int((x1 - x0 + 2.0) / r) + 1, int((y1 - y0 + 2.0) / r) + 1
        self.code = dict(bd['nets']); self.code[''] = -1
        self.own = {ln: np.zeros((self.nx, self.ny), dtype=np.int32) for ln in bd['layers']}
        self.plane = {}
        for z in fills:
            if z['layer'] not in self.own: continue
            self._poly(self.own[z['layer']], z['contours'], self.code.get(z['net'], -1))
        for p in bd['pads']:
            for ln, cs in p['polys'].items():
                if ln in self.own: self._poly(self.own[ln], cs, self.code.get(p['net'], -1))
        for t in bd['tracks']:
            if t['layer'] in self.own: self._seg(self.own[t['layer']], t['x1'], t['y1'], t['x2'], t['y2'], t['w'], self.code.get(t['net'], -1))
        for v in bd['vias']:
            for ln in self.own: self._seg(self.own[ln], v['x'], v['y'], v['x'], v['y'], v['dia'], self.code.get(v['net'], -1))
        log(f'  rasters {self.nx} x {self.ny} at {r} mm, {len(self.own)} layers ({time.time() - t0:.0f} s)')

    def _poly(self, R, contours, val):
        """even-odd scanline fill of pixel centres"""
        E = []
        for c in contours:
            if len(c) < 3: continue
            p = np.asarray(c, dtype=float); q = np.roll(p, -1, axis=0); E.append(np.hstack([p, q]))
        if not E: return
        E = np.vstack(E)
        E = E[E[:, 1] != E[:, 3]]
        ylo = np.minimum(E[:, 1], E[:, 3]); yhi = np.maximum(E[:, 1], E[:, 3])
        j0 = max(0, int(math.floor((ylo.min() - self.y0) / self.r - 0.5)))
        j1 = min(self.ny - 1, int(math.ceil((yhi.max() - self.y0) / self.r)))
        order = np.argsort(ylo); E, ylo, yhi = E[order], ylo[order], yhi[order]
        for j in range(j0, j1 + 1):
            yc = self.y0 + (j + 0.5) * self.r
            k = np.searchsorted(ylo, yc, side='right')
            if k == 0: continue
            e = E[:k]; m = yhi[:k] > yc
            if not m.any(): continue
            e = e[m]
            xs = np.sort(e[:, 0] + (yc - e[:, 1]) * (e[:, 2] - e[:, 0]) / (e[:, 3] - e[:, 1]))
            for a, bq in zip(xs[0::2], xs[1::2]):
                i0 = max(0, int(math.ceil((a - self.x0) / self.r - 0.5))); i1 = min(self.nx - 1, int(math.floor((bq - self.x0) / self.r - 0.5)))
                if i1 >= i0: R[i0:i1 + 1, j] = val

    def _seg(self, R, x1, y1, x2, y2, w, val):
        h = w / 2; r = self.r
        i0 = max(0, int((min(x1, x2) - h - self.x0) / r)); i1 = min(self.nx - 1, int((max(x1, x2) + h - self.x0) / r) + 1)
        j0 = max(0, int((min(y1, y2) - h - self.y0) / r)); j1 = min(self.ny - 1, int((max(y1, y2) + h - self.y0) / r) + 1)
        if i1 < i0 or j1 < j0: return
        X = self.x0 + (np.arange(i0, i1 + 1) + 0.5) * r; Y = self.y0 + (np.arange(j0, j1 + 1) + 0.5) * r
        X, Y = np.meshgrid(X, Y, indexing='ij')
        dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
        tt = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1) if L2 > 0 else 0.0
        d2 = (X - x1 - tt * dx) ** 2 + (Y - y1 - tt * dy) ** 2
        sub = R[i0:i1 + 1, j0:j1 + 1]; sub[d2 <= h * h] = val

    def make_planes(self, fills, layers):
        for ln in layers:
            P = np.zeros((self.nx, self.ny), dtype=bool)
            tmp = np.zeros((self.nx, self.ny), dtype=np.int32)
            for z in fills:
                if z['layer'] == ln: self._poly(tmp, z['contours'], 1)
            P |= tmp != 0
            self.plane[ln] = P

    def coverage(self, layer, size_mm=3.33):
        """share of copper (any net) on `layer` in a size_mm square around each pixel (cached)"""
        key = (layer, size_mm)
        if not hasattr(self, '_cov'): self._cov = {}
        if key not in self._cov:
            from scipy.ndimage import uniform_filter
            self._cov[key] = uniform_filter((self.own[layer] != 0).astype(np.float32), size=max(1, int(round(size_mm / self.r))), mode='constant')
        return self._cov[key]

    def coverage_plane(self, layer, size_mm):
        key = ('plane', layer, size_mm)
        if not hasattr(self, '_cov'): self._cov = {}
        if key not in self._cov:
            from scipy.ndimage import uniform_filter
            self._cov[key] = uniform_filter(self.plane[layer].astype(np.float32), size=max(1, int(round(size_mm / self.r))), mode='constant')
        return self._cov[key]

    def ij(self, x, y):
        i = np.clip(((np.asarray(x) - self.x0) / self.r).astype(int), 0, self.nx - 1)
        j = np.clip(((np.asarray(y) - self.y0) / self.r).astype(int), 0, self.ny - 1)
        return i, j

# ====================================================================================== copper measurement
class Copper:
    """Capacitance of the copper of one net from the board: tracks and pads sampled, vias counted."""
    DS = 0.05          # sample step along tracks and pads (mm)
    REACH = 1.5        # how far the side rays look for foreign copper (mm)

    def __init__(self, bd, ras, cpm):
        self.bd, self.ras, self.cpm = bd, ras, cpm
        self.six = bd['ncu'] >= 6
        self.via_c = A['via_6l'] if self.six else A['via_2l']
        self.tracks_by_net, self.vias_by_net, self.pads_by_net = {}, {}, {}
        for t in bd['tracks']: self.tracks_by_net.setdefault(t['net'], []).append(t)
        for v in bd['vias']: self.vias_by_net.setdefault(v['net'], []).append(v)
        for p in bd['pads']: self.pads_by_net.setdefault(p['net'], []).append(p)
        self.cache = {}

    def cases_at(self, layer, x, y):
        """[(stack-up case, weight array)] for each sample point. The reference copper is taken as the share of each
        layer covered with copper in a window about 3x its height above / below the track (the width over which the
        field of a strip reaches its reference), so a track that passes an antipad or a plane split is not counted as
        having no plane under it:
          6 layers, outer: adjacent plane (h 0.0994, window 0.3 mm) -> 'O6_plane'; else In2 (F.Cu: 0.4646, 1.4 mm ->
          'O6_far'; B.Cu: 0.5962 with In3 between, 1.8 mm -> 'O6_farB'); else the opposite outer layer (1.146, 3.4 mm)
          -> 'O6_opp'; else 'O6_air'.
          6 layers, In3: In2 above (0.1316, 0.4 mm) and In4 below (0.35, 1.05 mm) -> 'I6_both' / 'I6_in4' / 'I6_in2'.
          2 layers: opposite layer (1.11, 3.33 mm) -> 'O2_opp', else 'O2_air'."""
        R = self.ras; i, j = R.ij(x, y)
        if not self.six:
            opp = 'B.Cu' if layer == 'F.Cu' else 'F.Cu'
            w = R.coverage(opp)[i, j].astype(float)
            return [('O2_opp', w), ('O2_air', 1.0 - w)]
        if layer in ('F.Cu', 'B.Cu'):
            near = R.coverage_plane('In1.Cu' if layer == 'F.Cu' else 'In4.Cu', 0.3)[i, j].astype(float)
            far = R.coverage_plane('In2.Cu', 1.4 if layer == 'F.Cu' else 1.8)[i, j].astype(float)
            opp = R.coverage('B.Cu' if layer == 'F.Cu' else 'F.Cu', 3.4)[i, j].astype(float)
            rest = 1.0 - near
            return [('O6_plane', near), ('O6_far' if layer == 'F.Cu' else 'O6_farB', rest * far), ('O6_opp', rest * (1 - far) * opp),
                    ('O6_air', rest * (1 - far) * (1 - opp))]
        up = R.coverage_plane('In2.Cu', 0.4)[i, j].astype(float); dn = R.coverage_plane('In4.Cu', 1.05)[i, j].astype(float)
        return [('I6_both', up * dn), ('I6_in4', (1 - up) * dn + (1 - up) * (1 - dn)), ('I6_in2', up * (1 - dn))]

    def side_gaps(self, layer, code, x, y, nx, ny, half):
        """gap (mm) from the copper edge to the first foreign copper along +normal and -normal (inf if none)"""
        R = self.ras; own = R.own[layer]
        steps = np.arange(1, int(self.REACH / R.r) + 1) * R.r
        out = []
        for sgn in (1.0, -1.0):
            px = x[:, None] + sgn * nx[:, None] * (half[:, None] + steps[None, :])
            py = y[:, None] + sgn * ny[:, None] * (half[:, None] + steps[None, :])
            i, j = R.ij(px, py)
            v = own[i, j]
            foreign = (v != 0) & (v != code)
            first = np.where(foreign.any(axis=1), foreign.argmax(axis=1), -1)
            g = np.where(first >= 0, steps[np.maximum(first, 0)] - R.r / 2, np.inf)
            out.append(g)
        return out

    def _strip(self, layer, code, x, y, ux, uy, w, wt, own_pads=None, own_vias=None):
        """samples of a strip of width w along direction (ux, uy): returns (C_iso_sum, C_side_sum, length, info)"""
        keep = np.ones(len(x), dtype=bool)
        if own_pads:
            for p in own_pads:
                if layer not in p['polys']: continue
                a = math.radians(p['ang'])           # KiCad: y down, angle counter-clockwise on screen
                dx, dy = x - p['x'], y - p['y']
                lx = dx * math.cos(a) - dy * math.sin(a); ly = dx * math.sin(a) + dy * math.cos(a)
                keep &= ~((np.abs(lx) <= p['sx'] / 2) & (np.abs(ly) <= p['sy'] / 2))
        if own_vias:
            for v in own_vias:
                keep &= (x - v['x']) ** 2 + (y - v['y']) ** 2 > (v['dia'] / 2) ** 2
        x, y, wt = x[keep], y[keep], wt[keep]
        if len(x) == 0: return 0.0, 0.0, 0.0, {}
        cw = self.cases_at(layer, x, y)
        nx_, ny_ = np.full(len(x), -uy), np.full(len(x), ux)
        gl, gr = self.side_gaps(layer, code, x, y, nx_, ny_, np.full(len(x), w / 2))
        ciso = np.zeros(len(x)); cside = np.zeros(len(x)); info = {}
        for cs, wgt in cw:
            ciso += wgt * self.cpm.iso(cs, w)
            t = self.cpm.tab[cs]
            fs = lambda g: np.where(np.isfinite(g) & (g < t['gap'][-1]), np.interp(np.maximum(np.nan_to_num(g, posinf=9.0), t['gap'][0]), t['gap'], t['dside']), 0.0)
            cside += wgt * (fs(gl) + fs(gr))
            info[cs] = float((wt * wgt).sum())
        near = float(wt[(gl < 0.3) | (gr < 0.3)].sum())
        return float((ciso * wt).sum()), float((cside * wt).sum()), float(wt.sum()), dict(cases=info, near=near)

    def net(self, net):
        if net in self.cache: return self.cache[net]
        code = self.ras.code.get(net)
        res = dict(net=net, layers={}, pads=[], vias=0, c_iso=0.0, c_side=0.0)
        if code is None:
            res.update(c=(0.0, 0.0, 0.0), length=0.0); self.cache[net] = res; return res
        own_pads = self.pads_by_net.get(net, []); own_vias = self.vias_by_net.get(net, [])
        for t in self.tracks_by_net.get(net, []):
            L = math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1'])
            if L < 1e-6: continue
            n = max(1, int(math.ceil(L / self.DS)))
            s = (np.arange(n) + 0.5) / n
            ux, uy = (t['x2'] - t['x1']) / L, (t['y2'] - t['y1']) / L
            x = t['x1'] + s * (t['x2'] - t['x1']); y = t['y1'] + s * (t['y2'] - t['y1'])
            ci, cs, l, info = self._strip(t['layer'], code, x, y, ux, uy, t['w'], np.full(n, L / n), own_pads, own_vias)
            d = res['layers'].setdefault(t['layer'], dict(length=0.0, routed=0.0, c_iso=0.0, c_side=0.0, cases={}, near=0.0))
            d['routed'] += L; d['length'] += l; d['c_iso'] += ci; d['c_side'] += cs; d['near'] += info.get('near', 0.0)
            for k, v in info.get('cases', {}).items(): d['cases'][k] = d['cases'].get(k, 0.0) + v
            res['c_iso'] += ci; res['c_side'] += cs
        for p in own_pads:
            for ln in p['polys']:
                if ln not in self.ras.own: continue
                long_, short = max(p['sx'], p['sy']), min(p['sx'], p['sy'])
                a = math.radians(p['ang'])           # local x -> board (cos a, -sin a), local y -> (sin a, cos a)
                ex, ey = (math.cos(a), -math.sin(a)) if p['sx'] >= p['sy'] else (math.sin(a), math.cos(a))
                n = max(1, int(math.ceil(long_ / self.DS)))
                s = ((np.arange(n) + 0.5) / n - 0.5) * long_
                x = p['x'] + s * ex; y = p['y'] + s * ey
                scale = math.pi / 4 if p['shape'] == 0 else 1.0        # PAD_SHAPE_CIRCLE: disc instead of square
                ci, cs, l, info = self._strip(ln, code, x, y, ex, ey, short, np.full(n, long_ / n * scale))
                res['pads'].append(dict(pad=f"{p['ref']}.{p['num']}", layer=ln, c=ci + cs, size=(p['sx'], p['sy'])))
                res['c_iso'] += ci; res['c_side'] += cs
        res['vias'] = len(own_vias)
        tol, sh = A['copper_tol'], A['neighbour_min_share']
        vmin, vtyp, vmax = (res['vias'] * c for c in self.via_c)
        res['c'] = ((1 - tol) * (res['c_iso'] + sh * res['c_side']) + vmin, res['c_iso'] + res['c_side'] + vtyp,
                    (1 + tol) * (res['c_iso'] + res['c_side']) + vmax)
        res['length'] = sum(d['routed'] for d in res['layers'].values())
        self.cache[net] = res
        return res

# ====================================================================================== netlist (design module)
def load_design(name):
    if TOOLS not in sys.path: sys.path.insert(0, TOOLS)
    return importlib.import_module(name)

def rval(v):
    v = v.split()[0].lower().replace('ohm', '').replace('r', '')
    m = {'k': 1e3, 'm': 1e6}
    return float(v[:-1]) * m[v[-1]] if v[-1] in m else float(v)

def is_rail(D, n):
    return n in getattr(D, 'POWER_NETS', set()) or n in ('GND',) or re.match(r'^(\+|3V3_|VSYS_|V5_)', n or '') is not None

def kind_of(D, ref):
    lib, sym, val, fp, pos = D.PARTS[ref]
    if sym == 'R_Pack04': return 'array'
    if sym == 'R': return 'res'
    if sym == '2N7002': return 'fet'
    if sym == 'BAV99': return 'bav99'
    if sym == 'RP2350B': return 'qfn'
    if 'Pico' in sym or 'XIAO' in sym: return 'module'
    if sym.startswith('Famicom_CardEdge'): return 'edge'
    return sym

class Netlist:
    def __init__(self, D):
        self.D = D
        self.members = {}
        for ref, pins in D.NETS.items():
            for p, n in pins.items():
                if n: self.members.setdefault(n, []).append((ref, str(p)))

    def other_end(self, ref, pin):
        k = kind_of(self.D, ref)
        if k == 'array': return str(9 - int(pin))
        if k == 'res': return '2' if pin == '1' else '1'
        return None

    def node(self, net):
        """what sits on `net`: series elements to other nets, pull resistors, chip pins, FET pins, clamps, finger"""
        D = self.D
        out = dict(net=net, series={}, pulls=[], chips=[], fet_gate=[], fet_drain=[], clamps=[], finger=None, other=[])
        for ref, p in self.members.get(net, []):
            k = kind_of(D, ref)
            if k in ('array', 'res'):
                o = D.NETS[ref].get(self.other_end(ref, p))
                R = rval(D.PARTS[ref][2].split(' x')[0]) if k == 'array' else rval(D.PARTS[ref][2])     # arrays: the element value ('680 x4')
                if o is None: continue
                if is_rail(D, o): out['pulls'].append((ref, p, R, o))
                else: out['series'].setdefault(o, []).append((ref, p, R))
            elif k == 'fet':
                (out['fet_gate'] if p == '1' else out['fet_drain'] if p == '3' else out['other']).append(ref)
            elif k == 'bav99':
                if p == '3': out['clamps'].append(ref)
            elif k in ('qfn', 'module'): out['chips'].append((ref, p, k))
            elif k == 'edge': out['finger'] = p
            else: out['other'].append((ref, p, k))
        return out

    def console_signals(self):
        sig = []
        for pin, net in sorted(self.D.J1.items()):
            if not net or is_rail(self.D, net) or net.startswith('AUDIO'): continue
            sig.append((pin, net))
        return sig

def par(rs): return 1.0 / sum(1.0 / r for r in rs)

# ====================================================================================== node capacitance
class Nodes:
    """(min, typ, max) capacitance of a net: copper (+ open-connection bound) + pins + clamps (+ FET parasitics)."""
    def __init__(self, nl, cop, detour):
        self.nl, self.cop, self.detour = nl, cop, detour
        self.missing = {}

    def open_bound(self, net):
        """(n_missing, min, typ, max pF) for a net whose pads form more than one cluster on the board"""
        if net in self.missing: return self.missing[net]
        cl = self.cop.bd['clusters'].get(net, [])
        if len(cl) <= 1: self.missing[net] = (0, 0.0, 0.0, 0.0, []); return self.missing[net]
        pads = {f"{p['ref']}.{p['num']}": (p['x'], p['y']) for p in self.cop.pads_by_net.get(net, [])}
        pts = []
        for c in cl:
            q = []
            for it in c:
                if isinstance(it, str): q.append(pads[it])
                elif it[0] == 'via': q.append((it[1], it[2]))
                else: q += [(it[1], it[2]), (it[3], it[4])]
            pts.append(np.array(q))
        k = len(pts); inside = {0}; edges = []
        while len(inside) < k:
            best = None
            for a in inside:
                for b in range(k):
                    if b in inside: continue
                    d = np.sqrt(((pts[a][:, None, :] - pts[b][None, :, :]) ** 2).sum(-1)).min()
                    if best is None or d < best[0]: best = (d, a, b)
            edges.append(best[0]); inside.add(best[2])
        f_med, f_90, cpm_min, cpm_typ, cpm_max, v_typ = self.detour
        vt = self.cop.via_c
        L = sum(edges)
        lo = L * cpm_min
        ty = L * f_med * cpm_typ + len(edges) * v_typ * vt[1]
        hi = L * f_90 * cpm_max + len(edges) * 4 * vt[2]
        self.missing[net] = (len(edges), lo, ty, hi, edges)
        return self.missing[net]

    def copper(self, net):
        c = self.cop.net(net)['c']
        n, lo, ty, hi, _ = self.open_bound(net)
        return (c[0] + lo, c[1] + ty, c[2] + hi)

    def pins(self, net):
        """chip pins and clamps (FET parasitics are inside the FET models)"""
        nd = self.nl.node(net); lo = ty = hi = 0.0
        for ref, p, k in nd['chips']:
            c = A['pin_qfn'] if k == 'qfn' else A['pin_module']
            lo += c[0]; ty += c[1]; hi += c[2]
        for ref in nd['clamps']:
            lo += A['bav99'][0]; ty += A['bav99'][1]; hi += A['bav99'][2]
        return (lo, ty, hi)

    def total(self, net):
        a, b = self.copper(net), self.pins(net)
        return tuple(x + y for x, y in zip(a, b))

# ====================================================================================== 2N7002 model (rev G review)
# Port of the rev G review's FET model: EKV-style drain current, each corner calibrated to Id(Vgs=Vds=Vth) = 250 uA
# (JSCJ C8545 datasheet: Vth 1.0 / 1.6 / 2.5 V; gfs min 80 mS -> K 0.016 A/V^2 on paper; typical curves K ~0.4).
UT, NSLOPE = 0.02585, 1.3
def _l1pe(x): return np.logaddexp(0.0, x)
def ids(vg, vd, vs, vt0, k):
    b = k * NSLOPE; vp = (vg - vt0) / NSLOPE
    return 2 * NSLOPE * b * UT * UT * (_l1pe((vp - vs) / (2 * UT)) ** 2 - _l1pe((vp - vd) / (2 * UT)) ** 2)
def _calibrate(vth, k, itest=250e-6):
    lo, hi = vth - 1.5, vth + 0.5
    for _ in range(80):
        mid = (lo + hi) / 2
        if float(ids(vth, vth, 0.0, mid, k)) > itest: lo = mid
        else: hi = mid
    return (lo + hi) / 2
CORNERS = {n: (_calibrate(v, k), k, v) for n, v, k in (('typ', 1.6, 0.4), ('typcurve', 2.0, 0.4), ('hi_real', 2.5, 0.1),
                                                     ('hi_paper', 2.5, 0.016), ('lo', 1.0, 0.4))}
CAPS = {'min': (15.0, 4.0, 11.0), 'typ': (25.0, 8.0, 22.0), 'max': (45.0, 15.0, 65.0)}     # Cgs, Cgd, Cds (pF) at 0-3.3 V
DT = 0.01e-9

def _cross(ts, V, level, rising, t_from):
    """first crossing time per column of V (len(ts) x n) after t_from (per column); nan if none"""
    out = np.full(V.shape[1], np.nan)
    for c in range(V.shape[1]):
        v = V[:, c]; m = ts >= t_from[c]
        idx = np.nonzero(m)[0]
        if len(idx) < 2: continue
        v = v[idx[0] - 1 if idx[0] > 0 else 0:]; tt = ts[idx[0] - 1 if idx[0] > 0 else 0:]
        hit = np.nonzero((v[:-1] < level) & (v[1:] >= level))[0] if rising else np.nonzero((v[:-1] > level) & (v[1:] <= level))[0]
        if len(hit): out[c] = tt[hit[0] + 1]
    return out

def sim_inverter(runs):
    """runs: list of dicts(corner, caps, cext [pF], cg_ext [pF], rp, vp, rg, voh, vol, tr, tf, rs_hi, rs_lo, width,
    gate_pull=(R, V) or None, totem, branches=[(R ohm, C pF), ...]). One console pulse high->low (select) at 50 ns, back
    high after `width`. The console source drives the gate node through rs + rg (a totem pole only sources up to its VOH;
    above it only gate_pull lifts the node); each branch is an RC node behind its resistor on the gate node.
    Returns per run: sel20, sel16 (drain rising after the console edge crosses 1.5 V), des08, des13, vmax, vlow_end, and
    per branch sel13 / sel08 (branch falling) and des16 / des20 (branch rising after the console edge rises through
    min(1.5, VOH - 0.2))."""
    n = len(runs)
    g = lambda key, d=None: np.array([r.get(key, d) for r in runs], dtype=float)
    vt0 = np.array([CORNERS[r['corner']][0] for r in runs]); kk = np.array([CORNERS[r['corner']][1] for r in runs])
    cgs = np.array([CAPS[r['caps']][0] if isinstance(r['caps'], str) else r['caps'][0] for r in runs]) * 1e-12
    cgd = np.array([CAPS[r['caps']][1] if isinstance(r['caps'], str) else r['caps'][1] for r in runs]) * 1e-12
    cds = np.array([CAPS[r['caps']][2] if isinstance(r['caps'], str) else r['caps'][2] for r in runs]) * 1e-12
    cd = cds + g('cext') * 1e-12; cgx = g('cg_ext', 0.0) * 1e-12
    rp, vpp, rg = g('rp'), g('vp', 3.3), g('rg', 0.0)
    voh, vol, tr, tf = g('voh'), g('vol', 0.25), g('tr', 10e-9), g('tf', 6e-9)
    rsh, rsl, width = g('rs_hi', 120.0), g('rs_lo', 40.0), g('width', 349.2e-9)
    gpr = np.array([r['gate_pull'][0] if r.get('gate_pull') else np.inf for r in runs]); gpv = np.array([r['gate_pull'][1] if r.get('gate_pull') else 0.0 for r in runs])
    totem = np.array([bool(r.get('totem')) for r in runs])
    nb = max([len(r.get('branches') or ()) for r in runs] + [1])
    RB = np.full((n, nb), 1e12); CB = np.full((n, nb), 1e-12)        # unused slots: 1 pF behind 1 Tohm (inert)
    for c, r in enumerate(runs):
        for k, (rb, cbp) in enumerate(r.get('branches') or ()): RB[c, k] = rb; CB[c, k] = cbp * 1e-12
    t1 = 50e-9; t2 = t1 + width
    tend = float((t2 + 300e-9).max())
    vg = voh.copy(); vg[totem & np.isfinite(gpr)] = gpv[totem & np.isfinite(gpr)]
    VB = np.repeat(vg[:, None], nb, axis=1)
    vd = np.zeros(n)
    for _ in range(20000): vd += ((vpp - vd) / rp - ids(vg, vd, 0.0, vt0, kk)) / (cd + cgd) * DT
    a11, a12, a21, a22 = cgs + cgd + cgx, -cgd, -cgd, cd + cgd
    det = a11 * a22 - a12 * a21
    nsteps = int(tend / DT); rec = 10
    TS = np.empty(nsteps // rec + 1); VD = np.empty((nsteps // rec + 1, n)); VI = np.empty_like(VD); VBR = np.empty((nsteps // rec + 1, n, nb))
    t = 0.0; ri = 0
    for i in range(nsteps):
        # console source: high, falls at t1 (tf), low until t2, rises (tr)
        vi = np.where(t <= t1, voh, np.where(t <= t1 + tf, voh + (vol - voh) * (t - t1) / tf,
                      np.where(t <= t2, vol, np.where(t <= t2 + tr, vol + (voh - vol) * (t - t2) / tr, voh))))
        low = (t >= t1) & (t < t2)
        ig = np.where(low, (vi - vg) / (rsl + rg), np.where(totem, np.maximum(0.0, vi - vg) / (rsh + rg), (vi - vg) / (rsh + rg)))
        ig = ig + np.where(np.isfinite(gpr), (gpv - vg) / np.where(np.isfinite(gpr), gpr, 1.0), 0.0)
        ib = (vg[:, None] - VB) / RB
        ig = ig - ib.sum(axis=1)
        idr = (vpp - vd) / rp - ids(vg, vd, 0.0, vt0, kk)
        dvg = (ig * a22 - a12 * idr) / det; dvd = (a11 * idr - a21 * ig) / det
        vg = vg + dvg * DT; vd = vd + dvd * DT; VB = VB + ib / CB * DT; t += DT
        if i % rec == 0: TS[ri] = t; VD[ri] = vd; VI[ri] = vi; VBR[ri] = VB; ri += 1
    TS, VD, VI, VBR = TS[:ri], VD[:ri], VI[:ri], VBR[:ri]
    tsel = _cross(TS, VI, 1.5, False, np.zeros(n))
    tdes = np.array([_cross(TS, VI[:, [c]], min(1.5, voh[c] - 0.2), True, np.array([t2[c] - 1e-9]))[0] for c in range(n)])
    out = []
    s20 = _cross(TS, VD, 2.0, True, tsel); s16 = _cross(TS, VD, 1.6, True, tsel)
    d08 = _cross(TS, VD, 0.8, False, tdes); d13 = _cross(TS, VD, 1.3, False, tdes)
    br = [dict(sel13=_cross(TS, VBR[:, :, k], 1.3, False, tsel), sel08=_cross(TS, VBR[:, :, k], 0.8, False, tsel),
               des16=_cross(TS, VBR[:, :, k], 1.6, True, tdes), des20=_cross(TS, VBR[:, :, k], 2.0, True, tdes)) for k in range(nb)]
    for c in range(n):
        m = (TS > t1) & (TS < t2[c])
        nbc = len(runs[c].get('branches') or ())
        bout = [dict(sel13=(br[k]['sel13'][c] - tsel[c]) * 1e9, sel08=(br[k]['sel08'][c] - tsel[c]) * 1e9,
                     des16=(br[k]['des16'][c] - tdes[c]) * 1e9, des20=(br[k]['des20'][c] - tdes[c]) * 1e9) for k in range(nbc)]
        out.append(dict(sel20=(s20[c] - tsel[c]) * 1e9, sel16=(s16[c] - tsel[c]) * 1e9, des08=(d08[c] - tdes[c]) * 1e9,
                        des13=(d13[c] - tdes[c]) * 1e9, vmax=float(VD[m, c].max()), vlow_end=float(VD[-1, c]), branches=bout))
    return out

def sim_nor(runs):
    """WS_D = M2 AND NOT R/W (Q1: M2 -> M2n with rn to 5 V; Q3: M2n -> WS_D with rw to 3.3 V; Q2 off). runs: dicts(c1, c3,
    caps, cn_ext, cw_ext, cg_ext, rn, rw, voh, period, high, tedge, rs). Measured on the second cycle:
    start = M2 rising (1.5 V) -> WS_D 2.0 V [1.6 V]; end = M2 falling -> WS_D 0.8 V [1.3 V]."""
    n = len(runs)
    g = lambda key, d=None: np.array([r.get(key, d) for r in runs], dtype=float)
    vt1 = np.array([CORNERS[r['c1']][0] for r in runs]); k1 = np.array([CORNERS[r['c1']][1] for r in runs])
    vt3 = np.array([CORNERS[r['c3']][0] for r in runs]); k3 = np.array([CORNERS[r['c3']][1] for r in runs])
    cg = np.array([CAPS[r['caps']] for r in runs]) * 1e-12
    cgs, cgd, cds = cg[:, 0], cg[:, 1], cg[:, 2]
    cnx, cwx, cgx = g('cn_ext') * 1e-12, g('cw_ext') * 1e-12, g('cg_ext', 0.0) * 1e-12
    rn, rw, voh = g('rn'), g('rw'), g('voh')
    period, high, tedge, rs = 558.73e-9, g('high', 349.2e-9), 8e-9, g('rs', 50.0)
    low = period - high
    cycles = 2
    tend = float((low + cycles * period).max())
    Ainv = np.empty((n, 3, 3))
    for c in range(n):
        M = np.array([[cgs[c] + cgd[c] + cgx[c], -cgd[c], 0.0],
                      [-cgd[c], cds[c] + cgs[c] + 2 * cgd[c] + cnx[c], -cgd[c]],
                      [0.0, -cgd[c], 2 * cds[c] + 2 * cgd[c] + cwx[c]]])
        Ainv[c] = np.linalg.inv(M)
    vg, vn, vw = np.full(n, 0.15), np.full(n, 5.0), np.zeros(n)
    nsteps = int(tend / DT); rec = 10
    TS = np.empty(nsteps // rec + 1); VM = np.empty((nsteps // rec + 1, n)); VW = np.empty_like(VM); VN = np.empty_like(VM)
    t = 0.0; ri = 0
    for i in range(nsteps):
        # M2: low until `low`, rises in tedge, high for `high`, falls; repeat every period
        tc = t - low; k = np.floor(np.maximum(tc, 0) / period); ph = tc - k * period
        vi = np.where(tc < 0, 0.15, np.where(ph < tedge, 0.15 + (voh - 0.15) * ph / tedge,
                      np.where(ph < high, voh, np.where(ph < high + tedge, voh + (0.15 - voh) * (ph - high) / tedge, 0.15))))
        vi = np.where(k >= cycles, 0.15, vi)
        b0 = (vi - vg) / rs
        b1 = (5.0 - vn) / rn - ids(vg, vn, 0.0, vt1, k1)
        b2 = (3.3 - vw) / rw - ids(vn, vw, 0.0, vt3, k3)
        vg = vg + (Ainv[:, 0, 0] * b0 + Ainv[:, 0, 1] * b1 + Ainv[:, 0, 2] * b2) * DT
        vn = vn + (Ainv[:, 1, 0] * b0 + Ainv[:, 1, 1] * b1 + Ainv[:, 1, 2] * b2) * DT
        vw = vw + (Ainv[:, 2, 0] * b0 + Ainv[:, 2, 1] * b1 + Ainv[:, 2, 2] * b2) * DT
        t += DT
        if i % rec == 0: TS[ri] = t; VM[ri] = vi; VN[ri] = vn; VW[ri] = vw; ri += 1
    TS, VM, VN, VW = TS[:ri], VM[:ri], VN[:ri], VW[:ri]
    t_up = low + period; t_dn = t_up + high
    tu = _cross(TS, VM, 1.5, True, t_up - 1e-9); td = _cross(TS, VM, 1.5, False, t_dn - 1e-9)
    s20 = _cross(TS, VW, 2.0, True, tu); s16 = _cross(TS, VW, 1.6, True, tu)
    e08 = _cross(TS, VW, 0.8, False, td); e13 = _cross(TS, VW, 1.3, False, td)
    out = []
    for c in range(n):
        m = (TS > tu[c]) & (TS < td[c])
        out.append(dict(start20=(s20[c] - tu[c]) * 1e9, start16=(s16[c] - tu[c]) * 1e9, end08=(e08[c] - td[c]) * 1e9,
                        end13=(e13[c] - td[c]) * 1e9, ws_max=float(VW[m, c].max()), m2n_min=float(VN[m, c].min())))
    return out

# ====================================================================================== bus models
def ln(a, b): return math.log(a / b)

def ppu_read_lumped(R, c_rd_pf, c_bus_pf, worst, r_rd=1000.0):
    """rev G's PPU-read budget: /RD through r_rd (1k) into the RD_D node, PIO, then the data line
    through R into the lumped bus. Driver resistances: A['r_rd_src'] (PPU /RD), A['r_drv'] / A['r_drv_hi'] (RP2350
    low / high). Returns dict(t_rd, pio, fall, rise, total, vfin) in ns / V."""
    i = 1 if worst else 0
    vth_rd, vil, iil, pio = A['rd_vth'][i], A['console_vil'][i], A['iil'][i], A['pio'][i]
    t_rd = (r_rd + A['r_rd_src'][i]) * c_rd_pf * 1e-12 * ln(A['rd_from'] - A['rd_final'], vth_rd - A['rd_final']) * 1e9
    vfin = iil * R + A['v_drv_low']
    fall = (R + A['r_drv'][i]) * c_bus_pf * 1e-12 * ln(A['v_start_fall'] - vfin, vil - vfin) * 1e9
    rise = (R + A['r_drv_hi'][i]) * c_bus_pf * 1e-12 * ln(A['v_rise_to'] - A['v_rise_from'], A['v_rise_to'] - A['v_ih']) * 1e9
    return dict(t_rd=t_rd, pio=pio, fall=fall, rise=rise, total=t_rd + pio + max(fall, rise), vfin=vfin)

def rc_network_cross(nodes, res, src, inj, v0, node, vth, falling=True):
    """Linear RC network: nodes {name: C pF}, res [(a, b, R ohm)] (b may be a source name), src {name: V}, inj {node: A}
    (current into the node), all nodes start at v0. Returns the time (ns) at which `node` crosses vth, and the final level.
    Exact solution by the generalised eigenproblem G phi = lambda C phi."""
    import scipy.linalg as sl
    names = list(nodes); ix = {n: k for k, n in enumerate(names)}; m = len(names)
    G = np.zeros((m, m)); bvec = np.zeros(m)
    for a, b, R in res:
        g = 1.0 / R
        if a in ix and b in ix:
            G[ix[a], ix[a]] += g; G[ix[b], ix[b]] += g; G[ix[a], ix[b]] -= g; G[ix[b], ix[a]] -= g
        else:
            n_, s_ = (a, b) if a in ix else (b, a)
            G[ix[n_], ix[n_]] += g; bvec[ix[n_]] += g * src[s_]
    for n_, I in inj.items(): bvec[ix[n_]] += I
    C = np.diag([nodes[n] * 1e-12 for n in names])
    vinf = np.linalg.solve(G, bvec)
    lam, phi = sl.eigh(G, C)                   # phi^T C phi = I
    coef = phi.T @ C @ (np.full(m, v0) - vinf)
    k = ix[node]
    def v(t): return vinf[k] + float((phi[k] * coef * np.exp(-lam * t)).sum())
    lo, hi = 0.0, 5e-6
    if (v(hi) > vth) == falling: return float('nan'), vinf[k]
    for _ in range(100):
        mid = (lo + hi) / 2
        if (v(mid) > vth) == falling: lo = mid
        else: hi = mid
    return (lo + hi) / 2 * 1e9, vinf[k]

def ppu_read_network(R, c_rd_pf, c_drv_pf, c_f_pf, c_other_pf, worst, r_other, r_rd=1000.0):
    """Same chain, but the data line as a network: driver node (pin + its branch copper) - R - finger node (console +
    finger copper, 74LS373 current) - r_other - the other chip's branch node (exact linear solution)."""
    i = 1 if worst else 0
    vil, iil = A['console_vil'][i], A['iil'][i]
    base = ppu_read_lumped(R, c_rd_pf, c_f_pf, worst, r_rd)
    nodes = {'D': c_drv_pf, 'F': c_f_pf}
    res = [('D', 'S', A['r_drv'][i]), ('D', 'F', R)]
    if c_other_pf > 0: nodes['B'] = c_other_pf; res.append(('F', 'B', r_other))
    fall, vfin = rc_network_cross(nodes, res, {'S': A['v_drv_low']}, {'F': iil}, A['v_start_fall'], 'F', vil, True)
    # rising edge: from 0.3 V, driver to 3.2 V (rev G) through its high-side resistance, no LS current
    res[0] = ('D', 'S', A['r_drv_hi'][i])
    rise, _ = rc_network_cross(nodes, res, {'S': A['v_rise_to']}, {}, A['v_rise_from'], 'F', A['v_ih'], False)
    return dict(t_rd=base['t_rd'], pio=base['pio'], fall=fall, rise=rise, total=base['t_rd'] + base['pio'] + max(fall, rise), vfin=vfin)

def rc_delay(R, c_pf, v0, vinf, vth):
    """single pole: time (ns) for R*C from v0 towards vinf to cross vth"""
    if (vth - vinf) * (v0 - vinf) <= 0: return float('nan')
    return R * c_pf * 1e-12 * ln(v0 - vinf, vth - vinf) * 1e9

# ====================================================================================== the rev G run sets
RSEL_BASE = dict(rp=1000.0, vp=3.3, rg=0.0, vol=0.25, tr=10e-9, tf=6e-9, rs_hi=120.0, rs_lo=40.0, width=349.2e-9,
                 gate_pull=(2200.0, 5.0), totem=True)
PWS_BASE = dict(rp=1100.0, vp=3.3, rg=1000.0, vol=0.15, tr=12e-9, tf=8e-9, rs_hi=300.0, rs_lo=100.0, width=186.24e-9)
NOR_BASE = dict(rn=1000.0, rw=1000.0)

def rsel_runs(ext, cg_ext=(0.0, 0.0, 0.0), branches=((), (), ())):
    """ext: (min, typ, max) external drain capacitance, cg_ext: on the gate (finger) node, branches: per caps corner
    [(R, C)] behind the finger; rev G corner set (typ = typ caps, typcurve FET, /ROMSEL 3.4 V)"""
    runs, keys = [], []
    for ci, caps in enumerate(('min', 'typ', 'max')):
        for corner in ('typ', 'typcurve', 'hi_real', 'hi_paper'):
            for voh in (2.7, 3.0, 3.4):
                if caps != 'typ' and corner not in ('typcurve', 'hi_paper'): continue
                runs.append(dict(RSEL_BASE, corner=corner, caps=caps, cext=ext[ci], cg_ext=cg_ext[ci], voh=voh, branches=list(branches[ci])))
                keys.append((caps, corner, voh))
    return keys, runs

def pws_runs(ext, cg_ext=(0.0, 0.0, 0.0)):
    runs, keys = [], []
    for ci, caps in enumerate(('min', 'typ', 'max')):
        for corner, voh in (('lo', 4.5), ('typ', 4.0), ('typcurve', 4.0), ('typcurve', 3.5), ('hi_real', 3.5), ('hi_paper', 3.5)):
            if caps != 'typ' and corner not in ('lo', 'typcurve'): continue
            runs.append(dict(PWS_BASE, corner=corner, caps=caps, cext=ext[ci], cg_ext=cg_ext[ci], voh=voh)); keys.append((caps, corner, voh))
    return keys, runs

def nor_runs(cw, cn, cg=(0.0, 0.0, 0.0), versions=tuple(VERSIONS)):
    """rev G's corner set (Q1 corner, Q3 corner, M2 high level) for every CPU version (its M2 high time)"""
    runs, keys = [], []
    for ver in versions:
        high = T_CYC * (1 - VERSIONS[ver][0]) * 1e-9
        for ci, caps in enumerate(('min', 'typ', 'max')):
            for c1, c3, voh in (('typ', 'typ', 4.0), ('typcurve', 'typcurve', 4.0), ('hi_real', 'hi_real', 3.5), ('hi_paper', 'lo', 3.3),
                                ('hi_paper', 'lo', 3.1), ('hi_paper', 'hi_paper', 3.3), ('lo', 'lo', 4.5)):
                if caps != 'typ' and (c1, c3) != ('typcurve', 'typcurve'): continue
                runs.append(dict(NOR_BASE, c1=c1, c3=c3, caps=caps, cw_ext=cw[ci], cn_ext=cn[ci], cg_ext=cg[ci], voh=voh, high=high))
                keys.append((ver, caps, c1, c3, voh))
    return keys, runs

def summarize_strobes(rk, rr, pk, pr, nk, nr, raw_names=()):
    """the rev G table entries from the run results, plus every corner"""
    R = dict(zip(rk, rr)); P = dict(zip(pk, pr)); N = dict(zip(nk, nr))
    fin = lambda v: v if np.isfinite(v) else 1e9
    s = {}
    s['rsel_rise'] = (R[('typ', 'typcurve', 3.4)]['sel20'], R[('min', 'typcurve', 3.4)]['sel20'], R[('max', 'typcurve', 3.4)]['sel20'])
    s['rsel_rise_all'] = (min(v['sel20'] for v in rr), max(v['sel20'] for v in rr), max(R.items(), key=lambda kv: fin(kv[1]['sel20']))[0])
    s['rsel_fall'] = (R[('typ', 'typcurve', 3.4)]['des08'], max(v['des08'] for k, v in R.items() if k[0] == 'typ'), max(v['des08'] for v in rr))
    s['rsel_low_end'] = max(v['vlow_end'] for v in rr)
    s['rsel_fall_corner'] = max(R.items(), key=lambda kv: fin(kv[1]['des08']))[0]
    s['rsel_corners'] = [(k, v['sel20'], v['des08']) for k, v in R.items()]
    # raw /ROMSEL at each branch behind its 1k (same transient): typ = rev G's typ run, worst = slowest of all corners
    s['raw'] = {}
    for i, name in enumerate(raw_names):
        typ = R[('typ', 'typcurve', 3.4)]['branches'][i]
        ws = max(R.items(), key=lambda kv: fin(kv[1]['branches'][i]['sel08'])); wd = max(R.items(), key=lambda kv: fin(kv[1]['branches'][i]['des20']))
        s['raw'][name] = dict(sel=(typ['sel13'], ws[1]['branches'][i]['sel08']), des=(typ['des16'], wd[1]['branches'][i]['des20']),
                              sel_corner=ws[0], des_corner=wd[0])
    t = [P[k] for k in pk if k[0] == 'typ' and k[1:] in (('lo', 4.5), ('typ', 4.0), ('typcurve', 4.0), ('typcurve', 3.5))]
    s['pws_rise'] = (min(v['sel20'] for v in t), max(v['sel20'] for v in t))
    s['pws_peak'] = (min(v['vmax'] for v in t), max(v['vmax'] for v in t))
    s['pws_above'] = min(186.24 - v['sel20'] + v['des08'] for v in t)
    mx = [P[k] for k in pk if k[0] == 'max']
    s['pws_max_caps'] = (max(v['sel20'] for v in mx), min(v['vmax'] for v in mx))
    s['pws_corners'] = [(k, v['sel20'], v['vmax'], 186.24 - v['sel20'] + v['des08'] if np.isfinite(v['sel20']) else float('nan')) for k, v in P.items()]
    # WS_D, E/G/H: rev G's range = min caps .. max caps with typical-curve FETs, M2 4.0 V; 'ws_rise_all' = every corner
    E = {k[1:]: v for k, v in N.items() if k[0] == 'E/G/H'}
    s['ws_rise'] = (E[('typ', 'typ', 'typ', 4.0)]['start20'], E[('min', 'typcurve', 'typcurve', 4.0)]['start20'], E[('max', 'typcurve', 'typcurve', 4.0)]['start20'])
    s['ws_rise_all'] = (min(v['start20'] for v in E.values()), max(v['start20'] for v in E.values()))
    s['ws_fall'] = (E[('typ', 'typ', 'typ', 4.0)]['end08'], min(v['end08'] for v in E.values()), max(v['end08'] for v in E.values()))
    s['ws_max'] = min(v['ws_max'] for v in nr)
    s['ws_corners'] = [(k, v['start20'], v['end08'], v['ws_max']) for k, v in N.items()]
    ws = {}
    for k, v in N.items(): ws.setdefault(k[0], []).append((k[1:], v['start20']))
    s['windows'] = capture_windows(ws)
    s['windows_revg'] = capture_windows({'E/G/H': [(k, v['start20']) for k, v in E.items() if k[1:3] == ('typcurve', 'typcurve') and k[3] == 4.0]})
    return s

def capture_windows(ws):
    """write-data capture delay d after WS_D rises (rev G's write budget). ws: {CPU version: [(corner,
    WS_D rise ns)]}. On every console (corner c) the data must be valid (T/2 + 100 ns TMDS - M2 low) at t_ws(c) + d and
    not yet gone (M2 high + 30 ns THW): d_min = valid - fastest WS_D, d_max = gone - slowest WS_D."""
    out = {}
    for name, rows in ws.items():
        share, fw = VERSIONS[name]; low = T_CYC * share; high = T_CYC - low
        valid, gone = T_CYC / 2 + 100 - low, high + 30
        rows = [(c, t) for c, t in rows if np.isfinite(t)]
        fast = min(rows, key=lambda r: r[1]); slow = max(rows, key=lambda r: r[1])
        lo, hi = valid - fast[1], gone - slow[1]
        out[name] = dict(lo=lo, hi=hi, fast=fast, slow=slow, firmware=fw, margin=min(fw[0] - lo, hi - fw[1]),
                         fail=[(c, valid - t, gone - t) for c, t in rows if fw[0] < valid - t or fw[1] > gone - t])
    return out

REVG_DRIVERS = {'r_drv': (40.0, 40.0), 'r_drv_hi': (40.0, 40.0), 'r_rd_src': (40.0, 40.0)}      # rev G: 40 ohm everywhere

def selftest(log=print):
    """The models fed with rev G's published inputs (no board) must give rev G's raw simulation output
    (RSEL_D 45.6 (21.0 .. 106.6), WS_D 79.8 / 43.2, window 129 .. 187, PPU 500 ohm 158 ns); the RC-network solver must equal the
    closed form on one node. Returns the numbers and a list of failed checks."""
    t0 = time.time(); bad = []
    rk, rr = rsel_runs((5.6, 14.0, 24.0)); pk, pr = pws_runs((5.6, 14.0, 24.0)); nk, nr = nor_runs((6.0, 15.0, 26.0), (2.0, 2.0, 2.0), versions=('E/G/H',))
    rr, pr, nr = sim_inverter(rr), sim_inverter(pr), sim_nor(nr)
    s = summarize_strobes(rk, rr, pk, pr, nk, nr)
    out = {'strobes': s}
    log("== self-test: rev G's models with rev G's inputs (EXT 5.6 / 14 / 24 pF, WS_D 6 / 15 / 26 pF, M2n 2 pF, 40 ohm drivers) ==")
    log(f"   RSEL_D rise (1k, 2.2k to +5V):  {s['rsel_rise'][0]:6.1f} ns ({s['rsel_rise'][1]:.1f} .. {s['rsel_rise'][2]:.1f})   rev G 45.6 (21.0 .. 106.6)")
    log(f"   RSEL_D fall to 0.8 V:            typ {s['rsel_fall'][0]:.1f}, max over corners {s['rsel_fall'][2]:.1f} ns   rev G <= 55 (typ caps), <= 103 (max caps)")
    log(f"   WS_D rise after M2 rises:        {s['ws_rise'][0]:6.1f} ns ({s['ws_rise'][1]:.1f} .. {s['ws_rise'][2]:.1f})   rev G 79.8 (40.8 .. 191.8)")
    log(f"   WS_D fall after M2 falls:        {s['ws_fall'][0]:6.1f} ns ({s['ws_fall'][1]:.1f} .. {s['ws_fall'][2]:.1f})   rev G 43.2 (23.1 .. 112.0)")
    log(f"   PWS_D (1.1k) reaches 2.0 V:      {s['pws_rise'][0]:.1f} .. {s['pws_rise'][1]:.1f} ns, peak {s['pws_peak'][0]:.2f} .. {s['pws_peak'][1]:.2f} V   rev G 69 .. 102 ns, 3.0 .. 3.1 V")
    w = s['windows_revg']['E/G/H']
    log(f"   capture-delay window after WS_D (rev G's corners): E/G/H {w['lo']:.0f} .. {w['hi']:.0f} ns   rev G 129 .. 187")
    for got, ref in ((s['rsel_rise'], (45.6, 21.0, 106.6)), (s['ws_rise'], (79.8, 40.8, 191.8)), (s['ws_fall'], (43.2, 23.1, 112.0)),
                     ((w['lo'], w['hi']), (129.0, 187.0))):
        if max(abs(x - y) for x, y in zip(got, ref)) > 1.0: bad.append(f'self-test: {got} against rev G {ref}')
    keep = {k: A[k] for k in REVG_DRIVERS}; A.update(REVG_DRIVERS)
    try:
        for R, pub in ((1000.0, PUBLISHED['ppu1k']), (500.0, PUBLISHED['ppu500'])):
            ty = ppu_read_lumped(R, 20.0, 35.0, False); wo = ppu_read_lumped(R, 30.0, 60.0, True)
            log(f'   PPU read {R:4.0f} ohm (Crd 20/30, Cbus 35/60 pF): typ {ty["total"]:6.1f} ns, worst {wo["total"]:6.1f} ns (low level {wo["vfin"]:.2f} V)   rev G about {pub[0]:.0f} / {pub[1]:.0f}')
            out[f'ppu{int(R)}'] = (ty['total'], wo['total'])
            if abs(wo['total'] - pub[1]) > 1.0: bad.append(f'self-test: PPU read {R:.0f} ohm worst {wo["total"]:.1f} against rev G {pub[1]}')
    finally:
        A.update(keep)
    # RC-network solver against the closed form: one node of 30 pF behind 1040 ohm, 4.0 V -> 0.05 V, crossing 0.8 V
    tn, _ = rc_network_cross({'F': 30.0}, [('F', 'S', 1040.0)], {'S': 0.05}, {}, 4.0, 'F', 0.8, True)
    tc = rc_delay(1040.0, 30.0, 4.0, 0.05, 0.8)
    log(f'   RC-network solver on one node: {tn:.3f} ns, closed form {tc:.3f} ns')
    if abs(tn - tc) > 0.01: bad.append(f'self-test: network solver {tn:.3f} ns against closed form {tc:.3f} ns')
    log(f'   ({time.time() - t0:.0f} s) ' + ('all checks pass' if not bad else 'FAILED: ' + '; '.join(bad)))
    out['failed'] = bad
    return out

# ====================================================================================== board analysis
OPTIONAL = {'design_revg': {'U4', 'U5'}}           # modules rev G may leave out (its min corner: one pad on RSEL_D)

def mst_len(pts):
    pts = np.asarray(pts, dtype=float); k = len(pts)
    if k < 2: return 0.0
    inside = [0]; rest = list(range(1, k)); tot = 0.0
    while rest:
        d = np.sqrt(((pts[inside][:, None, :] - pts[rest][None, :, :]) ** 2).sum(-1))
        a, b = np.unravel_index(d.argmin(), d.shape); tot += d[a, b]; inside.append(rest.pop(b))
    return tot

class Analysis:
    def __init__(self, board, design, work, log=print):
        self.log = log; self.design = design; self.board = os.path.abspath(board)
        log(f'== {os.path.basename(board)} with {design} ==')
        self.D = load_design(design); self.nl = Netlist(self.D)
        copy = board_copy(board, work)
        self.bd = read_board(copy)
        fills = get_fills(copy, work, log)
        self.ras = Raster(self.bd, fills, log=log)
        self.six = self.bd['ncu'] >= 6
        if self.six: self.ras.make_planes(fills, ['In1.Cu', 'In2.Cu', 'In4.Cu'])
        cases = [k for k in CASES if k[:2] in ('O6', 'I6')] if self.six else ['O2_opp', 'O2_air']
        self.cpm = CPerMM(c_tables(os.path.join(work, 'cpul_cache.json'), cases, log))
        self.cop = Copper(self.bd, self.ras, self.cpm)
        self.optional = OPTIONAL.get(design, set())
        self.sigs = self._signals_raw()
        self.detour = self._detour()
        self.nodes = Nodes(self.nl, self.cop, self.detour)
        self.warnings = self._checks()

    def console_nets(self):
        return set(self.sigs) | self.branch_nets() | {'RSEL_D', 'WS_D', 'M2n', 'PWS_D', 'PWE_G'}

    def _checks(self):
        """self-checks against a board that does not match the design module (the tool would otherwise measure the
        wrong copper silently): track width of the console nets against the design's TRACK, every design pin of a
        console net on a board pad of that net and vice versa, series values of the data lines equal on every bit"""
        W = []
        pad_net = {(p['ref'], str(p['num'])): p['net'] for p in self.bd['pads']}
        on_board = {r for r, p in pad_net}
        wl = {}
        for t in self.bd['tracks']:
            if t['net'] in self.console_nets():
                wl[round(t['w'], 3)] = wl.get(round(t['w'], 3), 0.0) + math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1'])
        self.console_widths = dict(sorted(wl.items()))
        track = getattr(self.D, 'TRACK', None)
        if wl and track is not None:
            main = max(wl, key=wl.get)
            if abs(main - track) > 0.001:
                W.append(f'console nets are mostly {main} mm wide ({wl[main]:.0f} mm), the design module says TRACK = {track}: board and design do not match')
        for n in sorted(self.console_nets()):
            if n not in self.bd['nets']:
                W.append(f'design net {n} is not on the board (its copper counts as 0)'); continue
            want = {(r, str(p)) for r, p in self.nl.members.get(n, []) if r in on_board}
            for r, p in sorted(want):
                if pad_net.get((r, p)) != n: W.append(f'{r}.{p}: design net {n}, board net {pad_net.get((r, p))!r}')
            for (r, p), bn in pad_net.items():
                if bn == n and (r, p) not in want: W.append(f'{r}.{p}: board net {n}, not in the design net')
        for pre, mods in (('PPU_D', ('U2', 'U5')), ('CPU_D', ('U1', 'U4', 'U3'))):
            for m in mods:
                vals = {round(R, 1) for b in range(8) if f'{pre}{b}' in self.sigs for B, R, el in self.branches(f'{pre}{b}') if m in self.chip_of(B)}
                if len(vals) > 1: W.append(f'{pre}0-7 to {m}: series values differ between bits: {sorted(vals)} ohm')
        return W

    def _signals_raw(self):
        out = {}
        for pin, F in self.nl.console_signals():
            nd = self.nl.node(F); out[F] = dict(pin=pin, node=nd)
        return out

    def branch_nets(self):
        s = set()
        for F, d in self.sigs.items(): s |= set(d['node']['series'])
        return s

    def _detour(self):
        f, cpm, vpc = [], [], []
        for B in sorted(self.branch_nets()):
            cl = self.bd['clusters'].get(B, [])
            if len(cl) != 1: continue
            pads = [(p['x'], p['y']) for p in self.cop.pads_by_net.get(B, [])]
            m = mst_len(pads); r = self.cop.net(B)
            if m < 3.0 or r['length'] <= 0: continue
            f.append(r['length'] / m)
            ci = sum(v['c_iso'] + v['c_side'] for v in r['layers'].values()); ln_ = sum(v['length'] for v in r['layers'].values())
            if ln_ > 0: cpm.append(ci / ln_)
            vpc.append(r['vias'] / max(1, len(pads) - 1))
        f = np.array(f) if f else np.array([1.3]); cpm = np.array(cpm) if cpm else np.array([0.1])
        tol = A['copper_tol']
        if self.six:
            lo = (1 - tol) * self.cpm.iso('O6_plane', 0.15)
            hi = (1 + tol) * (self.cpm.iso('I6_both', 0.15) + 2 * self.cpm.side('I6_both', 0.15))
        else:
            lo = (1 - tol) * self.cpm.iso('O2_opp', 0.15)
            hi = (1 + tol) * (self.cpm.iso('O2_opp', 0.15) + 2 * self.cpm.side('O2_opp', 0.15))
        out = (float(np.median(f)), float(np.percentile(f, 90)), lo, float(np.median(cpm)), hi, float(np.median(vpc)) if vpc else 1.0)
        self.detour_stats = dict(n=len(f), f_med=out[0], f_90=out[1], cpm_min=lo, cpm_typ=out[3], cpm_max=hi, vias_per_link=out[5])
        return out

    # ---- capacitances with the module-fitting scenario of each corner
    def C(self, net, absent=()):
        lo, ty, hi = self.nodes.total(net)
        nd = self.nl.node(net)
        for ref, p, k in nd['chips']:
            if ref in absent:
                c = A['pin_qfn'] if k == 'qfn' else A['pin_module']; lo -= c[0]; ty -= c[1]; hi -= c[2]
        return (lo, ty, hi)

    def Cmin_opt(self, net):
        """min corner with the optional modules left out (rev G's 'one pad')"""
        return self.C(net, self.optional)[0]

    def corners(self, net):
        c = self.C(net); return (self.Cmin_opt(net), c[1], c[2])

    def branches(self, F):
        return [(B, par([e[2] for e in el]), el) for B, el in self.sigs[F]['node']['series'].items()]

    def chip_of(self, B):
        ch = self.nl.node(B)['chips']; return sorted({r for r, p, k in ch})

    def copper_table(self):
        rows = []
        for n in sorted(self.console_nets()):
            if n not in self.bd['nets']: continue
            r = self.cop.net(n); ob = self.nodes.open_bound(n)
            rows.append(dict(net=n, length=r['length'], layers={k: round(v['routed'], 2) for k, v in r['layers'].items()},
                             vias=r['vias'], pads=len(r['pads']), c_copper=r['c'], c_side=r['c_side'], open_links=ob[0],
                             open_c=ob[1:4], open_dist=ob[4], clusters=len(self.bd['clusters'].get(n, [])),
                             pins=self.nodes.pins(n), c_total=self.C(n),
                             per_mm={k: (v['c_iso'] + v['c_side']) / v['length'] for k, v in r['layers'].items() if v['length'] > 0}))
        return rows

    def layer_cpm(self):
        """length-weighted C/mm per layer over all console nets (tracks only)"""
        acc = {}
        for n in set(self.sigs) | self.branch_nets():
            if n not in self.bd['nets']: continue
            for k, v in self.cop.net(n)['layers'].items():
                a = acc.setdefault(k, [0.0, 0.0, 0.0, 0.0]); a[0] += v['length']; a[1] += v['c_iso'] + v['c_side']; a[2] += v['c_side']; a[3] += v['near']
        return {k: dict(length=a[0], cpm=a[1] / a[0] if a[0] else 0, side_share=a[2] / a[1] if a[1] else 0, near_frac=a[3] / a[0] if a[0] else 0) for k, a in acc.items()}

    # ---- strobes
    def strobes(self):
        lumped = lambda nets: tuple(sum(self.corners(n)[i] for n in nets) for i in range(3))
        add = lambda a, b: tuple(x + y for x, y in zip(a, b))
        rs_ext = self.corners('RSEL_D')
        rs_g = add(self.corners('nROMSEL'), A['console_romsel'])          # gate node = finger + console's own /ROMSEL
        rs_br = self.branches('nROMSEL')                                    # raw branches behind their 1k (rev H)
        rs_b = [[(R, self.corners(B)[i]) for B, R, el in rs_br] for i in range(3)]
        ws_ext = self.corners('WS_D'); m2n = self.corners('M2n')
        m2_g = add(lumped(['M2'] + [b for b, R, el in self.branches('M2')]), A['console_m2'])
        pw_ext = self.corners('PWS_D'); pw_g = self.corners('PWE_G')
        rk, rr = rsel_runs(rs_ext, rs_g, rs_b); pk, pr = pws_runs(pw_ext, pw_g); nk, nr = nor_runs(ws_ext, m2n, m2_g)
        rr, pr, nr = sim_inverter(rr), sim_inverter(pr), sim_nor(nr)
        s = summarize_strobes(rk, rr, pk, pr, nk, nr, [B for B, R, el in rs_br])
        s['inputs'] = dict(RSEL_D=rs_ext, nROMSEL_gate=rs_g, WS_D=ws_ext, M2n=m2n, M2_gate=m2_g, PWS_D=pw_ext, PWE_G=pw_g,
                           nROMSEL_branches={B: self.corners(B) for B, R, el in rs_br})
        return s

    # ---- PPU and CPU reads
    def bus_reads(self, ccons_ppu):
        """ccons_ppu: {reading: (typ, worst)} console-side capacitance of a PPU data line. PPU rows: the design's data
        resistance ('design') and the alternatives 500 / 333 / 1000 ohm on both chips' arrays."""
        out = {'ppu': {}, 'cpu': {}, 'ppu_R': {}, 'cpu_R': {}}
        crd = self.corners('RD_D') if 'RD_D' in self.bd['nets'] else (0, 0, 0)
        out['c_rd'] = crd
        for b in range(8):
            F = f'PPU_D{b}'
            if F not in self.sigs: continue
            cf = self.C(F); brs = self.branches(F)
            for drv in ('U2', 'U5'):
                dv = [x for x in brs if drv in self.chip_of(x[0])]
                if not dv: continue
                Bd, Rd, _ = dv[0]; oth = [x for x in brs if x[0] != Bd]
                out['ppu_R'][(b, drv)] = Rd
                for scen, absent in (('fitted', ()), ('U5 absent', ('U5',))):
                    if scen != 'fitted' and (drv == 'U5' or 'U5' not in self.optional): continue
                    co = [self.C(x[0], absent) for x in oth]
                    for rv in ('design', 500.0, 333.33, 1000.0):
                        if rv != 'design' and abs(rv - Rd) < 1: continue          # the design row already has it
                        R = Rd if rv == 'design' else rv
                        r_oth = (oth[0][1] if rv == 'design' else rv) if oth else R
                        for reading, (cty, cwo) in ccons_ppu.items():
                            ty = ppu_read_lumped(R, crd[1], cty + cf[1] + sum(c[1] for c in co), False)
                            wo = ppu_read_lumped(R, crd[2], cwo + cf[2] + sum(c[2] for c in co), True)
                            nty = ppu_read_network(R, crd[1], self.C(Bd)[1], cty + cf[1], sum(c[1] for c in co), False, r_oth)
                            nwo = ppu_read_network(R, crd[2], self.C(Bd)[2], cwo + cf[2], sum(c[2] for c in co), True, r_oth)
                            out['ppu'][(b, drv, scen, rv if rv == 'design' else round(rv), reading)] = dict(
                                R=R, typ=ty, worst=wo, net_typ=nty, net_worst=nwo, c_f=cf, c_drv=self.C(Bd),
                                c_other=[tuple(c) for c in co], other=[x[0] for x in oth])
        for b in range(8):
            F = f'CPU_D{b}'
            if F not in self.sigs: continue
            cf = self.C(F); brs = self.branches(F)
            for x in brs:
                Bd, Rd, _ = x; drv = ','.join(self.chip_of(Bd))
                out['cpu_R'][(b, drv)] = Rd
                oth = [y for y in brs if y[0] != Bd]
                for scen, drop in (('all', ()), ('without U3 branch', tuple(y[0] for y in oth if 'U3' in self.chip_of(y[0])))):
                    if scen != 'all' and not drop: continue
                    oo = [y for y in oth if y[0] not in drop]
                    co = [self.C(y[0]) for y in oo]
                    def network(i, Rd_, r_oth):
                        """settling at the console (finger node) through the driver's Rd_, other branches behind r_oth"""
                        j = i + 1; cons, vil = A['cpu_bus_console'][i], A['console_vil'][i]
                        nodes = {'D': self.C(Bd)[j], 'F': cons + cf[j]}
                        rr_ = [('D', 'S', A['r_drv'][i]), ('D', 'F', Rd_)]
                        for k_, (y, c) in enumerate(zip(oo, co)):
                            nodes[f'B{k_}'] = c[j]; rr_.append(('F', f'B{k_}', r_oth[k_]))
                        nf, _ = rc_network_cross(nodes, rr_, {'S': A['v_drv_low']}, {}, A['v_start_fall'], 'F', vil, True)
                        rr_[0] = ('D', 'S', A['r_drv_hi'][i])
                        nr_, _ = rc_network_cross(nodes, rr_, {'S': A['v_rise_to']}, {}, A['v_rise_from'], 'F', A['v_ih'], False)
                        return max(nf, nr_)
                    res = {}
                    for lab, i in (('typ', 0), ('worst', 1)):
                        j = i + 1                                                   # capacitance corner: typ / max
                        cons, vil = A['cpu_bus_console'][i], A['console_vil'][i]
                        cbus = cons + cf[j] + sum(c[j] for c in co)
                        fall = rc_delay(Rd + A['r_drv'][i], cbus, A['v_start_fall'], A['v_drv_low'], vil)
                        rise = rc_delay(Rd + A['r_drv_hi'][i], cbus, A['v_rise_from'], A['v_rise_to'], A['v_ih'])
                        res[lab] = dict(c_bus=cbus, c_cons=cons, fall=fall, rise=rise, lumped=max(fall, rise),
                                        network=network(i, Rd, [y[1] for y in oo]), R=Rd)
                    if scen == 'all':                                               # every chip's array at another value
                        res['alt'] = {rv: (network(0, rv, [rv] * len(oo)), network(1, rv, [rv] * len(oo))) for rv in (1000.0, 470.0, 330.0)}
                    out['cpu'][(b, drv, scen)] = res
        return out

    # ---- RC delays of every console input branch, outputs, loads
    def input_delays(self, strobes):
        """every branch behind its series resistor: single-pole RC from the console pin (A['r_console'] + R), except the
        raw /ROMSEL branches, which come from the strobe transient (74LS139 totem pole + 2.2k on the gate node)"""
        out = {}
        raw = strobes.get('raw', {})
        for F, d in self.sigs.items():
            for B, R, el in self.branches(F):
                c = self.corners(B)
                if B in raw:
                    out[(F, B)] = dict(R=R, c=c, chips=self.chip_of(B), fall=raw[B]['sel'], rise=raw[B]['des'], model='transient')
                    continue
                rt, rw = R + A['r_console'][0], R + A['r_console'][1]
                out[(F, B)] = dict(R=R, c=c, chips=self.chip_of(B), model='RC',
                                   fall=(rc_delay(rt, c[1], 4.0, 0.3, 1.3), rc_delay(rw, c[2], 4.0, 0.4, 0.8)),
                                   rise=(rc_delay(rt, c[1], 0.3, 4.0, 1.6), rc_delay(rw, c[2], 0.3, 2.7, 2.0)))
        return out

    def console_loads(self):
        """per console line: finger node (copper, clamps, pins on it), the branches behind their resistors, FET gates"""
        out = {}
        for F, d in self.sigs.items():
            br = [self.corners(B) for B, R, el in self.branches(F)]
            nd = self.nl.node(F)
            gates = list(nd['fet_gate']) + [g for B, R, el in self.branches(F) for g in self.nl.node(B)['fet_gate']]
            out[F] = dict(finger=self.C(F), branches=tuple(sum(c[i] for c in br) for i in range(3)) if br else (0.0, 0.0, 0.0),
                          n_branches=len(br), gates=gates, drains=nd['fet_drain'], pulls=[(r, R, o) for r, p, R, o in nd['pulls']])
        return out

def stackup_report(cpm6, cpm2, w6=0.15, log=print):
    """C per mm from the stack-up: field solver against closed-form formulas (w6: the rev H board's track width)"""
    L = [f'== C per mm from the stack-ups (2-D field solver; pF/mm) ==']
    if cpm6:
        fd_nm = section_c('O6_plane', 0.15, mask=False); hj = hammerstad_jensen(0.15, 0.0994, 4.1, 0.035)
        ipc = ipc2141_asym_stripline(0.15, 0.0152, 0.1164, 0.35, (4.16 * 0.1316 + 4.6 * 0.35) / 0.4816)
        L.append(f"   rev H F.Cu / B.Cu over In1 / In4 (3313 prepreg 0.0994 mm, er 4.1, 10 um mask er 3.8): {w6} mm {cpm6.iso('O6_plane', w6):.4f}, "
                 f"0.15 mm {cpm6.iso('O6_plane', 0.15):.4f}; 0.15 mm without mask {fd_nm:.4f}, Hammerstad-Jensen {hj[0]:.4f} (Z0 {hj[1]:.1f} ohm, eeff {hj[2]:.2f})")
        L.append(f"   rev H In3 between In2 (2116 prepreg 0.1164 mm, er 4.16) and In4 (core 0.35 mm, er 4.6): {w6} mm {cpm6.iso('I6_both', w6):.4f}, "
                 f"0.15 mm {cpm6.iso('I6_both', 0.15):.4f}; 0.15 mm IPC-2141 asymmetric stripline {ipc[0]:.4f} (Z0 {ipc[1]:.1f} ohm, er 4.48)")
        L.append(f"   rev H fall-backs ({w6} mm): F.Cu over In2 only {cpm6.iso('O6_far', w6):.4f}, B.Cu over In2 only {cpm6.iso('O6_farB', w6):.4f}, "
                 f"outer in the tab (opposite face 1.146 mm) {cpm6.iso('O6_opp', w6):.4f}, In3 with In2 missing {cpm6.iso('I6_in4', w6):.4f}")
        L.append(f"   coplanar neighbour on one side at 0.12 / 0.25 mm (0.15 mm track): outer +{cpm6.side('O6_plane', 0.12):.4f} / +{cpm6.side('O6_plane', 0.25):.4f}, "
                 f"In3 +{cpm6.side('I6_both', 0.12):.4f} / +{cpm6.side('I6_both', 0.25):.4f}")
    if cpm2:
        fd_nm = section_c('O2_opp', 0.15, mask=False); hj = hammerstad_jensen(0.15, 1.11, 4.5, 0.035)
        L.append(f"   rev G (FR4 1.11 mm, er 4.5) over the opposite pour, 0.15 mm: {cpm2.iso('O2_opp', 0.15):.4f}; without mask {fd_nm:.4f}, Hammerstad-Jensen {hj[0]:.4f} "
                 f"(Z0 {hj[1]:.1f}); no copper opposite {cpm2.iso('O2_air', 0.15):.4f}; coplanar pour at 0.15 / 0.25 mm on one side "
                 f"+{cpm2.side('O2_opp', 0.15):.4f} / +{cpm2.side('O2_opp', 0.25):.4f}")
    L.append(f"   vias: 6 layers {A['via_6l'][1]} pF (Johnson: 1.41 er T D1 / (D2 - D1), er 4.4, T 0.0472 in, D1 0.5 mm, D2 1.0 mm), 2 layers {A['via_2l'][1]} pF (assumed)")
    txt = '\n'.join(L); log(txt); return txt


def assumptions_report(log=print):
    L = ['== assumptions (min / typ / max, or typ / worst; source in the A table of the code) ==',
         f"   pin capacitance: RP2350B QFN-80 GPIO {A['pin_qfn']} pF (assumed: no datasheet value); Pico 2 / XIAO castellation {A['pin_module']} pF (rev G review)",
         f"   BAV99 clamp {A['bav99']} pF; vias 6 layers {A['via_6l']}, 2 layers {A['via_2l']} pF; copper +-{100 * A['copper_tol']:.0f} %, min counts "
         f"{100 * A['neighbour_min_share']:.0f} % of the coplanar-neighbour increment; 2N7002 Cgs/Cgd/Cds {CAPS} pF (rev G)",
         f"   RP2350 output (8 mA drive set by the firmware) low {A['r_drv']} ohm, high {A['r_drv_hi']} ohm (typ rev G / worst datasheet VOL 0.5 V, VOH 2.62 V at 8 mA)",
         f"   console: PPU /RD source {A['r_rd_src']} ohm (rev G, no data); address / strobe drivers {A['r_console']} ohm (assumed); own capacitance of "
         f"/ROMSEL {A['console_romsel']} pF and M2 {A['console_m2']} pF (assumed)",
         f"   console PPU data line: rev G's total {A['ppu_bus_total']} pF split by reading A / B / C (below); 74LS373 IIL {A['iil'][0]*1e3:.1f} / {A['iil'][1]*1e3:.1f} mA; "
         f"thresholds console {A['console_vil']} V, RP2350 /RD {A['rd_vth']} V; PIO {A['pio']} ns (rev G)",
         f"   CPU-read chain (not in rev G): console CPU data bus {A['cpu_bus_console']} pF (assumed), 6500 setup {A['tdsu']} ns, LS139 M2 -> /ROMSEL {A['ls139_tphl']} ns, "
         f"M2 high {T_CYC * (1 - VERSIONS['E/G/H'][0]):.1f} ns (E/G/H); CIRAM input + track {A['ciram_console']} pF (assumed)",
         '   open connections: straight distance between the pad clusters (MST); min = straight x lowest C/mm, typ = x median detour x median C/mm + median vias,',
         "   max = x 90th-percentile detour x highest C/mm + 4 vias per link (detours and C/mm from this board's complete branch nets)"]
    txt = '\n'.join(L); log(txt); return txt

def f1(x, d=1): return '  -- ' if x is None or (isinstance(x, float) and not np.isfinite(x)) else f'{x:.{d}f}'
def rng(t, d=1): return f'{f1(t[0], d)} / {f1(t[1], d)} / {f1(t[2], d)}'
def tg_dl(): return A['ppu_window'] - A['ppu_target_margin'], A['ppu_window']

def console_readings(an):
    """console-side capacitance of a PPU data line from rev G's lumped 35 / 60 pF and the rev G board:
    A: rev G's figure covered the console and the cartridge's finger-side copper, not U5's branch (docs/13's reading)
    B: rev G's figure was the console alone          C: it covered everything, U5 fitted included"""
    cf = [an.C(f'PPU_D{b}') for b in range(8)]
    cy = [an.C(f'YD{b}') for b in range(8)] if 'YD0' in an.bd['nets'] else [(0, 0, 0)] * 8
    typ, wo = A['ppu_bus_total']
    return {'A': (typ - float(np.mean([c[1] for c in cf])), wo - max(c[2] for c in cf)),
            'B': (typ, wo),
            'C': (typ - float(np.mean([a[1] + b[1] for a, b in zip(cf, cy)])), wo - max(a[2] + b[2] for a, b in zip(cf, cy)))}

def evaluate(an, readings, log=print):
    R = {'board': an.board, 'md5': an.bd['md5'], 'design': an.design, 'unconnected': an.bd['unconnected'], 'warnings': an.warnings}
    log(f"  copper layers {an.bd['ncu']}, tracks {len(an.bd['tracks'])}, vias {len(an.bd['vias'])}, unconnected items (pcbnew) {an.bd['unconnected']}")
    R['detour'] = an.detour_stats
    R['layer_cpm'] = an.layer_cpm()
    R['copper'] = an.copper_table()
    t0 = time.time(); R['strobes'] = an.strobes(); log(f'  strobe transients ({time.time() - t0:.0f} s)')
    R['reads'] = an.bus_reads(readings)
    R['inputs'] = an.input_delays(R['strobes'])
    R['loads'] = an.console_loads()
    R['readings'] = readings
    R['open'] = {n: an.nodes.open_bound(n) for n in sorted(an.console_nets()) if n in an.bd['nets'] and len(an.bd['clusters'].get(n, [])) > 1}
    return R

def ppu_summary(R, reading='A', tag='design'):
    """{(driver, scenario): (bit, record)} of the slowest bit by the network model's worst case"""
    rows = {}
    for (b, drv, scen, r, rd), v in R['reads']['ppu'].items():
        if rd != reading or r != tag: continue
        k = (drv, scen); cur = rows.get(k)
        if cur is None or v['net_worst']['total'] > cur[1]['net_worst']['total']: rows[k] = (b, v)
    return rows

def ppu_tags(R):
    return ['design'] + sorted({k[3] for k in R['reads']['ppu'] if k[3] != 'design'})

def cpu_chains(R, an):
    """CPU read chain per driver: M2 -> /ROMSEL (LS139) -> detection (raw /ROMSEL branch, or RSEL_D) -> PIO -> data bus
    settled at the console (network model, slowest bit). Returns {driver: dict}"""
    s = R['strobes']; out = {}
    worst = {}
    for (b, drv, scen), v in R['reads']['cpu'].items():
        if scen != 'all': continue
        cur = worst.get(drv)
        if cur is None or v['worst']['network'] > cur[1]['worst']['network']: worst[drv] = (b, v)
    for drv, (b, v) in sorted(worst.items()):
        det = {}
        if set(an.chip_of('RSEL_D')) & set(drv.split(',')):          # only the chips that have an RSEL_D pin
            det = {'RSEL_D (rev G corners)': (s['rsel_rise'][0], s['rsel_rise'][2]), 'RSEL_D (all corners)': (s['rsel_rise'][0], s['rsel_rise_all'][1])}
        for B, r in s['raw'].items():
            if set(an.chip_of(B)) & set(drv.split(',')): det[f'raw /ROMSEL ({B})'] = r['sel']
        ch = {}
        for lab, (dt, dw) in det.items():
            tt = A['ls139_tphl'][0] + dt + A['pio'][0] + v['typ']['network']
            tw = A['ls139_tphl'][1] + dw + A['pio'][1] + v['worst']['network']
            ch[lab] = dict(typ=tt, worst=tw, detect=(dt, dw))
        out[drv] = dict(bit=b, bus=v, chains=ch)
    return out

def report(R, an, calib=None, log=print):
    L = []
    P = L.append
    s = R['strobes']; six = an.six; tg, dl = tg_dl()
    name = os.path.basename(R['board'])
    P(f"\n=== {name} ({R['design']}) ===")
    P(f"   board {R['board']}, md5 {R['md5']}; copper layers {an.bd['ncu']}, {len(an.bd['tracks'])} track segments, {len(an.bd['vias'])} vias, "
      f"unconnected items (pcbnew) {R['unconnected']}")
    for ln_, h in sorted(an.bd['whist'].items()):
        tot = sum(h.values())
        P(f"   track widths {ln_:6s} " + ', '.join(f'{w:g} mm {l:.0f}' for w, l in sorted(h.items(), key=lambda kv: -kv[1])[:6]) + f' (of {tot:.0f} mm)')
    P(f"   console nets: " + ', '.join(f'{w:g} mm {l:.0f}' for w, l in sorted(an.console_widths.items(), key=lambda kv: -kv[1])) +
      f" mm; design TRACK {getattr(an.D, 'TRACK', '?')}")
    if R['warnings']:
        P(f"   SELF-CHECK WARNINGS ({len(R['warnings'])}):"); [P('     ' + w) for w in R['warnings'][:40]]
        if len(R['warnings']) > 40: P(f'     ... {len(R["warnings"]) - 40} more')
    else:
        P('   self-checks: board matches the design on every console net (pads, nets, series values), track width = design TRACK')
    P(f"\n   copper per layer of the console nets (tracks, length-weighted):")
    for k, v in sorted(R['layer_cpm'].items()):
        P(f"   {k:7s} {v['length']:7.0f} mm  {v['cpm']:.4f} pF/mm  (coplanar-neighbour share {100 * v['side_share']:.1f} %, "
          f"{100 * v['near_frac']:.0f} % of the length has foreign copper within 0.3 mm)")
    d = R['detour']
    P(f"   routed / straight (MST of the pads) over {d['n']} complete branch nets: median {d['f_med']:.2f}, 90th percentile {d['f_90']:.2f}; "
      f"{d['vias_per_link']:.1f} vias per pad-to-pad link")
    if R['open']:
        P('   OPEN connections on console nets (bound added to the node: links, straight mm, + pF min / typ / max):')
        for n, (k, lo, ty, hi, edges) in R['open'].items():
            P(f"     {n:10s} {k} missing link(s), straight {', '.join(f'{e:.1f}' for e in edges)} mm  ->  +{lo:.1f} / +{ty:.1f} / +{hi:.1f} pF")
    else:
        P('   no open connection on the console nets')
    other = sorted(n for n, cl in an.bd['clusters'].items() if len(cl) > 1 and n not in R['open'] and not is_rail(an.D, n))
    if other: P(f"   other incomplete nets (not console timing): {', '.join(other)}")
    # node capacitances
    P('\n   node capacitances (pF, min / typ / max; min with the optional modules left out where the design has them):')
    keyn = ['PPU_nRD', 'RD_D', 'RD_D3', 'nROMSEL', 'RSEL_D', 'C_ROMSEL', 'Z_ROMSEL', 'M2', 'M2n', 'WS_D', 'C_M2', 'ZM2', 'HM2', 'CPU_RW', 'C_RW', 'Z_RW',
            'PPU_nWE', 'PWE_G', 'PWS_D', 'P_WE', 'CIRAM_nCE', 'NCE_D', 'CIRAM_A10', 'NA10_D', 'nIRQ']
    keyn += [f'PPU_D{b}' for b in range(8)] + [f'PD{b}' for b in range(8)] + [f'YD{b}' for b in range(8)]
    keyn += [f'CPU_D{b}' for b in range(8)] + [f'CD{b}' for b in range(8)] + [f'XD{b}' for b in range(8)] + [f'ZD{b}' for b in range(8)]
    rows = {r['net']: r for r in R['copper']}
    P(f"   {'net':10s} {'mm':>6s} {'F/In3/B (or F/B) mm':>20s} {'vias':>4s} {'copper':>18s} {'pins+clamps':>16s} {'node':>18s}  chips")
    for n in keyn:
        r = rows.get(n)
        if not r: continue
        lay = '/'.join(f"{r['layers'].get(l, 0):.0f}" for l in (('F.Cu', 'In3.Cu', 'B.Cu') if six else ('F.Cu', 'B.Cu')))
        cc = r['c_copper']; oc = r['open_c']
        cop = (cc[0] + oc[0], cc[1] + oc[1], cc[2] + oc[2])
        chips = ','.join(sorted({c[0] for c in an.nl.node(n)['chips']}))
        P(f"   {n:10s} {r['length']:6.1f} {lay:>20s} {r['vias']:4d} {rng(cop):>18s} {rng(r['pins']):>16s} {rng(an.corners(n)):>18s}  {chips}{' OPEN' if r['open_links'] else ''}")

    # ---------------------------------------------------------------- PPU read
    P(f"\n=== {name}: PPU read (rev G's chain: /RD -> 1k -> RD_D node -> PIO -> data line; ns after /RD falls) ===")
    pr = R['reads']['ppu_R']
    for drv in ('U2', 'U5'):
        vals = sorted({round(v, 1) for (b, d_), v in pr.items() if d_ == drv})
        if vals: P(f"   data resistance {drv}: {', '.join(f'{v:g}' for v in vals)} ohm per bit (from the design values)")
    rdb = [(B, Rr) for B, Rr, el in an.branches('PPU_nRD')] if 'PPU_nRD' in an.sigs else []
    P('   /RD branches: ' + ', '.join(f"{B} {Rr:.0f} ohm ({','.join(an.chip_of(B))}, {rng(an.corners(B))} pF)" for B, Rr in rdb) +
      f"; the read waits on RD_D")
    P(f"   drivers: RP2350 low {A['r_drv'][0]:g} / {A['r_drv'][1]:g} ohm, high {A['r_drv_hi'][0]:g} / {A['r_drv_hi'][1]:g} ohm (typ / worst); PPU /RD {A['r_rd_src'][0]:g} / {A['r_rd_src'][1]:g} ohm")
    P(f"   console side of a data line (pF typ / worst): " + ', '.join(f'{k} {v[0]:.1f} / {v[1]:.1f}' for k, v in R['readings'].items()) +
      "  (A = docs/13's reading; B, C bracket it)")
    P(f"   {'data R':>8s} {'driver':12s} rd  {'typ net (lumped)':>18s} {'worst net (lumped)':>20s}  bit  margin to {tg:.1f} / {dl:.1f} (network worst)")
    for tag in ppu_tags(R):
        for reading in ('A', 'B', 'C'):
            for (drv, scen), (b, v) in sorted(ppu_summary(R, reading, tag).items()):
                if reading != 'A' and scen != 'fitted': continue
                w = v['net_worst']['total']
                P(f"   {v['R']:8.1f} {drv + ('' if scen == 'fitted' else ' (' + scen + ')'):12s} {reading:2s} {v['net_typ']['total']:7.1f} ({v['typ']['total']:5.1f})   "
                  f"{w:8.1f} ({v['worst']['total']:5.1f})      D{b}  {tg - w:+6.1f} / {dl - w:+6.1f}{'  <- as designed' if tag == 'design' and reading == 'A' else ''}")
    ps = ppu_summary(R, 'A', 'design')
    if ps:
        (b, v) = max(ps.values(), key=lambda bv: bv[1]['net_worst']['total'])
        w, nw = v['worst'], v['net_worst']; cw = R['readings']['A'][1]; crd = R['reads']['c_rd']
        oth = sum(c[2] for c in v['c_other'])
        P(f"   slowest bit D{b} [A], worst: /RD node {crd[2]:.1f} pF -> {nw['t_rd']:.1f} ns, PIO {nw['pio']:.0f}, data line fall {nw['fall']:.1f} / rise {nw['rise']:.1f} ns "
          f"(network: driver node {v['c_drv'][2]:.1f} pF, finger node {cw + v['c_f'][2]:.1f} pF = console {cw:.1f} + finger {v['c_f'][2]:.1f}, other branch {oth:.1f}); low level {w['vfin']:.2f} V")
        P(f"   typ: /RD node {crd[1]:.1f} pF -> {v['net_typ']['t_rd']:.1f} ns, PIO {v['net_typ']['pio']:.0f}, data line {max(v['net_typ']['fall'], v['net_typ']['rise']):.1f} ns")
        # what-ifs and sensitivities on that bit, network model (both chips' arrays take the new data value)
        Rdes = v['R']; ct = R['readings']['A'][0]; oth_t = sum(c[1] for c in v['c_other'])
        def nwk(Rd_, rr_=1000.0, crd_=crd[2], cf_=cw + v['c_f'][2], cd_=v['c_drv'][2], co_=oth):
            return ppu_read_network(Rd_, crd_, cd_, cf_, co_, True, Rd_, rr_)['total']
        def nwk_t(Rd_, rr_=1000.0, crd_=crd[1]):
            return ppu_read_network(Rd_, crd_, v['c_drv'][1], ct + v['c_f'][1], oth_t, False, Rd_, rr_)['total']
        P(f"   what-if on D{b} [A], network model (typ / worst):")
        for lab, Rd_, rr_, crd_ in ((f'as designed: data {Rdes:g} ohm, /RD 1k', Rdes, 1000.0, crd), ('data 500 ohm (rev G: 1k x2)', 500.0, 1000.0, crd),
                                    ('data 333 ohm (1k x3)', 333.33, 1000.0, crd), ('data 1k', 1000.0, 1000.0, crd),
                                    ('/RD 500 ohm (2 x 1k: halves the 5 V injection limit)', Rdes, 500.0, crd),
                                    ("/RD node at rev G's 20 / 30 pF", Rdes, 1000.0, (0.0, 20.0, 30.0))):
            if not lab.startswith('as designed') and abs(Rd_ - Rdes) < 1 and rr_ == 1000.0 and crd_ is crd: continue   # = the design row
            ty_, wo_ = nwk_t(Rd_, rr_, crd_[1]), nwk(Rd_, rr_, crd_[2])
            P(f"     {lab:52s} {ty_:6.1f} / {wo_:6.1f}   margin to {tg:.1f}: {tg - wo_:+6.1f}, to {dl:.1f}: {dl - wo_:+6.1f}")
        base = nwk(Rdes)
        npin = len(an.nl.node('RD_D')['chips']) if 'RD_D' in an.bd['nets'] else 0
        dp = A['pin_qfn'][2]
        sens = [('per pF on the data line (finger node)', nwk(Rdes, cf_=cw + v['c_f'][2] + 1) - base),
                ('per pF on the /RD node RD_D', nwk(Rdes, crd_=crd[2] + 1) - base),
                (f'per pF of every RP2350 pin ({npin} on RD_D, 1 on each data branch)', nwk(Rdes, crd_=crd[2] + npin, cd_=v['c_drv'][2] + 1, co_=oth + len(v['c_other'])) - base)]
        keep = {k: A[k] for k in ('r_drv', 'r_drv_hi', 'r_rd_src')}
        A['r_drv'] = (A['r_drv'][0], A['r_drv'][1] + 10); A['r_drv_hi'] = (A['r_drv_hi'][0], A['r_drv_hi'][1] + 10); sens.append(('per 10 ohm of RP2350 output resistance', nwk(Rdes) - base)); A.update(keep)
        A['r_rd_src'] = (A['r_rd_src'][0], A['r_rd_src'][1] + 100); sens.append(('per 100 ohm of PPU /RD source resistance', nwk(Rdes) - base)); A.update(keep)
        P('   sensitivity of that worst case: ' + '; '.join(f'{l} {x:+.2f} ns' for l, x in sens) + '; 1 ns per ns of PIO latency (33 ns, rev G)')
        R['ppu_sens'] = dict(sens)

    # ---------------------------------------------------------------- CPU read chain
    P(f"\n=== {name}: CPU read chain (M2 rises -> LS139 /ROMSEL -> detection -> PIO -> data bus settled at the console; ns after M2 rises) ===")
    m2h = T_CYC * (1 - VERSIONS['E/G/H'][0])
    dls = [(f'M2 fall - {t:.0f} setup', m2h - t) for t in A['tdsu']]
    cr = R['reads']['cpu_R']
    P('   data resistance: ' + ', '.join(f"{d_} {', '.join(f'{x:g}' for x in sorted({round(v, 1) for (b, dd), v in cr.items() if dd == d_}))} ohm" for d_ in sorted({k[1] for k in cr})) +
      f"; console bus {A['cpu_bus_console']} pF (assumed); deadlines " + ', '.join(f'{l} = {x:.1f}' for l, x in dls))
    chains = cpu_chains(R, an); R['cpu_chains'] = chains
    for drv, c in chains.items():
        bt, bw = c['bus']['typ'], c['bus']['worst']
        P(f"   {drv} drives (slowest bit D{c['bit']}): bus {bt['c_bus']:.0f} / {bw['c_bus']:.0f} pF, settles typ {bt['network']:.1f} (lumped {bt['lumped']:.1f}), "
          f"worst {bw['network']:.1f} (lumped {bw['lumped']:.1f}) ns")
        for lab, ch in c['chains'].items():
            P(f"     via {lab:30s} detect {ch['detect'][0]:5.1f} / {ch['detect'][1]:5.1f}   chain typ {ch['typ']:5.1f}, worst {ch['worst']:5.1f}   margins: "
              + ', '.join(f"{l} {x - ch['typ']:+.0f} / {x - ch['worst']:+.0f}" for l, x in dls))
    for (b, drv, scen), v in sorted(R['reads']['cpu'].items()):
        if scen != 'all' or (b, drv, 'without U3 branch') not in R['reads']['cpu'] or b != chains.get(drv, {}).get('bit'): continue
        v2 = R['reads']['cpu'][(b, drv, 'without U3 branch')]
        P(f"     U3 branch (ZD) adds {v['typ']['network'] - v2['typ']['network']:.1f} ns typ / {v['worst']['network'] - v2['worst']['network']:.1f} ns worst to {drv} on D{b}")
    if chains:
        best = {d_: min(c_['chains'].items(), key=lambda kv: kv[1]['worst']) for d_, c_ in chains.items() if c_['chains']}
        drv = max(best, key=lambda d_: best[d_][1]['worst']); lab, ch = best[drv]; c = chains[drv]
        bw = c['bus']['worst']; Rd = bw['R']
        k_c = (Rd + max(A['r_drv'][1], A['r_drv_hi'][1])) * 1e-3 * max(ln(A['v_start_fall'] - A['v_drv_low'], A['console_vil'][1] - A['v_drv_low']),
                                                                       ln(A['v_rise_to'] - A['v_rise_from'], A['v_rise_to'] - A['v_ih']))
        P(f"   worst chain over the drivers, each with its fastest detection: {drv} via {lab}: LS139 {A['ls139_tphl'][1]:.0f} + detect {ch['detect'][1]:.1f} + PIO {A['pio'][1]:.0f} + bus {bw['network']:.1f} "
          f"(of which the console's assumed {bw['c_cons']:.0f} pF: {k_c * bw['c_cons']:.0f} ns) = {ch['worst']:.1f} ns; {k_c:.2f} ns per pF of console bus")
        R['cpu_sens'] = dict(ns_per_pf_console=k_c)
        P(f"   what-if: every CPU data array at another value ({drv}, network; chain via {lab}, typ / worst, margins to "
          + ' / '.join(l for l, x in dls) + '):')
        alt = [(Rd, (c['bus']['typ']['network'], bw['network']))] + sorted(((k, x) for k, x in c['bus']['alt'].items() if abs(k - Rd) > 1), reverse=True)
        for rv, (bt_, bw_) in alt:
            tt = A['ls139_tphl'][0] + ch['detect'][0] + A['pio'][0] + bt_; tw = A['ls139_tphl'][1] + ch['detect'][1] + A['pio'][1] + bw_
            P(f"     {drv} data {rv:6.0f} ohm{' (design)' if rv == Rd else '         '}: bus {bt_:5.1f} / {bw_:5.1f}, chain {tt:5.1f} / {tw:5.1f}   "
              + ', '.join(f'{x - tw:+.1f}' for l, x in dls))

    # ---------------------------------------------------------------- strobes, every corner
    P(f"\n=== {name}: strobes and capture windows, every simulated corner (rev G's transient models) ===")
    inp = s['inputs']
    P(f"   node inputs (pF min / typ / max): RSEL_D {rng(inp['RSEL_D'])}; /ROMSEL gate node {rng(inp['nROMSEL_gate'])} incl. console {A['console_romsel']}; "
      + ''.join(f"{B} {rng(c)} behind 1k; " for B, c in inp['nROMSEL_branches'].items()) +
      f"WS_D {rng(inp['WS_D'])}; M2n {rng(inp['M2n'])}; M2 gate {rng(inp['M2_gate'])} incl. console {A['console_m2']}; PWS_D {rng(inp['PWS_D'])}; PWE_G {rng(inp['PWE_G'])}")
    P(f"   RSEL_D rise (/ROMSEL falls -> 2.0 V): typ {s['rsel_rise'][0]:.1f}, rev G's corners {s['rsel_rise'][1]:.1f} .. {s['rsel_rise'][2]:.1f}, "
      f"every corner {s['rsel_rise_all'][0]:.1f} .. {s['rsel_rise_all'][1]:.1f} (slowest: {s['rsel_rise_all'][2]})   rev G 46 (21 .. 107)")
    P(f"   RSEL_D fall (deselect -> 0.8 V): typ {s['rsel_fall'][0]:.1f}, typ caps max {s['rsel_fall'][1]:.1f}, every corner max {s['rsel_fall'][2]:.1f} "
      f"(at {s['rsel_fall_corner']})   rev G <= 55 / <= 103")
    P('     corner (caps, FET, /ROMSEL high)   rise 2.0 V   fall 0.8 V')
    for k, a_, b_ in s['rsel_corners']: P(f"     {str(k):34s} {f1(a_):>9s}   {f1(b_):>9s}")
    for B, r in s['raw'].items():
        P(f"   raw /ROMSEL at {B} ({','.join(an.chip_of(B))}): falls (to 1.3 / 0.8 V) {r['sel'][0]:.1f} / {r['sel'][1]:.1f}, rises (to 1.6 / 2.0 V) "
          f"{r['des'][0]:.1f} / {r['des'][1]:.1f} ns after the console edge (worst at {r['sel_corner']} / {r['des_corner']})")
    P(f"   WS_D (E/G/H) rise after M2 rises: typ {s['ws_rise'][0]:.1f}, rev G's corners {s['ws_rise'][1]:.1f} .. {s['ws_rise'][2]:.1f}, every corner "
      f"{s['ws_rise_all'][0]:.1f} .. {s['ws_rise_all'][1]:.1f}   rev G 80 (41 .. 192); fall after M2 falls {s['ws_fall'][0]:.1f} ({s['ws_fall'][1]:.1f} .. {s['ws_fall'][2]:.1f})   rev G 45 (23 .. 112)")
    P('     version corner (caps, Q1, Q3, M2 high V)          WS_D rise  fall  peak V   allowed capture delay   firmware')
    for k, st, en, mx in s['ws_corners']:
        share, fw = VERSIONS[k[0]]; low = T_CYC * share; valid, gone = T_CYC / 2 + 100 - low, T_CYC - low + 30
        lo, hi = valid - st, gone - st
        ok = 'ok' if lo <= fw[0] and fw[1] <= hi else f'FAILS by {max(lo - fw[0], fw[1] - hi):.1f}'
        P(f"     {k[0]:6s} {str(k[1:]):40s} {f1(st):>7s} {f1(en):>6s} {mx:5.2f}   {f1(lo, 0):>5s} .. {f1(hi, 0):<5s}        {fw[0]:.0f}..{fw[1]:.0f} {ok}")
    for k, w in s['windows'].items():
        P(f"   capture window {k:6s} over every corner: {w['lo']:.1f} .. {w['hi']:.1f} ns (fastest WS_D {w['fast'][1]:.1f} at {w['fast'][0]}, slowest {w['slow'][1]:.1f} at {w['slow'][0]}); "
          f"firmware {w['firmware'][0]:.0f} .. {w['firmware'][1]:.0f}: margin {w['margin']:+.1f}" + (f", {len(w['fail'])} corner(s) fail" if w['fail'] else ''))
    w = s['windows_revg']['E/G/H']
    P(f"   capture window E/G/H with rev G's corners only (typical-curve FETs, M2 4.0 V): {w['lo']:.1f} .. {w['hi']:.1f}   rev G 129 .. 187")
    P(f"   PWS_D (Q6, 1.1k) after /WE falls, typ caps: reaches 2.0 V in {s['pws_rise'][0]:.1f} .. {s['pws_rise'][1]:.1f} ns, peak {s['pws_peak'][0]:.2f} .. {s['pws_peak'][1]:.2f} V, "
      f"above 2.0 V for >= {s['pws_above']:.1f} ns (docs/11 >= 60)   rev G 69 .. 102 ns, 3.0 .. 3.1 V")
    P('     corner (caps, FET, /WE high V)   2.0 V at   peak V   time above 2.0 V')
    for k, a_, pk, ab in s['pws_corners']: P(f"     {str(k):32s} {f1(a_):>8s}   {pk:5.2f}    {f1(ab):>6s}")

    # ---------------------------------------------------------------- loads
    P(f"\n=== {name}: what the cartridge puts on each console line (pF typ / max) ===")
    P(f"   finger node = finger copper + clamps + pins on it; branches = nodes behind their series resistors (summed); FET gates direct or behind 1k: "
      f"Ciss {CAPS['typ'][0] + CAPS['typ'][1]:.0f} / {CAPS['max'][0] + CAPS['max'][1]:.0f} pF each (rev G's 2N7002)")
    LG = calib['loads'] if calib else {}
    P(f"   {'line':10s} {'finger':>13s} {'branches (n)':>19s} {'total':>13s}   {'rev G finger':>13s} {'rev G branches':>19s} {'change of total':>16s}  FET gates")
    for F in sorted(R['loads'], key=lambda f: (f[:3], f)):
        v = R['loads'][F]; tot = (v['finger'][1] + v['branches'][1], v['finger'][2] + v['branches'][2])
        g = LG.get(F)
        gs = (f"{g['finger'][1]:5.1f} / {g['finger'][2]:5.1f} {g['branches'][1]:6.1f} / {g['branches'][2]:5.1f} ({g['n_branches']})   "
              f"{tot[0] - g['finger'][1] - g['branches'][1]:+6.1f} / {tot[1] - g['finger'][2] - g['branches'][2]:+6.1f}") if g else f"{'-':>13s} {'-':>19s} {'-':>16s}"
        P(f"   {F:10s} {v['finger'][1]:5.1f} / {v['finger'][2]:5.1f} {v['branches'][1]:6.1f} / {v['branches'][2]:5.1f} ({v['n_branches']}) "
          f"{tot[0]:5.1f} / {tot[1]:5.1f}   {gs}  {','.join(v['gates']) or '-'}")

    # ---------------------------------------------------------------- inputs, outputs
    P(f"\n=== {name}: branch delays and outputs ===")
    P(f"   inputs through their series resistor (typ / worst; RC from the console pin with {A['r_console']} ohm, worst = max capacitance to 0.8 / 2.0 V from a 2.7 V high;"
      f" raw /ROMSEL from the transient):")
    for (F, B), v in sorted(R['inputs'].items()):
        if not (F in ('nROMSEL', 'CPU_RW', 'M2', 'PPU_nWE', 'PPU_nRD', 'CPU_A0', 'PPU_A0', 'CPU_A14', 'PPU_A10')): continue
        P(f"     {F + ' -> ' + B + ' (' + (','.join(v['chips']) or 'gate') + ')':36s} {v['R']:5.0f} ohm {v['c'][1]:5.1f} / {v['c'][2]:5.1f} pF: fall {f1(v['fall'][0])} / {f1(v['fall'][1])}, "
          f"rise {f1(v['rise'][0])} / {f1(v['rise'][1])}{'  (transient)' if v['model'] == 'transient' else ''}")
    if 'HM2' in an.bd['nets'] and 'C_M2' in an.bd['nets']:
        cm, ch = an.corners('C_M2'), an.corners('HM2'); rt, rw = 1000 + A['r_console'][0], 1000 + A['r_console'][1]
        r0t = rc_delay(rt, cm[1], 0.3, 4.0, 1.6); r0w = rc_delay(rw, cm[2], 0.3, 2.7, 2.0)
        r1t = rc_delay(rt, cm[1] + ch[1], 0.3, 4.0, 1.6); r1w = rc_delay(rw, cm[2] + ch[2], 0.3, 2.7, 2.0)
        P(f"     hub M2 on its own 1k (RN18): had HM2 ({ch[1]:.1f} / {ch[2]:.1f} pF) joined C_M2, U1 / U4 would see M2 rise {r1t - r0t:+.1f} ns typ / {r1w - r0w:+.1f} ns worst later")
    grp = {}
    for (F, B), v in R['inputs'].items():
        g = 'CPU A' if F.startswith('CPU_A') else 'PPU A' if F.startswith('PPU_A') else None
        if not g: continue
        key = (g, ','.join(v['chips'])); wv = max(x for x in (v['fall'][1], v['rise'][1]) if np.isfinite(x))
        if key not in grp or wv > grp[key][0]: grp[key] = (wv, F, B, v['c'][2])
    for (g, ch), (wv, F, B, c) in sorted(grp.items()):
        P(f"     {g} worst branch to {ch}: {wv:.1f} ns ({F} -> {B}, {c:.1f} pF)")
    for F in ('CIRAM_nCE', 'CIRAM_A10'):
        if F not in an.sigs: continue
        cf = an.C(F)
        for B, Rr, el in an.branches(F):
            ct, cw = A['ciram_console'][0] + cf[1], A['ciram_console'][1] + cf[2]
            typ_ = rc_delay(Rr + A['r_drv'][0], ct, 3.3, 0.05, 1.4)
            wo_ = max(rc_delay(Rr + A['r_drv'][1], cw, 3.3, 0.05, 0.8), rc_delay(Rr + A['r_drv_hi'][1], cw, 0.05, 3.3, 2.0))
            P(f"   {F} edge from U3 ({Rr:.0f} ohm): typ {typ_:.1f}, worst {wo_:.1f} ns ({ct:.0f} / {cw:.0f} pF)   rev G 8 .. 14")
    txt = '\n'.join(L)
    log(txt)
    return txt

def flat_summary(R):
    """one number per item (ns or pF; larger = slower) for --compare and for other tools"""
    f = {}
    for r in R['copper']: f[f'node pF max {r["net"]}'] = r['c_total'][2]; f[f'node pF typ {r["net"]}'] = r['c_total'][1]
    for tag in ppu_tags(R):
        for reading in ('A', 'B', 'C'):
            for (drv, scen), (b, v) in ppu_summary(R, reading, tag).items():
                f[f'PPU read {tag} {reading} {drv} {scen} worst'] = v['net_worst']['total']; f[f'PPU read {tag} {reading} {drv} {scen} typ'] = v['net_typ']['total']
    for drv, c in R.get('cpu_chains', {}).items():
        for lab, ch in c['chains'].items(): f[f'CPU read {drv} via {lab} worst'] = ch['worst']; f[f'CPU read {drv} via {lab} typ'] = ch['typ']
    s = R['strobes']
    f['RSEL_D rise worst (every corner)'] = s['rsel_rise_all'][1]; f['RSEL_D fall worst'] = s['rsel_fall'][2]
    f['WS_D rise worst (every corner)'] = s['ws_rise_all'][1]; f['WS_D fall worst'] = s['ws_fall'][2]
    f['PWS_D 2.0 V worst (typ caps)'] = s['pws_rise'][1]
    for k, w in s['windows'].items(): f[f'capture window {k} shortfall'] = -w['margin']
    for (F, B), v in R['inputs'].items():
        f[f'input {F}->{B} fall worst'] = v['fall'][1]; f[f'input {F}->{B} rise worst'] = v['rise'][1]
    return {k: (float(v) if v is not None and np.isfinite(v) else None) for k, v in f.items()}

def compare(new, old_path, log=print, tol=0.5):
    """items that are slower (larger) than in an earlier run of this tool (its timing.json); items on nets that the
    earlier run's self-check found different from the design are marked, their change is not the copper's"""
    old_run = json.load(open(old_path)); old = old_run.get('board_flat') or {}
    ob = old_run.get('board', {})
    moved = set()
    for w in ob.get('warnings', []):
        moved |= set(re.findall(r"(?:design net|board net) '?([A-Za-z0-9_]+)'?", w))
        m = re.match(r'design net (\S+) is not on the board', w)
        if m: moved.add(m.group(1))
    if 'RD_D' in moved: moved.add('PPU')                 # the PPU read waits on RD_D: mark the 'PPU read ...' items too
    L = [f"\n=== compared with {old_path} (board md5 {ob.get('md5', '?')}): items larger by more than {tol} ns / pF ==="]
    if ob.get('warnings'):
        L.append(f"   the earlier run had {len(ob['warnings'])} self-check warning(s): " + '; '.join(ob['warnings']))
    up = sorted(((new[k] - old[k], k) for k in new if k in old and new[k] is not None and old[k] is not None and new[k] - old[k] > tol), reverse=True)
    down = sum(1 for k in new if k in old and new[k] is not None and old[k] is not None and old[k] - new[k] > tol)
    for dlt, k in up:
        mark = '  (net differed from the design on the earlier board)' if set(re.findall(r'[A-Za-z0-9_]+', k)) & moved else ''
        L.append(f"   {k:60s} {old[k]:8.1f} -> {new[k]:8.1f}  ({dlt:+.1f}){mark}")
    L.append(f"   {len(up)} item(s) larger, {down} smaller, {sum(1 for k in new if k in old) - len(up) - down} within {tol}; "
             f"{len(set(new) - set(old))} only in this run, {len(set(old) - set(new))} only in the earlier one")
    txt = '\n'.join(L); log(txt); return txt

def jsonable(o):
    if isinstance(o, dict): return {(str(k) if not isinstance(k, str) else k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, np.integer)): return o.item()
    if isinstance(o, np.ndarray): return jsonable(o.tolist())
    if isinstance(o, float) and not np.isfinite(o): return None
    return o

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board', help='routed board (.kicad_pcb); it is copied into --out before pcbnew opens it')
    ap.add_argument('--design', default=os.environ.get('FC_DESIGN', 'design_revh'), help='design module in tools/pcb (default FC_DESIGN or design_revh)')
    ap.add_argument('--calib-board', help="rev G board: console side of the PPU data line (readings A / C) and the rev G column of the loads")
    ap.add_argument('--calib-design', default='design_revg')
    ap.add_argument('--out', help='output folder (default: a new temporary folder)')
    ap.add_argument('--compare', metavar='TIMING_JSON', help='list the items that are slower than in an earlier run of this tool')
    ap.add_argument('--selftest', action='store_true', help="only the models with rev G's inputs (no board)")
    ap.add_argument('--no-selftest', action='store_true')
    ap.add_argument('--set', action='append', default=[], metavar='KEY=v1,v2[,v3]',
                    help="override an assumption of A, e.g. --set pin_qfn=3,4,4.5 --set pio=13,21 (sensitivity runs)")
    a = ap.parse_args()
    out = os.path.abspath(a.out) if a.out else tempfile.mkdtemp(prefix='timing_')
    os.makedirs(out, exist_ok=True); work = os.path.join(out, 'work'); os.makedirs(work, exist_ok=True)
    lines = []
    def log(t=''): print(t, flush=True); lines.append(t)
    log(f"timing.py {' '.join(sys.argv[1:])}")
    for kv in a.set:
        k, v = kv.split('=', 1)
        if k not in A: raise SystemExit(f'unknown assumption {k}; known: {", ".join(A)}')
        vals = tuple(float(x) for x in v.split(','))
        A[k] = vals if isinstance(A[k], tuple) else vals[0]
        log(f'assumption {k} set to {A[k]}')
    res = {}; failed = []
    if a.selftest or not a.no_selftest:
        res['selftest'] = selftest(log); failed += res['selftest']['failed']
    if not a.selftest:
        assumptions_report(log)
        readings = {'A': (33.6, 58.2), 'B': A['ppu_bus_total'], 'C': (24.8, 45.3)}      # the rev G board's values, if no --calib-board
        Rg = ag = None
        if a.calib_board:
            ag = Analysis(a.calib_board, a.calib_design, work, log)
            readings = console_readings(ag)
            log("  console side of a PPU data line from rev G's 35 / 60 pF and this board (typ / worst, pF): " +
                ', '.join(f'{k} {v[0]:.1f} / {v[1]:.1f}' for k, v in readings.items()))
            Rg = evaluate(ag, readings, log); report(Rg, ag, log=log); res['calib'] = Rg; res['calib_flat'] = flat_summary(Rg)
            failed += [f'calib: {w}' for w in Rg['warnings']]
        else:
            log("  no --calib-board: console side of a PPU data line from the rev G board's stored values " +
                ', '.join(f'{k} {v[0]:.1f} / {v[1]:.1f}' for k, v in readings.items()))
        if a.board:
            ah = Analysis(a.board, a.design, work, log)
            w6 = max(ah.console_widths, key=ah.console_widths.get) if ah.console_widths else 0.15
            stackup_report(ah.cpm if ah.six else None, ag.cpm if ag else None, w6, log)
            Rh = evaluate(ah, readings, log); report(Rh, ah, Rg, log=log); res['board'] = Rh; res['board_flat'] = flat_summary(Rh)
            failed += Rh['warnings']
            if a.compare: compare(res['board_flat'], a.compare, log)
    log(f"\nself-checks: {'all pass' if not failed else str(len(failed)) + ' warning(s) above'}")
    json.dump(jsonable(res), open(os.path.join(out, 'timing.json'), 'w'), indent=1)
    open(os.path.join(out, 'timing_report.txt'), 'w').write('\n'.join(lines) + '\n')
    log(f"written: {os.path.join(out, 'timing_report.txt')}, {os.path.join(out, 'timing.json')}")
    return 1 if failed else 0

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--_fill':
        fill_zones_child(sys.argv[2], sys.argv[3]); code = 0
    else:
        code = main()
    sys.stdout.flush(); os._exit(code)
