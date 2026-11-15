"""A small reader and writer for KiCad's S-expression files (footprints, boards).

parse(text) returns nested Python lists.  An atom is a plain str; a quoted string is a Q (a str subclass),
so that dump() writes it back with quotes.  dump() writes KiCad's layout: a list whose items are all atoms
on one line, any other list with its head atoms on the first line and one child per line, indented by tabs.
KiCad reads any layout, so the only aim of the layout is a readable, stable file.
"""


class Q(str):
    """A quoted string."""


ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"'}


def _tokens(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            yield c
            i += 1
        elif c == '"':
            j, out = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    nxt = text[j + 1]
                    out.append(ESCAPES.get(nxt, "\\" + nxt))      # an unknown escape is kept as written
                    j += 2
                else:
                    out.append(text[j])
                    j += 1
            yield Q("".join(out))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            yield text[i:j]
            i = j


def parse(text):
    stack, top = [], None
    for t in _tokens(text):
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            if stack:
                stack[-1].append(node)
            else:
                top = node
        else:
            stack[-1].append(t)
    if stack:
        raise ValueError("unbalanced parentheses")
    return top


def _atom(a):
    if isinstance(a, Q):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'
    if isinstance(a, float):
        return fmt(a)
    return str(a)


def fmt(v):
    """A number the way KiCad writes it: no exponent, no trailing zeros, at most 6 decimals."""
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def dump(node, depth=0):
    tab = "\t" * depth
    if all(not isinstance(x, list) for x in node):
        return tab + "(" + " ".join(_atom(x) for x in node) + ")"
    head, rest = [], []
    for x in node:
        (rest if rest or isinstance(x, list) else head).append(x)
    lines = [tab + "(" + " ".join(_atom(x) for x in head)]
    for x in rest:
        lines.append(dump(x, depth + 1) if isinstance(x, list) else "\t" * (depth + 1) + _atom(x))
    lines.append(tab + ")")
    return "\n".join(lines)


def find(node, key):
    """The direct children of node that are lists starting with key."""
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def first(node, key):
    found = find(node, key)
    return found[0] if found else None
