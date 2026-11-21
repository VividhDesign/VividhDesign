"""Structure of the level-0 HNSW graph that faiss.IndexHNSWFlat builds around a group of identical vectors."""

import sys

import numpy as np

import faiss

faiss.omp_set_num_threads(1)
rng = np.random.default_rng(0)
base = rng.standard_normal(16).astype(np.float32)
order = sys.argv[1] if len(sys.argv) > 1 else "copies-first"
copies = np.tile(base, (200, 1))
others = rng.standard_normal((800, 16)).astype(np.float32)
X = np.concatenate([copies, others]) if order == "copies-first" else np.concatenate([others, copies])
is_copy = np.all(X == base, axis=1)

index = faiss.IndexHNSWFlat(16, 16)
index.hnsw.efConstruction = 100
index.add(X)
h = index.hnsw
neighbors = faiss.vector_to_array(h.neighbors)
offsets = faiss.vector_to_array(h.offsets).astype(np.int64)
cum = faiss.vector_to_array(h.cum_nneighbor_per_level).astype(np.int64)
n = len(X)
level0 = [neighbors[offsets[i] + cum[0]: offsets[i] + cum[1]] for i in range(n)]
level0 = [row[row >= 0] for row in level0]
indeg = np.zeros(n, int)
for row in level0:
    np.add.at(indeg, row, 1)
copy_ids = np.where(is_copy)[0]
out_edges_from_cluster = sum(int((~is_copy[row]).sum()) for i, row in enumerate(level0) if is_copy[i])
print(f"{order}: copies with in-degree 0 at level 0: {int((indeg[copy_ids] == 0).sum())}/200; "
      f"mean share of a copy's neighbours that are copies: {np.mean([is_copy[row].mean() for i, row in enumerate(level0) if is_copy[i] and len(row)]):.2f}; "
      f"edges from a copy to a non-copy: {out_edges_from_cluster}; non-copies with in-degree 0: {int((indeg[~is_copy] == 0).sum())}")
