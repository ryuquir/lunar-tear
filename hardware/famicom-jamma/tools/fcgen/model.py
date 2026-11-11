"""Circuit model for the Famicom JAMMA board.

The circuit is described in Python (design/*.py) with the small classes below.
tools/build.py turns that description into a KiCad project, and checks it.

Conventions
- A net is a plain string.  NC (None) marks a pin that is intentionally left open.
- Every pin of every part must be given a net or NC; the build fails otherwise.
- Sourcing class of each part (the project's parts rule):
    JLC   : assembled by JLCPCB; must be a Basic part (LCSC number checked against data/)
    AKI   : hand-soldered part bought from Akizuki Denshi (sales code)
    DONOR : taken from the donor Famicom
    PCB   : part of the bare board (jumpers, test points, footprints only)
"""
from dataclasses import dataclass, field

NC = None

JLC, AKI, DONOR, PCB = "JLC", "AKI", "DONOR", "PCB"

PIN_TYPES = {
    "in": "input", "out": "output", "bi": "bidirectional", "tri": "tri_state",
    "pas": "passive", "pwr": "power_in", "pwo": "power_out", "oc": "open_collector",
}


@dataclass
class SymDef:
    """A project symbol: one box, pins on the left and right in the given order."""
    name: str
    prefix: str
    left: list          # [(number, name, type)] ; None = one empty slot
    right: list
    desc: str = ""

    def pins(self):
        return [p for p in self.left + self.right if p is not None]

    def by_name(self):
        d = {}
        for num, name, _t in self.pins():
            if name in d:
                raise ValueError(f"{self.name}: duplicate pin name {name}; connect by number")
            d[name] = num
        return d


@dataclass
class Part:
    ref: str
    sym: object                 # SymDef, or "Lib:Symbol" string for KiCad library symbols
    value: str
    footprint: str
    conn: dict                  # pin number (str) -> net or NC
    src: str
    code: str = ""              # LCSC C-number or Akizuki sales code
    dnp: bool = False
    note: str = ""
    sheet: str = ""
    horizontal: bool = False    # library two-pin parts are drawn lying down

    @property
    def lib_id(self):
        return f"fcjamma:{self.sym.name}" if isinstance(self.sym, SymDef) else self.sym


class Design:
    def __init__(self, name, title):
        self.name = name
        self.title = title
        self.symdefs = {}
        self.sheets = []
        self.parts = {}
        self._auto = {}
        self.notes = {}           # sheet key -> list of text notes
        self.extras = []          # items to buy that have no footprint of their own (sockets, plug-in chips)

    def extra(self, src, code, value, qty, note=""):
        """An item for the parts list that is not a schematic part (a socket, a jumper plug, ...)."""
        self.extras.append((src, code, value, qty, note))

    # ---- symbols ----
    def symdef(self, name, prefix, left, right, desc=""):
        sd = SymDef(name, prefix, left, right, desc)
        nums = [p[0] for p in sd.pins()]
        if len(nums) != len(set(nums)):
            raise ValueError(f"{name}: duplicate pin number")
        self.symdefs[name] = sd
        return sd

    def sheet(self, key, title):
        s = Sheet(self, key, title)
        self.sheets.append(s)
        return s

    def autoref(self, prefix):
        n = self._auto.get(prefix, 0) + 1
        while f"{prefix}{n}" in self.parts:
            n += 1
        self._auto[prefix] = n
        return f"{prefix}{n}"

    def add(self, part):
        if part.ref in self.parts:
            raise ValueError(f"duplicate reference {part.ref}")
        self.parts[part.ref] = part
        return part

    # ---- derived data ----
    def nets(self):
        nets = {}
        for p in self.parts.values():
            for pin, net in p.conn.items():
                if net is not None:
                    nets.setdefault(net, []).append((p.ref, pin))
        return nets


def bus(pin_prefix, lo, hi, net_prefix, pin_fmt="{p}{i}", net_fmt="{n}{i}"):
    """{'A0': 'CA0', ...} for i in lo..hi."""
    return {pin_fmt.format(p=pin_prefix, i=i): net_fmt.format(n=net_prefix, i=i) for i in range(lo, hi + 1)}


class Sheet:
    def __init__(self, design, key, title):
        self.d = design
        self.key = key
        self.title = title

    def note(self, text):
        self.d.notes.setdefault(self.key, []).append(text)

    # ---- project symbols, connected by pin name ----
    def ic(self, ref, symname, value, fp, src, code="", pins=None, dnp=False, note=""):
        sd = self.d.symdefs[symname]
        names = sd.by_name()
        conn = {}
        for name, net in (pins or {}).items():
            if name not in names:
                raise ValueError(f"{ref} ({symname}): no pin named {name}")
            conn[str(names[name])] = net
        missing = [n for n in names if str(names[n]) not in conn]
        if missing:
            raise ValueError(f"{ref} ({symname}): pins not assigned: {missing}")
        return self.d.add(Part(ref, sd, value, fp, conn, src, code, dnp, note, self.key))

    # ---- KiCad library symbols, connected by pin number ----
    def lib(self, prefix, lib_id, value, fp, src, code, conn, dnp=False, note="", ref=None, horizontal=False):
        ref = ref or self.d.autoref(prefix)
        conn = {str(k): v for k, v in conn.items()}
        return self.d.add(Part(ref, lib_id, value, fp, conn, src, code, dnp, note, self.key, horizontal))
