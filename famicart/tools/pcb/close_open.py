#!/usr/bin/env python3
"""Close the last open connections of a routed board, one at a time, without making things worse.

finish_route.py forces a route through by removing the tracks of other nets that are in its way; on a crowded board
those nets then cannot be routed again and the number of open connections grows. This driver makes every step a
transaction on a copy of the board:
  1. route one open connection, removing what is in the way (finish_route.py --only NET, tracks of the nets in the
     protect list stay),
  2. route everything that this opened, using free room only (finish_route.py --no-rip),
  3. keep the copy if it has fewer open connections than before and no rule error; otherwise throw it away, protect
     the nets that could not be routed again, and try the connection once more (up to --tries times).
    FC_DESIGN=design_revg python3 close_open.py board.kicad_pcb [--tries 6]"""
import os, sys, re, shutil, subprocess, argparse, tempfile
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--tries', type=int, default=6)
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
    for net in sorted(set(opens)):
        protect = set()
        for attempt in range(args.tries):
            base, _ = state(args.pcb)
            if net not in base: break
            trial = os.path.join(work, 'famicart.kicad_pcb')
            for ext in ('.kicad_pcb', '.kicad_pro'):
                src = os.path.splitext(args.pcb)[0] + ext
                if os.path.exists(src): shutil.copy(src, os.path.splitext(trial)[0] + ext)
            for f in os.listdir(work):
                if f.endswith('.riphistory.json'): os.remove(os.path.join(work, f))
            log = run(trial, '--only', net, '--rounds', '1', '--protect', ','.join(sorted(protect)))
            ripped = sorted(set(re.findall(r"'([^']+)'", ' '.join(re.findall(r'ripping up \d+ items of (\[[^\]]*\])', log)))))
            log2 = run(trial, '--no-rip', '--rounds', '3')
            now, err = state(trial)
            print('  %s, try %d: removed tracks of %s -> open %d (was %d), rule errors %d' % (net, attempt + 1, ripped or 'nothing', len(now), len(base), err))
            if len(now) < len(base) and err == 0:
                shutil.copy(trial, args.pcb); print('    kept'); break
            stuck = set(now) - {net}
            if not ripped or not (stuck | set(ripped)) - protect: print('    no further way for', net); break
            protect |= stuck if stuck else set(ripped)
    opens, errors = state(args.pcb)
    print('open connections now:', len(opens), sorted(set(opens)), '| rule errors:', errors)
    sys.exit(1 if opens or errors else 0)

if __name__ == '__main__':
    main()
