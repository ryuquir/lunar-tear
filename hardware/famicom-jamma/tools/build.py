#!/usr/bin/env python3
"""Build the KiCad project from the circuit description and check it.

Run with the project's Python environment (see tools/setup_env.sh):
    /opt/fcjamma-venv/bin/python tools/build.py

Steps
 1. load design/circuit.py
 2. check the parts rule (JLCPCB parts must be Basic; values must match JLCPCB's description)
 3. check that every standard footprint exists in the KiCad library
 4. write kicad/ (symbol library, schematic sheets, project file)
 5. kicad-cli: upgrade to the KiCad 10 format, ERC, netlist, PDF
 6. compare KiCad's netlist with the model, pin by pin
 7. write out/ (BOM with sourcing, net list, reports)
"""
import csv
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
from fcgen.model import SymDef, JLC, AKI, DONOR, PCB   # noqa: E402

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


def check_rule(design, problems):
    basic = load_basic()
    for code, text in P.USED_CODES.items():
        row = basic.get(code)
        if row is None:
            problems.append(f"parts rule: {code} is not in the JLCPCB Basic list")
            continue
        hay = (row["description"] + " " + row["mpn"]).replace(" ", "")
        if text.replace(" ", "") not in hay:
            problems.append(f"parts rule: {code} is '{row['mpn']} / {row['description'][:60]}', expected to contain '{text}'")
    for p in design.parts.values():
        if p.src == JLC and p.code not in basic:
            problems.append(f"parts rule: {p.ref} ({p.value}) uses {p.code or 'no LCSC number'}, which is not Basic")
        if p.src == AKI and not p.dnp and not re.fullmatch(r"\d{6}", p.code or ""):
            problems.append(f"parts rule: {p.ref} ({p.value}) has no Akizuki sales code")
    for src, code, value, _qty, _note in design.extras:
        if src == AKI and not re.fullmatch(r"\d{6}", code or ""):
            problems.append(f"parts rule: extra item '{value}' has no Akizuki sales code")


def check_footprints(design, problems, custom):
    for p in design.parts.values():
        if not p.footprint:
            problems.append(f"footprint: {p.ref} has none")
            continue
        lib, name = p.footprint.split(":")
        if lib == "fcjamma":
            custom.add(p.footprint)
        elif not os.path.exists(os.path.join(KICAD_FP, f"{lib}.pretty", f"{name}.kicad_mod")):
            problems.append(f"footprint: {p.ref} -> {p.footprint} not found in the KiCad library")


PASSIVE_LIBS = ("Device:R", "Device:C", "Device:C_Polarized", "Device:R_Pack04", "Device:FerriteBead", "Device:R_Potentiometer_Trim",
                "Connector:TestPoint", "Connector_Generic:", "Switch:")
NON_FT = {"GP26", "GP27", "GP28"}                     # Pico pins that never tolerate 5 V
OPEN_DRAIN_595_INPUTS = {"SER", "SRCLK", "RCLK", "/OE"}   # 5 V shift-register inputs that a Pico pulls low (pull-up to +5V_SW)


def check_design_rules(design, problems):
    """Electrical rules of this board that can be checked from the netlist alone."""
    def pin_name(part, num):
        if isinstance(part.sym, SymDef):
            return next(x[1] for x in part.sym.pins() if str(x[0]) == num)
        return ""

    def supply(part):
        if not isinstance(part.sym, SymDef):
            return None
        for num, net in part.conn.items():
            if pin_name(part, num) in ("VCC", "V+", "+V", "VSYS"):
                return net
        return None

    def passive(part):
        return (not isinstance(part.sym, SymDef)) and part.lib_id.startswith(PASSIVE_LIBS)

    nets = design.nets()
    # 1. a 5 V part reaches a Pico pin only through a resistor (the open-drain dump lines are the documented exception)
    for net, pins in nets.items():
        picos = [(r, n) for r, n in pins if isinstance(design.parts[r].sym, SymDef) and design.parts[r].sym.name == "PICO2"]
        gp = [pin_name(design.parts[r], n) for r, n in picos if pin_name(design.parts[r], n).startswith("GP")]
        if not gp:
            continue
        for r, n in pins:
            part = design.parts[r]
            if (r, n) in picos or passive(part) or supply(part) in ("+3V3", "VSYS"):
                continue
            name = pin_name(part, n)
            ok = (part.sym.name == "74HC595" and name in OPEN_DRAIN_595_INPUTS and not (set(gp) & NON_FT)) if isinstance(part.sym, SymDef) else False
            if not ok:
                problems.append(f"design rule: net {net} joins Pico pin {'/'.join(gp)} directly to {r}.{n} ({name}), a part outside the 3.3 V domain")
    # 2. one 100 nF capacitor per IC on its supply net, counted per sheet
    need, have = {}, {}
    for part in design.parts.values():
        if isinstance(part.sym, SymDef) and part.ref.startswith("U") and part.sym.name not in ("PICO2", "CJ431", "AE_PAM8012"):
            need[(part.sheet, supply(part))] = need.get((part.sheet, supply(part)), 0) + 1
        if part.lib_id == "Device:C" and part.value == "100n" and not part.dnp:
            a, b = part.conn.get("1"), part.conn.get("2")
            rail = a if b == "GND" else b
            have[(part.sheet, rail)] = have.get((part.sheet, rail), 0) + 1
    for key, n in need.items():
        if have.get(key, 0) < n:
            problems.append(f"design rule: sheet {key[0]} has {n} ICs on {key[1]} but only {have.get(key, 0)} 100 nF capacitors there")
    # 3. every numbered bus bit has the same kinds of connections as its neighbours
    import collections
    fam = collections.defaultdict(dict)
    for net, pins in nets.items():
        m = re.fullmatch(r"([A-Z_]+?)(\d+)", net)
        if m and m.group(1) in ("CD", "PPD", "CART_D", "PD"):
            fam[m.group(1)][int(m.group(2))] = sorted(re.sub(r"\d+$", "", r) + ":" + type(design.parts[r].sym).__name__ for r, _ in pins)
    for name, bits_ in fam.items():
        shapes = collections.Counter(tuple(v) for v in bits_.values())
        if len(shapes) > 1:
            common = shapes.most_common(1)[0][0]
            odd = [f"{name}{i}" for i, v in sorted(bits_.items()) if tuple(v) != common]
            problems.append(f"design rule: bus {name} is not uniform; check {odd}")


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


def write_outputs(design, outdir):
    os.makedirs(outdir, exist_ok=True)
    order = {JLC: 0, AKI: 1, DONOR: 2, PCB: 3}
    with open(os.path.join(outdir, "bom_by_source.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "code", "value", "footprint", "qty", "dnp", "references", "note"])
        groups = {}
        for p in design.parts.values():
            groups.setdefault((p.src, p.code, p.value, p.footprint, p.dnp), []).append(p)
        for key in sorted(groups, key=lambda k: (order[k[0]], k[2], k[1])):
            ps = groups[key]
            w.writerow([key[0], key[1], key[2], key[3], len(ps), "DNP" if key[4] else "", " ".join(p.ref for p in ps), ps[0].note])
        for src, code, value, qty, note in design.extras:
            w.writerow([src, code, value, "(no footprint)", qty, "", "", note])
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
    problems, custom = [], set()
    check_rule(design, problems)
    check_footprints(design, problems, custom)
    check_design_rules(design, problems)
    single = sorted(n for n, pins in design.nets().items() if len(pins) == 1)
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
    write_outputs(design, odir)

    by = {}
    for p in design.parts.values():
        by.setdefault(p.src, []).append(p)
    print(f"parts: {len(design.parts)}  nets: {len(design.nets())}  sheets: {len(design.sheets)}")
    for s in (JLC, AKI, DONOR, PCB):
        ps = by.get(s, [])
        kinds = len(set(p.code for p in ps if not p.dnp)) if s == JLC else len(set((p.code, p.value.split(" (")[0]) for p in ps if not p.dnp))
        print(f"  {s:5s}: {len(ps):4d} parts, {kinds:3d} kinds fitted" + (f", {sum(p.dnp for p in ps)} not fitted" if any(p.dnp for p in ps) else ""))
    print("ERC:", erc_line)
    if custom:
        print("custom footprints still to be drawn:", ", ".join(sorted(custom)))
    if single:
        print(f"nets with a single pin ({len(single)}):", ", ".join(single[:40]))
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("OK: model and KiCad netlist agree; parts rule satisfied")


if __name__ == "__main__":
    main()
