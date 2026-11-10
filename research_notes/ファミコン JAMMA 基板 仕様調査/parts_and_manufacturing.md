# ファミコン JAMMA 基板: 部品調達・製造制約の調査ノート (作業中・随時更新)

データ日付: 2026-11-10 取得。CDFER/jlcpcb-parts-database (yaqwsx/jlcparts 由来, 2026-11-10 05:55 GMT 更新) の CSV/SQLite をローカルで照会。DB 内最新 fetched_at は 2026-10-28 (在庫・価格は数日~2週間古い可能性)。

## 1. JLCPCB クラス (Basic / Preferred / Extended) の実データ

### Takeaway
2026-11-10 時点の公開 DB では Basic は 352 品目のみ (抵抗185, コンデンサ90, 他77)。Basic に含まれるロジック IC は 74HC14 (C5605) と 74HC595 (C5947) の 2 種だけ。スルーホール(THT) の Basic 部品は存在しない。

### Cited Findings
- Basic=352件 (library_type=base)、Preferred Extended=1226件 (expand かつ preferred=1) — [CDFER CSV](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv) をローカル集計 (2026-11-10 取得)
- DB 全体 511,178 品目 (在庫5個以上) — [CDFER SQLite](https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components.sqlite3) (Last-Modified 2026-11-10 05:55 GMT)
- Basic の THT 品目は 0 (CSV の assembly_process=THT 表示は GBJ ブリッジ等 Preferred のみで、SMD ダイオードにも誤付与があり信頼できない)

(以降、各セクションを追記予定)
