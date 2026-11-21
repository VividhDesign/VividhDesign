"""Compare level-0..L neighbour arrays built with and without the adaptive rule, in one process."""
import os, sys, numpy as np, h5py, faiss
faiss.omp_set_num_threads(4)
name, n = sys.argv[1], int(sys.argv[2])
f = h5py.File(f"/home/user/datasets/{name}.hdf5", "r")
X = np.ascontiguousarray(f["train"][:n], dtype=np.float32)
metric = faiss.METRIC_INNER_PRODUCT if "angular" in name else faiss.METRIC_L2
if metric == faiss.METRIC_INNER_PRODUCT:
    X /= np.linalg.norm(X, axis=1, keepdims=True)
def build():
    idx = faiss.IndexHNSWFlat(X.shape[1], 16, metric); idx.hnsw.efConstruction = 200; idx.add(X)
    return faiss.vector_to_array(idx.hnsw.neighbors), faiss.vector_to_array(idx.hnsw.levels)
os.environ.pop("FAISS_HNSW_ADAPT", None); a, la = build()
os.environ["FAISS_HNSW_ADAPT"] = "1"; b, lb = build()
v = X.view(np.dtype((np.void, 4 * X.shape[1]))).ravel()
_, inv, cnt = np.unique(v, return_inverse=True, return_counts=True)
print(f"{name}[:{n}]: exact-duplicate rows {int((cnt[inv] > 1).sum())}; levels identical {np.array_equal(la, lb)}; "
      f"neighbour arrays identical {np.array_equal(a, b)}; differing entries {int((a != b).sum())} of {len(a)}")
