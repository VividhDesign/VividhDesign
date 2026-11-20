import sys, numpy as np, warnings
warnings.filterwarnings("ignore")
from pynndescent import NNDescent
def run(d, seed, metric="cosine", group=200, others=1800):
    rng = np.random.default_rng(seed); base = rng.standard_normal(d).astype(np.float32)
    X = np.concatenate([np.tile(base, (group, 1)), rng.standard_normal((others, d)).astype(np.float32)])
    idx = NNDescent(X, metric=metric, n_neighbors=30, random_state=seed, n_jobs=1); idx.prepare()
    G = idx._search_graph.tocsr(); indeg = np.bincount(G.indices, minlength=G.shape[0])
    I, _ = idx.query(base[None], k=group, epsilon=0.3)
    # every row searched with its own vector
    J, _ = idx.query(X, k=1, epsilon=0.3)
    self_hits = int(((J[:, 0] == np.arange(len(X))) | ((J[:, 0] < group) & (np.arange(len(X)) < group))).sum())
    return int((indeg == 0).sum()), len(set(I[0][I[0] < group].tolist())), self_hits
tot = [0, 0, 0]
for metric in ("cosine", "dot"):
    for d in (64, 384, 768):
        for seed in range(4):
            o, f, s = run(d, seed, metric)
            print(f"{sys.argv[1]:6} {metric:6} dim={d:4} seed={seed}: orphans={o:4}  duplicates found {f:3}/200  self-search hits {s}/2000", flush=True)
