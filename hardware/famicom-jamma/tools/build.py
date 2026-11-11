#!/usr/bin/env python3
"""Build the KiCad project from the circuit description and check it.

Run with the project's Python environment (see tools/setup_env.sh):
    /opt/fcjamma-venv/bin/python tools/build.py

Steps
 1. load design/circuit.py
 2. check the parts rule: every part that JLCPCB assembles is in its parts library (Basic parts
    against data/jlcpcb_basic_parts_*.csv, Extended parts against data/jlcpcb_extended_parts.csv,
    which tools/jlc_parts.py refreshes), is the part the circuit means, can be assembled on a
    Standard PCBA order and is in stock
 3. check that every standard footprint exists in the KiCad library, has a pad for every pin of
    its symbol and is the package JLCPCB supplies; check the board's own design rules and the
    datasheet facts written down in design/circuit.py (selfcheck)
 4. write kicad/ (symbol library, schematic sheets, project file)
 5. kicad-cli: upgrade to the KiCad 10 format, ERC, netlist, PDF
 6. compare KiCad's netlist with the model, pin by pin
 7. write out/ (BOM with sourcing, net list, reports, cost estimate)
"""
import csv
import datetime
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "design"))

from fcgen import kicad_out, parts as P          # noqa: E402
from fcgen.model import SymDef, JLC, JLCX, AKI, DONOR, PCB   # noqa: E402

KICAD_FP = "/usr/share/kicad/footprints"
KICAD_TEMPLATE = "/usr/share/kicad/template"
CFG = os.environ.get("FCJAMMA_KICAD_CONFIG", "/tmp/fcjamma-kicad-config")


def kicad_env():
    d = os.path.join(CFG, "10.0")
    os.makedirs(d, exist_ok=True)
    for t in ("sym-lib-table", "fp-lib-table"):
        if not os.path.exists(os.path.join(d, t)):
            shutil.copy(os.path.join(KICAD_TEMPLATE, t), d)
    env = dict(os.environ)
    env["KICAD_CONFIG_HOME"] = CFG
    return env


def run(cmd, env, cwd):
    r = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def load_basic():
    rows = {}
    with open(os.path.join(ROOT, "data", "jlcpcb_basic_parts_2026-11-10.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["lcsc"]] = r
    return rows


def load_extended():
    rows = {}
    path = os.path.join(ROOT, "data", "jlcpcb_extended_parts.csv")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["lcsc"]] = r
    return rows


MIN_BOARDS, COMFORT_BOARDS = 5, 20      # stock must cover the smallest order; below the second figure the build warns


def per_board(design):
    """LCSC number -> pieces on one board (fitted parts and the extra items)."""
    need = {}
    for p in design.parts.values():
        if p.src in (JLC, JLCX) and not p.dnp:
            need[p.code] = need.get(p.code, 0) + 1
    for src, code, _value, qty, _note, _refs in design.extras:
        if src in (JLC, JLCX):
            need[code] = need.get(code, 0) + qty
    return need


def check_rule(design, problems, warnings):
    basic, ext = load_basic(), load_extended()
    need = per_board(design)
    for code, text in P.USED_CODES.items():
        row = basic.get(code)
        if row is None:
            problems.append(f"parts rule: {code} is not in the JLCPCB Basic list")
            continue
        hay = (row["description"] + " " + row["mpn"]).replace(" ", "")
        if text.replace(" ", "") not in hay:
            problems.append(f"parts rule: {code} is '{row['mpn']} / {row['description'][:60]}', expected to contain '{text}'")
    for code, (text, package) in P.USED_EXT.items():
        row = ext.get(code)
        if row is None:
            problems.append(f"parts rule: {code} is not in data/jlcpcb_extended_parts.csv; run tools/jlc_parts.py")
            continue
        if text not in row["mpn"]:
            problems.append(f"parts rule: {code} is '{row['mpn']}', expected to contain '{text}'")
        if package and package not in row["package"]:
            problems.append(f"parts rule: {code} ({row['mpn']}) comes in '{row['package']}', the circuit expects '{package}'")
        if "Standard" not in row["pcba_type"]:
            problems.append(f"parts rule: {code} ({row['mpn']}) cannot be assembled on a Standard PCBA order ('{row['pcba_type']}')")
        if not row["assembly_type"]:
            problems.append(f"parts rule: {code} ({row['mpn']}): JLCPCB's page does not say how the part is assembled")
        stock, n = int(row["stock"] or 0), need.get(code, 0)
        if stock < n * MIN_BOARDS:
            problems.append(f"parts rule: {code} ({row['mpn']}): stock {stock} on {row['checked']} does not cover {MIN_BOARDS} boards ({n} per board)")
        elif stock < n * COMFORT_BOARDS:
            warnings.append(f"{code} ({row['mpn']}): stock {stock} on {row['checked']} covers only {stock // n} boards ({n} per board)")
    for p in design.parts.values():
        if p.src == JLC and p.code not in basic:
            problems.append(f"parts rule: {p.ref} ({p.value}) uses {p.code or 'no LCSC number'}, which is not Basic")
        if p.src == JLCX and p.code not in P.USED_EXT:
            problems.append(f"parts rule: {p.ref} ({p.value}) uses {p.code or 'no LCSC number'}, which is not in the table of Extended parts")
        if p.src == AKI and not p.dnp:
            problems.append(f"parts rule: {p.ref} ({p.value}) would have to be soldered by hand; every fitted part must be assembled by JLCPCB")
    for src, code, value, _qty, _note, _refs in design.extras:
        if src not in (JLC, JLCX) or code not in (set(P.USED_CODES) | set(P.USED_EXT)):
            problems.append(f"parts rule: extra item '{value}' is not a JLCPCB part of the tables")


# KiCad footprint (name, or the start of the name when it ends with "_") -> text of JLCPCB's package column, and whether
# the package column must be exactly that text.  A part on the wrong footprint passes every netlist check, hence this table.
PACKAGE_OF_FOOTPRINT = [
    ("R_0603_", "0603", True), ("C_0603_", "0603", True), ("L_0603_", "0603", True), ("LED_0603_", "0603", True),
    ("R_Array_Convex_4x0603", "0603x4", True), ("D_SMA", "SMA", False), ("D_SMB", "SMB", False),
    ("SOT-23", "SOT-23", True), ("SOT-23-5", "SOT-23-5", True), ("SOT-23-6", "SOT-23-6", True), ("SOT-223-3_TabPin2", "SOT-223", True),
    ("SOIC-8_", "SOIC-8", True), ("SOIC-14_", "SOIC-14", True), ("SOIC-16_", "SOIC-16", True), ("SOIC-20W_", "SOIC-20", True),
    ("MSOP-8_", "MSOP-8", True), ("TSOP-I-28_", "TSOPI-28", True),
    ("CP_EIA-3216-18_", "3216", False), ("CP_EIA-3528-21_", "3528", False), ("CP_Elec_6.3x7.7", "6.3", False), ("Fuse_2920_", "2920", True),
]


def expected_package(fp_name):
    for key, text, exact in PACKAGE_OF_FOOTPRINT:
        if fp_name == key or (key.endswith("_") and fp_name.startswith(key)):
            return text, exact
    return None, False


def check_footprints(design, problems, custom):
    """Every standard footprint exists, has a pad for every pin of its symbol, and is the package JLCPCB supplies."""
    basic, ext = load_basic(), load_extended()
    pads_of = {}
    for p in design.parts.values():
        if not p.footprint:
            problems.append(f"footprint: {p.ref} has none")
            continue
        lib, name = p.footprint.split(":")
        if lib == "fcjamma":
            custom.add(p.footprint)
            continue
        path = os.path.join(KICAD_FP, f"{lib}.pretty", f"{name}.kicad_mod")
        if not os.path.exists(path):
            problems.append(f"footprint: {p.ref} -> {p.footprint} not found in the KiCad library")
            continue
        if path not in pads_of:
            pads_of[path] = set(re.findall(r'\(pad "([^"]*)"', open(path, encoding="utf-8").read()))
        missing = sorted(n for n in p.conn if n not in pads_of[path])
        if missing:
            problems.append(f"footprint: {p.ref} ({p.value}) has pins {missing} that {name} has no pad for")
        row = basic.get(p.code) or ext.get(p.code)
        text, exact = expected_package(name)
        if row and text and not p.dnp:
            package = row["package"]
            if (package != text) if exact else (text not in package):
                problems.append(f"footprint: {p.ref} ({p.value}) sits on {name}, but JLCPCB supplies {p.code} in '{package}'")


PASSIVE_LIBS = ("Device:R", "Device:C", "Device:C_Polarized", "Device:R_Pack04", "Device:FerriteBead", "Device:R_Potentiometer_Trim",
                "Connector:TestPoint", "Connector_Generic:", "Switch:", "Jumper:")
RAILS_5V = ("+5V", "+5V_SW", "+5V_IN")
UNIFORM_BUSES = ("CD", "PPD", "CART_D", "PD", "DQ_PA", "DQ_D", "DI_CD", "DI_PD", "B_CD", "B_OVR")


def check_design_rules(design, problems):
    """Electrical rules of this board that can be checked from the netlist alone."""
    import collections

    def pin_name(part, num):
        if isinstance(part.sym, SymDef):
            return next(x[1] for x in part.sym.pins() if str(x[0]) == num)
        return ""

    def pin_type(part, num):
        if isinstance(part.sym, SymDef):
            return next(x[2] for x in part.sym.pins() if str(x[0]) == num)
        return ""

    def supply(part):
        if not isinstance(part.sym, SymDef):
            return None
        for num, net in part.conn.items():
            if pin_name(part, num) in ("VCC", "VDD", "V+", "VSYS", "IN"):
                return net
        return None

    def passive(part):
        return (not isinstance(part.sym, SymDef)) and part.lib_id.startswith(PASSIVE_LIBS)

    def is_pico(part):
        return isinstance(part.sym, SymDef) and part.sym.name == "PICO2"

    nets = design.nets()

    # 0. a net with a single pin is a typing mistake in a net name
    for net, pins in sorted(nets.items()):
        if len(pins) == 1:
            problems.append(f"design rule: net {net} has a single pin ({pins[0][0]}.{pins[0][1]}); check the spelling of the net name")

    # 1. a part outside the 3.3 V domain reaches a Pico GPIO only through a resistor.
    #    Pads 1 and 2 of a solder jumper that is made closed count as one net.
    joined = {}
    for part in design.parts.values():
        if part.lib_id == "Jumper:SolderJumper_3_Bridged12":
            a, b = part.conn["1"], part.conn["2"]
            group = joined.get(a, {a}) | joined.get(b, {b})
            for n in group:
                joined[n] = group
    done = set()
    for net in nets:
        group = frozenset(joined.get(net, {net}))
        if group in done:
            continue
        done.add(group)
        pins = [x for n in group for x in nets[n]]
        gp = [pin_name(design.parts[r], n) for r, n in pins if is_pico(design.parts[r]) and pin_name(design.parts[r], n).startswith("GP")]
        if not gp:
            continue
        for r, n in pins:
            part = design.parts[r]
            if is_pico(part) or passive(part) or supply(part) in ("+3V3", "VSYS"):
                continue
            problems.append(f"design rule: net {'/'.join(sorted(group))} joins Pico pin {'/'.join(gp)} directly to {r}.{n} "
                            f"({pin_name(part, n)}), a part outside the 3.3 V domain")

    # 2. every IC has its own 100 nF capacitor between its supply net and ground
    caps = collections.defaultdict(list)
    for part in design.parts.values():
        if part.at:
            if part.at not in design.parts:
                problems.append(f"design rule: capacitor {part.ref} is marked for {part.at}, which does not exist")
            caps[part.at].append(part)
    for part in design.parts.values():
        if isinstance(part.sym, SymDef) and part.ref.startswith("U") and part.sym.name not in ("PICO2", "CJ431"):
            rail = supply(part)
            own = [c for c in caps.get(part.ref, []) if c.value == "100n" and not c.dnp and {c.conn.get("1"), c.conn.get("2")} == {rail, "GND"}]
            if not own:
                problems.append(f"design rule: {part.ref} ({part.value}) has no 100 nF capacitor of its own between {rail} and GND")

    # 3. every bit of a bus has the same kinds of connections as its neighbours, and no bit is missing
    fam = collections.defaultdict(dict)
    for net, pins in nets.items():
        m = re.fullmatch(r"([A-Z_]+?)(\d+)", net)
        if m and m.group(1) in UNIFORM_BUSES:
            fam[m.group(1)][int(m.group(2))] = sorted(re.sub(r"\d+$", "", r) + ":" + type(design.parts[r].sym).__name__ for r, _ in pins)
    for name in UNIFORM_BUSES:
        bits_ = fam.get(name, {})
        if not bits_:
            problems.append(f"design rule: bus {name} is missing")
            continue
        gaps = sorted(set(range(max(bits_) + 1)) - set(bits_))
        if gaps:
            problems.append(f"design rule: bus {name} has no bit {gaps}")
        shapes = collections.Counter(tuple(v) for v in bits_.values())
        # PA8-13 come from another register than PA0-7, but through the same kind of parts, so one shape is expected everywhere
        if len(shapes) > 1:
            common = shapes.most_common(1)[0][0]
            odd = [f"{name}{i}" for i, v in sorted(bits_.items()) if tuple(v) != common]
            problems.append(f"design rule: bus {name} is not uniform; check {odd}")

    # 4. no net carries two outputs of the same IC
    for net, pins in nets.items():
        outs = collections.Counter(r for r, n in pins if pin_type(design.parts[r], n) in ("out", "tri"))
        for r, count in outs.items():
            if count > 1:
                problems.append(f"design rule: net {net} carries {count} outputs of {r}")

    # 5. GP26-GP28 never tolerate 5 V: a resistor from such a pin to anything that can carry 5 V needs a second resistor to ground
    def can_carry_5v(net):
        if net in RAILS_5V:
            return True
        for r, n in nets.get(net, []):
            part = design.parts[r]
            if part.src == DONOR and pin_type(part, n) != "in":
                return True
            if isinstance(part.sym, SymDef) and part.sym.name == "FC_CART60":
                return True
            if supply(part) in RAILS_5V and pin_type(part, n) in ("out", "tri", "bi", "oc"):
                return True
        return False

    for part in design.parts.values():
        if not is_pico(part):
            continue
        for num, net in part.conn.items():
            if pin_name(part, num) not in ("GP26", "GP27", "GP28") or net is None:
                continue
            far = []
            for r, n in nets[net]:
                other = design.parts[r]
                if other.lib_id in ("Device:R", "Device:R_Pack04"):
                    if other.lib_id == "Device:R":
                        far.append(other.conn["2" if n == "1" else "1"])
                    else:
                        far.append(other.conn[str(9 - int(n))])
            hot = [f for f in far if f and can_carry_5v(f)]
            if hot and "GND" not in far:
                problems.append(f"design rule: {part.ref} {pin_name(part, num)} (net {net}) reaches {hot[0]}, which can carry 5 V, "
                                "through a resistor but has no resistor to ground")


UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def stable_uuids(files):
    """Replace the random identifiers by ones derived from their order, so that a rebuild gives the same files."""
    import uuid
    ns = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
    texts = {f: open(f, encoding="utf-8").read() for f in sorted(files)}
    mapping = {}
    for f in sorted(files):
        for u in UUID_RE.findall(texts[f]):
            if u not in mapping:
                mapping[u] = str(uuid.uuid5(ns, f"fcjamma-{len(mapping)}"))
    for f, text in texts.items():
        open(f, "w", encoding="utf-8").write(UUID_RE.sub(lambda m: mapping[m.group(0)], text))


def parse_netlist(path):
    t = open(path, encoding="utf-8").read()
    nets = {}
    for m in re.finditer(r'\(net\s+\(code "?\d+"?\)\s+\(name "([^"]*)"\)(.*?)\n\t\t\)', t, re.S):
        nets[m.group(1)] = set(re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', m.group(2)))
    comps = re.findall(r'\(comp\s+\(ref "([^"]+)"\)', t)
    return nets, comps


def compare(design, kicad_nets, kicad_comps, problems):
    model = {n: set(v) for n, v in design.nets().items()}
    refs = set(design.parts)
    if set(kicad_comps) != refs:
        problems.append(f"netlist: components differ: only in model {sorted(refs - set(kicad_comps))[:10]}, only in KiCad {sorted(set(kicad_comps) - refs)[:10]}")
    for n, pins in model.items():
        k = kicad_nets.get(n) or kicad_nets.get("/" + n)
        if k is None:
            problems.append(f"netlist: net {n} missing in KiCad's netlist")
        elif k != pins:
            problems.append(f"netlist: net {n} differs: model-only {sorted(pins - k)[:6]}, KiCad-only {sorted(k - pins)[:6]}")
    extra = [n for n in kicad_nets if not n.startswith("unconnected-") and n.lstrip("/") not in model]
    if extra:
        problems.append(f"netlist: nets only in KiCad: {extra[:10]}")


def unit_price(row, pieces):
    """Price of one piece when `pieces` are bought (Basic list: one price; Extended list: three price breaks)."""
    if "unit_price_usd_qty1" in row:
        return float(row["unit_price_usd_qty1"] or 0)
    key = "price_100" if pieces >= 100 else "price_10" if pieces >= 10 else "price_1"
    return float(row.get(key) or row.get("price_1") or 0)


# JLCPCB's fees for a Standard PCBA order, single-sided, in USD.
# Source: https://jlcpcb.com/help/article/pcb-assembly-price ("Last updated on Oct 22, 2026"), read on 2026-11-11.
FEES = {"setup": 25.56, "stencil": 8.21, "loading per kind of SMT part": 1.53, "SMT joint": 0.0016, "hand-soldered joint": 0.0164,
        "hand-soldering labour per order": 3.58, "packing": 0.50, "confirm parts placement": 0.45}
XRAY = [(10, 1.64), (50, 0.82), (200, 0.49), (500, 0.33), (1000, 0.25), (3000, 0.16), (99999, 0.082)]   # up to n pieces: USD each
NOT_COUNTED = ("the bare boards, shipping and import tax; a soldering fixture (16.42 USD per order) and placing the Pico modules by hand "
               "(0.016 USD per joint, about 2.35 USD per board) if JLCPCB charges them; the spare pieces JLCPCB bills for losses")


def cost(design, boards):
    """Parts and assembly cost of one board when `boards` are ordered, from the data files and the fee table above."""
    basic, ext = load_basic(), load_extended()
    need = per_board(design)
    parts = sum(n * unit_price(basic.get(code) or ext.get(code) or {"price_1": 0}, n * boards) for code, n in need.items())
    tht = {code for code in need if (ext.get(code) or {}).get("assembly_type", "").startswith("Wave")}   # inserted and soldered by hand
    socketed = {ref: code for src, code, _v, _q, _n, refs in design.extras if src in (JLC, JLCX) for ref in refs.split()}
    smt_joints = tht_joints = 0
    for p in design.parts.values():
        code = p.code if p.src in (JLC, JLCX) else socketed.get(p.ref)
        if p.dnp or not code:
            continue
        if code in tht:
            tht_joints += len(p.conn)
        else:
            smt_joints += len(p.conn)
    xray_pieces = sum(n for code, n in need.items() if (ext.get(code) or {}).get("xray") == "Required")
    rate = next(r for limit, r in XRAY if xray_pieces * boards <= limit) if xray_pieces else 0.0
    fixed = (FEES["setup"] + FEES["stencil"] + FEES["loading per kind of SMT part"] * (len(need) - len(tht))
             + (FEES["hand-soldering labour per order"] if tht_joints else 0) + FEES["packing"] + FEES["confirm parts placement"])
    joints = smt_joints * FEES["SMT joint"] + tht_joints * FEES["hand-soldered joint"]
    xray = xray_pieces * rate
    return {"boards": boards, "kinds": len(need), "SMT kinds": len(need) - len(tht), "SMT joints": smt_joints, "hand-soldered joints": tht_joints,
            "parts": parts, "joints": joints, "X-ray": xray, "fixed per order": fixed, "fixed share": fixed / boards,
            "one board": parts + joints + xray + fixed / boards}


def write_outputs(design, outdir):
    os.makedirs(outdir, exist_ok=True)
    basic, ext = load_basic(), load_extended()
    order = {JLC: 0, JLCX: 1, DONOR: 2, PCB: 3, AKI: 4}
    with open(os.path.join(outdir, "bom_by_source.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "code", "value", "maker's part number", "footprint", "qty", "dnp", "references", "assembled by",
                    "stock", "unit price USD (1 piece)", "note"])
        groups = {}
        for p in design.parts.values():
            groups.setdefault((p.src, p.code, p.value, p.footprint, p.dnp), []).append(p)
        for key in sorted(groups, key=lambda k: (order[k[0]], k[2], k[1])):
            ps = groups[key]
            row = basic.get(key[1]) or ext.get(key[1]) or {}
            how = {JLC: "JLCPCB (SMT Assembly)", JLCX: "JLCPCB (%s)" % row.get("assembly_type", "?"), DONOR: "plugged in by hand",
                   PCB: "part of the board", AKI: "not fitted"}[key[0]]
            w.writerow([key[0], key[1], key[2], row.get("mpn", ""), key[3], len(ps), "DNP" if key[4] else "", " ".join(p.ref for p in ps),
                        how, row.get("stock", ""), unit_price(row, 1) if row else "", ps[0].note])
        for src, code, value, qty, note, refs in design.extras:
            row = basic.get(code) or ext.get(code) or {}
            w.writerow([src, code, value, row.get("mpn", ""), "(the footprint of %s)" % refs, qty, "", refs,
                        "JLCPCB (%s)" % row.get("assembly_type", "?"), row.get("stock", ""), unit_price(row, 1) if row else "", note])
    with open(os.path.join(outdir, "netlist_by_net.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["net", "pins", "connections (ref.pin:pin name)"])
        for net, pins in sorted(design.nets().items()):
            names = []
            for ref, num in pins:
                p = design.parts[ref]
                nm = ""
                if isinstance(p.sym, SymDef):
                    nm = ":" + next(x[1] for x in p.sym.pins() if str(x[0]) == num)
                names.append(f"{ref}.{num}{nm}")
            w.writerow([net, len(pins), " ".join(names)])
    with open(os.path.join(outdir, "cost_estimate.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        rows = [cost(design, n) for n in (5, 10)]
        w.writerow(["item (USD)"] + [f"{r['boards']} boards ordered" for r in rows])
        for key in ("kinds", "SMT kinds", "SMT joints", "hand-soldered joints"):
            w.writerow([key] + [r[key] for r in rows])
        for key in ("parts", "joints", "X-ray", "fixed per order", "fixed share", "one board"):
            w.writerow([{"parts": "parts for one board", "joints": "soldering by the joint, one board", "X-ray": "X-ray inspection, one board",
                         "fixed per order": "fees per order (set-up, stencil, loading, labour, packing, placement check)",
                         "fixed share": "fees per order, share of one board", "one board": "parts and assembly of one board"}[key]]
                       + [f"{r[key]:.2f}" for r in rows])
        w.writerow(["not counted", NOT_COUNTED])
        w.writerow(["fees", "; ".join(f"{k} {v}" for k, v in FEES.items()) + "; X-ray per piece by quantity " + ", ".join(f"<={a}: {b}" for a, b in XRAY[:3])])
    with open(os.path.join(outdir, "netlist_by_part.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sheet", "ref", "value", "pin", "pin name", "net"])
        for p in design.parts.values():
            for num, net in p.conn.items():
                nm = next((x[1] for x in p.sym.pins() if str(x[0]) == num), "") if isinstance(p.sym, SymDef) else ""
                w.writerow([p.sheet, p.ref, p.value, num, nm, net if net is not None else "(NC)"])


def main():
    import circuit
    design, flags = circuit.build()
    problems, warnings, custom = [], [], set()
    check_rule(design, problems, warnings)
    check_footprints(design, problems, custom)
    check_design_rules(design, problems)
    problems += [f"datasheet fact does not hold: {text}" for text in design.failed_facts]
    for row in load_extended().values():      # stock and prices change daily
        age = (datetime.date.today() - datetime.date.fromisoformat(row["checked"])).days
        if age > 7:
            warnings.append(f"data/jlcpcb_extended_parts.csv was fetched {age} days ago ({row['checked']}); run tools/jlc_parts.py before relying on stock or prices")
            break
    kdir, odir = os.path.join(ROOT, "kicad"), os.path.join(ROOT, "out")
    for f in os.listdir(kdir) if os.path.isdir(kdir) else []:
        if f.endswith(".kicad_sch"):
            os.remove(os.path.join(kdir, f))
    rpath, files = kicad_out.write_project(design, kdir, flags)
    env = kicad_env()
    os.makedirs(odir, exist_ok=True)
    stable_uuids(files)          # before the upgrade, because KiCad orders the items by identifier when it saves
    for f in files:
        rc, out = run(["kicad-cli", "sch", "upgrade", "--force", os.path.basename(f)], env, kdir)
        if rc:
            problems.append(f"kicad-cli upgrade failed for {os.path.basename(f)}: {out[-200:]}")
    stable_uuids(files)
    root = os.path.basename(rpath)
    rc, out = run(["kicad-cli", "sch", "erc", "--severity-all", "-o", os.path.join(odir, "erc.rpt"), root], env, kdir)
    erc_line = out.splitlines()[0] if out else ""
    epath = os.path.join(odir, "erc.rpt")
    if os.path.exists(epath):
        text = re.sub(r"^ERC report \([^)]*\)", "ERC report", open(epath, encoding="utf-8").read())
        open(epath, "w", encoding="utf-8").write(text)
        errors = len(re.findall(r"; error\b", text))
        if errors:
            problems.append(f"ERC: {errors} errors, see out/erc.rpt")
    rc, out = run(["kicad-cli", "sch", "export", "netlist", "-o", os.path.join(odir, f"{design.name}.net"), root], env, kdir)
    if rc:
        problems.append("kicad-cli netlist export failed: " + out[-200:])
    else:
        npath = os.path.join(odir, f"{design.name}.net")
        text = re.sub(r'\(date "[^"]*"\)', '(date "")', open(npath, encoding="utf-8").read())   # keep rebuilds identical
        open(npath, "w", encoding="utf-8").write(text)
        kn, kc = parse_netlist(npath)
        compare(design, kn, kc, problems)
    rc, out = run(["kicad-cli", "sch", "export", "pdf", "-o", os.path.join(odir, f"{design.name}_schematic.pdf"), root], env, kdir)
    if rc:
        problems.append("kicad-cli pdf export failed: " + out[-200:])
    try:
        write_outputs(design, odir)
    except Exception as e:      # for example a part that is missing from the data files; the list below says which
        problems.append(f"writing out/ failed: {type(e).__name__}: {e}")

    by = {}
    for p in design.parts.values():
        by.setdefault(p.src, []).append(p)
    print(f"revision {design.rev}  parts: {len(design.parts)}  nets: {len(design.nets())}  sheets: {len(design.sheets)}")
    label = {JLC: "JLCPCB, Basic parts", JLCX: "JLCPCB, Extended parts", DONOR: "from the donor Famicom", PCB: "part of the bare board",
             AKI: "options, not fitted"}
    for s in (JLC, JLCX, DONOR, PCB, AKI):
        ps = by.get(s, [])
        fitted = [p for p in ps if not p.dnp]
        kinds = len(set(p.code for p in fitted)) if s in (JLC, JLCX) else len(set(p.value for p in fitted))
        extra = sum(e[3] for e in design.extras if e[0] == s)
        kinds += len(set(e[1] for e in design.extras if e[0] == s) - set(p.code for p in fitted))
        print(f"  {label[s]:24s}: {len(fitted) + extra:4d} fitted, {kinds:3d} kinds" + (f", {len(ps) - len(fitted)} positions left empty" if len(ps) > len(fitted) else ""))
    for boards in (5, 10) if not problems else ():
        c = cost(design, boards)
        print(f"  one board when {boards:2d} are ordered: parts {c['parts']:.2f} + joints {c['joints']:.2f} + X-ray {c['X-ray']:.2f} "
              f"+ share of the fees per order {c['fixed share']:.2f} ({c['fixed per order']:.2f} / {boards}) = {c['one board']:.2f} USD")
    c = cost(design, 5) if not problems else None
    if c:
        print(f"  ({c['kinds']} kinds of parts, {c['SMT kinds']} of them SMT; {c['SMT joints']} SMT joints, {c['hand-soldered joints']} hand-soldered joints; "
          "not counted: see out/cost_estimate.csv)")
    print("ERC:", erc_line)
    if custom:
        print("custom footprints still to be drawn:", ", ".join(sorted(custom)))
    for w in warnings:
        print("WARNING:", w)
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("OK: model and KiCad netlist agree; parts rule satisfied")


if __name__ == "__main__":
    main()
