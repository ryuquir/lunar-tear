"""famicart rev H (docs/13_rev_h_plan.md): eight RP2350B (QFN-80), each with its own 16 MB W25Q128JVSIQ and 12 MHz crystal,
on a 6-layer board for the Nintendo LARGE (MMC5) Famicom shell, every part placed by JLCPCB (two-sided assembly).

  U1  CPU bus (mapper, PRG, cartridge RAM, LINK master; WLINK sender)        row 1, right of centre
  U2  PPU bus (CHR, nametables, PPU write capture; PEV to U3)                 row 1, left of centre
  U3  /IRQ, expansion audio, CIRAM /CE + A10; sees the whole CPU bus (ZA/ZD)  row 1, centre (2 mm right of the front O2 post)
  U4  CPU-bus extension (permanent), XLINK to U1 and U8, IRQ4                  row 2, right edge, above U8
  U5  PPU-bus extension (permanent), XLINK to U2 and U9, IRQ5                  row 2, left edge, above U9
  U6  hub: USB-C, microSD (4-bit / SPI1), SWD master of the other seven, nRST, VSEL, V5S / VBUS_S, EXT; U7 on QMI CS1
  U8  compute only (CPU side), XLINK-48 / -89                                 row 1, right edge
  U9  compute only (PPU side), XLINK-59 / -89                                 row 1, left edge
  U7  W25Q128JVSIQ on the hub's QSPI chip select 1 (GPIO47, 2.2k pull-up)
The console-interface band (fingers to h 21) is rev G's (design_revg.py) part for part, mirrored and moved to the back.

Drawing: the board is drawn as seen from the BACK of the cartridge (docs/13 "基板データの描き方"): KiCad F.Cu = the back
(main component side, JLCPCB "Top"), KiCad B.Cu = the front (label side, JLCPCB "Bottom"); x -> 90 - x against rev G.
Coordinates below: x' from the board centre line in this drawing (+ = right as seen from the back, i.e. the CPU side of
the card edge), h above the card-edge shoulder. The shell is shells.mirrored(hvc_large(...)), the card edge
famicart:Famicom_CardEdge_60_M (pins 31-60 on F.Cu, 1-30 on B.Cu).

Two-sided: KiCad F carries every IC, connector, switch, LED, FET, diode and the band; KiCad B (the label side) only
parts that may be turned by 180 degrees without harm (BOTTOM_OK): the 100 nF / 4.7 uF decoupling directly behind each
QFN and flash, each chip's crystal with its 12 pF pair and XOUT 1k, and the LINK 250-ohm arrays; plus the wire / test
pads (not assembled).

Each chip block (orig = the QFN footprint's own frame, rot 0 or 180 on the board):
  QFN at the block centre; SOIC-8 flash over the QSPI edge (pins 69-75) at orig (+2.0, -10.1) (hub: -4.6, so that pins
  66 / 67 have a free way up to the USB-C); on KiCad B behind the QFN a ring of 13 x 100 nF + 1 x 4.7 uF around the
  exposed-pad vias, the crystal group behind pins 30 / 31 (orig y 4.1 .. 7.9), the LINK array behind GPIO28.
Power per docs/13 "電源" (datasheet Fig. 24, external DVDD): VREG_FB and VREG_PGND to GND, VREG_LX open, VREG_VIN and
VREG_AVDD on +3V3 with one 4.7 uF, DVDD (10 / 32 / 51) on +1V1 with 100 nF each, 100 nF on each 3.3 V pin (68 and 69
share one). Two TLV62569DBVR: +3V3 (10k / 2.2k = 3.327 V) and +1V1 (10k / (10k + 2.2k) = 1.092 V, VSEL via Q7 puts
2 x 100k across the lower resistor: 1.122 V).

Where this file departs from the plan's block sketch (docs/13 "基板", 配置の案), and why:
  * Rows: the plan's 19.7 mm row height holds the QFN, the flash and the fan-out, but not the crystal group as well. The
    crystal groups therefore sit on KiCad B, and row 1 reaches h 46.5 (plan 45.2), row 2 starts at h 44.5 under U5, at
    46.6 (B) / 48.8 (F) under U4 and at 47.6 (B) under the hub. Rot-0 chips of row 1 stand with their QFN at h 33.5 so
    that their crystal clears the front rib band (h 22.6-25.4); rot-180 chips at h 38.5 so that their flash clears the slot.
  * U3 is 2 mm to the right (x' +2) as the plan says; with this ring of decoupling the post then stands between the
    exposed-pad vias and the right-hand column of capacitors, which stands upright 0.7 mm further out on U3 (RING_POST).
    The inner channels become 10.3 mm (U2 | U3) and 6.3 mm (U3 | U1) between courtyards.
  * The +3V3 converter is not under the microSD socket with the +1V1 one (no room for both and the VSEL network); it
    sits in the free strip at the top right, beside the USB diode D11 (both fed from V5_IN).
  * The USB-C sits 6 mm right of the hub's centre (the hub's flash takes the space straight above the hub).
  * U8 / U9 stand at x' +-36.2 (plan +-37.7): 1.5 mm inward, their pins on the board-edge side get a 2.9 mm escape strip
    before the side route keep-out (x' 44.4) and their flashes clear it; the channels U1 | U8 and U9 | U2 become 5.7 mm
    between courtyards (plan: 3.81 mm).
  * The hub stands 1 mm above row 2 (HUB_H): one row of vias between U3's and the hub's crystal groups on KiCad B.
  * The hub's M2 (GPIO33) has its own 1k (RN18's spare element) instead of joining U1 / U4's node C_M2 (docs/13).
  * Pre-routed (PREROUTE with layers): the 0.8 mm +5V trunk from pin 30 (B.Cu) to C4 / C3 / D10, the two ground-finger
    straps, and the 0.5 mm V5_IN trunk on B.Cu from D10 to both converters."""
import shells
from design_revd import GPIO_PIN       # RP2350B QFN-80: GPIO number -> pin number (checked against the datasheet, docs/13)

REV = 'rev H'
LAYERS = 6
STACKUP = 'JLC06121H-3313'
SHELL = shells.mirrored(shells.hvc_large(75.0, relief=0.6, side_inset=0.2))
JLC_RULES = True
# One track / clearance rule for the whole board (docs/13 "配線の決まり"). Same placement, Freerouting 15 passes:
# 0.15 / 0.15 left 47 connections open, 0.12 / 0.12 15, 0.10 / 0.10 18. JLCPCB multilayer minimum: 0.09 / 0.09.
TRACK, CLEAR, VIA_DIA, VIA_DRILL = 0.12, 0.12, 0.5, 0.3
BODY_H = SHELL['body_h']
H = BODY_H
ASSEMBLY = 'both'
OUTER_GND = True

def at(xp, h):
    """x' (from the centre line, + to the right in this drawing = seen from the back), h (above the shoulder)."""
    return round(45.0 + xp, 3), round(H - h, 3)

PARTS = {}
def P(ref, lib, sym, val, fp, xp, h, rot=0, side='F'):
    assert ref not in PARTS, ref
    x, y = at(xp, h)
    PARTS[ref] = (lib, sym, val, fp, (x, y, round(rot) % 360, side))
NETS = {}
def c(ref, pin, net): NETS.setdefault(ref, {})[str(pin)] = net
_n = {}
_taken = {'C3', 'C4', 'C8'}                                 # rev G's names for the supply capacitors (docs/13)
def nxt(k):
    while True:
        _n[k] = _n.get(k, 0) + 1
        r = f'{k}{_n[k]}'
        if r not in _taken and r not in PARTS: return r

R0402 = 'Resistor_SMD:R_0402_1005Metric'; R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0402 = 'Capacitor_SMD:C_0402_1005Metric'; C0603 = 'Capacitor_SMD:C_0603_1608Metric'; C0805 = 'Capacitor_SMD:C_0805_2012Metric'
RARR = 'Resistor_SMD:R_Array_Convex_4x0603'; SOT23 = 'Package_TO_SOT_SMD:SOT-23'; SOT235 = 'Package_TO_SOT_SMD:SOT-23-5'
SOD123 = 'Diode_SMD:D_SOD-123'; LED0603 = 'LED_SMD:LED_0603_1608Metric'; SOIC8 = 'Package_SO:SOIC-8_5.23x5.23mm_P1.27mm'
XTAL = 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm'; QFN = 'famicart:QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm_NoVia'
SW = 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A'; IND = 'famicart:L_SXN_SMNR4020'; PADS3 = 'famicart:WirePads_1x3'
TP = 'TestPoint:TestPoint_Pad_1.5x1.5mm'

def res(val, xp, h, a, b, rot=90, fp=R0603, side='F', ref=None):
    r = ref or nxt('R'); P(r, 'Device', 'R', val, fp, xp, h, rot, side); c(r, 1, a); c(r, 2, b); return r
def cap(val, fp, xp, h, a, b='GND', rot=90, side='F', ref=None):
    r = ref or nxt('C'); P(r, 'Device', 'C', val, fp, xp, h, rot, side); c(r, 1, a); c(r, 2, b); return r
def rarr(xp, h, pairs, ref=None, rot=180, side='F', val='1k x4'):
    """Resistor array (1k x4 unless `val` says otherwise); pairs = [(console_net, mcu_net)] x4, top to bottom on the board (None for unused).
    Rev G placed its arrays at 0 degrees with the console column on the left; drawn from the back, the mirror image is
    the array at 180 degrees (pins 1-4 on the right column, bottom to top) with the pair list reversed, so every element
    keeps its place relative to the finger it comes from."""
    r = ref or nxt('RN'); P(r, 'Device', 'R_Pack04', val, RARR, xp, h, rot, side)
    seq = list(pairs)[::-1] if rot % 360 == 180 else list(pairs)
    for i, (a, b) in enumerate(seq): c(r, 1 + i, a); c(r, 8 - i, b)
    return r
def nfet(xp, h, g, d, ref=None, rot=180):
    q = ref or nxt('Q'); P(q, 'Transistor_FET', '2N7002', '2N7002', SOT23, xp, h, rot); c(q, 1, g); c(q, 2, 'GND'); c(q, 3, d); return q
def schottky(ref, xp, h, a, k, rot=0):
    P(ref, 'Device', 'D_Schottky', 'B5819W', SOD123, xp, h, rot); c(ref, 1, k); c(ref, 2, a); return ref
def clamp(ref, xp, h, net, rot=180):
    """BAV99 (pin 1 anode, pin 3 common, pin 2 cathode) clamping a console line that ends on a FET gate to GND / +5V (rev G)."""
    P(ref, 'Diode', 'BAV99', 'BAV99', SOT23, xp, h, rot); c(ref, 1, 'GND'); c(ref, 2, '+5V'); c(ref, 3, net); return ref

# ------------------------------------------------------------------ card edge (rev G's nets; drawn from the back)
P('J1', 'famicart', 'Famicom_CardEdge_60', 'Famicom 60-pin edge', 'famicart:Famicom_CardEdge_60_M', 0.0, 0.0)
J1 = {1:'GND',2:'CPU_A11',3:'CPU_A10',4:'CPU_A9',5:'CPU_A8',6:'CPU_A7',7:'CPU_A6',8:'CPU_A5',9:'CPU_A4',10:'CPU_A3',11:'CPU_A2',12:'CPU_A1',13:'CPU_A0',14:'CPU_RW',15:'nIRQ',16:'GND',
      17:'PPU_nRD',18:'CIRAM_A10',19:'PPU_A6',20:'PPU_A5',21:'PPU_A4',22:'PPU_A3',23:'PPU_A2',24:'PPU_A1',25:'PPU_A0',26:'PPU_D0',27:'PPU_D1',28:'PPU_D2',29:'PPU_D3',30:'+5V',
      31:'+5V',32:'M2',33:'CPU_A12',34:'CPU_A13',35:'CPU_A14',36:'CPU_D7',37:'CPU_D6',38:'CPU_D5',39:'CPU_D4',40:'CPU_D3',41:'CPU_D2',42:'CPU_D1',43:'CPU_D0',44:'nROMSEL',
      45:'AUDIO_IN',46:'AUDIO_OUT',47:'PPU_nWE',48:'CIRAM_nCE',49:None,50:'PPU_A7',51:'PPU_A8',52:'PPU_A9',53:'PPU_A10',54:'PPU_A11',55:'PPU_A12',56:'PPU_A13',57:'PPU_D7',58:'PPU_D6',59:'PPU_D5',60:'PPU_D4'}
for p, nn in J1.items(): c('J1', p, nn)

# ------------------------------------------------------------------ pin tables (docs/13 "ピン割り当て")
def xl(link, src):
    """The three wires (clock, data 0, data 1) that chip `src` drives on XLINK `link` ('H1', 'H2', '14', '25', '48', '59', '89')."""
    return [f'X{link}_{src}_CK', f'X{link}_{src}_D0', f'X{link}_{src}_D1']
WL = ['WL_CK', 'WL_D0', 'WL_D1']                          # WLINK: U1 -> U2, U5, hub
def put(g, first, nets):
    for i, n in enumerate(nets): g[first + i] = n

G = {}
g = {i: f'CA{i}' for i in range(15)}; put(g, 15, [f'CD{i}' for i in range(8)])
g.update({23: 'C_RW', 24: 'C_M2', 25: 'C_ROMSEL', 26: 'RSEL_D', 27: 'WS_D', 28: 'LINK_A'})
put(g, 29, WL); put(g, 32, xl('H1', 1)); put(g, 35, xl('H1', 'H')); put(g, 38, xl('14', 1)); put(g, 41, xl('14', 4))
g.update({44: 'XSTAT0', 45: 'XSTAT1', 46: 'VSEL_S', 47: 'LED1'}); G[1] = g
g = {i: f'PA{i}' for i in range(14)}; put(g, 14, [f'PD{i}' for i in range(8)])
g.update({22: 'RD_D', 23: 'PEV', 24: 'P_WE', 25: None, 26: 'PWS_D', 27: 'PLINK_B', 28: 'LINK_B'})
put(g, 29, WL); put(g, 32, xl('H2', 2)); put(g, 35, xl('H2', 'H')); put(g, 38, xl('25', 2)); put(g, 41, xl('25', 5))
g.update({44: 'VSEL_S', 45: 'LED2', 46: None, 47: None}); G[2] = g
g = {i: f'ZA{i}' for i in range(15)}; put(g, 15, [f'ZD{i}' for i in range(8)])
g.update({23: 'ZM2', 24: 'Z_RW', 25: 'Z_ROMSEL', 26: None, 27: None, 28: 'LINK_C', 29: 'PWM', 30: 'IRQ_G', 31: 'HIRQ',
          32: 'PA10', 33: 'PA11', 34: 'PA12', 35: 'PA13', 36: 'RD_D3', 37: 'NCE_D', 38: 'NA10_D', 39: 'PEV', 40: 'XSTAT0', 41: 'XSTAT1',
          42: 'IRQ4', 43: 'IRQ5', 44: 'VSEL_S', 45: 'LED3', 46: None, 47: None}); G[3] = g
g = {i: f'CA{i}' for i in range(15)}; put(g, 15, [f'XD{i}' for i in range(8)])
g.update({23: 'C_RW', 24: 'C_M2', 25: 'C_ROMSEL', 26: 'RSEL_D', 27: 'WS_D', 28: 'LINK_D', 29: None, 30: None, 31: None})
put(g, 32, xl('48', 4)); put(g, 35, xl('48', 8)); put(g, 38, xl('14', 4)); put(g, 41, xl('14', 1))
g.update({44: 'IRQ4', 45: 'VSEL_S', 46: 'LED4', 47: None}); G[4] = g
g = {i: f'PA{i}' for i in range(14)}; put(g, 14, [f'YD{i}' for i in range(8)])
g.update({22: 'RD_D', 23: None, 24: 'P_WE', 25: None, 26: 'PWS_D', 27: 'PLINK_E', 28: 'LINK_E'})
put(g, 29, WL); put(g, 32, xl('59', 5)); put(g, 35, xl('59', 9)); put(g, 38, xl('25', 5)); put(g, 41, xl('25', 2))
g.update({44: 'IRQ5', 45: 'VSEL_S', 46: 'LED5', 47: None}); G[5] = g
g = {}                                                    # U6 hub: no spare pin left (docs/13)
# Each group on the side of the QFN that faces where it goes (U6 at 0 degrees; GPIO0-3 on the top side, 4-20 left,
# 21-32 bottom, 33-47 right): the microSD on SPI0 (GPIO2 SCK, 3 TX, 4 RX) at the corner towards J3, LINK_F next to its
# array RN25 (top left), WLINK and XLINK-H2 (U2) down the left side, XLINK-H1 (U1) and HIRQ (U3) at the bottom right,
# the SWD of U5 on the left and of U1 on the right. The first layout (microSD at GPIO26-32 on SPI1, XLINK-H1 at 3-8)
# crossed both groups round the hub and left 8 connections there that no finishing step could route (docs/13).
g.update({0: 'LINK_F', 1: 'SD_CD', 2: 'SD_CLK', 3: 'SD_CMD', 4: 'SD_DAT0', 5: 'SD_DAT1', 6: 'SD_DAT2', 7: 'SD_DAT3'})
put(g, 8, WL); put(g, 11, xl('H2', 2)); put(g, 14, xl('H2', 'H'))
g.update({17: 'PLINK_F', 18: 'SWCLK5', 19: 'SWDIO5', 20: 'SWCLK2', 21: 'SWDIO2', 22: 'SWCLK3', 23: 'SWDIO3', 24: 'nRST', 25: 'VSEL_S'})
put(g, 26, xl('H1', 1)); put(g, 29, xl('H1', 'H'))
g.update({32: 'HIRQ', 33: 'HM2', 34: 'PWM2', 35: 'SWCLK4', 36: 'SWDIO4', 37: 'SWCLK1', 38: 'SWDIO1', 39: 'LED6', 40: 'V5S', 41: 'EXT',
          42: 'VBUS_S', 43: 'SWCLK8', 44: 'SWDIO8', 45: 'SWCLK9', 46: 'SWDIO9', 47: 'QSPI6_SS1'}); G[6] = g
for n, (link_out, link_in) in ((8, ('48', '4')), (9, ('59', '5'))):      # U8 / U9: compute only, GPIO0-31 and 46-47 spare
    g = {i: None for i in range(48)}; put(g, 32, xl(link_out, n)); put(g, 35, xl(link_out, link_in))
    put(g, 38, xl('89', n)); put(g, 41, xl('89', 17 - n)); g.update({44: 'VSEL_S', 45: f'LED{n}'}); G[n] = g
for n in G:
    assert set(G[n]) <= set(GPIO_PIN), n
    for k in range(48): G[n].setdefault(k, None)

# ------------------------------------------------------------------ the eight chip blocks
DVDD = (10, 32, 51)
V33 = (5, 15, 24, 29, 41, 50, 60, 76, 59, 68, 69)          # IOVDD x8, ADC_AVDD, USB_OTP_VDD, QSPI_IOVDD
# KiCad B ring behind the QFN, in the QFN's own frame (x, y, angle, footprint, value, net; the other pad on GND):
# 13 x 100 nF and the 4.7 uF of VREG_VIN / VREG_AVDD around the 3 x 3 exposed-pad vias (+-1.35 mm)
RING = [(-3.3, -2.2, 0, C0402, '100n', '+3V3'),           # pin 5   IOVDD
        (-3.3, -0.2, 0, C0402, '100n', '+1V1'),           # pin 10  DVDD
        (-3.3, 1.8, 0, C0402, '100n', '+3V3'),            # pin 15  IOVDD
        (3.3, 2.6, 0, C0402, '100n', '+3V3'),             # pin 41  IOVDD
        (3.3, 0.7, 0, C0402, '100n', '+3V3'),             # pin 50  IOVDD
        (3.3, -0.7, 0, C0402, '100n', '+1V1'),            # pin 51  DVDD
        (3.3, -1.95, 0, C0402, '100n', '+3V3'),           # pin 59  ADC_AVDD
        (4.4, -3.5, 90, C0402, '100n', '+3V3'),           # pin 60  IOVDD
        (-1.8, -3.3, 90, C0402, '100n', '+3V3'),          # pin 76  IOVDD
        (-0.5, -3.3, 90, C0402, '100n', '+3V3'),          # pins 68 + 69 (USB_OTP_VDD, QSPI_IOVDD)
        (2.0, -4.0, 0, C0603, '4.7u', '+3V3'),            # pins 61 + 64 (VREG_AVDD, VREG_VIN)
        (-2.6, 3.3, 90, C0402, '100n', '+3V3'),           # pin 24  IOVDD
        (-0.6, 3.3, 90, C0402, '100n', '+3V3'),           # pin 29  IOVDD
        (0.6, 3.3, 90, C0402, '100n', '+1V1')]            # pin 32  DVDD
# U3 sits over the front O2 post (x' +-1.2, h 38.25-40.65): its right column stands upright further out, so that the
# post lands between the column and the exposed-pad vias
RING_POST = RING[:3] + [(4.0, 2.9, 90, C0402, '100n', '+3V3'), (4.0, 0.9, 90, C0402, '100n', '+3V3'), (4.0, -1.1, 90, C0402, '100n', '+1V1'),
                        (4.0, -3.1, 90, C0402, '100n', '+3V3'), (5.0, -3.4, 90, C0402, '100n', '+3V3')] + RING[8:]
FLASH_Y = -10.1                                            # flash centre in the QFN frame (courtyards 1.6 mm apart)
CHIP_XY = {}

def chip(n, xp, hc, rot, run, fx=2.0, ring=RING, xtal_dx=0.0, link=None, link_x=5.5, led=((7.0, 6.4), (7.0, -6.4)), usb=False, fcap_dx=3.6):
    """RP2350B U<n> with flash U1<n>, crystal Y<n>, decoupling, LED D2<n> + 2.2k. (xp, hc): QFN centre; rot 0 / 180.
    led: board-relative centres (dx, dy, y down) of the LED and of its resistor (both at 0 degrees)."""
    ref = f'U{n}'; CHIP_XY[ref] = (xp, hc, rot)
    def o(ox, oy):                                         # QFN frame -> (x', h)
        bx, by = (ox, oy) if rot == 0 else (-ox, -oy)
        return xp + bx, hc - by
    P(ref, 'famicart', 'RP2350B', 'RP2350B', QFN, xp, hc, rot)
    for gp, net in G[n].items(): c(ref, GPIO_PIN[gp], net)
    for p, nn in {30: f'XIN{n}', 31: f'XOUT{n}', 33: f'SWCLK{n}', 34: f'SWDIO{n}', 35: run,
                  70: f'QSPI{n}_SD3', 71: f'QSPI{n}_SCLK', 72: f'QSPI{n}_SD0', 73: f'QSPI{n}_SD2', 74: f'QSPI{n}_SD1', 75: f'QSPI{n}_SS',
                  66: 'USB_DM_R' if usb else None, 67: 'USB_DP_R' if usb else None,
                  61: '+3V3', 64: '+3V3', 62: 'GND', 65: 'GND', 63: None, 81: 'GND'}.items(): c(ref, p, nn)   # VREG: Fig. 24, LX open
    for p in DVDD: c(ref, p, '+1V1')
    for p in V33: c(ref, p, '+3V3')
    assert len(NETS[ref]) == 81, (ref, len(NETS[ref]))
    # flash on QSPI CS0, its 100 nF behind pin 8 (KiCad B)
    fl = f'U1{n}'; x_, h_ = o(fx, FLASH_Y)
    P(fl, 'Memory_Flash', 'W25Q128JVS', 'W25Q128JVSIQ', SOIC8, x_, h_, rot)
    for p, s in {1: 'SS', 2: 'SD1', 3: 'SD2', 5: 'SD0', 6: 'SCLK', 7: 'SD3'}.items(): c(fl, p, f'QSPI{n}_{s}')
    c(fl, 4, 'GND'); c(fl, 8, '+3V3')
    cap('100n', C0402, *o(fx + fcap_dx, FLASH_Y - 1.9), '+3V3', rot=rot, side='B')
    # decoupling ring (KiCad B)
    for (ox, oy, a, fp, val, net) in ring: cap(val, fp, *o(ox, oy), net, rot=a + rot, side='B')
    # crystal group behind pins 30 / 31 (KiCad B): XIN - crystal pin 1, XOUT - 1k - crystal pin 3, 12 pF on each side
    y = f'Y{n}'; P(y, 'Device', 'Crystal_GND24', '12MHz', XTAL, *o(xtal_dx, 6.2), rot, 'B')
    c(y, 1, f'XIN{n}'); c(y, 3, f'XOUT{n}_R'); c(y, 2, 'GND'); c(y, 4, 'GND')
    cap('12p', C0402, *o(xtal_dx - 2.9, 6.2), f'XIN{n}', rot=90 + rot, side='B')
    cap('12p', C0402, *o(xtal_dx + 2.9, 6.2), f'XOUT{n}_R', rot=90 + rot, side='B')
    res('1k', *o(xtal_dx + 2.9, 4.1), f'XOUT{n}', f'XOUT{n}_R', rot=90 + rot, fp=R0402, side='B')
    # LINK: 250 ohm (one 1k x4 array, all four in parallel) at the chip, KiCad B
    if link: rarr(*o(link_x, 6.0), [(link[1], 'LINK')] * 4, ref=link[0], rot=rot, side='B')
    # status LED (KT-0603R) + 2.2k on the GPIO of the pin table
    (lx, ly), (rx, ry) = led
    d = f'D2{n}'; P(d, 'Device', 'LED', 'KT-0603R', LED0603, xp + lx, hc - ly, 0); c(d, 1, 'GND'); c(d, 2, f'LED{n}_A')
    res('2.2k', xp + rx, hc - ry, f'LED{n}', f'LED{n}_A', rot=0)

ROW1_LO, ROW1_HI = 33.5, 38.5          # QFN centres in row 1: flash above (rot 0) / below (rot 180)
ROW2 = 54.5                            # row 2, rot 0 (flash above)
HUB_H = ROW2 + 1.0                     # the hub 1 mm higher: a row of vias between the crystal groups of U3 and the hub (B)
# Row 1 (h 25.5-46.5): U9, U2, U3, U1, U8. Bus pins face the outer channels (U2 left, U1 / U3 right), the links of U8 /
# U9 face the board edge, where XLINK-48 / -59 run straight up to U4 / U5.
chip(9, -36.2, ROW1_HI, 180, 'nRST', led=((4.3, 8.5), (4.3, 11.0)), fcap_dx=0.9)          # flash 100 nF off the corner rib box
chip(2, -19.4, ROW1_LO, 0, 'nRST', link=('RN22', 'LINK_B'))
chip(3, 2.0, ROW1_HI, 180, 'nRST', ring=RING_POST, link=('RN24', 'LINK_C'), led=((-7.0, -6.4), (-7.0, 6.35)), fcap_dx=1.2)   # flash 100 nF off the slot's rib box
chip(1, 19.4, ROW1_HI, 180, 'nRST', link=('RN20', 'LINK_A'), led=((-7.0, -6.4), (-7.0, 6.35)))
chip(8, 36.2, ROW1_LO, 0, 'nRST', xtal_dx=-1.1, led=((-1.2, 6.85), (2.3, 6.85)))   # LED + 2.2k as low as the notch allows
# Row 2 (h 44.5-67.5): U5 (rot 180, bus to the right), TF-01A with the +1V1 supply under it, hub with the USB-C above it,
# U7 + SW1-SW3, U4 (rot 0, bus to the left).
chip(5, -36.6, 57.5, 180, 'nRST', link=('RN23', 'LINK_E'), led=((7.0, -6.4), (7.0, -8.0)))
chip(6, 0.0, HUB_H, 0, 'RUN6', fx=-4.6, link=('RN25', 'LINK_F'), link_x=-5.5, led=((7.0, 6.4), (7.0, 8.0)), usb=True)
chip(4, 36.6, ROW2, 0, 'nRST', link=('RN21', 'LINK_D'), led=((-6.15, -8.6), (-6.15, -11.0)), fcap_dx=1.2)   # flash 100 nF off the right tab

# ------------------------------------------------------------------ console-interface band (rev G, mirrored, KiCad F)
# The arrays stand in the order of the fingers below them (see design_revg.py). Finger x' in this drawing (F | B):
#   CPU  M2 34.3, A12, A13, A14 26.7, D7 24.1 .. D0 6.4, /ROMSEL 3.86 | A11 34.3 .. A0 6.4, R/W 3.86, /IRQ 1.32
#   PPU  /WE -3.76, CIRAM /CE -6.3, A7 -11.4 .. A13 -26.7, D7 -29.2 .. D4 -36.8 | /RD -3.76, CIRAM A10 -6.3, A6 -8.84 .. A0 -24.1, D0 -26.7 .. D3 -34.3
HA = 5.0
XA = {1: 13.1, 2: 23.9, 3: 32.3, 4: 28.7, 5: 9.5, 6: 20.3, 13: 5.9, 14: 16.7}       # RN number -> x' (CPU side)
rarr(XA[1], HA, [(f'CPU_A{b}', f'CA{b}') for b in (3, 2, 1, 0)], 'RN1')
rarr(XA[2], HA, [(f'CPU_A{b}', f'CA{b}') for b in (7, 6, 5, 4)], 'RN2')
rarr(XA[3], HA, [(f'CPU_A{b}', f'CA{b}') for b in (11, 10, 9, 8)], 'RN3')
rarr(XA[4], HA, [('M2', 'C_M2'), ('CPU_A12', 'CA12'), ('CPU_A13', 'CA13'), ('CPU_A14', 'CA14')], 'RN4')
# CPU data: 680 ohm per bit for the three chips that can drive the bus (rev G: 1k). The timing check of the routed board
# (rev G's model, extended by the read chain M2 -> /ROMSEL -> chip -> data bus): with 1k the bus settles in 80 ns typ and
# 170 ns in the worst corner, and the worst-case chain ends 52 ns after the latest point for a 100 ns set-up time
# (rev G in the same model: 70 ns after). 680 ohm takes 52 ns off the worst corner. Value only: same array footprint,
# no change of the netlist (docs/13 "本体側の回路"). Two chips driving against each other still see 1.36k between them.
CPU_DATA_R = '680 x4'
rarr(XA[5], HA, [(f'CPU_D{b}', f'CD{b}') for b in (3, 2, 1, 0)], 'RN5', val=CPU_DATA_R)           # U1 data
rarr(XA[6], HA, [(f'CPU_D{b}', f'CD{b}') for b in (7, 6, 5, 4)], 'RN6', val=CPU_DATA_R)
ppu_x = [-(12.0 + 3.6 * i) for i in range(8)]
rarr(ppu_x[0], HA, [('CIRAM_nCE', 'NCE_D'), ('CIRAM_nCE', 'NCE_D'), ('PPU_A6', 'PA6'), ('PPU_A5', 'PA5')], 'RN7')
rarr(ppu_x[1], HA, [('PPU_A7', 'PA7'), ('PPU_A4', 'PA4'), ('PPU_A8', 'PA8'), ('PPU_A3', 'PA3')], 'RN8')
rarr(ppu_x[2], HA, [('PPU_A9', 'PA9'), ('PPU_A2', 'PA2'), ('PPU_A10', 'PA10'), ('PPU_A1', 'PA1')], 'RN9')
rarr(ppu_x[3], HA, [('PPU_A11', 'PA11'), ('PPU_A0', 'PA0'), ('PPU_A12', 'PA12'), ('PPU_A13', 'PA13')], 'RN10')
def two(a, b, mod):      # one array for two PPU data bits of one chip: two elements in parallel per bit
    return [(f'PPU_D{a}', f'{mod}{a}')] * 2 + [(f'PPU_D{b}', f'{mod}{b}')] * 2
# PPU data: 680 ohm arrays, 340 ohm per bit (rev G: 1k arrays, 500 ohm). The timing check of the routed 0.12 mm board
# put the PPU read at 500 ohm 0 +- 4 ns from the /RD deadline and 28-38 ns past docs/13's target; docs/13's fallback
# (333 ohm, 1k x3) needs four more arrays, 680 ohm x2 needs none (docs/13 "本体側の回路")
PPU_DATA_R = '680 x4'
PPU_PAIRS = ((0, 1), (2, 3), (6, 7), (4, 5))
for i in range(2): rarr(ppu_x[4 + i], HA, two(*PPU_PAIRS[i], 'PD'), f'RN{11 + i}', val=PPU_DATA_R)  # U2 data, bits 0-3
rarr(XA[13], HA, [(f'CPU_D{b}', f'XD{b}') for b in (3, 2, 1, 0)], 'RN13', val=CPU_DATA_R)         # U4 data
rarr(XA[14], HA, [(f'CPU_D{b}', f'XD{b}') for b in (7, 6, 5, 4)], 'RN14', val=CPU_DATA_R)
for i in range(2): rarr(ppu_x[6 + i], HA, two(*PPU_PAIRS[2 + i], 'PD'), f'RN{15 + i}', val=PPU_DATA_R)   # U2 data, bits 4-7
rarr(-8.4, HA, [('PPU_nRD', 'RD_D'), ('PPU_nWE', 'PWE_G'), ('CIRAM_A10', 'NA10_D'), ('CIRAM_A10', 'NA10_D')], 'RN17')
# rev H: raw R/W and /ROMSEL to the 5 V tolerant pins (U1 / U4 GPIO23 / 25 on one node, U3 GPIO24 / 25 on its own),
# PPU /WE to U2 / U5 GPIO24 (one element used), both by the fingers at the centre
rarr(2.5, HA, [('CPU_RW', 'C_RW'), ('nROMSEL', 'C_ROMSEL'), ('CPU_RW', 'Z_RW'), ('nROMSEL', 'Z_ROMSEL')], 'RN31')
# ... and PPU /RD to U3 alone (RD_D3): U3's branch off the shared RD_D node (U2, U5) takes about 8 pF off it, and the
# PPU read waits on that node (about 2 ns per pF)
rarr(-3.0, HA, [('PPU_nWE', 'P_WE'), ('PPU_nRD', 'RD_D3'), (None, None), (None, None)], 'RN32')
# rev H: U3's own branch of the CPU bus (ZA1-ZA4, ZD1-ZD2), a row above the arrays of the same fingers, so that the
# console-side stubs stay short (docs/13: U1 / U4's address node is not enlarged)
HZ = 9.6
rarr(7.7, HZ, [(f'CPU_D{b}', f'ZD{b}') for b in (3, 2, 1, 0)], 'ZD1', val=CPU_DATA_R)
rarr(11.6, HZ, [(f'CPU_A{b}', f'ZA{b}') for b in (3, 2, 1, 0)], 'ZA1')
rarr(18.5, HZ, [(f'CPU_D{b}', f'ZD{b}') for b in (7, 6, 5, 4)], 'ZD2', val=CPU_DATA_R)
rarr(22.3, HZ, [(f'CPU_A{b}', f'ZA{b}') for b in (7, 6, 5, 4)], 'ZA2')
rarr(28.5, HZ, [('M2', 'ZM2'), ('CPU_A12', 'ZA12'), ('CPU_A13', 'ZA13'), ('CPU_A14', 'ZA14')], 'ZA4')
rarr(32.4, HZ, [(f'CPU_A{b}', f'ZA{b}') for b in (11, 10, 9, 8)], 'ZA3')

# CPU-side strobes (rev G's row, moved up above the ZA / ZD row)
HB = 14.2
nfet(38.2, HB, 'M2', 'M2n', 'Q1')                                                       # M2n = NOT M2 (0 / 5 V)
rarr(34.3, HB, [('M2n', '+5V'), ('WS_D', '+3V3'), ('RSEL_D', '+3V3'), ('M2', 'HM2')], 'RN18')   # the three 1k pull-ups (now to the common +3V3);
# rev H: the spare element is the hub's own 1k branch of M2 (GPIO33, duty measurement), so that the hub's track does not
# load U1 / U4's M2 node C_M2
nfet(30.2, HB, 'CPU_RW', 'WS_D', 'Q2'); nfet(26.2, HB, 'M2n', 'WS_D', 'Q3')              # WS_D low while R/W is high or M2 is low
nfet(22.2, HB, 'nROMSEL', 'RSEL_D', 'Q4'); res('2.2k', 19.2, HB, 'nROMSEL', '+5V')       # RSEL_D = NOT /ROMSEL; 2.2k lifts the 74LS139's high level
res('100k', 16.8, HB, 'CPU_RW', '+5V')                                                 # R/W reads "read" while the CPU pins float
HC = 18.4
clamp('D5', 38.2, HC, 'M2'); clamp('D6', 30.2, HC, 'CPU_RW'); clamp('D7', 22.2, HC, 'nROMSEL')

# audio and /IRQ (centre, by pins 15 / 45 / 46)
HD = 10.8
res('2.2k', 4.6, HD, 'AUDIO_IN', 'AMIX'); res('2.2k', 2.2, HD, 'AMIX', 'AUDIO_OUT')     # console audio: 4.4k
rarr(-1.4, HD, [('PWM', 'AF1'), ('AF1', 'AF2'), ('AF2', 'AUDIO_OUT'), ('PWM2', 'AF1')], 'RN19')   # U3 and hub PWM, 1k each -> AF1 -1k- AF2 -1k- out
cap('10n', C0603, -4.6, HD, 'AF1'); cap('10n', C0603, -7.0, HD, 'AF2')
nfet(1.6, 15.6, 'IRQ_G', 'nIRQ', 'Q5'); res('2.2k', -1.4, 15.6, 'IRQ_G', 'GND')          # Q5: open-drain /IRQ from U3
clamp('D8', 5.8, 15.6, 'nIRQ')
# idle level of LINK: 4.4k to +3V3; the test pad J2 sees LINK through 2.2k (LINK arrays: at the chips)
res('2.2k', -5.0, 19.2, 'LINK', 'LINK_PU'); res('2.2k', -3.35, 19.2, 'LINK_PU', '+3V3'); res('2.2k', -1.7, 19.2, 'LINK', 'LINK_T')
# PPU side
res('10k', -9.4, HD, 'CIRAM_nCE', '+3V3')                                             # rev H: CIRAM /CE held high while U3 is not driving
res('10k', -11.05, HD, '+5V', 'V5S'); res('10k', -12.7, HD, 'V5S', 'GND')               # console +5V / 2 on hub ADC0 (GPIO40), 10k / 10k
nfet(-15.6, HD, 'PWE_G', 'PWS_D', 'Q6'); res('2.2k', -18.6, HD, 'PWS_D', '+3V3'); res('2.2k', -20.2, HD, 'PWS_D', '+3V3')   # PWS_D = NOT /WE, 1.1k
clamp('D9', -23.3, HD, 'PWE_G')
for i in range(4): rarr(ppu_x[4 + i] - 0.5, HD, two(PPU_PAIRS[i][1], PPU_PAIRS[i][0], 'YD'), f'RN{27 + i}', val=PPU_DATA_R)   # U5 data, 340 ohm
# +5V entry: pin 30 (B.Cu, x' -37.33) -> 0.8 mm trunk with C3 / C4 -> D10 (D_CON) -> V5_IN; pin 31 tied to +5V with C8
cap('10u', C0805, -41.15, 6.7, '+5V', rot=0, ref='C3'); cap('10u', C0805, -41.15, 4.6, '+5V', rot=0, ref='C4')
schottky('D10', -42.0, 9.0, '+5V', 'V5_IN', rot=180)                                   # D_CON: anode on the trunk (left), cathode right
cap('10u', C0805, 41.2, 5.7, '+5V', ref='C8')
# PLINK: hub -> U2 / U5, 500 ohm per receiver (between U5 and the +1V1 supply, where the two branches part; KiCad F)
rarr(-27.5, 48.6, [('PLINK_F', 'PLINK_B'), ('PLINK_F', 'PLINK_B'), ('PLINK_F', 'PLINK_E'), ('PLINK_F', 'PLINK_E')], 'RN26', rot=0)

# ------------------------------------------------------------------ supplies
# +1V1 (U21, the cores of all eight chips) under the microSD socket; VSEL: Q7 puts 2 x 100k across the lower resistor
# (TI SLVSDG1C 10.2: input capacitor at VIN / GND, inductor at SW, the feedback divider at FB on the far side from SW)
P('U21', 'Regulator_Switching', 'TLV62569DBV', 'TLV62569DBVR', SOT235, -22.2, 53.8, 0)    # SW / VIN row (h 52.85) faces L2
for p, nn in {1: 'V5_IN', 2: 'GND', 3: 'SW_1V1', 4: 'V5_IN', 5: 'FB_1V1'}.items(): c('U21', p, nn)   # EN tied to VIN
P('L2', 'Device', 'L', '2.2uH', IND, -22.2, 49.2, 0); c('L2', 1, 'SW_1V1'); c('L2', 2, '+1V1')
cap('10u', C0805, -18.4, 52.6, 'V5_IN', rot=0)                                           # input 10 uF beside VIN (pin 4)
cap('22u', C0805, -16.6, 49.2, '+1V1'); cap('22u', C0805, -14.4, 49.2, '+1V1')
# divider row: the three FB pads (R30, R33, R31) side by side on the top row, level with FB (pin 5); R30 takes +1V1 down
# between the two 22 uF; only VSEL_M (under R31 / R32) and VSEL_D (to Q7) run further
res('10k', -15.9, 53.8, '+1V1', 'FB_1V1'); res('10k', -12.6, 53.8, 'FB_1V1', 'FB_1V1_M', rot=270); res('2.2k', -10.95, 53.8, 'FB_1V1_M', 'GND')
res('100k', -14.25, 53.8, 'FB_1V1', 'VSEL_M', rot=270); res('100k', -9.3, 53.8, 'VSEL_M', 'VSEL_D')
nfet(-9.9, 49.2, 'VSEL_S', 'VSEL_D', 'Q7', rot=0); res('100k', -12.62, 49.2, 'VSEL_S', 'GND', rot=270)   # gate pull-down beside Q7: low voltage while the hub is in reset
# +3V3 (U20) at the top right, beside the USB diode D11 (D_USB)
schottky('D11', 14.5, 71.8, 'VBUS', 'V5_IN')
cap('10u', C0805, 19.0, 71.5, 'V5_IN', rot=270)                                          # input 10 uF: V5_IN level with VIN, GND below
P('U20', 'Regulator_Switching', 'TLV62569DBV', 'TLV62569DBVR', SOT235, 22.6, 71.5, 180)  # VIN (21.46) / SW (23.74) row at h 72.45
for p, nn in {1: 'V5_IN', 2: 'GND', 3: 'SW_3V3', 4: 'V5_IN', 5: 'FB_3V3'}.items(): c('U20', p, nn)
P('L1', 'Device', 'L', '2.2uH', IND, 28.2, 71.5, 0); c('L1', 1, 'SW_3V3'); c('L1', 2, '+3V3')
cap('10u', C0805, 32.6, 71.5, '+3V3')
# divider under FB (pin 5, h 70.55): both FB pads (23.28 / 21.83) within 2.3 mm of it, +3V3 taken on the right (towards
# L1 and the output 10 uF), GND on the left beside the input capacitor's GND
res('10k', 24.1, 68.3, '+3V3', 'FB_3V3', rot=180); res('2.2k', 21.0, 68.3, 'FB_3V3', 'GND', rot=180)
# test pads (KiCad B, not assembled): measure the dividers before the first power-up (docs/13 "立ち上げ" 1)
for i, (net, xp, h) in enumerate((('+1V1', -16.0, 51.0), ('+3V3', 30.0, 71.5), ('V5_IN', -26.0, 53.5), ('FB_3V3', 22.6, 68.6),
                                  ('FB_1V1', -13.0, 51.0), ('GND', 26.6, 71.5))):
    P(f'TP{i + 1}', 'Connector', 'TestPoint', 'TP ' + net, TP, xp, h, 0, 'B'); c(f'TP{i + 1}', 1, net)

# ------------------------------------------------------------------ USB-C, microSD, U7, switches, pads (row 2)
# USB-C at the top edge, mouth flush with it (HRO: board edge 5.79 mm ahead of the peg line; the EasyEDA origin is 1.206
# mm behind the pegs): D+ / D- through 27 ohm at the hub's pins 66 / 67, CC1 / CC2 each 2 x 10k (5.0k)
P('J7', 'Connector', 'USB_C_Receptacle_USB2.0_16P', 'TYPE-C-31-M-12', 'famicart:USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC', 6.0, H - 4.584, 180)
for pin in ('A4', 'A9', 'B4', 'B9'): c('J7', pin, 'VBUS')
for pin in ('A1', 'A12', 'B1', 'B12', 'S1'): c('J7', pin, 'GND')
c('J7', 'A5', 'CC1'); c('J7', 'B5', 'CC2'); c('J7', 'A6', 'USB_DP'); c('J7', 'B6', 'USB_DP'); c('J7', 'A7', 'USB_DM'); c('J7', 'B7', 'USB_DM')
c('J7', 'A8', None); c('J7', 'B8', None)
# 27 ohm: pad 1 (lower, 1.2 mm from pins 66 / 67) on the hub's side, pad 2 towards J7
res('27', 1.0, HUB_H + 6.6, 'USB_DP_R', 'USB_DP', fp=R0402); res('27', 2.1, HUB_H + 6.6, 'USB_DM_R', 'USB_DM', fp=R0402)
# CC2 (B5, x' 4.25) on the left and CC1 (A5, x' 7.25) on the right of the D+ / D- pins, with a corridor at x' 4.9-7.5 for the
# pair; CC pads on top (towards J7), and 1.1 mm under them for the pair on its way left to the 27 ohm
for xp_, cc in ((2.5, 'CC2'), (4.15, 'CC2'), (8.2, 'CC1'), (9.85, 'CC1')): res('10k', xp_, 65.3, cc, 'GND', rot=270)
res('10k', 8.6, 62.3, 'VBUS', 'VBUS_S', rot=0); res('10k', 11.75, 62.3, 'VBUS_S', 'GND', rot=0)     # VBUS / 2 on hub ADC2 (GPIO42)
# microSD TF-01A at the top edge, card mouth up: CLK GPIO26, CMD 27 (100k), DAT0 28 (100k), DAT1-2 29-30 (100k), DAT3/CS 31
# (10k), CD 32 (internal pull-up), 4.7 uF at VDD (KiCad B)
P('J3', 'famicart', 'TF-01A', 'TF-01A', 'famicart:microSD_HRO_TF-01A', -18.2, H - 9.4, 180)   # symbol with the shell tabs 10-13
for p, nn in {1: 'SD_DAT2', 2: 'SD_DAT3', 3: 'SD_CMD', 4: '+3V3', 5: 'SD_CLK', 6: 'GND', 7: 'SD_DAT0', 8: 'SD_DAT1', 9: 'SD_CD',
              10: 'GND', 11: 'GND', 12: 'GND', 13: 'GND'}.items(): c('J3', p, nn)
for xp_, net, val in ((-21.0, 'SD_DAT2', '100k'), (-19.35, 'SD_DAT3', '10k'), (-17.7, 'SD_CMD', '100k'), (-13.8, 'SD_DAT0', '100k'), (-12.15, 'SD_DAT1', '100k')):
    res(val, xp_, 57.8, net, '+3V3')
cap('4.7u', C0603, -17.1, 62.0, '+3V3', rot=0, side='B')
# U7: the hub's second QSPI chip (CS1 = GPIO47, 2.2k pull-up holds it deselected during boot), on SCLK / SD0-3 of the hub
P('U7', 'Memory_Flash', 'W25Q128JVS', 'W25Q128JVSIQ', SOIC8, 18.0, 63.5, 0)
for p, s in {1: 'SS1', 2: 'SD1', 3: 'SD2', 5: 'SD0', 6: 'SCLK', 7: 'SD3'}.items(): c('U7', p, f'QSPI6_{s}')
c('U7', 4, 'GND'); c('U7', 8, '+3V3')
cap('100n', C0402, 21.6, 65.4, '+3V3', rot=0, side='B')
res('2.2k', 24.0, 63.5, 'QSPI6_SS1', '+3V3')
# SW1: reset of U1-U5, U8, U9 (nRST, 10k pull-up; also hub GPIO24 open drain and J2); SW2: hub BOOTSEL (QSPI_SS through 1k
# to GND); SW3: hub RUN (pad J5). TS-1187A.
P('SW1', 'Switch', 'SW_Push', 'TS-1187A (RESET)', SW, 14.5, 50.5, 0); c('SW1', 1, 'nRST'); c('SW1', 2, 'GND')
P('SW2', 'Switch', 'SW_Push', 'TS-1187A (BOOTSEL)', SW, 22.5, 50.5, 0); c('SW2', 1, 'BOOT6'); c('SW2', 2, 'GND')
P('SW3', 'Switch', 'SW_Push', 'TS-1187A (HUB RUN)', SW, 18.5, 56.5, 0); c('SW3', 1, 'RUN6'); c('SW3', 2, 'GND')
res('1k', -5.0, 70.0, 'QSPI6_SS', 'BOOT6', rot=0, fp=R0402)                           # at the hub's flash (pin 1): only BOOT6 runs to SW2
res('10k', 9.6, 50.5, 'nRST', '+3V3')                                                 # (clear of the hub's LED)
res('2.2k', 9.0, 54.5, 'EXT_P', 'EXT')                                                 # J4: 0-3.3 V only (2.2k limits a 5 V lead to ~0.5 mA)
# wire pads (KiCad B, not assembled)
P('J2', 'famicart', 'WirePads_1x3_GND2', 'RST/GND/LINK pads', PADS3, 0.0, 17.5, 0, 'B'); c('J2', 1, 'nRST'); c('J2', 2, 'GND'); c('J2', 3, 'LINK_T')
P('J4', 'famicart', 'WirePads_1x3_GND2', 'EXT/GND/3V3 pads', PADS3, 18.0, 62.0, 0, 'B'); c('J4', 1, 'EXT_P'); c('J4', 2, 'GND'); c('J4', 3, '+3V3')
P('J5', 'Connector_Generic', 'Conn_01x05', 'hub SWD pads', 'Connector_PinHeader_1.27mm:PinHeader_1x05_P1.27mm_Vertical_SMD_Pin1Left', 26.5, 53.0, 0, 'B')
for p, nn in {1: 'SWCLK6', 2: 'SWDIO6', 3: 'RUN6', 4: 'GND', 5: '+3V3'}.items(): c('J5', p, nn)
P('J6', 'Connector_Generic', 'Conn_02x08_Odd_Even', 'SWD pads U1-U5 U8 U9', 'Connector_PinHeader_1.27mm:PinHeader_2x08_P1.27mm_Vertical_SMD', 18.5, 53.0, 0, 'B')
for i, k in enumerate((1, 2, 3, 4, 5, 8, 9)): c('J6', 2 * i + 1, f'SWCLK{k}'); c('J6', 2 * i + 2, f'SWDIO{k}')
c('J6', 15, 'GND'); c('J6', 16, 'GND')

# ------------------------------------------------------------------ board attributes
POWER_NETS = {'+5V', 'GND', '+3V3', '+1V1', 'V5_IN', 'VBUS'}
# Exposed pads: the footprint has no holes of its own; nine board vias per QFN (0.3 / 0.5 mm, 1.1 mm grid), epoxy filled
# and capped (free on 6 layers); the exposed pad is the only GND terminal of the RP2350B
EP_VIAS = {'footprint': QFN, 'grid': 3, 'pitch': 1.1, 'drill': 0.3, 'dia': 0.5, 'net': 'GND', 'count': 8}

def _poly(pts):
    """[(x', h)] -> board polygon"""
    return [at(xp, h) for xp, h in pts]
def _rect(xp0, h0, xp1, h1): return _poly([(xp0, h0), (xp1, h0), (xp1, h1), (xp0, h1)])
def _core_island(xp, hc, rot):
    """+1V1 on In2 under one chip: a bar through DVDD 10 / 51 (QFN frame y -1.0 .. 0.6) and a stub down to DVDD 32. The bar
    goes round the 3 x 3 exposed-pad vias (+-1.35 mm, 0.25 mm zone clearance) as a U (inner edge +-1.75, bottom 1.75 .. 2.6):
    a straight bar through them would fill as seven pieces and leave DVDD 10, 51 and 32 unjoined."""
    s = 1 if rot == 0 else -1
    pts = [(-4.4, -1.0), (-1.75, -1.0), (-1.75, 1.75), (1.75, 1.75), (1.75, -1.0), (4.4, -1.0), (4.4, 0.6), (2.6, 0.6), (2.6, 2.6),
           (1.0, 2.6), (1.0, 4.0), (0.2, 4.0), (0.2, 2.6), (-2.6, 2.6), (-2.6, 0.6), (-4.4, 0.6)]
    return _poly([(xp + s * x, hc - s * y) for x, y in pts])
# Layers (docs/13 "層の役目", drawn from the back): F.Cu (6) back, main parts, QFN fan-out, USB; In1 (5) GND; In2 (4)
# power: the +3V3 plane with +1V1 islands under each chip and at its supply, V5_IN at the two converter inputs;
# In3 (3) signal; In4 (2) GND; B.Cu (1) front: passives, fingers 1-30, pads. F.Cu and B.Cu get a GND pour (OUTER_GND).
# +1V1 islands that the routed board leaves without any via of +1V1 (island_vias.py finds no room for one): a floating
# island would only cut a hole into the +3V3 plane, so the routed board drops it and so does this map ('OUT' = the
# island at the +1V1 output). Filled in from the routed board (docs/13 "配線の結果"): U3's three DVDD pins and their
# 100 nF are joined by 0.4 mm tracks on B.Cu, under the chip, with no room for a via into the island.
ISLANDS_DROPPED = {'U3'}
PLANES = {'In1.Cu': [('GND', 'board')],
          'In2.Cu': [('+3V3', 'board')] + [('+1V1', _core_island(*CHIP_XY[u])) for u in sorted(CHIP_XY) if u not in ISLANDS_DROPPED]
                    + [('+1V1', _rect(-20.8, 46.9, -13.2, 51.2))] * ('OUT' not in ISLANDS_DROPPED)      # +1V1 output: L2, 2 x 22 uF
                    + [('V5_IN', _rect(-25.5, 51.6, -18.6, 56.0)),                   # +1V1 converter: VIN, EN, input 10 uF, trunk via
                       ('V5_IN', _rect(11.8, 69.4, 24.6, 74.4))],                    # trunk via, D11, +3V3 converter: input 10 uF, VIN, EN
          'In4.Cu': [('GND', 'board')]}
# Wider tracks for the supply nets the router draws (V5_IN from the trunk to the converter pads, VBUS, the switch nodes,
# +1V1 to the 24 DVDD pins). With PLANES the DSN gives every net of this map a width class for ALL its connections, so
# +5V is not in it: its other connections (pin 31 / C8, RN18, the BAV99 cathodes, the 2.2k / 100k / 10k pull-ups and V5S)
# end on 0.4-0.6 mm pads; the supply path itself is pre-routed below (as in rev G).
NET_WIDTH = {'V5_IN': 0.5, 'VBUS': 0.5, 'SW_1V1': 0.5, 'SW_3V3': 0.5, '+1V1': 0.4}
# After routing, widen_tracks.py widens +1V1 to 0.8 mm wherever the rule check allows, before the other supply nets and
# the ground stitching take the room: the far chips' feed (U4: 100 mm of 0.4 mm track) sets the drop of the core supply
# (docs/13 "配線の結果": 35 mV of the 39 mV budget at 0.4 mm with all eight chips at 240 MHz).
WIDEN_FIRST = {'+1V1': 0.8}
# Tracks and vias laid before routing (gen_pcb.py PREROUTE with a layer, PREROUTE_VIAS; the router keeps them):
#  * +5V trunk (docs/13 "電源"): finger 30 is on B.Cu (x' -37.33). 0.8 mm up from the finger on B and left under the
#    shoulder to two vias at x' -40.4 / -41.4 (left of finger 60's way up on F), then on F through the +5V pads of C4 and
#    C3 to the anode of D10.
#  * GND: a strap as wide as rev G's from each ground finger (1: B, x' +37.33, 1.6 mm; 16: B, x' -1.27, 1.2 mm) up into
#    the B.Cu pour.
#  * V5_IN trunk, 0.5 mm on B.Cu (docs/13 layer 1 carries the supply trunk): D10's cathode -> via -> up the left margin
#    and at 45 degrees (clear of the notch) into the U9 | U2 channel at x' -28 -> TP3 -> via into the In2 V5_IN island of
#    the +1V1 converter; from there up to h 63.5, along it under J3 / U16 (free on B) to x' 12.85 and a via into the
#    island of D11 and the +3V3 converter. The converter pads reach the islands through the router's vias.
PREROUTE = [('+5V', 0.8, _poly([(-37.33, -3.4), (-37.33, 1.2), (-41.4, 1.2)]), 'B.Cu'),
            ('+5V', 0.8, _poly([(-40.4, 1.2), (-41.4, 1.2), (-42.1, 1.9), (-42.1, 4.6), (-42.1, 6.7), (-42.1, 7.9), (-43.65, 9.0)])),
            ('GND', 1.6, _poly([(37.33, -3.1), (37.33, 1.4)]), 'B.Cu'), ('GND', 1.2, _poly([(-1.27, -3.3), (-1.27, 1.6)]), 'B.Cu'),
            ('V5_IN', 0.5, _poly([(-40.35, 9.0), (-40.35, 10.5)])),                                             # D10 cathode -> via (F)
            ('V5_IN', 0.5, _poly([(-40.35, 10.5), (-40.35, 19.5), (-28.0, 31.85), (-28.0, 50.5), (-26.0, 52.5), (-26.0, 53.5),
                                  (-24.9, 54.6), (-24.9, 55.4)]), 'B.Cu'),
            ('V5_IN', 0.5, _poly([(-24.9, 55.4), (-24.9, 63.5), (12.85, 63.5), (12.85, 69.9)]), 'B.Cu'),
            ('V5_IN', 0.5, _poly([(12.85, 69.9), (12.85, 71.8)]))]                                              # via -> D11 cathode (F)
PREROUTE_VIAS = [('+5V',) + at(-40.4, 1.2), ('+5V',) + at(-41.4, 1.2),
                 ('V5_IN',) + at(-40.35, 10.5), ('V5_IN',) + at(-24.9, 55.4), ('V5_IN',) + at(12.85, 69.9)]
# Crystal nets of the eight chips (XIN, XOUT, XOUT_R), laid before the autorouter: shortest routes on the unrouted board
# (1.5-2.8 mm, one via), found by  FC_DESIGN=design_revh python3 preroute_nets.py 'XIN\d|XOUT\d(_R)?' XTAL  -- run it again
# if a chip, crystal, 12 pF or 1k moves. Left to Freerouting they went round the QFN fan-out (XOUT8: 32 mm, 4 vias).
PREROUTE_XTAL = [
    ('XIN1', 0.15, _poly([(21.150, 43.800), (21.200, 43.800), (21.250, 43.850), (21.350, 43.850), (21.450, 43.950), (21.500, 43.950), (21.550, 44.000), (22.050, 44.000)]), 'B.Cu'),
    ('XIN1', 0.15, _poly([(19.850, 44.200), (19.850, 44.150), (19.650, 43.950), (19.650, 43.700)]), 'F.Cu'),
    ('XOUT1', 0.15, _poly([(18.050, 42.350), (17.600, 42.350), (17.550, 42.300), (16.750, 42.300)]), 'B.Cu'),
    ('XOUT1', 0.15, _poly([(18.050, 42.350), (18.450, 42.350), (18.850, 42.750), (19.050, 42.750), (19.150, 42.850), (19.150, 43.050)]), 'F.Cu'),
    ('XOUT1_R', 0.15, _poly([(16.250, 44.000), (16.250, 43.300)]), 'B.Cu'),
    ('XOUT1_R', 0.15, _poly([(16.750, 44.300), (16.800, 44.300), (16.850, 44.350), (16.900, 44.350), (16.950, 44.400), (17.050, 44.400), (17.650, 45.000)]), 'B.Cu'),
    ('XIN2', 0.15, _poly([(-22.050, 27.600), (-21.150, 27.600)]), 'B.Cu'),
    ('XIN2', 0.15, _poly([(-19.850, 27.800), (-19.850, 27.850), (-19.650, 28.050), (-19.650, 28.300)]), 'F.Cu'),
    ('XOUT2', 0.15, _poly([(-17.250, 29.450), (-17.200, 29.500), (-17.150, 29.500), (-17.100, 29.550), (-17.050, 29.550), (-17.000, 29.600), (-16.950, 29.600), (-16.900, 29.650), (-16.850, 29.650), (-16.800, 29.700), (-16.750, 29.700)]), 'B.Cu'),
    ('XOUT2', 0.15, _poly([(-17.250, 29.450), (-17.350, 29.450), (-17.400, 29.400), (-17.450, 29.400), (-17.500, 29.350), (-17.550, 29.350), (-17.600, 29.300), (-18.550, 29.300), (-18.600, 29.250), (-19.050, 29.250), (-19.150, 29.150), (-19.150, 28.950)]), 'F.Cu'),
    ('XOUT2_R', 0.15, _poly([(-16.750, 27.550), (-16.800, 27.500), (-16.850, 27.500), (-16.900, 27.450), (-16.950, 27.450), (-17.000, 27.400), (-17.050, 27.400), (-17.100, 27.350), (-17.150, 27.350), (-17.350, 27.150), (-17.500, 27.150), (-17.650, 27.000)]), 'B.Cu'),
    ('XOUT2_R', 0.15, _poly([(-16.750, 28.000), (-16.750, 28.700)]), 'B.Cu'),
    ('XIN3', 0.15, _poly([(4.650, 44.000), (3.850, 44.000), (3.800, 43.950), (3.750, 43.950)]), 'B.Cu'),
    ('XIN3', 0.15, _poly([(2.250, 43.700), (2.250, 43.950), (2.450, 44.150), (2.450, 44.200)]), 'F.Cu'),
    ('XOUT3', 0.15, _poly([(0.650, 42.350), (0.200, 42.350), (0.150, 42.300), (-0.650, 42.300)]), 'B.Cu'),
    ('XOUT3', 0.15, _poly([(0.650, 42.350), (1.050, 42.350), (1.450, 42.750), (1.650, 42.750), (1.750, 42.850), (1.750, 43.050)]), 'F.Cu'),
    ('XOUT3_R', 0.15, _poly([(0.250, 45.000), (0.100, 44.850), (-0.050, 44.850), (-0.300, 44.600), (-0.350, 44.600), (-0.400, 44.550), (-0.450, 44.550), (-0.500, 44.500), (-0.550, 44.500), (-0.600, 44.450), (-0.650, 44.450)]), 'B.Cu'),
    ('XOUT3_R', 0.15, _poly([(-1.150, 44.000), (-1.150, 43.300)]), 'B.Cu'),
    ('XIN4', 0.15, _poly([(33.950, 49.000), (34.850, 49.000)]), 'B.Cu'),
    ('XIN4', 0.15, _poly([(36.150, 48.800), (36.150, 48.850), (36.350, 49.050), (36.350, 49.300)]), 'F.Cu'),
    ('XOUT4', 0.15, _poly([(38.750, 50.450), (38.800, 50.500), (38.850, 50.500), (38.900, 50.550), (38.950, 50.550), (39.000, 50.600), (39.050, 50.600), (39.100, 50.650), (39.150, 50.650), (39.200, 50.700), (39.250, 50.700)]), 'B.Cu'),
    ('XOUT4', 0.15, _poly([(38.750, 50.450), (38.650, 50.450), (38.600, 50.400), (38.550, 50.400), (38.500, 50.350), (38.450, 50.350), (38.400, 50.300), (37.450, 50.300), (37.400, 50.250), (36.950, 50.250), (36.850, 50.150), (36.850, 49.950)]), 'F.Cu'),
    ('XOUT4_R', 0.15, _poly([(39.250, 48.650), (39.200, 48.650), (39.150, 48.600), (38.950, 48.600), (38.350, 48.000)]), 'B.Cu'),
    ('XOUT4_R', 0.15, _poly([(39.250, 49.000), (39.250, 49.700)]), 'B.Cu'),
    ('XIN5', 0.15, _poly([(-33.950, 63.250), (-34.850, 63.250)]), 'B.Cu'),
    ('XIN5', 0.15, _poly([(-36.350, 62.700), (-36.350, 62.950), (-36.150, 63.150), (-36.150, 63.200)]), 'F.Cu'),
    ('XOUT5', 0.15, _poly([(-37.950, 61.350), (-38.400, 61.350), (-38.450, 61.300), (-39.250, 61.300)]), 'B.Cu'),
    ('XOUT5', 0.15, _poly([(-37.950, 61.350), (-37.550, 61.350), (-37.150, 61.750), (-36.950, 61.750), (-36.850, 61.850), (-36.850, 62.050)]), 'F.Cu'),
    ('XOUT5_R', 0.15, _poly([(-39.750, 63.000), (-39.750, 62.300)]), 'B.Cu'),
    ('XOUT5_R', 0.15, _poly([(-39.250, 63.400), (-38.950, 63.400), (-38.350, 64.000)]), 'B.Cu'),
    ('XIN6', 0.15, _poly([(-2.650, 49.600), (-1.750, 49.600)]), 'B.Cu'),
    ('XIN6', 0.15, _poly([(-0.450, 49.800), (-0.450, 49.850), (-0.250, 50.050), (-0.250, 50.300)]), 'F.Cu'),
    ('XOUT6', 0.15, _poly([(2.650, 51.700), (2.600, 51.700), (2.550, 51.650), (2.500, 51.650), (2.450, 51.600), (2.400, 51.600), (2.350, 51.550), (2.300, 51.550), (2.250, 51.500), (2.200, 51.500), (2.150, 51.450)]), 'B.Cu'),
    ('XOUT6', 0.15, _poly([(2.150, 51.450), (2.050, 51.450), (2.000, 51.400), (1.950, 51.400), (1.900, 51.350), (1.850, 51.350), (1.800, 51.300), (0.850, 51.300), (0.800, 51.250), (0.350, 51.250), (0.250, 51.150), (0.250, 50.950)]), 'F.Cu'),
    ('XOUT6_R', 0.15, _poly([(2.650, 50.000), (2.650, 50.700)]), 'B.Cu'),
    ('XOUT6_R', 0.15, _poly([(2.650, 49.600), (2.350, 49.600), (1.750, 49.000)]), 'B.Cu'),
    ('XIN8', 0.15, _poly([(32.450, 27.950), (33.350, 27.950)]), 'B.Cu'),
    ('XIN8', 0.15, _poly([(34.650, 27.800), (34.900, 27.800)]), 'B.Cu'),
    ('XIN8', 0.15, _poly([(34.900, 27.800), (34.950, 27.850), (35.000, 27.850), (35.050, 27.900), (35.100, 27.900), (35.150, 27.950), (35.850, 27.950), (35.950, 28.050), (35.950, 28.300)]), 'F.Cu'),
    ('XOUT8', 0.15, _poly([(36.450, 28.950), (36.450, 29.150), (36.850, 29.550), (37.450, 29.550), (37.500, 29.600), (37.550, 29.600), (37.600, 29.650), (37.650, 29.650), (37.700, 29.700), (37.750, 29.700)]), 'F.Cu'),
    ('XOUT8_R', 0.15, _poly([(37.750, 27.550), (37.700, 27.550), (37.650, 27.500), (37.600, 27.500), (37.550, 27.450), (37.500, 27.450), (37.450, 27.400), (37.400, 27.400), (37.150, 27.150), (37.000, 27.150), (36.850, 27.000)]), 'B.Cu'),
    ('XOUT8_R', 0.15, _poly([(37.750, 28.000), (37.750, 28.700)]), 'B.Cu'),
    ('XIN9', 0.15, _poly([(-33.550, 44.100), (-34.450, 44.100)]), 'B.Cu'),
    ('XIN9', 0.15, _poly([(-35.950, 43.700), (-35.950, 43.950), (-35.750, 44.150), (-35.750, 44.200)]), 'F.Cu'),
    ('XOUT9', 0.15, _poly([(-37.550, 42.350), (-38.000, 42.350), (-38.050, 42.300), (-38.850, 42.300)]), 'B.Cu'),
    ('XOUT9', 0.15, _poly([(-36.450, 43.050), (-36.450, 42.850), (-36.550, 42.750), (-36.750, 42.750), (-37.150, 42.350), (-37.550, 42.350)]), 'F.Cu'),
    ('XOUT9_R', 0.15, _poly([(-39.350, 44.000), (-39.350, 43.300)]), 'B.Cu'),
    ('XOUT9_R', 0.15, _poly([(-37.950, 45.000), (-38.100, 44.850), (-38.250, 44.850), (-38.500, 44.600), (-38.550, 44.600), (-38.600, 44.550), (-38.650, 44.550), (-38.700, 44.500), (-38.750, 44.500), (-38.800, 44.450), (-38.850, 44.450)]), 'B.Cu'),
]
PREROUTE_XTAL_VIAS = [('XIN1',) + at(19.850, 44.200), ('XIN2',) + at(-19.850, 27.800), ('XIN3',) + at(2.450, 44.200), ('XIN4',) + at(36.150, 48.800), ('XIN5',) + at(-36.150, 63.200), ('XIN6',) + at(-0.450, 49.800), ('XIN8',) + at(34.900, 27.800), ('XIN9',) + at(-35.750, 44.200), ('XOUT1',) + at(18.050, 42.350), ('XOUT2',) + at(-17.250, 29.450), ('XOUT3',) + at(0.650, 42.350), ('XOUT4',) + at(38.750, 50.450), ('XOUT5',) + at(-37.950, 61.350), ('XOUT6',) + at(2.150, 51.450), ('XOUT8',) + at(37.750, 29.700), ('XOUT9',) + at(-37.550, 42.350)]
PREROUTE += PREROUTE_XTAL
PREROUTE_VIAS += PREROUTE_XTAL_VIAS
# No inner-layer copper in the card-edge tab below the shoulder (docs/13 "端子の面取り"; the planes stop at h 0.5, this
# keeps the router's In3 tracks and every inner via ring out of the tab as well)
RULE_AREAS = [('tab_inner_keepout', [(5.3, H), (84.7, H), (84.7, H + 11.2), (5.3, H + 11.2)], ['In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu'])]
# Parts that cross the top edge (mouths flush with it, docs/13 "捨て基板"); check_place.py lets their body cross it within
# the shell's usb_top window by at most EDGE_OVERHANG (default 1.0 mm)
EDGE_CONNECTORS = ('J3', 'J7')
# KiCad B (JLCPCB Bottom, the label side): only the 100 nF / 4.7 uF decoupling, the crystal groups (crystal, 12 pF, XOUT
# 1k) and the LINK arrays sit there; these are their footprints (gen_jlc.bottom_ok also wants BOTTOM_TURN footprints)
BOTTOM_OK = {C0402, C0603, R0402, XTAL, RARR}
# Edge rails (make_rails.py): rev G's left and right rails plus a top rail (5 mm, 2 mm gap, mouse-bite tabs), one frame;
# no top tab in front of the USB-C (J7, x 45.9-56.1) or the microSD socket (J3, x 18.2-35.4)
RAILS = dict(width=5.0, gap=2.0, tab=5.2, hole=0.6, hole_out=0.3, pitch=0.9, holes=7, end_gap=2.7,
             tabs={'L': (4.5, 45.0, 60.0), 'R': (4.5, 45.0, 60.0)}, top=dict(tabs=(8.0, 40.6, 83.0)),
             fiducials=(('T', 3.85), ('T', -3.85), ('L', -3.85)), fid_inset=3.85,
             tooling=(('T', 14.0), ('T', -14.0), ('L', -14.0), ('R', -14.0)), tooling_d=2.0)

ROLE = {'U1': 'cpu', 'U2': 'ppu', 'U3': 'x', 'U4': 'cpu-ext', 'U5': 'ppu-ext', 'U6': 'hub', 'U8': 'calc-cpu', 'U9': 'calc-ppu'}
# ROLE text off the exposed pad: 6.6 mm from the QFN centre on the side away from the flash (QFN frame), level
ROLE_AT = {'*': (0, 6.6, 0), 'U8': (0, -6.6, 0), 'U9': (0, -6.6, 0)}      # U8 / U9: the flash side (LED below U8, U5's flash above U9)
SILK_TEXT = [('famicart rev H', 45.0 - 36.0, H - 70.0, 'F', 1.2), ('famicart rev H (front)', 45.0 - 20.0, H - 15.0, 'B', 1.2)]
DRAW_NAMES = {'U1': 'U1 CPU バス', 'U2': 'U2 PPU バス', 'U3': 'U3 IRQ・音源', 'U4': 'U4 CPU 増設', 'U5': 'U5 PPU 増設',
              'U6': 'U6 ハブ', 'U7': 'U7 フラッシュ', 'U8': 'U8 計算 CPU 側', 'U9': 'U9 計算 PPU 側', 'J3': 'J3 microSD',
              'J7': 'J7 USB-C', 'U20': '3.3 V', 'U21': '1.1 V', 'SW1': 'SW1', 'SW2': 'SW2', 'SW3': 'SW3',
              'J2': 'J2', 'J4': 'J4', 'J5': 'J5', 'J6': 'J6'}
DRAW_NOTES = ['8 個の RP2350B（U1〜U6・U8・U9）は、それぞれ自分の 16 MB フラッシュ（U11〜U19）と 12 MHz 水晶を持つ。U7 はハブの 2 個目のフラッシュ。',
              '裏（KiCad の表）にチップ・フラッシュ・電源・コネクタ・スイッチ・LED、表（ラベル面）にコンデンサ・水晶・LINK の抵抗アレイとパッドだけ。',
              '端子の上の帯は rev G と同じ部品の本体側の回路（裏に移し、左右を反転）。USB-C（J7）と microSD（J3）は上端。まだ配線していない。']

# LCSC part numbers (docs/13 "部品表", 24 types); gen_jlc.py checks the classes, stock and pre-sale numbers
LCSC = {
    'RP2350B': ('C42415655', 'RP2350B QFN-80'), 'W25Q128JVSIQ': ('C97521', 'W25Q128JVSIQ 16MB SPI flash SOIC-8 208mil'),
    '12MHz': ('C362368', 'TXM12M0004322CBCDO00T 12MHz 9pF 3225'), '12p': ('C1547', '0402CG120J500NT 12pF C0G 0402'),
    '1k': ('C11702', '0402WGF1001TCE 1k 0402'), '100n': ('C1525', 'CL05B104KO5NNNC 100nF 0402'), '4.7u': ('C19666', 'CL10A475KO8NNNC 4.7uF 0603'),
    'TLV62569DBVR': ('C141836', 'TLV62569DBVR 2A buck SOT-23-5'), '2.2uH': ('C135262', 'SMNR4020-2.2UH 2.2uH 4x4'),
    '10u': ('C15850', 'CL21A106KAYNNNE 10uF 0805'), '22u': ('C45783', 'CL21A226MAQNNNE 22uF 0805'),
    '10k': ('C25804', '0603WAF1002T5E 10k 0603'), '2.2k': ('C4190', '0603WAF2201T5E 2.2k 0603'), '100k': ('C25803', '0603WAF1003T5E 100k 0603'),
    '10n': ('C57112', '0603B103K500NT 10nF 0603'), '1k x4': ('C20197', '4D03WGJ0102T5E 1k x4 0603'), '2N7002': ('C8545', '2N7002 SOT-23'),
    '680 x4': ('C12035', '4D03WGJ0681T5E 680R x4 0603'),
    'BAV99': ('C2500', 'BAV99,215 SOT-23'), 'B5819W': ('C8598', 'B5819W SOD-123'), 'TS-1187A': ('C318884', 'TS-1187A-B-A-B'),
    'TYPE-C-31-M-12': ('C165948', 'HRO TYPE-C-31-M-12 USB-C'), '27': ('C25100', '0402WGF270JTCE 27R 0402'), 'TF-01A': ('C91145', 'HRO TF-01A microSD'),
    'KT-0603R': ('C2286', 'KT-0603R red LED 0603'),
}
LCSC_CLASS = {code: 'Basic' for code, _ in LCSC.values()}
LCSC_CLASS.update({c_: 'Extended' for c_ in ('C42415655', 'C362368', 'C141836', 'C135262', 'C165948', 'C25100', 'C91145', 'C12035')})

if __name__ == '__main__':
    from collections import Counter
    nets = {}
    for ref, pins in NETS.items():
        for p, nn in pins.items():
            if nn: nets.setdefault(nn, []).append(f'{ref}.{p}')
    print(len(PARTS), 'parts', len(nets), 'nets')
    for nn, nodes in sorted(nets.items()):
        if len(nodes) < 2: print('  single-node net:', nn, nodes)
    print('parts without connections:', [r for r in PARTS if r not in NETS])
    placed = [r for r, v in PARTS.items() if v[2].split(' (')[0] in LCSC]
    types = Counter(PARTS[r][2].split(' (')[0] for r in placed)
    print('JLCPCB parts:', len(placed), 'in', len(types), 'types;', sum(1 for v in LCSC_CLASS.values() if v == 'Extended'), 'Extended')
    for side in 'FB': print(' ', side, sum(1 for r in placed if PARTS[r][4][3] == side), dict(Counter(PARTS[r][2].split(' (')[0] for r in placed if PARTS[r][4][3] == side)))
