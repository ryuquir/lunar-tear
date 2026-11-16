"""The board's own footprints (kicad/fcjamma.pretty).  tools/build.py writes them on every build.

Coordinates: millimetres, KiCad's footprint frame (X to the right, Y downward, seen from the parts side).
Every dimension below names its source.  The sources were read, and each value checked a second time by an
independent reader, on 2026-11-15; the full record (quotes, measurements, open points) is
research_notes/ファミコン JAMMA 基板 仕様調査/footprint_specs.md.

Seven footprints:
  JAMMA_Edge_56      J1   the 56-way gold-finger edge of this board (no part is fitted)
  Famicom_Cart_60    J8   WingTAT ED60BGFBK 60-way 2.54 mm card-edge slot (C5173310), Famicom numbering
  Trimmer_Bourns_3362P RV1 BOCHEN 3362P-1-103 trimmer (C118956), Bourns 3362P pin pattern
  SW_DIP_x04_...     SW3  copy of KiCad's 4-way DIP switch with 1.0 mm holes for HRO DS-04RP (C92645)
  RaspberryPi_Pico2_SMD_TP7KeepOut  U25-U27  copy of KiCad's Pico SMD footprint with the Pico 2 TP7 keep-out
  BreakLine_8h_D0.6mm_P0.9mm_KeepOut  MB*  mouse bites that join an edge rail to the board, with a 5 mm keep-out
  ToolingHole_2.0mm_NPTH              TH*  the edge rails' tooling holes

The keep-out areas carry names.  On a board whose project finds this library, KiCad 10.0.8's DRC does not report
vias (or other parts' pads) inside a footprint's keep-out, only tracks and pour; the rules in BOARD_RULES below,
which tools/build.py writes as kicad/fcjamma.kicad_dru, name the areas and do report them, and tools/check_rules.py
proves on a test board that each one fires.

facts() lists what the sources say, checked on what was drawn; every failure stops the build.
"""
import hashlib
import math
import os

from fcgen import footprint_out as F
from fcgen.sexpr import find, first, fmt

KICAD_FP = "/usr/share/kicad/footprints"

JAMMA = "JAMMA_Edge_56"
CART = "Famicom_Cart_60"
TRIM = "Trimmer_Bourns_3362P"
DIP = "SW_DIP_x04_HRO_DS-04RP_W7.62mm_P2.54mm_Drill1.0mm"
PICO = "RaspberryPi_Pico2_SMD_TP7KeepOut"
BREAK = "BreakLine_8h_D0.6mm_P0.9mm_KeepOut"
TOOL = "ToolingHole_2.0mm_NPTH"

# The JLCPCB part each footprint was drawn for (tools/build.py checks that the circuit uses it with that part).
# None: the footprint is part of the bare board itself.
PART_OF = {JAMMA: None, CART: "C5173310", TRIM: "C118956", DIP: "C92645", PICO: "C41407547", BREAK: None, TOOL: None}

SILK_MIN = 0.15        # JLCPCB legend: 'Minimum Line Width ≥0.15mm', 'Minimum text height 40 mil (1.0mm)', pad to silk 0.15


# ---------------------------------------------------------------------------------------------- JAMMA edge
# Sources: research sheet reference/02_jamma_interface.md 1.2.3 (22 design values) and 1.3 (JLCPCB gold fingers);
# JST GEC-561 'PC board layout (viewed from component side)'; Hirose CR7 catalogue 'PCB Dimensions 3.96 pitch' and drawing
# ADC-016737-72-02; Sullins EBM28D; JLCPCB help 'JLCPCB Gold Fingers' and 'Instructions for Chamfering Gold Fingers'.
# Origin: on the board tip line, at the centre of finger 1/A.  +X towards 28/f.  The board lies at negative Y.
JAMMA_PITCH = 3.96                 # 106.92 between 1 and 28 meets JST 106.92 ± 0.05 and Hirose 106.98 ± 0.08
JAMMA_SETBACK = 1.6                # no copper within 1.6 of the tip: JLCPCB's bevel reaches about 1.13 (30° on 1.6 mm); its ±5°, the
                                   # board's ±10 % and the routing's ±0.2 add about 0.36 (root-sum-square); JLCPCB is asked (3d)
JAMMA_FINGER = (2.30, 8.40)        # width: Hirose 2.3 ± 0.1 (JST prints '2.3 ±0.35 (.091 ±.001)'); length: 1.6 to 10.0 from the tip
JAMMA_FINGER_Y = -5.8              # centre; the mating contact touches 5.3 ± 0.4 from the tip (Hirose), well on the finger
JAMMA_LETTERS = "ABCDEFHJKLMNPRSTUVWXYZabcdef"   # solder side; G, I, O, Q are not used (Hirose, Sullins)
JAMMA_KEY_INDEX = 6                # position 7/H is the key slot
JAMMA_TONGUE = (-3.74, 110.66)     # 114.4 nominal, so that +0.2 routing never exceeds JST's 114.6 maximum (Hirose: 114.6-114.8)
JAMMA_KEY = (23.76, 3.0, 11.5)     # key slot centre, width, depth: covers every key (Sullins 2.36, Hirose CR1 2.0; Hirose slot 2.5 x 11)
JAMMA_SHOULDER = -12.0             # body wider than the tongue from 12 mm up: JST asks for a notch at least 10 deep; the housing's
                                   # face is 8.5 (Hirose) or 6.73 (Sullins) above the tip, its ears reach about 10.5 sideways
JAMMA_MASK_END = -10.1             # the open mask band ends 0.1 past the fingers, so that no track can run bare across it
JAMMA_TOP = -15.0                  # courtyard: no part within 15 mm of the tip (through-hole parts 5 mm from the fingers)
JAMMA_X = (-4.24, 111.16)          # the tongue plus 0.5 mm on each side
JAMMA_THT_X = (-6.15, 113.07)      # beside the tongue's root the courtyard widens to 5 mm past the outer fingers' copper


def jamma_edge():
    names = [(i, str(i + 1), JAMMA_LETTERS[i]) for i in range(28) if i != JAMMA_KEY_INDEX]
    fp = F.Footprint(JAMMA, "JAMMA 56-way card edge of this board: 2x27 gold fingers 2.30 x 8.40, pitch 3.96, 1.6-10.0 mm from the tip, "
                     "1-28 on F.Cu, A-f on B.Cu, 7/H key slot; the tongue (114.4 x 12) and the key slot (3.0 x 11.5) are drawn on "
                     "Edge.Cuts by the board generator; mates JST GEC, Hirose CR7E-56 and Sullins EBM28D",
                     "JAMMA card edge gold finger 3.96mm 56",
                     attr=("exclude_from_pos_files", "exclude_from_bom", "allow_soldermask_bridges"),
                     ref_at=(-7.5, -13.4), value_at=(53.46, -11.2))
    for i, num, letter in names:
        x = JAMMA_PITCH * i
        fp.pad(num, "connect", "rect", (x, JAMMA_FINGER_Y), JAMMA_FINGER, ["F.Cu", "F.Mask"])
        fp.pad(letter, "connect", "rect", (x, JAMMA_FINGER_Y), JAMMA_FINGER, ["B.Cu", "B.Mask"])
    x0, x1 = JAMMA_X
    for layer in ("F.Mask", "B.Mask"):  # JLCPCB: 'The gold finger area must have the solder mask fully opened'
        fp.rect((x0, 0.5), (x1, JAMMA_MASK_END), layer, width=0, fill=True)
    band = lambda y0, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    # the bevelled strip ('this area can not have copper'), the contact band (fingers only), the finger roots (no vias)
    fp.keepout(["F.Cu", "B.Cu"], band(0.5, -JAMMA_SETBACK), "JAMMA tip: no copper")
    fp.keepout(["F.Cu", "B.Cu"], band(-JAMMA_SETBACK, -9.0), "JAMMA contact band: fingers only", pads=False)
    fp.keepout(["F.Cu", "B.Cu"], band(-9.0, -11.0), "JAMMA finger roots: no vias or pour", tracks=False, pads=False)
    # courtyard: the tongue (0.5 wider on each side) and, where the body starts, 5 mm past the outer fingers' copper, so that
    # no part's courtyard can come within 5 mm of a finger beside the tongue's root either
    tx0, tx1 = JAMMA_THT_X
    crt = [(x0, 0.5), (x1, 0.5), (x1, JAMMA_SHOULDER), (tx1, JAMMA_SHOULDER), (tx1, JAMMA_TOP), (tx0, JAMMA_TOP),
           (tx0, JAMMA_SHOULDER), (x0, JAMMA_SHOULDER)]
    for layer in ("F.CrtYd", "B.CrtYd"):
        fp.poly(crt, layer, width=0.05, fill=False)
    kx, kw, kd = JAMMA_KEY
    t0, t1 = JAMMA_TONGUE
    fp.polyline([(t0, JAMMA_SHOULDER), (t0, -0.5), (t0 + 0.5, 0), (kx - kw / 2 - 0.5, 0), (kx - kw / 2, -0.5), (kx - kw / 2, -kd),
                 (kx + kw / 2, -kd), (kx + kw / 2, -0.5), (kx + kw / 2 + 0.5, 0), (t1 - 0.5, 0), (t1, -0.5), (t1, JAMMA_SHOULDER)],
                "F.Fab", 0.10, closed=True)
    for text, x in (("1", -2.4), ("28", 109.3), ("JAMMA PARTS SIDE 1-28", 53.46)):
        fp.text(text, (x, -13.4), "F.SilkS", 1.2, 0.18)
    for text, x in (("A", -2.4), ("f", 109.3), ("SOLDER SIDE A-f", 53.46)):
        fp.text(text, (x, -13.4), "B.SilkS", 1.2, 0.18, mirror=True)
    fp.line((JAMMA_THT_X[0], JAMMA_TOP), (JAMMA_THT_X[1], JAMMA_TOP), "Cmts.User", 0.10)
    fp.text("THT parts beyond this line (>= 5 mm from the fingers)", (53.46, JAMMA_TOP - 0.8), "Cmts.User", 1.0, 0.15)
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
# pad 9-n, so switch n joins pad n (I_DIPn) to pad 9-n (GND) when the part's '1' is at pads 1/8 and 'ON' over pads 5-8
# (JLCPCB's own footprint for C92645 also puts the switch numbers beside pads 1-4).
DIP_LIB = os.path.join(KICAD_FP, "Button_Switch_THT.pretty", "SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm.kicad_mod")
DIP_DRILL, DIP_PAD = 1.00, 1.70             # JLCPCB finishes a 1.0 drill at 0.92-1.13, around the maker's 0.97
DIP_BODY = (-0.99, -2.05, 8.61, 9.67)       # HRO body 9.60 x 11.72 centred on (3.81, 3.81)


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


def _inside(x, box):
    """Every point of a drawing lies inside the box (x0, y0, x1, y1)."""
    pts = [first(x, k) for k in ("start", "end", "center", "mid")] + (list(first(x, "pts")[1:]) if first(x, "pts") else [])
    pts = [(float(p[1]), float(p[2])) for p in pts if p is not None]
    return bool(pts) and all(box[0] <= px <= box[2] and box[1] <= py <= box[3] for px, py in pts)


def dip_switch():
    def edit(tree):
        for p in find(tree, "pad"):
            first(p, "drill")[1] = fmt(DIP_DRILL)
            size = first(p, "size")
            size[1] = size[2] = fmt(DIP_PAD)
            rr = first(p, "roundrect_rratio")
            if rr:
                rr[1] = fmt(round(0.25 / DIP_PAD, 6))          # 0.25 mm corner radius, KiCad's convention
        for x in [x for x in tree if isinstance(x, list) and x and x[0].startswith("fp_")]:
            # KiCad draws the switch levers on the silkscreen; under the fitted part they only print on bare board
            if str(first(x, "layer")[1]) == "F.SilkS" and _inside(x, DIP_BODY):
                tree.remove(x)
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
# one 2.5 mm circle on F.Cu and F.Mask.  Together with the board rules (BOARD_RULES) no copper and no mask opening can
# sit under TP7.
PICO_LIB = os.path.join(KICAD_FP, "Module.pretty", "RaspberryPi_Pico_SMD.kicad_mod")
PICO_TP7, PICO_TP7_R = (1.0, -5.0), 1.25
PICO_TP7_ZONE = "TP7 keep-out"

# The KiCad library files the two copies were checked against on 2026-11-15 (kicad-footprints 10.0.8): a library update
# must not change the copies unseen.
LIBRARY_SHA256 = {PICO_LIB: "b4b6e8c3f30d560dd69cf7306216269a72e45ccf906d4304ace34ee587040701",
                  DIP_LIB: "0a4713dac17ddbb198bb4ad25baf6bc76ea5dd1f1373d6d537704adbf1522847"}


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
                    "opening there (Pico 2 datasheet, Figure 5; enforced by the board rules in kicad/fcjamma.kicad_dru)", edit)


# ---------------------------------------------------------------------------------------------- edge rails
# Sources (read 2026-11-16): JLCPCB capabilities, 'Mouse bites Panel': 'Panel board spacing: 1.6 or 2 mm', 'Recommended
# diameter of mouse bite is 0.5mm-0.8mm; Recommended distance between the two mouse-bites is 0.2-0.3mm', 'For breakaway
# with mouse-bites, the minimum width is 5mm', 'For SMT assembly at JLCPCB, use 5 mm tooling edges, 2 mm tooling holes,
# and 1 mm fiducials centered at 3.85 mm from the panel edges'.  JLCPCB's mouse-bite guide (updated 2026-11-10): '5 to 8
# holes with a diameter of 0.60 mm', 'hole edge to hole edge 0.35-0.4 mm. A minimum spacing of 0.3 mm'.  Holes of 0.6 that
# are 0.3 apart meet both pages.  (KiCad's own Panelization library uses 0.5 holes at 0.85.)
# Break line: 8 holes along Y, centred on the origin, spanning 6.9.  design/board.py puts the line on the body's side of
# the edge, the holes touching the edge from inside (0.3 in), so that the stubs left after breaking stay inside the
# outline, and turns it by 180° on the right-hand rail.  The tab is wider than the line at the body's edge, so a thin web
# is left at each end of the line; it breaks with the rest.  The keep-out (+X, the board's side) keeps parts, pads, vias,
# tracks and pour 5 mm away from every hole, where snapping the rail bends the board; board rules make the DRC report
# vias, pads and parts in it.
BREAK_D, BREAK_P, BREAK_N = 0.6, 0.9, 8
BREAK_ZONE = "Breakaway tab: keep clear"
BREAK_KEEP = (-0.3, 5.3, 8.5)              # from the board's edge (0.3 behind the holes) to 5 mm past them, and 5 mm past the end holes
TOOL_D = 2.0                               # tooling hole (JLCPCB: '2 mm tooling holes')


def break_line():
    fp = F.Footprint(BREAK, "Mouse bites joining an edge rail to the board (JLCPCB): 8 holes of 0.6 at 0.9 (0.3 apart), not plated, "
                     "for a tab between 2 mm slots; keep-out 5 mm around the holes on the board's side (+X): no parts, pads, vias, "
                     "tracks or pour",
                     "mousebite break line edge rail tab JLCPCB",
                     attr=("board_only", "exclude_from_pos_files", "exclude_from_bom"), ref_at=(2.0, 0), value_at=(3.0, 0))
    for k in range(BREAK_N):
        fp.pad("", "np_thru_hole", "circle", (0, BREAK_P * (k - (BREAK_N - 1) / 2)), (BREAK_D, BREAK_D), ["*.Cu", "*.Mask"],
               drill=BREAK_D)
    half = BREAK_P * (BREAK_N - 1) / 2 + BREAK_D / 2 + 0.1
    for layer in ("F.CrtYd", "B.CrtYd"):
        fp.rect((-BREAK_D / 2 - 0.05, -half), (BREAK_D / 2 + 0.05, half), layer, width=0.05)
    x0, x1, h = BREAK_KEEP
    fp.keepout(["F.Cu", "B.Cu"], [(x0, -h), (x1, -h), (x1, h), (x0, h)], BREAK_ZONE, footprints=True)
    fp.rect((x0, -h), (x1, h), "Cmts.User", 0.10)
    return fp.tree()


def tooling_hole():
    fp = F.Footprint(TOOL, "Tooling hole of an edge rail: 2.0 mm, not plated, centred on the 5 mm rail (JLCPCB: '5 mm tooling edges, "
                     "2 mm tooling holes')", "tooling hole NPTH edge rail JLCPCB",
                     attr=("board_only", "exclude_from_pos_files", "exclude_from_bom"), ref_at=(0, -2.0), value_at=(0, 2.0))
    fp.pad("", "np_thru_hole", "circle", (0, 0), (TOOL_D, TOOL_D), ["*.Cu", "*.Mask"], drill=TOOL_D)
    for layer in ("F.CrtYd", "B.CrtYd"):
        fp.circle((0, 0), TOOL_D / 2 + 0.25, layer, width=0.05)
    return fp.tree()


def insert_before_pads(tree, items):
    idx = next(i for i, x in enumerate(tree) if isinstance(x, list) and x and x[0] == "pad")
    tree[idx:idx] = items


# ---------------------------------------------------------------------------------------------- board rules
# Written by tools/build.py as kicad/fcjamma.kicad_dru.  Each rule was tried with kicad-cli 10.0.8, and tools/check_rules.py
# proves on every build that it reports a probe placed where it forbids.  The JLCPCB rules (capabilities page, read
# 2026-11-15: 'Pad To Silkscreen 0.15mm', 'Pad Hole-to-Hole Spacing 0.45mm', 'PTH annular ring ... Recommended 0.25 mm')
# only make KiCad's defaults stricter; the silkscreen rule leaves out paste-only stencil openings, which are not copper.
# The mouse bites (references MB*) are 0.3 apart, as JLCPCB recommends for them; the 0.45 rule is for pad holes.
JAMMA_AREAS = ("JAMMA tip: no copper", "JAMMA contact band: fingers only", "JAMMA finger roots: no vias or pour")
BOARD_RULES = """(version 1)

(rule "TP7 keep-out: no via, pad or track"
    (constraint disallow via pad track)
    (condition "A.intersectsArea('TP7 keep-out')"))

(rule "TP7 keep-out: solder mask stays closed"
    (layer "F.Mask")
    (constraint disallow graphic text zone pad via)
    (condition "A.intersectsArea('TP7 keep-out')"))

(rule "JAMMA fingers: no vias near the fingers"
    (constraint disallow via)
    (condition "A.intersectsArea('JAMMA tip: no copper') || A.intersectsArea('JAMMA contact band: fingers only') || A.intersectsArea('JAMMA finger roots: no vias or pour')"))

(rule "JAMMA fingers: no tracks in the tip and contact bands"
    (constraint disallow track)
    (condition "A.intersectsArea('JAMMA tip: no copper') || A.intersectsArea('JAMMA contact band: fingers only')"))

(rule "Vias under a Pico are tented"
    (constraint disallow via)
    (condition "A.Type == 'Via' && (A.intersectsCourtyard('U25') || A.intersectsCourtyard('U26') || A.intersectsCourtyard('U27')) && (A.Front_tenting == 'Not tented' || A.Back_tenting == 'Not tented')"))

(rule "JLCPCB: silkscreen 0.15 from copper pads"
    (condition "A.existsOnLayer('F.Cu') || A.existsOnLayer('B.Cu') || B.existsOnLayer('F.Cu') || B.existsOnLayer('B.Cu')")
    (constraint silk_clearance (min 0.15mm)))

(rule "JLCPCB: pad holes 0.45 apart"
    (condition "A.Type == 'Pad' && B.Type == 'Pad' && !(A.memberOfFootprint('MB*') && B.memberOfFootprint('MB*'))")
    (constraint hole_to_hole (min 0.45mm)))

(rule "Breakaway tabs: no parts, pads, vias or tracks within 5 mm"
    (constraint disallow footprint pad via track)
    (condition "A.intersectsArea('Breakaway tab: keep clear') && !A.memberOfFootprint('MB*')"))

(rule "JLCPCB: annular ring of through-hole pads 0.25"
    (condition "A.Type == 'Pad'")
    (constraint annular_width (min 0.25mm)))
"""


# ---------------------------------------------------------------------------------------------- library and facts
BUILDERS = {JAMMA: jamma_edge, CART: cart60, TRIM: trimmer, DIP: dip_switch, PICO: pico2, BREAK: break_line, TOOL: tooling_hole}


def write_library(libdir):
    """Write every footprint; return {name: expected} for tools/check_footprints.py and (failed facts, number of facts)."""
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


def _one(exp, name):
    """{number: pad}, keeping only numbered pads; a number drawn twice makes the facts that use it fail."""
    out = {}
    for k, v in exp[name]["pads"].items():
        if not k.startswith("(no number)"):
            if len(v) != 1:
                raise ValueError(f"{name}: pad '{k}' is drawn {len(v)} times")
            out[k] = v[0]
    return out


def _near(a, b, tol=1e-6):
    return abs(a - b) <= tol


def _drawings(exp, name, kind=None, layer=None):
    return [d for d in exp[name]["drawings"] if (kind is None or d["type"] == kind) and (layer is None or d["layer"] == layer)]


def _rect_is(d, x0, y0, x1, y1):
    (ax, ay), (bx, by) = d["pts"]
    return (_near(min(ax, bx), min(x0, x1)) and _near(max(ax, bx), max(x0, x1))
            and _near(min(ay, by), min(y0, y1)) and _near(max(ay, by), max(y0, y1)))


def _sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def facts(exp, trees):
    """Statements from the sources, checked on what was drawn.  A statement that cannot be evaluated counts as failed."""
    F_ = []

    def fact(text, fn):
        F_.append((text, fn))

    # ---- JAMMA: written out again, apart from JAMMA_LETTERS, from the JAMMA pin-out (G, I, O, Q unused; 7/H = key)
    jamma_pairs = [("1", "A"), ("2", "B"), ("3", "C"), ("4", "D"), ("5", "E"), ("6", "F"), ("8", "J"), ("9", "K"), ("10", "L"),
                   ("11", "M"), ("12", "N"), ("13", "P"), ("14", "R"), ("15", "S"), ("16", "T"), ("17", "U"), ("18", "V"),
                   ("19", "W"), ("20", "X"), ("21", "Y"), ("22", "Z"), ("23", "a"), ("24", "b"), ("25", "c"), ("26", "d"),
                   ("27", "e"), ("28", "f")]

    def jamma_pads_right():
        j = _one(exp, JAMMA)
        if len(j) != 54:
            return False
        for num, letter in jamma_pairs:
            x = 3.96 * (int(num) - 1)
            for key, layers in ((num, ["F.Cu", "F.Mask"]), (letter, ["B.Cu", "B.Mask"])):
                p = j[key]
                if not (p["kind"] == "connect" and p["shape"] == "rect" and _near(p["x"], x) and _near(p["y"], -5.8)
                        and _near(p["w"], 2.30) and _near(p["h"], 8.40) and _near(p["rot"], 0) and p["layers"] == layers):
                    return False
        return True
    fact("JAMMA: 54 fingers 2.30 x 8.40 at 3.96, 1.6-10.0 mm from the tip, 1-28 on the parts side and A-f behind them "
         "(G, I, O, Q unused, 7/H the key), no paste, not turned", jamma_pads_right)
    fact("JAMMA: 1 to 28 is 106.92 (JST 106.92 ± 0.05, Hirose 106.98 ± 0.08)",
         lambda: _near(_one(exp, JAMMA)["28"]["x"] - _one(exp, JAMMA)["1"]["x"], 106.92))
    fact("JAMMA: the key slot is centred on position 7 (6 x 3.96)", lambda: _near(JAMMA_KEY[0], 6 * 3.96))
    fact("JAMMA: the solder mask is open over the whole finger band on both sides, 0.1 mm past the finger ends",
         lambda: all(any(d["fill"] and _rect_is(d, -4.24, 0.5, 111.16, -10.1) for d in _drawings(exp, JAMMA, "fp_rect", layer))
                     for layer in ("F.Mask", "B.Mask")))

    def jamma_keepouts_right():
        e = exp[JAMMA]
        want = {"JAMMA tip: no copper": ([0.5, -1.6], {"tracks": "not_allowed", "vias": "not_allowed", "pads": "not_allowed",
                                                         "copperpour": "not_allowed", "footprints": "allowed"}),
                "JAMMA contact band: fingers only": ([-1.6, -9.0], {"tracks": "not_allowed", "vias": "not_allowed", "pads": "allowed",
                                                                     "copperpour": "not_allowed", "footprints": "allowed"}),
                "JAMMA finger roots: no vias or pour": ([-9.0, -11.0], {"tracks": "allowed", "vias": "not_allowed", "pads": "allowed",
                                                                         "copperpour": "not_allowed", "footprints": "allowed"})}
        if sorted(e["keepout_names"]) != sorted(want):
            return False
        for i, n in enumerate(e["keepout_names"]):
            (ya, yb), rules = want[n]
            box = e["keepout_boxes"][i]
            if not (e["keepout_layers"][i] == ["B.Cu", "F.Cu"] and e["keepout_rules"][i] == rules and _near(box[0], -4.24)
                    and _near(box[2], 111.16) and _near(box[1], min(ya, yb)) and _near(box[3], max(ya, yb))):
                return False
        return True
    fact("JAMMA: three keep-outs on both copper layers: no copper in the bevel (0-1.6), fingers only in the contact band "
         "(1.6-9.0), no vias or pour at the finger roots (9.0-11.0)", jamma_keepouts_right)
    def jamma_setback_right():
        nominal = 1.13                                      # JLCPCB: the 30° bevel of a 1.6 mm board reaches about 1.13 mm
        flat = 1.6 - 2 * nominal * math.tan(math.radians(30))           # the tip the bevel leaves (about 0.30)
        reach = lambda t, a: (t - flat) / 2 / math.tan(math.radians(a))
        angle = reach(1.6, 25) - nominal                    # ±5°: the shallow end reaches further
        thick = reach(1.76, 30) - nominal                   # +10 % board
        rss = nominal + math.sqrt(angle ** 2 + thick ** 2 + 0.2 ** 2)  # with the routed tip ±0.2
        return rss <= JAMMA_SETBACK and all(p["y"] + p["h"] / 2 <= -JAMMA_SETBACK + 1e-9 for p in _one(exp, JAMMA).values())
    fact("JAMMA: no copper within 1.6 of the tip, which covers JLCPCB's bevel (about 1.13 at 30° on 1.6 mm) with its ±5°, the "
         "board's ±10 % and the routing's ±0.2 added as a root-sum-square (about 1.49)", jamma_setback_right)

    def jamma_courtyard_right():
        # written out again: 5 mm past the outer fingers' copper (finger 1 at 0, finger 28 at 27 x 3.96, half width 1.15)
        tx0, tx1 = -1.15 - 5.0, 27 * 3.96 + 1.15 + 5.0
        want = [(-4.24, 0.5), (111.16, 0.5), (111.16, -12.0), (tx1, -12.0), (tx1, -15.0), (tx0, -15.0), (tx0, -12.0), (-4.24, -12.0)]
        for layer in ("F.CrtYd", "B.CrtYd"):
            polys = _drawings(exp, JAMMA, "fp_poly", layer)
            if len(polys) != 1 or len(_drawings(exp, JAMMA, layer=layer)) != 1 or polys[0]["fill"]:
                return False
            got = polys[0]["pts"]
            if len(got) != len(want) or not all(_near(a[0], b[0]) and _near(a[1], b[1]) for a, b in zip(got, want)):
                return False
        return True
    fact("JAMMA: courtyard on both sides to 15 mm from the tip, and beside the tongue's root (12-15 mm) 5 mm past the outer fingers, "
         "so that no part comes within 5 mm of a finger", jamma_courtyard_right)
    fact("JAMMA: left out of the BOM and the position file, mask bridges allowed between fingers",
         lambda: sorted(exp[JAMMA]["attr"]) == ["allow_soldermask_bridges", "exclude_from_bom", "exclude_from_pos_files"])

    # ---- cartridge slot
    def cart_pads_right():
        c = _one(exp, CART)
        if sorted(c, key=int) != [str(n) for n in range(1, 61)]:
            return False
        for n in range(1, 61):
            k = (n - 1) % 30
            x, y = -36.83 + 2.54 * k, (2.54 if n <= 30 else -2.54)
            p = c[str(n)]
            if not (_near(p["x"], x) and _near(p["y"], y) and p["kind"] == "thru_hole" and p["shape"] == ("rect" if n == 1 else "circle")
                    and _near(p["drill"], 1.00) and _near(p["w"], 1.70) and _near(p["h"], 1.70) and p["layers"] == ["*.Cu", "*.Mask"]):
                return False
        return True
    fact("cartridge: 60 holes of 1.0 on 2.54 x 5.08 (WingTAT ED60BGFBK); 1-30 on the label row (+Y) from -X, 31-60 behind them; "
         "pad 1 square", cart_pads_right)
    fact("cartridge: the finished hole (+0.13/-0.08) stays inside the maker's Ø1.00 ± 0.15, ring at least 0.25, lands at most 1.9",
         lambda: all(0.85 <= p["drill"] - 0.08 and p["drill"] + 0.13 <= 1.15 + 1e-9 and (p["w"] - p["drill"]) / 2 >= 0.25 and p["w"] <= 1.9
                     for p in _one(exp, CART).values()))
    fact("cartridge: 'CART LABEL' is printed on the label side (+Y)",
         lambda: any(d["text"] == "CART LABEL" and d["pts"][0][1] > 2.54 for d in _drawings(exp, CART, "fp_text", "F.SilkS")))
    fact("cartridge: a JLCPCB part (in the BOM and the position file), through hole",
         lambda: exp[CART]["attr"] == ["through_hole"])

    # ---- trimmer
    def trim_pads_right():
        t = _one(exp, TRIM)
        if sorted(t) != ["1", "2", "3"]:
            return False
        x1, y1 = t["1"]["x"], t["1"]["y"]
        return (_near(t["3"]["x"] - x1, 5.08) and _near(t["3"]["y"] - y1, 0) and _near(t["2"]["x"] - x1, 2.54)
                and _near(t["2"]["y"] - y1, -2.54) and all(p["kind"] == "thru_hole" for p in t.values()))
    fact("trimmer: pin 3 at +5.08 from pin 1, pin 2 (wiper) at +2.54 and 2.54 towards the far edge (Bourns 3362P)", trim_pads_right)
    fact("trimmer: the finished hole clears a 0.55 lead by 0.2 and stays at most 1.1; ring at least 0.25",
         lambda: all(p["drill"] - 0.08 - 0.55 >= 0.2 - 1e-9 and p["drill"] + 0.13 <= 1.1 and (p["w"] - p["drill"]) / 2 >= 0.25
                     for p in _one(exp, TRIM).values()))
    fact("trimmer: the clockwise arrow ends on the pin-3 side, where '+' is",
         lambda: any(d["pts"][2][0] > d["pts"][0][0] and d["pts"][2][0] > 0 for d in _drawings(exp, TRIM, "fp_arc", "F.SilkS")))

    # ---- DIP switch
    def dip_pads_right():
        d = _one(exp, DIP)
        if sorted(d) != [str(n) for n in range(1, 9)]:
            return False
        ok = all(_near(p["drill"], DIP_DRILL) and _near(p["w"], DIP_PAD) and p["kind"] == "thru_hole" for p in d.values())
        for n in range(1, 5):
            a, b = d[str(n)], d[str(9 - n)]
            ok = ok and _near(a["x"], 0) and _near(a["y"], 2.54 * (n - 1)) and _near(b["x"] - a["x"], 7.62) and _near(b["y"], a["y"])
        return ok
    fact("DIP switch: pads 1-4 on one row at 2.54, pad n faces pad 9 - n across 7.62, 1.0 holes, 1.7 lands", dip_pads_right)
    fact("DIP switch: the 1.0 drill finishes at 0.92-1.13, around the maker's Ø0.97, and clears the 0.60 x 0.20 lead (0.63 across)",
         lambda: _near(DIP_DRILL, 1.0) and DIP_DRILL - 0.08 >= 0.633 + 0.2)
    fact("DIP switch: 'ON' is printed on the pad 5-8 side (+X)",
         lambda: any(d["text"] == "ON" and d["pts"][0][0] > 7.62 for d in _drawings(exp, DIP, "fp_text", "F.SilkS")))
    fact("DIP switch: no silkscreen under the fitted part",
         lambda: not any(all(DIP_BODY[0] <= x <= DIP_BODY[2] and DIP_BODY[1] <= y <= DIP_BODY[3] for x, y in d["pts"])
                         for d in _drawings(exp, DIP, layer="F.SilkS")))

    # ---- Pico 2
    fact("Pico 2 and DIP copies: the KiCad library files are the ones checked on 2026-11-15",
         lambda: all(_sha256(p) == h for p, h in LIBRARY_SHA256.items()))

    def pico_pads_unchanged():
        def pad_nodes(tree):
            return [[x for x in p if not (isinstance(x, list) and x and x[0] == "uuid")] for p in find(tree, "pad")]
        from fcgen.sexpr import parse
        return pad_nodes(trees[PICO]) == pad_nodes(parse(open(PICO_LIB, encoding="utf-8").read()))
    fact("Pico 2: every pad is KiCad's, unchanged (shape, angle, paste offset and all)", pico_pads_unchanged)

    def tp7_right():
        e = exp[PICO]
        if e["keepouts"] != 1 or e["keepout_names"] != [PICO_TP7_ZONE] or e["keepout_layers"] != [["F.Cu", "F.Mask"]]:
            return False
        if e["keepout_rules"][0] != {"tracks": "not_allowed", "vias": "not_allowed", "pads": "not_allowed",
                                     "copperpour": "not_allowed", "footprints": "allowed"}:
            return False
        x0, y0, x1, y1 = e["keepout_boxes"][0]
        return (_near((x0 + x1) / 2, 1.0, 1e-3) and _near((y0 + y1) / 2, -5.0, 1e-3)
                and _near(x1 - x0, 2.5, 1e-3) and _near(y1 - y0, 2.5, 1e-3))
    fact("Pico 2: one keep-out, 2.5 mm across, centred on TP7 at (+1.0, -5.0), on F.Cu and F.Mask, forbidding tracks, vias, pads "
         "and pour", tp7_right)
    fact("Pico 2: no pad of the module reaches the TP7 keep-out",
         lambda: not any(math.hypot(max(abs(p["x"] - 1.0) - p["w"] / 2, 0), max(abs(p["y"] + 5.0) - p["h"] / 2, 0)) < 1.25
                         for v in exp[PICO]["pads"].values() for p in v
                         if any(layer in ("F.Cu", "F.Mask", "*.Cu", "*.Mask") for layer in p["layers"])))

    # ---- edge rails: mouse bites and tooling holes
    def break_right():
        holes = [p for v in exp[BREAK]["pads"].values() for p in v]
        if not (5 <= len(holes) <= 8) or not all(p["kind"] == "np_thru_hole" and p["shape"] == "circle" and 0.5 <= p["drill"] <= 0.8
                                                 and _near(p["drill"], 0.6) and _near(p["w"], p["drill"]) and _near(p["x"], 0) for p in holes):
            return False
        ys = sorted(p["y"] for p in holes)
        gaps = [b - a - holes[0]["drill"] for a, b in zip(ys, ys[1:])]
        return all(_near(g, 0.3) for g in gaps) and _near(ys[0], -ys[-1])
    fact("mouse bites: 5-8 holes of 0.6, not plated, 0.3 apart, in one line along Y (JLCPCB: capabilities 0.5-0.8 and 0.2-0.3 apart; "
         "mouse-bite guide 5-8 holes of 0.6, at least 0.3 apart)", break_right)

    def break_keepout_right():
        e = exp[BREAK]
        if e["keepout_names"] != [BREAK_ZONE] or e["keepout_layers"] != [["B.Cu", "F.Cu"]]:
            return False
        if e["keepout_rules"][0] != {"tracks": "not_allowed", "vias": "not_allowed", "pads": "not_allowed",
                                     "copperpour": "not_allowed", "footprints": "not_allowed"}:
            return False
        x0, y0, x1, y1 = e["keepout_boxes"][0]
        holes = [p for v in e["pads"].values() for p in v]
        r = max(p["drill"] for p in holes) / 2
        far = max(abs(p["y"]) for p in holes) + r
        return (_near(x0, -r) and x1 >= r + 5.0 - 1e-9 and y0 <= -(far + 5.0) + 1e-9 and y1 >= far + 5.0 - 1e-9
                and x1 <= 6.0 and y1 <= 9.0)
    fact("mouse bites: a keep-out from the board's edge to 5 mm past every hole on the board's side (+X), forbidding parts, pads, "
         "vias, tracks and pour", break_keepout_right)
    fact("tooling hole: one hole of 2.0, not plated (JLCPCB: 2 mm tooling holes)",
         lambda: [(p["kind"], p["drill"], p["x"], p["y"]) for v in exp[TOOL]["pads"].values() for p in v] == [("np_thru_hole", 2.0, 0.0, 0.0)])
    fact("mouse bites and tooling hole: on the board only, left out of the BOM and the position file",
         lambda: all(sorted(exp[n]["attr"]) == ["board_only", "exclude_from_bom", "exclude_from_pos_files"] for n in (BREAK, TOOL)))

    # ---- silkscreen on every footprint
    def silk_ok():
        for name, tree in trees.items():
            for x in tree:
                if not (isinstance(x, list) and x and x[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly", "fp_text", "property")):
                    continue
                layer = first(x, "layer")
                if layer is None or str(layer[1]) not in ("F.SilkS", "B.SilkS"):
                    continue
                if x[0] in ("fp_text", "property"):
                    font = first(first(x, "effects"), "font")
                    size, thick = first(font, "size"), first(font, "thickness")
                    if float(size[1]) < 1.0 or float(size[2]) < 1.0 or float(thick[1]) < SILK_MIN:
                        return False
                elif x[0] != "fp_poly" or str(first(x, "fill")[1]) not in ("yes", "solid"):
                    if float(first(first(x, "stroke"), "width")[1]) < SILK_MIN:
                        return False
        return True
    fact("silkscreen: lines at least 0.15 wide, text at least 1.0 high and 0.15 thick (JLCPCB)", silk_ok)

    failed = []
    for text, fn in F_:
        try:
            ok = bool(fn())
        except Exception as e:          # a missing or doubled pad: the fact fails instead of the build crashing
            ok, text = False, f"{text} (could not be evaluated: {type(e).__name__}: {e})"
        if not ok:
            failed.append(text)
    return failed, len(F_)
