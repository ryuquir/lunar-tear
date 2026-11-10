# RP2C02 の EXT 方式（NESRGB 方式）と RGB 出力 PPU — 第2パス詳細調査（未解決点の詰め）

調査日: 2026-11-10。前提ノート: `rgb_from_rp2c02.md`（第1パス）。
表記: 「Cited Findings」= 出典付き事実（URL 明記）。「Inferences」= **推論**（筆者の判断、出典なし）。確認できなかった事項は **未確認**。
取得方法の注記: nesdev.org は curl では Cloudflare チャレンジで取得不可のため WebFetch で本文を取得。GitHub は raw.githubusercontent.com から直接取得（Lava RGB の BOM・ファーム zip、TinyNES 回路図 PDF、Breaking NES Wiki の Markdown/画像）。ダウンロードしたファイルは /tmp 配下でのみ解析した。

---

## 1. EXT0-3 出力（master）モードの論理レベル・駆動・タイミングと出力内容

### Takeaway
PPUCTRL($2000) bit6=1 で EXT0-3 は「パレットインデックス下位4bit」を画素ごとに出力し、内部では BG/スプライト優先選択直後の値を /PCLK でラッチして出す（パレット RAM・DAC より前段）。透明画素はその BG スライバーのパレット entry 0、レンダリング無効時は常に 0、backdrop override は EXT に出ない。出力電圧・駆動電流・EXT→VOUT の遅延（ns/画素数）を定量化した公開資料は見つからず **未確認**。既存品（NESRGB・Lava RGB）は EXT 側を遅延/FIFO で VOUT 由来の第5ビットに揃えている。

### Cited Findings
- 出力内容（NESdev Wiki）:「Setting bit 6 causes the PPU to output the lower four bits of the palette memory index on the EXT pins for each pixel.」「Since only four bits are output, background and sprite pixels can't normally be distinguished this way.」「Note that EXT output for transparent pixels is not a backdrop color as normal, but rather entry 0 of that background sliver's palette.」「When rendering is disabled, EXT output is always index 0 regardless of backdrop override.」「Setting this bit does not affect the image in the PPU's composite video output.」— [PPU programmer reference](https://www.nesdev.org/wiki/PPU_programmer_reference)
- 同旨の独立ソース（2C02 ダイ解析, Breaking NES Wiki, CC0）: マルチプレクサは「第1段で BG/スプライト選択（優先度 /ZPRIO）→第2段で EXT 入力との選択→第3段で TH カウンタの direct color（パレット直接アクセス時）」のカスケード。出力は「Color for external terminals (/EXT Out) (4 bits)」— [Breaking NES Wiki: Multiplexer](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/mux.md)。EXT パッド論理図では、マルチプレクサ出力 n_EXT_OUT が **n_PCLK を enable とする DLatch** を通り、n_SLAVE（$2000 bit6 の反転）でゲートされた出力バッファから EXT_Pad_Out に出る（入力側は透過 DLatch→EXT_IN）— [pads.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md)、図 [pads_ext.jpg](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/pads_ext.jpg)。PCLK 分配の表にも「/PCLK output for EXT terminals」がある — [pclk.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pclk.md)
  - →（direct color は第3段なので）backdrop override（強制ブランク中に v が $3Fxx を指すとその色を描く機能）は EXT に出ない、という Wiki の記述と回路構造が整合。
- 1 画素 = PCLK 1 周期 = CLK/4: NTSC CLK 21477272 Hz（~0.046 µs）、PCLK 5369318 Hz（~0.186 µs）— [pclk.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pclk.md)
- VOUT 側の遅延: カラーバッファ (CB) 出力は位相発生器へ直行せず D-Latch 連鎖を通る（「the video generator essentially outputs pixels "from the past"」）— [Breaking NES Wiki: CRAM](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/cram.md)。NTSC の映像出力は PPU 内部の画素タイミングより 1 pixel clock 遅れる — [NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- 既存品の位置合わせ: NESRGB v1.0 ブロック図では EXT0..EXT3 →「DELAY」→「EXT DATA SYNCHRONISE」（PIXEL CLOCK 入力）でコンパレータ由来の「EXT4-VIDEO」と合流 — [NESRGB operation block diagram](https://etim.net.au/nesrgb/operation_block_diagram.png)。Lava RGB ファーム更新履歴（2023-07-02）「使用FIFO实现ext4和ext0-3数据对齐，大大提升稳定性」（FIFO で ext4 と ext0-3 を揃え安定性向上）— [lava-rgb-kit firmware zip 内 readme.txt](https://github.com/v5100v5100/lava-rgb-kit)
- 1 画素ずれ: Fiskbit「they have sync issues where the digital and analog sources may be off by 1 pixel on some power cycles」「causing color fringes on one edge of all sprites」（アナログ映像の BG/スプライト遷移が速く変化しないことによるスプライト縁のちらつきにも言及）— [NESdev forum t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)
- 駆動・電圧: Wiki 等は「EXT が GND 直結の機体で出力すると VCC–GND 短絡になり得る」ことしか述べない（「could potentially damage the chip whenever it outputs a non-zero pixel value」）— [PPU programmer reference](https://www.nesdev.org/wiki/PPU_programmer_reference), [Myths](https://www.nesdev.org/wiki/Myths)。2013 年の Wiki 文言検証スレッドでも試験・電圧の記述なし — [nesdev.nes.science t9936](https://nesdev.nes.science/f3/t9936.xhtml)。2 PPU 構成スレッドも駆動能力・電圧・遅延は扱わない — [forum t=16479](https://forums.nesdev.org/viewtopic.php?t=16479)
- 実装例の接続: Lava RGB は EXT0-3 を 3.3V 側の EXT0_3V3〜EXT3_3V3 へレベル変換して FPGA（LCMXO2）に入れる（回路図ネット名、BOM に SN74LVC541APW×2・SN74LVC4245APWR×2）— [lava-rgb-kit（FC_RGB.SchDoc / out/Lava_RGB_Bom.xlsx）](https://github.com/v5100v5100/lava-rgb-kit)。TinyNES は EXT0-3 を各 10kΩ で GND へプルダウン（R25-R28）— [TinyNES Main Board Schematic (CC BY-SA 4.0)](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf)
- RP2350 の 5V 耐性: 「RP2350 is now officially 5V tolerant」、条件「keep IOVDD powered when 5V is applied to any GPIO pad, otherwise the pad will be damaged」— [Raspberry Pi news (A4/RP2354)](https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/)。対象外ピンについては読者コメント「GPIOs 0-25 (not the ADC ones)」のみ（公式本文ではない → ADC 兼用ピン除外は **未確認**、データシートの「FT」表記で要確認）。

### Inferences（推論）
- EXT は PCLK に同期した 1 画素 1 値の 4bit デジタル出力なので、外部サンプラは「PCLK の中央付近（/PCLK ラッチ後に安定した区間）」で取ればよい。サンプル位相を決める基準として、ALE（1 PPU サイクル High、VRAM アクセス毎）または自前で制御した /RST 解除時刻（第3節）が使える。
- 2C02 は NMOS で出力 High は 5V 未満（NMOS プルアップ/スーパーバッファ）と考えられ、74HC（CMOS 入力 V_IH≈3.5V@5V）で受けるのはマージン不明。安全側は 74HCT/74LVC/74AHCT（TTL 閾値）か RP2350 直結（5V トレラント・TTL 互換の 3.3V 入力）。いずれも V_OH 実測が必要（**未確認**）。
- EXT→VOUT の相対遅延は固定数 PCLK（パレット参照＋CB 遅延連鎖分）と考えられるが値は **未確認**。MCU 実装では「EXT サンプル列」と「第5ビット（コンパレータ）サンプル列」を別々に取り、ライン単位でシフト量を校正（例: 既知の sprite 0 位置や起動時テストパターン）するのが現実的。

### Gaps
- EXT 出力の V_OH/V_OL・駆動電流・立上り時間、PCLK エッジからの出力遅延（ns）、VOUT 上の同一画素までの遅延（PCLK 数）: いずれも一次資料なし **未確認**。Visual 2C02 シミュレータでの検証は今回実施していない（Breaking NES Wiki の回路解析で代替）。
- 水平/垂直ブランキング中に EXT が何を出すか（backdrop index 0 か不定か）: **未確認**。

---

## 2. NESRGB / Lava RGB が PPU に書く改変パレット、コンパレータ構成、公開状況

### Takeaway
公開資料で確認できる改変パレットは「BG 16 エントリ全部を黒、スプライト 16 エントリ全部を白」（NESRGB 作者 viletim の 2013 年説明、Hi-Def NES も同方式）までで、**具体的な色番号（$0F/$1D/$20/$30 等）は NESRGB・Lava・Hi-Def NES のいずれも未公開（未確認）**。kevtris は「NESRGB と Hi-Def NES は少し異なるパレットエントリを使う」と述べている。コンパレータは Lava RGB が 3 回路（LMV7219 ×1 + TLV3502 デュアル ×1、ネット名 VOUT_CS / VOUT_BLANK / EXT4）、NESRGB v5 も 3 回路（GSV331≒MCP6561 + MX3502S≒TLV3502）。Lava RGB は Altium 回路図・基板・BOM・ファーム（.jed のみ、HDL なし）を GitHub に公開しているがライセンス表記なし。HDL 公開は PPU-LITE / LAVA_RGB-TO-PPU_LITE / RP2C02-7-（いずれも GPL-3.0、ただし PPU 置換型で EXT 方式ではない）。

### Cited Findings
- NESRGB の改変パレット: viletim（=Tim Worthington）2013-01-12「The PPU instead gets a special palette - the 16 sprite entries are all white and the 16 background entries are all black.」「The fifth pixel bit then plops right out where the video used to be!」— [NESdev forum t=9561 p.4](https://forums.nesdev.org/viewtopic.php?t=9561&start=45)。NESRGB 公式: 「Modified data is passed to the PPU」「The modified data passed to the PPU removes data already available at the EXT0-3 outputs.」「The rest of the information required (EXT4, blanking, and sync) is extracted from the video output with comparators.」— [etim.net.au/nesrgb](https://etim.net.au/nesrgb/)
- Lava RGB: krzysiobal 2025-04-15「passes modified data to PPU via $2007 when palette range is written」「all background entries got one index and all sprites index got another one」、「There are 3 comparers with different threeshold」（vblank・走査線開始・スプライト/BG を検出）、R9=7.15k を大きく（10k）して WDL6528 問題解消、比較レベル 1.92V — [NESdev forum t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)（具体的な色番号の記載なし）
- Hi-Def NES: kevtris 2015-07-12「the nesRGB uses a slightly different set of palette entries from the HidefNES does」（NESRGB 互換用ソルダージャンパあり）、2015-08-30「The RGBNES tries to "lie" to the PPU by adjusting the data written to the PPU when 2000 or 2007 are written to.」「The HDN board has a jumper you can solder to make it "lie" to the PPU in the same way the NESRGB does it.」; 2016-11-26 ユーザ報告「RF is just showing the sprites as white on a black background」に tepples が bit4 出力のためと説明 — [Hi-Def NES スレッド アーカイブ t12019](https://archive.nes.science/nesdev-forums/f9/t12019.xhtml)
- **Lava RGB の BOM（一次資料）**: `out/Lava_RGB_Bom.xlsx`（Lava_RGB_Kit_V1.1(hardware).zip 内）— [github.com/v5100v5100/lava-rgb-kit](https://github.com/v5100v5100/lava-rgb-kit)

  | Ref | 部品 | 役割（ネット名からの判断は推論） |
  |---|---|---|
  | U7 | LCMXO2-1200HC-4TG100I（Lattice MachXO2） | メインロジック |
  | U2 | LMV7219M5X | 高速コンパレータ ×1 |
  | U5 | TLV3502AIDR | 高速デュアルコンパレータ（2 回路）|
  | U3 | SGM8051XN5/TR | 映像用 OP アンプ |
  | U4 | BH7240AKV | RGB→コンポジット/S エンコーダ |
  | U6, U8 | SN74LVC4245APWR | 5V↔3.3V 双方向バス変換（CPU 側・PPU 側データ）|
  | U9, U11 | SN74LVC541APW | 5V 入力→3.3V バッファ |
  | U1 | MCP1703T-3302E/MB | 3.3V LDO |
  | R9 | 7.15kΩ | フォーラムで言及の閾値抵抗 |
  | R7 / R19 / R11 | 16kΩ / 100kΩ / 300Ω | 閾値分圧等（接続は未解析）|
  | R13-R18 | 75Ω ×6 | 映像出力直列 |

  回路図（FC_RGB.SchDoc）中のネット名: `PPU_VOUT`, `VOUT_CS`, `VOUT_BLANK`, `EXT4`, `VBL`, `EXT0..3` / `EXT0_3V3..EXT3_3V3`, `CPU_SIDE_D0..7_5V/3V3`, `PPU_SIDE_D0..7_5V/3V3`, `CPU_SIDE_DIR`, `CPU_SIDE_OE`, `PPU_SIDE_OE`, `CPU_A0..2`, `CPU_R/W`, `PPU_CS`, `NEW_CLK`, `SRC_CLK`, `FC_RST`, `RST_3V3`, `RGB_R0..7/G0..7/B0..7`, `SUBCARRIER` — 同リポジトリ（SchDoc 文字列から抽出）。→ コンパレータ 3 回路の出力名は「複合同期 (CS)」「ブランキング」「EXT4（第5ビット）」と読める（**推論**、配線は未解析）。
  - ファーム: `Lava_RGB_Kit(firmware).zip` は .jed（9 種、パレット組合せ別: CXA+PC10, FCEUX+NTSC 等）と readme.txt のみ。HDL ソースは含まれない。リポジトリに LICENSE なし（GitHub 上もライセンス表示なし）— 同上
- **NESRGB v5 の映像入力アナログ部**: 「U10 GS8051-TR (alt. OPA356AIDBVR), U11 GSV331-TR (alt. MCP6561UT-E/OT), U12 MX3502S (alt. TLV3502AIDR)」、映像ドライバ U8 GS8051-TR — [NESRGB5 test mode](https://etim.net.au/nesrgb5/testmode/)
- NESRGB ブロック図: VIDEO BUFFER → COMPARATORS → SYNC / BLANKING / EXT4-VIDEO。TIMING ブロックに PPU の CLK・/RES・INT が接続。RGB は 7:7:7 で DAC へ。「TTL COMPOSITE SYNC (CS#)」出力あり — [NESRGB operation block diagram](https://etim.net.au/nesrgb/operation_block_diagram.png)。基板パッド: R/W, DP0-7/DB0-7（PPU 側/CPU 側データ）, A0-A2, CE#, EXT0-3, CLK, INT#, RST#, VIDEO、J8「composite sync output type. Open for TTL, short for 75 ohm」— [NESRGB-Pinout.pdf](https://etim.net.au/nesrgb/NESRGB-Pinout.pdf)
- NESRGB の回路図・PLD ソース: 公式ページに公開なし（ピン配置 PDF のみ）— [etim.net.au/nesrgb](https://etim.net.au/nesrgb/)
- オープンソース実装（いずれも PPU 全体を FPGA で置換する方式、EXT 方式ではない）:
  - PPU-LITE（andkorzh）: GPL-3.0（LICENSE 冒頭「GNU GENERAL PUBLIC LICENSE Version 3」）、Cyclone I EP1C3T100C8N、R2R DAC「6-bit plus one-bit emphasis per channel」、Lattice Diamond 版も追加 — [PPU-LITE README](https://raw.githubusercontent.com/andkorzh/PPU-LITE/main/README.md), [LICENSE](https://raw.githubusercontent.com/andkorzh/PPU-LITE/main/LICENSE)
  - LAVA_RGB-TO-PPU_LITE: Lava RGB 基板を FPGA PPU に転用、「It requires removing the comparators from the board」— [README](https://raw.githubusercontent.com/andkorzh/LAVA_RGB-TO-PPU_LITE/main/README.md)（LICENSE ファイルは raw で見つからず **未確認**）
  - RP2C02-7-（andkorzh）: GPL-3.0、Verilog（RP2C02.v 1672 行、EXT 端子は実装なし）— [GitHub](https://github.com/andkorzh/RP2C02-7-)
  - Breaking NES（emu-russia/breaks）: CC0 1.0（フォーク一覧表示）— [v5100v5100 リポジトリ一覧](https://github.com/v5100v5100?tab=repositories)
- マイコンによる EXT 方式の再実装: 見つからず（第5節）。

### Inferences（推論）
- 黒/白を選ぶ理由: 2C02 の $x1〜$xC は $xD と $x0 のレベル間で交互する方形波（色副搬送波）を出すが、$x0（$00/$10/$20）・$xD・$xE/$xF は平坦な DC レベル（[NTSC video](https://www.nesdev.org/wiki/NTSC_video)）。BG・スプライトをそれぞれ平坦な色にすれば、比較器 1 個の単純な閾値で第5ビットが取れる。候補は BG=$0F（=$1D と同電圧 312 mV 終端時）、スプライト=$20/$30（1100 mV）。
- **ブランキング検出との矛盾点**: BG を $0F/$1D にするとブランキング（blank=$1D と同レベル）と区別できない。NESRGB / Lava は「ブランキング」用コンパレータを別に持つので、(a) BG を $0F より明るい平坦レベル（例 $2D 552 mV、$00 616 mV）にしている、または (b) ブランキング比較器はカラーバースト/同期を見て水平タイミングを作っている、のいずれかと考えられる。公開資料からはどちらか判定できない（**未確認**）。自作する場合は (a)「BG=$00（または $2D）、スプライト=$20」とし、閾値を sync<th1<blank<th2<BG<th3<sprite に置くと 3 比較器で同期・ブランキング・第5ビットが分離できる（推論、要実測。$00 と $2D は emphasis 時に ×0.816 で下がる点に注意 — 強調ビットは PPU に渡さず外部で適用すれば影響しない）。
- PPU への $2001 書込みの強調・グレースケールビットを外部側で処理し PPU 側では 0 にマスクすれば、PPU のコンポジットは常に 3〜4 レベルの平坦な信号になり閾値設計が楽になる（推論。PPU 側を改変する設計は NESRGB の「Colour data filter」と同じ発想）。

### Gaps
- NESRGB / Lava / Hi-Def NES が実際に書き込む色番号、閾値電圧（Lava の 1.92V 以外）と分圧値の対応: **未確認**（Lava SchDoc のバイナリ配線解析は未実施。フォーラム添付 `lava_11_sch.png` は未取得）。
- Lava RGB のライセンス: 表示なし（著作権者の許諾なしに回路を流用できるかは不明）。

---

## 3. 画素位相合わせ（PPU の CLK/4 分周）と CPU/PPU アラインメント

### Takeaway
2C02 の /RST（pin22）は **PCLK 分周器（CLK/4）・映像位相発生器・H/V カウンタ・偶奇フレームフラグを初期状態に戻す**（NESdev Wiki と Breaking NES のダイ解析で一致）。一方 2A03 の CLK/12 分周器は reset の影響を受けない（Fiskbit）。Famicom は PPU /RST を +5V 直結なので PPU 分周器の位相は電源投入ごとにランダム、NES は CPU と同時にリセットされるがやはり CPU 分周器との位相はランダム（NTSC で 4 通り）。新基板が自前の発振器で CLK を作り、/RST を CLK に同期して解除すれば PPU の画素位相は毎回既知になり、さらに M2 の位相を見て解除時刻を決めれば CPU/PPU アラインメントも固定できる（推論、要実機確認）。

### Cited Findings
- /RST の効果:「Returns the following to power-on state: Clock divider, Video phase generator, Scanline/pixel counters, Even/odd frame toggle」、PPUCTRL/PPUMASK/PPUSCROLL/読出しバッファは 1 フレーム間 0 保持。「The Famicom ties it to +5V」。2 PPU 構成では /RST で同期（genlock）できる — [NESdev Wiki: PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- ダイ解析: /RES パッドは非同期の「Reset FF」をセットし、RES 信号は H/V カウンタ各ビットの「global reset signal of all sequential PPU circuits」— [Breaking NES Wiki pads.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md), [hv.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/hv.md)。PCLK 分周器のリセット時波形（RES=1 の間 PCLK/​/PCLK が固定され、解除後に一定位相で分周開始）— [pclk_reset.png](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/pclk_reset.png)（[pclk.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pclk.md) の「Reset Status」）。電源投入時の分周ラッチ値は「more correct to assume that the value of the latches is undefined (x)」— 同 pclk.md。任天堂の特許も複数 PPU の /RES を共通にして H/V を同時リセットすることを提案（図 ext_pads.png: 共通 CLOCK 21.48 MHz・共通 RESET）— [pads.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md)
- 「The CPU clock divider is not affected by reset.」「The PPU clock divider is affected by reset. Therefore, resetting the PPU changes the CPU/PPU sub-cycle alignment.」— [NESdev Wiki: User:Fiskbit](https://www.nesdev.org/wiki/User:Fiskbit)（ユーザページの下書きであり正式記事ではない点に注意）
- アラインメント数: blargg 2010-03-17「Nope, there are four for NTSC.」「It's due to the PPU and CPU using separate dividers.」「After power/reset, PPU is randomly in one of four synchronizations with CPU.」— [NESdev forum t=6186](https://forums.nesdev.org/viewtopic.php?t=6186)。Wiki も「The beginning of a CPU tick could be offset by 0-3 master clock ticks from the nearest following PPU tick.」— [PPU frame timing](https://www.nesdev.org/wiki/PPU_frame_timing)。一部機体ではアラインメント 4 通りのうち 1 つでパレット読出しが壊れる — [PPU programmer reference](https://www.nesdev.org/wiki/PPU_programmer_reference)
- Famicom と NES: 「PPU /reset is tied to 5V, and CPU /reset is connected to a 0.47µF capacitor.」（Famicom、PPU 初期化は CPU リセットより約 1 フレーム早く始まる）「On the NTSC NES, the PPU and CPU are reset at the exact same time.」; リセット後約 29658 CPU クロックは PPUCTRL/PPUMASK/PPUSCROLL/PPUADDR への書込みが無視される — [PPU power up state](https://www.nesdev.org/wiki/PPU_power_up_state)
- 2A03 の分周: CLK pad → Divider CLK/12 → PHI0、M2 は PHI2 より 1.5 CLK 早く High になる — [Breaking NES Wiki APU clkgen](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/APU/clkgen.md), [APU pads](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/APU/pads.md)。M2 はリセット中も動作し続ける観測あり（Jarhmander、検索要約経由）— [forum t=13993](https://forums.nesdev.org/viewtopic.php?t=13993)
- Lava RGB: 「the delay between fall of PPU /CE and rise of ALE is variable depending on a particular power-up allignment」— [forum t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)
- PPU-LITE 作者 andkorzh: 2 チップ同期には「Reset pin … will need to be used to synchronize the chips with each other」— [forum t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)
- Hi-Def NES は CPU/PPU を FPGA 生成クロックに切替え、HDMI 抜き差し時に NES をリセット（「the CPU would crash anyways during clock switchover」）、v2.0 で「do not reset PPU on reset to prevent the rolling」— [t12019 アーカイブ](https://archive.nes.science/nesdev-forums/f9/t12019.xhtml)
- NESRGB は TIMING ブロックに PPU の CLK・/RES・INT を入力（ブロック図）— [operation_block_diagram.png](https://etim.net.au/nesrgb/operation_block_diagram.png)

### Inferences（推論）
- 「電源投入後に 1 画素ずれる」原因: 外部回路は PPU の PCLK 位相（マスタークロック 4 相のどれか）を知らずに EXT と比較器出力をサンプルするため、PCLK 位相によっては EXT と第5ビットのサンプルが 1 画素ずれる（EXT は /PCLK ラッチで即出るが、VOUT は内部遅延を経て、さらに比較器遅延が加わる）。Famicom は PPU /RST 固定 High のため分周器初期値（不定 x）がそのまま残る。→ NESRGB 型の改造品は PPU の位相を制御できないので、FIFO/遅延調整で吸収している（Lava の 2023-07 更新）。
- 新基板での対策（推奨構成）:
  1. 21.47727 MHz 発振器 1 個を CPU CLK・PPU CLK・RP2350（XIN 外部クロック or PIO 入力）に分配（TinyNES は SiT2001B→PL133-37 クロックバッファ→各 30Ω 直列で CPU/PPU へ配る構成 — [TinyNES 回路図](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf)）。
  2. PPU /RST（pin22）を +5V 固定にせず、マスタークロックで動く D-FF（例 74HC74 か MCU の PIO）で **CLK 立上りに同期して解除**。これで PCLK 位相とマスタークロックの関係が毎回同じになる（Breaking NES の波形に基づく）。
  3. CPU/PPU アラインメントも固定したい場合は、2A03 の M2（CLK/12）の立上りを基準に「M2 エッジから n マスタークロック後」に PPU /RST を解除する（CPU 分周器はリセットされないので M2 で位相を観測する必要がある）。Famicom ソフト互換上は 4 通りいずれでも実機で起こり得る状態なので、どれか 1 つに固定して問題は生じないと考える。
  4. 解除は CPU /RST 解除より前（Famicom 同様、PPU 側を先に起動）にしておけば、リセット直後の PPU 書込み無視期間の挙動も Famicom と同等。
  - ただし非同期 /RES 入力の内部同期段の有無（解除タイミングが CLK エッジに近いとメタステーブルで 1 CLK 揺れる可能性）は **未確認**。実機で ALE か /RD の位相を測り、毎回同じになることを確認すべき。

### Gaps
- /RES 解除から最初の PCLK エッジまでのマスタークロック数、/RES の同期化段の有無: 波形図はシミュレーション由来で実測値なし **未確認**。
- 2A03 の分周器が /RST で本当にリセットされないことの第二出典（Fiskbit ユーザページ以外）: 未取得 **未確認**（blargg「power/reset でランダム」は NES の同時リセット環境での観測で、CPU 分周器の非リセットとは矛盾しない）。

---

## 4. RGB 出力 PPU（2C03/2C04/2C05）の出力回路・バッファ、Famicom Titler、両対応ソケット

### Takeaway
Famicom Titler の PPU は **RC2C05-99** で確定（NESdev Wiki 3 ページと Breaking NES が一致。Vs. System ページの「2C03」記載は誤り/旧情報）。RC2C05-99 は「2C02 timing（ドットスキップあり）」「PPUCTRL/PPUMASK の入替えなし」。RGB PPU の R/G/B は内部の重み付き電流加算 DAC（各 ch 8 レベル）、pin21 は内部分圧付きの /SYNC。ピン電圧・出力インピーダンスの数値資料と、VS. System / PlayChoice-10 / Sharp C1 の出力段回路図は取得できず **未確認**。オープンハードの TinyNES は RGB PPU の R/G/B を **THS7314（6dB ビデオアンプ）に直結し 75Ω 直列**で出しており、2C02/RGB PPU 両対応ソケットの具体例（EXT 10k プルダウン、2C05 用 A0 入替ゲート＋スイッチ）を示している。

### Cited Findings
- Famicom Titler: 「RC2C05-99 … An RGB PPU with RP2C02E behavior」「Uses 2C02 timing (a dot is skipped every other frame), unlike other RGB PPUs.」「PPUCTRL and PPUMASK aren't swapped.」「Used in the Famicom Titler.」— [NESdev Wiki: PPU variants](https://www.nesdev.org/wiki/PPU_variants)。「The Sharp Famicom Titler (AN-510) contains a RC2C05-99 PPU, whose RGB output is fed into a X0858CE "encoder" chip.」— [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes), [User:Forple](https://www.nesdev.org/wiki/User:Forple)。X0858CE は 2C05-99 の RGB をコンポジット/S に変換、色差に 0.5 ゲイン、3.579545 MHz 水晶 — [X0858CE](https://www.nesdev.org/wiki/X0858CE)。Breaking NES の改版表も「2C05-99 | Famicom Titler」— [PPU Readme](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/Readme.md)
- 他の RGB PPU の差（PPU variants）: RP2C03B「Color emphasis bits set the corresponding channel to full brightness」; RP2C04-0001「Equivalent to 2C02D, but keeps 2C03 timing (no skipped dot)」; RC2C05-01「PPUCTRL and PPUMASK swap locations. Five LSBs of PPUSTATUS return a constant.」— [PPU variants](https://www.nesdev.org/wiki/PPU_variants)
- RGB PPU の内部（RP2C04-0003 のダイ写真から復元）: 「EXT0-3 and VOUT pins are replaced by RED, GREEN, BLUE, /SYNC pins」「DAC with weighted current summation」、端子表 14=RED, 15=GREEN, 16=BLUE, 17=AGND, 21=/SYNC。偶奇（ドットスキップ）回路は存在するが切断、BURST 信号は生成されるが未使用、/SLAVE 未使用、EXT_IN は 0 固定 — [Breaking NES Wiki: RGB PPU](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md)。DAC は各色 B0〜B7 等 8 本のトランジスタ列（[RGB_DACs.png](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/rgb/RGB_DACs.png)）、/SYNC パッドは 3 本並列のプルダウントランジスタ＋「VOLTAGE DIVIDER」（[RGB_SYNC.png](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/rgb/RGB_SYNC.png)）
- NESdev Wiki PPU pinout は RGB PPU の R/G/B/CSYNC の電圧レベルを記載しない — [PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- 2C02 側の公式コンポジット増幅（参考）: +5V から 300Ω、PNP 2SA937（代替 2N3906、ピン配置 E-C-B と E-B-C が異なる）、220µF、110Ω、560pF、PPU pin20–pin22（Famicom）間にタンタル 4.7〜47µF（10µF 推奨）— [PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)。TinyNES も同定数（R19 300Ω、Q1 3906、C31 220µF、R21 110Ω、C35 560pF）— [TinyNES Main Board Schematic](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf)
- **TinyNES RGB Board（CC BY-SA 4.0, TD-TRGB-C rev C）**: ヘッダ RGBS（VCC, GND, R, G, B, EX3, S）、R/G/B → U1 THS7314 IN1-3 直結（入力にバイアス/終端抵抗なし）、OUT → 75Ω（R1-R3）→ RCA。EX3 は GND に接続。電源デカップリング 10µ+0.1µ — [TinyNES_RGB_Board_Schematic.pdf](https://raw.githubusercontent.com/loglow/TinyNES/main/RGB%20Board/TinyNES_RGB_Board_Schematic.pdf), [BOM](https://raw.githubusercontent.com/loglow/TinyNES/main/RGB%20Board/TinyNES_RGB_Board_BOM.csv)（U1 = TI THS7314DR）
- **TinyNES Main Board（TD-TNES-27-MB）の両対応構成**: PPU EXT0-3（pin14-17）は 10kΩ×4（R25-R28）で GND へ、同時に RGB ヘッダへ配線。PPU A0（pin12）は S5 スイッチで「CPU A0 直結」と「NOR（A1,A2）→XOR（A0）」出力を切替（2C05 用）。PPU pin21 は 2N3906 コンポジットアンプへ（RGB ヘッダの S にも接続、推論: 図から判読）— [TinyNES Main Board Schematic](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf)。ジャンパ基板（RGB キット未装着時）は「connects PPU pins 14, 15, and 16 to ground」— [Crowd Supply update](https://www.crowdsupply.com/tall-dog-electronics/tinynes/updates/orders-shipped-and-jumper-board-fix)（検索要約経由）。TinyNES RGB キット対応: RP2C03/RC2C03/RC2C05 全種、RP2C04 は「scrambled color palettes」— [tall-dog shop](https://reach.dog/shop/tall-dog-electronics/products/tinynes-rgb-video-kit)（検索要約経由）
- 2C05 の A0 入替式: `A0' = A0 xor (A1 nor A2)` — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)（第1パスで確認済み、TinyNES 実装と一致）
- 2005 年の NES 改造スレッド: RGB PPU の pin14-17 は NES 基板では GND に繋がるので「The RGB Pins should not connect from the socket to the pcb」、「RP2C03/4/5 PPUs output composite sync」「this signal is unamplified」、アンプに NTE123AP/NTE159（2N3904/2N3906 相当とされる）を使った例 — [nfggames NES RGB mod](https://nfggames.com/forum2/index.php?topic=1592.0)（電圧・抵抗値の記載なし）
- VS. System / PlayChoice-10 / Sharp C1 の回路図: 検索で elektrotanya の VS 回路図 PDF（ダウンロードゲート付き）を見つけたが本文未取得 — [elektrotanya](https://elektrotanya.com/nintendo_vs_sch.pdf/download.html)。consolemods の PlayChoice-10 PPU Mod ページは Cloudflare/403 で取得不可。

### Inferences（推論）
- TinyNES が THS7314（固定 6dB、出力は 75Ω 直列でバックターミネート）に直結していることから、RGB PPU のピン出力は概ね「0 V 付近から 0.7〜1 V 程度」の DC 結合レベルで、THS7314 の入力範囲内と推測される（**未確認**、実測が必要）。
- 両対応ソケット（2C02 EXT 方式 ⇔ RGB PPU）に必要なもの:
  1. pin14-16: 2C02 時は EXT0-2（MCU 入力へ。プルダウン 10k で入力モード時 backdrop=0 を保証）、RGB PPU 時は R/G/B アナログ → 映像バッファへ。**同じ配線に両方を並列接続すると、RGB PPU のアナログ出力が MCU 入力（デジタル）を中間電位で駆動し、EXT 方式の時は 2C02 のデジタル出力がそのまま映像アンプへ入る**。ジャンパ/アナログスイッチ（74HC4066 等）か 0Ω 抵抗の実装選択で分離する。
  2. pin17: RGB PPU では AGND（内部で GND）。2C02 出力モードでは EXT3 出力なので **GND 直結は不可**（TinyNES は 10k プルダウンで両立。RGB ボード側で EX3 を GND に落としているが、TinyNES の 2C02 は出力モードにしない前提）。本基板では 2C02 を出力モードにするため、pin17 は「10k プルダウン＋MCU 入力」、RGB PPU 時は 0Ω ジャンパで GND に落とす構成にする。
  3. pin21: 2C02=コンポジット VOUT（比較器入力＋必要ならコンポジット出力）、RGB PPU=/SYNC（内部分圧付き、非増幅）→ 74HC14 等で整形して JAMMA CSYNC へ。
  4. pin12（A0）: 2C05 用の A0 入替ゲート（74HC02+74HC86、または MCU 側でアドレスを入れ替えて PPU に渡す）とジャンパ。RC2C05-99 は入替不要。
  5. $2000 bit6 強制とパレット改変（EXT 方式用）は RGB PPU 時に無効化（MCU ファームで切替）。
  6. 2C04 は LUT 変換なしでは色が狂う（第1パス既述）。

### Gaps
- RGB PPU の R/G/B ピン電圧（黒/白レベル）、出力インピーダンス、/SYNC の電圧と極性の実測値: **未確認**（3 系統以上の検索・回路図探索で発見できず）。
- VS. System、PlayChoice-10、Sharp C1、Famicom Titler の RGB 出力段のトランジスタ型番・抵抗値: **未確認**。

---

## 5. 2C02 用のその他デジタル映像方式（LumaCode 等）、マイコンによる取込み

### Takeaway
c0pperdragon の **PPUdigitizer (for NES)** が存在する（第1パスの「NES 用 LumaCode 実装は見つからない」は誤り）。PPU のパッド裏に半田付けし、「PPU と他の部分の間のデータ転送を受動的に聞く」FPGA 基板で、元のコンポジットは無改変のまま LumaCode 信号を出す。内部方式（どの信号を盗聴するか）・回路・HDL は非公開で **未確認**。RP2040/RP2350 で 2C02 の画素データ（EXT 等）を取り込む公開プロジェクトは見つからなかった。

### Cited Findings
- PPUdigitizer: 「will passively listen to the data transfer between the PPU and the rest of the system」、LUM パッドが LumaCode 出力、「The mod kit contains the FPGA board」、「supports the PAL variants of the PPU, as well as most NTSC variants」、「NESRGB sync fix must be disabled on NTSC machines」の注記 — [LumaCode Wiki: PPUdigitizer (for NES)](https://github.com/c0pperdragon/LumaCode/wiki/PPUdigitizer-(for-NES))。LumaCode リポジトリは信号規格と参照実装（signalgenerator 等）のみで NES 用ソースなし、LICENSE なし — [github.com/c0pperdragon/LumaCode](https://github.com/c0pperdragon/LumaCode)。c0pperdragon の公開リポジトリ一覧にも NES/PPU 関連なし — [c0pperdragon repositories](https://github.com/c0pperdragon?tab=repositories)
- 「easily solders onto the back of a Ricoh 2C02 PPU」「converts the picture into a signal its creator has dubbed Lumacode」— [zdziarski.com blog 2026-02](https://www.zdziarski.com/blog/?m=202602)
- Issue #20（フィードバック）: 作者による内部方式の説明なし。「There are probably some differences between revisions, especially for NTSC machines.」— [LumaCode issue #20](https://github.com/c0pperdragon/LumaCode/issues/20)
- 類似方式: RGB Blaster（カートリッジ端子の PPU バス盗聴＋FPGA で PPU 再実装、第1パス）。
- マイコン関連で見つかった唯一の近縁例: Game Boy→RP2C02 アダプタ構想（RP2350/Pico 2 から 2C02 の EXT0-3 を**入力モード**で駆動する計画）。現状はソフトウェア PoC のみで実機検証は「future work」、ライセンス MIT / CERN-OHL-W-2.0 / CC BY-SA 4.0 — [SamDelorean/gameboy-rp2c02-crt-adapter README](https://raw.githubusercontent.com/SamDelorean/gameboy-rp2c02-crt-adapter/main/README.md)

### Inferences（推論）
- 本プロジェクトは PPU を基板上に持つので、LumaCode のような「外部へ送る符号化」は不要。PPUdigitizer は EXT ではなく PPU バス盗聴＋FPGA 再現（RGB Blaster 型）と推測されるが根拠は「passively listen」の一文のみ。
- RP2350 で EXT 方式を実装する前例はなく、本基板が初の例になる可能性が高い。

### Gaps
- PPUdigitizer の内部方式・FPGA 型番: 非公開で **未確認**（Tindie 製品ページは 403）。

---

## 6. コンポジット端子からのスプライト/BG 判定（汎用部品で）

### Takeaway
1 画素 186 ns に対し、比較器は「遅延そのもの」より「遅延のばらつき（入力オーバードライブ依存・立上り/立下り差）」が画素幅より十分小さいことが必要。LM393/LM339 は 5mV オーバードライブで 1.3 µs、TTL 振幅入力でも 300 ns と画素より遅く不適。LM311 は 115/165 ns（5mV OD）で境界的。LMV7219（7 ns）、TLV3501/3502（4.5 ns @20mV OD）、MAX999（4.5 ns）が既存品の実績領域（Lava = LMV7219+TLV3502、NESRGB v5 = TLV3502 相当＋MCP6561 相当）。2C02 の黒→白の段差は終端時で約 0.79 V（312→1100 mV）、kevtris 実測（エミッタ）で 1.30→2.74 V と大きく、オーバードライブは十分取れる。

### Cited Findings
- 2C02 の出力レベル（75Ω 終端時, mV）: sync 48、burst low 148、$0D 228、$1D(黒/blank) 312、burst high 524、$2D 552、$00 616、$10 840、$3D 880、$20 1100。強調時: $0D 192, $1D 256, $2D 448, $00 500, $10 676, $3D 712, $20 896。$xE/$xF は $1D と同電圧、$x1〜$xC は $xD と $x0 の間の方形波、$20=$30 — [NESdev Wiki: NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- kevtris 実測（NES の PPU VOUT に接続された増幅トランジスタのエミッタ、Agilent 54622D、絶対電圧 V）: sync 0.781、black 1.300、C.B. lo 1.000 / hi 1.712、L0 lo 1.131 / hi 1.875、L1 lo 1.300 / hi 2.287、L2 lo 1.743 / hi 2.743、L3 lo 2.331 / hi 2.743（強調全ビット時 L3 hi 2.243 など）。RCA 75Ω 負荷で「981mv peak to peak (synch to white)」— [NESdev forum t=2113](https://forums.nesdev.org/viewtopic.php?t=2113)
- 比較器データシート値:

  | 品番 | 応答/伝搬遅延（typ） | 条件 | 出典 |
  |---|---|---|---|
  | LM393 / LM2903 | 1.3 µs（B 版 1 µs）| 100 mV ステップ・5 mV OD、5.1k プルアップ | [TI LM393](https://www.ti.com/lit/ds/symlink/lm393.pdf) |
  | LM393 | 300 ns | 「TTL input with Vref = 1.4V」 | 同上 |
  | LM339 | 1.3 µs / 300 ns（TTL 入力）| 同上 | [TI LM339](https://www.ti.com/lit/ds/symlink/lm339.pdf) |
  | LM311 | 115 ns（L→H）/ 165 ns（H→L）| 100 mV ステップ・5 mV OD | [TI LM311](https://www.ti.com/lit/ds/symlink/lm311.pdf) |
  | LM119/LM319 | 80 ns | ±15 V、100 mV ステップ・5 mV OD | [TI LM119/LM319](https://www.ti.com/lit/ds/symlink/lm119.pdf) |
  | LMV7219 | 7 ns（5V, OD 50 mV）/ 8 ns（15 mV）/ 9 ns（5 mV）、skew 0.4 ns | 2.7〜5 V、プッシュプル出力 | [TI LMV7219](https://www.ti.com/lit/ds/symlink/lmv7219.pdf) |
  | TLV3501 / TLV3502 | 4.5 ns（max 6.4）@ OD 20 mV、7.5 ns @ OD 5 mV、skew 0.5 ns | 2.7〜5.5 V | [TI TLV3501](https://www.ti.com/lit/ds/symlink/tlv3501.pdf), [TLV3502](https://www.ti.com/lit/ds/symlink/tlv3502.pdf) |
  | MAX999 | 4.5 ns（5 mV OD, VCC=3V, 5pF）| +3/+5 V 単電源 | [elecfans 転載 MAX999](https://pdf.elecfans.com/MAXIM/MAX999.html)（二次ミラー、検索要約経由・原 PDF は analog.com が 503 で未取得）|
  | MCP6561 | 56 ns（H→L）/ 49 ns（L→H）@ VDD 1.8V | — | 検索要約（Microchip サイト 403 で未取得、**要再確認**）|

- 既存品の比較器: Lava RGB = LMV7219M5X + TLV3502AIDR（BOM）— [lava-rgb-kit](https://github.com/v5100v5100/lava-rgb-kit)。NESRGB v5 = GSV331（代替 MCP6561）+ MX3502S（代替 TLV3502）+ GS8051 バッファ — [NESRGB5 test mode](https://etim.net.au/nesrgb5/testmode/)
- 閾値の機種依存: Lava で WDL6528 は閾値 1.92 V を下げる必要（R9 7.15k→10k）、「ビデオ出力にアンプを繋ぐと動作しなくなる」— [forum t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)
- ディスクリート案の文献: kyuusaku 2012-12-03「bias the CMOS inputs (or better yet differential inputs) to act as comparators」、lidnariq「an array of 15 trimpots and 15 comparators is awfully hard to screw up」— [forum t=9561 p.2](https://forums.nesdev.org/viewtopic.php?t=9561&start=15)。差動トランジスタ対の具体回路の文献は見つからず。
- Fiskbit: アナログ映像の BG/スプライト遷移が十分速く変化しないとスプライト縁にちらつき/色にじみ — [forum t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)

### Inferences（推論）
- 画素 186 ns に対し、PPU 出力自体の遷移（560 pF 等の負荷・PPU 内部 DAC）にも数十 ns かかるので、比較器の判定点は「画素中央」でサンプルする設計が必要。RP2350 側は比較器出力を EXT と同じ PIO で、画素中央の位相（マスタークロック単位で調整可能）でサンプルすれば、比較器の絶対遅延（数 ns〜100 ns）はファームの位相設定で吸収できる。
- 部品選定: 5 V 単電源・高速・プッシュプルで実績のある TLV3502（デュアル）×1 ＋ 遅くてよい同期用に 1 回路、が Lava/NESRGB v5 と同じ構成。LM311 は伝搬遅延のばらつき（OD 依存）が 50 ns 以上ありマージン不足、LM393/LM339 は不可。
- ディスクリート代替: 74HC14（Basic Parts）の入力に、PPU VOUT を NPN エミッタフォロワで受けて抵抗分圧＋DC バイアスで「黒≒0.5V／白≒4V」程度に振らせれば、シュミット閾値（約 1.6〜3.0 V @5V）で 2 値化できる可能性がある（74HC の伝搬遅延は 10 ns 台）。ただし閾値の個体差・温度変化が大きく、PPU 品種差（WDL6528 の例）にも弱い。推論で未検証。
- 閾値は MCU の PWM＋RC（または抵抗分圧＋半固定）で可変にしておくと PPU の個体差に対応できる（Lava の R9 問題の教訓）。

### Gaps
- MAX999・MCP6561 の一次データシート本文は取得できず（ミラー/検索要約）。差動対ディスクリート比較器の文献例: 見つからず。
- JLCPCB Basic Parts に TLV3502/LMV7219 があるかは本調査範囲外（**未確認**）。

---

## 7. 64 色パレットデータ、ライセンス、強調・グレースケールの適用

### Takeaway
RGB PPU（2C03）の 3bit/ch 表は NESdev Wiki に掲載（第1パスで転記済み）。FirebrandX パレット（Smooth, PVM Style D93, Composite Direct, NES Classic）はライセンス・利用条件の記載なし。パレット生成器 pally / palgen-persune は **MIT No Attribution**（MIT-0）で、自前生成なら権利上の懸念が小さい。強調は 2C02 では非強調成分を約 0.816 倍に減衰（$xE/$xF には効かない）、2C03/2C05 では該当チャネルをフル輝度、グレースケールは 6bit 値を $30 で AND。

### Cited Findings
- Wiki 掲載パレットファイル: 2C02G_U_wiki.pal, 2C02G_J_wiki.pal, 2C07_wiki.pal, 2C03_wiki.pal、生成器 pally、Bisqwit、Drag、RGB PPU Palette Converter（WhoaMan）。ライセンス記述なし — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)。NESdev Wiki 自体のコンテンツライセンス表示はフッターになし — [Nesdev Wiki](https://www.nesdev.org/wiki/Nesdev_Wiki)
- FirebrandX: 「Smooth (FBX)」「PVM Style D93 (FBX)」「Composite Direct (FBX)」（「pure, unmodified direct-capture of the composite output of the front-loader NTSC NES」）「NES Classic (FBX)」。ライセンス・利用条件の記述なし — [firebrandx.com/nespalette.html](https://www.firebrandx.com/nespalette.html)
- pally / palgen-persune: LICENSE「MIT No Attribution, Copyright 2024 Persune」— [pally LICENSE](https://raw.githubusercontent.com/Gumball2415/pally/main/LICENSE), [palgen-persune LICENSE](https://raw.githubusercontent.com/Gumball2415/palgen-persune/main/LICENSE)
- 既存品の内蔵パレット: Lava RGB ファーム = CXA, PC10, FCEUX, NTSC, PAL, YUV の組合せ（.jed 名）— [lava-rgb-kit](https://github.com/v5100v5100/lava-rgb-kit)。LAVA_RGB-TO-PPU_LITE = Composite Direct, Nintendulator NTSC, FBX Magnum, Sony CXA, PC-10, Wavebeam, PAL, Kitrinx — [README](https://raw.githubusercontent.com/andkorzh/LAVA_RGB-TO-PPU_LITE/main/README.md)。NESRGB 初期 = Natural（Nestopia）/ Improved（FCEUX）/ Garish（PlayChoice）— [etim.net.au/nesrgb](https://etim.net.au/nesrgb/)
- 強調: 2C02 は減衰係数（平均）約 0.816、$xE/$xF 列には効かない — [NTSC video](https://www.nesdev.org/wiki/NTSC_video)。RGB PPU では「it sets the corresponding channel to full brightness」— [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes), [PPU variants](https://www.nesdev.org/wiki/PPU_variants), Breaking NES「Emphasis applies the corresponding channel output to all one's」— [rgb.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md)
- グレースケール: RGB PPU も 2C02 と同じ（2C04 は列寄せのみ）— [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)。Breaking NES: $2001 bit0（B/W）は CB の色相 4bit 出力を遮断（輝度 2bit は常に通す）— [cram.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/cram.md)。「ANDing the 6-bit palette color value with $30」（Fiskbit）— [forum t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)

### Inferences（推論）
- 本基板は「6bit 色番号＋強調 3bit = 512 エントリ」の LUT を RP2350 のフラッシュ/RAM に置く。2C02 準拠の見た目なら pally（MIT-0）で 2C02G の 512 色（強調込み）を生成して埋め込むのが権利的に最も安全。2C03 表は実チップの DAC 値（事実データ）なので併載可能と考えるが、法的評価は本調査範囲外。
- 適用順序: EXT 由来インデックス → シャドウパレットで 6bit 色 → グレースケール（AND $30）→ 強調（2C02 準拠なら LUT 512 エントリで処理）→ DAC。

### Gaps
- FirebrandX・Nestopia・FCEUX 等パレットの再配布条件: FBX は無記載、エミュ同梱パレットはエミュのライセンス（GPL 等）に従う可能性 — 個別確認していない **未確認**。

---

## 8. RGB モニタ用 CSYNC の再生成（2C02 の正確なタイミング）

### Takeaway
2C02 の 1 ラインは 341 ドット（63.51 µs、15.746 kHz）、H sync はドット 277 から 25 ドット（4.66 µs）、1 フレーム 262 ライン、V sync はライン 245〜247 の 3 ライン。レンダリング有効の奇数フレームはプリレンダーライン（261）で 1 ドット短い（89341 / 89342 PPU クロック）。NESRGB・Lava RGB は PPU のコンポジットから比較器で同期を抽出、Hi-Def NES は PLL で HDMI と同期。本基板は PPU の VOUT から sync tip を比較器で分離するか、/RST を制御して MCU のドットカウンタで生成する（ドットスキップ条件の模擬が必要）。

### Cited Findings
- 水平（1 ライン 341 ドット、開始ドット・長さ）: H sync 277 / 25、back porch 302 / 4、colorburst 306 / 15、back porch 321 / 5、pulse（backdrop のグレースケール）326 / 1、左ボーダー 327 / 15、active 1 / 256（ドット 0 は黒の 1 画素）、右ボーダー 257 / 11、front porch 268 / 9。「the video output of the PPU is delayed by 1 pixel clock」— [NESdev Wiki: NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- 垂直（262 ライン）: 表示 0〜239、post-render 240〜241（VBlank フラグはライン 241 でセット）、post-render blanking 242〜244、vertical sync 245〜247（3 ライン、vertical blanking pulse は dot 277 から 318 ドット、serration は dot 254 から 32 ドット）、pre-render 248〜261（VBlank はライン 261 でクリア）— 同上
- 奇数フレーム: レンダリング有効時「skipping the first idle tick on the first visible scanline」（(339,261) から (0,0) へ）、フレームは 89341 / 89342 クロック交互。レンダリング無効時は 341×262=89342。プリレンダーライン末尾でレンダリングを無効にすると 89342 に固定 — [PPU frame timing](https://www.nesdev.org/wiki/PPU_frame_timing), [NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- RGB PPU（2C03/2C04）は偶奇ドットスキップなし（回路切断）、RC2C05-99 はスキップあり — [rgb.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md), [PPU variants](https://www.nesdev.org/wiki/PPU_variants)
- NESRGB: 同期は比較器で抽出、CS# 出力（TTL / 75Ω 選択 J8）— [block diagram](https://etim.net.au/nesrgb/operation_block_diagram.png), [NESRGB-Pinout.pdf](https://etim.net.au/nesrgb/NESRGB-Pinout.pdf)。de-jitter は「precisely controlling the clock to the PPU to make the video timing standard compliant」（OSSC 作者 marqs の手法）— [De-jitter For NESRGB](https://etim.net.au/nesrgb/background_fault/de-jitter.html)、のちに NTSC で sync 不安定のため撤回（第1パス）。marqs の snes_dejitter は ATF1502AS CPLD の別基板 — [snes_dejitter README](https://raw.githubusercontent.com/marqs85/snes_dejitter/master/README.md)
- Lava RGB: 比較器で vblank・走査線開始を検出、ネット `VOUT_CS`, `VOUT_BLANK`, `VBL` — [forum t=25963](https://forums.nesdev.org/viewtopic.php?t=25963), [lava-rgb-kit](https://github.com/v5100v5100/lava-rgb-kit)
- Hi-Def NES: 「the NES and HDMI are locked together in synchrony so I only need to buffer a couple scanlines」、後に「I no longer stop the NES clock every frame to resynch … and use a PLL method now」— [t12019 アーカイブ](https://archive.nes.science/nesdev-forums/f9/t12019.xhtml)

### Inferences（推論）
- 数値: 21.477272 MHz/4 = 5.369318 MHz、1 ドット 186.24 ns、1 ライン 341 ドット = 63.51 µs（15.746 kHz）、H sync 25 ドット = 4.66 µs、V sync 3 ライン ≈ 190.5 µs、フレーム 60.10 Hz。15 kHz アーケードモニタの許容範囲内（一般論、モニタ仕様は別担当）。
- CSYNC 生成の 2 案:
  - (A) VOUT 比較器（sync tip 48 mV と burst low 148 mV の間、終端なしなら kevtris 測定で 0.78 V と 1.00 V の間 — ただし PPU ピン直では値が異なる）→ そのまま CSYNC。ドットスキップ・リセットに自動追従、PPU の serration（等化パルス相当）もそのまま出る。比較器は遅くてよい（LM393 でも可、1 µs 程度の遅れは全ライン一定）。
  - (B) RP2350 の PIO カウンタで生成: PPU /RST を MCU が解除するなら H/V 位相は既知。奇数フレームのスキップは「レンダリング有効（$2001 bit3|bit4）かつ奇数フレーム」でプリレンダーラインを 1 ドット短縮する必要があり、MCU は $2001 書込みを盗聴しているので模擬可能。ただし判定タイミング（ライン 261 dot 339 付近の $2001 状態）を誤ると 1 ドットずれが蓄積せず各フレームで揺れるだけなので、実害は小さい。
  - 推奨は (A) を主、(B) を予備（PPU を RGB PPU に差し替えたときは pin21 /SYNC をそのまま使う）。
- RGB を ブランキング期間 0 にするマスクは、(A) の比較器か MCU のドットカウンタ（active = dot 1〜256 + ボーダー 257〜267, 327〜340）で生成。ボーダー（backdrop 色）を出すかどうかは仕様判断。

### Gaps
- 2C02 の V sync 期間中の serration の正確な形（各パルス幅）を JAMMA モニタが要求するか: 範囲外 **未確認**。

---

## 既存ノートへの訂正（rgb_from_rp2c02.md に対して）

| # | 第1パスの記述 | 訂正・確定内容 | 出典 |
|---|---|---|---|
| 1 | Famicom Titler の PPU は「2C05-99（PPU palettes）と 2C03（Vs. System）で記述不一致」 | **RC2C05-99 で確定**。PPU variants・PPU palettes・User:Forple・X0858CE・Breaking NES が一致。さらに RC2C05-99 は 2C02 タイミング（ドットスキップあり）で PPUCTRL/PPUMASK の入替えなし（他の 2C05 と異なる）→ 2C05 用 A0 入替ゲートは不要 | [PPU variants](https://www.nesdev.org/wiki/PPU_variants), [X0858CE](https://www.nesdev.org/wiki/X0858CE) |
| 2 | 「LumaCode の NES 用実装は見つからなかった」 | **PPUdigitizer (for NES) が存在**（FPGA、PPU 裏に半田付け、受動盗聴、LumaCode 出力）。内部方式は非公開 | [LumaCode wiki](https://github.com/c0pperdragon/LumaCode/wiki/PPUdigitizer-(for-NES)) |
| 3 | NESRGB/Lava のコンパレータ型番 **未確認** | Lava RGB = LMV7219M5X ×1 + TLV3502AIDR ×1（計 3 回路）、FPGA = LCMXO2-1200HC-4TG100I、変換 SN74LVC4245A×2・SN74LVC541A×2。NESRGB v5 = GSV331（alt MCP6561）+ MX3502S（alt TLV3502）+ GS8051 | [lava-rgb-kit BOM](https://github.com/v5100v5100/lava-rgb-kit), [NESRGB5 testmode](https://etim.net.au/nesrgb5/testmode/) |
| 4 | Lava RGB のソース所在・ライセンス **未確認** | Altium 回路図・基板・BOM・ファーム(.jed のみ)を GitHub 公開、HDL なし、ライセンス表示なし | [lava-rgb-kit](https://github.com/v5100v5100/lava-rgb-kit) |
| 5 | 「RP2040/RP2350 の 5V 耐性は未確認」 | RP2350 は公式に 5V トレラント（IOVDD 通電中に限る）。RP2040 は対象外。ADC 兼用ピン除外は読者コメントのみで未確認 | [Raspberry Pi news](https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/) |
| 6 | 「LM393/LM339 は µs オーダー（未確認）」 | 確認: 1.3 µs（5 mV OD）、TTL 振幅入力でも 300 ns。LM311 115/165 ns | [TI LM393](https://www.ti.com/lit/ds/symlink/lm393.pdf), [TI LM311](https://www.ti.com/lit/ds/symlink/lm311.pdf) |
| 7 | 「1 画素ずれの物理的原因: 未確認」 | /RST が PPU の CLK/4 分周器・カウンタをリセットし、CPU 分周器はリセットされないこと、Famicom は PPU /RST を +5V 固定で分周器初期値が不定であることを確認（原因の特定自体は推論のまま） | [PPU pinout](https://www.nesdev.org/wiki/PPU_pinout), [User:Fiskbit](https://www.nesdev.org/wiki/User:Fiskbit), [pclk.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pclk.md) |
| 8 | 2SA937 増幅回路は「検索スニペットのみ・本文未確認」 | 本文で確認: 300Ω（+5V から）、2SA937（代替 2N3906、ピン配置相違）、220µF、110Ω、560pF、タンタル 4.7〜47µF（10µF 推奨）。TinyNES も同定数 | [PPU pinout](https://www.nesdev.org/wiki/PPU_pinout), [TinyNES 回路図](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf) |
| 9 | RGB PPU の pin21 は「CSYNC」 | 内部的には **/SYNC（アクティブ Low、オープンドレイン的な並列プルダウン＋内部分圧）**、非増幅。2C04 では pin17 は AGND | [rgb.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md), [nfggames](https://nfggames.com/forum2/index.php?topic=1592.0) |
| 10 | Hi-Def NES は「PPU に嘘をつく（改変パレット）言及あり」 | kevtris 本人: NESRGB と HDN は「slightly different set of palette entries」、HDN には NESRGB と同じ方法で「lie」させるジャンパがある。ユーザ報告で HDN 装着機の RF は「sprites as white on a black background」 | [t12019](https://archive.nes.science/nesdev-forums/f9/t12019.xhtml) |
| 11 | Q2 推論「改変パレット例: BG 側 $0F 系、スプライト側 $30 系」 | 公開資料で確認できるのは「BG 全黒・スプライト全白」まで。ただし BG=黒($0F/$1D) はブランキングと同電位で、ブランキング用比較器と両立しないため、実際の BG 値は別（$2D/$00 等）の可能性がある → 色番号は引き続き **未確認** | [t=9561 p.4](https://forums.nesdev.org/viewtopic.php?t=9561&start=45), [NTSC video](https://www.nesdev.org/wiki/NTSC_video) |
| 12 | Q1 推論「pin17 は 0Ω ジャンパ or 直列抵抗必須」 | 方向性は正しい。実例として TinyNES は EXT0-3 を 10k プルダウンで受け、RGB ボード側で EX3 を GND に落とす。本基板（2C02 出力モード）では pin17 を直接 GND にしない設計が必要 | [TinyNES 回路図](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf) |

---

## 付記: 試行したが取得できなかった経路（再調査用）

- nesdev.org を curl（`action=raw`）で取得 → Cloudflare チャレンジで不可（WebFetch は可）。
- consolemods.org（PlayChoice-10 PPU Mod）→ Cloudflare/403、web.archive.org → 取得不可。
- Microchip（MCP6561）・analog.com（MAX999）データシート → 403 / 503。
- Tindie（PPUdigitizer 製品ページ）→ 403。
- talldog.dozuki.com（TinyNES RGB 取付ガイド）→ サイト停止。
- Lava RGB の Altium SchDoc の配線（比較器と抵抗の接続）→ バイナリ解析未実施。iBOM（out/Lava_RGB.html）にはネット情報なし。
- Visual 2C02 による EXT/VOUT 遅延の実測シミュレーション → 未実施。
