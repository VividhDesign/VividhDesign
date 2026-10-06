# Application kit (drafts; edit them in your own voice before sending)

Every claim below comes from your public repos and profile README. Numbers marked † come from today's x86 runs
in this workbench, so they only hold once you merge the Strata patches and push.

---

## Resume bullets

**Strata: vector database in C++17** · github.com/VividhDesign/strata
- Built an HNSW vector database from scratch: NEON/AVX2 SIMD kernels, parallel lock-light construction
  with 1-byte per-node spinlocks, WAL + CRC-checked snapshots with crash recovery, REST server, and Python bindings.
- Matches FAISS and runs 1.9× faster than hnswlib at equal recall on SIFT1M (Apple M5 Pro). On x86 it is ahead of
  both at every recall level on GloVe-6B 100-d.†
- Added 8-bit scalar quantization with exact re-ranking and memory-mapped re-rank vectors. Same recall as float32;
  3.5× the single-thread QPS of FAISS HNSW-SQ8 at recall 0.90, and builds 2× faster.†
- Made inserts non-blocking for readers. During a 100k-vector insert, p99 query latency went from 18.4 s
  (blocked) to 0.46 ms, with insert throughput unchanged. Verified with ThreadSanitizer.†

**Evident: RAG with careful evaluation** · github.com/VividhDesign/evident
- Hybrid BM25 + dense retrieval with a from-scratch BM25 that reproduces Pyserini within ±0.002 nDCG@10 on 3 BEIR datasets.
- Showed that RRF fusion *hurts* when one retriever is much weaker (FiQA 0.360 vs dense 0.400) and that tuned convex
  fusion fixes it (0.415). MS MARCO cross-encoders failed to beat the tuned hybrid at 30–170× the latency.
- LLM-as-judge harness with claim-level faithfulness, citation precision, and paired-bootstrap 95% CIs.

**Research**: *A transformer-based architecture for pre-impact fall detection with highly imbalanced data*,
14th IEEE ISED 2026 (wearable IMU time series, KFall).

**Open source**: merged fixes in sktime (#11370, median metrics with list `horizon_weight`) and USearch
(#793, `compact()` corrupted key→slot tables). Regression test PR for USearch #794.

---

## Weaviate internship: cover note (≈200 words)

> Hi Weaviate team,
>
> I'm a final-year AI & ML student at BIT Mesra, and for the past months I've been building the thing you build: a
> vector database. Strata (github.com/VividhDesign/strata) is an HNSW engine I wrote from scratch in C++17. It has
> SIMD distance kernels, parallel graph construction with per-node spinlocks, a write-ahead log with crash
> recovery, and a REST server. On SIFT1M it matches FAISS and is 1.9× faster than hnswlib at equal recall.
>
> Most recently I added 8-bit quantization with exact re-ranking. The re-rank vectors can stay memory-mapped
> on disk. I also made inserts stop blocking queries: p99 latency during a large insert dropped from seconds to
> under half a millisecond. Before that, I fixed a `compact()` bug in USearch that silently corrupted the key
> lookup tables.
>
> On the retrieval side, my RAG project Evident measures every stage. Its BM25 reproduces Pyserini within ±0.002,
> and it showed that RRF can make hybrid search *worse* than dense alone when one retriever is weak.
>
> I'd love to work on Weaviate's indexing or quantization (your RQ/BQ work is close to what I've been
> exploring). Thank you for considering me.
>
> Vividh

---

## Cold email: MSR India Research Fellow / Google DeepMind India pre-doc

> **Subject:** Research Fellow application: vector search systems + time-series ML (B.Tech '27, BIT Mesra)
>
> Dear Dr. ⟨name⟩,
>
> I read your work on ⟨one specific paper of theirs: DiskANN / Filtered-DiskANN for MSR India's systems group⟩
> and I'm applying to the Research Fellow program, hoping to work with your group.
>
> Two things I've done that seem relevant:
> 1. **Strata**, a from-scratch HNSW vector database in C++ (SIMD, concurrent construction, WAL durability,
>    8-bit quantization with on-disk re-rank vectors). It matches FAISS on SIFT1M.
> 2. A paper at IEEE ISED 2026 on transformer models for pre-impact fall detection under heavy class imbalance.
>
> I also measure things carefully: my RAG system's BM25 reproduces Pyserini within ±0.002 nDCG on BEIR. I'd value
> 15 minutes of your time, or simply your consideration of my application.
>
> Best regards, Vividh · github.com/VividhDesign
>
> *(Personalise the first line for every recipient. MSR India's DiskANN team works on exactly the
> memory-vs-disk trade-off that your mmap re-rank feature touches.)*

---

## GSoC 2027 with sktime: how to prepare (Nov–Mar)

1. Keep landing PRs. Aim for 3–5 merged by March, including one non-trivial estimator or bug fix in forecasting.
2. sktime publishes its project ideas around February. A natural fit for you is **foundation-model forecasters
   and deep-learning time-series classifiers**, since your ISED paper is a transformer for IMU time series.
3. Draft your proposal in the sktime mentoring repo format early, and ask mentors for feedback in their Discord.
