#!/usr/bin/env python3
"""Bring the Value fields of a routed board in line with the design, without touching anything else.

BOM, CPL and the schematic are written from the design file; the board's footprints carry the value they had when
gen_pcb.py placed them. When only a value changes after routing (rev H: 1k arrays replaced by 680 ohm arrays on the data
lines, same footprint, same nets), the board would keep the old text. This tool sets every footprint's Value to the
design's and stops (exit 1) if anything else differs: a reference missing on either side, or another footprint. The zones
on the design's THT_THERMAL_LAYERS give plated holes thermal reliefs (gen_pcb.py does the same on a new board).
    FC_DESIGN=design_revh python3 sync_values.py board.kicad_pcb [--dry]"""
import os, sys, argparse, importlib
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('pcb'); ap.add_argument('--dry', action='store_true')
args = ap.parse_args()
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))

def main():
    board = pcbnew.LoadBoard(args.pcb)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    bad = []; changed = []
    for ref, (lib, sym, val, fpid, pos) in D.PARTS.items():
        fp = fps.get(ref)
        if fp is None: bad.append('%s: in the design, not on the board' % ref); continue
        if fp.GetFPIDAsString() != fpid: bad.append('%s: footprint %s on the board, %s in the design' % (ref, fp.GetFPIDAsString(), fpid)); continue
        if fp.GetValue() != val: changed.append((ref, fp.GetValue(), val)); fp.SetValue(val)
    for b in bad: print('sync_values:', b)
    if bad: return 1
    for ref, old, new in changed: print('  %-6s %s -> %s' % (ref, old, new))
    thermal = 0                # the design's THT_THERMAL_LAYERS (gen_pcb.py add_zone): zones there give plated holes thermal reliefs
    for z in board.Zones():
        if not z.GetIsRuleArea() and board.GetLayerName(z.GetLayer()) in getattr(D, 'THT_THERMAL_LAYERS', ()) \
                and z.GetPadConnection() != pcbnew.ZONE_CONNECTION_THT_THERMAL:
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL); thermal += 1
    print('sync_values: %d of %d values changed, %d zones set to thermal reliefs for plated holes%s' % (len(changed), len(D.PARTS), thermal, ' (dry run)' if args.dry else ''))
    if (changed or thermal) and not args.dry: pcbnew.SaveBoard(args.pcb, board)
    return 0

if __name__ == '__main__':
    rc = main(); sys.stdout.flush(); os._exit(rc)
