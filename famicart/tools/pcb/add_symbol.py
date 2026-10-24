#!/usr/bin/env python3
"""Append a simple rectangular multi-pin symbol to hardware/famicart.kicad_sym.
pins: list of (number, name, side, kind) with side in 'L','R','T','B'; kind = passive|input|output|bidirectional|power_in|no_connect."""
import os, sys
HW_LIB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'hardware'))
LIB = os.path.join(HW_LIB, 'famicart.kicad_sym')

def pin(num, name, x, y, ang, kind):
    return (f'      (pin {kind} line (at {x:g} {y:g} {ang}) (length 2.54)\n'
            f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'        (number "{num}" (effects (font (size 1.27 1.27)))))\n')

def make_symbol(name, footprint, pins, datasheet='~', value=None):
    L = [p for p in pins if p[2] == 'L']; R = [p for p in pins if p[2] == 'R']
    T = [p for p in pins if p[2] == 'T']; B = [p for p in pins if p[2] == 'B']
    rows = max(len(L), len(R)); cols = max(len(T), len(B), 4)
    h = (rows + 1) * 2.54; w = max(cols * 2.54 + 10.16, 25.4)
    hx, hy = round(w / 2, 2), round(h / 2, 2)
    out = [f'  (symbol "{name}" (in_bom yes) (on_board yes)\n',
           f'    (property "Reference" "U" (at {-hx:g} {hy + 1.27:g} 0) (effects (font (size 1.27 1.27)) (justify left)))\n',
           f'    (property "Value" "{value or name}" (at {-hx + 15:g} {hy + 1.27:g} 0) (effects (font (size 1.27 1.27)) (justify left)))\n',
           f'    (property "Footprint" "{footprint}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n',
           f'    (property "Datasheet" "{datasheet}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n',
           f'    (symbol "{name}_0_1"\n      (rectangle (start {-hx:g} {hy:g}) (end {hx:g} {-hy:g}) (stroke (width 0.254) (type default)) (fill (type background))))\n',
           f'    (symbol "{name}_1_1"\n']
    for i, (num, nm, _, kind) in enumerate(L): out.append(pin(num, nm, -hx - 2.54, round(hy - 2.54 * (i + 1), 2), 0, kind))
    for i, (num, nm, _, kind) in enumerate(R): out.append(pin(num, nm, hx + 2.54, round(hy - 2.54 * (i + 1), 2), 180, kind))
    for i, (num, nm, _, kind) in enumerate(T): out.append(pin(num, nm, round(-hx + 5.08 + 2.54 * i, 2), hy + 2.54, 270, kind))
    for i, (num, nm, _, kind) in enumerate(B): out.append(pin(num, nm, round(-hx + 5.08 + 2.54 * i, 2), -hy - 2.54, 90, kind))
    out.append('    )\n  )\n')
    return ''.join(out)

def add(name, footprint, pins, datasheet='~', value=None):
    s = open(LIB, encoding='utf-8').read()
    if f'(symbol "{name}"' in s: print('exists:', name); return
    body = make_symbol(name, footprint, pins, datasheet, value)
    i = s.rstrip().rfind(')')
    s = s[:i] + body + ')\n'
    open(LIB, 'w', encoding='utf-8').write(s); print('added', name)

if __name__ == '__main__':
    # ---- S29GL01GS (and GL512S/256S/128S) 56-pin TSOP, x16 (used here as x8 on DQ0-7) ----
    gl = {1:'A23',2:'A22',3:'A15',4:'A14',5:'A13',6:'A12',7:'A11',8:'A10',9:'A9',10:'A8',11:'A19',12:'A20',13:'WE#',14:'RESET#',15:'A21',16:'WP#',17:'RY/BY#',
          18:'A18',19:'A17',20:'A7',21:'A6',22:'A5',23:'A4',24:'A3',25:'A2',26:'A1',27:'RFU',28:'DNU',29:'VIO',30:'RFU',31:'A0',32:'CE#',33:'VSS',34:'OE#',
          35:'DQ0',36:'DQ8',37:'DQ1',38:'DQ9',39:'DQ2',40:'DQ10',41:'DQ3',42:'DQ11',43:'VCC',44:'DQ4',45:'DQ12',46:'DQ5',47:'DQ13',48:'DQ6',49:'DQ14',50:'DQ7',
          51:'DQ15',52:'VSS',53:'RFU',54:'A16',55:'A25',56:'A24'}
    def kind(n):
        if n.startswith('A') and n[1:].isdigit(): return 'input'
        if n.startswith('DQ'): return 'bidirectional'
        if n in ('VCC', 'VIO', 'VSS'): return 'power_in'
        if n in ('RFU', 'DNU'): return 'no_connect'
        if n == 'RY/BY#': return 'open_collector'
        return 'input'
    addr = sorted([p for p, n in gl.items() if n.startswith('A') and n[1:].isdigit()], key=lambda p: int(gl[p][1:]))
    dq = sorted([p for p, n in gl.items() if n.startswith('DQ')], key=lambda p: int(gl[p][2:]))
    ctrl = [p for p, n in gl.items() if n in ('CE#', 'OE#', 'WE#', 'RESET#', 'WP#', 'RY/BY#')]
    pw = [p for p, n in gl.items() if n in ('VCC', 'VIO')]; gnd = [p for p, n in gl.items() if n == 'VSS']; nc = [p for p, n in gl.items() if n in ('RFU', 'DNU')]
    pins = [(str(p), gl[p], 'L', kind(gl[p])) for p in addr] + [(str(p), gl[p], 'R', kind(gl[p])) for p in dq + ctrl + nc] + \
           [(str(p), gl[p], 'T', 'power_in') for p in pw] + [(str(p), gl[p], 'B', 'power_in') for p in gnd]
    add('S29GL01GS_TSOP56', 'Package_SO:TSOP-I-56_18.4x14mm_P0.5mm', pins,
        'https://www.infineon.com/cms/en/product/memories/nor-flash/parallel-nor-flash/', 'S29GL01GS')
    # ---- IS62WV5128 512K x 8 SRAM, 32-pin sTSOP (package H) ----
    sr = {1:'A11',2:'A9',3:'A8',4:'A13',5:'WE#',6:'A18',7:'A15',8:'VDD',9:'A17',10:'A16',11:'A14',12:'A12',13:'A7',14:'A6',15:'A5',16:'A4',17:'A3',18:'A2',
          19:'A1',20:'A0',21:'IO0',22:'IO1',23:'IO2',24:'GND',25:'IO3',26:'IO4',27:'IO5',28:'IO6',29:'IO7',30:'CS#',31:'A10',32:'OE#'}
    addr = sorted([p for p, n in sr.items() if n.startswith('A')], key=lambda p: int(sr[p][1:]))
    io = sorted([p for p, n in sr.items() if n.startswith('IO')], key=lambda p: int(sr[p][2:]))
    pins = [(str(p), sr[p], 'L', 'input') for p in addr] + [(str(p), sr[p], 'R', 'bidirectional') for p in io] + \
           [(str(p), sr[p], 'R', 'input') for p in (30, 32, 5)] + [('8', 'VDD', 'T', 'power_in'), ('24', 'GND', 'B', 'power_in')]
    add('IS62WV5128_sTSOP32', 'Package_SO:TSOP-I-32_11.8x8mm_P0.5mm', pins, 'https://www.issi.com/WW/pdf/62-65WV5128EALL-BLL.pdf', 'IS62WV5128')
