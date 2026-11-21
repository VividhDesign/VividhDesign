# FAISS: HNSW loses exact-duplicate vectors and traps searches near them — root cause and fix

**Patch:** `contributions/faiss/0001-Keep-exact-duplicate-vectors-reachable-in-HNSW.patch` (on the VividhDesign session
branch). It changes `faiss/impl/HNSW.cpp` (+38, −2) and adds 36 lines of tests to `tests/test_graph_based.py`, and it
applies to FAISS `main` at `c11a75c`.

**Status:** submitted as facebookresearch/faiss#5968 (issue) and facebookresearch/faiss#5969 (PR). The PR has a second
commit that limits the change to exact storage and removes a crash the first commit caused on codecs without
`symmetric_dis`. See `contributions/faiss/PR_COMMENT_v3.md`. Flat-storage graphs, and so every number below, are
unchanged by it.

**Suggested order:**
1. Sign the Meta CLA (https://code.facebook.com/cla).
2. Open the issue below.
3. Open the PR, referencing the issue.

Every number below was measured in this session against two builds of the same `main` checkout, one with the patch
and one without. The scripts are in `contributions/faiss/scripts/`.

---

## Issue

### Title
IndexHNSWFlat: a group of identical vectors larger than 2M becomes partly unreachable and traps searches

### Body
When more identical vectors are added than fit in a level-0 neighbour list (2M), `IndexHNSWFlat` cannot find some of
them. Searches that reach the group can also return fewer than `k` results, even with `efSearch` far above `k`.

```python
import numpy as np, faiss
rs = np.random.RandomState(0)
base = rs.randn(16).astype("float32")
xb = np.vstack([np.tile(base, (200, 1)), rs.randn(800, 16).astype("float32")])  # 200 copies + 800 others
index = faiss.IndexHNSWFlat(16, 32); index.hnsw.efConstruction = 100; index.add(xb)
params = faiss.SearchParametersHNSW(efSearch=1000)
_, I = index.search(base[None], 200, params=params)
print(len(set(I[0].tolist()) & set(range(200))))  # 135: only 135 of the 200 copies are found
_, I = index.search(base[None], 300, params=params)
print((I[0] >= 0).sum())                          # 135 results for k=300, from an index of 1,000 vectors
```

With `M=16`, the same script finds 166 of the 200 copies and returns all 300 results. hnswlib (same M,
`ef_construction=100`, `ef=1000`) finds all 200 copies for both M values.

**Cause.** Copies tie in their distance to the point being added, so they never prune one another in
`shrink_neighbor_list`: the test `Comp::cmp(dist_v1_q, dist_v1_v2)` is strict, and between copies both distances are
0. At level 0, `compute_forward_links_impl` and `add_links_starting_from_impl` keep `nb_neighbors(0)` = 2M targets.
The HNSW paper's Algorithm 1 keeps M at every level and leaves the rest of the list to reverse links. Once the group
outgrows 2M, each new copy's list is therefore all copies. The copies' lists stay full of copies, because reverse
links from later points lose to the tied copies in `merge_reverse_links_impl`. Two consequences follow:
- Few or no edges leave the group, so a search that enters it cannot get out.
- Copies whose reverse links all lose have no incoming edge.

Level-0 lists for the script above:

| | copies with in-degree 0 | edges from a copy to a non-copy |
|---|---|---|
| M=16 | 28 of 200 | 3 |
| M=32 | 2 of 200 | 0 |

**Real data.** I split 13 Python/C++ repositories (FAISS, scikit-learn, pandas, sktime, mteb and others) at blank
lines, as paragraph-aware RAG chunkers do. That gave 423,137 chunks of at least 40 characters. I embedded them with
TF-IDF followed by a 64-dimension SVD, normalised the vectors, and indexed them with
`IndexHNSWFlat(64, 32, METRIC_INNER_PRODUCT)`. Any deterministic embedder gives identical texts identical vectors.
- **Duplicates:** 17.6% of the vectors are exact duplicates (16.7% of the chunks are byte-identical text). 37 groups
  have more than 64 members. The largest is FAISS's own license header (759 copies), followed by scikit-learn's
  (608).
- **Missing:** 1,045 duplicate chunks are not returned by a search for their own vector, even with `k=759` and
  `efSearch=512`.
- **Short:** 645 of the 74,549 searches for a duplicate chunk return fewer than 100 results for `k=100`.

---

## Pull request

### Title
Keep exact-duplicate vectors reachable in HNSW

### Summary
When a point being added has an exact duplicate among its level-0 link targets, it now takes `nb_neighbors(1)` (M)
forward links, as in the paper. The other M slots of its list stay free for links from other points. An exact
duplicate is a target whose distance to the point equals the point's distance to itself. All other points are linked
exactly as before. The rule is a helper, `nb_links_to_add`, used by both link-building paths. The helper reads a copy
of the candidate queue, so the order of tied candidates does not change.

### Evidence

**Duplicates** (`efSearch=1000` unless noted):

| | before | after |
|---|---|---|
| Issue script, M=32: copies found / results for k=300 | 135 / 135 | **200 / 300** |
| Issue script, M=16: copies found / results for k=300 | 166 / 300 | **200 / 300** |
| Issue script, M=16 / M=32: copies with in-degree 0 | 28 / 2 | **0 / 0** |
| Other seed, query 0.05 from the copies, M=16: copies found / results for k=300 | 154 / 154 | **200 / 300** |
| Same, M=32 | 91 / 91 | **200 / 300** |
| 10,000 random 64-d vectors + a group of 50 / 200 / 1,000 copies (M=16): copies found | 48 / 181 / 323 | **50 / 200 / 679** |
| Code corpus: duplicate chunks not returned for their own vector | 1,045 | **37** |
| Code corpus: searches for a duplicate returning fewer than 100 of `k=100` | 645 | **0** |
| Code corpus: 50,000 unique chunks not first for their own vector (`efSearch=128`) | 1,373 | 1,351 |

**No change without duplicates.**
- On the first 200,000 vectors of SIFT and of GloVe-100 (M=16, efConstruction=200), the level-0 neighbour arrays
  are byte-identical before and after, 6,614,768 entries each.
- SIFT1M (M=16, efConstruction=200, 10,000 queries) contains 14,538 pairs of identical vectors, so the new rule
  applies to some points there. Recall@10:

  | efSearch | 16 | 32 | 64 | 128 | 256 |
  |---|---|---|---|---|---|
  | before | 0.8075 | 0.9108 | 0.9675 | 0.9904 | 0.9973 |
  | after | 0.8066 | 0.9101 | 0.9675 | 0.9904 | 0.9973 |

- SIFT1M queries per second, measured in the same process with saved indexes, alternating before and after, median
  of 5 runs. The differences are within run-to-run noise and go both ways:

  | efSearch | 16 | 64 | 128 | 256 |
  |---|---|---|---|---|
  | before | 11,342 | 3,959 | 2,079 | 1,105 |
  | after | 11,050 | 3,926 | 2,165 | 1,110 |

- SIFT1M build time: 147.7 s before, 149.9 s after.

### Alternatives tried

| Change | Copies found, M=16 | Effect on duplicate-free data |
|---|---|---|
| Break distance ties by newest id in `merge_reverse_links_impl` | 37 of 200 (worse) | not measured |
| Cap the share of copies in a list at M | 148 of 200; search trap removed | not measured |
| Use M links for every point at level 0 | 200 of 200 | Recall@10 at fixed `efSearch` drops on 200k vectors: SIFT 0.849→0.839 and GloVe 0.614→0.594 at ef16; 0.996→0.995 and 0.879→0.868 at ef128 |
| **This PR:** use M only for points that have an exact duplicate | 200 of 200 | none: graphs byte-identical |

### Tests
`TestHNSWDuplicates` covers L2 at M=16 and M=32, and inner product at M=16.
- Both tests fail without the change and pass with it.
- With the change, all 54 tests in `tests/test_graph_based.py` and `tests/test_hnsw.py` pass, including
  `test_deterministic_build`.

### Limits
A group much larger than the list still loses copies: with 1,000 copies and M=16, 679 are found (323 before). Groups
of any size would need a structural change, such as one graph node per distinct vector with id aliases. This patch
fixes groups of up to a few times 2M without changing graphs that have no duplicates.
