#!/usr/bin/env python3
"""Board outline and placement plan of the Famicom JAMMA board (the starting point of stage 2, not a finished layout).

    python3 mech/floorplan.py      # writes mech/board_outline_plan.svg and, with Chromium, mech/board_outline_plan.png

Dimensions are millimetres.  Origin: lower left corner of the bounding box, seen from the parts side with the
JAMMA fingers pointing down; y = 0 is the tip of the fingers, x runs to the right, y upwards.
Before it draws, the script checks that the large parts lie inside the outline and do not overlap each other,
the mounting holes or the space the cartridge shell needs, that the through-hole parts keep 2.5 mm from the body's edges
and every part and zone 2.5 mm from the edges without a rail (JLCPCB), and that no part or zone reaches into the JAMMA
band or the keep-out beside a rail tab.  tools/build.py runs the same check and compares the dimensions with
design/board.py.

Where the fixed dimensions come from
- JAMMA edge: research_notes/ファミコン JAMMA 基板 仕様調査/reference/02_jamma_interface.md section 1.2.3
  (pitch 3.96, tongue 114.4 wide, key slot 3.0 x 11.5 at finger 7, outer finger 3.74 from the side);
  design/footprints.py (fingers from 1.6 to 10.0; no part within 15 mm of the tip, nor within 5 mm of a finger
  beside the tongue's root)
- 60-pin connector ED60BGFBK (C5173310): maker's drawing, body 82.49 x 9.25, 15.6 high
- Famicom cartridge shell: about 108 x 17 mm seen from above, about 70 mm tall (published figures differ; to be measured)
- Raspberry Pi Pico 2: KiCad courtyard of Module:RaspberryPi_Pico_SMD, 53.9 x 23.1; DIP-40 socket courtyard 51.4 x 18.3
- USB-C HRO TYPE-C-31-M-12: about 8.9 wide, 7.3 deep
- edge rails (design/board.py): 5 mm on the left and right, a 2 mm slot, joined by tabs (5.5 mm at the narrowest) with mouse bites
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ outline
BODY_W, BODY_H = 220.0, 150.0          # board body
TONGUE_W, TONGUE_L = 114.4, 12.0       # JAMMA tongue with the gold fingers, below the body
TONGUE_X0 = (BODY_W - TONGUE_W) / 2    # 52.8
Y0 = TONGUE_L                          # the body starts 12 mm above the finger tips
TOP = Y0 + BODY_H                      # 162
PITCH, FINGER_W, FINGER_Y = 3.96, 2.30, (1.6, 10.0)
JAMMA_KEEP = 15.0                      # no part within 15 mm of the tip (J1's courtyard)
FINGER1_X = TONGUE_X0 + 3.74           # centre of finger 1
KEY_X, KEY_W, KEY_D = FINGER1_X + 6 * PITCH, 3.0, 11.5
RAIL_W = 5.0                           # JLCPCB edge rails (manufacturing only), on the left and right sides
RAIL_GAP = 2.0                         # routed slot between the rail and the body
TAB_W = 5.5                            # tabs with mouse bites that join the rails to the body (narrowest width)
TABS = (32.0, 48.0, 112.0, 130.0, 145.0)   # tab centres (y), the same on both sides
TAB_KEEP, TAB_KEEP_H = 5.6, 8.5        # no part within 5 mm of a tab's mouse bites (into the body, ±8.5 along the edge)

# ------------------------------------------------------------------ large parts: name -> (x, y, w, h, kind, label, height above the board)
PARTS = {
    "J8":  (68.76, 144.87, 82.49, 9.25, "conn", "J8 カセット端子（60 ピン）", 15.6),
    "U1":  (6.0, 104.0, 51.4, 18.3, "socket", "U1 CPU（RP2A03）用ソケット", 9.0),
    "U6":  (162.6, 104.0, 51.4, 18.3, "socket", "U6 PPU（RP2C02）用ソケット", 9.0),
    "U27": (2.0, 60.0, 53.9, 23.1, "pico", "U27 Pico 2 C（入出力・管理）", 4.0),
    "U26": (83.0, 76.0, 53.9, 23.1, "pico", "U26 Pico 2 B（バス）", 4.0),
    "U25": (140.0, 54.0, 53.9, 23.1, "pico", "U25 Pico 2 A（映像）", 4.0),
    "J10": (0.0, 85.0, 7.4, 9.0, "conn", "J10\nUSB-C", 3.3),
    "SW4": (12.0, 89.0, 5.2, 5.2, "sw", "SW4\nRESET", 1.6),
    "SW5": (20.0, 89.0, 5.2, 5.2, "sw", "SW5\nBOOT", 1.6),
    "SW3": (200.0, 84.0, 12.4, 9.8, "sw", "SW3\nDIP スイッチ", 6.0),
    "SW1": (200.0, 70.0, 5.2, 5.2, "sw", "SW1\nTEST", 1.6),
    "SW2": (207.5, 70.0, 5.2, 5.2, "sw", "SW2\nSERVICE", 1.6),
    "RV1": (88.0, 40.0, 7.0, 7.0, "sw", "RV1\n音量", 7.0),
    "C1":  (40.0, 20.0, 6.9, 6.9, "cap", "C1\n470µF", 7.7),
    "J3":  (6.0, 125.0, 51.8, 6.1, "opt", "J3 CPU バス（未実装）", 0.0),
    "J7":  (162.2, 125.0, 51.8, 6.1, "opt", "J7 PPU バス（未実装）", 0.0),
}
SHELL = (56.0, 141.0, 108.0, 17.0)      # where the cartridge shell stands: nothing taller than about 1 mm here
CART_TOP = 80.0                         # top of an inserted cartridge above the board (estimate, to be measured)
# areas for the small parts of each function: name -> (x, y, w, h, label)
ZONES = {
    "power": (9.0, 16.0, 43.0, 34.0, "電源\nヒューズ・保護・\n電源スイッチ・3.3V"),
    "coil":  (56.0, 15.5, 44.0, 8.5, "コイン用出力（4 本）"),
    "audio": (56.0, 26.0, 44.0, 24.0, "音声\nミキサー・アンプ"),
    "jamma": (104.0, 15.5, 108.0, 34.5, "JAMMA の入力 25 本と出力\n抵抗・コンデンサ・シフトレジスタ"),
    "dac":   (84.0, 54.0, 54.0, 18.0, "映像 DAC（RGB・同期）"),
    "mcu":   (58.0, 54.0, 22.0, 44.0, "Pico 間の\n配線部品"),
    "cpu":   (60.0, 102.0, 47.0, 37.0, "CPU まわり\nRAM・デコーダ・\nバスの抵抗"),
    "ppu":   (113.0, 102.0, 47.0, 37.0, "PPU まわり\nRAM・ラッチ・\n比較器"),
    "dumpL": (8.0, 133.0, 46.0, 25.0, "読み出し回路\n（CPU 側）"),
    "dumpR": (166.0, 133.0, 46.0, 25.0, "読み出し回路\n（PPU 側）"),
}
HOLES = [(4.0, 16.0), (216.0, 16.0), (4.0, 158.0), (216.0, 158.0), (4.0, 99.0), (216.0, 99.0), (110.0, 121.0)]   # M3, 3.2 mm
GUIDE_HOLES = [(52.0, 149.5), (168.0, 149.5)]   # for a bracket that holds the cartridge (not plated)
THT = ("U1", "U6", "J8", "SW3", "RV1")         # the through-hole parts (README chapter 8: at least 2.5 mm from the board's edges)
THT_EDGE = 2.5
EDGE_PARTS = 2.5     # JLCPCB assembly terms 2.3: every part's body 2.5 mm from the board's edge; the rails give it on the left and right


def check():
    """Large parts inside the outline and clear of each other, of the holes and of the cartridge shell."""
    problems = []

    def overlap(a, b, gap=0.0):
        return a[0] < b[0] + b[2] + gap and b[0] < a[0] + a[2] + gap and a[1] < b[1] + b[3] + gap and b[1] < a[1] + a[3] + gap

    names = list(PARTS)
    for i, n in enumerate(names):
        box = PARTS[n][:4]
        x, y, w, h = box
        if not (0.0 <= x and x + w <= BODY_W and Y0 <= y and y + h <= TOP):
            problems.append(f"{n} is outside the board body")
        for m in names[i + 1:]:
            if overlap(box, PARTS[m][:4], 0.5):
                problems.append(f"{n} overlaps {m}")
        if n != "J8" and overlap(box, SHELL):
            problems.append(f"{n} stands where the cartridge shell goes")
        for hx, hy in HOLES + GUIDE_HOLES:
            if overlap(box, (hx - 3.5, hy - 3.5, 7.0, 7.0)):
                problems.append(f"{n} overlaps the hole at ({hx}, {hy})")
    for hx, hy in HOLES:
        if not (3.5 <= hx <= BODY_W - 3.5 and Y0 + 3.5 <= hy <= TOP - 3.5):
            problems.append(f"hole at ({hx}, {hy}) is closer than 3.5 mm to the edge")
    if not (SHELL[0] >= 0 and SHELL[0] + SHELL[2] <= BODY_W and SHELL[1] + SHELL[3] <= TOP - 3.0):
        problems.append("the cartridge shell area is not inside the board")
    if not (SHELL[0] <= PARTS["J8"][0] and PARTS["J8"][0] + PARTS["J8"][2] <= SHELL[0] + SHELL[2]):
        problems.append("J8 is not centred under the cartridge shell")
    if TONGUE_X0 < 10.0:
        problems.append("no room beside the tongue for the ears of the cabinet's connector")
    if PARTS["J10"][0] < 0.0:
        problems.append("the USB socket must not stick out over the edge: the edge rail is attached there")
    for n in THT:
        x, y, w, h = PARTS[n][:4]
        d = min(x, BODY_W - (x + w), y - Y0, TOP - (y + h))
        if d < THT_EDGE:
            problems.append(f"{n} (through hole) is {d:.2f} mm from the body's edge, less than {THT_EDGE:g}")
    for n, box in [(n, PARTS[n][:4]) for n in PARTS] + [(f"zone '{n}'", ZONES[n][:4]) for n in ZONES]:
        x, y, w, h = box
        beside = x < TONGUE_X0 or x + w > TONGUE_X0 + TONGUE_W          # over the body's lower edge, not over the tongue
        d = min(TOP - (y + h), (y - Y0) if beside else 99.0)
        if d < EDGE_PARTS:
            problems.append(f"{n} is {d:.2f} mm from an edge without a rail (the top, or the body's lower edge beside the "
                            f"tongue), less than {EDGE_PARTS:g}")
    # the JAMMA band: J1's courtyard, to 15 mm above the tip and 5 mm past the outer fingers' copper
    band = (FINGER1_X - FINGER_W / 2 - 5.0, 0.0, 27 * PITCH + FINGER_W + 10.0, JAMMA_KEEP)
    keep = [(x0, t - TAB_KEEP_H, TAB_KEEP, 2 * TAB_KEEP_H) for t in TABS for x0 in (0.0, BODY_W - TAB_KEEP)]
    for n, box in [(n, PARTS[n][:4]) for n in PARTS] + [(f"zone '{n}'", ZONES[n][:4]) for n in ZONES]:
        if overlap(box, band):
            problems.append(f"{n} reaches into the JAMMA band (no part within {JAMMA_KEEP:g} mm of the tip)")
        if any(overlap(box, kb) for kb in keep):
            problems.append(f"{n} is within {TAB_KEEP:g} mm of a rail tab's mouse bites")
    for t in TABS:
        if not (Y0 + 2.0 + TAB_W / 2 + RAIL_GAP / 2 <= t <= TOP - 2.0 - TAB_W / 2 - RAIL_GAP / 2):
            problems.append(f"the tab at y {t:g} does not fit between the body's rounded corners")
    if any(b - a < TAB_W + RAIL_GAP + 2.0 for a, b in zip(TABS, TABS[1:])):
        problems.append("two tabs are too close to leave a slot between them")
    return problems


# ------------------------------------------------------------------ drawing helpers
S = 5.0                      # px per mm in the top view
MX, MY = 170.0, 110.0        # position of the top view on the page
PAGE_W, PAGE_H = 1700, 1660
FONT = "IPAPGothic, 'IPA Pゴシック', 'Noto Sans CJK JP', sans-serif"
COL = {"socket": "#c8c8c8", "pico": "#86c995", "conn": "#f2c27a", "sw": "#9dbde8", "cap": "#d8b2e6", "opt": "#ffffff"}


def shade(hexcol, k):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * k))) for c in (r, g, b))


def X(x):
    return MX + x * S


def Y(y):
    return MY + (TOP - y) * S


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=13, anchor="middle", weight="normal", fill="#111", rot=None):
    out = []
    lines = s.split("\n")
    for i, line in enumerate(lines):
        yy = y + (i - (len(lines) - 1) / 2) * size * 1.25
        tr = f' transform="rotate({rot} {x:.1f} {yy:.1f})"' if rot else ""
        out.append(f'<text x="{x:.1f}" y="{yy:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}" '
                   f'dominant-baseline="middle"{tr}>{esc(line)}</text>')
    return "\n".join(out)


def rect(x, y, w, h, fill, stroke="#333", sw=1.2, dash=None, rx=0, opacity=1.0):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{X(x):.1f}" y="{Y(y + h):.1f}" width="{w * S:.1f}" height="{h * S:.1f}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" rx="{rx}" fill-opacity="{opacity}"{d}/>')


def arrow_line(x1, y1, x2, y2):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#b00" stroke-width="1.3" '
            'marker-start="url(#a)" marker-end="url(#a)"/>')


def dim_h(x1, x2, y, label, off):
    yy = Y(y) + off
    return "\n".join([
        arrow_line(X(x1), yy, X(x2), yy),
        f'<line x1="{X(x1):.1f}" y1="{yy - 9:.1f}" x2="{X(x1):.1f}" y2="{Y(y):.1f}" stroke="#b00" stroke-width="0.8"/>',
        f'<line x1="{X(x2):.1f}" y1="{yy - 9:.1f}" x2="{X(x2):.1f}" y2="{Y(y):.1f}" stroke="#b00" stroke-width="0.8"/>',
        text((X(x1) + X(x2)) / 2, yy - 12, label, 15, fill="#b00", weight="bold")])


def dim_v(y1, y2, x, label, off):
    xx = X(x) + off
    return "\n".join([
        arrow_line(xx, Y(y1), xx, Y(y2)),
        f'<line x1="{xx - 9:.1f}" y1="{Y(y1):.1f}" x2="{X(x):.1f}" y2="{Y(y1):.1f}" stroke="#b00" stroke-width="0.8"/>',
        f'<line x1="{xx - 9:.1f}" y1="{Y(y2):.1f}" x2="{X(x):.1f}" y2="{Y(y2):.1f}" stroke="#b00" stroke-width="0.8"/>',
        text(xx - 13, (Y(y1) + Y(y2)) / 2, label, 15, fill="#b00", weight="bold", rot=-90)])


def outline_path():
    r = 2.0
    kx0, kx1 = KEY_X - KEY_W / 2, KEY_X + KEY_W / 2
    tx0, tx1 = TONGUE_X0, TONGUE_X0 + TONGUE_W
    pts = [("M", r, Y0), ("L", tx0, Y0), ("L", tx0, 0.5), ("L", tx0 + 0.5, 0), ("L", kx0, 0), ("L", kx0, KEY_D), ("L", kx1, KEY_D),
           ("L", kx1, 0), ("L", tx1 - 0.5, 0), ("L", tx1, 0.5), ("L", tx1, Y0), ("L", BODY_W - r, Y0), ("Q", BODY_W, Y0, BODY_W, Y0 + r),
           ("L", BODY_W, TOP - r), ("Q", BODY_W, TOP, BODY_W - r, TOP), ("L", r, TOP), ("Q", 0, TOP, 0, TOP - r), ("L", 0, Y0 + r),
           ("Q", 0, Y0, r, Y0)]
    d = []
    for p in pts:
        if p[0] == "Q":
            d.append(f"Q {X(p[1]):.1f} {Y(p[2]):.1f} {X(p[3]):.1f} {Y(p[4]):.1f}")
        else:
            d.append(f"{p[0]} {X(p[1]):.1f} {Y(p[2]):.1f}")
    return " ".join(d) + " Z"


# ------------------------------------------------------------------ views
def top_view():
    o = []
    # edge rails (manufacturing only), the slot beside them and the tabs that join them to the body
    for rx in (-RAIL_GAP - RAIL_W, BODY_W + RAIL_GAP):
        o.append(rect(rx, 0.0, RAIL_W, TOP, "#f3f3f3", "#999", 1.0, dash="6 4"))
    for t in TABS:
        for tx in (-RAIL_GAP, BODY_W):
            o.append(rect(tx, t - TAB_W / 2, RAIL_GAP, TAB_W, "#f3f3f3", "#999", 0.8))
    o.append(text(X(-RAIL_GAP - RAIL_W / 2), Y(80), "捨て基板（製造用。ミシン目で折って外す）", 12, fill="#777", rot=-90))
    o.append(text(X(BODY_W + RAIL_GAP + RAIL_W / 2), Y(80), "捨て基板（製造用。ミシン目で折って外す）", 12, fill="#777", rot=90))
    o.append(f'<path d="{outline_path()}" fill="#e2efdf" stroke="#1d4d1d" stroke-width="2.6"/>')
    for t in TABS:                       # no part within 5 mm of a tab's mouse bites
        for kx in (0.0, BODY_W - TAB_KEEP):
            o.append(rect(kx, t - TAB_KEEP_H, TAB_KEEP, 2 * TAB_KEEP_H, "#fbe3e3", "#c88", 0.6, dash="2 2", opacity=0.8))
    for x, y, w, h, label in ZONES.values():
        o.append(rect(x, y, w, h, "#ffffff", "#6a8f6a", 1.0, dash="6 4", rx=6, opacity=0.6))
        o.append(text(X(x + w / 2), Y(y + h / 2), label, 12, fill="#2f5d2f"))
    x, y, w, h = SHELL
    o.append(rect(x, y, w, h, "url(#hatch)", "#b44", 1.3, dash="4 3"))
    o.append(text(X(x + w / 2), Y(y + 1.9), "カセットの殻が来る範囲（約 108 × 17）。背の高い部品は置かない", 12, fill="#a33", weight="bold"))
    for name, (x, y, w, h, kind, label, _hz) in PARTS.items():
        o.append(rect(x, y, w, h, COL[kind], "#333", 1.4, dash="5 3" if kind == "opt" else None, rx=2))
        if name == "J10":
            o.append(text(X(x + w / 2), Y(y + h / 2), label, 9, fill="#123", weight="bold"))
        elif w * S < 70:
            o.append(text(X(x + w / 2), Y(y) + 8 + 6 * label.count("\n") + 6, label, 10, fill="#123"))
        else:
            o.append(text(X(x + w / 2), Y(y + h / 2), label, 13 if w * S > 200 else 11,
                          weight="bold" if kind in ("socket", "pico", "conn") else "normal"))
    o.append(text(X(2.0) + 4, Y(60 + 23.1 / 2), "USB", 9, anchor="start", fill="#063", weight="bold"))
    for hx, hy in HOLES:
        o.append(f'<circle cx="{X(hx):.1f}" cy="{Y(hy):.1f}" r="{3.0 * S:.1f}" fill="#f6e9a8" stroke="#8a6d00" stroke-width="1"/>')
        o.append(f'<circle cx="{X(hx):.1f}" cy="{Y(hy):.1f}" r="{1.6 * S:.1f}" fill="#ffffff" stroke="#333" stroke-width="1.2"/>')
    for hx, hy in GUIDE_HOLES:
        o.append(f'<circle cx="{X(hx):.1f}" cy="{Y(hy):.1f}" r="{1.6 * S:.1f}" fill="#ffffff" stroke="#b33" stroke-width="1.6"/>')
    for n in range(1, 29):
        if n == 7:
            continue
        cx = FINGER1_X + (n - 1) * PITCH
        o.append(f'<rect x="{X(cx - FINGER_W / 2):.1f}" y="{Y(FINGER_Y[1]):.1f}" width="{FINGER_W * S:.1f}" '
                 f'height="{(FINGER_Y[1] - FINGER_Y[0]) * S:.1f}" fill="#e2b93b" stroke="#8a6d00" stroke-width="0.6"/>')
    o.append(text(X(FINGER1_X), Y(FINGER_Y[1]) - 9, "1", 12, fill="#6b5200", weight="bold"))
    o.append(text(X(FINGER1_X + 27 * PITCH), Y(FINGER_Y[1]) - 9, "28", 12, fill="#6b5200", weight="bold"))
    o.append(text(X(KEY_X), Y(0) + 15, "キー溝（7 番）", 11, fill="#6b5200", weight="bold"))
    o.append(text(X(TONGUE_X0 + TONGUE_W) + 12, Y(6.0), "← 筐体のハーネスのコネクタをここに挿す", 12, anchor="start", fill="#6b5200", weight="bold"))
    # dimensions
    o.append(dim_h(0, BODY_W, TOP, f"{BODY_W:.0f}", -40))
    o.append(dim_v(0, TOP, 0, f"全体 {TOP:.0f}", -78))
    o.append(dim_v(Y0, TOP, 0, f"本体 {BODY_H:.0f}", -44))
    o.append(dim_h(TONGUE_X0, TONGUE_X0 + TONGUE_W, 0, f"JAMMA 差し込み部 {TONGUE_W}", 46))
    o.append(dim_h(0, TONGUE_X0, 0, f"{TONGUE_X0:.1f}", 46))
    o.append(dim_h(TONGUE_X0 + TONGUE_W, BODY_W, 0, f"{BODY_W - TONGUE_X0 - TONGUE_W:.1f}", 46))
    xx = X(BODY_W + RAIL_GAP + RAIL_W) + 22
    o.append(arrow_line(xx, Y(0), xx, Y(Y0)))
    o.append(f'<line x1="{X(TONGUE_X0 + TONGUE_W):.1f}" y1="{Y(0):.1f}" x2="{xx + 8:.1f}" y2="{Y(0):.1f}" stroke="#b00" stroke-width="0.8"/>')
    o.append(text(xx + 10, (Y(0) + Y(Y0)) / 2, f"{TONGUE_L:.0f}", 15, anchor="start", fill="#b00", weight="bold"))
    return "\n".join(o)


def legend(x0, y0):
    items = [("rect", COL["socket"], "IC ソケット（ドナー機の CPU・PPU を挿す）"), ("rect", COL["pico"], "Raspberry Pi Pico 2（基板にはんだ付け）"),
             ("rect", COL["conn"], "コネクタ（カセット端子・USB-C）"), ("rect", COL["sw"], "スイッチ・音量つまみ"),
             ("rect", COL["cap"], "電解コンデンサ"), ("dash", "#6a8f6a", "小さな部品（抵抗・IC など）を置く範囲"),
             ("hatch", "#b44", "カセットの殻が来る範囲"), ("gold", "#e2b93b", "JAMMA 端子（金めっきの接点。両面で 56 本）"),
             ("hole", "#8a6d00", "取り付け穴（M3）"), ("guide", "#b33", "カセットを支える金具用の穴")]
    o = [text(x0, y0, "凡例", 15, anchor="start", weight="bold")]
    for i, (kind, col, label) in enumerate(items):
        y = y0 + 26 + i * 25
        if kind == "rect":
            o.append(f'<rect x="{x0}" y="{y - 9}" width="34" height="18" fill="{col}" stroke="#333"/>')
        elif kind == "dash":
            o.append(f'<rect x="{x0}" y="{y - 9}" width="34" height="18" fill="#fff" stroke="{col}" stroke-dasharray="5 3" rx="4"/>')
        elif kind == "hatch":
            o.append(f'<rect x="{x0}" y="{y - 9}" width="34" height="18" fill="url(#hatch)" stroke="{col}" stroke-dasharray="4 3"/>')
        elif kind == "gold":
            o.append(f'<rect x="{x0 + 12}" y="{y - 10}" width="10" height="20" fill="{col}" stroke="#8a6d00"/>')
        elif kind == "hole":
            o.append(f'<circle cx="{x0 + 17}" cy="{y}" r="9" fill="#f6e9a8" stroke="{col}"/><circle cx="{x0 + 17}" cy="{y}" r="5" fill="#fff" stroke="#333"/>')
        else:
            o.append(f'<circle cx="{x0 + 17}" cy="{y}" r="6" fill="#fff" stroke="{col}" stroke-width="1.6"/>')
        o.append(text(x0 + 46, y, label, 13, anchor="start"))
    return "\n".join(o)


def side_view(ox, oy, s):
    """Seen from the right-hand side: the board's y coordinate runs to the right, heights go up."""
    def sx(v):
        return ox + v * s

    def sy(h):
        return oy - h * s

    o = [text(ox, sy(CART_TOP) - 34, "横から見た図（高さの目安）", 16, anchor="start", weight="bold")]
    o.append(f'<rect x="{sx(-11):.1f}" y="{sy(6.2):.1f}" width="{19.5 * s:.1f}" height="{12.4 * s:.1f}" fill="#f7f7f7" stroke="#777" stroke-dasharray="4 3"/>')
    o.append(text(sx(-1.5), sy(13.5), "筐体側の\nコネクタ", 11, fill="#555"))
    o.append(f'<rect x="{sx(0):.1f}" y="{sy(0.8):.1f}" width="{TOP * s:.1f}" height="{1.6 * s:.1f}" fill="#3e7d3e" stroke="#1d4d1d"/>')
    o.append(f'<rect x="{sx(0):.1f}" y="{sy(0.8):.1f}" width="{FINGER_Y[1] * s:.1f}" height="{1.6 * s:.1f}" fill="#e2b93b" stroke="#8a6d00"/>')
    bars = [("C1", "電解\n7.7"), ("U27", "Pico 2\n約 4"), ("U1", "ソケット＋\nチップ 約 9"), ("J8", "カセット端子\n15.6")]
    for name, label in bars:
        x, y, w, h, kind, _l, hz = PARTS[name]
        o.append(f'<rect x="{sx(y):.1f}" y="{sy(hz + 0.8):.1f}" width="{h * s:.1f}" height="{hz * s:.1f}" fill="{COL[kind]}" stroke="#333"/>')
        if name != "J8":
            o.append(text(sx(y + h / 2), sy(hz + 0.8) - 20, label, 11))
    x, y, w, h = SHELL
    o.append(f'<rect x="{sx(y):.1f}" y="{sy(CART_TOP):.1f}" width="{h * s:.1f}" height="{(CART_TOP - 11.0) * s:.1f}" fill="#f6dede" stroke="#a33" stroke-width="1.5"/>')
    o.append(text(sx(y + h / 2), sy((CART_TOP + 11) / 2), "ファミコンのカセット", 13, rot=-90, fill="#a33", weight="bold"))
    jy = PARTS["J8"][1]
    o.append(f'<line x1="{sx(jy) - 4:.1f}" y1="{sy(9):.1f}" x2="{sx(jy) - 34:.1f}" y2="{sy(30):.1f}" stroke="#555" stroke-width="1"/>')
    o.append(text(sx(jy) - 38, sy(30), "カセット端子\n15.6", 11, anchor="end"))
    xd = sx(TOP) + 26
    o.append(arrow_line(xd, sy(0.8), xd, sy(CART_TOP)))
    o.append(text(xd + 8, sy(CART_TOP / 2), f"約 {CART_TOP:.0f}\n（実物で確認）", 13, anchor="start", fill="#b00", weight="bold"))
    o.append(text(sx(0), oy + 36, "JAMMA 端子の側", 12, anchor="start", fill="#6b5200"))
    o.append(text(sx(TOP), oy + 36, "カセットの側", 12, anchor="end", fill="#a33"))
    o.append(text(sx(30), oy + 62, "基板の厚さ 1.6。部品は表面（部品面）だけに載る", 12, anchor="start", fill="#333"))
    return "\n".join(o)


def oblique_view(ox, oy, s):
    """A simple oblique sketch to give an idea of the shape (depth axis compressed)."""
    def P(x, y, z):
        return ox + (x + 0.50 * y) * s, oy - (0.42 * y + z) * s

    def box(x, y, w, h, z0, z1, col, stroke="#333", op=1.0):
        a, b, c, d = P(x, y, z1), P(x + w, y, z1), P(x + w, y + h, z1), P(x, y + h, z1)
        e, f, g = P(x, y, z0), P(x + w, y, z0), P(x + w, y + h, z0)
        pts = lambda ps: " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in ps)   # noqa: E731
        return (f'<polygon points="{pts((f, g, c, b))}" fill="{shade(col, 0.78)}" stroke="{stroke}" stroke-width="0.8" fill-opacity="{op}"/>'
                f'<polygon points="{pts((e, f, b, a))}" fill="{shade(col, 0.9)}" stroke="{stroke}" stroke-width="0.8" fill-opacity="{op}"/>'
                f'<polygon points="{pts((a, b, c, d))}" fill="{col}" stroke="{stroke}" stroke-width="0.8" fill-opacity="{op}"/>')

    o = [text(ox, P(0, TOP, CART_TOP)[1] - 30, "ななめから見た図（形の目安）", 16, anchor="start", weight="bold")]
    o.append(box(0, Y0, BODY_W, BODY_H, -1.6, 0, "#5f9f5f", "#1d4d1d"))
    o.append(box(TONGUE_X0, 0, TONGUE_W, TONGUE_L, -1.6, 0, "#e2b93b", "#8a6d00"))
    for n in sorted((n for n in PARTS if PARTS[n][6] > 0), key=lambda n: -PARTS[n][1]):
        x, y, w, h, kind, _l, hz = PARTS[n]
        if n == "J8":
            sx0, sy0, sw, sh = SHELL
            o.append(box(sx0, sy0, sw, sh, 11.0, CART_TOP, "#f6dede", "#a33", 0.95))
            cx, cy = P(sx0 + sw / 2, sy0, (11.0 + CART_TOP) / 2)
            o.append(text(cx, cy, "ファミコンのカセット", 14, fill="#a33", weight="bold"))
        o.append(box(x, y, w, h, 0, hz, COL[kind]))
    lx, ly = P(TONGUE_X0 + TONGUE_W / 2, 0, -1.6)
    o.append(text(lx, ly + 20, "JAMMA 端子（筐体のコネクタを挿す）", 12, fill="#6b5200", weight="bold"))
    return "\n".join(o)


def build_svg():
    title = "ファミコン JAMMA 基板　外形と部品配置の案（部品面から見た図・単位 mm）"
    notes = [
        "・外形: 本体 220 × 150 mm の下に、JAMMA 端子の差し込み部（幅 114.4 × 長さ 12）。全体で 220 × 162 mm です。A5 用紙（210 × 148）より少し大きい程度です。捨て基板を含めると 234 × 162 mm です。",
        "・部品はすべて表面に載ります。大きな部品は実寸で、点線の枠は小さな部品を置く予定の範囲です。",
        "・左右の灰色の帯は製造時だけ付く捨て基板（幅 5 mm、本体との間に 2 mm の溝、5 か所のミシン目でつながる）で、ミシン目の横の赤い枠（穴から 5 mm）には部品を置きません。",
        "・これは段階 2（部品配置）の出発点となる案です。配置と配線を進める中で、外形の寸法（目安 ±20 mm）と部品の位置は変わることがあります。",
        "・カセットは基板から垂直に立ちます（高さ 約 80 mm）。カセットの殻の寸法は資料によって 2 mm ほど違うので、端子のサンプルと実物のカセットで確かめてから確定します。",
    ]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}" height="{PAGE_H}" viewBox="0 0 {PAGE_W} {PAGE_H}" font-family="{FONT}">',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         '<path d="M 0 2 L 9 5 L 0 8 z" fill="#b00"/></marker>'
         '<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         '<rect width="8" height="8" fill="#fff6f6"/><line x1="0" y1="0" x2="0" y2="8" stroke="#e2a5a5" stroke-width="2"/></pattern></defs>',
         f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="#ffffff"/>',
         text(PAGE_W / 2, 38, title, 24, weight="bold"),
         top_view(),
         legend(int(X(BODY_W + RAIL_GAP + RAIL_W)) + 70, int(Y(TOP)) + 10)]
    y = Y(0) + 96
    for i, line in enumerate(notes):
        o.append(text(70, y + i * 26, line, 15, anchor="start"))
    o.append(side_view(120, 1480, 3.3))
    o.append(oblique_view(905, 1545, 2.15))
    o.append(text(70, PAGE_H - 30, "大きさの目安: A5 用紙 210 × 148 mm ／ ファミコンのカセット 約 108 × 70 × 17 mm ／ Raspberry Pi Pico 2 は 51 × 21 mm", 14,
                  anchor="start", fill="#444"))
    o.append("</svg>")
    return "\n".join(o)


def main():
    problems = check()
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    out = os.path.join(HERE, "board_outline_plan.svg")
    open(out, "w", encoding="utf-8").write(build_svg())
    print("wrote", os.path.relpath(out, os.path.dirname(HERE)))
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          f"const p=await b.newPage({{viewport:{{width:{PAGE_W},height:{PAGE_H}}},deviceScaleFactor:2}});"
          f"await p.goto('file://{out}');await p.waitForTimeout(300);await p.screenshot({{path:'{out[:-4]}.png'}});await b.close();}})()"
          ".catch(e=>{console.error(e.message);process.exit(1)});")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=HERE)
    print("png:", "written" if r.returncode == 0 else "not rendered (" + (r.stderr.strip()[:160] or "no Chromium") + ")")
    print(f"body {BODY_W:.0f} x {BODY_H:.0f} mm, overall {BODY_W:.0f} x {TOP:.0f} mm, area {(BODY_W * BODY_H + TONGUE_W * TONGUE_L) / 100:.0f} cm2")


if __name__ == "__main__":
    main()
