#!/usr/bin/python3
"""Read the board's own footprints back with KiCad's Python module and compare them with what the generator wrote.

    /usr/bin/python3 tools/check_footprints.py kicad/fcjamma.pretty out/footprints/expected.json

tools/build.py runs this after it has written the library.  It needs KiCad's pcbnew module, which comes with
the system Python of the KiCad package (not with the project's virtual environment).

expected.json holds, for every footprint, the pads, keep-out areas, drawings and attributes as the generator
(design/footprints.py) wrote them.  This script checks that KiCad reads the same thing from the files: units, the
direction of Y, layers, drills, pad shapes and angles, the layers and rules of the keep-outs, and the position of
every line, rectangle, circle, arc, polygon and text.  It cannot tell whether the generator drew the right thing;
that is what the facts in design/footprints.py are for.
Exit status 1 and one line per difference when anything disagrees.
"""
import json
import math
import sys

import pcbnew

TOL = 0.001          # mm

ATTR = {pcbnew.PAD_ATTRIB_PTH: "thru_hole", pcbnew.PAD_ATTRIB_NPTH: "np_thru_hole",
        pcbnew.PAD_ATTRIB_SMD: "smd", pcbnew.PAD_ATTRIB_CONN: "connect"}
PAD_SHAPE = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECTANGLE: "rect", pcbnew.PAD_SHAPE_OVAL: "oval",
             pcbnew.PAD_SHAPE_TRAPEZOID: "trapezoid", pcbnew.PAD_SHAPE_ROUNDRECT: "roundrect",
             pcbnew.PAD_SHAPE_CHAMFERED_RECT: "chamfered_rect", pcbnew.PAD_SHAPE_CUSTOM: "custom"}
SHAPE = {pcbnew.SHAPE_T_SEGMENT: "fp_line", pcbnew.SHAPE_T_RECTANGLE: "fp_rect", pcbnew.SHAPE_T_CIRCLE: "fp_circle",
         pcbnew.SHAPE_T_ARC: "fp_arc", pcbnew.SHAPE_T_POLY: "fp_poly"}

# the names in the files and the names pcbnew.LayerName() returns
DISPLAY_NAME = {"F.SilkS": "F.Silkscreen", "B.SilkS": "B.Silkscreen", "F.CrtYd": "F.Courtyard", "B.CrtYd": "B.Courtyard",
                "Cmts.User": "User.Comments", "Dwgs.User": "User.Drawings", "Eco1.User": "User.Eco1", "Eco2.User": "User.Eco2",
                "F.Adhes": "F.Adhesive", "B.Adhes": "B.Adhesive"}
FILE_NAME = {v: k for k, v in DISPLAY_NAME.items()}


def mm(v):
    return pcbnew.ToMM(v)


def xy(p):
    return [mm(p.x), mm(p.y)]


def names_of(layer_set):
    """Layer names as the files spell them, without the inner copper layers ('*.Cu' includes them; the board has two)."""
    names = [pcbnew.LayerName(layer_id) for layer_id in layer_set.Seq()]
    return sorted(FILE_NAME.get(n, n) for n in names if not n.startswith("In"))


def wanted_layers(spec):
    out = []
    for name in spec:
        if name == "*.Cu":
            out += ["F.Cu", "B.Cu"]
        elif name == "*.Mask":
            out += ["F.Mask", "B.Mask"]
        else:
            out.append(name)
    return sorted(set(out))


def same_points(a, b, ordered=True):
    if len(a) != len(b):
        return False
    if not ordered:
        a, b = sorted(a), sorted(b)
    return all(abs(p[0] - q[0]) < TOL and abs(p[1] - q[1]) < TOL for p, q in zip(a, b))


def drawing_of(g):
    """A drawing as KiCad reads it, in the form footprint_out.expected() records."""
    layer = FILE_NAME.get(pcbnew.LayerName(g.GetLayer()), pcbnew.LayerName(g.GetLayer()))
    if g.GetClass() == "PCB_TEXT":
        return {"type": "fp_text", "layer": layer, "pts": [xy(g.GetPosition())], "fill": False, "text": g.GetText()}
    kind = SHAPE.get(g.GetShape(), "other")
    if kind in ("fp_line", "fp_rect"):
        pts = [xy(g.GetStart()), xy(g.GetEnd())]
    elif kind == "fp_circle":
        pts = [xy(g.GetCenter()), xy(g.GetEnd())]
    elif kind == "fp_arc":
        pts = [xy(g.GetStart()), xy(g.GetArcMid()), xy(g.GetEnd())]
    elif kind == "fp_poly":
        outline = g.GetPolyShape().COutline(0)
        pts = [xy(outline.CPoint(i)) for i in range(outline.PointCount())]
    else:
        pts = []
    return {"type": kind, "layer": layer, "pts": pts, "fill": g.IsSolidFill(), "text": None}


def matches(w, g):
    if w["type"] != g["type"] or w["layer"] != g["layer"] or w["text"] != g["text"]:
        return False
    if w["type"] in ("fp_rect", "fp_circle", "fp_poly") and w["fill"] != g["fill"]:
        return False
    if w["type"] == "fp_rect":       # KiCad may store the two corners the other way round
        ws, gs = w["pts"], g["pts"]
        return same_points([[min(ws[0][0], ws[1][0]), min(ws[0][1], ws[1][1])], [max(ws[0][0], ws[1][0]), max(ws[0][1], ws[1][1])]],
                           [[min(gs[0][0], gs[1][0]), min(gs[0][1], gs[1][1])], [max(gs[0][0], gs[1][0]), max(gs[0][1], gs[1][1])]])
    if w["type"] == "fp_circle":     # centre and radius
        rw = math.dist(w["pts"][0], w["pts"][1])
        rg = math.dist(g["pts"][0], g["pts"][1])
        return same_points(w["pts"][:1], g["pts"][:1]) and abs(rw - rg) < TOL
    if w["type"] == "fp_arc":        # KiCad recomputes the middle point from the centre: compare the ends and the radius side
        return same_points([w["pts"][0], w["pts"][2]], [g["pts"][0], g["pts"][2]]) and math.dist(w["pts"][1], g["pts"][1]) < 0.01
    return same_points(w["pts"], g["pts"])


def check_one(name, want, fp, problems):
    got = {}
    for p in fp.Pads():
        key = p.GetNumber() or f"(no number) {mm(p.GetPosition().x):.3f},{mm(p.GetPosition().y):.3f}"
        got.setdefault(key, []).append(p)
    for key, wl in want["pads"].items():
        gl = got.get(key, [])
        if len(gl) != len(wl):
            problems.append(f"{name}: pad '{key}' appears {len(gl)} times, expected {len(wl)}")
            continue
        for w in wl:
            match = next((g for g in gl if abs(mm(g.GetPosition().x) - w["x"]) < TOL and abs(mm(g.GetPosition().y) - w["y"]) < TOL), None)
            if match is None:
                problems.append(f"{name}: no pad '{key}' at ({w['x']}, {w['y']})")
                continue
            if ATTR.get(match.GetAttribute()) != w["kind"]:
                problems.append(f"{name}: pad '{key}' is {ATTR.get(match.GetAttribute())}, expected {w['kind']}")
            shape = PAD_SHAPE.get(match.GetShape(pcbnew.F_Cu if "B.Cu" not in w["layers"] else pcbnew.B_Cu))
            if shape != w["shape"]:
                problems.append(f"{name}: pad '{key}' has shape {shape}, expected {w['shape']}")
            angle = match.GetOrientation().AsDegrees() % 360
            if abs((angle - w["rot"]) % 360) > 0.01 and abs((angle - w["rot"]) % 360 - 360) > 0.01:
                problems.append(f"{name}: pad '{key}' is turned {angle:.2f} degrees, expected {w['rot']}")
            sx, sy = mm(match.GetSize(pcbnew.F_Cu).x), mm(match.GetSize(pcbnew.F_Cu).y)
            if "B.Cu" in w["layers"] and "F.Cu" not in w["layers"]:
                sx, sy = mm(match.GetSize(pcbnew.B_Cu).x), mm(match.GetSize(pcbnew.B_Cu).y)
            if abs(sx - w["w"]) > TOL or abs(sy - w["h"]) > TOL:
                problems.append(f"{name}: pad '{key}' is {sx:.3f} x {sy:.3f}, expected {w['w']} x {w['h']}")
            dr = mm(match.GetDrillSize().x)
            if abs(dr - w.get("drill", 0.0)) > TOL:
                problems.append(f"{name}: pad '{key}' drill {dr:.3f}, expected {w.get('drill', 0.0)}")
            if names_of(match.GetLayerSet()) != wanted_layers(w["layers"]):
                problems.append(f"{name}: pad '{key}' on {names_of(match.GetLayerSet())}, expected {wanted_layers(w['layers'])}")
    extra = sorted(set(got) - set(want["pads"]))
    if extra:
        problems.append(f"{name}: pads not meant to be there: {extra}")

    zones = [z for z in fp.Zones() if z.GetIsRuleArea()]
    if len(zones) != want["keepouts"]:
        problems.append(f"{name}: {len(zones)} keep-out areas, expected {want['keepouts']}")
    by_name = {z.GetZoneName(): z for z in zones}
    for i, zname in enumerate(want["keepout_names"]):
        z = by_name.get(zname)
        if z is None:
            problems.append(f"{name}: no keep-out named '{zname}'")
            continue
        bb = z.GetBoundingBox()
        box = [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())]
        if any(abs(a - b) > 0.05 for a, b in zip(box, want["keepout_boxes"][i])):
            problems.append(f"{name}: keep-out '{zname}' spans {[round(v, 3) for v in box]}, expected about {want['keepout_boxes'][i]}")
        if names_of(z.GetLayerSet()) != want["keepout_layers"][i]:
            problems.append(f"{name}: keep-out '{zname}' is on {names_of(z.GetLayerSet())}, expected {want['keepout_layers'][i]}")
        rules = want["keepout_rules"][i]
        got_rules = {"tracks": z.GetDoNotAllowTracks(), "vias": z.GetDoNotAllowVias(), "pads": z.GetDoNotAllowPads(),
                     "copperpour": z.GetDoNotAllowZoneFills(), "footprints": z.GetDoNotAllowFootprints()}
        for key, forbidden in got_rules.items():
            if (rules.get(key) == "not_allowed") != forbidden:
                problems.append(f"{name}: keep-out '{zname}' {'forbids' if forbidden else 'allows'} {key}")

    attrs = fp.GetAttributes()
    for flag, bit in (("exclude_from_pos_files", pcbnew.FP_EXCLUDE_FROM_POS_FILES), ("exclude_from_bom", pcbnew.FP_EXCLUDE_FROM_BOM),
                      ("through_hole", pcbnew.FP_THROUGH_HOLE), ("smd", pcbnew.FP_SMD), ("board_only", pcbnew.FP_BOARD_ONLY)):
        if (flag in want["attr"]) != bool(attrs & bit):
            problems.append(f"{name}: attribute {flag} is {'set' if attrs & bit else 'not set'}")
    if ("allow_soldermask_bridges" in want["attr"]) != fp.AllowSolderMaskBridges():
        problems.append(f"{name}: allow_soldermask_bridges is {fp.AllowSolderMaskBridges()}")

    drawings = [drawing_of(g) for g in fp.GraphicalItems()]
    unmatched = list(drawings)
    for w in want["drawings"]:
        hit = next((g for g in unmatched if matches(w, g)), None)
        if hit is None:
            problems.append(f"{name}: KiCad has no {w['type']} on {w['layer']} at {[[round(c, 3) for c in p] for p in w['pts']][:3]}"
                            + (f" '{w['text']}'" if w["text"] else ""))
        else:
            unmatched.remove(hit)
    for g in unmatched:
        problems.append(f"{name}: KiCad reads an unexpected {g['type']} on {g['layer']} at {[[round(c, 3) for c in p] for p in g['pts']][:3]}")


def main():
    lib, expected_path = sys.argv[1], sys.argv[2]
    expected = json.load(open(expected_path, encoding="utf-8"))
    problems = []
    for name, want in expected.items():
        try:
            fp = pcbnew.FootprintLoad(lib, name)
        except Exception as e:          # a file KiCad cannot read
            problems.append(f"{name}: KiCad cannot load it ({e})")
            continue
        if fp is None:
            problems.append(f"{name}: not found in {lib}")
            continue
        check_one(name, want, fp, problems)
    for p in problems:
        print(p)
    print(f"checked {len(expected)} footprints with KiCad {pcbnew.Version()}: {len(problems)} differences")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
