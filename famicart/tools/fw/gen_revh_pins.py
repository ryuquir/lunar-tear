#!/usr/bin/env python3
"""Pin headers of the rev H firmware, generated from the board's netlist (tools/pcb/design_revh.py).

  src/revh/pins_u<N>.h   one per RP2350B (U1-U6, U8, U9; U7 is the hub's second flash): every connected GPIO as
                         PIN_<NET>, the QFN-80 pin and what the net reaches, the unconnected GPIOs, the pins whose
                         nets reach the console's card edge, and the consecutive groups a PIO program needs
                         (BASE / COUNT, the PIO window that holds them, a _Static_assert that they are consecutive)
  src/revh/pins_hub.h    U6 under the names docs/13 gives the hub's functions (SPI0 for the microSD, ADC channels and
                         dividers, PWM slices, the SWD pair of each target chip, XIP CS1 for U7)

  python3 tools/fw/gen_revh_pins.py            write the headers
  python3 tools/fw/gen_revh_pins.py --check    regenerate in memory; exit 1 if a header is stale or missing

The netlist is the single source of truth: NETS[ref][qfn_pin] (design_revh.NETS) is read through GPIO_PIN
(design_revd.GPIO_PIN, the RP2350B QFN-80 table) and must agree with the per-chip tables G[n]. Nothing here needs the
pico-sdk: the GPIO function numbers are referenced by their io_bank0.h names, so a pin that lacks the function fails
at compile time, not here.
"""
import argparse
import difflib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))                  # famicart/
PCB = os.path.join(ROOT, 'tools', 'pcb')
OUT = os.path.join(ROOT, 'src', 'revh')

CHIPS = (1, 2, 3, 4, 5, 6, 8, 9)
HUB = 6
POWER = {'GND', '+3V3', '+5V', '+1V1', 'V5_IN', 'VBUS'}
NGPIO = 48
TLV62569_VFB_MV = 600          # TLV62569 feedback reference (TI SLVSDG1C): +3V3 = 0.6 V x (1 + Rtop / Rbottom)

# Groups that are not a run of numbered nets or a link triplet: docs/13 "PIO の割り当て" and "ピン割り当て" (PIO windows).
# (chip, name, first net, last net, what it is for); every GPIO between first and last belongs to the group.
MANUAL_GROUPS = [
    (1, 'CPU_BUS', 'CA0', 'WS_D', 'bus capture: A0-14, D0-7, R/W, M2, /ROMSEL (raw), RSEL_D, WS_D (docs/13: GPIO0-27)'),
    (4, 'CPU_BUS', 'CA0', 'WS_D', 'bus capture: A0-14, D0-7, R/W, M2, /ROMSEL (raw), RSEL_D, WS_D (docs/13: GPIO0-27)'),
    (3, 'CPU_BUS', 'ZA0', 'Z_ROMSEL', "bus capture through U3's own branch: A0-14, D0-7, M2, R/W, /ROMSEL"),
    (3, 'CIRAM', 'PA10', 'NA10_D', 'CIRAM table: in PA10-13 and /RD, side-set /CE and A10 (docs/13: in_base 32, side-set 37 / 38)'),
    (2, 'PPU_BUS', 'PA0', 'RD_D', 'PPU bus capture: A0-13, D0-7, /RD'),
    (5, 'PPU_BUS', 'PA0', 'RD_D', 'PPU bus capture: A0-13, D0-7, /RD'),
    (6, 'SD', 'SD_CLK', 'SD_DAT3', 'microSD 4-bit (PIO): CLK, CMD, DAT0-3'),
]


def load_design():
    sys.dont_write_bytecode = True                  # tools/pcb is read-only for this script: no __pycache__ there
    os.environ.setdefault('FC_DESIGN', 'design_revh')
    sys.path.insert(0, PCB)
    import design_revh as D                         # noqa: E402  (needs the path above)
    return D


def cname(net):
    return re.sub(r'[^A-Za-z0-9_]', '_', net).upper()


def ohms(val):
    """'10k' -> 10000, '2.2k' -> 2200, '680 x4' -> 680, '27' -> 27"""
    v = val.split()[0]
    mul = 1000 if v.endswith('k') else 1
    return int(round(float(v.rstrip('k')) * mul))


class Netlist:
    def __init__(self, D):
        self.D = D
        self.nodes = {}                              # net -> [(ref, pin)]
        for ref, pins in D.NETS.items():
            for p, nn in pins.items():
                if nn:
                    self.nodes.setdefault(nn, []).append((ref, p))
        self.fingers = {}                            # net -> [finger numbers]
        for p, nn in D.NETS['J1'].items():
            if nn and nn not in POWER:
                self.fingers.setdefault(nn, []).append(int(p))
        self.chips = {ref for ref, v in D.PARTS.items() if v[1] == 'RP2350B'}

    def sym(self, ref):
        return self.D.PARTS[ref][1]

    def val(self, ref):
        return self.D.PARTS[ref][2]

    def resistor_ends(self, net):
        """[(ref, ohms, other net, elements)] for every resistor element with one end on `net`"""
        out = {}
        for ref, p in self.nodes.get(net, []):
            s = self.sym(ref)
            if s == 'R':
                other = self.D.NETS[ref].get('2' if p == '1' else '1')
            elif s == 'R_Pack04':
                other = self.D.NETS[ref].get(str(9 - int(p)))
            else:
                continue
            if other is None:
                continue
            k = (ref, other)
            out[k] = out.get(k, 0) + 1
        return [(ref, ohms(self.val(ref)), other, n) for (ref, other), n in sorted(out.items())]

    def fet_links(self, net):
        """[(ref, 'gate'|'drain', other net)]: 2N7002 gate <-> drain"""
        out = []
        for ref, p in self.nodes.get(net, []):
            if self.sym(ref) != '2N7002':
                continue
            if p == '1':
                out.append((ref, 'gate', self.D.NETS[ref]['3']))
            elif p == '3':
                out.append((ref, 'drain', self.D.NETS[ref]['1']))
        return out

    def reaches_console(self, net):
        """True when the net reaches a card-edge finger through resistors or a FET's gate / drain (not through a supply)."""
        seen, todo = {net}, [net]
        while todo:
            n = todo.pop()
            if n in self.fingers:
                return True
            nxt = [o for _, _, o, _ in self.resistor_ends(n)] + [o for _, _, o in self.fet_links(n)]
            for o in nxt:
                if o and o not in POWER and o not in seen:
                    seen.add(o)
                    todo.append(o)
        return False

    def describe(self, net, me):
        """Short text: the other chips on the net, then what the resistors / FETs / connectors lead to."""
        parts = []
        others = sorted({r for r, _ in self.nodes.get(net, []) if r in self.chips and r != me}, key=lambda r: int(r[1:]))
        if len(others) >= 6:
            parts.append('all other chips')
        elif others:
            parts.append(' '.join(others))
        for ref, r, other, n in self.resistor_ends(net):
            v = f'{r // 1000}k' if r >= 1000 and r % 1000 == 0 else (f'{r / 1000:g}k' if r >= 1000 else str(r))
            par = f' x{n}' if n > 1 else ''
            fin = self.fingers.get(other)
            tail = f' (finger {"/".join(map(str, sorted(fin)))})' if fin else ''
            parts.append(f'{ref} {v}{par} -> {other}{tail}')
        for ref, role, other in self.fet_links(net):
            parts.append(f'{ref} {role} ({"drain" if role == "gate" else "gate"} {other})')
        for ref, p in sorted(self.nodes.get(net, [])):
            s = self.sym(ref)
            if ref in self.chips or s in ('R', 'R_Pack04', '2N7002', 'C'):
                continue
            parts.append(f'{ref}.{p}')
        return '; '.join(parts)


def chip_role(D, n):
    for line in (D.__doc__ or '').splitlines():
        m = re.match(r'\s+U(\d)\s+(.+)$', line)
        if m and int(m.group(1)) == n:
            return re.split(r'\s{2,}', m.group(2).strip())[0]
    return D.ROLE.get(f'U{n}', '')


def windows(base, count):
    last = base + count - 1
    w = [b for b in (0, 16) if base >= b and last <= b + 31]
    if w == [0, 16]:
        return 'GPIOBASE 0 or 16'
    if w:
        return f'GPIOBASE {w[0]}'
    return 'no single PIO window (spans more than 32 GPIOs)'


def ranges(gs):
    """[0, 1, 2, 5] -> '0-2, 5'"""
    out, run = [], []
    for g in list(gs) + [None]:
        if run and (g is None or g != run[-1] + 1):
            out.append(f'{run[0]}-{run[-1]}' if len(run) > 2 else ', '.join(map(str, run)))
            run = []
        if g is not None:
            run.append(g)
    return ', '.join(out) if out else 'none'


def static_assert(conds, msg, indent='_Static_assert('):
    """_Static_assert(a && b && ..., "msg"); wrapped at about 116 columns"""
    lines, cur = [], indent
    for i, c in enumerate(conds):
        piece = c + (' &&' if i < len(conds) - 1 else ',')
        if len(cur) + len(piece) + 1 > 116 and cur.strip() != indent.strip():
            lines.append(cur.rstrip())
            cur = ' ' * len(indent)
        cur += piece + ' '
    lines.append(cur.rstrip())
    lines.append(' ' * len(indent) + f'"{msg}");')
    return lines


def link_info(name):
    """'XH1_1' -> ('XLINK-H1', 'U1', 'XH1'); 'WL' -> ('WLINK', 'U1', 'WL')"""
    if name == 'WL':
        return 'WLINK', 'U1', 'WL'
    m = re.match(r'X(\w+?)_(\w+)$', name)
    lk, src = m.group(1), m.group(2)
    drv = f'U{HUB}' if src == 'H' else f'U{src}'
    return f'XLINK-{lk}', drv, f'X{lk}'


def run_text(NL, me, nets):
    """What a run of numbered nets is: the card-edge nets its resistors lead to, else the chips it is shared with."""
    ends = [NL.resistor_ends(net) for net in nets]
    if all(e and e[0][2] in NL.fingers for e in ends):
        refs = sorted({e[0][0] for e in ends}, key=lambda r: (len(r), r))
        r = ends[0][0][1]
        v = f'{r // 1000}k' if r >= 1000 and r % 1000 == 0 else str(r)
        par = f' x{ends[0][0][3]}' if ends[0][0][3] > 1 else ''
        return f'to {ends[0][0][2]}..{ends[-1][0][2]} through {", ".join(refs)} ({v}{par} each)'
    chips = sorted({r for net in nets for r, _ in NL.nodes[net] if r in NL.chips and r != me}, key=lambda r: int(r[1:]))
    return 'shared with ' + ', '.join(chips) if chips else 'on this chip only'


def find_groups(NL, n, pins):
    """pins: {gpio: net}. Returns [(name, [gpio...], text)] in GPIO order."""
    by_net = {net: g for g, net in pins.items() if net}
    groups, in_triplet = [], set()
    # link triplets: <prefix>_CK, _D0, _D1 on consecutive GPIOs
    for g in sorted(pins):
        net = pins[g]
        if not net or not net.endswith('_CK'):
            continue
        pre = net[:-3]
        trio = [pre + '_CK', pre + '_D0', pre + '_D1']
        gs = [by_net.get(t) for t in trio]
        if None in gs:
            continue
        assert gs == [g, g + 1, g + 2], (n, trio, gs)
        lk, drv, _ = link_info(pre)
        way = 'sent' if drv == f'U{n}' else 'received'
        groups.append((pre, gs, f'{lk} {way} by this chip ({drv} drives clock, data 0, data 1)'))
        in_triplet.update(trio)
    # SWD pairs (hub): SWCLK<k>, SWDIO<k> on consecutive GPIOs
    for g in sorted(pins):
        m = re.match(r'SWCLK(\d)$', pins[g] or '')
        if m and by_net.get(f'SWDIO{m.group(1)}') == g + 1:
            groups.append((f'SWD{m.group(1)}', [g, g + 1], f'SWD of U{m.group(1)}: SWCLK, SWDIO (software SWD from SIO; PIO only for the debugprobe fallback)'))
    # runs of numbered nets (CA0..CA14, PA10..PA13, SD_DAT0..3, XSTAT0..1, IRQ4..5): consecutive numbers on consecutive GPIOs
    fam = {}
    for net, g in by_net.items():
        m = re.match(r'(.*?[A-Z_])(\d+)$', net)
        if m and net not in in_triplet and not re.match(r'SW(CLK|DIO)\d$', net) and not re.match(r'LED\d$', net):
            fam.setdefault(m.group(1), []).append((int(m.group(2)), g, net))
    for pre, items in fam.items():
        items.sort()
        run = [items[0]]
        for it in items[1:] + [None]:
            if it and it[0] == run[-1][0] + 1 and it[1] == run[-1][1] + 1:
                run.append(it)
                continue
            if len(run) >= 2:
                first, last = run[0][0], run[-1][0]
                name = pre.rstrip('_') if first == 0 else f'{pre}{first}_{last}'
                groups.append((name, [x[1] for x in run], run_text(NL, f'U{n}', [x[2] for x in run])))
            run = [it] if it else []
    # docs/13 groups
    for chip, name, a, b, text in MANUAL_GROUPS:
        if chip != n:
            continue
        ga, gb = by_net[a], by_net[b]
        gs = list(range(ga, gb + 1))
        assert all(pins.get(g) for g in gs), (n, name, 'gap in', a, b)
        groups.append((name, gs, text))
    names = [x[0] for x in groups]
    assert len(names) == len(set(names)), (n, names)
    return sorted(groups, key=lambda x: (x[1][0], -len(x[1]), x[0]))


def gen_chip(D, NL, n):
    ref = f'U{n}'
    pins = {}
    for g in range(NGPIO):
        net = D.NETS[ref].get(str(D.GPIO_PIN[g]))
        assert net == D.G[n][g], (ref, g, net, D.G[n][g])         # the table and the netlist agree
        pins[g] = net
    other = {p: D.NETS[ref].get(str(p)) for p in (33, 34, 35, 66, 67)}
    flash = next(r for r, pp in D.NETS.items() if D.PARTS[r][1] == 'W25Q128JVS' and pp.get('1') == f'QSPI{n}_SS')
    led = next(net for net in pins.values() if net and re.match(r'LED\d$', net))
    led_d = next(r for r, _ in NL.nodes[f'{led}_A'] if NL.sym(r) == 'LED')
    link = next((net for net in pins.values() if net and re.match(r'LINK_[A-F]$', net)), None)
    used = [g for g in range(NGPIO) if pins[g]]
    free = [g for g in range(NGPIO) if not pins[g]]
    console = [g for g in used if NL.reaches_console(pins[g])]
    width = max(len('PIN_' + cname(pins[g])) for g in used)

    L = []
    w = L.append
    w('/* Generated by tools/fw/gen_revh_pins.py from tools/pcb/design_revh.py -- do not edit; run the script again.')
    w(f' * famicart rev H, {ref}: {chip_role(D, n)}.')
    w(f' * RP2350B (QFN-80) with {flash} (W25Q128JVSIQ, 16 MB) on QSPI CS0, its own 12 MHz crystal, LED {led_d} on {led}.')
    w(f' * SWCLK (pin 33) {other[33]}, SWDIO (pin 34) {other[34]}, RUN (pin 35) {other[35]}' +
      (f', USB D- / D+ (pins 66 / 67) {other[66]} / {other[67]} (27 ohm to J7)' if other[66] else ', USB pins 66 / 67 open') + '.')
    w(' * "pin" below is the QFN-80 pin (design_revd.GPIO_PIN, checked against the datasheet). Include exactly one')
    w(' * pins_u<N>.h per program: the names repeat across chips with other numbers. */')
    guard = f'FAMICART_REVH_PINS_U{n}_H'
    w(f'#ifndef {guard}')
    w(f'#define {guard}')
    w('')
    w(f'#define REVH_CHIP_{n} 1')
    w(f'#define REVH_CHIP {n}')
    w(f'#define REVH_ROLE "{D.ROLE.get(ref, "")}"')
    w(f'#define REVH_IS_HUB {1 if n == HUB else 0}')
    w('')
    w('/* ---- every connected GPIO: pin, net, what else is on the net */')
    for g in used:
        net = pins[g]
        name = 'PIN_' + cname(net)
        desc = NL.describe(net, ref)
        w(f'#define {name:<{width}} {g:2d}  /* pin {D.GPIO_PIN[g]:2d}  {net}{": " + desc if desc else ""} */')
    w('')
    w(f'/* ---- GPIOs with no net (reset state: input buffer off, pad pull-down, isolated): {ranges(free)} */')
    w(f'#define REVH_UNCONNECTED_MASK 0x{sum(1 << g for g in free):012x}ull')
    w(f'/* ---- pins whose net reaches the console\'s card edge through the resistor arrays or a FET: {ranges(console)}')
    w(' * (programs that do not serve the bus keep them inputs without pulls, docs/13 "ファームウェアの決まりと課題") */')
    w(f'#define REVH_CONSOLE_MASK 0x{sum(1 << g for g in console):012x}ull')
    w('')
    w('/* ---- consecutive groups for PIO programs (in / out / set / side-set base and count). The PIO window is the')
    w(' * GPIOBASE (0 or 16) whose 32 GPIOs hold the whole group; with GPIOBASE 16, `wait gpio` numbers are relative. */')
    for name, gs, text in find_groups(NL, n, pins):
        base, cnt = gs[0], len(gs)
        mem = [pins[g] for g in gs]
        w(f'/* {name}: {mem[0]}..{mem[-1]}, {text}; PIO window {windows(base, cnt)} */')
        w(f'#define PIN_{name}_BASE  {base}')
        w(f'#define PIN_{name}_COUNT {cnt}')
        conds = [f'PIN_{cname(m)} == PIN_{name}_BASE + {i}' for i, m in enumerate(mem)]
        L.extend(static_assert(conds, f'{name}: {mem[0]}..{mem[-1]} must be consecutive GPIOs'))
        if pins[gs[0]].endswith('_CK') and name != 'WL':
            lk, drv, short = link_info(name)
            way = 'TX' if drv == ref else 'RX'
            w(f'#define PIN_{short}_{way}_BASE  PIN_{name}_BASE')
            w(f'#define PIN_{short}_{way}_COUNT PIN_{name}_COUNT')
    w('')
    w('/* ---- names shared by every chip */')
    w(f'#define PIN_LED PIN_{cname(led)}')
    if link:
        w(f'#define PIN_LINK PIN_{cname(link)}       /* 250 ohm to the common LINK (U1-U6) */')
    w('')
    w(f'#endif /* {guard} */')
    return '\n'.join(L) + '\n', pins


def adc_divider(NL, net):
    """(r_top, top net, top ref, r_bottom, bottom ref) of the resistors on an ADC input; r_bottom 0 = series only"""
    top = bot = None
    for ref, r, other, _ in NL.resistor_ends(net):
        if other == 'GND':
            bot = (r, ref)
        else:
            top = (r, other, ref)
    assert top, net
    return top[0], top[1], top[2], (bot[0] if bot else 0), (bot[1] if bot else None)


def gen_hub(D, NL, pins):
    by_net = {net: g for g, net in pins.items() if net}
    L = []
    w = L.append
    w('/* Generated by tools/fw/gen_revh_pins.py from tools/pcb/design_revh.py -- do not edit; run the script again.')
    w(' * famicart rev H, U6 (hub): the hub\'s functions under the names docs/13 gives them ("ピン割り当て", "移植の一覧"),')
    w(' * on top of pins_u6.h. GPIO function numbers come from the SDK\'s hardware/regs/io_bank0.h by name: a pin that')
    w(' * does not have the function stops the build. */')
    w('#ifndef FAMICART_REVH_PINS_HUB_H')
    w('#define FAMICART_REVH_PINS_HUB_H')
    w('#include "pins_u6.h"')
    w('#include "hardware/platform_defs.h"          /* _u() for the register headers */')
    w('#include "hardware/regs/io_bank0.h"')
    w('')

    def fn(net, func):
        g = by_net[net]
        return f'IO_BANK0_GPIO{g}_CTRL_FUNCSEL_VALUE_{func}'

    def spi_role(g):
        return ('RX', 'SS_N', 'SCLK', 'TX')[g & 3], (g >> 3) & 1
    for role, net in (('SCLK', 'SD_CLK'), ('TX', 'SD_CMD'), ('RX', 'SD_DAT0')):
        r, inst = spi_role(by_net[net])
        assert (r, inst) == (role, 0), (net, r, inst)
    ss = [g for g in range(NGPIO) if spi_role(g) == ('SS_N', 0)]                 # SPI0 CSn: GPIO1, 5, 17, 21, 33, 37
    assert by_net['SD_DAT3'] not in ss and all(pins[g] for g in ss), ss
    ss_text = ', '.join(f'{g} {pins[g]}' for g in ss)
    w('/* microSD (J3) on SPI0: SCK = SD_CLK, TX = SD_CMD, RX = SD_DAT0. The chip select DAT3 / CS (GPIO7) is driven by')
    w(f' * SIO: SPI0\'s own CSn only reaches GPIO{" / ".join(map(str, ss))}, and on the hub each of them carries something')
    w(f' * else ({ss_text}). 4-bit SD by PIO uses PIN_SD_BASE /')
    w(' * PIN_SD_COUNT. Card detect on SD_CD with the pad pull-up (no resistor on the board). */')
    w('#define HUB_SD_SPI_INDEX    0')
    w('#define HUB_SD_SPI_SCK_PIN  PIN_SD_CLK')
    w('#define HUB_SD_SPI_TX_PIN   PIN_SD_CMD')
    w('#define HUB_SD_SPI_RX_PIN   PIN_SD_DAT0')
    w('#define HUB_SD_SPI_CS_PIN   PIN_SD_DAT3         /* software chip select (SIO), 10k pull-up on the board */')
    w('#define HUB_SD_CD_PIN       PIN_SD_CD')
    w(f'#define HUB_SD_SPI_SCK_FUNC {fn("SD_CLK", "SPI0_SCLK")}')
    w(f'#define HUB_SD_SPI_TX_FUNC  {fn("SD_CMD", "SPI0_TX")}')
    w(f'#define HUB_SD_SPI_RX_FUNC  {fn("SD_DAT0", "SPI0_RX")}')
    for pin, net in (('SCK', 'SD_CLK'), ('TX', 'SD_CMD'), ('RX', 'SD_DAT0')):
        w(f'_Static_assert(HUB_SD_SPI_{pin}_PIN == {by_net[net]}, "the function name above is for GPIO{by_net[net]}");')
    w('')
    w('/* ADC: on the RP2350B (QFN-80) ADC0-7 are GPIO40-47 (the SDK\'s ADC_BASE_PIN with PICO_RP2350A 0).')
    w(' * volts at the source = volts at the pin x (R_TOP + R_BOTTOM) / R_BOTTOM; R_BOTTOM 0 = a series resistor only. */')
    w('#define HUB_ADC_BASE_PIN 40')
    for key, net in (('V5S', 'V5S'), ('EXT', 'EXT'), ('VBUS_S', 'VBUS_S')):
        rt, tnet, tref, rb, bref = adc_divider(NL, net)
        k = f'HUB_ADC_{key}_'
        w(f'#define {k + "PIN":<24} PIN_{cname(net)}')
        w(f'#define {k + "CH":<24} (PIN_{cname(net)} - HUB_ADC_BASE_PIN)   /* ADC{by_net[net] - 40} */')
        w(f'#define {k + "R_TOP":<24} {rt:<6} /* {tref}: {tnet} - {net} */')
        w(f'#define {k + "R_BOTTOM":<24} {rb:<6} /* {bref + ": " + net + " - GND" if bref else "none (series resistor only)"} */')
    rt, _, tref, rb, bref = adc_divider(NL, 'FB_3V3')
    vref = round(TLV62569_VFB_MV * (rt + rb) / rb)
    w(f'/* ADC reference = ADC_AVDD = +3V3: {TLV62569_VFB_MV} mV x ({rt} + {rb}) / {rb} ({tref} / {bref} on the TLV62569\'s FB),')
    w(' * nominal; the resistor and reference tolerances make it 3.21-3.45 V (docs/13 "電源"). */')
    w(f'#define HUB_ADC_VREF_MV {vref}')
    w('/* USB D+ pull-up only while VBUS_S (VBUS / 2) is above about 1.5 V (docs/13 "起動・書き込み・リセット", 決まり) */')
    w('#define HUB_VBUS_S_ON_MV  1500')
    w('#define HUB_VBUS_S_OFF_MV 1400')
    w('')

    def pwm(net):
        g = by_net[net]
        sl = (g >> 1) & 7 if g < 32 else 8 + ((g >> 1) & 3)          # RP2350 GPIO -> PWM slice (datasheet GPIO table)
        return sl, g & 1
    s, c = pwm('HM2')
    assert (s, c) == (8, 1), (s, c)
    w('/* PWM: HM2 = the console\'s M2 through its own 1k (RN18); measuring the duty needs a B (input) channel. PWM2 =')
    w(' * the hub\'s audio output into the RC filter of AUDIO_OUT (RN19). */')
    w('#define HUB_HM2_PIN        PIN_HM2')
    w(f'#define HUB_HM2_PWM_SLICE  {s}')
    w(f'#define HUB_HM2_PWM_CHAN   {c}   /* B */')
    w(f'#define HUB_HM2_FUNC       {fn("HM2", f"PWM_B_{s}")}')
    s, c = pwm('PWM2')
    w('#define HUB_PWM2_PIN       PIN_PWM2')
    w(f'#define HUB_PWM2_PWM_SLICE {s}')
    w(f'#define HUB_PWM2_PWM_CHAN  {c}   /* {"AB"[c]} */')
    ab = 'AB'[c]
    w(f'#define HUB_PWM2_FUNC      {fn("PWM2", f"PWM_{ab}_{s}")}')
    w(f'_Static_assert(HUB_HM2_PIN == {by_net["HM2"]} && HUB_PWM2_PIN == {by_net["PWM2"]}, "the function names above are for these GPIOs");')
    w('')
    targets = sorted(int(m.group(1)) for net in by_net for m in [re.match(r'SWCLK(\d)$', net)] if m)
    w('/* SWD master of the other seven chips: software SWD from SIO (docs/13 "PIO の割り当て"). At start SWCLK low,')
    w(' * SWDIO pulled up (docs/13 "起動・書き込み・リセット", 決まり). When writing RP-AP CTRL, keep bits 1:0 at 0. */')
    for k in targets:
        w(f'#define HUB_SWD_U{k}_SWCLK PIN_SWCLK{k}')
        w(f'#define HUB_SWD_U{k}_SWDIO PIN_SWDIO{k}')
    w(f'#define HUB_SWD_COUNT {len(targets)}')
    w('#define HUB_SWD_TARGETS     { ' + ', '.join(map(str, targets)) + ' }')
    w('#define HUB_SWD_SWCLK_PINS  { ' + ', '.join(f'PIN_SWCLK{k}' for k in targets) + ' }')
    w('#define HUB_SWD_SWDIO_PINS  { ' + ', '.join(f'PIN_SWDIO{k}' for k in targets) + ' }')
    w('/* the same pins as GPIO masks, for compile-time checks against REVH_CONSOLE_MASK */')
    for sig in ('SWCLK', 'SWDIO'):
        terms = [f'(1ull << PIN_{sig}{k})' for k in targets]
        head = f'#define HUB_SWD_{sig}_MASK ('
        lines, cur = [], head
        for i, t in enumerate(terms):
            piece = t + (' | ' if i < len(terms) - 1 else ')')
            if len(cur) + len(piece) > 114:
                lines.append(cur.rstrip() + ' \\')
                cur = ' ' * len(head)
            cur += piece
        lines.append(cur)
        L.extend(lines)
    w('')
    w('/* Reset and core voltage: nRST pulls RUN of U1-U5, U8, U9 low (open drain; 10k pull-up on the board). VSEL')
    w(' * (net VSEL_S) turns Q7 on and raises +1V1 to about 1.122 V; 100k pull-down on the board. */')
    w('#define HUB_NRST_PIN       PIN_NRST')
    w('#define HUB_VSEL_PIN       PIN_VSEL_S')
    w('')
    w('/* U7: second W25Q128JVSIQ on QMI chip select 1 (2.2k pull-up keeps it deselected during boot). The boot ROM')
    w(' * treats CS1 as absent until the firmware sets FLASH_DEVINFO; the read format of window 1 is QMI m[1]. */')
    w('#define HUB_XIP_CS1_PIN    PIN_QSPI6_SS1')
    w(f'#define HUB_XIP_CS1_FUNC   {fn("QSPI6_SS1", "XIP_SS_N_1")}')
    w(f'_Static_assert(HUB_XIP_CS1_PIN == {by_net["QSPI6_SS1"]}, "the function name above is for GPIO{by_net["QSPI6_SS1"]}");')
    w('')
    w('/* Links (receive / send as seen from the hub) and the rest */')
    w('#define HUB_LINK_PIN       PIN_LINK_F           /* LINK (U1-U6), 250 ohm */')
    w('#define HUB_PLINK_PIN      PIN_PLINK_F          /* PLINK to U2 / U5, 500 ohm each */')
    w('#define HUB_WLINK_RX_BASE  PIN_WL_BASE          /* WLINK from U1 */')
    w('#define HUB_XH1_RX_BASE    PIN_XH1_RX_BASE      /* XLINK-H1 from U1 */')
    w('#define HUB_XH1_TX_BASE    PIN_XH1_TX_BASE      /* XLINK-H1 to U1 */')
    w('#define HUB_XH2_RX_BASE    PIN_XH2_RX_BASE      /* XLINK-H2 from U2 */')
    w('#define HUB_XH2_TX_BASE    PIN_XH2_TX_BASE      /* XLINK-H2 to U2 */')
    w('#define HUB_HIRQ_PIN       PIN_HIRQ             /* interrupt request to U3 */')
    w('#define HUB_EXT_PIN        PIN_EXT              /* J4, 0-3.3 V only */')
    w('#define HUB_LED_PIN        PIN_LED6')
    w('')
    w('#endif /* FAMICART_REVH_PINS_HUB_H */')
    return '\n'.join(L) + '\n'


def generate():
    D = load_design()
    assert set(CHIPS) == set(D.G), sorted(D.G)
    NL = Netlist(D)
    files = {}
    for n in CHIPS:
        text, pins = gen_chip(D, NL, n)
        files[f'pins_u{n}.h'] = text
        if n == HUB:
            files['pins_hub.h'] = gen_hub(D, NL, pins)
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='exit 1 if a header in src/revh differs from what the design gives')
    ap.add_argument('--out', default=OUT, help='output directory (default: famicart/src/revh)')
    a = ap.parse_args()
    files = generate()
    if a.check:
        bad = 0
        for name, text in sorted(files.items()):
            path = os.path.join(a.out, name)
            old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
            if old != text:
                bad += 1
                print(f'stale: {path}' if old is not None else f'missing: {path}')
                if old is not None:
                    diff = list(difflib.unified_diff(old.splitlines(), text.splitlines(), 'file', 'design', lineterm='', n=0))
                    print('\n'.join(diff[:20]) + ('\n  ...' if len(diff) > 20 else ''))
        extra = sorted(f for f in os.listdir(a.out) if re.match(r'pins_u\d+\.h$', f) and f not in files) if os.path.isdir(a.out) else []
        for f in extra:
            bad += 1
            print(f'not in the design: {os.path.join(a.out, f)}')
        print(f'{len(files)} headers, {bad} stale' if bad else f'{len(files)} headers up to date')
        return 1 if bad else 0
    os.makedirs(a.out, exist_ok=True)
    for name, text in sorted(files.items()):
        path = os.path.join(a.out, name)
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        if old != text:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            print('wrote', path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
