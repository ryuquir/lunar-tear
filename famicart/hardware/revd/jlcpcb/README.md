# JLCPCB 注文パッケージ（famicart rev D: PRG ROM / CHR ROM / マッパーチップ分離構成）

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- **Layers 6**（F.Cu 信号 / In1 GND プレーン / In2・In3 信号 / In4 +3V3 プレーン / B.Cu 信号）/ Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm**（6 層で 1.2 mm を選択。無い場合は 1.6 mm でもシェルには入るが端子の嵌合がきつくなる）
- Surface Finish **ENIG** / **Gold Fingers: Yes** → **Bevelling: 30°** / Copper 1 oz（外層・内層とも）/ Via Covering: Tented / Impedance Control: No
- 層構成は JLC の標準 6 層スタックで可。**Min Track/Spacing 0.1/0.1 mm（4 mil）、Via 0.5/0.2 mm** — JLC の 6 層仕様（3.5 mil / 0.2 mm 穴）内。

## SMT Assembly（PCB Assembly → Assembly Side: Top + Bottom）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`（両面実装。表: RP2350B x2・水晶・USB-C x2・スイッチ・LDO・単ゲート、裏: NOR フラッシュ x2・F-RAM・SRAM・74LVC541/245/139/00・パスコン）
- 実装しない部品（DNP）: J1, J2, J5, J6, JP1, JP2（スルーホールのピンヘッダ J2/J5/J6 と、部品の無いジャンパ／パッド）
- 部品プレビュー画面で **極性と回転** を必ず確認: U1/U2 RP2350B（1 番ピン）、U5/U6 S29GL01GS（TSOP-56 の 1 番ピン・マーク側）、U7 FM28V100 / U8 IS62WV5128（TSOP-I-32）、U3/U4 W25Q16、U28 AMS1117（タブ = VOUT）、D1/D2 ショットキー、D3 LED、Y1/Y2 水晶、J3/J4 USB-C。
- 拡張部品: U1/U2（C42415655）、U5/U6（C2684783、在庫少。切れている場合は同ピン配置の S29GL512S = C393876 / S29GL128S = C914940 に差し替え可。容量が変わるだけでファームは自動認識）、U7 F-RAM（C66026、約 US$ 11）、U8 SRAM（C1348955）、Y1/Y2（C20625731）、L1/L2（C42411119）。
- 両面実装のため、裏面に TSOP-56 x2 と TSOP-32 x2 が載る。JLC の「Bottom side」実装費が追加になる。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（6 層・金フィンガー・ENIG・1.2 mm）: 約 US$ 110–160
- 実装（両面、約 135 点/枚）: セットアップ約 US$ 25（両面）+ 部品代（S29GL01GS 約 US$ 9 x2、FM28V100 約 US$ 11、IS62WV5128 約 US$ 8、RP2350B 約 US$ 1.5 x2、他 US$ 6–8/枚 → 約 US$ 43/枚）＋実装費 → 5 枚で約 US$ 260–320
