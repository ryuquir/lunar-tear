# NESRGB 方式（EXT＋シャドウパレット＋スプライト/BG 判定）を Pico 2（RP2350）で実装する工学的実現性調査

調査日: 2026-11-10（作業中ドラフト — 途中保存）。
表記: 「Cited Findings」= 出典付き事実（URL 明記）。「Inferences」= **推論**（筆者の判断）。未確認事項は **未確認**。

一次資料（本調査でダウンロードして pdftotext で本文確認）:
- RP2350 Datasheet, Release 8, Build date 01/10/2026, Build version 80d627281ed5 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- Hardware design with RP2350 — https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- TI SN74HC245 datasheet — https://www.ti.com/lit/ds/symlink/sn74hc245.pdf

## 1. タイミング予算（途中保存）

- PIO: "On every system clock cycle, each state machine fetches, decodes and executes one instruction. Each instruction takes precisely one cycle, unless it explicitly stalls" — RP2350 Datasheet §11.2.2
- PIO 入力同期: "each GPIO input is equipped with a standard 2-flipflop synchroniser. This adds two cycles of latency"、INPUT_SYNC_BYPASS で GPIO 毎にバイパス可 — §11.5.6.3
- clk_sys 最大 150 MHz（Table 573）。PLL 制約: FREF/REFDIV ≥ 5 MHz、VCO 750–1600 MHz、FBDIV 16–320、POSTDIV1/2 1–7 — §8.6.3
- PLL の FREF は XOSC の XIN に直結。XIN 外部クロック入力は最大 50 MHz。GPIN0/1 は clk_sys 等に使えるが 50 MHz まで（PLL の基準にはならない）— §8.1.2.4, §8.6.1
- Pico 2 の水晶は Abracon ABM8-272-T3（12 MHz, ±30 ppm）— Pico 2 Datasheet, Hardware design with RP2350 §4
- 12 MHz 水晶から到達可能な 21.477272 MHz 近似（整数 PIO 分周）: 最良 21.500000 MHz（+1058 ppm、FBDIV=86, POSTDIV 4×2, clk_sys=129 MHz, ÷6）。150 MHz÷7 = 21.428571 MHz（−2268 ppm）— 計算（scripts/pll.py）
- 2A03 書込み: lidnariq 実測「M2 rises 70-90ns after R/W does」「The 2A03 pulls D0 up about 250-260ns after R/W falls … roughly 100ns after M2 rises」 — https://forums.nesdev.org/viewtopic.php?t=19483
- 74HC245 VIH = 3.15 V @VCC 4.5 V（3.3 V 出力では満たさない）、tpd 21 ns typ/26 ns max(−40〜85°C) @4.5 V — TI SN74HC245
- 2A03/2C02 の VOH ≈ 4 V（lidnariq 実測）— https://forums.nesdev.org/viewtopic.php?t=19656&start=15 。入力閾値は未測定「you just assume it's TTL thresholds」— https://www.nesdev.org/wiki/Talk:Cartridge_connector
- TinyNES は 3.3 V MEMS 発振器 SIT2001BC-S2-33N-21.477270 → PL133-37 → 30 Ω（R3-R5）で CPU/PPU CLK を駆動 — https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_BOM.csv
