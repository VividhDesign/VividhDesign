Keep exact-duplicate vectors reachable in HNSW

---

Fixes #ISSUE_NUMBER

## Summary

A group of identical vectors larger than the level-0 list (2M) fills each copy's list with other copies. Copies tie in
distance, so they never prune one another, and FAISS gives each new point 2M level-0 links where the HNSW paper gives
M. Reverse links from later points then lose to the tied copies. A search that reaches the group cannot leave it, and
some copies have no incoming edge at all.

With this change, a point that has an exact duplicate among its level-0 link targets takes `nb_neighbors(1)` (M)
forward links, as in the paper. An exact duplicate is a target whose distance to the point equals the point's
distance to itself. The other M slots of the point's list stay free for links from other points.

All other points are linked exactly as before. The rule is a helper, `nb_links_to_add`, used by both
`add_links_starting_from_impl` and `compute_forward_links_impl`. The helper scans a copy of the candidate queue, so
the order of tied candidates does not change.

## Results

**Duplicates** (`efSearch=1000`):

| | before | after |
|---|---|---|
| Script in the issue, M=32: copies found / results for k=300 | 135 / 135 | **200 / 300** |
| Script in the issue, M=16: copies found / results for k=300 | 166 / 300 | **200 / 300** |
| Script in the issue, M=16 / M=32: copies with in-degree 0 | 28 / 2 | **0 / 0** |
| 10,000 random 64-d vectors plus a group of 50 / 200 / 1,000 copies (M=16): copies found | 48 / 181 / 323 | **50 / 200 / 679** |
| Code corpus from the issue: duplicate chunks missed by a search for their own vector | 1,045 | **37** |
| Code corpus: searches for a duplicate returning fewer than 100 of `k=100` | 645 | **0** |

**No change without duplicates:**

- First 200,000 vectors of SIFT and of GloVe-100 (M=16, efConstruction=200): the level-0 neighbour arrays are
  byte-identical before and after (6,614,768 entries each).
- SIFT1M (M=16, efConstruction=200, 10,000 queries) contains 14,538 pairs of identical vectors, so the new rule
  applies to some points:

| efSearch | 16 | 32 | 64 | 128 | 256 |
|---|---|---|---|---|---|
| recall@10 before | 0.8075 | 0.9108 | 0.9675 | 0.9904 | 0.9973 |
| recall@10 after | 0.8066 | 0.9101 | 0.9675 | 0.9904 | 0.9973 |

- SIFT1M QPS was measured in one process, alternating the saved indexes, as the median of 5 runs. Before and after:
  11,342 / 11,050 at ef16, 3,959 / 3,926 at ef64, 2,079 / 2,165 at ef128 and 1,105 / 1,110 at ef256. The
  differences are within run-to-run noise and go both ways.
- SIFT1M build time: 147.7 s before, 149.9 s after.

## Alternatives measured

| Change | Copies found (M=16, 200 copies) | Duplicate-free data |
|---|---|---|
| Break ties by newest id in `merge_reverse_links_impl` | 37 (worse) | |
| Cap the share of copies in a list at M | 148 | |
| M level-0 links for every point | 200 | recall@10 at ef16 drops from 0.849 to 0.839 on SIFT-200k and from 0.614 to 0.594 on GloVe-200k |
| **This change** | **200** | byte-identical graphs |

## Tests

New `TestHNSWDuplicates` covers L2 at M=16 and M=32, and inner product at M=16. Both tests fail on `main` and pass
with the change. `tests/test_graph_based.py` and `tests/test_hnsw.py` pass (54 tests, including
`test_deterministic_build`).

## Limits

A group many times the list size still loses copies: with 1,000 copies at M=16, 679 are found (323 before). Groups of
any size would need a structural change, such as one node per distinct vector with id aliases.

Scripts for every number: https://github.com/VividhDesign/VividhDesign/tree/claude/great-wright-hjnt9y/contributions/faiss/scripts

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_017uaXZrSYSh1iMaFrDMbm4o
