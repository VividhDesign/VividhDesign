"""Level-0 in-degree of the copies in the issue reproducer's index, for FAISS and (optionally) hnswlib."""
import sys
import numpy as np, faiss
rs = np.random.RandomState(0)
base = rs.randn(16).astype("float32")
xb = np.vstack([np.tile(base, (200, 1)), rs.randn(800, 16).astype("float32")])
is_copy = np.arange(1000) < 200
for M in (16, 32):
    index = faiss.IndexHNSWFlat(16, M); index.hnsw.efConstruction = 100; index.add(xb)
    h = index.hnsw
    nb = faiss.vector_to_array(h.neighbors); off = faiss.vector_to_array(h.offsets).astype(np.int64)
    cum = faiss.vector_to_array(h.cum_nneighbor_per_level).astype(np.int64)
    rows = [nb[off[i] + cum[0]: off[i] + cum[1]] for i in range(1000)]
    rows = [r[r >= 0] for r in rows]
    indeg = np.zeros(1000, int)
    for r in rows:
        np.add.at(indeg, r, 1)
    out = sum(int((~is_copy[r]).sum()) for i, r in enumerate(rows) if is_copy[i])
    print(f"faiss M={M}: copies with in-degree 0: {int((indeg[:200] == 0).sum())}/200; edges from a copy to a non-copy: {out}")
if "hnswlib" in sys.argv:
    import hnswlib
    for M in (16, 32):
        p = hnswlib.Index(space="l2", dim=16); p.init_index(max_elements=1000, M=M, ef_construction=100, random_seed=0)
        p.add_items(xb, np.arange(1000), num_threads=1); p.set_ef(1000)
        labels, _ = p.knn_query(base[None], k=200)
        found = len(set(labels[0].tolist()) & set(range(200)))
        labels, _ = p.knn_query(base[None], k=300)
        print(f"hnswlib M={M}: copies found {found}/200; results for k=300: {len(labels[0])}")
