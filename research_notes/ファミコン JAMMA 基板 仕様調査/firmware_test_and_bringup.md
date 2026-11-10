# ファームウェア・シミュレーション・テストROM・実機立ち上げ機材 (第2パス, 2026-11-10時点)

対象: 既存ノート `tooling_and_mcp.md` の §5(ファームウェア/テスト)、§6(実機立ち上げ機材。出典なし)、各Gapsの穴埋め。
表記ルール: 出典URLを各行に付す。「未確認」は3経路以上試しても確認できなかった事項。「推論」は筆者の工学的推論(出典なし)。
取得方法の注記: GitHubのリリース日は `releases.atom` / `api.github.com`(WebFetch経由)で年付きで取得した。秋月電子の価格と通販在庫数は 2026-11-10 に商品ページを直接取得した値(税込)。本セッションはWebSearchの検索枠が尽きていたため、全て既知URLの直接取得で検証した。krikzz.com は bot 対策(429/403)で一部ページしか取得できなかった。

---

## 0. まとめ表 (tool / purpose / version・date / URL / 日本での入手 / 必須度)

### 0.1 ソフトウェア

| ツール | 用途 | 版 / 日付 | URL | 必須度 |
|---|---|---|---|---|
| Raspberry Pi Pico SDK | RP2040/RP2350ファーム | 2.3.1 / 2026-09-04 | https://github.com/raspberrypi/pico-sdk | 必須 |
| picotool | UF2書込・情報表示・seal | 2.3.1 / 2026-09-05(SDKが同じタグを自動でFetchContent) | https://github.com/raspberrypi/picotool | 必須 |
| pioasm | PIOアセンブラ | SDK同梱ソースからビルド(版はSDK版と同じ) | https://github.com/raspberrypi/pico-sdk/tree/master/tools/pioasm | 必須 |
| Pico SDK `PICO_PLATFORM=host` | ハード非依存ロジックをPC上で単体テスト | SDK同梱 | https://github.com/raspberrypi/pico-sdk/tree/master/src/host | 必須(コイン/タイマ論理のテスト用) |
| rp2040-pio-emulator | PIOステートマシン1個をPythonで単体テスト | PyPI 0.88.0 / 2026-08-28, Apache-2.0 | https://github.com/NathanY3G/rp2040-pio-emulator | あれば便利 |
| rp2040js | RP2040全体のJSエミュレータ(PIO/DMA実装あり) | npm 1.4.1 / 2026-10-18, MIT | https://github.com/wokwi/rp2040js | あれば便利 |
| Wokwi CLI + wokwi-ci-action | クラウドでPico/Pico 2を模擬してCI | CLI v0.29.1(「23 Oct」、年表示なし)、MIT。シミュレータ本体はクラウドサービス | https://github.com/wokwi/wokwi-cli | あれば便利(無料CIは30日で50分) |
| MesenCE | 高精度NESエミュ、ヘッドレスtest runner、Lua | 2.2.1 / 2026-06-05(2.2.0 / 2026-06-04)、GPL-3.0 | https://github.com/nesdev-org/MesenCE | 必須(ROM回帰試験) |
| FCEUX | NESエミュ、Lua | 2.7.0 / 2026-10-14(aptは2.6.5) | https://github.com/TASEmulators/fceux | 補助 |
| cc65 (ca65/ld65/cl65) | 6502 C/アセンブラ、NESターゲット | 版番号2.19(最終タグ V2.19 = 2020-11-20)、Windowsスナップショット 2026-11-08、apt 2.19-1 | https://cc65.github.io/ | 必須 |
| asm6f | 6502アセンブラ(asm6派生) | v1.6_f03 / 2025-01-27 | https://github.com/freem/asm6f | 任意 |
| NESASM CE | NESASM派生 | v3.6(日付不明) | https://github.com/ClusterM/nesasm | 任意 |
| llvm-mos-sdk | Clang系C/C++。NES NROM/CNROM/UNROM/MMC1/MMC3等 | リリース版数は未確認 | https://github.com/llvm-mos/llvm-mos-sdk | 任意 |
| neslib (clbr版) | ca65用NES関数ライブラリ | zlib、版不明 | https://github.com/clbr/neslib | 推奨(Cで書く場合) |
| nesdoug チュートリアル/ライブラリ | cc65+neslibでのNES開発解説 | — | https://nesdoug.com/ | 推奨(参考資料) |
| sigrok-cli / PulseView | ロジアナの取得とデコード | apt 0.7.2 / 0.4.2(既存ノートでの実測) | https://sigrok.org/ | 必須(ロジアナ使用時) |
| minipro | XGecu書込器のLinux用OSSクライアント | タグ12個(最新版数は未確認) | https://gitlab.com/DavidGriffith/minipro | 必須(T48使用時) |

### 0.2 テストROM

| ROM | 検証内容 | マッパ(実測) | URL | 必須度 |
|---|---|---|---|---|
| AccuracyCoin | CPU/PPU/APU等のpass/fail 147個 + DRAW 5個。実機向け | NROM(README) | https://github.com/100thCoin/AccuracyCoin | 必須 |
| instr_test-v5 rom_singles | 公式/非公式命令 | NROM 32K+8K(01-basics.nesのiNESヘッダ実測) | https://github.com/christopherpow/nes-test-roms/tree/master/instr_test-v5 | 必須 |
| ppu_vbl_nmi rom_singles | VBLフラグとNMIタイミング(PPU 1クロック精度) | NROM(01-vbl_basics.nes実測) | https://github.com/christopherpow/nes-test-roms/tree/master/ppu_vbl_nmi | 必須 |
| apu_test rom_singles | CPUから見えるAPUの挙動 | NROM(1-len_ctr.nes実測) | https://github.com/christopherpow/nes-test-roms/tree/master/apu_test | 必須 |
| cpu_timing_test6 | 命令タイミング | NROM 16K | 同上のリポジトリ | 推奨 |
| oam_stress | $2003/$2004 | NROM 32K+8K | 同上 | 推奨 |
| ppu_sprite_hit / sprite_overflow_tests | スプライト0ヒット、スプライトオーバーフロー | 未確認 | NESdev wiki Emulator tests に記載のzip | 推奨 |
| cpu_interrupts_v2 / instr_timing | IRQ/NMI、命令タイミング | MMC1(80KB / 32KB、実測) | 同上 | 任意(MMC1対応カートが必要) |
| read_joy3 / allpads | コントローラ読み取り | 未確認 | NESdev wiki | 推奨 |
| full_nes_palette | 全パレットとエンファシスの表示 | 未確認 | http://www.slack.net/~ant/nes-hacks/full_nes_palette.nes | 推奨(映像変換の色確認) |
| 240p Test Suite (NES版 240pee) | PLUGE/カラーバー/グリッド/オーバースキャン/ラグ等28項目 | UNROM(README「burn ... with an UNROM board」) | https://github.com/pinobatch/240p-test-mini | 必須(映像調整) |

### 0.3 ハードウェア (価格は2026-11-10取得)

| 機材 | 目的 | 型番・仕様 | 価格・入手先 | 必須度 |
|---|---|---|---|---|
| ロジアナ(sigrok対応) | 1.79MHzバス、5.37MHz画素、21.48MHzクロックの観測 | DSLogic Plus: 400MHz(4ch)/200MHz(8ch)/100MHz(16ch) | $149(定価$199)、dreamsourcelab.com。日本の代理店は未確認 | 必須 |
| ロジアナ(国内で即納) | 同上 | ZEROPLUS LAP-C(16128) 16ch 200M(sigrok対応を確認できたのは別型番 LAP-C(16032) のみ) | 秋月 ￥53,800 (g103081) | 代替 |
| ロジアナ(高級) | 同上 | Saleae Logic 8(100MS/s。sigrokでは「planned」で非対応) | 秋月 ￥82,800 (g108975) | 非推奨(価格が高く、sigrok非対応) |
| オシロスコープ | クロック波形、電源、アナログRGB/音声 | OWON SDS1102 2ch 100MHz / SDS1104 4ch 100MHz | 秋月 ￥39,000 / ￥45,000 | 必須(どちらか1台) |
| プローブ | — | 100MHzプローブ / 250MHzプローブ | 秋月 ￥2,000 (g100240) / ￥2,540 (g117802) | 必須 |
| ROMライター | テストカートのEPROM/Flash書込 | XGecu T48(VPP 25V、VCC 1.8–6.5V、31000+デバイス) | 国内の価格・在庫は未確認 | 必須(自作カート路線の場合) |
| フラッシュカート | 実機で任意のROMを実行 | EverDrive N8 PRO Fami(60-pin、Cyclone IV、16MB) | krikzz.com $159。国内販売店は未確認 | 必須(推奨路線) |
| スキャンコンバータ | 15kHz RGBS→HDMI | OSSC 1.8(€115〜)/ RetroTINK-4K CE($475)/ 5X-Pro($325) | 各公式通販。国内は未確認 | 必須(どれか1台、またはCRT) |
| JAMMA電源 | +5V/+12V/−5V | MEAN WELL RT-65A(5V 6A / 12V 2.8A / −5V 0.5A) | 国内価格は未確認 | 必須(筐体なしで試験する場合) |
| 電動はんだ吸取器 | DIP-40の取り外し | HAKKO FR-301(350–500℃、98W、標準ノズル N61-08 φ1.0) | 秋月 ￥22,000 (g114459, FR301-82) | 必須(ドナー基板が多い場合) |
| 手動はんだ吸取器 | 同上(低予算) | goot GS-108 / エンジニア SS-03 | 秋月 ￥1,150 / ￥2,580 | 代替 |
| ICソケット | CPU/PPUの差し替え | 丸ピン40P / ZIF 40P 600mil | 秋月 ￥110 (g100034) / ￥250 (g111744) | 必須(試作) |
| ESD対策用品 | NMOSチップの保護 | リストストラップ 442B-01、導電スポンジ、静電シールド袋 | 秋月 ￥1,150 (g114463)、￥170 (g109709) | 必須 |
| Pico 2 / Pico | 試作用MCU | Raspberry Pi Pico 2 (SC1631) / Pico | 秋月 ￥990 (g129604、通販在庫1462) / ￥800 (g116132) | 必須 |

---

## 1. Raspberry Pi Pico SDK・picotool・pioasm・RP2350ステッピングとE9

### Takeaway
Pico SDKの最新は 2.3.1 (2026-09-04)、picotoolの最新は 2.3.1 (2026-09-05)。RP2350対応は SDK 2.0.0 (2024-08-08) から始まり、2.1.0 で A0/A1 が非対応になった。RP2350-E9(入力有効時のGPIOリークで、内部プルダウンが効かない)が該当するのは **A2のみで、A3で修正済み**。データシートでは A4 が「Production version」だが、2026年末に市販される Pico 2 や LCSC の RP2350A が A4 かどうかは販売ページに記載がなく未確認。

### Cited Findings
| 項目 | 内容 | 出典 |
|---|---|---|
| pico-sdk 2.3.1 | published_at 2026-09-04T22:38:41Z。「Some synchronization primitives on RP2350 also suffered from busy-wait instead of sleep issues」等を修正 | https://api.github.com/repos/raspberrypi/pico-sdk/releases |
| pico-sdk 2.3.0 | 2026-07-03。「RP2350's XIP cache can now be used as additional SRAM via `pico_use_xip_cache_as_ram()`」 | 同上 |
| pico-sdk 2.2.0 | 2025-07-29。「the workaround for erratum RP2350-E10」。`picotool seal` で LOAD_MAP を付与 | 同上 |
| pico-sdk 2.1.1 | 2025-02-19 | 同上 |
| pico-sdk 2.1.0 | 2024-11-25。「RP2350 A0/A1 silicon are no longer supported」 | 同上 |
| pico-sdk 2.0.0 | 8月8日(年はHTML一覧の並び順から2024と判断)。「adds support for the new RP2350 and for compiling RISC-V code in addition to Arm」 | https://github.com/raspberrypi/pico-sdk/releases |
| picotool | 2.3.1 = 2026-09-05(SDK 2.3.1に合わせたバグ修正)、2.3.0 = 2026-07-03(`bdev`、`uf2 combine`)、2.2.0-a4 = 2025-08-14(「RP2350 A3 and A4 chip revision display」)、2.2.0 = 2025-07-29 | https://api.github.com/repos/raspberrypi/picotool/releases |
| picotoolの入手 | 未インストールの場合、SDKのCMakeが `https://github.com/raspberrypi/picotool.git` を `GIT_TAG ${PICO_SDK_VERSION_STRING}` でFetchContentする | https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpicotool.cmake |
| pioasmの入手 | `${PICO_SDK_PATH}/tools/pioasm` のソースを ExternalProject_Add でビルド。版は `-DPIOASM_VERSION_STRING=${PICO_SDK_VERSION_STRING}` | https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpioasm.cmake |
| RP2350 の版歴 (Table 7) | A0/A1「Internal development」、A2「Initial release」、A3「Internal development, samples, and limited production」、A4「Production version」 | RP2350 Datasheet (build 01/10/2026) https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-3-rp2350-datasheet.pdf §1.4 |
| E9の内容 | 「Increased leakage current on Bank 0 GPIO when pad input is enabled」「Affects RP2350 A2」。未定義領域で約120µAを吐き出してピンを約2.2Vに保持し、内蔵プルダウンでは引き下げられない。「8.2 kΩ or less」の低インピーダンスで引けば回避でき、プルアップは機能する | 同データシート Appendix D.5.1 |
| E9の修正 | A3のハードウェア変更:「Fix ... RP2350-E9 ... The pad circuit is modified to eliminate the erroneous leakage path through the input buffer.」 | 同 Appendix C.2.1 |
| A4 | 「This stepping has no hardware changes.」(変更はブートROMのみ: E18修正、E24緩和、E25修正)。CHIP_ID.REVISION=0x3、ブートROM版バイト=0x4 | 同 Appendix C.3 |
| 刻印 | 部品番号は「RP2350」+「A」(QFN-60)/「B」(QFN-80)+パッケージ版「0」+ダイステッピング「A2」「A3」「A4」 | 同 §14.4 Package markings |
| 5V耐性 | 「GPIOs are 5 V-tolerant (powered) and 3.3 V-failsafe (unpowered)」。FTピンは「tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V」 | 同 §1 と Table 1673 |
| 市販品のステッピング | 秋月の Pico 2 (SC1631、発売日2024/09/18、￥990) と LCSC C42411118 (RP2350A、QFN-60、在庫3080、$1.18@1個) は、どちらもステッピングの記載がない | https://akizukidenshi.com/catalog/g/g129604/ , https://www.lcsc.com/product-detail/C42411118.html , jlcsearch API |

### Inferences
- (推論) E9の影響はA2だけなので、2026年末に新たに調達する品がA3/A4であれば、内蔵プルダウンを前提にした入力回路(コインスイッチ等)も使える。ただしA2の在庫品が混ざる可能性は排除できない。**入力は外付けプルアップ(アクティブLow)で設計**しておけば、A2/A3/A4のどれでも問題ない。JAMMAのコイン/ボタン入力はもともとアクティブLowとプルアップが慣例なので、設計上の追加コストはない。
- (推論) 起動時に `picotool info -a` を使うか、ファームで CHIP_ID.REVISION とブートROM版バイトを読んでログに出せば、実機のステッピングを確認できる。
- (推論) FTピンの5V耐性は「IOVDDに通電中」が条件。Famicom側の5Vが先に立ち上がる電源シーケンスでは、非通電時に3.63Vを超える電圧がかからないよう注意が必要(Famicomの5Vバスに直結するなら直列抵抗かバッファを推奨)。ADC兼用ピンがFTかどうかはピン表で個別に確認する必要がある(未確認)。

### Gaps
- 2026年11月時点で流通している Pico 2 / RP2350A のステッピング(A2/A3/A4)は、秋月、LCSC、Raspberry Pi の製品ページ、Pico 2データシート(build 03/07/2026)のどれにも記載がない → **未確認**。PCN 28 の本文は未取得。

---

## 2. ハードウェア無しでの PIO/Pico ファーム試験

### Takeaway
PIOの命令単位のロジックは、rp2040-pio-emulator(Python、ステートマシン1個)か rp2040js(MIT、pio.ts/dma.ts あり)を使えばローカルで単体試験できる。システム全体は Wokwi(クラウド、要トークン)でCIに載せられる。ただし **Wokwiが模擬するのはコア1つだけ**で、Pico 2でもArmコア1つのみ、RP2350固有のPIO命令は未対応。RP2040版WokwiのDMAは「PIO用のみ」。ハードに依存しないロジックは、SDK公式の `PICO_PLATFORM=host` でPC上にビルドするのが最も確実。どの方法でもアナログ映像出力や実バスとの位相関係は検証できないので、最終確認にはロジアナが必須。

### Cited Findings
| ツール | できること | できないこと/制限 | 出典 |
|---|---|---|---|
| SDK host platform | 「selected by `PICO_PLATFORM=host`」「extremely useful for testing and debugging higher level application code」。pico-host-sdl を使えば pico_multicore、タイマ、scanvideo を追加できる | 「sufficient for programs that don't access hardware directly」(ハードを直接触るコードは不可) | https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/host/README.md |
| rp2040-pio-emulator | Python、Apache-2.0。単体テスト、クロック数の計測、GPIOの時系列可視化。JMP/IN/PUSH/PULL/SET/WAIT に対応 | OUT(EXEC先)と MOV の一部が未実装、IRQ命令は非対応、「a single State Machine is emulated and not an entire PIO block」、IN用ピンセットは非対応、`PULL IFEMPTY`/`PUSH IFFULL` は閾値を無視 | https://github.com/NathanY3G/rp2040-pio-emulator , PyPI `rp2040-pio-emulator` 0.88.0 (2026-08-28) |
| rp2040js | 「A Raspberry Pi Pico Emulator in JavaScript」。MIT。src/peripherals に pio.ts, dma.ts, usb.ts, timer.ts 等がある | 「the SSI peripheral required for flash writing is not implemented yet」。RP2350対応の記述はない | https://github.com/wokwi/rp2040js , npm 1.4.1 (2026-10-18) |
| Wokwi (Pi Pico, RP2040) | GPIO、PIO(PIO Debuggerあり)、UART、I2C/SPI(マスタのみ)、PWM、ADC、GDB | 「Only one core is simulated」。DMAは「Only for the PIO peripheral」。SSIは最小限 | https://docs.wokwi.com/parts/wokwi-pi-pico |
| Wokwi (Pi Pico 2, RP2350) | PIOブロック3つ、DMA 16ch全部、PWM 12スライス、TIMER0/1、POWMAN、SHA-256、ADC、GDB | Armコア1つだけ(2つ目のArmとHazard3 RISC-Vは模擬しない)。RP2350固有のPIO命令はない。HSTXは記載なし | https://docs.wokwi.com/parts/board-pi-pico-2 |
| Wokwi CI | `wokwi/wokwi-ci-action@v1`、シークレット `WOKWI_CLI_TOKEN`(「starts with `wok_`」)、`expect_text` で合否判定 | 無料:「Free users: 50 minutes」(過去30日の合計)。1セッションは「Free and Hobby users: 5 minutes」 | https://docs.wokwi.com/wokwi-ci/github-actions , https://docs.wokwi.com/wokwi-ci/getting-started |
| Wokwi 料金 | Community €0、Hobby €5.6/月(fast build 100分)、Hobby+ €8.1/月、Pro €20/seat/月(「2000 monthly CI minutes」、「For commercial projects」) | 無料プランは public プロジェクトのみ | https://wokwi.com/pricing |
| Wokwi CLI | MIT。`wokwi-cli [dir]`、`--timeout`(既定30秒)、`--expect-text`、`wokwi-cli mcp`(実験的MCP) | シミュレーションはWokwiのサーバ側で動く(トークン必須) | https://github.com/wokwi/wokwi-cli |

### Inferences
- (推論) 本プロジェクトで一番重要なのは「PIOがFamicomのM2やPPU /RD・/WR等の外部信号に正しく同期するか」だが、どのシミュレータも外部ピンへの任意波形入力やナノ秒精度の位相検証には向かない(クロック数単位なら rp2040-pio-emulator で可)。現実的なのは次の3層: PIO命令ロジックは rp2040-pio-emulator のユニットテスト、コイン/タイマ/クレジットの状態機械は host platform のユニットテスト、統合試験は実機とロジアナ。
- (推論) Wokwi はクラウド依存で、無料枠は30日で50分、模擬コアは1つ。マルチコア(コア1で映像変換する等)を前提にしたファームのCIの主軸にはしない。rp2040js はローカルで動きMITだが、RP2350には対応していない(記述なし)。
- (推論) Pico 2(RP2350)固有のPIO命令(Wokwi未対応)を使う部分は、実機でしか検証できない。

### Gaps
- rp2040js の PIO/DMA の精度と RP2350 対応予定、Wokwi のPIOサイクル精度(タイミング精度の公式記述)、Wokwi CLI v0.29.1 のリリース年は未確認(atomとHTMLのどちらも年が表示されず、GitHubページ上は「23 Oct」)。

---

## 3. 自作ROMの自動回帰試験に使える NES/Famicom エミュレータ

### Takeaway
Mesen 2 の後継は MesenCE (nesdev-org) で、2.2.0 (2026-06-04) と 2.2.1 (2026-06-05) をリリースしている。`--testRunner` でヘッドレス実行でき、Luaの `emu.stop(code)` に渡した値がプロセスの終了コードになる(既定タイムアウト100秒、`timeout=秒` で変更)。FCEUX 2.7.0 (2026-10-14) は `-lua` でスクリプトを起動でき `emu.exit()` もあるが、ヘッドレス実行やGUI無効化のオプションは公式ドキュメントに記載がない。

### Cited Findings
- SourMesen/Mesen2 の最終リリースは 2.1.1 (2025-07-06)。— https://github.com/SourMesen/Mesen2/releases.atom
- MesenCE のリリース: Mesen 2.2.0 = 2026-06-04T10:36:12Z、2.2.1 = 2026-06-05T10:18:39Z(iNESのホットフィックス)。リリースノートには、Mesen は「MesenCE, a Community Edition」になり今後の開発はすべて新フォークで行う、という趣旨の記載がある。2.2.0 では「11 more AccuracyCoin tests passing」。macOS/Linux版は「SDL2 must be manually installed first」。— https://github.com/nesdev-org/MesenCE/releases , https://github.com/nesdev-org/MesenCE/releases.atom
- MesenCE README: Linux x64 / Linux ARM64 の開発ビルドあり(SDL2が必要)、GPL v3、「Copyright (C) 2014-2026 Sour, 2026 contributors」。— https://github.com/nesdev-org/MesenCE
- Test runner(ソースで確認): ヘルプ文は「--testRunner [lua script] [rom file] - Runs a Lua script in headless mode (use emu.exit(...) to stop execution)」。スイッチは `timeout=`、`novideo`、`noaudio`、`noinput`。既定値は `TestRunnerTimeout = 100` で、`while(sw.ElapsedMilliseconds < timeout * 1000)` のループで待つ。停止すると `EmuApi.GetStopCode()` の値を返し、タイムアウト時は -1。— https://raw.githubusercontent.com/nesdev-org/MesenCE/master/UI/Utilities/CommandLineHelper.cs , https://raw.githubusercontent.com/nesdev-org/MesenCE/master/UI/Utilities/TestRunner.cs
- **ヘルプ文とAPIが食い違っている**: Lua APIに登録されている関数は `stop`(`LuaApi::Stop` が `_emu->SetStopCode(stopCode)` を呼ぶ)で、`exit` は登録されていない。実際に使うのは `emu.stop(code)`。— https://raw.githubusercontent.com/nesdev-org/MesenCE/master/Core/Debugger/LuaApi.cpp
- MesenCE のLua関数(抜粋): read/write/read16/readWord、addMemoryCallback、addEventCallback、getScreenBuffer、getPixel、takeScreenshot、setInput/getInput、createSavestate/loadSavestate、getState/setState、getCpuCycleCount、getMasterClock、reset、stop、log、getRomInfo。— 同 LuaApi.cpp
- 旧Mesen(1)のドキュメントにも同様の説明がある:「Mesen.exe --testrunner MyGame.nes MyTest.lua」で「maximum speed」で実行し、`emu.stop()` の終了コードが返る。— https://www.mesen.ca/docs/apireference.html(注: これはMesen 1系のドキュメント。memTypeの名前などはMesen 2/CEと異なる)
- FCEUX: 2.7.0 = 2026-10-14、2.6.6 = 2023-08-27、interim-build の更新は 2026-11-10。— https://github.com/TASEmulators/fceux/releases.atom
- FCEUX の起動オプション: `-lua`(「Loads a Lua script on startup」、例 `fceux -lua memwatch.lua`)。ヘッドレス、no-GUI、音声/映像オフのオプションはページに記載がない。— https://fceux.com/web/help/CommandLineOptions.html
- FCEUX のLua: `memory.readbyte`、`emu.frameadvance`、`emu.exit`(「closes FCEUX」)、`emu.speedmode`("normal","nothrottle","turbo","maximum")、`emu.getscreenpixel`、`gui.savescreenshotas`、`joypad.set`。— https://fceux.com/web/help/LuaFunctionsList.html
- apt の fceux 2.6.5 は Qt5/SDL2/OpenGL に依存するGUIアプリ。— コンテナ実測 `apt-cache show fceux`

### Inferences
- (推論) CIでは MesenCE を `--testRunner test.lua game.nes timeout=30` で回す。Luaのフレーム終端コールバックでRAMや画面バッファ(getScreenBuffer)を検査し、`emu.stop(0/1)` で終わらせる。Linuxで完全ヘッドレス(ディスプレイ無し)で動く可能性は高い。test runnerはAvalonia UIを経由しない `TestRunner.Run` 経路を通るため。ただしコンテナでの動作は未実測。
- (推論) FCEUX でも Xvfb 等の仮想ディスプレイ下で `-lua` と `emu.exit()` を使えば回帰試験はできるが、MesenCE より手間がかかる。

### Gaps
- MesenCE の Linux ビルドで `--testRunner` がX無しで動くかの実測、2.2.1 より新しいリリースの有無、GitHubの★数は未確認。Lua の `eventType` / `memType` の値一覧は enum 定義ファイルを読んでおらず未確認。

---

## 4. 実機検証用テストROM群と実機での走らせ方

### Takeaway
再生した基板を実機で検証する中核は3つ: **AccuracyCoin(NROM、147テスト、実機向け)**、blargg の **rom_singles(各テストが NROM 32K+8K)**、映像調整用の **240p Test Suite(UNROM)**。blargg のまとめ版ROM(all_instrs.nes、ppu_vbl_nmi.nes、apu_test.nes、cpu_interrupts.nes 等)は **MMC1(マッパ1、80〜256KB)** なので、NROMの自作カートでは走らない(実測)。最も手間が少ないのは EverDrive N8 PRO Fami($159)、最も安いのは自作NROMカートとROMライターの組み合わせ。

### Cited Findings
- NESdev wiki Emulator tests の主要エントリ:
  - nestest(kevtris): 「start at $C000」で起動し既知のログと比較する、エミュレータ向け。
  - instr_test-v5: 公式・非公式命令。結果を $6000 にも書く。
  - instr_timing、cpu_timing_test6、cpu_interrupts_v2。
  - ppu_vbl_nmi: 「to one PPU clock」の精度。
  - ppu_sprite_hit、sprite_overflow_tests、oam_stress。
  - blargg_ppu_tests(palette RAM 等)、full_nes_palette(画面表示)。
  - apu_test、blargg_apu_2005、dmc_tests。
  - read_joy3(DMC DMAによる読み取り破損を含む)、allpads(tepples)。
  - リンク切れが多く、christopherpow/nes-test-roms にアーカイブされている。
  — https://www.nesdev.org/wiki/Emulator_tests
- blargg instr_test-v5 の結果の出し方:「print information on screen」に加え、ビープ音で結果を出す(0=pass、1=fail、2以上=理由コード)。$6000 にステータスを書く($80=実行中、$81=リセット要求)。$6004以降にテキスト。— https://raw.githubusercontent.com/christopherpow/nes-test-roms/master/instr_test-v5/readme.txt
- iNESヘッダの実測(本調査で取得したファイル)。出典は https://github.com/christopherpow/nes-test-roms (raw取得)。

  | ファイル | マッパ | PRG | CHR |
  |---|---|---|---|
  | all_instrs.nes / official_only.nes / ppu_vbl_nmi.nes | 1 | 256KB | — |
  | apu_test.nes | 1 | 128KB | — |
  | cpu_interrupts.nes | 1 | 80KB | — |
  | instr_timing.nes | 1 | 32KB | — |
  | oam_stress.nes | 0 | 32KB | 8KB |
  | cpu_timing_test.nes | 0 | 16KB | — |
  | rom_singles/01-basics.nes、01-vbl_basics.nes、1-len_ctr.nes | 0 | 32KB | 8KB |
- AccuracyCoin:「A large collection of NES accuracy tests on a single NROM cartridge」。— https://github.com/100thCoin/AccuracyCoin
  - テスト数: pass/fail 147個 + DRAW 5個。
  - 想定機:「designed for an NTSC console with an RP2A03G CPU and RP2C02G PPU」。リビジョンが異なる機体では一部を自動でスキップする。
  - 成功コードで、US NES と Famicom のコントローラ読み方の違いや、コンポジットPPUとRGB PPUを区別できる。
  - 結果は画面に PASS/FAIL とエラーコードで表示され、Startで全テストを実行する。ライセンスは MIT。
- 240p Test Suite NES版: 最新は v0.23 (2023-03-03)、GPL v2以降。README には「burn ... to a cartridge with an UNROM board」「Load 240pee.nes onto a PowerPak or EverDrive-N8」とある。— https://github.com/pinobatch/240p-test-mini/releases.atom , https://github.com/pinobatch/240p-test-mini/tree/master/nes , https://raw.githubusercontent.com/pinobatch/240p-test-mini/master/nes/src/helppages.txt
  - 項目: PLUGE, Gradient color bars, SMPTE color bars, Color bars on gray, Color bleed, Hanover bars, Monoscope, Convergence, Gray ramp, Solid color screen, IRE, Sharpness, Chroma crosstalk, Overscan, Safe areas, CPU clock speed, Shadow sprite, Stopwatch, Timing and reflex test, Hill zone/Vertical/Grid scroll test, Full screen stripes, Backlight zone test, Input test, Sound test, Audio sync test, MDFourier。
- EverDrive N8 PRO Fami: $159、色は White/Transparent/Blue。— https://krikzz.com/our-products/cartridges/n8-pro-fami.html (2026-11-10 にcurlで取得。在庫表示はテンプレート上「In stock / Out of stock」の両方の文字列があり判定できない)
  - 主な仕様:「Cyclone IV FPGA」「16MB of ROM memory. 8MB for PRG and 8MB for CHR」「256K of battery ram」「USB port for development」「Wide range of supported mappers」。
  - 互換機については「cannot guarantee compatibility with all of them」とある。
- krikzz のサイトマップには、旧製品の `legacy/edn8fami.html`(EverDrive N8 のFamicom版)と `famicom-to-nes-adapter` がある。— https://krikzz.com/sitemap.xml
- EverDrive N8 PRO の開発資料(MIT): https://github.com/krikzz/edn8-pro-pub
- オープンハードのFamicomカートPCB:
  - ponchick/FC-DiscreteCart: ジャンパで NROM/CNROM/GNROM/BNROM/AMROM/ANROM/AOROM/UNROM/UOROM を切り替える。NROM/CNROM では U1 に「DIP-28」または「DIP-32」のROMを使える。KiCadファイル、CERN-OHL-P-2.0。— https://github.com/ponchick/FC-DiscreteCart
  - Gumball2415/NES-Famicom-Cartridge-PCBs: `nrom-board` / `unrom-board`、TAPR OHL。— https://github.com/Gumball2415/NES-Famicom-Cartridge-PCBs
  - ClusterM/coolgirl-famicom-multicart: CPLD EPM1270T144 で多数のマッパを実装。「designed for ordering from JLCPCB」、4層1.2mm、GPL-3.0。書込は famicom-dumper-writer を使うか、「Non-soldered flash memory chip can be written using programmer」。— https://github.com/ClusterM/coolgirl-famicom-multicart
  - ClusterM/famicom-dumper-writer: STM32F103ZET + EPM3064。COOLGIRL/COOLBOY/UNROM-512 のフラッシュカートに書き込める。GPL-3.0。— https://github.com/ClusterM/famicom-dumper-writer
  - Keitark/fc-rom-vomitter: ESP32-S3 が Wi-Fi で受け取ったNROMイメージを CY62128 SRAM 2個に転送し、74LVC245 でバスを切り替える。6層、1.2mm、60本の金端子、JLCPCB形式のBOM/CPLを同梱、KiCad、ハードはCC BY-SA 4.0。**READMEに「Do not insert an untested board into a Famicom」とあり、実機検証は済んでいない**。— https://github.com/Keitark/fc-rom-vomitter
- メモリ部品の入手性:
  - 秋月(2026-11-10): パラレルFlashで見つかったのは SST39VF040-70(4Mbit、**2.7〜3.6V**、TSOP32、￥150、g112066)だけ。5V品(SST39SF0x0、27C256/512、28C256、62256)は「39SF040」「28C256」「62256」「27C256」「EPROM」で検索しても該当なし。SRAM は M68AF127B 1Mb が ￥70 (g101083)。— https://akizukidenshi.com/catalog/g/g112066/ ほか
  - LCSC(jlcsearch API): SST39SF040-55-4I-NHE-T(PLCC-32、C632847、在庫12、$5.46@1個、Extended)、SST39SF010A-55-4C-NHE-T(PLCC-32、C632838、在庫22)、IS62C256AL-45ULI-TR(SOIC-28、C14323、在庫2548、$2.89、Extended)。AS6C1008、62256、AT27C512、M27C512、CY62256 は該当0件。— https://jlcsearch.tscircuit.com/components/list.json?search=SST39SF040 等
- XGecu: T48 は USB 2.0HS、NAND最大256Gb、VPP最大25V、VCC 1.8–6.5V、対応デバイス31000+、「In Production」。TL866II Plus の Status は「T48 Replacement」。TL866A/CS は2018年2月に出荷を停止しており、市場に出回っている品は偽物だとメーカーが告知している。— http://www.xgecu.com/en/
- minipro(Linux向けOSS):「Compatibility with TL866CS, TL866A, TL866II+, T48, and T56 from XGecu」。— https://gitlab.com/DavidGriffith/minipro/-/raw/master/README.md

### Inferences
- (推論) 実機検証の推奨手順:
  1. AccuracyCoin(NROM)で CPU/PPU/APU をまとめて判定する。
  2. 失敗した項目に対応する blargg rom_singles(NROM)で詳しく調べる。
  3. 240p Test Suite(UNROM)で映像変換回路とスキャンコンバータを調整する。
  4. allpads/read_joy3 で、JAMMA入力からコントローラへの変換を確認する。
- (推論) NROMの自作カートなら PRG 32KB(27C256相当、または SST39SF010 の一部)と CHR 8KB で足り、blargg rom_singles と AccuracyCoin が載る。UNROM版(74HC161+74HC32)にすれば240p Test Suiteも載る(UxROMの論理は §5 参照)。
- (推論) 5V系のパラレルROMは秋月になく、LCSCも PLCC-32 の SST39SF0x0 が少量在庫しているだけ。DIPのEPROM/Flashは中古品や海外通販に頼ることになり、「手はんだ部品は秋月」というルールに合わない。**テスト用途なら EverDrive N8 PRO Fami を1台買う方が部品調達のリスクが低い**。
- (推論) fc-rom-vomitter の方式(MCUがSRAMにROMを書き込んでからバスを明け渡す)は、本基板のPicoがカートスロット経由でテストROMを供給する「自己試験モード」を設計する際の参考になる。ただし同プロジェクトは実機で検証されていない。

### Gaps
- EverDrive N8 PRO Fami の国内販売店、円価格、在庫: krikzz の販売店ページ(429/bot対策で取得不可)、Amazon.co.jp(503)、Stone Age Gamer(404)を試した → **未確認**。旧 EverDrive N8 Famicom版の価格・在庫も未取得。
- XGecu T48 の国内価格(秋月とスイッチサイエンスには無く、aitendoは検索結果を判別できなかった) → **未確認**。
- ppu_sprite_hit / sprite_overflow / read_joy3 / allpads / 240pee のマッパは未実測。

---

## 5. 専用アーケードゲームを書くためのツールとマッパ選定

### Takeaway
cc65 の版番号は 2.19 のまま(最終タグ V2.19 = 2020-11-20)だが開発は続いており、Windowsスナップショットは 2026-11-08 に更新された。Ubuntu の apt は 2.19-1。Cで書くなら cc65 + neslib(解説は nesdoug)、アセンブラなら ca65 か asm6f。製造が最も簡単なマッパは **NROM(マッパ0、ROM 2個だけでロジック不要)**。容量が必要なら **UxROM(マッパ2、74HC161+74HC32)**。

### Cited Findings
- cc65: 「A portable 6502/65c02/65c816 assembler, linker, and C compiler」。Linuxでは git clone して `make` するか、openSUSE Build Service の deb/rpm を使う。Windowsは「current cc65 snapshot」。— https://www.nesdev.org/wiki/Tools , https://cc65.github.io/getting-started.html
- cc65 の版: master の version.c は `VER_MAJOR 2U` / `VER_MINOR 19U`、タグ V2.19 = 2020-11-20、SourceForge の cc65-snapshot-win64.zip の更新は 2026-11-08。— https://raw.githubusercontent.com/cc65/cc65/master/src/common/version.c , https://github.com/cc65/cc65/releases.atom , https://sourceforge.net/projects/cc65/files/
- asm6f: v1.6 (modifications v03) = 2025-01-27。illegal opcode と NES 2.0ヘッダに対応。— https://github.com/freem/asm6f/releases.atom , https://www.nesdev.org/wiki/Tools
- NESASM CE: 「nesasm CE v3.6 - a 6502 assembler with specific NES support」。Linuxでは `make all`。— https://github.com/ClusterM/nesasm
- llvm-mos-sdk の NES ターゲット: `mos-nes-action53-clang`、`-cnrom-`、`-gtrom-`、`-mmc1-`、`-mmc3-`、`-nrom-`、`-unrom-`、`-unrom-512-`。— https://github.com/llvm-mos/llvm-mos-sdk
- その他の言語: NESFab、KickC、vbcc、Millfork 等。— https://www.nesdev.org/wiki/Tools
- neslib (clbr): 「a ca65 asm library consisting of useful NES functions」。zlib、cc65の開発版向け。— https://github.com/clbr/neslib
- nesdoug: 「NES programming tutorial for cc65」。neslib と nesdoug library の付録、MMC1/MMC3 の章がある。— https://nesdoug.com/
- NROM: PRG「16K or 32K」、CHR「8K」、ミラーリングははんだパッドで固定、iNESマッパ0。— https://www.nesdev.org/wiki/NROM
- UxROM: PRG 256K/4096K、CHR RAM 8K、「74HC161 binary counter used as a quad D latch」と74HC32 で構成。オリジナル基板にはバスコンフリクトがある。iNESマッパ2。— https://www.nesdev.org/wiki/UxROM

### Inferences
- (推論) 本基板は「カートスロットに市販または自作のカートを挿す」設計なので、専用ゲームを NROM(PRG 32KB + CHR 8KB)に収まる規模にすれば、テスト用の自作カートと同じPCBが使え、部品の種類も最小になる。容量が足りない場合だけ UxROM(CHR RAM)にする。74HC161/74HC32 が JLCPCB の Basic にあるかは未確認。
- (推論) Pico がカートスロット経由でROMを供給する構成にすれば、カートPCB自体が要らなくなる(fc-rom-vomitter 方式)。

### Gaps
- 74HC161/74HC32 が JLCPCB の Basic Parts か、DIP-28 ROMソケットのLCSC在庫は、本調査では未確認(別ノートの範囲)。

---

## 6. 立ち上げ機材 (ロジアナ・オシロ・JAMMA試験台・DIP-40取り外し・ESD)

### Takeaway
観測対象の周波数は、マスタークロック 21.477272MHz、CPU 1.789773MHz(÷12)、PPUドット 5.369318MHz(÷4)。ロジアナは **16ch以上で、全chを100MS/s以上で取れる機種**が必要(推論: 21.48MHzクロックの1周期46.6nsに4〜5サンプル入れるため)。費用対効果の候補は **DSLogic Plus($149、16ch時100MHz、sigrok対応)** と **Kingst LA2016(16ch、200MHz、sigrok対応)**。Saleae Logic 8 は秋月で ￥82,800 と高価なうえ、sigrok は非対応(planned)で、sigrok wiki によると8ch使用時は25MS/s。オシロは100MHz級(OWON SDS1102 ￥39,000)で足りる(推論)。DIP-40の取り外しは、HAKKO FR-301(秋月 ￥22,000)の取扱説明書の手順を一次資料として使える。

### Cited Findings
- タイミング: マスタークロックは「21.477272 MHz ± 40 Hz」、CPUは「21.47~ MHz ÷ 12 = 1.789773 MHz」、PPUの1ドットはマスタークロック4つ分(→5.369318MHz)。— https://www.nesdev.org/wiki/Cycle_reference_chart , https://www.nesdev.org/wiki/CPU
- ロジアナ(sigrok wiki の infobox):

| 機種 | sigrok | ch | サンプルレート | その他 | 出典 |
|---|---|---|---|---|---|
| DSLogic Plus | supported(ただし「newer V421/Pango variant ... Currently incompatible with sigrok」) | 16 | 400MHz(4ch)/200MHz(8ch)/100MHz(16ch) | 256Mbit、閾値0–5V(0.1V刻み) | https://sigrok.org/wiki/DreamSourceLab_DSLogic_Plus |
| DSLogic U3Pro16 | planned | 16 | 1GHz(3ch)/500MHz(6ch)/250MHz(12ch)/125MHz(16ch) | 256MB | https://sigrok.org/wiki/DreamSourceLab_DSLogic_U3Pro16 |
| Kingst LA2016 | supported(2021年11月〜2022年2月以降のソフトを推奨) | 16 | 200MHz max(ch数による変化の記載なし) | 128MB DDR2、閾値-4〜4V | https://sigrok.org/wiki/Kingst_LA2016 |
| Kingst LA5016 | supported | 16 | 500MHz max | 2Gib RAM | https://sigrok.org/wiki/Kingst_LA5016 |
| Saleae Logic8 | **planned(非対応)** | 3/6/7/8 | 100/50/40/25 MS/s | 価格$349(wikiの記載) | https://sigrok.org/wiki/Saleae_Logic8 |
| Saleae Logic Pro 8 | planned | 8 | 500/100MHz(4ch/8ch) | $619(wikiの記載) | https://sigrok.org/wiki/Saleae_Logic_Pro_8 |
| ZEROPLUS LAP-C(16032) | supported | 16 | 100MHz | 32Kbit/ch | https://sigrok.org/wiki/ZEROPLUS_Logic_Cube_LAP-C(16032) |
| fx2lafw系(Lcsoft Mini Board等) | supported | 8/16 | 「up to 24MHz」 | — | https://sigrok.org/wiki/Lcsoft_Mini_Board |

- DreamSourceLab の公式価格(2026-11-10): DSLogic Plus「$199.00 → $149.00」、U3Pro16「$399 → $299」、U3Pro32「$499 → $399(Out of Stock)」。「Free shipping for order amount over $100」。— https://www.dreamsourcelab.com/shop/ , https://www.dreamsourcelab.com/product/dslogic-series/
- Saleae Logic 8 の公式仕様:「Captures digital signals at up to 100 MS/s with analog recording at 10 MS/s, 10-bit resolution」。— https://www.saleae.com/products/saleae-logic-8
- 秋月のロジアナ(2026-11-10、税込、括弧内は通販可能数): Logic8-Black ￥82,800(34台、g108975)、Logic Pro8-Black ￥182,160(g108976)、ZEROPLUS LAP-C(16064) 16ch100M ￥22,800(g104426)、LAP-C(16128) 16ch200M ￥53,800(g103081)、LAP-C Pro(16064M) 16ch1G ￥119,800(g132044)。— https://akizukidenshi.com/catalog/g/g108975/ ほか
- スイッチサイエンスで「DSLogic」を検索してヒットしたのは、Saleae Logic16(販売終了)と24MHz 8chの互換品(販売終了)だけだった。— https://www.switch-science.com/search?q=DSLogic
- 秋月のオシロとプローブ:

  | 品名 | 価格 | 商品コード |
  |---|---|---|
  | OWON SDS1102 2ch 100MHz | ￥39,000 | g116900 |
  | OWON SDS1104 4ch 100MHz | ￥45,000 | g116901 |
  | OWON SDS1022 2ch 20MHz | ￥35,000 | — |
  | Hantek 6022BE USB 20MHz/48Msps | ￥12,720 | g116926 |
  | プローブ 100MHz | ￥2,000 | g100240 |
  | プローブ 250MHz | ￥2,540 | g117802 |
- 帯域と立ち上がり時間: 単極系で「BW·tr ≅ 0.35」(ガウス応答なら0.34)。— https://en.wikipedia.org/wiki/Rise_time
- JAMMA電源の候補 MEAN WELL RT-65A: CH1 5V 6A(0〜8A)、CH2 12V 2.8A、CH3 −5V 0.5A、66.1W。5Vの調整範囲は4.75〜5.5V、5Vのリップルは80mVp-p。RT-65Bは3出力目が−12V。— https://www.meanwell.com/Upload/PDF/RT-65/RT-65-SPEC.PDF
- スキャンコンバータ:
  - OSSC 1.8: €115.00(税込)〜€148.49(付属品による)、「OSSC 1.8 is now in stock」。— https://videogameperfection.com/products/open-source-scan-converter/
    - 入力: SCART は RGBs/RGsB/YPbPr、VGA(D-SUB15)は RGBHV/RGBs/RGsB/YPbPr。
    - 15kHzの 240p/288p を line 2x〜5x に変換し、HDMI/DVIで出力。
    - 入力電圧レベルの記載はない。
  - OSSC wiki の注意書き。— https://junkerhq.net/xrgb/index.php?title=OSSC
    - 映像入力:「the video inputs also have standard 75 ohm termination, so arcade boards may need extra resistors on the cable when connected directly without using a Supergun」。
    - 同期入力:「the sync input has 75 ohm termination, so a TTL-level sync signal should not be directly connected to the OSSC」。対策は「a 470 ohm series resistor on the console side ... is generally a good solution」。
    - 映像レベルが高い場合は Pre-ADC Gain を下げる。
  - RetroTINK。— https://www.retrotink.com/shop/retrotink-4k-ce , https://www.retrotink.com/shop/retrotink-5x-pro
    - 4K CE: $475、InStock。HD15/VGA は RGBHV RGBS RGsB YPbPr S-Video Composite、SCART は RGBS RGsB YPbPr …。
    - 5X Pro: $325。入力は 240p/480i/288p/576i/480p…、電源は 5V/2A microUSB。
    - そのほか 6X CE $230、2X Pro $139.99、4K Pro $750。
  - GBS-Control:「alternative firmware for Tvia Trueview5725 based upscalers」。RGBS(SCART)、RGBHV、コンポーネントを入力でき、ESP8266でWeb制御する。本ページにアーケードのレベルへの言及はない(「Arcade Boards notes」というwikiページは存在せず、作成画面になる)。— https://ramapcsx2.github.io/gbs-control/
- DIP-40の取り外し手順(HAKKO FR-301 取扱説明書、日本語、2019.04.01版):
  1. 「除去する部品のリード線をノズルの穴に差し込んで加熱します。ランドではなく、リード線とはんだを加熱するように心がけてください。ノズルを直接ランドにあてるとランドが剥離する恐れがあります。」
  2. 「... リード線をノズルに差し込んだままで、軽くゆっくりとリード線を動かしてください。リード線が簡単に動けばはんだがすべて溶けたと考えられます。」
  3. 「トリガーをひいて溶かしたはんだを吸引します。」
  4. 「失敗した時は、新しいはんだでもう一度はんだ付けしてからやり直します。」

  設定温度は350〜500℃、標準ノズルは N61-08 φ1.0。ノズルは N61-01〜16(φ0.6〜1.6、長円3×1/4×1mm)。— https://www.hakko.com/japan/support/doc/result.php?mode=download&seq=5895 , https://www.hakko.com/japan/products/hakko_fr301_spec.html , https://www.hakko.com/japan/products/hakko_fr301_tips.html
- 秋月の取り外し・ソケット関連(秋月各商品ページ):

  | 品名 | 価格 | 備考 |
  |---|---|---|
  | FR301-82 | ￥22,000 | 2026-06-16に￥23,500から値下げ、通販可能数23 |
  | goot GS-108 | ￥1,150 | — |
  | エンジニア SS-03 | ￥2,580 | — |
  | 丸ピンICソケット40P | ￥110 | 在庫3491個 |
  | ICソケット40P | ￥350/パック | — |
  | ZIF 40P 600mil | ￥250 | g111744 |
  | ロープロZIF 40P | ￥250 | g105436、Aries |
- ESD(TI SSYA010A §3.3 ESD Avoidance)。— https://www.ti.com/lit/an/ssya010a/ssya010a.pdf
  - 第一の原則:「the first and most important rule ... is to keep ICs and everything that comes in close proximity to them at ESD ground potential」。
  - 補助ルール1(人体の接地):「Any person handling ICs must be grounded either with a wrist strap or ESD protective footwear」。
  - 補助ルール2(作業面):「The work surface ... must be made of static dissipative material and be grounded」。
  - 補助ルール3(絶縁物):「All insulator materials either must be removed from the work area or ... neutralized with an ionizer」。
  - 補助ルール4(保管):「When ICs are being stored ... maintained in a Faraday shield container whose inside surface ... is static dissipative」。
- 秋月のESD用品: リストストラップ 442B-01 ￥1,150(g114463)、09070 ￥2,980、導電性スポンジ 200×100×5mm ￥170(g109709)、帯電防止(アルミ蒸着)袋 各種。

### Inferences
- (推論) ロジアナのサンプルレート: 1.79MHzのCPUバス(周期559ns)のアドレス/データ有効窓を見るだけなら25〜50MS/sでも足りる。M2やPPU /RD等とマスタークロック21.48MHz(周期46.6ns)の位相関係を見るには最低100MS/s(分解能10ns、1周期に約4.7サンプル)が必要で、余裕を持つなら200MS/s。CPUバス(A0–A15、D0–D7、M2、R/W の約26本)を全部同時に見るには16chでは足りない。**データ8本+制御数本+アドレスの一部**に絞るか、32ch機を使う。DSLogic Plus は16ch時に100MHzで最低線を満たす。
- (推論) オシロの帯域: 21.48MHzクロックの基本波と3次高調波(64MHz)を見るなら、100MHz機で実用上十分。立ち上がり時間を正確に測る(例: tr=5ns なら 0.35/5ns = 70MHz相当)ところまで求めるなら200MHz以上。既存ノートの「200MHz帯域以上を推奨」は厳しめだが誤りではない。15kHzアナログRGB(画素5.37MHz)と電源リップルの確認は100MHzで足りる。
- (推論) JAMMA試験台: 市販のスーパーガン(未調査)を使わなくても、RT-65A + JAMMAハーネス(56ピン端子)+ RGBをスキャンコンバータへ、で組める。JAMMAのRGBは一般にコンシューマの0.7Vppより高いとされ、OSSCは75Ω終端でTTLのcsyncを直結できないと明記している。そこで、**基板側に「民生0.7Vpp/75Ω出力モード」を設けるか、試験用の減衰ケーブル(csyncに470Ω直列)を用意する**と試験が楽になる。
- (推論) DIP-40の取り外し: 40本のピンを1本ずつ FR-301 で吸い、取説の手順2(リードを揺すって全体が溶けたことを確認)を守る。吸いきれない穴は新しい有鉛はんだを足して吸い直す(取説の手順4)。ランドの剥離を避けるため、ノズルをランドに押し付けない。抜いたチップはすぐ導電スポンジかシールド袋に入れる。
- (推論) RP2A03/RP2C02 は1980年代のNMOS世代の6502派生LSIで、入力保護は現代のCMOSより弱いと考えられる(一次資料は未取得)。上記TIの4ルール(リストストラップ、接地マット、絶縁物の排除、シールド袋)を守る。

### Gaps
- RP2A03/RP2C02 がNMOSであることの一次資料: nesdev wiki の CPU/PPU、Wikipedia の Ricoh 2A03(「6 μm」とあるだけ)、emu-russia/breaks、visual6502(503)を試した → **未確認**(推論として扱う)。
- JAMMAのRGBの実際の電圧レベル(Vpp)と、OSSC/RetroTINKの許容入力電圧: OSSC製品ページ、OSSC wiki、GBS-Control のどれにも数値がない → **未確認**。
- スーパーガン(MINIGUN等)の仕様と価格: retroelectronik.com(DNS解決不可)、arcadeworlduk(445)を試した → **未確認**。
- Kingst LA2016 の価格(qdkingst.com が503)、DSLogic/Kingst/T48/EverDrive/OSSC/RetroTINK/RT-65A の国内販売店と円価格 → **未確認**。
- オシロ帯域の「5倍則」等の一次資料は取得できなかった(Keysight/Tektronix とも失敗)。出典があるのは立ち上がり時間の関係式のみ。
- Famicom本体からDIP-40を取り外す専用の手順書(nesdevや修理サイト)は見つからず、汎用のはんだ吸取器の取説で代用した。

---

## 既存ノートへの訂正

| 既存ノートの記述 (tooling_and_mcp.md) | 訂正・補足 | 出典 |
|---|---|---|
| §5「Pico SDK: 2.3.1 (表示は「04 Sep」、年は…2026年と推定)」 | 推定は正しかった: published_at 2026-09-04T22:38:41Z。同梱の picotool は SDK と同じタグ(2.3.1、2026-09-05)を自動取得する | https://api.github.com/repos/raspberrypi/pico-sdk/releases , Findpicotool.cmake |
| §5「pioasmはPico SDKに同梱(ビルド時に取得)」 | 「取得」ではなく、SDKツリー内の `tools/pioasm` のソースをビルドする(ネットからの取得はない)。ネットから取得されるのは picotool | https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpioasm.cmake |
| §5「rp2040js: 指定URLは404。正しい所在…未確認」 | 所在は https://github.com/wokwi/rp2040js (MIT、npm 1.4.1 = 2026-10-18、pio.ts/dma.ts あり) | 同URL、registry.npmjs.org/rp2040js |
| §5「Wokwi CLI … RP2040/RP2350/PIO対応、APIトークン要否は未確認」 | トークンは必須(`WOKWI_CLI_TOKEN`、「wok_」で始まる)。RP2040/RP2350 ともPIOを模擬する。ただしコア1つのみ、RP2350固有のPIO命令はなく、RP2040のDMAはPIO用のみ | https://docs.wokwi.com/wokwi-ci/github-actions , https://docs.wokwi.com/parts/board-pi-pico-2 |
| §5「MesenCE … ヘッドレスtest runner/Lua詳細はREADMEから確認できず」 | `--testRunner [lua] [rom]` があり、`timeout=` の既定は100秒。終了コードは `emu.stop(code)` で返す(ヘルプ文の `emu.exit` は誤記で、Lua APIに `exit` はない)。MesenCE は Mesen 2.2.0 (2026-06-04) / 2.2.1 (2026-06-05) をリリース済み | MesenCE のソース (CommandLineHelper.cs, TestRunner.cs, LuaApi.cpp)、releases.atom |
| §5「cc65 … 最新タグ日付は未取得」 | 最終タグは V2.19 = 2020-11-20 で、version.c も 2.19。Windowsスナップショットは 2026-11-08 | https://github.com/cc65/cc65/releases.atom , SourceForge |
| §5「apt版fceux 2.6.5」 | 上流の最新は 2.7.0 (2026-10-14)。公式の起動オプションは `-lua` で、ヘッドレスのオプションは記載なし | https://github.com/TASEmulators/fceux/releases.atom , fceux.com |
| §5 NESテストROM一覧(nestest, instr_test-v5 …) | 重要な補足: blargg のまとめ版ROM(all_instrs、ppu_vbl_nmi、apu_test、cpu_interrupts、instr_timing)は **MMC1(mapper 1)** なので、NROMのテストカートでは走らない。rom_singles は NROM 32K+8K。nestest は「start at $C000」で起動してログと比較するエミュレータ向けのROMで、実機で合否を表示するものではない | iNESヘッダの実測、https://www.nesdev.org/wiki/Emulator_tests |
| §6「テストカート: EPROM/フラッシュ書き込み器(例: TL866系)」 | TL866A/CS は2018年2月に出荷を停止しており、市場品は偽物だとメーカーが告知している。TL866II Plus も後継の T48 に置き換わりつつある。新規に買うなら T48。Linuxでは minipro が T48 に対応している | http://www.xgecu.com/en/ , minipro README |
| §6「ロジアナ…Saleae互換や sigrok対応…を想定」 | 「Saleae互換」(fx2lafw系)は最大24MHzで、本用途には足りない。Saleae純正の Logic 8 も sigrok 非対応(planned)で、8ch使用時は25MS/s。sigrok対応で要件を満たすのは DSLogic Plus(旧版ハード)や Kingst LA2016/LA5016 等 | sigrok wiki の各ページ |
| §6 全体「出典なし・全て未確認」 | 本ノートの §6 で出典付きの内容に置き換えた(残る未確認事項は §6 の Gaps を参照) | — |
| §4表「Wokwi: 無料枠は30日で50分・1セッション5分」 | 正しい(CI用の無料枠)。補足として、Pro は €20/seat/月で CI 2000分。無料プランは public プロジェクトのみ | https://wokwi.com/pricing |
