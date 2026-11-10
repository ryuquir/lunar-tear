#!/usr/bin/env python3
"""Produce the JLCPCB order package (PCB + SMT assembly) in hardware/jlcpcb/:
   gerbers.zip, bom_jlc.csv (Comment, Designator, Footprint, LCSC Part #), cpl_jlc.csv (Designator, Mid X, Mid Y, Layer, Rotation).
A board with gold fingers cannot be ordered as "Economic PCBA" (JLCPCB PCB assembly capabilities: gold fingers "Not
Support"); it is a "Standard PCBA" order, which needs edge rails and fiducials (JLCPCB adds both). The README written
next to the files says so and gives the order options and the assembly cost from JLCPCB's price table.
LCSC part numbers: designs with their own LCSC map (rev E on: Basic parts only) use that map and nothing else;
older designs read <hw dir>/jlc_parts.json (created from DEFAULT_PARTS on first run; edit it to substitute parts)."""
import os, sys, csv, json, subprocess, shutil
sys.path.insert(0, os.path.dirname(__file__))
import os as _os, importlib as _il
_DESIGN = _os.environ.get('FC_DESIGN', 'design')
D = _il.import_module(_DESIGN)
HW_LIB = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'hardware'))   # custom symbols/footprints
HW = _os.path.abspath(_os.environ.get('FC_HW_DIR', HW_LIB))                                                        # outputs
OUT = os.path.join(HW, 'jlcpcb'); PCB = os.path.join(HW, 'famicart.kicad_pcb')
PARTS_JSON = os.path.join(HW, 'jlc_parts.json')

# KiCad -> JLCPCB placement angle: JLCPCB's part library draws some packages turned relative to the KiCad footprint.
# Correction in degrees (added to the KiCad angle) by exact footprint name, top side only; checked pad by pad against
# JLCPCB's own footprints for the parts used here (C20197 RES-ARRAY-SMD_0603-8P-...-BL, C8545 SOT-23-3_..._BR).
# The 1k x4 array is four identical isolated resistors, so 90 and 270 are the same placement.
# Do not take SOT-23 from the common "cpl_rotations_db.csv" (-90): that entry does not fit this part.
# The order preview remains the final check.
# SOIC-8 (W25Q128JVSIQ, C97521; rev G): JLCPCB's footprint is named SOIC-8_L5.3-W5.3-P1.27-LS8.0-BL, and by EasyEDA's
# naming rule the -BL token means pin 1 at the bottom left of their drawing, which is 270 for a KiCad SOIC at 0
# (the common rotation tables agree: "^SOIC-" = 270). This one was not compared pad by pad (EasyEDA refused the
# download), so U7's pin 1 is the first thing to look at in the order preview.
CPL_ROT = {'R_Array_Convex_4x0603': 270, 'SOT-23': 180, 'SOIC-8_5.23x5.23mm_P1.27mm': 270}

# JLCPCB "PCB assembly price" (help article, last updated 2026-10-22), Standard PCBA, single-sided, USD
JLC_PRICE = dict(date='2026-10-22', setup=25.56, stencil=8.21, feeder=1.53, joint=0.0016, board=0.48, packing=0.50, confirm=0.45)
def assembly_estimate(types, joints, n):
    """Standard PCBA fees without the parts themselves, a fixture (if JLCPCB quotes one), shipping and tax.
    The per-joint fee has a floor of $0.48 per board ("single board assembly surcharge")."""
    P = JLC_PRICE
    return P['setup'] + P['stencil'] + P['feeder'] * types + max(P['joint'] * joints, P['board']) * n + P['packing'] + P['confirm']
# files that go into gerbers.zip for designs made to JLCPCB's rules: the fabrication layers and the drill files only
# (the F.Fab / B.Fab plots are drawings for people; a fab note on them must not reach the order)
FAB_SUFFIX = ('_Cu.gtl', '_Cu.gbl', '_Cu.g2', '_Cu.g3', '_Cu.g4', '_Cu.g5', '_Paste.gtp', '_Paste.gbp', '_Silkscreen.gto', '_Silkscreen.gbo',
              '_Mask.gts', '_Mask.gbs', '-Edge_Cuts.gm1', '.drl')

DEFAULT_PARTS = {   # value-key [or "value@pkg"] -> (LCSC, comment, note)   (looked up via the JLCPCB parts API, 2026-10)
 # ---- rev B (Pico 2 module) ----
 'Raspberry Pi Pico 2': ('C41407547', 'Raspberry Pi Pico 2', 'extended part, stock ~450; JLCPCB can place the module on the castellated pads'),
 # ---- shared ----
 '74LVC541': ('C113281', 'SN74LVC541APWR', 'TI; alt Nexperia 74LVC541APW,118 = C6093'),
 '74LVC245': ('C6082', '74LVC245APW,118', 'Nexperia; alt TI SN74LVC245APWR = C7848'),
 '74LVC139': ('C7662', 'SN74LVC139APWR', 'TI; alt Nexperia 74LVC139PW,118 = C672267'),
 '74LVC1G17': ('C7836', 'SN74LVC1G17DBVR', 'TI'), '74LVC1G08': ('C7666', 'SN74LVC1G08DBVR', 'TI'), '74LVC1G07': ('C7829', 'SN74LVC1G07DBVR', 'TI'),
 '74LVC1G04': ('C7827', 'SN74LVC1G04DBVR', 'TI'),
 '2.2k': ('C4190', '2.2kΩ 0603 1%', 'basic'), '4.7k': ('C23162', '4.7kΩ 0603 1%', 'basic'), '1k': ('C21190', '1kΩ 0603 1%', 'basic'),
 '10k': ('C25804', '10kΩ 0603 1%', 'basic'), '5.1k': ('C23186', '5.1kΩ 0603 1%', 'basic'), '27': ('C25190', '27Ω 0603 1%', 'basic'),
 '33@0402': ('C25105', '33Ω 0402 1%', 'basic'), '1k@0402': ('C11702', '1kΩ 0402 1%', 'basic'),
 '100n': ('C14663', '100nF 50V X7R 0603', 'basic'), '100n@0402': ('C1525', '100nF 16V X7R 0402', 'basic'),
 '10n': ('C100042', '10nF 50V X7R 0603', 'extended'), '10u': ('C380332', '10uF 16V X5R 0805', 'extended'),
 '1u': ('C1592', '1uF 16V X7R 0603', 'extended'), '4.7u': ('C1705', '4.7uF 10V X5R 0603', 'extended'), '15p@0402': ('C1644', '15pF 50V C0G 0402', 'basic'),
 'USB-C': ('C165948', 'TYPE-C-31-M-12', 'Korean Hroparts, matches the KiCad footprint'),
 'USB-C DATA': ('C165948', 'TYPE-C-31-M-12', 'Korean Hroparts, matches the KiCad footprint'),
 'USB-C RP2350': ('', 'TYPE-C-31-M-12 (C165948)', 'DNP by default: optional second connector for the RP2350B (parallel to J3; fit only one of J3/J4 wired to the RP2350B)'),
 'RESET': ('C2886898', 'TL3342F160QG', 'E-Switch; alt basic part TS-1187A-B-A-B = C318884 (different footprint)'),
 'BOOTSEL': ('C2886898', 'TL3342F160QG', 'E-Switch'),
 'RUN/GND': ('', '2.54 mm 1x2 header', 'DNP: through-hole, solder by hand if you want the console-reset wire'),
 'SWD': ('', '2.54 mm 1x3 header', 'DNP: through-hole debug header'),
 'Famicom 60-pin edge': ('', '', 'PCB feature'), 'AUDIO bypass': ('', '', 'solder jumper'), 'CART_PRESENT': ('', '', 'solder jumper'),
 'USB D+ -> TP_A | TP_B': ('', '', 'solder jumper'), 'USB D- -> TP_B | TP_A': ('', '', 'solder jumper'), 'TP wire pads': ('', '', 'pads only'),
 # ---- rev C (bare RP2350B + XIAO RP2040) ----
 'RP2350B': ('C42415655', 'RP2350B', 'Raspberry Pi, QFN-80; extended part'),
 'W25Q128JVSIQ': ('C97521', 'W25Q128JVSIQ', 'Winbond 16 MB QSPI flash, SOIC-8 208 mil'),
 'AP2112K-3.3': ('C51118', 'AP2112K-3.3TRG1', 'Diodes Inc 600 mA LDO, SOT-23-5'),
 'Seeed XIAO RP2040': ('', 'Seeed Studio XIAO RP2040', 'DNP: not stocked at JLCPCB; buy from Seeed and solder the 14 castellated pads yourself'),
 '12MHz ABM8-272-T3': ('C20625731', 'ABM8-272-T3', 'Abracon 12 MHz 3225 (the crystal Raspberry Pi uses on Pico 2); alt X322512MSB4SI = C9002'),
 '3.3uH AOTA-B201610S3R3': ('C42411119', 'AOTA-B201610S3R3-101-T', '3.3 uH 0806 (2016) power inductor for the RP2350 core regulator; alt CKCSA201610-3.3uH = C5125966'),
 'B5819W': ('C64885', 'B5819W', 'MDD 1 A 40 V Schottky, SOD-123'),
 # ---- rev D (split PRG / CHR / mapper chips) ----
 'S29GL01GS 1Gbit NOR': ('C2684783', 'S29GL01GS10TFI010', 'Infineon 1 Gbit (64M x 16) parallel NOR, TSOP-56, 100 ns; used as 64M x 8. Alt: S29GL512S10TFI010 = C393876 (64 MB), S29GL128S10TFI010 = C914940 (16 MB) -- same pinout'),
 'FM28V100 128Kx8 F-RAM': ('C66026', 'FM28V100-TGTR', 'Infineon/Cypress 1 Mbit parallel F-RAM, 32-pin TSOP-I (8 x 13.4 mm); non-volatile save RAM, no battery'),
 'IS62WV5128 512Kx8 SRAM': ('C1348955', 'IS62WV5128EBLL-45HLI', 'ISSI 512K x 8 SRAM 3.3 V 45 ns, 32-pin sTSOP (package H)'),
 'AMS1117-3.3': ('C6186', 'AMS1117-3.3', 'basic part, SOT-223, 1 A LDO'),
 'W25Q16JVSSIQ': ('C131025', 'W25Q16JVSSIQ', 'Winbond 2 MB QSPI flash for the RP2350B firmware (same footprint/pinout as W25Q128)'),
 '74LVC00 PPU access / CIRAM glue': ('C7803', 'SN74LVC00APWR', 'TI quad NAND, TSSOP-14'),
 '74LVC139 CHR ROM/RAM select': ('C7662', 'SN74LVC139APWR', 'TI'),
 '74LVC1G11 AND3: CPU data enable': ('C460526', '74LVC1G11W6-7', 'Diodes Inc, SOT-26 (= SOT-23-6)'),
 '74LVC1G32 OR: CPU 245 /OE': ('C10096', 'SN74LVC1G32DBVR', 'TI'), '74LVC1G32 OR: PPU 245 /OE': ('C10096', 'SN74LVC1G32DBVR', 'TI'),
 '74LVC1G04 INV: R/W': ('C7827', 'SN74LVC1G04DBVR', 'TI'), '74LVC1G00 NAND: WRAM /WE': ('C7826', 'SN74LVC1G00DBVR', 'TI'),
 '74LVC1G07 OD: /IRQ A': ('C7829', 'SN74LVC1G07DBVR', 'TI'), '74LVC1G07 OD: /IRQ B': ('C7829', 'SN74LVC1G07DBVR', 'TI'),
 '10k x4': ('C29718', '4D03WGJ0103T5E 10k x4 0603', 'basic'), 'green 0603': ('C84267', 'NCD0603G1 0603 green LED', 'extended, large stock'),
 'RESET': ('C2886898', 'TL3342F160QG', 'E-Switch'), 'BOOTSEL A': ('C2886898', 'TL3342F160QG', 'E-Switch'), 'BOOTSEL B': ('C2886898', 'TL3342F160QG', 'E-Switch'),
 'B5819W (VBUS A->+5V)': ('C64885', 'B5819W', 'MDD'), 'B5819W (VBUS B->+5V)': ('C64885', 'B5819W', 'MDD'),
 'USB-C PRG/mapper': ('C165948', 'TYPE-C-31-M-12', 'Korean Hroparts'), 'USB-C CHR': ('C165948', 'TYPE-C-31-M-12', 'Korean Hroparts'),
 'RUN/GND': ('', '2.54 mm 1x2 header', 'DNP: solder by hand if you want an external reset switch'),
 'SWD A (SWCLK GND SWDIO)': ('', '2.54 mm 1x3 header', 'DNP'), 'SWD B (SWCLK GND SWDIO)': ('', '2.54 mm 1x3 header', 'DNP'),
}

README_B = '''# JLCPCB 注文パッケージ（famicart rev B）

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- Layers 2 / Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm** / PCB Color 任意 / Surface Finish **ENIG**（金フィンガー必須）
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented / Remove Order Number: Specify a location（任意）
- 確認事項: ガーバーの Edge.Cuts に端子タブの 1 mm 面取りが入っている。JLC 側の面取り（Bevel）はこれとは別にエッジ全体に掛かる。

## SMT Assembly（PCB Assembly → Assembly Side: Top + Bottom）
- BOM: `bom_jlc.csv`  / CPL: `cpl_jlc.csv`（両面。裏面はパスコン・ジャンパのみ）
- 実装しない部品（DNP）: @DNP@（スルーホールのピンヘッダ J2 と、部品の無いジャンパ／パッド）
- 部品プレビュー画面で **極性と回転** を必ず確認（KiCad と JLCPCB で回転の基準が異なる部品があるため。特に U1 Pico 2・J3 USB-C・SOT-23-5 の 3 点）。
- U1（Pico 2、C41407547）は JLCPCB の拡張部品。在庫が無い場合は DNP にして自分でハンダ付けする（キャステレーションなので手付け可）。
- J3 の USB D+/D− は JP3/JP4（裏面ソルダージャンパ）で割り当てを選ぶ。受け取り後に `docs/04_hardware.md` の手順で確認してブリッジする。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（金フィンガー・ENIG・1.2 mm）: 約 US$ 40–60（金フィンガーのオプション料が主）
- 実装（両面、部品 42 点/枚）: セットアップ約 US$ 8 + 部品代（Pico 2 約 US$ 9.3/枚、他 US$ 3–4/枚）＋実装費 → 5 枚で約 US$ 90–120
'''

README_C = '''# JLCPCB 注文パッケージ（famicart rev C: RP2350B + XIAO RP2040）

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- Layers 2 / Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm** / Surface Finish **ENIG**（金フィンガー必須）
- **Gold Fingers: Yes** → **Bevelling: 30°** / Copper 1 oz / Via Covering: Tented / Min via 0.5/0.25 mm（標準仕様内）
- QFN-80 0.4 mm ピッチ（U1 RP2350B）があるため、Min Track/Spacing は 0.127 mm 以上の標準で問題無い（設計値 0.15/0.15 mm）。

## SMT Assembly（PCB Assembly → Assembly Side: Top + Bottom）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`（両面。裏面は 0402 パスコン・CC 抵抗・LDO コンデンサ・ジャンパ）
- 実装しない部品（DNP）: @DNP@
  - U8 Seeed XIAO RP2040 は JLCPCB 在庫無し → Seeed から購入し、受け取り後に 14 個のキャステレーションパッドを手ハンダ（基板上面に裏返して載せる。シルクの白枠と USB-C 向きに合わせる）。
  - J4（RP2350B 専用の予備 USB-C）は標準では DNP。J3 1 本で RP2350B を使う構成が既定。J4 を付ける場合は J3 の D+/D− と並列になるので **J3 と J4 を同時に PC へ挿さない**。
  - J2（RUN/GND リセット端子）と J5（SWD）は 2.54 mm ピンヘッダ。必要なら手ハンダ。
- 部品プレビュー画面で **極性と回転** を必ず確認: U1 RP2350B（1 番ピン・マーク）、U2 W25Q128（1 番ピン）、U3/U6/U7 SOT-23-5、D1/D2 ショットキーのカソード帯、Y1 水晶（GND パッド 2/4）、J3 USB-C。
- U1 RP2350B（C42415655）、U2（C97521）、Y1（C20625731）、L1（C42411119）は拡張部品。在庫切れの場合は BOM の note 欄の代替品に差し替える。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（金フィンガー・ENIG・1.2 mm）: 約 US$ 40–60
- 実装（両面、約 60 点/枚）: セットアップ約 US$ 8 + 部品代（RP2350B 約 US$ 1.5、フラッシュ約 US$ 1.2、ロジック・受動部品 US$ 3–4/枚）＋実装費 → 5 枚で約 US$ 70–100
- 別途 Seeed XIAO RP2040 × 5（約 US$ 5.4/個）
'''

README_D = '''# JLCPCB 注文パッケージ（famicart rev D: PRG ROM / CHR ROM / マッパーチップ分離構成）

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- **Layers 6**（F.Cu 信号 / In1 GND プレーン / In2・In3 信号 / In4 +3V3 プレーン / B.Cu 信号）/ Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm**（6 層で 1.2 mm を選択。1.6 mm で使えるかは未確認）
- Surface Finish **ENIG** / **Gold Fingers: Yes** → **Bevelling: 30°** / Copper 1 oz（外層・内層とも）/ Via Covering: Tented / Impedance Control: No
- 層構成は JLC の標準 6 層スタックで可。**Min Track/Spacing 0.1/0.1 mm（4 mil）、Via 0.5/0.2 mm** — JLC の 6 層仕様（3.5 mil / 0.2 mm 穴）内。

## SMT Assembly（PCB Assembly → Assembly Side: Top + Bottom）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`（両面実装。表: RP2350B x2・水晶・USB-C x2・スイッチ・LDO・単ゲート、裏: NOR フラッシュ x2・F-RAM・SRAM・74LVC541/245/139/00・パスコン）
- 実装しない部品（DNP）: @DNP@（スルーホールのピンヘッダ J2/J5/J6 と、部品の無いジャンパ／パッド）
- 部品プレビュー画面で **極性と回転** を必ず確認: U1/U2 RP2350B（1 番ピン）、U5/U6 S29GL01GS（TSOP-56 の 1 番ピン・マーク側）、U7 FM28V100 / U8 IS62WV5128（TSOP-I-32）、U3/U4 W25Q16、U28 AMS1117（タブ = VOUT）、D1/D2 ショットキー、D3 LED、Y1/Y2 水晶、J3/J4 USB-C。
- 拡張部品: U1/U2（C42415655）、U5/U6（C2684783、在庫少。切れている場合は同ピン配置の S29GL512S = C393876 / S29GL128S = C914940 に差し替え可。容量が変わるだけでファームは自動認識）、U7 F-RAM（C66026、約 US$ 11）、U8 SRAM（C1348955）、Y1/Y2（C20625731）、L1/L2（C42411119）。
- 両面実装のため、裏面に TSOP-56 x2 と TSOP-32 x2 が載る。JLC の「Bottom side」実装費が追加になる。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（6 層・金フィンガー・ENIG・1.2 mm）: 約 US$ 110–160
- 実装（両面、約 135 点/枚）: セットアップ約 US$ 25（両面）+ 部品代（S29GL01GS 約 US$ 9 x2、FM28V100 約 US$ 11、IS62WV5128 約 US$ 8、RP2350B 約 US$ 1.5 x2、他 US$ 6–8/枚 → 約 US$ 43/枚）＋実装費 → 5 枚で約 US$ 260–320
'''

README_E = '''# JLCPCB 注文パッケージ（famicart rev E: JLCPCB Basic 部品のみ + 秋月の手はんだモジュール）

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
- 実装しない部品（DNP）: @DNP@
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
'''

README_F = '''# JLCPCB 注文パッケージ（famicart rev F: rev E + SFC 型コプロセッサ用 Pico 2 ×2、Basic 部品のみ）

> **訂正（2026-11-10）**: 金フィンガー（Gold Fingers）付きの基板は JLCPCB の **Economic PCBA では受け付けられない**
> （PCB Assembly Capabilities の表で Economic は Gold fingers "Not Support"）。**Standard PCBA** で注文する。
> Standard は捨て基板（Edge Rails）とフィデューシャルが必要で、注文画面で **Added by JLCPCB** を選べば JLCPCB が付ける。
> 料金は Economic より高い（セットアップ $25.56、ステンシル $8.21、部品 1 種類ごとに $1.53。2026-10-22 の料金表）。
> この版は rev G に置き換えた（`docs/12_rev_g_plan.md`）。新しく作るなら `hardware/revg/` を使う。

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- **Layers 2** / Dimensions **90 x 70.1 mm**（本体 59.4 mm + 端子タブ 10.7 mm）/ **PCB Thickness 1.2 mm** / Surface Finish **ENIG**
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented
- Min Track/Spacing 0.15 mm、Via 0.5/0.25 mm（JLC 標準仕様内、追加料金なし）
- 純正シェルには入らない（上に 24 mm 長い）。ファミコンのスロットは上が開いているので基板のまま挿せる。外装が要るなら 3D プリントで。

## SMT Assembly（PCB Assembly → **Standard PCBA / Top side のみ** / Edge Rails・Fiducials: Added by JLCPCB）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`。**全部品が JLCPCB Basic Parts**（`parts_check.csv` に API での確認結果）。
- 実装しない部品（DNP）: @DNP@
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
- 実装（Standard 片面、Basic のみ 10 種類）: セットアップ $25.56 + ステンシル $8.21 + フィーダー $1.53 × 10 種類 + 実装費 → 5 枚で約 US$ 55 ＋ 部品代
- モジュール（秋月）: 1 枚あたり ¥5,060（Pico 2 ×4 + XIAO RP2350）
'''

README_F2 = '''# JLCPCB 注文パッケージ（famicart rev F2: 任天堂の大型カセットシェル用、Basic 部品のみ）

> **訂正（2026-11-10）**: 金フィンガー（Gold Fingers）付きの基板は JLCPCB の **Economic PCBA では受け付けられない**
> （PCB Assembly Capabilities の表で Economic は Gold fingers "Not Support"）。**Standard PCBA** で注文する。
> Standard は捨て基板（Edge Rails）とフィデューシャルが必要で、注文画面で **Added by JLCPCB** を選べば JLCPCB が付ける。
> 料金は Economic より高い（セットアップ $25.56、ステンシル $8.21、部品 1 種類ごとに $1.53。2026-10-22 の料金表）。
> この版は rev G に置き換えた（`docs/12_rev_g_plan.md`）。新しく作るなら `hardware/revg/` を使う。

回路は rev F と同じ（Pico 2 ×4 + XIAO RP2350）。外形・切り欠き・スリットを任天堂の大型シェル（HVC-ExROM 系。光栄・エニックス・
スクウェアの大型カセット、市販の互換「でかカセットケース」）に合わせ、シェルのリブとボスを避けて部品を置いた版。

**シェルへの収まりは実物では未確認**。外形と部品禁止域は 4 つの資料（互換基板と作図）から作ったもので、シェル内の厚み方向の余裕は
どの資料にもない。最初の注文は少数にして、モジュールをはんだ付けする前に基板だけをシェルに入れて確かめること。

## PCB（Instant Quote → Add gerber file → gerbers.zip）
- **Layers 2** / Dimensions **90 x 85.7 mm**（本体 75.0 mm + 端子タブ 10.7 mm）/ **PCB Thickness 1.2 mm** / Surface Finish **ENIG**
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented
- 外形に**左右の切り欠きと内部スリット（5.4 × 2.4 mm）**がある。ガーバーの Edge_Cuts にそのまま入っているので追加指定は不要。
- Min Track/Spacing 0.15 mm、Via 0.5/0.25 mm（JLC 標準仕様内、追加料金なし）

## SMT Assembly（PCB Assembly → **Standard PCBA / Top side のみ** / Edge Rails・Fiducials: Added by JLCPCB）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`。**全部品が JLCPCB Basic Parts**（`parts_check.csv` に API での確認結果）。
- 実装しない部品（DNP）: @DNP@
- CPL の角度は JLCPCB の部品ライブラリの向きに合わせて補正済み: **抵抗アレイ RN1〜RN16 = 270°、2N7002 Q1/Q2 = 180°**（KiCad 上は 0°）。
  それでも注文画面の部品プレビューで、Q1/Q2、1N4148WS・B5819W（カソード帯）、抵抗アレイ、SW1 がパッドに重なっているかを確認する。

## 手はんだ（秋月電子で購入）
| 部品 | 秋月 通販コード | 価格 | 位置 | 書き込むファーム |
|---|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 ×4 | **裏**: U2（下、PPU 側）・U5（中、PPU 側コプロセッサ）・U1（上、CPU 側）／**表**: U4（上、CPU 側コプロセッサ） | U1 `reve_cpu`、U2 `reve_ppu`、U4 `reve_cop_cpu`、U5 `reve_cop_ppu` |
| Seeed XIAO RP2350 | 129619 | ¥1,100 | 表・中央右（U3、IRQ と拡張音源） | U3 `reve_x` |

- 4 枚の Pico 2 は見た目が同じでファームが違う。基板のシルクに `U1 reve_cpu` のように書いてあるので、**書き込んでから**その場所に載せる。
  シルクの `USB` の字がある側にモジュールの USB 端子を向ける。
- Pico 2 はキャステレーション（端面）40 か所だけをはんだ付けする。モジュール裏のテストパッドと USB シェルの足の下にある基板側のパッド
  （配線よけ。はんだペーストなし）は、はんだ付けしない。
- 裏の 3 枚を先に、表の U4・XIAO を後にはんだ付けすると楽。U4・U5 は載せなくても rev E と同じに動く。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（2 層・90×86 mm・金フィンガー・ENIG・1.2 mm）: 約 US$ 40–60
- 実装（Standard 片面、Basic のみ 10 種類）: セットアップ $25.56 + ステンシル $8.21 + フィーダー $1.53 × 10 種類 + 実装費 → 5 枚で約 US$ 55 ＋ 部品代
- モジュール（秋月）: 1 枚あたり ¥5,060（Pico 2 ×4 + XIAO RP2350）
- シェル: 任天堂の大型カセットの中古シェル、または互換の「でかカセットケース」
'''

README_G = '''# JLCPCB 注文パッケージ（famicart rev G: 任天堂の大型カセットシェル用、Basic 部品のみ）

Pico 2 ×2 + XIAO RP2350 ×2 が基本構成、Pico 2 ×2 は増設用（載せなくても動く）。16 MB の SPI フラッシュを載せ、microSD
ソケットは任意。回路と配置の説明は `docs/12_rev_g_plan.md`。

**状態**: 設計レビューの指摘を反映した版で、**実機では未検証**。rev G 用のファームウェアはまだ無い（ピン配置と一部の信号の
極性が rev F と違う。`docs/12_rev_g_plan.md` の作業一覧）。**シェルへの収まりも実物では未確認**なので、最初の注文は最少枚数にして、
モジュールをはんだ付けする前に基板だけをシェルに入れて確かめること。

## 1. 注文の種類
- 金フィンガー付きの基板は **Economic PCBA では受け付けられない**（JLCPCB の実装仕様表で Gold fingers は Economic "Not Support"、
  Standard "Support"）。**Standard PCBA** で注文する。
- Standard PCBA は捨て基板（Edge Rails）とフィデューシャルが必須。注文画面で **Added by JLCPCB** を選ぶと JLCPCB が付ける
  （基板には置いていない）。捨て基板は付いたまま届くので、受け取ってから外す。
- **捨て基板は左右だけに付けてもらう**（下の Remark で指定）。JLCPCB の金フィンガーの説明に「V カットで面付けした基板は、端子が
  面付けの内側に来るので面取りできない」とある。端子の辺（下）に捨て基板が付くと面取りができなくなるので、この基板は左右の端を
  それぞれ 1 本の直線にして、捨て基板を左右に付けられるようにしてある。面取りと捨て基板を同時に頼めるかどうかは JLCPCB のページに
  明記が無いので、**注文後の確認（エンジニアからの連絡）で「面取りはできない」と言われたら、面取り無しで作ってもらい**、
  受け取ってから端子の辺を手で面取りする（6 章）。捨て基板を上下に移す提案は断る。
- 実装は表面（Top）だけ。全部品が JLCPCB Basic Parts（@TYPES@ 種類・@PARTS@ 点/枚。在庫と区分は `parts_check.csv`）。

## 2. PCB の指定（Instant Quote → Add gerber file → `gerbers.zip`）
| 項目 | 指定 |
|---|---|
| Base Material / Layers | FR-4 / 2 |
| Dimensions | @SIZE@ mm（ガーバーから自動で入る。本体 75.0 mm + 端子タブ 10.7 mm）|
| PCB Qty | 5（最少）|
| PCB Thickness | **1.2 mm** |
| Surface Finish | **ENIG**、Gold Thickness は **2 U"**（約 0.05 µm。1 U" は約 0.025 µm。端子が擦れるので厚いほう）|
| Gold Fingers | **Yes**、Bevelling **30°**（ENIG を選んだときだけ端子が金になる。HASL を選ぶと端子ははんだ〔錫〕になる）|
| Outer Copper Weight | 1 oz |
| Via Covering | Tented |
| Min via hole size/diameter | 0.3 mm の標準のまま（設計値: 穴 0.3 mm・径 0.5 mm）|
| Board Outline Tolerance | ±0.2 mm（Regular）|
| Mark on PCB | Order Number (Specify Position)。裏面シルクの `JLCJLCJLCJLC` の位置に注文番号が入る |

PCB Remark（そのまま貼る）:

> Edge rails for assembly: LEFT and RIGHT sides only (both side edges are straight lines for this purpose).
> The bottom side is the gold-finger card edge: please keep it on the outer edge so that the 30 degree bevel can be made.
> If the bevel cannot be combined with the edge rails, make the boards WITHOUT bevel and keep the rails on the left and right.
> Please keep the two side notches, the inner slot and the rounded inner corners (R0.5 mm) as drawn.

**端子の金について**: JLCPCB の金フィンガーは ENIG（無電解ニッケル 3〜6 µm の上に置換金 0.05〜0.1 µm）で、抜き差しの多い
コネクタ用の硬質金めっき（電解めっき、0.5〜1.5 µm）ではない。JLCPCB は硬質金めっきを扱っていない（同社の記事に明記。表面処理は
HASL・ENIG・OSP）。同じ記事は、ENIG の金は数十回の抜き差しで減り、硬質金は 500〜1000 回以上もつ、としている（出典のない目安）。
このカセットは挿したまま使うのが前提で、ゲームの入れ替えは USB か microSD で行う。金が減っても下のニッケルで導通はするが、
接触が不安定になったら端子を無水アルコールで拭く。

## 3. PCB Assembly の指定
| 項目 | 指定 |
|---|---|
| PCBA Type | **Standard** |
| Assembly Side | Top Side |
| PCBA Qty | 2 または 5 |
| Edge Rails/Fiducials | **Added by JLCPCB** |
| Confirm Parts Placement | Yes（部品の向きを製造前に画面で確認できる）|
| BOM / CPL | `bom_jlc.csv` / `cpl_jlc.csv` |

- 実装しない部品（手はんだ・基板パターン）: @DNP@
- CPL の角度は JLCPCB の部品ライブラリの向きに合わせて補正済み: **抵抗アレイ = 270°、SOT-23（2N7002・BAV99）= 180°、U7（SOIC-8）= 270°**（KiCad 上は 0°）。
  JLCPCB は自社の部品ライブラリ（LCSC 番号ごとの EasyEDA のフットプリント）を CPL の角度で回して置く。全 @TYPES@ 種類について、その
  フットプリントを取り寄せて KiCad のフットプリントとパッド番号単位で突き合わせ、CPL の全行が合っていることを確かめてある
  （`tools/pcb/check_cpl.py`。結果は `cpl_check.csv`）。SOT-23 = 180°、SOIC = 270°、アレイ = 90°（270° と同じ結果）は、KiBot の補正表とも一致する。
- それでも**部品プレビューでは、U7 の 1 番ピン（丸印）が基板のシルクの印と同じ角にあること、2N7002・BAV99（@CLAMPS@）の 1 本足の側が
  パッド 1 個の側にあること、B5819W のカソード帯がシルクの帯と同じ側にあること**を見る（JLCPCB のライブラリは部品ごとに変わりうる）。

## 4. 費用（JLCPCB の料金表 @PRICEDATE@ 更新分から計算。部品代・送料・税は別）
| | 2 枚実装 | 5 枚実装 |
|---|---|---|
| 実装費（Standard・片面） | 約 US$ @EST2@ | 約 US$ @EST5@ |

- 内訳: セットアップ $25.56 + ステンシル $8.21 + フィーダー $1.53 × @TYPES@ 種類 + はんだ付け $0.0016 × @JOINTS@ 接点 × 枚数
  （1 枚あたり最低 $0.48）+ 梱包 $0.50 + 配置確認 $0.45。**部品の種類が 1 つ増えるごとに $1.53** かかる。
- 治具（Fixture）費が見積もりに加わることがある（料金表では 1 個 $8.21、29 枚以下は 2 個。どの注文に掛かるかは料金表に書かれていない）。
- 捨て基板を JLCPCB に外してもらう場合は追加の加工費がかかる（金額は料金表に無い。注文時に依頼する）。
- PCB 代は見積もり画面の表示による（ENIG・金フィンガー・1.2 mm を選ぶので、標準の基板より高い）。
- モジュール（秋月）: 基本構成 ¥4,180（Pico 2 ×2 + XIAO RP2350 ×2）、増設の Pico 2 は 1 枚 ¥990、microSD ソケット ¥150。

## 5. JLCPCB の製造条件との照合
| 項目 | この基板 | JLCPCB の条件 |
|---|---|---|
| 基板サイズ | @SIZE@ mm | Standard PCBA は 70 × 70 mm 以上。金フィンガーは 50 × 50 mm 以上 |
| 材質・板厚 | FR-4、1.2 mm | FR-4 は 0.4〜2.0 mm（1.2 mm あり）|
| 表面処理・端子 | ENIG、金フィンガー、30° 面取り。端子の銅は基板端の 1.0 mm 以上手前で終わる | 端子の金は ENIG。面取りは 30° か 45°。面取りする範囲に銅を置かない |
| 端子部のレジスト | タブの付け根から 4.0 mm より先（配線を置かない範囲）は、表裏とも端子の間を含めて全面開口 | 金フィンガーの範囲はレジストを全面開口にする（残すと抜き差しで剥がれる）|
| 端子の近く | ビアは端子から 1.0 mm 以上離す。シルクは無い | めっき穴・SMD パッドは金フィンガーから 1.0 mm 以上。端子の近くにレジスト・シルクを置かない（同社の記事の指針）|
| 面取りと面付け | 捨て基板は左右。端子の辺は面付けの外周に出る | V カットの面付けで端子が内側に来ると面取りできない |
| 配線幅 / 間隔 | @TRACK@ / @CLEAR@ mm | 0.10 / 0.10 mm 以上（2 層・1 oz）|
| ビア | 径 @VIA@ mm、穴 @VDR@ mm | 穴 0.3 mm 以上が標準（それより小さい穴は割高）。径は穴 + 0.1 mm 以上（推奨 + 0.15 mm）|
| 穴と穴 / 穴と配線 | 0.25 mm 以上 / 0.2 mm 以上 | 0.2 mm 以上 / 0.2 mm 以上 |
| 銅箔と基板端 | 0.3 mm 以上。捨て基板が付く左右の端は 0.4 mm 以上 | ルーター加工の端 0.2 mm 以上、V カットの端 0.4 mm 以上 |
| スリット・切り欠き | 幅 2.4 mm。内側の角は R0.5 mm で作図 | 非めっきスリットは幅 1.0 mm 以上。角に丸みの無い角穴・スリットは作れない |
| 外形の公差 | 切り欠きの奥行きとスリットの長さに 0.6 mm、左右の端に 0.2 mm の逃げ | ルーター加工 ±0.2 mm、V カット ±0.4 mm |
| シルク | 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上 | 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上 |
| レジスト | パッド間のレジストは 0.3 mm 以上 | 0.10 mm 以上（黒・白は 0.13 mm）|
| 実装 | 表面のみ、Basic Parts のみ | Standard PCBA は片面・両面とも可 |
| はんだペースト | 手はんだ部品のパッドには置いていない | ステンシルの開口は実装する部品のパッドだけに作られる |

ガーバーの ZIP には製造に使う層（銅箔・レジスト・シルク・ペースト・外形）とドリルだけを入れてある。

## 6. 受け取ってから
1. 捨て基板を外す（V カットは折る。ミシン目は切って、残った突起をやすりで落とす）。左右の端面をやすりで平らにする。
   面取り無しで届いた場合は、端子の辺の角を表裏とも 30〜45° の角度で 0.3〜0.5 mm ほど、目の細かいやすりで落とす
   （端子の銅は端から 1.0 mm 手前で終わっているので、金には触れない）。角が立ったままだと本体のコネクタの接点を傷める。
2. **基板だけ**をシェルに入れて、左右の切り欠き・スリット・端子タブの位置を確かめる。タブの付け根など、内側の角に残る丸みが
   シェルに当たる場合は、やすりで落とす。
   あわせて、**基板の表・裏それぞれからシェルの内壁までの隙間**を測る（ノギスの深さ測定か、粘土を挟んで閉じる）。この寸法は
   どの資料にも無かった。必要な高さの目安（基板の厚み＋コネクタの一般的な寸法からの見積もりで、実測ではない）:
   **表（ラベル面）** = XIAO（U3・U6）約 4.5 mm、増設の Pico 2（U4）約 3.8 mm、microSD ソケット約 2 mm、実装済みの部品は最大約 2.2 mm（U7）。
   **裏** = Pico 2（U1・U2・U5）約 3.8 mm。任天堂の純正基板は背の高い部品を裏（31〜60 番の面）に載せているので、表のほうが狭い
   可能性がある。表の隙間が XIAO に足りない場合、この版ではシェルの表側を閉じられない（表側のシェルの内側を削るか、開けたまま
   使い、次の版で XIAO を裏に移す）。動作には影響しない。
3. モジュールにファームを書き込んでから、はんだ付けする。裏面（U2 → U1、増設するなら U5）を先に、表面（U3・U6、増設するなら U4、
   使うなら J3）を後に。基板のシルクに `U1 cpu` のように役割が書いてある。シルクの `USB` の字がある側にモジュールの USB 端子を向ける。
4. Pico 2 は端面（キャステレーション）40 か所だけをはんだ付けする。XIAO は縁の 14 ピンだけ（裏面パッドは使わない）。
5. XIAO の 5V ピンは USB の VBUS と直結している。**本体の電源が入っている間は、電源の入っていない PC やハブに U3・U6 の USB を
   つながない**（本体の 5 V が USB ケーブル側へ出る）。

## 7. 手はんだ部品（秋月電子）
| 部品 | 秋月 通販コード | 価格 | 位置 |
|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 ×2（＋増設 ×2）| **裏**: U2（下、PPU 側）・U1（上、CPU 側）・U5（中、PPU 側の増設）／**表**: U4（上、CPU 側の増設）|
| Seeed XIAO RP2350 | 129619 | ¥1,100 ×2 | **表**: U3（中央右、IRQ・拡張音源・ネームテーブル制御）・U6（上、ハブ: SFC チップ機能・保存・更新）|
| microSD ソケット Hirose DM3AT-SF-PEJM5 | 102395 | ¥150（任意）| **表**: J3（右上）|

## 出典（JLCPCB 公式、2026-11-10 に確認）
- 実装仕様（Economic / Standard の違い、金フィンガー、基板サイズ）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- 基板の製造仕様（配線・ビア・外形・スリット・シルク・レジスト）: https://jlcpcb.com/capabilities/pcb-capabilities
- 追加料金になる場合（小径穴ほか）: https://jlcpcb.com/help/article/In-what-cases-will-there-be-charged-extra
- 金フィンガーと面取り（2026-09-18 更新。面取りの角度、V カット面付けでは面取り不可、端子部のレジスト全面開口）: https://jlcpcb.com/help/article/jlcpcb-gold-fingers 、 https://jlcpcb.com/blog/considerations-for-gold-finger-bevel-design
- 金フィンガーの設計の指針（めっき穴・パッドは端子から 1.0 mm 以上、端子の近くにレジスト・シルクを置かない）: https://jlcpcb.com/blog/pcb-gold-fingers
- 面付けと V カットの条件: https://jlcpcb.com/help/article/pcb-panelization
- 硬質金めっきと ENIG の違い、JLCPCB が硬質金を扱わないこと（2026-08-08 更新の記事）: https://jlcpcb.com/blog/hard-gold-pcb-finish
- 捨て基板とフィデューシャル: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- 実装の料金表（@PRICEDATE@ 更新）: https://jlcpcb.com/help/article/pcb-assembly-price
- 実装の FAQ（フィデューシャルは JLCPCB が追加、面付け）: https://jlcpcb.com/help/article/pcb-assembly-faqs
- ステンシルの開口: https://jlcpcb.com/help/article/smt-stencil-data-prepared-for-smt-orders
- 部品の向きの補正表（KiBot。JLCPCB 向けの回転の一覧）: https://kibot.readthedocs.io/en/latest/notes_position.html
'''

def check_basic(codes, min_stock=int(os.environ.get('FC_MIN_STOCK', '20000'))):
    """Every LCSC part must be a JLCPCB *Basic* part with plenty of stock (rev E rule). Writes parts_check.csv; exits 1 on failure."""
    import urllib.request
    url = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
    rows, bad = [], []
    for code in sorted(set(codes)):
        req = urllib.request.Request(url, data=json.dumps({'currentPage': 1, 'pageSize': 5, 'keyword': code}).encode(), headers={'Content-Type': 'application/json'})
        try:
            items = ((json.load(urllib.request.urlopen(req, timeout=30)).get('data') or {}).get('componentPageInfo') or {}).get('list') or []
        except Exception as e:
            rows.append((code, '?', '?', '?', f'lookup failed: {e}')); bad.append(code); continue
        it = next((i for i in items if i.get('componentCode') == code), None)
        if not it: rows.append((code, '?', '?', '?', 'not found')); bad.append(code); continue
        lib, stock = it.get('componentLibraryType'), int(it.get('stockCount') or 0)
        ok = lib == 'base' and stock >= min_stock
        rows.append((code, it.get('componentModelEn'), 'Basic' if lib == 'base' else 'Extended', stock, 'OK' if ok else 'NG'))
        if not ok: bad.append(code)
    with open(os.path.join(OUT, 'parts_check.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['LCSC', 'Part', 'Library', 'Stock', 'Result']); w.writerows(rows)
    for r in rows: print('  %-9s %-28s %-8s %9s %s' % tuple(str(x) for x in r))
    if bad: raise SystemExit(f'parts check FAILED for {bad} (must be JLCPCB Basic with stock >= {min_stock})')
    print(f'parts check: all {len(rows)} LCSC parts are JLCPCB Basic with stock >= {min_stock}')

def main():
    os.makedirs(OUT, exist_ok=True)
    if hasattr(D, 'LCSC'):           # designs that carry their own (Basic-only) part map: it is the only source
        parts = {k: (v[0], v[1], 'JLCPCB Basic') for k, v in D.LCSC.items()}
        for k, v in getattr(D, 'HAND', {}).items(): parts[k] = ('', k, 'hand-solder: ' + ', '.join(v))
    else:
        if not os.path.exists(PARTS_JSON):
            json.dump(DEFAULT_PARTS, open(PARTS_JSON, 'w'), indent=1, ensure_ascii=False)
        parts = json.load(open(PARTS_JSON))
    # ---- BOM ----
    groups = {}
    for ref, (lib, sym, val, fp, _) in D.PARTS.items():
        key = val.split(' (')[0]
        groups.setdefault((key, fp), []).append(ref)
    dnp = []; placed = set(); ntypes = 0
    with open(os.path.join(OUT, 'bom_jlc.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (key, fp), refs in groups.items():
            pkg = next((t for t in ('0402', '0603', '0805', '1206') if t in fp), '')
            lcsc, comment, note = parts.get(f'{key}@{pkg}', parts.get(key, ('', key, 'NOT FOUND')))
            if note == 'NOT FOUND':
                for k2 in ('74LVC541', '74LVC245', '74LVC139', '74LVC1G07', '74LVC1G32', '74LVC1G04', '74LVC1G00', '74LVC1G11', '74LVC00'):
                    if key.startswith(k2) and k2 in parts: lcsc, comment, note = parts[k2]; break
            if note == 'NOT FOUND': print('WARNING: no LCSC part for', key, fp)
            refs.sort(key=lambda r: (r.rstrip('0123456789'), int(''.join(ch for ch in r if ch.isdigit()) or 0)))
            if not lcsc: dnp += refs; continue
            w.writerow([comment or key, ','.join(refs), fp.split(':')[1], lcsc]); placed.update(refs); ntypes += 1
    # ---- CPL via kicad-cli pos export ----
    pos = os.path.join(OUT, 'pos.csv')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '-o', pos, PCB], check=True, capture_output=True)
    rows = list(csv.DictReader(open(pos)))
    with open(os.path.join(OUT, 'cpl_jlc.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for r in rows:
            ref = r['Ref']
            if ref in dnp or ref == 'J1': continue
            rot = float(r['Rot'])
            if r['Side'] == 'top':
                rot = (rot + CPL_ROT.get(D.PARTS[ref][3].split(':')[1], 0)) % 360
            w.writerow([ref, f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", 'Top' if r['Side'] == 'top' else 'Bottom', f"{rot:.1f}"])
    os.remove(pos)
    # ---- Gerbers ----
    fab = os.path.join(HW, 'fab'); z = os.path.join(OUT, 'gerbers.zip')
    if os.path.exists(z): os.remove(z)
    if getattr(D, 'JLC_RULES', False):
        import zipfile
        names = sorted(n for n in os.listdir(fab) if n.endswith(FAB_SUFFIX))
        need = ('F_Cu.gtl', 'B_Cu.gbl', 'F_Mask.gts', 'B_Mask.gbs', 'F_Silkscreen.gto', 'B_Silkscreen.gbo', 'Edge_Cuts.gm1', 'PTH.drl')
        missing = [k for k in need if not any(n.endswith(k) for n in names)]
        if missing: raise SystemExit(f'fab files missing for the JLCPCB zip: {missing} (run route_pcb.py first)')
        with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
            for n in names: zf.write(os.path.join(fab, n), n)
        print('gerbers.zip:', ', '.join(names))
    else:
        shutil.make_archive(z[:-4], 'zip', fab)
    if hasattr(D, 'LCSC'): check_basic([v[0] for v in D.LCSC.values()])
    txt = {'rev B': README_B, 'rev C': README_C, 'rev E': README_E, 'rev F': README_F, 'rev F2': README_F2, 'rev G': README_G}.get(D.REV, README_D).replace('@DNP@', ', '.join(dnp))
    if '@TYPES@' in txt:
        import pcbnew, gen_pcb
        b = pcbnew.LoadBoard(PCB); bb = b.GetBoardEdgesBoundingBox()
        joints = sum(len(list(fp.Pads())) for fp in b.GetFootprints() if fp.GetReference() in placed)
        TRK, CLR, VIA, VDR = gen_pcb.rules()
        for k, v in (('@TYPES@', str(ntypes)), ('@PARTS@', str(len(placed))), ('@JOINTS@', str(joints)), ('@PRICEDATE@', JLC_PRICE['date']),
                     ('@EST2@', '%.0f' % assembly_estimate(ntypes, joints, 2)), ('@EST5@', '%.0f' % assembly_estimate(ntypes, joints, 5)),
                     ('@SIZE@', '%.1f × %.1f' % (pcbnew.ToMM(bb.GetWidth()) - 0.1, pcbnew.ToMM(bb.GetHeight()) - 0.1)),
                     ('@TRACK@', '%.2f' % TRK), ('@CLEAR@', '%.2f' % CLR), ('@VIA@', '%.1f' % VIA), ('@VDR@', '%.1f' % VDR),
                     ('@CLAMPS@', '・'.join(sorted((r for r, v in D.PARTS.items() if v[2] == 'BAV99'), key=lambda r: int(r[1:]))))):
            txt = txt.replace(k, v)
    with open(os.path.join(OUT, 'README.md'), 'w') as f: f.write(txt)
    print('written:', OUT, 'DNP:', dnp)

if __name__ == '__main__':
    main()
