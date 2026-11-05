# Reproduce the analysis

Python 3.10+; use an isolated environment and the pinned libraries:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
```

Place the required Wine Reviews CSV in `data/raw/`; see [source setup](../data/README.md). Then run from the repository root:

```sh
python -I code/run_all.py
```

The runner executes nine steps: numerical slide audit, wine matching, exploratory bottle checks, match sensitivity, optional Iowa aggregation, Iowa/BC comparison, origin-price analysis, inflation sensitivity and figure generation. It stops on a failed command and reports input checksum or library-version differences. Outputs are written to `data/reproduced/`.

To rebuild the presentation from the supplied presentation-data file:

```sh
python -I code/build_v7.py
```

The result is `build/Can You Taste the Price.html`. This command rebuilds the presentation artifact; it does not regenerate the original Part A model tables. The remaining Part A scripts are included as analytical source, but the nine-step runner uses the supplied deck data as its presentation reference.

`RAW_WINE`, `BC_LIST`, `LMR_PREPOST`, `IOWA_RAW_GLOB`, `IOWA_ITEMS` and `OUT` can override input/output locations; see `code/paths.py`.

The supplied audit distinguishes 71 numerical checks from three informational records. These checks do not validate every visual element, identify every wine match or establish statistical generalization. Fuzzy matching may change across library versions; the frozen-key comparison reports drift.
