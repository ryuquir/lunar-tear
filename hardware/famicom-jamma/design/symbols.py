"""Symbols for the parts that are not taken from the KiCad library.

Each symbol is one box.  Pins are (number, name, type); type is one of
in / out / bi / tri / pas / pwr / pwo / oc (see tools/fcgen/model.py).

Pin numbers come from the verified reference sheets in
research_notes/ファミコン JAMMA 基板 仕様調査/reference/ (CPU, PPU, cartridge connector, JAMMA)
and from the manufacturers' data sheets (logic, SRAM, comparator, amplifier, modules).
A pin number is the name of the pad in the footprint, so it can be text ("A4", "TP6").

Pin types are chosen for the electrical rule check of this board, not as a general
library: a line that is driven by different parts in the two operating modes (for
example the CPU address bus, which the dump shift registers drive when the CPU socket
is empty) is declared three-state on both sides.
"""


def define(d):
    # ------------------------------------------------------------------ Famicom chips
    d.symdef("RP2A03", "U", [
        (29, "CLK", "in"), (3, "/RST", "in"), (30, "TST", "in"), (32, "/IRQ", "in"), (33, "/NMI", "in"), None,
        (31, "M2", "tri"), (34, "R/W", "tri"), None,
        (36, "/OE1", "out"), (35, "/OE2", "out"), (39, "OUT0", "out"), (38, "OUT1", "out"), (37, "OUT2", "out"), None,
        (1, "AD1", "out"), (2, "AD2", "out"), None,
        (28, "D0", "bi"), (27, "D1", "bi"), (26, "D2", "bi"), (25, "D3", "bi"),
        (24, "D4", "bi"), (23, "D5", "bi"), (22, "D6", "bi"), (21, "D7", "bi"),
    ], [
        (40, "VCC", "pwr"), (20, "GND", "pwr"), None,
        (4, "A0", "tri"), (5, "A1", "tri"), (6, "A2", "tri"), (7, "A3", "tri"), (8, "A4", "tri"), (9, "A5", "tri"),
        (10, "A6", "tri"), (11, "A7", "tri"), (12, "A8", "tri"), (13, "A9", "tri"), (14, "A10", "tri"),
        (15, "A11", "tri"), (16, "A12", "tri"), (17, "A13", "tri"), (18, "A14", "tri"), (19, "A15", "tri"),
    ], "Ricoh RP2A03 CPU and sound generator (NTSC), DIP-40, taken from the donor Famicom")

    d.symdef("RP2C02", "U", [
        (18, "CLK", "in"), (22, "/RST", "in"), None,
        (13, "/CS", "in"), (1, "R/W", "in"), (12, "A0", "in"), (11, "A1", "in"), (10, "A2", "in"), None,
        (2, "D0", "bi"), (3, "D1", "bi"), (4, "D2", "bi"), (5, "D3", "bi"),
        (6, "D4", "bi"), (7, "D5", "bi"), (8, "D6", "bi"), (9, "D7", "bi"), None,
        (14, "EXT0", "bi"), (15, "EXT1", "bi"), (16, "EXT2", "bi"), (17, "EXT3", "bi"), None,
        (19, "/INT", "oc"), (21, "VOUT", "out"),
    ], [
        (40, "VCC", "pwr"), (20, "GND", "pwr"), None,
        (39, "ALE", "tri"), (24, "/RD", "tri"), (23, "/WR", "tri"), None,
        (38, "AD0", "bi"), (37, "AD1", "bi"), (36, "AD2", "bi"), (35, "AD3", "bi"),
        (34, "AD4", "bi"), (33, "AD5", "bi"), (32, "AD6", "bi"), (31, "AD7", "bi"), None,
        (30, "PA8", "tri"), (29, "PA9", "tri"), (28, "PA10", "tri"), (27, "PA11", "tri"), (26, "PA12", "tri"), (25, "PA13", "tri"),
    ], "Ricoh RP2C02 picture processor (NTSC, composite output), DIP-40, taken from the donor Famicom")

    # ------------------------------------------------------------------ connectors
    left = [(n, f"P{n}", "pas") for n in range(1, 31)]
    right = [(n, f"P{n}", "pas") for n in range(31, 61)]
    d.symdef("FC_CART60", "J", left, right,
             "Famicom 60-pin cartridge connector; pin 1 is the left end of the front row seen from the player side, pin 31 is behind pin 1")

    comp = [n for n in range(1, 29) if n != 7]
    sold = [c for c in "ABCDEFHJKLMNPRSTUVWXYZabcdef" if c != "H"]
    d.symdef("JAMMA56", "J", [(str(n), f"C{n}", "pas") for n in comp], [(c, f"S{c}", "pas") for c in sold],
             "JAMMA 56-way edge connector made of gold fingers on this board; 1-28 parts side, A-f solder side, 7/H is the key slot")

    d.symdef("USB_C_16P", "J", [
        ("A4", "VBUS_A4", "pas"), ("A9", "VBUS_A9", "pas"), ("B4", "VBUS_B4", "pas"), ("B9", "VBUS_B9", "pas"), None,
        ("A5", "CC1", "pas"), ("B5", "CC2", "pas"), None,
        ("A6", "DP_A6", "pas"), ("B6", "DP_B6", "pas"), ("A7", "DN_A7", "pas"), ("B7", "DN_B7", "pas"), None,
        ("A8", "SBU1", "pas"), ("B8", "SBU2", "pas"),
    ], [("A1", "GND_A1", "pas"), ("A12", "GND_A12", "pas"), ("B1", "GND_B1", "pas"), ("B12", "GND_B12", "pas"), None, ("SH", "SHIELD", "pas")],
        "USB Type-C socket for USB 2.0, 16 contacts, surface mount; the pin numbers are the contact names of the Type-C standard")

    # ------------------------------------------------------------------ modules
    gp = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19, 15: 20,
          16: 21, 17: 22, 18: 24, 19: 25, 20: 26, 21: 27, 22: 29, 26: 31, 27: 32, 28: 34}
    d.symdef("PICO2", "U",
             [(gp[n], f"GP{n}", "bi") for n in range(0, 16)]
             + [None, ("D1", "SWCLK", "pas"), ("D3", "SWDIO", "pas"), None,
                ("TP2", "USB_DM", "pas"), ("TP3", "USB_DP", "pas"), ("TP6", "BOOTSEL", "pas"), ("TP4", "TP4", "pas"), ("TP5", "TP5", "pas")],
             [(39, "VSYS", "pwr"), (40, "VBUS", "pas"), (36, "3V3", "pas"), (37, "3V3_EN", "pas"), (35, "ADC_VREF", "pas"),
              (30, "RUN", "pas"), None]
             + [(gp[n], f"GP{n}", "bi") for n in (16, 17, 18, 19, 20, 21, 22, 26, 27, 28)]
             + [None, (33, "AGND", "pwr")] + [(n, f"GND_{n}", "pwr") for n in (3, 8, 13, 18, 23, 28, 38)]
             + [("D2", "GND_D2", "pwr"), ("TP1", "GND_TP1", "pas")],
             "Raspberry Pi Pico 2 (RP2350A) soldered flat on the board as a module.  1-40: the edge pads; D1-D3: the debug pads; "
             "TP1-TP6: the test pads on its underside (TP2/TP3 USB, TP6 BOOTSEL; TP4 and TP5 must not be used).  "
             "GP0-GP22 tolerate 5 V only while the module is powered, GP26-GP28 never do")

    # ------------------------------------------------------------------ logic (the same pin numbers for 74HC and 74HCT, DIP and SOIC)
    d.symdef("74x165", "U", [
        (1, "SH/LD", "in"), (2, "CLK", "in"), (15, "CLK_INH", "in"), (10, "SER", "in"), None,
        (11, "A", "in"), (12, "B", "in"), (13, "C", "in"), (14, "D", "in"), (3, "E", "in"), (4, "F", "in"), (5, "G", "in"), (6, "H", "in"),
    ], [(16, "VCC", "pwr"), (8, "GND", "pwr"), None, (9, "QH", "out"), (7, "/QH", "out")],
        "8-bit parallel-in serial-out shift register; SER -> A ... H -> QH, so H is read first")

    d.symdef("74x595", "U", [
        (14, "SER", "in"), (11, "SRCLK", "in"), (12, "RCLK", "in"), (10, "/SRCLR", "in"), (13, "/OE", "in"),
    ], [(16, "VCC", "pwr"), (8, "GND", "pwr"), None,
        (15, "QA", "tri"), (1, "QB", "tri"), (2, "QC", "tri"), (3, "QD", "tri"), (4, "QE", "tri"), (5, "QF", "tri"), (6, "QG", "tri"), (7, "QH", "tri"),
        None, (9, "QH'", "out")],
        "8-bit serial-in shift register with output latch and three-state outputs; the first bit shifted in ends at QH")

    d.symdef("74x138", "U", [
        (1, "A", "in"), (2, "B", "in"), (3, "C", "in"), None, (6, "G1", "in"), (4, "/G2A", "in"), (5, "/G2B", "in"),
    ], [(16, "VCC", "pwr"), (8, "GND", "pwr"), None,
        (15, "/Y0", "out"), (14, "/Y1", "out"), (13, "/Y2", "out"), (12, "/Y3", "out"),
        (11, "/Y4", "out"), (10, "/Y5", "out"), (9, "/Y6", "out"), (7, "/Y7", "out")],
        "3-to-8 line decoder")

    d.symdef("74x00", "U", [
        (1, "1A", "in"), (2, "1B", "in"), None, (4, "2A", "in"), (5, "2B", "in"), None,
        (9, "3A", "in"), (10, "3B", "in"), None, (12, "4A", "in"), (13, "4B", "in"),
    ], [(14, "VCC", "pwr"), (7, "GND", "pwr"), None, (3, "1Y", "out"), (6, "2Y", "out"), (8, "3Y", "out"), (11, "4Y", "out")],
        "quad 2-input NAND gate")

    d.symdef("74x573", "U", [
        (1, "/OE", "in"), (11, "LE", "in"), None,
        (2, "D0", "in"), (3, "D1", "in"), (4, "D2", "in"), (5, "D3", "in"), (6, "D4", "in"), (7, "D5", "in"), (8, "D6", "in"), (9, "D7", "in"),
    ], [(20, "VCC", "pwr"), (10, "GND", "pwr"), None,
        (19, "Q0", "tri"), (18, "Q1", "tri"), (17, "Q2", "tri"), (16, "Q3", "tri"), (15, "Q4", "tri"), (14, "Q5", "tri"), (13, "Q6", "tri"), (12, "Q7", "tri")],
        "octal transparent latch with three-state outputs (LE high = transparent); inputs on one side, outputs on the other")

    # ------------------------------------------------------------------ memory
    # ISSI's data sheet numbers the TSOP like the SOP (its corner pin, next to the dot, is called 22).
    # The footprint numbers the pads from that corner, so: pad = (data sheet number - 22) mod 28 + 1.
    sop = {"A14": 1, "A12": 2, "A7": 3, "A6": 4, "A5": 5, "A4": 6, "A3": 7, "A2": 8, "A1": 9, "A0": 10,
           "IO0": 11, "IO1": 12, "IO2": 13, "GND": 14, "IO3": 15, "IO4": 16, "IO5": 17, "IO6": 18, "IO7": 19,
           "/CE": 20, "A10": 21, "/OE": 22, "A11": 23, "A9": 24, "A8": 25, "A13": 26, "/WE": 27, "VDD": 28}
    pad = {name: (n - 22) % 28 + 1 for name, n in sop.items()}
    assert (pad["/OE"], pad["VDD"], pad["A3"], pad["A2"], pad["GND"], pad["A10"]) == (1, 7, 14, 15, 21, 28)
    d.symdef("IS62C256AL_TSOP", "U",
             [(pad[f"A{i}"], f"A{i}", "in") for i in range(15)] + [None, (pad["/CE"], "/CE", "in"), (pad["/OE"], "/OE", "in"), (pad["/WE"], "/WE", "in")],
             [(pad["VDD"], "VDD", "pwr"), (pad["GND"], "GND", "pwr"), None] + [(pad[f"IO{i}"], f"IO{i}", "bi") for i in range(8)],
             "ISSI IS62C256AL-45TLI 32K x 8 static RAM, 5 V, 45 ns, 28-pin TSOP type I.  The numbers are the pads of the footprint, "
             "counted from the corner with the dot (/OE); the data sheet's own figure uses the numbers of the SOP instead")

    # ------------------------------------------------------------------ analogue
    d.symdef("LM358", "U", [
        (3, "INA+", "in"), (2, "INA-", "in"), None, (5, "INB+", "in"), (6, "INB-", "in"),
    ], [(8, "V+", "pwr"), (4, "GND", "pwr"), None, (1, "OUTA", "out"), None, (7, "OUTB", "out")],
        "dual operational amplifier, single supply")

    d.symdef("LMV7219", "U", [(3, "+IN", "in"), (4, "-IN", "in")],
             [(5, "V+", "pwr"), (2, "V-", "pwr"), None, (1, "OUT", "out")],
             "TI LMV7219 comparator, 7 ns, 2.7-5 V, push-pull rail-to-rail output, SOT-23-5; inputs work from -0.2 V to V+ - 1.2 V")

    d.symdef("PAM8302A", "U", [(3, "IN+", "in"), (4, "IN-", "in"), None, (1, "/SD", "in")],
             [(6, "VDD", "pwr"), (7, "GND", "pwr"), None, (5, "VO+", "out"), (8, "VO-", "out"), None, (2, "NC", "pas")],
             "Diodes PAM8302A 2.5 W class-D amplifier, MSOP-8, bridge-tied outputs (never ground an output); /SD low = off")

    d.symdef("CJ431", "U", [(REF431["ref"], "REF", "in")], [(REF431["k"], "K", "pas"), (REF431["a"], "A", "pas")],
             "CJ431 adjustable shunt reference (2.5 V), SOT-23")


# SOT-23 pin numbers of the CJ431 (JSCJ).  They differ between makers of the 431, so they are
# kept in one place; the values are filled from the manufacturer's drawing (see README, part facts).
REF431 = {"k": 2, "ref": 1, "a": 3}
