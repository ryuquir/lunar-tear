# ファミコン基板（famicart rev H）発注指示書

この文書は、発注を代行する GrokBOT に向けた手順書です。JLCPCB への基板と部品実装（全部品、両面）の発注を扱います。手はんだの部品は無く、ほかの店での買い物はありません。書いてあるとおりに進め、「止まって確認」とある所では必ず依頼者（このフォルダの持ち主）の返事を待ってください。

## 依頼の内容

- JLCPCB に、基板 **5 枚**の製造と、そのうち **2 枚**への部品実装（Standard PCBA、**両面**）を発注する。
- 部品はすべて JLCPCB が載せる。**Basic 17 行・Extended 8 行**で、Extended はこの設計が宣言した 8 品番（C12035 4D03WGJ0681T5E 680R x4 0603、C135262 SMNR4020-2.2UH 2.2uH 4x4、C141836 TLV62569DBVR 2A buck SOT-23-5、C165948 HRO TYPE-C-31-M-12 USB-C、C25100 0402WGF270JTCE 27R 0402、C362368 TXM12M0004322CBCDO00T 12MHz 9pF 3225、C42415655 RP2350B QFN-80、C91145 HRO TF-01A microSD）。Extended があること自体は正しい（Standard PCBA では Basic と同じ料金）。

## 必ず守ること

1. **注文を確定する直前（支払いの直前）で止まる。** 注文内容と合計金額（送料・手数料・税を含む）を依頼者に見せ、承認をもらってから確定と支払いをする。依頼者があらかじめ上限金額を決めて任せていて、合計がその範囲に収まる場合だけ、この確認を省いてよい。
2. **ログイン情報、配送先、支払い方法は依頼者から受け取る。** このフォルダにも、この文書にも書かれていない。受け取った情報を、JLCPCB 以外に渡さない。
3. **判断が要る所で推測しない。** この文書の表にある項目で、書かれている値を選べない場合は、止まって依頼者に聞く。表に無い項目は、基板・実装とも、最初から選ばれている値のままにする。ただし、最初から選ばれている値が無くて自分で選ばないと進めない項目と、選ぶと追加料金が出る項目は、止まって確認する（下の「止まって確認する場面」）。
4. **JLCPCB からの提案を自分で承諾しない。** 担当者やサポートが、この文書と違うやり方（捨て基板の位置を変える、V カットにする、面取りをやめる、部品を別の品番に替える、など）を提案してきたら、内容を依頼者に伝えて指示を待つ。
5. **部品を別の品番に替えない。** JLCPCB の画面が出す代替部品の候補は選ばない。

## このフォルダのファイル

| ファイル | 使い道 |
|---|---|
| `gerbers_rails.zip` | **これを使う**。基板と左右・上の捨て基板を 1 枚にまとめた製造データ（6 層）。大きさ 103.6 × 92.7 mm |
| `gerbers.zip` | 基板だけのデータ（89.6 × 85.7 mm）。**注文には使わない**（上の捨て基板が無いと、上端のコネクタが実装の条件を満たさない） |
| `bom_jlc.csv` | 実装する部品の表 |
| `cpl_jlc.csv` | 部品の位置と向き（Top と Bottom の両面） |
| `rails.png` | JLCPCB のサポートへの質問に添付する図 |
| `jlcpcb_support_question.txt` | サポートへの質問文（英語）。そのまま送る |
| `jlcpcb_pcb_remark.txt`、`jlcpcb_assembly_remark.txt` | 注文フォームに貼る Remark（PCB 用と実装用） |
| `jlcpcb_order_notes.md` | 設計者が書いた注文メモの全文。この文書と食い違う所は、この文書に従う。メモに出てくる `docs/…` や `tools/pcb/…` のファイルはこのフォルダに無いので、探さなくてよい |
| `outline.png`、`placement.png` | 基板の外形図と部品の配置図（参考。シェルの裏、主な部品面から見た図） |
| `parts_check.csv`、`cpl_check.csv` | JLCPCB の部品の区分（宣言した Basic / Extended）・在庫と、部品の向きを照合した結果（参考。2026-11-14 時点） |

## 数量

| 品目 | 数量 | 補足 |
|---|---|---|
| 基板（PCB Qty） | 5 枚 | 注文できる最少の枚数 |
| 部品実装（PCBA Qty） | 2 枚 | 残りの 3 枚は部品なしの基板で届く |

## JLCPCB の手順

### 支払いの前にサポートへ質問する

この基板は端に金めっきの接点（金フィンガー）があり、その辺を斜めに削る加工（面取り）を頼みます。実装に必要な捨て基板は、左右と上の 3 辺にデータの中で描き込んであります。この組み合わせで面取りと両面の実装をしてもらえるかは、JLCPCB のどのページにも書かれていません。そのため、注文の前に確かめます。

1. JLCPCB のサポートに、`jlcpcb_support_question.txt` の英文を送り、`rails.png` を添付する。GrokBOT から送れない場合は、文面と図を依頼者に渡して送ってもらう。
2. 回答の全文を依頼者に報告する。
3. 回答に応じて、下の表のとおりに進める。

質問文（`jlcpcb_support_question.txt` と同じ内容）:

> I am going to order a 6-layer board, 1.2 mm, ENIG, gold fingers (30 on each side) with a 30 degree bevel, and Standard PCBA on both sides. Please see the attached drawing. My Gerber file already contains edge rails that I drew myself on the left, right and top edges (one frame, 5.0 mm wide), joined to the board by mouse-bite tabs (5.2 mm wide, 0.6 mm holes) across a 2.0 mm routed gap. There is no V-cut. The rails end 2.7 mm above the gold-finger edge, so that edge is completely free. The rails carry 3 fiducials on each side (top and bottom) and 4 tooling holes (2.0 mm). Panel size 103.6 x 92.7 mm, one board per panel.
> 1) Can you bevel the gold-finger edge of this board?
> 2) Is this rail arrangement accepted for Standard PCBA on both sides?
> 3) Which Delivery Format must I select: Single PCB or Panel by Customer (1 x 1)? Is there an extra charge?
> 4) The USB-C receptacle TYPE-C-31-M-12 (C165948) has four plated through-hole shell legs. Are they soldered in your assembly process without a hand-soldering charge?
> 5) Do you X-ray only the QFN parts (C42415655), or also the crystals (C362368) and the inductors (C135262)?

| 質問 | 回答 | すること |
|---|---|---|
| 1) 面取りできるか | できる | 次へ進む |
| 1) 面取りできるか | できない | **止まって確認。** |
| 2) この捨て基板で両面の実装ができるか | できる | 次へ進む |
| 2) この捨て基板で両面の実装ができるか | できない、または条件つき | **止まって確認。** 足りない点を聞き取って依頼者に伝える。データの作り直しが要る |
| 3) Delivery Format | Panel by Customer | この文書のとおりに選ぶ |
| 3) Delivery Format | Single PCB | Delivery Format を Single PCB にする。追加料金の説明があれば依頼者に伝える |
| 4)・5) 追加料金 | 追加料金がある | 金額を依頼者に伝える（止まって確認） |

2 営業日たっても回答が無い場合、回答があいまいな場合、質問 1)〜3) のどれかに答えが無い場合は、支払いへ進まずに、止まって依頼者に確認してください。

### 基板（PCB）の指定

1. [注文フォーム](https://cart.jlcpcb.com/quote) を開き、"Add gerber file" に `gerbers_rails.zip` を上げる。
2. 読み込まれた大きさ（Dimensions）が **103.6 × 92.7 mm**、層の数が **6** であることを確かめる。違う場合は止まって確認。
3. 下の表のとおりに選ぶ。表に無い項目は、最初から選ばれている値のままにする。
4. PCB Remark の欄に、`jlcpcb_pcb_remark.txt` の英文をそのまま貼る。欄に全文が入らない場合は、自分で削らずに止まって確認。

| 項目 | 選ぶ値 |
|---|---|
| Base Material | FR-4 |
| Layers | **6** |
| PCB Qty（Delivery Format を Panel by Customer にすると、項目名が Panel Qty に変わる） | 5 |
| Product Type | Industrial/Consumer electronics |
| Different Design | 1 |
| Delivery Format | **Panel by Customer**。Panel Format は Column 1、Row 1（サポートが Single PCB と答えた場合はそれに合わせる）。"Panel by JLCPCB" は選ばない |
| PCB Thickness | **1.2 mm** |
| Layer Stackup | **JLC06121H-3313**（選べない場合は止まって確認） |
| PCB Color | Green |
| Silkscreen | White |
| Surface Finish | **ENIG**。Gold Thickness は **2 U"** |
| Outer Copper Weight | 1 oz |
| Inner Copper Weight | **0.5 oz** |
| Min via hole size/diameter | **0.3mm/(0.4/0.45mm)**（最初に選ばれている値のまま。「0.2mm」は選ばない） |
| Via Covering | **Epoxy Filled & Capped** |
| Board Outline Tolerance | ±0.2 mm（Regular） |
| Mark on PCB | Remove Mark |
| Electrical Test | Flying Probe Fully Test |
| Gold Fingers | **Yes**。Beveling は **30°** |
| Castellated Holes | No |
| Confirm Production file | **Yes**。選ぶと出る画面では **"Do not confirm automatically"** を選ぶ |

PCB Remark に貼る文（`jlcpcb_pcb_remark.txt` と同じ内容）:

> 1) This is ONE board with edge rails that I drew myself on the left, right and top edges (one frame, 5.0 mm wide), joined by mouse-bite tabs (5.2 mm wide, 0.6 mm holes) across a 2.0 mm routed gap: panel 103.6 x 92.7 mm, one board per panel. 3 fiducials on each side (top and bottom) and 4 tooling holes (2.0 mm) are on the rails. Please do NOT add other rails and do NOT add V-cut.
> 2) Gold fingers are on ONE edge only: the bottom edge with the 78.4 mm wide tab (30 fingers on each side). Please bevel this edge 30 degrees. This edge must stay a free routed edge; the rails end 2.7 mm above it.
> 3) If you cannot bevel a board with these rails, do NOT move or change the rails: put the order on hold and contact me.
> 4) Stackup JLC06121H-3313, inner copper 0.5 oz. Vias: 0.3 mm holes; the vias with 0.2 mm holes have pads of at least 0.45 mm, so I left "Min via hole size" at 0.3mm/(0.4/0.45mm). All vias epoxy filled and capped, including the vias in the QFN exposed pads.
> 5) You may shorten the finger copper to your standard setback for the bevel.
> 6) The solder mask window over the gold fingers is intentional. The outline has two side notches, one inner slot and cut corners beside the tab; inner corners are drawn with R 0.5 mm. Please keep them as drawn.

### 部品実装（PCB Assembly）の指定

1. PCB Assembly を有効にし、下の表のとおりに選ぶ。表に無い項目は、最初から選ばれている値のままにする。
2. BOM に `bom_jlc.csv`、CPL に `cpl_jlc.csv` を上げる。
3. 部品の照合画面で、**25 行・296 点がすべて一致し、Basic 17 行・Extended 8 行（宣言済みの Extended は 8 品番: C12035 4D03WGJ0681T5E 680R x4 0603、C135262 SMNR4020-2.2UH 2.2uH 4x4、C141836 TLV62569DBVR 2A buck SOT-23-5、C165948 HRO TYPE-C-31-M-12 USB-C、C25100 0402WGF270JTCE 27R 0402、C362368 TXM12M0004322CBCDO00T 12MHz 9pF 3225、C42415655 RP2350B QFN-80、C91145 HRO TF-01A microSD）で、未選択の部品が無い**ことを確かめる。Extended の行があること自体は正しい。**宣言済みの一覧に無い Extended の行、在庫が足りない行（2 枚分に足りない、または在庫切れ）、不一致、未選択があれば止まって確認。**代替部品の候補は選ばない。
4. RP2350B（C42415655）の在庫を確かめる。1 枚に 8 個、2 枚で 16 個要る。在庫が 48 個より少ない場合は止まって確認。設計者は、在庫が薄いので部品を先に確保すること（JLCPCB の部品在庫として 16 個＋予備 2 個を先に買う）を勧めている。先に買うかどうかは依頼者に聞く。
5. 部品の配置のプレビューで、下の「部品の向きの確認」の 9 点と、Bottom（裏）の 160 点がパッドに重なっていることを確かめる。
6. 実装用の Remark の欄に、`jlcpcb_assembly_remark.txt` の英文をそのまま貼る。欄に全文が入らない場合は、自分で削らずに止まって確認。
7. カートに入れ、配送方法の候補とそれぞれの金額を控える。配送方法は依頼者が選ぶ。
8. 支払う日が 2026-11-14 より後になる場合は、支払いの前に止まり、依頼者に「部品の区分と在庫の確認（`gen_jlc.py`）と部品の向きの照合（`check_cpl.py`）を今日もう一度実行して、合格したか」を確かめてもらう。この道具はこのフォルダに無く、GrokBOT は実行できない。
9. 合計金額と内訳を依頼者に見せ、承認をもらってから支払う（「必ず守ること」の 1）。

| 項目 | 選ぶ値 |
|---|---|
| PCBA Type | **Standard**（Economic は金フィンガー付きの基板を受け付けない） |
| Assembly Side | **Both Sides** |
| PCBA Qty | 2 |
| Edge Rails/Fiducials | **Added by Customer** |
| Tooling holes（項目が出た場合） | Added by Customer |
| File provided as（項目が出た場合） | Complete File, just proceed with my own files |
| Confirm Parts Placement | **Yes**。選ぶと出る画面では **"Do not confirm automatically"** を選ぶ（この選択肢が出ない場合は止まって確認） |
| Parts Selection（部品の選び方） | By Customer (Self-Service) |
| X-ray Inspection（項目が出た場合） | **Yes** |
| 捨て基板を外すサービス（Depaneling） | 選ばない |

実装しない部品（照合画面に出なくて正しいもの）: J1, TP1, TP2, TP3, TP4, TP5, TP6, J2, J4, J5, J6。

### 部品の向きの確認

プレビューは、基板を上（Top）から見て、金色の接点が下に来る向きで確かめます。Bottom の部品（160 点）は、向きのない受動部品だけです。パッドに重なっていれば正しい。

1. RP2350B（QFN-80）: U1・U3・U5・U9 は 1 番ピンの角が**右下**（1〜20 番ピンが右の辺）、U2・U4・U6・U8 は 1 番ピンの角が**左上**（1〜20 番ピンが左の辺）。
2. W25Q128JVSIQ（SOIC-8）: U11・U13・U15・U19 は 1 番ピンの印が**右下**（1〜4 番ピンが右側に下から上へ並ぶ）、U7・U12・U14・U16・U18 は 1 番ピンの印が**左上**（1〜4 番ピンが左側に上から下へ並ぶ）。
3. TLV62569（SOT-23-5）: U20 は 1 番ピンが**右下**（足 3 本の側が右）、U21 は 1 番ピンが**左上**（足 3 本の側が左）。
4. 2N7002 と BAV99（SOT-23）: D5・D6・D7・D8・D9・Q1・Q2・Q3・Q4・Q5・Q6 は足 1 本の側が**左**、Q7 は足 1 本の側が**右**。
5. B5819W（SOD-123）: D10 はカソードの帯が**右**、D11 はカソードの帯が**左**。
6. LED: D21・D22・D23・D24・D25・D26・D28・D29 はカソード（K）の印が**左**。
7. 差し込み口: J3・J7 は口が**上**（基板の端）。
8. タクトスイッチ: SW1・SW2・SW3 は足が左と右。
9. 抵抗アレイ（Top）: 32 個すべて長い辺が縦。

**向きのある部品が 180° 回って見える場合や、パッドからずれて見える場合は、承認せずに止まって確認してください。**

### 金額の目安

- 基板: 約 US$ 75（5 枚。2026-11-14 の見積もり画面の値。6 層、ENIG、金フィンガー、面取り、Epoxy Filled & Capped、Confirm Production file を含み、送料は別）。
- 実装: 約 US$ 125（2 枚、両面、X 線検査込み。JLCPCB の料金表〔2026-10-22 更新〕から計算した値で、見積もり画面では確かめていない。治具の費用が加わると約 US$ 141）。部品代は見積もり画面に出る金額で、この文書では計算していない。
- 送料、関税、消費税は、見積もり画面と配送業者の案内による。この文書では確かめていない。
- 比べるのは項目ごと。基板の代金（送料を除く）が US$ 97 を超える場合、または実装の料金（部品代を除き、治具の費用を含む）が US$ 183 を超える場合は、止まって、どの項目が高いかを添えて依頼者に伝える。

### 注文したあと

1. 製造データ（Production file）の確認依頼が届いたら、承認する前に依頼者に見せる。確かめる点は、捨て基板が左右と上にあること、金色の接点の辺に捨て基板も V カットの線も無いこと、面取りの指示が入っていること、積層が JLC06121H-3313 であること。
2. 部品の配置の確認依頼（Confirm Parts Placement）が届いたら、「部品の向きの確認」の 9 点と Bottom の部品を確かめ、画面を依頼者に見せてから承認する。
3. JLCPCB から質問や変更の提案が届いたら、内容を依頼者に伝えて指示を待つ。

## 止まって確認する場面

- 注文の確定と支払いの直前（依頼者が上限金額を決めて任せていて、合計がその範囲に収まる場合を除く）。
- JLCPCB のサポートが、面取りできない、この捨て基板では実装できない、と答えたとき。回答が無い、あいまい、質問 1)〜3) のどれかに答えが無いとき。追加料金の説明があったとき。
- 注文フォームで、この文書の表にある値を選べないとき。最初から選ばれている値が無い項目や、選ぶと追加料金が出る項目に当たったとき。読み込まれた大きさや層の数が違うとき。
- Remark が欄に入りきらないとき。
- 部品の照合画面で、**宣言済みの一覧に無い Extended の行**、**在庫が足りない行**、不一致、未選択があるとき（宣言済みの Extended 8 品番の行は止まる理由にならない）。
- RP2350B の在庫が 48 個より少ないとき。
- 部品の向きが「部品の向きの確認」と違って見えるとき。Bottom の部品がパッドからずれて見えるとき。
- 支払う日が 2026-11-14 より後になるとき。
- 製造データや部品の配置の確認依頼が届いたとき（承認の前）。自動で承認されない設定（Do not confirm automatically）を選べなかったとき。
- JLCPCB から質問、変更の提案、追加料金の連絡が届いたとき。
- 基板の代金が US$ 97、または実装の料金（部品代を除く）が US$ 183 を超えたとき。

## 終わったら報告すること

- 注文番号、選んだ Delivery Format、合計金額と内訳、配送方法、納期の見込み、サポートの回答の全文。
- 部品の照合画面の Basic と Extended の行数、RP2350B の在庫と、先に確保したかどうか。
- 止まって確認した点と、その結果。未解決のことがあればその内容。

## この基板について知っておくこと

- 基板の名前は famicart rev H。ファミリーコンピュータ用のカセット基板で、大きさは 89.6 × 85.7 mm（捨て基板込み 103.6 × 92.7 mm）、6 層、板厚 1.2 mm。部品は Top 136 点・Bottom 160 点。
- データは機械的な検査（配線の未接続 0、設計ルールの違反 0、JLCPCB の製造条件、部品の向き、部品の区分と在庫）に合格している。実物での動作確認はまだで、今回が最初の製造になる。そのため数量は最少にしてある。
- この文書とフォルダのデータは、配線 9078 本・ビア 926 個の版のもの（`jlcpcb_order_notes.md` の冒頭に同じ数字がある）。数字が違うデータを渡された場合は、止まって確認する。
- この発注に含まれないもの: カセットの外側のケース、USB ケーブル。
- 細かい理由や JLCPCB の条件の出典は `jlcpcb_order_notes.md` にある。

## 根拠にした資料

- JLCPCB の注文フォーム（項目名、見積もり。2026-11-14 確認）: https://cart.jlcpcb.com/quote
- JLCPCB 実装仕様（金フィンガーは Standard PCBA のみ）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- JLCPCB 金フィンガーと面取り: https://jlcpcb.com/help/article/jlcpcb-gold-fingers
- JLCPCB ビアの処理: https://jlcpcb.com/help/article/pcb-via-covering
- JLCPCB 捨て基板とフィデューシャル: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- JLCPCB 実装の料金表: https://jlcpcb.com/help/article/pcb-assembly-price
