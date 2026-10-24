#!/usr/bin/env python3
"""Produce the JLCPCB order package (PCB + SMT assembly) in hardware/jlcpcb/:
   gerbers.zip, bom_jlc.csv (Comment, Designator, Footprint, LCSC Part #), cpl_jlc.csv (Designator, Mid X, Mid Y, Layer, Rotation).
LCSC part numbers come from hardware/jlc_parts.json (edit to substitute parts)."""
import os, sys, csv, json, subprocess, shutil
sys.path.insert(0, os.path.dirname(__file__))
import os as _os, importlib as _il
_DESIGN = _os.environ.get('FC_DESIGN', 'design')
D = _il.import_module(_DESIGN)
HW_LIB = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'hardware'))   # custom symbols/footprints
HW = _os.path.abspath(_os.environ.get('FC_HW_DIR', HW_LIB))                                                        # outputs
OUT = os.path.join(HW, 'jlcpcb'); PCB = os.path.join(HW, 'famicart.kicad_pcb')
PARTS_JSON = os.path.join(HW, 'jlc_parts.json')

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
 'S29GL01GS 1Gbit NOR (x8 use)': ('C2684783', 'S29GL01GS10TFI010', 'Infineon 1 Gbit (64M x 16) parallel NOR, TSOP-56, 100 ns; used as 64M x 8. Alt: S29GL512S10TFI010 = C393876 (64 MB), S29GL128S10TFI010 = C914940 (16 MB) -- same pinout'),
 'FM28V100 128Kx8 F-RAM (WRAM/save)': ('C66026', 'FM28V100-TGTR', 'Infineon/Cypress 1 Mbit parallel F-RAM, 32-pin TSOP-I (8 x 13.4 mm); non-volatile save RAM, no battery'),
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
 'USB-C PRG/mapper (U1)': ('C165948', 'TYPE-C-31-M-12', 'Korean Hroparts'), 'USB-C CHR (U2)': ('C165948', 'TYPE-C-31-M-12', 'Korean Hroparts'),
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
- **Layers 4**（F.Cu 信号 / In1 GND プレーン / In2 +3V3 プレーン / B.Cu 信号）/ Dimensions 90 x 46.1 mm / **PCB Thickness 1.2 mm**
- Surface Finish **ENIG** / **Gold Fingers: Yes** → **Bevelling: 30°** / Copper 1 oz / Via Covering: Tented / Impedance Control: No
- 層構成は JLC の標準 4 層スタック（JLC04161H-1080 等、1.2 mm 指定可）で可。Min Track/Spacing 0.15/0.15 mm、Via 0.5/0.25 mm（標準仕様内）。

## SMT Assembly（PCB Assembly → Assembly Side: Top + Bottom）
- BOM: `bom_jlc.csv` / CPL: `cpl_jlc.csv`（両面実装。表: RP2350B x2・水晶・USB-C x2・スイッチ・LDO・単ゲート、裏: NOR フラッシュ x2・SRAM x2・74LVC541/245/139/00・パスコン）
- 実装しない部品（DNP）: @DNP@（スルーホールのピンヘッダ J2/J5/J6 と、部品の無いジャンパ／パッド）
- 部品プレビュー画面で **極性と回転** を必ず確認: U1/U2 RP2350B（1 番ピン）、U5/U6 S29GL01GS（TSOP-56 の 1 番ピン・マーク側）、U7/U8 IS62WV5128、U3/U4 W25Q16、U28 AMS1117（タブ = VOUT）、D1/D2 ショットキー、D3 LED、Y1/Y2 水晶、J3/J4 USB-C。
- 拡張部品: U1/U2（C42415655）、U5/U6（C2684783、在庫少。切れている場合は同ピン配置の S29GL512S = C393876 / S29GL128S = C914940 に差し替え可。容量が変わるだけでファームは自動認識）、U7/U8（C1348955）、Y1/Y2（C20625731）、L1/L2（C42411119）。
- 両面実装のため、裏面に TSOP-56 x2 と TSOP-32 x2 が載る。JLC の「Bottom side」実装費が追加になる。

## 費用の目安（5 枚、2025–26 年の JLCPCB 価格帯、送料・税別）
- PCB 5 枚（4 層・金フィンガー・ENIG・1.2 mm）: 約 US$ 60–90
- 実装（両面、約 135 点/枚）: セットアップ約 US$ 25（両面）+ 部品代（S29GL01GS 約 US$ 9 x2、IS62WV5128 約 US$ 8 x2、RP2350B 約 US$ 1.5 x2、他 US$ 6–8/枚 → 約 US$ 43/枚）＋実装費 → 5 枚で約 US$ 260–320
'''

def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(PARTS_JSON):
        json.dump(DEFAULT_PARTS, open(PARTS_JSON, 'w'), indent=1, ensure_ascii=False)
    parts = json.load(open(PARTS_JSON))
    # ---- BOM ----
    groups = {}
    for ref, (lib, sym, val, fp, _) in D.PARTS.items():
        key = val.split(' (')[0]
        groups.setdefault((key, fp), []).append(ref)
    dnp = []
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
            w.writerow([comment or key, ','.join(refs), fp.split(':')[1], lcsc])
    # ---- CPL via kicad-cli pos export ----
    pos = os.path.join(OUT, 'pos.csv')
    subprocess.run(['kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '-o', pos, PCB], check=True, capture_output=True)
    rows = list(csv.DictReader(open(pos)))
    with open(os.path.join(OUT, 'cpl_jlc.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for r in rows:
            ref = r['Ref']
            if ref in dnp or ref == 'J1': continue
            w.writerow([ref, f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", 'Top' if r['Side'] == 'top' else 'Bottom', f"{float(r['Rot']):.1f}"])
    os.remove(pos)
    # ---- Gerbers ----
    fab = os.path.join(HW, 'fab'); z = os.path.join(OUT, 'gerbers.zip')
    if os.path.exists(z): os.remove(z)
    shutil.make_archive(z[:-4], 'zip', fab)
    with open(os.path.join(OUT, 'README.md'), 'w') as f:
        f.write({'rev B': README_B, 'rev C': README_C}.get(D.REV, README_D).replace('@DNP@', ', '.join(dnp)))
    print('written:', OUT, 'DNP:', dnp)

if __name__ == '__main__':
    main()
