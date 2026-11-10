# ファミコン業務用化の先例(VS./PC-10/FamicomBox)、コイン・時間制御の設計パターン、日本法上のリスク

(調査日 2026-11-10。作業途中保存版。法的事項は背景情報であり法的助言ではない。)

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
