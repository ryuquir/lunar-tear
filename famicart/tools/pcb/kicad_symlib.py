"""Load symbols (with all units) from KiCad .kicad_sym libraries and report pin geometry."""
import os
from sexp import parse, find, find_all, Sym

SYM_DIR = '/usr/share/kicad/symbols'
_cache = {}

def load_lib(name_or_path):
    path = name_or_path if name_or_path.endswith('.kicad_sym') else os.path.join(SYM_DIR, name_or_path + '.kicad_sym')
    if path not in _cache:
        _cache[path] = parse(open(path, encoding='utf-8').read())
    return _cache[path]

def get_symbol(lib, name):
    """Return the symbol node (resolving 'extends')."""
    root = load_lib(lib)
    for s in find_all(root, 'symbol'):
        if s[1] == name:
            ext = find(s, 'extends')
            if ext:
                base = get_symbol(lib, ext[1])
                # shallow merge: take base body, override properties from derived
                import copy
                merged = copy.deepcopy(base); merged[1] = name
                props = {p[1]: p for p in find_all(s, 'property')}
                merged[:] = [x for x in merged if not (isinstance(x, list) and x and x[0] == 'property' and x[1] in props)] + list(props.values())
                # rename sub-units
                for sub in find_all(merged, 'symbol'):
                    sub[1] = name + sub[1][len(ext[1]):]
                return merged
            return s
    raise KeyError(f'{lib}:{name}')

def pins(sym):
    """List of dicts: unit, number, name, x, y, angle, length, type (symbol coordinates, Y up)."""
    out = []
    for sub in find_all(sym, 'symbol'):
        unit = int(sub[1].rsplit('_', 2)[-2])
        for p in find_all(sub, 'pin'):
            at = find(p, 'at'); ln = find(p, 'length'); nm = find(p, 'name'); num = find(p, 'number')
            out.append(dict(unit=unit, number=num[1], name=nm[1], x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0,
                            length=float(ln[1]), type=str(p[1])))
    return out

def units(sym):
    return sorted({int(sub[1].rsplit('_', 2)[-2]) for sub in find_all(sym, 'symbol')} - {0})

if __name__ == '__main__':
    import sys
    for spec in sys.argv[1:]:
        lib, name = spec.split(':')
        s = get_symbol(lib, name)
        print(spec, 'units', units(s))
        for p in sorted(pins(s), key=lambda p: (p['unit'], int(p['number']) if p['number'].isdigit() else 99)):
            print('   u%d pin %-3s %-6s at (%6.2f,%6.2f) ang %3.0f len %.2f %s' % (p['unit'], p['number'], p['name'], p['x'], p['y'], p['angle'], p['length'], p['type']))
