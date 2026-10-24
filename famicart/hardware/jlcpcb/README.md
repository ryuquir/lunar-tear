# JLCPCB 注文パッケージ（famicart rev B）

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- Layers 2 / Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm** / PCB Color 任意 / Surface Finish **ENIG**（金フィンガー必須）
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented / Remove Order Number: Specify a location（任意）
- 確認事項: ガーバーの Edge.Cuts に端子タブの 1 mm 面取りが入っている。JLC 側の面取り（Bevel）はこれとは別にエッジ全体に掛かる。

## SMT Assembly（PCB Assembly → Assembly Side: Top + Bottom）
- BOM: `bom_jlc.csv`  / CPL: `cpl_jlc.csv`（両面。裏面はパスコン・ジャンパのみ）
- 実装しない部品（DNP）: J1, JP3, JP4, W1, J2, JP1, JP2（スルーホールのピンヘッダ J2 と、部品の無いジャンパ／パッド）
- 部品プレビュー画面で **極性と回転** を必ず確認（KiCad と JLCPCB で回転の基準が異なる部品があるため。特に U1 Pico 2・J3 USB-C・SOT-23-5 の 3 点）。
- U1（Pico 2、C41407547）は JLCPCB の拡張部品。在庫が無い場合は DNP にして自分でハンダ付けする（キャステレーションなので手付け可）。
- J3 の USB D+/D− は JP3/JP4（裏面ソルダージャンパ）で割り当てを選ぶ。受け取り後に `docs/04_hardware.md` の手順で確認してブリッジする。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（金フィンガー・ENIG・1.2 mm）: 約 US$ 40–60（金フィンガーのオプション料が主）
- 実装（両面、部品 42 点/枚）: セットアップ約 US$ 8 + 部品代（Pico 2 約 US$ 9.3/枚、他 US$ 3–4/枚）＋実装費 → 5 枚で約 US$ 90–120
