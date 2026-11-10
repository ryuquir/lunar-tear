#!/usr/bin/env python3
"""Produce the JLCPCB order package (PCB + SMT assembly) in hardware/jlcpcb/:
   gerbers.zip, bom_jlc.csv (Comment, Designator, Footprint, LCSC Part #), cpl_jlc.csv (Designator, Mid X, Mid Y, Layer, Rotation).
A board with gold fingers cannot be ordered as "Economic PCBA" (JLCPCB PCB assembly capabilities: gold fingers "Not
Support"); it is a "Standard PCBA" order, which needs edge rails and fiducials (JLCPCB adds both). The README written
next to the files says so and gives the order options and the assembly cost from JLCPCB's price table.
LCSC part numbers: designs with their own LCSC map (rev E on: Basic parts only) use that map and nothing else;
older designs read <hw dir>/jlc_parts.json (created from DEFAULT_PARTS on first run; edit it to substitute parts)."""
import os, sys, re, csv, json, subprocess, shutil
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
# SOIC-8 (W25Q128JVSIQ, C97521; rev G): JLCPCB's footprint SOIC-8_L5.3-W5.3-P1.27-LS8.0-BL has pin 1 at the bottom left
# of their drawing, which is 270 for a KiCad SOIC at 0 (the common rotation tables agree: "^SOIC-" = 270).
# check_cpl.py compares every row of the CPL with JLCPCB's library footprint pad by pad; run it on the day of the order.
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
- **Gold Fingers: Yes** → **Bevelling: 30°**（カードエッジ）/ Copper 1 oz / Via Covering: Tented / Mark on PCB: Remove Mark（JLCPCB は 2026 年 5 月に注文番号の印字をやめた）
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

README_G = '''# JLCPCB 注文パッケージ（famicart rev G: 任天堂の大型カセットシェル用）

Pico 2 ×2 + XIAO RP2350 ×2 が基本構成、Pico 2 ×2 は増設用（載せなくても動く）。16 MB の SPI フラッシュを載せ、microSD
ソケットは任意。回路と配置の説明は `docs/12_rev_g_plan.md`、外形図は `../outline.png`、配置図は `../placement.png`。

**状態**: 設計レビューと独立検証の指摘を反映した版で、**実機では未検証**。rev G 用のファームウェアはまだ無い（ピン配置と一部の信号の
極性が rev F と違う。`docs/12_rev_g_plan.md` の作業一覧）。**シェルへの収まりも実物では未確認**なので、最初の注文は最少枚数にして、
モジュールをはんだ付けする前に基板だけをシェルに入れて確かめること。

| ファイル | 内容 |
|---|---|
| `gerbers_rails.zip` | **A 案（推奨）**: 基板＋左右の捨て基板（ミシン目のタブでつないである）。@PANEL@ mm |
| `gerbers.zip` | B 案: 基板だけ。@SIZE@ mm。捨て基板は JLCPCB に付けてもらう |
| `bom_jlc.csv`、`cpl_jlc.csv` | 部品表と配置。A 案・B 案で共通（座標は同じ） |
| `rails.png` | 捨て基板の位置の図。JLCPCB への問い合わせに添付する |
| `parts_check.csv`、`cpl_check.csv` | 部品の区分・在庫と、部品の向きの検査結果 |

このデータの基板は、配線 @NTRACKS@ 本・ビア @NVIAS@ 個・未接続 @NOPEN@。

## 1. 注文の種類と、捨て基板の付け方
- 金フィンガー付きの基板は **Economic PCBA では受け付けられない**（JLCPCB の実装仕様表で Gold fingers は Economic "Not Support"、
  Standard "Support"）。**Standard PCBA** で注文する。実装は表面（Top）だけ、@TYPES@ 種類・@PARTS@ 点/枚。
- Standard PCBA は捨て基板（Edge Rails、幅 5 mm 以上）とフィデューシャルが必須。
- **JLCPCB に任せると、捨て基板は既定で「長いほうの 2 辺」に付く**（注文フォームの注意書き: "Please add two 5mm edge rails along
  the longer sides of your PCB"）。この基板は @SIZE@ mm なので、長い辺は**上の辺と端子の辺**になる。端子の辺に捨て基板が付くと、
  端子の面取りができず（JLCPCB の金フィンガーの説明: 面付けして端子が内側に来ると面取りできない）、端子の辺が割り取った面になる。
- そこでデータを 2 通り用意した。

**A 案（推奨）`gerbers_rails.zip`**: 捨て基板を自分で描き込んだデータ。全体 @PANEL@ mm、基板は 1 枚。
- 捨て基板は左右に 1 本ずつ。幅 @RAILW@ mm、長さ @RAILLEN@ mm。基板との間は幅 @GAP@ mm のルーター加工の溝で、V カットは無い。
- 端子の辺には何も付かない。捨て基板は端子の辺の線より @ENDGAP@ mm 手前で終わる（面取りの刃が通る所を空けるため）。
- 基板とは片側 @NTABS@ か所のタブ（幅 @TABW@ mm）でつながる。タブには直径 @HOLE@ mm の穴が @NHOLES@ 個、穴と穴の間を @WEB@ mm 空けて
  並んでいる（ミシン目）。穴は基板の端の線に外側から接している。折り取ると高さ @RIDGE@ mm 以下の突起が残るので、やすりで端の線まで落とす。
- 捨て基板の上に、フィデューシャル @NFID@ 個（銅 1 mm、レジスト開口 2 mm、中心がパネルの端から @FIDIN@ mm）と、ツーリング穴
  @NTOOL@ 個（直径 @TOOLD@ mm、めっき無し）がある。
- これらの数値は、JLCPCB が「自社で実装するミシン目パネル」に示している条件に合わせてある（5 章の表の「捨て基板」の行）。
- 注文画面では **Delivery Format を "Panel by Customer"（Panel Format は Column 1・Row 1）**、実装の **Edge Rails/Fiducials を
  "Added by Customer"** にする。JLCPCB の定義では、捨て基板をミシン目でつないだデータは「自分で面付けしたデータ」に当たる。
  ただし「基板 1 枚＋自分で描いた捨て基板」の注文のしかたを書いたページは無いので、下の質問の 3) で確かめる。

**B 案 `gerbers.zip`**: 基板だけのデータ（@SIZE@ mm）。捨て基板は JLCPCB に付けてもらい（Added by JLCPCB）、左右に付けるよう Remark で頼む。
- 注文フォームは、大きさを自動で **@FORMB@ mm** に書き換える（上の辺と端子の辺に付けた大きさ。フォームの文面はこれを
  "on the shorter sides" と呼ぶ）。これはフォームの既定の動作で、フォーム上では変えられない。Remark で左右に付けるよう頼み、
  結果は製造データで確かめる（この動作はフォームのスクリプトと文面の一覧から読んだもので、画面では確かめていない）。
- **Confirm Production file を Yes** にして、製造データの大きさが @PANELB@ mm（左右に付いた場合）で、端子の辺に V カットの線が
  無いことを確かめてから承認する。@FORMB@ mm なら上下に付いているので、承認しない。
- JLCPCB が付ける捨て基板は V カットでつながる。左右の端は V カットの面（公差 ±0.4 mm）になり、銅箔から端までの 0.4 mm に余裕が
  無い。JLCPCB は「形が四角や円でない基板の面付けは自分でやること」とも書いているので、B 案は断られることがある。そのときは A 案を使う。

**支払いの前に**: どちらの案でも、「捨て基板の付いた基板の端子を面取りしてもらえるか」は JLCPCB のどのページにも書かれていない。
サポート（チャット）に `rails.png` を見せて確かめる。質問文（そのまま貼る）:

> I am going to order a 2-layer board, 1.2 mm, ENIG, gold fingers (30 on each side) with a 30 degree bevel, and Standard PCBA
> on the top side. Please see the attached drawing. My Gerber file already contains two @RAILW@ mm edge rails that I drew myself,
> on the left and right edges (perpendicular to the gold-finger edge). Each rail is joined to the board by @NTABS@ mouse-bite tabs
> (@TABW@ mm wide, @HOLE@ mm holes) across a @GAP@ mm routed gap. There is no V-cut. The rails end @ENDGAP@ mm above the gold-finger
> edge, so that edge is completely free. The rails carry @NFID@ fiducials (1 mm, centre @FIDIN@ mm from the panel edges) and
> @NTOOL@ tooling holes (@TOOLD@ mm). Panel size @PANEL_X@ mm, one board per panel.
> 1) Can you bevel the gold-finger edge of this board?
> 2) Is this rail arrangement accepted for Standard PCBA?
> 3) Which Delivery Format must I select: Single PCB or Panel by Customer (1 x 1)? Is there an extra charge?
> 4) If I upload the board without rails (@SIZE_X@ mm) instead, can you add the rails on the same two edges
> (panel @PANELB_X@ mm) and still bevel the gold-finger edge?

答えに応じて変える所:
- 1) が「面取りできない」の場合: Gold Fingers の **Beveling を "No"** にし、Remark の "Please bevel this edge 30 degrees." を消す。
  面取り無しで作ってもらい、受け取ってから手で面取りする（6 章）。捨て基板を上下に移す提案は断る。
- 2) が「この捨て基板では実装できない」の場合: 足りない寸法を聞き、`tools/pcb/design_revg.py` の `RAILS` を直してデータを作り直す。
- 3) が "Single PCB" の場合: Delivery Format をそれに合わせる。追加料金があれば 4 章の見積もりに加える。

## 2. PCB の指定（Instant Quote → Add gerber file）
注文フォームの項目名は変わることがある（下の項目名は 2026-11-10 にフォームの文面で確認できたもの。面取りの角度、金の厚さ、外形公差、
ビアの処理、実装の項目は、選択やアップロードのあとに現れる）。

| 項目 | 指定 |
|---|---|
| Base Material / Layers | FR-4 / 2 |
| Dimensions | A 案 @PANEL@ mm、B 案 @SIZE@ mm（ガーバーから自動で入る。基板は本体 75.0 mm + 端子タブ 10.7 mm）|
| PCB Qty | 5（最少。3 枚などは選べない）|
| Product Type | Industrial/Consumer electronics |
| Different Design | 1 |
| Delivery Format | A 案: **Panel by Customer**、Panel Format は Column 1・Row 1。B 案: **Single PCB**。どちらの案でも "Panel by JLCPCB" は選ばない（選ぶと面取りの指定が消える）|
| PCB Thickness | **1.2 mm**（公差 ±10 %: 1.08〜1.32 mm）|
| PCB Color / Silkscreen | Green / White（ほかの色は納期が 2 日延びる）|
| Surface Finish | **ENIG**、Gold Thickness は **2 U"**（約 0.05 µm。1 U" は約 0.025 µm。端子が擦れるので厚いほう。5 枚で約 $17 の追加）|
| Outer Copper Weight | 1 oz |
| Via Covering | Tented |
| Min via hole size/diameter | 標準のまま（設計値: 穴 @VDR@ mm・径 @VIA@ mm）|
| Board Outline Tolerance | ±0.2 mm（Regular。ルーター加工の辺の値）|
| Mark on PCB | **Remove Mark**（既定。JLCPCB は 2026 年 5 月に注文番号の印字をやめた）|
| Electrical Test | Flying Probe Fully Test |
| Gold Fingers | **Yes**、Beveling **30°**（ENIG を選んだときだけ端子が金になる。HASL を選ぶと端子ははんだ〔錫〕になる）|
| Castellated Holes | No |
| Material Type、Via Plating Method、Edge Plating、Blind Slots、UL Marking、Humidity Indicator Card | 既定のまま |
| Confirm Production file | **Yes**（約 $1）。選ぶと「48 時間以内に確認しないと、自動で承認して製造に進む」という画面が出るので、**"Do not confirm automatically"** を選ぶ |

製造データ（Production file）が届いたら、承認する前に次を確かめる: 捨て基板が左右にあること、端子の辺に捨て基板も V カットの線も
無いこと、面取りの指示が入っていること、外形の切り欠きとスリットが図面どおりであること。

PCB Remark（A 案。そのまま貼る）:

> 1) This is ONE board with two @RAILW@ mm edge rails that I drew myself: panel @PANEL_X@ mm, one board per panel. The rails are
> on the left and right edges, each joined by @NTABS@ mouse-bite tabs (@TABW@ mm wide, @HOLE@ mm holes) across a @GAP@ mm routed gap.
> @NFID@ fiducials and @NTOOL@ tooling holes (@TOOLD@ mm) are on the rails. Please do NOT add other rails and do NOT add V-cut.
> 2) Gold fingers are on ONE edge only: the edge with the 78.4 mm wide tab (30 fingers on each side). Please bevel this edge
> 30 degrees. This edge must stay a free routed edge; the rails end @ENDGAP@ mm above it.
> 3) If you cannot bevel a board with these rails, do NOT move or change the rails: put the order on hold and contact me.
> 4) You may shorten the finger copper to your standard setback for the bevel.
> 5) The solder mask window over the gold fingers is intentional: it starts 4.0 mm below the root of the tab and runs to the
> edge. Please do not enlarge it towards the board: tracks run beside the upper ends of the fingers.
> 6) The outline has two side notches, one inner slot (6.6 x 2.4 mm) and cut corners beside the tab. Inner corners are drawn
> with R 0.5 mm. Please keep them as drawn.

PCB Remark（B 案。そのまま貼る）:

> 1) Gold fingers are on ONE edge only: the edge with the 78.4 mm wide tab (30 fingers on each side). Please bevel this edge
> 30 degrees.
> 2) Edge rails for assembly: please add the two 5 mm rails on the LEFT and RIGHT edges (the two 85.7 mm edges, perpendicular
> to the gold-finger edge). Panel size @PANELB_X@ mm, NOT @FORMB_X@ mm as the order form shows. Do NOT put a rail on the
> gold-finger edge or on the opposite edge.
> 3) The gold-finger edge must stay a free routed edge: no rail, no V-cut, no mouse bites.
> 4) If you cannot add the rails on these two edges, or cannot bevel a board with rails: do NOT move the rails; put the order
> on hold and contact me.
> 5) You may shorten the finger copper to your standard setback for the bevel.
> 6) The solder mask window over the gold fingers is intentional: it starts 4.0 mm below the root of the tab and runs to the
> edge. Please do not enlarge it towards the board: tracks run beside the upper ends of the fingers.
> 7) The outline has two side notches, one inner slot (6.6 x 2.4 mm) and cut corners beside the tab. Inner corners are drawn
> with R 0.5 mm. Please keep them as drawn.

**端子の金について**: JLCPCB は硬質金めっき（抜き差しの多いコネクタ用の電解めっき、0.5〜1.5 µm 級）を扱っておらず、金フィンガーにも
ENIG を使う（同社の記事に明記）。注文できる ENIG の金の厚さは 1 U"（約 0.025 µm）か 2 U"（約 0.05 µm）の 2 つ。同社の記事は、
ENIG は「抜き差しが 20 回未満の用途なら足りる」「数十回の抜き差しで金が減る」、硬質金は 500〜1000 回以上もつ、としている（出典の
ない目安）。このカセットは挿したまま使う前提で、ゲームの入れ替えは USB か microSD で行う。金が減っても下のニッケルで導通はするが、
接触が不安定になったら端子を無水アルコールで拭く。

**面取りの寸法**: JLCPCB の図では、面取りは 30° ± 5°、端子の銅は基板の端から 1.15 mm（板厚 1.6 mm 以下）手前で止める。注文フォームの
表示では、板厚 1.2 mm・30° の面取りは深さ 0.89 mm、残る厚み 0.4 mm。この基板の端子は端から 1.2 mm 以上（電源・GND の長い 4 本）と
2.0 mm（そのほか）手前で終わるので、面取りは銅に届かない（余裕 0.3 mm 以上）。JLCPCB は必要なら端子の銅を自分で短くする。

## 3. PCB Assembly の指定
| 項目 | 指定 |
|---|---|
| PCBA Type | **Standard** |
| Assembly Side | Top Side |
| PCBA Qty | 2 または 5 |
| Edge Rails/Fiducials | A 案: **Added by Customer**。B 案: Added by JLCPCB |
| Tooling holes（項目が出た場合）| A 案: 自分で付けた側（Added by Customer）。B 案: JLCPCB に任せる側 |
| File provided as（面付けの注文で出る項目）| "Complete File, just proceed with my own files"（BOM と CPL はこの 1 枚で完結している）|
| Confirm Parts Placement | Yes（部品の向きを製造前に画面で確認できる）|
| 部品の選び方 | By Customer (Self-Service)。BOM に LCSC の部品番号が入っている |
| BOM / CPL | `bom_jlc.csv` / `cpl_jlc.csv` |
| 捨て基板を外すサービス（Depaneling）| 選ばない（選ばなければ捨て基板は付いたまま届く。外してもらうのは有料）|

- 実装の Remark にも、PCB Remark の 1)〜3) を貼る（フォームの注意書き: 実装についての Remark は実装の欄に書くこと）。
- JLCPCB は検査用の記号を捨て基板に自動で印刷する（フォームの注意書き）。基板本体には影響しない。
- 部品の照合画面の正しい状態: **@TYPES@ 行・@PARTS@ 点がすべて一致、すべて Basic、未選択の部品なし**。
- 実装しない部品（手はんだ・基板パターン）: @DNP@
- CPL の角度は JLCPCB の部品ライブラリの向きに合わせて補正済み: 抵抗アレイ = 270°、SOT-23（2N7002・BAV99）= 180°、U7（SOIC-8）= 270°
  を、基板上の角度に足してある。JLCPCB は自社の部品ライブラリ（LCSC 番号ごとの EasyEDA のフットプリント）を、CPL の角度だけ
  反時計回りに回して置く（同社の説明: "Positive values are counter clockwise"）。全 @PARTS@ 点について、そのフットプリントを CPL の
  とおりに置いたときに、各パッドが基板の同じ番号のパッドに重なることを確かめてある（`tools/pcb/check_cpl.py`）。
  JLCPCB はライブラリを書き換えることがある（2026 年に 2 点が更新された）ので、**注文する日に `check_cpl.py` をもう一度実行する**。
- **部品プレビューで見る点**（上から見て、端子を下にした向き。下の向きはこのデータの基板から読み取ったもの）:
@ORIENT@
  **U7 か B5819W（@SCHOTTKY@）が 180° 回って見えたら承認しない。** @SENSE@
  SOT-23 は 180° 回るとパッドに合わなくなるので、画面で分かる。

## 4. 費用（JLCPCB の料金表 @PRICEDATE@ 更新分から計算。部品代・送料・税は別）
| | 2 枚実装 | 5 枚実装 |
|---|---|---|
| 実装費（Standard・片面） | 約 US$ @EST2@ | 約 US$ @EST5@ |
| 治具（Fixture）費 2 個が加わった場合 | 約 US$ @FIX2@ | 約 US$ @FIX5@ |

- 内訳: セットアップ $25.56 + ステンシル $8.21 + フィーダー $1.53 × @TYPES@ 種類 + はんだ付け $0.0016 × @JOINTS@ 接点 × 枚数
  （1 枚あたり最低 $0.48）+ 梱包 $0.50 + 配置確認 $0.45。**部品の種類が 1 つ増えるごとに $1.53** かかる（Standard では Basic と
  Extended で料金は同じ。Basic だけにしているのは、在庫が安定していて入手しやすいから）。
- 治具費は料金表では 1 個 $8.21、29 枚以下は 2 個。どの注文に掛かるかは料金表に書かれていない。料金表にはほかに、ステンシルと
  治具の保管料（各 $4.93）の項目がある。
- PCB 代（5 枚、ENIG 2 U"・金フィンガー・30° 面取り・1.2 mm・Confirm Production file 込み、送料別。2026-11-10 の見積もり画面）:
  A 案の大きさ（@PANEL@ mm）で約 US$ 44、B 案の大きさ（@SIZE@ mm）で約 US$ 40。A 案は 102 × 102 mm 以下の特別価格の対象外で、
  "Panel by Customer" を選んでも見積もりは同じだった。面付けデータは、注文後に JLCPCB が料金を直すことがある（同社の説明）。
- 納期: Standard PCBA の製造は 4 日以上（Economic は 1〜3 日）。
- モジュール（秋月）: 基本構成 ¥4,180（Pico 2 ×2 + XIAO RP2350 ×2）、増設の Pico 2 は 1 枚 ¥990、microSD ソケット ¥150。

## 5. JLCPCB の製造条件との照合
| 項目 | この基板 | JLCPCB の条件 |
|---|---|---|
| 基板サイズ | @SIZE@ mm（捨て基板込み @PANEL@ mm）| Standard PCBA は 70 × 70 mm 以上。金フィンガーは 50 × 50 mm 以上 |
| 材質・板厚 | FR-4、1.2 mm | FR-4 は 0.4〜2.0 mm（1.2 mm あり）。板厚の公差は ±10 % |
| 表面処理・端子 | ENIG、金フィンガー、30° 面取り。端子の銅は基板の端の 1.2 mm 以上手前で終わる | 端子の金は ENIG。面取りは 30° か 45°。銅は端から 1.15 mm 手前まで（板厚 1.6 mm 以下、30°）|
| 端子部のレジスト | タブの付け根から 4.0 mm より先（配線を置かない範囲）は、表裏とも端子の間を含めて全面開口 | 金フィンガーの範囲はレジストを全面開口にする（残すと抜き差しで剥がれる）|
| 端子の近く | ビアは端子から 1.0 mm 以上離す。シルクは無い | めっき穴・SMD パッドは金フィンガーから 1.0 mm 以上。端子の近くにレジスト・シルクを置かない（同社の記事の指針）|
| 面取りと面付け | 捨て基板は左右。端子の辺は外周のまま。V カット無し | 面付けして端子が内側に来ると面取りできない |
| 捨て基板（A 案）| 幅 @RAILW@ mm、左右。タブは幅 @TABW@ mm、穴 @HOLE@ mm、穴の間 @WEB@ mm。フィデューシャル @NFID@ 個（銅 1 mm、開口 2 mm、中心がパネルの端から @FIDIN@ mm）。ツーリング穴 @TOOLD@ mm × @NTOOL@ | 幅 5 mm 以上。ミシン目のタブは幅 5 mm 以上、穴 0.5〜0.8 mm、穴の間 0.2〜0.3 mm。フィデューシャルは 1 mm、中心がパネルの端から 3.85 mm（パッドの縁まで 3.35 mm）、開口は銅の 2 倍、3〜4 個。ツーリング穴 2 mm |
| 配線幅 / 間隔 | @TRACK@ / @CLEAR@ mm | 0.10 / 0.10 mm 以上（2 層・1 oz）|
| ビア | 径 @VIA@ mm、穴 @VDR@ mm | 穴 0.3 mm 以上が標準。径は穴 + 0.1 mm 以上（推奨 + 0.15 mm）。追加料金は「穴 0.3 mm 未満かつ径 0.4 mm 以下」のとき |
| 穴と穴 / 穴と配線 | 0.25 mm 以上 / 0.2 mm 以上 | 0.2 mm 以上 / 0.2 mm 以上 |
| 銅箔と基板端 | 0.3 mm 以上。左右の端は 0.4 mm 以上（タブの穴は基板の外側にあり、穴の縁から銅まで 0.4 mm）| ルーター加工の端 0.2 mm 以上、V カットの端 0.4 mm 以上。穴と配線は 0.2 mm 以上 |
| スリット・切り欠き | 幅 2.4 mm（捨て基板との間は @GAP@ mm）。内側の角は R0.5 mm で作図 | 非めっきスリットは幅 1.0 mm 以上。角に丸みの無い角穴・スリットは作れない |
| 外形の公差 | 切り欠きの奥行きとスリットの長さに 0.6 mm、左右の端に 0.2 mm の逃げ | ルーター加工 ±0.2 mm、V カット ±0.4 mm |
| シルク | 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上（英字は大文字だけ）| 線幅 0.15 mm 以上、文字の高さ 1.0 mm 以上 |
| レジスト | パッドの開口はパッドと同じ大きさ。開口と開口の間のレジストは @MASKWEB@ | 0.10 mm 以上（黒・白は 0.13 mm）。開口と隣の配線は 0.09 mm 以上 |
| 実装 | 表面のみ | Standard PCBA は片面・両面とも可 |
| はんだペースト | 手はんだ部品のパッドには置いていない | ステンシルの開口は実装する部品のパッドだけに作られる |

ガーバーの ZIP には製造に使う層（銅箔・レジスト・シルク・ペースト・外形）とドリルだけを入れてある。`tools/pcb/check_jlc.py` は、
2 つの ZIP の中身が基板ファイルを今プロットしたものと同じであること、捨て基板付きの基板の中身（配線・ビア・部品・ベタ・外形）が
基板だけのものと同じであること、捨て基板の寸法（上の表の数値）を、データから測って検査する。

## 6. 受け取ってから
1. 板厚をノギスで測る（1.08〜1.32 mm の範囲で届く）。
2. 捨て基板を外す。A 案はタブの穴と穴の間を**ニッパーで切る**（基板を折り曲げない。右側の下のタブのすぐ内側には電源の
   ダイオードが並んでいて、基板を曲げるとはんだ付けに力が掛かる）。端面に残った突起（高さ @RIDGE@ mm 以下）を、基板の端の
   線までやすりで落とす（左右 @NTABS@ か所ずつ）。B 案は V カットなら折り、端面をやすりで平らにする。
   面取り無しで届いた場合は、端子の辺の角を表裏とも 30〜45° の角度で 0.3〜0.5 mm ほど、目の細かいやすりで落とす
   （端子の銅は端から 1.2 mm 以上手前で終わっているので、金には触れない）。角が立ったままだと本体のコネクタの接点を傷める。
3. **基板だけ**をシェルに入れて、左右の切り欠き・スリット・端子タブの位置を確かめる。タブの付け根など、内側の角に残る丸みが
   シェルに当たる場合は、やすりで落とす。
   あわせて、**基板の表・裏それぞれからシェルの内壁までの隙間**を測る（ノギスの深さ測定か、粘土を挟んで閉じる）。この寸法は
   どの資料にも無かった。必要な高さの目安（基板の厚み＋コネクタの一般的な寸法からの見積もりで、実測ではない）:
   **表（ラベル面）** = XIAO（U3・U6）約 4.5 mm、増設の Pico 2（U4）約 3.8 mm、microSD ソケット約 2 mm、実装済みの部品は最大約 2.2 mm（U7）。
   **裏** = Pico 2（U1・U2・U5）約 3.8 mm。任天堂の純正基板は背の高い部品を裏（31〜60 番の面）に載せているので、表のほうが狭い
   可能性がある。表の隙間が XIAO に足りない場合、この版ではシェルの表側を閉じられない（表側のシェルの内側を削るか、開けたまま
   使い、次の版で XIAO を裏に移す）。動作には影響しない。
4. モジュールに**ファームを書き込んでから**はんだ付けする（U2 の USB 端子は基板の内側を向くので、付けたあとはケーブルを挿しにくい）。
   Pico 2 は、USB コネクタの固定足 4 か所（裏面に出ている）のはんだが盛り上がっていれば、先に平らにする（基板から浮くため）。
5. はんだ付けの順番: 裏面（U2 → U1、増設するなら U5）を先に、表面を後に。表面は **U6 → J3（使うなら）→ U4（増設するなら）**、
   U3 はいつでもよい。U2 を付けるときは、すぐ下の金フィンガーにはんだやフラックスが付かないよう、端子をテープで覆う。
   基板のシルクに `U1 CPU` のように役割が書いてある。シルクの `USB` の字がある側に、モジュールの USB 端子を向ける
   （XIAO は 180° 回しても載ってしまい、その向きでは 5 V が別のピンに入る）。
6. Pico 2 は端面（キャステレーション）40 か所だけをはんだ付けする。XIAO は縁の 14 ピンだけ（裏面パッドは使わない）。
   付けたあと、はんだブリッジが無いか見る所（かっこ内は、パッドを囲む四角どうしの距離）: @BRIDGES@
7. XIAO の 5V ピンは USB の VBUS と直結している。**本体の電源が入っている間は、電源の入っていない PC やハブに U3・U6 の USB を
   つながない**（本体の 5 V が USB ケーブル側へ出る）。

## 7. 手はんだ部品（秋月電子）
| 部品 | 秋月 通販コード | 価格 | 位置 |
|---|---|---|---|
| Raspberry Pi Pico 2 | 129604 | ¥990 ×2（＋増設 ×2）| **裏**: U2（下、PPU 側）・U1（上、CPU 側）・U5（中、PPU 側の増設）／**表**: U4（上、CPU 側の増設）|
| Seeed XIAO RP2350 | 129619 | ¥1,100 ×2 | **表**: U3（中央右、IRQ・拡張音源・ネームテーブル制御）・U6（上、ハブ: SFC チップ機能・保存・更新）|
| microSD ソケット Hirose DM3AT-SF-PEJM5 | 102395 | ¥150（任意）| **表**: J3（右上）|

## 出典（JLCPCB 公式、2026-11-10 に確認。同社のヘルプ記事は更新日が変わるので、注文する日にもう一度読む）
- 実装仕様（Economic / Standard の違い、金フィンガー、基板サイズ、面付けの種類）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- 基板の製造仕様（配線・ビア・外形・スリット・シルク・レジスト・板厚の公差、"Mouse bites Panel" の行: タブ・ミシン目・ツーリング穴・フィデューシャルの数値）: https://jlcpcb.com/capabilities/pcb-capabilities
- 追加料金になる場合（小径穴、金の厚さ、面付けと特別価格）: https://jlcpcb.com/help/article/In-what-cases-will-there-be-charged-extra
- 金フィンガー（面取りの角度、面付けと面取り、端子部のレジスト全面開口、銅の後退）: https://jlcpcb.com/help/article/jlcpcb-gold-fingers
- 面取りの寸法の図: https://jlcpcb.com/blog/considerations-for-gold-finger-bevel-design
- 金フィンガーの設計の指針（めっき穴・パッドは端子から 1.0 mm 以上）: https://jlcpcb.com/blog/pcb-gold-fingers
- 硬質金めっきと ENIG、JLCPCB が硬質金を扱わないこと: https://jlcpcb.com/blog/hard-gold-pcb-finish
- 捨て基板とフィデューシャル（図: フィデューシャルのパッドの縁から基板の端まで 3.35 mm 以上）: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- 注文フォーム（捨て基板は長い辺に付く旨の注意書き、Delivery Format の定義、Beveling、Confirm Production file、Mark on PCB、見積もり）: https://cart.jlcpcb.com/quote
- 注文番号の印字の廃止: https://jlcpcb.com/help/article/how-to-mark-on-pcb
- 面付けと V カットの条件: https://jlcpcb.com/help/article/pcb-panelization
- 実装の料金表（@PRICEDATE@ 更新）: https://jlcpcb.com/help/article/pcb-assembly-price
- 実装の FAQ（面付けの方法、フィデューシャル）: https://jlcpcb.com/help/article/pcb-assembly-faqs
- BOM と CPL の書式（回転は反時計回りが正）: https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly 、 https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly
- ステンシルの開口: https://jlcpcb.com/help/article/smt-stencil-data-prepared-for-smt-orders
- 部品の向きの補正表（KiBot。JLCPCB 向けの回転の一覧）: https://kibot.readthedocs.io/en/latest/notes_position.html
'''

def check_basic(codes, min_stock=int(os.environ.get('FC_MIN_STOCK', '20000'))):
    """Every LCSC part must be a JLCPCB *Basic* part with plenty of stock (rev E rule). Writes parts_check.csv; exits 1 on failure."""
    import urllib.request
    url = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
    rows, bad = [], []
    import time
    for code in sorted(set(codes)):
        req = urllib.request.Request(url, data=json.dumps({'currentPage': 1, 'pageSize': 30, 'keyword': code}).encode(), headers={'Content-Type': 'application/json'})
        it, err = None, 'not found'
        for attempt in range(5):         # the catalogue search now and then answers with an empty list: ask again
            try:
                items = ((json.load(urllib.request.urlopen(req, timeout=30)).get('data') or {}).get('componentPageInfo') or {}).get('list') or []
                it = next((i for i in items if i.get('componentCode') == code), None); err = 'not found'
            except Exception as e:
                err = f'lookup failed: {e}'
            if it: break
            time.sleep(2.0)
        if not it: rows.append((code, '?', '?', '?', err)); bad.append(code); continue
        lib, stock = it.get('componentLibraryType'), int(it.get('stockCount') or 0)
        ok = lib == 'base' and stock >= min_stock
        rows.append((code, it.get('componentModelEn'), 'Basic' if lib == 'base' else 'Extended', stock, 'OK' if ok else 'NG'))
        if not ok: bad.append(code)
    with open(os.path.join(OUT, 'parts_check.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['LCSC', 'Part', 'Library', 'Stock', 'Result']); w.writerows(rows)
    for r in rows: print('  %-9s %-28s %-8s %9s %s' % tuple(str(x) for x in r))
    if bad: raise SystemExit(f'parts check FAILED for {bad} (must be JLCPCB Basic with stock >= {min_stock})')
    print(f'parts check: all {len(rows)} LCSC parts are JLCPCB Basic with stock >= {min_stock}')

def _dir(dx, dy):
    """Where a point lies as seen from the part centre, in the view of the notes (from above, gold fingers at the bottom)."""
    if abs(dx) > 2 * abs(dy): return '右' if dx > 0 else '左'
    if abs(dy) > 2 * abs(dx): return '下' if dy > 0 else '上'
    return ('右' if dx > 0 else '左') + ('下' if dy > 0 else '上')

def _refs(refs):
    return '・'.join(sorted(refs, key=lambda r: (r.rstrip('0123456789'), int(''.join(ch for ch in r if ch.isdigit()) or 0))))

def orientation_notes(b, D):
    """The lines of the notes that say how each kind of part must look in JLCPCB's placement preview, read from the board."""
    import pcbnew
    def off(fp, num):
        p = next(q for q in fp.Pads() if q.GetNumber() == num); return p.GetPosition().x - fp.GetPosition().x, p.GetPosition().y - fp.GetPosition().y
    def grouped(val, fn):
        g = {}
        for ref, q in D.PARTS.items():
            if q[2].split(' (')[0] == val: g.setdefault(fn(b.FindFootprintByReference(ref)), []).append(ref)
        return g
    def span(fp):
        xs = [p.GetPosition().x for p in fp.Pads()]; ys = [p.GetPosition().y for p in fp.Pads()]
        return '縦' if max(ys) - min(ys) > max(xs) - min(xs) else '横'
    out = []
    u7 = b.FindFootprintByReference('U7')
    if u7:
        d1, d4 = off(u7, '1'), off(u7, '4'); vertical = abs(d4[1] - d1[1]) > abs(d4[0] - d1[0])
        row = ('右' if d1[0] > 0 else '左') if vertical else ('下' if d1[1] > 0 else '上')
        run = ('上から下へ' if d4[1] > d1[1] else '下から上へ') if vertical else ('左から右へ' if d4[0] > d1[0] else '右から左へ')
        out.append('U7: 1 番ピンの印が**%s**。1〜4 番ピンが%s側に、%s並ぶ。' % (_dir(*d1), row, run))
    for val, pad, text in (('B5819W', '1', 'カソードの帯が**%s**'),):
        g = grouped(val, lambda fp: _dir(*off(fp, pad)))
        out.append('B5819W: ' + '、'.join('%s は%s' % (_refs(r), text % k) for k, r in sorted(g.items())) + '。')
    g = {}
    for val in ('2N7002', 'BAV99'):
        for k, r in grouped(val, lambda fp: _dir(*off(fp, '3'))).items(): g.setdefault(k, []).extend(r)
    if g: out.append('2N7002 と BAV99（SOT-23）: ' + '、'.join('%s は足 1 本の側が**%s**' % (_refs(r), k) for k, r in sorted(g.items())) + '。')
    arr = {}
    for ref, q in D.PARTS.items():
        if 'R_Array' in q[3] and b.FindFootprintByReference(ref): arr.setdefault(span(b.FindFootprintByReference(ref)), []).append(ref)
    if arr: out.append('抵抗アレイ: ' + '、'.join(('%d 個すべて' % len(r) if len(arr) == 1 else _refs(r) + ' は') + '長い辺が%s' % k for k, r in sorted(arr.items())) + '。')
    sw = b.FindFootprintByReference('SW1')
    if sw: out.append('SW1: 足が%s。' % ('上と下' if span(sw) == '縦' else '左と右'))
    return '\n'.join('  %d. %s' % (i + 1, t) for i, t in enumerate(out))

def _boxes(b, layer, only=None):
    out = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.GetLayerSet().Contains(layer) or (only and not only(fp, p)): continue
            bb = p.GetBoundingBox(); out.append((bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom(), fp.GetReference(), p.GetNumber(), p.GetNetname(), p.GetSolderMaskExpansion()))
    return out

def _gap(a, c, grow=0):
    import math
    dx = max(c[0] - a[2], a[0] - c[2], 0) - (grow if max(c[0] - a[2], a[0] - c[2]) > 0 else 0)
    dy = max(c[1] - a[3], a[1] - c[3], 0) - (grow if max(c[1] - a[3], a[1] - c[3]) > 0 else 0)
    return math.hypot(max(dx, 0), max(dy, 0))

def mask_web_note(b):
    """Smallest strip of solder mask between two pad openings of one side (pads are axis-parallel boxes; openings that
    lie inside the gold-finger window, where there is no mask at all, do not count)."""
    import pcbnew, gen_pcb
    ywin = pcbnew.FromMM(gen_pcb.BODY_H + gen_pcb.FINGER_KEEP) if getattr(D, 'JLC_RULES', False) else None
    best = None
    for layer in (pcbnew.F_Mask, pcbnew.B_Mask):
        bx = sorted(_boxes(b, layer))
        for i, a in enumerate(bx):
            for c in bx[i + 1:]:
                if c[0] - a[2] > 2000000: break
                if a[4] == c[4] == 'J1' and ywin is not None: continue          # finger to finger: inside or beside the window
                g = _gap(a, c, a[7] + c[7])
                if g > 0 and (best is None or g < best[0]): best = (g, a, c)
    if not best: return '-'
    g, a, c = best
    return '%.2f mm 以上（最小は %s の %s 番と %s 番のパッドの間）' % (g / 1e6 - 0.0005, a[4], a[5], c[5]) if a[4] == c[4] else '%.2f mm 以上（最小は %s.%s と %s.%s の間）' % (g / 1e6 - 0.0005, a[4], a[5], c[4], c[5])

def bridge_note(b, D, limit=1.0):
    """Hand-soldered module pads with a foreign pad of another part within `limit` mm: the places to inspect for bridges."""
    import pcbnew
    hand = {r for r in D.PARTS if r.startswith('U') and r != 'U7'}
    near = {}
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        bx = _boxes(b, layer)
        for a in bx:
            if a[4] not in hand or not a[5] or not a[5].isdigit(): continue
            for c in bx:
                if c[4] == a[4] or c[4] in hand or (a[6] and a[6] == c[6]): continue
                g = _gap(a, c) / 1e6
                if g < limit: near.setdefault((a[4], c[4]), {})[int(a[5])] = min(g, near.get((a[4], c[4]), {}).get(int(a[5]), 9.0))
    if not near: return 'モジュールのパッドから %.1f mm 以内に、ほかの部品のパッドは無い。' % limit
    return '、'.join('%s の %s 番パッドと %s（%.2f mm）' % (m, '・'.join(str(n) for n in sorted(v)), o, min(v.values())) for (m, o), v in sorted(near.items())) + '。'

def sense_note(dnp):
    """Which parts with a direction would come out reversed if the sense of the CPL angle (counter-clockwise) were taken
    the other way round: the ones whose CPL angle is 90 or 270 degrees."""
    rot = {r[0]: float(r[4]) for r in cpl_table(dnp)[1:]}
    polar = [r for r, q in D.PARTS.items() if r in rot and (q[2].split(' (')[0] == 'B5819W' or r == 'U7')]
    turned = [r for r in polar if abs(rot[r] % 180 - 90) < 1]; same = [r for r in polar if r not in turned]
    if not polar: return ''
    txt = '回転の向き（時計回りと反時計回り）が取り違えられた場合に逆向きになるのは、CPL の角度が 90° か 270° の部品で、向きのある部品では'
    txt += (' %s がそれに当たる' % _refs(turned)) if turned else 'それに当たるものは無い'
    if same: txt += '（%s は %s なので変わらない）' % (_refs(same), '・'.join(sorted({'%.0f°' % rot[r] for r in same})))
    return txt + '。'

def routed_or_exit():
    """An order package made from an unrouted board looks complete (the notes, the BOM and the CPL do not depend on the
    routing), so refuse to write one: the board must have tracks and no open connection."""
    import pcbnew
    b = pcbnew.LoadBoard(PCB); b.BuildConnectivity()
    ntr = sum(1 for t in b.GetTracks()); nopen = b.GetConnectivity().GetUnconnectedCount(False)
    if not ntr or nopen:
        raise SystemExit(f'not packaging: the board has {ntr} tracks and {nopen} open connections (route it first; FC_ALLOW_UNROUTED=1 for a rehearsal)')

def part_map():
    if hasattr(D, 'LCSC'):           # designs that carry their own (Basic-only) part map: it is the only source
        parts = {k: (v[0], v[1], 'JLCPCB Basic') for k, v in D.LCSC.items()}
        for k, v in getattr(D, 'HAND', {}).items(): parts[k] = ('', k, 'hand-solder: ' + ', '.join(v))
        return parts
    if not os.path.exists(PARTS_JSON):
        json.dump(DEFAULT_PARTS, open(PARTS_JSON, 'w'), indent=1, ensure_ascii=False)
    return json.load(open(PARTS_JSON))

def bom_table(warn=True):
    """(rows of bom_jlc.csv with the header, parts that JLCPCB does not place, parts that it places, number of part
    types): a function of the design file alone."""
    parts = part_map(); groups = {}
    for ref, (lib, sym, val, fp, _) in D.PARTS.items():
        groups.setdefault((val.split(' (')[0], fp), []).append(ref)
    rows = [['Comment', 'Designator', 'Footprint', 'LCSC Part #']]; dnp = []; placed = set(); ntypes = 0
    for (key, fp), refs in groups.items():
        pkg = next((t for t in ('0402', '0603', '0805', '1206') if t in fp), '')
        lcsc, comment, note = parts.get(f'{key}@{pkg}', parts.get(key, ('', key, 'NOT FOUND')))
        if note == 'NOT FOUND':
            for k2 in ('74LVC541', '74LVC245', '74LVC139', '74LVC1G07', '74LVC1G32', '74LVC1G04', '74LVC1G00', '74LVC1G11', '74LVC00'):
                if key.startswith(k2) and k2 in parts: lcsc, comment, note = parts[k2]; break
        if note == 'NOT FOUND' and warn: print('WARNING: no LCSC part for', key, fp)
        refs.sort(key=lambda r: (r.rstrip('0123456789'), int(''.join(ch for ch in r if ch.isdigit()) or 0)))
        if not lcsc: dnp += refs; continue
        rows.append([comment or key, ','.join(refs), fp.split(':')[1], lcsc]); placed.update(refs); ntypes += 1
    return rows, dnp, placed, ntypes

def cpl_table(dnp):
    """Rows of cpl_jlc.csv with the header: the positions of the board file (kicad-cli), the angle turned by the offset
    between KiCad's footprint and the footprint of JLCPCB's part library (CPL_ROT)."""
    import tempfile
    pos = os.path.join(tempfile.mkdtemp(prefix='gen_jlc_'), 'pos.csv')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '-o', pos, PCB], check=True, capture_output=True)
    rows = [['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation']]
    for r in csv.DictReader(open(pos)):
        ref = r['Ref']
        if ref in dnp or ref == 'J1': continue
        rot = float(r['Rot'])
        if r['Side'] == 'top': rot = (rot + CPL_ROT.get(D.PARTS[ref][3].split(':')[1], 0)) % 360
        rows.append([ref, f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", 'Top' if r['Side'] == 'top' else 'Bottom', f"{rot:.1f}"])
    return rows

def order_notes(dnp, placed, ntypes):
    """Text of jlcpcb/README.md for the design and the board file as they are now (no network needed)."""
    txt = {'rev B': README_B, 'rev C': README_C, 'rev E': README_E, 'rev F': README_F, 'rev F2': README_F2, 'rev G': README_G}.get(D.REV, README_D).replace('@DNP@', ', '.join(dnp))
    if '@TYPES@' in txt:
        import pcbnew, gen_pcb
        b = pcbnew.LoadBoard(PCB); bb = b.GetBoardEdgesBoundingBox()
        joints = sum(len(list(fp.Pads())) for fp in b.GetFootprints() if fp.GetReference() in placed)
        TRK, CLR, VIA, VDR = gen_pcb.rules()
        ntr = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'); nvi = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
        RA = getattr(D, 'RAILS', None); bw, bh = pcbnew.ToMM(bb.GetWidth()) - 0.1, pcbnew.ToMM(bb.GetHeight()) - 0.1
        b.BuildConnectivity(); nopen = b.GetConnectivity().GetUnconnectedCount(False)
        byval = lambda v: '・'.join(sorted((r for r, q in D.PARTS.items() if q[2] == v), key=lambda r: (r[0], int(''.join(ch for ch in r if ch.isdigit())))))
        fix = 2 * 8.21                         # price table: 1-29 boards need two fixtures
        num = lambda v: ('%.2f' % v).rstrip('0').rstrip('.') if abs(v * 10 - round(v * 10)) > 1e-9 else '%.1f' % v
        rep = [('@FIX2@', '%.0f' % (assembly_estimate(ntypes, joints, 2) + fix)), ('@FIX5@', '%.0f' % (assembly_estimate(ntypes, joints, 5) + fix)),
               ('@NTRACKS@', str(ntr)), ('@NVIAS@', str(nvi)), ('@NOPEN@', str(nopen)), ('@SCHOTTKY@', byval('B5819W')),
               ('@ORIENT@', orientation_notes(b, D)), ('@MASKWEB@', mask_web_note(b)), ('@BRIDGES@', bridge_note(b, D)), ('@SENSE@', sense_note(dnp))]
        if RA:                                 # every number of the rails in the notes comes from the design; check_jlc.py measures the railed board against JLCPCB's limits
            pw = bw + 2 * (RA['gap'] + RA['width']); small_first = (bw, bh + 10.0) if bh <= bw else (bw + 10.0, bh)
            rep += [('@PANEL@', '%.1f × %.1f' % (pw, bh)), ('@PANEL_X@', '%.1f x %.1f' % (pw, bh)), ('@SIZE_X@', '%.1f x %.1f' % (bw, bh)),
                    ('@PANELB@', '%.1f × %.1f' % (bw + 10.0, bh)), ('@PANELB_X@', '%.1f x %.1f' % (bw + 10.0, bh)),
                    ('@FORMB@', '%.1f × %.1f' % small_first), ('@FORMB_X@', '%.1f x %.1f' % small_first),       # the order form adds 10 mm to the smaller dimension
                    ('@RAILW@', num(RA['width'])), ('@GAP@', num(RA['gap'])), ('@RAILLEN@', num(bh - RA.get('end_gap', 0.0))), ('@ENDGAP@', num(RA.get('end_gap', 0.0))),
                    ('@NTABS@', str(len(RA['tabs']['L']))), ('@TABW@', num(RA['tab'])), ('@HOLE@', num(RA['hole'])), ('@NHOLES@', str(RA['holes'])),
                    ('@WEB@', num(RA['pitch'] - RA['hole'])), ('@RIDGE@', num(RA['hole_out'])), ('@NFID@', str(len(RA['fiducials']))), ('@FIDIN@', num(RA['fid_inset'])),
                    ('@NTOOL@', str(len(RA.get('tooling', ())))), ('@TOOLD@', num(RA.get('tooling_d', 0.0)))]
            assert len(RA['tabs']['L']) == len(RA['tabs']['R']), 'the notes describe the same number of tabs on both rails'
        else: rep.append(('@PANEL@', '-'))
        for k, v in rep: txt = txt.replace(k, v)
        for k, v in (('@TYPES@', str(ntypes)), ('@PARTS@', str(len(placed))), ('@JOINTS@', str(joints)), ('@PRICEDATE@', JLC_PRICE['date']),
                     ('@EST2@', '%.0f' % assembly_estimate(ntypes, joints, 2)), ('@EST5@', '%.0f' % assembly_estimate(ntypes, joints, 5)),
                     ('@SIZE@', '%.1f × %.1f' % (pcbnew.ToMM(bb.GetWidth()) - 0.1, pcbnew.ToMM(bb.GetHeight()) - 0.1)),
                     ('@TRACK@', '%.2f' % TRK), ('@CLEAR@', '%.2f' % CLR), ('@VIA@', '%.1f' % VIA), ('@VDR@', '%.1f' % VDR)):
            txt = txt.replace(k, v)
        left = sorted(set(re.findall(r'@[A-Z0-9_]+@', txt)))
        if left: raise SystemExit('order notes: placeholders without a value: %s' % left)
    return txt

def main():
    os.makedirs(OUT, exist_ok=True)
    if getattr(D, 'JLC_RULES', False) and os.environ.get('FC_ALLOW_UNROUTED') != '1': routed_or_exit()
    # ---- BOM, CPL ----
    bom, dnp, placed, ntypes = bom_table()
    with open(os.path.join(OUT, 'bom_jlc.csv'), 'w', newline='') as f: csv.writer(f).writerows(bom)
    with open(os.path.join(OUT, 'cpl_jlc.csv'), 'w', newline='') as f: csv.writer(f).writerows(cpl_table(dnp))
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
    with open(os.path.join(OUT, 'README.md'), 'w') as f: f.write(order_notes(dnp, placed, ntypes))
    print('written:', OUT, 'DNP:', dnp)

if __name__ == '__main__':
    main()
