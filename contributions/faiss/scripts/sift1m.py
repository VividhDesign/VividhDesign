"""Recall@10 and single-thread QPS on full SIFT1M (ground truth from the dataset file)."""
import sys, time, json, numpy as np, h5py, faiss
label = sys.argv[1]
f = h5py.File("/home/user/datasets/sift-128-euclidean.hdf5", "r")
X = np.ascontiguousarray(f["train"][:], dtype=np.float32)
Q = np.ascontiguousarray(f["test"][:], dtype=np.float32)
gt = f["neighbors"][:, :10]
gtd = f["distances"][:, :10]
faiss.omp_set_num_threads(4)
idx = faiss.IndexHNSWFlat(128, 16); idx.hnsw.efConstruction = 200
t = time.time(); idx.add(X); build = time.time() - t
out = {"label": label, "build_s": round(build, 1)}
faiss.omp_set_num_threads(1)
for ef in (16, 32, 64, 128, 256):
    best = None
    for rep in range(2):
        t = time.time(); D, I = idx.search(Q, 10, params=faiss.SearchParametersHNSW(efSearch=ef)); dt = time.time() - t
        best = dt if best is None else min(best, dt)
    # recall with ann-benchmarks' distance-threshold convention: a result counts if within the 10th true distance
    thresh = gtd[:, 9:10] ** 2 * (1 + 1e-3)
    rec_ids = np.mean([len(set(a) & set(b)) / 10 for a, b in zip(I, gt)])
    rec_thr = float(np.mean((D <= thresh).sum(1) / 10))
    out[f"ef{ef}"] = {"recall_ids": round(float(rec_ids), 4), "recall_threshold": round(rec_thr, 4), "qps": round(len(Q) / best)}
print(json.dumps(out), flush=True)
json.dump(out, open(f"/home/user/realdup/sift1m_{label}.json", "w"))
