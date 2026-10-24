"""famicart hardware: single source of truth for parts and connectivity.
Used by gen_sch.py (schematic) and gen_pcb.py (placement). Net names are the schematic global labels."""

# ---------- parts ----------
# ref: (lib, symbol, value, footprint, pcb placement (x, y, rot, side))
PARTS = {
 'J1':  ('famicart', 'Famicom_CardEdge_60', 'Famicom 60-pin edge', 'famicart:Famicom_CardEdge_60', (45.0, 35.4, 0, 'F')),
 'U1':  ('famicart', 'RPi_Pico2', 'Raspberry Pi Pico 2', 'famicart:RPi_Pico_SMD', (31.0, 12.0, 90, 'F')),
 'U2':  ('74xx', '74LS541', '74LVC541 (CPU CTRL)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (9.0, 30.5, 90, 'F')),
 'U3':  ('74xx', '74LS541', '74LVC541 (CPU A8-14)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (17.5, 30.5, 90, 'F')),
 'U4':  ('74xx', '74LS541', '74LVC541 (CPU A0-7)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (26.0, 30.5, 90, 'F')),
 'U5':  ('74xx', '74HC245', '74LVC245 (CPU D)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (34.5, 30.5, 90, 'F')),
 'U6':  ('74xx', '74LS541', '74LVC541 (PPU A8-13)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (56.0, 30.5, 90, 'F')),
 'U7':  ('74xx', '74LS541', '74LVC541 (PPU A0-7)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (64.5, 30.5, 90, 'F')),
 'U8':  ('74xx', '74HC245', '74LVC245 (PPU D)', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (73.0, 30.5, 90, 'F')),
 'U9':  ('74xx', '74LS139', '74LVC139', 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm', (45.0, 30.5, 90, 'F')),
 'U10': ('74xGxx', '74LVC1G17', '74LVC1G17 (M2)', 'Package_TO_SOT_SMD:SOT-23-5', (62.0, 20.5, 0, 'F')),
 'J3':  ('Connector', 'USB_C_Receptacle', 'USB-C (USB 2.0, HRO TYPE-C-31-M-12)', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', (76.0, 4.3, 180, 'F')),
 'R6':  ('Device', 'R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', (73.5, 11.5, 0, 'F')),
 'R7':  ('Device', 'R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', (77.5, 11.5, 0, 'F')),
 'JP3': ('Jumper', 'SolderJumper_3_Open', 'USB D+ -> TP_A | TP_B', 'famicart:SolderJumper-3_P1.6mm_Open', (9.0, 6.0, 0, 'B')),
 'JP4': ('Jumper', 'SolderJumper_3_Open', 'USB D- -> TP_B | TP_A', 'famicart:SolderJumper-3_P1.6mm_Open', (9.0, 10.0, 0, 'B')),
 'W1':  ('famicart', 'WirePads_1x3', 'TP wire pads (A, B, GND)', 'famicart:WirePads_1x3', (9.0, 14.0, 0, 'B')),
 'SW1': ('Switch', 'SW_Push', 'RESET (RUN)', 'Button_Switch_SMD:SW_SPST_TL3342', (78.0, 21.5, 0, 'F')),
 'J2':  ('Connector_Generic', 'Conn_01x02', 'RUN/GND (console reset wire)', 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', (86.0, 20.0, 0, 'F')),
 'U11': ('74xGxx', '74LVC1G08', '74LVC1G08 (/PPUACC)', 'Package_TO_SOT_SMD:SOT-23-5', (82.0, 30.5, 0, 'F')),
 'U12': ('74xGxx', '74LVC1G07', '74LVC1G07 (/IRQ)', 'Package_TO_SOT_SMD:SOT-23-5', (64.0, 11.5, 0, 'F')),
 'R1':  ('Device', 'R', '2.2k', 'Resistor_SMD:R_0603_1608Metric', (65.0, 14.5, 0, 'F')),
 'R2':  ('Device', 'R', '2.2k', 'Resistor_SMD:R_0603_1608Metric', (69.0, 14.5, 0, 'F')),
 'R3':  ('Device', 'R', '4.7k', 'Resistor_SMD:R_0603_1608Metric', (73.0, 14.5, 0, 'F')),
 'R4':  ('Device', 'R', '1k',   'Resistor_SMD:R_0603_1608Metric', (77.0, 14.5, 0, 'F')),
 'R5':  ('Device', 'R', '10k',  'Resistor_SMD:R_0603_1608Metric', (69.0, 11.5, 0, 'F')),
 'C1':  ('Device', 'C', '10n',  'Capacitor_SMD:C_0603_1608Metric', (65.0, 17.5, 0, 'F')),
 'C2':  ('Device', 'C', '10n',  'Capacitor_SMD:C_0603_1608Metric', (69.0, 17.5, 0, 'F')),
 'C3':  ('Device', 'C', '10u',  'Capacitor_SMD:C_0805_2012Metric', (82.0, 11.5, 0, 'F')),
 'C4':  ('Device', 'C', '10u',  'Capacitor_SMD:C_0805_2012Metric', (82.0, 14.5, 0, 'F')),
 'JP1': ('Jumper', 'SolderJumper_2_Open', 'AUDIO bypass', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', (78.0, 14.0, 0, 'B')),
 'JP2': ('Jumper', 'SolderJumper_2_Open', 'CART_PRESENT', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', (82.0, 14.0, 0, 'B')),
}
# decoupling caps, one per IC, on the back side directly behind each IC
DECOUPLE = {ic: (PARTS[ic][4][0], PARTS[ic][4][1]) for ic in ('U2', 'U3', 'U4', 'U5', 'U6', 'U7', 'U8', 'U9', 'U10', 'U11', 'U12')}
for i, (ic, (x, y)) in enumerate(DECOUPLE.items()):
    PARTS['C%d' % (5 + i)] = ('Device', 'C', '100n', 'Capacitor_SMD:C_0603_1608Metric', (x, y, 90, 'B'))
DECOUPLE_REF = {ic: 'C%d' % (5 + i) for i, ic in enumerate(DECOUPLE)}

# ---------- connectivity: {ref: {pin_number: net}} ----------
NETS = {}
def c(ref, pin, net): NETS.setdefault(ref, {})[str(pin)] = net

# J1: Famicom card edge (nesdev pinout)
J1 = {1:'GND',2:'CPU_A11',3:'CPU_A10',4:'CPU_A9',5:'CPU_A8',6:'CPU_A7',7:'CPU_A6',8:'CPU_A5',9:'CPU_A4',10:'CPU_A3',11:'CPU_A2',12:'CPU_A1',13:'CPU_A0',14:'CPU_RW',15:'nIRQ',16:'GND',
      17:'PPU_nRD',18:'CIRAM_A10',19:'PPU_A6',20:'PPU_A5',21:'PPU_A4',22:'PPU_A3',23:'PPU_A2',24:'PPU_A1',25:'PPU_A0',26:'PPU_D0',27:'PPU_D1',28:'PPU_D2',29:'PPU_D3',30:'+5V',
      31:'CART_PRESENT',32:'M2',33:'CPU_A12',34:'CPU_A13',35:'CPU_A14',36:'CPU_D7',37:'CPU_D6',38:'CPU_D5',39:'CPU_D4',40:'CPU_D3',41:'CPU_D2',42:'CPU_D1',43:'CPU_D0',44:'nROMSEL',
      45:'AUDIO_IN',46:'AUDIO_OUT',47:'PPU_nWR',48:'CIRAM_nCE',49:None,50:'PPU_A7',51:'PPU_A8',52:'PPU_A9',53:'PPU_A10',54:'PPU_A11',55:'PPU_A12',56:'PPU_A13',57:'PPU_D7',58:'PPU_D6',59:'PPU_D5',60:'PPU_D4'}
for p, n in J1.items(): c('J1', p, n)

# U1: Pico 2 (pin numbers of the module)
PICO_GPIO_PIN = {0:1,1:2,2:4,3:5,4:6,5:7,6:9,7:10,8:11,9:12,10:14,11:15,12:16,13:17,14:19,15:20,16:21,17:22,18:24,19:25,20:26,21:27,22:29,26:31,27:32,28:34}
for gp in range(8):  c('U1', PICO_GPIO_PIN[gp], 'CPUP%d' % gp)
for gp in range(8):  c('U1', PICO_GPIO_PIN[8 + gp], 'PPUP%d' % gp)
c('U1', PICO_GPIO_PIN[16], 'nPPUACC'); c('U1', PICO_GPIO_PIN[17], 'M2_3V3')
c('U1', PICO_GPIO_PIN[18], 'SELC0'); c('U1', PICO_GPIO_PIN[19], 'SELC1'); c('U1', PICO_GPIO_PIN[20], 'SELP0'); c('U1', PICO_GPIO_PIN[21], 'SELP1')
c('U1', PICO_GPIO_PIN[22], 'IRQ_GPIO'); c('U1', PICO_GPIO_PIN[26], 'PWM'); c('U1', PICO_GPIO_PIN[27], 'CIRAM_A10'); c('U1', PICO_GPIO_PIN[28], 'CIRAM_nCE')
for p in (3, 8, 13, 18, 23, 28, 33, 38, 42): c('U1', p, 'GND')
c('U1', 36, '+3V3'); c('U1', 39, '+5V')
for p in (35, 37, 41, 43): c('U1', p, None)   # ADC_VREF, 3V3_EN, SWCLK, SWDIO: no connect
c('U1', 30, 'RUN'); c('U1', 40, 'VBUS')            # reset line, USB-C bus power into the Pico's VBUS input
c('U1', 44, 'USB_TPA'); c('U1', 45, 'USB_TPB'); c('U1', 46, 'GND')   # Pico underside USB test points (TP2/TP3 + TP1)
# J3 USB-C (USB 2.0 only): both A/B rows of D+/D- tied, CC pull-downs, VBUS
for pin in ('A4', 'A9', 'B4', 'B9'): c('J3', pin, 'VBUS')
for pin in ('A1', 'A12', 'B1', 'B12', 'S1'): c('J3', pin, 'GND')
c('J3', 'A5', 'CC1'); c('J3', 'B5', 'CC2')
for pin in ('A6', 'B6'): c('J3', pin, 'USB_DP')
for pin in ('A7', 'B7'): c('J3', pin, 'USB_DM')
for pin in ('A2', 'A3', 'A8', 'A10', 'A11', 'B2', 'B3', 'B8', 'B10', 'B11'): c('J3', pin, None)
c('R6', 1, 'CC1'); c('R6', 2, 'GND'); c('R7', 1, 'CC2'); c('R7', 2, 'GND')
# D+/D- to the Pico test points through swap-able 3-pad solder jumpers (bridge C-A on both for TP_A = D+)
c('JP3', 2, 'USB_DP'); c('JP3', 1, 'USB_TPA'); c('JP3', 3, 'USB_TPB')
c('JP4', 2, 'USB_DM'); c('JP4', 1, 'USB_TPB'); c('JP4', 3, 'USB_TPA')
c('W1', 1, 'USB_TPA'); c('W1', 2, 'USB_TPB'); c('W1', 3, 'GND')
# reset: tactile switch + 2-pin header (wire to the console's reset switch if desired)
c('SW1', 1, 'RUN'); c('SW1', 2, 'GND'); c('J2', 1, 'RUN'); c('J2', 2, 'GND')

# 74LVC541 pin map (74LS541 symbol): 1 /G1, 19 /G2, 2-9 A0-A7, 18..11 Y0..Y7, 10 GND, 20 VCC
def buf541(ref, inputs, outputs, oe):
    c(ref, 1, oe); c(ref, 19, oe); c(ref, 10, 'GND'); c(ref, 20, '+3V3')
    for i in range(8): c(ref, 2 + i, inputs[i]); c(ref, 18 - i, outputs[i])
CPUP = ['CPUP%d' % i for i in range(8)]; PPUP = ['PPUP%d' % i for i in range(8)]
buf541('U2', ['CPU_RW', 'nROMSEL', 'GND', 'GND', 'GND', 'GND', 'GND', 'GND'], CPUP, 'OEC_CTRL')
buf541('U3', ['CPU_A%d' % (8 + i) for i in range(7)] + ['GND'], CPUP, 'OEC_HI')
buf541('U4', ['CPU_A%d' % i for i in range(8)], CPUP, 'OEC_LO')
buf541('U6', ['PPU_A%d' % (8 + i) for i in range(6)] + ['PPU_nRD', 'PPU_nWR'], PPUP, 'OEP_HI')
buf541('U7', ['PPU_A%d' % i for i in range(8)], PPUP, 'OEP_LO')
# 74LVC245 (74HC245 symbol): 1 DIR(A->B), 19 /OE, 2-9 A0-A7, 18..11 B0..B7, 10 GND, 20 VCC
def xcvr245(ref, a, b, dir_net, oe):
    c(ref, 1, dir_net); c(ref, 19, oe); c(ref, 10, 'GND'); c(ref, 20, '+3V3')
    for i in range(8): c(ref, 2 + i, a[i]); c(ref, 18 - i, b[i])
xcvr245('U5', CPUP, ['CPU_D%d' % i for i in range(8)], 'CPU_RW', 'OEC_D')     # read (R/W=1): A(RP2040)->B(console)
xcvr245('U8', ['PPU_D%d' % i for i in range(8)], PPUP, 'PPU_nRD', 'OEP_D')    # read (/RD=0): B(RP2040)->A(console)
# 74LVC139 (74LS139 symbol): A: 1 /E, 2 A0, 3 A1, 4-7 O0-O3 ; B: 15 /E, 14 A0, 13 A1, 12-9 O0-O3 ; 8 GND, 16 VCC
c('U9', 1, 'GND'); c('U9', 2, 'SELC0'); c('U9', 3, 'SELC1'); c('U9', 4, 'OEC_CTRL'); c('U9', 5, 'OEC_LO'); c('U9', 6, 'OEC_HI'); c('U9', 7, 'OEC_D')
c('U9', 15, 'GND'); c('U9', 14, 'SELP0'); c('U9', 13, 'SELP1'); c('U9', 12, None); c('U9', 11, 'OEP_LO'); c('U9', 10, 'OEP_HI'); c('U9', 9, 'OEP_D')
c('U9', 8, 'GND'); c('U9', 16, '+3V3')
# single gates (SOT-23-5): 1G17: 1 NC, 2 A, 3 GND, 4 Y, 5 VCC ; 1G08: 1 A, 2 B, 3 GND, 4 Y, 5 VCC ; 1G07: 1 NC, 2 A, 3 GND, 4 Y(OD), 5 VCC
c('U10', 1, None); c('U10', 2, 'M2'); c('U10', 3, 'GND'); c('U10', 4, 'M2_3V3'); c('U10', 5, '+3V3')
c('U11', 1, 'PPU_nRD'); c('U11', 2, 'PPU_nWR'); c('U11', 3, 'GND'); c('U11', 4, 'nPPUACC'); c('U11', 5, '+3V3')
c('U12', 1, None); c('U12', 2, 'IRQ_GPIO'); c('U12', 3, 'GND'); c('U12', 4, 'nIRQ'); c('U12', 5, '+3V3')
# audio: PWM -R1- AF1 -R2- AF2 -R3- AUDIO_OUT ; C1 AF1-GND ; C2 AF2-GND ; R4 AUDIO_IN-AUDIO_OUT ; JP1 bypass
c('R1', 1, 'PWM'); c('R1', 2, 'AF1'); c('C1', 1, 'AF1'); c('C1', 2, 'GND')
c('R2', 1, 'AF1'); c('R2', 2, 'AF2'); c('C2', 1, 'AF2'); c('C2', 2, 'GND')
c('R3', 1, 'AF2'); c('R3', 2, 'AUDIO_OUT'); c('R4', 1, 'AUDIO_IN'); c('R4', 2, 'AUDIO_OUT')
c('JP1', 1, 'AUDIO_IN'); c('JP1', 2, 'AUDIO_OUT')
c('R5', 1, 'nIRQ'); c('R5', 2, '+5V')
c('JP2', 1, 'CART_PRESENT'); c('JP2', 2, '+5V')
c('C3', 1, '+5V'); c('C3', 2, 'GND'); c('C4', 1, '+3V3'); c('C4', 2, 'GND')
for ic, cref in DECOUPLE_REF.items(): c(cref, 1, '+3V3'); c(cref, 2, 'GND')

POWER_NETS = {'+5V', '+3V3', 'GND'}

if __name__ == '__main__':
    nets = {}
    for ref, pins in NETS.items():
        for p, n in pins.items():
            if n: nets.setdefault(n, []).append(f'{ref}.{p}')
    print(len(PARTS), 'parts', len(nets), 'nets')
    for n, nodes in sorted(nets.items()):
        if len(nodes) < 2: print('  single-node net:', n, nodes)
    import sys
    missing = [r for r in PARTS if r not in NETS]
    print('parts without connections:', missing)
