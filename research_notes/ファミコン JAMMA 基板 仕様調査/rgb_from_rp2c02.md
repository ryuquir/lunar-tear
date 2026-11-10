# RP2C02 から 15kHz アナログ RGB を得る方法（JAMMA 基板向け調査）

調査日: 2026-11-10。表記: 「Cited Findings」は出典付きの事実、「Inferences」は筆者（調査者）の推論・実現性検討で出典の裏付けはない。未確認事項は **未確認** と明記。
注: nicole.express の記事末尾に AI エージェント向けの指示文が埋め込まれていたが、調査依頼と無関係のため無視した。

---

## Q1. RGB 出力 PPU（RP2C03B, RC2C03B/C, RP2C04-0001〜0004, RC2C05-01〜05）

### Takeaway
RGB PPU は 2C02 と同じ DIP-40 で、pin14/15/16（2C02 の EXT0/1/2）が R/G/B アナログ出力、pin17（EXT3）が GND、pin21（VOUT）が CSYNC になる。2C03 は 2C02 とほぼ互換（強調ビットの意味・グレー $xD 等が異なる）、2C04 はパレットが並べ替え（スクランブル）、2C05 は $2000/$2001 が入れ替わり $2002 下位に ID を返す。入手は中古のみで 1 個 125〜260 USD と高価・品薄。

### Cited Findings
- RGB PPU は EXT3..0 と VOUT を RGB 映像用信号に置き換える。図では R=pin14, G=pin15, B=pin16, pin17=GND, pin21=CSYNC。「EXT3 is internally and externally tied to ground: perhaps it serves as an analog ground for the video DACs」。RGB PPU の pin21 は「only CSYNC, the composite sync signal」 — [NESdev Wiki: PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- 2C03 パレット（R,G,B 各 0〜7 の 3bit/ch、8bit 換算 C=255*DAC/7）64 エントリ表:
  ```
  $0x 333 014 006 326 403 503 510 420 320 120 031 040 022 000 000 000
  $1x 555 036 027 407 507 704 700 630 430 140 040 053 044 000 000 000
  $2x 777 357 447 637 707 737 740 750 660 360 070 276 077 000 000 000
  $3x 777 567 657 757 747 755 764 772 773 572 473 276 467 000 000 000
  ```
  — [NESdev Wiki: PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)
- 2C04-0001〜0004 は「All four 2C04 PPUs contain the same master palette, but in different permutations」。2C03/5 パレットのほぼ上位集合（グレー4色＋他6色を追加） — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)。VS. System 側の説明では「60-color master palette」で、新しい PRG/CHR に差し替えると色が狂うコピープロテクト — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- 2C05 は 2C03 と同じ色だが $2000 と $2001 の意味が入れ替わる（誤ったレジスタの bit7 に 1 を書き NMI が来ずロック）— [Vs. System](https://www.nesdev.org/wiki/Vs._System)。`A0' = A0 xor (A1 nor A2)` の回路で PPUCTRL/PPUMASK を入れ替えれば 2C03 として動く — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)
- 2C05 は $2002 の bit4-0 に ID を返す（2C05-02:$3D, 2C05-03:$1C, 2C05-04:$1B）— [NESdev Wiki: PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- 2C03 と 2C02 の差（tepples）: ①強調ビットはその成分をフル輝度にする（2C02 は他2成分を少し暗くする）②パレットは NTSC に近いがかなり彩度が高い ③グレー $2D/$3D が黒（$1D と同様）④「No shortened pre-render line every other field」（奇数フレームのドットスキップがない）— [NESdev forum t=15541（アーカイブ）](https://nesdev.nes.science/f2/t15541.xhtml)。強調全ビットで真っ白になる点は [PPU registers](https://www.nesdev.org/wiki/PPU_registers) でも確認。
- グレースケールは全 RGB PPU で 2C02 と同じだが、2C04 はインデックス上で第1列に寄せるだけでグレーにならない — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes), [PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- 2C03 (PlayChoice-10) と 2C05-99 は hue $D を暗灰でなく黒で表示 — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)
- 搭載機: 2C03 = VS. Duck Hunt / VS. Tennis / PlayChoice-10 全般 / Sharp C1（ファミコンテレビ）; 2C04 = 多くの VS. System; 2C05 = 後期 VS. のコピープロテクト、2C05-99 = Sharp ファミコンタイトラー（コピープロテクトなし） — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)。Vs. System ページは 2C03 を Famicom Titler にも挙げており、2C05-99 とする PPU palettes と食い違う（**記述不一致**）— [Vs. System](https://www.nesdev.org/wiki/Vs._System)
- NES の RGB 改造互換性（2012-13 年）: Quietust「2C03 は概ね互換」「The 2C04s are not compatible because they have scrambled palettes」「2C05s … registers $2000 and $2001 are reversed」。一方 Drakon は RC2C05-04 を baku の回路で動作させ、RGB アンプの代わりに Sony CXA2075 回路を使用 — [NESdev forum t=9503（アーカイブ）](https://nesdev.nes.science/f9/t9503.xhtml)。lidnariq: 2C04 を使うには「three 3-bit ADCs running at the pixel rate, three 3-bit DACs, and a 512×9b lookup table」が必要 — 同上
- 価格・入手性: 2019 年頃の相場 110〜150 USD（RC2C03B/RC2C03C/RP2C03B どれでも可）— [Arcade-Museum WTB: RP2C03 PPU](https://forums.arcade-museum.com/threads/wtb-rp2c03-ppu.506933/)。テスト済み RP2C03B が 125 USD で落札 — [PicClick](https://picclick.com/PLAYCHOICE-10-PC10-Nintendo-RP2C03B-PPU-Tested-Working-172533176401.html)。tall-dog は RP2C03B/RC2C03B/RC2C03C/RC2C05-03/RC2C05-04 を 260 USD で掲載、2026-11 時点で全品 Sold Out。中古抜き取り品で修理ピンあり得る。TinyNES では 2C05 用にジャンパ S5 を「2C05」へ — [tall-dog](https://shop.tall-dog.com/products/rgb-format-nes-core-ppu-chip)
- 2C02 系の VOUT 増幅はトランジスタ（2SA937）1石 — 検索結果スニペットのみ、[PPU pinout](https://nesdev.org/wiki/PPU_pinout) 由来（本文未確認）

### Inferences
- 2C02/RGB PPU 両対応レイアウトは可能と考える: pin14-16 を「RGB バッファ入力」と「EXT 入力（MCU 側、直列抵抗付き）」の両方へ、pin21 を「CSYNC バッファ」と「VOUT 処理（コンパレータ）」の両方へ配線し、ジャンパ/0Ω で選択。ただし pin17 は RGB PPU では GND、2C02 出力モードでは EXT3 出力なので、GND 直結にすると 2C02 が出力短絡で損傷し得る → pin17 は 0Ω ジャンパ or 直列抵抗必須。2C05 対応には A0 入替ゲート（XOR+NOR）を追加するかジャンパ化が要る。2C04 はパレット LUT 変換が必要で実用外。
- 2C03 ではドットスキップがないため、同じソフトでもフレーム周期が 2C02 と僅かに異なる（同期は PPU 自身の CSYNC を使えば問題なし）。
- RGB PPU を部品として量産前提に使うのは、価格（1個で 2C02 ドナー機数台分）と供給（中古のみ・品切れ）から非現実的。プロジェクトの「ドナー HVC-001 の 2C02 を使う」前提とも矛盾。

### Gaps
- PlayChoice-10 / VS. System の RGB 出力バッファ回路（トランジスタ型番・抵抗値）、RGB PPU の R/G/B 出力電圧レベル・出力インピーダンス、CSYNC 極性: 一次資料（回路図）を取得できず **未確認**。
- RC2C05-01/05 の詳細、2C04 の個別表は Wiki にあるが本ノートには転記せず。

---

## Q2. NESRGB（Tim Worthington）の動作原理と派生品（Hi-Def NES, LavaRGB, RGB Blaster, PPU-LITE, LumaCode）

### Takeaway
NESRGB は PPU を自基板上のソケットに載せ、CPU データバスと PPU の間に PLD を挟む。$2000 書込みに bit6 を立てて EXT0-3 を出力させ、パレット書込みを捕捉して内部にシャドウし、PPU には「BG=暗色・スプライト=明色」の改変パレットを書く。PPU の VOUT をコンパレータで見て第5ビット（スプライト/BG）、ブランキング、同期を取り出す。PLD は Altera MAX II（EPM570/EPM240）→ v4 は FPGA+補助 MCU。同方式の Lava RGB（Lattice FPGA）と Hi-Def NES（EXT＋CPU バス盗聴）がある。

### Cited Findings
- NESRGB は「Palette RAM (Color Generator), Decoder, and DAC」を迂回して複製する。「An Altera PLD sits between the PPU and the CPU data bus. When the CPU writes data into the Palette Ram … the data is captured and stored in the NESRGB board. Modified data is passed to the PPU. The PLD also intercepts writes to the register controlling the operation of the Multiplexer, making EXT0-3 outputs. … The rest of the information required (EXT4, blanking, and sync) is extracted from the video output with comparators.」フレームバッファなし・遅延なし 15kHz。パレット未選択時は素通し（元のコンポジット）。元アイデアは NESdev フォーラムの HardWareMan と thefox — [etim.net.au/nesrgb](https://etim.net.au/nesrgb/)
- Quietust (2020-08-06): PPU を slave モードにして EXT からパレットデータを出させる。EXT は4本なので BG とスプライトを区別できない。PPU に特殊パレットを与え「all background pixels are one color (likely black) and all nontransparent sprite pixels are another color (likely white)」、コンポジットから最上位パレットビットを復元。よって PPU 原コンポジットは「黒地に白い塊」 — [NESdev forum t=20636](https://forums.nesdev.org/viewtopic.php?t=20636)。同旨（BG パレット全黒・スプライト全白）が [Nerdly Pleasures](http://nerdlypleasures.blogspot.com/2015/06/nes-hardware-explained.html)（検索スニペットのみ確認）
- NESRGB の PLD: v1.x/v2.x = EPM570T100、v3 (2022) = EPM240T100（コア 1.8V、パレット1種固定）— [NESRGB Software and Errata](https://etim.net.au/nesrgb/background_fault/)。v4 = 「RAM based FPGA and a helper microcontroller」、6パレット内蔵、コントローラで切替、起動遅延のため NES のリセット容量 100n→220n — [NESRGB40](https://etim.net.au/nesrgb/NESRGB40.html)。v5 ドキュメント 2026-04-30 作成・2026-08-15 更新（内容未精査） — [NESRGB5](https://etim.net.au/nesrgb5/)
- NESRGB の「de-jitter」（NTSC 用タイミング補正）は NTSC 機で横揺れ（sync 不安定）を起こし、v2.2 で sync 補正を削除、v2.3 で機能自体を削除（実験版）— [Errata](https://etim.net.au/nesrgb/background_fault/)
- 内蔵パレット例: RGB Playchoice (Nestopia 2013), FCEUX, YUV, FirebrandX の Unsaturated-V6 / Smooth / Digital Prime / Magnum / Smooth V2, Sony CXA, Wavebeam — [Errata](https://etim.net.au/nesrgb/background_fault/), [NESRGB40](https://etim.net.au/nesrgb/NESRGB40.html)
- NESRGB はレンダリング無効時の色挙動（backdrop override）を再現しない（EXT に出ないため）— [WebSearch 要約（t=20636 周辺）](https://forums.nesdev.org/viewtopic.php?t=20636)（原文の該当箇所は未特定 → 弱い出典）。EXT 側の仕様（下記 Q3）とは整合。
- **Lava RGB**（Famicom AV 用、krzysiobal ら）: 「FPGA sits between PPU and CPU data buses and listens to that bus」。$2000 書込みを bit6 セットで PPU へ転送。パレット書込みを監視し完全コピーを内部保持。$2007 経由パレット書込みでは改変データを書き、BG とスプライトを2階調のモノクロにして第5ビットにする（Fiskbit「EXT only outputs the low 4 bits」）。閾値の異なる3コンパレータでビデオ出力から vblank・走査線開始・スプライト/BG を検出。FPGA は Lattice。クロックは 100Ω 経由で FPGA へ、他信号は 3.3-5V 変換バッファ経由。PPU の RD,/WR,ALE は FPGA 未接続 — [NESdev forum t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)
  - 既知の不具合: レンダリング中の $2007 アクセスによる v 増加を模擬しないため Codemasters（Dizzy, Micro Machines, MiG-29）で色化け。レンダリング無効時の色も再現せず（Fiskbit）— 同上
  - WDL6528（クローン PPU）多数でスプライトのみ乱れ → 原因はビデオ電圧レベル。R9 を 7.15k→10k にしてコンパレータ閾値（1.92V）を下げて解決。RP2C02G/H・UA6528 は問題なし。ビデオ出力にアンプを繋ぐと動作しなくなる — 同上
  - 注: 要約中「PPU pin 1 (video out)」とあるが 2C02 の VOUT は pin21（[PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)）。フォーラム原文の誤記か要約誤りかは **未確認**。
  - ライセンス表記なし。ソース所在: lava-fc.top, github.com/v5100v5100, PCBWay — 同上
- **Hi-Def NES**（kevtris）: 「connects to the NES CPU and PPU and extracts the video data from the EXP pins on the PPU, and turns it into HDMI」。CPU バスも盗聴（音源レジスタ書込み・DPCM DMA・コントローラ）。NES と HDMI を同期させ数ライン分だけバッファ。CPU/PPU を FPGA 生成クロック（約0.15%下げ）で駆動し 60.00fps 化。PPU に「嘘をつく」（改変パレット）言及あり — [NESdev forum t=12019（アーカイブ）](https://nesdev.nes.science/f9/t12019.xhtml)。スプライト判定の kevtris 自身の説明は取得範囲内になし（**未確認**）。
- **RGB Blaster**（Krikzz）: 無改造機向け。EXT は無改造機では接地で使えないため、カートリッジ端子の PPU バスを盗聴し、OAM は CPU の書込み（DMA）を追って FPGA 内で PPU を再実装。PPU 品種やタイミングに敏感、MMC5 等で不具合 — [nicole.express](https://nicole.express/2023/that-blasted-rgb.html)
- **PPU-LITE**（andkorzh, 2025）: Cyclone I EP1C3T100（41%使用）で PPU 全体を置換する FPGA PPU。初版 ADV7125、後版 R2R 抵抗 DAC。GitHub andkorzh/PPU-LITE、andkorzh/LAVA_RGB-TO-PPU_LITE（ライセンス名はスレッドに記載なし）。Fiskbit: slave モード（EXT 方式）機器は電源投入ごとに 1 画素ずれ、スプライト縁に色にじみが出ることがある — [NESdev forum t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)
- 市販 FPGA PPU 置換品 RGB2C02N Rev.3.2 は税込 17,980 円（家電のケンちゃん）、赤白 FC 取付基板 4,480 円 — [GDM 2024-01-12](https://gdm.or.jp/crew/2024/0112/521851)（検索要約経由、本文未精読）。Fiskbit は RGB2C02N に MMC3 ゲーム3本が壊れるバグがあると報告 — [t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)
- thefox: 「rogue writes might make FPGA's shadow palette out of sync」— [t=9503](https://nesdev.nes.science/f9/t9503.xhtml)

### Inferences
- NESRGB 方式の必須機能（本プロジェクトで再実装する場合）:
  1. CPU→PPU データバスの書込み改変: $2000 書込み時に PPU 側 D6=1 を強制、パレット領域への $2007 書込み時に D0-D5 を「BG 用暗色 / スプライト用明色」に差し替え（例: BG 側 $0F 系、スプライト側 $30 系。具体値は NESRGB で **未確認**）。→ CPU バスと PPU D0-D7 の間にバッファ（74HC245 等）を入れ、該当サイクルだけ外部（MCU）が PPU 側を駆動する構成になる。読出し（$2002/$2004/$2007）は素通し必須。
  2. CPU 書込みの盗聴と PPU 内部状態の追跡（Q4）。
  3. EXT0-3 の画素単位サンプリング（5.369 MHz）とパレット LUT → RGB DAC。
  4. VOUT のコンパレータ: 同期（sync tip vs blank）、第5ビット（暗/明）、可能ならブランキング。
  5. グレースケール・強調を外部で適用（EXT はパレットアドレスであり、$2001 の効果を含まないため）。
- 新設計基板では「PPU を外付けボードに載せる」必要がなく、上記を直接配線できるため NESRGB より単純化できる（ソケット変換・ケーブル不要）。
- LumaCode: c0pperdragon/LumaCode リポジトリの存在は確認したが、NES 用実装は見つからなかった（GitHub wiki は 403 で取得不可）。LumaCode は元機のデジタル画素データを輝度に符号化して送る規格であり、本件（基板内で直接 RGB 生成）には不要と判断。

### Gaps
- NESRGB が PPU に書く改変パレット値の正確な値、コンパレータ閾値・型番、PLD のソース（非公開と思われる、**未確認**）。
- Lava RGB の HDL 公開範囲・ライセンス（**未確認**）。
- 日本の同人基板で 2C02 EXT を使う RGB 化（自作）例は見つからなかった（日本語検索ではショップ記事の NESRGB / RGB2C02N 販売情報のみ: [GDM](https://www.gdm.or.jp/crew/2022/0308/430728)）。

---

## Q3. EXT ピンの正確な挙動

### Takeaway
PPUCTRL bit6=1 で EXT0-3 に「パレットメモリアドレスの下位4bit」が画素ごとに出る（bit4＝スプライト/BG は出ない）。透明画素ではそのスライバーのパレットの entry 0（=下位2bit 00）、レンダリング無効時は常に 0。出力タイミング・論理レベルの定量資料は見つからない。

### Cited Findings
- 「Setting bit 6 causes the PPU to output the lower four bits of the palette memory index on the EXT pins for each pixel.」「EXT output for transparent pixels is not a backdrop color as normal」（その BG スライバーのパレット entry 0 を出す）。「When rendering is disabled, EXT output is always index 0 regardless of backdrop override.」 — [NESdev Wiki: PPU programmer reference](https://www.nesdev.org/wiki/PPU_programmer_reference)
- bit6=0（通常）では EXT から backdrop 用パレットインデックスを読む。ストック機は EXT を GND 直結で backdrop = entry 0 — [PPU pinout](https://www.nesdev.org/wiki/PPU_pinout), [PPU programmer reference](https://www.nesdev.org/wiki/PPU_programmer_reference)。入力値は「neither BG nor SPR exists」の時に効く（Ueda 1989 論文、thomson；lidnariq が概ね同義と回答）— [NESdev forum t=14078](https://forums.nesdev.org/viewtopic.php?t=14078)
- 「Bit 6 of PPUCTRL should never be set on stock consoles because it may damage the PPU」「setting bit 6 is discouraged as it could potentially damage the chip whenever it outputs a non-zero pixel value」「Setting this bit does not affect the image in the PPU's composite video output.」 — [PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- slave 方式機器では電源投入ごとに EXT と映像の間で 1 画素ずれが起こり得る（Fiskbit）— [t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)
- 画素 = 4 マスタークロック（8 色生成クロック）≒186 ns、マスタークロック 21.47727273 MHz — [NESdev Wiki: NTSC video](https://www.nesdev.org/wiki/NTSC_video)

### Inferences
- 外部 LUT は「EXT 値の下位2bit=00 なら backdrop（$3F00）を使う」と処理すれば透明画素が正しく描ける（スプライト透明時も同様、第5ビットは BG 扱い）。$3F04/$3F08/$3F0C の値は通常描画で使われない。
- 新基板では EXT0-3 を GND に落とさず、MCU 入力へ直列抵抗（数百Ω〜1kΩ）経由で接続すれば bit6 の値にかかわらず安全（入力モード時は外部が 0 を与える必要があるので、プルダウン抵抗 10k 程度で backdrop=0 を保証）。
- EXT の出力レベル: 2C02 は NMOS で 5V 系。3.3V MCU（RP2040 は 5V トレラントでない）への接続には分圧またはレベル変換が必要（RP2040/RP2350 の 5V 耐性はデータシート未参照で **未確認**）。
- EXT と VOUT（第5ビット判定用）の相対遅延は固定数ドット程度と思われるが、1 画素ずれ報告があるため、起動時またはフレーム毎に位相を自動校正する仕組み（例: 既知パターンでの整合確認、あるいは VOUT の水平同期エッジ基準の位相合わせ）が望ましい。

### Gaps
- EXT 出力の画素クロックに対する遅延（ns/PPU サイクル）、VOUT 上の同一画素との遅延差、駆動能力・V_OH: 文書化された値なし（**未確認**）。Visual 2C02 シミュレータで検証可能 — [Visual 2C02](https://www.nesdev.org/wiki/Visual_2C02)
- 1 画素ずれの物理的原因（マスタークロック/4 分周の位相か）: **未確認**。

---

## Q4. パレットシャドウに必要な PPU 内部状態

### Takeaway
外部回路は CPU→PPU の $2000/$2001/$2002(読)/$2005/$2006/$2007 アクセスを盗聴し、t/v/w を模擬して $2007 の書込み先がパレット（$3F00-$3FFF）かを判定する必要がある。ミラー（$3F10↔$3F00 等）、+1/+32 増分、グレースケール・強調も外部で再現。レンダリング中の $2007 や backdrop override は既存品も未対応。

### Cited Findings
- $2002 読出しで内部 w をクリア。$2006 は上位→下位の順で 2 回書込み、t を経て v へ。$2007 アクセス後 v は PPUCTRL bit2 により +1/+32 — [PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- パレット読出しは内部バッファを経ず即時、上位2bitは PPU open bus。「developers should not rely on reading from palette RAM」（全 PPU にない機能）— [PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- 「the backdrop color can be written through both $3F00 and $3F10」、パレット全体は $3F00-$3FFF にミラー — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes), [PPU programmer reference](https://www.nesdev.org/wiki/PPU_programmer_reference)。$3F14/$3F18/$3F1C → $3F04/$3F08/$3F0C のミラーは今回取得したページ本文に明記なし（一般的な PPU 仕様では成立、**本調査では未確認**）。
- backdrop override: 強制ブランク中に v が $3F00-$3FFF を指すとその色を描画。スクロール位置次第で下端ボーダーにも自然発生 — [PPU programmer reference](https://www.nesdev.org/wiki/PPU_programmer_reference)
- グレースケールは「ANDing the 6-bit palette color value with $30」（Fiskbit）— [t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)。強調は 2C02 では他 2 成分を暗く、減衰係数約 0.816328（$xE/$xF には効かない）— [NTSC video](https://www.nesdev.org/wiki/NTSC_video), [PPU registers](https://www.nesdev.org/wiki/PPU_registers)
- レンダリング中の v 増加を模擬しない実装は Codemasters 系で色化け（Lava RGB）— [t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)
- $2007 への書込みはレンダリング中禁止（VRAM 破壊の恐れ）— [PPU registers](https://www.nesdev.org/wiki/PPU_registers)

### Inferences
- 最低限模擬すべき状態: t（15bit）, v（15bit）, w（1bit）, PPUCTRL bit2（増分）, PPUMASK（greyscale bit0, emphasis bit5-7, 表示有効 bit3/4）, パレット 32×6bit。$2005 も w を共有し t を書き換え、$2000 bit0-1 も t のネームテーブルビットを書く（[PPU scrolling](https://www.nesdev.org/wiki/PPU_scrolling) が出典の一般仕様だが今回本文未取得 → **要確認**）。パレット判定は v の上位ビットのみで足りるので、厳密には「$2006 の 2 回目書込み後の v」と「$2007 アクセス毎の増分」を追えば大半のゲームで十分。
- レンダリング中の v 変化（スクロール増分）を正確に追うには PPU のドット単位タイミングの模擬が必要。MCU では省略し、「表示有効中の $2007 書込みは無視」等の妥協が現実的（既存品も同じ妥協）。
- backdrop override（強制ブランク中に v がパレットを指す）は、外部回路が v と表示無効状態を知っているので理論上は再現可能（EXT は 0 を出すので、外部側で v 下位5bitのパレット値に置換）。既存品は未対応。

### Gaps
- PPU が CPU 書込みを内部に反映するタイミング（$2001 の強調・グレースケール変更が何ドット後に効くか）: **未確認**。

---

## Q5. マイコン（RP2040/RP2350 PIO）での実装可能性

### Takeaway
RP2040/RP2350 の PIO で 2C02 EXT を読んで RGB 化した公開実装は見つからなかった。既存の EXT 方式はすべて CPLD/FPGA（MAX II, Lattice, Cyclone）。理屈上は可能性があるが、CPU 書込みサイクル内での PPU データ改変（バス介入）と GPIO 本数・5V レベルが主なリスクで、前例なし。

### Cited Findings
- 「RP2040 PIO NES PPU RGB EXT」等で検索しても該当プロジェクトなし（RP2040 PIO の PAL 映像生成 [chipfire/rppico-pio-pal](https://codeberg.org/chipfire/rppico-pio-pal) など汎用例のみ）— 2026-11-10 検索
- 既存品の論理: NESRGB = EPM570T100/EPM240T100、v4 以降 FPGA+MCU（[Errata](https://etim.net.au/nesrgb/background_fault/), [NESRGB40](https://etim.net.au/nesrgb/NESRGB40.html)）; Lava RGB = Lattice FPGA（[t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)）; PPU-LITE = EP1C3T100（[t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)）
- Lava RGB の既知点: PPU 側の ALE と CPU/PPU サイクル位相が電源投入毎に変わる（「there are 3 PPU RD cycles per one CPU cycle」、/CE→ALE 遅延は起動時の位相依存）— [t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)
- 第5ビット判定コンパレータの閾値は PPU 品種の出力レベルで変わる（WDL6528 で 1.92V→下げる必要）— 同上

### Inferences（すべて調査者の推論、要試作検証）
- 画素レート: 5.369 MHz（186 ns/画素）。RP2350 を 150 MHz で動かすと 1 画素≒28 サイクル。PIO は 1 命令/サイクルなので EXT(4bit)+第5ビット(1bit) を 1 画素 1 回サンプリングし、DMA 経由で LUT 処理するのは帯域的に可能。ただし LUT（32 エントリ×色）をサンプル→出力に変換するのは CPU コアかPIO+DMA の工夫（例: DMA の「読出しアドレス=サンプル値」連鎖）が必要で、1 ライン遅延のバッファ方式（ライン単位でサンプル→変換→次ラインで出力、遅延 1H=63.5µs）にすれば余裕がある。
- クロック同期: マスター 21.47727 MHz 発振器を CPU/PPU と MCU で共有（RP2040/RP2350 の XIN に外部クロック入力し PLL で整数倍）すれば PIO と PPU ドットが位相固定になる。ドット位相（4 通り）の決定には PPU の /RD・ALE 等のストローブか VOUT 同期エッジでの位相合わせが必要。
- バス介入（最大の難所）: CPU 書込みは M2 High 期間（~280 ns）にデータが乗り PPU が取り込む。MCU が $2000 書込みの D6 と、パレット書込みの D0-D5 を PPU 側だけ差し替えるには、CPU バス—PPU バス間にバッファ（74HC245）または直列抵抗を挟み、MCU がアドレス (A0-A2, R/W, PPU /CS) をデコードして同サイクル内で駆動する必要がある。PIO の応答（数十 ns）で間に合う見込みはあるが前例なし。
  - 代替案（D6 強制のみロジックで）: $2000 書込み検出→PPU 側 D6 を強制 High は 74HC 系ゲート数個でも可能。パレット差し替えは MCU が担当。
- 第5ビットを改変パレットなしで得る案: EXT 値 i に対し候補色は BG 色 P[i] とスプライト色 P[16+i] の 2 つ。両者が同じなら判定不要、異なれば VOUT の輝度（またはサンプル波形）で区別できる場合がある。しかしパレット次第で判別不能（輝度同レベル・色相違い）なケースが残るため完全ではない。PPU へのパレット書込み改変を避けられる利点はある。
- GPIO 本数概算: Pico 2（RP2350A, 26 GPIO 程度使用可）で EXT 4 + 第5ビット/同期コンパレータ 2-3 + CPU 側盗聴 D0-7 8 + A0-A2/R-W/PPU-CS 5 + PPU 側 D 駆動の切替 1-2 + RGB DAC 9（3bit×3, 2C03 相当）〜12 + CSYNC 1 = 30〜35 本でオーバー。外部ラッチ（74HC574）での DAC 出力や、CPU データ盗聴を PPU 側バスで兼用する等の工夫が必要。RP2350B（48 GPIO）なら余裕だが Pico 2 ボードは RP2350A（**型番・GPIO 数はデータシート未参照で未確認**）。
- コンパレータ速度: 186 ns 画素で判定を誤らないには伝搬遅延が数十 ns 以下・遅延ばらつきが小さいことが必要。LM393/LM339 クラス（応答 µs オーダーの汎用品、**データシート未参照で未確認**）は不適と考えられ、高速コンパレータか、トランジスタ増幅＋74HC/74AC 入力閾値を利用した 2 値化が候補。同期分離（sync tip 48 mV vs blank 312 mV, 75Ω 終端時）は遅くてもよい。

### Gaps
- RP2350 GPIO の 5V トレラント可否、JLCPCB Basic Parts に高速コンパレータがあるか: 本調査範囲外で **未確認**（部品調査担当と要照合）。
- MCU によるバス介入の実証例: 見つからず。

---

## Q6. 代替: PPU のコンポジット出力を直接デコード

### Takeaway
2C02 の VOUT は「2 レベル間を切替える方形波」で生成される離散的な信号なので、21.47727 MHz の両エッジ（42.95 MHz）で生 VOUT をサンプリングすれば理論上パレット値を復元できる可能性がある（lidnariq が「oversampling VIDEO_OUT」と言及）。ただし高速 ADC/多段コンパレータと FPGA 級の処理が要り、前例・実装例は確認できず。アナログ NTSC デコーダ IC は画質（ドットクロール・にじみ）で劣る。

### Cited Findings
- マスタークロック 21.47727273 MHz、色生成は倍の約 42.95 MHz。1 画素 = 8 色生成クロック = 4 マスタークロック ≒186 ns。12 位相の方形波（約3.58 MHz）、色 $xY は Y 番の波。$x1〜$xC は $xD と $x0 の電圧間で交互、$xE/$xF は $1D と同電圧。終端時 sync 48 mV、blank 312 mV、$20 1100 mV。強調時 ×約0.816328。341 ドット×262 ライン、奇数フレームは1ドット短い（レンダリング有効時 89341 vs 89342 サイクル）。カラーバーストはドット 306 から 15 ドット、位相 8 — [NESdev Wiki: NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- lidnariq: 外部装置は「listening to the EXT bus or oversampling the VIDEO_OUT signal」で PPU を追える — [t=9503](https://nesdev.nes.science/f9/t9503.xhtml)
- NTSC video ページのデコーダは YUV→RGB 変換で、近隣画素の色が混ざり不正確と自ら述べる（インデックス復元は記載なし）— [NTSC video](https://www.nesdev.org/wiki/NTSC_video)
- RGB 化に Sony CXA2075 を使った例（RGB→コンポジット/S エンコーダ。逆方向ではない）— [t=9503](https://nesdev.nes.science/f9/t9503.xhtml)

### Inferences
- 生 VOUT（基板上フィルタ前）を 42.95 MHz で 8 サンプル/画素取得し、各サンプルを「どのレベルか（約 4 行×high/low＋sync/blank、強調で×0.816 の別レベル）」に量子化 → 高レベルの位相窓から hue を判定すれば 6bit 値＋強調が復元できる、という方式は理論上成立し得る。必要: 高速多値量子化（数十 MS/s の ADC か 8〜16 個の高速コンパレータ）と FPGA。部品規則（Basic Parts・FPGA 回避）に反し、本プロジェクトでは不適。
- 21.47727 MHz（片エッジ, 4 サンプル/画素）では 12 位相を一意に区別できない可能性が高い（推論、未検証）。
- アナログ NTSC→RGB デコーダ IC（例: TV 用 Y/C 分離＋RGB マトリクス IC）は入手性が悪く、ドットクロール・色にじみで「アーケード RGB 品質」にならない。入手性・型番は本調査で確認できず **未確認**。

### Gaps
- VOUT からの完全インデックス復元の実証例・論文: 見つからず。
- 現行入手可能な NTSC デコーダ IC（RGB アナログ出力）: 未調査。

---

## Q7. パレット選択・DAC・75Ω 出力・CSYNC

### Takeaway
2C03 互換なら 3bit/ch（9bit）で正確に再現でき、FirebrandX 等のエミュ由来パレットを使うなら 4〜5bit/ch 以上が望ましい。抵抗 DAC＋エミッタフォロワ（または高速 OP アンプ）で 75Ω 駆動。CSYNC は自走カウンタではなく PPU の VOUT から sync を分離して作るのが、262×341・奇数フレーム 1 ドット短縮に自然に追従する。

### Cited Findings
- 2C03 パレットは各チャネル 0〜7（3bit）、C=255×DAC/7 — [PPU palettes](https://www.nesdev.org/wiki/PPU_palettes)
- NESRGB が採用したパレット: RGB Playchoice（Nestopia）、FirebrandX Digital Prime（v3 標準）等 — [Errata](https://etim.net.au/nesrgb/background_fault/)
- PPU-LITE は ADV7125 から R2R 抵抗アレイ DAC に変更してコスト削減 — [t=26258](https://forums.nesdev.org/viewtopic.php?t=26258)
- 2C02 は常に 262 ライン、奇数フレーム 1 ドット短縮。2C03 はこの短縮なし — [NTSC video](https://www.nesdev.org/wiki/NTSC_video), [t=15541](https://nesdev.nes.science/f2/t15541.xhtml)
- NESRGB は同期をビデオ出力からコンパレータで抽出（[etim.net.au/nesrgb](https://etim.net.au/nesrgb/)）。de-jitter（同期補正）は不安定化で撤回（[Errata](https://etim.net.au/nesrgb/background_fault/)）。Lava RGB も vblank・走査線開始をコンパレータで検出（[t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)）

### Inferences
- アーケード（JAMMA）モニタは 0.7 Vp-p/75Ω 入力が一般的だが、日本の業務用モニタは 3〜5 Vp-p 程度の TTL 寄りレベルを受けるものも多い（**一般知識・未確認**）。ゲイン切替可能なエミッタフォロワ構成が無難。
- DAC 案: (a) 2C03 パレット専用 3bit×3 の重み付け抵抗（各ch 3本）＋ NPN エミッタフォロワ 3 石、(b) MCU GPIO 直結 R-2R 4〜5bit/ch。MCU GPIO 出力をそのまま抵抗 DAC にすると、出力切替のタイミングスキューは同一 PIO の同時出力で数 ns 程度に収まる見込み。
- CSYNC: VOUT の sync tip（終端時 48 mV）と blank（312 mV）の間（約 0.18 V、非終端時は約 2 倍）を閾値とする比較器（遅くてよい）で分離 → 74HC 系で整形して出力。これで 2C02 の奇数フレーム短縮やリセットにも自動追従。EXT 方式では RGB 映像と PPU 同期が同じ PPU から来るため位相ずれは画素未満（ただし 1 画素ずれ問題は Q3 参照）。
- ブランキング: EXT は表示外でも値を出すため、RGB をブランキング期間に 0 にするマスクが必要（VOUT のコンパレータ、または MCU のライン/ドットカウンタで生成）。

### Gaps
- 日本の業務用 15kHz モニタの入力レベル・CSYNC 極性の要件は本調査範囲外（**未確認**）。

---

## Q8. 選択肢の比較・ランキング（本プロジェクト向け、調査者の総合判断）

### Takeaway
部品規則（JLCPCB Basic Parts＋秋月入手品、FPGA/CPLD 回避）とドナー 2C02 前提を満たす唯一の現実的候補は「2C02 EXT 方式を RP2350（Pico 2）PIO で実装」だが前例がなくリスクが最大。確実性重視なら CPLD/FPGA による NESRGB/Lava RGB 方式（実績あり）。RGB PPU（2C03）は回路は最も簡単だが 1 個 125〜260 USD・品切れで量産不可。

### Cited Findings（ランキングの根拠）
- EXT 方式の実績: NESRGB（2013〜、MAX II CPLD）, Lava RGB（Lattice FPGA）, Hi-Def NES（FPGA）— [etim](https://etim.net.au/nesrgb/), [t=25963](https://forums.nesdev.org/viewtopic.php?t=25963), [t=12019](https://nesdev.nes.science/f9/t12019.xhtml)
- EXT 方式の既知制約: 1 画素ずれ（Fiskbit）、レンダリング中 $2007 での色化け、backdrop override 非対応、PPU 品種でコンパレータ閾値調整 — [t=26258](https://forums.nesdev.org/viewtopic.php?t=26258), [t=25963](https://forums.nesdev.org/viewtopic.php?t=25963)
- RGB PPU 価格 110〜260 USD、品切れ — [Arcade-Museum](https://forums.arcade-museum.com/threads/wtb-rp2c03-ppu.506933/), [tall-dog](https://shop.tall-dog.com/products/rgb-format-nes-core-ppu-chip)
- FPGA PPU 置換（PPU-LITE, RGB2C02N 17,980 円）は 2C02 を使わない — [t=26258](https://forums.nesdev.org/viewtopic.php?t=26258), [GDM](https://gdm.or.jp/crew/2024/0112/521851)

### Inferences（ランキング）
| 順位 | 方式 | コスト | 部品入手/規則適合 | 技術リスク | 画質 |
|---|---|---|---|---|---|
| 1 | 2C02 EXT＋Pico 2（RP2350 PIO）＋74HC バッファ/ゲート＋コンパレータ＋抵抗 DAC | 低（Pico 2 + 汎用品） | ◎（秋月 Pico 2、汎用ロジック/抵抗） | 高（前例なし、バス介入タイミング、GPIO 不足、5V レベル、1 画素ずれ） | 良（NESRGB 同等、レンダリング中 $2007 等の既知制約あり） |
| 2 | 2C02 EXT＋小型 CPLD/FPGA（NESRGB/Lava 方式の再実装） | 中 | ×（FPGA/CPLD 回避方針、EPM240 等は Basic ではない可能性大・**未確認**） | 中（実績あり） | 良 |
| 3 | RGB PPU（RP2C03B/RC2C03B/C）をソケット実装＋RGB バッファ | 高（1個 125〜260 USD） | ×（中古のみ・品切れ、量産不可） | 低（回路はバッファと同期のみ） | 良（2C03 パレット固定、強調挙動が異なる） |
| 4 | VOUT 高速サンプリング（FPGA）で完全復元 | 中〜高 | ×（高速 ADC/FPGA） | 高（前例なし） | 理論上良 |
| 5 | アナログ NTSC デコーダ IC | 中 | △（入手性 **未確認**） | 低〜中 | 低（ドットクロール、にじみ） |
| 参考 | FPGA PPU 置換（PPU-LITE/RGB2C02N） | 中〜高 | × | 中（互換性バグ報告あり） | 良 — ただし本件の「実機 2C02 使用」前提外 |

- 推奨方針（推論）: 基板は「2C02 ＋ Pico 2 方式」を主案とし、(a) pin14-17/21 をジャンパで RGB PPU にも対応できるようにしておく（Q1 Inferences）、(b) Pico 2 が CPU→PPU 書込みを改変できるよう CPU–PPU 間に 74HC245 を挟む、(c) コンパレータは閾値調整可能（半固定抵抗 or MCU PWM で閾値生成）にする — と、試作 1 回目で方式検証ができる。第5ビット判定と 1 画素ずれの自動校正をファーム側で吸収する設計が肝。
- 最小コスト・最小部品点数の観点では、MCU 1 個に処理を集約し外付けは 74HC245×1〜2、高速コンパレータ×1〜2（デュアル）、抵抗 DAC、エミッタフォロワ用トランジスタ 3〜4 石程度が下限と見積もる（推論、部品の Basic 可否は **未確認**）。

### Gaps
- Pico 2 でのバス介入・EXT サンプリングの実測例がないため、ランキング 1 位の成立性は試作検証待ち。
- JLCPCB Basic Parts 該当品（高速コンパレータ、74HC245、トランジスタ）の確認は別担当。
