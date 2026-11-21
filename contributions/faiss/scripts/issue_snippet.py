import numpy as np, faiss
rs = np.random.RandomState(0)
base = rs.randn(16).astype("float32")
xb = np.vstack([np.tile(base, (200, 1)), rs.randn(800, 16).astype("float32")])
for M in (16, 32):
    index = faiss.IndexHNSWFlat(16, M); index.hnsw.efConstruction = 100; index.add(xb)
    params = faiss.SearchParametersHNSW(efSearch=1000)
    _, I = index.search(base[None], 200, params=params)
    found = len(set(I[0].tolist()) & set(range(200)))
    _, I = index.search(base[None], 300, params=params)
    print(f"M={M}: copies found {found}/200; results for k=300: {(I[0] >= 0).sum()}")
