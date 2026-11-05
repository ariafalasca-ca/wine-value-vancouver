"""How much do doubtful matches matter? Compares three versions of the same-bottle set:
  all       every match the rules and the hand matches produced (data/reproduced/same_bottle_matched_all.csv)
  primary   all minus the pairs judged different or uncertain (code/match_exclusions.csv); this is what the report uses
  strict    primary minus every BC "Organic" line matched to a review title without "Organic" (a separate range may be involved)
Run from code/ after same_bottle.py: python3 -I match_sensitivity.py -> data/reproduced/match_sensitivity.json"""
import sys, json, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from paths import OUT, need

def load(name):
    m = pd.read_csv(need(OUT / name)); m["lm"] = np.minimum(m.gA, m.gB); return m
A = load("same_bottle_matched_all.csv"); P = load("same_bottle_matched.csv")
f_org = P.bc_name.str.contains("ORGANIC") & ~P.we_title.str.contains("Organic", case=False)
S = P[~f_org]

def headline(df):
    shz = df[(df.country == "Australia") & df.bc_name.str.contains("SHIRAZ") & (df.we_variety == "Shiraz")]
    pr = df[df.bc_class == "Portugal Red Wine"]; gr = df[(df.country == "Germany") & df.bc_name.str.contains("RIESLING")]
    by = df.groupby("country").ratio.agg(["size", "median"]).round(2)
    return {"n": int(len(df)), "overall_median_ratio": round(float(df.ratio.median()), 2),
            "median_ratio_by_origin_8plus": {c: float(r["median"]) for c, r in by[by["size"] >= 8].iterrows()},
            "shiraz_single_variety": [int(len(shz)), int((shz.lm > 0).sum())], "shiraz_le_25": [int((shz.bc_price <= 25).sum()), int(((shz.bc_price <= 25) & (shz.lm > 0)).sum())],
            "portuguese_red": [int(len(pr)), int((pr.lm > 0).sum())], "german_riesling": [int(len(gr)), int((gr.lm > 0).sum())]}

H = {"all": headline(A), "primary": headline(P), "strict": headline(S)}
o = lambda k: H[k]["median_ratio_by_origin_8plus"]
shift = max(abs(o(k)[c] - o("primary")[c]) for k in ("all", "strict") for c in o("primary") if c in o(k))
R = {"excluded_from_primary": int(len(A) - len(P)), "organic_lines_dropped_in_strict": int(f_org.sum()), "max_origin_median_shift_vs_primary": round(shift, 2),
     "organic_pairs": P[f_org][["country", "bc_name", "we_title"]].to_dict("records"), **H}
json.dump(R, open(OUT / "match_sensitivity.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in R.items() if k != "organic_pairs"}, indent=1, ensure_ascii=False))
