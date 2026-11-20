# PyNNDescent: copies of a vector lose every incoming search-graph edge (cosine, dot) — PR ready

**Patch:** `contributions/pynndescent/0001-Keep-search-graph-edges-to-duplicates-whose-distance.patch` (on the
VividhDesign session branch). Fork https://github.com/lmcinnes/pynndescent, then:
```bash
git clone https://github.com/<you>/pynndescent && cd pynndescent && git checkout -b fix-duplicate-search-graph-edges
```
```bash
git am /path/to/0001-Keep-search-graph-edges-to-duplicates-whose-distance.patch
```
Then push the branch and open the PR. The project asks for an issue for new bugs. Filing one with the description
below and referencing it from the PR is easiest.

## PR title
Keep search-graph edges to duplicates whose distance rounds below zero

## PR description (draft)
With `metric="cosine"` or `"dot"`, a dataset holding many copies of one vector can leave most copies with no
incoming edge in the search graph, so `query` can't return them:

```python
import numpy as np
from pynndescent import NNDescent
rng = np.random.default_rng(1)
base = rng.standard_normal(64).astype(np.float32)
X = np.concatenate([np.tile(base, (200, 1)), rng.standard_normal((1800, 64)).astype(np.float32)])
index = NNDescent(X, metric="cosine", n_neighbors=30, random_state=1, n_jobs=1)
index.prepare()
I, _ = index.query(base[None], k=200, epsilon=0.3)
print(len(set(I[0][I[0] < 200])))     # 74 of the 200 copies; after this change: 200
```

**Cause.** For some vectors, rounding gives `alternative_dot` a distance of about −1.7e-7 between identical
(normalised) rows. Other vectors give exactly 0 or about +2.6e-7. `build_search_graph` takes the union of forward
and reverse edges with `scipy.sparse.maximum` semantics: an edge present in one direction only is compared with an
implicit 0, and zero results are dropped. `prepare()` already raises exact zeros to `FLOAT32_EPS` ("Preserve any
distance 0 points") so they survive. A slightly negative distance isn't caught, so every one-directional edge
between copies was dropped. Whether a given duplicated vector is affected depends only on the sign of that rounding,
which is why it looks random.

**Change.** Raise all non-positive distances to `FLOAT32_EPS` instead of only exact zeros, in `prepare()` and in
`adjacency_matrix_representation`, which has the same guard. No metric produces negative distances by design (I
checked `inner_product`, `dot` and `cosine` on unnormalised data: 0% negative), so this only affects rounding around
duplicates.

**Effect.** Measured over cosine and dot, dimensions 64, 384 and 768, and 4 seeds each (200 copies in 2,000 rows,
`n_neighbors=30`):

| | before | after |
|---|---|---|
| builds with copies lacking any incoming edge | 6 of 24 (71–129 copies each) | 0 of 24 |
| copies found by `query(base, k=200)` | 74–130 of 200 in those builds | 200 of 200 in all 24 |
| self-search hits over all 2,000 rows | 1980–1998 | equal or higher in every build |

**Test.** `test_duplicate_rows_stay_reachable[cosine|dot]`. It picks a vector whose normalised self-distance rounds
below zero on the running platform, because `fastmath` rounding can differ between CPUs, and skips if none does.
It asserts every row has an incoming edge and that all 100 copies are returned. It fails on `master` and passes with
the change. `test_pynndescent_.py` and `test_search_graph.py` pass, 159 tests in total.

Found with annfuzz, a property suite run across several ANN libraries.
