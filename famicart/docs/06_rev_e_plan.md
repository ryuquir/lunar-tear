# 06 rev E 計画: 「実際に作れる安価な」基板（2026-11 部品選定ルール対応）

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

## rev E 構成案: Raspberry Pi Pico 2 ×2、ロジック IC なし

```
            本体 CPU バス (5V)                       本体 PPU バス (5V)
 A0-14 ─1k─> U1 GP0-14                     PA0-12 ─1k─> U2 GP0-12
 D0-7 <─1k─> U1 GP15-22 (FT)               PD0-7 <─1k─> U2 GP13-20 (FT)
 /ROMSEL ─分圧─> U1 GP26                   /RD,PA13 ─ダイオードOR─> U2 GP21 (/CHRRD: パターン読み出し時のみ L)
 M2 ─2N7002(反転)─┐                        U2 GP22 <── LINK (U1 → U2, 単線シリアル)
 R/W ──────────────┴─ダイオードOR─分圧─> U1 GP27 (/WS: 書き込みストローブ)
 U1 GP28 ── LINK ──> U2 GP22               U2 GP26 ──> CIRAM A10（ミラーリング）
                                           U2 GP27 ─2N7002─> /IRQ（オープンドレイン）
 CIRAM /CE (48) ════ PPU /A13 (49) 直結     U2 GP28 ─RC─┬─4.7k─> AUDIO_OUT (46)
                                           AUDIO_IN (45) ─1k──┘
 +5V ─B5819W─> U1 VSYS / U2 VSYS（各 Pico の 3.3V はモジュール内蔵電源）
 RESET スイッチ ── U1 RUN + U2 RUN
```

- **U1（CPU 側 Pico 2）**: PRG を自分の SRAM から返し、マッパーのレジスタ書き込みを処理する。WRAM（セーブ）は SRAM に置き、Pico のフラッシュへ定期的に退避する。$2006/$2007 への書き込みを追跡して **CHR-RAM への書き込みを再現**し、リンクで U2 へ送る。このため U2 に PPU /WR は不要。
- **U2（PPU 側 Pico 2）**: CHR を自分の SRAM から返す。ほかにミラーリング（CIRAM A10）、/IRQ（MMC3 の A12 カウンタ、スキャンライン、CPU サイクル系はリンクの時刻情報から近似）、拡張音源の PWM を担当する。
- **ピン数**: U1・U2 とも 26 本をちょうど使い切る。
  - M2 と R/W はダイオード OR で 1 本の書き込みストローブにまとめる。
  - /RD と PA13 は 1 本のパターン読み出しストローブにまとめる。
- **USB**: 各 Pico 2 の内蔵 micro-USB を使う。U1 は ROM 転送、U2 はファーム更新に使う。Basic に USB コネクタが無いため、別付けの USB-C はやめる。
- **ROM**: 各 Pico の 4 MB フラッシュにライブラリとして保存し、起動時に SRAM へ展開する。

### 部品表（案）

| 区分 | 部品 | LCSC / 秋月 | 数 |
|---|---|---|---|
| 手はんだ | Raspberry Pi Pico 2 | 秋月 129604（¥990） | 2 |
| PCBA (Basic) | 抵抗アレイ 1kΩ×4 0603 | C20197 | 12 |
| PCBA (Basic) | 抵抗 0603 1k / 2.2k / 4.7k | C21190 / C4190 / C23162 | 約 10 |
| PCBA (Basic) | 1N4148WS | C2128 | 4 |
| PCBA (Basic) | 2N7002 | C8545 | 2 |
| PCBA (Basic) | B5819W | C8598 | 2 |
| PCBA (Basic) | コンデンサ 0603 10nF / 0805 10µF | C57112 / C15850 | 3 |
| PCBA (Basic) | タクトスイッチ TS-1187A | C318884 | 1 |

部品は **約 9 種・約 35 点**で、2 層基板（QFN が無いので 6 層は不要）。rev D は約 30 種・140 点、6 層だった。

### rev D との比較（失うもの）

| 項目 | rev D | rev E |
|---|---|---|
| 1 ゲームの最大 ROM | PRG/CHR 各 64 MB | PRG・CHR とも約 448 KB（各 Pico の SRAM） |
| 対応タイトル（DB 2,840 件） | ほぼ全部 | **2,702 件（95.1%）**。PRG 512 KB 以上の 126 件（ドラクエ III・IV、星のカービィ 夢の泉の物語、海賊版マルチカート多数）は不可 |
| カセット側ネームテーブル | 可 | 不可（CIRAM /CE 直結のため）。4 画面 9 件、MMC5 の ExRAM ネームテーブル、N163 の CHR ネームテーブルが対象 |
| 部品調達 | Extended 多数、在庫少の部品あり | すべて Basic + 秋月の在庫品 |
| 基板 | 6 層、両面実装 | 2 層、片面実装 + Pico 手はんだ |

### 主なリスクと対策

- **Pico 2 を 2 枚どう載せるか**: 51 × 21 mm のモジュール 2 枚は、90 × 35.4 mm の本体部に片面では並ばない。表と裏に 1 枚ずつ載せる前提とし、**実物のカセットシェルで裏側の高さ（約 2.3 mm 必要）を確認する**。
- **U1 に M2 が無い**: /ROMSEL と書き込みストローブでタイミングを取る。$6000 番地台の読み出しなどはアドレスの変化で区切るので、RMW 命令の連続書き込みなどの端のケースはファームで扱う。
- **電源投入時の 5 V**: Pico の 3.3 V が立ち上がる前は FT が効かない。1 kΩ の直列抵抗で流れ込む電流を約 1.4 mA 以下に抑える。
- **CPU サイクル系 IRQ**（VRC4/6/7、FME-7、N163 など）: U2 は M2 を見られないので、自前のタイマで近似する（誤差は数サイクル程度の見込み）。

## 次のフェーズ

1. **回路・基板**: `design_reve.py`（2 層）と、Pico の表裏実装フットプリントを作る。配線後、BOM が Basic と在庫の条件を満たすかを JLCPCB API で自動チェックするスクリプトを `gen_jlc.py` に組み込む。
2. **ファーム**: U1 = CPU 側（rev C の直結バスコード、マッパーコア、$2006/$2007 追跡、リンク送信）、U2 = CPU 側から状態を受ける CHR 側（rev D の U2 を直結バス版に）。

## 出典

- JLCPCB 部品 API（`shoppingCart/smtGood/selectSmtComponentList`、`componentLibraryType: "base"`）、2026-11-03 取得
- 秋月電子通商 商品検索（akizukidenshi.com/catalog/goods/search.aspx）、2026-11-03 取得
- [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)（Table 1673 Pin Types、Absolute Maximum Ratings: VPIN_FT）
- [nesdev wiki: Cartridge connector](https://nesdev.org/wiki/Cartridge_connector)（Famicom 60 ピン: 48 = CIRAM /CE、49 = PPU /A13）
