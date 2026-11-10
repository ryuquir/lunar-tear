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
| 4 | 5 | Yes 30° | $25.00 | $20.10 | $18.50 | **$63.60** | $12.72 | 0.64kg |
| 4 | 5 | No | $25.00 | $20.10 | $18.50 | **$63.60** | $12.72 | 0.64kg |
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

---

## 4. ファミコン 60 ピン (2x30, 2.54mm) カードエッジコネクタ

### Takeaway
JLCPCB/LCSC に WingTAT の 60P 2.54mm 垂直スルーホール品 ED60BGFBK (LCSC C5173310) があり、在庫 299、$1.30、JLCPCB 部品ライブラリ上「Extended / Assembly Type: Wave Soldering / PCBA Type: Economic and Standard」— つまり JLCPCB に実装させられる。ただしデータシートの推奨カード厚は 1.57±0.15mm で、ファミコンのカートリッジ基板 (1.2mm) より厚い前提 (緩くなる)。ファミコン専用品としては AliExpress のクローン機用 60P スロットが $3.59-$5.82。国内店 (千石・マルツ・共立・aitendo・Amazon.co.jp・Yahoo) とデジキー・マウサーは自動取得がブロック/0 件で、在庫確認できず。

### Cited Findings
- ファミコンカートの寸法: 「The pin pitch is 2.54mm, with 2 rows of 30 pads」「Board thickness: 1.2 mm」「Card edge width: 78.4 mm」、信号パッド幅 1.6mm / 電源パッド 2.6mm、パッド間 0.94mm (ノギス実測 ±0.05mm) — [NESdev Wiki: Famicom cartridge dimensions](https://www.nesdev.org/wiki/Famicom_cartridge_dimensions) (WebFetch で本文取得 2026-11-10)
- 板厚の適合: kevtris「You want a 60 pin connector, .1" pitch pins, and for a board thickness of .043" or so. A connector for .062" boards will work, but it will be loose and wobble about.」「I suggest buying the cheapest cart-accepting famiclone possible on ebay to get a reasonable connector.」「One possible thing would be to bend the pins on a .062" connector outwards to grab the board tighter.」(2006-12-30) — [NESdev forum t=2836](https://forums.nesdev.org/viewtopic.php?t=2836)

| 候補 | 入手先 | 型番 / コード | 価格 | 在庫 (2026-11-10) | 実装 | 適合カード厚 | ファミコン適合の実績 |
|---|---|---|---|---|---|---|---|
| WingTAT 60P 2.54mm 垂直 THT, 金めっき | LCSC / JLCPCB | ED60BGFBK / C5173310 | $1.2959 (1+), $1.0805 (10+) | LCSC 299 / JLCPCB 299 | THT 垂直, 高さ 15.6mm, 幅 9.25mm; JLCPCB「Wave Soldering」「Economic and Standard」 | データシート「Recommended Card Layout」に 1.57±0.15 | 不明 (推論: 1.2mm カートでは緩い) |
| WingTAT 60P 2.54mm 垂直 THT | LCSC | ED60MEBGFBK / C5242017 | $1.6695 | LCSC 94 / JLCPCB 0 | THT 垂直 15.6mm | 未取得 | 不明 |
| WingTAT 60P 2.54mm 直角 THT | LCSC | ER60BGFBK / C5173348 | $1.8371 | 0 | 直角, 9.25mm | 未取得 | 不明 |
| WingTAT 60P 2.54mm Free Hanging (ケーブル用) | LCSC | EC60P03BK-0001 / C5448308 | $3.1538 | 120 | 基板実装ではない | - | - |
| Sullins EBC30 系 (30x2, 0.100") | LCSC | EBC30MMAN C6941170, EBC30DRAI C6841138, EBC30DRXI 等 | $15.78-$22.59 (1+) | 0 (「Pre/New」) | THT | 未取得 | 不明 |
| TinyNES (実チップ使用の量産再現機) の Famicom アダプタ | (BOM 記載) | WingTAT S-60M-2.54-5 | - | LCSC 検索で品番ヒットせず | - | 未確認 | TinyNES で採用 |
| クローン機用 60P スロット「Clone Console 60 Pin Connector Replacement ... for Famicom」 | AliExpress | - | $3.59 (新規ユーザー向け表示 $1.09) | 「6 sold」 | THT (写真未確認) | 未確認 (ファミコンカート用と推論) | 商品名上はファミコン用 |
| 「B18B Replacement 60 Pin Game Cartridge Adapter Card Slot Connector For Famicom FC Clone Console」 | AliExpress | - | $5.82 | - | 同上 | 同上 | 商品名上はファミコン用 |
| 「Game Card Slot For SFC SNES FC Console Connector 64Pin 60Pin 62Pin 50Pin ... 2.5mm Interval」 | AliExpress | - | $9.96 (表示 $1.09) | - | - | - | 「2.5mm Interval」表記 (2.54mm との差は未確認) |
| Hirose CR22A-60D-2.54DS(70) (第1パス: ブログで ¥250, 2008/2022) | 千石電商 | - | - | 千石サイト検索は bot 遮断で未確認 | THT | 未確認 | ブログでファミコン用に使用 |
- 出典: [LCSC 検索 "2.54mm edge connector 60P"](https://www.lcsc.com/search?q=2.54mm%20edge%20connector%2060P) (5 件)、[LCSC C5173310](https://www.lcsc.com/product-detail/C5173310.html)、[JLCPCB C5173310](https://jlcpcb.com/partdetail/C5173310)、ED60BGFBK データシート (JLCPCB 部品ページの Datasheet リンク, jlc-prod-smt.oss-eu-central-1.aliyuncs.com …/8590906393052864512-C5173310.pdf: 「Insertion Force:0.4Kgf Max.Per Pair」「Withdrawal Force:0.25Kgf Max.Per Pair」「Gold Plated On Contact Area」「Recommended Card Layout … 1.57±0.15」)、[LCSC 検索 EBC30](https://www.lcsc.com/search?q=EBC30) (139 件)、[AliExpress "famicom 60 pin slot"](https://www.aliexpress.com/w/wholesale-famicom-60-pin-slot.html)、[TinyNES Famicom Adapter BOM](https://raw.githubusercontent.com/loglow/TinyNES/main/Famicom%20Adapter/TinyNES_Famicom_Adapter_BOM.csv)
- 試行して失敗した経路 (2026-11-10): マルツ `GoodsListNavi.jsp?keyword=CR22A-60D` → Cloudflare「セキュリティ検証」; 千石電商 検索 (URL 直接 / 検索窓入力) → 「該当がありません」(パラメータ脱落) の後「現在、サイトをご利用いただけない状態です」; 共立エレショップ `keyword=カードエッジ / エッジコネクタ / CR22A / ファミコン` → 「ご指定の条件に一致する商品が見つかりませんでした」(4 語とも 0 件); aitendo `?mode=srh&keyword=` (EUC-JP/ASCII) → 検索結果ではなく通常ページが返り判定不能; Amazon.co.jp `s?k=ファミコン 60ピン スロット` → エラーページ; Yahoo!ショッピング → 「ページは現在表示できません」; Digi-Key (digikey.jp / digikey.com) → Cloudflare; Mouser (mouser.jp) → 「Access Denied」。
- ドナー機コネクタ流用: 他ノートの調査で、OpenTendo 作者が SRAM について「The RAM from an original OEM motherboard can be used on OpenTendo」と回答 (2023-10-16) — [OpenTendo issue #20](https://github.com/Redherring32/OpenTendo/issues/20) (famicom_electrical_and_pitfalls.md より)。60P コネクタ自体の取り外し体験談は本パスでは見つからず (Web 検索枠が尽きたため追加検索不能) — 未確認。

### Inferences
- 推論: PCBA に載せられる 60P 品は ED60BGFBK のみ現実的 (Extended, wave)。1.57mm 前提のため、1.2mm のファミコンカートでは接触圧不足・ガタの恐れ。kevtris の指摘どおり。実機で嵌合試験してから採用すべき。
- 推論: 最も確実なのはドナー機の 60P コネクタ流用 (どのみち CPU/PPU を取るために本体を分解する)。60 本の THT 吸い取りは手間だが、ファミコン純正カートとの嵌合実績は確実。コネクタのメーカー型番は他ノートでも未確認。
- 推論: AliExpress のクローン機用 60P スロットはファミコンカート (1.2mm) 用に作られていると考えられ、価格 $3.59-5.82 で 1 枚 1 個。ただしピン長・ピッチ (2.5 vs 2.54mm 表記) と取付穴形状は現物確認要。

---

## 5. 21.47727MHz クロック

### Takeaway
21.47727MHz の水晶は JLCPCB/LCSC に Extended 品が 4 種 (在庫 80-190 個、$0.07-0.11) あり、うち 3 種は JLCPCB で「Wave Soldering, Economic and Standard」実装可能。秋月には無い。TinyNES が使う SiTime MEMS 発振器 SIT2001BC-S2-33N-21.477270 は LCSC 在庫 0。秋月の Si5351A モジュール (¥650) は 21.4772727MHz を分数 PLL で表現できるが在庫 10 セット。ドナー機の水晶 X1 (21.47727MHz) は 2SC2021 による 1 石ディスクリート発振回路の部品で、流用するなら発振回路ごと再現する必要がある。

### Cited Findings
| 品 | 入手先 | コード | 価格 | 在庫 | 実装 |
|---|---|---|---|---|---|
| 21.47727MHz HC-49S 20pF ±20ppm | JLCPCB | C368768 | $0.0920 (1+) / $0.0732 (50+) | 134 | Extended, Wave Soldering, Economic and Standard |
| 21.47727MHz HC-49S 20pF ±20/±30ppm | JLCPCB | C18213345 | $0.0737 / $0.0586 (100+) | 190 | Extended, Wave Soldering |
| 21.47727MHz HC-49S-SMD-2P-Mini ±30ppm | JLCPCB | C7473019 | $0.0696 | 80 | Extended, Wave Soldering (表示どおり) |
| 21.4772MHz HC-49S-SMD 20pF | JLCPCB | C22464834 | $0.1125 | 83 | Extended, SMT Assembly |
| SIT2001BC-S2-33N-21.477270 (3.3V MEMS, SOT-23-5, ±25ppm) | LCSC | C17667580 | $1.446 | 0 | - |
| SIT2001BC-S2-33N-21.477270E | LCSC | C1020111 | $2.8515 | 0 | - |
| AE-Si5351A-B モジュール | 秋月 | 110679 | ¥650 | 10 セット | 手はんだ |
| SiT2001B / SiT8208 ブランク (要プログラマー) | 秋月 | 113512 / 113513 | ¥130 / ¥140 | 922 / 1,277 | 表面実装 SOT23-5、プログラマー Time Machine II (113514) 必要 |
- 出典: [JLCPCB C368768](https://jlcpcb.com/partdetail/C368768), [C18213345](https://jlcpcb.com/partdetail/C18213345), [C7473019](https://jlcpcb.com/partdetail/C7473019), [C22464834](https://jlcpcb.com/partdetail/C22464834), [LCSC 検索 SIT2001BC-S2-33N-21.477270](https://www.lcsc.com/search?q=SIT2001BC-S2-33N-21.477270), [秋月 AE-Si5351A-B](https://akizukidenshi.com/catalog/g/g110679/)
- TinyNES は「IC MEMS OSC XO 21.477270MHZ SMD, SiTime, SIT2001BC-S2-33N-21.477270」を使用 — [TinyNES Main Board BOM](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_BOM.csv)
- 純正 HVC-CPU-GPM-02 は「2SC2021 1 石発振 (X1, C1 18p, TC1 30p, C3 51p, R10 100k, R11 1.2k, R9 150Ω, C2 10n)」のコレクタから CPU/PPU へ 10nF 結合 — famicom_electrical_and_pitfalls.md (出典 [TrexMakes Nintendo_Famicom_Console](https://codeberg.org/TrexMakes/Nintendo_Famicom_Console))
- 秋月の 21.477 検索 0 件 (§3.5)。Digi-Key/Mouser は bot 遮断で未確認 (§4 と同じ)。

### Inferences
- 推論 (計算): Si5351A (25MHz 水晶) で 21.4772727MHz = 236.25/11 MHz を出すには PLL = 859.0909MHz (= 40 x 21.4772727) とし、PLL 倍率 = 859.0909/25 = 34 + 4/11 (a=34, b=4, c=11)、出力分周 40 (整数) で、水晶誤差を除けば厳密に一致する。Pico から I2C で設定可能。
- 推論: 最も安く PCBA 化できるのは JLCPCB の HC-49S 水晶 (C18213345, $0.07) + Basic のトランジスタ (MMBT3904 等) と受動部品で純正と同じ 1 石発振を組む案。ただし在庫は 134-190 個と少なく、10 枚程度なら足りる。発振回路の定数は純正 (2SC2021) と異なるトランジスタで要検証。
- 推論: ドナー機の水晶 X1 の流用は可能 (部品自体は汎用 HC-49 系水晶) だが、発振回路 (2SC2021 + トリマ TC1 等) も新基板に再現する必要がある。2SC2021 の入手性は未確認。
- 推論: RP2350 の PIO 生成は 12MHz 水晶基準で最良 +1058ppm (他ノート rgb_pico2_feasibility.md) — 色副搬送波を使わない RGB 出力なら許容できる可能性があるが、NTSC 規定 (±40Hz ≈ ±2ppm) からは大きく外れる。

---

## 6. BOM 方針 3 案と 1 枚あたりコスト (5 枚 / 10 枚)

### Takeaway
金指を本体基板に作る限り PCBA は Standard 確定で、Standard では Basic にも 1 種類 $1.53 の装填料がかかるため「Basic のみ」にしても装填料は無料にならない (Preferred の免除も Economic 限定)。試算 (下表、全て推論を含む概算) では 1 枚あたり総額は、A (Basic のみ + 秋月手はんだ) 5 枚 約¥6,800 / 10 枚 約¥5,200、B (Basic+Preferred+少数 Extended、新品 SRAM) 約¥8,800 / ¥6,800、C (金指エッジ基板を分離 + 本体 Economic PCBA、B と同じ部品) 約¥7,600 / ¥6,200。SRAM をドナー流用すると B・C とも約¥1,250/枚下がる。最安は「C の構成で PCBA は Basic のみ (C')」で 約¥5,100 / ¥4,350。いずれもドナー Famicom 本体の価格は含まない。

### 共通の仮定 (全て推論。実 BOM 未確定のため桁を示すもの)
- 為替 ¥158/USD (JLCPCB 表示 157.7523)。
- 本体基板 150x200mm 2 層 1.6mm ENIG。金指版 PCB 代は §2 の実見積: 5 枚 $39.70 (Standard PCBA でエッジレール付加後の実表示)、10 枚は $56.40 にレール分の比率を掛けた $58.0 (推論; レール付き 10 枚の実見積は未取得)。
- 分離案 C のエッジ基板: 120x60mm 2 層 ENIG 金指 30° 面取り、PCBA なし。実見積 5 枚 $24.90 / 10 枚 $29.30 (Engineering $4 + ENIG $17.40/$18.30 + Board $3.50/$7.00)。本体基板 150x150mm 2 層 LeadFree HASL: 5 枚 $16.50 / 10 枚 $27.80 (Economic PCBA の表で 2L 1.6mm Green HASL は 2-50 枚可)。— [cart.jlcpcb.com/quote](https://cart.jlcpcb.com/quote) 2026-11-10。日本向け OCS 送料: エッジ基板単体 $7.23、本体 150x150 は $8.66。
- PCBA 料金は §1 の料金表 (Standard: Setup $25.56 + ステンシル $8.21 + 全種類 $1.53/種; Economic: Setup $8.18 + ステンシル $1.53 + Extended のみ $3.07/種; SMT $0.0016/ジョイント; THT は $3.50/注文 + $0.0164/ジョイント)。Confirm Parts Placement ($0.45)、部品の最小購入数・損耗分 (attrition) は含めない。
- 部品種類数: Basic 20 種 (抵抗 6 値、MLCC 4 値、AMS1117-3.3、ULN2003A、LM358、74HC14、MMBT3904/S8050、SS34、LED、TVS 等)。SMT ジョイント 300 (A, C') / 500 (B, C) 個/枚。Basic 部品代 $1.50/枚。
- B・C で PCBA に追加する部品 (12 種; 単価は第1パス §2 と本ノート §4-5 の LCSC 表示): 74HC373 $0.339、74HC138 $0.200、74LVC245 x3 $0.206、74HC165 x2 $0.111 (Preferred)、IS62C256AL x2 $3.9694、21.47727MHz 水晶 C18213345 $0.0737 (wave)、60P ED60BGFBK $1.2959 (wave)、LM386 SOP $0.108、ポリスイッチ 1812 $0.062、SMD 電解 3 個 計 $0.30 (仮)、DIP-40 ソケット 2 個 計 $0.50 (仮; LCSC の DIP-40 ソケット品は本パスで未確認) → 部品代 $13.16/枚 (SRAM ドナー流用なら $5.22)。THT ジョイント 142/枚 (60P 60 + DIP40 x2 80 + 水晶 2) → $2.33/枚 + $3.50/注文。
- 秋月手はんだ (A, C'): DIP-40 丸ピンソケット x2 ¥220、Pico 2 ¥990、Pico 用ピンソケット (FH-1x20-3.2CO) ¥250、74HC373 ¥130、74HC138 (139 の代替) ¥40、74HC165 x2 ¥200、レベル変換 AE-LLCNV8-DIP20 x2 ¥500、M2073 ¥40、電解 5 個 ¥80、MF-R300 ¥40 = **¥2,490/枚**。SRAM・水晶・60P コネクタはドナー機から流用 (¥0) と仮定。B・C の手はんだは Pico 2 + ソケット ¥1,240/枚、C は基板間接続用ピンヘッダ/ソケット ¥150/枚を追加 (FH-2x20SG ¥80 + PH-1x40SG x2 ¥70)。
- 秋月送料: 佐川「荷物1個口あたり550円」、「商品合計…税込11,000円…以上は…送料無料」— [秋月 ご利用案内](https://akizukidenshi.com/catalog/pages/buy.aspx)。5 枚分以上の一括注文はほぼ ¥11,000 を超えるので送料 0 とした。
- JLCPCB→日本の送料: OCS 相当で $10-13 (PCBA 分の重量増を見込んだ推論値)。輸入消費税: 注文総額が ¥10,000 を超えるので 10% を加算 (事業用 = 課税価格 100% と仮定)。通関手数料・立替手数料は未確認のため含めない。

### 試算結果 (1 枚あたり、税込概算)

| 方針 | 内容 | 5 枚: JLCPCB 側 (税込) | 5 枚: 総額/枚 | 10 枚: JLCPCB 側 (税込) | 10 枚: 総額/枚 |
|---|---|---|---|---|---|
| A | 金指一体基板、Standard PCBA は Basic 20 種のみ、他は秋月 DIP を手はんだ、ドナーから SRAM・水晶・60P 流用 | $136.37 ($27.27/枚 ≈ ¥4,309) | **≈ ¥6,800** | $169.59 ($16.96/枚 ≈ ¥2,679) | **≈ ¥5,170** |
| B | 金指一体基板、Standard PCBA に Basic+Preferred+Extended 32 種 (新品 IS62C256AL x2、60P と水晶も wave 実装)、手はんだは Pico 2 のみ | $240.21 ($48.04/枚) | **≈ ¥8,830** | $352.11 ($35.21/枚) | **≈ ¥6,800** |
| B' | B で SRAM をドナー流用 | $196.54 | ≈ ¥7,450 | $264.79 | ≈ ¥5,420 |
| C | 金指エッジ基板 (PCBA なし) + 本体 Economic PCBA (B と同じ部品、Extended 10 種は $3.07、Preferred/Basic は無料) | $195.52 ($39.10/枚) | **≈ ¥7,570** | $304.57 ($30.46/枚) | **≈ ¥6,200** |
| C (SRAM 流用) | | $151.86 | ≈ ¥6,190 | $217.25 | ≈ ¥4,820 |
| C' | C の基板構成で PCBA は Basic のみ (装填料 $0)、他は A と同じ秋月手はんだ | $78.11 ($15.62/枚) | **≈ ¥5,110** | $108.47 ($10.85/枚) | **≈ ¥4,350** |
(計算スクリプトの値。丸め誤差 ±¥10。ドナー Famicom 本体の調達費、カートリッジ、筐体配線、Pico 用ファーム開発は含まない)

### Inferences
- 推論: 「Basic のみ」ルールは Economic PCBA でこそ意味がある (Basic/Preferred は装填料 0)。金指一体基板 (Standard) では Basic も 1 種 $1.53 なので、ルールの経済的根拠が薄れ、代わりに「種類数の最小化」がそのまま効く。
- 推論: 分離案 C/C' はエッジ基板に ENIG 代 (約 $17-18) を払い、本体は HASL で安く作れる。本体を Economic にできるため固定費が $33.77 → $9.71 に下がる。基板間接続 (JAMMA 信号 約 40 本 + 電源) の手はんだと嵌合信頼性が代償。
- 推論: 10 枚では A と C' の差は約 ¥800/枚、B と C の差は約 ¥600/枚。差の大部分は Standard の固定費 (Setup+ステンシル+Basic 装填料) の按分。
- 推論: どの方針でも JLCPCB の 21.47727MHz 水晶 (在庫 134-190) と ED60BGFBK (在庫 299)、IS62C256AL (在庫 2,548) の在庫が 10 枚分 (各 10-20 個) を満たす。秋月 Si5351A モジュールは在庫 10 なので 10 枚を超えると不足。

### Gaps (§6)
- レール付き Standard PCBA の 10 枚 PCB 代、部品 BOM を入れた実 PCBA 見積 (Gerber+BOM+CPL のアップロードが必要) は未取得。
- LCSC の DIP-40 ソケット (THT, wave 可) の品番・価格・在庫は未確認。
- 通関手数料・UPS/OCS の立替手数料額、PCB の関税率は未確認。
- ドナー Famicom の価格は本調査範囲外 (未確認)。

---

## 既存ノートへの訂正 (parts_and_manufacturing.md に対して)

| # | 第1パスの記述 | 訂正 / 補足 | 根拠 |
|---|---|---|---|
| 1 | §5「ゴールドフィンガー追加費の第三者推定: 5 枚注文で $10-20」 | Instant Quote 実測で金指 Yes + 30° 面取りの追加費は **$0** (2 層/4 層、5/10 枚の全 8 条件で同額)。$20 前後かかるのは金指ではなく ENIG 表面処理 ($20.10 / 5 枚、$23.50 / 10 枚; 120x60mm では $17.40 / $18.30) | §2 |
| 2 | §4「LCSC/JLCPCB にはファミコン用 60P 2.54mm カードエッジは確認できず … 2x30 と一致するピン数は DB 内で確認できず — 未確認」 | 60P 2.54mm の WingTAT ED60BGFBK (C5173310, 在庫 299, $1.30, JLCPCB Extended・Wave Soldering・Economic and Standard) ほか 60P 品が LCSC に 5 件ある。ただしデータシートの推奨カード厚 1.57±0.15mm でファミコンカート (1.2mm) 専用ではない | §4 |
| 3 | §5「日本向け送料・関税: JLCPCB 固有の数値は取得できず — 未確認」「基板価格 … 未確認」 | 実見積と日本向け送料を取得 (§2)。日本向けの配送選択肢は DDP 表記なし (配達時に税を払う方式と推論) | §2 |
| 4 | §1 Inferences「ゴールドフィンガー付き基板は Economic PCBA が使えず Standard PCBA 必須」 | 正しい (Gold Fingers: Yes で Economic ボタンが灰色化することを実画面で確認)。ただし「エッジパッドはあるが Gold Fingers: No (ENIG, 面取りなし)」では見積システム上 Economic が選べた。審査で再分類されるかは未確認 | §1 |
| 5 | §2.2 IS62C256AL-45ULI-TR (C14323) 在庫 2,792 / $4.45 | 2026-11-10 の LCSC 表示は在庫 2,548、$3.9694 (1+, 割引後) / $4.6698 (定価) | §5 調査時の LCSC 検索 |
| 6 | §1「THT は Basic/Extended の装填料なし」 | 公式ページで「THT 部品に装填料がかからない」旨の明記は見つからなかった (ブログ・FAQ は THT を $3.50/注文 + ジョイント単価で説明しているのみ)。**未確認**に格下げすべき | §1 |
| 7 | §3「Raspberry Pi Pico 用ピンソケット」等、秋月表の値 | 本パスで再取得した値 (Pico 2 ¥990 など) と一致。訂正なし | §3 |
| 8 | §1「FAQ が古い可能性」 | FAQ ページは「Last updated on Sep 09, 2026」だが依然 $8.00/$1.50/$0.0017/$3、698 種と記載。ソリューションページの料金表 (2026-11-10 取得) は $8.18/$1.53/$0.0016/$3.07 で、FAQ 本文が更新されていないと判断 (推論) | §1 |

---

## 全体の未確認事項
- エッジパッドあり・金指オプション No の注文が Economic PCBA のまま審査を通るか (JLCPCB への問い合わせが必要)。
- 国内店 (千石電商・マルツ・共立エレショップ・aitendo)、Amazon.co.jp、Yahoo!ショッピング、Digi-Key、Mouser のファミコン 60P コネクタ在庫: いずれも bot 遮断・エラー・0 件で確認できず (試行内容は §4)。
- ドナー機の 60P コネクタを取り外した実例・コネクタのメーカー型番: Web 検索枠を使い切ったため追加調査不可。
- ファミコン専用クローン 60P スロット (AliExpress) の板厚・ピッチ (2.5 / 2.54mm) の実寸。
- 74HC139 / 74HC368 / 74HC574 / CD4021 / 74HCT DIP および DIP 並列 SRAM の国内入手先 (秋月 0 件。他店未確認)。
- 輸入時の通関手数料、HS 8534 等の関税率。
