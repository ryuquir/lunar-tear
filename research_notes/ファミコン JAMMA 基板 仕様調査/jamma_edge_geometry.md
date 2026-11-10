# JAMMA 56ピン エッジコネクタの機械寸法と製造仕様(第2パス・作業中)

(調査日 2026-11-10。作業中の途中保存。)

## 暫定ファインディング
- Hirose CR7 シリーズ カタログ(3.96mm/4mm card edge)「PCB Dimensions 3.96 pitch」: フィンガ幅 2.3±0.1、ピッチ 3.96±0.05、端部面取り C0.5(両面)、基板厚 1.6±0.15、キー溝 2.5 +0.1/0(コンタクト位置に置く広い溝)と 1 +0.1/0(コンタクト間に置く狭い溝)、溝深さ 11 +0.5/0 と 10、56極: A(両端フィンガ中心間)=106.98±0.08(27×3.96=106.92 と不一致)、B(タング幅)=114.8 0/−0.2。定格 3A/600V AC、接触抵抗 15mΩ。 — https://s1.dtsheet.com/store/data/002648525.pdf (dtsheet.com/model/1263367 経由)
- DE10Jamma JAMMA-56.kicad_mod: パッド 2.35×8 mm、ピッチ 3.96、端から 1.05 mm、キー溝 幅3.0×深さ10、タング幅 114.6 — https://github.com/MisterJamma/DE10Jamma
- jzdziarski Universal JAMMA Edge: パッド 2.2×10、端から 1.13、溝 幅2.5×深さ11.5、基板幅 111 — https://github.com/jzdziarski/jamma
- ORB orb03.pcb (gEDA): パッド 2.032×9.652、端から約0.1、溝 3.81×10.92、タング 113.03 — https://github.com/ole00/orb
