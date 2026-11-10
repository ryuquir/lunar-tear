# ツール・MCP調査 (KiCad / JLCPCB / ファームウェア / テスト) — 2026-11-10時点

注記: 「未確認」は検証できなかった項目。GitHubのREADMEはWebFetch(小型モデルによる要約)経由で取得したため、星数・版数は取得時点の表示値。github.com / api.github.com へのcurlはプロキシで403、WebFetchは可。

## 1. KiCad本体: 最新版・CLI・IPC API・SWIG・導入方法

### Takeaway
KiCad最新安定版は 10.0.8 (2026-10-30)。ヘッドレスで使える公式手段は kicad-cli (ERC/DRC/netlist/BOM/Gerber/drill/pos/STEP/render/PDF/SVG/jobset)。IPC API(kipy)は「起動中のKiCad GUIが必要」でヘッドレス版は未実装、SWIG版pcbnewはKiCad 10では残るがKiCad 11で削除見込み。Ubuntu 24.04のaptは7.0.11で古く、PPA(kicad-10.0-releases)またはDocker公式イメージが現実的。

### Cited Findings
- KiCad 10.0.x リリース: 10.0.8=2026-10-30, 10.0.7=2026-10-07, 10.0.6=2026-08-29, 10.0.5=2026-07-22(いずれも保守リリース) — [kicad.org blog](https://www.kicad.org/blog/)
- KiCad 10の主な変更: PCBエディタのDesign Blocks、シンボルPin Table CSV入出力、ピン/ゲートスワップ、公式3DモデルはSTEPのみ — [KiCad 10.0.0 release post](https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/) (リリース記事自体はIPC API/SWIGに言及なし)
- kicad-cli 10.0 のサブコマンド: `fp`(export svg, upgrade), `jobset run`, `pcb`(drc, export {3dpdf, brep, drill, dxf, gencad, gerbers, glb, ipc2581, ipcd356, odb, pdf, ply, pos, ps, stats, step, stl, stpz, u3d, svg, vrml, xao}, import, render, upgrade), `sch`(erc, export {bom, dxf, netlist, pdf, ps, python-bom(旧), svg}, upgrade), `sym`(export, upgrade), `version`。HPGL出力は10.0で非対応、`sch export bom --include-excluded-from-bom`は10.0で非推奨・無効 — [KiCad 10.0 CLI docs](https://docs.kicad.org/10.0/en/cli/cli.html) (全文の末尾約1万字は未読)
- IPC API: 「稼働中のKiCadインスタンスがサーバとして動作する」設計。ヘッドレス動作の記述なし。安定化は9.0を目標、とされる(古い記述) — [IPC API docs](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/)
- KiCad開発者Jon Evansの発言(2026-01-06): 「SWIG(pcbnew.py)は10では削除されない」「ヘッドレスモードは未実装で、kicad-cliの機能(バックグラウンドサーバ)として実装予定。専用Pythonインタプリタではない」「eeschema(回路図)のIPC APIは10に間に合わなかった。11では実現可能だが開発者の時間次第」 — [KiCad devlist](https://groups.google.com/a/kicad.org/g/devlist/c/3e8OU0FiEHc)
- 開発版10.99ではSWIG APIと同梱Pythonが削除されたとのフォーラム/PR報告(KiCad 11でSWIG削除の見込み)。リリースノートでの直接確認はできていない — [WebSearch結果: forum.kicad.info スレッド](https://forum.kicad.info/t/kicad-10-99-win-missing-python-exe/71638)
- kicad-python (kipy): GitLab `kicad/code/kicad-python`, MIT, 11タグ。PyPI版は 0.8.0 (2026-08-30) — [GitLab](https://gitlab.com/kicad/code/kicad-python), [PyPI](https://pypi.org/pypi/kicad-python/json)
- apt標準: `kicad` 7.0.11+dfsg-1build4 (Installed-Size約146MB、DL約36MB、依存別) — コンテナ実測 (apt-cache policy/show kicad)
- PPA `kicad/kicad-10.0-releases` と `kicad-9.0-releases` の noble Release が取得可(HTTP 200) — https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu/dists/noble/Release (コンテナ実測)
- Docker Hub `kicad/kicad`: タグ 10.0.8 (圧縮約812MB), 10.0.8-full (約1.45GB, 3Dモデル・ライブラリ込み), 更新2026-10-30 — [Docker Hub API](https://registry.hub.docker.com/v2/repositories/kicad/kicad/tags)
- Flatpak: dl.flathub.org が403で本コンテナからは不可 — コンテナ実測
- KiBot のリポジトリには Dockerfile_k5〜k10 / dk5〜dk10 があり KiCad 10用が存在するらしい — [KiBot](https://github.com/INTI-CMNB/KiBot)

### Inferences
- ヘッドレスで安全に使える確実な経路は kicad-cli + (ファイル直接編集系ライブラリ / SWIG pcbnew(KiCad 10まで))。IPC API/kipyはxvfb等でGUIを仮想ディスプレイ上に起動すれば動く可能性があるが、公式には保証されていない(未確認)。
- 本プロジェクトでは `kicad-cli sch erc`, `pcb drc`, `pcb export gerbers/drill/pos`, `sch export bom/netlist`, `pcb render`, `jobset run` をCI的に回すのが中核。
- 推奨導入: `add-apt-repository ppa:kicad/kicad-10.0-releases` → `apt install kicad`(要:コンテナ内でのapt実行可否とサイズの確認。フル導入は数百MB〜GB級と推定、未実測)。Docker可なら `kicad/kicad:10.0.8`。

### Gaps
- PPA導入後の実サイズ、コンテナ内Docker可否、xvfb下でのIPC API動作は未確認。
- KiCad 10.0.0の正式リリース日(2026-03頃と推定、記事URLより)は本文で未確認。

## 2. コードファースト/ライブラリ/オートルータ/パネル化

### Cited Findings (PyPI JSON API実測: https://pypi.org/pypi/<name>/json)
| ツール | 目的 | 最新版 / 最終アップロード | 状態判断 | ヘッドレス | 区分 |
|---|---|---|---|---|---|
| kiutils | KiCadファイルS式の読み書き | 1.4.8 / 2024-02-02 | 約2.7年更新なし。KiCad 9/10書式対応は未確認 | 可 | 注意 |
| kicad-skip | 回路図/PCB S式操作 | 0.2.5 / 2024-02-16 | 同上 | 可 | 注意 |
| kicad-sch-api | 回路図生成 | 0.5.6 / 2025-11-19 | 約1年停滞 | 可 | 低 |
| circuit-synth | Python→KiCad | 0.12.1 / 2026-01-09 | 停滞気味 | 可 | 低 |
| SKiDL | Pythonで回路記述→netlist | 3.0.0 / 2026-10-16 | 活発 | 可 | 任意 |
| atopile | DSL→KiCad (GitHub ★4.1k, MIT) | 0.15.9 / 2026-09-12 | 活発だが0.x。大規模基板の実績は未確認 | 可 | 任意 |
| kicad-python (kipy) | IPC APIクライアント | 0.8.0 / 2026-08-30 | 活発。GUI必須 | 不可(GUI要) | 条件付 |
| KiKit | パネル化・製造出力 | 1.8.1 / 2026-08-05 | 活発 | 可(pcbnew Python要) | JAMMA基板は単面なら不要 |
| KiBot | KiCad出力の自動化(YAML) | 1.9.1 / 2026-07-28 | 活発、AGPL-3.0、k10 Docker有 | 可 | 推奨候補 |
- atopile GitHub: ★4.1k, MIT, 2,843 commits — [atopile](https://github.com/atopile/atopile)
- tscircuit: PyPIの `tscircuit` は無関係(0.0.1)。本体はnpmパッケージ(TypeScript) — PyPI実測。npm版の状態は未確認。
- Freerouting: v2.5.0 (2026-10-05)。ヘッドレス: `--gui.enabled=false --api_server.enabled=true`、127.0.0.1:37864、API認証は既定ON。v2.5.0でネイティブCLI(Java不要)・`POST /v1/autoroute`・MCP `autoroute_board`を追加。以前はJava 25必須(v2.2.0以降)。GHCRにDockerイメージ有。ライセンス記載はページ上で未確認 — [Freerouting releases](https://github.com/freerouting/freerouting/releases)
- apt には freerouting / kikit / picotool / pico-sdk パッケージ無し — コンテナ実測

### Inferences
- 約150部品の混在信号基板では、回路図は「Claudeが生成するS式(kicad-cli ERCで検証)」か「SKiDL」が現実的。kiutils/kicad-skipは更新停止のためKiCad 10書式での往復を要検証。
- 部品配置・配線の完全自動化は未成熟。配置は人間レビュー必須、ルーティングはFreerouting(v2.5.0)で粗配線→DRC。

### Gaps
- kiutils/kicad-skipがKiCad 10フォーマットを正しく扱えるかの実検証なし。tscircuitの現況、circuit-synthの大規模基板実績は未確認。

## 3. JLCPCB固有ツールと部品DB

### Cited Findings
| ツール | 内容 | 状態(取得時) | ヘッドレス | 区分 | URL |
|---|---|---|---|---|---|
| Fabrication Toolkit (bennymeg) | JLCPCB向けGerber/BOM/CPL/IPCネットリスト生成 | Apache-2.0, ★706。KiCad 6+同梱(PCM)。リリース版数は未取得 | 可: `python3 -m plugins.cli -p board.kicad_pcb` (`--autoFill`, `--excludeDNP`等) | 推奨 | https://github.com/bennymeg/Fabrication-Toolkit |
| kicad-jlcpcb-tools (Bouni) | LCSC番号割当、部品DB検索、Gerber/BOM/CPL出力 | MIT, ★2.1k。KiCad 7〜10対応表記、設計バリアントは10+ | GUIプラグイン前提。ヘッドレスの記載なし | 参考 | https://github.com/Bouni/kicad-jlcpcb-tools |
| KiBot | JLCPCB向け出力もYAMLで定義可 | AGPL-3.0, 1.9.1 | 可 | 推奨 | https://github.com/INTI-CMNB/KiBot |
| easyeda2kicad | LCSC番号→KiCadシンボル/フットプリント/3D | 1.0.1 (2026-04-06) | 可(CLI) | 推奨 | https://github.com/uPesy/easyeda2kicad.py |
| JLC2KiCadLib | 同上 | 1.3.2 (2026-09-11) | 可(CLI) | 代替 | PyPI https://pypi.org/pypi/JLC2KiCadLib/json |
| jlcsearch (tscircuit) | 在庫部品検索API(`.json`付与でJSON、`/api/easyeda_components/<LCSC>`等) | MIT。毎日05:00 UTC同期、Cloudflare D1 | HTTP APIのため可。ただし本コンテナからは curl -I が405(GET可否は未確認) | 推奨(要GET確認) | https://github.com/tscircuit/jlcsearch |
| CDFER/jlcpcb-parts-database | JLCPCB部品SQLite(約1GB, 在庫5個以上)とBasic/Preferred CSV(約3MB)。毎日06:00 UTC更新 | MIT | 可(ダウンロード) | 推奨 | https://github.com/CDFER/jlcpcb-parts-database |
| yaqwsx/jlcparts | 元DB(約11GB SQLite)のソース | 上記ページ経由で確認 | 可 | 参考 | https://github.com/yaqwsx/jlcparts |
- JLCPCB公式の .kicad_dru は見つからず、コミュニティ版: labtroll/KiCad-DesignRules (KiCad 7向け)、Cimos/KiCad-CustomDesignRules (JLCPCB/PCBWay、KiCad 8書式でKiCad 9/10前方互換と記載)。公式の基準値は https://jlcpcb.com/capabilities/pcb-capabilities (本文は未取得)。検索結果では標準1〜2層の最小線幅/間隔 約0.127mm(5mil)、ビア径0.25mm/ドリル0.15mmと記載する資料と、3.5mil(0.09mm)とする資料があり不一致 — [WebSearch結果](https://github.com/labtroll/KiCad-DesignRules), [Cimos](https://github.com/Cimos/KiCad-CustomDesignRules), [JLCPCB KiCadブログ](https://api.jlcpcb.com/blog/optimizing-kicad-designs-for-jlcpcb-fabrication)
- EasyEDA Pro自動化: レジストリにEasyEDA Pro拡張ブリッジ型MCPあり(後述)、いずれもEasyEDA Pro(GUI/ブラウザ)稼働が前提 — レジストリ実測

### Inferences
- 回路図は部品確定後に easyeda2kicad でLCSC部品をライブラリ化し、BOMのLCSC列を埋めて Fabrication Toolkit CLI か KiBot でJLCPCB出力、が最小構成。Basic判定は CDFER CSV で機械的に照合可能。
- JLCPCBの回転オフセット補正は Fabrication Toolkit / jlcpcb-tools 側の機能(詳細は未確認)。

### Gaps
- JLCDFM の自動化可否、JLCPCB公式Capabilitiesの現行数値、Fabrication Toolkit/KiBotの最新リリース日は未確認。

## 4. MCPサーバ (公式レジストリ https://registry.modelcontextprotocol.io 検索 + 各README)

### Takeaway
KiCad向けMCPは多数あるが、どれも若く流動的。ProductOfAmericaは保守モード宣言、mixelpixxは新開発をKiCad 10向けRust製Konnect(AGPL)へ移行。JLCPCB/LCSC専用の独立MCPはレジストリ検索で0件(KiCad系MCPに部品検索が内蔵されるものはある)。実機接続系(serial/OpenOCD/pico)はクラウドコンテナでは使えずデスクトップ用。

### Cited Findings (表)
| 名称 / URL | 状態(取得時) | ヘッドレス/クラウド | 区分 |
|---|---|---|---|
| ProductOfAmerica/mcp-server-kicad https://github.com/ProductOfAmerica/mcp-server-kicad | v0.21.1 (2026-10-20)、109ツール(回路図42/PCB34/プロジェクト24/シンボル5/フットプリント4)、2026-10に保守モード、★16、GPL-3.0以降(0.20.1まではMIT)。ファイル直接解析+kicad-cli、fill_zones/autoroute_pcbはpcbnew Python+Java25+Freerouting。Claude Codeプラグイン: `claude plugin marketplace add ProductOfAmerica/mcp-server-kicad`、他は `pip install mcp-server-kicad` / uvx | GUI不要、クラウド可 | 試用価値あり(nice-to-have) |
| mixelpixx/KiCAD-MCP-Server https://github.com/mixelpixx/KiCAD-MCP-Server | ★約3.3k、MIT、KiCad 9+/Node18+/Python3.11+、JLCPCB部品カタログ(価格・在庫)・Freerouting(Java/Docker)統合、1,052 commits。GUI要否は記載なし | 未確認 | nice-to-have(要検証) |
| oaslananka/kicad-mcp-pro https://github.com/oaslananka/kicad-mcp-pro | README上 v4.11.0 (レジストリ上は2.1.0=2026-04-15、不整合)、★206、MIT、stdio+Streamable HTTP、既定は24個の読み取りツール、build/releaseプロファイルで編集・製造出力。JLCPCB公開カタログ検索(Nexar/DigiKey/Mouserはキー要)。`uvx kicad-mcp-pro quickstart`。コアはGUI不要 | クラウド可 | レビュー用nice-to-have |
| lamaalrajih/kicad-mcp https://github.com/lamaalrajih/kicad-mcp | ★534、MIT、プロジェクト解析/BOM/kicad-cli DRC/サムネイル。編集機能は弱い | kicad-cliのみ | 低 |
| biosshot/kicad-copilot, daedalus/mcp-kicad, bunnyf/pcb-mcp, PCBEditor/pcbeditor-mcp | 0.1.0(2026-08)/0.1.1(2026-04)/3.5.0(2026-01)/1.3.11(2026-10) (レジストリ実測) | 未確認 | 未成熟・未確認 |
| EasyEDA Pro系: oaslananka/easyeda-mcp-pro (1.13.1, 2026-11-09), biosshot/easyeda-copilot (1.3.2, 2026-10-15), VLab-Software/easyeda_mcp (1.0.2, 2026-05-26) | EasyEDA Pro拡張ブリッジ | GUI必須→クラウド不可(推定) | EasyEDA採用時のみ |
| データシート: turbyho/datasheet-lens https://github.com/turbyho/datasheet-lens (0.6.1, 2026-11-10); FelixNovaNexus/datasheet-vend (1.1.0, 2026-10-27) | PDF索引/検索 | 未確認 | 未検証 |
| 流通: pipeworx-io/mcp-octopart (0.2.1, Nexar API), mrfentmen/digikey-mcp (1.0.0。mrfentmenは同名で大量の汎用MCPを出す「awesome-servers」リポジトリで信頼性疑問) | キー要 | — | 低 |
| PlatformIO: jl-codes/platformio-mcp (3.1.0, 2026-09-25), powerdragonfire/platformio.mcp (0.1.0) | ビルド可・書込は実機 | — | Pico SDK直ならば不要 |
| 実機: microhenrio/openocd-mcp (0.4.5), qarnet/serial-mcp (0.9.3), ctrlpi/pico-bay (0.9.34), es617/serial-mcp-server (0.1.3) | USB実機必須 | デスクトップのみ | 実機デバッグ時 |
| Wokwi: Wokwi CLIに実験的MCP対応あり(docs.wokwi.com サイドバー) | クラウドシミュレーション、無料枠は30日で50分・1セッション5分 | CI可(ただし外部クラウド依存) | 補助 |
- 出典(レジストリ): https://registry.modelcontextprotocol.io/v0/servers?search=kicad 等(search=kicad, easyeda, platformio, serial, datasheet, octopart, digikey, pico, openocd, gerber, pcb)。jlcpcb, lcsc, ngspice, spice, probe-rs, wokwi, mouser, nexar は該当0件。
- Freerouting自体にMCP `autoroute_board` が付属(v2.3.0以降) — [Freerouting releases](https://github.com/freerouting/freerouting/releases)
- Smithery/Glama/PulseMCP/mcp.so は未調査(Glama上のmixelpixxドキュメントは検索結果に出現のみ)。

### Inferences
- 推奨: KiCad系MCPは必須ではない。Claude Codeがkicad-cli・Python・シェルを直接使える環境では、MCPは「回路図編集ツールの便利ラッパ」程度。試すなら ProductOfAmerica(ファイル直接編集系の網羅性) か kicad-mcp-pro(レビュー/製造出力ゲート)を1つだけ。
- 保守状況の悪化リスク: GPL化、保守モード、Rust書き換えがあるため依存を深くしない。

### Gaps
- 各MCPのlast commit日はWebFetch要約に出ず(README上の版数・レジストリ更新日のみ)。mixelpixx/Konnect のGUI要否、Smithery/Glama/PulseMCP/mcp.so掲載状況、jlcsearchをラップする専用MCPの有無(レジストリ上は無し)は未確認。

## 5. ファームウェア/テストツールチェーン

### Cited Findings
- Pico SDK: GitHub最新は 2.3.1 (表示は「04 Sep」、年はページに無い。一覧順から2026年と推定)。2.0.0でRP2350対応(`rp2350-arm-s`/`rp2350-riscv`)、2.1.0でRP2350 A0/A1非対応、2.3.0で hardware_psram・XIPキャッシュSRAM化 — [pico-sdk releases](https://github.com/raspberrypi/pico-sdk/releases) (同梱picotoolの版は未確認)
- apt: gcc-arm-none-eabi 13.2.rel1-2、libnewlib-arm-none-eabi、cc65 2.19-1、ngspice 42、openocd 0.12.0、sigrok-cli 0.7.2、pulseview 0.4.2、fceux 2.6.5、ghdl 4.1.0、iverilog 12.0、yosys 0.33、nextpnr-ice40 0.6 (コンテナ実測)。pioasmはPico SDKに同梱(ビルド時に取得)— 未実測
- cc65: zlibライセンス、NESターゲット対応、マスターは12,276コミット、公開は「Snapshot」配布。最新タグ日付は未取得 — [cc65](https://github.com/cc65/cc65)
- Mesen(元): SourMesen/Mesen2 は2026-06-04にアーカイブ(2.1.1相当、2025年中頃)。後継は nesdev-org/MesenCE (GPL-3.0, ★646, Linux x64/ARM64ビルド有、SDL2要) — [Mesen2](https://github.com/SourMesen/Mesen2), [MesenCE](https://github.com/nesdev-org/MesenCE)(ヘッドレスtest runner/Lua詳細はREADMEから確認できず)
- NESテストROM群(NESdev wiki): nestest, instr_test-v5, instr_timing, cpu_timing_test6, branch_timing_tests, cpu_interrupts_v2, cpu_reset, ppu_vbl_nmi, ppu_sprite_hit, sprite_overflow_tests, oam_read/oam_stress, ppu_open_bus, apu_test, apu_mixer, apu_reset ほか。コントローラ: allpads, read_joy3, Zap Ruder, PaddleTest3, SNESパッドtest。映像: 240p Test Suite NES版 (240pee, tepples) — [NESdev Emulator tests](https://www.nesdev.org/wiki/Emulator_tests), 240p: https://github.com/pinobatch/240p-test-mini/tree/master/nes
- rp2040js: 指定URL (github.com/rp2040js/rp2040js) は404。正しい所在(wokwi/rp2040js)・PIO対応状況は未確認
- Wokwi CLI: `curl -L https://wokwi.com/ci/install.sh | sh` で導入、シリアル出力で合否判定、クラウド実行、実験的MCP — [Wokwi CI](https://docs.wokwi.com/wokwi-ci/getting-started), [install](https://docs.wokwi.com/wokwi-ci/cli-installation)。RP2040/RP2350/PIO対応、APIトークン要否は未確認
- apt版fceux 2.6.5は存在するがGUI寄り。ヘッドレス実行可否は未確認

### Inferences
- 6502テストROM/ゲーム: apt の cc65 2.19 で足りる。エミュレータ検証はMesenCEのビルド取得(GitHub到達性は要確認)。
- HDLシミュレータは「プログラマブルロジックが必要になった場合のみ」で、今はインストール不要(apt: ghdl/iverilog/yosys/nextpnr-ice40あり)。
- アナログ(ビデオDAC/音声アンプ)検証は apt の ngspice 42 で可(MCPは存在せず、直接CLI)。

### Gaps
- picotool の入手経路(PPAなし、SDK同梱ビルド)、Pico SDK の年付き正確なリリース日、RP2350でのPIOシミュレータ(rp2040js/Wokwi)対応、MesenCEのテストランナー、NESテストROMの入手URLの現存確認は未実施。

## 6. 実機立ち上げ機材 (出典なし・設計者の一般知識に基づく推定。全て 未確認)

### Inferences
- ロジックアナライザ: 21.47727MHz(マスタークロック)/5.37MHz(ピクセル)を観測するには、最低でも100MS/s、できれば200〜500MS/s・帯域100MHz以上(24ch級)。Saleae互換や sigrok対応(sigrok-cli/PulseViewはaptで入手可、コンテナ実測)を想定。
- オシロスコープ: 21MHzクロックの波形品質確認には 200MHz帯域以上を推奨(推定)。
- JAMMA試験: スーパーガン or ハーネス+5V/12V電源、15kHz入力可のディスプレイ or スキャンコンバータ(OSSC/GBS-Control/RetroTINK)。
- DIP-40の取り外し: 吸引式ハンダ吸い取り機+フラックス、ソケット使用を推奨(RP2A03/RP2C02はDIP-40)。
- テストカート: EPROM/フラッシュ書き込み器(例: TL866系)やFamicom用フラッシュカート。具体製品・価格は未調査。

### Gaps
- 上記は全て一次ソース未確認。必要なら別途調査。

## 7. 推奨最小構成 (本コンテナ向け)

1. KiCad 10.0.x (PPA kicad-10.0-releases または kicad/kicad:10.0.8 Docker) — 必須。kicad-cliでERC/DRC/出力。
2. Fabrication Toolkit CLI または KiBot (pip) — JLCPCB向けGerber/BOM/CPL。
3. easyeda2kicad (pip) + CDFER/jlcpcb-parts-database CSV(Basic/Preferred照合) と jlcsearch — 部品選定。
4. Freerouting 2.5.0 (ネイティブCLI or JAR) — 任意の粗配線。
5. Pico SDK 2.x + gcc-arm-none-eabi (apt) + cmake、picotool(SDKから)。cc65 2.19 (apt)。ngspice 42 (apt)。
6. MCPは「あれば便利」: kicad-mcp-pro か mcp-server-kicad を1つ。実機系MCPはユーザーのデスクトップ側のみ。
7. 各ツールのKiCad 10書式対応(kiutils等)は導入後にERC/DRCで往復検証すること。
