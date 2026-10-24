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
        f.write((README_B if D.REV == 'rev B' else README_C).replace('@DNP@', ', '.join(dnp)))
    print('written:', OUT, 'DNP:', dnp)

if __name__ == '__main__':
    main()
