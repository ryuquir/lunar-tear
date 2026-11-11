# JAMMA インターフェース（56ピン配列・寸法・電源・映像・音声・入力・コイン） - 要約

JAMMA は日本のアーケード業界団体が定めた、ゲーム基板と筐体をつなぐ 56 接点のエッジコネクタ（基板の縁に並べた銅の接点を、筐体側のコネクタに差し込む方式）の配線規格である。この要約はリファレンスシート（2026-11-11 に1件ずつ照合済み）を報告書用に縮めたもので、データの日付は 2026-11-10 である。

確度の印: 確認済＝独立した2つ以上の出典、またはネットリスト・データシート・メーカーの取扱説明書・ライブデータ（JLCPCB の API など）で確認。単一出典＝出典が1つだけ。未確認＝出典で確認できていない。推論＝出典のある事実からの工学的判断。

用語: 「部品面」は部品を載せる表面（KiCad の F.Cu）、「はんだ面」は裏面（B.Cu）。「フィンガ」はエッジ端子の銅パッド、「タング」は基板のうちコネクタに差し込む凸部、「肩」はタングの付け根で基板が広がる位置。「BTL」はスピーカーの両端を逆相の2出力で駆動する方式で、どちらの端子も GND ではない。「プルアップ」は入力線を抵抗で電源側に引いておく回路。「アクティブ Low」は GND に落ちたときに有効になる信号。

## 1. この分野の結論

1. エッジ端子は、ピッチ 3.96mm、タング幅 114.4mm（公称）、フィンガ幅 2.3mm、キー溝 幅 3.0mm × 深さ 11.5mm、板厚 1.6mm で作り、JLCPCB には ENIG + Gold Fingers: Yes + 30° 面取りで発注する。ピッチ・フィンガ幅・板厚は JST GEC と Hirose CR7 の両方の公差に入るが、タング幅は両社の範囲が 114.6mm の1点でしか重ならないための妥協値で、Hirose の下限を最大 0.4mm 下回るので、実際の筐体ハーネスで挿入を確かめる必要がある。（推論。根拠のメーカー図面は確認済）
2. 金フィンガー付きの基板は JLCPCB の Standard PCBA（部品実装の上位区分）になり、安い Economic PCBA は選べない。金フィンガーと 30° 面取りの追加料金は $0 で、費用がかかるのは ENIG 表面処理（150 × 200mm で5枚 $20.10、10枚 $23.50）である。（確認済）
3. 本基板の電源は +5V（3/4/C/D の4接点）だけを使い、GND は8接点（1/2/27/28/A/B/e/f）をすべて使う。日本の筐体の多くは −5V（5/E）を供給するので、5/E は無接続にし、GND や他の信号につないではいけない。嵌合コネクタの定格は1接点 3A である。（ピン・定格は確認済。JAMMA 規格書そのものの定格は未確認）
4. 映像は正極性アナログ RGB で、2kΩ 負荷に約 3Vp-p（黒 0V、DC 結合）を出し、同期は P ピンに負極性コンポジット同期を出す。これは Blast City の取扱説明書の "2kΩ / 3.0Vp-p" と "NEGATIVE, H/V Composite" に合わせた値である。（確認済）
5. ファミコンの走査周波数 15.7458 kHz / 60.0985 Hz は、Wells-Gardner K7000（15.1〜16.8 kHz / 47〜63 Hz）と Hantarex MTC 9000（15.625 ± 0.3 kHz / 45〜70 Hz）の同期範囲に入る。ただし日本の筐体の Nanao MS8/MS9 で実測した報告は無い。（周波数は確認済の計算、適合は推論）
6. 音声は 10（+）と L（−）の間に BTL で出し、L を GND とみなしてはいけない。調べた日本の筐体の配線図はどれも 10/L を GND につないでいない。11/M は無接続にする。（確認済）
7. 音声アンプは GND への短絡保護を持つ 5V の D 級 BTL アンプにし、第一候補は PAM8302AASCR（C113367、Extended）、確認が取れなければ秋月 AE-PAM8012（108217、短絡・過熱保護あり、4Ω 2.0W @5V）にする。目標の「4Ω で 3W 以上」には届かず、約 2W 級になる。（推論。PAM8302A の出力と短絡保護は未確認）
8. 入力はすべてアクティブ Low なので、JAMMA ピン → プルアップ 3.3kΩ（3.3V へ）→ 対 GND 10nF → 直列 1kΩ → BAV99（C2500、Basic）で 3.3V へクランプ → マイコン、の回路を全入力に共通で入れる。プルアップを実績値の 10kΩ にしないのは、コインのマイクロスイッチ（Omron D2MC-01、金接点）の最小負荷が 5VDC 1mA で、10kΩ@3.3V では 0.33mA しか流れないからである。（推論。最小負荷は確認済）
9. 日本の筐体のコインカウンタ（8/J）は +5V 系が主流で、コインロックアウト（9/K）と J は配線されていないことが多い。カウンタは AO3400A（C20917、Basic）のローサイドで ON 100〜120ms / OFF ≥ 100ms に駆動し、還流ダイオードのカソードは +12V（6/F）につなぐ。ULN2003ADR（C7512、Basic）は飽和電圧が約 1V あり、+5V カウンタに不利である。（筐体の電圧は確認済と図面読み取り、駆動回路は推論）
10. 音声アンプ IC、アルミ電解コンデンサ、ポリスイッチ／ヒューズ、ビデオアンプ、74HC86/74HCT/74LVC、BAT54 系、USB Type-C 端子は JLCPCB Basic に1件も無い。JAMMA 側の回路を「Basic のみ」で完結させることはできない。（確認済）

## 2. 報告書にそのまま載せる表

表はリファレンスシートの該当行をスクリプトで写したものである。表中の「1.6 節」「4.3 節」などはリファレンスシートの節番号を指す。

### 2.1 JAMMA 56ピンの全ピン表

入力はすべて GND に落とすと有効（アクティブ Low）です。はんだ面の文字は G、I、O、Q を使いません。

| 部品面 | 信号 | はんだ面 | 信号 | 確度 | 備考 |
|---|---|---|---|---|---|
| 1 | GND | A | GND | 確認済 | |
| 2 | GND | B | GND | 確認済 | |
| 3 | +5V | C | +5V | 確認済 | |
| 4 | +5V | D | +5V | 確認済 | |
| 5 | −5V | E | −5V | 確認済（配線表）／規格書原本では未確認 | 国内の配線表はすべて 5/E = −5V。Neo Geo MVS は −5V 無し。Astro City・New Astro City・Egret II・Windy・Exceleena 2 は供給、Blast City の JAMMA 変換ループは "-5v is not supplied" |
| 6 | +12V | F | +12V | 確認済 | |
| 7 | KEY（キー溝、接点無し） | H | KEY | 確認済 | 逆差し防止。キーの無いハーネスもあり、逆差しすると入力 IC が壊れるおそれがある |
| 8 | Coin Meter 1（コインカウンタ1） | J | Coin Meter 2 | 確認済 | 日本の筐体では J が無配線のことが多い（1.8 節） |
| 9 | Coin Lockout 1 | K | Coin Lockout 2 | 確認済 | 日本の筐体（Astro City、Egret II、Windy）では無配線（図面読み取り） |
| 10 | Speaker +（アンプ後） | L | Speaker −（アンプ後） | 確認済 | モノラル。L は GND ではない（1.6 節） |
| 11 | Audio +（プリアンプ出力、ほぼ未使用） | M | Audio GND | 単一出典の食い違いあり | ブログ1件は 11/M を "No connection" とする。Neo Geo の 1スロット基板の JAMMA 配置では 11 = Unused、M = Audio GND。マルチスロット MVS の「MVS pinout」では 10 = Right speaker、L = Left speaker、11 = Mono audio、**M = Test button** |
| 12 | Video Red | N | Video Green | 確認済 | |
| 13 | Video Blue | P | Video Sync（負極性コンポジット） | 確認済 | |
| 14 | Video GND | R | Service Switch | 確認済 | Service はクレジット +1（カウンタは増えない） |
| 15 | Test Switch | S | Tilt（Slam）Switch | 確認済 | Test でテストモード。Tilt は多くのゲームで未実装。マルチスロット MVS の「MVS pinout」では 15 = Coin switch #3 P1、S = Coin switch #4 P2（Test は M） |
| 16 | Coin 1 | T | Coin 2 | 確認済 | GND へのパルス |
| 17 | 1P Start | U | 2P Start | 確認済 | |
| 18 | 1P Up | V | 2P Up | 確認済 | |
| 19 | 1P Down | W | 2P Down | 確認済 | |
| 20 | 1P Left | X | 2P Left | 確認済（多数派） | 旧 ArcadeControls wiki の表は 20/21（X/Y）の Left/Right が逆との指摘がある（検索スニペット、単一出典） |
| 21 | 1P Right | Y | 2P Right | 確認済（多数派） | 同上 |
| 22 | 1P Button 1 | Z | 2P Button 1 | 確認済 | |
| 23 | 1P Button 2 | a | 2P Button 2 | 確認済 | |
| 24 | 1P Button 3 | b | 2P Button 3 | 確認済 | |
| 25 | (1P Button 4) 非公式 JAMMA+ | c | (2P Button 4) 非公式 | 確認済（入力として使われること） | Astro City は "1P SW 4 / 2P SW 4"、Egret II と Windy は "1P SPARE 1 / 2P SPARE 1" として配線。Neo Geo は 1スロット・MVS pinout とも "P1 button D / P2 button D"、CPS2 などは 4人目用に流用 |
| 26 | (1P Button 5) 非公式／未使用 | d | (2P Button 5) 非公式／未使用 | 食い違いあり | Hardware Book 版は "Not used"、pinouts.ru 版は Button5。Astro City は "1P SW 5 / 2P SW 5"、Egret II と Windy は "1P SPARE 2 / 2P SPARE 2"。Neo Geo は 1スロットの JAMMA 配置で Unused、MVS pinout で 26 = "Select up"、d = "Select down" |
| 27 | GND | e | GND | 確認済（多数派） | pinouts.ru 版のみ 27/e = Button6。Hardware Book 版と Arcade Otaku は GND |
| 28 | GND | f | GND | 確認済 | |

**情報源の間の食い違い（まとめ）**

| 箇所 | 食い違いの内容 | 本シートの扱い |
|---|---|---|
| 5/E（−5V） | 規格書原本で −5V が規定かは未確認。国内の配線表はすべて −5V。供給しない筐体もある | 本基板では無接続 |
| 11/M | Audio +/GND（Arcade Otaku 等）と "No connection"（ブログ）。MVS pinout では 11 = Mono audio、M = Test button（ステレオは 10 = 右、L = 左） | 無接続（ハイインピーダンス） |
| 25/c、26/d | Button4/5、"Not used"、SPARE1/2、MVS pinout の 25/c = button D・26/d = Select up/down と各種 | 入力専用（プルアップ付き）にする。出力・電源・GND に使わない |
| 15/S（MVS pinout） | JAMMA の Test/Tilt に対し、MVS pinout は Coin #3/#4 | JAMMA 配置として扱う。MVS 配線の筐体では Test が M に来る（4.4 節） |
| 27/e | pinouts.ru 版のみ Button6 | GND として扱う |
| 20/21（X/Y） | 旧 ArcadeControls wiki で Left/Right が逆との指摘 | 20 = Left、21 = Right（多数派） |
| 制定年 | 英語版 Wikipedia は 1985 年、日本語 Wikipedia と wdic は 1986（昭和61）年 | 設計に影響しない。未解決 |

**用語の注意（確認済）**: 「JAMMA VIDEO規格」は JVS（新 JAMMA、RS-485/USB）の正式名で、56ピンの JAMMA（JS）規格とは別物です。JAIA の公式「資料」ページに 56ピン JAMMA 規格書はありません。規格書の原本は未入手です。

### 2.2 エッジコネクタの寸法・向き・JLCPCB での指定

**向きの決まり（確認済）**

- 部品面（F.Cu、表面）に 1〜28、はんだ面（B.Cu、裏面）に A〜f を置きます。同じ番号の表裏（1↔A、2↔B …）は同じ X 位置です。3 設計と日本語の配線表（「部品面 1〜28 / はんだ面 A〜f」）で一致します。
- 部品面を見て端子端（先端）を下にすると、1番が左端、28番が右端です。先端を上にすると 1番が右端です。
- キー溝は 1番側から 7番目（6 と 8 の間、7/H 位置）にあります。
- 筐体に設置したときの向き（部品面が上か横か）は筐体の取付板しだいで、規格化されていません（未確認）。

**本基板のフットプリント設計値（推奨値）**

座標系: 原点は 1番パッドの中心線と基板先端線の交点です。X+ は 28番方向、Y+ は基板内側（先端から奥）です。部品面を見て先端を下にした図で、1番が左、28番が右になります。

| # | 項目 | 設計値 | 根拠 | 確度 |
|---|---|---|---|---|
| 1 | ピッチ | **3.96mm**（本シートで変更。第2パスは 3.9624mm） | JST 106.92 ± 0.05 と Hirose 106.98 ± 0.08 の両方を満たす。DE10Jamma の実績 | 推論（根拠は確認済） |
| 2 | パッド X 位置 | n番（n = 1〜6、8〜28）と対応する文字: X = (n − 1) × 3.96。1↔A、2↔B、3↔C、4↔D、5↔E、6↔F、8↔J、9↔K、10↔L、11↔M、12↔N、13↔P、14↔R、15↔S、16↔T、17↔U、18↔V、19↔W、20↔X、21↔Y、22↔Z、23↔a、24↔b、25↔c、26↔d、27↔e、28↔f（表裏同 X）。7/H はパッド無し | 3 設計とも表裏同 X | 確認済（配置規則）／推論（値） |
| 3 | 両端パッド中心間 | 106.92mm（本シートで変更） | 3.96 × 27 | 推論 |
| 4 | パッド幅 | **2.30mm**（パッド間ギャップ 1.66mm） | Hirose 2.3 ± 0.1、JST 2.3 ± 0.035 の中心値。DE10 2.35、jz 2.2、ORB 2.03 | 確認済（根拠） |
| 5 | パッド範囲（Y） | **1.2〜10.0mm**（長さ 8.8、中心 Y = 5.6） | JLCPCB の 30° 面取りのセットバック約 1.13mm、Hirose の接点位置 約 3.2 ± 0.4、挿入深さ 8.5 | 推論（根拠は確認済） |
| 6 | パッド形状・層 | 角形 SMD。部品面は F.Cu + F.Mask、はんだ面は B.Cu + B.Mask。**ペースト層は付けない** | DE10 基板版の誤り（裏パッドに F.Paste） | 推論 |
| 7 | マスク開口 | 両面とも X = −3.74〜+110.66（タング全幅）、Y = 0〜10.5 の帯を全面開口（パッド間もマスク無し）（本シートで X 範囲を変更） | JLCPCB: フィンガ領域は全面開口が必須、未指定なら自動開口 | 確認済（規則）／推論（値） |
| 8 | 銅禁止 | Y = 0〜1.2 は全層で銅禁止（ベタ・配線・ビア無し）。フィンガ帯（Y ≤ 10.5）内はパッド以外の銅・ビア・シルク無し。ベタは Y ≥ 11 から | JLCPCB: 面取り域に銅不可 | 推論 |
| 9 | パッドからの配線 | 各パッドの奥端（Y = 10.0）から引き出す。電源と GND は 1mm 以上の太幅で、複数ピンを並列にする | 1接点 3A | 推論 |
| 10 | キー溝（7/H） | 中心 X = 6 × 3.96 = **23.76**（本シートで変更）、幅 **3.0mm**（許容 2.5〜3.0）、深さ **11.5mm**、入口両角 0.5 × 45° 面取り、奥は R0.5 以上（ルータ径なり）。隣接パッドの銅から溝までは 1.31mm | Hirose 2.5 +0.1/0 × 11 +0.5/0、JST 3.0 × 10.0、DE10 3.0 × 10、jz 2.5 × 11.5、ORB 3.81 × 10.92、キー厚 2.36（Sullins）／2.0（CR1-GPIN） | 推論（根拠は確認済） |
| 11 | タング幅 | **114.4mm**（X = −3.74〜+110.66）（本シートで変更。第2パスは 114.6） | JST 114.4〜114.6 と JLCPCB の外形公差 ±0.2 | 推論 |
| 12 | 外端パッド中心→側面 | 3.74mm（パッド端→側面 2.59mm）（本シートで変更） | 上記タング幅から決まる。JST の規定 3.84 +0/−0.1 の下限ちょうどで、外形公差 ±0.2 の下振れでは JST の範囲を外れる | 推論 |
| 13 | タング外角 | 0.5 × 45° 面取り（または R0.5） | Hirose C0.5、JST 肩 C0.5、ORB 25mil 面取り | 推論（根拠は確認済） |
| 14 | 肩の位置 | 基板本体をタングより広くする場合、先端から **12.0mm** 以上 | Hirose 図の 10、JST 図の 10.0、ORB 約 12.07。コネクタの耳（タング外へ約 9.5〜10mm）が先端から 8.5mm まで来る | 推論 |
| 15 | 基板厚 | **1.6mm**（JLCPCB 公差 ±10% = ±0.16） | Hirose・JST 1.6 ± 0.15、Sullins 1.57 ± 0.20 | 確認済（根拠） |
| 16 | 先端面取り | JLCPCB の発注で **30°**（推奨）を選ぶ。45° ならセットバック 0.74 で足りるが、1.2 のままで問題ない | JLCPCB ヘルプ | 確認済（規則） |
| 17 | 表面処理 | **ENIG（1U"）+ Gold Fingers: Yes**。2U" は任意 | JLCPCB に硬質金は無く、金は ENIG のときだけ | 確認済（規則） |
| 18 | 面付け | 単品発注、またはフィンガ辺を外周に出す背中合わせ面付け。V カットの内側にフィンガを置かない | JLCPCB ヘルプ | 確認済（規則） |
| 19 | 基板最小寸法 | 50 × 50mm 以上（タングだけで 114.4 幅なので自動的に満たす） | JLCPCB | 確認済（規則） |
| 20 | 部品禁止域 | 先端〜12mm は両面とも部品・シルク禁止。12mm より奥は高さ制限なし | Hirose 挿入深さ 8.5、本体厚 11.1 | 推論 |
| 21 | 取付穴 | φ3.2（M3）を四隅、縁から 4mm 以上。先端〜12mm には置かない | jz M3（3.2mm）、DE10 3mm、フィンガーボード M3 × 4。JAMMA の規定は見つからない | 推論 |
| 22 | シルク | 部品面のパッド奥（Y > 11）に "1"・"28"、はんだ面に "A"・"f"、部品面に "PARTS SIDE / 1-28" | 慣行 | 推論 |

**JLCPCB での金フィンガーの指定方法と制約**

| 項目 | 内容 | 確度 |
|---|---|---|
| 指定方法 | 発注画面で "Gold Fingers: Yes"（選択肢 "No / Yes"）を選び、面取り角 30° または 45° を選ぶ。表面処理は ENIG にする | 確認済（ヘルプと発注画面） |
| 金になる条件 | "only when ENIG is chosen, the fingers for your PCB will be with gold, if you choose HASL surface treatment, then it will be covered with tin."。発注画面: "If you choose HASL surface finish, we will use HASL as edge connect plating." | 確認済 |
| 硬質金 | "does not offer electroplated hard gold finish"、"JLCPCB applies our precision Electroless Nickel Immersion Gold (ENIG) finish to the gold fingers." | 確認済 |
| ENIG の厚さ | "JLCPCB offers gold thicknesses of 1 or 2 microinches."（約 0.025/0.05µm）、Ni 約 3〜6µm | 確認済 |
| 面取り角 | "The available bevel angles are 30° and 45°. ... we recommend prioritizing a 30° bevel." | 確認済 |
| 銅のセットバック | 1.6mm 板厚で 30° ± 5° → "Approx. 1.13 mm"、45° ± 5° → "Approx. 0.74 mm"。"A thicker board requires a longer copper setback."。不足するとエンジニアがフィンガを短くする | 確認済 |
| 面取りの画面表示 | 30° 選択時に「a (bevel angle): 30° / t (board thickness): 1.6mm / d (depth): 1.13mm / tr (residual thickness): 0.53mm」 | 確認済（発注画面のスクリーンショット） |
| 面取り域 | "The red frame indicates the beveled area. ... this area can not have copper."。"As the entire edge will be chamfered, ensure enough clearance between traces and the board edge"（エッジ全長が削られる） | 確認済 |
| マスク | "The gold finger area must have the solder mask fully opened (clearance window). For designs without a solder mask opening, JLCPCB will automatically apply a solder mask opening by default." | 確認済 |
| 寸法制限 | "Chamfers are not available on boards smaller than 5x5cm."、"The length and width of a single board or panel with gold fingers shall not be less than 50mm." | 確認済 |
| 面付け | "If there is fingers in your file and it is panel with v-cut, then the fingers can not be made with chamfer since the fingers will be in the middle of the PCB."。パネルは背中合わせ配置でフィンガ辺を外周に出す | 確認済 |
| 板厚公差 | "Board thickness tolerance is +/-10%." | 確認済 |
| OSP | "Not supported for ... physical contact areas (e.g., gold fingers, keypads)" | 確認済 |
| 金フィンガーの追加料金 | Instant Quote の実見積で、Gold Fingers Yes + 30° 面取りの追加費は **$0**（2層・4層、5枚・10枚の全8条件で同額）。API 応答の goldThicknessMoney=0、送信値 goldFingerBevel=2（No は 0） | 確認済（ライブデータ） |
| ENIG の費用 | 150 × 200mm の ENIG 代は 5枚 $20.10、10枚 $23.50。120 × 60mm では $17.40 / $18.30。ENIG 露出面積が両面合計 30% を超える分は、1U" で超過 1% ごとに $0.8992/m²、2U" で $1.7985/m²/1% | 確認済 |
| PCBA の区分 | 能力表「Gold Fingers/Castellated Holes/Edge Plating — Economic: Not Support / Standard: Support」（JLCPCB と LCSC で同じ文言）。実画面で Gold Fingers: Yes にすると Economic ボタンが灰色（選択不可）になり、Standard が自動選択された | 確認済 |
| 「エッジパッドあり・Gold Fingers: No」 | 見積システム上は Economic PCBA が選べた（ENIG、面取りなし、PCB 価格 $38.60）。Gerber 審査で Standard へ再分類されるかは公式記述が無い。追加料金ページに "if you did not select the correct options during placing orders, there may be extra costs required during the file review process" とある | 単一出典（実操作）／審査は未確認 |
| Standard PCBA の自動変更 | Gold Fingers Yes で PCBA を ON にすると "Edge Rails/Fiducials: Added by JLCPCB"、"The board size is modified to be 160mm*200mm due to adding two 5mm edge rails on the shorter sides"、PCB 価格は $39.70（Board $15.40 / Surface Finish $20.30） | 確認済（実操作） |
| めっきリード | JLCPCB の資料に記載なし。ENIG（無電解）なので不要と考えられる | 推論 |

JLCPCB 実見積（150 × 200mm、1.6mm、ENIG 1U"、1oz、2026-11-10、Gerber 未アップロード）:

| 層 | 枚数 | 金指 | Engineering fee | Surface Finish（ENIG） | Board | 合計 | 1枚あたり |
|---|---|---|---|---|---|---|---|
| 2 | 5 | Yes 30° / No | $4.00 | $20.10 | $14.50 | $38.60 | $7.72 |
| 2 | 10 | Yes 30° / No | $4.00 | $23.50 | $28.90 | $56.40 | $5.64 |
| 4 | 5 | Yes 30° / No | $25.00 | $20.10 | $18.50 | $63.60 | $12.72 |
| 4 | 10 | Yes 30° / No | $25.00 | $23.50 | $37.00 | $85.50 | $8.55 |

### 2.3 電源・映像・音声・入力・コインの実態

**電源のピンと定格**

| 項目 | 内容 | 確度 |
|---|---|---|
| ピン | +5V: 3、4、C、D（4接点）。+12V: 6、F。−5V: 5、E。GND: 1、2、27、28、A、B、e、f（8接点）。Video GND: 14 | 確認済 |
| 1接点あたりの定格 | 3A（JST GEC、Hirose CR7、Sullins。Sullins は "one contact energized" 条件）。JAMMA 規格書そのものの値は未確認 | 確認済（コネクタ）／未確認（規格書） |
| 理論容量 | +5V は 4接点 × 3A = 12A。ただし全接点同時通電ではディレーティングが必要で、3A をそのまま4倍してはいけない | 推論 |
| 規格上の用途 | +5V（game）、+12V（sound） | 確認済 |
| 筐体の電線 | Astro City: "K: AWG18 UL1015 許容電流 12A / L: AWG20 UL1007 8.4A / 細: AWG22 UL1007 6.4A"。+5V と GND はエッジ側で2本ずつ配線（図面読み取り） | 確認済（一次資料） |

**筐体の電源装置**

| 筐体 | +5V | +12V | −5V | 確度 |
|---|---|---|---|---|
| Astro City（400-5198 PWR SPLY UNIT、入力 AC90〜132V） | 7 A | 1.5 A | 0.1 A（JAMMA 5/E に配線あり） | 確認済（取扱説明書） |
| New Astro City（400-5198-CE-01Z） | 7 A | 1.5 A（PEAK 2A） | 0.1 A | 確認済（取扱説明書） |
| Egret II（Switching Regulator Assy） | あり | あり（+ "POST +12V"） | あり（5/E） | 確認済（配線図） |
| Windy | 5 A | 1 A | 0.5 A（5/E に配線あり） | 確認済（配線図と筐体データベース） |
| Exceleena 2 | 7 A | 2 A（Peak 6A） | 0.2 A | 単一出典（筐体データベース） |
| Blast City（JAMMA 変換ループ 600-6738-21） | あり | あり | "-5v is not supplied"（電源は +5V/+3.3V/+12V のみ） | 確認済 |
| Mean Well RT-65A（現行の代替電源、3出力） | 定格 6 A、"CURRENT RANGE 0 ~ 8A"、"VOLTAGE ADJ. RANGE CH1: 4.75 ~ 5.5V"、負荷変動 ±1.0% | 2.8 A、0〜3.5A、±3.0% | 0.5 A、0〜1A、±1.0% | 確認済（データシート） |

**映像の信号レベル（筐体・モニタ別の抜粋）**

| 筐体／シャーシ | 映像入力・同期・周波数 | 確度 |
|---|---|---|
| Sega Blast City（Bass Fishing 版取説 p.49、29" 3-mode Nanao MS-2931） | SW3 で切替: "When inputting D-SUB MINI 15P: 75Ω / 0.7Vp-p"（ON）、"When inputting AMP 6P: 2kΩ / 3.0Vp-p"（OFF）。SW1/SW2 で 15kHz/24kHz/31kHz モード。"correct images can not be obtained unless the settings of the horizontal frequency or video input connector (input impedance/input level) are compatible with the board." | 確認済（取扱説明書） |
| Sega Blast City（JAMMA 変換） | "Video Signal = POSITIVE, 3.0Vp-p, 2kΩ Impedance & SYNC = NEGATIVE, H/V Composite"、制御出力インピーダンス 8Ω | 確認済（取説と Arcade Otaku） |
| Wells-Gardner K7000 | "RGB analog, [1?] to 5v peak-to-peak (adjustable with contrast control), 4.7k ohm input impedance"（OCR が崩れ、下限値は不確か）。オプション "RGB analog 0-0.75v, 75 ohm input impedance"。水平 "15.1 kHz to 16.8 kHz standard"、垂直 "47 Hz to 63 Hz" | 確認済（サービスマニュアル） |
| Hantarex MTC 9000 | "RGB anal/TTL compat., positive, white (high-level)、2-5 V p.p. (by use of input switch)"、"The three RGB video amplifiers are d.c. coupled"。水平 "15-16 kHz"（調整範囲 "15.625 +/- 0.3 kHz"）、垂直 "45-70 Hz" | 確認済（マニュアル） |

**同期信号**

| 項目 | 内容 | 確度 |
|---|---|---|
| 形式 | 負極性 TTL レベルのコンポジット同期（H/V 合成）を P ピンに出す。Low ≒ 0V、High ≒ 4〜5V | 確認済 |
| 日本の筐体の配線 | 1本の SYNC 線だけ: Astro City のカラーディスプレイ・コネクタは RED/GREEN/BLUE/SYNC/GND(SYNC) の5線。Egret II は "R, G, BL, SYNC, GND"。Windy は "SYNC, GND, BLUE, GREEN, RED" | 確認済（配線図） |
| K7000 | "Sync: TTL positive or negative going, separate or composite. Input impedance: 20K ohms for positive going sync; 12K ohms for negative going sync."、"If the sync signal is composite, use the horizontal sync input of the same polarity" | 確認済 |
| MTC 9000 | 同期振幅 "1.5 - 5 V p.p."、極性はスイッチで切替。"Contact 6 horizontal or composite sync"、"Contact 5 vertical sync (or no connexion if using composite sync)" | 確認済 |
| Nanao / Toei | 同期入力の閾値と入力インピーダンスは未確認 | 未確認 |
| 民生機器向け | 同期は "high-voltage TTL" で、民生機器向けには 470Ω を直列に入れる | 単一出典 |
| H/V 分離 | 必要になるのは Blast City の D-SUB15（31kHz/NAOMI）など JAMMA 以外の入力の場合 | 確認済 |

**音声**

| 項目 | 内容 | 確度 |
|---|---|---|
| スピーカー端子 | 10（Speaker +）と L（Speaker −）。モノラル、アンプ後の出力で、筐体側にアンプは不要（基板側にパワーアンプが必要） | 確認済 |
| L は GND ではない | "On mono JAMMA boards, the speaker- pin is not connected (this isn't ground)."。"ALL jamma boards use bridged amplifiers where sp- is never ground"、片側を接地するとアンプが壊れる（言い過ぎを含み、反対意見もある） | 確認済（複数出典、ただし表現の強さは単一出典） |
| 筐体の配線 | 配線図の 10/L はどれも GND に接続されていない | 確認済（配線図） |
| 11/M | Audio +（プリアンプ出力、ほぼ未使用）/ Audio GND。マルチスロット MVS の「MVS pinout」は 10 = Right speaker、L = Left speaker でステレオにし、11 = Mono audio、M = Test button とする（1スロット MVS は JAMMA 配置で、ステレオは基板上のピンヘッダ）。JAMMA 基板を MVS 配線の筐体に入れるとアンプが焼けたという報告がある（二次） | 確認済（ピン名、NeoGeo Dev Wiki の表を本シートで確認）／単一出典（事故報告） |

**筐体のスピーカーと音量**

| 筐体 | スピーカー | 音量の調整 | 確度 |
|---|---|---|---|
| Astro City | 前面パネルの LEFT と RIGHT にそれぞれ "8Ω 10W"（部品表 "130-5091 SPEAKER 8 OHM 10 SPL"）。コネクタの C 側で "A2×2"、"92×2" と束ねられる（並列で合成約 4Ω と読める、図面読み取り）。JAMMA 10（A, PINK）と L（90, GRAY）は電源ユニットの "SOUND" コネクタ → "SOUND VOL." → "SPEAKER" コネクタ（A2/92）の順 | 電源ユニットの SOUND VOL. | 確認済（取扱説明書） |
| New Astro City | — | "SOUND VOL. : Adjust the Speaker Volume." | 確認済 |
| Blast City（Bass Fishing 版） | "130-5156 SPEAKER BOX 8 OHM" | "220-5420 RHEO STAT 100 OHM 10W"、"SOUND VOLUME Adjust the Speaker Volume" | 確認済 |
| Egret II | SP(R) と SP(L) がどちらも "4Ω" | JAMMA の SPEAKER(+)/(−) は F3 SYSTEM(4P)・FX1 SYSTEM(4P) と並んで切替スイッチと "VOL." を通る | 確認済（配線図） |
| Windy | LEFT/RIGHT SPEAKER（インピーダンス未確認） | JAMMA 10（灰 8）と L（白 9）→ "SOUND VOLUME"（L-Ch / R-Ch の2連）。Konami 基板用の "STEREO SOUND (FOR KONAMI PCB)" コネクタ（NH-4）が別にある | 確認済（配線図）／インピーダンス未確認 |

**入力（抜粋）**

| 項目 | 内容 | 確度 |
|---|---|---|
| 電気的性質 | 全入力が GND 接続でアクティブ Low。日本の筐体の入力はすべて無電圧接点で GND に落とす方式（Astro City / Egret II / Windy の配線図） | 確認済 |
| Neo Geo（CRE401） | "The leftmost pin's net pulls all outputs through 1k resistors. The 330 ohm resistors provide current protection (sometimes as fuses), the capacitors smooth out eventual spikes."。実測: R1 330Ω、R2 1kΩ、C1 は 33nF（-17）、35〜36nF（-18）、41〜43nF（-19）、42〜43nF（-2N）。"cut-off frequency of about 15kHz"。部品は "MODEL CR SERIES Single-In-Line ... Resistor/Capacitor Networks" の "-A Circuit" | 確認済 |
| DE10Jamma | JAMMA ピン → 1k 直列 → FPGA GPIO ノード、ノードに 10k プルアップ（+3V3）と 10nF to GND。全 28 入力同一（netlist 上 R86 のみ 1k プルアップで、誤記と思われる＝推論）。"Inputs are RC filtered ... to give EMI protection to the FPGA."、"No multiplexing, polling or debouncing of the inputs" | 確認済（netlist + README） |
| jammanator-pi | JAMMA ピン — 10k プルアップ（+3.3V、4連アレイ）— 100nF to GND（4連 C アレイ C62857）— 1k 直列（4連アレイ）— BAT54S（C47546、中点＝信号、両端＝+3.3V/GND のクランプ）— SN74LVC244APWR（C7668）— MCP23017（C558584）× 2。保護回路は 470Ω + 1N5711 + 100nF として検証 | 確認済（kicad_pcb） |
| RP2040 の入力定格 | 絶対最大 "Voltage at IO VPIN -0.5 ... IOVDD + 0.5 V"（IOVDD max 3.63V）。ESD は HBM 2kV（全ピン）、FT ピンのみ 4kV。内蔵プルアップ RPU 50〜80kΩ（弱い） | 確認済（データシート） |
| RP2350（Pico 2）の入力定格 | このトピックのノートには記載なし。Pico 2 関連のシートで確認すること | 未確認 |
| 拡張ボタンの配線 | Astro City は 25/c/26/d を "1P SW 4 / 2P SW 4 / 1P SW 5 / 2P SW 5"、Egret II は "1P SPARE 1 / 2P SPARE 1 / 1P SPARE 2 / 2P SPARE 2" とし、S/S コネクタに "1P SPARE 3 / 2P SPARE 3"（キックハーネス）。Windy も "1P SPARE 1 / 2P SPARE 1 / 1P SPARE 2 / 2P SPARE 2" | 確認済（配線図） |
| Service / Test / Tilt | Service（R）はクレジット +1（カウンタは増えない）、Test（15）でテストモード、Tilt（S）は多くのゲームで未実装。電気的詳細（Slam）は未確認 | 確認済（意味）／未確認（電気的詳細） |

**コイン入力の信号（抜粋）**

| 機構 | 内容 | 確度 |
|---|---|---|
| 日本の筐体の主流 | 旭精工 AD-81P 系のメカセレクタ＋マイクロスイッチ（COM/NO の無電圧接点）。New Astro City の AD-81P は「機械式」で、マイクロスイッチの "COM(コモン)と NO(ノーマリーオープン)だけ使用" | 確認済 |
| Omron D2MC | D2MC-01 は "Gold alloy" 接点、**"Min. applicable load 5 VDC 1mA"**（銀接点の D2MC-5 は 5 VDC 160mA）、30 VDC 0.5A。レバーが長すぎると "improper switch resetting or contact chattering may occur" | 確認済（データシート） |
| 旭精工 AE-204D（電子セレクタ） | 電源 "DC24V(DC15.0~DC26.4V)" / "DC12V±5%(特別仕様)"。正貨信号 "信号電圧/DC30V(MAX) 信号電流/50mA(MAX) 信号パルス幅/50msec.±5msec." | 確認済（メーカー） |
| 汎用 HX-616 | "オープンコレクタ出力のよう"、パルス幅 "Fast/Medium/Slowでそれぞれ30msec/50msec/100msec程度"（オシロで観測）、電源 12V | 単一出典（ブログ） |
| チャタリング時間 | メカセレクタのマイクロスイッチの実測値は無い（Omron はレバー形状による、としか書いていない） | 未確認 |

**コインカウンタ（8/J）（抜粋）**

| 項目 | 内容 | 確度 |
|---|---|---|
| 日本の筐体の電圧 | **+5V 系が主流**。Astro City: COIN METER（220-5412 MAG CNTR W/CONN）の線色は 30（YELLOW、電源 DC OUT1 の +5V と同じ色）と 80（BLACK、JAMMA 8）。JAMMA 側の表で J/9/K は "(COIN METER 2)(COIN LOCK OUT 1)(COIN LOCK OUT 2)" と括弧付きで配線されていない。Windy: "GX-06PD" の2線は赤（2、+5V の線色）と灰（8、JAMMA 8 COIN COUNTER1）、J/9/K は無配線。Cyber Lead: "デンジカウンタ NX-06PD 5VDC"。Egret II: JAMMA 8 = "COUNTER"、J/9/K の下に配線は無い | 確認済（Cyber Lead の部品表）／図面読み取り（Astro City・Windy・Egret II。220-5412 のコイル電圧は線色からの推定） |
| 米国系・MVS | "The counters typically have one pin hardwired to +12V"、通電と遮断を "both during a long enough time" で行う。NEO-F0 → ULN2003 のオープンコレクタで駆動 | 確認済 |
| 電磁カウンタの一次仕様 | ライン精機 MZ シリーズ: "計数速度 20Hz"、"パルス幅(メーク比) 25ms(1:1)"、"電源 DC12V/24V"、"消費電力 DC1.2W"（公式ページ。検索要約の 50ms は誤記）。Kessler-Ellis の DC 電磁カウンタ（5 cps 品）は on 120ms / off 80ms、約 85mW | 確認済（ライン精機）／単一出典（KEP） |
| オープン基板の実例 | 調べたオープン JAMMA 基板（ORB、DE10Jamma、jammanator-pi、bad_raspi_jamma、PiPicoJamma、JAMMA_2player_xbox360、jzdziarski 13 枚、JammaMia 公開ピン配置）は**どれも 8/J と 9/K を駆動していない**。JammaMia: "A ULN2003 chip is used for the OUT signals ... Maximum current is 500mA and maximum voltage is +5V"、ただし同梱ピン配置では 8/J・9/K は "NC" | 確認済（各設計ファイル） |

**コインロックアウト（9/K）**

| 項目 | 内容 | 確度 |
|---|---|---|
| JAMMA/MVS の方式 | "Coin lockouts are typically coils hardwired to the 12V power supply. It's the game PCB's job to power them by grounding their second terminal"。"When powered, it allows an inserted coin ... When not powered ... the coin take the return path."（無通電時は返却側＝フェイルセーフ） | 確認済 |
| 日本の筐体 | Astro City、Egret II、Windy では 9/K と J が配線されていない（図面読み取り）。日本の「ブロッカー」はセレクタ側の部品 | 確認済（図面読み取り） |
| 旭精工のブロッカー | QL-102（CB/81M 用）は 12DC で "直流抵抗(Ω)=85±10% 電流(mA)=157以下"、24DC で "313±10% / 86以下"、"定格消費電力 約2W"。QM-5 は 12V 76Ω / 158mA 以下。QL-203 は 12V 100Ω / 120mA。SB-101 は 12V 57Ω / 210mA 以下 | 確認済（メーカー） |
| ブロッカーの極性 | 通電時に阻止するか受け付けるかはページに記載が無い。VM81-M の仕様も未確認 | 未確認 |

### 2.4 本基板の設計目標値

値そのものは推論（設計判断）で、根拠の欄が出典の事実である。

| 項目 | 目標値（許容） | 根拠（事実） |
|---|---|---|
| RGB 出力レベル | 白 3.0V ±10%（開放）、2kΩ 負荷で 2.5〜3.0Vp-p、黒 0V、DC 結合、正極性 | Blast City "2kΩ / 3.0Vp-p"、Neo Geo "0~3.5V"、MTC 9000 "2-5 V p.p."、K7000 "4.7k" |
| RGB 出力インピーダンス | 100〜150Ω が実在基板並み（Neo Geo ≈ 119Ω、Sega ≈ 129Ω）。3.3V 出力の無バッファ抵抗 DAC では 240〜300Ω 程度でも実績がある（DE10Jamma R = 302Ω、jammanator-pi R = 240Ω）。トリマは付けない | MAME の値からの計算、DE10Jamma と jammanator-pi の設計ファイル、New Astro City 取説（CONTRAST 調整） |
| 75Ω 入力への対応 | 直接は対象外（D-SUB15 側の設定）。誤設定でも約 1.1〜1.3V で破損しない | Blast City SW3 の表 |
| 同期 | 負極性コンポジット、TTL（Low ≤ 0.4V / High ≥ 3.5V）、5V 系の出力段＋直列 47〜100Ω | K7000 "TTL ... 12K ohms for negative"、MTC 9000 "1.5-5 V p.p."、Blast City "NEGATIVE, H/V Composite" |
| 走査 | 15.7458 kHz / 60.0985 Hz（341 × 262 固定を推奨） | 計算、K7000 15.1〜16.8 kHz / 47〜63 Hz、MTC 9000 15.625 ± 0.3 kHz / 45〜70 Hz |
| 電源 | +5V のみ使用、4.75〜5.5V で動作、> 5.5V への保護として TVS（SMBJ6.5CA。型番の 6.5V 級は動作電圧の上限で、5.5V を少し超えた程度では導通しない見込み。降伏電圧の値はノートに無く未確認）、入力容量 ≤ 220µF、−5V は使わない、+12V はカウンタ還流ダイオード用にだけ配線（4.3 節） | RT-65A "4.75 ~ 5.5V"、JST GEC 3A/接点 |
| 音声出力 | BTL（10 = +、L = −）、GND への短絡保護付き、11/M は無接続。出力は 4Ω で 3W 以上が目標（5V 電源の D 級では約 2W が現実値。4.3 節） | 筐体のスピーカー 4/8Ω、Neo Geo の BTL 系アンプ、"speaker- ... isn't ground"、AE-PAM8012 "4Ω 2.0W @5V" |
| 入力回路 | プルアップ 3.3kΩ@3.3V（または 4.7kΩ@5V。どちらも ≥ 1mA）、直列 1kΩ、対 GND 10nF（fc ≈ 16kHz）、3.3V へのクランプ。25/26/c/d は入力専用 | CRE401 1k/330/33nF、DE10Jamma 1k/10nF、D2MC-01 の最小負荷 1mA、Astro City の SW4/5 配線 |
| ボタン・レバーのデバウンス | 2〜5ms（1〜2 フレーム以内） | 推論 |
| コインのデバウンス | Low ≥ 10ms で確定、High ≥ 10ms で解除、1 パルスを 1 枚。30ms を超える長押しを別コインと数えない | 電子セレクタ 50 ± 5 / 72 ± 3ms、HX-616 30〜100ms、AD-81P2 の投入間隔 ≥ 0.5s |
| カウンタ駆動 | ロジックレベル N-MOSFET（AO3400A C20917、Basic）のローサイド、≥ 30V、≥ 0.5A、ON 100〜120ms / OFF ≥ 100ms、+5V と +12V のコイル両対応、還流ダイオードのカソードは +12V へ（4.3 節） | NX-06PD 5VDC、Astro City/Windy は +5V、MVS は +12V、ULN2003 の VCE(sat) 約 1V、ライン精機 MZ 25ms、KEP 120/80ms |
| ロックアウト駆動 | 同じドライバ、連続 ≥ 200mA@12V | 旭精工 QL-102 157mA / SB-101 210mA、MVS ULN2003 |

### 2.5 モニタの同期範囲とファミコンのタイミングの適合

| 項目 | 値 | 確度 |
|---|---|---|
| ドットクロック | 21.477272 MHz ÷ 4 = 5.369318 MHz | 確認済（計算） |
| 水平 | 5,369,318.18 Hz / 341 = **15,745.80 Hz**（15.7458 kHz）。NTSC 放送の 15,734.27 Hz より 0.073% 高い | 確認済（計算） |
| 垂直 | / 89,342（341 × 262）= **60.0985 Hz**（ドット飛ばし無し）、/ 89,341.5 = 60.0988 Hz（2C02 の平均） | 確認済（計算） |
| 2C02 のドット飛ばし | "odd frames ... skipping the first idle tick on the first visible scanline"、"(339,261) ... directly to (0,0)"。レンダリング無効時は毎フレーム 341 × 262 = 89,342 クロック。レンダリング有効時は奇数フレームだけ1クロック短い 89,341 クロック（偶数フレームは 89,342、平均 89,341.5） | 確認済（NESdev Wiki を本シートで再確認） |
| RGB PPU | RP2C04-0001 は "Equivalent to 2C02D, but keeps 2C03 timing (no skipped dot)"。RC2C05-99 は "Uses 2C02 timing (a dot is skipped every other frame), unlike other RGB PPUs." | 確認済 |
| 任天堂の業務用実績 | PlayChoice-10 は "This game uses one of four types of Video Monitors ... [32 Type] 20-EZV(R-C) / [33 Type] 20-EZV(R-C) / [35 Type] 20-Z2AW"。Signal PCB に "INVERT OUT / NON INVERT OUT" があり映像極性を切り替える。VS. System のモニタ型番は未確認 | 確認済（PC-10）／未確認（VS.） |
| ジッタ | 2C02 だけにある奇数フレームの1ドット飛ばしが、上端ラインの1ドットのジッタとして見えることがある（家庭用 RGB 化の利用者報告） | 単一出典 |
| 自作例 | NES2JAMMA（NESRGB → JAMMA）: 映像は "TLS1233 and LM1881"、音声は "a basic LM384"。テスト結果は "quite happy"、同期の問題は報告されていない | 単一出典 |

**適合（推論）**: 15.7458 kHz / 60.10 Hz は、K7000 の 15.1〜16.8 kHz / 47〜63 Hz、MTC 9000 の 15.625 ± 0.3 kHz（上限 15.925 kHz）と 45〜70 Hz、日本の筐体の公称 15.7 / 15.75 kHz のいずれにも入ります。ドット飛ばしは1ライン（341 → 340 ドット、−0.29%）だけの変化で、垂直周期の変化は 1/89,342 です。PLL を持つ業務用モニタが同期を外す原因にはならないと見込みます。マイコンで RGB を作り直すなら、出力を 341 ドット固定で生成すれば問題自体が消えます。Nanao MS8/MS9 で 15.7458 kHz を実測した報告は未確認です。

### 2.6 参考回路の一覧

回路の要点とライセンスは各プロジェクトの設計ファイルからの読み取り（確認済）。JLCPCB 分類の欄は、その部品または同等品について下の部品分類表にある分類を写したもので、表に無いものは「ノートに記載なし」とした。DE10Jamma と Console JAMMAizer はライセンス表示が無いので、回路の再利用には作者の許諾が要る。

| 機能 | 出典プロジェクト | 回路の要点と主要部品 | JLCPCB 分類（部品分類表より） | ライセンス |
|---|---|---|---|---|
| 入力保護 | ORB v0.3 | ダイオード（カソード→JAMMA）+ SoC 内蔵プルアップ 3.3V | ダイオードの分類はノートに記載なし（BOM は品番指定なし） | MIT |
| 入力保護 | DE10Jamma | 1k 直列 + 10k PU(3.3V) + 10nF | BOM の部品はすべて Extended。同等品の 4連抵抗アレイ 1k（C20197）・10k（C29718）は Basic | 記載なし（LICENSE ファイル無し＝再利用は要許諾） |
| 入力保護 | jammanator-pi | 10k PU(3.3V) + 100nF + 1k + BAT54S + 74LVC244 | BAT54S,215（C47546）・SN74LVC244APWR（C7668）は Extended、100nF × 4 C アレイ（C62857）は Extended | MIT |
| 入力保護 | PiPicoJamma | 直結 | —（部品なし） | GPL-3.0 |
| 入力保護 | jzdziarski Atari IF | 74LS04 等 | ノートに記載なし（Basic の 74 系ロジックは 74HC14・74HC595 だけ） | 非商用教育目的のみ |
| RGB DAC | ORB v0.3 | 5bit 2進重み 510 / 1k05 / 2k2 / 4k7 / 10k を GPIO（3.3V）から加算、終端 R 200Ω, G 220Ω, B 270Ω to GND。74HC4066（5V）で各色 1bit を同期に連動して切替 | 74HC 系のうち Basic は 74HC14・74HC595 だけ（74HC4066 の分類はノートに記載なし） | MIT |
| RGB DAC | DE10Jamma | 6bit R-2R、全抵抗を単一値 "2R" にし R は 2R 2本並列。回路図 2R = 475Ω / BOM 2R = 604Ω（Bourns CAY16-6040F4LF 4連） | BOM の部品はすべて Extended。0603 1% の 470Ω（C23179）は Basic | 記載なし（LICENSE ファイル無し＝再利用は要許諾） |
| RGB DAC | jammanator-pi | 6bit R-2R、R = 240Ω（C17572）、2R = 475Ω（C228851）、0805 1%。図中 TODO "BUFFER to avoid RGB drifting depending on monitor input impedance" | 240Ω 0805 1%（C17572）は Extended（Preferred）、475Ω 0805 1%（C228851）は Extended・在庫 3 | MIT |
| RGB DAC | PiPicoJamma | 6本の抵抗 8.2k / 4.3k / 2.2k / 1k / 510 / 180Ω（±5% THT）を並列加算 | ノートに記載なし | GPL-3.0 |
| RGB DAC | RP2040 公式 VGA demo | 5bit（G は 6bit）2進重み 8.06k / 4.02k / 2k / 1k / 499Ω | 0603 1% の 510Ω / 1k / 2k / 3.9k / 8.2k は Basic（C23193 / C21190 / C22975 / C23018 / C25981） | MIT |
| 映像バッファ | ORB v0.3 | CLC4007 単電源 +5V、非反転 利得 1 + 1k/470 = 3.13倍、出力 51Ω 直列 | ビデオアンプは Basic に1件も無い | MIT |
| 映像バッファ | Console JAMMAizer | THS7375 + 約 475Ω 可変 | ビデオアンプは Basic に1件も無い | 記載なし |
| 同期 | ORB v0.3 | P8-28 → 1k/470Ω 分圧 → CLC4007 第4ch 利得 1 + 1k/330 = 4.03倍 → CSync（直列抵抗なし） | ノートに記載なし | MIT |
| 同期 | DE10Jamma | GPIO → 100Ω 直列 → 13b | 100Ω（0603、C22775）は Basic | 記載なし（LICENSE ファイル無し＝再利用は要許諾） |
| 同期 | jammanator-pi | V/H を各 4k7 + 10µF で平均化し 74HC86 で XOR（極性正規化）、さらに XOR で合成 → 100Ω → P。74HC86 は +5V 給電 | 74HC86（SN74HC86PWR C2872580）は Extended・在庫 1,098 | MIT |
| 同期 | RP2040 公式 VGA demo | GPIO → 47Ω（H/V 別） | ノートに記載なし | MIT |
| 同期 | jzdziarski Atari IF | SN74LS86 XOR + 470Ω | ノートに記載なし（Basic の 74 系ロジックは 74HC14・74HC595 だけ） | 非商用教育目的のみ |
| 音声 | ORB v0.3 | PAM8403 モジュール L+ → 10、L− → L（BTL）、入力に 2kΩ トリマ（3362P）× 2、電源 5V | PAM8403DR-H（C17337）は Extended | MIT |
| 音声 | DE10Jamma | PWM → 560Ω + 10nF × 2段 RC → JP1 Mono/Stereo → 470nF → TDA7496（+12V）→ 各 ch 1000µF 結合で 10a "SPEAKER_R" / 10b "SPEAKER_L"。DC 音量 RV1 50k | BOM の部品はすべて Extended（1000µF の C442834 は在庫 0） | 記載なし（LICENSE ファイル無し＝再利用は要許諾） |
| 音声 | jammanator-pi | Pi PWM → 220Ω → 100nF → 470nF → 10k 2連ポット → PAM8403 モジュール（+5V）。L+/L− を JP4/JP5 経由で 10 / L（BTL） | PAM8403DR-H（C17337）は Extended | MIT |
| 音声 | PiPicoJamma | PAM8610 モジュール用スロット | ノートに記載なし | GPL-3.0 |
| 音声 | RP2040 公式 VGA demo | GPIO → NC7WZ16（TLV70033 給電）→ 220Ω → 100Ω + 100nF to GND → 47µF → 出力（1.8k to GND） | ノートに記載なし | MIT |
| 音声 | Console JAMMAizer | LM386 | LM386MX-1（C23573）・LM386G-S08-R（C85119）は Extended | 記載なし |
| 音声 | jzdziarski Atari IF | LM386N-1 @+5V、10k ポット → 2.2k → IN+、pin1–8 間 10µF（利得 200）、出力 1000µF 結合 → 10、L = GND、Zobel 10Ω + 0.1µF | LM386 は Extended、アルミ電解も Basic に無い | 非商用教育目的のみ |
| 電源保護 | RP2040 公式 VGA demo | ショットキー → VSYS | ショットキー B5819W SL（C8598）は Basic | MIT |
| 3.3V 生成 | ORB v0.3 | BBG 内 | —（BeagleBone Green の内部） | MIT |
| 3.3V 生成 | DE10Jamma | DE10 内 | —（DE10-Nano の内部） | 記載なし（LICENSE ファイル無し＝再利用は要許諾） |
| 3.3V 生成 | jammanator-pi | LM1117-3.3 | LM1117IMPX-3.3（C23984）は Extended。AMS1117-3.3（C6186）は Basic | MIT |
| 3.3V 生成 | PiPicoJamma | Pi/Pico 内 | —（Pi / Pico の内部） | GPL-3.0 |
| 3.3V 生成 | RP2040 公式 VGA demo | Pico 内 SMPS + TLV70033（音声用） | —（Pico の内部。TLV70033 の分類はノートに記載なし） | MIT |

**参照回路に使える部品の JLCPCB 分類（2026-11-10、JLCPCB API）**

| 用途 | 部品 | C 番号 | クラス | JLCPCB 在庫 | 確度 |
|---|---|---|---|---|---|
| 入力プルアップ・直列（4連アレイ） | 0603x4 1k 4D03WGJ0102T5E / 4.7k / 10k 4D03WGJ0103T5E | C20197 / C1980 / C29718 | Basic | 542,341 / 1,753,865 / 1,132,412 | 確認済 |
| 抵抗アレイ 470Ω | 0603x4 470R | C25510 | Preferred Extended | 116,840 | 確認済 |
| 入力クランプ（シリコン） | BAV99 | C2500 | Basic | 1,104,445 | 確認済 |
| 入力クランプ（ショットキー） | BAT54S | C7420333 | Preferred Extended | 555,145 | 確認済 |
| 同 | BAT54C | C22466350（クラス再検証ノート）／ BAT54C,215 C37704（オープン回路ノート） | Preferred Extended | 1,086,900 / 388,716 | 確認済（C 番号が2つある） |
| 同（jammanator 使用品） | BAT54S,215 | C47546 | Extended（非 Preferred） | 279,739 | 確認済 |
| 小信号 NPN | MMBT3904 | C20526 | Basic | 4,313,904 | 確認済 |
| NPN | S8050 J3Y / SS8050（1.5A） | C2146 / C2150 | Basic | 1,309,621 / 3,059,537 | 確認済 |
| N-MOSFET | AO3400A / 2N7002 | C20917 / C8545 | Basic | 992,725 / 5,867,377 | 確認済 |
| P-MOSFET（逆接保護） | AO3401A / SI2301CDS | C15127 / C10487 | Basic | 1,638,278 / 300,062 | 確認済 |
| ダーリントンアレイ | ULN2003ADR | C7512 | Basic | 368,016 | 確認済 |
| ショットキー | SS54（5A）/ SS34（3A）/ SS14 / B5819W SL | C22452 / C8678 / C2480 / C8598 | Basic | 1,735,691 / 2,938,768 / 1,610,469 / 727,407 | 確認済 |
| フライバック | 1N4148W / M7（1A 1kV） | C81598 / C95872 | Basic | 3,471,971 / 5,410,796 | 確認済 |
| TVS（+5V 用、双方向） | SMBJ6.5CA / P6SMB6.8CA | C7420377 / C78395 | Basic | 1,139,871 / 677,118 | 確認済 |
| ESD アレイ 12V 2線 | PSM712-LF-T7 | C32677 | Basic | 117,440 | 確認済 |
| TVS 5V 単方向 | SMBJ5.0A | C19077558 | Extended（Preferred） | 105,845 | 確認済 |
| ESD アレイ | SRV05-4 | C85364 | Preferred（Extended） | — | 確認済 |
| 5V → 3.3V LDO | AMS1117-3.3 | C6186 | Basic | 1,538,727 | 確認済 |
| シュミットインバータ | 74HC14D | C5605 | Basic | 315,750 | 確認済 |
| OP アンプ | LM358DR2G / NE5532DR / TL072CDT / LM324DT | C7950 / C7426 / C6961 / C71035 | Basic | 521,642 / 268,192 / 136,065 / 56,626 | 確認済 |
| DAC 用抵抗 0603 1% | 470Ω / 510Ω / 1k / 2k / 3.9k / 8.2k / 75Ω | C23179 / C23193 / C21190 / C22975 / C23018 / C25981 / C4275 | Basic | 3,885,962（470Ω）/ — / 25,401,324（1k）/ 8,470,828（2k）/ — / — / 1,500,609（75Ω） | 確認済 |
| 0603 1% Basic の他の値 | 100/120/150/200/220/270/300/330/390/510/560/680/820Ω、1.2k/1.5k/1.8k/2.2k/2.4k/2.7k/3k/3.3k/3.6k/3.9k/4.7k/4.99k/5.1k/5.6k/6.2k/6.8k/7.5k/8.2k/9.1k/10k ほか | 個別の C 番号はノートに無い（3.3k などは未確認） | Basic | — | 確認済（クラス） |
| 0805 抵抗 | 1k / 220Ω / 4.7k / 100Ω | C17513 / C17557 / C17673 / C17408 | Basic | 40,279,436 / 787,604 / 4,331,213 / 7,070,465 | 確認済 |
| 同期の直列抵抗 100Ω（0603） | 100Ω | C22775 | Basic | — | 単一出典（オープン回路ノートの参照回路表） |
| MLCC | 100nF 0603 / 10nF 0603 / 470nF 0603 / 22µF 25V 0805 / 47µF 6.3V 0805 / 100µF 6.3V 1206 | C14663 / C57112 / C1623 / C45783 / C16780 / C15008 | Basic | — | 確認済 |
| タンタル | 100µF 6.3V B / 10µF 16V A | C16133 / C7171 | Basic | 626,406 / 888,516 | 確認済 |
| フェライト | BLM18PG121SN1D（2A） | C14709 | Basic | 1,859,597 | 確認済 |
| 音声アンプ | PAM8403DR-H / PAM8302AASCR / NS4150B / LM386MX-1 / LM386G-S08-R / HT6872 / TDA2822M / LM4871 | C17337 / C113367 / C189961 / C23573 / C85119 / C93112 / C725341 / C7494970 | すべて Extended | 3,388 / 20,707 / 161,685 / 4,590 / 8,208 / 28,179 / 5,171 / 15,988 | 確認済 |
| ポリスイッチ／ヒューズ | nSMD200 / BSMD1812-200 / SMD1812P200TF / 0466003.NRHF / 0451005.MRL / Polyfuse 1812 1.1A / Polyfuse 1206 | C70085 / C883156 / C21010 / C14165 / C48467 / C269134 / C269108 | すべて Extended | — / — / — / — / — / 392,129 / 255,577 | 確認済 |
| アルミ電解 | 100µF 25V（D6.3 × L7.7mm） | C970685 | Extended | 20,174 | 確認済 |
| ロジック | 74HC165D / 74HC245D / SN74LVC4245APWR / 74HC86D / 74LVC244 | C5613 / C5625 / C7859 / C52140393 / C6079 | Extended（前3つは Preferred） | 214,412 / 52,801 / 53,630 / — / 24,825 | 確認済 |
| USB Type-C 16P | USB-C 16P | C393939 | Extended | 340,763 | 確認済 |

**秋月電子の手はんだ部品（確認済、2026-11-10）**

| 部品 | 販売コード | 価格 | 在庫 | 仕様（商品ページ） |
|---|---|---|---|---|
| LM386G-D08（DIP-8） | 114548 | ¥40 | 11,965 | 700mW（9V 8Ω THD10%）、4-12V、利得 46dB 固定 |
| LM386G-S08 | 114549 | ¥30 | 12,469 | SOP8 |
| M2073G-D08（NJM2073 互換、2回路 BTL 可） | 117431 | ¥40 | 4,992 | 1.8-15V、BTL 2.0W（9V 16Ω） |
| TDA2822L-D08 | 109720 | ¥50 | 27,759 | 1.8-12V、0.65W × 2 / BTL 1.35W |
| NJM2113D | 111192 | ¥60 | 555 | 低電圧動作パワーアンプ |
| AE-PAM8012（D級モジュール） | 108217 | ¥300 | 692 | 2.5-5.5V、8Ω で最大 1.0W / 4Ω 2.0W @5V、短絡・過熱保護、10.5 × 11mm、スルーホール端子 |
| PAM8302AADCR（D級 IC） | 114187 | ¥40 | 2,378 | SMD |
| MF-R300（リセッタブルヒューズ 3A、トリップ 6A、30V） | 112630 | ¥40 | 2,766 | |
| RGEF300（ポリスイッチ 3A、トリップ 5.1A、16V） | 100769 | ¥30 | 5,947 | |
| MF-R185（1.85A） | 112629 | ¥40 | 在庫あり | |
| 1N4007 | 108332 | ¥10 | 在庫あり | |
| 電解 470µF 16V / 1000µF 10V / 1000µF 25V | 108426 / 108424 / 117885 | ¥10 / ¥20 / ¥40 | 25,462 / 5,164 / 30,594 | |
| USB Type-C（USB2.0 16P）5077CR-16-SMC2-BK-TR | 114356 | ¥110 | 209（在庫僅少） | |

## 3. 選択肢の比較

### 3.1 基板の分け方（金フィンガーと PCBA の区分）

1枚あたりの金額は、ドナー機（部品取り用のファミコン）を除く概算で、推論を含む。

| 案 | かかるもの | リスク | 判断 |
|---|---|---|---|
| 一体基板（JAMMA フィンガを本体基板に作る） | Standard PCBA が確定（Setup $25.56、ステンシル $8.21、Basic にも1種類 $1.53 の装填料）。Basic 20種のみ + 秋月手はんだで 5枚 約¥6,800 / 10枚 約¥5,170、Basic + Preferred + Extended 32種で 約¥8,830 / ¥6,800 | 「Basic のみ」の経済的な根拠（装填料無料）が消える | **推奨**（推論）。基板間の中継が無く、嵌合と配線の信頼性が高い |
| 分離基板（金指のエッジ基板 + Economic PCBA の本体） | 約¥7,570 / ¥6,200。本体の PCBA を Basic のみにすると 約¥5,110 / ¥4,350（最安）。エッジ基板は5枚 $24.90 / 10枚 $29.30 | JAMMA 信号 約 40 本と電源を基板間で手はんだ中継する。嵌合の信頼性が落ちる。電源 4接点分の電流を中継コネクタで通す | 不採用（推論） |
| エッジパッドあり・Gold Fingers: No | 見積上は Economic PCBA が選べた（PCB 価格 $38.60） | 面取りが無く挿入性が落ち、コネクタを傷めるおそれ。Gerber 審査で Standard へ再分類されるかは未確認 | 不採用（推論） |

### 3.2 タング幅

| 案 | かかるもの | リスク | 判断 |
|---|---|---|---|
| 公称 114.4mm（通常公差 ±0.2） | 追加費なし | 114.2〜114.6 になり JST の上限は超えないが、JST の下限を最大 0.2mm、Hirose の下限を最大 0.4mm 下回る。片側 0.2mm の横ずれはフィンガ半幅 1.15mm に対して小さい | **推奨**（推論） |
| 公称 114.6mm（第2パスの値） | 追加費なし | Hirose の下限と JST の上限にちょうど一致し、製造公差の余裕が無い。大きすぎると入らない | 不採用（推論） |
| 公称 114.5mm + 精密公差 ±0.1 | 精密公差の費用と指定方法は未確認 | JST の範囲に完全に入る | 費用が分かれば検討（推論） |

### 3.3 音声アンプ

| 案 | かかるもの | リスク | 判断 |
|---|---|---|---|
| PAM8302AASCR（C113367、Extended、在庫 20,707）を PCBA で実装 | Extended 1種。5V 電源、部品が少ない | 2.5W @ 4Ω と GND への短絡保護がデータシートで未確認 | **第一候補**（推論）。確認が取れてから採用 |
| 秋月 AE-PAM8012（108217、¥300）を手はんだ | 手はんだ1点 | 短絡・過熱保護は商品ページに明記、4Ω 2.0W @5V。手はんだが要る | **第二候補**（推論） |
| M2073G-D08（秋月 117431、¥40）を +12V で BTL | 部品は安い | 短絡保護の情報が無い。+12V 線のサージで MVS のアンプが壊れた事例がある | 不採用（推論） |
| LM386 のシングルエンド（L = GND、出力 1000µF 結合） | オープン基板の実例あり | +5V では約 0.25〜0.3W しか出ない。L を GND にするので筐体側が L を何かに接続していないことが前提 | 不採用（推論） |

### 3.4 コインカウンタとロックアウトの駆動素子

| 案 | かかるもの | リスク | 判断 |
|---|---|---|---|
| AO3400A（C20917、Basic）のローサイド、還流ダイオード（1N4148W C81598 または M7 C95872、Basic）のカソードを +12V へ | 1チャンネル1個。+12V（6/F）をダイオードのためだけに配線 | 正確な耐圧と 3.3V ゲートでの RDS(on) は未確認 | **推奨**（推論）。+5V と +12V のどちらのコイルにも使える |
| ULN2003ADR（C7512、Basic） | 1個で7チャンネル、クランプダイオード内蔵、MVS で量産実績 | VCE(sat) が 100mA で typ 0.9 / max 1.1V あり、日本の主流の +5V カウンタには約 4V しかかからない | 不採用（推論） |
| 還流ダイオードのカソードを +5V へ | — | +12V カウンタの筐体ではコイル → ダイオード → +5V に常に電流が流れ、カウンタが通電しっぱなしになる | 不可（推論） |

### 3.5 入力回路のプルアップとクランプ

| 案 | かかるもの | リスク | 判断 |
|---|---|---|---|
| 3.3kΩ@3.3V（1.0mA）+ 10nF + 直列 1kΩ + BAV99 | 0603 1% の 3.3k は Basic（C 番号は未確認）、BAV99 C2500 は Basic | BAV99 はショットキーよりクランプ電圧が約 0.3V 高く、RP2350 の入力定格に対する余裕は未確認 | **推奨**（推論） |
| 10kΩ（DE10Jamma・jammanator-pi の実績値） | 4連アレイ C29718（Basic） | 10kΩ@3.3V では 0.33mA で、コインのマイクロスイッチの最小負荷 1mA に届かない | 不採用（推論） |
| 1kΩ の4連アレイ（C20197、Basic、3.3mA） | アレイで部品数が減る | 3.3mA を流す。Neo Geo の CRE401 と同じ 1k だが、導電ゴム接点には 1k は少し強すぎるという指摘がある（単一出典） | 4連アレイにしたい場合の代替（推論） |
| 4.7kΩ の4連アレイ（C1980、Basic） | — | 0.70mA で 1mA に届かない（プルアップとしては不可）。直列抵抗として使えば 12V 混入時に 3.3V 系へ流れ込む電流を減らせる | 直列抵抗を 4.7kΩ に上げる案は、クランプの余裕が足りないときの対策（推論） |
| BAT54S（C7420333、Preferred Extended）でクランプ | Extended 1種 | — | BAV99 で定格に余裕が無い場合の代替（推論） |

### 3.6 同期出力と RGB DAC

| 案 | かかるもの | リスク | 判断 |
|---|---|---|---|
| 同期: MMBT3904（C20526、Basic）のオープンコレクタ + 5V へ 1kΩ 程度のプルアップ + 直列 100Ω | Basic 部品だけで組める | 極性が反転するので、マイコンは正極性で出す。High 約 4.6V（12kΩ 負荷）、Low 0.4V 以下 | **推奨**（推論） |
| 同期: 3.3V の GPIO から直結（DE10Jamma 方式） | 部品なし | 日本の筐体での実績は確認されていない | 試作で比べる（推論） |
| 同期: 74HC14 を 5V で使って昇圧 | Basic | 3.3V 入力は 74HC の入力しきい値の保証外 | 不採用（推論） |
| RGB DAC: 6bit/色の単一値 R-2R（470Ω C23179、Basic） | 1色 17 本の抵抗 | 出力抵抗 約 235Ω で実在基板（100〜150Ω）より高く、モニタの入力インピーダンスで明るさが少し変わる（2kΩ で約 2.91V、4.7kΩ で約 3.09V） | **推奨**（推論）。将来の色数増加に備えられる |
| RGB DAC: 5bit の2進重み（510Ω / 1k / 2k / 3.9k / 8.2k、すべて Basic） | 部品が少ない | 並列 ≈ 260Ω、2kΩ 負荷で ≈ 2.9V。6bit 目（約 16k）の Basic 品はノートで未確認 | 部品数を優先するなら（推論） |

## 4. ユーザー要求ごとの判断

判断と推奨はすべて推論である。

| 要求 | 判断 | 理由 | 推奨 |
|---|---|---|---|
| 部品は Basic Parts のみ | できない | 音声アンプ IC、アルミ電解、ポリスイッチ、ビデオアンプ、BAT54 系、USB Type-C 端子が Basic に無い。金フィンガー付きは Standard PCBA で、Basic にも装填料がかかるので、Basic に限る経済的な理由も消える。 | Basic で済む箇所（入力保護、カウンタ駆動、電源保護、DAC）は Basic で揃え、Basic に無い部品は Extended を PCBA で載せる。ユーザーの了承が必要 |
| LCSC で豊富な在庫がある部品 | 条件つきでできる | 推奨部品の多くは在庫が数十万個以上ある。一方、jammanator-pi の 475Ω（C228851）は在庫 3、ULN2803ADWR（C9683）は在庫 0 で使えない。 | 既存設計の部品をそのまま写さず、部品分類表の C 番号から選び直す |
| 手はんだ部品は秋月で在庫があるもの | できる | AE-PAM8012（692 個）、MF-R300（2,766 個）、1N4007、電解コンデンサが秋月にある。Type-C 端子 114356 は在庫 209 で僅少。 | 手はんだはアンプモジュールなど最小限にとどめる |
| 全部を基板実装メーカーに実装してもらう | 条件つきでできる | 一体基板 + Standard PCBA なら Extended 部品も PCBA に載せられる。分離基板にすると基板間の中継を手はんだすることになる。 | 一体基板 + Standard PCBA |
| 実際に作れる安価な基板 | 条件つきでできる | 一体基板は1枚 約¥5,170〜¥6,800（10枚）で、最安の分離基板（約¥4,350）より高い。基板は 100 × 100mm を超えるので JLCPCB の最安枠に入らない。 | 信頼性を優先して一体基板 |
| JAMMA 端子 | できる | ピン配列、寸法、電源は嵌合コネクタのメーカー図面と日本の筐体の配線図で確認できている。タング幅だけは実ハーネスでの確認が要る。 | 2.2 節のフットプリント設計値で作る |
| 通常制と時間制を選べる | できる | 方式・形式で使う JAMMA 入力（レバー、ボタン1〜4、スタート、コイン）は同じ回路で受けられ、違いはファームウェアの割り当てだけになる。 | JAMMA 側の入力回路は全入力共通にする |
| タイマー方式（市販ソフト用） | 条件つきでできる | 入力の割り当てとコインでの時間加算はファームウェアで実現できる。時間切れ後の扱いと残り時間の表示は要求で未定で、JAMMA には表示用の信号が無いので映像に重ねて描く必要がある。 | コイン1・コイン2のどちらでも時間を加算し、Service（R）は時間を加算してカウンタは進めない |
| 通常方式・デフォルト形式 | できる | コイン → SELECT、スタート → START などはファームウェアの割り当てで済む。コインのパルス（25〜100ms）は一定幅に整形して渡せる。 | コインは Low ≥ 10ms で確定し、一定幅に整形して待ち行列から出す |
| 通常方式・特殊形式 | 条件つきでできる | ボタン4（25/c）は JAMMA の正式規格外で、筐体にボタン4が配線されていないと使えない。Astro City は SW4 として配線しているが、筐体ごとの違いは未確認。 | 25/c と 26/d は入力専用（プルアップ付き）にし、設置先の配線を確かめる |
| 切り替え手段はソフトウェア | できる | 方式と形式はファームウェアの設定値として不揮発メモリに保存し、Test スイッチ（15）で設定画面を開ける。マルチスロット MVS の配線の筐体では 15 が Coin #3、Test が M になるおそれがある。 | 設定画面は 15 の長押しで開き、USB からも開けるようにする。方式・形式用の DIP スイッチ（JLCPCB では Extended の C319050 / C99418 しかない）は置かない |
| CPU/PPU とラズパイのどちらを挿したかの設定 | 未確定 | この指示は方式・形式の切り替えとは別で、置き換えられていない。JAMMA 側には影響しない。 | 他の分野の判断に従う |
| Raspberry Pi を複数枚・将来の CPU/PPU/メモリ更新 | 条件つきでできる | JAMMA 側の制約は 56 接点の固定割り当てと +5V 4接点（1接点 3A）だけで、Pico 2 を複数枚載せても筐体の +5V（5〜7A）に余裕がある。フル機能の Raspberry Pi の消費電流は未確認。必要な入力 23〜25 本とカウンタ・ロックアウトの出力 4 本は1枚の Pico では足りない。 | 入出力専用の Pico を置き、JAMMA の入出力回路を CPU/PPU 側の構成と切り離した共通ブロックにする。ステレオ化などは JAMMA を通さず別端子にする |
| USB Type-C でファームウェア更新 | 条件つきでできる | Type-C 16P（C393939）は Extended で、秋月品（114356）は在庫僅少。JAMMA 端子には影響しない。 | VBUS と JAMMA の +5V を B5819W SL（C8598、Basic）で分け、端子はタングの反対側の辺に置く。更新は筐体の電源を切って USB 給電だけで行う手順にする |

## 5. ユーザーに決めてもらうこと、次に確かめること

### 5.1 ユーザーに決めてもらうこと

1. 「Basic のみ」の例外を認めるか。推奨の既定: Basic に無い部品（音声アンプ、ポリスイッチ、Type-C 端子など）は Extended を PCBA で載せる。
2. 基板を一体にするか、金フィンガーのエッジ基板を分けるか。推奨の既定: 一体基板 + Standard PCBA。
3. 音声アンプを PCBA の Extended 品（PAM8302AASCR）にするか、秋月のモジュール（AE-PAM8012）の手はんだにするか。推奨の既定: PAM8302AASCR の短絡保護が確認できればそれ、できなければ AE-PAM8012。
4. 音声出力が約 2W 級（目標の 3W に届かない）でよいか。推奨の既定: 筐体側に音量ボリュームがあるので 2W 級で進め、実機で音量を確かめる。
5. 米国式の筐体向けにロックアウト（9/K）のドライバも載せるか。推奨の既定: カウンタと同じドライバを載せる（日本の筐体では使われないことが多い）。
6. タイマー方式の時間切れ後の扱いと残り時間の表示方法（要求で未定）。推奨の既定: 残り時間は映像に重ねて表示する。
7. 要求で補った前提のうち、JAMMA 側に関わるもの（2P スタートを I コンの SELECT にする、デフォルト形式では筐体の C・D ボタンを使わない、コイン1・コイン2のどちらでも時間を加算する）でよいか。推奨の既定: 補ったとおり。

### 5.2 次に確かめること（この順に）

1. PAM8302A のデータシートで 4Ω での出力と GND への短絡保護を確かめ、試作では L を GND に落とした筐体を模した負荷で BTL 出力を短絡させ、アンプが保護停止して壊れないことを確かめる。
2. RP2350（Pico 2）の GPIO の入力電圧の絶対最大定格を調べ、BAV99 のクランプで定格を超えないかを確かめる。AO3400A の耐圧と、3.3V ゲートでの RDS(on) をデータシートで確かめる。
3. 試作基板を Astro City などの実ハーネスに挿し、タング幅 114.4mm とキー溝 3.0 × 11.5mm で挿入感・横ずれ・接触を確かめる。日本製の実物 JAMMA 基板のフィンガ寸法もノギスで実測する。
4. Astro City（MS8 系）と New Astro City / Egret II（MS9 系）で、15.7458 kHz / 60.0985 Hz に同期するか、画面位置・明るさを確かめる。同期はトランジスタ出力（5V）と 3.3V 直結の両方で試す。
5. 本基板だけを載せた状態で筐体の +5V が安定するか、筐体電源が保護停止しないかを測り、起動時と定常の +5V 消費電流を測ってポリスイッチの定格を決める。
6. 筐体のカウンタのコイル抵抗を測り、ON 100ms で確実に1カウント進むかを確かめる。オシロでコインスイッチの波形とパルス幅を測る。
7. 設置先ごとに、ハーネスの 25/c・26/d の配線と、マルチスロット MVS の配線（11/M/15/S）になっていないかを確かめる。
8. JLCPCB に、精密公差 ±0.1 の費用と指定方法、BOM を入れた Standard PCBA の実見積を問い合わせる。

## 6. 主要出典

### 1章（結論）と 2章（表）: ピン配列・寸法・JLCPCB
- Arcade Otaku Wiki「JAMMA」（ピン表、入出力の意味）: https://wiki.arcadeotaku.com/w/JAMMA
- NeoGeo Dev Wiki「JAMMA connector pinout」（1スロットとマルチスロット MVS の配置）: https://wiki.neogeodev.org/index.php?title=JAMMA_connector_pinout&action=raw
- Astro City 取扱説明書（拡張ボタン、電源、コインカウンタ、スピーカーの配線）: https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf
- Egret II 配線図（SPARE 配線、COUNTER、VOL.）: https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg
- Windy 束線図（SPARE 配線、GX-06PD、SOUND VOLUME）: https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg
- JST GEC データシート（JAMMA 準拠の適合基板図）: https://datasheet.octopart.com/GEC-561-JST-datasheet-180492417.pdf
- Hirose CR7 シリーズ カタログ（適合基板図、本体寸法、定格）: https://s1.dtsheet.com/store/data/002648525.pdf
- MisterJamma/DE10Jamma（フットプリント、入力・DAC・音声の実設計）: https://github.com/MisterJamma/DE10Jamma
- JLCPCB Help「JLCPCB Gold Fingers」（ENIG 条件、面取り角、セットバック、マスク）: https://jlcpcb.com/help/article/jlcpcb-gold-fingers
- JLCPCB PCBA Capabilities（Economic は Gold Fingers 非対応）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- JLCPCB 発注ページ（実見積、選択肢）: https://cart.jlcpcb.com/quote

### 1章と 2章: 電源・映像・音声・入力・コイン
- New Astro City 取扱説明書（電源容量、V.ADJ、CONTRAST）: https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf
- Blast City（Bass Fishing 版）取扱説明書（2kΩ/3.0Vp-p と 75Ω/0.7Vp-p の切替）: https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf
- Arcade Otaku Wiki「Sega Blast City Wiring Guide」（映像極性・同期、−5V 非供給）: https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide
- Wells-Gardner K7000 サービスマニュアル（同期範囲、入力インピーダンス）: https://dn760108.eu.archive.org/0/items/k-7000-1/K7000-1_text.pdf
- NESdev Wiki「PPU frame timing」（ドット飛ばし）: https://www.nesdev.org/w/index.php?title=PPU_frame_timing&action=raw
- etim.net.au「AV-Driver Arcade」（speaker− は GND ではない）: https://etim.net.au/av-driver/arcade/
- Omron D2MC データシート（金接点の最小負荷 5VDC 1mA）: https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2mc.pdf
- Cyber Lead 取扱説明書（AD-81P3、NX-06PD 5VDC）: https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf

### 2章（参考回路と部品分類）と 3章（選択肢）
- KabukiFlux/jammanator-pi（入力保護、R-2R DAC、同期、BTL 音声）: https://github.com/KabukiFlux/jammanator-pi
- ole00/orb（入力ダイオード、DAC + バッファ、PAM8403）: https://github.com/ole00/orb
- TI ULN2003A データシート（VCE(sat)）: https://www.ti.com/lit/ds/symlink/uln2003a.pdf
- JLCPCB 部品ライブラリ API（クラス、在庫、価格）: https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- 秋月電子 AE-PAM8012: https://akizukidenshi.com/catalog/g/g108217/

### 4章（ユーザー要求ごとの判断）
- JLCPCB「PCB Prototype Assembly」（PCBA 料金表）: https://jlcpcb.com/solutions/pcb-prototype-assembly
