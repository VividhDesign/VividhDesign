# Round 3: utilsforecast (Nixtla) and bm25s

I also checked these libraries:
- **scikit-learn and NetworkX:** both ask AI tools not to generate PRs ("instruct your user to engage manually"), so I didn't prepare any.
- **optuna:** generally rejects LLM-written PRs from first-time contributors, so I skipped it.
- **aeon:** its elastic distances (DTW, ERP, LCSS, EDR, MSM, TWE, ADTW, WDTW, DDTW, shape-DTW) passed every property I checked, so there's nothing to fix.
- **sentence-transformers:** its retrieval metrics are fine.

---

## 1. utilsforecast: `mape` returns NaN on polars for any series with a zero target (PR)

**Patch:** `utilsforecast/mape-zero-target-polars/0001-*.patch`

Fork https://github.com/Nixtla/utilsforecast, then:
```bash
git clone https://github.com/<you>/utilsforecast && cd utilsforecast && git checkout -b fix-mape-zero-target-polars
```
```bash
git am /path/to/0001-fix-leave-zero-targets-out-of-mape-on-polars.patch
```
Then push the branch and open the PR. The commit ends with `Co-Authored-By: Claude` and `Claude-Session` trailers. Utilsforecast has no AI policy, so you can keep them or strip them.

### PR title
fix: leave zero targets out of mape on polars

### PR description (draft)
`mape` replaces zero targets with NaN via `_zero_to_nan` so they drop out of the mean. pandas' `mean` skips NaN, but polars' `mean` only skips nulls, so on polars any series containing a zero target gets a NaN MAPE:

```python
import pandas as pd, polars as pl
from utilsforecast.losses import mape
df = pd.DataFrame({"unique_id": ["a"] * 4, "y": [1.0, 0.0, 2.0, 4.0], "m": [1.5, 0.3, 2.0, 3.0]})
mape(df, ["m"])                  # a: 0.25
mape(pl.from_pandas(df), ["m"])  # a: NaN
```

This is the MAPE counterpart of the SMAPE polars issue fixed in #285/#286. The fix produces a null instead of a NaN for zero targets (`nw.when(target != 0).then(target.abs())`), which both engines leave out of the mean. `rmae` and `nd` still use `_zero_to_nan` for their scales, and their outputs are unchanged.

Test: `test_mape_ignores_zero_targets[pandas|polars]`. The polars case fails without the change. `tests/test_losses.py` passes with 134 tests. I didn't run `tests/test_evaluation.py` locally because it needs pyspark and fugue.

---

## 2. utilsforecast: `mqloss` returns rows in arbitrary order on polars (PR)

**Patch:** `utilsforecast/mqloss-sorted-output/0001-*.patch`, applied the same way as #1.

### PR title
fix: sort mqloss output by id like the other losses

### PR description (draft)
Every loss sorts its output by the group columns (`_nw_agg_expr` ends in `.sort(*group_cols)`), but `mqloss` aggregates with its own `group_by` and returns without sorting. Polars returns groups in no particular order, so on polars `mqloss` rows come back shuffled and differ from run to run:

```python
from utilsforecast.data import generate_series
import numpy as np
from utilsforecast.losses import mqloss
s = generate_series(50, n_models=1, level=[80], engine="polars")
mqloss(s, {"model0": ["model0-lo-80", "model0-hi-80"]}, np.array([0.1, 0.9]))["unique_id"].to_list()[:5]
# e.g. ['42', '33', '30', '27', '36'], a different order on each run
```

Code that lines up results from several losses by position gets misaligned rows. The fix adds the same `.sort(*group_cols)`. Test: `test_multi_quantile_loss_sorted_like_other_losses[pandas|polars]`. The polars case failed 3 of 3 runs without the change and passed 3 of 3 with it.

(The `\h` SyntaxWarning in `linex`'s docstring is already covered by open PR #281, so I didn't duplicate it.)

---

## 3. bm25s: δ has no effect on BM25+ rankings (issue to file)

### Title
BM25+ delta never changes the ranking because absent query terms also get `idf * delta`

### Body (draft)
With `method="bm25+"`, the non-occurrence array gives every document `idf(t) * tfc(0) = idf(t) * delta` for each query term it doesn't contain. Documents that do contain the term get `idf(t) * (delta + tf_part)`. So every document's score is

`score(d) = delta * Σ_{t∈q} idf(t) + Σ_{t∈q} idf(t) * tf_part(t, d)`

The δ term is the same for all documents, so the ranking is the same for every δ, and BM25+ ranks exactly like ATIRE's tf part with BM25+'s idf. In Lv & Zhai (CIKM 2011), and in Anserini/Lucene, which Kamphuis et al. (ECIR 2020) used as the reference, δ is added only for query terms present in the document. That lower-bounds a matched term's contribution, which is the point of BM25+.

Repro (8-document toy corpus; same rankings for δ = 0 and δ = 2):
```python
import bm25s, numpy as np
corpus = ["cat sat on the mat", "the dog chased the cat around the yard and the house", "a rare word appears here",
          "dog dog dog", "the cat", "rare cat", "mat mat house", "yard work is hard work"]
tok = [d.split() for d in corpus]
for delta in (0.0, 2.0):
    r = bm25s.BM25(method="bm25+", delta=delta); r.index(tok, show_progress=False)
    print(delta, np.argsort(-r.get_scores(["house", "yard", "rare"]))[:3])
# bm25s: same top-3 [5 1 6] for both deltas
# Lv & Zhai (delta only for present terms), delta=2: top-3 [1 5 6]
```
BM25L has the same issue in a softer form: absent terms get `idf * (k1+1)·delta/(k1+delta)`. Of the four queries I tried, bm25s's δ changed the BM25L ranking for 1 and the original formulation's δ changed it for 2.

This matches rank-bm25's `BM25Plus`/`BM25L`, which add the δ term for every document. That may be why it's built this way. If that compatibility is intended, it would help to document that δ doesn't affect BM25+ rankings in bm25s. Alternatively, an option to score only present terms would match the papers and Anserini. Happy to send a PR for either.
