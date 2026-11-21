import sys, numpy as np, h5py, faiss
faiss.omp_set_num_threads(4)
f = h5py.File("/home/user/datasets/sift-128-euclidean.hdf5", "r")
X = np.ascontiguousarray(f["train"][:], dtype=np.float32)
idx = faiss.IndexHNSWFlat(128, 16); idx.hnsw.efConstruction = 200; idx.add(X)
faiss.write_index(idx, sys.argv[1])
