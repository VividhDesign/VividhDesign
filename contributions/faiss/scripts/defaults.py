"""The issue reproducer at FAISS's default efConstruction (40) and a few other settings."""
import numpy as np, faiss
rs = np.random.RandomState(0)
base = rs.randn(16).astype("float32")
xb = np.vstack([np.tile(base, (200, 1)), rs.randn(800, 16).astype("float32")])
params = faiss.SearchParametersHNSW(efSearch=1000)
for M, efc in ((32, 40), (16, 40), (32, 64), (32, 100), (16, 100)):
    index = faiss.IndexHNSWFlat(16, M)
    if efc != 40: index.hnsw.efConstruction = efc
    index.add(xb)
    _, I = index.search(base[None], 300, params=params)
    print(f"M={M} efC={efc}: copies {len(set(I[0].tolist()) & set(range(200)))}/200, results {(I[0] >= 0).sum()}")
