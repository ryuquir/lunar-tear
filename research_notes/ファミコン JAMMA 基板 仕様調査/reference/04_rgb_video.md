# RP2C02 からアナログ RGB 映像を得る方法 - リファレンスシート

- **推奨は「EXT 方式」である。** ドナー機の RP2C02 をそのまま使い、PPU の EXT 端子からパレット番号を読む。マイコンがパレットの複製を持って RGB を作り直す。RGB 出力版 PPU は中古しかなく、1 個 110〜260 USD と高く品切れなので、量産の前提にはできない。
- **マイコン 1 枚では端子が足りない。** 実チップで動かす場合は最小 37 本、推奨 40 本前後の GPIO が要り、Pico 2（26 本）1 枚では収まらない。マイコンを何枚使ってもよいという現行の要求により、Pico 2 を 2 枚にする構成（映像・クロック用と、バス・入出力用）が部品の規則の中で取れる。RP2350B を 1 個載せる構成もあるが、Extended 部品になる。
- **クロックと PPU の /RST（pin22）はマイコンが握る。** 映像側の RP2350 が 21.5 MHz（+1058 ppm）を出し、PPU /RST をクロックに合わせて解除する。こうすると、既存の EXT 方式の製品で起きる「電源投入ごとに 1 画素ずれる」問題が原理的に起きなくなる（推論）。
- **最大のリスクは、スプライトと背景を見分ける高速な比較器である。** JLCPCB の Basic/Preferred にある比較器は LM393 だけで、画素幅（186 ns）に間に合わない。秋月の ADCMP600（¥830）を手はんだで使うか、LM319 やトランジスタで作る回路が使えるかを、最初の試作で決める必要がある。
- **映像をマイコンが作り直すので、残り時間・INSERT COIN・設定画面は追加部品なしで重ねて描ける**（推論）。CPU と PPU の間には 470 Ω の直列抵抗を入れ、PPU 側のデータ線をマイコンが書き換える。

データの日付: 2026-11-10

---

## 1. 確定事実

確度の表記は次の 3 つである。

- **確認済**: 2 つ以上の独立した出典、またはネットリスト・データシート・実物のデータで確かめたもの。
- **単一出典**: 出典が 1 つだけのもの。
- **未確認**: 出典が見つからないもの。調査者の計算や判断は「未確認（推論）」と書く。

用語は次のとおりとする。

- **EXT 端子**: RP2C02 の pin14〜17（EXT0〜EXT3）。
- **EXT 方式**: PPU に EXT 端子からパレット番号を出させて RGB を作る方式。NESRGB 方式、slave 方式とも呼ばれる。
- **第5ビット**: パレット番号の bit4。0 が背景（BG）、1 がスプライトを表す。EXT には出てこない。
- **シャドウパレット**: CPU が PPU に書くパレットの値を、外部回路が盗み見て保持する複製。
- **VOUT**: PPU pin21 のコンポジット映像出力。
- **マスタークロック**: 21.47727 MHz のクロック。PPU はこれを 4 分周して画素クロック（PCLK）を作り、CPU は 12 分周して M2 を作る。

### 1.1 RGB を得る方式の一覧と比較

| 方式 | 仕組み | 実績のある例 | 部品・規則への適合 | 技術リスク | 画質 | 確度 |
|---|---|---|---|---|---|---|
| A. RGB 出力版 PPU に交換 | RP2C03B、RC2C03B/C、RC2C05-xx などを同じ DIP-40 ソケットに挿す。R/G/B と /SYNC が直接出る | VS. System、PlayChoice-10、Sharp C1、Famicom Titler。TinyNES の RGB キット | ×（中古のみ。1 個 110〜260 USD、品切れ） | 低（バッファと同期の整形だけ） | 良（パレットは 2C03 固定。強調の挙動が 2C02 と違う） | 確認済 |
| B. EXT 方式（EXT 端子とシャドウパレット） | $2000 の bit6 を立てて EXT にパレット番号の下位 4bit を出させる。パレットへの書き込みは盗聴して複製し、PPU には「BG は暗い色、スプライトは明るい色」に書き換えた値を渡す。第5ビット・ブランキング・同期は VOUT から比較器で取り出す | NESRGB（CPLD のち FPGA）、Lava RGB（Lattice FPGA）、Hi-Def NES（FPGA） | CPLD や FPGA で作れば規則外。RP2350 の PIO で作れば ◎ だが前例がない | 中（CPLD/FPGA）／高（マイコン） | 良（既知の制約あり。1.2 節参照） | 確認済（方式と製品）／マイコンでの実装は未確認 |
| C. コンポジット出力の解読 | (C1) VOUT を 42.95 MHz（画素あたり 8 回）で標本化して色番号を復元する。(C2) アナログの NTSC デコーダ IC で RGB にする | C1 は lidnariq が「oversampling VIDEO_OUT」と言及しただけで、実装例は見つからない。C2 は具体例が見つからない | ×（C1 は高速 ADC か多数の高速比較器と FPGA が要る）／△（C2 は IC の入手性が未確認） | 高（C1）／低〜中（C2） | C1 は理論上良。C2 はドットクロールと色にじみで劣る | 単一出典（C1 の言及）／未確認（性能） |
| D. PPU のバスを盗聴して PPU を作り直す | カートリッジ端子の PPU バスと CPU による OAM への書き込みを追い、FPGA の中で PPU を再実装する | RGB Blaster（Krikzz）、PPUdigitizer（c0pperdragon、受動的な盗聴で LumaCode を出す。内部方式は非公開で、D に分類するのは「passively listen」の一文に基づく推論） | ×（FPGA） | 中〜高（PPU の品種やタイミングに敏感。MMC5 などで不具合） | 良 | 単一出典（PPUdigitizer の分類は未確認（推論）） |
| E. PPU 自体を置き換える | FPGA で作った PPU を RP2C02 の代わりに挿す | PPU-LITE（andkorzh）、RGB2C02N Rev.3.2（税込 17,980 円。価格は検索要約経由で本文未精読） | ×（FPGA。実機の 2C02 を使う前提から外れる） | 中（RGB2C02N は MMC3 のゲーム 3 本が壊れるとの報告） | 良 | 単一出典 |

調査者による順位付け（未確認（推論））は次のとおり。

| 順位 | 方式 | コスト | 部品入手と規則への適合 | 技術リスク |
|---|---|---|---|---|
| 1 | B を Pico 2（RP2350 PIO）と汎用部品で作る | 低 | ◎（秋月の Pico 2、汎用ロジック、抵抗） | 高（前例なし。バス介入のタイミング、GPIO 不足、5V レベル、比較器） |
| 2 | B を小型 CPLD/FPGA で作り直す | 中 | ×（CPLD/FPGA は避ける方針） | 中（実績あり） |
| 3 | A（RGB 出力版 PPU） | 高 | ×（量産不可） | 低 |
| 4 | C1（VOUT の高速標本化） | 中〜高 | × | 高 |
| 5 | C2（アナログ NTSC デコーダ） | 中 | △ | 低〜中（画質は低） |
| 参考 | E（FPGA PPU） | 中〜高 | × | 中 |

- 既存の EXT 方式の製品はすべて CPLD か FPGA で作られている（NESRGB は EPM570T100/EPM240T100、v4 以降は FPGA と補助マイコン。Lava RGB は LCMXO2-1200HC-4TG100I。Hi-Def NES は FPGA）。確認済。
- RP2040/RP2350 で 2C02 の EXT を読んで RGB にした公開例は見つからなかった。近い例は、Pico 2 から 2C02 の EXT0-3 を**入力モード**で駆動して Game Boy の映像を出す構想（SamDelorean/gameboy-rp2c02-crt-adapter）だけである。これはソフトの試作段階で、実機での検証は「future work」とされ、ライセンスは MIT / CERN-OHL-W-2.0 / CC BY-SA 4.0 である。単一出典。

### 1.2 EXT 端子の挙動と、基板側で追跡が必要な PPU 内部状態

#### EXT 端子が出すもの

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

#### 外部回路が真似る必要のある PPU 内部状態

パレットへの書き込みは PPU の外の VRAM バスからは見えない（原文「writing to the internal palette range (3F00-3FFF) will not assert /WR」、確認済）。そのため CPU 側のバスを盗聴して、次の状態を外部で再現する必要がある。

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

#### 既存品が PPU に書く改変パレット

| 項目 | 内容 | 確度 |
|---|---|---|
| NESRGB | 作者 viletim（Tim Worthington）、2013-01-12: 「The PPU instead gets a special palette - the 16 sprite entries are all white and the 16 background entries are all black.」「The fifth pixel bit then plops right out where the video used to be!」。公式: 「Modified data is passed to the PPU」 | 確認済 |
| Lava RGB | krzysiobal、2025-04-15: 「passes modified data to PPU via $2007 when palette range is written」「all background entries got one index and all sprites index got another one」。$2000 書き込みは bit6 を立てて PPU へ渡す | 単一出典 |
| Hi-Def NES | kevtris: 「the nesRGB uses a slightly different set of palette entries from the HidefNES does」。NESRGB と同じ方法で PPU に「lie」させるソルダージャンパがある。Hi-Def NES を付けた機体の RF は「sprites as white on a black background」になるという利用者の報告がある | 単一出典 |
| 具体的な色番号（$0F/$1D/$20/$30 など） | 3 製品とも非公開 | 未確認 |
| 改変の結果 | PPU の元のコンポジット映像は「黒地に白い塊」になる | 確認済 |

### 1.3 スプライトと背景の判別、比較器の速度、候補部品

#### 判別の原理

PPU に「BG は全部暗い平坦な色、スプライトは全部明るい平坦な色」を書くと、VOUT の明るさだけで第5ビットが分かる。2C02 の $x1〜$xC は $xD と $x0 のレベルの間を行き来する方形波（色副搬送波）を出すが、$x0（$00/$10/$20）、$xD、$xE/$xF は平坦な DC レベルなので、比較器 1 個の単純なしきい値で判定できる（確認済：出力レベルは NESdev Wiki。改変パレットの値の選び方は推論）。

#### 2C02 の映像出力レベル（75Ω で終端したとき、mV）

| 信号 | 通常 | 強調時 |
|---|---|---|
| sync | 48 | — |
| burst low | 148 | — |
| $0D | 228 | 192 |
| $1D（黒、blank） | 312 | 256 |
| burst high | 524 | — |
| $2D | 552 | 448 |
| $00 | 616 | 500 |
| $10 | 840 | 676 |
| $3D | 880 | 712 |
| $20（= $30） | 1100 | 896 |

$xE/$xF は $1D と同じ電圧である。単一出典（NESdev Wiki: NTSC video。第1次・第2次の両ノートで取得し、2026-11-10 に原文で全値を再確認。独立した第 2 の出典はない。下の kevtris の実測は測定点が違うので数値の照合には使えない）。

#### kevtris による実測（NES の PPU VOUT につながる増幅トランジスタのエミッタ、絶対電圧 V）

| 項目 | lo | hi |
|---|---|---|
| sync | 0.781 | — |
| black | 1.300 | — |
| C.B.（カラーバースト） | 1.000 | 1.712 |
| L0 | 1.131 | 1.875 |
| L1 | 1.300 | 2.287 |
| L2 | 1.743 | 2.743 |
| L3 | 2.331 | 2.743（強調全ビット時は 2.243 など） |

RCA 75Ω 負荷では「981mv peak to peak (synch to white)」。単一出典（Agilent 54622D による実測）。

- PPU pin21 の直の電圧は、上のエミッタの値から PNP の VBE（約 0.65 V）を引いて、黒が約 0.65 V、白が約 2.1 V、sync が約 0.15 V と推定される。黒と白の差は約 1.4 V で、しきい値は 1.3〜1.5 V 付近になる。未確認（推論。ピン直の実測はない）。
- 黒（312 mV）から白（1100 mV）までの段差は、75Ω 終端時で約 0.79 V ある。比較器の入力の振れ（オーバードライブ）は十分取れる。確認済（値）。
- Lava RGB では比較レベルが 1.92V で、WDL6528（クローン PPU）の多くでスプライトだけ乱れた。R9 を 7.15k から 10k に変えてしきい値を下げると直った。RP2C02G/H と UA6528 では問題はなかった。「ビデオ出力にアンプを繋ぐと動作しなくなる」。単一出典。
- Fiskbit: アナログ映像の BG とスプライトの切り替わりが十分速くないと、スプライトの縁にちらつきや色にじみが出る。単一出典。

#### 比較器に必要な速度

1 画素は 186 ns である。比較器の遅延そのものは、マイコンが標本化する位相を設定すれば吸収できる。大事なのは、遅延の**ばらつき**（入力の振れ方による差、立ち上がりと立ち下がりの差）が画素幅よりも十分小さいことである（未確認（推論））。同期の分離に使う比較器は遅くてよい。

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
- 既存品の比較器: Lava RGB は LMV7219M5X ×1 と TLV3502AIDR ×1 の計 3 回路。回路図のネット名は `VOUT_CS`、`VOUT_BLANK`、`EXT4`。NESRGB v5 は U11 GSV331-TR（代替 MCP6561UT-E/OT）、U12 MX3502S（代替 TLV3502AIDR）、入力バッファ U10 GS8051-TR（代替 OPA356AIDBVR）、映像ドライバ U8 GS8051-TR。確認済（BOM・公式ページ）。
- ネット名からは、Lava の 3 回路は「複合同期」「ブランキング」「第5ビット」に使われていると読める。未確認（推論。配線は未解析）。
- 部品を使わない案としては、kyuusaku「bias the CMOS inputs (or better yet differential inputs) to act as comparators」、lidnariq「an array of 15 trimpots and 15 comparators is awfully hard to screw up」という発言がある。差動トランジスタ対の具体的な回路の文献は見つからなかった。単一出典。
- 部品の判断（未確認（推論））:
  - LM393 と LM339 は使えない。
  - LM311 はオーバードライブによる遅延のばらつきが 50 ns 以上あり、余裕が足りない。
  - LM319 は大きなオーバードライブで実効遅延が短くなる見込みだが、オープンコレクタ出力の立ち上がりが RC で決まる。立ち上がりと立ち下がりの遅延差を実測する必要がある。
  - ディスクリート案は、PNP エミッタフォロワ（S8550 / MMBT3906）で PPU ピンを受け、抵抗分圧で RP2350 の入力しきい値（VIL 0.8 V〜VIH 2.0 V）か 74HC14 に入れる。最も安いが最も不確かである。74HC14 のしきい値は VT+ 1.55〜3.13 V、VT− 0.9〜2.45 V（@4.5 V）、tpd は 12 ns typ / 31 ns max（@4.5 V）。
  - しきい値は PWM と RC、または分圧と半固定抵抗で変えられるようにしておく（Lava の R9 の教訓）。

### 1.4 既存製品・既存設計

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
- 日本の同人基板で 2C02 の EXT を使って RGB 化した例は見つからなかった（日本語の検索で出るのは NESRGB と RGB2C02N の販売記事だけ）。

### 1.5 画素の位置合わせと、リセット端子・クロックとの関係

| 事実 | 内容 | 確度 |
|---|---|---|
| PPU /RST（pin22）の効果 | 「Returns the following to power-on state: Clock divider, Video phase generator, Scanline/pixel counters, Even/odd frame toggle」。PPUCTRL、PPUMASK、PPUSCROLL、読み出しバッファを 1 フレームの間 0 に保つ | 確認済（NESdev Wiki と Breaking NES のダイ解析） |
| リセットの内部動作 | /RES パッドは非同期の「Reset FF」をセットする。RES は H/V カウンタの各ビットの「global reset signal of all sequential PPU circuits」。RES=1 の間は PCLK と /PCLK が固定され、解除後に一定の位相で分周が始まる（シミュレーション由来の波形） | 単一出典（Breaking NES） |
| 電源投入時の分周器 | 「more correct to assume that the value of the latches is undefined (x)」 | 単一出典（Breaking NES） |
| ファミコンの配線 | 「The Famicom ties it to +5V」。ネットリスト 3 種でも pin22 = +5V | 確認済（NESdev Wiki とネットリスト） |
| NES の配線 | 「On the NTSC NES, the PPU and CPU are reset at the exact same time.」ファミコンは PPU /reset が 5V、CPU /reset は 0.47µF のコンデンサにつながる（PPU は CPU より約 1 フレーム早く初期化を始める） | 確認済 |
| リセット後の書き込み無視 | リセット後約 29658 CPU クロックの間、PPUCTRL/PPUMASK/PPUSCROLL/PPUADDR への書き込みは無視される | 単一出典 |
| CPU の分周器 | 「The CPU clock divider is not affected by reset.」「The PPU clock divider is affected by reset. Therefore, resetting the PPU changes the CPU/PPU sub-cycle alignment.」 | 単一出典（Fiskbit のユーザページ。正式記事ではない） |
| CPU と PPU の位相の組み合わせ | blargg: 「Nope, there are four for NTSC.」「After power/reset, PPU is randomly in one of four synchronizations with CPU.」Wiki: 「The beginning of a CPU tick could be offset by 0-3 master clock ticks from the nearest following PPU tick.」一部の機体では、4 通りのうち 1 つでパレットの読み出しが壊れる | 確認済 |
| 2A03 の分周 | CLK パッドから CLK/12 の分周器を経て PHI0。M2 は PHI2 より 1.5 CLK 早く High になる。M2 はリセット中も動き続けるという観測がある | 単一出典（Breaking NES）／単一出典（検索要約経由） |
| Lava RGB の観測 | 「the delay between fall of PPU /CE and rise of ALE is variable depending on a particular power-up allignment」「there are 3 PPU RD cycles per one CPU cycle」 | 単一出典 |
| 2 つのチップの同期 | andkorzh: 「Reset pin … will need to be used to synchronize the chips with each other」。任天堂の特許も複数の PPU の /RES を共通にして H/V を同時にリセットする案を示す（共通 CLOCK 21.48 MHz・共通 RESET の図） | 単一出典 |
| NESRGB | TIMING ブロックに PPU の CLK、/RES、INT を入れる | 単一出典（ブロック図） |
| ALE | 「goes high at the beginning of a PPU VRAM access ... It stays high for one PPU cycle.」 | 確認済 |
| /RES 入力の内部同期段の有無 | 資料なし。クロックエッジの近くで解除すると 1 CLK 揺れる可能性がある | 未確認 |

本基板での位置合わせの方法（未確認（推論））は次のとおり。

1. マイコンがマスタークロックを出す（1.9.4 節）。PIO の時間軸と PPU の時間軸が同じになる。
2. PPU /RST を +5V に固定せず、マイコンがクロックの立ち上がりに合わせて解除する。PCLK の位相とマスタークロックの関係が毎回同じになる。
3. CPU と PPU の位相も固定したいときは、2A03 の M2 の立ち上がりを基準に「M2 のエッジから n マスタークロック後」に PPU /RST を解除する。CPU の分周器はリセットされないので、M2 を観測して位相を知る必要がある。4 通りのどれも実機で起こる状態なので、1 つに固定してもソフトの互換性は損なわれないと考える。
4. PPU の解除は CPU /RST の解除より先にする（ファミコンと同じ順序）。
5. 「電源投入ごとの 1 画素ずれ」の原因は、外部回路が PPU の PCLK の位相（4 相のどれか）を知らずに EXT と比較器出力を標本化することだと考えられる（原因の特定は推論のまま）。上の 1〜2 でこの原因が消える。EXT と VOUT の相対遅延は固定値になり、試作で 1 回校正すればよい（PPU の品種ごとに確認が要る）。起動時の確認には ALE の位相を使う。
6. 解除の位置が毎回同じかは、ALE か /RD の位相を測って実機で確かめる。

### 1.6 RGB 出力版 PPU のピンの違いと、両対応ソケットの条件

#### 品種

| 品種 | 特徴 | 搭載機 | 確度 |
|---|---|---|---|
| RP2C03B、RC2C03B/C | 2C02 とほぼ互換。違いは ① 強調ビットでその成分をフル輝度にする（「Color emphasis bits set the corresponding channel to full brightness」。2C02 は他の 2 成分を少し暗くする） ② パレットは NTSC に近いがかなり彩度が高い ③ グレー $2D/$3D が黒（$1D と同じ） ④ 「No shortened pre-render line every other field」 | VS. Duck Hunt、VS. Tennis、PlayChoice-10 全般、Sharp C1（ファミコンテレビ） | 確認済 |
| RP2C04-0001〜0004 | 「All four 2C04 PPUs contain the same master palette, but in different permutations」。VS. System の説明では「60-color master palette」のコピープロテクト。RP2C04-0001 は「Equivalent to 2C02D, but keeps 2C03 timing (no skipped dot)」。グレースケールは列を寄せるだけでグレーにならない | 多くの VS. System | 確認済 |
| RC2C05-01〜05 | 2C03 と同じ色だが $2000 と $2001 の意味が入れ替わる。$2002 の bit4-0 に ID を返す（2C05-02: $3D、2C05-03: $1C、2C05-04: $1B）。`A0' = A0 xor (A1 nor A2)` の回路で入れ替えれば 2C03 として動く | 後期の VS. System | 確認済 |
| RC2C05-99 | 「An RGB PPU with RP2C02E behavior」「Uses 2C02 timing (a dot is skipped every other frame), unlike other RGB PPUs.」「PPUCTRL and PPUMASK aren't swapped.」 | Sharp ファミコンタイトラー（AN-510）。RGB 出力は X0858CE エンコーダへ（色差に 0.5 ゲイン、3.579545 MHz 水晶） | 確認済（NESdev Wiki の 3 ページと Breaking NES） |
| 2C03 と 2C05-99 の hue $D | 暗い灰色ではなく黒で表示 | — | 単一出典 |
| 互換性（2012〜13 年の議論） | Quietust「2C03 は概ね互換」「The 2C04s are not compatible because they have scrambled palettes」。Drakon は RC2C05-04 を baku の回路で動かした（RGB アンプの代わりに Sony CXA2075 回路）。lidnariq: 2C04 を使うには「three 3-bit ADCs running at the pixel rate, three 3-bit DACs, and a 512×9b lookup table」が必要 | — | 単一出典 |
| 価格・入手性 | 2019 年頃の相場 110〜150 USD（RC2C03B/RC2C03C/RP2C03B のどれでも）。テスト済み RP2C03B が 125 USD で落札。tall-dog は RP2C03B/RC2C03B/RC2C03C/RC2C05-03/RC2C05-04 を 260 USD で掲載し、2026-11 時点で全品 Sold Out。中古の抜き取り品で修理ピンがある場合もある | — | 確認済（複数の販売情報） |

#### ピンの違い

| Pin | RP2C02 | RGB 出力版 PPU | 確度 |
|---|---|---|---|
| 14 | EXT0（双方向） | RED（アナログ） | 確認済 |
| 15 | EXT1 | GREEN | 確認済 |
| 16 | EXT2 | BLUE | 確認済 |
| 17 | EXT3 | AGND（「EXT3 is internally and externally tied to ground: perhaps it serves as an analog ground for the video DACs」） | 確認済 |
| 21 | VOUT（コンポジット） | /SYNC（アクティブ Low の複合同期。3 本並列のプルダウントランジスタと「VOLTAGE DIVIDER」。非増幅） | 確認済 |
| その他 | 同じ | 同じ（2C05-01〜05 は $2000/$2001 の入れ替えあり） | 確認済 |

- RGB 出力版 PPU の内部（RP2C04-0003 のダイ写真から復元）: 「DAC with weighted current summation」。各色 8 レベル（B0〜B7 など 8 本のトランジスタ列）。偶奇（ドットスキップ）回路はあるが切断されている。BURST 信号は作られるが使われない。/SLAVE は使われず、EXT_IN は 0 固定。単一出典（Breaking NES）。
- R/G/B のピン電圧（黒・白のレベル）、出力インピーダンス、/SYNC の電圧と極性の数値は、NESdev Wiki にも回路図にも見つからない。未確認。
- TinyNES が THS7314（固定 6dB、出力は 75Ω 直列）に直結していることから、ピン出力は「0 V 付近から 0.7〜1 V 程度」の DC 結合レベルと推測される。未確認（推論）。
- 2005 年の NES 改造スレッド: RGB 出力版 PPU の pin14〜17 は NES 基板では GND につながるので「The RGB Pins should not connect from the socket to the pcb」。「RP2C03/4/5 PPUs output composite sync」「this signal is unamplified」。アンプに NTE123AP/NTE159（2N3904/2N3906 相当とされる）を使った例がある。単一出典。
- VS. System、PlayChoice-10、Sharp C1、Famicom Titler の RGB 出力段（トランジスタの型番・抵抗値）は未確認。

#### 同じソケットで両対応にする条件（未確認（推論）。TinyNES の実例を一部含む）

1. **pin14〜16**: 2C02 のときは EXT0〜2 としてマイコン入力へ（10k のプルダウンで入力モード時の backdrop = 0 を保証）。RGB 出力版 PPU のときは R/G/B として映像バッファへ。同じ配線に両方を並べてつなぐと、RGB のアナログ出力がマイコンのデジタル入力を中間電位で駆動し、逆に 2C02 のデジタル出力が映像アンプに入る。ジャンパ、アナログスイッチ（74HC4066 など）、または 0Ω 抵抗の実装の選択で分ける。
2. **pin17**: RGB 出力版 PPU では AGND（内部で GND）。2C02 を出力モードにすると EXT3 の出力になるので、**GND に直結してはいけない**。本基板では「10k プルダウン + マイコン入力」とし、RGB 出力版 PPU のときだけ 0Ω ジャンパで GND に落とす。TinyNES は 10k プルダウンで両立させ、RGB 基板側で EX3 を GND に落としている（TinyNES の 2C02 は出力モードにしない前提）。
3. **pin21**: 2C02 のときは VOUT（比較器の入力、必要ならコンポジット出力）。RGB 出力版 PPU のときは /SYNC（内部分圧付き、非増幅）を 74HC14 などで整形して JAMMA の CSYNC へ。
4. **pin12（A0）**: 2C05-01〜05 用に A0 の入れ替えゲート（74HC02 と 74HC86、またはマイコン側で入れ替え）とジャンパ。RC2C05-99 は入れ替え不要。TinyNES は S5 スイッチで「CPU A0 直結」と「NOR(A1,A2) → XOR(A0)」を切り替える（確認済、回路図）。
5. **ファーム**: $2000 bit6 の強制とパレットの改変は、RGB 出力版 PPU のときに止める。
6. **2C04**: 色の変換表なしでは色が狂うので、実用外とする。

### 1.7 PPU の映像タイミングと同期信号の作り直し

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

「the video output of the PPU is delayed by 1 pixel clock」。単一出典（NESdev Wiki: NTSC video。複数ノートで取得し、2026-11-10 に原文で再確認。1 ライン 341 ドットであること自体は PPU rendering と PPU frame timing でも確認済）。

#### 垂直（262 ライン）

| 区間 | ライン |
|---|---|
| 表示 | 0〜239 |
| post-render | 240〜241（VBlank フラグはライン 241 でセット） |
| post-render blanking | 242〜244 |
| vertical sync | 245〜247（3 ライン。vertical blanking pulse は dot 277 から 318 ドット、serration は dot 254 から 32 ドット） |
| pre-render | 248〜261（VBlank はライン 261 でクリア） |

単一出典（NESdev Wiki: NTSC video。vertical sync 245〜247、pulse 277/318、serration 254/32 は 2026-11-10 に原文で再確認。262 ライン自体は PPU rendering でも確認済）。

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

#### 同期の取り出し方（既存品）

- NESRGB と Lava RGB は、PPU のコンポジットから比較器で同期を取り出す。Lava のネット名は `VOUT_CS`、`VOUT_BLANK`、`VBL`。確認済。
- Hi-Def NES は PLL で HDMI と同期させる。単一出典。

#### 本基板での作り直し方（未確認（推論））

| 案 | 方法 | 長所 | 短所 |
|---|---|---|---|
| (A) VOUT の比較器 | sync tip（48 mV）と burst low（148 mV）の間をしきい値にする（終端なしなら kevtris の測定で 0.78 V と 1.00 V の間。PPU ピン直では値が違う）。そのまま CSYNC にする | ドットスキップとリセットに自動で追従。PPU の serration もそのまま出る。比較器は遅くてよい（LM393 でも可。1 µs 程度の遅れは全ラインで一定） | 比較器 1 回路と配線が要る |
| (B) RP2350 の PIO カウンタ | PPU /RST をマイコンが解除するので H/V の位相は既知。奇数フレームの短縮は、盗聴している $2001 の表示有効ビット（bit3 または bit4）を見て、プリレンダーラインを 1 ドット短くしてまねる | 追加部品なし。映像を 1 ライン遅らせても、画像が 1 ライン下にずれるだけでモニタへの影響はない | 判定のタイミング（ライン 261 dot 339 付近の $2001 の状態）を誤ると、各フレームで 1 ドット揺れる（ずれは蓄積しない） |
| (C) 341 ドット固定 | 出力側を 341 ドット固定で作る | ドットスキップのジッタ自体が消える | 1 ライン遅延のラインバッファが前提 |

- 2 つの第2次ノートで推奨が分かれる。rgb_round2_details.md は (A) を主、(B) を予備とする。rgb_pico2_feasibility.md は、マイコンがクロックと /RST を握る構成を前提に (B) を使い、(A) は照合用の任意の比較器（LM393）とする。どちらも実験はされていない。後者のほうが新しく、クロックを握る構成と一体で検討されているので、本シートは (B) を主、(A) を照合用とする（推論）。RGB 出力版 PPU に差し替えたときは pin21 の /SYNC をそのまま使う。
- ブランキング中は RGB を 0 にするマスクが要る。EXT は表示の外でも値を出すからである。マスクは比較器かドットカウンタ（active = dot 1〜256 と、ボーダー 257〜267、327〜340）で作る。ボーダー（backdrop 色）を出すかどうかは仕様の判断である（推論）。
- JAMMA の同期は負極性 TTL（High ≥ 3.5 V 推奨、Low ≤ 0.4 V）のコンポジット同期で、5 V のゲート 1 段と直列 47〜100 Ω を推奨する（JAMMA の電気仕様の調査による推論）。3.3 V の GPIO の直出しでは High が足りないので、NPN（MMBT3904/S8050、Basic）で 5 V にプルアップして反転出力するか、74HCT 系を使う（推論）。
- JAMMA のモニタが V sync 中の serration（等化パルス相当）の正確な形を要求するかは未確認。

### 1.8 パレットデータの選択肢とライセンス、色強調とグレースケール

#### 2C03 のパレット（R,G,B 各 0〜7 の 3bit、8bit に直すと C = 255×DAC/7）

```
$0x 333 014 006 326 403 503 510 420 320 120 031 040 022 000 000 000
$1x 555 036 027 407 507 704 700 630 430 140 040 053 044 000 000 000
$2x 777 357 447 637 707 737 740 750 660 360 070 276 077 000 000 000
$3x 777 567 657 757 747 755 764 772 773 572 473 276 467 000 000 000
```

単一出典（NESdev Wiki: PPU palettes）。

#### パレットの選択肢

| パレット | 内容 | ライセンス | 確度 |
|---|---|---|---|
| 2C03（上表） | 実チップの DAC 値 | NESdev Wiki にライセンス表示なし（フッターにも無し） | 単一出典 |
| Wiki 掲載ファイル | 2C02G_U_wiki.pal、2C02G_J_wiki.pal、2C07_wiki.pal、2C03_wiki.pal。生成器 pally、Bisqwit、Drag、RGB PPU Palette Converter（WhoaMan） | 記載なし | 単一出典 |
| pally / palgen-persune | パレット生成器 | MIT No Attribution（「MIT No Attribution, Copyright 2024 Persune」） | 確認済（LICENSE ファイル 2 つ） |
| FirebrandX | Smooth (FBX)、PVM Style D93 (FBX)、Composite Direct (FBX)（「pure, unmodified direct-capture of the composite output of the front-loader NTSC NES」）、NES Classic (FBX)。NESRGB は Unsaturated-V6 / Smooth / Digital Prime / Magnum / Smooth V2 も内蔵 | 記載なし | 単一出典 |
| エミュレータ同梱のもの（Nestopia、FCEUX など） | NESRGB 初期: Natural（Nestopia）/ Improved（FCEUX）/ Garish（PlayChoice）。他に RGB Playchoice (Nestopia 2013)、YUV、Sony CXA、Wavebeam | エミュレータのライセンス（GPL など）に従う可能性がある | 未確認 |
| 既存品の内蔵 | Lava RGB は CXA、PC10、FCEUX、NTSC、PAL、YUV の組み合わせ（.jed 名）。LAVA_RGB-TO-PPU_LITE は Composite Direct、Nintendulator NTSC、FBX Magnum、Sony CXA、PC-10、Wavebeam、PAL、Kitrinx | — | 単一出典 |

- 3bit/ch（9bit）なら 2C03 の値をそのまま出せる。2C02 風のパレット（pally など）を出すには 3bit/ch では粗く、4〜5bit/ch 以上が望ましい（推論）。
- 2C02 準拠の見た目なら、pally（MIT-0）で 2C02G の 512 色（強調込み）を作って埋め込むのが権利の面で最も安全と考える。2C03 の表は事実のデータなので一緒に載せられると考えるが、法的な評価は調べていない（推論）。

#### 強調とグレースケール

| 項目 | 内容 | 確度 |
|---|---|---|
| 2C02 の強調 | 強調しない成分を約 0.816 倍（減衰係数約 0.816328）に暗くする。$xE/$xF には効かない | 確認済 |
| RGB 出力版 PPU の強調 | 「it sets the corresponding channel to full brightness」。Breaking NES: 「Emphasis applies the corresponding channel output to all one's」。全ビットで真っ白になる | 確認済 |
| グレースケール | 「ANDing the 6-bit palette color value with $30」。Breaking NES: $2001 bit0（B/W）はカラーバッファの色相 4bit の出力を遮断し、輝度 2bit は常に通す。RGB 出力版 PPU も 2C02 と同じ（2C04 は列を寄せるだけ） | 確認済 |
| EXT との関係 | EXT はパレットアドレスなので、$2001 の効果（グレースケールと強調）を含まない。外部で当てる必要がある | 確認済（EXT の出力位置から） |

- 外部での処理順（未確認（推論））: EXT の番号 → シャドウパレットで 6bit 色 → グレースケール（AND $30）→ 強調（2C02 準拠なら 512 エントリの表で処理）→ DAC。
- PPU に渡す $2001 の強調・グレースケールのビットを 0 に置き換えておけば、PPU のコンポジットは常に平坦な数レベルの信号になり、比較器のしきい値を決めやすい（推論。NESRGB の「Colour data filter」と同じ考え）。

### 1.9 Pico 2（RP2350）で実現する場合の検討結果

ここでの数値は一次資料（RP2350 Datasheet Release 8 など）のものだが、構成と判断は調査者の推論で、試作による実証はまだない。

#### 1.9.1 タイミングの余裕

| 量 | 値 | 確度 |
|---|---|---|
| マスタークロック周期 | 46.56 ns | 確認済（計算元は NESdev Wiki） |
| 画素 | 186.24 ns = 4 マスタークロック | 確認済 |
| CPU サイクル | 558.7 ns = 12 マスタークロック（「CPU cycles begin at the point where M2 goes low.」） | 確認済 |
| M2 High | 2A03E/G/H は 15/24 = 349.2 ns（「350ns/559ns」）、無印 2A03 は 17/24 = 395.8 ns | 確認済 |
| 2A03 の書き込みデータ | lidnariq の実測（60 MHz スコープ）: 「M2 rises 70-90ns after R/W does」「M2 falls 60-56ns before R/W does」、D0 は R/W 立ち下がりの約 250-260 ns 後、「roughly 100ns after M2 rises」に約 4 V。74'139 の遅延は NES-CPU-07 で約 20 ns | 単一出典 |
| 書き込みデータの有効な窓 | M2 立ち上がりの約 100 ns 後から M2 立ち下がりまで、約 250 ns | 未確認（推論・実測からの計算） |
| 2A03 の書き込みデータのホールド時間（M2 立ち下がり後） | 測定されていない | 未確認 |
| 2C02 のレジスタ書き込みのセットアップ/ホールド | 3 系統で探したが数値なし。レジスタアクセスは PCLK と非同期（「It should be understood that the access to the PPU registers is not related to PCLK in any way.」）。パレット読み出しの破損は「depends on when the PPU /CS signal that indicates register access is deasserted」 | 未確認（数値）／単一出典（非同期であること） |
| PIO の命令 | 「Each instruction takes precisely one cycle, unless it explicitly stalls」。150 MHz で 6.67 ns、129 MHz で 7.75 ns | 確認済（データシート） |
| GPIO 入力の同期器 | 「standard 2-flipflop synchroniser. This adds two cycles of latency」。GPIO ごとに INPUT_SYNC_BYPASS で外せる | 確認済 |
| clk_sys の最大 | 150 MHz（「a 150 MHz system clock, the maximum supported on RP2350」） | 確認済 |
| PIO の数・資源 | 3 ブロック × 4 SM = 12 SM、命令メモリは各ブロック 32 命令、各 SM に 4 語 × 2 の FIFO（8 語 1 方向に結合可）、分周器 16 整数 + 8 小数ビット | 確認済 |
| RP2350 の PIO の追加機能 | SHIFTCTRL.IN_COUNT、MOV の宛先に PINDIRS、FJOIN_RX_GET / FJOIN_RX_PUT（RX FIFO のランダムアクセス）、PIO ブロック間の IRQ（「no delay penalty」）、「Improved GPIO input/output delay and skew」 | 単一出典（データシート） |
| DMA・バス | DMA は毎サイクル 1 読み 1 書き。150 MHz で「maximum sustained bus bandwidth is 3.6 GB/s」。各コアに INTERP0/INTERP1 | 確認済 |
| GPIO のパッド遅延（ns） | データシートに数値なし | 未確認 |
| 1 画素あたりの命令数 | 27.9（150 MHz）/ 24（129 MHz） | 未確認（推論・計算） |
| 1 CPU サイクルあたりの命令数 | 84（150 MHz）/ 72（129 MHz） | 未確認（推論・計算） |
| 画素データ量 | 5 bit × 5.37 MHz = 26.8 Mbit/s。DMA の能力の 1% 未満 | 未確認（推論・計算） |

時間の分解能の点では PIO は十分である（推論）。

#### 1.9.2 候補となる構成（未確認（推論））

共通の方針は次の 3 つである。

1. **クロックとリセットを RP2350 が握る。** PIO が 21.5 MHz を出し、同じ時間軸で PPU /RST をクロックのエッジに合わせて解除する。
2. **データバスへの介入は直列抵抗で行う**（1.9.3 節）。
3. **映像は 1 ライン遅らせて出す。** 取り込みと出力が同じ PIO のクロック領域なので、FIFO があふれたりずれたりしない。

各部の動き:

- **EXT と第5ビットの取り込み**: PIO の SM「CAP」が 129 MHz で 1 画素 24 命令の周期で `in pins, 5` → `in null, 3` を繰り返し、32 bit ごと（4 画素）に DMA でラインバッファへ送る。標本化の位相は 7.75 ns 刻みで変えられるので、画素の中央に置く。第5ビットは VOUT 経由なので EXT より数画素遅れて届く。同じ時刻に取り、ファームで決まった画素数だけずらして合わせる。
- **PPU に書く固定パターンの例**: BG 16 エントリ = $0F（黒。blank と同じ電位）、スプライト 12 エントリ（$3F11-13/15-17/19-1B/1D-1F）= $20（白）。$3F10/14/18/1C は $3F00/04/08/0C のミラーなので BG 側（$0F）を書く。強調とグレースケールは PPU 側で 0 に置き換え、VOUT を常に 3 値（sync/黒/白）に保つ。同期をマイコンのカウンタで作るのでブランキング用の比較器が要らず、BG を $0F にできる。
- **同期とブランキングも VOUT から取る場合**: BG を $0F/$1D にするとブランキングと見分けられない。BG を $00（または $2D）、スプライトを $20 にして、しきい値を sync < th1 < blank < th2 < BG < th3 < sprite に置けば、比較器 3 個で同期・ブランキング・第5ビットを分けられる。$00 と $2D は強調時に ×0.816 で下がるが、強調ビットを PPU に渡さなければ影響しない。NESRGB と Lava が実際にどちらにしているかは公開資料から判断できない（未確認）。
- **シャドウパレットの変換と出力**: ライン n で取り込んだ画素を、ライン n+1 の間にコア 1 が変換し、ライン n+2 の H 同期から出力 SM「OUT」が 1 画素 24 命令で `out pins, 9` する。変換は idx = (spr<<4)|ext。(ext&3)==0 なら idx=0（backdrop）。c6 = shadow[idx]（6 bit）。グレースケールなら c6 &= $30。強調 3 bit と合わせて 512 エントリの表から 9 bit の RGB を得る。1 画素 8〜12 命令程度、256 画素 × 12 命令 ≈ 3,100 サイクル/ライン（129 MHz で 1 ライン 8,190 サイクル）で、1 コアの約 40%。
- **$2001 を画面の途中で変えたとき**: 盗聴側が書き込み時のドット位置を付けて記録し（PIO の時間軸が PPU と同じなので正確に分かる）、変換時にその画素から切り替える。
- **t/v/w の追跡**: PIO の SM「SNOOP」が `wait 0 pin /CS` で待ち、「M2 立ち上がりから n マスタークロック後」（M2 立ち下がりの約 60 ns 前）に `in pins` する（D8 + A3 + R/W = 12 bit）。CPU の分周器はリセットされず位相が電源投入ごとに不定なので、最初の /CS↓ か M2 を一度観測して位相を決める。盗聴で読む時刻を /CS の立ち上がり後にしてはいけない。/CS は 74139 を通って M2 より 20〜30 ns 遅れて立ち上がり、同期器 2 段を経ると M2 立ち下がりの 40〜60 ns 後になり、データが残っている保証がないからである。
- **置き換え値の先読み**: SM「SUBST」は次の $2007 で出すべき値をすぐ知る必要がある。コアは v が変わるたびに「次の $2007 がパレットか、BG/スプライトのどちらか」を計算し、FJOIN_RX_GET の RX FIFO 記憶レジスタに書いておく。PPU へのアクセスの最短間隔は通常 4 CPU サイクル（STA abs; STA abs）≈ 2.2 µs で、コアの更新（数百 ns）には余裕がある。1 サイクル間隔（RMW 命令の二重書き込み、DMC DMA による $2007 の二重読み出し）は間に合わない可能性があり、既知の限界とする。
- **パレットの読み出し**: PPU の実パレットは固定パターンなので、ゲームは改変値を読み戻す。直列抵抗方式では読み出し値を差し替えられない。2C02G より前の PPU には読み出し機能自体がないので、影響は限られる。

| 構成 | 内容 | 長所 | 短所 |
|---|---|---|---|
| 案 A: RP2350B（48 GPIO）1 個 | 38〜41 本を使い 7〜10 本余る。PIO 12 SM のうち 8〜9 SM、命令は 96 のうち 60 前後 | 最も素直。余りを重ね表示や 4-4-4 RGB に回せる | QFN-80（0.4 mm）で手はんだは無理。JLCPCB の Extended 実装が前提。外部 21.47727 MHz 発振器を XIN に入れる構成も可能 |
| 案 B: Pico 2 ×2 | Pico A = クロック・リセット・映像（EXT、比較器、RGB、CSYNC）。Pico B = バスの盗聴と置き換え、パッド応答、JAMMA の入出力 | Pico 2 モジュール（秋月）で組める。マイコン自体を基板実装に頼らない（ただし周辺の 74HC165 は Preferred Extended。1.9.5 節） | A と B のクロック領域が違う。B から A へのイベント（パレット書き込み、$2001 の変化）は SPI/UART などで送り、A が受信時刻のドット位置で当てる（$2001 を画面の途中で変えると数十画素ずれ得る）。B の置き換え判断は B の中で完結するので、PPU への改変のタイミングは影響を受けない |

- Pico A は PPU にクロックを出す側でなければならない（EXT の取り込みと同期させるため）。B は非同期でよいが、「M2 から n クロック後」の決め打ちは使えないので、「/CS↓ を同期器経由で検出 → 決まった命令数待つ → 標本化」とする（150 MHz で ±6.7 ns の揺れ。窓 250 ns に対して問題ない）。

#### 1.9.3 実 PPU のパレットを「BG 暗・スプライト明」に保つ回路の選択肢（未確認（推論））

| 方式 | 追加部品 | 仕組み | タイミング | 主なリスク | 判定 |
|---|---|---|---|---|---|
| D1: 直列抵抗インタポーザ（CPU D0-7 —R— PPU D0-7、RP2350 は PPU 側に直結） | 470 Ω ×8（0603 の単品 470 Ω C23179、Basic、×8。または 0603×4 アレイ C25510 ×2。C25510 は Preferred Extended で Basic ではない） | 置き換える書き込みの間だけ RP2350 が PPU 側を駆動する。抵抗が CPU 側との衝突電流を抑える | /CS↓ から約 20〜50 ns で駆動を始め、/CS↑ の 20〜30 ns 後まで保つ。M2 High 349 ns に対して余裕が大きい | ① 2C02 の入力が 3.3 V を High と受けるか（TTL しきい値と考えられているが未測定）② 衝突電流 3.3 V/470 Ω ≈ 7 mA/本（RP2350 は 12 mA 設定、IOVDD 合計 100 mA 以内）③ PPU からの読み出し（$2002/$2004/$2007）が抵抗とバス容量（推定 30〜50 pF → τ ≈ 14〜24 ns）だけ遅れる | **第一候補**。部品が最少。単品抵抗なら Basic のみ（アレイにすると Preferred Extended） |
| D2: 74HC245 インタポーザ | 74HC245（Preferred）と方向・OE の制御 | CPU 側を A、PPU 側を B にし、置き換え時は OE を切って RP2350 が B 側を駆動する | tpd 26 ns、ten 58 ns、tdis 50 ns（max、4.5 V） | ① 3.3 V で 5 V の 74HC の OE/DIR を駆動すると VIH 3.15 V(@4.5 V)〜約 3.5 V(@5 V) を満たさない（規格外）→ 74HCT245（Extended）が必要 ② それでも置き換えデータは 3.3 V で駆動するので D1 の①は残る ③ 読み出し時の方向切り替え | D1 がだめなときの予備（74HCT245 または SN74LVC4245A（Preferred）を使う） |
| D3: /CS の遮断 | 74HC08 など 1 個 | パレット範囲の $2007 書き込みを PPU に見せない | ゲート 1 段（〜20 ns） | PPU の中の v が +1/+32 されず、以後の VRAM アクセス先が実機とずれる。$2000 bit6 は書き込みを見せた上でビットを変える必要があり、遮断では実現できない | **不成立** |
| D4: 独自の書き込みの挿入 | PPU 側の RS/R/W//CS も分ける抵抗かバッファ | CPU が PPU を触らないサイクルに RP2350 が書く | 空きサイクルを探す必要 | 複雑。PPU の v/w を余計に動かす | 不採用 |
| D5: 改変なしで第5ビットを推定 | 多値の比較器 | BG 色 P[i] とスプライト色 P[16+i] を VOUT の明るさで比べる | — | 同じ明るさで色相が違うと区別できない | 不完全 |

- PPUCTRL bit6 の強制は D1 の上で行う。SUBST SM が「/CS=0, R/W=0, A2-0=000」を見つけたら D6 だけを 3.3 V で駆動する（他のビットは CPU の値が抵抗を通ってそのまま届く）。同じ仕組みで $2001 の bit0 と bit5〜7 を PPU 側で 0 に置き換える。PIO の例: `wait 0 gpio CS` → `mov pc, pins`（IN_COUNT=4 で {R/W,A2,A1,A0} の 16 分岐の表）→ 該当の分岐で `mov pins, …`／`mov pindirs, …` → `wait 1 gpio CS` → 数命令後に `mov pindirs, null`。/CS↓ から駆動まで約 5 命令（129 MHz で約 40 ns、同期器込みで約 55 ns）。
- 書き込みを置き換えるときは「/CS が Low の間ずっとと、/CS 立ち上がりの 20〜30 ns 後まで」PPU 側を駆動し続ける。PPU のラッチが透過型でもエッジ型でもセットアップとホールドを満たすためである。
- D1 では RP2350 が駆動するのは PPU 側だけで、CPU 側は CPU の値のままなので、MMC5 には本当の値が見える。
- 第1次調査が勧めた 74HC245 より、直列抵抗のほうが部品が少なく同等以上である（第2次調査の判断）。

#### 1.9.4 クロックの作り方

| 事実 | 内容 | 確度 |
|---|---|---|
| PLL の式と制約 | 「( FREF / REFDIV ) × FBDIV / ( POSTDIV1 × POSTDIV2 )」。基準は 5 MHz 以上、VCO は 750 MHz-1600 MHz、FBDIV は 16-320、POSTDIV は 1-7。12 MHz 水晶では FBDIV 63〜133。「Jitter decreases as VCO frequency increases」 | 確認済（データシート） |
| PLL の基準 | 「On both PLLs, the FREF (reference) input is connected to the crystal oscillator's XIN (XI) input.」XIN 入力は 50 MHz まで。GPIN0/1 は「can provide system and peripherals clocks, but is limited to 50 MHz」で、PLL の基準にはならない。XIN の矩形波入力時の VIH は 0.65×IOVDD | 確認済（データシート） |
| PLL の精度条件 | 「The PLLs can drive clocks at their maximum frequency as long as the reference clock is accurate to 1000ppm」 | 単一出典（データシート） |
| Pico 2 の水晶 | Abracon ABM8-272-T3、12 MHz、「The crystal has a 30 ppm frequency tolerance」。XIN は基板上でこの水晶につながっている | 確認済 |
| クロック出力 | GPOUT0-3 は GPIO13/15/21/23/24/25 などに出る。Pico 2 では GPIO23（SMPS PS）、GPIO24（VBUS sense）、GPIO25（LED）が基板内部用なので、ヘッダに出る GPOUT は GPIO13/15/21 | 確認済 |
| USB ブート | 既定では 12 MHz の入力に頼る（OTP で上書き可） | 単一出典（データシート） |
| Hi-Def NES の前例 | 「The NES is very very slightly underclocked to do this, around 0.15%.」「both CPU and PPU are clocked the same so no games should break」。FPGA のクロックは「slightly jittery」 | 単一出典 |
| 3.3 V でのクロック駆動の前例 | TinyNES は 3.3 V の MEMS 発振器とクロックバッファから 30 Ω で CPU/PPU の CLK を駆動して量産している。2A03 を 3.3 V の CPLD で駆動して動いた報告もある | 確認済 |
| 2A03 の低速クロック | NMOS なので DC（低速）クロックは不可 | 単一出典 |
| ファミコンのクロック回路 | X1 21.47727 MHz、Q2 2SC2021 のピアース型（推論）。PPU CLK は C4 51 pF で結合、CPU CLK は Q3 エミッタフォロワ（R9 1.2k）→ C9 220p → CPU 29、CPU 29 に R13 150k 対 GND。GPM-02 は CPU/PPU とも 10 nF で結合 | 確認済（ネットリスト） |
| 2A03/2C02 の CLK 入力のしきい値・振幅・バイアス、直結してよいか | 資料なし | 未確認 |

12 MHz を基準に整数分周で作れる候補（調査者の全探索。未確認（推論・計算））:

| PLL 設定 | clk_sys | PIO 分周 k | 出力 | 誤差 | 備考 |
|---|---|---|---|---|---|
| FBDIV=129、VCO 1548 MHz、POSTDIV 6×2 | 129.000 MHz | 6 | 21.500000 MHz | **+1058 ppm** | 推奨（VCO が高めでジッタが小さい、デューティ 50%） |
| FBDIV=86、VCO 1032 MHz、POSTDIV 4×2 | 129.000 MHz | 6 | 21.500000 MHz | +1058 ppm | 同上（VCO 低め） |
| FBDIV=125、VCO 1500 MHz、POSTDIV 5×2 | 150.000 MHz | 7 | 21.428571 MHz | −2268 ppm | 公称最大クロック。デューティ 4:3 |
| FBDIV=113、VCO 1356 MHz、POSTDIV 3×3 | 150.667 MHz | 7 | 21.523810 MHz | +2167 ppm | 150 MHz 超（規格外） |
| FBDIV=93、POSTDIV 2×2 | 279 MHz | 13 | 21.461538 MHz | −733 ppm | 規格外（オーバークロック必須） |

- 21.4772727 MHz = 12 MHz × 1.78977… で、小さい分母の最良の近似が 43/24（= 21.5 MHz）なので、規格内に ±1000 ppm より良い整数解はない。
- +1058 ppm の影響: 画素 5.375 MHz、ライン 15.762 kHz（公称 15.746 kHz）、フレーム 60.16 Hz（公称 60.10 Hz）、ゲーム速度 +0.106%、音程 +1.83 セント。15 kHz のモニタの受け入れ範囲に十分入る。Hi-Def NES の −0.15% より小さい。拡張音源も M2 由来なので同じだけずれる。コンポジットの色副搬送波は 3.5833 MHz（+3.8 kHz）になり、テレビの色同期は外れると考えられる（RGB だけなら関係ない）。
- 分数分周で平均を合わせると、周期が 1 clk_sys（6.7〜7.8 ns、マスター周期の 14〜17%）単位で揺れる。NMOS がこれに耐えるかは未確認で、RGB では周波数の正確さも要らないので採らない。
- 欠点: RP2350 が止まると CPU/PPU も止まる（書き換えやウォッチドッグの再起動時）。NMOS は低速クロック不可なので、クロックの停止前後は必ず /RST を保つ。RP2350 の GPIO はリセット時にプルダウンなので、/RST を Low に引く設計にしておけばブート中は自動でリセットが保たれる。
- 3.3 V での駆動は、RP2350 の GPIO（12 mA、高速スルー）と 30〜33 Ω の直列抵抗で、CPU と PPU を別のピン（同じ SM のサイドセットで同時に変化）から駆動する。

他の方式との比較（未確認（推論））:

| 方式 | 周波数精度 | ジッタ | 部品 | RP2350 との関係 | 判定 |
|---|---|---|---|---|---|
| ① RP2350 PIO の整数分周（129 MHz÷6） | +1058 ppm（水晶誤差 ±30 ppm を含めても 1.1×10⁻³） | PLL のジッタのみ（値は未確認） | 0（直列抵抗のみ） | 完全に同期 | **推奨** |
| ② RP2350 の分数分周 | 平均 0 ppm | 6.7〜7.8 ns の周期ジッタ | 0 | 同期 | 不採用 |
| ③ 74HC04（Preferred）と 21.47727 MHz 水晶のピアース発振 | 水晶の精度（数十 ppm） | 低 | 水晶 C5289705（Extended、在庫 2,648）、C×2、R×2、74HC04 | 非同期（同期器で ±1 clk_sys = ±6.7 ns 揺れる） | 可。ただし発振用途はアンバッファの 74HCU04 が定石で、74HC04 は要評価（JLCPCB の 74HCU04 は SN74HCU04N 79 個のみで実質在庫なし。秋月に TC74HCU04AP（DIP）¥30） |
| ④ 発振器モジュール（SG-8002 など 21.47727 MHz） | ±50 ppm 程度 | 低 | モジュール 1（Basic 外） | 非同期。自作 RP2350 基板なら XIN に入れて PLL で ×6 = 128.86 MHz に同期 | 案 A なら有力。USB ブートは 12 MHz 前提なので OTP の設定か別系統が要る。×7 = 150.34 MHz は公称最大 150 MHz を 0.23% 超える |
| ⑤ Si5351A モジュール（秋月 ¥650） | 実用上ほぼ 0 ppm | 未確認 | モジュールと I²C | 非同期（Pico 2）、自作基板なら XIN へ | 珍しい部品寄り。①で足りるので不要 |

- 秋月の「21.47727」のキーワード検索では該当商品が出なかった（2026-11-10）。型番違いで登録されている可能性は残る（未確認）。
- 非同期（③④⑤ を Pico 2 と組む）の場合: 21.477 MHz を FT ピンに入れ、PIO が `wait 1 pin`/`wait 0 pin` を 4 回繰り返して 1 画素を数えてから `in pins` する。出力側も同じく外部クロックのエッジに従わせる必要があり、±6.7 ns の揺れ（画素幅の 3.6%、CRT では見えないと推定）が出力画素のエッジに乗る。

#### 1.9.5 必要な端子数の見積もり（実チップモード）

| 事実 | 内容 | 確度 |
|---|---|---|
| Pico 2 の GPIO | 「exposes 26 of the 30 possible RP2350 GPIO pins」。GPIO0〜22 はデジタル専用で 5 V 耐性（23 本）、GPIO26〜28 は ADC 兼用で IOVDD + 約 300 mV まで | 確認済 |
| RP2350A / RP2350B | RP2350A は GPIO0–25 が FT、GPIO26-29 が ADC 兼用（FT ではない）。RP2350B は GPIO0–39 が FT、GPIO40–47 が ADC 兼用。PIO は「limited to 30 GPIOs for RP2350A」、各 PIO ブロックは GPIOBASE で 32 本の窓を選ぶ | 確認済 |
| 秋月（2026-11-10） | Raspberry Pi Pico 2（SC1631）¥990、在庫 1,462（販売コード 129604）。RP2350B（SC1510、QFN80、GPIO 48）¥220、在庫 242（130370）。RP2354B（SC1512、2 MB フラッシュ内蔵、QFN80）¥280、在庫 115（131441）。RP2350A 実装基板 AE-QFN60-7X7-0.4（GPIO 30）¥450（131106）。RP2350B を載せたモジュールは見当たらない | 単一出典（秋月） |
| JLCPCB | RP2350A（C42411118）は Extended。RP2350B の分類は未確認 | 単一出典／未確認 |
| ファミコンのパッド読み出し | OUT0 は 4021 の P/S、CLK は「normally held high, and becomes low during a read of $4016 or $4017」。/OE1・/OE2 は $4016/$4017 の読み出し時にアクティブ。ファミコンでは $4016 は D0（パッド I）・D1（拡張）・D2（マイク）のみ駆動（D3・D4 も open bus）、$4017 は D0-D4 を駆動 | 確認済 |

GPIO の内訳（未確認（推論））:

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

- 上の表の JAMMA 入力の内訳（Start ×2P、DIP 8 など）は、入力形式が決まる前の見積もりである。現行の要求（4 章）ではボタン 3・4（C・D、ピン 24・25・b・c）も読む必要があり、方式の切り替えはソフトで行うので DIP は減らせる。どちらもシフトレジスタの段数で吸収でき、GPIO の本数は変わらない（推論）。

#### 1.9.6 5V 信号との接続と電源の順序

| 事実 | 内容 | 確度 |
|---|---|---|
| FT ピンの耐圧 | 「very little current flows into the pin whilst it is below 3.63 V and IOVDD is 0 V. Additionally, they will tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V.」VPIN_FT の絶対最大は IOVDD=0V で 3.63 V。公式ブログ「RP2350 is now officially 5V tolerant!」「Just make sure to keep IOVDD powered when 5V is applied to any GPIO pad, otherwise the pad will be damaged.」 | 確認済（データシートと公式ブログ） |
| 電気特性 | VIH(FT) 2〜5.5 V（IOVDD 3.3 V）、VIL ≤ 0.8 V、VOH ≥ 2.62 V（2/4/8/12 mA 設定）、VOL ≤ 0.5 V、プルアップ 32〜86 kΩ、プルダウン 36〜113 kΩ、「Maximum Total IOVDD current 100 mA」 | 確認済（データシート） |
| リセット直後の GPIO | 「Output buffer is high-impedance … Pulled low」 | 確認済 |
| RP2350-E9 | A2 のみの不具合（入力有効時に約 120 µA を吐き出し約 2.2 V に張り付く、内蔵プルダウンが効かない、8.2 kΩ 以下で引けば回避）。A3 で修正、A4 が量産版。秋月の Pico 2 のステッピングは商品ページに記載なし | 確認済（不具合）／未確認（秋月のロット） |
| NMOS 側 | 2A03/2C02 の VOH ≈ 4 V。入力は「It's a mixture, but you just assume it's TTL thresholds. Because the NES is NMOS, not CMOS.」で、未測定 | 単一出典 |
| 74HC の入力 | 74HC245 は VIH 3.15 V @VCC 4.5 V（4.2 V @6 V）。74HC595/165 も 4.5 V で 3.15 V（5 V では 0.7×VCC 換算で 3.5 V）。74HCT245 は VIH 2 V、VIL 0.8 V | 確認済（TI データシート） |
| 既存品の変換 | Lava RGB は SN74LVC4245A ×2 と SN74LVC541A ×2。pico6502 は 74AHCT244/245 | 確認済 |

信号ごとの接続（未確認（推論））:

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

- 電源の順序の危険: 投入時、JAMMA の 5 V が先に立ち、Pico の RT6150 が 3V3 を出すまでの数 ms（未計測）の間に、5 V 側の静的な High（外付けプルアップ、NMOS 出力の High）が FT ピンに 3.63 V 超をかける。切断時は Pico の昇降圧 SMPS（VSYS 1.8 V まで動作）が 3V3 を長く保つ方向なので比較的安全。
- 対策（部品最少）: Pico の 3V3 を検出して P-MOS（SI2301 / AO3401A、Basic）で CPU/PPU/カートの 5 V を入れる（ゲートは 2N7002、Basic）。FT ピンへの直列抵抗（1 kΩ）で故障電流を抑える。FT ピンに 5 V のプルアップを付けない（RP2350 が見る線のプルアップは 3.3 V へ）。
- 74HC を使うなら 3.3 V で給電し、5 V 系との境界には置かない。境界にロジックが要るなら 74HCT（Extended）か LVC（例: SN74LVC4245A、Preferred）を使う。
- PPU の縦縞ノイズ対策のタンタルコンデンサ（4.7〜47µF、10µF 推奨）は、ファミコンでは pin 20(−)–22(+)、NES では pin 20(−)–40(+) に付ける（確認済）。本基板は PPU /RST を制御するので **pin 20(−)–40(+)** に付ける（推論）。

#### 1.9.7 RGB の出力段

| 事実 | 内容 | 確度 |
|---|---|---|
| 日本の JAMMA 筐体の映像入力 | 正極性アナログ RGB、約 3 Vp-p、入力インピーダンス約 2 kΩ、負極性コンポジット同期（TTL レベル）。Blast City の取説は SW3 で「D-SUB MINI 15P: 75Ω / 0.7Vp-p」と「AMP 6P: 2kΩ / 3.0Vp-p」を切り替える | 確認済（取説と配線ガイド） |
| 欧米のシャーシ | K7000 は「RGB analog, [1?] to 5v peak-to-peak ... 4.7k ohm input impedance」、MTC 9000 は「2-5 V p.p.」で DC 結合 | 確認済 |
| 実在する基板の出力段 | TTL/LS ゲートで駆動する抵抗 DAC をそのままエッジに出す。Neo Geo は 220/470/1k/2.2k/3.9k Ω で 0〜3.5 V、Sega System 16 は 250/500/1k/2k/3.9k Ω。合成インピーダンスは約 119 Ω / 129 Ω（計算）。トリマは無く、モニタの CONTRAST で合わせる | 確認済 |
| 新基板の目標（JAMMA の電気仕様の調査による） | 白 3.0 V ±10%（開放）、2 kΩ 負荷で 2.5〜3.0 Vp-p、黒 0 V、DC 結合、正極性、出力インピーダンス 100〜150 Ω、トリマなし | 未確認（推論） |
| PICO9918 の例 | 4 bit/色の重み付け抵抗 3.9 kΩ/1.8 kΩ/910 Ω/470 Ω。75 Ω 終端で 0.7 V を狙った値で、JAMMA には低い | 確認済（回路図）／推論（JAMMA への適合） |

- 3.3 V GPIO による 3 bit の重み付け抵抗（例: 合成 ≈ 120 Ω になる 210/420/840 Ω 級）で、2 kΩ 負荷時 ≈ 3.1 V になる計算である。E 系列への丸めは設計時に行う（未確認（推論））。
- 3-3-3 なら 2C03 の DAC 値をそのまま出せるが、2C02 風のパレットには粗い。4-4-4 にすると 3 ピン増える（未確認（推論））。
- 同じ PIO から同時に出力すれば、ビット間のずれは数 ns 程度に収まる見込みである（未確認（推論））。

#### 1.9.8 画面への重ね表示（未確認（推論））

- 1 ライン遅延のラインバッファ方式なら、出力前のバッファに文字を書くだけで重ね表示ができ、追加のハードウェアは要らない。
- コストはフォント（8×8 で 96 文字 ≈ 768 B）と、文字のあるラインで 300〜1,000 サイクル程度。変換（≈ 3,100 サイクル）と合わせても 1 ラインの予算 8,190 サイクルに収まる。
- 半透明（下地を暗くして文字を載せる）も表引きでできる。ゲーム画面全体を止めて「INSERT COIN」画面を出すこともできる。
- PPU には何も書かないので、ゲームへの影響はない。
- ラインバッファなしでも、出力直前に文字マスクを OR すればできるが、締め切りが 1 画素単位になって厳しい。
- 出力性能の根拠: PIO は「PIO can sustain 360 Mb/s during the active scanline period when running from a 48 MHz system clock」（確認済、データシート）。RP2350 で 2C02 の映像に重ね表示した前例は見つからない。

#### 1.9.9 リスクと確認実験の順序（未確認（推論））

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

### 1.10 RP2C02 のピン（RGB 化に関わるもの）

| Pin | 名称 | 方向 | ファミコンでの接続 | 本基板での扱い（推論） | 確度 |
|---|---|---|---|---|---|
| 1 | R/W | 入力 | CPU 34 | マイコンも盗聴（FT 入力） | 確認済 |
| 2-9 | CPU D0-D7 | 双方向 | 2 = D0（CPU 28）… 9 = D7（CPU 21） | CPU 側とは 470 Ω で分け、PPU 側をマイコンに直結 | 確認済 |
| 10 / 11 / 12 | CPU A2 / A1 / A0 | 入力 | CPU 6 / 5 / 4 | マイコンも盗聴。pin12 は 2C05 用の入れ替えジャンパ | 確認済 |
| 13 | /CS | 入力 | 74139 pin 5（1Y1、$2000-$3FFF、/DBE とも呼ぶ） | マイコンも盗聴 | 確認済 |
| 14-17 | EXT0-EXT3 | 双方向 | GND | 1 kΩ 直列 + 10 kΩ プルダウンでマイコンへ（RGB 版との両対応は 1.6 節） | 確認済 |
| 18 | CLK | 入力 | 21.47727 MHz（05/07 は 51 pF 結合、GPM-02 は 10 nF） | マイコンから 21.5 MHz、30〜33 Ω 直列 | 確認済 |
| 19 | /INT | 出力（オープンドレイン） | CPU 33 + 10k プルアップ | 変更なし | 確認済 |
| 20 | GND | 電源 | — | — | 確認済 |
| 21 | VOUT | 出力（アナログ） | 2SA937 ベース | 比較器へ（RGB 版では /SYNC） | 確認済 |
| 22 | /RST | 入力 | +5 V（ファミコン方式） | マイコンが制御（10 kΩ プルダウン） | 確認済 |
| 23 / 24 | /WR / /RD | 出力 | VRAM、カート 47 / 17 | 変更なし（パレット書き込み時は /WR が出ない） | 確認済 |
| 39 | ALE | 出力 | 373 pin 11（LE） | 任意で位相確認用にマイコンへ | 確認済 |
| 40 | VCC | 電源 | +5 V | タンタル C を pin 20–40 に | 確認済 |

- ピン配置は NESdev Wiki の逐語図、Everynes、3 種のネットリストで全 40 ピンが一致する。Everynes は pin22 を「/SYNC EXT」と呼ぶが、配線の事実は同じ（確認済）。
- ファミコンのコンポジット増幅（HVC-CPU-05/07）: PPU 21 → 2SA937（E-C-B）のベース、コレクタ GND、エミッタ → 220 Ω → VIDEO、VIDEO に 2.2k を +5V へ。GPM-02 はエミッタに 150 Ω を +5V から、フェライトを経て RF（確認済、ネットリスト）。NESdev Wiki の PPU pinout と TinyNES は、+5V から 300Ω、PNP 2SA937（代替 2N3906、ピン配置 E-C-B と E-B-C が違う）、220µF、110Ω、560pF の定数を示す（確認済）。両者は別の機種の回路で、ファミコンについてはネットリストのほうが証拠として強い（推論）。kevtris の電圧の実測は NES の増幅トランジスタでのものである。

---

## 2. 第1次調査からの訂正

第1次調査（rgb_from_rp2c02.md）の記述のうち、第2次調査と検証で訂正されたもの。

| # | 第1次調査の記述 | 訂正後の内容 |
|---|---|---|
| 1 | Famicom Titler の PPU は「2C05-99（PPU palettes）と 2C03（Vs. System）で記述が食い違う」 | **RC2C05-99 で確定**。NESdev Wiki の 3 ページと Breaking NES が一致する。RC2C05-99 は 2C02 タイミング（ドットスキップあり）で、PPUCTRL/PPUMASK の入れ替えがない（他の 2C05 と違う）。したがって A0 の入れ替えゲートは要らない |
| 2 | 「LumaCode の NES 用の実装は見つからなかった」 | **PPUdigitizer (for NES) が存在する**（FPGA、PPU の裏にはんだ付け、受動的な盗聴、LumaCode 出力）。内部方式は非公開 |
| 3 | NESRGB と Lava の比較器の型番は未確認 | Lava RGB は LMV7219M5X ×1 + TLV3502AIDR ×1（計 3 回路）、FPGA は LCMXO2-1200HC-4TG100I、変換は SN74LVC4245A ×2・SN74LVC541A ×2。NESRGB v5 は GSV331（代替 MCP6561）+ MX3502S（代替 TLV3502）+ GS8051 |
| 4 | Lava RGB のソースの所在とライセンスは未確認 | Altium 回路図・基板・BOM・ファーム（.jed のみ）を GitHub で公開。HDL はなく、ライセンスの表示もない |
| 5 | 「RP2040/RP2350 の 5V 耐性は未確認」 | RP2350 は公式に 5V 耐性（IOVDD が給電されている間に限る）。RP2040 は対象外。ADC 兼用ピン（RP2350A の GPIO26–29）は FT ではないことも、データシートの Table 1674 で確認済み |
| 6 | 「LM393/LM339 は µs オーダー（未確認）」 | 確認済み: 1.3 µs（5 mV オーバードライブ）、TTL 振幅の入力でも 300 ns。LM311 は 115/165 ns |
| 7 | 「1 画素ずれの物理的な原因は未確認」 | /RST が PPU の CLK/4 分周器とカウンタをリセットすること、CPU の分周器はリセットされないこと、ファミコンは PPU /RST を +5V に固定するので分周器の初期値が不定であることを確認した（原因の特定自体は推論のまま） |
| 8 | 2SA937 の増幅回路は「検索スニペットのみ・本文未確認」 | 本文で確認: 300Ω（+5V から）、2SA937（代替 2N3906、ピン配置が違う）、220µF、110Ω、560pF、タンタル 4.7〜47µF（10µF 推奨）。TinyNES も同じ定数。ただしファミコン HVC-CPU-05/07 のネットリストでは、エミッタ → 220 Ω → VIDEO、2.2k プルアップで、構成が違う |
| 9 | RGB 出力版 PPU の pin21 は「CSYNC」 | 内部では **/SYNC（アクティブ Low。並列のプルダウンと内部分圧）**で、増幅されていない。2C04 では pin17 は AGND |
| 10 | Hi-Def NES は「PPU に嘘をつく（改変パレット）言及あり」 | kevtris 本人によると、NESRGB と HDN は「slightly different set of palette entries」を使い、HDN には NESRGB と同じ方法で「lie」させるジャンパがある。HDN を付けた機体の RF は「sprites as white on a black background」 |
| 11 | 改変パレットの例「BG 側 $0F 系、スプライト側 $30 系」 | 公開資料で確認できるのは「BG 全黒・スプライト全白」まで。BG を黒（$0F/$1D）にするとブランキングと同じ電位になり、ブランキング用の比較器と両立しない。実際の BG の値は別（$2D/$00 など）の可能性があり、色番号は引き続き未確認 |
| 12 | 「pin17 は 0Ω ジャンパか直列抵抗が必須」 | 方向は正しい。TinyNES は EXT0-3 を 10k プルダウンで受け、RGB 基板側で EX3 を GND に落とす。本基板（2C02 を出力モードにする）では pin17 を GND に直結しない設計が必要 |
| 13 | 「マスター 21.47727 MHz の発振器を CPU/PPU とマイコンで共有し、RP2040/RP2350 の XIN に外部クロックを入れて PLL で整数倍すれば位相が固定できる」（第2次調査 rgb_round2_details.md の「XIN 外部クロック or PIO 入力に分配」も同じ） | **Pico 2 モジュールでは不可**。XIN は基板上の 12 MHz 水晶 ABM8-272-T3 につながっている。GPIN0/1 は clk_sys に使えるが 50 MHz までで、PLL の基準にならない（PLL の FREF は XIN に直結）。自作の RP2350 基板なら可能だが、×7 = 150.34 MHz は公称最大 150 MHz を 0.23% 超えるので ×6 = 128.86 MHz が規格内。Pico 2 で同期させるには、逆に RP2350 がマスタークロックを出す（21.5 MHz、+1058 ppm） |
| 14 | 推奨方針「Pico 2 が CPU→PPU の書き込みを改変できるよう、CPU–PPU 間に 74HC245 を挟む」 | 5 V 給電の 74HC245 の制御入力は VIH 3.15 V(@4.5 V)〜約 3.5 V(@5 V) で、3.3 V 出力では規格外。置き換えデータ自体も 3.3 V で駆動するので、245 を挟んでも 3.3 V 駆動の問題は残る。**直列抵抗（470 Ω）方式のほうが部品が少なく同等以上**。245 を使うなら 74HCT245（Extended）か SN74LVC4245A（Preferred） |
| 15 | 「2C02 は NMOS で出力 High は 5V 未満で、74HC（V_IH≈3.5V@5V）で受けるのはマージン不明」（第2次調査 rgb_round2_details.md の推論） | lidnariq の実測で 2A03/2C02 の VOH ≈ 4 V。5 V の 74HC（VIH 3.15 V@4.5 V）なら約 0.5〜0.85 V の余裕がある（実測 1 例）。RP2350 の FT 入力（VIH 2.0 V）なら十分 |
| 16 | GPIO の概算「30〜35 本でオーバー」、Pico 2 は「26 GPIO 程度（未確認）」 | Pico 2 は 26 本（5 V 耐性は GPIO0〜22 の 23 本）で確認済み。パッド応答（/OE1、/OE2、OUT0）、JAMMA の入出力（シフトレジスタ 5 本）、/RST 2 本、クロックを含めると**最小 37 本、推奨 40 本前後**。Pico 2 ×1 は不可で、Pico 2 ×2 か RP2350B が必要 |
| 17 | 比較器は「高速品か、トランジスタ増幅と 74HC/74AC の入力しきい値」。第2次調査の「JLCPCB Basic に TLV3502/LMV7219 があるかは未確認」 | JLCPCB の Basic/Preferred には LM393 より速い比較器は無い（全件照会）。秋月に ADCMP600（4 ns、¥830）、LTC6752（1.2 ns、3.5 V まで、¥750）、LM319M（5 個 ¥50）がある |
| 18 | 「アーケード（JAMMA）モニタは 0.7 Vp-p/75Ω 入力が一般的」 | 日本の JAMMA 側は正極性約 3 Vp-p・約 2 kΩ。75 Ω / 0.7 Vp-p は同じ筐体の D-SUB15 側の設定である。DAC は開放 3.0 V、出力インピーダンス 100〜150 Ω を目標にする |
| 19 | タンタルコンデンサを pin 20–22 に付ける（ファミコンの付け方） | ファミコンでこうなっているのは pin 22（/RST）が +5 V に固定だからである。本基板は PPU /RST を制御するので、**pin 20(−)–40(+)（VCC）**に付ける（NES と同じ）。pin 22 に付けると /RST の制御を妨げる |
| 20 | 「EXT と VOUT の相対遅延は、起動時またはフレームごとに位相を自動校正する仕組みが望ましい」 | RP2350 がクロックと PPU /RST を握れば位相は毎回同じになり、フレームごとの校正は要らない。初回設計時の 1 回と、ALE による起動時の確認で足りる見込み（推論） |
| 21 | Lava RGB の要約にある「PPU pin 1 (video out)」 | 2C02 の VOUT は pin21（ピン配置は全 40 ピン確認済み）。フォーラム原文の誤記か要約の誤りかは未確認のまま |

---

## 3. 未確認事項と実機で確かめるべきこと

### 3.1 資料が見つからず、実測で決める必要があるもの

| 項目 | 内容 | 確かめ方 |
|---|---|---|
| EXT の電気特性 | EXT 出力の V_OH/V_OL、駆動電流、立ち上がり時間、PCLK エッジからの遅延（ns） | 実験 1・6 でオシロとロジアナ |
| EXT と VOUT の相対遅延 | VOUT 上の同じ画素までの遅れ（PCLK 数） | 実験 6 |
| ブランキング中の EXT | 水平・垂直ブランキング中に EXT が何を出すか（index 0 か不定か） | 実験 1 のロジアナ記録 |
| /RES の内部同期段 | /RES 解除から最初の PCLK エッジまでのマスタークロック数、同期段の有無 | 実験 6（ALE の位相を 20 回の電源投入で記録） |
| 2C02 のレジスタ書き込みのセットアップ/ホールド | /CS からラッチまでの内部遅延 | 実験 2・3 |
| 2A03 の書き込みデータのホールド | M2 立ち下がり後に何 ns 残るか | 実験 3 |
| 2A03/2C02 の入力しきい値 | D 線・CLK・/RST が 3.3 V 駆動を確実に受けるか。CLK を AC 結合せず直結してよいか（ファミコンは 51 pF / 220 pF / 10 nF で結合している） | 実験 2 |
| 2A03/2C02 のクロック耐性 | 受け入れる周波数の範囲とジッタ耐性 | 実験 2・9 |
| RP2350 の PLL ジッタ・GPIO のパッド遅延 | データシートに数値なし | 実験 1 の波形 |
| 比較器 | LM319 とディスクリート案が 186 ns の画素に追従できるか。PPU pin21 の直の電圧（推定: 黒 0.65 V、白 2.1 V、sync 0.15 V） | 実験 1 |
| PPU の品種差 | RP2C02E/G/H などで比較器のしきい値と位相が変わるか | 実験 1（2 種類以上の 2C02） |
| 電源の順序 | Pico 2 の 3V3 の立ち上がり時間、IOVDD 無給電時に FT ピンへ 3.63〜5 V がかかったときの電流 | 実験 7 |
| v/w 追跡 | 追跡した v と実際の v の食い違い。1 サイクル間隔のアクセスへの対応 | 実験 4・5 |
| パレット読み出しを使うソフト | 該当タイトルの有無 | 実験 10 |
| $2001 の効き始め | 強調・グレースケールの変更が何ドット後に効くか | 実験 1 の基板でテスト ROM |
| PIO の命令数と SM 数 | 机上の概算のみ | ピン割り当てと PIO プログラムの確定（実験 8） |
| 重ね表示の CPU 時間 | 概算のみ | 試作ファームで測定 |

### 3.2 文献で決着していないもの

- 既存品（NESRGB、Lava RGB、Hi-Def NES）が PPU に書く具体的な色番号と、ブランキングの取り方。
- Lava RGB のしきい値電圧（1.92V 以外）と分圧の値の対応（SchDoc の配線は未解析）。
- $3F14/$3F18/$3F1C → $3F04/$3F08/$3F0C のミラー（本調査で取得したページに明記なし）。
- $2005 と $2000 bit0-1 による t の書き換え（PPU scrolling の本文が未取得）。
- 2A03 の分周器が /RST でリセットされないことの第 2 の出典（Fiskbit のユーザページのみ）。
- RGB 出力版 PPU の R/G/B のピン電圧（黒・白）、出力インピーダンス、/SYNC の電圧と極性。VS. System、PlayChoice-10、Sharp C1、Famicom Titler の RGB 出力段の部品値。
- MAX999 と MCP6561 の一次データシート（ミラーと検索要約のみ）。
- PPUdigitizer の内部方式と FPGA の型番、Hi-Def NES のスプライト判定の方法。
- ライセンス: Lava RGB（表示なし）、LAVA_RGB-TO-PPU_LITE（LICENSE ファイルが見つからない）、FirebrandX のパレット（記載なし）、エミュレータ同梱のパレット（個別未確認）。
- 日本の業務用 15 kHz モニタ（Nanao MS8/MS9、Toei）の入力レベル・インピーダンス・同期のしきい値と引き込み範囲。NES 由来の 15.7458 kHz を日本の筐体で測った報告。V sync 中の serration の要求。
- JLCPCB での RP2350B / RP2354B の分類と在庫、TLV3502 と LMV7219 の分類。RP2350B を載せたモジュールの国内入手性。
- 秋月の 21.47727 MHz の水晶・発振器の取り扱い（キーワード検索で見つからず）。
- 秋月で売られている Pico 2 のステッピング（A2/A3/A4）。購入品の刻印か `rp2350_chip_version()` で確かめる。
- 2C02 の V sync 期間中の serration の正確な形。

### 3.3 実験の順序（1.9.9 節の表の要約）

1. スプライト/BG の判定（比較器を 3 通り差し替え）。
2. 3.3 V 駆動で NMOS の入力が動くか（D 線、CLK、/RST）。
3. 直列抵抗インタポーザの副作用（WRAM と MMC5 のカート）。
4. v/w 追跡の正しさ（エミュレータのログでオフライン照合）。
5. コアの更新遅延（Pico 2 を 2 枚使った擬似バス）。
6. EXT と VOUT の相対遅延と 1 画素ずれ（20 回の電源投入）。
7. 電源の順序（3V3 確立前の 5 V 信号）。
8. GPIO の割り当てと PIO 命令数の確定（机上）。
9. クロック +1058 ppm の影響（モニタの同期と音程）。
10. パレット読み出しを使うソフトの調査。

1〜3 と 6 は同じ試作基板（2C02 + Pico 2 + 比較器の差し替え）で行える。1 で比較器が決まらないと方式全体が決まらないので、最初に行う（推論）。

---

## 4. ユーザー要求への影響

この章の判断はすべて調査者の推論（**推論**）であり、根拠の事実は 1 章にある。

### 4.1 部品選定・実装ルール（1 章: Basic Parts のみ、LCSC の在庫、手はんだは秋月、部品を減らす、安価に）

- **事実**: RGB 出力版 PPU は中古のみで 1 個 110〜260 USD、品切れ。JLCPCB の Basic/Preferred には LM393 より速い比較器がない。RP2350A（C42411118）は Extended、21.47727 MHz の水晶（C5289705）も Extended。470 Ω の抵抗アレイ C25510 は Preferred Extended（Basic ではない）で、0603 の単品 470 Ω（C23179）は Basic。JAMMA 入力用の 74HC165（C5613）も Preferred Extended。秋月に Pico 2 ¥990（在庫 1,462）、ADCMP600 ¥830（在庫 220）、LM319M 5 個 ¥50。
- **推論**:
  - RGB 出力版 PPU を前提にする案は、価格と入手性で規則に合わない。
  - EXT 方式を Pico 2 で作る案は、規則に最も合う。データバスへの介入は 470 Ω の単品抵抗 8 本（Basic）だけで済み、クロックは RP2350 が作るので水晶（Extended）も要らない。部品の種類を減らすためにアレイ（C25510）を使うと Preferred Extended になり、「Basic のみ」から外れる。
  - JAMMA 入力の 74HC165 も Preferred Extended なので、「Basic のみ」を厳密に守るなら、Basic の 74HC595 と組み合わせた別の読み方（例: 595 で行を選んで GPIO で読むマトリクス）か、ユーザーに Preferred Extended を許すかの判断が要る（入力回路は本シートの範囲外）。
  - 規則と衝突するのは比較器だけである。Basic で済む候補（LM393）は速度が足りない。秋月の ADCMP600 は SOT23-5 で、手はんだには小さく「小さい部品は PCBA に任せる」方針とぶつかる。LM319M（秋月）も SO パッケージと思われる（パッケージは未確認）。
  - **推奨**: 最初の試作で、(iii) ディスクリート案（Basic のトランジスタと抵抗）、(ii) LM319、(i) ADCMP600 の順に評価する。(iii) か (ii) が通れば規則の中に収まる。どれも通らなければ、ADCMP600 を手はんだにするか、高速比較器だけ Extended で基板実装するかをユーザーに決めてもらう必要がある。

### 4.2 製品要求（2 章: CPU と PPU だけを移植するか、Raspberry Pi でエミュレートするかを選べる。ソケットで選ぶ）

- **事実**: EXT 方式は実機の 2C02 を使う。実チップモードでは PPU の EXT・VOUT・CLK・/RST とバスの信号に約 37〜41 本の GPIO が要る。
- **推論**:
  - 実チップモードの映像は、EXT 方式で映像用のマイコンが作り直す。エミュレーションモードの映像は、エミュレータのマイコンが直接作る。**どちらのモードでも、JAMMA に出る RGB と CSYNC の出力段（抵抗 DAC と NPN の同期バッファ）を 1 組にまとめ、それを駆動するマイコンを 1 枚に決める**と部品が減る。方法は 2 つ考えられる。(a) 映像用のマイコン（Pico A）がエミュレーションモードでも出力を担当し、エミュレータから画素を受け取る。(b) エミュレータを Pico A 自体で動かす。どちらが成立するかは、エミュレーション側の GPIO 予算と処理能力の検討が要る（未確認）。
  - 実チップモードでは、映像用のマイコンが止まると CPU/PPU も止まる（クロック源のため）。エミュレーションモードとの切り替えやファーム更新のときは、必ず /RST を Low に保つ。
  - モードの切り替え（ソケットにどちらを挿したか）は、PPU の有無を映像用のマイコンが確かめられる（例: クロックを出して ALE が出るかを見る）ので、DIP スイッチなしで自動判定できる可能性がある（未確認）。

### 4.3 動作方式と入力形式（3 章: タイマー方式・通常方式、デフォルト形式・特殊形式）

- **事実**: 1 ライン遅延のラインバッファ方式なら、追加のハードウェアなしで文字を重ねて描ける（1.9.8 節）。PPU には何も書かないのでゲームに影響しない。
- **推論**:
  - タイマー方式に必要な**残り時間の表示**と時間切れの予告、アトラクト時の「INSERT COIN」は、映像用のマイコンが重ね表示で描ける。市販ソフトに手を加える必要はない。これは EXT 方式でマイコンが映像を作り直すことの大きな利点で、RGB 出力版 PPU の映像をそのまま出す場合は、別の合成回路がないと重ね表示ができない。
  - 時間切れ後に「次の客が前の客の場面から始まる」問題（要求の 3.7）には、映像用のマイコンが画面全体を「INSERT COIN」画面に差し替える方法がある。ゲームのリセットはしないので、要求の読み方（3.6）と矛盾しない。
  - 入力形式（デフォルト／特殊）の変換自体はパッド応答を担当するマイコン（案 B では Pico B）の仕事で、映像には関係しない。ただし特殊形式では C・D ボタン（ピン 24・25・b・c）を読む必要があるので、JAMMA 入力のシフトレジスタは 1.9.5 節の見積もりより入力が増える。GPIO の本数は変わらない。
  - タイマー方式の割り当て（2P スタート〔U〕を I コンの SELECT に、コインはゲームに渡さず時間の加算に使う、C・D は使わない）と、時間切れ後に操作を受け付けなくする処理も、パッド応答側（Pico B）で行える。残り時間は Pico B が数え、表示内容を Pico A へリンクで送れば、映像側の追加部品は要らない。

### 4.4 切り替え手段はソフトウェア（4 章）

- **事実**: 要求では、テストスイッチ（JAMMA ピン 15）で設定画面を出し、映像をマイコンが作り直す構成なら追加部品なしで描けるとしている。
- **推論**:
  - EXT 方式なら、設定画面（方式、形式、1 コインあたりの時間など）は重ね表示か画面全体の差し替えで描ける。追加部品は要らない。この点でも EXT 方式が要求に合う。
  - 新規開発カートからの切り替え（$4016 への書き込みで OUT1・OUT2 に信号を出す）は CPU の OUT 端子を読むマイコン（案 B では Pico B）が受ける。設定が変わったら、Pico B から Pico A へ（重ね表示の内容として）リンクで知らせる。

### 4.5 マイコンの枚数と将来の更新（5 章: 何枚でもよい。CPU・PPU・メモリの更新を視野に）

- **事実**: Pico 2 ×1 では GPIO が足りない（最小 37 本）。Pico 2 ×2 なら A 23 本、B 24 本で収まる。RP2350B ×1 は 48 本で 7〜11 本余るが、QFN-80 を Extended で実装する必要がある。3-3-3 の RGB は 2C02 風のパレットには粗く、4-4-4 にすると 3 ピン増える。
- **推論**:
  - 複数枚を認める現行の要求で、**案 B（Pico 2 ×2）が規則の中で取れる構成になった**。第2次調査は案 A（RP2350B）を推奨していたが、それは Basic のみという規則を外れる。
  - **推奨: 試作 1 回目は案 B（Pico 2 ×2）で作る。** 理由は、(1) 秋月の完成品モジュールで組めて Basic 以外の部品を基板実装に頼らない、(2) 試作の実験（1.9.9 節の 1〜3、5）がそのまま本番の構成で行える、(3) クロック領域が 2 つになる負担（$2001 の画面途中の変更で数十画素ずれ得る）はあるが、置き換えの判断は B の中で完結するので PPU への改変のタイミングは影響を受けない、の 3 点である。量産で Extended を許すなら、案 A に移る余地を残す。
  - 将来の色数の向上（要求の「DA 変換のビット数を多めに」）のため、**DAC は 4-4-4 以上を推奨する**。ただし Pico A は 3-3-3 で 23 本、4-4-4 では 26 本で、余りがなくなる。任意の ALE を削るか、CPU と PPU のクロックを 1 ピンにまとめて 1〜2 本空ける。5-5-5 以上にしたいなら、映像出力だけを担当する 3 枚目の Pico を置くか、案 A に移る（3 枚目の場合、画素データの受け渡しの方法は未検討）。
  - 将来の PPU の差し替えに備え、**PPU のソケットは RGB 出力版 PPU との両対応（1.6 節の条件）を残す**ことを推奨する。追加は 0Ω ジャンパと数本の配線だけである。FPGA の PPU（PPU-LITE など）への差し替えも同じソケットで受けられる可能性があるが、未確認。
  - 拡張用コネクタには、PPU の EXT0-3・VOUT・CLK・/RST と、映像用マイコンの予備端子を引き出しておくと、後から映像の処理を変えられる。

### 4.6 USB Type-C によるファームウェア更新（6 章）

- **事実**: Pico 2 の USB 端子は Micro-B で、USB の信号は 40 本の端子列に出ていない。RP2350 の USB ブートは既定で 12 MHz の入力に頼る。映像用のマイコンが止まると CPU/PPU のクロックも止まる。
- **推論**:
  - 案 B では Pico が 2 枚あるので、Type-C 端子を 1 つにまとめるには、端子につながる 1 枚がもう 1 枚を書き換えるか、USB ハブ IC を載せる（要求の 6.2 の論点どおり）。
  - 書き換え中は映像用のマイコンが止まり、CPU/PPU のクロックが止まる。**/RST を外付けプルダウンで Low に保つ設計（1.9.6 節）にしておけば、書き換え中に NMOS のチップが低速クロックの状態で動くことはない。**
  - 案 A（RP2350B）や外部発振器を XIN に入れる構成では、USB ブートが 12 MHz 前提であることに注意する（OTP の設定か別系統が要る）。Pico 2 の 12 MHz 水晶を使う案 B ではこの問題はない。

### 4.7 推奨構成のまとめ（推論）

| 項目 | 推奨 | 主な理由 | 主なリスク |
|---|---|---|---|
| RGB の方式 | EXT 方式（ドナー機の 2C02） | 規則に合い、重ね表示ができる | 前例がない |
| マイコン | Pico 2 ×2（A: クロック・リセット・映像、B: バス・入出力） | 秋月の完成品、Basic のみ | クロック領域が 2 つ |
| クロック | Pico A の PIO が 21.5 MHz（129 MHz ÷6、+1058 ppm）を出す | 完全に同期し、1 画素ずれが消える。水晶が要らない | NMOS が 3.3 V 駆動を受けるか（実験 2） |
| PPU /RST | Pico A がクロックに合わせて解除。10 kΩ プルダウン | 位相が毎回同じ | 内部同期段の有無（実験 6） |
| パレットの改変 | 470 Ω の直列抵抗（C25510 ×2）で PPU 側を置き換え | 部品最少、Basic | 置き換えの確実さ（実験 2・3） |
| PPU に書く値 | BG = $0F、スプライト = $20。強調・グレースケールは 0 に置き換え | 比較器 1 個で済む | 色番号の妥当性は実測で確認 |
| 第5ビットの比較器 | ディスクリート → LM319 → ADCMP600 の順に評価 | 規則に収まるものを優先 | 最大のリスク（実験 1） |
| 同期 | PIO のカウンタで生成し、NPN で 5 V の負極性 CSYNC に。VOUT の同期を LM393 で取って照合（任意） | 部品最少 | ドットスキップの判定タイミング |
| DAC | 4-4-4 以上の重み付け抵抗。開放 3.0 V、100〜150 Ω | 将来の色数向上 | Pico A の GPIO に余りがない |
| 重ね表示 | ラインバッファに文字を書く | 残り時間、INSERT COIN、設定画面 | なし（ソフトのみ） |
| ソケット | RGB 出力版 PPU との両対応（pin14〜17、21、12 のジャンパ） | 将来の差し替え | pin17 を GND に直結しないこと |
| パレット | pally（MIT-0）で 2C02G の 512 色を生成。2C03 の表も選べる | 権利の面で安全 | なし |

---

## 5. 出典一覧

### 冒頭の結論と 1.1（方式の一覧と比較）

- NESdev Wiki: PPU pinout（RGB 出力版 PPU のピン、/RST、VOUT 増幅）— https://www.nesdev.org/wiki/PPU_pinout
- NESdev Wiki: PPU pinout（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml
- NESRGB 公式ページ（動作原理）— https://etim.net.au/nesrgb/
- NESdev forum t=20636（Quietust の EXT 方式の説明）— https://forums.nesdev.org/viewtopic.php?t=20636
- Nerdly Pleasures「NES hardware explained」（BG 全黒・スプライト全白、検索スニペットのみ）— http://nerdlypleasures.blogspot.com/2015/06/nes-hardware-explained.html
- NESdev forum t=9503 アーカイブ（RGB 改造の互換性、lidnariq の VOUT 標本化の言及）— https://nesdev.nes.science/f9/t9503.xhtml
- nicole.express「That Blasted RGB」（RGB Blaster）— https://nicole.express/2023/that-blasted-rgb.html
- NESdev forum t=26258（PPU-LITE、1 画素ずれ、RGB2C02N のバグ）— https://forums.nesdev.org/viewtopic.php?t=26258
- GDM 2024-01-12（RGB2C02N の価格、検索要約経由）— https://gdm.or.jp/crew/2024/0112/521851
- GDM 2022-03-08（日本語のショップ記事）— https://www.gdm.or.jp/crew/2022/0308/430728
- Arcade-Museum WTB: RP2C03 PPU（相場）— https://forums.arcade-museum.com/threads/wtb-rp2c03-ppu.506933/
- PicClick（RP2C03B の落札）— https://picclick.com/PLAYCHOICE-10-PC10-Nintendo-RP2C03B-PPU-Tested-Working-172533176401.html
- tall-dog（RGB 出力版 PPU の販売、Sold Out）— https://shop.tall-dog.com/products/rgb-format-nes-core-ppu-chip
- RP2040 PIO の PAL 映像生成の例（汎用例）— https://codeberg.org/chipfire/rppico-pio-pal
- SamDelorean/gameboy-rp2c02-crt-adapter README — https://raw.githubusercontent.com/SamDelorean/gameboy-rp2c02-crt-adapter/main/README.md
- NTSC video（VOUT の構造とデコーダ）— https://www.nesdev.org/wiki/NTSC_video

### 1.2（EXT 端子の挙動と追跡すべき内部状態）

- NESdev Wiki: PPU programmer reference — https://www.nesdev.org/wiki/PPU_programmer_reference
- 同（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_programmer_reference.xhtml
- NESdev Wiki: PPU registers — https://www.nesdev.org/wiki/PPU_registers
- 同（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_registers.xhtml
- NESdev Wiki: PPU palettes — https://www.nesdev.org/wiki/PPU_palettes
- NESdev Wiki: Myths — https://www.nesdev.org/wiki/Myths
- NESdev Wiki: PPU scrolling（本文未取得）— https://www.nesdev.org/wiki/PPU_scrolling
- NESdev Wiki: Visual 2C02 — https://www.nesdev.org/wiki/Visual_2C02
- NESdev forum t=14078（EXT 入力の意味、Ueda 1989 論文）— https://forums.nesdev.org/viewtopic.php?t=14078
- nesdev.nes.science t9936（Wiki の文言検証）— https://nesdev.nes.science/f3/t9936.xhtml
- NESdev forum t=16479（2 PPU 構成）— https://forums.nesdev.org/viewtopic.php?t=16479
- Breaking NES Wiki: Multiplexer — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/mux.md
- Breaking NES Wiki: pads.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md
- Breaking NES Wiki: pads_ext.jpg — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/pads_ext.jpg
- Breaking NES Wiki: pclk.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pclk.md
- Breaking NES Wiki: CRAM — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/cram.md
- Breaking NES Wiki: regs.md（レジスタの非同期性、w の挙動）— https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/regs.md
- NESRGB operation block diagram — https://etim.net.au/nesrgb/operation_block_diagram.png
- NESRGB Software and Errata — https://etim.net.au/nesrgb/background_fault/
- NESdev forum t=9561 p.4（viletim の改変パレットの説明）— https://forums.nesdev.org/viewtopic.php?t=9561&start=45
- NESdev forum t=25963（Lava RGB）— https://forums.nesdev.org/viewtopic.php?t=25963
- Hi-Def NES スレッド アーカイブ t12019 — https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- 同（旧アーカイブ）— https://nesdev.nes.science/f9/t12019.xhtml
- lava-rgb-kit（回路図・BOM・ファーム）— https://github.com/v5100v5100/lava-rgb-kit
- TinyNES Main Board Schematic — https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf
- NESdev Wiki: MMC5（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/MMC5.xhtml
- NESdev forum t=19656 p.2（2A03/2C02 の VOH 約 4 V）— https://forums.nesdev.org/viewtopic.php?t=19656&start=15

### 1.3（スプライトと背景の判別、比較器）

- NESdev Wiki: NTSC video（出力レベル）— https://www.nesdev.org/wiki/NTSC_video
- NESdev forum t=2113（kevtris の実測）— https://forums.nesdev.org/viewtopic.php?t=2113
- NESdev forum t=9561 p.2（ディスクリート比較器の議論）— https://forums.nesdev.org/viewtopic.php?t=9561&start=15
- TI LM393 — https://www.ti.com/lit/ds/symlink/lm393.pdf
- TI LM339 — https://www.ti.com/lit/ds/symlink/lm339.pdf
- TI LM311 — https://www.ti.com/lit/ds/symlink/lm311.pdf
- TI LM119/LM319 — https://www.ti.com/lit/ds/symlink/lm119.pdf
- TI LMV7219 — https://www.ti.com/lit/ds/symlink/lmv7219.pdf
- TI TLV3501 — https://www.ti.com/lit/ds/symlink/tlv3501.pdf
- TI TLV3502 — https://www.ti.com/lit/ds/symlink/tlv3502.pdf
- MAX999（elecfans の二次ミラー）— https://pdf.elecfans.com/MAXIM/MAX999.html
- TI SN74HC14 — https://www.ti.com/lit/ds/symlink/sn74hc14.pdf
- 秋月 130362（ADCMP600BRJZ-R2、LM319M の関連表示）— https://akizukidenshi.com/catalog/g/g130362/
- 秋月 130361（LTC6752HS5）— https://akizukidenshi.com/catalog/g/g130361/
- NESRGB5 test mode（v5 の比較器と映像部）— https://etim.net.au/nesrgb5/testmode/
- lava-rgb-kit（BOM）— https://github.com/v5100v5100/lava-rgb-kit
- NESdev forum t=25963（Lava のしきい値と WDL6528）— https://forums.nesdev.org/viewtopic.php?t=25963
- NESdev forum t=26258（スプライト縁のにじみ）— https://forums.nesdev.org/viewtopic.php?t=26258
- JLCPCB の部品分類（parts_class_reverification.md の JLCPCB API 全件照会。URL はノートに記載なし）

### 1.4（既存製品・既存設計）

- NESRGB 公式 — https://etim.net.au/nesrgb/
- NESRGB40 — https://etim.net.au/nesrgb/NESRGB40.html
- NESRGB5 — https://etim.net.au/nesrgb5/
- NESRGB-Pinout.pdf — https://etim.net.au/nesrgb/NESRGB-Pinout.pdf
- De-jitter For NESRGB — https://etim.net.au/nesrgb/background_fault/de-jitter.html
- snes_dejitter README — https://raw.githubusercontent.com/marqs85/snes_dejitter/master/README.md
- lava-rgb-kit — https://github.com/v5100v5100/lava-rgb-kit
- v5100v5100 のリポジトリ一覧（Breaking NES のライセンス表示）— https://github.com/v5100v5100?tab=repositories
- PPU-LITE README — https://raw.githubusercontent.com/andkorzh/PPU-LITE/main/README.md
- PPU-LITE LICENSE — https://raw.githubusercontent.com/andkorzh/PPU-LITE/main/LICENSE
- LAVA_RGB-TO-PPU_LITE README — https://raw.githubusercontent.com/andkorzh/LAVA_RGB-TO-PPU_LITE/main/README.md
- RP2C02-7- — https://github.com/andkorzh/RP2C02-7-
- LumaCode Wiki: PPUdigitizer (for NES) — https://github.com/c0pperdragon/LumaCode/wiki/PPUdigitizer-(for-NES)
- LumaCode リポジトリ — https://github.com/c0pperdragon/LumaCode
- c0pperdragon のリポジトリ一覧 — https://github.com/c0pperdragon?tab=repositories
- LumaCode issue #20 — https://github.com/c0pperdragon/LumaCode/issues/20
- zdziarski.com blog 2026-02（PPUdigitizer）— https://www.zdziarski.com/blog/?m=202602
- Hi-Def NES スレッド アーカイブ — https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- nicole.express（RGB Blaster）— https://nicole.express/2023/that-blasted-rgb.html
- GDM 2024-01-12（RGB2C02N）— https://gdm.or.jp/crew/2024/0112/521851
- TinyNES Main Board Schematic — https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf
- TinyNES Main Board BOM — https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_BOM.csv
- TinyNES RGB Board Schematic — https://raw.githubusercontent.com/loglow/TinyNES/main/RGB%20Board/TinyNES_RGB_Board_Schematic.pdf
- TinyNES RGB Board BOM — https://raw.githubusercontent.com/loglow/TinyNES/main/RGB%20Board/TinyNES_RGB_Board_BOM.csv
- Crowd Supply（TinyNES のジャンパ基板、検索要約経由）— https://www.crowdsupply.com/tall-dog-electronics/tinynes/updates/orders-shipped-and-jumper-board-fix
- tall-dog shop（TinyNES RGB キットの対応品種、検索要約経由）— https://reach.dog/shop/tall-dog-electronics/products/tinynes-rgb-video-kit
- arcade-projects NES2JAMMA — https://www.arcade-projects.com/threads/nes2jamma.2779/

### 1.5（画素の位置合わせ、リセット、クロック）

- NESdev Wiki: PPU pinout — https://www.nesdev.org/wiki/PPU_pinout
- Breaking NES Wiki: pads.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md
- Breaking NES Wiki: hv.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/hv.md
- Breaking NES Wiki: pclk_reset.png — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/pclk_reset.png
- Breaking NES Wiki: pclk.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pclk.md
- NESdev Wiki: User:Fiskbit（CPU の分周器はリセットされない）— https://www.nesdev.org/wiki/User:Fiskbit
- NESdev forum t=6186（blargg、4 通りの位相）— https://forums.nesdev.org/viewtopic.php?t=6186
- NESdev Wiki: PPU frame timing — https://www.nesdev.org/wiki/PPU_frame_timing
- NESdev Wiki: PPU power up state — https://www.nesdev.org/wiki/PPU_power_up_state
- Breaking NES Wiki: APU clkgen — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/APU/clkgen.md
- Breaking NES Wiki: APU pads — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/APU/pads.md
- NESdev forum t=13993（M2 はリセット中も動く、検索要約経由）— https://forums.nesdev.org/viewtopic.php?t=13993
- NESdev forum t=25963（Lava の /CE と ALE の遅延）— https://forums.nesdev.org/viewtopic.php?t=25963
- NESdev forum t=26258（andkorzh の同期の発言）— https://forums.nesdev.org/viewtopic.php?t=26258
- Hi-Def NES スレッド アーカイブ — https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- NESRGB operation block diagram — https://etim.net.au/nesrgb/operation_block_diagram.png
- lava-rgb-kit（ファーム更新履歴の FIFO）— https://github.com/v5100v5100/lava-rgb-kit
- TinyNES Main Board Schematic（クロック分配）— https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf

### 1.6（RGB 出力版 PPU のピンと両対応ソケット）

- NESdev Wiki: PPU pinout — https://www.nesdev.org/wiki/PPU_pinout
- NESdev Wiki: PPU palettes — https://www.nesdev.org/wiki/PPU_palettes
- NESdev Wiki: PPU variants — https://www.nesdev.org/wiki/PPU_variants
- NESdev Wiki: Vs. System — https://www.nesdev.org/wiki/Vs._System
- NESdev Wiki: PPU registers（2C05 の ID）— https://www.nesdev.org/wiki/PPU_registers
- NESdev Wiki: User:Forple — https://www.nesdev.org/wiki/User:Forple
- NESdev Wiki: X0858CE — https://www.nesdev.org/wiki/X0858CE
- NESdev forum t=15541 アーカイブ（tepples、2C03 と 2C02 の差）— https://nesdev.nes.science/f2/t15541.xhtml
- NESdev forum t=9503 アーカイブ（互換性）— https://nesdev.nes.science/f9/t9503.xhtml
- Breaking NES Wiki: RGB PPU — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md
- Breaking NES Wiki: RGB_DACs.png — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/rgb/RGB_DACs.png
- Breaking NES Wiki: RGB_SYNC.png — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki/imgstore/ppu/rgb/RGB_SYNC.png
- Breaking NES Wiki: PPU Readme（改版表）— https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/Readme.md
- TinyNES RGB Board Schematic — https://raw.githubusercontent.com/loglow/TinyNES/main/RGB%20Board/TinyNES_RGB_Board_Schematic.pdf
- TinyNES RGB Board BOM — https://raw.githubusercontent.com/loglow/TinyNES/main/RGB%20Board/TinyNES_RGB_Board_BOM.csv
- TinyNES Main Board Schematic — https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf
- nfggames NES RGB mod（2005 年の改造スレッド）— https://nfggames.com/forum2/index.php?topic=1592.0
- elektrotanya（VS. System 回路図、本文未取得）— https://elektrotanya.com/nintendo_vs_sch.pdf/download.html
- tall-dog（価格と在庫）— https://shop.tall-dog.com/products/rgb-format-nes-core-ppu-chip
- tall-dog shop（RGB キット、検索要約経由）— https://reach.dog/shop/tall-dog-electronics/products/tinynes-rgb-video-kit

### 1.7（映像タイミングと同期）

- NESdev Wiki: NTSC video — https://www.nesdev.org/wiki/NTSC_video
- NESdev Wiki: PPU frame timing — https://www.nesdev.org/wiki/PPU_frame_timing
- NESdev Wiki: PPU frame timing（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_frame_timing.xhtml
- NESdev Wiki: Cycle reference chart（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/Cycle_reference_chart.xhtml
- NESdev Wiki: PPU rendering（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_rendering.xhtml
- Breaking NES Wiki: RGB PPU（ドットスキップ回路の切断）— https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md
- NESdev Wiki: PPU variants — https://www.nesdev.org/wiki/PPU_variants
- NESRGB operation block diagram — https://etim.net.au/nesrgb/operation_block_diagram.png
- NESRGB-Pinout.pdf — https://etim.net.au/nesrgb/NESRGB-Pinout.pdf
- De-jitter For NESRGB — https://etim.net.au/nesrgb/background_fault/de-jitter.html
- NESRGB Software and Errata — https://etim.net.au/nesrgb/background_fault/
- NESdev forum t=25963 — https://forums.nesdev.org/viewtopic.php?t=25963
- lava-rgb-kit — https://github.com/v5100v5100/lava-rgb-kit
- Hi-Def NES スレッド アーカイブ — https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- K7000 Service Manual（archive.org）— https://dn760108.eu.archive.org/0/items/k-7000-1/K7000-1_text.pdf
- Hantarex MTC 9000 manual（archive.org）— https://archive.org/stream/ArcadeGameManualMtc9000/mtc9000_djvu.txt
- PlayChoice-10 Operation Manual（archive.org）— https://archive.org/details/pc10operationmanualpch1-up
- shmups「NES/SNES 240p dejitter mod」（検索要約経由）— https://shmups.system11.org/viewtopic.php?t=61285
- Sega Blast City Wiring Guide（Arcade Otaku Wiki、同期の極性）— https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide

### 1.8（パレットデータ、強調とグレースケール）

- NESdev Wiki: PPU palettes — https://www.nesdev.org/wiki/PPU_palettes
- NESdev Wiki: Nesdev Wiki（コンテンツのライセンス表示なし）— https://www.nesdev.org/wiki/Nesdev_Wiki
- FirebrandX NES palette — https://www.firebrandx.com/nespalette.html
- pally LICENSE — https://raw.githubusercontent.com/Gumball2415/pally/main/LICENSE
- palgen-persune LICENSE — https://raw.githubusercontent.com/Gumball2415/palgen-persune/main/LICENSE
- lava-rgb-kit（.jed 名のパレット）— https://github.com/v5100v5100/lava-rgb-kit
- LAVA_RGB-TO-PPU_LITE README — https://raw.githubusercontent.com/andkorzh/LAVA_RGB-TO-PPU_LITE/main/README.md
- NESRGB 公式（初期の内蔵パレット）— https://etim.net.au/nesrgb/
- NESRGB Software and Errata / NESRGB40（内蔵パレット）— https://etim.net.au/nesrgb/background_fault/ ／ https://etim.net.au/nesrgb/NESRGB40.html
- NESdev Wiki: NTSC video（強調の減衰係数）— https://www.nesdev.org/wiki/NTSC_video
- NESdev Wiki: PPU registers — https://www.nesdev.org/wiki/PPU_registers
- NESdev Wiki: PPU variants — https://www.nesdev.org/wiki/PPU_variants
- Breaking NES Wiki: RGB PPU — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md
- Breaking NES Wiki: CRAM — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/cram.md
- NESdev forum t=25963（グレースケールの AND $30）— https://forums.nesdev.org/viewtopic.php?t=25963

### 1.9（Pico 2 / RP2350 での実現）

- RP2350 Datasheet（Release 8、Build date 01/10/2026）— https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- Hardware design with RP2350 — https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- Raspberry Pi news「RP2350 A4, RP2354 and a new hacking challenge」（5V 耐性、E9 の修正）— https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/
- TI SN74HC245 — https://www.ti.com/lit/ds/symlink/sn74hc245.pdf
- TI SN74HC14 — https://www.ti.com/lit/ds/symlink/sn74hc14.pdf
- TI SN74HC595 — https://www.ti.com/lit/ds/symlink/sn74hc595.pdf
- TI SN74HCT245 — https://www.ti.com/lit/ds/symlink/sn74hct245.pdf
- NESdev Wiki: NTSC video（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/NTSC_video.xhtml
- NESdev Wiki: CPU pinout（静的ミラー、M2 のデューティ）— https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml
- NESdev Wiki: PPU pinout（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml
- NESdev Wiki: PPU registers（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_registers.xhtml
- NESdev Wiki: PPU programmer reference（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_programmer_reference.xhtml
- NESdev Wiki: Standard controller（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/Standard_controller.xhtml
- NESdev Wiki: MMC5（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/MMC5.xhtml
- NESdev Wiki: Talk:Cartridge connector（入力は TTL しきい値と仮定）— https://www.nesdev.org/wiki/Talk:Cartridge_connector
- NESdev forum t=19483（2A03 の書き込みサイクルの実測）— https://forums.nesdev.org/viewtopic.php?t=19483
- NESdev forum t=19656 p.2（VOH 約 4 V）— https://forums.nesdev.org/viewtopic.php?t=19656&start=15
- Breaking NES Wiki: PPU regs.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/regs.md
- Breaking NES Wiki: PPU pads.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md
- NESdev Wiki: User:Fiskbit — https://www.nesdev.org/wiki/User:Fiskbit
- Hi-Def NES スレッド アーカイブ（約 0.15% の低速化）— https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- TinyNES Main Board BOM（3.3 V クロック駆動）— https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_BOM.csv
- NESdev forum アーカイブ t4698（2A03 を 3.3 V CPLD で駆動）— https://archive.nes.science/nesdev-forums/f9/t4698.xhtml
- emulationonline chiplab（2A03 は低速クロック不可）— https://emulationonline.neocities.org/systems/chiplab/experimenting-with-highspeed-chips/
- 秋月 129604（Raspberry Pi Pico 2）— https://akizukidenshi.com/catalog/g/g129604/
- 秋月 130370（RP2350B）— https://akizukidenshi.com/catalog/g/g130370/
- 秋月 131441（RP2354B）— https://akizukidenshi.com/catalog/g/g131441/
- 秋月 131106（AE-QFN60-7X7-0.4）— https://akizukidenshi.com/catalog/g/g131106/
- 秋月 110679（Si5351A モジュール）— https://akizukidenshi.com/catalog/g/g110679/
- 秋月 111328（TC74HCU04AP）— https://akizukidenshi.com/catalog/g/g111328/
- 秋月 130362（ADCMP600）— https://akizukidenshi.com/catalog/g/g130362/
- 秋月 130361（LTC6752）— https://akizukidenshi.com/catalog/g/g130361/
- TI LM393 / LM119 — https://www.ti.com/lit/ds/symlink/lm393.pdf ／ https://www.ti.com/lit/ds/symlink/lm119.pdf
- PICO9918 v2.0 回路図（4 bit 重み付け抵抗 DAC）— https://github.com/visrealm/pico9918/blob/main/pcb/v2.0/pico9918_v2_0_schematic.pdf
- NeoGeo Dev Wiki: Video DAC — https://wiki.neogeodev.org/index.php?title=Video_DAC&action=raw
- MAME neogeo_v.cpp — https://raw.githubusercontent.com/mamedev/mame/master/src/mame/snk/neogeo_v.cpp
- MAME segaic16.cpp — https://raw.githubusercontent.com/mamedev/mame/master/src/mame/sega/segaic16.cpp
- Blast City Bass Fishing 版取説（2kΩ / 3.0Vp-p）— https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf
- Sega Blast City Wiring Guide（Arcade Otaku Wiki）— https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide
- K7000 Service Manual — https://dn760108.eu.archive.org/0/items/k-7000-1/K7000-1_text.pdf
- Hantarex MTC 9000 manual — https://archive.org/stream/ArcadeGameManualMtc9000/mtc9000_djvu.txt
- 部品分類（JLCPCB の C 番号と Basic/Extended）は parts_class_reverification.md の JLCPCB API 照会による（URL はノートに記載なし）
- PLL の全探索は調査者のスクリプト（/tmp/p2f/scripts/pll.py、結果は rgb_pico2_feasibility.md の付記に転記）

### 1.10（RP2C02 のピン）

- NESdev Wiki: PPU pinout — https://www.nesdev.org/wiki/PPU_pinout
- NESdev Wiki: PPU pinout（静的ミラー）— https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml
- nocash Everynes — https://problemkaputt.de/everynes.htm
- OpenFC（HVC-CPU-07 のネットリスト）— https://github.com/starlightk7/OpenFC
- TrexMakes Nintendo_Famicom_Console（HVC-CPU-GPM-02 / HVC-CPU-07 のネットリスト）— https://codeberg.org/TrexMakes/Nintendo_Famicom_Console
- OpenTendo（NES-CPU のネットリスト）— https://github.com/Redherring32/OpenTendo
- HVC-CPU-05 トレース回路図 Rev.07 — https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf
- TinyNES Main Board Schematic（コンポジット増幅の定数）— https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf
- NESdev forum t=2113（kevtris の実測は NES 上）— https://forums.nesdev.org/viewtopic.php?t=2113

### 2（第1次調査からの訂正）

- NESdev Wiki: PPU variants — https://www.nesdev.org/wiki/PPU_variants
- NESdev Wiki: X0858CE — https://www.nesdev.org/wiki/X0858CE
- LumaCode Wiki: PPUdigitizer (for NES) — https://github.com/c0pperdragon/LumaCode/wiki/PPUdigitizer-(for-NES)
- lava-rgb-kit — https://github.com/v5100v5100/lava-rgb-kit
- NESRGB5 test mode — https://etim.net.au/nesrgb5/testmode/
- Raspberry Pi news（5V 耐性）— https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/
- RP2350 Datasheet（Table 1674、§8.1.2.4、§8.6.1）— https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- Hardware design with RP2350 — https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- TI LM393 — https://www.ti.com/lit/ds/symlink/lm393.pdf
- TI LM311 — https://www.ti.com/lit/ds/symlink/lm311.pdf
- TI SN74HC245 — https://www.ti.com/lit/ds/symlink/sn74hc245.pdf
- NESdev Wiki: PPU pinout — https://www.nesdev.org/wiki/PPU_pinout
- NESdev Wiki: PPU pinout（静的ミラー、タンタルの付け方）— https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml
- NESdev Wiki: User:Fiskbit — https://www.nesdev.org/wiki/User:Fiskbit
- Breaking NES Wiki: pclk.md — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pclk.md
- Breaking NES Wiki: RGB PPU — https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/rgb.md
- nfggames NES RGB mod — https://nfggames.com/forum2/index.php?topic=1592.0
- TinyNES Main Board Schematic — https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_Schematic.pdf
- OpenFC（ファミコンのコンポジット増幅のネットリスト）— https://github.com/starlightk7/OpenFC
- Hi-Def NES スレッド アーカイブ — https://archive.nes.science/nesdev-forums/f9/t12019.xhtml
- NESdev forum t=9561 p.4 — https://forums.nesdev.org/viewtopic.php?t=9561&start=45
- NESdev Wiki: NTSC video — https://www.nesdev.org/wiki/NTSC_video
- NESdev forum t=19656 p.2 — https://forums.nesdev.org/viewtopic.php?t=19656&start=15
- 秋月 130362 / 130361 — https://akizukidenshi.com/catalog/g/g130362/ ／ https://akizukidenshi.com/catalog/g/g130361/
- Blast City Bass Fishing 版取説 — https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf

### 3（未確認事項と実機での確認）

- 3 章の項目は 1 章と 2 章の出典に基づく。追加の出典はない。取得できなかった経路（再調査用）は次のとおり。
- consolemods（PlayChoice-10 PPU Mod、Cloudflare/403）— URL はノートに記載なし
- Microchip（MCP6561）・analog.com（MAX999）のデータシート（403 / 503）— URL はノートに記載なし
- Tindie（PPUdigitizer の製品ページ、403）— URL はノートに記載なし
- talldog.dozuki.com（TinyNES RGB の取り付けガイド、サイト停止）— URL はノートに記載なし
- elektrotanya（VS. System 回路図、本文未取得）— https://elektrotanya.com/nintendo_vs_sch.pdf/download.html

### 4（ユーザー要求への影響）

- 4 章は 1 章の事実と user_requirements.md に基づく調査者の推論で、追加の出典はない。部品の価格と在庫は 1.3 節と 1.9 節の秋月のページ、JLCPCB の分類は parts_class_reverification.md による。
