"""Time two saved SIFT1M graphs alternately in one process: search code is identical, only the graphs differ."""
import time, json, numpy as np, h5py, faiss
faiss.omp_set_num_threads(1)
f = h5py.File("/home/user/datasets/sift-128-euclidean.hdf5", "r")
Q = np.ascontiguousarray(f["test"][:], dtype=np.float32); gt = f["neighbors"][:, :10]
idx = {k: faiss.read_index(f"/home/user/realdup/sift1m_{k}.index") for k in ("base", "fix")}
res = {}
for ef in (16, 64, 128, 256):
    p = faiss.SearchParametersHNSW(efSearch=ef)
    times = {"base": [], "fix": []}
    for rep in range(5):
        for k in (("base", "fix") if rep % 2 == 0 else ("fix", "base")):
            t = time.perf_counter(); D, I = idx[k].search(Q, 10, params=p); times[k].append(time.perf_counter() - t)
            if rep == 0:
                res.setdefault(k, {})[f"ef{ef}_recall"] = round(float(np.mean([len(set(a) & set(b)) / 10 for a, b in zip(I, gt)])), 4)
    for k in times:
        res[k][f"ef{ef}_qps_median"] = round(len(Q) / float(np.median(times[k])))
print(json.dumps(res, indent=0))
