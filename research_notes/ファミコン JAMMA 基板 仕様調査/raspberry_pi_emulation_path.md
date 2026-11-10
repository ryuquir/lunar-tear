# Raspberry Pi 系ボードによるエミュレーション方式（Mode B）調査ノート

調査日: 2026-11-10。表記ルール: 出典付きの事実は「Cited Findings」、筆者の推論は「Inferences」に分離。出典を確認できなかった事項は「未確認」と明記。
主要一次資料（本調査でダウンロードして本文を grep 確認したもの）:
- RP2350 Datasheet: https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- RP2040 Datasheet: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet: https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- sanni Cart Reader NES.ino: https://raw.githubusercontent.com/sanni/cartreader/master/Cart_Reader/NES.ino

---

## 1. 候補デバイスとソフトウェア（Linux Pi / ベアメタル / Pico・Pico 2）

### Takeaway
「本物のカートリッジを差して遊ぶ」という前提では、RP2350（Pico 2、または RP2350B 搭載モジュール）＋既存 Pico 用 NES エミュレータ（InfoNES 系）が最有力。Linux Pi（Zero 2 W〜5）は精度の高い Mesen/Nestopia を使え DPI で 15 kHz RGB も出せるが、GPIO が DPI 映像でほぼ埋まり、カートリッジバスを読むには別マイコンが必要、加えて SD カード破損対策と起動時間の課題がある。既存 Pico NES エミュレータはいずれも HDMI/DVI か VGA 出力で、15 kHz アナログ RGB と実カートリッジ読み込みの両方を備えたものは見つからなかった（要改造）。

### Cited Findings
**Pico / Pico 2 系エミュレータ**
- pico-infones（shuichitakano）: Raspberry Pi Pico (RP2040) 用、HDMI で映像と音声を出力（PicoDVI ベース、Pico-DVI-Sock ピン配置）。ROM は `picotool load foo.nes -t bin -o 0x10080000` でフラッシュに書き込み、標準 Pico では 1.5 MiB まで。バッテリーバックアップ SRAM はタイトル毎 8 KB をフラッシュに保存（リセット時／ROM 選択時に書き込み）。GPL-3.0。マッパー一覧は README に記載なし — https://github.com/shuichitakano/pico-infones
- pico-infonesPlus（fhoedemakers）: RP2040 と RP2350 の両方に対応（Pico/Pico W/Pico 2/Pico 2 W、Pimoroni Pico Plus 2、Adafruit Fruit Jam、Waveshare RP2350-PiZero 等）。出力は DVI/HDMI（HSTX）のみで VGA/アナログ RGB の記載なし。ROM は SD カード（FAT32/exFAT）から。PSRAM 無しでは選択 ROM を起動時にフラッシュへ書き込む（数秒）、PSRAM 有りなら PSRAM に直接読込。SRAM 自動保存とセーブステートは SD カードへ。GPL-3.0 — https://github.com/fhoedemakers/pico-infonesPlus
- 同 README（後半）: セーブステートはマッパー 0–4 で動作確認、それ以外は不定。未対応マッパーは "Mapper n is unsupported." と表示。MMC5 (5)、VRC6a (24)、30、Sunsoft FME-7 (69)、VRC7 (85) が実装済み。マッパー 85（Lagrange Point）は RP2040 不可・RP2350 で動作。拡張音源: MMC5・VRC6・FDS・Sunsoft 5B は RP2040 でも動作、VRC7 は RP2350＋PSRAM＋オーバークロック必須で「時々グリッチ」。音声経路は HDMI または I2S/ライン出力。RP2040 ボードでは PAL/Dendy ゲームも 60 Hz で動作 — https://github.com/fhoedemakers/pico-infonesPlus
- xrip/pico-nes: MURMULATOR 開発ボード（RP2040）向け、VGA 出力、microSD スロット、GPL-3.0。DAC 抵抗値・音声・マッパーは README に記載なし — https://github.com/xrip/pico-nes
- Ben Stragnell の Pico NES エミュレータは VGA と PWM 音声出力（二次資料） — https://www.hackster.io/news/ben-stragnell-gets-super-mario-bros-running-on-the-raspberry-pi-pico-in-a-custom-nes-emulator-6dfcc3533ee7

**Linux Pi 上のエミュレータ精度**
- Mesen が最も正確と広く評価。古いフォーラム投稿ではテスト通過率 Mesen 100%、Nestopia 約 80%、QuickNES 約 70%、FCEUmm 約 50%（古い数値で参考程度） — https://retropie.org.uk/forum/post/140102 ／ https://retropie.org.uk/forum/post/140088
- 一部 ARM 機では Mesen が処理落ちし Nestopia/FCEUmm を使うとの報告（Pi 4/5 での Mesen ベンチマークは見つからず） — https://forums.libretro.com/t/fceumm-nestopia-the-evolution-of-fceumm/30970
- libretro Mesen2 コアの文書 — https://docs.libretro.com/library/mesen2/

**無人運用（電源断）関連**
- raspi-config の Overlay File System（`sudo raspi-config nonint do_overlayfs` で切替）で root を読み取り専用化できる。Bookworm では /boot 以外の全マウントが読み取り専用になるとの報告、Pi 5 64-bit では挙動差の報告あり — https://github.com/raspberrypi/bookworm-feedback/issues/137 ／ https://forum.core-electronics.com.au/t/pi-5-bookworm-64bit-cannot-set-filesystem-to-read-only/21769 ／ https://pidiylab.com/raspberry-pi-read-only-root-filesystem-setup/（二次資料）
- 読み取り専用 root と tmpfs による運用解説 — https://www.dzombak.com/blog/2024/03/running-a-raspberry-pi-with-a-read-only-root-filesystem/ ／ https://learn.adafruit.com/read-only-raspberry-pi

### Inferences
- Linux Pi 案: 映像（DPI）と JAMMA 入力は既存 Pi2Jamma/RGB-Pi 同様に実現可能。しかし実カートリッジを読むには GPIO が足りない（§4 参照）ため、カート読み取り用に別マイコン（例: Pico）を USB 経由で接続する 2 チップ構成になる。Linux＋SD＋別マイコンで部品点数・起動時間・電源断リスクが増え、「部品種類・点数最小」の方針と相性が悪い。
- Pico 2 案: ファイルシステムを持たず ROM はブートロムで保護されるため電源断でブート不能になるリスクが小さい。既存 InfoNES 系はマッパー 0/1/2/3/4/5/24/69/85 等をカバーするが、実カート対応では「ダンプした PRG/CHR を PSRAM またはフラッシュに置く」処理を追加する必要がある。
- ベアメタル Pi（Circle ベース等）は今回調査範囲内で具体的な NES＋DPI 15 kHz 実例の確認まで到達できず（Gaps 参照）。

### Gaps
- Pi Zero 2 W / 3 / 4 / 5 の起動時間・消費電力の実測値: 一次資料を取得できず未確認。
- ベアメタル Pi 用 NES エミュレータ（Circle ベース等）の現状: 未確認。
- pico-infonesPlus の正確な対応マッパー全一覧と最新リリース日: README からは取得できず未確認。
- InfoNES 系の精度（テスト ROM 通過率）: 資料見つからず未確認。

---

## 2. Raspberry Pi（Linux）から 15 kHz アナログ RGB／JAMMA 入出力

### Takeaway
DPI（GPIO0–27 の ALT2）＋抵抗ラダー DAC で 15 kHz RGB は確立済み技術。Bookworm 以降は `vc4-kms-dpi-generic` overlay で任意タイミングを指定し、`rgb666-padhi` で GPIO18/19 を PWM 音声用に空けるのが定番。Pi 5（RP1）は 240p/288p プログレッシブ対応、2025 年に PIO でインターレースと実験的 CSync を追加。JAMMA 入力はシフトレジスタ（Pi2Jamma: 74LS165×3）か I2C エキスパンダ（MCP23017×2）で読むのが既存製品の方式。

### Cited Findings
- DPI は GPIO Bank0 ALT2: GPIO0=PCLK、GPIO1=DE、GPIO2=VSYNC、GPIO3=HSYNC、GPIO4–27=DPI_D0–D23。`rgb666-padhi` は "Change to RGB666 output on GPIOs 0-9, 12-17, and 20-25"。I2C/SPI と競合するので `dtparam=i2c_arm=off`、`dtparam=spi=off`。Bookworm 以降 `dpi_output_format`/`dpi_timings` は `vc4-kms-dpi-generic` overlay に置き換え — https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#display-parallel-interface-dpi
- Pi 5（RP1）: 240p・288p のプログレッシブは当初から対応。インターレースは RP1 の PIO が DPI の HSYNC/DE を監視して VSYNC を生成する方式で追加（PIO 4 SM 中 2 個、命令メモリの大半を使用）。DE は GPIO1 に必ず出力。CSync は DPI 補助信号＋PIO で合成するが「改造ハードと GPIO1 に DE を出さないピン設定」が必要（実験的）。PIO タイミングのジッタ最大 ±5 ns。最新 Raspberry Pi OS / rpi-6.12.y カーネル推奨 — https://www.raspberrypi.com/news/how-we-added-interlaced-video-to-raspberry-pi-5/
- 同記事の設定例（576i）: `dtoverlay=vc4-kms-dpi-generic`、`dtparam=clock-frequency=13500000`、`dtparam=hactive=720,hfp=12,hsync=64,hbp=68`、`dtparam=vactive=576,vfp=5,vsync=5,vbp=39`、`dtparam=vsync-invert,hsync-invert`、`dtparam=interlaced` — https://www.raspberrypi.com/news/how-we-added-interlaced-video-to-raspberry-pi-5/
- 240p の KMS 設定例（フォーラム）: 13.5 MHz、hactive=640,hfp=52,hsync=64,hbp=108、vactive=240,vfp=26,vsync=3,vbp=43 — https://retropie.org.uk/forum/post/303319（二次資料、要実機確認）
- Pi2Jamma（Arcadeforge、設計 Jochen Zurborg）: 映像は内蔵 VGA666 回路（GPIO4–21）＋THS7314 ビデオアンプ、`dtoverlay=vga666`、`dpi_mode=87`、`hdmi_timings=320 1 16 30 34 240 1 2 3 22 0 0 0 60 0 6400000 1`（240p, 旧ファームウェア方式）。入力は 74LS165×3 で 24 入力をわずかな GPIO で読む（`pikeyd165` がキーボードキーに変換）。音声は Pi の 3.5 mm 出力をケーブルで基板へ→LM380N 2.5 W アンプ。Pi 3 以上が必要。回路図・ライセンスの公開記載なし — https://falz.net/wiki/Pi2jamma_hardware_and_software_info
- Pi2Jamma 系は GPIO から給電、外部電源不要（販売店記載） — https://www.arcadexpress.com/en/video-converters/258-tarjeta-pi2jamma.html
- RGB-Pi 互換 JAMMA 基板の一例は 40 ピン GPIO だけで映像・音声・入力を処理し、2P 分の入力に I2C GPIO エキスパンダ MCP23017×2 を使用（検索結果要約による二次情報、原典 URL 未特定） — 未確認
- Pi400RGB（llegoff）: DPI mode 6 / `rgb666-padhi` で GPIO18/19 を空け、`dtoverlay=audremap,pins_18_19` で PWM 音声。`gpio=2-9,12-17,20-24=a2`（GPIO0/1 は不使用）。KMS 例: `dtoverlay=vc4-kms-dpi-generic,rgb666-padhi`。ライセンス記載なし — https://github.com/llegoff/Pi400RGB
- Elektor の Pi Zero 用 VGA＋音声も GPIO18/19 の PWM 音声を使用し、そのために DPI mode 3 で動作 — https://www.elektormagazine.com/index.php/labs/vga-audio-interface-for-raspberry-pi-zero
- Gert VGA666: ライセンス GPL-3.0（© 2014 Fen Logic）、リポジトリに design_data/documents — https://github.com/fenlogic/vga666 ／ 設計マニュアル抜粋では直列抵抗の基準計算 Rs = 3.3/0.7×75−75 ≈ 278 Ω、6 ビットを 1:2:4:8:16:32 の比で並列 — https://static.chipdip.ru/lib/682/DOC041682208.pdf（具体的な抵抗値は回路図画像のみで本調査では未確認）

### Inferences
- `rgb666-padhi` 使用時、DPI が使うのは GPIO0–9,12–17,20–25 の 22 本。PCLK/DE を出さなければ（Pi400RGB 方式）GPIO0,1,10,11,18,19,26,27 の 8 本が空き、18/19 を PWM 音声に使うと残り 6 本。ここに 74HC165 系シフトレジスタ（3 本: LOAD/CLK/DATA）を繋げば JAMMA 入力は読めるが、カートリッジバス（約 54 信号）には全く足りない。
- JAMMA は複合同期（CSync）が標準。Pi 0–4 の DPI は HSYNC/VSYNC 別出力なので、XOR/AND ゲート（74HC86/74HC08 など JLC Basic にありそうな汎用ロジック）で合成するのが一般的手法と思われるが、本調査では出典を確認していない（未確認）。
- 6 ビット/色の抵抗 DAC は 1:2:4:8:16:32 の 6 本×3 色＝18 本の抵抗。部品点数最小化を重視するなら 3〜4 ビット/色（Famicom のパレットは 64 色程度）で十分な可能性がある（推論）。
- 音声: PWM（GPIO18/19）→RC フィルタ→既存のアンプ段で JAMMA スピーカー駆動、という構成が最小。Pi Zero 2 W は 3.5 mm ジャックを持たないので PWM 方式が必要（推論）。

### Gaps
- VGA666 の具体的抵抗値: 回路図を取得できず未確認。
- RGB-Pi JAMMA の回路・入力方式の一次資料: 未確認。
- Pi 0–4 の KMS（vc4）での 240p 安定性・CSync 生成の公式記述: 未確認。

---

## 3. Pico（RP2040/RP2350）から 15 kHz アナログ RGB

### Takeaway
PIO による VGA/DPI 生成は公式ライブラリ（pico-extras の pico_scanvideo_dpi、BSD-3-Clause）があり、タイミングを 15.7 kHz/60 Hz に変更すれば理論上 15 kHz RGB に流用可能。ただし「Pico NES エミュレータ＋15 kHz RGB 出力」の公開実例は見つからなかった。

### Cited Findings
- pico-extras の `pico_scanvideo_dpi`: パラレル RGB＋VSYNC/HSYNC/DEN/CLOCK を出す。"Highly functional and stable, but the API is subject to change"。参照回路は "Hardware design with RP2040" に記載。BSD-3-Clause — https://github.com/raspberrypi/pico-extras
- PICO9918（RP2040 で TMS9918A を再現）は PIO で VGA または SCART RGB を出力、PIO SM の一つが 12 ビット RGB を出力 — https://github.com/visrealm/pico9918/wiki/Firmware-Architecture
- RP2040 PIO で R/G/B/HSYNC/VSYNC を CRT 向けに出すアーケード表示アダプタの実例 — https://scd31.com/posts/building-an-arcade-display-adapter
- RP2040/RP2350 用 NES エミュレータで 15 kHz RGB 出力するものは検索で見つからず（xrip/pico-nes は VGA 31 kHz、他は HDMI/DVI） — https://github.com/xrip/pico-nes ／ https://github.com/fhoedemakers/pico-infonesPlus

### Inferences
- InfoNES 系はライン単位でレンダリングするため、VGA (31 kHz) 版のラインダブリングを止めて 15.7 kHz・262 ライン・60 Hz のタイミングにし、HSYNC と VSYNC を PIO 内で XOR した CSync を出すのは比較的素直な改造（推論・未検証）。DAC は Pico の GPIO 数制約から R/G/B 各 3〜5 ビット程度。
- RP2350 の HSTX はデジタル（DVI）向けで、アナログ RGB には PIO＋抵抗 DAC を使うことになる（推論）。

### Gaps
- 15 kHz 出力の Pico NES エミュレータ実例: 見つからず。
- Murmulator の VGA 抵抗 DAC 値: 未確認。

---

## 4. 実カートリッジとの連携（ダンプ方式 vs 実時間バスブリッジ）

### Takeaway
Famicom 60 ピンカートリッジは CPU 側 27 本＋PPU 側 27 本＝デジタル信号約 54 本（＋音声 2 本）を要し、Pi 40 ピン（28 GPIO）・Pico（26 GPIO）・RP2350B（48 GPIO）のいずれも直結では足りない。ダンプ方式なら 74HC595/74HC574 等でアドレスを外付けラッチすれば Pico でも可能で、既存ダンパ（sanni、ClusterM）は CRC データベース照合＋手動選択でマッパーを決めている。実時間バスブリッジは 6502 ソケット置換の RP2350B 実例はあるが、Famicom で CPU と PPU 両バスを同時に駆動する公開実例は見つからなかった。

### Cited Findings
- Famicom 60 ピン: CPU A0–A14（15）、CPU D0–D7（8）、M2・R/W・/ROMSEL・/IRQ（4）、PPU A0–A13（14）、PPU D0–D7（8）、PPU /RD・/WR（2）、PPU /A13（1）、CIRAM A10・CIRAM /CE（2）、Audio from 2A03（ピン45）・Audio to RF（ピン46）、+5V（30）、ピン31（基板版により 5V/カート検出）、GND（1,16）。EXP ピンは無い（NES 72 ピンのみ） — https://www.nesdev.org/wiki/Cartridge_connector
- GPIO 数: Pico 2 は RP2350 の 30 GPIO のうち 26 本を引き出し（GPIO0–22 はデジタル専用、GPIO26–28 は ADC 兼用） — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf ／ RP2350A（QFN-60）30 GPIO・ADC 4、RP2350B（QFN-80）48 GPIO・ADC 8 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf ／ Pi の DPI 対象は GPIO0–27（28 本） — https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#display-parallel-interface-dpi
- sanni Open Source Cartridge Reader（NES.ino）: PRG の最終 8 KB（$8000 と、MMC3 用に $E000）の CRC32 を計算し SD カード上の `nes.txt` データベースを検索、該当なしならマッピングを手動選択。マッパー表 `mapsize[]` に各マッパーの PRG/CHR/RAM サイズ範囲と "[sram r/w]" 等の注記。PRG 読み出しは「アドレス設定→PHI2(M2) High→/ROMSEL を A15 に応じて Low→1 µs 待ち→読む」、書き込みでは M2 を Low→High→Low とトグル。読み出し後は "Set phi2 to high state to keep cartridge unreseted"。リポジトリは 2026-06-15 にアーカイブ（読み取り専用） — https://raw.githubusercontent.com/sanni/cartreader/master/Cart_Reader/NES.ino ／ https://github.com/sanni/cartreader
- ClusterM famicom-dumper-client: マッパー毎の C# スクリプト（`IMapper`）で PRG/CHR ダンプとミラーリングを定義、iNES 番号・名前・スクリプトパスで選択、既定は mapper 0、自動マッパー検出の記載なし。バッテリー PRG-RAM 読み書き、FDS ダンプ／書き込み対応。GPL-3.0。ハードは famicom-dumper-writer / famicom-dumper — https://github.com/ClusterM/famicom-dumper-client
- dumping.guide: ダンプ前にデータベースからマッパーとサイズ情報を得る必要がある — https://dumping.guide/carts/nintendo/nes
- Retro Freak（CYBER Gadget）はカートリッジからゲームを SD カードに吸い出して本体にインストール可能（販売店記載）。マッパー対応表は見つからず — https://www.genkivideogames.com/cyber-gadget-retro-freak-controller-adapter-set-new-cyber-gadget-miscellaneous-hardware/cyrfb ／ https://www.nintendolife.com/news/2017/01/hardware_review_putting_the_retro_freaks_range_of_accessories_to_the_test
- pico6502（eaw.app）: RP2350B を DIP-40 フットプリント内（52×19 mm、6 層）に収め、6502 ソケットに挿して 6502 を置換。PIO 8 SM（3 ブロック）が PHI1/PHI2 生成・アドレス・データ・IRQ/NMI 監視を担当し、Core1 が CPU エミュレーション。"complete, cycle-accurate control" を謳い、BBC Model B（2 MHz）で実機比約 97%（RP2350 340 MHz、PHYSICAL モード）。5 V 側は 74AHCT244（アドレス/制御）・74AHCT245（データ）で緩衝、TLV62569 で 5 V→3.3 V。初回書き込みは USB マスストレージ、以後 OTA（5 MB×2 パーティション）。ESP32 を併載。本体のライセンス記載なし。2026-10 まで更新 — https://eaw.app/pico6502/
- chiplab の実験: 2A03 内部 6502 は入力クロックの 1/12 で動作（約 12 MHz 供給が必要）、NMOS 2A03 は低速（DC）クロック不可。ATmega＋シリアルでのサイクル毎駆動は速度不足で 2A03 はリセットベクタに到達せず失敗 — https://emulationonline.neocities.org/systems/chiplab/experimenting-with-highspeed-chips/
- 実カートを読んでエミュレーションする実例として Game Bub（FPGA 携帯機、ROM とオリジナルカートの両方を遊べる、作者は「FPGA は実機周辺とのインターフェースで有利」と述べる）がある — https://hackaday.com/2025/02/15/page/2（二次資料）

### Inferences
- **ダンプ方式**（推奨）: 起動時に PRG/CHR を読み出して PSRAM またはフラッシュに格納→エミュレート。Pico 2（26 GPIO）なら、例: アドレス 15+14 本を 74HC595 シフトレジスタや 74HC574 ラッチで時分割出力、データ 8 本（CPU/PPU 共用バスにするなら 74HC245 で切替）を直結、制御線（M2、R/W、/ROMSEL、/RD、/WR、CIRAM 系）を直結、という構成で可能と考えられる。読み出しは 1 バイト数 µs でも 512 KB で数秒以内（推論、実測なし）。
- マッパー判別: sanni 方式（PRG 末尾 8 KB の CRC32 → NES 2.0 系データベース）をそのまま採用できる。データベースはフラッシュに格納。未登録カートは「判別不能」として起動しない設計が無難。
- 制約: (1) バッテリーバックアップ SRAM は実カートの SRAM を直接使えない（エミュ側コピーになる）ので、起動時に読み込み・終了時に書き戻しが必要だが、電源断で書き戻せない→定期的な書き戻しが必要。(2) 拡張音源（VRC6/VRC7/MMC5/N163/5B/FDS）はエミュレータ側での再現が必須で、InfoNES 系では一部のみ対応。(3) 独自・海賊マッパーはデータベース外。
- **実時間バスブリッジ**: CPU バス 1.79 MHz（約 559 ns/サイクル）に加え、PPU バスはおよそ 2 ドット毎（5.37 MHz ドットクロック）にフェッチがあり、MMC3 などは PPU A12 の立ち上がりを数えて IRQ を出すため、PPU のフェッチ順序をバス上で正確に再現する必要がある（NESdev の既知仕様に基づく推論、本調査では一次資料未再確認）。約 54 本の信号は RP2350B の 48 GPIO でも直結不可で外付けラッチが必要。pico6502 は 2 MHz の単一 CPU バスで 340 MHz オーバークロックを要しており、CPU＋PPU 2 系統を同時に正確に駆動しつつ 15 kHz 映像を生成するのは RP2350B 1 個ではかなり厳しい（推論）。
- 実時間方式の利点は拡張音源をカートのアナログ出力（ピン46）でそのまま得られること（エミュの APU 音をピン45に入れ、ピン46から取り出す）。

### Gaps
- NES 2.0 XML データベース（nes20db）のライセンス・取得 URL: 未確認。
- 実ダンプ時間の実測値（sanni / ClusterM）: 未確認。
- Famicom カートの CPU＋PPU 両バスをマイコンで実時間駆動した公開プロジェクト: 見つからず。

---

## 5. 5 V インターフェース

### Takeaway
RP2350 の非 ADC GPIO（RP2350A: GPIO0–25、RP2350B: GPIO0–39）は IOVDD=3.3 V 給電中に限り 5.5 V まで耐える「Digital IO (FT)」。ADC 兼用ピンと RP2040・Pi SoC は 5 V 非耐性。E9 エラッタは A2 のみ（A3 で修正、量産は A4）。5 V カートを読むだけなら RP2350 の FT ピン直結も規格上は可能だが、出力 High は 3.3 V なので 5 V CMOS 入力のカート（VIH が高いもの）には 74HCT/74AHCT バッファが安全。

### Cited Findings
- RP2350 Table 1673 "Digital IO (FT)": "very little current flows into the pin whilst it is below 3.63 V and IOVDD is 0 V. Additionally, they will tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V." — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- 絶対最大: 通常ピン VPIN = −0.5〜IOVDD+0.5 V、FT ピン VPIN_FT = −0.5〜5.5 V（条件 IOVDD=3.3 V） — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- ピン表: GPIO0–25 は Digital IO (FT)、GPIO26_ADC0〜GPIO29_ADC3 は "Digital IO / Analogue"（IOVDD / ADC_AVDD）。RP2350B では ADC は GPIO40_ADC0〜GPIO47_ADC7 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Pico 2 Datasheet: "the ADC capable GPIO26-29 have an internal reverse diode to the IOVDD (3V3) rail and so the input voltage must not exceed IOVDD plus about 300 mV"、"Normal digital GPIO pins 0-25 … voltage can safely be applied to these pins when RP2350 is unpowered" — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- 公式ブログ (2025-07-29): "RP2350 is now officially 5V tolerant!"、"keep IOVDD powered when 5V is applied to any GPIO pad, otherwise the pad will be damaged." A2 が 5 V 耐性かは記事中で明言なし — https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/ ／ データシート改訂履歴にも "Added information about the GPIOs being 5 V tolerant." — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- RP2350-E9: "Increased leakage current on Bank 0 GPIO when pad input is enabled"、Affects: RP2350 A2、GPIO0–47。不定領域で約 120 µA を吐き約 2.2 V に保持、内蔵プルダウンでは不可、8.2 kΩ 以下で引けば回避、入力イネーブル解除でリセット、プルアップは正常 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf（Appendix D.5.1）
- 修正ステッピング: データシート Appendix C.2.1 は "Stepping A3 introduces … Fix RP2350-E9"。版履歴: A2=Initial release、A3=Internal development, samples, and limited production、A4=Production version — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf ／ 公式ブログは「A4 で E9 修正」と表現、A2 生産終了、A4 は A2 とドロップイン互換、約 3 万個の A3 を Pico 2 / Pico 2 W に使用、"Eventually all Pico 2 products will use the A4 stepping"、ステッピングはパッケージ上面刻印で判別 — https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/ ／ 二次: https://hackaday.com/2025/07/31/raspberry-pi-rp2350-a4-stepping-addresses-e9-current-leakage-bug ／ https://www.cnx-software.com/2025/07/29/raspberry-pi-rp2350-a4-stepping-fixes-e9-gpio-erratum-9-glitching-bugs-introduces-2mb-flash-variants/
  - 表現の差（A3 で修正 vs A4 で修正）は矛盾ではなく、A3 は限定生産の中間版で A4 が量産版という関係。
- RP2040: FT ピンは「IOVDD=0 V で 3.63 V 未満なら電流ほぼ流れない」のみで 5 V 耐性の記述なし。絶対最大 VPIN = IOVDD+0.5 V — https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- pico6502 は 5 V 6502 バスへの接続に 74AHCT244/74AHCT245 を使用 — https://eaw.app/pico6502/

### Inferences
- Pico 2 で 5 V に直結してよいのは GPIO0–22（Pico 2 で引き出されている非 ADC ピン）の 23 本。GPIO26–28 は 5 V 不可。
- 電源シーケンス: 5 V カートの信号が RP2350 より先に立ち上がる／RP2350 の 3.3 V が落ちた後も 5 V が残る状況は「IOVDD 未給電で 5 V 印加」に当たり違反。JAMMA 電源は同一 5 V から Pico の VSYS（1.8〜5.5 V 入力）を取れば概ね同時に上下するが、保証にはならない。74HCT/74AHCT（または 74LVC245 の 5 V 耐性入力）を挟むのが確実（推論）。
- 方向別の定石: 3.3 V→5 V（出力）は 74HCT244/74HCT245/74HCT574（VIH 2.0 V で 3.3 V 出力を受けられる）、5 V→3.3 V（入力）は 74LVC245（3.3 V 給電・5 V 耐性入力）または抵抗分圧。RP2350 なら入力は FT ピン直結も可。
- Linux Pi（BCM SoC）の GPIO は 3.3 V 専用・5 V 非耐性（一般常識。本調査では SoC データシートでの再確認は未実施＝未確認）。

### Gaps
- A2 ステッピングの 5 V 耐性: 公式に明言なし（Eben Upton の発言とされる二次情報のみ）、未確認。
- Akizuki で入手できる Pico 2 の現行ステッピング: 対象外（部品担当）だが設計上重要。

---

## 6. 「1 つのソケットに Raspberry Pi または CPU/PPU」案の実現性

### Takeaway
文字通りの「共用ソケット」は成立しにくい。DIP-40 は 0.6 in 列間隔、Pico/Pico 2 は 40 ピン 2.54 mm ピッチで基板幅 21 mm（列間隔は 0.7 in と広く言われるが本調査では図面値未確認）、Pi は 2×20 ヘッダで、ピン配置も信号も全く異なる。さらに Mode B は CPU と PPU の 2 個（計 80 ピン相当）を 1 枚で置き換える必要がある。現実的なのは「CPU/PPU 用 DIP-40×2 と、Pico 2 用ピンヘッダを別フットプリントで並べ、DIP スイッチ／ジャンパでバスを切り替える」構成。

### Cited Findings
- Pico 2: 51×21 mm、40 本のメインピンは 2.54 mm グリッド、1 mm 穴、DIP 形式・表面実装（キャスタレーション）両用 — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- 6502 ソケット置換の実例 pico6502（RP2350B、DIP-40 フットプリント内、現行 v2.3b は 20 ピン丸ピンヘッダ 2 本で装着、74AHCT244/245 バッファ、6 層基板） — https://eaw.app/pico6502/
- 2A03 は 1/12 分周で約 12 MHz 供給が必要、NMOS のため低速クロック不可 — https://emulationonline.neocities.org/systems/chiplab/experimenting-with-highspeed-chips/
- RP2040 を 2A03 ソケットに挿す公開プロジェクトは検索で見つからず — （検索結果のみ、該当なし）

### Inferences
- 2A03 ソケットには CPU バスに加え APU 音声出力（AUD1/AUD2）、コントローラ用 OUT0–2・/OE1・/OE2、21.477 MHz 入力などが載る（NESdev 既知仕様、本調査では未再確認）。PPU ソケットには PPU バス（AD0–7 多重化＋A8–13、ALE）とビデオ出力。これらを 1 個の RP2350B（48 GPIO）で同時に置き換えるのはピン数的に不可能に近い。
- 一方、Mode B では「CPU/PPU を置き換える」必要はなく、エミュレータが映像・音声・入力・カートアクセスを全部自前で行えば、CPU/PPU ソケット周辺の 5 V 回路は使わない。メイン基板上に Pico 2 フットプリント（またはソケット）とカート用ラッチ/バッファを用意し、DIP スイッチで「映像・音声の出所（実 PPU/APU か Pico か）」を切替えるだけで済む（推論）。
- pico6502 の例から、RP2350B を DIP-40 内に収めるには 6 層・カスタム基板が必要で、Akizuki で買える既製 Pico/Pico 2 では実現できない（推論）。

### Gaps
- Pico/Pico 2 の列間隔の公式寸法（17.78 mm と広く言われる）: 本調査ではデータシート本文テキストで確認できず未確認。
- 2A03/2C02 のソケット互換マイコン/FPGA 置換の実例: 見つからず。

---

## 7. USB によるファームウェア更新

### Takeaway
Pico/Pico 2 は ROM 内蔵の USB ブートローダ（BOOTSEL・UF2 ドラッグ＆ドロップ）が書き換え不能で最も堅牢。キャビネットを開けずに更新するには、(1) 筐体外に BOOTSEL ボタン（または RUN＋BOOTSEL）を引き出す、(2) 1200 baud タッチ、(3) `picotool reboot -u`、を併用できる。RP2350 は A/B パーティションと TBYB（Try Before You Buy）で電源断に強い更新が可能。Linux Pi は SD カード交換か USB メモリ経由のスクリプト更新が中心で、電源断耐性は Pico より劣る。

### Cited Findings
- Pico 2: BOOTSEL を押したまま電源投入→USB マスストレージとして見え、.uf2 をドラッグすると書き込み→再起動。"The USB boot code is stored in ROM on RP2350, so can not be accidentally overwritten." — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- RP2350 ブートロム: パーティションテーブル、"A/B versions to support double-buffered upgrades"、"Try before you buy support for phased upgrades with image self-test"、UF2 family ID（rp2040, rp2350-arm-s, rp2350-arm-ns, rp2350-riscv, data, absolute）でパーティション振り分け。TBYB では新イメージが自己テスト後にコールバックしない限り旧イメージに戻る — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf（Section 5.1, 5.1.17）
- pico-sdk の stdio_usb: `PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE`（ホストが 1200 baud に設定すると BOOTSEL へリセット、既定値 1200）、`PICO_STDIO_USB_ENABLE_RESET_VIA_VENDOR_INTERFACE`（picotool 用リセットインターフェース） — https://sourcevu.sysprogs.com/rp2040/picosdk/macros/PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE ／ https://sourcevu.sysprogs.com/rp2040/picosdk/files/src/rp2_common/pico_stdio_usb/reset_interface.c
- picotool: `picotool reboot [-a] [-u] [-g <partition>] [-c <cpu>]`、`-u` で BOOTSEL へ再起動、`-f` で強制 — https://dyn.manpages.debian.org/unstable/picotool/picotool-reboot.1 ／ https://github.com/raspberrypi/picotool/issues/88
- pico-infones の ROM 書き込みも picotool（`picotool load … -o 0x10080000`） — https://github.com/shuichitakano/pico-infones
- pico6502 は初回 USB マスストレージ、以後 OTA で 5 MB×2 パーティションを切替 — https://eaw.app/pico6502/

### Inferences
- 推奨: Pico 2 の USB コネクタをキャビネット内からアクセスしやすい位置に（あるいは基板端に USB-C/Micro-B 中継）出し、BOOTSEL を JAMMA の「テスト/サービス」ボタンとの同時押し（起動時に監視してソフトから `rom_reset_usb_boot` 相当で BOOTSEL へ）にすれば、ボタン追加なしで更新できる（推論。ソフトから BOOTSEL 再起動する ROM 関数の存在は SDK 機能として一般的だが、本調査では API 名を一次資料で再確認していない＝未確認）。
- 電源断対策: ファームはブートロム＋A/B＋TBYB で保護。SRAM セーブを内蔵フラッシュに書く場合は 2 セクタ交互書き＋CRC で電源断に耐える方式にする（推論）。
- Linux Pi の更新（USB メモリ挿入で自動適用など）は自作スクリプト依存で、読み取り専用 root と組み合わせると手順が複雑（推論）。

### Gaps
- Pi Zero 2 W の USB デバイスブート（rpiboot）での書き換え可否: 未確認。
- RP2040（初代 Pico）は A/B パーティション機能を持たない点のデータシート上の明示確認: 未確認（RP2350 側の新機能として記載されていることのみ確認）。

---

### 全体の総合所見（推論、§1〜§7 をまとめたもの）
- 第一候補: **Raspberry Pi Pico 2（RP2350A、A4 ステッピング推奨）＋外付け 74HC595/74HC574 等でカートをダンプ＋pico-infonesPlus 系エミュレータを 15 kHz PIO RGB 出力に改造**。GPIO は約 23 本（5 V 耐性）で、映像（RGB 9〜12 本＋CSync 1）、音声 PWM 1〜2、JAMMA 入力シフトレジスタ 3、カート用（データ 8＋制御 6〜8＋ラッチ制御 3〜4）を割り当てるとぎりぎりなので、ピン配分の詳細検討が必要。
- RP2350B 搭載ボード（48 GPIO）なら余裕が出るが、Akizuki 在庫・JLC Basic 可否は部品担当の確認事項。
- Linux Pi は「ROM ファイルを遊ぶ」なら最も簡単だが、本プロジェクトの「実カートを差す」「電源断」「部品点数最小」という条件では不利。
