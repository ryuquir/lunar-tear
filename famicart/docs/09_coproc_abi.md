# 09 コプロセッサ ABI v1（rev F・S0 段階）

FC のゲームから rev F の 2 つのコプロセッサを呼び出すための取り決め。ロードマップは [08](08_sfc_coprocessor_roadmap.md)。

> **rev G との関係（2026-11-10）**: この文書は rev F（U4・U5 が必ず載る構成）の版 1 で、実装とテストがあるのはこの版だけ。rev G では次の点が変わるので**版 2 が必要**になる。版 2 はまだ書いていない（設計の前提は [12](12_rev_g_plan.md) の「拡張チップの受け持ちと組み合わせ」）。
>
> | 項目 | 版 1（rev F） | 版 2（rev G、未作成） |
> |---|---|---|
> | 窓に答えるマイコン | U4（必ず載る） | U1 が窓の写し（1 KB）を持って答える。U4 は任意 |
> | コマンドの実行先 | U4・U5 | 既定はハブ（U6）。SA-1 は U4 または U1、Super FX は U5 または U2 |
> | 結果の戻し方 | U4 が自分でバスに出す | ハブが LINK の返信枠で U1 の写しを書き換える（遅れ 3〜4 µs の見込み、未測定） |
> | レジスタの配置 | 固定の 1 KB | 1 KB の窓をバンクで切り替える（チップごとの元の配置は入りきらない） |
> | 絵の受け渡し | U5 が CHR の枠に直接答える | U5、または PLINK 経由で U2 |
>
> 版 1 のコマンド番号と引数の並びは版 2 でもそのまま使えるようにする予定（STATUS の bit3-0 で版数を見分ける）。

## 定義

- **U4（CPU 側コプロセッサ）**: CPU バスに U1 と並列につながる Pico 2。窓 $5800-$5BEF を自分で読み書きさせる。計算・メモリ操作（将来は SA-1・DSP-n・展開回路）。
- **U5（PPU 側コプロセッサ）**: PPU バスに U2 と並列につながる Pico 2。プロファイルで指定した CHR の 1 KB 枠を自分で PPU に返し、そこへ絵を描く（将来は Super FX・Cx4）。
- **有効にする方法**: カートリッジのプロファイル（`tools/rom2uf2.py --coproc cpu|ppu|both --coproc-chr 0xF0 --coproc-base 0x5800`）。マッパーは何でもよく、MMC3 + コプロセッサのように組み合わせられる。プロファイルで有効にしないゲームでは U4・U5 は何もしない（rev E と同じ動作）。

## 窓の配置（基準 $5800、プロファイルで移動可）

| アドレス | 読み書き | 内容 | 応答するマイコン |
|---|---|---|---|
| $5800 | 書き | CMD（書くと実行開始、STATUS の busy が立つ） | U4 |
| $5801 | 読み | STATUS: bit7 busy、bit6 error、bit3-0 ABI 版数（=1） | U4 |
| $5802-$580F | 読み書き | 引数・結果（リトルエンディアン） | U4 |
| $5810-$5BEF | 読み書き | 共有 RAM 992 バイト（いつでも読み書き可） | U4 |
| $5BF0 | 書き | PPU 側 CMD | U5（U1 が中継） |
| $5BF1-$5BFE | 書き | PPU 側の引数 | U5（U1 が中継） |
| $5BFF | 読み | PPU 側 STATUS: bit7 busy | U1（U5 に問い合わせた値） |

- $5800 台は MMC5 のレジスタ（$5000-$5206）と ExRAM（$5C00-$5FFF）の間の空き。N163（$4800-$5FFF）と組み合わせるときは `--coproc-base` で $6000 台などへ移す。
- U1 は窓の中では（$5BFF 以外）バスを駆動しない。U2 は U5 の CHR 枠を駆動しない。間違って両方が出しても 1 kΩ 越しなので壊れない。

## CPU 側コマンド（U4）

| CMD | 名前 | 引数 → 結果 |
|---|---|---|
| $01 | MUL16 | a16 (+0) × b16 (+2) → 32 ビット (+4)。+8 bit0 = 1 で符号付き |
| $02 | DIV32 | u32 (+0) ÷ u16 (+4) → 商 32 (+6)、余り 16 (+10)。0 除算は error |
| $03 | MEMSET | 共有 RAM の off16 (+0) から len16 (+2) バイトを値 (+4) で埋める |
| $04 | MEMCPY | 共有 RAM 内で dst16 (+0) ← src16 (+2)、len16 (+4)。重なり可 |
| $05 | SINCOS | 角度 (+0、256 で 1 周) → sin (+2)、cos (+4)。s1.14 固定小数点 |
| $06 | ROT2D | (x16 +0, y16 +2) を角度 (+4) 回転 → x (+6)、y (+8)（符号付き） |

引数の位置は $5802 からの相対（+0 = $5802）。

## PPU 側コマンド（U5）

U5 の CHR 枠を **128 × 128 ドット・4 色のビットマップ**として扱う（16 × 16 タイル、タイル n は枠の先頭から n × 16 バイト、FC の 2 プレーン形式）。8 枠（8 KB）持たせると 2 画面ぶんになり、ダブルバッファにできる。

| CMD | 名前 | 引数（$5BF1 から） |
|---|---|---|
| $01 | CLEAR | 色 (0-3) |
| $02 | PLOT | x, y, 色 |
| $03 | LINE | x0, y0, x1, y1, 色 |
| $04 | RECT | x, y, 幅, 高さ, 色（塗りつぶし） |
| $05 | SELECT | 描画先バッファ (0/1) |

CPU 側は BG のネームテーブルに一度だけタイル番号 0-255 を並べておけば、あとは描くだけで画面が変わる。

## 使い方の例（ca65）

```asm
COP      = $5800
COP_ST   = COP+1
COP_ARG  = COP+2
PPU_CMD  = COP+$3F0
PPU_ARG  = COP+$3F1
PPU_ST   = COP+$3FF

        ; 1234 * 5678
        lda #<1234
        sta COP_ARG+0
        lda #>1234
        sta COP_ARG+1
        lda #<5678
        sta COP_ARG+2
        lda #>5678
        sta COP_ARG+3
        lda #0
        sta COP_ARG+8          ; unsigned
        lda #$01
        sta COP                ; MUL16
@wait:  bit COP_ST
        bmi @wait              ; busy
        lda COP_ARG+4          ; result, low byte

        ; draw a line (0,0)-(127,127) in color 3
@wait2: bit PPU_ST
        bmi @wait2
        lda #0
        sta PPU_ARG+0
        sta PPU_ARG+1
        lda #127
        sta PPU_ARG+2
        sta PPU_ARG+3
        lda #3
        sta PPU_ARG+4
        lda #$03
        sta PPU_CMD            ; LINE
```

## 実装

- 移植可能なコア: `src/core/coproc/`（`cop_abi.h` 取り決め、`cop_cpu.c` CPU 側、`cop_ppu.c` 描画）。ホストテスト `test/tm_coproc.c`。
- ファーム: `src/reve_cop/main_cpu.c`（U4、`-DFC_BOARD=reve_cop_cpu`）、`src/reve_cop/main_ppu.c`（U5、`-DFC_BOARD=reve_cop_ppu`）。U1/U2 の対応は `src/reve_cpu/main.c`・`src/reve_ppu/main.c`。
- 次（S1 以降）: このコマンド表に S-DD1 展開、SPC7110 の乗除算、DSP-1 の投影コマンド、GSU 命令列の実行を足していく。
