#!/usr/bin/env python3
"""Autoroute hardware/famicart.kicad_pcb with Freerouting, import the result, fill zones, run DRC, export fab files."""
import os, re, sys, subprocess, shutil, re
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
import dsn_export, ses_import, gen_pcb
HW_LIB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'hardware'))
HW = os.path.abspath(os.environ.get('FC_HW_DIR', HW_LIB))

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HW, 'famicart.kicad_pcb')
WORK = os.environ.get('FC_WORK', os.path.join(HW, 'build_route'))
JAR = os.environ.get('FREEROUTING_JAR', os.path.expanduser('~/freerouting-1.9.0.jar'))   # 1.9.0 single-threaded routes rev B in ~2 min; 2.0.1 did not finish
PASSES = int(os.environ.get('FC_PASSES', '60'))

def outline(inset=0.4):
    """Routing boundary: board outline shrunk by `inset` so tracks keep the edge clearance."""
    W, H, T, x0, x1, c = gen_pcb.BOARD_W, gen_pcb.BODY_H, gen_pcb.TOTAL_H, gen_pcb.TAB_X0, gen_pcb.TAB_X0 + gen_pcb.TAB_W, gen_pcb.CHAMFER
    i = inset
    return [(i, i), (W - i, i), (W - i, H - i), (x1 - i, H - i), (x1 - i, T - c - i), (x1 - c - i, T - i), (x0 + c + i, T - i), (x0 + i, T - c - i), (x0 + i, H - i), (i, H - i), (i, i)]

def main():
    os.makedirs(WORK, exist_ok=True)
    gen_pcb.main()                     # always start from a freshly generated, unrouted board
    board = pcbnew.LoadBoard(PCB)
    dsn = os.path.join(WORK, 'famicart.dsn'); ses = os.path.join(WORK, 'famicart.ses')
    TRK = float(os.environ.get('FC_TRACK', '0.15')); CLR = float(os.environ.get('FC_CLEAR', '0.15'))
    VIA = float(os.environ.get('FC_VIA', '0.5')); VDR = float(os.environ.get('FC_VIA_DRILL', '0.25'))
    n = dsn_export.export(board, dsn, outline(), track=TRK, clearance=CLR, pad_clearance=CLR, via_dia=VIA, via_drill=VDR)
    print('DSN written with', n, 'nets')
    pre = os.environ.get('FC_SES')            # import an existing session file instead of running the router
    if pre and os.path.exists(pre): ses = pre
    else:
      if os.path.exists(ses): os.remove(ses)
      cmd = ['xvfb-run', '-a', 'java', '-jar', JAR, '-de', dsn, '-do', ses, '-mp', str(PASSES), '-mt', '1', '-oit', os.environ.get('FC_OIT', '8'), '-da']
      print(' '.join(cmd))
      r = subprocess.run(cmd, capture_output=True, text=True, timeout=int(os.environ.get('FC_TIMEOUT', '1500')))
      log = (r.stdout + r.stderr)
      open(os.path.join(WORK, 'freerouting.log'), 'w').write(log)
      tail = [l for l in log.splitlines() if 'INFO' in l and ('pass' in l.lower() or 'complete' in l.lower() or 'routed' in l.lower() or 'incomplete' in l.lower())][-6:]
      print('\n'.join(tail))
    if not os.path.exists(ses): raise SystemExit('Freerouting produced no session file; see ' + os.path.join(WORK, 'freerouting.log'))
    nt, nv = ses_import.import_ses(board, ses, via_dia_mm=VIA, via_drill_mm=VDR)
    pcbnew.SaveBoard(PCB, board); board = pcbnew.LoadBoard(PCB)   # reload: avoids SWIG ownership issues before zone filling
    print('imported tracks', nt, 'vias', nv)
    if pre and os.environ.get('FC_REROUTE', '0') == '1':
        # stage 2: everything routed so far becomes fixed wiring; the router only works on what is still open
        dsn2 = os.path.join(WORK, 'famicart_stage2.dsn'); ses2 = os.path.join(WORK, 'famicart_stage2.ses')
        if os.path.exists(ses2): os.remove(ses2)
        # rip up the imported routing around the still-open connections (from the previous DRC report) so the router has room
        rip = float(os.environ.get('FC_RIP_RADIUS', '0'))
        drc_prev = os.path.join(HW, 'drc_report.txt')
        if rip > 0 and os.path.exists(drc_prev):
            pts = []
            for blk in open(drc_prev).read().split('\n['):
                if blk.startswith('unconnected_items]'):
                    pts += [(float(a), float(b)) for a, b in re.findall(r'@\(([0-9.]+) mm, ([0-9.]+) mm\)', blk)]
            doomed = []
            for t in board.GetTracks():
                if t.GetNetname() in ('GND', '+3V3'): continue                  # keep the power stubs
                pos = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
                if any(((ToMM(p.x) - x) ** 2 + (ToMM(p.y) - y) ** 2) ** 0.5 < rip for p in pos for (x, y) in pts): doomed.append(t)
            for t in doomed: board.Remove(t)
            print('stage 2: ripped up', len(doomed), 'items around', len(pts), 'open points (radius', rip, 'mm)')
            pcbnew.SaveBoard(PCB, board); board = pcbnew.LoadBoard(PCB)
        dsn_export.export(board, dsn2, outline(), track=TRK, clearance=CLR, pad_clearance=CLR, via_dia=VIA, via_drill=VDR)
        cmd = ['xvfb-run', '-a', 'java', '-jar', JAR, '-de', dsn2, '-do', ses2, '-mp', str(PASSES), '-mt', '1', '-oit', os.environ.get('FC_OIT', '8'), '-da']
        print('stage 2:', ' '.join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=int(os.environ.get('FC_TIMEOUT', '1500')))
        open(os.path.join(WORK, 'freerouting_stage2.log'), 'w').write(r.stdout + r.stderr)
        if os.path.exists(ses2):
            nt2, nv2 = ses_import.import_ses(board, ses2, via_dia_mm=VIA, via_drill_mm=VDR)
            pcbnew.SaveBoard(PCB, board); board = pcbnew.LoadBoard(PCB)
            print('stage 2 imported tracks', nt2, 'vias', nv2)
        else: print('stage 2 produced no session')
    filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones())
    board.BuildConnectivity()
    unconnected = board.GetConnectivity().GetUnconnectedCount(True)
    print('unconnected after routing:', unconnected)
    pcbnew.SaveBoard(PCB, board)
    drc = os.path.join(HW, 'drc_report.txt')
    pcbnew.WriteDRCReport(board, drc, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(drc).read()
    m = re.findall(r'\*\* Found (\d+) ([A-Za-z ]+?) \*\*', txt)
    errors = txt.count('Severity: error'); warnings = txt.count('Severity: warning')
    print('DRC:', m if m else txt[:300], '| errors:', errors, 'warnings (library checks etc.):', warnings)
    # fab exports
    fab = os.path.join(HW, 'fab'); shutil.rmtree(fab, ignore_errors=True); os.makedirs(fab)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', {6: 'F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu', 4: 'F.Cu,In1.Cu,In2.Cu,B.Cu'}.get(board.GetCopperLayerCount(), 'F.Cu,B.Cu') + ',F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts,F.Fab,B.Fab', '-o', fab + '/', PCB], check=True, capture_output=True)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '-o', fab + '/', PCB], check=True, capture_output=True)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'pdf', '--layers', 'F.Cu,F.SilkS,F.Fab,Edge.Cuts', '-o', os.path.join(HW, 'famicart_front.pdf'), PCB], check=True, capture_output=True)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'pdf', '--layers', 'B.Cu,B.SilkS,Edge.Cuts', '--mirror', '-o', os.path.join(HW, 'famicart_back.pdf'), PCB], check=True, capture_output=True)
    for name in ('front', 'back'):
        pdf = os.path.join(HW, f'famicart_{name}.pdf')
        png = os.path.join(HW, f'famicart_{name}.png')
        subprocess.run(['pdftoppm', '-r', '250', '-png', '-singlefile', pdf, os.path.join(HW, f'famicart_{name}')], capture_output=True)
        subprocess.run(['convert', png, '-trim', '+repage', '-bordercolor', 'white', '-border', '20', png], capture_output=True)
    print('fab files in', fab)

if __name__ == '__main__':
    main()
