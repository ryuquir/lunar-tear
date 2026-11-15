#!/usr/bin/env python3
"""Compare the rev H footprints of famicart.pretty with JLCPCB's own library footprints (EasyEDA), pad by pad, with the
comparison check_cpl.py makes for every CPL row (check_cpl.fits: at 0 / 90 / 180 / 270 degrees every library pad must
land within check_cpl.FIT = 0.40 mm of a KiCad pad, with as many pads on both sides and the same pad numbers).
  USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC  C165948   EasyEDA names a pad shared by two pins "A1B12" and the shell pads
                                                     "1"-"4"; KiCad has A1 and B12 on one spot and four "S1". Both
                                                     sides are put into one naming (A1+B12, S1) before comparing.
                                                     The footprint is HRO's land pattern on the EasyEDA origin
                                                     (famicart.pretty/README.md): its two peg holes and four shell legs
                                                     must lie within 0.02 mm of the library's.
  microSD_HRO_TF-01A                       C91145    also pad sizes and the two non-plated holes
  L_SXN_SMNR4020                           C135262   also pad sizes
  QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia  C42415655  (and the original with the nine holes, which must NOT fit)
The library data is read from <code>.json files (the EasyEDA component API answer, as check_cpl.py downloads it):
    python3 -I tests/check_footprints_easyeda.py --cache DIR      files already downloaded into DIR
    python3 -I tests/check_footprints_easyeda.py --fetch DIR      download into DIR (new or empty) first
Run it with -I: the downloaded files are data from the network. Exit status 1 when a footprint does not fit."""
import os, sys, json, math, re, argparse, tempfile, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
os.environ['FC_DESIGN'] = os.environ.get('FC_DESIGN', 'design_revg')               # check_cpl reads a design and
os.environ['FC_HW_DIR'] = os.environ.get('FC_HW_DIR', tempfile.mkdtemp(prefix='fc_easyeda_'))   # FC_HW_DIR on import
import pcbnew
from pcbnew import ToMM
import check_cpl

CASES = [  # (KiCad footprint, LCSC code, name map, extra checks, must fit)
    ('famicart:USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC', 'C165948', 'usb', False, True),
    ('famicart:microSD_HRO_TF-01A', 'C91145', None, True, True),
    ('famicart:L_SXN_SMNR4020', 'C135262', None, True, True),
    ('famicart:QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia', 'C42415655', None, False, True),
    ('famicart:QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm', 'C42415655', None, False, False),
]

def fetch(code, d):
    req = urllib.request.Request(check_cpl.API % code, headers={'User-Agent': 'parts-check/1.0', 'Accept': 'application/json'})
    data = urllib.request.urlopen(req, timeout=60).read()
    open(os.path.join(d, code + '.json'), 'wb').write(data)

def library(path):
    """(title, [(number, x, y)], [(number, x, y, w, h)], [(x, y, diameter)]) of the library footprint, mm from its
    origin, y down; the pad list is the one check_cpl.library_pads() makes from the same answer."""
    d = json.load(open(path))['result']
    data = d['packageDetail']['dataStr']; ox, oy = float(data['head']['x']), float(data['head']['y'])
    pads, sized, holes = [], [], []
    for shape in data['shape']:
        f = shape.split('~')
        if f[0] == 'PAD' and f[8]:
            pads.append((f[8], (float(f[2]) - ox) * 0.254, (float(f[3]) - oy) * 0.254))           # = check_cpl.library_pads
            sized.append((f[8], (float(f[2]) - ox) * 0.254, (float(f[3]) - oy) * 0.254, float(f[4]) * 0.254, float(f[5]) * 0.254))
        elif f[0] == 'HOLE':
            holes.append(((float(f[1]) - ox) * 0.254, (float(f[2]) - oy) * 0.254, 2 * float(f[3]) * 0.254))
    return d['packageDetail'].get('title', '?'), pads, sized, holes

def kicad(fpname):
    lib, name = fpname.split(':')
    fp = pcbnew.FootprintLoad(os.path.join(check_cpl.gen_pcb.HW_LIB, 'famicart.pretty'), name)
    pads = [(p.GetNumber(), ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), ToMM(p.GetSize().x), ToMM(p.GetSize().y)) for p in fp.Pads() if p.GetNumber()]
    holes = [(ToMM(p.GetPosition().x), ToMM(p.GetPosition().y), ToMM(p.GetDrillSize().x)) for p in fp.Pads()
             if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    return pads, holes

def usb_names(lib, kic):
    """One naming for both: a pad that serves two pins is 'A1+B12' (KiCad: two pads on one spot), shell pads 'S1'."""
    lib2 = [('S1' if n.isdigit() else '+'.join(sorted(re.findall(r'[AB]\d+', n))), x, y) for n, x, y in lib]
    groups = []
    for n, x, y in kic:
        for g in groups:
            if abs(g[1] - x) < 1e-3 and abs(g[2] - y) < 1e-3 and n != 'S1': g[0].append(n); break
        else: groups.append(([n], x, y))
    kic2 = [('+'.join(sorted(ns)), x, y) for ns, x, y in groups]
    return lib2, kic2

def main():
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--cache'); g.add_argument('--fetch'); a = ap.parse_args()
    d = os.path.abspath(a.cache or a.fetch)
    if a.fetch:
        os.makedirs(d, exist_ok=True)
        if os.listdir(d): raise SystemExit('--fetch: %s is not empty' % d)
        for code in sorted({c[1] for c in CASES}): fetch(code, d); print('downloaded', code)
    bad = []
    for fpname, code, names, extra, must in CASES:
        title, lib, sized, lholes = library(os.path.join(d, code + '.json'))
        kp, kholes = kicad(fpname)
        kic = [(n, x, y) for n, x, y, w, h in kp]
        l2, k2 = usb_names(lib, kic) if names == 'usb' else (lib, kic)
        fit = check_cpl.fits(l2, k2)
        ok0 = 0 in fit and fit[0][1] == 'same numbers'
        worst = fit[0][0] if 0 in fit else float('nan')
        print('%-52s %-9s %-40s pads %3d / %3d  fits at %s  worst %.3f mm  -> %s' % (fpname.split(':')[1], code, title, len(l2), len(k2),
              ', '.join('%d (%s)' % (r, v[1]) for r, v in sorted(fit.items())) or 'none', worst,
              ('OK' if ok0 else 'NO FIT') + ('' if must else ' (expected: it must not fit)')))
        if ok0 != must: bad.append(fpname)
        if names == 'usb' and ok0:
            per = sorted(((n, min(math.hypot(x - kx, y - ky) for kn, kx, ky in k2 if kn == n)) for n, x, y in l2), key=lambda t: -t[1])
            print('      largest pad offsets: %s' % ', '.join('%s %.3f' % t for t in per[:4]))
            mech = []                    # the parts of the connector that fix where it sits: peg holes and shell legs
            for (x, y, dia) in lholes:
                k = min(kholes, key=lambda h: math.hypot(h[0] - x, h[1] - y)); mech.append(math.hypot(k[0] - x, k[1] - y))
                print('      peg hole (%.3f, %.3f) d %.2f: footprint hole %.3f mm away, d %.2f' % (x, y, dia, mech[-1], k[2]))
            for n, x, y in l2:
                if n == 'S1': mech.append(min(math.hypot(x - kx, y - ky) for kn, kx, ky in k2 if kn == 'S1'))
            print('      peg holes and shell legs within %.3f mm of the library (0.02 allowed)' % max(mech))
            if len(lholes) != 2 or len(mech) != 6 or max(mech) > 0.02: bad.append(fpname + ' peg holes / shell legs')
        if extra and ok0:
            size_bad = []
            for n, x, y, w, h in sized:
                k = min((q for q in kp if q[0] == n), key=lambda q: math.hypot(q[1] - x, q[2] - y))
                if abs(k[3] - w) > 0.002 or abs(k[4] - h) > 0.002 or math.hypot(k[1] - x, k[2] - y) > 0.002: size_bad.append(n)
            print('      pad positions and sizes equal to the library to 0.002 mm: %s' % ('yes' if not size_bad else 'NO: %s' % size_bad))
            if size_bad: bad.append(fpname + ' pad sizes')
            if lholes or kholes:
                hb = len(lholes) != len(kholes) or any(min(math.hypot(h[0] - x, h[1] - y) + abs(h[2] - dia) for h in kholes) > 0.002 for x, y, dia in lholes)
                print('      non-plated holes: library %s, footprint %s -> %s' % ([(round(x, 3), round(y, 3), round(dd, 2)) for x, y, dd in lholes],
                      [(round(x, 3), round(y, 3), round(dd, 2)) for x, y, dd in kholes], 'equal' if not hb else 'DIFFERENT'))
                if hb: bad.append(fpname + ' holes')
    print('footprint check against JLCPCB library:', 'OK' if not bad else 'FAILED %s' % bad)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
