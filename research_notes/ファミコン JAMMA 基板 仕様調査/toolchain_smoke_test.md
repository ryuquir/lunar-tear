# ツールチェーン実地スモークテスト (Ubuntu 24.04 / root / 4CPU / コンテナ) — 2026-11-10

作業ディレクトリ: /tmp/toolchain_test/ 。本ノートは逐次更新中(途中保存)。

## Step 1: KiCad 10 (PPA)
- `add-apt-repository -y ppa:kicad/kicad-10.0-releases` → **失敗**: `ModuleNotFoundError: No module named 'apt_pkg'` (原因: /usr/bin/python3 が alternatives で python3.13 を指し、apt_pkg は python3.12 用のみ)
- 回避: `python3.12 /usr/bin/add-apt-repository -y ppa:kicad/kicad-10.0-releases` → 成功 (5.6秒、鍵はLaunchpad経由でsourcesファイルに埋め込み)
- `apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints` → 成功 20秒、DL 151MB、追加ディスク 947MB(apt表示)/実測 約840MB。78新規+1更新パッケージ
- kicad-cli version → 10.0.8 (`KICAD_IPC_API=ON`, ngspice 42, OCC 7.6.3)
