# 02. ファームウェア構成

```
famicart/
├── src/core/            移植可能なコア（ホスト PC でも RP2040 でも同じコードが動く）
│   ├── cart.[ch]        カートリッジ状態・高速パス用テーブル・バンク設定ヘルパー
│   ├── mapper.[ch]      マッパーインターフェースと登録表（63 種）
│   ├── mappers/*.c      マッパー実装（メーカー系ごとに分割）
│   ├── rom.[ch]         iNES / NES 2.0 解析、CRC32、DB 検索、ヘッダ無し推定
│   ├── romdb_gen.h      生成物: CRC32 → マッパー等（2,840 件、約 45KB）
│   ├── cartload.[ch]    ROM 画像 → SRAM プール配置 → マッパー接続 → 音源構成
│   ├── profile.[ch]     カートリッジ・プロファイル（上書き設定、音源の組み合わせ）
│   └── audio/expaudio.* 拡張音源レジスタ・ルーター / audio/synth.c 6 音源の合成コアとミキサー
├── src/pico/            RP2040/RP2350 依存部
│   ├── fc_bus.pio       CPU/PPU バス取り込み・応答の PIO プログラム
│   ├── bus.c            コア 0 割り込み（CPU バス）、コア 1 ループ（PPU バス）
│   ├── audio_out.c      PWM + DMA リングバッファ出力
│   ├── romslot.c        フラッシュ ROM スロットの読み取り
│   ├── usb_cmd.c        USB-CDC コマンド（INFO / RESET / BOOTSEL / LOAD / PROFILE）
│   └── board_*.h        ピン割当
├── tools/gen_romdb.py   Mesen DB → romdb_gen.h / docs/03_mapper_coverage.md
├── tools/rom2uf2.py     .nes → UF2（プロファイル付き）
└── test/                ホスト側ユニットテスト（858 チェック）
```

## 高速パス（バス応答で毎サイクル実行される部分）

```c
CPU read  A ($4020-$FFFF): p = prg_map[A>>13];  p ? p[A & 0x1FFF] : mapper->read()
CPU write A              : w = prg_wmap[A>>13]; w ? w[A & 0x1FFF] = v : mapper->write()
PPU read  A ($0000-$1FFF): chr_map[A>>10][A & 0x3FF]
PPU read  A ($2000-$2FFF): nt_map[(A>>10)&3] ? それ : 本体 CIRAM（CIRAM A10 を nt_ciram_a10[] で駆動）
```

- PRG は 8KB、CHR は 1KB 粒度のポインタ表。バンク切替はポインタの差し替え（32 ビット書き込み 1 回）なので PPU 側コアとの間で整合性問題が起きない。
- マッパー固有の処理はフック（`ppu_addr` = A12 エッジや MMC2 ラッチ、`cpu_cycle` = サイクルカウンタ IRQ、`read` = $4020–$7FFF の低位レジスタ読み出し）として必要なマッパーだけが有効化する。
- MMC5 の拡張属性モードなど「テーブル参照の結果を差し替える」必要がある場合は `ppu_override` ポインタで 1 バイト差し替える。

## ROM 自動判別の流れ（`rom_inspect`）

1. フラッシュ ROM スロット先頭にプロファイル（`FCCP` マジック + CRC）があれば読む。無ければ画像のみとみなす。
2. `NES\x1a` があれば iNES / NES 2.0 として解析（NES 2.0 ではサブマッパー、PRG/CHR の MSB、RAM サイズ指数、PAL 判定を使用。iNES で bytes 12–15 が汚れていれば上位マッパーニブルを無視）。
3. PRG+CHR の CRC32 を計算し、内蔵 DB に一致があれば **DB を正**としてマッパー・サブマッパー・ミラーリング・バッテリ・RAM サイズを上書き（ヘッダの誤りを修正）。
4. ヘッダ無し画像は全体 CRC32 で DB を引き、無ければサイズから推定（16/32KB → NROM、40KB → NROM-256、64KB → CNROM、128KB → UxROM、256KB → MMC3、それ以外 16KB 単位 → MMC1）。
5. プロファイルの上書き（`--mapper` 等）があればそれを最優先。

## マッパーと拡張音源の分離（「VRC7 音源 + MMC5 機能」の実現方法）

- マッパー = バンク切替・IRQ・ミラーリング。音源チップ = レジスタ窓 + 合成。
- すべての CPU 書き込みはまず `expaudio_cpu_write()` を通る。プロファイルで有効化された音源チップが自分のレジスタ範囲（VRC7 なら $9010/$9030）を捕捉する。`exclusive` 指定ならマッパーには渡さない。
- 衝突する場合（例: MMC3 + VRC6、MMC3 の $8000–$9FFF と VRC6 の $9000–$9003）は `base` でレジスタ窓を移動できる（`--audio vrc6@0xC000`）。MMC5 + VRC7 は MMC5 側で $9010/$9030 が ROM 領域なので無衝突。
- 各チップの合成（VRC6 矩形×2+鋸、VRC7 OPLL 2-op FM 6ch（パッチ ROM 15 音色＋リズム無し、エンベロープ・AM/VIB・KSL を近似）、MMC5 矩形×2+PCM、N163 波形メモリ 8ch、5B PSG 3ch（トーン＋ノイズ＋エンベロープ）、FDS 波形＋変調）は `synth.c` の `expaudio_render()` が 1 サンプルずつミックスし、`expaudio_chip_volume()` でチップごとの音量を掛けてクリップする。出力は PWM（4× ホールド・アップサンプリング）→ 2 段 RC フィルタ → カートリッジ端子 46 へ本体音声（45）と抵抗加算。
- rev C 基板では主 MCU（RP2350B）はレジスタ書き込みを UART フレーム（`audio_link.c`）で XIAO RP2040 に転送するだけで、合成は XIAO 側 `src/xiao_audio/main.c` が同じ `expaudio_apply()` → `expaudio_render()` で行う。

## バス・フロントエンド（`src/pico`）

- **PIO（CPU）**: M2 立ち上がりで CTRL（R/W, /ROMSEL）→ アドレス上位（A8–14）→ 下位（A0–7）の順に 8 ビットポートから 3 回取り込み、RX FIFO へ 24 ビット語を push。TX FIFO からの応答語（bit0 = データ駆動、bit1 = 書き込みデータ取り込み）に従い、M2 立ち下がりまでデータを駆動、または立ち下がりでデータを取り込む。
- **PIO（PPU）**: /PPUACC（/RD AND /WR）立ち下がりで同様に 16 ビット語を push。
- **コア 0**: PIO IRQ（最高優先度、SRAM 常駐）で CPU バス語を処理。残り時間でメインループ（音源合成・USB ログ）。
- **コア 1**: PPU バス専用のブロッキングループ。CIRAM A10 / CIRAM /CE を SIO で直接駆動。
- **/IRQ**: 74LVC1G07 オープンドレインバッファ経由（GPIO Low でアサート）。

## USB 経由の ROM 転送（`usb_cmd.c` / `tools/fcload.py`）

1. ホストが `LOAD <bytes> <crc32>` を送る → ファームは `READY` を返し、バス処理（PIO・コア 1）を停止する（フラッシュ書き込み中は XIP が使えないため。本体側はこの時点でバスがオープンになり、ゲームは止まる）。
2. 4 KB セクタ単位で受信・消去・書き込み。先頭 256 B のプロファイルは保持（無効なら既定値を書く）。
3. 受信完了後に CRC32 を照合して `OK` を返し、ウォッチドッグで再起動 → 新 ROM を判別して起動。**本体のリセットボタンを押す**と新しいゲームが始まる。
4. `PROFILE <hex>` でプロファイルのみ差し替え（マッパー強制・音源構成の変更）。`RESET` / `BOOTSEL` は再起動／UF2 モード。

## 既知の制約・未検証事項（正直に）

- 実機未検証。タイミング見積りは `docs/01_feasibility.md` の通りで、CPU 読み出しの余裕が約 ±50 ns しかない。
- CIRAM A10 / /CE は RP2040 がデコード後に駆動するため、本体 VRAM のアクセス時間が約 80 ns 短くなる。問題が出る場合は 74LVC153 でハードウェアミラーリングを組む案を `docs/04_hardware.md` に記載。
- MMC5 の縦分割（$5200–$5202）は未実装。拡張属性と 8x16 スプライト時の CHR セット切替はフェッチ数カウント方式で実装（実機 MMC5 と同方式）。
- Jaleco の uPD7756 音声サンプル、Bandai の Datach バーコード、Family BASIC キーボード等の周辺機能は対象外。
