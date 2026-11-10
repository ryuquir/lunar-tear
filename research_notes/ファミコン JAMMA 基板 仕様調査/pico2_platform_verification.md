# Pico 2 / RP2350 プラットフォーム主張の検証（第 2 パス）

調査日: 2026-11-10。表記ルール: 出典付きの事実は「Cited Findings」、筆者の推論は「推論」と明記、確認できなかった事項は「未確認」。ページ番号は「印刷ページ（PDF ページ）」の順で示す。

一次資料（本調査で 2026-11-10 にダウンロードし pdftotext で本文確認）:
- RP2350 Datasheet, Release 8, Build date 01/10/2026, Build version 80d627281ed5 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet, Build date 03/07/2026, Build version d4e0f1799616 — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf

（作業中: 以下のセクションは調査進行に合わせて追記）

## 1. RP2350 の 5 V 耐性・フェイルセーフ・Pico 2 の GPIO

### Takeaway
RP2350 の「Digital IO (FT)」ピンは IOVDD が 3.3 V 給電中に限り 5.5 V まで、IOVDD=0 V（無給電）では 3.63 V までしか許されない。Pico 2 で引き出される GPIO は GPIO0–22 と GPIO26–28 の 26 本で、5 V 耐性なのは GPIO0–22 の 23 本のみ。Pico 2 データシートの「無給電でも電圧を印加してよい」という記述は 3.63 V 以下の話であり、無給電中に 5 V を印加してよいという意味ではない。

### Cited Findings
- RP2350 Datasheet §1 Introduction, p.13 (PDF p.14): "GPIOs are 5 V-tolerant (powered) and 3.3 V-failsafe (unpowered)" — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- 同 Table 1673 "Pin Types", p.1331 (PDF p.1332): "Digital IO (FT) … Fault Tolerant Digital. These pins are described as Fault Tolerant, which in this case means that very little current flows into the pin whilst it is below 3.63 V and IOVDD is 0 V. Additionally, they will tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V. These pins have enhanced ESD protection." — 同上
- 同 Table 1680 "Absolute maximum ratings", p.1335 (PDF p.1336): VPIN (Standard) −0.5〜"IOVDD + 0.5" V。VPIN_FT: IOVDD=3.3 V で −0.5〜5.5 V、IOVDD=2.5 V で 4.2 V、IOVDD=1.8 V で 3.63 V、**IOVDD=0V で 3.63 V**、Comment "IOVDD must be present"。— 同上
- 同 Table 1683, p.1336 (PDF p.1337): "Input Voltage High (FT)" IOVDD=3.3 V で Min 2 V / Max 5.5 V、Comment "IOVDD must be powered to tolerate input voltages above 3.63V"。VIL(3.3 V) Max 0.8 V。VOH(3.3 V) Min 2.62 V（"IOH = 2, 4, 8 or 12mA depending on setting"）、VOL(3.3 V) Max 0.5 V。IIN 最大 1 µA。— 同上
- 同 Table 1674 "GPIO pins", p.1332–1333 (PDF p.1333–1334): QFN-60（RP2350A）では GPIO0–GPIO25 が "Digital IO (FT)"、GPIO26_ADC0〜GPIO29_ADC3 は "Digital IO / Analogue"（Power Domain "IOVDD / ADC_AVDD"）。QFN-80（RP2350B）では GPIO0–39 が FT、GPIO40_ADC0〜GPIO47_ADC7 が "Digital IO / Analogue"。全 GPIO の Reset State は "Pull-Down"。— 同上
- 同 §9.3 "Reset state", p.539 (PDF p.540): "At first power up, Bank 0 IOs … assume the following state: Output buffer is high-impedance / Input buffer is disabled / Pulled low / Isolation latches are set to latched" — 同上
- Pico 2 Datasheet p.8 (PDF p.9): 内部用途 "GPIO29 IP Used in ADC mode (ADC3) to measure VSYS/3"、"GPIO25 OP Connected to user LED"、"GPIO24 IP VBUS sense"、"GPIO23 OP Controls the on-board SMPS Power Save pin"。40 ピン上の GPIO・GND 以外は VBUS(40)、VSYS(39)、3V3_EN(37)、3V3(36)、ADC_VREF(35)、AGND(33)、RUN(30) の 7 本 — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- Pico 2 Datasheet p.14 (PDF p.15): "The Pico 2 exposes 26 of the 30 possible RP2350 GPIO pins by routing them straight out to Pico 2 header pins. GPIO0 to GPIO22 are digital only and GPIO 26-28 are able to be used either as digital GPIO or as ADC inputs"、"the ADC capable GPIO26-29 have an internal reverse diode to the IOVDD (3V3) rail and so the input voltage must not exceed IOVDD plus about 300 mV. Also, if the RP2350 is unpowered, applying a voltage to these GPIO pins will ‘leak’ through the diode into the IOVDD rail. Normal digital GPIO pins 0-25 (and also the debug pins) do not have this restriction and therefore voltage can safely be applied to these pins when RP2350 is unpowered." — 同上
- Pico 2 Datasheet p.14: "The Raspberry Pi Pico 2′s GPIO is powered from the on-board 3.3 V rail and is therefore fixed at 3.3 V." — 同上
- Pico 2 Datasheet p.9 (PDF p.10): "RUN is the RP2350 enable pin, and has an internal (on-chip) pull-up resistor to 3.3 V of about ~50 kΩ."、"3V3_EN connects to the on-board SMPS enable pin, and is pulled high (to VSYS) via a 100 kΩ resistor." VSYS 範囲 1.8–5.5 V。— 同上

### 推論
- Pico 2 の 40 ピン上で 5 V 信号を直結してよいのは **GPIO0–22 の 23 本**。GPIO26–28 は 5 V 不可（IOVDD+約 0.3 V まで）。
- **リセット中（RUN=Low）**: Pico 2 の 3.3 V（RT6150 SMPS 出力）は RUN と無関係に VSYS から生成されるため IOVDD は給電されており、FT ピンの 5.5 V 耐性条件（"provided IOVDD is powered to 3.3 V"）は満たされる。データシートにリセット中の例外記述は見当たらない（推論、リセット中に限定した明文は未確認）。
- **無給電中（IOVDD=0 V）**: 絶対最大 3.63 V。アーケード +5 V が先に立ち上がり、カート／実 CPU 側の 5 V 信号（あるいはプルアップ）が Pico より先に High になる、または Pico の 3.3 V が先に落ちる状態は絶対最大定格違反。Pico 2 を JAMMA +5 V から VSYS で給電すれば RT6150 の立ち上がり（数 ms 程度、本調査では未計測）の間だけ違反状態があり得る。対策: (a) 5 V 側ドライバを 74HC/74HCT の OE で Pico の 3V3 が確立するまで Hi-Z に保つ、(b) 直列抵抗（例 1–10 kΩ）で故障電流を制限（ただし 3.63 V 超で "very little current" の保証外となる点は変わらない）、(c) 5 V→3.3 V 方向は 3.3 V 給電の 74LVC 系（5 V 耐性入力）を挟む。最も部品の少ない現実解は (a)＋(b)（推論）。
