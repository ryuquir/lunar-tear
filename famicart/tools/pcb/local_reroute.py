#!/usr/bin/env python3
"""Route the open connections of a routed board again with Freerouting, letting it rip up only the wiring in chosen boxes.

finish_route.py / close_open.py work one connection at a time; around a crowded part (rev H: the hub U6 with the microSD
lines, SWD and reset) they find no room, and every forced route breaks another net. Freerouting's own rip-up and
re-route settles such a knot, but run on the whole board it starts from scratch. Here the board as it is goes to the
router: tracks and vias inside the boxes (both ends of a track inside one box, a via's centre inside) are handed over
as ordinary wiring that the router may rip up and route again; everything else stays fixed (protect), and so do the
nets matching --keep everywhere (crystal and supply nets by default). Freerouting then routes the open connections.
The free wiring is replaced by the session's; the result is checked (zone fill, rule check) and written to --out (the
input board by default) only when it has fewer open connections than before and no rule error (--force: always).
    FC_DESIGN=design_revh python3 local_reroute.py board.kicad_pcb --box 20,8,58,48 [--box ...] [--passes 20] [--out new.kicad_pcb]
Box coordinates are KiCad's (mm, y down), not the design's x' / h."""
import os, sys, re, argparse, subprocess, tempfile, shutil, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ap = argparse.ArgumentParser()
ap.add_argument('pcb'); ap.add_argument('--box', action='append', required=True, help='x0,y0,x1,y1 in mm (KiCad coordinates)')
ap.add_argument('--passes', type=int, default=20); ap.add_argument('--oit', default='8'); ap.add_argument('--timeout', type=int, default=3600)
ap.add_argument('--keep', default=r'XIN\d|XOUT\d(_R)?|\+5V|V5_IN|VBUS|GND|\+3V3|\+1V1|SW_.*', help='nets whose wiring always stays fixed (regex)')
ap.add_argument('--out', default=None); ap.add_argument('--force', action='store_true')
ap.add_argument('--ses', default=None, help='import this session file (from an earlier run with the same boxes) instead of routing')
args = ap.parse_args()
import pcbnew
from pcbnew import ToMM
import route_pcb, dsn_export, ses_import, gen_pcb

STATE = r'''
import sys, re, os, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
pcbnew.WriteDRCReport(b, sys.argv[2], pcbnew.EDA_UNITS_MILLIMETRES, True)
opens, errors = [], []
for blk in re.split(r'\n(?=\[)', open(sys.argv[2]).read()):
    if blk.startswith('[unconnected_items]'):
        m = re.search(r'\[([^\]]+)\] (?:on|of)', blk.split('\n', 2)[2] if blk.count('\n') >= 2 else blk)
        opens.append(m.group(1) if m else '?')
    elif 'Severity: error' in blk and not blk.startswith('[starved_thermal]'): errors.append(blk.split('\n')[0][:160])
print(json.dumps([opens, errors])); sys.stdout.flush(); os._exit(0)
'''

# Two child processes: one removes the wiring handed to the router, one imports the session. Done in one process (or in
# this one after the DSN export), the board loaded after removing ~1700 items came back as a bare SwigPyObject.
REMOVE = r'''
import sys, os, json, pcbnew
path, freed = sys.argv[1], set(json.load(open(sys.argv[2])))
b = pcbnew.LoadBoard(path); n = 0
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in freed: b.Remove(t); n += 1
pcbnew.SaveBoard(path, b)
print('removed %d' % n); sys.stdout.flush(); os._exit(0)
'''
IMPORT = r'''
import sys, os, pcbnew
sys.path.insert(0, os.getcwd())
import ses_import
path, ses, via, drill = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
b = pcbnew.LoadBoard(path)
nt, nv = ses_import.import_ses(b, ses, via_dia_mm=via, via_drill_mm=drill)
pcbnew.SaveBoard(path, b)
print('imported %d tracks and %d vias' % (nt, nv)); sys.stdout.flush(); os._exit(0)
'''

def state(path, work):
    """(open connections by net, rule errors) of a board file, from a zone fill and rule check in a child process."""
    r = subprocess.run([sys.executable, '-c', STATE, path, os.path.join(work, 'drc_state.txt')], capture_output=True, text=True)
    return json.loads([l for l in r.stdout.splitlines() if l.startswith('[')][-1])

def main():
    work = tempfile.mkdtemp(prefix='local_reroute_')
    wpcb = os.path.join(work, 'famicart.kicad_pcb')
    for ext in ('.kicad_pcb', '.kicad_pro'):
        src = os.path.splitext(args.pcb)[0] + ext
        if os.path.exists(src): shutil.copy(src, os.path.splitext(wpcb)[0] + ext)
    opens0, err0 = state(wpcb, work)
    print('before: %d open connections %s, %d rule errors' % (len(opens0), sorted(set(opens0)), len(err0)), flush=True)
    board = pcbnew.LoadBoard(wpcb)
    boxes = [tuple(float(v) for v in b.split(',')) for b in args.box]
    keep = re.compile(args.keep)
    def free(t):                                  # a via with its centre in a box, a track with both ends in one box
        if keep.fullmatch(t.GetNetname()): return False
        pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
        return any(all(x0 <= ToMM(p.x) <= x1 and y0 <= ToMM(p.y) <= y1 for p in pts) for x0, y0, x1, y1 in boxes)
    freed = [t for t in board.GetTracks() if free(t)]
    print('handed to the router: %d tracks and vias of %d nets in %d boxes' % (len(freed), len({t.GetNetname() for t in freed}), len(boxes)), flush=True)
    TRK, CLR, VIA, VDR = gen_pcb.rules()
    dsn = os.path.join(work, 'famicart.dsn'); ses = os.path.join(work, 'famicart.ses')
    ids = {t.m_Uuid.AsString() for t in freed}
    dsn_export.export(board, dsn, route_pcb.outline(), track=TRK, clearance=CLR, pad_clearance=CLR, via_dia=VIA, via_drill=VDR,
                      net_width=getattr(gen_pcb.D, 'NET_WIDTH', None), plane_map=route_pcb.PLANE_MAP, own_via_padstacks=route_pcb.OWN_VIAS,
                      free=lambda t: t.m_Uuid.AsString() in ids)
    if args.ses: ses = os.path.abspath(args.ses)
    else:
        cmd = ['xvfb-run', '-a', 'java', '-jar', route_pcb.JAR, '-de', dsn, '-do', ses, '-mp', str(args.passes), '-mt', '1', '-oit', str(args.oit), '-da']
        print('routing in', work, flush=True)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout, cwd=work)
            open(os.path.join(work, 'freerouting.log'), 'w').write(r.stdout + r.stderr)
        except subprocess.TimeoutExpired:
            print('Freerouting did not finish in %d s' % args.timeout)
    if not os.path.exists(ses): raise SystemExit('no session file; see ' + os.path.join(work, 'freerouting.log'))
    json.dump(sorted(ids), open(os.path.join(work, 'freed.json'), 'w'))
    r = subprocess.run([sys.executable, '-c', REMOVE, wpcb, os.path.join(work, 'freed.json')], capture_output=True, text=True, cwd=HERE)
    if not any(l.startswith('removed') for l in r.stdout.splitlines()): raise SystemExit('removing the free wiring failed:\n' + r.stderr[-1500:])
    r = subprocess.run([sys.executable, '-c', IMPORT, wpcb, ses, str(VIA), str(VDR)], capture_output=True, text=True, cwd=HERE)
    line = [l for l in r.stdout.splitlines() if l.startswith('imported')]
    if not line: raise SystemExit('import failed:\n' + r.stderr[-1500:])
    print('session: %s in place of the %d items handed over' % (line[-1], len(ids)), flush=True)
    opens1, err1 = state(wpcb, work)
    print('after: %d open connections %s, %d rule errors%s' % (len(opens1), sorted(set(opens1)), len(err1),
          (': ' + ' | '.join(err1[:6])) if err1 else ''), flush=True)
    out = args.out or args.pcb
    if args.force or (len(opens1) < len(opens0) and not err1):
        for ext in ('.kicad_pcb', '.kicad_pro'):
            src = os.path.splitext(wpcb)[0] + ext
            if os.path.exists(src): shutil.copy(src, os.path.splitext(out)[0] + ext)
        print('written:', out)
    else: print('not written (no fewer open connections, or rule errors); the trial board is', wpcb)
    sys.stdout.flush(); os._exit(0 if not opens1 and not err1 else 1)

if __name__ == '__main__':
    main()
