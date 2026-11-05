"""Does the $16-25 ranking survive restating Wine Enthusiast prices in 2026 dollars?
Prices are rescaled by a constant k (wine CPI or headline CPI); gaps are unchanged by construction
(a uniform rescale shifts ln(price) by a constant, which the quadratic-in-ln(price) model absorbs),
so only tier membership moves. Run from code/: python3 -I inflation_check.py"""
import sys, os, numpy as np, pandas as pd
import statsmodels.formula.api as smf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from style_map import style
from paths import RAW_WINE, OUT, need
d = pd.read_csv(need(RAW_WINE), index_col=0).drop_duplicates().dropna(subset=["price", "country"]).copy()
d["variety"] = d.variety.fillna("(unknown)"); d["lp"] = np.log(d.price); d["taster"] = d.taster_name.fillna("(none)")
d["designation"] = d.designation.fillna(""); d["style"] = [style(r) for r in d.itertuples()]
v = pd.to_numeric(d.title.str.extract(r"\b(19[5-9]\d|20[01]\d)\b")[0], errors="coerce")
d["vb"] = pd.cut(v, [1949, 2003, 2006, 2008, 2010, 2012, 2013, 2014, 2015, 2017]).astype(object).where(v.notna(), "NV").astype(str)
A = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d).fit(); d["gA"] = d.points - A.fittedvalues
B = smf.ols("points ~ lp + I(lp**2) + C(vb)", d).fit(); d["gB"] = d.points - B.fittedvalues
# check invariance: refit with rescaled price
d2 = d.copy(); d2["lp"] = np.log(d2.price * 1.35)
A2 = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d2).fit()
print("max |gap change| after x1.35 rescale:", float(np.abs((d2.points - A2.fittedvalues) - d.gA).max()))

def top10(k, sty, lo=15, hi=25):
    s = d[(d.price * k > lo) & (d.price * k <= hi) & (d["style"] == sty)]
    g = s.groupby(["country", "variety"]).agg(n=("gA", "size"), ma=("gA", "mean"), sa=("gA", "std"), mb=("gB", "mean"), sb=("gB", "std"))
    g = g[g.n >= 30]
    g["r"] = np.minimum(g.ma - 1.96 * g.sa / np.sqrt(g.n), g.mb - 1.96 * g.sb / np.sqrt(g.n))
    return g.sort_values("r", ascending=False)

SCEN = {"none (US$ as reviewed)": 1.0, "wine CPI 2017→2026 (+7.3%)": 1.073, "headline CPI 2017→2026 (+35%)": 1.35}
for sty in ["Red", "White"]:
    base = top10(1.0, sty); b10 = list(base.head(10).index)
    print(f"\n== {sty}, $16–25 tier. Base top 10:", [f"{c} {v}" for c, v in b10])
    for lab, k in SCEN.items():
        t = top10(k, sty); t10 = list(t.head(10).index)
        common = base.index.intersection(t.index)
        rc = base.loc[common, "r"].rank().corr(t.loc[common, "r"].rank())
        top3 = list(t.head(3).index)
        print(f"  {lab}: groups={len(t)}, overlap with base top10={len(set(b10) & set(t10))}/10, Spearman={rc:.2f}, top3={[f'{c} {v} ({t.loc[(c, v), 'r']:+.2f})' for c, v in top3]}")
        print("     base top3 ranks now:", [(f"{c} {v}", int(t.index.get_loc((c, v)) + 1) if (c, v) in t.index else "n<30") for c, v in b10[:3]])
# tier of Portuguese red and Australian Shiraz under each scenario: share of wines that stay in $16-25
for lab, k in SCEN.items():
    for c, vv in [("Portugal", "Portuguese Red"), ("Australia", "Shiraz"), ("France", "Melon")]:
        g = d[(d.country == c) & (d.variety == vv)]
        base_in = (g.price > 15) & (g.price <= 25); now_in = (g.price * k > 15) & (g.price * k <= 25)
        print(f"{lab:32s} {c} {vv}: in $16–25 base={int(base_in.sum())}, after={int(now_in.sum())}, stay={int((base_in & now_in).sum())}")
