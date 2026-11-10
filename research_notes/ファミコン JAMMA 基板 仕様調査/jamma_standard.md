# JAMMA 規格と JAMMA 基板の電気的・機械的要件

(途中保存版 1: ピン配置。以後トピックごとに追記)

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

(以降のセクション: 機械寸法 / 電源 / 映像 / 音声 / 入力・コイン / OSHW事例 は追記予定)
