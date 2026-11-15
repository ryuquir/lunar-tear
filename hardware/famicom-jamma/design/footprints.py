"""The board's own footprints (kicad/fcjamma.pretty).  tools/build.py writes them on every build.

Coordinates: millimetres, KiCad's footprint frame (X to the right, Y downward, seen from the parts side).
Every dimension below names its source.  The sources were read, and each value checked a second time by an
independent reader, on 2026-11-15; the full record (quotes, measurements, open points) is
research_notes/ファミコン JAMMA 基板 仕様調査/footprint_specs.md.

Five footprints:
  JAMMA_Edge_56      J1   the 56-way gold-finger edge of this board (no part is fitted)
  Famicom_Cart_60    J8   WingTAT ED60BGFBK 60-way 2.54 mm card-edge slot (C5173310), Famicom numbering
  Trimmer_Bourns_3362P RV1 BOCHEN 3362P-1-103 trimmer (C118956), Bourns 3362P pin pattern
  SW_DIP_x04_...     SW3  copy of KiCad's 4-way DIP switch with 1.0 mm holes for HRO DS-04RP (C92645)
  RaspberryPi_Pico2_SMD_TP7KeepOut  U25-U27  copy of KiCad's Pico SMD footprint with the Pico 2 TP7 keep-out
"""
import os

from fcgen import footprint_out as F
from fcgen.sexpr import find, first

KICAD_FP = "/usr/share/kicad/footprints"

JAMMA = "JAMMA_Edge_56"
CART = "Famicom_Cart_60"
TRIM = "Trimmer_Bourns_3362P"
DIP = "SW_DIP_x04_HRO_DS-04RP_W7.62mm_P2.54mm_Drill1.0mm"
PICO = "RaspberryPi_Pico2_SMD_TP7KeepOut"

# The JLCPCB part each footprint was drawn for (tools/build.py checks that the circuit uses it with that part).
# None: the footprint is part of the bare board itself.
PART_OF = {JAMMA: None, CART: "C5173310", TRIM: "C118956", DIP: "C92645", PICO: "C41407547"}

SILK_MIN = 0.15        # JLCPCB legend: 'Minimum Line Width ≥0.15mm', text height ≥1.0 mm, pad to silkscreen 0.15 mm


# ---------------------------------------------------------------------------------------------- JAMMA edge
# Sources: research sheet reference/02_jamma_interface.md 1.2.3 (22 design values) and 1.3 (JLCPCB gold fingers);
# JST GEC-561 'PC board layout (viewed from component side)'; Hirose CR7E drawing ADC-016737-72-02; Sullins EBM28D;
# JLCPCB help 'JLCPCB Gold Fingers' and 'Instructions for Chamfering Gold Fingers'.
# Origin: on the board tip line, at the centre of finger 1/A.  +X towards 28/f.  The board lies at negative Y.
JAMMA_PITCH = 3.96                 # 106.92 between 1 and 28 meets JST 106.92 ± 0.05 and Hirose 106.98 ± 0.08
JAMMA_FINGER = (2.30, 8.80)        # width: Hirose 2.3 ± 0.1, JST 2.3 ± 0.035; length: 1.2 to 10.0 from the tip
JAMMA_FINGER_Y = -5.6              # centre; copper 1.2 from the tip (JLCPCB 30° bevel set-back about 1.13)
JAMMA_LETTERS = "ABCDEFHJKLMNPRSTUVWXYZabcdef"   # solder side; G, I, O, Q are not used (Hirose, Sullins)
JAMMA_KEY_INDEX = 6                # position 7/H is the key slot
JAMMA_TONGUE = (-3.74, 110.66)     # 114.4 wide: inside JST's 114.4-114.6 at the JLCPCB outline tolerance of ±0.2
JAMMA_KEY = (23.76, 3.0, 11.5)     # key slot centre, width, depth: covers every key (Sullins 2.36, Hirose CR1 2.0)
JAMMA_SHOULDER = -12.0             # body wider than the tongue from 12 mm up: the housing's ears reach 10.5


def jamma_edge():
    names = [(i, str(i + 1), JAMMA_LETTERS[i]) for i in range(28) if i != JAMMA_KEY_INDEX]
    fp = F.Footprint(JAMMA, "JAMMA 56-way card edge of this board: 2x27 gold fingers 2.30 x 8.80, pitch 3.96, 1.2-10.0 mm from the tip, "
                     "1-28 on F.Cu, A-f on B.Cu, 7/H key slot; the tongue (114.4 x 12) and the key slot (3.0 x 11.5) are drawn on "
                     "Edge.Cuts by the board generator; mates JST GEC, Hirose CR7E-56 and Sullins EBM28D",
                     "JAMMA card edge gold finger 3.96mm 56",
                     attr=("exclude_from_pos_files", "exclude_from_bom", "allow_soldermask_bridges"),
                     ref_at=(-7.5, -13.4), value_at=(53.46, -11.2))
    for i, num, letter in names:
        x = JAMMA_PITCH * i
        fp.pad(num, "connect", "rect", (x, JAMMA_FINGER_Y), JAMMA_FINGER, ["F.Cu", "F.Mask"])
        fp.pad(letter, "connect", "rect", (x, JAMMA_FINGER_Y), JAMMA_FINGER, ["B.Cu", "B.Mask"])
    x0, x1 = -4.24, 111.16              # the tongue plus 0.5 mm on each side
    for layer in ("F.Mask", "B.Mask"):  # JLCPCB: 'The gold finger area must have the solder mask fully opened'
        fp.rect((x0, 0.5), (x1, -10.5), layer, width=0, fill=True)
    band = lambda y0, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    # the bevelled strip ('this area can not have copper'), the contact band (fingers only), the finger roots (no vias)
    fp.keepout(["F.Cu", "B.Cu"], band(0.5, -1.2), "JAMMA tip: no copper")
    fp.keepout(["F.Cu", "B.Cu"], band(-1.2, -9.0), "JAMMA contact band: fingers only", pads=False)
    fp.keepout(["F.Cu", "B.Cu"], band(-9.0, -11.0), "JAMMA finger roots: no vias or pour", tracks=False, pads=False)
    for layer in ("F.CrtYd", "B.CrtYd"):
        fp.rect((x0, 0.5), (x1, JAMMA_SHOULDER), layer, width=0.05)
    kx, kw, kd = JAMMA_KEY
    t0, t1 = JAMMA_TONGUE
    fp.polyline([(t0, JAMMA_SHOULDER), (t0, -0.5), (t0 + 0.5, 0), (kx - kw / 2 - 0.5, 0), (kx - kw / 2, -0.5), (kx - kw / 2, -kd),
                 (kx + kw / 2, -kd), (kx + kw / 2, -0.5), (kx + kw / 2 + 0.5, 0), (t1 - 0.5, 0), (t1, -0.5), (t1, JAMMA_SHOULDER)],
                "F.Fab", 0.10, closed=True)
    for text, x in (("1", -2.4), ("28", 109.3), ("JAMMA PARTS SIDE 1-28", 53.46)):
        fp.text(text, (x, -13.4), "F.SilkS", 1.2, 0.18)
    for text, x in (("A", -2.4), ("f", 109.3), ("SOLDER SIDE A-f", 53.46)):
        fp.text(text, (x, -13.4), "B.SilkS", 1.2, 0.18, mirror=True)
    fp.line((-6.15, -15.0), (113.07, -15.0), "Cmts.User", 0.10)
    fp.text("THT parts beyond this line (>= 5 mm from the fingers)", (53.46, -15.8), "Cmts.User", 1.0, 0.15)
    return fp.tree()


# ---------------------------------------------------------------------------------------------- cartridge slot
# Sources: WingTAT drawing 'EDxxxBGFBK' Rev A (LCSC/JLCPCB C5173310); NESdev wiki 'Cartridge connector' ('Pins 01-30 are
# on the label side of the cartridge, left to right'); OpenFC HVC-CPU-07 board file (slot row 1-30 towards the console
# front, 31 behind 1); NESdev 'Famicom cartridge dimensions' (HVC-TGROM-01: power pads at 1, 16, 30 and 31).
# The part is symmetric and has no pin 1: only this footprint sets the numbering.
# Origin: the centre of the 2 x 30 hole array (= the body and the slot).  Pins 1-30, the cartridge LABEL side, are on the
# row at +Y, pin 1 at -X; pins 31-60 at -Y, 31 behind 1.
CART_PITCH, CART_ROWS = 2.54, 5.08          # maker: 2.54 ± 0.05, rows 5.08 ± 0.05 apart, not staggered
CART_DRILL, CART_PAD = 1.00, 1.70           # maker: hole Ø1.00 ± 0.15 for 0.65 x 0.40 tails; ring 0.35
CART_BODY = (82.49, 9.25)                   # maker: 82.49 x 9.25, 15.60 high; slot 79.04 x 2.00, 9.00 deep


def cart_xy(n):
    if n <= 30:
        return -36.83 + CART_PITCH * (n - 1), CART_ROWS / 2
    return -36.83 + CART_PITCH * (n - 31), -CART_ROWS / 2


def cart60():
    fp = F.Footprint(CART, "WingTAT ED60BGFBK (LCSC C5173310) 60-way 2.54 mm card-edge slot, vertical THT, rows 5.08; Famicom numbering: "
                     "1-30 = cartridge label side (+Y), pin 1 at -X, 31 behind 1 (NESdev 'Cartridge connector'); the part itself is "
                     "symmetric and either way round is acceptable", "Famicom cartridge slot card edge 2x30 P2.54mm ED60BGFBK",
                     attr=("through_hole",), ref_at=(0, -6.0), value_at=(0, 7.6))
    for n in range(1, 61):
        fp.pad(n, "thru_hole", "rect" if n == 1 else "circle", cart_xy(n), (CART_PAD, CART_PAD), ["*.Cu", "*.Mask"], drill=CART_DRILL)
    bx, by = CART_BODY[0] / 2, CART_BODY[1] / 2
    fp.rect((-41.40, -4.78), (41.40, 4.78), "F.SilkS", SILK_MIN)
    fp.poly([(-36.83, 5.00), (-37.48, 6.10), (-36.18, 6.10)], "F.SilkS")            # points at pad 1
    for text, at in (("1", (-38.60, 5.70)), ("30", (36.83, 5.70)), ("31", (-36.83, -5.70)), ("60", (36.83, -5.70))):
        fp.text(text, at, "F.SilkS", 1.0, 0.15)
    fp.text("CART LABEL", (0, 6.00), "F.SilkS", 1.2, 0.20)                            # the cartridge's label faces +Y
    fp.poly([(-bx, -by), (bx, -by), (bx, by), (-bx + 1.0, by), (-bx, by - 1.0)], "F.Fab", 0.10, fill=False)   # chamfer: pin 1 / label
    fp.rect((-39.52, -1.00), (39.52, 1.00), "F.Fab", 0.10)                           # the card slot
    for s in (-1, 1):                                                                # end feet (about 1.5 mm, measured)
        fp.rect((s * 38.85, -3.75), (s * 40.37, 3.75), "F.Fab", 0.10)
    fp.text("${REFERENCE}", (0, 0), "F.Fab", 1.0, 0.15)
    fp.rect((-41.75, -6.85), (41.75, 6.85), "F.CrtYd", 0.05)                         # body + 0.5, and the silk legends
    fp.rect((-39.20, -0.60), (39.20, 0.60), "Dwgs.User", 0.10)                       # a 1.2 mm Famicom card in the slot
    fp.rect((-54.0, -8.5), (54.0, 8.5), "Dwgs.User", 0.10)                           # cartridge shell, about 108 x 17
    fp.text("cartridge shell about 108 x 17 (provisional; measure a real one)", (0, -9.4), "Dwgs.User", 1.0, 0.15)
    return fp.tree()


# ---------------------------------------------------------------------------------------------- trimmer
# Sources: BOCHEN 3362P approval sheet (LCSC/JLCPCB C118956, drawing p.3); Bourns 3362 datasheet REV. 03/25;
# LCSC/EasyEDA footprint RES-ADJ-TH_3362P for C118956 (same pin pattern and origin).
# Origin: the centre of the pads' bounding box (as LCSC/EasyEDA), the marking edge ('1 3362 3') at +Y.
# Pin 2 is the wiper.  Bourns: clockwise moves the wiper towards pin 3 (BOCHEN's sheet gives no direction).
TRIM_PADS = {"1": (-2.54, 1.27), "2": (0.0, -1.27), "3": (2.54, 1.27)}
TRIM_DRILL, TRIM_PAD = 0.90, 1.60           # leads ø0.5 (BOCHEN), 0.46 ± 0.03 (Bourns); no maker hole size; ring 0.35


def trimmer():
    fp = F.Footprint(TRIM, "Trimmer 1/4 in square, single turn, top adjust: BOCHEN 3362P-1-103 (LCSC C118956), Bourns 3362P pin pattern "
                     "(pins 1 and 3 5.08 apart, pin 2 offset 2.54); origin = centre of the pads as LCSC's footprint; clockwise moves "
                     "the wiper (2) towards pin 3 (Bourns)", "trimmer potentiometer 3362P top adjust THT",
                     attr=("through_hole",), ref_at=(0, 6.0), value_at=(0, 7.4))
    for num, at in TRIM_PADS.items():
        if num == "1":
            fp.pad(num, "thru_hole", "roundrect", at, (TRIM_PAD, TRIM_PAD), ["*.Cu", "*.Mask"], drill=TRIM_DRILL, rratio=0.25)
        else:
            fp.pad(num, "thru_hole", "circle", at, (TRIM_PAD, TRIM_PAD), ["*.Cu", "*.Mask"], drill=TRIM_DRILL)
    fp.rect((-3.45, -2.23), (3.45, 4.87), "F.Fab", 0.10)                             # BOCHEN body 6.9 x 7.1 (with the tabs)
    fp.circle((0, 0.97), 2.0, "F.Fab", 0.10)                                         # the rotor
    fp.line((-1.385, 0.97), (1.385, 0.97), "F.Fab", 0.10)
    fp.line((0, -0.415), (0, 2.355), "F.Fab", 0.10)
    fp.circle((-2.70, 2.85), 0.40, "F.Fab", 0.10)                                    # the dot printed on the part (pin 1)
    fp.text("${REFERENCE}", (0, 3.95), "F.Fab", 0.8, 0.12)
    fp.rect((-3.60, -2.38), (3.60, 5.02), "F.SilkS", SILK_MIN)
    fp.poly([(-3.95, 1.27), (-4.55, 0.92), (-4.55, 1.62)], "F.SilkS")              # points at pad 1
    # clockwise arrow around the rotor (R 5.0 about (0, 0.97), from -120° to -62°) and '+' at its end: louder
    fp.arc((-2.500, -3.360), (-0.087, -4.029), (2.347, -3.445), "F.SilkS", SILK_MIN)
    fp.poly([(3.078, -2.970), (2.512, -3.754), (2.183, -3.136)], "F.SilkS")
    fp.line((3.50, -3.40), (4.50, -3.40), "F.SilkS", SILK_MIN)
    fp.line((4.00, -3.90), (4.00, -2.90), "F.SilkS", SILK_MIN)
    fp.line((-4.10, -3.90), (-3.10, -3.90), "F.SilkS", SILK_MIN)
    fp.rect((-4.70, -4.30), (4.70, 5.15), "F.CrtYd", 0.05)                           # body + 0.25, and the silk marks
    return fp.tree()


# ---------------------------------------------------------------------------------------------- DIP switch (copy)
# Sources: HRO drawing 'MULTIFUNCTIONAL SWITCHES' DS-□□□□ REV. A (LCSC/JLCPCB C92645): hole Ø0.97 ± 0.05, pitch 2.54,
# rows 7.62 ± 0.1, leads 0.60 x 0.20, body 9.60 x 11.72; the maker numbers only the switches.  KiCad's pad n faces
# pad 9-n, so switch n joins pad n (I_DIPn) to pad 9-n (GND) when the part's '1' is at pads 1/8 and 'ON' over pads 5-8.
DIP_LIB = os.path.join(KICAD_FP, "Button_Switch_THT.pretty", "SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm.kicad_mod")
DIP_DRILL, DIP_PAD = 1.00, 1.70             # JLCPCB finishes a 1.0 drill at 0.92-1.13, around the maker's 0.97


def widen_silk(tree):
    """Raise silkscreen strokes to JLCPCB's minimum line width."""
    for x in tree:
        if isinstance(x, list) and x and x[0].startswith("fp_"):
            layer = first(x, "layer")
            stroke = first(x, "stroke")
            if layer and str(layer[1]) in ("F.SilkS", "B.SilkS") and stroke:
                w = first(stroke, "width")
                if float(w[1]) < SILK_MIN:
                    w[1] = str(SILK_MIN)


def dip_switch():
    def edit(tree):
        for p in find(tree, "pad"):
            first(p, "drill")[1] = "1"
            size = first(p, "size")
            size[1] = size[2] = "1.7"
            rr = first(p, "roundrect_rratio")
            if rr:
                rr[1] = "0.147059"                       # 0.25 mm corner radius, KiCad's convention for 1.7 mm pads
        widen_silk(tree)
        crt = [x for x in find(tree, "fp_rect") if str(first(x, "layer")[1]) == "F.CrtYd"]
        assert len(crt) == 1
        first(crt[0], "start")[1:] = ["-3.05", "-2.67"]   # also covers the switch numbers and 'ON'
        first(crt[0], "end")[1:] = ["11.62", "10.29"]
    tree = F.derive(DIP_LIB, DIP, "4-way slide DIP switch, rows 7.62, pitch 2.54, for HRO DS-04RP (LCSC C92645): KiCad's "
                    "SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm with 1.0 mm holes (maker: Ø0.97) and 1.7 mm lands; "
                    "switch n joins pad n to pad 9-n; fit the part with 'ON' over pads 5-8 and its '1' at pads 1 and 8", edit)
    extra = F.Footprint(DIP, "")
    extra.text("ON", (10.2, 3.81), "F.SilkS", 1.0, 0.15)
    extra.line((9.5, 5.2), (10.9, 5.2), "F.SilkS", SILK_MIN)
    extra.line((10.9, 5.2), (10.5, 4.9), "F.SilkS", SILK_MIN)
    extra.line((10.9, 5.2), (10.5, 5.5), "F.SilkS", SILK_MIN)
    for i in range(4):
        extra.text(str(i + 1), (-2.2, 2.54 * i), "F.SilkS", 1.0, 0.15)
    insert_before_pads(tree, extra.items)
    return tree


# ---------------------------------------------------------------------------------------------- Pico 2 (copy)
# Sources: Raspberry Pi Pico 2 datasheet (Release 5) Figures 3, 5 and 6, and its STEP model RP-009061-CA: every pad of
# KiCad's footprint matches; TP7 (1V1, new on the Pico 2, must not be soldered) is at (+1.0, -5.0) from the module centre.
# KiCad's footprint already keeps copper 0.2 mm off TP7 (two 1.9 mm zones on F.Cu and F.Paste); this copy replaces them with
# one 2.5 mm circle on F.Cu and F.Mask, so that no copper and no mask opening can sit under TP7.
PICO_LIB = os.path.join(KICAD_FP, "Module.pretty", "RaspberryPi_Pico_SMD.kicad_mod")
PICO_TP7, PICO_TP7_R = (1.0, -5.0), 1.25
PICO_TP7_ZONE = "TP7 keep-out"


def pico2():
    def edit(tree):
        for z in find(tree, "zone"):
            tree.remove(z)
        for g in find(tree, "group"):        # their member lists name the library's identifiers, which add_uuids() renews
            tree.remove(g)
        widen_silk(tree)
        zone = F.keepout_zone(["F.Cu", "F.Mask"], F.circle_points(PICO_TP7, PICO_TP7_R), PICO_TP7_ZONE)
        idx = next(i for i, x in enumerate(tree) if isinstance(x, list) and x and x[0] in ("embedded_fonts", "model"))
        tree.insert(idx, zone)
    return F.derive(PICO_LIB, PICO, "Raspberry Pi Pico 2 soldered flat (reflow), KiCad's RaspberryPi_Pico_SMD with the module's TP7 "
                    "(1.1 V, Pico 2 only, at +1.0/-5.0) under a 2.5 mm keep-out on F.Cu and F.Mask: no copper and no mask "
                    "opening there (Pico 2 datasheet, Figure 5)", edit)


def insert_before_pads(tree, items):
    idx = next(i for i, x in enumerate(tree) if isinstance(x, list) and x and x[0] == "pad")
    tree[idx:idx] = items


# ---------------------------------------------------------------------------------------------- library and facts
BUILDERS = {JAMMA: jamma_edge, CART: cart60, TRIM: trimmer, DIP: dip_switch, PICO: pico2}


def write_library(libdir):
    """Write every footprint; return {name: expected} for tools/check_footprints.py and the list of failed facts."""
    os.makedirs(libdir, exist_ok=True)
    for f in os.listdir(libdir):
        if f.endswith(".kicad_mod"):
            os.remove(os.path.join(libdir, f))
    expected, trees = {}, {}
    for name, build in BUILDERS.items():
        tree = build()
        F.write(tree, libdir)
        trees[name] = tree
        expected[name] = F.expected(tree)
    return expected, facts(expected, trees)


def _pads(exp, name):
    return {k: v[0] for k, v in exp[name]["pads"].items() if not k.startswith("(no number)")}


def facts(exp, trees):
    """Statements from the sources, checked on what was drawn.  Each failure is a build problem."""
    out = []
    j = _pads(exp, JAMMA)
    numbers = [str(n) for n in range(1, 29) if n != 7]
    letters = [c for c in JAMMA_LETTERS if c != "H"]
    out += [(sorted(j) == sorted(numbers + letters), "JAMMA: 54 fingers, 1-28 and A-f without 7 and H"),
            (all(j[n]["layers"] == ["F.Cu", "F.Mask"] and j[c]["layers"] == ["B.Cu", "B.Mask"] for n, c in zip(numbers, letters)),
             "JAMMA: 1-28 on the parts side, A-f on the solder side, no paste"),
            (all(abs(j[n]["x"] - j[c]["x"]) < 1e-9 for n, c in zip(numbers, letters)), "JAMMA: each letter is behind its number"),
            (abs(j["28"]["x"] - j["1"]["x"] - 106.92) < 1e-6, "JAMMA: 1 to 28 is 106.92 (JST 106.92 ± 0.05, Hirose 106.98 ± 0.08)"),
            (all(abs(j[n]["y"] + j[n]["h"] / 2 + 1.2) < 1e-6 and abs(j[n]["y"] - j[n]["h"] / 2 + 10.0) < 1e-6 for n in numbers),
             "JAMMA: fingers from 1.2 to 10.0 mm above the tip"),
            (all(j[n]["kind"] == "connect" for n in j), "JAMMA: edge-connector pads (copper and mask, never paste)")]
    c = _pads(exp, CART)
    out += [(sorted(c, key=int) == [str(n) for n in range(1, 61)], "cartridge: pads 1-60"),
            (all(abs(c[str(n + 30)]["x"] - c[str(n)]["x"]) < 1e-9 and abs(c[str(n)]["y"] - c[str(n + 30)]["y"] - 5.08) < 1e-9
                 for n in range(1, 31)), "cartridge: pin n + 30 directly behind pin n, rows 5.08 apart"),
            (c["1"]["x"] < 0 < c["1"]["y"], "cartridge: pin 1 at the left of the label row (+Y)"),
            (abs(c["30"]["x"] - c["1"]["x"] - 73.66) < 1e-6, "cartridge: 30 contacts at 2.54"),
            (all((p["w"] - p["drill"]) / 2 >= 0.25 for p in c.values()), "cartridge: annular ring at least 0.25 (JLCPCB)"),
            (all(0.85 <= p["drill"] - 0.08 and p["drill"] + 0.13 <= 1.15 + 1e-9 for p in c.values()),
             "cartridge: the finished hole (+0.13/-0.08) stays inside the maker's Ø1.00 ± 0.15")]
    t = _pads(exp, TRIM)
    out += [(sorted(t) == ["1", "2", "3"] and abs(t["3"]["x"] - t["1"]["x"] - 5.08) < 1e-9 and abs(t["1"]["y"] - t["2"]["y"] - 2.54) < 1e-9,
             "trimmer: pins 1 and 3 5.08 apart, pin 2 2.54 towards the far edge (Bourns 3362P)"),
            (all(p["drill"] - 0.08 - 0.55 >= 0.2 for p in t.values()), "trimmer: the smallest finished hole clears a 0.55 lead by 0.2")]
    d = _pads(exp, DIP)
    out += [(sorted(d) == [str(n) for n in range(1, 9)] and all(p["drill"] == 1.0 and p["w"] == 1.7 for p in d.values()),
             "DIP switch: 8 pads, 1.0 mm holes, 1.7 mm lands"),
            (all(abs(d[str(n)]["y"] - d[str(9 - n)]["y"]) < 1e-9 and abs(d[str(9 - n)]["x"] - d[str(n)]["x"] - 7.62) < 1e-9 for n in range(1, 5)),
             "DIP switch: pad n faces pad 9 - n across 7.62")]
    lib = F.expected(F.derive(PICO_LIB, "x", "", lambda tr: None))
    pz = exp[PICO]
    out += [(pz["pads"] == lib["pads"], "Pico 2: every pad is KiCad's, unchanged"),
            (pz["keepouts"] == 1 and abs(pz["keepout_boxes"][0][0] - (PICO_TP7[0] - PICO_TP7_R)) < 1e-3
             and abs(pz["keepout_boxes"][0][3] - (PICO_TP7[1] + PICO_TP7_R)) < 1e-3, "Pico 2: one 2.5 mm keep-out centred on TP7"),
            (not any(abs(p["x"] - PICO_TP7[0]) < PICO_TP7_R + p["w"] / 2 and abs(p["y"] - PICO_TP7[1]) < PICO_TP7_R + p["h"] / 2
                     for k, v in pz["pads"].items() for p in v if any(l in ("F.Cu", "F.Mask", "*.Cu", "*.Mask") for l in p["layers"])),
             "Pico 2: no pad reaches the TP7 keep-out")]
    for name, tree in trees.items():
        for x in tree:
            if isinstance(x, list) and x and x[0].startswith("fp_") and str(first(x, "layer")[1]) in ("F.SilkS", "B.SilkS"):
                st = first(x, "stroke")
                if st is not None and float(first(st, "width")[1]) < SILK_MIN and x[0] != "fp_poly":
                    out.append((False, f"{name}: a silkscreen line is thinner than JLCPCB's 0.15 mm"))
                    break
    return [text for ok, text in out if not ok], len(out)
