# JLCPCB 部品クラス・PCBA 規則の再検証 (第2パス)

全データ取得日: **2026-11-10** (UTC 22 時台)。第1パス (`parts_and_manufacturing.md`) が使った CDFER CSV とは別に、以下のソースで照合した。

| 記号 | ソース | 性格 |
|---|---|---|
| JLCPCB API | `POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList` (jlcpcb.com/parts の検索画面が実際に呼ぶ JSON。Playwright で画面操作時のリクエストを捕捉して確認)。応答の `componentLibraryType` = `base`/`expand`, `preferredComponentFlag` = true/false, `stockCount`, `componentPrices` | JLCPCB 一次データ (ライブ) |
| JLCPCB UI | [jlcpcb.com/parts 検索画面](https://jlcpcb.com/parts/componentSearch?searchTxt=74HC) と [partdetail ページ](https://jlcpcb.com/partdetail/Nexperia-74HC14D653/C5605) (Playwright で描画) | JLCPCB 一次 (表示) |
| LCSC API | `https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=Cxxxx` (lcsc.com 商品ページのデータ源) | LCSC 在庫・価格 (JLCPCB 組立在庫とは別倉庫)。クラス情報は無い |
| jlcsearch | `https://jlcsearch.tscircuit.com/components/list.json?search=Cxxxx` (正しい書式は `search=`。`is_basic`/`is_preferred` を返す) | jlcparts 派生 (独立性は低い) |
| jlcparts | [yaqwsx.github.io/jlcparts/data/cache.zip + cache.z01–z05](https://yaqwsx.github.io/jlcparts/data/cache.zip) (Last-Modified 2026-11-10 11:53 GMT, 内部 sqlite の fetched_at 最大 2026-11-10 11:28 UTC) | CDFER の上流。JLCPCB を巡回取得したもの (独立性は低い) |

注: jlcsearch・jlcparts・CDFER は全て同じ jlcparts 巡回データ系統であり、互いに「独立した第2ソース」ではない。真に独立なのは JLCPCB API/UI (JLCPCB 自身) と LCSC API (在庫・価格のみ)。

## 1. 第1パスの部品クラス主張は正しいか

### Takeaway
第1パスの Basic・Preferred Extended・Extended の各主張 (表の「第1パス主張」列) は、JLCPCB 自身の API でクラスが **全て一致** した (2026-11-10)。誤りはクラスではなく「ライブラリに無い」とした部品の扱いと、21.47727MHz 水晶の見落とし、一部の在庫値にある。

### Cited Findings
- JLCPCB API に `componentLibraryType:"base"` を指定すると total=**351** 件。全 351 件を取得し、第1パスの Basic 主張の受動部品 (抵抗 0603 10k C25804 … 0402 49.9Ω C25120, MLCC 100nF C14663 … 4.7uF C19666, タンタル C7171/C16133 ほか計 50 件) は **全て base** — [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) (2026-11-10)
- Basic 351 件の内訳 (JLCPCB API): 抵抗 182 (0603: 80, 0805: 57, 0402: 30, 1206: 15), MLCC 88, BJT 11, LED 6, ショットキー 6, LDO 6, 水晶 6, フェライト 4, スイッチングダイオード 4, MOSFET 4, 抵抗アレイ 3, オペアンプ 3, TVS/ESD 3, インダクタ 2, RS-485 2, タンタル 2, DC-DC 2, 汎用ダイオード 2, フォトカプラ 2, タクト 2, ブリッジ 1, 基準電圧 1, インバータ 1 (74HC14), シフトレジスタ 1 (74HC595), FET 入力アンプ 1 (TL072), 精密オペアンプ 1 (OP07), ダーリントンアレイ 1 (ULN2003A), コンパレータ 1 (LM393), RS232 1, NOR Flash 1 (W25Q128JVSIQ), ファストリカバリ 1 — [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList)
- 第1パスの抵抗値数 (0402 30, 0603 80, 0805 57, 1206 15) は JLCPCB API と完全一致 — 同上
- jlcparts sqlite の `library_type='base'` も 351 件で、JLCPCB API の 351 件と C 番号集合が完全一致 (差分 0) — [jlcparts cache](https://yaqwsx.github.io/jlcparts/data/cache.zip)
- Basic 351 件は全て SMD (パッケージ名に Plugin/THT 無し; jlcparts の assembly_process は 336 件 SMT, 15 件 null(全てチップ抵抗/コンデンサ))。「Basic の THT 部品は無い」は **確認** — [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList), [jlcparts](https://yaqwsx.github.io/jlcparts/data/cache.zip)
- Preferred は API で `preferredComponentFlag:true` を指定すると total=**1,235** 件 (うち在庫>0 は 1,220)。jlcparts は preferred=1 が 989 件 (API にあって jlcparts に無いものが 246 件)。CDFER の 1,226 件はそのどちらとも一致しない — [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList), [jlcparts](https://yaqwsx.github.io/jlcparts/data/cache.zip)
- **jlcpcb.com UI では「Preferred Extended」という語は表示されず、検索画面の Parts Type フィルタは「Basic / Promotional Extended / Extended / Mechanical Assembly」**。「Promotional Extended」にチェックすると画面は `preferredComponentFlag:true` を API に送り、キーワード 74HC では C5590, C5593, C5613, C5625 の 4 件のみが返る。結果行と partdetail ページのバッジは「Extended」としか表示されない — [JLCPCB 検索画面](https://jlcpcb.com/parts/componentSearch?searchTxt=74HC) (Playwright, 2026-11-10), [partdetail C5590](https://jlcpcb.com/partdetail/Nexperia-74HC04D653/C5590)
- partdetail C5605 のバッジは「Basic」、PCBA Type「Economic and Standard」、Assembly Type「SMT Assembly」 — [partdetail C5605](https://jlcpcb.com/partdetail/Nexperia-74HC14D653/C5605)
- jlcsearch の正しい書式は `components/list.json?search=C5605`。全 C 番号を照会し、クラス (is_basic/is_preferred) は JLCPCB API と全件一致。ただし jlcsearch の `stock` はほとんど null、価格は JLCPCB API と異なる (例 C5605: jlcsearch 1-49 個 $0.1242 vs JLCPCB $0.0763)。一部 C 番号で HTTP 500 が出たが再試行で取得 — [jlcsearch](https://jlcsearch.tscircuit.com/components/list.json?search=C5605)

### 決定版テーブル (2026-11-10 取得; 単価は JLCPCB API の最小数量帯 (1 個~) / LCSC は最小購入数量帯)
「一致ソース」に JLCPCB API と jlcsearch が両方あれば確度=高。jlcsearch を照会しなかった行 (「未照会」) は JLCPCB API のみで確度=中 (Basic/Preferred 行は JLCPCB API の全件リストにも含まれ、jlcparts の base/preferred 集合とも照合済み)。LCSC 在庫は LCSC 倉庫の数で、JLCPCB 組立在庫とは別 (クラス判定には使えない)。

| 部品 | C番号 | パッケージ | 第1パス主張 | JLCPCB API クラス | JLCPCB 在庫 | JLCPCB 単価 $ (1個~) | LCSC 在庫 | LCSC 単価 $ (最小数量) | jlcsearch クラス | 判定クラス | 一致ソース | 確度 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 74HC14 | C5605 | SOIC-14 | Basic | Basic | 315,750 | 0.0763 | 266,475 | 0.077 (≥5) | Basic | Basic | JLCPCB API, jlcsearch, partdetail 表示 Basic | 高 |
| 74HC595 | C5947 | SOIC-16 | Basic | Basic | 404,126 | 0.1018 | 267,210 | 0.1027 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| W25Q128JVSIQ | C97521 | SOIC-8-208mil | Basic | Basic | 83,406 | 2.2597 | 7,092 | 2.281 (≥1) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| AMS1117-3.3 | C6186 | SOT-223 | Basic | Basic | 1,538,727 | 0.1939 | 1,039,775 | 0.1958 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| AMS1117-5.0 | C6187 | SOT-223 | Basic | Basic | 110,165 | 0.2574 | 59,130 | 0.2602 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| XL1509-5.0E1 | C61063 | SOIC-8 | Basic | Basic | 479,258 | 0.2466 | 373,610 | 0.249 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| TPS5430DDAR | C9864 | SOIC-8-EP | Basic | Basic | 307,609 | 0.5302 | 189,819 | 0.5352 (≥1) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| LM358DR2G | C7950 | SOIC-8 | Basic | Basic | 521,642 | 0.054 | 410,180 | 0.0546 (≥10) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| LM324DT | C71035 | SOIC-14 | Basic | Basic | 56,626 | 0.1501 | 22,590 | 0.1512 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| NE5532DR | C7426 | SOIC-8 | Basic | Basic | 268,192 | 0.1069 | 218,535 | 0.1078 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| TL072CDT | C6961 | SO-8 | Basic | Basic | 136,065 | 0.1646 | 76,010 | 0.1656 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| LM393DR2G | C7955 | SOIC-8 | Basic | Basic | 340,506 | 0.0593 | 295,210 | 0.0598 (≥10) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| ULN2003ADR | C7512 | SOIC-16 | Basic | Basic | 368,016 | 0.1444 | 271,880 | 0.1457 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| MMBT3904 | C20526 | SOT-23 | Basic | Basic | 4,313,904 | 0.0103 | 3,854,550 | 0.0104 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| S8050 J3Y | C2146 | SOT-23 | Basic | Basic | 1,309,621 | 0.0142 | 808,450 | 0.0143 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| S8550 | C105432 | SOT-23 | Basic | Basic | 618,390 | 0.0176 | 507,700 | 0.0176 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| 2N7002 | C8545 | SOT-23 | Basic | Basic | 5,867,377 | 0.0154 | 5,297,850 | 0.0155 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| AO3400A | C20917 | SOT-23 | Basic | Basic | 992,725 | 0.0869 | 405,420 | 0.0878 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| AO3401A | C15127 | SOT-23 | Basic | Basic | 1,638,278 | 0.0941 | 1,147,755 | 0.095 (≥5) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| 1N4148W | C81598 | SOD-123 | Basic | Basic | 3,471,971 | 0.0124 | 1,981,000 | 0.0125 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| BAV99 | C2500 | SOT-23 | Basic | Basic | 1,104,445 | 0.0111 | 676,250 | 0.0112 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| SS14 | C2480 | SMA(DO-214AC) | Basic | Basic | 1,610,469 | 0.0192 | 1,103,650 | 0.0193 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| SS34 | C8678 | SMA(DO-214AC) | Basic | Basic | 2,938,768 | 0.0351 | 2,078,460 | 0.0354 (≥20) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| SS54 | C22452 | SMA(DO-214AC) | Basic | Basic | 1,735,691 | 0.0446 | 1,359,300 | 0.045 (≥10) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| SMBJ6.5CA | C7420377 | DO-214AA(SMB) | Basic | Basic | 1,139,871 | 0.0423 | 998,140 | 0.0428 (≥10) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| Tact 4x3 TS-1088 | C720477 | SMD,4x3mm | Basic | Basic | 933,385 | 0.0516 | 675,800 | 0.0521 (≥10) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| Tact 5.1 TS-1187A | C318884 | SMD-4P,5.1x5.1mm | Basic | Basic | 848,757 | 0.0215 | 572,520 | 0.0216 (≥20) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| LED 0603 red KT-0603R | C2286 | 0603 | Basic | Basic | 6,268,215 | 0.0077 | 3,762,000 | 0.0077 (≥100) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| RN 0603x4 1k | C20197 | 0603x4 | Basic | Basic | 542,341 | 0.0095 | 320,550 | 0.0096 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| RN 0603x4 4.7k | C1980 | 0603x4 | Basic | Basic | 1,753,865 | 0.0068 | 1,524,600 | 0.0069 (≥100) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| RN 0603x4 10k | C29718 | 0603x4 | Basic | Basic | 1,132,412 | 0.0075 | 491,300 | 0.0076 (≥100) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| Ferrite GZ1608D601TF | C1002 | 0603 | Basic | Basic | 442,867 | 0.0115 | 取得不可 | - | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| Ferrite BLM18PG121SN1D | C14709 | 0603 | Basic | Basic | 1,859,597 | 0.0124 | 1,212,950 | 0.0125 (≥50) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| Ferrite GZ2012D101TF | C1015 | 0805 | Basic | Basic | 2,331,671 | 0.0254 | 取得不可 | - | 未照会 | Basic | JLCPCB API | 中 |
| Ferrite GZ2012D601TF | C1017 | 0805 | Basic | Basic | 408,808 | 0.02 | 取得不可 | - | 未照会 | Basic | JLCPCB API | 中 |
| 10uH 0603 SDFL1608S100KTF | C1035 | 0603 | Basic | Basic | 404,696 | 0.0279 | 取得不可 | - | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| 10uH 0805 SDFL2012S100KTF | C1046 | 0805 | Basic | Basic | 191,633 | 0.0514 | 取得不可 | - | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| Tant 10uF A | C7171 | CASE-A-3216-18(mm) | Basic | Basic | 888,516 | 0.177 | 414,584 | 0.176 (≥2) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| Tant 100uF B | C16133 | CASE-B-3528-21(mm) | Basic | Basic | 626,406 | 0.2515 | 436,490 | 0.57 (≥2) | Basic | Basic | JLCPCB API, jlcsearch | 高 |
| 12MHz X322512MSB4SI | C9002 | SMD3225-4P | Basic | Basic | 225,205 | 0.0954 | 79,250 | 0.0965 (≥5) | 未照会 | Basic | JLCPCB API | 中 |
| SI2301CDS | C10487 | SOT-23 | (新規) | Basic | 300,062 | 0.091 | 211,070 | 0.0919 (≥10) | 未照会 | Basic | JLCPCB API | 中 |
| D882 | C9634 | SOT-89-3L | Basic | Basic | 543,799 | 0.0637 | 454,450 | 0.0643 (≥10) | 未照会 | Basic | JLCPCB API | 中 |
| 74HC04 | C5590 | SOIC-14 | Preferred | Preferred Extended | 170,290 | 0.1097 | 156,265 | 0.1107 (≥5) | Preferred | Preferred Extended | JLCPCB API, jlcsearch, jlcpcb.com UI「Promotional Extended」フィルタ | 高 |
| 74HC08 | C5593 | SOIC-14 | Preferred | Preferred Extended | 33,153 | 0.0972 | 20,190 | 0.0981 (≥5) | Preferred | Preferred Extended | JLCPCB API, jlcsearch, jlcpcb.com UI「Promotional Extended」フィルタ | 高 |
| 74HC165 | C5613 | SOIC-16 | Preferred | Preferred Extended | 214,412 | 0.1023 | 176,045 | 0.1033 (≥5) | Preferred | Preferred Extended | JLCPCB API, jlcsearch, jlcpcb.com UI「Promotional Extended」フィルタ | 高 |
| 74HC245 | C5625 | SOIC-20-300mil | Preferred | Preferred Extended | 52,801 | 0.2064 | 43,310 | 0.2083 (≥5) | Preferred | Preferred Extended | JLCPCB API, jlcsearch, jlcpcb.com UI「Promotional Extended」フィルタ | 高 |
| SN74LVC4245APWR | C7859 | TSSOP-24 | Preferred | Preferred Extended | 53,630 | 0.5187 | 32,557 | 0.5243 (≥1) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| STM32F103C8T6 | C8734 | LQFP-48(7x7) | Preferred | Preferred Extended | 200,800 | 1.3794 | 4,410 | 1.3924 (≥1) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| STM32F030C8T6 | C23922 | LQFP-48(7x7) | Preferred | Preferred Extended | 91,444 | 0.9998 | 54,026 | 1.0092 (≥1) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| ATMEGA328P-AU | C14877 | TQFP-32(7x7) | Preferred | Preferred Extended | 22,008 | 2.3055 | 668 | 2.3308 (≥1) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| STM8S003F3P6TR | C52717 | TSSOP-20 | (新規) | Preferred Extended | 143,937 | 0.4975 | 59,022 | 0.5022 (≥1) | 未照会 | Preferred Extended | JLCPCB API | 中 |
| MMBT3906 | C7420354 | SOT-23 | Preferred | Preferred Extended | 535,917 | 0.0117 | 514,100 | 0.0119 (≥50) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| BSS138 | C7420339 | SOT-23 | Preferred | Preferred Extended | 690,436 | 0.0194 | 445,250 | 0.0195 (≥50) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| BAT54S | C7420333 | SOT-23 | Preferred | Preferred Extended | 555,145 | 0.0129 | 552,100 | 0.013 (≥50) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| BAT54C | C22466350 | SOT-23 | Preferred | Preferred Extended | 1,086,900 | 0.0167 | 1,068,250 | 0.0168 (≥50) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| CD4051BM96 | C21379 | SOIC-16-150mil | Preferred | Preferred Extended | 71,752 | 0.2676 | 55,995 | 0.2698 (≥5) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| CD4052BM96 | C6521 | SOIC-16 | Preferred | Preferred Extended | 44,990 | 0.2731 | 35,495 | 0.2756 (≥5) | Preferred | Preferred Extended | JLCPCB API, jlcsearch | 高 |
| NE555DR | C7593 | SOIC-8 | (新規) | Preferred Extended | 300,370 | 0.108 | 252,020 | 0.109 (≥5) | 未照会 | Preferred Extended | JLCPCB API | 中 |
| LM2904DR2G | C18229 | SOIC-8 | (新規) | Preferred Extended | 525,127 | 0.0612 | 494,090 | 0.0619 (≥10) | 未照会 | Preferred Extended | JLCPCB API | 中 |
| MCP6002T-I/SN | C7377 | SOIC-8 | (新規) | Preferred Extended | 74,044 | 0.3088 | 40,060 | 0.3121 (≥5) | 未照会 | Preferred Extended | JLCPCB API | 中 |
| RN 0603x4 470R | C25510 | 0603x4 | (新規) | Preferred Extended | 116,840 | 0.0101 | 85,650 | 0.0102 (≥50) | 未照会 | Preferred Extended | JLCPCB API | 中 |
| 11.0592MHz X5032110592MSB2GI | C112574 | SMD5032-2P | (新規) | Preferred Extended | 12,384 | 0.3078 | 10,740 | 0.3108 (≥5) | 未照会 | Preferred Extended | JLCPCB API | 中 |
| ULN2803ADWR | C9683 | SOIC-18-300mil | (新規) | Preferred Extended | 0 | 6.3142 | 0 | 6.3242 (≥1) | 未照会 | Preferred Extended (在庫0=実質入手不可) | JLCPCB API | 中 |
| 74HC00 | C5586 | SOIC-14 | Extended | Extended | 216,856 | 0.1141 | 216,855 | 0.1152 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC32 | C5632 | SOIC-14 | Extended | Extended | 18,912 | 0.1147 | 18,185 | 0.116 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC74 | C27597 | SOIC-14 | Extended | Extended | 73,306 | 0.1213 | 73,160 | 0.1224 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC125 | C5598 | SOIC-14 | Extended | Extended | 127,432 | 0.1331 | 126,820 | 0.1344 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC138 | C5602 | SOIC-16 | Extended | Extended | 13,820 | 0.1409 | 13,820 | 0.1421 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC139 | C512773 | SOP-16 | Extended | Extended | 2,121 | 0.1673 | 2,120 | 0.1691 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC157 | C5609 | SOIC-16 | Extended | Extended | 1,430 | 0.3666 | 1,430 | 0.37 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC164 | C6825 | SOIC-14 | Extended | Extended | 166,658 | 0.0999 | 166,360 | 0.1008 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC244 | C5623 | TSSOP-20 | Extended | Extended | 91,188 | 0.2551 | 90,800 | 0.2575 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC257 | C5627 | SOIC-16 | Extended | Extended | 898 | 0.4091 | 898 | 0.4127 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC273 | C9030 | SO-20-300mil | Extended | Extended | 24,544 | 0.3553 | 24,540 | 0.3586 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC373 | C5636 | SOIC-20-300mil | Extended | Extended | 44,198 | 0.3383 | 44,195 | 0.3415 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC573 | C5944 | TSSOP-20 | Extended | Extended | 98,601 | 0.2371 | 98,600 | 0.2393 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HC574 | C16501 | SOIC-20-300mil | Extended | Extended | 4 | 0.3212 | 0 | 0.3229 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| CD4021BM96 | C134120 | SOIC-16 | Extended | Extended | 9,309 | 0.5793 | 7,711 | 0.5856 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HCT245 | C5979 | SOIC-20-300mil | Extended | Extended | 15,051 | 0.4026 | 15,051 | 0.4064 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HCT244 | C131088 | TSSOP-20 | Extended | Extended | 52,958 | 0.2468 | 52,955 | 0.2491 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74HCT125 | C5962 | SOIC-14 | Extended | Extended | 82,751 | 0.2072 | 82,750 | 0.2094 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74LVC245A | C6082 | TSSOP-20 | Extended | Extended | 229,188 | 0.1889 | 229,185 | 0.1906 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74LVC244A | C6079 | TSSOP-20 | Extended | Extended | 24,825 | 0.1599 | 24,825 | 0.1613 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 74LVC125A | C282343 | DHVQFN-14-EP(2.5x3) | Extended | Extended | 31,507 | 0.1951 | 31,505 | 0.196 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| TXS0108E | C17206 | TSSOP-20 | Extended | Extended | 33,728 | 0.4058 | 32,287 | 0.4094 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| TXB0108 | C53406 | TSSOP-20 | Extended | Extended | 3,882 | 0.6513 | 3,380 | 0.6569 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| IS62C256AL-45ULI-TR | C14323 | SOIC-28-8.4mm | Extended | Extended | 2,548 | 4.6191 | 2,548 | 4.6698 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| IS62C256AL-45TLI | C47143 | TSOPI-28 | (新規) | Extended | 2,021 | 3.3281 | 1,771 | 3.3647 (≥1) | 未照会 | Extended | JLCPCB API | 中 |
| RP2040 | C2040 | LQFN-56(7x7) | Extended | Extended | 84,778 | 1.0865 | 84,880 | 1.0968 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| RP2350A | C42411118 | QFN-60-EP(7x7) | Extended | Extended | 6,268 | 1.2943 | 5,699 | 1.3065 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| USB-C 16P | C393939 | SMD | Extended | Extended | 340,763 | 0.0691 | 329,380 | 0.0628 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| USB-C 6P | C456012 | SMD | Extended | Extended | 985,702 | 0.0378 | 979,450 | 0.0382 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| CH340C | C84681 | SOP-16 | Extended | Extended | 97,259 | 0.5449 | 95,762 | 0.5501 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| CH340G | C14267 | SOP-16 | Extended | Extended | 85,757 | 0.558 | 84,296 | 0.5629 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| USBLC6-2SC6 ST | C7519 | SOT-23-6L | Extended | Extended | 28,135 | 0.1624 | 28,160 | 0.1639 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| USBLC6-2SC6 GOODWORK | C21713975 | SOT-23-6 | Extended | Extended | 32,945 | 0.0392 | 32,600 | 0.0395 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| LM386 | C85119 | SOP-8 | Extended | Extended | 8,208 | 0.108 | 1,310 | 0.1086 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| TDA2822M | C725341 | SOP-8 | Extended | Extended | 5,171 | 0.1321 | 5,170 | 0.1334 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| NS8002 | C189960 | SOP-8 | Extended | Extended | 13,007 | 0.0426 | 13,000 | 0.0431 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| LM4871 | C7494970 | SOP-8 | Extended | Extended | 15,988 | 0.0719 | 15,980 | 0.0726 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| PAM8403 | C17337 | SOIC-16 | Extended | Extended | 3,388 | 0.5056 | 3,388 | 0.51 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| Polyfuse 1812 1.1A | C269134 | 1812 | Extended | Extended | 392,129 | 0.0591 | 385,450 | 0.0598 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| Polyfuse 1206 | C269108 | 1206 | Extended | Extended | 255,577 | 0.03 | 244,800 | 0.0303 (≥20) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| Elec 100uF25V | C970685 | SMD,D6.3xL7.7mm | Extended | Extended | 20,174 | 0.0411 | 17,620 | 0.0414 (≥20) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| DIP SW SMD 4P | C319050 | SMD,P=1.27mm | Extended | Extended | 40,095 | 0.5269 | 39,261 | 0.5316 (≥1) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| DIP SW THT 4P | C99418 | Plugin,P=2.54mm | Extended | Extended | 57,542 | 0.2152 | 56,125 | 0.2178 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| LM311DR | C12597 | SOIC-8 | Extended | Extended | 58,335 | 0.154 | 56,980 | 0.1558 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| LM339DR | C7948 | SOIC-14 | Extended | Extended | 50,734 | 0.1642 | 48,175 | 0.1656 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 21.47727 KUS21477272020 | C368768 | HC-49S | Extended | Extended | 134 | 0.092 | 130 | 0.0921 (≥5) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 21.47727 KUS2147A2030 | C18213345 | HC-49S | Extended | Extended | 190 | 0.0737 | 190 | 0.073 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 21.4772 SWXJHBCVE0 | C22464834 | HC-49S-SMD | Extended | Extended | 83 | 0.1125 | 取得不可 | - | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 21.47727 M49SMD | C7473019 | HC-49S-SMD-2P-Mini | Extended | Extended | 80 | 0.0696 | 80 | 0.0689 (≥10) | Extended | Extended | JLCPCB API, jlcsearch | 高 |
| 21.47727M 20PF 20PPM (SST) | C5289705 | HC-49S-SMD-Mini | (新規) | Extended | 2,648 | 0.0773 | 2,640 | 0.0766 (≥10) | 未照会 | Extended | JLCPCB API | 中 |
| 21.47727 KBD21477272020 | C2835971 | HC-49S-SMD | (新規) | Extended | 169 | 0.0959 | 165 | 0.0961 (≥5) | 未照会 | Extended | JLCPCB API | 中 |
| 21.47727 S47SMD 20pF 50ppm | C5345032 | HC-49S-SMD-2P-Mini | (新規) | Extended | 70 | 0.0696 | 70 | 0.0689 (≥10) | 未照会 | Extended | JLCPCB API | 中 |
| 21.47727 S47SMD 20pF 30ppm | C5345038 | HC-49S-SMD-2P-Mini | (新規) | Extended | 70 | 0.0734 | 70 | 0.0728 (≥10) | 未照会 | Extended | JLCPCB API | 中 |
| 21.47727 S47SMD 13.5pF | C5345042 | HC-49S-SMD-2P-Mini | (新規) | Extended | 55 | 0.0734 | 50 | 0.0728 (≥10) | 未照会 | Extended | JLCPCB API | 中 |
| 21.47727 HY214772M49SOB2T02 | C5265730 | HC-49S | (新規) | Extended | 34 | 0.0639 | 30 | 0.0619 (≥10) | 未照会 | Extended | JLCPCB API | 中 |
| 74HC368D | C5635 | SOIC-16 | 不在 (第1パス) | Extended | 0 | 0.4042 | 0 | 0.3835 (≥1) | 未照会 | Extended (在庫0=実質入手不可) | JLCPCB API | 中 |
| SN74HCU04N | C2867641 | PDIP-14 | 不在 (第1パス) | Extended | 79 | 0.594 | 79 | 0.5963 (≥1) | 未照会 | Extended | JLCPCB API | 中 |
| 74HCU04D | C3272681 | SOIC-14 | 不在 (第1パス) | Extended | 0 | 0.2231 | 取得不可 | - | 未照会 | Extended (在庫0=実質入手不可) | JLCPCB API | 中 |
| HM6116LFP-2 | C9900151975 | SOP-24_L15.7-W7.5-P1.27-LS10.5-BL | 不在 (第1パス) | Extended | 0 | 0.0398 | 取得不可 | - | 未照会 | Extended (在庫0=実質入手不可) | JLCPCB API | 中 |
| LY6264PL-70LL | C261871 | PDIP-28-600mil | 不在 (第1パス) | Extended | 0 | 3.7797 | 0 | 3.5344 (≥1) | 未照会 | Extended (在庫0=実質入手不可) | JLCPCB API | 中 |
| UT6264CPCL-70LL | C32483 | DIP-28-600mil | 不在 (第1パス) | Extended | 0 | 2.1713 | 0 | 2.0469 (≥1) | 未照会 | Extended (在庫0=実質入手不可) | JLCPCB API | 中 |


補足 (表の読み方):
- 「判定クラス」は JLCPCB API の値。jlcsearch は jlcparts 派生なので、「JLCPCB API + jlcsearch」の一致は「JLCPCB 現行値と巡回データの一致」を意味する。
- 在庫は時刻で変動する。LCSC の C1002/C1015/C1017/C1035/C1046/C22464834 などは LCSC API が空応答 (LCSC 側掲載なし/JLCPCB 専用在庫の可能性。推論)。
- ピンヘッダ・IC ソケットの例: C2337 `2.54-1*40PStraight pin` Extended 在庫 74,116 $0.1615; C2895846 PZ254V-11-40P Extended 7,239 $0.2312; DIP-40 IC ソケット C2332 `ICSockets-40P` Extended 9,994 $0.1264。スライドスイッチ: C431540 MSK12C02 (SMD) Extended 177,793 $0.0544; C22355741 SS-12D00-G3 (THT) Extended 11,427 $0.0473 — [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) (2026-11-10)

### Inferences
- 推論: Basic/Preferred の判定は「JLCPCB API のフラグ」で決まり、jlcparts 系データはその写しなので、今回のようにクラスはほぼ一致する。差が出るのは在庫・価格の鮮度と、jlcparts が巡回し損ねた部品 (下記の 21.47727MHz 水晶など) の有無。
- 推論: UI で「Preferred」が「Promotional Extended」と表示され、部品行のバッジが単に「Extended」になっているため、設計者が JLCPCB の画面だけを見ると Preferred を普通の Extended と誤認しうる。BOM 確認は検索画面のフィルタか API フラグで行う必要がある。

### Gaps
- 「Promotional Extended」=旧称「Preferred Extended」であり、Economic で装填料免除という扱いが UI 名変更後も同じであることを明示した JLCPCB の文書は見つけられなかった (FAQ は今も「Preferred Extended」と記載)。同一フラグ (`preferredComponentFlag`) であることは確認済み。名称変更の時期は未確認。

## 2. Basic 352 件 vs FAQ 698 件の食い違い

### Takeaway
現在の JLCPCB 自身のデータでは Basic は **351 件** で、CDFER の 352 件はほぼ正しい。FAQ の「698 kinds of basic components」は、同じ文中の「about 40k+ kinds of components … 300k+ extended」と同じく古い数字が残っているもので、現状を表していない。

### Cited Findings
- FAQ Q5 (ページ表示「Last updated on Sep 09, 2026」) の原文: "Currently, about 40k+ kinds of components are available, including 698 kinds of basic components and 300k+ extended components." — [PCB Assembly FAQs](https://jlcpcb.com/help/article/pcb-assembly-faqs) (2026-11-10 取得)
- 同じ FAQ の Q7: "Preferred Extended Parts … These parts were previously classified as Basic parts, but they have now been categorized as Extended (Preferred) parts." — 同上
- 一方 JLCPCB API の expand は total 7,310,438 件、base 351 件 (2026-11-10)。プロトタイプ組立ページは "720,000+ in-stock components" と記載 — [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList), [PCB Prototype Assembly](https://jlcpcb.com/solutions/pcb-prototype-assembly)
- Basic 351 + Preferred 1,235 = 1,586 件 (JLCPCB API, 2026-11-10)

### Inferences
- 推論: FAQ の 698 は「40k+ 品目 / 300k+ Extended」と同時期 (JLCPCB の部品数がまだ数十万規模だった時期) の記述が更新されずに残ったもの。Q7 が述べるとおり、かつて Basic だった部品の多くが Preferred Extended に移されたため、Basic は 351 件まで減った。698 → 351 の差 347 件が全て Preferred に移ったかどうかは確認できない (Preferred 1,235 件にはもともと Extended だった部品も含まれる可能性)。
- CDFER の 352 と API の 351 の 1 件差は取得時刻の違い (CDFER の最新 fetched_at は 2026-10-28) による入れ替わりと推定 (推論)。

### Gaps
- 再分類が行われた日付・JLCPCB の公式告知: 検索したが見つからず — 未確認。EasyEDA フォーラムに「C169540 が Basic から Extended になった」という利用者の質問はあるが日付・理由不明 — [EasyEDA forum](https://easyeda.com/forum/topic/Additional-Basic-Parts-d5c3a38d74604169a8152ace84086194)

## 3. 第1パスが見落とした Basic / Preferred 部品

### Takeaway
JLCPCB API から Basic 全 351 件と Preferred 全 1,235 件を取得して全件を調べた。結果、この設計に関係する Basic/Preferred の **SRAM・オーディオパワーアンプ・USB コネクタ・DIP/スライドスイッチ・LM393 より速いコンパレータ・21.47727MHz 水晶は存在しない**。新しく見つかった有用な部品は NE555 (C7593)、LM2904 (C18229)、MCP6002 (C7377)、Basic の P-MOS SI2301 (C10487)、0603x4 470Ω 抵抗アレイ (C25510)、11.0592MHz 水晶 (C112574)、STM8S003F3P6 (C52717) など少数。最大の見落としは **Extended の 21.47727MHz 水晶 C5289705 (JLCPCB 在庫 2,648)** で、第1パスの 4 品 (在庫 80–190) よりはるかに在庫が多い。

### Cited Findings (全て [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) 2026-11-10 の全件リストから)
| 分野 | Basic | Preferred Extended | 備考 |
|---|---|---|---|
| 74 系ロジック | 74HC14 C5605, 74HC595 C5947 のみ | 74HC04 C5590, 74HC08 C5593, 74HC165 C5613, 74HC245 C5625, SN74LVC4245A C7859 のみ | 他の 74 系は全て Extended。UI の Promotional Extended フィルタ + キーワード 74HC で 4 件のみと一致 |
| SRAM | なし | なし | Extended の 5V 品で在庫ありは IS62C256AL-45ULI-TR C14323 (2,548) と IS62C256AL-45TLI C47143 (TSOP-28, 2,021, $3.33; 第1パス未記載) |
| MCU | なし | STM32F103C8T6 C8734, STM32F030C8T6 C23922, ATMEGA328P-AU C14877, STM8S003F3P6TR C52717 (143,937, $0.4975), STM8S105K6T6C C8254 (在庫 566), STM32L151C8T6 C9861 (320) | RP2040/RP2350 は Extended |
| オーディオパワーアンプ | なし | なし | Basic にあるのはオペアンプ (LM358, LM324, NE5532, TL072, OP07 C7433) のみ |
| コンパレータ | LM393 C7955 のみ | なし | LM311/LM339 は Extended |
| オペアンプ (新規) | OP07CDR C7433 | LM2904DR2G C18229 (525,127, $0.0612), MCP6002T-I/SN C7377 (74,044, $0.3088), LMV321IDBVR C7972 (83,656, $0.1131) | |
| タイマー | なし | NE555DR C7593 (300,370, $0.108) | |
| 水晶 | 12MHz C9002 (3225), 25MHz C9006, 8MHz C12674 (HC-49S-SMD), 16MHz C13738, 8MHz C115962 (5032), 32.768kHz C32346 | 11.0592MHz C112574 (5032, 12,384, $0.3078) のみ | 21.47727MHz・12MHz 近傍の他品なし |
| USB コネクタ / USB-UART | なし | CP2102-GMR C6568 (49,670, $2.19) のみ (USB-UART) | USB-C コネクタは全て Extended |
| DIP / スライドスイッチ | なし (タクト C720477, C318884 のみ) | なし | |
| 抵抗アレイ (R-2R 用途) | 0603x4 1k C20197, 4.7k C1980, 10k C29718 | 0603x4 470Ω C25510 (116,840, $0.0101), 0402x4 10k C25725 (72,613, $0.0064) | R-2R 専用ネットワークは Basic/Preferred に無し |
| MOSFET (新規) | SI2301CDS-T1-GE3 C10487 (P-ch, 300,062, $0.091) | | 第1パスは AO3401A のみ記載 |
| BJT (新規) | D882 C9634 (SOT-89) ほか | | 第1パス記載済み |
| ダーリントン | ULN2003ADR C7512 | ULN2803ADWR C9683 は Preferred だが **在庫 0** | 第1パスの ULN2803A C845537 は Extended |
| DC-DC (新規 Preferred) | | XL1509-ADJE1 C74192, LM2596SX-5.0 C10002, MC34063A C32078, TPS61040 C7722 | |
| EEPROM | | AT24C256C C6482, M24C02 C7562, M24C64 C79988 | |

21.47727MHz 水晶 (全て Extended, JLCPCB API キーワード 21.47727/21.4772 の在庫>0 全件):
| C番号 | 型番 | メーカー | パッケージ | 負荷容量 | JLCPCB 在庫 | 単価 $ | LCSC 在庫 | 第1パス |
|---|---|---|---|---|---|---|---|---|
| C5289705 | 21.47727M 20PF 20PPM | SST | HC-49S-SMD-Mini | 20pF | 2,648 | 0.0773 | 2,640 | 未記載 |
| C18213345 | KUS2147A2030 | KYX | HC-49S (THT) | 20pF | 190 | 0.0737 | 190 | 記載 |
| C2835971 | KBD21477272020 | KYX | HC-49S-SMD | 20pF | 169 | 0.0959 | 165 | 未記載 |
| C368768 | KUS21477272020 | KYX | HC-49S (THT) | 20pF | 134 | 0.092 | 130 | 記載 |
| C22464834 | SWXJHBCVE0-21.477200 | Starwave | HC-49S-SMD | 20pF (21.4772MHz) | 83 | 0.1125 | 取得不可 | 記載 |
| C7473019 | M49SMD21.47727M20PF10PPM | SST | HC-49S-SMD-2P-Mini | 20pF | 80 | 0.0696 | 80 | 記載 |
| C5345032 | S47SMD21.47727M20PF50R30B3 | SST | HC-49S-SMD-2P-Mini | 20pF | 70 | 0.0696 | 70 | 未記載 |
| C5345038 | S47SMD21.47727M20PF30R30B3 | SST | HC-49S-SMD-2P-Mini | 20pF | 70 | 0.0734 | 70 | 未記載 |
| C5345042 | S47SMD21.47727M13.5PF30R30B3 | SST | HC-49S-SMD-2P-Mini | 13.5pF | 55 | 0.0734 | 50 | 未記載 |
| C5265730 | HY214772M49SOB2T02 | Huiyuan | HC-49S (THT) | 20pF | 34 | 0.0639 | 30 | 未記載 |
- C5289705 の partdetail は「Extended」「SMT Assembly」「PCBA Type Economic and Standard」 — [partdetail C5289705](https://jlcpcb.com/partdetail/C5289705)
- C5289705, C2835971, C5345032, C5265730 などは jlcparts sqlite に行が無い (jlcparts 未収載)。第1パスがこれらを見落とした原因は jlcparts/CDFER の収載漏れと考えられる — [jlcparts](https://yaqwsx.github.io/jlcparts/data/cache.zip)

### Inferences
- 推論: 「Basic のみ」の制約を厳密に守ると、74 系は 74HC14 と 74HC595 だけ、MCU・SRAM・USB・音声アンプ・21.47727MHz 水晶・DIP スイッチ・コネクタ類は全て使えない。Economic PCBA が使えない (ゴールドフィンガーのため Standard 必須、下記 §4) 以上、Preferred の装填料免除の利点も消えるので、Standard では Basic/Preferred/Extended の区別は装填料の面では意味が薄い (Standard は Basic も含め全種類に装填料) — 区別が効くのは「在庫の安定性」だけになる。
- 推論: 21.47727MHz 水晶を PCBA に載せるなら C5289705 (SMD, 在庫 2,648) が唯一の現実的候補。

### Gaps
- C5289705 の等価直列抵抗・データシート値: 未確認。

## 4. PCBA 料金・ゴールドフィンガー規則

### Takeaway
2026-10-22 更新の JLCPCB 料金記事で、Economic: Setup $8.18 / ステンシル $1.53 / Extended 装填料 $3.07、Standard: Setup $25.56 (片面) / ステンシル $8.21 (片面) / 装填料 $1.53「Basic/Extend」を確認。Standard は「all basic and extended components require feeder loading」と明記。Economic はゴールドフィンガー非対応 (JLCPCB と LCSC の能力表で一致)。第1パスの数値は正しいが、FAQ の $8.00 / $1.50 / $3 は旧値。

### Cited Findings
- 料金表 (Last updated on Oct 22, 2026): Setup fee Economic $8.18 / Standard $25.56 Single-side, $51.12 Double-side; Stencil $1.53 / $8.21 Single-side, $16.42 Double-side; SMT Assembly $0.0016/joint (両方, Standard は 50,001 以上で逓減); Manual Assembly $0.0164/joint (1–10,000); Hand-soldering Labor $3.58 per order; "Feeder Loading $3.07 Extend | $1.53 Basic/Extend"; Packing Standard $0.50 + $0.00003 × 面積(cm²); X-ray Inspection 1–10 pcs $1.64/pc …; Handling fee ≥ $14.93; Single board surcharge $0.48; Confirm Parts Placement $0.45; Stencil Storage $4.93 — [PCB Assembly Cost: What Does the Price Include?](https://jlcpcb.com/help/article/pcb-assembly-price) (2026-11-10 取得)
- 同記事の説明: "Extended Components Fee: For Economic PCBA orders, an additional labor fee applies to extended components that require extra feeder setup …" / "Feeder Loading Fee: For Standard PCBA orders, all basic and extended components require feeder loading on pick-and-place machines. An additional labor fee applies." / "X-ray inspection is required for components such as BGA, QFN, and other leadless packages" / Handling Fee: "When both Economic PCBA and Standard PCBA are available for the same order, the total price difference between the two options must be at least $14.93" — 同上
- プロトタイプ組立ページも同値 (Setup $8.18 / $25.56, Stencil $1.53 / $8.21, Feeders Loading fee "$3.07 Extend" / "$1.53 Basic/Extend", Hand-soldering labor **$3.50** per order) と "Preferred extended parts are also fee-free on Economic PCBA" — [PCB Prototype Assembly](https://jlcpcb.com/solutions/pcb-prototype-assembly) (2026-11-10 取得)
- FAQ (Last updated Sep 09, 2026) は Setup $8.00, Stencil $1.50, SMT $0.0017/joint, Hand-soldering $3.5, Manual $0.0173/joint, "we charge $3 per extended component", Preferred は "exempt from the Feeders Loading fee for Economic PCB assembly" — [PCB Assembly FAQs](https://jlcpcb.com/help/article/pcb-assembly-faqs)
- ゴールドフィンガー: 能力表「Gold Fingers/Castellated Holes/Edge Plating — Economic: Not Support / Standard: Support」 — [JLCPCB PCBA Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) と [LCSC PCBA Capabilities](https://www.lcsc.com/pcba/capabilities) (同じ文言, LCSC 側は最小パッケージ Standard 0201 と記載が一部異なる) (共に 2026-11-10 取得)
- JLCPCB 利用者回答 (2025-08-14): "Extended parts incur a loading fee of $3 per part, but neither Basic nor Preferred do." — [JLC Q&A 837](https://jlc3dp.com/help/answers/detail/837-What-is-the-practical-difference-between-Basic-and-Preferred) (利用者投稿、Economic/Standard の区別なし)

### Inferences
- 推論: Standard の $1.53 が「部品種類ごと」か「個数ごと」かは料金表に単位の記載が無い。Economic の Extended 料金が FAQ で "per extended component" (=種類ごと) と説明されていることと同じ表の同じ行に並んでいることから種類ごと と解釈するのが自然だが、文言上は 未確認。
- 推論: RP2040 (LQFN-56), RP2350A (QFN-60), 74LVC125A (DHVQFN-14) をボードに直付けすると X-ray 検査料 (1–10 個で $1.64/個) が加わる。Pico モジュールの手はんだならかからない。
- ハンドソルダ人件費は記事 $3.58 とプロトタイプページ $3.50 で不一致 (どちらも JLCPCB 公式)。

### Gaps
- Standard の装填料が部品種類単位であることの明文: 未確認 (Instant Quote 画面での試算が必要)。

## 既存ノートへの訂正

| # | 第1パスの記述 (parts_and_manufacturing.md) | 再検証結果 | 出典 |
|---|---|---|---|
| 1 | §2.1 / §2 Gaps「74HC368, 74HCU04: DB に該当品なし」 | **誤り**。JLCPCB ライブラリに掲載あり (全て Extended)。74HC368D C5635 (在庫 0, $0.4042)、ほか 74HC368 系 24 件は全て在庫 0。74HCU04 系 60 件中、在庫ありは SN74HCU04N C2867641 (PDIP-14, Wave Soldering, 在庫 79, $0.594) のみ。正しくは「掲載はあるが Extended で実質在庫なし」 | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList), [partdetail C2867641](https://jlcpcb.com/partdetail/C2867641) |
| 2 | §2.2「6116/6264/AS6C62256/CY62256 は DB 該当なし」 | **誤り (表現)**。掲載はある: HM6116LFP-2 C9900151975, LY6264PL-70LL C261871, UT6264CPCL-70LL C32483, AS6C62256 系 16 件, CY62256 系 91 件 — いずれも Extended で **在庫 0**。結論 (使えない) は変わらない | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) |
| 3 | §2.7「21.47727MHz 水晶は LCSC に 4 種、在庫 80–190」 | **誤り**。在庫ありは 10 種。最大は C5289705 (SST, HC-49S-SMD-Mini, 20pF, JLCPCB 在庫 2,648, $0.0773)。全て Extended なのは正しい | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList), [partdetail C5289705](https://jlcpcb.com/partdetail/C5289705) |
| 4 | §2.2「5V 動作の実質候補は IS62C256AL のみ (C14323)」 | 補足: 同型 TSOP-28 版 IS62C256AL-45TLI C47143 (在庫 2,021, $3.33) もある。IS61LV256AL C412837 の在庫は 18 ではなく 2,358 | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) |
| 5 | §2.1 74HC574 C16501 在庫 41,694 | 2026-11-10 の JLCPCB 在庫は **4** (LCSC 0)。実質入手不可 | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList), [LCSC API](https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C16501) |
| 6 | §2.4 74HC4051 C9386 在庫 23,555 | JLCPCB 在庫 **0** | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) |
| 7 | §1 「Preferred Extended=1226 件」 | JLCPCB API では 1,235 件 (jlcparts は 989 件)。CDFER 値は JLCPCB 現行値と一致しない | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) |
| 8 | §1 / §2「Basic 判定は CDFER の library_type による。JLCPCB サイトでの確認はしていない」 | JLCPCB API で全件確認済み: Basic 351 件。クラス判定は全て一致 | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) |
| 9 | (用語) 「Preferred Extended」 | 現行 jlcpcb.com UI ではフィルタ名「Promotional Extended」、部品行・詳細ページのバッジは「Extended」とのみ表示。FAQ は「Preferred Extended」のまま | [検索画面](https://jlcpcb.com/parts/componentSearch?searchTxt=74HC) |
| 10 | §2.4 ULN2803A は C845537 (ext) のみ記載 | ULN2803ADWR C9683 は Preferred だが在庫 0。C845537 は Extended (在庫 180,482) | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) |
| 11 | §1 「Basic の THT 品目は 0」「FAQ は 698 種」 | THT 0 は確認。698 は FAQ の古い記述 (同じ文が "40k+ kinds" "300k+ extended" と記載) | [FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs) |
| 12 | §6 手はんだ人件費「$3.5」 | 料金記事 (2026-10-22 更新) は $3.58、プロトタイプページは $3.50 と公式内で不一致 | [料金記事](https://jlcpcb.com/help/article/pcb-assembly-price) |
| 13 | 在庫・価格全般 (DB 2026-10-28 頃) | 2026-11-10 の値で上表に更新。例: 74HC14 C5605 在庫 315,750 $0.0763, W25Q128JVSIQ C97521 83,416 $2.26, AMS1117-3.3 C6186 1,538,727 $0.1939 | [JLCPCB API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList) |

確認された主張 (変更不要): Basic 主張 (74HC14, 74HC595, W25Q128JVSIQ, AMS1117-3.3/5.0, XL1509-5.0, TPS5430, LM358, LM324, NE5532, TL072, LM393, ULN2003A, MMBT3904, S8050, S8550, 2N7002, AO3400A, AO3401A, 1N4148W, BAV99, SS14/34/54, SMBJ6.5CA, タクト 2 種, LED, 0603x4 抵抗アレイ 1k/4.7k/10k, フェライト 4 種, 10µH 2 種, タンタル 10µF/100µF, ほか) と受動部品 50 件; Preferred 主張 (74HC04/08/165/245, SN74LVC4245A, STM32F103C8T6, MMBT3906, BSS138, BAT54S/C, CD4051/4052 ほか); Extended 主張 (表参照); Economic のゴールドフィンガー非対応; Economic/Standard の各料金。

## まだ未確認のこと
- 「Promotional Extended」への名称変更の時期と、それが旧「Preferred Extended」と同一の料金扱いであることの JLCPCB による明文 (フラグが同一であることは確認済み)。
- Basic 698 → 351 への再分類の日付・告知。
- Standard の装填料 $1.53 が部品種類単位か (表に単位なし)。
- jlcsearch の在庫値 (ほぼ null) と価格の更新時期。
