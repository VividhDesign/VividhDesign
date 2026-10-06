# Strata x86 benchmarks (6 Oct 2026)

Copied from the README section added by the patches. Raw JSON: `bench/results/*.json` in the patched repo.


Measured on a **4-vCPU cloud VM (Intel Xeon @ 2.8 GHz, AVX2)** with `bench/bench_ann.py`, `bench/bench_memory.py`,
`bench/bench_ingest` and `bench/bench_filter`. The dataset is GloVe-6B (Wikipedia + Gigaword, 400k words), with 5,000
held-out words as queries. Raw JSON is in `bench/results/`. QPS varies by about ±15% between runs on this VM, so
compare rows from the same table.

**GloVe-6B 300-d** (395k vectors, cosine, M=16, efC=200, one query thread):

| Library | Build (s) | Index file (MiB) | QPS @ R≥0.70 | QPS @ R≥0.80 | QPS @ R≥0.85 | All-core QPS (ef=64) |
|---|---:|---:|---:|---:|---:|---:|
| Strata float32 | 183 | 513 | 1,594 | 597 | 339 | 6,699 |
| **Strata SQ8 + rerank** | 180 | 627 | **2,494** | **853** | **480** | 9,045 |
| **Strata SQ8 (codes only)** | 191 | **175** | **2,681** | **964** | **532** | **10,708** |
| FAISS `IndexHNSWFlat` | 174 | 506 | 1,722 | 646 | 476 | 4,840 |
| FAISS `IndexHNSWSQ` (8-bit) | 495 | 167 | 627 | 233 | 125 | 2,154 |
| hnswlib | 169 | 508 | 1,667 | 618 | 358 | 7,018 |

- SQ8 with re-ranking keeps float recall (0.8888 vs 0.8885 at ef=512) and is 43–56% faster than float32. At 300
  dimensions the traversal is memory-bound and the codes are 4× smaller. At 100 dimensions the two run at the same speed.
- Against FAISS's 8-bit HNSW at the same code size, Strata is ~4× faster per query and builds 2.6× faster.
- FAISS `IndexHNSWFlat` is slightly ahead of Strata float32 here at high recall (476 vs 339 QPS at R≥0.85).

**Resident memory** (same data, ef=128, fresh process per row):

| Configuration | Non-reclaimable RAM | Recall@10 | QPS |
|---|---:|---:|---:|
| float32 | 537 MiB | 0.7945 | 905 |
| SQ8 + rerank | 652 MiB | 0.7955 | 1,208 |
| **SQ8 + rerank, `Index.load(path, mmap_vectors=True)`** | **197 MiB** | **0.7955** | **1,378** |
| SQ8, codes only | 197 MiB | 0.7904 | 1,039 |

With memory-mapped re-rank vectors, the graph and codes are the only private memory. The float vectors (456 MiB touched
here) live in the OS page cache, which the kernel can reclaim under pressure.

**Queries during a large insert** (`bench/bench_ingest`: 100k vectors inserted into a 100k index, 96-d, 3 insert
threads, one query thread):

| | Queries answered during the ~18 s insert | p50 | p99 |
|---|---:|---:|---:|
| before (insert held the index lock) | 2 | 17.3 s | 17.3 s |
| **now** | **81,561** | **0.19 ms** | **0.46 ms** |

**Filtered search** (`bench/bench_filter`: 200k × 96-d, allow-list filters, recall@10 = 1.0 for every row below,
ef=64 / 128):

| Selectivity | Graph walk only (old behaviour above 2,048 labels) | Cost-based planner (now) |
|---|---:|---:|
| 5% | 576 / 397 QPS | 1,430 / 1,423 QPS |
| 2% | 316 / 125 QPS | 2,136 / 3,120 QPS |
| 1% | brute force, 4,171 QPS | 7,175 / 7,090 QPS (faster scan) |


## GloVe-6B 100-d (first run; FAISS / hnswlib phases overlapped with compile jobs, so treat cross-library gaps as ±15%)

| Library | Build (s) | Index file (MiB) | QPS @ R≥0.85 | QPS @ R≥0.90 | QPS @ R≥0.95 | All-core QPS (ef=64) | Max recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strata float32 | 64.9 | 209 | 5,585 | 3,207 | 1,670 | 14,746 | 0.9838 |
| Strata SQ8 + rerank | 66.7 | 251 | 4,951 | 2,639 | 1,462 | 14,868 | 0.9836 |
| Strata SQ8 (codes only) | 81.0 | 102 | 4,489 | 3,069 | 882 | 17,663 | 0.9627 |
| FAISS IndexHNSWFlat | 85.2 | 202 | 4,699 | 2,523 | 1,433 | 14,586 | 0.9813 |
| FAISS IndexHNSWSQ (8-bit) | 164.4 | 91 | 1,471 | 858 | 322 | 2,746 | 0.9601 |
| hnswlib | 77.2 | 204 | 5,283 | 2,859 | 1,557 | 12,617 | 0.9839 |
