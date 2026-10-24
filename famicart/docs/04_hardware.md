# 04. ハードウェア（Pico / Pico 2 向け、26 GPIO 構成）— KiCad プロジェクト付き（rev B）

rev B の追加点: **USB-C 端子**（基板上端、本体に挿したまま ROM 転送）、**リセット**（タクトスイッチ + ヘッダ、ソフトからの再起動）、Pico 裏面 USB テストパッドへの接続（D+/D− 入れ替えジャンパ付き）。

設計データは `hardware/` にあります（KiCad 7 形式、スクリプト生成）。

| ファイル | 内容 |
|---|---|
| `hardware/famicart.kicad_pro` / `famicart.kicad_sch` | プロジェクト・回路図（ラベル方式：全ピンにネット名のグローバルラベル） |
| `hardware/famicart.kicad_pcb` | 基板（2 層、90 × 46.1 mm、ファミコン実機基板寸法、自動配線済み） |
| `hardware/famicart.kicad_sym` / `famicart.pretty/` | 自作シンボル・フットプリント（Pico 2 SMD、ファミコン 60 ピン端子） |
| `hardware/fab/` | ガーバー（RS-274X）・ドリル（Excellon） |
| `hardware/bom.csv` | 部品表 |
| `hardware/famicart_schematic.pdf`, `famicart_front.pdf`, `famicart_back.pdf`, `famicart_front.png`, `famicart_back.png` | 図面 |
| `hardware/drc_report.txt` | DRC 結果 |
| `tools/pcb/design.py` | **設計の唯一の情報源**（部品・配置座標・ネット）。回路図・基板・BOM はここから生成 |
| `tools/pcb/gen_sch.py`, `gen_pcb.py`, `route_pcb.py`, `gen_bom.py` | 生成スクリプト（Freerouting による自動配線含む） |

再生成: `python3 tools/pcb/gen_sch.py && python3 tools/pcb/gen_pcb.py && FREEROUTING_JAR=~/freerouting-1.9.0.jar python3 tools/pcb/route_pcb.py && python3 tools/pcb/gen_bom.py`
（KiCad 7.0.11 の `pcbnew` Python モジュール、Java 17/21、Freerouting 1.9.0、X サーバ（`xvfb-run`）が必要。シングルスレッド `-mt 1` で約 2 分。2.0.1 は rev B では完走しなかった）

## 配線結果（rev B）

| 項目 | 値 |
|---|---|
| 層数 | 2（表: 部品・信号、裏: GND ベタ + 信号） |
| 配線幅 / クリアランス | 0.15 mm / 0.15 mm（製造仕様 5 mil 相当） |
| ビア | 0.5 mm / ドリル 0.25 mm |
| 配線本数 / ビア数 | 約 1,600 セグメント / 110 個 |
| 未接続 | **0** |
| DRC 違反 | **0**（KiCad 7 標準ルール + 基板端 0.3 mm） |
| キープアウト | 端子タブ（マスク境界 4 mm 線より下は端子以外の銅箔禁止）。USB-C の D+/D− ペア（A6–B6, A7–B7）はスクリプトで事前配線し固定 |
| パスコン | 各 IC の真裏（裏面）に配置。JP1〜JP4・W1 も裏面 |

## 基板外形（nesdev「Famicom cartridge dimensions」HVC-TGROM-01 実測値）

| 項目 | 値 |
|---|---|
| 基板幅 × 高さ | 90.0 × 46.1 mm（本体部 35.4 mm + 端子タブ 10.7 mm） |
| 端子タブ幅 | 78.4 mm（先端 1 mm 面取り、製造時に 2 mm × 30° ベベル指定） |
| 板厚 | **1.2 mm**（ファミコン実機は 1.2 mm。1.6 mm はスロットに入らない） |
| 端子ピッチ | 2.54 mm × 30、表（1–30）／裏（31–60、1 の真裏が 31） |
| 端子パッド | 信号 1.6 × 5.7 mm、電源（1, 30, 31, 60）2.6 × 6.7 mm、タブ基部から 3 mm 下にパッド上端 |
| 表面処理 | 端子はハードゴールド推奨（ENIG でも可、挿抜回数が少なければ） |

> シェル内側の切り欠き（inset 43/33 mm）は実測ページに位置情報がないため省略。手持ちのシェルに合わせて `tools/pcb/gen_pcb.py` の外形を調整してください。

## GPIO 割当（Pico が露出する 26 本をすべて使用。GP23–25 は露出していないため不使用）

| GPIO | 役割 | 相手 |
|---|---|---|
| GP0–GP7 | CPU 側 8 ビット共有ポート | U2（CTRL）/ U3（A8–14）/ U4（A0–7）出力、U5（D0–7）トランシーバ |
| GP8–GP15 | PPU 側 8 ビット共有ポート | U6（A8–13 + /RD + /WR）/ U7（A0–7）出力、U8（D0–7） |
| GP16 | /PPUACC（PPU /RD AND /WR） | U11 74LVC1G08 |
| GP17 | M2（3.3V） | U10 74LVC1G17 |
| GP18, GP19 | SELC[1:0] → U9 A 側 → Y0 CTRL/idle, Y1 A-lo, Y2 A-hi, Y3 データ | 74LVC139 |
| GP20, GP21 | SELP[1:0] → U9 B 側 → Y0 idle（未使用）, Y1 A-lo, Y2 A-hi, Y3 データ | 74LVC139 |
| GP22 | IRQ 出力（Low でアサート） | U12 74LVC1G07 → 端子 15 /IRQ（R5 10k プルアップ） |
| GP26 | 音声 PWM | R1/C1/R2/C2 → R3 → 端子 46 |
| GP27 | CIRAM A10 | 端子 18（直結、3.3V 出力） |
| GP28 | CIRAM /CE | 端子 48（直結） |

### 「CTRL バッファ」の仕組み（27 → 26 本に減らした鍵）

R/W と /ROMSEL は専用 GPIO ではなく、3 個目の 74LVC541（U2）経由で CPU ポートに乗せる。U2 の /OE はデコーダの **Y0（アイドル状態）** に接続されているため、PIO が何も選択していないとき常に R/W・/ROMSEL がポートに見える。PIO は M2 立ち上がり後に CTRL → A-hi → A-lo の順に 3 回取り込む。ポートをデータ出力に切り替える（Y3）瞬間は U2 が自動的に切り離される。

## 部品表（抜粋、詳細は `hardware/bom.csv`）

| Ref | 部品 | パッケージ | 備考 |
|---|---|---|---|
| U1 | Raspberry Pi Pico 2（RP2040 版 Pico でも動作、容量制限あり） | 基板上 SMD 実装（キャステレーション） | USB は基板左端に向く |
| U2, U3, U4, U6, U7 | 74LVC541APW | TSSOP-20 | 5V トレラント入力、3.3V 出力 |
| U5, U8 | 74LVC245APW | TSSOP-20 | 双方向。U5: DIR = R/W、U8: DIR = PPU /RD（A 側 = 本体） |
| U9 | 74LVC139PW | TSSOP-16 | デュアル 2→4 デコーダ（出力 Low アクティブ） |
| U10 / U11 / U12 | 74LVC1G17 / 1G08 / 1G07 | SOT-23-5 | M2 レベル変換 / PPU ストローブ合成 / IRQ オープンドレイン |
| R1, R2 / C1, C2 | 2.2k / 10n | 0603 | PWM 2 段 RC（fc ≈ 7 kHz） |
| R3 / R4 | 4.7k / 1k | 0603 | 拡張音声／本体音声ミックス（端子 45 → 46） |
| R5 | 10k | 0603 | /IRQ プルアップ（+5V） |
| C3, C4 | 10µ | 0805 | +5V / +3V3 バルク |
| C5–C15 | 100n | 0603 | 各 IC パスコン |
| JP1 | ソルダージャンパ（裏面） | — | 音声バイパス（45–46 直結。拡張音声を使わないとき） |
| JP2 | ソルダージャンパ（裏面） | — | 端子 31（CartridgePresent）を +5V へ。本体リビジョンにより必要 |
| J3 | USB-C レセプタクル 16 ピン | HRO TYPE-C-31-M-12 | 基板上端。USB 2.0 のみ |
| R6, R7 | 5.1k | 0603 | USB-C CC プルダウン |
| JP3, JP4 | 3 端子ソルダージャンパ（裏面） | P2.0 mm | USB D+/D− → Pico TP2/TP3 の割り当て選択 |
| W1 | 1.6 mm パッド ×3（裏面） | — | 手はんだ時の TP 配線用 |
| SW1 | タクトスイッチ | TL3342 | RESET（RUN を GND へ） |
| J2 | 2 ピンヘッダ | 2.54 mm | RUN/GND（本体リセットスイッチへの配線用、任意） |

## USB-C（J3）と Pico の USB 接続

- J3 は USB 2.0 専用 16 ピンの USB-C レセプタクル（HRO TYPE-C-31-M-12 互換）。基板上端（カートリッジを挿したとき上を向く辺）に開口が来る配置。**外装の上面に 9 × 3.5 mm 程度の穴**を開ける必要がある。
- CC1/CC2 は 5.1 kΩ プルダウン（R6/R7）で「5V シンク」を宣言。VBUS は Pico の VBUS 端子（ピン 40）へ入り、Pico 内蔵ダイオードで VSYS（本体 5V）とダイオード OR される。本体に挿したまま PC を接続しても競合しない。
- Pico の USB D+/D− はモジュールの micro-USB にしか出ていないため、**Pico 2 データシート Fig.5 のテストパッド TP2/TP3**（モジュール裏、USB 端子寄りの 2 点、1.5 mm 角）にフットプリント側のパッド（U1 の 44/45）を重ねて接続する。TP1（GND）も 46 番で接続。
- 図面上 TP2 と TP3 のどちらが D+ か確定できないため、JP3/JP4（3 端子ソルダージャンパ、裏面）で割り当てを選ぶ。**手順**: Pico 単体を micro-USB で PC に接続し、micro-USB の D+（コネクタ 3 番）と導通するテストパッドを特定 → それが TP_A（Pico 側 USB 端子寄り左）なら JP3 と JP4 を共に C–A 側へ、TP_B なら共に C–B 側へブリッジ。
- Pico を**手はんだ**で載せる場合は TP が隠れて届かないので、裏面の W1（1.6 mm パッド ×3: A, B, GND）へ Pico の TP2/TP3/TP1 から短い線を飛ばす。
- 注意: Pico の micro-USB と J3 の両方に同時にケーブルを挿さないこと（D+/D− が並列になる）。

## リセット（RUN）

- SW1（タクトスイッチ）と J2（RUN/GND 2 ピンヘッダ）を Pico の RUN に接続。押すと RP2040/RP2350 がリセットされる。
- **ソフトからのリセット**: USB-CDC コマンド `RESET`（ウォッチドッグ再起動）、`BOOTSEL`（UF2 書き込みモードへ）、`LOAD`（ROM 転送後に自動再起動）。詳細は `src/pico/usb_cmd.h` と `tools/fcload.py`。
- **本体側のリセットについて**: ファミコンのカートリッジ端子に /RESET 信号は存在しない（60 ピン中に無い）。したがって「ソフトから本体をリセット」はカートリッジ単体では不可能で、ROM 転送後は本体のリセットボタンを押す必要がある。どうしても自動化したい場合は J2 を本体のリセットスイッチ両端に配線し（本体改造）、GPIO で駆動する方法が取れる。

## 電源

端子 30（+5V）→ Pico VSYS。Pico 内蔵レギュレータの 3V3(OUT) でロジック IC（合計 ~30 mA）を給電。USB を同時接続しても Pico のダイオード OR で問題なし。

## 音声回路

```
GP26 (PWM ~246 kHz) ─ R1 2.2k ─┬─ R2 2.2k ─┬─ R3 4.7k ─┬──── 端子 46 (AUDIO_OUT)
                               C1 10n     C2 10n       │
                               GND        GND    端子 45 ─ R4 1k ─┘   JP1: 45–46 直結
```

## 既知のリスクと対策

- **CIRAM タイミング**: RP2040 がアドレス解読後に A10 / /CE を駆動するため約 80 ns 遅れる。問題が出れば 74LVC153 で A10 をハードウェア選択（空き GPIO 2 本が必要 → 素の RP2040 / RP2350B 基板で）。
- **CPU 読み出し余裕**: 約 ±50 ns。252 MHz 動作、または RP2350（Pico 2）推奨。
- **自動配線**: Freerouting 1.9.0 の結果をそのまま収録（未接続 0 / DRC 0）。表面 GND ベタは配線で分断されるため、裏面ベタが主 GND。見た目の整理や GND スティッチングビア追加はフェーズ 3 の実機検証と合わせて行う。
- **シェル適合**: 外形は nesdev の HVC-TGROM-01 実測値に基づくが、シェル内側の切り欠きは未反映。初回試作で現物合わせを推奨。

---

# rev C: RP2350B（ベアチップ）+ Seeed XIAO RP2040 の 2 MCU 構成

rev B の「Pico 2 モジュール 1 個」を、**基板直付けの RP2350B（QFN-80、GPIO 48 本）** と **音源コプロセッサとしての XIAO RP2040** に分けた版。ユーザー要望（XIAO を使う／全マッパー／全拡張音源の横断利用／USB 3 口／リセット端子）を満たすための設計。
生成物は `hardware/revc/`（回路図・基板・fab・jlcpcb）。**配線結果: 2 層、未接続 0、DRC エラー 0**（Freerouting 1.9、トラック/クリアランス 0.15 mm、ビア 0.5/0.25 mm。DRC 報告の警告 58 件は KiCad 標準ライブラリとの照合警告で製造には無関係）。RP2350B の露出パッドは 0.4 mm ピッチのピン列に囲まれて自動配線が届かないため、サーマルビアから上下のパスコン GND パッドへの固定配線（`FIXED_LINKS`）で接続している。ジェネレータは `tools/pcb/design_revc.py`（`FC_DESIGN=design_revc FC_HW_DIR=hardware/revc` で各スクリプトを実行）。

## 役割分担

| MCU | 役割 | 理由 |
|---|---|---|
| **U1 RP2350B** @300 MHz | カートリッジバス全体（CPU 26 本・PPU 16 本）、マッパーエンジン、ROM 保持（SRAM 440 KB + QSPI フラッシュ 16 MB）、USB データ転送（J3）、拡張音源レジスタの受付と転送 | GPIO 48 本・5 V トレラント入力・520 KB SRAM。バスは **バッファ無しで直結**（rev B の 541/245/139 による多重化が不要になり、M2 1 サイクルあたりの PIO 取り込みが 1 回で済む） |
| **U8 XIAO RP2040** @200 MHz | 拡張音源 6 種（VRC6/VRC7/MMC5/N163/5B/FDS）のソフトシンセと PWM 出力、ステータス LED | 音源合成を主 MCU から追い出し、バス応答のタイミング余裕を確保。XIAO の USB は専用ポートとして露出（ファーム更新・音源デバッグ）。 |

PPU 側だけは GPIO 節約のため rev B 同様に **PPU A0–7 / D0–7 を 1 ポート共有**（U4 74LVC541 ＋ U5 74LVC245、PPU_SEL で切替、U6 1G08 で /PPUACC = /RD AND /WR、U7 1G04 で 245 の OE 反転）。CPU 側は直結。

## RP2350B GPIO 割当（48 本全使用）

| GPIO | 信号 | GPIO | 信号 |
|---|---|---|---|
| 0–14 | CPU A0–A14 | 30–37 | PPU 共有ポート（A0–7 / D0–7） |
| 15–22 | CPU D0–D7 | 38–43 | PPU A8–A13 |
| 23 | CPU R/W | 44 | /PPUACC（= /RD & /WR） |
| 24 | M2 | 45 | PPU /RD |
| 25 | /ROMSEL | 46 | PPU_SEL（541/245 切替） |
| 26 | /IRQ（オープンドレイン模擬、R5 10k で +5V プルアップ） | 47 | CIRAM A10 |
| 27 | CIRAM /CE | 28 / 29 | UART0 TX / RX → XIAO |

PIO: `src/pico/fc_bus_direct.pio`。`fc_cpu_direct` が M2 立ち上がりで GPIO0–25 を 26 bit 一括取り込み、`fc_ppu_direct` が GPIO30–45 を 16 bit 取り込み（side-set で PPU_SEL）。

## XIAO RP2040 ピン割当

| XIAO | 信号 | 備考 |
|---|---|---|
| D6 (GPIO0) TX | UART_RX → RP2350B GPIO29 | 3 Mbaud |
| D7 (GPIO1) RX | UART_TX ← RP2350B GPIO28 | 3 Mbaud、音源レジスタ・制御フレーム |
| D0 (GPIO26) | PWM 音声 → R1 2.2k / C1 10n / R2 2.2k / C2 10n（2 段 LPF）→ R3 4.7k → AUDIO_OUT（pin 46） | rev B と同じフィルタ定数 |
| 5V | XIAO_5V ← D2 ← +5V | 本体 5 V から給電。XIAO 側 USB からの逆流は D2 で遮断 |
| RST | RUN | SW1 / J2 で RP2350B と同時にリセット |
| GND ×3 | GND | |
| 残り 12 ピン | 未接続（NC） | 将来の拡張用 |

XIAO は JLCPCB の在庫に無いため **DNP（手実装）**。基板には XIAO 用 14 パッドのフットプリント（`famicart:XIAO-RP2040-SMD`）があり、裏返して載せて側面キャステレーションをハンダ付けする。

## USB 3 口の構成

| コネクタ | 接続先 | 用途 |
|---|---|---|
| **J3 USB-C（DATA）** | RP2350B USB（R10/R11 27 Ω 直列、CC1/CC2 5.1k） | ROM のリアルタイム転送（`tools/fcload.py`：INFO / LOAD / PROFILE / RESET / BOOTSEL）。**本体に挿したままでも使用可**。VBUS → D1 → +5V で本体電源と OR 結合（本体 OFF でも USB だけで動く） |
| **J4 USB-C（RP2350 予備）** | J3 と D+/D− が並列（CC3/CC4 5.1k） | 標準 **DNP**。ケース開口の都合で J3 と別位置に出したい時用。J3 と J4 を同時に PC に挿さないこと |
| **XIAO の USB-C** | XIAO RP2040 固有 | コプロセッサのファーム書き込み（BOOTSEL は XIAO 本体のボタン）、音源デバッグログ |

RP2350B の BOOTSEL は SW2（QSPI_SS を R13 1k 経由で GND）。J3 を挿して SW2 を押しながら SW1 を離すと UF2 ドライブとして現れる。ソフトからは `BOOTSEL` コマンドで同じ状態に入る。

## リセット端子

- **SW1**（タクトスイッチ）と **J2 1×2 ピンヘッダ（RUN / GND）** を RUN ネットに並列接続。J2 にケース外へ出すスイッチや本体リセット線を付けられる。
- RUN は RP2350B の RUN ピンと XIAO の RST を兼ねるので、両 MCU が同時にリセットされる。
- ソフトからのリセットは USB `RESET` コマンド（ウォッチドッグ再起動）。本体側の CPU リセットはカートリッジ端子に出ていない（ファミコンの仕様）ため、**ゲーム側の再起動は電源 OFF/ON か本体リセットボタン**になる。カートリッジのリセット（ROM 差し替え後の再起動）はこれで完結する。
- J5 1×3（SWCLK / GND / SWDIO）: RP2350B の SWD デバッグ用。DNP。

## 電源

本体 +5V（pin 1/60 相当）→ U3 AP2112K-3.3（600 mA）→ +3V3（RP2350B IOVDD/QSPI/ロジック）。RP2350B 内蔵スイッチングレギュレータ（L1 3.3 µH, C3/C4/C5 4.7 µF, R12 33 Ω）が +1V1 コアを生成。XIAO は +5V から D2 経由。消費電流の見積: RP2350B@300 MHz 約 80 mA、XIAO 約 40 mA、ロジック約 10 mA → 本体 5 V から約 130 mA（ファミコンのカートリッジ供給能力内）。

## MCU 間リンク（UART0, 3 Mbaud, 4 バイト固定長フレーム）

```
byte0 = 0xF0 | chip   (chip: 0 = 制御, 1 VRC6, 2 VRC7, 3 MMC5, 4 N163, 5 S5B, 6 FDS)
byte1 = addr_hi, byte2 = addr_lo  (チップ固有のネイティブレジスタアドレス、例 VRC7 $9010/$9030、MMC5 $5000-$5015、FDS $4040-$408A)
byte3 = value
制御: addr 0 = 全音源リセット / 1 = マスター音量 / 2 = LED 色（RGB565 上位・下位）
```
主 MCU 側 `expaudio.c` は、ゲームがどのチップのどの窓に書いたかを **プロファイルで自由に再配置**した上で（例: VRC7 の $9010/$9030 を MMC5 ゲームの空き領域 $5800/$5810 に移す）、ネイティブアドレスへ正規化してフレーム化する。XIAO 側 `src/xiao_audio/main.c` は `expaudio_apply()` で同じレジスタモデルに流し込み、`synth.c` が 6 音源を同時にミックスする。これにより **MMC5 のマッパー機能（ExRAM・拡張属性・スキャンライン IRQ）と VRC7 の FM 音源を同時に使う**といった横断構成が、ハード変更無しでプロファイル 1 つで成立する。

## 部品表（rev C、`hardware/revc/jlcpcb/bom_jlc.csv`）

| Ref | 部品 | LCSC |
|---|---|---|
| U1 | RP2350B QFN-80 | C42415655 |
| U2 | W25Q128JVSIQ 16 MB QSPI | C97521 |
| U3 | AP2112K-3.3 | C51118 |
| U4 / U5 | SN74LVC541APWR / 74LVC245APW | C113281 / C6082 |
| U6 / U7 | SN74LVC1G08DBVR / SN74LVC1G04DBVR | C7666 / C7827 |
| U8 | Seeed XIAO RP2040 | DNP（手実装） |
| Y1 | ABM8-272-T3 12 MHz（Pico 2 と同一品） | C20625731 |
| L1 | AOTA-B201610S3R3 3.3 µH | C42411119 |
| J3 / J4 | HRO TYPE-C-31-M-12 | C165948（J4 は DNP） |
| SW1 / SW2 | TL3342F160QG | C2886898 |
| D1 / D2 | B5819W ショットキー | C64885 |
| R/C | 0603/0402 ベーシック部品 | bom_jlc.csv 参照 |

## 既知のリスク（rev C 固有）

- **5 V トレラント GPIO の条件**: RP2350 は IOVDD=3.3 V のとき入力が 5 V トレラント（データシート §14.8.2.1）。ただし出力は 3.3 V なので、CPU D0–7 を駆動する時のハイレベルは 3.3 V。本体 CPU（RP2A03）は 2.0 V 以上を H と見るため動作上は問題無い（rev B の 245 経由と同じ条件）。
- **QFN-80 0.4 mm ピッチ**: 手ハンダは難しいため JLCPCB SMT 実装前提。
- **バスタイミング**: 300 MHz でも M2 の H 期間 350 ns 中にアドレス取り込み → テーブル参照 → データ駆動を 1 サイクルで終える必要がある。rev B と同じソフト構造だが、`fc_cpu_direct` は取り込みが 1 回なので約 60 ns 余裕が増える。実機測定まではオーバークロック無しの 150 MHz でも動くかは未確認。
- **XIAO の手実装**: キャステレーションのピッチは 2.54 mm で手付け可だが、裏面の中央パッド群（NC）はハンダ不要。

---

# rev D: 実カセット型の分離構成（マッパーチップ / PRG ROM / CHR ROM / RAM）

rev B/C は「MCU が ROM データそのものを SRAM から供給する」方式でした。rev D は **実際のファミコンカセットと同じ役割分担** に戻した版です。
MCU は「マッパー IC（＋拡張音源）」に徹してバンク線とチップセレクトを駆動し、ゲームデータは **別チップのパラレル NOR フラッシュ** が本体バスへ直接応答します。
生成物は `hardware/revd/`、ジェネレータは `tools/pcb/design_revd.py`（`FC_DESIGN=design_revd FC_HW_DIR=hardware/revd`）。

## チップ構成（実カセットとの対応）

| 役割 | 実カセット（例: MMC5 基板） | rev D |
|---|---|---|
| プログラム ROM | マスク ROM 128 KB～1 MB | **U5 S29GL01GS**（1 Gbit パラレル NOR、TSOP-56）を 64M×8 として使用 → **PRG 64 MB** |
| キャラクタ ROM | マスク ROM 8 KB～512 KB | **U6 S29GL01GS** → **CHR 64 MB** |
| ワーク RAM（セーブ） | 8～64 KB SRAM ＋電池 | **U7 FM28V100** 128 KB **F-RAM**（不揮発、電池不要、SRAM 互換タイミング 60 ns。8 KB バンク、PRG バンク線 A13–A16 で 16 バンク = MMC5 の 64 KB も収容） |
| キャラクタ RAM / 4 画面 NT | 8 KB SRAM（CHR-RAM 基板）／NT RAM | **U8 IS62WV5128** 512 KB SRAM（1 KB バンク、CHR バンク線 A10–A18） |
| マッパー IC（CPU 側） | MMC1/3/5、VRC、FME-7 … | **U1 RP2350B**「PRG マッパー／拡張音源チップ」 |
| マッパー IC（PPU 側） | 同上（1 チップ内） | **U2 RP2350B**「CHR マッパー」 |
| 拡張音源 | VRC6/VRC7/N163/5B/MMC5 内蔵音源 | U1 のコア 1 で合成 → PWM → RC フィルタ → 端子 46 |

「一般的なフラッシュ ROM で最大容量」の要件には、JLCPCB で実装できるパラレル NOR の中で最大の **S29GL01GS（1 Gbit = 128 MB、x16 専用）** を選び、8 bit バスなので下位バイト DQ0–7 のみ使用（上位 DQ8–15 は 10 kΩ でプルアップし 0xFF で書く）→ **1 チップ 64 MB** です。
同じピン配置の S29GL512S（64 MB → 32 MB 使用）/ S29GL128S（16 MB → 8 MB）に無改造で差し替えられます。ライセンス品の最大は PRG 768 KB / CHR 512 KB なので、**フラッシュ 1 枚に全ライセンス・タイトルの大半を「ROM ライブラリ」として入れ、起動メニューで選ぶ**運用ができます（ファーム側 フェーズ 4）。

## バス構成（3.3 V ローカルバス）

本体バスは 5 V なので、**74LVC541（アドレス・制御、計 5 個）と 74LVC245（データ、2 個）** で 3.3 V の「ローカルバス」に変換し、MCU・フラッシュ・SRAM はすべてローカルバス側に置きます（LVC は 5 V トレラント入力、3.3 V 出力は本体 CPU/PPU の TTL 入力しきい値 2.0 V を満たす）。

```
本体 CPU バス(5V) ─541x3→ CA0-14, CRW, CM2, CnROMSEL ─┬→ U1 RP2350B（監視）
                   ─245 ─→ CD0-7（双方向、DIR=/RW, /OE=CD_nOE）├→ U5 PRG flash  A0-12=CA, A13-25=PRG_A13-25(U1), /CE=CnROMSEL, /OE=/RW, /WE=U1
                                                              └→ U7 WRAM(F-RAM) A0-12=CA, A13-16=PRG_A13-16,  /CE1=WRAM_nCE(U1), CE2=H, /OE=/RW, /WE=NAND(M2,/RW)
本体 PPU バス(5V) ─541x2→ PA0-13, PnRD, PnWR ────────────┬→ U2 RP2350B（監視）
                   ─245 ─→ PD0-7（DIR=/RD, /OE=PD_nOE）    ├→ U6 CHR flash  A0-9=PA, A10-25=CHR_A10-25(U2), /CE=139.Y0, /OE=/RD, /WE=U2
                                                              └→ U8 CHR RAM    A0-9=PA, A10-18=CHR_A10-18,     /CE=139.Y1, /OE=/RD, /WE=/WR
CD0-7 ─245(ブリッジ, /OE=nBRIDGE)→ PD0-7   … CHR フラッシュ書き込み時だけ有効（U1 がデータ、U2 がアドレスを出す）
```

グルーロジック（すべて 3.3 V 側）:
- `CD_nOE = (CnROMSEL AND WRAM_nCE AND nDRIVE) OR ISOLATE`（U13 1G11 + U14 1G32）: ROM 領域・WRAM・MCU 応答（$4020–$5FFF の MMC5 レジスタ読み等）のときだけ CPU データバスを開く。
- `CRWn = NOT CRW`（U15）、`WRAM_nWE = NAND(CM2, CRWn)`（U16）。
- `PPU_ACC = NAND(/RD, /WR)`、`CIRAM_nCE = NAND(PA13, nFOURSCR)`（通常 = /A13、4 画面/ExRAM 時は CIRAM 無効）、`nCART_ACC = NAND(PPU_ACC, CIRAM_nCE)`（U20 74LVC00）。
- `PD_nOE = nCART_ACC OR ISOLATE`（U21）。U22 74LVC139 が nCART_ACC を /G、`CHR_SEL`（U2）を A にして CHR フラッシュ／CHR RAM の /CE を振り分け。
- `ISOLATE`（U1、10 kΩ プルダウン）= 1 で全 541/245 を切り離し → USB 給電のみでフラッシュ書き込み（本体から抜いた状態）。
- /IRQ は U26/U27（1G07 オープンドレイン）で U1・U2 のどちらからも引けるワイヤード OR。
- CIRAM A10（ミラーリング）は U2 の GPIO が PPU A10/A11 を見て直接出力（H/V/1 画面 A/B）。

## RP2350B の GPIO 割当

**U1（PRG マッパー）** — 48 本すべて使用
| GPIO | 信号 | GPIO | 信号 |
|---|---|---|---|
| 0–14 | CA0–14（ローカル CPU アドレス） | 40 | WRAM_nCE |
| 15–22 | CD0–7 | 26 | nDRIVE（MCU がデータを返す。PIO0 の窓内なので PIO の side-set で駆動） |
| 23 / 24 / 25 | CRW / CM2 / CnROMSEL | 41 | nIRQ_A |
| 27–39 | PRG_A13–A25（8 KB バンク、64 MB、1 回のマスク書き込みで更新） | 42 | PWM（拡張音源） |
| 43 / 44 | LINK_CLK / LINK_DATA（→ U2、PIO 同期シリアル） | 45 | LINK_B2A（← U2） |
| 46 | PRG_nWE（フラッシュ書き込み） | 47 | ISOLATE |

**U2（CHR マッパー）**
| GPIO | 信号 | GPIO | 信号 |
|---|---|---|---|
| 0–13 | PA0–13（ローカル PPU アドレス） | 33 | nFOURSCR |
| 14 / 15 | PnRD / PnWR | 34 | CIRAM_A10 |
| 16–31 | CHR_A10–A25（1 KB バンク、64 MB） | 35 | LED |
| 32 | CHR_SEL（0 = CHR ROM, 1 = CHR RAM） | 36 | CHR_nWE |
| 37 / 38 / 39 | LINK_CLK / LINK_DATA / LINK_B2A | 40 / 41 | nIRQ_B / nBRIDGE |
| 42–47 | 予備 | | |

## ファームウェア（フェーズ 4、実装済み・実機未検証）

| ファイル | 役割 |
|---|---|
| `src/pico/board_revd_prg.h` / `board_revd_chr.h` | U1 / U2 のピン定義（`FC_VIRTUAL_ROM=1`: ROM/RAM は外部チップ） |
| `src/core/cartload.c`（`cart_load_from_info`） | 画像を SRAM にコピーせず、`prg_map/chr_map` を **仮想アドレス**（`FC_VROM_*`）で構築。既存 63 マッパーのコードは無変更 |
| `src/core/rom.c`（`rom_inspect_header`） | ヘッダ 16 バイト＋データ CRC だけで判別（DB 照合込み） |
| `src/pico/bankout.c` | U1 コア 1: CA13/CA14//ROMSEL を監視し `PRG_A13–25` と `WRAM_nCE` を出力（テーブルは `tables_dirty` で再符号化） |
| `src/pico/bus_revd.c` + `fc_bus_revd.pio` | U1 の M2 ごとの取り込み、$4020–$5FFF の応答（nDRIVE を PIO の side-set で駆動）、レジスタ書き込みをマッパーと U2 へ転送、$FFFC/$FFFD 読み出しでリセット検出 |
| `src/pico/maplink.c` + `maplink.pio` | U1→U2 32 bit フレーム（25 Mbit/s、1.3 µs）、U2→U1 PIO UART 2 Mbaud |
| `src/revd_chr/main.c` | U2: 同じマッパーコアを U1 から届く書き込みで同期、コア 1 が PA10–13 から `CHR_A10–25`/`CHR_SEL`/`CIRAM_A10`/`nFOURSCR` を出力、/RD 立ち下がりで `ppu_addr` フック（MMC2/MMC3/MMC5）→ nIRQ_B |
| `src/pico/norflash.c` | 外部 S29GL の書き込み（ライトバッファ 512 B、DQ7 ポーリング）、F-RAM 読み書き、CHR 側は U2 とブリッジ経由 |
| `src/revd_prg/usb_cmd_revd.c` + `src/pico/library.h` | ROM ライブラリ（U1 の QSPI に索引、最大 63 本）: `LIBADD/LIB/LIBSEL/LIBDEL/BOOTBANK/FLASHID/WRAMDUMP` |
| `tools/bootstub.py` → `bootstub_gen.h` | 起動バンク（6502 スタブ 50 バイト） |
| `tools/fcload.py` | ホスト側: `libadd game.nes` でフラッシュ書き込み＋登録＋起動 |

ビルド: `cmake -S . -B build-revd_prg -DFC_BOARD=revd_prg && cmake --build build-revd_prg`（U2 は `revd_chr`）。ホストテスト `test/test_virtual.c` が仮想アドレス→バンク番号の変換（MMC3/UNROM/4 画面）を確認する。

## 動作の仕組み（設計メモ）

- **PRG バンク**: U1 のコア 1 が CA13/CA14/CnROMSEL を監視し、現在のウィンドウ（$6000/$8000/$A000/$C000/$E000）に対応するバンク番号を `PRG_A13–25` に出力する（既存の `prg_map[]` 8 KB テーブルがそのままバンク表になる）。応答はアドレス確定から約 40 ns、フラッシュ 100 ns、バッファ 10 ns → M2 の H 期間 350 ns 内。
- **レジスタ書き込み**: 既存 PIO `fc_cpu_direct` が M2 ごとに 26 bit を取り込み、コア 0 がマッパーの `write()` を呼ぶ（rev C と同じコード）。変化した CHR バンク・ミラーリング・IRQ 設定はリンクで U2 に送る（16 bit フレーム ≒ 0.4 µs）。
- **CHR バンク**: U2 のコア 1 が PA10–13 を監視し `CHR_A10–25` と `CHR_SEL` を出力（`chr_map[]` 1 KB テーブル）。MMC2/MMC4 の $FD/$FE ラッチ、MMC3 の A12 立ち上がりカウンタ、MMC5 のスキャンライン検出（/RD 170 回 = 1 ライン）は U2 が PPU バスを直接見て処理し、IRQ は nIRQ_B で出す。
- **拡張音源**: U1 のコア 1 はバンク出力ループが軽いので、コア 1 の空き時間で `synth.c` を回せる（または PIO/DMA 駆動の PWM）。XIAO は不要になった。
- **ROM 転送**: USB（J3）→ U1 が `ISOLATE=1` にして 541/245 を切り離し、ローカルバスを自分で駆動して PRG フラッシュを書く。CHR はブリッジ 245 を開き、U1 がデータ・U2 がアドレスと /WE を出す（リンクで 1 バイトずつ同期）。S29GL のバッファ書き込み（512 バイト）で約 1 MB/s → 1 MB のゲームが数秒。**書き込みは本体から抜いた状態（USB 給電）で行う**（本体バスへの逆駆動を避けるため）。
- **ROM ライブラリ**: フラッシュ 64 MB に複数タイトルを置き、プロファイル表（オフセット・マッパー・音源）をフラッシュ先頭に保持。起動メニュー（U1 が小さな NES プログラムをフラッシュに置き、最初にそれを $8000 にマップ）で選択 → バンク表の基点を切り替えてソフトリセット。

## 基板

- **4 層** 90 × 46.1 mm（F.Cu 信号 / In1 GND / In2 +3V3 / B.Cu 信号）。2 層では QFN-80 ×2 と TSOP-56 ×2 を 90 × 35 mm に収めて配線できないため。
- 表面: U1/U2（左右）、水晶、QSPI フラッシュ、USB-C ×2（上辺中央、J3 = U1、J4 = U2）、リセット SW1、BOOTSEL SW2/SW3、LDO U28、単ゲート列、音声フィルタ、ピンヘッダ J2（RUN/GND）・J5/J6（SWD）。
- 裏面: U5/U6 フラッシュ、U7 F-RAM、U8 SRAM、74LVC541 ×5（左右端）、74LVC245 ×3・139・00（中央）、パスコン。
- 電源: 本体 +5V または USB VBUS（D1/D2 で OR）→ AMS1117-3.3（SOT-223、1 A）。見積消費: RP2350B 2 個 120 mA + フラッシュ 2 個 60–80 mA + SRAM/ロジック 40 mA ≒ **250 mA**（LDO 損失 0.4 W、SOT-223 で許容）。本体 5 V 供給能力は AV ファミコンで余裕あり、初代でも 7805 の範囲内。

## 電源投入直後の動作（起動バンクとブートスタブ）

MCU が起動する数 ms の間も本体 CPU は動いているので、rev D では **PRG バンク線 13 本を 10 kΩ でプルアップ**（RN7–RN9 + R）し、U1 が出力を始めるまで全ウィンドウがフラッシュ最上位の 8 KB「起動バンク」に固定されるようにした。起動バンクには小さな 6502 スタブ（`tools/bootstub.py` で生成、フェーズ 4）を置く:

1. RESET ベクタ → 割り込み禁止、PPU 描画 OFF、本体 RAM $0300 にトランポリンをコピーして JMP。
2. トランポリンは `$5F00`（U1 が nDRIVE で返す）を読み、`$A5`（準備完了）になるまで待つ。U1 は起動後にマッパー初期化とバンク表の出力を済ませてから `$A5` を返す。
3. `$5F01` が 1 なら `JMP ($FFFC)`。このとき既にバンク線はゲームの値なので、ゲームのリセットベクタに正しく入る。

本体 RAM で待つのでカートリッジ側は何をしても安全で、同じ仕組みが ROM ライブラリのメニュー（フェーズ 4）とセーブ退避にも使える。

## 既知のリスク・制限

- **PRG-ROM を $6000–$7FFF にマップするマッパー**（FME-7 等の一部）はハードの /CE 構成上そのままでは不可。U1 が起動時に該当バンクを F-RAM へコピーして RAM として見せる方法で対応予定（フェーズ 4）。
- **MMC5 拡張アトリビュート**: MCU が PPU データバスを駆動する機能が無いため未対応（ExRAM ネームテーブル・フィルモード・スキャンライン IRQ・WRAM 64 KB は対応）。該当タイトルは Just Breed 等ごく少数。
- **S29GL01GS の在庫**（JLC 25 個、約 US$ 9）: 不足時は S29GL512S/128S に差し替え。F-RAM FM28V100（約 US$ 11、在庫 489）は SRAM IS62WV5128 + 電池回路でも代替できるが、電池ホルダの置き場所が無いため F-RAM を標準にした。
- **実機未検証**。CHR 側のタイミング（アドレス確定 → バンク出力 40 ns → フラッシュ 100 ns → 245 → PPU のデータ取り込みまで約 300 ns）は計算上は余裕があるが、U2 のコア 1 ループのジッタはロジアナで確認が必要。
