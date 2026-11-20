# hnswlib and Voyager: one NaN vector is returned in most unrelated queries

## hnswlib
Target: https://github.com/nmslib/hnswlib/issues. The existing #687 covers NaN and +Inf in **cosine** space only.
This report adds L2 and inner product, plus how far the NaN row spreads into results. Post it as a comment on #687, or
as its own issue linking #687.

### Body (draft)
In `l2` and `ip` spaces too, `add_items` accepts a row containing NaN. That row is then returned in most unrelated
queries' top-10, at distance `nan`:

```python
import numpy as np, hnswlib
rng = np.random.default_rng(0)
Y = rng.standard_normal((1000, 16)).astype(np.float32)
p = hnswlib.Index(space="l2", dim=16); p.init_index(max_elements=1001, M=16, ef_construction=100, random_seed=0)
p.add_items(Y[:500], np.arange(500))
p.add_items(np.full((1, 16), np.nan, np.float32), [10_000])
p.add_items(Y[500:], np.arange(500, 1000))
p.set_ef(64)
labels, dists = p.knn_query(Y, k=10)
print((labels == 10_000).any(1).sum())     # 652 of 1000 top-10 lists contain the NaN row
print(dists[labels == 10_000][:3])         # [nan nan nan]
```
NaN compares false both ways, so neighbour selection treats the row as never worse than any candidate. It ends up
linked from much of the graph and survives every top-k cut. Rejecting non-finite values in `add_items` (and in
queries) would match what FAISS's add path and PyNNDescent already do. It's an O(n·d) check next to the insertion
itself.

## Voyager (Spotify)
Target: https://github.com/spotify/voyager/issues. The earlier #93 ("Handling of missing values (NaN)") was closed
in 2024, but 2.2.4 still accepts NaN.

### Body (draft)
Voyager 2.2.4 accepts vectors containing NaN in every space, and the NaN item is then returned in most unrelated
queries:

```python
import numpy as np, voyager
rng = np.random.default_rng(0)
Y = rng.standard_normal((1000, 16)).astype(np.float32)
v = voyager.Index(voyager.Space.Euclidean, num_dimensions=16, M=16, ef_construction=100, random_seed=0)
v.add_items(Y[:500], list(range(500)))
v.add_items(np.full((1, 16), np.nan, np.float32), [10_000])
v.add_items(Y[500:], list(range(500, 1000)))
ids, dists = v.query(Y, k=10, query_ef=64)
print((np.asarray(ids) == 10_000).any(1).sum())   # 591 of 1000 top-10 lists contain the NaN item
```
Cosine and inner product behave the same (the NaN item is in 72 of 200 top-10 lists). Raising `ValueError` in
`add_items`/`add_item` for non-finite input, in Python and Java, would stop one bad embedding from silently degrading
every search.
