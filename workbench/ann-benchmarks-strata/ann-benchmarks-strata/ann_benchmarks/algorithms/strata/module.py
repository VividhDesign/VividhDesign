import numpy as np
import strata

from ..base.module import BaseANN


class Strata(BaseANN):
    """Strata: HNSW vector database in C++17 (https://github.com/VividhDesign/strata).

    quantization="sq8" stores one byte per dimension in the graph and re-ranks the ef
    candidates with the float32 vectors (rerank=True), or answers from codes alone.
    """

    def __init__(self, metric, method_param):
        self.metric = {"angular": "cosine", "euclidean": "l2"}[metric]
        self.M = method_param["M"]
        self.ef_construction = method_param["efConstruction"]
        self.quantization = method_param.get("quantization", "none")
        self.rerank = method_param.get("rerank", True)
        self.ef = 10

    def fit(self, X):
        X = np.ascontiguousarray(X, dtype=np.float32)
        self.index = strata.Index(
            X.shape[1],
            self.metric,
            M=self.M,
            ef_construction=self.ef_construction,
            capacity=len(X),
            quantization=self.quantization,
            rerank=self.rerank,
        )
        self.index.add(X)  # parallel build on all cores, like the other HNSW entries

    def set_query_arguments(self, ef):
        self.ef = ef
        self.name = "strata (M=%d, efC=%d, q=%s, ef=%d)" % (self.M, self.ef_construction, self.quantization, ef)

    def query(self, v, n):
        q = np.ascontiguousarray(v, dtype=np.float32).reshape(1, -1)
        return self.index.search(q, k=n, ef=self.ef, num_threads=1)[0][0]

    def batch_query(self, X, n):
        X = np.ascontiguousarray(X, dtype=np.float32)
        self.res = self.index.search(X, k=n, ef=self.ef, num_threads=0)[0]

    def get_batch_results(self):
        return self.res

    def get_memory_usage(self):
        return None if not hasattr(self, "index") else self.index.stats()["memory_bytes"] / 1024

    def freeIndex(self):
        del self.index
