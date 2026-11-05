"""Data for the 'Can You Taste the Price?' story page.
Run: python3 -I data.py <dedup_parquet> <bcldb_csv> <verify_json> <checks_json> <out_json>
"""
import sys, os, json, numpy as np, pandas as pd
import statsmodels.formula.api as smf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style_map import style  # shelf section per wine: Sparkling > Fortified & dessert > Rosé > Red/White
src, bc_path, ver_path, chk_path, out_path = sys.argv[1:6]
d0 = pd.read_parquet(src)
d = d0.dropna(subset=["price", "country"]).copy()
d["variety"] = d.variety.fillna("(unknown)")
d["lp"] = np.log(d.price); d["taster"] = d.taster_name.fillna("(none)")
d["designation"] = d.designation.fillna("")
d["style"] = [style(r) for r in d.itertuples()]
STYLES = ["Red", "White", "Rosé", "Sparkling", "Fortified & dessert"]
v = pd.to_numeric(d.title.str.extract(r"\b(19[5-9]\d|20[01]\d)\b")[0], errors="coerce")
d["vb"] = pd.cut(v, [1949, 2003, 2006, 2008, 2010, 2012, 2013, 2014, 2015, 2017]).astype(object).where(v.notna(), "NV").astype(str)
out = {}
# --- headline numbers
out["n_raw"] = 129971; out["n_dup"] = 9983; out["n_unique"] = len(d0); out["n_used"] = len(d)
out["n_critics"] = int(d0.taster_name.nunique())
# --- 1. median price by score
med = d.groupby("points").price.median()
out["median_by_points"] = [{"points": int(k), "price": float(v), "n": int((d.points == k).sum())} for k, v in med.items()]
out["premium_ctrl"] = 12.8
# --- 2. heatmap of ln(price) x points, and the simple expected curve
edges = np.linspace(np.log(4), np.log(500), 37)
d["pbin"] = np.clip(np.digitize(d.lp, edges) - 1, 0, len(edges) - 2)
hm = d.groupby(["pbin", "points"]).size()
out["heat"] = {"edges": [round(float(np.exp(e)), 2) for e in edges],
               "cells": [[int(b), int(p), int(c)] for (b, p), c in hm.items()]}
simple = smf.ols("points ~ lp + I(lp**2)", d).fit()
out["curve"] = {"b0": simple.params.Intercept, "b1": simple.params.lp, "b2": simple.params["I(lp ** 2)"]}
out["example"] = {"price": 20, "points": 90, "expected": round(float(simple.params.Intercept + simple.params.lp * np.log(20) + simple.params["I(lp ** 2)"] * np.log(20) ** 2), 2)}
# --- 3. two models
A = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d).fit(); d["gA"] = d.points - A.fittedvalues
B = smf.ols("points ~ lp + I(lp**2) + C(vb)", d).fit(); d["gB"] = d.points - B.fittedvalues
out["r2"] = {"A": round(A.rsquared, 3), "B": round(B.rsquared, 3)}
cv = d.groupby("country").agg(n=("gA", "size"), A=("gA", "mean"), B=("gB", "mean"))
out["country_ab"] = {c: {"n": int(r.n), "A": round(r.A, 2), "B": round(r.B, 2)} for c, r in cv.iterrows() if c in ["Austria", "Spain", "Chile", "Argentina", "Portugal", "France", "Italy", "US", "Germany", "Australia"]}
print("country_ab", out["country_ab"])
# --- 4. shelf guide: each shelf section (style) ranked on its own, by tier (deck tiers, upper bound inclusive)
sc = d["style"].value_counts()
out["styles"] = {"order": STYLES, "counts": {k: int(sc.get(k, 0)) for k in STYLES + ["Unclassified"]},
                 "unclassified_pct": round(float((d["style"] == "Unclassified").mean()) * 100, 1),
                 "gapA": {k: round(float(d.loc[d["style"] == k, "gA"].mean()), 2) for k in STYLES},
                 "gapB": {k: round(float(d.loc[d["style"] == k, "gB"].mean()), 2) for k in STYLES}}
print("styles", out["styles"])
A0 = smf.ols("points ~ lp + I(lp**2) + C(taster)", d).fit(); d["gA0"] = d.points - A0.fittedvalues
B0 = smf.ols("points ~ lp + I(lp**2)", d).fit(); d["gB0"] = d.points - B0.fittedvalues
out["year_check"] = {}
for sty in ["Red", "White"]:
    st = d[(d.price > 15) & (d.price <= 25) & (d["style"] == sty)]
    rob = {}
    for tag, ka, kb in [("with", "gA", "gB"), ("without", "gA0", "gB0")]:
        g = st.groupby(["country", "variety"]).agg(n=(ka, "size"), ma=(ka, "mean"), sa=(ka, "std"), mb=(kb, "mean"), sb=(kb, "std"))
        g = g[g.n >= 30]
        g["r"] = np.minimum(g.ma - 1.96 * g.sa / np.sqrt(g.n), g.mb - 1.96 * g.sb / np.sqrt(g.n))
        rob[tag] = g
    tw = set(rob["with"].sort_values("r", ascending=False).head(10).index); to = set(rob["without"].sort_values("r", ascending=False).head(10).index)
    cm = rob["with"].index.intersection(rob["without"].index)
    out["year_check"][sty] = {"overlap": len(tw & to), "rank_corr": round(float(rob["with"].loc[cm, "r"].rank().corr(rob["without"].loc[cm, "r"].rank())), 2)}
print("year_check", out["year_check"])
tiers = [("Up to $15", 0, 15), ("$16–25", 15, 25), ("$26–50", 25, 50), ("$51–100", 50, 100), ("Over $100", 100, 1e6)]
out["tiers"] = []
for lab, lo, hi in tiers:
    s = d[(d.price > lo) & (d.price <= hi)]
    rows = []
    for (sty, c, vv), g in s[s["style"].isin(STYLES)].groupby(["style", "country", "variety"]):
        n = len(g)
        if n < 30: continue
        r = {"style": sty, "country": c, "variety": vv, "n": n, "med": float(g.price.median()), "s90": round(float((g.points >= 90).mean()) * 100, 1)}
        for k in ["A", "B"]:
            m, sd = g["g" + k].mean(), g["g" + k].std()
            se = sd / np.sqrt(n)
            r["m" + k] = round(m, 3); r["lo" + k] = round(m - 1.96 * se, 3); r["hi" + k] = round(m + 1.96 * se, 3)
        tv = g.taster.value_counts(normalize=True)
        r["critic"] = tv.index[0]; r["cshare"] = round(float(tv.iloc[0]) * 100)
        rows.append(r)
    ns = s["style"].value_counts()
    out["tiers"].append({"label": lab, "lo": lo, "hi": hi if hi < 1e6 else None, "n": len(s), "ns": {k: int(ns.get(k, 0)) for k in STYLES}, "groups": rows})
    for sty in ["Red", "White"]:
        rr = sorted([r for r in rows if r["style"] == sty], key=lambda r: -min(r["loA"], r["loB"]))[:4]
        print(lab, sty, int(ns.get(sty, 0)), [(r["country"], r["variety"], r["n"], round(min(r["loA"], r["loB"]), 2)) for r in rr])
# --- 5. BC shelf check for the $16-25 shortlist
b = pd.read_csv(bc_path)
w = b[(b.ITEM_CATEGORY_NAME == "Wine") & (b.PRODUCT_LITRES_PER_CONTAINER == 0.75) & (b.PRD_CONTAINER_PER_SELL_UNIT == 1)].copy()
nm = w.PRODUCT_LONG_NAME.str.upper(); cty = w.PRODUCT_COUNTRY_ORIGIN_NAME; cls = w.ITEM_CLASS_NAME
rules = {
    ("France", "Melon"): ("class France White Wine, name contains Muscadet", cls.eq("France White Wine") & nm.str.contains("MUSCADET")),
    ("Portugal", "Portuguese Red"): ("class Portugal Red Wine", cls.eq("Portugal Red Wine")),
    ("Germany", "Riesling"): ("class Germany White Wine, name contains Riesling", cls.eq("Germany White Wine") & nm.str.contains("RIESLING")),
    ("Australia", "Riesling"): ("class Australia White Wine, name contains Riesling", cls.eq("Australia White Wine") & nm.str.contains("RIESLING")),
    ("Australia", "Shiraz"): ("class Australia Red Wine, name contains Shiraz", cls.eq("Australia Red Wine") & nm.str.contains("SHIRAZ")),
    ("France", "Malbec"): ("class France Red Wine, name contains Malbec or Cahors", cls.eq("France Red Wine") & (nm.str.contains("MALBEC") | nm.str.contains("CAHORS"))),
    ("South Africa", "Chardonnay"): ("class South Africa White Wine, name contains Chardonnay", cls.eq("South Africa White Wine") & nm.str.contains("CHARDONNAY")),
    ("Italy", "Turbiana"): ("class Italy White Wine, name contains Lugana", cls.eq("Italy White Wine") & nm.str.contains("LUGANA")),
    ("Spain", "Tinta de Toro"): ("class Spain Red Wine, name contains Toro", cls.eq("Spain Red Wine") & nm.str.contains(r"\bTORO\b")),
    ("France", "Pinot Noir"): ("France red, name contains Pinot Noir or Bourgogne", cls.eq("France Red Wine") & (nm.str.contains("PINOT NOIR") | nm.str.contains("BOURGOGNE"))),
    ("Argentina", "Chardonnay"): ("class Argentina White Wine, name contains Chardonnay", cls.eq("Argentina White Wine") & nm.str.contains("CHARDONNAY")),
    ("Argentina", "Pinot Noir"): ("class Argentina Red Wine, name contains Pinot Noir", cls.eq("Argentina Red Wine") & nm.str.contains("PINOT NOIR")),
}
us = d[(d.price > 15) & (d.price <= 25) & d["style"].isin(["Red", "White"])]
bc = []
for (c, vv), (desc, m) in rules.items():
    p = w[m].PRODUCT_PRICE
    u = us[(us.country == c) & (us.variety == vv)].price
    bc.append({"country": c, "variety": vv, "match": desc, "skus": int(len(p)),
               "bc_med": float(p.median()) if len(p) else None, "bc_q1": float(p.quantile(.25)) if len(p) else None,
               "bc_q3": float(p.quantile(.75)) if len(p) else None, "bc_share25": round(float((p <= 25).mean()) * 100) if len(p) else None,
               "us_med": float(u.median())})
out["bc"] = bc
out["bc_meta"] = {"wines": int((b.ITEM_CATEGORY_NAME == "Wine").sum()), "single750": int(len(w)), "month": "June 2026"}
for r in bc: print(r)
# --- 6. reuse verified pieces
ver = json.load(open(ver_path)); chk = json.load(open(chk_path))
out["seg90"] = {"points": ver["eligible_points"], "top10": [[r["country"], r["variety"]] for r in ver["team_top10"]]}
out["coverage"] = chk["coverage"]; out["country_vg"] = chk["country_vg"]
out["goldstein"] = chk["goldstein"]
json.dump(out, open(out_path, "w"), ensure_ascii=False, separators=(",", ":"), default=float)
print("bytes", len(json.dumps(out, default=float)))
