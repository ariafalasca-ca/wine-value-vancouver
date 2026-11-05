"""Metric prototypes on deduplicated wine reviews.
Run: python3 -I analysis.py <work_dir>
"""
import sys, json, re
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

w = sys.argv[1]
d = pd.read_parquet(f"{w}/wine_dedup.parquet")
d = d.dropna(subset=["price", "country"]).copy()
d["lp"] = np.log(d.price)
d["taster"] = d.taster_name.fillna("None")
top_var = d.variety.value_counts().index[:30]
top_cty = d.country.value_counts().index[:15]
d["var30"] = np.where(d.variety.isin(top_var), d.variety, "Other")
d["cty15"] = np.where(d.country.isin(top_cty), d.country, "Other")
out = {}

# 1) Economic value of a point: log(price) ~ points (+ controls)
m0 = smf.ols("lp ~ points", d).fit()
m1 = smf.ols("lp ~ points + C(taster) + C(var30) + C(cty15)", d).fit()
out["price_premium_per_point_raw_pct"] = round((np.exp(m0.params.points) - 1) * 100, 2)
out["price_premium_per_point_ctrl_pct"] = round((np.exp(m1.params.points) - 1) * 100, 2)
out["price_premium_ci_ctrl_pct"] = [round((np.exp(x) - 1) * 100, 2) for x in m1.conf_int().loc["points"]]
out["r2_raw"], out["r2_ctrl"] = round(m0.rsquared, 3), round(m1.rsquared, 3)

# 2) Threshold at 90: median price by point, and jump 89->90 vs neighbours
med = d.groupby("points").price.median()
out["median_price_by_points"] = med.to_dict()
lm = np.log(med)
steps = lm.diff()
out["log_step_89_90"] = round(float(steps.loc[90]), 3)
out["log_step_avg_86_93_excl90"] = round(float(steps.loc[[87, 88, 89, 91, 92, 93]].mean()), 3)

# 3) Taster leniency after controlling for wine traits & price
m2 = smf.ols("points ~ lp + C(taster) + C(var30) + C(cty15)", d[d.taster != "None"]).fit()
tfx = {k.replace("C(taster)[T.", "").rstrip("]"): round(v, 2) for k, v in m2.params.items() if k.startswith("C(taster)")}
out["taster_effects_vs_baseline"] = dict(sorted(tfx.items(), key=lambda x: x[1]))
base = sorted(d[d.taster != "None"].taster.unique())[0]
out["taster_baseline"] = base
out["taster_effect_range"] = round(max(list(tfx.values()) + [0]) - min(list(tfx.values()) + [0]), 2)

# 4) Value Gained = actual points - expected points given price (and taster)
mv = smf.ols("points ~ lp + I(lp**2) + C(taster)", d).fit()
d["exp_pts"] = mv.fittedvalues
d["value_gained"] = d.points - d.exp_pts
out["value_model_r2"] = round(mv.rsquared, 3)
bands = pd.cut(d.price, [0, 15, 25, 40, 75, 10000], labels=["<$15", "$15-25", "$25-40", "$40-75", "$75+"])
d["band"] = bands
g = (d.groupby(["band", "country", "variety"], observed=True)
       .agg(n=("value_gained", "size"), vg=("value_gained", "mean"), sd=("value_gained", "std"),
            pts=("points", "mean"), med_price=("price", "median")).reset_index())
g = g[g.n >= 50].copy()
g["se"] = g.sd / np.sqrt(g.n)
g["lo"] = g.vg - 1.96 * g.se
best = {}
for b in ["<$15", "$15-25", "$25-40", "$40-75"]:
    gb = g[g.band == b].sort_values("lo", ascending=False).head(5)
    best[b] = gb[["country", "variety", "n", "vg", "lo", "pts", "med_price"]].round(2).to_dict("records")
out["best_value_by_band_n50_rank_by_CI_lower"] = best
worst = g[g.band == "$15-25"].sort_values("vg").head(5)[["country", "variety", "n", "vg", "pts", "med_price"]].round(2)
out["worst_value_15_25"] = worst.to_dict("records")

# 5) Pareto frontier: max points achievable at or below price p
fr = d.groupby("price").points.max().sort_index().cummax()
out["frontier_samples"] = {int(p): int(fr[fr.index <= p].iloc[-1]) for p in [10, 15, 20, 25, 30, 40, 50, 75, 100, 200]}

# 6) Words: lift of word presence in >=90 vs <90 (note: descriptions are written AFTER scoring)
hi = d.points >= 90
tok = d.description.str.lower().str.findall(r"[a-z']+").apply(set)
from collections import Counter
ch, cl = Counter(), Counter()
for s, h in zip(tok, hi):
    (ch if h else cl).update(s)
nh, nl = hi.sum(), (~hi).sum()
rows = []
for wd in set(ch) | set(cl):
    a, b = ch[wd], cl[wd]
    if a + b < 800: continue
    rows.append((wd, a / nh, b / nl, (a / nh + 1e-9) / (b / nl + 1e-9)))
lift = pd.DataFrame(rows, columns=["word", "p_hi", "p_lo", "lift"]).sort_values("lift")
out["words_high_lift"] = lift.tail(15).round(3).to_dict("records")
out["words_low_lift"] = lift.head(15).round(3).to_dict("records")
out["share_90plus"] = round(float(hi.mean() * 100), 2)

# 7) holdout check for value model
rng = np.random.default_rng(7)
msk = rng.random(len(d)) < 0.8
mt = smf.ols("points ~ lp + I(lp**2) + C(taster)", d[msk]).fit()
pred = mt.predict(d[~msk])
out["holdout_r2"] = round(1 - ((d[~msk].points - pred) ** 2).sum() / ((d[~msk].points - d[~msk].points.mean()) ** 2).sum(), 3)

# robustness: value ranking without taster FE
mv2 = smf.ols("points ~ lp + I(lp**2)", d).fit()
d["vg_noFE"] = d.points - mv2.fittedvalues
g2 = d.groupby(["band", "country", "variety"], observed=True).agg(n=("vg_noFE", "size"), vg2=("vg_noFE", "mean")).reset_index()
mm = g.merge(g2, on=["band", "country", "variety", "n"])
out["rank_corr_with_vs_without_taster_FE"] = round(float(mm[["vg", "vg2"]].rank().corr().iloc[0, 1]), 3)

d[["country", "province", "variety", "winery", "title", "points", "price", "taster", "band", "exp_pts", "value_gained"]].to_csv(f"{w}/wine_value_gained.csv", index=False)
json.dump(out, open(f"{w}/analysis.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str, ensure_ascii=False))
