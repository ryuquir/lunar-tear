# コイン・スタート・時間制プレイの詳細(第2パス:ギャップ解消と再検証)

(調査日 2026-11-10。出典 URL は各行末。自分の推論は「推論」と明記し、出典のある事実と分けて書く。確認できなかった事項は「未確認」と書く。)

**調査範囲の制約**:この調査の途中で WebSearch の利用上限(セッション内 200 回、他エージェントと共有)に達した。そのため、項目 4 の後半と項目 5・6 は、検索せずに直接取得できるページ(MAME ソース、NESdev、TASVideos、任天堂の公式説明書 PDF、Internet Archive、arcade-projects の既知スレッド、Wikipedia の raw 本文)だけで調べた。日本語のホビーブログ、X/Twitter、ヤフオク、YouTube は検索できなかったため、その部分は「未確認」とした。

---

## 1. PlayChoice-10:時間切れ・追加コイン・コントローラマスク

### Takeaway
PC-10 は時間切れ時にゲームをリセットしない。ゲームを止め、ゲーム画面を黒くし、20 秒間コインの追加を待つ。コインが入ればゲームはそのまま再開する(Atari HQ。MAME の配線とも矛盾しない)。/CNTRLMASK が無効にするのは **P1 の Select(0x04)と Start(0x08)の 2 ビットと、ザッパーのトリガ**だけである。十字キー、A/B、P2 には影響しない。

### Cited Findings
- **Z80 出力ラッチの配線(MAME)**
  - LS259 #1(7D): Q0=SDCS、Q1=/CNTRLMASK、Q2=/DISPMASK、Q3=/SOUNDMASK、Q4=/GAMERES、Q5=/GAMESTOP。
  - MAME では、**/GAMERES は 2A03 の RESET 入力に、/GAMESTOP は 2A03 の HALT 入力に**つながっている(どちらも反転)。
  - LS259 #2(7E): Q0=NMI Enable、Q1=DOG DI、Q2=/PPURES、Q3-Q6=CSEL0-3(カートリッジ選択)、Q7=8UP。
  - 出典: [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- **/CNTRLMASK のマスク対象(MAME)**
  - $4016 のストローブが立ち下がったときに P1 の値をラッチし、そこから `m_input_latch[0] &= ~0x0c;` で 2 ビットを消す。コメントは "mask out select and start"。
  - P1 のビット割当は 0x01=A、0x02=B、0x04=Select("Game Select")、0x08=Start、0x10/0x20/0x40/0x80=上/下/左/右。
  - ガンゲームでは $4017 bit4(トリガ)も `if (!m_cntrl_mask)` のときだけ返す。つまりトリガもマスクされる。光センサ bit3 はマスクされない。
  - 出典: [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- **P2 には Select/Start が無い**: MAME では P2 の 0x04/0x08 が `IPT_UNUSED` で、"wired to 1p select button" / "wired to 1p start button" と注記されている。筐体には P1 用の Game Select と Start しかない — 同上
- **映像と音声のマスク(MAME)**
  - /DISPMASK: シングルモニタ版では切り替わるたびにゲーム画面と BIOS 画面を入れ替える。デュアルモニタ版では下画面(ゲーム)を黒で塗りつぶす(`bitmap.fill(0)`)。
  - /SOUNDMASK: システム全体をミュートする。
  - /PPURES: PPU をリセットする。
  - 出典: 同上
- **時間切れの判断は BIOS が行う**: ドライバ側に時間切れの処理は無く、Z80 BIOS ROM が決める。シングルモニタ版 BIOS は I/O $10-$13 に 4 桁の BCD 残り時間を書き込み、7 セグ LED に表示する(`time_w`) — 同上
- **DIP スイッチ(MAME)**
  - "Play Time/Coin": Standard Time で 2:00〜4:50(10 秒刻み)、Prime Time で 2:00〜4:00。
  - "Bonus": Standard Time / Prime Time for 2 Coins / Prime Time for 4 Coins。"Prime Time Bonus": 8〜100%。
  - マニュアル準拠の定義(MAME の条件付き DIP では表現できないためコメントアウトされている): "Timer speed" 60〜1 units per second、1 unit every 4 seconds、Free Play。
  - Steph のコメント: DSWB bit7 ON で Free Play(9999 units)。
  - 出典: 同上
- **オペレーションマニュアル PCH1-UP(OCR)**
  - 工場出荷時設定は "STANDARD TIME (no bonus)"。表題に "Seconds per Coin" と "Play Time/Coin" がある。
  - 例として "Regular Time 1 COIN = 300 (3 min.)" と "PRIME TIME 4 COINS = 1200 (12 min.)" がある(OCR の誤読あり)。
  - 300 が 300 unit を指すことと「3 min.」という分換算の整合は、OCR の品質が低いため**未確認**。
  - 出典: [Internet Archive: PC10 Operation Manual PCH1-UP(OCR)](https://archive.org/download/pc10operationmanualpch1-up/PC10_Operation_Manual_-PCH1-UP_djvu.txt)
- **自己診断とブックキーピングへの入り方(同マニュアル)**: (a) アトラクト中またはゲーム中に Service スイッチと Enter ボタンを同時に押す、(b) Service を押しながら電源を入れる(ブックキーピング RAM をリセットできる)、(c) SW1 のトグル H を ON にして電源を入れる — 同上
- **VS. UniSystem 用 PC-10 キットの最終チェック項目**: "5. Coins give credit." と "8. LED PC Board indicate player time." がある。つまりキットにも残り時間を表示する LED 基板が付いている — [Internet Archive: PC10 Kit Manual for Installation in VS UniSystem(OCR)](https://archive.org/download/pc10_kit_manual_for_installation_in_vs_unisystem_ptm/PC10_Kit_Manual_for_Installation_in_VS_UniSystem_djvu.txt)
- **プレイヤーから見た挙動**
  - 既定では 1 クォーターで 300 秒。いつでもクォーターを足せば 300 秒延びる。
  - "If you run out of play time" のとき、下画面(ゲーム)が黒くなる。上画面が "gives you 20 seconds to insert a coin"。
  - "Put one in and the game springs back into action." つまり、コインを入れるとゲームはその場から再開する。
  - 出典: [Atari HQ: PlayChoice-10](https://atarihq.com/tsr/nes/pc10.html)
- **シングルモニタ版の挙動**
  - コインを入れると、筐体上部の 4 桁 LED が残り時間をカウントダウンする。
  - プレイ中に Enter を押すと説明画面が出る。原文は "This apparently overrides the video from the game or halts the 2A03E CPU's execution"。
  - Enter を 2 秒押し続けるとゲームに戻る。
  - デュアルモニタ版では、上画面にメニュー、説明、残り時間を表示する。
  - 出典: [Nerdly Pleasures: Nintendo's PlayChoice-10](https://nerdlypleasures.blogspot.com/2015/06/nintendos-playchoice-10-arcade.html)
- **最短時間と追加コイン**: 最短 2 分。プレイ前に追加のコインを入れると Prime Time のボーナスが付く。ボタンでゲーム選択メニューを呼び出して切り替えられ、ポーズとリセットもできる(Cashbox 1986-08-30 p.41 などを出典として引用) — [Wikipedia: Nintendo Entertainment System models#PlayChoice-10](https://en.wikipedia.org/wiki/Nintendo_Entertainment_System_models#PlayChoice-10)
- **後継機 NSS(1991)の同じ仕組み**: Z80 のポート 01h の bit1 が "Maybe SNES CPU pause? (cleared on deposit coin to continue)"、bit0 が CPU/PPU リセット、bit7 が "SNES Joypad Enable (0=Disable/Demo)"、bit5 が "SNES Sound Mute" である。MAME はこの bit1 を CPU の HALT につないでいる。つまり後継機も「CPU 停止+パッド無効+ミュートで、コインの追加を待つ」形をとる — [MAME nss.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/nss.cpp)

### Inferences
- 推論: 時間切れのシーケンスは「/GAMESTOP(CPU 停止)+ /DISPMASK(ゲーム画面を黒)+(おそらく)/SOUNDMASK → 20 秒待つ → コインが無ければ /GAMERES でリセットしてメニューへ」と考えられる。時間切れの瞬間にはリセットせず、続けて遊ぶ機会を与える設計である。根拠は、/GAMESTOP が HALT につながっていること、Atari HQ の「その場から再開」という記述、NSS の "pause (cleared on deposit coin to continue)" の 3 つ。BIOS がどの順でラッチに書き込むかは一次資料で**未確認**。
- 推論: /CNTRLMASK が Select と Start だけを消すのは、時間外にゲームを開始したりポーズを解除したりさせないためと考えられる。十字キーと A/B は消さないので、CPU 停止(/GAMESTOP)と組み合わせて使ったと考えるのが自然である。
- 推論: 2A03 にはピンとしての RDY が無い。そのため、PC-10 の /GAMESTOP が実機で何を操作していたか(クロック停止、DMA 系の線、その他)は**未確認**である。NMOS 6502 のレジスタはダイナミックなので、クロックを長く止めると内容が保てない可能性がある。これは一般的な知識で、本調査では一次資料を確認していない。

### Gaps
- 時間切れ前の警告(音・表示)の有無は**未確認**。Atari HQ、Nerdly Pleasures、MAME、マニュアルの OCR のどれにも記述が無い。
- BIOS がラッチに書き込む順序は**未確認**。BIOS の逆アセンブルが必要。
- 「タイマーが動いていても、説明画面を見ている間は減らない」かどうかは**未確認**。
- arcadecontrols のフォーラムにある「コインを入れた後に Enter をもう一度押す必要がある」という記述は検索結果の要約でしか見ておらず、本文は 503 で取得できなかった(**未確認**)。

---

## 2. FamicomBox / ファミコンステーション

### Takeaway
1 コインあたりの時間は、資料によって「10/15 分」と「10/20 分」の 2 系統に分かれる。MAME の「20 分」は kevtris の資料を引き写したもので、独立した根拠ではない。決定的な一次資料(任天堂または JTB の取扱説明書の該当ページ)は入手できず、**確定できなかった**。

時間切れになると、画面が明暗に点滅し、約 1 秒ごとにビープが鳴る。これが約 1 分続き、その間にコインを入れれば続けて遊べる。入れなければ「TIME UP」画面で "SEE" "YOU" "NEXT" と表示し、タイトルに戻る(kevtris の実機観察)。日本語版 Wikipedia は「制限時間 90 秒前にブザー」と書いており、警告が始まるタイミングは資料によって食い違う。

ファミコンステーションがコインで動いたかどうかは、MAME(非対応と記述)と他の資料(言及なし)で判断できず、**未確認**。型番も AN-550 と AN-560 で食い違う。

### Cited Findings
- 1 コインあたりの時間(出典別):

| 出典 | 記載内容 | 根拠の性質 |
|---|---|---|
| [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox) | DIP 2: 0=10分 / 1=15分。コインタイマー TS1-0 は %01=10分、%10=15分 | 3199 の端子レベルでのハード解析 |
| [famicombox.jp(国内コレクター Kenvo)](http://www.famicombox.jp/aboutFB1.html) | 「100円を入れると10/15分間」「一定の時間内(10分か15分)」 | 実機を所有するコレクターのスペック表 |
| [Wikipedia 日本語版「ファミリーコンピュータ」のファミコンボックス節](https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%83%AA%E3%83%BC%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%BC%E3%82%BF) | 10分または15分(DIP)。制限時間の 90 秒前にブザー。追加しなければ「Time up.」と出て強制終了 | 二次資料(この部分に出典の注記なし) |
| [ゲームマシン 1986年9月15日号 p.5(onitama.tv の PDF、画像を目視で読み取り)](https://onitama.tv/gamemachine/pdf/19860915p.pdf) | 「タイマー式にもできるわけだが、例えば十〜十五分間百円という設定が考えられる」 | 発売当時の業界紙(設定の例示) |
| [kevtris: Famicombox(運用)](http://kevtris.org/mappers/famicombox/index1.html) / [同(レジスタ)](http://kevtris.org/mappers/famicombox/index6.html) | DIP 2: off=10分、on=20分 | 実機観察と、出所不明の日本語 DIP 表 |
| [kevtris 掲載の日本語 DIP 表画像「ディップスイッチの設定方法」](http://kevtris.org/mappers/famicombox/images/famicombox_dips.jpg) | 「コインタイマー 10分 OFF / 20分 ON」。同じ表に、アトラクション画面 5/10 秒、ゲームデモ画面 5/10/15/20 秒、課金方式(フリープレイ/コイン/キー/CATV)もある | 出所不明(公式資料のように見える) |
| [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp) | "10 or 20 minutes"、`m_money_reg == 0x22 ? 20 : 10` | 冒頭の謝辞に "Thanks for Kevin Horton for hardware docs"(kevtris の資料に依拠) |
| [Weblio(旧版 Wikipedia の転載)](https://www.weblio.jp/content/%E3%83%95%E3%82%A1%E3%83%9F%E3%82%B3%E3%83%B3%E3%83%9C%E3%83%83%E3%82%AF%E3%82%B9) | 10分または20分。制限時間の 1 分前にブザー | 二次資料 |
| [オヨブログ(非売品ファミコン)](https://famikonchuuken.blog.jp/archives/27809290.html) | 「100円を入れると10〜20分遊べたそうです」 | 伝聞 |

- **客室用の説明書(kevtris が撮影したページ。画像を目視で読み取り)**
  - 「注意 1枚目の100円硬貨が入った時点でタイマーが動き出します。」
  - 「連続5枚まで投入できます。」
  - コントローラのセレクト(SELECT)ボタンで遊びたいゲームを選び、スタート(START)ボタンで始める。
  - 「ゲームをしている途中でそのゲームを最初からやりたいときはリセット(RESET)スイッチを押してもう一度スタート(START)ボタンを押してください。」
  - 出典: [famicombox_book2.jpg](http://kevtris.org/mappers/famicombox/images/famicombox_book2.jpg)
- **時間切れのときにプレイヤーが見るもの**
  - "Once your time runs out ... the entire screen starts to flash bright/dim/bright/dim, and the unit feeps about once a second. This continues for 1 minute, giving you time to put more money in if you wish to continue playing. If you don't, then this screen appears. The text line says "SEE" "YOU" "NEXT"... Then it switches back to the title screen."
  - 出典: [kevtris: Famicombox(運用)](http://kevtris.org/mappers/famicombox/index1.html)。同じ趣旨が [kevtris トップページ](http://kevtris.org/mappers/famicombox/) にもあり、そこには「a cute "TIME UP" graphic」とも書かれている。
- **点滅の仕組み**
  - RF モジュレータの "40%" 入力を使う。この入力が Low のとき映像を 40% アンダーモジュレートする。
  - コインメックの LED もビープと同期して点滅する。
  - DIP 9 を ON にすると money feep が鳴らない。コインを入れたときにもビープが鳴る。
  - 出典: [kevtris: Famicombox(レジスタ)](http://kevtris.org/mappers/famicombox/index6.html)
  - NESdev によれば、"40%" と呼ばれるが実測ではおよそ 45% まで暗くなる。ビープは 874 Hz — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- **警告の開始タイミングが資料で異なる**
  - kevtris: 時間が尽きた後、1 分間の猶予として点滅とビープが続く。
  - 日本語版 Wikipedia: 制限時間の 90 秒前。
  - Weblio(旧版): 制限時間の 1 分前。
  - NESdev: /NE は「残り時間が少ない」を示し、/NEF は「時間切れになるかコインが追加されるまで」交互に切り替わる。
  - 3199A の ROM は解析されておらず、どれが正しいかは**未確認**。
- **リセットと例外**
  - クレジットが残っていれば、リセットボタンで別のゲームを選び直せる。ペナルティは無い — [kevtris](http://kevtris.org/mappers/famicombox/)
  - 例外が起きると CPU がリセットされる。メニューのコードは $5000R を読んで原因(8 ビットタイマー、キースイッチ、コイン、リセットボタン、ウォッチドッグ)を判別する — [kevtris(レジスタ)](http://kevtris.org/mappers/famicombox/index6.html)
  - クレジット遷移の例外が起きるのは、「クレジットあり」と「クレジットなし」の間を行き来したときだけである("transitioning either way between having and not having credit") — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- **$5005W のビット**: bit6 は joypad enable(1=無効)、bit3 は 40% 入力のイネーブル、bit7 は joypad swap — [kevtris(レジスタ)](http://kevtris.org/mappers/famicombox/index6.html)、[NESdev](https://www.nesdev.org/wiki/FamicomBox)
- **コインメックのコネクタ(3 ピン)**: pin1 = コインスイッチ(GND に落とすとクレジット加算。TEST ボタンと並列)、pin2 = GND、pin3 = LED — [kevtris(レジスタ)](http://kevtris.org/mappers/famicombox/index6.html)
- **発売の経緯と価格**
  - 1986 年 10 月に交通公社トラベランド興業(のちの JTB トラベランド)から発売。専用カセット 10 本込みで 11 万円、コインボックス式は 12 万円 — [日本語版 Wikipedia](https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%83%AA%E3%83%BC%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%BC%E3%82%BF)(出典はゲームマシン 1986-09-15)
  - famicombox.jp は販促リーフレットに基づき「月々 2,350 円の 5 年リース」と書いている — [famicombox.jp](http://www.famicombox.jp/aboutFB1.html)
- **ゲームマシン 1986-09-15 の記事(画像を目視で読み取り)**
  - 利用料金の取り方は「①コインボックス方式、②専用キー貸し出し式、③CATV のオンライン方式の三種類」。
  - 「ゲームソフトの著作権の関係から利用方法を限定するなど、TV ゲームの上映権を正面から実施するものとして注目される」。
  - 出典: [ゲームマシン 1986-09-15 p.5](https://onitama.tv/gamemachine/pdf/19860915p.pdf)
- **ファミコンステーション(資料ごとの記述)**
  - famicombox.jp: シャープとのコラボ製品で色は灰。**型番 AN-550**。コントローラにも SHARP ロゴがあり、説明書も別 — [famicombox.jp aboutFS](http://www.famicombox.jp/aboutFS.html)
  - NESdev: "Sharp FamicomStation (AN-560)" — [NESdev Wiki](https://www.nesdev.org/wiki/FamicomBox)
  - MAME: "more of a consumer (non-coin accept) unit" — [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp)
  - 日本語版 Wikipedia: メニュー画面の任天堂ロゴが「SHARP」になっているなどの違いがある。コインに非対応とは書いていない — [日本語版 Wikipedia](https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%83%AA%E3%83%BC%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%BC%E3%82%BF)
- **後継機のスーパーファミコンボックス**
  - MAME: "accepted 100 yen coins and gave 5 minutes of playtime" — [MAME sfcbox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/sfcbox.cpp)
  - 国内ブログに引用されたツイートに「６分１００円のスーファミボックス(現役稼働)」とある。料金と時間はホテルが設定していた — [すけゲームブログ](https://sukegames.blog/commentary-sfcbox/)

### Inferences
- 推論: 系統 (a)「10〜15 分」は、NESdev の端子解析、国内コレクターの資料、発売当時の業界紙の例示が支えている。系統 (b)「10/20 分」は、kevtris の資料と出所不明の日本語 DIP 表、それを引き写した MAME と旧版 Wikipedia が支えている。DIP 表の画像は公式資料のように見えるため、(b) を退ける根拠も無い。どちらであっても「100 円で 10 分台」なので、本プロジェクトの仕様決定には影響しない。
- 推論: FamicomBox は時間切れ後に「点滅とビープによる猶予(約 1 分)→ TIME UP 画面 → CPU リセットでアトラクトへ」と進み、ゲームの進み具合に関係なく強制終了する。PC-10(停止して 20 秒待つ)と同じく、**時間切れの瞬間に即リセットせず猶予を置く**のが任天堂の 2 つの先例に共通する。

### Gaps
- ファミコンステーションがコインボックスを付けられたかどうかと、型番(AN-550 か AN-560 か)は**未確認**。
- 警告の開始タイミング(時間切れ後の 1 分間の猶予か、残り 90 秒または 60 秒での予告か)は**未確認**。

---

## 3. VS. System:コイン、サービス、スタートの入り方(2 つの資料による再検証)

### Takeaway
2 つの資料(MAME vsnes.cpp と NESdev Wiki)が一致した。コイン 1/2 は $4016 bit5/bit6、サービスは $4016 bit2、DIP は $4016 bit3-4 と $4017 bit2-7 に入る。スタートボタンはシフトレジスタの **3 番目のビット(家庭用で Select の位置)**に入り、DualSystem のスタート 3/4 は 4 番目のビット(Start の位置)に入る。VS. のマニュアルの配線表でも、スタートボタンは「S SELECT 1〜4」「M SELECT 1〜4」と呼ばれている。

### Cited Findings
- **MAME `vsnes_in0_r`**: シリアルデータを bit0 に置き、`m_coins` で bit2(サービス)、bit5、bit6(コイン)を OR し、`(dsw & 3) << 3` で DIP を bit3-4 に、`Side << 7` で CPU 番号を bit7 に入れる。`vsnes_in1_r` は bit0 がシリアル、bit2-7 が DIP。コメントは "bit 1: always 0 (from floating input on 74LS240)"。
- **MAME のコイン入力**: `PORT_IMPULSE(3)`。コメントは "1 frame is too short for some games (T.K.O. Boxing) ... actual coin drop time varies between 2.5 to 4 frames"。
- **MAME の UniSystem ジョイスティック定義**: 0x01=A、0x02=B、0x04=START1/2("Select 1 (Blue)" / "Select 2 (Green)")、**0x08=IPT_UNUSED**、0x10-0x80=上下左右。DualSystem では 0x08 が START3/4("Select 3 (Purple)" / "Select 4 (Yellow)")。
  - 以上 3 項目の出典: [MAME vsnes.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp)
- **NESdev による同じ内容**
  - $4016 read: bit0 = "Buttons for right stick (A, B, 1, 3, Up, Down, Left, Right)"、bit2 = サービス、bit3-4 = DIP "2"・"1"、bit5-6 = コイン、bit7 = 主/副 CPU。
  - $4017 read: bit0 = "left stick (A, B, 2, 4, ...)"、bit2-7 = DIP "8"〜"3"。bit1 は常に 0。
  - コイン信号は "approximately 40 to 70ms" の間 true になる。"games MUST check both bits"。
  - $4020 に 1、続けて 0 を書くとカウンタが進む。$4017 を 1.2 秒以内ごとに読まないとウォッチドッグがリセットをかける。
  - 出典: [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- **任天堂のマニュアル(VS. System Upright, MDS-UP-US)の配線表**: スタートボタン線に "S SELECT 1"〜"S SELECT 4" と "M SELECT 1"〜"M SELECT 4"(S=Slave、M=Master と読める)と書かれている — [Internet Archive: VS. System Upright Operation Manual(OCR)](https://archive.org/download/vssystemuprightoperationmanualmds-up-us/VS_System_Upright_Operation_Manual_-MDS-UP-US_djvu.txt)
- **パッド位置の左右**: 左スティックは $4017、右スティックは $4016 に入り、家庭用機とは逆になる。どちらを P1 とするかはゲームによる — [MAME](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp)、[NESdev](https://www.nesdev.org/wiki/Vs._System)
- **家庭用のコントローラポート(比較用)**: 報告順は A, B, Select, Start, Up, Down, Left, Right。8 回読んだ後は 1 を返す。ファミコンでは $4016 bit1 が拡張ポート、bit2 が IIコンのマイク。上位ビットはドライブされず、直前のバス値が残る("Paperboy" はこれに依存している) — [NESdev Wiki: Standard controller](https://www.nesdev.org/wiki/Standard_controller)

### 標準のファミコンソフトを VS. ハードで動かしたときに起きる違い

| 項目 | VS. System | ファミコン(HVC-001) | 標準ソフトへの影響 |
|---|---|---|---|
| スタート | シフトの 3 番目(Select の位置) | 4 番目(Start) | UniSystem では Start 位置の入力が無い(IPT_UNUSED)ため、ゲームを開始できず、ポーズもできない |
| P1 の位置 | 多くは左スティック = $4017 | P1 = $4016 | 左側の操作パネルでは操作できない(P2 扱いになる) |
| $4016 の上位ビット | bit2 サービス、bit3-4 DIP、bit5-6 コイン、bit7 CPU 番号 | bit2 マイク、上位は open bus | 全ビットを比較するソフトは誤作動する。`and #3` でマスクするソフトは問題ない |
| $4017 の上位ビット | bit2-7 が DIP | bit1-4 は拡張ポート(bit3/4 はザッパー) | DIP の値がザッパー入力として見える |
| bit1 | 常に 0 | 拡張コントローラ(多くのソフトが D0 と OR する) | 影響なし |
| ウォッチドッグ | 副 CPU 側では 1.2 秒以内に $4017 を読む必要がある | なし | 読まない区間が長いソフトはリセットされる |
| パレットと PPU | 2C03/2C04/2C05 の RGB PPU | 2C02 | 2C04 では色化け、2C05 では $2000 と $2001 が入れ替わる(第 1 パスで既出) |
| ネームテーブル | 常に 4 画面 | カートリッジがミラーリングを決める | ミラーリングを前提にした描画が崩れる |

(表は上の出典から整理したもの。「影響」の列は推論を含む。)

### Inferences
- 推論: VS. の慣習では「スタート = Select のビット位置、コイン = 上位ビット」である。本プロジェクトの「コイン = SELECT、スタート = 十字キー 4 方向同時押し」は、VS. とは異なる独自の方式になる。専用ゲームを作る側から見れば、どちらの方式でもソフトでデコードできる。一方、市販カートリッジを無改造で動かす場合は、VS. 方式でも本プロジェクトの方式でもスタートが「Start ビット」として届かない。このため時間制モードでは、Start と Select をそのまま渡すマッピングが必要になる(§4)。

### Gaps
- VS. の回路図での実際の配線(74LS240 のどの入力にスタートが入るか)は回路図を入手できず、MAME と NESdev の 2 つの記述が一致したことで代用した。

---

## 4. 本プロジェクトが合成する入力に対する市販ソフトの反応

### Takeaway
- **上下・左右の同時押し**: ゲームプレイ中に送ると、実際にグリッチを起こすソフトが多数記録されている(例: Battletoads の 2 面で上+下を押すと続行不能)。タイトル画面だけで送る分には大きな害の報告は見当たらない。
- **SELECT と START の一般的な使い方**: タイトル画面では SELECT でカーソルを動かし、START で開始する。プレイ中は START でポーズし、SELECT は「はたらきません」。これは任天堂の説明書に明記されている。
- **IIコン**: Select/Start ボタンが無いので、ファミコン用ソフトは IIコンの Select/Start を頼りにしてはならない(NESdev)。
- **マイク**: 『ゼルダの伝説』『たけしの挑戦状』『バンゲリング ベイ』など、少数のソフトが使う。
- **結論(推論)**: DIP で「十字キー 4 方向同時押しのスタート」と「そのまま START/SELECT を渡す」を選べるようにすることが必須になる。

### Cited Findings
- **上下・左右の同時押しで起きる現象(TASVideos のゲームリソースページ)**

| ゲーム | 入力 | 起きること |
|---|---|---|
| Battletoads | 左+右 / 上+下 | 2 面で上+下を押すと "the toad disappears and loses functionality, so its impossible to continue"。4・6・8・9・12 面ではスプライトが浮く |
| Super Mario Bros. | 左+右 | 1 フレーム押すと "you'll start walking backwards to the right"。速度が急に落ちる |
| Super Mario Bros. 2 | 上+下(はしご)、上下左右(つる) | はしごで上+下を押すと "shot upwards at super high speed" |
| Rockman / Mega Man | 上+下(はしごの上端) | 壁抜けなどのショートカット |
| Teenage Mutant Ninja Turtles | 上+下+左/右+攻撃 | "glitches the game"。武器が画面に浮いて残る |
| Double Dragon II | 左+右 | 飛び膝蹴りが真上になる。ステージ 6 でテレポート |
| Rygar | 左+右、上+下+右、左+右+下 | 空中で何度でもジャンプできる。異常な上昇 |
| Battle of Olympus | 上+下(階段)、左+右 | 存在しない階段を上る。速度がラップアラウンドする |
| Super Contra 7 | 左+右 | アニメーションが止まり続ける |
| Q-Boy | 左+右+A | 後ろ向きにジャンプする |

  出典: [Battletoads](https://tasvideos.org/GameResources/NES/Battletoads)、[SuperMarioBros](https://tasvideos.org/GameResources/NES/SuperMarioBros)、[SuperMarioBros2](https://tasvideos.org/GameResources/NES/SuperMarioBros2)、[Rockman](https://tasvideos.org/GameResources/NES/Rockman)、[TeenageMutantNinjaTurtles](https://tasvideos.org/GameResources/NES/TeenageMutantNinjaTurtles)、[DoubleDragon2](https://tasvideos.org/GameResources/NES/DoubleDragon2)、[Rygar](https://tasvideos.org/GameResources/NES/Rygar)、[BattleOfOlympus](https://tasvideos.org/GameResources/NES/BattleOfOlympus)、[SuperContra7](https://tasvideos.org/GameResources/NES/SuperContra7)、[QBoy](https://tasvideos.org/GameResources/NES/QBoy)。TASVideos の NES リソースページ 74 件を "left+right / up+down / L+R / U+D" などで機械的に検索し、該当したのは上の 10 タイトルだった。
- **NESdev の見解**: "Opposing directions (Up+Down and Left+Right) are possible on non-standard controllers, or even on a worn out standard one." 推奨コードは、同時押しを検出したら前のフレームの方向で置き換える — [NESdev Wiki: Controller reading code](https://www.nesdev.org/wiki/Controller_reading_code)
- **SELECT と START の公式な挙動(スーパーマリオブラザーズの取扱説明書。画像を目視で読み取り)**
  - SELECT ボタン: 「タイトル画面で、このボタンを押すと(キノコ)印が移動します。希望するゲームに合わせてください。※ゲームがスタートすると、SELECTボタンははたらきません。」
  - START ボタン: 「このボタンを押すと、SELECTボタンでセットしたゲームが始まります。」
  - ポーズ機能: 「ゲームの途中で、プレイを一時中断したい時にSTARTボタンを押すと、ポーズ音が鳴ってゲームがストップします。次に再スタートしたい時にも押してください。」
  - 出典: [任天堂 ニンテンドークラシックミニ ファミコン 説明書 CLV-P-HAAAJ(スーパーマリオブラザーズ)](https://www.nintendo.co.jp/clv/manuals/ja/pdf/CLV-P-HAAAJ.pdf)
- **ゼルダの伝説(ディスク)のメニュー**: 「SELECTボタンでハートを『ナマエトウロク』に合わせ、STARTボタンを押そう」 — [任天堂 CLV-P-HAANJ](https://www.nintendo.co.jp/clv/manuals/ja/pdf/CLV-P-HAANJ.pdf)
- **FamicomBox のメニュー操作も同じ方式**: SELECT でゲームを選び、START で開始する — [kevtris 掲載の客室用説明書](http://kevtris.org/mappers/famicombox/images/famicombox_book2.jpg)
- **IIコン**: "The hard-wired second controller (II) lacks Select and Start."、"Famicom games must not rely on the second player being able to push Start or Select." マイクは $4016 bit2 で、"Games often track changes in that bit" — [NESdev Wiki: Standard controller](https://www.nesdev.org/wiki/Standard_controller)
- **マイクを使うソフト**: 『バンゲリング ベイ』『スターラスター』『たけしの挑戦状』『ゼルダの伝説』『ドラえもん(ハドソン版)』『スターソルジャー』、ファミリーベーシック V3 のサンプル『ハート』など。「本体の製造時期によってオン / オフの判別が逆にされたため、ゲームに有効なかたちでこの機能を利用するのは困難だった」 — [日本語版 Wikipedia「ファミリーコンピュータ」](https://ja.wikipedia.org/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%83%AA%E3%83%BC%E3%82%B3%E3%83%B3%E3%83%94%E3%83%A5%E3%83%BC%E3%82%BF)
- **NES の 2P では Select/Start が使える**: PC-10 の筐体には P2 の Select/Start が無く、P1 の線につながっている — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- **NES2JAMMA のフォーラムでの質問(2025)**: "some games need to use Select , how you do that please" と質問されたが、回答は無い — [arcade-projects NES2JAMMA](https://www.arcade-projects.com/threads/nes2jamma.2779/)。この質問は、JAMMA の操作系に SELECT が無いことが実際の運用で問題になることを示している。

### Inferences(DIP スイッチで選べるようにすべき項目)
- 推論:**市販カートリッジには、十字キー 4 方向同時押しを START として送ってはいけない**。理由は次の 2 つ。
  - そのソフトは同時押しを Start とみなさないので、そもそもゲームを開始できない。
  - プレイ中に JAMMA の START を押すと上下・左右の同時押しになり、上の表のようなグリッチを起こす(Battletoads では続行不能)。
- 推論:時間制モード(市販カートリッジ向け)では、少なくとも次の割り当てが必要になる。
  1. JAMMA 1P START → コントローラ I の START(ポーズにも使われる)。
  2. SELECT の入力源を用意する。候補は JAMMA の 1P ボタン 3、2P START、または「1P START 長押し」。
  3. 2P の START は、IIコンに Start が無いので、市販ソフトには送っても意味が無い。2P START を I コンの SELECT に割り当てる DIP を用意すると便利である。
  4. マイク(IIコンの $4016 D2)の入力源として、JAMMA の 2P ボタン 3 などを割り当てる DIP を付ける(『たけしの挑戦状』『ゼルダの伝説』対策)。極性は製造時期で逆になるという記述があるので、マイク入力は「変化」で駆動する(押下中に 0/1 を交互に出すか、ON/OFF のパルスにする)のが安全である。
  5. コインをゲームに見せない(時間を足すだけにする)。
- 推論:専用ゲーム向けのクレジットモードでは、コインを SELECT にするか START にするかを DIP で選べるようにし、スタートは十字キー 4 方向同時押しにする。専用ソフトは上下・左右の同時押しを Start として扱うよう作れば問題ない。ただし、専用ソフト側でも NESdev の推奨(同時押しの除去)とは逆の扱いになる点を設計資料に明記する。

### Gaps
- 上下・左右の同時押しでクラッシュする市販ソフトの網羅的なリストは見つからなかった。TASVideos の上の 10 タイトルは「TAS で利用されるグリッチ」の記録であり、網羅的ではない。
- IIコンの Select/Start ビットを読むファミコンソフトの具体名は**未確認**。NESdev の指針からは「存在しても稀」と推定される。
- 日本語版 Wikipedia の「AV 仕様ファミコンでは 2P の下+A またはセレクトでマイクを代用できる」という記述が、どのソフトのどの仕組みを指すのかは**未確認**。

---

## 5. ファミコン/NES を JAMMA 筐体に入れた例と市販製品

### Takeaway
確認できた自作例と製品は、どれもコインを扱わない(フリープレイ)か、Select を別の手段で補っている。家庭用機を JAMMA に変換する製品にコイン処理は無い。一方、汎用のコインタイマー基板は、機器の電源をリレーで入り切りして時間を制限する。

### Cited Findings
- **NES2JAMMA(YavuzG、2016 年 12 月の回路図 Rev1.0、2017 年に arcade-projects で公開)**
  - 映像: "TLS1233 and LM1881"。RGB は、フランス版 NES(SCART。コンポジットを RGB に分解したもの)、または PC10 PPU や NESRGB で改造した NES から取る。
  - 音声: "a basic LM384"。
  - 操作: "CD4021 shift registers as arcade controls encoder"。
  - 回路図(画像を目視で読み取り)では、2 個の CD4021 の入力 A〜H が JAMMA の 17〜24 番(各面)に、1k のプルアップ付きでつながっている。**16 番(コイン)は未接続**である。
  - 出典: [arcade-projects NES2JAMMA](https://www.arcade-projects.com/threads/nes2jamma.2779/)、[回路図 NES-TO-JAMMA.png](https://www.arcade-projects.com/attachments/nes-to-jamma-png.3448/)
  - 推論: 17〜24 番は START、上下左右、ボタン 1〜3 の 8 本なので、Select はボタン 3 に割り当てたか、使っていない可能性が高い。2025 年に Select の質問が付いたまま回答が無い。
- **Console JAMMAizer(Arthrimus)**
  - THS7375 と LM386 を使い、RGB の出力インピーダンスは約 475 Ω(既存ノート `jamma_open_hardware_circuits.md` §11)。
  - Select はボタンの組み合わせで代用する: "Select = B1+B2+Start"、"Home = B2+B3+Start"。"When the select or home combo is detected, the start button press will not be sent."
  - 補助ハーネス(JST NH)に Select、Home、B7、B8 がある。マニュアルに "coin" という語は無い。
  - 出典: [Console JAMMAizer User Manual v1.0](https://raw.githubusercontent.com/Arthrimus/Console-JAMMAizer/master/Console%20JAMMAizer%20User%20Manual%20Version%201.0.pdf)
- **汎用コインタイマー基板 JY-184(販売店の説明)**
  - 「Pause function: temporarily cuts power and resumes without resetting time」
  - 「Adjustable warning sound between 1 and 59 seconds」
  - 時間、1 コインの金額、起動モード、警告音、停電後のメモリーを設定できる。コインセレクタ、紙幣、カード、押しボタンに対応する。
  - 出典: [Arcade Express JY-184](https://www.arcadexpress.com/en/accessories/789-jy-184-timer-controller-board-with-led-display-for-coin-mechanism.html)
  - 時間や金額の具体的な設定範囲と、出力の形式(リレーか)は、このページからは読み取れなかった(**未確認**)。
- **コイン式 Xbox(リレーで電源を切る方式への批判)** — 第 1 パスで既出 [adambyers.com](https://adambyers.com/posts/Coin-Operated-Xbox/)。本文は動的に読み込まれ、今回は再取得できなかった。
- **PC-10 の PPU を NES に移す RGB 化**: [RetroRGB](https://www.retrorgb.com/?p=1439)(ページの存在のみ確認)。NES2JAMMA もこの方式に触れている。

### Inferences
- 推論: ファミコンを JAMMA 化した先例には、「コインで時間を売る」仕組みを電源の遮断以外で実装したものが無い。PC-10 や FamicomBox のように CPU の停止やリセット、入力・映像・音声のマスクを基板内で行う設計は、自作の世界では本プロジェクトが新しい部類になる(検索できた範囲での判断)。

### Gaps
- 日本語の自作例(ブログ、X/Twitter、ヤフオク、YouTube)と、国内で市販されているコインタイマー(ホテル用のテレビコインタイマーなど)の設定範囲は、**WebSearch の上限に達したため調べられず未確認**。

---

## 6. 時間制コイン機器の慣行

### Cited Findings
| 機器 | 1 コインあたりの時間 | 残り時間の表示 | 時間切れの扱い | 追加コイン | フリープレイ |
|---|---|---|---|---|---|
| PlayChoice-10 | 既定 300 秒/25¢(DIP で 2:00〜4:50)。複数枚を一度に入れるとボーナス | 上画面、または 4 桁 LED | ゲームを止めて画面を黒くし、20 秒コインを待つ | いつでも +300 秒 | DIP(9999 units) |
| FamicomBox | 100 円で 10 分、または 15 分(異説 20 分) | コインメックの LED(残りが少ないと点滅) | 点滅とビープの猶予(約 1 分、異説あり)→ TIME UP → アトラクト | 連続 5 枚まで投入でき、延長される | DIP 7・8 |
| スーパーファミコンボックス | 100 円で 5 分(MAME)。6 分 100 円の稼働例あり | — | — | — | — |
| NSS | — | — | SNES の CPU を一時停止し、コインで再開(推定) | — | — |
| JY-184(汎用) | 設定による | 基板の LED | 警告音(1〜59 秒)→ 電源を切る | 中断せずに延長(第 1 パス) | — |

出典: PC-10 は [MAME](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp) と [Atari HQ](https://atarihq.com/tsr/nes/pc10.html)。FamicomBox は §2 の各出典と [客室用説明書](http://kevtris.org/mappers/famicombox/images/famicombox_book2.jpg)。スーパーファミコンボックスは [MAME sfcbox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/sfcbox.cpp) と [すけゲームブログ](https://sukegames.blog/commentary-sfcbox/)。NSS は [MAME nss.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/nss.cpp)。JY-184 は [Arcade Express](https://www.arcadexpress.com/en/accessories/789-jy-184-timer-controller-board-with-led-display-for-coin-mechanism.html)。

- **キディライド**: 「投貨やカード操作により…数分間の遊びを提供する」 — [日本語版 Wikipedia「キディライド」](https://ja.wikipedia.org/wiki/%E3%82%AD%E3%83%87%E3%82%A3%E3%83%A9%E3%82%A4%E3%83%89)
- **JAMMA の慣行**: Service ボタンはクレジットを +1 するがカウンタは進めない — [Arcade Otaku Wiki](https://wiki.arcadeotaku.com/w/JAMMA)(既存ノート `jamma_standard.md` 経由)
- **カウンタのパルス**
  - VS. System: 50 ms High / 50 ms Low — [NESdev](https://www.nesdev.org/wiki/Vs._System)
  - ライン精機 MZ: 25 ms(1:1)、20 Hz。Kessler-Ellis: ON 120 ms / OFF 80 ms。日本の筐体は +5 V のカウンタが主流。
  - これらは既存ノート `jamma_electrical_details.md` §6 による。
- **コイン信号の長さ**: 電子セレクタは 50 ± 5 ms または 72 ± 3 ms(旭精工)。VS. のコイン信号は 40〜70 ms — `jamma_electrical_details.md` §6、[NESdev](https://www.nesdev.org/wiki/Vs._System)

### Gaps
- インターネットカフェ、カラオケ、コンソールの試遊台などの時間課金の慣行(残り時間の通知方法、延長の扱い)は、検索の上限に達したため**未確認**。

---

## 7. 推奨する動作仕様(すべて推論)

前提: コイン、スタート、DIP は Pico がデバウンスした後の論理値として扱う。「ラッチ」とは、2A03 の OUT0(ストローブ)の立ち下がりを Pico が数えたものを指す。

### 7.1 共通のタイミング
- **ゲームに見せるボタンの押下**
  - 長さは「ラッチ 4 回以上、かつ 67 ms 以上」。VS. の 2.5〜4 フレーム(40〜70 ms)に合わせ、MAME が採用した 3 フレームに 1 フレームの余裕を足した。
  - 押下の後は「ラッチ 4 回以上、かつ 67 ms 以上」離した状態を保ってから次の押下を出す。
  - ラッチの回数と時間の両方を条件にする理由: 1 フレームに 1 回だけ読むソフトにも、ラグで読み飛ばしが出るソフトにも、確実にエッジを見せるため。ラッチが 0.5 秒以上来ない(読んでいない)場合は、時間の条件だけで解除する。
- **連続したコイン**: 未処理分をキューに入れる(上限 15 回)。カウンタのパルスは別系統にし、ON 100 ms / OFF 100 ms 以上とする(`jamma_electrical_details.md` §6 の推論と同じ)。

### 7.2 モード A: クレジットモード(専用ゲーム向け)
- コイン 1、コイン 2、Service → I コンの SELECT にパルスを出す(DIP で START にもできる)。カウンタはコイン 1/2 だけ進め、Service では進めない。
- 1P START → I コンの上下左右を同時押しにする。2P START → IIコンの上下左右を同時押しにする。押している間はずっと出し続け、最短はラッチ 4 回とする。
- 専用ソフトに DIP を見せたい場合は、$4017 D3/D4(ザッパーの線。通常のソフトは読まない)などに Pico から出す。D1 は使わない。多くのソフトが D1 を D0 と OR するからである。

### 7.3 モード B: 時間制モード(市販カートリッジ向け)
- **入力の対応**: JAMMA の各入力を、市販ソフトがそのまま理解できる割り当てで渡す。

| JAMMA | ファミコン |
|---|---|
| 1P START | I コンの START |
| 1P ボタン 1 / 2 | I コンの B / A |
| 1P ボタン 3 | I コンの SELECT |
| 2P START | I コンの SELECT(DIP で選択) |
| 2P ボタン 3 | IIコンのマイク(DIP で選択。押している間は約 10 Hz で 0/1 を切り替える) |

- **待機中**
  - 2A03 /RES と 2C02 /RST を保持する。
  - Pico が自分で「INSERT COIN」と設定時間を描く(Pico は映像経路にいるので重ね描きできる。映像の構成に依存する)。
- **コインを入れたとき**
  - 残り時間に「1 コインの時間」を加える。上限は 99 分 59 秒。
  - 1 枚目でリセットを解除し、タイマーを動かし始める(FamicomBox と同じ)。
  - コインはゲームに見せない。
- **プレイ中**
  - 残り時間を画面の隅に重ねて表示する(DIP で OFF にできる)。PC-10 と同じく 4 桁の 7 セグを外付けにする案もある。
- **警告(DIP で 30 秒または 60 秒)**: 約 1 Hz で 874 Hz のビープを鳴らす(FamicomBox と同じ)。DIP で消せるようにする。合わせて、残り時間の表示を点滅させる。
- **時間切れの後**
  - 猶予を置く(DIP で 20 秒または 60 秒。PC-10 と FamicomBox に合わせた)。
  - 猶予中は、両方のパッドの全ビットを 0 にし、映像をおよそ 45% まで暗くし、ゲームの音を消し、「CONTINUE? 残り xx 秒」を重ねて表示する。
  - CPU のクロックは止めない(NMOS のダイナミック回路が状態を保てない懸念があり、未確認のため)。ゲームは裏で動き続ける。
  - 猶予中にコインが入れば、マスクを解いて続行する。
- **最終的な終了**
  - 2A03 /RES と 2C02 /RST を同時に Low にして保持する。
  - Pico が「TIME UP / SEE YOU NEXT」を約 5 秒表示し、待機画面に戻る。
  - 電源は切らない(バッテリーバックアップ SRAM の破損を避けるため)。
- **ゲームのやり直し**: 1P START を 3 秒押し続けるとリセットする(FamicomBox のリセットボタンに相当)。クレジットが残っていても時間は減らさない。
- **Service ボタン**: 1 コイン分の時間を加え、カウンタは進めない。
- **フリープレイ(DIP)**: タイマーを止め、リセットを常に解除しておく。

### 7.4 推奨する DIP スイッチ(8 極)

| SW | 機能 | OFF | ON |
|---|---|---|---|
| 1 | モード | A: クレジット | B: 時間制 |
| 2 | (A)コインの出力先 | SELECT | START |
| 3 | スタートの出力形式 | 上下左右の同時押し | そのまま START(B では常にこちら) |
| 4・5 | (B)1 コインあたりの時間 | 00=3 分 / 10=5 分 | 01=10 分 / 11=15 分 |
| 6 | (B)警告と猶予 | 警告 30 秒・猶予 20 秒 | 警告 60 秒・猶予 60 秒 |
| 7 | 2P START とボタン 3 の役割 | 2P 用(上下左右の同時押し、またはなし) | I コンの SELECT とマイク |
| 8 | フリープレイ | OFF | ON |

ビープの ON/OFF と、残り時間の重ね描きの ON/OFF は、余った極か、Pico の TEST メニューに置く。

---

## 既存ノートへの訂正

1. **PC-10 の時間切れ時の挙動(第 1 パスの Q2 と Q5 の推論)**
   - 第 1 パスは「時間切れでコントローラの Select/Start をマスクし、BIOS がリセットしてメニューへ戻す」と推論していた。
   - 実際は、まずゲームを停止して下画面を黒くし、20 秒間コインの追加を待つ。コインが入ればその場から再開する([Atari HQ](https://atarihq.com/tsr/nes/pc10.html))。MAME でも /GAMESTOP は CPU の HALT につながっている。
   - リセットは猶予の後に行われると考えられる(推論)。
2. **PC-10 の /CNTRLMASK**: 第 1 パスの「P1 の 0x0c(Select と Start)だけをマスクする」は正しい。ただし、**ザッパーのトリガ($4017 bit4)もマスクする**ことが抜けていた。P2 にはもともと Select/Start が無い(P1 の線につながっている)。
3. **FamicomBox の「10/20 分」の根拠**: 第 1 パスは MAME を NESdev と並ぶ独立した資料として扱っていた。実際には、MAME の値は Kevin Horton(kevtris)の資料に由来する(ドライバの謝辞)。独立した資料は「NESdev、famicombox.jp、ゲームマシン 1986 = 10〜15 分」と「kevtris が掲載した出所不明の日本語 DIP 表 = 10/20 分」の 2 つである。
4. **FamicomBox の要約の表現**: 第 1 パスの Takeaway は「クレジット増減時に例外を起こしてシステムをリセットしメニューへ戻す」と書いていた。NESdev によれば、例外が起きるのは「クレジットあり/なしの間を行き来したとき」だけである。クレジットが残っているときに追加のコインを入れても、リセットは起きない(延長されるだけ)。時間切れのときは、点滅とビープの猶予と TIME UP 画面を経てからタイトルに戻る(kevtris)。
5. **第 1 パスの Q3 の Gap「日本語の一次資料は未取得」**: 今回、客室用の説明書のページ(「1枚目の100円硬貨が入った時点でタイマーが動き出します」「連続5枚まで投入できます」)と、ゲームマシン 1986-09-15 の記事を確認した。
6. **第 1 パスの Q4 の Gap「日本語ホビーブログでのファミコン JAMMA 化事例は見つからず」**: 今回も、日本語の事例は検索の上限のため調べられなかった。英語の事例として NES2JAMMA(コインは未接続)と Console JAMMAizer(Select はボタンの組み合わせで代用、コインなし)を確認した。

---

## 未確認事項のまとめ
- PC-10 の BIOS がラッチに書き込む順序、時間切れ前の警告の有無、/GAMESTOP の実機での実装。
- FamicomBox の 1 コインあたりの時間(15 分か 20 分か)と、警告の開始タイミング。
- ファミコンステーションがコインに対応していたかどうかと、型番(AN-550 か AN-560 か)。
- IIコンの Select/Start ビットを読むファミコンソフトの具体名。上下・左右の同時押しでクラッシュするソフトの網羅的なリスト。
- 日本語の JAMMA 化事例(ブログ、X/Twitter、ヤフオク、YouTube)、国内のコインタイマーの設定範囲、ネットカフェなどの時間課金の慣行。これらは WebSearch の上限のため調べられなかった。
- NMOS 2A03 のクロックをどこまで止めてよいか(最低クロック)。
