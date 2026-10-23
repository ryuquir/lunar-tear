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
