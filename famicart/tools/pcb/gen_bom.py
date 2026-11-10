#!/usr/bin/env python3
"""Write hardware/bom.csv grouped by value+footprint from design.py."""
import os, sys, csv, collections
sys.path.insert(0, os.path.dirname(__file__))
import os as _os, importlib as _il
_DESIGN = _os.environ.get('FC_DESIGN', 'design')
D = _il.import_module(_DESIGN)
HW_LIB = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'hardware'))   # custom symbols/footprints
HW = _os.path.abspath(_os.environ.get('FC_HW_DIR', HW_LIB))                                                        # outputs
MPN = {  # suggested orderable parts (any equivalent works)
 'Raspberry Pi Pico 2': 'Raspberry Pi SC1631 (Pico 2) / Pico (RP2040) also fits',
 '74LVC541': 'Nexperia 74LVC541APW (TSSOP-20)', '74LVC245': 'Nexperia 74LVC245APW (TSSOP-20)', '74LVC139': 'Nexperia 74LVC139PW (TSSOP-16)',
 '74LVC1G17': 'Nexperia 74LVC1G17GW / TI SN74LVC1G17DBV', '74LVC1G08': 'Nexperia 74LVC1G08GW / TI SN74LVC1G08DBV', '74LVC1G07': 'Nexperia 74LVC1G07GW / TI SN74LVC1G07DBV',
 '100n': 'X7R 0603 16V', '10n': 'X7R 0603 50V', '10u': 'X5R 0805 10V', '2.2k': '0603 1%', '4.7k': '0603 1%', '1k': '0603 1%', '10k': '0603 1%',
 'Famicom 60-pin edge': 'PCB card edge (gold fingers), no part',
 'USB-C': 'HRO TYPE-C-31-M-12 (16-pin USB 2.0 receptacle) or GCT USB4105-GF-A', '5.1k': '0603 1% (USB-C CC pull-down)',
 'RESET': 'E-Switch TL3342 / any 4.7x3.5 mm low-profile tactile', 'RUN/GND': '2-pin 2.54 mm header (optional, wire to the console reset switch)',
 'RUN/GND/LINK pads': 'no part (wire pads)',
 'TP wire pads': 'no part (solder wires from Pico TP2/TP3/TP1 if hand-assembling)', 'USB D+ -> TP_A | TP_B': 'solder jumper, bridge after checking TP2/TP3', 'USB D- -> TP_B | TP_A': 'solder jumper, bridge after checking TP2/TP3',
}
LCSC, HAND = getattr(D, 'LCSC', {}), getattr(D, 'HAND', {})
def suggest(val):
    """Designs with their own part map (rev E on) name the exact part: the generic MPN table above describes the parts
    of the earlier boards (e.g. a different reset switch, and an RP2040 Pico must not be fitted where 5 V reaches the pins)."""
    if val in LCSC: return '%s (LCSC %s, JLCPCB Basic)' % (LCSC[val][1], LCSC[val][0])
    if val in HAND: return 'hand-soldered: ' + ', '.join(HAND[val])
    return MPN.get(val, '')
groups = collections.OrderedDict()
for ref, (lib, sym, val, fp, _) in D.PARTS.items():
    key = (val.split(' (')[0], fp)
    groups.setdefault(key, []).append(ref)
with open(os.path.join(HW, 'bom.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Qty', 'Value', 'Footprint', 'References', 'Suggested part'])
    for (val, fp), refs in groups.items():
        refs.sort(key=lambda r: (r.rstrip('0123456789'), int(''.join(ch for ch in r if ch.isdigit()) or 0)))
        w.writerow([len(refs), val, fp.split(':')[1], ' '.join(refs), suggest(val)])
print('bom written:', os.path.join(HW, 'bom.csv'), len(groups), 'lines')
