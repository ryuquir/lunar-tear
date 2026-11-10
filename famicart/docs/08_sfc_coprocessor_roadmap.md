# 08 SFC 拡張チップを FC で使う：ロードマップ

最終目標（2026-11-08 ユーザー指定）: **SA-1・Super FX を含む SFC の拡張チップをすべてエミュレートし、それらを使った FC のゲームを作れるようにする。**

## 定義

- **ここで作るもの**: SFC ゲームを動かすための互換チップではない。FC カセットの中で動く**コプロセッサ**で、FC のゲームが $4020-$7FFF のレジスタから呼び出す。演算結果は WRAM（CPU 側）や CHR-RAM（PPU 側）に直接書き込まれる。
- **命令セット・動作は元のチップに合わせる**: SFC 用に書かれたツールや知識（GSU のアセンブラ、DSP-1 の演算コマンド）をそのまま流用できるようにする。
- **SFC のバスの時間は再現しない**: 動けばよく、相手は FC の 1.79 MHz の CPU と 60 fps の画面。

## 要点

1. **計算資源**: RP2350 は Cortex-M33 ×2（150 MHz 定格）と SRAM 520 KB を持つ。実測では 1.1 V のまま 312 MHz 前後まで動いた報告が多い（保証外）[8][9][10]。
2. **前例**: RP2350 に Snes9x を移植した pico-snesPlus は 384 MHz で動く。SNES 本体ごとエミュレートしたうえで、Super FX・SA-1 のゲームは 3 フレームに 1 回の描画になる。ボトルネックは外付け PSRAM の帯域で、CPU ではない [11]。マイコン上で 65C816 や Super FX の単体コアを実時間で動かしたという公開記録は見つからなかった。
3. **rev E での置き場所**:
   - **CPU 側の処理（U1）**: SA-1、DSP-n、S-DD1・SPC7110 の展開。結果は WRAM に書く。
   - **絵を描くもの（U2）**: Super FX、Cx4。PPU が読む CHR-RAM を U2 自身が持っているので、描いた結果がそのまま画面に出る。
   - どちらもコア 1 はバス応答で埋まっているので、使えるのはコア 0 の空き時間だけ。重いチップ（SA-1・GSU-2）は、コプロセッサ専用のマイコンを足した **rev F** が必要になる見込み。
4. **権利**: Cx4・DSP-n・ST010/011/018 は、チップ内部のプログラムやデータ ROM（ダンプ）が動作に必要。これは任天堂などの著作物なので同梱できない。代わりに、snes9x のように動作を C で書き直したもの（HLE）を使う。DSP-n は HLE が既にある [6]。ST018 は HLE がない。
5. **2026-11-10 の再調査（一次資料で確認済み）**: 下の「提供できる範囲」の節にまとめた。要点は、(a) ST018 は HLE がどこにも無く、ST011 は未完成の HLE が 1 つあるだけなので、この 2 つはチップ内蔵 ROM のダンプなしには提供できない、(b) 公開されている HLE はどれもライセンスに条件がある、(c) Cortex-M33 は ARM（A32）命令を実行できないので、ST018 のコードを直接走らせる案は成り立たない、(d) rev G での置き場所は [12](12_rev_g_plan.md) に移した、の 4 点。

## チップ別の比較と実装方針

| チップ | 中身 | クロック | 市販 SFC 数 | ダンプ | famicart での方針 | 段階 |
|---|---|---|---|---|---|---|
| S-DD1 | 展開回路 | バス駆動 | 2 | 不要 | U1 で展開して WRAM / U2 CHR-RAM へ（CHR 圧縮として有用） | S1 |
| SPC7110 | 展開 + 乗除算 + マッパー | 不明 | 3 | 不要 | U1。乗除算は MMC5 の乗算器と同じ扱い | S1 |
| OBC-1 | スプライト表の補助 | — | 1 | 不要 | U1。FC の OAM（$0200 ページ）向けに意味を置き換える | S1 |
| S-RTC / RTC-4513 | 時計 | 32.768 kHz | 各 1 | 不要 | U3（常時動作）。電池なしなら起動時刻からの経過 | S1 |
| DSP-1〜4 | NEC µPD77C25（24 ビット命令） | 7.6 MHz | 約 16〜19（DSP-1） | 実機コードは 8 KB 必要 | snes9x 型の HLE（3D 回転・投影コマンド）を U1 で | S2 |
| Super FX（GSU-1/2） | 16 ビット RISC、命令 98 種、レジスタ 16 本 | 10.74 / 21.4 MHz | 約 10 | 不要 | U2 コア 0 で GSU インタプリタ。PLOT 命令の出力先を FC の 2 ビット CHR 形式にする | S3 |
| Cx4 | 日立 HG51B169 | 20 MHz | 2 | データ ROM 3 KB | 三角関数表を自前で生成し U2 に | S3 |
| SA-1 | 65C816 + DMA・乗除算・ビットマップ変換 | 10.74 MHz | 35 | 不要 | まず U1 コア 0 で低速版、実用速度は rev F の専用マイコン | S4 |
| ST010 / ST011 | µPD96050 | 10〜11 / 15 MHz | 各 1 | 52 KB 必要 | ST010 は HLE。ST011 は完成した HLE が無い（下の節） | S5 |
| ST018 | ARMv3（ARM60 系） | 21.44 MHz | 1 | 160 KB 必要 | HLE が無い。利用者が持つダンプがあれば ARMv3 のインタプリタで動かせるが、実時間にはならない。~~M33 上で ARM 命令を直接実行する案~~ は不可（Cortex-M は A32 命令を持たない）[12] | S5 |
| BS-X MCC | メモリ制御 | — | 衛星放送 | BIOS 必要 | 対象外（放送が前提） | — |
| スーパーゲームボーイ（ICD2 ＋ゲームボーイの CPU） | 別のゲーム機 1 台分 | — | — | 起動 ROM 必要 | 対象外 | — |
| サテラビュー用データパック、スーファミターボ、ニンテンドウパワー（書き換えカセット）、XBAND（モデム） | カセット側の周辺機器 | — | — | — | 対象外（演算チップではない） | — |

クロックの資料間の違い: Super FX は GSU-1 を 10.74 MHz、GSU-2 を 21 MHz とする資料と、21.47 MHz の信号で MARIO Chip 1 だけ 10.74 MHz とする資料がある。ST010 は 10 MHz とする資料と 11 MHz とする資料がある。DSP-1 は 7.6 MHz の記載と、部品の上限 8.192 MHz だけの記載がある [1][2][3]。

## 提供できる範囲（2026-11-10、fullsnes と各エミュレータのソースで確認）

| 区分 | チップ | 提供の形 | 根拠 |
|---|---|---|---|
| A. プログラムを外から与えるもの（内蔵 ROM なし） | SA-1（65C816、10.74 MHz）、Super FX（GSU-1／2）、Cx4（日立 HG51B169。内蔵は数表 1024 × 24 ビットだけで、プログラムはゲーム側の ROM にある） | 命令単位のインタプリタ。Cx4 の数表は fullsnes にある式（除算・平方根・正弦・逆正弦・正接・余弦）から生成する | fullsnes [1]、bsnes の数表 [4] |
| B. 固定機能 | S-DD1、SPC7110（展開・データ ROM ポート・乗除算・RTC-4513）、OBC-1、S-RTC | レジスタ動作の再実装。内蔵プログラムは無い。fullsnes に未解明と書かれたレジスタが一部ある（S-DD1 の $4802／$4803、OBC-1 の $7FF7、SPC7110 の数か所） | fullsnes [1] |
| C. 内蔵プログラムを持つもの（HLE あり） | DSP-1／1A／1B、DSP-2、DSP-3、DSP-4（NEC µPD77C25。命令 ROM 2048 × 24 ビット、データ ROM 1024 × 16 ビット）、ST010（µPD96050） | コマンド単位の HLE（数マイクロ秒で終わる）。公開実装: snes9x（DSP-1〜4、ST010、Cx4）、ZSNES（DSP-1・3・4、ST010、Cx4、S-DD1、OBC-1）、bsnes（DSP-1・2・4、ST010、Cx4） | 各ソース [5][6][13] |
| D. 内蔵プログラムを持ち、HLE が無い／未完成 | ST011（µPD96050、将棋ソフト 1 本）、ST018（ARMv3、将棋ソフト 1 本） | **提供できない。** ST011 は ZSNES に未完成の HLE があるだけ（作者自身が「足りない命令が多い」と書いている）。ST018 は snes9x・bsnes 系とも応答の殻だけ。Mesen2・ares・MAME は内蔵 ROM のダンプを使う低位エミュレーションで、ダンプは著作物。利用者が自分のチップから取ったダンプを持つ場合に限り、低位エミュレーションで動かせるが、実時間にはならない | snes9x の seta011.cpp／seta018.cpp、ZSNES の seta11.c、Mesen2・ares のファーム一覧 [3][6][13][14] |
| E. 対象外 | スーパーゲームボーイ、サテラビュー（BS-X）、スーファミターボ、ニンテンドウパワー、XBAND、MSU-1（当時の製品ではない） | — | fullsnes [1] |

**ライセンス**（公開 HLE を使う場合）:

- snes9x: 非商用に限る（LICENSE: 「for non-commercial purposes」「Snes9x is freeware for PERSONAL USE only」）。これを含むファームを載せたカセットは売れない。
- ZSNES: GPL バージョン 2 のみ。bsnes: GPL バージョン 3 以降。どちらも、ファームを配るならソースの公開が条件になる。
- snes9x の DSP-1 と DSP-3 の HLE には、チップのデータ ROM（1024 語の数表）がそのまま入っている。Cx4 の数表は数式から作れるが、DSP の数表が数式だけで再現できるかは未確認。
- 個人で使う範囲ではどれも使える。配布を考えるなら、公開されている仕様（fullsnes のコマンド表）から書き直すのが確実。

**速度の見通し**（未測定。実機での計測が要る）: RP2350 の 1 コアで、SA-1 は実チップの 0.5〜0.9 倍、Super FX は GSU-1 相当（0.3〜0.8 倍）という命令数からの見積もり。µPD77C25・HG51B169・ARM を命令単位で実時間に再現するのは無理で、DSP・ST010 はコマンド単位の HLE（実チップより速い）で、Cx4 は「数表つきの演算機能」として使う。pico-snesPlus の「Super FX・SA-1 のゲームは 3 フレームに 1 回」は、SNES 全体を再現したうえで外付け PSRAM の帯域が足を引いている数字で、チップ単体の速度ではない [11]。

**市販本数**（fullsnes の章見出しによる）: SA-1 35、Super FX 10（未発売・試作を含む。発売されたのは 8）、Cx4 2、DSP 系と ST010／ST011 を合わせて 23、ST018 1、OBC-1 1、S-DD1 2、SPC7110 3、S-RTC 1。

## 具体例（FC で何ができるか）

- **Super FX → 疑似 3D**: GSU が U2 の CHR-RAM に直接ポリゴンを描く。PPU は普通に BG タイルとして読むので、FC のまま『スターフォックス』型のワイヤーフレームや塗りつぶしポリゴンが出せる。BG 1 画面ぶんのタイル（256 枚 = 4 KB）を毎フレーム書き換えられる。
- **DSP-1 → 回転・拡大**: CPU は角度と座標を渡すだけで、投影後の座標を WRAM から読む（『パイロットウイングス』型の計算をコプロセッサで）。
- **SA-1 → 第 2 の CPU**: 65C816 で書いた AI・物理・展開を FC の CPU と並行して動かす。
- **S-DD1 → 大容量 CHR の圧縮**: 1 MB を超えるグラフィックを圧縮して持ち、バンク切り替えの代わりに展開して CHR-RAM に流し込む。

## 段階

| 段階 | 内容 | 必要なもの |
|---|---|---|
| S0 | 「FC コプロセッサ ABI」を決める。専用マッパー番号（NES 2.0 の未割り当て番号）、レジスタ窓、完了通知（IRQ または状態ビット）を定義 | ファームのみ |
| S1 | S-DD1・SPC7110・OBC-1・RTC（固定機能で軽い） | rev E |
| S2 | DSP-1〜4 の HLE | rev E |
| S3 | Super FX（GSU）を U2 で、Cx4 | rev E（性能測定してから判断） |
| S4 | SA-1。性能が足りなければ rev F（コプロセッサ専用の Pico 2 を追加） | rev F 候補 |
| S5 | ST01x。ダンプなしで動かせる範囲だけ | 調査 |
| 並行 | 開発キット: ca65 用のマクロ・サンプルゲーム、PC 上のエミュレータ（core をそのまま使う） | — |

前提: 市販マッパーの移植（フェーズ 5）と、rev E の実機確認が先。

## 出典

1. fullsnes — https://problemkaputt.de/fullsnes.htm
2. Wikipedia: List of Super NES enhancement chips — https://en.wikipedia.org/wiki/List_of_Super_NES_enhancement_chips
3. ares cartridge database code — https://github.com/ares-emulator/ares/blob/master/mia/medium/super-famicom.cpp
4. bsnes Cx4 data ROM — https://github.com/bsnes-emu/bsnes/blob/master/bsnes/sfc/coprocessor/hitachidsp/data-rom.cpp
5. bsnes coprocessors — https://github.com/bsnes-emu/bsnes/tree/master/bsnes/sfc/coprocessor
6. snes9x (dsp1-4.cpp, seta010/011/018.cpp, c4.cpp, sdd1.cpp, spc7110.cpp, srtc.cpp, obc1.cpp) — https://github.com/snes9xgit/snes9x
7. SNESdev wiki: Super FX — https://snes.nesdev.org/wiki/Super_FX
8. Raspberry Pi RP2350 — https://www.raspberrypi.com/products/rp2350/
9. RP2350 product brief — https://datasheets.raspberrypi.com/rp2350/rp2350-product-brief.pdf
10. Pimoroni: Overclocking the Pico 2 — https://learn-new.pimoroni.com/article/overclocking-the-pico-2
11. pico-snesPlus — https://github.com/fhoedemakers/pico-snesPlus
12. Arm ACLE（M プロファイルは A32 命令を持たない）— https://arm-software.github.io/acle/cmse/cmse.html
13. ZSNES 1.51 のチップ実装（dsp1emu.c、dsp3emu.c、dsp4emu.c、c4emu.c、seta10.c、seta11.c、GPL v2）— https://github.com/emillon/zsnes
14. Mesen2（内蔵 ROM のファイル一覧。GPL v3）— https://github.com/SourMesen/Mesen2 、 snes9x の LICENSE — https://raw.githubusercontent.com/snes9xgit/snes9x/master/LICENSE
