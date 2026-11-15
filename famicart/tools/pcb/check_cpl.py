#!/usr/bin/env python3
"""Verify the rotations in jlcpcb/cpl_jlc.csv against JLCPCB's own part library, pad by pad.

JLCPCB places a part with the footprint of its part library (the EasyEDA footprint of the LCSC number); the angle in
the CPL turns THAT footprint, and its zero position differs from KiCad's for several packages. For every part type
that JLCPCB places, this tool
  1. downloads the library footprint of the LCSC number (public EasyEDA component API; only the part number is sent),
  2. finds the rotations (0 / 90 / 180 / 270, counter-clockwise) at which its pads land on the pads of the KiCad
     footprint, and whether the pad numbers agree there,
  3. places the library footprint the way JLCPCB will - turned counter-clockwise by the angle of the CPL row, moved
     to its position - and checks that every library pad lands on the pad with the same number of that very
     footprint on the board (resistors, capacitors and the push button may land number-swapped),
  4. checks that the CPL position is the board position with Y negated, that the part is on the top side, and that
     BOM, CPL and design name exactly the same parts.
Pad names: some library footprints name their pads differently from KiCad (PAD_ALIAS, by LCSC number; a design may add
its own in PAD_ALIAS): a library pad then lands correctly on a board pad that carries one of the names it stands for,
and every board pad must be covered by exactly one library pad (pads stacked on one spot, like A1 / B12 of a USB-C
receptacle, are covered together).
Bottom side (designs with ASSEMBLY = 'both'; see gen_jlc.cpl_table for the angle): a Bottom row is allowed only for a
part on the back of the board that BOTTOM_OK allows there. JLCPCB views it from below, so the library footprint is
turned counter-clockwise by the CPL angle and then mirrored left to right (x -> -x about the CPL position) before it is
compared with the board pads; it must land pad for pad with the same numbers. Because JLCPCB does not document which
way it turns the board over, the placement turned by a further 180 degrees (mirrored top to bottom) must also land pad
on pad: BOTTOM_OK parts work either way round. The part must sit at a multiple of 90 degrees: there the KiCad angle
taken as it is (what JLCPCB's KiCad guide uploads without the plugin) is also within 180 degrees of both readings.
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
FIT = 0.40              # mm: pad centres closer than this count as the same pad (library pads are a little longer)
SYMMETRIC = ('R', 'C', 'SW')    # reference prefixes of parts without polarity ('RN' arrays, 'D', 'Q', 'U' are not in it)
# library pad name -> the KiCad pad names it stands for, by LCSC number (checked against the EasyEDA data, 2026-11-15)
PAD_ALIAS = {
    # HRO TYPE-C-31-M-12: EasyEDA joins the paired contacts (A1B12 = GND, A4B9 = VBUS, ...) and numbers the four shell
    # legs 1-4 ("EH"); KiCad's footprint has A1 and B12 stacked on one spot, and S1 for every shell leg
    'C165948': {'A1B12': ('A1', 'B12'), 'B1A12': ('B1', 'A12'), 'A4B9': ('A4', 'B9'), 'B4A9': ('B4', 'A9'),
                '1': ('S1',), '2': ('S1',), '3': ('S1',), '4': ('S1',)},
    # KT-0603R red LED: EasyEDA pin 1 = A (anode), 2 = K; KiCad's LED footprints: pad 1 = K, 2 = A
    'C2286': {'1': ('2',), '2': ('1',)},
}
STACK = 0.01            # mm: board pads this much farther than the nearest one still count as the same spot

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

def placed(lib, row, bottom=False, extra=0.0):
    """Library pads [(number, x, y)] as JLCPCB places them from one CPL row: turned counter-clockwise by the CPL angle
    (JLCPCB: "Positive values are counter clockwise"), moved to the CPL position. Board coordinates, y pointing down.
    bottom: a Bottom row, seen from below: turned in that view, then mirrored left to right into the board's top view.
    extra: degrees added to the CPL angle (180: the other way of turning the board over)."""
    cx, cy = float(row['Mid X'].rstrip('m')), -float(row['Mid Y'].rstrip('m'))
    out = []
    for (n, x, y) in lib:
        tx, ty = turn(x, y, float(row['Rotation']) + extra)
        out.append((n, cx - tx if bottom else cx + tx, cy + ty))
    return out

def land(lib, board, alias=None, symm=False):
    """Lay placed library pads [(number, x, y)] on board pads [(number, x, y)] with pad-name aliases
    {library name: (board names)}. Returns (worst distance in mm, 'same numbers' | 'same groups' | None):
    'same numbers' when every library pad lands on board pads that carry one of its names and every board pad is
    covered by exactly one library pad; 'same groups' (only with symm) when the numbers are swapped one to one."""
    alias = alias or {}
    hits, worst, same, groups = [0] * len(board), 0.0, True, {}
    for (n, px, py) in lib:
        d = [math.hypot(px - q[1], py - q[2]) for q in board]
        dmin = min(d); worst = max(worst, dmin)
        spot = [i for i, x in enumerate(d) if x <= dmin + STACK]
        for i in spot: hits[i] += 1
        nums = {board[i][0] for i in spot}
        if not nums <= set(alias.get(n, (n,))): same = False
        groups.setdefault(n, set()).update(nums)
    once = all(h == 1 for h in hits)
    if worst > FIT or not once: return worst, None
    if same: return worst, 'same numbers'
    targets = [next(iter(v)) for v in groups.values() if len(v) == 1]
    if symm and len(targets) == len(groups) and len(set(targets)) == len(targets) and set(targets) == {q[0] for q in board}: return worst, 'same groups'
    return worst, None

def fits_alias(lib, kic, alias, symm):
    """fits() for a footprint with pad-name aliases, by land()."""
    out = {}
    for deg in (0, 90, 180, 270):
        worst, how = land([(n,) + turn(x, y, deg) for (n, x, y) in lib], kic, alias, symm)
        if how: out[deg] = (worst, how)
    return out

def main():
    lcsc = getattr(D, 'LCSC', {})
    aliases = dict(PAD_ALIAS, **getattr(D, 'PAD_ALIAS', {}))
    both = getattr(D, 'ASSEMBLY', 'top') == 'both'
    if both: import gen_jlc
    board = pcbnew.LoadBoard(os.path.join(HW, 'famicart.kicad_pcb'))
    cpl_rows = list(csv.DictReader(open(os.path.join(HW, 'jlcpcb', 'cpl_jlc.csv'))))
    cpl = {r['Designator']: r for r in cpl_rows}
    bom = [d for r in csv.DictReader(open(os.path.join(HW, 'jlcpcb', 'bom_jlc.csv'))) for d in r['Designator'].split(',')]
    want = {ref for ref, (lib, sym, val, fpname, _) in D.PARTS.items() if val.split(' (')[0] in lcsc}
    rows, bad, table = [], [], {}
    # the three lists of placed parts must be the same set, each part once
    if len(cpl_rows) != len(cpl): bad.append('the CPL names a designator twice')
    if len(bom) != len(set(bom)): bad.append('the BOM names a designator twice')
    if set(cpl) != want: bad.append('CPL designators differ from the design: %s' % sorted(set(cpl) ^ want)[:8])
    if set(bom) != want: bad.append('BOM designators differ from the design: %s' % sorted(set(bom) ^ want)[:8])
    for ref in sorted(want & set(cpl)):
        lib_, sym_, val, fpname, _ = D.PARTS[ref]; key = val.split(' (')[0]; row = cpl[ref]
        if key not in table:
            code = lcsc[key][0]
            try: pkg, lp = library_pads(code)
            except Exception as e:
                print('could not read the JLCPCB library footprint of %s: %s' % (code, e)); sys.exit(2)
            # table of rotation offsets against the KiCad library footprint (for the notes; the test below does not use it)
            symm = ''.join(ch for ch in ref if ch.isalpha()) in SYMMETRIC
            if code in aliases: ok = fits_alias(lp, kicad_pads(fpname), aliases[code], symm)
            else: ok = {d: v for d, v in fits(lp, kicad_pads(fpname)).items() if v[1] == 'same numbers' or symm}
            table[key] = (code, pkg, lp, [])
            rows.append([key, code, pkg, fpname.split(':')[1], ' '.join('%d' % d for d in sorted(ok)) or 'none'])
        code, pkg, lp, worsts = table[key]
        fp = board.FindFootprintByReference(ref)
        if fp is None: bad.append('%s: not on the board' % ref); continue
        bottom = both and fp.IsFlipped() and row['Layer'] == 'Bottom' and gen_jlc.bottom_ok(ref)
        if both and not bottom and (fp.IsFlipped() or row['Layer'] != 'Top'):
            bad.append('%s: side of the board (%s) and CPL layer (%s) disagree, or the part is on the bottom side and BOTTOM_OK does not allow it there' % (ref, 'back' if fp.IsFlipped() else 'front', row['Layer']))
        elif not both and (fp.IsFlipped() or row['Layer'] != 'Top'): bad.append('%s: side of the board (%s) and CPL layer (%s) disagree or are not the top' % (ref, 'back' if fp.IsFlipped() else 'front', row['Layer']))
        x, y = ToMM(fp.GetPosition().x), ToMM(fp.GetPosition().y)
        cx, cy = float(row['Mid X'].rstrip('m')), float(row['Mid Y'].rstrip('m'))
        if abs(cx - x) > 0.01 or abs(cy + y) > 0.01: bad.append('%s: CPL position (%.3f, %.3f) is not the board position (%.3f, %.3f) with Y negated' % (ref, cx, cy, x, y))
        # end to end: every library pad, placed as the CPL says, must land on the pad of this very footprint that has
        # the same number (so the same net). Parts without polarity may also land number-swapped, group on group.
        pads = [(p.GetNumber(), ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)) for p in fp.Pads() if p.GetNumber()]
        symm = ''.join(ch for ch in ref if ch.isalpha()) in SYMMETRIC
        if bottom or code in aliases:    # pad-name aliases and the bottom side: land() (stacked pads, mirrored placement)
            worst, how = land(placed(lp, row, bottom=bottom), pads, aliases.get(code), symm)
            if bottom:                   # the other way of turning the board over: a further 180 degrees, pad on pad
                worst2, how2 = land(placed(lp, row, bottom=True, extra=180.0), pads, aliases.get(code), True)
                if how and not how2: bad.append('%s (%s, %s): bottom side, turned by a further 180 degrees the library pads do not land pad on pad (miss up to %.2f mm): not a part for BOTTOM_OK' % (ref, key, code, worst2))
                worst = max(worst, worst2)
                a = fp.GetOrientationDegrees() % 90.0
                if min(a, 90.0 - a) > 0.01:
                    bad.append('%s: on the bottom side at %.1f degrees; only multiples of 90 degrees come out right under every reading of the bottom-side angle (mirrored, mirrored and turned by 180, or the KiCad angle as it is)' % (ref, fp.GetOrientationDegrees()))
            worsts.append(worst)
            if how is None:
                got = sorted({(a, b) for (a, px, py) in placed(lp, row, bottom=bottom) for b in [min(pads, key=lambda q: math.hypot(px - q[1], py - q[2]))[0]]})
                bad.append('%s (%s, %s): at CPL rotation %s%s library pads miss the board pads by up to %.2f mm or land on other pad numbers: %s'
                           % (ref, key, code, row['Rotation'], ' (bottom side, mirrored)' if bottom else '', worst, got[:12]))
            continue
        pairs, worst = set(), 0.0
        for (n, px, py) in placed(lp, row):
            bn, dist = min(((q[0], math.hypot(px - q[1], py - q[2])) for q in pads), key=lambda t: t[1])
            worst = max(worst, dist); pairs.add((n, bn))
        worsts.append(worst)
        same = all(a == b for a, b in pairs); grouped = len({a for a, b in pairs}) == len(pairs) and len({b for a, b in pairs}) == len({q[0] for q in pads})
        if worst > FIT or len(lp) != len(pads): bad.append('%s (%s, %s): library pads miss the board pads by up to %.2f mm at CPL rotation %s' % (ref, key, code, worst, row['Rotation']))
        elif not (same or (symm and grouped)): bad.append('%s (%s, %s): at CPL rotation %s library pads land on other pad numbers: %s' % (ref, key, code, row['Rotation'], sorted(pairs)))
    for r in rows: r.append('%.2f' % max(table[r[0]][3], default=9.99))
    with open(os.path.join(HW, 'jlcpcb', 'cpl_check.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Part', 'LCSC', 'JLCPCB library footprint', 'KiCad footprint', 'Rotation offsets that fit (deg)', 'Worst pad distance on the board (mm)'])
        w.writerows(rows)
    for r in rows: print('  %-13s %-8s %-42s %-30s offset %-8s worst %s mm' % tuple(r))
    print('CPL check:', 'OK - %d placements land pad for pad on the board (BOM, CPL and design name the same %d parts)' % (len(cpl), len(want)) if not bad else '%d problems' % len(bad))
    for b in bad: print('  FAIL', b)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
