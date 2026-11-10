# ファームウェア・シミュレーション・テストROM・実機立ち上げ機材 (第2パス) — 2026-11-10時点

(作業中: 逐次追記)

## 1. Raspberry Pi Pico SDK / picotool / RP2350ステッピング

### Takeaway
Pico SDK最新は 2.3.1 (2026-09-04)、picotool最新は 2.3.1 (2026-09-05)。RP2350-E9(GPIO入力リーク)はA3ステッピングで修正済で、A4がデータシート上の「Production version」。

### Cited Findings
| 項目 | 内容 | 出典 |
|---|---|---|
| pico-sdk 2.3.1 | published_at 2026-09-04T22:38:41Z。バグ修正・RP2350ボード追加 | https://api.github.com/repos/raspberrypi/pico-sdk/releases |
| pico-sdk 2.3.0 | 2026-07-03。「RP2350's XIP cache can now be used as additional SRAM via `pico_use_xip_cache_as_ram()`」 | 同上 |
| pico-sdk 2.2.0 | 2025-07-29。「the workaround for erratum RP2350-E10」 | 同上 |
| pico-sdk 2.1.0 | 2024-11-25。「RP2350 A0/A1 silicon are no longer supported」 | 同上 |
| pico-sdk 2.0.0 | 2024-08-08。「adds support for the new RP2350 and for compiling RISC-V code」 | https://github.com/raspberrypi/pico-sdk/releases |
| picotool 2.3.1 | 2026-09-05、SDK 2.3.1対応のバグ修正 | https://api.github.com/repos/raspberrypi/picotool/releases |
| picotool 2.3.0 | 2026-07-03、`bdev`コマンド、`uf2 combine` | 同上 |
| picotool 2.2.0-a4 | 2025-08-14、「RP2350 A3 and A4 chip revision display」 | 同上 |

(暫定メモ: E9はA3で修正 — RP2350 datasheet build 01/10/2026 Appendix C.2.1 / D.5.1。A4=Production version (Table 7)。pioasmはSDK内ソースからビルド、picotoolはSDK版と同じタグをFetchContent。Wokwi: Free CI 50分/30日、セッション5分、Pro €20/seat 2000CI分、Pico2はArm1コアのみ・RP2350固有PIO命令なし・DMA16ch、Pico(RP2040)はDMAはPIO用のみ。rp2040js 1.4.1 2026-10-18 MIT pio.ts/dma.ts有。rp2040-pio-emulator 0.88.0 2026-08-28 Apache-2.0。MesenCE 2.2.0 2026-06-04 / 2.2.1 2026-06-05、--testRunner [lua] [rom] headless、emu.exit。FCEUX 2.7.0 2026-10-14、-lua。cc65 最新タグV2.19 2020-11-20)
(暫定メモ2: AccuracyCoin 147 pass/fail +5 DRAW, NROM, MIT, 「designed for an NTSC console with an RP2A03G CPU and RP2C02G PPU」 https://github.com/100thCoin/AccuracyCoin。240p Test Suite v0.23 2023-03-03 GPLv2+、UNROMで焼け、項目リストhelppages.txt。EverDrive N8 PRO Fami $159 krikzz.com/our-products/cartridges/n8-pro-fami.html (16MB ROM, Cyclone IV, USB)。cc65 VER 2.19、snapshot win zip 2026-11-08 (sourceforge)。asm6f v1.6_f03 2025-01-27。NESASM CE v3.6。llvm-mos-sdk NES: NROM/CNROM/UNROM/UNROM-512/MMC1/MMC3/GTROM/Action53。neslib (clbr) zlib。NROM PRG16/32K CHR8K mapper0。UxROM 74HC161+74HC32 mapper2。)
