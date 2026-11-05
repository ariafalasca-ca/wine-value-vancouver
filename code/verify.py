"""Re-verify claims in messages 1-4 and export chart data.
Run: python3 -I verify.py <dedup_parquet> <out_json>
"""
import sys, json
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

d0 = pd.read_parquet(sys.argv[1])
out = {}
out["rows_dedup"] = len(d0)
out["rows_price"] = int(d0.price.notna().sum())
d = d0.dropna(subset=["price", "country"]).copy()
out["rows_price_country"] = len(d)
d["lp"] = np.log(d.price)
d["taster"] = d.taster_name.fillna("None")
d["variety"] = d.variety.fillna("(unknown)")
mv = smf.ols("points ~ lp + I(lp**2) + C(taster)", d).fit()
d["exp"] = mv.fittedvalues
d["vg"] = d.points - d.exp
d["hi"] = (d.points >= 90).astype(float)

g = d.groupby(["country", "variety"]).agg(n=("points", "size"), med=("price", "median"), share90=("hi", "mean"),
                                           vg=("vg", "mean"), sd=("vg", "std"), pts=("points", "mean"), exp=("exp", "mean")).reset_index()
e = g[(g.n >= 30) & (g.med <= 25)].copy()
e["lo"] = e.vg - 1.96 * e.sd / np.sqrt(e.n)
e["s90_half"] = 1.96 * np.sqrt(e.share90 * (1 - e.share90) / e.n)
out["eligible"] = len(e)
out["pearson_share90_med"] = round(float(e[["share90", "med"]].corr().iloc[0, 1]), 3)
out["spearman_share90_med"] = round(float(e[["share90", "med"]].corr("spearman").iloc[0, 1]), 3)
team = e.sort_values(["share90", "n"], ascending=[False, False]).reset_index(drop=True)
team["rank"] = team.index + 1
vgr = e.sort_values("lo", ascending=False).reset_index(drop=True)
vgr["rank"] = vgr.index + 1
t10, v10 = team.head(10), vgr.head(10)
out["team_top10_median_of_medians"] = float(t10.med.median())
out["all_eligible_median_of_medians"] = float(e.med.median())
out["share_of_team_top10_with_med_ge_22_5"] = int((t10.med >= 22.5).sum())
out["overlap"] = sorted(set(zip(t10.country, t10.variety)) & set(zip(v10.country, v10.variety)))
# rank of austrian chardonnay
ac = team[(team.country == "Austria") & (team.variety == "Chardonnay")].iloc[0]
out["austria_chard"] = {k: (float(ac[k]) if k not in ("country", "variety") else ac[k]) for k in ["country", "variety", "n", "med", "share90", "vg", "pts", "exp", "rank"]}
# CI half width at n=30 for typical share
out["ci_half_n30_p40"] = round(1.96 * np.sqrt(0.4 * 0.6 / 30) * 100, 1)
out["ci_half_n30_p50"] = round(1.96 * np.sqrt(0.5 * 0.5 / 30) * 100, 1)
out["max_s90_half_in_team_top10"] = round(float(t10.s90_half.max() * 100), 1)
out["median_s90_half_eligible"] = round(float(e.s90_half.median() * 100), 1)
# n of eligible segments with n < 50
out["eligible_n_lt_50"] = int((e.n < 50).sum())

# price steps by score
med = d.groupby("points").price.median()
steps = {int(k): round(float(np.exp(np.log(med.loc[k] / med.loc[k - 1])) - 1) * 100, 1) for k in med.index[1:]}
out["median_price_by_points"] = {int(k): float(v) for k, v in med.items()}
out["steps_pct"] = steps
nb = [87, 88, 89, 91, 92, 93]
out["neighbour_steps"] = {k: steps[k] for k in nb}
out["neighbour_logavg_pct"] = round((np.exp(np.mean([np.log(med.loc[k] / med.loc[k - 1]) for k in nb])) - 1) * 100, 1)
out["step90"] = steps[90]
# premium per point
d["var30"] = np.where(d.variety.isin(d.variety.value_counts().index[:30]), d.variety, "Other")
d["cty15"] = np.where(d.country.isin(d.country.value_counts().index[:15]), d.country, "Other")
m1 = smf.ols("lp ~ points + C(taster) + C(var30) + C(cty15)", d).fit()
out["premium_ctrl_pct"] = round((np.exp(m1.params.points) - 1) * 100, 2)
m0 = smf.ols("lp ~ points", d).fit()
out["premium_raw_pct"] = round((np.exp(m0.params.points) - 1) * 100, 2)
out["value_model_r2"] = round(mv.rsquared, 3)

cols = ["country", "variety", "n", "med", "share90", "vg", "lo", "pts", "exp"]
out["team_top10"] = t10[cols + ["rank"]].round(4).to_dict("records")
out["vg_top10"] = v10[cols + ["rank"]].round(4).to_dict("records")
out["eligible_points"] = e[cols].round(4).to_dict("records")
# where do VG top10 rank under team rule
tr = {(r.country, r.variety): int(r["rank"]) for _, r in team.iterrows()}
out["vg_top10_team_rank"] = [tr[(r.country, r.variety)] for _, r in v10.iterrows()]
vr = {(r.country, r.variety): int(r["rank"]) for _, r in vgr.iterrows()}
out["team_top10_vg_rank"] = [vr[(r.country, r.variety)] for _, r in t10.iterrows()]
json.dump(out, open(sys.argv[2], "w"), indent=1, default=str)
skip = {"eligible_points", "median_price_by_points"}
print(json.dumps({k: v for k, v in out.items() if k not in skip}, indent=1, default=str))
