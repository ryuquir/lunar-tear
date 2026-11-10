# Pico 2 / RP2350 プラットフォーム主張の検証（第 2 パス）

調査日: 2026-11-10。表記ルール: 出典付きの事実は「Cited Findings」、筆者の推論は「推論」と明記、確認できなかった事項は「未確認」。ページ番号は「印刷ページ（PDF ページ）」の順で示す。

一次資料（本調査で 2026-11-10 にダウンロードし pdftotext で本文確認）:
- RP2350 Datasheet, Release 8, Build date 01/10/2026, Build version 80d627281ed5 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet, Build date 03/07/2026, Build version d4e0f1799616 — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf

構成: §1 5 V 耐性 / §2 E9 / §4 PIO / §5 エミュレータ・映像 / §6 出力しきい値 / §7 マッパー統計 / §8 sanni / §9 I/O 拡張 / §10 メモリ・秋月ボード / §11 起動時間 / §12 検証表 / §13 結論（推論）/ §14 既存ノートへの訂正 / §15 未確認事項

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
→ §6 を参照（調査順の都合で §6 に記載）。

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

## 8. sanni Cart Reader のマッパー判定とバス操作

### Cited Findings（https://raw.githubusercontent.com/sanni/cartreader/master/Cart_Reader/NES.ino 、2026-11-10 取得。NES.ino の最終コミット 2026-03-07、リポジトリは "archived by the owner on Jun 15, 2026"、GPL-3.0 — https://github.com/sanni/cartreader ）
- 判定方法（`getMapping()`）: コメント "Read last 8kb block of PRG ROM and compute CRC32 / Some mappers (like MMC3) map the last 8KB block of PRG ROM to 0xE000 while 0x8000 can contain random data after bootup"。実装は CPU $8000–$9FFF の 8 KB と $E000–$FFFF の 8 KB をそれぞれ CRC32 し、SD カードの `nes.txt` の各エントリ（"ファイル名" 行＋ "全体CRC,8KB CRC,iNES ヘッダ16バイト" 行）の 8 KB CRC と照合。両方 0xFF（CRC 0xBD7BC39F）なら "No data found. Using manual selection"、見つからなければ "CRC not found in database / Using manual selection"。
- `nes.txt`: 22,143 行（1 エントリ 3 行 → 約 7,380 エントリ）。例 "AA421A37,61BC931A,4E45531A34015008000F000700000001" — https://raw.githubusercontent.com/sanni/cartreader/master/sd/nes.txt
- 対応マッパー表 `mapsize[]`: 196 エントリ（0〜999 の iNES 番号、PRG/CHR/RAM サイズ範囲付き）。
- 使用信号（`setup_NES()`）: "CPU R/W, IRQ, PPU /RD, PPU /A13, CIRAM /CE, PPU /WR, /ROMSEL, PHI2"（PORTF の 8 本）、"A0-A7"（PORTL）、"A8-A14"（PORTA）、"D0-D7"（PORTK）、CIRAM A10 入力（PORTC、内部プルアップ）。`set_address()` は PRG 読み出しでも CHR 読み出しでも同じ PORTL/PORTA に 15 ビットを出し、PPU /A13 だけ別ピンで反転出力。
- PRG 読み出し `read_prg_byte()`: MODE_READ → PRG_READ（R/W=High）→ ROMSEL_HI → set_address → PHI2_HI → A15 なら ROMSEL_LOW → `_delay_us(1)` → PINK を読む。
- CHR 読み出し `read_chr_byte()`: PHI2_HI → ROMSEL_HI → set_address → CHR_READ_LOW（PPU /RD=Low）→ `_delay_us(1)` → 読む → CHR_READ_HI。
- 書き込み `write_prg_byte()`: PHI2 Low → データ出力 → アドレス → PHI2 High → /ROMSEL → 1 µs → PHI2 Low → 1 µs → /ROMSEL High → 読み出しモードへ → "Set phi2 to high state to keep cartridge unreseted"。MMC1 用 5 ビットシリアル書き込み、MMC5 の M2 パルス（`dumpPRG_pulsem2`）、Bandai 24C01/24C02 EEPROM 用ビットバング関数も持つ。

### 推論
- sanni 方式はコード上 CPU と PPU の**アドレスバスとデータバスをそれぞれ同じ MCU ポートに束ねて**いる（ハード側で配線を共通化していると読める。アダプタ回路図での確認は未実施＝未確認）。この方式なら必要信号は アドレス 15＋データ 8＋制御 8＋CIRAM A10 1＝**32 本**で、分離した 54 本より大幅に少ない。
- ただし本基板では実 CPU/PPU モード（Mode A）のために CPU バスと PPU バスを分離しておく必要があるため、ダンプ用に束ねることはできない（推論）。
- マッパー判定は「CRC → データベース」方式が実績ある唯一の汎用手段。DB はフラッシュに置ける規模（約 7,400 件 × 約 12 バイト（CRC+ヘッダ要約）≈ 90 KB、推論）。

## 9. I/O 本数とシフトレジスタによる拡張、ダンプ時間

### Cited Findings
- 60 ピン Famicom カートの信号（第 1 パス §4 で NESdev から確認済み）: CPU 側 27（A0–A14、D0–D7、M2、R/W、/ROMSEL、/IRQ）、PPU 側 27（A0–A13、D0–D7、/RD、/WR、/A13、CIRAM A10、CIRAM /CE）— https://www.nesdev.org/wiki/Cartridge_connector
- sanni は 32 本（§8）。
- 秋月の汎用シフトレジスタ（2026-11-10 取得）:

| 品名 | 型番 | 販売コード | 価格（税込） | 通販在庫 | URL |
|---|---|---|---|---|---|
| 8ビットシフトレジスター（DIP） | TC74HC595AP(F) | 131760 | ¥110 | 748 個 | https://akizukidenshi.com/catalog/g/g131760/ |
| 8ビットシフトレジスター（SOP） | TC74HC595AF | 110077 | ¥50 | 2,540 個 | https://akizukidenshi.com/catalog/g/g110077/ |
| 8ビットシフトレジスター | U74HC595AG-D16 | 114053 | ¥40 | 500 個（"2月中旬入荷予定" 表記あり） | https://akizukidenshi.com/catalog/g/g114053/ |
| 8ビットシフトレジスター（DIP） | TC74HC165AP(F) | 114679 | ¥100 | 1,010 個 | https://akizukidenshi.com/catalog/g/g114679/ |

- 74HC595 の fclock（TI SN74HC595, VCC=4.5 V）25 MHz（SN74HC595 列）、74HC165 21〜31 MHz（§6 表）。
- ダンプ時間の実測値（sanni / ClusterM）: 公開値は見つからず（未確認）。ClusterM famicom-dumper-writer は "this device is very fast"（STM32F103 の FSMC＋EPM3064 CPLD）とのみ記載 — https://github.com/ClusterM/famicom-dumper-writer

### 推論: シフトレジスタ構成とダンプ時間
- 構成例（GPIO 7 本）: 74HC595 × 5 段（SER/SRCLK/RCLK = 3 本）で CPU A0–A14（15）＋PPU A0–A13（14）＋M2・R/W・/ROMSEL・PPU /RD・PPU /WR・PPU /A13（6）＝ 35 ビットを出力。CPU D0–D7 書き込み用に 74HC595 1 段を追加し /OE を GPIO 1 本で制御。読み取りは 74HC165 × 2 段＋（JAMMA 入力 24〜28 本分 3〜4 段）を SH/LD・CLK・QH の 3 本で。**計 7 本**でカート全信号と JAMMA 入力を扱える。ダンプは静的動作（M2 も /ROMSEL も低速でよい）なので 595 出力で問題ない。ただし MMC5 のように M2 パルスで状態を検出するマッパーや、M2 停止をリセットとみなす MMC 系（sanni の "keep cartridge unreseted" 参照）は、M2 を GPIO 直結にして PIO で連続クロックを出すほうが確実 → +1 本で 8 本。
- 1 バイトあたり: 595 チェーン 48 ビット＋165 チェーン 16 ビット ≈ 64 クロック。PIO で 10 MHz シフト（74HC の 4.5 V 規格 21〜25 MHz の半分以下）なら約 6.4 µs＋1 µs のアクセス待ち ≈ 7.5 µs/バイト。→ 256 KB（日本カートの 86%）で約 2.0 s、512 KB（99%）で約 3.9 s、最大 1 MB（Metal Slader Glory）で約 7.9 s。シフト 2 MHz に落としても 512 KB で約 17 s。
- 高速化: CPU D0–D7 を FT GPIO に直結（+8 本、165 不要化）、アドレス下位 8 ビットだけ別チェーンにする、等で 1〜2 µs/バイトまで縮む（256 KB で 0.5 s 前後）。

## 10. メモリ: カート容量 vs RP2350 RAM / Pico 2 フラッシュ、および大容量カート時の選択肢

### Cited Findings
- RP2350: "520 kB on-chip SRAM, in 10 independent banks"、"Up to 16 MB of external QSPI flash or PSRAM through dedicated QSPI bus"、"Additional 16 MB flash or PSRAM through optional second chip-select" — RP2350 Datasheet p.13
- Pico 2: "RP2350A microcontroller with 4 MB flash"、フラッシュは "Winbond W25Q32RV" — Pico 2 Datasheet p.3–4
- Winbond W25Q32JV（Pico 2 の W25Q32RV とは別品種、参考値）: "Min. 100K Program-Erase cycles per sector"、"More than 20-year data retention"、tPP 0.4 ms typ / 3 ms max（256 B ページ）、tSE（4 KB）45 ms typ / 400 ms max、tBE2（64 KB）150 ms typ / 2,000 ms max — https://www.winbond.com/resource-files/w25q32jv%20revg%2003272018%20plus.pdf （W25Q32RV のデータシートは winbond.com から PDF として取得できず未確認）
- pico-infonesPlus: PSRAM 無しでは "the ROM is written to flash memory during startup … taking several seconds"、PSRAM 有りでは直接 PSRAM へ — §5
- 秋月で買える RP2350 系（2026-11-10 取得。価格は税込、在庫は「通販購入可能数」）:

| 品名 | 型番 | 販売コード | 価格 | 在庫 | GPIO / メモリ（秋月記載） | URL |
|---|---|---|---|---|---|---|
| Raspberry Pi Pico 2 | SC1631 | 129604 | ¥990 | 1,462 | GPIO 26、4 MB flash、520 kB | https://akizukidenshi.com/catalog/g/g129604/ |
| Raspberry Pi Pico 2 H(完成品) | SC1632 | 130982 | ¥1,180 | 53（在庫僅少） | GPIO 26 | https://akizukidenshi.com/catalog/g/g130982/ |
| Seeed XIAO RP2350 | 102010550 | 129619 | ¥1,100 | 308 | "19のGPIO"、2 MB flash | https://akizukidenshi.com/catalog/g/g129619/ |
| Tiny 2350 (Pimoroni) | PIM721 | 130201 | ¥1,600 | 17 | GPIO 12、4 MB | https://akizukidenshi.com/catalog/g/g130201/ |
| Plasma 2350 (Pimoroni) | PIM723 | 130202 | ¥2,340 | 37 | GPIO 15、4 MB | https://akizukidenshi.com/catalog/g/g130202/ |
| W5100S-EVB-Pico2 (WIZnet) | W5100S-EVB-Pico2 | 130218 | ¥2,420 | 73 | 秋月表記 "GPIO：48"（Pico 形状のため誤記の可能性、未確認） | https://akizukidenshi.com/catalog/g/g130218/ |
| RP2350A（チップ単体、QFN60） | SC1509 | 130369 | ¥190 | 521 | GPIO 30 | https://akizukidenshi.com/catalog/g/g130369/ |
| RP2350B（チップ単体、QFN80） | SC1510 | 130370 | ¥220 | 242 | GPIO 48 | https://akizukidenshi.com/catalog/g/g130370/ |
| RP2354A（2 MB flash 内蔵、QFN60） | SC1511 | 131439 | ¥250 | 281 | GPIO 30 | https://akizukidenshi.com/catalog/g/g131439/ |
| RP2354B（2 MB flash 内蔵、QFN80） | SC1512 | 131441 | ¥280 | 115 | GPIO 48 | https://akizukidenshi.com/catalog/g/g131441/ |
| RP2350A実装基板（秋月製 QFN60 変換基板） | AE-QFN60-7X7-0.4(RP2350A) | 131106 | ¥450 | 189 | GPIO 30 | https://akizukidenshi.com/catalog/g/g131106/ |
| Pimoroni Pico LiPo - 16MB（**RP2040**、参考） | PIM560 | 116997 | ¥1,480 | 170 | — | https://akizukidenshi.com/catalog/g/g116997/ |

- 秋月の検索（キーワード "PSRAM"、"APS6404"、"ESP-PSRAM64"、"LY68L6400"、"Pico Plus"、"RP2350B"、"SRAM"）では、**RP2350B 搭載の完成ボード、PSRAM 搭載の RP2350 ボード、QSPI PSRAM チップ単体はいずれもヒットせず**（"SRAM" では 23LC512-I/P（SPI SRAM 64 KB）、M68AF127B（1 Mb パラレル SRAM）のみ）— https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=PSRAM&search=search ほか

### 推論
- 日本カートの 86%（≤256 KB）は PRG+CHR をそのまま RP2350 の SRAM に置けるが、エミュレータ本体の作業領域（フレームバッファ、CHR-RAM 8 KB、WRAM 8 KB、音声バッファ等）を考えると SRAM 内に収められるのは 256 KB 程度までが現実的。それ以上（14%）はフラッシュ（XIP）に書くか PSRAM が必要。
- フラッシュ摩耗: 電源投入ごとに無条件に書き直しても 100K 回 ÷ 1 日 1 回 ≒ 270 年、1 日 10 回でも約 27 年で、ゲームセンター用途では寿命上の問題にならない。さらに「ダンプ CRC がフラッシュ上の既存イメージと同じなら書かない」にすれば実質書き込みはカート交換時だけ。書き込み時間は 512 KB で 64 KB ブロック消去 8 回（typ 1.2 s）＋2048 ページ（typ 0.8 s）≈ 2 s（typ）、最悪値では 16 s＋6 s。
- オンデマンド読み出し（エミュレータが毎アクセスでカートを読む）は、6502 の命令フェッチ毎にシフトレジスタ往復（数 µs）が入るため実時間エミュレーション（1 命令 ≒ 1〜4 µs 相当の実機時間）には遅すぎる。CPU D0–7 と A0–A14 を全て GPIO 直結すれば理屈上は可能だがピンが足りない（推論）。→ 選択肢は「SRAM に全部載る小容量はRAM、それ以上はフラッシュ XIP」の 2 段構え。
- PSRAM: 秋月で入手できないため、ユーザーの調達ルールでは採れない（LCSC/JLCPCB の PSRAM の Basic 可否は本調査範囲外、未確認）。

## 11. 起動時間と電源断耐性: Pico ファーム vs Linux Pi

### Cited Findings
- IronOxidizer/instant-pi（電源投入→ユーザ空間、±0.3 s）: Pi Zero W で "RPi OS Full 70 / Buildroot 10.5 / Buildroot Instant Pi 4.7 / CD Bootloader Overhead 4.1" 秒、Pi 1B で 77 / 13.0 / 5.9 / 4.3 秒。Pi Zero 2 W と 4B の欄は空欄 — https://github.com/IronOxidizer/instant-pi （README）
- furkantokac（Pi 3、高速度カメラで計測、2021-03-29 公開）: "Linux shell in 1.75 seconds, power-up to Qt (QML) application in 2.82 seconds"。内訳: Raspberry boot stage 1.25 s（変更不可）、start.elf 0.25 s、kernel 0.25 s、init 0、Qt アプリ 1.07 s。既定 Buildroot では合計 10.17 s — https://www.furkantokac.com/rpi3-fast-boot-less-than-2-seconds/
- 読み取り専用 root: raspi-config の Overlay File System 等（第 1 パス §1 で確認済みの出典）— https://github.com/raspberrypi/bookworm-feedback/issues/137 ／ https://learn.adafruit.com/read-only-raspberry-pi
- RP2350 ブートは ROM 内のブートロム → フラッシュの A/B パーティション＋TBYB（第 1 パス §7）。Pico 2 Datasheet: "The USB boot code is stored in ROM on RP2350, so can not be accidentally overwritten."

### 推論
- Pi Zero 2 W は Pi 3 と同系 SoC（BCM2710A1）なので、Buildroot 最小構成で 2〜5 秒、Raspberry Pi OS Lite なら数十秒が目安（Zero 2 W 自体の実測値は見つからず未確認）。Pico 2 は電源投入から main() まで数十 ms オーダー（データシートに数値記載なし、未確認）で、ゲーム開始までの時間はカートダンプ時間（§9: 256 KB で約 2 s）が支配的。
- 電源断: Pico は FS を持たず、フラッシュ書き込み中（カート交換直後のみ）以外は電源断で壊れる要素がない。書き込み中の断も「書き込み完了フラグ＋CRC 検査で起動時に再ダンプ」で回復可能。Linux は読み取り専用 root にしても SD カードのコントローラ自体の電源断耐性に依存する。

## 12. 第 1 パス主張の検証表

| # | 第 1 パスの主張（raspberry_pi_emulation_path.md） | 判定 | 一次資料の原文・根拠 |
|---|---|---|---|
| 1 | RP2350 FT ピンは IOVDD=3.3 V 給電中に限り 5.5 V まで耐える | **検証済** | "they will tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V"（RP2350 DS Table 1673, p.1331）、VPIN_FT 5.5 V（IOVDD=3.3 V）（Table 1680, p.1335） |
| 2 | 非 ADC GPIO（RP2350A: GPIO0–25、RP2350B: GPIO0–39）が FT、ADC 兼用ピンは非 FT | **検証済** | Table 1674（p.1332–1333） |
| 3 | Pico 2 で 5 V 直結可は GPIO0–22 の 23 本、GPIO26–28 不可 | **検証済** | Pico 2 DS p.14 "exposes 26 of the 30 … GPIO0 to GPIO22 are digital only and GPIO 26-28 …"、ADC ピンは "must not exceed IOVDD plus about 300 mV" |
| 4 | Pico 2 DS「GPIO0–25 は RP2350 無給電時も電圧印加可」 | **補足訂正** | 原文は正しいが、上限は "3.3 V-failsafe (unpowered)"（DS p.13）、VPIN_FT は IOVDD=0V で 3.63 V（Table 1680）。**無給電中の 5 V 印加は不可** |
| 5 | E9 は A2 のみ、A3 で修正、量産は A4 | **検証済** | D.5.1 "Affects RP2350 A2"、"Fixed by RP2350 A3, Documentation"、Table 7 "A4 Production version" |
| 6 | E9 の内容（約 120 µA、約 2.2 V、8.2 kΩ 以下で回避、プルアップは正常） | **検証済** | D.5.1 原文（§2） |
| 7 | 日本で 2026 年末に売られる Pico 2 のステッピング | **未確認** | 秋月 129604 の商品ページに記載なし。公式は "Eventually all Pico 2 products will use the A4 stepping" のみ |
| 8 | 3.3 V 出力で 5 V CMOS（74HC）入力を駆動するのは危険、74HCT が安全 | **検証済（数値追加）** | RP2350 VOH min 2.62 V（Table 1683）vs 74HC VIH 3.15 V@4.5 V（TI SN74HC595 §6.3）、74HCT VIH 2 V（TI SN74HCT245） |
| 9 | 2A03/2C02 入力は TTL しきい値 | **一次資料なし（二次・実験のみ）** | 既存ノート famicom_electrical_and_pitfalls.md の NESdev 引用のみ。公式データシートは存在確認できず |
| 10 | PIO 3 ブロック×4 SM、1 命令/クロック、2 段同期器と INPUT_SYNC_BYPASS | **検証済** | RP2350 DS §11（§4 表） |
| 11 | 最大システムクロック | **検証済: 150 MHz** | "a 150 MHz system clock, the maximum supported on RP2350"（p.531）。pico-infonesPlus は 252 MHz 動作（定格外） |
| 12 | pico-infonesPlus: RP2040/RP2350 対応、DVI/HDMI のみ、SD 読込、PSRAM 無しはフラッシュ書込、GPL-3.0 | **検証済**（リポジトリは PicoPlus-devel へ移管、v0.56） | README / LICENSE |
| 13 | pico-infonesPlus のマッパーは 0/1/2/3/4/5/24/69/85 等 | **訂正** | MapperTable は 157 エントリ（§5 に全列挙）。日本ライセンス品で使われる 58 マッパー全てを含む |
| 14 | VRC7 は RP2350＋PSRAM＋オーバークロック必須、時々グリッチ | **検証済** | README Known Issues |
| 15 | pico_scanvideo_dpi はタイミング変更で 15 kHz に流用可能 | **部分訂正** | 15 kHz プリセット無し、timing 構造体に CSync・インターレース項目無し。自作タイミング＋PIO 改造が必要 |
| 16 | PICO9918 は PIO で VGA または SCART RGB、12 ビット RGB | **検証済＋詳細** | 4 bit/色、3.9k/1.8k/910/470 Ω、Sync 47 Ω、SCART は 480i/576i インターレース 13.5 MHz、CSync は HSYNC ピンから |
| 17 | sanni: 8 KB CRC32 → nes.txt、無ければ手動選択、PHI2→/ROMSEL→1 µs で読む | **検証済（表現を精密化）** | CPU $8000 と $E000 の各 8 KB を CRC。読み出しシーケンスはコード通り |
| 18 | sanni リポジトリは 2026-06-15 にアーカイブ | **検証済** | GitHub 表示 "archived by the owner on Jun 15, 2026" |
| 19 | Famicom カートは約 54 信号 | **検証済** | NESdev Cartridge connector（第 1 パス）。sanni はバス共通化で 32 本 |
| 20 | RP2350B 搭載ボードの秋月在庫は部品担当の確認事項 | **今回確認** | 秋月に RP2350B はチップ単体（130370、¥220）のみ。RP2350B 完成ボード・PSRAM 搭載ボードは検索でヒットせず |
| 21 | 読み出しは 1 バイト数 µs、512 KB で数秒以内 | **推論のまま（計算根拠を追加）** | §9: 7.5 µs/バイトで 512 KB ≈ 3.9 s。実測値は未確認 |
| 22 | Linux Pi の起動時間 | **一部確認** | Pi Zero W 最小 4.7 s（instant-pi）、Pi 3 最小 1.75 s（shell）/2.82 s（Qt アプリ）。Zero 2 W の実測は未確認 |

## 13. 結論: Pico 2 1 個で足りるか（推論）

**推論**: エミュレーション＋起動時ダンプ方式（Mode B、ドナー無し）なら Pico 2 1 個で足りる。実 CPU/PPU＋Pico による RGB 生成（Mode A）は、RGB 化の方式次第で 1 個では足りない可能性が高い。

### Mode B（エミュレーション）の GPIO 予算（Pico 2: 5 V 可 23 本＋3.3 V 専用 3 本＝26 本）
| 用途 | 本数 | 5 V 接続 | 備考 |
|---|---|---|---|
| RGB DAC 4 bit×3 | 12 | 不要（抵抗のみ） | GPIO26–28 の 3 本はここに割当て可。3 bit×3 なら 9 本 |
| CSync | 1 | 不要 | PICO9918 同様 PIO で生成 |
| 音声 PWM | 1 | 不要 | RC フィルタ→アンプ |
| 74HC595 チェーン（SER/SRCLK/RCLK） | 3 | 74HC 側は 5 V 給電 → 3.3 V 入力は保証外。**74HCT595 にするか 595 を 3.3 V 給電**（§6） | カート アドレス 29 本・制御 6 本・コインカウンタ等 |
| CPU データ書き込み用 595 の /OE | 1 | 同上 | マッパーレジスタ書き込み用 |
| 74HC165 チェーン（SH/LD/CLK/QH） | 3 | QH（5 V）→ FT ピンは可（IOVDD 給電中のみ） | CPU D0–7、PPU D0–7、CIRAM A10、JAMMA 入力 24〜28 |
| M2 直結（PIO で連続クロック） | 1 | 5 V 側入力が TTL しきい値なら直結可（マッパー IC は未確認）→ 74HCT 経由が安全 | MMC5/MMC3 のリセット検出対策 |
| **小計** | **22** | | 残り 4 本（サービス/テスト SW 直結、/IRQ 監視、予備） |

- 処理能力: pico-infonesPlus は 252 MHz（定格 150 MHz の 1.68 倍）で動いており、業務用で連続運転する際の定格外動作がリスク。150 MHz で全速動作するかは未確認。
- メモリ: 日本カートの 86% は SRAM に、残りはフラッシュ XIP に置く。PSRAM は秋月で入手不可。
- カバー率: マッパー上位 5 種で 71%、10 種で 82%、15 種で 88%（nesdir 881 本標本）。ダンプ用のバンク切替ドライバとエミュレータ側の実装を両方書く必要があるので、「N 種サポート」の N は両方の実装数で決まる。拡張音源はエミュレータ側で再現（VRC6/N163/5B/MMC5 は pico-infonesPlus に実装済み、VRC7 は不安定）。
- 5 V 電源シーケンス: Pico の 3.3 V が立つ前に 5 V 信号が FT ピンに来ないよう、595/165/バッファの /OE または電源を Pico の 3V3 で制御する（§1 推論）。

### Mode A（実 CPU/PPU）
- 既存ノート rgb_from_rp2c02.md の見積もりでは EXT 方式 RGB 化に 30〜35 本必要で、Pico 2（26 本）では不足。RP2350B（48 GPIO）は秋月でチップ単体のみ（QFN-80、PCBA 側で実装なら JLC では Extended＝既存ノート parts_class_reverification.md）。→ Mode A でも Pico 2 1 個で済ませるなら、RGB 化をカラールックアップの外付け化や 3 bit×3 DAC への削減、595 経由化などで本数を削る設計が必要（推論）。

## 14. 既存ノートへの訂正
- raspberry_pi_emulation_path.md §1 Inferences「既存 InfoNES 系はマッパー 0/1/2/3/4/5/24/69/85 等をカバー」→ pico-infonesPlus の MapperTable は 157 マッパー（6 はコメントアウト、85 は RP2350 のみ）。日本ライセンス品の 58 マッパーは全て登録済み（§5, §7）。
- 同 §1 Cited Findings の URL https://github.com/fhoedemakers/pico-infonesPlus → 現在は https://github.com/PicoPlus-devel/pico-infonesPlus （README 内リンクも PicoPlus-devel を指す）。最新 v0.56（2026-11-08）。
- 同 §5 で引用された Pico 2 DS の「無給電でも GPIO0–25 に電圧を印加できる」は 3.63 V 以下に限る（RP2350 DS "3.3 V-failsafe (unpowered)"、VPIN_FT IOVDD=0V で 3.63 V）。第 1 パスの推論（無給電中の 5 V 印加は違反）は正しいが、引用文だけ読むと誤解を招くため明記する。
- 同 §3「pico_scanvideo_dpi はタイミングを 15.7 kHz/60 Hz に変更すれば理論上流用可能」→ 定義済みモードは全て 31 kHz 以上、timing 構造体に CSync/インターレース項目なし。HSYNC/VSYNC 別出力しかないので CSync は PIO プログラム改造か外付けゲートが必要。
- 同 §3「PICO9918 … SCART RGB」→ SCART 出力は 480i/576i の**インターレース**（13.5 MHz）で 240p ではない。JAMMA 用 240p の直接の前例ではない。
- 同 §4「PRG の最終 8 KB（$8000 と、MMC3 用に $E000）の CRC32」→ 正確には CPU $8000–$9FFF と $E000–$FFFF の 2 つの 8 KB 窓をそれぞれ CRC32 し、DB の 8 KB CRC 欄と照合（どちらかが一致すればよい）。
- 同 §5 Gaps「Akizuki で入手できる Pico 2 の現行ステッピング」→ 秋月の商品ページには記載が無いことを確認（依然として未確認）。
- rgb_round2_details.md の「ADC 兼用ピン除外は未確認」→ RP2350 DS Table 1674 で GPIO26–29（RP2350A）が "Digital IO / Analogue"（FT ではない）と確認済み。

## 15. 未確認事項
- 2026 年 11 月に秋月等で販売中の Pico 2 のステッピング（A2/A3/A4）。購入品の刻印確認が必要。
- 2A03 / 2C02 の入力しきい値の一次資料、およびカート内マッパー IC（MMC1/MMC3/VRC 等）と 74xx161/74xx32 が LS か HC か（3.3 V 直結の可否）。
- sanni アダプタ基板で CPU/PPU バスを物理的に共通化しているかの回路図確認（コードからの推論のみ）。
- 日本カート約 1,053 本のうち nesdir 未収録の約 170 本のマッパー分布。nescartdb.com は Cloudflare によりアクセス不可。
- Pico 2 の W25Q32RV の書き換え耐性（W25Q32JV の 100K 回を参考値として使用）。
- Pi Zero 2 W の最小 Linux 起動時間の実測値、Pico 2 の電源投入→main() の時間。
- pico-infonesPlus が 150 MHz（定格）で全速動作するか、および InfoNES 系のテスト ROM 通過率。
- シフトレジスタ方式の実ダンプ時間（実測なし、§9 は計算値）。
- 秋月 W5100S-EVB-Pico2 の "GPIO：48" 表記の真偽。
- Web 検索はセッション上限に達したため、後半（ダンプ速度の実例、Zero 2 W 起動時間）は既知 URL の直接取得のみで調査した。
