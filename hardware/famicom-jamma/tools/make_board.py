#!/usr/bin/python3
"""Build kicad/fcjamma.kicad_pcb from design/board.py, then read it back and check it.

    /usr/bin/python3 tools/make_board.py <kicad project folder> <board.json>

tools/build.py writes board.json from design/board.py and the circuit (the nets of J1) and runs this script with the
system Python, which has KiCad's pcbnew module.  The board holds, so far: the outline (body, JAMMA tongue and key
slot), the JAMMA edge J1 placed on the tongue, the mounting holes, the fiducials, the stackup (ENIG, bevelled edge
connector), via tenting, the title block and the drill/place origin.  The other parts come in stage 2-2.
Every item gets an identifier derived from its name, so that a rebuild writes the same file.
Exit status 1 and one line per failed check.
"""
import json
import math
import os
import re
import sys
import uuid

import pcbnew

MM = pcbnew.FromMM
NS = uuid.UUID("0f6d1f2a-7c55-4d8e-9f39-5b7b2c9e4a61")


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


def place(board, lib_dir, lib_name, fp_name, ref, value, at, attrs=0, path=None, nets=None, show_ref=True):
    fp = pcbnew.FootprintLoad(lib_dir, fp_name)
    if fp is None:
        raise RuntimeError(f"{lib_name}:{fp_name} not found in {lib_dir}")
    fp.SetFPID(pcbnew.LIB_ID(lib_name, fp_name))
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(v(at))
    if attrs:
        fp.SetAttributes(fp.GetAttributes() | attrs)
    if path:
        fp.SetPath(pcbnew.KIID_PATH(path))
    if not show_ref:                       # holes and fiducials need no label on the silkscreen
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
    tb = pcbnew.TITLE_BLOCK()
    tb.SetTitle(spec["title"])
    tb.SetRevision(spec["revision"])
    board.SetTitleBlock(tb)
    # the sheet stays KiCad's default A4 (landscape, 297 x 210): the board fits on it at ORIGIN

    add_outline(board, spec["outline"])
    for i, name in enumerate(sorted(set(spec["j1"]["nets"].values()))):
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    j1 = spec["j1"]
    place(board, os.path.join(project, "fcjamma.pretty"), "fcjamma", j1["footprint"], "J1", j1["value"], j1["at"],
          path=j1["path"], nets=j1["nets"])
    lib, name = spec["hole_footprint"].split(":")
    for i, at in enumerate(spec["holes"], 1):
        place(board, os.path.join(spec["kicad_fp"], f"{lib}.pretty"), lib, name, f"H{i}", "M3", at, pcbnew.FP_BOARD_ONLY,
              show_ref=False)
    lib, name = spec["fiducial_footprint"].split(":")
    for i, at in enumerate(spec["fiducials"], 1):
        place(board, os.path.join(spec["kicad_fp"], f"{lib}.pretty"), lib, name, f"FID{i}", "Fiducial", at,
              pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM, show_ref=False)
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


def facts(path, spec):
    """Read the board back and check what the design asks for."""
    board = pcbnew.LoadBoard(path)
    text = open(path, encoding="utf-8").read()
    out = []

    def fact(ok, what):
        out.append((bool(ok), what))

    poly = pcbnew.SHAPE_POLY_SET()
    ok = board.GetBoardPolygonOutlines(poly, False)       # False: do not infer an outline
    fact(ok and poly.OutlineCount() == 1 and poly.HoleCount(0) == 0, "the outline is one closed contour without holes")
    bb = poly.BBox() if ok else None
    ox, oy = spec["origin"]
    w, top = spec["body_w"], spec["top"]
    fact(bb and abs(pcbnew.ToMM(bb.GetLeft()) - ox) < 1e-3 and abs(pcbnew.ToMM(bb.GetRight()) - (ox + w)) < 1e-3
         and abs(pcbnew.ToMM(bb.GetTop()) - oy) < 1e-3 and abs(pcbnew.ToMM(bb.GetBottom()) - (oy + top)) < 1e-3,
         f"the board is {w} x {top} mm (body {w} x {spec['body_h']}, tongue {spec['tongue_l']})")

    def inside(p):
        return ok and poly.Contains(v(p))

    k = spec["kicad"]
    fact(inside(k["tongue_centre"]), "the tongue is board")
    fact(not inside(k["beside_tongue_left"]) and not inside(k["beside_tongue_right"]),
         "beside the tongue (where the connector's ears go) there is no board")
    fact(not inside(k["in_key_slot"]), "the key slot is cut out")
    fact(inside(k["above_key_slot"]), "there is board just above the bottom of the key slot")
    fact(inside(k["body_centre"]), "the body is board")

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    j1 = fps.get("J1")
    fact(j1 is not None and j1.GetFPID().GetUniStringLibId() == "fcjamma:" + spec["j1"]["footprint"], "J1 is the JAMMA edge")
    if j1 is not None:
        at = spec["j1"]["at"]
        fact(abs(pcbnew.ToMM(j1.GetPosition().x) - at[0]) < 1e-4 and abs(pcbnew.ToMM(j1.GetPosition().y) - at[1]) < 1e-4
             and abs(j1.GetOrientation().AsDegrees()) < 1e-6 and j1.GetLayer() == pcbnew.F_Cu and j1.IsLocked(),
             "J1 sits on the tip line at finger 1, not turned, on the parts side, locked")
        pads = list(j1.Pads())
        fact(len(pads) == 54 and all(inside((pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))) for p in pads),
             "all 54 fingers lie on the tongue")
        tip = oy + top
        fact(all(abs((tip - pcbnew.ToMM(p.GetPosition().y)) - 5.6) < 1e-4 for p in pads),
             "every finger runs from 1.2 to 10.0 mm above the board edge")
        nets = {p.GetNumber(): p.GetNetname() for p in pads}
        fact(all(nets.get(pad) == net for pad, net in spec["j1"]["nets"].items()), "J1's fingers carry the circuit's nets")
        fact(str(j1.GetPath().AsString()) == spec["j1"]["path"], "J1 is linked to its schematic symbol")

    holes = [fps.get(f"H{i}") for i in range(1, len(spec["holes"]) + 1)]
    fact(all(h is not None for h in holes), f"{len(spec['holes'])} mounting holes")
    for h, at in zip(holes, spec["holes"]):
        if h is None:
            continue
        pads = list(h.Pads())
        hx, hy = pcbnew.ToMM(h.GetPosition().x), pcbnew.ToMM(h.GetPosition().y)
        fact(len(pads) == 1 and pads[0].GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and abs(pcbnew.ToMM(pads[0].GetDrillSize().x) - 3.2) < 1e-6
             and abs(hx - at[0]) < 1e-4 and abs(hy - at[1]) < 1e-4, f"{h.GetReference()}: M3 hole of 3.2 mm, not plated, where planned")
        # distance from the hole's centre to the board edge
        d = math.inf
        if ok:
            outline = poly.COutline(0)
            for i in range(outline.SegmentCount()):
                seg = outline.CSegment(i)
                d = min(d, pcbnew.ToMM(seg.Distance(v((hx, hy)))))
        fact(d >= 4.0 - 1e-6, f"{h.GetReference()}: at least 4 mm from the board edge ({d:.2f})")
        fact((oy + top) - hy >= 12.0 + 3.2, f"{h.GetReference()}: clear of the 12 mm next to the tip")
    fids = [fps.get(f"FID{i}") for i in range(1, len(spec["fiducials"]) + 1)]
    fact(len([f for f in fids if f is not None]) == 3, "three fiducials")
    if all(f is not None for f in fids) and len(fids) == 3:
        (ax, ay), (bx, by), (cx, cy) = [(pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)) for f in fids]
        fact(abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) > 100.0, "the fiducials are not on one line")

    ds = board.GetDesignSettings()
    fact(board.GetCopperLayerCount() == 2, "two copper layers")
    fact(abs(pcbnew.ToMM(ds.GetBoardThickness()) - spec["thickness"]) < 1e-6, f"board {spec['thickness']} mm thick")
    fact('(copper_finish "ENIG")' in text and "(edge_connector bevelled)" in text,
         "stackup: ENIG finish and a bevelled edge connector (gold fingers)")
    fact(ds.m_TentViasFront and ds.m_TentViasBack, "vias are tented on both sides")
    ao = ds.GetAuxOrigin()
    fact(abs(pcbnew.ToMM(ao.x) - spec["aux_origin"][0]) < 1e-6 and abs(pcbnew.ToMM(ao.y) - spec["aux_origin"][1]) < 1e-6,
         "the drill/place origin is the lower-left corner of the bounding box")
    return out


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
    main()
