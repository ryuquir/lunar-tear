#!/usr/bin/env python3
"""Build the set of files that goes to the Google Drive folder "異能ソフト/ファミコンアーキテクチャー基盤".

    python3 ordering/make_grok_package.py OUTPUT_DIR [--date YYYY-MM-DD]

OUTPUT_DIR must not exist yet.  Needs pandoc (HTML -> Markdown text).
Every text file except 03 carries the version line on line 2, so that Grok and the owner can tell
old copies from new ones.  03 is copied unchanged and has no version
line, because everything after its "Subject:" line is sent to JLCPCB as it is; 04 tells Grok how to
recognise it by its content.  Before it finishes, the script scans every file (and every member of the
zip files) for e-mail addresses and for the words in the environment variable
GROK_PACKAGE_FORBIDDEN (comma separated, for example a user name); it fails if it finds one.
"""
import datetime
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)                       # hardware/famicom-jamma
REPO = os.path.dirname(os.path.dirname(PROJECT))      # repository root
RESEARCH = [os.path.join(REPO, "reports"), os.path.join(REPO, "research_notes", "ファミコン JAMMA 基板 仕様調査")]

MANUFACTURING_NOTE = """このフォルダ（50_製造データ）について
{version}

ここには、段階 3（配線）が終わったときに、次のファイルが入ります。

- fcjamma_gerber_rev○.zip（Gerber と穴あけのデータ）
- fcjamma_bom_jlcpcb_rev○.csv（部品表）
- fcjamma_cpl_jlcpcb_rev○.csv（部品の位置の表）
- 製造データの確認記録_rev○.txt（設計者の検査結果。最後の行が「OK」）
- 配置確認用の図_rev○.png（向きのある部品の正しい向き）

いまは、まだ 1 つもありません。
ファイルがそろい、「01_【Grok用】発注代行の指示書」が「発注用」の版に差し替わるまで、基板の発注はしません。
"""

RECORDS_NOTE = """このフォルダ（60_注文の記録）について
{version}

Grok が作業の記録を置く場所です。
ファイル名の先頭に日付を付けてください（例: 2026-11-15_依頼1_JLCPCBの回答.txt）。

残すもの:
- 送った質問と、回答の全文
- 注文番号、金額とその内訳、配送方法、追跡番号
- 画面の写し（見積もり、配置の確認画面など）
- JLCPCB の製造ファイル（zip）
- 止まって依頼者に確認した点と、その結果
"""

OLD_FOLDER_NOTE = """このフォルダ（ファミコン基板1）は使いません
{version}

最新のデータと文書は、同じ「異能ソフト」の中の「ファミコンアーキテクチャー基盤」フォルダに移しました。
Grok には、そのフォルダの「01_【Grok用】発注代行の指示書（最初に読ませる）.txt」を最初に読ませてください。
このフォルダにある文書は古い版です。読んだり、従ったりしないでください。
"""


def design_rev():
    sys.path.insert(0, os.path.join(PROJECT, "tools"))
    sys.path.insert(0, os.path.join(PROJECT, "design"))
    import circuit                      # noqa: E402
    design, _flags = circuit.build()
    return design.rev


def html_to_text(path):
    r = subprocess.run(["pandoc", "-f", "html", "-t", "gfm", "--wrap=none", path], capture_output=True, text=True, check=True)
    # pandoc escapes ASCII punctuation for Markdown ("\\[依頼者の名前\\]", "zz\\_旧版", "Part \\#", "1\\. U25").
    # Grok reads the text as plain text and copies some of it into JLCPCB's forms, so drop those
    # backslashes.  The HTML sources hold no backslash of their own; "\\|" is kept, as it would split a
    # table cell.
    return re.sub(r"\\([!-/:-@\[-`{}~])", r"\1", r.stdout)


def with_header(title, version, body):
    return f"{title}\n{version}\n\n{body.lstrip()}"


def zip_dir(target, sources, root):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for src in sources:
            for base, dirs, files in os.walk(src):
                dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".git"))
                for f in sorted(files):
                    if f.endswith((".pyc", ".kicad_prl", ".lck")):
                        continue
                    p = os.path.join(base, f)
                    z.write(p, os.path.relpath(p, root))


def scan(outdir, forbidden):
    email = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(com|net|org|jp|io|dev)\b")
    allowed = {b"support@jlcpcb.com", b"noreply@anthropic.com"}
    bad = []

    def check(name, data):
        for m in email.finditer(data):
            if m.group(0) in allowed or data[max(0, m.start() - 6):m.start()] == b"/list/":
                continue            # a public mailing list's name inside an archive link is not a personal address
            bad.append(f"{name}: e-mail address {m.group(0).decode(errors='replace')}")
        for w in forbidden:
            if w and w.encode() in data.lower():
                bad.append(f"{name}: contains a forbidden word")

    for base, _dirs, files in os.walk(outdir):
        for f in files:
            p = os.path.join(base, f)
            rel = os.path.relpath(p, outdir)
            if f.endswith(".zip"):
                with zipfile.ZipFile(p) as z:
                    for member in z.namelist():
                        check(f"{rel}/{member}", z.read(member))
            else:
                check(rel, open(p, "rb").read())
    return bad


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = os.path.abspath(sys.argv[1])
    date = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else datetime.date.today().isoformat()
    if os.path.exists(out):
        sys.exit(f"{out} exists already; give a new directory")
    for left in ("failed", "unchecked"):     # out/ then shows a build that did not pass every check (tools/build.py)
        if os.path.exists(os.path.join(PROJECT, "out", left)):
            sys.exit(f"out/{left}/ exists: the last build did not pass every check, so out/ does not match kicad/. "
                     "Run tools/build.py until it prints OK, then make the package.")
    rev = design_rev()
    version_text = f"版: rev {rev} / {date}"
    os.makedirs(out)

    def write(name, text):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(text)

    memo = open(os.path.join(HERE, "owner_memo.txt"), encoding="utf-8").read()
    write("00_【持ち主用】はじめに読む（Grokへの渡し方）.txt",
          memo.replace("{VERSION_LINE}", version_text).replace("{VERSION_TEXT}", version_text))
    write("01_【Grok用】発注代行の指示書（最初に読ませる）.txt",
          with_header("ファミコンアーキテクチャー基盤　発注代行の指示書（最初に読む）", version_text, html_to_text(os.path.join(HERE, "grok_instruction.html"))))
    write("02_【Grok用】発注のノウハウとバグチェック.txt",
          with_header("ファミコンアーキテクチャー基盤　発注のノウハウとバグチェック", version_text, html_to_text(os.path.join(HERE, "grok_ordering_knowhow.html"))))
    shutil.copy(os.path.join(HERE, "jlcpcb_support_question.txt"), os.path.join(out, "03_【Grok用】JLCPCBへの質問文（英語）.txt"))
    write("04_【Grok用】JLCPCBへの質問の手引き（何を・なぜ・どう聞くか）.txt",
          with_header("ファミコンアーキテクチャー基盤　JLCPCB への事前質問の手引き（依頼 1）", version_text,
                      html_to_text(os.path.join(HERE, "jlcpcb_question_guide.html"))))
    shutil.copy(os.path.join(PROJECT, "mech", "board_outline_plan.png"), os.path.join(out, "10_【図】基板の外形と配置の案.png"))
    shutil.copy(os.path.join(PROJECT, "out", "board", "fcjamma_board_top.png"),
                os.path.join(out, "11_【図】基板の外形（捨て基板つき・上から見た図）.png"))
    write("30_【参考】famicart rev H のまとめ（mk2 の検討用）.txt",
          with_header("ファミコンアーキテクチャー基盤　famicart rev H のまとめと mk2 の論点", version_text,
                      open(os.path.join(RESEARCH[1], "famicart_revh_for_mk2.md"), encoding="utf-8").read()))
    write("20_【参考】設計記録（README）.txt",
          with_header("ファミコンアーキテクチャー基盤　設計記録（README。設計データの説明）", version_text,
                      open(os.path.join(PROJECT, "README.md"), encoding="utf-8").read()))
    shutil.copy(os.path.join(PROJECT, "out", "fcjamma_schematic.pdf"), os.path.join(out, "21_【参考】回路図.pdf"))
    shutil.copy(os.path.join(PROJECT, "out", "bom_by_source.csv"), os.path.join(out, "22_【参考】部品表.csv"))
    shutil.copy(os.path.join(PROJECT, "out", "cost_estimate.csv"), os.path.join(out, "23_【参考】費用の内訳.csv"))
    zip_dir(os.path.join(out, "90_【保管用】設計データ一式.zip"), [PROJECT], os.path.dirname(PROJECT))
    zip_dir(os.path.join(out, "91_【保管用】調査資料と要求の記録.zip"), RESEARCH, REPO)
    for folder, note, text in (("50_製造データ（段階3で入る）", "まだ空です.txt", MANUFACTURING_NOTE),
                               ("60_注文の記録（Grokが記録を置く）", "このフォルダについて.txt", RECORDS_NOTE)):
        os.makedirs(os.path.join(out, folder))
        write(os.path.join(folder, note), text.format(version=version_text))
    old = os.path.join(out, "_for_the_old_folder")
    os.makedirs(old)
    write(os.path.join("_for_the_old_folder", "00_このフォルダは使いません.txt"), OLD_FOLDER_NOTE.format(version=version_text))

    forbidden = [w.strip().lower() for w in os.environ.get("GROK_PACKAGE_FORBIDDEN", "").split(",") if w.strip()]
    bad = scan(out, forbidden)
    if bad:
        print("PROBLEMS:")
        for b in bad:
            print("  -", b)
        sys.exit(1)
    for base, _dirs, files in sorted(os.walk(out)):
        for f in sorted(files):
            p = os.path.join(base, f)
            print(f"{os.path.getsize(p):>9}  {os.path.relpath(p, out)}")
    print(f"OK: {version_text}; no e-mail address or forbidden word found")


if __name__ == "__main__":
    main()
