# オープンハードウェア JAMMA 基板の実回路調査 (第2パス)

調査日: 2026-11-10。設計ファイルは raw.githubusercontent.com / git clone で取得し、KiCad netlist・kicad_pcb のパッド→ネット・Fritzing (.fzz) の接続をスクリプトで解析、PDF/JPG 回路図は 150–300dpi でラスタ化して目視で読んだ。

## 要約
- 回路図・設計ファイルを実際に読めたのは ORB (gEDA/PDF)、DE10Jamma (KiCad 5)、jammanator-pi (KiCad 8)、bad_raspi_jamma (KiCad 6)、PiPicoJamma (Fritzing)、JAMMA_2player_xbox360 (KiCad)、Raspberry Pi 公式 RP2040 VGA demo (KiCad)、jzdziarski/jamma 13 枚 (KiCad 10)、スーパーガン 3 種、Console JAMMAizer (説明書のみ)。
- 映像 DAC はバッファ無しで JAMMA に直結する設計が多数派 (DE10Jamma 6bit R-2R 2R=604/475Ω、jammanator 6bit R-2R 240/475Ω、PiPicoJamma 6本並列)。2kΩ 負荷で計算上 2.8–3.1V。バッファ付きは ORB (CLC4007 ×3.13 + 51Ω) と JAMMAizer (THS7375 + 約475Ω)。
- 入力は「10k プルアップ(3.3V) + 1k 直列 + 10–100nF」(DE10Jamma, jammanator) が実証済み。jammanator は加えて BAT54S クランプ + 74LVC244。
- **調べたオープン JAMMA 基板はどれもコインカウンタ (8/J)・ロックアウト (9/K) を駆動していない**。量産の実例は Neo Geo MVS の ULN2003 (コイル +12V 固定) のみで、ULN2003ADR (C7512) は JLCPCB Basic。
- **ヒューズ・TVS・逆接保護を持つオープン JAMMA 基板は見つからなかった**。
- JLCPCB Basic は 2026-11-10 時点で 351 件 (公式 API と CDFER CSV が完全一致)。音声アンプ IC・アルミ電解・ポリスイッチ/ヒューズは Basic に無い → 音声は秋月の LM386G-D08 (g114548, ¥40) 手はんだが最小構成。

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
| 入力 (1 入力あたり) | JAMMA ピン — 10k プルアップ (+3.3V, 4連アレイ R_Array_Concave_4x0603) — 100nF to GND (4連 C アレイ 0612, LCSC C62857) — 1k 直列 (4連アレイ) — BAT54S (SOT-23, LCSC C47546, 中点=信号、両端=+3.3V/GND のクランプ) — SN74LVC244APWR (3.3V, LCSC C7668) — MCP23017 (I2C, LCSC C558584) ×2。1k/10k アレイの LCSC は C20197 = 4D03WGJ0102T5E (1kΩ×4) / C29718 = 4D03WGJ0103T5E (10kΩ×4) (JLCPCB API の型番・仕様で確認)。保護回路は circuit_js/barrier_diode_simulation で 470Ω + 1N5711 + 100nF として検証 |
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

## 11. Arthrimus/Console-JAMMAizer (家庭用機 → JAMMA 変換)

- URL: https://github.com/Arthrimus/Console-JAMMAizer , LICENSE ファイル無し (ライセンス 未確認)。EDA: DipTrace (.dip バイナリ, 本環境では開けず) + Gerber zip + 取扱説明書 PDF ("Console JAMMAizer User Manual Version 1.0.pdf")
- 説明書 (原文): "Video and audio signals are amplified using a THS7375 and LM386 respectively so they can conform to the JAMMA video and audio standards." "The LM386 has internal gain control that can be adjusted using the SMD trimmer potentiometer ... This should usually be set as low as possible"。RGB 出力インピーダンス調整トリマ: "In stock form they are adjusted to approximately 475ohms but you can adjust them anywhere from 1Kohm all the way down to 0ohms. For most monitors the stock settings will look great"
- 派生設計スレッド (arcade-projects) も "JAMMAizer's default output impedance is 475 Ω" と記載 — https://www.arcade-projects.com/threads/rgb-amp-vga-to-jamma.15501/post-324475
- 推論: 75Ω/0.7Vpp 系の家庭用 RGB を 6dB アンプ + 約 475Ω 直列で JAMMA モニタへ出しても実用になっている = JAMMA モニタ側のコントラスト/ゲイン調整範囲がかなり広いことの傍証 (電圧実測値は 未確認)。

## 12. JLCPCB 部品クラス確認 (データ日付 2026-11-10)

### 確認方法と3ソースの一致
- 一次: JLCPCB 部品ライブラリ API `POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList` (`componentLibraryType`=base/expand, `preferredComponentFlag`)。`{"componentLibraryType":"base"}` で全件取得すると **Basic = 351 件** (2026-11-10 取得)。
- 二次: CDFER `jlcpcb-components-basic-preferred.csv` (https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv , Last-Modified 2026-11-10 05:55 GMT) の library_type=base も 351 件で、**C 番号集合が API と完全一致** (差分 0)。
- 三次: jlcsearch (https://jlcsearch.tscircuit.com/components/list.json?search=...) で C2500 BAV99,215 / C20526 MMBT3904 / C6186 AMS1117-3.3 / C23179 470Ω が is_basic=true。ただし jlcsearch の検索は在庫順の上位数件しか返さず ULN2003ADR(C7512) 等はヒットしなかった (検索仕様の限界、クラス不一致ではない)。
- Basic 351 件の構成 (API): 抵抗 182 + 抵抗アレイ 3 + MLCC 88 + タンタル 2 + その他半導体等。**アルミ電解・ヒューズ/ポリスイッチ・オーディオアンプ IC・ビデオアンプ・74HC86/74HCT/74LVC・BAT54 系は Basic に1件も無い**。

### 既存オープン設計で使われていた LCSC 部品のクラス (API, 2026-11-10)

| 部品 (使用プロジェクト) | C 番号 | クラス | 在庫 |
|---|---|---|---|
| 1k ×4 アレイ 0603x4 4D03WGJ0102T5E (jammanator 入力直列) | C20197 | **Basic** | 542,341 |
| 10k ×4 アレイ 0603x4 4D03WGJ0103T5E (jammanator プルアップ) | C29718 | **Basic** | 1,132,412 |
| 1k 0805 (jammanator) / 220Ω 0805 / 4.7k 0805 / 100Ω 0805 | C17513 / C17557 / C17673 / C17408 | **Basic** | 40,279,436 / 787,604 / 4,331,213 / 7,070,465 |
| 470nF 0805 CL21B474KBFNNNE (jammanator 音声結合) | C13967 | **Basic** | 822,821 |
| 240Ω 0805 1% (jammanator R-2R の R) | C17572 | Extended (Preferred) | 138,819 |
| 475Ω 0805 1% (jammanator R-2R の 2R) | C228851 | Extended | **3** |
| BAT54S,215 (jammanator 入力クランプ) | C47546 | Extended | 279,739 |
| 100nF ×4 C アレイ 0612 (jammanator) | C62857 | Extended | 12,358 |
| 100nF 0805 0805B104K500NT (jammanator) | C38141 | Extended | 2,588,515 |
| 10µF 1210 CL32B106KAJNNNE (jammanator) | C39232 | Extended | 138,818 |
| SN74LVC244APWR (jammanator) | C7668 | Extended | 107,701 |
| MCP23017T-E/SS (jammanator) | C558584 | Extended | 3,393 |
| SN74HC86PWR (jammanator CSync) | C2872580 | Extended | 1,098 |
| LM1117IMPX-3.3 (jammanator) | C23984 | Extended | 82,171 |
| 10nF 0805 CC0805KRX7R9BB103 (DE10Jamma) | C83170 | Extended | 1,628,794 |
| 470nF 0805 CC0805KKX7R9BB474 (DE10Jamma) | C106843 | Extended | 1,056,026 |
| 1000µF LKME1601E102MF (DE10Jamma) | C442834 | Extended | 0 |
| 1k 0805 AC0805FR-071KL (DE10Jamma) | C140870 | Extended | 635,999 |
| 100Ω 0805 RC0805FR-07100RL (DE10Jamma) | C105577 | Extended | 126,806 |
| 300k 0805 (DE10Jamma) | C114530 | Extended | 42,971 |
| 3362P-1-503LF 50k (DE10Jamma) | C81264 | Extended | 13,874 |

### 代替・推奨候補のクラス (API, 2026-11-10)

| 用途 | 部品 | C 番号 | クラス | 在庫 |
|---|---|---|---|---|
| コインカウンタ/ロックアウト | ULN2003ADR (SOIC-16) | C7512 | **Basic** | 368,016 |
| 入力クランプ (BAT54S の代替、シリコン) | BAV99,215 (SOT-23 直列2連) | C2500 | **Basic** | 1,104,395 |
| 同 (ショットキー) | BAT54S (SOT-23) | C7420333 | Extended (Preferred) | 555,134 |
| 同 | BAT54C,215 | C37704 | Extended (Preferred) | 388,716 |
| 小信号 NPN | MMBT3904 | C20526 | **Basic** | 4,313,904 |
| NPN 1.5A | SS8050 | C2150 | **Basic** | 3,059,537 |
| N-MOSFET | AO3400A / 2N7002 | C20917 / C8545 | **Basic** | 992,710 / 5,867,332 |
| P-MOSFET (逆接保護) | AO3401A / SI2301CDS | C15127 / C10487 | **Basic** | 1,638,262 / 300,062 |
| ショットキー | SS54 (5A) / SS34 (3A) / SS14 / B5819W SL | C22452 / C8678 / C2480 / C8598 | **Basic** | 1,735,691 / — / — / 727,407 |
| フライバック | 1N4148W / M7 (1A 1kV) | C81598 / C95872 | **Basic** | 3,471,971 / 5,410,796 |
| TVS (+5V 用, 双方向) | SMBJ6.5CA / P6SMB6.8CA | C7420377 / C78395 | **Basic** | 1,139,871 / 677,118 |
| ESD アレイ 12V 2線 | PSM712-LF-T7 | C32677 | **Basic** | 117,440 |
| TVS 5V 単方向 | SMBJ5.0A | C19077558 | Extended (Preferred) | 105,845 |
| 5V→3.3V LDO | AMS1117-3.3 | C6186 | **Basic** | 1,538,727 |
| シュミットインバータ | 74HC14D | C5605 | **Basic** | 315,750 |
| OP アンプ | LM358DR2G / NE5532DR / TL072CDT / LM324DT | C7950 / C7426 / C6961 / C71035 | **Basic** | — |
| DAC 用抵抗 0603 1% | 470Ω / 1k / 2k / 75Ω | C23179 / C21190 / C22975 / C4275 | **Basic** | 3,885,962 / 25,401,324 / 8,470,828 / 1,500,609 |
| 0603 1% Basic の他の値 (DAC 設計用) | 100/120/150/200/220/270/300/330/390/510/560/680/820Ω, 1.2k/1.5k/1.8k/2.2k/2.4k/2.7k/3k/3.3k/3.6k/3.9k/4.7k/4.99k/5.1k/5.6k/6.2k/6.8k/7.5k/8.2k/9.1k/10k ほか | basic_list (API) | **Basic** | — |
| MLCC | 100nF 0603 / 10nF 0603 / 470nF 0603 / 22µF 25V 0805 / 47µF 6.3V 0805 / 100µF 6.3V 1206 | C14663 / C57112 / C1623 / C45783 / C16780 / C15008 | **Basic** | — |
| タンタル | 100µF 6.3V B / 10µF 16V A | C16133 / C7171 | **Basic** | 626,367 / 888,477 |
| フェライト | BLM18PG121SN1D (2A) | C14709 | **Basic** | 1,859,491 |
| 音声アンプ | PAM8403DR-H / PAM8302AASCR / NS4150B / LM386MX-1 / LM386G-S08-R / HT6872 / TDA2822M / LM4871 | C17337 / C113367 / C189961 / C23573 / C85119 / C93112 / C725341 / C7494970 | すべて Extended | 3,388 / 20,707 / 161,685 / 4,590 / 8,208 / 28,179 / 5,171 / 15,988 |
| ポリスイッチ/ヒューズ | nSMD200 / BSMD1812-200 / SMD1812P200TF / 0466003.NRHF / 0451005.MRL | C70085 / C883156 / C21010 / C14165 / C48467 | すべて Extended | — |
| ロジック | 74HC165D (Preferred) / 74HC245D (Preferred) / SN74LVC4245APWR (Preferred) / 74HC86D / 74LVC244 | C5613 / C5625 / C7859 / C52140393 / C6079 | Extended | — |

### 秋月電子 (手はんだ部品) 在庫 (WebFetch, 2026-11-10)

| 部品 | 秋月 通販コード | 価格 | 在庫表示 |
|---|---|---|---|
| オーディオアンプIC LM386G-D08 (DIP-8) | g114548 | ¥40 | 在庫あり (11,965) — https://akizukidenshi.com/catalog/g/g114548/ |
| オーディオアンプIC LM386G-S08 | g114549 | ¥30 | 在庫あり (12,469) |
| 低電圧動作パワーアンプ NJM2113D | g111192 | ¥60 | 在庫あり (555) |
| PAM8012使用2ワットD級アンプモジュール AE-PAM8012 | g108217 | ¥300 | 在庫あり (692) |
| HT82V739使用ミニモノアンプキット | g107008 | ¥450 | 在庫僅少 |
| リセッタブルヒューズ 3A MF-R300 (トリップ 6A) | g112630 | ¥40 | 在庫あり |
| ポリスイッチ 3A RGEF300 (トリップ 5.1A) | g100769 | ¥30 | 在庫あり |
| リセッタブルヒューズ 1.85A MF-R185 | g112629 | ¥40 | 在庫あり |
| 1N4007 (単品) | g108332 | ¥10 | 在庫あり |
| TDA7297 / NJM2073 / LM4871 / TDA2822 / TA7368 | — | — | 検索ヒットなし |

(秋月の検索ページは curl では "現在メンテナンス中" の 403 になり、WebFetch では取得できた。検索 URL 形式 https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=<語>&search=search)

## 13. プロジェクト横断比較 (設計ファイルから確認した事実のみ)

| 項目 | ORB v0.3 | DE10Jamma | jammanator-pi | PiPicoJamma | RP2040 公式 VGA demo | JAMMAizer | jzdziarski Atari IF |
|---|---|---|---|---|---|---|---|
| ライセンス | MIT | 記載なし | MIT | GPL-3.0 | MIT | 記載なし | 非商用教育目的のみ |
| EDA | gEDA | KiCad 5 | KiCad 8 | Fritzing | KiCad | DipTrace | KiCad 10 |
| 入力 | ダイオード (カソード→JAMMA) + SoC 内蔵プルアップ 3.3V | 1k 直列 + 10k PU(3.3V) + 10nF | 10k PU(3.3V) + 100nF + 1k + BAT54S + 74LVC244 | 直結 | (該当なし) | (コントローラ側) | 74LS04 等 |
| DAC | 5bit 2進重み 510〜10k + 終端 200〜270Ω | 6bit R-2R 単一値 2R=475/604Ω | 6bit R-2R 240/475Ω | 6本 180〜8.2k | 5bit 2進重み 499〜8.06k | (アナログ入力) | (アナログ入力) |
| バッファ | CLC4007 ×3.13, 51Ω | なし | なし | なし | なし (75Ω 系) | THS7375 + 約475Ω 可変 | — |
| 計算上の 2kΩ 負荷フルスケール (推論) | ≈4.3V (OP アンプ出力振幅制限 未確認) | ≈2.8–2.9V | ≈2.9V | ≈3.1V | ≈2.9V | 未確認 | — |
| 同期 | 1k/470 分圧 → OP アンプ ×4.03 | GPIO → 100Ω | XOR(74HC86@5V) → 100Ω | 未確認 | GPIO → 47Ω (H/V 別) | — | 74LS86 XOR + 470Ω |
| 音声 | PAM8403 モジュール BTL (10/L) | TDA7496 @12V, SE 1000µF ×2 (10a/10b) | PAM8403 モジュール BTL (JP で 10/L) | PAM8610 モジュール | PWM→RC→47µF (ライン) | LM386 | LM386N-1 @5V, SE 1000µF→10, L=GND |
| コインカウンタ | なし | なし | なし | なし | — | — | なし (ネットのみ) |
| ヒューズ/TVS/逆接 | なし | なし | なし | なし | ショットキー→VSYS | 未確認 | なし |
| 3.3V 生成 | BBG 内 | DE10 内 | LM1117-3.3 | Pi/Pico 内 | Pico 内 SMPS + TLV70033 (音声用) | — | — |

## 14. 参照回路候補 (この基板向け、JLCPCB Basic のみで組める最小構成)

前提 (推論): RP2040 (Pico) が入力読取り・コイン処理・映像 (RGB 生成) を担当、JAMMA +5V 単一電源 (+12V は音声とカウンタのみ)。C 番号は全て API で Basic を確認 (2026-11-10)。

| # | 機能 | 候補回路 | 出典 (実証元) | 要適応点 |
|---|---|---|---|---|
| 1 | スイッチ入力 | JAMMA ピン — 10k PU→+3V3 (C29718 4連アレイ) — 100nF→GND (C14663) — 直列 1k (C20197 4連アレイ) — BAV99 (C2500, 中点=信号, 両端=+3V3/GND) — RP2040 GPIO (シュミット有効)。デバウンスはファーム | jammanator-pi の入力 (10k/100nF/1k/BAT54S) と DE10Jamma (1k/10k/10nF) | ①BAT54S (Extended) をシリコンの BAV99 (Basic) に置換 → クランプ電圧が約 0.3V 高く RP2040 絶対最大 IOVDD+0.5V を僅かに超え得る (推論)。12V 混入時に 3V3 へ電流が逆流するので直列を 4.7k アレイ (C1980, Basic) に上げる案も可 (推論)。②74LVC244 (Extended) は省略。③入力数 (約 26) が Pico の GPIO を超えるため 74HC165 (C5613, Preferred=Extended) 等の多重化が必要で、Basic のみでは 74HC14/74HC595 しかない (要設計) |
| 2 | RGB DAC | 各色 5bit 2進重み: 510Ω (C23193) / 1k (C21190) / 2k (C22975) / 3.9k (C23018) / 8.2k (C25981) 0603 1% を加算点で結び JAMMA R/G/B へ直結、バッファ無し。並列 ≈260Ω、2kΩ 負荷で ≈2.9V (推論計算) | Raspberry Pi 公式 RP2040 VGA demo (499/1k/2k/4.02k/8.06k) の値を Basic 値へ丸め、JAMMA への無バッファ直結は DE10Jamma / jammanator-pi / PiPicoJamma で実績 | 4.02k→3.9k、8.06k→8.2k、499→510 に置換 (誤差数 %)。代替: DE10Jamma 方式の単一値 R-2R を 470Ω (C23179) で組むと出力抵抗 235Ω・2kΩ 負荷 ≈2.86V だが 1色 14 本必要。モニタ入力インピーダンス差による明るさ変動は jammanator 作者も TODO としており、OP アンプは Basic の NE5532/LM358 では帯域不足の可能性 (推論) |
| 3 | 同期 | RP2040 で負極性 CSync を生成 → 100Ω 直列 (C22775) → JAMMA P (13 半田面) | DE10Jamma (3.3V FPGA GPIO → 100Ω)、RP2040 demo (47Ω) | 3.3V 振幅で足りることは DE10Jamma の実績のみ。5V 振幅が要る筐体向けには MMBT3904 (C20526) のオープンコレクタ + 5V プルアップ (推論、極性反転) を予備パターンに。74HC14 を 5V で使う昇圧は VT+ max 3.13V(@4.5V) で 5V 時は 3.3V 入力が保証外 (TI SN74HC14 データシート、5V 時は線形補間の推論) |
| 4 | 音声 | **Basic のみでは不可** (Basic に音声アンプ IC も電解コンデンサも無い)。最小構成: LM386 (秋月 LM386G-D08 g114548 ¥40 を手はんだ) 単電源・単端 (SE)、入力ボリューム 10k → IN+、出力 470–1000µF 電解 (手はんだ) → JAMMA 10、JAMMA L = GND、Zobel 10Ω+0.1µF、pin1–8 オープン (利得 20) | jzdziarski Atari JAMMA Interface (LM386N-1 @+5V、1000µF→10、L=GND)、Console JAMMAizer (LM386) | LM386N-1 の動作電源は 4–12V (TI データシート)。+5V では出力 ≈0.25–0.3W 級 (325mW typ@6V/8Ω から推論)。+12V で使うなら上限ぎりぎりなので 1N4007 直列などで電圧を下げる (推論)。BTL D級 (PAM8302 C113367 / PAM8403 / NS4150B, いずれも Extended) は出力が強いが JAMMA L が GND の筐体で破損リスク (第1パスノートの警告) |
| 5 | コインカウンタ/ロックアウト | RP2040 GPIO → ULN2003ADR (C7512) 入力、出力 → JAMMA 8 / J (カウンタ) と 9 / K (ロックアウト)、COM (pin 9) → +12V (内蔵クランプダイオードを使用) | Neo Geo MVS (NEO-F0 → ULN2003 オープンコレクタ、コイルは +12V 固定) | オープン JAMMA 基板での実例は無し。ULN2003A は 2.7kΩ 入力抵抗で VI(on) 規定は 250mA で 2.7V など → 3.3V 駆動で数百 mA 以下なら可 (データシート値からの推論)。カウンタの電流・パルス幅は 未確認 (50–100ms 程度を初期値にして実機調整、推論) |
| 6 | 電源入力 | JAMMA +5V (3,4,C,D 全指) → [ポリスイッチは Basic 無し: 秋月 MF-R300 g112630 を手はんだ、または省略] → SMBJ6.5CA (C7420377) を +5V–GND 間 → 100µF タンタル (C16133) + 22µF MLCC (C45783) → 5V 系。Pico VSYS へは B5819W SL (C8598) 経由 (Pico データシートの "power ORing")。3.3V は Pico の 3V3 出力、または AMS1117-3.3 (C6186) | Pico データシート / RP2040 demo (MBR120 → VSYS)、jammanator (LM1117-3.3) | オープン JAMMA 基板にヒューズ・TVS の実例は無く、ここは推論設計。+12V は音声とカウンタのみに使い、+12V 系 TVS の Basic 品は無い (PSM712 C32677 は 12V 信号線用 ESD アレイ) |
| 7 | ESD | 入力は #1 の BAV99 + 1k + 100nF で兼ねる。映像・音声出力は直列抵抗 (DAC 抵抗/100Ω) が実質の保護。RP2040 自体の HBM は 2kV | jammanator-pi (BAT54S + 1k + 100nF) | 専用 TVS アレイ (SRV05-4 C85364 は Preferred=Extended) を入れるなら Extended |

推論 (全体): Basic のみで完結しないのは「音声アンプ IC」「電解コンデンサ」「ポリスイッチ/ヒューズ」の 3 種。いずれも秋月で DIP/リードの在庫品があるため手はんだに回すのが現実的。JLCPCB 側 Extended を許すなら PAM8302AASCR (C113367) 1 種で音声が済むが BTL 注意。

## 既存ノートへの訂正

対象: jamma_standard.md (第1パス)。
1. 「DE10Jamma は 6bit R-2R DAC(604Ω/1kΩ系)×3」→ **誤り**。R-2R は単一値 2R のみで構成 (R は 2R を2本並列)。BOM 値 604Ω (Bourns CAY16-6040F4LF)、回路図値 475Ω。1kΩ は入力側の直列抵抗 (28 本) で DAC ではない — DE10Jamma.net / README "A single 2R value used in parallel to generate the R value"。
2. 「DE10Jamma ... LCSC部品番号入りBOM(10nF C83170, 1k C140870 等。JLCPCB Basic適合性は個別確認)」→ 確認結果: C83170・C140870・C106843・C105577・C114530・C81264・C442834 はすべて **Extended** (C442834 は在庫 0)。DE10Jamma の BOM は Basic 部品ではない (JLCPCB API, 2026-11-10)。
3. 「DE10Jamma(ライセンスは未確認)」→ リポジトリに LICENSE ファイルが無いことを git clone で確認 (ライセンス表示なし)。
4. 「Console JAMMAizer は OSHPark 公開との情報と "Not open source" との情報が矛盾」→ 部分解決: https://github.com/Arthrimus/Console-JAMMAizer に DipTrace 設計ファイルと Gerber、取扱説明書が公開されているがライセンス表示は無い。映像 THS7375・音声 LM386 (説明書)。
5. 「ORB: 24個のスイッチングダイオード(1N4148系)」→ BOM の記述は "Diode switching 100V 0.15A 4ns SMD1206"、回路図注記は "fast switching diode 15V, 4ns" で、品番の指定は無い。向きはカソードが JAMMA 側 (5V 入力から 3.3V GPIO を切り離す用途)。
6. 入力推論「10k プルアップ(または内蔵)+1k直列+100nF〜10nF」→ DE10Jamma (1k/10k/10nF) と jammanator-pi (10k/100nF/1k/BAT54S) の実設計で裏付けられた。ただし RP2040 の内蔵プルアップは 50–80kΩ と弱い (RP2040 データシート) ので「内蔵」で代替するのは推奨しない (推論)。
7. 「コインカウンタ … 2N2222/2N3904 等の小信号トランジスタで駆動可」(確度低) → オープン JAMMA 基板での実例は見つからず。量産実例として確認できたのは MVS の ULN2003 のみ。ULN2003ADR は JLCPCB Basic (C7512)。
8. 第1パスの他ノート (parts_class_reverification.md) は「BAT54S/C は Preferred」としているが、これは C7420333 (BAT54S) / C37704 (BAT54C,215) の話で正しい。一方 jammanator-pi が使う BAT54S,215 (C47546) は **Extended (非 Preferred)**。品番が同じでも C 番号でクラスが異なる点に注意。

## まだ未確認のこと
- ORB の CLC4007 単 5V 電源時の出力振幅 (計算上 4.3V 出力が必要で飽和の可能性) と 74HC4066 の正確な役割 (回路図から配線は読めたが意図の記述なし)。
- DE10Jamma の TDA7496 で MUTE (pin10)・STBY (pin9) が GND 接続になっている点の動作論理 (ST のデータシートが 503/接続断で取得できず)、および Mono ジャンパ時に 10a/10b が同相になる点の作者意図。
- PiPicoJamma の同期回路 (Fritzing ファイルからは特定できず)。
- JAMMA モニタ (日本の筐体: Astro City / Egret / Blast City 等) が 3.3V 振幅の CSync を確実に受けるか (DE10Jamma の実績のみ)。
- コインカウンタのコイル電流・抵抗・必要パルス幅、筐体ごとのカウンタ電圧 (5V/6V/12V)。
- LM386 を JAMMA +12V で使う場合の実際の出力・発熱 (UTC LM386G のデータシート未確認)。
- 映像バッファを Basic 部品 (MMBT3904 エミッタフォロワ等) で組んだ JAMMA 実例 (見つからず)。
- arcade-projects の Minigun (EasyEDA zip)、Pi2Jamma の回路図、Recalbox RGB JAMMA・RGB-Pi JAMMA は非公開またはログイン必須で未取得。
