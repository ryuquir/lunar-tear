# NESRGB 方式（EXT＋シャドウパレット＋スプライト/BG 判定）を Pico 2（RP2350）で実装する工学的実現性調査

調査日: 2026-11-10（第2パス・ギャップ埋めと検証）。前提ノート: `rgb_from_rp2c02.md`（第1パス）、`rgb_round2_details.md`、`raspberry_pi_emulation_path.md`、`famicom_hardware.md`、`pico2_platform_verification.md`、`parts_class_reverification.md`、`jamma_electrical_details.md`。
表記: 「Cited Findings」= 出典付き事実（URL 明記）。「Inferences」= **推論**（筆者の判断・計算。出典の裏付けはない）。確認できなかった事項は **未確認**。

一次資料（2026-11-10 にダウンロードし pdftotext / HTML→テキストで本文確認）:
- RP2350 Datasheet, Release 8, Build date 01/10/2026, Build version 80d627281ed5 — https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Raspberry Pi Pico 2 Datasheet — https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- Hardware design with RP2350 — https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- TI SN74HC245 — https://www.ti.com/lit/ds/symlink/sn74hc245.pdf 、TI SN74HC14 — https://www.ti.com/lit/ds/symlink/sn74hc14.pdf
- NESdev Wiki（静的ミラー nesdev-wiki.nes.science を curl 取得、逐語確認）: CPU pinout, PPU pinout, PPU registers, PPU programmer reference, NTSC video, Standard controller
- 秋月電子通商の商品ページ（2026-11-10 の価格・在庫表示）
- 計算スクリプト: /tmp/p2f/scripts/pll.py（12 MHz 基準から到達できる PLL 設定の全探索。本ノート末尾に結果を転記）

取得方法の注記: Nexperia のデータシートは Akamai の Access Denied で取得不可（TI 版で代替）。本調査の途中で WebSearch の上限に達したため、後半は既知 URL の直接取得（WebFetch / curl）だけで裏取りした。

---

## 1. タイミング予算（一次資料の値）

### Takeaway
マスタークロック 46.56 ns、画素 186.24 ns（4 マスタークロック）、CPU サイクル 558.7 ns、M2 High 約 349 ns（15/24）。2A03 の書込みデータは M2 立上りの約 100 ns 後に乗る（実測）ので、PPU レジスタ書込みには「M2 立上り＋約 100 ns 〜 M2 立下り」の約 250 ns の有効窓がある。2C02 がレジスタ書込みを /CS（/DBE）のどのエッジで確定するか、必要なセットアップ/ホールドの数値は公開資料に無い（**未確認**）。RP2350 側は「1 命令 1 クロック」「入力 2 段同期（2 クロック、GPIO 毎にバイパス可）」が明記され、clk_sys 最大 150 MHz（150 MHz で 6.67 ns/命令）。PIO は約 28 命令/画素、約 84 命令/CPU サイクルの余裕があり、時間分解能の点では十分。

### Cited Findings
**ファミコン側**
- 「The NTSC master clock is 21.47727273 MHz and each PPU pixel lasts four of these clocks: 186ns.」「The video output of the PPU is delayed by 1 pixel clock」— [NESdev Wiki: NTSC video（ミラー）](https://nesdev-wiki.nes.science/wikipages/NTSC_video.xhtml)
- CPU: CLK を ÷12 して φ0。「In the NTSC 2A03E, G, and H, M2 has a duty cycle of 15/24 (5/8), or 350ns/559ns. Equivalently, a CPU read (which happens during the second, high phase of M2) takes 1 and 7/8th PPU cycles.」無印 2A03 は 17/24（396ns/559ns）。「CPU cycles begin at the point where M2 goes low.」/RST 解除後「after 6 M2 clocks」でベクタ読出し — [NESdev Wiki: CPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml)
- 2A03 書込みサイクルの実測（lidnariq, 2019-11-17, 60 MHz スコープ）:「M2 rises 70-90ns after R/W does」「M2 falls 60-56ns before R/W does」、D0 は R/W 立下りの約 250-260 ns 後、「roughly 100ns after M2 rises」に約 4 V へ。R/W 立上り約 20 ns・立下り約 10 ns、M2 エッジ約 5 ns。74'139 の遅延は NES-CPU-07 で約 20 ns。同スレッドで「data hold after M2 falls」は測定されていない — [NESdev forum t=19483](https://forums.nesdev.org/viewtopic.php?t=19483)
- PPU の CPU インタフェース: R/W, D0-D7, RS0-RS2, /DBE（=/CS）。「It should be understood that the access to the PPU registers is not related to PCLK in any way.」（レジスタアクセスは PCLK と非同期）— [Breaking NES Wiki: PPU regs.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/regs.md), [pads.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md)
- /CS は 74139 で生成、「This signal is sometimes referred to as /DBE.」— [NESdev Wiki: PPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml)。パレット読出しの破損は「depends on when the PPU /CS signal that indicates register access is deasserted, which varies by console」— [PPU registers（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_registers.xhtml)。→ /CS 解除タイミングが PPU の挙動に影響すること自体は確認できるが、書込みのセットアップ/ホールドの数値は無い。
- 参考値（6502 系、2A03 ではない）: Rockwell 6502 は「Data bus stable during a write after φ2 rises: max 100ns」（実測 30 ns と比較）— 同 t=19483（lidnariq 2019-11-18 の引用）。
- 2A03/2C02 の出力 High は約 4 V:「my previous measurements have Voh from the 2A03 and 2C02 at approximately 4V」(lidnariq 2020-01-05) — [NESdev forum t=19656 p.2](https://forums.nesdev.org/viewtopic.php?t=19656&start=15)。入力閾値は未測定:「It's a mixture, but you just assume it's TTL thresholds. Because the NES is NMOS, not CMOS.」「To actually quantify the data bus inputs, we'll need to build a specialty cart」(Lidnariq 2022-03-30) — [NESdev Wiki: Talk:Cartridge connector](https://www.nesdev.org/wiki/Talk:Cartridge_connector)

**RP2350 側（RP2350 Datasheet）**
- 「On every system clock cycle, each state machine fetches, decodes and executes one instruction. Each instruction takes precisely one cycle, unless it explicitly stalls (such as the WAIT instruction).」— §11.2.2
- 「each GPIO input is equipped with a standard 2-flipflop synchroniser. This adds two cycles of latency to input sampling」「It is possible to bypass these synchronisers, on a per-GPIO basis … Generally this is only possible for synchronous interfaces」— §11.5.6.3（INPUT_SYNC_BYPASS レジスタ）
- PIO は 3 ブロック×4 SM、命令メモリは各ブロック 32 命令、各 SM に「4 × 32-bit bus FIFO in each direction (TX/RX), reconfigurable as 8 × 32 in a single direction」「Fractional clock divider (16 integer, 8 fractional bits)」「DMA interface (sustained throughput up to 1 word per clock from system DMA)」— §11.1
- RP2350 の PIO 追加機能: SHIFTCTRL.IN_COUNT（不要ピンを 0 マスク）、MOV の宛先に PINDIRS、RX FIFO の各エントリをランダムアクセスできる FJOIN_RX_GET / FJOIN_RX_PUT、別 PIO ブロック間 IRQ（「no delay penalty … observable to all state machines on the next cycle」）、CTRL.NEXTPREV_CLKDIV_RESTART、「Improved GPIO input/output delay and skew」— §11.1.1
- DMA: 「The DMA dual bus manager ports can issue one read and one write access per cycle.」— §12.6。バス: 150 MHz で「maximum sustained bus bandwidth is 3.6 GB/s」— §2.1
- 各コアに INTERP0/INTERP1（「table lookup address generation」等を 1 サイクルで）— §3.1.10
- clk_sys 公称最大 150 MHz（Table 573）。
- GPIO の伝搬遅延（パッド入力→PIO、PIO→パッド出力）の ns 値はデータシート本文に見当たらない（「Improved … delay and skew」の定性記述のみ）→ **未確認**。

### Inferences（推論・計算）
| 量 | 値 | 根拠 |
|---|---|---|
| マスタークロック周期 | 46.56 ns | 1/21.477272 MHz |
| 画素 | 186.24 ns = 4 MC | NTSC video |
| CPU サイクル | 558.7 ns = 12 MC | CPU pinout |
| M2 High | 349 ns = 7.5 MC（2A03E/G/H）、396 ns（無印） | CPU pinout |
| 書込みデータ有効窓（M2 High 内） | 約 100 ns 後〜M2 立下り ⇒ 約 250 ns | t=19483 実測 |
| PIO 1 命令 | 6.67 ns（150 MHz）/ 7.75 ns（129 MHz） | datasheet |
| 同期器遅延 | +2 命令（13〜16 ns）、バイパスで 0 | datasheet |
| 1 画素あたり命令数 | 27.9（150 MHz）/ 24（129 MHz、後述のクロック案） | 計算 |
| 1 CPU サイクルあたり命令数 | 84（150 MHz）/ 72（129 MHz） | 計算 |
| 画素データ量 | 5 bit × 5.37 MHz = 26.8 Mbit/s（8 bit 詰めでも 1.34 Mword/s） | 計算。DMA の 1 word/clock に対し 1% 未満 |

- PPU レジスタ書込みの確定エッジが不明なので、**置換する書込みでは「/CS が Low の間ずっと＋/CS 立上り後 20〜30 ns」PPU 側データを駆動し続ける**設計にすれば、ラッチが透過型でもエッジ型でもセットアップ/ホールドを満たす（推論）。
- 盗聴（スヌープ）で CPU データを読む時刻は「/CS 立上り後」ではなく「M2 立下りの 50〜70 ns 前」にすべき（CPU のホールド時間が未測定で、/CS は 74139 経由で M2 より 20〜30 ns 遅れて立ち上がるため、/CS 立上りを見てから同期器 2 段を経て読むと M2 立下り後 40〜60 ns になり、データが残っている保証がない）（推論）。

### Gaps
- 2C02 のレジスタ書込みのセットアップ/ホールド、/CS→ラッチの内部遅延: 3 経路（NESdev Wiki 各ページ、Breaking NES の回路解析、NESdev フォーラム）で探したが数値なし → **未確認**。
- 2A03 の書込みデータのホールド時間（M2 立下り後）: 実測値なし → **未確認**。
- RP2350 GPIO のパッド遅延（ns）: データシートに数値なし → **未確認**。

---

## 2. 候補アーキテクチャ（信号一覧とタイミング論証）

### Takeaway
**推奨は「RP2350 がマスタークロック（21.5 MHz）と PPU /RST を自分で生成し、PIO を PPU と完全同期させる」構成**。こうすると EXT サンプリング位相と画素位相が毎回同じになり、既存 EXT 方式の「電源投入ごとの 1 画素ずれ」が原理的に消える。データバス介入は 74HC245 ではなく **CPU バスと PPU D0-D7 の間に直列抵抗（470 Ω 程度）を入れ、RP2350 の 5 V 耐性ピンを PPU 側に直結する方式**が部品最少（抵抗アレイ 2 個）で、3.3 V 制御信号を 5 V の 74HC に入れる規格外問題も避けられる（推論）。/CS 遮断方式は $2007 の v 増分が PPU 内で起きなくなるため**成立しない**。映像は 1 ライン遅延のラインバッファ方式でシャドウパレット・強調・グレースケールを適用し、抵抗 DAC へ出す。最大の未解決リスクは、Basic/Preferred 部品に高速コンパレータが無いこと（LM393 は 300 ns 以上で画素 186 ns に間に合わない）と、2C02 の入力が 3.3 V 駆動を確実に受けるかの実証。

### Cited Findings
- EXT 出力内容: 「Setting bit 6 causes the PPU to output the lower four bits of the palette memory index on the EXT pins for each pixel.」「EXT output for transparent pixels is not a backdrop color as normal, but rather entry 0 of that background sliver's palette」「When rendering is disabled, EXT output is always index 0」— [PPU programmer reference（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_programmer_reference.xhtml)。EXT 出力は /PCLK で動く DLatch を通る — [Breaking NES pads.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/pads.md)（第2パスノートで確認済み）
- /RST は PPU の「clock divider, video phase generator, scanline/pixel counters, and the even/odd frame toggle」を初期化し、PPUCTRL/PPUMASK/PPUSCROLL を 1 フレームの間 0 に保つ — [PPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml)。CPU の分周器は reset の影響を受けない — [NESdev Wiki: User:Fiskbit](https://www.nesdev.org/wiki/User:Fiskbit)（ユーザページ、第2パス既出）
- 既存 EXT 方式の 1 画素ずれ（Fiskbit）、Lava RGB は FIFO で ext4 と ext0-3 を揃えた — 第2パス `rgb_round2_details.md` §1/§3 の出典（[t=26258](https://forums.nesdev.org/viewtopic.php?t=26258), [lava-rgb-kit](https://github.com/v5100v5100/lava-rgb-kit)）
- 「writing to the internal palette range (3F00-3FFF) will not assert /WR」— [PPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml)（→パレット書込みは PPU 外部の VRAM バスから観測できない。CPU 側の盗聴が必須）
- グレースケール = 色値 AND $30、強調は他 2 成分を暗くする、パレット読出しは 2C02G/H と PAL のみで「developers should not rely on reading from palette RAM」— [PPU registers（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_registers.xhtml)
- $2005/$2006 の 1 回目/2 回目ラッチは「only remembers the order of access (1 or 2), but not the register number」、$2002 読出しでリセット — [Breaking NES regs.md](https://raw.githubusercontent.com/emu-russia/breaks/master/BreakingNESWiki_DeepL/PPU/regs.md)
- 2C02 の映像出力レベル（75 Ω 終端時）: blank/黒 $1D=312 mV、$20=1100 mV、sync 48 mV（第2パス §6 の [NTSC video](https://www.nesdev.org/wiki/NTSC_video)）。PPU ピン 21 は PNP エミッタフォロワ（2SA937／代替 2N3906、エミッタ 300 Ω→+5 V）のベースを直接駆動 — [PPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml)。kevtris のエミッタ実測 black 1.300 V、L3 hi 2.743 V、sync 0.781 V — [forum t=2113](https://forums.nesdev.org/viewtopic.php?t=2113)（第2パス既出）
- タンタルコンデンサは「connected directly from PPU pin 20(-) to 22(+) on the Famicom, or from pin 20(-) to 40(+) on the front-loading NES」（4/8 画素幅の縦縞ノイズ対策）— [PPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml)
- 部品: JLCPCB の Basic/Preferred に「LM393 より速いコンパレータ」は無い（LM393 C7955 のみ）、0603×4 470 Ω 抵抗アレイ C25510 は Basic — `parts_class_reverification.md`（JLCPCB API 全件照会）。LM393 は 1.3 µs（5 mV OD）/ 300 ns（TTL 入力）— [TI LM393](https://www.ti.com/lit/ds/symlink/lm393.pdf)（第2パス既出）
- 秋月の高速コンパレータ（2026-11-10 表示）: ADCMP600BRJZ-R2 ¥830（応答 4 ns、2.5〜5.5 V、SOT23-5、在庫 220）— [秋月 130362](https://akizukidenshi.com/catalog/g/g130362/)、LTC6752HS5 ¥750（1.2 ns、2.45〜3.5 V、オープンドレイン）— [秋月 130361](https://akizukidenshi.com/catalog/g/g130361/)、LM319M 5 個 ¥50（同ページの関連商品表示）。LM319 は 80 ns（±15 V、5 mV OD）— [TI LM119/LM319](https://www.ti.com/lit/ds/symlink/lm119.pdf)（第2パス既出）
- 74HC245（TI）: VIH 3.15 V @VCC 4.5 V（4.2 V @6 V）、tpd 21 ns typ / 26 ns max(−40〜85 °C) @4.5 V、ten 46/58 ns、tdis 40/50 ns — [TI SN74HC245](https://www.ti.com/lit/ds/symlink/sn74hc245.pdf)
- 74HC14（TI）: VT+ 1.55〜3.13 V @4.5 V（2.1〜4.2 V @6 V）、VT− 0.9〜2.45 V @4.5 V、tpd 12 ns typ / 31 ns max @4.5 V — [TI SN74HC14](https://www.ti.com/lit/ds/symlink/sn74hc14.pdf)
- RP2350 FT ピン: VIH min 2 V / max 5.5 V（IOVDD 3.3 V 給電時）、VIL max 0.8 V、VOH min 2.62 V — RP2350 Datasheet Table 1683（`pico2_platform_verification.md` でも確認）

### Inferences（推論）— 共通方針
1. **クロックとリセットを RP2350 が握る**（§3 で詳述）: PIO が 21.5 MHz を出し、同じ PIO 時間軸で PPU /RST を特定のクロックエッジで解除する。M2 を観測して PPU /RST 解除時刻を決めれば CPU/PPU アラインメントも固定（4 通りのうち 1 つ）。EXT と VOUT の相対遅延は固定値になり、試作時に 1 回校正すれば以後不変（PPU 品種ごとに確認が要る）。
2. **データバス介入は直列抵抗方式**（§2(d) の比較参照）。
3. **映像は 1 ライン遅延**: 取込みと出力は同じ PIO クロック領域なので、FIFO 溢れ・ドリフトは起きない。

### (a) EXT0-3＋スプライト/BG ビットの画素毎取込み
| 信号 | 方向 | RP2350 ピン | 備考 |
|---|---|---|---|
| EXT0-3（PPU pin14-17） | PPU→RP2350 | FT ×4 | 1 kΩ 直列＋10 kΩ プルダウン（入力モード時に backdrop=0 を保証。TinyNES と同じ 10k）。PPU VOH≈4 V は FT 入力で可 |
| SPR（スプライト/BG 比較器出力） | 比較器→RP2350 | ×1 | 比較器は高速品（ADCMP600 等）か、要検証の代替（下記） |
| （任意）ALE（PPU pin39） | PPU→RP2350 | FT ×1 | /RST 解除後の PCLK 位相の自己確認用。ALE は「stays high for one PPU cycle」 |

- PIO SM「CAP」: 129 MHz で 24 命令/画素。ライン開始（タイミング SM からの IRQ）で起動し、`in pins, 5` → `in null, 3` を 24 命令周期で繰り返し、autopush 32 bit（4 画素/word）→ DMA でラインバッファへ。サンプル位相は 7.75 ns 刻みで可変（画素中央に置く）。
- 第5ビット（スプライト判定）は VOUT に乗るのが EXT より数画素遅い（VOUT は 1 画素遅延＋CB の D-Latch 連鎖＋比較器遅延）。同じ SM で同時刻に取り、ファームでビット列を固定画素数ずらして合わせる。遅延量は §2 共通方針 1 により固定。
- 比較器の候補（推論、§7 の実験で決める）:
  - (i) ADCMP600（秋月 ¥830、4 ns、5 V 可）: 前例（Lava = LMV7219+TLV3502、NESRGB v5 = TLV3502 相当）と同じ速度帯。手はんだ（SOT23-5）。
  - (ii) LM319（秋月 5 個 ¥50、80 ns@5 mV OD）: 本用途は 0.7 V 級の大オーバードライブなので実効遅延は短くなる見込みだが、オープンコレクタ出力の立上りが RC 律速。遅延そのものは位相設定で吸収できるので、問題は**立上り/立下りの遅延差**が画素幅（186 ns）に比べ十分小さいか — 実測が必要。
  - (iii) ディスクリート: PNP エミッタフォロワ（S8550 / MMBT3906）で PPU ピンを受け、抵抗分圧で RP2350 の入力閾値（VIL 0.8 V〜VIH 2.0 V の間）か 74HC14 に入れる。閾値が個体・温度でばらつくため、PWM＋RC で閾値（バイアス）を調整できる形にする。**最も安いが最も不確実**。
  - PPU ピン 21 の推定レベル: エミッタ実測 − VBE ≒ 黒 0.65 V、白 2.1 V、sync 0.15 V（推論：kevtris のエミッタ電圧から PNP の VBE≈0.65 V を引いた値。ピン直の実測は無い → **未確認**）。黒/白の差 ≈1.4 V で、比較器の閾値は 1.3〜1.5 V 付近。
- PPU に書く固定パターン（推論）: BG 16 エントリ = $0F（黒、blank と同電位）、スプライト 12 エントリ（$3F11-13/15-17/19-1B/1D-1F）= $20（白）。$3F10/14/18/1C は $3F00/04/08/0C のミラーなので BG 側（$0F）を書く。sync は黒より低いので、同期分離（任意）は別の遅い比較器（LM393、Basic）で可。強調・グレースケールは PPU 側では 0 に置換し（§2(e) と同じ手段）、VOUT を常に 3 値（sync/黒/白）に保つ。

### (b) シャドウパレット変換と抵抗 DAC 出力（1 ライン遅延ラインバッファ）
| 信号 | 方向 | ピン数 | 備考 |
|---|---|---|---|
| R2-0, G2-0, B2-0 | RP2350→DAC | 9 | 3.3 V 出力。非 FT ピン（RP2350B の GPIO40-47 など）でよい |
| CSYNC | RP2350→バッファ→JAMMA | 1 | JAMMA は負極性 TTL（High ≥3.5 V 推奨: `jamma_electrical_details.md`）。3.3 V 直出しは不足 → NPN（MMBT3904/S8050, Basic）で 5 V にプルアップして反転出力、または 74HCT 系 |
| （任意）VOUT 同期比較器 | 比較器→RP2350 | 1 | LM393（Basic）で sync tip を分離。自前カウンタの照合用 |

- 処理: ライン n で取り込んだ 341 画素（実際には表示 256＋ボーダー）を、ライン n+1 の間にコア 1 が変換し、ライン n+2 の H 同期から出力 SM「OUT」が 24 命令/画素で `out pins, 9` する（コア処理の締切が 1 ライン=63.5 µs で大きな余裕）。
- 変換: idx = (spr<<4)|ext。(ext&3)==0 なら idx=0（backdrop）。c6 = shadow[idx]（6 bit）。PPUMASK のグレースケールなら c6 &= $30。強調 3 bit と合わせて 512 エントリ LUT → 9 bit RGB。1 画素あたり C で 8〜12 命令程度、INTERP の表引きアドレス生成を使えばさらに減る。256 画素×12 命令 ≈ 3,100 サイクル/ライン（129 MHz で 1 ライン 8,190 サイクル）→ 1 コアの約 40%（推論・概算）。
- $2001（強調・グレースケール）の途中変更: バス盗聴側が「書込み時のドット位置」を付けて記録し（PIO 時間軸は PPU と同期しているのでドット位置は正確に分かる）、変換時に該当画素から切替える。
- 同期: H/V 同期は RP2350 自身の PIO カウンタで生成（PPU の /RST を自分で解除するので H/V 位相は既知）。奇数フレームのドットスキップ（レンダリング有効時にプリレンダーラインが 1 ドット短い）は、盗聴している $2001 の表示有効ビットで模擬。1 ライン遅延にしても同期は「画像を 1 ライン下にずらす」だけで、モニタ上の影響はない。
- DAC: JAMMA 側の目標は「開放 3.0 V（白）、出力インピーダンス 100〜150 Ω、DC 結合」（`jamma_electrical_details.md` §結論）。3.3 V GPIO の 3 bit 重み付け抵抗（例: 合成 ≈120 Ω になる 210/420/840 Ω 級）で、2 kΩ 負荷時 ≈3.1 V になる計算（推論、E 系列への丸めは設計時）。
- 色数の制約: 3-3-3 は 2C03 の DAC 値（各 ch 3 bit）をそのまま出せるが、2C02 風パレット（pally 等）は 3 bit/ch では粗い。4-4-4 にすると +3 ピン。

### (c) アドレスレジスタ（t/v）と書込みトグル（w）の追跡
| 信号 | 方向 | ピン数 |
|---|---|---|
| PPU 側 D0-D7（直列抵抗の PPU 側） | 双方向（普段は入力） | 8（FT） |
| A0-A2（PPU RS0-2） | 入力 | 3（FT） |
| R/W | 入力 | 1（FT） |
| PPU /CS（デコーダ出力） | 入力 | 1（FT） |

- PIO SM「SNOOP」: `wait 0 pin /CS` → クロック同期なので「M2 立上りから n マスタークロック後」の決め打ち時刻（M2 立下りの約 60 ns 前）で `in pins`（CPU の ÷12 分周器はリセットされず位相が電源投入ごとに不定なので、M2 の位相は最初の /CS↓（=M2↑＋デコーダ遅延）か M2 自体を一度観測して決める — 推論）（D8＋A3＋R/W=12 bit）→ push。DMA かコア 0 が FIFO を処理し、$2000（t の NT ビット、増分 +1/+32、bit6）、$2002 読（w=0）、$2005/$2006（t, w、2 回目で v=t）、$2007（読/書で v += 1 or 32）、$2001（マスク）を模擬。
- **置換の先読み**: SM「SUBST」が次の $2007 アクセスで駆動すべき値を即座に知る必要がある。コアは v が変わるたびに「次の $2007 書込みが palette か、BG/スプライトどちらか」を計算し、FJOIN_RX_GET の RX FIFO 記憶レジスタ（SM から 1 命令でランダム読出し可）に書いておく。連続する PPU アクセスの最短間隔は通常 4 CPU サイクル（STA abs; STA abs）≈2.2 µs で、コアの更新（数百 ns）に余裕がある。最短 1 サイクル（RMW 命令の二重書込み、DMC DMA による $2007 二重読出し）では間に合わない可能性 → 既知の限界として扱う（推論）。
- 既存品と同じ限界: レンダリング中の $2007 アクセスによる v の特殊増分（Codemasters）、backdrop override は EXT に出ない。ただし本構成は PPU のドット位置を正確に知っているので、将来ファームで「レンダリング中の v 更新」を模擬する余地はある（推論）。
- パレット読出し（$2007 で $3F00-$3FFF を読む）: PPU 側の実パレットは固定パターンなので、ゲームは改変値を読み戻す。直列抵抗方式では PPU が PPU 側ネットを直接駆動するため、RP2350 が読出し値を差し替えることはできない（推論）。Wiki が「should not rely on reading from palette RAM」とし、2C02G より前の PPU には機能自体が無いので、影響は限定的（推論）。

### (d) 実 PPU のパレットを「BG 暗・スプライト明」に保つ方法の比較
| 方式 | 追加部品 | 仕組み | タイミング | 主なリスク | 判定（推論） |
|---|---|---|---|---|---|
| **D1: 直列抵抗インタポーザ**（CPU D0-7 —R— PPU D0-7、RP2350 は PPU 側に直結） | 470 Ω×8（0603×4 アレイ C25510 Basic ×2） | 置換する書込みの間だけ RP2350 が PPU 側を駆動（抵抗が CPU 側との衝突電流を制限） | /CS↓ から約 20〜50 ns で駆動開始（同期器 0〜2＋数命令）、/CS↑ 後 20〜30 ns まで保持。M2 High 349 ns に対し大きな余裕 | ① 2C02 入力が 3.3 V を High と受けるか（TTL 閾値と仮定されるが未測定）② 衝突電流 3.3 V/470 Ω≈7 mA/本（RP2350 は 12 mA 設定、IOVDD 合計 100 mA 以内）③ PPU 読出し（$2002/$2004/$2007）が R×バス容量（推定 30〜50 pF → τ≈14〜24 ns）だけ遅れる | **第一候補**。部品最少、Basic のみ |
| D2: 74HC245 インタポーザ | 74HC245（Preferred）＋方向/OE 制御 | CPU 側 A、PPU 側 B。置換時は OE を切り RP2350 が B 側を駆動 | tpd 26 ns、ten 58 ns、tdis 50 ns（max, 4.5 V）。OE 切替が /CS↓ 直後に間に合う必要 | ① RP2350 の 3.3 V で 5 V の 74HC の OE/DIR を駆動すると VIH 3.15 V(@4.5 V)〜約 3.5 V(@5 V) を満たさない（規格外）→ 74HCT245（Extended）が必要 ② それでも置換データは RP2350 が 3.3 V で B 側を駆動するので D1 の①は解消しない ③ PPU 読出しの方向切替タイミング | 部品が増えて D1 の主リスクも残る。**D1 が NG のときの予備**（74HCT245 を使用） |
| D3: /CS 遮断（パレット範囲の $2007 書込みで PPU の /CS を出さない） | 74HC08 等 1 個 | PPU にパレット書込みを見せない | /CS 生成路にゲート 1 段（〜20 ns） | **PPU 内の v が +1/+32 されず、以後の VRAM アクセス先が実機とずれる**。$2000 bit6 は「書込みを見せた上でビットを変える」必要があり遮断では実現不可 | **不成立** |
| D4: PPU への独自書込み挿入（RP2350 がバスマスタとして PPU レジスタに書く） | PPU 側の RS/R/W//CS も分離する抵抗かバッファ | CPU が PPU を触らないサイクルに RP2350 が PPU に書く | CPU サイクルの空きを見つける必要 | 複雑。PPU の v/w を余計に動かす | 不採用 |
| D5: パレット改変なしで第5ビットを推定（BG 色 P[i] とスプライト色 P[16+i] の比較を VOUT の輝度で） | 多値比較器 | PPU は通常色 | — | 同輝度・異色相で判別不能（第1パス既出） | 不完全 |

- MMC5 は CPU バス上の $2000（bit5 スプライトサイズ）と $2001（bit3-4 の表示有効）への書込みを盗聴する:「The MMC5 listens to writes to PPUMASK ($2001)」「The MMC5 only listens to the fully decoded address $2001」— [NESdev Wiki: MMC5（ミラー）](https://nesdev-wiki.nes.science/wikipages/MMC5.xhtml)
- D1 の注意（推論）: D1 では RP2350 が駆動するのは PPU 側だけで、CPU 側は CPU の値のまま（CPU が Low を出していれば CPU 側の電圧は 7 mA×CPU 出力抵抗ぶん浮くだけ）なので MMC5 には実際の値が見える。

### (e) PPUCTRL bit6 の強制
- D1 の上で、SUBST SM が「/CS=0, R/W=0, A2-0=000」を検出したら **D6 のみ** 3.3 V を駆動（他のビットは CPU の値が抵抗経由でそのまま届く）。必要部品は D1 の抵抗だけ（推論）。同じ仕組みで $2001 の bit0（グレースケール）と bit5-7（強調）を PPU 側で 0 に置換すれば、VOUT は 3 値に保たれる（§2(a)）。
- PIO 実装例（推論）: `wait 0 gpio CS` → `mov pc, pins`（IN_COUNT=4 で {R/W,A2,A1,A0} の 16 分岐ジャンプ表）→ 該当分岐で `mov pins, …`／`mov pindirs, …` → `wait 1 gpio CS` → 数命令後に `mov pindirs, null`。/CS↓ から駆動開始まで約 5 命令（129 MHz で約 40 ns、同期器込みで約 55 ns）。

### 構成案まとめ（推論）
- **案 A（推奨）: RP2350B（48 GPIO）1 個**。§4 の表で 38〜41 本を使用し 7〜10 本余る。PIO 12 SM のうち 8〜9 SM、命令は 3 ブロック計 96 のうち 60 前後（概算）。
- **案 B: Pico 2 ×2**。Pico A＝クロック/リセット/映像（EXT・比較器・RGB・CSYNC）、Pico B＝バス盗聴・置換・パッド応答・JAMMA I/O。両者は別クロック領域なので、B→A のイベント（パレット書込み・$2001 変化）は SPI/UART などで送り、A が受信時刻のドット位置で適用する（$2001 の画面途中変更は数十画素の位置ずれが起こり得る）。B の置換判断は B 内で完結するので PPU への改変タイミングは影響を受けない。

### Gaps
- 2C02 の D 入力・CLK 入力の VIH/VIL: **未確認**（TinyNES が 3.3 V クロックで動作している事実（§3）は傍証）。
- EXT と VOUT の遅延差（画素数）、ブランキング中の EXT 値: **未確認**（試作で測る）。
- PIO プログラムの実際の命令数・SM 数は机上概算。

---

## 3. クロック生成（RP2350 で 21.477272 MHz を作れるか）

### Takeaway
Pico 2 の 12 MHz 水晶から整数比で作れる最も近い周波数は **21.500000 MHz（+1058 ppm）**（clk_sys 129 MHz ÷6、FBDIV=86 or 129）。150 MHz ÷7 = 21.428571 MHz（−2268 ppm、デューティ 4:3）も可能。分数分周なら平均は合わせられるが 1 クロック（6.7〜7.8 ns）の周期ジッタが乗る。RGB モニタ経路（色副搬送波を使わない）では +1058 ppm は無害（ライン 15.762 kHz、フレーム 60.16 Hz、音程 +1.8 セント）で、Hi-Def NES も CPU/PPU を約 0.15% 下げて製品化している。ただしこの周波数ではコンポジット映像の色は出ない（副搬送波が +3.8 kHz ずれる）。**Pico 2 モジュールは XIN が基板上の 12 MHz 水晶に接続済みなので、外部 21.477 MHz を PLL 基準にして RP2350 を PPU に同期させる構成は（モジュール改造なしでは）取れない**。RP2350 をクロック源にするのが Pico 2 で唯一の完全同期構成である。

### Cited Findings
- PLL: 「( FREF / REFDIV ) × FBDIV / ( POSTDIV1 × POSTDIV2 )」、「minimum reference frequency ( FREF / REFDIV ) is 5 MHz」「oscillator frequency ( FOUTVCO ) must be in the range 750 MHz-1600 MHz」「feedback divider ( FBDIV ) must be in the range 16-320」「the post dividers POSTDIV1 and POSTDIV2 must be in the range 1-7」、12 MHz 水晶では FBDIV 63〜133。「Jitter decreases as VCO frequency increases」— RP2350 Datasheet §8.6.3, §8.6.3.1
- 「On both PLLs, the FREF (reference) input is connected to the crystal oscillator’s XIN (XI) input.」— §8.6.1。外部クロックは「Use XIN and one of GPIN0-GPIN1」、XIN 入力は 50 MHz まで（「the on-chip PLLs can synthesise higher frequencies from the XIN input」）、GPIN0/1 は「can provide system and peripherals clocks, but is limited to 50 MHz」— §8.1.2.4。XIN は矩形波入力時 VIH 0.65×IOVDD（Table 1686）
- 「The PLLs can drive clocks at their maximum frequency as long as the reference clock is accurate to 1000ppm」— §8.1.2（PLL 節）
- クロック出力 GPOUT0-3 は GPIO13/15/21/23/24/25 などの CLOCK 機能（GPIO 機能表）。クロック生成器は「clock source multiplexing, division, duty cycle correction」を持つ — §8.1.3。Pico 2 では GPIO23（SMPS PS）、GPIO24（VBUS sense）、GPIO25（LED）が基板内部用 — Pico 2 Datasheet p.8（`pico2_platform_verification.md`）→ ヘッダに出る GPOUT は GPIO13/15/21。
- Pico 2 の水晶: Abracon ABM8-272-T3、12 MHz、「The crystal has a 30 ppm frequency tolerance」— [Hardware design with RP2350 §4](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf), Pico 2 Datasheet
- USB ブートモードは既定で 12 MHz 入力に依存（OTP で上書き可）— RP2350 Datasheet Table 1686 の Note
- Hi-Def NES: 「The NES is very very slightly underclocked to do this, around 0.15%.」「small enough that it isn't humanly detectible」(2014-11-13)、「both CPU and PPU are clocked the same so no games should break」(2014-11-20)、FPGA 生成クロックは「slightly jittery (due to how the clock generation works)」(2015-07-12) — [Hi-Def NES スレッド アーカイブ t12019](https://archive.nes.science/nesdev-forums/f9/t12019.xhtml)
- TinyNES（量産・出荷済み製品）は 3.3 V の MEMS 発振器 SIT2001BC-S2-33N-21.477270 → クロックバッファ PL133-37TC → 30 Ω（R3-R5）で CPU と PPU の CLK を駆動（BOM に 3.3 V LDO AP2127N-3.3）— [TinyNES Main Board BOM](https://raw.githubusercontent.com/loglow/TinyNES/main/Main%20Board/TinyNES_Main_Board_BOM.csv)。2A03 を 3.3 V CPLD で駆動して動作した報告 — [archive t4698](https://archive.nes.science/nesdev-forums/f9/t4698.xhtml)（`famicom_electrical_and_pitfalls.md` 既出）
- 2A03 は NMOS のため低速（DC）クロック不可 — [emulationonline chiplab](https://emulationonline.neocities.org/systems/chiplab/experimenting-with-highspeed-chips/)（`raspberry_pi_emulation_path.md` 既出）
- 部品の入手性: 秋月に Si5351A 3ch プログラマブル周波数ジェネレーターモジュール ¥650（在庫あり）[秋月 110679](https://akizukidenshi.com/catalog/g/g110679/)、TC74HCU04AP（DIP）¥30 [秋月 111328](https://akizukidenshi.com/catalog/g/g111328/)。秋月のキーワード「21.47727」検索では該当商品が表示されなかった（2026-11-10）。JLCPCB には 21.47727 MHz 水晶 C5289705（Extended、在庫 2,648）、74HCU04 は実質在庫なし（SN74HCU04N 79 個のみ）— `parts_class_reverification.md`

### Inferences（推論・計算）
**12 MHz 基準から整数分周で得られる候補（全探索の上位、/tmp/p2f/scripts/pll.py）**
| PLL 設定 | clk_sys | PIO 分周 k | 出力 | 誤差 | 備考 |
|---|---|---|---|---|---|
| FBDIV=129, VCO 1548 MHz, POSTDIV 6×2 | 129.000 MHz | 6 | 21.500000 MHz | **+1058 ppm** | 推奨（VCO 高めで低ジッタ、デューティ 50%） |
| FBDIV=86, VCO 1032 MHz, POSTDIV 4×2 | 129.000 MHz | 6 | 21.500000 MHz | +1058 ppm | 同上（VCO 低め） |
| FBDIV=125, VCO 1500 MHz, POSTDIV 5×2 | 150.000 MHz | 7 | 21.428571 MHz | −2268 ppm | 公称最大クロック。デューティ 4:3 |
| FBDIV=113, VCO 1356 MHz, POSTDIV 3×3 | 150.667 MHz | 7 | 21.523810 MHz | +2167 ppm | 150 MHz 超（規格外） |
| （規格外）FBDIV=93, POSTDIV 2×2 | 279 MHz | 13 | 21.461538 MHz | −733 ppm | オーバークロック必須 |

- 21.4772727 MHz = 12 MHz × 1.78977…、小さな分母の有理数近似の最良が 43/24（=21.5 MHz）なので、±1000 ppm より良い整数解は規格内に無い。
- **影響（+1058 ppm の場合）**: 画素 5.375 MHz、ライン 15.762 kHz（公称 15.746 kHz）、フレーム 60.16 Hz（公称 60.10 Hz）、ゲーム速度 +0.106%、音程 +1.83 セント（1200·log2(1.001058)）。15 kHz アーケードモニタの許容（K7000 15.1〜16.8 kHz 等、`jamma_electrical_details.md`）に十分収まる。Hi-Def NES の −0.15%（約 −1500 ppm）より小さい。拡張音源もすべて M2 由来なので比例して同じだけずれる。コンポジットの色副搬送波は 3.5833 MHz（+3.8 kHz）になりテレビの色同期は外れると考えられる（RGB 専用なら無関係）。
- **ジッタ**: 整数分周なら PLL 出力のジッタだけ（RP2350 データシートに数値なし → **未確認**）。分数分周（PIO 16.8、GPOUT 16.16）で 21.4772727 MHz の平均を出すと、周期が 1 clk_sys（6.7〜7.8 ns ≈ マスター周期の 14〜17%）単位で揺れる。NMOS の 2A03/2C02 がこれに耐えるかは **未確認** で、利点（周波数の正確さ）も RGB では不要なので採らない。
- **同期の利点**: PIO が CLK を出すので、PIO 時間軸＝PPU 時間軸。EXT サンプル位相は 7.75 ns 刻み（マスター周期の 1/6）で決め打ちでき、/RST をクロック同期で解除すれば電源投入ごとに同じ（/RES 入力の内部同期段の有無は **未確認** → ALE で毎回自己確認、§2(a)）。
- **欠点**: RP2350 が止まると CPU/PPU も止まる（書換え・ウォッチドッグ再起動時）。NMOS は低速クロック不可なので、クロック停止前後は必ず /RST を保持する（RP2350 の GPIO はリセット時プルダウン → /RST ラインを Low に引く設計にしておけば、ブート中は自動的にリセット保持）。
- **3.3 V 振幅で NMOS の CLK を駆動**: TinyNES（3.3 V バッファ＋30 Ω）が実例。RP2350 GPIO（12 mA、高速スルー）＋30〜33 Ω 直列で CPU・PPU を別ピン（同じ SM のサイドセットで同時変化）から駆動するのが妥当（推論）。

**他方式との比較**
| 方式 | 周波数精度 | ジッタ | 部品 | RP2350 との関係 | 判定（推論） |
|---|---|---|---|---|---|
| ① RP2350 PIO 整数分周（129 MHz÷6） | +1058 ppm（±30 ppm の水晶誤差を含めても 1.1×10⁻³） | PLL ジッタのみ | 0（直列抵抗のみ） | 完全同期 | **推奨** |
| ② RP2350 分数分周 | 平均 0 ppm | 6.7〜7.8 ns の周期ジッタ | 0 | 同期 | 不採用 |
| ③ 74HC04（Preferred）＋21.47727 MHz 水晶のピアス発振 | 水晶精度（数十 ppm） | 低 | 水晶（Extended）＋C×2＋R×2＋74HC04 | 非同期：PIO がクロックのエッジを待って画素を数える（同期器で ±1 clk_sys=±6.7 ns の揺れ）| 可。ただし発振用途はアンバッファ 74HCU04 が定石で、74HC04 は要評価。原 Famicom 互換の周波数が必要な場合の予備 |
| ④ 発振器モジュール（SG-8002 等 21.47727 MHz） | ±50 ppm 程度 | 低 | モジュール 1（Basic 外） | 非同期、または **自作 RP2350 基板なら XIN に入れて PLL で ×6=128.86 MHz** に同期 | RP2350B 自作基板（案 A）なら有力。USB ブートは 12 MHz 前提なので OTP 設定か別系統が要る |
| ⑤ Si5351A モジュール（秋月 ¥650） | 実用上ほぼ 0 ppm | 仕様値未確認 | モジュール＋I²C | 非同期（Pico 2）、自作基板なら XIN に供給可 | 「珍しい部品」寄り。① で足りるので不要 |

- 非同期（③④⑤ を Pico 2 と組む）場合の EXT 取込み: 21.477 MHz を FT ピンに入れ、PIO が `wait 1 pin`/`wait 0 pin` を 4 回繰り返して 1 画素を数え、その後 `in pins` する。150 MHz で 1 マスター周期 ≈7 命令なので可能だが、出力側（RGB）も同じく外部クロックのエッジに従わせる必要があり、±6.7 ns の揺れが出力画素エッジに乗る（画素幅の 3.6%、CRT では不可視と推定）。

### Gaps
- RP2350 PLL の出力ジッタ値: データシートに数値なし **未確認**。
- 2A03/2C02 が受け入れるクロック周波数の範囲・ジッタ耐性・CLK 入力の閾値: 一次資料なし **未確認**（Hi-Def NES の −0.15% と「jittery」クロックでの動作、TinyNES の 3.3 V 駆動は傍証）。
- 秋月での 21.47727 MHz 水晶・発振器の取扱い: キーワード検索で見つからず（型番違いで登録されている可能性は残る）**未確認**。

---

## 4. GPIO 予算（実チップモード）

### Takeaway
実チップモードに必要な信号は最小構成でも **約 37 本、推奨構成で 40 本前後**。Pico 2（26 本、うち 5 V 耐性 23 本）1 枚では不足し、**RP2350B（48 GPIO、うち FT 40 本）1 個**か、**Pico 2 ×2（映像側／バス側に分割）**が必要。秋月は RP2350B / RP2354B のチップ単体（¥220 / ¥280）を扱うが、今回の検索では RP2350B 搭載モジュールは見当たらなかった。QFN-80（0.4 mm）の手はんだは現実的でないので、RP2350B 案は JLCPCB の Extended 部品実装（Basic のみの方針から外れる）が前提になる。

### Cited Findings
- Pico 2: 「exposes 26 of the 30 possible RP2350 GPIO pins … GPIO0 to GPIO22 are digital only and GPIO 26-28 are able to be used either as digital GPIO or as ADC inputs」、GPIO26-29 は IOVDD+約 300 mV まで — Pico 2 Datasheet p.14（`pico2_platform_verification.md`）
- RP2350A: GPIO0–25 が Digital IO (FT)、GPIO26-29 は ADC 兼用。RP2350B: GPIO0–39 が FT、GPIO40–47 が ADC 兼用 — RP2350 Datasheet Table 1674（同上）。PIO は「limited to 30 GPIOs for RP2350A」、各 PIO ブロックは GPIOBASE で 32 本の窓を選ぶ — §11.1, §11.1.1
- 秋月（2026-11-10）: Raspberry Pi Pico 2（SC1631）¥990、在庫 1,462 — [秋月 129604](https://akizukidenshi.com/catalog/g/g129604/)。RP2350B（SC1510、QFN80、GPIO 48）¥220、在庫 242 — [秋月 130370](https://akizukidenshi.com/catalog/g/g130370/)。RP2354B（SC1512、2 MB フラッシュ内蔵、QFN80）¥280、在庫 115 — [秋月 131441](https://akizukidenshi.com/catalog/g/g131441/)。RP2350A 実装基板（秋月 AE-QFN60-7X7-0.4、GPIO 30）¥450 — [秋月 131106](https://akizukidenshi.com/catalog/g/g131106/)。秋月の「RP2350」検索結果には他に Seeed XIAO RP2350、Tiny 2350、Plasma 2350、W5500-EVB-Pico2 等が出たが、RP2350B 搭載モジュールは無かった。
- コントローラ: OUT0 は 4021 の P/S、CLK は「normally held high, and becomes low during a read of $4016 or $4017」— [Standard controller（ミラー）](https://nesdev-wiki.nes.science/wikipages/Standard_controller.xhtml)。/OE1・/OE2 は $4016/$4017 読出し時にアクティブ — [CPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/CPU_pinout.xhtml)。ファミコン本体では 368 が D0-D2（$4016）／D0-D4（$4017）だけを駆動し上位はオープンバス — `famicom_hardware.md`
- JLCPCB では RP2350A（C42411118）が Extended — `parts_class_reverification.md`（RP2350B の分類は本調査では **未確認**）

### Inferences（推論）— GPIO 表
| 群 | 信号 | 本数 | 5 V 入力（FT 必須） | 備考 |
|---|---|---|---|---|
| バス盗聴・置換 | PPU 側 D0-D7 | 8 | ○ | 双方向。パッド応答と共用 |
| | A0-A2, R/W, PPU /CS | 5 | ○ | |
| パッド応答 | /OE1, /OE2, OUT0 | 3 | ○ | RP2350 が PPU 側 D0（必要なら D1-D4）を抵抗経由で CPU バスへ出す。M2 は不要（クロックを自前で持つので位相既知） |
| 映像入力 | EXT0-3 | 4 | ○ | |
| | SPR 比較器 | 1 | — | |
| | （任意）ALE | 1 | ○ | 位相自己確認 |
| | （任意）同期比較器 | 1 | — | |
| クロック・リセット | CLK（CPU/PPU を別ピンにするなら 2） | 1〜2 | — | |
| | PPU /RST, CPU /RST | 2 | — | 5 V 側入力。3.3 V で駆動（VIH は TTL と仮定、要検証）。CPU /RST は RC で兼用すれば 1 |
| 映像出力 | RGB 3-3-3 | 9 | — | 非 FT ピン可 |
| | CSYNC | 1 | — | 外付け NPN で 5 V 化 |
| JAMMA 入力 | 74HC165 ×4（UDLR,A,B,Start ×2P＝14、Coin1/2・Service・Test＝4、DIP 8 → 26 入力） | 3 | — | 165 を 3.3 V 給電、プルアップも 3.3 V |
| JAMMA 出力 | 74HC595（Basic）でコインカウンタ×2・ロックアウト等（CLK は 165 と共用） | 2 | — | ULN2003A（Basic）で駆動 |
| 書換え | USB | 0 | — | 専用ピン |
| **合計** | | **最小 37 ／推奨 40〜41** | FT 必須 21〜22 本 | |

| 選択肢 | 使える GPIO | 判定 |
|---|---|---|
| Pico 2 ×1 | 26（FT 23） | **不足**（最小 37）。RGB を 2-2-2 にし任意信号を全部削っても 33 で足りない |
| Pico 2 ×2 | 52（FT 46） | **可**。A: CLK 2, /RST 2, EXT 4, SPR 1, ALE 1, RGB 9, CSYNC 1, リンク 3 = 23。B: D 8, A0-2/RW/CS 5, /OE1/OE2/OUT0 3, JAMMA 5, リンク 3 = 24（FT 16）。両者のクロック領域が違う点が設計上の負担（§2 案 B） |
| RP2350B ×1 | 48（FT 40） | **最も素直**。7〜11 本余り、オーバーレイや 4-4-4 RGB に回せる。ただし QFN-80 の実装を JLCPCB（Extended）に頼る |

- Pico 2 ×2 のうち A は PPU にクロックを出す側でなければならない（EXT 取込みと同期させるため）。B は非同期でよい（/CS などのストローブ駆動で動作）が、B が使う「M2 から n クロック後」の決め打ちは使えないので、B のスヌープは「/CS↓ を同期器経由で検出 → 固定命令数待ち → サンプル」とする（150 MHz で ±6.7 ns の揺れ。窓 250 ns に対して問題なし）。

### Gaps
- RP2350B 搭載の既製モジュール（Pimoroni Pico Plus 2 等）の国内入手性・JLCPCB での RP2350B / RP2354B の分類と在庫: 本調査では **未確認**（WebSearch 上限のため）。

---

## 5. 5 V インタフェースと電源シーケンス

### Takeaway
5 V の NMOS 出力（VOH≈4 V）は RP2350 の FT ピン（IOVDD 給電中は 5.5 V まで、VIH min 2.0 V）に直結できる。逆方向（RP2350 3.3 V 出力→2C02/2A03 入力）は「TTL 閾値と仮定」されるだけで未測定だが、TinyNES の 3.3 V クロック駆動が傍証。3.3 V 出力で 5 V 給電の 74HC を駆動するのは規格外（74HC245 VIH 3.15 V@4.5 V、74HC14 VT+ max 3.13 V@4.5 V → 5.0 V では約 3.5 V）。最大の電源シーケンス上の危険は「RP2350 の IOVDD が無いのに 5 V 信号が FT ピンに来る」状態で、FT ピンはこのとき 3.63 V までしか許されない。RP2350 がクロック源なら、RP2350 起動前は CPU/PPU が動かずバスは静止するが、静的に High の出力やプルアップは残るので、**5 V 系（CPU/PPU/カート）の電源を Pico の 3V3 確立後に P-MOS で投入する**のが確実（推論）。

### Cited Findings
- FT ピン: 「very little current flows into the pin whilst it is below 3.63 V and IOVDD is 0 V. Additionally, they will tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V.」、VPIN_FT 絶対最大は IOVDD=0 V で 3.63 V — RP2350 Datasheet Table 1673, 1680（`pico2_platform_verification.md` で逐語確認済み）
- RP2350 GPIO の電気特性: VIH(FT) 2〜5.5 V（IOVDD 3.3 V）、VIL ≤0.8 V、VOH ≥2.62 V（2/4/8/12 mA 設定）、プルアップ 32〜86 kΩ、プルダウン 36〜113 kΩ、「Maximum Total IOVDD current 100 mA」（全 GPIO の吐出し合計）— Table 1683
- リセット直後の GPIO は「Output buffer is high-impedance … Pulled low」— §9.3（`pico2_platform_verification.md`）
- RP2350-E9（A2 ステッピングの入力リーク、内蔵プルダウンが効かない）は A3/A4 で修正 — `raspberry_pi_emulation_path.md` §5
- 2A03/2C02 VOH ≈ 4 V（lidnariq）、入力は TTL 閾値と仮定（lidnariq）— §1 の出典
- 74HC245 VIH 3.15 V @4.5 V、74HC14 VT+ 1.55〜3.13 V @4.5 V / 2.1〜4.2 V @6 V — TI データシート（§2 の出典）
- 既存品の変換方法: Lava RGB は SN74LVC4245A ×2（双方向 5 V↔3.3 V）と SN74LVC541A ×2 — 第2パス §2。pico6502 は 74AHCT244/245 — `raspberry_pi_emulation_path.md` §5

### Inferences（推論）
| 信号 | 方向 | 接続 | 理由 |
|---|---|---|---|
| A0-2, R/W, /CS, /OE1, /OE2, OUT0, EXT0-3, ALE | 5 V→RP2350 | FT ピン直結＋直列 1 kΩ（保護） | VOH 4 V < 5.5 V、VIH 2 V を満たす |
| PPU 側 D0-D7 | 双方向 | FT 直結（CPU 側とは 470 Ω で分離） | 置換時に RP2350 が 3.3 V で駆動 |
| CPU/PPU CLK | RP2350→5 V | 直結＋30〜33 Ω | TinyNES 前例 |
| PPU /RST, CPU /RST | RP2350→5 V | 直結（Low 保持のため外付けプルダウン 10 kΩ） | 入力閾値は TTL と仮定（要確認）。RP2350 起動前も Low |
| CSYNC | RP2350→JAMMA | NPN＋5 V プルアップ（反転） | 3.3 V では TTL High 3.5 V 推奨を満たさない |
| RGB | RP2350→DAC | 抵抗 DAC 直出し | 5 V 不要 |
| 74HC165/595 | 3.3 V 給電 | 直結 | 3.3 V 給電なら 3.3 V ロジック同士 |
| 比較器（ADCMP600 等） | 5 V or 3.3 V | 3.3 V 給電にすれば出力を RP2350 に直結 | 入力は PPU VOUT（〜2 V 程度） |

- **電源シーケンスの危険**: ① 投入時、JAMMA 5 V が先に立ち、Pico の RT6150 が 3V3 を出すまでの数 ms（**未計測**）に、5 V 側の静的 High（例: 外付けプルアップ、NMOS 出力の High）が FT ピンに 3.63 V 超を掛ける。② 切断時は Pico の昇降圧 SMPS（VSYS 1.8 V まで動作）が 5 V 系より長く 3V3 を保つ方向なので比較的安全（推論）。③ RP2350 の書換え・再起動時はクロックが止まる → /RST を Low に保持。
- **対策（部品最少）**: Pico の 3V3 を検出して P-MOS（SI2301 / AO3401A、Basic）で CPU/PPU/カートの 5 V を入れる（ゲートは 2N7002、Basic）。加えて FT ピンへの直列抵抗（1 kΩ）で故障電流を制限。5 V プルアップを FT ピンに付けない（/IRQ 等 RP2350 が見る線のプルアップは 3.3 V へ）。
- 74HC を使うなら 3.3 V 給電（165/595/14 は 2〜6 V 動作）にし、5 V 系との境界には置かない。5 V 系の境界にどうしてもロジックが要るなら 74HCT（Extended）か LVC（例 SN74LVC4245A、Preferred）。

### Gaps
- Pico 2 の 3V3 立上り時間（VSYS 5 V 投入から）: **未計測**。
- FT ピンに IOVDD 無給電で 3.63〜5 V が掛かったときの電流（直列抵抗で制限した場合の許容）: データシートに記載なし **未確認**。

---

## 6. 画面上のオーバーレイ（残り時間、「INSERT COIN」）

### Takeaway
1 ライン遅延のラインバッファ方式なら、出力前のバッファに文字を書き込むだけでオーバーレイでき、**追加ハードウェアは不要**（推論）。コストはフォント（8×8 で 96 文字 ≈ 768 B）と、文字のあるラインで数百〜千サイクル程度の CPU 時間。半透明（下地を暗くして文字を載せる）も LUT で可能。ゲーム画面全体を止めて「INSERT COIN」画面を出すことも、RP2350 が映像出力を握っているので可能。

### Cited Findings
- 該当する前例（RP2350 で 2C02 映像にオーバーレイ）は見つからなかった（第1/第2パスの探索結果、本パスでは WebSearch 上限のため追加探索なし）。
- 出力経路の性能根拠: PIO の DPI/VGA 出力は「PIO can sustain 360 Mb/s during the active scanline period when running from a 48 MHz system clock」— RP2350 Datasheet §11.1

### Inferences（推論）
- 実装: コア 1 がライン n+1 を変換した後、オーバーレイ領域（例: 上端 8〜16 ライン、32 桁）について glyph ビットを読んで画素を上書き。256 画素中 文字部分のみ処理すれば 1 ライン ≈ 300〜1,000 サイクルで、変換処理（≈3,100 サイクル）と合わせても 1 ライン予算 8,190 サイクル以内。
- 実時間パイプライン（ラインバッファ無し）でも、出力直前に「文字マスク」を OR する処理を挟めば可能だが、締切が 1 画素単位になるのでラインバッファ方式より厳しい。
- 色数: 3-3-3 なら文字色・影色を自由に選べる。
- ゲーム側への影響はゼロ（PPU には何も書かない）。タイムプレイ時の残り時間表示・アトラクト時の「INSERT COIN」点滅とも可能。

### Gaps
- 実装例が無いので CPU 時間は概算。

---

## 7. リスク一覧（順位付け）と最小の検証実験

### Takeaway
最重要リスクは ① スプライト/BG ビットを安価な部品で 186 ns 画素に追従して判定できるか、② 2C02 が RP2350 の 3.3 V 駆動（D 線・CLK・/RST）を確実に受けるか、③ 直列抵抗インタポーザで置換値が PPU に確実にラッチされ、CPU 側に害がないか、の 3 つ。いずれも「ドナー Famicom の CPU/PPU＋Pico 2 1 枚＋ブレッドボード級の試作」で 1〜2 週間程度の実験により go/no-go を出せる（推論）。

### Inferences（推論）
| 順位 | リスク | 最小実験（作るもの） | 測るもの | Go / No-go |
|---|---|---|---|---|
| 1 | **スプライト/BG 判定**（Basic/Preferred に高速比較器なし。LM393 は 300 ns 以上で不可） | 2C02 を載せた小基板＋Pico 2（クロック・/RST・EXT・比較器入力）。テスト ROM で「BG=$0F、スプライト=$20」の固定パレット、1 画素幅・2 画素幅のスプライト縦線を表示。比較器を (i) ADCMP600、(ii) LM319（5 V 単電源）、(iii) PNP フォロワ＋74HC14 / RP2350 入力直、の 3 通り差し替え | RP2350 PIO をロジアナにして 129 MHz（7.75 ns）で EXT と比較器出力を同時取得。1 画素スプライトの比較器パルス幅と位置、立上り/立下り遅延差、ノイズ（タンタル C の有無） | Go: 1 画素幅が常に検出でき、サンプル点の前後に ≥40 ns の余裕、10 回の電源投入と 2 種類以上の 2C02（例 RP2C02E/G）で同じ位相。No-go: (iii)(ii) が不可なら (i) を採用（¥830/台）、(i) も不可なら方式自体を見直し |
| 2 | **3.3 V 駆動で NMOS 入力が動くか**（D6/D0-5 置換、CLK、/RST） | 実験 1 と同じ基板。CLK は RP2350 から 21.5 MHz（30 Ω 直列）、CPU も同じクロックで動かす | 数時間の連続動作、CLK 波形（ピン端）、$2000 D6 を 3.3 V で強制して EXT が出力モードになるか、パレット置換後に $2007 読出し（2C02G）で値を確認 | Go: 0〜50 °C で誤動作なし、置換値の読み戻し一致。No-go: 74HCT245/LVC4245A（5 V 出力）へ切替（D2 方式） |
| 3 | **直列抵抗インタポーザの副作用**（CPU 側電圧、PPU 読出しの遅れ、MMC5 の盗聴） | 実験 2 の基板に WRAM を載せ、通常カートと MMC5 搭載カートで動作させる | CPU 側/PPU 側 D 線の波形、$2002 読出しの立上り（τ）、置換時の CPU 側 Low レベル、WRAM テスト | Go: CPU 側 VOL ≤0.8 V、PPU 読出しデータが M2 立下り 50 ns 前までに安定。No-go: 抵抗値の変更（330 Ω など）か D2 |
| 4 | **v/w 追跡の正しさ**（ゲームによる例外: レンダリング中 $2007、RMW・DMC による 1 サイクル間隔アクセス） | ソフトのみ: エミュレータ（Mesen 等）の PPU レジスタアクセスログ＋内部 v を多数タイトルで記録し、追跡アルゴリズムをオフラインで照合 | パレット書込み時に追跡 v が実 v と一致しない件数 | Go: 不一致が既知の例外（Codemasters 等）に限られる |
| 5 | **コアの更新遅延**（次の $2007 置換値を間に合わせられるか） | Pico 2 を 2 枚使い、1 枚で 2A03 のバス波形（/CS, R/W, A, D）を擬似生成、もう 1 枚で SNOOP/SUBST を動かす | 連続 $2007 アクセス間隔 1/2/4 サイクルでの置換成功率 | Go: 2 サイクル間隔以上で 100% |
| 6 | **EXT と VOUT の相対遅延・1 画素ずれ** | 実験 1 の基板で /RST をクロック同期解除 | 20 回の電源投入で、EXT とスプライトビットの最適シフト量が不変か。ALE の位相 | Go: 毎回同じ（または ALE から自動判定できる）|
| 7 | **電源シーケンス**（FT ピンの 3.63 V 制限） | Pico 2 の VSYS 投入から 3V3 確立までの時間と、その間の 5 V 側信号を同時測定 | FT ピンの電圧/電流 | Go: P-MOS 遅延投入で 3V3 確立前の 5 V 信号が 0 |
| 8 | **GPIO 不足**（Pico 2 ×1 では不可） | 机上でピン割当表と PIO 命令数の確定 | — | 案 A（RP2350B）か 案 B（Pico 2 ×2）を確定 |
| 9 | **クロック +1058 ppm の影響** | 実験 1〜3 の基板で実ゲーム数本 | モニタの同期（15.762 kHz）、音程 | 低リスク。Go: モニタが同期 |
| 10 | **パレット読出しを使うソフト** | 対象タイトルの調査（エミュレータで $2007 のパレット読出しを検出） | 該当タイトル数 | 該当がなければ対策不要 |

### Gaps
- 上記実験は未実施。順位は公開資料に基づく筆者の判断。

---

## 既存ノートへの訂正

| # | 対象ノートと記述 | 訂正・補足 | 出典 |
|---|---|---|---|
| 1 | `rgb_from_rp2c02.md` Q5 推論「マスター 21.47727 MHz 発振器を CPU/PPU と MCU で共有（RP2040/RP2350 の **XIN に外部クロック入力**し PLL で整数倍）すれば…位相固定」 | **Pico 2 モジュールでは不可**（XIN は基板上の 12 MHz 水晶 ABM8-272-T3 に接続済み。GPIN0/1 は clk_sys に使えるが 50 MHz までで PLL の基準にならない — PLL の FREF は XIN 直結）。自作 RP2350 基板なら可能だが、×7 = 150.34 MHz は公称最大 150 MHz を 0.23% 超えるので ×6 = 128.86 MHz が規格内。Pico 2 で同期させるには**逆に RP2350 がマスタークロックを出す**（21.5 MHz、+1058 ppm） | RP2350 Datasheet §8.1.2.4, §8.6.1, Pico 2 Datasheet, Hardware design with RP2350 §4 |
| 2 | `rgb_round2_details.md` §3 推論 1「21.47727 MHz 発振器 1 個を CPU CLK・PPU CLK・RP2350（XIN 外部クロック or PIO 入力）に分配」 | 同上。Pico 2 では「PIO 入力（非同期でエッジを数える）」のみ可。完全同期は RP2350 をクロック源にする構成 | 同上 |
| 3 | `rgb_from_rp2c02.md` Q8 推奨方針「(b) Pico 2 が CPU→PPU 書込みを改変できるよう CPU–PPU 間に 74HC245 を挟む」 | 5 V 給電の 74HC245 の制御入力は VIH 3.15 V(@4.5 V)〜約 3.5 V(@5 V) で、RP2350 の 3.3 V 出力では規格外。しかも置換データ自体は RP2350 が 3.3 V で駆動するので 245 を挟んでも 3.3 V 駆動の問題は残る。**直列抵抗（470 Ω）方式の方が部品が少なく同等以上**（推論）。245 を使うなら 74HCT245（Extended）か SN74LVC4245A（Preferred） | [TI SN74HC245](https://www.ti.com/lit/ds/symlink/sn74hc245.pdf) |
| 4 | `rgb_round2_details.md` §1 推論「2C02 は NMOS で出力 High は 5V 未満…74HC（V_IH≈3.5V@5V）で受けるのはマージン不明」 | lidnariq の実測で 2A03/2C02 の VOH ≈ 4 V。5 V の 74HC（VIH 3.15 V@4.5 V）なら約 0.5〜0.85 V の余裕はある（ただし実測 1 例）。RP2350 FT 入力（VIH 2.0 V）なら十分 | [forum t=19656 p.2](https://forums.nesdev.org/viewtopic.php?t=19656&start=15) |
| 5 | `rgb_from_rp2c02.md` Q5 GPIO 概算「30〜35 本でオーバー」 | パッド応答（/OE1, /OE2, OUT0）、JAMMA 入出力（シフトレジスタ 5 本）、/RST 2 本、クロックを含めると**最小 37 本、推奨 40 本前後**。Pico 2 ×1 は不可、Pico 2 ×2 か RP2350B | 本ノート §4 |
| 6 | `rgb_from_rp2c02.md` Q5 推論「コンパレータ…高速コンパレータか、トランジスタ増幅＋74HC/74AC 入力閾値」／ `rgb_round2_details.md` §6 Gaps「JLCPCB Basic Parts に TLV3502/LMV7219 があるかは未確認」 | JLCPCB の Basic/Preferred には LM393 より速いコンパレータは無い（`parts_class_reverification.md` の全件照会）。秋月には ADCMP600（4 ns、¥830）、LTC6752（1.2 ns、3.5 V まで、¥750）、LM319M（5 個 ¥50）がある | [秋月 130362](https://akizukidenshi.com/catalog/g/g130362/), [秋月 130361](https://akizukidenshi.com/catalog/g/g130361/) |
| 7 | `rgb_from_rp2c02.md` Q7 推論「アーケード（JAMMA）モニタは 0.7 Vp-p/75Ω 入力が一般的」 | `jamma_electrical_details.md` の確認どおり、日本の JAMMA 側は正極性約 3 Vp-p・約 2 kΩ。DAC は開放 3.0 V・出力インピーダンス 100〜150 Ω を目標にする | `jamma_electrical_details.md` |
| 8 | （新規注意）PPU のタンタルコンデンサ（縦縞ノイズ対策）を「pin 20–22」に付けるのは Famicom で pin 22（/RST）が +5 V 固定だから | 本基板は PPU /RST を制御するので、**pin 20(−)–40(+)（VCC）** に付ける（NES と同じ）。pin 22 に付けると /RST の制御を妨げる | [PPU pinout（ミラー）](https://nesdev-wiki.nes.science/wikipages/PPU_pinout.xhtml) |
| 9 | `rgb_from_rp2c02.md` Q3 推論「EXT と VOUT の相対遅延は…起動時またはフレーム毎に位相を自動校正」 | RP2350 がクロックと PPU /RST を握れば位相は毎回同じになり、フレーム毎の校正は不要（初回設計時の 1 回＋ALE による起動時確認で足りる見込み）（推論） | §2 共通方針 |

---

## 付記: 計算結果（/tmp/p2f/scripts/pll.py）

- 目標: 21.4772727… MHz（= 236.25/11 MHz、315/88 MHz × 6）。探索範囲: FBDIV 16〜320 のうち VCO 750〜1600 MHz、POSTDIV 1〜7、整数分周 k 2〜16。
- 規格内（clk_sys ≤150 MHz）の最良: +1058.2 ppm（21.500000 MHz）。次点: −2267.6 ppm（21.428571 MHz、clk_sys 150 MHz ÷7）。規格外を許すと −732.6 ppm（279 MHz ÷13）が最良。

## 付記: 試行したが取得できなかった経路
- Nexperia 74HC245 データシート: Access Denied（TI 版で代替）。
- 2C02 レジスタ書込みのセットアップ/ホールド: NESdev Wiki（PPU registers / PPU pinout / programmer reference）、Breaking NES（regs.md / pads.md）、NESdev フォーラム（t=19483, t=8216 の検索要約）の 3 経路で数値なし。
- WebSearch は調査途中で上限に達したため、RP2350B モジュールの国内流通、比較器のメーカー一次データシート（ADCMP600）、PIO によるレトロ機映像取込みの前例探索は打ち切った。
