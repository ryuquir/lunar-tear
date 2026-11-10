# Raspberry Pi 系ボードによるエミュレーション方式（Mode B）調査ノート

（作成中・途中保存版。調査日 2026-11-10）

## 5 V インターフェース

### Takeaway
RP2350 の GPIO0–25（QFN-60 / RP2350A）および ADC 兼用でない Bank0 GPIO は「Digital IO (FT)」で、IOVDD=3.3 V 給電中に限り 5.5 V まで耐える。ADC 兼用ピン（RP2350A: GPIO26–29、RP2350B: GPIO40–47）は FT ではない。RP2040 は 5 V 非耐性（VPIN 最大 IOVDD+0.5 V）。

### Cited Findings
- RP2350 データシート Table 1673: "Digital IO (FT) … very little current flows into the pin whilst it is below 3.63 V and IOVDD is 0 V. Additionally, they will tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V." — [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
- 絶対最大定格: Voltage at IO VPIN = −0.5〜IOVDD+0.5 V（通常ピン）、VPIN_FT = −0.5〜5.5 V（条件 IOVDD=3.3 V） — [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
- ピン表: GPIO0–25 は Digital IO (FT)、GPIO26_ADC0〜GPIO29_ADC3 は "Digital IO / Analogue"（FT ではない） — [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
- 公式発表 (2025-07-29): "RP2350 is now officially 5V tolerant!" ／ "keep IOVDD powered when 5V is applied to any GPIO pad, otherwise the pad will be damaged." — [Raspberry Pi News: RP2350 A4](https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/)
- RP2040 データシート: FT ピンは「IOVDD=0 V で 3.63 V 未満なら電流がほぼ流れない」だけで 5 V 耐性の記述なし。絶対最大 VPIN = IOVDD+0.5 V — [RP2040 Datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
- RP2350-E9: "Increased leakage current on Bank 0 GPIO when pad input is enabled"、Affects: RP2350 A2。入力が不定領域にあると約 120 µA を吐き出して約 2.2 V に保持、内蔵プルダウンでは引き下げ不可、8.2 kΩ 以下で引けば回避。内蔵プルアップは機能 — [RP2350 Datasheet Appendix D.5.1](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
- データシート Appendix C.2.1: E9 の修正は「Stepping A3 introduces…」として記載（A3 で修正、A4 が量産版）。公式ブログは A4 で修正と表現（A3 は限定生産の中間ステッピング） — [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf); [Raspberry Pi News](https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/)
- 公式ブログ: A2 生産終了、A4 は A2 のドロップイン置換、"Eventually all Pico 2 products will use the A4 stepping"、約 3 万個の A3 在庫を Pico 2 / Pico 2 W に使用、ステッピングはパッケージ上面の刻印で識別 — [Raspberry Pi News](https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/)

### Inferences
- （未整理、後で追記）

### Gaps
- （後で追記）
