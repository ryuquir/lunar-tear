# RP2C02 からアナログ RGB 映像を得る方法 - 要約

## 1. この分野の結論

1. **推奨は EXT 方式である。** ドナー機のファミコンから外した RP2C02（PPU。画面を作るチップ）をそのまま使い、PPU の EXT 端子（pin14〜17）からパレット番号（色の表の何番目かを表す値）を読み、マイコンが持つパレットの複製で RGB を作り直す。方式と既存製品は確認済で、マイコンで作った前例はない（推論）。
2. **RGB 出力版 PPU（RP2C03B、RC2C03B/C、RC2C05-xx など。R/G/B を直接出す業務用の PPU）は量産の前提にできない。** 中古しかなく 1 個 110〜260 USD で、tall-dog の掲載品は 2026-11 時点で全品 Sold Out である（確認済）。
3. **最大のリスクは、スプライトと背景（BG）を見分ける高速な比較器（電圧がしきい値より上か下かを判定する部品）である。** 1 画素は 186 ns だが、JLCPCB の Basic/Preferred にある比較器は LM393（1.3 µs、TTL 振幅の入力でも 300 ns）だけで間に合わない（確認済）。ディスクリート回路、LM319（80 ns）、ADCMP600（4 ns、秋月 ¥830）の順に最初の試作で評価する（推論）。
4. **実チップで動かすには GPIO（マイコンの入出力端子）が最小 37 本、推奨 40〜41 本要り、Pico 2（26 本）1 枚では足りない。** 試作 1 回目は Pico 2 を 2 枚使い、A を「クロック・リセット・映像」、B を「バスの盗聴と置き換え・パッド応答・JAMMA の入出力」に分ける構成を推奨する（端子数は確認済、構成は推論）。
5. **CPU・PPU のクロックと PPU /RST（pin22）は Pico A が握る。** PIO（RP2350 の高速入出力用の小さな処理装置）が 129 MHz ÷ 6 = 21.5 MHz（公称 21.47727 MHz に対し +1058 ppm）を出し、PPU /RST をクロックに合わせて解除する。既存の EXT 方式の製品で起きる「電源投入ごとに 1 画素ずれる」問題が原理的に消え、15 kHz のモニタの受け入れ範囲にも入る（推論）。
6. **PPU に書くパレットは、CPU と PPU のデータ線の間に入れた 470 Ω の直列抵抗 8 本（0603 単品 C23179、Basic）を介して、マイコンが PPU 側だけ書き換える。** PPU には BG = $0F（黒）、スプライト = $20（白）を書き、強調とグレースケールのビットは 0 に置き換える。74HC245 を挟む案は 3.3 V で制御できず不利である（推論）。
7. **PPU の映像タイミングは 1 ライン 341 ドット・262 ライン、15.7458 kHz・約 60.10 Hz で、業務用の 15 kHz モニタの範囲に入る**（数値は確認済、適合の判断は推論）。同期信号は Pico A の PIO のカウンタで作り、NPN トランジスタで 5 V の負極性 CSYNC（複合同期）にする（推論）。
8. **映像をマイコンが作り直すので、タイマー方式の残り時間、INSERT COIN、設定画面は追加部品なしで画面に重ねて描ける。** 1 ライン遅延のラインバッファ（1 ライン分の画素をためる記憶領域）に文字を書くだけで済み、ゲームには影響しない（推論）。
9. **JAMMA への RGB 出力は、日本の筐体の入力（正極性約 3 Vp-p、約 2 kΩ）に合わせる。**（入力仕様は確認済）DAC（デジタル値を電圧に変える回路）は重み付け抵抗で開放 3.0 V、出力インピーダンス 100〜150 Ω を目標にし、将来の色数向上のため 4-4-4 以上を推奨する（推論）。
10. **色の表（パレットデータ）は pally（MIT No Attribution）で 2C02G の 512 色を生成して埋め込むのが権利の面で最も安全である。** ライセンスは確認済で、安全という判断は推論である。

## 2. 報告書にそのまま載せる表

確度の表記: 確認済（2 つ以上の独立した出典、またはネットリスト・データシート・実物のデータで確認）、単一出典（出典が 1 つ）、未確認（出典なし）、未確認（推論）（調査者の計算や判断）。用語: EXT 方式は EXT 端子とシャドウパレット（CPU が PPU に書くパレット値を外部回路が盗み見て保持する複製）を使う方式。第5ビットはパレット番号の bit4（0 = BG、1 = スプライト）で、EXT には出てこない。VOUT は PPU pin21 のコンポジット映像出力。

### 2.1 RGB を得る方式の比較

| 方式 | 仕組み | 実績のある例 | 部品・規則への適合 | 技術リスク | 画質 | 確度 |
|---|---|---|---|---|---|---|
| A. RGB 出力版 PPU に交換 | RP2C03B、RC2C03B/C、RC2C05-xx などを同じ DIP-40 ソケットに挿す。R/G/B と /SYNC が直接出る | VS. System、PlayChoice-10、Sharp C1、Famicom Titler。TinyNES の RGB キット | ×（中古のみ。1 個 110〜260 USD、品切れ） | 低（バッファと同期の整形だけ） | 良（パレットは 2C03 固定。強調の挙動が 2C02 と違う） | 確認済 |
| B. EXT 方式（EXT 端子とシャドウパレット） | $2000 の bit6 を立てて EXT にパレット番号の下位 4bit を出させる。パレットへの書き込みは盗聴して複製し、PPU には「BG は暗い色、スプライトは明るい色」に書き換えた値を渡す。第5ビット・ブランキング・同期は VOUT から比較器で取り出す | NESRGB（CPLD のち FPGA）、Lava RGB（Lattice FPGA）、Hi-Def NES（FPGA） | CPLD や FPGA で作れば規則外。RP2350 の PIO で作れば ◎ だが前例がない | 中（CPLD/FPGA）／高（マイコン） | 良（既知の制約あり。2.2 参照） | 確認済（方式と製品）／マイコンでの実装は未確認 |
| C. コンポジット出力の解読 | (C1) VOUT を 42.95 MHz（画素あたり 8 回）で標本化して色番号を復元する。(C2) アナログの NTSC デコーダ IC で RGB にする | C1 は lidnariq が「oversampling VIDEO_OUT」と言及しただけで、実装例は見つからない。C2 は具体例が見つからない | ×（C1 は高速 ADC か多数の高速比較器と FPGA が要る）／△（C2 は IC の入手性が未確認） | 高（C1）／低〜中（C2） | C1 は理論上良。C2 はドットクロールと色にじみで劣る | 単一出典（C1 の言及）／未確認（性能） |
| D. PPU のバスを盗聴して PPU を作り直す | カートリッジ端子の PPU バスと CPU による OAM への書き込みを追い、FPGA の中で PPU を再実装する | RGB Blaster（Krikzz）、PPUdigitizer（c0pperdragon、受動的な盗聴で LumaCode を出す。内部方式は非公開で、D に分類するのは「passively listen」の一文に基づく推論） | ×（FPGA） | 中〜高（PPU の品種やタイミングに敏感。MMC5 などで不具合） | 良 | 単一出典（PPUdigitizer の分類は未確認（推論）） |
| E. PPU 自体を置き換える | FPGA で作った PPU を RP2C02 の代わりに挿す | PPU-LITE（andkorzh）、RGB2C02N Rev.3.2（税込 17,980 円。価格は検索要約経由で本文未精読） | ×（FPGA。実機の 2C02 を使う前提から外れる） | 中（RGB2C02N は MMC3 のゲーム 3 本が壊れるとの報告） | 良 | 単一出典 |

調査者による順位付け（未確認（推論））:

| 順位 | 方式 | コスト | 部品入手と規則への適合 | 技術リスク |
|---|---|---|---|---|
| 1 | B を Pico 2（RP2350 PIO）と汎用部品で作る | 低 | ◎（秋月の Pico 2、汎用ロジック、抵抗） | 高（前例なし。バス介入のタイミング、GPIO 不足、5V レベル、比較器） |
| 2 | B を小型 CPLD/FPGA で作り直す | 中 | ×（CPLD/FPGA は避ける方針） | 中（実績あり） |
| 3 | A（RGB 出力版 PPU） | 高 | ×（量産不可） | 低 |
| 4 | C1（VOUT の高速標本化） | 中〜高 | × | 高 |
| 5 | C2（アナログ NTSC デコーダ） | 中 | △ | 低〜中（画質は低） |
| 参考 | E（FPGA PPU） | 中〜高 | × | 中 |

### 2.2 EXT 端子方式に必要なもの

#### EXT 端子が出すもの（取り出す信号）

| 項目 | 内容 | 確度 |
|---|---|---|
| 出力モードにする方法 | PPUCTRL（$2000）の bit6 = 1。原文は「Setting bit 6 causes the PPU to output the lower four bits of the palette memory index on the EXT pins for each pixel.」 | 確認済（NESdev Wiki と Breaking NES のダイ解析） |
| 出力の中身 | パレットメモリのアドレスの下位 4bit。BG とスプライトの区別（bit4）は出ない。原文は「Since only four bits are output, background and sprite pixels can't normally be distinguished this way.」 | 確認済 |
| 内部での位置 | マルチプレクサは 3 段になっている。1 段目で BG とスプライトを優先度（/ZPRIO）で選び、2 段目で EXT 入力と選び、3 段目で direct color（パレットへの直接アクセス時）を選ぶ。EXT に出るのは 2 段目の出力（n_EXT_OUT）で、パレット RAM と DAC より前にある | 確認済（Breaking NES） |
| ラッチ | n_EXT_OUT は n_PCLK を enable とする DLatch を通り、n_SLAVE（$2000 bit6 の反転）でゲートされた出力バッファから EXT_Pad_Out に出る。入力側は透過型の DLatch から EXT_IN に入る | 単一出典（Breaking NES の pads.md と図） |
| 透明画素 | 背景色（backdrop）ではなく、その BG スライバー（8 画素の区画）のパレットの entry 0 を出す。原文は「EXT output for transparent pixels is not a backdrop color as normal, but rather entry 0 of that background sliver's palette.」 | 確認済 |
| レンダリング無効時 | 常に index 0 を出す。原文は「When rendering is disabled, EXT output is always index 0 regardless of backdrop override.」 | 確認済 |
| backdrop override | 強制ブランク中に v が $3F00〜$3FFF を指すとその色が描かれる機能。これは EXT に出ない（direct color が 3 段目にあることと回路の構造が一致する） | 確認済 |
| コンポジットへの影響 | bit6 を立ててもコンポジット映像は変わらない。原文は「Setting this bit does not affect the image in the PPU's composite video output.」 | 確認済 |
| 入力モード（bit6 = 0） | EXT から backdrop 用のパレット番号を読む。BG もスプライトも無い画素で効く。市販機は EXT を GND に直結しているので backdrop は entry 0 | 確認済 |
| 損傷の危険 | 「Bit 6 of PPUCTRL should never be set on stock consoles because it may damage the PPU」。EXT が GND に直結された機体で 0 以外を出すと、VCC と GND の短絡になり得る | 確認済 |
| 論理レベル | 2A03/2C02 の出力 High は約 4 V（lidnariq の実測。原文は「my previous measurements have Voh from the 2A03 and 2C02 at approximately 4V」）。EXT 端子に限った V_OH/V_OL・駆動電流・立ち上がり時間の資料は無い | 単一出典（約 4 V）／未確認（EXT 個別の値） |
| タイミング | 1 画素 = PCLK 1 周期 = CLK/4。CLK は 21477272 Hz（約 0.046 µs）、PCLK は 5369318 Hz（約 0.186 µs）。PCLK エッジから EXT 出力までの遅延（ns）は資料なし | 確認済（周期）／未確認（遅延） |
| VOUT との相対遅延 | NTSC の映像出力は PPU 内部の画素タイミングより 1 pixel clock 遅れる。カラーバッファの出力は D-Latch の連鎖を通る（「the video generator essentially outputs pixels "from the past"」）。EXT と VOUT 上の同じ画素との差（PCLK 数）は資料なし | 確認済（遅れること）／未確認（量） |
| 水平・垂直ブランキング中の EXT の値 | 資料なし | 未確認 |
| 既存品の位置合わせ | NESRGB v1.0 のブロック図では、EXT0..EXT3 が「DELAY」と「EXT DATA SYNCHRONISE」（PIXEL CLOCK 入力）を通り、比較器から来る「EXT4-VIDEO」と合流する。Lava RGB のファーム更新履歴（2023-07-02）には「使用FIFO实现ext4和ext0-3数据对齐，大大提升稳定性」とある | 確認済（2 製品） |
| 1 画素ずれ | Fiskbit: 「they have sync issues where the digital and analog sources may be off by 1 pixel on some power cycles」「causing color fringes on one edge of all sprites」 | 単一出典 |
| 実例の接続 | Lava RGB は EXT0-3 を 3.3V 側（EXT0_3V3〜EXT3_3V3）へレベル変換して FPGA に入れる（BOM に SN74LVC541APW ×2、SN74LVC4245APWR ×2）。TinyNES は EXT0-3 を各 10kΩ で GND へプルダウンする（R25〜R28） | 確認済（回路図・BOM） |

#### 第5ビット（スプライトか BG か）の取り出し

PPU に「BG は全部暗い平坦な色、スプライトは全部明るい平坦な色」を書くと、VOUT の明るさだけで第5ビットが分かり、比較器 1 個のしきい値で判定できる。1 画素は 186 ns で、比較器の遅延そのものより遅延のばらつきが画素幅より十分小さいことが大事である（未確認（推論））。比較器の候補は 2.4 の表のとおり。

#### 外部回路が追跡する PPU 内部状態

パレットへの書き込みは PPU の外の VRAM バスからは見えない（確認済）ので、CPU 側のバスを盗聴して次の状態を外部で再現する。

| 状態・挙動 | 内容 | 確度 |
|---|---|---|
| 盗聴するアクセス | $2000 書き込み、$2001 書き込み、$2002 読み出し、$2005 書き込み、$2006 書き込み、$2007 の読み書き | 未確認（推論。各レジスタの挙動は下の行のとおり確認済で、そこから導いた一覧） |
| w（書き込みトグル） | $2002 の読み出しで 0 に戻る。$2005 と $2006 で共有され、「only remembers the order of access (1 or 2), but not the register number」 | 確認済 |
| t と v | $2006 は上位、下位の順で 2 回書き、t を経て v に入る。$2007 アクセスの後、v は PPUCTRL bit2 により +1 または +32 される | 確認済 |
| $2005 と $2000 bit0-1 による t の書き換え | $2005 も w を共有して t を書き換え、$2000 bit0-1 も t のネームテーブルのビットを書く | 未確認（第1次調査で一般仕様として挙げたが本文未取得） |
| 最低限まねる状態 | t（15bit）、v（15bit）、w（1bit）、PPUCTRL bit2（増分）、PPUMASK（グレースケール bit0、強調 bit5〜7、表示有効 bit3/4）、パレット 32 × 6bit | 未確認（推論） |
| パレットのミラー | 背景色は $3F00 と $3F10 のどちらからでも書ける。パレット全体は $3F00〜$3FFF にミラーされる | 確認済 |
| $3F14/$3F18/$3F1C → $3F04/$3F08/$3F0C のミラー | 取得したページには明記がない | 未確認 |
| パレットの読み出し | 内部バッファを通らず即時。上位 2bit は PPU の open bus。2C02G/H と PAL 版にしかない機能で、「developers should not rely on reading from palette RAM」 | 確認済 |
| レンダリング中の $2007 | 書き込みは禁止（VRAM 破壊の恐れ）。レンダリング中のアクセスによる v の特殊な増分をまねない実装では、Codemasters のゲーム（Dizzy、Micro Machines、MiG-29）で色化けが起きる（Lava RGB の既知の不具合） | 単一出典 |
| backdrop override の再現 | NESRGB と Lava RGB は再現しない | 単一出典 |
| 盗聴でずれる危険 | thefox: 「rogue writes might make FPGA's shadow palette out of sync」 | 単一出典 |
| $2001 の変更が何ドット後に効くか | 資料なし | 未確認 |
| MMC5 も CPU バスを盗聴する | 「The MMC5 listens to writes to PPUMASK ($2001)」「The MMC5 only listens to the fully decoded address $2001」 | 単一出典 |

### 2.3 既存製品・既存設計

| 名称 | 方式 | 主な部品 | 公開範囲 | ライセンス | 確度 |
|---|---|---|---|---|---|
| NESRGB（Tim Worthington） | EXT 方式。PPU を自分の基板のソケットに載せ、CPU データバスと PPU の間に PLD を挟む。パレットを複製し改変値を PPU に渡す。第5ビット・ブランキング・同期は比較器で取り出す。フレームバッファなし・遅延なし、15kHz。パレット未選択時は元のコンポジットを素通しする。元のアイデアは NESdev フォーラムの HardWareMan と thefox | v1.x/v2.x は EPM570T100、v3（2022）は EPM240T100（コア 1.8V、パレット 1 種固定）、v4 は「RAM based FPGA and a helper microcontroller」（6 パレット内蔵、コントローラで切り替え、起動が遅いので NES のリセット容量を 100n から 220n に変更）。v5 は GSV331、MX3502S、GS8051。RGB は 7:7:7 で DAC へ。「TTL COMPOSITE SYNC (CS#)」出力あり。J8 は「composite sync output type. Open for TTL, short for 75 ohm」 | ブロック図とピン配置 PDF のみ。回路図と PLD ソースは非公開 | 記載なし | 確認済 |
| NESRGB の de-jitter | 「precisely controlling the clock to the PPU to make the video timing standard compliant」（OSSC の作者 marqs の手法）。NTSC 機で横揺れが出たので v2.2 で同期補正を削除し、v2.3 で機能ごと削除（実験版） | — | — | — | 確認済 |
| Lava RGB（krzysiobal ら、ファミコン AV 用） | EXT 方式。「FPGA sits between PPU and CPU data buses and listens to that bus」。閾値の違う 3 つの比較器で vblank・走査線の開始・スプライト/BG を検出。クロックは 100Ω を通して FPGA へ。他の信号は 3.3-5V 変換バッファを通す。PPU の RD、/WR、ALE は FPGA につながない | U7 LCMXO2-1200HC-4TG100I、U2 LMV7219M5X、U5 TLV3502AIDR、U3 SGM8051XN5/TR（映像 OP アンプ）、U4 BH7240AKV（RGB からコンポジット/S へのエンコーダ）、U6/U8 SN74LVC4245APWR、U9/U11 SN74LVC541APW、U1 MCP1703T-3302E/MB、R9 7.15kΩ、R7/R19/R11 16kΩ/100kΩ/300Ω、R13〜R18 75Ω ×6 | Altium 回路図・基板・BOM・ファーム（.jed 9 種と readme.txt のみ）を GitHub に公開。HDL はない | 表示なし（LICENSE ファイルなし） | 確認済（BOM は一次資料） |
| Lava RGB の既知の不具合 | Codemasters 系の色化け、レンダリング無効時の色を再現しない、WDL6528 でスプライトだけ乱れる（R9 の変更で解決） | — | — | — | 単一出典 |
| Hi-Def NES（kevtris） | 「connects to the NES CPU and PPU and extracts the video data from the EXP pins on the PPU, and turns it into HDMI」。CPU バスも盗聴する（音源レジスタ、DPCM DMA、コントローラ）。CPU/PPU を FPGA が作るクロックで動かし、約 0.15% 下げて 60.00fps にする。「the NES and HDMI are locked together in synchrony so I only need to buffer a couple scanlines」、のちに PLL 方式。v2.0 で「do not reset PPU on reset to prevent the rolling」 | FPGA | 非公開 | 未確認 | 確認済 |
| PPUdigitizer（c0pperdragon） | 「will passively listen to the data transfer between the PPU and the rest of the system」。PPU の裏にはんだ付けする FPGA 基板で、LumaCode を出す。元のコンポジットは変えない。「supports the PAL variants of the PPU, as well as most NTSC variants」。内部方式は非公開 | FPGA（型番未確認） | LumaCode リポジトリは信号規格と参照実装のみで、NES 用のソースはない | LumaCode リポジトリに LICENSE なし | 単一出典 |
| RGB Blaster（Krikzz） | 無改造機向け。カートリッジ端子の PPU バスを盗聴し、OAM は CPU の書き込みを追って FPGA の中で PPU を再実装する。PPU の品種やタイミングに敏感で、MMC5 などで不具合 | FPGA | 未確認 | 未確認 | 単一出典 |
| PPU-LITE（andkorzh、2025） | PPU 全体を FPGA で置き換える | Cyclone I EP1C3T100C8N（41% 使用）。DAC は初版が ADV7125、後の版が R2R 抵抗 DAC（「6-bit plus one-bit emphasis per channel」）。Lattice Diamond 版もある | GitHub で HDL 公開 | GPL-3.0 | 確認済 |
| LAVA_RGB-TO-PPU_LITE | Lava RGB の基板を FPGA PPU に転用する。「It requires removing the comparators from the board」 | — | GitHub | 未確認（LICENSE ファイルが見つからない） | 単一出典 |
| RP2C02-7-（andkorzh） | Verilog による 2C02（RP2C02.v 1672 行、EXT 端子は実装なし） | — | GitHub | GPL-3.0 | 単一出典 |
| Breaking NES（emu-russia/breaks） | 2C02 などのダイ解析 | — | 公開 | CC0 1.0 | 単一出典 |
| RGB2C02N Rev.3.2 | 市販の FPGA PPU 置き換え品 | — | 非公開 | — | 単一出典（税込 17,980 円、赤白 FC 取付基板 4,480 円） |
| TinyNES（tall-dog） | 量産・出荷済みの NES 互換基板。RGB 出力版 PPU 用の RGB キットあり | 主基板 TD-TNES-27-MB: クロックは SIT2001BC-S2-33N-21.477270（3.3 V の MEMS 発振器）から PL133-37TC（クロックバッファ）を経て 30 Ω（R3〜R5）で CPU と PPU へ。3.3 V LDO は AP2127N-3.3。EXT0-3 は 10kΩ ×4（R25〜R28）で GND へ。2C05 用に S5 で PPU A0 を切り替え。コンポジットは R19 300Ω、Q1 3906、C31 220µF、R21 110Ω、C35 560pF。RGB 基板 TD-TRGB-C rev C: U1 THS7314DR に R/G/B を直結（入力にバイアス・終端抵抗なし）、出力は 75Ω（R1〜R3）、電源は 10µ + 0.1µ | 回路図・BOM を GitHub で公開 | CC BY-SA 4.0 | 確認済 |
| NES2JAMMA（自作例） | NESRGB の出力を JAMMA へ。映像は「TLS1233 and LM1881」、音声は「a basic LM384」。同期の問題は報告なし | — | フォーラム | — | 単一出典 |

- RP2040/RP2350 で EXT 方式を作った例は見つからない。本基板が最初の例になる可能性が高い（未確認（推論））。
- 日本の同人基板で 2C02 の EXT を使って RGB 化した例は見つからなかった。

### 2.4 比較器の候補

| 品番 | 応答・伝搬遅延（typ） | 条件 | 入手先 | 確度 |
|---|---|---|---|---|
| LM393 / LM2903 | 1.3 µs（B 版は 1 µs） | 100 mV ステップ、5 mV オーバードライブ、5.1k プルアップ | JLCPCB Basic/Preferred（C7955）。Basic/Preferred にある唯一の比較器 | 確認済（TI データシート、JLCPCB API 照会） |
| LM393 | 300 ns | 「TTL input with Vref = 1.4V」 | 同上 | 確認済 |
| LM339 | 1.3 µs / 300 ns（TTL 入力） | 同上 | 未確認 | 単一出典（TI） |
| LM311 | 115 ns（L→H）/ 165 ns（H→L） | 100 mV ステップ、5 mV オーバードライブ | 未確認 | 単一出典（TI） |
| LM119 / LM319 | 80 ns | ±15 V、100 mV ステップ、5 mV オーバードライブ | 秋月で LM319M 5 個 ¥50（関連商品の表示）。オープンコレクタ出力 | 単一出典（TI、秋月） |
| LMV7219 | 7 ns（5V、オーバードライブ 50 mV）/ 8 ns（15 mV）/ 9 ns（5 mV）、skew 0.4 ns | 2.7〜5 V、プッシュプル出力 | JLCPCB の分類は未確認 | 単一出典（TI） |
| TLV3501 / TLV3502 | 4.5 ns（max 6.4）@ オーバードライブ 20 mV、7.5 ns @ 5 mV、skew 0.5 ns | 2.7〜5.5 V | JLCPCB の分類は未確認 | 単一出典（TI） |
| MAX999 | 4.5 ns | 5 mV オーバードライブ、VCC=3V、5pF | 未確認 | 単一出典（二次ミラー。原 PDF は未取得） |
| MCP6561 | 56 ns（H→L）/ 49 ns（L→H）@ VDD 1.8V | — | 未確認 | 未確認（検索要約のみ。要再確認） |
| ADCMP600BRJZ-R2 | 応答 4 ns | 2.5〜5.5 V、SOT23-5 | 秋月 ¥830、在庫 220（2026-11-10） | 単一出典（秋月） |
| LTC6752HS5 | 1.2 ns | 2.45〜3.5 V、オープンドレイン | 秋月 ¥750 | 単一出典（秋月） |

- JLCPCB の Basic/Preferred には LM393 より速い比較器は無い。確認済（JLCPCB API の全件照会）。

### 2.5 PPU の映像タイミング

#### 水平（1 ライン 341 ドット）

| 区間 | 開始ドット | 長さ（ドット） |
|---|---|---|
| H sync | 277 | 25 |
| back porch | 302 | 4 |
| colorburst | 306 | 15（位相 8） |
| back porch | 321 | 5 |
| pulse（backdrop のグレースケール） | 326 | 1 |
| 左ボーダー | 327 | 15 |
| active | 1 | 256（ドット 0 は黒の 1 画素） |
| 右ボーダー | 257 | 11 |
| front porch | 268 | 9 |

単一出典（NESdev Wiki: NTSC video）。PPU の映像出力は 1 ピクセルクロック遅れる。

#### 垂直（262 ライン）

| 区間 | ライン |
|---|---|
| 表示 | 0〜239 |
| post-render | 240〜241（VBlank フラグはライン 241 でセット） |
| post-render blanking | 242〜244 |
| vertical sync | 245〜247（3 ライン。vertical blanking pulse は dot 277 から 318 ドット、serration は dot 254 から 32 ドット） |
| pre-render | 248〜261（VBlank はライン 261 でクリア） |

単一出典（NESdev Wiki: NTSC video。262 ライン自体は確認済）。

#### 奇数フレームの短縮と数値

| 項目 | 値 | 確度 |
|---|---|---|
| 奇数フレームの短縮 | レンダリング有効時、「skipping the first idle tick on the first visible scanline」（(339,261) から (0,0) へ）。フレームは 89341 / 89342 クロックの交互。レンダリング無効時は 341×262 = 89342 で短縮なし。プリレンダーラインの末尾でレンダリングを無効にすると 89342 に固定 | 確認済 |
| RGB 出力版 PPU | 2C03/2C04 は短縮なし（回路が切断）。RC2C05-99 は短縮あり | 確認済 |
| マスタークロック | 21.477272 MHz（236.25 MHz ÷ 11、± 40 Hz） | 確認済 |
| ドットクロック | 5.369318 MHz（÷4）、1 ドット 186.24 ns | 確認済 |
| 1 ライン | 341 ドット = 63.51 µs、15.7458 kHz（113.667 CPU サイクル） | 確認済 |
| H sync | 25 ドット = 4.66 µs | 未確認（推論・計算） |
| V sync | 3 ライン ≈ 190.5 µs | 未確認（推論・計算） |
| フレーム | 60.0985 Hz（描画無効）/ 60.0988 Hz（描画有効の 2 フレーム平均） | 確認済 |
| モニタの受け入れ範囲 | K7000 は 15.1〜16.8 kHz / 47〜63 Hz、MTC 9000 は 15.625 ± 0.3 kHz（調整範囲）と 45〜70 Hz。15.7458 kHz / 60.10 Hz はいずれにも入る。任天堂も VS. / PlayChoice-10 で同じ 341×262 を 15 kHz の業務用モニタで使った（型番 Sanyo 20-EZV / 20-Z2AW は PlayChoice-10 の取説で確認したもの。VS. System のモニタ型番は未確認） | 確認済（各マニュアル）／適合の判断は推論 |
| ドットスキップの見え方 | 短いラインの直後の最初の可視ラインが 1 ドット左にずれ、上端の画素が揺れる（利用者の報告） | 単一出典 |

### 2.6 Pico 2（RP2350）で実現する場合の検討結果

数値は一次資料（RP2350 Datasheet Release 8 など）のものだが、構成と判断は調査者の推論で、試作による実証はまだない。

#### 構成案（未確認（推論））

| 構成 | 内容 | 長所 | 短所 |
|---|---|---|---|
| 案 A: RP2350B（48 GPIO）1 個 | 38〜41 本を使い 7〜10 本余る。PIO 12 SM のうち 8〜9 SM、命令は 96 のうち 60 前後 | 最も素直。余りを重ね表示や 4-4-4 RGB に回せる | QFN-80（0.4 mm）で手はんだは無理。JLCPCB の Extended 実装が前提。外部 21.47727 MHz 発振器を XIN に入れる構成も可能 |
| 案 B: Pico 2 ×2 | Pico A = クロック・リセット・映像（EXT、比較器、RGB、CSYNC）。Pico B = バスの盗聴と置き換え、パッド応答、JAMMA の入出力 | Pico 2 モジュール（秋月）で組める。マイコン自体を基板実装に頼らない（ただし周辺の 74HC165 は Preferred Extended。2.6 の端子数の表） | A と B のクロック領域が違う。B から A へのイベント（パレット書き込み、$2001 の変化）は SPI/UART などで送り、A が受信時刻のドット位置で当てる（$2001 を画面の途中で変えると数十画素ずれ得る）。B の置き換え判断は B の中で完結するので、PPU への改変のタイミングは影響を受けない |

#### 端子数（実チップモードの GPIO 内訳、未確認（推論））

| 群 | 信号 | 本数 | 5 V 入力（FT 必須） | 備考 |
|---|---|---|---|---|
| バスの盗聴と置き換え | PPU 側 D0-D7 | 8 | ○ | 双方向。パッド応答と共用 |
| | A0-A2、R/W、PPU /CS | 5 | ○ | |
| パッド応答 | /OE1、/OE2、OUT0 | 3 | ○ | RP2350 が PPU 側 D0（必要なら D1-D4）を抵抗経由で CPU バスへ出す。M2 は不要（クロックを自前で持つので位相が既知） |
| 映像入力 | EXT0-3 | 4 | ○ | |
| | SPR（比較器） | 1 | — | |
| | （任意）ALE | 1 | ○ | 位相の自己確認 |
| | （任意）同期の比較器 | 1 | — | |
| クロック・リセット | CLK（CPU/PPU を別ピンにするなら 2） | 1〜2 | — | |
| | PPU /RST、CPU /RST | 2 | — | 3.3 V で駆動（VIH は TTL と仮定、要検証）。CPU /RST を RC と兼用すれば 1 |
| 映像出力 | RGB 3-3-3 | 9 | — | FT でないピンでよい |
| | CSYNC | 1 | — | 外付け NPN で 5 V に |
| JAMMA 入力 | 74HC165 ×4（UDLR, A, B, Start ×2P = 14、Coin1/2・Service・Test = 4、DIP 8 → 26 入力） | 3 | — | 165 を 3.3 V で給電、プルアップも 3.3 V。74HC165（C5613）は Preferred Extended で、Basic のシフトレジスタは 74HC595 だけ |
| JAMMA 出力 | 74HC595（Basic）でコインカウンタ ×2・ロックアウトなど（CLK は 165 と共用） | 2 | — | ULN2003A（Basic）で駆動 |
| 書き換え | USB | 0 | — | 専用ピン |
| **合計** | | **最小 37 ／推奨 40〜41** | FT 必須 21〜22 本 | |

| 選択肢 | 使える GPIO | 判定 |
|---|---|---|
| Pico 2 ×1 | 26（FT 23） | **不足**（最小 37）。RGB を 2-2-2 にし任意の信号を全部削っても 33 本で足りない |
| Pico 2 ×2 | 52（FT 46） | **可**。A: CLK 2、/RST 2、EXT 4、SPR 1、ALE 1、RGB 9、CSYNC 1、リンク 3 = 23。B: D 8、A0-2/RW/CS 5、/OE1/OE2/OUT0 3、JAMMA 5、リンク 3 = 24（FT 16） |
| RP2350B ×1 | 48（FT 40） | **最も素直**。7〜11 本余る。ただし QFN-80 の実装を JLCPCB（Extended）に頼る |

- 新規開発カートからの切り替えで OUT1・OUT2 を読むと、Pico B は 24 本から 26 本（FT 18 本）になり、Pico 2 の 26 本を使い切る（推論）。
- DAC を 4-4-4 にすると Pico A は 23 本から 26 本になり、余りがなくなる（推論）。

#### クロックの作り方

12 MHz を基準に整数分周で作れる候補（未確認（推論・計算））:

| PLL 設定 | clk_sys | PIO 分周 k | 出力 | 誤差 | 備考 |
|---|---|---|---|---|---|
| FBDIV=129、VCO 1548 MHz、POSTDIV 6×2 | 129.000 MHz | 6 | 21.500000 MHz | **+1058 ppm** | 推奨（VCO が高めでジッタが小さい、デューティ 50%） |
| FBDIV=86、VCO 1032 MHz、POSTDIV 4×2 | 129.000 MHz | 6 | 21.500000 MHz | +1058 ppm | 同上（VCO 低め） |
| FBDIV=125、VCO 1500 MHz、POSTDIV 5×2 | 150.000 MHz | 7 | 21.428571 MHz | −2268 ppm | 公称最大クロック。デューティ 4:3 |
| FBDIV=113、VCO 1356 MHz、POSTDIV 3×3 | 150.667 MHz | 7 | 21.523810 MHz | +2167 ppm | 150 MHz 超（規格外） |
| FBDIV=93、POSTDIV 2×2 | 279 MHz | 13 | 21.461538 MHz | −733 ppm | 規格外（オーバークロック必須） |

他の方式との比較（未確認（推論））:

| 方式 | 周波数精度 | ジッタ | 部品 | RP2350 との関係 | 判定 |
|---|---|---|---|---|---|
| ① RP2350 PIO の整数分周（129 MHz÷6） | +1058 ppm（水晶誤差 ±30 ppm を含めても 1.1×10⁻³） | PLL のジッタのみ（値は未確認） | 0（直列抵抗のみ） | 完全に同期 | **推奨** |
| ② RP2350 の分数分周 | 平均 0 ppm | 6.7〜7.8 ns の周期ジッタ | 0 | 同期 | 不採用 |
| ③ 74HC04（Preferred）と 21.47727 MHz 水晶のピアース発振 | 水晶の精度（数十 ppm） | 低 | 水晶 C5289705（Extended、在庫 2,648）、C×2、R×2、74HC04 | 非同期（同期器で ±1 clk_sys = ±6.7 ns 揺れる） | 可。ただし発振用途はアンバッファの 74HCU04 が定石で、74HC04 は要評価（JLCPCB の 74HCU04 は SN74HCU04N 79 個のみで実質在庫なし。秋月に TC74HCU04AP（DIP）¥30） |
| ④ 発振器モジュール（SG-8002 など 21.47727 MHz） | ±50 ppm 程度 | 低 | モジュール 1（Basic 外） | 非同期。自作 RP2350 基板なら XIN に入れて PLL で ×6 = 128.86 MHz に同期 | 案 A なら有力。USB ブートは 12 MHz 前提なので OTP の設定か別系統が要る。×7 = 150.34 MHz は公称最大 150 MHz を 0.23% 超える |
| ⑤ Si5351A モジュール（秋月 ¥650） | 実用上ほぼ 0 ppm | 未確認 | モジュールと I²C | 非同期（Pico 2）、自作基板なら XIN へ | 珍しい部品寄り。①で足りるので不要 |

#### 5V 信号との接続（未確認（推論））

| 信号 | 方向 | 接続 | 理由 |
|---|---|---|---|
| A0-2、R/W、/CS、/OE1、/OE2、OUT0、EXT0-3、ALE | 5 V → RP2350 | FT ピンに直結、保護に直列 1 kΩ | VOH 4 V < 5.5 V、VIH 2 V を満たす |
| EXT0-3 | 同上 | 1 kΩ 直列 + 10 kΩ プルダウン | 入力モードのとき backdrop = 0 を保証（TinyNES と同じ 10k） |
| PPU 側 D0-D7 | 双方向 | FT に直結（CPU 側とは 470 Ω で分ける） | 置き換え時に 3.3 V で駆動 |
| CPU/PPU CLK | RP2350 → 5 V | 直結 + 30〜33 Ω | TinyNES の前例 |
| PPU /RST、CPU /RST | RP2350 → 5 V | 直結（Low に保つため外付けプルダウン 10 kΩ） | 入力しきい値は TTL と仮定（要確認）。RP2350 の起動前も Low |
| CSYNC | RP2350 → JAMMA | NPN + 5 V プルアップ（反転） | 3.3 V では TTL High 3.5 V 推奨を満たさない |
| RGB | RP2350 → DAC | 抵抗 DAC へ直出し | 5 V 不要 |
| 74HC165/595 | 3.3 V 給電 | 直結 | 3.3 V のロジック同士 |
| 比較器（ADCMP600 など） | 3.3 V 給電 | 出力を RP2350 に直結 | 入力は PPU VOUT（〜2 V 程度） |

- 電源投入時、Pico の 3V3 が立つ前に 5 V 側の High が FT ピン（5 V 耐性ピン）に 3.63 V 超をかける危険がある。Pico の 3V3 を検出して P-MOS（SI2301 / AO3401A、Basic）で CPU/PPU/カートの 5 V を入れ、FT ピンに直列 1 kΩ を入れる（推論）。

#### 画面への重ね表示（未確認（推論））

- 1 ライン遅延のラインバッファ方式なら、出力前のバッファに文字を書くだけで重ね表示ができ、追加のハードウェアは要らない。
- コストはフォント（8×8 で 96 文字 ≈ 768 B）と、文字のあるラインで 300〜1,000 サイクル程度。変換（≈ 3,100 サイクル）と合わせても 1 ラインの予算 8,190 サイクルに収まる。
- 半透明（下地を暗くして文字を載せる）も表引きでできる。ゲーム画面全体を止めて「INSERT COIN」画面を出すこともできる。
- PPU には何も書かないので、ゲームへの影響はない。
- ラインバッファなしでも、出力直前に文字マスクを OR すればできるが、締め切りが 1 画素単位になって厳しい。
- 出力性能の根拠: PIO は「PIO can sustain 360 Mb/s during the active scanline period when running from a 48 MHz system clock」（確認済、データシート）。RP2350 で 2C02 の映像に重ね表示した前例は見つからない。

#### 推奨構成のまとめ（推論）

| 項目 | 推奨 | 主な理由 | 主なリスク |
|---|---|---|---|
| RGB の方式 | EXT 方式（ドナー機の 2C02） | 規則に合い、重ね表示ができる | 前例がない |
| マイコン | Pico 2 ×2（A: クロック・リセット・映像、B: バス・入出力） | 秋月の完成品で、マイコンは Basic 外の実装を要しない | クロック領域が 2 つ。Pico B は OUT1・OUT2 を読むと GPIO の余りがない |
| クロック | Pico A の PIO が 21.5 MHz（129 MHz ÷6、+1058 ppm）を出す | 完全に同期し、1 画素ずれが消える。水晶が要らない | NMOS が 3.3 V 駆動を受けるか（実験 2） |
| PPU /RST | Pico A がクロックに合わせて解除。10 kΩ プルダウン | 位相が毎回同じ | 内部同期段の有無（実験 6） |
| パレットの改変 | 470 Ω の直列抵抗（0603 単品 C23179 ×8、Basic。アレイ C25510 ×2 は Preferred Extended）で PPU 側を置き換え | 部品最少、Basic | 置き換えの確実さ（実験 2・3） |
| PPU に書く値 | BG = $0F、スプライト = $20。強調・グレースケールは 0 に置き換え | 比較器 1 個で済む | 色番号の妥当性は実測で確認 |
| 第5ビットの比較器 | ディスクリート → LM319 → ADCMP600 の順に評価 | 規則に収まるものを優先 | 最大のリスク（実験 1） |
| 同期 | PIO のカウンタで生成し、NPN で 5 V の負極性 CSYNC に。VOUT の同期を LM393 で取って照合（任意） | 部品最少 | ドットスキップの判定タイミング |
| DAC | 4-4-4 以上の重み付け抵抗。開放 3.0 V、100〜150 Ω | 将来の色数向上 | Pico A の GPIO に余りがない |
| 重ね表示 | ラインバッファに文字を書く | 残り時間、INSERT COIN、設定画面 | なし（ソフトのみ） |
| ソケット | RGB 出力版 PPU との両対応（pin14〜17、21、12 のジャンパ） | 将来の差し替え | pin17 を GND に直結しないこと |
| パレット | pally（MIT-0）で 2C02G の 512 色を生成。2C03 の表も選べる | 権利の面で安全 | なし |

### 2.7 リスクと確認実験の順序（未確認（推論））

| 順位 | リスク | 最小の実験（作るもの） | 測るもの | Go / No-go |
|---|---|---|---|---|
| 1 | **スプライト/BG の判定**（Basic/Preferred に高速な比較器がない。LM393 は 300 ns 以上で不可） | 2C02 を載せた小基板と Pico 2（クロック、/RST、EXT、比較器入力）。テスト ROM で「BG=$0F、スプライト=$20」の固定パレット、1 画素幅・2 画素幅のスプライトの縦線を表示。比較器を (i) ADCMP600、(ii) LM319（5 V 単電源）、(iii) PNP フォロワ + 74HC14 か RP2350 入力直、の 3 通りで差し替え | RP2350 の PIO をロジアナにして 129 MHz（7.75 ns）で EXT と比較器の出力を同時に取る。1 画素のスプライトの比較器パルスの幅と位置、立ち上がりと立ち下がりの遅延差、ノイズ（タンタル C の有無） | Go: 1 画素幅が常に検出でき、標本点の前後に 40 ns 以上の余裕があり、10 回の電源投入と 2 種類以上の 2C02（例: RP2C02E/G）で同じ位相。No-go: (iii)(ii) が不可なら (i) を採用（¥830/台）、(i) も不可なら方式を見直す |
| 2 | **3.3 V 駆動で NMOS の入力が動くか**（D6/D0-5 の置き換え、CLK、/RST） | 実験 1 と同じ基板。CLK は RP2350 から 21.5 MHz（30 Ω 直列）、CPU も同じクロックで動かす | 数時間の連続動作、CLK の波形（ピン端）、$2000 D6 を 3.3 V で強制して EXT が出力モードになるか、パレット置き換え後に $2007 読み出し（2C02G）で値を確認 | Go: 0〜50 °C で誤動作なし、置き換え値の読み戻しが一致。No-go: 74HCT245/LVC4245A（5 V 出力）に切り替え（D2） |
| 3 | **直列抵抗インタポーザの副作用**（CPU 側の電圧、PPU 読み出しの遅れ、MMC5 の盗聴） | 実験 2 の基板に WRAM を載せ、通常のカートと MMC5 のカートで動かす | CPU 側と PPU 側の D 線の波形、$2002 読み出しの立ち上がり（τ）、置き換え時の CPU 側の Low レベル、WRAM テスト | Go: CPU 側 VOL ≤ 0.8 V、PPU 読み出しのデータが M2 立ち下がりの 50 ns 前までに安定。No-go: 抵抗値の変更（330 Ω など）か D2 |
| 4 | **v/w 追跡の正しさ**（レンダリング中の $2007、RMW・DMC による 1 サイクル間隔のアクセス） | ソフトのみ: エミュレータ（Mesen など）の PPU レジスタアクセスのログと内部の v を多数のタイトルで記録し、追跡アルゴリズムと照合 | パレット書き込み時に追跡した v が実際の v と違う件数 | Go: 違いが既知の例外（Codemasters など）に限られる |
| 5 | **コアの更新遅延**（次の $2007 の置き換え値が間に合うか） | Pico 2 を 2 枚使い、1 枚で 2A03 のバス波形（/CS、R/W、A、D）を擬似生成、もう 1 枚で SNOOP/SUBST を動かす | 連続する $2007 アクセスの間隔 1/2/4 サイクルでの置き換えの成功率 | Go: 2 サイクル間隔以上で 100% |
| 6 | **EXT と VOUT の相対遅延・1 画素ずれ** | 実験 1 の基板で /RST をクロックに合わせて解除 | 20 回の電源投入で、EXT とスプライトビットの最適なずらし量が変わらないか。ALE の位相 | Go: 毎回同じ（または ALE から自動判定できる） |
| 7 | **電源の順序**（FT ピンの 3.63 V 制限） | Pico 2 の VSYS 投入から 3V3 確立までの時間と、その間の 5 V 側の信号を同時に測る | FT ピンの電圧・電流 | Go: P-MOS の遅延投入で、3V3 確立前の 5 V 信号が 0 |
| 8 | **GPIO 不足**（Pico 2 ×1 では不可） | 机上でピン割り当て表と PIO の命令数を確定 | — | 案 A（RP2350B）か案 B（Pico 2 ×2）を確定 |
| 9 | **クロック +1058 ppm の影響** | 実験 1〜3 の基板で実際のゲーム数本 | モニタの同期（15.762 kHz）、音程 | 低リスク。Go: モニタが同期する |
| 10 | **パレット読み出しを使うソフト** | 対象タイトルの調査（エミュレータで $2007 のパレット読み出しを検出） | 該当タイトル数 | 該当がなければ対策不要 |

実験 1〜3 と 6 は「ドナー機の CPU/PPU と Pico 2 1 枚、ブレッドボード級の試作」で 1〜2 週間程度で go/no-go を出せると見込まれる。

## 3. 選択肢の比較

### 3.1 RGB を得る方式

| 選択肢 | かかるもの | リスク | 判定 |
|---|---|---|---|
| EXT 方式を Pico 2 と汎用部品で作る | 低コスト。秋月の Pico 2、汎用ロジック、抵抗 | 高い。前例がなく、バス介入のタイミング、GPIO 不足、5V レベル、比較器が課題 | **採用（推論）** |
| EXT 方式を小型 CPLD/FPGA で作る | 中コスト | 中（実績あり）。ただし CPLD/FPGA は避ける方針に反する | 不採用 |
| RGB 出力版 PPU に交換 | 1 個 110〜260 USD、中古のみで品切れ | 技術リスクは低い（バッファと同期の整形だけ） | 量産不可。将来の差し替え用にソケットの両対応だけ残す |
| コンポジット出力の解読（高速標本化、または NTSC デコーダ IC） | 高速 ADC と FPGA、または入手性未確認の IC | 高（標本化）、画質が劣る（デコーダ） | 不採用 |
| バス傍受で PPU を作り直す、または PPU を FPGA で置き換える | FPGA | 中〜高。MMC5 などで不具合の報告。置き換えは実機の 2C02 を使う前提から外れる | 不採用 |

### 3.2 マイコンの構成

| 選択肢 | かかるもの | リスク | 判定 |
|---|---|---|---|
| Pico 2 ×1 | 1 枚（秋月 ¥990） | GPIO 26 本で最小 37 本に足りない | 不可 |
| Pico 2 ×2（A: クロック・リセット・映像、B: バス・入出力） | 2 枚。マイコン自体は基板実装に頼らない | クロック領域が 2 つになり、$2001 を画面の途中で変えると数十画素ずれ得る。B は OUT1・OUT2 を読むと余りがない | **試作 1 回目に採用（推論）** |
| RP2350B ×1 | QFN-80 を JLCPCB の Extended で実装 | 手はんだ不可。「Basic のみ」から外れる | 量産で Extended を許すなら移行先 |

### 3.3 PPU のパレットを「BG 暗・スプライト明」に保つ回路

| 選択肢 | かかるもの | リスク | 判定 |
|---|---|---|---|
| 470 Ω 直列抵抗 ×8 | 0603 単品 C23179 ×8（Basic）。アレイ C25510 は Preferred Extended | 2C02 が 3.3 V を High と受けるか、衝突電流（約 7 mA/本）、PPU 読み出しの遅れ | **第一候補** |
| 74HC245 を挟む | 74HCT245（Extended）または SN74LVC4245A（Preferred）が必要 | 3.3 V 駆動の問題は残る。方向切り替えが要る | 予備 |
| /CS を遮断する | 74HC08 など 1 個 | PPU 内の v がずれる。$2000 bit6 の強制ができない | 不成立 |
| 独自の書き込みを挿入 | 抵抗かバッファ | 複雑で、PPU の v/w を余計に動かす | 不採用 |
| 改変せずに第5ビットを推定 | 多値の比較器 | 同じ明るさで色相が違うと区別できない | 不完全 |

### 3.4 第5ビット用の比較器

| 選択肢 | かかるもの | リスク | 判定 |
|---|---|---|---|
| ディスクリート（PNP エミッタフォロワ S8550 / MMBT3906 と分圧、RP2350 入力か 74HC14） | 最も安い。Basic の部品で済む | 最も不確か | 最初に評価 |
| LM319（秋月 LM319M 5 個 ¥50） | 安い | オープンコレクタ出力の立ち上がりが RC で決まり、遅延差の実測が要る。パッケージは未確認 | 2 番目に評価 |
| ADCMP600（秋月 ¥830、SOT23-5） | 1 台 ¥830 | 小さく手はんだ向きでない | 上 2 つが不可なら採用 |
| LM393 | Basic/Preferred で唯一 | 1.3 µs / 300 ns で画素幅に間に合わない | 第5ビットには使えない。同期の照合用なら可 |

### 3.5 クロック

| 選択肢 | かかるもの | リスク | 判定 |
|---|---|---|---|
| RP2350 PIO の整数分周（129 MHz ÷ 6 = 21.5 MHz） | 直列抵抗のみ | +1058 ppm。NMOS が 3.3 V 駆動を受けるか未確認。RP2350 が止まると CPU/PPU も止まる | **推奨** |
| RP2350 の分数分周 | なし | 6.7〜7.8 ns の周期ジッタ | 不採用 |
| 74HC04 と 21.47727 MHz 水晶 | 水晶 C5289705（Extended）ほか | マイコンと非同期で ±6.7 ns 揺れる。発振には 74HCU04 が定石 | 可 |
| 発振器モジュール | Basic 外のモジュール | 非同期（自作 RP2350 基板なら同期できる） | 案 A なら有力 |
| Si5351A モジュール（秋月 ¥650） | モジュールと I²C | 珍しい部品寄り | 不要 |

### 3.6 同期信号の作り方

| 選択肢 | かかるもの | リスク | 判定 |
|---|---|---|---|
| RP2350 の PIO カウンタで生成 | 追加部品なし | 奇数フレーム短縮の判定タイミングを誤ると 1 ドット揺れる（蓄積はしない） | **主（推論）** |
| VOUT から比較器で取り出す | 比較器 1 回路（LM393 でも可）と配線 | ほぼなし。ドットスキップとリセットに自動で追従 | 照合用（任意） |
| 341 ドット固定で出力 | ラインバッファ | ドットスキップのジッタは消えるが、ラインバッファが前提 | 参考 |

## 4. ユーザー要求ごとの判断

この節の判断はすべて推論である。

| 要求 | 判定 | 理由 | 推奨 |
|---|---|---|---|
| 部品は Basic Parts のみ、PCBA は LCSC 在庫、手はんだは秋月 | 条件つきでできる | データバス介入は 0603 単品 470 Ω ×8（Basic）で、クロックも RP2350 が作るので水晶は要らない。規則と衝突するのは高速な比較器だけである | 試作でディスクリート → LM319 → ADCMP600 の順に評価する。どれも通らなければ手はんだか Extended 実装をユーザーが決める |
| 部品の種類・点数を減らす、安価に | 条件つきでできる | 抵抗アレイ C25510 を使うと種類は減るが Preferred Extended になる。重ね表示や設定画面に追加部品が要らない点は有利 | 単品抵抗で Basic を守る |
| CPU と PPU だけを移植する（実チップモード） | 条件つきでできる | ドナー機の 2C02 を EXT 方式で使うが、比較器と 3.3 V 駆動の実験が通ることが条件である | EXT 方式、Pico 2 ×2 |
| Raspberry Pi 等でエミュレートし、ソケットで選ぶ | 未確定 | RGB と CSYNC の出力段を 1 組にまとめ、駆動するマイコンを 1 枚に決めると部品が減るが、エミュレーション側の GPIO と処理能力は未検討である。PPU の有無は ALE を見て自動判定できる可能性がある | 出力段を共用し、Pico A が担当する案を検討する |
| ファームウェアの更新を USB で簡単に | 条件つきでできる | 映像用マイコンを書き換えると CPU/PPU のクロックが止まるが、/RST を外付けプルダウンで Low に保てば安全である | Pico B が Type-C につながり Pico A を書き換える順にする |
| タイマー方式（残り時間の表示、時間切れ後の扱い） | できる | 残り時間と予告、INSERT COIN を重ね表示で描け、時間切れ後は画面全体を INSERT COIN 画面に差し替えられる。ゲームのリセットはしない | Pico B が時間を数え、表示内容を Pico A へ送る |
| 通常方式のデフォルト形式・特殊形式 | できる | 入力形式の変換はパッド応答側（Pico B）の仕事で映像には関係しない。C・D ボタンを読む分はシフトレジスタで吸収でき、GPIO は増えない | Pico B で処理 |
| 切り替えはソフトウェアで（設定画面、カートからの切り替え） | 条件つきでできる | 設定画面は重ね表示で描ける。カートからの OUT1・OUT2 を読むと Pico B の GPIO を使い切る | Pico B で OUT1・OUT2 を読み、設定の変化を Pico A へ知らせる |
| マイコンは何枚でもよい | できる | 複数枚を認める要求で、Pico 2 ×2 が規則の中で取れる構成になった（ただし 74HC165 と Type-C 端子は Basic 外として残る） | Pico 2 ×2 |
| CPU・PPU・メモリの将来の更新、DA 変換のビット数に余裕 | 条件つきでできる | DAC を 4-4-4 にすると Pico A の余りがなくなる。PPU ソケットは RGB 出力版 PPU との両対応を 0Ω ジャンパと数本の配線で残せる。別の CPU に替えるときはクロック（3.3 V、21.5 MHz）を受けられるかの確認が要る | DAC 4-4-4 以上、ソケット両対応、EXT0-3・VOUT・CLK・/RST を拡張コネクタへ引き出す |
| USB Type-C でファームウェア更新 | 条件つきでできる | Pico 2 の USB は Micro-B で、信号は端子列に出ていない。Type-C 端子 C393939 は Extended で、Basic に USB コネクタはない | 要求 6.2 の 3 案から選び、Type-C は 1 つにまとめる |

## 5. ユーザーに決めてもらうこと、次に確かめること

### 5.1 ユーザーに決めてもらうこと

| 決めること | 推奨する既定 |
|---|---|
| 試作でディスクリートと LM319 がどちらも不可だった場合の比較器 | ADCMP600 を手はんだ（¥830/台）。基板実装にこだわるなら高速比較器だけ Extended を許す |
| 74HC165 など Preferred Extended の部品を許すか | 許す（許さない場合は 74HC595 と組んだ別の読み方が要る） |
| マイコン構成 | 試作は Pico 2 ×2。量産で Extended を許すなら RP2350B ×1 への移行を検討 |
| DAC のビット数 | 4-4-4 以上（3-3-3 は 2C03 の値をそのまま出せるが、2C02 風のパレットには粗い） |
| 画面の左右のボーダー（backdrop 色）を出すか | シートは判断を示していない（仕様の判断） |
| 内蔵するパレット | pally で生成した 2C02G の 512 色。2C03 の表も選べるようにする |
| PPU ソケットを RGB 出力版 PPU と両対応にするか | 両対応にする（0Ω ジャンパと数本の配線のみ） |
| タイマー方式の時間切れ後の画面 | 画面全体を INSERT COIN 画面に差し替える（ゲームはリセットしない） |

### 5.2 次に確かめること（順序どおり）

1. スプライト/BG の判定。2C02 を載せた小基板と Pico 2 で、比較器をディスクリート、LM319、ADCMP600 の 3 通りに差し替える。これが決まらないと方式全体が決まらないので最初に行う。
2. 3.3 V 駆動で NMOS の CPU・PPU の入力（D 線、CLK、/RST）が動くか。
3. 470 Ω 直列抵抗の副作用（WRAM と MMC5 のカートで確認）。
4. 内部状態（v/w）の追跡が正しいか（エミュレータのログでオフライン照合）。
5. マイコン内の更新が次の $2007 アクセスに間に合うか（Pico 2 を 2 枚使った擬似バス）。
6. EXT と VOUT の相対遅延と 1 画素ずれ（20 回の電源投入）。
7. 電源の順序（3V3 が立つ前に 5 V 信号が FT ピンにかからないか）。
8. GPIO の割り当てと PIO の命令数を机上で確定する。
9. クロック +1058 ppm の影響（モニタの同期と音程）。
10. パレットの読み出しを使うソフトの調査。

1〜3 と 6 は同じ試作基板で行え、1〜2 週間程度で go/no-go を出せると見込まれる。

## 6. 主要出典

### 1 章（結論）と 2.1（方式の比較）

- NESdev Wiki: PPU pinout（RGB 出力版 PPU のピン、/RST、VOUT 増幅）— https://www.nesdev.org/wiki/PPU_pinout
- NESRGB 公式ページ（EXT 方式の動作原理）— https://etim.net.au/nesrgb/
- tall-dog（RGB 出力版 PPU の価格と在庫、Sold Out）— https://shop.tall-dog.com/products/rgb-format-nes-core-ppu-chip
- Arcade-Museum WTB: RP2C03 PPU（RGB 出力版 PPU の相場）— https://forums.arcade-museum.com/threads/wtb-rp2c03-ppu.506933/

### 2.2（EXT 端子と追跡する内部状態）

- NESdev Wiki: PPU registers（$2000 bit6、損傷の警告、パレット読み出し）— https://www.nesdev.org/wiki/PPU_registers
- NESdev Wiki: PPU programmer reference — https://www.nesdev.org/wiki/PPU_programmer_reference
- Breaking NES Wiki: Multiplexer（EXT が出る内部位置）— https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/mux.md
- NESdev forum t=9561 p.4（viletim による改変パレットの説明）— https://forums.nesdev.org/viewtopic.php?t=9561&start=45

### 2.3（既存製品）

- lava-rgb-kit（Lava RGB の回路図・BOM・ファーム）— https://github.com/v5100v5100/lava-rgb-kit
- NESdev forum t=25963（Lava RGB の動作と既知の不具合）— https://forums.nesdev.org/viewtopic.php?t=25963
- Hi-Def NES スレッド アーカイブ — https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- TinyNES Main Board Schematic（EXT のプルダウン、3.3 V クロック駆動）— https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf
- NESdev forum t=26258（PPU-LITE、1 画素ずれ、RGB2C02N の不具合）— https://forums.nesdev.org/viewtopic.php?t=26258

### 2.4（比較器）

- TI LM393（応答時間）— https://www.ti.com/lit/ds/symlink/lm393.pdf
- TI LM119/LM319 — https://www.ti.com/lit/ds/symlink/lm119.pdf
- 秋月 130362（ADCMP600BRJZ-R2）— https://akizukidenshi.com/catalog/g/g130362/

### 2.5（映像タイミング）

- NESdev Wiki: NTSC video（出力レベル、水平・垂直の区間、強調の係数）— https://www.nesdev.org/wiki/NTSC_video
- NESdev Wiki: PPU frame timing（奇数フレームの短縮）— https://www.nesdev.org/wiki/PPU_frame_timing

### 2.6〜2.7（Pico 2 での実現）と 4 章

- RP2350 Datasheet（PIO、PLL、5V 耐性、電気特性）— https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet（GPIO 26 本、12 MHz 水晶）— https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- Raspberry Pi news「RP2350 A4, RP2354 and a new hacking challenge」（5V 耐性の公式化）— https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/
- 秋月 129604（Raspberry Pi Pico 2）— https://akizukidenshi.com/catalog/g/g129604/
- Blast City Bass Fishing 版取説（JAMMA 側 2kΩ / 3.0Vp-p）— https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf
- pally LICENSE（MIT No Attribution）— https://raw.githubusercontent.com/Gumball2415/pally/main/LICENSE
