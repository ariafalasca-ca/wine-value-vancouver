"""Historical score signals among wines listed in BC (exploratory).
Links each matched BC product to the historical Wine Enthusiast residuals of the same wine and asks whether bottles in the recommended
categories carry the historical advantage. This is not an out-of-sample test: the residuals come from models fitted on all reviews,
these wines included, and US prices set the benchmark; BC prices are used only to group the bottles.
Bottle metric: the lower of the two mean residuals (models A and B), averaged over that wine's reviews (median 2 reviews per wine).
It is a different, weaker measure than the deck's cautious estimate (the lower of the two 95% low ends over groups of 30+ reviews).
Run from code/ after same_bottle.py: python3 -I validate_picks.py -> data/reproduced/validate_summary.json, bc_rerank.csv
"""
import sys, json, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from paths import BC_LIST, RAW_WINE, OUT, need

M = pd.read_csv(need(OUT / "same_bottle_matched.csv"))
M["low_mean_resid"] = np.minimum(M.gA, M.gB)
def summ(s, label):
    return {"label": label, "n": int(len(s)), "positive": int((s.low_mean_resid > 0).sum()), "mean": round(float(s.low_mean_resid.mean()), 2) if len(s) else None,
            "bc_median": float(s.bc_price.median()) if len(s) else None, "reviews_per_wine_median": float(s.n_reviews.median()) if len(s) else None,
            "bottles": s.sort_values("bc_price")[["bc_name", "bc_price", "we_variety", "low_mean_resid", "n_reviews", "match_source"]].round(2).to_dict("records")}
S = {}
pr = M[M.bc_class == "Portugal Red Wine"]
S["portuguese_red_all"] = summ(pr, "Portuguese red, all matched")
S["portuguese_red_le_15"] = summ(pr[pr.bc_price <= 15], "Portuguese red, CA$15 or less")
S["portuguese_red_15_40"] = summ(pr[(pr.bc_price > 15) & (pr.bc_price <= 40)], "Portuguese red, CA$15-40")
S["portuguese_red_le_25"] = summ(pr[pr.bc_price <= 25], "Portuguese red, CA$25 or less")
shz_any = M[(M.country == "Australia") & M.bc_name.str.contains("SHIRAZ")]
shz = shz_any[shz_any.we_variety == "Shiraz"]
S["shiraz_and_blends"] = summ(shz_any, "Australian Shiraz incl. Shiraz blends")
S["shiraz_single_variety"] = summ(shz, "Australian Shiraz, single variety")
S["shiraz_single_variety_le_25"] = summ(shz[shz.bc_price <= 25], "Australian Shiraz, single variety, CA$25 or less")
S["muscadet"] = summ(M[M.bc_name.str.contains("MUSCADET")], "Muscadet")
S["german_riesling"] = summ(M[(M.country == "Germany") & M.bc_name.str.contains("RIESLING")], "German Riesling")
rw = M[M.bc_class.str.contains("Red Wine|White Wine", na=False)]
S["all_red_white_le_25"] = summ(rw[rw.bc_price <= 25], "All matched red and white, CA$25 or less")
for k in list(S): S[k] = {kk: vv for kk, vv in S[k].items() if not (kk == "bottles" and k.startswith("all_"))}
# BC price bands
M["band"] = pd.cut(M.bc_price, [0, 21, 35, 70, 140, 1e9], labels=["CA$21 or less", "CA$22-35", "CA$36-70", "CA$71-140", "over CA$140"])
S["by_bc_band"] = M.groupby("band", observed=True).agg(n=("low_mean_resid", "size"), mean=("low_mean_resid", "mean"), share_positive=("low_mean_resid", lambda x: (x > 0).mean() * 100)).round(2).reset_index().astype({"band": str}).to_dict("records")
# grouping matched bottles by BC price (CA$ bands = deck's US$ tiers x 1.40). Groups need 3+ bottles; the deck's groups need 30+ reviews.
tiers = [("CA$21 or less", 0, 21), ("CA$22-35", 21, 35), ("CA$36-70", 35, 70), ("CA$71-140", 70, 140), ("over CA$140", 140, 1e9)]
rr = []
for lab, lo, hi in tiers:
    s = M[(M.bc_price > lo) & (M.bc_price <= hi)]
    g = s.groupby(["country", "we_variety"]).agg(n=("low_mean_resid", "size"), mean_low_resid=("low_mean_resid", "mean"), bc_med=("bc_price", "median")).reset_index()
    g = g[g.n >= 3].sort_values("mean_low_resid", ascending=False); g["band"] = lab; g["rank"] = range(1, len(g) + 1); rr.append(g)
RR = pd.concat(rr, ignore_index=True); RR.round(3).to_csv(OUT / "bc_rerank.csv", index=False)
S["grouped_CA22_35"] = RR[RR.band == "CA$22-35"].head(8).round(2).to_dict("records")
# category level: all BC listings vs all Wine Enthusiast reviews of the group (not the same bottles)
b = pd.read_csv(need(BC_LIST)); w = b[(b.ITEM_CATEGORY_NAME == "Wine") & (b.PRODUCT_LITRES_PER_CONTAINER == 0.75) & (b.PRD_CONTAINER_PER_SELL_UNIT == 1)]
raw = pd.read_csv(need(RAW_WINE), index_col=0).drop_duplicates().dropna(subset=["price", "country"])
bcs = w[w.ITEM_CLASS_NAME == "Portugal Red Wine"].PRODUCT_PRICE; wes = raw[(raw.country == "Portugal") & (raw.variety == "Portuguese Red")].price
S["portuguese_red_category_quantiles"] = {"bc_n": int(len(bcs)), "we_n": int(len(wes)), "q": [.25, .5, .75], "bc": [float(bcs.quantile(q)) for q in (.25, .5, .75)], "we_usd": [float(wes.quantile(q)) for q in (.25, .5, .75)],
                                          "bc_over_we_at_1_40": [round(float(bcs.quantile(q)) / float(wes.quantile(q)) / 1.40, 2) for q in (.25, .5, .75)]}
json.dump(S, open(OUT / "validate_summary.json", "w"), indent=1, default=float, allow_nan=False)
for k, v in S.items():
    if isinstance(v, dict) and "n" in v: print(f"{v['label']}: n={v['n']}, positive={v['positive']}, mean={v['mean']}, BC median={v['bc_median']}")
print(pd.DataFrame(S["grouped_CA22_35"]).to_string(index=False)); print(S["portuguese_red_category_quantiles"])
