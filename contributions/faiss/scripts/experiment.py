"""Duplicate-vector behaviour of faiss.IndexHNSWFlat, run identically against two FAISS builds.

usage: python experiment.py LABEL [synthetic] [sweep] [corpus] [regression]
"""

import json
import sys
import time

import numpy as np

import faiss

faiss.omp_set_num_threads(4)
label = sys.argv[1]
parts = set(sys.argv[2:]) or {"synthetic", "sweep", "corpus", "regression"}
out = {"label": label, "faiss": faiss.__version__}


def hnsw(d, M, metric=faiss.METRIC_L2, efc=200):
    index = faiss.IndexHNSWFlat(d, M, metric)
    index.hnsw.efConstruction = efc
    return index


def search(index, Q, k, ef):
    return index.search(np.ascontiguousarray(Q, dtype=np.float32), k, params=faiss.SearchParametersHNSW(efSearch=ef))


if "synthetic" in parts:
    rng = np.random.default_rng(0)
    base = rng.standard_normal(16).astype(np.float32)
    X = np.concatenate([np.tile(base, (200, 1)), rng.standard_normal((800, 16)).astype(np.float32)])
    res = {}
    for M in (16, 32):
        faiss.omp_set_num_threads(1)
        index = hnsw(16, M, efc=100)
        index.add(X)
        faiss.omp_set_num_threads(4)
        _, I = search(index, base[None], 200, 1000)
        found = len(set(I[0][(I[0] >= 0) & (I[0] < 200)].tolist()))
        near = (base + 0.05 * rng.standard_normal(16)).astype(np.float32)
        _, I = search(index, near[None], 300, 1000)
        res[f"M{M}"] = {"copies_found_of_200": found, "results_for_k300_near": int((I[0] >= 0).sum())}
    out["synthetic"] = res
    print(label, "synthetic", res, flush=True)

if "sweep" in parts:
    res = {}
    for group in (10, 50, 200, 1000):
        rng = np.random.default_rng(group)
        base = rng.standard_normal(64).astype(np.float32)
        X = np.concatenate([rng.standard_normal((10_000, 64)).astype(np.float32), np.tile(base, (group, 1))])
        rng.shuffle(X)  # copies arrive interleaved with other inserts
        is_copy = np.all(X == base, axis=1)
        index = hnsw(64, 16)
        index.add(X)
        _, I = search(index, base[None], group, max(1024, 2 * group))
        found = len(set(I[0][I[0] >= 0].tolist()) & set(np.where(is_copy)[0].tolist()))
        _, I = search(index, base[None] + 0.01, group + 100, max(1024, 2 * group + 200))
        res[group] = {"copies_found": found, "results_for_k": int((I[0] >= 0).sum()), "k": group + 100}
    out["sweep"] = res
    print(label, "sweep", res, flush=True)

if "corpus" in parts:
    import os
    E = np.load(os.environ.get("CORPUS", "/home/user/realdup/multi.npy"))
    v = E.view(np.dtype((np.void, 4 * E.shape[1]))).ravel()
    _, inv, cnt = np.unique(v, return_inverse=True, return_counts=True)
    size = cnt[inv]
    t = time.time()
    index = hnsw(E.shape[1], 32, faiss.METRIC_INNER_PRODUCT)
    index.add(E)
    build_s = time.time() - t
    dup = np.where(size > 1)[0]
    kmax = int(size.max())
    _, I = search(index, E[dup], kmax, 512)
    lost = [int(i) for row, i in zip(I, dup) if i not in set(row[: size[i]].tolist() + row[size[i]:].tolist())]
    # rows whose own vector does not return them even among the whole group
    lost_dup = sum(1 for row, i in zip(I, dup) if i not in row)
    single = np.where(size == 1)[0]
    sample = np.random.default_rng(0).choice(single, 50_000, replace=False)
    _, I1 = search(index, E[sample], 1, 128)
    _, Ik = search(index, E[dup], 100, 512)
    short = int(((Ik >= 0).sum(1) < 100).sum())
    out["corpus"] = {"chunks": int(len(E)), "duplicate_chunks": int(len(dup)), "build_seconds": round(build_s, 1),
                     "duplicate_chunks_not_returned_by_own_vector": int(lost_dup),
                     "unique_chunks_sampled": 50_000, "unique_chunks_missed_at_k1": int((I1[:, 0] != sample).sum()),
                     "queries_at_duplicates_returning_fewer_than_100_of_k100": short}
    print(label, "corpus", out["corpus"], flush=True)

if "regression" in parts:
    import h5py

    res = {}
    for name, metric, n in (("sift-128-euclidean", faiss.METRIC_L2, 200_000), ("glove-100-angular", faiss.METRIC_INNER_PRODUCT, 200_000)):
        f = h5py.File(f"/home/user/datasets/{name}.hdf5", "r")
        X = np.ascontiguousarray(f["train"][:n], dtype=np.float32)
        Q = np.ascontiguousarray(f["test"][:2000], dtype=np.float32)
        if metric == faiss.METRIC_INNER_PRODUCT:
            X /= np.linalg.norm(X, axis=1, keepdims=True); Q /= np.linalg.norm(Q, axis=1, keepdims=True)
        exact = faiss.IndexFlat(X.shape[1], metric); exact.add(X)
        _, T = exact.search(Q, 10)
        index = hnsw(X.shape[1], 16, metric)
        t = time.time(); index.add(X); build = time.time() - t
        row = {"build_s": round(build, 1)}
        for ef in (16, 32, 64, 128):
            faiss.omp_set_num_threads(1)
            t = time.time(); _, I = search(index, Q, 10, ef); dt = time.time() - t
            faiss.omp_set_num_threads(4)
            row[f"ef{ef}"] = {"recall@10": round(float(np.mean([len(set(a) & set(b)) / 10 for a, b in zip(I, T)])), 4),
                              "qps": round(len(Q) / dt)}
        res[name] = row
    out["regression"] = res
    print(label, "regression", json.dumps(res), flush=True)

json.dump(out, open(f"/home/user/realdup/result_{label}.json", "w"), indent=1)
