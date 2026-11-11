#!/usr/bin/env python3
"""Fetch today's JLCPCB data for the Extended parts this board uses.

    python3 tools/jlc_parts.py            # refresh data/jlcpcb_extended_parts.csv
    python3 tools/jlc_parts.py C2332 ...  # only look, print to the screen

For every part number it records what decides whether JLCPCB can assemble the part:
library class, stock in JLCPCB's assembly library, price, and the "Assembly Type",
"PCBA Type" and "X-ray Inspection" lines of the part's page (for example "Wave Soldering",
"Economic and Standard", "Required").  JLCPCB charges an inspection fee for every piece of a part
whose page says that X-ray inspection is required.
Run it again right before an order: stock and prices change daily.

Sources: JLCPCB's parts-library search (the JSON the web page itself uses) and the part
detail page https://jlcpcb.com/partdetail/<C-number>.
"""
import csv
import datetime
import html.parser
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
OUT = os.path.join(ROOT, "data", "jlcpcb_extended_parts.csv")
FIELDS = ["lcsc", "class", "mpn", "brand", "package", "description", "stock", "price_1", "price_10", "price_100",
          "assembly_type", "pcba_type", "xray", "checked"]


class _Text(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip = max(0, self.skip - 1)
        self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def curl(args):
    return subprocess.run(["curl", "-sS", "-L", "-m", "90", "-A", UA] + args, capture_output=True, text=True).stdout


def price(row, qty):
    tiers = sorted(row.get("componentPrices") or [], key=lambda p: p["startNumber"])
    best = tiers[0]["productPrice"] if tiers else ""
    for p in tiers:
        if p["startNumber"] <= qty:
            best = p["productPrice"]
    return best


def api_row(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 25})
    try:
        data = json.loads(curl(["-X", "POST", API, "-H", "Content-Type: application/json", "-d", body]))
        for row in data["data"]["componentPageInfo"]["list"] or []:
            if row["componentCode"] == code:
                return row
    except (ValueError, KeyError, TypeError):
        pass
    return None


def page_labels(code):
    parser = _Text()
    parser.feed(curl(["https://jlcpcb.com/partdetail/" + code]))
    lines = [re.sub(r"\s+", " ", x).strip() for x in "".join(parser.out).split("\n")]
    lines = [x for x in lines if x]
    found = {}
    for label in ("Assembly Type", "PCBA Type", "X-ray Inspection"):
        for i, line in enumerate(lines[:-1]):
            if line == label:
                found[label] = lines[i + 1]
                break
    return found.get("Assembly Type", ""), found.get("PCBA Type", ""), found.get("X-ray Inspection", "")


def lookup(code):
    row = api_row(code)
    if row is None:
        return None
    if row.get("componentLibraryType") == "base":
        cls = "Basic"
    elif row.get("preferredComponentFlag"):
        cls = "Preferred Extended"
    else:
        cls = "Extended"
    assembly, pcba, xray = page_labels(code)
    return {"lcsc": code, "class": cls, "mpn": row.get("componentModelEn") or "", "brand": row.get("componentBrandEn") or "",
            "package": row.get("componentSpecificationEn") or "", "description": row.get("describe") or "",
            "stock": row.get("stockCount") or 0, "price_1": price(row, 1), "price_10": price(row, 10), "price_100": price(row, 100),
            "assembly_type": assembly, "pcba_type": pcba, "xray": xray,
            "checked": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")}


def codes_of_design():
    sys.path.insert(0, HERE)
    sys.path.insert(0, os.path.join(ROOT, "design"))
    import circuit
    from fcgen.model import JLCX
    design, _flags = circuit.build()
    return sorted({p.code for p in design.parts.values() if p.src == JLCX} | {e[1] for e in design.extras if e[0] == JLCX},
                  key=lambda c: int(c[1:]))


def main():
    only_look = len(sys.argv) > 1
    codes = sys.argv[1:] if only_look else codes_of_design()
    rows = []
    for code in codes:
        row = lookup(code)
        if row is None:
            print(f"{code}: not found in JLCPCB's parts library")
            continue
        rows.append(row)
        print(f"{code:11s} {row['class']:18s} stock {row['stock']:>7}  ${row['price_1']}  {row['assembly_type']:15s} {row['pcba_type']:22s} {('X-ray ' + row['xray']) if row['xray'] else '':15s} {row['mpn']}")
        time.sleep(0.5)
    if not only_look:
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} parts to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
