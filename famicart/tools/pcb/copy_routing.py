#!/usr/bin/env python3
"""Carry the routing of one board file over to a freshly generated board of the same placement.

The generators always start from an unrouted board. When a change does not move any pad (outline, silkscreen, solder
mask, edge rails, notes), routing the board again would only produce a different, unreviewed layout; this tool copies
every track and via of the old board onto the new one, net by net name, fills the zones and runs the design rule check.
It refuses to write when a net of the old routing does not exist on the new board, and reports rule violations and
open connections of the result (parts that did move show up there).
    python3 copy_routing.py routed_old.kicad_pcb new.kicad_pcb"""
import sys, os, re, tempfile
import pcbnew

def main():
    src = pcbnew.LoadBoard(sys.argv[1]); dst = pcbnew.LoadBoard(sys.argv[2])
    nets = {dst.GetNetInfo().GetNetItem(i).GetNetname(): dst.GetNetInfo().GetNetItem(i) for i in range(dst.GetNetCount())}
    have = {(t.GetClass(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetLayer()) for t in dst.GetTracks()}
    missing = sorted({t.GetNetname() for t in src.GetTracks()} - set(nets))
    if missing: raise SystemExit('copy_routing: the new board has no net %s' % missing)
    nt = nv = 0
    for t in src.GetTracks():
        if (t.GetClass(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetLayer()) in have: continue
        if t.GetClass() == 'PCB_VIA':
            v = pcbnew.PCB_VIA(dst); v.SetPosition(t.GetPosition()); v.SetViaType(t.GetViaType()); v.SetWidth(t.GetWidth()); v.SetDrill(t.GetDrillValue())
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[t.GetNetname()]); dst.Add(v); nv += 1
        else:
            k = pcbnew.PCB_TRACK(dst); k.SetStart(t.GetStart()); k.SetEnd(t.GetEnd()); k.SetWidth(t.GetWidth()); k.SetLayer(t.GetLayer())
            k.SetNet(nets[t.GetNetname()]); dst.Add(k); nt += 1
    pcbnew.SaveBoard(sys.argv[2], dst); dst = pcbnew.LoadBoard(sys.argv[2])
    pcbnew.ZONE_FILLER(dst).Fill(dst.Zones()); dst.BuildConnectivity()
    rep = os.path.join(tempfile.mkdtemp(prefix='copy_routing_'), 'drc.txt')
    pcbnew.WriteDRCReport(dst, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    errors = [b for b in re.split(r'\n(?=\[)', open(rep).read()) if 'Severity: error' in b and not b.startswith('[unconnected')]
    nopen = dst.GetConnectivity().GetUnconnectedCount(False)
    pcbnew.SaveBoard(sys.argv[2], dst)
    print('copy_routing: %d tracks and %d vias copied; design rule errors %d, open connections %d' % (nt, nv, len(errors), nopen))
    for b in errors[:12]: print('   ', ' | '.join(l.strip()[:90] for l in b.strip().splitlines()[:4:1] if not l.strip().startswith('Rule')))
    sys.exit(1 if errors or nopen else 0)

if __name__ == '__main__':
    main()
