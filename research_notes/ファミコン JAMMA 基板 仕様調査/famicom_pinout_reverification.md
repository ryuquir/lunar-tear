# ファミコン (HVC-001) ピン配置・回路 再検証ノート (第2パス)

調査日: 2026-11-10。対象: `famicom_hardware.md` (第1パス) の全表。
方針: 各行を「逐語テキスト」または「ネットリスト / データシート」で確認できるまで疑わしいものとして扱った。自分の推論は **推論**、確認できなかったものは **未確認** と明記する。

## 使用ソース (略号)

| 略号 | 内容 | URL / 入手方法 |
|---|---|---|
| NW-M | NESdev Wiki の静的ミラー (HTML 本文を curl で逐語取得、要約モデルを通さない)。スナップショット日付は不明 | https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml / PPU_pinout.xhtml / Cartridge_connector.xhtml / Expansion_port.xhtml / Standard_controller.xhtml / Controller_reading.xhtml / Open_bus_behavior.xhtml / CPU_variants.xhtml / Cycle_reference_chart.xhtml / PPU_frame_timing.xhtml / PPU_rendering.xhtml / NTSC_video.xhtml / Famicom_cartridge_dimensions.xhtml |
| NW-L | NESdev Wiki 現行版。WebFetch で**短い逐語引用**を要求し、NW-M と同一であることを確認 (全文逐語は WebFetch が拒否) | https://www.nesdev.org/wiki/CPU_pinout (最終編集 2026-10-03)、https://www.nesdev.org/wiki/Cartridge_connector (2026-08-31)、https://www.nesdev.org/wiki/PPU_pinout (2024-05-24)、https://www.nesdev.org/wiki/Expansion_port (2025-11-03) |
| EN | nocash「Everynes」NES ハードウェア仕様 (第1パスで未使用の独立資料。ローカル保存テキストを参照) | https://problemkaputt.de/everynes.htm |
| OFC | OpenFC HVC-CPU-07 Rev A の **kicad_pcb のパッド→ネット** を自作スクリプトで抽出 (第1パスとは別コードで再抽出) | https://github.com/starlightk7/OpenFC (commit 42cb3a5, `Motherboards/HVC-CPU-07/Rev A/HVC-CPU-07.kicad_pcb`) |
| TX-G | TrexMakes「Nintendo_Famicom_Console」の **HVC-CPU-GPM-02** kicad_pcb (作者 README で「electrically correct と検証済み」)。第1パス未使用の独立ネットリスト | https://codeberg.org/TrexMakes/Nintendo_Famicom_Console (`HVC-CPU-GPM-02/HVC-CPU-GPM-02.kicad_pcb`) |
| TX-7 | 同リポジトリの HVC-CPU-07 kicad_pcb (README の進捗表では未完成扱い → 参考扱い) | 同上 (`HVC-CPU-07/HVC-CPU-07.kicad_pcb`) |
| TX-C | 同リポジトリのコントローラ I / II kicad_pcb | 同上 (`CONTROLLER1/`, `CONTROLLER2/`) |
| OFC-C | OpenFC コントローラ 56.8231B Rev B / 56.8232A Rev A kicad_pcb | https://github.com/starlightk7/OpenFC (`Controllers/`) |
| OT | OpenTendo (NES-CPU 再現) Motherboard.kicad_pcb — 2A03/2C02/139 の独立確認用 | https://github.com/Redherring32/OpenTendo (commit 3bd0b0b, `Board Files/Motherboard.kicad_pcb`) |
| C05 | HVC-CPU-05 トレース回路図 Rev.07 (BABAX)。今回は PDF を 500 dpi でラスタ化して該当部を目視 | https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf |
| FCART | hi0t/fcart (ファミコン用カートリッジ基板 KiCad)。カード端子のパッド面・位置の確認用 | https://github.com/hi0t/fcart (commit 3f111fc, `board/fcart.kicad_pcb`) |
| PROVE | antarcticlion/FAMICOM_PROVE_CART (60 ピン端子フットプリント) | https://github.com/antarcticlion/FAMICOM_PROVE_CART (commit ab5cbf6) |
| TI-368 | TI SN74HC368 データシート (SCLS310F) | https://www.ti.com/lit/ds/symlink/sn74hc368.pdf |
| TI-139 / TI-LS139 | TI SN74HC139 (SCLS108E) / SN74LS139A (SDLS013A) | https://www.ti.com/lit/ds/symlink/sn74hc139.pdf / https://www.ti.com/lit/ds/symlink/sn74ls139a.pdf |
| TI-373 / TI-LS373 | TI SN74HC373 (SCLS140G) / SN74LS373 (SDLS165B) | https://www.ti.com/lit/ds/symlink/sn74hc373.pdf / https://www.ti.com/lit/ds/symlink/sn74ls373.pdf |
| TI-4021 | TI CD4021B (SCHS024C) | https://www.ti.com/lit/ds/symlink/cd4021b.pdf |

注: OFC / TX-G / TX-7 / OT のネットは KiCad の **PCB ファイルのパッドに付いたネット名**から取得した (回路図記号の解釈を挟まない)。

---

## 1. RP2A03 (CPU/APU) 全 40 ピン

### Takeaway
第1パスの RP2A03 表は **全 40 ピンとも正しい**。NESdev 逐語図 (NW-M / NW-L)、nocash EN、OFC・TX-G・TX-7 (ファミコン) と OT (NES) の 4 つの PCB ネットで全ピン一致。Pin 35 = /OE2 ($4017 読み出し)、Pin 36 = /OE1 ($4016 読み出し)、Pin 37/38/39 = OUT2/OUT1/OUT0、Pin 1 = AD1 (矩形波 2ch)、Pin 2 = AD2 (三角・ノイズ・DPCM)。唯一の補足は Pin 32 /IRQ の「内部プルアップ」がコンソール側 (RM1 10k) を指すことと、Pin 30 の E 版の挙動が NESdev 上でも「presumably」である点。

### Cited Findings
- NESdev 逐語図 (NW-M、NW-L で pin 01/02/21/29/30/31/35/36/37/39 行を逐語照合済み):
  ```
   AD1 <- |01  40| -- +5V
   AD2 <- |02  39| -> OUT0
  /RST -> |03  38| -> OUT1
   A00 <- |04  37| -> OUT2
   A01 <- |05  36| -> /OE1
   A02 <- |06  35| -> /OE2
   A03 <- |07  34| -> R/W
   A04 <- |08  33| <- /NMI
   A05 <- |09  32| <- /IRQ
   A06 <- |10  31| -> M2
   A07 <- |11  30| <- TST (usually GND)
   A08 <- |12  29| <- CLK
   A09 <- |13  28| <> D0
   ...
   A15 <- |19  22| <> D6
   GND -- |20  21| <> D7
  ```
  — [NW-M CPU pinout](https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml); [NW-L CPU pinout](https://www.nesdev.org/wiki/CPU_pinout)
- 「AD1 : Audio out pin (both pulse waves).」「AD2 : Audio out pin (triangle, noise, and DPCM).」 — [NW-M CPU pinout](https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml)
- 「/OE1 and /OE2 : Controller ports (for controller #1 and #2 respectively).」 — 同上。$4016/$4017 との対応は EN が明記: 「35 /JOY2 Out Low if A0-A15=4017h ...」「36 /JOY1 Out Low if A0-A15=4016h ...」 — [EN](https://problemkaputt.de/everynes.htm) (注: EN は条件を「R/W=0」と書いているが、読み出し時なので R/W=1 の誤記と判断 — **推論**)。NESdev Expansion port も「Joypad 1 /OE, Joypad 2 /OE: Output enables, asserted when reading from $4016 for joypad 1 and $4017 for joypad 2.」 — [NW-M Expansion port](https://nesdev-wiki.nes.science/wikipages/Expansion_port.xhtml)
- ネット: Pin 36 → 368 (U7) pin 1 [$4016 側]、Pin 35 → U8 pin 1 と pin 15 [$4017 側] (OFC: `OE1: U6.36 U7.1` / `OE2: U6.35 U8.1 U8.15`; TX-G: `/~{INP0}: U6.36 U7.1`, `/~{INP1}: U6.35 U8.1 U8.15`; TX-7 同一)。U7 出力 → $4016 のパッド I データ、U8 出力 → $4017 のパッド II データであることも同ネットで確認 (§4)。NES 版 OT でも `/~{OE1}`=U6.36→U7(CI)、`/~{OE2}`=U6.35→U8(CII)。
- 「OUT0..OUT2 : Output pins used by the controllers ($4016 output latch bits 0-2). ... OUT0 is additionally used as the "strobe" signal」 — [NW-M CPU pinout](https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml)。EN: 「37-39 J2-0 Out Bit2-0 of internal register 4016h (Bit0 = Joystick strobe)」。ネット: U6.39 = OUT0 = コントローラ I/II の P/S と拡張端子 12 (OFC/TX-G/TX-7)。
- 「CLK : 21.47727 MHz (NTSC) ... Internally, this clock is divided by 12 (NTSC 2A03)」 — [NW-M CPU pinout](https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml)。EN: 「29 CLK In Master clock input (236,250/11 MHz), clocks an internal divide-by-12 counter.」
- 「TST : (tentative name) Pin 30 ... normally it is grounded ... if it is pulled high on the RP2A03G, extra diagnostic registers ... $4018 through $401A, and the joystick ports $4016 and $4017 become open bus. On the RP2A07 (and presumably also the RP2A03E), pulling pin 30 high instead causes the CPU to stop execution by means of activating the embedded 6502's RDY input.」 — 同上。CPU variants: 2A03E「Pin 30 is /RDY」、無印 2A03「Pin 30 connects to nothing」 — [NW-M CPU variants](https://nesdev-wiki.nes.science/wikipages/CPU_variants.xhtml)。全ネットで U6.30 = GND (OFC/TX-G/TX-7/OT)。EN は pin 30 を「?」(用途不明) としており、ここは EN が古い。
- 「M2 ... CPU cycles begin at the point where M2 goes low. In the NTSC 2A03E, G, and H, M2 has a duty cycle of 15/24 (5/8), or 350ns/559ns. ... In the original NTSC 2A03 (no letter), M2 has a duty cycle of 17/24, or 396ns/559ns」 — [NW-M CPU pinout](https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml)。(EN は「62.5% duty cycle」= 15/24 と一致)
- 「Axx holds the target address during the entire read/write cycle. For reads, the value is read from Dx during φ2. For writes, the value appears on Dx during φ2 (and no sooner).」 — 同上
- 「/RST : When low, holds CPU in reset state, during which all CPU pins (except pin 2) are in high impedance state. When released, CPU starts executing code (read $FFFC, read $FFFD, ...) after 6 M2 clocks.」 — 同上
- アドレス/データのビット順: 全 4 ネットで U6.4 = A0 … U6.19 = A15、U6.21 = D7 … U6.28 = D0。さらに PPU 側・SRAM 側・カートリッジ側の同名ネットに接続されていることを確認 (例 OFC: `Net-(P1-C.A3): P1.10 U1.5 U6.7`)。

#### 行ごとの判定 (第1パス §1 表)

| Pin | 第1パスの記載 | 判定 | 根拠 |
|---|---|---|---|
| 1 | AD1 出力・Pulse1+2 | 確認 | NW-M/NW-L 逐語、EN「ROUT ... channel 1+2」、OFC/TX-G/TX-7/OT ネット (R 100Ω + 20k へ) |
| 2 | AD2 出力・三角+ノイズ+DPCM | 確認 | 同上 (EN「COUT ... channel 3+4+5」、ネットは 100Ω + 12k へ) |
| 3 | /RST 入力、Pin 2 以外 Hi-Z、6 M2 後にベクタ | 確認 | NW-M 逐語、4 ネット (C1 + SW1 へ) |
| 4-19 | A0-A15 (4=A0 … 19=A15) | 確認 | NW-M/NW-L、EN、4 ネット |
| 20 | GND | 確認 | 同上 |
| 21-28 | D7-D0 (21=D7 … 28=D0) | 確認 | 同上 |
| 29 | CLK 入力 21.47727 MHz、÷12 | 確認 | NW-M/NW-L、EN、ネット (OFC `CLK: C9 R13 U6.29`) |
| 30 | TST、通常 GND | 確認 (補足あり) | NW-M 逐語。「2A03E で High → 停止」は NESdev 上も「presumably」(推定) |
| 31 | M2 出力、デューティ E/G/H = 15/24、無印 = 17/24 | 確認 | NW-M/NW-L 逐語、EN 62.5% |
| 32 | /IRQ 入力「内部プルアップあり」 | 一部要訂正 | 入力であることは確認。NESdev の「internal pull-up resistor in the NES/Famicom」は本体基板上の RM1 10k を指す (Expansion port 頁「the internal 10kΩ pull-up」)。2A03 チップ内蔵プルアップの有無は **未確認** |
| 33 | /NMI 入力 (PPU /INT から) | 確認 | NW-M、全ネット (U5.19 = U6.33 + RM1 10k) |
| 34 | R/W 出力 | 確認 | NW-M、全ネット |
| 35 | /OE2 ($4017) | 確認 | NW-M、EN、4 ネット |
| 36 | /OE1 ($4016) | 確認 | 同上 |
| 37 | OUT2 | 確認 | NW-M/NW-L、EN、ネット (拡張端子 10) |
| 38 | OUT1 | 確認 | 同上 (拡張端子 11) |
| 39 | OUT0 (ストローブ) | 確認 | 同上 (拡張端子 12・両パッド P/S) |
| 40 | VCC +5V | 確認 | 同上 |

### Inferences
- 推論: 2A03 /RST には 3 つのファミコン基板ネット (OFC/TX-7/TX-G) のいずれにも外付けプルアップが無く、C (0.47 µF) とスイッチのみ。したがってチップ内部に /RST プルアップがあると考えるのが自然だが、一次資料での明記は見つからなかった。新基板では外付け 10k〜47k プルアップを追加しても害はない (推論)。

### Gaps
- 2A03 内部プルアップ (/RST, /IRQ, /NMI) の有無と値: **未確認**。

---

## 2. RP2C02 (PPU) 全 40 ピン

### Takeaway
第1パスの RP2C02 表は **全 40 ピン正しい**。CPU データは Pin 2 = D0 … Pin 9 = D7、Pin 10/11/12 = CPU A2/A1/A0、Pin 13 = /CS、14-17 = EXT0-3、18 = CLK、19 = /INT、21 = VOUT、22 = /RST、23 = /WR、24 = /RD、25-30 = PA13…PA8、31-38 = AD7…AD0、39 = ALE。ファミコンでは Pin 22 (/RST) は +5V 直結、Pin 14-17 は GND (3 ネット一致)。

### Cited Findings
- NESdev 逐語図 (NW-M、NW-L で pin 02/09/10/12/13/14/17/19/22/25/31 の行を逐語照合):
  ```
     R/W -> |01  40| -- +5V
  CPU D0 <> |02  39| -> ALE
  CPU D1 <> |03  38| <> PPU AD0
  ...
  CPU D7 <> |09  32| <> PPU AD6
  CPU A2 -> |10  31| <> PPU AD7
  CPU A1 -> |11  30| -> PPU A8
  CPU A0 -> |12  29| -> PPU A9
     /CS -> |13  28| -> PPU A10
    EXT0 <> |14  27| -> PPU A11
    EXT1 <> |15  26| -> PPU A12
    EXT2 <> |16  25| -> PPU A13
    EXT3 <> |17  24| -> /RD
     CLK -> |18  23| -> /WR
    /INT <+ |19  22| <- /RST
     GND -- |20  21| -> VOUT
  ```
  — [NW-M PPU pinout](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml); [NW-L PPU pinout](https://www.nesdev.org/wiki/PPU_pinout)
- EN の 2C02 表: 「2-9 I/O CPU D0-D7」「10-12 In CPU A2-A0」「13 In CPU /CS」「14-17 I/O EXT0-EXT3」「18 In CLK」「19 Out /VBL NMI」「21 Out VOUT」「22 In /SYNC EXT」「23,24 Out PPU /W,/R」「25-30 Out PPU A13-A8」「31-38 I/O PPU AD7-AD0」「39 Out PPU ALE」 — [EN](https://problemkaputt.de/everynes.htm)。Pin 22 の名称のみ EN (/SYNC EXT) と NESdev (/RST) が異なる。EN 自身も「On Famicom consoles, /SYNC EXT is always tied to logical one. On the NES ... tied in with the 2A03's reset input」と書いており配線事実は同じ。機能説明は NESdev の方が新しく詳細 (下記)。
- 「/RST resets certain parts of the chip to their initial power-on state: the clock divider, video phase generator, scanline/pixel counters, and the even/odd frame toggle. It also keeps several registers zeroed out for a full frame: PPUCTRL, PPUMASK ($2001), PPUSCROLL ($2005; the VRAM address latch "T", fine X scroll, and the H/V toggle), and the VRAM read buffer.」「Famicom ties this signal directly to the +5V rail, which is why the screen does not clear as you hold down the reset button.」 — [NW-M PPU pinout](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml) (後者は NW-L でも逐語確認)
- 「/INT is an open-drain output, connected to the CPU's /NMI pin as well as a pull-up resistor.」「ALE ... goes high at the beginning of a PPU VRAM access ... It stays high for one PPU cycle.」「As an exception, writing to the internal palette range (3F00-3FFF) will not assert /WR.」「CLK ... divided by 4 (NTSC) ... for the pixel and memory clocks.」「No official console uses the output mode, so these are normally grounded」 — 同上
- ネット (U5): OFC / TX-G / TX-7 で全 40 ピン一致: 1 R/W、2-9 CPU D0-D7 (CPU U6.28…U6.21 と同ネット)、10/11/12 = A2/A1/A0、13 = 74139 pin 5 出力、14-17 GND、18 PPU CLK、19 /NMI (RM1 10k プルアップ)、20 GND、21 → 2SA937 ベース、**22 = +5V**、23 = /WR (カート 47 / VRAM /WE)、24 = /RD (カート 17 / VRAM /OE)、25 = PA13 (カート 56 / 368 入力)、26-30 = PA12…PA8、31-38 = PD7…PD0、39 = ALE (373 pin 11)、40 = +5V。NES 版 OT も 22 以外同一 (OT は Pin 22 = /RST)。

#### 行ごとの判定 (第1パス §2 表)

| Pin | 第1パスの記載 | 判定 | 根拠 |
|---|---|---|---|
| 1 | R/W 入力 | 確認 | NW-M、EN、3+1 ネット |
| 2-9 | CPU D0-D7 (2=D0 … 9=D7) | 確認 | NW-M/NW-L 逐語、EN、ネット (U5.2 = U6.28 = D0 等) |
| 10 | CPU A2 | 確認 | 同上 |
| 11 | CPU A1 | 確認 | 同上 |
| 12 | CPU A0 | 確認 | 同上 |
| 13 | /CS (74139、$2000-$3FFF、/DBE) | 確認 | NW-M 逐語「sometimes referred to as /DBE」、ネット U3.5 = U5.13 |
| 14-17 | EXT0-3、公式機は GND | 確認 | NW-M 逐語、3 ネットで GND |
| 18 | CLK 21.47727 MHz、÷4 | 確認 | NW-M、EN |
| 19 | /INT オープンドレイン → CPU /NMI + プルアップ | 確認 | NW-M 逐語、ネット (RM1.8 または RM1.7 10k) |
| 20 | GND | 確認 | 全ソース |
| 21 | VOUT | 確認 | 全ソース、ネット → 2SA937 ベース |
| 22 | /RST (クロック分周器・映像位相・走査カウンタ・偶奇フレームをリセット、PPUCTRL/PPUMASK/PPUSCROLL/読みバッファを 1 フレーム 0 保持)、ファミコンは +5V 直結 | 確認 | NW-M/NW-L 逐語、3 ネットで +5V |
| 23 | /WR (パレット書込時は出ない) | 確認 | NW-M 逐語、ネット |
| 24 | /RD | 確認 | 同上 |
| 25-30 | PA13…PA8 | 確認 | NW-M/NW-L、EN、ネット |
| 31-38 | AD7…AD0 (31=AD7 … 38=AD0) | 確認 | 同上 |
| 39 | ALE (1 PPU サイクル High) | 確認 | NW-M 逐語、ネット |
| 40 | VCC | 確認 | 全ソース |

### Inferences
- 推論: PPU /RST を CPU リセットと共通にすると NES 方式になり、リセット中は画面消去・レジスタ 1 フレーム 0 保持となる。ファミコン実機互換を優先するなら +5V 固定 (3 ネット一致)。

### Gaps
- なし (ピン配置について)。

---

## 3. 60 ピン ファミコン カートリッジコネクタ

### Takeaway
第1パスの 60 ピン割付と方向は **全ピン正しい**。NESdev 逐語図 (NW-M、NW-L で要所を逐語照合)、EN、OFC・TX-G・TX-7 の 3 本体ネットで全 60 ピン一致。音声は **pin 45 = 本体→カート (増幅済み 2A03 音声)、pin 46 = カート→本体 (RF/出力へ)**。番号付けは: **本体を正面 (プレイヤー側) から見て、スロットの手前側の列が pin 1-30 で左端が pin 1、奥側の列が pin 31-60 で左端が pin 31 (pin 1 の真後ろ)**。カートリッジ側では **ラベル面 = pin 1-30**、ラベル面を見て端子を下にすると左端が pin 1。第1パスの「NESdev 図の矢印に一部不整合」という記述は誤りで、矢印は一貫している。

### Cited Findings
- 「This diagram represents a top-down view looking directly into the connector. Pins 01–30 are on the label side of the cartridge, left to right.」「The pitch, or pin spacing, of this connector is 2.54mm.」 — [NW-M Cartridge connector](https://nesdev-wiki.nes.science/wikipages/Cartridge_connector.xhtml); 前者 2 文は [NW-L](https://www.nesdev.org/wiki/Cartridge_connector) でも逐語確認
- 逐語図 (NW-M、NW-L で pin 01/15/18/30/31/44/45/46/48/49 行を逐語照合):
  ```
    (front)                 (back)
    Famicom    | Cart  |    Famicom
                -------
        GND -- |01   31| -> CartridgePresent or 5V supply, depending
    CPU A11 -> |02   32| <- M2
    ...
    CPU R/W -> |14   44| <- /ROMSEL (/A15 + /M2)
       /IRQ <- |15   45| <- Audio from 2A03
        GND -- |16   46| -> Audio to RF
    PPU /RD -> |17   47| <- PPU /WR
  CIRAM A10 <- |18   48| -> CIRAM /CE
     PPU A6 -> |19   49| <- PPU /A13
    ...
        +5V -- |30   60| <> PPU D4
  ```
  矢印の読み方: 左列は「Famicom (左) → Cart (中央)」が `->`、右列は「Famicom (右) → Cart (中央)」が `<-`。この規則で全 60 ピンを確認すると、本体→カート = CPU A0-A14, R/W, M2, /ROMSEL, PPU /RD, /WR, PPU A0-A13, PPU /A13, **pin 45**; カート→本体 = /IRQ, CIRAM A10, CIRAM /CE, **pin 46**, pin 31 (CartridgePresent); 双方向 = CPU D0-D7, PPU D0-D7。不整合は無い。
- 「Unless otherwise specified, these signals are from the console's viewpoint.」「Audio from 2A03 : Audio output from the 2A03's sound generation hardware, already amplified.」「Audio to RF : Usually just tied to the audio from 2A03. This one goes directly to the sound output of the console.」「/ROMSEL: This pin outputs the logical NAND of M2 and CPU A15.」 — [NW-M Cartridge connector](https://nesdev-wiki.nes.science/wikipages/Cartridge_connector.xhtml)
- 「pin 31: On certain revisions of the RF modulator board, pin 31 connects only to the TV/Game switch ... On other RF modulator board revisions, pin 31 is connected to the normal 5V supply.」 — 同上。ネット: OFC pin 31 = `VCC2` (C24 470µF + 電源コネクタ P3.4)、TX-7 = `+5VA`、TX-G (GPM-02) = `+5V` (pin 30 と同一ネット)。
- EN の 60 ピン表: 「1 GND / 2-13 CPU A11-A0 / 14 CPU R/W / 15 CPU /IRQ / 16 GND / 17 PPU /RD / 18 PPU NT A10 / 19-25 PPU A6-A0 / 26-29 PPU D0-D3 / 30-31 +5VDC / 32 PHI2 CLK / 33,35 CPU A12-A14 / 36-43 CPU D7-D0 / 44 CPU /PRG / 45 EXP SND_IN / 45,46 EXP SND_OUT / 47 PPU /WR / 48 PPU NT /CS / 49 PPU NT /A13 / 49-56 PPU A7-A12,A13 / 57-60 PPU D7-D4」「The Famicom connector uses standard 2.54mm pitch.」 — [EN](https://problemkaputt.de/everynes.htm)。EN の表には誤植 (「33,35」は 33-35、「45,46 EXP SND_OUT」、「49-56 PPU A7-…」は 50-56) があるが、割付自体は NESdev と矛盾しない。
- ネット (全 60 ピン、OFC / TX-7 / TX-G 一致): 1 GND、2-13 = CPU A11…A0、14 R/W、15 /IRQ (RM1 10k)、16 GND、17 PPU /RD、18 VRAM A10 (VRAM pin 19)、19-25 = PA6…PA0 (373 出力)、26-29 = PD0-PD3、30 +5V、31 (上記)、32 M2、33-35 = CPU A12-A14、36-43 = CPU D7…D0、44 = 74139 pin 9 (/ROMSEL)、45 = 368 音声アンプ出力 (OFC `A.IN: U7.13 P1.45 P2.2`)、46 → 電源/RF 基板 (OFC `P1.46 P3.5`)、47 PPU /WR、48 VRAM /CS (VRAM pin 18)、49 = 368 pin 11 (/PA13)、50-56 = PA7…PA13 (56 = PPU pin 25)、57-60 = PD7, PD6, PD5, PD4。
- 物理配置 (番号付け規約) の独立確認:
  - OFC の kicad_pcb (部品面 F.Cu の上面図): スロット P1 の pin 1-30 列はパッド y = +2.36 mm、pin 31-60 列は y = −2.75 mm (KiCad は y 下向き正)。拡張端子 P2 (y≈194) とコントローラコネクタ P4/P5 (y≈197)・リセット SW1 (x≈148, y≈182) は図の下側にあり、拡張端子は本体正面にあるので **図の下 = 本体正面**。よって pin 1-30 列が正面側。pin 1 は x = −35.6 (左)、pin 30 は x = +38.0 (右)。基板シルクの「1」(x 69.1, y 96.4) と「31」(x 68.8, y 83.9)、「30」「60」も同じ関係 — [OFC](https://github.com/starlightk7/OpenFC)
  - TX-G / TX-7 も同じ (pin 1 = (−36.83, +2.54)、pin 31 = (−36.83, −2.54)、拡張端子・コントローラが y≈160-171 で下側) — [TX-G](https://codeberg.org/TrexMakes/Nintendo_Famicom_Console)
  - カートリッジ側: FCART のカード端子フットプリントは pin 1-30 が F.Cu、pin 31-60 が B.Cu、pin 1 と pin 31 が同一座標 (−37.33, +6.35)、pin 30 が (+37.33)、端子はフットプリント原点より下 → 「一方の面を端子を下にして見ると左から 1…30、裏面の pin 31 は pin 1 の真裏」 — [FCART](https://github.com/hi0t/fcart)。PROVE の BUS_FC_60 フットプリントも pin 1 と 31 が同一座標 (−36.83, 3.23) — [PROVE](https://github.com/antarcticlion/FAMICOM_PROVE_CART)
- 「For the Famicom: most chips and components appear on the opposite side of the PCB from the label in Famicom cartridges.」 — [NW-M Cartridge connector](https://nesdev-wiki.nes.science/wikipages/Cartridge_connector.xhtml)
- カード寸法: 「C | 1.2 | Board thickness」「E.6 | 2.54 | Pad spacing」「B.3 | 10.7 | Card edge depth」「D.3 | 6.7 | Power pad height」「D.4 | 5.7 | Signal pad height」(HVC-TGROM-01 実測、±0.05 mm) — [NW-M Famicom cartridge dimensions](https://nesdev-wiki.nes.science/wikipages/Famicom_cartridge_dimensions.xhtml) (第1パスはスニペット経由だったが今回本文を逐語確認)

#### 行ごとの判定 (第1パス §3.15 / §6)

| Pin | 第1パスの記載 | 判定 | 根拠 |
|---|---|---|---|
| 1 | GND | 確認 | NW-M/NW-L、EN、3 ネット |
| 2-13 | CPU A11…A0 | 確認 | 同上 |
| 14 | R/W | 確認 | 同上 |
| 15 | /IRQ (カート→本体) | 確認 | 同上 |
| 16 | GND | 確認 | 同上 |
| 17 | PPU /RD | 確認 | 同上 |
| 18 | CIRAM A10 (カート→本体) | 確認 | 同上 |
| 19-25 | PPU A6…A0 | 確認 | 同上 |
| 26-29 | PPU D0-D3 | 確認 | 同上 |
| 30 | +5V | 確認 | 同上 |
| 31 | +5V / カートリッジ検出 (RF 基板版による) | 確認 | NW-M 逐語、ネットで版差 (OFC VCC2, TX-G +5V) |
| 32 | M2 | 確認 | 全ソース |
| 33-35 | CPU A12-A14 | 確認 | 同上 |
| 36-43 | CPU D7…D0 | 確認 | 同上 |
| 44 | /ROMSEL (NAND(M2, A15)) | 確認 | 同上 (139 pin 9) |
| 45 | 本体→カート、2A03 増幅済み音声 | 確認 | NW-M/NW-L 矢印 `<-` (右列) + 説明文、EN「SND_IN」(カート視点の入力)、ネット (368 出力) |
| 46 | カート→本体、RF/出力へ | 確認 | NW-M/NW-L 矢印 `->`、ネット (RF 基板へ) |
| 47 | PPU /WR | 確認 | 全ソース |
| 48 | CIRAM /CE (カート→本体) | 確認 | 同上 |
| 49 | PPU /A13 | 確認 | 同上 |
| 50 | PPU A7 | 確認 | 同上 |
| 51-56 | PPU A8-A13 | 確認 | 同上 |
| 57-60 | PPU D7, D6, D5, D4 | 確認 | 同上 |
| 規約 | 「pin 1-30 がラベル側 (正面)、31-60 が裏側」 | 確認 (端の向きを追記) | NW-M 逐語 + OFC/TX-G 配置 + FCART/PROVE |
| 注記 | 「NESdev 図の矢印は一部不整合」 | **誤り** | 逐語図では全ピン一貫 (上記) |

### Inferences
- 推論: 新基板で汎用 2.54 mm 2×30 カードエッジソケットを使う場合、ソケットのメーカー番号 (A1/B1 など) と上記ファミコン番号の対応は製品ごとに異なるため、フットプリントは「正面側列・左端 = 1」の規約で独自に番号付けし直すこと。

### Gaps
- ファミコン実機の 60 ピンコネクタ部品のメーカー型番: **未確認** (本調査範囲外)。

---

## 4. ロジック IC 配線 (74LS139 / 74LS373 / 74HC368・40H368 ×2)

### Takeaway
第1パスの 139・373・368 配線は HVC-CPU-05/07 については **正しい**。ただし **368 のどのゲートに何を割り当てるかは基板版で異なる** (GPM-02 では M2 クロックが U7 の 1 番ゲート、05/07 では 3 番ゲート) ので「この割付が唯一」ではない。機能 (U7 = /OE1 で $4016 の D0/D1/D2 とパッド I/拡張クロック、2OE 側の 2 ゲートを常時有効にして /PA13 と音声アンプ; U8 = /OE2 を両 OE に入れて $4017 の D0-D4 とパッド II クロック) は 3 ネットで共通。各 IC 自身のピン番号は TI データシートで確認。

### Cited Findings
#### 4.1 74139 (データシート)
- SN74HC139 / SN74LS139A ピン配置: 1 = 1G、2 = 1A、3 = 1B、4 = 1Y0、5 = 1Y1、6 = 1Y2、7 = 1Y3、8 = GND、9 = 2Y3、10 = 2Y2、11 = 2Y1、12 = 2Y0、13 = 2B、14 = 2A、15 = 2G、16 = VCC — [TI-139](https://www.ti.com/lit/ds/symlink/sn74hc139.pdf) p.3; [TI-LS139](https://www.ti.com/lit/ds/symlink/sn74ls139a.pdf) p.1 (同一)
- 真理値表: G=L のとき B=L,A=L → Y0=L; B=L,A=H → Y1=L; B=H,A=L → Y2=L; B=H,A=H → Y3=L; G=H → 全 H — 同上
#### 4.2 74139 の接続 (OFC / TX-G / TX-7 / OT すべて同一)
| 139 pin | 名称 | 接続 | 論理 |
|---|---|---|---|
| 15 | 2G | GND | 後段常時有効 |
| 14 | 2A | M2 (CPU 31) | |
| 13 | 2B | CPU A15 | |
| 9 | 2Y3 | **/ROMSEL** → カート 44 | M2=1 かつ A15=1 で L ($8000-$FFFF) |
| 11 | 2Y1 | → pin 1 (1G) | M2=1 かつ A15=0 で前段有効 |
| 10, 12 | 2Y2, 2Y0 | 未接続 | |
| 1 | 1G | ← pin 11 | |
| 2 | 1A | CPU A13 | |
| 3 | 1B | CPU A14 | |
| 4 | 1Y0 | **WRAM /CS** (A14=0, A13=0: $0000-$1FFF) | |
| 5 | 1Y1 | **PPU /CS** (pin 13) (A14=0, A13=1: $2000-$3FFF) | |
| 6, 7 | 1Y2, 1Y3 | 未接続 | |
| 8 / 16 | GND / VCC | | |
- 出典: ネット OFC (`1G: U3.1 U3.11`, `RSEL: P1.44 U3.9`, `{slash}CS: U3.5 U5.13 C21 C23`, `M2: U3.14`, `C.A15: U3.13`)、TX-G (`/$8000..FFFF_~{CS}: P1.44 U3.9`, `/$0000..1FFF_~{CS}: U1.18 U3.4`, `/$2000..3FFF_~{CS}: U3.5 U5.13`)、OT (`/~{ROMSEL}: U3.9`, `/WRAM-~{CE}: U3.4`, `/PPU-~{CE}: U3.5`, `Net-(U3A-E): U3.1 U3.11`, `/M2: U3.14`, `/CPU-A15: U3.13`)。C05 回路図とも一致 (第1パス)。
- PPU /CS 線の容量: 05/07 系 (OFC, TX-7) は C21 330 pF + C23 30 pF 対 GND。GPM-02 (TX-G) には無し。
- WRAM /CS 遅延回路: C05 回路図では 1Y0 → [D1 1S953 (アノード = SRAM /CS 側、カソード = 1Y0 側) ∥ R14 1.2k] → SRAM pin 18、SRAM 側に C20 68 pF 対 GND (今回 500 dpi 画像で目視確認) — [C05](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf)。**しかし HVC-CPU-07 の 2 つのネット (OFC と TX-7) では U3.4・D1 両端・R14 両端・U1.18・C20 が全て同一ネット** (TX-7 は D1 と並列にジャンパ JP1「CL1」がある)。つまり 07 では遅延回路がジャンパで短絡され、/CS は 139 から直結 (+ C20 68 pF) — [OFC](https://github.com/starlightk7/OpenFC); [TX-7](https://codeberg.org/TrexMakes/Nintendo_Famicom_Console)。GPM-02 (TX-G) は D1/R14/C20 自体が無く直結。
#### 4.3 74373 (データシート + 接続)
- SN74HC373 / SN74LS373 ピン配置: 1 = /OE、2 = 1Q、3 = 1D、4 = 2D、5 = 2Q、6 = 3Q、7 = 3D、8 = 4D、9 = 4Q、10 = GND、11 = LE (C)、12 = 5Q、13 = 5D、14 = 6D、15 = 6Q、16 = 7Q、17 = 7D、18 = 8D、19 = 8Q、20 = VCC。LE = H で透過、L でラッチ — [TI-373](https://www.ti.com/lit/ds/symlink/sn74hc373.pdf) Table 3-1 / Table 6-1; [TI-LS373](https://www.ti.com/lit/ds/symlink/sn74ls373.pdf) p.1
- 接続 (OFC / TX-G 同一): 1 = GND、11 = PPU ALE (pin 39)、D 入力 3/4/7/8/13/14/17/18 = PD7/PD6/PD5/PD4/PD3/PD2/PD1/PD0、Q 出力 2/5/6/9/12/15/16/19 = PA7/PA6/PA5/PA4/PA3/PA2/PA1/PA0。各 nD→nQ のビットは一致 (1D=PD7→1Q=PA7 … 8D=PD0→8Q=PA0)。
#### 4.4 74368 / 40H368 (データシート)
- SN74HC368 ピン配置: 1 = 1OE、2 = 1A1、3 = 1Y1、4 = 1A2、5 = 1Y2、6 = 1A3、7 = 1Y3、8 = GND、9 = 1Y4、10 = 1A4、11 = 2Y1、12 = 2A1、13 = 2Y2、14 = 2A2、15 = 2OE、16 = VCC — [TI-368](https://www.ti.com/lit/ds/symlink/sn74hc368.pdf) p.3
- 「organized as dual 4-line and 2-line buffers/drivers with active-low output-enable (1OE and 2OE) inputs. When OE is low, the device passes inverted data from the A inputs to the Y outputs. When OE is high, the outputs are in the high-impedance state.」 — 同上 p.1。真理値表 OE=H→Z、OE=L,A=H→L、A=L→H — 同 p.9
- → **1OE (pin 1) がゲート 1-4 (入力 2/4/6/10 → 出力 3/5/7/9)、2OE (pin 15) がゲート 5-6 (入力 12/14 → 出力 11/13)**。第1パスの「1-4 番ゲート = G1、5・6 番 = G2」は正しい。
- Toshiba TC40H368P のデータシートそのものは入手できず (**未確認**)。ただし TX-7 は U7/U8 を `TC40H368P`、TX-G は `74LS368`、OFC は `40H368` として同一ピンで配線しており、C05 回路図の G1 = pin 1 / G2 = pin 15 表記とも一致するので、40H368 は 74368 と同ピン配置と判断 (**推論**)。
#### 4.5 368 の接続 (基板版ごと)

U7 ($4016 側, 1OE = CPU /OE1 pin 36, 2OE = GND):

| 368 pin | 名称 | HVC-CPU-05 (C05) / HVC-CPU-07 (OFC, TX-7) | HVC-CPU-GPM-02 (TX-G) |
|---|---|---|---|
| 1 | 1OE | CPU pin 36 (/OE1) | CPU pin 36 (/OE1) |
| 2 → 3 | 1A1 → 1Y1 | パッド I データ (10k プルアップ) → CPU D0 | **M2 → $4016 クロック** (パッド I・拡張 14) |
| 4 → 5 | 1A2 → 1Y2 | 拡張端子 13 ($4016 D1) → CPU D1 | パッド I データ → CPU D0 |
| 6 → 7 | 1A3 → 1Y3 | **M2 → $4016 クロック** (パッド I・拡張 14、10k プルアップ) | 拡張端子 13 → CPU D1 |
| 10 → 9 | 1A4 → 1Y4 | マイク (R8 10k + C 0.1µF 経由) → CPU D2 | マイク (R8 10k + C 100nF) → CPU D2 |
| 15 | 2OE | GND (常時有効) | GND |
| 12 → 11 | 2A1 → 2Y1 | PPU PA13 (pin 25) → **/PA13** (カート 49) | 同左 |
| 14 → 13 | 2A2 → 2Y2 | 音声加算点 (C2 1µF 経由) → **音声出力** (カート 45)、帰還 R7 100k (13↔14) | 同左 (帰還 R7 **43k**) |

U8 ($4017 側, 1OE = 2OE = CPU /OE2 pin 35) — 05/07/GPM-02 で同一:

| 368 pin | 名称 | 接続 |
|---|---|---|
| 1, 15 | 1OE, 2OE | CPU pin 35 (/OE2) |
| 2 → 3 | 1A1 → 1Y1 | M2 → $4017 クロック (パッド II・拡張 9、10k プルアップ) |
| 4 → 5 | 1A2 → 1Y2 | 拡張 7 ($4017 D1) → CPU D1 |
| 6 → 7 | 1A3 → 1Y3 | 拡張 5 ($4017 D3) → CPU D3 |
| 10 → 9 | 1A4 → 1Y4 | 拡張 4 ($4017 D4) → CPU D4 |
| 12 → 11 | 2A1 → 2Y1 | 拡張 6 ($4017 D2) → CPU D2 |
| 14 → 13 | 2A2 → 2Y2 | パッド II データ・拡張 8 ($4017 D0) → CPU D0 |

- 出典: OFC (`M2: U7.6 U8.2`, `U7.7: P2.14 P4.4 RM1.12 U7.7`, `U7.2: P4.2 RM1.7`, `U7.4: P2.13 RM1.11`, `U7.10: C7 R8`, `P.A13: P1.49 U7.11`, `U7.12: P1.56 U5.25`, `A.IN: U7.13 P1.45 P2.2 R7`, `R7: C2 R7 U7.14`, `U8.14: RM10 → P2.8 P5.3`, ほか)、TX-7 (`/Φ2: U7.6 U8.2`, `/Controllers/4016_CUP: U7.7`)、TX-G (`/Φ2: U7.2 U8.2`, `4016_CUP: U7.3`, `4016_D0: U7.4`, `4016_D1: U7.6`)、C05 回路図 (U7 3A pin 6 = CLKOUT, 3Y pin 7 = 4016 CUP$, 4A pin 10 = MIC IN', 5A pin 12 = PA13$%, 6A pin 14 = SOUND I' を 500 dpi 画像で目視確認)。
- クロック出力の振る舞い: /OE 非アクティブ時は Hi-Z で RM1 10k により High、/OE アクティブ中は M2 の反転を出力 (M2 High の間 Low)。読み出しサイクル終了の M2 立下りでクロックが立ち上がり、4021 がシフトする (TI-4021「serial data ... shifted ... synchronously with the positive transition of the clock line」) — **推論** (データシート動作とネットからの組み立て。NESdev Standard controller「CLK ... becomes low during a read of $4016 or $4017. When the read is finished, it returns high, triggering the shift」と同じ結果)。

### Inferences
- 推論: 新基板では 368 のゲート割当は自由 (グループ 1 の 4 ゲートと /OE の対応さえ守ればよい)。PCB 配線の都合で選んでよい。
- 推論: WRAM /CS の D1/R14 遅延回路は 05 にはあるが 07 ではジャンパで短絡、GPM-02 では廃止されているので、新基板では省略可能。

### Gaps
- TC40H368 の公式データシート: **未確認** (ネット一致からの推論のみ)。

---

## 5. コントローラ プロトコルと拡張端子

### Takeaway
4021 の割当 (P8 = A、P7 = B、P6 = SELECT、P5 = START、P4 = UP、P3 = DOWN、P2 = LEFT、P1 = RIGHT、SER = GND、P/S = OUT0、CLK、Q8 → データ) と読み出し順 (A, B, Select, Start, Up, Down, Left, Right) は **確認**。パッド II は P6/P5 を +5V に固定し Select/Start 位置は常に 0 として読める。**訂正: ファミコンの $4016 は D0/D1/D2 しか駆動されず D3/D4 もオープンバス** (第1パスは「$4016/$4017 は bit 4-0 駆動、5-7 がオープンバス」と NES 一般の記述をそのまま当てはめていた)。拡張端子 15 ピンの割付は確認。コネクタの雄雌は資料間で矛盾 (NESdev = 本体側オス、EN = メス)。

### Cited Findings
- 4021 ピン (データシート): 1 = PI-8、2 = Q6、3 = Q8、4 = PI-4、5 = PI-3、6 = PI-2、7 = PI-1、8 = VSS、9 = PARALLEL/SERIAL CONTROL、10 = CLOCK、11 = SERIAL IN、12 = Q7、13 = PI-5、14 = PI-6、15 = PI-7、16 = VDD — [TI-4021](https://www.ti.com/lit/ds/symlink/cd4021b.pdf) p.1 Terminal Diagram。「In the CD4021B ... parallel entry is asynchronous」「When the PARALLEL/SERIAL CONTROL input is high, data is jammed into the 8-stage register via the parallel input lines」 — 同上
- パッド I ネット: TX-C は `A: U1.1`, `B: U1.15`, `SELECT: U1.14`, `START: U1.13`, `DOWN: U1.4`, `UP: U1.5`, `LEFT: U1.6`, `RIGHT: U1.7`、`GND: U1.11 U1.8`、`OUT0: U1.9`、`4016_CUP: U1.10`、`4016_D0: U1.3` — [TX-C](https://codeberg.org/TrexMakes/Nintendo_Famicom_Console)。OFC-C パッド I (56.8231B): `A: IC1.1`, `B: IC1.15`, `Sel.: IC1.14`, `Start: IC1.13`, **`Up: IC1.4`, `Down: IC1.5`**, `Left: IC1.6`, `Right: IC1.7`, SER (11) = GND — [OFC-C](https://github.com/starlightk7/OpenFC)。→ **パッド I の Up/Down の 4021 ピンが 2 つのネットで逆** (下記 Gaps)。パッド II は TX-C `Up: U1.4 (RN1-R4)`, `Down: U1.5 (RN1-R3)`、OFC-C `Up: IC1.4`, `Down: IC1.5` で一致 (P4 = UP, P3 = DOWN)。NESdev 標準コントローラ回路図も「Up Button -|PI-4」「Down Button -|PI-3」「A Button -|PI-8」「Right Button -|PI-1」 — [NW-M Standard controller](https://nesdev-wiki.nes.science/wikipages/Standard_controller.xhtml)
- 「PI-8 corresponds to the first button read: the A button.」「D0 reads the 4021's Q8 output.」「GND ... is also connected to its Serial In input, which will shift a 0 into each empty bit ... This is why (after inversion) the standard controller will read back all 1s once the 8 buttons have been read.」「OUT ($4016:0) controls the 4021's Parallel/Serial Control. When this goes high, the current state of the 8 buttons are read into the 4021's 8-bit register.」「CLK ... On a low-to-high transition this will shift ... This is normally held high, and becomes low during a read of $4016 or $4017.」 — [NW-M Standard controller](https://nesdev-wiki.nes.science/wikipages/Standard_controller.xhtml)
- 報告順「0 - A / 1 - B / 2 - Select / 3 - Start / 4 - Up / 5 - Down / 6 - Left / 7 - Right」「While S (strobe) is high, the shift registers in the controllers are continuously reloaded ... reading $4016/$4017 will keep returning the current state of the first button (A).」 — 同上
- 「The original Famicom's hard-wired second controller (II) is missing the Select and Start buttons. Its corresponding bits will read as 0」「This hard-wired second controller also contains a microphone, which gives an immediate 1-bit report at $4016 D2 whenever it is read.」 — 同上。ネット: パッド II の 4021 pin 13 (PI-5) と pin 14 (PI-6) が +5V (TX-C `+5V: U1.13 U1.14 U1.16`、OFC-C `VCC: IC1.13 IC1.14 IC1.16`) → 常に High → 反転後 0。
- ファミコン読み出しビット (逐語表、colspan を HTML で確認): Famicom $4016 = D0「0 if not connected」(パッド I)、D1「0 if not connected」(拡張)、D2「microphone on controller 2」、**D3「open bus」、D4「open bus」**; Famicom $4017 = D0-D4 すべて「0 if not connected」; D5-D7 は全機種「open bus」 — [NW-M Controller reading](https://nesdev-wiki.nes.science/wikipages/Controller_reading.xhtml)。回路上も U7 ($4016) は D0/D1/D2 しか駆動しない (§4.5)。
- 「In the NES and Famicom, the top three (or five) bits are not driven, and so retain the bits of the previous byte on the bus. Usually this is the most significant byte of the address of the controller port—0x40. Certain games (such as Paperboy) rely on this behavior and require that reads from the controller ports return exactly $40 or $41」 — [NW-M Standard controller](https://nesdev-wiki.nes.science/wikipages/Standard_controller.xhtml)
- 拡張端子 (逐語図、NW-L で 15 行すべて照合): 1 Gnd、2 SOUND (出力)、3 /IRQ、4 joypad 2 /D4、5 /D3、6 /D2、7 /D1、8 joypad 2 /D0、9 /OE for joypad 2 ($4017 read strobe)、10 OUT2、11 OUT1、12 OUT0、13 joypad 1 /D1、14 /OE for joypad 1 ($4016 read strobe)、15 +5V。「The Famicom has a 15-pin (male) port on the front edge of the console」「SOUND: ... In the RF Famicom, this is before expansion audio is mixed in.」「OUT2-0 ... updated every APU cycle (every 2 CPU cycles).」 — [NW-L Expansion port](https://www.nesdev.org/wiki/Expansion_port); [NW-M](https://nesdev-wiki.nes.science/wikipages/Expansion_port.xhtml)
- EN の拡張端子表も全 15 ピン同一 (「9 Out port1-CLK」「14 Out port0-CLK」「13 In port0-D1」) だが「standard db15, female」と記載 — [EN](https://problemkaputt.de/everynes.htm)。→ 本体側コネクタの雄雌は NESdev (male) と EN (female) で **矛盾**。検索結果要約では consolemods も本体側 male としている (本文 403 で未取得) — [consolemods](https://consolemods.org/wiki/NES:Connector_Pinouts)
- 拡張端子ネット (OFC / TX-7 / TX-G 一致): 1 GND、2 音声、3 /IRQ、4-8 = $4017 D4/D3/D2/D1/D0 (U8 入力)、9 = $4017 クロック (U8 pin 3)、10/11/12 = OUT2/1/0、13 = $4016 D1 (U7 入力)、14 = $4016 クロック、15 = +5V。ただし **pin 2 は 07 (OFC/TX-7) ではカート 45 側 (ミックス前)、GPM-02 (TX-G) ではカート 46 側 (`/SOUND+CART: P1.46 P2.2`)**。

#### 行ごとの判定 (第1パス §3.13 / §3.14 / §7)

| 第1パスの記載 | 判定 | 根拠 |
|---|---|---|
| 4021 割当 P8=A … P1=RIGHT | 確認 (パッド I の UP/DOWN ピンは資料間で不一致 → Gaps) | NW-M 回路図、TI-4021、OFC-C、TX-C |
| DS (pin 11) = GND、Q8 (pin 3) 出力、P/S (9) = OUT0、CLK (10) | 確認 | TI-4021、OFC-C、TX-C |
| ボタン順 A,B,Sel,Start,U,D,L,R | 確認 | NW-M 逐語 |
| ストローブ / クロック挙動 | 確認 | NW-M 逐語 + TI-4021 |
| 8 回後は 1 | 確認 | NW-M 逐語、SER=GND ネット |
| パッド II Select/Start = 0 (P6/P5 = VCC) | 確認 | NW-M 逐語、OFC-C/TX-C ネット |
| $4016 D0 パッド I、D1 拡張、D2 マイク | 確認 | NW-M 逐語表、ネット |
| $4017 D0 パッド II、D1-D4 拡張 | 確認 | 同上 |
| 「ビット 5-7 はオープンバス」/「$4016/$4017 はビット 4-0 のみ駆動」 | **不完全 (訂正)** | ファミコン $4016 は D3・D4 もオープンバス (NW-M 逐語表) |
| パッド印刷抵抗 50k (I) / 43k (II) | 値は資料により異なる | OFC-C は 40k、TX-C パッド II は 33k。印刷抵抗のため個体差 (第1パスも注記済み) |
| 拡張端子 15 ピン割付 | 確認 | NW-M/NW-L、EN、3 ネット |
| 拡張端子「15 ピン D-sub メス」 | **矛盾あり** | NESdev「(male) port」、EN「female」 → 未確認 |
| 拡張端子 pin 2 = SOUND I (ミックス前) | 07 では確認、GPM-02 では異なる可能性 | OFC/TX-7 vs TX-G |

### Inferences
- 推論: Pi エミュレーション時の $4016 読み値は「上位 5 ビット (D7-D3) = 直前のバス値 (通常 $40 の上位 → 01000)、D2 = マイク、D1 = 拡張、D0 = パッド I」。$40 の bit4/bit3 は 0 なので、実用上は第1パスの「$40|ボタン」で結果は変わらないが、仕様の記述としては D3/D4 も open bus。

### Gaps
- パッド I の 4021 pin 4 / pin 5 に UP と DOWN のどちらがつながるか: OFC-C は pin 4 = Up、pin 5 = Down (NESdev 回路図と同じで、ボタン順 Up→Down と整合)、TX-C パッド I は pin 4 = DOWN、pin 5 = UP。TX-C 側の入力ミスの可能性が高い (**推論**)。新基板ではコントローラは自作しない想定なので影響は小さいが、**未確認**として残す。
- 拡張端子の本体側コネクタ雄雌: **未確認** (NESdev male / EN female)。
- GPM-02 で拡張端子 pin 2 がカート 46 側につながるか: TX-G のみ、**未確認**。

---

## 6. 音声・映像・リセット・クロック回路の定数

### Takeaway
音声 (100 Ω 負荷、20k (矩形) / 12k (三角他)、10k (マイク)、1 µF、帰還 100k、出力 0.1 µF) と映像 (2SA937 エミッタフォロワ、220 Ω 直列、2.2k プルアップ) とリセット (0.47 µF + スイッチ) とクロック部品値は HVC-CPU-05/07 について **確認**。**訂正: マイクの経路は「R8 → R3」の直列ではなく、MIC IN から R3 10k (音声加算点へ) と R8 10k (+ 0.1 µF 対 GND、$4016 D2 バッファへ) に並列に分岐する。** また GPM-02 は帰還 43k、映像は 150 Ω プルアップ + フェライト、クロックは 1 石で CPU/PPU とも 10 nF 結合と、定数・構成が違う。クロック発振回路の型は「コルピッツ」より「ピアース型」(推論)。

### Cited Findings
#### 6.1 音声
- ネット OFC: `AD1: R2(100) R4(20K) U6.1`、`AD2: R1(100) R5(12K) U6.2`、R1/R2 他端 = GND、`C2 (加算点): C2.2 R3 R4 R5`、`R7: C2.1 R7 U7.14`、`A.IN: C8(0.1uf) P1.45 P2.2 R7 U7.13`、`R3: P5.1 (マイク) R3 R8`、`U7.10: C7(0.1uf) R8` — [OFC](https://github.com/starlightk7/OpenFC)
- TX-7 同一 (`/CPU_SND1: R2(100) R4(20k)`, `/CPU_SND2: R1(100) R5(12k)`, `Net-(C2-Pad2): C2(1u) R3(10k) R4 R5`, `/SOUND: C8(100n) P1.45 P2.2 R7(100K) U7.13`, `/MIC: P5.1 R3 R8`, `/Controllers/4016_D2: C7(100n) R8 U7.10`) — [TX-7](https://codeberg.org/TrexMakes/Nintendo_Famicom_Console)
- TX-G (GPM-02): 100/20k/100/12k/10k/C7 1µ は同じ、**帰還 R7 = 43k**、出力 C8 無し — [TX-G](https://codeberg.org/TrexMakes/Nintendo_Famicom_Console)
- C05 回路図 (目視): MIC IN が分岐し、一方は R8 10k → MIC IN' (C10 0.1uF 対 GND) → U7 pin 10、他方は R3 10k → 加算点。R4 20k・R5 12k・R1/R2 100・C2 1uF,50V・R7 100k・SOUND I → TP SOU — [C05](https://elec-junker-p2.blog.jp/FC_HVC-001%20HVC-CPU-05_REV07.pdf)
#### 6.2 映像
- OFC: `VOUT: Q1.3 (2SA937 B) U5.21`、`Q1.2 (C) = GND`、`Net-(Q1-Pad1): Q1.1 (E) R12(220)`、`VID: R12 R6(2.2K) P3.7`、`R6.1 = VCC` — [OFC](https://github.com/starlightk7/OpenFC)。TX-7 同一。2SA937 のピンは「E C B」(PPU pinout 頁の図「2SA937 ... E C B」 — [NW-M PPU pinout](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml); C05 図注記「2SA937 Grade P: ROHM PNP TRANSISTOR / EC B」)
- TX-G (GPM-02): エミッタ (`VID_A`) に R6 **150 Ω** を +5V から、フェライト FC2 → RF。220 Ω/2.2k 構成ではない。
#### 6.3 リセット
- OFC `RST: C1(0.47uf 50V) SW1 U6.3`、TX-7 `/~{RST}: C1(470n) SW1 U6.3`、C05 (C1 0.47µF/50V)。TX-G は C8 「47n」と記載 (0.47 µF の誤記か実値かは **未確認**)。いずれも外付けプルアップ無し。PPU /RST は +5V。
#### 6.4 クロック
- OFC: X1 21.47727 MHz の一端 = Q2 コレクタ節点 (`X1: C4(51p) C6(15p) Q2.2 Q3.3 R10(1.2K) R11(220K) X1.2`)、他端 = C22 18p + TC1 30p トリマを経てベース節点 (`C3: C22 C3(51pf) Q2.3 R11 TC1`)、C3 51p ベース対 GND、C6 15p コレクタ対 GND、R10 1.2k コレクタ負荷 (VCC)、R11 220k コレクタ-ベース帰還バイアス、Q2 エミッタ GND。PPU CLK = C4 51p でコレクタ節点から結合 (`Net-(U5-CLK): C4 U5.18`)。CPU CLK = Q3 (エミッタフォロワ、ベース = コレクタ節点、エミッタ R9 1.2k 対 GND) → C9 220p → U6.29、U6.29 に R13 150k 対 GND。C5 は DNP — [OFC](https://github.com/starlightk7/OpenFC)。TX-7 同値。C05 回路図では C9 と並列にジャンパ「CL」がある (目視)。
- TX-G (GPM-02): 1 石 (Q2) のみ、R10 100k / R11 1.2k / R9 150 + C2 10n (エミッタ)、CPU CLK・PPU CLK ともコレクタ節点から 10 nF (C4/C5) で結合。

#### 行ごとの判定 (第1パス §3.8-3.11、§6 項目)

| 第1パスの記載 | 判定 | 根拠 |
|---|---|---|
| AD1: 100 Ω 対 GND + 20k | 確認 | OFC, TX-7, TX-G, C05 (参照番号は R1/R2 が版で入れ替わる) |
| AD2: 100 Ω 対 GND + 12k | 確認 | 同上 |
| マイク: R8 10k (+C10) → R3 10k → 加算点 | **誤り** | R3 と R8 は MIC IN から並列分岐 (C05 目視、OFC、TX-7、TX-G) |
| C2 1 µF/50V → 368 6A、R7 100k 帰還、出力 C8 0.1 µF | 確認 (05/07)。GPM-02 は 43k・C8 無し | 同上 |
| 利得 約 5 倍 / 8.3 倍 | 推論のまま (100 Ω 負荷により実効値は異なる) | — |
| 映像: 2SA937、エミッタ → 220 Ω → VIDEO、2.2k プルアップ | 確認 (05/07)。GPM-02 は 150 Ω のみ | OFC, TX-7, TX-G |
| リセット: C1 0.47 µF + SW1、外付けプルアップ無し | 確認 | OFC, TX-7, C05 |
| クロック部品値 (220k, 18p, 30p トリマ, 51p, 1.2k, 15p, C4 51p, Q3 + 1.2k, C9 220p, R13 150k) | 確認 (05/07) | OFC, TX-7 |
| 「コルピッツ型」 | 表現要修正 (推論) | 水晶をコレクタ-ベース間に置き両端を C で接地する構成はピアース型 |
| 「C5 5 pF NC」/ OpenFC「C5 30pF」 | C5 は OpenFC で DNP | OFC 回路図 `(dnp yes)` |

### Inferences
- 推論: 新基板で 5V CMOS 発振器を使う場合、GPM-02 が CPU/PPU とも 10 nF で AC 結合しているので、2A03/2C02 の CLK 入力は内部バイアスを持つ AC 結合入力として扱われていると考えられる。発振器出力を直結してよいかは **未確認**。

### Gaps
- 2A03/2C02 CLK 入力の推奨振幅・バイアス: **未確認**。

---

## 7. タイミング (再計算)

### Takeaway
全数値 **確認**。マスタ 21.477272 MHz (= 236.25 MHz ÷ 11)、CPU = ÷12 = 1.789773 MHz、PPU ドット = ÷4 = 5.369318 MHz、1 ライン 341 ドット → 15.7458 kHz、1 フレーム 262 ライン = 89342 ドット (描画有効時の奇数フレームは 89341)、平均 89341.5 ドット → 60.0988 Hz。M2 High = 15/24 × 558.73 ns = 349.2 ns (2A03E/G/H)、無印 2A03 は 17/24 = 395.8 ns。

### Cited Findings
- 「21.477272 MHz ± 40 Hz」「236.25 MHz ÷ 11 by definition」「21.47~ MHz ÷ 12 = 1.789773 MHz」「341 × 261 + 340.5 = 89341.5 (pre-render line is one dot shorter in every odd frame)」「89341.5 ÷ 3 = 29780.5」「60.0988 Hz」 — [NW-M Cycle reference chart](https://nesdev-wiki.nes.science/wikipages/Cycle_reference_chart.xhtml)
- 「With rendering disabled ... each PPU frame is 341*262=89342 PPU clocks long. There is no skipped clock every other frame. With rendering enabled, each odd PPU frame is one PPU clock shorter than normal.」 — [NW-M PPU frame timing](https://nesdev-wiki.nes.science/wikipages/PPU_frame_timing.xhtml)
- 「The PPU renders 262 scanlines per frame. Each scanline lasts for 341 PPU clock cycles (113.667 CPU clock cycles; 1 CPU cycle = 3 PPU cycles)」 — [NW-M PPU rendering](https://nesdev-wiki.nes.science/wikipages/PPU_rendering.xhtml)
- 「divided by 4 (NTSC) ... for the pixel and memory clocks」 — [NW-M PPU pinout](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml)
- M2 デューティ: §1 の逐語引用 (15/24 = 350ns/559ns、17/24 = 396ns/559ns)。

| 量 | 計算 (自分で再計算) | 値 | 判定 |
|---|---|---|---|
| マスタ | 236.25 MHz / 11 | 21.4772727 MHz | 確認 |
| CPU (M2) | /12 | 1.7897727 MHz (558.73 ns) | 確認 |
| M2 High (E/G/H) | 15/24 × 558.73 | 349.2 ns (Low 209.5 ns) | 確認 |
| M2 High (無印) | 17/24 × 558.73 | 395.8 ns | 確認 |
| PPU ドット | /4 | 5.3693182 MHz | 確認 |
| ライン周波数 | 5.3693182 MHz / 341 | 15.7458 kHz | 確認 |
| フレーム (描画無効) | / 89342 | 60.0985 Hz | 確認 |
| フレーム (描画有効・2 フレーム平均) | / 89341.5 | 60.0988 Hz | 確認 |

### Inferences
- なし (数値は一致)。

### Gaps
- なし。

---

## 既存ノートへの訂正

| # | 第1パスの箇所 | 誤り / 不足 | 正しい内容 | 根拠 |
|---|---|---|---|---|
| 1 | §3.8 オーディオ回路 | 「マイク (MIC IN) → R8 10k (+ C10 0.1µF 対 GND) → R3 10k で加算点へ」 | MIC IN は 2 系統に並列分岐: (a) R3 10k → 音声加算点、(b) R8 10k → U7 pin 10 (1A4、C10/C7 0.1 µF 対 GND) → pin 9 → CPU D2 ($4016 マイクビット) | C05 目視、OFC、TX-7、TX-G |
| 2 | §7 / §4「$4016/$4017 はビット 4-0 のみ駆動、ビット 5-7 はオープンバス」 | ファミコンの $4016 について不完全 | ファミコン $4016 は D0 (パッド I)・D1 (拡張)・D2 (マイク) のみ駆動、**D3・D4 も open bus**。$4017 は D0-D4 駆動 | NW-M Controller reading 逐語表、368 ネット |
| 3 | §6 方向の注記「NESdev 図の矢印は一部不整合があると WebFetch 要約で指摘」 | 誤り (要約モデルの誤り) | 逐語図の矢印は全 60 ピンで一貫。45 = 本体→カート、46 = カート→本体 | NW-M/NW-L 逐語 |
| 4 | §3.16「デコーダ: … U3.4 → D1/R14/C20 → U1.18 (両ソースで一致)」 | HVC-CPU-07 については不正確 | 07 のネット (OFC、TX-7) では U3.4・D1 両端・R14 両端・U1.18 が同一ネット (遅延回路はジャンパで短絡、TX-7 は JP1「CL1」)。遅延回路が効くのは 05 の回路図のみ。GPM-02 は部品自体無し | OFC、TX-7、TX-G、C05 |
| 5 | §3.7 / §3.6 の 368 ゲート割当 | 基板版依存であることが書かれていない | 05/07 は U7 の 3 番ゲート (6→7) が M2 クロック、1 番 (2→3) が D0。GPM-02 は 1 番ゲート (2→3) が M2 クロック、2 番 (4→5) が D0、3 番 (6→7) が D1 | OFC、TX-7、TX-G |
| 6 | §1 Pin 32 /IRQ「内部プルアップあり」 | 主語が曖昧 | NESdev の「internal pull-up」は本体基板上の 10k (RM1) のこと。2A03 チップ内蔵プルアップは未確認 | NW-M Expansion port「internal 10kΩ pull-up」、ネット RM1 |
| 7 | §3.9「Q2 コルピッツ型水晶発振」/「C5 5 pF NC」/§3.16「C5 30pF」 | 回路型の名称と C5 | 構成はピアース型 (推論)。C5 は OpenFC で DNP | OFC ネット・回路図 |
| 8 | §3.14 / §7「拡張端子 15 ピン D-sub メス」 | 資料間で矛盾 | NESdev は「15-pin (male) port」、EN は「female」。未確認として扱う | NW-L、EN |
| 9 | §8 で GPM 基板の差は R7 のみのように読める | 差分の追加 | GPM-02 (TX-G) は R7 43k に加えて、映像 150 Ω + フェライト、クロック 1 石 + 10 nF 結合、WRAM 遅延回路無し、PPU /CS コンデンサ無し、/OE 線に 560 pF (C37/C38)、カート 31 = +5V、拡張 pin 2 = カート 46 側 | TX-G |
| 10 | §6 カード寸法「検索結果スニペット経由、本文未取得」 | 本文で確認済みに格上げ | 1.2 mm 厚、2.54 mm ピッチ、端子深さ 10.7 mm、電源パッド高 6.7 mm / 信号 5.7 mm (±0.05) | NW-M Famicom cartridge dimensions |

上記以外の第1パスの表 (2A03 全 40 ピン、2C02 全 40 ピン、60 ピン割付、74139/373 配線、U8 割付、拡張端子割付、タイミング) は誤りなし。

---

## 確定版の表 (PCB 設計用)

### A. RP2A03 (DIP-40)

| Pin | 名称 | 方向 | 接続先 (ファミコン準拠) |
|---|---|---|---|
| 1 | AD1 | 出力 (アナログ) | 100 Ω 対 GND + 20k → 音声加算点 (矩形波 2ch) |
| 2 | AD2 | 出力 (アナログ) | 100 Ω 対 GND + 12k → 音声加算点 (三角・ノイズ・DPCM) |
| 3 | /RST | 入力 | 0.47 µF 対 GND + リセット SW (外付けプルアップ無し) |
| 4-19 | A0-A15 | 出力 | 4 = A0, 5 = A1, … 18 = A14, 19 = A15 |
| 20 | GND | 電源 | |
| 21-28 | D7-D0 | 双方向 | 21 = D7, 22 = D6, … 27 = D1, 28 = D0 |
| 29 | CLK | 入力 | 21.47727 MHz (05/07: 220 pF 結合 + 150k 対 GND、GPM-02: 10 nF 結合) |
| 30 | TST | 入力 | GND |
| 31 | M2 | 出力 | 139 pin 14、368 クロックゲート入力、カート 32 |
| 32 | /IRQ | 入力 | カート 15、拡張 3、10k プルアップ |
| 33 | /NMI | 入力 | PPU pin 19、10k プルアップ |
| 34 | R/W | 出力 | PPU 1、WRAM /WE、カート 14 |
| 35 | /OE2 | 出力 | $4017 読み出し時 L → 368 (U8) pin 1 と pin 15 |
| 36 | /OE1 | 出力 | $4016 読み出し時 L → 368 (U7) pin 1 |
| 37 | OUT2 | 出力 | $4016 書込 bit2 → 拡張 10 |
| 38 | OUT1 | 出力 | $4016 書込 bit1 → 拡張 11 |
| 39 | OUT0 | 出力 | $4016 書込 bit0 → 両パッド 4021 P/S、拡張 12 |
| 40 | VCC | 電源 | +5 V |

### B. RP2C02 (DIP-40)

| Pin | 名称 | 方向 | 接続先 |
|---|---|---|---|
| 1 | R/W | 入力 | CPU 34 |
| 2-9 | CPU D0-D7 | 双方向 | 2 = D0 (CPU 28), 3 = D1, … 9 = D7 (CPU 21) |
| 10 | CPU A2 | 入力 | CPU 6 |
| 11 | CPU A1 | 入力 | CPU 5 |
| 12 | CPU A0 | 入力 | CPU 4 |
| 13 | /CS | 入力 | 139 pin 5 (1Y1、$2000-$3FFF) |
| 14-17 | EXT0-EXT3 | 双方向 | GND |
| 18 | CLK | 入力 | 21.47727 MHz (05/07: 51 pF 結合、GPM-02: 10 nF) |
| 19 | /INT | 出力 (オープンドレイン) | CPU 33 + 10k プルアップ |
| 20 | GND | 電源 | |
| 21 | VOUT | 出力 (アナログ) | 2SA937 ベース |
| 22 | /RST | 入力 | +5 V (ファミコン方式) |
| 23 | /WR | 出力 | VRAM /WE、カート 47 |
| 24 | /RD | 出力 | VRAM /OE、カート 17 |
| 25 | PA13 | 出力 | カート 56、368 (U7) pin 12 (→ /PA13) |
| 26 | PA12 | 出力 | カート 55 |
| 27 | PA11 | 出力 | カート 54 |
| 28 | PA10 | 出力 | カート 53 |
| 29 | PA9 | 出力 | カート 52、VRAM A9 |
| 30 | PA8 | 出力 | カート 51、VRAM A8 |
| 31-38 | AD7-AD0 | 双方向 | 31 = AD7 … 38 = AD0 (= PD7…PD0) → VRAM I/O、373 D、カート |
| 39 | ALE | 出力 | 373 pin 11 (LE) |
| 40 | VCC | 電源 | +5 V |

### C. 60 ピン カートリッジスロット

**番号付け規約 (曖昧さなし)**:
- 本体スロットを **上から見下ろし、本体の正面 (プレイヤー側、拡張端子のある側) を手前**にしたとき: 手前の列が pin 1-30 で **左端が pin 1、右端が pin 30**。奥の列が pin 31-60 で **左端が pin 31 (pin 1 の真後ろ)、右端が pin 60**。
- カートリッジ: **ラベル面が pin 1-30 側** (ラベルは本体正面を向いて挿さる)。ラベル面を見て端子を下にすると **左端が pin 1**。部品面 (ラベルの反対側) を見て端子を下にすると **右端が pin 31、左端が pin 60**。
- ピッチ 2.54 mm、2 列 × 30。カード厚 1.2 mm。
- 方向は本体側から見たもの (出力 = 本体→カート)。

| Pin | 信号 | 方向 | | Pin | 信号 | 方向 |
|---|---|---|---|---|---|---|
| 1 | GND | 電源 | | 31 | +5V (版によりカート検出) | 電源 / 入力 |
| 2 | CPU A11 | 出力 | | 32 | M2 | 出力 |
| 3 | CPU A10 | 出力 | | 33 | CPU A12 | 出力 |
| 4 | CPU A9 | 出力 | | 34 | CPU A13 | 出力 |
| 5 | CPU A8 | 出力 | | 35 | CPU A14 | 出力 |
| 6 | CPU A7 | 出力 | | 36 | CPU D7 | 双方向 |
| 7 | CPU A6 | 出力 | | 37 | CPU D6 | 双方向 |
| 8 | CPU A5 | 出力 | | 38 | CPU D5 | 双方向 |
| 9 | CPU A4 | 出力 | | 39 | CPU D4 | 双方向 |
| 10 | CPU A3 | 出力 | | 40 | CPU D3 | 双方向 |
| 11 | CPU A2 | 出力 | | 41 | CPU D2 | 双方向 |
| 12 | CPU A1 | 出力 | | 42 | CPU D1 | 双方向 |
| 13 | CPU A0 | 出力 | | 43 | CPU D0 | 双方向 |
| 14 | CPU R/W | 出力 | | 44 | /ROMSEL = NAND(M2, A15) | 出力 |
| 15 | /IRQ | 入力 (10k プルアップ) | | 45 | 音声 (2A03 増幅済み) | 出力 |
| 16 | GND | 電源 | | 46 | 音声戻り (→ アンプ/出力) | 入力 |
| 17 | PPU /RD | 出力 | | 47 | PPU /WR | 出力 |
| 18 | CIRAM A10 | 入力 | | 48 | CIRAM /CE | 入力 |
| 19 | PPU A6 | 出力 | | 49 | PPU /A13 | 出力 |
| 20 | PPU A5 | 出力 | | 50 | PPU A7 | 出力 |
| 21 | PPU A4 | 出力 | | 51 | PPU A8 | 出力 |
| 22 | PPU A3 | 出力 | | 52 | PPU A9 | 出力 |
| 23 | PPU A2 | 出力 | | 53 | PPU A10 | 出力 |
| 24 | PPU A1 | 出力 | | 54 | PPU A11 | 出力 |
| 25 | PPU A0 | 出力 | | 55 | PPU A12 | 出力 |
| 26 | PPU D0 | 双方向 | | 56 | PPU A13 | 出力 |
| 27 | PPU D1 | 双方向 | | 57 | PPU D7 | 双方向 |
| 28 | PPU D2 | 双方向 | | 58 | PPU D6 | 双方向 |
| 29 | PPU D3 | 双方向 | | 59 | PPU D5 | 双方向 |
| 30 | +5V | 電源 | | 60 | PPU D4 | 双方向 |

### D. 74x139 (アドレスデコーダ)

| Pin | 名称 | 接続 |
|---|---|---|
| 1 | 1G | pin 11 |
| 2 | 1A | CPU A13 |
| 3 | 1B | CPU A14 |
| 4 | 1Y0 | WRAM /CS ($0000-$1FFF) |
| 5 | 1Y1 | PPU /CS ($2000-$3FFF) |
| 6, 7 | 1Y2, 1Y3 | NC |
| 8 | GND | |
| 9 | 2Y3 | /ROMSEL → カート 44 |
| 10 | 2Y2 | NC |
| 11 | 2Y1 | → pin 1 |
| 12 | 2Y0 | NC |
| 13 | 2B | CPU A15 |
| 14 | 2A | M2 |
| 15 | 2G | GND |
| 16 | VCC | |

### E. 74x373 (PPU 下位アドレスラッチ)

| Pin | 名称 | 接続 | | Pin | 名称 | 接続 |
|---|---|---|---|---|---|---|
| 1 | /OE | GND | | 11 | LE | PPU ALE (39) |
| 2 | 1Q | PA7 | | 12 | 5Q | PA3 |
| 3 | 1D | PD7 (PPU 31) | | 13 | 5D | PD3 |
| 4 | 2D | PD6 | | 14 | 6D | PD2 |
| 5 | 2Q | PA6 | | 15 | 6Q | PA2 |
| 6 | 3Q | PA5 | | 16 | 7Q | PA1 |
| 7 | 3D | PD5 | | 17 | 7D | PD1 |
| 8 | 4D | PD4 | | 18 | 8D | PD0 (PPU 38) |
| 9 | 4Q | PA4 | | 19 | 8Q | PA0 |
| 10 | GND | | | 20 | VCC | |
(PA0-PA7 → VRAM A0-A7、カート 25…19 = PA0…PA6、カート 50 = PA7)

### F. 74x368 ×2 (HVC-CPU-05/07 準拠の割付。ゲート選択は自由)

U7 ($4016 / 空きゲート流用):

| Pin | 名称 | 接続 |
|---|---|---|
| 1 | 1OE | CPU 36 (/OE1) |
| 2 → 3 | 1A1 → 1Y1 | パッド I データ (10k プルアップ) → CPU D0 |
| 4 → 5 | 1A2 → 1Y2 | 拡張 13 (10k プルアップ) → CPU D1 |
| 6 → 7 | 1A3 → 1Y3 | M2 → $4016 クロック (パッド I CLK、拡張 14、10k プルアップ) |
| 10 → 9 | 1A4 → 1Y4 | マイク (R8 10k + 0.1 µF 対 GND) → CPU D2 |
| 8 / 16 | GND / VCC | |
| 15 | 2OE | GND |
| 12 → 11 | 2A1 → 2Y1 | PPU PA13 → /PA13 (カート 49) |
| 14 → 13 | 2A2 → 2Y2 | 加算点 (1 µF 経由) → 音声出力 (カート 45、拡張 2)、13↔14 に 100k (GPM は 43k)、出力 0.1 µF 対 GND |

U8 ($4017):

| Pin | 名称 | 接続 |
|---|---|---|
| 1, 15 | 1OE, 2OE | CPU 35 (/OE2) |
| 2 → 3 | 1A1 → 1Y1 | M2 → $4017 クロック (パッド II CLK、拡張 9、10k プルアップ) |
| 4 → 5 | 1A2 → 1Y2 | 拡張 7 → CPU D1 |
| 6 → 7 | 1A3 → 1Y3 | 拡張 5 → CPU D3 |
| 10 → 9 | 1A4 → 1Y4 | 拡張 4 → CPU D4 |
| 12 → 11 | 2A1 → 2Y1 | 拡張 6 → CPU D2 |
| 14 → 13 | 2A2 → 2Y2 | パッド II データ・拡張 8 → CPU D0 |
| 8 / 16 | GND / VCC | |
(各データ入力は 10k プルアップ。368 は反転なので「押下 = L」が 1 として読める)

### G. コントローラ (4021) と読み出しビット

| 4021 pin | 名称 | パッド I | パッド II |
|---|---|---|---|
| 1 | PI-8 | A | A |
| 15 | PI-7 | B | B |
| 14 | PI-6 | SELECT | +5V 固定 (常に 0 と読める) |
| 13 | PI-5 | START | +5V 固定 (常に 0 と読める) |
| 4 | PI-4 | UP | UP |
| 5 | PI-3 | DOWN | DOWN |
| 6 | PI-2 | LEFT | LEFT |
| 7 | PI-1 | RIGHT | RIGHT |
| 9 | P/S | OUT0 | OUT0 |
| 10 | CLK | $4016 クロック | $4017 クロック |
| 11 | SER | GND | GND |
| 3 | Q8 | → U7 pin 2 | → U8 pin 14 |
| 8 / 16 | VSS / VDD | GND / +5V | GND / +5V |
(パッド I の PI-4/PI-3 は NESdev 図と OFC-C に従う。TX-C は逆 — §5 Gaps)

| ビット | $4016 読み (ファミコン) | $4017 読み (ファミコン) |
|---|---|---|
| D0 | パッド I (反転、押下=1) | パッド II |
| D1 | 拡張端子 13 | 拡張端子 7 |
| D2 | マイク (瞬時値) | 拡張端子 6 |
| D3 | open bus | 拡張端子 5 |
| D4 | open bus | 拡張端子 4 |
| D5-D7 | open bus | open bus |

### H. 拡張端子 15 ピン (割付は確定、雄雌は未確認)

| Pin | 信号 | 方向 (本体から) |
|---|---|---|
| 1 | GND | 電源 |
| 2 | 音声 (05/07: カート 45 側 = ミックス前) | 出力 |
| 3 | /IRQ | 双方向 |
| 4 | $4017 D4 入力 | 入力 |
| 5 | $4017 D3 入力 | 入力 |
| 6 | $4017 D2 入力 | 入力 |
| 7 | $4017 D1 入力 | 入力 |
| 8 | $4017 D0 (パッド II と共通) | 入力/出力 |
| 9 | $4017 クロック (/OE ゲート付き反転 M2) | 出力 |
| 10 | OUT2 | 出力 |
| 11 | OUT1 | 出力 |
| 12 | OUT0 | 出力 |
| 13 | $4016 D1 入力 | 入力 |
| 14 | $4016 クロック | 出力 |
| 15 | +5V | 電源 |

### I. 回路定数 (HVC-CPU-05/07 準拠)

| ブロック | 定数 |
|---|---|
| 音声 | AD1: 100 Ω 対 GND, 20k; AD2: 100 Ω 対 GND, 12k; マイク: 10k (加算) と 10k + 0.1 µF ($4016 D2 へ); 結合 1 µF/50V; 368 反転アンプ帰還 100k (GPM-02: 43k); 出力 0.1 µF 対 GND |
| 映像 | PPU 21 → 2SA937 (E-C-B) ベース、コレクタ GND、エミッタ → 220 Ω → VIDEO、VIDEO に 2.2k を +5V へ |
| リセット | CPU /RST に 0.47 µF 対 GND + SW、PPU /RST = +5V、CPU TST = GND |
| クロック | X1 21.47727 MHz; Q2 2SC2021: R10 1.2k (負荷), R11 220k (C-B), C6 15p (C 対 GND), C3 51p (B 対 GND), C22 18p ∥ TC1 30p トリマ (水晶-ベース間); PPU CLK = C4 51p 結合; CPU CLK = Q3 エミッタフォロワ (R9 1.2k) → C9 220p → CPU 29、CPU 29 に R13 150k 対 GND |
| WRAM /CS | 05: D1 1S953 ∥ R14 1.2k + C20 68 pF; 07: ジャンパで短絡 (+68 pF); GPM-02: 直結 |
| PPU /CS | 05/07: 330 pF + 30 pF 対 GND; GPM-02: 無し |
| プルアップ | RM1 10k ×11 (/IRQ, /NMI, 各コントローラデータ・クロック線) |

### J. タイミング

| 量 | 値 |
|---|---|
| マスタクロック | 21.477272 MHz (236.25/11) |
| CPU (M2) | 1.789773 MHz (÷12)、周期 558.73 ns |
| M2 デューティ | 2A03E/G/H: 15/24 (High 349.2 ns); 無印 2A03: 17/24 (395.8 ns) |
| PPU ドット | 5.369318 MHz (÷4) |
| 1 ライン | 341 ドット = 113.667 CPU サイクル → 15.7458 kHz |
| 1 フレーム | 262 ライン = 89342 ドット (描画有効時の奇数フレーム 89341) |
| フレームレート | 60.0988 Hz (描画有効の 2 フレーム平均) / 60.0985 Hz (描画無効) |

---

## 未確認事項のまとめ
- 2A03 内部プルアップ (/RST, /IRQ, /NMI) の有無と値。
- TC40H368 の公式データシート (ピン配置はネット一致から 74368 と同一と推論)。
- 拡張端子の本体側コネクタ雄雌 (NESdev: male、EN: female)。
- パッド I の 4021 PI-4/PI-3 と UP/DOWN の対応 (OFC-C と NESdev は PI-4 = UP、TX-C は逆)。
- GPM-02 のリセットコンデンサ値 (TX-G 表記 47n)、拡張端子 pin 2 の接続先 (TX-G ではカート 46 側)。
- 2A03/2C02 CLK 入力に CMOS 発振器を直結してよいか。
- NESdev ミラー (nesdev-wiki.nes.science) のスナップショット日付。ただし要所は現行版 (NW-L) の逐語短文引用で一致を確認済み。
