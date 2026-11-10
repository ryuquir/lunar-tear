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

(以降のセクションは調査進行に応じて追記)
