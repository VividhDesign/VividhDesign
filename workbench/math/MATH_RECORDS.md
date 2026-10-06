# Open-problem record attempts: AlphaEvolve Repository of Problems

**Target:** [google-deepmind/alphaevolve_repository_of_problems](https://github.com/google-deepmind/alphaevolve_repository_of_problems).
This is the live list of 67 open problems from Georgiev, Gómez-Serrano, Tao and Wagner, *Mathematical exploration and
discovery at scale* (arXiv:2511.02864). It accepts improvements through GitHub issues and PRs, and credits outside
contributors by name. For example, problem 44 credits Robert Gerbicz and Fan Zheng.

**Outcome in one line:** no record was beaten today. I did produce one clean certificate you can submit (problem 61,
exact rational proof of C ≥ 47/42), plus local-optimality evidence for the current problem-59 records. I also built a
reusable toolkit: tabu search, symmetric iterated local search, an exhaustive (k,k+1)-swap certifier, and a SAT encoder.

## Problem 61: ring loading (open since Schrijver–Seymour–Winkler 1998)

Known bounds before AlphaEvolve: 11/10 ≤ C ≤ 13/10 (Skutella 2016; Däubel 2019). AlphaEvolve published an m = 15
instance with α ≈ 1.1190475684692776.

**What I found.**
1. AlphaEvolve's instance sits next to an exact vertex. Polishing it with sequential linear programming gives
   α = 1.119047619047619 = **47/42**. The published float is 5.1·10⁻⁸ below that.
2. **An exact rational instance with α = 47/42**, verified in exact `Fraction` arithmetic over all 2¹⁵ sign
   choices (`ringload/verify_61_exact.py ringload/ring_exact_47_42.json`):
   - u = [33/35, 19/42, 10/21, 1/3, 11/42, 25/84, 16/21, 1/2, 5/42, 59/84, 5/21, 2/3, 3/7, 23/42, 23/210]
   - v = [1/105, 23/42, 3/7, 2/3, 5/21, 59/84, 5/42, 1/2, 16/21, 25/84, 11/42, 1/3, 10/21, 19/42, 59/70]
   
   This turns AlphaEvolve's floating-point bound into a rigorous, checkable **C ≥ 47/42**. It matches their value
   and does not beat it.
3. Searching for more: basin hopping plus SLP at m = 15 and 17 (about 1 CPU-hour) found nothing above 47/42.
4. A cutting-plane MILP (HiGHS) certifies the optimum for small instances: α\*(4) = α\*(5) = 1. It stops scaling at m ≥ 6.

**Ready to post:** `ISSUE_DRAFT_problem61.md`.

## Problem 59: largest isosceles-free subsets of the n×n grid

Records: n = 64 → 112 and n = 100 → 164 (AlphaEvolve). n = 32 → 58 (hashkanna, issue #10, 4 Oct 2026; previously 56).

**Structural facts I established.**
- AlphaEvolve's 164-point n = 100 set is **exactly 4-fold mirror symmetric** (41 orbits about the centre). The 112-point
  n = 64 set is 108/112 symmetric, and a fully symmetric 112-point set also exists.
- 156 of the 164 points lie within 9 cells of the border.
- **Local optimality certificates.** No (k, k+1)-swap improves the records (remove k points or orbits, add k+1):

  | Set | Symmetry class searched | Verified up to |
  |---|---|---|
  | n=100, 164 (AlphaEvolve) | 4-fold orbits | (3,4)-swaps: all 10,660 triples of orbits |
  | n=100, 164 | mirror-in-x orbits | (2,3)-swaps |
  | n=100, 164 | no symmetry | (1,2)-swaps |
  | n=64, 112 (AlphaEvolve) | no symmetry | (2,3)-swaps: all 6,216 pairs |
  | n=32, 58 (hashkanna, set A and B) | mirror orbits | (6,7)-swaps: 475,020 subsets each |
  | n=32, 58 (set A and B) | no symmetry | (4,5)-swaps: 424,270 subsets each |

- **Large-neighbourhood search with exact SAT repair** (`lns_sat.py`): free a window near the border, fix all other
  points, and ask CaDiCaL for one more point inside it. Thousands of windows (up to 40×40 at n = 100) were proved
  unrepairable, and no improvement was found.
- So these records are deep local optima. Improving them needs a different basin, not a small edit.

**Tools (all in `isosceles/`).**
- `tabu.cpp`: k-fixed tabu search with exact incremental conflict tables. Pairs equidistant from a point lie on
  perpendicular bisectors (enumerated as lattice lines), and equal-distance legs lie on lattice circles
  (precomputed offsets). Add and remove scores are O(1) for all n² points.
- `sym.cpp` / `ils.cpp` / `ils2.cpp`: symmetric orbit search. ILS uses (1,2)-swaps in the style of
  Andrade–Resende–Werneck, with optional restriction to a border frame and strong perturbations.
- `swapk.cpp`: exhaustive (k, k+1)-swap certifier in 1-, 2- or 4-fold orbit spaces.
- `sat59.py`: SAT encoding (one 3-clause per equal-distance triple, plus a cardinality constraint) for CaDiCaL via
  PySAT. It is correct but slow for this problem: n = 16 without symmetry did not finish in 10 minutes.
- `verify_59.py`: the repository's own `verify_construction` (verbatim), plus an independent O(k²) check.

## Honest assessment

These problems are being attacked right now by teams with large compute (AlphaEvolve, ThetaEvolve, GigaEvo,
ImprovEvolve, OpenEvolve users). A few CPU-hours on 4 cores reproduced the records and certified that they are
locally optimal, but did not beat them. Three paths offer the best odds of a real record, and the toolkit supports
all of them:
1. **n = 100, problem 59**, with a long run (a day or more) of `ils2` from scratch and several border widths. The
   164 record's density (1.64·n) is well below the ~1.78·n seen at n = 16, 32, 64, so there is likely room.
2. **Ring loading with m ≥ 18**, using smarter initialisation, for example by concatenating copies of the 47/42 gadget.
3. **Sizes nobody has claimed**: problem 59 at n = 48, 80, 128 has no published value (per hashkanna's records file).
   A first result there is new, though less headline-worthy.
