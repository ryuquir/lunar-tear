"""famicart rev G (docs/12_rev_g_plan.md): Pico 2 x2 + XIAO RP2350 x2 as the base set, plus two optional Pico 2
positions, an SPI flash and an optional microSD socket, for the Nintendo LARGE Famicom shell (shells.hvc_large).

  back   U2  Pico 2  PPU bus (required)              low band, centred
         U5  Pico 2  PPU-bus extension (optional)    above the notch band, USB at the right edge
         U1  Pico 2  CPU bus (required)              top, USB at the left edge
  front  U4  Pico 2  CPU-bus extension (optional)    top left, USB at the left edge
         U3  XIAO    IRQ + expansion audio + CIRAM   middle, USB-C at the right edge
         U6  XIAO    hub: SFC chip functions, storage, PCM audio, firmware updates; USB-C at the top edge
         U7  W25Q128JVSIQ (16 MB SPI flash)  and  J3 microSD socket (optional, hand-soldered), both on U6's SPI
         all JLCPCB parts on the front (one-sided assembly), 10 part types, all JLCPCB Basic.
U4 / U5 hold the part of a 512 KB PRG / CHR image that does not fit one RP2350 (520 KB RAM) and can answer their bus
directly; the board works with them left empty.

Signals that reach a pad which is NOT 5 V tolerant (GP26-28 of a Pico 2, D0-D2 of a XIAO) are made on the board at
3.3 V. All three strobes are ACTIVE HIGH (each is one 2N7002 stage that inverts a console signal):
  RSEL_D  = NOT /ROMSEL            2N7002, gate /ROMSEL (2.2k to +5V), 1k to U1's 3.3 V   -> U1 / U4 GP26
  WS_D    = M2 AND NOT R/W         two 2N7002 in parallel (gates R/W and NOT M2), 1k to U1's 3.3 V   -> U1 / U4 GP27
  PWS_D   = NOT PPU /WE            2N7002, gate /WE behind 1k, 1.1k to U2's 3.3 V -> U2 / U5 GP26
The console sees FET gates (plus 2.2k to +5V on /ROMSEL and 100k on R/W). RSEL_D and WS_D are pulled up to U1's 3.3 V
and PWS_D to U2's, so the optional U4 / U5 see their neighbour's 3.3 V on GP26 / GP27 through 1 - 1.1k.
With the console's 5 V absent or collapsing all three strobes read ACTIVE (FETs off, pull-ups on): firmware accepts a
strobe only if it ends in time, and treats a strobe that stays high as "console not running".

Changes against rev F (design_revf.py), from the 2026-11 design review:
  * /WS: the diode OR + divider (about 1.7 V where 2.0 V is needed, and a 0.9 mA load on R/W) became the wired NOR
    above. R/W has a 100k pull-up to +5V: while the console holds the CPU in reset its pins float, and the strobe
    must then read "no write".
  * /ROMSEL: the 1k / 2.2k divider (x0.69: 1.86 V from the worst-case high of a 74LS139) became the inverter above.
    A Schottky clamp behind 1k was tried on paper and dropped: the diode's 110-350 pF makes the edge 230-360 ns late.
  * PPU /WE (J1 pin 47) is new: U2 sees real PPU writes.
  * CIRAM /CE and CIRAM A10 are driven by U3 (PA10..PA13 on four consecutive GPIOs) through 500 ohm (two array
    elements in parallel), like every other line to the console has a series resistor.
  * LINK: every node reaches the common wire through 250 ohm (one 1k x4 array in parallel) placed at the module; the
    single 1k of rev F limited the edge to about 90 ns, too slow for 12.5 Mbaud. 4.4k from LINK to U1's 3.3 V holds
    the idle level. PLINK (one-way, U6 to U2 / U5 GP27, frame data): 500 ohm per receiver.
  * Audio: console audio through 2 x 2.2k, cartridge audio (U3 PWM and U6 PWM2, 1k each into the first filter node)
    through 1k + 1k with 2 x 10 nF. Gains to pin 46 into a Famicom's load: console 0.32, each PWM pin 0.28 (rev F:
    0.87 and 0.13), which puts full-scale cartridge audio 9 to 19 dB above one 2A03 square channel, like a VRC6 cart.
  * /IRQ: one open-drain 2N7002 driven by U3 only (U6 asks U3 over LINK); gate pull-down 2.2k.
  * J1 pin 31 is tied to +5V (on some consoles it is the "cartridge present" input of the RF modulator).
  * The eight 100 k "park" pulls on D0-D7 and the 100 k from /A13 to CIRAM /CE are gone (they could not do their job
    against the pad pull-downs of an RP2350 in reset); firmware switches the pad pulls off.
  * RUN of each Pico reaches the reset switch through its own Schottky, so an unpowered module cannot hold the
    others in reset.
  * Flash and card chip selects have 2.2k pull-ups (a 100k cannot hold them high against the pad pull-down of a
    XIAO in reset). U6 reads the console's +5V through 100k / 100k on ADC2 (console on or off, power failing).
  * J4: three wire pads with a spare U6 pin (ADC0, behind 2.2k), 3.3 V and GND, for a hand-wired input (microphone,
    button).
  * BAV99 clamps to GND / +5V on the console lines that end on a FET (M2, R/W, /ROMSEL, the /WE gate, /IRQ).
  * PPU data lines D0-D7: 500 ohm (two array elements in parallel) to U2 and to U5 instead of 1k. The console's
    74LS373 latch inputs on these lines source current when low, which made the worst-case read too slow through 1k.
2-layer; parts: 1k x4 array, 2.2k, 100k, 10n, 10u, 2N7002, B5819W, BAV99, W25Q128JVSIQ, push switch."""
import shells

REV = 'rev G'
LAYERS = 2
# Outline prepared for JLCPCB (shells.py): rounded inner corners with 0.6 mm relief, straight side edges 0.2 mm inside
# the reference (edge rails / V-cut). Rules: 0.15 / 0.15 mm tracks, via 0.5 mm with a 0.3 mm hole (JLCPCB's standard
# hole size: no small-hole surcharge), silkscreen minimums, no paste on the hand-soldered parts (gen_pcb.py).
SHELL = shells.hvc_large(75.0, relief=0.6, side_inset=0.2)
JLC_RULES = True
TRACK, CLEAR, VIA_DIA, VIA_DRILL = 0.15, 0.15, 0.5, 0.3
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
def clamp(xp, h, net):
    """BAV99 (two diodes in series: pin 1 anode, pin 3 common, pin 2 cathode) as a clamp of `net` to GND and +5V.
    The 2N7002 of JLCPCB's Basic list has no gate protection, and these nets end on card-edge fingers that people
    touch: without the clamp a few hundred volts of static would be enough to break a gate. 1.5 pF per line."""
    d = nxt('D'); P(d, 'Diode', 'BAV99', 'BAV99', SOT23, xp, h, 0); c(d, 1, 'GND'); c(d, 2, '+5V'); c(d, 3, net); return d

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
    for p in range(1, 15): c(ref, p, pins.get(p))          # pads B15-B30 of the footprint (islands under the module's underside pads) stay without a net

# CPU bus: A0-14, D0-7, ROM select and write strobe (both active high at 3.3 V), LINK
GP_A = {i: f'CA{i}' for i in range(15)}
GP_A.update({15 + i: f'CD{i}' for i in range(8)})
GP_A.update({26: 'RSEL_D', 27: 'WS_D', 28: 'LINK_A'})
pico('U1', -18.3, 62.0, 90, 'B', GP_A, 'VSYS_A', 'RUN_A', '3V3_A')        # body h 51.5-72.5, USB past the left edge
GP_D = dict(GP_A); GP_D.update({15 + i: f'XD{i}' for i in range(8)}); GP_D[28] = 'LINK_D'   # shares U1's address / strobe nodes, own data resistors
pico('U4', -18.3, 63.0, 90, 'F', GP_D, 'VSYS_D', 'RUN_D')                 # optional; body h 52.5-73.5

# PPU bus: PA0-13, PD0-7, /RD, PPU write strobe (active high), PLINK input, LINK
GP_B = {i: f'PA{i}' for i in range(14)}
GP_B.update({14 + i: f'PD{i}' for i in range(8)})
GP_B.update({22: 'RD_D', 26: 'PWS_D', 27: 'PLINK_B', 28: 'LINK_B'})
pico('U2', 0.0, 11.3, 270, 'B', GP_B, 'VSYS_B', 'RUN_B', '3V3_B')         # body h 0.8-21.8, pads 0.4-22.2 (tab band below, slot keep-out from 22.4)
GP_E = dict(GP_B); GP_E.update({14 + i: f'YD{i}' for i in range(8)}); GP_E.update({27: 'PLINK_E', 28: 'LINK_E'})
pico('U5', 18.2, 37.3, 270, 'B', GP_E, 'VSYS_E', 'RUN_E')                 # optional; body h 26.8-47.8, USB past the right edge

# XIAO edge pins: 1 D0 GPIO26, 2 D1 GPIO27, 3 D2 GPIO28 (ADC pads, not 5 V tolerant: 3.3 V signals only), 4 D3 GPIO5,
# 5 D4 GPIO6, 6 D5 GPIO7, 7 D6 GPIO0, 8 D7 GPIO1, 9 D8 GPIO2, 10 D9 GPIO4, 11 D10 GPIO3, 12 3V3, 13 GND, 14 5V (= USB VBUS)
# U3: PA10..PA13 = GPIO4..GPIO7 (one PIO "in pins, 4" for the CIRAM table), /CE and A10 on GPIO1 / GPIO2 (side-set pair)
xiao('U3', 33.3, 37.9, 270, 'F', {1: 'LINK_C', 2: 'PWM', 3: 'IRQ_G', 4: 'PA11', 5: 'PA12', 6: 'PA13', 7: 'RD_D',
                                  8: 'NCE_D', 9: 'NA10_D', 10: 'PA10', 11: 'C_M2', 13: 'GND', 14: 'V5_C'})          # body x' 22.8-43.8: USB-C at the right edge
# U6: SPI0 on GPIO2 (SCK), GPIO3 (TX), GPIO4 (RX); chip selects are plain GPIOs. EXT (ADC0) and V5S (ADC2) are analog-capable.
xiao('U6', 18.75, 63.4, 0, 'F', {1: 'EXT', 2: 'PWM2', 3: 'V5S', 4: 'C_M2', 5: 'SD_CS', 6: 'PLINK_F', 7: 'LINK_F', 8: 'F_CS',
                                9: 'SPI_SCK', 10: 'SPI_MISO', 11: 'SPI_MOSI', 12: '3V3_F', 13: 'GND', 14: 'V5_F'})    # body h 52.9-73.9: USB-C at the top edge

# ------------------------------------------------------------------ 1k series arrays (console side | MCU side), front, by the card edge
# The arrays stand in the order of the fingers below them, and the elements of each array in the order in which the
# finger tracks arrive (finger further left = pad nearer the top). Grouping them by bit number, as up to rev F2, runs
# against the finger order on both buses (A11 .. A0 from left to right): every address line then has to cross all the
# others in the 5 mm between the fingers and the arrays, and the autorouter left ten connections open there.
# Finger positions x' (front | back):  CPU  A11 -34.3 .. A0 -6.4 | M2 -34.3, A12, A13, A14 -26.7, D7 -24.1 .. D0 -6.4
#                                      PPU  /RD 3.8, CIRAM A10 6.4, A6 8.9 .. A0 24.1, D0 26.7 .. D3 34.3
#                                         | /WE 3.8, CIRAM /CE 6.4, A7 11.4 .. A13 26.7, D7 29.2 .. D4 37.3
HA = 5.0
XA = {1: -13.1, 2: -23.9, 3: -32.3, 4: -28.7, 5: -9.5, 6: -20.3, 13: -5.9, 14: -16.7}       # RN number -> x' (CPU side)
rarr(XA[1], HA, [(f'CPU_A{b}', f'CA{b}') for b in (3, 2, 1, 0)])                                       # RN1
rarr(XA[2], HA, [(f'CPU_A{b}', f'CA{b}') for b in (7, 6, 5, 4)])                                       # RN2
rarr(XA[3], HA, [(f'CPU_A{b}', f'CA{b}') for b in (11, 10, 9, 8)])                                     # RN3
rarr(XA[4], HA, [('M2', 'C_M2'), ('CPU_A12', 'CA12'), ('CPU_A13', 'CA13'), ('CPU_A14', 'CA14')])      # RN4
rarr(XA[5], HA, [(f'CPU_D{b}', f'CD{b}') for b in (3, 2, 1, 0)])                                       # RN5: U1 data
rarr(XA[6], HA, [(f'CPU_D{b}', f'CD{b}') for b in (7, 6, 5, 4)])                                       # RN6
ppu_x = [12.0 + 3.6 * i for i in range(8)]
rarr(ppu_x[0], HA, [('CIRAM_nCE', 'NCE_D'), ('CIRAM_nCE', 'NCE_D'), ('PPU_A6', 'PA6'), ('PPU_A5', 'PA5')])     # RN7: /CE through 500 ohm, from U3
rarr(ppu_x[1], HA, [('PPU_A7', 'PA7'), ('PPU_A4', 'PA4'), ('PPU_A8', 'PA8'), ('PPU_A3', 'PA3')])              # RN8
rarr(ppu_x[2], HA, [('PPU_A9', 'PA9'), ('PPU_A2', 'PA2'), ('PPU_A10', 'PA10'), ('PPU_A1', 'PA1')])            # RN9
rarr(ppu_x[3], HA, [('PPU_A11', 'PA11'), ('PPU_A0', 'PA0'), ('PPU_A12', 'PA12'), ('PPU_A13', 'PA13')])        # RN10
for i in range(2): rarr(ppu_x[4 + i], HA, [(f'PPU_D{4 * i + k}', f'PD{4 * i + k}') for k in range(4)])     # RN11, RN12: U2 data
rarr(XA[13], HA, [(f'CPU_D{b}', f'XD{b}') for b in (3, 2, 1, 0)])                                      # RN13: U4 data
rarr(XA[14], HA, [(f'CPU_D{b}', f'XD{b}') for b in (7, 6, 5, 4)])                                      # RN14
for i in range(2): rarr(ppu_x[6 + i], HA, [(f'PPU_D{4 * i + k}', f'YD{4 * i + k}') for k in range(4)])     # RN15, RN16: U5 data
rarr(8.4, HA, [('PPU_nRD', 'RD_D'), ('PPU_nWE', 'PWE_G'), ('CIRAM_A10', 'NA10_D'), ('CIRAM_A10', 'NA10_D')])   # RN17: /RD, /WE to the gate of Q6,
                                                                                                        # CIRAM A10 through 500 ohm, from U3

# ------------------------------------------------------------------ CPU-side glue (front, left, row h 10.8)
HB = 10.8
nfet(-38.2, HB, 'M2', 'M2n')                                                           # Q1: M2n = NOT M2 (0 / 5 V)
rarr(-34.3, HB, [('M2n', '+5V'), ('WS_D', '3V3_A'), ('RSEL_D', '3V3_A'), (None, None)])  # RN18: the three 1k pull-ups
nfet(-30.2, HB, 'CPU_RW', 'WS_D'); nfet(-26.2, HB, 'M2n', 'WS_D')                       # Q2, Q3: WS_D low while R/W is high or M2 is low
nfet(-22.2, HB, 'nROMSEL', 'RSEL_D'); res('2.2k', -19.2, HB, 'nROMSEL', '+5V')          # Q4: RSEL_D = NOT /ROMSEL (1k pull-up in RN18);
                                                                                        # 2.2k lifts the 74LS139's high level so that any 2N7002 turns on fully
res('100k', -16.8, HB, 'CPU_RW', '+5V')                                                # R/W reads "read" while the CPU pins float (console reset)
# RUN: each Pico through its own Schottky to the reset switch
HC = 16.3
for x, run in zip((-34.2, -26.2, -18.3, -15.5), ('RUN_A', 'RUN_B', 'RUN_D', 'RUN_E')): schottky(x, HC, run, 'nRST')
# static-discharge clamps on the three console lines that end on a bare FET gate (each above its FET)
clamp(-38.2, HC, 'M2'); clamp(-30.2, HC, 'CPU_RW'); clamp(-22.2, HC, 'nROMSEL')

# ------------------------------------------------------------------ audio and /IRQ (front, centre, by pins 15 / 45 / 46)
res('2.2k', -4.6, HB, 'AUDIO_IN', 'AMIX'); res('2.2k', -2.2, HB, 'AMIX', 'AUDIO_OUT')   # console audio: 4.4k
rarr(1.4, HB, [('PWM', 'AF1'), ('AF1', 'AF2'), ('AF2', 'AUDIO_OUT'), ('PWM2', 'AF1')])  # RN19: U3 and U6 PWM, 1k each -> AF1 -1k- AF2 -1k- out
cap('10n', C0603, 4.6, HB, 'AF1'); cap('10n', C0603, 7.0, HB, 'AF2')
nfet(-1.6, 15.6, 'IRQ_G', 'nIRQ'); res('2.2k', 1.4, 15.6, 'IRQ_G', 'GND')               # Q5: open-drain /IRQ from U3
clamp(-5.8, 15.6, 'nIRQ')                                                               # the drain of Q5 is on a finger too

# ------------------------------------------------------------------ PPU-side glue and power (front, right)
nfet(15.6, HB, 'PWE_G', 'PWS_D'); res('2.2k', 18.6, HB, 'PWS_D', '3V3_B'); res('2.2k', 20.2, HB, 'PWS_D', '3V3_B')   # Q6: PWS_D = NOT PPU /WE,
                                                                                        # 1.1k pull-up: the /WE pulse is only 186 ns long
clamp(23.6, HB, 'PWE_G')                                                                # gate of Q6 (behind the 1k of RN17)
for i, k in enumerate(('VSYS_A', 'VSYS_B', 'V5_C', 'VSYS_D', 'VSYS_E', 'V5_F')): schottky(12.0 + 2.8 * i, HC, '+5V', k)
cap('10u', C0805, 28.8, HC, '+5V'); cap('10u', C0805, 31.4, HC, '+5V')

# ------------------------------------------------------------------ LINK / PLINK resistors at the modules (front)
def link(xp, h, node): rarr(xp, h, [(node, 'LINK')] * 4)                                # 250 ohm between a module and the LINK wire
link(-27.2, 48.6, 'LINK_A'); link(-23.4, 48.6, 'LINK_D')                                # below the U1 / U4 stack
# idle level: 4.4k to U1's 3.3 V, so that a module held in reset or sitting in the USB boot mode (pad pull-downs on)
# cannot drag the idle wire below the input-high level of the modules that are running
res('2.2k', -32.6, 48.6, 'LINK', 'LINK_PU'); res('2.2k', -30.9, 48.6, 'LINK_PU', '3V3_A')
link(9.0, 18.6, 'LINK_B')                                                              # over U2 pin 34
link(26.9, 49.9, 'LINK_E'); link(31.0, 49.7, 'LINK_C'); link(10.6, 50.4, 'LINK_F')
rarr(14.0, 50.4, [('PLINK_F', 'PLINK_B'), ('PLINK_F', 'PLINK_B'), ('PLINK_F', 'PLINK_E'), ('PLINK_F', 'PLINK_E')])   # 500 ohm per receiver

# ------------------------------------------------------------------ PPU data lines: a second array in parallel (500 ohm)
# Each PPU data line also feeds an input of the console's 74LS373 address latch, and an LS input sources up to 0.4 mA
# when it is held low. Through 1 k that lifts the low level to 0.45 V and slows the falling edge: worst case 240 ns from
# /RD falling to settled data, against a /RD window of 186 ns (typical 85 ns). With two elements in parallel the worst
# case is 158 ns and the low level 0.25 V. RN27-RN30 sit above RN11, RN12, RN15, RN16; their elements are listed in
# reverse so that the pads that face each other carry the same net.
for i in range(2): rarr(27.2 + 3.6 * i, HB, [(f'PPU_D{4 * i + k}', f'PD{4 * i + k}') for k in (3, 2, 1, 0)])      # RN27, RN28: U2
for i in range(2): rarr(34.4 + 3.6 * i, HB, [(f'PPU_D{4 * i + k}', f'YD{4 * i + k}') for k in (3, 2, 1, 0)])      # RN29, RN30: U5

# ------------------------------------------------------------------ storage on U6 (front, top right)
P('U7', 'Memory_Flash', 'W25Q128JVS', 'W25Q128JVSIQ', 'Package_SO:SOIC-8_5.23x5.23mm_P1.27mm', 38.5, 53.5, 0)
for p, nn in {1: 'F_CS', 2: 'SPI_MISO', 3: 'F_IO2', 4: 'GND', 5: 'SPI_MOSI', 6: 'SPI_SCK', 7: 'F_IO3', 8: '3V3_F'}.items(): c('U7', p, nn)
P('J3', 'Connector', 'Micro_SD_Card_Det_Hirose_DM3AT', 'microSD DM3AT-SF-PEJM5', 'Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5', 36.5, 65.7, 180)
for p, nn in {1: 'SD_DAT2', 2: 'SD_CS', 3: 'SPI_MOSI', 4: '3V3_F', 5: 'SPI_SCK', 6: 'GND', 7: 'SPI_MISO', 8: 'SD_DAT1', 9: None, 10: None, 11: 'GND'}.items(): c('J3', p, nn)
# row under U6 (h 50.6)
res('2.2k', 17.0, 50.6, 'SD_CS', '3V3_F')                                              # chip selects: 2.2k (held high while U6 is in reset)
res('100k', 18.6, 50.6, 'V5S', 'GND'); res('100k', 20.2, 50.6, '+5V', 'V5S')           # console +5V / 2 on U6 ADC2
res('100k', 21.8, 50.6, 'SD_DAT1', '3V3_F'); res('100k', 23.4, 50.6, 'SD_DAT2', '3V3_F')
cap('10u', C0805, 19.5, 47.2, '3V3_F', rot=0)
# pocket between U6 and U7 (x' 28.6-33.8, h 51.6-56.8): three in a row
res('2.2k', 29.75, 54.2, 'F_CS', '3V3_F'); res('100k', 31.35, 54.2, 'SPI_MISO', '3V3_F'); res('100k', 32.95, 54.2, 'F_IO2', '3V3_F')
# strip between U3 and U7 (2.9 mm high): parts lying flat
cap('10u', C0805, 36.0, 49.17, '3V3_F', rot=0); res('100k', 39.6, 49.17, 'F_IO3', '3V3_F', rot=0)
cap('10n', C0603, 16.2, 47.2, '3V3_F', rot=0)                                          # (x' 41.9 in the strip is U3's pin 1 mark)

# ------------------------------------------------------------------ reset switch and wire pads (front, middle left)
P('SW1', 'Switch', 'SW_Push', 'RESET', 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A', -38.0, 38.0, 90); c('SW1', 1, 'nRST'); c('SW1', 2, 'GND')
P('J2', 'famicart', 'WirePads_1x3', 'RST/GND/LINK pads', 'famicart:WirePads_1x3', -30.0, 38.0, 90); c('J2', 1, 'nRST'); c('J2', 2, 'GND'); c('J2', 3, 'LINK_T')
res('2.2k', -26.0, 40.0, 'LINK', 'LINK_T')                                             # the test pad sees LINK through 2.2k
P('J4', 'famicart', 'WirePads_1x3', 'EXT/GND/3V3 pads', 'famicart:WirePads_1x3', -22.0, 38.0, 90); c('J4', 1, 'EXT_P'); c('J4', 2, 'GND'); c('J4', 3, '3V3_F')
res('2.2k', -19.4, 38.0, 'EXT_P', 'EXT')                                               # a hand-wired lead is where 5 V or static arrives
# Pin 31 (back, left end) feeds the RF modulator on some main boards, and the cartridge is what joins it to pin 30
# (front, right end). The two 10u of the power row sit at pin 30; this one sits at pin 31, 75 mm of track away, so
# that the ripple of up to six module regulators does not ride on the modulator's supply. (Defined last: C8.)
cap('10u', C0805, -41.2, 5.7, '+5V')

POWER_NETS = {'+5V', 'GND'}
# Hand-soldered pads get thermal reliefs into the GND pour (gen_pcb.py). The four shell tabs of the card socket are
# joined solidly instead: they hold the socket, and beside the socket's keep-out areas one of them has room for a
# single spoke only (KiCad asks for two).
SOLID_PADS = {('J3', '11')}

# firmware of each hand-soldered module, printed on the silk under it
ROLE = {'U1': 'cpu', 'U2': 'ppu', 'U3': 'x', 'U4': 'cpu-ext', 'U5': 'ppu-ext', 'U6': 'hub'}
SILK_TEXT = [('famicart rev G', 45.0 - 12.0, H - 33.5, 'F', 1.5), ('famicart rev G (back)', 45.0 - 22.0, H - 37.0, 'B', 1.5),
             ('JLCJLCJLCJLC', 45.0 + 26.0, H - 62.0, 'B', 1.0)]          # JLCPCB prints the order number here ("Specify Position")

# LCSC part numbers -- all JLCPCB Basic parts (checked by gen_jlc.py against the parts API); modules and J3 are hand-soldered
LCSC = {
    '1k x4': ('C20197', '4D03WGJ0102T5E 1k x4 0603'), '2.2k': ('C4190', '0603WAF2201T5E 2.2k 0603'),
    '100k': ('C25803', '0603WAF1003T5E 100k 0603'), '10n': ('C57112', '0603B103K500NT 10nF 0603'), '10u': ('C15850', 'CL21A106KAYNNNE 10uF 0805'),
    '2N7002': ('C8545', '2N7002 SOT-23'), 'B5819W': ('C8598', 'B5819W SOD-123'), 'BAV99': ('C2500', 'BAV99,215 SOT-23'),
    'RESET': ('C318884', 'TS-1187A-B-A-B'),
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
