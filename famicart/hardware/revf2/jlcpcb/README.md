# JLCPCB 注文パッケージ（famicart rev F2: 任天堂の大型カセットシェル用、Basic 部品のみ）

回路は rev F と同じ（Pico 2 ×4 + XIAO RP2350）。外形・切り欠き・スリットを任天堂の大型シェル（HVC-ExROM 系。光栄・エニックス・
スクウェアの大型カセット、市販の互換「でかカセットケース」）に合わせ、シェルのリブとボスを避けて部品を置いた版。

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- **Layers 2** / Dimensions **90 x 85.7 mm**（本体 75.0 mm + 端子タブ 10.7 mm）/ **PCB Thickness 1.2 mm** / Surface Finish **ENIG**
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented
- 外形に**左右の切り欠きと内部スリット（5.4 × 2.4 mm）**がある。ガーバーの Edge_Cuts にそのまま入っているので追加指定は不要。
- Min Track/Spacing 0.15 mm、Via 0.5/0.25 mm（JLC 標準仕様内、追加料金なし）

## SMT Assembly（PCB Assembly → **Economic / Top side のみ**）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`。**全部品が JLCPCB Basic Parts**（`parts_check.csv` に API での確認結果）。
- 実装しない部品（DNP）: J1, U1, U2, U4, U5, U3, J2
- 部品プレビューで向きを確認するもの: 2N7002（Q1/Q2）、1N4148WS・B5819W（カソード帯）、抵抗アレイ。

## 手はんだ（秋月電子で購入）
| 部品 | 秋月 通販コード | 価格 | 位置 |
|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 ×4 | **裏**: U2（下、PPU 側）・U5（中、PPU 側コプロセッサ）・U1（上、CPU 側）／**表**: U4（上、CPU 側コプロセッサ） |
| Seeed XIAO RP2350 | 129619 | ¥1,100 | 表・中央右（U3、IRQ と拡張音源） |

- 裏の 3 枚を先に、表の U4・XIAO を後にはんだ付けすると楽。U4・U5 は載せなくても rev E と同じに動く。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（2 層・90×86 mm・金フィンガー・ENIG・1.2 mm）: 約 US$ 40–60
- 実装（Economic 片面、Basic のみ）: 5 枚で約 US$ 20–35
- モジュール（秋月）: 1 枚あたり ¥5,060（Pico 2 ×4 + XIAO RP2350）
- シェル: 任天堂の大型カセットの中古シェル、または互換の「でかカセットケース」
