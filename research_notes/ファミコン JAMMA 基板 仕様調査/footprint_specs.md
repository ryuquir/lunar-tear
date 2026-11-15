# 自作フットプリント 5 種の寸法（段階 2-1・2026-11-15）

## 0. この資料について

基板の自作フットプリント 5 種の寸法と、その出典をまとめる。
寸法の正本は `hardware/famicom-jamma/design/footprints.py` で、`tools/build.py` が毎回 `kicad/fcjamma.pretty` を書き出す。

**調べ方**
- 4 つの組に分けて、組ごとに別の担当が、メーカー図面と規格の一次資料から寸法を取った。
- 別の担当が、1 件ずつ資料を取り直して検証した。
- 項目は 133 件。検証の結果は次のとおり。
  - そのまま確認: 127 件
  - 訂正つきで確認: 6 件
  - 否定: 0 件
- 下の値は、訂正を反映した値。
- 全文（引用、図からの実測、出典の版、検証の記録）は `footprint_specs_2026-11-15.json` にある。
  中の /tmp のパスは、担当者の作業場所で、もう残っていない。

**座標**
- 単位は mm。
- KiCad のフットプリントの座標で、X は右、Y は下。部品面（表）から見る。
- 表記: 出典は各章の末尾と 7 章。「推論」と書いた値は、資料から決めた設計上の選択。

**ビルドが毎回確かめること**
- 出典の値（19 項目）が、描いた図形で成り立つこと。
- KiCad 自身が読み直しても、すべてのパッド、穴、層、禁止域、属性が意図どおりであること（`tools/check_footprints.py`）。
- 記号のすべてのピンにパッドがあること。
- 各フットプリントが、描いた対象の部品（JLCPCB の品番）にだけ使われていること。

**JLCPCB の規則で確かめた結果**
- 最小間隔 0.127、シルクとパッドの間 0.15、マスクの幅 0.1、穴の間 0.25、銅と外形の間 0.3。
- この規則で 5 種を 1 枚の試験基板に置いて DRC を通し、違反は 0 件だった。

## 1. J1 JAMMA の金フィンガー（JAMMA_Edge_56）

| 項目 | 値 | 出典 |
|---|---|---|
| 原点 | 基板の先端の線と、1/A 番の中心線の交点。+X は 28/f 番の向き、基板は −Y 側 | JST GEC「PC board layout (viewed from component side)」 |
| パッド | 種類 connect（金フィンガー用。銅とマスクだけで、ペーストなし）。表 1〜28（7 なし）、裏 A〜f（H なし）で、各 27 本 | JAMMA56 の記号、Hirose・Sullins（G, I, O, Q は使わない） |
| ピッチ | 3.96。1〜28 番の間は 106.92 | JST 106.92 ± 0.05、Hirose 106.98 ± 0.08 の両方に入る |
| フィンガー | 幅 2.30、先端から 1.2〜10.0（長さ 8.8、中心 Y −5.6） | 幅: Hirose 2.3 ± 0.1、JST 2.3 ± 0.035。1.2: JLCPCB の 30° 面取りでの後退が約 1.13 |
| 表裏の対応 | 同じ X に置く（A は 1 の真裏、f は 28 の真裏） | 公開されている 3 設計、国内の配線表 |
| マスク | 表裏とも (−4.24, 0.5)〜(111.16, −10.5) を全面開口 | JLCPCB「The gold finger area must have the solder mask fully opened」 |
| 禁止域 | 次の 3 帯（表裏の銅） | JLCPCB「this area can not have copper」（推論で範囲を決めた） |
| 外形線（基板側で描く） | タング 114.4（X −3.74〜110.66）、角 C0.5。キー溝は中心 X 23.76、幅 3.0、深さ 11.5、入口 C0.5、奥 R0.5。肩は Y −12.0 | 02_jamma_interface.md 1.2.3（JST 114.4〜114.6 と外形公差 ±0.2）。キー溝は Sullins のキー 2.36 と Hirose CR1-GPIN 2.0 を両方通す |
| 属性 | 部品表と位置ファイルから外す（`exclude_from_bom`、`exclude_from_pos_files`）。マスクの橋は許す（`allow_soldermask_bridges`） | この属性がないと DRC でマスクの橋のエラーが 199 件出る（KiCad 10.0.8 で試した） |
| シルク | 表に「1」「28」「JAMMA PARTS SIDE 1-28」、裏に（鏡像で）「A」「f」「SOLDER SIDE A-f」。Y −13.4、高さ 1.2 | 慣行 |

禁止域の 3 帯:
- Y 0.5〜−1.2: 銅は一切だめ。
- Y −1.2〜−9.0: フィンガー以外はだめ。
- Y −9.0〜−11.0: ビアとベタはだめ。

検証での訂正（配線の決まり。段階 3 で守る）:
- 配線は、フィンガーの根元からだけ入れる。終点は −10.0 ≦ y ≦ −9.0 − 線幅/2。
- まっすぐ入る線は、幅 2.0 まで。
- 表裏をビアでつなぐのは、同じネットの組だけ。
  - 1/A と 2/B（GND）
  - 3/C と 4/D（+5V_IN）
  - 27/e と 28/f（GND）
- 14 番（GND）の裏は R（SERVICE）なので、つないではいけない。
- マスクの開口の中（Y > −10.5）を横に走る線は禁止。
- 無接続の 5・6・11・E・F・M 番は配線しない。

研究ノートの訂正:
- Hirose の接点の位置は、差し込んだ基板の先端から 5.3 ± 0.4 mm で、3.2 mm ではない。
- 3.2 mm は、ハウジングの面から測った値だった。
- フットプリントは変わらない。

## 2. J8 カセット端子（Famicom_Cart_60、WingTAT ED60BGFBK、C5173310）

| 項目 | 値 | 出典 |
|---|---|---|
| 部品 | 2 × 30、ピッチ 2.54 ± 0.05、列の間隔 5.08 ± 0.05（千鳥ではない）。足 0.65 × 0.40、長さ 3.80。本体 82.49 × 9.25、高さ 15.60。差し込み口 79.04 × 2.00、深さ 9.00。両端の脚で立つ（外側の間 80.74）。位置決めの突起や NPTH はない。推奨の板厚 1.57 ± 0.15 | メーカー図面「EDxxxBGFBK」Rev A |
| 番号 | **ラベル面が 1〜30 番。ラベル面を見て左端が 1 番。31 番は 1 番の真裏、60 番は 30 番の真裏** | NESdev「Pins 01-30 are on the label side of the cartridge, left to right」。OpenFC HVC-CPU-07 の基板データ（1〜30 が本体の前側の列）。純正カセット HVC-TGROM-01 の実測図（電源の端子が 1・16・30 と 31 番） |
| 部品の向き | 部品は左右対称で、1 番がない。番号を決めるのはフットプリントだけ | メーカー図面に番号がない |
| 原点 | 穴の並びの中心（本体と差し込み口の中心） | — |
| パッド | 1〜30 番は Y = +2.54、X = −36.83 + 2.54 (n − 1)。31〜60 番は Y = −2.54 | — |
| 穴 | 穴 1.00、ランド 1.70（1 番は角）、環幅 0.35、パッドの間 0.84 | メーカーの推奨は Ø1.00 ± 0.15。JLCPCB の仕上がりは 0.92〜1.13 で、その範囲に収まる |
| シルク | 外形、1 番の三角、1・30・31・60 の数字、ラベル面の側に「CART LABEL」 | — |
| 部品の禁止範囲 | ±41.75 × ±6.85（本体 + 0.5、シルクの文字も含む） | — |
| 置き方の案 | 外形の案の (110.0, 149.5) に回転 0 で置く。ラベル面は JAMMA の端の側を向き、CPU 側の信号は −X（U1 の側）、PPU 側は +X（U6 の側）に来る | mech/floorplan.py |

検証での訂正:
- 本体の下のすき間は約 1.2 mm（1.1 ではない）。
- 両端の脚は、それぞれ X 方向に約 1.5 mm（±38.85〜±40.37）。
- パッドは変わらない。

実物での確認:
- 実寸の確認用紙を `out/footprints/J8_cartridge_slot_1to1_check.pdf` に出す。
  - サンプルの足 60 本が印の上に乗るか。
  - カセットのラベル面の 1 番と 16 番が導通するか（どちらも GND）。
- 番号の判定は資料 3 つで一致しているが、実物での導通の確認はまだ。

## 3. RV1 半固定抵抗（Trimmer_Bourns_3362P、BOCHEN 3362P-1-103、C118956）

| 項目 | 値 | 出典 |
|---|---|---|
| 足の並び | 1 番 (−2.54, +1.27)、2 番＝ワイパー (0, −1.27)、3 番 (+2.54, +1.27)。原点は 3 つのパッドの外接箱の中心で、LCSC の部品データと同じ | BOCHEN の承認書 p.3、Bourns 3362（REV. 03/25）、LCSC/EasyEDA の RES-ADJ-TH_3362P |
| 向き | 部品の印字の辺（「1 3362 3」）が +Y、1 番が左 | 3 つの資料で一致 |
| 足 | 丸足。BOCHEN は ø0.5、Bourns は 0.46 ± 0.03。穴の推奨値はない | 同上 |
| 穴 | 穴 0.9（推論）、ランド 1.6、1 番は角丸。環幅 0.35 | JLCPCB の上限と下限の範囲内 |
| 本体 | BOCHEN 6.9 × 7.1 × 高さ 4.8、Bourns 6.60 × 6.99 × 4.88 | — |
| 回す向き | 時計回りでワイパーが 3 番に近づく（＝音が大きくなる）。これを書いているのは Bourns だけ。**BOCHEN の資料には向きの記載がない** | Bourns の端子図「CCW ① … ③ CW」 |
| シルク | 外形、1 番の三角、時計回りの矢印と「+」（大きく）・「−」 | — |
| 部品の禁止範囲 | (−4.70, −4.30)〜(4.70, 5.15)（シルクの印も含む） | 検証で、印が範囲の外に出ていると指摘されたので広げた |

検証での訂正:
- 1 番（角丸）と 2 番のパッドの間は 1.83 mm（1.99 ではない）。
- 部品に印刷された点の位置は (−2.4〜−2.8, +2.8〜+3.0)。

未確認:
- BOCHEN 品の回す向きは、サンプルを 5 個（約 0.87 ドル）買ってテスターで確かめるのが安い。
- サンプルを買わない場合は、届いた基板の AMP_IN と GND の間で、時計回りに抵抗が増えるかを確かめる。
- 逆だったら、回路の 1 番と 3 番を入れ替え、シルクの「+」を直す。

## 4. SW3 DIP スイッチ（SW_DIP_x04_HRO_DS-04RP_W7.62mm_P2.54mm_Drill1.0mm、C92645）

| 項目 | 値 | 出典 |
|---|---|---|
| 元 | KiCad の SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm の写し | — |
| 穴 | 0.8 を 1.0 に、ランドを 1.6 から 1.7 に変えた（1 番は角丸、rratio 0.147059）。環幅 0.35 | HRO の図面: 穴 Ø0.97 ± 0.05、足 0.60 × 0.20 |
| 寸法 | ピッチ 2.54、列の間 7.62 ± 0.1、本体 9.60 × 11.72 | HRO の図面 |
| 番号 | パッド n とパッド 9 − n が向かい合い、スイッチ n がその 2 つをつなぐ | KiCad の番号付けと、メーカーのスイッチ番号が一致する |
| 部品の向き | 部品の「ON」の辺を 5〜8 番（GND）の側に、部品の「1」を 1/8 番の側に置く | 回路は 1〜4 番が I_DIP1〜4（プルアップ）、5〜8 番が GND。ON（閉）で 0 になる |
| シルク | 「ON →」を +X 側に、「1〜4」を 1〜4 番の横に足した。KiCad の 0.12 mm の線は、JLCPCB の最小 0.15 mm に太くした | JLCPCB「Minimum Line Width ≥0.15mm」 |
| 部品の禁止範囲 | X −3.05〜11.62、Y −2.67〜10.29（足したシルクも含む） | — |

検証での訂正:
- 1.7 mm のランドにした理由は、KiCad の慣例と、ウェーブはんだのフィレットのため。
- 1.6 mm でも環幅は 0.30 で、JLCPCB の推奨 0.25 は満たす。

未確認:
- JLCPCB 自身の C92645 の部品データで、どの端子が 1 番か。
- 配置確認の画面（有料 0.45 ドル）で、部品の「1」が 1/8 番に、「ON」が 5〜8 番の側にあることを見る。

## 5. U25〜U27 Pico 2（RaspberryPi_Pico2_SMD_TP7KeepOut、C41407547）

| 項目 | 値 | 出典 |
|---|---|---|
| 元 | KiCad の Module:RaspberryPi_Pico_SMD の写し。96 個のパッドは変えていない | — |
| パッドの照合 | 1〜40 番、D1〜D3、TP1〜TP6、USB の外殻 4 か所が、Pico 2 データシートの図 5 と一致 | Pico 2 データシート（Release 5）の図 3・5・6 |
| TP2・TP3 | TP2（USB_DM）は (+1.0, −24.3)、TP3（USB_DP）は (−1.0, −24.3) | Raspberry Pi の STEP モデルのシルク |
| TP7 | 1.1 V。Pico 2 で増えたパッドで、はんだ付けしてはいけない。位置は (+1.0, −5.0) | Pico 2 の図 5（Pico 1 の図 5 には無い） |
| 禁止域 | KiCad の元の 1.9 mm の禁止域（F.Cu と F.Paste）を消した。代わりに直径 2.5 mm の円（32 角形）を F.Cu と F.Mask に置き、名前を「TP7 keep-out」とした。配線、ビア、パッド、ベタはすべて禁止 | KiCad 10.0.8 で試した。ビア、表の線、マスクの開口は止まり、裏の線は通る。ベタは半径 1.25 で止まる |
| その他 | 元にあったグループ 6 個を消した（中身の番号が古いまま残るため）。シルクの線を 0.15 mm に太くした | — |

段階 3 で守ること（フットプリントでは表せない。基板の設定と発注で決める）:
- 基板の設定でビアを覆う（`(setup (tenting (front yes) (back yes)))`）。
- ビアごとに覆いを外す設定はしない。
- 発注では「Via Covering: Tented」を選ぶ。
- 基板の規則（.kicad_dru）を 2 つ置く。どちらも KiCad 10.0.8 で試してある。
  - 「TP7 の下はマスクを開けない」
  - 「Pico の下のビアは覆う」
- U27（Pico C）の Micro-USB 端子の前に、プラグを挿せる空きを残す（配置の禁止域）。

## 6. 段階 2-2 以降と発注に回す事項

1. カセットの殻の範囲を、DRC で守れる禁止域にする（高さ約 1 mm まで）。カセットを押さえる金具のための NPTH の位置を決める。殻の寸法は、実物を測ってから決める。
2. JLCPCB の部品データには J8 の CAD モデルがない。発注の備考に次を書く。
   - J8 は左右対称で 1 番がない。
   - 位置ファイルの回転 0 は、差し込み口が X 方向。
   - 原点は本体の中心。
   - どちら向きでもよい。
3. DIP スイッチの原点は 1 番のパッド（本体の中心は (3.81, 3.81)）。位置ファイルを書くときは、JLCPCB の部品データの中心に合わせて補正する。Pico 2 は、JLCPCB の部品データが KiCad と 90° 違う（README 8 章）。
4. JLCPCB への事前質問に足すとよいこと（発注の前に）。
   - 金フィンガーの銅の後退を 1.2 mm で足りるとするか、1.5 mm にするか。
   - 220 mm の本体から 12 mm 突き出したタングを、面取りの機械で削れるか。
   - 端材のレールは、左右の 2 辺だけに付くか。
   - 挿入部品の足を切るか（半固定抵抗の足は 4.4 mm 以上出る）。
   - 裏の金フィンガーをはんだから守る方法（耐熱テープか選択はんだか）。
5. タングの幅 114.4 に通常の外形公差 ±0.2 がつくと、114.2 になることがある。これは JST の下限 114.4 より細い。JLCPCB の高精度ルーター（±0.1）で公称 114.5 にする手もある。費用と条件を確かめてから決める。

## 7. 出典

1. JST「GEC CONNECTOR, 3.96mm pitch card edge connectors」(GEC-561) — https://datasheet.octopart.com/GEC-561-JST-datasheet-180492417.pdf
2. Hirose CR7E-30DB-3.96E(72) 図面 ADC-016737-72-02 — https://static.chipdip.ru/lib/690/DOC043690981.pdf
3. Hirose CR7 シリーズのカタログ「PCB Dimensions 3.96 pitch」 — https://s1.dtsheet.com/store/data/002648525.pdf
4. Sullins「Female Card Edge .156" [3.96mm]」 — https://s3.amazonaws.com/catalogspreads-pdf/PAGE74-75%20.156%20LP%20DS%20EYE%20RA.pdf
5. JLCPCB「JLCPCB Gold Fingers」（2026-11-10 更新） — https://jlcpcb.com/help/article/jlcpcb-gold-fingers
6. JLCPCB「Instructions for Chamfering Gold Fingers」 — https://jlcpcb.com/help/article/instructions-for-chamfering-gold-fingers
7. JLCPCB「PCB Capabilities」 — https://jlcpcb.com/capabilities/pcb-capabilities
8. JLCPCB「Via Covering in PCBs」（2026-11-10 更新） — https://jlcpcb.com/help/article/pcb-via-covering
9. WingTAT ED60BGFBK 図面 Rev A（LCSC C5173310） — https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2209231001_WingTAT-ED60BGFBK_C5173310.pdf
10. NESdev Wiki「Cartridge connector」（2026-08-31 更新） — https://www.nesdev.org/wiki/Cartridge_connector
11. NESdev Wiki「Famicom cartridge dimensions」（HVC-TGROM-01 の図） — https://www.nesdev.org/wiki/Famicom_cartridge_dimensions
12. OpenFC HVC-CPU-07 Rev A の KiCad データ — https://github.com/starlightk7/OpenFC
13. BOCHEN 3362P の承認書（LCSC C118956） — https://datasheet.lcsc.com/datasheet/pdf/e8c18fdb134841959db7142c14f620c3.pdf
14. Bourns 3362（REV. 03/25） — https://www.bourns.com/docs/Product-Datasheets/3362.pdf
15. LCSC/EasyEDA のフットプリント RES-ADJ-TH_3362P（C118956） — https://easyeda.com/api/products/C118956/components
16. HRO「MULTIFUNCTIONAL SWITCHES」DS-□□□□ REV. A（LCSC C92645） — https://datasheet.lcsc.com/datasheet/pdf/58c923485d5c652775c00f938a3bb4f1.pdf
17. Raspberry Pi Pico 2 Datasheet（Release 5） — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
18. Raspberry Pi Pico 2 の STEP モデル RP-009061-CA — https://pip.raspberrypi.com/documents/RP-009061-CA
19. Raspberry Pi Pico Datasheet（Pico 1 の図 5。TP7 が無いことの確認） — https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
20. KiCad 10.0.8 の標準ライブラリ（Module:RaspberryPi_Pico_SMD、Button_Switch_THT、Connector_PCBEdge）
21. このリポジトリ: `reference/02_jamma_interface.md` 1.2・1.3、`jamma_edge_geometry.md`、`reference/01_famicom_hardware.md`、`famicom_pinout_reverification.md`、`hardware/famicom-jamma/mech/floorplan.py`
