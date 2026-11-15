"""Sheets drawn from the board's own footprints: a 1:1 check print of the cartridge slot (A4, PDF) and an overview picture.

Both are rendered by Chromium through Playwright (node), as mech/floorplan.py does.  The check print is drawn from the
pad table that tools/check_footprints.py has confirmed KiCad reads, in millimetres on an A4 page, so that it prints at
true size when the printer is set to 100 % ('actual size').
"""
import html
import json
import os
import re
import subprocess

PAGE_W, PAGE_H = 297.0, 210.0


def _t(x, y, s, size, anchor="middle", weight="normal", fill="#000"):
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}" '
            f'font-family="Noto Sans CJK JP, Noto Sans JP, sans-serif">{html.escape(s)}</text>')


def cart_check_svg(pads, footprint_name, sources):
    """pads: {number: {"x":..,"y":..,"w":..,"drill":..}} in the footprint frame (origin at the hole array's centre)."""
    ox, oy = PAGE_W / 2, 105.0           # where the footprint origin lands on the page
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}">',
         '<rect x="0" y="0" width="297" height="210" fill="#fff"/>']
    o.append(_t(12, 14, "J8 カセット端子（WingTAT ED60BGFBK）の実寸の確認用紙", 5.2, "start", "bold"))
    o.append(_t(12, 21, "倍率 100 %（実際のサイズ）で印刷します。「用紙に合わせる」「縮小」は切ってください。部品面（表）から見た図です。", 3.3, "start"))
    o.append(_t(12, 26.5, "TOP VIEW (parts side) — この文字が裏返って見えたら、印刷の設定を直して印刷し直す", 3.0, "start", fill="#444"))
    # scale bars
    x0, y0 = 12.0, 38.0
    o.append(f'<line x1="{x0}" y1="{y0}" x2="{x0 + 100}" y2="{y0}" stroke="#000" stroke-width="0.35"/>')
    for k in range(11):
        h = 2.5 if k % 5 == 0 else 1.5
        o.append(f'<line x1="{x0 + 10 * k}" y1="{y0 - h}" x2="{x0 + 10 * k}" y2="{y0}" stroke="#000" stroke-width="0.25"/>')
    o.append(_t(x0 + 50, y0 + 4.5, "100 mm（定規で測り、0.5 mm 以上ずれていたら印刷し直す）", 3.0))
    vx = 280.0
    o.append(f'<line x1="{vx}" y1="{60}" x2="{vx}" y2="{110}" stroke="#000" stroke-width="0.35"/>')
    for k in range(6):
        o.append(f'<line x1="{vx - (2.5 if k % 5 == 0 else 1.5)}" y1="{60 + 10 * k}" x2="{vx}" y2="{60 + 10 * k}" stroke="#000" stroke-width="0.25"/>')
    o.append(f'<text x="{vx + 4}" y="85" font-size="3" text-anchor="middle" transform="rotate(90 {vx + 4} 85)" '
             'font-family="Noto Sans CJK JP, sans-serif">50 mm</text>')
    # the part: body, slot and a 1.2 mm Famicom card in it
    def r(x, y, w, h, **kw):
        attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
        return f'<rect x="{ox + x:.3f}" y="{oy + y:.3f}" width="{w:.3f}" height="{h:.3f}" {attrs}/>'
    o.append(r(-41.245, -4.625, 82.49, 9.25, fill="none", stroke="#666", stroke_width="0.25", stroke_dasharray="1.2 0.8"))
    o.append(r(-39.52, -1.0, 79.04, 2.0, fill="none", stroke="#999", stroke_width="0.2"))
    o.append(r(-39.2, -0.6, 78.4, 1.2, fill="#e8e8e8", stroke="none"))
    for num, p in pads.items():
        n = int(num)
        cx, cy = ox + p["x"], oy + p["y"]
        if n == 1:
            o.append(f'<rect x="{cx - p["w"] / 2:.3f}" y="{cy - p["w"] / 2:.3f}" width="{p["w"]}" height="{p["w"]}" fill="none" '
                     'stroke="#000" stroke-width="0.25"/>')
        else:
            o.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{p["w"] / 2}" fill="none" stroke="#000" stroke-width="0.25"/>')
        o.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{p["drill"] / 2}" fill="none" stroke="#000" stroke-width="0.12"/>')
        o.append(f'<line x1="{cx - 0.3:.3f}" y1="{cy:.3f}" x2="{cx + 0.3:.3f}" y2="{cy:.3f}" stroke="#000" stroke-width="0.1"/>')
        o.append(f'<line x1="{cx:.3f}" y1="{cy - 0.3:.3f}" x2="{cx:.3f}" y2="{cy + 0.3:.3f}" stroke="#000" stroke-width="0.1"/>')
        ty = cy + 3.7 if p["y"] > 0 else cy - 2.6
        o.append(_t(cx, ty, num, 1.45, weight="bold" if n in (1, 16, 30, 31, 60) else "normal"))
    for num, label in (("1", "GND"), ("16", "GND"), ("30", "+5V"), ("31", "+5V")):
        p = pads[num]
        ty = oy + p["y"] + (5.9 if p["y"] > 0 else -4.9)
        o.append(_t(ox + p["x"], ty, label, 1.6, fill="#b00"))
    o.append(_t(ox, oy + 12.5, "▼ カセットのラベル面はこちら側（1〜30 番の列）　／　cartridge LABEL faces this way", 3.2, weight="bold"))
    o.append(_t(ox, oy - 9.5, "裏面の列（31〜60 番）。31 番は 1 番の真裏", 2.8, fill="#444"))
    o.append(_t(ox, oy + 19.0, "▼ この向きで基板に載せると、ラベル面は JAMMA の金フィンガー（基板の下の辺）の側を向く", 2.8, fill="#444"))
    # instructions
    y = 140.0
    lines = [
        ("確かめ方", True),
        ("1. 上の 100 mm の線を定規で測る。0.5 mm 以上ずれていたら印刷し直す。", False),
        ("2. サンプルの端子が届いたら: この紙を段ボールか発泡スチロールの板に貼り、端子の足 60 本を ＋ 印に刺す。", False),
        ("　 全部の足が丸の中に入れば、穴の位置（2.54 mm 間隔、列の間 5.08 mm）は合っている。", False),
        ("3. カセットの向き: カセットのラベル面を自分に向け、端子を下にして、端子を図の 1〜30 番の列に重ねる。左端の端子が 1 番。", False),
        ("　 任天堂製のカセットなら、ラベル面の 1・16・30 番の端子はほかより長く、端の近くまで伸びている。", False),
        ("　 テスターの導通で、ラベル面の左端（1 番）と左から 16 番目（16 番）が鳴れば正しい（どちらも GND）。鳴らなければ知らせてください。", False),
        ("4. サンプルにカセットを挿し、ぐらつき・浅さ・入りにくさも見る（README 7 章の 4）。", False),
    ]
    for s, bold in lines:
        o.append(_t(12, y, s, 3.4 if bold else 3.0, "start", "bold" if bold else "normal"))
        y += 6.2 if bold else 5.0
    o.append(_t(12, 203, f"{footprint_name} ／ 出典: {sources}", 2.4, "start", fill="#555"))
    o.append("</svg>")
    return "\n".join(o)


def _node(js, cwd):
    return subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=cwd)


def render_pdf(svg_text, pdf_path):
    """A4 landscape PDF at true size.  The dates inside the PDF are replaced, so that a rebuild writes the same bytes."""
    page = pdf_path[:-4] + ".html"
    with open(page, "w", encoding="utf-8") as f:
        f.write('<!doctype html><html><head><meta charset="utf-8"><style>@page{size:297mm 210mm;margin:0}'
                'html,body{margin:0;padding:0}svg{display:block}</style></head><body>' + svg_text + "</body></html>")
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
          f"await p.goto('file://{page}');await p.pdf({{path:'{pdf_path}',width:'297mm',height:'210mm',printBackground:true,"
          "preferCSSPageSize:true,margin:{top:'0',right:'0',bottom:'0',left:'0'}});await b.close();})()"
          ".catch(e=>{console.error(e.message);process.exit(1)});")
    r = _node(js, os.path.dirname(pdf_path))
    os.remove(page)
    if r.returncode:
        return r.stderr.strip()[:200] or "no Chromium"
    data = open(pdf_path, "rb").read()
    data = re.sub(rb"D:\d{14}", b"D:20000101000000", data)
    open(pdf_path, "wb").write(data)
    return ""


def overview_png(svg_dir, names, captions, png_path):
    """The five footprints side by side, at a common scale (KiCad's own SVG export of each)."""
    cells = []
    for name in names:
        svg = open(os.path.join(svg_dir, f"{name}.svg"), encoding="utf-8").read()
        m = re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"', svg)
        w, h = (float(m.group(1)), float(m.group(2))) if m else (50.0, 50.0)
        cells.append((name, w, h))
    scale = 7.0                                   # px per mm
    blocks = []
    for name, w, h in cells:
        blocks.append(f'<figure><img src="{name}.svg" style="width:{w * scale:.0f}px;height:{h * scale:.0f}px">'
                      f'<figcaption><b>{html.escape(captions[name][0])}</b><br>{html.escape(captions[name][1])}</figcaption></figure>')
    page = os.path.join(svg_dir, "_overview.html")
    with open(page, "w", encoding="utf-8") as f:
        f.write('<!doctype html><html><head><meta charset="utf-8"><style>body{margin:24px;background:#fff;'
                'font-family:"Noto Sans CJK JP",sans-serif;font-size:15px}h1{font-size:22px}figure{display:inline-block;'
                'vertical-align:top;margin:12px 28px 24px 0;padding:10px;border:1px solid #ccc;background:#111}'
                'figcaption{color:#eee;margin-top:6px;max-width:900px}</style></head><body>'
                '<h1>基板の自作フットプリント（KiCad の書き出し。縮尺は共通: 1 mm = 7 px）</h1>' + "".join(blocks) + "</body></html>")
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          "const p=await b.newPage({viewport:{width:1600,height:900},deviceScaleFactor:1});"
          f"await p.goto('file://{page}');await p.waitForTimeout(300);await p.screenshot({{path:'{png_path}',fullPage:true}});"
          "await b.close();})().catch(e=>{console.error(e.message);process.exit(1)});")
    r = _node(js, svg_dir)
    os.remove(page)
    return "" if r.returncode == 0 else (r.stderr.strip()[:200] or "no Chromium")


def write_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
