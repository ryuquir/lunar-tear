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

## 2. エラッタ RP2350-E9 とステッピング

### Takeaway
E9 は「入力イネーブル時、不定電圧域でパッドが約 120 µA を吐き出し約 2.2 V に張り付く（内蔵プルダウンが効かない）」不具合で、影響は A2 のみ、A3 で修正（A3 は限定生産、A4 が量産版）。2026 年 11 月に日本で買える Pico 2 のステッピングは、一次資料（秋月の商品ページ）に記載が無く未確認。

### Cited Findings
- RP2350 Datasheet Appendix D.5.1 "RP2350-E9", p.1358–1359 (PDF p.1359–1360): "Summary: Increased leakage current on Bank 0 GPIO when pad input is enabled"、"Affects: RP2350 A2"、"For GPIO pads 0 through 47"、"the pad can source current … typically around 120μA). This leakage will hold the pad at around 2.2 V"、"The pad pull-down (if enabled) is significantly weaker than the leakage current"、"Driving / pulling the pad input low with a low impedance source of 8.2 kΩ or less will overcome the erroneous leakage"、"The pad pull-up still works."、"This doesn’t affect the pull-down behaviour of the pads immediately following a PoR or RUN reset because the input enable field is initially clear."、"PIO programs can’t toggle pad controls and therefore external pulls may be required"、"Fixed by: RP2350 A3, Documentation" — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- 同 Appendix C.2.1 "Hardware changes", p.1349 (PDF p.1350): "Stepping A3 introduces the following hardware fixes and mitigations: … Fix Appendix D.5.1. RP2350-E9: increased leakage current on Bank 0 GPIO when pad input is enabled. The pad circuit is modified to eliminate the erroneous leakage path through the input buffer." 判別法: "check the package markings … read the CHIP_ID .REVISION register field, or call the rp2350_chip_version() SDK function" — 同上
- 同 §1.4 Table 7 "RP2350 version history", p.21 (PDF p.22): "A2 Initial release / A3 Internal development, samples, and limited production / A4 Production version" — 同上
- Raspberry Pi 公式ブログ（2025-07-29）: "we’ve fixed Erratum 9"、"RP2350 is now officially 5V tolerant!"、"Just make sure to keep IOVDD powered when 5V is applied to any GPIO pad, otherwise the pad will be damaged."、"We have already ceased production of A2"、"approximately 30,000 units of A3 inventory will be used to build Pico 2 and Pico 2 W products"、"Eventually all Pico 2 products will use the A4 stepping."、"The stepping identifier can be found on the top of the package" — https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/ （2026-11-10 取得）
- 秋月電子 Raspberry Pi Pico 2（販売コード 129604、型番 SC1631、発売日 2024/09/18）の商品ページ本文にステッピング（A2/A3/A4）の記載なし（2026-11-10 取得、"A4"/"A2"/"ステッピング" で全文検索して商品説明中に該当なし） — https://akizukidenshi.com/catalog/g/g129604/

### 推論
- E9 は 5 V 耐性とは別問題。本基板で影響するのは「内蔵プルダウンに頼る入力」と「Hi-Z になるバス（カートのデータバスをプルダウンで読む等）」。外付けプルアップ／8.2 kΩ 以下のプルダウン、またはバスを常に駆動される状態で読む設計なら A2 でも問題にならない。設計を A2/A3/A4 のどれでも動くようにしておけば、ステッピング未確認のリスクは消える。
- 秋月の在庫ロットが A4 かどうかは購入品の刻印確認（または `rp2350_chip_version()`）で判断するしかない（未確認）。

## 3. 出力駆動: 3.3 V 出力で 5 V 入力を駆動できるか
（§3 は下に追記）

## 4. PIO・クロック・DMA（バス作業に必要な事実）

### Takeaway
RP2350 は PIO ブロック 3 個×SM 4 個＝12 SM、各 SM は 1 クロック 1 命令、命令メモリは各ブロック 32 語。GPIO 入力には 2 段 FF 同期器があり（2 サイクル遅延）、GPIO ごとに INPUT_SYNC_BYPASS で外せる。データシート上の最大システムクロックは 150 MHz（pico-infonesPlus は 252 MHz にオーバークロックして動作）。

### Cited Findings（すべて RP2350 Datasheet — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf）
| 項目 | データシートの記述（原文） | ページ |
|---|---|---|
| 最大クロック | "Dual Cortex-M33 or Hazard3 processors at 150 MHz"、"a 150 MHz system clock, the maximum supported on RP2350" | p.13 / p.531 (PDF p.14 / p.532) |
| PIO 数 | "RP2350 contains 3 identical PIO blocks"、"There are three PIO blocks, each containing four state machines"、"12 × PIO state machines" | p.791 / p.13 |
| 1 命令/クロック | "On every system clock cycle, each state machine fetches, decodes and executes one instruction. Each instruction takes precisely one cycle, unless it explicitly stalls (such as the WAIT instruction). Instructions may insert a delay of up to 31 cycles" | p.794 (PDF p.795) |
| 命令メモリ | "Each PIO instance has a 32-slot instruction memory, which all 4 state machines can see." | p.794 |
| 入力同期器 | "each GPIO input is equipped with a standard 2-flipflop synchroniser. This adds two cycles of latency to input sampling"、"It is possible to bypass these synchronisers, on a per-GPIO basis … Synchronisers are bypassed by setting the corresponding bit in INPUT_SYNC_BYPASS." | §11.5.6.3, p.824 (PDF p.825) |
| side-set | "Side-set is where a state machine drives a small number of GPIOs in addition to the main side effects of the instruction"、"Side-set … is not affected by stalls, and always takes place on the first cycle of the attached instruction."、".side_set <count> (opt) (pindirs) … pindirs may be specified to indicate that the side set values should be applied to the PINDIRs and not the PINs" | p.794, p.798, p.800 |
| 方向制御 | "Adds PINDIRS as a destination for MOV … changing the direction of all OUT-mapped pins with a single instruction: MOV PINDIRS, NULL or MOV PINDIRS, ~NULL"；SET/OUT の宛先に PINDIRS | p.792, p.806 |
| FIFO | "Each state machine has a pair of 4-word deep FIFOs"、"SHIFTCTRL_FJOIN option can merge the two FIFOs into a single 8-entry FIFO" | §11.2.4.4, p.797 |
| DMA | "The DMA can perform one read access and one write access, up to 32 bits in size, every clock cycle. There are 16 independent …"（チャネル）、"Reduced DMA request (DREQ) latency by one cycle vs RP2040." | §12.6, p.1010 付近 / p.793 |
| バス帯域 | "at a system clock of 150 MHz, the maximum sustained bus bandwidth is 3.6 GB/s" | p.23 |
| GPIO 範囲 | "Each PIO block is still limited to 32 GPIOs at a time, but GPIOBASE selects which 32." | §11 (RP2040 との差分) |

### 推論
- Famicom CPU バス（M2 ≈ 1.79 MHz、周期約 559 ns）は 150 MHz で約 84 クロック、252 MHz で約 141 クロック。PIO で M2 に同期したアドレス出力・データ読み取りは時間的に十分余裕がある。外部クロック（M2）に同期してサンプリングする場合は同期器を残す（+2 クロック ≈ 13 ns @150 MHz）のが安全。
- ダンプ用途（Pico が M2 を自分で生成する）なら非同期性の問題自体が無く、同期器はそのままでよい。

## 5. Pico 用 NES エミュレータ・映像出力の実例

### Cited Findings
**pico-infonesPlus（リポジトリは PicoPlus-devel 組織へ移管、旧 fhoedemakers/pico-infonesPlus）**
- ライセンス GPL-3.0（LICENSE: "GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007"）。最新リリース v0.56（"v0.56 adds support for the Pico Computer 3."、リリースページの日時 2026-11-08）— https://github.com/PicoPlus-devel/pico-infonesPlus ／ https://github.com/PicoPlus-devel/pico-infonesPlus/releases （2026-11-10 取得）
- 映像: README 冒頭 "It provides NES emulation with SD card support, an integrated menu system, and HDMI video output"。README 全文に "VGA" の語は無し（grep 0 件）。設定 "Display Mode" に DVI/HDMI、"Scanline Type … HSTX boards only" — https://raw.githubusercontent.com/PicoPlus-devel/pico-infonesPlus/main/README.md
- 音声: "External Audio | Route audio to the I2S/line-out output instead of HDMI."、Pimoroni Pico DV Demo Base と Murmulator は line-out ジャック — 同上
- 速度: "The emulator overclocks the Pico in order to get the emulator working fast enough."、"Overclock | Raise the CPU clock from 252 MHz to 384 MHz. Only on HSTX boards with PSRAM, and currently only needed for Lagrange Point (JP)." — 同上
- 地域: RP2350 は PAL "✓ (native speed)"、RP2040 は "PAL/Dendy games at 60Hz instead of 50Hz" — 同上
- 拡張音源: "VRC7 expansion audio requires an RP2350 board. MMC5, VRC6, FDS and Sunsoft 5B expansion audio also work on the RP2040."、VRC7 は "only works on HSTX boards with PSRAM and requires the Overclock setting … occasional glitches" — 同上（Known Issues）
- FDS: "FDS games run on both RP2040 and RP2350 boards"、BIOS は利用者が用意（`/bios/fds-bios.rom`、8 KB）— 同上
- PSRAM: "Without PSRAM, selecting a game ROM triggers a reboot: the ROM is written to flash memory during startup … taking several seconds"、"With PSRAM … Games are loaded directly from the SD card into PSRAM" — 同上
- **対応マッパー全一覧**（`infones/InfoNES_Mapper.cpp` の `MapperTable[]` を 2026-11-10 に取得して抽出、計 157 エントリ。`{6, Map6_Init}` はコメントアウト、`{85, Map85_Init}` は `#if PICO_RP2350` 内）— https://raw.githubusercontent.com/PicoPlus-devel/pico-infonesPlus/main/infones/InfoNES_Mapper.cpp
  0 1 2 3 4 5 7 8 9 10 11 13 15 16 17 18 19 20 21 22 23 24 25 26 30 31 32 33 34 37 40 41 42 43 44 45 46 47 48 49 50 51 57 58 60 61 62 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 82 83 85(RP2350のみ) 86 87 88 89 90 91 92 93 94 95 96 97 100 101 105 107 108 109 110 111 112 113 114 115 116 117 118 119 122 133 134 135 140 151 152 153 154 155 157 159 160 180 181 182 183 184 185 187 188 189 191 193 194 196 200 201 202 206 207 208 210 222 225 226 227 228 229 230 231 232 233 234 235 236 240 241 242 243 244 245 246 248 249 251 252 255 263 268 555
  （注: テーブルに登録＝完全動作ではない。README は "some mappers are either not fully implemented or exceed memory limitations" と明記。Save state は "mapper 0,1,2,3 and 4" のみ保証。）

**PICO9918（visrealm、RP2040/RP2354A で TMS9918A を置換）**
- ライセンス: ハード CERN-OHL-S、ファーム MIT — https://github.com/visrealm/pico9918
- アナログ RGB 方式: v2.0 回路図（Date 2026-03-09、Rev 2.0）で各色 4 ビットの重み付け抵抗 DAC。R0=3.9 kΩ、R1=1.8 kΩ、R2=910 Ω、R3=470 Ω（G/B も同値。R11/R1/R7/R18 ほか 12 本）を GPIO から出力ノードへ並列接続。HSYNC/VSYNC は各 47 Ω 直列（R28/R23）。5 V ホストとの間は 74HC245（データ、5 V 給電）、74AHC126（出力、5 V 給電）、74LVC245（入力、3.3 V 給電、"3.3V ← 5V"）でバッファ — https://github.com/visrealm/pico9918/blob/main/pcb/v2.0/pico9918_v2_0_schematic.pdf （PDF を画像化して目視確認）
- VGA: 640×480@60 Hz、25.175 MHz、"12-bit RGB (4 bits per channel, 4096 colors)" — https://github.com/visrealm/pico9918/wiki/VGA-Dongle
- SCART (15 kHz): "Both modes use interlaced output at 13.5 MHz pixel clock"、PAL 720×576i ライン周波数 15,625 Hz／NTSC 720×480i 15,734 Hz、システムクロック 270 MHz または 324 MHz（13.5 MHz の整数倍）。"Composite sync is driven on pin 8"（HSYNC ピンから CSync を出す）、"The RGB outputs are held at 0 V for the whole sync pulse and back porch … The firmware does this itself."、電圧レベル: RGB ピーク 0.7 V、Sync 0 V／Black 0.3 V、全線 75 Ω 終端。SCART ドングルは HSYNC–VSYNC 間 1 kΩ のみの受動品（ブート時に導通で検出）— https://github.com/visrealm/pico9918/wiki/SCART-Output-Reference ／ https://github.com/visrealm/pico9918/wiki/SCART-RGB-AV-Dongle ／ https://github.com/visrealm/pico9918/wiki/Display-Output

**pico-extras scanvideo と 15 kHz**
- pico-extras README: "pico_scanvideo_dpi | Highly functional and stable support for parallel RGB output and VSYNC/HSYNC/DEN/CLOCK for VGA/DPI." — https://github.com/raspberrypi/pico-extras （2026-11-10 取得）
- 定義済みモード（`src/common/pico_scanvideo/vga_modes.c`）は全て 24 MHz/768 以上の水平レート（例 640×480: clock 24 MHz・h_total 800、512×576: 24 MHz・h_total 768 ≒ 31.25 kHz）で、**15 kHz のプリセットは無い**。`scanvideo_timing_t` のフィールドは clock_freq, h_active, v_active, h_front_porch, h_pulse, h_total, h_sync_polarity, v_front_porch, v_pulse, v_total, v_sync_polarity, enable_clock, clock_polarity, enable_den のみで、**CSync・インターレースの設定項目は無い** — https://raw.githubusercontent.com/raspberrypi/pico-extras/master/src/common/pico_scanvideo/vga_modes.c ／ https://raw.githubusercontent.com/raspberrypi/pico-extras/master/src/common/pico_scanvideo/include/pico/scanvideo/scanvideo_base.h
- 代替: PicoVGA（codaris/picovga-cmake フォーク）は "Now supports both RP2040 and RP2350"、出力 "TV: PAL/NTSC interlaced up to 1024×576 or 848×480"、色 "8-bit R3G3B2"、配線例 "take 8 resistors and connect them to outputs GP0 to GP7 and the RGB connector of a VGA or SCART TV. Then, connect HSync (CSync) to GP8" — https://github.com/codaris/picovga-cmake （240p プログレッシブの記載は無し）

### 推論（§5）
- 「Pico 用 NES エミュレータ＋15 kHz RGB」の既製品はやはり見つからない（第 1 パスと同結論）。必要部品は揃っている: エミュレータ核（pico-infonesPlus、GPL-3.0）、15 kHz CSync 生成の実例（PICO9918 SCART: HSYNC ピンから CSync、RGB は 4 ビット重み付け抵抗 3.9k/1.8k/910/470 Ω）。scanvideo を使う場合は timing 構造体を 15.7 kHz（例: clock 6 MHz 前後、h_total ≈ 381、v_total 262）で自作し、CSync は PIO 側で HSYNC/VSYNC を合成する改造が要る。pico-infonesPlus は HSTX/DVI 前提なので、映像出力部は差し替えになる。
- JAMMA 向け（1 Vp-p 前後ではなく 3 Vp-p 程度を要求するモニタもある）のレベル合わせは jamma_electrical_details.md の議論に従う。PICO9918 の抵抗値は 75 Ω 終端で 0.7 V を狙った値であり、そのままでは JAMMA 用には低い（推論）。

## 6. 出力駆動しきい値（§3 の内容）

### Cited Findings
| 受け側 | VIH（High と認識される最小入力） | 出典 |
|---|---|---|
| RP2350 出力（送り側） | VOH min 2.62 V（IOVDD=3.3 V、IOH=2/4/8/12 mA 設定値で）、VOL max 0.5 V | RP2350 Datasheet Table 1683, p.1336 |
| 74HC595 / 74HC165（TI SN74HC595, SCLS041J Rev. Oct 2021） | VCC=4.5 V で 3.15 V、VCC=6 V で 4.2 V（VCC=5 V の値は表に無く、0.7×VCC 換算で 3.5 V） | https://www.ti.com/lit/ds/symlink/sn74hc595.pdf §6.3 |
| 74HCT245（TI SN74HCT245） | "VCC = 4.5 V to 5.5 V … 2 V"、VIL 0.8 V | https://www.ti.com/lit/ds/symlink/sn74hct245.pdf |
| 2A03 / 2C02（NMOS） | 公式データなし。NESdev の lidnariq: "Approximately TTL thresholds."、3.3 V CPLD 駆動実験（skrasms 2009）、TinyNES が CLK を 3.3 V 駆動 | 既存ノート famicom_electrical_and_pitfalls.md §2（https://forums.nesdev.org/viewtopic.php?f=9&p=269268 ほか） |
| 74HC595 出力 → 送り側として | VOH(4.5 V, −6 mA) min 3.84 V(85 °C)… つまり 5 V 給電の 74HC は 5 V 振幅を出す | TI SN74HC595 §6.5 |
| 74HC595 の最大クロック | fclock 4.5 V で 25 MHz（−40〜85 °C, SN74HC595 列）、74HC165 は 4.5 V で 21〜31 MHz（列による） | TI SN74HC595 / SN74HC165 |

### 推論
- RP2350 の 3.3 V 出力は **TTL しきい値（VIH 2.0 V）の入力**（2A03/2C02 推定、74HCT/AHCT/LS、マスク ROM の多く）なら VOH min 2.62 V で 0.6 V 余裕があり確実に駆動できる。
- **5 V 給電の 74HC 入力**（VIH 3.15 V@4.5 V、≈3.5 V@5 V）は 3.3 V 出力では**保証外**。VOH が無負荷で 3.3 V 近くまで上がっても 5.0 V 給電時の 3.5 V に届かない。→ 3.3 V 側から 5 V ロジックへ渡す場所は 74HCT（または 74AHCT）にするか、74HC595 自体を 3.3 V 給電にする（その場合 74HC595 の出力は 3.3 V 振幅になり、カート側入力が TTL しきい値なら駆動可）。
- 参考: PICO9918 v2.0 は 3.3 V→5 V データ方向に 5 V 給電の 74HC245（VIH 3.5 V 相当）を使っている。実働品だが規格上はマージン外（推論）。
- カートリッジ側のマッパー IC（MMC1/MMC3 等、CMOS か NMOS か）の入力しきい値は一次資料未確認。ディスクリートマッパー板（UNROM: "74xx161 / 74xx32"、nesdir の Chip Type 表記）は LS/HC の区別が表記上不明 → 3.3 V 直結は保証できない（未確認）。安全側は「Pico→カートの全出力を 5 V 給電 74HCT 系経由」。

## 7. 日本版ファミコン・カートのマッパー別本数とメモリ規模

### データ源と限界
- NES Directory（nesdir.github.io、各タイトルに "Region / Class: Licensed / Catalog / Board / PCB / Mapper / PRG・CHR サイズ・CRC32・SHA1" を持つ NesCartDB 形式の静的サイト）の索引ページを 2026-11-10 に取得し、Region=Japan の 881 タイトルを集計。各タイトルの個別ページ 881 件も取得し、最初の基板バリアントの PRG/CHR サイズを抽出（3 件は 404 のため Mesen DB で補完）— https://nesdir.github.io/ ／ 例 https://nesdir.github.io/D0DF726E_Japan.html
- サイズの検証: Mesen2 の `MesenNesDB.txt`（"Generated on 2022-07-21 using: NewRisingSun's NES 2.0 header database (2021-12-25), NesCartDB (dated 2017-08-21), Nestopia UE's latest DB"）と CRC で突合し、881 件中 871 件で PRG/CHR サイズ一致、7 件不一致（版違いと推定）— https://raw.githubusercontent.com/SourMesen/Mesen2/master/UI/Dependencies/MesenNesDB.txt
- nescartdb.com は Cloudflare によりアクセス拒否（2026-11-10、curl/Playwright とも "Sorry, you have been blocked"）。
- 国内市販 ROM カセットの総数は「市販のファミコンカセット全1053本」（ねとらぼ 2021-07-20） — https://nlab.itmedia.co.jp/cont/articles/3322975/ 。よって集計は全体の約 84%（881/1053）の標本で、未収録の約 170 本の分布は不明。

### マッパー別本数（日本、ライセンス品 881 本中、多い順・累積）
| iNES mapper | 主な基板 | 本数 | 割合 | 累積 |
|---|---|---|---|---|
| 1 | MMC1 (HVC-S*ROM) | 236 | 26.8% | 26.8% |
| 4 | MMC3 (HVC-T*ROM) | 142 | 16.1% | 42.9% |
| 0 | NROM | 110 | 12.5% | 55.4% |
| 2 | UNROM | 83 | 9.4% | 64.8% |
| 3 | CNROM | 57 | 6.5% | 71.3% |
| 206 | Namco 108 系 | 30 | 3.4% | 74.7% |
| 19 | Namco 163（拡張音源あり） | 20 | 2.3% | 77.0% |
| 16 | Bandai FCG / LZ93D50(+24C02) | 15 | 1.7% | 78.7% |
| 18 | Jaleco SS88006 | 15 | 1.7% | 80.4% |
| 5 | MMC5 | 14 | 1.6% | 82.0% |
| 210 | Namco 175/340 | 12 | 1.4% | 83.3% |
| 23 | Konami VRC2/VRC4 | 10 | 1.1% | 84.4% |
| 87 | Jaleco/Konami 簡易 | 10 | 1.1% | 85.6% |
| 33 | Taito TC0190 | 9 | 1.0% | 86.6% |
| 69 | Sunsoft FME-7 / 5A / 5B | 9 | 1.0% | 87.6% |
| 185 | CNROM+保護 | 7 | 0.8% | 88.4% |
| 25, 66, 75, 32, 80 | VRC4/GxROM/VRC1/Irem G-101/Taito X1-005 | 各 6 | 各 0.7% | 91.8% |
| 152, 159, 82 | — | 各 4 | — | 93.2% |
| 68, 184, 7, 140, 65, 88, 10, 72 | — | 各 3 | — | 95.9% |
| 118, 48, 26, 70, 93, 67, 21, 22, 78, 85 | — | 各 2 | — | 98.2% |
| 24, 180, 154, 95, 207, 97, 34, 76, 9, 86, 92, 77, 96, 73, 94, 89 | — | 各 1 | — | 100% |
（全 58 種のマッパー。上位 5 種=71.3%、10 種=82.0%、15 種=87.6%、20 種=91.8%。）

- 上記 58 種は**すべて pico-infonesPlus の MapperTable に登録あり**（突合結果、85 は RP2350 ビルドのみ）。ただし登録＝完全動作ではない（§5）。

### 拡張音源・特殊マッパーを使う主な日本タイトル（nesdir より）
| 種別 | mapper | タイトル（基板） |
|---|---|---|
| Konami VRC6 音源 | 24 / 26 | 悪魔城伝説 Akumajou Densetsu (KONAMI-VRC-6, 24)、魍魎戦記MADARA、エスパードリーム2 (26) |
| Konami VRC7 FM 音源 | 85 | Lagrange Point（VRC7 音源使用）、Tiny Toon Adventures 2（同チップ。音源使用の有無は未確認） |
| Namco 163（音源内蔵チップ） | 19 | 20 本（NAMCOT-163、Star Wars のみ NAMCOT-129）: Megami Tensei II、Famista '90、King of Kings、Youkai Douchuuki、Rolling Thunder、Final Lap、Kaijuu Monogatari、Sangokushi II: Haou no Tairiku 等。各タイトルが実際に拡張音源を鳴らすかは本調査では未確認 |
| Sunsoft 5B 音源 | 69 | Gimmick!（SUNSOFT-5B）。同 mapper の他 8 本は FME-7/5A で音源なし |
| MMC5 | 5 | 14 本（光栄の歴史 SLG 多数、Just Breed、Metal Slader Glory 等） |
| EEPROM セーブ（24C01/24C02） | 16 / 159 | Bandai: ドラゴンボールZ 系、SDガンダム外伝 ナイトガンダム物語 1〜3、ロクでなしBLUES 等 |
| バッテリーバックアップ（Mesen DB の Battery フラグ） | 各種 | 881 本中 217 本（SaveRam 8 KB: 187、32 KB: 5、2 KB: 3、4 KB: 1、0（EEPROM 等）: 21） |

### PRG+CHR 容量分布（日本 881 本、Mesen DB 突合値）
| PRG+CHR 合計 | 本数（累積） | 累積割合 |
|---|---|---|
| ≤256 KB | 759 | 86.2% |
| ≤384 KB | 826 | 93.8% |
| ≤512 KB | 873 | 99.1% |
| ≤768 KB | 880 | 99.9% |
| ≤1024 KB | 881 | 100% |
- PRG 単体は 8 KB〜512 KB（最多 128 KB: 496 本）、CHR は 0（CHR-RAM、208 本）〜256 KB。最大は Metal Slader Glory（MMC5 / HVC-ELROM、PRG 512 KB + CHR 512 KB = 1 MB）。768 KB 級: 青き狼と白き牝鹿 元朝秘史、星のカービィ 夢の泉の物語、Just Breed、信長の野望 武将風雲録（各 512+256）。
