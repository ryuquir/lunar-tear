"""famicart rev C: bare RP2350B (bus + mappers, 48 GPIO, 5 V-tolerant) + Seeed XIAO RP2040 (expansion-audio synth,
status LED, second USB). Same 90 x 46.1 mm Famicom outline as rev B. See docs/04_hardware.md (rev C section)."""

REV = 'rev C'

PARTS = {
 # ref: (lib, symbol, value, footprint, (x, y, rot, side))
 'J1':  ('famicart', 'Famicom_CardEdge_60', 'Famicom 60-pin edge', 'famicart:Famicom_CardEdge_60', (45.0, 35.4, 0, 'F')),
 'U1':  ('famicart', 'RP2350B', 'RP2350B', 'famicart:QFN-80-1EP_10x10mm_P0.4mm_EP3.4x3.4mm', (45.0, 16.0, 0, 'F')),
 'U2':  ('Memory_Flash', 'W25Q128JVS', 'W25Q128JVSIQ', 'Package_SO:SOIC-8_5.23x5.23mm_P1.27mm', (36.0, 6.5, 0, 'F')),
 'U3':  ('Regulator_Linear', 'AP2112K-3.3', 'AP2112K-3.3', 'Package_TO_SOT_SMD:SOT-23-5', (84.0, 12.5, 0, 'F')),
 'U4':  ('74xx', '74LS541', '74LVC541 (PPU A0-7)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (62.0, 30.5, 90, 'F')),
 'U5':  ('74xx', '74HC245', '74LVC245 (PPU D)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (71.0, 30.5, 90, 'F')),
 'U6':  ('74xGxx', '74LVC1G08', '74LVC1G08 (/PPUACC)', 'Package_TO_SOT_SMD:SOT-23-5', (80.0, 30.5, 0, 'F')),
 'U7':  ('74xGxx', '74LVC1G04', '74LVC1G04 (OE inv)', 'Package_TO_SOT_SMD:SOT-23-5', (84.0, 25.5, 0, 'F')),
 'U8':  ('famicart', 'XIAO-RP2040', 'Seeed XIAO RP2040', 'famicart:XIAO-RP2040-SMD', (14.0, 11.5, 0, 'F')),
 'Y1':  ('Device', 'Crystal_GND24', '12MHz ABM8-272-T3', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', (56.0, 7.0, 0, 'F')),
 'L1':  ('Device', 'L', '3.3uH AOTA-B201610S3R3', 'famicart:L_0806_2016Metric', (56.0, 23.0, 0, 'F')),
 'J3':  ('Connector', 'USB_C_Receptacle', 'USB-C DATA (HRO TYPE-C-31-M-12)', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', (68.0, 4.3, 180, 'F')),
 'J4':  ('Connector', 'USB_C_Receptacle', 'USB-C RP2350 (optional, DNP)', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', (84.0, 4.3, 180, 'F')),
 'J2':  ('Connector_Generic', 'Conn_01x02', 'RUN/GND', 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', (87.5, 30.0, 0, 'F')),
 'J5':  ('Connector_Generic', 'Conn_01x03', 'SWD (SWCLK GND SWDIO)', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical', (6.0, 34.0, 90, 'F')),
 'SW1': ('Switch', 'SW_Push', 'RESET', 'Button_Switch_SMD:SW_SPST_TL3342', (76.0, 20.0, 0, 'F')),
 'SW2': ('Switch', 'SW_Push', 'BOOTSEL', 'Button_Switch_SMD:SW_SPST_TL3342', (31.0, 15.5, 0, 'F')),
 # audio (XIAO PWM -> RC -> mix)
 'R1':  ('Device', 'R', '2.2k', 'Resistor_SMD:R_0603_1608Metric', (4.0, 24.0, 90, 'F')),
 'R2':  ('Device', 'R', '2.2k', 'Resistor_SMD:R_0603_1608Metric', (7.0, 24.0, 90, 'F')),
 'R3':  ('Device', 'R', '4.7k', 'Resistor_SMD:R_0603_1608Metric', (10.0, 24.0, 90, 'F')),
 'R4':  ('Device', 'R', '1k',   'Resistor_SMD:R_0603_1608Metric', (13.0, 24.0, 90, 'F')),
 'C1':  ('Device', 'C', '10n',  'Capacitor_SMD:C_0603_1608Metric', (4.0, 27.0, 90, 'F')),
 'C2':  ('Device', 'C', '10n',  'Capacitor_SMD:C_0603_1608Metric', (7.0, 27.0, 90, 'F')),
 # misc R
 'R5':  ('Device', 'R', '10k',  'Resistor_SMD:R_0603_1608Metric', (16.0, 24.0, 90, 'F')),   # /IRQ pull-up to +5V
 'R6':  ('Device', 'R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', (64.0, 11.5, 0, 'F')),     # J3 CC1
 'R7':  ('Device', 'R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', (72.0, 11.5, 0, 'F')),     # J3 CC2
 'R8':  ('Device', 'R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', (80.0, 9.5, 0, 'B')),     # J4 CC1
 'R9':  ('Device', 'R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', (88.0, 9.5, 0, 'B')),     # J4 CC2
 'R10': ('Device', 'R', '27',   'Resistor_SMD:R_0603_1608Metric', (56.0, 12.0, 0, 'F')),    # USB_DM series
 'R11': ('Device', 'R', '27',   'Resistor_SMD:R_0603_1608Metric', (56.0, 14.0, 0, 'F')),    # USB_DP series
 'R12': ('Device', 'R', '33',   'Resistor_SMD:R_0402_1005Metric', (54.0, 25.5, 0, 'F')),    # VREG_AVDD filter
 'R13': ('Device', 'R', '1k',   'Resistor_SMD:R_0603_1608Metric', (42.5, 7.5, 0, 'F')),    # BOOTSEL series
 'R14': ('Device', 'R', '10k',  'Resistor_SMD:R_0603_1608Metric', (42.5, 5.0, 0, 'F')),    # QSPI_SS pull-up
 'R15': ('Device', 'R', '1k',   'Resistor_SMD:R_0402_1005Metric', (59.5, 7.0, 90, 'F')),    # XOUT series
 # regulator / crystal caps
 'C3':  ('Device', 'C', '4.7u', 'Capacitor_SMD:C_0603_1608Metric', (59.0, 23.0, 90, 'F')),  # VREG_VIN
 'C4':  ('Device', 'C', '4.7u', 'Capacitor_SMD:C_0603_1608Metric', (53.0, 23.0, 90, 'F')),  # 1V1 (VREG_FB)
 'C5':  ('Device', 'C', '4.7u', 'Capacitor_SMD:C_0603_1608Metric', (56.5, 25.8, 0, 'F')),   # VREG_AVDD
 'C6':  ('Device', 'C', '15p',  'Capacitor_SMD:C_0402_1005Metric', (52.0, 7.0, 90, 'F')),
 'C7':  ('Device', 'C', '15p',  'Capacitor_SMD:C_0402_1005Metric', (58.0, 9.5, 0, 'F')),
 'C8':  ('Device', 'C', '10u',  'Capacitor_SMD:C_0805_2012Metric', (84.0, 15.5, 0, 'F')),   # +5V bulk
 'C9':  ('Device', 'C', '10u',  'Capacitor_SMD:C_0805_2012Metric', (84.0, 18.0, 0, 'F')),   # +3V3 bulk
 'C10': ('Device', 'C', '100n', 'Capacitor_SMD:C_0603_1608Metric', (37.0, 12.5, 0, 'F')),   # flash
 # jumpers
 'D1':  ('Device', 'D_Schottky', 'B5819W (VBUS->+5V)', 'Diode_SMD:D_SOD-123', (84.0, 21.0, 0, 'F')),
 'D2':  ('Device', 'D_Schottky', 'B5819W (+5V->XIAO)', 'Diode_SMD:D_SOD-123', (20.0, 24.0, 90, 'F')),
 'JP1': ('Jumper', 'SolderJumper_2_Open', 'AUDIO bypass', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', (11.0, 28.0, 0, 'B')),
 'JP2': ('Jumper', 'SolderJumper_2_Open', 'CART_PRESENT', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', (16.0, 28.0, 0, 'B')),
}
# RP2350 decoupling (0402, back side under the chip), DVDD x3 and IOVDD/others x7
DEC_1V1 = [(41.5, 11.0), (45.0, 21.5), (49.5, 11.0)]
DEC_3V3 = [(39.5, 14.0), (39.5, 18.0), (50.5, 14.0), (50.5, 18.0), (43.0, 21.5), (47.0, 21.5), (45.0, 10.5)]
DECOUPLE_REF = {}
n = 11
for x, y in DEC_1V1: PARTS[f'C{n}'] = ('Device', 'C', '100n', 'Capacitor_SMD:C_0402_1005Metric', (x, y, 0, 'B')); n += 1
for x, y in DEC_3V3: PARTS[f'C{n}'] = ('Device', 'C', '100n', 'Capacitor_SMD:C_0402_1005Metric', (x, y, 0, 'B')); n += 1
# logic IC decoupling behind U4..U7
for ic in ('U4', 'U5', 'U6', 'U7'):
    x, y, _, _ = PARTS[ic][4]
    PARTS[f'C{n}'] = ('Device', 'C', '100n', 'Capacitor_SMD:C_0603_1608Metric', (x, y, 90, 'B')); DECOUPLE_REF[ic] = f'C{n}'; n += 1
# LDO in/out 1uF
PARTS[f'C{n}'] = ('Device', 'C', '1u', 'Capacitor_SMD:C_0603_1608Metric', (84.0, 12.0, 0, 'B')); C_LDO_IN = f'C{n}'; n += 1
PARTS[f'C{n}'] = ('Device', 'C', '1u', 'Capacitor_SMD:C_0603_1608Metric', (84.0, 13.6, 0, 'B')); C_LDO_OUT = f'C{n}'; n += 1

NETS = {}
def c(ref, pin, net): NETS.setdefault(ref, {})[str(pin)] = net

J1 = {1:'GND',2:'CPU_A11',3:'CPU_A10',4:'CPU_A9',5:'CPU_A8',6:'CPU_A7',7:'CPU_A6',8:'CPU_A5',9:'CPU_A4',10:'CPU_A3',11:'CPU_A2',12:'CPU_A1',13:'CPU_A0',14:'CPU_RW',15:'nIRQ',16:'GND',
      17:'PPU_nRD',18:'CIRAM_A10',19:'PPU_A6',20:'PPU_A5',21:'PPU_A4',22:'PPU_A3',23:'PPU_A2',24:'PPU_A1',25:'PPU_A0',26:'PPU_D0',27:'PPU_D1',28:'PPU_D2',29:'PPU_D3',30:'+5V',
      31:'CART_PRESENT',32:'M2',33:'CPU_A12',34:'CPU_A13',35:'CPU_A14',36:'CPU_D7',37:'CPU_D6',38:'CPU_D5',39:'CPU_D4',40:'CPU_D3',41:'CPU_D2',42:'CPU_D1',43:'CPU_D0',44:'nROMSEL',
      45:'AUDIO_IN',46:'AUDIO_OUT',47:'PPU_nWR',48:'CIRAM_nCE',49:None,50:'PPU_A7',51:'PPU_A8',52:'PPU_A9',53:'PPU_A10',54:'PPU_A11',55:'PPU_A12',56:'PPU_A13',57:'PPU_D7',58:'PPU_D6',59:'PPU_D5',60:'PPU_D4'}
for p, nn in J1.items(): c('J1', p, nn)

# ---- RP2350B GPIO plan (all 48 used; see src/pico/board_rp2350b.h) ----
GPIO_PIN = {0:77,1:78,2:79,3:80,4:1,5:2,6:3,7:4,8:6,9:7,10:8,11:9,12:11,13:12,14:13,15:14,16:16,17:17,18:18,19:19,20:20,21:21,22:22,23:23,24:25,25:26,26:27,27:28,28:36,29:37,30:38,31:39,32:40,33:42,34:43,35:44,36:45,37:46,38:47,39:48,40:49,41:52,42:53,43:54,44:55,45:56,46:57,47:58}
GPIO_NET = {}
for i in range(15): GPIO_NET[i] = f'CPU_A{i}'
for i in range(8):  GPIO_NET[15 + i] = f'CPU_D{i}'
GPIO_NET.update({23: 'CPU_RW', 24: 'M2', 25: 'nROMSEL', 26: 'nIRQ', 27: 'CIRAM_nCE', 28: 'UART_TX', 29: 'UART_RX'})   # 28/29 = hardware UART0
for i in range(8):  GPIO_NET[30 + i] = f'PPUP{i}'
for i in range(6):  GPIO_NET[38 + i] = f'PPU_A{8 + i}'
GPIO_NET.update({44: 'nPPUACC', 45: 'PPU_nRD', 46: 'PPU_SEL', 47: 'CIRAM_A10'})
for g, net in GPIO_NET.items(): c('U1', GPIO_PIN[g], net)
for p, nn in {70:'QSPI_SD3',71:'QSPI_SCLK',72:'QSPI_SD0',73:'QSPI_SD2',74:'QSPI_SD1',75:'QSPI_SS',30:'XIN',31:'XOUT',35:'RUN',33:'SWCLK',34:'SWDIO',66:'USB_DM_R',67:'USB_DP_R',
              61:'VREG_AVDD',62:'GND',63:'VREG_LX',64:'+3V3',65:'+1V1',69:'+3V3',68:'+3V3',59:'+3V3',81:'GND'}.items(): c('U1', p, nn)
for p in (10, 32, 51): c('U1', p, '+1V1')
for p in (5, 15, 24, 29, 41, 50, 60, 76): c('U1', p, '+3V3')
# flash
c('U2', 1, 'QSPI_SS'); c('U2', 2, 'QSPI_SD1'); c('U2', 3, 'QSPI_SD2'); c('U2', 4, 'GND'); c('U2', 5, 'QSPI_SD0'); c('U2', 6, 'QSPI_SCLK'); c('U2', 7, 'QSPI_SD3'); c('U2', 8, '+3V3')
c('C10', 1, '+3V3'); c('C10', 2, 'GND')
c('R14', 1, 'QSPI_SS'); c('R14', 2, '+3V3'); c('R13', 1, 'QSPI_SS'); c('R13', 2, 'BOOTSEL_SW'); c('SW2', 1, 'BOOTSEL_SW'); c('SW2', 2, 'GND')
# crystal: XIN - Y1 - XOUT via 1k
c('Y1', 1, 'XIN'); c('Y1', 3, 'XOUT_R'); c('Y1', 2, 'GND'); c('Y1', 4, 'GND'); c('R15', 1, 'XOUT'); c('R15', 2, 'XOUT_R')
c('C6', 1, 'XIN'); c('C6', 2, 'GND'); c('C7', 1, 'XOUT_R'); c('C7', 2, 'GND')
# regulator
c('L1', 1, 'VREG_LX'); c('L1', 2, '+1V1'); c('C3', 1, '+3V3'); c('C3', 2, 'GND'); c('C4', 1, '+1V1'); c('C4', 2, 'GND')
c('R12', 1, '+3V3'); c('R12', 2, 'VREG_AVDD'); c('C5', 1, 'VREG_AVDD'); c('C5', 2, 'GND')
for i, (x, y) in enumerate(DEC_1V1): c(f'C{11 + i}', 1, '+1V1'); c(f'C{11 + i}', 2, 'GND')
for i, (x, y) in enumerate(DEC_3V3): c(f'C{14 + i}', 1, '+3V3'); c(f'C{14 + i}', 2, 'GND')
# LDO 5V -> 3V3
c('U3', 1, '+5V'); c('U3', 2, 'GND'); c('U3', 3, '+5V'); c('U3', 4, None); c('U3', 5, '+3V3')
c(C_LDO_IN, 1, '+5V'); c(C_LDO_IN, 2, 'GND'); c(C_LDO_OUT, 1, '+3V3'); c(C_LDO_OUT, 2, 'GND'); c('C8', 1, '+5V'); c('C8', 2, 'GND'); c('C9', 1, '+3V3'); c('C9', 2, 'GND')
# USB: J3 (DATA, edge) and J4 (optional) in parallel -> 27R -> chip
for J, (cc1, cc2) in (('J3', ('CC1', 'CC2')), ('J4', ('CC3', 'CC4'))):
    for pin in ('A4', 'A9', 'B4', 'B9'): c(J, pin, 'VBUS')
    for pin in ('A1', 'A12', 'B1', 'B12', 'S1'): c(J, pin, 'GND')
    c(J, 'A5', cc1); c(J, 'B5', cc2)
    for pin in ('A6', 'B6'): c(J, pin, 'USB_DP')
    for pin in ('A7', 'B7'): c(J, pin, 'USB_DM')
    for pin in ('A2', 'A3', 'A8', 'A10', 'A11', 'B2', 'B3', 'B8', 'B10', 'B11'): c(J, pin, None)
c('R6', 1, 'CC1'); c('R6', 2, 'GND'); c('R7', 1, 'CC2'); c('R7', 2, 'GND'); c('R8', 1, 'CC3'); c('R8', 2, 'GND'); c('R9', 1, 'CC4'); c('R9', 2, 'GND')
c('R10', 1, 'USB_DM'); c('R10', 2, 'USB_DM_R'); c('R11', 1, 'USB_DP'); c('R11', 2, 'USB_DP_R')
c('R5', 1, 'nIRQ'); c('R5', 2, '+5V')
# PPU shared port: U4 (A0-7 buffer, /OE = PPU_SEL), U5 (data, /OE = /PPU_SEL via U7, DIR = PPU_nRD, A side = console)
def buf541(ref, inputs, outputs, oe):
    c(ref, 1, oe); c(ref, 19, oe); c(ref, 10, 'GND'); c(ref, 20, '+3V3')
    for i in range(8): c(ref, 2 + i, inputs[i]); c(ref, 18 - i, outputs[i])
PPUP = ['PPUP%d' % i for i in range(8)]
buf541('U4', ['PPU_A%d' % i for i in range(8)], PPUP, 'PPU_SEL')
c('U5', 1, 'PPU_nRD'); c('U5', 19, 'PPU_nSEL'); c('U5', 10, 'GND'); c('U5', 20, '+3V3')
for i in range(8): c('U5', 2 + i, 'PPU_D%d' % i); c('U5', 18 - i, PPUP[i])
c('U6', 1, 'PPU_nRD'); c('U6', 2, 'PPU_nWR'); c('U6', 3, 'GND'); c('U6', 4, 'nPPUACC'); c('U6', 5, '+3V3')
c('U7', 2, 'PPU_SEL'); c('U7', 4, 'PPU_nSEL'); c('U7', 3, 'GND'); c('U7', 5, '+3V3')
for ic, cref in DECOUPLE_REF.items(): c(cref, 1, '+3V3'); c(cref, 2, 'GND')
# XIAO RP2040: UART link, audio PWM, power from +5V, reset together with RP2350B
c('U8', 7, 'UART_RX'); c('U8', 8, 'UART_TX')        # XIAO TX(GPIO0) -> RP2350 RX ; XIAO RX(GPIO1) <- RP2350 TX
c('U8', 1, 'PWM')                                   # D0/GPIO26 audio PWM
c('U8', 14, 'XIAO_5V'); c('U8', 13, 'GND'); c('U8', 18, 'GND'); c('U8', 20, 'GND'); c('U8', 17, 'RUN')
for p in (2, 3, 4, 5, 6, 9, 10, 11, 12, 15, 16, 19): c('U8', p, None)
# audio mix
c('R1', 1, 'PWM'); c('R1', 2, 'AF1'); c('C1', 1, 'AF1'); c('C1', 2, 'GND'); c('R2', 1, 'AF1'); c('R2', 2, 'AF2'); c('C2', 1, 'AF2'); c('C2', 2, 'GND')
c('R3', 1, 'AF2'); c('R3', 2, 'AUDIO_OUT'); c('R4', 1, 'AUDIO_IN'); c('R4', 2, 'AUDIO_OUT'); c('JP1', 1, 'AUDIO_IN'); c('JP1', 2, 'AUDIO_OUT')
c('JP2', 1, 'CART_PRESENT'); c('JP2', 2, '+5V')
# reset / debug
c('SW1', 1, 'RUN'); c('SW1', 2, 'GND'); c('J2', 1, 'RUN'); c('J2', 2, 'GND'); c('J5', 1, 'SWCLK'); c('J5', 2, 'GND'); c('J5', 3, 'SWDIO')
# USB VBUS -> D1 -> +5V (console rail); +5V -> D2 -> XIAO 5V pin (so the XIAO's own USB cannot back-feed the console)
c('D1', 2, 'VBUS'); c('D1', 1, '+5V'); c('D2', 2, '+5V'); c('D2', 1, 'XIAO_5V')

POWER_NETS = {'+5V', '+3V3', '+1V1', 'GND', 'VBUS'}

if __name__ == '__main__':
    nets = {}
    for ref, pins in NETS.items():
        for p, nn in pins.items():
            if nn: nets.setdefault(nn, []).append(f'{ref}.{p}')
    print(len(PARTS), 'parts', len(nets), 'nets')
    for nn, nodes in sorted(nets.items()):
        if len(nodes) < 2: print('  single-node net:', nn, nodes)
    print('parts without connections:', [r for r in PARTS if r not in NETS])
    print('GPIO used:', len(GPIO_NET))
