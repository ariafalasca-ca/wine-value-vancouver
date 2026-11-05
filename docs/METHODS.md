# Method and interpretation

## Two datasets, two purposes

Wine Enthusiast reviews via Kaggle establish the historical US price/score relationship. BC Liquor Stores' June 2026 price snapshot tests local price bands and availability by category. A category listing is not verified current store stock; US and BC prices are not substituted for one another in the score model.

After exact deduplication, 119,988 reviews remain. Excluding missing price or country leaves 111,538 for analysis. Scores are published from 80 points upward; review prices are historical US suggested retail and the corpus has no review dates. Missing prices are not random across origins.

## Points above price

Each review's residual is its score minus a benchmark fitted as a quadratic in log price. Both models include vintage groups; one includes critic fixed effects and one omits them. Groups are country plus grape within a US price tier and wine type, with at least 30 reviews. Red, white and other shelf sections are ranked separately.

For each group, the cautious estimate is the lower of the two models' 95% lower confidence limits for the mean residual. This sensitivity rule reduces reliance on one treatment of critic effects; it does not identify or bound the true critic effect.

## BC checks and matching

The primary matched sample contains 451 wines after excluding doubtful pairs: 444 rule matches and seven manual matches. The broader 459-pair set and stricter 439-pair set support sensitivity comparisons. Matching requires compatible producer, wine, grape, style, tier and named appellation; vintages may differ. Review pooling preserves appellation with documented aliases.

Among matched Portuguese reds, 9 of 11 have a positive historical bottle-level signal; among single-variety Australian Shiraz, 8 of 9 do. The bottle measure is the lower of two mean residuals and is different from the group confidence-bound measure. The matching exercise reuses reviews fitted in the original models and has a median of two reviews per matched wine; it is exploratory.

The 100-pair rule-match audit was AI-judged and partly checked by the analysis lead. Agreement with AI judgments is not independently established matching precision. Manual Portuguese matches represent a substantial share of the small Portugal sample.

## Cross-market evidence

BC CA$ list price divided by historical US$ suggested retail is a numerical cross-currency ratio, not a real markup or a causal measure. Price histories, distribution costs, taxes and customer preferences are not isolated.

Iowa is an additional comparison of 47 matched spirits, not a wine benchmark. The Liquor Market Review measure is wholesale revenue per litre, including product-mix effects; it is not a shelf-price index or an estimate of tariff effects.

## Scope of the decision

The project supports historical shelf-guide hypotheses within the observed sample. It does not establish shopper taste, current availability, predictive performance, causal effects or realized business benefits.
