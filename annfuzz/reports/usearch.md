# USearch: NaN rows and duplicate vectors (2.26.6 and 3.0.0-rc.1)

The 3.0 reports (NaN, `values_per_key`, integer-storage zeros, low connectivity on #815) and the PR for empty NumPy
batches are drafted in `contributions/ROUNDS1-2.md` and `contributions/ROUND3.md` on the VividhDesign session
branch. The 2.x numbers below support the NaN report, since most users are still on 2.x.

Copies of one vector: annfuzz's `duplicate_vectors_reachable` finds 130–131 of 200 copies with
`expansion_search=1000`. This is the known issue #815, so add a data point there rather than opening a new one.

NaN row, USearch 2.26.6 (`Index(ndim=16, metric="l2sq", dtype="f32")`, a NaN row inserted between two halves of
1,000 Gaussian rows): **694 of 1,000** rows still find themselves, against 1,000 without it. Under cosine it's
697 of 1,000. The NaN row is returned in 56–58 of 200 top-10 lists.
