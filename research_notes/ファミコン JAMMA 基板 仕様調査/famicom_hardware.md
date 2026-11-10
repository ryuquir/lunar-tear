# ファミリーコンピュータ (HVC-001) ハードウェア調査ノート — RP2A03 / RP2C02 移植 JAMMA 基板設計用

調査日: 2026-11-10。主な一次情報源は NESdev Wiki (https://www.nesdev.org/wiki/)。
注意: NESdev Wiki は Cloudflare チャレンジのため curl 取得不可、WebFetch (要約モデル経由) で取得した。数値・ピン番号はできる限り2ソース以上で照合し、照合できなかったものは「未確認」と明記する。

## 1. RP2A03 (CPU/APU) ピン配置

### Takeaway
DIP-40。Pin 1/2 = 音声 AD1/AD2、Pin 29 = CLK (21.47727 MHz を内部で ÷12)、Pin 31 = M2、Pin 35 = /OE2 ($4017 読み出し)、Pin 36 = /OE1 ($4016 読み出し)、Pin 37-39 = OUT2-OUT0、Pin 30 = TST (GND に接続)。

### Cited Findings
完全ピン表 — [NESdev CPU pinout](https://www.nesdev.org/wiki/CPU_pinout)

| Pin | 名前 | 方向 | 機能 |
|---|---|---|---|
| 1 | AD1 | 出力 (アナログ) | 音声出力: 矩形波 Pulse 1 + Pulse 2 |
| 2 | AD2 | 出力 (アナログ) | 音声出力: 三角波 + ノイズ + DPCM |
| 3 | /RST | 入力 | Low でリセット保持 (Pin 2 以外の出力は Hi-Z)。解除後 M2 6 クロックで $FFFC/$FFFD のリセットベクタを読む |
| 4-19 | A0-A15 | 出力 | アドレスバス (Pin 4 = A0 … Pin 19 = A15)。1サイクル全体で保持 |
| 20 | GND | 電源 | |
| 21-28 | D7-D0 | 双方向 | データバス (Pin 21 = D7 … Pin 28 = D0)。読みは φ2 中にサンプル、書きは φ2 中に駆動 |
| 29 | CLK | 入力 | 21.47727 MHz (NTSC)。内部で ÷12 → 1.789773 MHz |
| 30 | TST | 入力 | 通常 GND。2A03G で High にすると $4018-$401A 診断レジスタ有効・$4016/$4017 がオープンバス。2A03E/2A07 では High で CPU 停止 (/RDY 無効化) |
| 31 | M2 | 出力 | φ2 由来のクロック出力。各 CPU サイクルは M2 立下りで開始。デューティ: 2A03E/G/H = 15/24 (5/8)、初期 2A03 (無印) = 17/24 |
| 32 | /IRQ | 入力 | マスク可能割り込み (内部プルアップあり — カートリッジコネクタ頁) |
| 33 | /NMI | 入力 | ノンマスカブル割り込み (PPU /INT から) |
| 34 | R/W | 出力 | Low = 書き込み。サイクル中固定 |
| 35 | /OE2 | 出力 | $4017 読み出し時にアクティブ (コントローラ2側) |
| 36 | /OE1 | 出力 | $4016 読み出し時にアクティブ (コントローラ1側) |
| 37 | OUT2 | 出力 | $4016 書き込み bit2 ラッチ |
| 38 | OUT1 | 出力 | $4016 書き込み bit1 ラッチ |
| 39 | OUT0 | 出力 | $4016 書き込み bit0 ラッチ (コントローラ・ストローブ) |
| 40 | VCC | 電源 | +5 V |

- /OE1 ↔ $4016、/OE2 ↔ $4017 の対応: 「/OE1 … activated by reading $4016」「/OE2 … activated by reading $4017」 — [NESdev Input devices](https://www.nesdev.org/wiki/Input_devices)。CPU pinout 頁は「コントローラ1/2の出力イネーブル」とのみ記述 — [NESdev CPU pinout](https://www.nesdev.org/wiki/CPU_pinout)。

- 第2ソース照合: HVC-CPU-05 回路図の U6 RP2A03 シンボル (1 AUX A, 2 AUX B, 3 RES, 4-19 A0-A15, 20 VEE(GND), 21-28 D7…D0, 29 XIN, 30 (NC 表記; 実基板は GND), 31 O2, 32 IRQ, 33 NMI, 34 R/W, 35 RDP1, 36 RDP0, 37 P2, 38 P1, 39 P0, 40 VCC) と全ピン一致 — [HVC-CPU-05 回路図](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf)。RDP0 (pin 36) → U7 ($4016 バッファ)、RDP1 (pin 35) → U8 ($4017 バッファ) を同図および [OpenFC HVC-CPU-07 ネット](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A) (U6.36 = U7.1、U6.35 = U8.1) で確認。

### Inferences
- /OE1・/OE2 は「$4016/$4017 読み出し中に Low」となる 2A03 内部デコード出力なので、外部デコードは不要。Raspberry Pi 代替モードでもこの 2 本と OUT0 を再現すればコントローラ回路は共用できる。

### Gaps
- 2A03 各ピンの入力閾値・出力駆動能力・消費電流の公式データは未発見 (未確認)。

## 2. RP2C02 (PPU) ピン配置

### Takeaway
DIP-40。Pin 21 = VOUT (コンポジット直接出力)、Pin 22 = /RST (ファミコンでは +5V 直結、NES ではリセット回路に接続)、Pin 19 = /INT (オープンドレイン → CPU /NMI + プルアップ)、Pin 14-17 = EXT0-3 (公式機は全て GND)。

### Cited Findings
完全ピン表 — [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)

| Pin | 名前 | 方向 | 機能 |
|---|---|---|---|
| 1 | R/W | 入力 | CPU R/W |
| 2-9 | CPU D0-D7 | 双方向 | CPU データバス (Pin 2 = D0 … Pin 9 = D7) |
| 10 | CPU A2 | 入力 | レジスタ選択 |
| 11 | CPU A1 | 入力 | |
| 12 | CPU A0 | 入力 | |
| 13 | /CS | 入力 | 74139 デコーダ出力 ($2000-$3FFF)。/DBE とも |
| 14 | EXT0 | 双方向 | 2PPU 合成用。PPUCTRL bit6 = 1 (master/出力) でパレット番号を出力、0 で入力 (背景色選択)。公式機は出力モード未使用、GND 接続 |
| 15 | EXT1 | 双方向 | 同上 |
| 16 | EXT2 | 双方向 | 同上 |
| 17 | EXT3 | 双方向 | 同上 |
| 18 | CLK | 入力 | 21.47727 MHz。÷4 でドット/メモリクロック (5.369 MHz) |
| 19 | /INT | 出力 (オープンドレイン) | VBlank NMI。CPU /NMI とプルアップ抵抗へ |
| 20 | GND | 電源 | |
| 21 | VOUT | 出力 (アナログ) | コンポジット映像 |
| 22 | /RST | 入力 | クロック分周器・ビデオ位相・走査カウンタ・偶奇フレームをリセット。PPUCTRL/PPUMASK/PPUSCROLL/読みバッファを1フレーム間0に保持 |
| 23 | /WR | 出力 | VRAM 書き込み (パレット $3F00-$3FFF 書き込み時は出ない) |
| 24 | /RD | 出力 | VRAM 読み出し |
| 25 | PA13 | 出力 | PPU アドレス上位 |
| 26 | PA12 | 出力 | |
| 27 | PA11 | 出力 | |
| 28 | PA10 | 出力 | |
| 29 | PA9 | 出力 | |
| 30 | PA8 | 出力 | |
| 31-38 | AD7-AD0 | 双方向 | PPU データ/下位アドレス多重 (Pin 31 = AD7 … Pin 38 = AD0) |
| 39 | ALE | 出力 | VRAM アクセス開始時 High (1 PPU サイクル)。下位8bitアドレスをラッチ |
| 40 | VCC | 電源 | +5 V |

- ファミコンでは PPU /RST (Pin 22) は +5V 直結 (そのためリセットボタン押下中も画面が消えない)。NES ではリセットボタン/CIC 経由で画面クリアに使用 — [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- RGB PPU (2C03/2C04/2C05) では Pin 14-16 = R,G,B、Pin 17 = GND、Pin 21 = CSYNC — [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- HVC-CPU-GPM-01/-02 では Pin 21 をパターンから切り離すと画質改善 (コンポジット改造の話) — [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)

- 第2ソース照合: HVC-CPU-05 回路図の U5 RP2C02 シンボル (1 R/W, 2-9 D0-D7, 10-12 RS2/RS1/RS0 = A2/A1/A0, 13 DBE, 14-17 EXT0-3, 18 CLK, 19 NMI, 20 GND, 21 VD OUT, 22 RST, 23 WR, 24 RD, 25-30 PA13…PA8, 31-38 AD7…AD0, 39 ALE, 40 VCC) と全ピン一致 — [HVC-CPU-05 回路図](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf)

### Inferences
- PPU /RST を +5V 固定にするファミコン方式なら、リセット時に PPU の初期化が CPU と非同期になる (ゲームは $2002 の VBlank 待ちで対処する前提)。NES 方式で /RST を CPU リセットと共通にすることも可能だが、ファミコン実機と挙動が変わる (推論)。

### Gaps
- VOUT の無負荷電圧、PPU の消費電流・発熱の数値は未発見 (未確認)。

## 3. メイン基板回路 (HVC-CPU-05 実機トレース回路図による)

### Takeaway
HVC-CPU-05 の実機トレース回路図 (BABAX 氏 Rev.07, 2021-04-29) で全回路を確認した。メインボード IC は RP2A03 (U6)、RP2C02 (U5)、74LS139 (U3)、74LS373 (U2)、2KB SRAM ×2 (U1 = WRAM, U4 = VRAM)、40H368 ×2 (U7 = $4016, U8 = $4017) のみ。クロックは 2SC2021 ×2 の水晶ディスクリート発振回路、オーディオ増幅は 74HCU04 ではなく **40H368 の空きゲート (U7 6A→6Y) をフィードバック抵抗 100k で線形増幅器として使用**、/PA13 も **U7 の空きゲート (5A→5Y)** で生成。映像は PPU Pin 21 → 2SA937 PNP エミッタフォロワ。電源は 7805 (DC 10V 入力)。CIC なし、リセットは CPU /RST のみ (PPU /RST は +5V)。

### Cited Findings
出典 (以下すべて): [FC HVC-001 HVC-CPU-05 基板回路図 Rev.07 (BABAX, PDF)](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf) — 実機 HVC-CPU-05 (Serial H1701639) からのトレース。回路図中の凡例: ラベル末尾「$」= プルアップされた端子/回路、「%」= プルダウンされた端子/回路。

#### 3.1 部品表 (HVC-CPU-05 メイン基板)
| Ref | 部品 | 用途 |
|---|---|---|
| U6 | RP2A03 | CPU/APU |
| U5 | RP2C02 (図中 RP2C02C) | PPU |
| U3 | 74LS139 | アドレスデコーダ (/ROMSEL, WRAM /CS, PPU /CS) |
| U2 | 74LS373 | PPU 下位アドレスラッチ |
| U1 | 16Kbit (2K×8) SRAM, DIP-24 | CPU WRAM $0000-$07FF |
| U4 | 16Kbit (2K×8) SRAM, DIP-24 | VRAM (CIRAM) |
| U7 | 40H368 (または 74HC368) | $4016 読み出しバッファ + /PA13 インバータ + オーディオアンプ |
| U8 | 40H368 (または 74HC368) | $4017 読み出しバッファ |
| Q2 | 2SC2021 (ROHM, Grade S) | 水晶発振 |
| Q3 | 2SC2021 | クロックバッファ (エミッタフォロワ) |
| Q1 | 2SA937 (ROHM, Grade P) | 映像バッファ (PNP エミッタフォロワ) |
| X1 | 21.47727 MHz 水晶 | |
| D1 | NEC 1S953 (同等品 松下 MA162) | WRAM /CS 遅延回路 |
| RM1 | 10k ×11 集合抵抗 | /IRQ, /NMI, $4016/$4017 データ・クロック線のプルアップ |
| REG1 | 7805 (電源/RF モジュレータ基板上) | +5V 生成、入力 DC 10V (HVC-002 AC アダプタ) |
| SW1 | リセットスイッチ | |
- SRAM 実装品例: LH5116 (SHARP), TMM2115AP-15 (TOSHIBA), MB8416A-15-SK (FUJITSU), HM6116 (HITACHI) 等。

#### 3.2 アドレスデコード (74LS139 U3)
- 後段 (2/2): A (pin14) = M2 (CLKOUT, CPU pin 31)、B (pin13) = CPU A15、/G (pin15) = GND。
  - /Y3 (pin 9) → **/ROMSEL** (M2=1 かつ A15=1 で Low: $8000-$FFFF) → カートリッジ pin 44
  - /Y1 (pin 11) → 前段の /G (pin 1) (M2=1 かつ A15=0 で前段を有効化)
- 前段 (1/2): A (pin2) = CPU A13、B (pin3) = CPU A14、/G (pin1) = 上記 /Y1。
  - /Y0 (pin 4) → **RAMSEL#** (WRAM /CS, $0000-$1FFF)
  - /Y1 (pin 5) → **DBE#** (PPU /CS pin 13, $2000-$3FFF)
  - /Y2, /Y3 (pin 6, 7) 未使用 ($4000-$7FFF はマザーボードでデコードしない; $4000-$401F は 2A03 内部)
- PPU /CS (DBE#) ラインに C21 330 pF と C23 30 pF の対 GND コンデンサ (HVC-CPU-07 の KiCad ネット: U3.5 = U5.13 = C21.2 = C23.2 — [OpenFC HVC-CPU-07 KiCad](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A))。
- 結果: WRAM と PPU レジスタは M2 High 期間のみ選択される。

#### 3.3 WRAM (U1, 2KB)
- A0-A10 = CPU A0-A10 (A11, A12 は未接続 → $0000-$1FFF で 4 回ミラー)、/WE = CPU R/W、/OE (pin 20) = GND 固定、D = CPU D0-D7。
- /CS (pin 18) は RAMSEL# から **ダイオード D1 (1S953) + R14 1.2k 並列 + C20 68 pF (対 GND)** を経由: RAMSEL# 立下りはダイオード経由で即座に Low、立上りは 1.2k×68pF で遅延 (書き込みホールド時間確保のためと推定 — 推論)。

#### 3.4 VRAM / CIRAM (U4, 2KB)
- A0-A7 = 74LS373 出力 (PA0-PA7)、A8 = PA8、A9 = PA9、**A10 = カートリッジ pin 18 (CIRAM A10/VRAM_A10)**、**/CS = カートリッジ pin 48 (CIRAM /CE, VRAMCS#)**、/OE = PPU /RD、/WE = PPU /WR、I/O = PPU AD0-AD7 (PD0-PD7)。

#### 3.5 アドレスラッチ (74LS373 U2)
- /OE (pin1) = GND、G (pin 11) = PPU ALE (pin 39)、D = PPU AD0-7、Q = PA0-PA7 (→ VRAM とカートリッジ pin 25-19, 50)。
- 図では D/Q の割り当てがビット順に並んでいない (配線都合で入れ替え; D0 入力 = PD7 → Q0 = PA7 等、各ビットは対応が取れている)。

#### 3.6 /PA13 インバータ
- U7 (40H368) 5A (pin 12) = PPU PA13 → 5Y (pin 11) = **PA13'** (= /PA13) → カートリッジ pin 49。U7 G2 (pin 15) = GND (常時有効)。専用インバータ IC は無い。

#### 3.7 コントローラ入力バッファ (40H368 U7/U8)
- U7 ($4016): G1 (pin1) = CPU /OE1 (pin 36, 図中 INP0#/RDP0)。1A (2) = 4016 D0$ (パッド I データ) → 1Y (3) = D0、2A (4) = 4016 D1$ (拡張端子) → 2Y (5) = D1、3A (6) = M2 (CLKOUT) → 3Y (7) = **4016 CUP$ (パッド I / 拡張端子のシフトクロック)**、4A (10) = MIC IN' → 4Y (9) = D2 (マイク)。G2 (pin15) = GND で 5・6 ゲートは常時有効 (/PA13 とオーディオに流用)。
- U8 ($4017): G1 (pin1) と G2 (pin15) とも CPU /OE2 (pin 35, INP1#)。1A = M2 → 1Y = **4017 CUP$ (パッド II / 拡張端子クロック)**、2A = 4017 D1$ → D1、3A = 4017 D3$ → D3、4A = 4017 D4$ → D4、5A = 4017 D2$ → D2、6A = 4017 D0$ → D0。
- つまりシフトクロックは「/OE がアクティブな間だけ M2 を反転して出力」 (/OE 非アクティブ時は Hi-Z → RM1 10k プルアップで High)。368 は反転バッファなので、4021 Q8 出力 (押下 = Low) が D0 では 1 として読める。
- 回路図改版履歴 Rev.06: 「U7,U8 それぞれ 40H368 の10番,9番を操作するハイインピーダンスコントロールゲートピンの番号が15番ピン接続となっていたので1番に修正」— マイクバッファ (U7 4A/4Y) は G1 (/OE1) 側。

#### 3.8 オーディオ回路
- RP2A03 pin 1 (AUX A, 矩形波) → R1 100Ω 対 GND、R4 20k で加算点へ。pin 2 (AUX B, 三角/ノイズ/DPCM) → R2 100Ω 対 GND、R5 12k で加算点へ。マイク (MIC IN) → R8 10k (+ C10 0.1µF 対 GND) → R3 10k で加算点へ。
- 加算点 → C2 1µF/50V → U7 6A (pin 14, SOUND I') → 6Y (pin 13) = **SOUND I**。帰還抵抗 R7 100k (6Y→6A)。出力に C8 0.1µF/12V 対 GND。→ 反転増幅器 (利得 約 100k/20k = 5 倍 (矩形)、100k/12k ≈ 8.3 倍 (TND) — 推論、100Ω 負荷との関係は未計算)。
- SOUND I → **カートリッジ pin 45** および拡張端子 pin 2。カートリッジ pin 46 (SOUND O) → 電源/RF モジュレータ基板 (R13 12k、C18 0.001µF を経て RF-M AUDIO)。カートリッジが無いと音が出ない (pin 45-46 はカートリッジ側で接続/ミックス) — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector) と一致: 「Audio to RF … Usually tied to the 2A03 audio」。

#### 3.9 クロック発振回路
- Q2 (2SC2021) コルピッツ型水晶発振: X1 21.47727 MHz、R11 220k (バイアス)、C22 18 pF、TC1 30 pF トリマ、C3 51 pF、(C5 5 pF NC)、R10 1.2k、C6 15 pF。
- PPU CLK (pin 18) は発振ノードから C4 51 pF で結合。
- CPU CLK (pin 29, 図中 XIN) は Q3 (2SC2021) エミッタフォロワ (R9 1.2k) 経由、C9 220 pF / R13 150k / ジャンパ CL あり。
- 回路図注記 Rev.02: 「PPUCLK と CPUCLK のラベルが逆に表示されていたので修正」。

#### 3.10 リセット回路
- CPU /RST (pin 3, 図中 RES#$%) に C1 0.47µF/50V 対 GND、SW1 (リセットボタン) で GND へ短絡。外付けプルアップ抵抗は図に無い (2A03 内部プルアップ前提と読める — 内部プルアップの有無は未確認)。
- PPU /RST (pin 22) は **VCC 直結** (HVC-CPU-07 KiCad ネット U5.22 = VCC — [OpenFC](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A); [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout) と一致)。CPU TST (pin 30) も GND (U6.30 = GND)。
- CPU /RST ネット (HVC-CPU-07): U6.3 = C1 = SW1 のみ (外付けプルアップ無し) — [OpenFC](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A)。

#### 3.11 映像出力
- PPU pin 21 (VOUT) → Q1 2SA937 (PNP) のベース、コレクタ GND、エミッタ → R12 220Ω → VIDEO、VIDEO に R6 2.2k プルアップ (+5V)。→ 電源/RF 基板の RF モジュレータ (V 端子)。
- PPU EXT0-EXT3 (pin 14-17) は GND 接続。

#### 3.12 電源/RF モジュレータ基板
- DC 10V IN → C29 0.01µF, C24 47µF/16V → 7805 → C75 0.1µF, C2 0.01µF, C25 1000µF/6.3V → POWER SW → 7P コネクタ (G, VCC, VCC, +B, A, G, V)。
- カートリッジ pin 31 (VCC_SLOT) は別系統 (+5V、C14 0.01µF)。

#### 3.13 コントローラ (本体直結)
- コントローラ I (MITSUMI T19 56_8231B): 4021 P8=A, P7=B, P6=SELECT, P5=START, P4=UP, P3=DOWN, P2=LEFT, P1=RIGHT、DS (pin 11) = GND、Q8 (pin 3) 出力、P/S (pin 9) = OUT0、CLK (pin 10) = 4016 CUP$。各入力 50k 印刷カーボン抵抗プルアップ、ボタンで GND へ。ケーブル: 1 茶 GND, 2 赤 4016_D0, 3 橙 OUT0, 4 黄 4016 CLK, 5 白 VCC。
- コントローラ II (MITSUMI T19 56_8232A): P8=A, P7=B, **P6/P5 (SELECT/START 位置) は VCC に直結 (常に非押下 → 0 として読める)**、P4-P1 = UP/DOWN/LEFT/RIGHT、プルアップ 43k。マイク: ECM → 4069 増幅 (VR1 165k, PII-R8 2.2k, CE1 0.33µF, PII-R7 400Ω)。ケーブル: 1 茶 MIC OUT, 2 赤 GND, 3 橙 4017_D0, 4 黄 OUT0, 5 白 4017 CLK, 6 青 VCC。
- 印刷抵抗のため値の誤差が大きいとの注記あり。

#### 3.14 拡張端子 (15 ピン D-sub メス, P5 D-JACK(EXT))
| Pin | 信号 |
|---|---|
| 1 | GND |
| 2 | SOUND I (増幅後オーディオ) |
| 3 | /IRQ |
| 4 | $4017 D4 |
| 5 | $4017 D3 |
| 6 | $4017 D2 |
| 7 | $4017 D1 |
| 8 | $4017 D0 |
| 9 | $4017 CLK (U8 1Y) |
| 10 | OUT2 |
| 11 | OUT1 |
| 12 | OUT0 |
| 13 | $4016 D1 |
| 14 | $4016 CLK (U7 3Y) |
| 15 | +5V |
(pin 1 = GND / pin 15 = +5V は図の線の判読による。NESdev Expansion port で照合 — 次節)

#### 3.15 カートリッジスロット (回路図上の名称)
- 図の 60 ピン割付は NESdev と一致: 1 GND, 2-13 A11…A0, 14 R/W, 15 /IRQ, 16 GND, 17 PPU /RD, 18 VRAM A10, 19-25 PA6…PA0, 26-29 PD0-PD3, 30 VCC, 31 VCC_SLOT, 32 O2 (M2), 33-35 A12-A14, 36-43 D7…D0, 44 /ROMSEL, 45 SOUND I, 46 SOUND O, 47 PPU /WR, 48 VRAM /CS, 49 /PA13 (PA13'), 50 PA7, 51-56 PA8-PA13, 57-60 PD7, PD6, PD5, PD4。
- PPU /RD (pin 17) に C18 68 pF 対 GND。

#### 3.16 第2ソースによる照合 (HVC-CPU-07)
- [OpenFC HVC-CPU-07 Rev A KiCad データ](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A) (コミット 42cb3a5, 2026-04-24) の部品値とネットを抽出し、HVC-CPU-05 回路図と照合した。以下は**両ソースで一致**:
  - 音声: U6.1 (AD1) → R2 100Ω 対 GND + R4 20k、U6.2 (AD2) → R1 100Ω + R5 12k、R3 10k (マイク P5.1 から)、C2 1µF、**R7 100k を U7.13 (6Y) ↔ U7.14 (6A) 間に帰還**、U7.13 = カートリッジ P1.45 = 拡張端子 P2.2。P1.46 → 電源/RF コネクタ P3.5。
  - デコーダ: U3.1 = U3.11 (後段 /Y1 → 前段 /G)、U3.2 = A13、U3.3 = A14、U3.13 = A15、U3.14 = M2、U3.15 = GND、U3.9 = P1.44 (/ROMSEL)、U3.5 = PPU /CS、U3.4 → D1/R14/C20 → U1.18 (WRAM /CS)。
  - /OE: U6.36 (/OE1) = U7.1、U6.35 (/OE2) = U8.1 = U8.15。M2 = U3.14 = U7.6 = U8.2 = P1.32。
  - /PA13: U7.12 = PPU pin 25 (PA13) = P1.56、U7.11 = P1.49。
  - VRAM: U4.18 (/CS) = P1.48、U4.19 (A10) = P1.18、U4.20 (/OE) = PPU /RD = P1.17 (+C18 68pF)、U4.21 (/WE) = PPU /WR = P1.47。
  - WRAM: U1.20 (/OE) = GND、U1.21 (/WE) = R/W。
  - /NMI = PPU pin 19 = RM1.8 (10k プルアップ)、/IRQ = P1.15 = 拡張 P2.3 = RM1.2。
  - クロック部品値: R9/R10/R14 1.2k、R11 220k、R13 150k (CPU CLK ネット: U6.29 = C9 220pF = R13)、C3/C4 51pF、C22 18pF、C6 15pF、TC1 30pF、C5 30pF。PPU CLK (U5.18) = C4 経由。
  - 映像: Q1 2SA937、R12 220Ω、R6 2.2k。
- OpenFC 側の型番は 74HC139 / 74HC373 / 40H368 表記 (再現基板での推奨品で、オリジナルの LS 品とは異なる可能性)。

### Inferences
- 移植基板の最小ロジック構成は「74HC139 ×1、74HC373 ×1、74HC368 ×2 (うち空きゲートを /PA13 と音声アンプに流用)、6116 系 2K×8 SRAM ×2」で、オリジナルと同じ IC 種類数 (4種) で再現できる。2KB SRAM は入手性が悪いので、62256 等 32KB SRAM の上位アドレスを GND に固定して代用するのが一般的 (ただし JLCPCB Basic Parts に該当品があるかは未確認)。
- クロック発振は 2SC2021 ディスクリート回路の代わりに 21.47727 MHz の 5V CMOS 水晶発振器モジュールを使うのが部品点数的に有利 (オリジナルは CPU 側をエミッタフォロワでバッファしており、CPU CLK 入力は C9 220pF + R13 150k の AC 結合/バイアス構成。発振器モジュールの直結で良いかは未確認 — NES 系再現基板 OpenTendo は元回路を踏襲)。
- WRAM /CS のダイオード+RC 遅延は書き込みホールド時間対策と見られる (推論)。省略した場合の影響は未確認。

### Gaps
- 74LS 系オリジナルの正確な型番 (LS か HC か) は基板写真で未確認。HVC-CPU-05 図は 74LS139/74LS373、40H368 (または 74HC368) と記載。
- 2A03 /RST 内部プルアップの有無: 外付けプルアップが無いことは2ソースで確認したが、内部プルアップを明記した資料は未発見 (未確認)。
- 電源全体の消費電流、HVC-002 アダプタ定格: 信頼できる数値を発見できず (未確認)。

## 4. CPU / PPU 動作タイミングとメモリマップ

### Takeaway
CPU クロック = 21.47727 MHz ÷ 12 = 1.789773 MHz、PPU ドット = ÷4 = 5.369318 MHz。2A03E/G/H の M2 デューティは 15/24 (High 期間 ≈ 349 ns)。メインボードは $0000-$1FFF (WRAM, 2KB×4 ミラー)、$2000-$3FFF (PPU, 8バイト毎ミラー)、$8000-$FFFF (/ROMSEL) のみデコードし、$4020-$7FFF はカートリッジが A15/A14/A13 と M2 から自前デコードする。

### Cited Findings
- CLK ÷12 (NTSC 2A03)、M2 デューティ 2A03E/G/H = 15/24、初期無印 2A03 = 17/24 — [NESdev CPU pinout](https://www.nesdev.org/wiki/CPU_pinout); [NESdev CPU variants](https://www.nesdev.org/wiki/CPU_variants)
- M2 High 中にアドレスと R/W が有効、データは M2 立下りでのみ保証 — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector)
- PPU CLK 21.47727 MHz を ÷4 でドット/メモリクロック — [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- 1フレーム 262 ライン × 341 ドット、レンダリング有効時の奇数フレームは 1 ドット短い (89341 ドット) — [NESdev NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- CPU メモリマップ: $0000-$07FF 2KB RAM、$0800-$1FFF ミラー、$2000-$2007 PPU、$2008-$3FFF ミラー (8バイト毎)、$4000-$4017 APU/IO、$4018-$401F 通常無効 (CPU テストモード)、$4020-$FFFF カートリッジ — [NESdev CPU memory map](https://www.nesdev.org/wiki/CPU_memory_map)
- 「no circuit in the Control Deck decodes reads from $4000-$4014 or $4018-$7FFF」— [NESdev Open bus behavior](https://www.nesdev.org/wiki/Open_bus_behavior)
- オープンバス: 最後にバス上にあった値が読める。$4016/$4017 はビット 4-0 のみ駆動、ビット 7-5 は直前の値 (通常 $40 の上位 010) — [NESdev Open bus behavior](https://www.nesdev.org/wiki/Open_bus_behavior)
- Mindscape 製ゲーム (Paperboy, Captain Planet, Dirty Harry, Infiltrator, Mad Max, The Last Starfighter) はコントローラ読み値が正確に $41 であることに依存 — [NESdev Open bus behavior](https://www.nesdev.org/wiki/Open_bus_behavior)
- PPU レジスタ読み出しは PPU 内部 I/O バスの値 (書き込み専用レジスタも)。未接続の VRAM アドレス読み出しは通常アドレス下位バイト — [NESdev Open bus behavior](https://www.nesdev.org/wiki/Open_bus_behavior)
- PPU アドレス空間: $0000-$1FFF はカートリッジ (CHR)、$2000-$3EFF はネームテーブル (CIRAM 2KB、カートリッジが CIRAM /CE = /PA13 と CIRAM A10 = PA10 または PA11 を選んでミラーリング決定)、$3F00-$3FFF はパレット (PPU 内部、/WR は出ない) — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector); [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)

### Inferences
- 1 CPU サイクル = 12/21.47727 MHz ≈ 558.7 ns、M2 High ≈ 15/24 × 558.7 ≈ 349 ns、Low ≈ 210 ns (計算値)。
- Raspberry Pi エミュレーションモードで $4016/$4017 の上位ビットを 0 にすると Mindscape 系ゲームで入力が効かないため、上位 3 ビットは $40 (直前のアドレス上位バイト) を返すべき。
- ライン周波数 5.369318 MHz/341 ≈ 15.746 kHz、フレーム ≈ 60.10 Hz (計算値) — JAMMA 15 kHz モニタで同期可能範囲と見込まれる (モニタ側の許容は未確認)。

### Gaps
- 2A03 入力の閾値電圧 (NMOS/TTL) を明記した一次資料は未発見 (未確認)。

## 5. 映像出力レベル

### Takeaway
2C02 VOUT は直流オフセット付きの非標準コンポジット。75Ω 終端時、同期先端 48 mV、ブランク/黒 312 mV、白 ($20) 1100 mV (振幅約 1.05 V)。ファミコンは 2SA937 エミッタフォロワ + 220Ω 直列で RF モジュレータへ。

### Cited Findings
- 75Ω 終端時の測定値 (lidnariq): Sync 48 mV、Colorburst L/H 148/524 mV、$0D 228 mV、$1D (=黒) 312 mV、$2D 552、$3D 880、$00 616、$10 840、$20 (白) 1100 mV。強調ビット時は減衰 — [NESdev NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- 日本の NTSC はセットアップ無し — [NESdev NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- 映像バッファ: PPU pin 21 → 2SA937 (PNP) ベース、エミッタ → 220Ω → VIDEO (2.2k プルアップ) — [HVC-CPU-05 回路図](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf); 部品値は [OpenFC HVC-CPU-07](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A) と一致
- 2C02 は RGB を出力しない (RGB 版は 2C03/2C04/2C05、ピン 14-16) — [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)

### Inferences
- JAMMA モニタはアナログ RGB + 負極性同期入力なので、2C02 のコンポジットをそのまま使えない。RGB 化はコンポジットからのデコード (NTSC デコーダ IC) か、PPU のパレットインデックス/輝度をデジタルに取り出す方式 (NESRGB 等の FPGA 型) が必要。部品点数制約を考えると要検討事項 (本調査範囲外)。

### Gaps
- PPU 無負荷時 (非終端) の VOUT 電圧、PPU 消費電流・発熱の数値は未発見 (未確認)。

## 6. カートリッジコネクタ (60 ピン)

### Takeaway
2.54 mm ピッチ、2 列 × 30。pin 1-30 がラベル側 (正面)、31-60 が裏側。カートリッジ基板厚は 1.2 mm (TGROM 実測)。NES 72 ピン (2.50 mm ピッチ) とはピッチ・配置が異なり非互換。

### Cited Findings
- 全 60 ピン表 (§3.15 と同一。1 GND, 2-13 CPU A11…A0, 14 R/W, 15 /IRQ, 16 GND, 17 PPU /RD, 18 CIRAM A10, 19-25 PPU A6…A0, 26-29 PPU D0-D3, 30 +5V, 31 +5V (一部 RF 基板版ではカートリッジ検出用), 32 M2, 33-35 CPU A12-A14, 36-43 CPU D7…D0, 44 /ROMSEL, 45 Audio from 2A03, 46 Audio to RF, 47 PPU /WR, 48 CIRAM /CE, 49 PPU /A13, 50 PPU A7, 51-56 PPU A8-A13, 57-60 PPU D7, D6, D5, D4) — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector) と [HVC-CPU-05 回路図](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf) で一致
- 方向: CPU A0-A14, R/W, M2, /ROMSEL, PPU /RD, /WR, PPU A0-A13, /A13 は本体→カートリッジ。/IRQ, CIRAM A10, CIRAM /CE はカートリッジ→本体。データバスは双方向。45 は本体→カート、46 はカート→本体 (NESdev 図の矢印は一部不整合があると WebFetch 要約で指摘あり。HVC-CPU-05 図の SOUND I/O の矢印と信号記述に基づく)。
- pin 31: 一部の RF モジュレータ基板版では TV/GAME 切替のみに接続され、カートリッジが 30-31 を短絡したときだけ映像を出す。他の版では通常の 5V — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector)。HVC-CPU-05/07 では P1.31 は電源/RF コネクタの別ピン (+B / VCC2) に接続 — [OpenFC](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A)
- /IRQ は内部プルアップ (メイン基板 RM1 10k も) — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector); [OpenFC](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A)
- ピッチ 2.54 mm (60 ピン) / 2.50 mm (72 ピン)。72 ピンには CIC 端子、EXP0-9、SYSTEM CLK があり音声端子なし。NES は PPU A10/A11 が入れ替わり (63/62)、レイアウトはほぼ鏡像 — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector)
- 基板厚 1.2 mm ±0.05 mm (HVC-TGROM-01 実測)、カードエッジ深さ 10.7 mm、パッド高さ 電源 約 6.7 mm / 信号 約 5.7 mm — [NESdev Famicom cartridge dimensions](https://nesdev.org/wiki/Famicom_cartridge_dimensions) (検索結果スニペット経由、本文未取得)
- 市販 60 ピン 2.54 mm エッジコネクタは 0.062" (1.57 mm) 基板用が多く、ファミコンカートでは緩い — [NESdev forum (検索結果スニペット)](https://nesdev-wiki.nes.science/wikipages/Cartridge_connector.xhtml)
- ファミコンカートリッジは部品がラベルの反対側に実装 — [NESdev Cartridge connector](https://www.nesdev.org/wiki/Cartridge_connector)

### Inferences
- 拡張音源 (VRC6, N163, FDS 等) を鳴らすため、pin 45 に本体の増幅済み音声を出し、pin 46 から戻ってきた信号をアンプ (JAMMA スピーカ) へ送る必要がある。カートが 45-46 を接続しないと無音になる設計なので、移植基板でも同じ配線にする。

### Gaps
- 1.2 mm 基板用 60 ピンコネクタの具体的型番 (Akizuki 在庫品) は未調査。

## 7. コントローラ / 拡張端子プロトコル

### Takeaway
$4016 書き込み bit0 (OUT0) = 両パッドの 4021 P/S (ラッチ)。読み出しは /OE1 ($4016) / /OE2 ($4017) の間だけ 368 を有効にし、同時に M2 を反転したクロックをパッドへ出す (サイクル末の M2 立下り = クロック立上りでシフト)。ボタン順 A, B, SELECT, START, UP, DOWN, LEFT, RIGHT。パッド II の SELECT/START 位置は常に 0。

### Cited Findings
- ボタン順: 0 A, 1 B, 2 Select, 3 Start, 4 Up, 5 Down, 6 Left, 7 Right — [NESdev Standard controller](https://www.nesdev.org/wiki/Standard_controller); 4021 の P8…P1 割当 (P8=A … P1=RIGHT) は [HVC-CPU-05 回路図](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf) で一致
- ストローブ: S=1 の間は連続ロードで A ボタンが読める、1→0 で確定。CLK は通常 High、$4016/$4017 読み出し中 Low、読み出し終了で High に戻りシフト — [NESdev Standard controller](https://www.nesdev.org/wiki/Standard_controller)
- ファミコンでのクロック生成: 368 の 1 ゲートで M2 を反転し /OE で 3 ステート制御 (U7 3A=M2→3Y=4016 CLK、U8 1A=M2→1Y=4017 CLK)、10k プルアップ — [HVC-CPU-05 回路図](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf); [OpenFC ネット U7.6/U8.2 = M2](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A)。NESdev Controller reading は「CLK は R/W と $4016/$4017 デコードの NAND」と NES 一般の説明 — [NESdev Controller reading](https://www.nesdev.org/wiki/Controller_reading) (方式の記述が異なるが、読み出しサイクル中 Low → 終了時立上りでシフトという振る舞いは同じ)
- 8 回読んだ後: 公式 NES コントローラは 1 を返し続ける (DS=GND の 0 が反転されて 1) — [NESdev Standard controller](https://www.nesdev.org/wiki/Standard_controller)。ファミコン本体直結パッドも DS (pin 11) = GND — [HVC-CPU-05 回路図](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf)
- ファミコン読み出しビット: $4016 D0 = パッド I、D1 = 拡張端子、D2 = マイク (パッド II)。$4017 D0 = パッド II、D1-D4 = 拡張端子。ビット 5-7 はオープンバス — [NESdev Input devices](https://www.nesdev.org/wiki/Input_devices); [NESdev Controller reading](https://www.nesdev.org/wiki/Controller_reading); 368 割当は回路図で一致
- パッド II は Select/Start が無く、そのビットは 0 — [NESdev Standard controller](https://www.nesdev.org/wiki/Standard_controller); 回路図ではパッド II 4021 P6/P5 を VCC に固定
- マイクは $4016 D2 に即時 1 ビット (読むたびの瞬時値) — [NESdev Standard controller](https://www.nesdev.org/wiki/Standard_controller)
- 拡張端子コントローラは D1 で同じ 8 ビットを返し、多くのゲームが D0|D1 を OR する (対応しないゲームもある) — [NESdev Standard controller](https://www.nesdev.org/wiki/Standard_controller)
- 拡張端子 15 ピン (DA-15): 1 GND, 2 SOUND, 3 /IRQ, 4-8 Joypad2 /D4…/D0, 9 $4017 /OE (クロック), 10 OUT2, 11 OUT1, 12 OUT0, 13 Joypad1 /D1, 14 $4016 /OE (クロック), 15 +5V。OUT0-2 は APU サイクル (2 CPU サイクル) 毎に更新。RF ファミコンの SOUND は拡張音源ミックス前 — [NESdev Expansion port](https://www.nesdev.org/wiki/Expansion_port); 回路図 §3.14 と一致 (回路図はピン 9/14 を「CUP$」= M2 反転ゲートクロックと表記)
- DPCM 読み出しグリッチ: DMC DMA が $4016/$4017 読み出しと同サイクルに起きるとクロックが余分に入りビットが欠落、典型的には「右」押下の誤検出。PAL 2A07 で修正、NTSC 2A03 は影響あり — [NESdev Controller reading](https://www.nesdev.org/wiki/Controller_reading); [NESdev CPU variants](https://www.nesdev.org/wiki/CPU_variants) (2A07: "Fixed DPCM RDY address bus glitches")
- AV ファミコンはパッド II にも Select/Start があり、マイクなし — [NESdev Standard controller](https://www.nesdev.org/wiki/Standard_controller)

### 同時押し (上下・左右) に関する既知の挙動 — START = U+D+L+R 方式への影響
- [NESdev Game bugs](https://www.nesdev.org/wiki/Game_bugs) 記載:
  - **Clu Clu Land: 上+下+右、上+下+左+右で「プレイヤーがプレイフィールド外の左上隅に引っかかる」**
  - Battletoads: 縦トンネル面で上+下を押すと即死。左右同時で 2D 面で上/後ろへ歩く
  - Mega Man 1/2: はしご上端で上+下 → 壁抜け
  - Panic Restaurant: 上+下 (しゃがみ) でゴミスプライト
  - Spy vs. Spy: 左+右/上+下で飛行機等のゴミスプライト
  - Super Mario Bros. 2: 上+下ではしご高速昇降
  - TMNT / TMNT II: 上+下でゴミスプライト / 異常移動
  - Tetris (任天堂): 左+下+右で現・次ピースのスプライトがちらつく
  - Tiny Toon Adventures / Zelda II: 左+右で異常加速
  - 意図的仕様: Star Soldier の裏技は左+右、左+右+上+下 (コントローラ1と拡張の OR を利用)、Predator は左+右+A/B でレベルスキップ、Star Wars (Namco) は上+下でレベルセレクト、Codemasters 作品は上+下+左+右+A+B+Select+Start でチェックサム確認
  - Tetris 2 + Bombliss: 2P が START を押すとソフトロック (NES / AV ファミコン / 拡張端子コントローラ使用時)
- NESdev フォーラム: Commando は逆方向同時押しで「flat out crash」との投稿 (blargg/baisoku 他) — [NESdev forum t=711](https://forums.nesdev.org/viewtopic.php?t=711)

### Inferences
- U+D+L+R を START として注入する方式は、ゲームによってはゲーム中の誤動作 (Clu Clu Land のスタック、Battletoads 即死など) や隠しコマンド発動 (Star Soldier) を誘発しうる。少なくとも「START 注入は短時間のパルスにする」「ゲーム中は注入しない/DIP で無効化」等の配慮が必要。標準 HVC-001 パッド II には START が物理的に無いため、2P START を U+D+L+R で表現しても多くのゲームでは 2P 側の START は元々意味を持たない。

### Gaps
- U+D+L+R の 4 方向同時押しを START として解釈する既存の慣習・ゲーム側の仕様は見つからず (この方式自体はプロジェクト固有)。網羅的なゲーム別影響調査は未実施。

## 8. 基板リビジョン

### Takeaway
初代 HVC-001 のメイン基板は HVC-CPU-01〜08 → HVC-CPU-GPM-01/02 (1988-89, EMI/VCCI 対策)、AV ファミコン (HVC-101) は HVCN-CPU-01/02 で 74LS139 + 368 ×2 を 1 個のカスタム「JIO」チップに統合。GPM 版では音声アンプ帰還抵抗 R7 が 100k → 43k (音量低下)。

### Cited Findings
- HVC-CPU-01〜-08 (標準): 矩形 20k、TND 12k、各 100Ω 対 GND、1µF → インバータ + 100k 帰還 — [Nerdly Pleasures](http://nerdlypleasures.blogspot.com/2018/01/famicom-nes-simple-tweaks-to-restore.html) (§3 の2ソースと一致)
- HVC-CPU-GPM-01/-02: R7 が 43k、100k に戻すと旧基板の音量に戻る (ただし RF モジュレータが過大入力になる) — [Nerdly Pleasures](http://nerdlypleasures.blogspot.com/2018/01/famicom-nes-simple-tweaks-to-restore.html)
- AV ファミコン HVCN-CPU-01/-02: JIO チップが 74LS139 と 40HC368 ×2 を置き換え。音声混合の R14 68k — [Nerdly Pleasures](http://nerdlypleasures.blogspot.com/2018/01/famicom-nes-simple-tweaks-to-restore.html)
- HVC-CPU-07 (1984 年刻印) は最も一般的でチップセットは主に Rev. E — [OpenFC README](https://github.com/starlightk7/OpenFC); [famicomworld forum](https://www.famicomworld.com/forum/index.php?msg=101483)
- GPM-01 (1988)、GPM-02 (1989, シールド付き、C37 560pF 追加、FC2 移動)。同スレッドは GPM のチップを "rev. H" と記載 — [famicomworld forum](https://www.famicomworld.com/forum/index.php?msg=101483)。ただし 2A03H/2C02H-0 の初出は 1993-12 — [NESdev CPU variants](https://www.nesdev.org/wiki/CPU_variants); [NESdev PPU variants](https://www.nesdev.org/wiki/PPU_variants) → **矛盾。1988-89 年基板なら G 版が妥当 (推論、未確認)**
- HVC-CPU-01〜04 は NCL のリコールで交換され、05 が通常の交換品 — [famicomworld forum](https://www.famicomworld.com/forum/index.php?msg=101483)
- HVC-CPU-08 は 07 の派生で RAM が表面実装 — [ConsoleMods / 検索結果要約](https://consolemods.org/wiki/NES:NES_Model_Differences) (本文未確認)
- HVC-CPU-07 部品: MB8416A-15L RAM ×2、74LS373、74LS139P、7805。GPM-02: XRM6216-10 RAM、74LS373N、74LS139N — [console5 TechWiki Famicom](https://wiki.console5.com/wiki/Famicom) (検索スニペット経由、本文は 403 で未取得)
- GPM 基板では PPU pin 21 をパターンから切り離すとコンポジット改造時の画質改善 — [NESdev PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)

### Gaps
- HVC-CPU-01〜06 各版の IC 表、CPU-08 と GPM の詳細回路差は一次資料未取得 (未確認)。JIO チップの型番・ピン配置は未調査。

## 9. CPU/PPU リビジョン差 (ソフト互換性) と取り外し時の注意

### Takeaway
2A03E/G/H の差はほぼ無いが、最初期の無印 2A03 (1983-84) はノイズの周期モード欠如等の差がある。2C02 は G-0 から OAMDATA/パレット読み出し可能・OAMADDR 書き込みで OAM 破損等の差がある。ドナーが HVC-CPU-07 なら 2A03E + 2C02E(-0) の可能性が高い。

### Cited Findings
- 2A03 無印 (1983-07〜1984-09): M2 デューティ 17/24、ノイズの tonal (周期) モード無し、最短ノイズ周期が異なる、リセットでフレームカウンタ再起動しない、pin 30 未接続。2A03E (1984-10〜1986-06): pin 30 = /RDY。2A03G (1987-04〜1993-11): 基準品、pin 30 = テストモード、後期ロットで DMC DMA バグ。2A03H: 後期 G と差無し — [NESdev CPU variants](https://www.nesdev.org/wiki/CPU_variants)
- 2C02A/B: X=255 のスプライト誤表示。2C02E-0 以前: OAMDATA とパレット RAM が読めない、OAM 評価のバグ。2C02G-0: OAMADDR 書き込みで OAM 破損、OAMADDR≥8 でレンダリング開始時に破損、カートリッジ ROM バスの反射で OAM 破損 (CPU-カート間の直列抵抗で対策)。2C02H-0: G-0 の一部を修正 — [NESdev PPU variants](https://www.nesdev.org/wiki/PPU_variants)
- ソフト影響例: Micro Machines / Super Cars は 2C02G より前で表示不具合、Topple Zip は G 以降でゴミスプライト、Balloon Fight は有字 CPU のみの周期ノイズを使用 — [NESdev Game bugs](https://www.nesdev.org/wiki/Game_bugs)
- TST (pin 30) は GND 固定 (G 版で High にすると $4016/$4017 がオープンバスになる) — [NESdev CPU pinout](https://www.nesdev.org/wiki/CPU_pinout)
- 取り外し・故障: 信頼できる網羅的資料は見つからず。フォーラム報告として、取り外し作業でパターン/パッド損傷、近傍コンデンサ損傷、PPU を壊した例、ソケット化が推奨される — [nesdev.nes.science アーカイブ (検索結果要約)](https://archive.nes.science/nesdev-forums/f9/t15230.xhtml)
- 互換品 UA6527 (CPU) は矩形波デューティが入れ替わっている、UA6528 (PPU) は全ゲーム互換か不明 — [OpenTendo BOM](https://github.com/Redherring32/OpenTendo/tree/master/BOM)

### Inferences
- G-0 の「カートリッジバス反射で OAM 破損」対策として、新基板では CPU データ/アドレスとカートリッジ間に直列ダンピング抵抗 (NES 後期基板相当) を検討する価値がある。
- 取り外しは基板側を切断してピンを1本ずつ抜く/全ピン同時加熱 (ホットエア/デソルダリングガン) が一般的手法。NMOS チップは静電気に比較的強いが ESD 対策は必要 (一般論、未確認)。

### Gaps
- 2A03/2C02 の消費電流・典型的故障モードの定量資料は未発見。

## 10. オープンソース再現マザーボード

### Takeaway
ファミコン用は **OpenFC (starlightk7) — HVC-CPU-07 再現、KiCad、CERN-OHL-S**、NES 用は **OpenTendo (Redherring32) — NES-CPU 前面ロード機再現、KiCad v8、TAPR OHL**、同作者の OpenTendo-TopLoader (NES-101)。いずれもオリジナル CPU/PPU を DIP-40 で使用。

### Cited Findings
- OpenFC: https://github.com/starlightk7/OpenFC — ライセンス CERN-OHL-S (GitHub API spdx: CERN-OHL-S-2.0)、KiCad (.kicad_sch/.kicad_pcb)。HVC-CPU-07 (Rev A) リリース済、GPM-01/02・HVCN-CPU-02 等は計画/作業中。電源/AV 基板 OFC-PWRAV-01 (SFC 型電源/音声回路 + THS7314 コンポジット)。コントローラ基板 56.8231B / 56.8232A も KiCad で公開。最終コミット 2026-04-24 — [OpenFC README](https://github.com/starlightk7/OpenFC) (README の表で HVC-CPU-01〜06 も "AV Famicom / New Famicom" と記載されているのは誤記と思われる — 推論)
- OpenFC HVC-CPU-07 の部品シンボル: 74HC139、74HC373、40H368 ×3 (シート重複のため実数は要確認)、S-RAM 2K×8、2SC2021 ×2、2SA937、21.47727 MHz 水晶、TC1 30pF トリマ — [OpenFC KiCad](https://github.com/starlightk7/OpenFC/tree/main/Motherboards/HVC-CPU-07/Rev%20A)
- OpenTendo: https://github.com/Redherring32/OpenTendo — 1985 年前面ロード NES 再現、KiCad v8、Rev v1.4、TAPR Open Hardware License、2 層 119×196 mm 1.6 mm。オリジナルから流用: RP2C02/RP2A03、CIC 3193A、A937、C2021 ×2、DAN601、UPA64H — [OpenTendo README](https://github.com/Redherring32/OpenTendo); [BOM](https://github.com/Redherring32/OpenTendo/tree/master/BOM)
- OpenTendo の現代代替部品: SRAM 6116SA15SOG (SOIC, 要変換基板) または 6116SA15TPG (DIP)、SN74HC373N、SN74HC139N、SN74HC368N ×2、SN74HCU04N、水晶 ECS-214-S-4X (21.47727 MHz)、TC1 GKG30015 (6.5-30 pF)、51pF の代わりに 56pF で動作確認、DIP-40 ソケット ED40DT — [OpenTendo BOM](https://github.com/Redherring32/OpenTendo/tree/master/BOM)
- OpenTendo-TopLoader: https://github.com/Redherring32/OpenTendo-TopLoader — NES-101 再現、KiCad、TAPR OHL、2 層 106.1×155 mm — [README](https://github.com/Redherring32/OpenTendo-TopLoader)

### Inferences
- 本プロジェクトのリファレンスとしては OpenFC HVC-CPU-07 が最適 (60 ピンスロット、ファミコン配線、KiCad)。CERN-OHL-S は強い相互主義ライセンスのため、派生設計を配布する場合はソース公開義務が生じる点に注意。OpenTendo (TAPR OHL) は NES 72 ピン/CIC 前提だが、HC 系代替部品の実績がある。
- いずれの再現基板も 2SC2021 ディスクリート発振とオリジナルの映像/音声回路を踏襲しており、JLCPCB Basic Parts 化 (SMD 化、発振器モジュール化) は独自設計が必要。
