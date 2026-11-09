# JLCPCB 注文パッケージ（famicart rev F: rev E + SFC 型コプロセッサ用 Pico 2 ×2、Basic 部品のみ）

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- **Layers 2** / Dimensions **90 x 70.1 mm**（本体 59.4 mm + 端子タブ 10.7 mm）/ **PCB Thickness 1.2 mm** / Surface Finish **ENIG**
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented
- Min Track/Spacing 0.15 mm、Via 0.5/0.25 mm（JLC 標準仕様内、追加料金なし）
- 純正シェルには入らない（上に 24 mm 長い）。ファミコンのスロットは上が開いているので基板のまま挿せる。外装が要るなら 3D プリントで。

## SMT Assembly（PCB Assembly → **Economic / Top side のみ**）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`。**全部品が JLCPCB Basic Parts**（`parts_check.csv` に API での確認結果）。
- 実装しない部品（DNP）: J1, U1, U2, U4, U5, U3, J2
- 部品プレビューで向きを確認するもの: 2N7002（Q1/Q2）、1N4148WS・B5819W（カソード帯）、抵抗アレイ。

## 手はんだ（秋月電子で購入）
| 部品 | 秋月 通販コード | 価格 | 位置 |
|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 ×4 | U1（表・下段、CPU 側）、U4（表・上段、CPU 側コプロセッサ）、U2（**裏**・下段、PPU 側）、U5（**裏**・上段、PPU 側コプロセッサ） |
| Seeed XIAO RP2350 | 129619 | ¥1,100 | U3（表・上段右、IRQ と拡張音源） |

- U4・U5 は SFC 型コプロセッサを使うゲーム（自作ソフト）でだけ働く。**載せなくても rev E と同じに動く**（U1・U2 が全部を受け持つ）。
- 裏面の U2・U5 を先に、表面の U1・U4・U3 を後にはんだ付けすると楽。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（2 層・90×70 mm・金フィンガー・ENIG・1.2 mm）: 約 US$ 35–55
- 実装（Economic 片面、Basic のみ）: 5 枚で約 US$ 20–35
- モジュール（秋月）: 1 枚あたり ¥5,060（Pico 2 ×4 + XIAO RP2350）
