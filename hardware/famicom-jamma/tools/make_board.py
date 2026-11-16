#!/usr/bin/python3
"""Build kicad/fcjamma.kicad_pcb from design/board.py, then read it back and check it.

    /usr/bin/python3 tools/make_board.py <kicad project folder> <board.json>

tools/build.py writes board.json from design/board.py, the circuit and KiCad's netlist (J1's nets, path and fields) and runs
this script with the system Python, which has KiCad's pcbnew module.  The board holds, so far: the outline (body, JAMMA
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
import sys
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
TAB = 5.0                       # JLCPCB: a breakaway tab with mouse bites at least 5 mm wide
TOOLING_HOLE = 2.0              # JLCPCB: 2 mm tooling holes
FIDUCIAL_EDGE = 3.35            # JLCPCB: fiducial copper at least 3.35 mm from the board's edge
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


def write(project, spec):
    path = os.path.join(project, "fcjamma.kicad_pcb")
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
    """Sorted coordinates where the line x = at (axis 0) or y = at (axis 1) crosses the contours' edges."""
    other = 1 - axis
    out = []
    for pts in contours:
        for a, b in zip(pts, pts[1:] + pts[:1]):
            if (a[axis] - at) * (b[axis] - at) < 0:
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

    conts = [[design(p) for p in c] for c in chains(poly)] if ok else []
    n_slots = 2 * (len(BRD.TABS) - 1)
    fact(ok and poly.OutlineCount() == 1 and poly.HoleCount(0) == n_slots,
         f"the board is one piece: one outer contour and {n_slots} slots between the rails and the body")
    bb = poly.BBox() if ok else None
    if bb:
        fact(abs(mm(bb.GetLeft()) - aox) < 1e-3 and abs(mm(bb.GetBottom()) - aoy) < 1e-3,
             "the drill/place origin is the panel's lower-left corner")
        w, h = mm(bb.GetWidth()), mm(bb.GetHeight())
        fact(abs(w - (BRD.PANEL_X[1] - BRD.PANEL_X[0])) < 1e-3 and abs(h - BRD.TOP) < 1e-3 and max(w, h) <= PANEL_MAX,
             f"the panel is {w:.1f} x {h:.1f} mm (the body {BRD.BODY_W:g} x {BRD.BODY_H:g} with the tongue, and two rails), "
             f"within JLCPCB's {PANEL_MAX:g} x {PANEL_MAX:g}")
    fact(ds.GetGridOrigin().x == ao.x and ds.GetGridOrigin().y == ao.y, "the grid origin is the drill/place origin")

    # ---- the JAMMA tongue, measured on the outline 6 mm above the tip (between the body's edges only)
    t_cuts = [x for x in crossings(conts, 1, 6.0) if 0.0 < x < BRD.BODY_W]
    fact(len(t_cuts) == 4, f"6 mm above the tip the outline shows the tongue's two sides and the key slot's two walls ({len(t_cuts)} edges)")
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    j1 = fps.get("J1")
    fact(j1 is not None and j1.GetFPID().GetUniStringLibId() == "fcjamma:" + spec["j1"]["footprint"], "J1 is the JAMMA edge")
    if len(t_cuts) == 4:
        left, k0, k1, right = t_cuts
        fact(TONGUE_WIDTH[0] - 1e-3 <= right - left <= TONGUE_WIDTH[1] + 1e-3, f"the tongue is {right - left:.3f} wide (JST 114.4-114.6)")
        fact(KEY_WIDTH[0] - 1e-3 <= k1 - k0 <= KEY_WIDTH[1] + 1e-3, f"the key slot is {k1 - k0:.3f} wide (2.5-3.0)")
        kc = (k0 + k1) / 2
        deep = [y for y in crossings(conts, 0, kc) if 0.0 < y < BRD.Y0]
        depth = deep[0] if deep else 0.0
        fact(KEY_DEPTH[0] - 1e-3 <= depth <= KEY_DEPTH[1] + 1e-3, f"the key slot is {depth:.3f} deep (Hirose 11.0-11.5)")
        if j1 is not None:
            px = {p.GetNumber(): at_of(p)[0] for p in j1.Pads()}
            if all(n in px for n in ("1", "6", "8", "28")):
                fact(FINGER_TO_SIDE[0] - 1e-3 <= px["1"] - left <= FINGER_TO_SIDE[1] + 1e-3
                     and FINGER_TO_SIDE[0] - 1e-3 <= right - px["28"] <= FINGER_TO_SIDE[1] + 1e-3,
                     f"the outer fingers lie {px['1'] - left:.3f} and {right - px['28']:.3f} from the tongue's sides (JST 3.74-3.84)")
                fact(abs((kc - px["1"]) - KEY_PITCHES * PITCH) < 0.01, f"the key slot is centred on position 7 ({kc - px['1']:.3f} from finger 1)")
                fact(abs((px["28"] - px["1"]) - 27 * PITCH) < 0.01, "fingers 1 and 28 are 27 pitches apart")
                fact(k0 - (px["6"] + FINGER[0] / 2) >= SLOT_TO_COPPER - 1e-3 and (px["8"] - FINGER[0] / 2) - k1 >= SLOT_TO_COPPER - 1e-3,
                     f"fingers 6 and 8 keep their copper {SLOT_TO_COPPER} from the key slot's walls")
            else:
                fact(False, "J1 has fingers 1, 6, 8 and 28")
    fact(not inside((BRD.TONGUE_X0 - 1.0, SHOULDER - 0.05)) and not inside((BRD.TONGUE_X0 + BRD.TONGUE_W + 1.0, SHOULDER - 0.05))
         and inside((BRD.TONGUE_X0 - 1.0, SHOULDER + 0.05)) and inside((BRD.TONGUE_X0 + BRD.TONGUE_W + 1.0, SHOULDER + 0.05)),
         f"beside the tongue the body starts {SHOULDER:g} mm above the tip (room for the connector's housing)")
    fact(inside((BRD.BODY_W / 2, 6.0)) and inside((BRD.BODY_W / 2, (BRD.Y0 + BRD.TOP) / 2)), "the tongue and the body are board")

    if j1 is not None:
        fact(abs(j1.GetOrientation().AsDegrees()) < 1e-6 and j1.GetLayer() == pcbnew.F_Cu and j1.IsLocked(),
             "J1 is not turned, on the parts side, locked")
        pads = list(j1.Pads())
        spans = []
        for p in pads:
            box = p.GetBoundingBox()
            (x0, y1), (x1, y0) = design((mm(box.GetLeft()), mm(box.GetTop()))), design((mm(box.GetRight()), mm(box.GetBottom())))
            spans.append((round(y0, 4), round(y1, 4), round(x1 - x0, 4)))
        fact(len(pads) == 54 and all(s == (FINGER[1], FINGER[2], FINGER[0]) for s in spans),
             f"all 54 fingers are {FINGER[0]} wide and run from {FINGER[1]} to {FINGER[2]} mm above the tip")
        fact(all(inside(at_of(p)) for p in pads), "every finger lies on the tongue")
        nets = {p.GetNumber(): p.GetNetname() for p in pads}
        want = spec["j1"]["nets"]
        fact(len(want) == 54 and nets == want, "every finger carries the net KiCad's netlist gives it, and no other")
        fact({n for n, net in nets.items() if net.startswith("unconnected-(J1-")} == UNWIRED,
             "exactly the six open JAMMA positions (5, 6, 11, E, F, M) are left unconnected")
        fact(str(j1.GetPath().AsString()) == schematic_path(spec["schematic_dir"]),
             "J1 is linked to the J1 symbol of the jamma sheet (identifiers read from the schematic files)")
        fields = spec["j1"]["fields"]
        fact(bool(fields) and all(j1.HasField(k) and j1.GetFieldText(k) == val for k, val in fields.items()),
             "J1 carries its symbol's fields")

    # ---- mounting holes: compared with design/board.py, on the body, clear of every edge and of the tip
    holes = sorted((f for r, f in fps.items() if re.fullmatch(r"H\d+", r)), key=lambda f: int(f.GetReference()[1:]))
    got = [at_of(h) for h in holes]
    fact(len(holes) == len(BRD.HOLES) == 7 and all(math.dist(a, b) < 1e-4 for a, b in zip(got, BRD.HOLES)),
         f"{len(holes)} mounting holes, where design/board.py puts them")
    for h, at in zip(holes, got):
        pads = list(h.Pads())
        fact(len(pads) == 1 and pads[0].GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and abs(mm(pads[0].GetDrillSize().x) - 3.2) < 1e-6,
             f"{h.GetReference()}: M3 hole of 3.2 mm, not plated")
        d = edge_dist(conts, at) if conts else 0.0
        fact(inside(at) and 0.0 <= at[0] <= BRD.BODY_W and d >= HOLE_EDGE - 1e-6,
             f"{h.GetReference()}: on the body, at least {HOLE_EDGE:g} mm from every edge ({d:.2f})")
        fact(at[1] - 1.6 >= HOLE_TIP, f"{h.GetReference()}: not within {HOLE_TIP:g} mm of the tip")
    for cx, cy in ((0.0, BRD.Y0), (BRD.BODY_W, BRD.Y0), (0.0, BRD.TOP), (BRD.BODY_W, BRD.TOP)):
        fact(any(math.dist(at, (cx, cy)) <= 8.0 for at in got), f"a mounting hole near the body's corner ({cx:g}, {cy:g})")

    # ---- the rails: width, slot, tabs, mouse bites, tooling holes and fiducials
    xl, xr = BRD.PANEL_X
    y_mid = (BRD.TABS[1] + BRD.TABS[2]) / 2          # half way between two tabs: rail | slot | body | slot | rail
    cuts = crossings(conts, 1, y_mid)
    widths = [b - a for a, b in zip(cuts[0::2], cuts[1::2])]
    gaps = [b - a for a, b in zip(cuts[1::2], cuts[2::2])]
    fact(len(widths) == 3 and abs(widths[0] - RAIL) < 1e-3 and abs(widths[2] - RAIL) < 1e-3,
         f"two rails, {RAIL:g} mm wide (JLCPCB)")
    fact(len(gaps) == 2 and all(RAIL_SLOT[0] - 1e-3 <= g <= RAIL_SLOT[1] + 1e-3 for g in gaps),
         f"the slots between the rails and the body are {', '.join(f'{g:.2f}' for g in gaps)} mm (JLCPCB 1.6 or 2)")
    for side, x_rail, x_slot, x_body in (("left", xl + RAIL / 2, -BRD.RAIL_GAP / 2, 1.0),
                                         ("right", xr - RAIL / 2, BRD.BODY_W + BRD.RAIL_GAP / 2, BRD.BODY_W - 1.0)):
        fact(inside((x_rail, 0.5)) and inside((x_rail, BRD.TOP - 0.5)), f"{side} rail: runs from the tip line to the top")
        ys = crossings(conts, 0, x_slot)
        tabs = [(a, b) for a, b in zip(ys[0::2], ys[1::2]) if inside((x_slot, (a + b) / 2))]
        fact(len(tabs) == len(BRD.TABS) and all(b - a >= TAB - 0.01 for a, b in tabs) and all(inside((x_body, t)) for t in BRD.TABS),
             f"{side}: {len(tabs)} tabs join the rail to the body, the narrowest {min((b - a for a, b in tabs), default=0):.2f} mm "
             f"(JLCPCB at least {TAB:g})")
    bites = sorted((f for r, f in fps.items() if re.fullmatch(r"MB\d+", r)), key=lambda f: int(f.GetReference()[2:]))
    fact(len(bites) == 2 * len(BRD.TABS), f"{len(bites)} lines of mouse bites, one on each tab")
    for mb in bites:
        at = at_of(mb)
        hx = [at_of(p) for p in mb.Pads()]
        ys = sorted(y for _, y in hx)
        fact(len(hx) == 9 and all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in mb.Pads())
             and any(abs(at[1] - t) < 1e-4 for t in BRD.TABS) and all(abs(x - at[0]) < 1e-4 for x, _ in hx)
             and min(abs(at[0]), abs(at[0] - BRD.BODY_W)) <= 0.5 and inside(at) and ys[-1] - ys[0] >= TAB,
             f"{mb.GetReference()}: 9 holes across its tab, just inside the body's edge")
    tools = sorted((f for r, f in fps.items() if re.fullmatch(r"TH\d+", r)), key=lambda f: int(f.GetReference()[2:]))
    fact(len(tools) == 4, f"{len(tools)} tooling holes")
    for th in tools:
        at = at_of(th)
        pads = list(th.Pads())
        on_rail = min(abs(at[0] - (xl + RAIL / 2)), abs(at[0] - (xr - RAIL / 2))) < 1e-3
        fact(len(pads) == 1 and pads[0].GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and abs(mm(pads[0].GetDrillSize().x) - TOOLING_HOLE) < 1e-6
             and on_rail and inside(at) and 3.0 <= at[1] <= BRD.TOP - 3.0, f"{th.GetReference()}: {TOOLING_HOLE:g} mm, not plated, centred on a rail")
    fids = sorted((f for r, f in fps.items() if re.fullmatch(r"FID\d+", r)), key=lambda f: int(f.GetReference()[3:]))
    fat = [at_of(f) for f in fids]
    fact(len(fids) == 3 and all(math.dist(a, b) < 1e-4 for a, b in zip(fat, BRD.FIDUCIALS)),
         f"{len(fids)} fiducials, where design/board.py puts them")
    if len(fat) == 3:
        (ax, ay), (bx, by), (cx, cy) = fat
        fact(abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) > 100.0, "the fiducials are not on one line")
    for f, at in zip(fids, fat):
        copper = [p for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu)]
        r = mm(copper[0].GetSize().x) / 2 if copper else 0.0
        outer = min(at[0] - xl, xr - at[0])
        clear = min((math.dist(at, at_of(o)) for o in tools + holes), default=99.0)
        fact(inside(at) and (at[0] < -BRD.RAIL_GAP or at[0] > BRD.BODY_W + BRD.RAIL_GAP) and outer - r >= FIDUCIAL_EDGE - 1e-6
             and abs(r - 0.5) < 1e-6 and clear >= 3.0,
             f"{f.GetReference()}: 1 mm copper on a rail, {outer - r:.2f} mm from the panel's edge (JLCPCB 3.35), clear of the holes")

    # ---- settings
    fact(board.GetCopperLayerCount() == 2, "two copper layers")
    fact(abs(mm(ds.GetBoardThickness()) - THICKNESS) < 1e-6, f"board {THICKNESS} mm thick (the JAMMA connectors' 1.6 ± 0.15)")
    stack = re.search(r"\(stackup(.*?)\n\t\t\)", text, re.S)
    layers = re.findall(r"\(thickness ([0-9.]+)\)", stack.group(1)) if stack else []
    fact(len(layers) == 5 and abs(sum(float(t) for t in layers) - THICKNESS) < 1e-6,
         f"the stackup adds up to the board's {THICKNESS} mm ({sum(float(t) for t in layers):.3f})")
    fact(bool(stack) and '(copper_finish "ENIG")' in stack.group(1) and "(edge_connector bevelled)" in stack.group(1),
         "stackup: ENIG finish and a bevelled edge connector (gold fingers)")
    fact(ds.m_TentViasFront and ds.m_TentViasBack, "vias are tented on both sides")
    opts = board.GetPlotOptions()
    fact(opts.GetUseGerberProtelExtensions() and opts.GetUseAuxOrigin(),
         "plot settings: Protel file names, Gerbers from the drill/place origin (the frame of the drill and position files)")
    return out


def schematic_path(sch_dir):
    """The path KiCad gives J1's footprint: the jamma sheet's identifier, then the J1 symbol's, read from the schematics."""
    root = sx_parse(open(os.path.join(sch_dir, "fcjamma.kicad_sch"), encoding="utf-8").read())
    sheet = None
    for s in sx_find(root, "sheet"):
        props = {str(p[1]): str(p[2]) for p in sx_find(s, "property")}
        if props.get("Sheetfile") == "jamma.kicad_sch":
            sheet = str(sx_first(s, "uuid")[1])
    sub = sx_parse(open(os.path.join(sch_dir, "jamma.kicad_sch"), encoding="utf-8").read())
    symbol = None
    for s in sx_find(sub, "symbol"):
        props = {str(p[1]): str(p[2]) for p in sx_find(s, "property")}
        if props.get("Reference") == "J1":
            symbol = str(sx_first(s, "uuid")[1])
    return f"/{sheet}/{symbol}" if sheet and symbol else "(not found in the schematic)"


def main():
    project, spec_path = sys.argv[1], sys.argv[2]
    spec = json.load(open(spec_path, encoding="utf-8"))
    path = write(project, spec)
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
