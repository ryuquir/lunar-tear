# ツール・MCP調査 (KiCad / JLCPCB / ファームウェア / テスト) — 2026-11-10時点 (作業中ドラフト v1)

注: 本ファイルは段階保存中。「未確認」は検証できなかった項目。

## 1. コンテナ実機プローブ結果 (Ubuntu 24.04.5, apt-get update後)

### Takeaway
apt標準のKiCadは7.0.11で古く、KiCad 10系を使うにはPPAまたはDockerイメージが必要。PPA(10.0/9.0)とDocker Hub APIはプロキシ経由で到達可能、GitHub本体(github.com / api.github.com)へのcurlは403だがWebFetch経由では読める。

### Cited Findings
- apt-cache policy kicad の Candidate は 7.0.11+dfsg-1build4、Installed-Size 約146MB(本体のみ、依存は別)、ダウンロード約36MB — コンテナ実測 (`apt-cache policy kicad` / `apt-cache show kicad`)
- apt候補: gcc-arm-none-eabi 15:13.2.rel1-2、libnewlib-arm-none-eabi 4.4.0.20231231-2、cc65 2.19-1、ngspice 42+ds-3build1、openocd 0.12.0-1build2、sigrok-cli 0.7.2、pulseview 0.4.2、fceux 2.6.5+dfsg1-2build3、ghdl 4.1.0、iverilog 12.0、yosys 0.33、nextpnr-ice40 0.6 — コンテナ実測
- apt に無い: freerouting、picotool、pico-sdk、kikit — コンテナ実測 (候補なし)
- 到達性(curl -sSI, HTTPSプロキシ経由, HTTPコード): ppa.launchpadcontent.net/kicad/kicad-10.0-releases および kicad-9.0-releases の dists/noble/Release=200; hub.docker.com=200; registry.hub.docker.com/v2/repositories=200; registry-1.docker.io/v2/=401(認証要求=到達可); pypi.org=200; registry.modelcontextprotocol.io=200; gitlab.com=200; flathub.org=307(リダイレクト); dl.flathub.org/repo=403; github.com / api.github.com=403(curl); downloads.kicad.org=405(HEAD不可、到達はしている); ghcr.io/v2/=405; raw.githubusercontent.com=301 — コンテナ実測
- PPA: https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu/ (noble Release有り) と kicad-9.0-releases — コンテナ実測
- Docker Hub kicad/kicad: タグ 10.0.8 (約812MB圧縮), 10.0.8-full (約1.45GB圧縮) 、更新 2026-10-30 — https://registry.hub.docker.com/v2/repositories/kicad/kicad/tags
- KiCad最新安定版は 10.0.8 (2026-10-30)。10.0.7=2026-10-07, 10.0.6=2026-08-29, 10.0.5=2026-07-22 — https://www.kicad.org/blog/
- 注意: プロキシ設定では pypi.org, registry.npmjs.org 等はNO_PROXY(直接)。ghcr.io はHEAD 405だがpull可否は未確認 — `curl $HTTPS_PROXY/__agentproxy/status`

### Inferences
- コンテナへのKiCad導入は (a) PPA kicad-10.0-releases の apt、(b) kicad/kicad:10.0.8 Dockerイメージ中身の利用 のどちらかが現実的。Flatpakは dl.flathub.org が403のため不可。
- 注意: コンテナ内でDockerデーモンが使えるかは未確認。

### Gaps
- PPA経由でkicadをapt installした場合の実サイズ(依存込み)は未確認(大容量インストール禁止のため)。

## 2. PyPIパッケージ (JSON API実測)

### Cited Findings
| パッケージ | 最新版 | 最終アップロード | 判断 |
|---|---|---|---|
| kiutils | 1.4.8 | 2024-02-02 | 更新停止気味。KiCad 9/10の新書式未対応の恐れ(未確認) |
| kicad-skip | 0.2.5 | 2024-02-16 | 更新停止気味 |
| kicad-python (kipy, IPC API) | 0.8.0 | 2026-08-30 | 活発 |
| skidl | 3.0.0 | 2026-10-16 | 活発 |
| atopile | 0.15.9 | 2026-09-12 | 活発 (0.x) |
| easyeda2kicad | 1.0.1 | 2026-04-06 | 保守中 |
| JLC2KiCadLib | 1.3.2 | 2026-09-11 | 活発 |
| kibot | 1.9.1 | 2026-07-28 | 活発 |
| kikit | 1.8.1 | 2026-08-05 | 活発 |
| kicad-sch-api | 0.5.6 | 2025-11-19 | 1年近く更新なし |
| circuit-synth | 0.12.1 | 2026-01-09 | やや停滞 |
| kicad-mcp (PyPI) | 0.1.6 | 2026-04-20 | 未成熟 |
| kicad-mcp-server (bunnyf/pcb-mcp) | 3.5.0 | 2026-01-17 | — |
- 出典: https://pypi.org/pypi/<package>/json (各パッケージ名で実測)。pico-sdk(PyPI)は別物(2020, 無関係)。

## 3. MCPサーバ (公式レジストリ registry.modelcontextprotocol.io 検索結果)

| 名称 | URL | 状態 | headless | 判定 |
|---|---|---|---|---|
| ProductOfAmerica/mcp-server-kicad | https://github.com/ProductOfAmerica/mcp-server-kicad | v0.21.1 (2026-10-20)、109ツール(sch42/pcb34/project24)、GPL-3.0以降(0.20.1まではMIT)、★16、2026-10に「保守モード」宣言 | 概ねファイル直接解析+kicad-cli。fill_zones/autoroute_pcbはpcbnew Pythonと Java25+ Freerouting要 | 参考(保守モードのため推奨度中) |
| mixelpixx/KiCAD-MCP-Server | https://github.com/mixelpixx/KiCAD-MCP-Server | ★約3.3k、MIT、KiCad9+、Node18+/Python3.11+、JLCPCB部品カタログ・Freerouting統合。新開発はRust製Konnect(KiCad10 IPC, AGPL-3.0)へ移行と記載 | GUI要否は記載なし(未確認) | 要検証 nice-to-have |
| lamaalrajih/kicad-mcp | https://github.com/lamaalrajih/kicad-mcp | ★534、MIT、解析・BOM・kicad-cli DRC中心(編集系は弱い) | kicad-cli使用 | 読み取り専用用途のみ |
| oaslananka/kicad-mcp-pro | https://github.com/oaslananka/kicad-mcp-pro | v4.11.0(READMEより; レジストリ上は2.1.0=2026-04-15)、★206、MIT、stdio+Streamable HTTP、24読み取りツール既定+build/releaseプロファイル、JLCPCB公開カタログ検索 | コア機能はGUI不要(ツールバー連携のみPCB Editor要) | nice-to-have (レビュー用) |
| biosshot/kicad-copilot | https://github.com/biosshot/kicad-copilot | 0.1.0 (2026-08-09) | 未確認 | 未成熟 |
| daedalus/mcp-kicad | https://github.com/daedalus/mcp-kicad | 0.1.1 (2026-04-10) | 未確認 | 未成熟 |
| bunnyf/pcb-mcp (kicad-mcp-server) | https://github.com/bunnyf/pcb-mcp | 3.5.0 (2026-01-17) | 未確認 | 未確認 |
| PCBEditor/pcbeditor-mcp | https://github.com/PCBEditor/pcbeditor-mcp | 1.3.11 (2026-10-28), 商用/クラウド系の可能性(未確認) | 未確認 | 未確認 |
| oaslananka/easyeda-mcp-pro | https://github.com/oaslananka/easyeda-mcp-pro | 1.13.1 (2026-11-09), EasyEDA Pro拡張ブリッジ | GUI必須(EasyEDA Pro) | クラウド不可 |
| biosshot/easyeda-copilot | https://github.com/biosshot/easyeda-copilot | 1.3.2 (2026-10-15) | GUI必須 | 同上 |
| VLab-Software/easyeda_mcp | https://github.com/VLab-Software/easyeda_mcp | 1.0.2 (2026-05-26) | GUI必須 | 同上 |
| turbyho/datasheet-lens | https://github.com/turbyho/datasheet-lens | 0.6.1 (2026-11-10), データシートPDF索引/検索 | 未確認 | 試す価値あり |
| FelixNovaNexus/datasheet-vend | https://github.com/FelixNovaNexus/datasheet-vend | 1.1.0 (2026-10-27) | 未確認 | 未確認 |
| pipeworx-io/mcp-octopart | https://github.com/pipeworx-io/mcp-octopart | 0.2.1 (2026-11-03), Nexar API | APIキー要 | 低 |
| mrfentmen/digikey-mcp | https://github.com/mrfentmen/awesome-servers | 1.0.0 (2026-11-08) 汎用量産リポジトリの疑い | — | 信頼性低(未確認) |
| jl-codes/platformio-mcp | https://github.com/jl-codes/platformio-mcp | 3.1.0 (2026-09-25) | ビルド可・書込は実機 | Pico SDK直ビルドなら不要 |
| microhenrio/openocd-mcp | https://github.com/microhenrio/openocd-mcp | 0.4.5 (2026-07-02) | 実機要 | 実機デバッグ時のみ(デスクトップ) |
| qarnet/serial-mcp | https://github.com/qarnet/serial-mcp | 0.9.3 (2026-08-15) | 実機要 | デスクトップのみ |
| ctrlpi/pico-bay | https://github.com/ctrlpi/pico-bay | 0.9.34 (2026-11-08) | USB実機要 | デスクトップのみ |
- 出典: https://registry.modelcontextprotocol.io/v0/servers?search=<語> (実測) と各GitHub README(WebFetch)。
- レジストリで jlcpcb / lcsc / ngspice / probe-rs / wokwi / mouser / nexar の検索は0件 (実測)。

### Inferences
- 「KiCadファイルを直接編集するMCP」は乱立しているが成熟度は低く、GPL化・保守モード・Rust書き換え(Konnect)など流動的。エージェント(Claude Code)がkicad-cliとPython/テキスト編集を直接使う方がMCPより安定する可能性が高い。

### Gaps (以降のバージョンで調査継続)
- KiCad 10のIPC API/ヘッドレス可否、KiCad CLI機能、JLCPCB周辺ツール、ファーム/テストツールチェーン、計測機器は次回更新で追記。
