# famicart — RP2040/RP2350 ファミコン・マルチマッパー・カートリッジ ファームウェア

ファミコン（NES）の公式・ライセンス品 2,233 タイトルで使われた 92 種のマッパーを調査し、そのうち 63 種（タイトル数ベース **96.0%**（2,143 本））をソフトウェアで再現する 1 チップ・カートリッジのファームウェアです。フラッシュに書き込んだ ROM 画像からマッパーを自動判別し、プロファイル指定で「MMC5 のバンク機能 + VRC7 音源」のような拡張 IC の組み合わせも可能にします。

> **重要な前提**: Seeed Studio XIAO RP2040 は GPIO が 11 本しかなく、カートリッジバス（最低 26 本）を駆動できません。実機で動かすには Raspberry Pi Pico / Pico 2 または自作 RP2350 基板を使ってください。理由と数値は [docs/01_feasibility.md](docs/01_feasibility.md) を参照。XIAO 向けには同じファームウェアの「バス無し版」（ROM 判別・音源合成・USB ログ）がビルドできます。

## 状態（フェーズ 1 完了）

| 項目 | 状態 |
|---|---|
| マッパー調査・集計（Mesen DB 由来） | 完了 → [docs/03_mapper_coverage.md](docs/03_mapper_coverage.md) |
| コア（バンク表・マッパー 63 種・ROM 判別・DB 2,840 件・プロファイル） | 実装済み、ホストテスト 858 チェック通過 |
| 拡張音源レジスタ・ルーター（組み合わせ機構） | 実装済み |
| 拡張音源の合成（VRC6/VRC7/MMC5/N163/5B/FDS） | **フェーズ 2**（レジスタは捕捉済み、`expaudio_render()` は無音） |
| PIO バス・フロントエンド、2 コア処理、PWM 音声出力 | 実装済み・**実機未検証** |
| USB-CDC コマンド（INFO / RESET / BOOTSEL / LOAD / PROFILE）と転送ツール `tools/fcload.py` | 実装済み・**実機未検証** |
| Pico / Pico 2 / XIAO 向けビルド | 通過（Pico: text 93KB, BSS 254KB） |
| 回路図・基板 rev B（KiCad 7、90×46.1 mm ファミコン実寸、USB-C・リセット付き、自動配線 未接続 0・DRC 違反 0）・ガーバー・BOM | [hardware/](hardware/) と [docs/04_hardware.md](docs/04_hardware.md) |

## ビルド

```sh
# ホスト側ユニットテスト
cd famicart/test && make

# ファームウェア（pico | pico2 | xiao_rp2040）
cd famicart && mkdir -p build && cd build
cmake -DPICO_SDK_PATH=/path/to/pico-sdk -DFC_BOARD=pico2 ..
make -j
# -> famicart.uf2 を BOOTSEL モードのドライブへコピー
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

## ロードマップ

1. **フェーズ 2**: 拡張音源合成コア（VRC7 OPLL を含む）、ミキサー、音量校正
2. **フェーズ 3**: 基板の試作・実機検証（ロジアナでタイミング確認）、配線の手直し、USB マスストレージからの ROM 選択、セーブ（バッテリ RAM）のフラッシュ退避
3. 未実装マッパー（海賊版マルチカート系）は対象外のまま

## ライセンス・出典

ファームウェアはリポジトリのライセンスに従います。`data/MesenNesDB.txt` は Mesen プロジェクト配布の生成データ（NesCartDB および NewRisingSun の NES 2.0 header database 由来）で、マッパー判別用のメタデータのみを利用しています。ゲーム ROM は含みません。
