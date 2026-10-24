"""Report courtyard overlaps and edge-clearance problems of the generated (unrouted) board, with bounding boxes."""
import os, sys, re, pcbnew
pcb = sys.argv[1]
b = pcbnew.LoadBoard(pcb)
rep = '/tmp/claude-0/-home-user-lunar-tear/8e7c1580-4b4b-59e1-9722-29cf444c6384/scratchpad/overlap_drc.txt'
pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, False)
txt = open(rep).read()
fps = {f.GetReference(): f for f in b.GetFootprints()}
def bbox(ref):
    f = fps[ref]; bb = f.GetBoundingBox(False, False)
    return f'{ref}@({pcbnew.ToMM(bb.GetX()):.1f},{pcbnew.ToMM(bb.GetY()):.1f})-({pcbnew.ToMM(bb.GetRight()):.1f},{pcbnew.ToMM(bb.GetBottom()):.1f}){"B" if f.IsFlipped() else "F"}'
pairs = set()
for m in re.finditer(r'\[courtyards_overlap\].*?\n.*?\n\s+@\([^)]*\): Footprint (\w+)\n\s+@\([^)]*\): Footprint (\w+)', txt):
    pairs.add(tuple(sorted(m.groups())))
for a, c in sorted(pairs): print('OVERLAP', bbox(a), bbox(c))
for m in re.finditer(r'\[copper_edge_clearance\][^\n]*\n[^\n]*\n\s+@\(([^)]*)\): ([^\n]*)\n\s+@\(([^)]*)\): ([^\n]*)', txt): print('EDGE', m.group(1), m.group(2), '|', m.group(3), m.group(4))
print(re.findall(r'\*\* Found (\d+) ([A-Za-z ]+?) \*\*', txt))
