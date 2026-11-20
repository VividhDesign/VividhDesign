# annfuzz

**Property-based correctness tests for approximate-nearest-neighbour (ANN) libraries.**

Recall benchmarks such as ann-benchmarks ask how *often* an index finds the true neighbours. annfuzz asks whether
it ever breaks a rule no approximate method is allowed to break. It must not return ids that were never inserted,
report distances that are wrong for the ids it returns, or keep returning deleted entries. One bad row must not damage
searches for unrelated vectors, and no stored entry may become impossible to find. Each property is a metamorphic or
oracle check that holds for every correct index, whatever its recall.

One adapter per library maps it onto a five-call interface (`build`, `add`, `search`, and optionally `delete`,
`roundtrip`, `search_filtered`), so all libraries face the same checks.

```bash
pip install numpy hnswlib faiss-cpu voyager annoy pynndescent usearch   # whichever you want to test
python -m annfuzz                                  # every installed library, every metric
python -m annfuzz faiss --metric l2 --json out.json
python -m annfuzz strata --property nan_row_isolated
```

## Results (November 2026)

159 checks across 7 libraries and 3 metrics (L2, cosine, inner product): **16 findings in 5 libraries**, all
confirmed with standalone reproductions. A check runs only where the library has the feature (FAISS's HNSW index has
no delete, for example), so the count per library varies: 31 for hnswlib and Strata, 12 for FAISS. Raw results: [`results/2026-11-20.json`](results/2026-11-20.json).

| Library | Version | NaN row accepted and leaks into results | Identical vectors become unreachable | Other checks |
|---|---|---|---|---|
| hnswlib | 0.8.0 | ✗ returned in 72–91 of 200 top-10 lists | ✓ | ✓ |
| Voyager (Spotify) | 2.2.4 | ✗ same as hnswlib, which it builds on | ✓ | ✓ |
| FAISS `IndexHNSWFlat` | 1.16.0 | ✓ | ✗ 175 of 200 found; a query near the copies returns 154 results for k=300 | ✓ |
| USearch | 2.26.6 | ✗ unrelated self-matches drop 1000 → 697 | ✗ 130 of 200 found | ✓ |
| PyNNDescent | 0.7.0 | ✓ (refused) | ✗ 74 of 200 found (cosine, dot) | ✓ |
| Annoy (Spotify) | 1.17.3 | ✓ | ✓ | ✓ |
| Strata | 0.2.0 + fix | ✓ (was ✗ before the fix in this study) | ✓ | ✓ |

USearch 3.0.0-rc.1 was checked separately, because it shares a module name with 2.x. A NaN row costs 120 of 1,000
unrelated self-matches. A 400-key duplicate group has 88 keys unreachable. `values_per_key` is accepted but never
enforced. NumPy batches of no rows are refused.

### What the findings mean

**NaN rows.** A NaN component makes every distance to that row NaN, and NaN compares false both ways. Graph
construction orders candidates by distance, so one such row corrupts the neighbour selection around it. In hnswlib and
Voyager, the row then appears in 45–65% of unrelated queries' top-10, reported at distance `nan`. In USearch 2.x it
silently breaks 25–30% of other vectors' self-matches. Embedding pipelines do produce NaN, for example from a
zero-norm normalisation. FAISS and Annoy isolate it, PyNNDescent refuses it, and Strata now refuses it.

**Duplicate vectors.** Real corpora hold many identical embeddings: boilerplate, generated code, repeated chunks. With
identical vectors every distance ties, and HNSW-style pruning breaks ties arbitrarily. A new copy can lose every
reverse link and become unreachable, even with `ef` equal to the index size. In FAISS the duplicate cluster also
traps searches. Its copies' neighbour lists point only at one another, so a query at or near the duplicated
vector returns 154 results when asked for 300 (with `efSearch=1000` over 1,000 vectors), and its recall against exact
search is 0.51. Without the duplicates the same query returns all 300. In PyNNDescent the cause is different and precise. Rounding gives some identical
rows an `alternative_dot` distance of about −1.7e-7, and the search graph's `maximum`-style union drops one-directional
edges whose value is not positive. Most copies end up with no incoming edge at all. A one-line fix (preserve
non-positive distances like zero ones) removes every orphan in 24 of 24 tested configurations.

## Properties

| Property | Invariant |
|---|---|
| `results_are_valid` | Returned ids were inserted, are unique per query, are sorted, and their distances match brute force under the library's documented convention |
| `k_larger_than_size` | `k` above the index size returns each stored entry exactly once |
| `empty_and_tiny` | Empty and single-entry indexes answer sensibly |
| `duplicate_vectors_reachable` | Every key stored under an identical vector is found by a search as wide as the index |
| `nan_row_isolated` | A NaN row is refused, or at least leaves other searches unchanged and is never returned |
| `zero_vector_cosine` | A zero vector under cosine is refused or harmless |
| `save_load_roundtrip` | Saving and loading changes no result |
| `deleted_never_returned` | Deleted ids never come back, before or after save/load, and survivors stay findable |
| `readd_replaces_vector` | Re-adding an id replaces its vector instead of leaving a stale copy |
| `filter_only_allowed` | Filtered search returns only allowed ids, with reasonable recall at 50%, 5% and 0.5% selectivity |
| `low_connectivity_reachable` | Entries stay findable at small `M` with a wide beam |

Inner-product checks use unit-normalised data, because otherwise a longer vector can legitimately outscore a vector's
dot product with itself. Distance checks first identify which standard convention a library uses (squared L2, L2,
1 − cos, chord distance, dot), so a convention difference is never reported as a bug.

## Adding a library

Subclass `annfuzz.adapters.Adapter`. Set `metrics`, `convention` and the `can_*` flags, implement `build`, `add`
and `search` (padding missing results with −1), and append an instance to `ALL`.

## License

MIT
