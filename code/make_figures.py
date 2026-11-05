"""Report figures in the deck's visual system (Archivo / Lato / Plex Mono, cream-burgundy-gold). Run: python3 -I make_figures.py"""
import sys, json, pathlib, numpy as np, pandas as pd, matplotlib, glob
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); from paths import OUT, FIG, FONTS
matplotlib.use("Agg"); import matplotlib.pyplot as plt; from matplotlib import font_manager as fm
for f in glob.glob(str(FONTS / "*.ttf")): fm.fontManager.addfont(f)
WINE, GOLD, INK, INK2, INK3, RULE, GRID, DATA, BG, PANEL = "#6b1d2b", "#a57d33", "#2a1b1d", "#5a4a4b", "#8a7b78", "#e2d6c4", "#eadfcf", "#b9ab9a", "#ffffff", "#fffaf1"
plt.rcParams.update({"font.family": "Lato", "font.size": 10, "axes.edgecolor": RULE, "axes.labelcolor": INK2, "xtick.color": INK3, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.titlelocation": "left", "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlecolor": INK, "figure.facecolor": BG, "axes.facecolor": BG})
def title(ax, t, sub=None):
    ax.set_title(t, fontfamily="Archivo", fontweight="bold", pad=18 if sub else 8)
    if sub: ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=8.5, color=INK3)
V = json.load(open(OUT / "validate_summary.json")); SB = json.load(open(OUT / "same_bottle_summary.json")); IO = json.load(open(OUT / "iowa_bc_summary.json"))

# ---- Figure E: evidence chain (two rows of three)
fig, ax = plt.subplots(figsize=(7.4, 4.6), dpi=220); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
steps = [("THE DECISION", "A Vancouver shopper with about\nCA$25 and two minutes", "same 90 points:\nUS$22 or US$45"),
         ("THE OBVIOUS RULE FAILS", "'Share scoring 90+' mostly\nranks by price, so we dropped it", "r = 0.69 with price\nMoschofilero +2.4, ranked 72nd"),
         ("THE METRIC", "Points above price: score minus\nthe typical score at that price", "$20 bottle: typical 87.5,\nso a 90 is +2.5"),
         ("THE CATCH", "One critic per country, so every\ngroup is scored two ways", "Austria +1.6 without,\n+0.3 with critic adjustment"),
         ("THE SHELF CHECK", "US data ranks the groups;\nthe BC price list checks the shelf", "Portuguese red CA$18.99\nAustralian Shiraz CA$22.99"),
         ("THE ANSWER", "Under CA$25, reach for a Portuguese\nred or an Australian Shiraz", "+1.4 and +1.0 points,\ncautious estimate")]
cols = [0.17, 0.50, 0.83]; rows = [0.72, 0.30]
for i, (eb, what, num) in enumerate(steps):
    x = cols[i % 3]; yy = rows[i // 3]; hot = i in (0, 2, 5)
    ax.scatter([x], [yy + 0.13], s=520, color=WINE if hot else PANEL, edgecolors=WINE, linewidths=1.4, zorder=3)
    ax.text(x, yy + 0.13, str(i + 1), ha="center", va="center", fontsize=9.5, color=PANEL if hot else WINE, fontfamily="Archivo", fontweight="bold", zorder=4)
    if i % 3 < 2: ax.annotate("", xy=(cols[i % 3 + 1] - 0.045, yy + 0.13), xytext=(x + 0.045, yy + 0.13), arrowprops=dict(arrowstyle="-|>", color=RULE, lw=1.2))
    ax.text(x, yy + 0.055, eb, ha="center", va="top", fontsize=7, color=GOLD, fontfamily="IBM Plex Mono")
    ax.text(x, yy + 0.005, what.replace("$", "\\$"), ha="center", va="top", fontsize=8.4, color=INK, linespacing=1.3, fontweight="bold" if hot else "normal")
    ax.text(x, yy - 0.12, num.replace("$", "\\$"), ha="center", va="top", fontsize=7.8, color=WINE, fontfamily="IBM Plex Mono", linespacing=1.35)
ax.annotate("", xy=(cols[0], rows[1] + 0.19), xytext=(cols[2], rows[0] - 0.22), arrowprops=dict(arrowstyle="-|>", color=RULE, lw=1.2, connectionstyle="angle3,angleA=0,angleB=90"))
ax.text(0, 0.995, "How a Kaggle file became two bottle names", fontfamily="Archivo", fontweight="bold", fontsize=12.5, color=INK, va="top")
ax.text(0, 0.935, "Each step was forced by the one before it. Filled circles are the three decisions that set the project's direction.", fontsize=8.4, color=INK3, va="top")
plt.savefig(FIG / "figE_chain.png", bbox_inches="tight"); plt.close()

# ---- Figure A: same-bottle price ratio by origin (main origin evidence; no reference country)
t = pd.read_csv(OUT / "same_bottle_by_origin.csv").set_index("country"); t = t[t.n >= 8].sort_values("median_ratio")
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=220); y = np.arange(len(t))
ax.barh(y, t.median_ratio, color=[WINE if c in ("Portugal", "Australia") else DATA for c in t.index], height=0.62); ax.hlines(y, t.q1, t.q3, color=GOLD, lw=2.2)
for i, (c, r) in enumerate(t.iterrows()): ax.text(r.q3 + 0.06, i, f"{r.median_ratio:.2f}   n = {int(r.n)}", va="center", fontsize=8.2, color=INK2, fontfamily="IBM Plex Mono")
ax.set_yticks(y); ax.set_yticklabels(t.index); ax.set_xlim(0, 3.5)
ax.axvline(SB["overall_median_ratio"], color=INK3, ls=(0, (4, 3)), lw=1); ax.text(SB["overall_median_ratio"] + 0.03, len(t) - 0.55, f"all {SB['matched_total']} bottles: {SB['overall_median_ratio']:.2f}", fontsize=8, color=INK3, fontfamily="IBM Plex Mono")
ax.set_xlabel("BC list price (CA\\$) ÷ US\\$ suggested retail, same wine")
title(ax, "The same wine costs 1.2 to 1.8 times its US list price in BC, depending on origin", f"{SB['matched_total']} bottles ({SB['rule_matches']} by rule, {SB['manual_matches']} by hand); bar = median, gold = middle half; wine colour = origins of our two picks; 8+ bottles")
plt.tight_layout(); plt.savefig(FIG / "figA_same_bottle_ratio.png"); plt.close()

# ---- Figure B (appendix): the regression with France as reference, on US and on BC prices
t2 = pd.read_csv(OUT / "same_bottle_by_origin.csv").set_index("country"); t2 = t2[(t2.n >= 8)][["US_price_pct_below_France", "BC_price_pct_below_France"]].dropna().sort_values("BC_price_pct_below_France")
fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=220); y = np.arange(len(t2))
ax.hlines(y, t2.US_price_pct_below_France, t2.BC_price_pct_below_France, color=GRID, lw=5)
ax.scatter(t2.US_price_pct_below_France, y, color=DATA, s=40, zorder=3, label="US list prices")
ax.scatter(t2.BC_price_pct_below_France, y, color=WINE, s=40, zorder=3, label="BC list prices (June 2026)")
ax.set_yticks(y); ax.set_yticklabels(t2.index); ax.axvline(0, color=INK3, lw=1)
ax.set_xlabel("% below France at the same score and grape (same bottles)"); ax.legend(frameon=False, fontsize=8, loc="lower right")
title(ax, "Relative to France, every origin is cheaper in BC than in US list prices", "France itself is the dearest origin in BC, so part of each shift is a France effect")
plt.tight_layout(); plt.savefig(FIG / "figB_origin_us_vs_bc.png"); plt.close()

# ---- Figure C: Iowa by category
r = pd.read_csv(OUT / "iowa_bc_same_sku.csv")
cat = r.groupby("category").agg(n=("ratio_cad_per_usd", "size"), med=("ratio_cad_per_usd", "median")).reset_index()
ren = {"100% Agave Tequila": "Tequila (100% agave)", "Mixto Tequila": "Tequila (mixto)", "Imported Cordials & Liqueur": "Imported liqueurs", "Straight Bourbon Whiskies": "Bourbon", "Canadian Whiskies": "Canadian whisky", "Imported Dry Gins": "Gin (imported)", "American Vodkas": "Vodka (US)", "Imported Vodkas": "Vodka (imported)", "Tennessee Whiskies": "Tennessee whiskey", "Cream Liqueurs": "Cream liqueurs"}
cat["cat"] = cat.category.str.title().map(lambda x: ren.get(x, x))
cat = cat[cat.n >= 2].sort_values("med")
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=220); y = np.arange(len(cat))
ax.barh(y, cat.med, color=[GOLD if "Canadian" in c else WINE for c in cat.cat], height=0.62)
for i, rr in enumerate(cat.itertuples()): ax.text(rr.med + 0.03, i, f"{rr.med:.2f}   n = {rr.n}", va="center", fontsize=8.2, color=INK2, fontfamily="IBM Plex Mono")
ax.set_yticks(y); ax.set_yticklabels(cat.cat); ax.set_xlim(0, 3.0); ax.axvline(IO["fx_usd_cad"], color=INK3, ls=(0, (4, 3)), lw=1); ax.text(IO["fx_usd_cad"] + 0.03, len(cat) - 0.5, "USD/CAD ≈ 1.40", fontsize=8, color=INK3, fontfamily="IBM Plex Mono")
ax.set_xlabel("BC price (CA\\$) ÷ Iowa state price (US\\$), category median")
title(ax, f"47 identical spirits: BC shelf ≈ {IO['median_ratio']:.2f} × Iowa's price to retailers", "Categories with 2+ bottles; gold = Canadian whisky, the domestic product")
plt.tight_layout(); plt.savefig(FIG / "figC_iowa_bc.png"); plt.close()

# ---- Figure D: historical signals among matched BC bottles, Portuguese red and single-variety Australian Shiraz, shared scale
m = pd.read_csv(OUT / "same_bottle_matched.csv"); m["lm"] = np.minimum(m.gA, m.gB)
pr = m[(m.bc_class == "Portugal Red Wine") & (m.bc_price <= 60)].sort_values("bc_price")
sh = m[(m.country == "Australia") & m.bc_name.str.contains("SHIRAZ") & (m.we_variety == "Shiraz") & (m.bc_price <= 60)].sort_values("bc_price")
def short(n):
    n = n.replace("SHIRAZ- ", "SHIRAZ - ")
    head, _, tail = n.partition(" - ")
    name = (tail or head).title().replace("Bin 128 Coonawarra 2019", "Bin 128 Coonawarra").replace("Bin 28 Kalimna 2022", "Bin 28 Kalimna").replace("Red Blend 2022", "Red Blend").replace(" 2021", "").replace(" 2020", "").replace("Jose Maria Da Fonseca Periquita", "J. M. da Fonseca Periquita")
    return name[:30]
fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.9), dpi=220, sharex=True, gridspec_kw={"height_ratios": [len(pr), len(sh)]})
for ax, df, lab in [(axes[0], pr, f"Portuguese red ({len(pr)} matched bottles up to CA\\$60)"), (axes[1], sh, f"Australian Shiraz, single variety ({len(sh)} matched bottles up to CA\\$60)")]:
    y = np.arange(len(df)); ax.barh(y, df.lm, color=[WINE if v > 0 else DATA for v in df.lm], height=0.62); ax.axvline(0, color=INK3, lw=1)
    ax.set_yticks(y); ax.set_yticklabels([f"{short(n)}   CA\\${p:.2f}" for n, p in zip(df.bc_name, df.bc_price)], fontsize=7.8)
    for i, (v, k) in enumerate(zip(df.lm, df.n_reviews)):
        ax.text(max(v, 0) + 0.1, i, f"{v:+.1f}  ({k} review{'s' if k > 1 else ''})", va="center", ha="left", fontsize=7.4, color=INK2, fontfamily="IBM Plex Mono")
    ax.set_xlim(-3.0, 6.2); ax.set_xticks([-2, 0, 2, 4]); ax.set_title(lab, fontfamily="Archivo", fontweight="bold", fontsize=9.5, loc="left")
axes[1].set_xlabel("historical points above price (lower of the two mean residuals)")
fig.suptitle("Matched BC bottles in BC price order: most carry a positive historical score signal", x=0.01, y=0.995, ha="left", fontfamily="Archivo", fontweight="bold", fontsize=11, color=INK)
fig.text(0.01, 0.948, "Grey = below the typical score for its US price. Exploratory: residuals come from models fitted on all reviews, these wines included.", fontsize=8, color=INK3)
plt.tight_layout(rect=(0, 0, 1, 0.955)); fig.subplots_adjust(top=0.875); plt.savefig(FIG / "figD_shelf_validation.png"); plt.close()
print("figures ok", FIG)
