"""Wine style classification (Red / White / Rosé / Sparkling / Fortified & dessert) and per-style shelf rankings.
Run: python3 -I style_map.py <dedup_parquet> <out_json>
"""
import sys, re, json, numpy as np, pandas as pd
import statsmodels.formula.api as smf

RED = """Pinot Noir|Cabernet Sauvignon|Red Blend|Bordeaux-style Red Blend|Syrah|Merlot|Zinfandel|Malbec|Sangiovese|Nebbiolo|Portuguese Red|Tempranillo|Rhône-style Red Blend|Cabernet Franc|Shiraz|Gamay|Petite Sirah|Grenache|Tempranillo Blend|Barbera|Sangiovese Grosso|Carmenère|Corvina, Rondinella, Molinara|Garnacha|Nero d'Avola|Aglianico|Petit Verdot|Meritage|Mourvèdre|Primitivo|Blaufränkisch|Montepulciano|G-S-M|Zweigelt|Mencía|Dolcetto|Tinta de Toro|Touriga Nacional|Tannat|Pinot Nero|Monastrell|Pinotage|Cabernet Sauvignon-Merlot|Nerello Mascalese|Bonarda|Cabernet Sauvignon-Syrah|Tinto Fino|Sagrantino|Malbec-Merlot|Cabernet Blend|Negroamaro|Lagrein|Carignan|St. Laurent|Spätburgunder|Agiorgitiko|Malbec-Cabernet Sauvignon|Syrah-Grenache|Austrian Red Blend|Grenache-Syrah|Provence red blend|Tempranillo-Cabernet Sauvignon|Alicante Bouschet|Graciano|Cabernet Sauvignon-Carmenère|Shiraz-Viognier|Cinsault|Frappato|Shiraz-Cabernet Sauvignon|Lemberger|Claret|Prugnolo Gentile|Syrah-Cabernet Sauvignon|Saperavi|Merlot-Cabernet Sauvignon|Tempranillo-Garnacha|Pinot Meunier""".split("|")
WHITE = """Chardonnay|Riesling|Sauvignon Blanc|White Blend|Pinot Gris|Grüner Veltliner|Pinot Grigio|Viognier|Portuguese White|Gewürztraminer|Bordeaux-style White Blend|Chenin Blanc|Albariño|Rhône-style White Blend|Pinot Blanc|Moscato|Sauvignon|Verdejo|Torrontés|Melon|Garganega|Vermentino|Roussanne|Verdicchio|Pinot Bianco|Sémillon|Turbiana|Muscat|Grenache Blanc|Fiano|Vernaccia|Alvarinho|Friulano|Viura|Greco|Grillo|Godello|Arneis|Ribolla Gialla|Falanghina|Fumé Blanc|Sauvignon Blanc-Semillon|Marsanne|Arinto|Cortese|Austrian white blend|Semillon-Sauvignon Blanc|Verdelho|Vidal Blanc|Alsace white blend|Petit Manseng|Furmint|Trebbiano|Müller-Thurgau|Sylvaner|Pecorino|Malvasia|Assyrtico|Gros and Petit Manseng|Weissburgunder|Carricante|Muscat Canelli|Silvaner|Traminer|Moschofilero|Garnacha Blanca|Chardonnay-Viognier""".split("|")
ROSE = ["Rosé", "Rosato", "Rosado"]
SPARK = ["Sparkling Blend", "Champagne Blend", "Glera", "Prosecco", "Portuguese Sparkling", "Lambrusco"]
FORT = ["Port", "Sherry", "Pedro Ximénez", "Moscatel", "Madeira", "Tokaji"]
base = {**{v: "Red" for v in RED}, **{v: "White" for v in WHITE}, **{v: "Rosé" for v in ROSE},
        **{v: "Sparkling" for v in SPARK}, **{v: "Fortified & dessert" for v in FORT}}
re_spark = re.compile(r"champagne|\bbrut\b|sparkling|\bcava\b|crémant|cremant|prosecco|spumante|\bsekt\b|blanc de blancs|blanc de noirs|franciacorta|frizzante|pét-nat|pet-nat", re.I)
re_fort = re.compile(r"\bport\b|\bporto\b|sherry|madeira|ice ?wine|eiswein|late harvest|sauternes|barsac|tokaji|vin santo|beerenauslese|\bdessert\b", re.I)
re_rose = re.compile(r"rosé|rosato|rosado|\brose\b", re.I)

def style(row):
    t = f"{row.title} {row.designation or ''}"
    if row.variety in SPARK or re_spark.search(t): return "Sparkling"
    if row.variety in FORT or re_fort.search(t): return "Fortified & dessert"
    if row.variety in ROSE or re_rose.search(t): return "Rosé"
    return base.get(row.variety, "Unclassified")

if __name__ == "__main__":
    d = pd.read_parquet(sys.argv[1]).dropna(subset=["price", "country"]).copy()
    d["variety"] = d.variety.fillna("(unknown)"); d["designation"] = d.designation.fillna("")
    d["style"] = [style(r) for r in d.itertuples()]
    print(d["style"].value_counts().to_dict())
    print("unclassified share %", round((d["style"] == "Unclassified").mean() * 100, 2))
    # spot checks of overrides
    for v in ["Chardonnay", "Pinot Noir", "Riesling", "Vidal Blanc", "Pinot Meunier", "Verdelho", "Moscato"]:
        print(v, d[d.variety == v]["style"].value_counts().to_dict())
    d["lp"] = np.log(d.price); d["taster"] = d.taster_name.fillna("(none)")
    v = pd.to_numeric(d.title.str.extract(r"\b(19[5-9]\d|20[01]\d)\b")[0], errors="coerce")
    d["vb"] = pd.cut(v, [1949, 2003, 2006, 2008, 2010, 2012, 2013, 2014, 2015, 2017]).astype(object).where(v.notna(), "NV").astype(str)
    A = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d).fit(); d["gA"] = d.points - A.fittedvalues
    B = smf.ols("points ~ lp + I(lp**2) + C(vb)", d).fit(); d["gB"] = d.points - B.fittedvalues
    print("style mean gap A/B:", d.groupby("style")[["gA", "gB"]].mean().round(2).to_dict())
    tiers = [("Up to $15", 0, 15), ("$16–25", 15, 25), ("$26–50", 25, 50), ("$51–100", 50, 100), ("Over $100", 100, 1e6)]
    out = {"counts": d["style"].value_counts().to_dict(), "tiers": []}
    summary = []
    for lab, lo, hi in tiers:
        s = d[(d.price > lo) & (d.price <= hi)]
        for st in ["Red", "White", "Rosé", "Sparkling", "Fortified & dessert"]:
            ss = s[s["style"] == st]; rows = []
            for (c, vv), g in ss.groupby(["country", "variety"]):
                n = len(g)
                if n < 30: continue
                r = {"country": c, "variety": vv, "n": n, "med": float(g.price.median())}
                for k in "AB":
                    m, sd = g["g" + k].mean(), g["g" + k].std(); se = sd / np.sqrt(n)
                    r["m" + k] = round(m, 3); r["lo" + k] = round(m - 1.96 * se, 3); r["hi" + k] = round(m + 1.96 * se, 3)
                tv = g.taster.value_counts(normalize=True); r["critic"] = tv.index[0]; r["cshare"] = round(float(tv.iloc[0]) * 100)
                rows.append(r)
            out["tiers"].append({"tier": lab, "style": st, "wines": len(ss), "groups": rows})
            summary.append((lab, st, len(ss), len(rows)))
    print("\n tier x style: wines, groups(n>=30)")
    for x in summary: print(x)
    for st in ["Red", "White"]:
        t = [x for x in out["tiers"] if x["tier"] == "$16–25" and x["style"] == st][0]
        g = pd.DataFrame(t["groups"]); g["score"] = g[["loA", "loB"]].min(axis=1); g["bad"] = g[["hiA", "hiB"]].max(axis=1)
        a = set(map(tuple, g.sort_values("loA", ascending=False).head(10)[["country", "variety"]].values)); b = set(map(tuple, g.sort_values("loB", ascending=False).head(10)[["country", "variety"]].values))
        print(f"\n{st} $16-25: groups {len(g)}, in both top10 {len(a & b)}")
        print(g.sort_values("score", ascending=False).head(6)[["variety", "country", "n", "mA", "mB", "score", "critic"]].round(2).to_string(index=False))
        print("weakest:", g.sort_values("bad").head(3)[["variety", "country", "bad"]].round(2).values.tolist())
    for st in ["Rosé", "Sparkling", "Fortified & dessert"]:
        allg = [(x["tier"], len(x["groups"])) for x in out["tiers"] if x["style"] == st]
        print(st, allg)
    json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, default=float)
