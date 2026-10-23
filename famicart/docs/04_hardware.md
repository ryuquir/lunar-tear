# 04. ハードウェア（Pico / Pico 2 向け、26 GPIO 構成）— KiCad プロジェクト付き

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

再生成: `python3 tools/pcb/gen_sch.py && python3 tools/pcb/gen_pcb.py && python3 tools/pcb/route_pcb.py && python3 tools/pcb/gen_bom.py`

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
| JP1 | ソルダージャンパ | — | 音声バイパス（45–46 直結。拡張音声を使わないとき） |
| JP2 | ソルダージャンパ | — | 端子 31（CartridgePresent）を +5V へ。本体リビジョンにより必要 |

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
- **自動配線**: Freerouting の結果をそのまま収録。手直し（GND ベタの分断、端子付近の配線整理）はフェーズ 3 の実機検証と合わせて行う。
