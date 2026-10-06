# Strata: SQ8 quantization, on-disk re-rank vectors, non-blocking inserts, cost-based filtered search

Four commits, all authored by Vividh Yadav: `workbench/strata/000*.patch`. In your Strata clone run:

```bash
git am /path/to/workbench/strata/*.patch   # applies cleanly onto 0ed9d74 (checked)
cmake -S . -B build -G Ninja && cmake --build build && ./build/strata_tests
pip install ".[test]" && pytest
git push
```

## 1. `quantization="sq8"`: 8-bit scalar quantization
- The graph block stores **one byte per dimension** (d=128, M=16: 656 → 272 bytes per node).
- Per-dimension min/max codebook. While the index has fewer than 1,000 vectors, the ranges widen and the codes
  are re-encoded exactly, so one-by-one upserts don't freeze a degenerate range. A test caught this:
  recall had dropped to 0.50.
- Asymmetric kernels `sq8_l2` / `sq8_dot` for AVX2, NEON and scalar. All agree to 1e-6. NEON was checked through
  `NEON_2_SSE.h` emulation on x86; the macOS CI job checks it on real ARM.
- `rerank=True` (default): the graph is built at full precision, queries traverse the codes, and the ef candidates are
  re-ranked exactly. `rerank=False`: codes only, about 3× smaller.
- `Index.load(path, mmap_vectors=True)`: the re-rank vectors are memory-mapped from the snapshot (64-byte aligned, CRC
  still verified). On GloVe-300, private RAM drops from 537 to 197 MiB at equal recall.
- Index format v2 for quantized indexes; v1 files still load. Plumbed through the Python `Index`, `Collection`,
  the HTTP client and the REST server.

## 2. Inserts no longer block searches
- `add()` has two phases: a short exclusive one (allocate, store vectors, update labels) and linking under the
  **shared** lock. While linking is in progress, queries copy neighbour lists under the per-node spinlocks. Otherwise they keep the lock-free path.
- `Collection::upsert` no longer holds the collection lock across the WAL write and the index insert.
- 100k vectors inserted into a 100k index: before, 2 queries were answered during the 17 s insert (one waited the
  whole time); now 81,561 are answered, with p50 0.19 ms and p99 0.46 ms.

## 3. Cost-based filtered search
- Brute force over the allowed set when |allowed| ≤ sqrt(M0/2 · ef · n), calibrated with `bench/bench_filter`.
  The fixed 2,048-label floor stays. At 2% selectivity: 125–316 → 2,100–3,100 QPS. At 5%: 397–576 → 1,430. Recall is 1.0 throughout.
- Open-addressing label map (16 B/slot, ~14 ns per prefetched lookup) replaces `std::unordered_map`.
- An exact scan when ef ≥ live vectors. This fixes a rare unreachable-node case in small parallel builds, which also
  existed in the original code (2/3000 builds in release, 110/3000 under ASan).
- An ACORN-1 style two-hop walk was tried and rejected, with numbers in `docs/DESIGN.md`.

## 4. Docs
README x86 section (GloVe-6B 300-d vs FAISS/hnswlib, memory, ingest, filters) and DESIGN.md sections for all of the above.

## Tests
- C++: 39 cases / 155,163 assertions (SQ8, mmap, concurrency, planner, LabelMap fuzz vs `std::unordered_map`).
- Python: 19 tests. ThreadSanitizer and AddressSanitizer clean.

## Benchmarks
See `BENCHMARKS_X86.md`.
