#!/usr/bin/python3
"""Build the board file from design/board.py, then read it back and check it.

    /usr/bin/python3 tools/make_board.py <kicad project folder> <board.json> <board file to write>

tools/build.py writes board.json from design/board.py, the circuit and KiCad's netlist (J1's nets, path and fields) and runs
this script with the system Python, which has KiCad's pcbnew module, on the project it stages: the board is written there
whether or not it passes (before the checks, so that even a crash in them leaves it to look at); tools/build.py then
runs KiCad's DRC and the schematic parity on it, and the staged project replaces kicad/ only when the whole build has no
problem (otherwise it is kept in out/failed/kicad/).  The board holds, so far: the outline (body, JAMMA
tongue and key slot, and the edge rails, joined by mouse bites), the JAMMA edge J1 placed on the tongue, the mounting holes,
the rails' tooling holes and fiducials, the stackup (ENIG, bevelled edge connector), via tenting, the plot settings, the
title block and the drill/place origin.  The other parts come in stage 2-2.  Every item gets an identifier derived from its
name, so that a rebuild writes the same file.

The checks read the saved board back and measure it.  Positions are taken back to the design frame through the drill/place
origin (itself checked against the outline) and compared with design/board.py, not with board.json; and the limits that
matter (the mating connectors, JLCPCB's rules) are written out again below.  So a wrong value in design/board.py or a wrong
transformation in tools/build.py fails here.
Exit status 1 and one line per failed check.
"""
import json
import math
import os
import re
import shutil
import sys
import tempfile
import uuid

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "design"), HERE]
import board as BRD            # noqa: E402  (design/board.py: what the board should be)
from fcgen.sexpr import parse as sx_parse, find as sx_find, first as sx_first   # noqa: E402

MM = pcbnew.FromMM
NS = uuid.UUID("0f6d1f2a-7c55-4d8e-9f39-5b7b2c9e4a61")

# ---- written out again from the sources, not taken from design/board.py
# research_notes/ファミコン JAMMA 基板 仕様調査/reference/02_jamma_interface.md 1.2.3 and footprint_specs.md section 1;
# JLCPCB capabilities and help pages (read 2026-11-16).
THICKNESS = 1.6                 # JST, Hirose: 1.6 ± 0.15
PITCH = 3.96                    # JST 106.92 ± 0.05 over 27 pitches
TONGUE_WIDTH = (114.4, 114.6)   # JST 114.6 +0/-0.2
FINGER_TO_SIDE = (3.74, 3.84)   # centre of an outer finger to the tongue's side: JST 3.84 +0/-0.1
KEY_PITCHES = 6                 # the key slot is position 7/H, six pitches from finger 1
KEY_WIDTH = (2.5, 3.0)          # Hirose 2.5 +0.1/0, JST 3.0; the keys are at most 2.36 thick (Sullins)
KEY_DEPTH = (11.0, 11.5)        # Hirose 11 +0.5/0 (JST 10.0)
SLOT_TO_COPPER = 1.3            # the copper of fingers 6 and 8 at least 1.3 from the key slot's walls
SHOULDER = 12.0                 # no board beside the tongue up to 12 mm from the tip (JST: a notch at least 10 deep)
FINGER = (2.30, 1.6, 10.0)      # width; copper from 1.6 (JLCPCB's 30 ± 5° bevel on a tip routed ±0.2) to 10.0 (JST)
UNWIRED = {"5", "6", "11", "E", "F", "M"}       # JAMMA positions this board leaves open (README chapter 8)
RAIL = 5.0                      # JLCPCB: 5 mm tooling edges
RAIL_SLOT = (1.6, 2.0)          # JLCPCB mouse-bite panels: board spacing 1.6 or 2 mm
ROUTING = 0.2                   # JLCPCB: routed board edges ±0.2 (regular precision)
TAB = 5.0                       # JLCPCB: a breakaway tab with mouse bites at least 5 mm wide,
TAB_MIN = TAB + 2 * ROUTING     # and either slot end may lie 0.2 off: 5.4 as drawn
BITE_WEB = 0.3                  # JLCPCB's mouse-bite guide: at least 0.3 of board between holes; kept between an end hole and the slot
TOOLING_HOLE = 2.0              # JLCPCB: 2 mm tooling holes
HOLE_WALL = 1.0                 # our choice: no hole's wall within 1 mm of a routed edge (JLCPCB: a tooling hole near a milling path
                                # weakens the rail); the tooling holes keep 1.5, the mounting holes 2.4
FIDUCIAL_EDGE = 3.35            # JLCPCB: 3.35 mm from the board's edge, where the conveyor holds the panel; measured to the copper, as
                                # JLCPCB's figures do (centre 3.85); its texts say 'including' the 2 mm opening (support question 3a)
FIDUCIAL_CLEAR = 1.0            # our choice: nothing routed or drilled within 1 mm of a fiducial's mask opening
EDGE_PARTS = 2.5                # JLCPCB assembly terms, 2.3: 'The distance between the body of the components and the edge of the
                                # board must be equal or greater than 2.5mm'; the rails give it on the left and right edges, where
                                # only through-hole parts must keep it too (README chapter 8)
HOLE_EDGE = 4.0                 # mounting holes at least 4 mm from the edges (02_jamma_interface.md 1.2.3)
HOLE_TIP = 12.0                 # and not within 12 mm of the tip
PANEL_MAX = 250.0               # JLCPCB: PCBA panels up to 250 x 250 mm


def kiid(name):
    return pcbnew.KIID(str(uuid.uuid5(NS, name)))


def v(p):
    return pcbnew.VECTOR2I(MM(p[0]), MM(p[1]))


def add_outline(board, path):
    for i, seg in enumerate(path):
        s = pcbnew.PCB_SHAPE(board)
        if seg[0] == "line":
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(v(seg[1]))
            s.SetEnd(v(seg[2]))
        else:
            s.SetShape(pcbnew.SHAPE_T_ARC)
            s.SetArcGeometry(v(seg[1]), v(seg[2]), v(seg[3]))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.05))
        s.SetUuidDirect(kiid(f"outline-{i}"))
        board.Add(s)


def place(board, lib_dir, lib_name, fp_name, ref, value, at, attrs=0, path=None, nets=None, show_ref=True, rot=0.0, fields=None):
    fp = pcbnew.FootprintLoad(lib_dir, fp_name)
    if fp is None:
        raise RuntimeError(f"{lib_name}:{fp_name} not found in {lib_dir}")
    fp.SetFPID(pcbnew.LIB_ID(lib_name, fp_name))
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(v(at))
    if rot:
        fp.SetOrientationDegrees(rot)
    if attrs:
        fp.SetAttributes(fp.GetAttributes() | attrs)
    if path:
        fp.SetPath(pcbnew.KIID_PATH(path))
    for name, text in (fields or {}).items():     # the symbol's own fields, as KiCad copies them when it updates the board
        fp.SetField(name, text)
        f = fp.GetField(name)
        f.SetVisible(False)
        f.SetLayer(pcbnew.F_Fab)
    if not show_ref:                       # holes, fiducials and mouse bites need no label on the silkscreen
        fp.Reference().SetVisible(False)
    board.Add(fp)
    if nets:
        for pad in fp.Pads():
            net = nets.get(pad.GetNumber())
            if net:
                pad.SetNet(board.FindNet(net))
    fp.SetLocked(True)
    # identifiers derived from the reference, so that a rebuild writes the same bytes
    fp.SetUuidDirect(kiid(f"fp-{ref}"))
    for i, pad in enumerate(fp.Pads()):
        pad.SetUuidDirect(kiid(f"fp-{ref}-pad-{i}"))
    for i, g in enumerate(fp.GraphicalItems()):
        g.SetUuidDirect(kiid(f"fp-{ref}-gr-{i}"))
    for i, z in enumerate(fp.Zones()):
        z.SetUuidDirect(kiid(f"fp-{ref}-zone-{i}"))
    for i, f in enumerate(fp.GetFields()):
        f.SetUuidDirect(kiid(f"fp-{ref}-field-{i}"))
    return fp


def build(project, spec):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(spec["thickness"]))
    ds.SetAuxOrigin(v(spec["aux_origin"]))
    ds.SetGridOrigin(v(spec["aux_origin"]))
    ds.m_TentViasFront = True
    ds.m_TentViasBack = True
    opts = board.GetPlotOptions()
    opts.SetUseGerberProtelExtensions(spec["plot"]["protel_extensions"])
    opts.SetUseAuxOrigin(spec["plot"]["use_aux_origin"])
    board.SetPlotOptions(opts)
    tb = pcbnew.TITLE_BLOCK()
    tb.SetTitle(spec["title"])
    tb.SetRevision(spec["revision"])
    board.SetTitleBlock(tb)
    # the sheet stays KiCad's default A4 (landscape, 297 x 210): the panel fits on it

    add_outline(board, spec["outline"])
    for name in sorted(set(spec["j1"]["nets"].values())):
        board.Add(pcbnew.NETINFO_ITEM(board, name))
    j1 = spec["j1"]
    own = os.path.join(project, "fcjamma.pretty")
    place(board, own, "fcjamma", j1["footprint"], "J1", j1["value"], j1["at"], path=j1["path"], nets=j1["nets"],
          fields=j1["fields"])
    hidden = dict(show_ref=False)
    lib, name = spec["hole_footprint"].split(":")
    for i, at in enumerate(spec["holes"], 1):
        place(board, os.path.join(spec["kicad_fp"], f"{lib}.pretty"), lib, name, f"H{i}", "M3", at, pcbnew.FP_BOARD_ONLY, **hidden)
    lib, name = spec["fiducial_footprint"].split(":")
    for i, at in enumerate(spec["fiducials"], 1):
        place(board, os.path.join(spec["kicad_fp"], f"{lib}.pretty"), lib, name, f"FID{i}", "Fiducial", at,
              pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM, **hidden)
    lib, name = spec["tooling_footprint"].split(":")
    for i, at in enumerate(spec["tooling"], 1):
        place(board, own, lib, name, f"TH{i}", "Tooling hole", at, **hidden)
    lib, name = spec["break_footprint"].split(":")
    for i, (x, y, rot) in enumerate(spec["break_lines"], 1):
        place(board, own, lib, name, f"MB{i}", "Mouse bites", (x, y), rot=rot, **hidden)
    return board


def write(project, spec, path):
    board = build(project, spec)
    board.Save(path)
    # pcbnew's Python module cannot set the stackup: put it into the setup, then let pcbnew read and write the file once more
    text = open(path, encoding="utf-8").read()
    if "(stackup" not in text:
        text = text.replace("\t(setup\n", "\t(setup\n" + spec["stackup"], 1)
        open(path, "w", encoding="utf-8").write(text)
    board = pcbnew.LoadBoard(path)
    board.Save(path)
    return path


# ------------------------------------------------------------------------------------------------ measuring the board
def mm(x):
    return pcbnew.ToMM(x)


def chains(poly):
    """Every closed contour of the board (outer ones and holes), as lists of points in millimetres."""
    out = []
    for i in range(poly.OutlineCount()):
        for c in [poly.COutline(i)] + [poly.CHole(i, k) for k in range(poly.HoleCount(i))]:
            out.append([(mm(c.CPoint(j).x), mm(c.CPoint(j).y)) for j in range(c.PointCount())])
    return out


def crossings(contours, axis, at):
    """Sorted coordinates where the line x = at (axis 0) or y = at (axis 1) crosses the contours' edges.  Half-open, so that
    a line through a vertex counts that crossing once."""
    other = 1 - axis
    out = []
    for pts in contours:
        for a, b in zip(pts, pts[1:] + pts[:1]):
            if (a[axis] <= at < b[axis]) or (b[axis] <= at < a[axis]):
                t = (at - a[axis]) / (b[axis] - a[axis])
                out.append(a[other] + t * (b[other] - a[other]))
    return sorted(out)


def seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy or 1e-30)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def edge_dist(contours, p):
    return min(seg_dist(p, a, b) for pts in contours for a, b in zip(pts, pts[1:] + pts[:1]))


def _ccw_within(a, lo, hi):
    """Is the angle a on the counter-clockwise sweep from lo to hi?"""
    return (a - lo) % (2 * math.pi) <= (hi - lo) % (2 * math.pi) + 1e-12


def arc_dist(p, c, r, s, m, e):
    """Distance from p to the arc about c of radius r from s through m to e (exact, not the polygon's chords)."""
    ang = lambda q: math.atan2(q[1] - c[1], q[0] - c[0])
    a0, am, a1, ap = ang(s), ang(m), ang(e), ang(p)
    on = _ccw_within(ap, a0, a1) if _ccw_within(am, a0, a1) else _ccw_within(ap, a1, a0)
    return abs(math.dist(p, c) - r) if on else min(math.dist(p, s), math.dist(p, e))


def outline_dist(items, p):
    """Distance from p to the nearest Edge.Cuts line or arc."""
    return min([seg_dist(p, it[1], it[2]) for it in items if it[0] == "line"]
               + [arc_dist(p, *it[1:6]) for it in items if it[0] == "arc"] or [float("inf")])


def facts(path, spec):
    """Read the board back and measure it."""
    board = pcbnew.LoadBoard(path)
    text = open(path, encoding="utf-8").read()
    out = []

    def fact(ok, what):
        out.append((bool(ok), what))

    poly = pcbnew.SHAPE_POLY_SET()
    ok = board.GetBoardPolygonOutlines(poly, False)       # False: do not infer an outline
    ds = board.GetDesignSettings()
    ao = ds.GetAuxOrigin()
    aox, aoy = mm(ao.x), mm(ao.y)
    # the design frame, from the drill/place origin (the panel's lower-left corner): x right from the body's left edge, y up
    x_left = BRD.PANEL_X[0]

    def design(p):
        return (p[0] - aox + x_left, aoy - p[1])

    def kicad(p):
        return (aox + p[0] - x_left, aoy - p[1])

    def inside(p):
        return ok and poly.Contains(v(kicad(p)))

    def at_of(item):
        return design((mm(item.GetPosition().x), mm(item.GetPosition().y)))

    def area_in(x0, y0, x1, y1):
        """Board area (mm²) inside a rectangle of the design frame."""
        if not ok:
            return float("nan")
        r = pcbnew.SHAPE_POLY_SET()
        r.NewOutline()
        for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            q = kicad(p)
            r.Append(MM(q[0]), MM(q[1]))
        inter = pcbnew.SHAPE_POLY_SET(poly)
        inter.BooleanIntersection(r)
        return inter.Area() / 1e12

    conts = [[design(p) for p in c] for c in chains(poly)] if ok else []
    n_slots = 2 * (len(BRD.TABS) - 1)
    holes_n = poly.HoleCount(0) if ok and poly.OutlineCount() else 0
    fact(ok and poly.OutlineCount() == 1 and holes_n == n_slots,
         f"the board is one piece: one outer contour and {n_slots} slots between the rails and the body "
         f"({poly.OutlineCount() if ok else 0} contours, {holes_n} slots)")
    # the Edge.Cuts items themselves, in the design frame, for exact distances and the shape of the corners
    items, others = [], 0
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        pt = lambda q: design((mm(q.x), mm(q.y)))
        if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            items.append(("line", pt(d.GetStart()), pt(d.GetEnd())))
        elif d.GetShape() == pcbnew.SHAPE_T_ARC:
            items.append(("arc", pt(d.GetCenter()), mm(d.GetRadius()), pt(d.GetStart()), pt(d.GetArcMid()), pt(d.GetEnd()),
                          abs(d.GetArcAngle().AsDegrees())))
        else:
            others += 1
    fact(others == 0, f"the outline is drawn with lines and arcs only ({others} other shapes)")
    bb = poly.BBox() if ok else None
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    j1 = fps.get("J1")
    if bb:
        fact(abs(mm(bb.GetLeft()) - aox) < 1e-3 and abs(mm(bb.GetBottom()) - aoy) < 1e-3,
             f"the drill/place origin is the panel's lower-left corner (origin {aox:.3f}, {aoy:.3f}; corner "
             f"{mm(bb.GetLeft()):.3f}, {mm(bb.GetBottom()):.3f} on the sheet)")
        w, h = mm(bb.GetWidth()), mm(bb.GetHeight())
        fact(abs(w - (BRD.PANEL_X[1] - BRD.PANEL_X[0])) < 1e-3 and abs(h - BRD.TOP) < 1e-3 and max(w, h) <= PANEL_MAX,
             f"the panel is {w:.3f} x {h:.3f} mm, as designed ({BRD.PANEL_X[1] - BRD.PANEL_X[0]:g} x {BRD.TOP:g}: the body "
             f"{BRD.BODY_W:g} x {BRD.BODY_H:g} with the tongue, and two rails), within JLCPCB's {PANEL_MAX:g} x {PANEL_MAX:g}")
        if j1 is not None:
            low = aoy - mm(bb.GetBottom())
            fact(abs(at_of(j1)[1] - low) < 1e-3,
                 f"the finger tips are the lowest edge of the board: nothing lies below the tip line, so the bevel can reach it "
                 f"(tip line y {at_of(j1)[1]:.3f}, lowest edge y {low:.3f})")
    go = ds.GetGridOrigin()
    fact(go.x == ao.x and go.y == ao.y, f"the grid origin is the drill/place origin ({mm(go.x):.3f}, {mm(go.y):.3f})")
    j1_id = j1.GetFPID().GetUniStringLibId() if j1 is not None else "(no J1)"
    fact(j1_id == "fcjamma:" + spec["j1"]["footprint"], f"J1 is the JAMMA edge ({j1_id})")

    # ---- the JAMMA tongue, measured on the outline 6 mm above the tip (between the body's edges only)
    t_cuts = [x for x in crossings(conts, 1, 6.0) if 0.0 < x < BRD.BODY_W]
    fact(len(t_cuts) == 4, f"6 mm above the tip the outline shows the tongue's two sides and the key slot's two walls ({len(t_cuts)} edges)")
    if len(t_cuts) == 4:
        left, k0, k1, right = t_cuts
        fact(TONGUE_WIDTH[0] - 1e-3 <= right - left <= TONGUE_WIDTH[1] + 1e-3, f"the tongue is {right - left:.3f} wide (JST 114.4-114.6)")
        fact(KEY_WIDTH[0] - 1e-3 <= k1 - k0 <= KEY_WIDTH[1] + 1e-3, f"the key slot is {k1 - k0:.3f} wide (2.5-3.0)")
        kc = (k0 + k1) / 2
        deep = [y for y in crossings(conts, 0, kc) if y > 0.0]
        depth = deep[0] if deep else 0.0
        fact(KEY_DEPTH[0] - 1e-3 <= depth <= KEY_DEPTH[1] + 1e-3, f"the key slot is {depth:.3f} deep (Hirose 11.0-11.5)")
        if j1 is not None:
            px = {p.GetNumber(): at_of(p)[0] for p in j1.Pads()}
            if all(n in px for n in ("1", "6", "8", "28")):
                fact(FINGER_TO_SIDE[0] - 1e-3 <= px["1"] - left <= FINGER_TO_SIDE[1] + 1e-3
                     and FINGER_TO_SIDE[0] - 1e-3 <= right - px["28"] <= FINGER_TO_SIDE[1] + 1e-3,
                     f"the outer fingers lie {px['1'] - left:.3f} and {right - px['28']:.3f} from the tongue's sides (JST 3.74-3.84)")
                fact(abs((kc - px["1"]) - KEY_PITCHES * PITCH) < 0.01, f"the key slot is centred on position 7 ({kc - px['1']:.3f} from finger 1)")
                fact(abs((px["28"] - px["1"]) - 27 * PITCH) < 0.01, f"fingers 1 and 28 are 27 pitches apart ({px['28'] - px['1']:.3f})")
                c6, c8 = k0 - (px["6"] + FINGER[0] / 2), (px["8"] - FINGER[0] / 2) - k1
                fact(min(c6, c8) >= SLOT_TO_COPPER - 1e-3,
                     f"fingers 6 and 8 keep their copper {SLOT_TO_COPPER} from the key slot's walls ({c6:.3f}, {c8:.3f})")
            else:
                fact(False, f"J1 has fingers 1, 6, 8 and 28 (it has {len(px)} pads)")
    for side, x0, x1, xo in (("left", 0.0, BRD.TONGUE_X0, BRD.TONGUE_X0 - 1.0),
                             ("right", BRD.TONGUE_X0 + BRD.TONGUE_W, BRD.BODY_W, BRD.TONGUE_X0 + BRD.TONGUE_W + 1.0)):
        a = area_in(x0, 0.0, x1, SHOULDER)
        fact(a < 1e-3 and inside((xo, SHOULDER + 0.05)),
             f"{side} of the tongue there is no board up to {SHOULDER:g} mm above the tip ({a:.3f} mm² of board there), "
             f"and the body starts there ({'board' if inside((xo, SHOULDER + 0.05)) else 'no board'} at {SHOULDER + 0.05:g})")
    tongue_in, body_in = inside((BRD.BODY_W / 2, 6.0)), inside((BRD.BODY_W / 2, (BRD.Y0 + BRD.TOP) / 2))
    fact(tongue_in and body_in, f"the tongue and the body are board (tongue: {tongue_in}, body: {body_in})")

    # ---- the shape of the outline: every arc is a convex corner, a corner of the key slot or a slot's round end, by its
    # radius, its sweep and the side its centre lies on (on the board for a convex corner, off it for the others)
    kinds = {"convex corner": (BRD.CORNER_R, 90.0, True), "key-slot corner": (0.5, 90.0, False),
             "slot end": (BRD.RAIL_GAP / 2, 180.0, False)}
    counts, odd = {k: 0 for k in kinds}, []
    for it in [it for it in items if it[0] == "arc"]:
        c, r, sweep = it[1], it[2], it[6]
        on_board = inside(c)
        kind = next((k for k, (wr, wa, wc) in kinds.items() if abs(r - wr) < 1e-3 and abs(sweep - wa) < 0.01 and on_board == wc), None)
        if kind:
            counts[kind] += 1
        else:
            odd.append((round(r, 3), round(sweep, 2), "centre on the board" if on_board else "centre off the board",
                        (round(c[0], 2), round(c[1], 2))))
    expect = {"convex corner": 8 if BRD.CORNER_R > 0 else 0, "key-slot corner": 2, "slot end": 2 * n_slots + 4}
    fact(not odd and counts == expect,
         f"the outline's arcs: {counts['convex corner']} convex corners R{BRD.CORNER_R:g}, {counts['key-slot corner']} R0.5 corners "
         f"at the bottom of the key slot, {counts['slot end']} half-round slot ends R{BRD.RAIL_GAP / 2:g} (expected "
         f"{expect['convex corner']}, 2, {expect['slot end']}; {len(odd)} others{': ' + str(odd[:2]) if odd else ''})")
    bad_slots = []
    for k in range(holes_n):
        c = poly.CHole(0, k)
        hb = c.BBox()
        sw, sh = mm(hb.GetWidth()), mm(hb.GetHeight())
        want = sw * (sh - sw) + math.pi * (sw / 2) ** 2
        if abs(abs(c.Area()) / 1e12 - want) > 0.05 or abs(sw - BRD.RAIL_GAP) > 1e-3:
            bad_slots.append((round(sw, 3), round(abs(c.Area()) / 1e12, 2), round(want, 2)))
    fact(holes_n and not bad_slots, f"every slot is {BRD.RAIL_GAP:g} mm wide with half-round ends ({len(bad_slots)} not"
         + (f"; e.g. width, area, a slot's area {bad_slots[0]})" if bad_slots else ")"))

    if j1 is not None:
        deg = j1.GetOrientation().AsDegrees()
        fact(abs(deg) < 1e-6 and j1.GetLayer() == pcbnew.F_Cu and j1.IsLocked(),
             f"J1 is not turned, on the parts side, locked ({deg:g}°, {board.GetLayerName(j1.GetLayer())}, "
             f"{'locked' if j1.IsLocked() else 'not locked'})")
        pads = list(j1.Pads())
        spans = []
        for p in pads:
            box = p.GetBoundingBox()
            (x0, y1), (x1, y0) = design((mm(box.GetLeft()), mm(box.GetTop()))), design((mm(box.GetRight()), mm(box.GetBottom())))
            spans.append((round(y0, 4), round(y1, 4), round(x1 - x0, 4)))
        wrong = [s_ for s_ in spans if s_ != (FINGER[1], FINGER[2], FINGER[0])]
        fact(len(pads) == 54 and not wrong,
             f"all 54 fingers are {FINGER[0]} wide and run from {FINGER[1]} to {FINGER[2]} mm above the tip ({len(pads)} fingers"
             + (f"; e.g. {wrong[0][2]} wide, {wrong[0][0]}-{wrong[0][1]})" if wrong else ")"))
        off = sorted(p.GetNumber() for p in pads if not inside(at_of(p)))
        fact(not off, f"every finger lies on the tongue ({len(off)} do not{': ' + ', '.join(off[:5]) if off else ''})")
        nets = {p.GetNumber(): p.GetNetname() for p in pads}
        want = spec["j1"]["nets"]
        diff = sorted(k for k in set(nets) | set(want) if nets.get(k) != want.get(k))
        fact(len(want) == 54 and not diff,
             f"every finger carries the net KiCad's netlist gives it, and no other (KiCad's schematic parity checks it again) "
             f"({len(want)} pins in the netlist, {len(diff)} differ"
             + (f"; pad {diff[0]}: board '{nets.get(diff[0])}', netlist '{want.get(diff[0])}')" if diff else ")"))
        open_ = sorted(n for n, net in nets.items() if net.startswith("unconnected-(J1-"))
        fact(set(open_) == UNWIRED, f"exactly the six open JAMMA positions (5, 6, 11, E, F, M) are left unconnected ({', '.join(open_) or 'none'})")
        path_s, props = schematic_symbol(spec["schematic_dir"])
        path_b = str(j1.GetPath().AsString())
        fact(path_b == path_s, f"J1 is linked to the J1 symbol of the jamma sheet (board {path_b or '(none)'}, schematic {path_s})")
        fields = spec["j1"]["fields"]
        bad = [k for k in fields if not (j1.HasField(k) and j1.GetFieldText(k) == props.get(k))]
        fact(bool(fields) and not bad, f"J1 carries its symbol's fields, as the schematic file has them ({len(fields)} fields"
             + (f"; {bad[0]}: board '{j1.GetFieldText(bad[0]) if j1.HasField(bad[0]) else '(missing)'}', schematic '{props.get(bad[0])}')"
                if bad else ")"))

    # ---- mounting holes: compared with design/board.py, on the body, clear of every edge and of the tip
    holes = sorted((f for r, f in fps.items() if re.fullmatch(r"H\d+", r)), key=lambda f: int(f.GetReference()[1:]))
    got = [at_of(h) for h in holes]
    moved = [f"{h.GetReference()} at ({a[0]:g}, {a[1]:g})" for h, a, b in zip(holes, got, BRD.HOLES) if math.dist(a, b) >= 1e-4]
    fact(len(holes) == len(BRD.HOLES) == 7 and not moved,
         f"{len(holes)} mounting holes, where design/board.py puts them (7{'; ' + ', '.join(moved[:3]) if moved else ''})")
    for h, at in zip(holes, got):
        pads = list(h.Pads())
        drills = [round(mm(p.GetDrillSize().x), 3) for p in pads]
        npth = all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in pads)
        fact(len(pads) == 1 and npth and abs(drills[0] - 3.2) < 1e-6,
             f"{h.GetReference()}: M3 hole of 3.2 mm, not plated ({len(pads)} hole of {drills}, {'not plated' if npth else 'plated'})")
        on = inside(at) and 0.0 <= at[0] <= BRD.BODY_W
        d = edge_dist(conts, at) if conts else 0.0
        fact(on and d >= HOLE_EDGE - 1e-6, f"{h.GetReference()}: on the body, at least {HOLE_EDGE:g} mm from every edge "
             + (f"({d:.2f})" if on else f"(it lies off the body, at ({at[0]:g}, {at[1]:g}))"))
        fact(at[1] - 1.6 >= HOLE_TIP, f"{h.GetReference()}: not within {HOLE_TIP:g} mm of the tip ({at[1] - 1.6:.2f})")
    for cx, cy in ((0.0, BRD.Y0), (BRD.BODY_W, BRD.Y0), (0.0, BRD.TOP), (BRD.BODY_W, BRD.TOP)):
        near = min((math.dist(at, (cx, cy)) for at in got), default=99.0)
        fact(near <= 8.0, f"a mounting hole near the body's corner ({cx:g}, {cy:g}) (the nearest {near:.1f} mm away)")

    # ---- the rails, the slots and the tabs, measured on the outline
    xl, xr = BRD.PANEL_X
    y_mid = (BRD.TABS[1] + BRD.TABS[2]) / 2          # half way between two tabs: rail | slot | body | slot | rail
    cuts = crossings(conts, 1, y_mid)
    widths = [b - a for a, b in zip(cuts[0::2], cuts[1::2])]
    gaps = [b - a for a, b in zip(cuts[1::2], cuts[2::2])]
    fact(len(widths) == 3 and abs(widths[0] - RAIL) < 1e-3 and abs(widths[2] - RAIL) < 1e-3,
         f"two rails, {RAIL:g} mm wide (JLCPCB) ({', '.join(f'{w_:.2f}' for w_ in widths[0::2])})")
    fact(len(gaps) == 2 and all(RAIL_SLOT[0] - 1e-3 <= g <= RAIL_SLOT[1] + 1e-3 for g in gaps),
         f"the slots between the rails and the body are {', '.join(f'{g:.2f}' for g in gaps)} mm (JLCPCB 1.6 or 2)")
    tab_centres = {}
    for side, x_rail, x_slot, x_edge, x_far in (("left", xl + RAIL / 2, -BRD.RAIL_GAP / 2, -0.05, -BRD.RAIL_GAP + 0.05),
                                                ("right", xr - RAIL / 2, BRD.BODY_W + BRD.RAIL_GAP / 2, BRD.BODY_W + 0.05,
                                                 BRD.BODY_W + BRD.RAIL_GAP - 0.05)):
        ends = (inside((x_rail, 0.5)), inside((x_rail, BRD.TOP - 0.5)))
        fact(all(ends), f"{side} rail: runs from the tip line to the top (board at y 0.5: {ends[0]}, at y {BRD.TOP - 0.5:g}: {ends[1]})")
        ys = crossings(conts, 0, x_slot)
        tabs = [(a, b) for a, b in zip(ys[0::2], ys[1::2]) if inside((x_slot, (a + b) / 2))]
        tab_centres[side] = [(a + b) / 2 for a, b in tabs]
        # the narrowest width of a tab lies on the slot's centre line, between the round slot ends that face each other
        # across it: measured on those arcs themselves, not on the outline's polygon (whose chords read about 0.005 wide)
        ends = sorted(it[1][1] for it in items if it[0] == "arc" and abs(it[2] - BRD.RAIL_GAP / 2) < 1e-3
                      and abs(it[6] - 180.0) < 0.01 and abs(it[1][0] - x_slot) < 1e-3)
        widths_t = []
        for c in tab_centres[side]:
            below, above = [y for y in ends if y < c], [y for y in ends if y > c]
            widths_t.append(min(above) - max(below) - BRD.RAIL_GAP if below and above else 0.0)
        narrow = min(widths_t, default=0.0)
        fact(len(tabs) == len(BRD.TABS) and all(abs(c - t) < 0.05 for c, t in zip(tab_centres[side], BRD.TABS)),
             f"{side}: {len(tabs)} tabs at y {', '.join(f'{c:.1f}' for c in tab_centres[side])} (design/board.py "
             f"{', '.join(f'{t:g}' for t in BRD.TABS)})")
        fact(tabs and narrow >= TAB_MIN - 1e-3, f"{side}: the tabs are at least {TAB_MIN:g} mm wide (JLCPCB {TAB:g}, and ±{ROUTING:g} "
             f"on each slot end) (narrowest {narrow:.3f})")
        loose = [f"{c:.1f}" for c in tab_centres[side] if not all(inside((x, c)) for x in (x_edge, x_slot, x_far))]
        fact(tabs and not loose, f"{side}: every tab bridges the whole slot, from the rail to the body ({len(loose)} do not"
             + (f": y {', '.join(loose)})" if loose else ")"))

    # ---- mouse bites: one line on each measured tab, on the body's side of the edge, its keep-out on the body
    bites = sorted((f for r, f in fps.items() if re.fullmatch(r"MB\d+", r)), key=lambda f: int(f.GetReference()[2:]))
    fact(len(bites) == 2 * len(BRD.TABS), f"{len(bites)} lines of mouse bites ({2 * len(BRD.TABS)}: one on each tab)")
    seen, mb_y = {"left": [], "right": []}, {"left": [], "right": []}
    for mb in bites:
        at = at_of(mb)
        side = "left" if at[0] < BRD.BODY_W / 2 else "right"
        inset = at[0] if side == "left" else BRD.BODY_W - at[0]
        rot = round(mb.GetOrientation().AsDegrees()) % 360
        hx = [at_of(p) for p in mb.Pads()]
        drills = sorted({round(mm(p.GetDrillSize().x), 3) for p in mb.Pads()})
        tab = [c for c in tab_centres.get(side, []) if abs(c - at[1]) < 0.01]
        seen[side] += tab
        mb_y[side].append(at[1])
        zones = [z for z in mb.Zones() if z.GetZoneName() == "Breakaway tab: keep clear"]
        zb = [design((mm(z.GetBoundingBox().GetLeft()), 0))[0] for z in zones] + \
             [design((mm(z.GetBoundingBox().GetRight()), 0))[0] for z in zones]
        on_body = bool(zones) and (min(zb) >= -0.01 and max(zb) <= 6.0 if side == "left"
                                   else min(zb) >= BRD.BODY_W - 6.0 and max(zb) <= BRD.BODY_W + 0.01)
        fact(len(tab) == 1 and 0.0 < inset <= 0.5 and rot == (0 if side == "left" else 180),
             f"{mb.GetReference()}: on a tab ({side}, y {at[1]:.2f}), {inset:.2f} mm inside the body's edge, turned {rot}°")
        npth = all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in mb.Pads())
        fact(5 <= len(hx) <= 8 and npth and all(0.0 <= x <= BRD.BODY_W and inside((x, y)) for x, y in hx),
             f"{mb.GetReference()}: {len(hx)} holes of {drills}, {'not plated' if npth else 'plated'}, every one in the body")
        web = min((outline_dist(items, (x, y)) - mm(p.GetDrillSize().x) / 2 for (x, y), p in zip(hx, mb.Pads())), default=0.0)
        fact(web >= BITE_WEB - 1e-6, f"{mb.GetReference()}: every hole keeps {BITE_WEB:g} mm of board from the routed edges, the slots' "
             f"round ends included (JLCPCB's least spacing of mouse bites) ({web:.3f})")
        fact(on_body, f"{mb.GetReference()}: its keep-out lies on the body's side"
             + (f" (x {min(zb):.2f} to {max(zb):.2f})" if zones else " (no keep-out)"))
    for side in ("left", "right"):
        fact(sorted(seen[side]) == sorted(tab_centres.get(side, [])) and len(set(seen[side])) == len(seen[side]),
             f"{side}: exactly one line of mouse bites on every tab (lines at y {', '.join(f'{y:.1f}' for y in sorted(mb_y[side]))}; "
             f"tabs at {', '.join(f'{y:.1f}' for y in sorted(tab_centres.get(side, [])))})")

    # ---- tooling holes and fiducials
    tools = sorted((f for r, f in fps.items() if re.fullmatch(r"TH\d+", r)), key=lambda f: int(f.GetReference()[2:]))
    tat = [at_of(t) for t in tools]
    moved = [f"{t.GetReference()} at ({a[0]:g}, {a[1]:g})" for t, a, b in zip(tools, tat, BRD.TOOLING) if math.dist(a, b) >= 1e-4]
    fact(len(tools) == len(BRD.TOOLING) == 4 and not moved,
         f"{len(tools)} tooling holes, where design/board.py puts them (4{'; ' + ', '.join(moved[:2]) if moved else ''})")
    for th, at in zip(tools, tat):
        pads = list(th.Pads())
        drill = mm(pads[0].GetDrillSize().x) if pads else 0.0
        npth = bool(pads) and all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in pads)
        on_rail = min(abs(at[0] - (xl + RAIL / 2)), abs(at[0] - (xr - RAIL / 2))) < 1e-3
        fact(len(pads) == 1 and npth and abs(drill - TOOLING_HOLE) < 1e-6 and on_rail and inside(at),
             f"{th.GetReference()}: {TOOLING_HOLE:g} mm, not plated, centred on a rail ({len(pads)} hole of {drill:g} mm, "
             f"{'not plated' if npth else 'plated'}, at x {at[0]:.2f})")
        wall = outline_dist(items, at) - drill / 2 if inside(at) else -1.0
        fact(wall >= HOLE_WALL - 1e-6, f"{th.GetReference()}: its wall at least {HOLE_WALL:g} mm from every routed edge ({wall:.2f})")
    fids = sorted((f for r, f in fps.items() if re.fullmatch(r"FID\d+", r)), key=lambda f: int(f.GetReference()[3:]))
    fat = [at_of(f) for f in fids]
    moved = [f"{f.GetReference()} at ({a[0]:g}, {a[1]:g})" for f, a, b in zip(fids, fat, BRD.FIDUCIALS) if math.dist(a, b) >= 1e-4]
    fact(len(fids) == 3 and not moved, f"{len(fids)} fiducials, where design/board.py puts them (3{'; ' + ', '.join(moved[:2]) if moved else ''})")
    if len(fat) == 3:
        (ax, ay), (bx, by), (cx, cy) = fat
        area2 = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
        fact(area2 > 100.0, f"the fiducials are not on one line (twice the triangle's area {area2:.0f} mm²)")
    for f, at in zip(fids, fat):
        ref = f.GetReference()
        copper = [p for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu)]
        r = mm(copper[0].GetSize().x) / 2 if copper else 0.0
        opening = 2 * r + 2 * mm(copper[0].GetSolderMaskExpansion(pcbnew.F_Mask)) if copper else 0.0
        outer = min(at[0] - xl, xr - at[0])
        side = "left" if at[0] < BRD.BODY_W / 2 else "right"
        fact(inside(at) and (at[0] < -BRD.RAIL_GAP or at[0] > BRD.BODY_W + BRD.RAIL_GAP), f"{ref}: on a rail (at {at[0]:.2f}, {at[1]:.2f})")
        fact(abs(r - 0.5) < 1e-6 and abs(opening - 2.0) < 1e-6, f"{ref}: 1 mm copper, 2 mm mask opening (JLCPCB) ({2 * r:g}, {opening:g})")
        fact(outer - r >= FIDUCIAL_EDGE - 1e-6, f"{ref}: its copper {outer - r:.2f} mm from the panel's outer edge (JLCPCB 3.35)")
        dy = min((abs(at[1] - t) for t in tab_centres.get(side, [])), default=99.0)
        fact(dy <= TAB / 2, f"{ref}: level with a tab, where the rail is held ({dy:.2f} from the nearest tab's centre)")
        routed = outline_dist(items, at)
        drilled = min((math.dist(at, at_of(p)) - mm(p.GetDrillSize().x) / 2 for o in tools + holes + bites for p in o.Pads()),
                      default=99.0)
        fact(min(routed, drilled) - opening / 2 >= FIDUCIAL_CLEAR - 1e-6,
             f"{ref}: nothing routed or drilled within {FIDUCIAL_CLEAR:g} mm of its mask opening (routed edge {routed - opening / 2:.2f}, "
             f"hole {drilled - opening / 2:.1f}; the copper is {routed - r:.2f} from the nearest routed edge)")

    # ---- every part has a courtyard (KiCad's DRC only checks courtyards it is given), and lies on the body: not on a rail,
    # over a slot or off the board (J1's reaches 0.5 past the tip on purpose; the tooling holes and fiducials are checked above)
    bare = [r for r, f in fps.items() if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() + f.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() == 0]
    fact(not bare, f"every footprint has a courtyard ({', '.join(sorted(bare)[:5]) or 'all do'})")
    astray, near_edge, parts = [], [], set()
    for ref, f in sorted(fps.items()):
        if ref == "J1" or re.fullmatch(r"(TH|FID)\d+", ref):
            continue
        for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            crt = f.GetCourtyard(layer)
            if crt.OutlineCount() == 0:
                continue
            off_board = pcbnew.SHAPE_POLY_SET(crt)
            off_board.BooleanSubtract(poly)
            cb = crt.BBox()
            cx0, cx1 = design((mm(cb.GetLeft()), 0))[0], design((mm(cb.GetRight()), 0))[0]
            if off_board.Area() / 1e12 > 1e-3 or cx0 < -0.1 or cx1 > BRD.BODY_W + 0.1:
                astray.append(f"{ref} x {cx0:.2f}-{cx1:.2f}, {off_board.Area() / 1e12:.2f} mm² off the board")
            if re.fullmatch(r"(H|MB)\d+", ref):          # holes and mouse bites are not parts with a body
                continue
            parts.add(ref)
            cy0, cy1 = design((0, mm(cb.GetBottom())))[1], design((0, mm(cb.GetTop())))[1]
            beside = cx0 < BRD.TONGUE_X0 or cx1 > BRD.TONGUE_X0 + BRD.TONGUE_W     # over the body's lower edge, not the tongue
            gap = min(BRD.TOP - cy1, cy0 - BRD.Y0 if beside else 99.0)
            if f.GetAttributes() & pcbnew.FP_THROUGH_HOLE:                          # through hole: the left and right edges too
                gap = min(gap, cx0, BRD.BODY_W - cx1)
            if gap < EDGE_PARTS - 1e-6:
                near_edge.append(f"{ref} {gap:.2f} mm")
    fact(not astray, f"every part's courtyard lies on the body, between its left and right edges and inside the outline "
         f"({'; '.join(astray[:3]) or 'all do'})")
    fact(not near_edge, f"every part's courtyard keeps {EDGE_PARTS:g} mm from the edges without a rail (the top edge, the body's "
         f"lower edge beside the tongue; JLCPCB), a through-hole part's from every edge (parts placed so far: {len(parts)}"
         + (f"; too near: {len(near_edge)}, {'; '.join(near_edge[:3])})" if near_edge else ", all clear)"))

    # ---- settings
    fact(board.GetCopperLayerCount() == 2, f"two copper layers ({board.GetCopperLayerCount()})")
    t = mm(ds.GetBoardThickness())
    fact(abs(t - THICKNESS) < 1e-6, f"the board is {THICKNESS} mm thick, for the JAMMA connectors' 1.6 ± 0.15 ({t:g})")
    stack = re.search(r"\(stackup(.*?)\n\t\t\)", text, re.S)
    layers = re.findall(r"\(thickness ([0-9.]+)\)", stack.group(1)) if stack else []
    fact(len(layers) == 5 and abs(sum(float(x) for x in layers) - THICKNESS) < 1e-6,
         f"the stackup adds up to the board's {THICKNESS} mm ({sum(float(x) for x in layers):.3f} in {len(layers)} layers)")
    finish = re.search(r'\(copper_finish "([^"]*)"\)', stack.group(1)) if stack else None
    edge = re.search(r"\(edge_connector (\w+)\)", stack.group(1)) if stack else None
    fact(bool(finish and edge) and finish.group(1) == "ENIG" and edge.group(1) == "bevelled",
         f"stackup: ENIG finish and a bevelled edge connector (gold fingers) ({finish.group(1) if finish else 'no finish'}, "
         f"{edge.group(1) if edge else 'no edge connector'})")
    fact(ds.m_TentViasFront and ds.m_TentViasBack, f"vias are tented on both sides (front {ds.m_TentViasFront}, back {ds.m_TentViasBack})")
    opts = board.GetPlotOptions()
    fact(opts.GetUseGerberProtelExtensions(), f"plot settings: Protel file names (JLCPCB's KiCad guide) ({opts.GetUseGerberProtelExtensions()})")
    fact(opts.GetUseAuxOrigin(), f"plot settings: Gerbers from the drill/place origin, the frame of the drill and position files "
         f"({opts.GetUseAuxOrigin()})")
    return out

def schematic_symbol(sch_dir):
    """The path KiCad gives J1's footprint (the jamma sheet's identifier, then the J1 symbol's) and the J1 symbol's
    properties, read from the schematic files themselves."""
    root = sx_parse(open(os.path.join(sch_dir, "fcjamma.kicad_sch"), encoding="utf-8").read())
    sheet = None
    for s in sx_find(root, "sheet"):
        props = {str(p[1]): str(p[2]) for p in sx_find(s, "property")}
        if props.get("Sheetfile") == "jamma.kicad_sch":
            sheet = str(sx_first(s, "uuid")[1])
    sub = sx_parse(open(os.path.join(sch_dir, "jamma.kicad_sch"), encoding="utf-8").read())
    symbol, props = None, {}
    for s in sx_find(sub, "symbol"):
        p = {str(q[1]): str(q[2]) for q in sx_find(s, "property")}
        if p.get("Reference") == "J1":
            symbol, props = str(sx_first(s, "uuid")[1]), p
    return (f"/{sheet}/{symbol}" if sheet and symbol else "(not found in the schematic)"), props


def main():
    project, spec_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    spec = json.load(open(spec_path, encoding="utf-8"))
    # built in a scratch folder without a project file, so that the saved bytes do not depend on where it is checked
    with tempfile.TemporaryDirectory(prefix="fcjamma-make-board-") as tmp:
        path = write(project, spec, os.path.join(tmp, "fcjamma.kicad_pcb"))
        shutil.copy(path, out_path)            # before the checks, so that a crash in them still leaves the board to look at
        results = facts(path, spec)
    failed = [what for ok, what in results if not ok]
    for what in failed:
        print("board check failed:", what)
    print(f"board: {len(results) - len(failed)}/{len(results)} checks hold")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:             # one readable line for tools/build.py instead of a traceback
        print(f"make_board.py stopped: {type(e).__name__}: {e}")
        sys.exit(1)
