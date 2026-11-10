# JLCPCB 注文パッケージ（famicart rev G: 任天堂の大型カセットシェル用、Basic 部品のみ）

Pico 2 ×2 + XIAO RP2350 ×2 が基本構成、Pico 2 ×2 は増設用（載せなくても動く）。16 MB の SPI フラッシュを載せ、microSD
ソケットは任意。回路と配置の説明は `docs/12_rev_g_plan.md`。

**状態**: 設計レビューの指摘を反映した版で、**実機では未検証**。rev G 用のファームウェアはまだ無い（ピン配置と一部の信号の
極性が rev F と違う。`docs/12_rev_g_plan.md` の作業一覧）。**シェルへの収まりも実物では未確認**なので、最初の注文は最少枚数にして、
モジュールをはんだ付けする前に基板だけをシェルに入れて確かめること。

## 1. 注文の種類
- 金フィンガー付きの基板は **Economic PCBA では受け付けられない**（JLCPCB の実装仕様表で Gold fingers は Economic "Not Support"、
  Standard "Support"）。**Standard PCBA** で注文する。
- Standard PCBA は捨て基板（Edge Rails）とフィデューシャルが必須。注文画面で **Added by JLCPCB** を選ぶと JLCPCB が付ける
  （基板には置いていない）。捨て基板は付いたまま届くので、受け取ってから外す。
- **捨て基板は左右だけに付けてもらう**（下の Remark で指定）。JLCPCB の金フィンガーの説明に「V カットで面付けした基板は、端子が
  面付けの内側に来るので面取りできない」とある。端子の辺（下）に捨て基板が付くと面取りができなくなるので、この基板は左右の端を
  それぞれ 1 本の直線にして、捨て基板を左右に付けられるようにしてある。面取りと捨て基板を同時に頼めるかどうかは JLCPCB のページに
  明記が無いので、**注文後の確認（エンジニアからの連絡）で「面取りはできない」と言われたら、面取り無しで作ってもらい**、
  受け取ってから端子の辺を手で面取りする（6 章）。捨て基板を上下に移す提案は断る。
- 実装は表面（Top）だけ。全部品が JLCPCB Basic Parts（10 種類・81 点/枚。在庫と区分は `parts_check.csv`）。

## 2. PCB の指定（Instant Quote → Add gerber file → `gerbers.zip`）
| 項目 | 指定 |
|---|---|
| Base Material / Layers | FR-4 / 2 |
| Dimensions | 89.6 × 85.7 mm（ガーバーから自動で入る。本体 75.0 mm + 端子タブ 10.7 mm）|
| PCB Qty | 5（最少）|
| PCB Thickness | **1.2 mm** |
| Surface Finish | **ENIG**、Gold Thickness は **2 U"**（約 0.05 µm。1 U" は約 0.025 µm。端子が擦れるので厚いほう）|
| Gold Fingers | **Yes**、Bevelling **30°**（ENIG を選んだときだけ端子が金になる。HASL を選ぶと端子ははんだ〔錫〕になる）|
| Outer Copper Weight | 1 oz |
| Via Covering | Tented |
| Min via hole size/diameter | 0.3 mm の標準のまま（設計値: 穴 0.3 mm・径 0.5 mm）|
| Board Outline Tolerance | ±0.2 mm（Regular）|
| Mark on PCB | Order Number (Specify Position)。裏面シルクの `JLCJLCJLCJLC` の位置に注文番号が入る |

PCB Remark（そのまま貼る）:

> Edge rails for assembly: LEFT and RIGHT sides only (both side edges are straight lines for this purpose).
> The bottom side is the gold-finger card edge: please keep it on the outer edge so that the 30 degree bevel can be made.
> If the bevel cannot be combined with the edge rails, make the boards WITHOUT bevel and keep the rails on the left and right.
> Please keep the two side notches, the inner slot and the rounded inner corners (R0.5 mm) as drawn.

**端子の金について**: JLCPCB の金フィンガーは ENIG（無電解ニッケル 3〜6 µm の上に置換金 0.05〜0.1 µm）で、抜き差しの多い
コネクタ用の硬質金めっき（電解めっき、0.5〜1.5 µm）ではない。JLCPCB は硬質金めっきを扱っていない（同社の記事に明記。表面処理は
HASL・ENIG・OSP）。同じ記事は、ENIG の金は数十回の抜き差しで減り、硬質金は 500〜1000 回以上もつ、としている（出典のない目安）。
このカセットは挿したまま使うのが前提で、ゲームの入れ替えは USB か microSD で行う。金が減っても下のニッケルで導通はするが、
接触が不安定になったら端子を無水アルコールで拭く。

## 3. PCB Assembly の指定
| 項目 | 指定 |
|---|---|
| PCBA Type | **Standard** |
| Assembly Side | Top Side |
| PCBA Qty | 2 または 5 |
| Edge Rails/Fiducials | **Added by JLCPCB** |
| Confirm Parts Placement | Yes（部品の向きを製造前に画面で確認できる）|
| BOM / CPL | `bom_jlc.csv` / `cpl_jlc.csv` |

- 実装しない部品（手はんだ・基板パターン）: J1, U1, U2, U4, U5, U3, U6, J3, J2, J4
- CPL の角度は JLCPCB の部品ライブラリの向きに合わせて補正済み: **抵抗アレイ = 270°、SOT-23（2N7002・BAV99）= 180°、U7（SOIC-8）= 270°**（KiCad 上は 0°）。
  JLCPCB は自社の部品ライブラリ（LCSC 番号ごとの EasyEDA のフットプリント）を CPL の角度で回して置く。全 10 種類について、その
  フットプリントを取り寄せて KiCad のフットプリントとパッド番号単位で突き合わせ、CPL の全行が合っていることを確かめてある
  （`tools/pcb/check_cpl.py`。結果は `cpl_check.csv`）。SOT-23 = 180°、SOIC = 270°、アレイ = 90°（270° と同じ結果）は、KiBot の補正表とも一致する。
- それでも**部品プレビューでは、U7 の 1 番ピン（丸印）が基板のシルクの印と同じ角にあること、2N7002・BAV99（D5・D6・D7・D8・D9）の 1 本足の側が
  パッド 1 個の側にあること、B5819W のカソード帯がシルクの帯と同じ側にあること**を見る（JLCPCB のライブラリは部品ごとに変わりうる）。

## 4. 費用（JLCPCB の料金表 2026-10-22 更新分から計算。部品代・送料・税は別）
| | 2 枚実装 | 5 枚実装 |
|---|---|---|
| 実装費（Standard・片面） | 約 US$ 51 | 約 US$ 53 |

- 内訳: セットアップ $25.56 + ステンシル $8.21 + フィーダー $1.53 × 10 種類 + はんだ付け $0.0016 × 361 接点 × 枚数
  （1 枚あたり最低 $0.48）+ 梱包 $0.50 + 配置確認 $0.45。**部品の種類が 1 つ増えるごとに $1.53** かかる。
- 治具（Fixture）費が見積もりに加わることがある（料金表では 1 個 $8.21、29 枚以下は 2 個。どの注文に掛かるかは料金表に書かれていない）。
- 捨て基板を JLCPCB に外してもらう場合は追加の加工費がかかる（金額は料金表に無い。注文時に依頼する）。
- PCB 代は見積もり画面の表示による（ENIG・金フィンガー・1.2 mm を選ぶので、標準の基板より高い）。
- モジュール（秋月）: 基本構成 ¥4,180（Pico 2 ×2 + XIAO RP2350 ×2）、増設の Pico 2 は 1 枚 ¥990、microSD ソケット ¥150。

## 5. JLCPCB の製造条件との照合
| 項目 | この基板 | JLCPCB の条件 |
|---|---|---|
| 基板サイズ | 89.6 × 85.7 mm | Standard PCBA は 70 × 70 mm 以上。金フィンガーは 50 × 50 mm 以上 |
| 材質・板厚 | FR-4、1.2 mm | FR-4 は 0.4〜2.0 mm（1.2 mm あり）|
| 表面処理・端子 | ENIG、金フィンガー、30° 面取り。端子の銅は基板端の 1.0 mm 以上手前で終わる | 端子の金は ENIG。面取りは 30° か 45°。面取りする範囲に銅を置かない |
| 端子部のレジスト | タブの付け根から 4.0 mm より先（配線を置かない範囲）は、表裏とも端子の間を含めて全面開口 | 金フィンガーの範囲はレジストを全面開口にする（残すと抜き差しで剥がれる）|
| 端子の近く | ビアは端子から 1.0 mm 以上離す。シルクは無い | めっき穴・SMD パッドは金フィンガーから 1.0 mm 以上。端子の近くにレジスト・シルクを置かない（同社の記事の指針）|
| 面取りと面付け | 捨て基板は左右。端子の辺は面付けの外周に出る | V カットの面付けで端子が内側に来ると面取りできない |
| 配線幅 / 間隔 | 0.15 / 0.15 mm | 0.10 / 0.10 mm 以上（2 層・1 oz）|
| ビア | 径 0.5 mm、穴 0.3 mm | 穴 0.3 mm 以上が標準（それより小さい穴は割高）。径は穴 + 0.1 mm 以上（推奨 + 0.15 mm）|
| 穴と穴 / 穴と配線 | 0.25 mm 以上 / 0.2 mm 以上 | 0.2 mm 以上 / 0.2 mm 以上 |
| 銅箔と基板端 | 0.3 mm 以上。捨て基板が付く左右の端は 0.4 mm 以上 | ルーター加工の端 0.2 mm 以上、V カットの端 0.4 mm 以上 |
| スリット・切り欠き | 幅 2.4 mm。内側の角は R0.5 mm で作図 | 非めっきスリットは幅 1.0 mm 以上。角に丸みの無い角穴・スリットは作れない |
| 外形の公差 | 切り欠きの奥行きとスリットの長さに 0.6 mm、左右の端に 0.2 mm の逃げ | ルーター加工 ±0.2 mm、V カット ±0.4 mm |
| シルク | 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上 | 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上 |
| レジスト | パッド間のレジストは 0.3 mm 以上 | 0.10 mm 以上（黒・白は 0.13 mm）|
| 実装 | 表面のみ、Basic Parts のみ | Standard PCBA は片面・両面とも可 |
| はんだペースト | 手はんだ部品のパッドには置いていない | ステンシルの開口は実装する部品のパッドだけに作られる |

ガーバーの ZIP には製造に使う層（銅箔・レジスト・シルク・ペースト・外形）とドリルだけを入れてある。

## 6. 受け取ってから
1. 捨て基板を外す（V カットは折る。ミシン目は切って、残った突起をやすりで落とす）。左右の端面をやすりで平らにする。
   面取り無しで届いた場合は、端子の辺の角を表裏とも 30〜45° の角度で 0.3〜0.5 mm ほど、目の細かいやすりで落とす
   （端子の銅は端から 1.0 mm 手前で終わっているので、金には触れない）。角が立ったままだと本体のコネクタの接点を傷める。
2. **基板だけ**をシェルに入れて、左右の切り欠き・スリット・端子タブの位置を確かめる。タブの付け根など、内側の角に残る丸みが
   シェルに当たる場合は、やすりで落とす。
   あわせて、**基板の表・裏それぞれからシェルの内壁までの隙間**を測る（ノギスの深さ測定か、粘土を挟んで閉じる）。この寸法は
   どの資料にも無かった。必要な高さの目安（基板の厚み＋コネクタの一般的な寸法からの見積もりで、実測ではない）:
   **表（ラベル面）** = XIAO（U3・U6）約 4.5 mm、増設の Pico 2（U4）約 3.8 mm、microSD ソケット約 2 mm、実装済みの部品は最大約 2.2 mm（U7）。
   **裏** = Pico 2（U1・U2・U5）約 3.8 mm。任天堂の純正基板は背の高い部品を裏（31〜60 番の面）に載せているので、表のほうが狭い
   可能性がある。表の隙間が XIAO に足りない場合、この版ではシェルの表側を閉じられない（表側のシェルの内側を削るか、開けたまま
   使い、次の版で XIAO を裏に移す）。動作には影響しない。
3. モジュールにファームを書き込んでから、はんだ付けする。裏面（U2 → U1、増設するなら U5）を先に、表面（U3・U6、増設するなら U4、
   使うなら J3）を後に。基板のシルクに `U1 cpu` のように役割が書いてある。シルクの `USB` の字がある側にモジュールの USB 端子を向ける。
4. Pico 2 は端面（キャステレーション）40 か所だけをはんだ付けする。XIAO は縁の 14 ピンだけ（裏面パッドは使わない）。
5. XIAO の 5V ピンは USB の VBUS と直結している。**本体の電源が入っている間は、電源の入っていない PC やハブに U3・U6 の USB を
   つながない**（本体の 5 V が USB ケーブル側へ出る）。

## 7. 手はんだ部品（秋月電子）
| 部品 | 秋月 通販コード | 価格 | 位置 |
|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 ×2（＋増設 ×2）| **裏**: U2（下、PPU 側）・U1（上、CPU 側）・U5（中、PPU 側の増設）／**表**: U4（上、CPU 側の増設）|
| Seeed XIAO RP2350 | 129619 | ¥1,100 ×2 | **表**: U3（中央右、IRQ・拡張音源・ネームテーブル制御）・U6（上、ハブ: SFC チップ機能・保存・更新）|
| microSD ソケット Hirose DM3AT-SF-PEJM5 | 102395 | ¥150（任意）| **表**: J3（右上）|

## 出典（JLCPCB 公式、2026-11-10 に確認）
- 実装仕様（Economic / Standard の違い、金フィンガー、基板サイズ）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- 基板の製造仕様（配線・ビア・外形・スリット・シルク・レジスト）: https://jlcpcb.com/capabilities/pcb-capabilities
- 追加料金になる場合（小径穴ほか）: https://jlcpcb.com/help/article/In-what-cases-will-there-be-charged-extra
- 金フィンガーと面取り（2026-09-18 更新。面取りの角度、V カット面付けでは面取り不可、端子部のレジスト全面開口）: https://jlcpcb.com/help/article/jlcpcb-gold-fingers 、 https://jlcpcb.com/blog/considerations-for-gold-finger-bevel-design
- 金フィンガーの設計の指針（めっき穴・パッドは端子から 1.0 mm 以上、端子の近くにレジスト・シルクを置かない）: https://jlcpcb.com/blog/pcb-gold-fingers
- 面付けと V カットの条件: https://jlcpcb.com/help/article/pcb-panelization
- 硬質金めっきと ENIG の違い、JLCPCB が硬質金を扱わないこと（2026-08-08 更新の記事）: https://jlcpcb.com/blog/hard-gold-pcb-finish
- 捨て基板とフィデューシャル: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- 実装の料金表（2026-10-22 更新）: https://jlcpcb.com/help/article/pcb-assembly-price
- 実装の FAQ（フィデューシャルは JLCPCB が追加、面付け）: https://jlcpcb.com/help/article/pcb-assembly-faqs
- ステンシルの開口: https://jlcpcb.com/help/article/smt-stencil-data-prepared-for-smt-orders
- 部品の向きの補正表（KiBot。JLCPCB 向けの回転の一覧）: https://kibot.readthedocs.io/en/latest/notes_position.html
