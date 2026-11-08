"""famicart rev F: rev E + two coprocessor Picos for SFC-style expansion chips (docs/08_sfc_coprocessor_roadmap.md).

  Everything of rev E, moved 24 mm down (the body grows from 35.4 to 59.4 mm; the card-edge tab is unchanged), plus:
  U4  Raspberry Pi Pico 2 (front, top row)  CPU-side coprocessor (SA-1 / DSP-n / S-DD1 / SPC7110 ...). Same pin map as
                                            U1: A0-14 and /ROMSEL, /WS share U1's nodes behind the 1k arrays, D0-D7 get
                                            their own 1k array so U1 and U4 can never short each other.
  U5  Raspberry Pi Pico 2 (back, top row)   PPU-side coprocessor (Super FX / Cx4): PA0-13 and /RD share U2's nodes,
                                            PD0-7 through its own 1k array; draws straight into the CHR pages it serves.
  Both join the shared LINK (1k each) and get their own B5819W from +5V. Firmware decides which MCU drives which
  address window; the series resistors make a mistake harmless.
  The cartridge no longer fits a stock Famicom shell (70.1 mm tall); the top-loading slot takes it bare or in a printed shell.
2-layer, PCBA parts all on the front."""


REV = 'rev F'
LAYERS = 2
BODY_H = 59.4                      # rev E 35.4 + 24
DY = 24.0
NOSHIFT = {'U3', 'J2'}             # stay in the (new) top row
SHIFT = [True]

PARTS = {}
def P(ref, lib, sym, val, fp, x, y, rot=0, side='F'):
    if SHIFT[0] and ref not in NOSHIFT: y += DY
    PARTS[ref] = (lib, sym, val, fp, (x, y, rot, side))
NETS = {}
def c(ref, pin, net): NETS.setdefault(ref, {})[str(pin)] = net
_n = {'R': 0, 'C': 0, 'RN': 0, 'D': 0, 'Q': 0}
def nxt(k): _n[k] += 1; return f'{k}{_n[k]}'
R0603 = 'Resistor_SMD:R_0603_1608Metric'; C0603 = 'Capacitor_SMD:C_0603_1608Metric'; C0805 = 'Capacitor_SMD:C_0805_2012Metric'
RARR = 'Resistor_SMD:R_Array_Convex_4x0603'; SOT23 = 'Package_TO_SOT_SMD:SOT-23'
def res(val, x, y, rot, a, b):
    r = nxt('R'); P(r, 'Device', 'R', val, R0603, x, y, rot); c(r, 1, a); c(r, 2, b); return r
def cap(val, fp, x, y, rot, a, b='GND'):
    r = nxt('C'); P(r, 'Device', 'C', val, fp, x, y, rot); c(r, 1, a); c(r, 2, b); return r
def rarr(x, y, rot, pairs):
    """1k x4 array; pairs = [(console_net, mcu_net)] x4 (None for unused)."""
    r = nxt('RN'); P(r, 'Device', 'R_Pack04', '1k x4', RARR, x, y, rot)
    for i, (a, b) in enumerate(pairs): c(r, 1 + i, a); c(r, 8 - i, b)
    return r
def nfet(x, y, rot, g, d):
    q = nxt('Q'); P(q, 'Transistor_FET', '2N7002', '2N7002', SOT23, x, y, rot); c(q, 1, g); c(q, 2, 'GND'); c(q, 3, d); return q
def diode(sym, val, fp, x, y, rot, a, k):
    d = nxt('D'); P(d, 'Diode' if sym == '1N4148WS' else 'Device', sym, val, fp, x, y, rot); c(d, 1, k); c(d, 2, a); return d

# ------------------------------------------------------------------ card edge
P('J1', 'famicart', 'Famicom_CardEdge_60', 'Famicom 60-pin edge', 'famicart:Famicom_CardEdge_60', 45.0, 35.4)
J1 = {1:'GND',2:'CPU_A11',3:'CPU_A10',4:'CPU_A9',5:'CPU_A8',6:'CPU_A7',7:'CPU_A6',8:'CPU_A5',9:'CPU_A4',10:'CPU_A3',11:'CPU_A2',12:'CPU_A1',13:'CPU_A0',14:'CPU_RW',15:'nIRQ',16:'GND',
      17:'PPU_nRD',18:'CIRAM_A10',19:'PPU_A6',20:'PPU_A5',21:'PPU_A4',22:'PPU_A3',23:'PPU_A2',24:'PPU_A1',25:'PPU_A0',26:'PPU_D0',27:'PPU_D1',28:'PPU_D2',29:'PPU_D3',30:'+5V',
      31:None,32:'M2',33:'CPU_A12',34:'CPU_A13',35:'CPU_A14',36:'CPU_D7',37:'CPU_D6',38:'CPU_D5',39:'CPU_D4',40:'CPU_D3',41:'CPU_D2',42:'CPU_D1',43:'CPU_D0',44:'nROMSEL',
      45:'AUDIO_IN',46:'AUDIO_OUT',47:None,48:'CIRAM_nCE',49:'PPU_nA13',50:'PPU_A7',51:'PPU_A8',52:'PPU_A9',53:'PPU_A10',54:'PPU_A11',55:'PPU_A12',56:'PPU_A13',57:'PPU_D7',58:'PPU_D6',59:'PPU_D5',60:'PPU_D4'}
for p, nn in J1.items(): c('J1', p, nn)

# ------------------------------------------------------------------ the three modules
PICO_GP = {0:1,1:2,2:4,3:5,4:6,5:7,6:9,7:10,8:11,9:12,10:14,11:15,12:16,13:17,14:19,15:20,16:21,17:22,18:24,19:25,20:26,21:27,22:29,26:31,27:32,28:34}
PICO_GND = (3, 8, 13, 18, 23, 28, 33, 38)
def pico(ref, x, y, rot, side, gp, vsys):
    P(ref, 'famicart', 'RPi_Pico2', 'Raspberry Pi Pico 2', 'famicart:RPi_Pico_SMD', x, y, rot, side)
    for g, pin in PICO_GP.items(): c(ref, pin, gp.get(g))
    for p in PICO_GND: c(ref, p, 'GND')
    c(ref, 30, 'RUN'); c(ref, 39, vsys)
    for p in (35, 36, 37, 40, 41, 42, 43, 44, 45, 46): c(ref, p, None)

GP_A = {i: f'CA{i}' for i in range(15)}
GP_A.update({15 + i: f'CD{i}' for i in range(8)})
GP_A.update({26: 'ROMSEL_D', 27: 'WS_D', 28: 'LINK_A'})
pico('U1', 26.5, 12.4, 90, 'F', GP_A, 'VSYS_A')            # USB at the left board edge

GP_B = {i: f'PA{i}' for i in range(14)}
GP_B.update({14 + i: f'PD{i}' for i in range(8)})
GP_B.update({22: 'RD_D', 26: 'CIRAM_nCE', 27: 'CIRAM_A10', 28: 'LINK_B'})   # /CE + A10 adjacent: one PIO side-set drives both
pico('U2', 63.5, 12.4, 270, 'B', GP_B, 'VSYS_B')           # USB at the right board edge

P('U3', 'famicart', 'XIAO-RP2350', 'Seeed XIAO RP2350', 'famicart:XIAO-RP2350-Edge', 72.0, 11.0, 0, 'F')
for p, nn in {1: 'LINK_C', 2: 'PWM', 3: 'IRQ_G', 4: 'C_M2', 5: 'PA12', 6: 'PA13', 7: 'RD_D', 8: None, 9: None, 10: None, 11: None, 12: None, 13: 'GND', 14: 'V5_C'}.items():
    c('U3', p, nn)

# ------------------------------------------------------------------ 1k series arrays (console side | MCU side)
YA = 26.5
for i, x in enumerate((6.0, 11.5, 17.0, 22.5)):
    bits = list(range(4 * i, 4 * i + 4))
    pairs = [(f'CPU_A{b}', f'CA{b}') if b < 15 else ('M2', 'C_M2') for b in bits]
    rarr(x, YA, 90, pairs)
for i, x in enumerate((28.0, 33.5)):
    rarr(x, YA, 90, [(f'CPU_D{4 * i + k}', f'CD{4 * i + k}') for k in range(4)])
for i, x in enumerate((48.5, 54.0, 59.5)):
    rarr(x, YA, 90, [(f'PPU_A{4 * i + k}', f'PA{4 * i + k}') for k in range(4)])
rarr(65.0, YA, 90, [('PPU_A12', 'PA12'), ('PPU_A13', 'PA13'), ('PPU_nRD', 'RD_D'), (None, None)])
for i, x in enumerate((70.5, 76.0)):
    rarr(x, YA, 90, [(f'PPU_D{4 * i + k}', f'PD{4 * i + k}') for k in range(4)])

# ------------------------------------------------------------------ CPU-side glue (front, left)
YG = 31.2
nfet(6.0, YG, 0, 'M2', 'M2n')                          # M2n = NOT M2
res('2.2k', 9.5, YG, 90, 'M2n', '+5V')
diode('1N4148WS', '1N4148WS', 'Diode_SMD:D_SOD-323', 12.5, YG, 90, 'CPU_RW', 'nWS')   # /WS = R/W OR M2n
diode('1N4148WS', '1N4148WS', 'Diode_SMD:D_SOD-323', 15.0, YG, 90, 'M2n', 'nWS')
res('1k', 17.5, YG, 90, 'nWS', 'WS_D'); res('2.2k', 20.0, YG, 90, 'WS_D', 'GND')       # divider (also the OR pull-down)
res('1k', 22.5, YG, 90, 'nROMSEL', 'ROMSEL_D'); res('2.2k', 25.0, YG, 90, 'ROMSEL_D', 'GND')
# power-up / soft-reset parking: undriven CPU data bus reads $4C (= JMP abs) -> CPU loops in JMP $4C4C
for b, x in zip(range(8), (27.5, 29.5, 31.5, 33.5, 35.5, 37.5, 39.5, 41.5)):
    res('100k', x, YG + 0.4, 90, f'CPU_D{b}', '+5V' if (0x4C >> b) & 1 else 'GND')

# ------------------------------------------------------------------ PPU-side glue, IRQ, audio, power, reset (front, right)
res('100k', 49.5, YG, 90, 'PPU_nA13', 'CIRAM_nCE')     # CIRAM follows /A13 until U2 drives /CE
nfet(53.0, YG, 0, 'IRQ_G', 'nIRQ')                      # open-drain /IRQ from U3
res('100k', 56.5, YG, 90, 'IRQ_G', 'GND')
res('2.2k', 59.0, YG, 90, 'PWM', 'AF1'); cap('10n', C0603, 61.5, YG, 90, 'AF1')
res('2.2k', 64.0, YG, 90, 'AF1', 'AF2'); cap('10n', C0603, 66.5, YG, 90, 'AF2')
res('2.2k', 69.0, YG, 90, 'AF2', 'AUDIO_OUT'); res('1k', 71.5, YG, 90, 'AUDIO_IN', 'AUDIO_OUT')
for x, y, nn in ((55.0, 21.0, 'LINK_A'), (57.5, 21.0, 'LINK_B'), (56.2, 16.5, 'LINK_C')):
    res('1k', x, y, 90, nn, 'LINK')
for x, k in ((74.5, 'VSYS_A'), (77.5, 'VSYS_B'), (80.5, 'V5_C')):
    diode('D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', x, YG, 90, '+5V', k)
cap('10u', C0805, 84.0, YG, 90, '+5V')
P('SW1', 'Switch', 'SW_Push', 'RESET', 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A', 86.0, 24.5, 90); c('SW1', 1, 'RUN'); c('SW1', 2, 'GND')
P('J2', 'famicart', 'WirePads_1x3', 'RUN/GND/LINK pads', 'famicart:WirePads_1x3', 86.5, 10.0, 90); c('J2', 1, 'RUN'); c('J2', 2, 'GND'); c('J2', 3, 'LINK')


# ------------------------------------------------------------------ rev F: coprocessors (absolute coordinates)
SHIFT[0] = False
GP_D = {i: f'CA{i}' for i in range(15)}                        # shares U1's address nodes
GP_D.update({15 + i: f'XD{i}' for i in range(8)})             # own data resistors
GP_D.update({26: 'ROMSEL_D', 27: 'WS_D', 28: 'LINK_D'})
pico('U4', 26.5, 12.4, 90, 'F', GP_D, 'VSYS_D')                # USB at the left board edge, above U1
GP_E = {i: f'PA{i}' for i in range(14)}                        # shares U2's address nodes
GP_E.update({14 + i: f'YD{i}' for i in range(8)})
GP_E.update({22: 'RD_D', 28: 'LINK_E'})
pico('U5', 63.5, 12.4, 270, 'B', GP_E, 'VSYS_E')               # USB at the right board edge, above U2
for i, x in enumerate((64.0, 69.5)):
    rarr(x, 30.5, 90, [(f'CPU_D{4 * i + k}', f'XD{4 * i + k}') for k in range(4)])
for i, x in enumerate((75.0, 80.5)):
    rarr(x, 30.5, 90, [(f'PPU_D{4 * i + k}', f'YD{4 * i + k}') for k in range(4)])
res('1k', 59.5, 40.5, 90, 'LINK_D', 'LINK'); res('1k', 62.0, 40.5, 90, 'LINK_E', 'LINK')
for x, k in ((66.5, 'VSYS_D'), (70.0, 'VSYS_E')):
    diode('D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', x, 37.5, 90, '+5V', k)
cap('10u', C0805, 73.5, 37.5, 90, '+5V')

POWER_NETS = {'+5V', 'GND'}

# LCSC part numbers -- all JLCPCB Basic parts (checked by gen_jlc.py against the parts API); modules are hand-soldered
LCSC = {
    '1k x4': ('C20197', '4D03WGJ0102T5E 1k x4 0603'), '1k': ('C21190', '0603WAF1001T5E 1k 0603'), '2.2k': ('C4190', '0603WAF2201T5E 2.2k 0603'),
    '100k': ('C25803', '0603WAF1003T5E 100k 0603'), '10n': ('C57112', '0603B103K500NT 10nF 0603'), '10u': ('C15850', 'CL21A106KAYNNNE 10uF 0805'),
    '2N7002': ('C8545', '2N7002 SOT-23'), '1N4148WS': ('C2128', '1N4148WS SOD-323'), 'B5819W': ('C8598', 'B5819W SOD-123'),
    'RESET': ('C318884', 'TS-1187A-B-A-B'),
}
HAND = {   # not assembled by JLCPCB: bought from Akizuki and hand-soldered
    'Raspberry Pi Pico 2': ('Akizuki 129604', '990 yen'), 'Seeed XIAO RP2350': ('Akizuki 129619', '1,100 yen'),
}

if __name__ == '__main__':
    nets = {}
    for ref, pins in NETS.items():
        for p, nn in pins.items():
            if nn: nets.setdefault(nn, []).append(f'{ref}.{p}')
    print(len(PARTS), 'parts', len(nets), 'nets')
    for nn, nodes in sorted(nets.items()):
        if len(nodes) < 2: print('  single-node net:', nn, nodes)
    print('parts without connections:', [r for r in PARTS if r not in NETS])
    from collections import Counter
    print('BOM types:', Counter(v[2] for v in PARTS.values()))
