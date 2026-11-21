Keep search-graph edges to duplicates whose distance rounds below zero

---

With `metric="cosine"` or `"dot"`, a dataset holding many copies of one vector can leave most copies with no incoming edge in the search graph, so `query` can't return them:

```python
import numpy as np
from pynndescent import NNDescent
rng = np.random.default_rng(1)
base = rng.standard_normal(64).astype(np.float32)
X = np.concatenate([np.tile(base, (200, 1)), rng.standard_normal((1800, 64)).astype(np.float32)])
index = NNDescent(X, metric="cosine", n_neighbors=30, random_state=1, n_jobs=1)
index.prepare()
I, _ = index.query(base[None], k=200, epsilon=0.3)
print(len(set(I[0][I[0] < 200])))     # 74 of the 200 copies on master; 200 with this change
```

## Cause

For some vectors, rounding gives `alternative_dot` a distance of about −1.7e-7 between identical (normalised) rows. Other vectors give exactly 0 or about +2.6e-7.

`prepare()` builds the search graph as the union of forward and reverse edges, with `scipy.sparse.maximum` semantics. An edge present in one direction only is compared with an implicit 0, and a result of zero is dropped. `prepare()` already raises exact zeros to `FLOAT32_EPS` ("Preserve any distance 0 points") so that they survive. A slightly negative distance escapes that guard, so every one-directional edge between such copies was dropped.

Whether a duplicated vector is affected depends only on the sign of that rounding, which is why the failure looks random.

This is the same rounding as in #283. That PR clamps the corrected distances that users get back. This change covers the uncorrected alternative distances that the search graph is built from.

## Change

Raise all non-positive distances to `FLOAT32_EPS` instead of only exact zeros. This applies in `prepare()` and in `adjacency_matrix_representation`, which has the same guard.

No metric produces negative distances by design. I checked `inner_product`, `dot` and `cosine` on unnormalised data and found no negative distances, so this only affects rounding around duplicates.

## Effect

Measured over cosine and dot, dimensions 64, 384 and 768, and 4 seeds each, with 200 copies in 2,000 rows and `n_neighbors=30`:

| | master | this change |
|---|---|---|
| Builds where some copies have no incoming edge | 6 of 24 (71–129 copies each) | 0 of 24 |
| Copies found by `query(base, k=200)` | 74–130 of 200 in those builds | 200 of 200 in all 24 |
| Self-search hits over all 2,000 rows | 1980–1998 | equal or higher in every build |

## Tests

New test: `test_duplicate_rows_stay_reachable[cosine|dot]`.
- It picks a vector whose normalised self-distance rounds below zero on the running platform, because `fastmath` rounding can differ between CPUs. If no vector does, it skips.
- It asserts that every row has an incoming edge and that all 100 copies are returned.
- It fails on master and passes with this change.

The full suite passes: `pytest pynndescent/tests` gives 389 passed and 1 skipped.

I found this with annfuzz, a property-based suite I ran across several ANN libraries. The investigation and the change were done with Claude Code, an AI coding assistant.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_017uaXZrSYSh1iMaFrDMbm4o
