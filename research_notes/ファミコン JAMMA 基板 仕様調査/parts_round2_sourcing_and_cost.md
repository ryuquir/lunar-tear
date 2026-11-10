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
