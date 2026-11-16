"""The bare board: outline, edge rails, mounting holes, fiducials and the settings that go with the order.

tools/make_board.py turns this into kicad/fcjamma.kicad_pcb; tools/build.py runs it and checks the result.
Parts other than the JAMMA edge (J1) are placed in stage 2-2, after the cartridge-slot sample and JLCPCB's answers.

Frame (the same as mech/floorplan.py): millimetres, seen from the parts side with the JAMMA fingers pointing down; x = 0 is
the body's left edge (the rails lie at negative x), y = 0 the tip of the fingers, x to the right, y upwards.  The origin is
where the body's left edge meets the tip line; the body itself starts 12 mm higher, at Y0.
In KiCad the board sits on the default A4 sheet with y downwards: x_k = ORIGIN[0] + x, y_k = ORIGIN[1] + (TOP - y).
The drill/place (auxiliary) origin is the lower-left corner of the panel (the left rail's outer edge, the tip line), so that
no coordinate is negative; the Gerbers, the drill files and the position file all use it (PLOT below, README chapter 8).

Edge rails: JLCPCB's Standard PCBA needs them ('Edge Rails: Necessary', 'Fiducials: Necessary').  Left to JLCPCB, they
may land on the gold-finger edge, which then cannot be bevelled; so the board carries its own, on the two edges at right
angles to the fingers.  They are joined by mouse bites, not V-cut: JLCPCB's gold-finger page says fingers in a V-cut panel
cannot be chamfered.  If JLCPCB confirms that V-cut rails on these two edges keep the bevel, RAIL_GAP = 0 and a V-cut
would do (to be redrawn then).

Sources: research_notes/ファミコン JAMMA 基板 仕様調査/footprint_specs.md section 1 (the JAMMA tongue, key slot and
shoulder, drawn here on Edge.Cuts because the footprint holds only the fingers), reference/02_jamma_interface.md 1.2.3
(mounting holes: M3, at least 4 mm from the edges, none within 12 mm of the tip; 1.6 mm FR-4; ENIG with gold fingers,
bevelled), mech/floorplan.py (body size, hole positions); JLCPCB (read 2026-11-16): the capabilities page, 'Mouse bites
Panel', and the mouse-bite guide (both quoted in design/footprints.py at the edge rails); 'Design Optimization:
Specifications for Adding Process Edges and Positioning Holes' (5 mm rails, 2 mm tooling holes 'Centered on process
edge', 1 mm fiducials 3.85 from the edge; a tooling hole near a milling path weakens the rail); 'How to Add Edge Rails
and Fiducials' (fiducial copper 3.35 from the board edge).
"""
import math

import footprints as FPL

BODY_W, BODY_H = 220.0, 150.0                    # board body
TONGUE_W = FPL.JAMMA_TONGUE[1] - FPL.JAMMA_TONGUE[0]          # 114.4
TONGUE_X0 = (BODY_W - TONGUE_W) / 2              # 52.8: the tongue is centred under the body
Y0 = -FPL.JAMMA_SHOULDER                         # 12: the body starts 12 mm above the finger tips
TOP = Y0 + BODY_H                                # 162
J1_AT = (TONGUE_X0 - FPL.JAMMA_TONGUE[0], 0.0)   # finger 1 on the tip line: (56.54, 0)
CORNER_R = 2.0                                   # rounded corners of the body and the panel (the tongue keeps its 0.5 mm chamfers)
THICKNESS = 1.6                                  # JAMMA mating connectors: 1.6 ± 0.15 (JST, Hirose)
ORIGIN = (27.0, 20.0)                            # where the frame's (0, TOP) lies on the KiCad sheet: the panel starts at x 20

# ---- edge rails (manufacturing only; snapped off or kept when the board is fitted)
RAIL_W = 5.0                                     # JLCPCB: 'use 5 mm tooling edges'
RAIL_GAP = 2.0                                   # routed slot between rail and body (JLCPCB mouse-bite panels: 1.6 or 2 mm)
PANEL_X = (-RAIL_GAP - RAIL_W, BODY_W + RAIL_GAP + RAIL_W)    # -7 .. 227: the rails run the full height, 0 .. TOP
TAB_W = 5.5                                      # at its narrowest; JLCPCB: 'For breakaway with mouse-bites, the minimum width is
                                                 # 5mm', and the slots' ends may lie 0.2 off (routing ±0.2)
# tab centres (y), the same on both sides: clear of the mounting holes (y 16, 99, 158), of U27 at the left edge (y 60-83),
# of the USB-C socket J10 (y 85-94), which faces the left slot, and of the IC sockets' pins; their keep-outs (5 mm around
# the mouse bites) stay clear of all of these.  JLCPCB's guide asks for a set every 50-60 mm: here 15-64 mm apart, the
# 64 mm gap on the left being where U27 and J10 sit.  The first tab could go about 4 mm lower before its keep-out meets
# H1's courtyard (y 16 + 3.45); the rail's free end below it would then be about 25 mm instead of 29.
TABS = (32.0, 48.0, 112.0, 130.0, 145.0)
BITE_INSET = FPL.BREAK_D / 2                     # mouse-bite line on the body's side, the holes touching the edge from inside
BREAK_FOOTPRINT = "fcjamma:" + FPL.BREAK
TOOLING_FOOTPRINT = "fcjamma:" + FPL.TOOL
# 2.0 mm tooling holes centred on the rails (JLCPCB's figure: 'Centered on process edge', which leaves 1.5 mm of rail on each
# side), 5 mm from the rails' ends: near the panel's corners, our choice (JLCPCB gives no position).  Below the first tab the
# rail's inner edge is routed: JLCPCB warns that a tooling hole next to a milling path weakens the rail, so the holes keep
# the same 1.5 mm there as on the outer edge, and JLCPCB is asked (support question 3a).
TOOLING = [(PANEL_X[0] + RAIL_W / 2, 5.0), (PANEL_X[0] + RAIL_W / 2, TOP - 5.0),
           (PANEL_X[1] - RAIL_W / 2, 5.0), (PANEL_X[1] - RAIL_W / 2, TOP - 5.0)]

# M3, 3.2 mm, not plated (KiCad MountingHole_3.2mm_M3): the four corners, two beside the IC sockets and one between them,
# where pressing a chip into its socket (nearly 10 kg) needs the board to be supported.
HOLE_FOOTPRINT = "MountingHole:MountingHole_3.2mm_M3"
HOLES = [(4.0, 16.0), (216.0, 16.0), (4.0, 158.0), (216.0, 158.0), (4.0, 99.0), (216.0, 99.0), (110.0, 121.0)]

# Fiducials for the assembly machine, on the rails: 1 mm copper, 2 mm mask opening, centred 3.85 from the panel's outer
# edge (JLCPCB's figures; the copper then keeps its 3.35 mm from the edge, which the conveyor's clamps hold); three, not
# symmetric.  They sit level with the lowest and the highest tab, where the rail is held, not on the rails' free ends.
# There the nearest routed edge is the round end of a slot beside the tab: 2.82 from the copper, 2.32 from the mask
# opening (nothing clamps there; JLCPCB is asked, support question 3a).
FIDUCIAL_FOOTPRINT = "Fiducial:Fiducial_1mm_Mask2mm"
FIDUCIALS = [(PANEL_X[0] + 3.85, TABS[0]), (PANEL_X[0] + 3.85, TABS[-1]), (PANEL_X[1] - 3.85, TABS[-1])]

TITLE = "Famicom JAMMA board (fcjamma)"

# Plot settings stored in the board: Protel file names (JLCPCB's KiCad guide) and the drill/place origin for the Gerbers,
# so that the Gerbers, the drill files and the position file share one frame.
PLOT = {"protel_extensions": True, "use_aux_origin": True}

# The stackup KiCad writes for a 2-layer board, with the finish and the bevelled edge connector of the order
# (JLCPCB: gold fingers only with ENIG; bevel 30°).  The core is what is left of THICKNESS after the copper and the mask,
# so that the stackup and the board thickness cannot disagree.  tools/make_board.py puts it into the board's setup.
MASK_T, COPPER_T = 0.01, 0.035
CORE_T = round(THICKNESS - 2 * (MASK_T + COPPER_T), 6)       # 1.51
STACKUP = f"""		(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness {MASK_T}))
			(layer "F.Cu" (type "copper") (thickness {COPPER_T}))
			(layer "dielectric 1" (type "core") (thickness {CORE_T}) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness {COPPER_T}))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness {MASK_T}))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen"))
			(copper_finish "ENIG")
			(dielectric_constraints no)
			(edge_connector bevelled)
		)
"""


def key_slot():
    """x0, x1 and depth of the key slot at position 7/H, in this frame."""
    kx, kw, kd = FPL.JAMMA_KEY
    return J1_AT[0] + kx - kw / 2, J1_AT[0] + kx + kw / 2, kd


def _arc(start, end, centre):
    """An arc of less than 360° from start to end about centre, turning left (counter-clockwise, y up), as (start, mid, end)."""
    a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
    a1 = math.atan2(end[1] - centre[1], end[0] - centre[0])
    sweep = (a1 - a0) % (2 * math.pi) or 2 * math.pi
    r = math.hypot(start[0] - centre[0], start[1] - centre[1])
    am = a0 + sweep / 2
    return ("arc", start, (round(centre[0] + r * math.cos(am), 9), round(centre[1] + r * math.sin(am), 9)), end)


def _corner(start, end, centre, r):
    """A rounded corner, or nothing when the corner is square (r = 0: the lines meet at the corner)."""
    return [_arc(start, end, centre)] if r > 0 else []


def _arc_cw(start, end, centre):
    """The same, turning right (clockwise): the mid point lies on the other side."""
    a = _arc(end, start, centre)
    return ("arc", start, a[2], end)


def _path(points_and_arcs):
    """Lines between consecutive points; ('arc', s, m, e) items are kept; zero-length lines are dropped."""
    out, last = [], None
    for item in points_and_arcs:
        if isinstance(item, tuple) and item and item[0] == "arc":
            if last is not None and last != item[1]:
                out.append(("line", last, item[1]))
            out.append(item)
            last = item[3]
        else:
            if last is not None and last != item:
                out.append(("line", last, item))
            last = item
    return out


def tab_spans():
    """For each tab, (y_lo, y_hi) of the slots' straight sides around it: the slot ends are half circles of RAIL_GAP / 2."""
    h = TAB_W / 2 + RAIL_GAP / 2
    return [(t - h, t + h) for t in TABS]


def contours():
    """The board's closed contours, in order, as ('line', a, b) and ('arc', start, mid, end) in this frame: first the outer
    contour (rails, body, tongue), then the slots between the rails and the body (two per gap between tabs)."""
    t0, t1 = TONGUE_X0, TONGUE_X0 + TONGUE_W
    k0, k1, kd = key_slot()
    r, w, g = CORNER_R, BODY_W, RAIL_GAP
    xl, xr = PANEL_X
    spans = tab_spans()
    lo, hi = spans[0][0], spans[-1][1]                 # the open slot ends below the first tab and above the last
    c = g / 2
    outer = _path([
        (xl + r, 0.0), (-g, 0.0),                                           # left rail, bottom
        (-g, lo), _arc_cw((-g, lo), (0.0, lo), (-c, lo)),                   # up the rail; round end of the open slot
        (0.0, lo), (0.0, Y0 + r), *_corner((0.0, Y0 + r), (r, Y0), (r, Y0 + r), r),        # down the body's left edge
        (r, Y0), (t0, Y0),                                                  # shoulder, left of the tongue (sharp inner corner)
        (t0, 0.5), (t0 + 0.5, 0.0),                                         # tongue, left side, C0.5
        (k0 - 0.5, 0.0), (k0, 0.5),                                         # tip; key slot mouth, C0.5
        (k0, kd - 0.5), _arc_cw((k0, kd - 0.5), (k0 + 0.5, kd), (k0 + 0.5, kd - 0.5)),    # R0.5 at the bottom of the slot
        (k1 - 0.5, kd), _arc_cw((k1 - 0.5, kd), (k1, kd - 0.5), (k1 - 0.5, kd - 0.5)),
        (k1, 0.5), (k1 + 0.5, 0.0),                                         # C0.5
        (t1 - 0.5, 0.0), (t1, 0.5),                                         # tip, C0.5
        (t1, Y0), (w - r, Y0),                                              # tongue, right side; shoulder, right
        *_corner((w - r, Y0), (w, Y0 + r), (w - r, Y0 + r), r),
        (w, Y0 + r), (w, lo), _arc_cw((w, lo), (w + g, lo), (w + c, lo)),   # up the body's right edge; slot end
        (w + g, lo), (w + g, 0.0), (xr - r, 0.0),                           # down the right rail; its bottom
        *_corner((xr - r, 0.0), (xr, r), (xr - r, r), r),
        (xr, r), (xr, TOP - r), *_corner((xr, TOP - r), (xr - r, TOP), (xr - r, TOP - r), r),
        (xr - r, TOP), (w + g, TOP),                                        # right rail, top
        (w + g, hi), _arc_cw((w + g, hi), (w, hi), (w + c, hi)),            # down the rail; round end of the top slot
        (w, hi), (w, TOP - r), *_corner((w, TOP - r), (w - r, TOP), (w - r, TOP - r), r),
        (w - r, TOP), (r, TOP), *_corner((r, TOP), (0.0, TOP - r), (r, TOP - r), r),      # body, top
        (0.0, TOP - r), (0.0, hi), _arc_cw((0.0, hi), (-g, hi), (-c, hi)),  # down the body's left edge; slot end
        (-g, hi), (-g, TOP), (xl + r, TOP),                                 # up the left rail; its top
        *_corner((xl + r, TOP), (xl, TOP - r), (xl + r, TOP - r), r),
        (xl, TOP - r), (xl, r), *_corner((xl, r), (xl + r, 0.0), (xl + r, r), r),
        (xl + r, 0.0),
    ])
    slots = []
    for (_, a), (b, _) in zip(spans, spans[1:]):      # between the upper end of one tab and the lower end of the next
        for x in (0.0, w):                              # the left slot is -g .. 0, the right one w .. w + g
            xa, xb = (x - g, x) if x == 0.0 else (x, x + g)
            slots.append(_path([(xb, a), (xb, b), _arc((xb, b), (xa, b), ((xa + xb) / 2, b)),
                                (xa, b), (xa, a), _arc((xa, a), (xb, a), ((xa + xb) / 2, a)), (xb, a)]))
    return [outer] + slots


def outline():
    """Every segment of every contour, in order."""
    return [seg for contour in contours() for seg in contour]


def break_lines():
    """(x, y, rotation) of each line of mouse bites: BITE_INSET (0.3) inside the body's edge, at each tab, on both sides."""
    return [(x, t, rot) for t in TABS for x, rot in ((BITE_INSET, 0.0), (BODY_W - BITE_INSET, 180.0))]


def to_kicad(p):
    return (ORIGIN[0] + p[0], ORIGIN[1] + TOP - p[1])


def aux_origin():
    """The drill/place origin in this frame: the panel's lower-left corner."""
    return (PANEL_X[0], 0.0)
