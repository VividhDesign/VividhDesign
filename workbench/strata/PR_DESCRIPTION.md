# Strata: SQ8 quantization, on-disk re-rank vectors, and inserts that don't block reads

Two commits, both in `workbench/strata/*.patch` (apply with `git am workbench/strata/*.patch` in your Strata clone).

## 1. `quantization="sq8"` (8-bit scalar quantization)

- The graph block stores **one byte per dimension** instead of a float (d=128, M=16: 656 → 272 bytes per node).
- Per-dimension min/max codebook. While the index has fewer than 1,000 vectors, the ranges widen and existing
  codes are re-encoded, so one-by-one upserts don't freeze a degenerate range. A test caught this case:
  recall had dropped to 0.50.
- Asymmetric distance: the query stays float and is transformed once, then each candidate costs one
  widen + FMA. Kernels are `sq8_l2` / `sq8_dot` for AVX2, NEON and scalar. All three agree to 1e-6 relative error.
  NEON was checked through `NEON_2_SSE.h` emulation on x86; the macOS CI job checks it on real ARM.
- `rerank=True` (default): float vectors are kept outside the graph blocks. The graph is built at full precision,
  queries traverse the codes, and the ef candidates are re-ranked exactly. Recall equals the float index.
- `rerank=False`: codes only, so the index is about half the size or smaller, with approximate distances.
- `Index.load(path, mmap_vectors=True)`: the re-rank vectors are memory-mapped from the snapshot (64-byte
  aligned at the end of the file and still CRC-verified), so only the graph and codes stay in RAM. The first
  `add()` copies them into memory.
- Index format v2 for quantized indexes; v1 files load unchanged. Plumbed through the Python `Index`, `Collection`,
  the HTTP client and the REST server (`"quantization": "sq8"`).

## 2. Searches no longer block while a batch is inserted

- `add()` is now two-phase: a short exclusive phase (allocate nodes, store vectors, update labels), then linking
  under the **shared** lock. During linking, queries copy neighbour lists under the per-node spinlocks. With no
  insert in flight they keep the lock-free path.
- `Collection::upsert` no longer holds the collection lock across the WAL write and the index insert.
- `bench/bench_ingest` (100k inserted into 100k, 96-d, 3 insert threads, x86):

  | | queries answered during the 18 s insert | p50 | p99 |
  |---|---:|---:|---:|
  | before | 2 | 18.4 s | 18.4 s |
  | after | 81,561 | 0.19 ms | 0.46 ms |

## Tests

- C++: 37 cases / 10,504 assertions. New cases cover SQ8 kernels for every dimension remainder, SQ8 recall for
  all metrics, rerank on/off, upsert/delete/filter/compact on SQ8, one-by-one inserts, save/load round-trips,
  mmap'd vectors (identical results, re-save, writes after mmap, truncated file rejected), and concurrent
  search plus stats during a 20k-vector insert (float32 and SQ8). Collection queries during an upsert are also tested.
- Python: 19 tests.
- ThreadSanitizer and AddressSanitizer: clean.

## Benchmarks (x86, 4 vCPU Xeon @ 2.8 GHz, AVX2)

See `BENCHMARKS_X86.md` in the workbench for the GloVe tables.
