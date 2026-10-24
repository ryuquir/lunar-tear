"""Minimal S-expression reader/writer for KiCad files."""
class Sym(str):
    """Bare symbol token (unquoted)."""
    __slots__ = ()

def parse(text):
    i, n = 0, len(text)
    def skip_ws():
        nonlocal i
        while i < n and text[i] in ' \t\r\n': i += 1
    def read():
        nonlocal i
        skip_ws()
        if text[i] == '(':
            i += 1; lst = []
            while True:
                skip_ws()
                if text[i] == ')': i += 1; return lst
                lst.append(read())
        if text[i] == '"':
            i += 1; out = []
            while text[i] != '"':
                if text[i] == '\\': i += 1; out.append(text[i])
                else: out.append(text[i])
                i += 1
            i += 1; return ''.join(out)
        j = i
        while i < n and text[i] not in ' \t\r\n()': i += 1
        tok = text[j:i]
        return Sym(tok)
    return read()

def dump(node, indent=0):
    if isinstance(node, list):
        if not node: return '()'
        head = node[0]
        if isinstance(head, str) and not isinstance(head, Sym): head = Sym(head)   # list heads are always keywords
        inner_lists = any(isinstance(x, list) for x in node[1:])
        if not inner_lists:
            return '(' + ' '.join([dump(head)] + [dump(x) for x in node[1:]]) + ')'
        parts = ['(' + dump(head)]
        atoms = []
        rest = node[1:]
        k = 0
        while k < len(rest) and not isinstance(rest[k], list):
            atoms.append(dump(rest[k])); k += 1
        if atoms: parts[0] += ' ' + ' '.join(atoms)
        out = parts[0]
        for x in rest[k:]:
            out += '\n' + '  ' * (indent + 1) + dump(x, indent + 1)
        return out + '\n' + '  ' * indent + ')'
    if isinstance(node, Sym): return str(node)
    if isinstance(node, str):
        return '"' + node.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(node, float):
        s = ('%.6f' % node).rstrip('0').rstrip('.')
        return s if s not in ('', '-0') else '0'
    return str(node)

def find(node, key):
    """First child list whose head == key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key: return x
    return None

def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
