"""Origin-associated price differences in the Wine Enthusiast data: ln(price) ~ points + grape + country, country relative to the US.
An observed conditional price gap, not a measure of consumer preference. Run from code/: python3 -I origin_premium.py -> data/reproduced/origin_premium_US_reviews.csv"""
import sys, pathlib, numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); from paths import RAW_WINE, OUT, need
d = pd.read_csv(need(RAW_WINE), index_col=0).drop_duplicates().dropna(subset=["price", "country"]).copy()
d["variety"] = d.variety.fillna("(unknown)"); d["lp"] = np.log(d.price)
top = d.variety.value_counts(); d["var2"] = np.where(d.variety.isin(top[top >= 100].index), d.variety, "(other)")
d["country"] = pd.Categorical(d.country, categories=["US"] + sorted(c for c in d.country.unique() if c != "US"))
m = smf.ols("lp ~ points + C(var2) + C(country)", d).fit(cov_type="HC1")
print("n =", int(m.nobs), "R2 =", round(m.rsquared, 3), "per point:", f"{(np.exp(m.params['points'])-1)*100:.1f}%")
rows = []
for c in ["Portugal", "Australia", "France", "Italy", "Spain", "Chile", "Argentina", "New Zealand", "Germany", "Austria", "South Africa"]:
    k = f"C(country)[T.{c}]"; b = m.params[k]; lo, hi = m.conf_int().loc[k]
    rows.append((c, int((d.country == c).sum()), (np.exp(b) - 1) * 100, (np.exp(lo) - 1) * 100, (np.exp(hi) - 1) * 100))
out = pd.DataFrame(rows, columns=["country", "n", "price_vs_US_pct", "lo95", "hi95"]).sort_values("price_vs_US_pct")
print(out.round(1).to_string(index=False)); out.round(1).to_csv(OUT / "origin_premium_US_reviews.csv", index=False)
