"""Same-SKU spirits benchmark: Iowa state 'bottle retail' (the monopoly's price to Class E retailers, US$) vs BC Liquor Stores shelf price (CA$), 750 mL, 2026.
Run: python3 -I iowa_bc_benchmark.py -> iowa_bc_same_sku.csv, iowa_bc_summary.json. Pairs were curated by hand from the top-selling Iowa items."""
import sys, pathlib, pandas as pd, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); from paths import BC_LIST, IOWA_ITEMS, OUT, need
FX = 1.40  # USD/CAD, about the 2026 average and the June 2026 level (1.38 to 1.42)
b = pd.read_csv(need(BC_LIST)); sp = b[(b.ITEM_CATEGORY_NAME == "Spirits") & (b.PRODUCT_LITRES_PER_CONTAINER == 0.75) & (b.PRD_CONTAINER_PER_SELL_UNIT == 1)]
io = pd.read_csv(need(IOWA_ITEMS))
PAIRS = [("TITOS HANDMADE VODKA", "FIFTH GENERATION - TITO'S HANDMADE"), ("CROWN ROYAL", "CROWN ROYAL"), ("CROWN ROYAL REGAL APPLE", "CROWN ROYAL - APPLE"), ("CROWN ROYAL BLACK", "CROWN ROYAL - BLACK"), ("CROWN ROYAL VANILLA", "CROWN ROYAL - VANILLA"),
         ("BUFFALO TRACE BOURBON", "BUFFALO TRACE KENTUCKY BOURBON"), ("CAPTAIN MORGAN ORIGINAL SPICED", "CAPTAIN MORGAN - SPICED"), ("FIREBALL CINNAMON WHISKEY", "FIREBALL"), ("ABSOLUT SWEDISH VODKA 80PRF", "ABSOLUT"), ("JACK DANIELS OLD #7 BLACK LABEL", "(REPACK)JACK DANIEL'S - OLD 7"),
         ("PATRON SILVER", "PATRON - SILVER"), ("JAMESON", "JAMESON - IRISH"), ("MALIBU COCONUT", "MALIBU - COCONUT"), ("JOSE CUERVO ESPECIAL SILVER", "JOSE CUERVO - ESPECIAL SILVER"), ("JOSE CUERVO ESPECIAL REPOSADO", "JOSE CUERVO - ESPECIAL GOLD"), ("JIM BEAM", "JIM BEAM - KENTUCKY BOURBON"),
         ("MAKERS MARK", "MAKER'S MARK - KENTUCKY BOURBON"), ("SMIRNOFF 80PRF", "SMIRNOFF - RED LABEL"), ("HENNESSY VS", "HENNESSY - VERY SPECIAL"), ("JAGERMEISTER LIQUEUR", "JAGERMEISTER"), ("WOODFORD RESERVE", "WOODFORD RESERVE - DISTILLERS SELECT"), ("BACARDI SUPERIOR", "BACARDI - SUPERIOR WHITE"),
         ("DON JULIO REPOSADO", "DON JULIO - REPOSADO"), ("DON JULIO BLANCO", "DON JULIO - BLANCO"), ("BULLEIT BOURBON", "BULLEIT - FRONTIER BOURBON"), ("GREY GOOSE", "GREY GOOSE"), ("KETEL ONE", "NOLET - KETEL ONE"), ("TEREMANA BLANCO TEQUILA", "TEREMANA - TEQUILA BLANCO"), ("ESPOLON BLANCO", "ESPOLON - BLANCO"),
         ("TANQUERAY GIN", "TANQUERAY - LONDON DRY"), ("ELIJAH CRAIG", "ELIJAH CRAIG - SMALL BATCH"), ("LICOR 43", "LICOR 43"), ("BAILEYS ORIGINAL IRISH CREAM", "BAILEYS - ORIGINAL IRISH CREAM"), ("COINTREAU LIQUEUR", "COINTREAU"), ("CASAMIGOS BLANCO", "CASAMIGOS - BLANCO"), ("KAHLUA COFFEE", "KAHLUA"),
         ("JACK DANIELS TENNESSEE HONEY", "JACK DANIEL'S - TENNESSEE HONEY"), ("ST GERMAIN", "ELDERFLOWER LIQUEUR - ST GERMAIN"), ("CAZADORES REPOSADO", "CAZADORES - REPOSADO"), ("OLMECA ALTOS PLATA", "OLMECA - ALTOS PLATA"), ("BOMBAY SAPPHIRE GIN", "BOMBAY SAPPHIRE - LONDON DRY"), ("HENDRICKS GIN", "HENDRICK'S GIN"),
         ("GLENLIVET 12YR", "GLENLIVET - 12 YEAR OLD"), ("GENTLEMAN JACK", "JACK DANIEL'S - GENTLEMAN JACK RARE TENNESSEE"), ("JIM BEAM BLACK", "(REPACK)JIM BEAM - BLACK EXTRA AGED"), ("RUMCHATA", "RUMCHATA CREAM"), ("FOUR ROSES BOURBON", "FOUR ROSES - 80 PROOF")]
rows = []
for ides, bname in PAIRS:
    ii = io[io.im_desc.str.upper() == ides]; bb = sp[sp.PRODUCT_LONG_NAME.str.strip() == bname]
    if not len(ii) or not len(bb): print("missing", ides, bname, len(ii), len(bb)); continue
    i = ii.sort_values("bottles", ascending=False).iloc[0]; p = bb.PRODUCT_PRICE.min()
    rows.append({"item": ides, "category": i.category_name, "iowa_state_retail_usd": i.retail_med, "bc_name": bname, "bc_price_cad": p, "ratio_cad_per_usd": round(p / i.retail_med, 2), "iowa_bottles_2026": int(i.bottles)})
R = pd.DataFrame(rows).sort_values("ratio_cad_per_usd"); R.to_csv(OUT / "iowa_bc_same_sku.csv", index=False)
S = {"n": int(len(R)), "median_ratio": float(R.ratio_cad_per_usd.median()), "q1": float(R.ratio_cad_per_usd.quantile(.25)), "q3": float(R.ratio_cad_per_usd.quantile(.75)), "min": float(R.ratio_cad_per_usd.min()), "max": float(R.ratio_cad_per_usd.max()),
     "by_category": R.groupby("category").ratio_cad_per_usd.median().round(2).to_dict(), "by_category_n": R.groupby("category").size().to_dict(), "iowa_markup_cost_to_retail": 1.5,
     "fx_usd_cad": FX, "median_ratio_constant_currency": round(float(R.ratio_cad_per_usd.median()) / FX, 2),
     "bc_shelf_vs_us_shelf_if_retail_markup_10_to_25pct": [round(float(R.ratio_cad_per_usd.median()) / FX / 1.25, 2), round(float(R.ratio_cad_per_usd.median()) / FX / 1.10, 2)]}
json.dump(S, open(OUT / "iowa_bc_summary.json", "w"), indent=1)
pd.set_option("display.width", 230); print(R.to_string(index=False)); print(json.dumps(S, indent=1))
