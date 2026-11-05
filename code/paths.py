"""Project-relative paths for every Part C script. Override any input with an environment variable of the same name.
Layout (relative to the submission root):
  data/raw/winemag-data-130k-v2.csv        Kaggle "Wine Reviews" (zynicide); not shipped, download from the link in README.md
  data/raw/iowa_liquor_sales_*.csv         Iowa Liquor Sales 2026 extract (optional; data/iowa_750_items.csv is shipped)
  data/bc_liquor_store_product_price_list_june_2026.csv   shipped
  data/bcldb_lmr_pre_vs_post_march_2025.csv               shipped (built by parse_lmr.py from the LMR PDFs)
Outputs of run_all.py go to data/reproduced/."""
import os, pathlib
CODE = pathlib.Path(__file__).resolve().parent
ROOT = CODE.parent
DATA = ROOT / "data"
def _p(name, default):
    return pathlib.Path(os.environ.get(name, str(default)))
RAW_WINE = _p("RAW_WINE", DATA / "raw" / "winemag-data-130k-v2.csv")
BC_LIST = _p("BC_LIST", DATA / "bc_liquor_store_product_price_list_june_2026.csv")
LMR_PREPOST = _p("LMR_PREPOST", DATA / "bcldb_lmr_pre_vs_post_march_2025.csv")
IOWA_RAW_GLOB = os.environ.get("IOWA_RAW_GLOB", str(DATA / "raw" / "iowa_liquor_sales_*.csv"))
IOWA_ITEMS = _p("IOWA_ITEMS", DATA / "iowa_750_items.csv")
MANUAL_PT = CODE / "manual_portugal.csv"
FONTS = CODE / "fonts"
OUT = _p("OUT", DATA / "reproduced")
OUT.mkdir(parents=True, exist_ok=True)
FIG = OUT / "fig"
FIG.mkdir(parents=True, exist_ok=True)

def need(path):
    """Stop with a clear message if an input file is missing."""
    path = pathlib.Path(path)
    if not path.exists():
        raise SystemExit(f"Missing input: {path}\nSee README.md, section Data, for where to get it.")
    return path
