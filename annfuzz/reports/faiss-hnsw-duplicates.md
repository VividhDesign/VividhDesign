# FAISS: duplicate vectors make IndexHNSWFlat lose copies and trap nearby searches

Target: https://github.com/facebookresearch/faiss/issues (no existing report; the closest is #1097, which is about
`IndexBinaryHNSW` build speed with duplicates, 2020).

## Title
IndexHNSWFlat: identical vectors become unfindable and trap nearby queries (fewer than k results)

## Body (draft)
When many stored vectors are identical, `IndexHNSWFlat` loses some of the copies, and queries near them return fewer
than `k` results, even with `efSearch` equal to the index size.

```python
import numpy as np, faiss
faiss.omp_set_num_threads(1)
rng = np.random.default_rng(0)
base = rng.standard_normal(16).astype(np.float32)
X = np.concatenate([np.tile(base, (200, 1)), rng.standard_normal((800, 16)).astype(np.float32)])
index = faiss.IndexHNSWFlat(16, 16); index.hnsw.efConstruction = 100; index.add(X)
params = faiss.SearchParametersHNSW(efSearch=1000)

D, I = index.search(base[None], 200, params=params)
print(len(set(I[0][(I[0] >= 0) & (I[0] < 200)])))   # 173 to 175 of the 200 copies (exact search: 200)

D, I = index.search(base[None], 300, params=params)
print((I[0] >= 0).sum())                            # 154 results for k=300; the index holds 1,000 vectors

near = base + 0.05 * rng.standard_normal(16).astype(np.float32)
D, I = index.search(near[None], 300, params=params)
print((I[0] >= 0).sum())                            # 154 again, recall 0.51 against IndexFlatL2
```
Without the 200 copies, the same query returns all 300 results. `M` changes the count but not the behaviour (copies
found: 170 at M=16, 195 at M=32, 161 at M=64; efConstruction=200).

What seems to happen, from `HNSW::shrink_neighbor_list` and `add_link_tpl`:
1. A candidate is pruned only if a kept neighbour is strictly closer to it than the base node is
   (`Comp::cmp(dist_v1_q, dist_v1_v2)`). Between identical vectors both distances are 0, so copies never prune one
   another, and a copy's level-0 list fills with other copies.
2. When a new copy back-links into a full list, `add_link_tpl` lets all candidates "fight out" the slots, but every
   distance ties at 0. Which ones survive is decided by the priority queue's order on ties, so a new copy can lose all
   of its reverse links and become unreachable.
3. The copies' lists then point only at one another. A query that enters the cluster has no edge out, so the
   beam visits about 150 nodes and stops, and the search returns fewer than `k` results.

Real corpora hit this: boilerplate text, generated code and repeated chunks often share an embedding exactly. A
workaround is to deduplicate before indexing and keep an alias table. Possible fixes in the library are tie-breaking
that favours the incoming node in `add_link_tpl`, or always keeping at least one link out of a set of exact
duplicates. Happy to help test either.

Found with annfuzz (a cross-library ANN property suite); hnswlib, Voyager, Annoy and Strata keep all 200 copies
reachable on the same data.
