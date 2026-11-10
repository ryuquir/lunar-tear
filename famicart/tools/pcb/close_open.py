#!/usr/bin/env python3
"""Close the last open connections of a routed board, one at a time, without making things worse.

finish_route.py forces a route through by removing the tracks of other nets that are in its way; on a crowded board
those nets then cannot be routed again and the number of open connections grows. This driver makes every step a
transaction on a copy of the board:
  1. route one open connection, removing what is in the way (finish_route.py --only NET, tracks of the nets in the
     protect list stay),
  2. route everything that this opened, using free room only (finish_route.py --no-rip),
  3. keep the copy if it has fewer open connections than before and no rule error. A copy with the same number, but
     with another connection open, is kept as a sideways step once per such state (the next try starts from there).
     Otherwise the copy is thrown away, the nets that could not be routed again are protected, and the connection is
     tried once more. --tries limits the number of steps in total.
    FC_DESIGN=design_revg python3 close_open.py board.kicad_pcb [--tries 12]"""
import os, sys, re, shutil, subprocess, argparse, tempfile
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--tries', type=int, default=12)
args = ap.parse_args()

def state(path):
    """(open connections [(net, text)], number of rule errors) of a board file."""
    b = pcbnew.LoadBoard(path); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
    rep = os.path.join(tempfile.mkdtemp(prefix='close_open_'), 'drc.txt')
    pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    opens, errors = [], 0
    for blk in re.split(r'\n(?=\[)', open(rep).read()):
        if blk.startswith('[unconnected_items]'):
            m = re.search(r'\[([^\]]+)\] (?:on|of)', blk.split('\n', 2)[2] if blk.count('\n') >= 2 else blk)
            opens.append(m.group(1) if m else '?')
        elif 'Severity: error' in blk and not blk.startswith('[starved_thermal]'): errors += 1
    return opens, errors

def run(board, *opts):
    r = subprocess.run([sys.executable, os.path.join(HERE, 'finish_route.py'), board] + list(opts), capture_output=True, text=True)
    return '\n'.join(l for l in (r.stdout + r.stderr).splitlines() if 'memory leak' not in l)

def main():
    opens, errors = state(args.pcb)
    print('open connections:', len(opens), sorted(set(opens)), '| rule errors:', errors)
    work = tempfile.mkdtemp(prefix='close_open_')
    seen = {frozenset(opens)}; protect = {}; tries = 0
    while opens and tries < args.tries:
        net = sorted(set(opens), key=lambda n: len(protect.get(n, ())))[0]; tries += 1
        trial = os.path.join(work, 'famicart.kicad_pcb')
        for ext in ('.kicad_pcb', '.kicad_pro'):
            src = os.path.splitext(args.pcb)[0] + ext
            if os.path.exists(src): shutil.copy(src, os.path.splitext(trial)[0] + ext)
        for f in os.listdir(work):
            if f.endswith('.riphistory.json'): os.remove(os.path.join(work, f))
        log = run(trial, '--only', net, '--rounds', '1', '--protect', ','.join(sorted(protect.get(net, ()))))
        ripped = sorted(set(re.findall(r"'([^']+)'", ' '.join(re.findall(r'ripping up \d+ items of (\[[^\]]*\])', log)))))
        run(trial, '--no-rip', '--rounds', '3')
        now, err = state(trial)
        better = len(now) < len(opens) and err == 0
        sideways = len(now) == len(opens) and err == 0 and frozenset(now) not in seen       # another connection is open instead: a new position to try from
        print('  try %d, %s: removed tracks of %s -> open %d %s (was %d), rule errors %d%s' % (tries, net, ripped or 'nothing', len(now), sorted(set(now)), len(opens), err,
              ' - kept' if better else ' - kept as a sideways step' if sideways else ''), flush=True)
        if better or sideways:
            shutil.copy(trial, args.pcb); opens = now; seen.add(frozenset(now)); continue
        stuck = set(now) - {net}
        protect.setdefault(net, set()).update(stuck if stuck else ripped)
        if not ripped and 'no path' in log: protect.setdefault(net, set()).add('?')        # nothing to try differently for this net
    opens, errors = state(args.pcb)
    print('open connections now:', len(opens), sorted(set(opens)), '| rule errors:', errors)
    sys.exit(1 if opens or errors else 0)

if __name__ == '__main__':
    main()
