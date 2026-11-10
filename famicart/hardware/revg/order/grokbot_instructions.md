# ファミコン基板（famicart rev G）発注指示書

この文書は、発注を代行する GrokBOT に向けた手順書です。JLCPCB への基板と部品実装の発注、秋月電子通商への手はんだ部品の発注の 2 件を扱います。書いてあるとおりに進め、「止まって確認」とある所では必ず依頼者（このフォルダの持ち主）の返事を待ってください。

## 依頼の内容

- JLCPCB に、基板 **5 枚**の製造と、そのうち **2 枚**への部品実装（Standard PCBA、表面のみ）を発注する。
- 秋月電子通商の通販で、手はんだ用のモジュールとコネクタを発注する。数量は、下の「数量」の 3 通りから依頼者が選ぶ。
- 2 件は別々の注文で、どちらを先に進めてもよい。秋月の注文は、JLCPCB のサポートの回答を待たずに進めてよい。

## 必ず守ること

1. **注文を確定する直前（支払いの直前）で止まる。** 注文内容と合計金額（送料・手数料・税を含む）を依頼者に見せ、承認をもらってから確定と支払いをする。秋月の代金引換と銀行振込は、支払いより前に注文が確定するので、注文を確定するボタンを押す前に止まる（秋月は確定後に内容を変更できず、取り消しは発送作業の前だけ）。依頼者があらかじめ上限金額を決めて任せていて、合計がその範囲に収まる場合だけ、この確認を省いてよい。
2. **ログイン情報、配送先、支払い方法は依頼者から受け取る。** このフォルダにも、この文書にも書かれていない。受け取った情報を、注文に必要な相手（JLCPCB、秋月）以外に渡さない。
3. **判断が要る所で推測しない。** この文書の表にある項目で、書かれている値を選べない場合は、止まって依頼者に聞く。表に無い項目は、基板・実装とも、最初から選ばれている値のままにする。ただし、最初から選ばれている値が無くて自分で選ばないと進めない項目と、選ぶと追加料金が出る項目は、止まって確認する（下の「止まって確認する場面」）。
4. **JLCPCB からの提案を自分で承諾しない。** 担当者やサポートが、この文書と違うやり方（捨て基板の位置を変える、V カットにする、面取りをやめる、部品を別の品番に替える、など）を提案してきたら、内容を依頼者に伝えて指示を待つ。
5. **部品を別の品番に替えない。** JLCPCB の画面が出す代替部品の候補も、秋月の似た商品も選ばない。

## このフォルダのファイル

| ファイル | 使い道 |
|---|---|
| `gerbers_rails.zip` | **A 案（これを使う）**。基板と左右の捨て基板を 1 枚にまとめた製造データ。大きさ 103.6 × 85.7 mm |
| `gerbers.zip` | B 案。基板だけの製造データ（89.6 × 85.7 mm）。JLCPCB が A 案を受け付けないと答え、依頼者が B 案への切り替えを認めた場合だけ使う |
| `bom_jlc.csv` | 実装する部品の表。A 案・B 案で共通 |
| `cpl_jlc.csv` | 部品の位置と向き。A 案・B 案で共通 |
| `rails.png` | JLCPCB のサポートへの質問に添付する図 |
| `jlcpcb_support_question.txt` | サポートへの質問文（英語）。そのまま送る |
| `jlcpcb_pcb_remark_plan_a.txt`、`jlcpcb_assembly_remark_plan_a.txt` | A 案の注文フォームに貼る Remark（PCB 用と実装用） |
| `jlcpcb_pcb_remark_plan_b.txt`、`jlcpcb_assembly_remark_plan_b.txt` | B 案に切り替えた場合の Remark |
| `jlcpcb_order_notes.md` | 設計者が書いた注文メモの全文。この文書の根拠と、細かい理由が書いてある。この文書と食い違う所は、この文書に従う。メモに出てくる `docs/…` や `tools/pcb/…` のファイルはこのフォルダに無いので、探さなくてよい |
| `akizuki_parts.csv` | 秋月で買う品目、販売コード、数量、金額 |
| `outline.png`、`placement.png` | 基板の外形図と部品の配置図（参考） |
| `parts_check.csv`、`cpl_check.csv` | JLCPCB の部品の区分・在庫と、部品の向きを照合した結果（参考。2026-11-10 時点） |

## 数量

| 注文先 | 品目 | 数量 | 補足 |
|---|---|---|---|
| JLCPCB | 基板（PCB Qty） | 5 枚 | 注文できる最少の枚数 |
| JLCPCB | 部品実装（PCBA Qty） | 2 枚 | 残りの 3 枚は部品なしの基板で届く |
| 秋月 | モジュールとコネクタ | 下の 3 通りから選ぶ | 依頼者が選ぶ |

基板 1 枚に載る手はんだ部品は、Raspberry Pi Pico 2 が 4 個（U1・U2 は必ず要る。U4・U5 は任意の増設）、Seeed XIAO RP2350 が 2 個（U3・U6。必ず要る）、microSD のコネクタが 1 個（J3。任意）です。任意の部品は、載せなくても基板が動きます。**秋月でカートに入れる前に、次の 3 通りと金額を依頼者に見せ、選ばれた数量で注文してください。** 上限金額を任されている場合でも、数量は選んでもらいます。

| 選び方 | 数量 | 商品合計（税込） | 送料 |
|---|---|---|---|
| (a) 2 台分の全部 | Raspberry Pi Pico 2 ×8、Seeed XIAO RP2350 ×4、microSD コネクタ ×2 | 12,620 円 | 送料無料 |
| (b) 2 台分の必ず要る部品だけ | Raspberry Pi Pico 2 ×4、Seeed XIAO RP2350 ×4 | 8,360 円 | 送料が加わる |
| (c) 1 台分の全部 | Raspberry Pi Pico 2 ×4、Seeed XIAO RP2350 ×2、microSD コネクタ ×1 | 6,310 円 | 送料が加わる |

## JLCPCB の手順

### 支払いの前にサポートへ質問する

この基板は端に金めっきの接点（金フィンガー）があり、その辺を斜めに削る加工（面取り、Beveling）を頼みます。実装に必要な捨て基板（Edge Rails）は、データの中に左右に描き込んであります。この組み合わせで面取りをしてもらえるか、注文の種類を何にすればよいかは、JLCPCB のどのページにも書かれていません。そのため、注文の前に確かめます。

1. JLCPCB のサポート（サイトのチャット、またはメール）に、`jlcpcb_support_question.txt` の英文を送り、`rails.png` を添付する。GrokBOT から送れない場合は、文面と図を依頼者に渡して送ってもらう。
2. 回答の全文を依頼者に報告する。
3. 回答に応じて、下の表のとおりに進める。

質問文（`jlcpcb_support_question.txt` と同じ内容）:

> I am going to order a 2-layer board, 1.2 mm, ENIG, gold fingers (30 on each side) with a 30 degree bevel, and Standard PCBA on the top side. Please see the attached drawing. My Gerber file already contains two 5.0 mm edge rails that I drew myself, on the left and right edges (perpendicular to the gold-finger edge). Each rail is joined to the board by 3 mouse-bite tabs (5.2 mm wide, 0.6 mm holes) across a 2.0 mm routed gap. There is no V-cut. The rails end 2.7 mm above the gold-finger edge, so that edge is completely free. The rails carry 3 fiducials (1 mm, centre 3.85 mm from the panel edges) and 4 tooling holes (2.0 mm). Panel size 103.6 x 85.7 mm, one board per panel.
> 1) Can you bevel the gold-finger edge of this board?
> 2) Is this rail arrangement accepted for Standard PCBA?
> 3) Which Delivery Format must I select: Single PCB or Panel by Customer (1 x 1)? Is there an extra charge?
> 4) If I upload the board without rails (89.6 x 85.7 mm) instead, can you add the rails on the same two edges (panel 99.6 x 85.7 mm) and still bevel the gold-finger edge?

| 質問 | 回答 | すること |
|---|---|---|
| 1) 面取りできるか | できる | 次へ進む |
| 1) 面取りできるか | できない | **止まって確認。** 依頼者が「面取りなしで作る」と決めた場合は、Gold Fingers の Beveling を No にし、PCB 用と実装用の両方の Remark から "Please bevel this edge 30 degrees." の 1 文を消して進める（ほかの文は変えない） |
| 2) この捨て基板で実装できるか | できる | 次へ進む |
| 2) この捨て基板で実装できるか | できない、または条件つき | **止まって確認。** 足りない点（寸法や数）を聞き取って依頼者に伝える。データの作り直しが要る |
| 3) Delivery Format | Panel by Customer | この文書のとおりに選ぶ |
| 3) Delivery Format | Single PCB | Delivery Format を Single PCB にする。追加料金の説明があれば依頼者に伝える |
| 4) 基板だけのデータでも左右に捨て基板を付けて面取りできるか | どちらでも | 回答を記録して依頼者に伝える。A 案が使える間は B 案に切り替えない |

2 営業日たっても回答が無い場合、回答があいまいな場合、質問 1)〜3) のどれかに答えが無い場合は、支払いへ進まずに、止まって依頼者に確認してください（答えの無い質問だけをもう一度送ってよい）。4) だけ答えが無い場合は進めてかまいません。3) の答えが Single PCB でも Panel by Customer でもない場合と、追加料金の説明があった場合は、内容を依頼者に伝えて指示を待ちます。

### 基板（PCB）の指定

1. [注文フォーム](https://cart.jlcpcb.com/quote) を開き、"Add gerber file" に `gerbers_rails.zip` を上げる。
2. 読み込まれた大きさ（Dimensions）が **103.6 × 85.7 mm** であることを確かめる。0.5 mm 以上違う場合は止まって確認。
3. 下の表のとおりに選ぶ。表に無い項目は、最初から選ばれている値のままにする。
4. PCB Remark の欄に、`jlcpcb_pcb_remark_plan_a.txt` の英文をそのまま貼る。欄に全文が入らない場合は、自分で削らずに止まって確認。

| 項目 | 選ぶ値 |
|---|---|
| Base Material | FR-4 |
| Layers | 2 |
| PCB Qty（Delivery Format を Panel by Customer にすると、項目名が Panel Qty に変わる） | 5 |
| Product Type | Industrial/Consumer electronics |
| Different Design | 1 |
| Delivery Format | **Panel by Customer**。Panel Format は Column 1、Row 1（サポートが Single PCB と答えた場合はそれに合わせる）。"Panel by JLCPCB" は選ばない |
| PCB Thickness | **1.2 mm**（最初に選ばれている値が違えば、1.2 mm に変える） |
| PCB Color | Green |
| Silkscreen | White |
| Surface Finish | **ENIG**。Gold Thickness は **2 U"** |
| Outer Copper Weight | 1 oz |
| Via Covering | Tented |
| Board Outline Tolerance | ±0.2 mm（Regular） |
| Mark on PCB | Remove Mark |
| Electrical Test | Flying Probe Fully Test |
| Gold Fingers | **Yes**。Beveling は **30°** |
| Castellated Holes | No |
| Confirm Production file | **Yes**。選ぶと出る画面では **"Do not confirm automatically"** を選ぶ |

PCB Remark に貼る文（`jlcpcb_pcb_remark_plan_a.txt` と同じ内容）:

> 1) This is ONE board with two 5.0 mm edge rails that I drew myself: panel 103.6 x 85.7 mm, one board per panel. The rails are on the left and right edges, each joined by 3 mouse-bite tabs (5.2 mm wide, 0.6 mm holes) across a 2.0 mm routed gap. 3 fiducials and 4 tooling holes (2.0 mm) are on the rails. Please do NOT add other rails and do NOT add V-cut.
> 2) Gold fingers are on ONE edge only: the edge with the 78.4 mm wide tab (30 fingers on each side). Please bevel this edge 30 degrees. This edge must stay a free routed edge; the rails end 2.7 mm above it.
> 3) If you cannot bevel a board with these rails, do NOT move or change the rails: put the order on hold and contact me.
> 4) You may shorten the finger copper to your standard setback for the bevel.
> 5) The solder mask window over the gold fingers is intentional: it starts 4.0 mm below the root of the tab and runs to the edge. Please do not enlarge it towards the board: tracks run beside the upper ends of the fingers.
> 6) The outline has two side notches, one inner slot (6.6 x 2.4 mm) and cut corners beside the tab. Inner corners are drawn with R 0.5 mm. Please keep them as drawn.

### 部品実装（PCB Assembly）の指定

1. PCB Assembly を有効にし、下の表のとおりに選ぶ。表に無い項目は、最初から選ばれている値のままにする。
2. BOM に `bom_jlc.csv`、CPL に `cpl_jlc.csv` を上げる。
3. 部品の照合画面で、**10 行・81 点がすべて一致し、すべて Basic で、未選択の部品が無い**ことを確かめる。1 行でも在庫切れ、Extended、不一致があれば止まって確認。代替部品の候補は選ばない。
4. 部品の配置のプレビューで、下の「部品の向きの確認」の 5 点を確かめる。
5. 実装用の Remark の欄に、`jlcpcb_assembly_remark_plan_a.txt` の英文をそのまま貼る。欄に全文が入らない場合は、自分で削らずに止まって確認。
6. カートに入れ、配送方法の候補とそれぞれの金額を控える。配送方法は依頼者が選ぶ。
7. 支払いの前にデータの審査を受けられる選択肢（Review Before Payment など）が出た場合は、そちらを選ぶ。
8. 支払う日が 2026-11-10 より後になる場合は、支払いの前に止まり、依頼者に「部品の向きの照合（`check_cpl.py`）を今日もう一度実行して、81 点とも合格したか」を確かめてもらう。JLCPCB が部品ライブラリの向きを書き換えることがあるため。この道具はこのフォルダに無く、GrokBOT は実行できない。
9. 合計金額と内訳を依頼者に見せ、承認をもらってから支払う（「必ず守ること」の 1）。

| 項目 | 選ぶ値 |
|---|---|
| PCBA Type | **Standard**（Economic は金フィンガー付きの基板を受け付けない） |
| Assembly Side | Top Side |
| PCBA Qty | 2 |
| Edge Rails/Fiducials | **Added by Customer** |
| Tooling holes（項目が出た場合） | Added by Customer |
| File provided as（項目が出た場合） | Complete File, just proceed with my own files |
| Confirm Parts Placement | **Yes**。期限までに確認しないと自動で承認されて製造に進むので、選ぶと出る画面では **"Do not confirm automatically"** を選ぶ（Confirm Production file と同じ。この選択肢が出ない場合は止まって確認） |
| Parts Selection（部品の選び方） | By Customer (Self-Service) |
| 捨て基板を外すサービス（Depaneling） | 選ばない |

実装しない部品（照合画面に出なくて正しいもの）: J1, U1, U2, U4, U5, U3, U6, J3, J2, J4。これらは依頼者が自分ではんだ付けする部品と、基板のパターンです。

### 部品の向きの確認

プレビューは、基板を上から見て、金色の接点が下に来る向きで確かめます。

1. U7: 1 番ピンの印が**右下**。1〜4 番ピンが右側に、下から上へ並ぶ。
2. B5819W: D10・D11・D12・D13・D14・D15 はカソードの帯が**左**。
3. 2N7002 と BAV99（SOT-23）: D1・D2・D3・D4・D5・D6・D7・D8・D9・Q1・Q2・Q3・Q4・Q5・Q6 は足 1 本の側が**右**。
4. 抵抗アレイ: 30 個すべて長い辺が縦。
5. SW1: 足が上と下。

**U7 か B5819W（D10〜D15）が 180° 回って見える場合は、承認せずに止まって確認してください。** そのほかの点が違って見える場合も同じです。

### 金額の目安

- 基板: 約 US$ 44（5 枚。2026-11-10 の見積もり画面の値。ENIG、金フィンガー、面取り、Confirm Production file を含み、送料は別）。
- 実装: 約 US$ 51（2 枚。JLCPCB の料金表〔2026-10-22 更新〕から計算した値で、見積もり画面では確かめていない。治具の費用が加わると約 US$ 68。料金表にはほかに、ステンシルと治具の保管料の項目がある）。部品代は見積もり画面に出る金額で、この文書では計算していない。
- 送料、関税、消費税は、見積もり画面と配送業者の案内による。この文書では確かめていない。
- 比べるのは項目ごと。基板の代金（送料を除く）が US$ 57 を超える場合、または実装の料金（部品代を除き、治具の費用を含む）が US$ 88 を超える場合は、止まって、どの項目が高いかを添えて依頼者に伝える。部品代、送料、税にはこの文書の目安が無いので、金額をそのまま依頼者に見せる。

### 注文したあと

1. 製造データ（Production file）の確認依頼が届いたら、承認する前に依頼者に見せる。確かめる点は、捨て基板が左右にあること、金色の接点の辺に捨て基板も V カットの線も無いこと、面取りの指示が入っていること、外形の切り欠きとスリットが `rails.png` のとおりであること。
2. 部品の配置の確認依頼（Confirm Parts Placement）が届いたら、「部品の向きの確認」の 5 点を確かめ、画面を依頼者に見せてから承認する。
3. JLCPCB から質問や変更の提案が届いたら、内容を依頼者に伝えて指示を待つ。

### B 案に切り替える場合

JLCPCB が「捨て基板を描き込んだデータは受け付けない」と答え、依頼者が切り替えを認めた場合だけ、次のように変えます。

- サポートが質問 4) に「できる」と答えていない場合は、B 案で注文しない（止まって確認）。
- 上げるデータは `gerbers.zip`。Dimensions は 89.6 × 85.7 mm。
- Delivery Format は Single PCB（Panel Format は使わない）。実装の Edge Rails/Fiducials は Added by JLCPCB、Tooling holes（項目が出た場合）も JLCPCB に任せる側を選ぶ。
- 注文フォームは大きさを 89.6 × 95.7 mm（上下に捨て基板を付けた大きさ）に書き換えるはずだが、設計者はフォームの文面から読んだだけで、画面では確かめていない。表示された大きさを控えて依頼者に伝える。どの値が出ても、Remark で左右に付けるよう頼む。
- Remark は `jlcpcb_pcb_remark_plan_b.txt` と `jlcpcb_assembly_remark_plan_b.txt` を貼る。
- 基板の金額の目安は約 US$ 40。
- 製造データの大きさが 99.6 × 85.7 mm（左右に付いた場合）でなければ承認しない。

## 秋月電子通商の手順

1. 「数量」の 3 通りを依頼者に見せ、どれにするかを選んでもらう。
2. [秋月電子通商の通販サイト](https://akizukidenshi.com/) で、下の表の品目を**販売コードで**探し、選ばれた数量をカートに入れる。
3. 品名と型番が表と同じであることを確かめる。名前の似た別の商品（Raspberry Pi Pico 2 W、Pico 2 H、初代の Pico、ピンヘッダー付きの品）は選ばない。
4. カートの商品合計が、選ばれた数量 × 表の単価の合計（(a) なら 12,620 円）と同じであることを確かめる。税込 11,000 円以上なら送料は掛からず、未満なら送料（佐川急便 550 円、ヤマト運輸 600 円）が加わる。
5. 在庫が足りない品目、価格が表と違う品目、購入数の制限に掛かる品目があれば、止まって確認する。
6. 支払い方法と配送先は依頼者の指定に従う。
7. 注文を確定するボタンを押す前に止まり、内容と合計（送料・手数料を含む）を依頼者に見せて承認をもらう。

下の表は (a) の数量です。

| 販売コード | 品名 | 型番 | 単価（税込） | 数量 | うち任意 | 小計 |
|---|---|---|---|---|---|---|
| 129604 | [Raspberry Pi Pico 2](https://akizukidenshi.com/catalog/g/g129604/) | SC1631 | 990 円 | 8 | 4 | 7,920 円 |
| 129619 | [Seeed XIAO RP2350](https://akizukidenshi.com/catalog/g/g129619/) | 102010550 | 1,100 円 | 4 | 0 | 4,400 円 |
| 102395 | [ヒロセ・マイクロSDカードコネクター DM3AT-SF-PEJM5](https://akizukidenshi.com/catalog/g/g102395/) | DM3AT-SF-PEJM5 | 150 円 | 2 | 2 | 300 円 |
|  | 合計 |  |  | 14 | 6 | 12,620 円 |

価格と在庫は 2026-11-10 に秋月のサイトで確かめた値です（3 品目とも在庫あり。通販で買える数は、それぞれ 1,462 個、308 個、1,500 個でした）。同社の案内では、送料は佐川急便が 1 個口 550 円、ヤマト運輸が 600 円で、商品合計が税込 11,000 円以上なら無料です。

支払い方法は 3 つです。クレジットカード（会員登録と、3D セキュア 2.0 対応のカードが要る）、代金引換（手数料 300 円。配達のときに現金で払う。離島は使えない）、銀行振込（全額前払い。振込手数料は客の負担。会員登録が要る）。会員登録をしない注文で使えるのは代金引換だけです。

## 止まって確認する場面

- 注文の確定と支払いの直前（JLCPCB、秋月とも。依頼者が上限金額を決めて任せていて、合計がその範囲に収まる場合を除く）。
- 秋月でカートに入れる前（数量の 3 通りから選んでもらう）。
- JLCPCB のサポートが、面取りできない、この捨て基板では実装できない、と答えたとき。回答が無い、あいまい、質問 1)〜3) のどれかに答えが無いとき。追加料金の説明があったとき。
- 注文フォームで、この文書の表にある値を選べないとき。最初から選ばれている値が無い項目や、選ぶと追加料金が出る項目に当たったとき。読み込まれた大きさが違うとき。
- Remark が欄に入りきらないとき。
- 部品の照合画面で、在庫切れ、Extended、不一致、未選択があるとき。
- 部品の向きが「部品の向きの確認」と違って見えるとき。
- 支払う日が 2026-11-10 より後になるとき（部品の向きの照合を、依頼者にもう一度実行してもらう）。
- 製造データや部品の配置の確認依頼が届いたとき（承認の前）。自動で承認されない設定（Do not confirm automatically）を選べなかったとき。
- JLCPCB から質問、変更の提案、追加料金の連絡が届いたとき。
- 秋月で在庫が足りない、価格が違う、購入数の制限があるとき。
- 基板の代金が US$ 57、または実装の料金（部品代を除く）が US$ 88 を超えたとき。

## 終わったら報告すること

- JLCPCB: 注文番号、選んだ Delivery Format、合計金額と内訳、配送方法、納期の見込み、サポートの回答の全文。
- 秋月: 注文番号、合計金額、発送の見込み。
- 止まって確認した点と、その結果。未解決のことがあればその内容。

## この基板について知っておくこと

- 基板の名前は famicart rev G。ファミリーコンピュータ用のカセット基板で、大きさは 89.6 × 85.7 mm、2 層、板厚 1.2 mm。
- データは機械的な検査（配線の未接続 0、設計ルールの違反 0、JLCPCB の製造条件、部品の向き 81 点）に合格している。設計者以外による見直しと、実物での動作確認はまだで、今回が最初の製造になる。そのため数量は最少にしてある。
- この文書とフォルダのデータは、配線 3311 本・ビア 432 個の版のもの（`jlcpcb_order_notes.md` の冒頭に同じ数字がある）。数字が違うデータを渡された場合は、止まって確認する。
- この発注に含まれないもの: カセットの外側のケース、USB ケーブル、はんだ付けの道具。
- 細かい理由や JLCPCB の条件の出典は `jlcpcb_order_notes.md` にある。

## 根拠にした資料

- JLCPCB の注文フォーム（項目名、見積もり。2026-11-10 確認）: https://cart.jlcpcb.com/quote
- JLCPCB 実装仕様（金フィンガーは Standard PCBA のみ）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- JLCPCB 金フィンガーと面取り: https://jlcpcb.com/help/article/jlcpcb-gold-fingers
- JLCPCB 捨て基板とフィデューシャル: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- JLCPCB 実装の料金表: https://jlcpcb.com/help/article/pcb-assembly-price
- 秋月電子通商 Raspberry Pi Pico 2（2026-11-10 確認）: https://akizukidenshi.com/catalog/g/g129604/
- 秋月電子通商 Seeed XIAO RP2350（2026-11-10 確認）: https://akizukidenshi.com/catalog/g/g129619/
- 秋月電子通商 ヒロセ・マイクロSDカードコネクター DM3AT-SF-PEJM5（2026-11-10 確認）: https://akizukidenshi.com/catalog/g/g102395/
- 秋月電子通商 注文方法（送料、支払い方法。2026-11-10 確認）: https://akizukidenshi.com/catalog/pages/buy.aspx
