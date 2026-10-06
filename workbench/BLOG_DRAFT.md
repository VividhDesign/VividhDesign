# Two weekends of vector-database engineering: 8-bit codes, disk-resident vectors, and readers that never wait

*Draft blog post for dev.to / Medium / your site. Post it after the Strata patches are merged, then share it on
LinkedIn and in r/MachineLearning or r/cpp. Fill the ⟨⟩ placeholders from `BENCHMARKS_X86.md`.*

---

I've been building [Strata](https://github.com/VividhDesign/strata), a vector database written from scratch in
C++17. Its README listed three limitations I kept apologising for: no vector compression, writes that block reads,
and single-node only. This post is about fixing the first two, and the bugs I hit doing it.

## 1. Quantization that doesn't cost recall

A Strata node lives in one fixed-size block: its neighbour list, then its vector. For 128-d floats with M=16 that is
656 bytes, of which 512 are the vector. HNSW search is a chain of cache misses through those blocks, so shrinking
the vector shrinks the working set.

**SQ8** stores each dimension as one byte: `x ≈ min_d + scale_d · c`. The query stays in float, which makes this
"asymmetric" quantization. I transform the query once per search, so each candidate costs a widen-and-FMA:

- L2: `Σ scale_d² · ((q_d − min_d)/scale_d − c_d)²`
- dot product: `⟨q, min⟩ + Σ (q_d · scale_d) · c_d`

On AVX2 the widen is `_mm256_cvtepu8_epi32` followed by `_mm256_cvtepi32_ps`. On NEON it is
`vmovl_u8 → vmovl_u16 → vcvtq_f32_u32`. I don't own an x86 *and* an ARM machine in the same place, so I tested the NEON
kernel on x86 through Intel's `NEON_2_SSE.h` translation header. All three backends (scalar, AVX2, NEON) agree to
1e-6 relative error.

**The bug.** My first version trained min/max on the first batch. A test that inserted vectors one at a time
got **recall 0.50**. The first "batch" was a single vector, so every range had zero width. When later vectors
widened it, the range jumped by 255 units, because I had reconstructed max as `min + 255·scale` with a placeholder
scale of 1. Now Strata tracks the true min/max and keeps widening, re-encoding from the float vectors, until the
index holds 1,000 vectors. After that the ranges freeze.

**Re-ranking.** By default Strata keeps the float vectors outside the graph blocks. It builds the graph with exact
distances, so the graph is identical to the float index, walks it on codes, and re-ranks the `ef` candidates exactly.
On GloVe-6B (400k words) recall is unchanged (0.9335 vs 0.9334 at ef=128).

**Then move the floats to disk.** The re-rank vectors are read for only `ef` nodes per query, which makes them a
natural fit for memory-mapping. Snapshots now put them last, 64-byte aligned, so `Index.load(path, mmap_vectors=True)`
maps them instead of reading them. Only the graph and the codes count toward resident memory:
⟨RSS numbers from bench_memory⟩.

Against FAISS's `IndexHNSWSQ` on the same 4-vCPU x86 box (GloVe-100): ⟨3.5×⟩ the single-thread QPS at recall 0.90,
⟨6.4×⟩ the all-core throughput, and half the build time.

## 2. Readers that don't wait for writers

Strata's `add()` used to take the index lock exclusively and then insert in parallel internally. Inserting
100k vectors takes 18 s on 4 cores, and a concurrent query waited all 18 s.

The fix splits `add()` into two phases:

1. **Exclusive and short:** grow arrays, assign node ids, write vectors, update the label map. This takes about 80 ms for 100k vectors.
2. **Shared and long:** link the new nodes into the graph.

While phase 2 runs, queries must not read a neighbour list that an inserting thread is rewriting. The inserting
threads already copy neighbour lists under 1-byte per-node spinlocks, so readers do the same. They do it **only
while an insert is linking**. An atomic `linking_` flag is set only under the exclusive lock, so a reader that saw
`false` while holding the shared lock knows no linking phase can overlap it. The common, write-free path stays
lock-free.

| | queries answered during an 18 s insert | p50 | p99 |
|---|---:|---:|---:|
| before | 2 | 18.4 s | 18.4 s |
| after | 81,561 | 0.19 ms | 0.46 ms |

Insert throughput didn't change. ThreadSanitizer runs a test where three reader threads query and read stats while
a 20k-vector batch links, for both float and SQ8 indexes. It is clean.

## What I learned

- Write the adversarial test first. The one-by-one insert test found the quantizer bug in seconds.
- "Lock-free reads" and "concurrent writes" are compatible if the reader can cheaply tell which world it is in.
- Benchmark on the hardware people actually deploy on. On x86, Strata is ahead of both FAISS and hnswlib at every
  recall level, which is a different story from the Apple Silicon numbers.

Code: github.com/VividhDesign/strata · Design notes: `docs/DESIGN.md`
