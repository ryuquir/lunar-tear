# 設計・検証に必要なソフトウェアと MCP サーバー - 要約

データの日付は 2026-11-10 である。確度の語は次の意味で使う。確認済は、独立した出典が2つ以上あるか、このクラウド環境での実測・ライブデータ・データシートで確かめたもの。単一出典は、出典が1つだけのもの。未確認は、確かめられていないもの。推論は、調査者の判断で出典がないもの。

## 1. この分野の結論

1. 基板設計は KiCad 10.0.8 とそのコマンドライン版 `kicad-cli` で、回路図の電気的検査（ERC）から基板の設計ルール検査（DRC）、Gerber・ドリル・部品配置・部品表の出力まで、画面のないクラウド環境で実際に動いた。JLCPCB 向けの出力一式（Gerber の zip、BOM、部品配置表 CPL）は KiBot 1.9.1 で出せた。（確認済）
2. KiCad の「回路図から基板を更新」に当たるコマンドは `kicad-cli` にないため、KiCad 同梱の Python モジュール（SWIG 版 `pcbnew`、`/usr/bin/python3.12` 限定）を使う約40行の自作スクリプト net2pcb.py で代用し、回路図との不一致 0 件を確かめた。この SWIG 版は KiCad 11 で削除される見込みなので、KiCad は 10.0.x に固定するのが安全である。（実測は確認済、削除見込みは単一出典、固定の判断は推論）
3. 部品クラス（Basic など）と在庫の最終判定は、JLCPCB の部品検索画面が呼ぶ JSON（JLCPCB API）で行う。Basic は 351 件、Preferred は 1,235 件で、jlcsearch・jlcparts・CDFER は同じ巡回データ系統のため独立した裏取りにならず、CDFER の Preferred は 1,226 件と食い違い、21.47727MHz 水晶 C5289705 などの収載漏れもある。（確認済）
4. MCP サーバー（AI エージェントに外部ツールを関数として渡す仕組み）は必須ではない。クラウドで価値があるのは部品検索の pcbparts-mcp（MIT、無認証、100 req/min/IP）くらいで、KiCad・JLCPCB・LCSC の公式 MCP は存在せず、秋月電子には公開 API も MCP も見つからない。（MCP の状況は確認済、秋月は単一出典）
5. Raspberry Pi Pico 系のファームウェアのビルド（Pico SDK 2.3.1）、Freerouting 2.5.0 による自動配線、Fabrication Toolkit の実行は、このクラウド環境で「外部から取得したコードの実行」として許可が下りず、動くかどうかは確かめていない。（拒否されたことは確認済、動作は未確認）
6. 新規開発ゲーム側の自動試験は、cc65 2.19 で作った 24,592 B の ROM を FCEUX 2.6.5（apt 版）で画面なしで起動し、Lua の `joypad.set` で入力を与えて `memory.readbyte` で結果を読むところまで実証できた。高精度の MesenCE 2.2.1 の `--testRunner` はソースで仕様を確かめただけである。（FCEUX は確認済、MesenCE の動作は未確認）
7. 実機なしで Pico のファームを試す手段（SDK の `PICO_PLATFORM=host`、rp2040-pio-emulator、Wokwi）はどれも、複数枚のマイコンの協調や、ファミコンの M2・PPU の /RD・/WR とのナノ秒単位の位相関係を検証できない。Wokwi はコアを1つしか模擬せず、RP2350 固有の PIO 命令もない。（各ツールの制限は単一出典、検証範囲の判断は推論）
8. 実機確認には、16ch・100MS/s 以上のロジックアナライザ（DSLogic Plus $149）、100MHz 級のオシロスコープ（OWON SDS1102 ￥39,000）、フラッシュカート（EverDrive N8 PRO Fami $159）、15kHz 映像の表示手段（OSSC 1.8 €115.00〜）、JAMMA 電源（MEAN WELL RT-65A）、DIP-40 の取り外し道具と静電気対策用品が要る。円建ての最小構成だけで ￥64,570 になり、これにドル・ユーロ建ての3品と JAMMA 電源が加わる。（各価格は単一出典、合計は推論）
9. USB 機器（Pico、デバッグプローブ、ロジックアナライザ、シリアル）はクラウドの作業マシンに届かないので、実機を扱う MCP（embedded-debugger-mcp、serial-mcp、sigrok-mcp-server）と USB Type-C からのファームウェア更新の試験は、利用者のパソコンで動く Claude Code が前提になる。（推論）
10. 通信先を制限した Limited 環境では、既定の許可リストに pcbparts.dev、jlcsearch.tscircuit.com、jlcpcb.com、lcsc.com が含まれず、KiCad の PPA 本体 ppa.launchpadcontent.net も見当たらないので、追加の許可が要る。（許可リストは単一出典、PPA の要否は未確認）

## 2. 報告書にそのまま載せる表

### 2.1 工程別の必須ソフトウェアと任意ソフトウェア

「クラウドで動作」は、このクラウド環境（Ubuntu 24.04、root、4CPU のコンテナ）で実際に動かした結果である。区分の「必須」「推奨」「任意」「不要」「使わない」「参考」はシートの判定のままである。

**回路図**

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| KiCad（回路図エディタと `kicad-cli sch`） | 必須 | 10.0.8（2026-10-30） | PPA `kicad/kicad-10.0-releases` を apt で導入 | 動作した（ERC・netlist・BOM・PDF・SVG・`sch upgrade`） | 確認済 |
| kicad-sch-api | 任意（回路図を Python で生成） | 0.5.6（`__version__` は 0.5.5 と表示） | pip | 動作した（生成・読み書き往復とも。属性に軽微な差） | 確認済 |
| SKiDL | 任意（Python で回路を記述） | 3.0.0（2026-10-16） | pip（導入に 217 秒、venv 全体 431MB） | 動作した（netlist・回路図・基板の生成） | 確認済 |
| kicad-skip | 任意（回路図ファイル操作） | 0.2.5 | pip | 回路図は無損失で往復できた。基板は読めない | 確認済 |
| kiutils | 使わない | 1.4.8（2024-02-02） | pip | 回路図は属性が欠落する。基板は読めない | 確認済 |
| atopile | 任意（独自言語で回路記述。内蔵 MCP あり） | 0.15.9（2026-09-12） | pip | 試していない | 単一出典 |
| circuit-synth | 任意 | 0.12.1（2026-01-09） | pip | 試していない | 単一出典 |
| easyeda2kicad | 必須（LCSC 部品をシンボル・フットプリント・3D に変換） | 1.0.1（2026-04-06） | pip | 動作した（C2040 を取得） | 確認済 |
| JLC2KiCadLib | 任意（easyeda2kicad の代替） | 1.3.2（2026-09-11） | pip | 動作した（C25804 を取得） | 確認済 |

**部品選定**

| ツール | 区分 | 版数・データ日 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| JLCPCB の部品検索 API（jlcpcb.com/parts の画面が呼ぶ JSON） | 必須（Basic/Preferred 判定の一次データ） | ライブ | HTTPS の POST。Playwright で画面操作時の通信を捕捉して確認したもの | 動作した（Basic 351 件、Preferred 1,235 件を全件取得） | 確認済 |
| jlcsearch（tscircuit） | 推奨（候補の検索・絞り込み。MCP ではない HTTP API。jlcparts と同系統のデータなので、JLCPCB と独立した裏取りにはならない。1.6.1） | 毎日同期 | HTTPS の GET、無認証 | 動作した（GET は 200。HEAD は 405） | 確認済 |
| CDFER/jlcpcb-parts-database | 任意（オフラインの一覧） | 2026-11-10 版 | HTTPS で CSV（1,252,216 B）と SQLite（419,360,768 B）を取得 | 動作した。ただし全文検索索引は空で、Preferred 件数が JLCPCB と一致しない | 確認済 |
| pcbparts-mcp（ホスト版） | 任意（最も実用的な部品検索 MCP） | `/health` は 0.8.24、serverInfo は "3.4.3" | HTTP の MCP、無認証、100 req/min/IP | 動作した（JSON-RPC を curl で実行） | 確認済 |
| LCSC の商品データ API（商品ページのデータ源） | 任意（LCSC 倉庫の在庫・価格。クラス情報なし） | ライブ | HTTPS の GET | 動作した | 確認済 |
| Claude Code 標準の Read ツール + poppler-utils | 必須（データシート読解） | — | `apt-get install poppler-utils` | 文書上の機能（20 ページ単位で PDF を読める） | 単一出典 |
| 秋月電子の在庫確認 | 必須（手はんだ部品） | — | 公開 API・MCP は見つからない。人がウェブで確認 | — | 単一出典 |

**配置配線**

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| SWIG 版 pcbnew（KiCad 同梱） | 必須（回路図→基板の反映、配置、配線追加） | 10.0.8 | KiCad に同梱。`/usr/bin/python3.12` で使う | 動作した（読込・フットプリント追加・配線・保存・Gerber・Specctra DSN 出力） | 確認済 |
| 自作 net2pcb.py（約40行） | 必須（「回路図から基板を更新」の代わり） | — | 自作（SWIG pcbnew 使用） | 動作した（schematic parity 0 件） | 確認済 |
| kipy（kicad-python）+ IPC API | 任意（GUI の KiCad を外部から操作） | 0.8.0（2026-08-30） | pip | xvfb 上の pcbnew で動作した（起動ウィザード抑止の設定が必須） | 確認済 |
| Freerouting | 任意（粗い自動配線） | 2.5.0（2026-10-05） | GitHub Releases（jar 64,599,107 B、またはネイティブ CLI 20,714,066 B） | ダウンロードと sha256 照合のみ。実行は許可されず未実施 | 確認済（取得）／未確認（実行） |
| KiKit | 任意（パネル化。JAMMA 基板が1枚なら不要） | 1.8.1（2026-08-05） | pip | 試していない | 単一出典 |
| JLCPCB 用設計ルール（.kicad_dru） | 必須（DRC 用） | JLCPCB 公式品は見つからない。コミュニティ版あり | — | 試していない。最小線幅・間隔の値は資料間で不一致 | 未確認 |

**検証**

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| `kicad-cli sch erc` / `kicad-cli pcb drc --schematic-parity` | 必須 | 10.0.8 | KiCad に同梱 | 動作した | 確認済 |
| `kicad-cli pcb render` | 任意（基板の画像） | 10.0.8 | KiCad に同梱 | xvfb なしで動作した（800x450 が 1.9 秒） | 確認済 |
| ngspice | 必須（映像 DAC・RGB 増幅・音声のアナログ検証） | 42 | apt | 動作した（`ngspice -b` のバッチ実行） | 確認済 |
| kicad-mcp-pro（`default` プロファイル） | 任意（設計レビュー補助） | 4.11.0（2026-11-10） | uvx（版の固定が必須） | 試していない | 単一出典 |

**製造データ出力**

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| `kicad-cli pcb export gerbers/drill/pos`、`sch export bom` | 必須 | 10.0.8 | KiCad に同梱 | 動作した。ただし JLCPCB 形式の部品配置表の列名と回転補正は手作業での変換が要る（推論） | 確認済 |
| KiBot（JLCPCB 用の出力一式を YAML で定義） | 必須（推奨経路） | 1.9.1（2026-07-28）、AGPL-3.0 | pip（`--no-compile` と lxml が必要） | 動作した（JLCPCB 用 zip、BOM、CPL を出力） | 確認済 |
| Fabrication Toolkit（bennymeg） | 任意（KiBot の代替） | HEAD 7f627b6（2026-09-29）、metadata.json の先頭版 "5.3.1"、Apache-2.0 | git clone | clone のみ。実行は許可されず未実施 | 未確認 |
| kicad-jlcpcb-tools（Bouni） | 参考 | KiCad 7〜10 対応と表記 | KiCad のプラグイン | GUI 前提。ヘッドレスの記載なし | 単一出典 |

**ファームウェア**

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| Raspberry Pi Pico SDK | 必須 | 2.3.1（2026-09-04） | git clone（サブモジュール込み 428MB） | clone は成功。ビルドは許可されず未実施 | 確認済（取得）／未確認（ビルド） |
| picotool | 必須（UF2 書き込み・情報表示・seal） | 2.3.1（2026-09-05） | SDK の CMake が自動で取得してビルド | 未実施 | 確認済（版）／未確認（ビルド） |
| pioasm | 必須（PIO アセンブラ） | SDK と同じ版 | SDK のソースからビルド（ネットからの取得はない） | 未実施 | 確認済（入手方法） |
| gcc-arm-none-eabi / cmake / ninja | 必須 | 13.2.1 20231009（15:13.2.rel1-2）/ 3.28.3 / 1.11.1 | apt（cmake と ninja は元から導入済み） | 導入は成功 | 確認済 |
| cc65（ca65/ld65） | 必須（6502 の自作 ROM） | 2.19（apt 2.19-1、ca65 は V2.18 と表示） | apt | 動作した（iNES ROM 24,592 B を生成） | 確認済 |
| neslib / nesdoug | 推奨（C で書く場合） | 版不明 | GitHub / ウェブ | 試していない | 単一出典 |
| asm6f / NESASM CE / llvm-mos-sdk | 任意 | v1.6_f03（2025-01-27）/ v3.6 / 未確認 | GitHub | 試していない | 単一出典 |
| openocd | 任意（SWD デバッグ） | 0.12.0 | apt | 導入可能であることのみ確認 | 単一出典 |

**シミュレーション**

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| Pico SDK の `PICO_PLATFORM=host` | 必須（コイン・タイマー・入力形式の論理を PC 上で単体試験） | SDK 同梱 | SDK | 未実施（SDK のビルドが未許可） | 単一出典 |
| rp2040-pio-emulator | 任意（PIO ステートマシン1個の単体試験） | 0.88.0（2026-08-28）、Apache-2.0 | pip | 試していない | 単一出典 |
| rp2040js | 任意（RP2040 全体の JS エミュレータ。RP2350 の記述なし） | npm 1.4.1（2026-10-18）、MIT | npm | 試していない | 確認済（所在と版） |
| Wokwi CLI | 任意（クラウドで Pico / Pico 2 を模擬する CI） | v0.29.1（「23 Oct」、年表示なし） | 公式インストールスクリプト。トークン `WOKWI_CLI_TOKEN` が必須 | 試していない | 確認済（仕様）／未確認（動作） |
| FCEUX（xvfb + Lua） | 必須（自作 ROM の自動試験。現時点で唯一実証済み） | apt 2.6.5（上流の最新は 2.7.0、2026-10-14） | apt（DL 11.6MB） | 動作した（入力を与えて RAM を検査） | 確認済 |
| MesenCE（`--testRunner`） | 必須（高精度の回帰試験） | 2.2.1（2026-06-05）、GPL-3.0 | GitHub の Linux ビルド（SDL2 が必要） | 試していない | 確認済（ソースで仕様確認）／未確認（動作） |
| mednafen / nestopia | 任意 | 1.29.0 / 1.52.0 | apt | 試していない | 単一出典 |
| ghdl / iverilog / yosys / nextpnr-ice40 | 不要（プログラマブルロジックを使う場合のみ） | 4.1.0 / 12.0 / 0.33 / 0.6 | apt | 試していない | 単一出典 |

**実機確認**

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| sigrok-cli / PulseView | 必須（ロジックアナライザ使用時） | 0.7.2 / 0.4.2 | apt | 取り込みは実機が必要。保存したキャプチャのデコードはクラウドでも可能（推論） | 単一出典 |
| minipro | 必須（XGecu T48 使用時） | タグ12個、最新版数は未確認 | GitLab からビルド | 実機が必要 | 単一出典 |
| picotool（実機への書き込み） | 必須 | 2.3.1 | 上記 | 実機が必要 | 確認済（版） |

### 2.2 セットアップ用スクリプトの案と、必要な通信先

このスクリプトは、実行・成功したコマンドだけを、繰り返し実行しても壊れないように `if` や `[ -f ]` で包んだものである。個々の手順は確認済だが、スクリプト全体の通し実行は未確認である。シートは「Freerouting の実行、Pico SDK のビルド、Fabrication Toolkit の実行は未検証のため、取得だけにとどめている」と書いている（ただしスクリプトに Fabrication Toolkit の取得は入っていない）。スクリプト中の URL はコマンドの引数であり、出典ではない。

```bash
#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# 1. KiCad 10 (PPA). python3 が 3.13 を指す環境でも動くよう python3.12 を明示
if [ ! -f /etc/apt/sources.list.d/kicad-ubuntu-kicad-10_0-releases-noble.sources ]; then
  python3.12 /usr/bin/add-apt-repository -y ppa:kicad/kicad-10.0-releases
else
  apt-get update
fi
apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints \
  gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib \
  cmake ninja-build build-essential cc65 ngspice fceux xdotool
# 2. KiCad ヘッドレス設定 (lib-table と起動ウィザード抑止、IPC API有効)
CFG="${KICAD_CONFIG_HOME:-$HOME/.config/kicad}/10.0"
mkdir -p "$CFG"
[ -f "$CFG/sym-lib-table" ] || cp /usr/share/kicad/template/sym-lib-table "$CFG/"
[ -f "$CFG/fp-lib-table" ]  || cp /usr/share/kicad/template/fp-lib-table "$CFG/"
[ -f "$CFG/design-block-lib-table" ] || printf '(design_block_lib_table\n\t(version 7)\n\t(lib (name "KiCad") (type "Table") (uri "/usr/share/kicad/template/design-block-lib-table") (options "") (descr "KiCad Default Libraries"))\n)\n' > "$CFG/design-block-lib-table"
[ -f "$CFG/kicad_common.json" ] || echo '{"api":{"enable_server":true},"do_not_show_again":{"update_check_prompt":true,"data_collection_prompt":true}}' > "$CFG/kicad_common.json"
# 3. Python ツール (KiCad の pcbnew を使うため python3.12 + system-site-packages)
[ -x /opt/kicad-venv/bin/python ] || /usr/bin/python3.12 -m venv --system-site-packages /opt/kicad-venv
/opt/kicad-venv/bin/pip install -q kicad-python kiutils kicad-skip kicad-sch-api easyeda2kicad JLC2KiCadLib
/opt/kicad-venv/bin/pip install -q skidl          # 約3.5分 (matplotlib/h5py 等)
[ -x /opt/kibot-venv/bin/python ] || /usr/bin/python3.12 -m venv --system-site-packages /opt/kibot-venv
/opt/kibot-venv/bin/pip install -q --no-compile kibot lxml
find /opt/kibot-venv/lib/python3.12/site-packages/kibot -name '__pycache__' -prune -exec rm -rf {} +
# 4. Pico SDK (取得のみ; ビルドは未検証)
[ -d /opt/pico-sdk/.git ] || git clone -b 2.3.1 --depth 1 https://github.com/raspberrypi/pico-sdk.git /opt/pico-sdk
(cd /opt/pico-sdk && git submodule update --init --depth 1)
# 5. Freerouting native CLI (取得とsha256検証のみ; 実行は未検証)
mkdir -p /opt/freerouting && cd /opt/freerouting
[ -f freerouting-cli-2.5.0-linux-x64.tar.gz ] || curl -sSL -o freerouting-cli-2.5.0-linux-x64.tar.gz https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-cli-2.5.0-linux-x64.tar.gz
echo "64a957a9ef2a2fbde6ab2001bb32800f5ba34f9fd15575e363512934b870d63a  freerouting-cli-2.5.0-linux-x64.tar.gz" | sha256sum -c -
# 6. JLCPCB Basic/Preferred 部品CSV
curl -sS -o /opt/jlcpcb-components-basic-preferred.csv https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv
```

スクリプト案の注意点:

- 所要時間の見込みは apt 約1分（DL 約750MB）、pip 約4分、clone 約20秒。ディスクは apt 約4GB、venv 約0.5GB、pico-sdk 0.43GB（実測値の合算。推論）。
- `$HOME/.config/kicad/10.0` への配置は、`KICAD_CONFIG_HOME` を使って検証した内容と同等のもので、その場所自体では試していない（未確認）。
- **スクリプト案には xvfb の導入が含まれていない。** IPC API と FCEUX の試験では `xvfb-run` を使ったが、xvfb が元から入っていたのかはノートに記載がない（未確認）。新しい環境で使う場合は xvfb の導入を足す必要がある可能性が高い（推論）。
- kiutils と kicad-skip は基板ファイルを読めない（2.3 の表）。スクリプト案では導入しているが、使う予定がなければ外してよい（推論）。
- 公式文書によれば、クラウド環境のセットアップスクリプトは約5分以内に終われば環境ごとキャッシュされる（単一出典）。上記の見込み（約5分20秒）はその境目にあり、SKiDL（約3.5分）を外せば確実に収まる（推論）。
- クラウドの作業マシンの目安は Ubuntu 24.04 x86_64、4 vCPU / 16GB RAM / 30GB ディスクで、Python+uv、Node 20/21/22、OpenJDK 21、GCC/Clang/cmake/ninja、Docker が入っている（単一出典）。ディスク約5GB の追加は収まる（推論）。

**各手順が必要とする通信先**（調査したセッション自身のネットワーク設定は無制限（Full）だった。右端の列は、制限付き（Limited）環境の既定の許可リストと照らし合わせた結果である）

| 手順 | 通信先（ホスト名） | このセッションでの結果 | Limited 環境の既定許可リストに含まれるか |
|---|---|---|---|
| KiCad PPA | ppa.launchpadcontent.net（PPA 本体） | 到達 | 見当たらない（ppa.launchpad.net はある）。追加許可が要る可能性（未確認） |
| add-apt-repository の鍵取得 | api.launchpad.net（推論） | 到達 | 未確認 |
| 鍵の代替取得 | keyserver.ubuntu.com | 200 | `*.ubuntu.com` に含まれる（推論） |
| apt 依存パッケージ | archive.ubuntu.com、security.ubuntu.com | 到達 | 含まれる |
| pip | pypi.org、files.pythonhosted.org | 到達 | 含まれる（パッケージ取得先として） |
| KiCad ソース調査 | gitlab.com | 200 | 含まれる |
| git clone（Fabrication Toolkit、pico-sdk とサブモジュール、picotool） | github.com（git のみ。素の curl は 403） | 到達 | 含まれる |
| easyeda2kicad / JLC2KiCadLib | easyeda.com、modules.easyeda.com | 到達 | 未確認 |
| jlcsearch | jlcsearch.tscircuit.com | 到達 | 含まれない |
| CDFER の CSV / SQLite | cdfer.github.io | 到達 | 未確認 |
| raw ファイル | raw.githubusercontent.com | 200 | 含まれる |
| Freerouting の取得 | github.com の `/releases/download/` → release-assets.githubusercontent.com | 200 | github.com は含まれる。release-assets 側は未確認 |
| pcbparts-mcp | pcbparts.dev | 到達 | 含まれない |
| JLCPCB API / LCSC API | jlcpcb.com、wmsc.lcsc.com | 到達 | jlcpcb.com と lcsc.com は含まれない |
| Wokwi | wokwi.com 系（具体的なホスト名は未確認） | 試していない | 含まれない |
| Flatpak | dl.flathub.org | 403（不可） | — |

### 2.3 動かなかったもの・確認できなかったもの

| 対象 | 状態 | 理由 | 確度 |
|---|---|---|---|
| Fabrication Toolkit の CLI 実行 | 未実施 | セッションの権限判定が「外部から取得したコードの実行」として拒否した。想定手順はリポジトリのルートで `/usr/bin/python3.12 -m plugins.cli -p <board> --nonInteractive`（推論）。コードは `import pcbnew` と `import wx` を行い、`is_v10()` の分岐（9.99≤ver<10.99）を持つ | 確認済（拒否の事実） |
| Freerouting の自動配線→SES 取り込み→DRC | 未実施 | 同上。想定手順（未検証）は `tar xzf freerouting-cli-2.5.0-linux-x64.tar.gz && ./freerouting-cli -de dac.dsn -do dac.ses` → `/usr/bin/python3.12 dsn_io.py import dac.kicad_pcb dac.ses routed.kicad_pcb` → `kicad-cli pcb drc` | 確認済（拒否の事実） |
| Freerouting jar の Java 21 での実行 | 未実施 | jar はクラスファイル major version 69 = Java 25 で、MANIFEST は `Created-By: 25.0.4.1 (Eclipse Adoptium ...)`。コンテナの既定は OpenJDK 21.0.12 なので動かないはず（推論）。apt に `openjdk-25-jre-headless 25.0.5.0.3+1-1~24.04.1`（DL 59MB、展開 239MB）がある。ネイティブ CLI は Java 不要 | 確認済（クラス版）／未確認（実行） |
| Pico / Pico 2 の cmake ビルド、UF2 生成、PIO ヘッダ生成、picotool のビルド | 未実施 | 「clone した SDK の CMake スクリプトの実行」として権限判定が拒否した | 確認済（拒否の事実） |
| KiCad の「回路図から基板を更新」（F8 相当）の CLI | 存在しない | kicad-cli 10.0 のサブコマンド一覧に該当なし | 確認済 |
| kicad-cli の Specctra DSN 出力・SES 取り込み | 存在しない | `pcb export --help` / `pcb import --help` で確認。import は pads/altium/eagle/cadstar/fabmaster/pcad/solidworks のみ。SWIG の `pcbnew.ExportSpecctraDSN` で代替できた（3,857 B）。`pcbnew.ImportSpecctraSES` も存在する | 確認済 |
| `kicad-cli pcb export svg --mode-single -o <ディレクトリ>` | 失敗 | "Failed to create file"。`-o` にファイル名を与えれば成功 | 確認済 |
| kiutils による KiCad 10 基板の読み込み | 失敗 | `IndexError: list index out of range`（kiutils/items/common.py:543）。KiCad 10 はパッドのネット参照を `(net "/VOUT")`（番号なし）で書くため | 確認済 |
| kicad-skip による基板の読み込み | 失敗 | `AttributeError: 'Symbol' object has no attribute '_base_coords'`（skip/pcbnew/footprint.py:59）。配線なしの単純な基板でも同じ | 確認済 |
| kinet2pcb（netlist ファイル入力） | 失敗 | `ValueError: Sexp isn't in a form that permits extracting a single value.`（KiCad 10 の netlist の入れ子 value を拾うバグ） | 確認済 |
| SKiDL の `generate_pcb` を `fp_libs` なしで実行 | 失敗 | `KeyError 'Connector_PinHeader_2.54mm'`。kinet2pcb の `get_global_fp_lib_table_fn()` が "9.0".."5.0" しか探さない | 確認済 |
| CDFER SQLite の全文検索（FTS5） | 0件 | `jlc_components_fts` への MATCH が 'RP2350*' でも0件。LIKE 検索を使う | 確認済 |
| jlcsearch の `resistance=10k` 指定 | 期待と異なる | 10Ω 品が返った。パラメータ書式は未確認 | 確認済（現象）／未確認（書式） |
| Flatpak 版 KiCad | 不可 | dl.flathub.org が 403 | 確認済（このクラウド環境での実測） |
| github.com の HTML と api.github.com への素の curl | 不可（403） | プロキシの制限。WebFetch、git、`/releases/download/`、raw.githubusercontent.com、*.github.io は可 | 確認済 |
| MesenCE のコンテナでの `--testRunner` | 未実測 | — | 未確認 |
| Wokwi の動作、RP2350 の PIO の扱い | 未実測 | トークンが必要で、試していない | 未確認 |
| kicad-packages3d 導入時の render | 未実測 | — | 未確認 |

### 2.4 MCP サーバーの評価

「動く場所」は、クラウドの作業環境で動くか、利用者のパソコン（実機や GUI のある環境）でしか動かないかを示す。

| サーバー（リポジトリ） | 用途 | 保守状況（2026-11-10） | ライセンス | 動く場所 | 必要度 | 確度 |
|---|---|---|---|---|---|---|
| pcbparts-mcp（Averyy/pcbparts-mcp） | JLCPCB 部品検索。14ツール（jlc_stock_check、jlc_search、jlc_search_help、jlc_get_part、jlc_find_alternatives、jlc_get_pinout、mouser_get_part、digikey_get_part、cse_search、cse_get_kicad、sensor_recommend、get_design_rules、board_search、board_get）。`library_type` = basic / preferred / no_fee / extended / all | ★144、push 2026-11-10。ホスト版の版表記は `/health` が 0.8.24、serverInfo が "3.4.3"（どちらが製品版か未確認）。SLA なし | MIT | クラウド（HTTP。ホスト版は無認証、100 req/min/IP。Mouser/DigiKey は共有キーで各 1,000 req/日）。自前ホストも可 | 有用（クラウドで最上位） | 確認済（実測） |
| kicad-mcp-pro（oaslananka/kicad-mcp-pro） | 設計レビュー。`default` プロファイルは読み取り24ツール、`build` は編集、`release` は製造出力（人手の確認付き）、`expert/full` は全部 | 4.11.0（PyPI・npm・レジストリとも 2026-11-10）、★206。PyPI 63 リリース（2026-06-21〜）、npm 81 版と更新が非常に頻繁。CI、CodeQL、OpenSSF Scorecard あり | MIT | クラウド（stdio と Streamable HTTP）。KiCad 10 IPC の Companion は利用者のパソコン（読み取り専用・開発プレビュー） | 任意（版固定が必須） | 単一出典 |
| mcp-server-kicad（ProductOfAmerica/mcp-server-kicad） | KiCad 編集。109ツール（回路図42/基板34/プロジェクト24/シンボル5/フットプリント4） | 0.21.1（2026-10-20、計68リリース）。2026-10 から保守モード（セキュリティと KiCad 互換の修正のみ）。★16 | GPL-3.0-or-later（0.20.1 までは MIT） | クラウド（大半はファイル直接解析、`fill_zones`/`autoroute_pcb` は pcbnew Python） | 不要 | 確認済 |
| KiCAD-MCP-Server（mixelpixx/KiCAD-MCP-Server） | KiCad 編集、JLCPCB 部品、Freerouting 統合。「251 tools across 20 categories」（別の節では 244 と自己矛盾） | v2.8.3、★3,255、push 2026-11-10、テスト「1551 Python and 63 TypeScript tests」 | MIT | 「Automatically uses IPC when available, falls back to SWIG」。SWIG 経路ならクラウドでも動くと推論（未検証）。KiCad 9.0+ と pcbnew Python が必須 | 不要（ツール数が多すぎ、SWIG は KiCad 11 で削除見込み） | 単一出典 |
| Konnect（mixelpixx/Konnect） | KiCad 10 プラグイン、Rust 製 | **アーカイブ済み**（2026-11-02 最終 push）。後継 Konnect-EDA は商用・非公開で、1.0 以降は無料版も含め全インストールにライセンスキーが要る。AGPL 版のフォーク（dylbertram/konnect-maintained）あり | AGPL-3.0 | 基板ツールの大半は KiCad GUI 必須 | 不要 | 確認済 |
| Seeed-Studio/kicad-mcp-server | 解析・レビュー寄り24ツール（run_erc/run_drc、detect_pin_conflicts、export_gerber など） | ★184、push 2026-10-22、テスト記載なし | README は MIT（GitHub は未検出） | クラウド（kicad-cli） | 任意 | 単一出典 |
| lamaalrajih/kicad-mcp | プロジェクト一覧、BOM、DRC | ★534、push 2025-10-17（約13か月停滞） | MIT | クラウド（kicad-cli） | 不要 | 確認済 |
| その他の KiCad 系（turbyho/kicad-workbench 0.1.0、nevenfo/kicad-agentic-mcp、belaszalontai/kipilot-mcp、daedalus/mcp-kicad 0.1.1、bunnyf/pcb-mcp 3.5.0、biosshot/kicad-copilot 0.1.0、circuit-synth/mcp-kicad-sch-api、blwfish/kicad-mcp） | — | 若い、停滞、または玩具級 | 各種 | 未確認または GUI 前提 | 不要 | 単一出典 |
| Freerouting 公式 MCP（npm `@freerouting/freerouting-mcp-server`） | 自動配線（`autoroute_board`） | 2.5.0（2026-10-05）、初版 2026-06-16。freerouting 本体 ★2,206、push 2026-11-10。本体の MCP サーバーは v2.3.0 から、`autoroute_board` は v2.5.0 で追加（リリースページ） | GPL-3.0（npm は GPL-3.0-only） | クラウド（ローカル jar の stdio モード）。Public API モードはキーと外部送信が必要 | 不要（CLI で足りる） | 確認済 |
| spicebridge（clanker-lover/spicebridge） | ngspice の解析28ツール | 1.3.0（2026-02-13）、push 2026-04-06（7か月停滞） | GPL-3.0-or-later | クラウド（ngspice 必要） | 不要（ngspice 直で足りる） | 単一出典 |
| ltspice-mcp（Cognitohazard/ltspice-mcp） | LTspice（ngspice でも可） | 0.8.0（2026-11-06）、「Work in progress. Expect breaking changes」 | GPL-3.0-or-later | LTspice は Wine 前提 | 不要 | 単一出典 |
| pdf-mcp（I-CAN-hack/pdf-mcp） | 巨大データシートの検索（search_text、目次、ページ画像） | ★82、push 2026-10-19 | MIT | クラウド（uvx） | 任意（`pdftotext` + `grep` で代替可） | 単一出典 |
| datasheet-lens（turbyho/datasheet-lens） | データシート索引 | 0.6.1（2026-11-10）、README は「version 0.4」で不一致 | MIT | 未確認 | 不要（若すぎる） | 単一出典 |
| embedded-debugger-mcp（Adancurusul/embedded-debugger-mcp） | SWD デバッグ・書き込み・RTT。24ツール。probe-rs または OpenOCD | ★217、push 2026-07-16、テストあり | MIT | 利用者のパソコン（SWD プローブ実機必須） | 有用（実機段階）。RP2040/RP2350 の明記なし | 単一出典 |
| serial-mcp（qarnet/serial-mcp） | シリアルポート25ツール（Pico の USB CDC ログ監視） | 0.9.3、★19、push 2026-11-10 | MIT | 利用者のパソコン（USB 実機必須） | 有用（実機段階） | 単一出典 |
| sigrok-mcp-server（KenosInc/sigrok-mcp-server） | ロジックアナライザ11ツール | 0.2.0、★15、push 2026-10-28 | MIT | 取り込みは利用者のパソコン。デコードはファイルで可 | 有用（実機段階） | 単一出典 |
| Wokwi（wokwi-cli 内蔵、`wokwi-cli mcp`） | Pico ファームのシミュレーション | 実験的。wokwi-cli ★72、push 2026-10-23 | MIT | シミュレーションは Wokwi のクラウドで実行。トークン必須 | 任意 | 確認済（文書） |
| platformio-mcp（jl-codes 3.1.0 / powerdragonfire 0.6.2） | PlatformIO のビルド・書き込み | 活発 | MIT | ビルドはクラウド可、書き込みは実機 | 不要（Pico SDK 直と不一致） | 単一出典 |
| pico-bay（ctrlpi/pico-bay） | MicroPython/CircuitPython 管理 | 0.9.34（2026-11-06） | — | 実機必須 | 不要（C 開発に不適） | 単一出典 |
| easyeda-client-cli（easyeda 公式組織） | EasyEDA Pro の操作 | ★21、push 2026-11-02、クライアント V4.1.70 以上 | Apache-2.0 | 利用者のパソコン（デスクトップクライアント必須） | 不要（KiCad 路線では） | 確認済 |
| atopile 内蔵 MCP | atopile のビルド・JLCPCB 部品導入 | atopile ★4,056、push 2026-10-14 | MIT | クラウド（CLI）と推論 | atopile を採用する場合のみ | 単一出典 |
| JLCPCB/LCSC 系の小規模 MCP（Eyalm321/jlcpcb-mcp、nvsofts/jlcpcb-parts-mcp、hulryung/jlcpcb-skill-mcp、peterb154/jlcpcb-search-mcp、zhr1008/component-sourcing-mcp） | 部品検索 | 若い、停滞（nvsofts は 2025-04-20 で停止）、またはライセンスなし | 各種 | クラウド | 不要 | 単一出典 |
| 流通 API 系（pipeworx-io/mcp-octopart、SpectraSynq/mcp-nexar、bengineer19/digikey_mcp、JPMarhefka/Partuno、mrfentmen の大量登録品） | Octopart/DigiKey/Mouser | キーが必要。mrfentmen は量産型で信頼性が低い | 各種 | クラウド（キー要） | 不要 | 単一出典 |
| Altium / Fusion / tscircuit / EasyEDA 第三者系 | — | — | — | GUI 必須、または設計フローと不一致 | 不要 | 単一出典 |

- ProductOfAmerica の作者自身の比較では、プラグインありの正解 3/18 に対し、素の Claude Code は 18/18 だった。作者自身も「a coding agent such as Claude Code, with KiCad installed」を推奨している。（単一出典）

**MCP なしで足りる工程**

| 工程 | MCP の代わりに使うもの | 確度 |
|---|---|---|
| 回路図・基板の検証と製造出力 | kicad-cli、KiBot | 確認済 |
| 回路図→基板 | SWIG pcbnew の自作スクリプト | 確認済 |
| 部品クラスの判定 | JLCPCB API、jlcsearch（curl） | 確認済 |
| データシート読解 | Claude Code 標準の Read（+ poppler-utils） | 単一出典 |
| アナログ検証 | ngspice 直 | 確認済 |
| 粗配線 | Freerouting CLI（`--gui.enabled=false`） | 未確認（実行未実施） |
| Pico ファームのビルド | Pico SDK + cmake + gcc-arm-none-eabi | 未確認（ビルド未実施） |
| 6502 ROM と自動試験 | cc65、FCEUX/MesenCE の Lua | 確認済（FCEUX）／未確認（MesenCE） |
| ロジックアナライザのデコード | sigrok-cli | 単一出典 |

推奨構成（推論）: クラウドでは `.mcp.json` に pcbparts（HTTP）だけを置き、他はすべてコマンドラインのツールをセットアップスクリプトで導入する。利用者のパソコンでは、実機段階で embedded-debugger-mcp、serial-mcp、sigrok-mcp-server をユーザースコープで追加する。

### 2.5 Claude Code への MCP サーバーの接続方法（要点）

**設定の置き場所**（単一出典: Claude Code 公式文書）

| スコープ | 置き場所 | 共有 | 優先順位 |
|---|---|---|---|
| Local（既定） | `~/.claude.json` | しない | 1 |
| Project | プロジェクト直下の `.mcp.json`（バージョン管理で共有） | する | 2 |
| User | `~/.claude.json` | しない | 3 |
| プラグイン同梱 | プラグイン直下の `.mcp.json` または `plugin.json` | — | 4 |
| claude.ai の connector | claude.ai の customize/connectors で追加 | — | 5 |

- 追加のコマンドは `claude mcp add [options] <name> -- <command> [args...]`、HTTP のサーバーは `claude mcp add --transport http <name> <url>` で、共有するなら `--scope project` を付ける。（単一出典）
- 対話セッションでは、project スコープのサーバーを使う前に承認を求められる。`claude -p`、Agent SDK、プロジェクトのスレッド外のクラウドセッションでは承認画面を出せないので、確認なしで読み込まれる。（単一出典）

**クラウドセッション（claude.ai/code）に持ち込まれる設定**（単一出典: 公式文書）

| 設定 | クラウドに持ち込まれるか |
|---|---|
| リポジトリにコミットした `.mcp.json` | 持ち込まれる（リポジトリが1つのセッション） |
| `claude mcp add` で local / user スコープに追加したサーバー | 持ち込まれない。`claude mcp add --scope project` で追加してファイルをコミットする |
| リポジトリの `.claude/settings.json` で宣言したプラグインとマーケットプレイス | 持ち込まれない |
| claude.ai で追加した connector | クラウドのホストが渡す |

- HTTP のサーバー（pcbparts.dev など）は、Limited 環境では許可ドメインへの追加が要る。Full なら不要である。（単一出典）
- connector の通信は Anthropic のサーバーを経由するため、リモート MCP を claude.ai の custom connector として登録すれば許可リストを変えずに使える可能性が高いが、任意の URL を登録できるかはプラン依存で未確認である。（推論）
- USB 実機を扱う MCP は、利用者のパソコンで動く Claude Code（または Remote Control で自宅のパソコンのセッションを操作）が前提である。（推論）

**`.mcp.json` の例**（推論。動作未確認。URL はコマンドの設定値であり、出典ではない）

```json
{"mcpServers": {
  "pcbparts": {"type": "http", "url": "https://pcbparts.dev/mcp"},
  "kicad-review": {"command": "uvx", "args": ["kicad-mcp-pro==4.11.0"]}
}}
```

- kicad-mcp-pro は更新頻度が高いため、`==4.11.0` のように版を固定しないと再現性が崩れる。既定の起動引数とプロファイル指定方法は未確認である。（推論）

### 2.6 利用者が準備する機材・物

**必須**

| 項目 | 内容 | 理由 |
|---|---|---|
| クラウド環境での実行許可 | Pico SDK のビルド、Freerouting の実行、Fabrication Toolkit の実行を許可する（権限設定、または利用者のパソコンでの実行） | 今回はセッションの権限判定が「外部から取得したコードの実行」として拒否した |
| クラウド環境のネットワーク設定 | Limited 環境なら ppa.launchpadcontent.net、jlcsearch.tscircuit.com、pcbparts.dev、jlcpcb.com、wmsc.lcsc.com、easyeda.com、modules.easyeda.com、cdfer.github.io、release-assets.githubusercontent.com などの許可（どれが既定で通るかは一部未確認） | 2.2 の通信先表のとおり |
| セットアップスクリプトの登録 | 2.2 のスクリプト案（xvfb の追加を検討） | 毎回の導入の手間を省く |
| 利用者のパソコンで動く Claude Code | 実機（Pico、ロジックアナライザ、シリアル）を扱うため | USB 機器はクラウドに届かない |
| ドナーのファミコン | CPU（RP2A03）と PPU（RP2C02）の取り出し | 製品要求 |
| DIP-40 の取り外し道具 | HAKKO FR-301（￥22,000）または goot GS-108（￥1,150）/ エンジニア SS-03（￥2,580）、フラックス | DIP-40 の取り外しのため |
| 静電気対策用品 | リストストラップ（￥1,150）、導電性スポンジ（￥170）、帯電防止袋 | 取り外したチップの保護のため |
| IC ソケット | ZIF 40P 600mil（￥250）または丸ピン40P（￥110） | 試作で CPU/PPU を差し替えるため |
| ロジックアナライザ | DSLogic Plus（$149）または Kingst LA2016（価格未確認） | 16ch・100MS/s 以上 |
| オシロスコープとプローブ | OWON SDS1102（￥39,000）+ プローブ（￥2,000 または ￥2,540） | 100MHz 級 |
| 実機で ROM を走らせる手段 | EverDrive N8 PRO Fami（$159）。または自作カート + XGecu T48 | テスト ROM と自作ゲームの実行 |
| 15kHz 映像の表示手段 | OSSC 1.8（€115.00〜）、RetroTINK のいずれか、または 15kHz 対応 CRT。同期線に 470Ω 直列の試験用ケーブル | OSSC の同期入力は75Ω 終端で、TTL レベルの同期を直結してはいけないため |
| JAMMA 電源とハーネス | MEAN WELL RT-65A（国内価格未確認）+ JAMMA 56ピン端子のハーネス（筐体がない場合） | 筐体なしの試験 |
| Raspberry Pi Pico 2 | 必要な枚数（￥990/枚） | 試作 |
| JLCPCB のアカウント | 発注用 | — |

**任意**

| 項目 | 内容 |
|---|---|
| Wokwi のトークン（`WOKWI_CLI_TOKEN`） | Pico ファームのクラウド模擬。無料枠は過去30日で50分、1セッション5分。非公開プロジェクトは有料プラン |
| SWD デバッグプローブ | embedded-debugger-mcp や openocd で使う（Raspberry Pi Debug Probe での RP2350 対応は未確認） |
| claude.ai の custom connector 登録 | pcbparts-mcp を許可リストの変更なしで使う（登録可否はプラン依存で未確認） |
| JLCPCB / LCSC の公式 API の申請 | 審査制。公開データで足りる |
| Nexar / DigiKey / Mouser のキー | 本件は不要 |
| kicad-packages3d | 3D 描画（DL 280MB / 展開 3.29GB） |

## 3. 選択肢の比較

### 3.1 部品クラス・在庫の判定に使うデータ

| 選択肢 | 費用 | リスク | 判定 |
|---|---|---|---|
| JLCPCB API（画面が呼ぶ JSON） | 無料。Limited 環境では jlcpcb.com の許可が要る | 非公開 API なので仕様変更の恐れがある（推論） | 推奨。BOM の LCSC 番号を照会して最終判定に使う |
| jlcsearch（tscircuit） | 無料、無認証 | クラス判定は JLCPCB API と一致したが、在庫はほとんど null で価格も異なる。JLCPCB と独立した裏取りにならない | 候補の検索・絞り込みに使う |
| pcbparts-mcp（ホスト版） | 無料、無認証、100 req/min/IP | 第三者運営で SLA なし。データ系統と版表記（0.8.24 と 3.4.3）が未確認 | 候補の検索・絞り込みに使う |
| CDFER の CSV / SQLite | 無料、オフライン | Preferred が 1,226 件で JLCPCB の 1,235 件と一致せず、収載漏れあり。全文検索索引は空 | オフラインの下調べだけに使う |
| JLCPCB / LCSC の公式 API | 申請制 | 「Not all applications will be approved」とされ、審査がある | 不要（公開データで足りる、推論） |

### 3.2 製造データ（JLCPCB 向け）の出力

| 選択肢 | 費用 | リスク | 判定 |
|---|---|---|---|
| KiBot 1.9.1（`import: - file: JLCPCB`） | 無料（AGPL-3.0）。導入に `--no-compile` と lxml が要る | 回路図を `kicad-cli sch upgrade --force` で KiCad 10 正規形式にしないと LCSC 列が空になる。CPL の回転補正は未確認 | 推奨。出力を一本化する（推論） |
| `kicad-cli pcb export` 直 | 無料（KiCad 同梱） | JLCPCB 形式の CPL の列名と回転補正を手作業で変換する必要がある（推論） | KiBot の補助 |
| Fabrication Toolkit（bennymeg） | 無料（Apache-2.0） | このクラウド環境では実行未実施 | 未評価（KiBot の代替候補） |
| kicad-jlcpcb-tools（Bouni） | 無料 | GUI 前提でヘッドレスの記載なし | 参考 |

### 3.3 回路図から基板への反映

| 選択肢 | 費用 | リスク | 判定 |
|---|---|---|---|
| 自作 net2pcb.py（SWIG 版 pcbnew） | 約40行の自作 | フットプリントにシンボルへのリンクを設定しないため KiBot が W013 を出す（本番では `footprint.SetPath()` を使うべき、推論）。KiCad 11 で SWIG 削除見込み | 推奨（確認済の経路1） |
| SKiDL 3.0.0 の `generate_pcb` | 無料。導入 217 秒、venv 431MB | `fp_libs` 指定が必須。基板外形は別途追加が要る | 代替（確認済の経路2） |
| kipy（IPC API）+ xvfb 上の pcbnew | 無料 | 起動ウィザード抑止の設定が必須。公式のヘッドレスモードは未実装 | 任意 |
| KiCad 編集用 MCP（mixelpixx など） | 無料 | ツール数が多すぎ、SWIG 依存は KiCad 11 で削除見込み | 不要 |

### 3.4 KiCad 10 のファイル操作ライブラリ

KiCad 10.0.8 が保存した回路図と、配線入りの基板を、各ライブラリで読み込み、無変更で書き出し、kicad-cli で再読込して比べた結果である。（すべて確認済）

| ライブラリ | 版 | 回路図の読み書き | kicad-cli で再読込 | 書き出しで失われる内容 | 基板の読み込み | 判定 |
|---|---|---|---|---|---|---|
| kiutils | 1.4.8 | 可 | ERC 0件、netlist 同一 | **あり**: `hide` 16、`do_not_autoplace` 34、`exclude_from_sim` 6、`in_pos_files` 6、`body_style` 4、`embedded_fonts` 2、`duplicate_pin_numbers_are_jumpers` 2、`generator_version` 1 が消える。非表示の項目が表示に変わるなど、気付きにくい壊れ方をする | **不可**（IndexError） | 使わない |
| kicad-skip | 0.2.5 | 可 | ERC 0件、netlist 同一 | なし（要素数が完全一致。ただし整形は1行に潰れる） | **不可**（AttributeError） | 回路図の読み書きのみ可 |
| kicad-sch-api | 0.5.6 | 可 | ERC 0件、netlist 同一、`(version 20260306)` 維持 | 小: `in_pos_files` 4、`body_style` 4 が消え、`hide` 8、`fields_autoplaced` 4 が増える | 対象外（回路図専用） | 回路図の生成に使える |
| SWIG pcbnew | 10.0.8 | 対象外 | — | — | 可（読込・追加・配線・保存） | 基板の操作に使う |
| kipy（IPC API） | 0.8.0 | 回路図エディタの IPC は使えない | — | — | 可（xvfb 上の GUI 経由） | 任意 |

- kipy の行の「回路図エディタの IPC は使えない」について、シートの別の節は、KiCad 10.0.x に回路図エディタの API ハンドラ自体は存在する模様で、使える命令の範囲は未確認としている。本プロジェクトは回路図をファイル直接編集で扱うので、設計上の影響は小さい（推論）。

### 3.5 新規開発ゲームの自動試験に使うエミュレータ

| 選択肢 | 費用 | リスク | 判定 |
|---|---|---|---|
| FCEUX 2.6.5（apt、xvfb + Lua） | 無料。DL 11.6MB | 公式にヘッドレスのオプションはなく xvfb が要る。上流の最新は 2.7.0 | 当面の主力（実証済み） |
| MesenCE 2.2.1（`--testRunner`） | 無料（GPL-3.0）。SDL2 の手動導入が要る | コンテナでの動作は未実測 | 導入後に高精度の回帰試験に使う（推論） |
| mednafen 1.29.0 / nestopia 1.52.0 | 無料（apt） | 未試験 | 任意 |

### 3.6 実機なしでの Pico ファームの試験手段

| 方法 | できること | できないこと・制限 | 確度 |
|---|---|---|---|
| SDK の host platform（`PICO_PLATFORM=host`） | ハードに依存しないアプリのコードを PC でビルド・試験。pico-host-sdl で pico_multicore、タイマー、scanvideo を追加 | 「sufficient for programs that don't access hardware directly」（ハードを直接触るコードは不可） | 単一出典 |
| rp2040-pio-emulator | Python で単体試験、クロック数の計測、GPIO の時系列表示。JMP/IN/PUSH/PULL/SET/WAIT に対応 | OUT（EXEC 先）と MOV の一部が未実装、IRQ 命令は非対応、ステートマシン1個のみ、IN 用ピンセット非対応、`PULL IFEMPTY`/`PUSH IFFULL` は閾値を無視 | 単一出典 |
| rp2040js | src/peripherals に pio.ts、dma.ts、usb.ts、timer.ts など | フラッシュ書き込みに要る SSI が未実装。RP2350 の記述なし | 単一出典 |
| Wokwi（Pi Pico、RP2040） | GPIO、PIO（PIO Debugger あり）、UART、I2C/SPI（マスタのみ）、PWM、ADC、GDB | 「Only one core is simulated」。DMA は「Only for the PIO peripheral」。SSI は最小限 | 単一出典 |
| Wokwi（Pi Pico 2、RP2350） | PIO ブロック3つ、DMA 16ch 全部、PWM 12 スライス、TIMER0/1、POWMAN、SHA-256、ADC、GDB | Arm コア1つだけ（2つ目の Arm と Hazard3 RISC-V は模擬しない）。RP2350 固有の PIO 命令はない。HSTX は記載なし | 単一出典 |
| Wokwi CI | `wokwi/wokwi-ci-action@v1`、シークレット `WOKWI_CLI_TOKEN`（「starts with `wok_`」）、`expect_text` で合否判定。CLI は `--timeout`（既定30秒）、`--expect-text` | 無料枠は過去30日で50分、1セッション5分（Free と Hobby）。無料プランは公開プロジェクトのみ | 確認済 |
| Wokwi 料金 | Community €0、Hobby €5.6/月（fast build 100分）、Hobby+ €8.1/月、Pro €20/seat/月（「2000 monthly CI minutes」「For commercial projects」） | — | 単一出典 |

推論: 現実的な分担は、PIO の命令論理は rp2040-pio-emulator、コイン・タイマー・クレジットの状態機械は host platform、統合試験は実機とロジックアナライザである。

### 3.7 自動配線（Freerouting 2.5.0）の使い方

| 選択肢 | 費用 | リスク | 判定 |
|---|---|---|---|
| ネイティブ CLI（20,714,066 B） | 無料（GPL-3.0）。Java 不要 | このクラウド環境では実行未実施 | 推奨候補（粗配線して DRC にかける、推論） |
| jar（64,599,107 B） | 無料。`openjdk-25-jre-headless`（DL 59MB、展開 239MB）が要る | jar は Java 25 のクラスファイルで、コンテナ既定の OpenJDK 21.0.12 では動かないはず（推論） | 非推奨 |
| Freerouting 公式 MCP | 無料 | CLI で足りる | 不要 |

### 3.8 ロジックアナライザ（sigrok 対応状況は sigrok wiki）

| 機種 | sigrok | ch | サンプルレート | 価格・入手先（2026-11-10） | 判定 | 確度 |
|---|---|---|---|---|---|---|
| DSLogic Plus | supported（ただし「newer V421/Pango variant ... Currently incompatible with sigrok」） | 16 | 400MHz(4ch)/200MHz(8ch)/100MHz(16ch)。256Mbit、閾値0–5V | $149（定価$199）、dreamsourcelab.com、$100 以上で送料無料。日本の代理店は未確認 | 推奨（16ch 時に 100MHz の最低線を満たす） | 確認済 |
| Kingst LA2016 | supported（2021年11月〜2022年2月以降のソフトを推奨） | 16 | 200MHz max（ch 数による変化の記載なし）。128MB DDR2 | 価格未確認 | 推奨候補 | 単一出典 |
| Kingst LA5016 | supported | 16 | 500MHz max | 価格未確認 | 候補 | 単一出典 |
| DSLogic U3Pro16 | planned（非対応） | 16 | 1GHz(3ch)/500MHz(6ch)/250MHz(12ch)/125MHz(16ch) | $299（定価$399） | sigrok 非対応 | 単一出典 |
| ZEROPLUS LAP-C(16128) | sigrok 対応は別型番 LAP-C(16032) でのみ確認 | 16 | 200M | 秋月 ￥53,800（g103081） | 国内で即納の代替 | 単一出典 |
| ZEROPLUS LAP-C(16064) | 未確認 | 16 | 100M | 秋月 ￥22,800（g104426） | 未評価 | 単一出典 |
| Saleae Logic 8 | **planned（非対応）** | 3/6/7/8 | 100/50/40/25 MS/s（8ch 時 25MS/s） | 秋月 ￥82,800（g108975、通販34台） | 非推奨（高価で sigrok 非対応） | 確認済 |
| fx2lafw 系（いわゆる Saleae 互換） | supported | 8/16 | 「up to 24MHz」 | — | 不足 | 単一出典 |

### 3.9 実機で ROM を走らせる手段と、DIP-40 の取り外し道具

| 選択肢 | 費用 | リスク | 判定 |
|---|---|---|---|
| EverDrive N8 PRO Fami | krikzz.com $159 | 国内販売店・在庫は未確認。互換機は「cannot guarantee compatibility」 | 推奨（まず1台） |
| 自作テストカート + XGecu T48 | T48 の国内価格は未確認 | 5V のパラレル ROM は秋月で見つからず、LCSC でも SST39SF040（C632847）は在庫12・Extended。部品調達のリスクが高い（推論） | 自作カート路線の場合のみ |
| HAKKO FR-301（電動はんだ吸取器） | 秋月 ￥22,000 | — | ドナー基板が多い場合に推奨 |
| goot GS-108 / エンジニア SS-03（手動） | 秋月 ￥1,150 / ￥2,580 | — | 低予算の代替 |

### 3.10 MCP サーバーの採用方針

| 選択肢 | 費用 | リスク | 判定 |
|---|---|---|---|
| MCP を使わず、コマンドラインのツールだけ | 無料 | 部品検索は curl で JLCPCB API と jlcsearch を引く手間がある | 可 |
| クラウドでは pcbparts-mcp だけを `.mcp.json` に置く | 無料。Limited 環境では pcbparts.dev の許可が要る | 第三者の無料サービスで運営継続性が未確認 | 推奨（推論） |
| 上記に kicad-mcp-pro 4.11.0 を設計レビュー補助として追加 | 無料（MIT） | 約5か月で PyPI 63 リリースと更新が激しく、版固定が必須 | 任意 |
| KiCad 編集用の大型 MCP（mixelpixx、ProductOfAmerica、Konnect） | 無料または商用 | ツール数過多、保守モード、アーカイブ済みなど | 不要 |

## 4. ユーザー要求ごとの判断

| 要求 | 判断 | 理由 | 推奨する選択 |
|---|---|---|---|
| 部品は JLCPCB の Basic Parts のみ、LCSC で在庫豊富、手はんだ部品は秋月（要求1章） | 条件つきでできる | Basic の判定と在庫は JLCPCB API で機械的に確かめられる。秋月には API も MCP もないので、人がウェブで在庫を確かめる必要がある。 | KiBot で出した BOM の LCSC 番号をスクリプトで JLCPCB API に照会し、一覧を人が確認する（推論） |
| 安価で実際に作れる基板（要求1章） | 条件つきでできる | 必要なソフトはすべて無料で入手できる。ただし実機確認の機材は円建て部分だけで ￥64,570 かかり、開発時の一度きりの投資として了承が要る（推論）。 | 2.6 の必須品の最小構成から始める（推論） |
| 全部を基板実装メーカーに実装してもらう（要求2章） | 条件つきでできる | KiBot で JLCPCB 用の Gerber zip、BOM、CPL をクラウドで出力できた。CPL の回転補正が正しいかは未確認である。 | 出力は KiBot に一本化し、初回発注では JLCPCB のプレビューで全部品の向きを人が確認する（推論） |
| CPU・PPU を実チップか Raspberry Pi かで選べる、ソケット実装（要求2章） | 条件つきでできる | 同じテスト ROM（AccuracyCoin、rom_singles、240p Test Suite）を両方の構成で走らせれば、同じ物差しで比べられる（推論）。DIP-40 の取り外しには吸取器と静電気対策が要る。 | 試作は ZIF 40P 600mil（￥250）を使い、取り外したチップはすぐ導電スポンジに保管する。ROM の実行には EverDrive N8 PRO Fami を1台用意する（推論） |
| タイマー方式・通常方式と、デフォルト形式・特殊形式（要求3章） | 条件つきでできる | 入力割り当てとコイン・タイマーの論理は状態機械として PC 上で単体試験でき、ゲーム側は FCEUX の Lua で自動試験できる（推論）。エミュレータが「左右同時」「上下同時」をそのまま通すかは未確認である。 | 状態機械は host 試験、ゲーム側は FCEUX（当面）と MesenCE（導入後）の Lua 試験、最終は実機の allpads の3段で検証する（推論） |
| 切り替えはソフトウェアで行う（要求4章） | 未確定 | 新規開発カートリッジと基板の通信手順（$4016 の OUT1・OUT2 と、$4016 の D1・$4017 の D1〜D4）がまだ設計されていない。エミュレータは基板側のファームを模擬しないので、両者を結ぶ試験は実機とロジックアナライザでしかできない（推論）。 | 通信手順は、ゲーム側と基板側で同じ試験データ（書き込み列と期待される応答）を共有する形で設計する（推論） |
| Raspberry Pi は何枚使ってもよい（要求5章） | 条件つきでできる | 複数枚の協調を模擬できるツールは見つかっておらず、16ch のロジックアナライザではボード間通信と CPU バスを同時に見られない場面が出る（推論）。 | 最初は DSLogic Plus（$149、16ch）で始め、必要になったら 32ch 機を追加する。ボード間の通信にはデバッグ用の試験点を基板に設ける（推論） |
| 将来の CPU・PPU・メモリの更新（要求5章） | 条件つきでできる | SWIG 版 pcbnew は KiCad 11 で削除見込みで、MCP は更新が激しいかアーカイブ済みのものがある。KiCad 本体と公式 SDK を中心に据えれば長期の改版に耐えられる（推論）。 | KiCad 10.0.x に固定し、セットアップスクリプトと設計ファイルを一緒にリポジトリで管理する。MCP はレビュー補助（版固定）と部品検索に限る（推論） |
| USB（Type-C）でファームウェアを簡単に更新できる（要求2章・6章） | 未確定 | Pico SDK と picotool のビルドがこの環境で未確認で、USB 実機はクラウドに届かない。Pico 2 の USB 端子は Micro-B で、Type-C 端子 C393939 は在庫 340,763 だが Extended である。 | 最初の試作で、Type-C 端子から全マイコンを更新し、わざと途中で止めて書き込みモードから復旧する試験を行う。そのために利用者のパソコンに Claude Code と picotool を用意する（推論） |

## 5. ユーザーに決めてもらうこと、次に確かめること

### 5.1 ユーザーに決めてもらうこと

1. **Pico SDK のビルド、Freerouting の実行、Fabrication Toolkit の実行を、クラウド環境で許可するか、利用者のパソコンで行うか。** 推奨の既定は、クラウド環境の権限設定で許可することである。今回はセッションの権限判定が拒否したため、これらが動くかどうかが確かめられていない。
2. **クラウド環境のネットワークを Limited のまま必要な通信先だけ足すか、Full にするか。** 推奨の既定は、Limited のまま 2.2 の通信先表で「含まれない」「未確認」とされたホストを足すことである。
3. **セットアップスクリプト案を環境に登録するか、SKiDL を含めるか。** 推奨の既定は、xvfb の導入を足し、SKiDL（約3.5分）を外して登録することである。セットアップが約5分以内に終われば環境ごとキャッシュされる（単一出典）。
4. **実機確認の機材を購入するか。** 推奨の既定は、2.6 の必須品の最小構成（円建て部分 ￥64,570 に、DSLogic Plus $149、EverDrive N8 PRO Fami $159、OSSC 1.8 €115.00〜と JAMMA 電源を加えたもの）である。
5. **実機で ROM を走らせる手段。** 推奨の既定は、自作カートではなく EverDrive N8 PRO Fami を1台買うことである。
6. **MCP サーバーの使い方。** 推奨の既定は、クラウドでは pcbparts-mcp だけを使い、実機段階で利用者のパソコンに embedded-debugger-mcp、serial-mcp、sigrok-mcp-server を足すことである。
7. **Wokwi のトークン（有料プランを含む）を用意するか。** 推奨の既定は、当面は用意しないことである。無料枠は過去30日で50分・1セッション5分で、非公開プロジェクトは有料プランになる。

### 5.2 次に確かめること（順番）

1. Pico（RP2040）/ Pico 2（RP2350）の cmake ビルド、UF2 の生成、PIO ヘッダの生成、picotool の自動ビルド（実行の許可が必要）。
2. `PICO_PLATFORM=host` でのコイン・タイマー・入力形式の論理の単体試験。
3. セットアップスクリプト案を新しい環境で通し実行する。xvfb が元から入っているか、`pip install --no-compile kibot lxml` の一括形が通るか、`$HOME/.config/kicad` 直下の設定で動くかを確かめる。
4. Limited 環境で必要な許可ホストを確定する（ppa.launchpadcontent.net、api.launchpad.net、easyeda.com 系、cdfer.github.io、release-assets.githubusercontent.com、Wokwi のホスト名）。
5. Freerouting のネイティブ CLI による自動配線 → SES の取り込み（SWIG の `ImportSpecctraSES`）→ DRC。
6. Fabrication Toolkit の CLI 実行と、KiBot の出力との比較。JLCPCB 形式の CPL の回転補正を、JLCPCB の発注画面のプレビューで確かめる。
7. JLCPCB 用の設計ルール（.kicad_dru）の数値を決める。最小線幅・間隔を約0.127mm（5mil）とする資料と 3.5mil（0.09mm）とする資料があり、不一致である。
8. MesenCE の Linux ビルドで `--testRunner` がディスプレイなしで動くか。
9. 実機: 購入した Pico 2 / RP2350A のステッピング（A2/A3/A4）を `picotool info -a` などで確かめる。
10. 実機: Pico の PIO がファミコンの M2、PPU の /RD・/WR に正しく同期するかを、ロジックアナライザで位相を見て確かめる。
11. 実機: AccuracyCoin で CPU/PPU/APU をまとめて判定し、失敗項目を blargg の rom_singles で詳しく調べる。240p Test Suite と full_nes_palette で映像と色を調整する。
12. 実機: allpads / read_joy3 で、JAMMA 入力からコントローラ入力への変換を、タイマー方式・デフォルト形式・特殊形式の3つすべてで確かめる。
13. 実機: USB Type-C 端子からのファームウェア更新と、更新失敗時の書き込みモードへの再進入。

## 6. 主要出典

### 1章（この分野の結論）の出典
- KiCad 10.0 CLI 文書（`kicad-cli` のサブコマンド）: https://docs.kicad.org/10.0/en/cli/cli.html
- KiBot（JLCPCB 用出力の定義）: https://github.com/INTI-CMNB/KiBot
- KiCad 開発者メーリングリスト（SWIG の扱い、ヘッドレスモードの予定）: https://groups.google.com/a/kicad.org/g/devlist/c/3e8OU0FiEHc
- JLCPCB 部品検索 API（Basic・Preferred 件数の一次データ）: https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- CDFER jlcpcb-parts-database（オフライン一覧）: https://github.com/CDFER/jlcpcb-parts-database
- pcbparts-mcp（部品検索 MCP）: https://github.com/Averyy/pcbparts-mcp
- pico-sdk のリリース（2.3.1 の版と日付）: https://api.github.com/repos/raspberrypi/pico-sdk/releases
- Freerouting のリリース（2.5.0、MCP の導入版）: https://github.com/freerouting/freerouting/releases
- FCEUX の Lua 関数一覧: https://fceux.com/web/help/LuaFunctionsList.html
- MesenCE の Lua API ソース（`emu.stop` の確認）: https://raw.githubusercontent.com/nesdev-org/MesenCE/master/Core/Debugger/LuaApi.cpp

### 2章（表）の出典
- Claude Code の MCP 文書（設定の置き場所とコマンド）: https://code.claude.com/docs/en/mcp
- Claude Code のクラウド環境文書（持ち込まれる設定、許可リスト）: https://code.claude.com/docs/en/cloud-environments
- kicad-mcp-pro（版と保守状況）: https://github.com/oaslananka/kicad-mcp-pro
- mixelpixx/KiCAD-MCP-Server の README（IPC と SWIG の切り替え、ツール数）: https://raw.githubusercontent.com/mixelpixx/KiCAD-MCP-Server/main/README.md
- Konnect-EDA（Konnect の商用後継）: https://github.com/Orchis-ai-LLC/Konnect-EDA
- EverDrive N8 PRO Fami（仕様と価格）: https://krikzz.com/our-products/cartridges/n8-pro-fami.html
- MEAN WELL RT-65 仕様書（JAMMA 電源）: https://www.meanwell.com/Upload/PDF/RT-65/RT-65-SPEC.PDF
- OSSC 製品ページ（価格と在庫）: https://videogameperfection.com/products/open-source-scan-converter/

### 3章（選択肢の比較）の出典
- sigrok wiki の DSLogic Plus（対応状況と新しいハードの非互換）: https://sigrok.org/wiki/DreamSourceLab_DSLogic_Plus
- DreamSourceLab ショップ（DSLogic の価格）: https://www.dreamsourcelab.com/shop/
- SDK host platform の README（ハードを触らないコードの試験）: https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/host/README.md
- Wokwi の Pi Pico 2（模擬の範囲）: https://docs.wokwi.com/parts/board-pi-pico-2
- HAKKO FR-301 仕様: https://www.hakko.com/japan/products/hakko_fr301_spec.html

### 4章（ユーザー要求ごとの判断）の出典
- AccuracyCoin（CPU/PPU/APU の判定 ROM）: https://github.com/100thCoin/AccuracyCoin
- picotool のリリース（2.3.1、`bdev` と `uf2 combine`）: https://api.github.com/repos/raspberrypi/picotool/releases
