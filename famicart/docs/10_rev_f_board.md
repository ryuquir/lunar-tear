# 10 rev F 基板（rev E + SFC 型コプロセッサ用 Pico 2 ×2）

[06 rev E](06_rev_e_plan.md) と同じ部品選定ルール（JLCPCB Basic 部品のみ、手はんだは秋月のモジュール）。コプロセッサの使い方は [09](09_coproc_abi.md)。

## 構成

| 部品 | 位置 | 役割 | 接続 |
|---|---|---|---|
| U1 Pico 2 | 表・下段 | CPU バス（rev E と同じ） | — |
| U2 Pico 2 | 裏・下段 | PPU バス（rev E と同じ） | — |
| U3 XIAO RP2350 | 表・上段右 | IRQ・拡張音源（rev E と同じ） | — |
| **U4 Pico 2** | 表・上段左 | CPU 側コプロセッサ（SA-1・DSP-n など） | A0-14・/ROMSEL・/WS は U1 と共有（1 kΩ の後ろ）、D0-7 は専用の 1 kΩ アレイ ×2 |
| **U5 Pico 2** | 裏・上段 | PPU 側コプロセッサ（Super FX・Cx4 など） | PA0-13・/RD は U2 と共有、PD0-7 は専用の 1 kΩ アレイ ×2 |

- U4・U5 は LINK にも 1 kΩ でつながり、電源は各自の B5819W から取る。
- U4・U5 を載せなければ rev E と同じに動く（ファームが窓を使わない）。

## 基板

- **外形 90 × 70.1 mm**（本体 59.4 mm + 端子タブ 10.7 mm）。rev E の本体を上に 24 mm 延ばし、上段に U4・U5・XIAO を置いた。
- 2 層、トラック/クリアランス 0.15 mm、ビア 0.5/0.25 mm。
- **配線結果: 未接続 0、DRC エラー 0**（トラック 2206 本、ビア 234 個。警告 57 件は KiCad 標準ライブラリとの照合とシルクのみ）。
- 純正の通常シェルには入らない。大型カセットのシェル（外寸で通常より約 27 mm 高い）に入る見込みだが、基板外形・ネジ穴の実寸は調査中（`tools/pcb/design_revf.py` の `BODY_H` と外形で合わせる）。

## 部品表（`hardware/revf/jlcpcb/`、JLCPCB API で Basic・在庫を確認済み）

| 部品 | LCSC | 数 |
|---|---|---|
| 抵抗アレイ 1kΩ×4 0603 | C20197 | 16 |
| 抵抗 100kΩ 0603 | C25803 | 10 |
| 抵抗 1kΩ 0603 | C21190 | 8 |
| 抵抗 2.2kΩ 0603 | C4190 | 6 |
| B5819W | C8598 | 5 |
| 2N7002 | C8545 | 2 |
| 1N4148WS | C2128 | 2 |
| コンデンサ 10nF 0603 | C57112 | 2 |
| コンデンサ 10µF 0805 | C15850 | 2 |
| タクトスイッチ TS-1187A | C318884 | 1 |
| Raspberry Pi Pico 2（手はんだ） | 秋月 129604（¥990） | 4 |
| Seeed XIAO RP2350（手はんだ） | 秋月 129619（¥1,100） | 1 |

PCBA は 10 種・54 点、手はんだはモジュール 5 個。

## 生成

```sh
cd tools/pcb
export FC_DESIGN=design_revf FC_HW_DIR=../../hardware/revf FC_LAYERS=2
python3 gen_sch.py && FC_TRACK=0.15 FC_CLEAR=0.15 FC_VIA=0.5 FC_VIA_DRILL=0.25 python3 route_pcb.py
python3 gen_bom.py && python3 gen_jlc.py
```
