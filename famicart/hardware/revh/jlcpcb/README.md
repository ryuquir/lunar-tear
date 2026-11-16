# JLCPCB 注文パッケージ（famicart rev H: RP2350B ×8、JLCPCB の実装だけで完成）

回路・配置・部品の選び方は `docs/13_rev_h_plan.md`、外形図は `../outline.png`、配置図は `../placement.png`。
**基板はシェルの裏（主な部品面）から見て描いてある**: KiCad の表（F.Cu）＝ JLCPCB の Top ＝ シェルの裏。端子は Top に 31〜60 番、
Bottom に 1〜30 番。JLCPCB の Bottom（シェルの表、ラベル面）には、180° 回っても同じ働きの受動部品だけを置いてある。

**状態**: 実機では未検証。手はんだの部品は無く、全部品を JLCPCB が実装する。**シェルへの収まり（特に表の隙間）は実物で確かめて
から注文する**（`docs/13_rev_h_plan.md` の「立ち上げの手順と合格基準」の 0）。最初の注文は最少枚数にする。

| ファイル | 内容 |
|---|---|
| `gerbers_rails.zip` | **注文に使うデータ**: 基板＋左右と上の捨て基板（ミシン目のタブでつないだ 1 枚）。103.6 × 92.7 mm、6 層 |
| `gerbers.zip` | 基板だけ（89.6 × 85.7 mm）。注文には使わない（上端の USB-C と microSD が「部品の本体は基板の端から 2.5 mm 以上」の条件を満たすには、上の捨て基板が要る） |
| `bom_jlc.csv`、`cpl_jlc.csv` | 部品表と配置。CPL は両面（Top と Bottom） |
| `rails.png` | 捨て基板の位置の図。JLCPCB への問い合わせに添付する |
| `parts_check.csv`、`cpl_check.csv` | 部品の区分（宣言した Basic / Extended）・在庫と、部品の向きの検査結果 |

このデータの基板は、配線 9078 本・ビア 926 個・未接続 0。

## 1. 注文の種類と、捨て基板
- 金フィンガー付きの基板は **Economic PCBA では受け付けられない**。**Standard PCBA** で、実装は**両面**（Top 136 点、Bottom 160 点）、
  25 種類・296 点/枚。Standard PCBA では Basic と Extended のフィーダー料金は同じ（1 種類 $1.53）。
- 捨て基板は自分で描き込んである（JLCPCB に付けてもらうと、上の辺に付かない・端子の辺に付く、のどちらかになる）。全体 103.6 × 92.7 mm、基板は 1 枚。
  - 左・右・上の 3 本で 1 つの枠になっている。幅 5.0 mm、基板との間は幅 2.0 mm のルーター加工の溝で、V カットは無い。
  - 端子の辺には何も付かない。左右の捨て基板は端子の辺の線より 2.7 mm 手前で終わる（面取りの刃が通る所を空けるため）。
  - 基板とは、左右に各 3 か所、上に 3 か所のタブ（幅 5.2 mm）でつながる。タブには直径 0.6 mm の穴が 7 個、
    穴と穴の間を 0.3 mm 空けて並ぶ（ミシン目）。穴は基板の端の線に外側から接している。折り取った跡は高さ 0.3 mm 以下。
  - USB-C と microSD の口は基板の上端にそろえてあり、縁が上の溝に少し出る（上のタブはその前を避けてある）。
  - フィデューシャルが表と裏に 3 個ずつ（両面の同じ位置。銅 1 mm、レジスト開口 2 mm、中心がパネルの端から 3.85 mm）と、
    ツーリング穴 4 個（直径 2.0 mm、めっき無し）が捨て基板の上にある。
- 注文画面では **Delivery Format を "Panel by Customer"（Panel Format は Column 1・Row 1）**、実装の **Edge Rails/Fiducials を
  "Added by Customer"** にする。

**支払いの前に**: 次をサポート（チャット）に `rails.png` を添えて確かめる。質問文（そのまま貼る）:

> I am going to order a 6-layer board, 1.2 mm, ENIG, gold fingers (30 on each side) with a 30 degree bevel, and Standard PCBA
> on both sides. Please see the attached drawing. My Gerber file already contains edge rails that I drew myself on the left, right
> and top edges (one frame, 5.0 mm wide), joined to the board by mouse-bite tabs (5.2 mm wide, 0.6 mm holes) across a 2.0 mm
> routed gap. There is no V-cut. The rails end 2.7 mm above the gold-finger edge, so that edge is completely free. The rails carry
> 3 fiducials on each side (top and bottom) and 4 tooling holes (2.0 mm). Panel size 103.6 x 92.7 mm, one board per panel.
> 1) Can you bevel the gold-finger edge of this board?
> 2) Is this rail arrangement accepted for Standard PCBA on both sides?
> 3) Which Delivery Format must I select: Single PCB or Panel by Customer (1 x 1)? Is there an extra charge?
> 4) The USB-C receptacle TYPE-C-31-M-12 (C165948) has four plated through-hole shell legs. Are they soldered in your assembly process
> without a hand-soldering charge?
> 5) Do you X-ray only the QFN parts (C42415655), or also the crystals (C362368) and the inductors (C135262)?

答えに応じて変える所:
- 1) が「面取りできない」の場合: 止まって確認する（捨て基板を外して端子の辺に付ける提案は断る）。
- 2) が「この捨て基板では実装できない」の場合: 足りない寸法を聞き、設計の `RAILS` を直してデータを作り直す。
- 4)・5) で追加料金がある場合: 4 章の見積もりに加える（`docs/13_rev_h_plan.md` の費用の表の「加わりうるもの」）。

## 2. PCB の指定（Instant Quote → Add gerber file → `gerbers_rails.zip`）
| 項目 | 指定 |
|---|---|
| Base Material / Layers | FR-4 / **6** |
| Dimensions | 103.6 × 92.7 mm（ガーバーから自動で入る）|
| PCB Qty | 5（Delivery Format を Panel by Customer にすると、項目名が Panel Qty に変わる）|
| Delivery Format | **Panel by Customer**、Panel Format は Column 1・Row 1 |
| PCB Thickness | **1.2 mm** |
| Layer Stackup | **JLC06121H-3313**（外層の下 0.0994 mm、芯 0.35 mm、中央 0.1164 mm。基板ファイルの積層と同じ。選べない場合は止まって確認）|
| PCB Color / Silkscreen | Green / White |
| Surface Finish | **ENIG**、Gold Thickness は **2 U"** |
| Outer Copper Weight | 1 oz |
| Inner Copper Weight | **0.5 oz** |
| Min via hole size/diameter | **0.3mm/(0.4/0.45mm)**（既定のまま。設計値: 標準のビアは穴 0.3 mm・径 0.5 mm、穴 0.3 mm 未満のビア 0 個は径 0.45 mm 以上。注文画面: 多層で径 0.45 mm 以上なら 0.2 mm の穴も追加料金なし。「0.2mm」を選ぶと見積もりが上がる）|
| Via Covering | **Epoxy Filled & Capped**（6 層では無料。QFN の中央パッドのビアもこれで埋める）|
| Board Outline Tolerance | ±0.2 mm（Regular）|
| Mark on PCB | **Remove Mark** |
| Electrical Test | Flying Probe Fully Test |
| Gold Fingers | **Yes**、Beveling **30°** |
| Confirm Production file | **Yes**（約 $1）。選ぶと出る画面では **"Do not confirm automatically"** を選ぶ |

製造データ（Production file）が届いたら、承認する前に次を確かめる: 捨て基板が左右と上にあること、端子の辺に捨て基板も V カットの線も
無いこと、面取りの指示が入っていること、積層が JLC06121H-3313 であること、外形の切り欠きとスリットが図面どおりであること。

PCB Remark（そのまま貼る）:

> 1) This is ONE board with edge rails that I drew myself on the left, right and top edges (one frame, 5.0 mm wide), joined by
> mouse-bite tabs (5.2 mm wide, 0.6 mm holes) across a 2.0 mm routed gap: panel 103.6 x 92.7 mm, one board per panel. 3 fiducials
> on each side (top and bottom) and 4 tooling holes (2.0 mm) are on the rails. Please do NOT add other rails and do NOT add V-cut.
> 2) Gold fingers are on ONE edge only: the bottom edge with the 78.4 mm wide tab (30 fingers on each side). Please bevel this edge
> 30 degrees. This edge must stay a free routed edge; the rails end 2.7 mm above it.
> 3) If you cannot bevel a board with these rails, do NOT move or change the rails: put the order on hold and contact me.
> 4) Stackup JLC06121H-3313, inner copper 0.5 oz. Vias: 0.3 mm holes; the vias with 0.2 mm holes have pads of at least 0.45 mm, so I
> left "Min via hole size" at 0.3mm/(0.4/0.45mm). All vias epoxy filled and capped, including the vias in the QFN exposed pads.
> 5) You may shorten the finger copper to your standard setback for the bevel.
> 6) The solder mask window over the gold fingers is intentional. The outline has two side notches, one inner slot and cut corners
> beside the tab; inner corners are drawn with R 0.5 mm. Please keep them as drawn.

## 3. PCB Assembly の指定
| 項目 | 指定 |
|---|---|
| PCBA Type | **Standard** |
| Assembly Side | **Both Sides**（Top: 主な部品、Bottom: 受動部品だけ）|
| PCBA Qty | 2 または 5 |
| Edge Rails/Fiducials | **Added by Customer** |
| Tooling holes（項目が出た場合）| Added by Customer |
| File provided as（面付けの注文で出る項目）| "Complete File, just proceed with my own files" |
| Confirm Parts Placement | Yes。期限までに確認しないと自動で承認されるので、選ぶと出る画面では **"Do not confirm automatically"** を選ぶ |
| Parts Selection（部品の選び方）| By Customer (Self-Service)。BOM に LCSC の部品番号が入っている |
| X-ray Inspection（項目が出た場合）| **Yes**（QFN などの見えない接合 8 個/枚。項目が無くても料金表では自動で掛かる）|
| BOM / CPL | `bom_jlc.csv` / `cpl_jlc.csv` |
| 捨て基板を外すサービス（Depaneling）| 選ばない |

- 実装の Remark には、PCB Remark の 1)〜3) を貼る。
- 部品の照合画面の正しい状態: **25 行・296 点がすべて一致、Basic 17 行・Extended 8 行（Extended は設計が宣言した 8 品番だけ: C12035 4D03WGJ0681T5E 680R x4 0603、C135262 SMNR4020-2.2UH 2.2uH 4x4、C141836 TLV62569DBVR 2A buck SOT-23-5、C165948 HRO TYPE-C-31-M-12 USB-C、C25100 0402WGF270JTCE 27R 0402、C362368 TXM12M0004322CBCDO00T 12MHz 9pF 3225、C42415655 RP2350B QFN-80、C91145 HRO TF-01A microSD）、未選択の部品なし**。
  宣言に無い Extended の行、在庫が足りない行（`parts_check.csv` の条件: 在庫が必要数の 3 倍以上、予約可能数が必要数以上）、不一致があれば止める。
  Extended であること自体は問題ない（Standard PCBA ではフィーダー料金が Basic と同じ）。
- 実装しない部品: J1, TP1, TP2, TP3, TP4, TP5, TP6, J2, J4, J5, J6
- **RP2350B（C42415655）は 1 品番だけで在庫が薄い**（JLCPCB の予備も 0）。1 枚に 8 個。注文する日に在庫を確かめ、5 枚なら先に JLCPCB の
  部品在庫として 40 個（＋予備 2 個）を買って確保する。2 枚なら 16 個。
- Bottom の 160 点は、180° 回っても同じパッドに同じ働きで載る部品（チップ抵抗・コンデンサ、1 kΩ ×4 アレイ、3225 水晶）だけ。
  JLCPCB は裏面の角度の決まりを公開していないので、Bottom の角度は KiBot が JLCPCB 向けとして載せている規則（180° − KiCad の角度 ＋ 補正）で書き、
  `check_cpl.py` はその両方の読み方（鏡映、鏡映＋180°）でパッドが合うことを確かめてある。**最初の注文では、部品の配置の確認画面で Bottom の向きも見る。**
- CPL の角度は JLCPCB の部品ライブラリの向きに合わせて補正済み。JLCPCB はライブラリを書き換えることがあるので、**注文する日に `check_cpl.py` を
  もう一度実行する**。
- **部品プレビューで見る点**（Top を上から見て、端子を下にした向き）:
  1. U7: 1 番ピンの印が**左上**。1〜4 番ピンが左側に、上から下へ並ぶ。
  2. B5819W: D10 はカソードの帯が**右**、D11 はカソードの帯が**左**。
  3. 2N7002 と BAV99（SOT-23）: Q7 は足 1 本の側が**右**、D5・D6・D7・D8・D9・Q1・Q2・Q3・Q4・Q5・Q6 は足 1 本の側が**左**。
  4. 抵抗アレイ: 38 個すべて長い辺が縦。
  5. SW1: 足が左と右。

## 4. 費用（JLCPCB の料金表 2026-10-22 更新分から計算。部品代・送料・税は別）
| | 2 枚実装 | 5 枚実装 |
|---|---|---|
| 実装費（Standard・両面、X 線検査込み） | 約 US$ 125 | 約 US$ 152 |
| 治具（Fixture）費 2 個が加わった場合 | 約 US$ 141 | 約 US$ 169 |

- 内訳: 両面のセットアップ $51.12 + ステンシル $16.42 + フィーダー $1.53 × 25 種類 + はんだ付け $0.0016 × 1611 接点 × 枚数
  （1 枚あたり最低 $0.48）+ X 線検査 8 個/枚 × 枚数（料金表の段階で 1 個 $0.82〜$1.64）+ 梱包 $0.50 + 配置確認 $0.45。
- PCB 代（5 枚、6 層、上の捨て基板込み、ENIG 2 U"・金フィンガー・30° 面取り・1.2 mm・Epoxy Filled & Capped・Confirm Production file 込み、
  送料別。2026-11-14 の見積もり画面）: 約 US$ 75。最小ビアに「0.2mm」を選ぶと約 US$ 113 になる（だから既定のままにする）。
- 部品代（2026-11-14 の部品データ）: 2 枚で約 US$ 63、5 枚で約 US$ 140。RP2350B の事前購入はこの中に入る。

## 5. 受け取ってから
1. 板厚をノギスで測る（1.08〜1.32 mm）。
2. 捨て基板を外す: タブの穴と穴の間をニッパーで切り（基板を折り曲げない）、端面の突起を基板の端の線までやすりで落とす。
3. 通電の前に `docs/13_rev_h_plan.md` の「立ち上げの手順と合格基準」の 1（+1V1・+3V3 の短絡と分圧抵抗の値）を行う。

## 出典（JLCPCB 公式。注文する日にもう一度読む）
- 実装仕様（金フィンガーは Standard PCBA のみ、両面実装）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- 製造仕様（6 層の最小ビア、ミシン目パネル、PTH の環状幅）: https://jlcpcb.com/capabilities/pcb-capabilities
- ビアの処理（Epoxy Filled & Capped）: https://jlcpcb.com/help/article/pcb-via-covering 、パッド上のビア: https://jlcpcb.com/help/article/via-in-pad-pofv-guide
- 積層: https://jlcpcb.com/impedance
- 金フィンガー（面取り、端子部のレジスト全面開口）: https://jlcpcb.com/help/article/jlcpcb-gold-fingers
- 捨て基板とフィデューシャル: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- 実装の料金表（2026-10-22 更新、X 線検査・両面）: https://jlcpcb.com/help/article/pcb-assembly-price
- BOM と CPL の書式（回転は反時計回りが正）: https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly
- 裏面の角度（KiBot の JLCPCB 向けの規則）: https://kibot.readthedocs.io/en/latest/notes_position.html
