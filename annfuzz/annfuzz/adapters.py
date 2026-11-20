"""Uniform adapters over approximate-nearest-neighbour libraries.

Every adapter exposes the same small surface so one property suite can run against all of them:

    idx = A.build(dim, metric, M)          # metric in {"l2", "cos", "ip"}
    A.add(idx, vectors, ids)               # ids: int64 array
    ids, dists = A.search(idx, queries, k, ef)   # ids padded with -1 when fewer than k results
    A.delete(idx, ids)                     # optional, A.can_delete
    idx = A.roundtrip(idx, path)           # optional save + load, A.can_save
    ids, dists = A.search_filtered(idx, queries, k, ef, allowed)  # optional, A.can_filter

Distances are returned exactly as each library reports them; `annfuzz.oracle` knows the conventions.
"""

from __future__ import annotations

import numpy as np

MISSING = -1


def _pad(ids, dists, k):
    out_i = np.full((len(ids), k), MISSING, dtype=np.int64)
    out_d = np.full((len(ids), k), np.nan, dtype=np.float64)
    for r, (i, d) in enumerate(zip(ids, dists)):
        n = min(k, len(i))
        out_i[r, :n] = i[:n]
        out_d[r, :n] = d[:n]
    return out_i, out_d


class Adapter:
    name = "base"
    metrics: dict = {}
    can_delete = can_save = can_filter = can_update = False
    incremental = True
    # how the library reports a distance for each metric, see oracle.CONVENTIONS
    convention: dict = {}

    def supports(self, metric):
        return metric in self.metrics


class Hnswlib(Adapter):
    name = "hnswlib"
    metrics = {"l2": "l2", "cos": "cosine", "ip": "ip"}
    convention = {"l2": "l2sq", "cos": "one_minus_cos", "ip": "one_minus_dot"}
    can_delete = can_save = can_filter = can_update = True

    def build(self, dim, metric, M=16, efc=100):
        import hnswlib

        native = hnswlib.Index(space=self.metrics[metric], dim=dim)
        native.init_index(max_elements=16, ef_construction=efc, M=M, random_seed=0, allow_replace_deleted=False)
        return self._wrap(native, dim, self.metrics[metric])

    class _Holder:
        pass

    def _wrap(self, native, dim, space, deleted=()):
        h = self._Holder()
        h.native, h._dim, h.space, h._deleted = native, dim, space, set(deleted)
        return h

    def add(self, h, X, ids):
        idx = h.native
        need = idx.get_current_count() + len(X)
        if need > idx.get_max_elements():
            idx.resize_index(max(need, 2 * idx.get_max_elements()))
        idx.add_items(X, ids, num_threads=1)

    def search(self, h, Q, k, ef):
        idx = h.native
        idx.set_ef(max(ef, k))
        n = idx.get_current_count() - len(h._deleted)
        kk = min(k, max(n, 0))
        if kk == 0 or len(Q) == 0:
            return _pad([[]] * len(Q), [[]] * len(Q), k)
        labels, dists = idx.knn_query(Q, k=kk, num_threads=1)
        return _pad(labels.astype(np.int64), dists, k)

    def search_filtered(self, h, Q, k, ef, allowed):
        idx = h.native
        allowed = set(int(a) for a in allowed)
        idx.set_ef(max(ef, k))
        rows_i, rows_d = [], []
        for q in Q:
            kk = min(k, len(allowed))
            try:
                l, d = idx.knn_query(q[None], k=kk, filter=lambda i: i in allowed, num_threads=1)
                rows_i.append(l[0].astype(np.int64)); rows_d.append(d[0])
            except RuntimeError:
                rows_i.append(np.array([], dtype=np.int64)); rows_d.append(np.array([]))
        return _pad(rows_i, rows_d, k)

    def delete(self, h, ids):
        for i in ids:
            h.native.mark_deleted(int(i))
            h._deleted.add(int(i))

    def roundtrip(self, h, path):
        import hnswlib

        h.native.save_index(path)
        new = hnswlib.Index(space=h.space, dim=h._dim)
        new.load_index(path)
        return self._wrap(new, h._dim, h.space, h._deleted)


class Faiss(Adapter):
    name = "faiss"
    metrics = {"l2": "l2", "ip": "ip"}
    convention = {"l2": "l2sq", "ip": "dot"}

    def build(self, dim, metric, M=16, efc=100):
        import faiss

        faiss.omp_set_num_threads(1)
        base = faiss.IndexHNSWFlat(dim, M, faiss.METRIC_L2 if metric == "l2" else faiss.METRIC_INNER_PRODUCT)
        base.hnsw.efConstruction = efc
        return faiss.IndexIDMap(base)

    def add(self, idx, X, ids):
        idx.add_with_ids(np.ascontiguousarray(X, dtype=np.float32), np.asarray(ids, dtype=np.int64))

    def search(self, idx, Q, k, ef):
        import faiss

        params = faiss.SearchParametersHNSW(efSearch=max(ef, k))
        if len(Q) == 0:
            return _pad([], [], k)
        D, I = idx.search(np.ascontiguousarray(Q, dtype=np.float32), k, params=params)
        return I.astype(np.int64), D.astype(np.float64)


class Voyager(Adapter):
    name = "voyager"
    metrics = {"l2": "Euclidean", "cos": "Cosine", "ip": "InnerProduct"}
    convention = {"l2": "l2sq", "cos": "one_minus_cos", "ip": "one_minus_dot"}
    can_delete = can_save = can_update = True

    def build(self, dim, metric, M=16, efc=100):
        import voyager

        return voyager.Index(getattr(voyager.Space, self.metrics[metric]), num_dimensions=dim, M=M,
                             ef_construction=efc, random_seed=0)

    def add(self, idx, X, ids):
        idx.add_items(X, [int(i) for i in ids], num_threads=1)

    def search(self, idx, Q, k, ef):
        n = len(idx)
        kk = min(k, n)
        if kk == 0 or len(Q) == 0:
            return _pad([[]] * len(Q), [[]] * len(Q), k)
        I, D = idx.query(Q, k=kk, num_threads=1, query_ef=max(ef, kk))
        return _pad(np.asarray(I, dtype=np.int64), np.asarray(D, dtype=np.float64), k)

    def delete(self, idx, ids):
        for i in ids:
            idx.mark_deleted(int(i))

    def roundtrip(self, idx, path):
        import voyager

        idx.save(path)
        return voyager.Index.load(path)


class Annoy(Adapter):
    name = "annoy"
    metrics = {"l2": "euclidean", "cos": "angular", "ip": "dot"}
    convention = {"l2": "l2", "cos": "angular_chord", "ip": "dot"}
    incremental = False
    can_save = True

    class _Idx:
        pass

    def build(self, dim, metric, M=16, efc=100):
        h = self._Idx()
        h.dim, h.metric, h.items, h.built = dim, metric, {}, None
        return h

    def add(self, h, X, ids):
        for i, x in zip(ids, X):
            h.items[int(i)] = np.asarray(x, dtype=np.float32)
        h.built = None

    def _index(self, h):
        if h.built is None:
            from annoy import AnnoyIndex

            a = AnnoyIndex(h.dim, self.metrics[h.metric])
            a.set_seed(0)
            for i, x in h.items.items():
                a.add_item(i, x.tolist())
            a.build(20, n_jobs=1)
            h.built = a
        return h.built

    def search(self, h, Q, k, ef):
        a = self._index(h)
        rows_i, rows_d = [], []
        for q in Q:
            i, d = a.get_nns_by_vector(q.tolist(), k, search_k=max(ef, k) * 20, include_distances=True)
            rows_i.append(np.asarray(i, dtype=np.int64)); rows_d.append(np.asarray(d))
        return _pad(rows_i, rows_d, k)

    def roundtrip(self, h, path):
        from annoy import AnnoyIndex

        a = self._index(h)
        a.save(path)
        b = AnnoyIndex(h.dim, self.metrics[h.metric])
        b.load(path)
        new = self._Idx()
        new.dim, new.metric, new.items, new.built = h.dim, h.metric, dict(h.items), b
        return new


class PyNNDescent(Adapter):
    name = "pynndescent"
    metrics = {"l2": "euclidean", "cos": "cosine", "ip": "dot"}
    convention = {"l2": "l2", "cos": "one_minus_cos", "ip": "one_minus_dot"}
    incremental = False

    class _Idx:
        pass

    def build(self, dim, metric, M=16, efc=100):
        h = self._Idx()
        h.metric, h.ids, h.X, h.built, h.M = metric, [], [], None, M
        return h

    def add(self, h, X, ids):
        h.X.append(np.asarray(X, dtype=np.float32)); h.ids += [int(i) for i in ids]; h.built = None

    def search(self, h, Q, k, ef):
        from pynndescent import NNDescent

        if h.built is None:
            data = np.concatenate(h.X)
            h.built = NNDescent(data, metric=self.metrics[h.metric], n_neighbors=max(2 * h.M, 10), random_state=0,
                                n_jobs=1, verbose=False)
            h.built.prepare()
            h.idmap = np.asarray(h.ids, dtype=np.int64)
        kk = min(k, len(h.idmap))
        I, D = h.built.query(np.asarray(Q, dtype=np.float32), k=kk, epsilon=0.1 + ef / 1000)
        ids = np.where(I >= 0, h.idmap[np.clip(I, 0, None)], MISSING)
        return _pad(ids, D, k)


class USearch2(Adapter):
    name = "usearch-2.x"
    metrics = {"l2": "l2sq", "cos": "cos", "ip": "ip"}
    convention = {"l2": "l2sq", "cos": "one_minus_cos", "ip": "one_minus_dot"}
    can_delete = can_save = can_update = True

    def build(self, dim, metric, M=16, efc=100):
        from usearch.index import Index

        return Index(ndim=dim, metric=self.metrics[metric], dtype="f32", connectivity=M, expansion_add=efc)

    def add(self, idx, X, ids):
        idx.add(np.asarray(ids, dtype=np.uint64), np.asarray(X, dtype=np.float32), threads=1)

    def search(self, idx, Q, k, ef):
        if len(Q) == 0 or len(idx) == 0:
            return _pad([[]] * len(Q), [[]] * len(Q), k)
        idx.expansion_search = max(ef, k)
        m = idx.search(np.asarray(Q, dtype=np.float32), k, threads=1)
        keys = np.atleast_2d(m.keys).astype(np.int64)
        dist = np.atleast_2d(m.distances).astype(np.float64)
        counts = np.atleast_1d(getattr(m, "counts", len(np.atleast_1d(m.keys))))
        rows_i = [keys[r, : counts[r]] for r in range(len(Q))]
        rows_d = [dist[r, : counts[r]] for r in range(len(Q))]
        return _pad(rows_i, rows_d, k)

    def delete(self, idx, ids):
        idx.remove(np.asarray(ids, dtype=np.uint64))

    def roundtrip(self, idx, path):
        from usearch.index import Index

        idx.save(path)
        return Index.restore(path)


class Strata(Adapter):
    name = "strata"
    metrics = {"l2": "l2", "cos": "cosine", "ip": "ip"}
    convention = {"l2": "l2sq", "cos": "one_minus_cos", "ip": "one_minus_dot"}
    can_delete = can_save = can_filter = can_update = True

    def build(self, dim, metric, M=16, efc=100):
        import strata

        return strata.Index(dim=dim, metric=self.metrics[metric], M=M, ef_construction=efc, seed=0)

    def add(self, idx, X, ids):
        idx.add(np.asarray(X, dtype=np.float32), ids=np.asarray(ids, dtype=np.int64), num_threads=1)

    def search(self, idx, Q, k, ef):
        if len(Q) == 0:
            return _pad([], [], k)
        I, D = idx.search(np.asarray(Q, dtype=np.float32), k=k, ef=max(ef, k), num_threads=1)
        return np.asarray(I, dtype=np.int64), np.asarray(D, dtype=np.float64)

    def search_filtered(self, idx, Q, k, ef, allowed):
        I, D = idx.search(np.asarray(Q, dtype=np.float32), k=k, ef=max(ef, k), num_threads=1,
                          filter_ids=np.asarray(sorted(allowed), dtype=np.int64))
        return np.asarray(I, dtype=np.int64), np.asarray(D, dtype=np.float64)

    def delete(self, idx, ids):
        idx.remove(np.asarray(ids, dtype=np.int64))

    def roundtrip(self, idx, path):
        import strata

        idx.save(path)
        return strata.Index.load(path)


ALL = [Hnswlib(), Faiss(), Voyager(), Annoy(), PyNNDescent(), USearch2(), Strata()]


class USearch3(Adapter):
    """USearch 3.0 release candidate (DenseIndex API). Needs its own environment: 2.x and 3.x share a module name."""

    name = "usearch-3.0"
    metrics = {"l2": "EUCLIDEAN", "cos": "ANGULAR", "ip": "INNER"}
    convention = {"l2": "l2", "cos": "one_minus_cos", "ip": "one_minus_dot"}
    can_save = True

    def build(self, dim, metric, M=16, efc=100):
        from usearch import DenseIndex, DenseMetric, Scalar

        idx = DenseIndex.init_ram(dimensions=dim, metric=getattr(DenseMetric, self.metrics[metric]),
                                  quantization=Scalar.BF16, connectivity=M)
        return idx

    def add(self, idx, X, ids):
        if len(X):
            idx.insert(np.asarray(ids, dtype=np.uint64), np.asarray(X, dtype=np.float32))

    def search(self, idx, Q, k, ef):
        from usearch import Arena

        if len(Q) == 0 or len(idx) == 0:
            return _pad([[]] * len(Q), [[]] * len(Q), k)
        m = idx.search(np.asarray(Q, dtype=np.float32), k, Arena(), expansion_factor=max(ef, k))
        rows_i = [np.array([int(x.key) for x in m[r]], dtype=np.int64) for r in range(len(Q))]
        rows_d = [np.array([float(x.distance) for x in m[r]]) for r in range(len(Q))]
        return _pad(rows_i, rows_d, k)

    def roundtrip(self, idx, path):
        from usearch import DenseIndex

        idx.save(path)
        return DenseIndex.load_ram(path)


# Selected by name only: USearch 2.x and 3.x share a module name, so 3.x runs in its own environment.
EXTRA = [USearch3()]
