"""Write KiCad 10 footprints (.kicad_mod) for the board's own footprint library (kicad/fcjamma.pretty).

Two ways to make a footprint:
- Footprint(...): drawn from scratch with pad(), line(), rect(), circle(), poly(), text() and keepout();
- derive(...): a copy of a KiCad library footprint, renamed and changed by a function that edits the parsed file.

Coordinates are millimetres in KiCad's footprint frame: X to the right, Y downward, seen from the parts side.
Identifiers (uuid) are derived from the footprint name and the item's position in the file, so a rebuild
writes the same bytes.
"""
import math
import os
import uuid

from .sexpr import Q, dump, find, first, fmt, parse

NS = uuid.UUID("5d6c0e64-4a52-4c2e-9a35-3f0b1f2c7a11")
VERSION = "20260206"          # the footprint format of KiCad 10.0


def _n(v):
    return fmt(float(v))


def _xy(p):
    return [_n(p[0]), _n(p[1])]


def _stroke(width):
    return ["stroke", ["width", _n(width)], ["type", "solid"]]


def _font(size, thickness):
    return ["effects", ["font", ["size", _n(size), _n(size)], ["thickness", _n(thickness)]]]


class Footprint:
    def __init__(self, name, descr, tags="", attr=("through_hole",), ref_at=(0, -3), value_at=(0, 3)):
        self.name, self.descr, self.tags, self.attr = name, descr, tags, tuple(attr)
        self.ref_at, self.value_at = ref_at, value_at
        self.items = []

    # ---------------------------------------------------------------- graphics
    def line(self, a, b, layer, width=0.12):
        self.items.append(["fp_line", ["start", *_xy(a)], ["end", *_xy(b)], _stroke(width), ["layer", Q(layer)]])

    def rect(self, a, b, layer, width=0.12, fill=False):
        self.items.append(["fp_rect", ["start", *_xy(a)], ["end", *_xy(b)], _stroke(width), ["fill", "yes" if fill else "no"],
                           ["layer", Q(layer)]])

    def circle(self, c, r, layer, width=0.12, fill=False):
        self.items.append(["fp_circle", ["center", *_xy(c)], ["end", _n(c[0] + r), _n(c[1])], _stroke(width),
                           ["fill", "yes" if fill else "no"], ["layer", Q(layer)]])

    def poly(self, pts, layer, width=0.0, fill=True):
        self.items.append(["fp_poly", ["pts", *[["xy", *_xy(p)] for p in pts]], _stroke(width), ["fill", "yes" if fill else "no"],
                           ["layer", Q(layer)]])

    def outline(self, a, b, layer, width):
        """Four lines (a rectangle that is not one item, so that it can be broken later if needed)."""
        (x0, y0), (x1, y1) = a, b
        for p, q in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            self.line(p, q, layer, width)

    def arc(self, start, mid, end, layer, width=0.12):
        self.items.append(["fp_arc", ["start", *_xy(start)], ["mid", *_xy(mid)], ["end", *_xy(end)], _stroke(width), ["layer", Q(layer)]])

    def polyline(self, pts, layer, width, closed=False):
        seq = list(pts) + ([pts[0]] if closed else [])
        for a, b in zip(seq, seq[1:]):
            self.line(a, b, layer, width)

    def text(self, s, at, layer, size=1.0, thickness=0.15, rot=0, mirror=False):
        eff = _font(size, thickness)
        if mirror:
            eff.append(["justify", "mirror"])
        self.items.append(["fp_text", "user", Q(s), ["at", *_xy(at), _n(rot)], ["layer", Q(layer)], eff])

    # ---------------------------------------------------------------- pads
    def pad(self, number, kind, shape, at, size, layers, drill=None, rratio=None, rot=0):
        """kind: smd, thru_hole, np_thru_hole or connect (edge-connector finger: copper and mask, never paste)."""
        node = ["pad", Q(str(number)), kind, shape, ["at", *_xy(at)] + ([_n(rot)] if rot else []), ["size", _n(size[0]), _n(size[1])]]
        if drill is not None:
            node.append(["drill", _n(drill)])
        node.append(["layers", *[Q(x) for x in layers]])
        if kind == "thru_hole":
            node.append(["remove_unused_layers", "no"])
        if rratio is not None:
            node.append(["roundrect_rratio", _n(rratio)])
        self.items.append(node)

    # ---------------------------------------------------------------- rule areas
    def keepout(self, layers, pts, name, tracks=True, vias=True, pads=True, copperpour=True, footprints=False):
        """A keep-out rule area: True means 'not allowed'.  The name is what board rules (.kicad_dru) refer to."""
        self.items.append(keepout_zone(layers, pts, name, tracks, vias, pads, copperpour, footprints))

    # ---------------------------------------------------------------- file
    def tree(self):
        head = ["footprint", Q(self.name), ["version", VERSION], ["generator", Q("fcgen")], ["generator_version", Q("10.0")],
                ["layer", Q("F.Cu")], ["descr", Q(self.descr)], ["tags", Q(self.tags)],
                ["property", Q("Reference"), Q("REF**"), ["at", *_xy(self.ref_at), "0"], ["layer", Q("F.SilkS")], _font(1, 0.15)],
                ["property", Q("Value"), Q(self.name), ["at", *_xy(self.value_at), "0"], ["layer", Q("F.Fab")], _font(1, 0.15)]]
        if self.attr:
            head.append(["attr", *self.attr])
        head.append(["duplicate_pad_numbers_are_jumpers", "no"])
        return head + self.items + [["embedded_fonts", "no"]]


def keepout_zone(layers, pts, name, tracks=True, vias=True, pads=True, copperpour=True, footprints=False):
    def rule(flag):
        return "not_allowed" if flag else "allowed"
    layer_node = ["layer", Q(layers[0])] if len(layers) == 1 else ["layers", *[Q(x) for x in layers]]
    return ["zone", layer_node, ["name", Q(name)], ["hatch", "full", "0.5"], ["connect_pads", ["clearance", "0"]],
            ["min_thickness", "0.25"],
            ["keepout", ["tracks", rule(tracks)], ["vias", rule(vias)], ["pads", rule(pads)],
             ["copperpour", rule(copperpour)], ["footprints", rule(footprints)]],
            ["placement", ["enabled", "no"], ["sheetname", Q("")]],
            ["fill", ["thermal_gap", "0.5"], ["thermal_bridge_width", "0.5"], ["island_removal_mode", "0"]],
            ["polygon", ["pts", *[["xy", *_xy(p)] for p in pts]]]]


def circle_points(c, r, n=32):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _pts(node, key):
    return [[float(v[1]), float(v[2])] for v in first(node, key)[1:] if isinstance(v, list) and v[0] == "xy"]


def _xyf(node, key):
    v = first(node, key)
    return [float(v[1]), float(v[2])]


def expected(tree):
    """What KiCad should read from this footprint: every pad (keyed by number, or by position when unnumbered),
    every keep-out area, every drawing and the attributes.  tools/check_footprints.py compares it with KiCad."""
    out = {"pads": {}, "keepouts": 0, "keepout_boxes": [], "keepout_rules": [], "keepout_layers": [], "keepout_names": [],
           "attr": [], "graphics": {}, "drawings": []}
    for p in find(tree, "pad"):
        at, size = first(p, "at"), first(p, "size")
        x, y = float(at[1]), float(at[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
        drill = first(p, "drill")
        d = 0.0
        if drill is not None:
            nums = [v for v in drill[1:] if not isinstance(v, list) and v != "oval"]
            d = float(nums[0]) if nums else 0.0
        key = str(p[1]) or f"(no number) {x:.3f},{y:.3f}"
        out["pads"].setdefault(key, []).append({"x": x, "y": y, "rot": rot, "kind": str(p[2]), "shape": str(p[3]),
                                                "w": float(size[1]), "h": float(size[2]), "drill": d,
                                                "layers": [str(v) for v in first(p, "layers")[1:]]})
    for z in find(tree, "zone"):
        ko = first(z, "keepout")
        if ko is None:
            continue
        pts = _pts(first(z, "polygon"), "pts")
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        layer_node = first(z, "layers") or first(z, "layer")
        name = first(z, "name")
        out["keepouts"] += 1
        out["keepout_boxes"].append([min(xs), min(ys), max(xs), max(ys)])
        out["keepout_rules"].append({r[0]: r[1] for r in ko[1:]})
        out["keepout_layers"].append(sorted(str(v) for v in layer_node[1:]))
        out["keepout_names"].append(str(name[1]) if name else "")
    attr = first(tree, "attr")
    out["attr"] = [str(a) for a in attr[1:]] if attr else []
    for x in tree:
        if not (isinstance(x, list) and x and x[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly", "fp_text")):
            continue
        layer = str(first(x, "layer")[1])
        out["graphics"][layer] = out["graphics"].get(layer, 0) + 1
        fill = first(x, "fill")
        item = {"type": x[0], "layer": layer, "fill": bool(fill and fill[1] in ("yes", "solid")), "text": None}
        if x[0] in ("fp_line", "fp_rect"):
            item["pts"] = [_xyf(x, "start"), _xyf(x, "end")]
        elif x[0] == "fp_circle":
            item["pts"] = [_xyf(x, "center"), _xyf(x, "end")]
        elif x[0] == "fp_arc":
            item["pts"] = [_xyf(x, "start"), _xyf(x, "mid"), _xyf(x, "end")]
        elif x[0] == "fp_poly":
            item["pts"] = _pts(x, "pts")
        else:
            item["pts"] = [_xyf(x, "at")]
            item["text"] = str(x[2])
        out["drawings"].append(item)
    return out


def add_uuids(tree, name):
    """Give every item that KiCad identifies by uuid a stable one (replacing any copied from a library file)."""
    count = [0]
    kinds = ("property", "fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly", "fp_text", "pad", "zone", "group", "point")

    def walk(node):
        for x in node:
            if isinstance(x, list) and x:
                if x[0] in kinds:
                    for u in find(x, "uuid"):
                        x.remove(u)
                    count[0] += 1
                    x.append(["uuid", Q(str(uuid.uuid5(NS, f"{name}-{count[0]}")))])
                if x[0] not in ("pad", "zone"):
                    walk(x)
    walk(tree)
    return tree


def write(tree, libdir):
    name = str(tree[1])
    add_uuids(tree, name)
    os.makedirs(libdir, exist_ok=True)
    path = os.path.join(libdir, f"{name}.kicad_mod")
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(tree) + "\n")
    return path


def derive(library_file, new_name, descr, edit):
    """A copy of a KiCad library footprint: renamed, described, then changed by edit(tree)."""
    tree = parse(open(library_file, encoding="utf-8").read())
    tree[1] = Q(new_name)
    for node in find(tree, "property"):
        if node[1] == "Value":
            node[2] = Q(new_name)
    d = first(tree, "descr")
    d[1] = Q(descr)
    g = first(tree, "generator")
    g[1] = Q("fcgen")
    edit(tree)
    return tree


def pads(tree):
    return find(tree, "pad")
