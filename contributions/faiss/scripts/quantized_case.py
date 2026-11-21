"""One case of quantized.py per process, since an exception inside HNSW's OpenMP region aborts the process."""
import sys, numpy as np, faiss
rs = np.random.RandomState(0)
base = rs.randn(16).astype("float32")
xb = np.vstack([np.tile(base, (200, 1)), rs.randn(800, 16).astype("float32")])
case, n = sys.argv[1], int(sys.argv[2])
qt = faiss.ScalarQuantizer
index = faiss.IndexHNSWPQ(16, 8, 32) if case == "PQ8" else faiss.IndexHNSWSQ(16, getattr(qt, case), 32)
index.hnsw.efConstruction = 100
index.train(xb); index.add(xb[:n] if n == 1000 else xb[200:200 + n])
if n == 1000:
    _, I = index.search(base[None], 300, params=faiss.SearchParametersHNSW(efSearch=1000))
    print(f"{case}: copies in top 300: {len(set(I[0].tolist()) & set(range(200)))}/200; results: {(I[0] >= 0).sum()}")
else:
    print(f"{case}, add {n} distinct vectors: ok")
