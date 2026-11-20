"""The suite's own tests: a brute-force index must pass every property."""

import numpy as np

from annfuzz.adapters import MISSING, Adapter, _pad
from annfuzz.properties import PROPERTIES


class Exact(Adapter):
    name = "exact"
    metrics = {"l2": "l2", "cos": "cos", "ip": "ip"}
    convention = {"l2": "l2sq", "cos": "one_minus_cos", "ip": "one_minus_dot"}
    can_delete = can_filter = can_update = True

    def build(self, dim, metric, M=16, efc=100):
        return {"metric": metric, "rows": {}}

    def add(self, idx, X, ids):
        X = np.asarray(X, dtype=np.float64)
        if not np.isfinite(X).all():
            raise ValueError("non-finite row")
        for i, x in zip(ids, X):
            idx["rows"][int(i)] = x

    def _dist(self, idx, X, q):
        if idx["metric"] == "l2":
            return ((X - q) ** 2).sum(1)
        if idx["metric"] == "ip":
            return 1 - X @ q
        return 1 - (X @ q) / np.maximum(np.linalg.norm(X, axis=1) * np.linalg.norm(q), 1e-30)

    def search(self, idx, Q, k, ef, allowed=None):
        keys = [i for i in idx["rows"] if allowed is None or i in allowed]
        if not keys:
            return _pad([[]] * len(Q), [[]] * len(Q), k)
        X = np.stack([idx["rows"][i] for i in keys])
        out_i, out_d = [], []
        for q in np.asarray(Q, dtype=np.float64):
            d = self._dist(idx, X, q)
            order = np.argsort(d, kind="stable")[:k]
            out_i.append(np.asarray(keys)[order]); out_d.append(d[order])
        return _pad(out_i, out_d, k)

    def search_filtered(self, idx, Q, k, ef, allowed):
        return self.search(idx, Q, k, ef, set(int(a) for a in allowed))

    def delete(self, idx, ids):
        for i in ids:
            idx["rows"].pop(int(i), None)


def test_exact_index_passes_every_property():
    A = Exact()
    for metric in ("l2", "cos", "ip"):
        for prop in PROPERTIES:
            assert prop(A, metric) == [], (metric, prop.__name__)


def test_padding_marks_missing_results():
    ids, dists = _pad([np.array([3])], [np.array([0.5])], 3)
    assert ids.tolist() == [[3, MISSING, MISSING]]
    assert np.isnan(dists[0, 1:]).all()
