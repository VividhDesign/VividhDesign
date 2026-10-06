"""Imitates the ann-benchmarks harness against the Strata module (run from this directory)."""
import sys, types, importlib.util
import numpy as np

base = types.ModuleType("ann_benchmarks.algorithms.base.module")
class BaseANN:  # minimal stand-in for ann_benchmarks' BaseANN
    pass
base.BaseANN = BaseANN
for name in ["ann_benchmarks", "ann_benchmarks.algorithms", "ann_benchmarks.algorithms.base"]:
    sys.modules[name] = types.ModuleType(name)
sys.modules["ann_benchmarks.algorithms.base.module"] = base
spec = importlib.util.spec_from_file_location("ann_benchmarks.algorithms.strata.module",
                                              "ann_benchmarks/algorithms/strata/module.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

rng = np.random.default_rng(0)
X, Q = rng.standard_normal((20000, 64)).astype(np.float32), rng.standard_normal((200, 64)).astype(np.float32)
truth = np.argsort(((Q[:, None] - X[None]) ** 2).sum(-1), axis=1)[:, :10]
for params in [{"M": 16, "efConstruction": 200}, {"M": 16, "efConstruction": 200, "quantization": "sq8"}]:
    algo = mod.Strata("euclidean", params)
    algo.fit(X)
    algo.set_query_arguments(128)
    single = np.array([algo.query(q, 10) for q in Q])
    algo.batch_query(Q, 10)
    batch = algo.get_batch_results()
    recall = np.mean([len(set(a) & set(t)) / 10 for a, t in zip(single, truth)])
    assert (single == batch).all() and recall > 0.9, recall
    print(algo.name, "recall@10 =", round(recall, 4), "memory KiB =", int(algo.get_memory_usage()))
print("ok")
