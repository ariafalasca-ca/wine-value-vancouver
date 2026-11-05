# Data sources and setup

## Included

- `bc_liquor_store_product_price_list_june_2026.csv`: Government of BC product price snapshot; historical CA$ list prices before tax.
- `bcldb_lmr_pre_vs_post_march_2025.csv` and `bcldb_lmr_wine_by_origin_14_quarters.csv`: parsed BCLDB Liquor Market Review tables.
- `iowa_750_items.csv`: item-level 750 mL aggregate from the Iowa spirits extract.
- `deck_data.json` and `report_data.json`: presentation and report data tables.
- `same_bottle_audit_100_judged.csv`: judged sample, with human-check attribution.
- `same_bottle_match_keys_frozen.csv`: reference matched keys for reproduction checks.
- `shelf_check_10_bottles.csv`: product-page observations dated October 30, 2026; not current stock.
- `reproduced/`: numerical audit, matching and sensitivity outputs. `../fig/` contains the corresponding figures.

The packaged Tableau workbook includes the cleaned Excel dataset it uses. It can be explored without the original raw CSV, subject to Tableau Desktop compatibility.

## Required for the Python analysis

Download `winemag-data-130k-v2.csv` from [Kaggle Wine Reviews, zynicide](https://www.kaggle.com/datasets/zynicide/wine-reviews) and place it in `data/raw/`.

Expected SHA-256: `52af2643c8ac29f010f0cc629dfbdda1c74aa0f332d11762af9ef3de4e567ac9`.

The optional raw Iowa files are named `iowa_liquor_sales_*.csv`. If absent, the pipeline uses the included item-level aggregate. The raw Wine Reviews and Iowa extracts are not redistributed as standalone files here; use their source terms when obtaining and reusing them.

Sources: [BC open-data catalogue](https://catalogue.data.gov.bc.ca/), [BCLDB Liquor Market Review](https://www.bcldb.com/publications/liquor-market-review), [Iowa open data](https://data.iowa.gov/).
