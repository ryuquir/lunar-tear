# マイコン基盤（Raspberry Pi Pico 2 / RP2350）とエミュレーション方式 - リファレンスシート

- **マイコンは RP2350（Raspberry Pi Pico 2 または RP2350A/B チップ）を使う。** Linux が動く Raspberry Pi は、カセットを読む端子が足りず、起動が遅く、電源断にも弱いので採らない。
- **エミュレーションモードは「電源投入時にカセットを丸ごと読み出してから動かす方式」なら Pico 2 1 枚で成り立つ見込みである**（端子 22 本は机上の割り当てで未確認、日本のライセンス品カセットで使われる 58 種のマッパーはすべて既存エミュレータに登録済み）。カセットのバスを実時間で動かす方式は成り立たない（推論）。
- **実チップモード（ファミコンの CPU/PPU を使う）は Pico 2 1 枚では端子が足りない**（机上の割り当てで最小 38 本）。Pico 2 を 2 枚に分けるか、RP2350B（48 端子）を基板に直接載せる。マイコンは何枚使ってもよいという現行要求に合わせ、役割ごとに複数枚に分ける（推論）。
- **5V への直結は、RP2350 の 3.3V 電源が入っている間に限って GPIO0〜22（Pico 2）で許される。** 電源が入っていない間は 3.63V までしか許されないので、5V 側の電源投入を遅らせる回路が要る（推論）。3.3V 出力で 5V 給電の 74HC を駆動するのは規格外である。
- **Pico 2 の USB 端子は Micro-B で、USB の信号は 40 本の端子列に出ておらず、裏面のテストパッド TP2（USB DM）・TP3（USB DP）にだけ出ている**（Pico 2 Datasheet で確認）。USB Type-C で更新するには、ケーブル中継、裏面パッドへの配線、チップ直載せのどれかを選ぶ必要がある。書き込み機能は書き換えできない ROM にあるので、更新に失敗しても書き込みモードに入り直せる。

データの日付: 2026-11-10（秋月電子の価格・在庫、GitHub のリリース、データシートの版はすべてこの日に取得した値）

---

## 1. 確定事実

### 1.0 用語

このシートで使う用語を先に定義する。

| 用語 | 意味 |
|---|---|
| 実チップモード（Mode A） | ファミコン本体から外した CPU（RP2A03）と PPU（RP2C02）を基板のソケットに挿して動かす方式。マイコンは映像の RGB 化、入力、コイン・タイマー制御を担う。 |
| エミュレーションモード（Mode B） | CPU と PPU をマイコンのソフトウェアで再現（エミュレート）する方式。CPU/PPU のチップは使わない。 |
| ダンプ方式 | エミュレーションモードで、電源投入時にカセットの ROM の中身をマイコンのメモリへ読み出し（ダンプし）、その後はメモリ上のデータでエミュレートする方式。 |
| 実時間バス駆動 | エミュレータが命令を実行するたびに、本物のカセットのバスを実際に操作して読み書きする方式。 |
| マッパー | カセットに載っている、ROM のバンク切り替えなどを行う回路。iNES 規格の番号（mapper 0, 1, 4 など）で区別する。 |
| GPIO | マイコンの汎用入出力端子。 |
| FT ピン（Digital IO (FT)） | RP2350 のデータシートで「Fault Tolerant」と分類される GPIO。条件付きで 5.5V まで耐える。 |
| IOVDD | RP2350 の GPIO 用電源（Pico 2 では基板上の 3.3V）。 |
| PIO / SM | RP2350 が持つ、端子を 1 クロック単位で操作できる小さなプログラム実行装置（Programmable I/O）。1 個の PIO ブロックに 4 個の状態機械（State Machine, SM）がある。 |
| ステッピング | 同じチップの製造版の違い（A2, A3, A4）。パッケージ上面の刻印で分かる。 |
| E9 エラッタ | RP2350 の不具合 RP2350-E9（入力を有効にした GPIO から電流が漏れる）。 |
| BOOTSEL | Pico/Pico 2 のボタン。押しながら電源を入れると USB 書き込みモードになる。 |
| UF2 | USB マスストレージとして見えるマイコンに、ファイルをドラッグするだけで書き込めるファームウェアのファイル形式。 |
| A/B 区画・TBYB | RP2350 のブート ROM の機能。フラッシュに 2 つの区画（A/B）を持ち、交互に更新する。TBYB（Try Before You Buy）は新しいイメージが自己テストに合格しない限り旧イメージに戻す機能。 |
| XIP | フラッシュメモリ上のプログラムやデータを、RAM にコピーせずに直接実行・参照する方式（eXecute In Place）。 |
| PSRAM | QSPI で接続する外付けの擬似 SRAM。大容量のデータ置き場になる。 |
| CSync | 水平同期と垂直同期を 1 本にまとめた複合同期信号。JAMMA の映像の標準。 |
| DPI | Linux の Raspberry Pi が持つ、GPIO からパラレル RGB を出す映像出力機能。 |
| HSTX | RP2350 が持つ高速デジタル出力機能（DVI/HDMI 向け）。 |
| 確認済 / 単一出典 / 未確認 | 確認済 = 独立した出典が 2 つ以上、またはデータシート・ネットリスト・実データ（販売ページや取得したソースコード）で確かめたもの。単一出典 = 出典が 1 つだけのもの。未確認 = 出典で確かめられていないもの（計算値・推論を含む）。 |

### 1.1 候補デバイスの比較と秋月電子での入手性

#### 1.1.1 方式別の比較

| 候補 | GPIO | 5V 耐性 | 映像出力の手段 | カセット読み出し | 起動・電源断 | 確度 |
|---|---|---|---|---|---|---|
| Raspberry Pi Pico 2（RP2350A、モジュール） | 26 本（GPIO0–22 と GPIO26–28）。うち 5V 耐性は GPIO0–22 の 23 本 | IOVDD 給電中のみ 5.5V まで | PIO＋抵抗 DAC でアナログ RGB。HSTX は DVI 向け | シフトレジスタで端子を増やせば可能（1.8） | ファイルシステムなし。書き込み機能は ROM 内 | 確認済 |
| RP2350B（QFN-80、チップを基板に直接実装） | 48 本。うち FT は GPIO0–39 の 40 本、GPIO40–47 は ADC 兼用 | 同上 | 同上 | 同上（端子に余裕） | 同上 | 確認済 |
| 初代 Pico（RP2040） | 未確認（本シートの対象外） | **5V 耐性の記述なし**。絶対最大 VPIN = IOVDD+0.5V | PIO | — | A/B 区画機能の明示確認は未確認 | 確認済（5V 耐性なし） |
| Linux が動く Raspberry Pi（Zero 2 W〜5） | 40 ピンヘッダの GPIO0–27（28 本）。DPI 映像でほぼ埋まる | 3.3V 専用・5V 非耐性（SoC データシートでの再確認は未実施） | DPI（GPIO0–27 の ALT2）＋抵抗 DAC で 15kHz RGB は確立済み | GPIO が足りず、別マイコンが必要 | SD カード破損対策が必要。起動は最小構成で数秒、Raspberry Pi OS では数十秒 | 5V 非耐性は未確認、他は確認済 |

#### 1.1.2 秋月電子で買える RP2350 系（2026-11-10 取得。価格は税込、在庫は「通販購入可能数」）

| 品名 | 型番 | 販売コード | 価格 | 在庫 | GPIO / メモリ（秋月記載） | 確度 |
|---|---|---|---|---|---|---|
| Raspberry Pi Pico 2 | SC1631 | 129604 | ¥990 | 1,462 | GPIO 26、4 MB flash、520 kB（発売日 2024/09/18） | 確認済 |
| Raspberry Pi Pico 2 H(完成品) | SC1632 | 130982 | ¥1,180 | 53（在庫僅少） | GPIO 26 | 確認済 |
| Seeed XIAO RP2350 | 102010550 | 129619 | ¥1,100 | 308 | "19のGPIO"、2 MB flash | 確認済 |
| Tiny 2350 (Pimoroni) | PIM721 | 130201 | ¥1,600 | 17 | GPIO 12、4 MB | 確認済 |
| Plasma 2350 (Pimoroni) | PIM723 | 130202 | ¥2,340 | 37 | GPIO 15、4 MB | 確認済 |
| W5100S-EVB-Pico2 (WIZnet) | W5100S-EVB-Pico2 | 130218 | ¥2,420 | 73 | 秋月表記 "GPIO：48"（Pico 形状なので誤記の可能性、未確認） | 確認済（表記の真偽は未確認） |
| RP2350A（チップ単体、QFN60） | SC1509 | 130369 | ¥190 | 521 | GPIO 30 | 確認済 |
| RP2350B（チップ単体、QFN80） | SC1510 | 130370 | ¥220 | 242 | GPIO 48 | 確認済 |
| RP2354A（2 MB flash 内蔵、QFN60） | SC1511 | 131439 | ¥250 | 281 | GPIO 30 | 確認済 |
| RP2354B（2 MB flash 内蔵、QFN80） | SC1512 | 131441 | ¥280 | 115 | GPIO 48 | 確認済 |
| RP2350A実装基板（秋月製 QFN60 変換基板） | AE-QFN60-7X7-0.4(RP2350A) | 131106 | ¥450 | 189 | GPIO 30 | 確認済 |
| Pimoroni Pico LiPo - 16MB（**RP2040**、参考） | PIM560 | 116997 | ¥1,480 | 170 | — | 確認済 |
| Raspberry Pi Pico（RP2040、参考） | — | g116132 | ¥800 | 未確認 | — | 単一出典 |
| Pico 用ピンソケット | FH-1x20-3.2CO | 未確認 | ¥250（Pico 1 枚分。「Pico 2 + ソケット ¥1,240/枚」） | 未確認 | — | 単一出典 |

- 秋月の検索（"PSRAM"、"APS6404"、"ESP-PSRAM64"、"LY68L6400"、"Pico Plus"、"RP2350B"、"SRAM"）では、**RP2350B を載せた完成ボード、PSRAM を載せた RP2350 ボード、QSPI PSRAM チップ単体はどれも見つからなかった**。"SRAM" では 23LC512-I/P（SPI SRAM 64 KB）と M68AF127B（1 Mb パラレル SRAM）だけが出た。（確認済：検索結果の実データ）
- 別の第 2 パスノートは、秋月の「RP2350」検索に W5500-EVB-Pico2 が出たと記録しており、上表の W5100S-EVB-Pico2 と名前が異なる。設計には影響しない。（未確認）
- QFN-80（0.4 mm ピッチ）の手はんだは現実的でないので、RP2350B 案は JLCPCB の部品実装が前提になる。（推論）

#### 1.1.3 LCSC / JLCPCB での RP2350

| 品 | 番号 | 分類 | 在庫・価格 | 確度 |
|---|---|---|---|---|
| RP2350A（QFN-60） | C42411118 | JLCPCB Extended | JLCPCB 在庫 6,268・$1.2943（1 個〜）、LCSC 在庫 5,699・$1.3065（1 個〜）（JLCPCB と LCSC の直接照会、parts_class_reverification.md）。別ノートの「在庫 3080、$1.18@1 個」は jlcparts 系の派生データの値で採らない。ステッピング記載なし | 確認済 |
| RP2350B / RP2354B | 未確認 | 未確認 | 未確認 | 未確認 |
| PSRAM（LCSC/JLCPCB） | 未確認 | Basic 可否は未確認 | 未確認 | 未確認 |

#### 1.1.4 Pico 2 モジュールの仕様

| 項目 | 値 | 確度 |
|---|---|---|
| 外形 | 51×21 mm。40 本のメインピンは 2.54 mm グリッド、1 mm 穴。DIP 形式・表面実装（キャスタレーション）の両用 | 確認済（Pico 2 Datasheet） |
| 列間隔 | 17.78 mm（0.7 in）と広く言われるが、データシート本文での確認はできていない | 未確認 |
| マイコン・フラッシュ | "RP2350A microcontroller with 4 MB flash"、フラッシュは "Winbond W25Q32RV" | 確認済 |
| 内部で使う GPIO | GPIO23（基板上 SMPS の Power Save 制御）、GPIO24（VBUS 検出）、GPIO25（ユーザー LED）、GPIO29（ADC3 で VSYS/3 を測定） | 確認済 |
| 40 ピン上の GPIO・GND 以外 | VBUS(40)、VSYS(39)、3V3_EN(37)、3V3(36)、ADC_VREF(35)、AGND(33)、RUN(30) の 7 本 | 確認済 |
| VSYS の範囲 | 1.8–5.5V | 確認済 |
| RUN | "RUN is the RP2350 enable pin, and has an internal (on-chip) pull-up resistor to 3.3 V of about ~50 kΩ." | 確認済 |
| 3V3_EN | "connects to the on-board SMPS enable pin, and is pulled high (to VSYS) via a 100 kΩ resistor." | 確認済 |
| GPIO の電圧 | "The Raspberry Pi Pico 2′s GPIO is powered from the on-board 3.3 V rail and is therefore fixed at 3.3 V." | 確認済 |
| 水晶 | Abracon ABM8-272-T3、12 MHz、"The crystal has a 30 ppm frequency tolerance"。XIN はこの水晶に接続済み | 確認済 |
| 3.3V 電源 | 基板上の RT6150 SMPS が VSYS から 3.3V を作る。RUN とは無関係に動く | 単一出典（Pico 2 Datasheet の記述からの読み取り） |
| USB 端子 | Micro-B（"Micro-USB B port for power and data"）。USB の信号線は 40 本の端子列には出ておらず、基板裏のテストパッド TP1（USB 用 GND）・TP2（USB DM）・TP3（USB DP）にしかない（"TP1, TP2 and TP3 can be used to access the USB signals instead of using the micro-USB port"）。TP6 は BOOTSEL（電源投入時に Low で USB 書き込みモード） | 確認済（Pico 2 Datasheet §3.1、本検証で原文確認） |
| VSYS 投入から 3V3 確立までの時間 | 数 ms 程度と推定、実測なし | 未確認 |

#### 1.1.5 RP2350 チップの主要仕様

| 項目 | 値 | 確度 |
|---|---|---|
| CPU | "Dual Cortex-M33 or Hazard3 processors at 150 MHz" | 確認済 |
| 最大システムクロック | "a 150 MHz system clock, the maximum supported on RP2350"（Table 573 も clk_sys 公称最大 150 MHz） | 確認済 |
| SRAM | "520 kB on-chip SRAM, in 10 independent banks" | 確認済 |
| 外付けメモリ | "Up to 16 MB of external QSPI flash or PSRAM through dedicated QSPI bus"、"Additional 16 MB flash or PSRAM through optional second chip-select" | 確認済 |
| GPIO | RP2350A（QFN-60）30 本・ADC 4、RP2350B（QFN-80）48 本・ADC 8 | 確認済 |
| リセット直後の GPIO | 全 GPIO の Reset State は "Pull-Down"。"Output buffer is high-impedance / Input buffer is disabled / Pulled low / Isolation latches are set to latched" | 確認済 |
| GPIO の電気特性（IOVDD=3.3V） | VIH(FT) 2〜5.5V、VIL ≤0.8V、VOH ≥2.62V（2/4/8/12 mA 設定）、VOL ≤0.5V、IIN 最大 1 µA、プルアップ 32〜86 kΩ、プルダウン 36〜113 kΩ | 確認済 |
| GPIO 電流の合計 | "Maximum Total IOVDD current 100 mA"（全 GPIO の吐き出し合計） | 確認済 |
| 各コアの補助演算器 | INTERP0/INTERP1（"table lookup address generation" 等を 1 サイクルで） | 確認済 |
| XIP キャッシュの RAM 化 | pico-sdk 2.3.0 から "RP2350's XIP cache can now be used as additional SRAM via `pico_use_xip_cache_as_ram()`" | 単一出典 |

### 1.2 RP2350 の 5V 耐性

#### 1.2.1 正確な条件

| 条件 | 許される電圧 | データシートの原文 | 確度 |
|---|---|---|---|
| IOVDD=3.3V 給電中の FT ピン | −0.5〜5.5V | "they will tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V"（Table 1673）、VPIN_FT は IOVDD=3.3V で 5.5V（Table 1680） | 確認済 |
| IOVDD=2.5V | 4.2V まで | Table 1680 | 確認済 |
| IOVDD=1.8V | 3.63V まで | Table 1680 | 確認済 |
| **IOVDD=0V（電源が入っていない）** | **3.63V まで** | "very little current flows into the pin whilst it is below 3.63 V and IOVDD is 0 V"、Table 1680 Comment "IOVDD must be present" | 確認済 |
| FT ピンの入力 High | IOVDD=3.3V で Min 2V / Max 5.5V | Table 1683 "IOVDD must be powered to tolerate input voltages above 3.63V" | 確認済 |
| 通常ピン（ADC 兼用など） | −0.5〜IOVDD+0.5V | Table 1680 VPIN (Standard) | 確認済 |
| 総括 | "GPIOs are 5 V-tolerant (powered) and 3.3 V-failsafe (unpowered)"（§1 Introduction） | — | 確認済 |
| 公式ブログ（2025-07-29） | "RP2350 is now officially 5V tolerant!"、"Just make sure to keep IOVDD powered when 5V is applied to any GPIO pad, otherwise the pad will be damaged." | — | 確認済 |
| データシート改訂履歴 | "Added information about the GPIOs being 5 V tolerant." | — | 確認済 |
| A2 ステッピングが 5V 耐性か | 公式に明言なし（二次情報のみ） | — | 未確認 |

#### 1.2.2 端子ごとの可否

| 端子 | 分類 | 5V 直結 | 確度 |
|---|---|---|---|
| RP2350A の GPIO0–25 | Digital IO (FT) | 可（IOVDD 給電中のみ） | 確認済 |
| RP2350A の GPIO26_ADC0〜GPIO29_ADC3 | "Digital IO / Analogue"（Power Domain "IOVDD / ADC_AVDD"） | **不可** | 確認済 |
| RP2350B の GPIO0–39 | Digital IO (FT) | 可（IOVDD 給電中のみ） | 確認済 |
| RP2350B の GPIO40_ADC0〜GPIO47_ADC7 | "Digital IO / Analogue" | **不可** | 確認済 |
| **Pico 2 の GPIO0–22（23 本）** | FT | **可**（IOVDD 給電中のみ） | 確認済 |
| Pico 2 の GPIO26–28 | ADC 兼用。"the input voltage must not exceed IOVDD plus about 300 mV" | **不可**（RGB DAC など 3.3V だけの用途に回す） | 確認済 |
| RP2040 | FT ピンは「IOVDD=0V で 3.63V 未満なら電流ほぼ流れない」のみ | 不可 | 確認済 |

#### 1.2.3 電源が入っていないときの扱い

- Pico 2 Datasheet p.14 の "Normal digital GPIO pins 0-25 (and also the debug pins) do not have this restriction and therefore voltage can safely be applied to these pins when RP2350 is unpowered." は、**3.63V 以下の電圧に限った話である**。電源が入っていない RP2350 に 5V を掛けてよいという意味ではない。（確認済：RP2350 Datasheet "3.3 V-failsafe (unpowered)"、VPIN_FT は IOVDD=0V で 3.63V）
- ADC 兼用ピン（GPIO26–29）は、RP2350 に電源がないときに電圧を掛けると内部ダイオードを通って IOVDD へ漏れる。（確認済）
- FT ピンに、電源のない状態で 3.63〜5V が掛かったときの電流（直列抵抗で制限した場合の許容値）はデータシートに記載がない。（未確認）
- **リセット中（RUN=Low）**: Pico 2 の 3.3V は RUN と無関係に VSYS から作られるので IOVDD は給電されたままであり、5.5V 耐性の条件は満たされると読める。リセット中に限った明文は見つかっていない。（未確認：推論）
- **危険な時間帯（推論）**: JAMMA の +5V が先に立ち上がり、Pico の 3.3V が立つまでの数 ms（未計測）に、5V 側の静的な High（外付けプルアップ、NMOS 出力の High）が FT ピンに 3.63V を超えて掛かる。電源断のときは、Pico の昇降圧 SMPS が VSYS 1.8V まで動くので 3.3V が 5V 系より長く残り、比較的安全である（推論）。
- **対策の候補（推論）**:
  - (a) 5V 側のドライバ（74HC/74HCT）の /OE を、Pico の 3V3 が確立するまで Hi-Z に保つ。
  - (b) FT ピンに直列抵抗（1〜10 kΩ、推奨 1 kΩ）を入れて故障電流を制限する。ただし 3.63V を超えた時点で "very little current" の保証外であることは変わらない。
  - (c) 5V→3.3V 方向には、3.3V 給電の 74LVC 系（5V 耐性入力）を挟む。
  - (d) Pico の 3V3 を検出して P-MOS（SI2301 / AO3401A、JLCPCB Basic）で CPU/PPU/カセットの 5V を後から入れる（ゲートは 2N7002、Basic）。
  - (e) FT ピンにつながる線のプルアップは 5V ではなく 3.3V へつなぐ（/IRQ など RP2350 が見る線）。
  - 部品が最も少ないのは (a)+(b)（pico2_platform_verification.md の推論）。実チップモードで CPU/PPU も含めて守るなら (d)+(b)+(e)（rgb_pico2_feasibility.md の推論）。

### 1.3 E9 エラッタと対策済みの版

| 項目 | 内容 | 確度 |
|---|---|---|
| 名称 | RP2350-E9 "Increased leakage current on Bank 0 GPIO when pad input is enabled"（Appendix D.5.1） | 確認済 |
| 影響する版 | "Affects: RP2350 A2"、"For GPIO pads 0 through 47" | 確認済 |
| 症状 | 入力を有効にしたパッドが不定電圧域で電流を吐き出し（"typically around 120μA"）、"hold the pad at around 2.2 V"。"The pad pull-down (if enabled) is significantly weaker than the leakage current" | 確認済 |
| 回避 | "Driving / pulling the pad input low with a low impedance source of 8.2 kΩ or less will overcome the erroneous leakage"。"The pad pull-up still works." 入力イネーブルを解除するとリセットされる | 確認済 |
| 起動直後 | "This doesn't affect the pull-down behaviour of the pads immediately following a PoR or RUN reset because the input enable field is initially clear." | 確認済 |
| PIO への影響 | "PIO programs can't toggle pad controls and therefore external pulls may be required" | 確認済 |
| 修正 | "Fixed by: RP2350 A3, Documentation"。Appendix C.2.1 "Stepping A3 introduces the following hardware fixes … The pad circuit is modified to eliminate the erroneous leakage path through the input buffer." | 確認済 |
| 版の履歴（Table 7） | A0/A1 "Internal development"、A2 "Initial release"、A3 "Internal development, samples, and limited production"、A4 "Production version" | 確認済 |
| A4 の変更 | "This stepping has no hardware changes."（変更はブート ROM のみ: E18 修正、E24 緩和、E25 修正）。CHIP_ID.REVISION=0x3、ブート ROM 版バイト=0x4 | 確認済 |
| 公式ブログ（2025-07-29） | "we've fixed Erratum 9"、"We have already ceased production of A2"、"approximately 30,000 units of A3 inventory will be used to build Pico 2 and Pico 2 W products"、"Eventually all Pico 2 products will use the A4 stepping."、A4 は A2 とドロップイン互換 | 確認済 |
| 判別法 | パッケージ刻印（部品番号は「RP2350」+「A」(QFN-60)/「B」(QFN-80)+パッケージ版「0」+ダイステッピング「A2」「A3」「A4」）、CHIP_ID.REVISION、SDK の `rp2350_chip_version()`。picotool 2.2.0-a4（2025-08-14）は "RP2350 A3 and A4 chip revision display" に対応 | 確認済 |
| 秋月 Pico 2（129604）のステッピング | 商品ページ本文に記載なし（"A4"/"A2"/"ステッピング" で全文検索して該当なし） | 未確認（記載がないことは確認済） |
| LCSC C42411118 のステッピング | 記載なし | 未確認 |
| SDK の版と対応 | pico-sdk 2.1.0（2024-11-25）で "RP2350 A0/A1 silicon are no longer supported"。2.2.0（2025-07-29）で "the workaround for erratum RP2350-E10" | 確認済 |

- 「A3 で修正」と「A4 で修正」という表現の差は矛盾ではない。ハードウェアの修正は A3 で入り、A3 は限定生産の中間版、A4 は量産版でハードウェアの変更はない。
- E9 は 5V 耐性とは別の問題である。本基板で影響するのは「内蔵プルダウンに頼る入力」と「Hi-Z になるバスをプルダウンで読む箇所」だけである。（推論）
- **設計方針（推論）**: 入力は外付けプルアップ（アクティブ Low）にする。JAMMA のコイン・ボタン入力はもともとアクティブ Low とプルアップが慣例なので追加費用はない。プルダウンが必要な箇所は 8.2 kΩ 以下の外付け抵抗にする。こうすれば A2/A3/A4 のどれでも動き、ステッピングが未確認であることのリスクが消える。起動時に CHIP_ID.REVISION とブート ROM 版バイトを読んでログに出す。

### 1.4 3.3V 出力で 5V の NMOS チップや 74HC を駆動できるか

| 受け側 | 入力 High と認識される最小電圧（VIH） | RP2350 の VOH min 2.62V で駆動できるか | 確度 |
|---|---|---|---|
| 74HCT245（TI SN74HCT245） | "VCC = 4.5 V to 5.5 V … 2 V"、VIL 0.8V | **可**（余裕 約 0.6V） | 確認済 |
| 74HC595 / 74HC165（TI SN74HC595, SCLS041J Rev. Oct 2021） | VCC=4.5V で 3.15V、VCC=6V で 4.2V（VCC=5V の値は表になく 0.7×VCC 換算で 3.5V） | **規格外（保証なし）** | 確認済 |
| 74HC245（TI） | VIH 3.15V @VCC 4.5V（4.2V @6V） | **規格外** | 確認済 |
| 74HC14（TI） | VT+ 1.55〜3.13V @4.5V（2.1〜4.2V @6V） | 5.0V 給電では約 3.5V で**規格外** | 確認済 |
| 2A03 / 2C02（NMOS） | 公式データなし。NESdev の lidnariq: "Approximately TTL thresholds."、"It's a mixture, but you just assume it's TTL thresholds. Because the NES is NMOS, not CMOS." 実測は未実施（"To actually quantify the data bus inputs, we'll need to build a specialty cart"） | TTL しきい値（VIH 2.0V）と仮定すれば可。3.3V CPLD 駆動の実験（skrasms 2009）と TinyNES の 3.3V クロック駆動が傍証 | 単一出典（二次資料・実験のみ。一次資料なし） |
| カセット内のマッパー IC（MMC1/MMC3/VRC 等）、ディスクリート板の 74xx161 / 74xx32 | 一次資料なし。nesdir の表記では LS か HC か区別できない | 保証できない | 未確認 |

その他の事実:

- 2A03/2C02 の出力 High は約 4V（lidnariq の実測 "Voh from the 2A03 and 2C02 at approximately 4V"）。RP2350 の FT 入力（VIH 2.0V、5.5V まで）に直結できる。5V 給電の 74HC（VIH 3.15V@4.5V）で受けても約 0.5〜0.85V の余裕があるが、実測は 1 例だけである。（単一出典）
- 74HC595 の出力（送り側）は、VOH(4.5V, −6 mA) min 3.84V(85 °C)。5V 給電の 74HC は 5V 振幅を出す。（確認済）
- 74HC595 の最大クロックは 4.5V で 25 MHz（−40〜85 °C, SN74HC595 列）、74HC165 は 4.5V で 21〜31 MHz（列による）。（確認済）
- 74HC595/165/14 は 2〜6V で動く。3.3V 給電にすれば 3.3V ロジック同士として RP2350 と直結できる。（確認済：動作電圧範囲）
- 実働品の例: PICO9918 v2.0 は 3.3V→5V のデータ方向に 5V 給電の 74HC245 を使っている（規格上はマージン外）。5V ホストとの間は 74HC245（データ、5V 給電）、74AHC126（出力、5V 給電）、74LVC245（入力、3.3V 給電、"3.3V ← 5V"）でつないでいる。pico6502 は 74AHCT244（アドレス/制御）・74AHCT245（データ）で緩衝し、TLV62569 で 5V→3.3V を作る。Lava RGB は SN74LVC4245A ×2（双方向 5V↔3.3V）と SN74LVC541A ×2 を使う。（確認済：各回路図・製品ページ）
- JAMMA の CSync は負極性 TTL で High ≥3.5V が推奨されるので、3.3V の直出しでは足りない。NPN（MMBT3904/S8050、Basic）で 5V にプルアップして反転出力するか、74HCT 系を使う。（単一出典：jamma_electrical_details.md 経由）
- 部品の入手性: 秋月には 74HCT 系の DIP、74HC574（DIP）、74HC139、74HC368、CD4021 がない（検索 0 件）。JLCPCB では 74HCT が Extended、SN74LVC4245A が Preferred。秋月のレベル変換は AE-LLCNV8 (FXMA108) 104522 ¥350 在庫 398、AE-LLCNV8-DIP20 117062 ¥250 154 セット、AE-LLCNV-LVCH16T245 115696 ¥300 315 セット、AE-TXS0104E-BO 129507 ¥350 498、AE-LCNV4-MOSFET(BSS138) 113837 ¥200 2,456。（確認済：秋月の実データ。JLCPCB 分類は単一出典）

**まとめ（推論）**: 3.3V から 5V ロジックへ渡す箇所は 74HCT（または 74AHCT）にするか、74HC を 3.3V 給電にする。カセット側の入力は TTL しきい値と保証できないので、安全側は「Pico からカセットへの出力はすべて 5V 給電の 74HCT 系を通す」である。

### 1.5 PIO の要点（バス操作に必要な事実）

すべて RP2350 Datasheet による（確認済）。

| 項目 | データシートの記述 | 場所 |
|---|---|---|
| PIO の数 | "RP2350 contains 3 identical PIO blocks"、"There are three PIO blocks, each containing four state machines"、"12 × PIO state machines" | p.791 / p.13 |
| 1 命令 1 クロック | "On every system clock cycle, each state machine fetches, decodes and executes one instruction. Each instruction takes precisely one cycle, unless it explicitly stalls (such as the WAIT instruction). Instructions may insert a delay of up to 31 cycles" | p.794, §11.2.2 |
| 命令メモリ | "Each PIO instance has a 32-slot instruction memory, which all 4 state machines can see."（3 ブロックで計 96 命令） | p.794 |
| 入力同期回路 | "each GPIO input is equipped with a standard 2-flipflop synchroniser. This adds two cycles of latency to input sampling"、"It is possible to bypass these synchronisers, on a per-GPIO basis … Synchronisers are bypassed by setting the corresponding bit in INPUT_SYNC_BYPASS."、"Generally this is only possible for synchronous interfaces" | §11.5.6.3, p.824 |
| side-set | "Side-set is where a state machine drives a small number of GPIOs in addition to the main side effects of the instruction"、"Side-set … is not affected by stalls, and always takes place on the first cycle of the attached instruction."、".side_set <count> (opt) (pindirs)" で PINDIRS に適用可 | p.794, p.798, p.800 |
| 方向制御 | "Adds PINDIRS as a destination for MOV … changing the direction of all OUT-mapped pins with a single instruction: MOV PINDIRS, NULL or MOV PINDIRS, ~NULL"。SET/OUT の宛先にも PINDIRS | p.792, p.806 |
| FIFO | "Each state machine has a pair of 4-word deep FIFOs"、"SHIFTCTRL_FJOIN option can merge the two FIFOs into a single 8-entry FIFO" | §11.2.4.4, p.797 |
| RP2350 の追加機能 | SHIFTCTRL.IN_COUNT（不要ピンを 0 マスク）、RX FIFO の各エントリをランダムに読み書きできる FJOIN_RX_GET / FJOIN_RX_PUT、別ブロック間の IRQ（"no delay penalty … observable to all state machines on the next cycle"）、CTRL.NEXTPREV_CLKDIV_RESTART、"Improved GPIO input/output delay and skew" | §11.1.1 |
| クロック分周 | "Fractional clock divider (16 integer, 8 fractional bits)" | §11.1 |
| DMA との接続 | "DMA interface (sustained throughput up to 1 word per clock from system DMA)" | §11.1 |
| 端子の範囲 | "Each PIO block is still limited to 32 GPIOs at a time, but GPIOBASE selects which 32."、RP2350A では "limited to 30 GPIOs" | §11, §11.1 |
| DMA | "The DMA can perform one read access and one write access, up to 32 bits in size, every clock cycle."、16 チャネル。"Reduced DMA request (DREQ) latency by one cycle vs RP2040." | §12.6 / p.793 |
| バス帯域 | "at a system clock of 150 MHz, the maximum sustained bus bandwidth is 3.6 GB/s" | p.23 |
| 映像出力の性能 | "PIO can sustain 360 Mb/s during the active scanline period when running from a 48 MHz system clock" | §11.1 |
| GPIO のパッド遅延（ns） | データシートに数値なし（"Improved … delay and skew" の定性記述のみ） | 未確認 |

ファミコン側の時間（NESdev Wiki。確認済）:

| 量 | 値 |
|---|---|
| マスタークロック | 21.47727273 MHz（周期 46.56 ns） |
| 画素 | 4 マスタークロック = 186 ns（186.24 ns） |
| CPU サイクル | 12 マスタークロック = 558.7 ns（M2 ≈ 1.79 MHz） |
| M2 High | 2A03E/G/H で 15/24（350 ns/559 ns）、無印 2A03 で 17/24（396 ns/559 ns）。"CPU cycles begin at the point where M2 goes low." |
| 2A03 書き込みデータ | M2 立ち上がりの約 100 ns 後に有効（lidnariq の実測、単一出典）。M2 立ち下がり後のホールド時間は未測定（未確認） |

計算値（未確認：計算のみ）:

- CPU サイクルあたりの PIO 命令数は 150 MHz で約 84、252 MHz で約 141、129 MHz で 72。画素あたりは 150 MHz で 27.9、129 MHz で 24。
- 同期回路の遅延は +2 命令（150 MHz で約 13 ns、129 MHz で約 16 ns）、バイパスで 0。
- 外部クロック（M2）に同期してサンプリングする場合は同期回路を残すのが安全である。ダンプ用途で Pico が M2 を自分で出すなら、非同期の問題自体がない。（推論）

### 1.6 クロック生成（実チップモードで CPU/PPU に 21.477 MHz を供給する場合）

| 項目 | 内容 | 確度 |
|---|---|---|
| PLL の式と制約 | "( FREF / REFDIV ) × FBDIV / ( POSTDIV1 × POSTDIV2 )"、"minimum reference frequency ( FREF / REFDIV ) is 5 MHz"、VCO "750 MHz-1600 MHz"、FBDIV "16-320"、POSTDIV1/2 "1-7"。12 MHz 水晶では FBDIV 63〜133。"Jitter decreases as VCO frequency increases" | 確認済 |
| PLL の基準 | "On both PLLs, the FREF (reference) input is connected to the crystal oscillator's XIN (XI) input." | 確認済 |
| 外部クロック入力 | XIN は 50 MHz まで。GPIN0/1 は "can provide system and peripherals clocks, but is limited to 50 MHz"（PLL の基準にはならない）。XIN は矩形波入力時 VIH 0.65×IOVDD | 確認済 |
| 精度 | "The PLLs can drive clocks at their maximum frequency as long as the reference clock is accurate to 1000ppm" | 確認済 |
| クロック出力 | GPOUT0-3 は GPIO13/15/21/23/24/25 などの CLOCK 機能。Pico 2 のヘッダに出るのは GPIO13/15/21 | 確認済 |
| USB ブートとクロック | USB ブートモードは既定で 12 MHz 入力に依存（OTP で上書き可） | 確認済 |
| **Pico 2 で外部 21.477 MHz を PLL 基準にできるか** | **モジュールを改造しない限りできない**（XIN は基板上の 12 MHz 水晶に接続済み）。Pico 2 で CPU/PPU と完全同期させる唯一の方法は、RP2350 がクロックを出す側になること | 確認済（データシートからの帰結） |
| 12 MHz から整数分周で得られる最良値 | 21.500000 MHz（+1058 ppm）。clk_sys 129 MHz（FBDIV=129, VCO 1548 MHz, POSTDIV 6×2、または FBDIV=86, VCO 1032 MHz, POSTDIV 4×2）を ÷6 | 未確認（計算値） |
| 次点 | 150 MHz ÷7 = 21.428571 MHz（−2268 ppm、デューティ 4:3）。規格外を許せば 279 MHz ÷13 = 21.461538 MHz（−733 ppm） | 未確認（計算値） |
| +1058 ppm の影響 | 画素 5.375 MHz、ライン 15.762 kHz（公称 15.746 kHz）、フレーム 60.16 Hz（公称 60.10 Hz）、ゲーム速度 +0.106%、音程 +1.83 セント。色副搬送波は 3.5833 MHz（+3.8 kHz）でコンポジットの色は出ない（RGB なら無関係） | 未確認（計算値） |
| 前例 | Hi-Def NES は CPU/PPU を約 0.15% 下げて製品化（"The NES is very very slightly underclocked to do this, around 0.15%."）。TinyNES は 3.3V の MEMS 発振器 SIT2001BC-S2-33N-21.477270 → クロックバッファ PL133-37TC → 30 Ω（R3-R5）で CPU と PPU の CLK を駆動 | 確認済 |
| 2A03 の低速クロック | NMOS のため低速（DC）クロック不可。内部 6502 は入力クロックの 1/12 で動き、約 12 MHz 以上の供給が必要。ATmega＋シリアルでのサイクル毎駆動は速度不足でリセットベクタに届かなかった | 単一出典 |
| RP2350 PLL の出力ジッタ値 | データシートに数値なし | 未確認 |

- RP2350 が CPU/PPU のクロックを出す構成では、RP2350 が止まると CPU/PPU も止まる（書き換え・ウォッチドッグ再起動時）。NMOS は低速クロック不可なので、止める前後は必ず /RST を Low に保持する。RP2350 の GPIO はリセット時にプルダウンなので、/RST を外付け 10 kΩ で Low に引いておけば、ブート中は自動的にリセットが保持される。（推論）
- 3.3V 振幅で NMOS の CLK を駆動する: RP2350 GPIO（12 mA）＋30〜33 Ω 直列で CPU・PPU を別ピン（同じ SM の side-set で同時に変化）から駆動するのが妥当。（推論、TinyNES が前例）

### 1.7 GPIO の本数（端子予算）

#### 1.7.1 エミュレーションモード（Pico 2 1 枚、5V 可 23 本＋3.3V 専用 3 本＝26 本）

| 用途 | 本数 | 5V との接続 | 備考 |
|---|---|---|---|
| RGB DAC 4 bit×3 | 12 | 不要（抵抗のみ） | GPIO26–28 の 3 本はここに回せる。3 bit×3 なら 9 本 |
| CSync | 1 | 不要 | PIO で生成（PICO9918 と同じ考え方） |
| 音声 PWM | 1 | 不要 | RC フィルタ→アンプ |
| 74HC595 チェーン（SER/SRCLK/RCLK） | 3 | 74HC を 5V 給電にすると 3.3V 入力は保証外。**74HCT595 にするか 595 を 3.3V 給電**（1.4） | カセットのアドレス 29 本・制御 6 本・コインカウンタ等 |
| CPU データ書き込み用 595 の /OE | 1 | 同上 | マッパーレジスタへの書き込み用 |
| 74HC165 チェーン（SH/LD・CLK・QH） | 3 | QH（5V）→FT ピンは可（IOVDD 給電中のみ） | CPU D0–7、PPU D0–7、CIRAM A10、JAMMA 入力 24〜28 |
| M2 直結（PIO で連続クロック） | 1 | マッパー IC の入力しきい値が未確認なので 74HCT 経由が安全 | MMC5/MMC3 のリセット検出対策 |
| **小計** | **22** | | 残り 4 本（サービス/テストスイッチ直結、/IRQ 監視、予備） |

（未確認：机上の割り当て。pico2_platform_verification.md §13）

#### 1.7.2 実チップモード（CPU/PPU は本物、RP2350 が RGB 化・入力・クロックを担当）

| 群 | 信号 | 本数 | 5V 入力（FT 必須） | 備考 |
|---|---|---|---|---|
| バス盗聴・置換 | PPU 側 D0-D7 | 8 | ○ | 双方向。パッド応答と共用 |
| | A0-A2, R/W, PPU /CS | 5 | ○ | |
| パッド応答 | /OE1, /OE2, OUT0 | 3 | ○ | RP2350 が PPU 側 D0（必要なら D1-D4）を抵抗経由で CPU バスへ出す |
| 映像入力 | EXT0-3 | 4 | ○ | |
| | SPR 比較器 | 1 | — | |
| | （任意）ALE | 1 | ○ | 位相の自己確認 |
| | （任意）同期比較器 | 1 | — | |
| クロック・リセット | CLK（CPU/PPU を別ピンにするなら 2） | 1〜2 | — | |
| | PPU /RST, CPU /RST | 2 | — | CPU /RST を RC で兼用すれば 1 |
| 映像出力 | RGB 3-3-3 | 9 | — | 非 FT ピン可 |
| | CSYNC | 1 | — | 外付け NPN で 5V 化 |
| JAMMA 入力 | 74HC165 ×4（UDLR,A,B,Start ×2P＝14、Coin1/2・Service・Test＝4、DIP 8 → 26 入力） | 3 | — | 165 を 3.3V 給電、プルアップも 3.3V |
| JAMMA 出力 | 74HC595（Basic）でコインカウンタ×2・ロックアウト等（CLK は 165 と共用） | 2 | — | ULN2003A（Basic）で駆動 |
| 書き換え | USB | 0 | — | 専用ピン |
| **合計** | | **最小 38 ／推奨 40〜41**（任意信号をすべて入れると 42） | FT 必須 20〜21 本 | |

- 合計の注記: 元ノートは「最小 37、FT 必須 21〜22、2-2-2 で 33」と書くが、上の表を足すと最小 38（CLK 1・/RST 1・任意信号なし）、FT 必須 20（ALE を入れて 21）、2-2-2 で 35 になる。同じノートの別の節も「38〜41 本を使用」と書いているので、表の合計を採った。どの値でも Pico 2 ×1 では足りないという結論は変わらない。（未確認：机上の合計）

| 選択肢 | 使える GPIO | 判定 |
|---|---|---|
| Pico 2 ×1 | 26（FT 23） | **不足**。RGB を 2-2-2 にし任意信号を全部削っても 35 本で足りない |
| Pico 2 ×2 | 52（FT 46） | **可**。A: CLK 2, /RST 2, EXT 4, SPR 1, ALE 1, RGB 9, CSYNC 1, リンク 3 = 23。B: D 8, A0-2/RW/CS 5, /OE1/OE2/OUT0 3, JAMMA 5, リンク 3 = 24（FT 16）。A は PPU にクロックを出す側でなければならない。A と B は別のクロック領域になる |
| RP2350B ×1 | 48（FT 40） | **最も素直**。7〜10 本余り、オーバーレイや 4-4-4 RGB に回せる。PIO 12 SM のうち 8〜9 SM、命令は 96 のうち 60 前後（概算）。QFN-80 の実装を JLCPCB（Extended）に頼る |

（未確認：机上の割り当て。rgb_pico2_feasibility.md §4。JAMMA 入力・コイン・タイマー制御の詳細は別シートの範囲）

### 1.8 エミュレーション方式（起動時にカセットを読み出してから動かす）の実現条件

#### 1.8.1 カセットの信号数

| 区分 | 信号 | 本数 | 確度 |
|---|---|---|---|
| CPU 側 | A0–A14（15）、D0–D7（8）、M2・R/W・/ROMSEL・/IRQ（4） | 27 | 確認済 |
| PPU 側 | A0–A13（14）、D0–D7（8）、/RD・/WR（2）、/A13（1）、CIRAM A10・CIRAM /CE（2） | 27 | 確認済 |
| 音声 | Audio from 2A03（ピン45）・Audio to RF（ピン46） | 2 | 確認済 |
| 電源など | +5V（30）、ピン31（基板版により 5V/カセット検出）、GND（1,16）。EXP ピンはない（NES 72 ピンのみ） | — | 確認済 |
| 合計 | デジタル約 54 本（＋音声 2 本） | — | 確認済 |
| sanni Cart Reader | CPU と PPU のアドレス・データを同じポートに束ね、アドレス 15＋データ 8＋制御 8＋CIRAM A10 1＝**32 本** | — | 単一出典（コードからの読み取り。アダプタの回路図は未確認） |

- 本基板では実チップモードのために CPU バスと PPU バスを分けておく必要があるので、sanni のようにダンプ用に束ねることはできない。（推論）
- 54 本は Pi（28 GPIO）、Pico 2（26 本）、RP2350B（48 本）のどれでも直結では足りない。（確認済：本数の比較）

#### 1.8.2 端子の増やし方（シフトレジスタ）

秋月の汎用シフトレジスタ（2026-11-10 取得。確認済）:

| 品名 | 型番 | 販売コード | 価格（税込） | 通販在庫 |
|---|---|---|---|---|
| 8ビットシフトレジスター（DIP） | TC74HC595AP(F) | 131760 | ¥110 | 748 個 |
| 8ビットシフトレジスター（SOP） | TC74HC595AF | 110077 | ¥50 | 2,540 個 |
| 8ビットシフトレジスター | U74HC595AG-D16 | 114053 | ¥40 | 500 個（"2月中旬入荷予定" 表記あり） |
| 8ビットシフトレジスター（DIP） | TC74HC165AP(F) | 114679 | ¥100 | 1,010 個 |

構成例（未確認：机上の構成）:

- 74HC595 × 5 段（SER/SRCLK/RCLK = 3 本）で CPU A0–A14（15）＋PPU A0–A13（14）＋M2・R/W・/ROMSEL・PPU /RD・PPU /WR・PPU /A13（6）＝ 35 ビットを出す。
- CPU D0–D7 の書き込み用に 74HC595 を 1 段足し、/OE を GPIO 1 本で制御する。
- 読み取りは 74HC165 × 2 段（データ）＋JAMMA 入力 24〜28 本分 3〜4 段を SH/LD・CLK・QH の 3 本で読む。
- **計 7 本**でカセットの全信号と JAMMA 入力を扱える。ダンプは静的な動作（M2 も /ROMSEL も低速でよい）なので 595 の出力で足りる。
- ただし MMC5 のように M2 のパルスで状態を検出するマッパーや、M2 の停止をリセットとみなすマッパーがあるので、M2 は GPIO に直結して PIO で連続クロックを出すほうが確実である（+1 本で **8 本**）。
- 高速化: CPU D0–D7 を FT GPIO に直結（+8 本、165 不要）、アドレス下位 8 ビットだけ別チェーンにする等で 1〜2 µs/バイトまで縮む。
- 実チップモードと両立させるには、カセットのアドレス線を駆動するシフトレジスタの出力を、実チップモードの間は /OE で Hi-Z にしておく必要がある。（推論）

#### 1.8.3 マッパーの判別（sanni Cart Reader の方式）

| 項目 | 内容 | 確度 |
|---|---|---|
| 判別法（`getMapping()`） | CPU $8000–$9FFF の 8 KB と $E000–$FFFF の 8 KB をそれぞれ CRC32 し、SD カードの `nes.txt` の 8 KB CRC 欄と照合（どちらかが一致すればよい）。コメント "Some mappers (like MMC3) map the last 8KB block of PRG ROM to 0xE000 while 0x8000 can contain random data after bootup" | 確認済（ソースコード） |
| 一致しないとき | 両方 0xFF（CRC 0xBD7BC39F）なら "No data found. Using manual selection"、見つからなければ "CRC not found in database / Using manual selection" | 確認済 |
| データベース `nes.txt` | 22,143 行（1 エントリ 3 行 → 約 7,380 エントリ）。例 "AA421A37,61BC931A,4E45531A34015008000F000700000001" | 確認済 |
| 対応マッパー表 `mapsize[]` | 196 エントリ（0〜999 の iNES 番号、PRG/CHR/RAM サイズ範囲付き） | 確認済 |
| PRG 読み出し `read_prg_byte()` | MODE_READ → PRG_READ（R/W=High）→ ROMSEL_HI → set_address → PHI2_HI → A15 なら ROMSEL_LOW → `_delay_us(1)` → 読む | 確認済 |
| CHR 読み出し `read_chr_byte()` | PHI2_HI → ROMSEL_HI → set_address → CHR_READ_LOW（PPU /RD=Low）→ `_delay_us(1)` → 読む → CHR_READ_HI | 確認済 |
| 書き込み `write_prg_byte()` | PHI2 Low → データ出力 → アドレス → PHI2 High → /ROMSEL → 1 µs → PHI2 Low → 1 µs → /ROMSEL High → 読み出しモードへ → "Set phi2 to high state to keep cartridge unreseted" | 確認済 |
| 特殊処理 | MMC1 用 5 ビットシリアル書き込み、MMC5 の M2 パルス（`dumpPRG_pulsem2`）、Bandai 24C01/24C02 EEPROM 用ビットバング関数 | 確認済 |
| 使用信号（`setup_NES()`） | "CPU R/W, IRQ, PPU /RD, PPU /A13, CIRAM /CE, PPU /WR, /ROMSEL, PHI2"（PORTF の 8 本）、"A0-A7"（PORTL）、"A8-A14"（PORTA）、"D0-D7"（PORTK）、CIRAM A10 入力（PORTC、内部プルアップ）。PPU /A13 だけ別ピンで反転出力 | 確認済 |
| リポジトリ | NES.ino の最終コミット 2026-03-07。"archived by the owner on Jun 15, 2026"（読み取り専用）。GPL-3.0 | 確認済 |
| ClusterM famicom-dumper-client | マッパーごとの C# スクリプト（`IMapper`）で PRG/CHR ダンプとミラーリングを定義。既定は mapper 0、自動マッパー検出の記載なし。バッテリー PRG-RAM 読み書き、FDS 対応。GPL-3.0。ハードは famicom-dumper-writer（STM32F103 の FSMC＋EPM3064 CPLD、"this device is very fast"） | 確認済 |
| dumping.guide | ダンプ前にデータベースからマッパーとサイズ情報を得る必要がある | 単一出典 |
| Retro Freak（CYBER Gadget） | カセットからゲームを SD カードに吸い出して本体にインストールできる（販売店記載）。マッパー対応表は見つからない | 単一出典 |

- マッパー判別は「CRC → データベース」が実績のある唯一の汎用手段である。データベースは約 7,400 件 × 約 12 バイト ≈ 90 KB でフラッシュに置ける。未登録のカセットは「判別不能」として起動しない設計が無難である。（推論）
- NES 2.0 XML データベース（nes20db）のライセンスと取得 URL は未確認。

#### 1.8.4 日本のライセンス品カセットのマッパー別本数（nesdir の Region=Japan 881 本を集計）

| iNES mapper | 主な基板 | 本数 | 割合 | 累積 |
|---|---|---|---|---|
| 1 | MMC1 (HVC-S*ROM) | 236 | 26.8% | 26.8% |
| 4 | MMC3 (HVC-T*ROM) | 142 | 16.1% | 42.9% |
| 0 | NROM | 110 | 12.5% | 55.4% |
| 2 | UNROM | 83 | 9.4% | 64.8% |
| 3 | CNROM | 57 | 6.5% | 71.3% |
| 206 | Namco 108 系 | 30 | 3.4% | 74.7% |
| 19 | Namco 163（拡張音源あり） | 20 | 2.3% | 77.0% |
| 16 | Bandai FCG / LZ93D50(+24C02) | 15 | 1.7% | 78.7% |
| 18 | Jaleco SS88006 | 15 | 1.7% | 80.4% |
| 5 | MMC5 | 14 | 1.6% | 82.0% |
| 210 | Namco 175/340 | 12 | 1.4% | 83.3% |
| 23 | Konami VRC2/VRC4 | 10 | 1.1% | 84.4% |
| 87 | Jaleco/Konami 簡易 | 10 | 1.1% | 85.6% |
| 33 | Taito TC0190 | 9 | 1.0% | 86.6% |
| 69 | Sunsoft FME-7 / 5A / 5B | 9 | 1.0% | 87.6% |
| 185 | CNROM+保護 | 7 | 0.8% | 88.4% |
| 25, 66, 75, 32, 80 | VRC4/GxROM/VRC1/Irem G-101/Taito X1-005 | 各 6 | 各 0.7% | 91.8% |
| 152, 159, 82 | — | 各 4 | — | 93.2% |
| 68, 184, 7, 140, 65, 88, 10, 72 | — | 各 3 | — | 95.9% |
| 118, 48, 26, 70, 93, 67, 21, 22, 78, 85 | — | 各 2 | — | 98.2% |
| 24, 180, 154, 95, 207, 97, 34, 76, 9, 86, 92, 77, 96, 73, 94, 89 | — | 各 1 | — | 100% |

- 全 58 種。上位 5 種=71.3%、10 種=82.0%、15 種=87.6%、20 種=91.8%。（確認済：nesdir の実データ集計）
- 標本の限界: 国内市販 ROM カセットは「市販のファミコンカセット全1053本」（ねとらぼ 2021-07-20）なので、集計は約 84%（881/1053）の標本で、未収録の約 170 本の分布は不明。nescartdb.com は Cloudflare によりアクセス拒否（2026-11-10）。（確認済：標本数。未収録分の分布は未確認）
- サイズの検証: Mesen2 の `MesenNesDB.txt`（"Generated on 2022-07-21 …"）と CRC で突合し、881 件中 871 件で PRG/CHR サイズが一致、7 件不一致（版違いと推定）、3 件は nesdir が 404 のため Mesen DB で補完。（確認済）
- 上記 58 種は**すべて pico-infonesPlus の MapperTable に登録がある**（85 は RP2350 ビルドのみ）。ただし登録＝完全動作ではない。（確認済：ソースコードとの突合）
- 対応マッパーの数 N は、ダンプ用のバンク切り替えドライバとエミュレータ側の実装の両方で決まる。（推論）

拡張音源・特殊マッパーを使う主な日本タイトル（確認済：nesdir）:

| 種別 | mapper | タイトル（基板） |
|---|---|---|
| Konami VRC6 音源 | 24 / 26 | 悪魔城伝説 Akumajou Densetsu (KONAMI-VRC-6, 24)、魍魎戦記MADARA、エスパードリーム2 (26) |
| Konami VRC7 FM 音源 | 85 | Lagrange Point（VRC7 音源使用）、Tiny Toon Adventures 2（同チップ。音源使用の有無は未確認） |
| Namco 163（音源内蔵チップ） | 19 | 20 本（NAMCOT-163、Star Wars のみ NAMCOT-129）。各タイトルが実際に拡張音源を鳴らすかは未確認 |
| Sunsoft 5B 音源 | 69 | Gimmick!（SUNSOFT-5B）。同 mapper の他 8 本は FME-7/5A で音源なし |
| MMC5 | 5 | 14 本（光栄の歴史 SLG 多数、Just Breed、Metal Slader Glory 等） |
| EEPROM セーブ（24C01/24C02） | 16 / 159 | Bandai: ドラゴンボールZ 系、SDガンダム外伝 ナイトガンダム物語 1〜3、ロクでなしBLUES 等 |
| バッテリーバックアップ（Mesen DB の Battery フラグ） | 各種 | 881 本中 217 本（SaveRam 8 KB: 187、32 KB: 5、2 KB: 3、4 KB: 1、0（EEPROM 等）: 21） |

#### 1.8.5 メモリ容量

| 項目 | 値 | 確度 |
|---|---|---|
| PRG+CHR 合計 ≤256 KB | 759 本（86.2%） | 確認済 |
| ≤384 KB | 826 本（93.8%） | 確認済 |
| ≤512 KB | 873 本（99.1%） | 確認済 |
| ≤768 KB | 880 本（99.9%） | 確認済 |
| ≤1024 KB | 881 本（100%） | 確認済 |
| PRG 単体 | 8 KB〜512 KB（最多 128 KB: 496 本） | 確認済 |
| CHR | 0（CHR-RAM、208 本）〜256 KB | 確認済 |
| 最大 | Metal Slader Glory（MMC5 / HVC-ELROM、PRG 512 KB + CHR 512 KB = 1 MB）。768 KB 級: 青き狼と白き牝鹿 元朝秘史、星のカービィ 夢の泉の物語、Just Breed、信長の野望 武将風雲録（各 512+256） | 確認済 |
| RP2350 SRAM | 520 kB | 確認済 |
| Pico 2 フラッシュ | 4 MB（W25Q32RV） | 確認済 |
| フラッシュ書き換え耐性 | W25Q32JV（Pico 2 の W25Q32RV とは別品種、参考値）: "Min. 100K Program-Erase cycles per sector"、"More than 20-year data retention"、tPP 0.4 ms typ / 3 ms max（256 B ページ）、tSE（4 KB）45 ms typ / 400 ms max、tBE2（64 KB）150 ms typ / 2,000 ms max。W25Q32RV のデータシートは取得できず | 単一出典（参考品） |
| PSRAM | 秋月で入手不可（1.1.2） | 確認済 |

- エミュレータの作業領域（フレームバッファ、CHR-RAM 8 KB、WRAM 8 KB、音声バッファ等）を考えると、SRAM に PRG+CHR を置けるのは 256 KB 程度まで（日本カセットの 86%）。それ以上の 14% はフラッシュ（XIP）に書く。（推論）
- フラッシュの摩耗: 電源投入ごとに無条件に書き直しても 100K 回 ÷ 1 日 1 回 ≒ 270 年、1 日 10 回でも約 27 年。「ダンプの CRC がフラッシュ上の既存イメージと同じなら書かない」にすれば、実際の書き込みはカセット交換時だけになる。（推論・計算値）
- フラッシュへの書き込み時間: 512 KB で 64 KB ブロック消去 8 回（typ 1.2 s）＋2048 ページ（typ 0.8 s）≈ 2 s（typ）、最悪値では 16 s＋6 s。（未確認：計算値）
- pico-infonesPlus も PSRAM がない場合は "the ROM is written to flash memory during startup … taking several seconds"、PSRAM があれば "Games are loaded directly from the SD card into PSRAM"。（確認済）

#### 1.8.6 ダンプの所要時間（計算値、実測なし）

| 条件 | 値 | 確度 |
|---|---|---|
| 1 バイトあたりのシフト量 | 595 チェーン 48 ビット＋165 チェーン 16 ビット ≈ 64 クロック | 未確認（計算値） |
| PIO で 10 MHz シフト（74HC の 4.5V 規格 21〜25 MHz の半分以下） | 約 6.4 µs＋1 µs のアクセス待ち ≈ 7.5 µs/バイト | 未確認（計算値） |
| 256 KB（日本カセットの 86%） | 約 2.0 s | 未確認（計算値） |
| 512 KB（99%） | 約 3.9 s | 未確認（計算値） |
| 1 MB（Metal Slader Glory） | 約 7.9 s | 未確認（計算値） |
| シフトを 2 MHz に落とした場合 | 512 KB で約 17 s | 未確認（計算値） |
| データ線を直結した場合 | 1〜2 µs/バイト、256 KB で 0.5 s 前後 | 未確認（計算値） |
| 既存ダンパの実測値（sanni / ClusterM） | 公開値なし | 未確認 |

#### 1.8.7 ダンプ方式の制約

- バッテリーバックアップ SRAM は、実カセットの SRAM を直接使えない（エミュレータ側のコピーになる）。起動時に読み込み、定期的に書き戻す必要がある。電源断では書き戻せない。（推論）
- 拡張音源（VRC6/VRC7/MMC5/N163/5B/FDS）はエミュレータ側で再現する必要がある。（推論）
- 独自マッパー・海賊版マッパーはデータベースの外にある。（推論）

### 1.9 既存の Pico 用ファミコンエミュレータと 15kHz RGB の実例

#### 1.9.1 エミュレータ

| 名称 | 対応チップ | 映像・音声 | ROM の置き場 | ライセンス | 確度 |
|---|---|---|---|---|---|
| pico-infonesPlus（リポジトリは PicoPlus-devel 組織へ移管、旧 fhoedemakers/pico-infonesPlus） | RP2040 と RP2350（Pico/Pico W/Pico 2/Pico 2 W、Pimoroni Pico Plus 2、Adafruit Fruit Jam、Waveshare RP2350-PiZero 等） | HDMI（DVI/HSTX）のみ。README 全文に "VGA" の語はない（grep 0 件）。音声は HDMI または "External Audio | Route audio to the I2S/line-out output instead of HDMI." | SD カード（FAT32/exFAT）。PSRAM なしではフラッシュへ書き込み（数秒）、PSRAM ありなら PSRAM へ | GPL-3.0（LICENSE: "GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007"） | 確認済 |
| pico-infones（shuichitakano） | RP2040 | HDMI で映像と音声（PicoDVI ベース、Pico-DVI-Sock ピン配置） | `picotool load foo.nes -t bin -o 0x10080000` でフラッシュへ、標準 Pico で 1.5 MiB まで。SRAM はタイトルごと 8 KB をフラッシュに保存 | GPL-3.0 | 単一出典 |
| xrip/pico-nes | RP2040（MURMULATOR 開発ボード） | VGA（31 kHz）、microSD | microSD | GPL-3.0 | 単一出典 |
| Ben Stragnell の Pico NES エミュレータ | RP2040 | VGA と PWM 音声 | 未確認 | 未確認 | 単一出典（二次資料） |

pico-infonesPlus の詳細:

| 項目 | 内容 | 確度 |
|---|---|---|
| 最新リリース | v0.56（"v0.56 adds support for the Pico Computer 3."、リリースページの日時 2026-11-08） | 確認済 |
| 動作クロック | "The emulator overclocks the Pico in order to get the emulator working fast enough."、"Overclock | Raise the CPU clock from 252 MHz to 384 MHz. Only on HSTX boards with PSRAM, and currently only needed for Lagrange Point (JP)."（定格 150 MHz に対し 252 MHz は 1.68 倍） | 確認済 |
| 150 MHz（定格）で全速動作するか | 不明 | 未確認 |
| 対応マッパー（`infones/InfoNES_Mapper.cpp` の `MapperTable[]`、計 157 エントリ。`{6, Map6_Init}` はコメントアウト、`{85, Map85_Init}` は `#if PICO_RP2350` 内） | 0 1 2 3 4 5 7 8 9 10 11 13 15 16 17 18 19 20 21 22 23 24 25 26 30 31 32 33 34 37 40 41 42 43 44 45 46 47 48 49 50 51 57 58 60 61 62 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 82 83 85(RP2350のみ) 86 87 88 89 90 91 92 93 94 95 96 97 100 101 105 107 108 109 110 111 112 113 114 115 116 117 118 119 122 133 134 135 140 151 152 153 154 155 157 159 160 180 181 182 183 184 185 187 188 189 191 193 194 196 200 201 202 206 207 208 210 222 225 226 227 228 229 230 231 232 233 234 235 236 240 241 242 243 244 245 246 248 249 251 252 255 263 268 555 | 確認済（ソースコード） |
| 登録と完全動作の違い | README "some mappers are either not fully implemented or exceed memory limitations"。セーブステートは "mapper 0,1,2,3 and 4" のみ保証。未対応マッパーは "Mapper n is unsupported." と表示 | 確認済 |
| 拡張音源 | "VRC7 expansion audio requires an RP2350 board. MMC5, VRC6, FDS and Sunsoft 5B expansion audio also work on the RP2040."、VRC7 は "only works on HSTX boards with PSRAM and requires the Overclock setting … occasional glitches" | 確認済 |
| FDS | "FDS games run on both RP2040 and RP2350 boards"、BIOS は利用者が用意（`/bios/fds-bios.rom`、8 KB） | 確認済 |
| 地域 | RP2350 は PAL "✓ (native speed)"、RP2040 は "PAL/Dendy games at 60Hz instead of 50Hz" | 確認済 |
| 設定 | "Display Mode" に DVI/HDMI、"Scanline Type … HSTX boards only" | 確認済 |
| 精度（テスト ROM 通過率） | 資料なし | 未確認 |

- **15kHz アナログ RGB 出力と実カセット読み込みの両方を持つ既製の Pico 用エミュレータは見つからなかった**（第 1 パス、第 2 パスとも同じ結論）。映像出力部の差し替えと、ダンプしたデータをメモリに置く処理の追加が必要である。（確認済：探索結果。2 回の独立した探索）
- GPL-3.0 なので、pico-infonesPlus を改造して基板に載せる場合、配布するファームウェアのソースコードも GPL-3.0 で公開する義務が生じる。（推論。ライセンス条件の法的な確認は別シートの範囲）

#### 1.9.2 Pico で 15kHz の RGB を出す実例

| 実例 | 内容 | 確度 |
|---|---|---|
| PICO9918（visrealm、RP2040/RP2354A で TMS9918A を置換） | ハード CERN-OHL-S、ファーム MIT。v2.0 回路図（Date 2026-03-09、Rev 2.0）で各色 4 ビットの重み付け抵抗 DAC: R0=3.9 kΩ、R1=1.8 kΩ、R2=910 Ω、R3=470 Ω（G/B も同値。R11/R1/R7/R18 ほか 12 本）を GPIO から出力ノードへ並列接続。HSYNC/VSYNC は各 47 Ω 直列（R28/R23） | 確認済（回路図） |
| PICO9918 の VGA | 640×480@60 Hz、25.175 MHz、"12-bit RGB (4 bits per channel, 4096 colors)" | 確認済 |
| PICO9918 の SCART（15 kHz） | "Both modes use interlaced output at 13.5 MHz pixel clock"、PAL 720×576i ライン周波数 15,625 Hz／NTSC 720×480i 15,734 Hz、システムクロック 270 MHz または 324 MHz（13.5 MHz の整数倍）。"Composite sync is driven on pin 8"（HSYNC ピンから CSync）、"The RGB outputs are held at 0 V for the whole sync pulse and back porch … The firmware does this itself."、RGB ピーク 0.7V、Sync 0V／Black 0.3V、全線 75 Ω 終端。SCART ドングルは HSYNC–VSYNC 間 1 kΩ だけの受動品（ブート時に導通で検出） | 確認済 |
| PICO9918 の注意 | SCART 出力は 480i/576i の**インターレース**で 240p ではない。JAMMA 用 240p の直接の前例ではない。抵抗値は 75 Ω 終端で 0.7V を狙った値なので、正極性約 3 Vp-p・約 2 kΩ の日本の JAMMA には低い | 確認済（インターレース）／推論（レベル） |
| pico-extras `pico_scanvideo_dpi` | "Highly functional and stable support for parallel RGB output and VSYNC/HSYNC/DEN/CLOCK for VGA/DPI."、"the API is subject to change"、BSD-3-Clause | 確認済 |
| scanvideo の 15 kHz 対応 | 定義済みモード（`vga_modes.c`）はすべて 31 kHz 以上（例 640×480: clock 24 MHz・h_total 800、512×576: 24 MHz・h_total 768 ≒ 31.25 kHz）。**15 kHz のプリセットはない**。`scanvideo_timing_t` のフィールドは clock_freq, h_active, v_active, h_front_porch, h_pulse, h_total, h_sync_polarity, v_front_porch, v_pulse, v_total, v_sync_polarity, enable_clock, clock_polarity, enable_den だけで、**CSync・インターレースの設定項目はない** | 確認済（ソースコード） |
| PicoVGA（codaris/picovga-cmake フォーク） | "Now supports both RP2040 and RP2350"、"TV: PAL/NTSC interlaced up to 1024×576 or 848×480"、"8-bit R3G3B2"、"take 8 resistors and connect them to outputs GP0 to GP7 and the RGB connector of a VGA or SCART TV. Then, connect HSync (CSync) to GP8"。240p プログレッシブの記載はない | 確認済 |
| RP2040 PIO のアーケード表示アダプタ（scd31） | R/G/B/HSYNC/VSYNC を CRT 向けに出す | 単一出典 |

- 実装の方針（推論）: InfoNES 系はライン単位で描画するので、VGA 版の倍線をやめて 15.7 kHz・262 ライン・60 Hz にし、CSync を PIO で合成する。scanvideo を使う場合は timing 構造体を自作（例: clock 6 MHz 前後、h_total ≈ 381、v_total 262）し、CSync は PIO の改造か外付けゲートで作る。
- 映像レベルの目標: 日本の JAMMA は正極性約 3 Vp-p・約 2 kΩ。DAC は開放 3.0V（白）・出力インピーダンス 100〜150 Ω・DC 結合を目標にする。3.3V GPIO の 3 bit 重み付け抵抗（例: 合成 ≈120 Ω になる 210/420/840 Ω 級）で 2 kΩ 負荷時 ≈3.1V になる計算。（単一出典：jamma_electrical_details.md 経由。抵抗値は推論）

### 1.10 実カセットのバスを実時間で駆動する方式の可否

| 項目 | 内容 | 確度 |
|---|---|---|
| 結論 | **採らない（成り立たない）** | 推論 |
| 公開実例 | ファミコンの CPU と PPU の両バスをマイコンで実時間に駆動した公開プロジェクトは見つからない | 確認済（探索結果） |
| 近い実例 | pico6502（eaw.app）: RP2350B を DIP-40 の外形内（52×19 mm、6 層）に収め、6502 ソケットに挿して 6502 を置換。PIO 8 SM（3 ブロック）が PHI1/PHI2 生成・アドレス・データ・IRQ/NMI 監視、Core1 が CPU エミュレーション。"complete, cycle-accurate control"。BBC Model B（2 MHz）で実機比約 97%（RP2350 340 MHz、PHYSICAL モード）。2026-10 まで更新、本体のライセンス記載なし | 単一出典 |
| 近い実例 2 | Game Bub（FPGA 携帯機、ROM とオリジナルカセットの両方を遊べる。作者は「FPGA は実機周辺とのインターフェースで有利」と述べる） | 単一出典（二次資料） |
| 理由 1: 端子 | 約 54 本は RP2350B の 48 GPIO でも直結できず、外付けラッチが必要 | 確認済（本数） |
| 理由 2: 速度 | シフトレジスタ経由では 6502 の命令フェッチごとに数 µs の往復が入り、実機の 1 命令 ≒ 1〜4 µs に対して遅すぎる。データ線とアドレス線を全部直結すれば理屈上は可能だがピンが足りない | 推論 |
| 理由 3: PPU 側 | PPU バスはおよそ 2 ドットごと（5.37 MHz ドットクロック）にフェッチがあり、MMC3 などは PPU A12 の立ち上がりを数えて IRQ を出すので、PPU のフェッチ順序をバス上で正確に再現する必要がある | 推論（NESdev の既知仕様に基づく。一次資料は未再確認） |
| 理由 4: 処理量 | pico6502 は 2 MHz の単一 CPU バスで 340 MHz のオーバークロックを要している。CPU＋PPU 2 系統を同時に駆動しつつ 15 kHz 映像を作るのは RP2350B 1 個ではかなり厳しい | 推論 |
| 実時間方式の利点 | 拡張音源をカセットのアナログ出力（ピン46）でそのまま得られる（エミュレータの APU 音をピン45 に入れ、ピン46 から取り出す） | 推論 |

- 選択肢は「SRAM に全部載る小容量は RAM、それ以上はフラッシュ XIP」の 2 段構えのダンプ方式になる。（推論）

### 1.11 「同じソケットにラズパイか CPU/PPU のどちらかを挿す」案の評価

| 項目 | 内容 | 確度 |
|---|---|---|
| DIP-40 | 0.6 in 列間隔 | 確認済 |
| Pico 2 | 40 ピン 2.54 mm ピッチ、基板幅 21 mm。列間隔は 0.7 in（17.78 mm）と言われるがデータシートで未確認 | 確認済（ピッチ・幅）／未確認（列間隔） |
| Linux Pi | 2×20 ヘッダ | 確認済 |
| 置き換える対象 | エミュレーションでは CPU と PPU の 2 個（計 80 ピン相当）を 1 枚で置き換えることになる | 確認済（ピン数） |
| 2A03 ソケットの信号 | CPU バスに加え APU 音声出力（AUD1/AUD2）、コントローラ用 OUT0–2・/OE1・/OE2、21.477 MHz 入力など | 推論（NESdev 既知仕様、未再確認） |
| PPU ソケットの信号 | PPU バス（AD0–7 多重化＋A8–13、ALE）とビデオ出力 | 推論（同上） |
| 置換の実例 | 6502 ソケット置換は pico6502 がある（RP2350B、DIP-40 外形内、現行 v2.3b は 20 ピン丸ピンヘッダ 2 本で装着、74AHCT244/245 バッファ、6 層基板）。RP2040 を 2A03 ソケットに挿す公開プロジェクトや、2A03/2C02 のソケット互換マイコン/FPGA 置換は見つからない | 確認済（探索結果） |

評価（推論）:

- 文字どおりの「共用ソケット」は成り立たない。外形・ピン配置・信号がまったく異なり、CPU と PPU の両ソケットを 1 個の RP2350B（48 GPIO）で同時に置き換えるのはピン数的に不可能に近い。RP2350B を DIP-40 内に収めるには pico6502 のように 6 層のカスタム基板が必要で、秋月で買える既製の Pico 2 では実現できない。
- エミュレーションモードでは CPU/PPU を「置き換える」必要がそもそもない。エミュレータが映像・音声・入力・カセットアクセスを全部自分で行えば、CPU/PPU ソケット周辺の 5V 回路は使わない。
- **現実的な代替案**: CPU/PPU 用の DIP-40 ソケット 2 個と、Pico 2 用のピンソケットを別の場所に並べる。マイコン（Pico 2）は両モードで常に挿しておき、モードによって役割を変える。映像・音声の出どころ（実 PPU/APU か Pico か）を切り替える。どちらのモードかは、DIP スイッチではなくファームウェアの設定か自動検出で決める（4 章）。

### 1.12 USB でのファームウェア更新

#### 1.12.1 Pico 2 / RP2350 の書き込みの仕組み

| 項目 | 内容 | 確度 |
|---|---|---|
| 書き込みモード | BOOTSEL を押したまま電源投入 → USB マスストレージとして見え、.uf2 をドラッグすると書き込み → 再起動 | 確認済 |
| ROM の保護 | "The USB boot code is stored in ROM on RP2350, so can not be accidentally overwritten." | 確認済 |
| A/B 区画 | ブート ROM がパーティションテーブルを持ち、"A/B versions to support double-buffered upgrades" | 確認済 |
| TBYB | "Try before you buy support for phased upgrades with image self-test"。新イメージが自己テスト後にコールバックしない限り旧イメージに戻る（Section 5.1, 5.1.17） | 確認済 |
| UF2 family ID | rp2040, rp2350-arm-s, rp2350-arm-ns, rp2350-riscv, data, absolute。family ID でパーティションに振り分ける | 確認済 |
| ソフトから書き込みモードへ | pico-sdk の stdio_usb: `PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE`（ホストが 1200 baud に設定すると BOOTSEL へリセット、既定値 1200）、`PICO_STDIO_USB_ENABLE_RESET_VIA_VENDOR_INTERFACE`（picotool 用リセットインターフェース） | 単一出典 |
| picotool | `picotool reboot [-a] [-u] [-g <partition>] [-c <cpu>]`、`-u` で BOOTSEL へ再起動、`-f` で強制 | 確認済 |
| ファームから直接 BOOTSEL へ入る ROM 関数（`rom_reset_usb_boot` 相当） | SDK 機能として一般的だが API 名を一次資料で再確認していない | 未確認 |
| 実例 | pico-infones の ROM 書き込みも picotool（`picotool load … -o 0x10080000`）。pico6502 は初回 USB マスストレージ、以後 OTA で 5 MB×2 パーティションを切り替え | 確認済 |
| 初代 Pico（RP2040）が A/B 区画を持たないことの明示 | データシート上の確認はしていない（RP2350 の新機能として記載があることのみ確認） | 未確認 |

#### 1.12.2 開発ツール

| ツール | 版 / 日付 | 内容 | 確度 |
|---|---|---|---|
| Raspberry Pi Pico SDK | 2.3.1 / 2026-09-04（published_at 2026-09-04T22:38:41Z） | RP2350 対応は 2.0.0（2024-08-08。リリース一覧の表示は「8月8日」だけで、年は一覧の並び順から判断）から | 確認済（2.0.0 の年は推論） |
| picotool | 2.3.1 / 2026-09-05。2.3.0 = 2026-07-03（`bdev`、`uf2 combine`） | 未インストールなら SDK の CMake が `GIT_TAG ${PICO_SDK_VERSION_STRING}` で FetchContent する | 確認済 |
| pioasm | SDK 同梱ソースからビルド（版は SDK と同じ） | ネットからの取得はない | 確認済 |
| `PICO_PLATFORM=host` | SDK 同梱 | ハードを直接触らないロジック（コイン・タイマーの状態機械など）を PC 上で単体テスト | 確認済 |
| rp2040-pio-emulator | PyPI 0.88.0 / 2026-08-28、Apache-2.0 | PIO の SM 1 個を Python で単体テスト。IRQ 命令は非対応、"a single State Machine is emulated and not an entire PIO block" | 確認済 |
| rp2040js | npm 1.4.1 / 2026-10-18、MIT | RP2040 全体の JS エミュレータ。RP2350 対応の記述なし | 確認済 |
| Wokwi（Pi Pico 2） | CLI v0.29.1（年表示なし） | PIO 3 ブロック、DMA 16ch を模擬。**Arm コア 1 つだけ**、RP2350 固有の PIO 命令はない。CI は無料で 30 日 50 分、トークン必須 | 確認済 |
| Pico SDK でのビルド・UF2 生成の実地確認 | 本プロジェクトの環境ではまだ実施していない（権限で拒否、toolchain_smoke_test.md） | 未確認 |

- どのシミュレータも外部ピンへの任意波形入力やナノ秒精度の位相検証には向かない。PIO 命令は rp2040-pio-emulator、状態機械は host platform、統合試験は実機とロジックアナライザ、の 3 層で試験する。（推論）

#### 1.12.3 USB Type-C 端子の部品

| 調達先 | 品名 / 型番 | 番号 | 価格 | 在庫 | 確度 |
|---|---|---|---|---|---|
| 秋月 | USB Type-C (USB2.0 16P) 5077CR-16-SMC2-BK-TR | 114356 | ¥110 | 209（在庫僅少） | 確認済 |
| 秋月 | USB Type-C 電源用 A295-CTRPB-1 / UJC-HP-3-SMT-TR | 116895 / 116438 | ¥40 / ¥90 | 19,835 / 3,727 | 確認済（電源用で USB 信号はない） |
| 秋月 | USB Type-C DIP 化（シンプル）AE-USB2.0-TYPE-C | 113080 | ¥350 | 695 | 確認済 |
| 秋月 | USB Type-C 電源用 DIP 化キット AE-USB2.0-TYPE-C-CTRPB-1 | 117123 | ¥130 | 1,246 セット | 確認済（電源用） |
| 秋月 | USB-シリアル (Type-C) AE-CH340E-TYPEC | 114745 | ¥550 | 1,287 | 確認済 |
| JLCPCB / LCSC | USB-C 16P | C393939 | JLCPCB $0.0691（1 個〜）、LCSC $0.0628（10 個〜） | JLCPCB 340,763、LCSC 329,380 | 確認済（JLCPCB と LCSC の直接照会、parts_class_reverification.md。分類は Extended） |
| — | USB ハブ IC | 未確認 | 未確認 | 未確認 | 未確認（調査ノートに記載なし） |
| — | Type-C→Micro-B の短いケーブル | 未確認 | 未確認 | 未確認 | 未確認 |

#### 1.12.4 Type-C 端子への引き出し方（user_requirements.md の 3 候補）

| 方法 | 内容 | 利点 | 欠点 | 確度 |
|---|---|---|---|---|
| (1) チップ直載せ | RP2350 を基板に直接実装し、Type-C 端子を直結する | 配線が最も素直。全部を基板実装メーカーに任せられる | チップと端子が Extended 部品。フラッシュ・水晶・3.3V 電源も自分で設計する | 推論 |
| (2) モジュール直付け | Pico 2 を基板に直接はんだ付けし、裏面のテストパッドを基板側の穴越しにはんだ付けして Type-C 端子へつなぐ | 部品追加が少ない | 手作業が難しく、Pico 2 の差し替えができなくなる | 推論 |
| (3) ケーブル中継 | 基板に Type-C 端子を置き、Pico 2 の Micro-B 端子へ短いケーブルで中継する | Pico 2 をソケットで差し替えられる | ケーブルとコネクタの嵌合が振動で緩む恐れ。ケーブルの調達先は未確認 | 推論 |

#### 1.12.5 複数枚のマイコンをまとめて更新する方法

調査ノートに一次資料のある方法はない。以下はすべて推論で、実現性は未確認である。

| 方法 | 仕組み | 利点 | 欠点 |
|---|---|---|---|
| (a) USB ハブ IC | Type-C → ハブ IC → 各マイコンの USB | 各マイコンが別々の UF2 ドライブとして見え、picotool で個別に書ける | ハブ IC の部品・在庫が未確認。各 Pico 2 の USB 信号がテストパッドにしかないので、モジュールでは配線できない（チップ直載せ向け） |
| (b) 管理用マイコンが他を書き換える | Type-C につながる 1 枚が、他の枚の更新イメージを自分のフラッシュ（UF2 family "data" の区画など）に受け取り、マイコン間のリンク線か SWD（デバッグ用の 2 線）で他の枚へ書き込む | Type-C は 1 つ、モジュールのままでよい | 書き込み手順を自作する必要がある。SWD で書く場合は管理用マイコンの GPIO を 1 枚あたり 2 本程度使う |
| (c) 各マイコンが自分で受信 | 各枚のファームに「リンク線から新イメージを受け取り、自分の A/B 区画の空き側へ書く」機能を入れる | A/B＋TBYB で失敗しても旧版に戻る | ファームが壊れた枚は受信できない。最後の手段として (b) の SWD 経路か各枚の Micro-B が必要 |

### 1.13 電源断への強さと起動時間

| 項目 | 内容 | 確度 |
|---|---|---|
| Pico 2 のブート | ROM 内のブート ROM → フラッシュの A/B 区画＋TBYB。ファイルシステムを持たない | 確認済 |
| Pico 2 の電源投入→main() | 数十 ms のオーダーと推定。データシートに数値なし | 未確認 |
| ゲーム開始までの時間（Pico 2） | カセットのダンプ時間が支配的（256 KB で約 2 s の計算値）。フラッシュへの書き込みが入る場合は 512 KB で約 2 s（typ）を追加 | 未確認（計算値） |
| Pico 2 の電源断 | フラッシュ書き込み中（カセット交換直後や設定保存時）以外は、電源断で壊れる要素がない。書き込み中の断も「書き込み完了フラグ＋CRC 検査で起動時に再ダンプ」で回復可能 | 推論 |
| SRAM セーブ・設定の保存 | 内蔵フラッシュに書くなら 2 セクタ交互書き＋CRC で電源断に耐える方式にする | 推論 |
| Linux Pi の起動（instant-pi、電源投入→ユーザ空間、±0.3 s） | Pi Zero W で "RPi OS Full 70 / Buildroot 10.5 / Buildroot Instant Pi 4.7 / CD Bootloader Overhead 4.1" 秒、Pi 1B で 77 / 13.0 / 5.9 / 4.3 秒。Pi Zero 2 W と 4B は空欄 | 単一出典 |
| Linux Pi の起動（furkantokac、Pi 3、高速度カメラで計測、2021-03-29） | "Linux shell in 1.75 seconds, power-up to Qt (QML) application in 2.82 seconds"。内訳: Raspberry boot stage 1.25 s（変更不可）、start.elf 0.25 s、kernel 0.25 s、init 0、Qt アプリ 1.07 s。既定 Buildroot では合計 10.17 s | 単一出典 |
| Pi Zero 2 W の起動 | Pi 3 と同系 SoC（BCM2710A1）なので Buildroot 最小構成で 2〜5 秒、Raspberry Pi OS Lite なら数十秒が目安。実測は見つからない | 未確認 |
| Linux Pi の読み取り専用化 | raspi-config の Overlay File System（`sudo raspi-config nonint do_overlayfs`）で root を読み取り専用化できる。Bookworm では /boot 以外の全マウントが読み取り専用になるとの報告、Pi 5 64-bit では挙動差の報告あり。それでも SD カードのコントローラ自体の電源断耐性に依存する | 確認済（機能）／推論（耐性） |

### 1.14 Linux が動く Raspberry Pi の映像・入出力（参考）

| 項目 | 内容 | 確度 |
|---|---|---|
| DPI | GPIO Bank0 ALT2: GPIO0=PCLK、GPIO1=DE、GPIO2=VSYNC、GPIO3=HSYNC、GPIO4–27=DPI_D0–D23。`rgb666-padhi` は "Change to RGB666 output on GPIOs 0-9, 12-17, and 20-25"。I2C/SPI と競合するので `dtparam=i2c_arm=off`、`dtparam=spi=off`。Bookworm 以降は `vc4-kms-dpi-generic` overlay | 確認済 |
| Pi 5（RP1） | 240p・288p のプログレッシブは当初から対応。インターレースは RP1 の PIO（4 SM 中 2 個）で追加。CSync は「改造ハードと GPIO1 に DE を出さないピン設定」が必要（実験的）。PIO タイミングのジッタ最大 ±5 ns | 確認済 |
| Pi2Jamma | 映像は VGA666 回路（GPIO4–21）＋THS7314、`dtoverlay=vga666`、`dpi_mode=87`、`hdmi_timings=320 1 16 30 34 240 1 2 3 22 0 0 0 60 0 6400000 1`。入力は 74LS165×3 で 24 入力。音声は 3.5 mm 出力→LM380N 2.5 W。Pi 3 以上が必要。回路図・ライセンスの公開記載なし | 単一出典 |
| Pi400RGB | `rgb666-padhi` で GPIO18/19 を空け、`dtoverlay=audremap,pins_18_19` で PWM 音声 | 単一出典 |
| 端子の余り | `rgb666-padhi` で DPI が使うのは 22 本。PCLK/DE を出さなければ 8 本空き、18/19 を音声に使うと残り 6 本。JAMMA 入力は読めるが、カセットバス（約 54 本）には足りない | 推論 |
| 秋月での Linux Pi の価格・在庫 | 調査ノートに記載なし | 未確認 |
| Linux Pi 上のエミュレータ精度 | Mesen が最も正確と広く評価。古いフォーラム投稿ではテスト通過率 Mesen 100%、Nestopia 約 80%、QuickNES 約 70%、FCEUmm 約 50%（古い数値） | 単一出典 |

### 1.15 マイコンを複数枚使う・将来更新する構成の考え方（事実の整理）

構成を決めるのに使う事実を整理する。構成の推奨は 4 章に書く。

| 事実 | 値 | 確度 |
|---|---|---|
| エミュレーションモードに必要な GPIO | 22 本（Pico 2 1 枚で足りる） | 未確認（机上の割り当て） |
| 実チップモードに必要な GPIO | 最小 38 本（元ノートの記載は 37、1.7.2 の注記）、推奨 40〜41 本（Pico 2 1 枚では足りない） | 未確認（机上の割り当て） |
| 実チップモードを Pico 2 ×2 で組む場合 | A（クロック・映像）23 本、B（バス・入力）24 本 | 未確認（机上の割り当て） |
| Pico 2 の価格 | ¥990（秋月 129604、在庫 1,462）、ピンソケット込み ¥1,240/枚 | 確認済（価格）／単一出典（ソケット込み） |
| RP2350B チップ | ¥220（秋月 130370、在庫 242）。JLCPCB での分類は未確認 | 確認済（秋月）／未確認（JLCPCB） |
| RP2350 の処理速度の余裕 | pico-infonesPlus は定格外の 252 MHz で動いている。150 MHz で全速かは未確認 | 確認済（252 MHz）／未確認（150 MHz） |
| 外付けメモリの拡張余地 | QSPI で最大 16 MB＋第 2 チップセレクトで 16 MB。秋月では PSRAM を入手できない | 確認済 |
| 別クロック領域のマイコン間通信 | B→A のイベント（パレット書き込み・$2001 変化）は SPI/UART などで送り、A が受信時刻のドット位置で適用する（$2001 の画面途中変更は数十画素の位置ずれが起こり得る） | 推論 |

---

## 2. 第1次調査からの訂正

第 1 次調査（raspberry_pi_emulation_path.md、rgb_from_rp2c02.md、rgb_round2_details.md、tooling_and_mcp.md、parts_and_manufacturing.md）の記述のうち、後の検証で訂正されたものを挙げる。

| # | 第 1 次調査の記述 | 何が誤りか | 訂正後の値 | 訂正したノート |
|---|---|---|---|---|
| 1 | 「既存 InfoNES 系はマッパー 0/1/2/3/4/5/24/69/85 等をカバー」「pico-infonesPlus の正確な対応マッパー全一覧は未確認」 | 範囲を大幅に過小評価していた | `MapperTable[]` は 157 エントリ（6 はコメントアウト、85 は RP2350 のみ）。日本ライセンス品の 58 マッパーは全部登録済み。ただし登録＝完全動作ではない | pico2_platform_verification.md |
| 2 | pico-infonesPlus の所在を GitHub の fhoedemakers/pico-infonesPlus とした | リポジトリが移管された | 現在の所在は PicoPlus-devel/pico-infonesPlus（URL は 5 章）。最新 v0.56（2026-11-08） | pico2_platform_verification.md |
| 3 | Pico 2 Datasheet の「GPIO0–25 は RP2350 無給電時も電圧を印加できる」の引用 | 引用文だけでは無給電中に 5V を掛けてよいと誤解される（第 1 次の推論自体は正しかった） | 無給電中は 3.63V まで（"3.3 V-failsafe (unpowered)"、VPIN_FT は IOVDD=0V で 3.63V）。**無給電中の 5V 印加は不可** | pico2_platform_verification.md |
| 4 | 「pico_scanvideo_dpi はタイミングを 15.7 kHz/60 Hz に変更すれば理論上流用可能」 | 設定だけでは済まない | 定義済みモードは全部 31 kHz 以上。timing 構造体に CSync とインターレースの項目がなく、HSYNC/VSYNC 別出力しかない。タイミングの自作と、CSync 用の PIO 改造か外付けゲートが必要 | pico2_platform_verification.md |
| 5 | 「PICO9918 は PIO で VGA または SCART RGB を出力」（15 kHz の前例として） | SCART 出力は 240p ではない | 480i/576i のインターレース（13.5 MHz）。JAMMA 用 240p の直接の前例ではない。RGB は 4 bit/色（3.9k/1.8k/910/470 Ω）、Sync 47 Ω、CSync は HSYNC ピンから | pico2_platform_verification.md |
| 6 | 「PRG の最終 8 KB（$8000 と、MMC3 用に $E000）の CRC32」 | 表現が不正確 | CPU $8000–$9FFF と $E000–$FFFF の 2 つの 8 KB 窓をそれぞれ CRC32 し、DB の 8 KB CRC 欄と照合（どちらかが一致すればよい） | pico2_platform_verification.md |
| 7 | 「Akizuki で入手できる Pico 2 の現行ステッピング」を部品担当の確認事項とした | — | 秋月の商品ページに記載がないことを確認（依然として未確認） | pico2_platform_verification.md |
| 8 | 「RP2350B 搭載ボードの秋月在庫・JLC Basic 可否は部品担当の確認事項」 | — | 秋月の RP2350B はチップ単体（130370、¥220）のみ。RP2350B 完成ボード・PSRAM 搭載ボードは検索で見つからない | pico2_platform_verification.md |
| 9 | rgb_round2_details.md「ADC 兼用ピン除外は未確認」 | — | RP2350 DS Table 1674 で GPIO26–29（RP2350A）が "Digital IO / Analogue"（FT ではない）と確認済み | pico2_platform_verification.md |
| 10 | 「Pico 2 案は GPIO 約 23 本でぎりぎり、ピン配分の詳細検討が必要」 | 具体的な割り当てが未検討だった | エミュレーションモードはシフトレジスタ方式で 22 本（残り 4 本）に収まる（机上） | pico2_platform_verification.md |
| 11 | 「読み出しは 1 バイト数 µs、512 KB で数秒以内」 | 根拠がなかった | 計算根拠を追加: 7.5 µs/バイトで 512 KB ≈ 3.9 s、256 KB ≈ 2.0 s。実測は依然未確認 | pico2_platform_verification.md |
| 12 | 「Pi Zero 2 W〜5 の起動時間は未確認」 | — | 一部確認: Pi Zero W 最小 4.7 s（instant-pi）、Pi 3 最小 1.75 s（shell）/2.82 s（Qt アプリ）。Zero 2 W の実測は未確認 | pico2_platform_verification.md |
| 13 | 最大システムクロックの記載なし（pico-infonesPlus の動作クロックを考慮していなかった） | 定格外動作のリスクを見落としていた | データシートの最大は 150 MHz。pico-infonesPlus は 252 MHz（定格の 1.68 倍）で動く | pico2_platform_verification.md |
| 14 | rgb_from_rp2c02.md「マスター 21.47727 MHz 発振器を CPU/PPU と MCU で共有（RP2040/RP2350 の XIN に外部クロック入力し PLL で整数倍）すれば位相固定」 | Pico 2 モジュールでは不可 | XIN は基板上の 12 MHz 水晶（ABM8-272-T3）に接続済み。GPIN0/1 は 50 MHz までで PLL の基準にならない。自作 RP2350 基板なら可能だが ×7 = 150.34 MHz は公称最大を 0.23% 超えるので ×6 = 128.86 MHz。Pico 2 で同期させるには RP2350 がマスタークロック（21.5 MHz、+1058 ppm）を出す | rgb_pico2_feasibility.md |
| 15 | rgb_round2_details.md「21.47727 MHz 発振器 1 個を CPU CLK・PPU CLK・RP2350（XIN 外部クロック or PIO 入力）に分配」 | 同上 | Pico 2 では「PIO 入力（非同期でエッジを数える）」のみ可。完全同期は RP2350 をクロック源にする構成 | rgb_pico2_feasibility.md |
| 16 | rgb_from_rp2c02.md「Pico 2 が CPU→PPU 書き込みを改変できるよう CPU–PPU 間に 74HC245 を挟む」 | 5V 給電の 74HC245 の制御入力（VIH 3.15V@4.5V〜約 3.5V@5V）は 3.3V 出力では規格外。しかも置換データは RP2350 が 3.3V で駆動するので問題は残る | 直列抵抗（470 Ω）方式のほうが部品が少なく同等以上（推論）。245 を使うなら 74HCT245（Extended）か SN74LVC4245A（Preferred） | rgb_pico2_feasibility.md |
| 17 | rgb_from_rp2c02.md「実チップモードの GPIO は 30〜35 本でオーバー」 | 本数を少なく見積もっていた | パッド応答、JAMMA 入出力、/RST 2 本、クロックを含めると最小 37 本（訂正したノートの記載。表の合計は 38 本、1.7.2 の注記）、推奨 40 本前後。Pico 2 ×1 は不可、Pico 2 ×2 か RP2350B | rgb_pico2_feasibility.md |
| 18 | rgb_round2_details.md「2C02 の出力 High は 5V 未満…74HC で受けるのはマージン不明」 | — | lidnariq の実測で VOH ≈ 4V。5V の 74HC（VIH 3.15V@4.5V）なら約 0.5〜0.85V の余裕（実測 1 例）。RP2350 FT 入力（VIH 2.0V）なら十分 | rgb_pico2_feasibility.md |
| 19 | tooling_and_mcp.md「pioasm は Pico SDK に同梱（ビルド時に取得）」 | 取得ではない | SDK ツリー内の `tools/pioasm` のソースをビルドする。ネットから取得されるのは picotool | firmware_test_and_bringup.md |
| 20 | tooling_and_mcp.md「Pico SDK: 2.3.1（年は 2026 年と推定）」 | 推定のままだった | 推定は正しかった（published_at 2026-09-04T22:38:41Z）。picotool は SDK と同じタグ（2.3.1、2026-09-05）を自動取得 | firmware_test_and_bringup.md |
| 21 | tooling_and_mcp.md「Wokwi CLI … RP2040/RP2350/PIO 対応、API トークン要否は未確認」 | — | トークンは必須（`WOKWI_CLI_TOKEN`、「wok_」で始まる）。RP2040/RP2350 とも PIO を模擬するが、コア 1 つのみ、RP2350 固有の PIO 命令はない、RP2040 の DMA は PIO 用のみ | firmware_test_and_bringup.md |
| 22 | tooling_and_mcp.md「rp2040js: 指定 URL は 404」 | 所在が誤り | 正しい所在は wokwi/rp2040js（URL は 5 章。MIT、npm 1.4.1 = 2026-10-18） | firmware_test_and_bringup.md |

ユーザー要求の更新によって前提が変わった第 1 次調査の記述（訂正ではなく、要求の変更による見直し）:

| # | 第 1 次調査の前提 | 現行の要求 | 見直しの結果 |
|---|---|---|---|
| A | 「DIP スイッチで映像・音声の出どころ（実 PPU/APU か Pico か）を切り替える」 | 方式と形式の切り替えはソフトウェアで行う（user_requirements.md 4 章） | 切り替えはファームウェアの設定（不揮発メモリ）か自動検出で行い、モード選択用の DIP スイッチはなくせる（4 章） |
| B | 「第一候補: Pico 2 1 個」「RP2350B 搭載ボードなら余裕が出る」 | Raspberry Pi は何枚使ってもよい（5 章） | 1 枚に収める制約がなくなった。役割ごとに複数枚に分ける（4 章） |
| C | 「Pico 2 の USB コネクタをキャビネット内からアクセスしやすい位置に（あるいは基板端に USB-C/Micro-B 中継）」 | USB Type-C を基板に持ち、そこから更新する（6 章） | Type-C は必須。モジュールの Micro-B だけでは要求を満たさない（1.12.4、4 章） |
| D | 「BOOTSEL を JAMMA のテスト/サービスボタンとの同時押しにする」 | 変更なし（USB で簡単に更新） | 引き続き有効な案。ただしファームから BOOTSEL に入る ROM 関数の名前は未確認 |

---

## 3. 未確認事項と実機で確かめるべきこと

### 3.1 資料で確認できなかった事項

| # | 事項 | 影響 | 確かめ方 |
|---|---|---|---|
| 1 | 秋月などで 2026 年 11 月に売られている Pico 2 / RP2350A のステッピング（A2/A3/A4） | A2 なら E9 の対策が必須。設計を A2 でも動くようにしておけば影響はない | 購入品の刻印確認、`picotool info -a`、`rp2350_chip_version()` |
| 2 | 2A03/2C02 の入力しきい値（一次資料なし）。カセット内のマッパー IC（MMC1/MMC3/VRC 等）と 74xx161/74xx32 が LS か HC か | 3.3V 直結の可否。カセット側への出力に 74HCT を入れるかどうか | 実機での電圧掃引、カセット基板の部品型番の確認 |
| 3 | pico-infonesPlus が定格 150 MHz で全速動作するか。InfoNES 系のテスト ROM 通過率 | 業務用の連続運転で定格外動作を避けられるか | 150 MHz でビルドして AccuracyCoin などのテスト ROM とフレーム時間を測る |
| 4 | Pico 2 の VSYS 投入から 3V3 確立までの時間。FT ピンに無給電で 3.63〜5V が掛かったときの電流 | 電源シーケンス回路（P-MOS 遅延投入や /OE 制御）の必要性と定数 | オシロスコープで 3V3 と 5V 側信号を同時測定 |
| 5 | Pico 2 の電源投入→main() の時間。Pi Zero 2 W の最小 Linux 起動時間 | 起動時間の見積もり | 実測 |
| 6 | シフトレジスタ方式の実ダンプ時間（第 2 パスの値は計算値） | 起動時間 | 試作でダンプ時間を測る |
| 7 | 日本カセット約 1,053 本のうち nesdir 未収録の約 170 本のマッパー分布 | 対応率の見積もり | 別のデータベース（nescartdb.com はアクセス不可）での照合 |
| 8 | Pico 2 の W25Q32RV の書き換え耐性（W25Q32JV の 100K 回を参考値として使用） | フラッシュ寿命 | W25Q32RV のデータシート入手 |
| 9 | sanni アダプタ基板で CPU/PPU バスを物理的に共通化しているか（コードからの推論のみ） | 参考情報 | 回路図の確認 |
| 10 | NES 2.0 XML データベース（nes20db）のライセンスと取得 URL | マッパー判別データベースを基板に載せてよいか | ライセンスの確認 |
| 11 | Pico 2 の USB テストパッド（TP2/TP3。名前と、テストパッドだけに出ていることは本検証で確認済み）の座標・パッド寸法 | Type-C 端子の配線方法 | Pico 2 Datasheet の SMT フットプリント図の寸法を読む |
| 12 | Pico/Pico 2 の列間隔（17.78 mm と広く言われる）の公式寸法 | フットプリント | Pico 2 の機械図面の確認 |
| 13 | ファームウェアから BOOTSEL に入る ROM 関数の API 名 | 筐体ボタンからの書き込みモード移行 | pico-sdk のソースで確認 |
| 14 | 複数枚のマイコンを 1 つの Type-C から更新する具体的な方法（USB ハブ IC の部品、SWD による書き込み、リンク線による受信） | 更新の手間 | 試作で検証。ハブ IC は部品の在庫・分類を調べる |
| 15 | JLCPCB / LCSC での RP2350B / RP2354B の分類と在庫、PSRAM の Basic 可否 | RP2350B 直載せ案の費用 | JLCPCB 部品検索 |
| 16 | RP2350 PLL の出力ジッタ値、GPIO のパッド遅延（ns） | 実チップモードのクロックとバス盗聴の余裕 | 実測 |
| 17 | 秋月 W5100S-EVB-Pico2 の "GPIO：48" 表記の真偽 | 影響小 | 製品ページ・メーカー資料 |
| 18 | Pico SDK でのビルドと UF2 生成（本プロジェクトの環境では未実施） | 開発環境の準備 | 開発者の PC でビルドする |
| 19 | GPL-3.0 のエミュレータを業務用基板に載せる場合の配布条件 | ファームの公開義務 | ライセンス担当の確認（別シート） |

### 3.2 実機で確かめるべきこと（最小の実験）

| 順位 | 確かめること | 作るもの | 測るもの | 合格の目安 |
|---|---|---|---|---|
| 1 | ダンプ方式の成立（エミュレーションモード） | Pico 2 ＋ 74HC595/165 チェーン（カセット側は 74HCT 経由）＋ファミコン 60 ピンコネクタの小基板 | MMC1・MMC3・NROM・UNROM・CNROM の実カセットのダンプ CRC がデータベースと一致するか、ダンプ時間、M2 連続クロックの有無による MMC5/MMC3 の挙動 | 上位 5 マッパーのカセットで CRC 一致、256 KB で数秒以内 |
| 2 | エミュレータの 150 MHz 動作 | Pico 2 単体＋抵抗 DAC | 150 MHz と 252 MHz でのフレーム処理時間、テスト ROM の結果 | 150 MHz で 60 fps を維持 |
| 3 | 15 kHz・240p・CSync 出力 | 同上 | 15 kHz モニタまたはスキャンコンバータ（OSSC 等）で同期するか、映像レベル（開放 3.0V・2 kΩ 負荷） | JAMMA モニタで同期・正しい色 |
| 4 | 電源シーケンス | Pico 2 の VSYS 投入から 3V3 確立までを、5V 側の信号と同時に測る | FT ピンの電圧と電流 | 3V3 確立前に FT ピンへ 3.63V を超える電圧が掛からない |
| 5 | 3.3V 駆動で NMOS 入力が動くか（実チップモード） | ドナーの CPU/PPU＋Pico 2。CLK は RP2350 から 21.5 MHz（30 Ω 直列） | 数時間の連続動作、CLK 波形、D 線の置換値の読み戻し | 0〜50 °C で誤動作なし。不合格なら 74HCT245/LVC4245A（5V 出力）に切り替え |
| 6 | 実チップモードの自動検出 | 同上 | /RST 解除後に ALE や /CS が動くかで CPU/PPU の有無を判定できるか | 挿してあるとき・ないときを毎回正しく判定 |
| 7 | 複数枚の一括更新 | Pico 2 ×2〜3 をリンク線（および SWD）でつないだ試作 | 管理用の 1 枚に UF2 を書き込んだだけで全枚が更新されるか、途中で電源を切っても復旧するか | 更新中の電源断から全枚が自動復旧 |
| 8 | ステッピングの確認 | 購入した Pico 2 | 刻印と `rp2350_chip_version()` | 記録して設計に反映（設計は A2 でも動くようにする） |

---

## 4. ユーザー要求への影響

この章の「推奨」「理由」は、ことわりのない限り筆者の**推論**である。根拠にした事実は 1 章の項目番号で示す。

### 4.1 部品選定・実装ルール（user_requirements.md 1 章）

**事実**: 秋月で買える Pico 2 は ¥990・在庫 1,462 で、手はんだの部品として十分に在庫がある（1.1.2）。RP2350A のチップは JLCPCB で Extended（1.1.3）。Type-C 端子 C393939 も Extended（1.12.3）。秋月には PSRAM、74HCT 系の DIP、74HC574（DIP）がない（1.1.2、1.4）。

**影響（推論）**:

- Pico 2 モジュールをピンソケットで手はんだする構成は「手はんだ部品は秋月で在庫があるもの」に合い、PCBA 側の部品は Basic のまま保てる。
- RP2350 を基板に直接載せる構成は、チップ・フラッシュ・水晶・電源 IC が PCBA の Extended 部品になり、「Basic のみ」から外れる。
- **Type-C 端子の要求（6 章）を満たすと、JLCPCB で Type-C 端子を実装する限り、端子自体が Extended なので「Basic のみ」は守れない。** 要求どうしの衝突としてユーザーに確認すべきである。秋月の 114356（¥110、在庫僅少 209、表面実装品）や DIP 化基板 113080（¥350）を手はんだにすれば PCBA は Basic のままにできるが、在庫僅少と手はんだ工数が代償になる。
- 3.3V→5V の境界に 74HCT を使うと、秋月の DIP では手に入らず JLCPCB では Extended になる。境界の部品を減らすには、74HC を 3.3V 給電にしてマイコン側に置き、5V 側との境界は直列抵抗と FT ピン直結で済ませる設計（rgb_pico2_feasibility.md の方針）が部品点数・種類の点で有利である。ただしカセット側の入力しきい値が未確認なので、エミュレーションモードでカセットへ出す線だけは 74HCT か LVC4245A が要る可能性が残る（3.1 #2）。

**推奨**: 第 1 版は Pico 2 モジュール（ピンソケット実装）を採用し、PCBA は Basic を中心にする。Type-C 端子と 3.3V→5V の境界部品の 2 か所だけ例外（Extended か秋月手はんだ）を認めるよう、ユーザーに確認する。

### 4.2 両方式の選択とソケット（2 章「ラズパイを挿すか CPU/PPU を挿すかを選び、DIP スイッチ等で設定」）

**事実**: 同じソケットにマイコンか CPU/PPU を挿す案は、外形・ピン配置・信号が異なり成り立たない（1.11）。エミュレーションモードは CPU/PPU ソケットを使わない（1.11）。切り替えはソフトウェアで行うのが現行の要求である（user_requirements.md 4 章）。

**選択肢**:

| 案 | 内容 | 利点 | 欠点・リスク |
|---|---|---|---|
| (a) 共用ソケット | 1 つのソケットにマイコンか CPU/PPU を挿す | 要求の文言どおり | **成り立たない**（1.11） |
| (b) 別ソケット＋DIP スイッチ | CPU/PPU 用 DIP-40 ×2 と Pico 2 用ソケットを別に置き、DIP スイッチで選ぶ | 単純 | 現行の「ソフトウェアで切り替え」に反する。部品が 1 点増える |
| (c) 別ソケット＋自動検出・設定 | (b) と同じ配置で、マイコンは常に挿しておく。電源投入時に、マイコンが CPU/PPU の /RST を解除して ALE や /CS が動くかを見て、CPU/PPU の有無を判定する。設定値（不揮発メモリ）で上書きもできる | DIP スイッチ不要。挿し間違いがない | 自動検出の確実さは未確認（3.2 #6）。CPU/PPU を挿していない端子が浮くので、プルアップ/プルダウンの設計が要る |

**推奨**: (c)。理由は、DIP スイッチをなくせて部品点数の方針に合い、現行要求の「ソフトウェアで切り替え」も満たすからである。「マイコンを挿すか CPU/PPU を挿すか」ではなく、「マイコンは常に挿し、CPU/PPU は挿しても挿さなくてもよい」と言い換えてユーザーに確認する。

### 4.3 エミュレーションモードの実現方式（2 章「Raspberry Pi 等を実装し、CPU・PPU をエミュレートさせる」）

**事実**: ダンプ方式は Pico 2 1 枚・22 本で成り立つ（1.7.1）。日本のライセンス品の 58 マッパーはすべて pico-infonesPlus に登録済み（1.8.4）。PRG+CHR が 256 KB 以下のカセットは 86.2%、512 KB 以下は 99.1%（1.8.5）。ダンプ時間は 256 KB で約 2.0 s（計算値、1.8.6）。実時間バス駆動は成り立たない（1.10）。Linux Pi は端子不足・起動時間・電源断の点で不利（1.1.1、1.13）。15 kHz RGB とカセット読み出しの両方を持つ既製のエミュレータはない（1.9.1）。

**選択肢**:

| 案 | 費用（マイコン分） | 利点 | 欠点・リスク |
|---|---|---|---|
| (a) Pico 2＋ダンプ方式＋pico-infonesPlus 改造 | ¥990＋ソケット（¥1,240/枚）＋74HC595/165 数個 | 部品が少ない。起動が速い。電源断に強い | 映像出力部の差し替えとダンプ処理を自作。定格外 252 MHz 動作のリスク。GPL-3.0 によるソース公開義務。マッパーごとのバンク切り替えドライバを書く必要 |
| (b) Linux Pi＋別マイコンでダンプ | 未確認（秋月価格はノートにない） | Mesen 等の高精度エミュレータが使える | 端子不足で 2 チップ構成。SD カードの電源断リスク。起動に数秒〜数十秒 |
| (c) 実時間バス駆動 | — | 拡張音源をカセットのまま使える | 成り立たない |

**推奨**: (a)。対応マッパーは上位 5 種（71.3%）から始め、上位 15 種（87.6%）まで段階的に増やす。ファームはまず 150 MHz で全速動作するかを確かめ（3.2 #2）、足りなければオーバークロックの温度・長時間試験を行う。データベースにないカセットは起動しない。PRG+CHR が 256 KB を超えるカセットはフラッシュ（XIP）に置き、CRC が同じなら書き直さない。

**リスクと注意**: タイマー方式で動かす市販ソフトのうち 217 本（881 本中）がバッテリーバックアップを使う（1.8.4）。業務用ではセーブの保持は必須ではないと考えられるが、セーブ RAM の扱い（毎回消すか、フラッシュに保存するか）はユーザーに確認すべきである。

### 4.4 実チップモードのマイコン構成（2 章「CPU と PPU のみをファミコンから取り外して移植」）

**事実**: 実チップモードには最小 38 本（机上の割り当て）が要り、Pico 2 1 枚では足りない（1.7.2）。Pico 2 では外部の 21.477 MHz を PLL 基準にできず、RP2350 がクロックを出す（21.5 MHz、+1058 ppm）のが唯一の完全同期構成である（1.6）。

**選択肢**:

| 案 | 費用（マイコン分） | 利点 | 欠点・リスク |
|---|---|---|---|
| (a) Pico 2 ×2（A: クロック・映像、B: バス・入力） | ¥1,240×2 = ¥2,480 | 秋月で手はんだ可。モジュールを差し替えて更新できる | 2 枚が別クロック領域で、B→A のイベント伝達に遅延が出る |
| (b) RP2350B ×1 を基板に直載せ | チップ ¥220（秋月）。PCBA の Extended 費用は未確認 | 1 クロック領域で素直。7〜10 本余る | QFN-80 の実装を JLCPCB の Extended に頼る。周辺回路の設計が増える。JLCPCB での分類は未確認 |

**推奨**: 第 1 版は (a)。理由は、マイコンは何枚使ってもよいという現行要求で枚数の制約がなくなり、秋月の手はんだ部品だけで組めて、モジュールを差し替えれば将来の更新もできるからである。(b) は量産版で Type-C 直結と合わせて検討する（4.7）。

### 4.5 動作方式と入力形式（3 章）、切り替えはソフトウェア（4 章）

**事実**: エミュレーションモードではエミュレータがパッドの状態を直接作れる。実チップモードでは、マイコン B が /OE1・/OE2・OUT0 を見て PPU 側 D0（必要なら D1-D4）を抵抗経由で CPU バスへ出し、パッドの応答を作る（1.7.2）。ファミコン本体では 368 が D0-D2（$4016）／D0-D4（$4017）だけを駆動する（単一出典：rgb_pico2_feasibility.md が famicom_hardware.md から引用）。1 ライン遅延のラインバッファ方式なら、追加部品なしで残り時間などを画面に重ねて表示できる（rgb_pico2_feasibility.md §6、推論）。

**影響（推論）**:

- タイマー方式・デフォルト形式・特殊形式の入力割り当て（3.3〜3.5）は、すべてマイコンのファームウェアの表で実現でき、ハードウェアは共通にできる。特殊形式の「左右同時」「上下同時」も、ファームが合成するだけである。
- 2P 側の START・SELECT（初代ファミコンには存在しないビット）も、マイコンがパッド応答を作るので出せる。
- タイマー方式の残り時間表示は、エミュレーションモードではエミュレータの描画に重ね、実チップモードでは映像変換の Pico A がラインバッファに重ねる。どちらも追加部品は要らない。
- 方式・形式の設定はフラッシュに保存する。2 セクタ交互書き＋CRC で電源断に耐えるようにする（1.13）。書き込み回数は設定変更時だけなので寿命は問題にならない（1.8.5）。
- 新規開発ゲームから基板への指示（OUT1・OUT2、$4016 の D1、$4017 の D1〜D4 を使う通信）は、実チップモードではマイコン B が CPU バスを盗聴して受け取る必要がある。B は 26 本中 24 本を使う予定なので、OUT1・OUT2 を見る 2 本を残りの 2 本で賄えるか確認が要る（1.7.2）。OUT1・OUT2 は 5V 信号なので FT ピン（GPIO0–22）が要る。3.3V だけの線（74HC165/595 の制御、リンク線）を GPIO26–28 に回せば FT ピンが 2 本残る計算である。エミュレーションモードではエミュレータ内で処理でき、端子は要らない。
- 方式の切り替えはファームの設定（読み方 A）と、新規開発カートリッジからの指示（読み方 B）の両方で受け付ける。市販ソフトは指示を出せないので、市販ソフトを動かすときは担当者がタイマー方式に設定する（user_requirements.md 4.2）。
- タイマー方式ではコインをゲームへ渡さず時間の加算だけに使い、通常方式ではコインを SELECT（デフォルト形式）または上下同時押し（特殊形式）として渡す。コインスイッチのパルスは長さがまちまちなので、ファームで 1 フレームより長い一定幅に整形し、連続投入は 1 枚ずつ間隔を空けて出す（user_requirements.md 3.7）。
- タイマー方式の時間切れ後の扱い（操作を止めるだけか、リセットするか）は要求で未定である。実チップモードでは CPU/PPU の /RST をマイコンが握っているので、どちらを選んでもハードウェアの追加は要らない。
- モード選択用の DIP スイッチは不要になる（4.2）。

**推奨**: 方式・形式・入力割り当ては、すべて入出力担当のマイコンのファームウェアに置き、設定は JAMMA のテストスイッチで出す設定画面と USB の両方から変えられるようにする。

### 4.6 マイコンの枚数と将来の更新（5 章「ラズパイは何枚使ってもかまいません。将来的に CPU、PPU、各種メモリのアップデートも視野に」）

**事実**: エミュレーションモードは 22 本、実チップモードは Pico 2 ×2 で A 23 本・B 24 本（1.15）。RP2350 は QSPI で最大 16 MB＋16 MB の外付けメモリを持てる（1.1.5）。RP2350 の処理能力は定格 150 MHz で、既存エミュレータは 252 MHz で動いている（1.9.1）。

**推奨する構成（推論）**: Pico 2 を 3 枚、役割ごとに分ける。

| マイコン | 実チップモードでの役割 | エミュレーションモードでの役割 | 端子の目安 |
|---|---|---|---|
| Pico A（映像） | CPU/PPU のクロック（21.5 MHz）と /RST、EXT 取り込み、シャドウパレット変換、RGB DAC・CSync 出力、オーバーレイ | エミュレータ本体（CPU/PPU/APU）、RGB DAC・CSync・音声 PWM 出力、オーバーレイ | 23〜24 本（実チップモードの割り当てに音声 PWM 1 本） |
| Pico B（バス・入力） | PPU レジスタ書き込みの盗聴と置換、パッド応答、JAMMA 入力（74HC165）・出力（74HC595）、コイン・タイマー制御 | JAMMA 入力・出力、コイン・タイマー制御（パッドの状態を Pico A へ送る） | 24 本 |
| Pico C（カセット・管理） | 待機（カセットのアドレス線を駆動するシフトレジスタは /OE で Hi-Z）。基板の Type-C につながる管理用マイコンとして、他の枚の更新と設定の保存を担う | 起動時のダンプとマッパー判別、ダンプしたデータを Pico A へ転送、管理用マイコン | 8 本（ダンプ）＋リンク＋更新用の線 |

- 理由: 映像を出す DAC を Pico A だけにつなげば、両モードで映像回路を共通にできる。エミュレーションモードで使わない Pico A の EXT・CLK・/RST 端子は空くだけである。カセットのダンプは、実チップモードでは CPU/PPU が使うバスに対して行うので、駆動回路を Hi-Z にできる専用の Pico C に分けると端子の取り合いが起きない。
- 将来の更新への備え:
  - CPU/PPU はソケット実装のままにし、代替モジュールへの差し替え経路を残す。
  - Pico はピンソケットで挿すので、RP2350 の後継モジュールや、RP2350B を載せた代替基板に差し替えられる。ピン配置が同じモジュールに限る。
  - エミュレーション側はファームウェア更新だけで仕様を拡張できる（新規開発ゲーム向けにファミコンを超える性能を足す余地）。
  - メモリについては、エミュレーションモードでは RP2350 の SRAM とフラッシュが「各種メモリ」に当たり、QSPI の第 2 チップセレクトで PSRAM を足す余地がある（ただし秋月で入手できない）。
  - 予備の拡張コネクタに、各 Pico の空き端子とマイコン間のリンク線を引き出しておく。
- 費用: Pico 2 ×3 で ¥2,970、ピンソケット込みで ¥3,720（¥1,240×3）。
- リスク: 3 枚の間の通信（リンク線、ダンプデータの転送、パッド状態の転送）の設計が増える。Pico A と Pico C の間で 512 KB を転送する時間は、リンクの速度次第で未確認である。

### 4.7 USB でのファームウェア更新と USB Type-C（2 章・6 章）

**事実**: RP2350 の書き込み機能は書き換えできない ROM にあり、A/B 区画と TBYB で更新失敗から戻れる（1.12.1）。Pico 2 の USB 端子は Micro-B で、USB の信号は 40 本の端子列に出ていない（1.1.4、未確認）。Type-C 端子は秋月 114356（¥110、在庫僅少）、JLCPCB C393939（Extended）がある（1.12.3）。複数枚の一括更新の方法には一次資料がない（1.12.5）。

**選択肢**（1.12.4 の 3 案の評価）:

| 案 | 費用 | 利点 | 欠点・リスク | 評価（推論） |
|---|---|---|---|---|
| (1) RP2350 直載せ＋Type-C 直結 | RP2350A は LCSC $1.18、Type-C C393939。他は未確認 | 配線が素直。全部を基板実装メーカーに任せられる（2 章「全部を基板実装メーカーに実装」に最も合う） | Extended 部品が増える。フラッシュ・水晶・電源の設計と検証が要る。モジュール差し替えによる更新ができない | 量産版の本命 |
| (2) Pico 2 直付け＋裏面パッド配線 | 追加ほぼなし | 部品が少ない | 手作業が難しく、量産に向かない。差し替え不可 | 推奨しない |
| (3) Type-C 端子＋Micro-B へケーブル中継 | Type-C 端子 ¥110 または DIP 化基板 ¥350＋ケーブル（未確認） | Pico 2 をソケットで差し替えられる | ケーブルの緩み。ケーブルの調達先が未確認 | 第 1 版の本命 |

**複数枚の更新（推論）**: 管理用マイコン（Pico C）だけを Type-C につなぎ、他の枚の更新イメージも Pico C が受け取って、リンク線か SWD で書き込む方式（1.12.5 (b)）を推奨する。各枚のファームには A/B 区画と TBYB を使い、失敗時は旧版に戻るようにする（1.12.5 (c) との併用）。USB ハブ IC 方式は、各 Pico 2 の USB 信号がテストパッドにしかないのでモジュール構成では使いにくく、チップ直載せの量産版で検討する。

**書き込みモードへの入り方（推論）**: 筐体のテストスイッチ・サービススイッチの同時押しを起動時に監視し、ファームから BOOTSEL へ入る。ホスト側からは 1200 baud タッチか `picotool reboot -u` でも入れる（1.12.1）。基板上にも BOOTSEL ボタン（または RUN＋BOOTSEL）を残し、ファームが完全に壊れたときの最後の手段にする。

**推奨**: 第 1 版は (3) で、Type-C 端子を管理用の Pico C の Micro-B へ短いケーブルで中継する。理由は、Pico 2 の差し替えによる将来の更新を残せ、QFN の実装設計のリスクを避けられるからである。量産版では (1) に移り、Type-C を RP2350 に直結する。どちらの版でも、更新は Type-C 1 つから全枚に行き渡る設計にする。

### 4.8 電源と 5V インターフェース（全要求に共通）

**事実**: FT ピンは IOVDD 給電中だけ 5.5V まで、無給電中は 3.63V まで（1.2.1）。Pico 2 で 5V 可は GPIO0–22（1.2.2）。3.3V 出力で 5V 給電の 74HC は規格外（1.4）。

**推奨（推論）**:

- 5V 側につなぐ線は GPIO0–22 に割り当て、GPIO26–28 は RGB DAC など 3.3V だけの用途に使う。
- FT ピンには 1 kΩ の直列抵抗を入れ、FT ピンにつながる線のプルアップは 3.3V へつなぐ。
- Pico の 3V3 を検出して P-MOS（SI2301 / AO3401A、Basic）で CPU/PPU/カセットの 5V を後から入れる。カセットへのドライバは /OE を Pico の 3V3 確立まで Hi-Z に保つ。
- CPU/PPU の /RST は外付け 10 kΩ で Low に引き、RP2350 の書き換え・再起動中もリセットを保持する。
- E9 対策として入力は外付けプルアップ（アクティブ Low）、プルダウンは 8.2 kΩ 以下にする（1.3）。
- 理由: どのステッピングでも、どの電源投入順でも、データシートの絶対最大定格の範囲に収まるからである。電源シーケンスの実測（3.2 #4）で不要と分かれば P-MOS は省ける。

---

## 5. 出典一覧

### 1 章（確定事実）

**RP2350 / Pico 2 のデータシートと公式情報**
- RP2350 Datasheet（Release 8, Build date 01/10/2026, Build version 80d627281ed5。5V 耐性、E9、PIO、クロック、メモリ、版履歴）— https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- RP2350 Datasheet（同じ build の別 URL）— https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-3-rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet（Build date 03/07/2026。GPIO、外形、電源、USB ブート）— https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- Hardware design with RP2350（水晶 ABM8-272-T3）— https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- RP2040 Datasheet（RP2040 の 5V 非耐性）— https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- Raspberry Pi 公式ブログ（2025-07-29、A4・5V 耐性・A3 在庫）— https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/
- Hackaday の A4 記事（二次資料）— https://hackaday.com/2025/07/31/raspberry-pi-rp2350-a4-stepping-addresses-e9-current-leakage-bug
- CNX Software の A4 記事（二次資料）— https://www.cnx-software.com/2025/07/29/raspberry-pi-rp2350-a4-stepping-fixes-e9-gpio-erratum-9-glitching-bugs-introduces-2mb-flash-variants/

**秋月電子・LCSC（2026-11-10 取得）**
- Raspberry Pi Pico 2（129604）— https://akizukidenshi.com/catalog/g/g129604/
- Raspberry Pi Pico 2 H（130982）— https://akizukidenshi.com/catalog/g/g130982/
- Seeed XIAO RP2350（129619）— https://akizukidenshi.com/catalog/g/g129619/
- Tiny 2350（130201）— https://akizukidenshi.com/catalog/g/g130201/
- Plasma 2350（130202）— https://akizukidenshi.com/catalog/g/g130202/
- W5100S-EVB-Pico2（130218）— https://akizukidenshi.com/catalog/g/g130218/
- RP2350A（130369）— https://akizukidenshi.com/catalog/g/g130369/
- RP2350B（130370）— https://akizukidenshi.com/catalog/g/g130370/
- RP2354A（131439）— https://akizukidenshi.com/catalog/g/g131439/
- RP2354B（131441）— https://akizukidenshi.com/catalog/g/g131441/
- RP2350A 実装基板（131106）— https://akizukidenshi.com/catalog/g/g131106/
- Pimoroni Pico LiPo - 16MB（116997）— https://akizukidenshi.com/catalog/g/g116997/
- 秋月の PSRAM 検索（他のキーワードも同じ形式）— https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=PSRAM&search=search
- TC74HC595AP(F)（131760）— https://akizukidenshi.com/catalog/g/g131760/
- TC74HC595AF（110077）— https://akizukidenshi.com/catalog/g/g110077/
- U74HC595AG-D16（114053）— https://akizukidenshi.com/catalog/g/g114053/
- TC74HC165AP(F)（114679）— https://akizukidenshi.com/catalog/g/g114679/
- 秋月 USB コネクター検索（Type-C 114356、116895、116438、113080、117123、114745）— https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=USB%E3%82%B3%E3%83%8D%E3%82%AF%E3%82%BF%E3%83%BC&search=search
- 秋月 レベル変換検索（104522、117062、115696、129507、113837）— https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%83%AC%E3%83%99%E3%83%AB%E5%A4%89%E6%8F%9B&search=search
- AE-LLCNV8（104522）— https://akizukidenshi.com/catalog/g/g104522/
- AE-TXS0104E-BO（129507）— https://akizukidenshi.com/catalog/g/g129507/
- Si5351A モジュール（110679）— https://akizukidenshi.com/catalog/g/g110679/
- TC74HCU04AP（111328）— https://akizukidenshi.com/catalog/g/g111328/
- LCSC RP2350A（C42411118）— https://www.lcsc.com/product-detail/C42411118.html
- Raspberry Pi Pico（RP2040、g116132）と Pico 用ピンソケット FH-1x20-3.2CO の価格は firmware_test_and_bringup.md と parts_round2_sourcing_and_cost.md の記載による（URL の記載なし）
- JLCPCB の Type-C C393939 の分類・在庫は parts_class_reverification.md の記載による（JLCPCB API、jlcsearch）

**ロジック IC のデータシート**
- TI SN74HC595 — https://www.ti.com/lit/ds/symlink/sn74hc595.pdf
- TI SN74HCT245 — https://www.ti.com/lit/ds/symlink/sn74hct245.pdf
- TI SN74HC245 — https://www.ti.com/lit/ds/symlink/sn74hc245.pdf
- TI SN74HC14 — https://www.ti.com/lit/ds/symlink/sn74hc14.pdf
- Winbond W25Q32JV（参考品）— https://www.winbond.com/resource-files/w25q32jv%20revg%2003272018%20plus.pdf

**ファミコン側の仕様と実測**
- NESdev Wiki: Cartridge connector — https://www.nesdev.org/wiki/Cartridge_connector
- NESdev Wiki: Talk:Cartridge connector（入力しきい値は未測定）— https://www.nesdev.org/wiki/Talk:Cartridge_connector
- NESdev Wiki ミラー: NTSC video — https://nesdev-wiki.nes.science/wikipages/NTSC_video.xhtml
- NESdev Wiki ミラー: CPU pinout — https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml
- NESdev Wiki ミラー: PPU pinout — https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml
- NESdev Wiki ミラー: Standard controller — https://nesdev-wiki.nes.science/wikipages/Standard_controller.xhtml
- NESdev フォーラム t=19483（2A03 書き込みサイクルの実測）— https://forums.nesdev.org/viewtopic.php?t=19483
- NESdev フォーラム t=19656 p.2（2A03/2C02 の VOH ≈ 4V）— https://forums.nesdev.org/viewtopic.php?t=19656&start=15
- NESdev フォーラム（TTL しきい値、famicom_electrical_and_pitfalls.md §2 経由）— https://forums.nesdev.org/viewtopic.php?f=9&p=269268
- emulationonline chiplab（2A03 は低速クロック不可）— https://emulationonline.neocities.org/systems/chiplab/experimenting-with-highspeed-chips/
- Hi-Def NES スレッド（約 0.15% 低速化）— https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- TinyNES Main Board BOM（3.3V クロック駆動）— https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_BOM.csv
- 2A03 を 3.3V CPLD で駆動した報告 — https://archive.nes.science/nesdev-forums/f9/t4698.xhtml

**カセットのダンプとマッパー統計**
- sanni Cart Reader NES.ino — https://raw.githubusercontent.com/sanni/cartreader/master/Cart_Reader/NES.ino
- sanni Cart Reader リポジトリ（アーカイブ表示）— https://github.com/sanni/cartreader
- sanni nes.txt — https://raw.githubusercontent.com/sanni/cartreader/master/sd/nes.txt
- ClusterM famicom-dumper-client — https://github.com/ClusterM/famicom-dumper-client
- ClusterM famicom-dumper-writer — https://github.com/ClusterM/famicom-dumper-writer
- dumping.guide NES — https://dumping.guide/carts/nintendo/nes
- NES Directory（日本 881 本の集計元）— https://nesdir.github.io/ ／ 例 https://nesdir.github.io/D0DF726E_Japan.html
- Mesen2 MesenNesDB.txt — https://raw.githubusercontent.com/SourMesen/Mesen2/master/UI/Dependencies/MesenNesDB.txt
- ねとらぼ「市販のファミコンカセット全1053本」— https://nlab.itmedia.co.jp/cont/articles/3322975/
- Retro Freak（販売店記載）— https://www.genkivideogames.com/cyber-gadget-retro-freak-controller-adapter-set-new-cyber-gadget-miscellaneous-hardware/cyrfb ／ https://www.nintendolife.com/news/2017/01/hardware_review_putting_the_retro_freaks_range_of_accessories_to_the_test

**エミュレータと映像出力の実例**
- pico-infonesPlus（現在の所在）— https://github.com/PicoPlus-devel/pico-infonesPlus
- pico-infonesPlus リリース — https://github.com/PicoPlus-devel/pico-infonesPlus/releases
- pico-infonesPlus README — https://raw.githubusercontent.com/PicoPlus-devel/pico-infonesPlus/main/README.md
- pico-infonesPlus MapperTable — https://raw.githubusercontent.com/PicoPlus-devel/pico-infonesPlus/main/infones/InfoNES_Mapper.cpp
- pico-infonesPlus（旧所在）— https://github.com/fhoedemakers/pico-infonesPlus
- pico-infones（shuichitakano）— https://github.com/shuichitakano/pico-infones
- xrip/pico-nes — https://github.com/xrip/pico-nes
- Ben Stragnell の Pico NES エミュレータ（二次資料）— https://www.hackster.io/news/ben-stragnell-gets-super-mario-bros-running-on-the-raspberry-pi-pico-in-a-custom-nes-emulator-6dfcc3533ee7
- PICO9918 リポジトリ — https://github.com/visrealm/pico9918
- PICO9918 v2.0 回路図 — https://github.com/visrealm/pico9918/blob/main/pcb/v2.0/pico9918_v2_0_schematic.pdf
- PICO9918 Firmware Architecture — https://github.com/visrealm/pico9918/wiki/Firmware-Architecture
- PICO9918 VGA Dongle — https://github.com/visrealm/pico9918/wiki/VGA-Dongle
- PICO9918 SCART Output Reference — https://github.com/visrealm/pico9918/wiki/SCART-Output-Reference
- PICO9918 SCART RGB AV Dongle — https://github.com/visrealm/pico9918/wiki/SCART-RGB-AV-Dongle
- PICO9918 Display Output — https://github.com/visrealm/pico9918/wiki/Display-Output
- pico-extras — https://github.com/raspberrypi/pico-extras
- pico-extras vga_modes.c — https://raw.githubusercontent.com/raspberrypi/pico-extras/master/src/common/pico_scanvideo/vga_modes.c
- pico-extras scanvideo_base.h — https://raw.githubusercontent.com/raspberrypi/pico-extras/master/src/common/pico_scanvideo/include/pico/scanvideo/scanvideo_base.h
- PicoVGA（codaris/picovga-cmake）— https://github.com/codaris/picovga-cmake
- RP2040 アーケード表示アダプタ — https://scd31.com/posts/building-an-arcade-display-adapter
- pico6502 — https://eaw.app/pico6502/
- Game Bub（二次資料）— https://hackaday.com/2025/02/15/page/2
- Lava RGB（変換部品の例、rgb_pico2_feasibility.md 経由）— https://github.com/v5100v5100/lava-rgb-kit

**USB 更新と開発ツール**
- PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE — https://sourcevu.sysprogs.com/rp2040/picosdk/macros/PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE
- pico_stdio_usb reset_interface.c — https://sourcevu.sysprogs.com/rp2040/picosdk/files/src/rp2_common/pico_stdio_usb/reset_interface.c
- picotool reboot の man ページ — https://dyn.manpages.debian.org/unstable/picotool/picotool-reboot.1
- picotool issue 88 — https://github.com/raspberrypi/picotool/issues/88
- pico-sdk リリース（API）— https://api.github.com/repos/raspberrypi/pico-sdk/releases
- pico-sdk リリース（HTML）— https://github.com/raspberrypi/pico-sdk/releases
- pico-sdk — https://github.com/raspberrypi/pico-sdk
- Findpicotool.cmake — https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpicotool.cmake
- Findpioasm.cmake — https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpioasm.cmake
- picotool リリース（API）— https://api.github.com/repos/raspberrypi/picotool/releases
- picotool — https://github.com/raspberrypi/picotool
- pioasm — https://github.com/raspberrypi/pico-sdk/tree/master/tools/pioasm
- SDK host platform README — https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/host/README.md
- rp2040-pio-emulator — https://github.com/NathanY3G/rp2040-pio-emulator
- rp2040js — https://github.com/wokwi/rp2040js
- Wokwi Pi Pico — https://docs.wokwi.com/parts/wokwi-pi-pico
- Wokwi Pi Pico 2 — https://docs.wokwi.com/parts/board-pi-pico-2
- Wokwi CI（GitHub Actions）— https://docs.wokwi.com/wokwi-ci/github-actions
- Wokwi CI（Getting started）— https://docs.wokwi.com/wokwi-ci/getting-started
- Wokwi 料金 — https://wokwi.com/pricing
- Wokwi CLI — https://github.com/wokwi/wokwi-cli

**Linux Pi（起動時間・電源断・映像）**
- IronOxidizer/instant-pi — https://github.com/IronOxidizer/instant-pi
- furkantokac（Pi 3 高速起動）— https://www.furkantokac.com/rpi3-fast-boot-less-than-2-seconds/
- Bookworm の読み取り専用 root — https://github.com/raspberrypi/bookworm-feedback/issues/137
- Pi 5 の読み取り専用化の挙動差 — https://forum.core-electronics.com.au/t/pi-5-bookworm-64bit-cannot-set-filesystem-to-read-only/21769
- 読み取り専用 root の解説（二次資料）— https://pidiylab.com/raspberry-pi-read-only-root-filesystem-setup/
- 読み取り専用 root と tmpfs — https://www.dzombak.com/blog/2024/03/running-a-raspberry-pi-with-a-read-only-root-filesystem/
- Adafruit Read-Only Raspberry Pi — https://learn.adafruit.com/read-only-raspberry-pi
- Raspberry Pi 公式文書 DPI — https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#display-parallel-interface-dpi
- Pi 5 のインターレース対応 — https://www.raspberrypi.com/news/how-we-added-interlaced-video-to-raspberry-pi-5/
- 240p KMS 設定例（フォーラム）— https://retropie.org.uk/forum/post/303319
- Pi2Jamma — https://falz.net/wiki/Pi2jamma_hardware_and_software_info
- Pi2Jamma 販売店 — https://www.arcadexpress.com/en/video-converters/258-tarjeta-pi2jamma.html
- Pi400RGB — https://github.com/llegoff/Pi400RGB
- Elektor Pi Zero VGA — https://www.elektormagazine.com/index.php/labs/vga-audio-interface-for-raspberry-pi-zero
- Gert VGA666 — https://github.com/fenlogic/vga666 ／ https://static.chipdip.ru/lib/682/DOC041682208.pdf
- エミュレータ精度（RetroPie フォーラム）— https://retropie.org.uk/forum/post/140102 ／ https://retropie.org.uk/forum/post/140088
- ARM 機での Mesen の処理落ち — https://forums.libretro.com/t/fceumm-nestopia-the-evolution-of-fceumm/30970
- libretro Mesen2 コア — https://docs.libretro.com/library/mesen2/

### 2 章（第1次調査からの訂正）

- pico-infonesPlus の MapperTable と移管先 — https://raw.githubusercontent.com/PicoPlus-devel/pico-infonesPlus/main/infones/InfoNES_Mapper.cpp ／ https://github.com/PicoPlus-devel/pico-infonesPlus
- 無給電時の上限・ADC 兼用ピン・最大クロック — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- scanvideo の 15 kHz プリセットと timing 構造体 — https://raw.githubusercontent.com/raspberrypi/pico-extras/master/src/common/pico_scanvideo/vga_modes.c ／ https://raw.githubusercontent.com/raspberrypi/pico-extras/master/src/common/pico_scanvideo/include/pico/scanvideo/scanvideo_base.h
- PICO9918 SCART がインターレースであること — https://github.com/visrealm/pico9918/wiki/SCART-Output-Reference
- sanni の CRC 窓 — https://raw.githubusercontent.com/sanni/cartreader/master/Cart_Reader/NES.ino
- 秋月 Pico 2 のステッピング記載なし・RP2350B の在庫 — https://akizukidenshi.com/catalog/g/g129604/ ／ https://akizukidenshi.com/catalog/g/g130370/
- Linux Pi の起動時間 — https://github.com/IronOxidizer/instant-pi ／ https://www.furkantokac.com/rpi3-fast-boot-less-than-2-seconds/
- XIN と PLL 基準（Pico 2 で外部クロック同期不可）— https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf ／ https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf ／ https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- 74HC245 の VIH — https://www.ti.com/lit/ds/symlink/sn74hc245.pdf
- 2A03/2C02 の VOH — https://forums.nesdev.org/viewtopic.php?t=19656&start=15
- pico-sdk の版・picotool/pioasm の取得方法 — https://api.github.com/repos/raspberrypi/pico-sdk/releases ／ https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpicotool.cmake ／ https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpioasm.cmake
- Wokwi のトークンと制限 — https://docs.wokwi.com/wokwi-ci/github-actions ／ https://docs.wokwi.com/parts/board-pi-pico-2
- rp2040js の所在 — https://github.com/wokwi/rp2040js

### 3 章（未確認事項と実機で確かめるべきこと）

- テスト ROM AccuracyCoin（150 MHz 動作の確認に使う）— https://github.com/100thCoin/AccuracyCoin
- ステッピングの判別法 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- nescartdb.com（アクセス拒否）— 調査ノートに URL の記載なし（ドメイン名のみ）
- その他の項目は 1 章の出典と同じ

### 4 章（ユーザー要求への影響）

- ユーザー要求の原文と整理 — 本リポジトリの user_requirements.md（Web の出典なし）
- 費用の根拠（Pico 2 ¥990、Type-C 114356 ¥110、113080 ¥350、RP2350B ¥220、LCSC RP2350A $1.18）— https://akizukidenshi.com/catalog/g/g129604/ ／ https://akizukidenshi.com/catalog/g/g130370/ ／ https://www.lcsc.com/product-detail/C42411118.html ／ https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=USB%E3%82%B3%E3%83%8D%E3%82%AF%E3%82%BF%E3%83%BC&search=search
- バッテリーバックアップの本数 — https://raw.githubusercontent.com/SourMesen/Mesen2/master/UI/Dependencies/MesenNesDB.txt
- その他の根拠は 1 章の出典と同じ（4 章の推奨は筆者の推論で、独自の出典はない）
