# JAMMA 基板の電気的実装規約 — 日本のキャンディ筐体向け(第2パス・ギャップ埋め)

調査日 2026-11-10。`jamma_standard.md`(第1パス)の Gaps を埋めるための調査。
一次資料として、hard--candy.com が公開している筐体取扱説明書・配線図のスキャン(Sega Astro City / New Astro City / Blast City(Bass Fishing 版)、Taito Egret II、Konami Windy、Namco Cyber Lead)を画像で読み取った。スキャン画像の読み取りなので、図面の細部は「図面読み取り」と注記した。
表記: 出典の無い自分の工学的判断は **(推論)**、確認できなかったものは **未確認**。

---

## 1. 筐体・モニタの映像入力仕様と同期の受入範囲

### Takeaway
日本の JAMMA 筐体の映像入力の基準値は、**正極性アナログ RGB、約 3 Vp-p、入力インピーダンス約 2 kΩ、負極性コンポジット同期(TTL レベル)** である(Sega Blast City 取説の明記値)。75 Ω / 0.7 Vp-p は、同じ筐体の D-SUB15 入力(NAOMI など)側の設定で、JAMMA(AMP 6P)側の設定ではない。欧米のモニタシャーシの仕様も、RGB 1(または 2)~5 Vp-p、4.7 kΩ 前後、水平 15~16 kHz(K7000 は 15.1~16.8 kHz)、垂直 45/47~63/70 Hz で、上の基準値と同じ範囲に入る。レベルの違いは、モニタ側の CONTRAST(ゲイン)と入力切替で吸収する運用である。

### Cited Findings

**筐体別の一次資料**

| 筐体 | モニタ(資料記載) | 映像入力・同期・周波数の記述 | 出典 |
|---|---|---|---|
| Sega Blast City(Bass Fishing 版取説 p.49) | 29" 3-mode(Nanao MS-2931) | SW3 で切替: "When inputting D-SUB MINI 15P: 75Ω / 0.7Vp-p"(ON)、"When inputting AMP 6P: 2kΩ / 3.0Vp-p"(OFF)。SW1/SW2 で 15 kHz/24 kHz/31 kHz モード。"correct images can not be obtained unless the settings of the horizontal frequency or video input connector (input impedance/input level) are compatible with the board." | [BlastCityBassFishing-Manual.pdf](https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf) |
| Sega Blast City(JAMMA 変換) | — | "Video Signal = POSITIVE, 3.0Vp-p, 2kΩ Impedance & SYNC = NEGATIVE, H/V Composite"(第1パスで引用済み) | [Arcade Otaku Wiki Blast City](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide) |
| Sega Astro City(取説 p.8) | ナナオ 200-5242-15/-24、三和電気 200-5243-15/-24 の2社 | "SYSTEM 24 用の水平周波数 24.83 KHz の中解像度モード(24Kモード)と通常の GAME BD 用の水平周波数 15.7 KHz の低解像度モード(15Kモード)を切り替えられます。モードの切り替えはモニターメイン基板のコネクタを差し替える"。メーカーごとに調整方法が異なる旨の注意あり | [AstroCityMan.pdf](https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf) |
| Sega New Astro City(Serviceman Manual 420-6294-01 p.17) | NANAO 200-5242-15-04(15K)/-24-04(24K) | "When replacing the GAME BD, the above-mentioned monitor frequency change and ④CONTRAST adjustment may be required depending on the game contents." | [NewAstroCity-Manual.pdf](https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf) |
| Namco Cyber Lead(取説 p.68「10. 仕様」) | Nanao 29"(二次資料) | "対応ゲームPCボード JAMMA VIDEO規格(JVS)ゲームPCボード(水平同期周波数 15.75kHz, 24.83kHz) *JAMMA規格ゲームPCボードは、オプション対応により使用可能" | [CyberLead-Manual.pdf](https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf) |
| Taito Egret II(配線図 W1000310B) | VIDEO Assy 29INCH(R, G, BL, SYNC, GND) | 映像レベルの記載なし。JAMMA 13/P/14 が VIDEO B/SYNC/GND | [Egret II Schematics.jpg](https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg) |
| Konami Windy(束線図 5-10) | 29inch MONITOR(SYNC, GND, BLUE, GREEN, RED) | 映像レベルの記載なし | [Windy Specs.jpg](https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg) |

**モニタの型式(二次資料: hard--candy の筐体データベース)**: Astro City = Nanao MS8-29FSG?、New Astro City / Versus City = Nanao MS9-29A、Egret II = Nanao MS9-29T、Windy = Toshiba PB-6643(15/24 kHz)、Windy II = Toshiba PB-7534(15/24/31 kHz)、Exceleena 2 = "29 Nanao MS8. TOEI TCL2xx. SANWA PM1745"、Neo Candy 29 = Hitachi GMK-29FS2、Egret 3 = Toshiba K29CQ50(15/24/31 kHz)、Cyber Lead = Nanao MS9?、Cyber Lead II = Nanao 15/24/31 kHz — [hard--candy cabinet list](https://www.hard--candy.com/wiki/candy-cabinets) と各ページ(例: [Windy](https://www.hard--candy.com/wiki/candy/Windy)、[Egret II](https://www.hard--candy.com/wiki/candy/Egret_II))

**シャーシのサービスマニュアル**

| シャーシ | RGB 入力 | 同期 | 水平 | 垂直 | 出典 |
|---|---|---|---|---|---|
| Wells-Gardner K7000 | "RGB analog, [1?] to 5v peak-to-peak (adjustable with contrast control), 4.7k ohm input impedance"(OCR が崩れており下限値は "Ту" と読める)。オプションで "RGB analog 0-0.75v, 75 ohm input impedance" | "TTL positive or negative going, separate or composite. Input impedance: 20K ohms for positive going sync; 12K ohms for negative going sync." コンポジット同期は "use the horizontal sync input of the same polarity" | "15.1 kHz to 16.8 kHz standard" | "47 Hz to 63 Hz" | [K7000 Service Manual (archive.org)](https://dn760108.eu.archive.org/0/items/k-7000-1/K7000-1_text.pdf) |
| Hantarex MTC 9000 | "RGB anal/TTL compat., positive, white (high-level)、2-5 V p.p. (by use of input switch)"。"The three RGB video amplifiers are d.c. coupled" | Composite / separate とも "1.5 - 5 V p.p. positive/negative (switchable by switch on p.c.b.)" | "15-16 kHz"(H freq 調整範囲 "15.625 +/- 0.3 kHz") | "45-70 Hz" | [MTC 9000 manual (archive.org)](https://archive.org/stream/ArcadeGameManualMtc9000/mtc9000_djvu.txt) |
| Hantarex MTC 900 | 約 1~10 Vpp(抽出テキストが崩れている)、校正目標 "1 Vpp ±5%" | 約 1.5~5.5 Vpp、極性はスイッチ CY | — | — | [manualslib MTC 900](https://www.manualslib.com/manual/1710685/Hantarex-Mtc-900.html?page=8)(検索要約経由) |
| Nanao MS9-29 | 未確認(一次資料は取得できず) | 未確認 | 15 kHz / 24 kHz(手動切替、最終世代は自動) | 未確認 | [mikejmoffitt MS9 notes](http://mikejmoffitt.com/pages/ms9-hax/)、[gamerepair.info](https://gamerepair.info/hardware/35_nanao_ms9_29)(検索要約経由) |

- MS9 について: "The MS9's PLL is known for being fairly robust"、"Strange scan rates and sync pulse widths / placements are handled with grace"、垂直ホールド調整は無い。リモート基板の Contrast は "unity gain control across all three video channels" — [mikejmoffitt.com MS9](http://mikejmoffitt.com/pages/ms9-hax/)
- MS8 の利用者報告: "0.7V RGB and -0.3V Csync"の組合せで、RGB に 270 Ω、同期に 680~750 Ω を直列に入れる案が出ている。Astro City のモニタのリモート基板には "video impedance" 切替スイッチがあり、設定を誤ると極端に明るいか暗い画面になる、という報告もある(フォーラム、確度は低い) — [arcade-projects "Video impedance selector"](https://www.arcade-projects.com/threads/video-impedance-selector.18012/)(検索要約経由)
- 一般論: "TTL level amplitude (3-5 Vpp)"、モニタ入力は "(1-5k ohms)" — [etim.net.au AV-Driver Arcade](https://etim.net.au/av-driver/arcade/)。"1k-10k ohms" — [gbs-control wiki](https://github.com/ramapcsx2/gbs-control/wiki/Arcade-Boards)
- 歴史的経緯: 1992 年の記事は "tentative AMOA standards" がロジック基板の最大映像出力を 2 V としていたと紹介している。初期の任天堂ゲームは負極性(反転)映像で、Sanyo モニタには "video inverter" 基板(2SC1815×3)が載っていた — [Mike's Arcade "Video Inversion and You!"](https://www.mikesarcade.com/cgi-bin/spies.cgi?action=url&type=info&page=vidinvrt.txt)

### Inferences
- (推論)日本の筐体で最も厳しい既知の条件は、Blast City の JAMMA 側の 2 kΩ / 3.0 Vp-p。これと Hantarex の 2 Vp-p 下限、K7000 の 4.7 kΩ から、**基板は 2 kΩ 負荷で 2.5~3.0 Vp-p(黒 0 V、DC 結合)を出せればよい**。
- (推論)水平 15.7458 kHz / 垂直 60.10 Hz(§3)は、K7000 の 15.1~16.8 kHz、MTC 9000 の 15.625 ± 0.3 kHz(上限 15.925 kHz)と 45~70 Hz、日本筐体の公称 15.7 / 15.75 kHz のいずれにも収まる。

### Gaps
- Nanao MS8/MS9 と Toei の、入力インピーダンス・入力レベル・水平と垂直の引込み範囲は**未確認**。MS9 の正式マニュアルは Sega Touring Car の取説に同梱されている(p.136~)らしいが、取得できなかった。arcadeotaku wiki は Anubis でブロックされ、Wayback も接続できなかった。
- Exceleena / Windy / Egret II の取説で、映像入力レベルを明記した箇所は見つからなかった(Egret II は全50ページを縮小画像で確認、Windy は配線図を確認)。

---

## 2. 実在する基板の RGB 出力段と、新基板の出力レベル・出力インピーダンス

### Takeaway
実在する JAMMA 基板は、**TTL/LS ゲートで駆動する抵抗 DAC をそのままエッジに出す**のが標準である(Neo Geo: 220/470/1k/2.2k/3.9k Ω で 0~3.5 V、Sega System 16: 250/500/1k/2k/3.9k Ω)。DAC の出力インピーダンスは約 120~130 Ω(計算)。トリマで出力を調整する慣習は基板側には無く、筐体のモニタの CONTRAST/GAIN で合わせる。75 Ω / 0.7 Vp-p 化は supergun 側の仕事で、可変抵抗による分圧か、THS73xx などのビデオバッファで行う。

### Cited Findings
- Neo Geo: 74LS273 ラッチと 74LS05 で抵抗 DAC を駆動。"The output isn't lowered like on the AES. It goes straight to the JAMMA edge as a 0~3.5V signal for the high-impedance inputs on arcade monitors."。家庭用 AES は "2200 / (6800 + 2200)" で分圧して "~0.9Vp-p max" — [NeoGeo Dev Wiki Video DAC](https://wiki.neogeodev.org/index.php?title=Video_DAC&action=raw)
- MAME の Neo Geo パレット: "resistances[] = {3900, 2200, 1000, 470, 220}"。dark ビットは 8200 Ω、shadow は 150 Ω のプルダウン — [MAME neogeo_v.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/snk/neogeo_v.cpp)
- MAME の Sega 16bit 系: "Bit 0 = 1 x 3.9K ohm / Bit 1 = 1 x 2.0K ohm / Bit 2 = 1 x 1.0K ohm / Bit 3 = 2 x 1.0K ohm / Bit 4 = 4 x 1.0K ohm"。"Another data bit is connected by a tristate buffer to the color output through a 470 ohm resistor ... halve brightness (pull-down) or double brightness (pull-up)" — [MAME segaic16.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/sega/segaic16.cpp)
- CPS1: RGB は LS07/LS367 バッファ → 抵抗アレイ(1色あたり2アレイ)。会員の実測で、緑の RA6~RA11 が約 0.1k/0.22k/0.47k/1k/2.2k/4.7k Ω(フォーラム) — [arcade-museum forum](https://forums.arcade-museum.com/threads/resistor-arrays-on-capcom-cps1-a-board.331665/)(検索要約経由)。CPS2 の出力段は**未確認**。
- DE10Jamma(新規設計の例): "Three 6bit R-2R DACs"、ラダーは 604 Ω(Bourns CAY16-6040F4LF)で構成。"Output level is not noticeably lower than a NeoGeo MVS, and well within adjustment range on arcade monitors."。トリマは無い — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)
- supergun 側の変換: 従来の可変抵抗アッテネータでは、基板から見た負荷が "75-575 ohms depending on the pot position" と重くなる(モニタは "1-5k ohms")。AV-Driver は 10 k の多連ポットとバッファで負荷を軽くしている — [etim.net.au](https://etim.net.au/av-driver/arcade/)。390 Ω/1 kΩ の分圧+負電源付きバッファの例 — [slashdirt supergun](http://hacks.slashdirt.org/hw/supergun/)(本文 503、検索要約経由)。直列 180 Ω + 75 Ω 終端(0.3 倍)の例、直列 220 Ω を CPS2/F3/MVS で使った報告(フォーラム) — [neo-geo.com "RGB voltage levels"](https://www.neo-geo.com/forums/index.php?threads/rgb-voltage-levels.250783/)(検索要約経由)
- 実測例: Axunworks Supergun Mini に Neo Geo MV1C をつなぎ、ポット最大・75 Ω 終端で "1.2v on the scope" — [RetroRGB review](https://retrorgb.com/axunworks-jamma-supergun-mini-full-review.html)(検索要約経由)
- JAMMAizer(コンソール→JAMMA 変換)の既定出力インピーダンスは 475 Ω(検索要約のみ、本文で確認できず)— [arcade-projects RGB amp thread](https://www.arcade-projects.com/threads/rgb-amp-vga-to-jamma.15501/)。同スレッドで、モニタに 0.75 Ω(75 Ω)/1 kΩ 切替がある場合は "it needs to be set to 1kohm if using an amp"(Zebra)

### Inferences
- (推論・計算)Neo Geo の DAC 合成抵抗は 1/(1/3900+1/2200+1/1000+1/470+1/220) ≈ **119 Ω**、Sega は ≈ **129 Ω**。開放 3.5 V の Neo Geo を 2 kΩ に入れると約 3.3 V、75 Ω に入れると約 1.35 V になる。75 Ω 入力に JAMMA 基板を直結すると、基準の 0.7 V に対して約2倍の過大入力になる。75 Ω の筐体は D-SUB15 側(NAOMI 用)なので、JAMMA 基板は 75 Ω を直接駆動しない前提でよい。
- (推論)**新基板の目標**: 開放出力 3.0 V ±10%(白、黒 0 V)、出力インピーダンス 100~150 Ω(Neo Geo/Sega 並み)、DC 結合。この条件なら、2 kΩ 負荷で約 2.8 V(Blast City の基準 3.0 Vp-p の範囲内)、4.7 kΩ(K7000)で約 2.9 V、75 Ω を誤って選んだ場合でも約 1.1~1.3 V(Neo Geo 直結より小さい)になる。トリマやジャンパは**慣習ではない**。部品点数の制約からも不要で、モニタの CONTRAST で吸収する。ただし Pico の 3.3 V GPIO で抵抗 DAC を組むと、白が開放 3.3 V × ラダー比になる。2 kΩ 負荷で 3 Vp-p を確保するには、ラダーを低めのインピーダンス(合成 100~150 Ω)にするか、5 V 系の 74HC(T)541 などのバッファで振り上げる必要がある。

### Gaps
- CPS2 / Taito F3 / Konami の出力段の部品値は**未確認**。Neo Geo の DAC を駆動する 74LS273 の High 出力値と、実機出力の 0~3.5 V の対応も、wiki の記述以上には確認していない。

---

## 3. Famicom 系タイミングとアーケードモニタ

### Takeaway
21.477272 MHz ÷ 4 = 5.369318 MHz のドットクロックで、**水平 15.7458 kHz、垂直 60.0985 Hz(ドット飛ばし無し)/60.0988 Hz(2C02 の平均)** になる。これは NTSC の 15.7343 kHz より 0.073% 高いだけで、上記のどのモニタの受入範囲にも入る。任天堂自身も VS. / PlayChoice-10 で同じ 341×262 のタイミングを 15 kHz の業務用モニタ(Sanyo 20-EZV / 20-Z2AW 等)で使っていた。2C02 だけにある奇数フレームの1ドット飛ばしは、上端ラインの1ドットのジッタとして見えることがある(家庭用 RGB 化の利用者報告)。業務用の RGB PPU(2C03/2C04)にはこの飛ばしが無い。

### Cited Findings
- 計算: 5,369,318.18 Hz / 341 = 15,745.80 Hz、/ (341×262 = 89,342) = 60.0985 Hz、/ 89,341.5 = 60.0988 Hz。NTSC 放送は 15,734.27 Hz / 59.94 Hz(自分で算出)。
- "odd frames ... skipping the first idle tick on the first visible scanline"、"(339,261) ... directly to (0,0)"。レンダリング有効時は 89,341 クロック、無効時は 89,342 クロック — [nesdev PPU frame timing](https://www.nesdev.org/wiki/PPU_frame_timing)
- RGB PPU: RP2C04-0001 は "Equivalent to 2C02D, but keeps 2C03 timing (no skipped dot)"。RC2C05-99 は "Uses 2C02 timing (a dot is skipped every other frame), unlike other RGB PPUs." — [nesdev PPU variants](https://www.nesdev.org/wiki/PPU_variants)
- PlayChoice-10: "This game uses one of four types of Video Monitors ... [32 Type] 20-EZV(R-C) / [33 Type] 20-EZV(R-C) / [35 Type] 20-Z2AW"。Signal PCB に "INVERT OUT / NON INVERT OUT"("In case of PCH-UP, Plug in here!")があり、映像極性を切り替える — [PC10 Operation Manual (archive.org)](https://archive.org/details/pc10operationmanualpch1-up)
- Nintendo/Sanyo 20-EZV(R-B,C) 用の video inversion kit が市販されている — [Paradise Arcade Shop](https://paradisearcadeshop.com/a/p/products/nintendo-sanyo-20-ezvr-bc-monitor-video-inversion-kit-by-zanen)(検索要約経由)。VS. System のモニタ型番は一次資料で**未確認**(Sanyo 系と推定)。
- NES のジッタ: 短いスキャンラインの直後の最初の可視ラインが1ドット左にずれ、短いラインが隔フレームで生じると上端ラインの画素がジッタする。FPGA でクロックをゲートする対策や、NESRGB のラインバッファ方式が議論されている(フォーラム、本文は 403) — [shmups "NES/SNES 240p dejitter mod"](https://shmups.system11.org/viewtopic.php?t=61285)(検索要約経由)
- NES2JAMMA(NESRGB → JAMMA の自作例): 映像は "TLS1233 and LM1881"、音声は "a basic LM384"。テスト結果は "quite happy"。同期の問題は報告されていない — [arcade-projects NES2JAMMA](https://www.arcade-projects.com/threads/nes2jamma.2779/)

### Inferences
- (推論)ドット飛ばしは**1ライン(341 → 340 ドット、−0.29%)だけ**の周期変化で、垂直周期の変化は 1/89,342。PLL/フライホイールを持つ業務用モニタ(MS9 は "robust")が同期を外す原因にはならない。見えるのは上端1ラインの1ドットの揺れ程度。Pico で RGB を再生成するなら、出力側を 341 ドット固定でタイミング生成すれば問題自体が消える。
- (推論)2C02 は負極性映像やコンポジットしか出さない。2C03 のような RGB は出さないので、RGB 化は別ノート `rgb_from_rp2c02.md` の範囲。

### Gaps
- Nanao MS8/MS9 で NES 由来の 15.7458 kHz を実測した報告は**未確認**。

---

## 4. 同期信号(コンポジット負極性)

### Takeaway
JAMMA の同期は **負極性 TTL レベル(High ≒ 4~5 V、Low ≒ 0 V)のコンポジット同期**を P 番ピンに出す。モニタの入力インピーダンスは数 kΩ~20 kΩ(K7000 の負極性同期は 12 kΩ)なので、駆動能力はほとんど要らない。日本の JAMMA 筐体は 1 本の SYNC 線しか持たない(Astro City / Egret II / Windy の配線図)。H/V 分離が必要になるのは、Blast City の D-SUB15(31 kHz/NAOMI)側など JAMMA 以外の入力の場合である。

### Cited Findings
- K7000: "Sync: TTL positive or negative going, separate or composite. Input impedance: 20K ohms for positive going sync; 12K ohms for negative going sync."。"If the sync signal is composite, use the horizontal sync input of the same polarity" — [K7000 manual](https://dn760108.eu.archive.org/0/items/k-7000-1/K7000-1_text.pdf)
- MTC 9000: 同期振幅 "1.5 - 5 V p.p."、"Contact 6 horizontal or composite sync"、"Contact 5 vertical sync (or no connexion if using composite sync)" — [MTC 9000 manual](https://archive.org/stream/ArcadeGameManualMtc9000/mtc9000_djvu.txt)
- Blast City の JAMMA 入力は "SYNC = NEGATIVE, H/V Composite" — [Arcade Otaku Wiki](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide)
- 配線図: Astro City のカラーディスプレイ・コネクタは RED/GREEN/BLUE/SYNC/GND(SYNC) の5線 — [AstroCityMan.pdf p.30](https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf)。Egret II は VIDEO Assy に "R, G, BL, SYNC, GND" — [Egret II Schematics.jpg](https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg)。Windy は 29inch MONITOR に "SYNC, GND, BLUE, GREEN, RED" — [Windy Specs.jpg](https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg)
- supergun のレビューは、同期を "high-voltage TTL" とし、民生機器向けには 470 Ω を直列に入れるとしている — [RetroRGB](https://retrorgb.com/axunworks-jamma-supergun-mini-full-review.html)(検索要約経由)

### Inferences
- (推論)**目標**: 5 V CMOS/TTL の出力(74HC/74HCT ゲート1段)で、Low ≤ 0.4 V、High ≥ 3.5 V、直列 47~100 Ω(短絡保護とリンギング抑制)。3.3 V GPIO の直結(High 3.3 V)でも MTC 9000(1.5 V~)や K7000(TTL)の仕様には入るが、MS8/MS9 の閾値は未確認なので、5 V バッファを推奨する。

### Gaps
- Nanao/Toei シャーシの同期入力の閾値と入力インピーダンスは**未確認**。

---

## 5. 電源(接点定格・電流・最小負荷・+5 V 調整・−5 V)

### Takeaway
JAMMA 用カードエッジ(JST GEC)は**1接点あたり 3 A**、基板厚 1.6 ± 0.15 mm。日本の筐体電源は **+5 V 5~7 A、+12 V 1~2 A、−5 V 0.1~0.5 A** で、Astro City / New Astro City / Egret II / Windy / Exceleena 2 は **−5 V を供給している**(Blast City の JAMMA ループは −5 V 無し)。+5 V は電源ユニットの V.ADJ で工場調整されている。現行の代替電源(Mean Well RT-65A)は無負荷から規定されているが、多出力時の +12 V/−5 V の精度には CH1(+5 V)の負荷 10% 以上が推奨されている。

### Cited Findings
- JST GEC(GEC-561、56極): "The GEC connector conforns to the JAMMA standards"、"Current rating: 3A AC, DC"、"Voltage rating: 250V AC, DC"、"Contact resistance: Initial value/15m Ω max. After environmental testing/30m Ω max."、"Applicable wire: AWG #24 to #16"、"Applicable PC board thickness: 1.6 ± 0.15mm"。接触部は金めっき。参考基板図: ピッチ 3.96 ± 0.05、Circuit 1~28 の間隔 106.92 ± 0.05、エッジ部の幅 114.6(+0/−0.2)、Circuit 7 と H に "Mis-insertion preventive key groove"(溝幅 2.3 ± 0.035、深さ 10.0 と読める)、肩 C0.5、先端断面 C0.5(図面読み取り) — [JST GEC datasheet](https://datasheet.octopart.com/GEC-561-JST-datasheet-180492417.pdf)
- Sullins の 0.156" 系は "3 Amps per contact" — [Sullins news](https://www.sullinscorp.com/news/news-releases/sullins-double-row-male-edgecard-connector-series-features-0-100-or-0-156-contact-centerline-parts/)(検索要約経由)

**筐体の電源**

| 筐体 | +5 V | +12 V | −5 V | 出典 |
|---|---|---|---|---|
| Astro City(400-5198 PWR SPLY UNIT, 入力 AC90~132V) | 7 A | 1.5 A | 0.1 A(JAMMA 5/E に配線あり) | [AstroCityMan.pdf p.31](https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf) |
| New Astro City(400-5198-CE-01Z) | 7 A | 1.5 A (PEAK 2A) | 0.1 A | [NewAstroCity-Manual.pdf p.10, p.22](https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf) |
| Egret II(Switching Regulator Assy) | あり | あり(+ "POST +12V") | あり(5/E) | [Egret II Schematics.jpg](https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg) |
| Windy | 5 A | 1 A | 0.5 A(5/E に配線あり) | [hard--candy Windy](https://www.hard--candy.com/wiki/candy/Windy)、[Specs.jpg](https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg) |
| Exceleena 2 | 7 A | 2 A (Peak 6A) | 0.2 A | [hard--candy Exceleena 2](https://www.hard--candy.com/wiki/candy/Exceleena_2) |
| Blast City(JAMMA 変換ループ 600-6738-21) | あり | あり | "-5v is not supplied" | [Arcade Otaku](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide) |

- New Astro City: "Using any Board which requires power in excess of the above-mentioned capacity is not allowed."。"V. ADJ. : DC Power Supply voltage (+5V) adjustment volume (V.R.)"、"V.ADJ. has been adjusted at the time of shipment from the factory. Use the settings as is ... Changing the settings without a good reason can cause damage to the IC Board" — [NewAstroCity-Manual.pdf p.10](https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf)
- 電線: Astro City の配線図の電線表は "K: AWG18 UL1015 許容電流 12A / L: AWG20 UL1007 8.4A / 細: AWG22 UL1007 6.4A"。+5V と GND はエッジ側で 30×2・50×2 のように2本ずつ配線されている(図面読み取り) — [AstroCityMan.pdf p.31](https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf)
- Mean Well RT-65A(5 V / 12 V / −5 V の3出力): 定格 6 A / 2.8 A / 0.5 A、"CURRENT RANGE 0 ~ 8A / 0 ~ 3.5A / 0 ~ 1A"、"VOLTAGE ADJ. RANGE CH1: 4.75 ~ 5.5V"、負荷変動 ±1.0% / ±3.0% / ±1.0%、"INRUSH CURRENT (Typ.) COLD START 50A/230VAC"、注記 "when multi-channel output, it is recommended that CH1 load > 10%." — [Mean Well RT-65 spec](https://www.meanwell.com/Upload/PDF/RT-65/RT-65-SPEC.PDF)
- 古いスイッチング電源の最小負荷: "a lot of switchers require a minimum load, typically on the +5V line, usually around 0.5A"、"older switching supplies tended to measure high when unloaded ... sometimes ... hit the over voltage protection and shut down"。ダミー負荷は 5 V に 10 Ω(500 mA)が経験則(フォーラム) — [arcade-museum "What value resistors to satisfy PSU minimum load reqs?"](https://forums.arcade-museum.com/threads/what-value-resistors-to-satisfy-psu-minimum-load-reqs.499357/) ほか(検索要約経由)
- DE10Jamma: "If +5v rail is adjusted too high, the DE10-Nano's over-voltage protection circuitry will not allow the board to power up." — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)
- 小型基板の電流の参考: Famicom 本体の専用 AC アダプタ HVC-002 は "DC10V 850mA"(任天堂公式の仕様表) — [任天堂 ファミリーコンピュータ ハードウェア](https://www.nintendo.com/jp/famicom/hardware/index.html)(検索要約経由)

### Inferences
- (推論)本基板の +5 V 消費は、Famicom 本体(10 V 入力 0.85 A 定格、7805 損失と RF モジュレータを含む)より小さく、0.3~0.6 A 程度と見込む。ピーク 1 A 未満なら 3/4/C/D の +5 V ピン(4 接点 × 3 A)で十分すぎる余裕がある。
- (推論)古い Sega/Nanao 系の電源は、最小負荷の要否が**未確認**。基板に「最小負荷用の抵抗」を載せるのは熱の面で不利なので載せない。代わりに、+5 V で 4.75~5.5 V(RT-65A の調整範囲)を許容し、5.5 V を超える場合の保護(TVS 6.0~6.8 V クラス + ポリスイッチ)を入れる。−5 V と +12 V は使わない(音声アンプに +12 V を使うなら §7)。
- (推論)突入電流: 基板の入力容量は 100~220 µF 程度に抑え、筐体電源の起動を妨げないようにする。メイン SW で電源を入れる運用なので、ホットプラグ対策(エッジの長短ピン)は JAMMA には無い。挿抜は電源 OFF で行う、とマニュアルに書く。
- (推論)GND: エッジの GND 8 接点(1/2/27/28/A/B/e/f)をすべてベタ GND に落とす。14(Video GND)は映像のリターンとしてモニタの GND(SYNC) に配線されているので、RGB と同期のリターンを近くに通す。

### Gaps
- 400-5198(Sega)・Taito・Konami の電源の最小負荷、無負荷時の電圧、OVP 設定値は**未確認**。
- JAMMA 規格書そのものの接点定格の記載は**未確認**(JST GEC の「JAMMA 準拠」の 3 A を採用)。

---

## 6. コイン系(セレクタ出力・カウンタ・ブロッカー/ロックアウト・駆動回路)

### Takeaway
日本の筐体のコイン入力は主に**旭精工 AD-81P 系のメカセレクタ+マイクロスイッチ(COM/NO の無電圧接点)**で、マイクロスイッチは金接点(Omron D2MC-01 系、最小適用負荷 5 VDC 1 mA)。電子セレクタは**正貨パルス 50 ± 5 ms または 72 ± 3 ms**(旭精工)。**カウンタは日本の筐体では +5 V 系が主流**(Astro City、Windy、Cyber Lead の "NX-06PD 5VDC")。MVS や米国系の +12 V とは違う。**ロックアウト(9/K)は日本の筐体では配線されていないことが多い**。日本の「ブロッカー」(旭精工 QL-102)は 12 V で 85 Ω / 157 mA 以下。

### Cited Findings

**入力側(セレクタ)**
- 旭精工 AD-81P2: "メカ式1WAYドロップセレクター"、"硬貨投入間隔 0.5秒以上"。オプションは "専用チャンネルブラケット:MODEL CB/81M マイクロスイッチ付"、"コイン投入防止ブロッカー:MODEL QL-102(DC12V、DC24V)" — [旭精工 AD-81P2](https://www.asahiseiko.com/product/139/)
- 実機: Cyber Lead の部品表は "コインセレクタ AD-81P3 ¥100"、"チャンネルブラケット CB/81M"、"デンシロック VM81-M"、"デンジカウンタ NX-06PD 5VDC" — [CyberLead-Manual.pdf p.57/59](https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf)。New Astro City の AD-81P は「機械式」で、マイクロスイッチの "COM(コモン)と NO(ノーマリーオープン)だけ使用" — [ameblo tarcade](https://ameblo.jp/tarcade/entry-12686617268.html)
- 旭精工のマイクロスイッチ D2MC-01F1: "適応製品 コインセレクター(電子セレクターを除く)およびブラケット全製品"、"電気定格(125VAC) 0.5A"、"接触抵抗 100mΩ以下"、"許容動作頻度 機械的/240回/分 電気的/60回/分" — [旭精工 マイクロスイッチ](https://www.asahiseiko.com/product/374/)
- Omron D2MC: D2MC-01 は "Gold alloy" 接点、"Min. applicable load 5 VDC 1mA"(銀接点の D2MC-5 は 5 VDC 160 mA)、30 VDC 0.5 A。レバーが長すぎると "improper switch resetting or contact chattering may occur" — [Omron D2MC datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2mc.pdf)
- 旭精工の電子セレクタ AE-204D: 電源は "DC24V(DC15.0~DC26.4V)" / "DC12V±5%(特別仕様)"、正貨信号は "信号電圧/DC30V(MAX) 信号電流/50mA(MAX) 信号パルス幅/50msec.±5msec." — [旭精工 AE-204D](https://www.asahiseiko.com/product/148/)。AE-192D は "信号パルス幅 72msec.±3msec."、"DC35V(MAX)" / "10mA(MAX)" — [旭精工 AE-192D](https://www.asahiseiko.com/product/146/)(検索要約経由)
- 汎用マルチコインアクセプタ HX-616: "オープンコレクタ出力のよう"、パルス幅は "Fast/Medium/Slowでそれぞれ30msec/50msec/100msec程度"(オシロで観測)、電源 12 V — [はてなブログ 工作と競馬2](https://dekuo-03.hatenablog.jp/entry/2020/01/30/224222)
- 電子メックのパルス幅は 25/50/75/100 ms などから選べる。ある基板は約 100 ms 以上でないとクレジットを認識しなかった(フォーラム) — [arcadecontrols forum](http://forum.arcadecontrols.com/index.php?topic=153821.0)(検索要約経由)

**カウンタ(8/J)**
- Astro City: COIN METER(220-5412 MAG CNTR W/CONN)の線色は 30(YELLOW。電源 DC OUT1 の +5V と同じ色)と 80(BLACK、JAMMA 8)。JAMMA 側の表では J/9/K が "(COIN METER 2)(COIN LOCK OUT 1)(COIN LOCK OUT 2)" と括弧付きで、配線されていない(図面読み取り) — [AstroCityMan.pdf p.30-31](https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf)
- Windy: "GX-06PD" の2線は、赤(2、この束線図では +5V の線色)と灰(8、JAMMA 8 COIN COUNTER1)。JAMMA J/9/K は無配線(図面読み取り) — [Windy Specs.jpg](https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg)
- Cyber Lead: "デンジカウンタ NX-06PD 5VDC" — [CyberLead-Manual.pdf](https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf)
- Sega NAOMI Universal 筐体: カウンタが無いときは +5V と coin meter 線の間に 100 Ω を入れて偽装する。12 V を使うのは "Provided the coin meter accepts 12V" の場合だけ — [arcade-projects "Naomi universal coin meter"](https://www.arcade-projects.com/threads/naomi-universal-coin-meter.32723/)
- Neo Geo MVS: "The counters typically have one pin hardwired to +12V"、通電と遮断を "both during a long enough time" で行う — [NeoGeo Dev Wiki Coin counter](https://wiki.neogeodev.org/index.php?title=Coin_counter&action=raw)
- 電磁カウンタの一次仕様: ライン精機 MZ シリーズ(超小型・自販機/クレーンゲーム用途)は "計数速度 20Hz"、"パルス幅(メーク比) 25ms(1:1)"、"電源 DC12V/24V"、"消費電力 DC1.2W" — [ライン精機 MZ](https://www.line.co.jp/product/2104/)。(検索要約は 50 ms と誤記していたが、公式ページは 25 ms)。Kessler-Ellis の DC 電磁カウンタ(5 cps 品)は on 120 ms / off 80 ms、約 85 mW — [KEP catalog](http://kepsales.com/pdf/KEP_ii_catalog.pdf)(検索要約経由)
- コイル抵抗の利用者実測: 12 V カウンタで 129.1 Ω(フォーラム) — [arcadecontrols](https://forum.arcadecontrols.com/index.php?topic=52711.0)(検索要約経由)

**ロックアウト/ブロッカー(9/K)**
- 旭精工のブロッカー(公式): QL-102(CB/81M 用)は 12DC で "直流抵抗(Ω)=85±10% 電流(mA)=157以下"、24DC で "313±10% / 86以下"、"定格消費電力 約2W"。QM-5 は 12 V 76 Ω / 158 mA 以下。QL-203 は 12 V 100 Ω / 120 mA。SB-101 は 12 V 57 Ω / 210 mA 以下 — [旭精工 ブロッカー](https://www.asahiseiko.com/product/366/)。**通電時に阻止するか受け付けるかはページに記載が無い(未確認)**。
- JAMMA/MVS の lockout: "Coin lockouts are typically coils hardwired to the 12V power supply. It's the game PCB's job to power them by grounding their second terminal"。"When powered, it allows an inserted coin ... When not powered ... the coin take the return path."。MVS は NEO-F0 → ULN2003 のオープンコレクタ — [NeoGeo Dev Wiki Coin lockout](https://wiki.neogeodev.org/index.php?title=Coin_lockout&action=raw)
- Egret II の配線図: JAMMA 8 = "COUNTER"。J/9/K の下に配線は無い(図面読み取り) — [Egret II Schematics.jpg](https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg)

**駆動素子**
- TI ULN2003A: "500mA-rated collector current"、"High-voltage outputs: 50V"、"Output clamp diodes"(COM ピンに共通カソード)。VCE(sat) は IC = 100 mA で typ 0.9 / max 1.1 V、IC = 200 mA で typ 1.0 / max 1.3 V。VI(on) は IC = 200 mA で 2.4 V、250 mA で 2.7 V、300 mA で 3 V(VCE = 2 V) — [TI ULN2003A datasheet](https://www.ti.com/lit/ds/symlink/uln2003a.pdf)

### Inferences
- (推論)**コイン入力**: 金接点の最小負荷が 1 mA なので、プルアップは 5 V なら ≤ 4.7 kΩ、3.3 V なら ≤ 3.3 kΩ(どちらも ≥ 1 mA)。これに 1 kΩ 直列と 10~33 nF の RC を組み合わせる(§8)。デバウンスはソフトで行い、**Low が 10 ms 以上連続したら有効、その後 High が 10 ms 以上でリリース**とする。最小有効幅を 10 ms にすれば、電子セレクタの 25~100 ms パルスも確実に拾える。0.5 秒の投入間隔(AD-81P2)に対しても余裕がある。30 ms を超える長押しを別コインと数えない。
- (推論)**カウンタ**: 日本の筐体は +5 V カウンタが主流なので、ULN2003 では VCE(sat) が約 1 V 落ち、5 V コイルに 4 V しかかからない(MVS 流の +12 V 前提ならこれで問題ない)。**低 RDS(on) の N-MOSFET(ロジックレベル、例: AO3400 クラス)でローサイドを駆動し、コイルに並列に還流ダイオード(1N4148 / 1N4007 / SS14 など)を基板上に置く**のが +5 V と +12 V の両対応になる。電流は 100 Ω で 50 mA(5 V)、85 Ω で 141 mA(12 V)程度を想定し、定格 ≥ 500 mA・≥ 30 V の素子を選ぶ。パルスは **ON 100 ms ±10% / OFF ≥ 100 ms**。ライン精機 MZ の 25 ms(1:1)、20 Hz にも、Kessler-Ellis の 120/80 ms(5 cps)にもほぼ対応できる。KEP 品を最悪条件とみるなら ON 120 ms / OFF 100 ms。
- (推論)**ロックアウト**: 日本の筐体では配線されていないことが多い。米国式の配線(+12 V コイル、ON で受付)の筐体のために同じドライバを 9/K に付けておく。通電したままにするので、12 V・157 mA の連続通電(約 2 W はコイル側の発熱)に耐える素子にする。
- (推論)ドライバの出力端子は、筐体側のコイル電源(+5 V / +12 V)への誤接続や短絡に備えて、ポリスイッチか 1~2 Ω の直列抵抗で保護すると安全である。

### Gaps
- NX-06PD / GX-06PD のメーカーとコイル抵抗は**未確認**(Cyber Lead の部品表で 5 VDC であることだけ確認)。Sega 220-5412 のコイル電圧は線色からの推定で、**未確認**。
- 旭精工のブロッカーの通電時の動作(阻止か受付か)と、VM81-M の仕様は**未確認**。
- メカセレクタのマイクロスイッチのチャタリング時間の実測値は**未確認**(Omron はレバー形状による、としか書いていない)。

---

## 7. 音声(スピーカ・アンプ・BTL・音量)

### Takeaway
日本の筐体は**スピーカを2個(L/R)持ち、JAMMA のモノラル 10/L で両方を鳴らす**。インピーダンスは筐体ごとに違い、Astro City は 8 Ω 10 W ×2(並列で合成約 4 Ω と読める)、Egret II は 4 Ω ×2、Blast City は 8 Ω。**音量は筐体側の直列ボリューム/レオスタットで調整する**(Blast City は 100 Ω 10 W のレオスタット、Astro City は電源ユニットの SOUND VOL.、Windy は2連 VR、Egret II は VOL)。配線図の 10/L は、どれも GND に接続されていない。実在する基板のアンプは BTL のカーオーディオ用 IC(TA8201AK、TDA7240、HA13001 の BTL モード)が多く、L は GND ではない。

### Cited Findings
- Astro City: JAMMA 10(A, PINK)と L(90, GRAY)は電源ユニットの "SOUND" コネクタ → "SOUND VOL." → "SPEAKER" コネクタ(A2/92)の順に通る。前面パネルの LEFT と RIGHT にそれぞれ "8Ω 10W"(部品表 "130-5091 SPEAKER 8 OHM 10 SPL")があり、コネクタの C 側で "A2×2"、"92×2" と束ねられている(図面読み取り) — [AstroCityMan.pdf p.20, p.30-31](https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf)
- New Astro City: "SOUND VOL. : Adjust the Speaker Volume." — [NewAstroCity-Manual.pdf p.10](https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf)
- Blast City(Bass Fishing 版の部品表 ASSY FRONT CABI): "220-5420 RHEO STAT 100 OHM 10W"、"130-5156 SPEAKER BOX 8 OHM"。取説 7-1 に "SOUND VOLUME Adjust the Speaker Volume" — [BlastCityBassFishing-Manual.pdf](https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf)
- Egret II: SP(R) と SP(L) がどちらも "4Ω"。JAMMA の SPEAKER(+)/(−) は、F3 SYSTEM(4P)・FX1 SYSTEM(4P)と並んで切替スイッチと "VOL." を通ってスピーカへ行く — [Egret II Schematics.jpg](https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg)
- Windy: JAMMA 10(灰 8)と L(白 9)→ "SOUND VOLUME"(L-Ch / R-Ch の2連)→ LEFT/RIGHT SPEAKER。Konami 基板用の "STEREO SOUND (FOR KONAMI PCB)" コネクタ(NH-4)が別にある — [Windy Specs.jpg](https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg)
- Cyber Lead のスピーカは 2 個、型番 "9AFOQS5WLA"(インピーダンスは**未確認**) — [CyberLead-Manual.pdf p.59](https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf)
- Neo Geo の基板のアンプ: "Most arcade cabs don't have embedded audio amps."。MV1A は "Motorola MC13308T4"、MV1F/MV1FZS は "Hitachi HA13001. Stereo. 2x 5W in 4 ohms."、MV1B は "Toshiba TA8201AK. Mono. 1x ~7W in 4 ohms."、MV1C は "ST TDA7240. Mono 1x 20W in 4ohms."。"These components can die from overheating or voltage surges on the 12V line." — [NeoGeo Dev Wiki Power amp](https://wiki.neogeodev.org/index.php?title=Power_amp&action=raw)
- TA8201AK: BTL 構成で出力結合コンデンサが不要。"POUT = 17W at VCC = 14.4V ... RL = 4Ω"、"14W at VCC = 13.2V" — [TA8201AK datasheet](https://datasheetspdf.com/datasheet/TA8201AK.html)(検索要約経由)。TDA7240A: "20W BRIDGE AMPLIFIER FOR CAR RADIO"、"SHORT CIRCUITS TO GROUND AND ACROSS LOAD" の保護あり — [TDA7240A datasheet](https://manualmachine.com/sgsthomsonmicroelectronics/tda7240a/4458195-datasheet)(検索要約経由)。HA13001: "5.5W Dual / 17.5W BTL"(アグリゲータ、確度は低い) — [datasheetcafe](https://www.datasheetcafe.com/ha13001-pdf-datasheet-26622/)
- "On mono JAMMA boards, the speaker- pin is not connected (this isn't ground)." — [etim.net.au](https://etim.net.au/av-driver/arcade/)。"ALL jamma boards use bridged amplifiers where sp- is never ground"、片側を接地するとアンプが壊れる(フォーラム、言い過ぎを含み、反対意見もある) — [arcade-projects "jamma speakers"](https://www.arcade-projects.com/threads/jamma-speakers.5497/)(検索要約経由)
- ステレオ: MVS 配線の筐体は 10/L と 11/M でステレオ。JAMMA 基板を MVS 配線の筐体に入れるとアンプが焼けた、という報告がある(二次) — [NeoGeo Dev Wiki JAMMA pinout](https://wiki.neogeodev.org/index.php/JAMMA_connector_pinout)、検索要約
- 自作例: NES2JAMMA は "a basic LM384"(シングルエンド、利用者は "the volume is too low and muffled") — [arcade-projects NES2JAMMA](https://www.arcade-projects.com/threads/nes2jamma.2779/)。DE10Jamma は TDA7496 と Mono/Stereo ジャンパ — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)

### Inferences
- (推論)**負荷**: 最悪は 4 Ω(Astro City の 8 Ω 並列、Egret II は1チャンネル 4 Ω)。音量のレオスタットが 0 Ω 位置なら 4 Ω をそのまま駆動する。**目標は 4 Ω で 3~5 W 程度、8 Ω で 2~3 W、短絡保護付き**。
- (推論)**方式**: 筐体側は「L は GND ではない」を前提に作られているので、**BTL(10 = OUT+、L = OUT−)**を基準にする。ただし、改造などでスピーカ−が GND に落とされている筐体では、BTL の負側出力が GND に短絡する。そのため、**GND への短絡保護を持つ BTL アンプを選ぶ**(TDA7240 はデータシートに "short circuits to ground" 保護を明記)。シングルエンド+出力コンデンサ(L を GND)にする手もあるが、出力が下がる。候補は 5 V 電源の D 級 BTL(PAM8302A 系。2.5 W @ 4 Ω と短絡保護はデータシート未確認)。+12 V で AB 級の BTL を使う場合は、MVS で起きた故障(12 V 線のサージ)を踏まえて余裕を取る。
- (推論)**音量**: 筐体側で調整するのが慣習なので、基板上の VR は省略可。ただし Famicom の音量はゲームごとの差が大きいので、基板上に半固定 1 個(ゲイン調整)を置くか、Pico のソフトで固定ゲインにする。
- (推論)**ステレオ**: Famicom はモノラルなので 11/M は無接続(ハイインピーダンス)にし、MVS 配線の筐体での事故を避ける。

### Gaps
- Windy、Cyber Lead、Exceleena のスピーカのインピーダンスと出力は**未確認**。CPS1/CPS2/Sega/Taito 基板のアンプ IC の一次資料は**未確認**。

---

## 8. 実在する基板の入力回路(プルアップ・直列抵抗・フィルタ)

### Takeaway
Neo Geo の入力は **1 kΩ プルアップ+330 Ω 直列+33~43 nF**(CRE401、fc 約 15 kHz)。新規の DE10Jamma は **1 kΩ + 10 nF の RC で、デバウンスはソフト側**。日本の筐体の入力はすべて無電圧接点で GND に落とす方式である(Astro City / Egret II / Windy の配線図)。

### Cited Findings
- CRE401: "The leftmost pin's net pulls all outputs through 1k resistors. The 330 ohm resistors provide current protection (sometimes as fuses), the capacitors smooth out eventual spikes." — [NeoGeo Dev Wiki CRE401](https://wiki.neogeodev.org/index.php?title=CRE401&action=raw)
- CRE401 の実測(複製プロジェクト): R1 330 Ω、R2 1 kΩ、C1 は 33 nF(-17)、35~36 nF(-18)、41~43 nF(-19)、42~43 nF(-2N)。"cut-off frequency of about 15kHz" — [mourix/CRE401 README](https://raw.githubusercontent.com/mourix/CRE401/main/README.md)。部品の系列は "MODEL CR SERIES Single-In-Line ... Resistor/Capacitor Networks" の "-A Circuit" — [Cr.pdf](https://wiki.neogeodev.org/images/5/5a/Cr.pdf)
- DE10Jamma: "Inputs are RC filtered ... to give EMI protection to the FPGA."、"No multiplexing, polling or debouncing of the inputs"。BOM は 1 kΩ ×28(C140870)、10 nF ×30(C83170) — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)
- その他: "1K pullups are a little too strong for conductive rubber contacts, and the Neo Geo originals use 1k" と、10 k を使う例(フォーラム) — 検索要約経由 [arcade-projects Console JAMMAizer](https://www.arcade-projects.com/threads/console-jammaizer-easily-connect-home-consoles-to-your-jamma-arcade-cabinet.10074/page-26)
- Astro City は 25/c/26/d を "1P SW 4 / 2P SW 4 / 1P SW 5 / 2P SW 5" として配線している — [AstroCityMan.pdf p.31](https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf)。Egret II は 25/c/26/d を "1P SPARE 1 / 2P SPARE 1 / 1P SPARE 2 / 2P SPARE 2" とし、S/S コネクタに "1P SPARE 3 / 2P SPARE 3"(キックハーネス)がある — [Egret II Schematics.jpg](https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg)。Windy も 25/c/26/d を "1P SPARE 1 / 2P SPARE 1 / 1P SPARE 2 / 2P SPARE 2" としている — [Windy Specs.jpg](https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg)

### Inferences
- (推論)**目標**: プルアップ 4.7 kΩ(5 V)または 3.3 kΩ(3.3 V。マイクロスイッチの金接点の最小負荷 1 mA 以上を確保)、直列 1 kΩ、対 GND 10 nF(fc ≈ 16 kHz。CRE401 並み)。入力 IC は、3.3 V の Pico 直結ならプルアップを 3.3 V に取り、5 V 系に引き上げない。コイン/スタート/サービス/テストも同じ回路でよい。デバウンスは方向とボタンが 2~5 ms(1~2 フレーム以内)、コインは §6 の 10 ms。
- (推論)25/c/26/d は筐体によってはボタン(GND に落ちるスイッチ)が付いているので、**入力専用(プルアップ付き)か無接続にする。出力や電源には絶対に使わない**。

### Gaps
- Sega/Capcom/Taito 基板の入力部品の値の一次資料は**未確認**。

---

## 9. 設計目標値のまとめ(出典つき)

| 項目 | 目標値(許容) | 根拠 |
|---|---|---|
| RGB 出力レベル | 白 3.0 V ±10%(開放)、2 kΩ 負荷で 2.5~3.0 Vp-p、黒 0 V、DC 結合、正極性 | Blast City "2kΩ / 3.0Vp-p"、Neo Geo "0~3.5V"、MTC 9000 "2-5 V p.p."、K7000 "4.7k" |
| RGB 出力インピーダンス | 100~150 Ω(抵抗 DAC の合成値)、トリマ無し | Neo Geo ≈119 Ω、Sega ≈129 Ω(MAME の値から計算)。慣習ではモニタの CONTRAST で調整(NAC 取説) |
| 75 Ω 入力への対応 | 直接は対象外(D-SUB15 側の設定)。誤設定でも約 1.1~1.3 V で破損しない | Blast City SW3 の表 |
| 同期 | 負極性コンポジット、TTL(Low ≤ 0.4 V / High ≥ 3.5 V)、5 V バッファ+直列 47~100 Ω | K7000 "TTL ... 12K ohms for negative"、MTC 9000 "1.5-5 V p.p."、Blast City "NEGATIVE, H/V Composite" |
| 走査 | 15.7458 kHz / 60.0985 Hz(341×262 固定を推奨) | 計算、K7000 15.1~16.8 kHz / 47~63 Hz、MTC 9000 15.625 ± 0.3 kHz / 45~70 Hz |
| 電源 | +5 V のみ使用、4.75~5.5 V で動作、> 5.5 V で保護、消費 < 1 A(推定)、入力容量 ≤ 220 µF | RT-65A "4.75 ~ 5.5V"、JST GEC 3 A/接点、HVC-002 10 V 850 mA |
| 音声 | BTL(10 = +、L = −)、4 Ω で 3 W 以上、短絡保護、11/M は無接続 | 筐体のスピーカ 4/8 Ω、NeoGeo の BTL 系アンプ、"speaker- ... isn't ground" |
| 入力 | プルアップ 4.7 kΩ@5 V / 3.3 kΩ@3.3 V、直列 1 kΩ、10 nF。25/26/c/d は入力専用 | CRE401 1k/330/33 nF、DE10Jamma 1k/10 nF、D2MC-01 の最小負荷 1 mA、Astro City の SW4/5 配線 |
| コインのデバウンス | Low ≥ 10 ms で確定、High ≥ 10 ms で解除、1 パルスを 1 枚 | 電子セレクタ 50 ± 5 / 72 ± 3 ms、HX-616 30~100 ms、AD-81P2 の投入間隔 ≥ 0.5 s |
| カウンタ駆動 | ロジックレベル N-MOSFET のローサイド、≥ 30 V、≥ 0.5 A、還流ダイオードを基板に搭載、ON 100~120 ms / OFF ≥ 100 ms、+5 V と +12 V のコイル両対応 | NX-06PD 5VDC、Astro City/Windy は +5 V、MVS は +12 V、ULN2003 の VCE(sat) 約 1 V、ライン精機 MZ 25 ms、KEP 120/80 ms |
| ロックアウト駆動 | 同じドライバ、連続 ≥ 200 mA@12 V | 旭精工 QL-102 157 mA / SB-101 210 mA、MVS ULN2003 |

---

## 既存ノートへの訂正(`jamma_standard.md` に対して)

1. **「多くの日本製筐体は -5V を供給しない」は誤り。** Astro City / New Astro City(−5 V 0.1 A)、Egret II(−5 V を 5/E に配線)、Windy(−5 V 0.5 A)、Exceleena 2(−5 V 0.2 A)は −5 V を供給している。供給しないことを確認できたのは Blast City の JAMMA ループだけ(出典は §5 の表)。
2. **「コインカウンタは +12 V に接続(MVS の例)」は、日本の筐体には当てはまらない。** Astro City と Windy はカウンタが +5 V 系で、Cyber Lead の部品は "NX-06PD 5VDC"。Sega NAOMI 系もカウンタを +5 V + 100 Ω で偽装している。ドライバは +5 V コイルを前提に、飽和電圧の小さい素子を選ぶ必要がある(§6)。
3. **「ロックアウト (9/K) も同様に +12V コイルを GND へ落とす」**は MVS/米国系の話で、日本の筐体(Astro City、Egret II、Windy)では 9/K と J は配線されていない(図面読み取り)。日本の「ブロッカー」はセレクタ側の部品(旭精工 QL-102 等)。
4. **25/c/26/d を「未接続で安全」とした推論は不十分。** Astro City はここを 1P/2P SW4・SW5 として、Egret II と Windy は SPARE1/2 として配線している。基板側は入力専用(プルアップ)か無接続にし、出力や電源・GND に使ってはいけない。
5. **「音量調整の規約は未確認」→ 筐体側で調整するのが慣習。** Blast City は 100 Ω 10 W のレオスタット、Astro City は電源ユニットの SOUND VOL.、Windy は 2 連 SOUND VOLUME、Egret II は VOL。基板の音量 VR は必須ではない。スピーカは 4 Ω(Egret II)/ 8 Ω ×2(Astro City)/ 8 Ω(Blast City)。
6. **機械寸法の Gaps の一部を解消。** JST GEC("conforns to the JAMMA standards")の参考図: ピッチ 3.96 ± 0.05、1~28 の間隔 106.92 ± 0.05、エッジ幅 114.6(+0/−0.2)、7/H にキー溝(幅 2.3 ± 0.035、深さ 10.0 と読める)、C0.5、適合基板厚 1.6 ± 0.15 mm、接点 3 A。第1パスの「+5V(2~3A/pinでなく多数の指で分担)」という表現は、「1 接点 3 A 定格」に置き換えるべき。
7. **CRE401 の値の補足**: 1 kΩ プルアップ・330 Ω 直列に加えて、C は 33~43 nF(実測)。
8. **0.7 Vpp/75 Ω を「民生用」とだけ書いた点の補足**: Blast City は同じモニタに 75 Ω / 0.7 Vp-p(D-SUB15)と 2 kΩ / 3.0 Vp-p(AMP 6P = JAMMA)の切替(SW3)を持つ。JAMMA 基板が狙うのは後者。
9. **第1パスの映像の推論「各ch 75~330Ω直列+…約2~3Vpp」**: 実在する基板は抵抗 DAC 直出しで、合成出力インピーダンスは約 120~130 Ω、開放は最大 3.5 V(Neo Geo)。「75 Ω 直列」は不要で、100~150 Ω の DAC 合成インピーダンスが実在基板並み。

---

## 未確認事項(まとめ)
- Nanao MS8/MS9 と Toei のサービスマニュアルの映像入力レベル・インピーダンス・同期閾値・水平垂直の引込み範囲。
- CPS2 / Taito / Konami 基板の RGB 出力段とアンプ IC の一次資料。
- Sega 400-5198 などの筐体電源の最小負荷と OVP。
- NX-06PD / GX-06PD / Sega 220-5412 のコイル抵抗・定格電圧(5 V は Cyber Lead の部品表でのみ確認)。
- 旭精工のブロッカー(QL-102)と VM81-M の極性(通電で阻止か受付か)。
- Windy / Cyber Lead / Exceleena のスピーカのインピーダンス。
- VS. System のモニタ型番(PC-10 は Sanyo 20-EZV / 20-Z2AW で確認)。
- NES 由来の 15.7458 kHz を日本筐体のモニタで実測した報告。
