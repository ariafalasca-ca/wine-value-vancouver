"""Parse BCLDB Liquor Market Review PDFs (wine section) into a quarterly panel.
Usage: python3 -I parse_lmr.py <pdf_dir> <out_csv>
Each report lists 5 quarters; later reports override earlier ones for the same quarter (restatements)."""
import re, sys, subprocess, csv, glob, os

pdf_dir, out = sys.argv[1], sys.argv[2]
rows = {}  # (quarter, country, type, measure) -> value
QRE = re.compile(r"Fiscal (\d{4}/\d{2}) Q(\d)")
NUM = re.compile(r"\(?\$?-?[\d,]+\)?")

def parse_num(s):
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    v = float(re.sub(r"[^\d.]", "", s) or 0)
    return -v if neg else v

for pdf in sorted(glob.glob(os.path.join(pdf_dir, "*.pdf"))):
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    lines = txt.split("\n")
    measure = None; quarters = None; in_wine = False; country = None
    for ln in lines:
        if re.search(r"Wine Sales \(Net \$\)", ln): in_wine = True; measure = "net_sales"; continue
        if re.search(r"Wine Sales \(Litres\)", ln): in_wine = True; measure = "litres"; continue
        if re.search(r"(Beer|Spirits|Refreshment Beverages) Sales", ln): in_wine = False; continue
        if not in_wine: continue
        qs = QRE.findall(ln)
        if len(qs) == 5:
            quarters = [f"F{a} Q{b}" for a, b in qs]; continue
        if quarters is None: continue
        # data line: optional country group, a type label, then 5 numbers
        nums = re.findall(r"\(?\$?[\d,]+\)?", ln)
        nums = [n for n in nums if re.search(r"\d", n)]
        if len(nums) < 5: continue
        label_part = ln[: ln.find(nums[-5])].rstrip()
        # label part may contain "<Country> Wine   <Type>" or just "<Type>" or "Summary"
        indent = len(label_part) - len(label_part.lstrip())
        parts = re.split(r"\s{2,}", label_part.strip())
        if len(parts) >= 2: grp, typ = parts[0], parts[-1]
        else: grp, typ = None, parts[0]
        if grp: country = re.sub(r"\s*Wine$", "", grp).strip()
        if typ == "Summary" and indent < 22:
            for q, n in zip(quarters, nums[-5:]): rows[(q, "ALL", "ALL", measure)] = parse_num(n)
            continue
        if typ in ("Summary", "Report Quarters") or typ.startswith("Net Sales") or typ.startswith("Litres"):
            if typ == "Summary" and country:
                for q, n in zip(quarters, nums[-5:]): rows[(q, country, "ALL", measure)] = parse_num(n)
            continue
        if country is None: continue
        for q, n in zip(quarters, nums[-5:]):
            rows[(q, country, typ, measure)] = parse_num(n)

with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["quarter", "country", "type", "net_sales", "litres"])
    keys = sorted({(q, c, t) for (q, c, t, m) in rows})
    for q, c, t in keys:
        w.writerow([q, c, t, rows.get((q, c, t, "net_sales"), ""), rows.get((q, c, t, "litres"), "")])
print(len(keys), "rows")
