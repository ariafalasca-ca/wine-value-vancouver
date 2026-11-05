"""Same-bottle matching: Wine Enthusiast reviews (same producer and wine, any vintage) to BC Liquor Stores products (June 2026).
Run from code/: python3 -I same_bottle.py
Writes to data/reproduced/: same_bottle_candidates.csv (every candidate pair); same_bottle_matched_all.csv (rule matches + Portugal
matches made by hand, each with its reason); same_bottle_matched.csv (the primary set: all minus the pairs in code/match_exclusions.csv);
same_bottle_audit_sample.csv (the fixed, judged audit sample and whether each pair is still matched); same_bottle_by_origin.csv;
same_bottle_summary.json; match_key_drift.csv only if the matched pairs differ from data/same_bottle_match_keys_frozen.csv.
Deterministic: ties are broken by SKU and review title with a stable sort. Tested versions are pinned in requirements.txt.
Rules: block by country; the BC name must contain the producer's distinctive words; colour, grape or appellation, tier words
(Reserva, Riserva, Premier Cru) and any named cuvee must agree; a word in the BC name that the review never uses rejects the pair.
"""
import warnings; warnings.filterwarnings("ignore", message="This pattern is interpreted")
import re, json, sys, pathlib, numpy as np, pandas as pd
from unidecode import unidecode
from rapidfuzz import fuzz
import statsmodels.formula.api as smf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from style_map import style
from paths import DATA, RAW_WINE, BC_LIST, MANUAL_PT, OUT, need
RAW = need(RAW_WINE); BC = need(BC_LIST)
CTRY = {"Portugal": "PORTUGAL", "Australia": "AUSTRALIA", "France": "FRANCE", "Germany": "GERMANY", "Chile": "CHILE", "Argentina": "ARGENTINA",
        "Spain": "SPAIN", "Italy": "ITALY", "New Zealand": "NEW ZEALAND", "South Africa": "SOUTH AFRICA", "US": "UNITED STATES OF AMERICA", "Austria": "AUSTRIA", "Greece": "GREECE"}
STOP = set("QUINTA DOMAINE DOMAINES CHATEAU CH BODEGAS BODEGA ESTATE ESTATES WINERY WINERIES VINEYARD VINEYARDS CELLARS CELLAR VINA VINAS VINOS VINHOS CASA CANTINA CANTINE AZIENDA AGRICOLA TENUTA TENUTE FAMILY FAMILIA WEINGUT MAISON LES LA LE DE DU DES DEL DELLA DI DA DO DOS DAS EL LOS LAS AND & THE OF CO WINES WINE VINTNERS".split())
norm = lambda s: re.sub(r"[^A-Z0-9 ]+", " ", unidecode(str(s)).upper()).strip()
toks = lambda s: [t for t in norm(s).split() if t]

raw = pd.read_csv(RAW, index_col=0).drop_duplicates()
d = raw.dropna(subset=["price", "country"]).copy()
d["variety"] = d.variety.fillna(""); d["designation"] = d.designation.fillna(""); d["region_1"] = d.region_1.fillna("")
d["lp"] = np.log(d.price); d["taster"] = d.taster_name.fillna("(none)"); d["region_2"] = d.region_2.fillna(""); d["province"] = d.province.fillna("")
d["style"] = [style(r) for r in d.itertuples()]
v = pd.to_numeric(d.title.str.extract(r"\b(19[5-9]\d|20[01]\d)\b")[0], errors="coerce")
d["vb"] = pd.cut(v, [1949, 2003, 2006, 2008, 2010, 2012, 2013, 2014, 2015, 2017]).astype(object).where(v.notna(), "NV").astype(str)
A = smf.ols("points ~ lp + I(lp**2) + C(taster) + C(vb)", d).fit(); d["gA"] = d.points - A.fittedvalues
B = smf.ols("points ~ lp + I(lp**2) + C(vb)", d).fit(); d["gB"] = d.points - B.fittedvalues

b = pd.read_csv(BC)
w = b[(b.ITEM_CATEGORY_NAME == "Wine") & (b.PRODUCT_LITRES_PER_CONTAINER == 0.75) & (b.PRD_CONTAINER_PER_SELL_UNIT == 1)].copy()
w = w[~w.ITEM_CLASS_NAME.str.contains(r"^Port Wine|Sherry|Fortified|Sparkling|Champagne|Dessert|Icewine", case=False, na=False)]  # still wines, like the deck
w["N"] = w.PRODUCT_LONG_NAME.map(norm)

GENERIC = set("RESERVA RESERVE RESERVAS GRAN GRAND GRANDE CRU PREMIER ESTATE VINTAGE CLASSIC CLASSICO SELECTION SELECCION SPECIAL EDITION OLD VINES VIEILLES VIGNES RED WHITE ROUGE BLANC BLANCO TINTO BRANCO ROSE ROSADO ROSATO DRY SEC BRUT ORGANIC VEGAN SINGLE VINEYARD BLEND CUVEE".split())
VAR_ALIAS = {"Red Blend": ["RED", "ROUGE", "TINTO", "BLEND"], "White Blend": ["WHITE", "BLANC", "BLANCO", "BRANCO", "BLEND"], "Portuguese Red": ["RED", "TINTO", "DOURO", "DAO", "ALENTEJANO", "ALENTEJO", "LISBOA", "TEJO", "BAIRRADA", "SETUBAL"], "Portuguese White": ["WHITE", "BRANCO", "VINHO VERDE", "DOURO", "DAO", "ALENTEJANO", "LISBOA"],
             "Bordeaux-style Red Blend": ["BORDEAUX", "MEDOC", "PAUILLAC", "MARGAUX", "ST", "SAINT", "POMEROL", "EMILION", "RED", "ROUGE"], "Rhône-style Red Blend": ["RHONE", "CHATEAUNEUF", "GIGONDAS", "VACQUEYRAS", "COTES"], "Sparkling Blend": ["BRUT"], "Shiraz": ["SHIRAZ", "SYRAH"], "Syrah": ["SYRAH", "SHIRAZ"], "Pinot Grigio": ["PINOT GRIGIO", "PINOT GRIS"], "Pinot Gris": ["PINOT GRIS", "PINOT GRIGIO"], "Melon": ["MUSCADET"], "Sangiovese Grosso": ["BRUNELLO"], "Nebbiolo": ["BAROLO", "BARBARESCO", "NEBBIOLO"], "Sangiovese": ["CHIANTI", "SANGIOVESE", "TOSCANA"], "Tempranillo": ["RIOJA", "RIBERA", "TEMPRANILLO"], "Garnacha": ["GARNACHA", "GRENACHE"], "Corvina, Rondinella, Molinara": ["AMARONE", "VALPOLICELLA", "RIPASSO"], "Glera": ["PROSECCO"], "Champagne Blend": ["CHAMPAGNE"], "Chardonnay": ["CHARDONNAY", "CHABLIS", "MEURSAULT", "MONTRACHET", "MACON", "POUILLY FUISSE", "BOURGOGNE BLANC"], "Pinot Noir": ["PINOT NOIR", "BOURGOGNE", "GEVREY", "NUITS", "POMMARD", "VOLNAY", "BEAUNE", "CHAMBOLLE", "VOSNE", "MOREY", "SPATBURGUNDER"], "Gamay": ["BEAUJOLAIS", "MORGON", "FLEURIE", "MOULIN", "GAMAY"], "Chenin Blanc": ["CHENIN", "VOUVRAY"], "Sauvignon Blanc": ["SAUVIGNON BLANC", "SANCERRE", "POUILLY FUME", "SAUV BLANC"], "Cabernet Sauvignon": ["CABERNET SAUVIGNON", "CAB SAUV"], "Riesling": ["RIESLING"], "Malbec": ["MALBEC", "CAHORS"], "Zinfandel": ["ZINFANDEL", "ZIN"], "Merlot": ["MERLOT"], "Carmenère": ["CARMENERE"], "Grüner Veltliner": ["GRUNER"], "Albariño": ["ALBARINO"], "Verdejo": ["VERDEJO", "RUEDA"], "Montepulciano": ["MONTEPULCIANO"], "Primitivo": ["PRIMITIVO"], "Nero d'Avola": ["NERO D AVOLA"], "Barbera": ["BARBERA"], "Dolcetto": ["DOLCETTO"], "Vermentino": ["VERMENTINO"], "Gewürztraminer": ["GEWURZTRAMINER"], "Viognier": ["VIOGNIER"], "Torrontés": ["TORRONTES"], "Pinotage": ["PINOTAGE"], "Cabernet Franc": ["CABERNET FRANC", "CHINON", "BOURGUEIL"], "Petite Sirah": ["PETITE SIRAH"], "Moscato": ["MOSCATO"], "Rosé": ["ROSE", "ROSADO", "ROSATO"]}
TIER = set("GRAN GRANDE GRAND RESERVA RESERVE RISERVA SUPERIORE SUPERIOR PREMIER CRU SELECCION SELECTION SPECIAL LIMITED VIEILLES OLD VINES SIGNATURE CLASSICO CLASSIC".split())
ALLOW = set("WINE WINES RED WHITE ROSE ROUGE BLANC BLANCO BRANCO TINTO ROSADO ROSATO VALLEY VALLEYS VINEYARD VINEYARDS ESTATE ESTATES ORGANIC VEGAN REPACK COUNTY HILLS HILL COAST COASTAL SOUTH NORTH EAST WEST CENTRAL EXTRA BRUT DRY SEC MAGNUM BOTTLE DOMAINE DOMAINES CHATEAU BODEGAS BODEGA CANTINA TENUTA QUINTA WEINGUT MAISON CELLAR CELLARS WINERY FAMILY VINTNERS BLEND BLENDS VINHO VERDE DELLE VENEZIE".split())
# ---- appellation: a wine's identity includes its appellation (region_1; province when region_1 is blank).
# app_norm() removes accents and punctuation, spells out St/Ste, and merges spelling variants and renamed appellations
# listed in APP_ALIAS (checked by hand against the reviews; hierarchy is NOT merged: Napa Valley is not Oakville).
APP_ALIAS = {"PIEDMONT": "PIEMONTE", "BAROSSA": "BAROSSA VALLEY", "VALLE DE UCO": "UCO VALLEY", "VENEZIE": "DELLE VENEZIE",
             "TERRE SICILIANE": "SICILIA", "SONOMA COUNTY MONTEREY COUNTY SANTA BARBARA COUNTY": "MONTEREY SANTA BARBARA SONOMA",
             "BURGUNDY": "BOURGOGNE", "COLUMBIA VALLEY WA": "COLUMBIA VALLEY", "COLUMBIA VALLEY OR": "COLUMBIA VALLEY", "MOULIS EN MEDOC": "MOULIS"}
def app_norm(s):
    a = " ".join(re.sub(r"\bSTE\b", "SAINTE", re.sub(r"\bST\b", "SAINT", norm(s))).split())
    return APP_ALIAS.get(a, a)
def bc_apps(name, apps):
    """Appellations named in the BC prefix (the part before ' - '), longest first, without overlaps."""
    pre = app_norm(name.split(" - ")[0]) if " - " in name else ""
    found = []
    for a in apps:
        if re.search(r"\b" + re.escape(a) + r"\b", pre):
            found.append(a); pre = re.sub(r"\b" + re.escape(a) + r"\b", " ", pre)
    return set(found)
def var_ok(variety, region, n):
    al = [norm(a) for a in (VAR_ALIAS.get(variety) or [norm(variety)]) if a]
    generic = ("Blend" in variety) or variety.startswith("Portuguese") or variety in ("Rosé", "Rosato", "Rosado", "Red", "White")
    if generic: al += [t for t in toks(region) if len(t) > 3]  # a regional blend is named by its appellation, a grape by its grape
    return any(re.search(r"\b" + re.escape(a) + r"\b", n) for a in al if a)
d["app"] = [app_norm(r1 if r1 else pv) for r1, pv in zip(d.region_1, d.province)]
# named cuvees whose reviews carry a broader or narrower label for the same wine across vintages (checked by hand against every review):
# for these, the reviews are pooled across the appellation labels; every other wine is pooled within one appellation only
CUVEE_POOL = {("Trivento", "Golden Reserve"), ("Noble Vines", "242"), ("Zuccardi", "Serie A"), ("Belle Glos", "Clark & Telephone Vineyard"),
              ("Ornellaia", "Le Serre Nuove"), ("Penfolds", "Bin 28 Kalimna"), ("Doña Paula", "Estate"), ("Sartarelli", "Tralivio"),
              ("Santa Julia", "Reserva"), ("Bucci", "Villa Bucci Riserva")}
d["app_key"] = [("ANY LABEL: " + "; ".join(sorted(set(d.app[(d.winery == w) & (d.designation == ds)])))) if (w, ds) in CUVEE_POOL else a
                for w, ds, a in zip(d.winery, d.designation, d.app)]
pairs = []
for ctry, bcc in CTRY.items():
    wc = w[w.PRODUCT_COUNTRY_ORIGIN_NAME == bcc]
    if not len(wc): continue
    dc = d[d.country == ctry]
    APPS = sorted({app_norm(a) for a in dc.region_1.unique() if len(app_norm(a)) >= 4}, key=len, reverse=True)  # this country's appellations (region_1), longest first
    for winery, g in dc.groupby("winery"):
        wt = [t for t in toks(winery) if t not in STOP and len(t) > 2]
        if not wt or (len(wt) == 1 and len(wt[0]) < 4): continue
        phrase = r"\b" + r"\s+".join(re.escape(t) for t in wt) + r"\b"
        cand = wc[wc.N.str.contains(phrase, regex=True)]
        if not len(cand): continue
        prod = lambda n: n.split(" - ")[-1].strip() if " - " in n else n  # BC names read REGION/GRAPE - PRODUCER WINE VINTAGE
        for _, p in cand.iterrows():
            rest = " ".join(t for t in toks(p.PRODUCT_LONG_NAME) if t not in wt and not re.fullmatch(r"(19|20)\d\d", t))
            best = None
            bclass = "Red" if "Red" in p.ITEM_CLASS_NAME else "White" if "White" in p.ITEM_CLASS_NAME else "Rosé" if "Rose" in p.ITEM_CLASS_NAME else None
            btoks = set(toks(p.PRODUCT_LONG_NAME)); bapps = bc_apps(p.PRODUCT_LONG_NAME, APPS)
            for _, r in g.iterrows():
                if bclass and r.style in ("Red", "White", "Rosé") and r.style != bclass: continue  # colour must agree
                dt = [t for t in toks(r.designation) if t not in STOP and t not in GENERIC and t not in wt and len(t) > 2]
                des_ok = (not dt) or all(re.search(r"\b" + re.escape(t) + r"\b", p.N) for t in dt)
                if not des_ok: continue
                # the producer segment must start with the winery unless a named cuvée ties the two (second wines read "Le X de Château Y")
                if not dt and not re.match(phrase, prod(unidecode(p.PRODUCT_LONG_NAME).upper().replace("(REPACK)", "").strip())): continue
                if not var_ok(r.variety, r.region_1, p.N): continue  # grape or appellation must agree
                # an appellation named in the BC prefix must be the review's: same appellation, or named in the review's designation, or the
                # same appellation plus tier words the BC name also carries (VERDICCHIO ... + CLASSICO); a named cuvee identifies the wine on its own
                if bapps and not dt and not (r.app in bapps or any(a in app_norm(r.designation) for a in bapps)
                                             or any(r.app.startswith(a + " ") and all(t in p.N.split() for t in r.app[len(a):].split()) for a in bapps)): continue
                wetoks = set(toks(f"{r.designation} {r.variety} {r.region_1} {r.region_2} {r.province} {winery}"))
                if (btoks & TIER) != (wetoks & TIER): continue  # Reserva vs Gran Reserva, Riserva, Premier Cru: tier words must agree
                extra = [t for t in btoks - wetoks - GENERIC - TIER - ALLOW - set(wt) if len(t) >= 4 and not t.isdigit() and not any(t in a for a in sum(VAR_ALIAS.values(), []))]
                if extra: continue  # a word in the BC name that the review never uses: a different cuvée, vineyard or line
                name = " ".join(toks(f"{r.designation} {r.variety} {r.region_1}"))
                sc = fuzz.token_set_ratio(rest, name) if name else 0
                sc += 15 if dt else 0  # a named cuvée that matches is stronger evidence than a bare grape
                if best is None or sc > best[0]: best = (sc, r, bool(dt))
            if best is None: continue
            pairs.append({"country": ctry, "bc_name": p.PRODUCT_LONG_NAME, "bc_class": p.ITEM_CLASS_NAME, "bc_price": p.PRODUCT_PRICE, "sku": p.PRODUCT_SKU_NO,
                          "winery": winery, "we_title": best[1].title, "we_variety": best[1].variety, "we_designation": best[1].designation, "we_app": best[1].app_key, "we_price": best[1].price,
                          "we_points": best[1].points, "name_score": best[0], "named": best[2], "n_reviews_winery": len(g)})
P = pd.DataFrame(pairs)
# keep one BC product per WE title and vice versa, best name score first
# deterministic: ties on name score are broken by SKU and review title, with a stable sort, so the result does not depend on row order
P = P.sort_values(["name_score", "sku", "we_title"], ascending=[False, True, True], kind="mergesort").drop_duplicates("sku").drop_duplicates("we_title")
P["accept"] = P.named | (P.name_score >= 70)  # a named cuvee that passed every rule, or a close name match
P.to_csv(OUT / "same_bottle_candidates.csv", index=False)
acc = P[P.accept].sort_values(["sku", "we_title"], kind="mergesort").reset_index(drop=True)
# every review of the matched wine across vintages: same winery + designation (cuvee, tier) + variety (grape, colour) + appellation
key = ["winery", "we_designation", "we_variety", "we_app"]
agg = d.assign(we_designation=d.designation, we_variety=d.variety, we_app=d.app_key).groupby(key).agg(we_med=("price", "median"), we_pts=("points", "mean"), gA=("gA", "mean"), gB=("gB", "mean"), n_reviews=("price", "size")).reset_index()
acc = acc.merge(agg, on=key, how="left")
# diagnostic: the earlier key (winery, designation, variety) pooled reviews from other appellations for some wines
old = d.groupby(["winery", "designation", "variety"]).agg(n_old=("price", "size"), med_old=("price", "median")).reset_index().rename(columns={"designation": "we_designation", "variety": "we_variety"})
acc = acc.merge(old, on=["winery", "we_designation", "we_variety"], how="left")
IDFIX = {"rule_matches_pooling_other_appellations_under_old_key": int((acc.n_old > acc.n_reviews).sum()),
         "of_which_median_us_price_changed_over_10pct": int(((acc.n_old > acc.n_reviews) & ((acc.we_med / acc.med_old - 1).abs() > 0.10)).sum()),
         "median_ratio_rule_matches_new_key": round(float((acc.bc_price / acc.we_med).median()), 3), "median_ratio_rule_matches_old_key": round(float((acc.bc_price / acc.med_old).median()), 3)}
acc["match_source"] = "rule"; acc["match_reason"] = "rule match, name score " + acc.name_score.round(0).astype(int).astype(str)
acc["we_titles"] = acc.we_title
# audit sample: a fixed set of 100 rule matches, drawn on October 30 (random_state 7 over the 457 rule matches of the rules before the
# appellation check) and judged pair by pair in data/same_bottle_audit_100_judged.csv. It is kept fixed so the judgements stay valid;
# this step reports which audited pairs the current rules still accept.
J = pd.read_csv(DATA / "same_bottle_audit_100_judged.csv"); ak = set(zip(acc.bc_name, acc.we_title))
J["still_matched"] = [(a, b) in ak for a, b in zip(J.bc_name, J.we_title)]
J[["sample_id", "country", "bc_name", "we_title", "judgement", "still_matched"]].to_csv(OUT / "same_bottle_audit_sample.csv", index=False)
print("audit sample: still matched", int(J.still_matched.sum()), "of", len(J), "| dropped by the current rules:",
      J[~J.still_matched][["sample_id", "judgement"]].values.tolist())

# ---- Portugal: few producer names overlap, so eight further matches were made by hand (code/manual_portugal.csv records the reason)
d["TT"] = d.title.map(lambda x: unidecode(str(x)))
man = pd.read_csv(MANUAL_PT); rows = []
for _, r in man.iterrows():
    hit = d[(d.country == "Portugal") & d.TT.str.contains(r.we_title_regex, regex=True)]
    if isinstance(r.we_exclude_regex, str) and r.we_exclude_regex: hit = hit[~hit.TT.str.contains(r.we_exclude_regex, regex=True)]
    if not len(hit): raise SystemExit(f"manual match found no review: {r.bc_name}")
    rows.append({"country": "Portugal", "bc_name": r.bc_name, "bc_class": r.bc_class, "bc_price": r.bc_price, "sku": r.sku, "winery": hit.winery.mode().iloc[0], "we_title": hit.title.iloc[0],
                 "we_titles": " | ".join(sorted(set(hit.title))), "we_variety": hit.variety.mode().iloc[0], "we_designation": hit.designation.mode().iloc[0] if len(hit.designation.mode()) else "", "we_app": "; ".join(sorted(set(hit.app))),
                 "we_med": float(hit.price.median()), "we_pts": float(hit.points.mean()), "gA": float(hit.gA.mean()), "gB": float(hit.gB.mean()), "n_reviews": int(len(hit)),
                 "match_source": "manual", "match_reason": r.reason})
MA = pd.concat([acc, pd.DataFrame(rows)], ignore_index=True)
MA["ratio"] = MA.bc_price / MA.we_med
cols = ["country", "bc_name", "bc_class", "bc_price", "sku", "winery", "we_title", "we_titles", "we_variety", "we_designation", "we_app", "we_med", "we_pts", "gA", "gB", "n_reviews", "ratio", "match_source", "match_reason", "name_score"]
MA[cols].to_csv(OUT / "same_bottle_matched_all.csv", index=False)

# ---- frozen keys: the audited run's matched pairs; a different library version can break ties differently, so report any drift
keys = MA[["bc_name", "we_title", "match_source"]].sort_values(["bc_name", "we_title"]).reset_index(drop=True)
FROZEN = DATA / "same_bottle_match_keys_frozen.csv"
if FROZEN.exists():
    fz = pd.read_csv(FROZEN); kn, kf = set(zip(keys.bc_name, keys.we_title)), set(zip(fz.bc_name, fz.we_title))
    drift = len(kn ^ kf)
    if drift:
        pd.DataFrame([{"bc_name": a, "we_title": b, "in": "this run only"} for a, b in kn - kf] + [{"bc_name": a, "we_title": b, "in": "frozen set only"} for a, b in kf - kn]).to_csv(OUT / "match_key_drift.csv", index=False)
        print(f"WARNING: {drift} matched pairs differ from the frozen audited set (see data/reproduced/match_key_drift.csv). Check library versions against requirements.txt.")
    else:
        print("Matched pairs identical to the frozen audited set:", len(kf))
else:
    drift = None

# ---- primary analysis: drop the pairs judged different or uncertain (code/match_exclusions.csv records each and who found it)
EX = pd.read_csv(MANUAL_PT.parent / "match_exclusions.csv")
exk = set(zip(EX.bc_name, EX.we_title)); isx = MA.apply(lambda r: (r.bc_name, r.we_title) in exk, axis=1)
missing = exk - set(zip(MA.bc_name, MA.we_title))
if missing: print("Note: exclusions not present in this run:", sorted(missing))
M = MA[~isx].reset_index(drop=True)
M[cols].to_csv(OUT / "same_bottle_matched.csv", index=False)
print(f"all matches {len(MA)} (rule {int((MA.match_source == 'rule').sum())}, by hand {int((MA.match_source == 'manual').sum())}); excluded {int(isx.sum())}; primary {len(M)}")

# ---- same-bottle price ratio by origin (no reference country needed)
overall = float(M.ratio.median())
bo = M.groupby("country").agg(n=("ratio", "size"), median_ratio=("ratio", "median"), q1=("ratio", lambda x: x.quantile(.25)), q3=("ratio", lambda x: x.quantile(.75)), we_med=("we_med", "median"), bc_med=("bc_price", "median")).reset_index()
bo["vs_all_median_pct"] = (bo.median_ratio / overall - 1) * 100
# ---- the same regression on US list prices and on BC list prices, France as the reference (supplementary)
m = M.dropna(subset=["we_med", "we_pts"]).copy(); m["lbc"] = np.log(m.bc_price); m["lus"] = np.log(m.we_med)
tv = m.we_variety.value_counts(); m["var2"] = np.where(m.we_variety.isin(tv[tv >= 15].index), m.we_variety, "(other)")
base = "France"
def prem(model, c): return round((1 - np.exp(model.params.get(f"C(country, Treatment('{base}'))[T.{c}]", 0.0))) * 100, 1)
mus = smf.ols(f"lus ~ we_pts + C(var2) + C(country, Treatment('{base}'))", m).fit(cov_type="HC1")
mbc = smf.ols(f"lbc ~ we_pts + C(var2) + C(country, Treatment('{base}'))", m).fit(cov_type="HC1")
bo["US_price_pct_below_France"] = bo.country.map(lambda c: prem(mus, c) if c != base else np.nan)
bo["BC_price_pct_below_France"] = bo.country.map(lambda c: prem(mbc, c) if c != base else np.nan)
bo.round(2).sort_values("median_ratio").to_csv(OUT / "same_bottle_by_origin.csv", index=False)
S = {"candidates": int(len(P)), "rule_matches_all": int(len(acc)), "manual_matches_all": len(rows), "matched_all": int(len(MA)), "excluded": int(isx.sum()), "frozen_key_drift": drift,
     "rule_matches": int((M.match_source == "rule").sum()), "manual_matches": int((M.match_source == "manual").sum()), "matched_total": int(len(M)), "overall_median_ratio": round(overall, 2),
     "reviews_per_bottle": {"median": float(M.n_reviews.median()), "share_le_2": round(float((M.n_reviews <= 2).mean()) * 100), "max": int(M.n_reviews.max())},
     "matched_price_medians": {"we_usd": float(M.we_med.median()), "bc_cad": float(M.bc_price.median())},
     "identity_fix": IDFIX, "n_regression": int(len(m)), "pct_per_point_matched": {"US": round((np.exp(mus.params.we_pts) - 1) * 100, 1), "BC": round((np.exp(mbc.params.we_pts) - 1) * 100, 1)},
     "by_origin": bo.round(2).astype(object).where(bo.round(2).notna(), None).to_dict("records")}
json.dump(S, open(OUT / "same_bottle_summary.json", "w"), indent=1, default=float, allow_nan=False)
print(bo.round(2).sort_values("median_ratio").to_string(index=False)); print({k: v for k, v in S.items() if k != "by_origin"})
