# ファミコン JAMMA 基板: 調達・コスト 第2パス (ギャップ解消と検証)

調査日: 2026-11-10 (全データこの日に取得)。為替は JLCPCB 自身の換算レート 1 USD = 157.7523 JPY ([queryRateList API](https://cart.jlcpcb.com/api/overseas-basic-data/v1/queryRateList?country=JP), 2026-11-10 取得) を使用。以下 ¥ 換算は ¥158/USD で丸め。
第1パスのノート: `parts_and_manufacturing.md`。本ノートはそれを前提に、未確認事項を一次ソースで埋める。
表記: 推論 = 自分の推論。未確認 = 一次ソースで確認できなかった事項。

---

## 1. JLCPCB PCBA の規則 (Economic / Standard, 金フィンガー, THT, 料金)

### Takeaway
JLCPCB 公式の能力表では Economic PCBA は「Gold Fingers/Castellated Holes/Edge Plating: Not Support」。実際に 150x200mm のダミー Gerber (下辺に 3.96mm ピッチのエッジ端子パッド 28 個) を Instant Quote にアップロードして確認したところ、「Gold Fingers: Yes」を選ぶと PCBA Type の Economic ボタンが灰色 (選択不可) になり Standard が自動選択され、「Gold Fingers: No」(ENIG のまま、面取りなし) だと Economic が選択可能だった。ただし、この「金指オプション No」の注文が審査段階で再分類・追加料金になるかは公式文書に記載がなく未確認。

### Cited Findings
- 能力表 (Economic / Standard): Assembly Types「Single sided placement (SMT/Thru-hole)」/「Single & double sided placement (SMT/Thru-hole)」; Layer 2,4,6 / 1-32; Thickness 0.8-1.6mm / No limit; 単板 10x10-470x500mm / 70x70-460x500mm; パネル 10x10-250x250 / 70x70-250x250mm; Order Volume「2 - 50 pcs」/「2 - 80000 pcs」; 「Gold Fingers/Castellated Holes/Edge Plating: Not Support / Support」; Edge Rails・Fiducials「Not necessary / Necessary」; Minimum Package 0402 / 01005; Build time 1-3 days / ≥4 days — [JLCPCB PCBA Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) (2026-11-10 Playwright で本文取得)
- 同ページ「PCB Specs for Economic PCB Assembly」表: 2層 1.6mm Green は HASL / ENIG 可、数量 2-50; 4層 1.6mm Green は HASL / ENIG 可、数量 2-50; 1.6mm Blue/Purple/Red/White は HASL のみ・5-30 枚 — 同上
- THT FAQ:「JLCPCB supports Through-Hole Technology (THT) component assembly and mixed-technology (SMD + THT)… THT components are assembled using wave soldering. This service is available under both the Economic and Standard PCBA.」「Unused through-holes are protected from solder ingress」 — 同上
- スタック部品 FAQ:「Installing an IC part A on a DIP socket part B is acceptable.」両方を BOM/CPL に入れ、A の座標を B から 0.2mm 以上ずらして登録し、備考に「need to put the B part on the A part」と書く。「This process is normally handled manually, so there will be some additional manual operation costs.」 — 同上
- 料金表 (公式ソリューションページ, 2026-11-10 取得): Setup fee Economic $8.18 / Standard $25.56 (片面)・$51.12 (両面); SMT assembly Economic $0.0016/joint (1-100,000) / Standard $0.0016 (1-50,000), $0.0013 (50,001-100,000), $0.0012 (100,001-); Stencil $1.53 / $8.21 (片面)・$16.42 (両面); 「Feeders Loading fee: $3.07 Extend / $1.53 Basic/Extend」; Hand-soldering labor $3.50 per order (両方); Components「Per system」 — [PCB Prototype Assembly](https://jlcpcb.com/solutions/pcb-prototype-assembly) (ページ内 JSON の表データ)
- 同ページ:「Basic parts are preloaded on pick-and-place machines with no feeder loading fee. Preferred extended parts are also fee-free on Economic PCBA.」 — 同上
- 公式ブログ (2026-10 の見積に基づく): 「With Economic PCBA, Basic parts load free, and so do Preferred Extended parts… Every other unique Extended part carries a $3.07 loading fee. Standard PCBA charges a loading fee on every unique part, Basic or Extended.」「The charge applies per part number, per order, regardless of quantity.」 — [JLCPCB blog: reduce PCB assembly cost](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- 同ブログ: Standard と Economic の両方に該当する注文では「the Standard total has to be at least $14.93 higher; if it isn't, the shortfall is added as a handling fee」 — 同上
- 同ブログ: THT は「as long as the part is listed for through-hole assembly in the parts library, charged at about $0.0164 per joint plus a $3.58 hand-soldering labor fee per order」 — 同上
- 同ブログ: Standard PCBA は「a minimum assembly charge of $0.48 per board on bulk orders」; Standard のステンシル保管 $4.93/3か月; Confirm Parts Placement $0.45 — 同上
- 同ブログ: 「JLCPCB fabricates at least 5 bare boards per order but can assemble as few as 2 of them」 — 同上
- 旧 FAQ ページ (Last updated Sep 09, 2026) は依然「Setup fee: $8.00 / Stencil: $1.50 / SMT Assembly: $0.0017 per joint / Hand-soldering labor fee: $3.5 / Manual Assembly: $0.0173 per joint」「698 kinds of basic components」「we charge $3 per extended component」と記載 — [PCB Assembly FAQs](https://jlcpcb.com/help/article/pcb-assembly-faqs)。料金表・ブログより古い数値で、内部不整合がある (ソリューションページの表を正とするのが妥当: 推論)
- 同 FAQ: 「The part's assembly type marked with "wave soldering" in our assembly parts library will be assembled manually. Cost: $3.5 hand-soldering labor fee + $0.0173 manual assembly fee per joint. Build time: SMT assembly service time + 1 more day」 — 同上
- 金フィンガーのヘルプ (Last updated Nov 10, 2026): 「only when ENIG is chosen, the fingers for your PCB will be with gold, if you choose HASL… covered with tin」「Chamfers are not available on boards smaller than 5x5cm」「If there is fingers in your file and it is panel with v-cut, then the fingers can not be made with chamfer」「The available bevel angles are 30° and 45°… we recommend prioritizing a 30° bevel」、金指部は「solder mask fully opened… JLCPCB will automatically apply a solder mask opening by default」「The length and width of a single board or panel with gold fingers shall not be less than 50mm」 — [JLCPCB Gold Fingers](https://jlcpcb.com/help/article/jlcpcb-gold-fingers)
- Instant Quote 画面の Gold Fingers ツールチップ: 「Only when ENIG surface finish is chosen, the fingers will be gold-plated. If you choose HASL surface finish, we will use HASL as edge connect plating.」 — [cart.jlcpcb.com/quote](https://cart.jlcpcb.com/quote) (2026-11-10 HTML 取得)
- 30° 面取り選択時、画面に「a (bevel angle): 30° / t (board thickness): 1.6mm / d (depth): 1.13mm / tr (residual thickness): 0.53mm」と表示 — 同上 (スクリーンショット確認)
- 実験 (2026-11-10, Playwright): 150x200mm の 2 層ダミー Gerber (下辺に 2.54x7mm パッド 28 個 @3.96mm、上面 SMD パッド 20 個、2.54mm THT 穴 40 個) をアップロード → 1.6mm/ENIG/Gold Fingers Yes/30° で PCB Assembly を ON にすると「PCBA Type: Economic (灰色・選択不可) / Standard (選択)」、「Edge Rails/Fiducials: Added by JLCPCB」「The board size is modified to be 160mm*200mm due to adding two 5mm edge rails on the shorter sides」「PCBA Qty 5, Qty from 2 to 5」、Charge Details 見出し「Standard PCBA Price」、PCB 価格は $39.70 (レール追加で Board $15.40 / Surface Finish $20.30) — [cart.jlcpcb.com/quote](https://cart.jlcpcb.com/quote) 実操作
- 同じ Gerber で Gold Fingers No (ENIG, 面取りなし) → PCBA Type は Economic が選択状態、「Tooling holes: Added by JLCPCB」、「Economic PCBA Price」表示、PCB 価格 $38.60 — 同上
- 2021 年頃の EasyEDA フォーラムで JLCPCB サポートが「the Gold fingers boards are not supported by our assembly lines for the moment and that's why the assembly feature disappear when you select the Gold fingers option」と回答 (古い。現在は Standard で可) — [EasyEDA forum](https://easyeda.com/forum/topic/JLC-SMT-and-Gold-Fingers-d1c2d2d6193b4d2cbed3d25e7f2601c2)
- 追加料金ページ: 「if you did not select the correct options during placing orders, there may be extra costs required during the file review process」; ENIG 面積が両面合計 30% 超で 1U" 金は超過 1% ごとに $0.8992/m²; 「When the area of one board exceeds 650 square centimeters, an additional charge」 — [In what cases will there be charged extra](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra) (Last updated Nov 10, 2026)

### Inferences
- 推論: 「金フィンガーなしの ENIG 基板 + エッジパッド」は、見積システム上は Economic PCBA が通る。ただし (a) 面取りなしだとカード挿入性が落ち JAMMA コネクタを傷める可能性、(b) 審査で「金指があるのにオプション未選択」と判断されると、追加料金ページの「did not select the correct options」条項によりオプション変更 (= Standard への移行) を求められる可能性、が残る。確実にしたいなら注文前に JLCPCB チャットで確認すべき (未確認)。
- 推論: 金指オプション自体の追加費は Instant Quote 上 $0 (§2)。したがって「金指のコスト」は実質「Standard PCBA の固定費差」(Setup +$17.38、ステンシル +$6.68、Basic にも装填料 $1.53/種、Edge rail 追加分) である。
- 推論: Standard の装填料 $1.53 は Preferred Extended にも課金される (ブログ「every unique part, Basic or Extended」)。Preferred の無料は Economic のみ。
- 推論: DIP-40 ソケット、2.54mm ピンソケット、カードエッジコネクタは「parts library で through-hole assembly 指定の品」であれば JLCPCB が wave/手はんだで実装可能。個別品の可否はパーツライブラリの各品の assembly type 次第 (§1 Gaps)。

### Gaps
- 「エッジパッドあり・Gold Fingers オプション No」の注文が JLCPCB の Gerber 審査で Standard へ再分類されるかどうか: 公式記述なし、未確認 (問い合わせ要)。
- DIP-40 ソケット / 2x20 ピンソケット / 60P カードエッジの個別 LCSC 品が「THT assembly 可」と表示されるか: 本パスでは JLCPCB パーツページの個別確認は未実施 → §3 以降で扱えた範囲のみ記載。

---

## 2. JLCPCB 実見積 (Instant Quote, 2026-11-10, Playwright で画面操作し API 応答も記録)

条件: FR-4 TG135, 150 x 200 mm, 1.6mm, Green/White, ENIG (1U"), 1oz, Tented via, 0.3mm 最小ビア, Single PCB, 1 design, Flying probe, Build time 3 days (標準)。Gold Fingers Yes の場合は Beveling 30°。Gerber 未アップロードの見積 (寸法入力のみ)。

### Takeaway
2 層 5 枚 $38.60 / 10 枚 $56.40、4 層 5 枚 $63.60 / 10 枚 $85.50。Gold Fingers Yes + 30° 面取りを選んでも価格は 1 セントも変わらなかった (金指の追加料金は見積上 $0)。日本への送料は OCS Express $8.66 (5 枚, 0.64kg) / $10.09 (10 枚, 1.17kg)、UPS $9.79 / $9.88。

### Cited Findings (全て [cart.jlcpcb.com/quote](https://cart.jlcpcb.com/quote) の calculationGoodsCostsNew 応答と画面表示, 2026-11-10)

| 層 | 枚数 | 金指 | Engineering fee | Surface Finish (ENIG) | Board | 合計 (Web Price) | 1 枚あたり | 重量 |
|---|---|---|---|---|---|---|---|---|
| 2 | 5 | Yes 30° | $4.00 | $20.10 | $14.50 | **$38.60** | $7.72 | 0.64kg |
| 2 | 5 | No | $4.00 | $20.10 | $14.50 | **$38.60** | $7.72 | 0.64kg |
| 2 | 10 | Yes 30° | $4.00 | $23.50 | $28.90 | **$56.40** | $5.64 | 1.17kg |
| 2 | 10 | No | $4.00 | $23.50 | $28.90 | **$56.40** | $5.64 | 1.17kg |
| 4 | 5 | Yes 30° | $25.00 | $20.10 | $18.50 | **$63.60** | $12.72 | 0.64kg 前後 (未記録) |
| 4 | 5 | No | $25.00 | $20.10 | $18.50 | **$63.60** | $12.72 | 同上 |
| 4 | 10 | Yes 30° | $25.00 | $23.50 | $37.00 | **$85.50** | $8.55 | 1.17kg |
| 4 | 10 | No | $25.00 | $23.50 | $37.00 | **$85.50** | $8.55 | 1.17kg |

- 画面には「Desktop Price From $36.60」(2 層 5 枚; JLCONE デスクトップアプリ割引 $2) と「Additional charges may apply for special cases」が併記。24 時間特急は +$7.60 (2 層 5 枚)。
- API 応答の内訳フィールド: projectMoney (=Engineering fee), adornPutMoney (=表面処理), stencilMoney (=Board 費), goldThicknessMoney=0, halfHoleMoney=0, largeAreaImmersionGoldMoney=0。Gold Fingers Yes/30° 選択時の送信値は goldFingerBevel=2 (No は 0)。
- 参考: Gerber をアップロードし Standard PCBA を ON にした場合、エッジレール 5mm x2 が自動追加され基板寸法 160x200mm 扱い、2 層 5 枚の PCB 価格は $39.70 に上がった (§1)。
- 画面上の「Coupons: Save $30.00 / Save $20.00」は新規アカウント向けクーポン表示 (適用条件は未確認; 見積額には含めていない)。

日本向け送料 (Shipping Estimate のダイアログで国を Japan に切替, calculateGoodsFreight 応答):

| 配送方法 | 5 枚 (0.64kg) | 10 枚 (1.17kg) | 日数 | 制限 |
|---|---|---|---|---|
| OCS Express | $8.66 | $10.09 | 4-6 business days | ≤20kg |
| UPS Worldwide Express Saver | $9.79 | $9.88 | 3-5 | ≤10000kg |
| S.F Express Economy | $18.90 | $21.53 | 5-9 | |
| DHL Express | $19.54 | $21.60 | 1-3 | |
| FedEx Express | $24.79 | $28.71 | 2-4 | |
| OCS NEP | 表示なし (—) | — | 4-6 | ≤0.6kg, ≤10x10cm |
| FedEx International Connect Plus | — | — | 5-6 | 1.5-10kg, ≤$650 |

- 米国向け表示 (比較): UPS Express Saver(DDP) $31.69 / DHL (DDP) $33.08 等、米国向けは "DDP" 表記。日本向けの選択肢には "DDP" の表記が無い — 同上
- JLCPCB 決済ページの配送条件の説明: 「CPT (Carriage paid to a named destination, duty, customs and taxes fee collected at the time of delivery)」「DDP (Customs fee paid by JLC…)」「FCA (Freight, customs clearance, taxes and duties are buyer's responsibility)」 — [JLCPCB payMethod テンプレート](https://cart.jlcpcb.com/client/template/payment/payMethod.html)
- 日本の輸入税: 課税価格の合計 1 万円以下は原則として関税・消費税・地方消費税が免除、個人使用貨物は海外小売価格 x0.6 を課税価格とする特例 (2026-10-04 時点で有効) — [hunade.com 解説 (2026-10-04 更新)](https://hunade.com/low-value-import-tax-reform)。同記事および財務省資料によれば 0.6 掛け特例の廃止と 1 万円以下の越境 EC 物品への消費税課税は 2028-04-01 (令和10年4月1日) 施行 — [財務省 令和8年度税制改正の解説 消費税法等](https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2026/explanation/PDF/p0823-0860.pdf), [brains-inc 解説](https://brains-inc.co.jp/column/others/useful-information/duty-exemption-system-for-small-value-imports/)
- 一般論として日本の輸入消費税は 10% を CIF+関税に課税 — [sino-shipping 解説](https://www.sino-shipping.com/dap-vs-ddp-japan/) (二次資料)

### Inferences
- 推論: 日本向けは CPT/DAP 型 (配達時に税を受取人払い)。2 層 5 枚 $38.60 + 送料 $8.66 = $47.26 ≈ ¥7,470 は、個人使用なら x0.6 で課税価格 ≈ ¥4,500 → 1 万円以下で免税。商用 (ゲームセンター向け事業用) なら x1.0 で ¥7,470 → それでも 1 万円以下で免税。PCBA を付けて 1 万円を超えると 10% の消費税 (+通関手数料、運送業者の立替手数料) が配達時に請求される。プリント基板 (HS 8534) と組立済み基板の関税率は本パスでは未確認 (多くの電子部品は日本で無税だが要確認)。
- 推論: 金指は追加料金 $0 なので「金指を付けるか否か」の PCB 製造費差はゼロ。差が出るのは PCBA の Standard/Economic 区分だけ。
- 推論: 4 層は 5 枚で +$25 (Engineering fee $4→$25 が主因)。5V NMOS バスと JAMMA 配線だけなら 2 層で足りる可能性が高い (設計判断)。

### Gaps
- PCBA 込みの実見積 (部品 BOM を入れた Economic/Standard の総額) は BOM 未確定のため未取得。§6 で料金表から計算。
- Gerber 審査後の追加料金 (特殊ケース) は実注文しないと確定しない。
- PCB の HS コード別関税率・UPS/OCS の通関手数料額: 未確認。

---

## 3. 秋月電子 (akizukidenshi.com) の手はんだ代替品 (2026-11-10 取得)

取得方法: 検索ページ `https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=<語>&search=search` を curl で取得し、商品ブロック (商品名・型番・販売コード・単位・税込価格・在庫表示・通販購入可能数) を解析。仕様欄は各商品ページ `https://akizukidenshi.com/catalog/g/g<販売コード>/` の「主な仕様」から。価格は税込、在庫数は「通販購入可能数」。

### Takeaway
74HC の DIP 品は 00/04/U04/08/14/32/74/125/138/157/165/244/245/373/573/595 が全て在庫あり (¥20-160)。秋月に無いのは 74HC139・74HC368・74HC574 (DIP)・CD4021・74HCT 系 DIP、および DIP の並列 SRAM (6116/6264/62256 系は 0 件)。5V 並列 SRAM で唯一在庫があるのは M68AF127B (1Mbit, 5V, 55ns) だが SOP32 の表面実装品。21.47727MHz の水晶・発振器は 0 件で、代替は Si5351A モジュール (在庫 10 セットのみ) か、14.31818MHz/3.579545MHz 品。高速コンパレータは DIP なら TL712CP (25ns, 5V, ¥210)。

### 3.1 SRAM (2KB ワーク RAM / VRAM 用)

| 品名 | 型番 | 販売コード | 価格 | 在庫 | 仕様 (商品ページ) |
|---|---|---|---|---|---|
| SRAM 1Mb | M68AF127B | 101083 (1個) / 101634 (5個入) | ¥70 / ¥250 | 639個 / 128パック | 1Mbit, 4.5-5.5V, 読出 55ns, SOP32 表面実装, STMicro |
| SRAM 512Kb (SPI シリアル) | 23LC512-I/P | 114062 | ¥250 | 565個 | シリアル。Famicom バスには直結不可 (推論) |
| (参考) 4Mbit DRAM | M11B416256A-35J | 101451 | ¥100 | 3,898個 | DRAM (リフレッシュ要、不適: 推論) |
- 検索語 6116 / 6264 / 62256 / HM62256 / CY62256 / AS6C / スタティックRAM: 該当 SRAM 0 件 (6116・6264 はヒットしても型番の一部一致の無関係品) — 各検索 URL (keyword=6116 等)
- 推論: M68AF127B を使うなら SOP32 なので PCBA 不可 (Basic でない) かつ手はんだ (1.27mm ピッチ SOP) になる。DIP 化には秋月の SOP 変換基板が必要。PCBA 側で LCSC の IS62C256AL (ext, 第1パス §2.2) を使う方が現実的。あるいは CPU 内蔵 RAM 相当をドナー Famicom の 2KB SRAM (CPU 用 / PPU 用の 2 個) から流用する (famicom_hardware.md 参照; 本パスでは未確認)。

### 3.2 74HC / CMOS ロジック (DIP 中心)

| 機能 | 型番 | 販売コード | 価格 | 在庫 | パッケージ |
|---|---|---|---|---|---|
| 74HC00 | TC74HC00AP / U74HC00L-D14 | 110856 / 114052 | ¥30 / ¥20 | 4,063 / 11,777 | DIP14 (114052 は商品ページで DIP, 伝播遅延 max 90ns) |
| 74HC02 | TC74HC02AP | 111489 | ¥30 | 672 | DIP |
| 74HC04 | TC74HC04AP(F) | 114058 | ¥30 | 1,120 | DIP (TC74HC04AF 111490 は SOP 2個入 ¥100) |
| 74HCU04 | TC74HCU04AP | 111328 | ¥30 | 157 | DIP |
| 74HC08 | TC74HC08AP | 114059 | ¥30 | 3,144 | DIP |
| 74HC14 | TC74HC14AP / U74HC14L-D14 | 110923 / 114054 | ¥40 / ¥30 | 2,945 / 2,857 | DIP14 |
| 74HC32 | TC74HC32AP(F) | 112877 | ¥30 | 323 (在庫僅少表示) | DIP |
| 74HC74 | TC74HC74AP | 110879 | ¥25 | 4,249 | DIP |
| 74HC125 | TC74HC125AP(F) | 131766 | ¥40 | 1,378 | DIP |
| 74AC125 | TC74AC125P | 111487 | ¥30 | 1,000 | DIP |
| 74HC138 | TC74HC138AP(F) | 110013 | ¥40 | 5,782 | DIP |
| 74ACT138 (TTL 入力) | TC74ACT138P | 110920 | ¥50 | 101 | DIP |
| 74LS138 | HD74LS138P | 107204 | ¥60 | 2,000 | DIP |
| 74HC139 | (該当なし) | - | - | 0 件 | - |
| 74HC157 | TC74HC157AP(F) | 131765 | ¥80 | 1,138 | DIP |
| 74HC165 | TC74HC165AP(F) | 114679 | ¥100 | 1,010 | DIP |
| 74HC244 | TC74HC244AP(F) / HD74HC244FPEL | 131762 / 111398 | ¥120 / ¥100(4個入) | 1,480 / 19パック | DIP / SOP |
| 74HC245 | TC74HC245AP(F) | 131761 | ¥120 | 1,405 | DIP |
| 74HC368 | (該当なし) | - | - | 0 件 | - |
| 74HC373 | TC74HC373AP(F) | 131768 | ¥130 | 1,522 | DIP |
| 74F373 | 74F373PC | 113348 | ¥100 (10個入) | 11パック | DIP |
| 74HC541 | TC74HC541AP | 103632 | ¥50 | 12,608 | DIP (244 の代替に使える 8bit バッファ: 推論) |
| 74HC573 | TC74HC573AP(F) | 131763 | ¥160 | 1,465 | DIP |
| 74HC574 | (DIP 該当なし) / 74LCX574FT (3.3V 系 TSSOP) | 114114 | ¥100 (5個入) | 829パック | TSSOP |
| 74HC273 (8bit D-FF, 574 の代替候補) | TC74HC273AP | 115412 | ¥70 | 1,856 | DIP |
| 74HC595 | TC74HC595AP(F) / U74HC595AG-D16 / TC74HC595AF | 131760 / 114053 / 110077 | ¥110 / ¥40 / ¥50 | 748 / 500 (「2月中旬入荷予定」併記) / 2,540 | DIP / DIP / SOP |
| CD4021 (Famicom パッドのシフトレジスタ) | (該当なし) | - | - | 0 件 (TC4021, 4021B でも 0) | - |
| 74HC161 | TC74HC161AF | 110857 | ¥30 | 3,230 | SOP |
| 74HC4040 | TC74HC4040AP(F) | 131767 | ¥110 | 1,245 | DIP |
| 74HCT 系 DIP | (該当なし) | - | - | 「74HCT」検索 0 件。TC74VHCT04AFT (109522, ¥100/5個, SOP) と TC74VHCT540AF (100659, ¥100/5個, SOP) のみ | SOP |
- 出典: 各検索ページ (keyword=74HC00 … 74HC595, 4021, 74HCT, 74AC, ロジックIC p=1-3)、例 [74HC245 検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=74HC245&search=search)、[ロジックIC 検索 (142 件)](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%83%AD%E3%82%B8%E3%83%83%E3%82%AFIC&search=search)
- 推論: 74HC368 (反転 3 ステートバッファ, Famicom のコントローラ入力用) は 74HC240 系や 74HC125+インバータで代替が必要。74HC139 は 74HC138 1 個 (または 2 個) で代替可能。CD4021 はコントローラ側 (パッド内) の部品なので本基板では MCU で模擬するか 74HC165 で代替可能 (動作差は要検証)。

### 3.3 スピーカー用パワーアンプ

| 品名 | 型番 | 販売コード | 価格 | 在庫 | 仕様 (商品ページ) |
|---|---|---|---|---|---|
| LM386 (DIP8) | LM386G-D08 (UTC) | 114548 | ¥40 | 11,965 | 700mW (9V 8Ω THD10%), 4-12V, 利得 46dB 固定 |
| LM386 (SOP8) | LM386G-S08 | 114549 | ¥30 | 12,469 | SOP8 |
| LM386 アンプキット | AE-KIT45-386AMP | 115540 | ¥500 | 314セット | キット |
| 2回路 (BTL 可) | M2073G-D08 (UTC, NJM2073 互換) | 117431 | ¥40 | 4,992 | 1.8-15V, BTL 2.0W (9V 16Ω), DIP8 |
| 2回路 (BTL 可) | TDA2822L-D08 | 109720 | ¥50 | 27,759 | 1.8-12V, 0.65Wx2 / BTL 1.35W, DIP8 |
| TA7368P 互換 | TA7368PG (UTC) | 106662 | ¥60 | 6,456 | 1.1W, max 14V, SIP9 |
| TDA2030 | TDA2030L-TB51 | 109719 | ¥60 | 6,361 | (検索一覧より、仕様未取得) |
| LM1875 | LM1875G-TB5 | 115954 | ¥90 | 15,598 | 20W 級 (一覧の品名より) |
| D級モジュール | AE-PAM8012 | 108217 | ¥300 | 692 | 2.5-5.5V, 8Ω で最大 1.0W / 4Ω 2.0W @5V, 短絡・過熱保護, 10.5x11mm, スルーホール端子 |
| D級 IC | PAM8302AADCR | 114187 | ¥40 | 2,378 | SMD |
| D級 IC | PAM8304ASR | 113716 | ¥45 | 1,520 | SMD |
| ステレオ D級モジュール | AE-PAM8403-AMP | 115698 | ¥750 | 32 (在庫僅少) | - |
| μPC2002H | uPC2002H | 117725 | ¥200 | 84 | 8-18V |
| 10W BTL | LA4902 | 101571 | ¥300 (2個入) | 37パック | 8-18V |
- 出典: [オーディオアンプ 検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%82%AA%E3%83%BC%E3%83%87%E3%82%A3%E3%82%AA%E3%82%A2%E3%83%B3%E3%83%97&search=search)、[LM386G-D08](https://akizukidenshi.com/catalog/g/g114548/)、[M2073](https://akizukidenshi.com/catalog/g/g117431/)、[TDA2822L](https://akizukidenshi.com/catalog/g/g109720/)、[TA7368P](https://akizukidenshi.com/catalog/g/g106662/)、[AE-PAM8012](https://akizukidenshi.com/catalog/g/g108217/)
- 推論: JAMMA は +12V が供給されるので、LM386 (max 12V) は 12V 直結だと定格上限ぎりぎり。M2073 (max 15V) を 12V で BTL 動作させるのが手はんだ部品で最も単純。5V で動かすなら AE-PAM8012 (8Ω 1.0W) モジュールを載せるのが最小部品数。

### 3.4 コンパレータ (同期分離・ビデオ処理用)

| 品名 | 型番 | 販売コード | 価格 | 在庫 | 応答時間・電源・パッケージ (商品ページ) |
|---|---|---|---|---|---|
| 高速 (プッシュプル) | TL712CP | 113885 | ¥210 | 730 | 25ns, 5V, 17mA, DIP8 |
| 高速 | ADCMP600BRJZ-R2 | 130362 | ¥830 | 220 | 4ns, 2.5-5.5V, SOT23-5 |
| 高速 | LTC6752HS5#TRMPBF | 130361 | ¥750 | 129 | 1.2ns, 2.45-3.5V (5V 不可), TSOT23-5 |
| ハイスピード 2回路 | LM319M | 101270 | ¥50 (5個入) | 1,051パック | 80ns, オープンコレクタ, SOP14 |
| 汎用 2回路 | LM393GN | 116987 | ¥30 | 7,427 | (一覧) |
| 汎用 4回路 | LM339 | 100436 | ¥30 | 23,038 | (一覧) |
| 汎用 2回路 | NJM2903D | 113486 | ¥40 | 8,201 | (一覧) |
| 汎用 4回路 | μPC339C | 112556 | ¥20 | 328 | (一覧) |
| LM311 / TLV3501 / LT1016 | - | - | - | 0 件 | - |
- 出典: [コンパレーター検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%82%B3%E3%83%B3%E3%83%91%E3%83%AC%E3%83%BC%E3%82%BF%E3%83%BC&search=search)、[TL712CP](https://akizukidenshi.com/catalog/g/g113885/)、[ADCMP600](https://akizukidenshi.com/catalog/g/g130362/)、[LTC6752](https://akizukidenshi.com/catalog/g/g130361/)、[LM319M](https://akizukidenshi.com/catalog/g/g101270/)

### 3.5 クロック源

| 品名 | 型番 | 販売コード | 価格 | 在庫 | 備考 |
|---|---|---|---|---|---|
| 21.47727MHz 水晶/発振器 | - | - | - | 0 件 (keyword=21.477) | 取扱なし |
| Si5351A 3ch プログラマブル周波数ジェネレーターモジュール | AE-Si5351A-B | 110679 | ¥650 | **10 セット** | 2.5kHz-200MHz, 3 出力 (PLL 2 系統), I2C 設定 |
| Si5351A IC 単体 | Si5351A-B | 110141 | ¥320 | 入荷未定 | |
| 14.31818MHz 水晶 | HUSG-14.31818-20 | 108670 | ¥30 | 4,310 | HC-49 系 |
| 14.31818MHz 発振器 5V | SG8002DC-14.31818MHz-PHB | 104534 | ¥300 | 196 | |
| 14.31818MHz 分周付発振器 | EXO3 14.31818MHz (キンセキ) | 101685 | ¥120 | 2,000 | DIP8, 5V, 1/2-1/256 分周出力 (3.579545MHz 等), ±100ppm |
| 3.579545MHz 水晶 | HUSG-3.579545-20 | 108664 | ¥30 | 269 | |
| 3.579545MHz 発振器 | TCO-711A 3.579545MHz | 101567 | ¥100 | 2,652 | |
| MEMS 発振器 (書込用ブランク) | SIT2001BI-S1-XXX / SIT8208AI-21-XXX | 113512 / 113513 | ¥130 / ¥140 | 922 / 1,277 | 「専用のプログラマーで書き込むことで任意の周波数」(プログラマー Time Machine II 113514 が別途必要) |
| 26.601712MHz (PAL) | - | - | - | 0 件 | |
- 出典: [クリスタル検索 (114 件)](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%82%AF%E3%83%AA%E3%82%B9%E3%82%BF%E3%83%AB&search=search)、[14.318 検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=14.318&search=search)、[AE-Si5351A-B](https://akizukidenshi.com/catalog/g/g110679/)、[EXO3](https://akizukidenshi.com/catalog/g/g101685/)、[SiT2001B blank](https://akizukidenshi.com/catalog/g/g113512/)

### 3.6 レベル変換・USB・ヒートシンク・ヒューズ・電解コンデンサ

| 分類 | 品名 / 型番 | 販売コード | 価格 | 在庫 | 備考 |
|---|---|---|---|---|---|
| レベル変換 8bit | AE-LLCNV8 (FXMA108) | 104522 | ¥350 | 398 | 1.65-5.5V 双方向, 自動方向検出, DIP20 相当 |
| レベル変換 8bit (Sbkit) | AE-LLCNV8-DIP20 (FXMA108) | 117062 | ¥250 | 154セット | 同上 |
| レベル変換 16bit | AE-LLCNV-LVCH16T245 | 115696 | ¥300 | 315セット | 方向ピン制御型, 1.65-5.5V |
| レベル変換 4bit | AE-TXS0104E-BO | 129507 | ¥350 | 498 | 24Mbps |
| レベル変換 4bit (MOSFET) | AE-LCNV4-MOSFET(BSS138) | 113837 | ¥200 | 2,456 | |
| USB Type-C (USB2.0 16P) | 5077CR-16-SMC2-BK-TR | 114356 | ¥110 | 209 (在庫僅少) | |
| USB Type-C 電源用 | A295-CTRPB-1 / UJC-HP-3-SMT-TR | 116895 / 116438 | ¥40 / ¥90 | 19,835 / 3,727 | |
| USB Type-C DIP 化 (シンプル) | AE-USB2.0-TYPE-C | 113080 | ¥350 | 695 | |
| USB Type-C 電源用 DIP 化キット | AE-USB2.0-TYPE-C-CTRPB-1 | 117123 | ¥130 | 1,246セット | |
| USB microB 電源用 DIP 化キット | AE-MRUSB-DIP | 110972 | ¥130 | 186セット | |
| USB-シリアル (Type-C) | AE-CH340E-TYPEC | 114745 | ¥550 | 1,287 | |
| ヒートシンク TO-220 | 30PC030-01030 (30x30x30) | 100429 | ¥110 | 772 | |
| ヒートシンク | 16PB017-01025 / 20PB020-01025 | 105053 / 105054 | ¥60 / ¥80 | 2,437 / 2,054 | |
| ポリスイッチ (リード) | MF-R300 (3A, trip 6A, 30V) | 112630 | ¥40 | 2,766 | |
| ポリスイッチ (リード) | MF-RX110 (1.1A, trip 2.2A, 72V) | 113585 | ¥50 | 4,732 | |
| ポリスイッチ (リード) | RGEF300 (3A, trip 5.1A, 16V) | 100769 | ¥30 | 5,947 | |
| ポリスイッチ (SMD) | PICOSMDC110S-2 (1.1A, 6V) | 113955 | ¥40 | 19,591 | |
| ガラス管ヒューズ 20mm | MF51NR 250V 2A / 5A | 107130 / 107131 | ¥40 | 536 / 1,961 | |
| 電解 470µF16V | 16WXA470MEFC8X9 / 16PX470MEFC8X11.5 | 108426 / 110273 | ¥10 | 25,462 / 11,016 | |
| 電解 1000µF25V | 25PX1000MEFC10X16 | 117885 | ¥40 | 30,594 | |
| 電解 1000µF10V | 10WXA1000MEFC10X9 | 108424 | ¥20 | 5,164 | |
| 電解 220µF16V / 25V | 16PX220MEFC6.3X11 / 25PX220MEFC6.3X11 | 110272 / 117879 | ¥10 / ¥20 | 13,434 / 21,767 | |
| 電解 47µF35V | 35PX47MEFC5X11 | 117887 | ¥10 | 75,188 | |
| 電解 10µF50V | 50PX10MEFC5X11 | 117897 | ¥10 | 135,778 | |
| 電解 100µF16V (第1パス) | 16PX100MEFC5X11 | 110271 | ¥10 | 67,744 | |
- 出典: [レベル変換検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%83%AC%E3%83%99%E3%83%AB%E5%A4%89%E6%8F%9B&search=search)、[USBコネクター検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=USB%E3%82%B3%E3%83%8D%E3%82%AF%E3%82%BF%E3%83%BC&search=search)、[ポリスイッチ検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%83%9D%E3%83%AA%E3%82%B9%E3%82%A4%E3%83%83%E3%83%81&search=search)、電解コンデンサー各容量検索、[ヒートシンク検索](https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%83%92%E3%83%BC%E3%83%88%E3%82%B7%E3%83%B3%E3%82%AF&search=search)、[AE-LLCNV8](https://akizukidenshi.com/catalog/g/g104522/)、[AE-TXS0104E-BO](https://akizukidenshi.com/catalog/g/g129507/)

### Gaps (§3)
- 秋月の DIP 並列 SRAM は 0 件 (検索で確認)。他店 (共立・千石・マルツ・aitendo) の 62256 系在庫は本パスでは未確認。
- 74HC139 / 74HC368 / 74HC574 / CD4021 / 74HCT DIP: 秋月では入手不可 (0 件)。
