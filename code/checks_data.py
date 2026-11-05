"""Chart data for the 'Checking Our Wine Ranking' page.
Run: python3 -I data.py <dedup_parquet> <out_json>
"""
import sys, json, numpy as np, pandas as pd
import statsmodels.formula.api as smf
d0 = pd.read_parquet(sys.argv[1])
d = d0.dropna(subset=["price", "country"]).copy()
d["variety"] = d.variety.fillna("(unknown)")
d["lp"] = np.log(d.price); d["taster"] = d.taster_name.fillna("(none)")
d["vintage"] = pd.to_numeric(d.title.str.extract(r"\b(19[5-9]\d|20[01]\d)\b")[0], errors="coerce")
out = {}
# 1) critic coverage, top 10 countries
top = d.country.value_counts().index[:10]
cov = []
for c in top:
    s = d[d.country == c]; named = s[s.taster != "(none)"]
    vc = named.taster.value_counts()
    cov.append(dict(country=c, n=len(s), top_critic=vc.index[0], top=round(vc.iloc[0] / len(s) * 100, 1),
                    other=round((len(named) - vc.iloc[0]) / len(s) * 100, 1), none=round((len(s) - len(named)) / len(s) * 100, 1),
                    top_n=int(vc.iloc[0]), other_n=int(len(named) - vc.iloc[0]), none_n=int(len(s) - len(named))))
out["coverage"] = cov
# 2) country mean VG with / without critic adjustment
m_fe = smf.ols("points ~ lp + I(lp**2) + C(taster)", d).fit(); d["fe"] = d.points - m_fe.fittedvalues
m_no = smf.ols("points ~ lp + I(lp**2)", d).fit(); d["nofe"] = d.points - m_no.fittedvalues
g = d[d.country.isin(top)].groupby("country").agg(n=("fe", "size"), fe=("fe", "mean"), nofe=("nofe", "mean")).reindex(top).reset_index()
out["country_vg"] = g.round(2).to_dict("records")
# 3) top 10 lists in $15-25
band = (d.price > 15) & (d.price <= 25)
lists = {}
for k in ["fe", "nofe"]:
    s = d[band].groupby(["country", "variety"])[k].agg(["size", "mean", "std"]).reset_index()
    s = s[s["size"] >= 50]; s["lo"] = s["mean"] - 1.96 * s["std"] / np.sqrt(s["size"])
    s = s.sort_values("lo", ascending=False).reset_index(drop=True); s["rank"] = s.index + 1
    lists[k] = s
for k in ["fe", "nofe"]:
    other = lists["nofe" if k == "fe" else "fe"].set_index(["country", "variety"])["rank"]
    t = lists[k].head(10).copy()
    t["other_rank"] = [int(other.get((a, b), -1)) for a, b in zip(t.country, t.variety)]
    # critic of segment (top critic share)
    crit = []
    for a, b in zip(t.country, t.variety):
        s = d[band & (d.country == a) & (d.variety == b)].taster.value_counts(normalize=True)
        crit.append(f"{s.index[0]} {round(s.iloc[0]*100)}%")
    t["critic"] = crit
    out["top_" + k] = t[["country", "variety", "size", "mean", "lo", "rank", "other_rank", "critic"]].round(2).to_dict("records")
# 4) score counts 80-100 and share at 80 by band
out["score_counts"] = {int(k): int(v) for k, v in d0.points.value_counts().sort_index().items()}
d["bandlab"] = pd.cut(d.price, [0, 15, 25, 40, 75, 1e5], labels=["Under $15", "$15-25", "$25-40", "$40-75", "$75 and up"])
out["low_share_by_band"] = [dict(band=str(b), at80=round((s.points == 80).mean() * 100, 2), le82=round((s.points <= 82).mean() * 100, 1), n=len(s))
                            for b, s in d.groupby("bandlab", observed=True)]
# 5) VG by vintage bin
bins = [1949, 2003, 2006, 2008, 2010, 2012, 2013, 2014, 2015, 2017]
labs = ["2003 or earlier", "2004-06", "2007-08", "2009-10", "2011-12", "2013", "2014", "2015", "2016-17"]
d["vb"] = pd.cut(d.vintage, bins, labels=labs)
vb = d.groupby("vb", observed=True).agg(n=("fe", "size"), fe=("fe", "mean"), sd=("fe", "std")).reset_index()
vb["se"] = vb.sd / np.sqrt(vb.n)
out["vintage_vg"] = [dict(bin=str(r.vb), n=int(r.n), vg=round(r.fe, 2), lo=round(r.fe - 1.96 * r.se, 2), hi=round(r.fe + 1.96 * r.se, 2)) for r in vb.itertuples()]
# top10 with year control
m_v = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d.assign(vb=d.vb.astype(str))).fit()
d["fev"] = d.points - m_v.fittedvalues
s = d[band].groupby(["country", "variety"]).fev.agg(["size", "mean", "std"]).reset_index(); s = s[s["size"] >= 50]
s["lo"] = s["mean"] - 1.96 * s["std"] / np.sqrt(s["size"])
tv = set(map(tuple, s.sort_values("lo", ascending=False).head(10)[["country", "variety"]].values))
tf = set(map(tuple, lists["fe"].head(10)[["country", "variety"]].values))
out["year_control_overlap"] = len(tv & tf)
common = lists["fe"].set_index(["country", "variety"]).index.intersection(s.set_index(["country", "variety"]).index)
out["year_control_rankcorr"] = round(float(lists["fe"].set_index(["country", "variety"]).loc[common, "mean"].rank().corr(s.set_index(["country", "variety"]).loc[common, "mean"].rank())), 3)
pp = {}
for lab, gg in d.groupby(pd.cut(d.vintage, [1949, 2005, 2010, 2013, 2017], labels=["2005 or earlier", "2006-10", "2011-13", "2014-17"]), observed=True):
    mm = smf.ols("lp ~ points", gg).fit(); pp[str(lab)] = round((np.exp(mm.params.points) - 1) * 100, 1)
out["premium_by_era"] = pp
out["goldstein"] = [{"group": "Regular drinkers", "pts": -4}, {"group": "Experts", "pts": 7}]
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
for k, v in out.items():
    if k not in ("score_counts",): print(k, json.dumps(v, ensure_ascii=False)[:900])
print("score_counts", out["score_counts"])
