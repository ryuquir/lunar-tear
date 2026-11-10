# ツールチェーン実地スモークテスト (Ubuntu 24.04 / root / 4CPU / コンテナ) — 2026-11-10

作業ディレクトリ: /tmp/toolchain_test/ 。本ノートは逐次更新中(途中保存)。

## Step 1: KiCad 10 (PPA)
- `add-apt-repository -y ppa:kicad/kicad-10.0-releases` → **失敗**: `ModuleNotFoundError: No module named 'apt_pkg'` (原因: /usr/bin/python3 が alternatives で python3.13 を指し、apt_pkg は python3.12 用のみ)
- 回避: `python3.12 /usr/bin/add-apt-repository -y ppa:kicad/kicad-10.0-releases` → 成功 (5.6秒、鍵はLaunchpad経由でsourcesファイルに埋め込み)
- `apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints` → 成功 20秒、DL 151MB、追加ディスク 947MB(apt表示)/実測 約840MB。78新規+1更新パッケージ
- kicad-cli version → 10.0.8 (`KICAD_IPC_API=ON`, ngspice 42, OCC 7.6.3)
- 注意: KiCadの `_pcbnew.so` は libpython3.12 にリンク。本コンテナの `python3` は 3.13 (/usr/local/bin) だが `/usr/lib/python3/dist-packages` を sys.path に含むため import自体は通ってしまう(異なるlibpythonの混在で危険)。**pcbnew は必ず `/usr/bin/python3.12` で使う**。
- 初回の kicad-cli / pcbnew 実行で ~/.config/kicad/10.0/ が自動生成されるが、sym-lib-table / fp-lib-table は**作られない** → ERCで "The current configuration does not include the symbol library 'Device'" 警告。回避: `cp /usr/share/kicad/template/{sym,fp}-lib-table $KICAD_CONFIG_HOME/10.0/` (本テストは `KICAD_CONFIG_HOME=/tmp/toolchain_test/kcfg`)。

## Step 2: kicad-cli ヘッドレス (DISPLAY無し、xvfb無し)
テスト基板: kicad-sch-api で生成した4部品(J1 Conn_01x04, R1 470, R2 1k, R3 75)の映像DAC風回路 → kicad-cli netlist → 自作pcbnewスクリプトでPCB化(後述)。

| コマンド | 結果 | 時間 |
|---|---|---|
| `kicad-cli sch erc -o erc.rpt dac.kicad_sch` | PASS (lib-table設定後 0 violations) | 0.4s |
| `kicad-cli sch upgrade --force` | PASS: KiCad 10 回路図フォーマット `(version 20260306)` `(generator_version "10.0")` | <1s |
| `kicad-cli sch export netlist -o dac.net` | PASS (4ネット正しい) | <1s |
| `kicad-cli sch export bom -o bom.csv --fields 'Reference,Value,Footprint,${QUANTITY}' --group-by Value` | PASS | <1s |
| `kicad-cli pcb drc --schematic-parity -o drc.rpt` | PASS (parity 0件、未配線6件=想定通り) | 3.9s |
| `kicad-cli pcb export gerbers -o out/gerber/` | PASS (※--layers未指定だと全レイヤ29ファイル出力) | 0.4s |
| `kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2` | PASS | 0.4s |
| `kicad-cli pcb export pos --format csv --units mm --side both` | PASS | 0.2s |
| `kicad-cli pcb export pdf --layers F.Cu,F.SilkS,Edge.Cuts` | PASS | 0.3s |
| `kicad-cli pcb export svg --mode-single -o out/plots/` | FAIL "Failed to create file" → `-o` にファイル名を与えれば PASS | 0.3s |
| `kicad-cli sch export pdf` / `sch export svg` | PASS | 0.3s |
| `kicad-cli pcb export step` / `glb` / `ipc2581` / `odb` | PASS | <0.4s |
| `kicad-cli pcb render -o x.png` (DISPLAY無し) | **PASS: xvfb不要**(CPUレイトレーサ)。`--quality high --rotate '-45,0,45' --floor --perspective` で 800x450 が 1.9s | 0-2s |
- PCBフォーマット: `(kicad_pcb (version 20260206) (generator_version "10.0"))`
- 3Dモデル(kicad-packages3d: DL 280MB / 展開 3.29GB)は未導入。renderは部品本体なしで基板・パッド・シルクのみ描画(画像確認済)。

## Step 3: Pythonによる自動化
### 3a. SWIG `pcbnew` (KiCad同梱, `/usr/bin/python3.12`)
- `/usr/bin/python3.12 -c "import pcbnew; print(pcbnew.Version())"` → `10.0.8` (PASS)
- scripts/pcbnew_edit.py: `pcbnew.LoadBoard()` → `FootprintLoad(".../Capacitor_SMD.pretty","C_0603_1608Metric")` 追加 → `PCB_TRACK` 3本追加(VOUTネット) → `pcbnew.SaveBoard()` → `PLOT_CONTROLLER` で F_Cu/Edge_Cuts のGerber出力 → **全てPASS**。保存結果を `kicad-cli pcb drc` で再読込: 0 violations、未配線 6→5 (追加配線が認識された)。
- scripts/net2pcb.py (自作 約40行): kicad-cliのnetlist(.net)を正規表現で読み、`FootprintLoad`→`SetPosition`→`pad.SetNet()`→Edge.Cuts外形→`SaveBoard`。**これがヘッドレスで「回路図→足跡配置済みPCB」を作る確実な経路だった**(`kicad-cli pcb drc --schematic-parity` で parity 0件)。KiCadには「回路図からPCBを更新」(F8相当)のCLIは無い(kicad-cli 10.0のサブコマンド一覧に該当なし)。

### 3b. kicad-python (kipy) 0.8.0 + IPC API — xvfb下で**動作した**
- `pip install kicad-python` → 0.8.0 (依存 protobuf 5.29.6, pynng 0.9.0)、3秒。
- IPC APIサーバは GUI の pcbnew が提供。`kicad_common.json` の `"api": {"enable_server": true}` で有効化。ソケット: `/tmp/kicad/api.sock`。
- 1回目: `xvfb-run -a pcbnew board.kicad_pcb` → ソケットは出来るが kipy は `ApiError: KiCad returned error: KiCad is not ready to reply`。スクリーンショット(`import -window root`)で原因判明: 初回起動ウィザード「Welcome to KiCad 10.0 / KiCad Setup」がモーダルで待機。xdotoolでCancel→Yesを押すと動作。
- 原因の特定(KiCadソース 10.0ブランチ `common/startwizard/*.cpp`, https://gitlab.com/kicad/code/kicad/-/tree/10.0/common/startwizard): ウィザードは3プロバイダのどれかが `NeedsUserInput()` なら表示。
  - SETTINGS: `!SettingsDirectoryValid()`
  - LIBRARIES: `!LIBRARY_MANAGER::GlobalTablesValid()` → **sym-lib-table, fp-lib-table に加え design-block-lib-table も必要**(実験: これを消すとウィザード再表示)
  - PRIVACY: `!m_DoNotShowAgain.update_check_prompt || !m_DoNotShowAgain.data_collection_prompt`
- **完全非対話の起動方法(実測PASS)**: 空の設定ディレクトリに sym-lib-table / fp-lib-table / design-block-lib-table と次の kicad_common.json を置く:
  `{"api":{"enable_server":true},"do_not_show_again":{"update_check_prompt":true,"data_collection_prompt":true}}`
  → `xvfb-run -a pcbnew board.kicad_pcb &` から**約3秒で** kipy が応答。
- kipy で実行できたこと(PASS): `KiCad().get_version()`→`10.0.8`, `get_board()`, `get_footprints()`, `get_nets()`, `create_items(Track)` (B.Cu), `board.save()`。保存ファイルに B.Cu segment が追加されていることを確認、kicad-cli DRCで再読込OK。
- 制約(推論): GUIプロセス(wx/GTK, Xvfb)常駐が必要で、回路図(eeschema)のIPC APIは無い(既存ノートの devlist 情報と整合)。ヘッドレスCIでは SWIG pcbnew の方が単純。

### 3c. ファイル直接操作ライブラリの KiCad 10 往復(round-trip)試験
入力: KiCad 10.0.8が保存した回路図 `(version 20260306)` と PCB `(version 20260206)`(配線入り)。各ライブラリで読み込み→無変更で書き出し→ kicad-cli で再読込(ERC/DRC/netlist比較)。トークン増減は S式の `(token` 出現数比較(scripts/rt.py と比較スクリプト)。

| ライブラリ | 版 | 回路図 読込/書出 | kicad-cliで再読込 | 内容の欠落 | PCB 読込 |
|---|---|---|---|---|---|
| kiutils | 1.4.8 | OK | ERC 0件, ネットリスト同一 | **あり**: `hide` 16, `do_not_autoplace` 34, `exclude_from_sim` 6, `in_pos_files` 6, `body_style` 4, `embedded_fonts` 2, `duplicate_pin_numbers_are_jumpers` 2, `generator_version` 1 が消失(非表示フィールドが表示に変わる等の静かな破損) | **FAIL** `IndexError: list index out of range` (kiutils/items/common.py:543 `object.name = exp[2]`)。原因: KiCad 10 PCBではパッドのネット参照が `(net "/VOUT")` (番号なし、名前のみ)になっており、旧 `(net 3 "/VOUT")` 前提のパーサが落ちる |
| kicad-skip | 0.2.5 | OK | ERC 0件, ネットリスト同一 | なし(トークン数完全一致。ただし整形は1行に潰れる) | **FAIL** `AttributeError: 'Symbol' object has no attribute '_base_coords'` (skip/pcbnew/footprint.py:59)。配線なしの単純PCBでも同じ |
| kicad-sch-api | 0.5.6 (`__version__`は0.5.5表示) | OK | ERC 0件, ネットリスト同一, `(version 20260306)` 維持 | 小: `in_pos_files` 4, `body_style` 4 消失、`hide` 8, `fields_autoplaced` 4 追加 | 対象外(回路図専用) |

- 新規生成: kicad-sch-api の `create_schematic()` + `components.add("Device:R", ...)` + ピン座標へ `add_label()` で作った回路図は KiCad 9書式 `(version 20250114)` `(generator_version "9.0")` で出力されるが、kicad-cli 10.0.8 で ERC 0件(lib-table設定後)、netlist正常。`kicad-cli sch upgrade --force` で10書式化可能。

### 3d. SKiDL 3.0.0 / kinet2pcb 1.1.4
- `pip install skidl` は 217秒(matplotlib, h5py, numpy 等の依存 — inspice経由)。venv全体 431MB。
- `set_default_tool(KICAD10)` が存在。`lib_search_paths[KICAD10].append("/usr/share/kicad/symbols")` で `Part("Device","R")` 解決 → `generate_netlist()` PASS、`generate_schematic()` PASS(出力は `(version 20250114)` `(generator "skidl")`、kicad-cli ERC は `lib_symbol_mismatch` 警告4件+`power_pin_not_driven` 1件、kicad-cli で書き出したnetlistはSKiDL netlistと同一ネット)。
- `generate_pcb(file_=..., fp_libs=["/usr/share/kicad/footprints"])` → PASS(4フットプリント自動配置(hierplace)、パッドにネット割当済、DRCは外形なしの `invalid_outline` 1件と未配線6件のみ)。`fp_libs` を渡さないと `KeyError 'Connector_PinHeader_2.54mm'`(kinet2pcb の `get_global_fp_lib_table_fn()` は "9.0".."5.0" しか探さず KiCad 10 設定を見ないため)。
- `kinet2pcb -i dac.net`(kicad-cli 10 が出したnetlistファイルを入力)→ **FAIL** `ValueError: Sexp isn't in a form that permits extracting a single value.`(comp内の `(property (name ..)(value ..))` の入れ子 value を拾うバグ)。→ ネットリストファイル経由なら自作 net2pcb.py (3a) を使う。

### 3e. ヘッドレスで「回路図/ネットリスト → フットプリント配置済みPCB」の実証済み経路
1. kicad-sch-api で回路図生成 → `kicad-cli sch erc` → `kicad-cli sch export netlist` → `/usr/bin/python3.12 net2pcb.py`(SWIG pcbnew) → `kicad-cli pcb drc --schematic-parity`(parity 0) — PASS
2. SKiDL(Python記述) → `generate_pcb(fp_libs=[...])` → kicad-cli DRC — PASS(外形は別途追加要)

## Step 4: JLCPCB フロー
### 4a. Fabrication Toolkit (bennymeg)
- `git clone --depth 1 https://github.com/bennymeg/Fabrication-Toolkit.git` → PASS 1秒(gitはセッションgitプロキシ経由でgithub.comに到達。plain curl の github.com/api.github.com は403のまま)。HEAD 7f627b6 (2026-09-29)、metadata.json の先頭 version は "5.3.1"(※配列の先頭=最新とは限らない、未確認)。
- CLI: `python3 -m plugins.cli -p board.kicad_pcb [--nonInteractive] [--noBackup] [--autoFill] [--excludeDNP] [--autoTranslate] ...`(plugins/cli.py 読解)。コードは `import pcbnew` と `import wx`(plugins/utils.py) を行い、`is_v10()` 分岐(9.99≤ver<10.99)を持つ=KiCad 10対応コードあり。
- **実行は未実施(本セッションの権限分類器が「外部から取得したコードの実行」として拒否)**。実行には KiCad同梱の `/usr/bin/python3.12`(pcbnew と python3-wxgtk4.0 はKiCadの依存として導入済)を使い、リポジトリのルートで `/usr/bin/python3.12 -m plugins.cli -p <board> --nonInteractive` とするのが想定手順(推論)。→ **未確認**
- 代替(実証済): kicad-cli だけで JLCPCB 用一式(gerbers, drill, pos CSV, BOM CSV)は出力できる(Step 2)。JLCPCB形式のCPL列名/回転補正は手で変換が必要(推論)。

### 4b. easyeda2kicad 1.0.1 / JLC2KiCadLib 1.3.2 (pip, 3秒)
| コマンド | 結果 |
|---|---|
| `easyeda2kicad --full --lcsc_id=C2040 --output <dir>/lib` | PASS 2秒: シンボル RP2040 (`kicad_symbol_lib (version 20211014)`=KiCad 6書式)、フットプリント `LQFN-56_L7.0-W7.0-P0.4-EP.kicad_mod`、3D (.wrl/.step)。出力先フォルダが無いと `[ERROR] Can't find the folder` → 事前に mkdir 要 |
| `JLC2KiCadLib C25804 -dir <dir>` | PASS 5秒: シンボル `0603WAF1002T5E`(`(property "LCSC" "C25804")` 付き)、フットプリント `R0603.kicad_mod`、STEP |
| 検証: `kicad-cli sym export svg`, `kicad-cli fp export svg`, `kicad-cli sym upgrade --force`(→ `version 20251024`), `kicad-cli fp upgrade --force`(→ `version 20260206`) | 全て PASS(KiCad 10で読める) |
- 使用ホスト(コード内URL): easyeda.com (`/api/products/{lcsc_id}/components`, `/api/components/{uuid}`), modules.easyeda.com (3D), easyeda.com/analyzer/api/3dmodel (JLC2KiCadLib)。いずれもプロキシ経由で到達。

### 4c. jlcsearch / CDFER DB
- `curl "https://jlcsearch.tscircuit.com/api/search?q=RP2040&limit=3"` → HTTP 200: `{"lcsc":2040,"mfr":"RP2040","package":"LQFN-56(7x7)","is_basic":false,"stock":86210,"price":0.9941}`
- `curl "https://jlcsearch.tscircuit.com/components/list.json?search=C25804"` → HTTP 200: 0603WAF1002T5E, `"is_basic":true`
- `curl ".../resistors/list.json?resistance=10k&package=0603"` → HTTP 200 (79kB) だが 10Ω品が返った=`resistance=10k` の解釈が期待と違う(パラメタ書式 未確認)。
- 既存ノートの「curl -I が405」は HEAD 非対応のためで、**GETは200**。
- CDFER: `https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv` → 200, **1,252,216 B**(0.5秒), 1578行(library_type: base 352 / expand(preferred) 1226)。SQLite `jlcpcb-components.sqlite3` → 200, **419,360,768 B (約419MB)**, 18秒, Last-Modified 2026-11-10 05:55 GMT。テーブル `jlc_components` 511,178行(うち `library_type='base'` 351)、`lcsc_components` 47,381行、`meta`(format=source-db-v2)。
- サンプル: `select 'C'||lcsc,mfr,package,library_type,stock from jlc_components where lcsc in (2040,25804)` → `('C2040','RP2040','LQFN-56(7x7)','expand',53168)`, `('C25804','0603WAF1002T5E','0603','base',32380385)`。`mfr like 'RP2350%'` → C42411118 RP2350A QFN-60 (expand, 6849), C42415655 RP2350B QFN-80 (expand, 2925)。
- 注意: FTS5テーブル `jlc_components_fts` (external content) への MATCH は 'RP2350*' でも0件=このスナップショットでは索引が空/不整合。LIKE検索を使う。
- 在庫数は jlcsearch (RP2040 86,210) と CDFER (53,168) で異なる(同期時刻差と推定、推論)。
- github.com への plain curl は403だが、raw.githubusercontent.com と *.github.io (GitHub Pages) は200。

### 4d. KiBot 1.9.1 (pip) — PASS(Fabrication Toolkit の代替として実証)
- `python3.12 -m venv --system-site-packages venv_kibot && venv_kibot/bin/pip install kibot` → 5秒, 35MB。
- 1回目実行: `ERROR:Unable to import plug-ins: cannot import name 'macros' from 'kibot.macros'` + `Make sure you used --no-compile` → 回避: `pip install --no-compile --force-reinstall --no-deps kibot` と `__pycache__` 削除。次に `No module named 'lxml'` → `pip install lxml`。**最初から `pip install --no-compile kibot lxml` とするのが正解**(推論、エラーメッセージの指示に基づく)。
- 設定(全文):
  ```yaml
  kibot:
    version: 1
  global:
    field_lcsc_part: LCSC
  import:
    - file: JLCPCB
  ```
  `kibot -c jlc.kibot.yaml -b dac.kicad_pcb -e dac.kicad_sch -d out` → 2秒, rc=0。出力: `out/JLCPCB/dac-_JLCPCB_compress.zip`(F/B Cu, Silk, Mask, Edge_Cuts, PTH/NPTH drl+map の11ファイル)、`dac_bom_jlc.csv`(Comment, Designator, Footprint, "LCSC Part #")、`dac_cpl_jlc.csv`(Designator, Val, Package, Mid X, Mid Y, Rotation, Layer)。
- 落とし穴: kicad-sch-api が書いた KiCad 9書式の回路図では KiBot が `W036 Component without the basic fields` を出し、LCSC列が空。**`kicad-cli sch upgrade --force` で KiCad 10正規書式にしてから** KiBot に渡すと LCSC列(C2337, C4275, C23179, C21190)が正しく入った。
- 自作 net2pcb.py はフットプリントにシンボルへのリンク(パス/UUID)を設定していないため KiBot が `W013 ... not linked to an existing schematic component` を出す(参照名で照合されるので出力は正しい)。本番では `footprint.SetPath()` で netlist の tstamps を設定すべき(推論)。
- 参考: 使ったLCSC番号を CDFER CSV で照合 → C23179 0603WAF4700T5E (base), C21190 0603WAF1001T5E (base), C4275 0603WAF750JT5E (base), C2337 は basic/preferred CSV に無し(=Extended)。

## Step 5: Freerouting 2.5.0 — DL・DSN出力はPASS、**自動配線の実行は未実施(権限で拒否)**
- GitHub Releases のダウンロードはプロキシ経由で**可能**: `curl -L https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar` → 302 → release-assets.githubusercontent.com → 200, 64,599,107 B, 2.5秒。(github.com のHTMLページ/API は curl 403 だが `/releases/download/` パスは通る)
- アセット一覧(WebFetch https://github.com/freerouting/freerouting/releases/expanded_assets/v2.5.0): freerouting-2.5.0.jar 61.6MB, freerouting-cli-2.5.0-linux-x64.tar.gz 19.8MB, linux-arm64/macos/windows版CLI, AppImage 80.7MB, linux-x64.zip 88.1MB 等 計13件。
- `freerouting-cli-2.5.0-linux-x64.tar.gz` (20,714,066 B) を取得し、公式 `freerouting-cli-2.5.0-checksums.txt` の sha256 `64a957a9...863a` と一致。中身は単一実行ファイル `freerouting-cli` (50,202,888 B)。
- Java要件: jar の MANIFEST `Created-By: 25.0.4.1 (Eclipse Adoptium ...)`、クラスファイル major version **69 = Java 25**。コンテナの既定 Java は OpenJDK 21.0.12 → jarは**そのままでは動かない**(推論: UnsupportedClassVersionError になる)。Ubuntu noble の apt に `openjdk-25-jre-headless 25.0.5.0.3+1-1~24.04.1` あり(DL 59MB, 展開 239MB)。native CLI 版はJava不要(リリースノート: "These native binaries eliminate the Java JRE requirement for CLI users, CI/CD runners")。
- CLI書式(README master, https://raw.githubusercontent.com/freerouting/freerouting/master/README.md): `java -jar freerouting.jar -de MyBoard.dsn -do MyBoard.ses [-inc GND,VCC]`。v2.5.0で `-hr` 削除、`--router.autorouter.*` 形式推奨(リリースページ)。
- DSN出力: KiCad 10 の kicad-cli には Specctra DSN 出力/SES 取込のサブコマンドが**無い**(`pcb export --help`, `pcb import --help` で確認; importはpads/altium/eagle/cadstar/fabmaster/pcad/solidworks のみ)。SWIG で `pcbnew.ExportSpecctraDSN(board, "dac.dsn")` → True (3,857 B, host_version "10.0.8")、`pcbnew.ImportSpecctraSES` も存在(hasattr=True)。
- **未実施**: jar/CLI の実行(autoroute→SES取込)は本セッションの権限分類器が「外部コード実行」として拒否。手順(未検証): `tar xzf freerouting-cli-2.5.0-linux-x64.tar.gz && ./freerouting-cli -de dac.dsn -do dac.ses` → `/usr/bin/python3.12 dsn_io.py import dac.kicad_pcb dac.ses routed.kicad_pcb` → `kicad-cli pcb drc`。→ 未確認

## Step 6: ファームウェア (Pico SDK) — ツール導入・cloneはPASS、**ビルドは未実施(権限で拒否)**
- `apt-get install -y --no-install-recommends gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib cmake ninja-build build-essential cc65 ngspice` → 35秒, DL **581MB**, 新規8パッケージ, ディスク実測 **約3.0GB** 増(大半は newlib/libstdc++ のマルチリブ)。`arm-none-eabi-gcc 13.2.1 20231009 (15:13.2.rel1-2)`。cmake 3.28.3 と ninja 1.11.1 は元から導入済。
- `git clone -b 2.3.1 --depth 1 https://github.com/raspberrypi/pico-sdk.git` → 1秒 PASS。`git submodule update --init --depth 1` → 17秒 PASS (tinyusb, cyw43-driver, lwip, mbedtls, btstack — すべて github.com)。合計 428MB。**セッションgitプロキシ経由のサブモジュール取得は動作**。
- pico-sdk 2.3.1 タグのコミット日付 = **2026-09-04** (git log)。→ 既存ノートで年不明だった「04 Sep」は2026年と確定。
- picotool: SDK の tools/CMakeLists.txt で `set(picotool_VERSION_REQUIRED 2.3.0)`、見つからなければ `https://github.com/raspberrypi/picotool.git` を FetchContent してビルド(Findpicotool.cmake)。`git ls-remote --tags https://github.com/raspberrypi/picotool` は到達可(最新タグ 2.3.1)。
- **未実施**: 最小プログラム(GPIO+printf)と PIO 例(2命令の矩形波 .pio + `pico_generate_pio_header`)を用意し `cmake -S . -B build -G Ninja -DPICO_BOARD=pico`(および `pico2`)を実行しようとしたが、本セッションの権限分類器が「外部コード(clone した SDK の CMake スクリプト)の実行」として拒否。UF2 生成・RP2040/RP2350 両対応・picotool ビルドは **未確認**。

## Step 7: 6502 (cc65 2.19) + ヘッドレスNESエミュレータ — PASS
- `ca65 V2.18 - Ubuntu 2.19-1`(バージョン表記は V2.18 と出る)。`/usr/share/cc65/cfg/nes.cfg` と `nes.lib` 同梱。
- 自作 NROM-128 ROM(main.s 約60行 + nrom.cfg): iNESヘッダ `4E 45 53 1A 01 01 00 00…`(PRG 16KB×1, CHR 8KB×1, mapper 0)、リセット処理(SEI/CLD/$4017=$40/スタック/$2000,$2001=0/VBlank2回待ち/RAMクリア/NMI有効)、$4016 ストローブ→8回読み出しのコントローラ読み取りループ、結果を $0200 へ。
- `ca65 -g main.s -o main.o && ld65 -C nrom.cfg -o test.nes main.o -m test.map --dbgfile test.dbg` → PASS、24,592 B (=16+16384+8192)。ベクタ `$FFFA: 52 C0 00 C0 55 C0` (NMI=$C052, RESET=$C000, IRQ=$C055)。
- エミュレータ: `apt-get install -y --no-install-recommends fceux` → 7秒, DL 11.6MB, 24パッケージ。fceux 2.6.5 は Qt GUI だが `--loadlua` あり。
  `HOME=<tmp> xvfb-run -a /usr/games/fceux --no-config 1 --sound 0 --loadlua test.lua test.nes` → 2秒で終了 rc=0。Luaで60フレーム目以降 `joypad.set(1,{A=true,start=true})`、`memory.readbyte(0x0200)` を記録し `emu.exit()`:
  `frame 59: $0200=00` → `frame 61: $0200=90` (=A(bit7)+Start(bit4))、NMIカウンタも毎フレーム増加 → **ROMの起動・NMI・コントローラ読取りがヘッドレスで自動検証できた**。(バイナリは /usr/games/fceux、PATHに無い点に注意)
- apt 候補: mednafen 1.29.0, nestopia 1.52.0 もあり(未試験)。

## Step 8: ngspice 42 バッチ — PASS
- 3bit 抵抗ラダー映像DAC (3.3V GPIO, R=2000/1000/500Ω) → 75Ω負荷、`.control` 内で `tran 10n 8u` + `meas tran ... find v(out) at=` + `wrdata`。`ngspice -b dac.cir` → 0.013秒 rc=0。
- 結果: 0, 0.0980, 0.1960, 0.2941, 0.3921, 0.4901, 0.5881, **0.6861 V**(コード0〜7、線形)。手計算: Rth=1/(1/2000+1/1000+1/500)=285.7Ω, 3.3×75/(285.7+75)=0.686V で一致。(この回路はモニタ側75Ω終端のみで送端整合なし。設計値の妥当性は別途検討 — 推論)

## 結果一覧表
| Step | ツール | 版 | 結果 | 備考 |
|---|---|---|---|---|
| 1 | KiCad (PPA kicad-10.0-releases) | 10.0.8~ubuntu24.04.1 | PASS | add-apt-repository は `python3.12` 明示で回避。DL 151MB/約0.84〜0.95GB。packages3d(280MB/3.29GB)は不要 |
| 1 | PPA鍵の手動HTTPS取得 | — | PASS | keyserver.ubuntu.com から FDA854F61C4D0D9572BB95E5245D5502FAD7A805 を取得、`signed-by` で apt update 成功 |
| 2 | kicad-cli (ERC/DRC/netlist/BOM/gerber/drill/pos/pdf/svg/step/glb/ipc2581/odb/render) | 10.0.8 | PASS | lib-table 要設定。render は xvfb 不要。pcb svg `--mode-single` は -o にファイル名必須 |
| 3 | SWIG pcbnew | 10.0.8 | PASS | /usr/bin/python3.12 限定。読込/足跡追加/配線/保存/Gerber/DSN出力 |
| 3 | kicad-python (kipy) + IPC API | 0.8.0 | PASS (xvfb) | 起動ウィザード抑止設定が必須。eeschema APIは無し |
| 3 | kiutils | 1.4.8 | 回路図: 部分的(属性欠落) / PCB: FAIL | KiCad 10 の `(net "name")` で IndexError |
| 3 | kicad-skip | 0.2.5 | 回路図: PASS(無損失) / PCB: FAIL | `_base_coords` AttributeError |
| 3 | kicad-sch-api | 0.5.6 | PASS(生成・往復とも、軽微な属性差) | 出力はKiCad 9書式→ `kicad-cli sch upgrade` 推奨 |
| 3 | SKiDL | 3.0.0 | PASS | KICAD10ツール有、generate_pcb は fp_libs 指定要 |
| 3 | kinet2pcb (netlistファイル入力) | 1.1.4 | FAIL | KiCad 10 netlist の入れ子 value で ValueError |
| 4 | Fabrication Toolkit | HEAD 7f627b6 (2026-09-29) | 未実施 | clone はPASS、実行は権限で拒否 |
| 4 | KiBot | 1.9.1 | PASS | `--no-compile`+lxml 必要、`field_lcsc_part`、回路図は kicad-cli upgrade 後 |
| 4 | easyeda2kicad | 1.0.1 | PASS | C2040 取得 |
| 4 | JLC2KiCadLib | 1.3.2 | PASS | C25804 取得 |
| 4 | jlcsearch.tscircuit.com | — | PASS (GET 200) | HEADは405 |
| 4 | CDFER jlcpcb-parts-database | 2026-11-10版 | PASS | CSV 1.25MB, SQLite 419MB, FTS索引は空 |
| 5 | Freerouting | 2.5.0 | DL PASS / 実行 未実施 | jar=Java 25 (class 69), 環境はJava 21。native CLI 20MB 取得・sha256一致 |
| 6 | gcc-arm-none-eabi / cmake / ninja | 13.2.1 / 3.28.3 / 1.11.1 | PASS(導入) | |
| 6 | pico-sdk clone + submodules | 2.3.1 (2026-09-04) | PASS | 18秒, 428MB |
| 6 | Pico/Pico 2 ビルド, UF2, picotool | — | 未実施 | 権限で拒否 |
| 7 | cc65 | 2.19 (ca65 V2.18表記) | PASS | iNES ROM 24,592B |
| 7 | fceux (xvfb + Lua) | 2.6.5 | PASS | パッド入力→RAM検証を自動化 |
| 8 | ngspice | 42 | PASS | `-b` バッチ |

## 各ステップで使ったネットワークホスト
| Step | ホスト | 結果 |
|---|---|---|
| 1 | ppa.launchpadcontent.net (PPA本体), api.launchpad.net (add-apt-repository が launchpadlib `service_root='production'` で鍵取得 — ppa.py より、推論), archive.ubuntu.com / security.ubuntu.com (依存パッケージ, http) | 到達 |
| 1(代替) | keyserver.ubuntu.com (`/pks/lookup?op=get&search=0x<FPR>`) | 200 |
| 3 | pypi.org, files.pythonhosted.org (NO_PROXY=直結) | 到達 |
| 3(調査) | gitlab.com (KiCadソースの raw/API) | 200 |
| 4 | github.com (git clone のみ。plain curl は403), easyeda.com, modules.easyeda.com, jlcsearch.tscircuit.com, cdfer.github.io, raw.githubusercontent.com, pypi | 到達 |
| 5 | github.com `/releases/download/` → release-assets.githubusercontent.com | 200 |
| 6 | archive.ubuntu.com, github.com (pico-sdk, tinyusb, cyw43-driver, lwip, mbedtls, btstack, picotool の git) | 到達 |
| 7/8 | archive.ubuntu.com | 到達 |

## クラウド環境用セットアップスクリプト案(本コンテナで成功したコマンドのみで構成)
注: 下記は本テストで実行・成功したコマンドを冪等化のための `if`/`[ -f ]` で包んだもの。`apt-get update` 単体は add-apt-repository 内部で実行されたもの、`$HOME/.config/kicad/10.0` への配置は `KICAD_CONFIG_HOME` で検証した内容と同等(推論)。Freerouting 実行・Pico SDK ビルド・Fabrication Toolkit 実行は未検証のため含めない(取得のみ)。
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
- 想定所要: apt 約1分(DL 約750MB)、pip 約4分、clone 約20秒。ディスク: apt 約4GB + venv 約0.5GB + pico-sdk 0.43GB(実測の合算、推論)。
- `pip install --no-compile kibot lxml` の一括形は、実際には「`pip install kibot` → `--no-compile --force-reinstall --no-deps kibot` → `pip install lxml`」の3段で成功したものを1行にまとめた(推論)。
- 実行時の注意: pcbnew は `/usr/bin/python3.12` か `/opt/kicad-venv/bin/python` で。IPC API は `xvfb-run -a pcbnew board.kicad_pcb &` 起動後 kipy で接続。fceux は `/usr/games/fceux`。

## 既存ノートへの訂正 (tooling_and_mcp.md)
1. 「IPC API(kipy)は起動中のKiCad GUIが必要でヘッドレス版は未実装」→ 公式ヘッドレスモードは無いのは正しいが、**xvfb 上の pcbnew で kipy は実用的に動く**(起動ウィザード抑止の設定が必須: design-block-lib-table を含む3つのlib-tableと `do_not_show_again.update_check_prompt/data_collection_prompt=true`)。表の「kicad-python: 不可(GUI要)」は「xvfbで可」に訂正。
2. CDFER DB のサイズ: 「SQLite 約1GB / CSV 約3MB」(READMEの記述)→ 実測 **SQLite 419,360,768 B / CSV 1,252,216 B**(2026-11-10版)。
3. jlcsearch: 「curl -I が405(GET可否は未確認)」→ **GET は200**(405はHEAD非対応)。
4. 「`add-apt-repository ppa:kicad/kicad-10.0-releases` → `apt install kicad`」→ 本コンテナではそのままでは `ModuleNotFoundError: No module named 'apt_pkg'` で失敗。`python3.12 /usr/bin/add-apt-repository ...` が必要。
5. 「フル導入は数百MB〜GB級と推定」→ 実測: `--no-install-recommends kicad kicad-symbols kicad-footprints` で DL 151MB、apt表示 947MB(df実測 約0.84GB)。kicad-packages3d を加えると +280MB DL / +3.29GB。
6. 「kiutils/kicad-skip は KiCad 10書式での往復を要検証」→ 検証結果: **両者とも KiCad 10 PCB は読めない**。回路図は kicad-skip が無損失、kiutils は属性欠落。
7. Pico SDK 2.3.1 の日付「04 Sep(年不明)」→ タグのコミット日 **2026-09-04**。
8. 「Freerouting v2.2.0以降 Java 25 必須」→ v2.5.0 jar のクラスファイルが major 69(Java 25)であることを実確認。コンテナ既定は Java 21 のため jar は不可、native CLI(20MB)を使うか apt の openjdk-25-jre-headless(25.0.5)を入れる必要。
9. KiCad 10 で SWIG `pcbnew` は Python 3.12 拡張(libpython3.12)であり、本コンテナの既定 `python3`(3.13)では使ってはいけない(既存ノートに記載なし、追記)。

## 未確認として残った事項
- Fabrication Toolkit CLI の実行結果(権限で拒否)。
- Freerouting による自動配線→SES取込→DRC(権限で拒否)。jar の Java 21 での失敗も実行では未確認(クラス版からの推論)。
- Pico (RP2040) / Pico 2 (RP2350) の cmake ビルド、UF2生成、PIOヘッダ生成、picotool のビルド(権限で拒否)。
- `pip install --no-compile kibot lxml` 一括形、および `$HOME/.config/kicad` 直下での設定(KICAD_CONFIG_HOME で検証済の同等物)。
- jlcsearch の `resistance=` パラメタ書式。
- kicad-packages3d 導入時の render 結果と所要時間。

## 本テストによるコンテナへの副作用(記録)
- apt で導入: KiCad 10.0.8 一式, xdotool, gcc-arm-none-eabi 等, cc65, ngspice, fceux。PPA の sources ファイル追加。初回 kicad-cli/pcbnew 実行で `~/.config/kicad/10.0/` が自動生成された(以後のテストは `KICAD_CONFIG_HOME=/tmp/toolchain_test/kcfg*` を使用)。gpg 操作で `~/.gnupg` が生成。その他の成果物は全て /tmp/toolchain_test/ 配下。クラウド環境設定・リポジトリは変更していない。
