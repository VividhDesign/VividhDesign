# Study guide: the work in annfuzz, and how to defend it

Everything here was built with an AI assistant (Claude Code) in one session. Before you present any of it, as a PR, a
post or in an interview, make it yours: re-run the key numbers yourself, and read the fixes until you could have
written them. Below is what you need to know.

## 1. The FAISS duplicate bug, from first principles

**HNSW in one paragraph.** Each vector is a node, linked to a few near neighbours. A search starts at an entry point
and repeatedly moves to neighbours closer to the query, keeping a beam of `efSearch` candidates. Level 0 holds every
node, and each node's level-0 list has room for 2M links.

**Neighbour pruning.** When a node's list must shrink, HNSW keeps a candidate `v` only if no already-kept neighbour
`u` is closer to `v` than the node itself is: `dist(v, u) < dist(v, node)` means `v` is redundant. FAISS writes this
as `Comp::cmp(dist_v1_q, dist_v1_v2)`.

**Why identical vectors break it.**
- Between copies every distance is 0. The pruning test `0 < 0` is false, so copies never prune one another.
- FAISS gives a new node up to 2M links at level 0 (`nb_neighbors(0)`). The paper (Malkov & Yashunin, Algorithm 1)
  gives M and lets reverse links fill the rest.
- With more than 2M copies, each copy's whole list is therefore other copies. Later nodes' reverse links compete with
  copies at distance 0 and always lose.

Consequences:
1. Few or no edges leave the group. A search that enters it can only visit copies, so it stops early and returns
   fewer than `k` results. The issue script at M=32 has zero edges out and returns 135 results for k=300.
2. A copy whose reverse links all lose has no incoming edge, so nothing can ever reach it.

**The fix.** If a new node has an exact duplicate among its candidates (a candidate whose distance equals the node's
distance to itself), it takes M links instead of 2M, as in the paper. The other M slots stay free, so later nodes'
reverse links into the group find room, and the group keeps edges going out. Nodes without duplicates take 2M
exactly as before. That's why graphs on GloVe and SIFT-200k are byte-identical.

**Why not just use M for everyone?** I measured it. Recall@10 at a fixed `efSearch` drops 0.1–2 points on SIFT and
GloVe, and FAISS wouldn't accept that. The adaptive rule only touches nodes that have duplicates.

## 2. Re-run the key numbers yourself

All scripts are in `contributions/faiss/scripts/` (`issue_snippet.py`, `inspect_snippet.py`, `experiment.py`,
`sift1m.py`, `qps_ab.py`, `graph_identity.py`, `build_corpus_paragraphs.py`). Some paths inside them point at
`/home/user/...`, so edit those first. To reproduce:
1. Clone FAISS and build it from source with Python bindings (`cmake -B build -DFAISS_ENABLE_GPU=OFF
   -DFAISS_ENABLE_PYTHON=ON -DBUILD_TESTING=OFF . && make -C build -j swigfaiss`). The first build takes about 30
   minutes; after that, a change to `HNSW.cpp` alone rebuilds in seconds.
2. Install the unpatched build in its own folder: `cd build/faiss/python && pip install --no-deps --target ~/faiss-before .`
3. Apply the patch (`git am 0001-*.patch`), rebuild, and install to `~/faiss-after` the same way. Keep the two
   folders separate: `pip install .` rewrites `build/lib`, so a second install silently replaces the first. I made
   this mistake once in this session and caught it because the before and after numbers came out identical.
4. Run each script twice, with `PYTHONPATH=~/faiss-before` and with `PYTHONPATH=~/faiss-after`. Start with
   `issue_snippet.py`, which takes a second: before gives 166 and 135 copies found; after gives 200 and 200.
5. For SIFT1M, download `sift-128-euclidean.hdf5` from ann-benchmarks.com and run `sift1m.py`.
6. For the corpus, run `build_corpus_paragraphs.py` over any set of repositories. Your numbers will differ with
   other repositories, but the pattern won't.

## 3. Questions you will get, and honest answers

- **"Does this change results on normal data?"** Not where there are no exact duplicates: the graph is byte-identical,
  which I checked on GloVe and SIFT-200k. On SIFT1M, which has 2.9% duplicate pairs, recall differs by at most 0.0009
  at efSearch 16–32 and is identical from 64 up.
- **"Why compare `d == d_self` with exact float equality?"** Duplicates produce bit-identical distances, since the
  same computation runs on the same inputs. Distinct vectors at exactly the self-distance are measure-zero. Even then,
  the only effect is that one node takes M instead of 2M links, which is what the paper does anyway.
- **"Is it fully fixed?"** No. A group 30 times larger than the list (1,000 copies, M=16) still loses about a third of
  its copies, against two thirds before. A complete fix needs aliasing (one node per distinct vector). Say so up
  front: maintainers trust contributors who state the limits of their own work.
- **"How did you find it?"** A property-based suite (annfuzz) runs identical correctness checks across seven ANN
  libraries. Only FAISS, USearch and PyNNDescent lost duplicates. Reading both graphs (FAISS's level-0 lists and
  hnswlib's saved index) showed the structural difference.
- **"Did you use AI?"** Yes, and say so. Explain what you checked and understood yourself. Projects such as pandas
  require this disclosure. FAISS doesn't have a policy, but honesty here protects you.

## 4. The other root cause: PyNNDescent's −1.7e-7

PyNNDescent's cosine and dot distances compute `−log2(<x, y>)` in float32. For identical rows that should be 0, but
for some vectors rounding gives −1.7e-7. The search graph merges forward and reverse edges with `scipy.sparse.maximum`
semantics, which compare an edge present in one direction only with an implicit 0 and drop zero results. Exact zeros
were already protected (raised to `FLOAT32_EPS`), but a tiny negative was not, so most copies lost their incoming
edges. The fix changes `== 0.0` to `<= 0.0`.
