# JLCPCB 注文パッケージ（famicart rev G: 任天堂の大型カセットシェル用）

Pico 2 ×2 + XIAO RP2350 ×2 が基本構成、Pico 2 ×2 は増設用（載せなくても動く）。16 MB の SPI フラッシュを載せ、microSD
ソケットは任意。回路と配置の説明は `docs/12_rev_g_plan.md`、外形図は `../outline.png`、配置図は `../placement.png`。

**状態**: 設計レビューと独立検証の指摘を反映した版で、**実機では未検証**。rev G 用のファームウェアはまだ無い（ピン配置と一部の信号の
極性が rev F と違う。`docs/12_rev_g_plan.md` の作業一覧）。**シェルへの収まりも実物では未確認**なので、最初の注文は最少枚数にして、
モジュールをはんだ付けする前に基板だけをシェルに入れて確かめること。

| ファイル | 内容 |
|---|---|
| `gerbers_rails.zip` | **A 案（推奨）**: 基板＋左右の捨て基板（ミシン目のタブでつないである）。103.6 × 85.7 mm |
| `gerbers.zip` | B 案: 基板だけ。89.6 × 85.7 mm。捨て基板は JLCPCB に付けてもらう |
| `bom_jlc.csv`、`cpl_jlc.csv` | 部品表と配置。A 案・B 案で共通（座標は同じ） |
| `rails.png` | 捨て基板の位置の図。JLCPCB への問い合わせに添付する |
| `parts_check.csv`、`cpl_check.csv` | 部品の区分・在庫と、部品の向きの検査結果 |

このデータの基板は、配線 3861 本・ビア 543 個・未接続 0。

## 1. 注文の種類と、捨て基板の付け方
- 金フィンガー付きの基板は **Economic PCBA では受け付けられない**（JLCPCB の実装仕様表で Gold fingers は Economic "Not Support"、
  Standard "Support"）。**Standard PCBA** で注文する。実装は表面（Top）だけ、10 種類・81 点/枚。
- Standard PCBA は捨て基板（Edge Rails、幅 5 mm 以上）とフィデューシャルが必須。
- **JLCPCB に任せると、捨て基板は既定で「長いほうの 2 辺」に付く**（注文フォームの注意書き: "Please add two 5mm edge rails along
  the longer sides of your PCB"）。この基板は 89.6 × 85.7 mm なので、長い辺は**上の辺と端子の辺**になる。端子の辺に捨て基板が付くと、
  端子の面取りができず（JLCPCB の金フィンガーの説明: 面付けして端子が内側に来ると面取りできない）、端子の辺が割り取った面になる。
- そこでデータを 2 通り用意した。

**A 案（推奨）`gerbers_rails.zip`**: 捨て基板を自分で描き込んだデータ。全体 103.6 × 85.7 mm、基板は 1 枚。
- 捨て基板は左右に 1 本ずつ。幅 5.0 mm、長さ 83.0 mm。基板との間は幅 2.0 mm のルーター加工の溝で、V カットは無い。
- 端子の辺には何も付かない。捨て基板は端子の辺の線より 2.7 mm 手前で終わる（面取りの刃が通る所を空けるため）。
- 基板とは片側 3 か所のタブ（幅 5.2 mm）でつながる。タブには直径 0.6 mm の穴が 7 個、穴と穴の間を 0.3 mm 空けて
  並んでいる（ミシン目）。穴は基板の端の線に外側から接している。折り取ると高さ 0.3 mm 以下の突起が残るので、やすりで端の線まで落とす。
- 捨て基板の上に、フィデューシャル 3 個（銅 1 mm、レジスト開口 2 mm、中心がパネルの端から 3.85 mm）と、ツーリング穴
  4 個（直径 2.0 mm、めっき無し）がある。
- これらの数値は、JLCPCB が「自社で実装するミシン目パネル」に示している条件に合わせてある（5 章の表の「捨て基板」の行）。
- 注文画面では **Delivery Format を "Panel by Customer"（Panel Format は Column 1・Row 1）**、実装の **Edge Rails/Fiducials を
  "Added by Customer"** にする。JLCPCB の定義では、捨て基板をミシン目でつないだデータは「自分で面付けしたデータ」に当たる。
  ただし「基板 1 枚＋自分で描いた捨て基板」の注文のしかたを書いたページは無いので、下の質問の 3) で確かめる。

**B 案 `gerbers.zip`**: 基板だけのデータ（89.6 × 85.7 mm）。捨て基板は JLCPCB に付けてもらい（Added by JLCPCB）、左右に付けるよう Remark で頼む。
- 注文フォームは、大きさを自動で **89.6 × 95.7 mm** に書き換える（上の辺と端子の辺に付けた大きさ。フォームの文面はこれを
  "on the shorter sides" と呼ぶ）。これはフォームの既定の動作で、フォーム上では変えられない。Remark で左右に付けるよう頼み、
  結果は製造データで確かめる（この動作はフォームのスクリプトと文面の一覧から読んだもので、画面では確かめていない）。
- **Confirm Production file を Yes** にして、製造データの大きさが 99.6 × 85.7 mm（左右に付いた場合）で、端子の辺に V カットの線が
  無いことを確かめてから承認する。89.6 × 95.7 mm なら上下に付いているので、承認しない。
- JLCPCB が付ける捨て基板は V カットでつながる。左右の端は V カットの面（公差 ±0.4 mm）になり、銅箔から端までの 0.4 mm に余裕が
  無い。JLCPCB は「形が四角や円でない基板の面付けは自分でやること」とも書いているので、B 案は断られることがある。そのときは A 案を使う。

**支払いの前に**: どちらの案でも、「捨て基板の付いた基板の端子を面取りしてもらえるか」は JLCPCB のどのページにも書かれていない。
サポート（チャット）に `rails.png` を見せて確かめる。質問文（そのまま貼る）:

> I am going to order a 2-layer board, 1.2 mm, ENIG, gold fingers (30 on each side) with a 30 degree bevel, and Standard PCBA
> on the top side. Please see the attached drawing. My Gerber file already contains two 5.0 mm edge rails that I drew myself,
> on the left and right edges (perpendicular to the gold-finger edge). Each rail is joined to the board by 3 mouse-bite tabs
> (5.2 mm wide, 0.6 mm holes) across a 2.0 mm routed gap. There is no V-cut. The rails end 2.7 mm above the gold-finger
> edge, so that edge is completely free. The rails carry 3 fiducials (1 mm, centre 3.85 mm from the panel edges) and
> 4 tooling holes (2.0 mm). Panel size 103.6 x 85.7 mm, one board per panel.
> 1) Can you bevel the gold-finger edge of this board?
> 2) Is this rail arrangement accepted for Standard PCBA?
> 3) Which Delivery Format must I select: Single PCB or Panel by Customer (1 x 1)? Is there an extra charge?
> 4) If I upload the board without rails (89.6 x 85.7 mm) instead, can you add the rails on the same two edges
> (panel 99.6 x 85.7 mm) and still bevel the gold-finger edge?

答えに応じて変える所:
- 1) が「面取りできない」の場合: Gold Fingers の **Beveling を "No"** にし、Remark の "Please bevel this edge 30 degrees." を消す。
  面取り無しで作ってもらい、受け取ってから手で面取りする（6 章）。捨て基板を上下に移す提案は断る。
- 2) が「この捨て基板では実装できない」の場合: 足りない寸法を聞き、`tools/pcb/design_revg.py` の `RAILS` を直してデータを作り直す。
- 3) が "Single PCB" の場合: Delivery Format をそれに合わせる。追加料金があれば 4 章の見積もりに加える。

## 2. PCB の指定（Instant Quote → Add gerber file）
注文フォームの項目名は変わることがある（下の項目名は 2026-11-10 にフォームの文面で確認できたもの。面取りの角度、金の厚さ、外形公差、
ビアの処理、実装の項目は、選択やアップロードのあとに現れる）。

| 項目 | 指定 |
|---|---|
| Base Material / Layers | FR-4 / 2 |
| Dimensions | A 案 103.6 × 85.7 mm、B 案 89.6 × 85.7 mm（ガーバーから自動で入る。基板は本体 75.0 mm + 端子タブ 10.7 mm）|
| PCB Qty | 5（最少。3 枚などは選べない）|
| Product Type | Industrial/Consumer electronics |
| Different Design | 1 |
| Delivery Format | A 案: **Panel by Customer**、Panel Format は Column 1・Row 1。B 案: **Single PCB**。どちらの案でも "Panel by JLCPCB" は選ばない（選ぶと面取りの指定が消える）|
| PCB Thickness | **1.2 mm**（公差 ±10 %: 1.08〜1.32 mm）|
| PCB Color / Silkscreen | Green / White（ほかの色は納期が 2 日延びる）|
| Surface Finish | **ENIG**、Gold Thickness は **2 U"**（約 0.05 µm。1 U" は約 0.025 µm。端子が擦れるので厚いほう。5 枚で約 $17 の追加）|
| Outer Copper Weight | 1 oz |
| Via Covering | Tented |
| Min via hole size/diameter | 標準のまま（設計値: 穴 0.3 mm・径 0.5 mm）|
| Board Outline Tolerance | ±0.2 mm（Regular。ルーター加工の辺の値）|
| Mark on PCB | **Remove Mark**（既定。JLCPCB は 2026 年 5 月に注文番号の印字をやめた）|
| Electrical Test | Flying Probe Fully Test |
| Gold Fingers | **Yes**、Beveling **30°**（ENIG を選んだときだけ端子が金になる。HASL を選ぶと端子ははんだ〔錫〕になる）|
| Castellated Holes | No |
| Material Type、Via Plating Method、Edge Plating、Blind Slots、UL Marking、Humidity Indicator Card | 既定のまま |
| Confirm Production file | **Yes**（約 $1）。選ぶと「48 時間以内に確認しないと、自動で承認して製造に進む」という画面が出るので、**"Do not confirm automatically"** を選ぶ |

製造データ（Production file）が届いたら、承認する前に次を確かめる: 捨て基板が左右にあること、端子の辺に捨て基板も V カットの線も
無いこと、面取りの指示が入っていること、外形の切り欠きとスリットが図面どおりであること。

PCB Remark（A 案。そのまま貼る）:

> 1) This is ONE board with two 5.0 mm edge rails that I drew myself: panel 103.6 x 85.7 mm, one board per panel. The rails are
> on the left and right edges, each joined by 3 mouse-bite tabs (5.2 mm wide, 0.6 mm holes) across a 2.0 mm routed gap.
> 3 fiducials and 4 tooling holes (2.0 mm) are on the rails. Please do NOT add other rails and do NOT add V-cut.
> 2) Gold fingers are on ONE edge only: the edge with the 78.4 mm wide tab (30 fingers on each side). Please bevel this edge
> 30 degrees. This edge must stay a free routed edge; the rails end 2.7 mm above it.
> 3) If you cannot bevel a board with these rails, do NOT move or change the rails: put the order on hold and contact me.
> 4) You may shorten the finger copper to your standard setback for the bevel.
> 5) The solder mask window over the gold fingers is intentional: it starts 4.0 mm below the root of the tab and runs to the
> edge. Please do not enlarge it towards the board: tracks run beside the upper ends of the fingers.
> 6) The outline has two side notches, one inner slot (6.6 x 2.4 mm) and cut corners beside the tab. Inner corners are drawn
> with R 0.5 mm. Please keep them as drawn.

PCB Remark（B 案。そのまま貼る）:

> 1) Gold fingers are on ONE edge only: the edge with the 78.4 mm wide tab (30 fingers on each side). Please bevel this edge
> 30 degrees.
> 2) Edge rails for assembly: please add the two 5 mm rails on the LEFT and RIGHT edges (the two 85.7 mm edges, perpendicular
> to the gold-finger edge). Panel size 99.6 x 85.7 mm, NOT 89.6 x 95.7 mm as the order form shows. Do NOT put a rail on the
> gold-finger edge or on the opposite edge.
> 3) The gold-finger edge must stay a free routed edge: no rail, no V-cut, no mouse bites.
> 4) If you cannot add the rails on these two edges, or cannot bevel a board with rails: do NOT move the rails; put the order
> on hold and contact me.
> 5) You may shorten the finger copper to your standard setback for the bevel.
> 6) The solder mask window over the gold fingers is intentional: it starts 4.0 mm below the root of the tab and runs to the
> edge. Please do not enlarge it towards the board: tracks run beside the upper ends of the fingers.
> 7) The outline has two side notches, one inner slot (6.6 x 2.4 mm) and cut corners beside the tab. Inner corners are drawn
> with R 0.5 mm. Please keep them as drawn.

**端子の金について**: JLCPCB は硬質金めっき（抜き差しの多いコネクタ用の電解めっき、0.5〜1.5 µm 級）を扱っておらず、金フィンガーにも
ENIG を使う（同社の記事に明記）。注文できる ENIG の金の厚さは 1 U"（約 0.025 µm）か 2 U"（約 0.05 µm）の 2 つ。同社の記事は、
ENIG は「抜き差しが 20 回未満の用途なら足りる」「数十回の抜き差しで金が減る」、硬質金は 500〜1000 回以上もつ、としている（出典の
ない目安）。このカセットは挿したまま使う前提で、ゲームの入れ替えは USB か microSD で行う。金が減っても下のニッケルで導通はするが、
接触が不安定になったら端子を無水アルコールで拭く。

**面取りの寸法**: JLCPCB の図では、面取りは 30° ± 5°、端子の銅は基板の端から 1.15 mm（板厚 1.6 mm 以下）手前で止める。注文フォームの
表示では、板厚 1.2 mm・30° の面取りは深さ 0.89 mm、残る厚み 0.4 mm。この基板の端子は端から 1.2 mm 以上（電源・GND の長い 4 本）と
2.0 mm（そのほか）手前で終わるので、面取りは銅に届かない（余裕 0.3 mm 以上）。JLCPCB は必要なら端子の銅を自分で短くする。

## 3. PCB Assembly の指定
| 項目 | 指定 |
|---|---|
| PCBA Type | **Standard** |
| Assembly Side | Top Side |
| PCBA Qty | 2 または 5 |
| Edge Rails/Fiducials | A 案: **Added by Customer**。B 案: Added by JLCPCB |
| Tooling holes（項目が出た場合）| A 案: 自分で付けた側（Added by Customer）。B 案: JLCPCB に任せる側 |
| File provided as（面付けの注文で出る項目）| "Complete File, just proceed with my own files"（BOM と CPL はこの 1 枚で完結している）|
| Confirm Parts Placement | Yes（部品の向きを製造前に画面で確認できる）|
| 部品の選び方 | By Customer (Self-Service)。BOM に LCSC の部品番号が入っている |
| BOM / CPL | `bom_jlc.csv` / `cpl_jlc.csv` |
| 捨て基板を外すサービス（Depaneling）| 選ばない（選ばなければ捨て基板は付いたまま届く。外してもらうのは有料）|

- 実装の Remark にも、PCB Remark の 1)〜3) を貼る（フォームの注意書き: 実装についての Remark は実装の欄に書くこと）。
- JLCPCB は検査用の記号を捨て基板に自動で印刷する（フォームの注意書き）。基板本体には影響しない。
- 部品の照合画面の正しい状態: **10 行・81 点がすべて一致、すべて Basic、未選択の部品なし**。
- 実装しない部品（手はんだ・基板パターン）: J1, U1, U2, U4, U5, U3, U6, J3, J2, J4
- CPL の角度は JLCPCB の部品ライブラリの向きに合わせて補正済み: 抵抗アレイ = 270°、SOT-23（2N7002・BAV99）= 180°、U7（SOIC-8）= 270°
  を、基板上の角度に足してある。JLCPCB は自社の部品ライブラリ（LCSC 番号ごとの EasyEDA のフットプリント）を、CPL の角度だけ
  反時計回りに回して置く（同社の説明: "Positive values are counter clockwise"）。全 81 点について、そのフットプリントを CPL の
  とおりに置いたときに、各パッドが基板の同じ番号のパッドに重なることを確かめてある（`tools/pcb/check_cpl.py`）。
  JLCPCB はライブラリを書き換えることがある（2026 年に 2 点が更新された）ので、**注文する日に `check_cpl.py` をもう一度実行する**。
- **部品プレビューで見る点**（上から見て、端子を下にした向き。下の向きはこのデータの基板から読み取ったもの）:
  1. U7: 1 番ピンの印が**左上**。1〜4 番ピンが左側に、上から下へ並ぶ。
  2. B5819W: D10・D11・D12・D13・D14・D15 はカソードの帯が**下**。
  3. 2N7002 と BAV99（SOT-23）: D1・D2・D3・D4・D5・D6・D7・D8・D9・Q1・Q2・Q3・Q4・Q5・Q6 は足 1 本の側が**右**。
  4. 抵抗アレイ: 30 個すべて長い辺が縦。
  5. SW1: 足が上と下。
  **U7 か B5819W（D10・D11・D12・D13・D14・D15）が 180° 回って見えたら承認しない**（回転の向きが取り違えられると、向きのある部品のうちこの 2 種類が
  逆になる。SOT-23 は 180° 回るとパッドに合わなくなるので、画面で分かる）。

## 4. 費用（JLCPCB の料金表 2026-10-22 更新分から計算。部品代・送料・税は別）
| | 2 枚実装 | 5 枚実装 |
|---|---|---|
| 実装費（Standard・片面） | 約 US$ 51 | 約 US$ 53 |
| 治具（Fixture）費 2 個が加わった場合 | 約 US$ 68 | 約 US$ 69 |

- 内訳: セットアップ $25.56 + ステンシル $8.21 + フィーダー $1.53 × 10 種類 + はんだ付け $0.0016 × 365 接点 × 枚数
  （1 枚あたり最低 $0.48）+ 梱包 $0.50 + 配置確認 $0.45。**部品の種類が 1 つ増えるごとに $1.53** かかる（Standard では Basic と
  Extended で料金は同じ。Basic だけにしているのは、在庫が安定していて入手しやすいから）。
- 治具費は料金表では 1 個 $8.21、29 枚以下は 2 個。どの注文に掛かるかは料金表に書かれていない。料金表にはほかに、ステンシルと
  治具の保管料（各 $4.93）の項目がある。
- PCB 代（5 枚、ENIG 2 U"・金フィンガー・30° 面取り・1.2 mm・Confirm Production file 込み、送料別。2026-11-10 の見積もり画面）:
  A 案の大きさ（103.6 × 85.7 mm）で約 US$ 44、B 案の大きさ（89.6 × 85.7 mm）で約 US$ 40。A 案は 102 × 102 mm 以下の特別価格の対象外で、
  "Panel by Customer" を選んでも見積もりは同じだった。面付けデータは、注文後に JLCPCB が料金を直すことがある（同社の説明）。
- 納期: Standard PCBA の製造は 4 日以上（Economic は 1〜3 日）。
- モジュール（秋月）: 基本構成 ¥4,180（Pico 2 ×2 + XIAO RP2350 ×2）、増設の Pico 2 は 1 枚 ¥990、microSD ソケット ¥150。

## 5. JLCPCB の製造条件との照合
| 項目 | この基板 | JLCPCB の条件 |
|---|---|---|
| 基板サイズ | 89.6 × 85.7 mm（捨て基板込み 103.6 × 85.7 mm）| Standard PCBA は 70 × 70 mm 以上。金フィンガーは 50 × 50 mm 以上 |
| 材質・板厚 | FR-4、1.2 mm | FR-4 は 0.4〜2.0 mm（1.2 mm あり）。板厚の公差は ±10 % |
| 表面処理・端子 | ENIG、金フィンガー、30° 面取り。端子の銅は基板の端の 1.2 mm 以上手前で終わる | 端子の金は ENIG。面取りは 30° か 45°。銅は端から 1.15 mm 手前まで（板厚 1.6 mm 以下、30°）|
| 端子部のレジスト | タブの付け根から 4.0 mm より先（配線を置かない範囲）は、表裏とも端子の間を含めて全面開口 | 金フィンガーの範囲はレジストを全面開口にする（残すと抜き差しで剥がれる）|
| 端子の近く | ビアは端子から 1.0 mm 以上離す。シルクは無い | めっき穴・SMD パッドは金フィンガーから 1.0 mm 以上。端子の近くにレジスト・シルクを置かない（同社の記事の指針）|
| 面取りと面付け | 捨て基板は左右。端子の辺は外周のまま。V カット無し | 面付けして端子が内側に来ると面取りできない |
| 捨て基板（A 案）| 幅 5.0 mm、左右。タブは幅 5.2 mm、穴 0.6 mm、穴の間 0.3 mm。フィデューシャル 3 個（銅 1 mm、開口 2 mm、中心がパネルの端から 3.85 mm）。ツーリング穴 2.0 mm × 4 | 幅 5 mm 以上。ミシン目のタブは幅 5 mm 以上、穴 0.5〜0.8 mm、穴の間 0.2〜0.3 mm。フィデューシャルは 1 mm、中心がパネルの端から 3.85 mm（パッドの縁まで 3.35 mm）、開口は銅の 2 倍、3〜4 個。ツーリング穴 2 mm |
| 配線幅 / 間隔 | 0.15 / 0.15 mm | 0.10 / 0.10 mm 以上（2 層・1 oz）|
| ビア | 径 0.5 mm、穴 0.3 mm | 穴 0.3 mm 以上が標準。径は穴 + 0.1 mm 以上（推奨 + 0.15 mm）。追加料金は「穴 0.3 mm 未満かつ径 0.4 mm 以下」のとき |
| 穴と穴 / 穴と配線 | 0.25 mm 以上 / 0.2 mm 以上 | 0.2 mm 以上 / 0.2 mm 以上 |
| 銅箔と基板端 | 0.3 mm 以上。左右の端は 0.4 mm 以上（タブの穴は基板の外側にあり、穴の縁から銅まで 0.4 mm）| ルーター加工の端 0.2 mm 以上、V カットの端 0.4 mm 以上。穴と配線は 0.2 mm 以上 |
| スリット・切り欠き | 幅 2.4 mm（捨て基板との間は 2.0 mm）。内側の角は R0.5 mm で作図 | 非めっきスリットは幅 1.0 mm 以上。角に丸みの無い角穴・スリットは作れない |
| 外形の公差 | 切り欠きの奥行きとスリットの長さに 0.6 mm、左右の端に 0.2 mm の逃げ | ルーター加工 ±0.2 mm、V カット ±0.4 mm |
| シルク | 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上（英字は大文字だけ）| 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上 |
| レジスト | パッドの開口はパッドと同じ大きさ。開口と開口の間のレジストは 0.25 mm 以上（最小は J3 の 8 番と 9 番のパッドの間） | 0.10 mm 以上（黒・白は 0.13 mm）。開口と隣の配線は 0.09 mm 以上 |
| 実装 | 表面のみ | Standard PCBA は片面・両面とも可 |
| はんだペースト | 手はんだ部品のパッドには置いていない | ステンシルの開口は実装する部品のパッドだけに作られる |

ガーバーの ZIP には製造に使う層（銅箔・レジスト・シルク・ペースト・外形）とドリルだけを入れてある。`tools/pcb/check_jlc.py` は、
2 つの ZIP の中身が基板ファイルを今プロットしたものと同じであること、捨て基板付きの基板の中身（配線・ビア・部品・ベタ・外形）が
基板だけのものと同じであること、捨て基板の寸法（上の表の数値）を、データから測って検査する。

## 6. 受け取ってから
1. 板厚をノギスで測る（1.08〜1.32 mm の範囲で届く）。
2. 捨て基板を外す。A 案はタブの穴の列で折り、端面に残った突起（高さ 0.3 mm 以下）を、基板の端の線までやすりで落とす
   （左右 3 か所ずつ）。B 案は V カットなら折り、端面をやすりで平らにする。
   面取り無しで届いた場合は、端子の辺の角を表裏とも 30〜45° の角度で 0.3〜0.5 mm ほど、目の細かいやすりで落とす
   （端子の銅は端から 1.2 mm 以上手前で終わっているので、金には触れない）。角が立ったままだと本体のコネクタの接点を傷める。
3. **基板だけ**をシェルに入れて、左右の切り欠き・スリット・端子タブの位置を確かめる。タブの付け根など、内側の角に残る丸みが
   シェルに当たる場合は、やすりで落とす。
   あわせて、**基板の表・裏それぞれからシェルの内壁までの隙間**を測る（ノギスの深さ測定か、粘土を挟んで閉じる）。この寸法は
   どの資料にも無かった。必要な高さの目安（基板の厚み＋コネクタの一般的な寸法からの見積もりで、実測ではない）:
   **表（ラベル面）** = XIAO（U3・U6）約 4.5 mm、増設の Pico 2（U4）約 3.8 mm、microSD ソケット約 2 mm、実装済みの部品は最大約 2.2 mm（U7）。
   **裏** = Pico 2（U1・U2・U5）約 3.8 mm。任天堂の純正基板は背の高い部品を裏（31〜60 番の面）に載せているので、表のほうが狭い
   可能性がある。表の隙間が XIAO に足りない場合、この版ではシェルの表側を閉じられない（表側のシェルの内側を削るか、開けたまま
   使い、次の版で XIAO を裏に移す）。動作には影響しない。
4. モジュールに**ファームを書き込んでから**はんだ付けする（U2 の USB 端子は基板の内側を向くので、付けたあとはケーブルを挿しにくい）。
   Pico 2 は、USB コネクタの固定足 4 か所（裏面に出ている）のはんだが盛り上がっていれば、先に平らにする（基板から浮くため）。
5. はんだ付けの順番: 裏面（U2 → U1、増設するなら U5）を先に、表面を後に。表面は **U6 → J3（使うなら）→ U4（増設するなら）**、
   U3 はいつでもよい。U2 を付けるときは、すぐ下の金フィンガーにはんだやフラックスが付かないよう、端子をテープで覆う。
   基板のシルクに `U1 CPU` のように役割が書いてある。シルクの `USB` の字がある側に、モジュールの USB 端子を向ける
   （XIAO は 180° 回しても載ってしまい、その向きでは 5 V が別のピンに入る）。
6. Pico 2 は端面（キャステレーション）40 か所だけをはんだ付けする。XIAO は縁の 14 ピンだけ（裏面パッドは使わない）。
   付けたあと、はんだブリッジが無いか見る所: U3 の 4・5 番パッドと RN24（0.89 mm）、U6 の 14 番パッドと J3（0.97 mm）。
7. XIAO の 5V ピンは USB の VBUS と直結している。**本体の電源が入っている間は、電源の入っていない PC やハブに U3・U6 の USB を
   つながない**（本体の 5 V が USB ケーブル側へ出る）。

## 7. 手はんだ部品（秋月電子）
| 部品 | 秋月 通販コード | 価格 | 位置 |
|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 ×2（＋増設 ×2）| **裏**: U2（下、PPU 側）・U1（上、CPU 側）・U5（中、PPU 側の増設）／**表**: U4（上、CPU 側の増設）|
| Seeed XIAO RP2350 | 129619 | ¥1,100 ×2 | **表**: U3（中央右、IRQ・拡張音源・ネームテーブル制御）・U6（上、ハブ: SFC チップ機能・保存・更新）|
| microSD ソケット Hirose DM3AT-SF-PEJM5 | 102395 | ¥150（任意）| **表**: J3（右上）|

## 出典（JLCPCB 公式、2026-11-10 に確認。同社のヘルプ記事は更新日が変わるので、注文する日にもう一度読む）
- 実装仕様（Economic / Standard の違い、金フィンガー、基板サイズ、面付けの種類）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- 基板の製造仕様（配線・ビア・外形・スリット・シルク・レジスト・板厚の公差、"Mouse bites Panel" の行: タブ・ミシン目・ツーリング穴・フィデューシャルの数値）: https://jlcpcb.com/capabilities/pcb-capabilities
- 追加料金になる場合（小径穴、金の厚さ、面付けと特別価格）: https://jlcpcb.com/help/article/In-what-cases-will-there-be-charged-extra
- 金フィンガー（面取りの角度、面付けと面取り、端子部のレジスト全面開口、銅の後退）: https://jlcpcb.com/help/article/jlcpcb-gold-fingers
- 面取りの寸法の図: https://jlcpcb.com/blog/considerations-for-gold-finger-bevel-design
- 金フィンガーの設計の指針（めっき穴・パッドは端子から 1.0 mm 以上）: https://jlcpcb.com/blog/pcb-gold-fingers
- 硬質金めっきと ENIG、JLCPCB が硬質金を扱わないこと: https://jlcpcb.com/blog/hard-gold-pcb-finish
- 捨て基板とフィデューシャル（図: フィデューシャルのパッドの縁から基板の端まで 3.35 mm 以上）: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- 注文フォーム（捨て基板は長い辺に付く旨の注意書き、Delivery Format の定義、Beveling、Confirm Production file、Mark on PCB、見積もり）: https://cart.jlcpcb.com/quote
- 注文番号の印字の廃止: https://jlcpcb.com/help/article/how-to-mark-on-pcb
- 面付けと V カットの条件: https://jlcpcb.com/help/article/pcb-panelization
- 実装の料金表（2026-10-22 更新）: https://jlcpcb.com/help/article/pcb-assembly-price
- 実装の FAQ（面付けの方法、フィデューシャル）: https://jlcpcb.com/help/article/pcb-assembly-faqs
- BOM と CPL の書式（回転は反時計回りが正）: https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly 、 https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly
- ステンシルの開口: https://jlcpcb.com/help/article/smt-stencil-data-prepared-for-smt-orders
- 部品の向きの補正表（KiBot。JLCPCB 向けの回転の一覧）: https://kibot.readthedocs.io/en/latest/notes_position.html
