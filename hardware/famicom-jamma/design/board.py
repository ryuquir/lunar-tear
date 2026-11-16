"""The bare board: outline, mounting holes, fiducials and the settings that go with the order.

tools/make_board.py turns this into kicad/fcjamma.kicad_pcb; tools/build.py runs it and checks the result.
Parts other than the JAMMA edge (J1) are placed in stage 2-2, after the cartridge-slot sample and JLCPCB's answers.

Frame (the same as mech/floorplan.py): millimetres, origin at the lower-left corner of the board's bounding box, seen
from the parts side with the JAMMA fingers pointing down; y = 0 is the tip of the fingers, x to the right, y upwards.
In KiCad the board sits on the default A4 sheet at ORIGIN with y downwards: x_k = ORIGIN[0] + x, y_k = ORIGIN[1] + (TOP - y).
The drill/place (auxiliary) origin is the lower-left corner of the bounding box, so that the position file uses this frame.

Sources: research_notes/ファミコン JAMMA 基板 仕様調査/footprint_specs.md section 1 (the JAMMA tongue, key slot and
shoulder, drawn here on Edge.Cuts because the footprint holds only the fingers), reference/02_jamma_interface.md 1.2.3
(mounting holes: M3, at least 4 mm from the edges, none within 12 mm of the tip; 1.6 mm FR-4; ENIG with gold fingers,
bevelled), mech/floorplan.py (body size, hole positions).
"""
import math

import footprints as FPL

BODY_W, BODY_H = 220.0, 150.0                    # board body
TONGUE_W = FPL.JAMMA_TONGUE[1] - FPL.JAMMA_TONGUE[0]          # 114.4
TONGUE_X0 = (BODY_W - TONGUE_W) / 2              # 52.8: the tongue is centred under the body
Y0 = -FPL.JAMMA_SHOULDER                         # 12: the body starts 12 mm above the finger tips
TOP = Y0 + BODY_H                                # 162
J1_AT = (TONGUE_X0 - FPL.JAMMA_TONGUE[0], 0.0)   # finger 1 on the tip line: (56.54, 0)
CORNER_R = 2.0                                   # rounded corners of the body (the tongue keeps its 0.5 mm chamfers)
THICKNESS = 1.6                                  # JAMMA mating connectors: 1.6 ± 0.15 (JST, Hirose)
ORIGIN = (20.0, 20.0)                            # top-left corner of the bounding box on the KiCad sheet

# M3, 3.2 mm, not plated (KiCad MountingHole_3.2mm_M3): the four corners, two beside the IC sockets and one between them,
# where pressing a chip into its socket (nearly 10 kg) needs the board to be supported.
HOLE_FOOTPRINT = "MountingHole:MountingHole_3.2mm_M3"
HOLES = [(4.0, 16.0), (216.0, 16.0), (4.0, 158.0), (216.0, 158.0), (4.0, 100.0), (216.0, 100.0), (110.0, 121.0)]

# Global fiducials for the assembly machine: three corners, not symmetric, on the parts side.
FIDUCIAL_FOOTPRINT = "Fiducial:Fiducial_1mm_Mask2mm"
FIDUCIALS = [(4.0, 30.0), (4.0, 150.0), (216.0, 150.0)]

TITLE = "Famicom JAMMA board (fcjamma)"

# The stackup KiCad writes for a 2-layer 1.6 mm board, with the finish and the bevelled edge connector of the order
# (JLCPCB: gold fingers only with ENIG; bevel 30°).  tools/make_board.py puts it into the board's setup.
STACKUP = """		(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
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
    """A quarter (or any < 180°) arc from start to end about centre: (start, mid, end)."""
    vx, vy = (start[0] - centre[0]) + (end[0] - centre[0]), (start[1] - centre[1]) + (end[1] - centre[1])
    r = math.hypot(start[0] - centre[0], start[1] - centre[1])
    n = math.hypot(vx, vy)
    return ("arc", start, (centre[0] + r * vx / n, centre[1] + r * vy / n), end)


def outline():
    """The board's one closed contour, as ('line', a, b) and ('arc', start, mid, end) in this frame, in order."""
    t0, t1 = TONGUE_X0, TONGUE_X0 + TONGUE_W
    k0, k1, kd = key_slot()
    r, w = CORNER_R, BODY_W
    path = [
        ("line", (r, Y0), (t0, Y0)),                     # shoulder, left of the tongue (sharp inner corner)
        ("line", (t0, Y0), (t0, 0.5)),                   # tongue, left side
        ("line", (t0, 0.5), (t0 + 0.5, 0.0)),            # C0.5
        ("line", (t0 + 0.5, 0.0), (k0 - 0.5, 0.0)),      # tip
        ("line", (k0 - 0.5, 0.0), (k0, 0.5)),            # key slot mouth, C0.5
        ("line", (k0, 0.5), (k0, kd - 0.5)),
        _arc((k0, kd - 0.5), (k0 + 0.5, kd), (k0 + 0.5, kd - 0.5)),       # R0.5 at the bottom of the slot
        ("line", (k0 + 0.5, kd), (k1 - 0.5, kd)),
        _arc((k1 - 0.5, kd), (k1, kd - 0.5), (k1 - 0.5, kd - 0.5)),
        ("line", (k1, kd - 0.5), (k1, 0.5)),
        ("line", (k1, 0.5), (k1 + 0.5, 0.0)),            # C0.5
        ("line", (k1 + 0.5, 0.0), (t1 - 0.5, 0.0)),      # tip
        ("line", (t1 - 0.5, 0.0), (t1, 0.5)),            # C0.5
        ("line", (t1, 0.5), (t1, Y0)),                   # tongue, right side
        ("line", (t1, Y0), (w - r, Y0)),                 # shoulder, right
        _arc((w - r, Y0), (w, Y0 + r), (w - r, Y0 + r)),
        ("line", (w, Y0 + r), (w, TOP - r)),
        _arc((w, TOP - r), (w - r, TOP), (w - r, TOP - r)),
        ("line", (w - r, TOP), (r, TOP)),
        _arc((r, TOP), (0.0, TOP - r), (r, TOP - r)),
        ("line", (0.0, TOP - r), (0.0, Y0 + r)),
        _arc((0.0, Y0 + r), (r, Y0), (r, Y0 + r)),
    ]
    return path


def to_kicad(p):
    return (ORIGIN[0] + p[0], ORIGIN[1] + TOP - p[1])
