"""famicart rev G (docs/12_rev_g_plan.md): Pico 2 x2 + XIAO RP2350 x2 as the base set, plus two optional Pico 2
positions, an SPI flash and an optional microSD socket, for the Nintendo LARGE Famicom shell (shells.hvc_large).

  back   U2  Pico 2  PPU bus (required)              low band, centred
         U5  Pico 2  PPU-bus extension (optional)    above the notch band, USB at the right edge
         U1  Pico 2  CPU bus (required)              top, USB at the left edge
  front  U4  Pico 2  CPU-bus extension (optional)    top left, USB at the left edge
         U3  XIAO    IRQ + expansion audio + CIRAM   middle, USB-C at the right edge
         U6  XIAO    hub: SFC chip functions, storage, PCM audio, firmware updates; USB-C at the top edge
         U7  W25Q128JVSIQ (16 MB SPI flash)  and  J3 microSD socket (optional, hand-soldered), both on U6's SPI
         all JLCPCB parts (one-sided assembly).
U4 / U5 hold the part of a 512 KB PRG / CHR image that does not fit one RP2350 (520 KB RAM) and can answer their bus
directly; the board works with them left empty.

Changes against rev F (design_revf.py), from the 2026-11 design review:
  * /WS: diode OR + divider replaced by a wired NOR of two 2N7002 (M2n and R/W on the gates), pulled up to U1's own
    3.3 V: WS_D is an ACTIVE-HIGH write strobe at 0 / 3.3 V with no DC load on R/W (the old node reached only ~1.7 V).
  * /ROMSEL: the 1k / 2.2k divider (x0.69, about 2.3 V from the console's 74LS139) became 1k in series plus a Schottky
    clamp to U1's 3.3 V: the pad sees the console's own level, at most 3.3 V + 0.3 V, with no load on the high level.
    Polarity is unchanged (ROMSEL_D active low).
  * PPU /WE (J1 pin 47) is wired the same way (1k of the spare array element + clamp to U2's 3.3 V) to U2 / U5 GP26
    (WE_D active low). U2 sees real PPU writes.
  * CIRAM /CE and CIRAM A10 are driven by U3 (PA10..PA13 on four consecutive GPIOs), which frees U2 GP26 / GP27.
  * PLINK: one-way serial from U6 to U2 / U5 GP27 for frame data.
  * J1 pin 31 is tied to +5V (on some consoles it is the "cartridge present" input of the RF modulator).
  * The eight 100 k "park" pulls on D0-D7 and the 100 k from /A13 to CIRAM /CE are gone (they could not do their job
    against the pad pull-downs of an RP2350 in reset); firmware switches the pad pulls off.
  * RUN of each Pico reaches the reset switch through its own Schottky, so an unpowered module cannot hold the
    others in reset.
2-layer, JLCPCB Basic parts only (1N4148WS left the list, W25Q128JVSIQ joined it)."""
import shells

REV = 'rev G'
LAYERS = 2
SHELL = shells.hvc_large(75.0)
BODY_H = SHELL['body_h']
H = BODY_H

def at(xp, h):
    """x' (from the board centre line, + to the right seen from the front), h (height above the card-edge shoulder)"""
    return round(45.0 + xp, 3), round(H - h, 3)

PARTS = {}
def P(ref, lib, sym, val, fp, xp, h, rot=0, side='F'):
    x, y = at(xp, h)
    PARTS[ref] = (lib, sym, val, fp, (x, y, rot, side))
NETS = {}
def c(ref, pin, net): NETS.setdefault(ref, {})[str(pin)] = net
_n = {'R': 0, 'C': 0, 'RN': 0, 'D': 0, 'Q': 0}
def nxt(k): _n[k] += 1; return f'{k}{_n[k]}'
R0603 = 'Resistor_SMD:R_0603_1608Metric'; C0603 = 'Capacitor_SMD:C_0603_1608Metric'; C0805 = 'Capacitor_SMD:C_0805_2012Metric'
RARR = 'Resistor_SMD:R_Array_Convex_4x0603'; SOT23 = 'Package_TO_SOT_SMD:SOT-23'; SOD123 = 'Diode_SMD:D_SOD-123'
def res(val, xp, h, a, b, rot=90):
    r = nxt('R'); P(r, 'Device', 'R', val, R0603, xp, h, rot); c(r, 1, a); c(r, 2, b); return r
def cap(val, fp, xp, h, a, b='GND', rot=90):
    r = nxt('C'); P(r, 'Device', 'C', val, fp, xp, h, rot); c(r, 1, a); c(r, 2, b); return r
def rarr(xp, h, pairs):
    """1k x4 array; pairs = [(console_net, mcu_net)] x4 (None for unused)."""
    r = nxt('RN'); P(r, 'Device', 'R_Pack04', '1k x4', RARR, xp, h, 0)
    for i, (a, b) in enumerate(pairs): c(r, 1 + i, a); c(r, 8 - i, b)
    return r
def nfet(xp, h, g, d):
    q = nxt('Q'); P(q, 'Transistor_FET', '2N7002', '2N7002', SOT23, xp, h, 0); c(q, 1, g); c(q, 2, 'GND'); c(q, 3, d); return q
def schottky(xp, h, a, k):
    d = nxt('D'); P(d, 'Device', 'D_Schottky', 'B5819W', SOD123, xp, h, 90); c(d, 1, k); c(d, 2, a); return d

# ------------------------------------------------------------------ card edge
P('J1', 'famicart', 'Famicom_CardEdge_60', 'Famicom 60-pin edge', 'famicart:Famicom_CardEdge_60', 0.0, 0.0)
J1 = {1:'GND',2:'CPU_A11',3:'CPU_A10',4:'CPU_A9',5:'CPU_A8',6:'CPU_A7',7:'CPU_A6',8:'CPU_A5',9:'CPU_A4',10:'CPU_A3',11:'CPU_A2',12:'CPU_A1',13:'CPU_A0',14:'CPU_RW',15:'nIRQ',16:'GND',
      17:'PPU_nRD',18:'CIRAM_A10',19:'PPU_A6',20:'PPU_A5',21:'PPU_A4',22:'PPU_A3',23:'PPU_A2',24:'PPU_A1',25:'PPU_A0',26:'PPU_D0',27:'PPU_D1',28:'PPU_D2',29:'PPU_D3',30:'+5V',
      31:'+5V',32:'M2',33:'CPU_A12',34:'CPU_A13',35:'CPU_A14',36:'CPU_D7',37:'CPU_D6',38:'CPU_D5',39:'CPU_D4',40:'CPU_D3',41:'CPU_D2',42:'CPU_D1',43:'CPU_D0',44:'nROMSEL',
      45:'AUDIO_IN',46:'AUDIO_OUT',47:'PPU_nWE',48:'CIRAM_nCE',49:None,50:'PPU_A7',51:'PPU_A8',52:'PPU_A9',53:'PPU_A10',54:'PPU_A11',55:'PPU_A12',56:'PPU_A13',57:'PPU_D7',58:'PPU_D6',59:'PPU_D5',60:'PPU_D4'}
for p, nn in J1.items(): c('J1', p, nn)

# ------------------------------------------------------------------ modules (hand-soldered)
PICO_GP = {0:1,1:2,2:4,3:5,4:6,5:7,6:9,7:10,8:11,9:12,10:14,11:15,12:16,13:17,14:19,15:20,16:21,17:22,18:24,19:25,20:26,21:27,22:29,26:31,27:32,28:34}
PICO_GND = (3, 8, 13, 18, 23, 28, 33, 38)
def pico(ref, xp, h, rot, side, gp, vsys, run, v33=None):
    P(ref, 'famicart', 'RPi_Pico2', 'Raspberry Pi Pico 2', 'famicart:RPi_Pico_SMD_Short', xp, h, rot, side)
    for g, pin in PICO_GP.items(): c(ref, pin, gp.get(g))
    for p in PICO_GND: c(ref, p, 'GND')
    c(ref, 30, run); c(ref, 39, vsys); c(ref, 36, v33)
    for p in (35, 37, 40, 41, 42, 43, 44, 45, 46): c(ref, p, None)
def xiao(ref, xp, h, rot, side, pins):
    P(ref, 'famicart', 'XIAO-RP2350', 'Seeed XIAO RP2350', 'famicart:XIAO-RP2350-Edge', xp, h, rot, side)
    for p in range(1, 15): c(ref, p, pins.get(p))

# CPU bus: A0-14, D0-7, ROM select and write strobe (both active high at 3.3 V), LINK
GP_A = {i: f'CA{i}' for i in range(15)}
GP_A.update({15 + i: f'CD{i}' for i in range(8)})
GP_A.update({26: 'ROMSEL_D', 27: 'WS_D', 28: 'LINK_A'})
pico('U1', -18.3, 62.0, 90, 'B', GP_A, 'VSYS_A', 'RUN_A', '3V3_A')        # body h 51.5-72.5, USB past the left edge
GP_D = dict(GP_A); GP_D.update({15 + i: f'XD{i}' for i in range(8)}); GP_D[28] = 'LINK_D'   # shares U1's address / strobe nodes, own data resistors
pico('U4', -18.3, 63.0, 90, 'F', GP_D, 'VSYS_D', 'RUN_D')                 # optional; body h 52.5-73.5

# PPU bus: PA0-13, PD0-7, /RD, write strobe (active high), PLINK input, LINK
GP_B = {i: f'PA{i}' for i in range(14)}
GP_B.update({14 + i: f'PD{i}' for i in range(8)})
GP_B.update({22: 'RD_D', 26: 'WE_D', 27: 'PLINK_B', 28: 'LINK_B'})
pico('U2', 0.0, 11.3, 270, 'B', GP_B, 'VSYS_B', 'RUN_B', '3V3_B')         # body h 0.8-21.8, pads 0.4-22.2 (tab band below, slot keep-out from 22.4)
GP_E = dict(GP_B); GP_E.update({14 + i: f'YD{i}' for i in range(8)}); GP_E.update({27: 'PLINK_E', 28: 'LINK_E'})
pico('U5', 18.5, 37.3, 270, 'B', GP_E, 'VSYS_E', 'RUN_E')                 # optional; body h 26.8-47.8, USB past the right edge

# XIAO edge pins: 1 D0 GPIO26, 2 D1 GPIO27, 3 D2 GPIO28 (not 5 V tolerant: 3.3 V signals only), 4 D3 GPIO5, 5 D4 GPIO6,
# 6 D5 GPIO7, 7 D6 GPIO0, 8 D7 GPIO1, 9 D8 GPIO2, 10 D9 GPIO4, 11 D10 GPIO3, 12 3V3, 13 GND, 14 5V
# U3: PA10..PA13 = GPIO4..GPIO7 (one PIO "in pins, 4" for the CIRAM table), /CE and A10 on GPIO1 / GPIO2 (side-set pair)
xiao('U3', 33.6, 37.9, 270, 'F', {1: 'LINK_C', 2: 'PWM', 3: 'IRQ_G', 4: 'PA11', 5: 'PA12', 6: 'PA13', 7: 'RD_D',
                                  8: 'CIRAM_nCE', 9: 'CIRAM_A10', 10: 'PA10', 11: 'C_M2', 13: 'GND', 14: 'V5_C'})   # body x' 23.1-44.1: USB-C at the right edge
# U6: SPI0 on GPIO2 (SCK), GPIO3 (TX), GPIO4 (RX), GPIO5 (CSn)
xiao('U6', 19.0, 63.4, 0, 'F', {1: 'LINK_F', 2: 'PWM2', 3: 'IRQ2_G', 4: 'F_CS', 5: 'SD_CS', 7: 'PLINK_F', 8: 'C_M2',
                                9: 'SPI_SCK', 10: 'SPI_MISO', 11: 'SPI_MOSI', 12: '3V3_F', 13: 'GND', 14: 'V5_F'})    # body h 52.9-73.9: USB-C at the top edge

# ------------------------------------------------------------------ 1k series arrays (console side | MCU side), front, by the card edge
HA = 5.0
cpu_x = [-38.0 + 3.6 * i for i in range(8)]
for i in range(4):
    bits = list(range(4 * i, 4 * i + 4))
    rarr(cpu_x[i], HA, [(f'CPU_A{b}', f'CA{b}') if b < 15 else ('M2', 'C_M2') for b in bits])
for i in range(2): rarr(cpu_x[4 + i], HA, [(f'CPU_D{4 * i + k}', f'CD{4 * i + k}') for k in range(4)])
ppu_x = [12.0 + 3.6 * i for i in range(8)]
for i in range(3): rarr(ppu_x[i], HA, [(f'PPU_A{4 * i + k}', f'PA{4 * i + k}') for k in range(4)])
rarr(ppu_x[3], HA, [('PPU_A12', 'PA12'), ('PPU_A13', 'PA13'), ('PPU_nRD', 'RD_D'), ('PPU_nWE', 'WE_D')])
for i in range(2): rarr(ppu_x[4 + i], HA, [(f'PPU_D{4 * i + k}', f'PD{4 * i + k}') for k in range(4)])
for i in range(2): rarr(cpu_x[6 + i], HA, [(f'CPU_D{4 * i + k}', f'XD{4 * i + k}') for k in range(4)])     # RN13, RN14: U4 data
for i in range(2): rarr(ppu_x[6 + i], HA, [(f'PPU_D{4 * i + k}', f'YD{4 * i + k}') for k in range(4)])     # RN15, RN16: U5 data

# ------------------------------------------------------------------ CPU-side glue (front, left, row h 10.8)
HB = 10.8
nfet(-38.0, HB, 'M2', 'M2n');            res('1k', -35.0, HB, 'M2n', '+5V')            # Q1: M2n = NOT M2
nfet(-31.8, HB, 'CPU_RW', 'WS_D'); nfet(-27.6, HB, 'M2n', 'WS_D')                       # Q2, Q3: WS_D low while R/W is high or M2 is low
res('1k', -24.6, HB, 'WS_D', '3V3_A')                                                  # ... and 3.3 V only while M2 is high and R/W is low
res('1k', -21.8, HB, 'nROMSEL', 'ROMSEL_D'); schottky(-19.2, HB, 'ROMSEL_D', '3V3_A')   # /ROMSEL through 1k, clamped to U1's 3.3 V
# RUN: each Pico through its own Schottky to the reset switch
HC = 16.3
for i, run in enumerate(('RUN_A', 'RUN_B', 'RUN_D', 'RUN_E')): schottky(-38.0 + 2.8 * i, HC, run, 'nRST')
for i, nn in enumerate(('LINK_A', 'LINK_B', 'LINK_C', 'LINK_D', 'LINK_E', 'LINK_F')): res('1k', -26.4 + 2.4 * i, HC, nn, 'LINK')

# ------------------------------------------------------------------ PPU-side glue, IRQ, audio, power (front, right)
schottky(12.0, HB, 'WE_D', '3V3_B')                                                    # PPU /WE (behind 1k of RN10) clamped to U2's 3.3 V
nfet(15.6, HB, 'IRQ_G', 'nIRQ');         res('100k', 18.6, HB, 'IRQ_G', 'GND')         # Q4: open-drain /IRQ from U3
nfet(21.8, HB, 'IRQ2_G', 'nIRQ');        res('100k', 24.8, HB, 'IRQ2_G', 'GND')        # Q5: open-drain /IRQ from U6
res('2.2k', 27.8, HB, 'PWM', 'AF1');     cap('10n', C0603, 30.2, HB, 'AF1')
res('2.2k', 32.6, HB, 'AF1', 'AF2');     cap('10n', C0603, 35.0, HB, 'AF2')
res('2.2k', 37.4, HB, 'AF2', 'AUDIO_OUT'); res('1k', 39.8, HB, 'AUDIO_IN', 'AUDIO_OUT')
for i, k in enumerate(('VSYS_A', 'VSYS_B', 'V5_C', 'VSYS_D', 'VSYS_E', 'V5_F')): schottky(12.0 + 2.8 * i, HC, '+5V', k)
cap('10u', C0805, 28.8, HC, '+5V'); cap('10u', C0805, 31.4, HC, '+5V')
res('2.2k', 33.9, HC, 'PWM2', 'AF1')                                                    # U6 sample audio into the same filter
res('1k', 36.3, HC, 'PLINK_F', 'PLINK_B'); res('1k', 38.7, HC, 'PLINK_F', 'PLINK_E')

# ------------------------------------------------------------------ storage on U6 (front, top right)
P('U7', 'Memory_Flash', 'W25Q128JVS', 'W25Q128JVSIQ', 'Package_SO:SOIC-8_5.23x5.23mm_P1.27mm', 38.5, 53.5, 0)
for p, nn in {1: 'F_CS', 2: 'SPI_MISO', 3: 'F_IO2', 4: 'GND', 5: 'SPI_MOSI', 6: 'SPI_SCK', 7: 'F_IO3', 8: '3V3_F'}.items(): c('U7', p, nn)
P('J3', 'Connector', 'Micro_SD_Card_Det_Hirose_DM3AT', 'microSD DM3AT-SF-PEJM5', 'Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5', 36.8, 65.8, 180)
for p, nn in {1: 'SD_DAT2', 2: 'SD_CS', 3: 'SPI_MOSI', 4: '3V3_F', 5: 'SPI_SCK', 6: 'GND', 7: 'SPI_MISO', 8: 'SD_DAT1', 9: None, 10: None, 11: 'GND'}.items(): c('J3', p, nn)
HF = 49.3
for i, (a, b) in enumerate((('F_CS', '3V3_F'), ('SD_CS', '3V3_F'), ('F_IO2', '3V3_F'), ('F_IO3', '3V3_F'), ('SPI_MISO', '3V3_F'), ('SD_DAT1', '3V3_F'), ('SD_DAT2', '3V3_F'))):
    res('100k', 9.8 + 2.4 * i, HF, a, b)
cap('10n', C0603, 26.6, HF, '3V3_F'); cap('10u', C0805, 29.2, HF, '3V3_F'); cap('10u', C0805, 31.8, HF, '3V3_F')

# ------------------------------------------------------------------ reset switch and wire pads (front, middle left)
P('SW1', 'Switch', 'SW_Push', 'RESET', 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A', -38.0, 38.0, 90); c('SW1', 1, 'nRST'); c('SW1', 2, 'GND')
P('J2', 'famicart', 'WirePads_1x3', 'RST/GND/LINK pads', 'famicart:WirePads_1x3', -30.0, 38.0, 90); c('J2', 1, 'nRST'); c('J2', 2, 'GND'); c('J2', 3, 'LINK')

POWER_NETS = {'+5V', 'GND'}

# firmware of each hand-soldered module, printed on the silk under it
ROLE = {'U1': 'cpu', 'U2': 'ppu', 'U3': 'x', 'U4': 'cpu-ext', 'U5': 'ppu-ext', 'U6': 'hub'}
SILK_TEXT = [('famicart rev G', 45.0 - 12.0, H - 33.5, 'F', 1.5), ('famicart rev G (back)', 45.0 - 22.0, H - 37.0, 'B', 1.5)]

# LCSC part numbers -- all JLCPCB Basic parts (checked by gen_jlc.py against the parts API); modules and J3 are hand-soldered
LCSC = {
    '1k x4': ('C20197', '4D03WGJ0102T5E 1k x4 0603'), '1k': ('C21190', '0603WAF1001T5E 1k 0603'), '2.2k': ('C4190', '0603WAF2201T5E 2.2k 0603'),
    '100k': ('C25803', '0603WAF1003T5E 100k 0603'), '10n': ('C57112', '0603B103K500NT 10nF 0603'), '10u': ('C15850', 'CL21A106KAYNNNE 10uF 0805'),
    '2N7002': ('C8545', '2N7002 SOT-23'), 'B5819W': ('C8598', 'B5819W SOD-123'), 'RESET': ('C318884', 'TS-1187A-B-A-B'),
    'W25Q128JVSIQ': ('C97521', 'W25Q128JVSIQ 16MB SPI flash SOIC-8 208mil'),
}
HAND = {   # not assembled by JLCPCB: bought from Akizuki and hand-soldered
    'Raspberry Pi Pico 2': ('Akizuki 129604', '990 yen'), 'Seeed XIAO RP2350': ('Akizuki 129619', '1,100 yen'),
    'microSD DM3AT-SF-PEJM5': ('Akizuki 102395', '150 yen', 'optional'),
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
