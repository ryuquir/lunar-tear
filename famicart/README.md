# famicart — RP2040/RP2350 ファミコン・マルチマッパー・カートリッジ ファームウェア＋基板

ファミコン（NES）の公式・ライセンス品 2,233 タイトルで使われた 92 種のマッパーを調査し、そのうち 63 種（タイトル数ベース **96.0%**（2,143 本））をソフトウェアで再現する 1 チップ・カートリッジのファームウェアです。フラッシュに書き込んだ ROM 画像からマッパーを自動判別し、プロファイル指定で「MMC5 のバンク機能 + VRC7 音源」のような拡張 IC の組み合わせも可能にします。

> **重要な前提**: Seeed Studio XIAO RP2040 は GPIO が 11 本しかなく、単体ではカートリッジバス（最低 26 本）を駆動できません。理由と数値は [docs/01_feasibility.md](docs/01_feasibility.md) を参照。そのため **rev C 基板では基板直付けの RP2350B（GPIO 48 本）がバスを担当し、XIAO RP2040 は拡張音源コプロセッサ**として同居します（[docs/04_hardware.md](docs/04_hardware.md) の rev C 節）。rev A/B は Pico / Pico 2 モジュール 1 個の構成です。

## 状態（フェーズ 1・2 完了、フェーズ 3 = 実機検証 待ち）

| 項目 | 状態 |
|---|---|
| マッパー調査・集計（Mesen DB 由来） | 完了 → [docs/03_mapper_coverage.md](docs/03_mapper_coverage.md) |
| コア（バンク表・マッパー 63 種・ROM 判別・DB 2,840 件・プロファイル） | 実装済み、ホストテスト 864 チェック通過 |
| 拡張音源レジスタ・ルーター（組み合わせ機構） | 実装済み |
| 拡張音源の合成（VRC6/VRC7/MMC5/N163/5B/FDS、`src/core/audio/synth.c`） | 実装済み（6 音源とも発音をホストテストで確認、VRC7 は OPLL 近似）。rev C では XIAO 側で動作 |
| PIO バス・フロントエンド、2 コア処理、PWM 音声出力 | 実装済み・**実機未検証** |
| USB-CDC コマンド（INFO / RESET / BOOTSEL / LOAD / PROFILE）と転送ツール `tools/fcload.py` | 実装済み・**実機未検証** |
| Pico / Pico 2 / RP2350B / XIAO（コプロセッサ）向けビルド | 通過（Pico: text 120KB, BSS 249KB / RP2350B: text 106KB, BSS 512KB / XIAO audio: text 42KB） |
| 2 MCU 間 UART リンク（3 Mbaud、音源レジスタのストリーム） | 実装済み・**実機未検証** |
| 回路図・基板 rev B（Pico 2、KiCad 7、90×46.1 mm ファミコン実寸、USB-C・リセット付き、未接続 0・DRC 0）・ガーバー・JLCPCB 実装パッケージ | [hardware/](hardware/)、[hardware/jlcpcb/](hardware/jlcpcb/) |
| 回路図・基板 rev C（RP2350B + XIAO RP2040、USB 3 口、リセット端子 J2、未接続 0・DRC 0）・ガーバー・JLCPCB 実装パッケージ | [hardware/revc/](hardware/revc/) |
| 回路図・基板 rev D（実カセット型分離構成: RP2350B×2 マッパーチップ + PRG/CHR パラレル NOR 64 MB×2 + SRAM 512 KB×2、4 層）・ガーバー・JLCPCB 実装パッケージ | [hardware/revd/](hardware/revd/)、docs/04_hardware.md の rev D 節。**ファームのバンク出力層はフェーズ 4** |

## ビルド

```sh
# ホスト側ユニットテスト
cd famicart/test && make

# ファームウェア（FC_BOARD = pico | pico2 | rp2350b | xiao_audio | xiao_rp2040）
cd famicart && mkdir -p build && cd build
cmake -DPICO_SDK_PATH=/path/to/pico-sdk -DFC_BOARD=pico2 ..
make -j
# -> famicart.uf2 を BOOTSEL モードのドライブへコピー

# rev C 基板は 2 つ書く: 主 MCU（J3 を挿し SW2 を押しながら SW1 を離す）と XIAO（XIAO 自身の USB-C と BOOT ボタン）
cmake -S . -B build-rp2350b   -DFC_BOARD=rp2350b   && cmake --build build-rp2350b   # -> RP2350B へ
cmake -S . -B build-xiao_audio -DFC_BOARD=xiao_audio && cmake --build build-xiao_audio # -> XIAO RP2040 へ
```

## ROM の書き込み（自動判別）

```sh
# そのまま: ヘッダ → CRC32 DB → サイズ推定 の順で自動判別
python3 tools/rom2uf2.py game.nes -o game.uf2 --family rp2350

# マッパーを強制し、VRC7 音源を追加（MMC5 の機能 + VRC7 の音）
python3 tools/rom2uf2.py game.nes -o game.uf2 --mapper 5 --audio vrc7:exclusive --audio mmc5

# レジスタ窓が衝突する組み合わせは窓を移動（VRC6 のレジスタを $C000 へ）
python3 tools/rom2uf2.py game.nes -o game.uf2 --audio vrc6@0xC000
```

## 本体に挿したまま ROM を転送（USB-C）

```sh
pip install pyserial
python3 tools/fcload.py /dev/ttyACM0 info          # 判別結果・バス統計
python3 tools/fcload.py /dev/ttyACM0 load game.nes # 転送 → カートリッジ自動再起動 → 本体のリセットを押す
python3 tools/fcload.py /dev/ttyACM0 reset         # ソフトからカートリッジをリセット
python3 tools/fcload.py /dev/ttyACM0 bootsel       # ファーム更新用 UF2 モードへ
```

ROM はフラッシュ先頭から 256KB の位置（`FC_FLASH_ROM_SLOT`）に、48 バイトのプロファイル（256 バイト境界にパディング）＋画像の形で書き込まれます。ツールを介さず `.nes` を直接その位置に焼いた場合もヘッダ/DB で判別します。起動後、USB CDC（115200）に判別結果とバス統計が 2 秒ごとに出ます。

## データベースの再生成

```sh
python3 tools/gen_romdb.py   # data/MesenNesDB.txt -> src/core/romdb_gen.h, docs/03_mapper_coverage.md
```

## ドキュメント

- [01 実現可能性](docs/01_feasibility.md) — ピン数・タイミング・メモリの数値と結論
- [02 ファームウェア構成](docs/02_architecture.md) — 高速パス、マッパー IF、音源ルーター、判別フロー、既知の制約
- [03 マッパー集計](docs/03_mapper_coverage.md) — 92 種の本数・サブマッパー・代表基板・実装状況
- [04 ハードウェア](docs/04_hardware.md) — KiCad プロジェクト、基板寸法、GPIO 割当、部品表、音声ミックス回路

## 基板の再生成（KiCad 7 + Freerouting）

```sh
cd famicart/tools/pcb
python3 gen_sch.py && python3 route_pcb.py && python3 gen_bom.py && python3 gen_jlc.py            # rev B -> hardware/
FC_DESIGN=design_revc FC_HW_DIR=../../hardware/revc python3 gen_sch.py   # rev C -> hardware/revc/（route_pcb / gen_bom / gen_jlc も同じ環境変数で）
FC_DESIGN=design_revd FC_HW_DIR=../../hardware/revd python3 gen_sch.py   # rev D（4 層）-> hardware/revd/
```

## ロードマップ

1. **フェーズ 3**: 基板の試作・実機検証（ロジアナでタイミング確認）、配線の手直し、VRC7 音色の実機比較による校正、USB マスストレージからの ROM 選択、セーブ（バッテリ RAM）のフラッシュ退避
2. **フェーズ 4（rev D 向けファーム）**: `prg_map/chr_map` テーブルをバンク線出力に変換するコア 1 ループ、U1↔U2 PIO リンク、PPU 側の MMC2/MMC3/MMC5 検出、S29GL フラッシュ書き込み（USB 経由）、ROM ライブラリ選択メニュー
3. 未実装マッパー（海賊版マルチカート系）は対象外のまま

## ライセンス・出典

ファームウェアはリポジトリのライセンスに従います。`data/MesenNesDB.txt` は Mesen プロジェクト配布の生成データ（NesCartDB および NewRisingSun の NES 2.0 header database 由来）で、マッパー判別用のメタデータのみを利用しています。ゲーム ROM は含みません。
