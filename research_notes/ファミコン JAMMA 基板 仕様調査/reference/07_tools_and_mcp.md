# 設計・検証に必要なソフトウェアと MCP サーバー - リファレンスシート

- 基板設計は KiCad 10.0.8 とそのコマンドライン版 `kicad-cli` だけで、回路図の検査から JLCPCB 向け製造データ（Gerber、ドリル、部品配置、部品表）の出力まで、画面のないクラウド環境で実際に動いた。回路図から基板への反映は SWIG 版 `pcbnew`（`/usr/bin/python3.12` 限定）の自作スクリプトで行う。
- MCP サーバーは必須ではない。ほとんどの工程はコマンドラインのツールを直接使う方が確実で、クラウドで価値があるのは部品検索の pcbparts-mcp くらいである。ただし部品クラス（Basic など）の最終判定は JLCPCB 自身のデータで行う。
- Pico SDK による Raspberry Pi Pico 系のファームウェアのビルド、Freerouting による自動配線、Fabrication Toolkit の実行は、このクラウド環境では実行の許可が下りず未確認である。6502 用の cc65、エミュレータ FCEUX の自動試験、回路シミュレータ ngspice は動いた。
- 実機の確認には、16ch・100MS/s 以上のロジックアナライザ、100MHz 級のオシロスコープ、フラッシュカート、15kHz 映像を受けられる表示手段、JAMMA 用電源、DIP-40 の取り外し道具と静電気対策用品が要る。USB 機器を扱う MCP は利用者のパソコンでしか動かない。
- データの日付: 2026-11-10

## 1. 確定事実

### 1.1 用語と確度の付け方

- **MCP（Model Context Protocol）サーバー**: AI エージェント（ここでは Claude Code）に外部ツールを「関数」として提供する仕組み。コマンドラインのツールを AI が直接実行できる環境では、必ずしも必要ではない。
- **ヘッドレス**: 画面（ディスプレイ）なしでプログラムを動かすこと。
- **xvfb**: 画面のないマシンで仮想の画面を作るソフト。`xvfb-run` コマンドで GUI のプログラムを画面なしで起動できる。
- **kicad-cli**: KiCad に付属するコマンドライン版。回路図の電気的検査（ERC）、基板の設計ルール検査（DRC）、各種ファイル出力ができる。
- **SWIG 版 pcbnew**: KiCad 付属の Python モジュール `pcbnew`。基板ファイルを Python から直接読み書きできる。KiCad 11 で削除される見込み。
- **IPC API と kipy**: 起動中の KiCad（GUI）に外部プログラムから命令を送る新しい仕組みと、その Python 用ライブラリ（PyPI 名 `kicad-python`）。
- **Basic / Preferred（Promotional Extended）/ Extended**: JLCPCB の部品分類。現行の jlcpcb.com の画面では Preferred は「Promotional Extended」というフィルタ名で表示され、部品のバッジは「Extended」としか表示されない。
- **UF2**: Raspberry Pi Pico 系にファームウェアを書き込むためのファイル形式。**picotool** はその書き込みや情報表示を行う公式ツール。**PIO** は RP2040/RP2350 が持つ、タイミング精度の高い入出力専用の小型プロセッサ。
- **テスト ROM**: ファミコン（NES）の CPU・PPU・APU の動作を自動判定するために作られたソフト。
- 確度の記号: **確認済** = 独立した出典が2つ以上、またはこのクラウド環境での実測・ライブデータ・データシート。**単一出典** = 出典が1つだけ（README の記述など）。**未確認** = 確かめられていない。

### 1.2 工程別の必須ツールと任意ツール

「クラウドで動作」は、このクラウド環境（Ubuntu 24.04、root、4CPU のコンテナ）で実際に動かした結果である。

#### 回路図

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

#### 部品選定

| ツール | 区分 | 版数・データ日 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| JLCPCB の部品検索 API（jlcpcb.com/parts の画面が呼ぶ JSON） | 必須（Basic/Preferred 判定の一次データ） | ライブ | HTTPS の POST。Playwright で画面操作時の通信を捕捉して確認したもの | 動作した（Basic 351 件、Preferred 1,235 件を全件取得） | 確認済 |
| jlcsearch（tscircuit） | 推奨（候補の検索・絞り込み。MCP ではない HTTP API。jlcparts と同系統のデータなので、JLCPCB と独立した裏取りにはならない。1.6.1） | 毎日同期 | HTTPS の GET、無認証 | 動作した（GET は 200。HEAD は 405） | 確認済 |
| CDFER/jlcpcb-parts-database | 任意（オフラインの一覧） | 2026-11-10 版 | HTTPS で CSV（1,252,216 B）と SQLite（419,360,768 B）を取得 | 動作した。ただし全文検索索引は空で、Preferred 件数が JLCPCB と一致しない | 確認済 |
| pcbparts-mcp（ホスト版） | 任意（最も実用的な部品検索 MCP） | `/health` は 0.8.24、serverInfo は "3.4.3" | HTTP の MCP、無認証、100 req/min/IP | 動作した（JSON-RPC を curl で実行） | 確認済 |
| LCSC の商品データ API（商品ページのデータ源） | 任意（LCSC 倉庫の在庫・価格。クラス情報なし） | ライブ | HTTPS の GET | 動作した | 確認済 |
| Claude Code 標準の Read ツール + poppler-utils | 必須（データシート読解） | — | `apt-get install poppler-utils` | 文書上の機能（20 ページ単位で PDF を読める） | 単一出典 |
| 秋月電子の在庫確認 | 必須（手はんだ部品） | — | 公開 API・MCP は見つからない。人がウェブで確認 | — | 単一出典 |

#### 配置配線

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| SWIG 版 pcbnew（KiCad 同梱） | 必須（回路図→基板の反映、配置、配線追加） | 10.0.8 | KiCad に同梱。`/usr/bin/python3.12` で使う | 動作した（読込・フットプリント追加・配線・保存・Gerber・Specctra DSN 出力） | 確認済 |
| 自作 net2pcb.py（約40行） | 必須（「回路図から基板を更新」の代わり） | — | 自作（SWIG pcbnew 使用） | 動作した（schematic parity 0 件） | 確認済 |
| kipy（kicad-python）+ IPC API | 任意（GUI の KiCad を外部から操作） | 0.8.0（2026-08-30） | pip | xvfb 上の pcbnew で動作した（起動ウィザード抑止の設定が必須） | 確認済 |
| Freerouting | 任意（粗い自動配線） | 2.5.0（2026-10-05） | GitHub Releases（jar 64,599,107 B、またはネイティブ CLI 20,714,066 B） | ダウンロードと sha256 照合のみ。実行は許可されず未実施 | 確認済（取得）／未確認（実行） |
| KiKit | 任意（パネル化。JAMMA 基板が1枚なら不要） | 1.8.1（2026-08-05） | pip | 試していない | 単一出典 |
| JLCPCB 用設計ルール（.kicad_dru） | 必須（DRC 用） | JLCPCB 公式品は見つからない。コミュニティ版あり | — | 試していない。最小線幅・間隔の値は資料間で不一致 | 未確認 |

#### 検証

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| `kicad-cli sch erc` / `kicad-cli pcb drc --schematic-parity` | 必須 | 10.0.8 | KiCad に同梱 | 動作した | 確認済 |
| `kicad-cli pcb render` | 任意（基板の画像） | 10.0.8 | KiCad に同梱 | xvfb なしで動作した（800x450 が 1.9 秒） | 確認済 |
| ngspice | 必須（映像 DAC・RGB 増幅・音声のアナログ検証） | 42 | apt | 動作した（`ngspice -b` のバッチ実行） | 確認済 |
| kicad-mcp-pro（`default` プロファイル） | 任意（設計レビュー補助） | 4.11.0（2026-11-10） | uvx（版の固定が必須） | 試していない | 単一出典 |

#### 製造データ出力

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| `kicad-cli pcb export gerbers/drill/pos`、`sch export bom` | 必須 | 10.0.8 | KiCad に同梱 | 動作した。ただし JLCPCB 形式の部品配置表の列名と回転補正は手作業での変換が要る（推論） | 確認済 |
| KiBot（JLCPCB 用の出力一式を YAML で定義） | 必須（推奨経路） | 1.9.1（2026-07-28）、AGPL-3.0 | pip（`--no-compile` と lxml が必要） | 動作した（JLCPCB 用 zip、BOM、CPL を出力） | 確認済 |
| Fabrication Toolkit（bennymeg） | 任意（KiBot の代替） | HEAD 7f627b6（2026-09-29）、metadata.json の先頭版 "5.3.1"、Apache-2.0 | git clone | clone のみ。実行は許可されず未実施 | 未確認 |
| kicad-jlcpcb-tools（Bouni） | 参考 | KiCad 7〜10 対応と表記 | KiCad のプラグイン | GUI 前提。ヘッドレスの記載なし | 単一出典 |

#### ファームウェア

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

#### シミュレーション

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

#### 実機確認

| ツール | 区分 | 版数 | 入手方法 | クラウドで動作 | 確度 |
|---|---|---|---|---|---|
| sigrok-cli / PulseView | 必須（ロジックアナライザ使用時） | 0.7.2 / 0.4.2 | apt | 取り込みは実機が必要。保存したキャプチャのデコードはクラウドでも可能（推論） | 単一出典 |
| minipro | 必須（XGecu T48 使用時） | タグ12個、最新版数は未確認 | GitLab からビルド | 実機が必要 | 単一出典 |
| picotool（実機への書き込み） | 必須 | 2.3.1 | 上記 | 実機が必要 | 確認済（版） |

### 1.3 動作を確認した導入手順・セットアップスクリプト案・通信先

#### 1.3.1 動作を確認した手順と注意点

1. **KiCad 10 の導入**（確認済）
   - `add-apt-repository -y ppa:kicad/kicad-10.0-releases` はそのままでは `ModuleNotFoundError: No module named 'apt_pkg'` で失敗した。原因は `/usr/bin/python3` が alternatives で python3.13 を指し、`apt_pkg` が python3.12 用しかないこと。
   - `python3.12 /usr/bin/add-apt-repository -y ppa:kicad/kicad-10.0-releases` で成功した（5.6 秒）。
   - 代替として、keyserver.ubuntu.com から鍵 `FDA854F61C4D0D9572BB95E5245D5502FAD7A805` を取り、`signed-by` で指定する方法でも `apt update` が成功した。
   - `apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints` は 20 秒、DL 151MB、apt 表示 947MB（実測約 840MB）、新規 78 + 更新 1 パッケージ。
   - `kicad-cli version` は 10.0.8（`KICAD_IPC_API=ON`、ngspice 42、OCC 7.6.3）。
   - 3D モデル（kicad-packages3d、DL 280MB / 展開 3.29GB）は入れていない。`pcb render` は部品本体なしで基板・パッド・シルクを描いた。
2. **KiCad の初期設定**（確認済）
   - 初回実行で `~/.config/kicad/10.0/` は作られるが、`sym-lib-table` と `fp-lib-table` は作られない。そのままでは ERC が「The current configuration does not include the symbol library 'Device'」と警告する。
   - `/usr/share/kicad/template/{sym,fp}-lib-table` を設定ディレクトリにコピーすれば解決した。
   - GUI（IPC API 用）を画面なしで起動するには、さらに `design-block-lib-table` と、次の `kicad_common.json` が必要（下記 1.5.4）。
3. **Python の使い分け**（確認済）
   - KiCad の `_pcbnew.so` は libpython3.12 にリンクされている。このコンテナの既定 `python3` は 3.13（`/usr/local/bin`）だが、`/usr/lib/python3/dist-packages` を読むため import 自体は通ってしまう。異なる libpython が混ざって危険なので、**pcbnew は必ず `/usr/bin/python3.12` で使う**。
4. **KiBot**（確認済）
   - `python3.12 -m venv --system-site-packages` の venv に `pip install kibot`（5 秒、35MB）。
   - 1回目は `cannot import name 'macros' from 'kibot.macros'` で失敗した。`pip install --no-compile --force-reinstall --no-deps kibot` と `__pycache__` の削除で解決し、次に `No module named 'lxml'` が出たので `pip install lxml` で解決した。
   - 一括形 `pip install --no-compile kibot lxml` は、成功した3段の手順を1行にまとめたもので、そのままの形では試していない（未確認）。
5. **ファームウェア用ツール**（確認済）
   - `apt-get install -y --no-install-recommends gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib cmake ninja-build build-essential cc65 ngspice` は 35 秒、DL 581MB、ディスク約 3.0GB 増（大半は newlib と libstdc++ のマルチライブラリ）。
   - `git clone -b 2.3.1 --depth 1` で pico-sdk を取得し、`git submodule update --init --depth 1`（tinyusb、cyw43-driver、lwip、mbedtls、btstack）は 17 秒で成功した。セッションの git プロキシ経由のサブモジュール取得は動いた。
6. **Freerouting の取得**（確認済）
   - github.com の HTML ページや API への素の curl は 403 だが、`/releases/download/` のパスは通る（release-assets.githubusercontent.com へ転送されて 200）。
   - `freerouting-cli-2.5.0-linux-x64.tar.gz` の sha256 は公式チェックサムと一致した。中身は単一の実行ファイル `freerouting-cli`（50,202,888 B）。
7. **FCEUX**（確認済）
   - `apt-get install -y --no-install-recommends fceux` は 7 秒、DL 11.6MB、24 パッケージ。実行ファイルは `/usr/games/fceux` で、PATH に入っていない。

#### 1.3.2 クラウド環境用セットアップスクリプト案

このスクリプトは、上記で実行・成功したコマンドだけを、繰り返し実行しても壊れないように `if` や `[ -f ]` で包んだものである（確認済の手順の組み合わせ。スクリプト全体としての通し実行は未確認）。Freerouting の実行、Pico SDK のビルド、Fabrication Toolkit の実行は未検証のため、取得だけにとどめている。スクリプト中の URL はコマンドの引数であり、出典ではない（出典は 5 章）。

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
- kiutils と kicad-skip は基板ファイルを読めない（1.5.3）。スクリプト案では導入しているが、使う予定がなければ外してよい（推論）。
- 公式文書によれば、クラウド環境のセットアップスクリプトは約5分以内に終われば環境ごとキャッシュされる（単一出典）。上記の見込み（約5分20秒）はその境目にあり、SKiDL（約3.5分）を外せば確実に収まる（推論）。
- クラウドの作業マシンの目安は Ubuntu 24.04 x86_64、4 vCPU / 16GB RAM / 30GB ディスクで、Python+uv、Node 20/21/22、OpenJDK 21、GCC/Clang/cmake/ninja、Docker が入っている（単一出典）。ディスク約5GB の追加は収まる（推論）。

#### 1.3.3 各手順が必要とする通信先

調査を行ったセッション自身のネットワーク設定は無制限（Full）だった。制限付き（Limited）環境で使う場合の可否は、既定の許可リストと照らし合わせた結果を右の列に記す。

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

### 1.4 動かなかったもの・確認できなかったもの

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

### 1.5 KiCad 10 のファイル操作ライブラリと、画面なしで回路図から基板まで進める手順

#### 1.5.1 KiCad 10 のファイル形式

- 回路図: `(version 20260306)` `(generator_version "10.0")`。
- 基板: `(kicad_pcb (version 20260206) (generator_version "10.0"))`。
- `kicad-cli sym upgrade --force` でシンボルは `version 20251024`、`kicad-cli fp upgrade --force` でフットプリントは `version 20260206` になった。（確認済）

#### 1.5.2 kicad-cli のヘッドレス実行結果（画面なし、xvfb なし）

テスト回路は、kicad-sch-api で作った4部品（J1 Conn_01x04、R1 470、R2 1k、R3 75）の映像 DAC 風の回路。（すべて確認済）

| コマンド | 結果 | 時間 |
|---|---|---|
| `kicad-cli sch erc -o erc.rpt dac.kicad_sch` | 成功（lib-table 設定後 0 violations） | 0.4s |
| `kicad-cli sch upgrade --force` | 成功（KiCad 10 回路図形式になる） | <1s |
| `kicad-cli sch export netlist -o dac.net` | 成功（4ネット正しい） | <1s |
| `kicad-cli sch export bom -o bom.csv --fields 'Reference,Value,Footprint,${QUANTITY}' --group-by Value` | 成功 | <1s |
| `kicad-cli pcb drc --schematic-parity -o drc.rpt` | 成功（parity 0件、未配線6件は想定どおり） | 3.9s |
| `kicad-cli pcb export gerbers -o out/gerber/` | 成功（`--layers` 未指定だと全レイヤ29ファイルを出力） | 0.4s |
| `kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2` | 成功 | 0.4s |
| `kicad-cli pcb export pos --format csv --units mm --side both` | 成功 | 0.2s |
| `kicad-cli pcb export pdf --layers F.Cu,F.SilkS,Edge.Cuts` | 成功 | 0.3s |
| `kicad-cli pcb export svg --mode-single -o out/plots/` | 失敗（"Failed to create file"）。`-o` にファイル名を与えれば成功 | 0.3s |
| `kicad-cli sch export pdf` / `sch export svg` | 成功 | 0.3s |
| `kicad-cli pcb export step` / `glb` / `ipc2581` / `odb` | 成功 | <0.4s |
| `kicad-cli pcb render -o x.png` | 成功（xvfb 不要、CPU のレイトレーサ）。`--quality high --rotate '-45,0,45' --floor --perspective` で 800x450 が 1.9s | 0-2s |

補足（単一出典）:
- kicad-cli 10.0 のサブコマンドは `fp`（export svg、upgrade）、`jobset run`、`pcb`（drc、export の多数の形式、import、render、upgrade）、`sch`（erc、export {bom, dxf, netlist, pdf, ps, python-bom(旧), svg}、upgrade）、`sym`（export、upgrade）、`version`。HPGL 出力は 10.0 で非対応。`sch export bom --include-excluded-from-bom` は 10.0 で非推奨・無効。
- macOS の 10.0.4 で「画面サーバーがなく DRC 違反があると `kicad-cli pcb drc` が落ちる」不具合（#25413）は 10.0.7 で修正済み。

#### 1.5.3 ファイル操作ライブラリの可否

KiCad 10.0.8 が保存した回路図と、配線入りの基板を、各ライブラリで読み込み、無変更で書き出し、kicad-cli で再読込して比べた。（すべて確認済）

| ライブラリ | 版 | 回路図の読み書き | kicad-cli で再読込 | 書き出しで失われる内容 | 基板の読み込み | 判定 |
|---|---|---|---|---|---|---|
| kiutils | 1.4.8 | 可 | ERC 0件、netlist 同一 | **あり**: `hide` 16、`do_not_autoplace` 34、`exclude_from_sim` 6、`in_pos_files` 6、`body_style` 4、`embedded_fonts` 2、`duplicate_pin_numbers_are_jumpers` 2、`generator_version` 1 が消える。非表示の項目が表示に変わるなど、気付きにくい壊れ方をする | **不可**（IndexError） | 使わない |
| kicad-skip | 0.2.5 | 可 | ERC 0件、netlist 同一 | なし（要素数が完全一致。ただし整形は1行に潰れる） | **不可**（AttributeError） | 回路図の読み書きのみ可 |
| kicad-sch-api | 0.5.6 | 可 | ERC 0件、netlist 同一、`(version 20260306)` 維持 | 小: `in_pos_files` 4、`body_style` 4 が消え、`hide` 8、`fields_autoplaced` 4 が増える | 対象外（回路図専用） | 回路図の生成に使える |
| SWIG pcbnew | 10.0.8 | 対象外 | — | — | 可（読込・追加・配線・保存） | 基板の操作に使う |
| kipy（IPC API） | 0.8.0 | 回路図エディタの IPC は使えない（1.5.4） | — | — | 可（xvfb 上の GUI 経由） | 任意 |

- kicad-sch-api で新規作成した回路図は KiCad 9 形式（`(version 20250114)` `(generator_version "9.0")`）で出力されるが、kicad-cli 10.0.8 で ERC 0件、netlist も正常。`kicad-cli sch upgrade --force` で KiCad 10 形式にできる。（確認済）
- SKiDL 3.0.0 は `set_default_tool(KICAD10)` を持つ。`lib_search_paths[KICAD10].append("/usr/share/kicad/symbols")` で `Part("Device","R")` を解決し、`generate_netlist()`、`generate_schematic()`（出力は `(version 20250114)` `(generator "skidl")`、ERC は `lib_symbol_mismatch` 警告4件と `power_pin_not_driven` 1件）、`generate_pcb(file_=..., fp_libs=["/usr/share/kicad/footprints"])`（4つのフットプリントを自動配置し、パッドにネットを割当。DRC は外形なしの `invalid_outline` 1件と未配線6件のみ）が成功した。（確認済）

#### 1.5.4 IPC API（kipy）を画面なしで使う方法

- IPC API のサーバーは GUI の pcbnew が提供する。`kicad_common.json` の `"api": {"enable_server": true}` で有効になり、ソケットは `/tmp/kicad/api.sock`。（確認済）
- 1回目は `xvfb-run -a pcbnew board.kicad_pcb` でソケットはできたが、kipy は `ApiError: KiCad returned error: KiCad is not ready to reply` を返した。原因は初回起動ウィザード「Welcome to KiCad 10.0 / KiCad Setup」が画面上で待っていたこと。（確認済）
- ウィザードは、設定ディレクトリが無効、ライブラリ表が揃っていない（**sym-lib-table、fp-lib-table、design-block-lib-table の3つが必要**）、更新確認・データ収集の確認が未回答、のどれかで表示される（KiCad 10.0 ブランチのソース `common/startwizard/*.cpp` で確認）。（確認済）
- **完全に対話なしで起動する方法**: 空の設定ディレクトリに3つの lib-table と、次の `kicad_common.json` を置く。`xvfb-run -a pcbnew board.kicad_pcb &` から約3秒で kipy が応答した。（確認済）
  `{"api":{"enable_server":true},"do_not_show_again":{"update_check_prompt":true,"data_collection_prompt":true}}`
- kipy で成功した操作: `KiCad().get_version()`→`10.0.8`、`get_board()`、`get_footprints()`、`get_nets()`、`create_items(Track)`（B.Cu）、`board.save()`。保存結果は kicad-cli の DRC で再読込できた。（確認済）
- 公式のヘッドレスモードは未実装で、kicad-cli の機能（バックグラウンドサーバー）として実装予定と KiCad 開発者が述べている（2026-01-06）。SWIG（pcbnew.py）は KiCad 10 では削除されないが、開発版 10.99 では削除されたとの報告がある（KiCad 11 で削除見込み）。（単一出典）
- 回路図エディタ（eeschema）の IPC API の範囲は、出典が食い違っており未確認（2 章・3 章参照）。

#### 1.5.5 画面なしで「回路図 → フットプリント配置済みの基板」を作る手順（実証済み）

経路1（推奨。確認済）:
1. 回路図を作る（kicad-sch-api で生成するか、AI が S 式を直接書く）。
2. `kicad-cli sch upgrade --force` で KiCad 10 正規形式にする（KiBot が LCSC 列を正しく読むために必要。1.6.3）。
3. `kicad-cli sch erc` で検査する。
4. `kicad-cli sch export netlist` で netlist を出す。
5. `/usr/bin/python3.12 net2pcb.py` を実行する。自作スクリプト（約40行）は netlist を正規表現で読み、`FootprintLoad` → `SetPosition` → `pad.SetNet()` → Edge.Cuts の外形 → `SaveBoard` を行う。
6. `kicad-cli pcb drc --schematic-parity` で回路図との一致を確かめる（parity 0件）。

経路2（確認済）: SKiDL で回路を Python で書き、`generate_pcb(fp_libs=[...])` で基板を作り、kicad-cli の DRC で確かめる。基板外形は別途追加が要る。

注意:
- 自作 net2pcb.py はフットプリントにシンボルへのリンク（パス/UUID）を設定しないため、KiBot が `W013 ... not linked to an existing schematic component` を出した。出力は参照名で照合されるので正しかったが、本番では `footprint.SetPath()` で netlist の tstamps を設定すべきである（推論）。
- 配置は人間のレビューが必須で、配線は Freerouting で粗く配線して DRC にかける運用を想定している（推論。Freerouting の実行は未確認）。
- 配線の追加（SWIG pcbnew で `PCB_TRACK` 3本を追加して保存）は、kicad-cli DRC で 0 violations、未配線 6→5 と認識された。（確認済）

### 1.6 部品データの情報源と信頼性

#### 1.6.1 情報源の性格

| 情報源 | 性格 | 独立性 | 確度 |
|---|---|---|---|
| JLCPCB API（画面が呼ぶ JSON。`componentLibraryType` = `base`/`expand`、`preferredComponentFlag`、`stockCount`、`componentPrices`） | JLCPCB の一次データ（ライブ） | 独立 | 確認済 |
| JLCPCB の画面（検索画面と partdetail ページ） | JLCPCB の一次データ（表示） | 独立 | 確認済 |
| LCSC API | LCSC 倉庫の在庫・価格。JLCPCB の組立在庫とは別倉庫で、クラス情報はない | 独立（在庫・価格のみ） | 確認済 |
| jlcsearch | jlcparts 派生 | 低い | 確認済 |
| jlcparts（yaqwsx） | CDFER の上流。JLCPCB を巡回取得したもの | 低い | 確認済 |
| CDFER | jlcparts 由来 | 低い | 確認済 |
| pcbparts-mcp | 第三者運営の無料サービス（データ系統は未確認） | 未確認 | 単一出典 |

- jlcsearch、jlcparts、CDFER はすべて同じ jlcparts の巡回データ系統で、互いに「独立した第2の出典」にはならない。真に独立なのは JLCPCB 自身（API と画面）と LCSC API（在庫・価格のみ）である。（確認済）

#### 1.6.2 実測でわかった信頼性

| 事実 | 値 | 確度 |
|---|---|---|
| JLCPCB の Basic 件数 | 351 件（JLCPCB API）。jlcparts の `library_type='base'` も 351 件で C 番号集合が完全一致。CDFER の CSV は 352 件（CDFER の最新 fetched_at は 2026-10-28） | 確認済 |
| JLCPCB の Preferred 件数 | 1,235 件（うち在庫>0 は 1,220）。jlcparts は 989 件、CDFER は 1,226 件で、どちらも一致しない | 確認済 |
| jlcsearch のクラス判定 | 全 C 番号で JLCPCB API と一致 | 確認済 |
| jlcsearch の在庫・価格 | 在庫はほとんど null、価格は JLCPCB API と異なる（例 C5605: jlcsearch 1-49 個 $0.1242、JLCPCB $0.0763）。一部の C 番号で HTTP 500 が出たが再試行で取得できた | 確認済 |
| jlcparts / CDFER の収載漏れ | 21.47727MHz 水晶 C5289705（JLCPCB 在庫 2,648）や C2835971、C5345032、C5265730 は jlcparts に行がない | 確認済 |
| 在庫値の食い違い（RP2040 C2040） | jlcsearch の `/api/search` 86,210、CDFER 53,168、JLCPCB API 84,778、LCSC 84,880（取得時刻の差と推定） | 確認済（値）／推論（原因） |
| pcbparts-mcp と jlcsearch の一致 | 74HC245 は Basic 0件、Preferred は C5625（74HC245D,653、SOIC-20-300mil、在庫 52,801）のみ。2つの情報源が一致（ただし独立性は未確認） | 確認済 |
| jlcsearch の正しい書式 | `components/list.json?search=Cxxxx`。`/api/search?q=` も 200 を返した | 確認済 |
| JLCPCB の画面での Preferred の表示 | フィルタ名「Promotional Extended」、部品行と詳細ページのバッジは「Extended」のみ。画面だけ見ると Preferred を普通の Extended と誤認しうる | 確認済 |

結論（推論）: 部品クラス・在庫・価格の最終判定は JLCPCB API で行う。jlcsearch と pcbparts-mcp は検索と絞り込みに使い、CDFER はオフラインの下調べにだけ使う。

#### 1.6.3 KiBot による JLCPCB 出力の実測（確認済）

- 設定ファイル（全文）:
  ```yaml
  kibot:
    version: 1
  global:
    field_lcsc_part: LCSC
  import:
    - file: JLCPCB
  ```
- `kibot -c jlc.kibot.yaml -b dac.kicad_pcb -e dac.kicad_sch -d out` は 2 秒、rc=0。
- 出力: `out/JLCPCB/dac-_JLCPCB_compress.zip`（F/B Cu、Silk、Mask、Edge_Cuts、PTH/NPTH の drl と map の 11 ファイル）、`dac_bom_jlc.csv`（Comment、Designator、Footprint、"LCSC Part #"）、`dac_cpl_jlc.csv`（Designator、Val、Package、Mid X、Mid Y、Rotation、Layer）。
- 落とし穴: kicad-sch-api が書いた KiCad 9 形式の回路図では、KiBot が `W036 Component without the basic fields` を出し LCSC 列が空になった。`kicad-cli sch upgrade --force` で KiCad 10 正規形式にしてから渡すと、LCSC 列（C2337、C4275、C23179、C21190）が正しく入った。
- 使った LCSC 番号を CDFER の CSV で照合した結果: C23179 0603WAF4700T5E（base）、C21190 0603WAF1001T5E（base）、C4275 0603WAF750JT5E（base）、C2337 は CSV になし（= Extended）。

#### 1.6.4 ライブラリ化ツールの実測（確認済）

| コマンド | 結果 |
|---|---|
| `easyeda2kicad --full --lcsc_id=C2040 --output <dir>/lib` | 2 秒。シンボル RP2040（`kicad_symbol_lib (version 20211014)` = KiCad 6 形式）、フットプリント `LQFN-56_L7.0-W7.0-P0.4-EP.kicad_mod`、3D（.wrl/.step）。出力先フォルダがないと `[ERROR] Can't find the folder` になるので、事前に mkdir が要る |
| `JLC2KiCadLib C25804 -dir <dir>` | 5 秒。シンボル `0603WAF1002T5E`（`(property "LCSC" "C25804")` 付き）、フットプリント `R0603.kicad_mod`、STEP |
| `kicad-cli sym export svg`、`kicad-cli fp export svg`、`sym upgrade --force`、`fp upgrade --force` | すべて成功（KiCad 10 で読める） |

- 使用ホスト: easyeda.com（`/api/products/{lcsc_id}/components`、`/api/components/{uuid}`）、modules.easyeda.com（3D）、easyeda.com/analyzer/api/3dmodel（JLC2KiCadLib）。

#### 1.6.5 公式 API

- JLCPCB 公式 API（PCB / Stencil / 3D Printing / Components）は申請制で、「Not all applications will be approved」とされ、過去の注文・会社・事業状況で審査される。MCP の記載はない。（単一出典）
- LCSC 公式 API（Products、Orders、Shipment。キーワード検索は1ページ最大30件）も申請制で、認証は key/nonce/signature/timestamp。（単一出典）
- 個人の新規プロジェクトが短期間で取得できる保証はなく、公開データで足りる（推論）。

### 1.7 MCP サーバーの評価

#### 1.7.1 全体の状況

- KiCad 系の MCP は 2026-11 時点で少なくとも40件以上あるが、★100 超かつ継続保守されているのは mixelpixx/KiCAD-MCP-Server（★3,255）、oaslananka/kicad-mcp-pro（★206）、Seeed-Studio/kicad-mcp-server（★184）程度。（確認済）
- KiCad、JLCPCB、LCSC の公式 MCP は存在しない。EasyEDA は公式組織の easyeda-client-cli に MCP モードがあるが、デスクトップクライアントが必須。（確認済）
- 公式 MCP レジストリの検索は名前の部分一致のみで、説明文は検索対象にならない。そのためレジストリだけでは JLCPCB/LCSC 系を見落とす。（確認済）
- 秋月電子の MCP サーバーや公開 API は見つからない。（単一出典）
- Raspberry Pi Pico SDK / picotool 専用の MCP は見つからない。（確認済）
- KiCad の IPC API に依存する MCP（Konnect の基板ツール、daedalus、KiPilot、kicad-mcp-pro の Companion）はクラウドでは使えない（推論。ただし xvfb 上なら IPC API 自体は動く。1.5.4）。

#### 1.7.2 評価表

「動く場所」は、クラウドの作業環境で動くか、利用者のパソコン（実機や GUI のある環境）でしか動かないか。リポジトリの URL は 5 章にまとめた。

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

#### 1.7.3 MCP なしで足りる工程

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

### 1.8 Claude Code に MCP サーバーを接続する方法と、クラウドセッションでの制約

#### 1.8.1 設定の置き場所（単一出典: Claude Code 公式文書）

| スコープ | 置き場所 | 共有 | 優先順位 |
|---|---|---|---|
| Local（既定） | `~/.claude.json` | しない | 1 |
| Project | プロジェクト直下の `.mcp.json`（バージョン管理で共有） | する | 2 |
| User | `~/.claude.json` | しない | 3 |
| プラグイン同梱 | プラグイン直下の `.mcp.json` または `plugin.json` | — | 4 |
| claude.ai の connector | claude.ai の customize/connectors で追加 | — | 5 |

- スコープ間でフィールドはマージされない。
- コマンド: `claude mcp add [options] <name> -- <command> [args...]`（`--` 以降はサーバーにそのまま渡る）。HTTP は `claude mcp add --transport http <name> <url>`、`--header "Authorization: Bearer ..."`、`--scope project`。SSE は非推奨。ほかに `claude mcp add-json <name> '<json>'`、`claude mcp add-from-claude-desktop`。
- `.mcp.json` の形式は `{"mcpServers": {"name": {"type": "http", "url": "..."}}}`。`command`、`args`、`env`、`url`、`headers` で `${VAR}` / `${VAR:-default}` の展開が使える。リモートの `url`/`headers` では `ANTHROPIC_API_KEY`、`HTTPS_PROXY`、`NPM_TOKEN` などの資格情報変数は空として扱われる。
- 対話セッションでは project スコープのサーバーを使う前に承認を求められる（`claude mcp reset-project-choices` でリセット）。`claude -p`、Agent SDK、プロジェクトのスレッド外のクラウドセッションでは承認画面を出せないので、確認なしで読み込まれる。除外は `disabledMcpjsonServers` / `--strict-mcp-config`。
- 制限: `MCP_TIMEOUT`（起動タイムアウト）、出力は 10,000 トークン超で警告、既定上限 25,000（`MAX_MCP_OUTPUT_TOKENS`）、サーバーごとの `"timeout"`、`MCP_TOOL_TIMEOUT`。Tool search は既定で有効（`ENABLE_TOOL_SEARCH=false` で無効、`alwaysLoad`）。
- プラグイン同梱 MCP のツール名は `mcp__plugin_<plugin>_<server>__<tool>`、パスには `${CLAUDE_PLUGIN_ROOT}` を使う。
- connector はチーム・エンタープライズのプランでは管理者だけが追加できる。

#### 1.8.2 クラウドセッション（claude.ai/code）での制約（単一出典: 公式文書）

| 設定 | クラウドに持ち込まれるか |
|---|---|
| リポジトリにコミットした `.mcp.json` | 持ち込まれる（リポジトリが1つのセッション） |
| `claude mcp add` で local / user スコープに追加したサーバー | 持ち込まれない。`claude mcp add --scope project` で追加してファイルをコミットする |
| リポジトリの `.claude/settings.json` で宣言したプラグインとマーケットプレイス | 持ち込まれない |
| claude.ai で追加した connector | クラウドのホストが渡す |

- ネットワークのアクセスレベルは None / Limited / Full の3つ。新規環境は Limited + パッケージマネージャー許可。旧 Trusted は Limited+パッケージマネージャー許可、旧 Custom は Limited+許可ドメインとして開かれる。
- stdio のサーバーはクラウドの VM 内で起動し、その通信は環境の許可リストに従う。uvx/npx で PyPI/npm から取得するものは既定の許可リストで動く（推論）。
- HTTP のサーバー（pcbparts.dev など）は、Limited 環境では許可ドメインに追加が要る。Full なら不要。
- connector の通信は Anthropic のサーバーを経由するため、許可ドメインへの追加なしで動く。そのためリモート MCP を claude.ai の custom connector として登録すれば、許可リストを変えずに使える可能性が高い。ただし custom connector に任意の URL を登録できるかはプラン依存で未確認（推論）。
- 既定の許可リストには github.com、api.github.com、raw.githubusercontent.com、codeload.github.com、ghcr.io、registry-1.docker.io、gitlab.com、registry.gitlab.com、archive.ubuntu.com、*.ubuntu.com、ppa.launchpad.net、launchpad.net、pypi/npm/crates などが含まれる。pcbparts.dev、jlcsearch.tscircuit.com、wokwi.com、freerouting.app、jlcpcb.com、lcsc.com は含まれない（取得できた一覧の範囲内。一部欠落の可能性あり）。
- ProductOfAmerica の Claude Code プラグイン方式は、クラウドではリポジトリ設定経由で自動導入されないので、クラウドで使うなら `.mcp.json` に直接書く必要がある（推論）。
- USB 実機（Pico、デバッグプローブ、ロジックアナライザ、シリアル）はクラウドの VM には届かない。実機系の MCP は、利用者のパソコンで動く Claude Code（または Remote Control で自宅のパソコンのセッションを操作）が前提（推論）。

#### 1.8.3 `.mcp.json` の例（推論。動作未確認）

```json
{"mcpServers": {
  "pcbparts": {"type": "http", "url": "https://pcbparts.dev/mcp"},
  "kicad-review": {"command": "uvx", "args": ["kicad-mcp-pro==4.11.0"]}
}}
```

- kicad-mcp-pro の既定の起動引数とプロファイル指定方法は未確認。README にあるのは `uvx kicad-mcp-pro --transport streamable-http …` と `quickstart`。ProductOfAmerica の起動は `uvx --from mcp-server-kicad mcp-server-kicad`。
- kicad-mcp-pro は更新頻度が高いため、`==4.11.0` のように版を固定しないと再現性が崩れる（推論）。
- 例にある URL はコマンドの設定値であり、出典ではない。

### 1.9 ファームウェア開発環境、6502 用ツール、テスト用 ROM、エミュレータ

#### 1.9.1 Pico SDK・picotool・pioasm（確認済。API の公開日と git のタグ日で一致）

| 版 | 日付 | 主な内容 |
|---|---|---|
| pico-sdk 2.3.1 | 2026-09-04（published_at 2026-09-04T22:38:41Z） | RP2350 の同期処理が sleep せずに busy-wait していた問題などを修正 |
| pico-sdk 2.3.0 | 2026-07-03 | RP2350 の XIP キャッシュを `pico_use_xip_cache_as_ram()` で追加 SRAM として使える。hardware_psram |
| pico-sdk 2.2.0 | 2025-07-29 | RP2350-E10 の回避策。`picotool seal` で LOAD_MAP を付与 |
| pico-sdk 2.1.1 | 2025-02-19 | — |
| pico-sdk 2.1.0 | 2024-11-25 | 「RP2350 A0/A1 silicon are no longer supported」 |
| pico-sdk 2.0.0 | 8月8日（年は一覧の並びから 2024 と判断） | RP2350 対応と RISC-V のビルド（`rp2350-arm-s` / `rp2350-riscv`） |
| picotool 2.3.1 | 2026-09-05 | SDK 2.3.1 に合わせたバグ修正 |
| picotool 2.3.0 | 2026-07-03 | `bdev`、`uf2 combine` |
| picotool 2.2.0-a4 | 2025-08-14 | 「RP2350 A3 and A4 chip revision display」 |
| picotool 2.2.0 | 2025-07-29 | — |

- picotool は、未導入なら SDK の CMake が `GIT_TAG ${PICO_SDK_VERSION_STRING}` で FetchContent して自動でビルドする。SDK の `tools/CMakeLists.txt` は `set(picotool_VERSION_REQUIRED 2.3.0)`。`git ls-remote` で picotool の最新タグ 2.3.1 に到達できた。（確認済）
- pioasm は SDK ツリー内の `tools/pioasm` を ExternalProject_Add でビルドし、版は `-DPIOASM_VERSION_STRING=${PICO_SDK_VERSION_STRING}`。ネットからの取得はない。（確認済）
- apt には freerouting、kikit、picotool、pico-sdk のパッケージはない。（単一出典）

#### 1.9.2 RP2350 のステッピングと入力回路に関わる不具合（単一出典: RP2350 データシート build 01/10/2026）

| 項目 | 内容 |
|---|---|
| ステッピング（Table 7） | A0/A1「Internal development」、A2「Initial release」、A3「Internal development, samples, and limited production」、A4「Production version」 |
| RP2350-E9 | 「Increased leakage current on Bank 0 GPIO when pad input is enabled」。A2 のみ。入力が未定義の領域で約120µA を出してピンを約2.2V に保ち、内蔵プルダウンでは引き下げられない。「8.2 kΩ or less」の低インピーダンスで引けば回避でき、プルアップは機能する |
| E9 の修正 | A3 でパッド回路を変更して修正 |
| A4 | 「This stepping has no hardware changes.」（ブート ROM のみ変更: E18 修正、E24 緩和、E25 修正）。CHIP_ID.REVISION=0x3、ブート ROM 版バイト=0x4 |
| 刻印 | 「RP2350」+「A」（QFN-60）/「B」（QFN-80）+ パッケージ版「0」+ ステッピング「A2」「A3」「A4」 |
| 5V 耐性 | 「GPIOs are 5 V-tolerant (powered) and 3.3 V-failsafe (unpowered)」。FT ピンは「tolerate voltages up to 5.5 V, provided IOVDD is powered to 3.3 V」 |
| 市販品のステッピング | 秋月の Pico 2（SC1631、発売日 2024/09/18、￥990）と LCSC C42411118（RP2350A）のどちらにも記載がない（未確認） |

- 推論: 入力は外付けプルアップ（アクティブ Low）で設計すれば、A2/A3/A4 のどれでも問題ない。JAMMA の入力はもともとアクティブ Low とプルアップが慣例なので追加費用はない。実機のステッピングは `picotool info -a`、またはファームで CHIP_ID.REVISION とブート ROM 版バイトを読んで確認できる。
- 推論: FT ピンの 5V 耐性は IOVDD に通電中が条件なので、ファミコン側の 5V が先に立ち上がる場合に備え、5V バスへの直結には直列抵抗かバッファを入れる。

#### 1.9.3 実機なしでの Pico ファームの試験

| 方法 | できること | できないこと・制限 | 確度 |
|---|---|---|---|
| SDK の host platform（`PICO_PLATFORM=host`） | ハードに依存しないアプリのコードを PC でビルド・試験。pico-host-sdl で pico_multicore、タイマー、scanvideo を追加 | 「sufficient for programs that don't access hardware directly」（ハードを直接触るコードは不可） | 単一出典 |
| rp2040-pio-emulator | Python で単体試験、クロック数の計測、GPIO の時系列表示。JMP/IN/PUSH/PULL/SET/WAIT に対応 | OUT（EXEC 先）と MOV の一部が未実装、IRQ 命令は非対応、ステートマシン1個のみ、IN 用ピンセット非対応、`PULL IFEMPTY`/`PUSH IFFULL` は閾値を無視 | 単一出典 |
| rp2040js | src/peripherals に pio.ts、dma.ts、usb.ts、timer.ts など | フラッシュ書き込みに要る SSI が未実装。RP2350 の記述なし | 単一出典 |
| Wokwi（Pi Pico、RP2040） | GPIO、PIO（PIO Debugger あり）、UART、I2C/SPI（マスタのみ）、PWM、ADC、GDB | 「Only one core is simulated」。DMA は「Only for the PIO peripheral」。SSI は最小限 | 単一出典 |
| Wokwi（Pi Pico 2、RP2350） | PIO ブロック3つ、DMA 16ch 全部、PWM 12 スライス、TIMER0/1、POWMAN、SHA-256、ADC、GDB | Arm コア1つだけ（2つ目の Arm と Hazard3 RISC-V は模擬しない）。RP2350 固有の PIO 命令はない。HSTX は記載なし | 単一出典 |
| Wokwi CI | `wokwi/wokwi-ci-action@v1`、シークレット `WOKWI_CLI_TOKEN`（「starts with `wok_`」）、`expect_text` で合否判定。CLI は `--timeout`（既定30秒）、`--expect-text` | 無料枠は過去30日で50分、1セッション5分（Free と Hobby）。無料プランは公開プロジェクトのみ | 確認済 |
| Wokwi 料金 | Community €0、Hobby €5.6/月（fast build 100分）、Hobby+ €8.1/月、Pro €20/seat/月（「2000 monthly CI minutes」「For commercial projects」） | — | 単一出典 |

- 推論: どの方法でも、アナログ映像出力や、ファミコンの M2・PPU の /RD・/WR などの外部信号とのナノ秒単位の位相関係は検証できない。現実的な分担は、PIO の命令論理は rp2040-pio-emulator、コイン・タイマー・クレジットの状態機械は host platform、統合試験は実機とロジックアナライザ。

#### 1.9.4 6502 用の開発ツール

| ツール | 版・日付 | 内容 | 確度 |
|---|---|---|---|
| cc65（ca65/ld65/cl65） | 版番号 2.19（最終タグ V2.19 = 2020-11-20、master の version.c も `VER_MAJOR 2U` / `VER_MINOR 19U`）。Windows スナップショットは 2026-11-08。apt は 2.19-1 | 6502/65c02/65c816 のアセンブラ・リンカ・C コンパイラ。zlib ライセンス。`/usr/share/cc65/cfg/nes.cfg` と `nes.lib` 同梱 | 確認済 |
| asm6f | v1.6 (modifications v03) = 2025-01-27 | illegal opcode と NES 2.0 ヘッダに対応 | 単一出典 |
| NESASM CE | v3.6（日付不明） | NES 向けアセンブラ。Linux では `make all` | 単一出典 |
| llvm-mos-sdk | 版数未確認 | NES ターゲット `mos-nes-action53-clang`、`-cnrom-`、`-gtrom-`、`-mmc1-`、`-mmc3-`、`-nrom-`、`-unrom-`、`-unrom-512-` | 単一出典 |
| neslib（clbr 版） | 版不明、zlib | ca65 用の NES 関数ライブラリ（cc65 開発版向け） | 単一出典 |
| nesdoug | — | cc65 + neslib の NES 開発解説（MMC1/MMC3 の章あり） | 単一出典 |

cc65 の実測（確認済）:
- 自作 NROM-128 ROM（main.s 約60行 + nrom.cfg）。iNES ヘッダ `4E 45 53 1A 01 01 00 00…`（PRG 16KB×1、CHR 8KB×1、マッパ0）。リセット処理（SEI/CLD/$4017=$40/スタック/$2000,$2001=0/VBlank 2回待ち/RAM クリア/NMI 有効）と、$4016 をストローブして8回読むコントローラ読み取りを含み、結果を $0200 に書く。
- `ca65 -g main.s -o main.o && ld65 -C nrom.cfg -o test.nes main.o -m test.map --dbgfile test.dbg` で 24,592 B（=16+16384+8192）。ベクタは `$FFFA: 52 C0 00 C0 55 C0`（NMI=$C052、RESET=$C000、IRQ=$C055）。

マッパの選択（単一出典）:
- NROM（マッパ0）: PRG「16K or 32K」、CHR「8K」、ミラーリングははんだパッドで固定。ROM 2個だけでロジック不要。
- UxROM（マッパ2）: PRG 256K/4096K、CHR RAM 8K、「74HC161 binary counter used as a quad D latch」と 74HC32。オリジナル基板にはバスの衝突がある。
- 74HC32 は JLCPCB で Extended（C5632）。74HC161 は、JLCPCB API から全件取得した Basic（351件。74 系は 74HC14 と 74HC595 のみ）にも Preferred（1,235件。74 系は 74HC04/08/165/245 と SN74LVC4245A のみ）にも含まれないので、Basic では使えない（確認済）。Extended としての C 番号と在庫は未確認。

#### 1.9.5 スクリプトで動かせるエミュレータ

| エミュレータ | 自動試験の方法 | 確度 |
|---|---|---|
| FCEUX 2.6.5（apt） | `HOME=<tmp> xvfb-run -a /usr/games/fceux --no-config 1 --sound 0 --loadlua test.lua test.nes` が2秒で終了、rc=0。Lua で60フレーム目以降に `joypad.set(1,{A=true,start=true})`、`memory.readbyte(0x0200)` を記録して `emu.exit()`。結果は `frame 59: $0200=00` → `frame 61: $0200=90`（=A(bit7)+Start(bit4)）、NMI カウンタも毎フレーム増加。**ROM の起動・NMI・コントローラ読み取りを画面なしで自動検証できた** | 確認済 |
| FCEUX の公式オプション | `-lua`（「Loads a Lua script on startup」）。Lua に `memory.readbyte`、`emu.frameadvance`、`emu.exit`（「closes FCEUX」）、`emu.speedmode`（"normal","nothrottle","turbo","maximum"）、`emu.getscreenpixel`、`gui.savescreenshotas`、`joypad.set`。ヘッドレスや GUI 無効のオプションは記載なし。apt 版は Qt5/SDL2/OpenGL に依存する GUI アプリ | 確認済 |
| MesenCE | `--testRunner [lua script] [rom file]` で画面なし実行。スイッチは `timeout=`、`novideo`、`noaudio`、`noinput`。既定タイムアウト100秒、タイムアウト時の終了コードは -1。**終了コードは `emu.stop(code)` で返す**（ヘルプ文の `emu.exit` は誤記で、Lua API に `exit` は登録されていない）。Lua 関数: read/write/read16/readWord、addMemoryCallback、addEventCallback、getScreenBuffer、getPixel、takeScreenshot、setInput/getInput、createSavestate/loadSavestate、getState/setState、getCpuCycleCount、getMasterClock、reset、stop、log、getRomInfo。macOS/Linux 版は SDL2 を手動で入れる必要がある。2.2.0 では「11 more AccuracyCoin tests passing」 | 確認済（ソースで確認）／未確認（コンテナでの動作） |
| Mesen2（旧） | 最終リリース 2.1.1（2025-07-06）。開発は MesenCE（Community Edition）に移った | 確認済 |
| mednafen 1.29.0 / nestopia 1.52.0 | apt にあるが未試験 | 単一出典 |

- 推論: CI では MesenCE を `--testRunner test.lua game.nes timeout=30` で回し、フレーム終端のコールバックで RAM や画面バッファを検査して `emu.stop(0/1)` で終える。test runner は Avalonia UI を通らない経路なので、ディスプレイなしで動く可能性が高いが未実測。FCEUX は xvfb 下で実証済みで、当面の主力になる。

#### 1.9.6 テスト用 ROM

| ROM | 検証内容 | マッパ | 必要度 | 確度 |
|---|---|---|---|---|
| AccuracyCoin | CPU/PPU/APU などの pass/fail 147個 + DRAW 5個。「designed for an NTSC console with an RP2A03G CPU and RP2C02G PPU」。リビジョンが異なる機体では一部を自動でスキップ。成功コードで US NES と Famicom のコントローラの読み方の違いや、コンポジット PPU と RGB PPU を区別できる。結果は画面に PASS/FAIL とエラーコードで表示し、Start で全テストを実行。MIT | NROM（README） | 必須 | 単一出典 |
| instr_test-v5 rom_singles | 公式・非公式命令。結果を画面とビープ音（0=pass、1=fail、2以上=理由コード）で出し、$6000 にステータス（$80=実行中、$81=リセット要求）、$6004 以降にテキスト | NROM 32K+8K（01-basics.nes の実測） | 必須 | 確認済 |
| ppu_vbl_nmi rom_singles | VBL フラグと NMI のタイミング（「to one PPU clock」） | NROM（01-vbl_basics.nes の実測） | 必須 | 確認済 |
| apu_test rom_singles | CPU から見える APU の挙動 | NROM（1-len_ctr.nes の実測） | 必須 | 確認済 |
| cpu_timing_test6 | 命令タイミング | NROM 16K | 推奨 | 確認済 |
| oam_stress | $2003/$2004 | NROM 32K+8K | 推奨 | 確認済 |
| ppu_sprite_hit / sprite_overflow_tests | スプライト0ヒット、スプライトオーバーフロー | 未確認 | 推奨 | 単一出典 |
| cpu_interrupts_v2 / instr_timing | IRQ/NMI、命令タイミング | MMC1（80KB / 32KB、実測） | 任意（MMC1 対応カートが必要） | 確認済 |
| read_joy3 / allpads | コントローラ読み取り（read_joy3 は DMC DMA による読み取り破損を含む） | 未確認 | 推奨 | 単一出典 |
| full_nes_palette | 全パレットとエンファシスの表示 | 未確認 | 推奨（映像変換の色確認） | 単一出典 |
| 240p Test Suite（NES 版 240pee） | PLUGE、カラーバー各種、Monoscope、Convergence、Gray ramp、Overscan、Safe areas、CPU clock speed、Input test、Sound test、Audio sync test、MDFourier など28項目。最新 v0.23（2023-03-03）、GPL v2 以降 | UNROM（README「burn ... with an UNROM board」） | 必須（映像調整） | 確認済 |
| nestest | 「start at $C000」で起動し既知のログと比較するエミュレータ向け。実機で合否を表示するものではない | — | エミュレータ試験のみ | 単一出典 |

- **blargg のまとめ版 ROM（all_instrs.nes、official_only.nes、ppu_vbl_nmi.nes は MMC1・PRG 256KB、apu_test.nes は 128KB、cpu_interrupts.nes は 80KB、instr_timing.nes は 32KB）は MMC1（マッパ1）なので、NROM の自作カートでは走らない。** rom_singles は NROM 32K+8K で走る。（確認済）
- テスト ROM の多くはリンク切れで、christopherpow/nes-test-roms にアーカイブされている。（単一出典）

### 1.10 実機確認に必要な機材

#### 1.10.1 観測対象と必要な性能の根拠

- マスタークロックは「21.477272 MHz ± 40 Hz」、CPU は 21.47~ MHz ÷ 12 = 1.789773 MHz、PPU の1ドットはマスタークロック4つ分（5.369318MHz）。（確認済）
- 推論: CPU バス（周期559ns）の有効窓を見るだけなら 25〜50MS/s で足りる。M2 や PPU /RD とマスタークロック（周期46.6ns）の位相関係を見るには最低 100MS/s（1周期に約4.7サンプル）、余裕を見るなら 200MS/s が要る。CPU バス（A0–A15、D0–D7、M2、R/W の約26本）を全部同時に見るには 16ch では足りないので、データ8本+制御数本+アドレスの一部に絞るか、32ch 機を使う。
- 推論: オシロスコープは、21.48MHz の基本波と3次高調波（64MHz）を見るなら 100MHz 機で実用上十分。立ち上がり時間を正確に測る（例: tr=5ns なら 0.35/5ns = 70MHz 相当）ところまで求めるなら 200MHz 以上。根拠は「BW·tr ≅ 0.35」（ガウス応答なら0.34）の関係式。15kHz のアナログ RGB（画素 5.37MHz）と電源リップルの確認は 100MHz で足りる。

#### 1.10.2 ロジックアナライザ（sigrok 対応状況は sigrok wiki）

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

#### 1.10.3 その他の機材

| 機材 | 目的 | 型番・仕様 | 価格・入手先（2026-11-10、税込） | 必要度 | 確度 |
|---|---|---|---|---|---|
| オシロスコープ | クロック波形、電源、アナログ RGB/音声 | OWON SDS1102 2ch 100MHz / SDS1104 4ch 100MHz | 秋月 ￥39,000（g116900）/ ￥45,000（g116901） | 必須（どちらか1台） | 単一出典 |
| 低価格オシロ（参考） | — | OWON SDS1022 2ch 20MHz / Hantek 6022BE USB 20MHz/48Msps | 秋月 ￥35,000 / ￥12,720（g116926） | 帯域不足（推論） | 単一出典 |
| プローブ | — | 100MHz / 250MHz | 秋月 ￥2,000（g100240）/ ￥2,540（g117802） | 必須 | 単一出典 |
| フラッシュカート | 実機で任意の ROM を実行 | EverDrive N8 PRO Fami（60-pin、Cyclone IV、16MB = PRG 8MB + CHR 8MB、256K バッテリー RAM、開発用 USB ポート） | krikzz.com $159。国内販売店・在庫は未確認。互換機は「cannot guarantee compatibility」 | 必須（推奨路線） | 単一出典 |
| ROM ライター | 自作テストカートの書き込み | XGecu T48（USB 2.0HS、VPP 最大25V、VCC 1.8–6.5V、31000+ デバイス、「In Production」）。Linux では minipro が対応 | 国内価格未確認 | 自作カート路線の場合のみ必須 | 確認済 |
| スキャンコンバータ | 15kHz RGBS → HDMI | OSSC 1.8（€115.00〜€148.49、在庫あり）/ RetroTINK-4K CE（$475）/ 5X Pro（$325）/ 6X CE $230 / 2X Pro $139.99 / 4K Pro $750 | 各公式通販。国内は未確認 | 必須（どれか1台、または15kHz 対応 CRT） | 単一出典 |
| JAMMA 電源 | +5V/+12V/−5V | MEAN WELL RT-65A（5V 6A（0〜8A）、12V 2.8A、−5V 0.5A、66.1W。5V の調整範囲 4.75〜5.5V、リップル 80mVp-p）。RT-65B は3出力目が −12V | 国内価格未確認 | 必須（筐体なしで試験する場合） | 単一出典 |
| 電動はんだ吸取器 | DIP-40 の取り外し | HAKKO FR-301（350–500℃、98W、標準ノズル N61-08 φ1.0。ノズルは N61-01〜16、φ0.6〜1.6、長円3×1/4×1mm） | 秋月 ￥22,000（g114459、FR301-82。2026-06-16 に ￥23,500 から値下げ、通販23） | 必須（ドナー基板が多い場合） | 単一出典 |
| 手動はんだ吸取器 | 同上（低予算） | goot GS-108 / エンジニア SS-03 | 秋月 ￥1,150 / ￥2,580 | 代替 | 単一出典 |
| IC ソケット | CPU/PPU の差し替え | 丸ピン40P（在庫3491個）/ IC ソケット40P / ZIF 40P 600mil / ロープロ ZIF 40P（Aries） | 秋月 ￥110（g100034）/ ￥350/パック / ￥250（g111744）/ ￥250（g105436） | 必須（試作） | 単一出典 |
| 静電気対策用品 | NMOS 世代チップの保護（NMOS であることは推論） | リストストラップ 442B-01 / 09070、導電性スポンジ 200×100×5mm、帯電防止袋 | 秋月 ￥1,150（g114463）/ ￥2,980、￥170（g109709） | 必須 | 単一出典 |
| Pico 2 / Pico | 試作用マイコン | Raspberry Pi Pico 2（SC1631）/ Pico | 秋月 ￥990（g129604、通販在庫1462）/ ￥800（g116132） | 必須 | 単一出典 |

#### 1.10.4 DIP-40 の取り外し手順（HAKKO FR-301 取扱説明書、2019.04.01 版。単一出典）

1. 「除去する部品のリード線をノズルの穴に差し込んで加熱します。ランドではなく、リード線とはんだを加熱するように心がけてください。ノズルを直接ランドにあてるとランドが剥離する恐れがあります。」
2. 「... リード線をノズルに差し込んだままで、軽くゆっくりとリード線を動かしてください。リード線が簡単に動けばはんだがすべて溶けたと考えられます。」
3. 「トリガーをひいて溶かしたはんだを吸引します。」
4. 「失敗した時は、新しいはんだでもう一度はんだ付けしてからやり直します。」

- ファミコン本体から DIP-40 を外す専用の手順書は見つからず、汎用の取扱説明書で代用している。（単一出典）
- 静電気対策（TI SSYA010A §3.3）: 第一の原則「keep ICs and everything that comes in close proximity to them at ESD ground potential」。人体の接地（リストストラップか静電気対策靴）、作業面は静電気拡散性の材料で接地、絶縁物は作業場から除くかイオナイザで中和、保管はファラデーシールド容器。（単一出典）
- 推論: 40本のピンを1本ずつ吸い、手順2でリードが動くことを確かめる。抜いたチップはすぐ導電スポンジかシールド袋に入れる。

#### 1.10.5 試験台を組むときの注意（単一出典: OSSC wiki）

- OSSC の映像入力は75Ω 終端なので、アーケード基板を直結すると追加の抵抗が要る場合がある。
- 同期入力も75Ω 終端で、TTL レベルの同期信号を直結してはいけない。対策は「a 470 ohm series resistor on the console side」。
- 映像レベルが高い場合は Pre-ADC Gain を下げる。
- JAMMA の RGB の実際の電圧（Vpp）と、OSSC / RetroTINK の許容入力電圧の数値は未確認。

#### 1.10.6 テストカートの部品入手性

- 秋月で見つかったパラレル Flash は SST39VF040-70（4Mbit、2.7〜3.6V、TSOP32、￥150、g112066）だけ。5V 品（SST39SF0x0、27C256/512、28C256、62256）は見つからない。SRAM は M68AF127B 1Mb が ￥70（g101083）。（単一出典）
- LCSC（jlcsearch 経由）: SST39SF040-55-4I-NHE-T（PLCC-32、C632847、在庫12、$5.46@1個、Extended）、SST39SF010A-55-4C-NHE-T（PLCC-32、C632838、在庫22）、IS62C256AL-45ULI-TR（SOIC-28、C14323、在庫2548、Extended）。（単一出典。C14323 のクラスと在庫は JLCPCB API でも Extended・2,548 で確認済）
- 推論: 5V のパラレル ROM は入手が難しく、テスト用途なら EverDrive N8 PRO Fami を1台買う方が部品調達のリスクが低い。
- オープンハードのカート基板: ponchick/FC-DiscreteCart（ジャンパで NROM/CNROM/GNROM/BNROM/AMROM/ANROM/AOROM/UNROM/UOROM、DIP-28 か DIP-32 の ROM、KiCad、CERN-OHL-P-2.0）、Gumball2415/NES-Famicom-Cartridge-PCBs（`nrom-board` / `unrom-board`、TAPR OHL）、ClusterM/coolgirl-famicom-multicart（CPLD EPM1270T144、「designed for ordering from JLCPCB」、4層1.2mm、GPL-3.0）、ClusterM/famicom-dumper-writer（STM32F103ZET + EPM3064）、Keitark/fc-rom-vomitter（ESP32-S3 が Wi-Fi で受けた NROM イメージを CY62128 SRAM 2個に転送、6層、**README に「Do not insert an untested board into a Famicom」とあり実機検証は済んでいない**）。（単一出典）

### 1.11 利用者が準備すべきもの

#### 必須

| 項目 | 内容 | 理由 |
|---|---|---|
| クラウド環境での実行許可 | Pico SDK のビルド、Freerouting の実行、Fabrication Toolkit の実行を許可する（権限設定、または利用者のパソコンでの実行） | 今回はセッションの権限判定が「外部から取得したコードの実行」として拒否した |
| クラウド環境のネットワーク設定 | Limited 環境なら ppa.launchpadcontent.net、jlcsearch.tscircuit.com、pcbparts.dev、jlcpcb.com、wmsc.lcsc.com、easyeda.com、modules.easyeda.com、cdfer.github.io、release-assets.githubusercontent.com などの許可（どれが既定で通るかは一部未確認） | 1.3.3 |
| セットアップスクリプトの登録 | 1.3.2 の案（xvfb の追加を検討） | 毎回の導入の手間を省く |
| 利用者のパソコンで動く Claude Code | 実機（Pico、ロジックアナライザ、シリアル）を扱うため | USB 機器はクラウドに届かない |
| ドナーのファミコン | CPU（RP2A03）と PPU（RP2C02）の取り出し | 製品要求 |
| DIP-40 の取り外し道具 | HAKKO FR-301（￥22,000）または goot GS-108（￥1,150）/ エンジニア SS-03（￥2,580）、フラックス | 1.10.4 |
| 静電気対策用品 | リストストラップ（￥1,150）、導電性スポンジ（￥170）、帯電防止袋 | 1.10.4 |
| IC ソケット | ZIF 40P 600mil（￥250）または丸ピン40P（￥110） | 試作で CPU/PPU を差し替えるため |
| ロジックアナライザ | DSLogic Plus（$149）または Kingst LA2016（価格未確認） | 16ch・100MS/s 以上 |
| オシロスコープとプローブ | OWON SDS1102（￥39,000）+ プローブ（￥2,000 または ￥2,540） | 100MHz 級 |
| 実機で ROM を走らせる手段 | EverDrive N8 PRO Fami（$159）。または自作カート + XGecu T48 | テスト ROM と自作ゲームの実行 |
| 15kHz 映像の表示手段 | OSSC 1.8（€115.00〜）、RetroTINK のいずれか、または 15kHz 対応 CRT。同期線に 470Ω 直列の試験用ケーブル | 1.10.5 |
| JAMMA 電源とハーネス | MEAN WELL RT-65A（国内価格未確認）+ JAMMA 56ピン端子のハーネス（筐体がない場合） | 筐体なしの試験 |
| Raspberry Pi Pico 2 | 必要な枚数（￥990/枚） | 試作 |
| JLCPCB のアカウント | 発注用 | — |

#### 任意

| 項目 | 内容 |
|---|---|
| Wokwi のトークン（`WOKWI_CLI_TOKEN`） | Pico ファームのクラウド模擬。無料枠は過去30日で50分、1セッション5分。非公開プロジェクトは有料プラン |
| SWD デバッグプローブ | embedded-debugger-mcp や openocd で使う（Raspberry Pi Debug Probe での RP2350 対応は未確認） |
| claude.ai の custom connector 登録 | pcbparts-mcp を許可リストの変更なしで使う（登録可否はプラン依存で未確認） |
| JLCPCB / LCSC の公式 API の申請 | 審査制。公開データで足りる |
| Nexar / DigiKey / Mouser のキー | 本件は不要 |
| kicad-packages3d | 3D 描画（DL 280MB / 展開 3.29GB） |

## 2. 第1次調査からの訂正

第1次調査ノート（tooling_and_mcp.md、parts_and_manufacturing.md）の記述のうち、第2次調査（toolchain_smoke_test.md、mcp_landscape.md、firmware_test_and_bringup.md、parts_class_reverification.md）で訂正されたもの。

### 2.1 KiCad とその周辺

| 第1次調査の記述 | 訂正後 |
|---|---|
| IPC API（kipy）は起動中の KiCad GUI が必要で、ヘッドレスでは「不可(GUI要)」 | 公式のヘッドレスモードがないのは正しいが、**xvfb 上の pcbnew で kipy は実用的に動く**。起動ウィザード抑止の設定（design-block-lib-table を含む3つの lib-table と `do_not_show_again.update_check_prompt/data_collection_prompt=true`）が必須。表は「xvfb で可」に訂正 |
| `add-apt-repository ppa:kicad/kicad-10.0-releases` → `apt install kicad` | このコンテナではそのままでは `ModuleNotFoundError: No module named 'apt_pkg'` で失敗する。`python3.12 /usr/bin/add-apt-repository ...` が必要 |
| フル導入は数百MB〜GB級と推定 | 実測: `--no-install-recommends kicad kicad-symbols kicad-footprints` で DL 151MB、apt 表示 947MB（実測約0.84GB）。kicad-packages3d を加えると DL +280MB / +3.29GB |
| kiutils / kicad-skip は KiCad 10 書式での往復を要検証 | **どちらも KiCad 10 の基板を読めない**。回路図は kicad-skip が無損失、kiutils は属性が欠落する |
| （記載なし） | KiCad 10 の SWIG `pcbnew` は Python 3.12 拡張であり、このコンテナの既定 `python3`（3.13）では使ってはいけない |
| PPA の noble Release が HTTP 200（ppa.launchpadcontent.net） | 実測は Full ネットワークのセッションでのもの。既定の Limited 環境の許可リストには ppa.launchpad.net はあるが ppa.launchpadcontent.net は見当たらず、追加の許可が要る可能性がある（未確認） |
| eeschema（回路図）の IPC API は KiCad 10 に間に合わなかった（開発者の 2026-01 の発言） | GitLab #24803 は「The schematic editor (`API_HANDLER_SCH`, KiCad 10) does not register `RevertDocument`」、#25666 は「The schematic editor in 10.0.x doesn't have [variant commands]」と書いており、KiCad 10.0.x に回路図エディタの API ハンドラ自体は存在する模様。範囲は未確認（3章） |

### 2.2 部品データ

| 第1次調査の記述 | 訂正後 |
|---|---|
| CDFER: SQLite 約1GB / CSV 約3MB（README の記述） | 実測 SQLite 419,360,768 B / CSV 1,252,216 B（2026-11-10 版） |
| jlcsearch: `curl -I` が 405（GET 可否は未確認） | **GET は 200**（405 は HEAD に対応していないだけ） |
| Basic 判定は CDFER CSV で機械的に照合可能（Basic 判定は CDFER の library_type による） | クラス自体は JLCPCB API と一致したが、CDFER の Preferred は 1,226 件で JLCPCB API の 1,235 件と一致せず、jlcparts 系は 21.47727MHz 水晶 C5289705 などを収載し漏らす。jlcsearch・jlcparts・CDFER は同じ系統で独立した裏取りにならない。最終判定は JLCPCB API で行う |
| Preferred Extended = 1226 件 | JLCPCB API では 1,235 件（jlcparts は 989 件） |
| 「Preferred Extended」という用語 | 現行の jlcpcb.com の画面ではフィルタ名「Promotional Extended」、部品のバッジは「Extended」とだけ表示される |

### 2.3 MCP

| 第1次調査の記述 | 訂正後 |
|---|---|
| kicad-mcp-pro: README 上 v4.11.0、レジストリ上は 2.1.0=2026-04-15 で不整合 | 不整合ではない。レジストリは全版を返し、2.1.0 は最古の項目（`isLatest=false`）。最新は 4.11.0（2026-11-10） |
| JLCPCB/LCSC 専用の独立 MCP はレジストリ検索で0件 | 公式レジストリの検索が名前一致のみのため。実際には Averyy/pcbparts-mcp（★144、ホスト型）、Eyalm321/jlcpcb-mcp、nvsofts/jlcpcb-parts-mcp（停滞）、hulryung/jlcpcb-skill-mcp、zhr1008/component-sourcing-mcp などが存在する |
| mixelpixx は新開発を KiCad 10 向け Rust 製 Konnect（AGPL）へ移行 | 2026-11 時点で Konnect 自体がアーカイブされ、開発は Orchis.ai LLC の商用・非公開「Konnect-EDA」へ移った。AGPL 版はフォーク（dylbertram/konnect-maintained）が継続 |
| mixelpixx: GUI 要否は記載なし（★約3.3k） | README に「Automatically uses IPC when available, falls back to SWIG」と明記。版は v2.8.3、ツール数 251（別の節では 244）、MIT |
| Freerouting: ライセンス記載はページ上で未確認。MCP `autoroute_board` を「v2.5.0 で追加」と「v2.3.0 以降」の両方で記述 | GPL-3.0（npm `@freerouting/freerouting-mcp-server` は GPL-3.0-only）。npm ブリッジの初版は 2026-06-16、最新 2.5.0（2026-10-05）。第1次調査の2つの記述はどちらも一部正しく、リリースページによれば MCP サーバー自体は v2.3.0 で入り、`autoroute_board`（1回で配線を済ませる複合ツール）は v2.5.0 で追加された（本検証で確認。第2次調査では未確認とされていた） |
| PowerDragonfire/platformio.mcp（0.1.0） | PyPI の最新は 0.6.2（2026-11-10） |
| EasyEDA Pro 系は GUI 必須→クラウド不可（推定） | 公式組織の easyeda-client-cli が「requires the desktop client of EasyEDA Pro」と明記し、推定が裏付けられた |
| Smithery/Glama/PulseMCP/mcp.so は未調査 | Glama、PulseMCP、mcp.so は調査済み（1.7.1）。Smithery は検索画面が取得できず網羅的な検索は未実施 |

### 2.4 ファームウェアとテスト

| 第1次調査の記述 | 訂正後 |
|---|---|
| Pico SDK 2.3.1（表示は「04 Sep」、年は2026年と推定） | 推定は正しかった。published_at 2026-09-04T22:38:41Z、タグのコミット日も 2026-09-04。picotool は SDK と同じタグ（2.3.1、2026-09-05）を自動取得する |
| pioasm は Pico SDK に同梱（ビルド時に取得） | ネットからの「取得」ではなく、SDK ツリー内の `tools/pioasm` のソースをビルドする。ネットから取得されるのは picotool |
| rp2040js: 指定 URL は404、正しい所在・PIO 対応状況は未確認 | 所在は wokwi/rp2040js（MIT、npm 1.4.1 = 2026-10-18、★536）。pio.ts / dma.ts がある。PIO の精度は未確認 |
| Wokwi CLI: RP2040/RP2350/PIO 対応、API トークン要否は未確認 | トークンは必須（`WOKWI_CLI_TOKEN`、「wok_」で始まる）。RP2040/RP2350 とも PIO を模擬するが、コア1つのみ、RP2350 固有の PIO 命令はなく、RP2040 の DMA は PIO 用のみ |
| MesenCE: ヘッドレス test runner / Lua の詳細は README から確認できず | `--testRunner [lua] [rom]` があり、`timeout=` の既定は100秒。終了コードは `emu.stop(code)` で返す（ヘルプ文の `emu.exit` は誤記）。Mesen 2.2.0（2026-06-04）/ 2.2.1（2026-06-05）をリリース済み |
| cc65: 最新タグ日付は未取得 | 最終タグは V2.19 = 2020-11-20、version.c も 2.19。Windows スナップショットは 2026-11-08 |
| apt 版 fceux 2.6.5（ヘッドレス実行可否は未確認） | 上流の最新は 2.7.0（2026-10-14）。公式の起動オプションは `-lua` でヘッドレスの記載はないが、xvfb 下で Lua による自動検証が動いた |
| NES テスト ROM 一覧（nestest、instr_test-v5 …） | blargg のまとめ版 ROM（all_instrs、ppu_vbl_nmi、apu_test、cpu_interrupts、instr_timing）は MMC1 なので NROM のテストカートでは走らない。rom_singles は NROM 32K+8K。nestest はエミュレータ向けで実機で合否を表示しない |
| Freerouting は v2.2.0 以降 Java 25 必須 | v2.5.0 の jar のクラスファイルが major 69（Java 25）であることを実際に確認。コンテナの既定は Java 21 なので jar は使えず、ネイティブ CLI（20MB）か apt の openjdk-25-jre-headless（25.0.5）が要る |
| Wokwi: 無料枠は30日で50分・1セッション5分 | 正しい（CI 用の無料枠）。Pro は €20/seat/月で CI 2000分。無料プランは公開プロジェクトのみ |

### 2.5 実機確認機材

| 第1次調査の記述 | 訂正後 |
|---|---|
| §6 全体「出典なし・全て未確認」 | 出典付きの内容に置き換えた（1.10） |
| テストカート: EPROM/フラッシュ書き込み器（例: TL866 系） | TL866A/CS は2018年2月に出荷を停止しており、市場品は偽物だとメーカーが告知している。TL866II Plus の状態は「T48 Replacement」。新規に買うなら T48。Linux では minipro が T48 に対応 |
| ロジアナ: Saleae 互換や sigrok 対応を想定 | 「Saleae 互換」（fx2lafw 系）は最大24MHz で本用途に足りない。Saleae 純正の Logic 8 も sigrok 非対応（planned）で、8ch 使用時は25MS/s。要件を満たす sigrok 対応機は DSLogic Plus（旧版ハード）や Kingst LA2016/LA5016 など |
| ロジアナ: 100MS/s 以上、できれば 200〜500MS/s・帯域100MHz 以上（24ch 級） | 最低 100MS/s・16ch 以上という結論は維持（推論）。16ch では CPU バス全体を同時に見られないので、信号を絞るか 32ch 機を使う |
| オシロ: 200MHz 帯域以上を推奨 | 厳しめだが誤りではない。21.48MHz と3次高調波を見るなら 100MHz 機で実用上十分（推論） |

## 3. 未確認事項と実機で確かめるべきこと

### 3.1 このクラウド環境（または利用者のパソコン）で確かめるべきこと

1. Pico（RP2040）/ Pico 2（RP2350）の cmake ビルド、UF2 の生成、PIO ヘッダの生成、picotool の自動ビルド（実行の許可が必要）。
2. `PICO_PLATFORM=host` でのコイン・タイマー・入力形式の論理の単体試験。
3. Freerouting のネイティブ CLI による自動配線 → SES の取り込み（SWIG の `ImportSpecctraSES`）→ DRC。
4. Fabrication Toolkit の CLI 実行と、KiBot の出力との比較。
5. JLCPCB 形式の部品配置表（CPL）の回転補正が正しいかどうか（KiBot / Fabrication Toolkit の機能の詳細は未確認）。JLCPCB の発注画面のプレビューで確かめる必要がある（推論）。
6. MesenCE の Linux ビルドで `--testRunner` がディスプレイなしで動くか。2.2.1 より新しいリリースの有無。Lua の `eventType` / `memType` の値一覧。
7. セットアップスクリプト案の通し実行（新しい環境で）。xvfb が元から入っているか。`pip install --no-compile kibot lxml` の一括形。`$HOME/.config/kicad` 直下での設定。
8. Limited 環境で必要な許可ホストの確定（ppa.launchpadcontent.net、api.launchpad.net、easyeda.com 系、cdfer.github.io、release-assets.githubusercontent.com、Wokwi のホスト名）。
9. kicad-mcp-pro の既定の起動引数とプロファイル指定方法。pcbparts-mcp の運営継続性と利用規約、2系統の版表記（0.8.24 と 3.4.3）のどちらが製品版か。
10. jlcsearch の在庫値の扱い（下記 3.3）と `resistance=` パラメータの書式。
11. JLCPCB 用の設計ルール（.kicad_dru）の数値。最小線幅/間隔を約0.127mm（5mil）、ビア径0.25mm/ドリル0.15mm とする資料と、3.5mil（0.09mm）とする資料があり不一致。JLCPCB 公式の能力表の本文は未取得。
12. kicad-packages3d を入れた場合の render 結果と所要時間。
13. Wokwi の PIO サイクル精度、Wokwi CLI v0.29.1 のリリース年、Wokwi MCP の具体的なツール名。
14. rp2040js の PIO/DMA の精度と RP2350 対応予定。
15. probe-rs（embedded-debugger-mcp の基盤）が Raspberry Pi Debug Probe（CMSIS-DAP）で RP2040/RP2350 に対応するか。
16. claude.ai の custom connector に任意の URL を登録できるプラン。
17. ppu_sprite_hit / sprite_overflow / read_joy3 / allpads / 240pee のマッパ（240pee は README では UNROM）。
18. 74HC161 の JLCPCB での C 番号と在庫（UxROM のテストカートを作る場合）。Basic・Preferred のどちらにもないことは確認済み（1.9.4）。

### 3.2 実機で確かめるべきこと

1. 購入した Pico 2 / RP2350A のステッピング（A2/A3/A4）。`picotool info -a` またはファームで CHIP_ID.REVISION とブート ROM 版バイトを読む。
2. RP2350 固有の PIO 命令を使う部分の動作（どのシミュレータも未対応）。
3. Pico の PIO がファミコンの M2、PPU の /RD・/WR などに正しく同期するか（ロジックアナライザで位相を確認）。
4. 複数の Pico を使う場合の協調動作（Wokwi は1コアしか模擬しない）。
5. AccuracyCoin（NROM）で CPU/PPU/APU をまとめて判定し、失敗項目を blargg の rom_singles で詳しく調べる。
6. 240p Test Suite で映像変換回路とスキャンコンバータを調整する。full_nes_palette で色を確認する。
7. allpads / read_joy3 で、JAMMA 入力からコントローラ入力への変換を確認する（タイマー方式、デフォルト形式、特殊形式の3つ）。
8. JAMMA の RGB の実際の電圧（Vpp）と、OSSC / RetroTINK の許容入力。同期線に 470Ω 直列が要るか。
9. RP2A03/RP2C02 が NMOS であることの一次資料は未取得（静電気対策は NMOS 前提で行う）。
10. USB Type-C 端子からのファームウェア更新と、更新失敗時の書き込みモードへの再進入。

### 3.3 第2次調査どうしの食い違い

| 論点 | 食い違いの内容 | より強い証拠と扱い |
|---|---|---|
| 回路図エディタの IPC API | toolchain_smoke_test.md は「回路図（eeschema）の IPC API は無い（devlist 情報と整合）」と書くが、これは推論で、実際には試していない。mcp_landscape.md は GitLab の課題（2026-08〜09）を引いて、KiCad 10.0.x に `API_HANDLER_SCH` が存在する模様とする | GitLab の課題の方が新しく、コード上の名前を挙げていて具体的なので、「ハンドラは存在するが、使える命令の範囲は未確認」とするのが妥当。本プロジェクトは回路図をファイル直接編集で扱うので、設計上の影響は小さい（推論） |
| jlcsearch の在庫値 | parts_class_reverification.md は `components/list.json` の `stock` は「ほとんど null」とする。toolchain_smoke_test.md は `/api/search` で RP2040 の stock 86,210 を、mcp_landscape.md は `list.json` で C5625 の在庫 52,801 を得ている | 前者は全 C 番号を照会した結果で母数が大きい。後者は個別の照会で、値が入る部品もある（両立しうる）。いずれにせよ在庫と価格は JLCPCB API を正とする |
| RP2350A（C42411118）の在庫と価格 | firmware_test_and_bringup.md は LCSC 在庫3080、$1.18@1個（jlcsearch API 経由）。parts_class_reverification.md は JLCPCB 在庫 6,268・$1.2943、LCSC 在庫 5,699・$1.3065（ともに一次 API）。CDFER は 6849 | 取得時刻と経路が異なる。一次 API を直接引いた parts_class_reverification.md の値を採る |
| Freerouting の Java 版 | mixelpixx の README は Freerouting 統合に「Java 21+」と書くが、Freerouting 2.5.0 の jar は Java 25 のクラスファイル（実測） | jar の実測の方が強い。2.5.0 を使うならネイティブ CLI か Java 25 が要る。mixelpixx が古い Freerouting を使う前提かは未確認 |
| mixelpixx のツール数 | README 内で 251 と 244 の両方 | README の自己矛盾。どちらとも決められない |
| datasheet-lens の版 | PyPI 0.6.1、README は「version 0.4」 | PyPI の値を採る（README の更新漏れと推定） |

## 4. ユーザー要求への影響

以下、事実の部分と推論の部分を分けて書く。「推論」と明記したものは筆者の判断で、出典はない。

### 4.1 部品は JLCPCB の Basic Parts のみ、LCSC で在庫豊富、手はんだ部品は秋月（要求1章）

- 事実: Basic は 351 件しかなく、クラスの判定と在庫は JLCPCB API が一次データ。jlcsearch・CDFER・jlcparts は同じ系統で、収載漏れや古い件数がある。pcbparts-mcp は `library_type="basic"` で絞り込めるが第三者の無料サービス。秋月には API も MCP もない。
- 選択肢:
  - A. JLCPCB API を BOM 照合の一次とし、jlcsearch / pcbparts-mcp は候補探しに使う。利点は正確さ。欠点は非公開 API で仕様変更の恐れがあること（推論）。
  - B. CDFER の CSV だけで照合する。利点はオフラインで簡単。欠点は Preferred 件数の不一致と収載漏れ。
- 推奨（推論）: A。KiBot で出した BOM の LCSC 番号を、スクリプトで JLCPCB API に照会して Basic/Preferred/Extended と在庫を一覧にし、人が確認する。秋月の部品は人がウェブで在庫を確認する手順を残す（自動化の手段がない）。Limited 環境では jlcpcb.com と pcbparts.dev の許可が要る。

### 4.2 全部を基板実装メーカーに実装してもらう（要求2章）

- 事実: kicad-cli と KiBot（`import: - file: JLCPCB`）で、JLCPCB 用の Gerber zip、BOM、CPL がクラウドで出力できた。回路図は KiCad 10 正規形式にしてから KiBot に渡す必要がある。Fabrication Toolkit は未実行。
- 推奨（推論）: 製造データの出力は KiBot に一本化する。CPL の回転補正は未確認なので、初回発注では JLCPCB のプレビューで全部品の向きを人が確認する。

### 4.3 CPU・PPU を実チップか Raspberry Pi かで選べる、ソケット実装（要求2章）

- 事実: AccuracyCoin は RP2A03G / RP2C02G の実機向けで、US NES と Famicom の違いや RGB PPU も区別できる。DIP-40 の取り外しには FR-301 などの吸取器と静電気対策が要る。ZIF 40P 600mil は秋月で ￥250。
- 推論: 同じテスト ROM 群（AccuracyCoin、rom_singles、240p Test Suite）を、実チップ構成とエミュレーション構成の両方で走らせれば、2つの構成の差を同じ物差しで比べられる。エミュレーション側の合格基準は AccuracyCoin の通過数で決めるのが分かりやすい。
- 推奨（推論）: 試作では ZIF ソケットを使い、取り外したチップはすぐ導電スポンジに保管する。テスト ROM を走らせる手段は、まず EverDrive N8 PRO Fami（$159）を1台用意する（5V のパラレル ROM は秋月にも LCSC にもほとんどなく、自作カートは部品調達のリスクが高いため）。

### 4.4 タイマー方式・通常方式と、デフォルト形式・特殊形式（要求3章）

- 要求の現行版（要求3章）: タイマー方式は市販ソフト用で、コインを入れると一定時間だけ操作を受け付ける。コインはゲームに渡さず時間の加算だけに使い、2P スタートボタンを I コンの SELECT に割り当てる。通常方式は新規開発ゲーム用で、入力形式を設定で選ぶ。デフォルト形式はコイン → そのパッドの SELECT、スタート → START。特殊形式はボタン3（C）→ SELECT、ボタン4（D）→ START、スタート → 左右同時、コイン → 上下同時。時間切れ後の扱いと残り時間の表示方法は未定。
- 事実: FCEUX の Lua で `joypad.set` により入力を与え、`memory.readbyte` で結果を読む自動試験が画面なしで動いた。MesenCE は `setInput` と `emu.stop(code)` で同様のことができる（未実測）。Pico SDK の host platform はハードに依存しない論理の単体試験に使える（未実測）。
- 推論:
  - コインのパルス整形、連続投入の待ち行列、タイマーの加算・時間切れ、3つの入力割り当て（タイマー方式、デフォルト形式、特殊形式）は、ハードに依存しない状態機械として書き、host platform で単体試験するのが最も確実である。
  - 特殊形式は「左右同時」「上下同時」というレバーでは作れない入力を使う。エミュレータがこの組み合わせをそのまま通すかは確かめていない（未確認。エミュレータによっては同時押しを抑制する設定がある可能性）。新規開発ゲーム側の試験では、この点をまず確かめる。
  - 特殊形式では、コインのパルス中は上下が、スタートを押している間は左右が読めなくなる。ゲーム側がその軸の入力を無視するかどうかも、Lua の自動試験の項目に入れる。タイマー方式では、コインが SELECT などとしてゲームに漏れていないこと、時間切れで入力が止まることを試験する。
  - 実機では allpads / read_joy3 を使い、JAMMA の各ピンを押したときにどのビットが立つかを、3つの方式・形式すべてで確認する。
- 推奨（推論）: 「状態機械は host 試験、ゲーム側は FCEUX（当面）と MesenCE（導入後）の Lua 試験、最終は実機の allpads」の3段で検証する。

### 4.5 切り替えはソフトウェアで行う（要求4章）

- 要求の現行版（要求4章）: 方式（タイマー/通常）と形式（デフォルト/特殊）は物理 DIP スイッチではなくソフトウェアで切り替える。要求ノートの整理では、設定値はファームウェアの不揮発メモリに保存し、店舗の担当者はテストスイッチ（JAMMA ピン15）の設定画面か USB で変更する。市販ソフトは基板に指示を出せないので、市販ソフトを動かすときは担当者がタイマー方式に設定する（これらの実現方法は推論）。
- 事実: 新規開発カートリッジからの切り替えは、$4016 への書き込み（OUT1・OUT2）と、$4016 の D1・$4017 の D1〜D4（拡張端子用の読み出しビット）を使う独自の通信手順として要求ノートで構想されている（未設計）。MesenCE の Lua には addMemoryCallback がある。
- 推論: エミュレータは基板側のファームウェア（Pico）を模擬しないので、通信手順の試験は二つに分ける。ゲーム側は MesenCE の addMemoryCallback などで $4016 への書き込み列を記録して期待値と比べる。基板側は host platform で、書き込み列を入力として与えて設定値の変化を確かめる。両者を結ぶ試験は実機とロジックアナライザでしかできない。
- 推奨（推論）: 通信手順は、ゲーム側と基板側で同じ試験データ（書き込み列と期待される応答）を共有する形で設計し、両側の単体試験に使う。

### 4.6 Raspberry Pi は何枚使ってもよい（要求5章）

- 事実: Wokwi はコア1つしか模擬せず、RP2350 固有の PIO 命令もない。rp2040js は RP2040 のみで RP2350 の記述がない。複数枚の協調を模擬できるツールは見つかっていない。ロジックアナライザは 16ch では CPU バス全体を同時に見られない。
- 推論: マイコンを増やすほど、シミュレーションでは検証できない部分（ボード間の通信と同期）が増える。各ボードの役割ごとの論理は host 試験で固め、ボード間の通信は実機で確かめる。ボード間の信号も観測する必要があるので、ロジックアナライザのチャンネル数は 16ch で足りない場面が出る。
- 推奨（推論）: 最初は DSLogic Plus（$149、16ch）で始め、ボード間通信と CPU バスを同時に見る必要が出たら 32ch 機を追加する。ボード間の通信にはデバッグ用の試験点を基板に設けておく。

### 4.7 将来の CPU・PPU・メモリの更新（要求5章）

- 事実: KiCad は 10 の保守版が出続けており、SWIG は KiCad 11 で削除見込み。kicad-mcp-pro は約5か月で PyPI 63 リリースと更新が激しく、ProductOfAmerica は保守モード、Konnect はアーカイブ済み。Pico SDK 2.3.0 で XIP キャッシュを SRAM として使える機能が追加された。
- 推論: 何年も後に基板を改版することを考えると、MCP やファイル操作ライブラリへの依存を深くせず、KiCad 本体（kicad-cli）と公式 SDK を中心に据え、ツールの版をセットアップスクリプトで固定しておくのが安全である。SWIG pcbnew で書いた自作スクリプト（net2pcb.py など）は KiCad 11 で動かなくなる見込みなので、KiCad 10 に版を固定するか、11 で IPC API のヘッドレスモードが実装されたら移植する。
- 推奨（推論）: KiCad 10.0.x に固定し、セットアップスクリプトと設計ファイルを一緒にリポジトリで管理する。MCP はレビュー補助（版固定）と部品検索に限る。

### 4.8 USB Type-C によるファームウェア更新（要求6章）

- 事実: picotool 2.3.1 が UF2 の書き込みと情報表示を行い、2.3.0 で `bdev` と `uf2 combine` が加わった（機能の詳細は未確認）。Pico SDK と picotool のビルドはこの環境では未確認。USB の実機（Pico、シリアル）はクラウドに届かない。
- 事実（要求6章の整理）: Raspberry Pi Pico 2 の USB 端子は Micro-B で、USB の信号線は40本の端子列に出ていない（裏面のテストパッドのみ）。基板用の16ピン Type-C 端子 C393939 は JLCPCB 在庫 340,763 と豊富だが Extended で、USB-C 端子は Basic・Preferred に1つもない。RP2350 は USB からの書き込み機能を書き換えられない領域に持つので、更新に失敗しても書き込みモードに入り直せる。
- 推論: 複数のマイコンを1つの Type-C 端子から更新する方式（端子につながる1枚が他を書き換える、または USB ハブ IC）は、どちらもシミュレータでは検証できず、実機で確かめるしかない。更新の試験には、利用者のパソコン側で picotool と serial-mcp（または `screen`/`pyserial`）を使う。
- 推奨（推論）: 最初の試作で、Type-C 端子から全マイコンを更新し、わざと更新を途中で止めて書き込みモードから復旧する試験を必ず行う。そのために利用者のパソコンに Claude Code と picotool を用意する。

### 4.9 安価で実際に作れる基板（要求1章）

- 事実: 必要なソフトはすべて無料で入手できる（Wokwi の有料プランなどを除く）。実機確認の機材は、ロジックアナライザ $149、オシロ ￥39,000 + プローブ、フラッシュカート $159、スキャンコンバータ €115.00〜、はんだ吸取器 ￥1,150〜￥22,000、静電気対策 ￥1,320 程度（リストストラップ ￥1,150 + 導電性スポンジ ￥170）、ZIF ソケット ￥250 など。JAMMA 電源の国内価格は未確認。
- 推論: 機材費は通貨が混在するため正確な合計は出せないが、上記の最小構成で円建て部分（オシロ、プローブ1本、FR-301、静電気対策、ZIF ソケット1個 = ￥39,000 + ￥2,000 + ￥22,000 + ￥1,150 + ￥170 + ￥250）だけで ￥64,570 になり、これにドル・ユーロ建ての3品と JAMMA 電源が加わる。基板1枚の単価を下げる要求とは別に、開発時の一度きりの投資として利用者に了承を得る必要がある。

## 5. 出典一覧

### 1. 確定事実

#### 1.2〜1.5 KiCad とそのツール
- KiCad 公式ブログ（10.0.x 保守リリースの日付）: https://www.kicad.org/blog/
- KiCad 10.0.0 リリース記事: https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/
- KiCad 10.0 CLI 文書: https://docs.kicad.org/10.0/en/cli/cli.html
- KiCad IPC API 文書: https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/
- KiCad 開発者メーリングリスト（SWIG・ヘッドレス・eeschema IPC の発言）: https://groups.google.com/a/kicad.org/g/devlist/c/3e8OU0FiEHc
- KiCad フォーラム（10.99 で同梱 Python 削除の報告）: https://forum.kicad.info/t/kicad-10-99-win-missing-python-exe/71638
- kicad-python（kipy）GitLab: https://gitlab.com/kicad/code/kicad-python
- kicad-python PyPI: https://pypi.org/pypi/kicad-python/json
- KiCad 10 PPA の Release ファイル: https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu/dists/noble/Release
- Docker Hub kicad/kicad のタグ: https://registry.hub.docker.com/v2/repositories/kicad/kicad/tags
- KiCad 起動ウィザードのソース（10.0 ブランチ）: https://gitlab.com/kicad/code/kicad/-/tree/10.0/common/startwizard
- KiCad GitLab #25413（kicad-cli DRC のクラッシュ修正）: https://gitlab.com/kicad/code/kicad/-/work_items/25413
- 各 Python ツールの版（PyPI JSON API の書式）: https://pypi.org/pypi/<name>/json
- KiBot: https://github.com/INTI-CMNB/KiBot
- atopile: https://github.com/atopile/atopile
- Freerouting リリース: https://github.com/freerouting/freerouting/releases
- Freerouting README（CLI 書式）: https://raw.githubusercontent.com/freerouting/freerouting/master/README.md
- Freerouting v2.5.0 のアセット一覧: https://github.com/freerouting/freerouting/releases/expanded_assets/v2.5.0
- Fabrication Toolkit: https://github.com/bennymeg/Fabrication-Toolkit
- kicad-jlcpcb-tools: https://github.com/Bouni/kicad-jlcpcb-tools
- easyeda2kicad: https://github.com/uPesy/easyeda2kicad.py
- JLC2KiCadLib PyPI: https://pypi.org/pypi/JLC2KiCadLib/json
- JLCPCB 用設計ルール（コミュニティ版）: https://github.com/labtroll/KiCad-DesignRules
- JLCPCB 用設計ルール（コミュニティ版）: https://github.com/Cimos/KiCad-CustomDesignRules
- JLCPCB の KiCad 設計記事: https://api.jlcpcb.com/blog/optimizing-kicad-designs-for-jlcpcb-fabrication
- JLCPCB 製造能力表（本文未取得）: https://jlcpcb.com/capabilities/pcb-capabilities
- その他の実測（kicad-cli、SWIG pcbnew、kipy、各ライブラリの往復試験、KiBot、apt の版、セットアップ手順）: toolchain_smoke_test.md のコンテナ実測（URL なし）

#### 1.6 部品データ
- JLCPCB 部品検索 API: https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- JLCPCB 部品検索画面: https://jlcpcb.com/parts/componentSearch?searchTxt=74HC
- JLCPCB partdetail C5605: https://jlcpcb.com/partdetail/Nexperia-74HC14D653/C5605
- JLCPCB partdetail C5590: https://jlcpcb.com/partdetail/Nexperia-74HC04D653/C5590
- LCSC 商品データ API: https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=Cxxxx
- jlcsearch（リポジトリ）: https://github.com/tscircuit/jlcsearch
- jlcsearch（C5605 の照会例）: https://jlcsearch.tscircuit.com/components/list.json?search=C5605
- jlcsearch（74HC245 の照会例）: https://jlcsearch.tscircuit.com/components/list.json?search=74HC245&limit=20
- jlcparts のデータ: https://yaqwsx.github.io/jlcparts/data/cache.zip
- jlcparts リポジトリ: https://github.com/yaqwsx/jlcparts
- CDFER jlcpcb-parts-database: https://github.com/CDFER/jlcpcb-parts-database
- CDFER Basic/Preferred CSV: https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv
- pcbparts-mcp（ホスト）: https://pcbparts.dev/mcp
- JLCPCB 公式 API: https://api.jlcpcb.com/
- JLCPCB 公式 API の案内: https://jlcpcb.com/help/article/jlcpcb-online-api-available-now
- LCSC OpenAPI: https://www.lcsc.com/docs/openapi/index.html
- LCSC API の申請案内: https://www.lcsc.com/agent
- Claude Code ツールリファレンス（Read ツールと PDF）: https://code.claude.com/docs/en/tools-reference

#### 1.7 MCP サーバー
- 公式 MCP レジストリ（KiCad 検索）: https://registry.modelcontextprotocol.io/v0/servers?search=kicad&version=latest
- 公式 MCP レジストリ（EasyEDA 検索）: https://registry.modelcontextprotocol.io/v0/servers?search=easyeda&version=latest
- 公式 MCP レジストリ（circuit 検索）: https://registry.modelcontextprotocol.io/v0/servers?search=circuit&version=latest
- 公式 MCP レジストリ（pcb 検索）: https://registry.modelcontextprotocol.io/v0/servers?search=pcb&version=latest
- 公式 MCP レジストリ（digikey 検索）: https://registry.modelcontextprotocol.io/v0/servers?search=digikey&version=latest
- 公式 MCP レジストリ（kicad-mcp-pro の全版）: https://registry.modelcontextprotocol.io/v0/servers?search=kicad-mcp-pro&limit=100
- Glama（kicad）: https://glama.ai/mcp/servers?query=kicad
- Glama（jlcpcb）: https://glama.ai/mcp/servers?query=jlcpcb
- Glama（lcsc）: https://glama.ai/mcp/servers?query=lcsc
- Glama（spice）: https://glama.ai/mcp/servers?query=spice
- Glama（raspberry pi pico）: https://glama.ai/mcp/servers?query=raspberry%20pi%20pico
- Glama（datasheet）: https://glama.ai/mcp/servers?query=datasheet
- PulseMCP（kicad）: https://www.pulsemcp.com/servers?q=kicad
- mcp.so（kicad）: https://mcp.so/search?q=kicad
- Smithery（lamaalrajih）: https://smithery.ai/server/@lamaalrajih/kicad-mcp/api
- Smithery（whatic）: https://smithery.ai/servers/pit-here/whatic
- GitHub 検索 "kicad mcp": https://github.com/search?q=kicad+mcp&type=repositories&s=stars
- GitHub 検索 "jlcpcb mcp": https://github.com/search?q=jlcpcb+mcp&type=repositories
- GitHub 検索 "akizuki": https://github.com/search?q=akizuki&type=repositories
- pcbparts-mcp: https://github.com/Averyy/pcbparts-mcp
- kicad-mcp-pro: https://github.com/oaslananka/kicad-mcp-pro
- kicad-mcp-pro README: https://raw.githubusercontent.com/oaslananka/kicad-mcp-pro/main/README.md
- kicad-mcp-pro PyPI: https://pypi.org/pypi/kicad-mcp-pro/json
- kicad-mcp-pro npm: https://registry.npmjs.org/kicad-mcp-pro
- kicad-mcp-pro 2.1.0（旧版ページ）: https://pypi.org/project/kicad-mcp-pro/2.1.0/
- ProductOfAmerica/mcp-server-kicad: https://github.com/ProductOfAmerica/mcp-server-kicad
- ProductOfAmerica README: https://raw.githubusercontent.com/ProductOfAmerica/mcp-server-kicad/main/README.md
- ProductOfAmerica PyPI: https://pypi.org/pypi/mcp-server-kicad/json
- mixelpixx/KiCAD-MCP-Server: https://github.com/mixelpixx/KiCAD-MCP-Server
- mixelpixx README: https://raw.githubusercontent.com/mixelpixx/KiCAD-MCP-Server/main/README.md
- mixelpixx/Konnect: https://github.com/mixelpixx/Konnect
- Konnect README: https://raw.githubusercontent.com/mixelpixx/Konnect/main/README.md
- Konnect-EDA: https://github.com/Orchis-ai-LLC/Konnect-EDA
- konnect-maintained（AGPL フォーク）: https://github.com/dylbertram/konnect-maintained
- Seeed-Studio/kicad-mcp-server: https://github.com/Seeed-Studio/kicad-mcp-server
- Seeed README: https://raw.githubusercontent.com/Seeed-Studio/kicad-mcp-server/main/README.md
- lamaalrajih/kicad-mcp: https://github.com/lamaalrajih/kicad-mcp
- turbyho/kicad-workbench: https://github.com/turbyho/kicad-workbench
- nevenfo/kicad-agentic-mcp: https://github.com/nevenfo/kicad-agentic-mcp
- belaszalontai/kipilot-mcp: https://github.com/belaszalontai/kipilot-mcp
- daedalus/mcp-kicad: https://github.com/daedalus/mcp-kicad
- bunnyf/pcb-mcp: https://github.com/bunnyf/pcb-mcp
- biosshot/kicad-copilot: https://github.com/biosshot/kicad-copilot
- circuit-synth/mcp-kicad-sch-api: https://github.com/circuit-synth/mcp-kicad-sch-api
- blwfish/kicad-mcp: https://github.com/blwfish/kicad-mcp
- Eyalm321/jlcpcb-mcp: https://github.com/Eyalm321/jlcpcb-mcp
- nvsofts/jlcpcb-parts-mcp: https://github.com/nvsofts/jlcpcb-parts-mcp
- hulryung/jlcpcb-skill-mcp: https://github.com/hulryung/jlcpcb-skill-mcp
- peterb154/jlcpcb-search-mcp: https://github.com/peterb154/jlcpcb-search-mcp
- zhr1008/component-sourcing-mcp: https://github.com/zhr1008/component-sourcing-mcp
- pipeworx-io/mcp-octopart: https://github.com/pipeworx-io/mcp-octopart
- SpectraSynq/mcp-nexar: https://github.com/SpectraSynq/mcp-nexar
- bengineer19/digikey_mcp: https://github.com/bengineer19/digikey_mcp
- JPMarhefka/Partuno: https://github.com/JPMarhefka/Partuno
- npm digikey-mcp（mrfentmen）: https://registry.npmjs.org/digikey-mcp
- salitronic/eda-agent: https://github.com/salitronic/eda-agent
- coffeenmusic/altium-mcp: https://github.com/coffeenmusic/altium-mcp
- embedded-society/altium-designer-mcp: https://github.com/embedded-society/altium-designer-mcp
- groundplane-studio/fusion-electronics-mcp: https://github.com/groundplane-studio/fusion-electronics-mcp
- charlielockyer-rice/tscircuit-mcp: https://github.com/charlielockyer-rice/tscircuit-mcp
- easyeda/easyeda-client-cli: https://github.com/easyeda/easyeda-client-cli
- easyeda/easyeda-api-skill: https://github.com/easyeda/easyeda-api-skill
- easyeda/extension-dev-mcp-tools: https://github.com/easyeda/extension-dev-mcp-tools
- EasyEDA Pro 拡張 API ガイド: https://prodocs.easyeda.com/en/api/guide/
- EasyEDA pro-api-sdk 案内: https://prodocs.easyeda.com/en/api/guide/ancillary-projects/pro-api-sdk.html
- oaslananka/easyeda-mcp-pro: https://github.com/oaslananka/easyeda-mcp-pro
- biosshot/easyeda-copilot: https://github.com/biosshot/easyeda-copilot
- hyl64/jlcmcp: https://github.com/hyl64/jlcmcp
- zhoushoujianwork/easyeda-agent: https://github.com/zhoushoujianwork/easyeda-agent
- VLab-Software/easyeda_mcp: https://github.com/VLab-Software/easyeda_mcp
- I-CAN-hack/pdf-mcp: https://github.com/I-CAN-hack/pdf-mcp
- turbyho/datasheet-lens: https://github.com/turbyho/datasheet-lens
- clanker-lover/spicebridge: https://github.com/clanker-lover/spicebridge
- Cognitohazard/ltspice-mcp: https://github.com/Cognitohazard/ltspice-mcp
- lucasgerads/spicelib-mcp: https://github.com/lucasgerads/spicelib-mcp
- gtnoble/ngspice-mcp: https://github.com/gtnoble/ngspice-mcp
- Freerouting MCP ガイド: https://raw.githubusercontent.com/freerouting/freerouting/master/docs/API/MCP.md
- Freerouting MCP npm: https://registry.npmjs.org/@freerouting/freerouting-mcp-server
- easyeda/easyeda-pcb-router: https://github.com/easyeda/easyeda-pcb-router
- Adancurusul/embedded-debugger-mcp: https://github.com/Adancurusul/embedded-debugger-mcp
- okhsunrog/flashprobe-mcp: https://github.com/okhsunrog/flashprobe-mcp
- Klievan/jlink-mcp: https://github.com/Klievan/jlink-mcp
- microhenrio/openocd-mcp: https://github.com/microhenrio/openocd-mcp
- luiox/openocd-mcp: https://github.com/luiox/openocd-mcp
- qarnet/serial-mcp: https://github.com/qarnet/serial-mcp
- es617/serial-mcp-server: https://github.com/es617/serial-mcp-server
- KenosInc/sigrok-mcp-server: https://github.com/KenosInc/sigrok-mcp-server
- jl-codes/platformio-mcp: https://github.com/jl-codes/platformio-mcp
- powerdragonfire/platformio.mcp: https://github.com/powerdragonfire/platformio.mcp
- platformio.mcp PyPI: https://pypi.org/pypi/platformio.mcp/json
- ctrlpi/pico-bay: https://github.com/ctrlpi/pico-bay
- Wokwi MCP 対応文書: https://docs.wokwi.com/wokwi-ci/mcp-support
- KiCad GitLab の MCP 関連課題検索: https://gitlab.com/api/v4/projects/kicad%2Fcode%2Fkicad/issues?search=MCP
- KiCad GitLab #24803: https://gitlab.com/kicad/code/kicad/-/work_items/24803
- KiCad GitLab #25666: https://gitlab.com/kicad/code/kicad/-/work_items/25666

#### 1.8 Claude Code への接続とクラウドの制約
- Claude Code の MCP 文書: https://code.claude.com/docs/en/mcp
- Claude Code のクラウド環境文書: https://code.claude.com/docs/en/cloud-environments

#### 1.9 ファームウェア・6502・テスト ROM・エミュレータ
- pico-sdk: https://github.com/raspberrypi/pico-sdk
- pico-sdk リリース（API）: https://api.github.com/repos/raspberrypi/pico-sdk/releases
- pico-sdk リリース（HTML）: https://github.com/raspberrypi/pico-sdk/releases
- picotool: https://github.com/raspberrypi/picotool
- picotool リリース（API）: https://api.github.com/repos/raspberrypi/picotool/releases
- Findpicotool.cmake: https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpicotool.cmake
- Findpioasm.cmake: https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpioasm.cmake
- pioasm のソース: https://github.com/raspberrypi/pico-sdk/tree/master/tools/pioasm
- SDK host platform: https://github.com/raspberrypi/pico-sdk/tree/master/src/host
- SDK host platform README: https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/host/README.md
- RP2350 データシート（build 01/10/2026）: https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-3-rp2350-datasheet.pdf
- 秋月 Pico 2: https://akizukidenshi.com/catalog/g/g129604/
- LCSC RP2350A C42411118: https://www.lcsc.com/product-detail/C42411118.html
- rp2040-pio-emulator: https://github.com/NathanY3G/rp2040-pio-emulator
- rp2040js: https://github.com/wokwi/rp2040js
- rp2040js の所在確認（wokwi 組織）: https://github.com/wokwi
- Wokwi CLI: https://github.com/wokwi/wokwi-cli
- Wokwi CI 入門: https://docs.wokwi.com/wokwi-ci/getting-started
- Wokwi CLI の導入: https://docs.wokwi.com/wokwi-ci/cli-installation
- Wokwi GitHub Actions: https://docs.wokwi.com/wokwi-ci/github-actions
- Wokwi Pi Pico: https://docs.wokwi.com/parts/wokwi-pi-pico
- Wokwi Pi Pico 2: https://docs.wokwi.com/parts/board-pi-pico-2
- Wokwi 料金: https://wokwi.com/pricing
- MesenCE: https://github.com/nesdev-org/MesenCE
- MesenCE リリース: https://github.com/nesdev-org/MesenCE/releases
- MesenCE リリース（atom）: https://github.com/nesdev-org/MesenCE/releases.atom
- MesenCE CommandLineHelper.cs: https://raw.githubusercontent.com/nesdev-org/MesenCE/master/UI/Utilities/CommandLineHelper.cs
- MesenCE TestRunner.cs: https://raw.githubusercontent.com/nesdev-org/MesenCE/master/UI/Utilities/TestRunner.cs
- MesenCE LuaApi.cpp: https://raw.githubusercontent.com/nesdev-org/MesenCE/master/Core/Debugger/LuaApi.cpp
- Mesen2（旧）: https://github.com/SourMesen/Mesen2
- Mesen2 リリース（atom）: https://github.com/SourMesen/Mesen2/releases.atom
- 旧 Mesen の API 文書: https://www.mesen.ca/docs/apireference.html
- FCEUX リリース（atom）: https://github.com/TASEmulators/fceux/releases.atom
- FCEUX: https://github.com/TASEmulators/fceux
- FCEUX 起動オプション: https://fceux.com/web/help/CommandLineOptions.html
- FCEUX Lua 関数一覧: https://fceux.com/web/help/LuaFunctionsList.html
- cc65: https://cc65.github.io/
- cc65 入門: https://cc65.github.io/getting-started.html
- cc65 リポジトリ: https://github.com/cc65/cc65
- cc65 version.c: https://raw.githubusercontent.com/cc65/cc65/master/src/common/version.c
- cc65 リリース（atom）: https://github.com/cc65/cc65/releases.atom
- cc65 SourceForge: https://sourceforge.net/projects/cc65/files/
- asm6f: https://github.com/freem/asm6f
- asm6f リリース（atom）: https://github.com/freem/asm6f/releases.atom
- NESASM CE: https://github.com/ClusterM/nesasm
- llvm-mos-sdk: https://github.com/llvm-mos/llvm-mos-sdk
- neslib: https://github.com/clbr/neslib
- nesdoug: https://nesdoug.com/
- NESdev wiki Tools: https://www.nesdev.org/wiki/Tools
- NESdev wiki NROM: https://www.nesdev.org/wiki/NROM
- NESdev wiki UxROM: https://www.nesdev.org/wiki/UxROM
- NESdev wiki Emulator tests: https://www.nesdev.org/wiki/Emulator_tests
- nes-test-roms アーカイブ: https://github.com/christopherpow/nes-test-roms
- instr_test-v5: https://github.com/christopherpow/nes-test-roms/tree/master/instr_test-v5
- instr_test-v5 readme: https://raw.githubusercontent.com/christopherpow/nes-test-roms/master/instr_test-v5/readme.txt
- ppu_vbl_nmi: https://github.com/christopherpow/nes-test-roms/tree/master/ppu_vbl_nmi
- apu_test: https://github.com/christopherpow/nes-test-roms/tree/master/apu_test
- AccuracyCoin: https://github.com/100thCoin/AccuracyCoin
- full_nes_palette: http://www.slack.net/~ant/nes-hacks/full_nes_palette.nes
- 240p Test Suite: https://github.com/pinobatch/240p-test-mini
- 240p Test Suite NES 版: https://github.com/pinobatch/240p-test-mini/tree/master/nes
- 240p Test Suite リリース（atom）: https://github.com/pinobatch/240p-test-mini/releases.atom
- 240p Test Suite 項目一覧: https://raw.githubusercontent.com/pinobatch/240p-test-mini/master/nes/src/helppages.txt
- その他の実測（cc65 の ROM 生成、FCEUX の Lua 試験、ngspice、iNES ヘッダ）: toolchain_smoke_test.md と firmware_test_and_bringup.md の実測（URL なし）

#### 1.10 実機確認機材
- NESdev wiki Cycle reference chart: https://www.nesdev.org/wiki/Cycle_reference_chart
- NESdev wiki CPU: https://www.nesdev.org/wiki/CPU
- sigrok: https://sigrok.org/
- sigrok wiki DSLogic Plus: https://sigrok.org/wiki/DreamSourceLab_DSLogic_Plus
- sigrok wiki DSLogic U3Pro16: https://sigrok.org/wiki/DreamSourceLab_DSLogic_U3Pro16
- sigrok wiki Kingst LA2016: https://sigrok.org/wiki/Kingst_LA2016
- sigrok wiki Kingst LA5016: https://sigrok.org/wiki/Kingst_LA5016
- sigrok wiki Saleae Logic8: https://sigrok.org/wiki/Saleae_Logic8
- sigrok wiki Saleae Logic Pro 8: https://sigrok.org/wiki/Saleae_Logic_Pro_8
- sigrok wiki ZEROPLUS LAP-C(16032): https://sigrok.org/wiki/ZEROPLUS_Logic_Cube_LAP-C(16032)
- sigrok wiki Lcsoft Mini Board: https://sigrok.org/wiki/Lcsoft_Mini_Board
- DreamSourceLab ショップ: https://www.dreamsourcelab.com/shop/
- DreamSourceLab DSLogic シリーズ: https://www.dreamsourcelab.com/product/dslogic-series/
- Saleae Logic 8: https://www.saleae.com/products/saleae-logic-8
- 秋月 Saleae Logic8（ほか秋月の各商品ページ）: https://akizukidenshi.com/catalog/g/g108975/
- スイッチサイエンスの DSLogic 検索: https://www.switch-science.com/search?q=DSLogic
- 立ち上がり時間と帯域の関係: https://en.wikipedia.org/wiki/Rise_time
- MEAN WELL RT-65 仕様書: https://www.meanwell.com/Upload/PDF/RT-65/RT-65-SPEC.PDF
- OSSC 製品ページ: https://videogameperfection.com/products/open-source-scan-converter/
- OSSC wiki: https://junkerhq.net/xrgb/index.php?title=OSSC
- RetroTINK-4K CE: https://www.retrotink.com/shop/retrotink-4k-ce
- RetroTINK-5X Pro: https://www.retrotink.com/shop/retrotink-5x-pro
- GBS-Control: https://ramapcsx2.github.io/gbs-control/
- HAKKO FR-301 取扱説明書: https://www.hakko.com/japan/support/doc/result.php?mode=download&seq=5895
- HAKKO FR-301 仕様: https://www.hakko.com/japan/products/hakko_fr301_spec.html
- HAKKO FR-301 ノズル: https://www.hakko.com/japan/products/hakko_fr301_tips.html
- TI SSYA010A（ESD 対策）: https://www.ti.com/lit/an/ssya010a/ssya010a.pdf
- EverDrive N8 PRO Fami: https://krikzz.com/our-products/cartridges/n8-pro-fami.html
- krikzz サイトマップ: https://krikzz.com/sitemap.xml
- EverDrive N8 PRO 開発資料: https://github.com/krikzz/edn8-pro-pub
- XGecu: http://www.xgecu.com/en/
- minipro: https://gitlab.com/DavidGriffith/minipro
- minipro README: https://gitlab.com/DavidGriffith/minipro/-/raw/master/README.md
- 秋月 SST39VF040（ほか秋月のメモリ部品）: https://akizukidenshi.com/catalog/g/g112066/
- jlcsearch（SST39SF040 の照会例）: https://jlcsearch.tscircuit.com/components/list.json?search=SST39SF040
- FC-DiscreteCart: https://github.com/ponchick/FC-DiscreteCart
- NES-Famicom-Cartridge-PCBs: https://github.com/Gumball2415/NES-Famicom-Cartridge-PCBs
- coolgirl-famicom-multicart: https://github.com/ClusterM/coolgirl-famicom-multicart
- famicom-dumper-writer: https://github.com/ClusterM/famicom-dumper-writer
- fc-rom-vomitter: https://github.com/Keitark/fc-rom-vomitter

### 2. 第1次調査からの訂正
- 訂正の根拠は 1 章の各出典と同じ。主なもの:
- 公式 MCP レジストリ（kicad-mcp-pro の全版）: https://registry.modelcontextprotocol.io/v0/servers?search=kicad-mcp-pro&limit=100
- Glama（jlcpcb）: https://glama.ai/mcp/servers?query=jlcpcb
- Konnect README: https://raw.githubusercontent.com/mixelpixx/Konnect/main/README.md
- Konnect-EDA: https://github.com/Orchis-ai-LLC/Konnect-EDA
- mixelpixx README: https://raw.githubusercontent.com/mixelpixx/KiCAD-MCP-Server/main/README.md
- jlcsearch: https://jlcsearch.tscircuit.com/components/list.json?search=74HC245&limit=20
- Freerouting MCP npm: https://registry.npmjs.org/@freerouting/freerouting-mcp-server
- KiCad GitLab #24803: https://gitlab.com/kicad/code/kicad/-/work_items/24803
- KiCad GitLab #25666: https://gitlab.com/kicad/code/kicad/-/work_items/25666
- platformio.mcp PyPI: https://pypi.org/pypi/platformio.mcp/json
- easyeda-client-cli: https://github.com/easyeda/easyeda-client-cli
- Claude Code のクラウド環境文書: https://code.claude.com/docs/en/cloud-environments
- JLCPCB 部品検索 API: https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- JLCPCB 部品検索画面: https://jlcpcb.com/parts/componentSearch?searchTxt=74HC
- pico-sdk リリース（API）: https://api.github.com/repos/raspberrypi/pico-sdk/releases
- Findpioasm.cmake: https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/tools/Findpioasm.cmake
- rp2040js npm: https://registry.npmjs.org/rp2040js
- Wokwi GitHub Actions: https://docs.wokwi.com/wokwi-ci/github-actions
- Wokwi Pi Pico 2: https://docs.wokwi.com/parts/board-pi-pico-2
- Wokwi 料金: https://wokwi.com/pricing
- MesenCE LuaApi.cpp: https://raw.githubusercontent.com/nesdev-org/MesenCE/master/Core/Debugger/LuaApi.cpp
- cc65 リリース（atom）: https://github.com/cc65/cc65/releases.atom
- FCEUX リリース（atom）: https://github.com/TASEmulators/fceux/releases.atom
- FCEUX 起動オプション: https://fceux.com/web/help/CommandLineOptions.html
- NESdev wiki Emulator tests: https://www.nesdev.org/wiki/Emulator_tests
- XGecu: http://www.xgecu.com/en/
- minipro README: https://gitlab.com/DavidGriffith/minipro/-/raw/master/README.md
- sigrok wiki Saleae Logic8: https://sigrok.org/wiki/Saleae_Logic8
- sigrok wiki Lcsoft Mini Board: https://sigrok.org/wiki/Lcsoft_Mini_Board
- その他の訂正（KiCad の導入、CDFER のサイズ、kiutils/kicad-skip、Python 版、Freerouting jar の Java 版）: toolchain_smoke_test.md のコンテナ実測（URL なし）

### 3. 未確認事項と実機で確かめるべきこと
- JLCPCB 製造能力表（未取得の数値）: https://jlcpcb.com/capabilities/pcb-capabilities
- JLCPCB 用設計ルール（コミュニティ版）: https://github.com/labtroll/KiCad-DesignRules
- JLCPCB 用設計ルール（コミュニティ版）: https://github.com/Cimos/KiCad-CustomDesignRules
- KiCad 開発者メーリングリスト（eeschema IPC）: https://groups.google.com/a/kicad.org/g/devlist/c/3e8OU0FiEHc
- KiCad GitLab #24803 / #25666（上記）
- RP2350 データシート（ステッピング）: https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-3-rp2350-datasheet.pdf
- OSSC wiki（入力の終端）: https://junkerhq.net/xrgb/index.php?title=OSSC
- MesenCE TestRunner.cs: https://raw.githubusercontent.com/nesdev-org/MesenCE/master/UI/Utilities/TestRunner.cs
- Wokwi Pi Pico 2: https://docs.wokwi.com/parts/board-pi-pico-2
- Adancurusul/embedded-debugger-mcp（probe-rs）: https://github.com/Adancurusul/embedded-debugger-mcp
- jlcsearch（在庫値の食い違い）: https://jlcsearch.tscircuit.com/components/list.json?search=C5605
- LCSC RP2350A C42411118: https://www.lcsc.com/product-detail/C42411118.html

### 4. ユーザー要求への影響
- 4 章の事実部分は 1 章の出典に基づく。主なもの:
- JLCPCB 部品検索 API: https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- pcbparts-mcp: https://github.com/Averyy/pcbparts-mcp
- KiBot: https://github.com/INTI-CMNB/KiBot
- AccuracyCoin: https://github.com/100thCoin/AccuracyCoin
- EverDrive N8 PRO Fami: https://krikzz.com/our-products/cartridges/n8-pro-fami.html
- FCEUX Lua 関数一覧: https://fceux.com/web/help/LuaFunctionsList.html
- MesenCE LuaApi.cpp: https://raw.githubusercontent.com/nesdev-org/MesenCE/master/Core/Debugger/LuaApi.cpp
- SDK host platform README: https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/host/README.md
- Wokwi Pi Pico 2: https://docs.wokwi.com/parts/board-pi-pico-2
- picotool リリース（API）: https://api.github.com/repos/raspberrypi/picotool/releases
- pico-sdk リリース（API）: https://api.github.com/repos/raspberrypi/pico-sdk/releases
- KiCad 開発者メーリングリスト（SWIG の扱い）: https://groups.google.com/a/kicad.org/g/devlist/c/3e8OU0FiEHc
- DreamSourceLab ショップ: https://www.dreamsourcelab.com/shop/
- 秋月の各商品ページ（価格）: https://akizukidenshi.com/catalog/g/g108975/
- 要求の内容: user_requirements.md（URL なし）

## 6. 検証記録

検証日: 2026-11-10。1〜4章の各表と数値・識別子を、元ノート（tooling_and_mcp.md、mcp_landscape.md、toolchain_smoke_test.md、firmware_test_and_bringup.md）、相互参照（parts_class_reverification.md）、要求（user_requirements.md）と1件ずつ照合した。第2次調査ノートの「既存ノートへの訂正」節は、すべて第1次調査の値より優先して照合した。

### 6.1 照合した項目数（合計 約540件）

| 範囲 | 照合した事実の数 | 結果 |
|---|---|---|
| 1.2 工程別ツール表（8表・49行。版数、日付、サイズ、件数、確度） | 約150 | 誤り0。区分の誤り1（jlcsearch）、確度の付け方1（下記） |
| 1.3 導入手順・セットアップスクリプト・通信先表（コマンド、時間、DL 量、鍵指紋、sha256、ホスト16行） | 約70 | 誤り0。スクリプトは元ノートと1行ずつ一致、sha256 一致 |
| 1.4 動かなかったもの（17行） | 約30 | 確度の付け方1（Flatpak） |
| 1.5 KiCad 10 形式・kicad-cli 表（13行）・ライブラリ表（5行）・IPC API・手順 | 約60 | 誤り0 |
| 1.6 部品データ（情報源表、信頼性表、KiBot、ライブラリ化、公式 API） | 約45 | 誤り0（件数 351/352/1,235/1,220/989/1,226、在庫 84,778/84,880/86,210/53,168、C5605 価格を parts_class_reverification.md と照合） |
| 1.7 MCP 評価表（26行。★、push 日、版、ライセンス、ツール数） | 約90 | 誤り0。Freerouting MCP の導入版を補足 |
| 1.8 Claude Code の MCP 設定・クラウド制約 | 約25 | 誤り0 |
| 1.9 Pico SDK/picotool 版表、RP2350 ステッピング、試験手段、6502 ツール、エミュレータ、テスト ROM | 約80 | 74HC161 の記述を更新 |
| 1.10〜1.11 機材（ロジアナ8行、機材14行、価格・商品コード・仕様） | 約70 | 誤り0 |
| 2章 訂正表（5表・30行） | 30 | Freerouting の未確認事項を解決 |
| 4章 要求への影響（9節、金額の合計 ￥64,570・￥1,320 を再計算） | 約20 | 現行要求の記述を補強（下記） |

### 6.2 訂正・変更の内容

| 箇所 | 変更前 | 変更後 | 根拠 |
|---|---|---|---|
| 1.2 部品選定表 jlcsearch の区分 | 「必須（裏取り。MCP ではない HTTP API）」 | 「推奨（候補の検索・絞り込み。…JLCPCB と独立した裏取りにはならない）」 | parts_class_reverification.md: jlcsearch・jlcparts・CDFER は同じ巡回データ系統で、独立した第2の出典ではない。シート自身の 1.6.1・1.6.2 の結論とも矛盾していた |
| 1.9.4 マッパの選択 | 「74HC161 のクラスは未確認」 | Basic 351件・Preferred 1,235件の全件リストに含まれないので Basic では使えない（確認済）。Extended の C 番号と在庫は未確認 | parts_class_reverification.md §3 の74系ロジック行（Basic は 74HC14・74HC595 のみ、Preferred は 74HC04/08/165/245・SN74LVC4245A のみ、他は Extended） |
| 3.1 の18番 | 「74HC161 の JLCPCB クラス」 | 「74HC161 の C 番号と在庫」（Basic・Preferred にないことは確認済み） | 同上 |
| 1.7.2 Freerouting 公式 MCP の行 | 導入版の記載なし | 本体の MCP サーバーは v2.3.0 から、`autoroute_board` は v2.5.0 で追加 | Freerouting のリリースページを本検証で取得（v2.3.0 の「Dedicated Model Context Protocol server」、v2.5.0 の「MCP `autoroute_board`」）。第1次調査は2つの版を併記、第2次調査は未確認としていた |
| 2.3 Freerouting の訂正行 | 「どの版で `autoroute_board` が入ったかは未確認」 | 上記の確認結果に置換 | 同上 |
| 1.4 Flatpak 版 KiCad の確度 | 単一出典 | 確認済（このクラウド環境での実測） | 1.1 の定義では環境での実測は確認済。tooling_and_mcp.md と toolchain_smoke_test.md の両方が実測を記録 |
| 4.4 | 現行要求の中身（タイマー方式のコインの扱い、2P スタート → I コンの SELECT、デフォルト・特殊形式の割り当て）が書かれていなかった | 要求3章の現行の割り当てを追記。特殊形式で軸が読めなくなる点と、タイマー方式でコインが漏れないことを試験項目に追加 | user_requirements.md 3.3〜3.5、3.7 |
| 4.5 | 切り替えの経路が通信手順だけ。拡張ビットの範囲があいまい | 不揮発メモリ・テストスイッチ（ピン15）・USB の経路、市販ソフトは担当者がタイマー方式に設定することを追記（推論と明記）。読み出しビットを「$4016 の D1・$4017 の D1〜D4」に具体化 | user_requirements.md 4.2 |
| 4.8 | Pico 2 の端子形状と Type-C 端子の部品クラスに触れていなかった | Pico 2 は Micro-B で USB 信号が端子列に出ないこと、C393939 は在庫 340,763 だが Extended で USB-C 端子は Basic・Preferred にないこと、RP2350 の書き換え不能な USB 書き込み機能を追記 | user_requirements.md 6.2、parts_class_reverification.md（C393939 の行、§3 の USB コネクタ行） |

4章が評価している要求が現行版か: タイマー方式、デフォルト形式・特殊形式、ソフトウェアでの切り替え、Raspberry Pi の枚数自由、CPU・PPU・メモリの将来更新、USB Type-C 更新端子の6点とも、user_requirements.md の現行版（第5回の追加指示まで）に沿っていた。置き換え済みの指示（DIP スイッチでの切り替え、C=上下同時・D=左右同時）を前提にした記述はなかった。上記は欠けていた要求の中身を補ったもの。

### 6.3 出典で確かめた項目

| 項目 | 確かめた出典 | 結果 |
|---|---|---|
| MesenCE の Lua 関数（`stop` が登録され `exit` はない、`LuaApi::Stop` が `SetStopCode` を呼ぶ） | MesenCE の LuaApi.cpp（raw） | 一致 |
| マスタークロック 21.477272 MHz ± 40 Hz、CPU ÷12 = 1.789773 MHz、PPU 1ドット = 4マスタークロック | NESdev Wiki Cycle reference chart（`?action=raw`） | 一致 |
| Freerouting の MCP 導入版、v2.5.0 のネイティブ CLI が Java 不要 | Freerouting のリリースページ | 6.2 のとおり補足。Java 不要の記述は一致 |

### 6.4 確認できなかったこと・判断を変えなかったこと

- 元ノートで未確認のまま残っている事項（3章の一覧）は、本検証でも確認していない。特に回路図エディタの IPC API の範囲、Wokwi の RP2350/PIO の精度、probe-rs の RP2350 対応、JLCPCB の設計ルールの数値（5mil と 3.5mil の不一致）、pcbparts-mcp の2系統の版表記、販売中の RP2350 のステッピング、JAMMA の RGB の電圧は未解決。
- mixelpixx のツール数（251 と 244）と datasheet-lens の版（0.6.1 と README の 0.4）は出典自体が矛盾しており、シートの扱いを変えていない。
- 確度が実際より低く付いている行（環境で実測した apt の版数、`apt に freerouting などがない` など、「単一出典」と付いているもの）は、危険側の誤りではないため Flatpak 以外は変えていない。
- 1.2 の KiKit の「JAMMA 基板が1枚なら不要」は、元ノートの「単面なら不要」を言い換えたもの。元の語の意味（片面か1枚か）は確認できなかったが、パネル化の用途から見て妥当なので残した。
- 本文中の URL は 1.3.2 のスクリプトと 1.8.3 の `.mcp.json` の例にだけあり、どちらもコマンドの引数・設定値（シート中でそう明記済み）なので残した。出典の URL は5章にだけある。
