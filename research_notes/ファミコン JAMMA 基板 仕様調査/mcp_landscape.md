# MCP サーバ全景調査 (PCB設計・部品選定・回路シミュレーション・組込みFW) — 2026-11-10時点 (第2パス)

調査条件と凡例
- 「★」= GitHub スター数、「push」= GitHub の最終 push 日 (pushed_at)。いずれも 2026-11-10 に `gh api "search/repositories?q=repo:<owner>/<name>"` で取得 (GitHub Search API。`repos/…` 系と releases.atom は本セッションのプロキシで 403 だったため、最終 push 日を「最終コミット日」の代用とした)。
- 版数・公開日は PyPI JSON (`https://pypi.org/pypi/<name>/json`)、npm (`https://registry.npmjs.org/<name>`)、公式 MCP レジストリ (`https://registry.modelcontextprotocol.io/v0/servers?search=<語>&version=latest`) の実測値。
- README の内容は WebFetch 経由 (小型モデル要約) で取得したため、細部は原文確認を推奨。
- 「推論」= 筆者の工学的推論。「未確認」= 検証できなかった項目。
- WebSearch は本ターンの共有上限 (200回) に途中で到達したため、後半は既知URLの WebFetch・GitHub Search API・各レジストリAPIのみで調査した。

---

## 1. レジストリ横断スイープ (公式レジストリ / Glama / PulseMCP / mcp.so / Smithery / GitHub)

### Takeaway
KiCad 系 MCP は 2026-11 時点で少なくとも 40 件以上乱立している (Glama の "kicad" 検索だけで約40件+続き) が、★100超かつ継続保守されているのは mixelpixx/KiCAD-MCP-Server (★3,255)、oaslananka/kicad-mcp-pro (★206)、Seeed-Studio/kicad-mcp-server (★184) 程度。JLCPCB/LCSC 部品検索の MCP は公式レジストリの名前検索では 0 件だが、実際には多数存在し、最も実用的なのはホスト型・無認証の Averyy/pcbparts-mcp (★144)。

### Cited Findings
- 公式レジストリの `search` は名前の部分一致のみ (説明文は検索対象外) と判断: `search=jlcpcb`, `lcsc`, `tscircuit`, `atopile`, `ngspice`, `ltspice`, `freerouting`, `wokwi`, `probe-rs`, `rp2040`, `mouser`, `nexar` はいずれも 0 件だが、説明文に JLCPCB/LCSC を含むサーバ (例: `io.github.mo9652962-ai/circuit-agent-client` 「live LCSC parts」) は別語で見つかる — [registry API](https://registry.modelcontextprotocol.io/v0/servers?search=circuit&version=latest) (推論を含む)
- 公式レジストリ (version=latest) の KiCad 系 7 件: ProductOfAmerica/mcp-server-kicad 0.21.1 (2026-10-20), biosshot/kicad-copilot 0.1.0 (2026-08-09), bunnyf/kicad-mcp-server 3.5.0 (2026-01-17), daedalus/mcp-kicad 0.1.1 (2026-04-10), oaslananka/kicad-mcp-pro 4.11.0 (2026-11-10), turbyho/kicad-workbench 0.1.0 (2026-11-08), unmateria/mcp-kicad 0.2.7 (2026-08-10) — [registry search=kicad](https://registry.modelcontextprotocol.io/v0/servers?search=kicad&version=latest)
- 公式レジストリの EasyEDA 系 3 件: VLab-Software/easyeda-pro-mcp 1.0.2 (2026-05-26), biosshot/easyeda-copilot 1.3.2 (2026-10-15), oaslananka/easyeda-mcp-pro 1.13.1 (2026-11-09) — [registry search=easyeda](https://registry.modelcontextprotocol.io/v0/servers?search=easyeda&version=latest)
- 公式レジストリのその他関連: embedded-society/altium-designer-mcp 1.4.0, com.autodesk.aps.api/fusion-local-mcp 1.0.1 (「Must locally run Fusion」), com.pcbeditor/pcbeditor 1.3.11 (remote streamable-http), io.github.EasyGerber/easygerber 0.1.1 (remote), pipeworx-io/octopart 0.2.1, turbyho/datasheet-lens 0.6.1, com.datasheetvend/datasheet-contracts 1.1.0 (remote), io.whatic/datasheets 1.0.0 (remote), microhenrio/openocd-mcp 0.4.5, jl-codes/platformio-mcp 3.1.0, powerdragonfire/platformio.mcp 0.1.0 (PyPI上は 0.6.2), es617/serial-mcp-server 0.1.3, qarnet/serial-mcp 0.9.3, ctrlpi/pico-bay 0.9.34, KenosInc/sigrok-mcp-server 0.2.0, daedalus/mcp-sigrok 0.1.0, Zeraissh/stm32-gdb-mcp 0.15.1, es617/dbgprobe-mcp-server 0.1.4, stramanu/esp32sim-mcp 0.2.6, netchuu/tinkercad-circuits-mcp 0.1.0 — [registry](https://registry.modelcontextprotocol.io/v0/servers?search=pcb&version=latest) ほか各語
- `io.github.mrfentmen/*` は同一リポジトリ `mrfentmen/awesome-servers` から digikey-mcp・gdb-mcp・quartus-simulation-ip-mcp 等を大量登録 (digikey-mcp の npm 初版は 2026-11-01)。量産型でスパム/玩具と判断 — [registry search=digikey](https://registry.modelcontextprotocol.io/v0/servers?search=digikey&version=latest), [npm digikey-mcp](https://registry.npmjs.org/digikey-mcp)
- Glama: "kicad" で約40件 (+Load More)、License/Quality/Maintenance の A〜F 評価付き。M=A は ProductOfAmerica/mcp-server-kicad と mixelpixx/KiCAD-MCP-Server のみ — [Glama kicad](https://glama.ai/mcp/servers?query=kicad)
- Glama: "jlcpcb" で16件 (Averyy「PCB Parts MCP Server」が A/A/A、Eyalm321/jlcpcb-mcp A/A/C、hulryung/jlcpcb-skill-mcp A/A/C、peterb154/jlcpcb-search-mcp F/A/D ほか) — [Glama jlcpcb](https://glama.ai/mcp/servers?query=jlcpcb)
- Glama: "lcsc" で21件中、電子部品関連は jlcpcb-mcp, jlcpcb-skill-mcp, circuit-agent, eda-agent (Nivakaran-S), szlcsc-mcp (zhr1008, A/B/A), parts-mcp (Ngopad), easyeda-copilot-mcp, CircuitPilot, EasyEDA Standard MCP Server 等 — [Glama lcsc](https://glama.ai/mcp/servers?query=lcsc)
- Glama: "spice" で mcp-spice (zesun33, Apache-2.0, A/A/C, 2026-10-05), SPICEBridge (GPL-3.0, A/B/D), spicelib-mcp (GPL-3.0, A/A/D), microcap-mcp 等 — [Glama spice](https://glama.ai/mcp/servers?query=spice)
- Glama: "raspberry pi pico" で RP2040/RP2350/Pico SDK/picotool を扱うサーバは 0 件 (MicroPython 系 thonny-ai と HID 系 clawtouch-mcp のみ) — [Glama pico](https://glama.ai/mcp/servers?query=raspberry%20pi%20pico)
- Glama: "datasheet" で電子系14件 (datasheet-lens A/B/B, mcp-nexar A/A/D, trm-mcp, szlcsc-mcp 等) — [Glama datasheet](https://glama.ai/mcp/servers?query=datasheet)
- PulseMCP: "kicad" で10件。Seeed Studio「KiCad」、KiPilot、Partreel に "Official" ラベル (ツール提供元自身による公開の意と推論。KiCad 公式という意味ではない) — [PulseMCP](https://www.pulsemcp.com/servers?q=kicad)
- mcp.so: "kicad" で9件 (mixelpixx, oaslananka 3件 [kicad-mcp-pro / kicad-studio-kit / boardreadyops] ほか) — [mcp.so](https://mcp.so/search?q=kicad)
- Smithery: 検索ページはクライアント描画で取得不可 (`https://smithery.ai/search?q=kicad` は404、`registry.smithery.ai/servers?q=` は 500)。検索エンジン経由で `@lamaalrajih/kicad-mcp` (Remote, 要 Smithery API key) と `pit-here/whatic` (IC datasheets) のみ確認 — [Smithery lamaalrajih](https://smithery.ai/server/@lamaalrajih/kicad-mcp/api), [Smithery whatic](https://smithery.ai/servers/pit-here/whatic)
- GitHub 検索 "kicad mcp" (★順) 上位: mixelpixx/KiCAD-MCP-Server 3,255 / lamaalrajih/kicad-mcp 534 / salitronic/eda-agent 340 (Altium) / oaslananka/kicad-mcp-pro 206 / Seeed-Studio/kicad-mcp-server 184 / tangency-labs/pcbcraft-gpl 178 (独自Rust EDA) — [GitHub search](https://github.com/search?q=kicad+mcp&type=repositories&s=stars)
- 秋月電子 (Akizuki) の MCP サーバ・公開 API は、GitHub 検索 "akizuki" (購入履歴DLツール・Chrome拡張・新商品通知Bot等のみ) と各レジストリで見つからず — [GitHub search akizuki](https://github.com/search?q=akizuki&type=repositories)

### Inferences
- レジストリの数の多さは品質を意味しない。★・継続 push・テスト有無で絞ると実用候補は各分野1〜3件。
- 公式レジストリは「名前検索のみ」なので、レジストリだけでは JLCPCB/LCSC 系を見落とす (第1パスの「0件」はこの仕様による)。

### Gaps
- Smithery の網羅的検索は未実施 (UI がJS描画・API要キー)。WebSearch 上限到達後は Smithery を再試行できなかった。
- 秋月電子に非公開の API が存在するか否かは、公式サイト側での確認ができておらず 未確認。

---

## 2. 主要サーバ詳細表

### Takeaway
「クラウドのヘッドレスコンテナで本当に使えるもの」は、ファイル直接解析+kicad-cli 型 (kicad-mcp-pro、ProductOfAmerica、Seeed、mixelpixx の SWIG モード)、ホスト型 HTTP (pcbparts-mcp)、CLI ラッパ (spicebridge、Freerouting の stdio MCP、sigrok のファイルデコード) に限られる。KiCad の IPC API 依存 (Konnect の PCB ツール、daedalus、KiPilot 等) と EasyEDA Pro 系はすべて GUI 稼働が前提。

### Cited Findings — KiCad 系

| サーバ / URL | 保守者 | 最新版・日付 | ★ / push / ライセンス / open issues | 主な機能 | 輸送 | GUI要否・ヘッドレス | 品質シグナル・判定 |
|---|---|---|---|---|---|---|---|
| [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) | mixelpixx (個人) | README「What's New in v2.8.3」 | 3,255 / 2026-11-10 / MIT / 31 | 「251 tools across 20 categories」(別節では244と自己矛盾)。board, component, export, drc, schematic, library, routing, autoroute, jlcpcb, digikey, gui-driver 等。JLCPCB は「No API credentials needed」(JLCSearch + yaqwsx/jlcparts) と公式API (JLCPCB_API_KEY/SECRET) の3モード。Freerouting統合 (Java 21+ または Docker/Podman) | STDIO のみ | 「Automatically uses IPC when available, falls back to SWIG」。KiCad 9.0+ と pcbnew Python 必須。SWIG経路ならGUI不要と推論 (ただしKiCad 11でSWIG削除見込み) | テスト: v2.4.1注記「1551 Python and 63 TypeScript tests」。活発。巨大(ツール過多) |
| [mixelpixx/Konnect](https://github.com/mixelpixx/Konnect) | mixelpixx → Orchis.ai LLC | リリース記載なし | 1,458 / 2026-11-02 / AGPL-3.0 / **archived=true** | 「228 tools across 21 on-demand toolsets」(GitHub説明は217) Rust 単一バイナリ、KiCad 10 プラグイン | stdio 既定、Streamable HTTP 可 | 「For most PCB tools: KiCAD running with the target board open (IPC API)」。回路図編集のみKiCad不要 | アーカイブ済。後継 [Orchis-ai-LLC/Konnect-EDA](https://github.com/Orchis-ai-LLC/Konnect-EDA) は「commercial, closed-source」、1.0までは無料、1.0以降は「Every installation will need a license key」。Linux は「hasn't had per-platform QA yet」。フォーク [dylbertram/konnect-maintained](https://github.com/dylbertram/konnect-maintained) (AGPL維持, push 2026-11-10) |
| [oaslananka/kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro) | oaslananka (個人、同作者が easyeda-mcp-pro / kicad-studio-kit / boardreadyops / zaptrace も) | 4.11.0 (PyPI・npm・レジストリとも 2026-11-10) | 206 / 2026-11-10 / MIT / 21 | プロファイル制: `default`=24個の読み取りレビューツール、`build`=編集、`release`=製造出力(人手ゲート)、`expert/full`=全部。部品: JLCPCB公開カタログ既定、Nexar/DigiKey/Mouser はキー要 | stdio と Streamable HTTP (`/mcp`) | ERC/DRC/出力は KiCad エンジン(kicad-cli)。「PCB Editor Companion」(KiCad 10 IPC ツールバー) は read-only・開発プレビュー | CI, CodeQL, OpenSSF Scorecard バッジ。PyPI 63 リリース (2026-06-21〜)、npm 81 版 = 約5か月で極めて高頻度 (API安定性に注意)。README内でも parity 84.4% vs 76.6% の不一致 |
| [ProductOfAmerica/mcp-server-kicad](https://github.com/ProductOfAmerica/mcp-server-kicad) | ProductOfAmerica | 0.21.1 (PyPI 2026-10-20、計68リリース) | 16 / 2026-11-05 / GPL-3.0-or-later / 36 | 109ツール (回路図42/PCB34/プロジェクト24/シンボル5/フットプリント4)、Claude Code プラグイン+6スキル | ローカルコマンド起動 (`uvx --from mcp-server-kicad mcp-server-kicad`) = stdio と推論 | 大半はファイル直接解析で KiCad 不要、kicad-cli 使用、`fill_zones`/`autoroute_pcb` は pcbnew Python | 「As of October 2026 this project gets security fixes and KiCad compatibility fixes only.」作者テストで plugin あり 3/18 正解 vs 素の Claude Code 18/18。作者自身が「a coding agent such as Claude Code, with KiCad installed」を推奨。CI: Linux/macOS/Windows × Python 3.11〜3.14 |
| [Seeed-Studio/kicad-mcp-server](https://github.com/Seeed-Studio/kicad-mcp-server) | Seeed Studio (企業) | README に版記載なし | 184 / 2026-10-22 / GitHubはライセンス未検出 (READMEは「MIT」) / 6 | 24ツール: 回路図/PCB/ネットリスト解析、run_erc/run_drc (kicad-cli)、detect_pin_conflicts、簡易編集、export_gerber | stdio | 「kicad-cli in PATH」、ERC/DRC は「headless, CI friendly」、PCB詳細解析は KiCad 同梱 Python の pcbnew | テスト記載なし。解析・レビュー寄り |
| [lamaalrajih/kicad-mcp](https://github.com/lamaalrajih/kicad-mcp) | lamaalrajih | — | 534 / **2025-10-17** / MIT / 24 | プロジェクト一覧・BOM・DRC・可視化 | stdio (Smithery では Remote 版あり) | kicad-cli | 約13か月 push なし → 実質停滞 (Glama M=D) |
| [turbyho/kicad-workbench](https://github.com/turbyho/kicad-workbench) | turbyho | 0.1.0 (2026-11-08) | 0 / 2026-11-08 / MIT | KiCad 8/9/10 の回路図・基板・ERC/DRC/BOM | stdio | 未確認 | 作成6日の新作。評価不能 |
| [nevenfo/kicad-agentic-mcp](https://github.com/nevenfo/kicad-agentic-mcp) | nevenfo | — | 13 / 2026-11-09 / AGPL-3.0 / 9 | KiCad 10 ネイティブプラグイン、Glama では「202 tools; verifies via kicad-cli」 | 未確認 | KiCad 10 プラグイン (GUI前提と推論) | 若い |
| [belaszalontai/kipilot-mcp](https://github.com/belaszalontai/kipilot-mcp) | Béla Szalontai | — | 16 / 2026-10-29 / Apache-2.0 | 「live KiCad PCB workflow」 | 未確認 | GUI(ライブ)前提 | 未調査 |
| [daedalus/mcp-kicad](https://github.com/daedalus/mcp-kicad) | daedalus (大量の小MCPを量産) | 0.1.1 (2026-04-10) | 1 / 2026-04-21 / MIT | IPC API 経由の PCB Editor 操作 | stdio | GUI 必須 | 玩具級 |
| [bunnyf/pcb-mcp](https://github.com/bunnyf/pcb-mcp) | bunnyf | 3.5.0 (2026-01-17、PyPI 1リリースのみ) | 11 / 2026-01-17 / MIT (PyPI表記はGPL) | KiCad 9.x | — | 未確認 | 停滞、ライセンス表記不一致 |
| [biosshot/kicad-copilot](https://github.com/biosshot/kicad-copilot) | biosshot | 0.1.0 (npm 2026-08-09) | 23 / 2026-08-23 / MIT | ファイル指向の回路図・配置・配線・ベタ | stdio | 不要 (file-oriented) | 版1つのみ |
| [circuit-synth/mcp-kicad-sch-api](https://github.com/circuit-synth/mcp-kicad-sch-api) | circuit-synth | — | 22 / 2025-08-20 / MIT | 回路図操作 | — | 不要 | 停滞 (15か月) |
| [blwfish/kicad-mcp](https://github.com/blwfish/kicad-mcp) | blwfish | — | 29 / 2026-11-09 / MIT | 「71 tools」 | — | 未確認 | 未調査 |

出典 (★/push/ライセンス): 各行のリポジトリURLに対する `gh api search/repositories?q=repo:...` 実測。各 README は行頭リンク先 (README は [mixelpixx raw README](https://raw.githubusercontent.com/mixelpixx/KiCAD-MCP-Server/main/README.md), [Konnect raw README](https://raw.githubusercontent.com/mixelpixx/Konnect/main/README.md), [kicad-mcp-pro raw README](https://raw.githubusercontent.com/oaslananka/kicad-mcp-pro/main/README.md), [ProductOfAmerica raw README](https://raw.githubusercontent.com/ProductOfAmerica/mcp-server-kicad/main/README.md), [Seeed raw README](https://raw.githubusercontent.com/Seeed-Studio/kicad-mcp-server/main/README.md))。版数は [PyPI kicad-mcp-pro](https://pypi.org/pypi/kicad-mcp-pro/json), [PyPI mcp-server-kicad](https://pypi.org/pypi/mcp-server-kicad/json), [npm kicad-mcp-pro](https://registry.npmjs.org/kicad-mcp-pro)。

### Cited Findings — 部品データ (JLCPCB/LCSC/流通)

| サーバ / URL | 最新・状態 | ★ / push / ライセンス | 機能 | 輸送・認証 | ヘッドレス | 判定 |
|---|---|---|---|---|---|---|
| [Averyy/pcbparts-mcp](https://github.com/Averyy/pcbparts-mcp) | ホスト版 `/health` は version 0.8.24、MCP initialize の serverInfo.version は "3.4.3" (2系統の版表記、どちらが製品版か未確認) | 144 / 2026-11-10 / MIT | 14ツール (実測 tools/list): jlc_stock_check, jlc_search, jlc_search_help, jlc_get_part, jlc_find_alternatives, jlc_get_pinout, mouser_get_part, digikey_get_part, cse_search, cse_get_kicad, sensor_recommend, get_design_rules, board_search, board_get。`library_type` = basic / preferred / no_fee / extended / all | ホスト `https://pcbparts.dev/mcp` (Streamable HTTP, stateless, 認証なし, 100 req/min/IP)、自前ホストも可 (`uv run python -m pcbparts_mcp.server` → `http://localhost:8080/mcp` / Docker)。Mouser/DigiKey は共有キーで各 1,000 req/日 | 可 (HTTP) | 本プロジェクトで最有用。ただし第三者運営の無料サービスで SLA なし |
| [tscircuit/jlcsearch](https://github.com/tscircuit/jlcsearch) (MCPではなくHTTP API) | 毎日同期 | 40 / 2026-11-06 / MIT / open issues 295 | `https://jlcsearch.tscircuit.com/components/list.json?search=...` で JSON (is_basic / is_preferred / stock / 価格段階) | HTTP GET、無認証 | 可 | MCP不要の素直な代替 |
| [Eyalm321/jlcpcb-mcp](https://github.com/Eyalm321/jlcpcb-mcp) | — | 2 / 2026-06-03 / MIT | jlcparts SQLite + ライブ在庫・価格・データシート・注文 | stdio | 可 | 若く停滞気味 |
| [nvsofts/jlcpcb-parts-mcp](https://github.com/nvsofts/jlcpcb-parts-mcp) | — | 33 / **2025-04-20** / GPL-3.0 | 「JLCPCB PCBA向けの、部品探しを補助するためのMCPサーバー」(日本語) | — | 可 | 19か月停滞 → 放棄扱い (README raw は404で詳細未取得) |
| [hulryung/jlcpcb-skill-mcp](https://github.com/hulryung/jlcpcb-skill-mcp) | — | 4 / 2026-10-26 / ライセンス未検出 | KiCad BOM 解析・Tier/手数料考慮の部品提案 + Claude Code skill | — | 可 | 小規模 |
| [peterb154/jlcpcb-search-mcp](https://github.com/peterb154/jlcpcb-search-mcp) | — | 9 / 2026-04-29 / なし | 450K+ カタログ検索 | — | 可 | ライセンス無し → 不採用 |
| [zhr1008/component-sourcing-mcp](https://github.com/zhr1008/component-sourcing-mcp) | — | 1 / 2026-10-29 / MIT | SZLCSC(立創商城)/JLCPCB 在庫・CNY価格・データシート | — | 可 | 中国国内向け |
| [pipeworx-io/mcp-octopart](https://github.com/pipeworx-io/mcp-octopart) | npm 0.2.1 (2026-11-03) | 0 / 2026-11-09 / MIT | Nexar Supply API (GraphQL) | stdio + remote | 可 (Nexarキー要) | pipeworx は汎用MCP量産業者。低 |
| [SpectraSynq/mcp-nexar](https://github.com/SpectraSynq/mcp-nexar) | — | 0 / 2026-07-13 / Apache-2.0 | Nexar/Octopart 検索・データシートURL | — | 可 (キー要) | 低 |
| [bengineer19/digikey_mcp](https://github.com/bengineer19/digikey_mcp) | — | 36 / 2025-06-28 / なし | DigiKey | — | キー要 | 停滞 |
| [JPMarhefka/Partuno](https://github.com/JPMarhefka/Partuno) | — | 7 / 2026-10-29 / Apache-2.0 | DigiKey+Mouser 検索・BOM | — | キー要 | 低 (本件は JLCPCB/秋月中心) |

- 実測 (2026-11-10): pcbparts `jlc_search(query="74HC245", library_type="basic")` → basic 0件、「1 preferred … and 14 extended」(data_as_of 2026-11-10T20:13:31Z)。jlcsearch `list.json?search=74HC245` でも is_basic=True は0件、C5625 (74HC245D,653, SOIC-20-300mil, 在庫52,801) のみ is_preferred=True。2ソース一致 — [pcbparts MCP](https://pcbparts.dev/mcp) (curl で JSON-RPC 実行), [jlcsearch](https://jlcsearch.tscircuit.com/components/list.json?search=74HC245&limit=20)

### Cited Findings — 他EDA (Altium / Fusion / tscircuit / atopile / EasyEDA)

| 対象 | サーバ | 状態 | GUI要否 | 判定 |
|---|---|---|---|---|
| Altium | [salitronic/eda-agent](https://github.com/salitronic/eda-agent) ★340, Apache-2.0, push 2026-11-10「drive a live session of Altium Designer」/ [coffeenmusic/altium-mcp](https://github.com/coffeenmusic/altium-mcp) ★219 MIT / [embedded-society/altium-designer-mcp](https://github.com/embedded-society/altium-designer-mcp) ★91 GPL-3.0 (ライブラリ管理) | 活発 | Altium (Windows) 稼働必須 | 本件スキップ (KiCad/JLCPCB 前提、Altium は高価) |
| Fusion Electronics | Autodesk公式 `com.autodesk.aps.api/fusion-local-mcp` 1.0.1「Must locally run Fusion」/ [groundplane-studio/fusion-electronics-mcp](https://github.com/groundplane-studio/fusion-electronics-mcp) ★6 | — | Fusion 稼働必須 | スキップ |
| tscircuit | 公式MCPは見つからず (tscircuit/cli のコード検索で "mcp" は bun.lock のみ)。コミュニティ [charlielockyer-rice/tscircuit-mcp](https://github.com/charlielockyer-rice/tscircuit-mcp) ★3, push 2025-07-09 | 停滞・玩具 | — | スキップ (npm `tscircuit` 0.0.3146 は活発だが MCP 不要) |
| atopile | **本体内蔵MCPあり**: `src/atopile/cli/mcp.py` の `start(http: bool = False, ...)`「Start the MCP server.」、ツール `build_project`, `search_and_install_jlcpcb_part`, `install_package`, `verify_package`, `find_project_from_filepath`, `inspect_library_module_or_interface`, `get_library_modules_or_interfaces`, `inspect_package`, `find_packages` | atopile ★4,056 MIT, push 2026-10-14 | ヘッドレス可 (CLI) と推論 | atopile を採用する場合のみ有用 |
| EasyEDA/JLCEDA | 公式 org `easyeda` (公式文書が SDK として github.com/easyeda/pro-api-sdk を案内) の [easyeda/easyeda-client-cli](https://github.com/easyeda/easyeda-client-cli) (Apache-2.0, ★21, push 2026-11-02): 「Running as an MCP server」機能、「The CLI requires the **desktop client** of EasyEDA Pro; the browser / online edition does not support sessions and the bridge」、client V4.1.70 以上。[easyeda/easyeda-api-skill](https://github.com/easyeda/easyeda-api-skill) ★1,083 (Skill + Node WebSocket bridge、port 49620-49629、MCPではない)。[easyeda/extension-dev-mcp-tools](https://github.com/easyeda/extension-dev-mcp-tools) (拡張開発のデバッグ用) | 公式orgで活発 | デスクトップクライアント稼働必須 | EasyEDA を使う場合のみ (デスクトップ側) |
| EasyEDA 第三者 | [oaslananka/easyeda-mcp-pro](https://github.com/oaslananka/easyeda-mcp-pro) ★69 (npm 1.13.1, 2026-11-09, 96版), [biosshot/easyeda-copilot](https://github.com/biosshot/easyeda-copilot) ★217, [hyl64/jlcmcp](https://github.com/hyl64/jlcmcp) ★272 (「基于官方 Run API Gateway」), [zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent) ★1,008 (ライセンス NOASSERTION), [VLab-Software/easyeda_mcp](https://github.com/VLab-Software/easyeda_mcp) ★42 | 活発 | いずれも EasyEDA Pro 拡張ブリッジ経由で GUI 稼働必須 | デスクトップ側・任意 |

### Cited Findings — データシート/PDF

| サーバ | 状態 | 機能 | 判定 |
|---|---|---|---|
| Claude Code 標準 Read ツール (MCP ではない) | — | 「For PDFs longer than 10 pages, it reads in ranges with a `pages` parameter … up to 20 pages at a time. Page-range reads render pages with `pdftoppm` from poppler-utils」 — [tools reference](https://code.claude.com/docs/en/tools-reference) | 第一選択。`apt-get install poppler-utils` だけ |
| [I-CAN-hack/pdf-mcp](https://github.com/I-CAN-hack/pdf-mcp) ★82, MIT(GitHub検出), push 2026-10-19 | uvx 起動 | get_pdf_info, get_table_of_contents, get_page_text, get_page_image (DPI既定150), search_text。PyMuPDF 2 | 数百頁の RP2040/RP2350 データシート全文検索に有用 |
| [turbyho/datasheet-lens](https://github.com/turbyho/datasheet-lens) 0.6.1 (PyPI 2026-11-10, 7リリース, 初版2026-10-29) ★0 MIT | README「in development (version 0.4) … The interfaces can change.」(PyPI 版と不一致) | 索引・ページ/領域抽出、BOMチェック、JLCPCB ローカル部品ライブラリ(276 MB)、stdio | 若すぎる。様子見 |
| `com.datasheetvend/datasheet-contracts`, `io.whatic/datasheets` (remote) | — | データシート→JSON、IC 検索 | 商用サービス、未評価 |

### Cited Findings — SPICE / オートルータ

| サーバ | 状態 | 機能・要件 | 判定 |
|---|---|---|---|
| [clanker-lover/spicebridge](https://github.com/clanker-lover/spicebridge) PyPI 1.3.0 (2026-02-13), ★45, push 2026-04-06, GPL-3.0-or-later, open issues 10 | 7か月 push なし | 28ツール (run_ac_analysis, run_transient, run_dc_op, measure_*, run_monte_carlo, run_worst_case, export_kicad[KiCad 8 .kicad_sch] 等)。「ngspice installed and on PATH」。stdio と `--transport streamable-http` | 任意。ngspice 直叩きで足りる |
| [Cognitohazard/ltspice-mcp](https://github.com/Cognitohazard/ltspice-mcp) PyPI ltspice-mcp 0.8.0 (2026-11-06)、★70, GPL-3.0-or-later, 1,797 commits | 「Work in progress. Expect breaking changes」 | LTspice (Windows/WSL2/Linux は Wine)、ngspice でも可、QSPICE/Xyce は副。8ツール。stdio | 活発だが LTspice 前提。ngspice 経路なら可 |
| [lucasgerads/spicelib-mcp](https://github.com/lucasgerads/spicelib-mcp) 0.1.5 (2026-04-15), GPL-3.0 | 停滞 | spicelib 経由 | スキップ |
| [gtnoble/ngspice-mcp](https://github.com/gtnoble/ngspice-mcp) ★19, push 2025-04-13 | 放棄 | — | スキップ |
| Freerouting 公式 MCP — [MCP Guide](https://raw.githubusercontent.com/freerouting/freerouting/master/docs/API/MCP.md) | freerouting ★2,206, GPL-3.0, push 2026-11-10。npm `@freerouting/freerouting-mcp-server` 2.5.0 (2026-10-05)、初版 2026-06-16、GPL-3.0-only | Option A: npx ブリッジ → Freerouting Public API (`FREEROUTING_API_KEY`)。Option B: ローカル `java -jar freerouting.jar --api_server.enabled=true --api_server.authentication.enabled=false --mcp_server.enabled=true --mcp_server.authentication.enabled=false --mcp_server.stdio=true --gui.enabled=false`。1ターン複合ツール `autoroute_board` (filePath/rulesPath/outputFormats ["SES","DRC_SUMMARY"]/timeoutSeconds) | Option B はヘッドレス可。ただし CLI で .dsn→.ses を回すだけなら MCP 不要 |
| easyeda/easyeda-pcb-router — [GitHub](https://github.com/easyeda/easyeda-pcb-router) GPL-3.0 | 「基于Freerouting实现的无GUI版自动布线服务」 | EasyEDA 向け | 参考 |

### Cited Findings — 組込み (デバッグ・シリアル・ロジアナ・シミュレーション)

| サーバ | 状態 | 機能 | 実機要否 | 判定 |
|---|---|---|---|---|
| [Adancurusul/embedded-debugger-mcp](https://github.com/Adancurusul/embedded-debugger-mcp) ★217, MIT, push 2026-07-16, Rust | release checks (rustfmt, clippy, cargo test 等) | 24ツール: list_probes, connect, halt/run/reset/step, read/write_memory, breakpoints, diagnose_fault, flash_erase/program/verify, run_firmware, rtt_attach/read/write。probe-rs または OpenOCD (GDB RSP) バックエンド。プローブ: ST-Link, J-Link, DAPLink, Black Magic Probe, FTDI。stdio | SWD プローブ実機必須 | デスクトップ側で有用。RP2040/RP2350 の明記なし (probe-rs が CMSIS-DAP=Raspberry Pi Debug Probe に対応することは本パスで未確認) |
| [okhsunrog/flashprobe-mcp](https://github.com/okhsunrog/flashprobe-mcp) ★6 / [Klievan/jlink-mcp](https://github.com/Klievan/jlink-mcp) ★43 / [microhenrio/openocd-mcp](https://github.com/microhenrio/openocd-mcp) ★5 (PyPI 0.4.5, 2026-07-02) / [luiox/openocd-mcp](https://github.com/luiox/openocd-mcp) ★10 | 小規模 | flash/RTT、J-Link/OpenOCD | 実機必須 | 代替。小規模のため優先度低 |
| [qarnet/serial-mcp](https://github.com/qarnet/serial-mcp) ★19, MIT, push 2026-11-10, Rust, レジストリ 0.9.3 (Linux x86_64/aarch64 バイナリ配布) | 活発 | 「25 tools」シリアルポート | USB 実機必須 | デスクトップ側で有用 (Pico の USB CDC ログ監視) |
| [es617/serial-mcp-server](https://github.com/es617/serial-mcp-server) ★27, PyPI 0.1.3 (2026-03-07) | 停滞気味 | list/connect/send/read | 実機必須 | 代替 |
| [KenosInc/sigrok-mcp-server](https://github.com/KenosInc/sigrok-mcp-server) ★15, MIT, push 2026-10-28, Go, open issues 12, ghcr イメージ 0.2.0 | 活発 | 11ツール (scan_devices, capture_data, decode_protocol, list_supported_decoders 等)。Docker は `--privileged` で USB。「works without firmware for devices that don't need it (e.g. demo, protocol-only analysis)」 | キャプチャは実機、デコードはファイルで可 | デスクトップ側で有用。クラウドでは sigrok-cli 直で十分 |
| [jl-codes/platformio-mcp](https://github.com/jl-codes/platformio-mcp) ★54, MIT, npm 3.1.0 (2026-09-25) / [powerdragonfire/platformio.mcp](https://github.com/powerdragonfire/platformio.mcp) PyPI 0.6.2 (2026-11-10, 初版 2026-09-16) | 活発 | build/flash/monitor/size_report/decode_backtrace | ビルドは不要、書込は実機 | Pico SDK (CMake) 直なら不要 → スキップ |
| [ctrlpi/pico-bay](https://github.com/ctrlpi/pico-bay) npm 0.9.34 (2026-11-06) ★9 | — | MicroPython/CircuitPython の Pico/ESP32 管理 | 実機必須 | C/Pico SDK 開発には不適 → スキップ |
| Pico SDK / picotool 専用 MCP | 見つからず (公式レジストリ search=pico, rp2040, pico-sdk / Glama / GitHub "raspberry pi pico mcp") | — | — | 「MCP 不要、CLI 直」 |
| Wokwi 公式 (wokwi-cli 内蔵) — [docs](https://docs.wokwi.com/wokwi-ci/mcp-support) | wokwi/wokwi-cli ★72, MIT, push 2026-10-23 | 「includes an experimental MCP server」、`"command": "wokwi-cli", "args": ["mcp"]`、「You will need a valid Wokwi CLI token」(`WOKWI_CLI_TOKEN`)、stdio。ツール名は文書に列挙なし | 実機不要。ただし「The simulation runs in the cloud」、無料枠「50 minutes」/30日、1セッション「5 minutes」 — [getting started](https://docs.wokwi.com/wokwi-ci/getting-started) | 任意 (Pico ファーム CI)。RP2350/PIO 対応は本パス未確認 |
| [wokwi/rp2040js](https://github.com/wokwi/rp2040js) (MCPではない) | ★536, MIT, push 2026-10-18 | JS 製 RP2040 エミュレータ | — | 第1パスの「所在不明」を解消 |

### Inferences
- KiCad 系で「IPC API 必須」のもの (Konnect PCB ツール、daedalus、KiPilot、kicad-mcp-pro の Companion) はクラウドコンテナでは使えない。KiCad 開発者が IPC のヘッドレスモードを「未実装」としている (第1パス引用) ため (推論)。
- kicad-mcp-pro は約5か月で PyPI 63 リリースという異常な頻度で、版を固定 (`uvx kicad-mcp-pro==4.11.0`) しないと再現性が崩れる (推論)。

### Gaps
- 各サーバの「最新コミット日」は GitHub API 制限により push 日で代用。releases 一覧は取得不能。
- Seeed / blwfish / nevenfo / KiPilot / kicad-workbench の実ツール動作は未検証 (README 要約のみ)。
- Wokwi MCP の具体ツール名、RP2350・PIO 対応は 未確認。

---

## 3. 第1パスの未解決事項の決着

### Takeaway
(1) kicad-mcp-pro の版不整合は第1パスの読み違い、(2) ProductOfAmerica は 2026-10 から保守モード・0.20.1 以前は MIT・以後 GPL-3.0-or-later、(3) mixelpixx 本体 (MIT) は継続中だが Konnect は 2026-11 にアーカイブされ商用クローズドの Konnect-EDA へ移行、(4) KiCad・JLCPCB・LCSC の公式 MCP は存在せず、EasyEDA は公式 org の CLI に MCP モードがあるがデスクトップクライアント必須。

### Cited Findings
- kicad-mcp-pro: 公式レジストリは版履歴を全件返し、2.1.0 (publishedAt 2026-04-15) は最古エントリで `isLatest=false`。最新は 4.11.0 (2026-11-10)。PyPI・npm も 4.11.0 (2026-11-10) — [registry search=kicad-mcp-pro](https://registry.modelcontextprotocol.io/v0/servers?search=kicad-mcp-pro&limit=100), [PyPI](https://pypi.org/pypi/kicad-mcp-pro/json), [npm](https://registry.npmjs.org/kicad-mcp-pro)
- kicad-mcp-pro の GitHub リポジトリ作成日は 2026-05-31 だが、レジストリ初登録 2.1.0 は 2026-04-15、PyPI の最古ファイルは 3.13.0 (2026-06-21)。旧版の PyPI ページは検索結果に存在 (例 2.1.0, 2.3.x) — [GitHub search](https://github.com/oaslananka/kicad-mcp-pro), [pypi.org/project/kicad-mcp-pro/2.1.0](https://pypi.org/project/kicad-mcp-pro/2.1.0/)。renovate-bot のミラー `renovate-bot/oaslananka-lab-_-kicad-mcp-pro` があることから、旧 org `oaslananka-lab` からの移管と推論 (未確認)。
- ProductOfAmerica: 「As of October 2026 this project gets security fixes and KiCad compatibility fixes only. … No new tools or features are planned. Existing installs keep working.」「Releases up to and including 0.20.1 were MIT-licensed; see NOTICE.」PyPI のライセンス表記 GPL-3.0-or-later、最新 0.21.1 (2026-10-20) — [README](https://raw.githubusercontent.com/ProductOfAmerica/mcp-server-kicad/main/README.md), [PyPI](https://pypi.org/pypi/mcp-server-kicad/json)。GitHub 説明文も「Maintenance mode: security and KiCad compatibility fixes only」— [GitHub](https://github.com/ProductOfAmerica/mcp-server-kicad)
- mixelpixx/KiCAD-MCP-Server: README「Konnect … is where new development happens」かつ本体は「remains fully open (MIT) and maintained」。push 2026-11-10 — [README](https://raw.githubusercontent.com/mixelpixx/KiCAD-MCP-Server/main/README.md)
- mixelpixx/Konnect: GitHub `archived: true` (作成 2026-07-05、最終 push 2026-11-02)。README「This repository is being archived, which makes it read-only. Development continues at Konnect-EDA, from Orchis.ai LLC.」— [Konnect README](https://raw.githubusercontent.com/mixelpixx/Konnect/main/README.md)
- Konnect-EDA: 「Konnect-EDA is commercial, closed-source software from Orchis.ai LLC.」「Until version 1.0, anyone can download and use Konnect-EDA free of charge」「Every installation will need a license key, free ones included.」Releases は空 — [Orchis-ai-LLC/Konnect-EDA](https://github.com/Orchis-ai-LLC/Konnect-EDA)
- KiCad 公式: GitHub org `KiCad` (ミラー) と GitLab に公式 MCP なし。GitLab 課題に MCP 利用者からの API 要望が多数 (例 #24803「expose RevertDocument via IPC API (silent reload for external/MCP edits)」→ milestone 11.0, fix-committed; #25666「schematic variant commands in 10.0.x」は Konnect を名指し) — [GitLab issues search=MCP](https://gitlab.com/api/v4/projects/kicad%2Fcode%2Fkicad/issues?search=MCP), [#24803](https://gitlab.com/kicad/code/kicad/-/work_items/24803), [#25666](https://gitlab.com/kicad/code/kicad/-/work_items/25666)
- KiCad ヘッドレス関連: #25413「crash kicad-cli pcb drc when there is no window server and there are DRC violations」(macOS, 10.0.4) は milestone 10.0.7 で fix-committed — [#25413](https://gitlab.com/kicad/code/kicad/-/work_items/25413)
- JLCPCB 公式 API: PCB API / Stencil API / 3D Printing API / Components API、「apply for free API access」。MCP 記載なし — [api.jlcpcb.com](https://api.jlcpcb.com/)。「Not all applications will be approved」、過去の注文・会社・事業状況で審査、"Last updated on Nov 10, 2026" — [JLCPCB help](https://jlcpcb.com/help/article/jlcpcb-online-api-available-now)
- LCSC 公式 API: Products (Category, Manufacturer, Item Details, Keyword Search「maximum of 30 parts per page」)、Orders、Shipment。認証は key/nonce/signature/timestamp — [LCSC OpenAPI](https://www.lcsc.com/docs/openapi/index.html)。「Apply for free API access. We'll send you the credentials after our review.」MCP 記載なし。Luminovo と CalcuQuote に API 提供を許諾 — [lcsc.com/agent](https://www.lcsc.com/agent)
- EasyEDA Pro Extension API: 「a set of JS API interfaces built on the front-end」— [prodocs guide](https://prodocs.easyeda.com/en/api/guide/)。SDK は「https://github.com/easyeda/pro-api-sdk」— [pro-api-sdk page](https://prodocs.easyeda.com/en/api/guide/ancillary-projects/pro-api-sdk.html)。同 org の easyeda-client-cli に MCP サーバモード (デスクトップクライアント必須) — [easyeda-client-cli](https://github.com/easyeda/easyeda-client-cli)

### Inferences
- 「公式」に最も近い EDA 系 MCP は EasyEDA の easyeda-client-cli (公式 org) と Autodesk の fusion-local-mcp のみで、どちらも GUI アプリ稼働前提。KiCad/JLCPCB/LCSC に公式 MCP は無い。
- JLCPCB/LCSC 公式 API は審査制・注文実績重視で、個人の新規プロジェクトが短期に取得できる保証はない。部品選定は公開データ (jlcsearch, CDFER DB, pcbparts) で十分 (推論)。

### Gaps
- KiCad 開発者が MCP について公式見解を出したかは、WebSearch 上限到達のため devlist/フォーラムを追加確認できず 未確認。
- JLCPCB API 審査の具体的な基準・期間は 未確認。

---

## 4. Claude Code への MCP 接続方法 (公式文書)

### Takeaway
ローカルでは `claude mcp add` (local/user スコープ = `~/.claude.json`) か、リポジトリにコミットする `.mcp.json` (project スコープ) で追加する。クラウドセッション (claude.ai/code) で効くのは「リポジトリにコミットした `.mcp.json`」と「claude.ai で追加した connector」だけで、`~/.claude.json` のサーバやリポジトリ設定で有効化したプラグインは持ち込まれない。stdio サーバはクラウド VM 内で起動され、その通信は環境のネットワーク許可リストに従う。connector は Anthropic 経由なので許可リスト不要。

### Cited Findings
- スコープ表: Local=`~/.claude.json` (既定)、Project=「`.mcp.json` in project root」(バージョン管理で共有)、User=`~/.claude.json`。優先順位「1. Local scope 2. Project scope 3. User scope 4. Plugin-provided servers 5. claude.ai connectors」、フィールドはスコープ間でマージされない — [Claude Code MCP](https://code.claude.com/docs/en/mcp)
- コマンド: `claude mcp add [options] <name> -- <command> [args...]`、`--` 以降はサーバへそのまま渡る。HTTP は `claude mcp add --transport http <name> <url>`、`--header "Authorization: Bearer ..."`、`--scope project`、SSE は非推奨。`claude mcp add-json <name> '<json>'`、`claude mcp add-from-claude-desktop` — 同上
- `.mcp.json` 形式 `{"mcpServers": {"name": {"type": "http", "url": "..."}}}`、環境変数展開 `${VAR}` / `${VAR:-default}` を `command`, `args`, `env`, `url`, `headers` で使用可。リモートの `url`/`headers` では `ANTHROPIC_API_KEY`, `HTTPS_PROXY`, `NPM_TOKEN` 等の資格情報変数は空として扱われる — 同上
- 対話セッションでは project スコープのサーバ使用前に承認プロンプト (`claude mcp reset-project-choices` でリセット)。「In `claude -p` runs, Agent SDK sessions, and cloud sessions outside a project's threads, Claude Code can't show that prompt and loads project-scoped servers without asking.」除外は `disabledMcpjsonServers` / `--strict-mcp-config` — 同上
- 制限: `MCP_TIMEOUT` (起動タイムアウト)、出力は 10,000 トークン超で警告・既定上限 25,000 (`MAX_MCP_OUTPUT_TOKENS`)、サーバごとの `"timeout"`、`MCP_TOOL_TIMEOUT`。Tool search は既定 ON (`ENABLE_TOOL_SEARCH=false` で無効、`alwaysLoad`) — 同上
- claude.ai connectors: 「Add servers at claude.ai/customize/connectors. On Team and Enterprise plans, only admins can add servers.」claude.ai サブスクリプションでログイン時のみ取得。`disableClaudeAiConnectors` / `ENABLE_CLAUDEAI_MCP_SERVERS=false` は Claude Code 自身が取得する connector にのみ作用。クラウドセッションでは「The cloud host passes them in」— 同上 (後半, offset 100000)
- プラグイン同梱 MCP: プラグイン直下 `.mcp.json` または `plugin.json` 内、`${CLAUDE_PLUGIN_ROOT}`、ツール名 `mcp__plugin_<plugin>_<server>__<tool>` — 同上
- クラウドで持ち込まれるもの: 「Your repo's `.mcp.json` MCP servers | Yes, in a session with one repository」/「MCP servers you added with `claude mcp add` at the default local scope or the user scope | No … Add the server with `claude mcp add --scope project` … and commit that file.」/「Plugins and marketplaces declared in your repo's `.claude/settings.json` | No」— [cloud environments](https://code.claude.com/docs/en/cloud-environments)
- ネットワーク: アクセスレベルは None / Limited / Full の3つ (旧 Trusted は Limited+Allow package managers、旧 Custom は Limited+Allowed domains として開く)。新規環境は Limited+Allow package managers。「MCP connectors you enable on a session or scheduled task work without adding their hosts to **Allowed domains**, because connector traffic travels through Anthropic's servers rather than the session's network.」— 同上
- 既定許可リストには github.com, api.github.com, raw.githubusercontent.com, codeload.github.com, ghcr.io, registry-1.docker.io, gitlab.com, registry.gitlab.com, archive.ubuntu.com, *.ubuntu.com, ppa.launchpad.net, launchpad.net, pypi/npm/crates 等。pcbparts.dev, jlcsearch.tscircuit.com, wokwi.com, freerouting.app, jlcpcb.com, lcsc.com は含まれない (取得した一覧の範囲内で) — 同上。`ppa.launchpadcontent.net` は一覧に見当たらず (第1パスの PPA 導入手順に影響しうる。未確認)
- VM: Ubuntu 24.04 x86_64、4 vCPU / 16 GB RAM / 30 GB disk 目安、Python+uv、Node 20/21/22、OpenJDK 21、GCC/Clang/cmake/ninja、Docker (docker, dockerd, compose)、Chrome for Testing。セットアップスクリプトは約5分以内に終われば環境キャッシュ (ファイルシステムスナップショット) — 同上
- 本セッション自身の環境は `network.type = "unrestricted"` (Full) — get_environment ツール実測 (env 名 "Claude-kun")

### Inferences
- クラウドで使う MCP は、`.mcp.json` に stdio (uvx/npx で PyPI/npm から取得 → 既定許可リストで可) か HTTP (ホストを Allowed domains に追加要、Full なら不要) で書き、リポジトリにコミットする。例:
  ```json
  {"mcpServers": {
    "pcbparts": {"type": "http", "url": "https://pcbparts.dev/mcp"},
    "kicad-review": {"command": "uvx", "args": ["kicad-mcp-pro==4.11.0"]}
  }}
  ```
  (kicad-mcp-pro の既定起動引数・プロファイル指定方法は README の範囲で 未確認。`uvx kicad-mcp-pro --transport streamable-http …` と `quickstart` は README 記載)
- リモート MCP を claude.ai の custom connector として登録すれば、クラウドの許可リストを変えずに使える可能性が高い (connector 経路は allowlist 対象外のため)。ただし custom connector に任意 URL を登録できるかはプラン依存で本パス 未確認。
- ProductOfAmerica の「Claude Code プラグイン」導入方式は、クラウドではリポジトリ設定経由で自動導入されないため、クラウド用途では `.mcp.json` 直書きが必要 (推論)。
- USB 実機 (Pico、デバッグプローブ、ロジアナ、シリアル) はクラウド VM に届かない。実機系 MCP はユーザーのデスクトップで動く Claude Code (または Remote Control で自宅PCのセッションを操作) が前提 (推論)。

### Gaps
- claude.ai custom connector の登録条件 (Pro/Max で任意 URL 可か) は 未確認。
- 既定許可リストの全行は WebFetch 要約経由で一部欠落の可能性あり (204 行中のgrep結果)。

---

## 5. 本プロジェクト向けランキング推奨 (2列)

### Takeaway
本プロジェクトの大半のステップでは **「MCP サーバは不要、CLI を直接使う」** が最良。例外的に価値が高いのは部品選定の pcbparts-mcp (JLCPCB Basic/Preferred を機械的に絞れる) だけで、それすら jlcsearch の HTTP GET や CDFER の CSV で代替可能。デスクトップ側は実機立ち上げ (デバッグプローブ・シリアル・ロジアナ) の段階で初めて MCP の価値が出る。

### (a) ヘッドレス・クラウドコンテナで使えるもの

| 順位 | ステップ | 推奨 | 区分 | 理由 |
|---|---|---|---|---|
| 1 | 部品選定 (JLCPCB Basic 限定) | Averyy/pcbparts-mcp (HTTP `https://pcbparts.dev/mcp`) | **useful (最上位)** | 無認証・実測動作、`library_type="basic"`/`"no_fee"` 絞り込みと「なぜ0件か」の診断付き。74HC245 が Basic に無いこと (Preferred は C5625 のみ) を即判定できた。第三者運営なので最終確認は jlcsearch/CDFER DB と突合 (Limited 環境では pcbparts.dev を Allowed domains に追加要) |
| 2 | 部品選定の裏取り | jlcsearch HTTP API + CDFER/jlcpcb-parts-database (MCPではない) | **must-have (CLI/データ)** | MCP 不要。`curl` で JSON 取得可 (実測)。Basic/Preferred 判定の一次データ |
| 3 | 回路図/基板の検証・製造出力 | kicad-cli 直 (ERC/DRC/Gerber/drill/pos/BOM/jobset) | **must-have (CLI)** | 「no MCP server is needed for this step; use the CLI tool directly」。ProductOfAmerica の作者自身の比較でも素の Claude Code が 18/18 vs MCP 3/18 |
| 4 | 設計レビュー補助 | oaslananka/kicad-mcp-pro (`default` = 24 読み取りツール、版固定) | useful (任意) | ヘッドレス可・MIT・CI/CodeQL あり。ただし更新頻度が異常に高く (5か月で63リリース) 版固定必須。編集系プロファイルは使わない |
| 5 | KiCad 編集の MCP 化 | ProductOfAmerica/mcp-server-kicad | skip | 保守モード、GPL 化、作者自身が素の Claude Code を推奨 |
| 6 | KiCad 編集の MCP 化 | mixelpixx/KiCAD-MCP-Server (SWIG モード) | skip | 244〜251 ツールは文脈コスト過大、SWIG は KiCad 11 で削除見込み、ヘッドレス時の動作は未検証 |
| 7 | データシート読解 | Claude Code 標準 Read (+ `apt-get install poppler-utils`) | **must-have (内蔵)** | MCP 不要。20頁単位で読める |
| 8 | 巨大データシート検索 (RP2040/RP2350 等) | I-CAN-hack/pdf-mcp | useful (任意) | search_text・目次・ページ画像。`pdftotext` + `grep` でも代替可 |
| 9 | アナログ検証 (ビデオDAC/RGBアンプ/音声) | ngspice 直 (apt ngspice 42) | **must-have (CLI)** | MCP 不要。spicebridge は 7か月停滞・GPL、ltspice-mcp は LTspice/Wine 前提 → いずれも skip〜任意 |
| 10 | 粗配線 | Freerouting CLI/JAR 直 (`--gui.enabled=false`) | useful (CLI) / MCP は skip | 公式 MCP (`autoroute_board`, stdio ローカル) は動くが、DSN→SES を回すだけなら CLI で十分。Public API モードはキーと外部送信が必要 |
| 11 | Pico ファームのビルド | Pico SDK + cmake + gcc-arm-none-eabi 直 | **must-have (CLI)** | Pico SDK/picotool 専用 MCP は存在しない。PlatformIO MCP は Pico SDK 路線では不要 → skip |
| 12 | Pico ファームのシミュレーション CI | Wokwi CLI (`wokwi-cli mcp`, experimental) | useful (任意) | トークン必須、シミュレーションはクラウド実行、無料 50分/30日・1回5分。wokwi.com 系ホストの許可要 (具体ホスト名は未確認) |
| 13 | atopile/tscircuit/Altium/Fusion/EasyEDA 系 | — | skip | 設計フロー (KiCad + JLCPCB) と不一致、または GUI 必須 |
| 14 | 流通 API (Octopart/DigiKey/Mouser) | — | skip | キー要、本件は JLCPCB Basic + 秋月中心。秋月の MCP/API は見つからず (手作業/ウェブ確認) |

### (b) ユーザーのデスクトップ (KiCad / EasyEDA / 実機が動く環境) 専用

| 順位 | ステップ | 推奨 | 区分 | 理由 |
|---|---|---|---|---|
| 1 | 実機立ち上げ: SWD デバッグ・書込・RTT | Adancurusul/embedded-debugger-mcp (probe-rs/OpenOCD) | useful | ★217・MIT・テスト有。Raspberry Pi Debug Probe 等の CMSIS-DAP で RP2040/RP2350 が使えるかは要確認 (未確認)。使わなければ `picotool`/`openocd` 直でよい |
| 2 | Pico の USB シリアルログ | qarnet/serial-mcp | useful | 活発 (push 2026-11-10)、Linux バイナリ配布、25ツール。`screen`/`pyserial` 直でも可 |
| 3 | ロジアナで 21.47727MHz 系・JAMMA 信号確認 | KenosInc/sigrok-mcp-server | useful | sigrok-cli ラッパ。キャプチャファイルをクラウドへ持ち込みデコードするなら sigrok-cli 直で足りる |
| 4 | KiCad GUI と同時編集 (ライブ) | oaslananka/kicad-mcp-pro + KiCad 10 IPC Companion (プレビュー) / mixelpixx (IPC モード) | useful (任意) | 人間が GUI で配置を確認しながら AI に小修正させる用途のみ |
| 5 | KiCad GUI 前提の新興サーバ (Konnect-EDA, KiPilot, nevenfo, daedalus 等) | — | skip | Konnect はアーカイブ→商用クローズド・Linux未QA、他は若すぎる/玩具級 |
| 6 | EasyEDA Pro を使う場合 | easyeda/easyeda-client-cli (公式 org、MCP モード) | useful (EasyEDA 採用時のみ) | デスクトップクライアント V4.1.70+ 稼働必須。KiCad 路線なら skip |
| 7 | PlatformIO / pico-bay / OpenOCD 小型 MCP 群 | — | skip | Pico SDK (C) 路線と不一致、または小規模・重複 |

### Inferences
- 推奨構成 (推論): クラウド側は `.mcp.json` に pcbparts (HTTP) だけを置き、他は全て CLI (kicad-cli, ngspice, Freerouting, Pico SDK, poppler) をセットアップスクリプトで導入。デスクトップ側は実機段階で embedded-debugger-mcp / serial-mcp / sigrok-mcp をユーザースコープで追加。
- MCP の文脈コスト (KiCad 系は 24〜251 ツール) は Tool search で緩和されるが、編集の正確さは「ファイルを直接編集し kicad-cli で検証」の方が高いという作者報告 (ProductOfAmerica) と整合 (推論)。

### Gaps
- pcbparts-mcp の運営継続性・利用規約は 未確認 (README に SLA 記載なし)。
- probe-rs の RP2350 対応、Wokwi の RP2350/PIO 対応は 未確認。

---

## 6. 既存ノートへの訂正 (tooling_and_mcp.md 第4節ほか)

### Takeaway
第1パスの MCP 節には、レジストリ API の読み方に起因する誤り (版不整合・JLCPCB 0件) と、時点が古くなった記述 (Konnect の位置づけ) がある。

### Cited Findings
- 訂正1: 「oaslananka/kicad-mcp-pro README上 v4.11.0 (レジストリ上は2.1.0=2026-04-15、不整合)」→ 不整合ではない。レジストリは全版を返し 2.1.0 は最古エントリ (`isLatest=false`)、最新は 4.11.0 (2026-11-10) — [registry](https://registry.modelcontextprotocol.io/v0/servers?search=kicad-mcp-pro&limit=100)。第1パスの他の版数も同じ読み方なら旧版の可能性があるが、本パスで `version=latest` 再取得した値 (ProductOfAmerica 0.21.1 等) は第1パスと一致した。
- 訂正2: 「JLCPCB/LCSC専用の独立MCPはレジストリ検索で0件」→ 公式レジストリの検索が名前一致のみのため。実際には Averyy/pcbparts-mcp (★144, ホスト型), Eyalm321/jlcpcb-mcp, nvsofts/jlcpcb-parts-mcp (停滞), hulryung/jlcpcb-skill-mcp, zhr1008/component-sourcing-mcp 等が存在 — [Glama jlcpcb](https://glama.ai/mcp/servers?query=jlcpcb), [GitHub search](https://github.com/search?q=jlcpcb+mcp&type=repositories)
- 訂正3: 「mixelpixxは新開発をKiCad 10向けRust製Konnect(AGPL)へ移行」→ 2026-11 時点で Konnect 自体がアーカイブされ、開発は Orchis.ai LLC の商用クローズド「Konnect-EDA」へ移行。AGPL 版はフォーク (dylbertram/konnect-maintained) が継続 — [Konnect README](https://raw.githubusercontent.com/mixelpixx/Konnect/main/README.md), [Konnect-EDA](https://github.com/Orchis-ai-LLC/Konnect-EDA)
- 訂正4: mixelpixx「GUI要否は記載なし」→ README に「Automatically uses IPC when available, falls back to SWIG」と明記。版は v2.8.3、ツール数 251 (別節 244)。ライセンス MIT — [README](https://raw.githubusercontent.com/mixelpixx/KiCAD-MCP-Server/main/README.md)
- 訂正5: jlcsearch「本コンテナからは curl -I が405(GET可否は未確認)」→ GET で JSON 取得可 (HEAD が 405 なだけ) — [jlcsearch](https://jlcsearch.tscircuit.com/components/list.json?search=74HC245&limit=20)
- 訂正6: Freerouting「ライセンス記載はページ上で未確認」→ GPL-3.0 (GitHub ライセンス検出、npm `@freerouting/freerouting-mcp-server` も GPL-3.0-only)。また第1パスは MCP `autoroute_board` を「v2.5.0で追加」と「v2.3.0以降」の両方で書いており自己矛盾。npm MCP ブリッジの初版は 2026-06-16、最新 2.5.0 (2026-10-05)。どの版で autoroute_board が入ったかは本パスでも 未確認 — [npm](https://registry.npmjs.org/@freerouting/freerouting-mcp-server), [MCP Guide](https://raw.githubusercontent.com/freerouting/freerouting/master/docs/API/MCP.md)
- 訂正7: 「rp2040js: 指定URL (github.com/rp2040js/rp2040js) は404。正しい所在・PIO対応状況は未確認」→ 所在は wokwi/rp2040js (★536, MIT, push 2026-10-18)。PIO 対応は引き続き 未確認 — [GitHub search user:wokwi](https://github.com/wokwi)
- 訂正8: 「(KiCad devlist) eeschema(回路図)のIPC APIは10に間に合わなかった」→ GitLab #24803 は「The schematic editor (`API_HANDLER_SCH`, KiCad 10) does not register `RevertDocument`」、#25666 は「The schematic editor in 10.0.x doesn't have [variant commands]」と書いており、KiCad 10.0.x に回路図エディタの API ハンドラ自体は存在する模様。両出典は食い違う (devlist は 2026-01 時点の開発者発言、GitLab は 2026-08〜09 の利用者報告)。範囲は 未確認 — [#24803](https://gitlab.com/kicad/code/kicad/-/work_items/24803), [#25666](https://gitlab.com/kicad/code/kicad/-/work_items/25666)
- 補足9: 「PowerDragonfire/platformio.mcp (0.1.0)」→ PyPI 最新は 0.6.2 (2026-11-10) — [PyPI](https://pypi.org/pypi/platformio.mcp/json)
- 補足10: 「EasyEDA Pro系…GUI必須→クラウド不可(推定)」→ 公式 org の easyeda-client-cli が「requires the desktop client of EasyEDA Pro」と明記し推定が裏付けられた — [easyeda-client-cli](https://github.com/easyeda/easyeda-client-cli)
- 補足11: 第1パス第1節の「PPA kicad-10.0-releases (ppa.launchpadcontent.net) HTTP 200」は本セッション (Full network) での実測。既定 Limited 環境の許可リストには ppa.launchpad.net はあるが ppa.launchpadcontent.net は見当たらず、Limited 環境では追加許可が要る可能性 (未確認) — [cloud environments](https://code.claude.com/docs/en/cloud-environments)

### Inferences
- 第1パスの「推奨: KiCad系MCPは必須ではない」は本パスでも支持される (ProductOfAmerica 作者の比較結果が追加根拠)。

### Gaps
- 第1パス表の他行 (biosshot/kicad-copilot 等) の版は再確認済みで一致。datasheet-lens は PyPI 0.6.1 だが README は「version 0.4」で不一致 (原因未確認)。
