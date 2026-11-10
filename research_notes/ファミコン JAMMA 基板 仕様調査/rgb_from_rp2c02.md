# RP2C02 から 15kHz アナログ RGB を得る方法（JAMMA 基板向け調査）

（調査中・途中保存版。2026-11-10）

## 1. RGB 出力 PPU（2C03/2C04/2C05）

### Takeaway
RGB PPU は RP2C02 と同じ 40pin で、EXT0-2(pin14-16) が R/G/B アナログ出力、pin17(EXT3) が GND、pin21(VOUT) が CSYNC に置き換わる。パレットは 2C03 が 3bit/ch、2C04 はスクランブル、2C05 は $2000/$2001 入替と $2002 ID。

### Cited Findings
- RGB PPU は EXT3..0 と VOUT を RGB 映像用信号に置き換える。図上 R=pin14, G=pin15, B=pin16, pin17=GND, pin21=CSYNC。「EXT3 is internally and externally tied to ground: perhaps it serves as an analog ground for the video DACs」 — [NESdev Wiki PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- 2C02 の EXT3..0(pin14-17) は双方向。PPUCTRL の slave ビットでパレットインデックスを出力、クリア時は入力として backdrop 色選択。「No official console uses the output mode, so these are normally grounded」 — [NESdev Wiki PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- 2C03 パレット（R,G,B 各 0-7、8bit 換算 C=255*DAC/7）は NESdev Wiki に 64 エントリ表あり。$0D/$1D 等 hue D は 2C03(PC-10)と 2C05-99 で黒 — [NESdev Wiki PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)
- 2C04-0001〜0004 は同一マスターパレットの並べ替え。2C03/5 パレットのほぼ上位集合（グレー4色+他6色追加） — [NESdev Wiki PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)
- 2C05 は後期 VS. ゲームのコピープロテクト用。2C05-99 は Sharp ファミコンタイトラー。`A0' = A0 xor (A1 nor A2)` 回路で PPUCTRL と PPUMASK を入れ替えれば 2C03 として動く — [NESdev Wiki PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)
- 2C05 は $2002 の bit4-0 に ID を返す（2C05-02:$3D, -03:$1C, -04:$1B） — [NESdev Wiki PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- RGB PPU の強調ビットは減光ではなく該当チャネルをフル輝度にする（3ビット全部で真っ白）。グレースケールは 2C02 と同じだが 2C04 ではインデックス上で第1列に強制するだけでグレーにならない — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes), [PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- 使用機種: 2C03 = VS. Duck Hunt, VS. Tennis, PlayChoice-10 全般, Sharp C1(ファミコンテレビ)。2C04 = 多くの VS. System。2C05 = 後期 VS.、2C05-99 = ファミコンタイトラー — [NESdev Wiki PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)

## 2. PPU 内部状態（パレットシャドウに必要）

### Cited Findings
- PPUCTRL bit6: 0=EXT から backdrop 読込, 1=EXT へ色出力。「should never be set on stock consoles because it may damage the PPU」。コンポジット出力には影響しない — [NESdev Wiki PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- $2002 読出しで w トグルクリア。$2006 は上位→下位の2回書込み。$2007 アクセス後 PPUCTRL bit2 により +1/+32。パレット読出しは内部バッファを介さず即時、上位2bit は PPU open bus。パレット読出しは全 PPU にない機能 — [NESdev Wiki PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- backdrop は $3F00 と $3F10 双方から書ける。パレット RAM 全体は $3F00-$3FFF にミラー。強制ブランク中に v がパレットを指すとその色が描画（backdrop override） — [NESdev Wiki PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)

## 3. NESRGB（Tim Worthington）

### Cited Findings
- PPU ソケットに挿すボード。Altera PLD が PPU と CPU データバスの間に入り、パレット RAM への書込みを捕捉・保存し、改変データを PPU に渡す。PPUCTRL への書込みを横取りして EXT0-3 を出力に。PPU に渡すデータからは EXT0-3 で得られる情報を除去。残り（EXT4=スプライト/BG ビット、ブランキング、同期）はビデオ出力からコンパレータで抽出 — [etim.net.au/nesrgb](https://etim.net.au/nesrgb/)
- 元アイデアは NESdev フォーラムの HardWareMan と thefox。フレームバッファなし・遅延なし 15kHz 出力。PAL/NTSC 両対応 — [etim.net.au/nesrgb](https://etim.net.au/nesrgb/)
- NESRGB ハード世代: v1.x/v2.x = Altera EPM570T100 (MAX II CPLD, VCCINT 3.3V)、v3 (2022) = EPM240T100 (コア 1.8V、パレット1種のみ)、v4 = 「RAM based FPGA and a helper microcontroller」（コントローラ読取用 MCU、起動に時間がかかり NES のリセット容量を 100n→220n に交換）、v5 ドキュメント 2026-04-30 作成 — [Software and Errata](https://etim.net.au/nesrgb/background_fault/), [NESRGB40](https://etim.net.au/nesrgb/NESRGB40.html), [NESRGB5](https://etim.net.au/nesrgb5/)
- NESRGB 内蔵パレット: RGB Playchoice (Nestopia 2013), FCEUX, YUV, Unsaturated-V6/Smooth/Digital Prime/Magnum (FirebrandX), Sony CXA, Wavebeam 等。「de-jitter」機能は NTSC で同期不安定を起こし v2.2 で sync 補正削除、v2.3 で機能全削除（実験版）— [Software and Errata](https://etim.net.au/nesrgb/background_fault/)
- 原理（Quietust, 2020-08-06）: PPU を slave(EXT 出力)モードにする。EXT は 4 本しかないので BG とスプライトを区別できない。PPU に特殊パレットを与え、全 BG 画素を1色（おそらく黒）、不透明スプライト画素を別色（おそらく白）にし、コンポジット信号から最上位パレットビットを復元する。そのため PPU 原コンポジットは「黒地に白い塊」になる — [NESdev forum t=20636](https://forums.nesdev.org/viewtopic.php?t=20636)
- 同原理は Nerdly Pleasures でも説明（BG パレットは全て黒、スプライトパレットは全て白）— [Nerdly Pleasures](http://nerdlypleasures.blogspot.com/2015/06/nes-hardware-explained.html)（検索スニペットのみ、本文未取得）

## 4. 他の EXT 方式クローン / 代替機器

### Cited Findings
- **LavaRGB**（krzysiobal ほか、Famicom AV 用）: FPGA が PPU と CPU データバスの間に入り $2000 書込みを bit6 セットして PPU に転送、パレット書込みを監視して内部に完全コピーを保持。$2007 経由のパレット書込み時に改変データを書き、BG とスプライトを別グレー（モノクロ2階調）にして第5ビットとする。3つのコンパレータ（閾値違い）でビデオ出力から vblank・走査線開始・スプライト/BG を検出。FPGA は Lattice。クロックは 100Ω 経由で FPGA へ直結、他は 3.3-5V 変換バッファ経由。PPU_RD, /WR, ALE は FPGA に未接続 — [NESdev forum t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)
  - 注: 同スレ要約では「PPU pin 1 (video out)」とあるが、2C02 の VOUT は pin21（[PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)）。要約誤記の可能性。未確認。
  - 既知の欠陥: レンダリング中の v 増加を模擬しないため Codemasters 系（Dizzy, Micro Machines, MiG-29）で色化け。レンダリング無効時の色挙動も再現しない（Fiskbit）。
  - WDL6528（クローン PPU）14個中多数でスプライトのみアーティファクト。原因はビデオ電圧レベルで、R9 7.15k→10k に変えてコンパレータ閾値(1.92V)を下げて解決。RP2C02G/H, UA6528 は問題なし → **コンパレータ閾値は PPU 個体/品種の出力レベル依存**。
  - ライセンス記載なし。参照: lava-fc.top, github.com/v5100v5100, PCBWay プロジェクト。
  - Fiskbit: グレースケールは「ANDing the 6-bit palette color value with $30」なのでグレースケールで情報を得る案は約3階調しかなく不可。
- **RGB Blaster**（Krikzz）: 無改造ファミコンのカートリッジ端子の PPU バスを盗聴し、OAM は CPU の書込み（DMA）を追跡して FPGA 内で PPU を再実装。EXT は使わない（無改造機では接地）。タイミングに敏感で一部 PPU 品種や高度なマッパー（MMC5 等）で不具合 — [nicole.express](https://nicole.express/2023/that-blasted-rgb.html)
