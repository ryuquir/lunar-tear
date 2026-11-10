# オープンハードウェア JAMMA 基板の実回路調査 (第2パス・作業中)

調査日: 2026-11-10。設計ファイルは raw.githubusercontent.com から取得し、KiCad netlist をスクリプトで解析、PDF 回路図は 150–300dpi でラスタ化して目視で読んだ。

## 1. ole00/orb (Open Retro Board) v0.3

- URL: https://github.com/ole00/orb , ライセンス MIT (LICENSE ファイル), EDA: gEDA gschem (schem/orb03_p1..p3.sch) + PDF (orb03.pdf, 2017-07-08 生成, 3ページ)
- 回路図 PDF: https://raw.githubusercontent.com/ole00/orb/master/orb03.pdf / BOM: https://raw.githubusercontent.com/ole00/orb/master/bom.txt

| 機能 | ORB の実回路 (orb03.pdf から読み取り) |
|---|---|
| 入力 | JAMMA 入力→スイッチングダイオード D1 (カソードが JAMMA 側)→BBG GPIO。BBG 側内部プルアップ 3.3V。図注 "JAMMA outputs either 0V (button pressed) or disconnected or 5V (either means b. released)" "BBG GPIO input pins held high on 3.3V (active low)" "D1: fast switching diode 15V, 4ns"。BOM は "Diode switching 100V 0.15A 4ns SMD1206" ×24 |
| RGB DAC | 各色 5bit 2 進重み抵抗 (510 / 1k05 / 2k2 / 4k7 / 10k) を BBG GPIO (3.3V) から加算、加算点に終端抵抗 (R 200Ω, G 220Ω, B 270Ω) to GND。74HC4066 (5V) のスイッチ3本で各色 1bit を同期信号に連動して切り替え |
| バッファ | CLC4007 (クワッド高速 OP アンプ) 単電源 +5V (-VS=GND), 非反転増幅 利得 1+1k/470 = 3.13 倍、出力に 51Ω 直列 → JAMMA R/G/B。電源に 2.2µF タンタル |
| 同期 | BBG P8-28 sync → 1k / 470Ω 分圧 (3.3V→約1.05V) → CLC4007 第4ch 非反転 利得 1+1k/330 = 4.03 倍 → JAMMA CSync (直列抵抗なし)。同ノードが 74HC4066 の制御端子 (pin 5,12,13) へ |
| 音声 | PAM8403 モジュール (eBay の 2×3W 緑基板) の L+ → JAM 10 "Audio +", L- → JAM L "Audio -" (BTL)。入力に 2kΩ トリマ (3362P) ×2 を音量調整として使用。電源 5V |
| コインカウンタ | 回路なし |
| 電源 | JAM 3 +5V を直接 BBG P9-8 等へ。ヒューズ・TVS・逆接保護なし。100nF のみ (ATtiny13a 自動起動回路) |
| ESD | 専用部品なし (入力ダイオードが 5V 印加から 3.3V GPIO を守る役目のみ) |

## 2. MisterJamma/DE10Jamma

- URL: https://github.com/MisterJamma/DE10Jamma , ライセンス: リポジトリに LICENSE ファイルなし (README にも記載なし) → **未確認 (実質ライセンス無し=再利用は要許諾)**。EDA: KiCad 5 (DE10Jamma.sch / .kicad_pcb / .net) + PDF (DE10Jamma.pdf, 2020-08-02 生成, 図面日付 "18 04 2020")
- 取得ファイル: https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/DE10Jamma.net , .sch , .pdf , README.md
- 注意: README "Values for some components do not match the schematic, and have been adjusted to reduce the number of different components." 回路図 (475R/560R) と BOM (604R Bourns CAY16-6040F4LF / 1k) で値が異なる。

| 機能 | DE10Jamma の実回路 (netlist + PDF で確認) |
|---|---|
| 入力 | JAMMA ピン → 1k 直列 → FPGA GPIO ノード、ノードに 10k プルアップ (+3V3) と 10nF to GND。全 28 入力同一 (netlist 上 R86 のみ 1k プルアップ=誤記と思われる、推論)。デバウンス無し ("No multiplexing, polling or debouncing")。README は NeoGeo CRE401 を参照 |
| RGB DAC | 各色 6bit R-2R、全抵抗を同一値 "2R" にし R は 2R 2本並列。回路図 2R=475Ω (R=237.5Ω) / BOM 2R=604Ω (CAY16-6040F4LF 4連アレイ, R=302Ω)。LSB 側終端は GND。バッファ無しで JAMMA R/G/B (12a/12b/13a) に直結 |
| 同期 | DE10-Nano GPIO の composite sync → 100Ω 直列 (R1/R3) → JAMMA 13b (Sync) |
| 音声 | PWM (AUDIO_L/R) に 1k プルダウン (基板検出用)、560Ω+10nF ×2 段 RC (fc≈28kHz/段, 推論計算)、JP1 で Mono/Stereo 切替、470nF 結合 → TDA7496 (+12V 単電源, TO-220-15)。出力は各 ch 1000µF 結合で JAMMA 10a "SPEAKER_R" / 10b "SPEAKER_L"。DC 音量: RV1 50k (+5V–GND) ワイパ→300k→pin3 (100nF to GND)。電源 +12V に 100nF + 1000µF。SVR 470µF |
| コインカウンタ | 無し (8/J, 9/K 未接続) |
| 電源 | JAMMA +5V (3a/3b/4a/4b) を "+5VL" として 2.1mm DC ジャックで DE10-Nano へ。ヒューズ・TVS・逆接保護なし。3.3V は DE10-Nano の GPIO ヘッダから供給 |
| ESD | 専用部品なし (1k+10nF の RC のみ) |

推論 (計算): R-2R の出力インピーダンス = R。3.3V CMOS 出力でフルスケール開放電圧 3.3×63/64 ≈ 3.25V。モニタ入力 2kΩ (Blast City 仕様) を負荷とすると 604Ω版で 3.25×2000/2302 ≈ 2.82V、475Ω版 (R=237.5Ω) で ≈ 2.90V。README の "Output level is not noticeably lower than a NeoGeo MVS" と整合。

推論 (要注意点): JP1 を Mono にすると L/R 両アンプに同一信号が入り、10a と 10b に同相出力が出る。スピーカを 10 と L の間に繋ぐ JAMMA 筐体ではほぼ無音になるはずで、L 側が GND の筐体を前提にしている可能性がある。作者の意図は 未確認。

## 3. KabukiFlux/jammanator-pi (Raspberry Pi → JAMMA, "JAMMANATOR" Rev 1.01)

- URL: https://github.com/KabukiFlux/jammanator-pi , ライセンス MIT (Copyright (c) 2025 Kabuki Flux), EDA: KiCad 8.0.8 (kicad/jamma_raspi.kicad_sch, jamma_raspi_ios.kicad_sch, .kicad_pcb), 回路図画像 assets/schematics.jpg (図面日付 2023-02-22), iBOM, Gerber。部品に "LCSC Part" フィールドあり
- 解析方法: kicad_pcb のパッド→ネット対応を抽出、回路図 JPG を目視

| 機能 | 実回路 |
|---|---|
| 入力 (1 入力あたり) | JAMMA ピン — 10k プルアップ (+3.3V, 4連アレイ R_Array_Concave_4x0603) — 100nF to GND (4連 C アレイ 0612, LCSC C62857) — 1k 直列 (4連アレイ) — BAT54S (SOT-23, LCSC C47546, 中点=信号、両端=+3.3V/GND のクランプ) — SN74LVC244APWR (3.3V, LCSC C7668) — MCP23017 (I2C, LCSC C558584) ×2。1k/10k アレイの LCSC は C20197 / C29718 (どちらがどちらかは 未確認)。保護回路は circuit_js/barrier_diode_simulation で 470Ω + 1N5711 + 100nF として検証 |
| RGB DAC | 各色 6bit R-2R、R=240Ω (LCSC C17572)、2R=475Ω (LCSC C228851)、0805 1%。Pi GPIO (3.3V) 直結、バッファ無し。図中 TODO: "BUFFER to avoid RGB drifting depending on monitor input impedance" |
| 同期 | VSYNC/HSYNC を各々 4k7 + 10µF の RC で平均化し 74HC86 で元信号と XOR (極性正規化)、さらに XOR で合成 → 74HC86 4段目 → 100Ω 直列 → JAMMA P (CSYNC 相当ピン)。74HC86 (LCSC C2872580) は +5V 給電 |
| 音声 | Pi PWM → 220Ω → 100nF to GND (fc≈7.2kHz, 推論計算) → 470nF 結合 → 10k 2連ポット (音量) → PAM8403 モジュール (+5V)。L 出力 (L+/L-) をジャンパ JP4/JP5 経由で JAMMA 10 / L (BTL)。ステレオ用 Molex 396 4P 端子も |
| コインカウンタ | 無し |
| 電源 | JAMMA +5V (3,4,C,D) → LM1117IMPX-3.3 (LCSC C23984) で +3.3V、10µF (1210, LCSC C39232) 入出力。電源 LED、アナログ電圧計。ヒューズ・TVS 無し |
| ESD | BAT54S クランプ + 1k + 100nF が実質の ESD/過電圧対策 |

推論: 74HC86 を 5V で動かすと VIH(min)=3.5V (74HC, VCC=4.5V) で、Pi の 3.3V 出力はしきい値未満。動作実績はあっても規格外 (74HCT86 なら VIH=2.0V)。

## 4. ninomegadriver/PiPicoJamma (Raspberry Pi 4 + Pico, v1.2)

- URL: https://github.com/ninomegadriver/PiPicoJamma , ライセンス GPL-3.0, EDA: Fritzing (PiPicoJamma1.2.fzz), Gerber, BOM HTML (JammaPiPico_bom.html)。PCBWay 共有あり
- 解析: .fzz を展開し PCB ビューの接続をスクリプトで解析

| 機能 | 実回路 |
|---|---|
| 入力 | JAMMA 入力ピンを Pico の GPIO に直結 (抵抗・コンデンサ・保護素子なし、BOM にも無し)。Pico は USB キーボードとして Pi に入力 |
| RGB DAC | 各色 6 本の抵抗 (8.2k / 4.3k / 2.2k / 1k / 510 / 180Ω, ±5% THT) を Pi GPIO から並列加算し JAMMA R/G/B に直結。終端・バッファなし。README "VGA666 interface, with resistor values tunned for better contrast on legacy arcade monitors" |
| 同期 | 未確認 (Fritzing 上で 74F04 "Logic Conv" はあるが Pro Micro 系の配線) |
| 音声 | PAM8610 モジュール用スロット + ステレオ音量ポット、JAMMA モノ or 外部スピーカ端子 |
| コインカウンタ / 電源保護 / ESD | なし。JAMMA +5V を Pi に直結 |

推論 (計算): 6 本並列の出力抵抗 ≈ 107Ω、フルスケール 3.3V。2kΩ 負荷で ≈3.13V。重みが 2 進比になっていない (180→510 は 2.8 倍) ため階調は非線形。

## 5. fenlogic/vga666 (参考: 多くの Pi→JAMMA 基板の DAC 原型)

- URL: https://github.com/fenlogic/vga666 , GPL-3.0, 回路図 design_data/schematic/vga.gif, マニュアル documents/vga_manual.pdf (Rev 1.0, 8 September 2014)
- マニュアル記載: "Rs = 3.3/0.7*75-75 = 278 Ohms ... x = 547 Ohms ... rounded down to 500, 1K, 2K, 4K, 8K and 16K"、実装値 "Red = 499 Ohm, Orange = 1K, Yellow = 2K, Green = 4K, Blue = 8K, Purple = 16k, White = 80..120 Ohm" (HSYNC/VSYNC)。"You should not draw more than 16mA from a pin. Thus the minimum resistor is 3.3/0.016 = 206 Ohms" — 75Ω/0.7Vpp 用設計で JAMMA 用ではない。

## 6. KabukiFlux/bad_raspi_jamma (反面教師として作者自身が誤りを列挙)

- URL: https://github.com/KabukiFlux/bad_raspi_jamma , MIT (2022), KiCad 6 (bad_raspijamma.kicad_sch) + schematic.pdf (2022-12-25, Rev 1.00)
- 構成: VGA666 と同じ 6bit 2進重み (499 / 1K / 2K / 4.22K / 8.06K / 16.2K) を直結、HSYNC/VSYNC を各 120Ω で抵抗合成して CSYNC、LM4952TS (+12V, VDD 10µF, BYPASS 4.7µF, PWM→220Ω→100nF→470nF 結合, DC_VOL に 50k ポット(3.3V)) 出力 470µF/16V ×2 結合、MCP23017 ×2 (3.3V)
- 図中の "ERRORS" 欄 (原文): "Bad CSync generation for the JAMMA", "Bad RGB levels for JAMMA", "No decoupling caps on multiple ICs", "No pullup on I2C", "Limit JAMMA inputs to 3.3v PULLUP or IC is DEAD", "It is better to operate at 5v and limit I2C to 3.3v"、MCP23017 横: "IF POWERED VIA 3.3V MAX INPUT WILL BE 3.9V If 5v are coming from the JAMMA (pullup or transient) it will kill the IC"、DAC 横: "DAC for 75ohm output needs to be changed for JAMMA via buffered output"
- README: "The audio IC generates too much heat for a 3.1watt output." "No overvoltage prevention has been included on the design."
- 意義: 同じ作者が後継 jammanator-pi で 10k プルアップ(3.3V)+1k+BAT54S+100nF+74LVC244 の入力保護と XOR CSync を採用した経緯の一次資料。

## 7. KabukiFlux/JAMMA_2player_xbox360 (RP2040 ×2, 入力専用)

- URL: https://github.com/KabukiFlux/JAMMA_2player_xbox360 , MIT (2023), KiCad (KiCAD/Jamma_rgbuntu_xbox360.kicad_sch) + schematics.pdf + iBOM
- Pico 2 枚を JAMMA エッジの入力に直結 (抵抗・保護なし)。ファーム GP2040-CE。タイトル自体が "(cheap version, no protections)"
- README の現場注意 (原文): "Ensure your Arcade Cabinet doesn't send 12v on the coin circuitry, a switch is only allowed here." "I recommend ENIG as the surface finish and Gold Fingers checked with 30º angle chamfer as well."
- 推論: 筐体によってはコイン入力線に 12V 系が乗る可能性を作者が警告している → Pico 直結は不可、クランプ必須の根拠になる。

## 8. スーパーガン系 (JAMMA 基板を「受ける」側。入力駆動・電源・映像受けの参考)

| プロジェクト | URL / ライセンス / EDA | 関係する回路 |
|---|---|---|
| yoonjustin/WinchesterPCB | https://github.com/yoonjustin/WinchesterPCB , MIT (2021), KiCad 5 + BOM PDF | 電源 ATX 20pin、+5V/+12V に INA260 電流モニタ、+5V 配線幅 2.5mm (README: "If we assume 5A through a 1oz copper board ... 2.59mm trace width")。JAMMA 入力の駆動は Teensy 4.1 → MUN5230DW1T1G (内蔵 1k/1k のデジタル NPN, SOT-363) で GND に落とす。RGB は 3362P 1k トリマ経由 BA7230LS → THS7376 |
| charcole/MiniGun | https://github.com/charcole/MiniGun , CC BY-NC 3.0 (非商用), KiCad 4 (.sch/.net) | JAMMA 入力を TLC5926 (定電流シンク LED ドライバ) ×2 で GND に引く。JAMMA RGB → 4.7µF 直列 → 470Ω → SCART (75Ω)、Sync → 330Ω、スピーカ → 10k/1k 分圧で SCART 音声。+5V → LD1117S33 |
| kamencesc/Supergun-Basica | https://github.com/kamencesc/Supergun-Basica , Eagle 9.4 | 受動配線のみ (10k/1k/560Ω, 3362 トリマ, 3.5mm ジャック Mono/Stereo 切替) |
| Hackafe/diy-arcade-jamma-pcb | https://github.com/Hackafe/diy-arcade-jamma-pcb , GPL-2.0 | KiCad ファイルは空 (sch 34 バイト / pcb 51 バイト) → 回路情報なし |
| cspang1/jcap | https://github.com/cspang1/jcap , MIT (2017-2020), KiCad 6 | JAMMA 互換を目標とする Propeller 基板だが現行 PCB に JAMMA エッジ無し (VGA 出力)。入力は 10k SIP アレイ プルアップ (+3.3V) + 74HC165 ×2。DC 入力 → P-MOSFET IPP80P03P4L-04 (逆接保護) → LM3940IT-3.3 |

## 9. その他確認したもの (回路情報なし or 範囲外)

| 対象 | 結果 |
|---|---|
| pi2jamma (Jochen Zurborg / arcadeforge) | 商用・回路図非公開。falz.net は構成 (VGA666 + THS7314, LM380N 2.5W, 74LS165 ×3) のみで抵抗値・電源・ヒューズ情報なし — https://falz.net/wiki/Pi2jamma_hardware_and_software_info |
| misteraddons/MiSTercadeV1 / V2 | GitHub はファーム・マッピング・スクリプトのみ。回路図・設計ファイル無し (git clone で全ファイル確認) |
| MiSTer-DB9/JAMMA_MiSTer | README と jamma_inputs.zip のみ |
| njz3/jammamia | ファームのみ MIT (2024)。基板は非公開。README: "A ULN2003 chip is used for the OUT signals ... Maximum current is 500mA and maximum voltage is +5V"。同梱 Pinout PDF では JammaMia の 8/J・9/K は "NC" (コインカウンタ非駆動) |
| jzdziarski/jamma | KiCad (v10 形式) の旧基板→JAMMA 変換基板群。ライセンス "For non-commercial educational use only"。Atari JAMMA Interface: 音声 LM386N-1 (+5V 給電, 10k ポット→2.2k→IN+, pin1–8 間 10µF=利得 200, BYPASS 10µF, 出力 1000µF 結合→JAMMA 10, Zobel 10Ω+0.1µF)、CSync は SN74LS86 XOR + 470Ω、-12V は MC34063A。全 13 基板とも COUNTER_1/2 (8/J)・LOCKOUT_1/2 (9/K) はネット名のみで未接続 |

### コインカウンタ駆動の調査結果 (重要)
- 調べたオープン JAMMA 基板 (ORB, DE10Jamma, jammanator-pi, bad_raspi_jamma, PiPicoJamma, JAMMA_2player_xbox360, jzdziarski 13 枚, JammaMia 公開ピン配置) の **どれも 8/J (Coin counter) と 9/K (Lockout) を駆動していない** (各設計ファイルのネットを確認)。
- 量産基板の実例: Neo Geo MVS は NEO-F0 → ULN2003 のオープンコレクタ出力、コイルは "hardwired to the 12V power supply"、無通電時は返却側 — https://wiki.neogeodev.org/index.php/Coin_lockout , https://wiki.neogeodev.org/index.php/Coin_counter
- 外付けフライホイールダイオード: メーターに内蔵が無い場合 "You need to use an external 1N4004 or 1N4007 diode"、カソードを +12V 側・アノードを JAMMA 8 側。例として "KE-610 Counter DC12V" — https://forums.arcade-museum.com/threads/coin-counter-help-suppression-diode-voltage.420173/ (フォーラム、確度中)
- Double JAMMA アダプタ説明書: "The coin counter outputs are diode protected at both game boards." — https://www.mikesarcade.com/estore/datasheets/Dbl-JAMMA.pdf
- コイル電流・抵抗値・必要パルス幅の数値は今回も 未確認 (NeoGeo Dev Wiki は "long enough time for the mechanism to work" とのみ記載)。

## 10. Raspberry Pi 公式 RP2040 参考設計 (Pico-class 基板の「実証済み」回路の一次資料)

- 資料: "Hardware design with RP2040" (PDF 作成日 2026-08-20) — https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf 、KiCad 一式 (MIT, "RPI-PVSA_R3-S1") — https://datasheets.raspberrypi.com/rp2040/VGA-KiCAD.zip (→ pip-assets.raspberrypi.com/.../RP-008395-DS-2-VGA-KiCAD.zip にリダイレクト)。kicad_pcb のネットを抽出して値を確認した。

| 機能 | 回路 (kicad_pcb ネットで確認) |
|---|---|
| RGB DAC | 各色 5bit (G は 6bit) の 2 進重み抵抗: LSB→MSB = 8.06k / 4.02k / 2k / 1k / 499Ω を加算点 VGA_R に直結。PDF: "1/Rparallel = 1/499 + 1/1000 + 1/2000 + 1/4020 + 1/8060 = 0.00388, so Rparallel is 258 Ω ... 3.3 × 75 / (258 + 75) = 0.74V"。LSB の GPIO はブランキング中に 1k 経由のボタン入力として兼用 |
| 同期 | GPIO16 (HSYNC) / GPIO17 (VSYNC) → 各 47Ω 直列 → VGA コネクタ |
| PWM 音声 | GPIO → NC7WZ16 バッファ (専用 3.3VA LDO TLV70033 給電) → 220Ω 直列 → 100Ω to GND + 100nF to GND → 47µF 結合 → 出力 (1.8k to GND)。PDF: "This method is the same as is used on the Raspberry Pi 4 audio output jack" |
| 電源 | USB/外部 +5V → MBR120VLSFT1G (ショットキー) → Pico VSYS。Pico データシート: "VSYS ... allowed range 1.8 V to 5.5 V"、"The simplest way to safely add a second power source to Pico is to feed it into VSYS via another Schottky diode" — https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf |

推論 (計算): この 5 本 (Rparallel=258Ω) を JAMMA モニタ (2kΩ, Blast City 仕様) に直結すると 3.3×2000/2258 ≈ 2.92V フルスケール。75Ω 系 (0.74V) 用の設計でも JAMMA の高インピーダンス入力ではちょうど 3Vpp 級になる。

RP2040 の入力に関する一次資料 (RP2040 Datasheet https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf Table 622/623 ほか):
- Absolute max "Voltage at IO VPIN -0.5 ... IOVDD + 0.5 V" (IOVDD max 3.63V) → **5V 直結は定格外**。JAMMA 入力線に 5V/12V が来る可能性 (§7 の作者警告) と合わせ、クランプ必須。
- ESD: HBM 2kV (全ピン)、FT ピンのみ 4kV。
- 内蔵プルアップ RPU 50–80kΩ (弱い) → 外付け 10k プルアップが既存設計 (DE10Jamma, jammanator-pi) の標準。

