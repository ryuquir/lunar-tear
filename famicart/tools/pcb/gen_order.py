#!/usr/bin/env python3
"""Write the hand-over folder for whoever places the orders (run after gen_jlc.py / finish_package.sh).

<hw>/order/ gets
  grokbot_instructions.md / .html   the procedure for the ordering agent: JLCPCB (boards and assembly) and Akizuki
                                    (hand-soldered modules); the .html is the same text for upload as a Google Doc
  jlcpcb_support_question.txt       the question to JLCPCB support, to be sent before paying
  jlcpcb_pcb_remark_plan_a.txt / _b.txt, jlcpcb_assembly_remark_plan_a.txt / _b.txt   remarks to paste into the order form
  akizuki_parts.csv                 what to buy at Akizuki, with order codes, prices and quantities

Everything that depends on the board is taken from jlcpcb/README.md (which gen_jlc.py writes from the design and the
board file and check_jlc.py verifies); the tool stops when a passage it relies on is missing, so the instructions cannot
drift away from the order notes. Quantities and the Akizuki price list are the constants below.
    FC_DESIGN=design_revg FC_HW_DIR=../../hardware/revg python3 gen_order.py"""
import os, re, csv, sys, html, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = importlib.import_module(os.environ.get('FC_DESIGN', 'design'))
HW = os.path.abspath(os.environ['FC_HW_DIR'])
OUT = os.path.join(HW, 'order')

# ---- what to order (defaults; the buyer may change them)
PCB_QTY, PCBA_QTY = 5, 2            # JLCPCB: 5 boards is the minimum, 2 of them assembled
BUILD = 2                           # sets of hand-soldered parts to buy: one per assembled board
# Akizuki: (order code, name on the page, maker's part number, unit price in yen incl. tax, pieces per board, where it goes)
AKIZUKI_DATE = '2026-11-10'
AKIZUKI = [('129604', 'Raspberry Pi Pico 2', 'SC1631', 990, 4, 'U1・U2（基本）と U4・U5（増設）'),
           ('129619', 'Seeed XIAO RP2350', '102010550', 1100, 2, 'U3・U6'),
           ('102395', 'ヒロセ・マイクロSDカードコネクター DM3AT-SF-PEJM5', 'DM3AT-SF-PEJM5', 150, 1, 'J3（microSD を使う場合）')]
AKIZUKI_FREE_SHIPPING, AKIZUKI_SHIPPING = 11000, 550
JLC_DATE = '2026-11-10'            # day on which the order form and the part catalogue were read (the amounts come from the order notes)

def need(pattern, text, what):
    m = re.search(pattern, text, re.S)
    if not m: raise SystemExit('gen_order: the order notes no longer contain %s; adapt gen_order.py' % what)
    return m

def quote_after(notes, marker):
    """The block quote that follows `marker` in the order notes, as a list of items: the leading sentence(s), then one
    string per numbered point '1) ...'."""
    i = notes.index(marker); lines = []
    for line in notes[i:].splitlines()[1:]:
        if line.startswith('>'): lines.append(line[1:].strip())
        elif lines: break
    text = ' '.join(lines)
    parts = re.split(r'\s(?=\d\) )', ' ' + text)
    return [p.strip() for p in parts if p.strip()]

def inline(t):
    """**bold**, `code` and [text](url) of the source text as HTML."""
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', t)

def to_md(blocks):
    out = []
    for b in blocks:
        k = b[0]
        if k in ('h1', 'h2', 'h3'): out += ['#' * int(k[1]) + ' ' + b[1], '']
        elif k == 'p': out += [b[1], '']
        elif k == 'ul': out += ['- ' + x for x in b[1]] + ['']
        elif k == 'ol': out += ['%d. %s' % (i + 1, x) for i, x in enumerate(b[1])] + ['']
        elif k == 'quote': out += ['> ' + x for x in b[1]] + ['']
        elif k == 'table':
            out += ['| ' + ' | '.join(b[1]) + ' |', '|' + '---|' * len(b[1])] + ['| ' + ' | '.join(r) + ' |' for r in b[2]] + ['']
    return '\n'.join(out)

def to_html(blocks, title):
    out = ['<html><head><meta charset="utf-8"><title>%s</title></head><body>' % html.escape(title)]
    for b in blocks:
        k = b[0]
        if k in ('h1', 'h2', 'h3'): out.append('<%s>%s</%s>' % (k, inline(b[1]), k))
        elif k == 'p': out.append('<p>%s</p>' % inline(b[1]))
        elif k in ('ul', 'ol'): out.append('<%s>%s</%s>' % (k, ''.join('<li>%s</li>' % inline(x) for x in b[1]), k))
        elif k == 'quote': out.append('<blockquote>%s</blockquote>' % ''.join('<p>%s</p>' % inline(x) for x in b[1]))
        elif k == 'table':
            out.append('<table border="1" cellpadding="4" style="border-collapse:collapse"><tr>%s</tr>%s</table>' % (
                ''.join('<th>%s</th>' % inline(c) for c in b[1]), ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in b[2])))
    return '\n'.join(out) + '\n</body></html>\n'

def main():
    notes = open(os.path.join(HW, 'jlcpcb', 'README.md')).read()
    # ---- taken from the order notes
    question = quote_after(notes, '質問文（そのまま貼る）:')
    remark_a = quote_after(notes, 'PCB Remark（A 案。そのまま貼る）:')
    remark_b = quote_after(notes, 'PCB Remark（B 案。そのまま貼る）:')
    assert len(question) == 5 and question[1].startswith('1) ') and question[4].startswith('4) '), question
    assert len(remark_a) == 6 and len(remark_b) == 7, (len(remark_a), len(remark_b))
    panel = need(r'\*\*A 案（推奨）`gerbers_rails\.zip`\*\*: 捨て基板を自分で描き込んだデータ。全体 ([\d.]+ × [\d.]+) mm', notes, 'the panel size of plan A').group(1)
    board = need(r'\*\*B 案 `gerbers\.zip`\*\*: 基板だけのデータ（([\d.]+ × [\d.]+) mm）', notes, 'the board size of plan B').group(1)
    panel_b = need(r'製造データの大きさが ([\d.]+ × [\d.]+) mm（左右に付いた場合）', notes, 'the panel size of plan B').group(1)
    form_b = need(r'注文フォームは、大きさを自動で \*\*([\d.]+ × [\d.]+) mm\*\* に書き換える', notes, 'the size the form shows for plan B').group(1)
    m = need(r'部品の照合画面の正しい状態: \*\*(\d+) 行・(\d+) 点がすべて一致、すべて Basic、未選択の部品なし\*\*', notes, 'the expected state of the parts list')
    ntypes, nparts = m.group(1), m.group(2)
    dnp = need(r'実装しない部品（手はんだ・基板パターン）: ([^\n]+)', notes, 'the list of parts that are not placed').group(1).strip()
    orient = re.findall(r'^  \d\. (.+)$', need(r'\*\*部品プレビューで見る点\*\*[^\n]*\n((?:  \d\. [^\n]+\n)+)', notes, 'the preview check list').group(1), re.M)
    counts = need(r'このデータの基板は、配線 (\d+) 本・ビア (\d+) 個・未接続 (\d+)。', notes, 'the track and via counts')
    if counts.group(3) != '0': raise SystemExit('gen_order: the board of the order notes has open connections')
    col = {2: 1, 5: 2}.get(PCBA_QTY)                              # the cost table of the notes has a column for 2 and for 5 assembled boards
    if col is None: raise SystemExit('gen_order: the order notes give assembly costs for 2 or 5 boards only')
    JLC_ASM = int(need(r'\| 実装費（Standard・片面） \| 約 US\$ (\d+) \| 約 US\$ (\d+) \|', notes, 'the assembly cost').group(col))
    JLC_ASM_FIX = int(need(r'\| 治具（Fixture）費 2 個が加わった場合 \| 約 US\$ (\d+) \| 約 US\$ (\d+) \|', notes, 'the assembly cost with fixtures').group(col))
    m = need(r'A 案の大きさ（[^）]*）で約 US\$ (\d+)、B 案の大きさ（[^）]*）で約 US\$ (\d+)', notes, 'the board prices')
    JLC_PCB_A, JLC_PCB_B = int(m.group(1)), int(m.group(2))
    if PCB_QTY != 5: raise SystemExit('gen_order: the board price of the order notes is for 5 boards')
    for s in ('**Panel by Customer**', 'Do not confirm automatically', 'Added by Customer', 'Complete File, just proceed with my own files', 'By Customer (Self-Service)',
              '**ENIG**', '**2 U"**', 'Beveling **30°**', '**1.2 mm**', 'Remove Mark', 'Flying Probe Fully Test'):
        if s not in notes: raise SystemExit('gen_order: the order notes no longer contain %r; adapt gen_order.py' % s)
    os.makedirs(OUT, exist_ok=True)
    def write(name, text):
        open(os.path.join(OUT, name), 'w').write(text); print('written', os.path.join(OUT, name))
    write('jlcpcb_support_question.txt', '\n\n'.join([question[0]] + ['\n'.join(question[1:])]) + '\n')
    write('jlcpcb_pcb_remark_plan_a.txt', '\n'.join(remark_a) + '\n')
    write('jlcpcb_pcb_remark_plan_b.txt', '\n'.join(remark_b) + '\n')
    write('jlcpcb_assembly_remark_plan_a.txt', '\n'.join(remark_a[:3]) + '\n')
    write('jlcpcb_assembly_remark_plan_b.txt', '\n'.join(remark_b[:4]) + '\n')
    # ---- Akizuki list
    rows = [(code, name, mpn, price, per * BUILD, price * per * BUILD, 'https://akizukidenshi.com/catalog/g/g%s/' % code, use) for code, name, mpn, price, per, use in AKIZUKI]
    total = sum(r[5] for r in rows); ship = 0 if total >= AKIZUKI_FREE_SHIPPING else AKIZUKI_SHIPPING
    one = sum(price * per for _, _, _, price, per, _ in AKIZUKI)
    with open(os.path.join(OUT, 'akizuki_parts.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['販売コード', '品名', '型番', '単価（税込・円）', '数量', '小計（円）', 'URL', '使う場所'])
        w.writerows(rows); w.writerow(['', '合計（税込）', '', '', sum(r[4] for r in rows), total, '', '送料 %d 円' % ship])
    print('written', os.path.join(OUT, 'akizuki_parts.csv'))
    yen = lambda v: '{:,}'.format(v)
    # ---- the instructions
    T = 'ファミコン基板（famicart rev G）発注指示書'
    B = [('h1', T),
         ('p', 'この文書は、発注を代行する GrokBOT に向けた手順書です。JLCPCB への基板と部品実装の発注、秋月電子通商への手はんだ部品の発注の 2 件を扱います。'
               '書いてあるとおりに進め、「止まって確認」とある所では必ず依頼者（このフォルダの持ち主）の返事を待ってください。'),
         ('h2', '依頼の内容'),
         ('ul', ['JLCPCB に、基板 **%d 枚**の製造と、そのうち **%d 枚**への部品実装（Standard PCBA、表面のみ）を発注する。' % (PCB_QTY, PCBA_QTY),
                 '秋月電子通商の通販で、手はんだ用のモジュールとコネクタを **%d 台分**発注する。' % BUILD,
                 '2 件は別々の注文で、どちらを先に進めてもよい。秋月の注文は、JLCPCB のサポートの回答を待たずに進めてよい。']),
         ('h2', '必ず守ること'),
         ('ol', ['**支払いの直前で止まる。** 注文内容と合計金額（送料・税を含む）を依頼者に見せ、承認をもらってから支払う。依頼者があらかじめ上限金額を決めて任せている場合は、その範囲なら進めてよい。',
                 '**ログイン情報、配送先、支払い方法は依頼者から受け取る。** このフォルダにも、この文書にも書かれていない。受け取った情報を、注文に必要な相手（JLCPCB、秋月）以外に渡さない。',
                 '**判断が要る所で推測しない。** この文書に書かれていない選択肢や、書かれている値を選べない場面では、止まって依頼者に聞く（下の「止まって確認する場面」）。',
                 '**JLCPCB からの提案を自分で承諾しない。** 担当者やサポートが、この文書と違うやり方（捨て基板の位置を変える、V カットにする、面取りをやめる、部品を別の品番に替える、など）を提案してきたら、内容を依頼者に伝えて指示を待つ。',
                 '**部品を別の品番に替えない。** JLCPCB の画面が出す代替部品の候補も、秋月の似た商品も選ばない。']),
         ('h2', 'このフォルダのファイル'),
         ('table', ['ファイル', '使い道'],
          [['`gerbers_rails.zip`', '**A 案（これを使う）**。基板と左右の捨て基板を 1 枚にまとめた製造データ。大きさ %s mm' % panel],
           ['`gerbers.zip`', 'B 案。基板だけの製造データ（%s mm）。JLCPCB が A 案を受け付けないと答え、依頼者が B 案への切り替えを認めた場合だけ使う' % board],
           ['`bom_jlc.csv`', '実装する部品の表。A 案・B 案で共通'],
           ['`cpl_jlc.csv`', '部品の位置と向き。A 案・B 案で共通'],
           ['`rails.png`', 'JLCPCB のサポートへの質問に添付する図'],
           ['`jlcpcb_support_question.txt`', 'サポートへの質問文（英語）。そのまま送る'],
           ['`jlcpcb_pcb_remark_plan_a.txt`、`jlcpcb_assembly_remark_plan_a.txt`', 'A 案の注文フォームに貼る Remark（PCB 用と実装用）'],
           ['`jlcpcb_pcb_remark_plan_b.txt`、`jlcpcb_assembly_remark_plan_b.txt`', 'B 案に切り替えた場合の Remark'],
           ['`jlcpcb_order_notes.md`', '設計者が書いた注文メモの全文。この文書の根拠と、細かい理由が書いてある。迷ったときに読む'],
           ['`akizuki_parts.csv`', '秋月で買う品目、販売コード、数量、金額'],
           ['`outline.png`、`placement.png`', '基板の外形図と部品の配置図（参考）'],
           ['`parts_check.csv`、`cpl_check.csv`', 'JLCPCB の部品の区分・在庫と、部品の向きを照合した結果（参考。%s 時点）' % JLC_DATE]]),
         ('h2', '数量'),
         ('table', ['注文先', '品目', '数量', '補足'],
          [['JLCPCB', '基板（PCB Qty）', '%d 枚' % PCB_QTY, '注文できる最少の枚数'],
           ['JLCPCB', '部品実装（PCBA Qty）', '%d 枚' % PCBA_QTY, '残りの %d 枚は部品なしの基板で届く' % (PCB_QTY - PCBA_QTY)]] +
          [['秋月', '%s（販売コード %s）' % (name, code), '%d 個' % qty, use] for code, name, mpn, price, qty, sub, url, use in rows]),
         ('p', '秋月の数量は、実装した %d 枚を両方とも全部の機能つきで組み立てる数です。1 台だけ組む場合は半分（1 台分で %s 円）になります。依頼者から数量の指定があれば、そちらに従ってください。' % (BUILD, yen(one))),
         ('h2', 'JLCPCB の手順'),
         ('h3', '支払いの前にサポートへ質問する'),
         ('p', 'この基板は端に金めっきの接点（金フィンガー）があり、その辺を斜めに削る加工（面取り、Beveling）を頼みます。実装に必要な捨て基板（Edge Rails）は、データの中に左右に描き込んであります。'
               'この組み合わせで面取りをしてもらえるか、注文の種類を何にすればよいかは、JLCPCB のどのページにも書かれていません。そのため、注文の前に確かめます。'),
         ('ol', ['JLCPCB のサポート（サイトのチャット、またはメール）に、`jlcpcb_support_question.txt` の英文を送り、`rails.png` を添付する。GrokBOT から送れない場合は、文面と図を依頼者に渡して送ってもらう。',
                 '回答の全文を依頼者に報告する。',
                 '回答に応じて、下の表のとおりに進める。']),
         ('p', '質問文（`jlcpcb_support_question.txt` と同じ内容）:'),
         ('quote', question),
         ('table', ['質問', '回答', 'すること'],
          [['1) 面取りできるか', 'できる', '次へ進む'],
           ['1) 面取りできるか', 'できない', '**止まって確認。** 依頼者が「面取りなしで作る」と決めた場合は、Gold Fingers の Beveling を No にし、Remark から "Please bevel this edge 30 degrees." の 1 文を消して進める'],
           ['2) この捨て基板で実装できるか', 'できる', '次へ進む'],
           ['2) この捨て基板で実装できるか', 'できない、または条件つき', '**止まって確認。** 足りない点（寸法や数）を聞き取って依頼者に伝える。データの作り直しが要る'],
           ['3) Delivery Format', 'Panel by Customer', 'この文書のとおりに選ぶ'],
           ['3) Delivery Format', 'Single PCB', 'Delivery Format を Single PCB にする。追加料金の説明があれば依頼者に伝える'],
           ['4) 基板だけのデータでも左右に捨て基板を付けて面取りできるか', 'どちらでも', '回答を記録して依頼者に伝える。A 案が使える間は B 案に切り替えない']]),
         ('p', '2 営業日たっても回答が無い場合や、回答があいまいな場合は、止まって依頼者に確認してください。'),
         ('h3', '基板（PCB）の指定'),
         ('ol', ['[注文フォーム](https://cart.jlcpcb.com/quote) を開き、"Add gerber file" に `gerbers_rails.zip` を上げる。',
                 '読み込まれた大きさ（Dimensions）が **%s mm** であることを確かめる。0.5 mm 以上違う場合は止まって確認。' % panel,
                 '下の表のとおりに選ぶ。表に無い項目は、最初から選ばれている値のままにする。',
                 'PCB Remark の欄に、`jlcpcb_pcb_remark_plan_a.txt` の英文をそのまま貼る。']),
         ('table', ['項目', '選ぶ値'],
          [['Base Material', 'FR-4'], ['Layers', '2'], ['PCB Qty', '%d' % PCB_QTY], ['Product Type', 'Industrial/Consumer electronics'], ['Different Design', '1'],
           ['Delivery Format', '**Panel by Customer**。Panel Format は Column 1、Row 1（サポートが Single PCB と答えた場合はそれに合わせる）。"Panel by JLCPCB" は選ばない'],
           ['PCB Thickness', '**1.2 mm**（最初に選ばれている値が違えば、1.2 mm に変える）'], ['PCB Color', 'Green'], ['Silkscreen', 'White'],
           ['Surface Finish', '**ENIG**。Gold Thickness は **2 U"**'], ['Outer Copper Weight', '1 oz'], ['Via Covering', 'Tented'],
           ['Board Outline Tolerance', '±0.2 mm（Regular）'], ['Mark on PCB', 'Remove Mark'], ['Electrical Test', 'Flying Probe Fully Test'],
           ['Gold Fingers', '**Yes**。Beveling は **30°**'], ['Castellated Holes', 'No'],
           ['Confirm Production file', '**Yes**。選ぶと出る画面では **"Do not confirm automatically"** を選ぶ']]),
         ('p', 'PCB Remark に貼る文（`jlcpcb_pcb_remark_plan_a.txt` と同じ内容）:'),
         ('quote', remark_a),
         ('h3', '部品実装（PCB Assembly）の指定'),
         ('ol', ['PCB Assembly を有効にし、下の表のとおりに選ぶ。',
                 'BOM に `bom_jlc.csv`、CPL に `cpl_jlc.csv` を上げる。',
                 '部品の照合画面で、**%s 行・%s 点がすべて一致し、すべて Basic で、未選択の部品が無い**ことを確かめる。1 行でも在庫切れ、Extended、不一致があれば止まって確認。代替部品の候補は選ばない。' % (ntypes, nparts),
                 '部品の配置のプレビューで、下の「部品の向きの確認」の %d 点を確かめる。' % len(orient),
                 '実装用の Remark の欄に、`jlcpcb_assembly_remark_plan_a.txt` の英文をそのまま貼る。',
                 'カートに入れ、配送方法の候補とそれぞれの金額を控える。配送方法は依頼者が選ぶ。',
                 '支払いの前にデータの審査を受けられる選択肢（Review Before Payment など）が出た場合は、そちらを選ぶ。',
                 '合計金額と内訳を依頼者に見せ、承認をもらってから支払う。']),
         ('table', ['項目', '選ぶ値'],
          [['PCBA Type', '**Standard**（Economic は金フィンガー付きの基板を受け付けない）'], ['Assembly Side', 'Top Side'], ['PCBA Qty', '%d' % PCBA_QTY],
           ['Edge Rails/Fiducials', '**Added by Customer**'], ['Tooling holes（項目が出た場合）', 'Added by Customer'],
           ['File provided as（項目が出た場合）', 'Complete File, just proceed with my own files'], ['Confirm Parts Placement', 'Yes'],
           ['部品の選び方', 'By Customer (Self-Service)'], ['捨て基板を外すサービス（Depaneling）', '選ばない']]),
         ('p', '実装しない部品（照合画面に出なくて正しいもの）: %s。これらは依頼者が自分ではんだ付けする部品と、基板のパターンです。' % dnp),
         ('h3', '部品の向きの確認'),
         ('p', 'プレビューは、基板を上から見て、金色の接点が下に来る向きで確かめます。'),
         ('ol', orient),
         ('p', '**U7 か B5819W（D10〜D15）が 180° 回って見える場合は、承認せずに止まって確認してください。** そのほかの点が違って見える場合も同じです。'),
         ('h3', '金額の目安'),
         ('ul', ['基板: 約 US$ %d（%d 枚。%s の見積もり画面の値。ENIG、金フィンガー、面取り、Confirm Production file を含み、送料は別）。' % (JLC_PCB_A, PCB_QTY, JLC_DATE),
                 '実装: 約 US$ %d（%d 枚。治具の費用が加わると約 US$ %d）。部品代は見積もり画面に出る金額で、この文書では計算していない。' % (JLC_ASM, PCBA_QTY, JLC_ASM_FIX),
                 '送料、関税、消費税は、見積もり画面と配送業者の案内による。この文書では確かめていない。',
                 '合計がこの目安より 3 割以上高い場合は、理由（どの項目が高いか）を添えて依頼者に伝える。']),
         ('h3', '注文したあと'),
         ('ol', ['製造データ（Production file）の確認依頼が届いたら、承認する前に依頼者に見せる。確かめる点は、捨て基板が左右にあること、金色の接点の辺に捨て基板も V カットの線も無いこと、面取りの指示が入っていること、外形の切り欠きとスリットが `rails.png` のとおりであること。',
                 '部品の配置の確認依頼（Confirm Parts Placement）が届いたら、「部品の向きの確認」の %d 点を確かめ、画面を依頼者に見せてから承認する。' % len(orient),
                 'JLCPCB から質問や変更の提案が届いたら、内容を依頼者に伝えて指示を待つ。']),
         ('h3', 'B 案に切り替える場合'),
         ('p', 'JLCPCB が「捨て基板を描き込んだデータは受け付けない」と答え、依頼者が切り替えを認めた場合だけ、次のように変えます。'),
         ('ul', ['上げるデータは `gerbers.zip`。Dimensions は %s mm。' % board,
                 'Delivery Format は Single PCB。実装の Edge Rails/Fiducials は Added by JLCPCB。',
                 '注文フォームは大きさを %s mm と表示する（上下に捨て基板を付けた大きさ）。これはフォームの既定の動きで、Remark で左右に付けるよう頼む。' % form_b,
                 'Remark は `jlcpcb_pcb_remark_plan_b.txt` と `jlcpcb_assembly_remark_plan_b.txt` を貼る。',
                 '製造データの大きさが %s mm（左右に付いた場合）でなければ承認しない。' % panel_b]),
         ('h2', '秋月電子通商の手順'),
         ('ol', ['[秋月電子通商の通販サイト](https://akizukidenshi.com/) で、下の表の品目を**販売コードで**探してカートに入れる。',
                 '品名と型番が表と同じであることを確かめる。名前の似た別の商品（Raspberry Pi Pico 2 W、Pico 2 H、初代の Pico、ピンヘッダー付きの品）は選ばない。',
                 'カートの商品合計が %s 円（税込）であることを確かめる。%s' % (yen(total), '税込 %s 円以上なので送料は掛からない。' % yen(AKIZUKI_FREE_SHIPPING) if ship == 0 else '送料は 1 個口 %d 円。' % AKIZUKI_SHIPPING),
                 '在庫が足りない品目、価格が表と違う品目、購入数の制限に掛かる品目があれば、止まって確認する。',
                 '支払い方法と配送先は依頼者の指定に従う。']),
         ('table', ['販売コード', '品名', '型番', '単価（税込）', '数量', '小計'],
          [[code, '[%s](%s)' % (name, url), mpn, '%s 円' % yen(price), '%d' % qty, '%s 円' % yen(sub)] for code, name, mpn, price, qty, sub, url, use in rows] +
          [['', '合計', '', '', '%d' % sum(r[4] for r in rows), '%s 円' % yen(total)]]),
         ('p', '価格と在庫は %s に秋月のサイトで確かめた値です（3 品目とも在庫あり）。同社の案内では、送料は佐川急便が 1 個口 550 円、ヤマト運輸が 600 円で、商品合計が税込 11,000 円以上なら無料です。'
               'クレジットカード払いは会員登録と 3D セキュア 2.0 対応のカードが要り、代金引換は手数料 300 円です。' % AKIZUKI_DATE),
         ('h2', '止まって確認する場面'),
         ('ul', ['支払いの直前（JLCPCB、秋月とも）。',
                 'JLCPCB のサポートが、面取りできない、この捨て基板では実装できない、と答えたとき。回答が無い、あいまいなとき。',
                 '注文フォームに、この文書の表にある値が無いとき。読み込まれた大きさが違うとき。',
                 '部品の照合画面で、在庫切れ、Extended、不一致、未選択があるとき。',
                 '部品の向きが「部品の向きの確認」と違って見えるとき。',
                 '製造データや部品の配置の確認依頼が届いたとき（承認の前）。',
                 'JLCPCB から質問、変更の提案、追加料金の連絡が届いたとき。',
                 '秋月で在庫が足りない、価格が違う、購入数の制限があるとき。',
                 '合計金額が目安より 3 割以上高いとき。']),
         ('h2', '終わったら報告すること'),
         ('ul', ['JLCPCB: 注文番号、選んだ Delivery Format、合計金額と内訳、配送方法、納期の見込み、サポートの回答の全文。',
                 '秋月: 注文番号、合計金額、発送の見込み。',
                 '止まって確認した点と、その結果。未解決のことがあればその内容。']),
         ('h2', 'この基板について知っておくこと'),
         ('ul', ['基板の名前は famicart rev G。ファミリーコンピュータ用のカセット基板で、大きさは %s mm、2 層、板厚 1.2 mm。' % board,
                 'データは機械的な検査（配線の未接続 0、設計ルールの違反 0、JLCPCB の製造条件、部品の向き %s 点）に合格している。設計者以外による見直しと、実物での動作確認はまだで、今回が最初の製造になる。そのため数量は最少にしてある。' % nparts,
                 'この文書とフォルダのデータは、配線 %s 本・ビア %s 個の版のもの（`jlcpcb_order_notes.md` の冒頭に同じ数字がある）。数字が違うデータを渡された場合は、止まって確認する。' % (counts.group(1), counts.group(2)),
                 'この発注に含まれないもの: カセットの外側のケース、USB ケーブル、はんだ付けの道具。',
                 '細かい理由や JLCPCB の条件の出典は `jlcpcb_order_notes.md` にある。']),
         ('h2', '根拠にした資料'),
         ('ul', ['JLCPCB の注文フォーム（項目名、見積もり。%s 確認）: https://cart.jlcpcb.com/quote' % JLC_DATE,
                 'JLCPCB 実装仕様（金フィンガーは Standard PCBA のみ）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities',
                 'JLCPCB 金フィンガーと面取り: https://jlcpcb.com/help/article/jlcpcb-gold-fingers',
                 'JLCPCB 捨て基板とフィデューシャル: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order',
                 'JLCPCB 実装の料金表: https://jlcpcb.com/help/article/pcb-assembly-price'] +
                ['秋月電子通商 %s（%s 確認）: https://akizukidenshi.com/catalog/g/g%s/' % (name, AKIZUKI_DATE, code) for code, name, mpn, price, per, use in AKIZUKI] +
                ['秋月電子通商 注文方法（送料、支払い方法。%s 確認）: https://akizukidenshi.com/catalog/pages/buy.aspx' % AKIZUKI_DATE])]
    write('grokbot_instructions.md', to_md(B))
    write('grokbot_instructions.html', to_html(B, T))
    print('order folder: PCB %d, PCBA %d, Akizuki %d sets = %s yen (shipping %d yen)' % (PCB_QTY, PCBA_QTY, BUILD, yen(total), ship))

if __name__ == '__main__':
    main()
