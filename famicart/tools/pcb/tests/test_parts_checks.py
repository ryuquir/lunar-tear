#!/usr/bin/env python3
"""Self-test of the rev H additions to gen_jlc.py, check_cpl.py and check_jlc.py (declared part classes, two-sided
assembly, pad-name aliases, multilayer rules, X-ray and double-sided assembly fees).

It writes a small design module and a 6-layer board with parts on both sides into a temporary directory (pcbnew),
then runs the tools on it:
  - gen_jlc.py main(): BOM, CPL (bottom-side angle convention), gerbers.zip with the inner layers, the declared-class
    parts check (the parts API answer is simulated: classes, stock, canPresaleNumber, lossNumber),
  - check_cpl.py main(): every placement, top and bottom, against JLCPCB's library footprints. Offline the library pads
    are the EasyEDA pad tables below (recorded 2026-11-15); with --online they are downloaded from EasyEDA and must
    equal the tables, and the parts API is asked for the classes of the rev H parts.
  - check_jlc.py main(): layer count, small holes, plated holes in the drill file, pours on inner layers, parts on the
    bottom side, declared classes in parts_check.csv,
and checks that wrong data is refused: a bottom-side angle without the mirror, a part on the back that BOTTOM_OK
does not allow, a missing pad alias, a small via with too little copper, an inner pour too close to the edge, a class
or stock that does not fit the order.
    python3 tests/test_parts_checks.py [--online]        (from tools/pcb; exit status 1 when a test fails)"""
import os, sys, csv, io, shutil, tempfile, importlib, contextlib, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ONLINE = '--online' in sys.argv
SYS_FP = '/usr/share/kicad/footprints'

# EasyEDA library footprints (pad number, x, y in mm from the footprint origin, y down), as check_cpl.library_pads reads
# them; recorded from easyeda.com/api/products/<code>/components on 2026-11-15. --online compares them with the live data.
EASYEDA = {
    'C141836': ('SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR', [('5', -1.3, 0.95), ('4', -1.3, -0.95), ('3', 1.3, -0.95), ('2', 1.3, 0.0), ('1', 1.3, 0.95)]),
    'C2286': ('LED-SMD_L1.6-W0.8-R-RD', [('2', -0.75, 0.0), ('1', 0.75, 0.0)]),
    'C165948': ('USB-C_SMD-TYPE-C-31-M-12_1', [('B8', -1.75, -2.474), ('A5', -1.25, -2.474), ('B7', -0.75, -2.474), ('A6', -0.25, -2.474),
                                             ('A7', 0.25, -2.474), ('B6', 0.75, -2.474), ('A8', 1.25, -2.474), ('B5', 1.75, -2.474),
                                             ('A1B12', -3.2, -2.474), ('B1A12', 3.2, -2.474), ('B4A9', 2.4, -2.474), ('A4B9', -2.4, -2.474),
                                             ('2', 4.325, 2.474), ('1', 4.325, -1.706), ('4', -4.325, -1.706), ('3', -4.325, 2.474)]),
    'C362368': ('OSC-SMD_4P-L3.2-W2.5-BL', [('1', -1.1, 0.875), ('2', 1.1, 0.875), ('3', 1.1, -0.875), ('4', -1.1, -0.875)]),
    'C20197': ('RES-ARRAY-SMD_0603-8P-L3.2-W1.6-BL', [('5', 1.2, -0.8), ('4', 1.2, 0.8), ('6', 0.4, -0.8), ('3', 0.4, 0.8),
                                                    ('7', -0.4, -0.8), ('2', -0.4, 0.8), ('8', -1.2, -0.8), ('1', -1.2, 0.8)]),
    'C25100': ('R0402', [('2', 0.433, 0.0), ('1', -0.433, 0.0)]),
}
USB_SHIFT = 1.5     # mm: the KiCad HRO footprint moved by this in +y lies on the EasyEDA origin (rev H draws such a copy)

DESIGN = '''"""check-tool self-test fixture (tests/test_parts_checks.py): 6 layers, parts on both sides."""
REV = 'rev selftest'
LAYERS = 6
JLC_RULES = True
ASSEMBLY = 'both'
BOTTOM_OK = {'R', 'RN', 'Y', 'Capacitor_SMD:C_0402_1005Metric'}
TRACK, CLEAR, VIA_DIA, VIA_DRILL = 0.15, 0.15, 0.5, 0.3
SOT = 'Package_TO_SOT_SMD:SOT-23-5'; LED = 'LED_SMD:LED_0603_1608Metric'; USB = 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12'
R0402 = 'Resistor_SMD:R_0402_1005Metric'; C0402 = 'Capacitor_SMD:C_0402_1005Metric'; RARR = 'Resistor_SMD:R_Array_Convex_4x0603'
XTAL = 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm'; QFN = 'Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm'
PARTS = {
    'U1': ('', '', 'TLV62569DBVR', SOT, (10.0, 8.0, 0, 'F')), 'U2': ('', '', 'TLV62569DBVR', SOT, (16.0, 8.0, 90, 'F')),
    'D1': ('', '', 'red LED', LED, (22.0, 8.0, 0, 'F')), 'D2': ('', '', 'red LED', LED, (26.0, 8.0, 180, 'F')),
    'J3': ('', '', 'USB-C', USB, (40.0, 8.0, 0, 'F')),
    'R1': ('', '', '27', R0402, (8.0, 22.0, 0, 'B')), 'R2': ('', '', '27', R0402, (12.0, 22.0, 90, 'B')), 'R3': ('', '', '27', R0402, (16.0, 22.0, 180, 'B')),
    'C1': ('', '', '27 (as a capacitor)', C0402, (8.0, 30.0, 270, 'B')),
    'RN1': ('', '', '1k x4', RARR, (22.0, 22.0, 0, 'B')), 'RN2': ('', '', '1k x4', RARR, (27.0, 22.0, 90, 'B')), 'RN3': ('', '', '1k x4', RARR, (32.0, 22.0, 180, 'B')),
    'Y1': ('', '', '12MHz', XTAL, (38.0, 22.0, 90, 'B')), 'Y2': ('', '', '12MHz', XTAL, (44.0, 22.0, 270, 'B')), 'Y3': ('', '', '12MHz', XTAL, (50.0, 22.0, 180, 'B')),
    'U5': ('', '', 'RP2350B (not placed here)', QFN, (50.0, 32.0, 0, 'F')),
}
LCSC = {'TLV62569DBVR': ('C141836', 'TLV62569DBVR'), 'red LED': ('C2286', 'KT-0603R'), 'USB-C': ('C165948', 'TYPE-C-31-M-12'),
        '27': ('C25100', '27R 0402'), '1k x4': ('C20197', '4D03WGJ0102T5E'), '12MHz': ('C362368', 'TXM12M0004322CBCDO00T')}
LCSC_CLASS = {'C141836': 'Extended', 'C2286': 'Basic', 'C165948': 'Extended', 'C25100': 'Extended', 'C20197': 'Basic', 'C362368': 'Extended'}
'''

failures, passed = [], [0]
def check(cond, what):
    if cond: passed[0] += 1; print('  ok  ', what)
    else: failures.append(what); print('  FAIL', what)

def run(fn):
    """(exit code or None, stdout) of fn()."""
    out = io.StringIO(); code = None
    with contextlib.redirect_stdout(out):
        try: fn()
        except SystemExit as e: code = e.code
    return code, out.getvalue()

# ---------------------------------------------------------------- fixture
def build_board(hw, D, vias=((30.0, 34.0, 0.5, 0.3), (34.0, 34.0, 0.45, 0.2)), edge_pour=False, layers=6, pth=None):
    """The fixture board: Edge.Cuts 60 x 40 mm, `layers` copper layers, a GND pour on In1 (and on In3 up to the left
    edge with edge_pour), the parts of D.PARTS except U5, vias (x, y, diameter, hole), pth = (x, y, copper, hole): one
    plated through-hole pad of its own; fabrication files in <hw>/fab."""
    import pcbnew
    from pcbnew import FromMM, VECTOR2I
    os.makedirs(os.path.join(hw, 'fab'), exist_ok=True)
    b = pcbnew.BOARD(); b.SetCopperLayerCount(layers)
    b.GetDesignSettings().m_CopperEdgeClearance = 0       # let a pour reach the edge (the refusal case)
    b.GetDesignSettings().SetBoardThickness(FromMM(1.2))
    gnd = pcbnew.NETINFO_ITEM(b, 'GND'); b.Add(gnd)
    for (x0, y0, x1, y1) in ((0, 0, 60, 0), (60, 0, 60, 40), (60, 40, 0, 40), (0, 40, 0, 0)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1))
        s.SetStart(VECTOR2I(FromMM(x0), FromMM(y0))); s.SetEnd(VECTOR2I(FromMM(x1), FromMM(y1))); b.Add(s)
    for ref, (lib, sym, val, fpname, (x, y, rot, side)) in D.PARTS.items():
        if ref == 'U5': continue
        l, n = fpname.split(':')
        fp = pcbnew.FootprintLoad(os.path.join(SYS_FP, l + '.pretty'), n)
        if ref == 'J3':                          # the copy of the footprint with its origin on the EasyEDA origin
            for p in fp.Pads():
                p.SetPos0(p.GetPos0() + VECTOR2I(0, FromMM(USB_SHIFT))); p.SetPosition(p.GetPosition() + VECTOR2I(0, FromMM(USB_SHIFT)))
        fp.SetReference(ref); fp.SetValue(val); b.Add(fp)
        fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
        if side == 'B': fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(rot)
    for (x, y, dia, hole) in vias:
        v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); v.SetWidth(FromMM(dia)); v.SetDrill(FromMM(hole)); v.SetNet(gnd); b.Add(v)
    if pth:                                    # a plated hole that belongs to a footprint (no LCSC part: not in the BOM)
        x, y, cu, hole = pth
        fp = pcbnew.FOOTPRINT(b); fp.SetReference('TP1'); fp.SetValue('test point'); fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_BOARD_ONLY); b.Add(fp); fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
        pad = pcbnew.PAD(fp); pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE); pad.SetNumber('1')
        pad.SetSize(VECTOR2I(FromMM(cu), FromMM(cu))); pad.SetDrillSize(VECTOR2I(FromMM(hole), FromMM(hole))); pad.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
        pad.SetLayerSet(pcbnew.PAD.PTHMask()); pad.SetNet(gnd); fp.Add(pad)
    def pour(layer, x0, y0, x1, y1):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd); z.SetIsFilled(False); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        o = z.Outline(); o.NewOutline()
        for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): o.Append(FromMM(px), FromMM(py))
        b.Add(z)
    pour(pcbnew.In1_Cu, 2.0, 2.0, 58.0, 38.0)
    if edge_pour: pour(pcbnew.In3_Cu, 0.1, 30.0, 6.0, 38.0)
    pcb = os.path.join(hw, 'famicart.kicad_pcb'); pcbnew.SaveBoard(pcb, b)
    b = pcbnew.LoadBoard(pcb)                  # fill the pours on the board as loaded from its file (as route_pcb.py does)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity(); pcbnew.SaveBoard(pcb, b)
    fab = os.path.join(hw, 'fab')
    cu = ','.join(['F.Cu'] + ['In%d.Cu' % k for k in range(1, layers - 1)] + ['B.Cu'])
    subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', cu + ',F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts', '-o', fab + '/', pcb], check=True, capture_output=True)
    subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '-o', fab + '/', pcb], check=True, capture_output=True)
    return pcb

def catalogue(overrides=None):
    """Simulated parts API: an entry per code with the declared class and ample stock (overrides: {code: {field: value}})."""
    D = sys.modules['design_selftest']
    def lookup(code):
        cls = D.LCSC_CLASS.get(code, 'Basic')
        it = dict(componentCode=code, componentModelEn='part ' + code, componentLibraryType={'Basic': 'base', 'Extended': 'expand'}[cls],
                  stockCount=100000, canPresaleNumber=100000, lossNumber=3)
        it.update((overrides or {}).get(code, {}))
        return it, ''
    return lookup

LIB = dict(EASYEDA)        # the library footprints check_cpl uses: the recorded tables, or (--online) the live data

def load(hw):
    """(gen_jlc, check_cpl, check_jlc) loaded for the fixture design and the hardware directory `hw`."""
    os.environ['FC_HW_DIR'] = hw
    mods = []
    for name in ('gen_jlc', 'check_cpl', 'check_jlc'):
        mods.append(importlib.reload(sys.modules[name]) if name in sys.modules else importlib.import_module(name))
    mods[1].library_pads = lambda code: LIB[code]
    return mods

def jlc_check(check_jlc):
    """check_jlc.main() with draw_outline.py left out (it needs a cartridge shell; the fixture has none)."""
    real = subprocess.run
    def run_(args, *a, **k):
        if any(str(x).endswith('draw_outline.py') for x in args): return subprocess.CompletedProcess(args, 0, b'', b'')
        return real(args, *a, **k)
    check_jlc.subprocess.run = run_
    try: return run(check_jlc.main)
    finally: check_jlc.subprocess.run = real

def write_package(gen_jlc, overrides=None):
    gen_jlc.lookup = catalogue(overrides)
    return run(gen_jlc.main)

# ---------------------------------------------------------------- tests
def test_estimate(gen_jlc, D):
    print('assembly estimate (X-ray, two-sided)')
    P = gen_jlc.JLC_PRICE
    for t, j, n in ((10, 721, 2), (10, 721, 5), (3, 100, 2)):       # the formula used up to rev G, term for term
        old = P['setup'] + P['stencil'] + P['feeder'] * t + max(P['joint'] * j, P['board']) * n + P['packing'] + P['confirm']
        check(gen_jlc.assembly_estimate(t, j, n) == old, 'one side, no X-ray: the same number as before (%d types, %d joints, %d boards)' % (t, j, n))
    for parts, fee in ((0, 0.0), (1, 1.64), (10, 16.4), (11, 9.02), (50, 41.0), (51, 24.99), (200, 98.0), (201, 66.33)):
        check(abs(gen_jlc.xray_fee(parts) - fee) < 1e-9, 'X-ray fee for %d parts in the order: $%.2f' % (parts, fee))
    # docs/13_rev_h_plan.md: 24 types, about 1571 joints, 8 QFN per board, two-sided -> about $123.4 (2 boards) / $150.6 (5)
    e2, e5 = gen_jlc.assembly_estimate(24, 1571, 2, xray=8, sides=2), gen_jlc.assembly_estimate(24, 1571, 5, xray=8, sides=2)
    check(abs(e2 - 123.36) < 0.01 and abs(e5 - 150.58) < 0.01, 'rev H numbers of the plan: $%.2f for 2 boards, $%.2f for 5' % (e2, e5))
    check(abs(gen_jlc.assembly_estimate(5, 100, 2, sides=2) - gen_jlc.assembly_estimate(5, 100, 2) - (51.12 - 25.56 + 16.42 - 8.21)) < 1e-9,
          'two-sided assembly adds the double-sided setup and stencil')
    check(gen_jlc.xray_count({'U5', 'U1', 'R1'}) == 1, 'X-ray count: QFN yes, SOT-23-5 and 0402 no')
    keep = dict(D.PARTS)
    for i, name in enumerate(('X_DFN-8', 'X_LGA-14', 'X_BGA-64', 'X_WSON-8', 'X_SOIC-8', 'X_TSSOP-20')): D.PARTS['T%d' % i] = ('', '', 't', 'lib:' + name, (0, 0, 0, 'F'))
    check(gen_jlc.xray_count({'T%d' % i for i in range(6)}) == 4, 'X-ray count: DFN, LGA, BGA, SON yes; SOIC, TSSOP no')
    D.PARTS.clear(); D.PARTS.update(keep)

def test_declared(gen_jlc, D, hw):
    print('declared part classes (LCSC_CLASS)')
    per = {'C141836': 2, 'C2286': 8}
    keep = dict(D.LCSC_CLASS)
    D.LCSC_CLASS.clear(); D.LCSC_CLASS.update({'C141836': 'Extended', 'C2286': 'Basic'})
    def case(overrides, qty=None, per_board=per):
        gen_jlc.lookup = catalogue(overrides)
        if qty is not None: os.environ['FC_PCBA_QTY'] = str(qty)
        else: os.environ.pop('FC_PCBA_QTY', None)
        code, out = run(lambda: gen_jlc.check_declared(per_board))
        rows = list(csv.DictReader(open(os.path.join(hw, 'jlcpcb', 'parts_check.csv'))))
        return code, out, {r['LCSC']: r for r in rows}, open(os.path.join(hw, 'jlcpcb', 'parts_check.csv')).readline().strip()
    code, out, rows, head = case({})
    check(code is None and all(r['Result'] == 'OK' for r in rows.values()), 'declared classes and ample stock: passes')
    check(head.startswith('LCSC,Part,Library,Stock,Result,'), 'parts_check.csv keeps its first five columns (LCSC, Part, Library, Stock, Result)')
    check(head.endswith(',Problem,Boards') and all(r['Boards'] == '5' for r in rows.values()), 'parts_check.csv: the number of boards checked for (Boards) is the last column (5 by default)')
    check(rows['C141836']['Library'] == 'Extended' and rows['C2286']['Library'] == 'Basic', 'the Library column carries the class from the catalogue')
    check(rows['C2286']['Need'] == str(8 * 5 + 3), 'need = per board x 5 boards (default FC_PCBA_QTY) + lossNumber')
    code, out, rows, _ = case({'C2286': dict(componentLibraryType='expand')})
    check(code is not None and rows['C2286']['Result'] == 'NG' and 'declares Basic' in rows['C2286']['Problem'], 'a Basic declaration of an Extended part fails')
    code, out, rows, _ = case({'C141836': dict(componentLibraryType='base')})
    check(code is not None and rows['C141836']['Result'] == 'NG', 'an Extended declaration of a Basic part fails (the declaration must be exact)')
    need = 2 * 5 + 3
    code, out, rows, _ = case({'C141836': dict(stockCount=3 * need - 1)})
    check(code is not None and 'stock %d < 3 x %d' % (3 * need - 1, need) in rows['C141836']['Problem'], 'stock below 3 x need fails')
    code, out, rows, _ = case({'C141836': dict(stockCount=3 * need)})
    check(code is None, 'stock of exactly 3 x need passes')
    code, out, rows, _ = case({'C141836': dict(canPresaleNumber=need - 1)})
    check(code is not None and 'canPresaleNumber' in rows['C141836']['Problem'], 'canPresaleNumber below need fails')
    code, out, rows, _ = case({'C141836': dict(canPresaleNumber=need)})
    check(code is None, 'canPresaleNumber of exactly need passes')
    code, out, rows, _ = case({'C141836': dict(canPresaleNumber=None)})
    check(code is not None, 'a catalogue entry without canPresaleNumber fails')
    code, out, rows, _ = case({'C141836': dict(canPresaleNumber=2 * 2 + 3)}, qty=2)
    check(code is None and rows['C141836']['Need'] == '7' and rows['C141836']['Boards'] == '2', 'FC_PCBA_QTY=2: need = 2 x 2 + 3, Boards 2')
    code, out, rows, _ = case({}, per_board=dict(per, C99999=1))
    check(code is not None and 'not declared' in rows['C99999']['Problem'], 'a placed code without a declaration fails')
    code, out, rows, _ = case({}, per_board={'C141836': 2})
    check(code is not None and rows['C2286']['Result'] == 'NG', 'a declared code that is not placed fails')
    gen_jlc.lookup = lambda code: (None, 'not found')
    code, out = run(lambda: gen_jlc.check_declared(per))
    check(code is not None, 'a code the catalogue does not find fails')
    os.environ.pop('FC_PCBA_QTY', None)
    D.LCSC_CLASS.clear(); D.LCSC_CLASS.update(keep)

def test_cpl_rot(gen_jlc, D):
    print('CPL angle corrections')
    check(gen_jlc.cpl_correction('Package_TO_SOT_SMD:SOT-23-5') == 180, 'SOT-23-5: 180 for designs with LCSC_CLASS')
    keep = D.LCSC_CLASS; del D.LCSC_CLASS
    check(gen_jlc.cpl_correction('Package_TO_SOT_SMD:SOT-23-5') == 0, 'SOT-23-5: 0 for designs without LCSC_CLASS (rev B-D keep their files)')
    check(gen_jlc.cpl_correction('Resistor_SMD:R_Array_Convex_4x0603') == 270 and gen_jlc.cpl_correction('Package_TO_SOT_SMD:SOT-23') == 180, 'the rev G corrections are unchanged')
    D.LCSC_CLASS = keep

def test_package(hw, D):
    print('gen_jlc main(): two-sided package of a 6-layer board')
    gen_jlc, check_cpl, check_jlc = load(hw)
    code, out = write_package(gen_jlc)
    check(code is None, 'gen_jlc.py writes the package (exit %r)%s' % (code, '' if code is None else ': ' + out[-300:]))
    cpl = {r['Designator']: r for r in csv.DictReader(open(os.path.join(hw, 'jlcpcb', 'cpl_jlc.csv')))}
    want = {'U1': ('Top', 180.0), 'U2': ('Top', 270.0), 'D1': ('Top', 0.0), 'D2': ('Top', 180.0), 'J3': ('Top', 0.0),
            'R1': ('Bottom', 180.0), 'R2': ('Bottom', 90.0), 'R3': ('Bottom', 0.0), 'C1': ('Bottom', 270.0),
            'RN1': ('Bottom', 90.0), 'RN2': ('Bottom', 0.0), 'RN3': ('Bottom', 270.0), 'Y1': ('Bottom', 90.0), 'Y2': ('Bottom', 270.0), 'Y3': ('Bottom', 0.0)}
    got = {r: (cpl[r]['Layer'], float(cpl[r]['Rotation'])) for r in cpl}
    check(got == want, 'CPL layers and angles: top = KiCad + correction, bottom = 180 - KiCad + correction')
    if got != want: print('       ', sorted(set(got.items()) ^ set(want.items())))
    import pcbnew
    b = pcbnew.LoadBoard(os.path.join(hw, 'famicart.kicad_pcb'))
    check(all(abs(float(cpl[r]['Mid X'][:-2]) - pcbnew.ToMM(b.FindFootprintByReference(r).GetPosition().x)) < 1e-3 for r in cpl), 'Mid X is the board x on both sides (not negated)')
    import zipfile
    names = zipfile.ZipFile(os.path.join(hw, 'jlcpcb', 'gerbers.zip')).namelist()
    check(all(any(n.endswith('In%d_Cu.g%d' % (k, k + 1)) for n in names) for k in range(1, 5)), 'gerbers.zip carries In1..In4 (.g2 .. .g5)')
    rows = {r['LCSC']: r for r in csv.DictReader(open(os.path.join(hw, 'jlcpcb', 'parts_check.csv')))}
    check(set(rows) == set(D.LCSC_CLASS) and rows['C20197']['Per board'] == '3' and rows['C25100']['Per board'] == '4', 'parts check counts the parts per board from the BOM (C25100: 3 R + 1 C)')

    print('check_cpl main(): pad by pad, both sides%s' % (' (EasyEDA, online)' if ONLINE else ' (recorded EasyEDA pads)'))
    code, out = run(check_cpl.main)
    check(code == 0, 'every placement lands pad on pad (exit %r)%s' % (code, '' if code == 0 else ': ' + out[-600:]))
    table = {r['LCSC']: r for r in csv.DictReader(open(os.path.join(hw, 'jlcpcb', 'cpl_check.csv')))}
    check(table['C141836']['Rotation offsets that fit (deg)'] == '180', 'SOT-23-5 (C141836): the only rotation offset that fits is 180')
    check(table['C2286']['Rotation offsets that fit (deg)'] == '0', 'LED (C2286) with the pad alias: offset 0 (without it, 180 would seem to fit)')
    check(table['C165948']['Rotation offsets that fit (deg)'] == 'none', 'USB-C: the stock KiCad footprint is %.1f mm off the EasyEDA origin (rev H needs its own copy)' % USB_SHIFT)

    # a bottom angle without the mirror (KiCad angle + correction) is not the convention gen_jlc writes: refused
    p = os.path.join(hw, 'jlcpcb', 'cpl_jlc.csv'); good = open(p).read()
    rows = list(csv.reader(open(p)))
    for r in rows[1:]:
        if r[3] == 'Bottom':
            th = float(b.FindFootprintByReference(r[0]).GetOrientationDegrees())
            r[4] = '%.1f' % ((th + gen_jlc.cpl_correction(D.PARTS[r[0]][3])) % 360)
    with open(p, 'w', newline='') as f: csv.writer(f).writerows(rows)
    code, out = run(check_cpl.main)
    flagged = {ref for ref in D.PARTS if ('FAIL %s (' % ref) in out}
    # at 0 / 180 degrees the two rules differ by 180 degrees: the arrays and the crystal land with their numbers turned
    # (1-5 / 1-3), which check_cpl does not accept from the CPL itself; at 90 / 270 they agree (180 - a = a mod 360);
    # the two-pad R1 / R3 fit either way. (At angles that are not a multiple of 90 they differ by other angles, which
    # is why check_cpl wants bottom-side parts at multiples of 90 degrees.)
    check(code == 1 and flagged == {'RN1', 'RN3', 'Y3'}, 'bottom angles without the mirror are refused where they differ: %s' % sorted(flagged))
    # the other way of turning the board over (+180): JLCPCB's convention is not documented, BOTTOM_OK parts survive it
    for r in rows[1:]:
        if r[3] == 'Bottom':
            th = float(b.FindFootprintByReference(r[0]).GetOrientationDegrees())
            r[4] = '%.1f' % ((-th + gen_jlc.cpl_correction(D.PARTS[r[0]][3])) % 360)
    with open(p, 'w', newline='') as f: csv.writer(f).writerows(rows)
    code, out = run(check_cpl.main)
    check(code == 1 and 'RN1 (' in out and 'Y3 (' in out, 'the angle turned by 180 is refused too (pad numbers): check_cpl wants exactly the convention gen_jlc writes')
    open(p, 'w').write(good)

    # aliases are needed: without them the USB-C and the LEDs do not fit
    keep = dict(check_cpl.PAD_ALIAS); check_cpl.PAD_ALIAS.clear()
    code, out = run(check_cpl.main)
    check(code == 1 and 'J3 (' in out and 'D1 (' in out and 'D2 (' in out, 'without the pad aliases, J3 (USB-C) and D1 / D2 (LED) are refused')
    check_cpl.PAD_ALIAS.update(keep)
    lib = dict(LIB); t, pads = lib['C2286']; lib['C2286'] = (t, [(n, -x, y) for (n, x, y) in pads])    # anode on the other side
    check_cpl.library_pads = lambda code: lib[code]
    code, out = run(check_cpl.main)
    check(code == 1 and 'D1 (' in out, 'an aliased part whose library pads land on the wrong pads is still refused (LED mirrored)')
    check_cpl.library_pads = lambda code: LIB[code]

    print('check_jlc main(): multilayer and two-sided rules')
    code, out = jlc_check(check_jlc)
    fails = [l for l in out.splitlines() if l.startswith('  FAIL')]
    # the fixture is not routed, is small, uses KiCad's stock footprints (0.12 mm silkscreen) and gets rev D's notes text
    expected = ('no tracks', 'open', 'drc_report', '70 x 70', 'silkscreen line', 'track and via counts')
    unexpected = [l for l in fails if not any(e in l for e in expected)]
    check(not unexpected, 'only the expected problems of an unrouted small fixture: %s' % (unexpected[:4] or 'none other'))
    check('copper layers' not in out, 'copper layers: 6 as the design says')
    check('1 holes below 0.30 mm, each with copper >= 0.45 mm across' in out, 'a 0.2 / 0.45 mm via is accepted on a 6-layer board')
    check('15 parts for JLCPCB (6 types), 5 on the top side and 10 on the bottom side' in out, 'parts counted per side')
    check('gerbers.zip: 15 files, each identical to a fresh plot of the board' in out, 'gerbers.zip with In1..In4 is identical to a fresh plot (inner layers plotted too)')
    check('parts_check.csv: 6 part numbers, 2 Basic and 4 Extended as declared' in out, 'parts_check.csv: declared Extended parts are accepted')
    check('plated drill file' not in out, 'plated drill hits = vias + plated pad holes + plated slots (USB-C shell legs: 4 slots)')
    return gen_jlc, check_cpl, check_jlc

def test_refusals(base, D):
    print('refusals: small via, inner pour at the edge, part on the back that BOTTOM_OK does not allow, declared class')
    hw = os.path.join(base, 'hw2')
    D.PARTS['U9'] = ('', '', 'TLV62569DBVR', D.SOT, (20.0, 32.0, 0, 'B'))
    D.PARTS['R9'] = ('', '', '27', D.R0402, (26.0, 32.0, 30, 'B'))       # allowed part, but not at a multiple of 90 degrees
    build_board(hw, D, vias=((30.0, 34.0, 0.5, 0.3), (34.0, 34.0, 0.40, 0.2), (38.0, 34.0, 0.5, 0.15)), edge_pour=True)
    gen_jlc, check_cpl, check_jlc = load(hw)
    code, out = write_package(gen_jlc)
    check(code is not None and 'U9' in str(code), 'gen_jlc.py refuses a bottom-side part that BOTTOM_OK does not allow (%s)' % str(code)[:90])
    D.BOTTOM_OK.add('U')                     # declaring it is not enough: a SOT-23-5 does not turn by 180 degrees without harm
    code, out = write_package(gen_jlc)
    check(code is not None and 'U9' in str(code), 'gen_jlc.py refuses it even when BOTTOM_OK names its prefix (bottom_ok: footprint not in BOTTOM_TURN)')
    D.BOTTOM_OK.discard('U')
    real = gen_jlc.bottom_ok; gen_jlc.bottom_ok = lambda ref, fpname=None: True       # a package written without the rule,
    code, out = write_package(gen_jlc); gen_jlc.bottom_ok = real                    # to see that the checks refuse it on their own
    code, out = run(check_cpl.main)
    check(code == 1 and 'U9: side of the board' in out, 'check_cpl.py refuses U9 on the bottom side')
    check('R9: on the bottom side at 30.0 degrees' in out, 'check_cpl.py refuses a bottom-side part that is not at a multiple of 90 degrees')
    check('FAIL R1' not in out and 'FAIL RN1' not in out and 'FAIL Y1' not in out, 'the allowed bottom-side parts of the same board pass')
    code, out = jlc_check(check_jlc)
    check('U9 is assembled by JLCPCB on the back, but it may not be there' in out, 'check_jlc.py refuses U9 on the back')
    check("CPL layers disagree with the sides of the board or with what may go on the bottom side (BOTTOM_OK, gen_jlc.BOTTOM_TURN): ['U9']" in out, 'check_jlc.py refuses the Bottom row of U9')
    check('2 holes break the multilayer small-hole rule' in out and '0.20 mm needs copper 0.45 mm across, it has 0.40' in out and 'hole 0.15 mm < 0.20' in out,
          'small holes: 0.2 mm with 0.40 mm copper and a 0.15 mm hole are refused')
    check('mm from the left edge <' in out, 'a pour on In3 is measured against the edges')
    rows = list(csv.reader(open(os.path.join(hw, 'jlcpcb', 'parts_check.csv'))))
    rows[1][2] = 'Extended' if rows[1][2] == 'Basic' else 'Basic'
    with open(os.path.join(hw, 'jlcpcb', 'parts_check.csv'), 'w', newline='') as f: csv.writer(f).writerows(rows)
    code, out = jlc_check(check_jlc)
    check('not every part has its declared class' in out, 'check_jlc.py refuses a parts_check.csv row whose class is not the declared one')
    del D.PARTS['U9'], D.PARTS['R9']

def test_old_designs(base, D):
    print('designs without the new attributes keep the old rules')
    hw = os.path.join(base, 'hw')
    keep = {k: getattr(D, k) for k in ('ASSEMBLY', 'LCSC_CLASS', 'LAYERS')}
    for k in keep: delattr(D, k)
    gen_jlc, check_cpl, check_jlc = load(hw)
    rows = {r[0]: r for r in gen_jlc.cpl_table([])[1:]}
    import pcbnew
    b = pcbnew.LoadBoard(os.path.join(hw, 'famicart.kicad_pcb'))
    check(all(abs(float(rows[r][4]) - b.FindFootprintByReference(r).GetOrientationDegrees() % 360) < 0.05 or abs(float(rows[r][4]) - b.FindFootprintByReference(r).GetOrientationDegrees()) < 0.05
              for r in rows if rows[r][3] == 'Bottom'), 'bottom rows keep the KiCad angle (as rev B-D)')
    check(float(rows['U1'][4]) == 0.0, 'SOT-23-5 on the top keeps the KiCad angle without LCSC_CLASS')
    check(check_jlc.NL == 2 and check_jlc.CU_NAMES == 'F.Cu,B.Cu' and not check_jlc.TWO_SIDED, 'check_jlc: 2 layers (no LAYERS), F.Cu and B.Cu only, one side')
    D.LAYERS = 6; D.JLC_RULES = False; check_jlc = importlib.reload(check_jlc)
    check(check_jlc.NL == 2, 'check_jlc: a 6-layer design without JLC_RULES (rev D) is checked as before (2 layers expected)')
    D.JLC_RULES = True
    for k, v in keep.items(): setattr(D, k, v)

def test_bottom_rule(base, D):
    print('bottom side: only footprints whose 180-degree turn is harmless, whatever BOTTOM_OK declares')
    gen_jlc, check_cpl, check_jlc = load(os.path.join(base, 'hw'))
    keep = set(D.BOTTOM_OK); D.BOTTOM_OK.update({'D', 'C', 'Y', 'U', 'Q'})
    ok = {'Resistor_SMD:R_0402_1005Metric': 'R7', 'Capacitor_SMD:C_0603_1608Metric': 'C7', 'Capacitor_SMD:C_1206_3216Metric': 'C8',
          'Resistor_SMD:R_0201_0603Metric': 'R8', 'Resistor_SMD:R_Array_Convex_4x0603': 'RN7', 'Resistor_SMD:R_Array_Convex_4x0402': 'RN8',
          'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm': 'Y7'}
    no = {'LED_SMD:LED_0603_1608Metric': 'D7', 'Diode_SMD:D_SOD-123': 'D8', 'Capacitor_Tantalum_SMD:CP_EIA-3216-18_Kemet-A': 'C9',
          'Package_TO_SOT_SMD:SOT-23': 'Q7', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm_HandSoldering': 'Y8', 'Capacitor_SMD:C_1210_3225Metric': 'C10',
          'Package_TO_SOT_SMD:SOT-23-5': 'U7'}
    check(all(gen_jlc.bottom_ok(r, fp) for fp, r in ok.items()), 'bottom_ok: R / C 0201-1206, the 4x0603 / 4x0402 arrays and the 3225 crystal when declared')
    check(not any(gen_jlc.bottom_ok(r, fp) for fp, r in no.items()), 'bottom_ok refuses LEDs, diodes, tantalum capacitors, SOT-23, other crystals, 1210, SOT-23-5 although declared')
    D.BOTTOM_OK.clear(); D.BOTTOM_OK.update(keep)
    check(not gen_jlc.bottom_ok('D7', 'Resistor_SMD:R_0402_1005Metric'), 'bottom_ok: a safe footprint that BOTTOM_OK does not declare is refused')
    keep_attr = D.BOTTOM_OK; D.BOTTOM_OK = 'RN'
    check(gen_jlc.bottom_ok('RN1') and not gen_jlc.bottom_ok('R1'), "BOTTOM_OK = 'RN' (a string) is one entry: RN1 allowed, R1 not ('R' is not taken as a letter of it)")
    D.BOTTOM_OK = keep_attr
    maps = {'Resistor_SMD:R_0402_1005Metric': {'1': '2', '2': '1'}, 'Resistor_SMD:R_Array_Convex_4x0603': {'1': '5', '2': '6', '3': '7', '4': '8', '5': '1', '6': '2', '7': '3', '8': '4'},
            'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm': {'1': '3', '2': '4', '3': '1', '4': '2'}}
    check(all(gen_jlc.bottom_turn(fp) == m for fp, m in maps.items()), 'BOTTOM_TURN pad maps: R 1<->2, array k<->k+4, crystal 1<->3 2<->4')
    # each map against the KiCad footprint itself: turned by 180 degrees every pad lands on its partner
    import math
    good = True
    for fp, m in maps.items():
        pads = check_cpl.kicad_pads(fp)
        for (n, x, y) in pads:
            q = min(pads, key=lambda p: math.hypot(p[1] + x, p[2] + y)); good &= q[0] == m[n] and math.hypot(q[1] + x, q[2] + y) < 1e-6
    check(good, 'the BOTTOM_TURN maps are the 180-degree pad maps of the KiCad footprints')
    # land_turned: the second reading must land on the 180-degree partners, not just on some pads
    xt = [(n, x, y) for (n, x, y) in check_cpl.kicad_pads('Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')]
    turned = [(n, -x, -y) for (n, x, y) in xt]; mirrored = [(n, -x, y) for (n, x, y) in xt]
    check(check_cpl.land_turned(xt, turned, xt, maps['Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm'])[1], 'land_turned: a crystal turned by 180 degrees lands on its partners (1-3, 2-4)')
    check(not check_cpl.land_turned(xt, mirrored, xt, maps['Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm'])[1], 'land_turned: pads that land on other pads (1-2, 3-4: the crystal across its case pins) are refused')
    check(not check_cpl.land_turned(xt, turned, xt, None)[1], 'land_turned: a footprint without a 180-degree map is refused')

    print('an LED declared for the bottom side is refused by gen_jlc, check_cpl and check_jlc')
    hw = os.path.join(base, 'hw_led')
    D.PARTS['D3'] = ('', '', 'red LED', D.LED, (44.0, 32.0, 0, 'B')); D.PARTS['D4'] = ('', '', 'red LED', D.LED, (48.0, 32.0, 90, 'B'))
    D.BOTTOM_OK.add('D')
    build_board(hw, D)
    gen_jlc, check_cpl, check_jlc = load(hw)
    code, out = write_package(gen_jlc)
    check(code is not None and 'D3' in str(code) and 'D4' in str(code), 'gen_jlc.py refuses the LEDs on the bottom side although BOTTOM_OK names D (%s)' % str(code)[:80])
    real = gen_jlc.bottom_ok; gen_jlc.bottom_ok = lambda ref, fpname=None: True
    code, out = write_package(gen_jlc); gen_jlc.bottom_ok = real
    code, out = run(check_cpl.main)
    check(code == 1 and 'D3: side of the board' in out and 'D4: side of the board' in out, 'check_cpl.py refuses D3 / D4 on the bottom side')
    code, out = jlc_check(check_jlc)
    check('D3 is assembled by JLCPCB on the back, but it may not be there' in out and 'D4 is assembled by JLCPCB on the back' in out, 'check_jlc.py refuses D3 / D4 on the back')
    check("['D3', 'D4']" in out and 'CPL layers disagree' in out, 'check_jlc.py refuses their Bottom rows')
    D.BOTTOM_OK.discard('D'); del D.PARTS['D3'], D.PARTS['D4']

def test_eight_layers(base, D):
    print('8 layers (the fallback of docs/13): In1..In6 in gerbers.zip, the fresh plot and the layer count')
    hw = os.path.join(base, 'hw8'); D.LAYERS = 8
    try:
        build_board(hw, D, layers=8)
        gen_jlc, check_cpl, check_jlc = load(hw)
        check(all(('In%d_Cu.g%d' % (k, k + 1)).endswith(gen_jlc.FAB_SUFFIX) for k in range(1, 7)), 'FAB_SUFFIX covers In1..In6 (.g2 .. .g7)')
        code, out = write_package(gen_jlc)
        check(code is None, 'gen_jlc.py writes the package of an 8-layer board (exit %r)%s' % (code, '' if code is None else ': ' + out[-200:]))
        import zipfile
        names = zipfile.ZipFile(os.path.join(hw, 'jlcpcb', 'gerbers.zip')).namelist()
        check(all(any(n.endswith('In%d_Cu.g%d' % (k, k + 1)) for n in names) for k in range(1, 7)), 'gerbers.zip carries In1..In6')
        code, out = jlc_check(check_jlc)
        check('copper layers' not in out and check_jlc.NL == 8, 'check_jlc: 8 copper layers as the design says')
        check('gerbers.zip: %d files, each identical to a fresh plot of the board' % len(names) in out, 'gerbers.zip with In1..In6 is identical to a fresh plot (%d files)' % len(names))
    finally:
        D.LAYERS = 6

def test_small_holes_without_vias(base, D):
    print('multilayer small-hole rule on a board without vias (plated pad holes)')
    hw = os.path.join(base, 'hw_novia')
    build_board(hw, D, vias=(), pth=(44.0, 34.0, 0.40, 0.20))
    gen_jlc, check_cpl, check_jlc = load(hw)
    write_package(gen_jlc)
    code, out = jlc_check(check_jlc)
    check('1 holes break the multilayer small-hole rule' in out and 'pad TP1.1: hole 0.20 mm needs copper 0.45 mm across, it has 0.40' in out,
          'a 0.20 mm plated pad hole with 0.40 mm copper is refused although the board has no via')

def test_stock_for_order(hw, D):
    print('check_jlc.py recomputes the stock needed for FC_PCBA_QTY boards from parts_check.csv')
    gen_jlc, check_cpl, check_jlc = load(hw)
    write_package(gen_jlc)
    p = os.path.join(hw, 'jlcpcb', 'parts_check.csv'); rows = list(csv.DictReader(open(p))); fields = list(rows[0].keys())
    r = next(r for r in rows if r['LCSC'] == 'C20197'); need2 = int(r['Per board']) * 2 + int(r['Loss'])
    r['Stock'], r['Can presale'] = str(3 * need2), str(need2)            # enough for 2 boards, not for 5
    with open(p, 'w', newline='') as f: w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    os.environ['FC_PCBA_QTY'] = '2'
    try: code, out = jlc_check(check_jlc)
    finally: os.environ.pop('FC_PCBA_QTY', None)
    check('not enough stock' not in out and 'can presale >= need for 2 boards' in out, 'FC_PCBA_QTY=2: stock for 2 boards is enough')
    code, out = jlc_check(check_jlc)
    check("not enough stock for 5 boards" in out and 'C20197: need %d' % (int(r['Per board']) * 5 + int(r['Loss'])) in out, 'default 5 boards: the same rows are refused (stock for 2 boards only)')

def test_usb_footprint(base):
    print('the USB-C footprint of famicart.pretty against JLCPCB\'s library footprint (recorded pads)')
    gen_jlc, check_cpl, check_jlc = load(os.path.join(base, 'hw'))
    kp = check_cpl.kicad_pads('famicart:USB_C_Receptacle_HRO_TYPE-C-31-M-12_JLC')
    fit = check_cpl.fits_alias(EASYEDA['C165948'][1], kp, check_cpl.PAD_ALIAS['C165948'], False)
    check(list(fit) == [0] and fit[0][1] == 'same numbers' and fit[0][0] < 0.2, 'USB_C_..._JLC fits C165948 at 0 degrees only, same numbers, worst %.3f mm (HRO land vs EasyEDA pads)' % fit.get(0, (9,))[0])

def test_handover(base, D):
    print('hand-over of a design with declared classes: gen_bom, part_map, README_H, gen_order')
    hw = os.path.join(base, 'hw')
    gen_jlc, check_cpl, check_jlc = load(hw)
    pm = gen_jlc.part_map()
    check(pm['TLV62569DBVR'][2] == 'JLCPCB Extended' and pm['1k x4'][2] == 'JLCPCB Basic', 'part_map labels each part with its declared class')
    env = dict(os.environ, FC_DESIGN='design_selftest', FC_HW_DIR=hw, PYTHONPATH=os.pathsep.join(sys.path))
    subprocess.run([sys.executable, os.path.join(TOOLS, 'gen_bom.py')], env=env, check=True, capture_output=True)
    bom = {r['Value']: r['Suggested part'] for r in csv.DictReader(open(os.path.join(hw, 'bom.csv')))}
    check(bom['TLV62569DBVR'].endswith('JLCPCB Extended)') and bom['1k x4'].endswith('JLCPCB Basic)'), 'gen_bom.py: bom.csv names the declared class (%s / %s)' % (bom['TLV62569DBVR'], bom['1k x4']))
    keep_rev = D.REV; D.REV = 'rev H'
    D.RAILS = dict(width=5.0, gap=2.0, tab=5.2, hole=0.6, hole_out=0.3, pitch=0.9, holes=7, end_gap=2.7, tabs={'L': (8.0, 30.0), 'R': (8.0, 30.0)},
                   top=dict(tabs=(12.0, 48.0)), fiducials=(('T', 3.85), ('T', -3.85), ('L', -3.85)), fid_inset=3.85, tooling=(('T', 14.0), ('T', -14.0)), tooling_d=2.0)
    try:
        gen_jlc, check_cpl, check_jlc = load(hw)
        code, out = write_package(gen_jlc)
        check(code is None, 'gen_jlc.py writes the rev H notes (README_H) without a placeholder left (exit %r)%s' % (code, '' if code is None else ': ' + str(code)[:200]))
        notes = open(os.path.join(hw, 'jlcpcb', 'README.md')).read()
        bom_, dnp, placed, ntypes = gen_jlc.bom_table(warn=False)
        import pcbnew
        b = pcbnew.LoadBoard(os.path.join(hw, 'famicart.kicad_pcb'))
        joints = sum(len(list(fp.Pads())) for fp in b.GetFootprints() if fp.GetReference() in placed)
        e2, e5 = (gen_jlc.assembly_estimate(ntypes, joints, n, gen_jlc.xray_count(placed), 2) for n in (2, 5))
        check('| 実装費（Standard・両面、X 線検査込み） | 約 US$ %.0f | 約 US$ %.0f |' % (e2, e5) in notes, 'README_H: @EST2@ / @EST5@ are the two-sided estimates ($%.0f / $%.0f)' % (e2, e5))
        check('Basic 2 行・Extended 5 行（Extended は設計が宣言した 4 品番だけ: C141836 TLV62569DBVR、C165948 TYPE-C-31-M-12、C25100 27R 0402、C362368 TXM12M0004322CBCDO00T）' in notes,
              'README_H: the parts list state with the declared Extended codes')
        settings = ('FR-4 / **6**', '**JLC06121H-3313**', '**0.5 oz**', '**0.3mm/(0.4/0.45mm)**', '**Epoxy Filled & Capped**', 'Beveling **30°**', '**Panel by Customer**',
                    'left, right\n> and top edges', '**Both Sides**', '**Yes**（QFN などの見えない接合', 'RP2350B（C42415655）は 1 品番だけで在庫が薄い', '74.0 × 47.0 mm')
        check(all(s in notes for s in settings), 'README_H: 6 layers, JLC06121H-3313, inner 0.5 oz, min via kept, epoxy filled & capped, 30 deg, panel with three rails, both sides, X-ray, RP2350B, panel size (missing: %s)'
              % [s for s in settings if s not in notes])
        sys.modules.pop('gen_order', None); os.environ['FC_HW_DIR'] = hw
        import gen_order
        code, out = run(gen_order.main)
        check(code is None, 'gen_order.py writes the hand-over of the declared design (exit %r)%s' % (code, '' if code is None else ': ' + str(code)[:200]))
        g = open(os.path.join(hw, 'order', 'grokbot_instructions.md')).read()
        check('Basic 2 行・Extended 5 行（宣言済みの Extended は 4 品番' in g and 'すべて Basic' not in g, 'gen_order: "Basic n, Extended m (declared)", not "all Basic"')
        check('**宣言済みの一覧に無い Extended の行、在庫が足りない行（2 枚分に足りない、または在庫切れ）、不一致、未選択があれば止まって確認。**' in g
              and '宣言済みの Extended 4 品番の行は止まる理由にならない' in g, 'gen_order: stops on undeclared Extended rows or short stock only')
        check(not os.path.exists(os.path.join(hw, 'order', 'akizuki_parts.csv')) and '**Both Sides**' in g and '**6**' in g, 'gen_order: no Akizuki list, both sides, 6 layers')
        check(open(os.path.join(hw, 'order', 'jlcpcb_pcb_remark.txt')).read().count('\n') == 6, 'gen_order: the PCB remark of README_H (6 points)')
    finally:
        D.REV = keep_rev; del D.RAILS; sys.modules.pop('gen_order', None)

def fetch_live(check_cpl):
    """--online: the EasyEDA footprints of the fixture's parts, downloaded once (spaced: EasyEDA refuses bursts), must
    be the recorded tables; the checks then use the live data."""
    print('online: EasyEDA footprints')
    import time
    for code, (title, pads) in EASYEDA.items():
        t, live = check_cpl.library_pads(code); time.sleep(4)
        same = t == title and len(live) == len(pads) and all(any(n == m and abs(x - a) < 0.002 and abs(y - c) < 0.002 for (m, a, c) in live) for (n, x, y) in pads)
        check(same, '%s: the recorded pad table is the live EasyEDA footprint %s' % (code, t))
        LIB[code] = (t, live)

def test_online(gen_jlc):
    print('online: classes of the rev H parts in the JLCPCB catalogue')
    revh = {'C42415655': 'Extended', 'C362368': 'Extended', 'C141836': 'Extended', 'C135262': 'Extended', 'C165948': 'Extended',
            'C25100': 'Extended', 'C91145': 'Extended', 'C2286': 'Basic', 'C97521': 'Basic', 'C1525': 'Basic'}
    for code, cls in revh.items():
        it, err = gen_jlc.lookup(code)
        got = gen_jlc.API_CLASS.get((it or {}).get('componentLibraryType'), '?')
        check(got == cls, '%s is %s in the catalogue (stock %s, can presale %s, loss %s)' % (code, cls, (it or {}).get('stockCount'), (it or {}).get('canPresaleNumber'), (it or {}).get('lossNumber')))

def main():
    base = tempfile.mkdtemp(prefix='parts_checks_test_')
    try:
        dd = os.path.join(base, 'designs'); os.makedirs(dd)
        open(os.path.join(dd, 'design_selftest.py'), 'w').write(DESIGN)
        sys.path.insert(0, dd); sys.path.insert(0, TOOLS)
        os.environ['FC_DESIGN'] = 'design_selftest'; os.environ['FC_ALLOW_UNROUTED'] = '1'
        D = importlib.import_module('design_selftest')
        hw = os.path.join(base, 'hw'); build_board(hw, D)
        gen_jlc, check_cpl, check_jlc = load(hw)
        if ONLINE: fetch_live(importlib.reload(check_cpl))
        os.makedirs(gen_jlc.OUT, exist_ok=True)
        test_estimate(gen_jlc, D)
        test_declared(gen_jlc, D, hw)
        test_cpl_rot(gen_jlc, D)
        gen_jlc, check_cpl, check_jlc = test_package(hw, D)
        test_refusals(base, D)
        test_bottom_rule(base, D)
        test_eight_layers(base, D)
        test_small_holes_without_vias(base, D)
        test_stock_for_order(hw, D)
        test_usb_footprint(base)
        test_handover(base, D)
        test_old_designs(base, D)
        if ONLINE: test_online(load(hw)[0])
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print('%d passed, %d failed' % (passed[0], len(failures)))
    for f in failures: print('  FAILED:', f)
    sys.exit(1 if failures else 0)

if __name__ == '__main__':
    main()
