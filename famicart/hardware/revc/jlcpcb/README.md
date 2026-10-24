# JLCPCB 注文パッケージ（famicart rev C: RP2350B + XIAO RP2040）

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- Layers 2 / Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm** / Surface Finish **ENIG**（金フィンガー必須）
- **Gold Fingers: Yes** → **Bevelling: 30°** / Copper 1 oz / Via Covering: Tented / Min via 0.5/0.25 mm（標準仕様内）
- QFN-80 0.4 mm ピッチ（U1 RP2350B）があるため、Min Track/Spacing は 0.127 mm 以上の標準で問題無い（設計値 0.15/0.15 mm）。

## SMT Assembly（PCB Assembly → Assembly Side: Top + Bottom）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`（両面。裏面は 0402 パスコン・CC 抵抗・LDO コンデンサ・ジャンパ）
- 実装しない部品（DNP）: J1, U8, J4, J2, J5, JP1, JP2
  - U8 Seeed XIAO RP2040 は JLCPCB 在庫無し → Seeed から購入し、受け取り後に 14 個のキャステレーションパッドを手ハンダ（基板上面に裏返して載せる。シルクの白枠と USB-C 向きに合わせる）。
  - J4（RP2350B 専用の予備 USB-C）は標準では DNP。J3 1 本で RP2350B を使う構成が既定。J4 を付ける場合は J3 の D+/D− と並列になるので **J3 と J4 を同時に PC へ挿さない**。
  - J2（RUN/GND リセット端子）と J5（SWD）は 2.54 mm ピンヘッダ。必要なら手ハンダ。
- 部品プレビュー画面で **極性と回転** を必ず確認: U1 RP2350B（1 番ピン・マーク）、U2 W25Q128（1 番ピン）、U3/U6/U7 SOT-23-5、D1/D2 ショットキーのカソード帯、Y1 水晶（GND パッド 2/4）、J3 USB-C。
- U1 RP2350B（C42415655）、U2（C97521）、Y1（C20625731）、L1（C42411119）は拡張部品。在庫切れの場合は BOM の note 欄の代替品に差し替える。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（金フィンガー・ENIG・1.2 mm）: 約 US$ 40–60
- 実装（両面、約 60 点/枚）: セットアップ約 US$ 8 + 部品代（RP2350B 約 US$ 1.5、フラッシュ約 US$ 1.2、ロジック・受動部品 US$ 3–4/枚）＋実装費 → 5 枚で約 US$ 70–100
- 別途 Seeed XIAO RP2040 × 5（約 US$ 5.4/個）
