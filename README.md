# Can You Taste the Price?

**Wine value signals from critic reviews, checked against British Columbia shelf prices.**

A UBC Sauder BAIT 518 team project asking which country–grape groups earn higher critic scores than their historical US prices predict, and whether those groups are available within a Vancouver shopper's **CA$25 before-tax budget**.

![Country–grape rankings by points above price](assets/value-ranking.png)

## Findings

| Historical group, US$16–25 tier | Reviews | Cautious points-above-price estimate | BC category listings | Median BC list price |
|---|---:|---:|---:|---:|
| Portuguese red | 535 | +1.38 | 23 | CA$18.99 |
| Australian Shiraz | 166 | +0.98 | 57 | CA$22.99 |

The cautious estimate is the lower of two models' 95% lower confidence limits. It describes a historical group-level score signal, not a promise about a particular bottle or a shopper's taste. BC listing counts and prices refer to the **June 2026 snapshot**, not current stock.

Three findings shape the decision:

- A simple share-scoring-90+ ranking largely follows price: correlation **0.69** across 178 eligible groups with median US prices of US$25 or less. The project instead uses points above a price-based benchmark.
- Portuguese red and Australian Shiraz combine positive historical signals with lower BC category prices. Other high-scoring groups, including German Riesling and Muscadet, tend to sit in higher BC price bands.
- Among **451 matched wines**, origin-specific BC/US list-price ratios differ. The overall median ratio is **1.56 CA$/US$**; currencies, time periods, product selection and distribution effects matter. This is not a same-currency markup estimate.

## Explore

- **Interactive presentation:** download the repository and open [Can You Taste the Price.html](Can%20You%20Taste%20the%20Price.html) in a browser. It works offline, offers presentation mode and includes an interactive shelf guide. GitHub's file view displays HTML source rather than the running page.
- **Tableau:** [Wine Value.twbx](tableau/Wine%20Value.twbx) is a packaged supporting workbook with its cleaned Excel data included. Built by Willance Zheng, it illustrates the relationship between price and the share of wines scoring 90+; the full points-above-price analysis is in the Python pipeline and presentation.
- **Analysis:** [method and limitations](docs/METHODS.md), [sources and data](data/README.md), [reproduction instructions](docs/REPRODUCE.md).

![BC price check for shortlisted groups](assets/bc-price-check.png)

## My contribution and team credits

**Arianna Falasca:** proposed the topic, title and initial plan with ChatGPT support, prepared the first Part A deck with Muse, and participated in the team presentation. The final implementation and analysis were team work; the table below identifies ownership.

| Team member | Documented contribution |
|---|---|
| Arianna Falasca | Topic and initial plan; first Part A deck; presentation |
| Willance Zheng | Metric development, analysis, interactive presentation, supporting Tableau workbook, animation, script and final report |
| Taha Saeed | Data cleaning and cleaning documentation |
| Max Chen | Part A video editing and presentation materials |
| Nanalin Sangthong | Part B video editing and team discussions |

ChatGPT and Muse supported Arianna's initial work. Claude supported Taha's cleaning and Willance's analysis, coding, design and writing; Codex supported analytical reviews. The Tableau workbook is credited to Willance and documented as built without AI. [Contribution and AI use](docs/AI-USE.md) explains these roles.

## Data and reproduction

The analysis starts with **129,971 Wine Enthusiast reviews**, removes **9,983 exact duplicates**, and uses **111,538 reviews** with price and country information. Included files contain the BC price snapshot, supporting market tables, item-level Iowa aggregates, match audits and analytical outputs. The Tableau package includes its cleaned workbook data.

The original Wine Reviews CSV is obtained from the linked source and placed in `data/raw/` for numerical reproduction. The optional full Iowa extract can be replaced by the supplied item-level aggregate. See [data setup](data/README.md).

## Limits

Critic scores measure critic assessments, not consumer taste or sales. Historical US suggested retail prices and June 2026 BC list prices serve different purposes and time periods. Critic and country effects are difficult to separate; the two-model comparison checks sensitivity without identifying a true critic effect. Bottle matching pools vintages and involves judgment. Bottle-level checks reuse the model-fitting reviews and are exploratory, not out-of-sample validation.

This is an independent educational team project. No measured commercial impact, deployment or causal effect is claimed. Source data and third-party assets remain subject to their original terms.
