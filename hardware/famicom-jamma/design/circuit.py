"""Circuit of the Famicom JAMMA board, revision 0.1.

The circuit is written as Python so that it can be checked by program:
tools/build.py turns it into a KiCad project, runs KiCad's electrical rule check,
compares KiCad's netlist with this description pin by pin, and checks the parts rule
(JLCPCB-assembled parts must be Basic parts, hand-soldered parts come from Akizuki).

Read design/README.md first: it explains the three microcontrollers, the two operating
modes, the power domains and the assumptions that still have to be proven on the bench.

Net naming
  CA0-15  CPU address          CD0-7   CPU data at the CPU pins
  PPD0-7  CPU data at the PPU pins (behind the 470 ohm resistors)
  CART_D0-7  CPU data at the cartridge (behind the 100 ohm resistors)
  PA0-13  PPU address (PA0-7 from the latch)      PD0-7   PPU multiplexed address/data bus
  A_xxx / B_xxx / C_xxx   the microcontroller side of a series resistor
  J_xxx   a JAMMA finger       I_xxx   an input of the shift-register chain
  xxx_N   active low
"""
from fcgen.model import Design, NC, JLC, AKI, DONOR, PCB
from fcgen import parts as P
import symbols

V5 = "+5V"          # after the fuse, always on while the cabinet is on
VSW = "+5V_SW"      # switched: CPU, PPU, memories, 5 V logic, cartridge
V33 = "+3V3"        # board logic rail (input shift registers, pull-ups)
GND = "GND"

# Akizuki sales codes (checked against the shop's pages; see README "Parts")
AKI_CODE = {
    "pico2": "129604", "dip40_socket": "100034", "pico_socket": "117584", "header_1x40": "100167",
    "74HC138": "110013", "74HC00": "110856", "74HC373": "131768", "74HC165": "114679",
    "sram": "101083", "tl712": "113885", "pam8012": "108217", "usbc": "113080",
    "polyfuse": "100769", "cap470u": "108426",
    "dip8_socket": "", "socket_strip": "", "dipsw4": "", "trimmer10k": "", "jumper": "",
}


def bits(prefix, n, start=0):
    return [f"{prefix}{i}" for i in range(start, start + n)]


def hc595(s, ref, value, vcc, ser, srclk, rclk, oe_n, q, qh_s=NC, note=""):
    """74HC595D (JLCPCB Basic).  q is the list of eight nets for QA..QH."""
    pins = {"SER": ser, "SRCLK": srclk, "RCLK": rclk, "/SRCLR": vcc, "/OE": oe_n, "VCC": vcc, "GND": GND, "QH'": qh_s}
    pins.update({f"Q{c}": net for c, net in zip("ABCDEFGH", q)})
    s.ic(ref, "74HC595", value, P.FP_SOIC16, JLC, P.use("C5947", "74HC595D"), pins=pins, note=note)
    P.C(s, "100n", vcc, GND)


def hc165(s, ref, value, ser, qh, inputs, note=""):
    """74HC165 (Akizuki, DIP-16) on the 3.3 V rail.  inputs is the list of eight nets for A..H."""
    pins = {"SH/LD": "IO_LATCH", "CLK": "IO_CLK", "CLK_INH": GND, "SER": ser, "QH": qh, "/QH": NC, "VCC": V33, "GND": GND}
    pins.update({c: net for c, net in zip("ABCDEFGH", inputs)})
    s.ic(ref, "74HC165", value, P.FP_DIP16, AKI, AKI_CODE["74HC165"], pins=pins, note=note)
    P.C(s, "100n", V33, GND)


# ====================================================================== power
def sheet_power(d):
    s = d.sheet("power", "Power: +5V entry, switched +5V_SW, +3V3, supply of the Pico modules")
    s.note("+5V_IN comes from the JAMMA fingers 3, 4, C, D.  -5 V and +12 V are not used.")
    s.note("+5V_SW feeds the CPU, the PPU, the memories, the 5 V logic and the cartridge.  It is off until Pico C raises EN_5VSW,")
    s.note("so that no 5 V signal reaches a Pico pin before that Pico is powered (the RP2350 pins tolerate 5 V only while powered).")
    s.note("VSYS feeds the three Pico modules and the +3V3 regulator from +5V or from the USB socket, whichever is present.")

    s.lib("F", "Device:Polyfuse", "RGEF300 (3 A hold)", "Fuse:Fuse_Bourns_MF-RG300", AKI, AKI_CODE["polyfuse"],
          {1: "+5V_IN", 2: V5}, ref="F1", horizontal=True)
    P.tvs(s, V5, GND, note="absorbs spikes only: it starts to conduct above 7.2 V and does not protect against a steady over-voltage")
    P.diode(s, "SS54", GND, V5, note="conducts and trips F1 if the supply is connected the wrong way round")
    s.lib("C", "Device:C_Polarized", "470u/16V", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", AKI, AKI_CODE["cap470u"],
          {1: V5, 2: GND}, horizontal=True)
    P.C(s, "10u", V5, GND)
    P.C(s, "100n", V5, GND)

    # supply of the Pico modules and of the 3.3 V regulator
    P.diode(s, "SS14", V5, "VSYS")
    P.diode(s, "SS14", "VBUS_USB", "VSYS", note="lets the USB socket power the three Pico modules for a firmware update on the bench")
    P.C(s, "10u", "VSYS", GND)
    P.semi(s, "U", "AMS1117-3.3", {1: GND, 2: V33, 3: "VSYS"}, ref="U28")
    P.CT(s, "100u/6.3V", V33, GND, note="the regulator needs a tantalum capacitor of 22 uF or more at its output")
    P.C(s, "100n", V33, GND)
    # shunt clamp: a wiring fault that feeds 5 V or 12 V into a JAMMA input reaches +3V3 through the 1 k pull-up
    s.ic("U2", "CJ431", "CJ431", P.FP_SOT23, JLC, P.use("C3113", "CJ431"),
         pins={"K": V33, "REF": "CLAMP_REF", "A": GND}, note="clamps +3V3 at about 3.8 V = 2.5 V x (1 + 5.1k/10k)")
    P.R(s, "5.1k", V33, "CLAMP_REF")
    P.R(s, "10k", "CLAMP_REF", GND)
    P.R(s, "1k", V33, "LED_3V3")
    P.led(s, "LED_3V3", GND, note="lit while the board logic rail is up")

    # high-side switch for the Famicom half of the board, slow turn-on through the gate-drain capacitor
    P.pfet(s, "SW_GATE", VSW, V5, note="AO3401A: source +5V, drain +5V_SW")
    P.R(s, "47k", V5, "SW_GATE")
    P.C(s, "100n", "SW_GATE", VSW, note="gate-drain capacitor: +5V_SW rises in a few milliseconds, which limits the inrush current")
    P.R(s, "10k", "SW_GATE", "SW_GATE_L", note="on: gate at 5 V x 10k/57k = 0.9 V, so the gate-source voltage is -4.1 V")
    P.nfet(s, "SW_EN_G", "SW_GATE_L", GND)
    P.R(s, "1k", "EN_5VSW", "SW_EN_G")
    P.R(s, "1k", "EN_5VSW", GND, note="keeps +5V_SW off while Pico C is unpowered, in reset or being programmed; "
        "1 k is low enough to hold the line low against the pad leakage of early RP2350 chips (erratum E9)")
    P.C(s, "100n", "SW_EN_G", GND)
    P.C(s, "10u", VSW, GND)
    P.C(s, "10u", VSW, GND)
    P.R(s, "1k", VSW, "LED_5VSW")
    P.led(s, "LED_5VSW", GND, note="lit while the Famicom half is powered")

    # +5V monitor for Pico C (ADC input, 3.3 V only)
    P.R(s, "20k", V5, "ADC_5V")
    P.R(s, "12k", "ADC_5V", GND)
    P.C(s, "100n", "ADC_5V", GND)

    for n in (V5, VSW, V33, "VSYS", GND, GND):
        P.testpoint(s, n)


# ====================================================================== CPU
def sheet_cpu(d):
    s = d.sheet("cpu", "CPU: RP2A03, work RAM, address decoder, data-bus resistors")
    s.note("U1 is the donor's RP2A03 in a 40-pin socket.  In emulation mode the socket is empty and the dump shift registers drive the buses.")
    s.note("The 470 ohm resistors let Pico B replace what the PPU sees on a write without disturbing the CPU side of the bus.")
    s.note("No pull-ups on the CPU data bus: they are known to upset some PPU revisions, and games read the floating bus.")

    cpu = {"CLK": "CPU_CLK", "/RST": "CPU_RST_N", "TST": GND, "/IRQ": "IRQ_N", "/NMI": "NMI_N",
           "M2": "M2", "R/W": "CPU_RW", "/OE1": "OE1_N", "/OE2": "OE2_N",
           "OUT0": "OUT0", "OUT1": "OUT1", "OUT2": "OUT2", "AD1": "APU_AD1", "AD2": "APU_AD2",
           "VCC": VSW, "GND": GND}
    cpu.update({f"D{i}": f"CD{i}" for i in range(8)})
    cpu.update({f"A{i}": f"CA{i}" for i in range(16)})
    s.ic("U1", "RP2A03", "RP2A03 (donor)", P.FP_DIP40_SOCKET, DONOR, "", pins=cpu,
         note="fitted in a 40-pin round-pin socket")
    P.C(s, "100n", VSW, GND)
    P.CT(s, "10u/16V", VSW, GND)

    # clock and reset from Pico A
    P.R(s, "33", "CLK", "CPU_CLK", note="21.5 MHz from Pico A, 3.3 V square wave, DC coupled")
    P.R(s, "470", "A_CPU_RST", "CPU_RST_N")
    P.RA(s, "4.7k", [("CPU_RST_N", GND), ("PPU_RST_N", GND)],
         note="both resets are held low until Pico A releases them")
    P.RA(s, "10k", [("IRQ_N", VSW), ("NMI_N", VSW), ("CPU_RW", VSW), ("M2", GND)],
         note="defined levels while the CPU is in reset or absent: read, and M2 low so that nothing is selected")

    # work RAM: 2K used, as in the Famicom (mirrored four times in 0000-1FFF)
    ram = {"/E1": "WRAM_CS_N", "E2": VSW, "/G": GND, "/W": "CPU_RW", "VCC": VSW, "VSS": GND, "NC": NC}
    ram.update({f"A{i}": f"CA{i}" for i in range(11)})
    ram.update({f"A{i}": f"WRAM_A{i}" for i in range(11, 17)})
    ram.update({f"DQ{i}": f"CD{i}" for i in range(8)})
    s.ic("U3", "M68AF127B", "M68AF127B (work RAM)", P.FP_SOP32, AKI, AKI_CODE["sram"], pins=ram)
    P.C(s, "100n", VSW, GND)
    P.RA_many(s, "10k", [(f"WRAM_A{i}", GND) for i in range(11, 17)], note="upper address lines held low; J4 can drive them for a larger RAM")

    # address decoder (the Famicom's 74LS139 rebuilt from a 74HC138 and a NAND gate)
    s.ic("U4", "74HC138", "74HC138", P.FP_DIP16, AKI, AKI_CODE["74HC138"], pins={
        "A": "CA13", "B": "CA14", "C": GND, "G1": "M2", "/G2A": "CA15", "/G2B": GND,
        "/Y0": "WRAM_CS_N", "/Y1": "PPU_CS_N", "/Y2": "DEC_4000_N", "/Y3": "DEC_6000_N",
        "/Y4": NC, "/Y5": NC, "/Y6": NC, "/Y7": NC, "VCC": VSW, "GND": GND},
        note="M2 high and A15 low: Y0 = 0000-1FFF (RAM), Y1 = 2000-3FFF (PPU), Y2 = 4000-5FFF, Y3 = 6000-7FFF")
    P.C(s, "100n", VSW, GND)
    s.ic("U5", "74HC00", "74HC00", P.FP_DIP14, AKI, AKI_CODE["74HC00"], pins={
        "1A": "M2", "1B": "CA15", "1Y": "ROMSEL_N",
        "2A": "PA13", "2B": "PA13", "2Y": "PA13_N",
        "3A": GND, "3B": GND, "3Y": NC, "4A": GND, "4B": GND, "4Y": NC, "VCC": VSW, "GND": GND},
        note="/ROMSEL = NAND(M2, A15); /PA13 for the cartridge")
    P.C(s, "100n", VSW, GND)

    # data bus: CPU side -> PPU side, cartridge, Pico B
    for i in range(8):
        P.R(s, "470", f"CD{i}", f"PPD{i}")
    for i in range(8):
        P.R(s, "100", f"CD{i}", f"CART_D{i}")
    for i in range(8):
        P.R(s, "100", f"CD{i}", f"B_CD{i}")
    P.RA_many(s, "4.7k", [(f"CD{i}", GND) for i in range(8)], dnp=True,
              note="not fitted: pull-downs that some Disk System RAM adapters need")

    # taps for Pico B (address, read/write, pad read strobes)
    P.RA(s, "1k", [("CA0", "B_CA0"), ("CA1", "B_CA1"), ("CA2", "B_CA2"), ("CPU_RW", "B_RW")])
    P.RA(s, "1k", [("PPU_CS_N", "B_PPUCS"), ("OE1_N", "B_OE1"), ("OE2_N", "B_OE2")])
    P.R(s, "10k", "OUT0", "B_OUT0")
    P.R(s, "20k", "B_OUT0", GND, note="divider: this Pico pin is not 5 V tolerant")

    # expansion header, not fitted
    hdr = {1: VSW, 2: GND, 40: GND}
    names = bits("CA", 16) + bits("CD", 8) + ["CPU_RW", "M2", "IRQ_N", "NMI_N", "CPU_RST_N", "ROMSEL_N",
                                               "OUT0", "OUT1", "OUT2", "OE1_N", "OE2_N", "DEC_4000_N", "DEC_6000_N"]
    for k, n in enumerate(names):
        hdr[3 + k] = n
    P.header(s, "J3", 2, 20, "CPU bus (option)", hdr, dnp=True)
    P.header(s, "J4", 2, 7, "RAM A11-A16 (option)", {
        1: "WRAM_A11", 3: "WRAM_A12", 5: "WRAM_A13", 7: "WRAM_A14", 9: "WRAM_A15", 11: "WRAM_A16",
        2: "VRAM_A11", 4: "VRAM_A12", 6: "VRAM_A13", 8: "VRAM_A14", 10: "VRAM_A15", 12: "VRAM_A16", 13: VSW, 14: GND}, dnp=True)
    for n in ("M2", "CLK"):
        P.testpoint(s, n)


# ====================================================================== PPU
def sheet_ppu(d):
    s = d.sheet("ppu", "PPU: RP2C02, address latch, video RAM, sprite detector")
    s.note("U6 is the donor's RP2C02 in a 40-pin socket.  EXT0-3 give the lower four bits of the palette index of every pixel once")
    s.note("Pico B has forced bit 6 of register 2000 high.  The fifth bit (sprite or background) is read from the brightness of VOUT:")
    s.note("Pico B makes the PPU store a dark colour in every background entry and a bright one in every sprite entry.")

    ppu = {"CLK": "PPU_CLK", "/RST": "PPU_RST_N", "/CS": "PPU_CS_N", "R/W": "CPU_RW",
           "A0": "CA0", "A1": "CA1", "A2": "CA2", "/INT": "NMI_N", "VOUT": "VOUT",
           "ALE": "ALE", "/RD": "PPU_RD_N", "/WR": "PPU_WR_N", "VCC": VSW, "GND": GND}
    ppu.update({f"D{i}": f"PPD{i}" for i in range(8)})
    ppu.update({f"EXT{i}": f"EXT{i}" for i in range(4)})
    ppu.update({f"AD{i}": f"PD{i}" for i in range(8)})
    ppu.update({f"PA{i}": f"PA{i}" for i in range(8, 14)})
    s.ic("U6", "RP2C02", "RP2C02 (donor)", P.FP_DIP40_SOCKET, DONOR, "", pins=ppu, note="fitted in a 40-pin round-pin socket")
    P.C(s, "100n", VSW, GND)
    P.CT(s, "10u/16V", VSW, GND, note="place directly across pins 40 and 20: reduces the vertical bars in the picture")

    P.R(s, "33", "CLK", "PPU_CLK")
    P.R(s, "470", "A_PPU_RST", "PPU_RST_N")
    P.header(s, "JP1", 1, 2, "PPU /RST = +5V (Famicom wiring)", {1: "PPU_RST_N", 2: VSW}, code=AKI_CODE["header_1x40"],
             note="normally open; a jumper plug ties the PPU reset high as in the Famicom")

    # Pico B's substitution drivers on the PPU side of the data bus
    for i in range(8):
        P.R(s, "33", f"PPD{i}", f"B_OVR{i}")

    # palette index outputs to Pico A
    P.RA(s, "10k", [(f"EXT{i}", GND) for i in range(4)], note="pulled low, never tied to ground: the pins become outputs")
    P.RA(s, "1k", [(f"EXT{i}", f"A_EXT{i}") for i in range(4)])
    P.R(s, "1k", "ALE", "A_ALE")
    P.R(s, "10k", "ALE", GND)

    # low address latch
    s.ic("U7", "74HC373", "74HC373", P.FP_DIP20, AKI, AKI_CODE["74HC373"], pins={
        "/OE": "LATCH_OE_N", "LE": "ALE",
        "1D": "PD7", "1Q": "PA7", "2D": "PD6", "2Q": "PA6", "3D": "PD5", "3Q": "PA5", "4D": "PD4", "4Q": "PA4",
        "5D": "PD3", "5Q": "PA3", "6D": "PD2", "6Q": "PA2", "7D": "PD1", "7Q": "PA1", "8D": "PD0", "8Q": "PA0",
        "VCC": VSW, "GND": GND}, note="same pin use as the Famicom's 74LS373")
    P.C(s, "100n", VSW, GND)
    P.R(s, "10k", "LATCH_OE_N", GND, note="latch outputs on, unless the dump circuit turns them off")
    P.RA_many(s, "10k", [(f"PD{i}", VSW) for i in range(8)], note="defined level while nothing drives the bus; helps the 74HC inputs")
    P.RA(s, "10k", [("PPU_RD_N", VSW), ("PPU_WR_N", VSW), ("CIRAM_CE_N", VSW)])
    P.C(s, "47p", "PPU_RD_N", GND, dnp=True, note="not fitted: the Famicom has 68 pF here")
    P.C(s, "220p", "PPU_CS_N", GND, dnp=True, note="not fitted: early Famicoms have 330 pF + 30 pF here")

    # video RAM: 2K used; the cartridge decides A10 and the chip enable (mirroring)
    ram = {"A8": "PA8", "A9": "PA9", "A10": "CIRAM_A10", "/E1": "CIRAM_CE_N", "E2": VSW,
           "/G": "PPU_RD_N", "/W": "PPU_WR_N", "VCC": VSW, "VSS": GND, "NC": NC}
    ram.update({f"A{i}": f"PA{i}" for i in range(8)})
    ram.update({f"A{i}": f"VRAM_A{i}" for i in range(11, 17)})
    ram.update({f"DQ{i}": f"PD{i}" for i in range(8)})
    s.ic("U8", "M68AF127B", "M68AF127B (video RAM)", P.FP_SOP32, AKI, AKI_CODE["sram"], pins=ram)
    P.C(s, "100n", VSW, GND)
    P.RA_many(s, "10k", [(f"VRAM_A{i}", GND) for i in range(11, 17)])

    # VOUT buffer, sprite comparator
    P.R(s, "100", "VOUT", "VBUF_B")
    P.npn(s, "VBUF_B", VSW, "VBUF", note="emitter follower: VBUF = VOUT - 0.65 V, so the PPU pin sees almost no load")
    P.R(s, "1k", "VBUF", GND)
    P.R(s, "100", "VBUF", "CVBS", note="composite picture for bring-up on a television; not used in the cabinet")
    P.header(s, "J5", 1, 2, "composite video (test)", {1: "CVBS", 2: GND}, code=AKI_CODE["header_1x40"])
    P.R(s, "100", "VBUF", "CMP_INP")
    s.ic("U9", "TL712", "TL712CP", P.FP_DIP8_SOCKET, AKI, AKI_CODE["tl712"], pins={
        "IN+": "CMP_INP", "IN-": "VREF", "OE": VSW, "OUT+": "CMP_OUT", "OUT-": NC, "NC": NC, "VCC": VSW, "GND": GND},
        note="in an 8-pin socket so that a faster comparator on an adapter can replace it")
    P.C(s, "100n", VSW, GND)
    P.C(s, "10u", VSW, GND)
    P.R(s, "100", "VREF_BUF", "VREF")
    P.C(s, "100n", "VREF", GND)
    P.header(s, "J6", 1, 3, "sprite bit source", {1: "CMP_OUT", 2: "SPR_SEL", 3: "VBUF"}, code=AKI_CODE["header_1x40"],
             note="jumper 1-2: comparator (default); 2-3: buffered VOUT straight to the Pico input (experiment)")
    P.R(s, "1k", "SPR_SEL", "A_SPR")

    hdr = {1: VSW, 2: GND, 40: GND}
    names = bits("PA", 14) + bits("PD", 8) + ["PPU_RD_N", "PPU_WR_N", "ALE", "PPU_CS_N", "PPU_RST_N", "NMI_N",
                                               "EXT0", "EXT1", "EXT2", "EXT3", "VOUT", "PA13_N", "CIRAM_A10", "CIRAM_CE_N", "VBUF"]
    for k, n in enumerate(names):
        hdr[3 + k] = n
    P.header(s, "J7", 2, 20, "PPU bus (option)", hdr, dnp=True)
    for n in ("VBUF", "VREF", "CMP_OUT"):
        P.testpoint(s, n)


# ====================================================================== cartridge
def sheet_cart(d):
    s = d.sheet("cart", "Cartridge connector and the dump circuit for emulation mode")
    s.note("J8 is the 60-pin connector taken from the donor Famicom.  Pin 45 carries the board's sound to the cartridge, pin 46 brings it back.")
    s.note("Dump circuit: with the CPU and PPU sockets empty, Pico C reads the cartridge through shift registers and hands the data to Pico A.")
    s.note("The six 74HC595 run from +5V_SW; Pico C drives their inputs open-drain against 4.7 k pull-ups, so they see proper 5 V levels.")
    s.note("In real-chip mode D_OE_ADDR_N and D_OE_DATA_N stay high (pull-ups) and every 74HC595 output is switched off.")

    cart = {1: GND, 16: GND, 30: VSW, 31: VSW, 14: "CPU_RW", 15: "IRQ_N", 17: "PPU_RD_N", 18: "CIRAM_A10",
            32: "M2", 44: "ROMSEL_N", 45: "CART_AUD_OUT", 46: "CART_AUD_RET", 47: "PPU_WR_N", 48: "CIRAM_CE_N", 49: "PA13_N"}
    cart.update({2 + k: f"CA{11 - k}" for k in range(12)})          # 2..13 = A11..A0
    cart.update({33: "CA12", 34: "CA13", 35: "CA14"})
    cart.update({36 + k: f"CART_D{7 - k}" for k in range(8)})        # 36..43 = D7..D0
    cart.update({19 + k: f"PA{6 - k}" for k in range(7)})            # 19..25 = PA6..PA0
    cart.update({50 + k: f"PA{7 + k}" for k in range(7)})            # 50..56 = PA7..PA13
    cart.update({26: "PD0", 27: "PD1", 28: "PD2", 29: "PD3", 57: "PD7", 58: "PD6", 59: "PD5", 60: "PD4"})
    assert sorted(cart) == list(range(1, 61))
    s.ic("J8", "FC_CART60", "Famicom 60-pin (donor)", "fcjamma:Famicom_Cart_60", DONOR, "",
         pins={f"P{n}": net for n, net in cart.items()})
    P.C(s, "100n", VSW, GND)
    P.C(s, "10u", VSW, GND)

    # address and control drivers
    oe, rck = "D_OE_ADDR_N", "D_RCLK"
    hc595(s, "U10", "74HC595 (CPU A0-7)", VSW, "D_SER", "D_SRCLK_F", rck, oe, bits("CA", 8), "D_CA_Q7S")
    hc595(s, "U11", "74HC595 (CPU A8-15)", VSW, "D_CA_Q7S", "D_SRCLK_F", rck, oe, bits("CA", 8, 8))
    hc595(s, "U12", "74HC595 (PPU A0-7)", VSW, "D_SER", "D_SRCLK_F", rck, oe, bits("PA", 8), "D_PA_Q7S")
    hc595(s, "U13", "74HC595 (PPU A8-13)", VSW, "D_PA_Q7S", "D_SRCLK_F", rck, oe, bits("PA", 6, 8) + [NC, NC])
    hc595(s, "U14", "74HC595 (control)", VSW, "D_SER", "D_SRCLK_S", rck, oe,
          ["CPU_RW", "PPU_RD_N", "PPU_WR_N", "LATCH_OE_N", "EMU_PU", NC, NC, NC], "D_CTL_Q7S",
          note="QA R/W, QB PPU /RD, QC PPU /WR, QD latch off, QE pull-up source for M2")
    hc595(s, "U15", "74HC595 (data to cartridge)", VSW, "D_CTL_Q7S", "D_SRCLK_S", rck, "D_OE_DATA_N", bits("CART_D", 8),
          note="drives the data bus only while a mapper register is being written")
    P.RA(s, "4.7k", [("D_SER", VSW), ("D_SRCLK_F", VSW), ("D_SRCLK_F", VSW), ("D_SRCLK_S", VSW)],
         note="two elements in parallel on the fast clock")
    P.RA(s, "4.7k", [("D_RCLK", VSW), ("D_OE_ADDR_N", VSW), ("D_OE_DATA_N", VSW)])
    P.R(s, "1k", "M2", "EMU_PU", note="pull-up for M2 that exists only while the dump circuit is enabled")
    P.R(s, "100", "M2", "C_M2")

    # data read-back, on the 3.3 V input chain (first two registers read by Pico C)
    P.RA_many(s, "10k", [(f"CART_D{i}", f"DI_CD{i}") for i in range(8)],
              note="limit the current into the 3.3 V inputs when the bus is at 5 V")
    P.RA_many(s, "10k", [(f"PD{i}", f"DI_PD{i}") for i in range(8)])
    hc165(s, "U16", "74HC165 (cartridge CPU data)", "IN_Q4", "IN_Q5", bits("DI_CD", 8))
    hc165(s, "U17", "74HC165 (cartridge PPU data)", "IN_Q5", "IN_Q6", bits("DI_PD", 8))
    P.R(s, "100", "IN_Q6", "IN_DATA")

    # mirroring sense for Pico C
    P.R(s, "10k", "CIRAM_A10", "C_CIRAM_A10")
    P.R(s, "20k", "C_CIRAM_A10", GND)


# ====================================================================== video
def sheet_video(d):
    s = d.sheet("video", "Video: RGB resistor DAC and composite sync")
    s.note("Pico A drives the DAC directly.  Full scale is 3.0 V open circuit, about 2.85 V into 2 k, source resistance about 125 ohm.")
    s.note("Red and blue have 3 bits, green has 4.  Only 470 ohm and 1 k are used so that the parts list stays short.")

    def dac(colour, nbits):
        out = f"VID_{colour}"
        b = [f"{colour}{i}" for i in range(nbits)]
        msb, mid, lsb = b[-1], b[-2], b[-3]
        P.R(s, "470", msb, out)
        P.R(s, "470", msb, out, note="two in parallel: 235 ohm")
        P.R(s, "470", mid, out)
        P.R(s, "470", lsb, f"{colour}_L1")
        P.R(s, "470", f"{colour}_L1", out, note="two in series: 940 ohm")
        if nbits == 4:
            P.R(s, "1k", b[0], f"{colour}_L0")
            P.R(s, "1k", f"{colour}_L0", out, note="two in series: 2 k")
        P.R(s, "1k", out, f"{colour}_SH")
        P.R(s, "470", f"{colour}_SH", GND, note="1.47 k to ground sets the 3.0 V full scale")

    dac("R", 3)
    dac("G", 4)
    dac("B", 3)

    # composite sync, negative going, 5 V
    P.R(s, "1k", "CSYNC", "SYNC_B")
    P.R(s, "10k", "SYNC_B", GND)
    P.npn(s, "SYNC_B", "SYNC_C", GND, note="inverts: Pico A outputs the sync pulses high")
    P.R(s, "470", V5, "SYNC_C")
    P.R(s, "100", "SYNC_C", "VID_SYNC")
    P.header(s, "J9", 1, 6, "RGB + sync (monitor / option)", {1: "VID_R", 2: "VID_G", 3: "VID_B", 4: "VID_SYNC", 5: GND, 6: V5},
             code=AKI_CODE["header_1x40"], dnp=True)


# ====================================================================== audio
def sheet_audio(d):
    s = d.sheet("audio", "Audio: mixer, loop through the cartridge, power amplifier")
    s.note("Real-chip mode: 2A03 pins -> mixer (Famicom values) -> cartridge pin 45 -> cartridge -> pin 46 -> volume -> amplifier.")
    s.note("Emulation mode: Pico A's PWM output -> two RC stages -> volume -> amplifier.")
    s.note("The loudspeaker outputs are bridge-tied: JAMMA L is not ground.")

    P.R(s, "100", "APU_AD1", GND)
    P.R(s, "100", "APU_AD2", GND)
    P.R(s, "20k", "APU_AD1", "APU_MIX", note="pulse channels")
    P.R(s, "12k", "APU_AD2", "APU_MIX", note="triangle, noise, DPCM")
    P.C(s, "1u", "APU_MIX", "AUD_INV")
    s.ic("U18", "LM358", "LM358", P.FP_SOIC8, JLC, P.use("C7950", "LM358"), pins={
        "INA+": "AUD_BIAS", "INA-": "AUD_INV", "OUTA": "AUD_PRE",
        "INB+": "VREF_F", "INB-": "VREF_BUF", "OUTB": "VREF_BUF", "V+": VSW, "GND": GND},
        note="A: inverting mixer amplifier.  B: buffer for the comparator threshold")
    P.C(s, "100n", VSW, GND)
    P.R(s, "47k", "AUD_PRE", "AUD_INV")
    P.C(s, "220p", "AUD_PRE", "AUD_INV", note="15 kHz low-pass")
    P.R(s, "20k", VSW, "AUD_BIAS")
    P.R(s, "12k", "AUD_BIAS", GND, note="1.9 V bias, the middle of the LM358's output range on 5 V")
    P.C(s, "10u", "AUD_BIAS", GND)
    P.R(s, "1k", "AUD_PRE", GND, note="keeps the output stage sourcing current (no crossover distortion)")
    P.R(s, "100", "AUD_PRE", "CART_AUD_OUT")

    # comparator threshold: PWM from Pico A, filtered, buffered by the second amplifier
    P.R(s, "10k", "VREF_PWM", "VREF_F")
    P.C(s, "1u", "VREF_F", GND)

    # return from the cartridge and PWM sound from Pico A
    P.C(s, "1u", "CART_AUD_RET", "AUD_RET_AC")
    P.R(s, "10k", "AUD_RET_AC", "AUD_SUM")
    P.R(s, "1k", "AUD_PWM", "AUD_PWM_F1")
    P.C(s, "10n", "AUD_PWM_F1", GND)
    P.R(s, "1k", "AUD_PWM_F1", "AUD_PWM_F2")
    P.C(s, "10n", "AUD_PWM_F2", GND)
    P.C(s, "1u", "AUD_PWM_F2", "AUD_PWM_AC")
    P.R(s, "10k", "AUD_PWM_AC", "AUD_SUM")
    s.lib("RV", "Device:R_Potentiometer_Trim", "10k (volume)", "fcjamma:Trimmer_10k", AKI, AKI_CODE["trimmer10k"],
          {1: "AUD_SUM", 2: "AMP_IN", 3: GND}, ref="RV1")

    s.ic("U19", "AE_PAM8012", "AE-PAM8012", "fcjamma:AE-PAM8012", AKI, AKI_CODE["pam8012"], pins={
        "+V": V5, "GND": GND, "IN+": "AMP_IN", "IN-": GND,
        "OUT+": "SPK_P", "OUT+_8": "SPK_P", "OUT-": "SPK_N", "OUT-_6": "SPK_N"},
        note="input coupling capacitors are on the module; powered from +5V, not through the +5V_SW switch")
    P.CT(s, "10u/16V", V5, GND)
    P.C(s, "10u", V5, GND)
    P.C(s, "100n", V5, GND)
    P.ferrite(s, "SPK_P", "J_SPK_P")
    P.ferrite(s, "SPK_N", "J_SPK_N")
    P.C(s, "1n", "J_SPK_P", GND)
    P.C(s, "1n", "J_SPK_N", GND)
    for n in ("AUD_PRE", "AMP_IN"):
        P.testpoint(s, n)


# ====================================================================== JAMMA
JAMMA_INPUTS = [   # (finger, name)
    ("18", "1P_UP"), ("19", "1P_DOWN"), ("20", "1P_LEFT"), ("21", "1P_RIGHT"),
    ("22", "1P_B1"), ("23", "1P_B2"), ("24", "1P_B3"), ("25", "1P_B4"),
    ("V", "2P_UP"), ("W", "2P_DOWN"), ("X", "2P_LEFT"), ("Y", "2P_RIGHT"),
    ("Z", "2P_B1"), ("a", "2P_B2"), ("b", "2P_B3"), ("c", "2P_B4"),
    ("17", "START1"), ("U", "START2"), ("16", "COIN1"), ("T", "COIN2"),
    ("R", "SERVICE"), ("15", "TEST"), ("S", "TILT"), ("26", "1P_B5"), ("d", "2P_B5"),
]


def sheet_jamma(d):
    s = d.sheet("jamma", "JAMMA edge connector, inputs, coin counter and lock-out drivers")
    s.note("Every input: 1 k pull-up to +3V3 (3.3 mA through the switch), 4.7 k in series, 10 nF to ground, then a 74HC165 on +3V3.")
    s.note("Pico C reads the chain: after a low pulse on IO_LATCH the first bit on IN_DATA is input H of U17, the last is input A of U20.")
    s.note("The same pulse copies the 74HC595's shift register to its outputs, so one cycle reads the inputs and writes the outputs.")
    s.note("Fingers 5/E (-5 V), 6/F (+12 V) and 11/M are not connected.  7/H is the key slot.")

    j = {"1": GND, "2": GND, "A": GND, "B": GND, "27": GND, "28": GND, "e": GND, "f": GND, "14": GND,
         "3": "+5V_IN", "4": "+5V_IN", "C": "+5V_IN", "D": "+5V_IN",
         "5": NC, "E": NC, "6": NC, "F": NC, "11": NC, "M": NC,
         "8": "J_CNT1", "J": "J_CNT2", "9": "J_LOCK1", "K": "J_LOCK2",
         "10": "J_SPK_P", "L": "J_SPK_N",
         "12": "VID_R", "N": "VID_G", "13": "VID_B", "P": "VID_SYNC"}
    for finger, name in JAMMA_INPUTS:
        j[finger] = f"J_{name}"
    pins = {}
    for finger, net in j.items():
        pins[("C" if finger.isdigit() else "S") + finger] = net
    s.ic("J1", "JAMMA56", "JAMMA edge (gold fingers)", "fcjamma:JAMMA_Edge_56", PCB, "", pins=pins)

    names = [n for _f, n in JAMMA_INPUTS]
    P.RA_many(s, "1k", [(f"J_{n}", V33) for n in names])
    P.RA_many(s, "4.7k", [(f"J_{n}", f"I_{n}") for n in names])
    for n in names:
        P.C(s, "10n", f"I_{n}", GND)
    P.tact(s, "SW1", "J_TEST", GND, note="TEST, same as JAMMA finger 15")
    P.tact(s, "SW2", "J_SERVICE", GND, note="SERVICE, same as JAMMA finger R")

    # DIP switch: 1 = chip mode (off: real CPU and PPU, on: emulation); 2-4 are read by the firmware
    s.lib("SW", "Switch:SW_DIP_x04", "DIP switch 4", "Button_Switch_THT:SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm",
          AKI, AKI_CODE["dipsw4"], {1: "I_DIP1", 2: "I_DIP2", 3: "I_DIP3", 4: "I_DIP4", 5: GND, 6: GND, 7: GND, 8: GND}, ref="SW3",
          note="1: off = CPU and PPU chips fitted, on = emulation; 2-4: for the firmware")
    P.RA(s, "10k", [(f"I_DIP{i}", V33) for i in range(1, 5)])

    # signals from the Famicom half that Pico C reads slowly
    for n in ("OUT1", "OUT2"):
        P.R(s, "10k", n, f"I_{n}")
        P.R(s, "20k", f"I_{n}", GND, note="divider from 5 V logic; a game can signal the board through these two CPU outputs")
    P.R(s, "10k", VSW, "I_5VSW")
    P.R(s, "20k", "I_5VSW", GND, note="lets Pico C check that +5V_SW really is on or off")

    hc165(s, "U20", "74HC165 (1P)", GND, "IN_Q1", [f"I_{n}" for n in names[0:8]])
    hc165(s, "U21", "74HC165 (2P)", "IN_Q1", "IN_Q2", [f"I_{n}" for n in names[8:16]])
    hc165(s, "U22", "74HC165 (start, coin, service)", "IN_Q2", "IN_Q3",
          ["I_START1", "I_START2", "I_COIN1", "I_COIN2", "I_SERVICE", "I_TEST", "I_TILT", "I_1P_B5"])
    hc165(s, "U23", "74HC165 (switches, status)", "IN_Q3", "IN_Q4",
          ["I_2P_B5", "I_DIP1", "I_DIP2", "I_DIP3", "I_DIP4", "I_OUT1", "I_OUT2", "I_5VSW"])

    # outputs: coin counters and coin lock-outs
    hc595(s, "U24", "74HC595 (JAMMA outputs)", V33, "OUT_SER", "IO_CLK", "IO_LATCH", "OUT_OE_N",
          ["CNT1_G", "CNT2_G", "LOCK1_G", "LOCK2_G", "GPO4", "GPO5", "GPO6", "GPO7"])
    P.R(s, "10k", "OUT_OE_N", V33, note="outputs stay off until Pico C has loaded the register")
    P.RA(s, "10k", [("CNT1_G", GND), ("CNT2_G", GND), ("LOCK1_G", GND), ("LOCK2_G", GND)])
    for g, drain in (("CNT1_G", "J_CNT1"), ("CNT2_G", "J_CNT2"), ("LOCK1_G", "J_LOCK1"), ("LOCK2_G", "J_LOCK2")):
        P.nfet(s, g, drain, GND, note="low-side switch for a 5 V or 12 V coil in the cabinet")
    P.tvs2(s, "J_CNT1", "J_CNT2", GND, note="clamps the turn-off spike of the coil; works whether the coil is on 5 V or 12 V")
    P.tvs2(s, "J_LOCK1", "J_LOCK2", GND)
    P.header(s, "J2", 1, 6, "spare outputs (option)", {1: "GPO4", 2: "GPO5", 3: "GPO6", 4: "GPO7", 5: V33, 6: GND}, dnp=True)


# ====================================================================== microcontrollers
def pico(s, ref, value, gp, run, v33_tp, note=""):
    pins = {f"GP{n}": gp.get(n, NC) for n in list(range(0, 23)) + [26, 27, 28]}
    pins.update({"VSYS": "VSYS", "VBUS": NC, "3V3": v33_tp, "3V3_EN": NC, "ADC_VREF": NC, "RUN": run, "AGND": GND})
    pins.update({f"GND_{n}": GND for n in (3, 8, 13, 18, 23, 28, 38)})
    s.ic(ref, "PICO2", value, P.FP_PICO, AKI, AKI_CODE["pico2"], pins=pins, note=note)
    P.C(s, "10u", "VSYS", GND)
    P.testpoint(s, v33_tp)


def sheet_mcu(d):
    s = d.sheet("mcu", "Three Raspberry Pi Pico 2 modules, USB Type-C socket, links")
    s.note("Pico A (video): clock and reset for CPU and PPU, palette index and sprite bit in, RGB and sync out; the emulator in emulation mode.")
    s.note("Pico B (bus): watches the CPU's accesses to the PPU, replaces palette data on the PPU side, answers the controller reads.")
    s.note("Pico C (input/output and management): JAMMA inputs and outputs, coin and timer logic, cartridge dump, USB Type-C,")
    s.note("power switch of the Famicom half, and reprogramming of Pico A and Pico B through their debug pins (J13, J14).")

    a = {0: "A_EXT0", 1: "A_EXT1", 2: "A_EXT2", 3: "A_EXT3", 4: "A_SPR", 5: "A_ALE",
         6: "R0", 7: "R1", 8: "R2", 9: "G0", 10: "G1", 11: "G2", 12: "G3", 13: "B0", 14: "B1", 15: "B2",
         16: "CSYNC", 17: "CLK", 18: "A_PPU_RST", 19: "A_MISO", 20: "C_MOSI", 21: "LINK_BA", 22: "C_SCK",
         26: "A_CPU_RST", 27: "AUD_PWM", 28: "VREF_PWM"}
    b = {**{i: f"B_CD{i}" for i in range(8)}, **{8 + i: f"B_OVR{i}" for i in range(8)},
         16: "B_CA0", 17: "B_CA1", 18: "B_CA2", 19: "B_RW", 20: "B_PPUCS", 21: "B_OE1", 22: "B_OE2",
         26: "B_OUT0", 27: "LINK_CB", 28: "B_TX"}
    c = {0: "D_SER", 1: "D_SRCLK_F", 2: "D_SRCLK_S", 3: "D_RCLK", 4: "D_OE_ADDR_N", 5: "D_OE_DATA_N", 6: "C_M2",
         7: "OUT_OE_N", 8: "IN_DATA", 9: "IO_LATCH", 10: "IO_CLK", 11: "OUT_SER",
         12: "C_SWCLK_A", 13: "C_SWDIO_A", 14: "C_SWCLK_B", 15: "C_SWDIO_B",
         16: "C_TX", 17: "C_RUN_A", 18: "C_SCK_O", 19: "C_MOSI_O", 20: "C_MISO", 21: "C_RUN_B", 22: "EN_5VSW",
         26: "ADC_5V", 27: "C_CIRAM_A10", 28: "C_SPARE"}
    pico(s, "U25", "Pico 2 A (video)", a, "RUN_A", "A_3V3")
    pico(s, "U26", "Pico 2 B (bus)", b, "RUN_B", "B_3V3")
    pico(s, "U27", "Pico 2 C (I/O, management)", c, "RUN_C", "C_3V3")

    # links between the modules, one series resistor per line
    P.R(s, "100", "B_TX", "LINK_BA", note="Pico B -> Pico A: palette and mask register writes")
    P.R(s, "100", "C_TX", "LINK_CB", note="Pico C -> Pico B: controller state for both players")
    P.R(s, "100", "C_SCK_O", "C_SCK")
    P.R(s, "100", "C_MOSI_O", "C_MOSI", note="Pico C -> Pico A: cartridge image, controller state, timer display")
    P.R(s, "100", "A_MISO", "C_MISO")

    # Pico C programs and resets the other two
    P.RA(s, "1k", [("C_SWCLK_A", "SWCLK_A"), ("C_SWDIO_A", "SWDIO_A"), ("C_SWCLK_B", "SWCLK_B"), ("C_SWDIO_B", "SWDIO_B")])
    P.RA(s, "1k", [("C_RUN_A", "RUN_A"), ("C_RUN_B", "RUN_B")])
    P.socket(s, "J13", 3, "debug pins of Pico A", {1: "SWCLK_A", 2: GND, 3: "SWDIO_A"}, code=AKI_CODE["socket_strip"],
             note="meets a 3-pin header soldered downwards into the Pico's debug pads")
    P.socket(s, "J14", 3, "debug pins of Pico B", {1: "SWCLK_B", 2: GND, 3: "SWDIO_B"}, code=AKI_CODE["socket_strip"])
    P.socket(s, "J15", 3, "debug pins of Pico C", {1: "SWCLK_C", 2: GND, 3: "SWDIO_C"}, code=AKI_CODE["socket_strip"])
    P.header(s, "J16", 1, 3, "debug probe for Pico C (option)", {1: "SWCLK_C", 2: GND, 3: "SWDIO_C"}, dnp=True)
    P.tact(s, "SW4", "RUN_C", GND, note="resets Pico C, which then restarts the whole board")

    # USB Type-C socket for firmware updates
    s.ic("J10", "AE_USB_TYPE_C", "AE-USB2.0-TYPE-C", "fcjamma:AE-USB2.0-TYPE-C", AKI, AKI_CODE["usbc"], pins={
        "VBUS": "VBUS_USB", "D-": "USB_DM", "D+": "USB_DP", "CC1": "USB_CC1", "CC2": "USB_CC2", "GND": GND, "GND_7": GND})
    P.R(s, "5.1k", "USB_CC1", GND)
    P.R(s, "5.1k", "USB_CC2", GND, note="the module has no CC resistors; without them a Type-C host supplies no power")
    P.header(s, "J11", 1, 4, "USB to Pico C", {1: "VBUS_USB", 2: "USB_DM", 3: "USB_DP", 4: GND}, code=AKI_CODE["header_1x40"],
             note="a short Micro-B lead to Pico C's USB socket, or two wires to its test points TP2 (D-) and TP3 (D+)")
    P.testpoint(s, "C_SPARE")


def build():
    d = Design("fcjamma", "Famicom JAMMA board")
    symbols.define(d)
    sheet_power(d)
    sheet_cpu(d)
    sheet_ppu(d)
    sheet_cart(d)
    sheet_video(d)
    sheet_audio(d)
    sheet_jamma(d)
    sheet_mcu(d)

    # things to buy that are not schematic parts
    d.extra(AKI, AKI_CODE["dip40_socket"], "40-pin round-pin IC socket", 2, "for U1 (RP2A03) and U6 (RP2C02)")
    d.extra(AKI, AKI_CODE["dip8_socket"], "8-pin IC socket", 1, "for U9 (TL712CP)")
    d.extra(AKI, AKI_CODE["pico_socket"], "pin sockets for a Pico, pair of 1x20", 3, "for U25, U26, U27")
    d.extra(AKI, AKI_CODE["header_1x40"], "pin header 1x40", 4, "the Pico modules are sold without pins: 2 x 20 + 3 debug pins each")
    d.extra(AKI, AKI_CODE["jumper"], "jumper plug 2.54 mm", 2, "J6 (and JP1 if the Famicom reset wiring is wanted)")
    return d, ["GND", "+5V", "+5V_SW", "VSYS"]
