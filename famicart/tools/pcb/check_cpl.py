#!/usr/bin/env python3
"""Verify the rotations in jlcpcb/cpl_jlc.csv against JLCPCB's own part library, pad by pad.

JLCPCB places a part with the footprint of its part library (the EasyEDA footprint of the LCSC number); the angle in
the CPL turns THAT footprint, and its zero position differs from KiCad's for several packages. For every part type
that JLCPCB places, this tool
  1. downloads the library footprint of the LCSC number (public EasyEDA component API; only the part number is sent),
  2. finds the rotations (0 / 90 / 180 / 270, counter-clockwise) at which its pads land on the pads of the KiCad
     footprint, and whether the pad numbers agree there,
  3. checks that every row of cpl_jlc.csv uses (KiCad orientation + such a rotation), and that the CPL position is the
     KiCad footprint position.
Writes jlcpcb/cpl_check.csv. Exit status 1 when a row does not fit, 2 when the library could not be read.
    FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg python3 check_cpl.py"""
import os, sys, csv, json, math, importlib, urllib.request
import pcbnew
from pcbnew import ToMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
import gen_pcb
HW = os.path.abspath(os.environ['FC_HW_DIR'])
API = 'https://easyeda.com/api/products/%s/components?version=6.4.19.5'
FIT = 0.35              # mm: pad centres closer than this count as the same pad (library pads are a little longer)
SYMMETRIC = ('R', 'C', 'SW')    # reference prefixes of parts without polarity ('RN' arrays, 'D', 'Q', 'U' are not in it)

def library_pads(code):
    """[(pad number, x, y)] of the JLCPCB library footprint, mm from the footprint origin, y pointing down."""
    req = urllib.request.Request(API % code, headers={'User-Agent': 'check-cpl/1.0', 'Accept': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=40))['result']
    data = d['packageDetail']['dataStr']; ox, oy = float(data['head']['x']), float(data['head']['y'])
    pads = []
    for shape in data['shape']:
        f = shape.split('~')
        if f[0] == 'PAD' and f[8]: pads.append((f[8], (float(f[2]) - ox) * 0.254, (float(f[3]) - oy) * 0.254))
    return d['packageDetail'].get('title', '?'), pads

def kicad_pads(fpname):
    lib, name = fpname.split(':')
    libdir = os.path.join(gen_pcb.HW_LIB, 'famicart.pretty') if lib == 'famicart' else os.path.join(gen_pcb.SYS_FP, lib + '.pretty')
    fp = pcbnew.FootprintLoad(libdir, name)
    return [(p.GetNumber(), ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)) for p in fp.Pads() if p.GetNumber()]

def turn(x, y, deg):    # counter-clockwise as seen on the board, y pointing down
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)

def fits(lib, kic):
    """{rotation: (worst pad distance, 'same numbers' | 'same groups')} for the rotations at which every library pad
    lands on a KiCad pad and pads that share a KiCad number are not mixed with others."""
    out = {}
    for deg in (0, 90, 180, 270):
        worst, pairs = 0.0, set()
        for (n, x, y) in lib:
            tx, ty = turn(x, y, deg)
            kn, dist = min(((k[0], math.hypot(tx - k[1], ty - k[2])) for k in kic), key=lambda t: t[1])
            worst = max(worst, dist); pairs.add((n, kn))
        if worst > FIT or len(lib) != len(kic): continue
        if all(a == b for a, b in pairs): out[deg] = (worst, 'same numbers')
        elif len({a for a, b in pairs}) == len(pairs): out[deg] = (worst, 'same groups')      # each library pad -> one KiCad number
    return out

def main():
    lcsc = getattr(D, 'LCSC', {})
    board = pcbnew.LoadBoard(os.path.join(HW, 'famicart.kicad_pcb'))
    cpl = {r['Designator']: r for r in csv.DictReader(open(os.path.join(HW, 'jlcpcb', 'cpl_jlc.csv')))}
    rows, bad, table = [], [], {}
    for ref, (lib, sym, val, fpname, _) in sorted(D.PARTS.items()):
        key = val.split(' (')[0]
        if key not in lcsc: continue
        if key not in table:
            code = lcsc[key][0]
            try: pkg, lp = library_pads(code)
            except Exception as e:
                print('could not read the JLCPCB library footprint of %s: %s' % (code, e)); sys.exit(2)
            kp = kicad_pads(fpname)
            # A rotation counts when the pad numbers agree. Resistors, capacitors and the push button have no polarity:
            # for them a rotation at which the pads only land on each other (numbers swapped or named differently) counts too.
            sym = ''.join(ch for ch in ref if ch.isalpha()) in SYMMETRIC
            ok = {d: v for d, v in fits(lp, kp).items() if v[1] == 'same numbers' or sym}
            table[key] = (code, pkg, ok, fpname)
            rows.append([key, code, pkg, fpname.split(':')[1], ' '.join('%d' % d for d in sorted(ok)) or 'none',
                         '%.2f' % min((v[0] for v in ok.values()), default=9.99)])
        code, pkg, ok, _ = table[key]
        fp = board.FindFootprintByReference(ref); row = cpl.get(ref)
        if fp is None or row is None: bad.append('%s: missing on the board or in the CPL' % ref); continue
        theta = fp.GetOrientationDegrees() % 360
        want = sorted({int(round(theta + d)) % 360 for d in ok})
        have = int(round(float(row['Rotation']))) % 360
        if have not in want: bad.append('%s (%s, %s): CPL rotation %d, library fit needs %s' % (ref, key, code, have, want or 'no fit'))
        x, y = ToMM(fp.GetPosition().x), ToMM(fp.GetPosition().y)
        cx, cy = float(row['Mid X'].rstrip('m')), float(row['Mid Y'].rstrip('m'))
        if abs(cx - x) > 0.01 or abs(abs(cy) - abs(y)) > 0.01: bad.append('%s: CPL position (%.3f, %.3f) differs from the board (%.3f, %.3f)' % (ref, cx, cy, x, y))
    with open(os.path.join(HW, 'jlcpcb', 'cpl_check.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Part', 'LCSC', 'JLCPCB library footprint', 'KiCad footprint', 'Rotation offsets that fit (deg)', 'Worst pad distance (mm)'])
        w.writerows(rows)
    for r in rows: print('  %-13s %-8s %-42s %-30s fits at %-8s worst %s mm' % tuple(r))
    print('CPL check:', 'OK - %d placements match the JLCPCB library footprints' % len(cpl) if not bad else '%d problems' % len(bad))
    for b in bad: print('  FAIL', b)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
