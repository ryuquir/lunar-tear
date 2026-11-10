# ファミコン JAMMA 基板: 部品調達・製造制約の調査ノート (作業中・随時更新)

データ日付: 2026-11-10 取得。CDFER/jlcpcb-parts-database (yaqwsx/jlcparts 由来, 2026-11-10 05:55 GMT 更新) の CSV/SQLite をローカルで照会。DB 内最新 fetched_at は 2026-10-28 (在庫・価格は数日~2週間古い可能性)。

## 1. JLCPCB クラス (Basic / Preferred / Extended) の実データ

### Takeaway
2026-11-10 時点の公開 DB では Basic は 352 品目のみ (抵抗185, コンデンサ90, 他77)。Basic に含まれるロジック IC は 74HC14 (C5605) と 74HC595 (C5947) の 2 種だけ。スルーホール(THT) の Basic 部品は存在しない。

### Cited Findings
- Basic=352件 (library_type=base)、Preferred Extended=1226件 (expand かつ preferred=1) — [CDFER CSV](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv) をローカル集計 (2026-11-10 取得)
- DB 全体 511,178 品目 (在庫5個以上) — [CDFER SQLite](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components.sqlite3) (Last-Modified 2026-11-10 05:55 GMT)
- Basic の THT 品目は 0 (CSV の assembly_process=THT 表示は GBJ ブリッジ等 Preferred のみで、SMD ダイオードにも誤付与があり信頼できない)

- JLCPCB 公式 FAQ は Basic 部品を 698 種と記載し、Extended 追加料金を $3、Setup $8.00、ステンシル $1.50 と表記 (古い数値の可能性)。DB の Basic は 352 件で食い違う。2026-10 の公式ブログは $8.18 / $1.53 / $3.07 — [PCA FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs) vs [公式ブログ 2026-10-13](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- Basic = P&P 機に常設で装填済み、追加料金なし。Extended = オペレータがフィーダ手装填、1 種類ごとに追加。Preferred Extended = 旧 Basic、Economic PCBA では装填料免除 — [FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs), [Prototype Assembly 価格表](https://jlcpcb.com/solutions/pcb-prototype-assembly)
- 料金表 (2026-10-09 時点, USD): Economic = Setup $8.18, ステンシル $1.53, 装填料 $3.07/Extended 種類 (Basic・Preferred は無料), SMT $0.0016/ジョイント。Standard = Setup $25.56 (片面)/$51.12 (両面), ステンシル $8.21 (片面)/$16.42 (両面), 装填料 $1.53/種類 (Basic も Extended も課金), 手はんだ/THT 人件費 $3.50-3.58/注文 — [公式ブログ](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype), [価格表](https://jlcpcb.com/solutions/pcb-prototype-assembly)
- Economic の制限: 片面実装のみ、層数 2/4/6、厚み 0.8-1.6mm、数量 2-50 枚 (組合せにより 30 枚)、単板 10x10~470x500mm、パネルは 250x250 以下でミシン目のみ(Vカット不可)、最小 0402、「ゴールドフィンガー・キャスタレーションホールは非対応」 — [PCBA 能力表](https://jlcpcb.com/capabilities/pcb-assembly-capabilities), [公式ブログ](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- Standard の条件: 両面実装、Vカット、ゴールドフィンガー、50 枚超、層数 1-32 に対応。単板 70x70~460x500mm — [PCBA 能力表](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
- 部品ライブラリで "wave soldering" と表示される部品は人手実装。THT は Basic/Extended の装填料なし、1 ジョイント約 $0.0164-0.0173 + 注文あたり手はんだ人件費 $3.5-3.58 — [FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs), [公式ブログ](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- 部品配置確認 (Confirm Parts Placement) $0.45; ステンシル保管 (Standard) $4.93/3か月; Standard 最低実装費 $0.48/枚 — [公式ブログ](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- ICソケットに IC を載せる "stacked parts" は個別対応で追加人件費の可能性 — [PCBA 能力表](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
- 納期: Economic 1-3 日、Standard 4 日以上。未在庫部品は 9-15 日で調達 — [価格表](https://jlcpcb.com/solutions/pcb-prototype-assembly)
- Basic の検証方法: jlcsearch/jlcparts/CDFER CSV の library_type=base (preferred=0)。本ノートは CDFER CSV の library_type を使用 — [CDFER README](https://raw.githubusercontent.com/CDFER/jlcpcb-parts-database/main/README.md)

### Inferences
- ゴールドフィンガー付き基板は Economic PCBA が使えず Standard PCBA 必須。Standard では Basic 部品にも $1.53/種類の装填料がかかるため、「部品種類の最小化」が直接コストに効く。ゴールドフィンガーの無い基板に分けて Economic で組む案 (JAMMA コネクタは別基板/エッジコネクタ)もあるが本題外。
- 150x200mm は Economic 上限 (470x500) 内でも、Standard (460x500) 内。

### Gaps
- Standard PCBA の部品ごとの追加人件費、THT 部品 (ソケット等) を JLCPCB に実装させる場合の個別単価: 未確認。
- JLCPCB 公式ブログと FAQ の数値 (価格 $3 vs $3.07, 698 種 vs 352 種) は異なる。公式の最新は Instant Quote 画面で確認が必要。

## 2. 機能別 JLCPCB 部品候補 (データ: CDFER DB 2026-11-10 公開版を SQLite 照会。価格は最小数量帯の単価 USD, 在庫は DB 取得時点)

出典(全表共通): [CDFER CSV(Basic/Preferred)](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv), [CDFER SQLite(全在庫品)](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components.sqlite3)。クラス欄 BASIC=Basic, PREF=Preferred Extended, ext=Extended。

### 2.1 5V ロジック: Basic は 74HC14 と 74HC595 のみ

| 機能 | LCSC | 型番 | パッケージ | クラス | 在庫 | 単価$ |
|---|---|---|---|---|---|---|
| 74HC14 | C5605 | 74HC14D,653 | SOIC-14 | BASIC | 132,292 | 0.083 |
| 74HC595 | C5947 | 74HC595D,118 | SOIC-16 | BASIC | 283,069 | 0.114 |
| 74HC04 | C5590 | 74HC04D,653 | SOIC-14 | PREF | 30,108 | 0.130 |
| 74HC08 | C5593 | 74HC08D,653 | SOIC-14 | PREF | 55,278 | 0.126 |
| 74HC165 | C5613 | 74HC165D,653 | SOIC-16 | PREF | 249,930 | 0.111 |
| 74HC245 | C5625 | 74HC245D,653 | SOIC-20 | PREF | 51,602 | 0.220 |
| 74HC00 | C5586 | 74HC00D,653 | SOIC-14 | ext | 43,080 | 0.151 |
| 74HC32 | C5632 | 74HC32D,653 | SOIC-14 | ext | 11,237 | 0.120 |
| 74HC74 | C27597 | 74HC74D,653 | SOIC-14 | ext | 28,070 | 0.168 |
| 74HC125 | C5598 | 74HC125D,653 | SOIC-14 | ext | 46,542 | 0.143 |
| 74HC126 | C5600 | 74HC126D,653 | SOIC-14 | ext | 2,368 | 0.259 |
| 74HC138 | C5602 | 74HC138D,653 | SOIC-16 | ext | 18,485 | 0.200 |
| 74HC139 | C512773 | 74HC139M/TR | SOP-16 | ext | 2,236 | 0.174 |
| 74HC157 | C5609 | 74HC157D,653 | SOIC-16 | ext | 2,134 | 0.359 |
| 74HC164 | C6825 | 74HC164D,653 | SOIC-14 | ext | 146,425 | 0.109 |
| 74HC244 | C5623 | 74HC244PW,118 | TSSOP-20 | ext | 48,675 | 0.274 |
| 74HC257 | C5627 | 74HC257D,653 | SOIC-16 | ext | 1,198 | 0.416 |
| 74HC273 | C9030 | 74HC273D,653 | SO-20 | ext | 24,944 | 0.357 |
| 74HC373 | C5636 | 74HC373D,653 | SOIC-20 | ext | 45,633 | 0.339 |
| 74HC573 | C5944 | 74HC573PW,118 | TSSOP-20 | ext | 57,196 | 0.261 |
| 74HC574 | C16501 | 74HC574D,653 | SOIC-20 | ext | 41,694 | 0.322 |
| CD4021 | C134120 | CD4021BM96 | SOIC-16 | ext | 10,893 | 0.580 |
| 74HCT245 | C5979 | 74HCT245D,653 | SOIC-20 | ext | 17,015 | 0.403 |
| 74HCT244 | C131088 | 74HCT244PW,118 | TSSOP-20 | ext | 24,222 | 0.276 |
| 74HCT125 | C5962 | 74HCT125D,653 | SOIC-14 | ext | 86,201 | 0.210 |
| 74LVC245 | C6082 | 74LVC245APW,118 | TSSOP-20 | ext | 239,648 | 0.206 |
| 74LVC244 | C6079 | 74LVC244APW,118 | TSSOP-20 | ext | 26,424 | 0.222 |
| 74LVC125 | C282343 | 74LVC125ABQ,115 | DHVQFN-14 | ext | 32,032 | 0.195 |
| SN74LVC4245A (8bit 3.3/5V 変換) | C7859 | SN74LVC4245APWR | TSSOP-24 | PREF | 112,801 | 0.498 |
| TXS0108E | C17206 | TXS0108EPWR | TSSOP-20 | ext | 42,633 | 0.454 |
| TXB0108 | C53406 | TXB0108PWR | TSSOP-20 | ext | 29,616 | 0.652 |

- 74HC368, 74HCU04: DB に該当品なし (在庫5個未満または未収載) — 未確認扱い。
- 全て上記 DB 行から。他パッケージ違い・互換品 (UMW/HX 等の -JSM 品) は多数あるが全て Extended。
- 含意: 「Basic のみ」の制約下では 74HC14/74HC595 以外のロジックは使えない。CPLD/FPGA 等でも Basic はゼロ。Preferred Extended (08/04/165/245/LVC4245) は Extended の部品ごと追加料金なし(下記 §1 JLCPCB 規則で確認)。

### 2.2 5V パラレル SRAM (2KB 級)
| LCSC | 型番 | パッケージ | クラス | 在庫 | 単価$ |
|---|---|---|---|---|---|
| C14323 | IS62C256AL-45ULI-TR (32Kx8 5V) | SOIC-28 8.4mm | ext | 2,792 | 4.45 |
| C1136813 | R1LP5256ESP-5SI#B1 | SOP-28 | ext | 18 | 3.09 |
| C412837 | IS61LV256AL-10TLI (3.3V) | TSOP-28 | ext | 18 | 3.87 |
- 6116/6264/AS6C62256/CY62256 は DB 該当なし。Basic の SRAM は無い。5V 動作の実質候補は IS62C256AL のみ(在庫 2,792 と少なめ)。シリアル 23K256 (C136317, SOIC-8, 3.3V) は Famicom バスの速度に合わない。
- 推論: 2KB 級 RAM は MCU 内蔵 RAM/FPGA で代替するか、ドナー機の PPU/CPU 周辺の既存 RAM を再利用するか、IS62C256 を Extended として許容する設計判断が必要。

### 2.3 MCU・周辺
| 機能 | LCSC | 型番 | パッケージ | クラス | 在庫 | 単価$ |
|---|---|---|---|---|---|---|
| RP2040 | C2040 | RP2040 | LQFN-56 | ext | 53,168 | 1.00 |
| RP2350A | C42411118 | RP2350A | QFN-60 | ext | 6,849 | 1.30 |
| STM32F103C8T6 | C8734 | STM32F103C8T6 | LQFP-48 | PREF | 238,965 | 1.53 |
| STM32F030C8T6 | C23922 | STM32F030C8T6 | LQFP-48 | PREF | 74,729 | 1.18 |
| ATmega328P | C14877 | ATMEGA328P-AU | TQFP-32 | PREF | 47,571 | 2.31 |
| GD32F103C8T6 | C77994 | GD32F103C8T6 | LQFP-48 | ext | 12,863 | 1.47 |
| ATmega32U4 | C44854 | ATMEGA32U4-AU | TQFP-44 | ext | 3,633 | 6.93 |
| ESP32-WROOM-32E-N4 | C701341 | ESP32-WROOM-32E-N4 | module | ext | 26,423 | 3.77 |
| W25Q128JV | C97521 | W25Q128JVSIQ | SOIC-8 208mil | BASIC | 66,921 | 2.57 |
| W25Q16JV | C131025 | W25Q16JVSSIQ | SOIC-8 208mil | ext | 3,665 | 1.26 |
| W25Q32JV | C179173 | W25Q32JVSSIQ | SOIC-8 208mil | ext | 12,933 | 1.70 |
| CH340C | C84681 | CH340C | SOP-16 | ext | 124,020 | 0.546 |
| CH340G | C14267 | CH340G | SOP-16 | ext | 48,905 | 0.539 |
| USB ESD | C7519 | USBLC6-2SC6 | SOT-23-6 | ext | 32,269 | 0.178 |
| USB ESD (安価) | C21713975 | USBLC6-2SC6 | SOT-23-6 | ext | 25,652 | 0.039 |
| USB-C 16P | C393939 | TYPE-C16PIN | SMD | ext | 351,293 | 0.069 |
| USB-C 6P(電源のみ) | C456012 | TYPE-C 6P | SMD | ext | 721,375 | 0.039 |
- Basic の MCU は無い。Basic の Flash は W25Q128JVSIQ(16MB; 2.57 ドルと高い) のみ。RP2040 は Basic ではなく Extended。→ ボード上に RP2040 を直付けせず、Pico/Pico 2 をソケット実装(手はんだ)にするのが「Basic のみ」要件に合致。
- RP2350B (C42415655), CH32V (C7570477 他), ESP32-S3 は在庫あるが全て ext/未収載。

### 2.4 電源・オーディオ・アナログ
| 機能 | LCSC | 型番 | パッケージ | クラス | 在庫 | 単価$ |
|---|---|---|---|---|---|---|
| 3.3V LDO | C6186 | AMS1117-3.3 | SOT-223 | BASIC | 1,139,974 | 0.209 |
| 5V LDO | C6187 | AMS1117-5.0 | SOT-223 | BASIC | 70,633 | 0.256 |
| 3.3V LDO 小型 | C5446 | XC6206P332MR-G | SOT-23 | BASIC | 405,951 | 0.144 |
| 3.3V LDO | C14289 | HT7533-1 | SOT-89 | BASIC | 125,058 | 0.158 |
| 5V 78L05 | C71136 | 78L05G-AB3-R | SOT-89 | BASIC | 197,960 | 0.090 |
| 5V 78M05 | C58069 | L78M05ABDT-TR | DPAK | BASIC | 140,157 | 0.206 |
| Buck 5V 固定 | C61063 | XL1509-5.0E1 (2A, 最大40V入力) | SOIC-8 | BASIC | 481,694 | 0.246 |
| Buck 可変 | C9864 | TPS5430DDAR (3A) | SOIC-8-EP | BASIC | 284,077 | 0.593 |
| Buck 可変 | C9865 | TPS54331DR | SOIC-8 | PREF | 348,405 | 0.333 |
| 7805 TO-220 | C347289 | L7805CV(UMW) | TO-220 | ext(THT) | 127,112 | 0.206 |
| 12V 78L12 | C915681 | L78L12ABUTR | SOT-89 | ext | 99,813 | 0.122 |
| ポリヒューズ 1812 1.1A | C269134 | SMD1812B110TF/33 | 1812 | ext | 404,195 | 0.062 |
| ポリヒューズ 1206 | C269108 | SMD1206B010TF | 1206 | ext | 258,714 | 0.031 |
| 逆接/整流 Schottky | C8678 / C22452 / C2480 | SS34 / SS54 / SS14 | SMA | BASIC | 400万 / 218万 / 132万 | 0.035 / 0.045 / 0.019 |
| 整流 | C95872 | M7 (1N4007 相当) | SMA | BASIC | 4,659,401 | 0.010 |
| P-MOS 逆接保護 | C15127 | AO3401A | SOT-23 | BASIC | 587,250 | 0.103 |
| N-MOS | C20917 / C8545 | AO3400A / 2N7002 | SOT-23 | BASIC | 757,862 / 1,830,508 | 0.090 / 0.018 |
| LM358 | C7950 | LM358DR2G | SOIC-8 | BASIC | 716,041 | 0.055 |
| LM324 | C71035 | LM324DT | SOIC-14 | BASIC | 129,724 | 0.167 |
| NE5532 | C7426 | NE5532DR | SOIC-8 | BASIC | 285,263 | 0.108 |
| TL072 | C6961 | TL072CDT | SO-8 | BASIC | 64,077 | 0.163 |
| LM393 | C7955 | LM393DR2G | SOIC-8 | BASIC | 212,935 | 0.067 |
| LM339 | C7948 | LM339DR | SOIC-14 | ext | 40,667 | 0.161 |
| LMV358 | C63813 | LMV358IDR | SOIC-8 | ext | 184,119 | 0.223 |
| 高速コンパレータ LM311 | C12597 | LM311DR | SOIC-8 | ext | 146,417 | 0.172 |
| CD4051 | C21379 | CD4051BM96 | SOIC-16 | PREF | 122,728 | 0.260 |
| CD4052 | C6521 | CD4052BM96 | SOIC-16 | PREF | 100,622 | 0.281 |
| CD4053 | C6742 | CD4053BM96 | SOIC-16 | ext | 25,113 | 0.384 |
| 74HC4051 | C9386 | 74HC4051D,653 | SOIC-16 | ext | 23,555 | 0.218 |
| 74HC4053 | C5647 | 74HC4053D,653 | SOIC-16 | ext | 39,335 | 0.201 |
| ULN2003A | C7512 | ULN2003ADR | SOIC-16 | BASIC | 365,093 | 0.149 |
| ULN2803A | C845537 | ULN2803A | SOP-18 | ext | 295,948 | 0.211 |
| 8Ω アンプ LM386 | C85119 | LM386G-S08-R | SOP-8 | ext | 8,760 | 0.108 |
| TDA2822 | C725341 | TDA2822M/TR | SOP-8 | ext | 5,533 | 0.135 |
| NS8002 (8002 系 BTL) | C189960 | NS8002 | SOP-8 | ext | 20,089 | 0.042 |
| LM4871 | C7494970 | LM4871 | SOP-8 | ext | 28,002 | 0.070 |
| NS4150B (Class-D 3W) | C189961 | NS4150B | MSOP-8 | ext | 123,541 | 0.154 |
| PAM8403 | C17337 | PAM8403DR-H | SOIC-16 | ext | 4,110 | 0.449 |
| PAM8302 | C113367 | PAM8302AASCR | MSOP-8 | ext | 13,083 | 0.322 |
- Basic のスピーカーアンプは無い(Audio Amplifiers 区分に Basic ゼロ)。Basic の範囲で 8Ω スピーカーを駆動するなら、NE5532/TL072/LM358 + 既存 Basic のトランジスタ(S8050/S8550/D882 SOT-89, 下記)でディスクリートのプッシュプルを組むのが唯一の道。D882 (C9634, SOT-89, 3A) は Basic。
- 12V 入力から 5V を作る場合 XL1509-5.0E1 (2A 固定 5V, 150kHz, Basic) が候補。入力耐圧は DB 属性に無く 未確認 (データシート要確認)。

### 2.5 ディスクリート・保護
| 機能 | LCSC | 型番 | クラス | 在庫 | 単価$ |
|---|---|---|---|---|---|
| MMBT3904 | C20526 | MMBT3904 (SOT-23) | BASIC | 576,019 | 0.012 |
| MMBT3906 | C7420354 | MMBT3906 | PREF | 780,352 | 0.012 |
| S8050 / SS8050 | C2146 / C2150 | S8050 J3Y / SS8050 | BASIC | 1,462,365 / 1,923,984 | 0.015 |
| S8550 / SS8550 | C105432 / C8542 | S8550 / SS8550 Y2 | BASIC | 217,855 / 1,042,151 | 0.017 / 0.016 |
| S9012 / S9013 | C8543 / C6749 | | BASIC | 233,418 / 893,713 | 0.019 / 0.015 |
| MMBT2222A | C8512 | | BASIC | 589,927 | 0.018 |
| MMBT5551 / 5401 | C2145 / C8326 | | BASIC | 1.78M / 582k | 0.015 |
| BSS138 | C7420339 | BSS138 | PREF | 126,833 | 0.027 |
| 1N4148W | C81598 | SOD-123 | BASIC | 4,633,707 | 0.012 |
| 1N4148WS | C2128 | SOD-323 | BASIC | 2,567,411 | 0.015 |
| BAV99 / BAV70 | C2500 / C68978 | SOT-23 | BASIC | 1.13M / 342k | 0.012 / 0.018 |
| BAT54S / BAT54C | C7420333 / C22466350 | SOT-23 | PREF | 1.07M / 732k | 0.014 / 0.017 |
| BAT54W | C7502705 | SOD-123 | PREF | 159,728 | - |
| 1N5819WS / B5819W | C191023 / C8598 | SOD-323/123 | BASIC | 4.29M / 385k | 0.014 / 0.028 |
| ツェナー BZT52C5V1/5V6 | C19077401 / C19077402 | SOD-123 | PREF | 2.3M / 2.97M | 0.017 |
| TVS 双方向 | C7420377 (SMBJ6.5CA) / C78395 (P6SMB6.8CA) | SMB | BASIC | 818k / 148k | 0.039 / 0.056 |
| TVS | C19077561 (SMBJ6.0CA), C19077524 (SMAJ5.0CA) | SMB/SMA | PREF | 1.48M / 746k | 0.049 / 0.038 |
| ESD 3線 | C32677 | PSM712-LF-T7 | BASIC | 188,977 | 0.326 |
| ESD アレイ SRV05-4 | C558418 | SRV05-4 | ext | 362,536 | 0.027 |
| ESD (1チャネル) | C668924 | ESD5V0D3-TP SOD-323 | ext | 67,335 | 0.028 |
| 光アイソレータ | C109227 | LTV-817S-TA1-C | BASIC | 214,560 | 0.079 |
| フェライトビーズ | C1002 / C14709 (0603), C1015 / C1017 (0805) | GZ1608D601TF / BLM18PG121SN1D / GZ2012D101TF / GZ2012D601TF | BASIC | 717k / 1.29M / 2.26M / 691k | 0.012-0.027 |
| インダクタ 10µH | C1035 (0603) / C1046 (0805) | SDFL1608S100KTF / SDFL2012S100KTF | BASIC | 759k / 286k | 0.028 / 0.052 |
| 抵抗アレイ 0603x4 | C29718 (10k) / C1980 (4.7k) / C20197 (1k) | 4D03WGJ0103T5E 他 | BASIC | 1.98M / 1.92M / 338k | 0.0075 / 0.0068 / 0.017 |

### 2.6 受動部品 (Basic の値一覧)
- 抵抗 (全て Basic, 1% 系 / 在庫は百万個単位): 0402 は 30 値、0603 は 80 値、0805 は 57 値、1206 は 15 値。主要値 LCSC: 0603 → 10k C25804, 1k C21190, 100Ω C22775, 4.7k C23162, 5.1k C23186, 75Ω C4275 (映像 75Ω 終端), 220Ω C22962, 330Ω C23138, 470Ω C23179, 2.2k C4190, 1.5k C22843, 22k C31850, 100k C25803, 47k C25819, 0Ω C21189。0805 → 10k C17414, 1k C17513, 100Ω C17408, 4.7k C17673, 75Ω は 0805 Basic に無し(0603 C4275 を使用)。0402 → 10k C25744, 1k C11702, 100Ω C25076, 4.7k C25900, 49.9Ω C25120。
- 注: 47Ω は 0603 C23182, 0805 C17714 (Basic)。
- 積層セラミック (Basic): 100nF 0603 C14663 (50V X7R, 在庫 5,035万), 0402 C1525 / C307331, 0805 C28233 / C49678; 1uF 0603 C15849, 10uF 0603 C19702 / C96446, 22uF 0603 C59461, 0805 22uF C45783, 47uF 0805 C16780, 1206 100uF C15008; 10pF 0603 C1634, 22pF 0603 C1653, 33pF C1663, 100pF C14858, 1nF C1588, 10nF C57112, 47nF C1622, 220nF C21120, 2.2uF C23630, 4.7uF C19666。
- タンタル (Basic): C7171 10uF 3216-A, C16133 100uF 3528-B。
- 電解コンデンサ: Basic なし。SMD アルミ電解 (例 C970685 100uF25V, C970686 100uF35V, C976030 470uF35V, C970714 1000uF16V) は全て ext。→ 大容量は手はんだ(秋月)か 1206 100uF 積層 (C15008) / タンタル 100uF (C16133) で代替。
- 注: MLCC DC バイアス劣化は未検討。

### 2.7 水晶・発振器 (21.47727MHz 含む)
| LCSC | 型番 | パッケージ | クラス | 在庫 | 単価$ |
|---|---|---|---|---|---|
| C368768 | KUS21477272020 | HC-49S (THT) | ext | 144 | 0.092 |
| C18213345 | KUS2147A2030 | HC-49S (THT) | ext | 190 | 0.074 |
| C22464834 | SWXJHBCVE0-21.477200 | HC-49S-SMD | ext | 88 | 0.113 |
| C7473019 | M49SMD21.47727M20PF10PPM | HC-49S-SMD | ext | 80 | 0.070 |
- 21.47727MHz 水晶は LCSC に 4 種あるが全て Extended で在庫が 80-190 個と少ない。Basic の水晶は 12MHz C9002 (X322512MSB4SI, 3225, 負荷 20pF), 25MHz C9006 (12pF), 16MHz C13738 (9pF), 8MHz C12674 (HC-49S SMD) / C115962 (5032), 32.768kHz C32346。21.47727 の発振器(オシレータ)は DB 該当なし。
- 結論: 21.47727MHz は Basic で用意不可。ドナー Famicom から基板上水晶を流用するか、Pico の PIO で生成(RP2040 は 12MHz 水晶→PLL)も検討余地。Akizuki の取り扱いは §4 参照。

### 2.8 スイッチ・LED・コネクタ
| 機能 | LCSC | 型番 | クラス | 在庫 | 単価$ |
|---|---|---|---|---|---|
| タクト SMD 4x3 | C720477 | TS-1088-AR02016 | BASIC | 561,602 | 0.053 |
| タクト SMD 5.1x5.1 | C318884 | TS-1187A-B-A-B | BASIC | 296,384 | 0.021 |
| LED 0603 赤/白 | C2286 / C2290 | KT-0603R / KT-0603W | BASIC | 7.86M / 1.90M | 0.008 / 0.012 |
| LED 0805 緑/黄/白/赤 | C2297 / C2296 / C34499 / C84256 | KT-0805G / Y / W / NCD0805R1 | BASIC | 2.7M / 791k / 432k / 3.97M | 0.014-0.020 |
| DIP SW 1.27mm 4P (SMD) | C319050 | DSHP04TS-S | ext | 51,304 | 0.528 |
| DIP SW 2.54mm THT 4P | C99418 | DSWB04LHGET | ext | 37,752 | 0.211 |
| カードエッジ | (60P 2.54mm ピッチは DB に該当なし → 未確認。検索ヒットは 0.5/0.8mm 品) | | | | |
- Basic に DIP スイッチ、ピンヘッダ、IC ソケット、コネクタは無い。タクト・LED のみ Basic。THT の Basic は 0 品(§1)。→ DIP SW・ソケット・コネクタは「Extended 扱い」または手はんだ。

### Takeaway (§2 全体)
Basic だけで揃うのは受動部品、LED、タクト、1N4148W/BAV99/Schottky/TVS(双方向 SMBJ6.5CA)、MMBT3904・S8050/S8550、2N7002・AO3400/AO3401、LM358/LM393/NE5532/TL072、AMS1117-3.3/-5.0、XL1509-5.0 など。74HC14 と 74HC595 以外の 74HC ロジック、SRAM、MCU、USB-C、スピーカーアンプ、水晶 21.47727MHz、DIP スイッチ、ソケット、コネクタ、電解コンデンサ、ポリヒューズは Basic に無い (Preferred または Extended)。

### Gaps (§2)
- 74HC368, 74HCU04, 6116/6264 系 DIP/SOP SRAM は DB 未収載。
- DB の在庫・価格は最終取得 2026-10-28 頃 (CSV 内 fetched_at 最大値)。発注直前に jlcpcb.com/parts で再確認が必要。
- 「Basic」判定は CDFER CSV の library_type=base による (jlcparts 由来)。JLCPCB サイトでの目視確認はしていない。

## 3. 秋月電子通商 (akizukidenshi.com) の在庫・価格 (2026-11-10 に検索ページを直接取得)

### Takeaway
DIP-40 ソケット、ピンソケット/ヘッダ、Pico 系、DIP スイッチ、電解コンデンサ、トリマ、ヒートシンクは在庫あり。60 ピン 2.54mm カードエッジ(ファミコン用)、21.47727MHz 水晶は秋月に無い (3.579545MHz 水晶 HUSG-3.579545-20 はある)。

### Cited Findings (URL は検索ページ: https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=<語>&search=search 、商品は https://akizukidenshi.com/catalog/g/g<販売コード>/ 形式。g100034 のページ取得で形式を確認)
| 品目 | 型番 | 販売コード | 価格(税込) | 在庫(通販可能数) |
|---|---|---|---|---|
| 丸ピン IC ソケット 40P (600mil) | 2227MC-40-06 | 100034 | ¥110 | 在庫あり 3,491 |
| ゼロプレッシャーIC ソケット 40P 600mil | ULO-ZS431-40P1G | 111744 | ¥250 | 在庫あり 175 |
| ロープロファイル ゼロプレッシャー 40P 600mil | (型番表示なし) | 105436 | ¥250 | 在庫あり 846 |
| 丸ピン IC ソケット 28P 600mil | 2227MC-28-06 / -06-01 | 100033 / 106740 | ¥60 / ¥50 | 1,000 / 439 |
| ピンソケット 1x20 | FH-1x20 | 103077 | ¥50 | 6,125 |
| 丸ピンIC用ソケット 1x20 | 6604S-20 | 100241 | ¥80 | 4,474 |
| Pico 用ピンソケット 20P 左右セット (6.1mm / 3.2mm) | FH-1x20-6.1CO / FH-1x20-3.2CO | 117584 / 117585 | ¥300 / ¥250 | 1,319 / 1,609 |
| 丸ピンIC用ソケット 1x40 | 6604S-40 | 101591 | ¥150 | 5,000 |
| ピンヘッダー 1x40 | PH-1x40SG | 100167 | ¥35 | 8,000 |
| ピンソケット 2x20 (RasPi 用) | FH-2x20SG | 100085 | ¥80 | 7,906 |
| ラズパイ用スタッキング 2x20 | MFH2X20SG-2 | 110702 | ¥150 | 11,503 |
| Raspberry Pi Pico | SC0915 | 116132 | ¥800 | 在庫あり 1,520 |
| Raspberry Pi Pico H | SC0917 | 118085 | ¥920 | 523 |
| Raspberry Pi Pico W | SC0918 | 117947 | ¥1,240 | 1,037 |
| Raspberry Pi Pico WH | SC0919 | 118086 | ¥1,375 | 1,126 |
| Raspberry Pi Pico 2 | SC1631 | 129604 | ¥990 | 1,462 |
| Raspberry Pi Pico 2 H | SC1632 | 130982 | ¥1,180 | 在庫僅少 53 |
| Raspberry Pi Pico 2 W | SC1633 | 130330 | ¥1,375 | 625 |
| Raspberry Pi Pico 2 WH | SC1634 | 130399 | ¥1,710 | 166 |
| Raspberry Pi Zero 2 WH | SC0721 | 129607 | ¥3,980 | 欠品 (表示「2月上旬入荷予定」) |
| Raspberry Pi Zero WH | Raspberry Pi Zero WH | 112961 | ¥3,580 | 「在庫あり 1月上旬入荷」の表示 (解釈未確認) |
| DIP スイッチ 4P | EDS104SZ / KSD42 | 100586 / 108923 | ¥100 / ¥70 | 5,000 / 4,141 |
| DIP スイッチ 6P | EDS106SZ / KSD62 | 115241 / 108925 | ¥60 / ¥120 | 1,546 / 442 |
| DIP スイッチ 8P | EDS108SZ / KSD82 | 100587 / 108926 | ¥120 / ¥130 | 3,000 / 674 |
| DIP スイッチ 10P | KSD102 | 108927 | ¥200 | 326 |
| 表面実装 DIP スイッチ 4P / 8P | KHS42E / KHS82E | 108929 / 108930 | ¥100 / ¥170 | 12,685 / 在庫僅少 2 |
| 電解コンデンサ 100uF 16V / 25V / 35V / 50V (ルビコン) | 16PX100MEFC5X11 / 25PX100MEFC5X11 / 35ZLH100MEFC6.3X11 / 50PX100MEFC8X11.5 | 110271 / 117877 / 102724 / 117905 | ¥10 / ¥10 / ¥15 / ¥20 | 67,744 / 94,293 / 在庫あり / 34,335 |
| 半固定VR 3362P 10k | 3362P-1-103LF | 103277 | ¥70 | 19,914 |
| 半固定VR 3362P 1k/5k/50k/100k | 3362P-1-102/502/503/104LF | 103271/103275/103281/103283 | ¥50-70 | 2,210-17,955 |
| 小型ボリューム 10kΩB | SH16K4B103L20KCCI | 118292 | ¥80 | 5,000 |
| USB Type-C コネクター 電源供給用 | A295-CTRPB-1 / UJC-HP-3-SMT-TR | 116895 / 116438 | ¥40 / ¥90 | 19,835 / 3,727 |
| USB Type-C 基板用(16P) | 5077CR-16-SMC2-BK-TR | 114356 | ¥110 | 在庫僅少 209 |
| ヒートシンク 20x20x25mm / TO-220用 30x30x30mm | 20PB020-01025 / 30PC030-01030 | 105054 / 100429 | ¥80 / ¥110 | 2,054 / 772 |
| クリスタル 12MHz / 3.579545MHz / 16MHz | HUSG-12.000-20 / HUSG-3.579545-20 / HUSG-16.000-20 | 108669 / 108664 / 108671 | ¥30 | 862 / 269 / 2,702 |
| カードエッジ 60P 2.54mm | 取扱なし (「カードエッジ」検索は micro:bit 用 1.27mm 80P 等 3 件のみ) | - | - | - |
| 21.47727MHz 水晶/発振器 | 取扱なし (検索ヒット 0。他に 20MHz/24MHz/25MHz 等のみ) | - | - | - |
- 出典: 上記検索ページ (キーワード: ICソケット 40P, 600mil, ピンソケット 1x20, ピンソケット 2x20, Raspberry Pi Pico, ディップスイッチ, DIPスイッチ 6P/10P, 電解コンデンサ 100uF, 半固定ボリューム, USBコネクタ Type-C, ヒートシンク, 水晶振動子) 
- 注意: 検索ページには 1x20/1x40 の 2.54mm 品ほか 1.27mm/2mm ピッチ品も混在 — 購入時はピッチ確認。
- 秋月に Pico 以外の Zero 2 W 単体 (非 H) は検索に出ず。Zero 2 WH のみ。

## 4. ファミコン 60P カードエッジ・21.47727MHz 水晶 (秋月以外の入手先)

### Cited Findings
- ヒロセ CR22A-60D-2.54DS(70): 2.54mm ピッチ 60 ピン、システムギアダイレクトに見積依頼して 1 個 ¥250 (ブログ記載、2008 投稿・2022 更新)。千石電商にも取扱があるが取付ミミを削る必要あり — [BAKUTENDO](https://bakutendo.net/blog-entry-45.html)
- ZedLabz の Famicom 60 ピン交換コネクタ £8.56 (売切れ表示) — [ZedLabz](https://www.zedlabz.com/products/replacement-cartridge-60-pin-connector-for-nintendo-famicom-game-cartridge-slot-socket-zedlabz)
- メルカリに「FC 60 ピンスロットコネクタ (ネジ穴付)」¥1,680 の出品、Amazon.co.jp の同名商品は「現在在庫切れ」(検索結果の要約, 個別ページ未確認) — [Amazon.co.jp](https://www.amazon.co.jp/FC-60%E3%83%94%E3%83%B3%E3%82%B9%E3%83%AD%E3%83%83%E3%83%88%E3%82%B3%E3%83%8D%E3%82%AF%E3%82%BF-%E3%83%95%E3%82%A1%E3%83%9F%E3%82%B3%E3%83%B3%E3%83%AA%E3%83%9A%E3%82%A2%E3%83%91%E3%83%BC%E3%83%84/dp/B00C460760)
- Kasyn Parts / eBay / AliExpress に 60 ピンクローン機用スロット ($1.95 から、$4-14 程度)。ピッチ記載なし — [Kasyn Parts](https://kasynparts.com/product/nintendo-famicom-fc-cartridge-60-pin-connector/), [eBay](https://www.ebay.com/itm/294860326964)
- LCSC/JLCPCB にはファミコン用 60P 2.54mm カードエッジは確認できず。2.54mm ピッチ edge コネクタは X2549WV-2x31-PTV01 (C21261717, 2x31=62P, ext, 在庫 558, $1.67), X2549WR-2x32A-PTV01 (C21261728, 2x32=64P 直角, 在庫 876, $1.91) など 2x28/2x31/2x32 の別ピン数品のみ (CDFER SQLite 2026-11-10)。Famicom の 60P (2x30) と一致するピン数は DB 内で確認できず — 未確認
- 21.47727MHz: JLCPCB 側 Extended 4 種 (§2.7)。LCSC の他在庫は未確認。AliExpress/Sengoku/Marutsu での 21.47727MHz 取扱は未確認 (検索未実施)。

### Gaps
- 千石電商・マルツ・共立・aitendo の 60P 2.54mm カードエッジの現在の在庫と価格: 未確認 (サイト検索未実施)。
- Famicom 側のピン配列・ピッチ (2.54mm=0.1") はブログ記載のみで一次資料未確認。

## 5. JLCPCB PCB 製造 (ゴールドフィンガー付き JAMMA 基板)

### Takeaway
ゴールドフィンガーは ENIG のみ提供、面取り 30°/45°、1.6mm 板は可。公式にハードゴールド記載は無く、要問い合わせ。ゴールドフィンガーを使うと PCBA は Standard 必須。価格は動的見積のため 150x200mm の具体額は未確認。

### Cited Findings
- ゴールドフィンガーは ENIG のみで、HASL では錫が被る。面取りは 30° と 45° (30° 推奨)、5x5cm 未満の板では面取り不可、面取り部に銅箔不可、フィンガー部ソルダーマスク全開口 (未指定でも自動開口)、板/パネルは縦横 50mm 以上 — [JLCPCB Gold fingers](https://jlcpcb.com/help/article/jlcpcb-gold-fingers)
- 30° 面取りで 1.6mm 板ではパッド端と板端の間に 0.6mm 必要 (JLCPCB ブログ記載) — [JLCPCB blog](https://jlcpcb.com/blog/pcb-card-edge-connectors-design-gold-fingers-manufacturing)
- ENIG 金厚 2-5µin / 硬質金 30-50µin は一般論で JLCPCB 固有値ではない (同ブログ)。JLCPCB の金厚・ハードゴールド対応は公式ページで未記載
- ENIG 面積が板全体の 30% 超だと超過分に追加費用 (1U" 金で 1% あたり $0.8992/m² の例) — [JLCPCB 追加費用](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra)
- 標準サービスの設計ルール: 線幅/間隔 2層 0.10/0.10mm (4/4mil)、4層 0.09/0.09mm; 最小ビア穴/径 0.15/0.25mm (推奨穴 0.2mm); 最小 PTH 0.15mm; 最小 NPTH 0.50mm; 板厚 0.4-2.0mm (1.6mm 標準); 最大サイズ 2層 670x600mm 等 — [JLCPCB PCB capabilities](https://jlcpcb.com/capabilities/pcb-capability)
- ゴールドフィンガー追加費の第三者推定: 5 枚注文で $10-20 とするガイドあり (非公式・信頼性低) — [検索結果要約](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra)
- 日本向け送料・関税: JLCPCB 固有の数値は取得できず。一般論として日本の輸入少額免税は課税価格 10,000 円以下 (2026 年ガイド記載、一次資料未確認) — 未確認
- 基板価格 (150x200mm, 2層/4層, 5/10 枚): JLCPCB Instant Quote は動的で今回取得不可 — 未確認

### Inferences
- 150x200mm は 2 層でも「100x100mm 超」の価格帯で、$数十/5枚規模になる可能性があるが数値は未確認。
- JAMMA 56P の 3.96mm ピッチ金指は片面28本 (表裏各28=56)。30° 面取り要件のため、指先端の銅領域とエッジ処理 (パッド端-板端 0.6mm 以上) を KiCad のエッジカット側で確保。
- 板厚は 1.6mm が JAMMA の標準規格 (一般知識; 本ノートでは未検証)。

## 6. 1 枚あたりコスト見積もり方法 (概算例)

### 方法
総額 = PCB 製造費 + PCBA (Setup + ステンシル + 装填料 + SMT ジョイント + 手はんだ/THT 費) + 部品代 (JLCPCB/LCSC) + 送料・関税 + 秋月部品 (別送料)。
- Standard PCBA (ゴールドフィンガーのため必須): Setup $25.56 + ステンシル $8.21 + 1.53 x 部品種類数 (Basic も Extended も課金) + 0.0016 x SMT ジョイント数 + $3.5 (人手あり時) + $0.45 (配置確認) — 出典 [公式ブログ](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
- 比較: Economic (ゴールドフィンガーなし基板に分割する場合) Setup $8.18 + ステンシル $1.53 + 3.07 x Extended 種類数のみ (Basic/Preferred は無料)

### 概算例 (仮定値。実 BOM 未確定なので全体の桁だけを示す)
仮定: 部品種類 30 (全て Basic またはPreferred、受動・74HC14/595・LM358 等)、SMD ジョイント 800、数量 5 枚、手はんだ無し。
- PCBA 固定費: 25.56 + 8.21 + 30 x 1.53 (=45.90) + 800 x 0.0016 (=1.28) + 0.45 = 約 $81.4 (5 枚で $16.3/枚)
- 部品代 (JLCPCB 単価ベース): 受動 100 個 x $0.01 + IC 8 個 x ~$0.15 + 他 ~ $5 ≒ $7-8/枚 (§2 の単価を使用した推定)
- PCB 製造費: 未確認 (Instant Quote で要見積)。
- 秋月部品 (手はんだ): DIP-40 ソケット 2 個 ¥220 + Pico ¥800 (または Pico 2 ¥990) + Pico 用ソケット ¥250-300 + DIP スイッチ ¥100-200 + 21.47727MHz 水晶は秋月に無く別途 + カードエッジ別途 ≒ ¥1,500 前後 (§3 の単価の合計) 。
- 結論: Standard PCBA ではコスト支配項は固定費 (約 $80) を枚数で割ったもの。種類数を 1 つ減らすと $1.53 減、枚数を 10 に倍増すると固定費/枚はほぼ半減。

### Gaps (全体)
- JLCPCB 公式 FAQ (Basic 698 種, $3, $8, $1.50) と 2026-10 公式ブログ (Basic 数不記載, $3.07, $8.18, $1.53) の差異の理由は未確認 (FAQ が古い可能性)。
- Standard PCBA での THT 部品 (DIP ソケット等) 実装費、ゴールドフィンガー + 部品面制約は未確認。
