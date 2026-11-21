# FAISS: keep exact-duplicate vectors reachable in HNSW

This folder holds a fix for `IndexHNSWFlat`. When a group of identical vectors grows larger than 2M, part of the group
becomes unreachable, and searches near it return fewer than `k` results.
- The issue and PR text, with all the evidence, is in
  [`annfuzz/reports/faiss-hnsw-duplicates.md`](../../annfuzz/reports/faiss-hnsw-duplicates.md).
- The background you need to explain the fix is in [`annfuzz/UNDERSTAND_THIS.md`](../../annfuzz/UNDERSTAND_THIS.md).

| File | What it is |
|---|---|
| `ISSUE.md`, `PR.md` | Paste-ready issue and PR text: the title, then `---`, then the body |
| `0001-Keep-exact-duplicate-vectors-reachable-in-HNSW.patch` | The fix and its tests, as a `git am` patch against FAISS `main` at `c11a75c` |
| `scripts/issue_snippet.py` | The reproducer from the issue (one second to run) |
| `scripts/inspect_snippet.py` | In-degree and outgoing edges of the copies in that index |
| `scripts/sample_links.py` | Shows FAISS's existing sink repair (`add_level_0_links_from_sample`) finds no sinks here |
| `scripts/experiment.py` | Synthetic, sweep, code-corpus and 200k regression measurements |
| `scripts/sift1m.py`, `save_sift.py`, `qps_ab.py` | SIFT1M recall, saved indexes and the alternating QPS comparison |
| `scripts/dump_graph.py`, `graph_identity.py` | Dump level-0 neighbour arrays and compare them byte for byte |
| `scripts/build_corpus_paragraphs.py` | Builds the paragraph-chunked code corpus |
| `scripts/inspect_graph.py`, `inspect_hnswlib.py` | The same graph inspection for FAISS and for hnswlib's saved index |
| `results/*.json` | Raw outputs. `base` and `reg_base` are unpatched. `final` is this patch. `ties`, `dupcap` and `ownM` are the rejected alternatives. |

## Submitting it

1. Sign the Meta CLA: https://code.facebook.com/cla
2. Fork `facebookresearch/faiss` on GitHub, then clone your fork.
3. Apply the patch and push it to a branch:

   ```bash
   git checkout -b hnsw-duplicate-links
   ```

   ```bash
   git am /path/to/0001-Keep-exact-duplicate-vectors-reachable-in-HNSW.patch
   ```

   ```bash
   git push -u origin hnsw-duplicate-links
   ```

4. Open the issue first, with the title and body from `ISSUE.md`.
5. Open the PR with `PR.md`. Replace `#ISSUE_NUMBER` with the new issue's number.
6. Before you open either one, run `scripts/issue_snippet.py` on your own build, so that you have seen the numbers
   yourself.

The commit message carries `Co-Authored-By` and `Claude-Session` trailers. FAISS has no AI-contribution policy, so
keep them; they disclose that the work was AI-assisted. Before you open the PR, check `CONTRIBUTING.md` again in case
the policy has changed.
