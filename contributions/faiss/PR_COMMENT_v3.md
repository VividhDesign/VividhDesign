I pushed a second commit (f422620) that fixes a problem I found in the first one.

**Problem.** The duplicate check called `symmetric_dis(pt_id, pt_id)` for every point added at level 0. Not every `DistanceComputer` implements `symmetric_dis`: the full TurboQuant scalar quantizer throws "Not implemented", and PQ throws when it has no SDC table. With the first commit, adding 20 vectors to `IndexHNSWSQ(16, ScalarQuantizer.QT_4bit_tq, 32)` aborted the process. `main` builds that index without error.

**Change.**
- A copy is now found with `ptdis(pt_id)`, the same kind of distance the link targets carry.
- `symmetric_dis` is called only once a copy is found. It checks whether copies tie in the pruning, which happens only with exact storage.
- With lossy storage, a copy's distance to the point differs from its distance to another copy, so the pruning decides between copies as before.
- The check is skipped when there are fewer than `nb_neighbors(1)` targets, since every target is kept either way.

All runs below use 200 copies plus 800 other vectors, `efSearch=1000`, and k=300.

| | `main` | first commit | now |
|---|---|---|---|
| `IndexHNSWSQ` `QT_4bit_tq`: add 20 vectors | ok | process aborts | ok |
| Copies found with SQ8 / fp16 / PQ8 / EDEN-4bit (M=32, efConstruction=100) | 161 / 200 / 151 / 149 | 161 / 200 / 151 / 149 | 161 / 200 / 151 / 149 |
| Flat, script in #5968: copies found at M=16 / M=32 | 166 / 135 | 200 / 200 | 200 / 200 |
| Flat, default efConstruction (40): copies found at M=16 / M=32 | 129 / 163 | 193 / 191 | 193 / 191 |
| Flat, default efConstruction, M=16: results returned | 129 | 300 | 300 |

With flat storage, the graphs are byte-identical to the first commit:
- SIFT1M: 33,064,528 neighbour entries, so the recall and QPS tables in the description still apply.
- The code-corpus and sweep results in the description are also unchanged.
- SIFT-200k and GloVe-200k remain byte-identical to `main`.

Tests: the 23 Python test files that mention HNSW give 589 passed and 47 skipped. `clang-format-21` reports nothing.

Separately, `main` already aborts when building `IndexHNSWSQ` with `QT_4bit_tq` at a normal size: adding 1,000 vectors aborts the process. `shrink_neighbor_list` calls `symmetric_dis` inside the OpenMP region, and the exception terminates the process. This PR does not change that. I can open a separate issue for it.
