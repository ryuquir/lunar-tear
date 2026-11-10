# JAMMA 規格と JAMMA 基板の電気的・機械的要件

(調査日 2026-11-10。調査は約20回のツール呼出で打ち切り、未確認事項は Gaps / 未確認 に明記)

## 56ピン JAMMA ピン配置

### Takeaway
標準JAMMAは 56ピン(片面28)・ピッチ 0.156in(3.96mm)。複数の独立ソースで 1-24/A-b・電源・ビデオ・音声・コイン系は一致。ばらつきは (a) pin5/E の -5V、(b) pin25/26/c/d(拡張ボタン)、(c) 11/M の扱い。入力はすべてアクティブLow(GNDへ落とす)。

### Cited Findings
完全表(パーツ面 1-28 / ハンダ面 A-f。文字 G,I,O,Q は欠番)。出典: Arcade Otaku Wiki / Hardware Book / old.pinouts.ru の3者を突合。

| パーツ面 | 信号 | ハンダ面 | 信号 |
|---|---|---|---|
| 1 | GND | A | GND |
| 2 | GND | B | GND |
| 3 | +5V | C | +5V |
| 4 | +5V | D | +5V |
| 5 | -5V | E | -5V |
| 6 | +12V | F | +12V |
| 7 | KEY(スロット/ピン無し) | H | KEY |
| 8 | Coin Meter 1(コインカウンタ1) | J | Coin Meter 2 |
| 9 | Coin Lockout 1 | K | Coin Lockout 2 |
| 10 | Speaker + | L | Speaker - |
| 11 | Audio +(プリアンプ出力、ほぼ未使用) | M | Audio GND |
| 12 | Video Red | N | Video Green |
| 13 | Video Blue | P | Video Sync(負極性コンポジット) |
| 14 | Video GND | R | Service Switch |
| 15 | Test Switch | S | Tilt(Slam) Switch |
| 16 | Coin 1 | T | Coin 2 |
| 17 | 1P Start | U | 2P Start |
| 18 | 1P Up | V | 2P Up |
| 19 | 1P Down | W | 2P Down |
| 20 | 1P Left | X | 2P Left |
| 21 | 1P Right | Y | 2P Right |
| 22 | 1P Button 1 | Z | 2P Button 1 |
| 23 | 1P Button 2 | a | 2P Button 2 |
| 24 | 1P Button 3 | b | 2P Button 3 |
| 25 | (1P Button 4) 非公式 JAMMA+ | c | (2P Button 4) 非公式 |
| 26 | (1P Button 5) 非公式 / 未使用 | d | (2P Button 5) 非公式 / 未使用 |
| 27 | GND | e | GND |
| 28 | GND | f | GND |

- 上表は Arcade Otaku Wiki(21 May 2022版)の表そのもの。入力はGNDで有効(active low)、Speaker +/- (10/L) はモノラル・アンプ後出力、Audio +/- (11/M) はプリアンプ出力でほぼ未使用、Service(R)はクレジット+1(カウンタ増えず)、Tilt(S)は 'slam' — [Arcade Otaku Wiki JAMMA](https://wiki.arcadeotaku.com/w/JAMMA)
- 同一の割当(5=-5V, 25=P1 B4 (括弧付き), 26=P1 B5 括弧 or 未使用) — [old.pinouts.ru JAMMA](https://old.pinouts.ru/Slots/jamma.shtml) (原典 Hardware Book、[ミラー](https://k1.spdns.de/Develop/Hardware/Infomix/Stecker%20und%20Kabel/hwbook/connector/bus/jamma.html)): Hardware Book 版は 25/c=Button4、26/d は "Not used"、pinouts.ru 版は 26/d=Button5、27/e=Button6(Hardware Book版では27/e,28/fはGND)。→ 出典間の不一致。信頼すべきは 27/28/e/f=GND。
- 別の第三者表(videogametesteroffer ブログ)は 25/26/c/d を "No connection"、5/E=-5V、11/M を "No connection" と記載 — [blog](https://videogametesteroffer.blogspot.com/2020/04/understand-jamma-pcb-and-edge-connector.html)。(11/M を未接続とする点は他と不一致、ブログなので信頼度低)
- Neo Geo MVS 版は E/5 を未使用(-5V無し)、25/c/26/d を Select 系に流用し、11/M 等を使用する独自派生(JAMMA非互換のルックアライク) — [NeoGeo Dev Wiki](https://wiki.neogeodev.org/index.php/JAMMA_connector_pinout)(ただし取得内容は要約で正確なピン対応は未確認)
- Capcom CPS2 など一部ゲームは c/25 を4人目用などに流用 — [Arcade Otaku Wiki](https://wiki.arcadeotaku.com/w/JAMMA)
- 旧 ArcadeControls wiki の表は pin20/21 (X/Y) の Left/Right が逆とする指摘あり(検索スニペット) — [検索結果経由 oldwiki.arcadecontrols.com](https://oldwiki.arcadecontrols.com/index.php/JAMMA)。本表(20=Left, 21=Right)が多数派。
- 歴史: JAMMA配線標準は 1985年導入(英Wikipedia/Arcade Otaku)、日本語Wikipediaは「1986年、JVSは1997年」と記載。協会は1981年設立、2018年 AOU と統合し JAIA — [en.wikipedia](https://en.wikipedia.org/wiki/JAMMA) / [ja.wikipedia](https://ja.wikipedia.org/wiki/JAMMA)。1985 vs 1986 は不一致(要旧規格原本確認)。
- Sega Blast City の JAMMA 側仕様(後述の映像節): [Arcade Otaku Wiki Blast City](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide)

### Gaps
- JAIA 公式の旧JAMMA配線表(setup-japan.com の「旧JAMMAコネクタ配線表」)原本は未取得。公式で -5V が規定か 未確認。


### Inferences
- 設計上は「5/E の -5V は未使用・無接続」「25/26/c/d は未接続(使うならJAMMA+として任意)」「27/28/e/f と 1/2/A/B は全てGND」で安全。11/M(Audio +/GND)は出力しない。
- 多くの日本製筐体は -5V を供給しない(下記電源節参照)。

## 機械寸法(エッジコネクタ)

### Takeaway
確認できたのはピッチ 0.156in(3.96mm)・片面28極・基板厚1.6mm・キー切欠き位置が 7/H のみ。フィンガー幅/長さ/切欠き寸法/面取り角度は一次資料を取得できず 未確認。

### Cited Findings
- ピッチ .156in (3.96mm)、基板側がオス(エッジ)、片面28ピン(キー含む)計56 — [en.wikipedia JAMMA](https://en.wikipedia.org/wiki/JAMMA), [NeoGeo Dev Wiki](https://wiki.neogeodev.org/index.php/JAMMA_connector_pinout)
- 一部の古い基板(麻雀等)は 4mm ピッチ、新しい基板は 3.96mm という報告(フォーラム、確度低) — [arcade-projects](https://www.arcade-projects.com/goto/post?id=410606)
- 基板厚 1.6mm、エッジは面取り(bevel)、接点は硬質金フラッシュ(ENIGでも足りる可能性) — [OSH Park shared project](https://oshpark.com/shared_projects/KrFAoVRl)。ORB(後述)も 1.6mm 2層・寸法 129x117mm で製造 — [ole00/orb README](https://raw.githubusercontent.com/ole00/orb/master/README.md)
- キー: 7/H はコネクタ側に樹脂のキーがあり、基板側にスロットを切って逆差し防止。キー無しのハーネスもあり逆差しすると入力IC破損の恐れ — [Arcade Otaku Wiki](https://wiki.arcadeotaku.com/w/JAMMA), [NeoGeo Dev Wiki](https://wiki.neogeodev.org/index.php/JAMMA_connector_pinout)
- 既成KiCadフットプリント: 専用ライブラリは見つからず。jzdziarski/jamma に JAMMA エッジ用 CAD(Universal edge 等)あり。ただしライセンスは "educational use only"(OSS ライセンス無し) — [GitHub jzdziarski/jamma](https://github.com/jzdziarski/jamma/), [解説ブログ](https://www.zdziarski.com/blog/?p=13445)。ORB / DE10Jamma / mobiusstriptech の ZaxxonToJAMMA(44ピン3.96mm)も JAMMAエッジを持つ(CADフォーマットは未確認、ORBはgEDA)。

### Inferences
- 自作フットプリントが現実的: 3.96mm ピッチのパッドを両面28個、7/H位置に切欠き。寸法は実コネクタ(JAMMA基板の実測)で要確認。

### Gaps
- 未確認: フィンガー幅・長さ(一般に 2.5mm 幅程度との話はあるが出典無し)、キー切欠き寸法と位置、面取り角度、金メッキ厚、典型基板サイズ、取付穴規約(JAIA規格原本・コネクタメーカ図面が必要。setup-japan.com と jamma.or.jp は取得失敗)。

## 電源

### Takeaway
+5V(2~3A/pinでなく多数の指で分担)・+12V・-5V の3系統が規格上存在するが、-5Vを使う基板はごく少数。+5Vは調整式で、負荷時降下に注意。Blast Cityは-5Vを供給しない。

### Cited Findings
- 規格上の電源: +5V(game)、+12V(sound) — [en.wikipedia JAMMA](https://en.wikipedia.org/wiki/JAMMA)
- 汎用フォーラムの目安最小容量: +5V 12A / +12V 2A / -5V 1A。別例: 12V 4A, 5V 15A, -5V 1A — [arcadecontrols forum](https://forum.arcadecontrols.com/index.php/topic,143607.0.html)(検索要約経由、確度低)
- 集めた基板のうち -5V を使うものは1枚だけという報告 — 同上検索結果 / [arcadeotaku forum -5V thread](https://forum.arcadeotaku.com/viewtopic.php?p=455265)(本文はAnubisで取得不可)
- Sega Blast City: JAMMA変換ループ 600-6738-21 使用時 "-5v is not supplied"。電源は +5V/+3.3V/+12V のみ — [Arcade Otaku Blast City](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide)
- DE10Jamma: 調整式の+5V電源を想定。+5Vを上げ過ぎるとDE10-Nanoの過電圧保護で起動しない — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)
- 5V線1本だと電流が制限される、2本目の+5V/GNDを足せとの報告。調整式+5VでAdjustすると他レールも連動 — 上記arcadecontrols検索結果

### Inferences
- 低コスト基板設計: +5Vのみで動かし、+12V/-5Vは使わない(必要なら+12Vから降圧)。+5Vは4.75~5.25V程度を想定し、3/4(+5V)両ピン・1/2/A/B/27/28/e/f(GND)全ピンを使う。突入電流対策として入力に大容量電解+TVS/ポリスイッチを置く(出典無し、設計判断)。

### Gaps
- 未確認: JAMMA公式の1ピン当たり電流定格、実測の+5V設定値(5.1V等)、日本筐体電源(Astro City/Egret II)の具体的容量、突入電流の実測値。

## 映像(RGB・同期)

### Takeaway
JAMMAは映像レベルを標準化していない。実機は「アナログRGBでTTL級振幅(3~5Vpp)・高入力インピーダンス(1k~10k)」が通説。Sega Blast City の仕様は正極性 3.0Vp-p・2kΩ・負極性コンポジット同期。0.7Vpp/75Ωは民生用。

### Cited Findings
- Blast City JAMMA映像入力: "Video Signal = POSITIVE, 3.0Vp-p, 2kΩ Impedance & SYNC = NEGATIVE, H/V Composite"; 制御出力インピーダンス8Ω — [Arcade Otaku Blast City](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide)
- アーケードRGBSは NTSC同様のタイミングだが電気特性は "TTL level amplitude (3-5 Vpp)"、モニタ入力は 1k~10kΩ、家庭用は0.7Vpp/75Ω。JAMMAは映像を規格化せず、モニタ側に調整ポットが付く — [gbs-control wiki Arcade Boards](https://github.com/ramapcsx2/gbs-control/wiki/Arcade-Boards)
- 負極性コンポジット同期は標準(Wikipedia: analog RGB, negative composite sync) — [en.wikipedia](https://en.wikipedia.org/wiki/JAMMA)
- 実装例: DE10Jamma は 6bit R-2R DAC(604Ω/1kΩ系)×3で出力、出力はNeo Geo MVS並みで「アーケードモニタの調整範囲内」 — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)
- ORB: 5V、15kHz、負極性CSync、BBGから出力。BOM に CLC4007(クワッドOPアンプ)、74HC4066、抵抗 51/470/510Ω 等 — [ORB README](https://raw.githubusercontent.com/ole00/orb/master/README.md), [bom.txt](https://raw.githubusercontent.com/ole00/orb/master/bom.txt)
- pi2jamma(商用、設計は公開): VGA666 + THS7314 ビデオアンプ — [falz.net](https://falz.net/wiki/Pi2jamma_hardware_and_software_info)
- 古いRGB出力段の一般例として470Ω直列でTTL5V→約0.7Vの目安(フォーラム、数値は例) — arcade-projects 検索結果(確度低)

### Inferences
- 設計: RGBは3Vpp前後・2kΩ負荷を想定。PPUのコンポジット/RGB出力は低振幅なので、トランジスタ/オペアンプ・バッファで約2~3Vppへ増幅し、各ch 75~330Ω直列+負荷に対し調整。CSyncは負極性TTL(約4~5V)を出す。値は実機モニタで要調整(ポット付きが望ましいが部品点数との兼ね合い)。

### Gaps
- 未確認: Astro City/Egret II/Namco/Konami 筐体別の入力レベル、モニタ同期ロック許容範囲(15.73~15.75kHz, 60.0988Hz, 262本非インターレース, 奇数フレームのドット飛ばし)の実測や出典、Nanao/Toeiシャーシ仕様書。

## 音声

### Takeaway
JAMMAのスピーカ出力(10/L)はモノラルで、基板側にパワーアンプが必要。Speaker -(L) は GND ではなくBTLのもう一方の出力であることがあり、接地すると破損する。

### Cited Findings
- Speaker +/- (10/L) はモノラル・アンプ後で外部アンプ不要、Audio +/- (11/M) はプリアンプ出力でほぼ未使用 — [Arcade Otaku Wiki](https://wiki.arcadeotaku.com/w/JAMMA)
- 負側はGNDでなくてもよく、ブリッジアンプとして逆相駆動される。ブリッジ出力のどちらかを接地するとアンプが壊れるとの警告 — [arcadecontrols forum](https://forum.arcadecontrols.com/index.php/topic,69692.0.html) 等(検索要約経由、確度低)
- 使用アンプ例: LM380N 2.5W(pi2jamma)、TDA7496(DE10Jamma, 2ch)、PAM8403モジュール(ORBオプション、2kΩトリマ付き) — 各README/wiki(上記URL)
- DE10Jamma: Mono/Stereo ジャンパ、2極RCフィルタでPWMを平滑 — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)
- Blast City: JAMMA音声入力はモノ(10/L)。アンプ搭載筐体 — [Arcade Otaku Blast City](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide)

### Gaps
- 未確認: 標準スピーカ抵抗(一般に4~8Ω)と出力(数W)の出典、音量調整の規約(多くの筐体は外部ボリューム or 基板上VR)。

## 入力・コイン・サービス

### Takeaway
全入力はGND接続でアクティブLow。コインカウンタ(8/J)は+12V(Neo Geo MVSの例)に接続したコイルをGNDへ落とす低電位駆動、ロックアウト(9/K)も同様。逆起電力ダイオードが必要。

### Cited Findings
- 全入力アクティブLow。Coin 1/2 はGNDパルス。Service(R)はクレジット+1でカウンタ非加算。Test(15)でテストモード。Tilt(S)は多くのゲームで未実装 — [Arcade Otaku Wiki](https://wiki.arcadeotaku.com/w/JAMMA)
- カウンタは機械式、MVSでは一端が+12V、他端がJAMMA 8/Jに接続。ロックアウトも通常+12V固定のコイルで、基板が第2端子をGNDへ落とす。MVSはNEO-F0がULN2003(オープンコレクタ)で駆動。コイル無通電時はコインは返却側(フェイルセーフ) — [NeoGeo Dev Wiki Coin counter](https://wiki.neogeodev.org/index.php/Coin_counter), [Coin lockout](https://wiki.neogeodev.org/index.php/Coin_lockout)
- 逆バイアスダイオードをコイルに並列、2N2222/2N3904等の小信号トランジスタで駆動可、との実用情報。電圧は5V/6V/12V等まちまち — [arcadecontrols forum 検索結果](https://forum.arcadecontrols.com/index.php/topic,85039.0.html)(確度低)
- 入力保護: NeoGeoはCRE401(1kプルアップ+330Ω直列+コンデンサ)の抵抗コンデンサアレイ — [NeoGeo Dev Wiki CRE401](https://wiki.neogeodev.org/index.php?title=CRE401)。DE10JammaはRCフィルタでFPGAを保護し、デバウンスはしない(コア側で実施) — [DE10Jamma README](https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md)
- pi2jamma: 74LS165×3で24入力 — [falz.net](https://falz.net/wiki/Pi2jamma_hardware_and_software_info)。ORB: 24個のスイッチングダイオード(1N4148系)を使用 — [bom.txt](https://raw.githubusercontent.com/ole00/orb/master/bom.txt)
- Blast City制御出力インピーダンス 8Ω(基板側入力は低インピーダンスのスイッチ) — [Arcade Otaku Blast City](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide)

### Inferences
- 入力: 10k プルアップ(または内蔵)+1k直列+100nF〜10nF、デバウンスは基板で数ms~20ms。コインは機械式でバウンス多く、20~50ms以上の確定+最小パルス幅要件を確認。コイン電子式の出力は不明(未確認)。
- コインカウンタ/ロックアウト: NMOS/NPNで+12V(or +5V)コイルをGND側でスイッチ、コイルに逆並列ダイオード(1N4148/1N4007)。通電時間は約50~100ms(未確認、設計判断)。

### Gaps
- 未確認: コイル電流値(典型数十~百数十mA)、電子式コインアクセプタ出力仕様・パルス幅、Service/Test/Tilt の電気的詳細(Slam)。

## 背景と非互換ルックアライク

### Cited Findings
- JAMMA配線標準は1985年導入(英語)、日本語Wikipediaでは1986年。JVSは1996/97年、RS-485ベース、JVSで入力増・ステレオ — [en.wikipedia](https://en.wikipedia.org/wiki/JAMMA), [ja.wikipedia](https://ja.wikipedia.org/wiki/JAMMA)
- Neo Geo MVS は独自派生(25/c/26/dをSelect等に流用、-5V無し、ステレオ) — [NeoGeo Dev Wiki](https://wiki.neogeodev.org/index.php/JAMMA_connector_pinout)
- Sega Blast City は JAMMA/JVS/Model3 兼用の汎用筐体I/Oボードを内蔵 — [Arcade Otaku Blast City](https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide)
- 旧規格 Electrocoin 等が存在 — [Hardware Book electrocoin](https://connectorbook.com/hardwarebook/connector/bus/electrocoin.html)(検索結果のみ)

### Gaps
- CHAMMA の資料は未取得(未確認)。

## 既存オープンハードウェア事例

### Cited Findings
- ole00/orb (Open Retro Board): JAMMAエッジ、5V映像、MIT、gEDAスキマ、BBGベース、PAM8403 — [GitHub](https://github.com/ole00/orb)
- MisterJamma/DE10Jamma: JAMMA/MVSオーディオ・ビデオ・制御、R-2R DAC、TDA7496、LCSC部品番号入りBOM(10nF C83170, 1k C140870 等。JLCPCB Basic適合性は個別確認) — [GitHub](https://github.com/MisterJamma/DE10Jamma)(ライセンスは未確認)
- jzdziarski/jamma: JAMMAエッジCAD、"educational use only" — [GitHub](https://github.com/jzdziarski/jamma/)
- Console JAMMAizer(arthrimus)はOSHPark公開との情報と "Not open source" との情報が矛盾 — [RetroRGB](https://retrorgb.com/console-jammaizer-by-arthrimus.html)
- pi2jamma: 商用、設計情報のみ — [falz.net](https://falz.net/wiki/Pi2jamma_hardware_and_software_info)
- CoinOp Connect/Whirlwind(Marco Guidolin): Gerber+ファームがGitHub公開、ライセンス未確認 — [Hackster](https://hackster.io/news/marco-guidolin-s-coinop-connect-connects-pcs-to-classic-non-jamma-arcade-cabs-with-no-damage-06493b9b4fee)

### Gaps
- 各リポジトリの回路図詳細(RGBバッファ値・コイン駆動)は本調査では精読しておらず、設計前に原図確認が必要。
