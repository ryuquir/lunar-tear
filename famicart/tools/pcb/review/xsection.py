"""Cross-section field solver for links.py: delay, impedance and capacitance of a trace or a pair of traces.

What it does and why
  links.py needs the delay per mm (flight time), the capacitance per mm (the load a driver charges) and, for the USB
  pair and for crosstalk, the coupling between two parallel traces, for the board's own stack-up (microstrip on the
  outer layers, asymmetric stripline on In3). Closed forms do not cover the solder mask or the asymmetric stripline,
  so the cross-section is solved numerically.

Method
  A 2-D finite-difference solution of div(eps grad phi) = 0 on a graded rectilinear grid (grid lines on every
  dielectric interface and conductor edge, cells growing by `ratio` from `hmin` to at most `hmax`) inside a grounded
  box. Conductors are rectangles held at fixed potentials; the planes are the box floor (and ceiling for a stripline).
  The linear system is solved directly (block-tridiagonal elimination, one dense block per grid row, numpy only).
  The field energy gives the capacitance: sum over grid edges of g * dphi^2 = V^T C V. C0 is the same with every
  dielectric replaced by air; eps_eff = C / C0, t_pd = sqrt(eps_eff) / c, Z0 = 1 / (c sqrt(C C0)).
  A pair of equal traces: V = (1, 0) gives C11, V = (1, 1) gives C11 + C22 + 2 C12, so the mutual capacitance
  Cm = -C12, the odd-mode (C11 + Cm) and even-mode (C11 - Cm) capacitances and Z_diff = 2 Z_odd follow.

Checks (self_test(); `python3 xsection.py` prints them)
  Cohn's exact zero-thickness stripline (single and edge-coupled, odd and even mode), a homogeneous stripline
  (eps_eff must equal er), Hammerstad-Jensen's microstrip with thickness. A healthy result is within about 1 %.

Limits
  Quasi-static (no dispersion, no loss); rectangular traces (no etch trapezoid); the box walls are ground (1.5 mm or
  15 dielectric heights away, 2 mm for a stripline)."""
import math
import numpy as np

C_MM_PER_NS = 299.792458
EPS0 = 8.8541878128e-12
ETA0 = 376.730313668
RES = (0.002, 0.04, 1.2)            # default grid: hmin 2 um, hmax 40 um, growth 1.2


def _fill(a, b, hmin, hmax, ratio):
    """Grid points in (a, b]: steps growing by `ratio` from hmin at both ends, at most hmax."""
    L = b - a
    half, tot, s = [], 0.0, hmin
    while tot + s <= L / 2 + 1e-15:
        half.append(s); tot += s; s = min(s * ratio, hmax)
    mid = L - 2 * tot
    seq = list(half)
    if mid > 1e-12:
        n = max(1, int(math.ceil(mid / s - 1e-9)))
        seq += [mid / n] * n
    seq += half[::-1]
    xs, x = [], a
    for st in seq:
        x += st; xs.append(x)
    xs[-1] = b
    return xs


def grid(keys, hmin, hmax, ratio):
    keys = sorted(set(round(k, 9) for k in keys))
    pts = [keys[0]]
    for a, b in zip(keys, keys[1:]):
        pts += _fill(a, b, hmin, hmax, ratio)
    return np.array(pts)


def _blocktri_solve(a, b, deg, rhs):
    """Solve the symmetric block-tridiagonal system of a grid: rows j = 0..m-1 of n nodes; a[j, i] couples nodes i and
    i + 1 of row j, b[j, i] couples node i of rows j and j + 1, deg the diagonal. rhs (m, n, k). Direct elimination
    with one dense n x n block per row (the Schur complements stay symmetric positive definite)."""
    m, n = deg.shape
    k = rhs.shape[2]
    inv = np.empty((m, n, n))
    y = np.empty((m, n, k))
    idx = np.arange(n)
    for j in range(m):
        S = np.zeros((n, n))
        S[idx, idx] = deg[j]
        S[idx[:-1], idx[1:]] = -a[j]
        S[idx[1:], idx[:-1]] = -a[j]
        yj = rhs[j].copy()
        if j:
            c = b[j - 1]
            S -= c[:, None] * inv[j - 1] * c[None, :]
            yj += c[:, None] * (inv[j - 1] @ y[j - 1])
        inv[j] = np.linalg.inv(S)
        y[j] = yj
    x = np.empty((m, n, k))
    x[m - 1] = inv[m - 1] @ y[m - 1]
    for j in range(m - 2, -1, -1):
        x[j] = inv[j] @ (y[j] + b[j][:, None] * x[j + 1])
    return x


def solve(xs, ys, eps_rects, cond_rects, volt_sets, air=False):
    """Field energy sum(g dphi^2) (F/m, times eps0) for each set of conductor potentials.
    eps_rects: [(x0, x1, y0, y1, eps)] painted in order over a background of 1 (cells by their centre).
    cond_rects: [(x0, x1, y0, y1, conductor index)]: nodes inside or on the edge are held at that conductor's
    potential. volt_sets: [tuple of potentials per conductor index]. The box walls are at 0."""
    nx, ny = len(xs), len(ys)
    hx, hy = np.diff(xs), np.diff(ys)
    xc, yc = (xs[:-1] + xs[1:]) / 2, (ys[:-1] + ys[1:]) / 2
    E = np.ones((ny - 1, nx - 1))
    if not air:
        for x0, x1, y0, y1, e in eps_rects:
            mx = (xc > x0) & (xc < x1); my = (yc > y0) & (yc < y1)
            E[np.ix_(my, mx)] = e
    # edge conductances (dual-cell flux / edge length): gh between (j, i) and (j, i + 1), gv between (j, i) and (j + 1, i)
    Eb = np.zeros((ny, nx - 1)); Ea = np.zeros((ny, nx - 1))
    Eb[1:, :] = E * hy[:, None] / 2
    Ea[:-1, :] = E * hy[:, None] / 2
    gh = (Eb + Ea) / hx[None, :]
    El = np.zeros((ny - 1, nx)); Er = np.zeros((ny - 1, nx))
    El[:, 1:] = E * hx[None, :] / 2
    Er[:, :-1] = E * hx[None, :] / 2
    gv = (El + Er) / hy[:, None]
    X, Y = np.meshgrid(xs, ys)                                  # (ny, nx)
    fixed = (X <= xs[0]) | (X >= xs[-1]) | (Y <= ys[0]) | (Y >= ys[-1])
    which = np.full((ny, nx), -1)
    for x0, x1, y0, y1, ci in cond_rects:
        m = (X >= x0 - 1e-12) & (X <= x1 + 1e-12) & (Y >= y0 - 1e-12) & (Y <= y1 + 1e-12)
        fixed |= m; which[m] = ci
    val = np.zeros((len(volt_sets), ny, nx))
    for s, vs in enumerate(volt_sets):
        for ci, v in enumerate(vs):
            val[s][which == ci] = v
    free = ~fixed
    deg = np.zeros((ny, nx))
    deg[:, :-1] += gh; deg[:, 1:] += gh; deg[:-1, :] += gv; deg[1:, :] += gv
    # couplings between two free nodes stay in the matrix; a fixed neighbour moves to the right-hand side
    ah = gh * (free[:, :-1] & free[:, 1:])
    av = gv * (free[:-1, :] & free[1:, :])
    rhs = np.zeros((len(volt_sets), ny, nx))
    rhs[:, :, :-1] += gh * (free[:, :-1] & fixed[:, 1:]) * val[:, :, 1:]
    rhs[:, :, 1:] += gh * (fixed[:, :-1] & free[:, 1:]) * val[:, :, :-1]
    rhs[:, :-1, :] += gv * (free[:-1, :] & fixed[1:, :]) * val[:, 1:, :]
    rhs[:, 1:, :] += gv * (fixed[:-1, :] & free[1:, :]) * val[:, :-1, :]
    deg = np.where(fixed, 1.0, deg)                             # a fixed node: identity row, right-hand side = its potential
    rhs = np.where(fixed[None], val, rhs)
    if nx <= ny:                                                # rows along y, blocks of nx nodes
        phi = _blocktri_solve(ah, av, deg, np.moveaxis(rhs, 0, 2))
    else:                                                       # rows along x, blocks of ny nodes
        phi = _blocktri_solve(av.T, ah.T, deg.T, np.moveaxis(rhs, 0, 2).transpose(1, 0, 2)).transpose(1, 0, 2)
    out = []
    for s in range(len(volt_sets)):
        p = phi[:, :, s]
        out.append(EPS0 * float(np.sum(gh * np.diff(p, axis=1) ** 2) + np.sum(gv * np.diff(p, axis=0) ** 2)))
    return out


def _single(eps, cond, kx, ky, res):
    xs = grid(kx, *res); ys = grid(ky, *res)
    C, = solve(xs, ys, eps, cond, [(1.0,)])
    Ca, = solve(xs, ys, eps, cond, [(1.0,)], air=True)
    ee = C / Ca
    return dict(eps_eff=ee, tpd_ps_mm=math.sqrt(ee) / C_MM_PER_NS * 1e3, z0=1.0 / (C_MM_PER_NS * 1e6 * math.sqrt(C * Ca)),
                c_pf_mm=C * 1e12 / 1e3, nodes=len(xs) * len(ys))


def _pair(eps, cond, kx, ky, res):
    """Two equal traces (conductors 0 and 1): self and mutual capacitance, odd / even mode, Z_diff."""
    xs = grid(kx, *res); ys = grid(ky, *res)
    c11, e11 = solve(xs, ys, eps, cond, [(1.0, 0.0), (1.0, 1.0)])
    a11, ae11 = solve(xs, ys, eps, cond, [(1.0, 0.0), (1.0, 1.0)], air=True)
    cm, am = c11 - e11 / 2, a11 - ae11 / 2                      # -C12 (Maxwell C12 is negative)
    co, ce, ao, ae = c11 + cm, c11 - cm, a11 + am, a11 - am
    zo = 1.0 / (C_MM_PER_NS * 1e6 * math.sqrt(co * ao)); ze = 1.0 / (C_MM_PER_NS * 1e6 * math.sqrt(ce * ae))
    return dict(c11_pf_mm=c11 * 1e9, cm_pf_mm=cm * 1e9, z_odd=zo, z_even=ze, z_diff=2 * zo,
                tpd_odd_ps_mm=math.sqrt(co / ao) / C_MM_PER_NS * 1e3, tpd_even_ps_mm=math.sqrt(ce / ae) / C_MM_PER_NS * 1e3,
                nodes=len(xs) * len(ys))


def _micro_geom(w, t, h, er, mask_t, mask_er, centres, cpw_gap=None):
    X = max(1.5, 15 * h) + (max(centres) - min(centres)) / 2
    eps = [(-X, X, 0, h, er)]
    cond, kx = [], [-X, X]
    for i, c0 in enumerate(centres):
        if mask_t > 0:
            eps.append((c0 - w / 2 - mask_t, c0 + w / 2 + mask_t, h, h + t + mask_t, mask_er))        # mask over the trace
            kx += [c0 - w / 2 - mask_t, c0 + w / 2 + mask_t]
        cond.append((c0 - w / 2, c0 + w / 2, h, h + t, i))
        kx += [c0 - w / 2, c0, c0 + w / 2]
    if mask_t > 0:
        eps.insert(1, (-X, X, h, h + mask_t, mask_er))                                                  # mask on the bare laminate
    if cpw_gap is not None:                                                                             # GND pour both sides
        g0 = max(centres) + w / 2 + cpw_gap; g1 = min(centres) - w / 2 - cpw_gap
        n = len(centres)
        cond += [(g0, X, h, h + t, n), (-X, g1, h, h + t, n)]
        kx += [g0, g1]
        if mask_t > 0:
            eps += [(g0 - mask_t, X, h, h + t + mask_t, mask_er), (-X, g1 + mask_t, h, h + t + mask_t, mask_er)]
            kx += [g0 - mask_t, g1 + mask_t]
    ky = [0, h, h + t, max(1.5, 15 * h)] + ([h + mask_t, h + t + mask_t] if mask_t > 0 else [])
    return eps, cond, [k for k in kx if -X <= k <= X], ky


def _strip_geom(w, t, h_below, er_below, h_above, er_above, embed, centres):
    X = 2.0 + (max(centres) - min(centres)) / 2
    y0 = h_below; y1 = h_below + t
    top = y1 + h_above if embed == 'above' else y0 + h_above
    eps = [(-X, X, 0, y0, er_below), (-X, X, y0, top, er_above)]
    cond, kx = [], [-X, X]
    for i, c0 in enumerate(centres):
        cond.append((c0 - w / 2, c0 + w / 2, y0, y1, i)); kx += [c0 - w / 2, c0, c0 + w / 2]
    return eps, cond, kx, [0, y0, y1, top]


def microstrip(w, t, h, er, mask_t=0.0, mask_er=1.0, cpw_gap=None, res=RES):
    """Trace w x t on a dielectric h (er) over a plane at y = 0; optional conformal solder mask and coplanar ground
    (both sides, at cpw_gap from the trace edges). All mm."""
    eps, cond, kx, ky = _micro_geom(w, t, h, er, mask_t, mask_er, [0.0], cpw_gap)
    return _single(eps, cond, kx, ky, res)


def stripline(w, t, h_below, er_below, h_above, er_above, embed='above', res=RES):
    """Trace w x t between planes: dielectric h_below (er_below) under it; above it h_above (er_above) measured from the
    trace's top face (embed='above': KiCad's convention, the copper thickness is separate) or from the trace's base
    (embed='base': the prepreg thickness includes the copper). The trace is embedded in the upper dielectric."""
    return _single(*_strip_geom(w, t, h_below, er_below, h_above, er_above, embed, [0.0]), res)


def microstrip_pair(w, s, t, h, er, mask_t=0.0, mask_er=1.0, res=RES):
    """Two traces w x t, s apart (edge to edge), as microstrip(); see _pair() for the result."""
    d = (w + s) / 2
    return _pair(*_micro_geom(w, t, h, er, mask_t, mask_er, [-d, d]), res)


def stripline_pair(w, s, t, h_below, er_below, h_above, er_above, embed='above', res=RES):
    d = (w + s) / 2
    return _pair(*_strip_geom(w, t, h_below, er_below, h_above, er_above, embed, [-d, d]), res)


def ellipk(m):
    """Complete elliptic integral of the first kind K(m), parameter m = k^2 (arithmetic-geometric mean)."""
    a, b = 1.0, math.sqrt(1.0 - m)
    for _ in range(60):
        a, b = (a + b) / 2, math.sqrt(a * b)
        if abs(a - b) < 1e-15 * a:
            break
    return math.pi / (2 * a)


def cohn_stripline_z0(w, b, er):
    """Exact Z0 of a zero-thickness strip centred between planes b apart (Cohn 1954)."""
    k = 1.0 / math.cosh(math.pi * w / (2 * b)); kp = math.tanh(math.pi * w / (2 * b))
    return ETA0 / (4 * math.sqrt(er)) * ellipk(k * k) / ellipk(kp * kp)


def cohn_coupled_stripline(w, s, b, er):
    """Exact even / odd Z0 of two zero-thickness strips w, s apart, centred between planes b apart (Cohn 1955)."""
    t1 = math.tanh(math.pi * w / (2 * b))
    ke = t1 * math.tanh(math.pi * (w + s) / (2 * b)); ko = t1 / math.tanh(math.pi * (w + s) / (2 * b))
    f = ETA0 / (4 * math.sqrt(er))
    return f * ellipk(1 - ke * ke) / ellipk(ke * ke), f * ellipk(1 - ko * ko) / ellipk(ko * ko)


def hammerstad_jensen(w, h, t, er):
    """Microstrip eps_eff and Z0 (Hammerstad & Jensen 1980, with their thickness correction); no solder mask."""
    u = w / h
    def a_(u): return 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
    b_ = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    def ee(u): return (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a_(u) * b_)
    def z01(u):
        f = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u) ** 0.7528)
        return ETA0 / (2 * math.pi) * math.log(f / u + math.sqrt(1 + 4 / u ** 2))
    if t > 0:
        T = t / h
        du1 = T / math.pi * math.log(1 + 4 * math.e / (T * (1 / math.tanh(math.sqrt(6.517 * u))) ** 2))
        dur = 0.5 * (1 + 1 / math.cosh(math.sqrt(er - 1))) * du1
        u1, ur = u + du1, u + dur
    else:
        u1 = ur = u
    e = ee(ur) * (z01(u1) / z01(ur)) ** 2
    return dict(eps_eff=e, z0=z01(ur) / math.sqrt(ee(ur)), tpd_ps_mm=math.sqrt(e) / C_MM_PER_NS * 1e3)


def self_test(res=RES):
    """Solver against closed forms. Returns rows (case, solver, reference, relative difference)."""
    rows = []
    for w, b, er in ((0.15, 0.4816, 4.4), (0.3, 0.6, 1.0)):
        s = stripline(w, 1e-4, b / 2 - 0.5e-4, er, b / 2 - 0.5e-4, er, res=res)
        z = cohn_stripline_z0(w, b, er)
        rows.append(('stripline Z0 w %.2f b %.4f er %.1f (t 0.1 um) vs Cohn' % (w, b, er), s['z0'], z, s['z0'] / z - 1))
        rows.append(('stripline eps_eff, homogeneous er %.1f' % er, s['eps_eff'], er, s['eps_eff'] / er - 1))
    w, sp, b, er = 0.12, 0.15, 0.4816, 4.4
    p = stripline_pair(w, sp, 1e-4, b / 2 - 0.5e-4, er, b / 2 - 0.5e-4, er, res=res)
    ze, zo = cohn_coupled_stripline(w, sp, b, er)
    rows.append(('coupled stripline Z_odd  w %.2f s %.2f b %.4f vs Cohn' % (w, sp, b), p['z_odd'], zo, p['z_odd'] / zo - 1))
    rows.append(('coupled stripline Z_even w %.2f s %.2f b %.4f vs Cohn' % (w, sp, b), p['z_even'], ze, p['z_even'] / ze - 1))
    for w, h, t, er in ((0.15, 0.0994, 0.035, 4.1), (0.12, 0.0994, 0.035, 4.1), (0.3, 0.2, 0.035, 4.5)):
        m = microstrip(w, t, h, er, res=res)
        hj = hammerstad_jensen(w, h, t, er)
        rows.append(('microstrip eps_eff w %.2f h %.4f t %.4f er %.1f vs H-J' % (w, h, t, er), m['eps_eff'], hj['eps_eff'], m['eps_eff'] / hj['eps_eff'] - 1))
        rows.append(('microstrip Z0      w %.2f h %.4f t %.4f er %.1f vs H-J' % (w, h, t, er), m['z0'], hj['z0'], m['z0'] / hj['z0'] - 1))
    return rows


if __name__ == '__main__':
    import time
    t0 = time.time()
    for r in self_test():
        print('%-62s %9.4f %9.4f %+7.2f %%' % (r[0], r[1], r[2], 100 * r[3]))
    print('%.1f s' % (time.time() - t0))
