"""Write the circuit model as a KiCad project (label-style schematic sheets).

Symbols are placed with kicad-sch-api; net labels, no-connect marks and notes are
appended to the saved files as plain S-expressions.  Pin positions are taken from
Schematic.get_component_pin_position(), which was checked against kicad-cli's own
netlist export (Component.get_pin_position() and get_pins_info() mirror the Y axis).
"""
import math
import os
import re
import uuid

import kicad_sch_api as ksa

from .model import SymDef, PIN_TYPES

GRID = 2.54
CHAR = 1.15          # approximate width of one label character at 1.27 mm text size
PAPER = {"A3": (420, 297), "A2": (594, 420), "A1": (841, 594), "A0": (1189, 841)}


def U():
    return str(uuid.uuid4())


def snap(v):
    return round(v / GRID) * GRID


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ---------------------------------------------------------------- symbol library
def symdef_geometry(sd: SymDef):
    ln = max([len(p[1]) for p in sd.left if p] + [1])
    rn = max([len(p[1]) for p in sd.right if p] + [1])
    w = max(20.32, math.ceil(((ln + rn) * CHAR + 7.62) / 5.08) * 5.08)
    n = max(len(sd.left), len(sd.right))
    h = (n + 1) * GRID
    return w, h


def symdef_sexpr(sd: SymDef):
    w, h = symdef_geometry(sd)
    top = h / 2
    # keep pin ends on the 2.54 mm grid whatever the pin count
    top = math.ceil(top / GRID) * GRID
    o = [f'\t(symbol "{sd.name}"', "\t\t(pin_names (offset 1.016))", "\t\t(exclude_from_sim no)", "\t\t(in_bom yes)", "\t\t(on_board yes)"]

    def prop(k, v, y, hide=False):
        return (f'\t\t(property "{k}" "{esc(v)}"\n\t\t\t(at 0 {y:.2f} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)'
                + ("\n\t\t\t\t(hide yes)" if hide else "") + "\n\t\t\t)\n\t\t)")
    o += [prop("Reference", sd.prefix, top + 2.54), prop("Value", sd.name, -top - 2.54),
          prop("Footprint", "", 0, True), prop("Datasheet", "", 0, True), prop("Description", sd.desc, 0, True)]
    o.append(f'\t\t(symbol "{sd.name}_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start {-w/2:.2f} {top:.2f})\n\t\t\t\t(end {w/2:.2f} {-top:.2f})\n'
             "\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)\n\t\t)")
    o.append(f'\t\t(symbol "{sd.name}_1_1"')
    for side, lst in (("L", sd.left), ("R", sd.right)):
        for i, p in enumerate(lst):
            if p is None:
                continue
            num, name, typ = p
            y = top - GRID * (i + 1)
            x = -w / 2 - GRID if side == "L" else w / 2 + GRID
            ang = 0 if side == "L" else 180
            o.append(f'\t\t\t(pin {PIN_TYPES[typ]} line\n\t\t\t\t(at {x:.2f} {y:.2f} {ang})\n\t\t\t\t(length 2.54)\n'
                     f'\t\t\t\t(name "{esc(name)}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
                     f'\t\t\t\t(number "{esc(str(num))}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)')
    o.append("\t\t)")
    o.append("\t\t(embedded_fonts no)\n\t)")
    return "\n".join(o)


def write_symbol_lib(design, path):
    body = "\n".join(symdef_sexpr(sd) for sd in design.symdefs.values())
    with open(path, "w", encoding="utf-8") as f:
        f.write('(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "fcgen")\n\t(generator_version "9.0")\n' + body + "\n)\n")


# ---------------------------------------------------------------- S-expression snippets
def glabel(text, x, y, direction):
    rot, just = {"L": (180, "right"), "R": (0, "left"), "U": (90, "left"), "D": (270, "right")}[direction]
    return (f'\t(global_label "{esc(text)}"\n\t\t(shape passive)\n\t\t(at {x:.2f} {y:.2f} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at 0 0 0)\n\t\t\t(effects\n'
            "\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n\t)")


def noconn(x, y):
    return f'\t(no_connect\n\t\t(at {x:.2f} {y:.2f})\n\t\t(uuid "{U()}")\n\t)'


def text(s, x, y, size=1.8):
    return (f'\t(text "{esc(s)}"\n\t\t(exclude_from_sim no)\n\t\t(at {x:.2f} {y:.2f} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n'
            f'\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


# ---------------------------------------------------------------- layout
def cell_size(part):
    """(width, height, left margin) of the area one part needs, labels included."""
    nets = [n for n in part.conn.values() if n]
    longest = max([len(n) for n in nets] + [3]) * CHAR + 4
    if isinstance(part.sym, SymDef):
        w, h = symdef_geometry(part.sym)
        by = {str(p[0]): p for p in part.sym.pins()}
        ll = max([len(part.conn[str(p[0])] or "") for p in part.sym.left if p] + [2]) * CHAR + 4
        rl = max([len(part.conn[str(p[0])] or "") for p in part.sym.right if p] + [2]) * CHAR + 4
        return ll + w + 2 * GRID + rl + 6, h + 14, ll + GRID + w / 2
    n = len(part.conn)
    if part.horizontal and n == 2:
        return 2 * longest + 12, 7.62, longest + 5
    if part.lib_id.startswith("Connector_Generic:Conn_01x"):
        return 2 * longest + 14, n * GRID + 12, longest + 6
    if part.lib_id.startswith("Connector_Generic:Conn_02x"):
        return 2 * longest + 20, n / 2 * GRID + 12, longest + 8
    if part.lib_id.startswith("Switch:SW_DIP"):
        return 2 * longest + 24, n / 2 * GRID + 14, longest + 12
    if "R_Pack04" in part.lib_id:
        return 22, 2 * longest + 14, 11
    return 2 * longest + 22, 2 * longest + 18, longest + 10       # three-pin parts, vertical labels above and below


def layout(parts, paper_w, top):
    """Flow layout: tall parts in rows first, then the small parts in rows below."""
    pos = {}
    big = [p for p in parts if cell_size(p)[1] > 32]
    small = [p for p in parts if cell_size(p)[1] <= 32]
    x, y, rowh = 12.0, top, 0.0
    for group in (big, small):
        x = 12.0
        if rowh:
            y += rowh + 8
            rowh = 0.0
        for p in group:
            w, h, lm = cell_size(p)
            if x + w > paper_w - 12:
                x = 12.0
                y += rowh + 6
                rowh = 0.0
            pos[p.ref] = (snap(x + lm), snap(y + h / 2 + 4))
            x += w
            rowh = max(rowh, h)
    return pos, y + rowh + 12


# ---------------------------------------------------------------- property clean-up
def _balanced(t, i):
    depth = 0
    for j in range(i, len(t)):
        if t[j] == "(":
            depth += 1
        elif t[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    raise ValueError("unbalanced")


def tidy_properties(t, dnp_refs):
    """Hide every field except Reference and Value, and mark DNP parts."""
    out, i = [], 0
    for m in re.finditer(r'\(property "([^"]+)" "', t):
        name = m.group(1)
        if name in ("Reference", "Value", "Sheetname", "Sheetfile", "Intersheetrefs"):
            continue
        j = _balanced(t, m.start())
        blk = t[m.start():j + 1]
        if "(hide yes)" not in blk and "(effects" in blk:
            k = blk.index("(effects")
            ke = _balanced(blk, k)
            blk = blk[:ke] + "(hide yes)" + blk[ke:]
            out.append((m.start(), j + 1, blk))
    for a, b, blk in reversed(out):
        t = t[:a] + blk + t[b:]
    for ref in dnp_refs:
        k = t.find(f'(property "Reference" "{ref}"')
        if k < 0:
            continue
        s0 = t.rfind("(dnp no)", 0, k)
        if s0 >= 0 and t.rfind("(symbol", 0, k) < s0:
            t = t[:s0] + "(dnp yes)" + t[s0 + 8:]
    return t


def place_two_pin_text(t, refs):
    """Reference above and value below a two-pin part that is drawn lying down."""
    for ref in refs:
        k = t.find(f'(property "Reference" "{ref}"')
        if k < 0:
            continue
        s0 = t.rfind("(symbol", 0, k)
        m = re.search(r"\(at ([-0-9.]+) ([-0-9.]+) [-0-9.]+\)", t[s0:k])
        if not m:
            continue
        x, y = float(m.group(1)), float(m.group(2))
        for name, dy in (("Reference", -2.3), ("Value", 2.3)):
            a = t.find(f'(property "{name}" "', s0)
            b = _balanced(t, a)
            blk = t[a:b + 1]
            blk = re.sub(r"\(at [-0-9.]+ [-0-9.]+ [-0-9.]+\)", f"(at {x:.2f} {y + dy:.2f} 90)", blk, count=1)   # 90: the symbol itself is turned by 90
            blk = blk.replace("(justify left)", "")
            t = t[:a] + blk + t[b + 1:]
    return t


def inject(path, items):
    t = open(path, encoding="utf-8").read().rstrip()
    k = t.rfind("\n\t(sheet_instances")
    if k < 0:
        k = t.rfind("\n\t(embedded_fonts")
    if k < 0:
        k = t.rfind("\n)")
    t = t[:k] + "\n" + "\n".join(items) + t[k:]
    open(path, "w", encoding="utf-8").write(t + "\n")


# ---------------------------------------------------------------- schematic writer
def direction_of(part, num, comp_xy, pin_xy):
    if isinstance(part.sym, SymDef):
        return "L" if any(p and str(p[0]) == num for p in part.sym.left) else "R"
    dx, dy = pin_xy[0] - comp_xy[0], pin_xy[1] - comp_xy[1]
    if part.lib_id.startswith(("Connector_Generic:", "Switch:SW_DIP")):
        return "L" if dx < 0 else "R"          # tall symbols: their pins only point sideways
    if abs(dx) >= abs(dy):
        return "L" if dx < 0 else "R"
    return "U" if dy < 0 else "D"


def write_project(design, outdir, power_flag_nets):
    os.makedirs(outdir, exist_ok=True)
    name = design.name
    symlib = os.path.join(outdir, "fcjamma.kicad_sym")
    write_symbol_lib(design, symlib)
    with open(os.path.join(outdir, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n  (version 7)\n  (lib (name "fcjamma")(type "KiCad")(uri "${KIPRJMOD}/fcjamma.kicad_sym")(options "")(descr "Famicom JAMMA board symbols"))\n)\n')
    with open(os.path.join(outdir, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n  (version 7)\n  (lib (name "fcjamma")(type "KiCad")(uri "${KIPRJMOD}/fcjamma.pretty")(options "")(descr "Famicom JAMMA board footprints"))\n)\n')
    pro = os.path.join(outdir, f"{name}.kicad_pro")
    if not os.path.exists(pro):
        with open(pro, "w") as f:
            # the embedded copies of library symbols are written by the generator and differ
            # cosmetically from the library, so that one check is switched off
            f.write('{"erc":{"rule_severities":{"lib_symbol_mismatch":"ignore"}},"meta":{"filename":"%s.kicad_pro","version":3},'
                    '"schematic":{"legacy_lib_dir":"","legacy_lib_list":[]},"sheets":[],"text_variables":{}}\n' % name)

    cache = ksa.get_symbol_cache()
    cache.add_library_path(os.path.abspath(symlib))

    root = ksa.create_schematic(name)
    root.set_paper_size("A3")
    root.set_title_block(title=design.title, rev=design.rev, company="")
    root_items = [text(design.title, 20, 20, 3.0)]
    files = []

    for idx, sh in enumerate(design.sheets):
        parts = [p for p in design.parts.values() if p.sheet == sh.key]
        notes = design.notes.get(sh.key, [])
        top = 22 + 5 * len(notes)
        paper = "A3"
        for paper in ("A3", "A2", "A1", "A0"):
            pos, bottom = layout(parts, PAPER[paper][0], top)
            if bottom < PAPER[paper][1] - 20:
                break
        sch = ksa.create_schematic(name)
        sch.set_paper_size(paper)
        sch.set_title_block(title=f"{design.title} - {sh.title}", rev=design.rev, company="")
        sx, sy = 25.4 + (idx % 4) * 63.5, 38.1 + (idx // 4) * 38.1
        su = root.add_sheet(sh.key, f"{sh.key}.kicad_sch", position=(sx, sy), size=(50.8, 25.4), project_name=name, page_number=str(idx + 2))
        sch.set_hierarchy_context(root.uuid, su)
        root_items.append(text(sh.title, sx, sy + 33, 1.6))
        items = [text(sh.title, 12, 14, 3.0)]
        for i, n in enumerate(notes):
            items.append(text(n, 12, 20 + 5 * i, 1.5))
        for p in parts:
            xy = pos[p.ref]
            props = {"Source": p.src}
            if p.src in ("JLC", "JLCX"):
                props["LCSC"] = p.code
            elif p.src == "AKI" and p.code:
                props["Akizuki"] = p.code
            if p.note:
                props["Note"] = p.note
            rot = 90 if (p.horizontal and len(p.conn) == 2) else 0
            sch.components.add(p.lib_id, reference=p.ref, value=p.value, position=xy, footprint=p.footprint, rotation=rot, **props)
            for num, net in p.conn.items():
                # kicad-sch-api reports the two pins of a rotated part the wrong way round
                # (found by the netlist comparison in build.py), so read the other pin's position
                q = {"1": "2", "2": "1"}[num] if rot else num
                pp = sch.get_component_pin_position(p.ref, q)
                if pp is None:
                    raise ValueError(f"{p.ref}: symbol {p.lib_id} has no pin {num}")
                if net is None:
                    items.append(noconn(pp.x, pp.y))
                else:
                    items.append(glabel(net, pp.x, pp.y, direction_of(p, num, xy, (pp.x, pp.y))))
        path = os.path.join(outdir, f"{sh.key}.kicad_sch")
        sch.save(path)
        inject(path, items)
        files.append((path, [p.ref for p in parts if p.dnp], [p.ref for p in parts if p.horizontal and len(p.conn) == 2]))

    # power flags on the root sheet
    for i, net in enumerate(power_flag_nets):
        ref = f"#FLG{i+1:02d}"
        xy = (snap(30 + i * 25.4), snap(170))
        root.components.add("power:PWR_FLAG", reference=ref, value="PWR_FLAG", position=xy)
        pp = root.get_component_pin_position(ref, "1")
        root_items.append(glabel(net, pp.x, pp.y, "D"))
    rpath = os.path.join(outdir, f"{name}.kicad_sch")
    root.save(rpath)
    inject(rpath, root_items)
    files.append((rpath, [], []))
    for path, dnp, lying in files:
        t = open(path, encoding="utf-8").read()
        open(path, "w", encoding="utf-8").write(place_two_pin_text(tidy_properties(t, dnp), lying))
    return rpath, [f[0] for f in files]
