#!/usr/bin/python3
"""Read the board's own footprints back with KiCad's Python module and compare them with what was meant.

    /usr/bin/python3 tools/check_footprints.py kicad/fcjamma.pretty out/footprints/expected.json

tools/build.py runs this after it has written the library.  It needs KiCad's pcbnew module, which comes with
the system Python of the KiCad package (not with the project's virtual environment).  expected.json holds,
for every footprint, the pads, attributes and keep-out areas that design/footprints.py meant to draw; this
script checks that KiCad reads the same thing from the files (units, the direction of Y, layers, drills).
Exit status 1 and one line per difference when anything disagrees.
"""
import json
import sys

import pcbnew

TOL = 0.001          # mm

ATTR = {pcbnew.PAD_ATTRIB_PTH: "thru_hole", pcbnew.PAD_ATTRIB_NPTH: "np_thru_hole",
        pcbnew.PAD_ATTRIB_SMD: "smd", pcbnew.PAD_ATTRIB_CONN: "connect"}

# the names in the files and the names pcbnew.LayerName() returns
DISPLAY_NAME = {"F.SilkS": "F.Silkscreen", "B.SilkS": "B.Silkscreen", "F.CrtYd": "F.Courtyard", "B.CrtYd": "B.Courtyard",
                "Cmts.User": "User.Comments", "Dwgs.User": "User.Drawings", "Eco1.User": "User.Eco1", "Eco2.User": "User.Eco2",
                "F.Adhes": "F.Adhesive", "B.Adhes": "B.Adhesive"}


def mm(v):
    return pcbnew.ToMM(v)


def layer_names(pad):
    """The pad's layers, without the inner copper layers ('*.Cu' includes them; the board has two layers)."""
    names = [pcbnew.LayerName(layer_id) for layer_id in pad.GetLayerSet().Seq()]
    return [n for n in names if not n.startswith("In")]


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
        got = {}
        for p in fp.Pads():
            key = p.GetNumber() or f"(no number) {mm(p.GetPosition().x):.3f},{mm(p.GetPosition().y):.3f}"
            got.setdefault(key, []).append(p)
        want_pads = want["pads"]
        for key, wl in want_pads.items():
            gl = got.get(key, [])
            if len(gl) != len(wl):
                problems.append(f"{name}: pad '{key}' appears {len(gl)} times, expected {len(wl)}")
                continue
            for w in wl:
                # match by position among pads of the same number
                match = None
                for g in gl:
                    if abs(mm(g.GetPosition().x) - w["x"]) < TOL and abs(mm(g.GetPosition().y) - w["y"]) < TOL:
                        match = g
                        break
                if match is None:
                    problems.append(f"{name}: no pad '{key}' at ({w['x']}, {w['y']})")
                    continue
                if ATTR.get(match.GetAttribute()) != w["kind"]:
                    problems.append(f"{name}: pad '{key}' is {ATTR.get(match.GetAttribute())}, expected {w['kind']}")
                sx, sy = mm(match.GetSize().x), mm(match.GetSize().y)
                if abs(sx - w["w"]) > TOL or abs(sy - w["h"]) > TOL:
                    problems.append(f"{name}: pad '{key}' is {sx:.3f} x {sy:.3f}, expected {w['w']} x {w['h']}")
                dr = mm(match.GetDrillSize().x)
                if abs(dr - w.get("drill", 0.0)) > TOL:
                    problems.append(f"{name}: pad '{key}' drill {dr:.3f}, expected {w.get('drill', 0.0)}")
                gl_names = sorted(layer_names(match))
                if gl_names != wanted_layers(w["layers"]):
                    problems.append(f"{name}: pad '{key}' on {gl_names}, expected {wanted_layers(w['layers'])}")
        extra = sorted(set(got) - set(want_pads))
        if extra:
            problems.append(f"{name}: pads not meant to be there: {extra}")
        zones = [z for z in fp.Zones() if z.GetIsRuleArea()]
        if len(zones) != want.get("keepouts", 0):
            problems.append(f"{name}: {len(zones)} keep-out areas, expected {want.get('keepouts', 0)}")
        for z, wz, wr in zip(zones, want.get("keepout_boxes", []), want.get("keepout_rules", [])):
            bb = z.GetBoundingBox()
            box = [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())]
            if any(abs(a - b) > 0.05 for a, b in zip(box, wz)):
                problems.append(f"{name}: keep-out '{z.GetZoneName()}' spans {[round(v, 3) for v in box]}, expected about {wz}")
            got_rules = {"tracks": z.GetDoNotAllowTracks(), "vias": z.GetDoNotAllowVias(), "pads": z.GetDoNotAllowPads(),
                         "copperpour": z.GetDoNotAllowZoneFills(), "footprints": z.GetDoNotAllowFootprints()}
            for key, forbidden in got_rules.items():
                if (wr.get(key) == "not_allowed") != forbidden:
                    problems.append(f"{name}: keep-out '{z.GetZoneName()}' {'forbids' if forbidden else 'allows'} {key}")
        attrs = fp.GetAttributes()
        for flag, wanted in (("exclude_from_pos_files", pcbnew.FP_EXCLUDE_FROM_POS_FILES),
                             ("exclude_from_bom", pcbnew.FP_EXCLUDE_FROM_BOM)):
            if (flag in want.get("attr", [])) != bool(attrs & wanted):
                problems.append(f"{name}: attribute {flag} is {'set' if attrs & wanted else 'not set'}")
        if ("allow_soldermask_bridges" in want.get("attr", [])) != fp.AllowSolderMaskBridges():
            problems.append(f"{name}: allow_soldermask_bridges is {fp.AllowSolderMaskBridges()}")
        layers = {}
        for g in fp.GraphicalItems():
            layers[pcbnew.LayerName(g.GetLayer())] = layers.get(pcbnew.LayerName(g.GetLayer()), 0) + 1
        for layer, count in want.get("graphics", {}).items():
            shown = DISPLAY_NAME.get(layer, layer)
            if layers.get(shown, 0) != count:
                problems.append(f"{name}: {layers.get(shown, 0)} drawings on {layer}, expected {count}")
    for p in problems:
        print(p)
    print(f"checked {len(expected)} footprints with KiCad {pcbnew.Version()}: {len(problems)} differences")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
