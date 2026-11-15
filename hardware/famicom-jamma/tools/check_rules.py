#!/usr/bin/python3
"""Prove that the board rules (kicad/fcjamma.kicad_dru) report what the footprints' keep-outs forbid.

    /usr/bin/python3 tools/check_rules.py <kicad project folder> <work folder>

On a board whose project finds the footprint library, KiCad 10.0.8's DRC does not report vias inside a footprint's
keep-out area (only tracks and pour), so the board relies on named-area rules.  This script copies the project's
library table, footprint library, rules and project file into the work folder and builds two test boards there:
- the five footprints alone, apart: the DRC with the board rules must find nothing (silkscreen 0.15 from copper,
  pad holes 0.45 apart, rings 0.25, ...);
- two Pico 2 copies, the JAMMA edge and the cartridge slot with one probe in each forbidden place: every probe must be
  reported by the rule meant for it, and a via in a free place by none of them.
tools/build.py runs it on every build.  Exit status 1 and one line per failure.
"""
import json
import os
import shutil
import subprocess
import sys

import pcbnew

MM = pcbnew.FromMM
PICO = "RaspberryPi_Pico2_SMD_TP7KeepOut"
JAMMA = "JAMMA_Edge_56"
U25, U26, J1 = (60.0, 60.0), (120.0, 60.0), (40.0, 150.0)      # board positions of the three footprints (mm)
TP7 = (1.0, -5.0)
RULES = {"tp7": "TP7 keep-out: no via, pad or track", "mask": "TP7 keep-out: solder mask stays closed",
         "jvia": "JAMMA fingers: no vias near the fingers", "jtrack": "JAMMA fingers: no tracks in the tip and contact bands",
         "tent": "Vias under a Pico are tented", "silk": "JLCPCB: silkscreen 0.15 from copper pads"}
J8 = (150.0, 120.0)
CLEAN = {"JAMMA_Edge_56": ("J1", (10.0, 190.0)), "Famicom_Cart_60": ("J8", (110.0, 30.0)), "Trimmer_Bourns_3362P": ("RV1", (30.0, 80.0)),
         "SW_DIP_x04_HRO_DS-04RP_W7.62mm_P2.54mm_Drill1.0mm": ("SW3", (60.0, 75.0)), "RaspberryPi_Pico2_SMD_TP7KeepOut": ("U25", (160.0, 100.0))}


def place(board, lib, name, ref, at):
    fp = pcbnew.FootprintLoad(lib, name)
    fp.SetFPID(pcbnew.LIB_ID("fcjamma", name))
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


def drc(work, path):
    report = path[:-10] + ".json"
    r = subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", report, path],
                       capture_output=True, text=True, cwd=work)
    if r.returncode or not os.path.exists(report):
        print("kicad-cli pcb drc failed: " + (r.stdout + r.stderr)[-300:])
        sys.exit(1)
    return json.load(open(report, encoding="utf-8")).get("violations", [])


def clean_board(work, lib):
    """All five footprints on a board of their own, apart: the board rules must find nothing."""
    board = pcbnew.BOARD()
    for name, (ref, at) in CLEAN.items():
        place(board, lib, name, ref, at)
    outline(board, 230, 190)
    path = os.path.join(work, "clean.kicad_pcb")
    board.Save(path)
    shutil.copy(os.path.join(work, "fcjamma.kicad_dru"), os.path.join(work, "clean.kicad_dru"))
    return [f"the footprints alone break a rule: {v.get('type')}: {v.get('description', '')[:120]} "
            f"({'; '.join(i.get('description', '')[:60] for i in v.get('items', []))})" for v in drc(work, path)]


def main():
    project, work = sys.argv[1], sys.argv[2]
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    for f in ("fp-lib-table", "fcjamma.kicad_dru", "fcjamma.kicad_pro"):
        shutil.copy(os.path.join(project, f), work)
    shutil.copytree(os.path.join(project, "fcjamma.pretty"), os.path.join(work, "fcjamma.pretty"))
    lib = os.path.join(work, "fcjamma.pretty")

    problems = clean_board(work, lib)

    board = pcbnew.BOARD()
    place(board, lib, PICO, "U25", U25)
    place(board, lib, PICO, "U26", U26)
    place(board, lib, JAMMA, "J1", J1)
    place(board, lib, "Famicom_Cart_60", "J8", J8)
    outline(board, 220, J1[1])

    t7a = (U25[0] + TP7[0], U25[1] + TP7[1])
    t7b = (U26[0] + TP7[0], U26[1] + TP7[1])
    gap1 = J1[0] + 3.96 * 9.5                    # between fingers 10 and 11
    gap2 = J1[0] + 3.96 * 19.5                   # between fingers 20 and 21
    probes = {                                    # name: (where to look, rule that must report it, kind of item)
        "via in TP7": (t7a, "tp7", "Via"),
        "track across TP7": (t7b, "tp7", "Track"),
        "mask opening at TP7": (t7b, "mask", "Rectangle"),
        "via in the JAMMA bevel band": ((gap1, J1[1] - 0.6), "jvia", "Via"),
        "via in the JAMMA contact band": ((gap1, J1[1] - 5.0), "jvia", "Via"),
        "via at the JAMMA finger roots": ((gap1, J1[1] - 10.5), "jvia", "Via"),
        "track in the JAMMA contact band": ((gap2, J1[1] - 5.5), "jtrack", "Track"),
        "untented via under a Pico": ((U26[0] - 3.0, U26[1] + 10.0), "tent", "Via"),
        "silkscreen line 0.1 mm from a cartridge pad": ((J8[0] - 36.83, J8[1] + 2.54 + 0.95), "silk", "Segment"),
    }
    via(board, t7a)
    track(board, (t7b[0] - 2.0, t7b[1] + 0.3), (t7b[0] + 2.0, t7b[1] + 0.3))
    rect(board, (t7b[0] - 0.3, t7b[1] - 0.3), (t7b[0] + 0.3, t7b[1] + 0.3), pcbnew.F_Mask)
    for name in ("via in the JAMMA bevel band", "via in the JAMMA contact band", "via at the JAMMA finger roots"):
        via(board, probes[name][0])
    track(board, (gap2, J1[1] - 4.0), (gap2, J1[1] - 7.0))
    via(board, probes["untented via under a Pico"][0], tented=False)
    sx, sy = probes["silkscreen line 0.1 mm from a cartridge pad"][0]
    silk = pcbnew.PCB_SHAPE(board)
    silk.SetShape(pcbnew.SHAPE_T_SEGMENT)
    silk.SetStart(pcbnew.VECTOR2I(MM(sx - 1.0), MM(sy)))
    silk.SetEnd(pcbnew.VECTOR2I(MM(sx + 1.0), MM(sy)))
    silk.SetLayer(pcbnew.F_SilkS)
    silk.SetWidth(MM(0.15))
    board.Add(silk)
    free = (200.0, 20.0)
    via(board, free, tented=False)                # a free place: no rule may report it

    path = os.path.join(work, "fcjamma.kicad_pcb")
    board.Save(path)
    violations = drc(work, path)

    def reported(rule_key, at, kind, radius=2.6):
        for v in violations:
            if RULES[rule_key] not in v.get("description", ""):
                continue
            for item in v.get("items", []):
                pos = item.get("pos", {})
                if (item.get("description", "").startswith(kind) and abs(pos.get("x", 1e9) - at[0]) < radius
                        and abs(pos.get("y", 1e9) - at[1]) < radius):
                    return True
        return False

    for name, (at, rule_key, kind) in probes.items():
        if not reported(rule_key, at, kind):
            problems.append(f"the rule '{RULES[rule_key]}' does not report the probe '{name}'")
    for key in RULES:
        if reported(key, free, "Via", radius=1.0):
            problems.append(f"the rule '{RULES[key]}' reports a via in a free place")
    for p in problems:
        print(p)
    missed = len([p for p in problems if "does not report" in p])
    print(f"board rules: {len(probes) - missed}/{len(probes)} probes reported by their rule, "
          f"{len([p for p in problems if 'footprints alone' in p])} findings on the five footprints alone")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
