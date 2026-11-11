"""Helpers for the common small parts, with their JLCPCB part numbers.

Every part that JLCPCB assembles is named here by its LCSC number:
- Basic parts (R0603, RARRAY, C0603, TANT, SEMI) are checked against
  data/jlcpcb_basic_parts_2026-11-10.csv,
- Extended parts (EXT) against data/jlcpcb_extended_parts.csv, which tools/jlc_parts.py
  refreshes from JLCPCB's parts library (stock, price, how the part is assembled).
tools/build.py fails if a number is missing from its list, or if the text written here
does not appear in JLCPCB's own description of that number.

JLCPCB charges a loading fee for every distinct part on a Standard PCBA order (this board
needs Standard PCBA because of the gold fingers), so the tables below are kept short on
purpose: prefer a value that is already used over a new one.
"""
from .model import JLC, JLCX, AKI, DONOR, PCB, NC

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_RA = "Resistor_SMD:R_Array_Convex_4x0603"
FP_TANT_A = "Capacitor_Tantalum_SMD:CP_EIA-3216-18_Kemet-A"
FP_TANT_B = "Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B"
FP_CP_6x8 = "Capacitor_SMD:CP_Elec_6.3x7.7"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SOT23_5 = "Package_TO_SOT_SMD:SOT-23-5"
FP_SOT23_6 = "Package_TO_SOT_SMD:SOT-23-6"
FP_SOD123 = "Diode_SMD:D_SOD-123"
FP_SMA = "Diode_SMD:D_SMA"
FP_SMB = "Diode_SMD:D_SMB"
FP_SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_SOIC16 = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
FP_SOIC20W = "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm"
FP_TSOP28 = "Package_SO:TSOP-I-28_11.8x8mm_P0.55mm"
FP_MSOP8 = "Package_SO:MSOP-8_3x3mm_P0.65mm"
FP_SOT223 = "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
FP_DIP40_SOCKET = "Package_DIP:DIP-40_W15.24mm_Socket"
FP_DIPSW4 = "Button_Switch_THT:SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm"
FP_PICO = "Module:RaspberryPi_Pico_SMD"
FP_USBC = "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
FP_FUSE2920 = "Fuse:Fuse_2920_7451Metric"
FP_HDR = "Connector_PinHeader_2.54mm:PinHeader_{r}x{n:02d}_P2.54mm_Vertical"
FP_TP = "TestPoint:TestPoint_Pad_D1.5mm"
FP_SJ2 = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
FP_SJ3 = "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm"
FP_SW_TACT = "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_FB = "Inductor_SMD:L_0603_1608Metric"

# ---- Basic parts: value -> (LCSC number, text that must appear in JLCPCB's description)
R0603 = {
    "33": ("C23140", "33Ω"), "100": ("C22775", "100Ω"), "470": ("C23179", "470Ω"),
    "1k": ("C21190", "1kΩ"), "5.1k": ("C23186", "5.1kΩ"), "10k": ("C25804", "10kΩ"),
    "12k": ("C22790", "12kΩ"), "20k": ("C4184", "20kΩ"), "47k": ("C25819", "47kΩ"),
}
RARRAY = {"1k": ("C20197", "1kΩ"), "4.7k": ("C1980", "4.7kΩ"), "10k": ("C29718", "10kΩ")}
C0603 = {
    "47p": ("C1671", "47pF"), "220p": ("C1603", "220pF"), "1n": ("C1588", "1nF"),
    "10n": ("C57112", "10nF"), "100n": ("C14663", "100nF"),
    "1u": ("C15849", "1uF"), "10u": ("C19702", "10uF"),
}
TANT = {"10u/16V": ("C7171", "10uF", FP_TANT_A), "100u/6.3V": ("C16133", "100uF", FP_TANT_B)}
# name -> (LCSC number, KiCad symbol, footprint, text that must appear in JLCPCB's part number)
SEMI = {
    "S8550": ("C105432", "Transistor_BJT:MMBT3906", FP_SOT23, "S8550"),     # PNP; SOT-23 pins as the MMBT3906: 1 B, 2 E, 3 C
    "AO3400A": ("C20917", "Transistor_FET:AO3400A", FP_SOT23, "AO3400A"),
    "SS14": ("C2480", "Diode:SS14", FP_SMA, "SS14"),
    "SS54": ("C22452", "Device:D_Schottky", FP_SMA, "SS54"),
    "SMBJ6.5CA": ("C7420377", "Device:D_TVS", FP_SMB, "SMBJ6.5CA"),
    "AMS1117-3.3": ("C6186", "Regulator_Linear:AMS1117-3.3", FP_SOT223, "AMS1117-3.3"),
    "LED-R": ("C2286", "Device:LED", FP_LED, "KT-0603R"),
    "TS-1187A": ("C318884", "Switch:SW_Push", FP_SW_TACT, "TS-1187A"),
    "BLM18PG121": ("C14709", "Device:FerriteBead", FP_FB, "BLM18PG121SN1D"),
}
USED_CODES = {}   # Basic: LCSC number -> expected text, filled as parts are created

# ---- Extended parts: name -> (LCSC number, text that must appear in the maker's part number, text of the package)
EXT = {
    "pico2": ("C41407547", "Raspberry Pi Pico 2", ""),
    "dip40_socket": ("C2874018", "IC254V-12-40", "DIP-40"),
    "cart60": ("C5173310", "ED60BGFBK", "2.54mm"),
    "sram": ("C47143", "IS62C256AL-45TLI", "TSOP"),
    "74HCT138": ("C5965", "74HCT138D", "SOIC-16"),
    "74HCT00": ("C6764", "SN74HCT00DR", "SOIC-14"),
    "74HCT573": ("C5209384", "74HCT573D", "SOIC-20"),
    "74HC165": ("C5613", "74HC165D", "SOIC-16"),
    "74HCT595": ("C282339", "74HCT595D", "SOIC-16"),
    "comparator": ("C283912", "LMV7219M5X", "SOT-23-5"),
    "amp": ("C113367", "PAM8302AASCR", "MSOP-8"),
    "usbc": ("C165948", "TYPE-C-31-M-12", ""),
    "loadswitch": ("C55266", "TPS2553DBVR", "SOT-23-6"),
    "tvs15": ("C86819", "SMAJ15A", "SMA"),
    "polyfuse": ("C262042", "TLC-LSMD300D", "2920"),
    "cap470u": ("C46550400", "JVJ16V470M6x8", "6.3"),
    "dipsw4": ("C92645", "DS-04RP", "2.54mm"),
    "trimmer10k": ("C118956", "3362P-1-103", ""),
}
USED_EXT = {}     # Extended: LCSC number -> (expected part number text, expected package text)


def use(code, text):
    USED_CODES[code] = text
    return code


def usex(name):
    code, text, package = EXT[name]
    USED_EXT[code] = (text, package)
    return code


def R(sh, value, a, b, dnp=False, note=""):
    code, text = R0603[value]
    return sh.lib("R", "Device:R", value, FP_R, JLC, use(code, text), {1: a, 2: b}, dnp, note, horizontal=True)


def C(sh, value, a, b, dnp=False, note="", at=""):
    code, text = C0603[value]
    return sh.lib("C", "Device:C", value, FP_C, JLC, use(code, text), {1: a, 2: b}, dnp, note, horizontal=True, at=at)


def decouple(sh, ref, rail, note=""):
    """The 100 nF capacitor of one IC, between its supply rail and ground.  The build checks that every IC has its own."""
    return C(sh, "100n", rail, "GND", note=note or f"at {ref}", at=ref)


def CT(sh, value, plus, minus, note=""):
    code, text, fp = TANT[value]
    return sh.lib("C", "Device:C_Polarized", value, fp, JLC, use(code, text), {1: plus, 2: minus}, False, note, horizontal=True)


def RA(sh, value, pairs, dnp=False, note=""):
    """Four-resistor array; pairs = [(a1, b1), ... up to 4]; unused elements are left open.

    Element k sits between pin k and pin 9-k (KiCad Device:R_Pack04 and the 0603x4 footprint).
    """
    code, text = RARRAY[value]
    if not 1 <= len(pairs) <= 4:
        raise ValueError("a resistor array has 1 to 4 elements")
    conn = {}
    for i in range(4):
        a, b = pairs[i] if i < len(pairs) else (NC, NC)
        conn[1 + i] = a
        conn[8 - i] = b
    return sh.lib("RN", "Device:R_Pack04", value, FP_RA, JLC, use(code, text), conn, dnp, note)


def RA_many(sh, value, pairs, dnp=False, note=""):
    """Any number of (a, b) pairs, packed four to an array."""
    return [RA(sh, value, pairs[i:i + 4], dnp, note) for i in range(0, len(pairs), 4)]


def semi(sh, prefix, name, conn, dnp=False, note="", value=None, horizontal=None, ref=None):
    code, lib_id, fp, text = SEMI[name]
    if horizontal is None:
        horizontal = len(conn) == 2
    return sh.lib(prefix, lib_id, value or name, fp, JLC, use(code, text), conn, dnp, note, ref=ref, horizontal=horizontal)


def nfet(sh, g, d, s, note=""):
    return semi(sh, "Q", "AO3400A", {1: g, 2: s, 3: d}, note=note)


def pnp(sh, b, c, e, note=""):
    return semi(sh, "Q", "S8550", {1: b, 2: e, 3: c}, note=note, value="S8550")


def diode(sh, name, anode, cathode, dnp=False, note=""):
    return semi(sh, "D", name, {1: cathode, 2: anode}, dnp, note)


def tvs(sh, a, b, note=""):
    return semi(sh, "D", "SMBJ6.5CA", {1: a, 2: b}, note=note)


def tvs15(sh, line, gnd, note=""):
    """SMAJ15A, one direction: nothing flows up to 15 V, it clamps between 16.7 V and 24.4 V.  Pin 1 is the cathode."""
    return sh.lib("D", "Device:D_Zener", "SMAJ15A", FP_SMA, JLCX, usex("tvs15"), {1: line, 2: gnd}, False, note, horizontal=True)


def led(sh, anode, cathode, note=""):
    return semi(sh, "D", "LED-R", {1: cathode, 2: anode}, note=note)


def tact(sh, ref, a, b, note=""):
    code, lib_id, fp, text = SEMI["TS-1187A"]
    return sh.lib("SW", lib_id, "TS-1187A", fp, JLC, use(code, text), {1: a, 2: b}, False, note, ref=ref)


def ferrite(sh, a, b, note=""):
    return semi(sh, "FB", "BLM18PG121", {1: a, 2: b}, note=note, value="120R@100MHz 2A")


def header(sh, ref, rows, n, value, conn, note=""):
    """A 2.54 mm pin header position that is left empty (an option to fit by hand)."""
    if rows == 1:
        sym = f"Connector_Generic:Conn_01x{n:02d}"
    else:
        sym = f"Connector_Generic:Conn_{rows:02d}x{n:02d}_Odd_Even"
    return sh.lib("J", sym, value, FP_HDR.format(r=rows, n=n), AKI, "", conn, True, note, ref=ref)


def solder_jumper2(sh, ref, value, a, b, note=""):
    """Two pads that are open until someone bridges them with solder."""
    return sh.lib("JP", "Jumper:SolderJumper_2_Open", value, FP_SJ2, PCB, "", {1: a, 2: b}, False, note, ref=ref)


def solder_jumper3(sh, ref, value, a, common, b, note=""):
    """Three pads; the board is made with a-common joined by a copper bridge that can be cut."""
    return sh.lib("JP", "Jumper:SolderJumper_3_Bridged12", value, FP_SJ3, PCB, "", {1: a, 2: common, 3: b}, False, note, ref=ref)


def testpoint(sh, net, name=None):
    return sh.lib("TP", "Connector:TestPoint", name or net, FP_TP, PCB, "", {1: net})
