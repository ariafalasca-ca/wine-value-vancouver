"""Independent re-derivation of the numbers on the presentation slides, from the raw Kaggle CSV, the June 2026 BC list and the parsed Liquor Market Review.
Run from code/: python3 -I audit_v5.py   (prints one OK/XX line per claim; exits 1 if any claim does not match)
"""
import sys, re, json, numpy as np, pandas as pd
import statsmodels.formula.api as smf
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from style_map import style
from paths import RAW_WINE, BC_LIST, LMR_PREPOST, OUT, need
RAW = need(RAW_WINE); BC = need(BC_LIST)
R = {}
def claim(k, slide, claimed, got, ok=None, record=False):
    # record=True: an informational value printed for reference, not tested; ok given = a tolerance check
    kind = "record" if record else "check"
    if record: ok = True
    if ok is None: ok = (claimed == got)
    R[k] = {"slide": slide, "claimed": claimed, "recomputed": got, "match": bool(ok), "kind": kind}

raw = pd.read_csv(RAW, index_col=0)
claim("raw rows", 3, 129971, len(raw))
dd = raw.drop_duplicates()
claim("duplicates removed", 3, 9983, len(raw) - len(dd))
d = dd.dropna(subset=["price", "country"]).copy()
claim("no price or country", 3, 8450, len(dd) - len(d))
claim("reviews used", 3, 111538, len(d))
claim("share kept %", 3, 86, round(len(d) / len(raw) * 100))
claim("critics", 3, 19, int(dd.taster_name.nunique()))
d["variety"] = d.variety.fillna("(unknown)"); d["designation"] = d.designation.fillna("")
d["lp"] = np.log(d.price); d["taster"] = d.taster_name.fillna("(none)")
d["style"] = [style(r) for r in d.itertuples()]
v = pd.to_numeric(d.title.str.extract(r"\b(19[5-9]\d|20[01]\d)\b")[0], errors="coerce")
d["vb"] = pd.cut(v, [1949, 2003, 2006, 2008, 2010, 2012, 2013, 2014, 2015, 2017]).astype(object).where(v.notna(), "NV").astype(str)

# slide 4: median price by score, 13% per point, 89->90 step
med = d.groupby("points").price.median()
claim("median $ at 80", 4, 14, float(med[80])); claim("median $ at 90", 4, 30, float(med[90])); claim("median $ at 100", 4, 359, float(med[100]))
top_var = d.variety.value_counts().index[:30]; top_cty = d.country.value_counts().index[:15]
d["var30"] = np.where(d.variety.isin(top_var), d.variety, "Other"); d["cty15"] = np.where(d.country.isin(top_cty), d.country, "Other")
m1 = smf.ols("lp ~ points + C(taster) + C(var30) + C(cty15)", d).fit()
pp = (np.exp(m1.params.points) - 1) * 100; ci = [(np.exp(x) - 1) * 100 for x in m1.conf_int().loc["points"]]
claim("premium per point % (critic+grape+country)", 4, 12.8, round(pp, 1)); claim("premium 95% CI", 4, [12.7, 12.9], [round(c, 1) for c in ci])
steps = (np.log(med).diff() * 100).apply(lambda x: (np.exp(x / 100) - 1) * 100)
claim("step 89->90 %", 4, 15, round(float(steps[90])))
nb = [round(float(steps[k])) for k in [87, 88, 89, 91, 92, 93]]
claim("neighbour steps range %", 4, [8, 27], [min(nb), max(nb)])

# slide 5: simple curve and the $20 example
simple = smf.ols("points ~ lp + I(lp**2)", d).fit()
e20 = simple.params.Intercept + simple.params.lp * np.log(20) + simple.params["I(lp ** 2)"] * np.log(20) ** 2
claim("typical score at $20", 5, 87.5, round(float(e20), 1)); claim("gap for 90 at $20", 5, 2.5, round(90 - float(e20), 1))

# models A and B
A = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d).fit(); d["gA"] = d.points - A.fittedvalues
B = smf.ols("points ~ lp + I(lp**2) + C(vb)", d).fit(); d["gB"] = d.points - B.fittedvalues
claim("R2 with critic adj.", 12, 0.44, round(A.rsquared, 2)); claim("R2 without", 12, 0.41, round(B.rsquared, 2))
claim("mean gap per critic is 0 (max abs)", 12, "< 1e-9", float(d.groupby("taster").gA.mean().abs().max()), float(d.groupby("taster").gA.mean().abs().max()) < 1e-9)
cv = d.groupby("country").agg(A=("gA", "mean"), B=("gB", "mean"))
claim("Austria without adj.", 7, 1.6, round(float(cv.loc["Austria", "B"]), 1)); claim("Austria with adj.", 7, 0.3, round(float(cv.loc["Austria", "A"]), 1))
claim("unclassified style %", 12, 2.8, round(float((d["style"] == "Unclassified").mean() * 100), 1))
fa, fb = d.loc[d["style"] == "Fortified & dessert", ["gA", "gB"]].mean(); ro = d.loc[d["style"] == "Rosé", ["gA", "gB"]].mean()
claim("fortified gap both ways", 8, [0.68, 0.85], sorted([round(float(fa), 2), round(float(fb), 2)]))
claim("rosé gap about -0.5", 8, -0.5, [round(float(x), 2) for x in ro], all(abs(x + 0.5) < 0.1 for x in ro))

# slide 7: critic coverage
cov = {}
for c in ["US", "France", "Italy", "Spain", "Portugal", "Chile", "Argentina", "Austria", "Australia", "Germany"]:
    s = d[d.country == c].taster_name.value_counts(normalize=True, dropna=False)
    top = s.index[0] if not pd.isna(s.index[0]) else s.index[1]
    sh = float(d[d.country == c].taster_name.value_counts(normalize=True, dropna=False).sort_values(ascending=False).loc[lambda x: x.index.notna()].iloc[0]) * 100
    cov[c] = (top, round(sh))
claim("critic coverage", 7, {"US": ("Virginie Boone", 17), "France": ("Roger Voss", 81), "Italy": ("Kerin O’Keefe", 57), "Spain": ("Michael Schachner", 99), "Portugal": ("Roger Voss", 99), "Chile": ("Michael Schachner", 97), "Argentina": ("Michael Schachner", 100), "Austria": ("Anne Krebiehl\xa0MW", 69), "Australia": ("Joe Czerwinski", 87), "Germany": ("Anna Lee C. Iijima", 81)}, cov,
      all(cov[c][1] == s for c, (_, s) in {"US": ("", 17), "France": ("", 81), "Italy": ("", 57), "Spain": ("", 99), "Portugal": ("", 99), "Chile": ("", 97), "Argentina": ("", 100), "Austria": ("", 69), "Australia": ("", 87), "Germany": ("", 81)}.items()))

# slide 6: share-90 rule (critic-adjusted model without vintage, as in the team's rule check)
mv = smf.ols("points ~ lp + I(lp**2) + C(taster)", d).fit(); d["vg"] = d.points - mv.fittedvalues; d["hi"] = (d.points >= 90).astype(float)
g = d.groupby(["country", "variety"]).agg(n=("points", "size"), med=("price", "median"), share90=("hi", "mean"), vg=("vg", "mean"), sd=("vg", "std")).reset_index()
e = g[(g.n >= 30) & (g.med <= 25)].copy()
claim("eligible groups (median <= $25, n >= 30)", 6, 178, len(e))
claim("corr share90 vs median price", 6, 0.69, round(float(e[["share90", "med"]].corr().iloc[0, 1]), 2))
team = e.sort_values(["share90", "n"], ascending=[False, False]).reset_index(drop=True); team["rank"] = team.index + 1
mo = team[(team.country == "Greece") & (team.variety == "Moschofilero")].iloc[0]; ac = team[(team.country == "Austria") & (team.variety == "Chardonnay")].iloc[0]
claim("Moschofilero rank by share90", 6, 72, int(mo["rank"])); claim("Moschofilero gap", 6, 2.4, round(float(mo.vg), 1)); claim("Austrian Chardonnay rank", 6, 4, int(ac["rank"]))
claim("Austrian Chardonnay gap about 0", 6, "≈0", round(float(ac.vg), 2), abs(ac.vg) < 0.25)

# tiers and the shelf guide
tiers = [("Up to $15", 0, 15), ("$16–25", 15, 25), ("$26–50", 25, 50), ("$51–100", 50, 100), ("Over $100", 100, 1e6)]
claim("tier counts", 10, [23260, 33137, 36661, 15251, 3229], [int(((d.price > lo) & (d.price <= hi)).sum()) for _, lo, hi in tiers])
def groups(lo, hi, sty):
    s = d[(d.price > lo) & (d.price <= hi) & (d["style"] == sty)]
    g = s.groupby(["country", "variety"]).agg(n=("gA", "size"), mA=("gA", "mean"), sA=("gA", "std"), mB=("gB", "mean"), sB=("gB", "std"), med=("price", "median")).reset_index()
    g = g[g.n >= 30].copy()
    g["loA"] = g.mA - 1.96 * g.sA / np.sqrt(g.n); g["loB"] = g.mB - 1.96 * g.sB / np.sqrt(g.n)
    g["hiA"] = g.mA + 1.96 * g.sA / np.sqrt(g.n); g["hiB"] = g.mB + 1.96 * g.sB / np.sqrt(g.n)
    g["cau"] = np.minimum(g.loA, g.loB); g["best"] = np.maximum(g.hiA, g.hiB)
    return g
def top(g, k=10): return g.sort_values("cau", ascending=False).head(k)
def row(g, c, v): return g[(g.country == c) & (g.variety == v)].iloc[0]
r25 = groups(15, 25, "Red"); w25 = groups(15, 25, "White")
t = top(r25); claim("red $16-25 top 3 (cautious)", 8, ["Portugal Portuguese Red 1.38", "Australia Shiraz 0.98", "France Malbec 0.94"], [f"{r.country} {r.variety} {r.cau:.2f}" for r in t.head(3).itertuples()])
claim("Portuguese red n, median", 8, [535, 20], [int(row(r25, "Portugal", "Portuguese Red").n), float(row(r25, "Portugal", "Portuguese Red").med)])
claim("Shiraz n, median", 8, [166, 20], [int(row(r25, "Australia", "Shiraz").n), float(row(r25, "Australia", "Shiraz").med)])
claim("Malbec FR n, median", 8, [137, 20], [int(row(r25, "France", "Malbec").n), float(row(r25, "France", "Malbec").med)])
wk = r25.sort_values("best").head(2); claim("red $16-25 weakest 2 (best estimate)", 8, ["Argentina Pinot Noir -1.27", "France Pinot Noir -1.21"], [f"{r.country} {r.variety} {r.best:.2f}" for r in wk.itertuples()])
tA = set(zip(*[r25.sort_values("loA", ascending=False).head(10)[c] for c in ["country", "variety"]])); tB = set(zip(*[r25.sort_values("loB", ascending=False).head(10)[c] for c in ["country", "variety"]]))
claim("red top 10 same both ways", 8, 8, len(tA & tB))
tA = set(zip(*[w25.sort_values("loA", ascending=False).head(10)[c] for c in ["country", "variety"]])); tB = set(zip(*[w25.sort_values("loB", ascending=False).head(10)[c] for c in ["country", "variety"]]))
claim("white top 10 same both ways", 8, 9, len(tA & tB))
t = top(w25); claim("white $16-25 top 3", 8, ["France Melon", "Germany Riesling", "Australia Riesling"], [f"{r.country} {r.variety}" for r in t.head(3).itertuples()])
claim("Muscadet cautious", 10, 1.7, round(float(row(w25, "France", "Melon").cau), 1))
# shelf graphic: best non-US red/white and weakest per tier
shelf = {}
for lab, lo, hi in tiers:
    rr = groups(lo, hi, "Red"); ww = groups(lo, hi, "White"); rr = rr[rr.country != "US"]; ww = ww[ww.country != "US"]
    al = pd.concat([groups(lo, hi, s) for s in ["Red", "White"]]); al = al[al.country != "US"]
    br = top(rr, 1).iloc[0]; bw = top(ww, 1).iloc[0]; wo = al.sort_values("best").iloc[0]
    shelf[lab] = [f"{br.country} {br.variety} {br.cau:+.1f}", f"{bw.country} {bw.variety} {bw.cau:+.1f}", f"{wo.country} {wo.variety} {wo.best:+.1f}"]
claim("shelf graphic rows", 10, {"Over $100": ["Italy Sangiovese Grosso +0.3", "France Chardonnay -0.4", "Italy Sangiovese -0.1"], "$51–100": ["Portugal Portuguese Red +1.1", "France Sauvignon Blanc +1.0", "New Zealand Pinot Noir -0.3"], "$26–50": ["France Malbec +1.6", "France Chenin Blanc +1.1", "France Pinot Noir -0.7"], "$16–25": ["Portugal Portuguese Red +1.4", "France Melon +1.7", "Argentina Pinot Noir -1.3"], "Up to $15": ["Portugal Portuguese Red +0.6", "Germany Riesling +0.9", "Argentina Chardonnay -0.9"]}, shelf)
r50 = groups(25, 50, "Red"); r50 = r50[r50.country != "US"].sort_values("cau", ascending=False).reset_index(drop=True)
claim("$26-50: Malbec vs Portuguese red (close 2nd)", 10, [1.6, 1.5], [round(float(r50.iloc[0].cau), 1), round(float(row(r50, "Portugal", "Portuguese Red").cau), 1)])
claim("Portuguese red rank at $26-50", 10, 2, int(r50[(r50.country == "Portugal") & (r50.variety == "Portuguese Red")].index[0]) + 1)
h = groups(100, 1e6, "Red"); claim("best group over $100 (cautious)", 11, 0.29, round(float(top(h, 1).iloc[0].cau), 2))

# slide 11: 80-82 share by tier; vintage check
for lab, lo, hi, cl in [("up to $15", 0, 15, 6.7), ("$16-25", 15, 25, 2.4)]:
    s = d[(d.price > lo) & (d.price <= hi)]; claim(f"share scoring 80-82, {lab} %", 11, cl, round(float((s.points <= 82).mean() * 100), 1))
A0 = smf.ols("points ~ lp + I(lp**2) + C(taster)", d).fit(); d["gA0"] = d.points - A0.fittedvalues
B0 = smf.ols("points ~ lp + I(lp**2)", d).fit(); d["gB0"] = d.points - B0.fittedvalues
for sty, ov, rc in [("Red", 10, 0.98), ("White", 9, 0.99)]:
    st = d[(d.price > 15) & (d.price <= 25) & (d["style"] == sty)]; rob = {}
    for tag, ka, kb in [("with", "gA", "gB"), ("without", "gA0", "gB0")]:
        g = st.groupby(["country", "variety"]).agg(n=(ka, "size"), ma=(ka, "mean"), sa=(ka, "std"), mb=(kb, "mean"), sb=(kb, "std")); g = g[g.n >= 30]
        g["r"] = np.minimum(g.ma - 1.96 * g.sa / np.sqrt(g.n), g.mb - 1.96 * g.sb / np.sqrt(g.n)); rob[tag] = g
    tw = set(rob["with"].sort_values("r", ascending=False).head(10).index); to = set(rob["without"].sort_values("r", ascending=False).head(10).index); cm = rob["with"].index.intersection(rob["without"].index)
    claim(f"vintage check {sty}: top-10 overlap", 11, ov, len(tw & to)); claim(f"vintage check {sty}: rank corr", 11, rc, round(float(rob["with"].loc[cm, "r"].rank().corr(rob["without"].loc[cm, "r"].rank())), 2))

# slide 12: inflation (rescale 1.073: gaps unchanged, re-tier) and origin premium
d2 = d.copy(); d2["price"] = d2.price * 1.073; d2["lp"] = np.log(d2.price)
A2 = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d2).fit(); claim("uniform rescale: max gap change", 12, "< 1e-9", float((d2.points - A2.fittedvalues - d.gA).abs().max()), float((d2.points - A2.fittedvalues - d.gA).abs().max()) < 1e-6)
d2["gA"], d2["gB"] = d.gA, d.gB
def groups2(dd_, lo, hi, sty):
    s = dd_[(dd_.price > lo) & (dd_.price <= hi) & (dd_["style"] == sty)]
    g = s.groupby(["country", "variety"]).agg(n=("gA", "size"), mA=("gA", "mean"), sA=("gA", "std"), mB=("gB", "mean"), sB=("gB", "std")).reset_index(); g = g[g.n >= 30].copy()
    g["cau"] = np.minimum(g.mA - 1.96 * g.sA / np.sqrt(g.n), g.mB - 1.96 * g.sB / np.sqrt(g.n)); return g.set_index(["country", "variety"])
for sty, hold, rc, lab in [("Red", 2, 0.96, "top 2 red hold"), ("White", 3, 0.95, "top 3 white hold")]:
    g0 = groups2(d, 15, 25, sty).sort_values("cau", ascending=False); g1 = groups2(d2, 15, 25, sty).sort_values("cau", ascending=False)
    claim(f"inflation: {lab} (as a set)", 12, True, set(g0.index[:hold]) == set(g1.index[:hold])); claim(f"inflation: {sty} top {hold} order after", 12, "-", list(g1.index[:hold]), record=True)
    cm = g0.index.intersection(g1.index); claim(f"inflation: rank corr {sty}", 12, rc, round(float(g0.loc[cm, "cau"].rank().corr(g1.loc[cm, "cau"].rank())), 2))
    if sty == "Red": claim("inflation: French Malbec rank in 2026 $", 12, 6, int(list(g1.index).index(("France", "Malbec"))) + 1)
tv = d.variety.value_counts(); d["var2"] = np.where(d.variety.isin(tv[tv >= 100].index), d.variety, "(other)")
op = smf.ols("lp ~ points + C(var2) + C(country)", d).fit()
cp = lambda c: op.params.get(f"C(country)[T.{c}]", 0.0)
prem = {c: round((1 - np.exp(cp(c) - cp("US"))) * 100) for c in ["Chile", "Portugal", "Argentina", "Australia", "Spain", "France"]}
prem1 = {c: round((1 - np.exp(cp(c) - cp("US"))) * 100, 1) for c in ["Chile", "Portugal", "Argentina", "Australia", "Spain", "France"]}
claim("origin premium (1 dp)", 12, "see slide", prem1, record=True)
claim("origin premium below US %", 12, {"Chile": 29, "Portugal": 22, "Argentina": 20, "Australia": 14, "Spain": 13, "France": 1}, prem)
claim("origin model: % per point", 12, 12.2, round((np.exp(op.params.points) - 1) * 100, 1))

# slide 9: BC list
b = pd.read_csv(BC)
w = b[(b.ITEM_CATEGORY_NAME == "Wine") & (b.PRODUCT_LITRES_PER_CONTAINER == 0.75) & (b.PRD_CONTAINER_PER_SELL_UNIT == 1)].copy()
claim("BC wines listed", 3, 5957, int((b.ITEM_CATEGORY_NAME == "Wine").sum()))
nm = w.PRODUCT_LONG_NAME.str.upper(); cls = w.ITEM_CLASS_NAME
rules = {"Portuguese red": cls.eq("Portugal Red Wine"), "Shiraz AU": cls.eq("Australia Red Wine") & nm.str.contains("SHIRAZ"), "Malbec FR": cls.eq("France Red Wine") & (nm.str.contains("MALBEC") | nm.str.contains("CAHORS")),
         "Muscadet": cls.eq("France White Wine") & nm.str.contains("MUSCADET"), "Riesling DE": cls.eq("Germany White Wine") & nm.str.contains("RIESLING"), "Riesling AU": cls.eq("Australia White Wine") & nm.str.contains("RIESLING"),
         "Pinot Noir AR": cls.eq("Argentina Red Wine") & nm.str.contains("PINOT NOIR"), "Chardonnay AR": cls.eq("Argentina White Wine") & nm.str.contains("CHARDONNAY")}
bcc = {k: (int(m.sum()), float(w[m].PRODUCT_PRICE.median())) for k, m in rules.items()}
claim("BC listings and medians", 9, {"Portuguese red": (23, 18.99), "Shiraz AU": (57, 22.99), "Malbec FR": (5, 37.99), "Muscadet": (6, 36.49), "Riesling DE": (54, 50.49), "Riesling AU": (3, 24.99), "Pinot Noir AR": (2, 18.99), "Chardonnay AR": (18, 19.99)}, bcc)
claim("till price of CA$25 at 15% tax", 9, 28.75, round(25 * 1.15, 2))
claim("US 750 mL wines still in the June 2026 catalogue (store site shows 0 stores)", 9, 267, int((w.PRODUCT_COUNTRY_ORIGIN_NAME.str.contains("United States|USA", case=False, na=False)).sum()))

# LMR and CPI from the earlier research files
lm = pd.read_csv(need(LMR_PREPOST), encoding="utf-8-sig").set_index("country").rename(index={"ALL": "All wine"}).rename(columns={"Δ price %": "d_price", "Δ litres %": "d_litres"})
for o, v in [("Portugal", -2.5), ("Australia", 2.4), ("France", 4.1), ("Italy", 2.9), ("Spain", -2.5), ("Chile", 0.6), ("All wine", 0.9)]:
    claim(f"LMR wholesale $/L change, {o} %", 12, v, round(float(lm.loc[o, "d_price"]), 1))
claim("LMR US volume change %", 12, -85, round(float(lm.loc["USA", "d_litres"])))
claim("LMR: every recommended origin moved < 5%", 9, True, bool((lm.loc[["Portugal", "Australia", "France", "Italy", "Spain", "Chile", "Argentina", "New Zealand"], "d_price"].abs() < 5).all()))
json.dump(R, open(OUT / "audit_results.json", "w"), indent=1, default=str, ensure_ascii=False)
for k, v in R.items(): print(("NOTE" if v["kind"] == "record" else "OK " if v["match"] else "XX ") + " " + k, "| claimed", v["claimed"], "| recomputed", v["recomputed"])
chk = {k: v for k, v in R.items() if v["kind"] == "check"}; bad = [k for k, v in chk.items() if not v["match"]]
print(f"\n{len(chk) - len(bad)} of {len(chk)} recomputed checks match; plus {len(R) - len(chk)} informational records (not tested).", "Mismatches:" if bad else "", bad if bad else "")
sys.exit(1 if bad else 0)
