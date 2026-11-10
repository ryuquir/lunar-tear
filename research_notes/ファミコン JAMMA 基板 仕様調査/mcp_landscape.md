# MCP サーバ全景調査 (PCB設計・部品選定・回路シミュレーション・組込みFW) — 2026-11-10時点 (第2パス)

(作業中: 途中保存。以下は確定済みの一次データ)

## 0. 調査方法 (途中)
- 公式レジストリ: `https://registry.modelcontextprotocol.io/v0/servers?search=<語>&version=latest&limit=100` を curl で約60語検索。検索は名前の部分一致のみ(説明文は対象外)と推論 (jlcpcb/lcsc が0件なのに説明文にJLCPCBを含むサーバが存在するため)。
- GitHub: `gh api search/repositories?q=...` (検索APIは許可、`repos/<owner>/<name>` は本セッションで403)。星数・最終push日・ライセンスは `gh api "search/repositories?q=repo:<owner>/<name>"` で 2026-11-10 取得。

## 途中確定事項 (後で本文に統合)
- oaslananka/kicad-mcp-pro: 公式レジストリは版履歴を全件返す。2.1.0 (publishedAt 2026-04-15) は最古の登録で isLatest=false。最新は 4.11.0 (2026-11-10)。PyPI でも 4.11.0 (2026-11-10)、PyPI上の最古は 3.13.0 (2026-06-21)、計63リリース。→ 第1パスの「不整合」は旧版エントリを読んだことによる誤読。
- mixelpixx/KiCAD-MCP-Server: README「What's New in v2.8.3」、MIT、251 tools/20 categories (別箇所では244と不一致)、STDIO、KiCad 9.0+、IPC(実験的)優先・SWIG fallback。★3,255、最終push 2026-11-10。
- mixelpixx/Konnect: GitHub上 archived=true (最終push 2026-11-02、作成 2026-07-05、AGPL-3.0、★1,458)。README「This repository is being archived ... Development continues at Konnect-EDA, from Orchis.ai LLC.」Konnect-EDA は商用クローズドソース、1.0まで無料、1.0以降は全インストールにライセンスキー要。PCBツールは「KiCAD running with the target board open (IPC API)」。フォーク dylbertram/konnect-maintained (AGPL維持)。
- ProductOfAmerica/mcp-server-kicad: 「As of October 2026 this project gets security fixes and KiCad compatibility fixes only.」理由: 作者の小規模テストで plugin あり 3/18 正解 vs 素の Claude Code 18/18。GPL-3.0-or-later、0.20.1 までMIT。PyPI 0.21.1 (2026-10-20)、計68リリース。
- Claude Code 文書: スコープ local/project(.mcp.json)/user、優先順位 Local>Project>User>Plugin>claude.ai connectors。クラウドセッションは repo の .mcp.json を読む(単一リポジトリ時)、~/.claude.json のサーバは持ち込まれない。connector は Anthropic 経由で allowlist 不要。
- 本セッションの環境 (get_environment): network type = "unrestricted" (Full)。既定 Default 環境は Limited。
