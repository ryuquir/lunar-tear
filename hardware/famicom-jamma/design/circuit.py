"""Circuit of the Famicom JAMMA board, revision 0.3: every part is assembled by JLCPCB.

The circuit is written as Python so that it can be checked by program:
tools/build.py turns it into a KiCad project, runs KiCad's electrical rule check,
compares KiCad's netlist with this description pin by pin, and checks the parts rule
(every fitted part is in JLCPCB's parts library, can be assembled on this kind of order
and is in stock; the only parts added afterwards are the donor's CPU and PPU, which plug
into sockets).

Read README.md first: it explains the three microcontrollers, the two operating
modes, the power domains and the assumptions that still have to be proven on the bench.
Revision 0.1 (JLCPCB assembles only Basic parts, the rest is soldered by hand with parts
from Akizuki) is commit 35126bd.  Revision 0.2 (the first all-JLCPCB version, before the
independent review) is commit ae6575b.  Revision 0.3 is revision 0.2 with the findings of
that review worked in; README.md chapter 6 lists them.

Net naming
  CA0-15  CPU address          CD0-7   CPU data at the CPU pins
  PPD0-7  CPU data at the PPU pins (behind the 470 ohm resistors)
  CART_D0-7  CPU data at the cartridge (behind the 100 ohm resistors)
  PA0-13  PPU address (PA0-7 from the latch)      PD0-7   PPU multiplexed address/data bus
  A_xxx / B_xxx / C_xxx   the microcontroller side of a series resistor
  D_xxx   the dump circuit's shift registers       DQ_xxx  a shift-register output before its series resistor
  J_xxx   a JAMMA finger       I_xxx   an input of the shift-register chain
  xxx_N   active low
"""
from fcgen.model import Design, NC, JLC, JLCX, DONOR, PCB
from fcgen import parts as P
import symbols

V5 = "+5V"          # after the fuse, always on while the cabinet is on
VSW = "+5V_SW"      # switched: CPU, PPU, memories, 5 V logic, cartridge
V33 = "+3V3"        # board logic rail (input shift registers, pull-ups)
GND = "GND"


def bits(prefix, n, start=0):
    return [f"{prefix}{i}" for i in range(start, start + n)]


def sr595(s, ref, value, vcc, ser, srclk, rclk, oe_n, q, qh_s=NC, note=""):
    """8-bit output shift register; q is the list of eight nets for QA..QH.

    On +5V_SW it is a 74HCT595D (its inputs accept the 3.3 V levels of a Pico);
    on +3V3 it is the 74HC595D from JLCPCB's Basic list.
    """
    pins = {"SER": ser, "SRCLK": srclk, "RCLK": rclk, "/SRCLR": vcc, "/OE": oe_n, "VCC": vcc, "GND": GND, "QH'": qh_s}
    pins.update({f"Q{c}": net for c, net in zip("ABCDEFGH", q)})
    if vcc == V33:
        s.ic(ref, "74x595", value, P.FP_SOIC16, JLC, P.use("C5947", "74HC595D"), pins=pins, note=note)
    else:
        s.ic(ref, "74x595", value, P.FP_SOIC16, JLCX, P.usex("74HCT595"), pins=pins, note=note)
    P.decouple(s, ref, vcc)


def sr165(s, ref, value, ser, qh, inputs, note=""):
    """74HC165D on the 3.3 V rail.  inputs is the list of eight nets for A..H."""
    pins = {"SH/LD": "IO_LATCH", "CLK": "IO_CLK", "CLK_INH": GND, "SER": ser, "QH": qh, "/QH": NC, "VCC": V33, "GND": GND}
    pins.update({c: net for c, net in zip("ABCDEFGH", inputs)})
    s.ic(ref, "74x165", value, P.FP_SOIC16, JLCX, P.usex("74HC165"), pins=pins, note=note)
    P.decouple(s, ref, V33)


def sram(s, ref, value, addr, data, ce_n, oe_n, we_n):
    """IS62C256AL-45TLI, 32K x 8.  addr is the list of fifteen nets for A0..A14."""
    pins = {"/CE": ce_n, "/OE": oe_n, "/WE": we_n, "VDD": VSW, "GND": GND}
    pins.update({f"A{i}": net for i, net in enumerate(addr)})
    pins.update({f"IO{i}": net for i, net in enumerate(data)})
    s.ic(ref, "IS62C256AL_TSOP", value, P.FP_TSOP28, JLCX, P.usex("sram"), pins=pins)
    P.decouple(s, ref, VSW)


# ====================================================================== power
def sheet_power(d):
    s = d.sheet("power", "Power: +5V entry, switched +5V_SW, +3V3, supply of the Pico modules")
    s.note("+5V_IN comes from the JAMMA fingers 3, 4, C, D.  -5 V and +12 V are not used.  Supply range at the fingers: 4.75 V to 5.25 V.")
    s.note("+5V_SW feeds the CPU, the PPU, the memories, the 5 V logic and the cartridge through the power switch U29.  It is off until")
    s.note("Pico C raises EN_5VSW, so that no 5 V signal reaches a Pico pin before that Pico is powered (the RP2350 pins tolerate 5 V only")
    s.note("while powered).  U29 limits the current to about 1.3 A: a short circuit in a cartridge cannot draw the cabinet supply's full current.")
    s.note("VSYS feeds the three Pico modules and the +3V3 regulator from +5V or from the USB socket, whichever is present.")

    s.lib("F", "Device:Polyfuse", "TLC-LSMD300D (3 A hold)", P.FP_FUSE2920, JLCX, P.usex("polyfuse"),
          {1: "+5V_IN", 2: V5}, ref="F1", horizontal=True, note="resettable fuse: holds 3 A, trips at 6 A")
    P.tvs(s, V5, GND, note="absorbs spikes only: it starts to conduct above 7.2 V and does not protect against a steady over-voltage")
    P.diode(s, "SS54", GND, V5, note="conducts and trips F1 if the supply is connected the wrong way round")
    s.lib("C", "Device:C_Polarized", "470u/16V", P.FP_CP_6x8, JLCX, P.usex("cap470u"),
          {1: V5, 2: GND}, horizontal=True)
    P.C(s, "10u", V5, GND)
    P.C(s, "100n", V5, GND)

    # supply of the Pico modules and of the 3.3 V regulator
    P.diode(s, "SS14", V5, "VSYS")
    P.diode(s, "SS14", "VBUS_USB", "VSYS", note="lets the USB socket power the three Pico modules for a firmware update on the bench")
    P.R(s, "1k", "VBUS_USB", GND, note="keeps the socket's supply pin below 0.3 V while no cable is plugged in, even with a diode at its "
        "leakage limit (a Type-C host may check for 0 V before it switches its supply on); takes 5 mA from the host")
    P.C(s, "100n", "VBUS_USB", GND)
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

    # power switch for the Famicom half of the board, with current limit
    s.ic("U29", "TPS2553", "TPS2553", P.FP_SOT23_6, JLCX, P.usex("loadswitch"), pins={
        "IN": V5, "OUT": VSW, "EN": "SW_EN", "ILIM": "SW_ILIM", "/FAULT": "I_5VSW", "GND": GND},
        note="off while EN is low or +5V is below 2.4 V; limits the current to 1.2-1.4 A; nothing flows back from +5V_SW to +5V; "
             "/FAULT pulls the I_5VSW bit low on over-current (after 7.5 ms), over-temperature or reverse voltage.  "
             "7 V is the part's absolute maximum; in a short circuit it switches off and on thermally until Pico C lowers EN")
    P.decouple(s, "U29", V5, note="directly at pin 1 of U29")
    P.R(s, "20k", "SW_ILIM", GND, note="sets the current limit (1.3 A typical); keep the track short and away from signals")
    P.R(s, "1k", "EN_5VSW", "SW_EN")
    P.R(s, "1k", "EN_5VSW", GND, note="keeps +5V_SW off while Pico C is unpowered, in reset or being programmed; "
        "1 k is low enough to hold the line low against the pad leakage of early RP2350 chips (erratum E9)")
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
    s.note("U1 is the donor's RP2A03, plugged into a 40-pin socket.  In emulation mode the socket is empty and the dump shift registers drive the buses.")
    s.note("The 470 ohm resistors let Pico B replace what the PPU sees on a write.  A line that Pico B pulls low also drags the CPU side down,")
    s.note("so the firmware reads the CPU side first and drives afterwards (README 3.9).")
    s.note("No pull-ups on the CPU data bus: they are known to upset some PPU revisions, and games read the floating bus.")
    s.note("The logic next to the CPU and the PPU is 74HCT: its inputs switch at TTL levels, which is what the two NMOS chips deliver.")

    cpu = {"CLK": "CPU_CLK", "/RST": "CPU_RST_N", "TST": GND, "/IRQ": "IRQ_N", "/NMI": "NMI_N",
           "M2": "M2", "R/W": "CPU_RW", "/OE1": "OE1_N", "/OE2": "OE2_N",
           "OUT0": "OUT0", "OUT1": "OUT1", "OUT2": "OUT2", "AD1": "APU_AD1", "AD2": "APU_AD2",
           "VCC": VSW, "GND": GND}
    cpu.update({f"D{i}": f"CD{i}" for i in range(8)})
    cpu.update({f"A{i}": f"CA{i}" for i in range(16)})
    s.ic("U1", "RP2A03", "RP2A03 (donor)", P.FP_DIP40_SOCKET, DONOR, "", pins=cpu,
         note="plugged into the 40-pin socket that JLCPCB solders at this position")
    P.decouple(s, "U1", VSW)
    P.CT(s, "10u/16V", VSW, GND)

    # clock and reset from Pico A
    P.solder_jumper3(s, "JP2", "CLK 5V", "CLK", "CLK_SEL", "CLK_BUF",
                     note="as made: Pico A's 3.3 V clock goes straight to the chips.  For a 5 V clock (in case a donor chip does not "
                          "accept 3.3 V): CUT 1-2 FIRST, then bridge 2-3; the clock then passes through a gate of U5 (inverted, about "
                          "10 ns later).  Bridging 2-3 without cutting 1-2 sets the gate against Pico A's pin")
    P.R(s, "33", "CLK_SEL", "CPU_CLK", note="21.5 MHz from Pico A, 3.3 V square wave, DC coupled")
    P.R(s, "470", "CLK", "CLK_G")
    P.R(s, "470", "CLK", "CLK_G", note="two in parallel, 235 ohm: limit the current into the gate's input while +5V_SW is off, "
        "and are small enough to keep the clock's duty cycle (the input's 3 pF adds under 1 ns)")
    P.R(s, "100", "CLK_BUF_O", "CLK_BUF", note="limits the current if JP2 is bridged 2-3 with 1-2 still closed; adds about 3 ns")
    P.R(s, "470", "A_CPU_RST", "CPU_RST_N")
    P.RA(s, "4.7k", [("CPU_RST_N", GND), ("PPU_RST_N", GND), ("CLK", GND)],
         note="both resets are held low until Pico A releases them; the clock line is low while Pico A is in reset")
    P.RA(s, "10k", [("IRQ_N", VSW), ("NMI_N", VSW), ("OE1_N", VSW), ("OE2_N", VSW)],
         note="defined levels while the CPU is in reset or absent")
    P.R(s, "47k", "CPU_RW", VSW, note="read while the CPU is in reset or absent; weak, as the Famicom has no pull-up here")
    P.R(s, "47k", "M2", GND, note="M2 low, so that nothing is selected, while the CPU is in reset or absent; a light load for the CPU's "
        "output.  On an early RP2350 (stepping A2) this holds only while Pico C keeps the input buffer of its M2 pin off (README 3.9)")
    P.R(s, "47k", "OUT0", GND)
    for n in ("CA13", "CA14", "CA15", "PA13"):
        P.R(s, "47k", n, VSW, note="the inputs of U4 and U5 do not float while nothing drives these lines")

    # work RAM: 2K used, as in the Famicom (mirrored four times in 0000-1FFF)
    sram(s, "U3", "IS62C256AL (work RAM)", bits("CA", 11) + bits("WRAM_A", 4, 11), bits("CD", 8), "WRAM_CS_N", GND, "CPU_RW")
    P.RA(s, "10k", [(f"WRAM_A{i}", GND) for i in range(11, 15)], note="upper address lines held low; J4 can drive them for a larger RAM")

    # address decoder (the Famicom's 74LS139 rebuilt from a 74HCT138 and a NAND gate)
    s.ic("U4", "74x138", "74HCT138", P.FP_SOIC16, JLCX, P.usex("74HCT138"), pins={
        "A": "CA13", "B": "CA14", "C": GND, "G1": "M2", "/G2A": "CA15", "/G2B": GND,
        "/Y0": "WRAM_CS_N", "/Y1": "DEC_2000_N", "/Y2": "DEC_4000_N", "/Y3": "DEC_6000_N",
        "/Y4": NC, "/Y5": NC, "/Y6": NC, "/Y7": NC, "VCC": VSW, "GND": GND},
        note="M2 high and A15 low: Y0 = 0000-1FFF (RAM), Y1 = 2000-3FFF (PPU), Y2 = 4000-5FFF, Y3 = 6000-7FFF")
    P.decouple(s, "U4", VSW)
    P.R(s, "33", "DEC_2000_N", "PPU_CS_N",
        note="33 ohm changes nothing; with a larger value and the capacitor on PPU_CS_N the chip select can be delayed towards "
             "the timing of the Famicom's slower 74LS139")
    s.ic("U5", "74x00", "74HCT00", P.FP_SOIC14, JLCX, P.usex("74HCT00"), pins={
        "1A": "M2", "1B": "CA15", "1Y": "ROMSEL_N",
        "2A": "PA13", "2B": "PA13", "2Y": "PA13_N",
        "3A": "OUT0", "3B": "OUT0", "3Y": "OUT0_N", "4A": "CLK_G", "4B": VSW, "4Y": "CLK_BUF_O", "VCC": VSW, "GND": GND},
        note="1: /ROMSEL = NAND(M2, A15); 2: /PA13 for the cartridge; 3: receives OUT0 at TTL levels; 4: optional 5 V clock buffer (JP2)")
    P.decouple(s, "U5", VSW)

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
    P.R(s, "10k", "OUT0_N", "B_OUT0", note="OUT0 (the controller strobe), inverted by U5: a full 5 V swing whatever the CPU's high level is")
    P.R(s, "12k", "B_OUT0", GND, note="divider to 2.7 V: this Pico pin is not 5 V tolerant")

    # expansion headers, not fitted
    hdr = {1: VSW, 2: GND, 40: GND}
    names = bits("CA", 16) + bits("CD", 8) + ["CPU_RW", "M2", "IRQ_N", "NMI_N", "CPU_RST_N", "ROMSEL_N",
                                               "OUT0", "OUT1", "OUT2", "OE1_N", "OE2_N", "DEC_4000_N", "DEC_6000_N"]
    for k, n in enumerate(names):
        hdr[3 + k] = n
    P.header(s, "J3", 2, 20, "CPU bus (option)", hdr)
    P.header(s, "J4", 2, 5, "RAM A11-A14 (option)", {
        1: "WRAM_A11", 3: "WRAM_A12", 5: "WRAM_A13", 7: "WRAM_A14",
        2: "VRAM_A11", 4: "VRAM_A12", 6: "VRAM_A13", 8: "VRAM_A14", 9: VSW, 10: GND})
    for n in ("M2", "CLK", "CLK_SEL"):
        P.testpoint(s, n)


# ====================================================================== PPU
def sheet_ppu(d):
    s = d.sheet("ppu", "PPU: RP2C02, address latch, video RAM, sprite detector")
    s.note("U6 is the donor's RP2C02, plugged into a 40-pin socket.  EXT0-3 give the lower four bits of the palette index of every pixel once")
    s.note("Pico B has forced bit 6 of register 2000 high.  The fifth bit (sprite or background) is read from the brightness of VOUT:")
    s.note("Pico B makes the PPU store a dark colour in every background entry and a bright one in every sprite entry.")
    s.note("EXT shows entry 0 of the current background palette (4, 8 or 12) on transparent pixels, and 0 while rendering is off: the firmware maps these.")

    ppu = {"CLK": "PPU_CLK", "/RST": "PPU_RST_N", "/CS": "PPU_CS_N", "R/W": "CPU_RW",
           "A0": "CA0", "A1": "CA1", "A2": "CA2", "/INT": "NMI_N", "VOUT": "VOUT",
           "ALE": "ALE", "/RD": "PPU_RD_N", "/WR": "PPU_WR_N", "VCC": VSW, "GND": GND}
    ppu.update({f"D{i}": f"PPD{i}" for i in range(8)})
    ppu.update({f"EXT{i}": f"EXT{i}" for i in range(4)})
    ppu.update({f"AD{i}": f"PD{i}" for i in range(8)})
    ppu.update({f"PA{i}": f"PA{i}" for i in range(8, 14)})
    s.ic("U6", "RP2C02", "RP2C02 (donor)", P.FP_DIP40_SOCKET, DONOR, "", pins=ppu,
         note="plugged into the 40-pin socket that JLCPCB solders at this position")
    P.decouple(s, "U6", VSW)
    P.CT(s, "10u/16V", VSW, GND, note="place directly across pins 40 and 20: reduces the vertical bars in the picture")

    P.R(s, "33", "CLK_SEL", "PPU_CLK")
    P.R(s, "470", "A_PPU_RST", "PPU_RST_N")
    P.solder_jumper2(s, "JP1", "RST=5V", "PPU_RST_N", VSW,
                     note="normally open; bridged, it ties the PPU reset to +5V_SW as in the Famicom")

    # Pico B's substitution drivers on the PPU side of the data bus
    for i in range(8):
        P.R(s, "33", f"PPD{i}", f"B_OVR{i}")

    # palette index outputs to Pico A
    for i in range(4):
        P.R(s, "47k", f"EXT{i}", GND, note="pulled low, never tied to ground: the pins become outputs; a light load for them")
    P.RA(s, "1k", [(f"EXT{i}", f"A_EXT{i}") for i in range(4)])
    P.R(s, "1k", "ALE", "A_ALE")
    P.R(s, "47k", "ALE", GND)

    # low address latch
    latch = {"/OE": "LATCH_OE_N", "LE": "ALE", "VCC": VSW, "GND": GND}
    latch.update({f"D{i}": f"PD{i}" for i in range(8)})
    latch.update({f"Q{i}": f"PA{i}" for i in range(8)})
    s.ic("U7", "74x573", "74HCT573", P.FP_SOIC20W, JLCX, P.usex("74HCT573"), pins=latch,
         note="does the job of the Famicom's 74LS373: holds PA0-7 while the bus carries data")
    P.decouple(s, "U7", VSW)
    P.R(s, "10k", "LATCH_OE_N", GND, note="latch outputs on, unless the dump circuit turns them off")
    for i in range(8):
        P.R(s, "47k", f"PD{i}", VSW, note="defined level while nothing drives the bus; weak, as the Famicom has no pull-ups here")
    for n in ("PPU_RD_N", "PPU_WR_N", "CIRAM_CE_N"):
        P.R(s, "47k", n, VSW, note="inactive while the PPU is absent and the dump circuit is off")
    P.C(s, "47p", "PPU_RD_N", GND, dnp=True, note="not fitted: the Famicom has 68 pF here")
    P.C(s, "220p", "PPU_CS_N", GND, dnp=True, note="not fitted: early Famicoms have 330 pF + 30 pF here")

    # video RAM: 2K used; the cartridge decides A10 and the chip enable (mirroring)
    sram(s, "U8", "IS62C256AL (video RAM)", bits("PA", 10) + ["CIRAM_A10"] + bits("VRAM_A", 4, 11), bits("PD", 8),
         "CIRAM_CE_N", "PPU_RD_N", "PPU_WR_N")
    P.RA(s, "10k", [(f"VRAM_A{i}", GND) for i in range(11, 15)])

    # VOUT buffer (a PNP emitter follower, as in the Famicom), sprite comparator, composite test output
    P.R(s, "100", "VOUT", "VBUF_B")
    P.pnp(s, "VBUF_B", GND, "VBUF",
          note="emitter follower as in the Famicom: VBUF = VOUT + 0.65 V (sync tip about 0.8 V, black 1.3 V, white 2.7 V)")
    for _ in range(3):
        P.R(s, "470", VSW, "VBUF", note="three in parallel: 157 ohm, enough current for a television on the test output")
    P.R(s, "1k", "VBUF", "CMP_INP")
    P.R(s, "1k", "CMP_INP", GND, note="halves the signal: black 0.65 V, white 1.4 V, inside the comparator's input range on 3.3 V")
    s.lib("C", "Device:C_Polarized", "470u/16V", P.FP_CP_6x8, JLCX, P.usex("cap470u"), {1: "VBUF", 2: "CVBS_C"}, horizontal=True,
          note="blocks the DC level of the composite test output")
    P.R(s, "100", "CVBS_C", "CVBS", note="composite picture for bring-up on a television (black and white: the clock is not exactly NTSC); not used in the cabinet")
    P.R(s, "10k", "CVBS", GND)
    P.header(s, "J5", 1, 2, "composite video (test)", {1: "CVBS", 2: GND})
    s.ic("U9", "LMV7219", "LMV7219", P.FP_SOT23_5, JLCX, P.usex("comparator"), pins={
        "+IN": "CMP_INP", "-IN": "VREF", "OUT": "CMP_OUT", "V+": V33, "V-": GND},
        note="high while the pixel is brighter than the threshold; 7 ns, against a pixel time of 186 ns; on +3V3, so its output suits the Pico")
    P.decouple(s, "U9", V33)
    P.R(s, "10k", "VREF_PWM", "VREF", note="threshold (about 1.0 V): Pico A's PWM output, averaged")
    P.C(s, "1u", "VREF", GND, note="next to pin 4")
    P.R(s, "1k", "CMP_OUT", "A_SPR")

    hdr = {1: VSW, 2: GND, 40: GND}
    names = bits("PA", 14) + bits("PD", 8) + ["PPU_RD_N", "PPU_WR_N", "ALE", "PPU_CS_N", "PPU_RST_N", "NMI_N",
                                               "EXT0", "EXT1", "EXT2", "EXT3", "VOUT", "PA13_N", "CIRAM_A10", "CIRAM_CE_N", "VBUF"]
    for k, n in enumerate(names):
        hdr[3 + k] = n
    P.header(s, "J7", 2, 20, "PPU bus (option)", hdr)
    for n in ("VBUF", "VREF", "CMP_OUT"):
        P.testpoint(s, n)


# ====================================================================== cartridge
def sheet_cart(d):
    s = d.sheet("cart", "Cartridge connector and the dump circuit for emulation mode")
    s.note("J8 is a new 60-pin card-edge connector.  Pin 45 carries the board's sound to the cartridge, pin 46 brings it back.")
    s.note("Dump circuit: with the CPU and PPU sockets empty, Pico C reads the cartridge through shift registers and hands the data to Pico A.")
    s.note("The six 74HCT595 run from +5V_SW and take the 3.3 V signals of Pico C through 470 ohm.")
    s.note("Their outputs can be switched on only while DIP switch 1 is set to emulation AND Pico C raises C_DUMP_EN (Q with its source on the switch).")
    s.note("C_DUMP_EN also holds the CPU in reset (all its bus pins are released then).  A PPU cannot be switched off its bus, so every driver that")
    s.note("meets a PPU output has 1 k in series: the drivers put at most 5 mA into each pin of a PPU left in its socket by mistake.")
    s.note("The resistors do not cover PD0-7: a forced /RD sets the cartridge ROM against such a PPU.  Only the firmware's check for chips prevents that.")
    s.note("Pico C must hold its four lines to the 74HCT595 low whenever +5V_SW is off.")

    cart = {1: GND, 16: GND, 30: VSW, 31: VSW, 14: "CPU_RW", 15: "IRQ_N", 17: "PPU_RD_N", 18: "CIRAM_A10",
            32: "M2", 44: "ROMSEL_N", 45: "CART_AUD_OUT", 46: "CART_AUD_RET", 47: "PPU_WR_N", 48: "CIRAM_CE_N", 49: "PA13_N"}
    cart.update({2 + k: f"CA{11 - k}" for k in range(12)})          # 2..13 = A11..A0
    cart.update({33: "CA12", 34: "CA13", 35: "CA14"})
    cart.update({36 + k: f"CART_D{7 - k}" for k in range(8)})        # 36..43 = D7..D0
    cart.update({19 + k: f"PA{6 - k}" for k in range(7)})            # 19..25 = PA6..PA0
    cart.update({50 + k: f"PA{7 + k}" for k in range(7)})            # 50..56 = PA7..PA13
    cart.update({26: "PD0", 27: "PD1", 28: "PD2", 29: "PD3", 57: "PD7", 58: "PD6", 59: "PD5", 60: "PD4"})
    assert sorted(cart) == list(range(1, 61))
    s.ic("J8", "FC_CART60", "ED60BGFBK (60-pin card edge, 2.54 mm)", "fcjamma:Famicom_Cart_60", JLCX, P.usex("cart60"),
         pins={f"P{n}": net for n, net in cart.items()},
         note="made for 1.57 mm cards; its fit with Famicom cartridges has to be tried with a sample before the order")
    P.C(s, "100n", VSW, GND)
    P.C(s, "10u", VSW, GND)

    # address and control drivers
    oe, rck = "D_OE_N", "D_RCLK"
    sr595(s, "U10", "74HCT595 (CPU A0-7)", VSW, "D_SER", "D_SRCLK_F", rck, oe, bits("CA", 8), "D_CA_Q7S")
    sr595(s, "U11", "74HCT595 (CPU A8-15)", VSW, "D_CA_Q7S", "D_SRCLK_F", rck, oe, bits("CA", 8, 8),
          note="the CPU address lines are driven directly: some cartridges load them with several 74LS inputs")
    sr595(s, "U12", "74HCT595 (PPU A0-7)", VSW, "D_SER", "D_SRCLK_F", rck, oe, bits("DQ_PA", 8), "D_PA_Q7S")
    sr595(s, "U13", "74HCT595 (PPU A8-13)", VSW, "D_PA_Q7S", "D_SRCLK_F", rck, oe, bits("DQ_PA", 6, 8) + [NC, NC])
    sr595(s, "U14", "74HCT595 (control)", VSW, "D_SER", "D_SRCLK_S", rck, oe,
          ["DQ_CPU_RW", "DQ_PPU_RD_N", "DQ_PPU_WR_N", "LATCH_OE_N", "DQ_M2", "D_OE_DATA_N", NC, NC], "D_CTL_Q7S",
          note="QA R/W, QB PPU /RD, QC PPU /WR, QD latch off, QE M2, QF low = U15 drives the data bus")
    sr595(s, "U15", "74HCT595 (data to cartridge)", VSW, "D_CTL_Q7S", "D_SRCLK_S", rck, "D_OE_DATA_N", bits("DQ_D", 8),
          note="drives the data bus only while a mapper register is being written")
    P.RA_many(s, "1k", [(f"DQ_PA{i}", f"PA{i}") for i in range(14)] + [("DQ_PPU_RD_N", "PPU_RD_N"), ("DQ_PPU_WR_N", "PPU_WR_N")],
              note="every dump driver that meets an output of the PPU: at most 5 mA if a PPU is in its socket by mistake")
    P.R(s, "470", "DQ_CPU_RW", "CPU_RW")
    P.R(s, "470", "DQ_M2", "M2", note="M2 for the cartridge in emulation mode, a full 5 V swing")
    for i in range(8):
        P.R(s, "470", f"DQ_D{i}", f"CART_D{i}", note="at most 10 mA per line if a cartridge ROM drives the bus at the same time; "
            "the firmware writes mapper registers at a ROM address that holds the same value, so that no bit fights")
    P.R(s, "10k", "D_OE_DATA_N", VSW, note="U15 off whenever U14 is off")

    # the drivers can be switched on only while DIP switch 1 says emulation and Pico C asks for it
    P.R(s, "10k", "DUMP_OE_N", V33, note="outputs off unless the transistor pulls the line low; 3.3 V is a valid high level for a 74HCT input")
    P.nfet(s, "DUMP_EN_G", "DUMP_OE_N", "I_DIP1",
           note="source on DIP switch 1: with the switch off (real chips) the source is not grounded and the outputs stay off")
    P.R(s, "47k", "DUMP_OE_N", "D_OE_N", note="while +5V_SW is off the /OE pins sit one diode above 0 V; this resistor keeps that from "
        "pulling DIP switch 1's line down through the transistor's body diode")
    P.C(s, "1n", "D_OE_N", GND, note="with the 47 k: no edge on the gate can couple a pulse into the /OE pins; the outputs follow C_DUMP_EN after about 60 us")
    P.nfet(s, "DUMP_EN_G", "CPU_RST_N", GND,
           note="holds the CPU in reset whenever Pico C enables the dump drivers: in reset the 2A03 releases all of its bus pins")
    P.R(s, "100", "C_DUMP_EN", "DUMP_EN_G")
    P.R(s, "1k", "DUMP_EN_G", GND, note="off while Pico C is in reset; low enough against the pad leakage of early RP2350 chips")
    for n in ("SER", "SRCLK_F", "SRCLK_S", "RCLK"):
        P.R(s, "470", f"C_{n}", f"D_{n}", note="limits the current if Pico C drives the line while +5V_SW is off")
    P.RA(s, "4.7k", [("D_SER", GND), ("D_SRCLK_F", GND), ("D_SRCLK_S", GND), ("D_RCLK", GND)],
         note="defined levels while Pico C is in reset")
    P.R(s, "1k", "M2", "C_M2", note="Pico C only reads M2: a CPU that is fitted and out of reset makes it toggle")

    # data read-back, on the 3.3 V input chain (first two registers read by Pico C)
    P.RA_many(s, "10k", [(f"CART_D{i}", f"DI_CD{i}") for i in range(8)],
              note="limit the current into the 3.3 V inputs when the bus is at 5 V")
    P.RA_many(s, "10k", [(f"PD{i}", f"DI_PD{i}") for i in range(8)])
    sr165(s, "U16", "74HC165 (cartridge CPU data)", "IN_Q4", "IN_Q5", bits("DI_CD", 8))
    sr165(s, "U17", "74HC165 (cartridge PPU data)", "IN_Q5", "IN_Q6", bits("DI_PD", 8))
    P.R(s, "100", "IN_Q6", "IN_DATA")

    # mirroring sense for Pico C
    P.R(s, "47k", "CIRAM_A10", "C_CIRAM_A10")
    P.R(s, "47k", "C_CIRAM_A10", GND, note="half the level, read with Pico C's converter (the high level depends on what drives the line in the cartridge)")


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
    P.R(s, "100", "CSYNC", "SYNC_G")
    P.R(s, "1k", "SYNC_G", GND, note="output high (no sync) while Pico A is in reset")
    P.nfet(s, "SYNC_G", "SYNC_C", GND, note="inverts: Pico A outputs the sync pulses high")
    P.R(s, "470", V5, "SYNC_C")
    P.R(s, "100", "SYNC_C", "VID_SYNC")
    P.header(s, "J9", 1, 6, "RGB + sync (monitor / option)", {1: "VID_R", 2: "VID_G", 3: "VID_B", 4: "VID_SYNC", 5: GND, 6: V5})


# ====================================================================== audio
def sheet_audio(d):
    s = d.sheet("audio", "Audio: mixer, loop through the cartridge, power amplifier")
    s.note("Real-chip mode: 2A03 pins -> mixer (Famicom values) -> cartridge pin 45 -> cartridge -> pin 46 -> volume -> amplifier.")
    s.note("Emulation mode: Pico A's PWM output -> two RC stages -> volume -> amplifier.")
    s.note("The loudspeaker outputs are bridge-tied: JAMMA L is not ground.  The amplifier stays off until Pico C raises AMP_EN.")

    P.R(s, "100", "APU_AD1", GND)
    P.R(s, "100", "APU_AD2", GND)
    P.R(s, "20k", "APU_AD1", "APU_MIX", note="pulse channels")
    P.R(s, "12k", "APU_AD2", "APU_MIX", note="triangle, noise, DPCM")
    P.C(s, "1u", "APU_MIX", "AUD_INV")
    s.ic("U18", "LM358", "LM358", P.FP_SOIC8, JLC, P.use("C7950", "LM358"), pins={
        "INA+": "AUD_BIAS", "INA-": "AUD_INV", "OUTA": "AUD_PRE",
        "INB+": "AUD_BIAS", "INB-": "OPB_OUT", "OUTB": "OPB_OUT", "V+": VSW, "GND": GND},
        note="A: inverting mixer amplifier.  B: spare, wired as a follower of the bias voltage so that it stays quiet")
    P.decouple(s, "U18", VSW)
    P.R(s, "47k", "AUD_PRE", "AUD_INV")
    P.C(s, "220p", "AUD_PRE", "AUD_INV", note="15 kHz low-pass")
    P.R(s, "20k", VSW, "AUD_BIAS")
    P.R(s, "12k", "AUD_BIAS", GND, note="1.9 V bias, the middle of the LM358's output range on 5 V")
    P.C(s, "10u", "AUD_BIAS", GND)
    P.R(s, "1k", "AUD_PRE", GND, note="keeps the output stage sourcing current (no crossover distortion)")
    P.R(s, "100", "AUD_PRE", "CART_AUD_OUT")

    # return from the cartridge and PWM sound from Pico A
    P.R(s, "47k", "CART_AUD_RET", GND, note="defined level while no cartridge is inserted")
    P.C(s, "1u", "CART_AUD_RET", "AUD_RET_AC")
    P.R(s, "10k", "AUD_RET_AC", "AUD_SUM")
    P.R(s, "470", "AUD_PWM", "AUD_PWM_F1")
    P.C(s, "10n", "AUD_PWM_F1", GND)
    P.R(s, "470", "AUD_PWM_F1", "AUD_PWM_F2")
    P.C(s, "10n", "AUD_PWM_F2", GND, note="two stages, -3 dB at 12.7 kHz.  Keep the PWM frequency away from the amplifier's own "
        "200-300 kHz and its double (for example 350 kHz, or 650 kHz and above), or the two beat audibly")
    P.C(s, "1u", "AUD_PWM_F2", "AUD_PWM_AC")
    P.R(s, "10k", "AUD_PWM_AC", "AUD_SUM")
    s.lib("RV", "Device:R_Potentiometer_Trim", "10k (volume)", "fcjamma:Trimmer_Bourns_3362P", JLCX, P.usex("trimmer10k"),
          {1: GND, 2: "AMP_IN", 3: "AUD_SUM"}, ref="RV1",
          note="3362P: pin 2 is the wiper; clockwise moves it towards pin 3, so clockwise is louder")

    P.C(s, "1u", "AMP_IN", "AMP_INP", note="with the amplifier's own 10 k input resistor: 16 Hz high-pass")
    P.C(s, "1u", "AMP_INN", GND, note="the unused input gets the same capacitor so that both inputs settle alike")
    s.ic("U19", "PAM8302A", "PAM8302A", P.FP_MSOP8, JLCX, P.usex("amp"), pins={
        "IN+": "AMP_INP", "IN-": "AMP_INN", "/SD": "AMP_EN", "VDD": V5, "GND": GND,
        "VO+": "SPK_P", "VO-": "SPK_N", "NC": NC},
        note="class D, gain 15 (23.5 dB), 1.3 W into 8 ohm at 1 % distortion (1.5 W at 10 %); powered from +5V, not through the +5V_SW switch")
    P.decouple(s, "U19", V5)
    P.C(s, "1u", V5, GND, note="directly at pin 6")
    P.C(s, "10u", V5, GND)
    P.CT(s, "10u/16V", V5, GND)
    P.R(s, "470", "C_AMP_EN", "AMP_EN")
    P.R(s, "1k", "AMP_EN", GND, note="amplifier off while Pico C is in reset (also against the pad leakage of early RP2350 chips); "
        "on: 2.2 V, the amplifier needs 1.2 V.  The firmware switches it on after the supply has settled")
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
    s.note("Coin counter and lock-out coils: 5 V or 12 V types, switched to ground; each output has its own clamp, so the board needs no +12 V.")

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

    # DIP switch: 1 = chip mode (off: real CPU and PPU, on: emulation); 2-4 are read by the firmware.
    # Switch 1 is also the ground return of the transistor that enables the dump drivers (sheet cart).
    s.lib("SW", "Switch:SW_DIP_x04", "DS-04RP (DIP switch 4)", P.FP_DIPSW4, JLCX, P.usex("dipsw4"),
          {1: "I_DIP1", 2: "I_DIP2", 3: "I_DIP3", 4: "I_DIP4", 5: GND, 6: GND, 7: GND, 8: GND}, ref="SW3",
          note="1: off = CPU and PPU chips fitted, on = emulation (it also unlocks the dump drivers); 2-4: for the firmware")
    P.RA(s, "10k", [(f"I_DIP{i}", V33) for i in range(1, 5)])

    # signals from the Famicom half that Pico C reads slowly
    for n in ("OUT1", "OUT2"):
        P.R(s, "10k", n, f"I_{n}")
        P.R(s, "47k", f"I_{n}", GND, note="a game can signal the board through these two CPU outputs; the divider keeps 0.8 of the CPU's "
            "high level, and the 74HC165's input diode takes what exceeds 3.3 V")
    P.R(s, "10k", VSW, "I_5VSW")
    P.R(s, "20k", "I_5VSW", GND, note="lets Pico C check that +5V_SW really is on; the power switch pulls this bit low when it limits the current")

    sr165(s, "U20", "74HC165 (1P)", GND, "IN_Q1", [f"I_{n}" for n in names[0:8]])
    sr165(s, "U21", "74HC165 (2P)", "IN_Q1", "IN_Q2", [f"I_{n}" for n in names[8:16]])
    sr165(s, "U22", "74HC165 (start, coin, service)", "IN_Q2", "IN_Q3",
          ["I_START1", "I_START2", "I_COIN1", "I_COIN2", "I_SERVICE", "I_TEST", "I_TILT", "I_1P_B5"])
    sr165(s, "U23", "74HC165 (switches, status)", "IN_Q3", "IN_Q4",
          ["I_2P_B5", "I_DIP1", "I_DIP2", "I_DIP3", "I_DIP4", "I_OUT1", "I_OUT2", "I_5VSW"])

    # outputs: coin counters and coin lock-outs
    sr595(s, "U24", "74HC595 (JAMMA outputs)", V33, "OUT_SER", "IO_CLK", "IO_LATCH", "OUT_OE_N",
          ["CNT1_G", "CNT2_G", "LOCK1_G", "LOCK2_G", "GPO4", "GPO5", "GPO6", "GPO7"])
    P.R(s, "1k", "OUT_OE_N", V33, note="outputs stay off until Pico C has loaded the register; 1 k wins safely against the Pico pad's pull-down in reset")
    P.RA(s, "10k", [("CNT1_G", GND), ("CNT2_G", GND), ("LOCK1_G", GND), ("LOCK2_G", GND)])
    for g, drain in (("CNT1_G", "J_CNT1"), ("CNT2_G", "J_CNT2"), ("LOCK1_G", "J_LOCK1"), ("LOCK2_G", "J_LOCK2")):
        P.nfet(s, g, drain, GND, note="low-side switch for a 5 V or 12 V coil in the cabinet (never 24 V); not protected against a short to the coil supply")
        P.tvs15(s, drain, GND, note="takes the coil's turn-off current: nothing flows up to 15 V (coil supplies above that are not allowed), "
                 "the drain stays below 25 V (the transistor stands 30 V)")
    P.header(s, "J2", 1, 6, "spare outputs (option)", {1: "GPO4", 2: "GPO5", 3: "GPO6", 4: "GPO7", 5: V33, 6: GND})


# ====================================================================== microcontrollers
def pico(s, ref, value, gp, run, v33_tp, swclk, swdio, tp=None, note=""):
    pins = {f"GP{n}": gp.get(n, NC) for n in list(range(0, 23)) + [26, 27, 28]}
    pins.update({"VSYS": "VSYS", "VBUS": NC, "3V3": v33_tp, "3V3_EN": NC, "ADC_VREF": NC, "RUN": run, "AGND": GND,
                 "SWCLK": swclk, "SWDIO": swdio, "GND_D2": GND, "GND_TP1": GND,
                 "USB_DM": NC, "USB_DP": NC, "BOOTSEL": NC, "TP4": NC, "TP5": NC})
    pins.update(tp or {})
    pins.update({f"GND_{n}": GND for n in (3, 8, 13, 18, 23, 28, 38)})
    s.ic(ref, "PICO2", value, P.FP_PICO, JLCX, P.usex("pico2"), pins=pins, note=note)
    P.C(s, "10u", "VSYS", GND)
    P.testpoint(s, v33_tp)


def sheet_mcu(d):
    s = d.sheet("mcu", "Three Raspberry Pi Pico 2 modules, USB Type-C socket, links")
    s.note("Pico A (video): clock and reset for CPU and PPU, palette index and sprite bit in, RGB and sync out; the emulator in emulation mode.")
    s.note("Pico B (bus): watches the CPU's accesses to the PPU, replaces palette data on the PPU side, answers the controller reads.")
    s.note("Pico C (input/output and management): JAMMA inputs and outputs, coin and timer logic, cartridge dump, USB Type-C,")
    s.note("power switch of the Famicom half, and reprogramming of Pico A and Pico B through their debug pads.")
    s.note("The modules are soldered flat on the board.  The USB socket reaches Pico C through the pads under the module (TP2, TP3).")
    s.note("Use either the board's Type-C socket or Pico C's own Micro-USB socket, never both at once: they are the same two wires.")

    a = {0: "A_EXT0", 1: "A_EXT1", 2: "A_EXT2", 3: "A_EXT3", 4: "A_SPR", 5: "A_ALE",
         6: "R0", 7: "R1", 8: "R2", 9: "G0", 10: "G1", 11: "G2", 12: "G3", 13: "B0", 14: "B1", 15: "B2",
         16: "CSYNC", 17: "CLK", 18: "A_PPU_RST", 19: "A_MISO", 20: "C_MOSI", 21: "LINK_BA", 22: "C_SCK",
         26: "A_CPU_RST", 27: "AUD_PWM", 28: "VREF_PWM"}
    b = {**{i: f"B_CD{i}" for i in range(8)}, **{8 + i: f"B_OVR{i}" for i in range(8)},
         16: "B_CA0", 17: "B_CA1", 18: "B_CA2", 19: "B_RW", 20: "B_PPUCS", 21: "B_OE1", 22: "B_OE2",
         26: "B_OUT0", 27: "LINK_CB", 28: "B_TX"}
    c = {0: "C_SER", 1: "C_SRCLK_F", 2: "C_SRCLK_S", 3: "C_RCLK", 4: "C_DUMP_EN", 5: "C_SPARE", 6: "C_M2",
         7: "OUT_OE_N", 8: "IN_DATA", 9: "IO_LATCH", 10: "IO_CLK", 11: "OUT_SER",
         12: "C_SWCLK_A", 13: "C_SWDIO_A", 14: "C_SWCLK_B", 15: "C_SWDIO_B",
         16: "C_TX", 17: "C_RUN_A", 18: "C_SCK_O", 19: "C_MOSI_O", 20: "C_MISO", 21: "C_RUN_B", 22: "EN_5VSW",
         26: "ADC_5V", 27: "C_CIRAM_A10", 28: "C_AMP_EN"}
    pico(s, "U25", "Pico 2 A (video)", a, "RUN_A", "A_3V3", "SWCLK_A", "SWDIO_A")
    pico(s, "U26", "Pico 2 B (bus)", b, "RUN_B", "B_3V3", "SWCLK_B", "SWDIO_B")
    pico(s, "U27", "Pico 2 C (I/O, management)", c, "RUN_C", "C_3V3", "SWCLK_C", "SWDIO_C",
         tp={"USB_DM": "USB_DM", "USB_DP": "USB_DP", "BOOTSEL": "BOOTSEL_C"})

    # links between the modules, one series resistor per line
    P.R(s, "100", "B_TX", "LINK_BA", note="Pico B -> Pico A: palette and mask register writes")
    P.R(s, "100", "C_TX", "LINK_CB", note="Pico C -> Pico B: controller state for both players")
    P.R(s, "100", "C_SCK_O", "C_SCK")
    P.R(s, "100", "C_MOSI_O", "C_MOSI", note="Pico C -> Pico A: cartridge image, controller state, timer display")
    P.R(s, "100", "A_MISO", "C_MISO")

    # Pico C programs and resets the other two
    P.RA(s, "1k", [("C_SWCLK_A", "SWCLK_A"), ("C_SWDIO_A", "SWDIO_A"), ("C_SWCLK_B", "SWCLK_B"), ("C_SWDIO_B", "SWDIO_B")])
    P.R(s, "470", "C_RUN_A", "RUN_A")
    P.R(s, "470", "C_RUN_B", "RUN_B")
    P.RA(s, "4.7k", [("RUN_A", GND), ("RUN_B", GND)],
         note="Pico A and Pico B stay in reset (all pins released) unless Pico C holds their RUN lines high: "
              "they cannot drive the Famicom half while Pico C is in reset, being programmed, or keeps +5V_SW off")
    for n in ("RUN_A", "RUN_B", "C_SPARE"):
        P.testpoint(s, n)
    P.header(s, "J16", 1, 3, "debug probe for Pico C (option)", {1: "SWCLK_C", 2: GND, 3: "SWDIO_C"})
    P.tact(s, "SW4", "RUN_C", GND, note="RESET: restarts Pico C, which then restarts the whole board")
    P.tact(s, "SW5", "BOOTSEL_C", GND,
           note="BOOT: held down while RESET is pressed, it makes Pico C appear as a USB drive for a firmware update; keep the track short")

    # USB Type-C socket for firmware updates
    s.ic("J10", "USB_C_16P", "USB Type-C socket (TYPE-C-31-M-12)", P.FP_USBC, JLCX, P.usex("usbc"), pins={
        "VBUS_A4": "VBUS_USB", "VBUS_A9": "VBUS_USB", "VBUS_B4": "VBUS_USB", "VBUS_B9": "VBUS_USB",
        "CC1": "USB_CC1", "CC2": "USB_CC2", "DP_A6": "USB_DP", "DP_B6": "USB_DP", "DN_A7": "USB_DM", "DN_B7": "USB_DM",
        "SBU1": NC, "SBU2": NC, "GND_A1": GND, "GND_A12": GND, "GND_B1": GND, "GND_B12": GND, "SHIELD": GND})
    P.R(s, "5.1k", "USB_CC1", GND)
    P.R(s, "5.1k", "USB_CC2", GND, note="tell a Type-C host that a device is attached; without them it supplies no power")
    P.header(s, "J11", 1, 4, "USB lines (option)", {1: "VBUS_USB", 2: "USB_DM", 3: "USB_DP", 4: GND},
             note="for a USB socket on the cabinet's panel")


def selfcheck(d):
    """Polarity and pin facts taken straight from the makers' datasheets.

    They repeat what the symbols and the helper functions already say, on purpose: a slip in a
    symbol or a helper (a swapped pin number, a reversed diode) passes every other check.
    Pin numbers here are pad numbers of the footprint.  Returns the list of facts that do not hold;
    tools/build.py reports them with its other findings.
    """
    def pin(ref, n):
        return d.parts[ref].conn.get(str(n)) if ref in d.parts else None

    def by_value(value):
        return [p for p in d.parts.values() if p.value == value and not p.dnp]

    facts = []
    # TPS2553DBV (TI SLVS841): 1 IN, 2 GND, 3 EN, 4 /FAULT, 5 ILIM, 6 OUT
    facts += [(pin("U29", 1) == V5, "U29 pad 1 (IN) on +5V"), (pin("U29", 6) == VSW, "U29 pad 6 (OUT) on +5V_SW"),
              (pin("U29", 2) == GND, "U29 pad 2 on GND"), (pin("U29", 3) == "SW_EN", "U29 pad 3 (EN)")]
    # SMAJ15A: pad 1 of D_SMA is the cathode (banded end); it is the pad on the coil line
    tvs = by_value("SMAJ15A")
    facts += [(len(tvs) == 4, "four coil clamps")]
    facts += [(p.conn["2"] == GND and p.conn["1"].startswith("J_"), f"{p.ref}: cathode on the coil line, anode on GND") for p in tvs]
    # S8550 in SOT-23 (JSCJ): 1 base, 2 emitter, 3 collector; the follower's collector is on GND
    facts += [(p.conn["3"] == GND and p.conn["2"] == "VBUF", f"{p.ref}: PNP follower, emitter VBUF, collector GND") for p in by_value("S8550")]
    facts += [(len(by_value("S8550")) == 1, "one PNP")]
    # AO3400A in SOT-23: 1 gate, 2 source, 3 drain; no gate may sit on a supply rail
    facts += [(p.conn["1"] not in (V5, VSW, V33, GND), f"{p.ref}: gate is a signal") for p in by_value("AO3400A")]
    # 3362P trimmer: pad 2 is the wiper; pad 3 is the clockwise end (Bourns 3362 data sheet)
    facts += [(pin("RV1", 2) == "AMP_IN" and pin("RV1", 1) == GND and pin("RV1", 3) == "AUD_SUM", "RV1: wiper to the amplifier, clockwise is louder")]
    # LMV7219 in SOT-23-5: 1 OUT, 2 V-, 3 +IN, 4 -IN, 5 V+; it must run from +3V3 (5.5 V is its absolute maximum)
    facts += [(pin("U9", 5) == V33 and pin("U9", 2) == GND, "U9 supply is +3V3")]
    # diodes (pad 1 = cathode): SS54 clamps a reversed supply, the two SS14 feed VSYS
    facts += [(p.conn["1"] == V5 and p.conn["2"] == GND, f"{p.ref}: SS54 cathode on +5V") for p in by_value("SS54")]
    facts += [(p.conn["1"] == "VSYS", f"{p.ref}: SS14 cathode on VSYS") for p in by_value("SS14")]
    # polarised capacitors: pad 1 is the positive pad and never on GND
    facts += [(p.conn["1"] != GND, f"{p.ref}: positive pad") for p in d.parts.values() if p.lib_id == "Device:C_Polarized"]
    # the dump drivers' enable: pull-up to +3V3 and the series resistor of the interlock are both present
    nets = d.nets()
    facts += [(any(r.startswith("Q") for r, _ in nets.get("DUMP_OE_N", [])) and len(nets.get("D_OE_N", [])) == 7,
               "interlock: the transistor is on DUMP_OE_N, and D_OE_N has only the five /OE pins, the 47 k and the 1 nF")]
    return [text for ok, text in facts if not ok]


def build():
    d = Design("fcjamma", "Famicom JAMMA board", rev="0.3")
    symbols.define(d)
    sheet_power(d)
    sheet_cpu(d)
    sheet_ppu(d)
    sheet_cart(d)
    sheet_video(d)
    sheet_audio(d)
    sheet_jamma(d)
    sheet_mcu(d)

    # parts that JLCPCB fits and that are not schematic parts
    d.extra(JLCX, P.usex("dip40_socket"), "40-pin IC socket, round pins", 2,
            "soldered by JLCPCB; the donor's CPU and PPU are plugged in afterwards", refs="U1 U6")
    d.failed_facts = selfcheck(d)
    return d, ["GND", "+5V", "VSYS"]
