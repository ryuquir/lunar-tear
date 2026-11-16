#!/usr/bin/python3
"""Prove that the board rules (kicad/fcjamma.kicad_dru) report what they forbid, and nothing the board needs.

    /usr/bin/python3 tools/check_rules.py <kicad project folder> <work folder> <KiCad netlist>

On a board whose project finds the footprint library, KiCad 10.0.8's DRC does not report vias inside a footprint's
keep-out area (only tracks and pour), so the board relies on named-area rules.  This script copies the project's
library table, footprint library, rules and project file into the work folder and builds two test boards there:
- every footprint the board uses, once each and apart, with the nets of its first part in the netlist (the circuit's
  footprints, KiCad's and this project's, and the bare board's mounting hole, fiducial, tooling hole and mouse bites):
  the DRC with the board rules must find nothing;
- two Pico 2 copies, the JAMMA edge, the cartridge slot and a line of mouse bites with probes in forbidden places:
  every probe must be reported by the rule meant for it (or by KiCad's own check, where the project relies on it: J1's
  courtyard beside the tongue's root, a part without a courtyard).  A rule with a value (0.45, 0.25, 0.20, 0.15) has a
  probe just inside its limit, which it must report, and one just outside, which no rule may report; so a weakened value
  fails here too.  A via in a free place may be reported by none of them.  Every rule in the rules file has a probe.
tools/build.py runs it on every build.  Exit status 1 and one line per failure.
"""
import collections
import json
import os
import re
import shutil
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "design"), HERE]
import board as BRD            # noqa: E402  (design/board.py: the bare board's footprints)
import footprints as FPL       # noqa: E402  (design/footprints.py: names and the mouse bites' geometry)
from fcgen.sexpr import parse as sx_parse, find as sx_find, first as sx_first   # noqa: E402

MM = pcbnew.FromMM
KICAD_FP = "/usr/share/kicad/footprints"
U25, U26, J1 = (60.0, 60.0), (120.0, 60.0), (40.0, 150.0)      # board positions of the three footprints (mm)
TP7 = (1.0, -5.0)
RULES = {"tp7": "TP7 keep-out: no via, pad or track", "mask": "TP7 keep-out: solder mask stays closed",
         "jvia": "JAMMA fingers: no vias near the fingers", "jtrack": "JAMMA fingers: no tracks in the tip and contact bands",
         "tent": "Vias under a Pico are tented", "silk": "JLCPCB: silkscreen 0.15 from copper pads",
         "tab": "Breakaway tabs: no parts, pads, vias or tracks within 5 mm", "holes": "JLCPCB: pad holes 0.45 apart",
         "ring": "JLCPCB: annular ring of through-hole pads 0.25", "ringm": "JLCPCB: annular ring of mechanical pads 0.20",
         "smd": "JLCPCB: SMD pads of different nets 0.15 apart"}
BUILT_IN = {"courtyard": "courtyards_overlap", "nocrt": "missing_courtyard", "clearance": "clearance"}   # KiCad's own checks
J8 = (150.0, 120.0)
MB = (190.0, 40.0)                                             # a line of mouse bites, its keep-out to +X
R0402 = (f"{KICAD_FP}/Resistor_SMD.pretty", "R_0402_1005Metric")             # a small part as a probe
THT = (f"{KICAD_FP}/TestPoint.pretty", "TestPoint_THTPad_D1.0mm_Drill0.5mm")  # one 0.5 mm plated hole in a 1.0 land
SMD = (f"{KICAD_FP}/TestPoint.pretty", "TestPoint_Pad_1.0x1.0mm")            # one 1.0 x 1.0 SMD pad


def place(board, lib, name, ref, at, lib_name="fcjamma"):
    fp = pcbnew.FootprintLoad(lib, name)
    if fp is None:
        raise RuntimeError(f"{lib_name}:{name} not found in {lib}")
    fp.SetFPID(pcbnew.LIB_ID(lib_name, name))
    fp.SetReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I(MM(at[0]), MM(at[1])))
    board.Add(fp)
    return fp


def via(board, at, tented=True):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(at[0]), MM(at[1])))
    v.SetWidth(MM(0.6))
    v.SetDrill(MM(0.3))
    mode = pcbnew.TENTING_MODE_TENTED if tented else pcbnew.TENTING_MODE_NOT_TENTED
    v.SetFrontTentingMode(mode)
    v.SetBackTentingMode(mode)
    board.Add(v)


def track(board, a, b, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(0.2))
    t.SetLayer(layer)
    board.Add(t)


def silk_line(board, centre, half=1.0, width=0.15):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(centre[0] - half), MM(centre[1])))
    s.SetEnd(pcbnew.VECTOR2I(MM(centre[0] + half), MM(centre[1])))
    s.SetLayer(pcbnew.F_SilkS)
    s.SetWidth(MM(width))
    board.Add(s)


def rect(board, a, b, layer):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECTANGLE)
    s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    s.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    s.SetLayer(layer)
    s.SetFilled(True)
    s.SetWidth(0)
    board.Add(s)


def outline(board, w, h):
    for a, b in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.05))
        board.Add(s)


def net(board, name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
    return n


def drc(work, path):
    report = path[:-10] + ".json"
    r = subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", report, path],
                       capture_output=True, text=True, cwd=work)
    if r.returncode or not os.path.exists(report):
        print("kicad-cli pcb drc failed: " + (r.stdout + r.stderr)[-300:])
        sys.exit(1)
    return json.load(open(report, encoding="utf-8")).get("violations", [])


def board_footprints(netlist):
    """{footprint: (reference, {pin: net})} for every footprint the board uses: the circuit's (the first part of each, in
    reference order) and the bare board's own."""
    tree = sx_parse(open(netlist, encoding="utf-8").read())
    nets = collections.defaultdict(dict)
    for n in sx_find(sx_first(tree, "nets"), "net"):
        name = str(sx_first(n, "name")[1])
        for node in sx_find(n, "node"):
            nets[str(sx_first(node, "ref")[1])][str(sx_first(node, "pin")[1])] = name
    order = lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0))
    comps = sorted(((str(sx_first(c, "ref")[1]), str(sx_first(c, "footprint")[1])) for c in sx_find(sx_first(tree, "components"), "comp")),
                   key=lambda rc: order(rc[0]))
    out = {}
    for ref, fpid in comps:
        out.setdefault(fpid, (ref, nets.get(ref, {})))
    for fpid, ref in ((BRD.HOLE_FOOTPRINT, "H1"), (BRD.FIDUCIAL_FOOTPRINT, "FID1"), (BRD.TOOLING_FOOTPRINT, "TH1"),
                      (BRD.BREAK_FOOTPRINT, "MB1")):
        out.setdefault(fpid, (ref, {}))
    return out


def clean_board(work, lib, netlist):
    """Every footprint the board uses on a board of its own, apart, with its nets: the board rules must find nothing."""
    board = pcbnew.BOARD()
    kinds = board_footprints(netlist)
    x, y, row, width = 10.0, 10.0, 0.0, 300.0
    for fpid, (ref, pins) in sorted(kinds.items()):
        lib_name, name = fpid.split(":")
        path = lib if lib_name == "fcjamma" else os.path.join(KICAD_FP, f"{lib_name}.pretty")
        fp = place(board, path, name, ref, (0.0, 0.0), lib_name=lib_name)
        box = fp.GetBoundingBox(False)
        for z in fp.Zones():                       # keep-outs reach beyond the drawing
            box.Merge(z.GetBoundingBox())
        w, h = pcbnew.ToMM(box.GetWidth()), pcbnew.ToMM(box.GetHeight())
        if x + w > width - 10.0:
            x, y, row = 10.0, y + row + 8.0, 0.0
        fp.SetPosition(pcbnew.VECTOR2I(MM(x - pcbnew.ToMM(box.GetLeft())), MM(y - pcbnew.ToMM(box.GetTop()))))
        for pad in fp.Pads():
            if pins.get(pad.GetNumber()):
                pad.SetNet(net(board, pins[pad.GetNumber()]))
        x, row = x + w + 8.0, max(row, h)
    outline(board, width, y + row + 10.0)
    path = os.path.join(work, "clean.kicad_pcb")
    board.Save(path)
    for ext in ("kicad_dru", "kicad_pro"):            # the board rules and the project's severities
        shutil.copy(os.path.join(work, f"fcjamma.{ext}"), os.path.join(work, f"clean.{ext}"))
    found = [f"the footprints alone break a rule: {v.get('type')}: {v.get('description', '')[:120]} "
             f"({'; '.join(i.get('description', '')[:60] for i in v.get('items', []))})" for v in drc(work, path)]
    return found, len(kinds)


def main():
    project, work, netlist = sys.argv[1], sys.argv[2], sys.argv[3]
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    for f in ("fp-lib-table", "fcjamma.kicad_dru", "fcjamma.kicad_pro"):
        shutil.copy(os.path.join(project, f), work)
    shutil.copytree(os.path.join(project, "fcjamma.pretty"), os.path.join(work, "fcjamma.pretty"))
    lib = os.path.join(work, "fcjamma.pretty")

    problems, n_kinds = clean_board(work, lib, netlist)

    board = pcbnew.BOARD()
    place(board, lib, FPL.PICO, "U25", U25)
    place(board, lib, FPL.PICO, "U26", U26)
    place(board, lib, FPL.JAMMA, "J1", J1)
    place(board, lib, FPL.CART, "J8", J8)
    place(board, lib, FPL.BREAK, "MB1", MB)
    outline(board, 220, J1[1])

    t7a = (U25[0] + TP7[0], U25[1] + TP7[1])
    t7b = (U26[0] + TP7[0], U26[1] + TP7[1])
    gap1 = J1[0] + 3.96 * 9.5                    # between fingers 10 and 11
    gap2 = J1[0] + 3.96 * 19.5                   # between fingers 20 and 21
    first_bite = MB[1] - FPL.BREAK_P * (FPL.BREAK_N - 1) / 2         # the first hole of the line
    bite_end = FPL.BREAK_P * (FPL.BREAK_N - 1) / 2 + FPL.BREAK_D / 2  # its far edge, from the line's centre
    pad1 = (J8[0] - 36.83, J8[1] + 2.54)                             # cartridge pins 1 and 20 (land 1.7)
    pad20 = (J8[0] - 36.83 + 19 * 2.54, J8[1] + 2.54)
    silk_at = lambda pad, gap: (pad[0], pad[1] + 0.85 + 0.075 + gap)  # a 0.15 line 'gap' from the land's edge
    probes = {                                    # name: (where to look, rule that must report it, kind of item)
        "via in TP7": (t7a, "tp7", "Via"),
        "track across TP7": (t7b, "tp7", "Track"),
        "mask opening at TP7": (t7b, "mask", "Rectangle"),
        "via in the JAMMA bevel band": ((gap1, J1[1] - 0.6), "jvia", "Via"),
        "via in the JAMMA contact band": ((gap1, J1[1] - 5.0), "jvia", "Via"),
        "via at the JAMMA finger roots": ((gap1, J1[1] - 10.5), "jvia", "Via"),
        "track in the JAMMA contact band": ((gap2, J1[1] - 5.5), "jtrack", "Track"),
        "untented via under a Pico": ((U26[0] - 3.0, U26[1] + 10.0), "tent", "Via"),
        "silkscreen line 0.14 from a cartridge pad": (silk_at(pad1, 0.14), "silk", "Segment"),
        # beside the tongue's root (12-15 mm above the tip), within 5 mm of finger 1: only J1's widened courtyard covers it
        "small part beside the root of finger 1": ((J1[0] - 5.2, J1[1] - 13.5), "courtyard", "Footprint"),
        "via 2 mm from a line of mouse bites": ((MB[0] + 2.0, MB[1] + 2.0), "tab", "Via"),
        "small part 2.5 mm from a line of mouse bites": ((MB[0] + 2.5, MB[1] - 3.0), "tab", "Footprint"),
        "via 4 mm past the end of a line of mouse bites": ((MB[0] + 0.6, MB[1] + bite_end + 4.0), "tab", "Via"),
        "track 3 mm from a line of mouse bites": ((MB[0] + 3.0, MB[1]), "tab", "Track"),
        "pad 3.5 mm from a line of mouse bites, its part's courtyard outside": ((MB[0] + 3.5, MB[1] - 6.5), "tab", "Pad"),
        "two pad holes 0.44 apart": ((170.0, 20.0), "holes", ""),
        "a pad hole 0.30 from a mouse-bite hole": ((MB[0] - 0.85, first_bite), "holes", ""),
        "a through-hole pad with a 0.24 ring": ((150.0, 20.0), "ring", ""),
        "a mechanical slot with a 0.19 ring": ((150.0, 30.0), "ringm", ""),
        "two SMD pads of different nets 0.14 apart": ((90.0, 20.0), "smd", ""),
        "a part without a courtyard": ((130.0, 20.0), "nocrt", "Footprint"),
    }
    clear = {                                     # name: (where to look, rules that must not report it)
        "two pad holes 0.46 apart": ((170.0, 30.0), ["holes"]),
        "a through-hole pad with a 0.26 ring": ((160.0, 20.0), ["ring", "ringm"]),
        "a mechanical slot with a 0.21 ring": ((160.0, 30.0), ["ring", "ringm"]),
        "two SMD pads of different nets 0.16 apart": ((90.0, 30.0), ["smd", "clearance"]),
        "silkscreen line 0.16 from a cartridge pad": (silk_at(pad20, 0.16), ["silk"]),
    }
    via(board, t7a)
    track(board, (t7b[0] - 2.0, t7b[1] + 0.3), (t7b[0] + 2.0, t7b[1] + 0.3))
    rect(board, (t7b[0] - 0.3, t7b[1] - 0.3), (t7b[0] + 0.3, t7b[1] + 0.3), pcbnew.F_Mask)
    for name in ("via in the JAMMA bevel band", "via in the JAMMA contact band", "via at the JAMMA finger roots"):
        via(board, probes[name][0])
    track(board, (gap2, J1[1] - 4.0), (gap2, J1[1] - 7.0))
    via(board, probes["untented via under a Pico"][0], tented=False)
    silk_line(board, probes["silkscreen line 0.14 from a cartridge pad"][0])
    silk_line(board, clear["silkscreen line 0.16 from a cartridge pad"][0])
    place(board, *R0402, "R1", probes["small part beside the root of finger 1"][0], lib_name="Resistor_SMD")
    via(board, probes["via 2 mm from a line of mouse bites"][0])
    place(board, *R0402, "R2", probes["small part 2.5 mm from a line of mouse bites"][0], lib_name="Resistor_SMD")
    via(board, probes["via 4 mm past the end of a line of mouse bites"][0])
    track(board, (MB[0] + 3.0, MB[1] - 1.0), (MB[0] + 3.0, MB[1] + 1.0))
    px, py = probes["pad 3.5 mm from a line of mouse bites, its part's courtyard outside"][0]
    lone = place(board, *SMD, "SP1", (MB[0] + 9.0, py), lib_name="TestPoint")      # courtyard beyond the keep-out (5.3)
    for pad in lone.Pads():
        pad.SetPosition(pcbnew.VECTOR2I(MM(px), MM(py)))                              # only its pad inside it
    for (hx, hy), gap, refs in (((170.0, 20.0), 0.44, ("TP1", "TP2")), ((170.0, 30.0), 0.46, ("TP5", "TP6"))):
        place(board, *THT, refs[0], (hx, hy), lib_name="TestPoint")
        place(board, *THT, refs[1], (hx + 0.5 + gap, hy), lib_name="TestPoint")       # 0.5 holes: 'gap' between them
    place(board, *THT, "TP3", probes["a pad hole 0.30 from a mouse-bite hole"][0], lib_name="TestPoint")
    for at, land, ref in (((150.0, 20.0), 0.98, "TP4"), ((160.0, 20.0), 1.02, "TP10")):
        f = place(board, *THT, ref, at, lib_name="TestPoint")
        for pad in f.Pads():
            pad.SetSize(pcbnew.VECTOR2I(MM(land), MM(land)))                          # on a 0.5 hole: rings 0.24, 0.26
    for at, land, ref in (((150.0, 30.0), 0.98, "TP11"), ((160.0, 30.0), 1.02, "TP12")):
        f = place(board, *THT, ref, at, lib_name="TestPoint")
        for pad in f.Pads():                      # a mechanical slot like the USB-C shell's: 0.6 x 1.7, rings 0.19, 0.21
            pad.SetShape(pcbnew.PAD_SHAPE_OVAL)
            pad.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_OBLONG)
            pad.SetDrillSize(pcbnew.VECTOR2I(MM(0.6), MM(1.7)))
            pad.SetSize(pcbnew.VECTOR2I(MM(land), MM(land + 1.1)))
            pad.SetProperty(pcbnew.PAD_PROP_MECHANICAL)
    for (sx, sy), gap, refs, nets in (((90.0, 20.0), 0.14, ("SP2", "SP3"), ("N1", "N2")), ((90.0, 30.0), 0.16, ("SP4", "SP5"), ("N3", "N4"))):
        for ref, x, n in ((refs[0], sx - (0.5 + gap / 2), nets[0]), (refs[1], sx + (0.5 + gap / 2), nets[1])):
            f = place(board, *SMD, ref, (x, sy), lib_name="TestPoint")
            for pad in f.Pads():
                pad.SetNet(net(board, n))         # 1.0 pads of different nets, 'gap' apart
    bare = place(board, *R0402, "R3", probes["a part without a courtyard"][0], lib_name="Resistor_SMD")
    for g in [g for g in bare.GraphicalItems() if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd)]:
        bare.Remove(g)
    free = (200.0, 20.0)
    via(board, free, tented=False)                # a free place: no rule may report it

    path = os.path.join(work, "fcjamma.kicad_pcb")
    board.Save(path)
    violations = drc(work, path)

    def reported(rule_key, at, kind, radius=2.6):
        for v in violations:
            if rule_key in BUILT_IN:
                if v.get("type") != BUILT_IN[rule_key]:
                    continue
            elif RULES[rule_key] not in v.get("description", ""):
                continue
            for item in v.get("items", []):
                pos = item.get("pos", {})
                if (item.get("description", "").startswith(kind) and abs(pos.get("x", 1e9) - at[0]) < radius
                        and abs(pos.get("y", 1e9) - at[1]) < radius):
                    return True
        return False

    for name, (at, rule_key, kind) in probes.items():
        if not reported(rule_key, at, kind):
            problems.append(f"the rule '{RULES.get(rule_key, BUILT_IN.get(rule_key))}' does not report the probe '{name}'")
    for name, (at, keys) in clear.items():
        for key in keys:
            if reported(key, at, "", radius=1.5):
                problems.append(f"the rule '{RULES.get(key, BUILT_IN.get(key))}' reports '{name}', which its limit allows")
    for key in RULES:
        if reported(key, free, "Via", radius=1.0):
            problems.append(f"the rule '{RULES[key]}' reports a via in a free place")
    unproved = sorted(set(RULES) - {k for _, k, _ in probes.values()})
    problems += [f"the rule '{RULES[k]}' has no probe" for k in unproved]
    for p in problems:
        print(p)
    missed = len([p for p in problems if "does not report" in p])
    wrong = len([p for p in problems if "its limit allows" in p])
    print(f"board rules: {len(probes) - missed}/{len(probes)} probes reported by their rule, {len(clear) - wrong}/{len(clear)} "
          f"on the allowed side of a limit left alone, {len([p for p in problems if 'footprints alone' in p])} findings on the "
          f"{n_kinds} footprints the board uses")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
