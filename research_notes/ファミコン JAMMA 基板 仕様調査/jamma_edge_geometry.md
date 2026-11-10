# JAMMA 56ピン エッジ(ゴールドフィンガー)の機械寸法と製造指定 — 第2パス(ギャップ解消)

(調査日 2026-11-10。対象: 第1パス `jamma_standard.md` の「機械寸法」Gaps。一次資料 = 嵌合コネクタのメーカー図面2社、公開フットプリント実ファイル3系統、JLCPCB 公式ヘルプ/発注ページ。各事実に URL を付記。自分の工学判断は「推論」と明記。確認できなかったものは「未確認」。)

---

## 1. 嵌合コネクタ(メス側)のデータシートが規定する「適合基板」寸法と定格

### Takeaway
JAMMA ハーネス側に使われる 0.156in(3.96mm)ピッチ 56極(28×2)カードエッジコネクタは、Hirose CR7E-56DB-3.96E と Sullins EBM28D 系の2社図面で確認できた。Hirose は適合基板を「フィンガ幅 2.3±0.1、ピッチ 3.96±0.05、両端フィンガ中心間 106.98±0.08、タング幅 114.8 0/−0.2、基板厚 1.6±0.15、端面両面 C0.5、コンタクト位置キー溝 幅 2.5 +0.1/0・深さ 11 +0.5/0」と規定し、定格は両社とも 1接点 3A。

### Cited Findings
**Hirose CR7 シリーズ(3.96mm / 4mm Pitch Card Edge Connector)カタログ** — [dtsheet 経由 PDF](https://s1.dtsheet.com/store/data/002648525.pdf)(取得元ページ [dtsheet.com/model/1263367](https://dtsheet.com/model/1263367)。hirose.com 本体は本環境から 403 "Forbidden")
- 定格: "Current rating: 3A"、"Voltage rating: 600V AC"、接触抵抗 "15m ohms max."(100mA)、挿抜 500回後も 15mΩ max、使用温度 −30〜+85℃。
- 接点数ラインナップ: 3.96mm ピッチ(E モールド)12/20/30/36/44/56/72/80、4mm ピッチ(C モールド)20/28/36/44/56。→ **56極の 4mm ピッチ版 CR7C-56DB-4E/-4DS が実在**。
- 56極(3.96)本体: CR7E-56DB-3.96E(アイレット)/ -3.96DS(スルーホール)、A=133.7(全長)、B=126(取付穴間)、C=118.1、D=115(基板挿入口長)、E=106.92(27×3.96)、F=11.1(本体厚)、G=117.1。図中に「基板挿入深さ 8.5」、本体高さ 12、総高 19.4。
- **「PCB Dimensions 3.96 pitch」図**(カタログ A11 頁、本調査で 500dpi に拡大して判読):
  - フィンガ幅 **2.3±0.1**、ピッチ **3.96±0.05**
  - A(両端フィンガ中心間)±0.08: 56極 = **106.98**
  - B(タング=差込部の全幅)0/−0.2: 56極 = **114.8**
  - 基板厚 **1.6±0.15**、先端は両面 **C0.5**(0.5mm×45°の面取り)、タング外側の角も C0.5
  - "Mis-insertion preventive key (Recommended)" として2種のキー溝: **コンタクト位置に置く広い溝 2.5 +0.1/0**(深さ **11 +0.5/0**、溝の入口両側 C0.5、溝中心はコンタクト中心線上)と、コンタクト間に置く狭い溝 **1 +0.1/0**(深さ 10)。
  - 寸法 "10" は先端から基板の肩(タングの付け根)までの線として描かれている(図の読み取り。数値の意味は図からの判読であり本文説明は無い)。
  - 注記 "To use the polarizing key, insert the polarizing key so as to hit the mold bottom."
- キー部品: CR7C-GPIN(厚 0.5、POM)、CR1-GPIN(厚 2.0、幅 2.5、ABS)、HIF5B-GPIN(厚 0.5)。→ 厚 2.0 の CR1-GPIN がコンタクト位置用(2.5mm 溝)、厚 0.5 品がコンタクト間用(1mm 溝)に対応(推論: 寸法の一致から)。
- 4mm ピッチ版の適合基板: フィンガ幅 2.3±0.1、ピッチ 4±0.05、56極 A=108.0、B=107.8(B<A となっており表の誤記の可能性。未確認)。
- 端子番号: 1–28 / A–f、"G, I, O, Q, g, i, o, q" は不使用。

**Hirose CR7E-30DB-3.96E(72) 個別図面 ADC-016737-72-02(2018-05-14)** — [chipdip 経由 PDF](https://static.chipdip.ru/lib/690/DOC043690981.pdf)
- 接点めっき「(接触部)Ni2.5µm+Au0.2µm」、端子「(実装部)Ni2.5µm+Sn2µm」、絶縁体ポリカーボネート UL94V-2。
- 「(8.5)(基板挿入深さ)」、「5.3±0.4(接点位置)」(本体上面=挿入口から接点までの距離)、接触幅「(2)(接触巾)」、ピッチ 3.96±0.2。
- → 推論: 基板を 8.5mm 挿入したとき、接点は基板端から約 8.5−5.3 = **3.2±0.4mm** の位置でフィンガに触れる。
- Digi-Key では CR7E-56DB-3.96E(72) が "Obsolete" 表示(検索結果要約経由、[Digi-Key](https://www.digikey.com.au/en/products/detail/hirose-electric-co-ltd/CR7E-56DB-3-96E-72/8561491))。CR7E-56DA-3.96E は「Conn Card Edge 56 POS 3.96mm Solder ST Panel Mount」(検索要約経由、[electronicsdatasheets](https://www.electronicsdatasheets.com/manufacturers/hirose-electric-uk-ltd/parts/cr7e-56da-396e))。DA 版の個別図面は入手できず、未確認。

**Sullins Female Card Edge .156" [3.96mm], .431" insulator(EBM28D… = 28/56 position)** — [Sullins catalog p.74–75 PDF](https://s3.amazonaws.com/catalogspreads-pdf/PAGE74-75%20.156%20LP%20DS%20EYE%20RA.pdf)(Digi-Key EBM28DRXH 製品ページから辿った公式カタログ)
- "Accommodates .062" ± .008" [1.57 mm ± 0.20 mm] PC board"
- "3 Amps current rating for one contact energized (for 5 Amps application, consult factory)"、"30 milli Ohms maximum at rated current"
- "INSERTION DEPTH .265 [6.73]"
- 28/56: A=4.212" = **106.98mm**(両端コンタクト間、= 27×0.156")、B=4.532" = **115.11mm**(B は本体開口長と読める)、C=118.16、D=126.11(取付穴間)、E max=135.48(全長)
- 極性キー: "PLM-K2 KEY IN CONTACT" 厚 **.093" [2.36]**、"PLA-K1 KEY IN BETWEEN CONTACTS" 厚 .030" [0.76]。
- 接点めっき標準 "B = .000010" Gold"(0.25µm)、オプション .000030"(0.76µm)。"LETTERS G, I, O & Q NOT USED"。
- Digi-Key: EBM28DRXH = 56 positions, Card Thickness 0.062"(1.57mm), Pitch 0.156"(3.96mm), Contact Finish Thickness 10.0µin — [Digi-Key](https://www.digikey.com/en/products/detail/sullins-connector-solutions/EBM28DRXH/927310)

**市販 JAMMA 56P コネクタ(ホビー向け)**: Paradise Arcade の 56P 直角品は「Gold-plated contacts」「Standard JAMMA pinout compatible」以外の寸法・定格記載なし — [Paradise Arcade](https://paradisearcadeshop.com/products/jamma-56-pin-right-angle-connector)

### Inferences
- **ピッチの真値は 0.156in = 3.9624mm**(推論、根拠: Sullins の A=4.212"=106.98mm、Hirose も 56極だけ A=106.98 と記載。27×3.96=106.92 との差 0.065mm)。Hirose カタログ内でも 30極は 55.44(=14×3.96)と 3.96 基準、56/72極は 0.156in 基準で不統一。どちらで作っても累積差 0.065mm はフィンガ幅公差(±0.1)以内で実害なし。推奨はインチ基準 3.9624。
- タング幅は Hirose 114.8 0/−0.2(=114.6〜114.8)、Sullins の開口 115.11±0.20。**大きすぎると入らない、小さすぎても横ずれが増えるだけ**なので、114.6 が両社に対し安全側(推論)。
- 1接点 3A(両社)。JAMMA の +5V は 3/4/C/D の4接点 → 理論 12A、GND は 1/2/27/28/A/B/e/f の8接点(推論: 全接点同時通電時はディレーティングが必要で、"one contact energized" 条件の 3A をそのまま4倍してはいけない)。本基板の想定消費(1A 前後、推論)には十分。
- コネクタ側の金は 0.2〜0.25µm(Hirose/Sullins 標準)で、基板側が ENIG(0.025〜0.05µm)でも「金対金」接触にはなる(推論)。

### Gaps
- Hirose CR7E-56DA-3.96E(DA = パネル取付型)の個別図面は未取得(hirose.com が 403)。DB 版と適合基板寸法は同一シリーズ共通図なので同じと推定(推論)。
- Sullins の接点位置(先端から何 mm で接触するか)は図に無く 未確認。
- 日本の筐体(アストロシティ等)のハーネスに実際どのメーカー品が付いているかは 未確認(汎用 56P 品が多いとの情報も出典無し)。

---

## 2. 公開オープンハードウェアのフットプリント実ファイル(3系統+派生)

### Takeaway
3つの独立プロジェクト(DE10Jamma=KiCad、jzdziarski/jamma=KiCad 9、ORB=gEDA PCB)の実ファイルを git clone して座標を読んだ。3者とも「パーツ面(F.Cu/top)に 1–28、ハンダ面に A–f、同番号は表裏同じ X 位置」「パーツ面を見て端子端を上にすると 1番が右端(=端子端を下にすると 1番が左端)」「キー溝は 6 と 8 の間(7/H 位置)」で一致。フィンガ幅は 2.03〜2.35mm、長さ 8〜10mm、溝幅 2.5〜3.81mm、溝深さ 10〜11.5mm、タング幅 111〜114.6mm とばらつく。

### Cited Findings
実測値の表(座標はファイルから計算。「端からの距離」は Edge.Cuts の先端線からパッド先端まで)

| 項目 | Hirose 適合基板図 | DE10Jamma(KiCad) | jzdziarski Universal JAMMA Edge(KiCad 9) | ORB orb03(gEDA) |
|---|---|---|---|---|
| 出典 | [CR7 catalog](https://s1.dtsheet.com/store/data/002648525.pdf) | [MisterJamma/DE10Jamma](https://github.com/MisterJamma/DE10Jamma) `Jamma.pretty/JAMMA-56.kicad_mod`, `DE10Jamma.kicad_pcb` | [jzdziarski/jamma](https://github.com/jzdziarski/jamma) `CAD/Universal JAMMA Edge.kicad_pcb` | [ole00/orb](https://github.com/ole00/orb) `orb03.pcb`, `gerbers/` |
| ピッチ | 3.96±0.05(56極 A=106.98) | 3.96 一定(1↔28 = 106.92) | 手置きで不均一 3.92〜4.01、1↔28 = 106.84 | 3.956 一定(1↔28 = 106.812) |
| フィンガ幅 | 2.3±0.1 | 2.35 | 2.2 | 2.032(80mil 角アパーチャ) |
| フィンガ長 | 図で約9mm(寸法記入無し) | ライブラリ版 8.0 / 基板埋込版 10.0 | 10.0 | 9.652(300mil 線+80mil 角) |
| 先端からパッドまで | 記載無し(先端まで描画) | 基板版 0.05(ライブラリ版を同位置に置くと 1.05) | 1.13 | 約0.1 |
| キー溝 幅×深さ | 2.5 +0.1/0 × 11 +0.5/0(入口 C0.5) | 3.0 × 10.0 | 2.5 × 11.5 | 3.81(150mil) × 10.92(430mil) |
| キー溝中心と7番中心 | 一致(図) | 一致(174.584) | 179.25 vs 理想 179.19 | 4700mil vs 4698mil |
| タング幅 | 114.8 0/−0.2 | 114.6(基板幅そのもの) | 111.0(基板幅そのもの) | 113.03、角に 25mil 面取り |
| 外端フィンガ中心→タング側面 | (114.8−106.98)/2 = 3.91 | 3.84 | 約2.08 | 2.99 / 3.23(非対称) |
| 肩(タング付け根)の深さ | 図で 10 | 肩無し(全幅) | 肩無し(全幅) | 約12.07(475mil、肩に 50mil 面取り) |
| 基板厚 | 1.6±0.15 | 1.6(general thickness) | 1.6(stackup) | 1.6(README "Board thickness: 1.6 mm", "Copper thickness: 1 oz") |
| マスク | — | 先端〜10.05mm の帯を F/B 両面で全面開口(gr_poly on F.Mask/B.Mask) | パッド単位開口 | パッド単位(mask 2.0mm) |

- DE10Jamma の注意点: ライブラリ `JAMMA-56.kicad_mod` はパッド 2.35×8・裏パッドのレイヤ指定 "B.Cu B.Mask F.Mask"、基板ファイルに埋め込まれた版は 2.35×10 で裏パッドが "B.Cu F.Paste F.Mask"(B.Mask が無い)。裏面マスクは別途 B.Mask ポリゴンで開けて救っている。→ そのままコピーすると裏フィンガがマスクで覆われる/ペーストが載る恐れ(推論)。
- jzdziarski/jamma は README で "educational use only"(第1パスの記載どおり)。寸法の参照のみ。
- [estechnical/jammakludge](https://github.com/estechnical/jammakludge) の `jamma.pretty/JAMMA-56.kicad_mod` は 2.35×8・ピッチ 3.96 で DE10Jamma 版と同一形状(派生と判断、独立ソースとして数えない)。
- [yoonjustin/WinchesterPCB](https://github.com/yoonjustin/WinchesterPCB) の `JAMMA56HALF`(2.3×5 パッド、ピッチ 3.96、キー溝無し、タング 110mm×6mm)はスーパーガン側でメスコネクタをストラドル実装するための形状で、ゲーム基板のフィンガではない(参考外)。
- Frank_fjs の JAMMA フィンガーボード(Arcade-Projects、要登録): "124mm x 40mm", "2 layer PCB", "Four M3 mounting holes.", "Dimensionally accurate jamma finger with rounded corners, solder mask cutout and key notch." JLCPCB で製造し "They pass through a cps2 board on my astro city without a hiccup." — [Arcade-Projects thread](https://www.arcade-projects.com/threads/jamma-fingerboards.7042/)(寸法値は非公開で 未確認)
- 3者共通の向き: パーツ面 1–28。KiCad/gEDA 座標(Y 下向き)で端子端を上に置いたとき 1番が右端、28番が左端。キー溝は1番側から7番目。日本語の配線表も「部品面 1〜28 / はんだ面 A〜f」 — [wdic JAMMAハーネス](https://www.wdic.org/w/MOE/JAMMA%E3%83%8F%E3%83%BC%E3%83%8D%E3%82%B9)、[calm-life.jp JAMMA 規格 56P](https://www.calm-life.jp/game/connect/jamma.html)

### Inferences
- 実物で動いている3設計の範囲(幅 2.03〜2.35、長さ 8〜10、溝 2.5〜3.81 × 10〜11.5)はいずれもコネクタに挿さっているので、Hirose 値を中心にこの範囲内で選べば実用上問題ない(推論)。
- 「先端までパッドを伸ばす」DE10Jamma/ORB 方式は JLCPCB の面取りで銅が露出・剥離する(第4節)。JLCPCB では先端から 1.13mm 以上下げる必要がある。

### Gaps
- 日本製の実物 JAMMA 基板(カプコン、セガ等)のフィンガ実測値は入手できず 未確認(実物ノギス計測が最終確認として推奨)。

---

## 3. 4.00mm ピッチ説と原典(JAMMA 規格書)

### Takeaway
「古い基板は 4.00mm ピッチ」の直接証拠(具体的な基板名+実測)は見つからなかったが、Hirose が 4mm ピッチ 56極カードエッジ(CR7C-56DB-4E)を製品化していることは確認でき、メトリック 4mm 系が国内に存在したことは裏付けられる。JAMMA(56ピン)規格の原本・スキャンは3経路以上試したが入手できず、-5V が公式規定かは依然 未確認(ただし国内の配線表はすべて 5/E = −5V)。

### Cited Findings
- Hirose CR7C(4mm pitch mold)に 56極あり、適合基板 A=108.0 — [CR7 catalog](https://s1.dtsheet.com/store/data/002648525.pdf)
- 4mm ピッチ説の唯一の出典は第1パスのフォーラム投稿(確度低) — [arcade-projects](https://www.arcade-projects.com/goto/post?id=410606)
- 「JAMMA VIDEO規格」は 56ピンではなく JVS(新JAMMA、RS-485/USB)を指す。第3版のドラフト PDF が非公式に流通 — [daifukkat.su jvs_wip.pdf](http://daifukkat.su/files/jvs_wip.pdf)、旧 jamma.or.jp の資料集に JAMMA VIDEO規格第3版があったとの記載 — [usada.yabou.jp](https://usada.yabou.jp/game/acgame_jvs.html)(リンク先 `http://web.archive.org/web/20180110070223/http://www.jamma.or.jp/`)
- 56ピン規格の名称・年: 「JAMMA規格(JS規格)」「1986(昭和61)年以降」、−5V は 5/E、逆差防止キーは 7/H — [wdic](https://www.wdic.org/w/MOE/JAMMA%E3%83%8F%E3%83%BC%E3%83%8D%E3%82%B9)。英語版 Wikipedia は 1985 年(第1パス記載)。
- 個人サイトの配線表(2006)も 5/E = −5V、7/H = 逆挿し防止キー — [calm-life.jp](https://www.calm-life.jp/game/connect/jamma.html)、[fujikko](http://www3.big.or.jp/~fujikko/kiban/jamma.html)
- JAIA 公式「資料」ページには JAIA Digital 規格・景品ガイドライン等のみで 56ピン JAMMA 規格書は無い — [jaia.jp/reference](https://jaia.jp/reference/)。JAIA の 2022 年ガイドラインは旧 JAMMA の「課金などの情報収集端末の取付容易化ガイドライン」(9極コネクタ)で別物 — [JAIA PDF](https://jaia.jp/wp-content/uploads/2022/08/%E6%B1%BA%E6%B8%88%E3%81%AA%E3%81%A9%E3%81%AE%E6%83%85%E5%A0%B1%E5%8F%8E%E9%9B%86%E7%AB%AF%E6%9C%AB%E3%81%AE%E5%8F%96%E4%BB%98%E5%AE%B9%E6%98%93%E5%8C%96%E3%82%AC%E3%82%A4%E3%83%89%E3%83%A9%E3%82%A4%E3%83%B320220801%E6%94%B9%E5%AE%9A.pdf)
- 試行した経路: (1) jaia.jp 資料ページ(該当無し)、(2) web.archive.org / archive.ph の jamma.or.jp アーカイブ(本環境から接続リセットで取得不可)、(3) 日本語個人サイト・用語辞典(配線表のみ、原典引用無し)、(4) 英語検索 "JAMMA standard original document scan"(原本無し)。

### Inferences
- 4mm 基板を 3.9624mm コネクタに挿した場合の累積ずれは 27×0.0376 = 1.02mm、中央合わせで両端 ±0.51mm。フィンガ半幅 1.15mm、接点幅約 2mm なので接触はするが余裕は小さい(推論)。新規設計は 0.156in で作れば問題ない。
- −5V は本基板では未使用・無接続とする(第1パス推論を維持)。公式規定かどうかは設計に影響しない。

### Gaps
- JAMMA(JS)規格書の原本・スキャン: 未確認(web.archive.org が使える環境で `jamma.or.jp` の資料集を再確認すべき)。
- 4.00mm ピッチの具体的な基板名と実測: 未確認。

---

## 4. JLCPCB のゴールドフィンガー指定(2026-11 時点)

### Takeaway
JLCPCB(リジッド FR-4)は電解硬質金を提供せず、フィンガは ENIG(金 1 または 2 µ"=約 0.025/0.05µm)でのみ金になる。発注画面の "Gold Fingers: Yes" と面取り角 30°/45°(30° 推奨)を選ぶ。1.6mm 基板では 30° で約 1.13mm、45° で約 0.74mm のコッパーセットバック(先端からフィンガまでの銅無し距離)が必要。面取りは 50×50mm 未満の基板/パネルや V カット内側のフィンガには不可で、直線エッジ全体が面取りされる。

### Cited Findings
- JLCPCB Help "JLCPCB Gold Fingers"(Last updated on Nov 10, 2026) — [jlcpcb.com/help/article/jlcpcb-gold-fingers](https://jlcpcb.com/help/article/jlcpcb-gold-fingers)
  - "only when ENIG is chosen, the fingers for your PCB will be with gold, if you choose HASL surface treatment, then it will be covered with tin."
  - "Chamfers are not available on boards smaller than 5x5cm."
  - "If there is fingers in your file and it is panel with v-cut, then the fingers can not be made with chamfer since the fingers will be in the middle of the PCB."
  - "The available bevel angles are 30° and 45°. ... we recommend prioritizing a 30° bevel."
  - "The gold finger area must have the solder mask fully opened (clearance window). For designs without a solder mask opening, JLCPCB will automatically apply a solder mask opening by default."
  - "The red frame indicates the beveled area. ... this area can not have copper."
  - "The length and width of a single board or panel with gold fingers shall not be less than 50mm."
  - 同記事の図(画像 `copper-setback-definition.png`): **1.6mm 板厚で 30°±5° → Copper Setback "Approx. 1.13 mm"、45°±5° → "Approx. 0.74 mm"**、"A thicker board requires a longer copper setback."、セットバック不足時はエンジニアがフィンガを短くする(図の Before/After)。
- JLCPCB Help "Instructions for chamfering gold fingers" の図: "As the entire edge will be chamfered, ensure enough clearance between traces and the board edge"(機械のスロットに基板を通してエッジ全長を削る)、パネルは背中合わせ配置でフィンガ辺を外周に出すのが正 — [jlcpcb.com/help/article/instructions-for-chamfering-gold-fingers](https://jlcpcb.com/help/article/instructions-for-chamfering-gold-fingers)
- 発注ページ(cart.jlcpcb.com/quote の静的テキスト): "Gold Fingers ... Only when ENIG surface finish is chosen, the fingers will be gold-plated. If you choose HASL surface finish, we will use HASL as edge connect plating." 選択肢 "No / Yes"。"Board thickness tolerance is +/-10%."、OSP は "Not supported for ... physical contact areas (e.g., gold fingers, keypads)" — [cart.jlcpcb.com/quote](https://cart.jlcpcb.com/quote)
- 硬質金: "does not offer electroplated hard gold finish"、"JLCPCB applies our precision Electroless Nickel Immersion Gold (ENIG) finish to the gold fingers."(2026-02-28 公開、2026-08-08 更新) — [JLCPCB blog hard-gold-pcb-finish](https://jlcpcb.com/blog/hard-gold-pcb-finish)
- ENIG 厚: "JLCPCB offers gold thicknesses of 1 or 2 microinches."、Ni 約 3〜6µm(Last updated Nov 10, 2026) — [JLCPCB surface finish](https://jlcpcb.com/help/article/jlcpcb-surface-finish)
- 追加費用: ENIG 露出面積が 30% を超える分について 1U" は $0.8992/m²/1%、2U" は $1.7985/m²/1%(Last updated Nov 10, 2026) — [In what cases will there be charged extra?](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra)。ENIG 自体の基本加算額・"Gold Fingers: Yes" の加算額は見積画面(JS)でしか表示されず 未確認。第三者ガイドの「5枚で $10〜20」は出典無しで不採用 — [zbotic](https://zbotic.in/pcb-gold-fingers-edge-connector-design-guide/)
- JLCPCB ブログの面取り記述は自社ヘルプと一部食い違う: "bevel the board down to about 1/3 to 1/2 of its thickness" — [beveled-edges blog](https://jlcpcb.com/blog/beveled-edges-card-edge-connectors)。別ブログは「フィンガと外形の距離 0.5mm」と「1.0mm 以上」を併記して自己矛盾 — [pcb-gold-fingers blog](https://jlcpcb.com/blog/pcb-gold-fingers)。→ 2026-11-10 更新のヘルプ記事(1.13/0.74mm)を優先。
- 外形公差: CNC ルーティング ±0.2mm(通常)/±0.1mm(精密)、非めっきスロット最小幅 1.0mm(検索要約経由) — [JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)、[slot blog](https://jlcpcb.com/blog/reliable-pcb-slot-holes-design)
- めっきリード(バスバー): JLCPCB の資料には記載なし。PCBWay の金フィンガページも言及なし(角度 20/30/45°、60° も可、角度公差 ±5°、フィンガ〜外形 0.5mm 以上) — [PCBWay](https://www.pcbway.com/pcb_prototype/PCB_Gold_fingers.html)
- 実例: JLCPCB の ENIG フィンガでカートリッジを量産し接点摩耗の報告なし、という利用者投稿(検索要約経由、確度低) — [stardot forum](https://stardot.org.uk/forums/viewtopic.php?t=20829)
- 一般論: 硬質金 0.5〜1.5µm、ENIG 金 0.05〜0.1µm(JLCPCB ブログ記載の一般値) — [hard-gold blog](https://jlcpcb.com/blog/hard-gold-pcb-finish)。IPC の厚み規定(IPC-6012/4552)は原文未入手で 未確認。

### Inferences
- JLCPCB では ENIG(電解ではない)なので**めっきリード/バスバーは不要**(推論: 無電解プロセスの性質から。JLCPCB 側の明文は無い)。他社で電解硬質金を選ぶ場合はめっきリードが必要になるのが一般的だが本調査では出典未取得。
- JAMMA 基板は設置時・交換時に数回〜数十回挿抜する程度で、ENIG で実用上足りる見込み(推論。旧来の日本製アーケード基板には金でなく錫系に見えるエッジも多いとの愛好家証言あり — 検索要約経由・確度低 [classiccmp](https://classiccmp.org/mailman3/hyperkitty/list/test-drb@ccmp.vtda.org/message/Z4QCMRGYFVHVHKEKNFXUIKF4TCIJAI36))。
- タング幅 114.6mm が必須なので基板は必ず 100×100mm を超え、JLCPCB の 100×100 以下の最安枠には入らない(推論)。

### Gaps
- "Gold Fingers: Yes"+ENIG の実際の加算額(5枚・10枚)は 未確認(見積画面で要確認)。
- 30°/45° が「板面に対する角度」か「片側半角」かの定義は図からは半角(基板中心面からの角)と読めるが 未確認。

---

## 5. 基板外形の慣行(コネクタ奥行き・部品禁止域・取付穴・サイズ・向き)

### Takeaway
コネクタ本体は基板先端から 8.5mm(Hirose)/6.73mm(Sullins)まで被さり、基板面から約 4.75mm(Hirose 本体厚 11.1)張り出す。本体の耳(全長 133.7〜135.5mm)はタング両脇へ約 9.5〜10mm はみ出すので、タングより広い基板にするなら肩は先端から 10mm 以上(Hirose 図)、余裕を見て 12mm(ORB 実績)に置く。取付穴・最大サイズの JAMMA 公式規定は見つからなかった。

### Cited Findings
- Hirose: 基板挿入深さ 8.5、本体厚 F=11.1(56極)、本体全長 133.7、取付穴 φ3.3 ピッチ 126 — [CR7 catalog](https://s1.dtsheet.com/store/data/002648525.pdf)
- Sullins: 挿入深さ 6.73、全長 E max 135.48、取付穴ピッチ 126.11 — [Sullins catalog](https://s3.amazonaws.com/catalogspreads-pdf/PAGE74-75%20.156%20LP%20DS%20EYE%20RA.pdf)
- ORB は肩付きタング(タング長 約12mm、本体 6000×4825mil 枠内) — `orb03.pcb` [ole00/orb](https://github.com/ole00/orb)
- フィンガーボード例: 124×40mm、M3 取付穴4個 — [Arcade-Projects](https://www.arcade-projects.com/threads/jamma-fingerboards.7042/)
- jzdziarski Universal JAMMA Edge は M3(3.2mm)穴(`MountingHole_3.2mm_M3_Pad_Via`)、DE10Jamma は 3mm 穴(`MountingHole_3mm`)— 各 kicad_pcb
- 筐体側: Astro City 2 の基板取付板は約 48×40cm・厚さ約1cm の木板、電源位置のため余裕が少ないとの記述(Arcade Otaku Wiki、本体は Anubis で取得不可のため検索要約経由・確度低) — [Sega Astro City 2](https://wiki.arcadeotaku.com/w/Sega_Astro_City_2)、[arcadeotaku forum](https://forum.arcadeotaku.com/viewtopic.php?t=43430)。基板はプラスチック製の基板足(PCB feet)で板に固定するのが一般的(フォーラム、確度低) — [arcade-projects](https://www.arcade-projects.com/threads/pcb-holder-for-astro-city-cab.20532/)
- 向き: 配線表は「部品面 1〜28 / はんだ面 A〜f」 — [wdic](https://www.wdic.org/w/MOE/JAMMA%E3%83%8F%E3%83%BC%E3%83%8D%E3%82%B9)

### Inferences
- 部品禁止域: 先端〜12mm(肩まで)は両面とも部品・シルク・ビア禁止。先端〜1.2mm は銅禁止(面取り)。コネクタ本体は挿入深さより奥には来ないので、12mm より奥は高さ制限なし(推論)。
- 設置時の向き(部品面が上か横か)は筐体の取付板次第で規格化されていない(未確認)。
- 取付穴: JAMMA 規定は見つからず(未確認)。M3 用 φ3.2 を四隅(縁から 4mm 以上)に置けば、ねじ+スペーサでも汎用スナップ式基板足でも使える(推論)。
- サイズ: 筐体の取付板(数十 cm 角)に比べ、本基板(推定 150×120mm 前後)は制約にならない(推論)。

### Gaps
- アストロシティ/ブラストシティ/エッグレット II の基板取付スペースの公式寸法・JAMMA 基板の最大寸法規定: 未確認。
- 汎用 PCB 足の穴径(一般に φ3〜4mm と思われる)の出典: 未確認。

---

## 6. 推奨 KiCad フットプリント仕様(このまま作図可能な寸法)

### Takeaway
下表の値で、パーツ面(F.Cu)1–28・ハンダ面(B.Cu)A–f の両面 SMD パッドと Edge.Cuts を作れば、Hirose/Sullins 両図面と JLCPCB(ENIG・30°面取り)の制約を同時に満たす。各値の採用理由は右列(推論を含む)。

### Cited Findings
(根拠は第1〜5節の出典。以下は設計値のまとめ)

座標系: 原点 = 1番パッドの中心線と基板先端線の交点。X+ は 28番方向、Y+ は基板内側(先端から奥へ)。パーツ面を見て先端を下にした図で「1番が左、28番が右」(=第2節の3設計と同じ向き。KiCad 画面で先端を上にすれば 1番が右)。

| # | 項目 | 推奨値 | 出典ごとの値 | 採用理由 |
|---|---|---|---|---|
| 1 | ピッチ | **3.9624mm(0.156in)** | Hirose 3.96±0.05(56極 A=106.98)、Sullins 0.156"、DE10 3.96、ORB 3.956 | 両社の 56極 A=106.98 がインチ基準。3.96 でも累積 0.065mm で許容内 |
| 2 | パッド X 位置 | n番(n=1..6, 8..28)と対応文字: X = (n−1)×3.9624。1↔A, 2↔B, 3↔C, 4↔D, 5↔E, 6↔F, 8↔J, 9↔K, 10↔L, 11↔M, 12↔N, 13↔P, 14↔R, 15↔S, 16↔T, 17↔U, 18↔V, 19↔W, 20↔X, 21↔Y, 22↔Z, 23↔a, 24↔b, 25↔c, 26↔d, 27↔e, 28↔f(表裏同 X) | 3設計とも表裏同 X | 7/H はパッド無し |
| 3 | 両端パッド中心間 | 106.985 | Hirose/Sullins 106.98 | — |
| 4 | パッド幅 | **2.30mm** | Hirose 2.3±0.1、DE10 2.35、jz 2.2、ORB 2.03 | メーカー図の中心値。パッド間ギャップ 1.66mm |
| 5 | パッド範囲(Y) | **1.2 〜 10.0mm**(長さ 8.8、中心 Y=5.6) | JLC セットバック 30°で約1.13、Hirose 接点位置 約3.2±0.4、パッド長 8〜10(各設計) | 面取りで銅が出ない最小値+接点位置と挿入深さ 8.5 を十分覆う |
| 6 | パッド形状・層 | 角形 SMD、F 側: F.Cu+F.Mask、B 側: B.Cu+B.Mask。**ペースト層は付けない** | DE10 基板版は誤って F.Paste/F.Mask を裏パッドに付与 | ステンシルでフィンガにはんだが載るのを防ぐ |
| 7 | マスク開口 | 両面とも X = −3.81〜+110.795、Y = 0〜10.5 の帯を全面開口(パッド間もマスク無し) | JLC: フィンガ領域は全面開口必須・未指定なら自動開口。DE10 は帯で開口 | JLC 規定に一致させ DFM 差し戻しを避ける |
| 8 | 銅禁止 | Y = 0〜1.2 は全層銅禁止(ベタ・配線・ビア無し)、フィンガ帯(Y ≤ 10.5)内はパッド以外の銅・ビア・シルク無し、ベタは Y ≥ 11 から | JLC: 面取り域に銅不可 | 面取り時の銅露出・剥離防止 |
| 9 | パッドからの配線 | 各パッドの奥端(Y=10.0)から引き出す。電源/GND は 1mm 以上の太幅、複数ピン並列 | Sullins/Hirose 1接点 3A | 推論 |
| 10 | キー溝(7/H) | 中心 X = 6×3.9624 = **23.774**、幅 **3.0mm**(許容 2.5〜3.0)、深さ **11.5mm**、入口両角 0.5×45° 面取り、奥は R0.5 以上(ルータ径なり) | Hirose 2.5 +0.1/0 × 11 +0.5/0、DE10 3.0×10、jz 2.5×11.5、ORB 3.81×10.92、Sullins キー厚 2.36、Hirose CR1-GPIN 厚 2.0 | 汎用ハーネスのキー厚ばらつきと JLC 外形公差 ±0.2 を吸収するため 2.5 より広く、隣接パッドとの銅〜溝間 1.31mm を確保。深さは Hirose 範囲内 |
| 11 | タング幅 | **114.6mm**(X = −3.81 〜 +110.795) | Hirose 114.8 0/−0.2、Sullins 開口 115.11、DE10 114.6、ORB 113.03、jz 111 | Hirose 範囲下限=JLC 公差 ±0.2 でも 114.8 を超えない |
| 12 | 外端パッド中心→側面 | 3.81mm(パッド端→側面 2.66mm) | Hirose 3.91、DE10 3.84、ORB 2.99/3.23 | 上記タング幅から決まる |
| 13 | タング外角 | 0.5×45° 面取り(または R0.5) | Hirose C0.5、ORB 25mil 面取り | 挿入ガイド |
| 14 | 肩(タング付け根)位置 | 先端から **12.0mm** 以上(基板本体をタングより広くする場合) | Hirose 図 10、ORB 約12.07 | コネクタ耳(タング外へ約9.5mm)が先端から 8.5mm まで来るため。全幅=114.6 の場合は肩不要 |
| 15 | 基板厚 | **1.6mm**(JLC 公差 ±10% = ±0.16) | Hirose 1.6±0.15、Sullins 1.57±0.20、3設計とも 1.6 | — |
| 16 | 先端面取り | JLC 発注で **30°**(推奨)を選択 | JLC 30°/45°、Hirose C0.5 | JLC 推奨・挿入性。45° を選ぶ場合はセットバック 0.74 で可だが 1.2 のままで問題なし |
| 17 | 表面処理 | **ENIG(1U")+ Gold Fingers: Yes**。2U" は任意 | JLC: 硬質金なし、金は ENIG 時のみ | HASL だとフィンガが錫になる |
| 18 | 面付け | 単品発注(または フィンガ辺を外周に出す背中合わせ面付け)、V カット内側にフィンガを置かない | JLC ヘルプ | 面取り不可になるため |
| 19 | 基板最小寸法 | 50×50mm 以上(本設計はタングだけで 114.6 幅なので自動的に満たす) | JLC | — |
| 20 | 部品禁止域 | 先端〜12mm は両面とも部品・シルク禁止 | Hirose 挿入深さ 8.5、本体厚 11.1 | 推論 |
| 21 | 取付穴 | φ3.2(M3)を四隅、縁から 4mm 以上、タング近傍(先端〜12mm)には置かない | jz M3、DE10 3mm、フィンガーボード M3×4 | JAMMA 規定は見つからず(推論) |
| 22 | シルク | パーツ面のパッド奥(Y>11)に "1"・"28"、ハンダ面に "A"・"f"、パーツ面に "PARTS SIDE / 1-28" | 慣行 | 逆差し・誤配線防止(推論) |

### Inferences
- フットプリントは「両面 SMD パッド+Edge.Cuts を含まない」形にし、Edge.Cuts(タング・キー溝・肩)は基板側で描く方が、KiCad DRC(パッド〜外形クリアランス)設定と干渉しにくい(推論)。DE10Jamma もフットプリント外で Edge.Cuts を描いている。
- KiCad の "Board setup → Constraints → Copper to edge clearance" はフィンガ部で 1.2mm を満たすので、全体を 0.3〜0.5mm 程度に設定しても DRC エラーにならない(推論)。

### Gaps
- 実際の国内 JAMMA ハーネス(汎用品)への嵌合確認は実機でのみ可能: 未確認。

---

## 既存ノートへの訂正

### Takeaway
第1パス `jamma_standard.md` の機械寸法節には、事実誤認1件と不正確・不足が数件ある。

### Cited Findings
- **訂正1(誤り)**: 「既成KiCadフットプリント: 専用ライブラリは見つからず … DE10Jamma … も JAMMAエッジを持つ(CADフォーマットは未確認)」→ DE10Jamma は KiCad フットプリント `Jamma.pretty/JAMMA-56.kicad_mod`(パッド 2.35×8、ピッチ 3.96)を同梱しており、その派生が estechnical/jammakludge にもある — [DE10Jamma](https://github.com/MisterJamma/DE10Jamma)、[jammakludge](https://github.com/estechnical/jammakludge)
- **訂正2(不正確)**: 「接点は硬質金フラッシュ(ENIGでも足りる可能性)」→ 想定製造先 JLCPCB は電解硬質金を提供せず、フィンガは ENIG(金 1/2 µ")のみ — [JLCPCB hard-gold blog](https://jlcpcb.com/blog/hard-gold-pcb-finish)、[JLCPCB Gold Fingers](https://jlcpcb.com/help/article/jlcpcb-gold-fingers)
- **訂正3(精度)**: 「ピッチ 0.156in(3.96mm)」は正しいが、56極の両端間はインチ基準 106.98mm(3.9624mm×27)で、3.96mm×27=106.92 ではない — [Sullins](https://s3.amazonaws.com/catalogspreads-pdf/PAGE74-75%20.156%20LP%20DS%20EYE%20RA.pdf)、[Hirose](https://s1.dtsheet.com/store/data/002648525.pdf)
- **訂正4(未確認→確認)**: 「フィンガー幅・長さ…キー切欠き寸法と位置、面取り角度…未確認(一般に 2.5mm 幅程度との話)」→ メーカー適合基板図ではフィンガ幅 2.3±0.1、キー溝 2.5 +0.1/0 × 11 +0.5/0(コンタクト位置中心)、先端 C0.5、基板厚 1.6±0.15、タング幅 114.8 0/−0.2(第1節)。
- **訂正5(1ピン当たり電流の Gap)**: 「JAMMA公式の1ピン当たり電流定格 未確認」→ JAMMA 公式値は依然未確認だが、嵌合コネクタ定格は Hirose CR7・Sullins EBM とも 1接点 3A(第1節)。
- **補足(用語)**: 調査依頼文にある「JAMMA VIDEO規格」は JVS(新JAMMA)の正式名で、56ピンの JAMMA(JS)規格とは別物 — [usada.yabou.jp](https://usada.yabou.jp/game/acgame_jvs.html)、[wdic](https://www.wdic.org/w/MOE/JAMMA%E3%83%8F%E3%83%BC%E3%83%8D%E3%82%B9)

### Inferences
- 第1パスの「設計上は 5/E の −5V は未使用・無接続」の結論は変更不要。

### Gaps
- JAMMA(JS)規格原本による −5V・ピン名の公式確認は今回も 未確認(第3節の経路参照)。
