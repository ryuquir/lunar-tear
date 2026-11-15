# Pico 2 を素の RP2350 に替えられるか（第 15 回の質問への調査）

調査日: 2026-11-14〜15。在庫と価格は 2026-11-14 23 時〜11-15 0 時（UTC）に読んだ値で、発注の直前に読み直すこと。

調べ方:
- 4 つの観点を、別々の担当が調べた。
  - チップと周辺回路
  - 書き換えの方式
  - JLCPCB の部品・規則・費用
  - この基板の設計への影響
- 別の担当が、一次資料で 1 件ずつ確かめ直した。
- 主張は 187 件。結果は次のとおり。下の記述は、訂正を反映したもの。
  - そのまま確認: 160 件
  - 訂正つきで確認: 27 件
  - 否定: 0 件
- 主な在庫と価格は、`hardware/famicom-jamma/tools/jlc_parts.py` で 2026-11-15 に読み直した。

表記: 出典は末尾にまとめる。「推論」と書いたものは資料から導いた判断で、資料に書いてあることではない。

## 1. 結論

- 置き換えはできる。次の 3 つは RP2350 のチップそのものにあり、Pico 2 の小基板が足していたものではない。
  - USB の端子
  - SWD（デバッグ用の線）の端子
  - 書き込みの機能（ブート ROM）
- 「USB-C 1 個で 3 個とも書き換える」形は、rev 0.3 にすでにある。
  - J10 は Pico C の USB につながる。
  - C が A と B を SWD で書き換え、2 個の RUN を握る。
  - 素のチップでも、部品を足さずにそのまま使える。USB-C を足す必要はない。
- 費用は、部品と実装だけで 1 枚あたり約 9〜11 ドル下がる（5 枚時）。
- GPIO は 1 個あたり増える。RP2350A なら +4 本、RP2350B なら +22 本。
- 条件が 3 つある。
  - (1) 指定の電源用コイルの在庫が、JLCPCB に 16 個しかない（4 章）。
  - (2) 3.3 V の電源を作り直す（5 章）。
  - (3) チップ周りの配線を、Raspberry Pi の手本どおりに 3 か所で引く（3 章）。

## 2. チップの種類

| | RP2350A | RP2350B | RP2354A | RP2354B |
|---|---|---|---|---|
| パッケージ | QFN-60（7 mm 角） | QFN-80（10 mm 角） | QFN-60 | QFN-80 |
| GPIO | 30 本 | 48 本 | 30 本 | 48 本 |
| 5V を受けられる GPIO | GPIO0〜25（26 本） | GPIO0〜39（40 本） | 同 RP2350A | 同 RP2350B |
| ADC | GPIO26〜29 | GPIO40〜47 | GPIO26〜29 | GPIO40〜47 |
| 内蔵フラッシュ | なし | なし | 2 MB | 2 MB |
| JLCPCB 品番 | C42411118 | C42415655 | C41378174 | C39843328 |
| 在庫（11-15） | 5,321 | 3,586 | 598 | 432 |
| 単価 1 個 / 10 個以上 | 1.2942 / 1.2206 ドル | 1.2795 / 1.1911 ドル | 1.2566 / 1.2320 ドル | 1.5151 / 1.4447 ドル |

参考として、Pico 2（C41407547）は次のとおり。
- 在庫 480 個。
- 単価は 1 個 9.2916、10 個以上 7.9712、30 個以上 7.1646 ドル。
- 「Standard Only」「X-ray Required」。

**5V 耐性**
- 5V を受けられるのは「FT」の端子だけ。上の表の GPIO のほかに、RUN・SWCLK・SWDIO も FT。
- 5.5 V まで受けられるのは、IOVDD が 3.3 V で給電されている間だけ。無給電では 3.63 V まで。
- ADC・QSPI・USB の端子は 5V を受けられない。

**Pico 2 が使っていた GPIO**
- 次の 4 本は Pico 2 が自分で使っている。素のチップでは空く。
  - GPIO23（電源の動作切り替え）
  - GPIO24（VBUS の検出）
  - GPIO25（LED）
  - GPIO29（VSYS の 1/3）

**RP2354**
- RP2350 と同じピン配置で、2 MB のフラッシュ（Winbond W25Q16JV）を同じパッケージに重ねたもの。
- QSPI_IOVDD は 3.3 V にする。
- 2 個目のフラッシュか PSRAM は、GPIO をチップセレクトにして足せる。
- 湿気への弱さは MSL 3（RP2350B は MSL 1）。
- 容量は Pico 2 の 4 MB の半分。

**版（ステッピング）**
- 量産品は A4 だけ。A2 は 2025-07 に生産をやめ、流通在庫も回収された。A3 は素のチップとしては売られていない。
- A4 を示すもの:
  - LCSC の製品写真の刻印は「RP2350A0A4」「RP2350B0A4」。
  - JLCPCB の部品データの内部名も A4 を示す。
- JLCPCB が実際に載せる巻きの版は、届いた基板の刻印で確かめる。
- E9（入力の漏れ電流）は A2 だけの不具合で、A3 から直っている。README の決まりは、版によらず動くように書いてある。

## 3. チップ 1 個に要る部品（Raspberry Pi の最小構成 R4-S1 による）

| 部品 | 数 | JLCPCB | 備考 |
|---|---|---|---|
| フラッシュ W25Q128JVSIQ（16 MB） | 1 | C97521、Basic、68,814 個、2.2595 / 1.9519 ドル | 1 本のチップセレクトで扱える最大の容量。100 nF を 1 個 |
| 12 MHz 水晶 ABM8-272-T3 | 1 | C20625731、Extended、532 個、0.3983 ドル | 15 pF ×2、直列 1 kΩ。水晶の定数は変えない |
| 3.3 µH コイル AOTA-B201610S3R3-101-T | 1 | C42411119、Extended、16 個、0.3366 ドル | 極性の印が必須（4 章） |
| 4.7 µF | 3 | Basic | 入力・出力と、VREG_AVDD のフィルタ（33 Ω と組む） |
| 100 nF | 11〜13 | Basic | 電源端子ごとに 1 個。RP2350A で 11、RP2350B で 13（フラッシュ用を含む） |
| 10 µF | 1 | Basic | 3.3 V の溜め |
| 27 Ω | 2 | Extended（C25100） | USB を使う C だけ |

**水晶について**
- Raspberry Pi は、水晶の定数を変えないよう警告している。
- Basic の 12 MHz 水晶 C9002 は使えない。負荷 20 pF・ESR 80 Ω で、Raspberry Pi の仕様（10 pF・最大 50 Ω）に合わない。

**部品の数と大きさ**
- 1 個あたり 20〜30 部品になる。0.4 mm ピッチなので、0402 の部品が避けられない。
- パッケージはどちらも 0.4 mm ピッチで、中央に 3.4 mm 角のパッドがある。
- GND は 2 か所: 中央のパッドと、VREG_PGND（QFN-60 は 47 番、QFN-80 は 62 番）。

**内蔵の電源回路の配置**
- 内蔵の電源回路は、1.1 V・最大 200 mA の降圧型。
- その配置を、Raspberry Pi は「最も重要」で「厳守」と書いている。手本どおりにしない場合は「自己責任」。
- 主な決まり:
  - 電源回路を最初に置く。
  - コンデンサとコイルは、チップと同じ面に置く。
  - コイルの真下は、表面の銅箔を抜く。
  - スイッチング電流の GND は、隣り合う 2 本のビアで中央パッドへ 1 点でつなぐ。
  - VREG_FB は、コイルの下を通さない。
- DVDD のいちばん遠い端子のコンデンサは、手本によって違う。
  - Pico 2 は 4.7 µF。Raspberry Pi は、Pico 2 の配置が「いちばん検証されている」と書いている。
  - 最小構成は 100 nF。

**データシートの表の誤り**
- 表 1679 は、QFN-60 の IOVDD を「11, 20, 30, 38, 45, 54」と書いている。
- 54 番は QSPI_IOVDD で、IOVDD の残りの 1 本は 1 番が正しい。
- 表から記号を作ると、1 番の配線を間違える。

## 4. 電源用コイルの在庫（いちばんの制約）

**指定品**
- Abracon AOTA-B201610S3R3-101-T。2016 サイズで、白い点で向きを示す。3.3 µH、Isat 2.4 A。
- Raspberry Pi の要求は次の 5 つ。
  - 完全シールド
  - 3.3 µH ±20%
  - DCR 250 mΩ 以下
  - 飽和電流 1.5 A 以上
  - 極性の印がある
- 指定品がある理由:
  - 小さいコイルには普通、向きの印がない。巻きの中でも向きがそろわない。
  - そこで Raspberry Pi が Abracon に作らせた。
  - 0806 の大きさでは、ほかに合う品は見つからなかったと Raspberry Pi は書いている。

**在庫（2026-11-14〜15）**

| 調達先 | 在庫 |
|---|---|
| JLCPCB | 16 個（同じ日に 27 → 21 → 16 と減った） |
| LCSC | 30 個 |
| DigiKey | 約 1,146 個（要約で確かめた二次情報） |

- JLCPCB は注文ごとに 1 個の損耗分を足す。
- したがって 5 枚（15 個 + 1）はちょうど足り、10 枚（31 個）は足りない。

**回避策**

JLCPCB で買う:
- 部品の先行購入（予約）、取り寄せ（Global Sourcing）、持ち込み。
- 予約した部品は、倉庫に届いてから使える。
- 買った部品は JLCPCB の部品庫に残り、送ってはもらえない。

コイルを使わない:
- DVDD に外から 1.1 V を与え、内蔵の電源回路を止める（VREG_FB を GND へ）。
- VREG_AVDD と VREG_VIN には、給電が要る。
- Raspberry Pi は、この形の配置の手本を出していない。
- Bus Pirate 6 は両方の形で作り、「どちらも動いた」と報告している（測定値はない）。
- 電圧が固定になるので、動作周波数を上げるために電圧を上げることはできない（推論）。
- Pico A のエミュレータは、定格の 150 MHz より上げる可能性がある（README 7 章の 7）。

## 5. 3.3 V の電源（今回分かった新しい課題）

**いまとの違い**
- いまは、Pico 2 が 1 枚ずつ自分で 3.3 V を作っている（1.8〜5.5 V で動く昇降圧）。
- 素のチップでは、チップ 3 個とフラッシュ 3 個の 3.3 V を基板が作る。

**電流の見込み（推論）**
- ふだんは約 0.08〜0.11 A。
- 上限の組み合わせでは約 0.5〜0.8 A。GPIO の負荷による。

**いまのレギュレータでは足りない**
- いまの AMS1117-3.3（U28）は、入出力の差が 1.1 V（標準）〜1.3 V（最大、0.8 A 時）ないと 3.3 V を保てない。
- VSYS は、+5V からショットキー（SS14、1 A で 0.55 V）を通って来る。
- JAMMA の電圧が下限の 4.75 V のとき、VSYS は約 4.2〜4.4 V になる。
- このとき 3.3 V が下がり、RP2350 の VREG_AVDD と USB_OTP_VDD の下限 3.135 V を割るおそれがある。
- USB だけで書き換えるときも同じ（定量は未確認）。

**過電圧クランプ**
- +3V3 の過電圧クランプ（CJ431、約 3.8 V）は、RP2350 の絶対最大 3.63 V より高い。

**対策（推論）**
- マイコン用の 3.3 V を分け、電圧の落ち方が小さいレギュレータ（低ドロップアウトの LDO か昇降圧型）で作る。
- 部品は、設計のときに JLCPCB の在庫から選ぶ。
- VREG_VIN は 2.7〜5.5 V なので、VSYS から取る形もある（Raspberry Pi の手本は 3.3 V から取る）。

## 6. 書き換えの方式

**どの方式にも共通する事実**
- ブート ROM（32 kB）はマスク ROM で、消すことも書き換えることもできない。
- 空のチップ（OTP が空）は、フラッシュに有効なイメージがなければ、自分で USB の書き込みモード（BOOTSEL）に入る。最初の書き込みにボタンは要らない。
- SWD・USB 書き込み・UART 書き込みを閉じられるのは、OTP（一度きりの書き込み領域）だけ。空のチップでは何も閉じていない。この基板では OTP を書かない。
- USB の書き込みモードには、12 MHz の水晶（か、XIN への 12 MHz のクロック）が要る。

### (a) C が SWD で A と B を書く（いまの方式）

**配線**
- rev 0.3 の配線のまま使え、部品の追加はない。
  - C の GPIO12〜15 から、1 kΩ を通して A と B の SWD へ。
  - RUN は 470 Ω で駆動し、4.7 kΩ で引き下げる。
- A と B の線は別々のままにする。空のチップは、複数の相手を区別する番号がどれも 0 だから。

**C のファームウェアに要るもの**
- SWD の手順。休止からの起こし方、救済リセット、Secure 状態、RCP の起動。
- ブート ROM のフラッシュ用の関数。接続、消去、書き込み、XIP の再開。
- 書いたあとの読み返し。

**再利用できるコード**
- yapicoprobe。ライセンスは MIT・BSD-3-Clause・Apache-2.0 が混ざる。RP2350 の上で動かすのは「試験的」。
- Corteil/swd_hexpansion（MIT、MicroPython）。
- debugprobe の PIO の SWD 部分（MIT と Apache-2.0）。
- OpenOCD の rp2xxx.c（GPL。参考用）。

**速さ**
- フラッシュの消去と書き込みで、1 MB あたり約 4 秒（標準）。
- PIO の SWD は約 100 KB/s で、1 MB に約 10 秒かかる。
- 1 kΩ の直列抵抗のためにクロックを下げる必要があるかは、試作で測る。

**失敗したとき**
- ブート ROM は無事なので、やり直せる。
- 救済リセットは、クロックが止まっていても効く。

**1 回のコピーで全部を更新するには**
- UF2 の中を 1 つの「ファミリー」（例: absolute）にそろえ、固定の番地に置く必要がある（データシート 5.5.3.2）。
- パーティションを使う形では、2〜3 回のコピーか、picotool のコマンドが要る。
- C のフラッシュの割り付けは、C の書き込みプログラムを作る前に決める。

**作業量**
- これは Pico 2 のままでも要る作業で、段階 4（未着手）に入っている。置き換えで増えるものではない。

### (b) UART 書き込み（ROM にある機能。複数チップの基板向け）

- 入り方: QSPI の CSn を Low、SD1 を High にしてリセットを放す。
- 信号: SD2 が送信、SD3 が受信で、1 Mbaud。
- 読み込み先は SRAM だけ（最大 520 kB、0x20000000 から）。
- 向く使い方: B をフラッシュなしにして、電源を入れるたびに C が送り込む。B は壊れようがない。
  - C の GPIO が 4 本要る。
  - pico-examples の bootloaders/uart が、ちょうどこの例。
- 別のやり方: いまの SWD の線で、B の SRAM に直接書き込んで走らせる。線は増えない（速さは未測定）。

### (c) USB ハブ

**部品**
- ハブの IC は CH334P/CH334R（WCH）、FE1.1s、SL2.1A。JLCPCB で 0.23〜0.70 ドル（2026-11-14）。
- チップごとに、USB の 27 Ω ×2 が要る。

**できること**
- 3 個とも、それぞれの USB 書き込みモードで書ける。書き込み用のファームウェアは要らない。
- PC から、picotool で 1 個ずつ書く。

**A と B を書き込みモードに入れる**
- C が A と B の QSPI_SS を Low にして、RUN を入れ直す（C の GPIO が 2 本要る）。
- A と B には、USB の処理を常駐させない。

**注意点**
- USB-C からハブまでは 480 Mbps になるので、短くする。
- ハブから RP2350 までは 12 Mbps（RP2350 は Full Speed だけ）。
- ハブ 1 個が故障点になる。

### (d) その他

- 相手を RUN で止めたまま、そのフラッシュを C が SPI で直接書く。
- A/B の 2 区画を使い、試してから切り替える（TBYB）。
- USB の 2:1 切り替え（CH442E など）を使う。
- 4 個目のチップを書き換え専用に置く（推論）。
  - いまの形より良くなる点は小さい。C の USB 書き込み機能も ROM にあり、壊れないから。
  - コイルが 1 枚あたり 4 個に増え、4 章の在庫の問題が重くなる。

## 7. JLCPCB の規則と費用

**分類**
- 4 種類のチップは、どれも「SMT Assembly」「Economic and Standard」。

**X 線検査**
- JLCPCB の料金の記事（2026-10-22 更新）は、「BGA、QFN など、はんだが見えない部品は X 線検査が必要」と書いている。
- 部品ページには、RP2350A/B・RP2354A/B の X 線の表示がない（xrayFlag=false）。Pico 2 には「Required」とある。
- どちらになるかは、見積もりで確かめる。1 枚あたり 0〜2.46 ドルの差になる。
- 数え方（注文全体で何個か、1 枚ごとに何個か）も分からない。

**装着の料金**
- Standard PCBA は、Basic・Extended とも、部品の種類ごとに 1.53 ドル。
- 金めっきの端子があるので、この基板はもともと Standard PCBA。

**基板の製造**
- 0.4 mm ピッチは範囲内（Economic は 0.4 mm、Standard は 0.35 mm まで）。
- Raspberry Pi の手本の寸法は、2 層の標準で作れ、追加料金もない。
  - 線幅と間隔は 0.15 mm。
  - ビアは 0.6/0.25 mm。

**中央パッドのビア**
- 手本は、ソルダーマスクでふさいだビアを、中央パッドに 9 本置いている。ところが、マスクの開口がビアのパッドの縁まで来ている。
- JLCPCB は次のように書いている。
  - 間隔が足りないと、ふさぎ切れない。
  - 0.35 mm より近いと、穴埋めできない。
- はんだが穴に吸われるおそれがあるので、JLCPCB に聞く。

**JLCPCB と Raspberry Pi の確認**
- JLCPCB の RP2350 のページには、JLCPCB が Raspberry Pi と一緒に基板のデータを見るという案内がある。
- 料金と日数は書いていない。

**費用（MCU まわりだけ。1 枚あたり。JLCPCB の段階価格）**

| | 5 枚 | 10 枚 |
|---|---|---|
| Pico 2 ×3（X 線を含む） | 26.91 ドル | 24.34 ドル |
| RP2350A ×3 の構成（X 線なし） | 15.64 ドル | 13.43 ドル |
| 同（X 線あり） | 18.10 ドル | 15.89 ドル |
| 差（1 枚あたり） | −8.82〜−11.28 ドル | −8.45〜−10.91 ドル |
| 差（注文全体） | −44.10〜−56.40 ドル | −84.50〜−109.10 ドル |

この見積もりの前提:
- 部品: RP2350A、W25Q128JVSIQ、ABM8-272-T3、AOTA のコイル、最小構成の受動部品、C の USB 部品。
- 2 個目の AMS1117 を仮に入れた。電源は 5 章のとおり作り直すので、ここは仮の値。
- 新しい部品の種類は 9 個。
- 損耗分は、コイルと水晶だけに入れた。新しい 0402 の部品の損耗分を入れると、1 枚あたり約 0.04 ドル増える。

ほかの構成:
- RP2350B でも、差は数セント。
- RP2354A（外付けフラッシュなし）なら、9.45 / 8.15 ドル。2 MB で足りる場合に限る。

基板全体（部品と実装。基板代・送料・税は含まない）:
- 5 枚: 71.02 → 約 59.75 ドル。
- 10 枚: 57.09 → 約 46.18 ドル。
  - 57.09 ドルは、Pico 2 を 30 個以上の単価で計算した値。
  - `cost_estimate.csv` の 59.51 ドルは、10 個以上の単価で計算した値。

この見積もりに入っていないもの:
- 4 層にした場合の、基板代の値上がり。JLCPCB は表を出していないので、見積もりが要る。
- Pico 2 を手で置く料金がかかった場合の、1 枚あたり約 2.35 ドル。素のチップなら発生しない。

## 8. この基板の設計への影響（rev 0.4 にする場合）

**変える所**
- `design/circuit.py`
  - mcu シート（`pico()` の部分、568〜636 行）
  - 電源シート（VSYS、U28、CJ431）
- `design/symbols.py`: PICO2 の記号（68〜84 行）を RP2350 の記号にする。表 1679 の誤り（3 章）に注意する。
- `tools/fcgen/parts.py` の部品の外形（QFN、0402、水晶、コイル、SOIC-8）と、`tools/build.py` の外形の照合。
- `tools/build.py` の 5V の検査（225・233・281・292・362 行）。記号の名前「PICO2」と GP26〜28 に結びついているので、作り直す。そのままだと次のようになる。
  - プロジェクトの記号で描く場合: 規則 1 と 5 は、黙って検査を飛ばす。規則 2 は、電源端子の名前（IOVDD など）を覚えるまで失敗する。
  - KiCad の部品庫の記号を使う場合: 規則 1・2・4・5 が、全部黙って飛ばす。
- 費用モデル（X 線、手置き）。
- README（3.2・3.3・3.8・8 章ほか）。
- 発注の文書（GrokBOT の指示書、ノウハウ、JLCPCB への質問）。
- 配置の案（U25〜U27）と、ドライブの一式。

**そのまま**
- Famicom 側のシート（CPU・PPU・カセット・映像・音声・JAMMA）のネット。

**見直し**
- 独立レビューをやり直す。
- 「52 件の故障を見つけた」検査は、そのスクリプトがリポジトリにないので、そのままは再実行できない。

**作業量（推論）**
- rev 0.1→0.2 の切り替えより大きめになる。
  - その切り替えは、手書きのコードで +530/−242 行、README で +121/−40 行。そのあと 52 件の指摘を直した。
  - 今回は、配置で性能が決まる部分（電源回路、水晶、フラッシュ、USB）が新しく入るため。
- 段階 2 は外形の案だけ、段階 3 は未着手。切り替えるなら、いまがいちばん安い。

**役割ごとの向き不向き**
- B（バス）: RP2350B なら、CPU のアドレス線と M2 を全部見られる。
- A（映像）: どちらでもよい。
  - RP2350B なら、RGB のビットを増やせ、PSRAM も足せる。
  - ROM イメージを置くので、フラッシュは 2 MB より大きい方が安全（2 MB で足りるかは未確認）。
- C（管理）:
  - RP2350A なら、ADC（GPIO26・27）の割り当てがそのまま使える。
  - RP2350B だと、ADC が GPIO40〜47 に移る。

## 9. 未確認事項

1. JLCPCB が素の QFN を X 線検査して課金するか。課金するなら、数え方は注文全体か 1 枚ごとか。
2. コイルをどう確保するか。予約、取り寄せ、外部 1.1 V のどれにするか。
3. 2 層と 4 層の基板代の差（220 × 162 mm、5 枚と 10 枚、ENIG、金めっきの端子）。
4. 3 個のチップの電源回路を手本どおりに置いて、この 2 層・1.6 mm の基板で引き回せるか（まだ試していない）。
   - Raspberry Pi の文書には、1 mm の厚さを前提に書いた箇所がある。一方、KiCad の層構成は 1.6 mm になっている。
   - 厚さについての注意は、USB の線にだけ書いてある。
5. Raspberry Pi の 2 層の手本は、コンデンサを減らしているので「最高速度を制限する可能性がある」と書いている。エミュレータを定格より速く回すときに安定するかは、試作で確かめる。
6. RP2354 の 2 MB に、A のファームウェアと ROM イメージが入るか。
7. JLCPCB が載せる巻きの版（A4 の見込み）。
8. 中央パッドのビアを、JLCPCB がふさげるか。
9. JLCPCB と Raspberry Pi による基板データの確認について。
   - 必須か。
   - 何日かかるか。
   - 指定外のコイルでも通るか。
10. 1 kΩ を通したときの、SWD の実際の速さ。
11. DVDD のいちばん遠い端子のコンデンサを、4.7 µF にするか 100 nF にするか（3 章）。

## 出典

1. Raspberry Pi, RP2350 Datasheet, Release 8 (build 2026-10-01): https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
   - §1 表 1
   - §3.5.9（デバッグの鍵）
   - §5.2（ブート ROM と BOOTSEL）
   - §5.5.3.2（UF2 のファミリー）
   - §5.8（UART 書き込み）
   - §6.3.8（電源回路とコイル）
   - §14（RP2354 と型番）
   - 表 1673〜1680（端子、5V 耐性、絶対最大）
   - 表 1693（電流）
   - 付録 C・D（版と不具合）
2. Raspberry Pi, Hardware design with RP2350（2026-08）: https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
3. Raspberry Pi, 最小構成の設計データ R4-S1（KiCad と部品表。MIT ライセンス）
   - RP2350A: https://pip.raspberrypi.com/documents/RP-010328-CA
   - RP2350B: https://pip.raspberrypi.com/documents/RP-010329-CA
4. Raspberry Pi, Pico 2 Datasheet: https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
5. Raspberry Pi News, RP2350 A4, RP2354 and a new hacking challenge（2025-07-29）: https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/
6. Raspberry Pi, RP235x A4 stepping PCN: https://pip.raspberrypi.com/categories/1263-pcn/documents/RP-008771-CC/RP235x-A4-stepping-PCN.pdf
7. JLCPCB の部品ページ（https://jlcpcb.com/partdetail/ のあとに品番）
   - C42411118（RP2350A）
   - C42415655（RP2350B）
   - C41378174（RP2354A）
   - C39843328（RP2354B）
   - C42411119（コイル）
   - C20625731（水晶）
   - C97521（フラッシュ）
   - C41407547（Pico 2）
   - C9002（Basic の水晶）
8. JLCPCB, PCB Assembly Price（2026-10-22 更新）: https://jlcpcb.com/help/article/pcb-assembly-price
9. JLCPCB, PCB Capabilities: https://jlcpcb.com/capabilities/pcb-capabilities
10. JLCPCB, PCB Assembly Capabilities: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
11. JLCPCB, PCB via covering: https://jlcpcb.com/help/article/pcb-via-covering
12. JLCPCB, Common BOM and CPL matching issues: https://jlcpcb.com/help/article/common-bom-and-cpl-matching-issues-and-explanations
13. JLCPCB, Pre-ordering parts terms and conditions: https://jlcpcb.com/help/article/pre-ordering-parts-terms-conditions
14. JLCPCB, Raspberry Pi RP2350: https://jlcpcb.com/raspberry-pi-rp2350
15. Raspberry Pi News, RP2350 now available at JLCPCB: https://www.raspberrypi.com/news/rp2350-now-available-at-jlcpcb/
16. LCSC の製品ページ（https://www.lcsc.com/product-detail/ のあとに 品番.html）。C42411118、C42415655、C42411119 ほか。
17. Abracon, AOTA-B201610S3R3-101-T: https://abracon.com/datasheets/AOTA-B201610S3R3-101-T.pdf
18. Advanced Monolithic Systems, AMS1117: http://www.advanced-monolithic.com/pdf/ds1117.pdf
19. Winbond, W25Q128JV（LCSC C97521 のデータシート）: https://datasheet.lcsc.com/datasheet/pdf/d009d960f1daec6149edaa35b7dae856.pdf
20. WCH, CH334/CH335 データシート V2.4: https://atta.szlcsc.com/upload/public/pdf/source/20240313/2136C33A6EB724334E520DEFC33CFBA6.pdf
21. FE1.1s データシート: https://datasheet.lcsc.com/datasheet/pdf/3f684d9313f1d4efb6d15bf57ad88930.pdf
22. SL2.1A データシート: https://datasheet.lcsc.com/datasheet/pdf/df332af74440545569134d5952707942.pdf
23. raspberrypi/pico-examples、bootloaders/uart: https://github.com/raspberrypi/pico-examples/tree/master/bootloaders/uart
24. raspberrypi/picotool: https://github.com/raspberrypi/picotool
25. raspberrypi/pico-sdk: https://github.com/raspberrypi/pico-sdk
26. rgrr/yapicoprobe: https://github.com/rgrr/yapicoprobe
27. raspberrypi/debugprobe: https://github.com/raspberrypi/debugprobe
28. Corteil/swd_hexpansion: https://github.com/Corteil/swd_hexpansion
29. OpenOCD, rp2xxx.c: https://github.com/openocd-org/openocd/blob/master/src/flash/nor/rp2xxx.c
30. Bus Pirate 6 rev2 の RP2350（外部 1.1 V と内蔵電源の両方）: https://docs.buspirate.com/docs/hardware/bp6rev2/rp2350/
31. DigiKey、AOTA-B201610S3R3-101-T の在庫（2026-11-15。要約で確かめた二次情報）
32. このリポジトリ
    - `hardware/famicom-jamma/README.md`（3.2、3.3、3.8、7 章）
    - `design/circuit.py`（電源 75〜107 行、mcu 568〜636 行）
    - `tools/build.py`
    - `out/cost_estimate.csv`
    - `design/`・`tools/`・`out/` は、どれも `hardware/famicom-jamma/` の下にある。
