# JLCPCB 注文パッケージ（famicart rev E: JLCPCB Basic 部品のみ + 秋月の手はんだモジュール）

> **訂正（2026-11-10）**: 金フィンガー（Gold Fingers）付きの基板は JLCPCB の **Economic PCBA では受け付けられない**
> （PCB Assembly Capabilities の表で Economic は Gold fingers "Not Support"）。**Standard PCBA** で注文する。
> Standard は捨て基板（Edge Rails）とフィデューシャルが必要で、注文画面で **Added by JLCPCB** を選べば JLCPCB が付ける。
> 料金は Economic より高い（セットアップ $25.56、ステンシル $8.21、部品 1 種類ごとに $1.53。2026-10-22 の料金表）。
> この版は rev G に置き換えた（`docs/12_rev_g_plan.md`）。新しく作るなら `hardware/revg/` を使う。

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- **Layers 2** / Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm** / Surface Finish **ENIG**
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented
- Min Track/Spacing 0.15 mm、Via 0.5/0.25 mm（JLC 標準仕様内、追加料金なし）

## SMT Assembly（PCB Assembly → **Standard PCBA / Top side のみ** / Edge Rails・Fiducials: Added by JLCPCB）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`。**全部品が JLCPCB Basic Parts**（`parts_check.csv` に API での確認結果）。Extended 部品の追加料金はかからない。
- 実装しない部品（DNP）: J1, U1, U2, U3, J2
- 部品プレビューで向きを確認するもの: 2N7002（Q1/Q2）、1N4148WS・B5819W（カソード帯）、抵抗アレイ。

## 手はんだ（秋月電子で購入）
| 部品 | 秋月 通販コード | 価格 | 位置 |
|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 | U1（表面、CPU 側）・U2（**裏面**、PPU 側） |
| Seeed XIAO RP2350 | 129619 | ¥1,100 | U3（表面、特殊チップ） |

- Pico 2 はキャステレーション（端面スルーホール）を基板のパッドに直接はんだ付けする。U2 は裏面に載せる。
- XIAO は縁の 14 ピンだけをはんだ付けする（裏面パッドは使わない。基板側にも銅箔を置いていない）。
- 先にファームを書き込んでからはんだ付けすると、BOOTSEL 操作が楽。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（2 層・金フィンガー・ENIG・1.2 mm）: 約 US$ 30–45
- 実装（Standard 片面、Basic のみ 10 種類、約 47 点/枚）: セットアップ $25.56 + ステンシル $8.21 + フィーダー $1.53 × 10 種類 + 実装費 → 5 枚で約 US$ 55 ＋ 部品代
- 基板 1 枚が 70 × 70 mm より小さい（90 × 46.1 mm）ので、Standard PCBA では JLCPCB 側の捨て基板で 70 mm 以上にする必要がある（注文画面の指示に従う）
- モジュール（秋月）: 1 枚あたり ¥3,080（Pico 2 ×2 + XIAO RP2350）
