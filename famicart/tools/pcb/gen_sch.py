#!/usr/bin/env python3
"""Generate hardware/famicart.kicad_sch (+ .kicad_pro) from design.py.

Style: every symbol pin gets a global label carrying its net name (label-style schematic).
Unconnected pins receive no-connect flags. Library symbols are embedded (lib_symbols) so the
file is self-contained; the custom Pico 2 and card-edge symbols come from hardware/famicart.kicad_sym.
"""
import os, uuid, sys, copy
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, dump, find, find_all, Sym
import kicad_symlib as KL
import os as _os, importlib as _il
_DESIGN = _os.environ.get('FC_DESIGN', 'design')
D = _il.import_module(_DESIGN)
HW_LIB = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'hardware'))   # custom symbols/footprints
HW = _os.path.abspath(_os.environ.get('FC_HW_DIR', HW_LIB))                                                        # outputs

HERE = os.path.dirname(os.path.abspath(__file__))
CUSTOM_LIB = os.path.join(HW_LIB, 'famicart.kicad_sym')
ROOT_UUID = '8e7c1580-4b4b-59e1-9722-29cf444c0001'

def U(): return str(uuid.uuid4())

def lib_path(lib):
    return CUSTOM_LIB if lib == 'famicart' else lib

def embedded_symbol(lib, name):
    s = copy.deepcopy(KL.get_symbol(lib_path(lib), name))
    s[1] = f'{lib}:{name}'
    return s

def pin_label_pose(sym_x, sym_y, p):
    """Connection point and label rotation for a pin of an unrotated symbol instance."""
    x = sym_x + p['x']; y = sym_y - p['y']
    rot = {0: 180, 180: 0, 90: 270, 270: 90}[int(p['angle']) % 360]
    return x, y, rot

def prop(name, value, x, y, hide=False, justify=None):
    eff = ['effects', ['font', ['size', 1.27, 1.27]]]
    if justify: eff.append(['justify', Sym(justify)])
    if hide: eff.append(Sym('hide'))
    return ['property', name, value, ['at', x, y, 0], eff]

def main():
    out = ['kicad_sch', ['version', 20221206], ['generator', Sym('famicart')], ['uuid', Sym(ROOT_UUID)], ['paper', 'A1']]
    libsyms = ['lib_symbols']
    seen = set()
    items = []
    # ---- placement on the sheet (mm). Columns of symbols, generous spacing for labels ----
    # Column plan: x=40 J1 ; x=120 U1 ; x=200.. buffers in two rows ; passives bottom.
    def place(ref, x, y, unit=1):
        lib, name, value, fp, _ = D.PARTS[ref]
        key = (lib, name)
        if key not in seen:
            libsyms.append(embedded_symbol(lib, name)); seen.add(key)
        sym = KL.get_symbol(lib_path(lib), name)
        pins = [p for p in KL.pins(sym) if p['unit'] in (0, unit)]
        inst = ['symbol', ['lib_id', f'{lib}:{name}'], ['at', x, y, 0], ['unit', unit], ['in_bom', Sym('yes')], ['on_board', Sym('yes')], ['dnp', Sym('no')],
                ['uuid', Sym(U())],
                prop('Reference', ref, x, y - 2, justify='left'),
                prop('Value', value, x, y + 2, justify='left'),
                prop('Footprint', fp, x, y, hide=True),
                prop('Datasheet', '~', x, y, hide=True)]
        for p in pins: inst.append(['pin', p['number'], ['uuid', Sym(U())]])
        inst.append(['instances', ['project', 'famicart', ['path', f'/{ROOT_UUID}', ['reference', ref], ['unit', unit]]]])
        items.append(inst)
        nets = D.NETS.get(ref, {})
        for p in pins:
            px, py, rot = pin_label_pose(x, y, p)
            net = nets.get(p['number'], 'UNASSIGNED_' + ref + '_' + p['number'])
            if net is None or p['type'] in ('no_connect',):
                items.append(['no_connect', ['at', px, py], ['uuid', Sym(U())]])
                continue
            justify = 'left' if rot == 0 else 'right' if rot == 180 else 'left'
            items.append(['global_label', net, ['shape', Sym('bidirectional')], ['at', px, py, rot], ['fields_autoplaced'],
                          ['effects', ['font', ['size', 1.27, 1.27]], ['justify', Sym(justify)]], ['uuid', Sym(U())],
                          ['property', 'Intersheetrefs', '${INTERSHEET_REFS}', ['at', px, py, 0], ['effects', ['font', ['size', 1.27, 1.27]], Sym('hide')]]])
    # ---- automatic layout: parts sorted by size, placed in rows; margin leaves room for labels ----
    def extent(ref):
        lib, name, _, _, _ = D.PARTS[ref]
        pins = KL.pins(KL.get_symbol(lib_path(lib), name))
        xs = [p['x'] for p in pins] or [0]; ys = [p['y'] for p in pins] or [0]
        return (max(xs) - min(xs) + 60, max(ys) - min(ys) + 14)
    units_of = {ref: (KL.units(KL.get_symbol(lib_path(D.PARTS[ref][0]), D.PARTS[ref][1])) or [1]) for ref in D.PARTS}
    order = sorted(D.PARTS, key=lambda r: -extent(r)[0] * extent(r)[1])
    x, y, row_h, X0, XMAX = 40, 60, 0, 40, 560
    for ref in order:
        for u in units_of[ref]:
            w, h = extent(ref)
            if u > 1: w, h = w * 0.7, h * 0.7
            if x + w > XMAX: x = X0; y += row_h + 10; row_h = 0
            place(ref, round(x + w / 2, 2), round(y + h / 2, 2), unit=u)
            x += w; row_h = max(row_h, h)
    out.append(libsyms)
    out.extend(items)
    out.append(['sheet_instances', ['path', '/', ['page', '1']]])
    text = dump(out)
    os.makedirs(HW, exist_ok=True)
    with open(os.path.join(HW, 'famicart.kicad_sch'), 'w') as f: f.write(text + '\n')
    pro = '''{
  "board": { "design_settings": { "defaults": {}, "rules": {} } },
  "libraries": { "pinned_footprint_libs": [], "pinned_symbol_libs": [] },
  "meta": { "filename": "famicart.kicad_pro", "version": 1 },
  "net_settings": { "classes": [ { "bus_width": 12, "clearance": %(clr)s, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "Default", "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": %(trk)s, "via_diameter": %(via)s, "via_drill": %(vdr)s, "wire_width": 6 } ], "meta": { "version": 3 } },
  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] },
  "sheets": [ [ "%(root)s", "" ] ],
  "text_variables": {}
}
''' % dict(root=ROOT_UUID, clr=os.environ.get('FC_CLEAR', '0.15'), trk=os.environ.get('FC_TRACK', '0.15'), via=os.environ.get('FC_VIA', '0.5'), vdr=os.environ.get('FC_VIA_DRILL', '0.25'))
    pro_path = os.path.join(HW, 'famicart.kicad_pro')
    # keep a project file that pcbnew has already filled with the board's design rules (min drill, edge clearance, ...)
    if not os.path.exists(pro_path) or '"design_settings": { "defaults": {}' in open(pro_path).read() or os.environ.get('FC_WRITE_PRO') == '1':
        with open(pro_path, 'w') as f: f.write(pro)
    # project-local library tables so the custom lib resolves
    rel = os.path.relpath(HW_LIB, HW).replace(os.sep, '/')
    rel = '' if rel == '.' else rel + '/'
    with open(os.path.join(HW, 'sym-lib-table'), 'w') as f:
        f.write('(sym_lib_table\n  (version 7)\n  (lib (name "famicart")(type "KiCad")(uri "${KIPRJMOD}/%sfamicart.kicad_sym")(options "")(descr "famicart custom symbols"))\n)\n' % rel)
    with open(os.path.join(HW, 'fp-lib-table'), 'w') as f:
        f.write('(fp_lib_table\n  (version 7)\n  (lib (name "famicart")(type "KiCad")(uri "${KIPRJMOD}/%sfamicart.pretty")(options "")(descr "famicart custom footprints"))\n)\n' % rel)
    print('schematic written:', os.path.join(HW, 'famicart.kicad_sch'), len(items), 'items')

if __name__ == '__main__':
    main()
