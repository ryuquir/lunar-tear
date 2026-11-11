# JAMMA インターフェース（56ピン配列・寸法・電源・映像・音声・入力・コイン） - リファレンスシート

- **エッジ**: ピッチ 0.156in 系（3.96mm）、片面 28 接点、部品面が 1〜28、はんだ面が A〜f です。7/H はキー溝で、パッドを置きません。本シートは**ピッチ 3.96mm、差し込み部の幅 114.4mm（公称）、フィンガ幅 2.3mm、キー溝 幅 3.0mm、板厚 1.6mm、JLCPCB では ENIG + Gold Fingers: Yes + 30° 面取り**を推奨します（推論）。ピッチ・フィンガ幅・板厚は JST GEC と Hirose CR7 の両方の公差に入りますが、タング幅は両社の範囲が 114.6 の1点でしか重ならないための妥協値で、Hirose の下限（114.6）を下回ります（第2パスの推奨値 3.9624mm / 114.6mm から変えた理由は 1.2 節）。
- **電源**: 本基板は電源として +5V（3/4/C/D）だけを使い（+12V の 6/F はコインカウンタの還流ダイオード用にだけ配線。4.3 節）、GND は 8 接点（1/2/27/28/A/B/e/f）をすべて使います。日本の筐体の多くは −5V を供給しますが、本基板では使いません。嵌合コネクタ（JST GEC、Hirose CR7、Sullins）の1接点あたりの定格は 3A です（JAMMA 規格書そのものの値は未確認）。
- **映像と音声**: 映像は正極性アナログ RGB で、2kΩ 負荷に約 3Vp-p（黒 0V、DC 結合）を出します。同期は P ピンに負極性コンポジット同期を出します。音声は 10（+）と L（−）の間に BTL（ブリッジ）で出し、**L を GND とみなしてはいけません**。11/M は無接続にします。
- **入力とコイン**: 入力はすべて GND に落ちるとアクティブ（アクティブ Low）です。プルアップ、直列抵抗、コンデンサ、クランプを入れずに 3.3V マイコンへ直結してはいけません。日本の筐体のコインカウンタは +5V 系が主流です。ロックアウト（9/K）は配線されていないことが多いです。
- **部品**: 金フィンガー付きの基板は JLCPCB の Standard PCBA になります。音声アンプ IC、アルミ電解コンデンサ、ポリスイッチは JLCPCB Basic に1件もありません。

データの日付: 2026-11-10（すべての調査ノートの取得日）

用語: 「部品面」は部品を載せる面（KiCad の F.Cu、表面）、「はんだ面」は裏面（B.Cu）です。「フィンガ」はエッジ端子の銅パッド、「タング」は基板のうちコネクタに差し込む凸部（差し込み部）、「肩」はタングの付け根で基板が広がる位置です。「BTL（Bridge-Tied Load）」はスピーカーの両端を逆相の2出力で駆動する方式で、どちらの端子も GND ではありません。「プルアップ」は入力線を抵抗で電源側に引いておく回路です。

確度の表記:
- **確認済**: 独立した2つ以上の出典、またはネットリスト・データシート・メーカーの取扱説明書・ライブデータ（JLCPCB API など）で確認できたもの。
- **単一出典**: 出典が1つだけのもの（フォーラム、ブログ、検索要約経由のものを含む）。
- **未確認**: 出典で確認できていないもの。
- **推論**: 調査ノートまたは本シートの工学的判断で、出典の事実ではないもの。

---

## 1. 確定事実

### 1.1 JAMMA 56ピンの全ピン表

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
| 11 | Audio +（プリアンプ出力、ほぼ未使用） | M | Audio GND | 単一出典の食い違いあり | ブログ1件は 11/M を "No connection" とする。MVS 配線の筐体は 10/L と 11/M でステレオ |
| 12 | Video Red | N | Video Green | 確認済 | |
| 13 | Video Blue | P | Video Sync（負極性コンポジット） | 確認済 | |
| 14 | Video GND | R | Service Switch | 確認済 | Service はクレジット +1（カウンタは増えない） |
| 15 | Test Switch | S | Tilt（Slam）Switch | 確認済 | Test でテストモード。Tilt は多くのゲームで未実装 |
| 16 | Coin 1 | T | Coin 2 | 確認済 | GND へのパルス |
| 17 | 1P Start | U | 2P Start | 確認済 | |
| 18 | 1P Up | V | 2P Up | 確認済 | |
| 19 | 1P Down | W | 2P Down | 確認済 | |
| 20 | 1P Left | X | 2P Left | 確認済（多数派） | 旧 ArcadeControls wiki の表は 20/21（X/Y）の Left/Right が逆との指摘がある（検索スニペット、単一出典） |
| 21 | 1P Right | Y | 2P Right | 確認済（多数派） | 同上 |
| 22 | 1P Button 1 | Z | 2P Button 1 | 確認済 | |
| 23 | 1P Button 2 | a | 2P Button 2 | 確認済 | |
| 24 | 1P Button 3 | b | 2P Button 3 | 確認済 | |
| 25 | (1P Button 4) 非公式 JAMMA+ | c | (2P Button 4) 非公式 | 確認済（入力として使われること） | Astro City は "1P SW 4 / 2P SW 4"、Egret II と Windy は "1P SPARE 1 / 2P SPARE 1" として配線。Neo Geo MVS は Select 系、CPS2 などは 4人目用に流用 |
| 26 | (1P Button 5) 非公式／未使用 | d | (2P Button 5) 非公式／未使用 | 食い違いあり | Hardware Book 版は "Not used"、pinouts.ru 版は Button5。Astro City は "1P SW 5 / 2P SW 5"、Egret II と Windy は "1P SPARE 2 / 2P SPARE 2" |
| 27 | GND | e | GND | 確認済（多数派） | pinouts.ru 版のみ 27/e = Button6。Hardware Book 版と Arcade Otaku は GND |
| 28 | GND | f | GND | 確認済 | |

**情報源の間の食い違い（まとめ）**

| 箇所 | 食い違いの内容 | 本シートの扱い |
|---|---|---|
| 5/E（−5V） | 規格書原本で −5V が規定かは未確認。国内の配線表はすべて −5V。供給しない筐体もある | 本基板では無接続 |
| 11/M | Audio +/GND（Arcade Otaku 等）と "No connection"（ブログ）。MVS 配線の筐体ではステレオの片チャンネル | 無接続（ハイインピーダンス） |
| 25/c、26/d | Button4/5、"Not used"、SPARE1/2、MVS の Select 流用と各種 | 入力専用（プルアップ付き）にする。出力・電源・GND に使わない |
| 27/e | pinouts.ru 版のみ Button6 | GND として扱う |
| 20/21（X/Y） | 旧 ArcadeControls wiki で Left/Right が逆との指摘 | 20 = Left、21 = Right（多数派） |
| 制定年 | 英語版 Wikipedia は 1985 年、日本語 Wikipedia と wdic は 1986（昭和61）年 | 設計に影響しない。未解決 |

**用語の注意（確認済）**: 「JAMMA VIDEO規格」は JVS（新 JAMMA、RS-485/USB）の正式名で、56ピンの JAMMA（JS）規格とは別物です。JAIA の公式「資料」ページに 56ピン JAMMA 規格書はありません。規格書の原本は未入手です。

### 1.2 エッジコネクタの寸法と向き

#### 1.2.1 嵌合コネクタ（メス側）のメーカー図面が規定する適合基板寸法

| 項目 | JST GEC（GEC-561、"conforns to the JAMMA standards"） | Hirose CR7E-56DB-3.96E（CR7 カタログ「PCB Dimensions 3.96 pitch」図） | Sullins EBM28D 系（.156" [3.96mm]） | 確度 |
|---|---|---|---|---|
| ピッチ | 3.96 ± 0.05 | 3.96 ± 0.05 | 0.156" | 確認済 |
| 1〜28 の両端フィンガ中心間 | 106.92 ± 0.05 | 106.98 ± 0.08（56極） | A = 4.212" = 106.98mm（両端コンタクト間） | 確認済（食い違いあり。下記） |
| フィンガ幅 | 2.3 ± 0.035（"(.091 ± .001)"。上側の同じ寸法は "2.3 ± 0.35" と印刷されており誤植と読める。電気的実装ノートはこの寸法をキー溝幅と読んでいたが、図では1本のフィンガの両端に引かれている） | 2.3 ± 0.1 | 記載なし | 確認済（JST・Hirose。JST は本シートで図面を再確認） |
| タング（差し込み部）の幅 | 114.6（+0/−0.2） | 114.8（0/−0.2） | 本体開口 B = 4.532" = 115.11mm | 確認済（食い違いあり。下記） |
| 基板厚 | 1.6 ± 0.15mm | 1.6 ± 0.15 | .062" ± .008"（1.57mm ± 0.20mm） | 確認済 |
| 先端の面取り | 先端断面 C0.5、肩 C0.5（図面読み取り） | 先端は両面 C0.5（0.5mm × 45°）、タング外側の角も C0.5 | 記載なし | 確認済 |
| キー溝 | Circuit 7 と H に "Mis-insertion preventive key groove"。溝の詳細図で幅 3.0（.118）、深さ 10.0（.394）（公差の記載なし） | コンタクト位置に置く溝: 幅 2.5 +0.1/0、深さ 11 +0.5/0、入口両側 C0.5、溝中心はコンタクト中心線上。別にコンタクト間に置く狭い溝 1 +0.1/0（深さ 10） | 極性キー "PLM-K2 KEY IN CONTACT" 厚 .093" [2.36]、"PLA-K1 KEY IN BETWEEN CONTACTS" 厚 .030" [0.76] | 確認済 |
| 外端フィンガ中心→タング側面 | 3.84 +0/−0.1（1番と A 番の両方に記入。114.6 = 106.92 + 2 × 3.84 と整合） | （114.8 − 106.98）/ 2 = 3.91（計算） | 記載なし | 確認済（JST） |
| 肩までの距離 | タング長 10.0、肩の切り欠きの奥行き 10.0 min.、タング外側の切り欠き幅 10.0 min.（図面読み取り。寸法線の起点は図からの判読） | 図で 10（先端からタングの付け根まで、図の読み取り） | 記載なし | 確認済（JST と Hirose の図が一致） |
| 挿入深さ | 記載なし | 基板挿入深さ 8.5 | "INSERTION DEPTH .265 [6.73]" | 確認済 |
| 接点位置 | 記載なし | 個別図面（CR7E-30DB-3.96E(72)）で「5.3±0.4（接点位置）」→ 基板端から約 3.2 ± 0.4mm で接触（推論: 8.5 − 5.3） | 未確認 | 単一出典＋推論 |
| 定格電流 | "Current rating: 3A AC, DC" | "Current rating: 3A" | "3 Amps current rating for one contact energized (for 5 Amps application, consult factory)" | 確認済 |
| その他の定格 | 250V AC, DC、接触抵抗 初期 15mΩ max／環境試験後 30mΩ max、適合電線 AWG #24〜#16、接触部は金めっき | 600V AC、接触抵抗 15mΩ max（100mA）、挿抜 500回後も 15mΩ max、−30〜+85℃ | 30 milli Ohms maximum at rated current | 確認済 |
| 接点めっき | 金めっき | 接触部 Ni2.5µm + Au0.2µm、実装部 Ni2.5µm + Sn2µm、絶縁体ポリカーボネート UL94V-2 | 標準 "B = .000010" Gold"（0.25µm）、オプション .000030"（0.76µm） | 確認済 |
| 本体寸法 | — | CR7E-56DB-3.96E（アイレット）／-3.96DS（スルーホール）: 全長 A = 133.7、取付穴間 B = 126、C = 118.1、基板挿入口長 D = 115、E = 106.92（27 × 3.96）、本体厚 F = 11.1、G = 117.1、本体高さ 12、総高 19.4、取付穴 φ3.3 | C = 118.16、取付穴間 D = 126.11、全長 E max = 135.48 | 確認済 |

補足（確認済）:
- Hirose には 4mm ピッチの 56極品 CR7C-56DB-4E／-4DS が実在します（適合基板: フィンガ幅 2.3 ± 0.1、ピッチ 4 ± 0.05、56極 A = 108.0、B = 107.8。B < A なので表の誤記の可能性があり、未確認）。「古い基板は 4mm ピッチ」という説の直接証拠（具体的な基板名と実測）は見つかっていません（単一出典のフォーラム投稿のみ）。
- Hirose のキー部品: CR7C-GPIN（厚 0.5、POM）、CR1-GPIN（厚 2.0、幅 2.5、ABS）、HIF5B-GPIN（厚 0.5）。厚 2.0 品がコンタクト位置用の 2.5mm 溝に対応すると推定されます（推論: 寸法の一致から）。
- Digi-Key では CR7E-56DB-3.96E(72) が "Obsolete" 表示です（検索要約経由、単一出典）。Digi-Key の EBM28DRXH は 56 positions、Card Thickness 0.062"（1.57mm）、Pitch 0.156"（3.96mm）、Contact Finish Thickness 10.0µin です。
- 端子番号は 1〜28 / A〜f で、"G, I, O, Q, g, i, o, q" は不使用です（Hirose）。"LETTERS G, I, O & Q NOT USED"（Sullins）。

**食い違い1: 両端フィンガ中心間（ピッチの真値）**
- Hirose（56極 A = 106.98 ± 0.08）と Sullins（4.212" = 106.98mm）はインチ基準 0.156in = 3.9624mm です。一方、JST GEC は 106.92 ± 0.05（3.96 × 27）で、Hirose カタログの本体寸法 E も 106.92 です。
- 第2パスのエッジ寸法ノートは JST の図面を見ずに 3.9624mm を推奨しましたが、3.9624 × 27 = 106.985 は JST の許容範囲（106.87〜106.97）を 0.015mm 外れます。
- 3.96mm × 27 = 106.92 は JST の範囲にも Hirose の範囲（106.90〜107.06）にも入ります。DE10Jamma の実基板も 3.96 一定（1↔28 = 106.92）で動いています。
- **判断（推論）: ピッチは 3.96mm を採用します。** どちらの規格書もデータシートで、証拠の強さは同等です。両方を同時に満たす値を選びました。

**食い違い2: タング幅**
- JST GEC は 114.6（+0/−0.2）、すなわち 114.4〜114.6 です。Hirose は 114.8（0/−0.2）、すなわち 114.6〜114.8 です。両者が重なるのは 114.6 の1点だけです。
- JLCPCB の外形公差は CNC ルーティングで ±0.2mm（通常）／±0.1mm（精密）です（検索要約経由）。
- 大きすぎると入らず、小さすぎても横ずれが増えるだけです（推論、エッジ寸法ノート）。Sullins の開口は 115.11 です。
- JST の図は外端フィンガ中心からタング側面までを 3.84 +0/−0.1（3.74〜3.84）と規定しており、114.6 +0/−0.2 と同じ条件を片側ずつ指定しています。
- **判断（推論）: 公称 114.4mm を採用します。** 通常公差 ±0.2 でも 114.2〜114.6 になり、JST の上限を超えません。ただし下側は JST の下限 114.4（片側 3.74）も最大 0.2mm 下回り、Hirose の下限より最大 0.4mm 細くなります。片側 0.2mm の横ずれはフィンガ半幅 1.15mm、接触幅約 2mm に対して小さいです。第2パスの推奨値 114.6mm は Hirose の下限と JST の上限にちょうど一致しますが、製造公差の余裕がありません。JLCPCB の精密公差 ±0.1 を指定できるなら、公称 114.5mm（114.4〜114.6）で JST の範囲に完全に入れる選択肢もあります（推論。精密公差の費用と指定方法はノートに無く未確認）。

**食い違い3: キー溝**
- JST は幅 3.0・深さ 10.0（公差の記載なし）、Hirose は幅 2.5 +0.1/0・深さ 11 +0.5/0 です。実在する 3 設計は 2.5〜3.81 × 10〜11.5 です。第2パスの電気的実装ノートは JST の溝幅を 2.3 ± 0.035 と読んでいましたが、これはフィンガ幅の寸法の読み違いでした（本シートで JST の図面を再確認）。
- 溝はキーより広く深ければ挿さります。キーの厚さは Sullins 2.36、Hirose CR1-GPIN 2.0 です。JST のキー部品 GEC-PK2 の図には 2.3 と 1.6 の寸法があります（どちらが厚さかは図からは未確認）。
- **判断（推論）: 第2パスの推奨値（幅 3.0mm、深さ 11.5mm）を維持します。** すべてのキー厚とすべての深さ規定を満たします。

#### 1.2.2 公開されているフットプリントの実ファイル（実測値）

座標はファイルから計算したものです。「先端からパッドまで」は Edge.Cuts の先端線からパッド先端までの距離です。いずれもネットリストや基板ファイルからの実測なので、各値は確認済（そのファイルについて）です。

| 項目 | DE10Jamma（KiCad） | jzdziarski Universal JAMMA Edge（KiCad 9） | ORB orb03（gEDA） |
|---|---|---|---|
| ピッチ | 3.96 一定（1↔28 = 106.92） | 手置きで不均一 3.92〜4.01、1↔28 = 106.84 | 3.956 一定（1↔28 = 106.812） |
| フィンガ幅 | 2.35 | 2.2 | 2.032（80mil 角アパーチャ） |
| フィンガ長 | ライブラリ版 8.0 / 基板埋込版 10.0 | 10.0 | 9.652（300mil 線 + 80mil 角） |
| 先端からパッドまで | 基板版 0.05（ライブラリ版を同位置に置くと 1.05） | 1.13 | 約 0.1 |
| キー溝 幅 × 深さ | 3.0 × 10.0 | 2.5 × 11.5 | 3.81（150mil） × 10.92（430mil） |
| キー溝中心と7番中心 | 一致（174.584） | 179.25 vs 理想 179.19 | 4700mil vs 4698mil |
| タング幅 | 114.6（基板幅そのもの） | 111.0（基板幅そのもの） | 113.03、角に 25mil 面取り |
| 外端フィンガ中心→タング側面 | 3.84 | 約 2.08 | 2.99 / 3.23（非対称） |
| 肩の深さ | 肩無し（全幅） | 肩無し（全幅） | 約 12.07（475mil、肩に 50mil 面取り） |
| 基板厚 | 1.6 | 1.6 | 1.6（"Board thickness: 1.6 mm", "Copper thickness: 1 oz"） |
| マスク | 先端〜10.05mm の帯を F/B 両面で全面開口 | パッド単位開口 | パッド単位（mask 2.0mm） |

- DE10Jamma のライブラリ `JAMMA-56.kicad_mod` はパッド 2.35 × 8 で、裏パッドのレイヤ指定が "B.Cu B.Mask F.Mask" です。基板ファイルに埋め込まれた版は 2.35 × 10 で、裏パッドが "B.Cu F.Paste F.Mask"（B.Mask が無い）です。裏面マスクは別の B.Mask ポリゴンで開けて救っています。そのままコピーすると裏フィンガがマスクで覆われたりペーストが載ったりするおそれがあります（推論）。
- estechnical/jammakludge の `JAMMA-56.kicad_mod` は DE10Jamma 版と同一形状で、独立した出典とは数えません。
- yoonjustin/WinchesterPCB の `JAMMA56HALF` はスーパーガン側のメスコネクタ用で、ゲーム基板のフィンガではありません。
- jzdziarski/jamma のライセンスは "educational use only" で、寸法の参照だけに使えます。
- Frank_fjs の JAMMA フィンガーボードは "124mm x 40mm", "2 layer PCB", "Four M3 mounting holes." で、JLCPCB で製造し "They pass through a cps2 board on my astro city without a hiccup." とされます（単一出典。寸法値は非公開）。

**向きの決まり（確認済）**
- 部品面（F.Cu、表面）に 1〜28、はんだ面（B.Cu、裏面）に A〜f を置きます。同じ番号の表裏（1↔A、2↔B …）は同じ X 位置です。3 設計と日本語の配線表（「部品面 1〜28 / はんだ面 A〜f」）で一致します。
- 部品面を見て端子端（先端）を下にすると、1番が左端、28番が右端です。先端を上にすると 1番が右端です。
- キー溝は 1番側から 7番目（6 と 8 の間、7/H 位置）にあります。
- 筐体に設置したときの向き（部品面が上か横か）は筐体の取付板しだいで、規格化されていません（未確認）。

#### 1.2.3 本基板のフットプリント設計値（作図できる粒度）

座標系: 原点は 1番パッドの中心線と基板先端線の交点です。X+ は 28番方向、Y+ は基板内側（先端から奥）です。部品面を見て先端を下にした図で、1番が左、28番が右になります。

第2パスのエッジ寸法ノート第6節の推奨値を基準にし、ピッチ・タング幅・それに連動する値だけを 1.2.1 節の判断で変えました。変えた行は「本シートで変更」と書いてあります。

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

- フットプリントは両面の SMD パッドだけにし、Edge.Cuts（タング・キー溝・肩）は基板側で描くほうが、KiCad の DRC 設定と干渉しにくいです（推論。DE10Jamma もフットプリントの外で描いています）。
- コネクタ本体は基板面から約 4.75mm（Hirose 本体厚 11.1 から）張り出し、本体の耳（全長 133.7〜135.5mm）はタング両脇へ約 9.5〜10mm はみ出します（推論、エッジ寸法ノート）。
- 筐体側: Astro City 2 の基板取付板は約 48 × 40cm・厚さ約 1cm の木板で、電源位置のため余裕が少ないという記述があります（単一出典、検索要約経由）。基板はプラスチック製の基板足で板に固定するのが一般的です（単一出典）。取付穴・最大寸法の JAMMA 公式規定は見つかっていません（未確認）。
- 基板が 100 × 100mm を超えるので、JLCPCB の 100 × 100 以下の最安枠には入りません（推論）。

### 1.3 JLCPCB での金フィンガーの指定方法と制約

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

日本への送料は OCS Express $8.66（5枚、0.64kg）／$10.09（10枚、1.17kg）、UPS $9.79 / $9.88 です（確認済）。

PCBA の料金（確認済、2026-11-10）: Setup fee は Economic $8.18、Standard $25.56（片面）／$51.12（両面）。ステンシルは $1.53 / $8.21（片面）・$16.42（両面）。装填料は「$3.07 Extend / $1.53 Basic/Extend」で、Standard では "all basic and extended components require feeder loading"。Economic では Basic と Preferred（UI 表記は Promotional Extended）が無料です。装填料の単位は料金表には書かれていませんが、JLCPCB の公式ブログは "The charge applies per part number, per order, regardless of quantity."、"Standard PCBA charges a loading fee on every unique part, Basic or Extended." と書いています（単一出典の公式ブログ）。手はんだ人件費は公式内で $3.50（プロトタイプページ）と $3.58（料金記事）が不一致です。両方が該当する注文では Standard の総額が Economic より $14.93 以上高くなければ差額が handling fee として加算されます。

その他（確認済／単一出典）:
- JLCPCB の別ブログには "bevel the board down to about 1/3 to 1/2 of its thickness" や「フィンガと外形の距離 0.5mm」「1.0mm 以上」の併記があり、ヘルプ記事と食い違います。2026-11-10 更新のヘルプ記事（1.13 / 0.74mm）を優先します。
- 一般値として硬質金は 0.5〜1.5µm、ENIG の金は 0.05〜0.1µm です（JLCPCB ブログ）。IPC の厚み規定は未確認です。
- JLCPCB の ENIG フィンガでカートリッジを量産し接点摩耗の報告がないという利用者投稿があります（単一出典）。JAMMA 基板の挿抜は設置時と交換時の数回〜数十回なので、ENIG で実用上足りる見込みです（推論）。コネクタ側の金は 0.2〜0.25µm で、基板が ENIG でも金対金の接触になります（推論）。
- JAMMA_2player_xbox360 の作者は "I recommend ENIG as the surface finish and Gold Fingers checked with 30º angle chamfer as well." と書いています（単一出典）。

### 1.4 電源

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

- New Astro City の取扱説明書: "Using any Board which requires power in excess of the above-mentioned capacity is not allowed."、"V. ADJ. : DC Power Supply voltage (+5V) adjustment volume (V.R.)"、"V.ADJ. has been adjusted at the time of shipment from the factory. Use the settings as is ... Changing the settings without a good reason can cause damage to the IC Board"（確認済）。
- RT-65A: "INRUSH CURRENT (Typ.) COLD START 50A/230VAC"、"when multi-channel output, it is recommended that CH1 load > 10%."（確認済）。
- 古いスイッチング電源の最小負荷: "a lot of switchers require a minimum load, typically on the +5V line, usually around 0.5A"、"older switching supplies tended to measure high when unloaded ... sometimes ... hit the over voltage protection and shut down"。ダミー負荷は 5V に 10Ω（500mA）が経験則（単一出典、フォーラム）。Sega 400-5198 などの最小負荷と OVP は未確認です。
- 汎用フォーラムの目安最小容量（+5V 12A / +12V 2A / −5V 1A など）は確度が低く、日本の筐体の実値（上表）が優先します（単一出典）。
- DE10Jamma: "If +5v rail is adjusted too high, the DE10-Nano's over-voltage protection circuitry will not allow the board to power up."（確認済）。調整式の +5V を上げると他のレールも連動するという報告があります（単一出典）。
- 参考: ファミコン本体の専用 AC アダプタ HVC-002 は "DC10V 850mA"（任天堂公式の仕様表、検索要約経由、単一出典）。
- 挿抜時のホットプラグ対策（エッジの長短ピン）は JAMMA にはありません（推論）。挿抜は電源 OFF で行います。

**−5V の扱い**: 本基板では −5V（5/E）を使わず、無接続にします（推論、第1パスから変更なし）。日本の筐体の多くは −5V を供給するので、5/E を GND や他の信号につないではいけません。

**オープン基板の電源保護（確認済）**: 調べたオープン JAMMA 基板（ORB、DE10Jamma、jammanator-pi、PiPicoJamma ほか）には、ヒューズ・TVS・逆接保護を持つものがありませんでした。jammanator-pi は JAMMA +5V（3、4、C、D）から LM1117IMPX-3.3 で 3.3V を作ります。DE10Jamma は +5V（3a/3b/4a/4b）を 2.1mm DC ジャックで DE10-Nano へ送ります。cspang1/jcap（JAMMA エッジ無し）は P-MOSFET IPP80P03P4L-04 で逆接保護しています。Raspberry Pi 公式の RP2040 参考設計は外部 +5V を MBR120VLSFT1G（ショットキー）経由で Pico の VSYS に入れます。Pico のデータシートは "VSYS ... allowed range 1.8 V to 5.5 V"、"The simplest way to safely add a second power source to Pico is to feed it into VSYS via another Schottky diode" と書いています。

### 1.5 映像

#### 1.5.1 信号レベルと入力インピーダンス（筐体・モニタ別）

JAMMA 規格は映像レベルを標準化していません。レベルの違いはモニタ側の CONTRAST（ゲイン）と入力切替で吸収する運用です（確認済）。

| 筐体／シャーシ | 映像入力・同期・周波数 | 確度 |
|---|---|---|
| Sega Blast City（Bass Fishing 版取説 p.49、29" 3-mode Nanao MS-2931） | SW3 で切替: "When inputting D-SUB MINI 15P: 75Ω / 0.7Vp-p"（ON）、"When inputting AMP 6P: 2kΩ / 3.0Vp-p"（OFF）。SW1/SW2 で 15kHz/24kHz/31kHz モード。"correct images can not be obtained unless the settings of the horizontal frequency or video input connector (input impedance/input level) are compatible with the board." | 確認済（取扱説明書） |
| Sega Blast City（JAMMA 変換） | "Video Signal = POSITIVE, 3.0Vp-p, 2kΩ Impedance & SYNC = NEGATIVE, H/V Composite"、制御出力インピーダンス 8Ω | 確認済（取説と Arcade Otaku） |
| Sega Astro City（取説 p.8、ナナオ 200-5242-15/-24、三和電気 200-5243-15/-24） | "SYSTEM 24 用の水平周波数 24.83 KHz の中解像度モード(24Kモード)と通常の GAME BD 用の水平周波数 15.7 KHz の低解像度モード(15Kモード)を切り替えられます。モードの切り替えはモニターメイン基板のコネクタを差し替える" | 確認済（取扱説明書） |
| Sega New Astro City（420-6294-01 p.17、NANAO 200-5242-15-04 / -24-04） | "When replacing the GAME BD, the above-mentioned monitor frequency change and ④CONTRAST adjustment may be required depending on the game contents." | 確認済（取扱説明書） |
| Namco Cyber Lead（取説 p.68） | "対応ゲームPCボード JAMMA VIDEO規格(JVS)ゲームPCボード(水平同期周波数 15.75kHz, 24.83kHz) *JAMMA規格ゲームPCボードは、オプション対応により使用可能" | 確認済（取扱説明書） |
| Taito Egret II（配線図 W1000310B） | 映像レベルの記載なし。VIDEO Assy 29INCH は R, G, BL, SYNC, GND | 確認済（配線図）／レベルは未確認 |
| Konami Windy（束線図 5-10） | 映像レベルの記載なし。29inch MONITOR は SYNC, GND, BLUE, GREEN, RED | 確認済（配線図）／レベルは未確認 |
| Wells-Gardner K7000 | "RGB analog, [1?] to 5v peak-to-peak (adjustable with contrast control), 4.7k ohm input impedance"（OCR が崩れ、下限値は不確か）。オプション "RGB analog 0-0.75v, 75 ohm input impedance"。水平 "15.1 kHz to 16.8 kHz standard"、垂直 "47 Hz to 63 Hz" | 確認済（サービスマニュアル） |
| Hantarex MTC 9000 | "RGB anal/TTL compat., positive, white (high-level)、2-5 V p.p. (by use of input switch)"、"The three RGB video amplifiers are d.c. coupled"。水平 "15-16 kHz"（調整範囲 "15.625 +/- 0.3 kHz"）、垂直 "45-70 Hz" | 確認済（マニュアル） |
| Hantarex MTC 900 | 約 1〜10 Vpp（抽出テキストが崩れている）、校正目標 "1 Vpp ±5%" | 単一出典（検索要約経由） |
| Nanao MS9-29 | 入力レベル・インピーダンスは未確認。15kHz / 24kHz（手動切替、最終世代は自動）。"The MS9's PLL is known for being fairly robust"、"Strange scan rates and sync pulse widths / placements are handled with grace"、垂直ホールド調整は無い。リモート基板の Contrast は "unity gain control across all three video channels" | 単一出典 |
| Nanao MS8 | 利用者報告: "0.7V RGB and -0.3V Csync" の組合せで RGB に 270Ω、同期に 680〜750Ω を直列に入れる案。Astro City のモニタのリモート基板には "video impedance" 切替スイッチがあり、誤ると極端に明るいか暗い画面になる | 単一出典（フォーラム） |

- 一般論: アーケードの RGBS は "TTL level amplitude (3-5 Vpp)"、モニタ入力は "(1-5k ohms)"（etim.net.au）または "1k-10k ohms"（gbs-control wiki）。家庭用は 0.7Vpp/75Ω（確認済: 複数の二次資料）。
- 1992 年の記事は "tentative AMOA standards" がロジック基板の最大映像出力を 2V としていたと紹介しています。初期の任天堂ゲームは負極性（反転）映像で、Sanyo モニタには "video inverter" 基板（2SC1815 × 3）が載っていました（単一出典）。
- モニタの型式（筐体データベース、単一出典）: Astro City = Nanao MS8-29FSG?、New Astro City / Versus City = Nanao MS9-29A、Egret II = Nanao MS9-29T、Windy = Toshiba PB-6643（15/24kHz）、Windy II = Toshiba PB-7534（15/24/31kHz）、Exceleena 2 = "29 Nanao MS8. TOEI TCL2xx. SANWA PM1745"、Neo Candy 29 = Hitachi GMK-29FS2、Egret 3 = Toshiba K29CQ50（15/24/31kHz）、Cyber Lead = Nanao MS9?、Cyber Lead II = Nanao 15/24/31kHz。

**75Ω/0.7Vp-p の位置づけ（確認済）**: Blast City の 75Ω/0.7Vp-p は同じモニタの D-SUB15 入力（NAOMI など）側の設定で、JAMMA（AMP 6P）側ではありません。JAMMA 基板が狙うのは 2kΩ/3.0Vp-p 側です。

#### 1.5.2 実在する JAMMA 基板の RGB 出力段

| 基板 | 出力段 | 確度 |
|---|---|---|
| Neo Geo MVS | 74LS273 ラッチと 74LS05 で抵抗 DAC を駆動。"The output isn't lowered like on the AES. It goes straight to the JAMMA edge as a 0~3.5V signal for the high-impedance inputs on arcade monitors."。抵抗は "resistances[] = {3900, 2200, 1000, 470, 220}"、dark ビットは 8200Ω、shadow は 150Ω のプルダウン。家庭用 AES は "2200 / (6800 + 2200)" で分圧し "~0.9Vp-p max" | 確認済 |
| Sega 16bit 系 | "Bit 0 = 1 x 3.9K ohm / Bit 1 = 1 x 2.0K ohm / Bit 2 = 1 x 1.0K ohm / Bit 3 = 2 x 1.0K ohm / Bit 4 = 4 x 1.0K ohm"。別のビットが 3ステートバッファと 470Ω で明るさを半分または2倍にする | 確認済（MAME ソース） |
| Capcom CPS1 | RGB は LS07/LS367 バッファ → 抵抗アレイ。緑の RA6〜RA11 が約 0.1k/0.22k/0.47k/1k/2.2k/4.7kΩ（会員の実測） | 単一出典（フォーラム） |
| CPS2 / Taito F3 / Konami | 未確認 | 未確認 |

- DAC の合成出力インピーダンスは Neo Geo ≈ 119Ω、Sega ≈ 129Ω です（推論・計算）。開放 3.5V の Neo Geo を 2kΩ に入れると約 3.3V、75Ω に入れると約 1.35V になります（推論・計算）。
- 出力をトリマで調整する慣習は基板側にはありません。筐体のモニタの CONTRAST/GAIN で合わせます（確認済）。
- 75Ω/0.7Vp-p への変換はスーパーガン側の仕事です。従来の可変抵抗アッテネータでは基板から見た負荷が "75-575 ohms depending on the pot position" と重くなり、AV-Driver は 10k の多連ポットとバッファで負荷を軽くしています（単一出典）。Axunworks Supergun Mini に Neo Geo MV1C をつなぎ、ポット最大・75Ω 終端で "1.2v on the scope"（単一出典）。
- Console JAMMAizer の RGB 出力インピーダンス調整トリマ: "In stock form they are adjusted to approximately 475ohms but you can adjust them anywhere from 1Kohm all the way down to 0ohms. For most monitors the stock settings will look great"（確認済: 取扱説明書とフォーラム）。モニタに 75Ω/1kΩ 切替がある場合は "it needs to be set to 1kohm if using an amp"（単一出典）。

#### 1.5.3 同期信号

| 項目 | 内容 | 確度 |
|---|---|---|
| 形式 | 負極性 TTL レベルのコンポジット同期（H/V 合成）を P ピンに出す。Low ≒ 0V、High ≒ 4〜5V | 確認済 |
| 日本の筐体の配線 | 1本の SYNC 線だけ: Astro City のカラーディスプレイ・コネクタは RED/GREEN/BLUE/SYNC/GND(SYNC) の5線。Egret II は "R, G, BL, SYNC, GND"。Windy は "SYNC, GND, BLUE, GREEN, RED" | 確認済（配線図） |
| K7000 | "Sync: TTL positive or negative going, separate or composite. Input impedance: 20K ohms for positive going sync; 12K ohms for negative going sync."、"If the sync signal is composite, use the horizontal sync input of the same polarity" | 確認済 |
| MTC 9000 | 同期振幅 "1.5 - 5 V p.p."、極性はスイッチで切替。"Contact 6 horizontal or composite sync"、"Contact 5 vertical sync (or no connexion if using composite sync)" | 確認済 |
| Nanao / Toei | 同期入力の閾値と入力インピーダンスは未確認 | 未確認 |
| 民生機器向け | 同期は "high-voltage TTL" で、民生機器向けには 470Ω を直列に入れる | 単一出典 |
| H/V 分離 | 必要になるのは Blast City の D-SUB15（31kHz/NAOMI）など JAMMA 以外の入力の場合 | 確認済 |

#### 1.5.4 モニタの同期範囲とファミコンのタイミング

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

### 1.6 音声

| 項目 | 内容 | 確度 |
|---|---|---|
| スピーカー端子 | 10（Speaker +）と L（Speaker −）。モノラル、アンプ後の出力で、筐体側にアンプは不要（基板側にパワーアンプが必要） | 確認済 |
| L は GND ではない | "On mono JAMMA boards, the speaker- pin is not connected (this isn't ground)."。"ALL jamma boards use bridged amplifiers where sp- is never ground"、片側を接地するとアンプが壊れる（言い過ぎを含み、反対意見もある） | 確認済（複数出典、ただし表現の強さは単一出典） |
| 筐体の配線 | 配線図の 10/L はどれも GND に接続されていない | 確認済（配線図） |
| 11/M | Audio +（プリアンプ出力、ほぼ未使用）/ Audio GND。MVS 配線の筐体は 10/L と 11/M でステレオで、JAMMA 基板を MVS 配線の筐体に入れるとアンプが焼けたという報告がある（二次） | 確認済（ピン名）／単一出典（事故報告） |

**筐体のスピーカーと音量**

| 筐体 | スピーカー | 音量の調整 | 確度 |
|---|---|---|---|
| Astro City | 前面パネルの LEFT と RIGHT にそれぞれ "8Ω 10W"（部品表 "130-5091 SPEAKER 8 OHM 10 SPL"）。コネクタの C 側で "A2×2"、"92×2" と束ねられる（並列で合成約 4Ω と読める、図面読み取り）。JAMMA 10（A, PINK）と L（90, GRAY）は電源ユニットの "SOUND" コネクタ → "SOUND VOL." → "SPEAKER" コネクタ（A2/92）の順 | 電源ユニットの SOUND VOL. | 確認済（取扱説明書） |
| New Astro City | — | "SOUND VOL. : Adjust the Speaker Volume." | 確認済 |
| Blast City（Bass Fishing 版） | "130-5156 SPEAKER BOX 8 OHM" | "220-5420 RHEO STAT 100 OHM 10W"、"SOUND VOLUME Adjust the Speaker Volume" | 確認済 |
| Egret II | SP(R) と SP(L) がどちらも "4Ω" | JAMMA の SPEAKER(+)/(−) は F3 SYSTEM(4P)・FX1 SYSTEM(4P) と並んで切替スイッチと "VOL." を通る | 確認済（配線図） |
| Windy | LEFT/RIGHT SPEAKER（インピーダンス未確認） | JAMMA 10（灰 8）と L（白 9）→ "SOUND VOLUME"（L-Ch / R-Ch の2連）。Konami 基板用の "STEREO SOUND (FOR KONAMI PCB)" コネクタ（NH-4）が別にある | 確認済（配線図）／インピーダンス未確認 |
| Cyber Lead | 2個、型番 "9AFOQS5WLA" | — | 確認済（部品表）／インピーダンス未確認 |
| Exceleena | 未確認 | 未確認 | 未確認 |

**実在する基板のアンプ（確認済、Neo Geo Dev Wiki）**: "Most arcade cabs don't have embedded audio amps."。MV1A は "Motorola MC13308T4"、MV1F/MV1FZS は "Hitachi HA13001. Stereo. 2x 5W in 4 ohms."、MV1B は "Toshiba TA8201AK. Mono. 1x ~7W in 4 ohms."、MV1C は "ST TDA7240. Mono 1x 20W in 4ohms."。"These components can die from overheating or voltage surges on the 12V line."。
- TA8201AK: BTL 構成で出力結合コンデンサが不要。"POUT = 17W at VCC = 14.4V ... RL = 4Ω"、"14W at VCC = 13.2V"（単一出典、検索要約経由）。
- TDA7240A: "20W BRIDGE AMPLIFIER FOR CAR RADIO"、"SHORT CIRCUITS TO GROUND AND ACROSS LOAD" の保護あり（単一出典、検索要約経由）。
- HA13001: "5.5W Dual / 17.5W BTL"（アグリゲータ、確度は低い）。

**アンプの出し方**: 実在する基板は BTL のカーオーディオ用 IC が多く、L は GND ではありません（確認済）。改造などでスピーカー − が GND に落とされている筐体では、BTL の負側出力が GND に短絡します（推論）。そのため GND への短絡保護を持つ BTL アンプを選びます（推論）。

**接地の注意**: スピーカー − を基板の GND に落とす設計（シングルエンド＋出力コンデンサ、L = GND）もオープン基板には実在します（jzdziarski Atari JAMMA Interface）。この場合は、筐体側が L を何かに接続していないことが前提です（推論）。

### 1.7 入力（プルアップ、フィルタ、保護）

| 項目 | 内容 | 確度 |
|---|---|---|
| 電気的性質 | 全入力が GND 接続でアクティブ Low。日本の筐体の入力はすべて無電圧接点で GND に落とす方式（Astro City / Egret II / Windy の配線図） | 確認済 |
| Neo Geo（CRE401） | "The leftmost pin's net pulls all outputs through 1k resistors. The 330 ohm resistors provide current protection (sometimes as fuses), the capacitors smooth out eventual spikes."。実測: R1 330Ω、R2 1kΩ、C1 は 33nF（-17）、35〜36nF（-18）、41〜43nF（-19）、42〜43nF（-2N）。"cut-off frequency of about 15kHz"。部品は "MODEL CR SERIES Single-In-Line ... Resistor/Capacitor Networks" の "-A Circuit" | 確認済 |
| DE10Jamma | JAMMA ピン → 1k 直列 → FPGA GPIO ノード、ノードに 10k プルアップ（+3V3）と 10nF to GND。全 28 入力同一（netlist 上 R86 のみ 1k プルアップで、誤記と思われる＝推論）。"Inputs are RC filtered ... to give EMI protection to the FPGA."、"No multiplexing, polling or debouncing of the inputs" | 確認済（netlist + README） |
| jammanator-pi | JAMMA ピン — 10k プルアップ（+3.3V、4連アレイ）— 100nF to GND（4連 C アレイ C62857）— 1k 直列（4連アレイ）— BAT54S（C47546、中点＝信号、両端＝+3.3V/GND のクランプ）— SN74LVC244APWR（C7668）— MCP23017（C558584）× 2。保護回路は 470Ω + 1N5711 + 100nF として検証 | 確認済（kicad_pcb） |
| ORB | JAMMA 入力 → スイッチングダイオード（カソードが JAMMA 側）→ BBG GPIO（内部プルアップ 3.3V）。図注 "JAMMA outputs either 0V (button pressed) or disconnected or 5V (either means b. released)"、"D1: fast switching diode 15V, 4ns"。BOM は "Diode switching 100V 0.15A 4ns SMD1206" × 24 | 確認済（回路図と BOM） |
| PiPicoJamma、JAMMA_2player_xbox360 | JAMMA 入力を Pico の GPIO に直結（抵抗・コンデンサ・保護素子なし）。後者のタイトル自体が "(cheap version, no protections)" | 確認済 |
| 筐体からの電圧混入 | "Ensure your Arcade Cabinet doesn't send 12v on the coin circuitry, a switch is only allowed here."（JAMMA_2player_xbox360 の作者） | 単一出典 |
| bad_raspi_jamma の自己批判 | "Limit JAMMA inputs to 3.3v PULLUP or IC is DEAD"、MCP23017 横: "IF POWERED VIA 3.3V MAX INPUT WILL BE 3.9V If 5v are coming from the JAMMA (pullup or transient) it will kill the IC" | 確認済（回路図の注記） |
| RP2040 の入力定格 | 絶対最大 "Voltage at IO VPIN -0.5 ... IOVDD + 0.5 V"（IOVDD max 3.63V）。ESD は HBM 2kV（全ピン）、FT ピンのみ 4kV。内蔵プルアップ RPU 50〜80kΩ（弱い） | 確認済（データシート） |
| RP2350（Pico 2）の入力定格 | このトピックのノートには記載なし。Pico 2 関連のシートで確認すること | 未確認 |
| その他 | "1K pullups are a little too strong for conductive rubber contacts, and the Neo Geo originals use 1k"（10k を使う例） | 単一出典 |
| 拡張ボタンの配線 | Astro City は 25/c/26/d を "1P SW 4 / 2P SW 4 / 1P SW 5 / 2P SW 5"、Egret II は "1P SPARE 1 / 2P SPARE 1 / 1P SPARE 2 / 2P SPARE 2" とし、S/S コネクタに "1P SPARE 3 / 2P SPARE 3"（キックハーネス）。Windy も "1P SPARE 1 / 2P SPARE 1 / 1P SPARE 2 / 2P SPARE 2" | 確認済（配線図） |
| 多重化の例 | pi2jamma: 74LS165 × 3 で 24 入力。cspang1/jcap: 10k SIP アレイ プルアップ（+3.3V）+ 74HC165 × 2 | 単一出典（各1件） |
| Service / Test / Tilt | Service（R）はクレジット +1（カウンタは増えない）、Test（15）でテストモード、Tilt（S）は多くのゲームで未実装。電気的詳細（Slam）は未確認 | 確認済（意味）／未確認（電気的詳細） |

### 1.8 コイン機構・コインカウンタ・コインロックアウト

#### 1.8.1 コイン入力の信号の性質

| 機構 | 内容 | 確度 |
|---|---|---|
| 日本の筐体の主流 | 旭精工 AD-81P 系のメカセレクタ＋マイクロスイッチ（COM/NO の無電圧接点）。New Astro City の AD-81P は「機械式」で、マイクロスイッチの "COM(コモン)と NO(ノーマリーオープン)だけ使用" | 確認済 |
| 旭精工 AD-81P2 | "メカ式1WAYドロップセレクター"、"硬貨投入間隔 0.5秒以上"。オプション "専用チャンネルブラケット:MODEL CB/81M マイクロスイッチ付"、"コイン投入防止ブロッカー:MODEL QL-102(DC12V、DC24V)" | 確認済（メーカー） |
| Cyber Lead の実機部品 | "コインセレクタ AD-81P3 ¥100"、"チャンネルブラケット CB/81M"、"デンシロック VM81-M"、"デンジカウンタ NX-06PD 5VDC" | 確認済（部品表） |
| 旭精工 D2MC-01F1 | "適応製品 コインセレクター(電子セレクターを除く)およびブラケット全製品"、"電気定格(125VAC) 0.5A"、"接触抵抗 100mΩ以下"、"許容動作頻度 機械的/240回/分 電気的/60回/分" | 確認済（メーカー） |
| Omron D2MC | D2MC-01 は "Gold alloy" 接点、**"Min. applicable load 5 VDC 1mA"**（銀接点の D2MC-5 は 5 VDC 160mA）、30 VDC 0.5A。レバーが長すぎると "improper switch resetting or contact chattering may occur" | 確認済（データシート） |
| 旭精工 AE-204D（電子セレクタ） | 電源 "DC24V(DC15.0~DC26.4V)" / "DC12V±5%(特別仕様)"。正貨信号 "信号電圧/DC30V(MAX) 信号電流/50mA(MAX) 信号パルス幅/50msec.±5msec." | 確認済（メーカー） |
| 旭精工 AE-192D | "信号パルス幅 72msec.±3msec."、"DC35V(MAX)" / "10mA(MAX)" | 単一出典（検索要約経由） |
| 汎用 HX-616 | "オープンコレクタ出力のよう"、パルス幅 "Fast/Medium/Slowでそれぞれ30msec/50msec/100msec程度"（オシロで観測）、電源 12V | 単一出典（ブログ） |
| 電子メック一般 | パルス幅は 25/50/75/100ms などから選べる。ある基板は約 100ms 以上でないとクレジットを認識しなかった | 単一出典（フォーラム） |
| チャタリング時間 | メカセレクタのマイクロスイッチの実測値は無い（Omron はレバー形状による、としか書いていない） | 未確認 |

#### 1.8.2 コインカウンタ（8/J）

| 項目 | 内容 | 確度 |
|---|---|---|
| 日本の筐体の電圧 | **+5V 系が主流**。Astro City: COIN METER（220-5412 MAG CNTR W/CONN）の線色は 30（YELLOW、電源 DC OUT1 の +5V と同じ色）と 80（BLACK、JAMMA 8）。JAMMA 側の表で J/9/K は "(COIN METER 2)(COIN LOCK OUT 1)(COIN LOCK OUT 2)" と括弧付きで配線されていない。Windy: "GX-06PD" の2線は赤（2、+5V の線色）と灰（8、JAMMA 8 COIN COUNTER1）、J/9/K は無配線。Cyber Lead: "デンジカウンタ NX-06PD 5VDC"。Egret II: JAMMA 8 = "COUNTER"、J/9/K の下に配線は無い | 確認済（Cyber Lead の部品表）／図面読み取り（Astro City・Windy・Egret II。220-5412 のコイル電圧は線色からの推定） |
| 米国系・MVS | "The counters typically have one pin hardwired to +12V"、通電と遮断を "both during a long enough time" で行う。NEO-F0 → ULN2003 のオープンコレクタで駆動 | 確認済 |
| Sega NAOMI Universal | カウンタが無いときは +5V と coin meter 線の間に 100Ω を入れて偽装する。12V を使うのは "Provided the coin meter accepts 12V" の場合だけ | 単一出典 |
| 電磁カウンタの一次仕様 | ライン精機 MZ シリーズ: "計数速度 20Hz"、"パルス幅(メーク比) 25ms(1:1)"、"電源 DC12V/24V"、"消費電力 DC1.2W"（公式ページ。検索要約の 50ms は誤記）。Kessler-Ellis の DC 電磁カウンタ（5 cps 品）は on 120ms / off 80ms、約 85mW | 確認済（ライン精機）／単一出典（KEP） |
| コイル抵抗 | 12V カウンタで 129.1Ω（利用者実測） | 単一出典 |
| 外付けダイオード | メーターに内蔵が無い場合 "You need to use an external 1N4004 or 1N4007 diode"、カソードを +12V 側・アノードを JAMMA 8 側。例 "KE-610 Counter DC12V"。Double JAMMA アダプタ: "The coin counter outputs are diode protected at both game boards." | 単一出典（各1件） |
| オープン基板の実例 | 調べたオープン JAMMA 基板（ORB、DE10Jamma、jammanator-pi、bad_raspi_jamma、PiPicoJamma、JAMMA_2player_xbox360、jzdziarski 13 枚、JammaMia 公開ピン配置）は**どれも 8/J と 9/K を駆動していない**。JammaMia: "A ULN2003 chip is used for the OUT signals ... Maximum current is 500mA and maximum voltage is +5V"、ただし同梱ピン配置では 8/J・9/K は "NC" | 確認済（各設計ファイル） |
| NX-06PD / GX-06PD | メーカーとコイル抵抗は未確認 | 未確認 |

#### 1.8.3 コインロックアウト／ブロッカー（9/K）

| 項目 | 内容 | 確度 |
|---|---|---|
| JAMMA/MVS の方式 | "Coin lockouts are typically coils hardwired to the 12V power supply. It's the game PCB's job to power them by grounding their second terminal"。"When powered, it allows an inserted coin ... When not powered ... the coin take the return path."（無通電時は返却側＝フェイルセーフ） | 確認済 |
| 日本の筐体 | Astro City、Egret II、Windy では 9/K と J が配線されていない（図面読み取り）。日本の「ブロッカー」はセレクタ側の部品 | 確認済（図面読み取り） |
| 旭精工のブロッカー | QL-102（CB/81M 用）は 12DC で "直流抵抗(Ω)=85±10% 電流(mA)=157以下"、24DC で "313±10% / 86以下"、"定格消費電力 約2W"。QM-5 は 12V 76Ω / 158mA 以下。QL-203 は 12V 100Ω / 120mA。SB-101 は 12V 57Ω / 210mA 以下 | 確認済（メーカー） |
| ブロッカーの極性 | 通電時に阻止するか受け付けるかはページに記載が無い。VM81-M の仕様も未確認 | 未確認 |

#### 1.8.4 駆動素子

| 素子 | データ | 確度 |
|---|---|---|
| TI ULN2003A | "500mA-rated collector current"、"High-voltage outputs: 50V"、"Output clamp diodes"（COM ピンに共通カソード）。VCE(sat) は IC = 100mA で typ 0.9 / max 1.1V、IC = 200mA で typ 1.0 / max 1.3V。VI(on) は IC = 200mA で 2.4V、250mA で 2.7V、300mA で 3V（VCE = 2V）。入力抵抗 2.7kΩ | 確認済（データシート） |
| ULN2003ADR（JLCPCB） | C7512、SOIC-16、Basic、在庫 368,016、$0.1444 | 確認済（ライブデータ） |
| AO3400A（JLCPCB） | C20917、SOT-23、Basic（N-MOSFET）。RDS(on) などの値はノートに無い | 確認済（クラス）／未確認（特性） |
| ULN2803ADWR | C9683、Preferred だが**在庫 0**。ULN2803A C845537 は Extended（在庫 180,482） | 確認済 |

### 1.9 実績のあるオープンハードウェアの回路例と部品の JLCPCB 分類

#### 1.9.1 プロジェクトごとの回路（設計ファイルから確認した事実）

| 項目 | ORB v0.3 | DE10Jamma | jammanator-pi | PiPicoJamma | RP2040 公式 VGA demo | Console JAMMAizer | jzdziarski Atari IF |
|---|---|---|---|---|---|---|---|
| ライセンス | MIT | 記載なし（LICENSE ファイル無し＝再利用は要許諾） | MIT | GPL-3.0 | MIT | 記載なし | 非商用教育目的のみ |
| EDA | gEDA | KiCad 5 | KiCad 8 | Fritzing | KiCad | DipTrace | KiCad 10 |
| 入力 | ダイオード（カソード→JAMMA）+ SoC 内蔵プルアップ 3.3V | 1k 直列 + 10k PU(3.3V) + 10nF | 10k PU(3.3V) + 100nF + 1k + BAT54S + 74LVC244 | 直結 | （該当なし） | （コントローラ側） | 74LS04 等 |
| RGB DAC | 5bit 2進重み 510 / 1k05 / 2k2 / 4k7 / 10k を GPIO（3.3V）から加算、終端 R 200Ω, G 220Ω, B 270Ω to GND。74HC4066（5V）で各色 1bit を同期に連動して切替 | 6bit R-2R、全抵抗を単一値 "2R" にし R は 2R 2本並列。回路図 2R = 475Ω / BOM 2R = 604Ω（Bourns CAY16-6040F4LF 4連） | 6bit R-2R、R = 240Ω（C17572）、2R = 475Ω（C228851）、0805 1%。図中 TODO "BUFFER to avoid RGB drifting depending on monitor input impedance" | 6本の抵抗 8.2k / 4.3k / 2.2k / 1k / 510 / 180Ω（±5% THT）を並列加算 | 5bit（G は 6bit）2進重み 8.06k / 4.02k / 2k / 1k / 499Ω | （アナログ入力） | （アナログ入力） |
| バッファ | CLC4007 単電源 +5V、非反転 利得 1 + 1k/470 = 3.13倍、出力 51Ω 直列 | なし | なし | なし | なし（75Ω 系） | THS7375 + 約 475Ω 可変 | — |
| 2kΩ 負荷のフルスケール（推論・計算） | ≈ 4.3V（OP アンプの出力振幅制限は未確認） | ≈ 2.8〜2.9V | ≈ 2.9V | ≈ 3.1V | ≈ 2.9V | 未確認 | — |
| 同期 | P8-28 → 1k/470Ω 分圧 → CLC4007 第4ch 利得 1 + 1k/330 = 4.03倍 → CSync（直列抵抗なし） | GPIO → 100Ω 直列 → 13b | V/H を各 4k7 + 10µF で平均化し 74HC86 で XOR（極性正規化）、さらに XOR で合成 → 100Ω → P。74HC86 は +5V 給電 | 未確認 | GPIO → 47Ω（H/V 別） | — | SN74LS86 XOR + 470Ω |
| 音声 | PAM8403 モジュール L+ → 10、L− → L（BTL）、入力に 2kΩ トリマ（3362P）× 2、電源 5V | PWM → 560Ω + 10nF × 2段 RC → JP1 Mono/Stereo → 470nF → TDA7496（+12V）→ 各 ch 1000µF 結合で 10a "SPEAKER_R" / 10b "SPEAKER_L"。DC 音量 RV1 50k | Pi PWM → 220Ω → 100nF → 470nF → 10k 2連ポット → PAM8403 モジュール（+5V）。L+/L− を JP4/JP5 経由で 10 / L（BTL） | PAM8610 モジュール用スロット | GPIO → NC7WZ16（TLV70033 給電）→ 220Ω → 100Ω + 100nF to GND → 47µF → 出力（1.8k to GND） | LM386 | LM386N-1 @+5V、10k ポット → 2.2k → IN+、pin1–8 間 10µF（利得 200）、出力 1000µF 結合 → 10、L = GND、Zobel 10Ω + 0.1µF |
| コインカウンタ | なし | なし | なし | なし | — | — | なし（ネット名のみ） |
| ヒューズ/TVS/逆接 | なし | なし | なし | なし | ショットキー → VSYS | 未確認 | なし |
| 3.3V 生成 | BBG 内 | DE10 内 | LM1117-3.3 | Pi/Pico 内 | Pico 内 SMPS + TLV70033（音声用） | — | — |

確度: 表の値はすべて設計ファイル（netlist、kicad_pcb、回路図 PDF、BOM、取扱説明書）からの読み取りで、確認済です。「推論・計算」の行だけが推論です。

補足（確認済）:
- DE10Jamma の README: "Values for some components do not match the schematic, and have been adjusted to reduce the number of different components."、"Output level is not noticeably lower than a NeoGeo MVS, and well within adjustment range on arcade monitors."。R-2R の出力インピーダンスは R で、3.3V 出力のフルスケール開放電圧は 3.3 × 63/64 ≈ 3.25V です（推論・計算）。
- DE10Jamma の JP1 を Mono にすると L/R 両アンプに同一信号が入り、10a と 10b に同相出力が出ます。10 と L の間にスピーカーをつなぐ筐体ではほぼ無音になるはずで、作者の意図は未確認です（推論）。
- jammanator-pi の 74HC86 を 5V で動かすと VIH(min) = 3.5V（74HC、VCC = 4.5V）で、3.3V 出力はしきい値未満です。動作実績はあっても規格外です（推論。74HCT86 なら VIH = 2.0V）。
- RP2040 公式 VGA demo の PDF: "1/Rparallel = 1/499 + 1/1000 + 1/2000 + 1/4020 + 1/8060 = 0.00388, so Rparallel is 258 Ω ... 3.3 × 75 / (258 + 75) = 0.74V"。この5本を 2kΩ に直結すると 3.3 × 2000/2258 ≈ 2.92V になります（推論・計算）。
- fenlogic/vga666 は 75Ω/0.7Vpp 用で JAMMA 用ではありません: "Rs = 3.3/0.7*75-75 = 278 Ohms ... rounded down to 500, 1K, 2K, 4K, 8K and 16K"、"You should not draw more than 16mA from a pin. Thus the minimum resistor is 3.3/0.016 = 206 Ohms"。
- bad_raspi_jamma の "ERRORS" 欄: "Bad CSync generation for the JAMMA", "Bad RGB levels for JAMMA", "No decoupling caps on multiple ICs", "No pullup on I2C", "Limit JAMMA inputs to 3.3v PULLUP or IC is DEAD", "It is better to operate at 5v and limit I2C to 3.3v"、"DAC for 75ohm output needs to be changed for JAMMA via buffered output"。README: "The audio IC generates too much heat for a 3.1watt output." "No overvoltage prevention has been included on the design."
- Console JAMMAizer の説明書: "Video and audio signals are amplified using a THS7375 and LM386 respectively so they can conform to the JAMMA video and audio standards." "The LM386 has internal gain control that can be adjusted using the SMD trimmer potentiometer ... This should usually be set as low as possible"。
- NES2JAMMA の LM384 は利用者が "the volume is too low and muffled" と書いています（単一出典）。
- スーパーガン側の参考（確認済）: WinchesterPCB は JAMMA 入力を Teensy 4.1 → MUN5230DW1T1G（内蔵 1k/1k のデジタル NPN）で GND に落とし、+5V 配線幅 2.5mm（README: "If we assume 5A through a 1oz copper board ... 2.59mm trace width"）。MiniGun は JAMMA 入力を TLC5926 × 2 で GND に引き、JAMMA RGB → 4.7µF → 470Ω → SCART、Sync → 330Ω。

#### 1.9.2 参照回路に使える部品の JLCPCB 分類（2026-11-10、JLCPCB API）

JLCPCB の Basic は 351 件です（JLCPCB API と CDFER CSV と jlcparts で C 番号集合が完全一致）。Basic にあるのは抵抗 182、抵抗アレイ 3、MLCC 88、タンタル 2 などで、**アルミ電解・ヒューズ/ポリスイッチ・オーディオアンプ IC・ビデオアンプ・74HC86/74HCT/74LVC・BAT54 系は Basic に1件も無い**（確認済）。74 系ロジックで Basic なのは 74HC14（C5605）と 74HC595（C5947）だけです。UI の「Promotional Extended」フィルタは API の `preferredComponentFlag:true`（旧称 Preferred Extended）で、部品行のバッジは単に「Extended」と表示されます。

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

既存オープン設計の部品のクラス（確認済、JLCPCB API）: jammanator-pi の 240Ω 0805 1%（C17572）は Extended（Preferred）在庫 138,819、475Ω 0805 1%（C228851）は Extended **在庫 3**、100nF × 4 C アレイ（C62857）は Extended、100nF 0805（C38141）は Extended、10µF 1210（C39232）は Extended、SN74LVC244APWR（C7668）・MCP23017T-E/SS（C558584）・SN74HC86PWR（C2872580、在庫 1,098）・LM1117IMPX-3.3（C23984）は Extended、470nF 0805（C13967）は Basic。DE10Jamma の BOM の C83170・C140870・C106843・C105577・C114530・C81264・C442834 はすべて Extended で、C442834（1000µF）は在庫 0 です。

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

LM386 の動作電源は 4〜12V（TI データシート）です。+5V では出力 ≈ 0.25〜0.3W 級（325mW typ@6V/8Ω から推論）、+12V では上限ぎりぎりです（推論）。秋月の通販コードはオープン回路ノートでは "g114548" のように g 付きで書かれています（同じ品）。

### 1.10 本基板の設計目標値

電気的実装ノート第9節の目標値を基準にし、他のノートとの食い違いを解決した結果を反映しています（解決の経緯は 2 章の末尾と 4 章）。値そのものは推論（設計判断）で、根拠の欄が出典の事実です。

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

---

## 2. 第1次調査からの訂正

| # | 第1次調査の記述 | 訂正後 | 訂正したノート |
|---|---|---|---|
| 1 | 既成 KiCad フットプリントは見つからず、DE10Jamma の CAD 形式は未確認 | DE10Jamma は KiCad フットプリント `Jamma.pretty/JAMMA-56.kicad_mod`（パッド 2.35 × 8、ピッチ 3.96）を同梱し、その派生が estechnical/jammakludge にもある | エッジ寸法 |
| 2 | 接点は硬質金フラッシュ（ENIG でも足りる可能性） | JLCPCB は電解硬質金を提供せず、フィンガは ENIG（金 1/2 µ"）だけ | エッジ寸法 |
| 3 | ピッチ 0.156in（3.96mm）だけを記載 | 56極の両端間は Hirose/Sullins ではインチ基準 106.98mm。ただし JST GEC は 106.92 ± 0.05 で 3.96mm 基準。本シートは両方を満たす 3.96mm を採用（1.2.1 節） | エッジ寸法（本シートで追加の判断） |
| 4 | フィンガ幅・長さ、キー溝寸法と位置、面取り角度は未確認（一般に 2.5mm 幅程度との話） | メーカー図: フィンガ幅 2.3 ± 0.1（Hirose）／2.3 ± 0.035（JST）、キー溝 2.5 +0.1/0 × 11 +0.5/0（コンタクト位置中心、Hirose）／3.0 × 10.0（JST。電気的実装ノートの「溝幅 2.3 ± 0.035」はフィンガ幅の読み違いで、本シートで図面を再確認して訂正）、外端フィンガ中心→側面 3.84 +0/−0.1（JST）、先端 C0.5、基板厚 1.6 ± 0.15、タング幅 114.8 0/−0.2（Hirose）／114.6 +0/−0.2（JST） | エッジ寸法、電気的実装 |
| 5 | +5V は「2〜3A/pin でなく多数の指で分担」、1ピン当たり電流定格は未確認 | 嵌合コネクタの定格は1接点 3A（JST GEC、Hirose CR7、Sullins）。JAMMA 規格書の値は依然未確認 | エッジ寸法、電気的実装 |
| 6 | 多くの日本製筐体は −5V を供給しない | 誤り。Astro City / New Astro City（0.1A）、Egret II（5/E に配線）、Windy（0.5A）、Exceleena 2（0.2A）は供給する。供給しないと確認できたのは Blast City の JAMMA ループだけ | 電気的実装 |
| 7 | コインカウンタは +12V（MVS の例）に接続 | 日本の筐体には当てはまらない。Astro City と Windy は +5V 系、Cyber Lead の部品は "NX-06PD 5VDC"。NAOMI 系も +5V + 100Ω で偽装 | 電気的実装 |
| 8 | ロックアウト（9/K）も +12V コイルを GND へ落とす | MVS／米国系の話。日本の筐体（Astro City、Egret II、Windy）では 9/K と J は無配線。日本の「ブロッカー」はセレクタ側の部品（旭精工 QL-102 等） | 電気的実装 |
| 9 | 25/26/c/d は未接続で安全 | 不十分。Astro City は SW4・SW5、Egret II と Windy は SPARE1/2 として配線している。入力専用（プルアップ）か無接続にし、出力・電源・GND に使ってはいけない | 電気的実装 |
| 10 | 音量調整の規約は未確認、標準スピーカー抵抗は未確認 | 筐体側で調整するのが慣習（Blast City 100Ω 10W レオスタット、Astro City SOUND VOL.、Windy 2連 SOUND VOLUME、Egret II VOL）。スピーカーは 4Ω（Egret II）／8Ω × 2（Astro City）／8Ω（Blast City） | 電気的実装 |
| 11 | NeoGeo CRE401 は 1k プルアップ + 330Ω 直列 + コンデンサ | C は 33〜43nF（実測）、fc 約 15kHz | 電気的実装 |
| 12 | 0.7Vpp/75Ω は民生用 | Blast City は同じモニタに 75Ω/0.7Vp-p（D-SUB15）と 2kΩ/3.0Vp-p（AMP 6P = JAMMA）の切替（SW3）を持つ。JAMMA 基板が狙うのは後者 | 電気的実装 |
| 13 | 映像は各 ch 75〜330Ω 直列 + バッファで約 2〜3Vpp | 実在する基板は抵抗 DAC 直出しで、合成出力インピーダンス約 120〜130Ω、開放最大 3.5V（Neo Geo）。75Ω 直列は不要 | 電気的実装 |
| 14 | DE10Jamma は 6bit R-2R DAC（604Ω/1kΩ 系）× 3 | 誤り。R-2R は単一値 2R だけで構成（R は 2R を2本並列）。BOM 値 604Ω（CAY16-6040F4LF）、回路図値 475Ω。1kΩ は入力側の直列抵抗（28本） | オープン回路 |
| 15 | DE10Jamma の BOM は LCSC 番号入り（Basic 適合性は個別確認） | C83170・C140870・C106843・C105577・C114530・C81264・C442834 はすべて Extended（C442834 は在庫 0） | オープン回路 |
| 16 | DE10Jamma のライセンスは未確認 | リポジトリに LICENSE ファイルが無い（ライセンス表示なし＝再利用は要許諾） | オープン回路 |
| 17 | Console JAMMAizer は公開と非公開の情報が矛盾 | 部分解決: GitHub に DipTrace 設計ファイル、Gerber、取扱説明書が公開されているがライセンス表示は無い。映像 THS7375・音声 LM386 | オープン回路 |
| 18 | ORB は 24個のスイッチングダイオード（1N4148 系） | BOM は "Diode switching 100V 0.15A 4ns SMD1206"、回路図注記は "fast switching diode 15V, 4ns" で品番指定は無い。カソードが JAMMA 側 | オープン回路 |
| 19 | 入力は 10k プルアップ（または内蔵）+ 1k 直列 + 100nF〜10nF | DE10Jamma と jammanator-pi の実設計で裏付けられた。ただし RP2040 の内蔵プルアップは 50〜80kΩ と弱く、内蔵で代替するのは推奨しない。さらにコインのマイクロスイッチ（金接点）は最小負荷 1mA なので、3.3V では 3.3kΩ 以下が必要（10kΩ では 0.33mA） | オープン回路、電気的実装（本シートで統合） |
| 20 | コインカウンタは 2N2222/2N3904 等の小信号トランジスタで駆動可 | オープン JAMMA 基板での実例は見つからない。量産の実例は MVS の ULN2003 だけ。ULN2003ADR は Basic（C7512）。ただし日本の +5V カウンタには VCE(sat) 約 1V が不利（4.3 節） | オープン回路、電気的実装 |
| 21 | コインは 20〜50ms 以上の確定 | 電子セレクタのパルスが 25〜30ms の機種があるので、確定は 10ms 以上とする（推論の訂正） | 電気的実装 |
| 22 | カウンタ通電は約 50〜100ms（未確認） | ON 100〜120ms / OFF ≥ 100ms（ライン精機 MZ 25ms（1:1）・20Hz、Kessler-Ellis 120/80ms から） | 電気的実装 |
| 23 | +5V は 4.75〜5.25V 程度を想定 | 4.75〜5.5V で動作させる（RT-65A の調整範囲 "4.75 ~ 5.5V"） | 電気的実装 |
| 24 | ゴールドフィンガーの追加費は5枚で $10〜20（第三者推定） | 実見積で金指 Yes + 30° 面取りの追加費は $0。$20 前後かかるのは ENIG 表面処理（$20.10 / 5枚、$23.50 / 10枚） | 調達・コスト第2パス |
| 25 | ゴールドフィンガー付き基板は Economic PCBA が使えず Standard 必須 | 正しい（実画面で確認）。ただし「エッジパッドはあるが Gold Fingers: No」では見積システム上 Economic が選べた（審査で再分類されるかは未確認） | 調達・コスト第2パス |
| 26 | BAT54S/C は Preferred | C7420333（BAT54S）と BAT54C 系は Preferred で正しいが、jammanator-pi が使う BAT54S,215（C47546）は Extended（非 Preferred）。品番が同じでも C 番号でクラスが違う | オープン回路 |
| 27 | 映像の推論「各 ch 75〜330Ω 直列」のうち 75Ω 直列（Blast City の 75Ω 入力とは無関係） | 不要（#13 と同じ内容の再掲） | 電気的実装 |

第2パスのノート同士の食い違い（本シートで解決したもの）:
- **ピッチとタング幅**: エッジ寸法ノート（Hirose/Sullins 基準、3.9624mm・114.6mm）と電気的実装ノート（JST GEC、106.92 ± 0.05・114.6 +0/−0.2）。どちらもメーカー図面で証拠の強さは同じです。両方の公差を満たす 3.96mm・114.4mm を採用しました（1.2.1 節）。
- **カウンタの駆動素子**: オープン回路ノートは ULN2003ADR（Basic、COM を +12V）を推奨し、電気的実装ノートは低 RDS(on) の N-MOSFET を推奨しています。日本の筐体が +5V カウンタであることは一次資料（Cyber Lead の部品表、配線図）で確認されており、こちらの証拠が強いので N-MOSFET を採用しました（4.3 節）。
- **音声アンプ**: オープン回路ノートは Basic 制約から LM386 のシングルエンド（L = GND）を最小構成とし、電気的実装ノートは短絡保護付き BTL を推奨しています。筐体の配線図で L が GND でないこと、+5V の LM386 では出力が約 0.25〜0.3W しかないことから、BTL を採用しました（4.3 節）。
- **入力プルアップ**: オープン回路ノートは 10kΩ（実績あり）、電気的実装ノートは 3.3kΩ@3.3V（金接点の最小負荷 1mA）です。Omron のデータシートの最小負荷が一次資料なので、少なくともコイン入力には 1mA 以上を流します（4.3 節）。

---

## 3. 未確認事項と実機で確かめるべきこと

**規格・寸法**
1. JAMMA（JS）規格書の原本（−5V・ピン名・接点定格の公式規定）。web.archive.org が使える環境で旧 jamma.or.jp の資料集を再確認する必要があります。
2. 国内の筐体のハーネスに実際に付いているコネクタのメーカーと型番（JST GEC か Hirose か汎用品か）。**実機: 試作基板を Astro City などの実ハーネスに挿し、タング幅 114.4mm とキー溝 3.0 × 11.5mm で挿入感・横ずれ・接触を確認する。**
3. 日本製の実物 JAMMA 基板（カプコン、セガ等）のフィンガ寸法。**実機: ノギスで実測する。**
4. 4.00mm ピッチの基板の具体名と実測。
5. Hirose CR7E-56DA-3.96E（パネル取付型）の個別図面、Sullins の接点位置、JST GEC のキー溝寸法の公差（図面は幅 3.0・深さ 10.0 で公差の記載なし）と肩まわりの 10.0 / 10.0 min. の寸法線の起点。
6. 30°/45° が板面に対する角度か片側の半角か（図からは半角と読める）。
7. 筐体の基板取付スペースの公式寸法、JAMMA 基板の最大寸法、汎用基板足の穴径。

**JLCPCB**
8. 「エッジパッドあり・Gold Fingers: No」の注文が Gerber 審査で Standard へ再分類されるか（JLCPCB への問い合わせが必要）。
9. Standard PCBA でエッジレール付きの 10枚の PCB 代、BOM を入れた実 PCBA 見積。
10. Standard の装填料 $1.53 が部品種類単位であることの、料金表そのものでの明文（公式ブログには "per part number, per order" とある。料金表と FAQ には単位の記載が無い）。

**電源**
11. Sega 400-5198・Taito・Konami の電源の最小負荷、無負荷時の電圧、OVP 設定値。**実機: 本基板だけを載せた状態で +5V が安定するか、筐体電源が保護停止しないかを測る。**
12. 本基板（Pico 2 を複数枚使う構成、または Raspberry Pi を載せる構成）の +5V 消費電流。**実機: 起動時と定常の電流を測る。**

**映像**
13. Nanao MS8/MS9 と Toei の入力インピーダンス・入力レベル・同期閾値・水平垂直の引込み範囲。
14. 日本の筐体のモニタが 15.7458 kHz / 60.0985 Hz に同期すること。**実機: Astro City（MS8 系）と New Astro City / Egret II（MS9 系）で同期・画面位置・明るさを確認する。**
15. 3.3V 振幅の CSync を日本の筐体が確実に受けるか（DE10Jamma の実績のみ）。**実機: トランジスタ出力（5V）と 3.3V 直結の両方で確認する。**
16. Astro City のモニタのリモート基板の "video impedance" 切替の位置と既定値。
17. CPS2 / Taito F3 / Konami の RGB 出力段の部品値、ORB の CLC4007 の 5V 単電源での出力振幅。

**音声**
18. Windy、Cyber Lead、Exceleena のスピーカーのインピーダンスと出力。
19. PAM8302A 系の出力（2.5W @ 4Ω の可否）と GND への短絡保護の有無（データシート未確認）。**実機: L を GND に落とした筐体を模した負荷で BTL 出力を短絡させ、アンプが保護停止して壊れないことを確かめる。**
20. LM386 を +12V で使ったときの実際の出力と発熱（UTC LM386G のデータシート未確認）。
21. DE10Jamma の TDA7496 の MUTE/STBY の論理、Mono ジャンパ時に 10a/10b が同相になる作者意図。

**入力・コイン**
22. RP2350（Pico 2）の GPIO の入力電圧の絶対最大定格と、BAV99（シリコン）クランプで定格を超えないか（RP2040 では IOVDD + 0.5V を僅かに超え得る）。
23. 筐体のコイン線に 12V が乗るケースの実在と頻度。
24. メカセレクタのマイクロスイッチのチャタリング時間。**実機: オシロでコインスイッチの波形とパルス幅を測る。**
25. 電子セレクタ（AE-204D 等）の出力形式（オープンコレクタか）と、プルアップ電圧との相性。
26. NX-06PD / GX-06PD / Sega 220-5412 のメーカー・コイル抵抗・定格電圧（5V は Cyber Lead の部品表でのみ確認）。**実機: 筐体のカウンタのコイル抵抗を測り、ON 100ms で確実に1カウント進むか確かめる。**
27. 旭精工のブロッカー（QL-102）と VM81-M の極性（通電で阻止か受付か）。
28. Service / Test / Tilt の電気的詳細。
29. AO3400A の RDS(on) と、3.3V ゲート駆動での飽和（データシートの確認）。

---

## 4. ユーザー要求への影響

### 4.1 部品選定・実装ルール（Basic のみ、LCSC 在庫、秋月手はんだ、PCBA 任せ、点数削減、安価）

**事実**
- 金フィンガー付きの基板は Standard PCBA になります。Standard では Basic にも1種類 $1.53 の装填料がかかり、Setup $25.56、ステンシル $8.21 です。Economic は Setup $8.18、ステンシル $1.53、Basic と Preferred は装填料無料です。
- JLCPCB Basic には、音声アンプ IC、アルミ電解コンデンサ、ポリスイッチ／ヒューズ、ビデオアンプ、74HC86/74HCT/74LVC、BAT54 系、USB Type-C 端子がありません。
- JAMMA の入出力に必要な部品のうち Basic で揃うもの: 抵抗アレイ（C20197 / C1980 / C29718）、BAV99（C2500）、MMBT3904（C20526）、AO3400A（C20917）、ULN2003ADR（C7512）、SMBJ6.5CA（C7420377）、B5819W SL（C8598）、1N4148W（C81598）、AMS1117-3.3（C6186）、74HC14（C5605）、74HC595（C5947）、0603 1% の DAC 用抵抗、MLCC、タンタル。
- 調達・コスト第2パスの試算（推論を含む概算、ドナー機を除く1枚あたり）: A（金指一体、Basic 20種のみ + 秋月手はんだ）5枚 約¥6,800 / 10枚 約¥5,170。B（金指一体、Basic + Preferred + Extended 32種）約¥8,830 / ¥6,800。C（金指エッジ基板を分離 + 本体 Economic PCBA）約¥7,570 / ¥6,200。C'（C の構成で PCBA は Basic のみ）約¥5,110 / ¥4,350。分離案のエッジ基板（120 × 60mm 2層 ENIG 金指 30°）は5枚 $24.90 / 10枚 $29.30。

**選択肢（推論）**

| 案 | 内容 | 利点 | 欠点・リスク |
|---|---|---|---|
| 一体基板（A/B） | JAMMA フィンガを本体基板に作る | 基板間接続が無く、嵌合と配線の信頼性が高い。全部を PCBA に任せる方針に合う | Standard PCBA が確定し、「Basic のみ」の経済的根拠（装填料無料）が消える |
| 分離基板（C/C'） | 金指のエッジ基板と本体基板を分け、本体は Economic + HASL | 1枚あたり最も安い（C' で約 ¥4,350） | JAMMA 信号 約 40 本 + 電源の基板間接続を手はんだする。嵌合の信頼性が落ちる。電源 4接点分の電流を中継コネクタで通す必要がある |
| Gold Fingers: No でエッジパッド | 一体基板のまま Economic を狙う | 見積上は Economic が通った | 面取りが無く挿入性が落ち、コネクタを傷めるおそれ。審査で再分類される可能性（未確認） |

**推奨（推論）**: **一体基板＋Standard PCBA** を推奨します。JAMMA の電源と 40 本超の信号を基板間で中継するのは、信頼性の面で割に合わないからです。Standard では Basic と Preferred/Extended の装填料が同じ $1.53/種なので、音声アンプなど Basic に無い部品は **Extended を PCBA で載せる**ほうが、秋月の手はんだより「全部を基板実装メーカーに」の要求に合います。「Basic のみ」の規則は、在庫の安定性を確かめる基準として残し、Basic で済む箇所（入力保護、カウンタ駆動、電源保護、DAC）は Basic で揃えます。この判断はユーザーの「Basic のみ」の指示から外れるので、ユーザーの了承が必要です。

### 4.2 JAMMA 端子（製品要求）

**事実**: 1.1〜1.4 節のピン配列、寸法、電源のとおりです。

**推奨（推論）**
- フットプリントは 1.2.3 節の値で作ります（ピッチ 3.96mm、タング 114.4mm、フィンガ 2.3 × 8.8mm（Y 1.2〜10.0）、キー溝 3.0 × 11.5mm、先端〜12mm は部品禁止）。
- 電源として使うのは +5V（3/4/C/D）だけです。+12V（6/F）は負荷の電源には使いませんが、コインカウンタとロックアウトの還流ダイオードのカソードをつなぐために配線します（4.3 節）。−5V（5/E）は無接続です。GND は 8 接点すべてをベタに落とし、14（Video GND）は RGB と同期のリターンとして近くに通します。
- +5V 入力には TVS SMBJ6.5CA（C7420377、Basic）を置き、入力容量は 220µF 以下に抑えます。ポリスイッチは Basic に無いので、Extended の 1812 品（C269134 など）を PCBA で載せるか、秋月 MF-R300（112630）を手はんだします。C269134 は 1.1A 品なので、Pico 2 を複数枚や Raspberry Pi を載せる構成では足りない可能性があり、消費電流を測ってから定格を選びます（推論。nSMD200 C70085 などの 2A 級も Extended）。SMBJ6.5CA は 5.5V を少し超えた程度では導通しない見込みなので（1.10 節）、+5V の上げ過ぎへの保護としては不十分です（推論）。
- 25/c、26/d は入力専用（プルアップ付き）にします。11/M は無接続にします。

### 4.3 動作方式と入力形式（タイマー方式、通常方式のデフォルト形式・特殊形式）

**事実**
- 方式・形式の表で使う JAMMA 入力は、レバー（18〜21 / V〜Y）、ボタン1〜2（22・23 / Z・a）、ボタン3〜4（24・25 / b・c）、スタート（17 / U）、コイン（16 / T）です。ボタン4（25/c）は JAMMA の正式規格外です。Astro City はここを SW4、Egret II と Windy は SPARE1 として配線しています。
- コインのパルスは機構によって 25〜100ms（電子セレクタ 50 ± 5 / 72 ± 3ms、HX-616 30/50/100ms 程度）で、メカセレクタはマイクロスイッチの無電圧接点です。投入間隔は 0.5 秒以上です（AD-81P2）。
- Service（R）は「クレジット +1、カウンタは増えない」という慣習です。

**影響と推奨（推論）**
- **入力回路**: すべての入力を同じ回路にします。JAMMA ピン → プルアップ 3.3kΩ（3.3V へ）→ 対 GND 10nF → 直列 1kΩ → 3.3V へのクランプ（BAV99 C2500、Basic）→ マイコンの入力（シュミット有効）。
  - プルアップを 10kΩ（実績のある値）にしない理由は、コインのマイクロスイッチ（Omron D2MC-01 の金接点）の最小負荷が 5VDC 1mA で、10kΩ@3.3V では 0.33mA しか流れないからです。3.3kΩ@3.3V なら 1.0mA です。0603 1% の 3.3k は Basic ですが、C 番号はノートに無く未確認です。4連アレイにしたいなら Basic の 1k アレイ（C20197、3.3mA。Neo Geo の CRE401 と同じ 1k）が使えます。4.7k アレイ（C1980）は 0.70mA で、1mA に届きません。
  - BAV99 はシリコンなので、クランプ電圧がショットキー（BAT54S）より約 0.3V 高くなります。RP2350 の定格に対する余裕は未確認です（3 章 #22）。余裕が足りなければ、BAT54S（C7420333、Preferred Extended）に替えるか、直列抵抗を 4.7kΩ（C1980、Basic）に上げます。12V がコイン線に乗った場合、直列 1kΩ とクランプを通って約 8mA、さらにプルアップ 3.3kΩ を通って約 2.6mA、計 約 10.6mA が 3.3V 系に流れ込みます（推論・計算）。3.3V 系の負荷がこれより小さいと 3.3V が押し上げられるので、直列を 4.7kΩ にする案のほうが安全です（推論）。
- **入力の本数**: 必要な入力は、コイン2、スタート2、レバー8、ボタン8（1〜4 × 2）、Test、Service、Tilt の計 23 本で、26/d を読むなら 25 本です。カウンタ2本とロックアウト2本の出力を加えると、1枚の Pico の GPIO では足りません（オープン回路ノートの指摘）。マイコンを複数枚使えるので（5 章の要求）、入出力専用の Pico を1枚置き、入力は 74HC165（C5613、Preferred Extended）× 3 で多重化するか、Pico を2枚に分けます。
- **デバウンスとコインの整形**: レバーとボタンは 2〜5ms、コインは Low ≥ 10ms で確定・High ≥ 10ms で解除、1パルスを1枚と数えます。通常方式のデフォルト形式（コイン → SELECT）と特殊形式（コイン → 上下同時）では、ユーザー要求の 3.7 節のとおり、ゲームに渡すパルスを一定幅（任天堂 VS. システムの実機は 2.5〜4 フレーム）に整形し、連続投入は待ち行列にして間隔を空けて出します。これは JAMMA の入力側の事実（パルス幅 25〜100ms、投入間隔 ≥ 0.5 秒）とも両立します。
- **タイマー方式のコイン**: コイン1・コイン2のどちらでも時間を加算し、ゲームには渡しません。Service（R）は「時間を加算するがカウンタは進めない」と扱うのが慣習に合います。
- **タイマー方式の入力の割り当て**: 1P スタート（17）は I コンの START、2P スタート（U）は I コンの SELECT になり、ボタン3・4（24・25・b・c）は使いません（ユーザー要求 3.3 節。「セレクトが2Pボタン」を 2P スタートと読んだのはユーザー未確認の前提）。どれも同じ入力回路なので、JAMMA 側の回路は方式・形式によらず共通で、割り当てはファームウェアだけで変わります（推論）。時間切れ後の扱いと残り時間の表示手段はユーザー要求で未定・要検討とされており、JAMMA 側には表示用の信号が無いので、映像に重ねて描くなどの方法が必要です（推論）。
- **コインカウンタ**: コイン1枚ごとに 8（J は日本の筐体では無配線が多いが、同じ回路を付ける）を ON 100〜120ms / OFF ≥ 100ms で駆動し、連続投入は待ち行列にします。駆動素子は次のとおり選びます。
  - 選択肢1: ULN2003ADR（C7512、Basic）。MVS で量産実績があり、1個で7チャンネル、クランプダイオード内蔵です。ただし VCE(sat) が 100mA で typ 0.9 / max 1.1V あるので、日本の主流の +5V カウンタには約 4V しかかかりません。
  - 選択肢2: AO3400A（C20917、Basic）のローサイド駆動。飽和電圧が小さく、+5V と +12V のどちらのコイルにも使えます。部品は1チャンネル1個です。
  - **推奨は選択肢2**です。日本の筐体が +5V カウンタであることが一次資料で確認されているからです。還流ダイオード（1N4148W C81598 または M7 C95872、Basic）は、**ドレインから +12V（6/F）へ、カソードを +12V 側**に置きます。カソードを +5V に置くと、+12V カウンタの筐体ではコイル → ダイオード → +5V に常に電流が流れ、カウンタが通電しっぱなしになります。+12V に置けば、+5V コイルでも +12V コイルでも、遮断時のサージは約 12.7V に抑えられ、AO3400A の耐圧（30V 級。ノートの目標値 ≥ 30V。正確な定格は未確認）以内です。この方式では +12V（6/F）をダイオードのためだけに配線することになります。出力端子には誤接続と短絡に備えて 1〜2Ω の直列抵抗（またはポリスイッチ）を入れます。
- **ロックアウト**: 日本の筐体では配線されていないことが多いですが、米国式の筐体のために 9/K にも同じドライバを付けます。12V・157mA の連続通電に耐える素子にします。タイマー方式で使う場面は無く、通常方式でクレジットの上限に達したときに受付を止める用途が考えられます。
- **リスク**: 特殊形式のボタン4（25/c）は、筐体にボタン4が配線されていないと使えません。Astro City は SW4 として配線していますが、筐体ごとの違いは実機で確かめる必要があります。

### 4.4 切り替え手段はソフトウェア

**事実**: Test（15）は JAMMA の正式な入力で、筐体のテストスイッチにつながっています。Service（R）も同様です。

**推奨（推論）**: 方式と形式（タイマー方式／通常方式、デフォルト形式／特殊形式、1コインあたりの時間など）はファームウェアの設定値として不揮発メモリに保存します（ユーザー要求 4.2 節）。設定画面は、Test スイッチで開きます。追加の部品は要りません。ユーザー要求 4.2 節は、ほかに USB（ファームウェア更新と同じ Type-C 端子）からの書き換えと、新規開発カートリッジからの切り替え（$4016 の OUT1・OUT2 で指示し、$4016 の D1 と $4017 の D1〜D4 で返す。手順は未設計）も挙げています。後者はファミコン側の信号だけで完結し、JAMMA 端子は関係しません。市販ソフトは基板に指示を出せないので、市販ソフトを動かすときは担当者が Test スイッチの設定画面でタイマー方式にします。JAMMA 側の入力回路は他の入力と同じで、Test と Service もプルアップ・フィルタ・クランプを付けます。方式・形式用の物理 DIP スイッチは置かないことで、部品点数を減らせます（DIP スイッチは JLCPCB では Extended の C319050 / C99418 しかありません）。設定画面を描くには、映像をマイコンが作り直す構成が必要です（映像経路は別シート）。

### 4.5 Raspberry Pi（複数枚）と将来の CPU/PPU/メモリ更新

**事実**: JAMMA 側の制約は、56 接点の固定された割り当てと、+5V 4接点（1接点 3A）の電源だけです。音声はモノラル（10/L）で、11/M でのステレオは MVS 配線の筐体との事故の元になります。25/c、26/d は筐体によってボタンが付いています。

**推奨（推論）**
- **JAMMA の入出力回路は、CPU/PPU 実チップの構成とエミュレーション構成で共通の1ブロックにします。** 入出力専用の Pico（または複数枚）が JAMMA の入力・コイン・カウンタ・ロックアウトを受け持てば、CPU/PPU 側をどう更新しても JAMMA 側の回路を作り直さずに済みます。
- **映像の DAC は、将来の色数の増加に備えて 6bit/色にします。** 3.3V の GPIO から無バッファで出す場合、単一値 R-2R を 470Ω（C23179、Basic）で組むと出力抵抗は約 235Ω、2kΩ 負荷で約 2.91V になります（推論・計算: 3.3 × 63/64 × 2000/2235。オープン回路ノートの「約 2.86V」は計算の誤り）。1色 17 本の抵抗が要ります（推論・計算: 2R の脚 6 本 + 終端 2R 1 本 + R 5 本をそれぞれ 2R 2本並列で 10 本。オープン回路ノートの「14 本」は数え誤り）。5bit の2進重み（510Ω C23193 / 1k C21190 / 2k C22975 / 3.9k C23018 / 8.2k C25981、Basic）は並列 ≈ 260Ω、2kΩ 負荷で ≈ 2.9V で、部品は少ないですが 6bit 目の値（約 16k）の Basic 品はノートで未確認です。どちらも出力インピーダンスが実在基板（100〜150Ω）より高いので、モニタの入力インピーダンスによって明るさが少し変わります（R-2R 470Ω 版で 2kΩ なら約 2.91V、4.7kΩ なら約 3.09V。推論・計算）。モニタの CONTRAST の調整範囲に入る見込みで、DE10Jamma（R = 302Ω）の実績もあります。
- **同期は 5V 振幅の出力段にします。** MMBT3904（C20526、Basic）のオープンコレクタに 5V へのプルアップ（1kΩ 程度）と直列 100Ω を付けると、High は約 4.6V（12kΩ 負荷）、Low は 0.4V 以下になります（推論・計算）。この段は極性を反転するので、マイコンは正極性で出します。74HC14 を 5V で使う昇圧は 3.3V 入力が保証外なので使いません。5V の筐体で 3.3V 直結（DE10Jamma 方式）でも動く可能性はありますが、日本の筐体での実績は確認されていません。
- **音声は BTL（10 = +、L = −）で出し、GND への短絡保護を持つアンプにします。**
  - 選択肢1: PAM8302AASCR（C113367、Extended、在庫 20,707）を PCBA で載せる。5V 電源、部品が少ない。2.5W @ 4Ω と短絡保護はデータシートで未確認なので、採用前に確認が必要です。
  - 選択肢2: 秋月 AE-PAM8012（108217、¥300）を手はんだする。短絡・過熱保護が商品ページに明記され、4Ω 2.0W @5V です。
  - 選択肢3: M2073G-D08（秋月 117431、¥40）を +12V で BTL にする。部品は安いが、短絡保護の情報が無く、+12V 線のサージで MVS のアンプが壊れた事例があります。
  - 選択肢4: LM386 のシングルエンド（L = GND、出力 1000µF 結合）。オープン基板の実例はありますが、+5V では約 0.25〜0.3W しか出ず、NES2JAMMA の LM384 では "the volume is too low and muffled" とされています。
  - **推奨は選択肢1、確認が取れなければ選択肢2**です。目標の「4Ω で 3W 以上」は、5V の D 級 BTL では約 2W 級になります。筐体側に音量の直列ボリュームがあり、ファミコンの音声はモノラルなので、2W 級で実用になると見込みますが、実機で音量を確かめる必要があります。基板上の音量調整は必須ではありませんが、ゲームごとの音量差に備えてファームウェアで固定ゲインを持たせます。
- **ステレオ化などの拡張は JAMMA を通しません。** 11/M は無接続のままにし、将来ステレオにするなら Windy の Konami 基板用コネクタ（NH-4）のような別端子を用意します。
- **予備入力**: 26/d は入力専用で読めるようにしておけば、Astro City の SW5 や Egret II の SPARE2 を将来の新規ゲームのボタンとして使えます。
- **電源の余裕**: Pico 2 を複数枚載せても、筐体の +5V（5〜7A）と 4 接点（1接点 3A）には余裕があります。フル機能の Raspberry Pi を載せる場合の消費電流は、このトピックのノートには無く未確認です。New Astro City の取説は筐体電源の容量を超える基板を禁じています。

### 4.6 USB Type-C によるファームウェア更新

**事実**: USB Type-C 16P（C393939）は JLCPCB では Extended です。秋月には 5077CR-16-SMC2-BK-TR（114356、¥110、在庫僅少）があります。Pico のデータシートは、2つ目の電源をショットキーダイオード経由で VSYS に入れることを勧めています。B5819W SL（C8598）は Basic です。

**推奨（推論）**
- **USB の VBUS と JAMMA の +5V は、ショットキーダイオード（B5819W SL C8598、Basic）で分けます。** 筐体の電源を切った状態で USB をつないだとき、USB の 5V が基板の +5V 網を通って筐体の +5V 線（モニタ以外の筐体側負荷やカウンタのコイル）に逆流するのを防ぐためです。逆に、筐体の +5V が PC の USB ポートへ流れ込むのも防げます。
- **Type-C 端子は、基板を筐体に取り付けたまま挿せる辺に置きます。** タング側（先端〜12mm の部品禁止域）とコネクタ本体の耳の範囲には置けません。タングの反対側の辺が適当です。
- 筐体の中で USB ケーブルをつなぐときは、JAMMA の GND と PC の GND が共通になります。ファームウェア更新は筐体の電源を切って USB 給電だけで行う手順にすると、接地の問題を避けられます。

---

## 5. 出典一覧

### 1.1 ピン配列（および第2章の該当訂正）
- Arcade Otaku Wiki「JAMMA」（ピン表、入出力の意味、CPS2 の流用）: https://wiki.arcadeotaku.com/w/JAMMA
- old.pinouts.ru「JAMMA」（Hardware Book 系のピン表）: https://old.pinouts.ru/Slots/jamma.shtml
- Hardware Book JAMMA のミラー: https://k1.spdns.de/Develop/Hardware/Infomix/Stecker%20und%20Kabel/hwbook/connector/bus/jamma.html
- videogametesteroffer ブログ（25/26/c/d と 11/M を "No connection" とする表）: https://videogametesteroffer.blogspot.com/2020/04/understand-jamma-pcb-and-edge-connector.html
- NeoGeo Dev Wiki「JAMMA connector pinout」（MVS 派生、ピッチ、キー、ステレオ配線の事故）: https://wiki.neogeodev.org/index.php/JAMMA_connector_pinout
- 旧 ArcadeControls wiki「JAMMA」（20/21 が逆との指摘、検索結果経由）: https://oldwiki.arcadecontrols.com/index.php/JAMMA
- 英語版 Wikipedia「JAMMA」（1985 年、電源用途、負極性同期、ピッチ）: https://en.wikipedia.org/wiki/JAMMA
- 日本語版 Wikipedia「JAMMA」（1986 年、JVS）: https://ja.wikipedia.org/wiki/JAMMA
- wdic「JAMMAハーネス」（JAMMA（JS）規格、1986 年、5/E と 7/H、部品面 1〜28）: https://www.wdic.org/w/MOE/JAMMA%E3%83%8F%E3%83%BC%E3%83%8D%E3%82%B9
- calm-life.jp「JAMMA 規格 56P」（個人の配線表）: https://www.calm-life.jp/game/connect/jamma.html
- fujikko の配線表: http://www3.big.or.jp/~fujikko/kiban/jamma.html
- usada.yabou.jp（JAMMA VIDEO規格＝JVS の説明）: https://usada.yabou.jp/game/acgame_jvs.html
- JVS 第3版ドラフト PDF（非公式流通）: http://daifukkat.su/files/jvs_wip.pdf
- JAIA「資料」ページ（56ピン規格書は無い）: https://jaia.jp/reference/
- JAIA 2022 年ガイドライン PDF（別物の 9極コネクタ）: https://jaia.jp/wp-content/uploads/2022/08/%E6%B1%BA%E6%B8%88%E3%81%AA%E3%81%A9%E3%81%AE%E6%83%85%E5%A0%B1%E5%8F%8E%E9%9B%86%E7%AB%AF%E6%9C%AB%E3%81%AE%E5%8F%96%E4%BB%98%E5%AE%B9%E6%98%93%E5%8C%96%E3%82%AC%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%B320220801%E6%94%B9%E5%AE%9A.pdf
- Hardware Book「electrocoin」（旧規格、検索結果のみ）: https://connectorbook.com/hardwarebook/connector/bus/electrocoin.html
- Astro City 取扱説明書（25/c/26/d の SW4/5 配線ほか）: https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf
- Egret II 配線図（25/c/26/d の SPARE 配線ほか）: https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg
- Windy 束線図（25/c/26/d の SPARE 配線ほか）: https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg

### 1.2 エッジ寸法と向き
- Hirose CR7 シリーズ カタログ（適合基板図、本体寸法、定格、キー部品）: https://s1.dtsheet.com/store/data/002648525.pdf （取得元ページ https://dtsheet.com/model/1263367 ）
- Hirose CR7E-30DB-3.96E(72) 個別図面 ADC-016737-72-02（めっき、挿入深さ、接点位置）: https://static.chipdip.ru/lib/690/DOC043690981.pdf
- Digi-Key CR7E-56DB-3.96E(72)（Obsolete 表示、検索要約経由）: https://www.digikey.com.au/en/products/detail/hirose-electric-co-ltd/CR7E-56DB-3-96E-72/8561491
- electronicsdatasheets CR7E-56DA-3.96E（検索要約経由）: https://www.electronicsdatasheets.com/manufacturers/hirose-electric-uk-ltd/parts/cr7e-56da-396e
- Sullins カタログ p.74–75（.156" カードエッジ、適合基板、定格、キー）: https://s3.amazonaws.com/catalogspreads-pdf/PAGE74-75%20.156%20LP%20DS%20EYE%20RA.pdf
- Digi-Key EBM28DRXH: https://www.digikey.com/en/products/detail/sullins-connector-solutions/EBM28DRXH/927310
- Sullins ニュース（3 Amps per contact、検索要約経由）: https://www.sullinscorp.com/news/news-releases/sullins-double-row-male-edgecard-connector-series-features-0-100-or-0-156-contact-centerline-parts/
- JST GEC データシート（"conforns to the JAMMA standards"、参考基板図、定格）: https://datasheet.octopart.com/GEC-561-JST-datasheet-180492417.pdf
- Paradise Arcade の JAMMA 56P 直角コネクタ: https://paradisearcadeshop.com/products/jamma-56-pin-right-angle-connector
- MisterJamma/DE10Jamma（`Jamma.pretty/JAMMA-56.kicad_mod`、`DE10Jamma.kicad_pcb`）: https://github.com/MisterJamma/DE10Jamma
- jzdziarski/jamma（`CAD/Universal JAMMA Edge.kicad_pcb`）: https://github.com/jzdziarski/jamma （旧記載 https://github.com/jzdziarski/jamma/ ）
- jzdziarski の解説ブログ: https://www.zdziarski.com/blog/?p=13445
- ole00/orb（`orb03.pcb`、gerbers）: https://github.com/ole00/orb
- ORB README（1.6mm 2層、129 × 117mm）: https://raw.githubusercontent.com/ole00/orb/master/README.md
- estechnical/jammakludge（DE10Jamma 派生フットプリント）: https://github.com/estechnical/jammakludge
- yoonjustin/WinchesterPCB（`JAMMA56HALF`）: https://github.com/yoonjustin/WinchesterPCB
- Arcade-Projects「JAMMA fingerboards」（Frank_fjs のフィンガーボード）: https://www.arcade-projects.com/threads/jamma-fingerboards.7042/
- OSH Park shared project（1.6mm、面取り、金フラッシュ。第1パス）: https://oshpark.com/shared_projects/KrFAoVRl
- arcade-projects（4mm ピッチ説のフォーラム投稿）: https://www.arcade-projects.com/goto/post?id=410606
- Arcade Otaku Wiki「Sega Astro City 2」（基板取付板、検索要約経由）: https://wiki.arcadeotaku.com/w/Sega_Astro_City_2
- arcadeotaku forum（Astro City 2 の取付スペース）: https://forum.arcadeotaku.com/viewtopic.php?t=43430
- arcade-projects「PCB holder for astro city cab」（基板足）: https://www.arcade-projects.com/threads/pcb-holder-for-astro-city-cab.20532/
- JLCPCB capabilities（外形公差、検索要約経由）: https://jlcpcb.com/capabilities/pcb-capabilities
- JLCPCB slot ブログ（非めっきスロット最小幅、検索要約経由）: https://jlcpcb.com/blog/reliable-pcb-slot-holes-design

### 1.3 JLCPCB の金フィンガー
- JLCPCB Help「JLCPCB Gold Fingers」（ENIG 条件、面取り角、セットバック、マスク、寸法制限）: https://jlcpcb.com/help/article/jlcpcb-gold-fingers
- JLCPCB Help「Instructions for chamfering gold fingers」（エッジ全長の面取り、面付け）: https://jlcpcb.com/help/article/instructions-for-chamfering-gold-fingers
- JLCPCB 発注ページ（Gold Fingers の選択肢、板厚公差、OSP、実見積、面取り表示）: https://cart.jlcpcb.com/quote
- JLCPCB ブログ「hard-gold-pcb-finish」（硬質金なし、一般的な金厚）: https://jlcpcb.com/blog/hard-gold-pcb-finish
- JLCPCB Help「surface finish」（ENIG 1/2 µ"、Ni 厚）: https://jlcpcb.com/help/article/jlcpcb-surface-finish
- JLCPCB Help「In what cases will there be charged extra?」（ENIG 面積の追加料金、オプション未選択時の追加費）: https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra
- JLCPCB ブログ「beveled-edges-card-edge-connectors」（1/3〜1/2 の面取り記述）: https://jlcpcb.com/blog/beveled-edges-card-edge-connectors
- JLCPCB ブログ「pcb-gold-fingers」（0.5mm と 1.0mm の併記）: https://jlcpcb.com/blog/pcb-gold-fingers
- zbotic のガイド（「5枚で $10〜20」、不採用）: https://zbotic.in/pcb-gold-fingers-edge-connector-design-guide/
- PCBWay「PCB Gold fingers」（比較）: https://www.pcbway.com/pcb_prototype/PCB_Gold_fingers.html
- stardot forum（ENIG フィンガの量産報告、検索要約経由）: https://stardot.org.uk/forums/viewtopic.php?t=20829
- classiccmp メーリングリスト（日本製基板のエッジが錫系との証言、検索要約経由）: https://classiccmp.org/mailman3/hyperkitty/list/test-drb@ccmp.vtda.org/message/Z4QCMRGYFVHVHKEKNFXUIKF4TCIJAI36
- JLCPCB PCBA Capabilities（Economic は Gold Fingers 非対応）: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- LCSC PCBA Capabilities（同じ文言）: https://www.lcsc.com/pcba/capabilities
- JLCPCB「PCB Prototype Assembly」（PCBA 料金表）: https://jlcpcb.com/solutions/pcb-prototype-assembly
- JLCPCB Help「PCB Assembly Cost: What Does the Price Include?」（料金記事、$3.58）: https://jlcpcb.com/help/article/pcb-assembly-price
- JLCPCB ブログ「reduce PCB assembly cost」（装填料の扱い、handling fee）: https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype
- JLCPCB「PCB Assembly FAQs」（旧値）: https://jlcpcb.com/help/article/pcb-assembly-faqs
- EasyEDA forum（2021 年頃の金指と組立の回答）: https://easyeda.com/forum/topic/JLC-SMT-and-Gold-Fingers-d1c2d2d6193b4d2cbed3d25e7f2601c2
- KabukiFlux/JAMMA_2player_xbox360（ENIG と 30° の推奨、12V の警告）: https://github.com/KabukiFlux/JAMMA_2player_xbox360

### 1.4 電源
- Astro City 取扱説明書 p.30-31（電源 400-5198、電線表）: https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf
- New Astro City 取扱説明書 p.10, p.22（電源容量、V.ADJ）: https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf
- Egret II 配線図: https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg
- hard--candy「Windy」（電源容量）: https://www.hard--candy.com/wiki/candy/Windy
- Windy 束線図: https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg
- hard--candy「Exceleena 2」: https://www.hard--candy.com/wiki/candy/Exceleena_2
- Arcade Otaku Wiki「Sega Blast City Wiring Guide」（−5V 非供給）: https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide
- Mean Well RT-65 仕様書: https://www.meanwell.com/Upload/PDF/RT-65/RT-65-SPEC.PDF
- arcade-museum「What value resistors to satisfy PSU minimum load reqs?」（最小負荷、検索要約経由）: https://forums.arcade-museum.com/threads/what-value-resistors-to-satisfy-psu-minimum-load-reqs.499357/
- arcadecontrols forum（電源容量の目安、検索要約経由）: https://forum.arcadecontrols.com/index.php/topic,143607.0.html
- arcadeotaku forum −5V スレッド（本文取得不可）: https://forum.arcadeotaku.com/viewtopic.php?p=455265
- DE10Jamma README（+5V の上げ過ぎ）: https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md
- 任天堂 ファミリーコンピュータ ハードウェア（HVC-002、検索要約経由）: https://www.nintendo.com/jp/famicom/hardware/index.html
- Raspberry Pi「Hardware design with RP2040」（VSYS へのショットキー）: https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf
- Pico データシート（VSYS の範囲、電源の OR 接続）: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- cspang1/jcap（逆接保護の例）: https://github.com/cspang1/jcap

### 1.5 映像
- Blast City（Bass Fishing 版）取扱説明書 p.49（SW3 の切替、周波数モード）: https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf
- Arcade Otaku Wiki「Sega Blast City Wiring Guide」（3.0Vp-p / 2kΩ、負極性コンポジット同期、8Ω）: https://wiki.arcadeotaku.com/w/Sega_Blast_City_Wiring_Guide
- Astro City 取扱説明書 p.8, p.30（15K/24K、カラーディスプレイ・コネクタ）: https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf
- New Astro City 取扱説明書 p.17（CONTRAST 調整）: https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf
- Cyber Lead 取扱説明書 p.68（対応ボード）: https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf
- Egret II 配線図（VIDEO Assy）: https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg
- Windy 束線図（29inch MONITOR）: https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg
- hard--candy 筐体一覧（モニタ型式）: https://www.hard--candy.com/wiki/candy-cabinets
- hard--candy「Egret II」: https://www.hard--candy.com/wiki/candy/Egret_II
- hard--candy「Windy」: https://www.hard--candy.com/wiki/candy/Windy
- Wells-Gardner K7000 サービスマニュアル（archive.org）: https://dn760108.eu.archive.org/0/items/k-7000-1/K7000-1_text.pdf
- Hantarex MTC 9000 マニュアル（archive.org）: https://archive.org/stream/ArcadeGameManualMtc9000/mtc9000_djvu.txt
- Hantarex MTC 900（manualslib、検索要約経由）: https://www.manualslib.com/manual/1710685/Hantarex-Mtc-900.html?page=8
- mikejmoffitt.com「MS9」（PLL、Contrast）: http://mikejmoffitt.com/pages/ms9-hax/
- gamerepair.info「Nanao MS9-29」（検索要約経由）: https://gamerepair.info/hardware/35_nanao_ms9_29
- arcade-projects「Video impedance selector」（MS8、検索要約経由）: https://www.arcade-projects.com/threads/video-impedance-selector.18012/
- etim.net.au「AV-Driver Arcade」（TTL 3-5Vpp、1-5kΩ、アッテネータの負荷、speaker−）: https://etim.net.au/av-driver/arcade/
- gbs-control wiki「Arcade Boards」（1k-10kΩ、0.7Vpp/75Ω）: https://github.com/ramapcsx2/gbs-control/wiki/Arcade-Boards
- Mike's Arcade「Video Inversion and You!」（AMOA 2V、任天堂の反転映像）: https://www.mikesarcade.com/cgi-bin/spies.cgi?action=url&type=info&page=vidinvrt.txt
- NeoGeo Dev Wiki「Video DAC」（0〜3.5V 直出し、AES の分圧）: https://wiki.neogeodev.org/index.php?title=Video_DAC&action=raw
- MAME neogeo_v.cpp（抵抗値）: https://raw.githubusercontent.com/mamedev/mame/master/src/mame/snk/neogeo_v.cpp
- MAME segaic16.cpp（抵抗値）: https://raw.githubusercontent.com/mamedev/mame/master/src/mame/sega/segaic16.cpp
- arcade-museum「Resistor arrays on Capcom CPS1 A board」（検索要約経由）: https://forums.arcade-museum.com/threads/resistor-arrays-on-capcom-cps1-a-board.331665/
- slashdirt supergun（分圧＋バッファ、検索要約経由）: http://hacks.slashdirt.org/hw/supergun/
- neo-geo.com「RGB voltage levels」（直列抵抗の例、検索要約経由）: https://www.neo-geo.com/forums/index.php?threads/rgb-voltage-levels.250783/
- RetroRGB「Axunworks JAMMA Supergun Mini review」（1.2V、同期 470Ω、検索要約経由）: https://retrorgb.com/axunworks-jamma-supergun-mini-full-review.html
- arcade-projects「RGB amp VGA to JAMMA」（JAMMAizer 475Ω、1kΩ 設定）: https://www.arcade-projects.com/threads/rgb-amp-vga-to-jamma.15501/ （投稿 https://www.arcade-projects.com/threads/rgb-amp-vga-to-jamma.15501/post-324475 ）
- nesdev「PPU frame timing」（ドット飛ばし）: https://www.nesdev.org/wiki/PPU_frame_timing
- nesdev「PPU variants」（2C03/2C04/2C05 のタイミング）: https://www.nesdev.org/wiki/PPU_variants
- PlayChoice-10 Operation Manual（archive.org、モニタ型番、映像極性）: https://archive.org/details/pc10operationmanualpch1-up
- Paradise Arcade Shop（Sanyo 20-EZV の video inversion kit、検索要約経由）: https://paradisearcadeshop.com/a/p/products/nintendo-sanyo-20-ezvr-bc-monitor-video-inversion-kit-by-zanen
- shmups「NES/SNES 240p dejitter mod」（ジッタ、検索要約経由）: https://shmups.system11.org/viewtopic.php?t=61285
- arcade-projects「NES2JAMMA」（TLS1233・LM1881・LM384）: https://www.arcade-projects.com/threads/nes2jamma.2779/
- DE10Jamma README（R-2R DAC、出力レベル）: https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md
- ORB bom.txt（CLC4007、74HC4066 等）: https://raw.githubusercontent.com/ole00/orb/master/bom.txt
- falz.net「Pi2jamma hardware and software info」（VGA666 + THS7314 ほか）: https://falz.net/wiki/Pi2jamma_hardware_and_software_info

### 1.6 音声
- Astro City 取扱説明書 p.20, p.30-31（スピーカー 8Ω 10W、SOUND VOL.）: https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf
- New Astro City 取扱説明書 p.10（SOUND VOL.）: https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf
- Blast City（Bass Fishing 版）取扱説明書（レオスタット、スピーカーボックス）: https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf
- Egret II 配線図（4Ω × 2、VOL.）: https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg
- Windy 束線図（2連 SOUND VOLUME、NH-4）: https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg
- Cyber Lead 取扱説明書 p.59（スピーカー型番）: https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf
- NeoGeo Dev Wiki「Power amp」（MVS のアンプ IC）: https://wiki.neogeodev.org/index.php?title=Power_amp&action=raw
- TA8201AK データシート（検索要約経由）: https://datasheetspdf.com/datasheet/TA8201AK.html
- TDA7240A データシート（検索要約経由）: https://manualmachine.com/sgsthomsonmicroelectronics/tda7240a/4458195-datasheet
- HA13001（datasheetcafe、確度低）: https://www.datasheetcafe.com/ha13001-pdf-datasheet-26622/
- etim.net.au（"the speaker- pin is not connected (this isn't ground)"）: https://etim.net.au/av-driver/arcade/
- arcade-projects「jamma speakers」（BTL、検索要約経由）: https://www.arcade-projects.com/threads/jamma-speakers.5497/
- arcadecontrols forum（ブリッジ出力の接地の警告、検索要約経由）: https://forum.arcadecontrols.com/index.php/topic,69692.0.html
- NeoGeo Dev Wiki「JAMMA connector pinout」（MVS ステレオ配線）: https://wiki.neogeodev.org/index.php/JAMMA_connector_pinout
- Arcade Otaku Wiki「JAMMA」（Speaker +/− と Audio +/−）: https://wiki.arcadeotaku.com/w/JAMMA
- arcade-projects「NES2JAMMA」（LM384 の音量不足）: https://www.arcade-projects.com/threads/nes2jamma.2779/
- DE10Jamma README（TDA7496、Mono/Stereo ジャンパ）: https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md

### 1.7 入力
- NeoGeo Dev Wiki「CRE401」: https://wiki.neogeodev.org/index.php?title=CRE401&action=raw （第1パスの参照 https://wiki.neogeodev.org/index.php?title=CRE401 ）
- mourix/CRE401 README（実測値）: https://raw.githubusercontent.com/mourix/CRE401/main/README.md
- CR シリーズの資料 Cr.pdf: https://wiki.neogeodev.org/images/5/5a/Cr.pdf
- DE10Jamma（netlist、README）: https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/DE10Jamma.net 、https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md
- KabukiFlux/jammanator-pi: https://github.com/KabukiFlux/jammanator-pi
- ole00/orb 回路図 PDF: https://raw.githubusercontent.com/ole00/orb/master/orb03.pdf
- ninomegadriver/PiPicoJamma: https://github.com/ninomegadriver/PiPicoJamma
- KabukiFlux/JAMMA_2player_xbox360: https://github.com/KabukiFlux/JAMMA_2player_xbox360
- KabukiFlux/bad_raspi_jamma: https://github.com/KabukiFlux/bad_raspi_jamma
- RP2040 データシート（入力の絶対最大定格、ESD、内蔵プルアップ）: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- arcade-projects「Console JAMMAizer」スレッド（1k プルアップの議論、検索要約経由）: https://www.arcade-projects.com/threads/console-jammaizer-easily-connect-home-consoles-to-your-jamma-arcade-cabinet.10074/page-26
- Astro City 取扱説明書 p.31、Egret II 配線図、Windy 束線図（拡張ボタンの配線）: https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf 、https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg 、https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg
- falz.net（pi2jamma の 74LS165 × 3）: https://falz.net/wiki/Pi2jamma_hardware_and_software_info
- cspang1/jcap（10k SIP + 74HC165 × 2）: https://github.com/cspang1/jcap
- Arcade Otaku Wiki「JAMMA」（Service / Test / Tilt）: https://wiki.arcadeotaku.com/w/JAMMA

### 1.8 コイン・カウンタ・ロックアウト
- 旭精工 AD-81P2: https://www.asahiseiko.com/product/139/
- 旭精工 マイクロスイッチ D2MC-01F1: https://www.asahiseiko.com/product/374/
- Omron D2MC データシート: https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2mc.pdf
- 旭精工 AE-204D: https://www.asahiseiko.com/product/148/
- 旭精工 AE-192D（検索要約経由）: https://www.asahiseiko.com/product/146/
- 旭精工 ブロッカー（QL-102、QM-5、QL-203、SB-101）: https://www.asahiseiko.com/product/366/
- はてなブログ「工作と競馬2」（HX-616 のパルス幅）: https://dekuo-03.hatenablog.jp/entry/2020/01/30/224222
- arcadecontrols forum（電子メックのパルス幅、検索要約経由）: http://forum.arcadecontrols.com/index.php?topic=153821.0
- ameblo tarcade（New Astro City の AD-81P）: https://ameblo.jp/tarcade/entry-12686617268.html
- Cyber Lead 取扱説明書 p.57/59（AD-81P3、NX-06PD 5VDC）: https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf
- Astro City 取扱説明書 p.30-31（COIN METER の配線）: https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf
- Windy 束線図（GX-06PD の配線）: https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg
- Egret II 配線図（JAMMA 8 = COUNTER）: https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg
- arcade-projects「Naomi universal coin meter」: https://www.arcade-projects.com/threads/naomi-universal-coin-meter.32723/
- NeoGeo Dev Wiki「Coin counter」: https://wiki.neogeodev.org/index.php?title=Coin_counter&action=raw （https://wiki.neogeodev.org/index.php/Coin_counter ）
- NeoGeo Dev Wiki「Coin lockout」: https://wiki.neogeodev.org/index.php?title=Coin_lockout&action=raw （https://wiki.neogeodev.org/index.php/Coin_lockout ）
- ライン精機 MZ シリーズ: https://www.line.co.jp/product/2104/
- Kessler-Ellis カタログ（検索要約経由）: http://kepsales.com/pdf/KEP_ii_catalog.pdf
- arcadecontrols forum（12V カウンタのコイル抵抗、検索要約経由）: https://forum.arcadecontrols.com/index.php?topic=52711.0
- arcadecontrols forum（小信号トランジスタと逆バイアスダイオード、第1パス、検索結果）: https://forum.arcadecontrols.com/index.php/topic,85039.0.html
- arcade-museum「Coin counter help - suppression diode voltage」: https://forums.arcade-museum.com/threads/coin-counter-help-suppression-diode-voltage.420173/
- Mike's Arcade「Dbl-JAMMA」説明書: https://www.mikesarcade.com/estore/datasheets/Dbl-JAMMA.pdf
- TI ULN2003A データシート: https://www.ti.com/lit/ds/symlink/uln2003a.pdf
- njz3/jammamia（ULN2003 の記述、8/J・9/K は NC）: https://github.com/njz3/jammamia

### 1.9 オープンハードウェアの回路例と JLCPCB 分類
- ole00/orb: https://github.com/ole00/orb 、回路図 https://raw.githubusercontent.com/ole00/orb/master/orb03.pdf 、BOM https://raw.githubusercontent.com/ole00/orb/master/bom.txt
- MisterJamma/DE10Jamma: https://github.com/MisterJamma/DE10Jamma 、netlist https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/DE10Jamma.net 、README https://raw.githubusercontent.com/MisterJamma/DE10Jamma/master/README.md
- KabukiFlux/jammanator-pi: https://github.com/KabukiFlux/jammanator-pi
- ninomegadriver/PiPicoJamma: https://github.com/ninomegadriver/PiPicoJamma
- fenlogic/vga666: https://github.com/fenlogic/vga666
- KabukiFlux/bad_raspi_jamma: https://github.com/KabukiFlux/bad_raspi_jamma
- KabukiFlux/JAMMA_2player_xbox360: https://github.com/KabukiFlux/JAMMA_2player_xbox360
- yoonjustin/WinchesterPCB: https://github.com/yoonjustin/WinchesterPCB
- charcole/MiniGun: https://github.com/charcole/MiniGun
- kamencesc/Supergun-Basica: https://github.com/kamencesc/Supergun-Basica
- Hackafe/diy-arcade-jamma-pcb: https://github.com/Hackafe/diy-arcade-jamma-pcb
- cspang1/jcap: https://github.com/cspang1/jcap
- misteraddons/MiSTercadeV1 / V2、MiSTer-DB9/JAMMA_MiSTer（回路情報なし。URL はノートに無い）
- njz3/jammamia: https://github.com/njz3/jammamia
- jzdziarski/jamma: https://github.com/jzdziarski/jamma
- Arthrimus/Console-JAMMAizer: https://github.com/Arthrimus/Console-JAMMAizer
- RetroRGB「Console JAMMAizer by Arthrimus」: https://retrorgb.com/console-jammaizer-by-arthrimus.html
- Hackster「CoinOp Connect」: https://hackster.io/news/marco-guidolin-s-coinop-connect-connects-pcs-to-classic-non-jamma-arcade-cabs-with-no-damage-06493b9b4fee
- falz.net（pi2jamma）: https://falz.net/wiki/Pi2jamma_hardware_and_software_info
- Raspberry Pi「Hardware design with RP2040」: https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf
- Raspberry Pi VGA KiCad 一式: https://datasheets.raspberrypi.com/rp2040/VGA-KiCAD.zip
- Pico データシート: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- RP2040 データシート: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- NeoGeo Dev Wiki「Coin lockout」「Coin counter」: https://wiki.neogeodev.org/index.php/Coin_lockout 、https://wiki.neogeodev.org/index.php/Coin_counter
- JLCPCB 部品ライブラリ API（クラス、在庫、価格）: https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- JLCPCB 部品検索画面（Promotional Extended フィルタ）: https://jlcpcb.com/parts/componentSearch?searchTxt=74HC
- JLCPCB partdetail C5605: https://jlcpcb.com/partdetail/Nexperia-74HC14D653/C5605
- CDFER jlcpcb-components-basic-preferred.csv: https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv
- jlcsearch: https://jlcsearch.tscircuit.com/components/list.json?search=C5605
- jlcparts cache: https://yaqwsx.github.io/jlcparts/data/cache.zip
- LCSC 商品 API: https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C16501
- 秋月電子 LM386G-D08: https://akizukidenshi.com/catalog/g/g114548/
- 秋月電子 M2073: https://akizukidenshi.com/catalog/g/g117431/
- 秋月電子 TDA2822L: https://akizukidenshi.com/catalog/g/g109720/
- 秋月電子 AE-PAM8012: https://akizukidenshi.com/catalog/g/g108217/
- 秋月電子 オーディオアンプ検索: https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%82%AA%E3%83%BC%E3%83%87%E3%82%A3%E3%82%AA%E3%82%A2%E3%83%B3%E3%83%97&search=search
- 秋月電子 ポリスイッチ検索: https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=%E3%83%9D%E3%83%AA%E3%82%B9%E3%82%A4%E3%83%83%E3%83%81&search=search
- 秋月電子 USB コネクター検索: https://akizukidenshi.com/catalog/goods/search.aspx?search=x&keyword=USB%E3%82%B3%E3%83%8D%E3%82%AF%E3%82%BF%E3%83%BC&search=search

### 1.10 設計目標値
- 1.4〜1.8 節の出典と同じ（Blast City 取説、Arcade Otaku Blast City、NeoGeo Dev Wiki Video DAC、MTC 9000、K7000、MAME、New Astro City 取説、Mean Well RT-65、JST GEC、CRE401、DE10Jamma、Omron D2MC、旭精工、ライン精機、KEP、TI ULN2003A）。

### 2. 第1次調査からの訂正
- 各訂正の根拠は、上記 1.1〜1.9 の出典のうち該当するもの。特に: Hirose CR7 カタログ https://s1.dtsheet.com/store/data/002648525.pdf 、Sullins カタログ https://s3.amazonaws.com/catalogspreads-pdf/PAGE74-75%20.156%20LP%20DS%20EYE%20RA.pdf 、JST GEC https://datasheet.octopart.com/GEC-561-JST-datasheet-180492417.pdf 、JLCPCB Gold Fingers https://jlcpcb.com/help/article/jlcpcb-gold-fingers 、JLCPCB hard-gold https://jlcpcb.com/blog/hard-gold-pcb-finish 、DE10Jamma https://github.com/MisterJamma/DE10Jamma 、estechnical/jammakludge https://github.com/estechnical/jammakludge 、Astro City 取説 https://www.hard--candy.com/wiki/uploads/AstroCity/Downloads/AstroCityMan.pdf 、New Astro City 取説 https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf 、Egret II 配線図 https://www.hard--candy.com/wiki/uploads/EgretII/Downloads/Schematics.jpg 、Windy 束線図 https://www.hard--candy.com/wiki/uploads/Windy/Downloads/Specs.jpg 、Cyber Lead 取説 https://www.hard--candy.com/wiki/uploads/CyberLead/Downloads/CyberLead-Manual.pdf 、Blast City 取説 https://www.hard--candy.com/wiki/uploads/BlastCity/Downloads/BlastCityBassFishing-Manual.pdf 、Mean Well RT-65 https://www.meanwell.com/Upload/PDF/RT-65/RT-65-SPEC.PDF 、mourix/CRE401 https://raw.githubusercontent.com/mourix/CRE401/main/README.md 、Arthrimus/Console-JAMMAizer https://github.com/Arthrimus/Console-JAMMAizer 、ORB BOM https://raw.githubusercontent.com/ole00/orb/master/bom.txt 、JLCPCB API https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList 、JLCPCB 発注ページ https://cart.jlcpcb.com/quote 、JLCPCB PCBA Capabilities https://jlcpcb.com/capabilities/pcb-assembly-capabilities 、ライン精機 MZ https://www.line.co.jp/product/2104/ 、旭精工 AE-204D https://www.asahiseiko.com/product/148/ 、Omron D2MC https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2mc.pdf 、RP2040 データシート https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf

### 3. 未確認事項
- 規格書原本の探索経路: jaia.jp https://jaia.jp/reference/ 、旧 jamma.or.jp のアーカイブ http://web.archive.org/web/20180110070223/http://www.jamma.or.jp/ （本環境から取得不可）
- そのほかは 1.1〜1.9 の出典を参照。

### 4. ユーザー要求への影響
- PCBA の区分と料金: https://jlcpcb.com/capabilities/pcb-assembly-capabilities 、https://jlcpcb.com/solutions/pcb-prototype-assembly 、https://jlcpcb.com/help/article/pcb-assembly-price 、https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype
- 実見積と分離案の見積: https://cart.jlcpcb.com/quote
- 秋月電子の送料: https://akizukidenshi.com/catalog/pages/buy.aspx
- 部品クラス: https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
- 秋月電子の部品: https://akizukidenshi.com/catalog/g/g108217/ 、https://akizukidenshi.com/catalog/g/g117431/ 、https://akizukidenshi.com/catalog/g/g114548/
- Pico の電源 OR 接続: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- Omron D2MC（最小負荷）: https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2mc.pdf
- TI ULN2003A（VCE(sat)）: https://www.ti.com/lit/ds/symlink/uln2003a.pdf
- New Astro City 取説（電源容量の制限）: https://www.hard--candy.com/wiki/uploads/NewAstroCity/Downloads/NewAstroCity-Manual.pdf
- そのほかは 1.1〜1.9 の出典を参照。
