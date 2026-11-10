# ファミコン業務用化の先例(VS./PC-10/FamicomBox)、コイン・時間制御の設計パターン、日本法上のリスク

(調査日 2026-11-10。法的事項は背景情報であり法的助言ではない。条文は e-Gov 法令API 取得版による。)

## Q1. Nintendo VS. System(VS. UniSystem / DualSystem)

### Takeaway
VS. System は RP2A03(無印リビジョン)+ RGB PPU(2C03/2C04/2C05)構成で、コイン・サービス・DIP は $4016/$4017 の未使用上位ビットに、スタートボタンはコントローラシフトレジスタの「Select」位置(3番目のビット)に割り当てられる。Famicom の Start 位置は UniSystem では未使用のため、無改造の家庭用ソフトはそのままではゲーム開始操作ができない(推論)。

### Cited Findings
- CPU は常に letterless(無印)リビジョンで、2A03G とは非互換(tonal noise 非対応)。各 CPU は $0000-$1FFF に 2 KiB RAM、$2000-$3FFF に PPU — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- PPU は RGB 出力。2C03 は NTSC 2C02 に近い色、2C04 は 60 色マスターパレットの並びを 4 種類に入れ替えた版(コピープロテクト目的、フェードには専用テーブルが必要)、2C05 は 2C03 と同色だが $2000/$2001 を入れ替え、$2002 bit4-0 に識別値を返す — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- $6000-$7FFF に共有 2 KiB RAM(DualSystem では CPU 間で切替、バッテリーバックアップ可)。ネームテーブル RAM は常に 4 KiB(4画面) — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- $4016 write: bit0 = コントローラストローブ、bit1 = (DualSystem)相手CPUへのIRQ/共有RAM選択、bit2 = CHR 8KiB バンク選択(mapper 99) — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- $4016 read: bit7 = 0:メインCPU/1:サブCPU、bit6-5 = コイン投入(各ビットを独立に確認する必要あり)、bit4-3 = DIP「2」「1」、bit2 = サービスボタン(通常クレジット投入)、bit1 = 常に0、bit0 = 右スティック直列データ(A, B, 1, 3, Up, Down, Left, Right の順) — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System);MAME も同一(bit2 service, bit3-4 DSW SW:1,2, bit5-6 coins, bit7 CPU indicator) — [MAME vsnes.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp)
- $4017 read: bit7-2 = DIP「8」〜「3」、bit1 = 常に0、bit0 = 左スティック(A, B, 2, 4, Up, Down, Left, Right の順) — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- つまりスタートボタン 1/2 は Famicom パッドの「Select」ビット位置(シフト3番目)、スタート 3/4(DualSystem)は「Start」ビット位置。MAME の UniSystem 定義では IN0 の 0x04 に START1、IN1 の 0x04 に START2、0x08 は IPT_UNUSED — [MAME vsnes.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp)
- 実配線は左スティック→$4017、右スティック→$4016(NES と逆)。多くのゲームは左を P1 とみなすが、SMB・TKO Boxing・Mighty Bomb Jack は右を P1 とみなす — [MAME vsnes.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp);[NESdev Wiki](https://www.nesdev.org/wiki/Vs._System) も「どちらを P1 とするかはゲームにより異なる」と記載
- コインカウンタ $4020 bit0(1→遅延→0 で1カウント)。$4020-$5FFF にミラー。10 Hz カウンタは 50 ms High / 50 ms Low で確実に駆動。電源投入・リセットでクリア — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- ウォッチドッグ: サブ CPU(ソケット 8J)が 1.2 秒以内ごとに $4017 を読まないと両 CPU・両 PPU・$4020 をリセット — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System);MAME も「Sub 側のみ $4017 読み出しでウォッチドッグを蹴る。UniSystem のゲームも Sub 側に挿す理由の一つ」 — [MAME vsnes.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp)
- コイン信号の長さ: MAME はコイン・サービスを 3 フレームのインパルスで入力。「1フレームでは短すぎるゲームがある(T.K.O. Boxing)。実機テストではコイン落下時間は 2.5〜4 フレーム」 — [MAME vsnes.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp)
- クレジット管理はゲームソフト側が $4016 のコインビットを読んで行う(ハードにクレジットカウンタはない)— 上記レジスタ構成より。

### Inferences
- 無改造ファミコンソフトを VS. ハードで動かすと:①パレット非互換(2C04 系)で色化け、②$4016 上位ビットにコイン・DIP 値が乗るため bit0 以外をマスクしないソフトは誤動作の可能性、③UniSystem には Start 位置の入力がないので開始・ポーズ不可、④2A03 の P2 マイク等も無し。本プロジェクトの「コイン→SELECT、スタート→十字4方向同時押し」は VS. の慣習(スタート=Select位置)とは異なる独自設計である。
- VS. 実機の「スタートを Select 位置に置く」慣習は、本プロジェクトのコイン=SELECT 案と同じビット位置を使う点で参考になる。

### Gaps
- VS. 用ソフトがファミコン版から具体的にどのように改修されたか(クレジット・タイマー・DIP 難易度)は個別ゲームの逆アセンブル情報が必要で未確認。

## Q2. Nintendo PlayChoice-10

### Takeaway
PC-10 は「コイン=プレイ時間」モデル。Z80 の BIOS が NES 側を /GAMERES・/GAMESTOP・/PPURES・/CNTRLMASK・/DISPMASK・/SOUNDMASK で制御し、残り時間を管理する。コントローラマスクは Select と Start ビットのみを落とす実装(MAME)。

### Cited Findings
- 構成: Z80 @ 4 MHz + N2A03 @ 1.789772 MHz。コインはクレジットではなく時間を追加 — [System16](https://system16.com/hardware.php?id=550)
- BIOS(Z80)入力ポート0: bit0 CHSelect, bit1 Enter, bit2 Reset, bit3 INTDETECT, bit5 Coin2, bit6 Service, bit7 Coin1。ポート1/2 = DIP1/2 — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- BIOS 出力ポート(bit0): 0=SDCS, 1=/CNTRLMASK, 2=/DISPMASK, 3=/SOUNDMASK, 4=/GAMERES, 5=/GAMESTOP, 8=NMI Enable, 9=DOG DI, A=/PPURES, B-E=CSEL0-3(カートリッジ選択 0〜9), F=8UP KEY — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- MAME 実装では /CNTRLMASK 有効時、P1 ラッチの 0x0c(Select と Start)だけをマスク(「mask out select and start」)。/SOUNDMASK はシステム全体ミュート — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- 時間表示用 4 桁(time_w → digit 出力)が BIOS 側にある — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- DIP: DSWA 下位6ビットでコイン A/B あたりの「時間単位」、DSWB 下位6ビットでタイマー速度、DSWB bit7 ON(他 OFF)でフリープレイ(9999 単位) — [MAME playch10.cpp コメント (Steph 2000.09.07)](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- MAME の別 DIP 定義では「Play Time/Coin」2:00〜4:50(10秒刻み)、「Bonus: Standard Time / Prime Time for 2 Coins / Prime Time for 4 Coins」(複数枚同時投入で 8〜100% ボーナス) — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- 「プレイ開始前に追加でコインを入れると時間が追加される」 — [NIWA PlayChoice-10](https://niwanetwork.org/wiki/PlayChoice-10)(二次資料)
- フリープレイ時はアトラクトモードが走らない欠陥がある — [NESdev forum archive](https://nesdev.nes.science/f4/t14054.xhtml)

### Inferences
- PC-10 の手法(時間切れでコントローラの Select/Start をマスク+BIOS がリセットしてメニューへ戻す)は、本プロジェクトの「時間制モード」実装にそのまま転用できる:時間切れ時に CPU リセット保持またはパッド入力マスク+映像ブランク+ミュート。
- Select/Start だけをマスクするのは「時間切れ後に新しいゲームを開始させない/ポーズ操作させない」ための部分マスクと解釈できる(未確認:実機 BIOS の時間切れ時の厳密なシーケンス)。

### Gaps
- 時間切れ時の厳密な挙動(即リセットか、ゲーム継続中は終了まで待つのか、映像を BIOS 画面に切替えるのか)は一次資料(PC-10 オペレーターマニュアル)で未確認。

## Q3. FamicomBox(SSS-CDS)/ シャープ ファミコンステーション/汎用コインタイマー基板

### Takeaway
FamicomBox は 100円硬貨で時間を買う方式で、専用コインタイマー IC(3199A)が残り時間を管理し、残り少なくなると LED 消灯・874 Hz ビープ・画面輝度 40% 化で警告、クレジット増減時に「例外」を起こしてシステムをリセットしメニューへ戻す。汎用コインタイマー基板は主にリレーで電源を切る方式。

### Cited Findings
- 課金方式: コイン/キー/CATV/フリープレイを DIP 7-8 で選択。コインボックスは 100円硬貨、LED が残り時間を表示し残り少ないと点滅。コネクタは /coin スイッチ入力・GND・コイン LED 出力。CTB-370S はクレジットカウンタ用に 5V が必要、CTB-370N はカウンタなし — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- 1コインあたりの時間: DIP SW2 = 0:10分 / 1:15分(コインタイマー TS1-0 = %01:10分、%10:15分) — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)。**食い違い**: MAME は「10 or 20 minutes - DIP selectable」、DIP 定義も「10 min / 20 min」 — [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp)。どちらが正しいか未確認(NESdev の方がハード解析に基づく記述が詳細)。
- コインタイマー 3199A: Sharp SM59x 系 4bit CPU。ROM は完全にはダンプされておらず動作は完全には解明されていない。出力 /ACT(クレジットあり)、/NE(残り少)、/NEF(終了間近点滅) — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- 残り少時の警告: コイン LED 消灯、874 Hz ビープ(DIP 9 で無効化可)、40% 輝度機能で画面を暗くする — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)。MAME は「coin beep (before time out)」「screen modulation (before time out)」を未エミュレートと注記 — [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp)
- 打ち切り機構: コインタイマーの「credit transition」パルスがクレジット得失のたびに例外を発生させ、有効例外数が 0→1 になると 3198 CIC を 1.76 ms リセット保持してコンソールをリセット。$5005W bit6 でパッド1/2を無効化可能だがコインタイマーが自動でセットするかは記載なし。明示的な打ち切りシーケンスの完全な記述はない — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- 追加コイン: 終了間近点滅は時間切れまたはコイン追加まで続く(=追加投入で延長) — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)。MAME 実装でもコイン毎に m_coins++、タイマー満了ごとに減算 — [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp)
- ロックアウト: 3198A CIC(16ピン)が $5004W のスロット選択を受け、不正カートなら単発リセットでメニューに戻しスロットをスキップ。カートは NES 型 72 ピンだが EXP ピン配置が異なり、通常 NES カートや EXP 使用の FC 変換アダプタは破損のおそれ — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- メニュー: ゲーム DB のチェックサム一致か任天堂ヘッダを持つゲームのみ起動。ゲームを選んだコントローラを joypad 1 に入れ替える。電源投入時から 6.83 Hz 周期例外が有効でメニューが無効化しないとリセットを繰り返す(ウォッチドッグ相当) — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox);MAME もメニューが ROM チェックサム DB と標準任天堂ヘッダで判定と記載 — [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp)
- カートは $8000-$FFFF のみにマップ、$6000-$7FFF は本体の 8 KiB RAM(非バックアップ)、/IRQ・M2・PPU A12 等の問題で多くのマッパーが誤動作 — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- DIP 一覧: SW1 動作モード/SW2 時間/SW4 タイトルアトラクト時間/SW5-6 デモ時間/SW7-8 課金モード/SW9 ビープ無効/SW10 ザッパー無効 — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- 設置先: ホテルで 100円硬貨により 10 or 20 分(MAME 記載)。ファミコンステーションについて **食い違い**: MAME は「より民生向け(コイン非対応)のユニット、機能はほぼ同一、色が異なる(Box=黒、Station=灰)」 — [MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp);NESdev は「Sharp FamicomStation (AN-560) としても発売」と同一機扱い — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)
- 汎用コインタイマー: コインでリレーを励磁し機器の主電源を供給、タイマー満了でリレー解放という古典的構成(特許例) — [US Patent 4805900 PDF](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4805900);市販タイマー基板 JY-184 は LED 表示付きコインメック用タイマー — [arcadexpress JY-184](https://www.arcadexpress.com/en/accessories/789-jy-184-timer-controller-board-with-led-display-for-coin-mechanism.html);コイン式 Xbox の例ではリレーで電源遮断する手法が「電源コードを抜くのと同じ」と批判されている — [Coin Operated Xbox (adambyers.com)](https://adambyers.com/posts/Coin-Operated-Xbox/)

### Inferences
- 任天堂の先例は「電源断」ではなく「リセット+メニュー復帰」「入力マスク」「映像/音声マスク」を組み合わせる。本プロジェクトの時間制モードでも、電源断より /RESET 保持+パッド入力マスク+映像ブランク(または減光)+ミュートが望ましい(電源断はカートリッジのバッテリーSRAM破損リスクが高い — 一般的な知見、本調査で一次資料未確認)。
- 残り時間警告は FamicomBox の「LED+ビープ+画面減光」が先例。PPU 単体ではオーバーレイ合成ができないため、外部7セグ/LED 表示+ビープ+(RGB段での)減光が実装しやすい。PC-10 も 4 桁の時間表示を BIOS 側に持つ。

### Gaps
- FamicomBox 実機で時間切れ時にプレイ中のゲームが即リセットされるのか、どのような猶予があるのかは一次資料で確認できず(NESdev も「明示的な打ち切りシーケンスは記載なし」)。
- 日本語の一次資料(取扱説明書、日本語 Wikipedia)は本調査では未取得。料金(100円で何分)の実運用値も未確認。

## Q4. 「コイン=ボタン押下」の設計パターン(無改造カートリッジ)

### Takeaway
1フレーム1回ポーリングのゲームに確実に検出させるには数フレーム(実機 VS. 準拠で約 3 フレーム ≒ 50 ms 前後)のパルスが目安。ただし長すぎると「押しっぱなし」扱いになり、SELECT/START の副作用(タイトルのカーソル移動、プレイ中のポーズ)が出る。

### Cited Findings
- VS. 実機のコイン信号は 2.5〜4 フレーム。MAME は 1 フレームでは短すぎるゲームがある(T.K.O. Boxing)ため 3 フレームのインパルスを採用 — [MAME vsnes.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/vsnes.cpp)
- PC-10 は時間外に P1 の Select/Start ビットのみマスク(新規開始・ポーズの制御に Select/Start が要であることを示す先例) — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- コインカウンタ(メカカウンタ)は 50 ms ON / 50 ms OFF で確実に駆動 — [NESdev Wiki: Vs. System](https://www.nesdev.org/wiki/Vs._System)
- ファミコンの RGB 化手段として RP2C02 置換基板「RGB2C02N」(税込 17,980円、MMC3 等互換性向上の Rev.3.2)が国内で流通 — [GDM 2025/05/07](https://www.gdm.or.jp/crew/2025/0507/586206)、[GDM 2024/01/12](https://gdm.or.jp/crew/2024/0112/521851)

### Inferences
- 推奨パルス: 3〜4 フレーム(50〜67 ms)押下、その後少なくとも同程度の解放期間を置き連続コインはキューイング。多くのゲームは「押下エッジ」で反応するため、解放期間がないと連続投入が 1 回にまとまる。
- 副作用: (1) SELECT 割り当て:タイトル画面のメニューカーソルが動く(1P/2P 選択がずれる)。プレイ中は多くのゲームで無視されるが、一部ではアイテム切替等に使う。(2) START 割り当て:プレイ中のコイン投入がポーズを引き起こす。→ 通常クレジットモードでは「コインはクレジット加算のみ(パッドに出さない)、開始はスタートボタン」方式の方が安全。コイン→SELECT はゲーム自体がクレジット処理を実装する専用カート向けとするのが妥当。
- Up+Down+Left+Right 同時押しをスタートとして提示する案: 標準パッドでは物理的に起こり得ない組合せのため専用カートの検出には好都合だが、無改造ソフトでは十字キー同時押しが予期しない挙動(グリッチ)を起こす例がある(例: 左右同時押しバグ — 一般知見、一次資料未確認)。時間制モードでは JAMMA START を素直にファミコン START へ割り当てる DIP 設定も検討すべき。

### Gaps
- 日本語ホビーブログでのファミコン JAMMA 化事例(コイン/スタート配線)は検索で見つからず未確認。

## Q5. 時間制プレイの設計パターン

### Takeaway
先例(PC-10/FamicomBox)は、時間単位を DIP で設定、追加コインで延長、残り少で警告、時間切れでリセット/入力マスク、フリープレイ DIP、を共通に持つ。

### Cited Findings
- PC-10: コイン A/B ごとの時間単位、タイマー速度、フリープレイ(9999 単位)、2 枚/4 枚同時投入ボーナス(Prime Time)を DIP で設定。標準 2:00〜4:50/コイン — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- PC-10 の Z80 は NES 側に対し /GAMERES(リセット)、/GAMESTOP、/PPURES、/CNTRLMASK、/DISPMASK、/SOUNDMASK を個別制御 — [MAME playch10.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/playch10.cpp)
- FamicomBox: 10/15 分(NESdev)または 10/20 分(MAME)、課金モード4種、警告(LED・874Hz・40%減光)、クレジット遷移でリセット — [NESdev Wiki: FamicomBox](https://www.nesdev.org/wiki/FamicomBox)、[MAME famibox.cpp](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/nintendo/famibox.cpp)
- 市販タイマー基板にはコイン追加で中断なく延長、一時停止機能などがある(ベンダー説明) — 検索結果要約経由、[arcadexpress JY-184](https://www.arcadexpress.com/en/accessories/789-jy-184-timer-controller-board-with-led-display-for-coin-mechanism.html)

### Inferences
- 推奨構成: DIP で 1コイン = 1/2/3/5/10 分程度、追加投入で加算、残り 30 秒程度で警告音+表示点滅、時間切れで (a) パッド入力を全マスク(または START/SELECT のみ)→ 数秒後 (b) CPU /RESET 保持+映像ブランク+ミュート、コイン投入で /RESET 解除。リセットは RP2A03 /RES と RP2C02 /RST を同時に。カートリッジ側は /RESET を受けないので、マッパーは CPU のリセットベクタ処理で初期化される(ファミコン本体の仕様と同じ)。
- 時間制では「コイン→SELECT」をゲームに見せる必要はない(ゲームはクレジットを知らない)ため、コインは時間加算のみに使い、パッドには出さないのが副作用最少。

### Gaps
- PC-10/FamicomBox の時間切れ時に「ゲーム途中なら何秒の猶予を与えるか」の正確な値は未確認。

## Q6. 日本法上のリスク(背景情報、法的助言ではない)

### Takeaway
最大のリスクは著作権(上映権)。市販ソフトをコイン収入目的で公衆に遊ばせる行為は、権利者の許諾がない限り著作権法 22 条の2 の上映権侵害となり得、2018 年にゲームバー経営者が逮捕された先例がある。自社開発ソフトのみなら上映権リスクは解消される。ゲームセンター設置は風営法5号営業の許可の枠内。PSE は DC 基板単体には通常かからないが電源装置は対象。

### Cited Findings(確定事実:条文・報道)
- 著作権法 22条の2「著作者は、その著作物を公に上映する権利を専有する。」 — [e-Gov 著作権法](https://laws.e-gov.go.jp/law/345AC0000000048)
- 同法 2条1項17号「上映」= 著作物(公衆送信されるものを除く)を映写幕その他の物に映写すること(映画の著作物に固定された音の再生を含む)。2条3項:「映画の著作物」には映画の効果に類似する視覚的又は視聴覚的効果を生じさせる方法で表現され、かつ、物に固定されている著作物を含む。2条5項:「公衆」には特定かつ多数の者を含む — [e-Gov 著作権法](https://laws.e-gov.go.jp/law/345AC0000000048)
- 同法 38条1項:営利を目的とせず、かつ観衆から料金を受けない場合のみ公に上映できる(=コイン収入のある運用には適用されない) — [e-Gov 著作権法](https://laws.e-gov.go.jp/law/345AC0000000048)
- 2018年6月12・13日、京都府警・兵庫県警共同捜査本部が京都市・神戸市のゲームバー4店舗の経営者・店長4名を「家庭用ゲームソフトを客に遊戯させて無断上映」した著作権法違反(上映権侵害)容疑で逮捕。ACCS と会員が警告書を送付していたが無視して継続していた — [ScanNetSecurity(ACCS発表転載)](https://scan.netsecurity.ne.jp/article/2018/06/14/41048.html);同件解説 — [弁護士ドットコム](https://www.bengo4.com/internet/n_8087/)、[政治山](https://seijiyama.jp/article/news/omn20180702-2.html)
- 大阪の系列店が ACCS の指摘を理由に 2018年7月29日閉店 — 検索結果要約による、[AUTOMATON](https://automaton-media.com/articles/newsjp/20180409-65798)(要原文確認)
- 風営法 2条1項5号:スロットマシン、テレビゲーム機その他の遊技設備で本来の用途以外の用途として射幸心をそそるおそれのある遊技に用いることができるもの(規則で定めるもの)を備える店舗等で客に遊技させる営業 — [e-Gov 風営法](https://laws.e-gov.go.jp/law/323AC0000000122)
- 同法施行規則3条2号:対象テレビゲーム機 = 勝敗を争うことを目的とする遊技をさせる機能を有するもの又は遊技の結果が数字・文字等で表示装置上に表示される機能を有するもの(射幸心をそそるおそれがある遊技に供されないことが明らかなものを除く) — [e-Gov 風営法施行規則](https://laws.e-gov.go.jp/law/360M50400000001)。スコア表示のあるファミコンソフトは通常これに該当すると考えられる(解釈)。
- 同法施行令1条:ホテル等(旅館・ホテル営業の建物)内、大規模小売店舗(500㎡超)内、遊園地内の区画施設で、外部から容易に見通せるものは5号営業から除外 — [e-Gov 風営法施行令](https://laws.e-gov.go.jp/law/359CO0000000319)(FamicomBox のホテル設置と整合する)
- 同法18条:5号営業所は午後10時以後18歳未満立入禁止の表示義務(条例でさらに制限可) — [e-Gov 風営法](https://laws.e-gov.go.jp/law/323AC0000000122)
- いわゆる「10%ルール」(他業種店舗での遊技機設置面積が客室の10%以下なら5号営業扱いしない運用)は解釈運用基準上の運用で、その法的根拠が訴訟で争点になった — [裁判所 判決PDF](https://www.courts.go.jp/app/files/hanrei_jp/635/083635_hanrei.pdf)、[DARTSLIVE 資料](https://www.dartslive.com/jp/for_entrepreneur/pdf/20181001.pdf)(解釈運用基準原文は未取得)
- 電気用品安全法 2条1項:電気用品 = 一般用電気工作物等の部分となり又はこれに接続して用いられる機械器具材料で政令で定めるもの — [e-Gov 電気用品安全法](https://laws.e-gov.go.jp/law/336AC0000000234)。直流電源装置は特定電気用品(◇PSE) — [METI 2015資料](https://www.meti.go.jp/policy/consumer/seian/denan/kaishaku/hani/kaiseigaiyou150122.pdf);遊戯機器等に組み込む直流電源ユニットを非対象とした解釈事例あり — [METI 組込用直流電源](https://www.meti.go.jp/policy/consumer/seian/denan/kaishaku/taishou_hitaishou/20030526/kumikomiyou_chokuden.pdf)(本文未精読、検索要約による)
- 商標: 任天堂は 2022-2023 年にファミコンカートリッジの形状・マークを商標出願 — [Game*Spark](https://www.gamespark.jp/article/2023/05/20/130085.html)。「ファミコン」名称はかつてシャープの商標だったとの記述あり(二次資料、未確認) — [ファミコン互換機(3rd-in pedia)](https://pedia.3rd-in.co.jp/wiki/%E3%83%95%E3%82%A1%E3%83%9F%E3%82%B3%E3%83%B3%E4%BA%92%E6%8F%9B%E6%A9%9F)

### Inferences(解釈)
- 市販ファミコンソフトの時間制運用は、2018年ゲームバー事件と同型(家庭用ソフトを料金を取って公衆に遊ばせる)であり、上映権侵害の刑事リスクが高い。ハードが自作基板でも結論は変わらない(上映主体は運営者)。権利者(任天堂・各社)の個別許諾が必要。VS./PC-10/FamicomBox は任天堂自身による業務用製品であり、許諾の問題がなかった点が本プロジェクトと決定的に異なる。
- 自社開発(権利を持つ)ソフトのみを稼働させる運用、または権利者許諾済みソフトに限る運用が現実的。「時間制モード=市販カート向け」という DIP 機能の設計・宣伝自体が侵害の助長と見られる余地がある(解釈;間接侵害の論点は未調査)。
- 中古本体から CPU/PPU を取り出して再利用すること自体は、著作権(チップ内に任天堂著作物の ROM は無い:2A03/2C02 にプログラム ROM なし — 一般知見)・特許(1983年出願系は満了)の観点で大きな問題は見当たらないが、確認できた一次資料はない(未確認)。CIC(10NES)は HVC-001 には無い。
- PSE: 5V/12V DC で JAMMA 筐体の電源から給電される基板単体は「一般用電気工作物に接続して用いられる」物に当たらず対象外となる可能性が高いが、AC アダプター等を同梱・販売する場合は特定電気用品(◇PSE)の規制対象(解釈。METI 製品安全課への照会推奨)。
- 商標: 製品名・広告に「ファミコン」「Famicom」「ファミリーコンピュータ」を商品名として使うのは避け、「HVC-001 規格カートリッジ対応」等の記述的表示に留めるのが一般的なリスク回避(解釈。J-PlatPat での登録番号・指定商品は未確認)。

### Gaps
- 中古ゲームソフト事件(最高裁 平成14年4月25日)等、ゲーム=映画の著作物とする判例の一次 URL は本調査で未取得(未確認)。
- ACCS 公式サイトの声明原文、警察庁「解釈運用基準」原文(10%ルール本文)、J-PlatPat 上の「ファミコン」商標登録番号・権利者・指定商品は未取得。
- チップ再利用(中古部品の流用)に関する法的論点の一次資料は見つからなかった。
