"""famicart rev D: "real cartridge" partition -- separate PRG ROM, CHR ROM and mapper/expansion chips.

  U1  RP2350B   "PRG mapper / expansion chip": snoops the (level-shifted) CPU bus, drives the PRG flash bank lines
                 (A13-A25, 8 KB granularity, 64 MB), WRAM chip-select, IRQ, expansion audio (PWM), USB (J3) and the
                 flash programmer. Sends CHR/mirroring state to U2 over a 2-wire PIO link.
  U2  RP2350B   "CHR mapper": snoops the PPU bus, drives the CHR flash/RAM bank lines (A10-A25, 1 KB granularity),
                 CHR ROM/RAM select, CIRAM A10 (mirroring) and the 4-screen enable, MMC2/MMC4 latches, MMC3 A12 /
                 MMC5 scanline IRQ, USB (J4).
  U5  S29GL01GS PRG ROM: 1 Gbit parallel NOR, used as 64M x 8 (DQ0-7; DQ8-15 pulled up).
  U6  S29GL01GS CHR ROM: same part, 64 MB.
  U7  FM28V100  WRAM 128 KB F-RAM: non-volatile save RAM without a battery (banked 8 KB through PRG_A13-A16).
  U8  IS62WV5128 CHR RAM 512 KB (banked 1 KB through the CHR bank lines A10-A18; also holds 4-screen / ExRAM
                 nametables).
  The console bus (5 V) is level-shifted by 74LVC541/245 to a local 3.3 V bus shared by MCUs, flash and SRAM.
  4-layer board (F.Cu signal, In1 GND plane, In2 +3V3 plane, B.Cu signal), same 90 x 46.1 mm Famicom outline.
See docs/04_hardware.md (rev D section)."""

REV = 'rev D'
LAYERS = 4

PARTS = {}
def P(ref, lib, sym, val, fp, x, y, rot=0, side='F'): PARTS[ref] = (lib, sym, val, fp, (x, y, rot, side))
NETS = {}
def c(ref, pin, net): NETS.setdefault(ref, {})[str(pin)] = net

_cn = [0]; _rn = [0]
def cap(val, fp, x, y, rot=0, side='F', n1=None, n2='GND'):
    _cn[0] += 1; ref = f'C{_cn[0]}'; P(ref, 'Device', 'C', val, fp, x, y, rot, side)
    if n1: c(ref, 1, n1); c(ref, 2, n2)
    return ref
def res(val, fp, x, y, rot=0, side='F', n1=None, n2=None):
    _rn[0] += 1; ref = f'R{_rn[0]}'; P(ref, 'Device', 'R', val, fp, x, y, rot, side)
    if n1 is not None or n2 is not None: c(ref, 1, n1); c(ref, 2, n2)
    return ref
C0402 = 'Capacitor_SMD:C_0402_1005Metric'; C0603 = 'Capacitor_SMD:C_0603_1608Metric'; C0805 = 'Capacitor_SMD:C_0805_2012Metric'
R0402 = 'Resistor_SMD:R_0402_1005Metric'; R0603 = 'Resistor_SMD:R_0603_1608Metric'; RARR = 'Resistor_SMD:R_Array_Convex_4x0603'

# ------------------------------------------------------------------ card edge (console side nets)
P('J1', 'famicart', 'Famicom_CardEdge_60', 'Famicom 60-pin edge', 'famicart:Famicom_CardEdge_60', 45.0, 35.4)
J1 = {1:'GND',2:'CPU_A11',3:'CPU_A10',4:'CPU_A9',5:'CPU_A8',6:'CPU_A7',7:'CPU_A6',8:'CPU_A5',9:'CPU_A4',10:'CPU_A3',11:'CPU_A2',12:'CPU_A1',13:'CPU_A0',14:'CPU_RW',15:'nIRQ',16:'GND',
      17:'PPU_nRD',18:'CIRAM_A10',19:'PPU_A6',20:'PPU_A5',21:'PPU_A4',22:'PPU_A3',23:'PPU_A2',24:'PPU_A1',25:'PPU_A0',26:'PPU_D0',27:'PPU_D1',28:'PPU_D2',29:'PPU_D3',30:'+5V',
      31:'CART_PRESENT',32:'M2',33:'CPU_A12',34:'CPU_A13',35:'CPU_A14',36:'CPU_D7',37:'CPU_D6',38:'CPU_D5',39:'CPU_D4',40:'CPU_D3',41:'CPU_D2',42:'CPU_D1',43:'CPU_D0',44:'nROMSEL',
      45:'AUDIO_IN',46:'AUDIO_OUT',47:'PPU_nWR',48:'CIRAM_nCE',49:None,50:'PPU_A7',51:'PPU_A8',52:'PPU_A9',53:'PPU_A10',54:'PPU_A11',55:'PPU_A12',56:'PPU_A13',57:'PPU_D7',58:'PPU_D6',59:'PPU_D5',60:'PPU_D4'}
for p, nn in J1.items(): c('J1', p, nn)

# ------------------------------------------------------------------ the two RP2350B "mapper chips"
GPIO_PIN = {0:77,1:78,2:79,3:80,4:1,5:2,6:3,7:4,8:6,9:7,10:8,11:9,12:11,13:12,14:13,15:14,16:16,17:17,18:18,19:19,20:20,21:21,22:22,23:23,24:25,25:26,26:27,27:28,28:36,29:37,30:38,31:39,32:40,33:42,34:43,35:44,36:45,37:46,38:47,39:48,40:49,41:52,42:53,43:54,44:55,45:56,46:57,47:58}
GPIO_A = {}
for i in range(15): GPIO_A[i] = f'CA{i}'                 # local CPU address
for i in range(8):  GPIO_A[15 + i] = f'CD{i}'            # local CPU data
GPIO_A.update({23: 'CRW', 24: 'CM2', 25: 'CnROMSEL', 26: 'nDRIVE'})   # nDRIVE inside PIO0's GPIO window (side-set while driving data)
for i in range(13): GPIO_A[27 + i] = f'PRG_A{13 + i}'    # PRG flash / WRAM bank address A13-A25 (one contiguous masked write)
GPIO_A.update({40: 'WRAM_nCE', 41: 'nIRQ_A', 42: 'PWM', 43: 'LINK_CLK', 44: 'LINK_DATA', 45: 'LINK_B2A', 46: 'PRG_nWE', 47: 'ISOLATE'})
GPIO_B = {}
for i in range(14): GPIO_B[i] = f'PA{i}'                 # local PPU address
GPIO_B.update({14: 'PnRD', 15: 'PnWR'})
for i in range(16): GPIO_B[16 + i] = f'CHR_A{10 + i}'    # CHR flash / CHR RAM bank address A10-A25
GPIO_B.update({32: 'CHR_SEL', 33: 'nFOURSCR', 34: 'CIRAM_A10', 35: 'LED', 36: 'CHR_nWE', 37: 'LINK_CLK', 38: 'LINK_DATA', 39: 'LINK_B2A', 40: 'nIRQ_B', 41: 'nBRIDGE',
               42: 'BRIDGE_DIR', 43: 'CHR_RYBY'})        # bridge direction (1 = CPU->PPU data, 0 = read back), CHR flash RY/BY#
for g in range(44, 48): GPIO_B[g] = None                 # spare

def mcu(ref, s, x, y, gpio_net, mirror):
    """RP2350B + flash + crystal + regulator passives + BOOTSEL + USB series/CC. mirror=-1 flips the support parts in x."""
    m = mirror
    def X(dx): return x + m * dx
    P(ref, 'famicart', 'RP2350B', 'RP2350B', 'famicart:QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm', x, y)
    for g, net in gpio_net.items(): c(ref, GPIO_PIN[g], net)
    v11 = f'+1V1{s}'
    for p, nn in {70:f'QSPI{s}_SD3',71:f'QSPI{s}_SCLK',72:f'QSPI{s}_SD0',73:f'QSPI{s}_SD2',74:f'QSPI{s}_SD1',75:f'QSPI{s}_SS',30:f'XIN{s}',31:f'XOUT{s}',35:'RUN',33:f'SWCLK{s}',34:f'SWDIO{s}',
                  66:f'USB{s}_DM_R',67:f'USB{s}_DP_R',61:f'VREG{s}_AVDD',62:'GND',63:f'VREG{s}_LX',64:'+3V3',65:v11,69:'+3V3',68:'+3V3',59:'+3V3',81:'GND'}.items(): c(ref, p, nn)
    for p in (10, 32, 51): c(ref, p, v11)
    for p in (5, 15, 24, 29, 41, 50, 60, 76): c(ref, p, '+3V3')
    # QSPI flash (W25Q16, same pinout as W25Q128) + BOOTSEL
    fl = 'U3' if s == 'A' else 'U4'
    P(fl, 'Memory_Flash', 'W25Q128JVS', 'W25Q16JVSSIQ', 'Package_SO:SOIC-8_5.23x5.23mm_P1.27mm', X(-9), y - 9.5, 0 if m > 0 else 180)
    c(fl, 1, f'QSPI{s}_SS'); c(fl, 2, f'QSPI{s}_SD1'); c(fl, 3, f'QSPI{s}_SD2'); c(fl, 4, 'GND'); c(fl, 5, f'QSPI{s}_SD0'); c(fl, 6, f'QSPI{s}_SCLK'); c(fl, 7, f'QSPI{s}_SD3'); c(fl, 8, '+3V3')
    cap('100n', C0603, X(-8.5), y - 4.5, 0, 'F', '+3V3')
    res('10k', R0603, X(-2.5), y - 8.5, 0, 'F', f'QSPI{s}_SS', '+3V3')
    res('1k', R0603, X(-2.5), y - 11, 0, 'F', f'QSPI{s}_SS', f'BOOT{s}_SW')
    # crystal 12 MHz
    yref = 'Y1' if s == 'A' else 'Y2'
    P(yref, 'Device', 'Crystal_GND24', '12MHz ABM8-272-T3', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', X(11), y - 9)
    c(yref, 1, f'XIN{s}'); c(yref, 3, f'XOUT{s}_R'); c(yref, 2, 'GND'); c(yref, 4, 'GND')
    res('1k', R0402, X(14.5), y - 9, 90, 'F', f'XOUT{s}', f'XOUT{s}_R')
    cap('15p', C0402, X(7), y - 9, 90, 'F', f'XIN{s}'); cap('15p', C0402, X(13), y - 6.5, 0, 'F', f'XOUT{s}_R')
    # core regulator
    lref = 'L1' if s == 'A' else 'L2'
    P(lref, 'Device', 'L', '3.3uH AOTA-B201610S3R3', 'famicart:L_0806_2016Metric', X(11), y + 7)
    c(lref, 1, f'VREG{s}_LX'); c(lref, 2, v11)
    cap('4.7u', C0603, X(14), y + 7, 90, 'F', '+3V3'); cap('4.7u', C0603, X(8), y + 7, 90, 'F', v11)
    res('33', R0402, X(9), y + 9.5, 0, 'F', '+3V3', f'VREG{s}_AVDD'); cap('4.7u', C0603, X(11.5), y + 9.8, 0, 'F', f'VREG{s}_AVDD')
    # USB series resistors
    res('27', R0603, X(11), y - 4, 0, 'F', f'USB{s}_DM', f'USB{s}_DM_R'); res('27', R0603, X(11), y - 2, 0, 'F', f'USB{s}_DP', f'USB{s}_DP_R')
    # decoupling ring (front, outside the QFN pad ring)
    for dx, dy in ((-3.0, -6.6), (0, 6.3), (4.5, -6.3)): cap('100n', C0402, X(dx), y + dy, 0, 'F', v11)
    for dx, dy in ((-6.3, -2), (-6.3, 2), (6.3, -2), (6.3, 2), (-2.5, 6.3), (2.5, 6.3), (0, -6.3)): cap('100n', C0402, X(dx), y + dy, 0 if abs(dx) < 6 else 90, 'F', '+3V3')

mcu('U1', 'A', 17.0, 15.0, GPIO_A, +1)
mcu('U2', 'B', 73.0, 15.0, GPIO_B, -1)

# USB-C x2 (J3 -> U1, J4 -> U2), VBUS of either -> Schottky -> +5V rail
for J, s, x in (('J3', 'A', 38.0), ('J4', 'B', 52.0)):
    P(J, 'Connector', 'USB_C_Receptacle', f'USB-C {"PRG/mapper (U1)" if s == "A" else "CHR (U2)"} (HRO TYPE-C-31-M-12)', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', x, 4.3, 180)
    for pin in ('A4', 'A9', 'B4', 'B9'): c(J, pin, f'VBUS{s}')
    for pin in ('A1', 'A12', 'B1', 'B12', 'S1'): c(J, pin, 'GND')
    c(J, 'A5', f'CC{s}1'); c(J, 'B5', f'CC{s}2')
    for pin in ('A6', 'B6'): c(J, pin, f'USB{s}_DP')
    for pin in ('A7', 'B7'): c(J, pin, f'USB{s}_DM')
    for pin in ('A2', 'A3', 'A8', 'A10', 'A11', 'B2', 'B3', 'B8', 'B10', 'B11'): c(J, pin, None)
    res('5.1k', R0603, x - 2, 11.0, 0, 'F', f'CC{s}1', 'GND'); res('5.1k', R0603, x + 2, 11.0, 0, 'F', f'CC{s}2', 'GND')
P('D1', 'Device', 'D_Schottky', 'B5819W (VBUS A->+5V)', 'Diode_SMD:D_SOD-123', 38.0, 14.5, 90); c('D1', 2, 'VBUSA'); c('D1', 1, '+5V')
P('D2', 'Device', 'D_Schottky', 'B5819W (VBUS B->+5V)', 'Diode_SMD:D_SOD-123', 52.0, 14.5, 90); c('D2', 2, 'VBUSB'); c('D2', 1, '+5V')

# reset / BOOTSEL / debug
P('SW1', 'Switch', 'SW_Push', 'RESET', 'Button_Switch_SMD:SW_SPST_TL3342', 45.0, 15.0); c('SW1', 1, 'RUN'); c('SW1', 2, 'GND')
P('SW2', 'Switch', 'SW_Push', 'BOOTSEL A', 'Button_Switch_SMD:SW_SPST_TL3342', 14.0, 29.0); c('SW2', 1, 'BOOTA_SW'); c('SW2', 2, 'GND')
P('SW3', 'Switch', 'SW_Push', 'BOOTSEL B', 'Button_Switch_SMD:SW_SPST_TL3342', 76.0, 29.0); c('SW3', 1, 'BOOTB_SW'); c('SW3', 2, 'GND')
P('J2', 'Connector_Generic', 'Conn_01x02', 'RUN/GND', 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', 67.0, 33.5, 90); c('J2', 1, 'RUN'); c('J2', 2, 'GND')
P('J5', 'Connector_Generic', 'Conn_01x03', 'SWD A (SWCLK GND SWDIO)', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical', 7.7, 33.5, 270); c('J5', 1, 'SWCLKA'); c('J5', 2, 'GND'); c('J5', 3, 'SWDIOA')
P('J6', 'Connector_Generic', 'Conn_01x03', 'SWD B (SWCLK GND SWDIO)', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical', 82.3, 33.5, 90); c('J6', 1, 'SWCLKB'); c('J6', 2, 'GND'); c('J6', 3, 'SWDIOB')
res('10k', R0603, 45.0, 28.5, 90, 'F', 'RUN', '+3V3')

# 3.3 V regulator (AMS1117, SOT-223) fed from the console / USB +5V
P('U28', 'Regulator_Linear', 'AMS1117-3.3', 'AMS1117-3.3', 'Package_TO_SOT_SMD:SOT-223-3_TabPin2', 45.0, 23.0)
c('U28', 1, 'GND'); c('U28', 2, '+3V3'); c('U28', 3, '+5V')
cap('10u', C0805, 39.5, 23.0, 90, 'F', '+5V'); cap('10u', C0805, 50.5, 23.0, 90, 'F', '+3V3')

# audio: PWM -> 2-stage RC -> 4.7k -> AUDIO_OUT; console audio through 1k; JP1 bypass; JP2 CART_PRESENT
res('2.2k', R0603, 20.0, 30.0, 0, 'F', 'PWM', 'AF1'); res('2.2k', R0603, 23.0, 30.0, 0, 'F', 'AF1', 'AF2'); res('4.7k', R0603, 26.0, 30.0, 0, 'F', 'AF2', 'AUDIO_OUT')
cap('10n', C0603, 21.5, 32.5, 270, 'F', 'AF1'); cap('10n', C0603, 24.5, 32.5, 270, 'F', 'AF2')
res('1k', R0603, 29.0, 30.0, 90, 'F', 'AUDIO_IN', 'AUDIO_OUT')
res('10k', R0603, 34.0, 23.0, 90, 'F', 'nIRQ', '+5V')
P('JP1', 'Jumper', 'SolderJumper_2_Open', 'AUDIO bypass', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 31.0, 24.0, 0, 'B'); c('JP1', 1, 'AUDIO_IN'); c('JP1', 2, 'AUDIO_OUT')
P('JP2', 'Jumper', 'SolderJumper_2_Open', 'CART_PRESENT', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', 31.0, 27.2, 0, 'B'); c('JP2', 1, 'CART_PRESENT'); c('JP2', 2, '+5V')

# pull-ups / pull-downs so the bus logic is sane before the MCUs boot
P('RN1', 'Device', 'R_Pack04', '10k x4', RARR, 36.5, 28.5); P('RN2', 'Device', 'R_Pack04', '10k x4', RARR, 53.5, 28.5)
for rn, nets in (('RN1', ('WRAM_nCE', 'nDRIVE', 'PRG_nWE', 'nBRIDGE')), ('RN2', ('CHR_nWE', 'nFOURSCR', 'nIRQ_A', 'nIRQ_B'))):
    for i, nn in enumerate(nets): c(rn, 1 + i, nn); c(rn, 8 - i, '+3V3')
res('10k', R0603, 36.5, 23.0, 90, 'F', 'ISOLATE', 'GND'); res('10k', R0603, 56.0, 23.0, 90, 'F', 'CHR_SEL', 'GND')

# ------------------------------------------------------------------ memories (back side)
GL = {1:'A23',2:'A22',3:'A15',4:'A14',5:'A13',6:'A12',7:'A11',8:'A10',9:'A9',10:'A8',11:'A19',12:'A20',13:'WE#',14:'RESET#',15:'A21',16:'WP#',17:'RY/BY#',18:'A18',19:'A17',20:'A7',21:'A6',22:'A5',
      23:'A4',24:'A3',25:'A2',26:'A1',27:'RFU',28:'DNU',29:'VIO',30:'RFU',31:'A0',32:'CE#',33:'VSS',34:'OE#',35:'DQ0',36:'DQ8',37:'DQ1',38:'DQ9',39:'DQ2',40:'DQ10',41:'DQ3',42:'DQ11',43:'VCC',
      44:'DQ4',45:'DQ12',46:'DQ5',47:'DQ13',48:'DQ6',49:'DQ14',50:'DQ7',51:'DQ15',52:'VSS',53:'RFU',54:'A16',55:'A25',56:'A24'}
def flash(ref, x, y, addr_lo, addr_hi, data, ce, oe, we, rn_x):
    P(ref, 'famicart', 'S29GL01GS_TSOP56', 'S29GL01GS 1Gbit NOR (x8 use)', 'Package_SO:TSOP-I-56_18.4x14mm_P0.5mm', x, y, 0, 'B')
    for p, nm in GL.items():
        if nm.startswith('A') and nm[1:].isdigit():
            a = int(nm[1:]); c(ref, p, addr_lo[a] if a < len(addr_lo) else addr_hi[a - len(addr_lo)])
        elif nm.startswith('DQ'):
            d = int(nm[2:]); c(ref, p, data[d] if d < 8 else f'{ref}_DQ{d}')
        else:
            c(ref, p, {'WE#': we, 'RESET#': 'RUN', 'WP#': '+3V3', 'RY/BY#': ('CHR_RYBY' if ref == 'U6' else None), 'RFU': None, 'DNU': None, 'VIO': '+3V3', 'VCC': '+3V3', 'VSS': 'GND', 'CE#': ce, 'OE#': oe}[nm])
    # DQ8-15 pull-ups (x16 device programmed with 0xFF in the upper byte)
    for k in range(2):
        rn = f'RN{3 + 2 * (ref == "U6") + k}'; P(rn, 'Device', 'R_Pack04', '10k x4', RARR, rn_x, y - 1.5 + 5 * k, 90, 'B')
        for i in range(4): c(rn, 1 + i, f'{ref}_DQ{8 + 4 * k + i}'); c(rn, 8 - i, '+3V3')
    cap('100n', C0402, x - 4, y + 8.3, 0, 'B', '+3V3'); cap('1u', C0603, x + 4, y + 8.3, 0, 'B', '+3V3')
CA = [f'CA{i}' for i in range(15)]; CD = [f'CD{i}' for i in range(8)]
PA = [f'PA{i}' for i in range(14)]; PD = [f'PD{i}' for i in range(8)]
PRG_HI = [f'PRG_A{13 + i}' for i in range(13)]; CHR_HI = [f'CHR_A{10 + i}' for i in range(16)]
flash('U5', 20.0, 12.0, CA[:13], PRG_HI, CD, 'CnROMSEL', 'CRWn', 'PRG_nWE', 33.0)
flash('U6', 70.0, 12.0, PA[:10], CHR_HI, PD, 'CHR_ROM_nCE', 'PnRD', 'CHR_nWE', 56.8)

SR = {1:'A11',2:'A9',3:'A8',4:'A13',5:'WE#',6:'A18',7:'A15',8:'VDD',9:'A17',10:'A16',11:'A14',12:'A12',13:'A7',14:'A6',15:'A5',16:'A4',17:'A3',18:'A2',19:'A1',20:'A0',
      21:'IO0',22:'IO1',23:'IO2',24:'GND',25:'IO3',26:'IO4',27:'IO5',28:'IO6',29:'IO7',30:'CS#',31:'A10',32:'OE#'}
def sram(ref, x, y, addr_lo, addr_hi, data, cs, oe, we):
    P(ref, 'famicart', 'IS62WV5128_sTSOP32', 'IS62WV5128 512Kx8 SRAM', 'Package_SO:TSOP-I-32_11.8x8mm_P0.5mm', x, y, 0, 'B')
    for p, nm in SR.items():
        if nm.startswith('A'): a = int(nm[1:]); c(ref, p, addr_lo[a] if a < len(addr_lo) else addr_hi[a - len(addr_lo)])
        elif nm.startswith('IO'): c(ref, p, data[int(nm[2:])])
        else: c(ref, p, {'WE#': we, 'CS#': cs, 'OE#': oe, 'VDD': '+3V3', 'GND': 'GND'}[nm])
    cap('100n', C0402, x + 8.5, y, 90, 'B', '+3V3')
# WRAM = 128 KB F-RAM (non-volatile, no battery, SRAM-compatible timing; 16 x 8 KB banks on PRG_A13-A16)
FM = {1:'A11',2:'A9',3:'A8',4:'A13',5:'WE#',6:'CE2',7:'A15',8:'VDD',9:'NC',10:'A16',11:'A14',12:'A12',13:'A7',14:'A6',15:'A5',16:'A4',17:'A3',18:'A2',19:'A1',20:'A0',
      21:'DQ0',22:'DQ1',23:'DQ2',24:'VSS',25:'DQ3',26:'DQ4',27:'DQ5',28:'DQ6',29:'DQ7',30:'CE1#',31:'A10',32:'OE#'}
P('U7', 'famicart', 'FM28V100_TSOP32', 'FM28V100 128Kx8 F-RAM (WRAM/save)', 'Package_SO:TSOP-I-32_11.8x8mm_P0.5mm', 20.0, 26.0, 0, 'B')
for p, nm in FM.items():
    if nm.startswith('A') and nm[1:].isdigit(): a = int(nm[1:]); c('U7', p, CA[a] if a < 13 else PRG_HI[a - 13])
    elif nm.startswith('DQ'): c('U7', p, CD[int(nm[2:])])
    else: c('U7', p, {'WE#': 'WRAM_nWE', 'CE1#': 'WRAM_nCE', 'CE2': '+3V3', 'OE#': 'CRWn', 'VDD': '+3V3', 'VSS': 'GND', 'NC': None}[nm])
cap('100n', C0402, 28.5, 26.0, 90, 'B', '+3V3')
sram('U8', 70.0, 26.0, PA[:10], CHR_HI, PD, 'CHR_RAM_nCE', 'PnRD', 'PnWR')

# ------------------------------------------------------------------ bus level shifters and glue (back side)
TSSOP20 = 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm'; TSSOP16 = 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm'; TSSOP14 = 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm'; SOT235 = 'Package_TO_SOT_SMD:SOT-23-5'; SOT236 = 'Package_TO_SOT_SMD:SOT-23-6'
LX, RX = 4.5, 85.5; SROWS = (8.5, 17.9, 27.3); SCAP = (13.2, 22.6, 32.0)      # edge strips (3 chips each)
COLS = (41.4, 48.8); ROWS = (13.0, 22.4); CY1 = 17.7                         # centre block (2 x 2)
def logic(ref, lib, sym, val, fp, x, y, cap_xy):
    P(ref, lib, sym, val, fp, x, y, 90, 'B'); cap('100n', C0402, cap_xy[0], cap_xy[1], 0, 'B', '+3V3')
def buf541(ref, inputs, outputs, oe, x, y, cap_xy):
    logic(ref, '74xx', '74LS541', '74LVC541 ' + ref, TSSOP20, x, y, cap_xy)
    c(ref, 1, oe); c(ref, 19, oe); c(ref, 10, 'GND'); c(ref, 20, '+3V3')
    for i in range(8): c(ref, 2 + i, inputs[i] if i < len(inputs) else 'GND'); c(ref, 18 - i, outputs[i] if i < len(outputs) else None)
def xcvr245(ref, a, b, dir_, oe, x, y, cap_xy, val):
    logic(ref, '74xx', '74HC245', val, TSSOP20, x, y, cap_xy)
    c(ref, 1, dir_); c(ref, 19, oe); c(ref, 10, 'GND'); c(ref, 20, '+3V3')
    for i in range(8): c(ref, 2 + i, a[i]); c(ref, 18 - i, b[i])
# CPU side
buf541('U9',  [f'CPU_A{i}' for i in range(8)], CA[:8], 'ISOLATE', LX, SROWS[0], (LX, SCAP[0]))
buf541('U10', [f'CPU_A{i}' for i in range(8, 15)] + ['CPU_RW'], CA[8:15] + ['CRW'], 'ISOLATE', LX, SROWS[1], (LX, SCAP[1]))
buf541('U11', ['M2', 'nROMSEL'], ['CM2', 'CnROMSEL'], 'ISOLATE', LX, SROWS[2], (LX, SCAP[2]))
xcvr245('U12', [f'CPU_D{i}' for i in range(8)], CD, 'CRWn', 'CD_nOE', COLS[0], ROWS[0], (COLS[0] - 1.8, CY1), '74LVC245 CPU data (console<->local)')
xcvr245('U24', CD, PD, 'BRIDGE_DIR', 'nBRIDGE', COLS[1], ROWS[0], (COLS[1] - 1.8, CY1), '74LVC245 CPU->PPU data bridge (CHR flash programming)')
logic('U22', '74xx', '74LS139', '74LVC139 CHR ROM/RAM select', TSSOP16, COLS[0], ROWS[1], (COLS[0] + 1.8, CY1))
c('U22', 1, 'nCART_ACC'); c('U22', 2, 'CHR_SEL'); c('U22', 3, 'GND'); c('U22', 4, 'CHR_ROM_nCE'); c('U22', 5, 'CHR_RAM_nCE'); c('U22', 6, None); c('U22', 7, None)
c('U22', 15, '+3V3'); c('U22', 14, 'GND'); c('U22', 13, 'GND'); c('U22', 12, None); c('U22', 11, None); c('U22', 10, None); c('U22', 9, None); c('U22', 8, 'GND'); c('U22', 16, '+3V3')
# PPU side
buf541('U17', [f'PPU_A{i}' for i in range(8)], PA[:8], 'ISOLATE', RX, SROWS[0], (RX, SCAP[0]))
buf541('U18', [f'PPU_A{i}' for i in range(8, 14)] + ['PPU_nRD', 'PPU_nWR'], PA[8:14] + ['PnRD', 'PnWR'], 'ISOLATE', RX, SROWS[1], (RX, SCAP[1]))
xcvr245('U19', [f'PPU_D{i}' for i in range(8)], PD, 'PnRD', 'PD_nOE', RX, SROWS[2], (RX, SCAP[2]), '74LVC245 PPU data (console<->local)')
logic('U20', '74xx', '74HC00', '74LVC00 PPU access / CIRAM glue', TSSOP14, COLS[1], ROWS[1], (COLS[1] + 1.8, CY1))
c('U20', 1, 'PnRD'); c('U20', 2, 'PnWR'); c('U20', 3, 'PPU_ACC')            # PPU_ACC = /RD NAND /WR (high during any PPU access)
c('U20', 4, 'PA13'); c('U20', 5, 'nFOURSCR'); c('U20', 6, 'CIRAM_nCE')       # CIRAM /CE = NAND(A13, /4SCR): normal = /A13, 4-screen/ExRAM = disabled
c('U20', 9, 'PPU_ACC'); c('U20', 10, 'CIRAM_nCE'); c('U20', 8, 'nCART_ACC')  # cart responds when accessed and CIRAM is not selected
c('U20', 12, 'GND'); c('U20', 13, 'GND'); c('U20', 11, None); c('U20', 7, 'GND'); c('U20', 14, '+3V3')
# single gates (back, bottom row)
G = [('U13', '74LVC1G11', SOT236, 'AND3: CPU data enable', {1: 'CnROMSEL', 3: 'WRAM_nCE', 6: 'nDRIVE', 4: 'CD_EN3', 2: 'GND', 5: '+3V3'}),
     ('U14', '74LVC1G32', SOT235, 'OR: CPU 245 /OE', {1: 'CD_EN3', 2: 'ISOLATE', 4: 'CD_nOE', 3: 'GND', 5: '+3V3'}),
     ('U15', '74LVC1G04', SOT235, 'INV: R/W', {2: 'CRW', 4: 'CRWn', 3: 'GND', 5: '+3V3'}),
     ('U16', '74LVC1G00', SOT235, 'NAND: WRAM /WE', {1: 'CM2', 2: 'CRWn', 4: 'WRAM_nWE', 3: 'GND', 5: '+3V3'}),
     ('U21', '74LVC1G32', SOT235, 'OR: PPU 245 /OE', {1: 'nCART_ACC', 2: 'ISOLATE', 4: 'PD_nOE', 3: 'GND', 5: '+3V3'}),
     ('U26', '74LVC1G07', SOT235, 'OD: /IRQ A', {2: 'nIRQ_A', 4: 'nIRQ', 3: 'GND', 5: '+3V3'}),
     ('U27', '74LVC1G07', SOT235, 'OD: /IRQ B', {2: 'nIRQ_B', 4: 'nIRQ', 3: 'GND', 5: '+3V3'})]
for i, (ref, sym, fp, val, pins) in enumerate(G):
    x = 34.0 + 4.6 * i      # front, bottom row; decoupling caps on the back directly behind each gate
    P(ref, '74xGxx', sym, f'{sym} {val}', fp, x, 32.5, 0, 'F'); cap('100n', C0402, x, 32.8, 0, 'B', '+3V3')
    for p, nn in pins.items(): c(ref, p, nn)

# PRG bank-line pull-ups: before the MCUs boot (and whenever U1 is held in reset) every CPU window maps to the
# top 8 KB bank of the PRG flash ("boot bank"), which holds a stub that parks the console in RAM until U1 is ready.
for i in range(3):
    rn = f'RN{7 + i}'; P(rn, 'Device', 'R_Pack04', '10k x4', RARR, 31.5 + 3.5 * (i % 2), 14.3 + 4.1 * (i // 2))
    for k in range(4): c(rn, 1 + k, f'PRG_A{13 + 4 * i + k}'); c(rn, 8 - k, '+3V3')
res('10k', R0603, 35.0, 18.6, 90, 'F', 'PRG_A25', '+3V3')

res('10k', R0603, 66.0, 27.5, 90, 'F', 'BRIDGE_DIR', '+3V3'); res('10k', R0603, 69.0, 27.5, 90, 'F', 'CHR_RYBY', '+3V3')

# status LED on U2 GPIO35
P('D3', 'Device', 'LED', 'green 0603', 'LED_SMD:LED_0603_1608Metric', 58.0, 30.0, 0, 'F'); c('D3', 2, 'LED_A'); c('D3', 1, 'GND')
res('1k', R0603, 61.0, 30.0, 0, 'F', 'LED', 'LED_A')

POWER_NETS = {'+5V', '+3V3', '+1V1A', '+1V1B', 'GND', 'VBUSA', 'VBUSB'}

if __name__ == '__main__':
    nets = {}
    for ref, pins in NETS.items():
        for p, nn in pins.items():
            if nn: nets.setdefault(nn, []).append(f'{ref}.{p}')
    print(len(PARTS), 'parts', len(nets), 'nets')
    for nn, nodes in sorted(nets.items()):
        if len(nodes) < 2: print('  single-node net:', nn, nodes)
    print('parts without connections:', [r for r in PARTS if r not in NETS])
