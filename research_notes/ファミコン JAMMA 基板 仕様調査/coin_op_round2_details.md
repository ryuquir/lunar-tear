# コイン・スタート・時間制プレイの詳細(第2パス:ギャップ解消と再検証)

(調査日 2026-11-10。作業中・逐次更新。出典 URL は各行末。推論は「推論」と明記し出典事実と分離する。)

## 1. PlayChoice-10:時間切れ・追加コイン・コントローラマスク

### Takeaway
(作成中)

### Cited Findings
- MAME の配線(`playch10.cpp` の `playch10()` マシン構成): Z80 の出力ラッチ LS259 #1(7D)Q0=SDCS、Q1=/CNTRLMASK、Q2=/DISPMASK、Q3=/SOUNDMASK、Q4=/GAMERES → 2A03 の RESET 入力(反転)、Q5=/GAMESTOP → 2A03 の **HALT** 入力(反転)。LS259 #2(7E)Q0=NMI Enable、Q1=DOG DI、Q2=/PPURES、Q7=8UP、Q3-Q6=CSEL0-3 — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- /CNTRLMASK 有効時の MAME 実装:$4016 ストローブ立下り時にラッチした P1 の値から `m_input_latch[0] &= ~0x0c`(「mask out select and start」)。ビット割当は 0x01=A, 0x02=B, 0x04=Select(MAME 名 "Game Select"), 0x08=Start, 0x10-0x80=上下左右。**P1 の Select と Start の 2 ビットのみ**がマスクされ、A/B/十字キーと P2 は影響を受けない。加えてガンゲームでは $4017 のザッパー・トリガ(bit4)もマスクされる(`if (!m_cntrl_mask) ret |= m_trigger->read() << 4;`)。光センサ(bit3)はマスクされない — 同上
- P2 の Select/Start ビット(0x04/0x08)は MAME で `IPT_UNUSED` とされ「wired to 1p select button / wired to 1p start button」とコメント。つまり PC-10 の筐体には P2 用の Select/Start は存在しない — 同上
- /DISPMASK:MAME ではシングルモニタ版で /DISPMASK が立つたびにゲーム画面と BIOS 画面を切替、デュアルモニタ版では下画面(ゲーム)を黒で塗りつぶす(`bitmap.fill(0)`)。/SOUNDMASK はシステム全体ミュート。/PPURES は PPU リセット — 同上
- MAME は Z80 BIOS ROM 自体を実行しており、時間切れシーケンスは BIOS コードが決める(ドライバ側に時間切れロジックは無い)。シングルモニタ版 BIOS は I/O $10-$13 に 4 桁の残り時間表示(7 セグ、BCD)を書く(`time_w`) — 同上
- DIP(MAME 内「マニュアル準拠だが MAME の条件付き DIP の制約で使えない」とされる定義): SW2 bit6 "Coin Mode" Mode1/Mode2、SW2 "Timer speed" 60/30/20/15/10/6/5/4/3/2/1 units per second、1 unit every 4 seconds、Free Play(0x80)。SW1 bit6 Demo Sounds、bit7 Service — 同上
- 実際に使われる DIP 定義(MAME):"Play Time/Coin" 2:00〜4:50(10 秒刻み、Standard Time)、Prime Time 時 2:00〜4:00;"Bonus" = Standard Time / Prime Time for 2 Coins / Prime Time for 4 Coins;"Prime Time Bonus" 8%〜100% — 同上
- オペレーションマニュアル(PCH1-UP)の OCR では、工場出荷時設定に「STANDARD TIME (no bonus)」、表に「Seconds per Coin」「Play Time/Coin」、例として「Regular Time 1 COIN = 300 (3 min.)」「PRIME TIME 4 COINS = 1200 (12 min.)」(OCR 誤読あり)。※「300」は 300 unit であり、表記上「3 min.」となっているが OCR 品質が低く、単位(秒 or unit)と分換算の整合は未確認 — [Internet Archive: PC10 Operation Manual PCH1-UP (OCR txt)](https://archive.org/download/pc10operationmanualpch1-up/PC10_Operation_Manual_-PCH1-UP_djvu.txt)
- 同マニュアル:自己診断・ブックキーピングには (a) アトラクト中またはゲーム中に Service スイッチと Enter ボタンを同時押し、(b) Service を押しながら電源投入(ブックキーピング RAM リセット可)、(c) SW1 トグル H を ON で電源投入、の 3 通り — 同上
- プレイヤー視点の挙動(デュアルモニタ版): 1 クォーターで既定 300 秒、いつでも追加クォーターで +300 秒。時間切れになるとゲームが止まり**下画面(ゲーム)が黒くなり、上画面が 20 秒間コイン投入を促す**。コインを入れるとゲームが「そのまま再開(springs back into action)」する — [Atari HQ: PlayChoice-10](https://atarihq.com/tsr/nes/pc10.html)
- シングルモニタ版:メニュー画面 → コイン投入で筐体上部の **4 桁 LED 表示**が残り時間をカウントダウン。ゲーム中に Enter ボタンで説明画面を表示(ゲーム映像を上書きするか 2A03 を停止させる「apparently」)、Enter 2 秒長押しでゲームに戻る — [Nerdly Pleasures: Nintendo's PlayChoice-10](https://nerdlypleasures.blogspot.com/2015/06/nintendos-playchoice-10-arcade.html)
- デュアルモニタ版では上画面がメニュー・説明・残り時間を表示 — 同上
- 「最短 2 分。プレイ前に追加コインを入れるとボーナス時間(Prime Time)。ボタンでゲーム選択メニューを呼び出して自由にゲームを切替でき、ポーズとリセットも可能」 — [Wikipedia: Nintendo Entertainment System models#PlayChoice-10](https://en.wikipedia.org/wiki/Nintendo_Entertainment_System_models#PlayChoice-10)(Cashbox 1986-08-30 p.41 を出典として引用)

### Inferences
- 推論:/GAMESTOP が 2A03 の HALT(MAME では CPU 実行停止。実機では RDY 系の停止と推定)に接続されていること、Atari HQ の「時間切れでゲームが止まり、コイン投入で再開」という記述、/DISPMASK による下画面ブランクを合わせると、PC-10 の時間切れシーケンスは「/GAMESTOP(CPU 停止)+ /DISPMASK(画面黒)+(おそらく)/SOUNDMASK → 20 秒間コイン待ち → 投入なしなら /GAMERES でリセットしてメニューへ」であり、**時間切れ直後はリセットせず“一時停止”して継続のチャンスを与える**設計と考えられる。実機 BIOS の書込順序そのものは一次資料未確認。
- 推論:/CNTRLMASK が Select/Start だけを落とすのは「時間外にゲーム開始・ポーズ解除をさせない」ためと解釈できる(第1パスの推論を維持)。十字キーと A/B は落とさないので、BIOS は /GAMESTOP(停止)と組み合わせて使ったと考えるのが自然。

### Gaps
- 時間切れ前の警告(音・表示)の有無:一次資料では未確認(Atari HQ・Nerdly Pleasures・MAME いずれにも記述なし)。
- /CNTRLMASK・/GAMESTOP・/DISPMASK・/SOUNDMASK の BIOS 内での書込順序:BIOS 逆アセンブルが必要で未確認。

## 2. FamicomBox / ファミコンステーション

### Takeaway
(作成中)

### Cited Findings
- 1コインあたり時間の出典別一覧:

| 出典 | 記載 | 根拠の性質 |
|---|---|---|
| [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox) | DIP 2: 0=10分 / 1=15分。コインタイマー TS1-0 %01=10分、%10=15分 | ハード解析(3199 の端子レベル) |
| [famicombox.jp(Kenvo、国内コレクター)aboutFB1](http://www.famicombox.jp/aboutFB1.html) | 「100円を入れると10/15分間」「一定の時間内(10分か15分)」 | 実機所有コレクターのスペック表 |
| [Wikipedia 日本語「ファミリーコンピュータ」ファミコンボックス節](https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%83%AA%E3%83%BC%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%BC%E3%82%BF) | 10分または15分(DIP)、制限時間 90 秒前にブザー、追加しないと「Time up.」で強制終了 | 二次(出典記載なし部分) |
| [ゲームマシン 1986年9月15日号 p.5(onitama.tv PDF)](https://onitama.tv/gamemachine/pdf/19860915p.pdf) | 「タイマー式にもできるわけだが、例えば十〜十五分間百円という設定が考えられる」 | 発売当時の業界紙(設定例) |
| [kevtris: Famicombox page 2](http://kevtris.org/mappers/famicombox/index1.html) / [page 7](http://kevtris.org/mappers/famicombox/index6.html) | DIP 2: off=10分, on=20分。時間切れ時の画面点滅・ビープは 1 分間 | 実機観察+出所不明の日本語 DIP 表画像 |
| kevtris 掲載の日本語 DIP 表画像「ディップスイッチの設定方法」 [famicombox_dips.jpg](http://kevtris.org/mappers/famicombox/images/famicombox_dips.jpg) | 「コインタイマー 10分 OFF / 20分 ON」 | 出所不明(公式資料の可能性) |
| [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp) | 10 or 20 minutes、DIP "10 min / 20 min"、`m_money_reg == 0x22 ? 20 : 10` | Kevin Horton の資料に依拠(ドライバ冒頭の謝辞) |
| [Weblio(旧版 Wikipedia 転載)](https://www.weblio.jp/content/%E3%83%95%E3%82%A1%E3%83%9F%E3%82%B3%E3%83%B3%E3%83%9C%E3%83%83%E3%82%AF%E3%82%B9) | 10分または20分、制限時間1分前にブザー | 二次 |

- 時間切れ時のプレイヤー体験(実機観察): 時間が尽きると画面全体が明・暗・明・暗と点滅し、本体が約 1 秒に 1 回ビープ。これが **1 分間**続き、その間にコインを入れればプレイ続行。入れなければ「TIME UP」画面に「SEE」「YOU」「NEXT」の文字が順に点滅表示され、タイトル(アトラクト)に戻る — [kevtris: Famicombox page 2](http://kevtris.org/mappers/famicombox/index1.html)、同趣旨 [kevtris: Famicombox page 1](http://kevtris.org/mappers/famicombox/)
- 点滅の手段は RF モジュレータの「40%」入力(Low で映像を 40% アンダーモジュレート)。コインメックの LED もビープと同期して点滅。ビープ(money feep)は DIP 9 ON でミュート。コイン投入時にもビープが鳴る — [kevtris: Famicombox page 7](http://kevtris.org/mappers/famicombox/index6.html);NESdev は「40% と呼ばれるが実測では約 45% に減光」、ビープ 874 Hz — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- 警告のタイミングの食い違い:kevtris は「時間が尽きてから 1 分間」点滅・ビープ(=猶予)、ja Wikipedia は「制限時間 90 秒前」にブザー、Weblio(旧版)は「1 分前」。NESdev は /NE(残り少)・/NEF(点滅制御)が「時間切れまたはコイン追加まで」交互に変化すると記述 — 各上記 URL。いずれが正しいかは 3199A の ROM が未解析のため未確認。
- リセットボタンでクレジットが残っている限りいつでも別ゲームを選び直せる(ペナルティなし) — [kevtris page 1](http://kevtris.org/mappers/famicombox/)、[kevtris page 2](http://kevtris.org/mappers/famicombox/index1.html);ja Wikipedia も「制限時間内であればリセットボタンを押すことで他のゲームに切り替えることもできる」
- 例外(exception)が発生すると CPU がリセットされ、メニューコードが $5000R を読んで原因(タイマー、キースイッチ、コイン、リセットボタン、ウォッチドッグ)を判別する — [kevtris page 7](http://kevtris.org/mappers/famicombox/index6.html)
- $5005W bit6 = joypad enable(1=disable)、bit3 = 40% 入力イネーブル、bit7 = joypad swap — [kevtris page 7](http://kevtris.org/mappers/famicombox/index6.html);NESdev も「bit6 = Disable joypads 1 and 2」 — [NESdev Wiki](https://www.nesdev.org/wiki/FamicomBox)
- コインメック用 3 ピンコネクタ:pin1 = コインスイッチ(GND 短絡でクレジット加算、TEST ボタンと並列)、pin2 = GND、pin3 = LED — [kevtris page 7](http://kevtris.org/mappers/famicombox/index6.html)
- 発売:1986 年 10 月、交通公社トラベランド興業(のち JTB トラベランド)。専用カセット 10 本込み 11 万円、コインボックス式 12 万円(ゲームマシン 1986-09-15 を出典) — [ja Wikipedia](https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%83%AA%E3%83%BC%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%BC%E3%82%BF)。famicombox.jp は販促リーフレットに基づき「月々 2,350 円の 5 年リース」と記載 — [famicombox.jp aboutFB1](http://www.famicombox.jp/aboutFB1.html)
- ゲームマシン 1986-09-15 の記事(画像を目視で読み取り):利用料金は ①コインボックス方式、②専用キー貸し出し式、③CATV のオンライン方式の三種類。「ゲームソフトの著作権の関係から利用方法を限定するなど、TV ゲームの上映権を正面から実施するものとして注目される」 — [ゲームマシン 1986-09-15 p.5](https://onitama.tv/gamemachine/pdf/19860915p.pdf)
- ファミコンステーション:
  - famicombox.jp:シャープとのコラボ製品、灰色、**型番 AN-550**、コントローラにも SHARP ロゴ、説明書も別 — [famicombox.jp aboutFS](http://www.famicombox.jp/aboutFS.html)
  - NESdev:「Sharp FamicomStation (AN-560)」としても発売 — [NESdev Wiki](https://www.nesdev.org/wiki/FamicomBox)(型番が famicombox.jp と食い違う)
  - MAME:「より民生向け(コイン非対応)のユニット」 — [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp)
  - ja Wikipedia:「シャープ版の『ファミコンステーション』もあり、メニュー画面の任天堂ロゴが『SHARP』の文字に変更されているなどの違いがある」(コイン非対応とは書かない) — [ja Wikipedia](https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%83%AA%E3%83%BC%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%BC%E3%82%BF)

### Inferences
- 推論:「10/15 分」と「10/20 分」は、(a) 3199A のタイマー選択端子レベル解析(NESdev)と国内コレクター資料・発売時業界紙の例示が 10〜15 分、(b) 出所不明の日本語 DIP 表と kevtris/MAME が 10/20 分、という二系統に分かれる。MAME の 20 分は kevtris 由来であり独立の根拠ではない。DIP 表画像は日本語で公式資料風だが出所不明。決定的な一次資料(任天堂/JTB の取扱説明書の該当頁)は未入手のため**確定できない**。本プロジェクトの仕様決定には影響しない(どちらも「100円=10分台」)。
- 推論:FamicomBox の時間切れは「点滅+ビープによる猶予(1 分程度)→ TIME UP 画面 → CPU リセットでアトラクトへ」であり、ゲームの進行に関わらず強制終了する。PC-10(停止して 20 秒待つ)と同様、**時間切れ直後に即リセットせず猶予を設ける**のが任天堂の両先例に共通。

### Gaps
- ファミコンステーションがコインボックスを装着できたかは、MAME(非対応)と他資料(言及なし)で確定できず未確認。型番 AN-550/AN-560 も食い違い。
- 警告の開始時点(時間切れ後 1 分の猶予か、残り 90 秒/60 秒の予告か)は未確認。

(以下、3〜6 は作業中)
