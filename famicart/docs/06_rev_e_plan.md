# 06 rev E: 「実際に作れる安価な」基板（2026-11 部品選定ルール対応）

## 部品選定・実装ルール（ユーザー指定）

- 実装は JLCPCB、**Basic Parts のみ**。LCSC に十分な在庫があるもの。
- 手はんだ部品は**秋月電子で在庫があるもの**。小さい部品は PCBA に任せる。
- 特殊・調達しにくい部品は避ける。部品の種類と点数を減らす。

rev D（RP2350B 直付け ×2、1 Gbit パラレル NOR ×2、F-RAM、SRAM、74LVC 系、USB-C、水晶、インダクタ、6 層）は、主要部品のほぼすべてが Extended Parts で、QFN-80 は手はんだも不可。**このルールを満たさない**ので、rev E として構成を作り直す。

## 調査結果（2026-11-03）

### JLCPCB Basic Parts（API `componentLibraryType: "base"` で確認）

| 分野 | Basic にあるもの |
|---|---|
| MCU | なし（RP2040 / RP2350 / STM32 / CH32 / GD32 / ESP32 すべて 0） |
| ロジック IC | 74HC14D（C5605）と 74HC595D（C5947）のみ。74HC/74HCT/74LVC の 245・541・139・138・00・08・32・04・157・573 と 1G 系はすべて 0 |
| メモリ | W25Q128JVSIQ（C97521、QSPI）のみ。パラレル NOR・SRAM・EEPROM は 0 |
| コネクタ | USB・Type-C・ピンヘッダとも 0 |
| 使える部品 | 抵抗・抵抗アレイ（4D03 1k = C20197 ほか）、コンデンサ、AMS1117-3.3（C6186）、XC6206（C5446）、ショットキー B5819W（C8598）/ SS14、1N4148WS（C2128）、2N7002（C8545）、AO3400/3401、LED、タクトスイッチ TS-1187A（C318884）、12 MHz 水晶 X322512MSB4SI（C9002） |

→ **バスバッファもメモリも PCBA に載せられない**。MCU は秋月のモジュールを手はんだし、本体バスに**直結**する以外にない。

### 秋月電子（akizukidenshi.com 検索、2026-11-03 時点）

| 品名 | 通販コード | 価格 | 在庫 |
|---|---|---|---|
| Raspberry Pi Pico 2（RP2350A） | 129604 | ¥990 | 在庫あり（1503） |
| Raspberry Pi Pico（RP2040） | 116132 | ¥800 | 在庫あり（1648） |
| Seeed XIAO RP2350 | 129619 | ¥1,100 | 在庫あり（313） |
| ピンヘッダー 1×40 | 100167 | ¥35 | 在庫あり |
| RP2350B 搭載モジュール（GPIO 48 本） | — | — | **取り扱いなし**（チップ単体のみ） |

### RP2350 の 5 V トレラント（公式データシート Table 1673 / 絶対最大定格）

- Bank 0 の GPIO（Pico 2 では GP0〜GP22）は **Fault Tolerant**: IOVDD = 3.3 V が加わっていれば **5.5 V まで**入力可。無給電時は 3.63 V まで。
- **GP26〜GP28 は ADC 兼用で FT ではない**（IOVDD + 0.5 V まで）。
- → 本体の 5 V 信号は GP0〜22 に直結できる（電源投入時の保護として 1 kΩ 直列抵抗を入れる）。GP26〜28 は出力か、分圧した入力に使う。

### ファミコン端子（nesdev Cartridge connector）

- **49 番 = PPU /A13、48 番 = CIRAM /CE**。多くの実カセットと同じく、この 2 本を基板上で直結すれば、ネームテーブル用 VRAM の選択に MCU のピンも部品も要らない。

## rev E 確定構成: Pico 2 ×2 ＋ XIAO RP2350 ×1（2026-11-07）

対象は**市販（公式ライセンス）のファミコン カセット全タイトル**。MMC5 の拡張機能（ExRAM ネームテーブル、フィルモード、拡張アトリビュート、スキャンライン IRQ、分割画面、拡張音源）まで含めて動かすことを前提にした。

```
              本体 CPU バス (5V)                                本体 PPU バス (5V)
 CPU_A0-14 ─1k─> U1 GP0-14                          PPU_A0-13 ─1k─> U2 GP0-13
 CPU_D0-7 <─1k─> U1 GP15-22 (FT)                    PPU_D0-7 <─1k─> U2 GP14-21 (FT)
 /ROMSEL ─1k/2.2k 分圧─> U1 GP26                    PPU /RD ─1k/2.2k 分圧─> U2 GP26
 M2 ─2N7002 反転─┐                                  U2 GP22 ──> CIRAM /CE（PIO で A10/A11/A13 から即時生成）
 R/W ────────────┴─ダイオード OR─分圧─> U1 GP27     U2 GP27 ──> CIRAM A10
   (/WS = 書き込みストローブ)                         PPU /A13 ─100k─> CIRAM /CE（U2 起動前の既定値）
 CPU_D0-7 に 100k プル（$4C）: 起動・ソフトリセット時に本体 CPU を JMP $4C4C で待機させる

 U3 XIAO RP2350:  D0 = LINK, D1 = 拡張音源 PWM ─RC─> AUDIO_OUT, D2 = /IRQ（2N7002 オープンドレイン）,
                  D3 = M2（1k）, D4/D5 = PA12/PA13, D6 = /RD   → MMC3・VRC・FME-7・MMC5 の IRQ を正確なタイミングで生成
 LINK: U1・U2・U3 の 3 点を 1k 経由で 1 本に。U1 が親の半二重シリアル。
 電源: 本体 +5V ─B5819W─> 各モジュール（VSYS / 5V）。モジュール内蔵の 3.3 V を使う。
 リセット: SW1 と配線パッド（RUN/GND）で U1・U2 を同時にリセット → ゲームが最初から始まる。
```

### 主な仕組み

- **ROM 容量**: 各 Pico 2 の SRAM（約 448 KB）を作業領域、4 MB フラッシュを本体にする。市販ソフトの最大（PRG 2 MB・CHR 1 MB）まで収まる。SRAM に入らない約 70 本は、バンク切り替えの書き込みを合図に先読みし、間に合わないときはフラッシュから直接返す（試作で実測が必要）。
- **MMC5 / 4 画面**: U2 が CIRAM /CE をネームテーブル 4 枚ごとに切り替え、カセット側のネームテーブル（ExRAM、フィル、4 画面用 RAM）は U2 が直接返す。PIO が A10/A11/A13 を見て 1 命令の表引きで /CE と A10 を出すので、遅れは数十 ns。
- **CHR-RAM への書き込み**: U1 が CPU からの $2006/$2007 書き込みを追跡して再現し、LINK で U2 に送る（PPU /WR は配線しない）。
- **IRQ**: U3 が M2・PA12・PA13・/RD を直接見て数える。MMC5 のスキャンライン検出もここで行い、$5204 の状態は LINK で U1 へ返す。
- **起動とソフトリセット**: MCU が応答しない間、データバスは 100 kΩ のプルで $4C になる。本体 CPU は「JMP $4C4C」で待ち、U1 の準備ができると $4C4C に「JMP ($FFFC)」を返してゲームを最初から始める。100 kΩ は通常動作中のオープンバス（前の値の保持）には影響しない。

### 基板（hardware/reve/）

- **2 層**、90 × 46.1 mm、トラック/クリアランス 0.15 mm、ビア 0.5/0.25 mm（JLC 標準仕様内）。
- **配線結果: 未接続 0、DRC エラー 0**（トラック 1475 本、ビア 175 個。警告 47 件は KiCad 標準ライブラリ照合とシルク文字のみ）。
- PCBA 部品はすべて表面（Economic 片面実装）。U1 と U3 は表面、U2 は裏面に手はんだ。USB 端子は U1 が基板左端、U2 が右端、XIAO（USB-C）が上端に出る。

### 部品表（`hardware/reve/jlcpcb/`、JLCPCB API で Basic・在庫を自動確認済み）

| 部品 | LCSC | 区分 | 数 |
|---|---|---|---|
| 抵抗アレイ 1kΩ×4 0603 | C20197 | Basic | 12 |
| 抵抗 100kΩ 0603 | C25803 | Basic | 10 |
| 抵抗 2.2kΩ 0603 | C4190 | Basic | 7 |
| 抵抗 1kΩ 0603 | C21190 | Basic | 6 |
| B5819W | C8598 | Basic | 3 |
| 2N7002 | C8545 | Basic | 2 |
| 1N4148WS | C2128 | Basic | 2 |
| コンデンサ 10nF 0603 | C57112 | Basic | 2 |
| コンデンサ 10µF 0805 | C15850 | Basic | 1 |
| タクトスイッチ TS-1187A | C318884 | Basic | 1 |
| Raspberry Pi Pico 2 | 秋月 129604（¥990） | 手はんだ | 2 |
| Seeed XIAO RP2350 | 秋月 129619（¥1,100） | 手はんだ | 1 |

PCBA は **10 種・46 点**、手はんだはモジュール 3 個だけ。

### 残るリスク

- **シェルの厚み**: 裏面の Pico 2（約 2.3 mm）が収まるか、実物のカセットシェルで確認する。
- **フラッシュ直読みの速さ**: SRAM に入らない約 70 本で使う経路。試作で CPU の読み取り期限（約 450 ns）に間に合うかを測る。
- **CIRAM /CE を MCU が出す遅れ**: PIO の表引きで数十 ns の見込み。ロジアナで確認する。
- **ファーム**: rev E 用に 3 つのファーム（U1・U2・U3）と、市販タイトルで使われる残りのマッパー（約 29 種）の実装が必要（次のフェーズ）。

## 出典

- JLCPCB 部品 API（`shoppingCart/smtGood/selectSmtComponentList`、`componentLibraryType: "base"`）、2026-11-03 取得
- 秋月電子通商 商品検索（akizukidenshi.com/catalog/goods/search.aspx）、2026-11-03 取得
- [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)（Table 1673 Pin Types、Absolute Maximum Ratings: VPIN_FT）
- [nesdev wiki: Cartridge connector](https://nesdev.org/wiki/Cartridge_connector)（Famicom 60 ピン: 48 = CIRAM /CE、49 = PPU /A13）
