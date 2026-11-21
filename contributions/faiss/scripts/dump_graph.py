import sys, numpy as np, h5py, faiss
faiss.omp_set_num_threads(4)
name, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
f = h5py.File(f"/home/user/datasets/{name}.hdf5", "r")
X = np.ascontiguousarray(f["train"][:n], dtype=np.float32)
metric = faiss.METRIC_INNER_PRODUCT if "angular" in name else faiss.METRIC_L2
if metric == faiss.METRIC_INNER_PRODUCT:
    X /= np.linalg.norm(X, axis=1, keepdims=True)
idx = faiss.IndexHNSWFlat(X.shape[1], 16, metric); idx.hnsw.efConstruction = 200; idx.add(X)
np.save(out, faiss.vector_to_array(idx.hnsw.neighbors))
