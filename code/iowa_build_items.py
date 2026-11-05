"""Build data/iowa_750_items.csv from the raw Iowa Liquor Sales extract (optional step; the result is shipped).
Input: data/raw/iowa_liquor_sales_*.csv (the 2026 extract, about 1.8 million rows, from https://data.iowa.gov/catalog/dataset/1263).
Also prints the category list, which shows the dataset holds spirits only. Run from code/: python3 -I iowa_build_items.py"""
import sys, glob, pathlib, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); from paths import IOWA_RAW_GLOB, IOWA_ITEMS
fs = sorted(glob.glob(IOWA_RAW_GLOB))
if not fs:
    print("Iowa raw files not found; using the shipped", IOWA_ITEMS); sys.exit(0)
cols = ["category_name", "item_no", "im_desc", "bottle_volume_ml", "state_bottle_retail", "sales_bottles"]
d = pd.concat([pd.read_csv(f, usecols=cols) for f in fs], ignore_index=True)
print("rows", len(d), "categories", d.category_name.nunique()); print(sorted(d.category_name.dropna().unique()))
d = d[d.bottle_volume_ml == 750]
g = d.groupby(["item_no", "im_desc", "category_name"]).agg(bottles=("sales_bottles", "sum"), retail_med=("state_bottle_retail", "median"), retail_last=("state_bottle_retail", "last"), n=("sales_bottles", "size")).reset_index().sort_values("bottles", ascending=False)
g.to_csv(IOWA_ITEMS, index=False); print("wrote", IOWA_ITEMS, len(g))
