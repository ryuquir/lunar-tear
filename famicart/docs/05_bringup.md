# 05 実機ブリングアップ手順（rev D）

目標は「実際のファミコンでゲームが動く」こと。基板到着後は以下の順で確認し、各段階でログ（USB の `INFO` 出力とロジアナ波形）を残す。

## 0. 用意するもの
- rev D 基板（JLCPCB 実装済み）＋ XIAO 不要。USB-C ケーブル 2 本、ファミコン本体（初代 or AV）、テスト用 ROM（ヘッダ付き .nes: NROM → MMC1 → UNROM → MMC3 → MMC5 の順）。
- ロジックアナライザ（≥ 100 MS/s、16 ch 以上）。プローブ先: M2(CM2)、/ROMSEL(CnROMSEL)、CA13/CA14、PRG_A13–A16、WRAM_nCE、nDRIVE、PPU /RD(PnRD)、PA10–PA13、CHR_A10–A13、CHR_SEL、CIRAM_A10、nIRQ。
- SWD デバッガ（任意、J5/J6）。

## 1. 基板単体（本体に挿さない、USB 給電）
1. J3 に USB を挿す → U1 が CDC として見える。`fcload.py <port> info` で `[famicart rev D / U1]` が出ること。J4 で U2 の UF2/CDC も確認。
2. ファームを両 MCU に書く（SW2/SW3 を押しながら電源投入 → UF2 ドライブ → `build-revd_prg/famicart.uf2` / `build-revd_chr/famicart.uf2`）。
3. `fcload.py <port> flashid` → PRG フラッシュの ID が `mfr 01 id 227E…`（Cypress/Infineon GL）で読めること。読めない場合: U5 のハンダ、ISOLATE（U1 GPIO47 = H のとき 541/245 が切れているか）、CRW→1G04→OE# の経路を当たる。
4. `fcload.py <port> bootbank` → 起動バンク書き込み＋ベリファイ `ok`。
5. `fcload.py <port> libadd nrom_test.nes` → `OK slot 0 crc …`。`lib` で一覧。
6. `wramdump` で F-RAM が読めること（初回は 0xFF または不定）。

## 2. 本体に挿して起動（NROM）
1. 本体電源 ON。U2 の LED が 1 秒点滅（loaded）になること。`INFO` の `bus : m2=…` が増え続けること（M2 取り込みが動いている）。
2. 画面が出ない場合の切り分け:
   - `resets` が増える／`rd` が 0 → ブートスタブが走っていない: ロジアナで電源投入直後の $FFFC/$FFFD 読み出しとその時の PRG_A13–25（すべて H = 起動バンク）を確認。
   - スタブは走るがゲームに入らない → $5F00/$5F01 の読み出しに対して nDRIVE が L になっているか（PIO の side-set）。
   - ゲームには入るが絵が壊れる → PPU 側: PA10–13 の変化から CHR_A10–13 が変わるまでの遅延（目標 < 60 ns）、CHR_SEL、CIRAM_A10 がミラーリング通りか。
3. タイミング測定（必須）: M2 ↑ から PRG バンク線確定までの遅延、/RD ↓ から CHR バンク線確定までの遅延を記録。300 ns を超える場合は `FC_SYS_CLOCK_KHZ` を上げる（250 MHz まで）か、コア 1 ループの命令数を削る。

## 3. マッパーを増やす
| 順 | ROM | 確認すること |
|---|---|---|
| 1 | NROM（CHR ROM） | 起動、背景、スプライト |
| 2 | UNROM（CHR RAM） | CHR RAM 書き込み（PnWR→U8 /WE）、バンク切替後の即時反映（`STA $8000` → 次の命令取り込みまでに PRG_A13–16 が変わる） |
| 3 | MMC1 | 5 回連続書き込みの取りこぼし無し（`INFO` の `wr` とゲームの挙動）、WRAM セーブ（電源を切って再投入し `wramdump` で残っていること） |
| 4 | MMC3 | IRQ（画面分割）: ロジアナで PA12 ↑ の計数と nIRQ_B のタイミング、/IRQ が本体に届くこと（U27 1G07） |
| 5 | MMC2（パンチアウト） | $FD/$FE ラッチ: タイルフェッチの直後に CHR_A12 相当が切り替わる |
| 6 | MMC5 | スキャンライン IRQ（$5204 の in-frame ビット = U2→U1 同期）、WRAM 32/64 KB、拡張音源 |
| 7 | VRC6/VRC7/N163/5B | 拡張音源（端子 46 の波形）、プロファイルで MMC5 + VRC7 の横断 |

## 4. 既知の落とし穴
- 本体の電源投入時に U1/U2 が起動する前の数 ms はブートスタブが待つので、**本体 RESET を押す必要はない**はず。押さないと起動しない場合はスタブ／$5F00 応答の問題。
- `libadd` は必ず本体から抜いて行う（ISOLATE 中にバスを駆動するため）。
- 4 層基板なので内層の GND/3V3 プレーン切れは無いが、QFN-80 の露出パッドのハンダ不良（熱）があると U1/U2 がリセットを繰り返す。LED の点滅周期で判別。
- AV ファミコンは本体の /IRQ プルアップが弱い個体がある。IRQ が効かないときは R5（10 kΩ → 4.7 kΩ）。
