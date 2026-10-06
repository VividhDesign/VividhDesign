# Draft: ECIR 2027 Reproducibility Track paper, built from Evident

**Working title:** *Do Hybrid Retrieval and Cross-Encoder Reranking Gains Transfer Out of Domain? A From-Scratch
Reproducibility Study on BEIR*

**Format:** ECIR reproducibility papers are LNCS, ~12 pages plus references (check the 2027 call).
**Venue fit:** the track asks for *reproduction*, then *generalisation* to new settings, which is exactly
what Evident already does.

---

## Abstract (draft, 180 words)

Hybrid lexical–dense retrieval and cross-encoder reranking are widely reported to improve retrieval quality, and both
are default components of retrieval-augmented generation (RAG) pipelines. We reproduce three claims from the
literature with an independent, from-scratch implementation: (i) a Lucene-style BM25 baseline on BEIR, (ii) the
BEIR BM25+cross-encoder results, and (iii) the claim that reciprocal rank fusion (RRF) is a robust, tuning-free
fusion method. Our BM25 matches Pyserini within ±0.002 nDCG@10 on SciFact, NFCorpus and FiQA, and our
BM25→MiniLM reranking matches the BEIR paper on two of three datasets; the third gap is explained by candidate depth.
Claim (iii) does not hold: when one retriever is much weaker (FiQA, BM25 0.238 vs dense 0.400), RRF falls *below*
dense-only retrieval (0.360), while a convex combination with α tuned on the dev split reaches 0.415. Two MS MARCO
cross-encoders fail to improve a tuned hybrid on any dataset at 30–170× the latency. We release code, run files and
per-query results.

## Research questions

- **RQ1 (reproduction):** Can a from-scratch BM25 reproduce Pyserini's published BEIR numbers?
  *Already answered:* 0.680/0.321/0.238 vs 0.679/0.322/0.236.
- **RQ2 (reproduction):** Do BEIR's BM25+CE numbers reproduce? *Answered for 2 of 3 datasets*; FiQA needs
  the top-100 run (see TODO 1).
- **RQ3 (generalisation):** Is RRF a safe default when the two retrievers differ a lot in strength?
  *Answered: no, on FiQA.* Strengthen it with more datasets (TODO 2).
- **RQ4 (generalisation):** Do MS MARCO-trained rerankers help *on top of a tuned hybrid* out of domain?
  *Answered: no, on 3 datasets.*
- **RQ5 (optional, RAG):** Does better retrieval change downstream answer faithfulness and abstention?
  You already have 100-question FiQA results with bootstrap CIs, including the negative "evidence removed" result.

## Section plan, mapped to existing material

| Section | Source in the repo | Status |
|---|---|---|
| 1 Introduction | README "Why" | rewrite in paper voice |
| 2 Original claims being reproduced | Kamalloo et al. 2023 (Pyserini BEIR), Thakur et al. 2021 (BEIR), Cormack et al. 2009 (RRF) | write |
| 3 Implementation (BM25, metrics, fusion, Strata HNSW) | `evident/bm25.py`, `metrics.py`, `fusion.py`, METHODOLOGY.md | mostly done |
| 4 Experimental setup | METHODOLOGY.md "Retrieval" | done |
| 5 RQ1–RQ2 results | `results/retrieval_*.json`, sanity-check table | done except FiQA top-100 |
| 6 RQ3–RQ4 results | README retrieval table | done; add CIs (TODO 3) |
| 7 RQ5 (RAG) | `results/generation_fiqa_*` | done |
| 8 Lessons and limitations | README "Limitations" | done |

## TODOs before submission (ordered by value)

1. **Rerank top-100 on FiQA** with MiniLM. This closes RQ2 (expected ≈0.347). One CLI run:
   change the rerank depth flag.
2. **Add 3–5 more BEIR datasets** (TREC-COVID, ArguAna, SCIDOCS, Touché-2020, Quora). These generalise RQ3 and RQ4.
   Pick at least one where BM25 beats dense (Touché, and sometimes TREC-COVID): RRF should *help* there, which makes
   the paper's message "RRF's value depends on the relative strength of the two retrievers", a nuanced and publishable result.
3. **Paired significance tests** per query (paired t-test or randomisation test, Holm–Bonferroni corrected) for
   every row against the tuned hybrid. Reviewers in this track expect them.
4. **α sensitivity plot:** nDCG@10 versus α on dev and test, per dataset. It shows how robust tuning is.
5. **A second dense model** (e.g. e5-small or bge-base) to show that the findings do not depend on the encoder.
6. **Release:** TREC run files plus a single `make reproduce` target.

## Related work to cite (verify each reference)

- Thakur et al. 2021, *BEIR* (NeurIPS Datasets & Benchmarks).
- Kamalloo et al. 2023, *Resources for Brewing BEIR: Reproducible Reference Models and an Official Leaderboard*
  (arXiv 2306.07471).
- Cormack, Clarke & Büttcher 2009, *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods* (SIGIR).
- Bruch, Gai & Ingber 2023, *An Analysis of Fusion Functions for Hybrid Retrieval* (ACM TOIS). This is the closest prior
  work: it also argues convex combination beats RRF. Position your paper as a from-scratch reproduction and extension of it.
- Lin et al., Pyserini (SIGIR 2021 resource).
- Malkov & Yashunin 2018, HNSW.

> **Important:** Bruch et al. 2023 overlaps with RQ3. Read it before writing and frame RQ3 as
> *independent confirmation in a full RAG setting, plus the reranker interaction*, not as a new discovery.
