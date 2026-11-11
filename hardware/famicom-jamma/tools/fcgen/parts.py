"""Helpers for the common small parts, with their JLCPCB Basic part numbers.

Every LCSC number used here is checked against data/jlcpcb_basic_parts_2026-11-10.csv
by tools/build.py: the build fails if a number is not in the Basic list, or if the
value written here does not appear in JLCPCB's own description of that number.

JLCPCB charges a loading fee for every distinct part on a Standard PCBA order (this board
needs Standard PCBA because of the gold fingers), so the tables below are kept short on
purpose: prefer a value that is already used over a new one.
"""
from .model import JLC, AKI, DONOR, PCB, NC

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_RA = "Resistor_SMD:R_Array_Convex_4x0603"
FP_TANT_A = "Capacitor_Tantalum_SMD:CP_EIA-3216-18_Kemet-A"
FP_TANT_B = "Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SOD123 = "Diode_SMD:D_SOD-123"
FP_SMA = "Diode_SMD:D_SMA"
FP_SMB = "Diode_SMD:D_SMB"
FP_SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_SOIC16 = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
FP_SOP32 = "Package_SO:SOP-32_11.305x20.495mm_P1.27mm"
FP_SOT223 = "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
FP_DIP8_SOCKET = "Package_DIP:DIP-8_W7.62mm_Socket"
FP_DIP14 = "Package_DIP:DIP-14_W7.62mm"
FP_DIP16 = "Package_DIP:DIP-16_W7.62mm"
FP_DIP20 = "Package_DIP:DIP-20_W7.62mm"
FP_DIP40_SOCKET = "Package_DIP:DIP-40_W15.24mm_Socket"
FP_PICO = "Module:RaspberryPi_Pico_Common_THT"
FP_HDR = "Connector_PinHeader_2.54mm:PinHeader_{r}x{n:02d}_P2.54mm_Vertical"
FP_SOCKET = "Connector_PinSocket_2.54mm:PinSocket_1x{n:02d}_P2.54mm_Vertical"
FP_TP = "TestPoint:TestPoint_Pad_D1.5mm"
FP_SW_TACT = "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_FB = "Inductor_SMD:L_0603_1608Metric"

# value -> (LCSC number, text that must appear in JLCPCB's description)
R0603 = {
    "33": ("C23140", "33Ω"), "100": ("C22775", "100Ω"), "470": ("C23179", "470Ω"),
    "1k": ("C21190", "1kΩ"), "5.1k": ("C23186", "5.1kΩ"), "10k": ("C25804", "10kΩ"),
    "12k": ("C22790", "12kΩ"), "20k": ("C4184", "20kΩ"), "47k": ("C25819", "47kΩ"),
    "100k": ("C25803", "100kΩ"),
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
    "MMBT3904": ("C20526", "Transistor_BJT:MMBT3904", FP_SOT23, "MMBT3904"),
    "AO3400A": ("C20917", "Transistor_FET:AO3400A", FP_SOT23, "AO3400A"),
    "AO3401A": ("C15127", "Transistor_FET:AO3401A", FP_SOT23, "AO3401A"),
    "1N4148W": ("C81598", "Diode:1N4148W", FP_SOD123, "1N4148W"),
    "SS14": ("C2480", "Diode:SS14", FP_SMA, "SS14"),
    "SS54": ("C22452", "Device:D_Schottky", FP_SMA, "SS54"),
    "SMBJ6.5CA": ("C7420377", "Device:D_TVS", FP_SMB, "SMBJ6.5CA"),
    "PSM712": ("C32677", "Device:D_TVS_Dual_AAC", FP_SOT23, "PSM712"),
    "AMS1117-3.3": ("C6186", "Regulator_Linear:AMS1117-3.3", FP_SOT223, "AMS1117-3.3"),
    "LED-R": ("C2286", "Device:LED", FP_LED, "KT-0603R"),
    "TS-1187A": ("C318884", "Switch:SW_Push", FP_SW_TACT, "TS-1187A"),
    "BLM18PG121": ("C14709", "Device:FerriteBead", FP_FB, "BLM18PG121SN1D"),
}
USED_CODES = {}   # LCSC number -> expected text, filled as parts are created


def use(code, text):
    USED_CODES[code] = text
    return code


def R(sh, value, a, b, dnp=False, note=""):
    code, text = R0603[value]
    return sh.lib("R", "Device:R", value, FP_R, JLC, use(code, text), {1: a, 2: b}, dnp, note, horizontal=True)


def C(sh, value, a, b, dnp=False, note=""):
    code, text = C0603[value]
    return sh.lib("C", "Device:C", value, FP_C, JLC, use(code, text), {1: a, 2: b}, dnp, note, horizontal=True)


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


def npn(sh, b, c, e, note=""):
    return semi(sh, "Q", "MMBT3904", {1: b, 2: e, 3: c}, note=note)


def nfet(sh, g, d, s, note=""):
    return semi(sh, "Q", "AO3400A", {1: g, 2: s, 3: d}, note=note)


def pfet(sh, g, d, s, note=""):
    return semi(sh, "Q", "AO3401A", {1: g, 2: s, 3: d}, note=note)


def diode(sh, name, anode, cathode, dnp=False, note=""):
    return semi(sh, "D", name, {1: cathode, 2: anode}, dnp, note)


def tvs(sh, a, b, note=""):
    return semi(sh, "D", "SMBJ6.5CA", {1: a, 2: b}, note=note)


def tvs2(sh, line1, line2, common, note=""):
    """PSM712: pins 1 and 2 are the two lines, pin 3 is the common (ground) pin."""
    return semi(sh, "D", "PSM712", {1: line1, 2: line2, 3: common}, note=note)


def led(sh, anode, cathode, note=""):
    return semi(sh, "D", "LED-R", {1: cathode, 2: anode}, note=note)


def tact(sh, ref, a, b, note=""):
    code, lib_id, fp, text = SEMI["TS-1187A"]
    return sh.lib("SW", lib_id, "TS-1187A", fp, JLC, use(code, text), {1: a, 2: b}, False, note, ref=ref)


def ferrite(sh, a, b, note=""):
    return semi(sh, "FB", "BLM18PG121", {1: a, 2: b}, note=note, value="120R@100MHz 2A")


def header(sh, ref, rows, n, value, conn, src=AKI, code="", dnp=False, note=""):
    if rows == 1:
        sym = f"Connector_Generic:Conn_01x{n:02d}"
    else:
        sym = f"Connector_Generic:Conn_{rows:02d}x{n:02d}_Odd_Even"
    fp = FP_HDR.format(r=rows, n=n)
    return sh.lib("J", sym, value, fp, src, code, conn, dnp, note, ref=ref)


def socket(sh, ref, n, value, conn, src=AKI, code="", dnp=False, note=""):
    return sh.lib("J", f"Connector_Generic:Conn_01x{n:02d}", value, FP_SOCKET.format(n=n), src, code, conn, dnp, note, ref=ref)


def testpoint(sh, net, name=None):
    return sh.lib("TP", "Connector:TestPoint", name or net, FP_TP, PCB, "", {1: net})
