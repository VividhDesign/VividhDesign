**Where to post:** as a comment on https://github.com/google-deepmind/alphaevolve_repository_of_problems/issues/10
(problem 59, the 58-point n = 32 sets). Post it only after checking the final numbers in `MATH_RECORDS.md`.

---

Some local-optimality data on the current problem-59 records, in case it helps whoever tries next. All checks use
exact integer arithmetic, and every reported set passes the notebook's `verify_construction`.

**Exhaustive (k, k+1)-swap search.** For every k-subset of the set (or of its symmetry orbits): remove it, collect
every grid point (orbit) that can then be added without creating an isosceles triple, and search those for k + 1
mutually compatible ones. No improvement exists in any of these neighbourhoods:

| Construction | Orbits | Exhausted up to | Subsets checked |
|---|---|---|---:|
| n = 100, 164 points (AlphaEvolve) | 4-fold (41 orbits about the centre; the set is exactly 4-fold symmetric) | (3,4) | 10,660 |
| n = 100, 164 points | mirror in x | (2,3) | 3,321 |
| n = 64, 112 points (AlphaEvolve) | none | (2,3) | 6,216 |
| n = 32, 58 points (set_a and set_b above) | mirror in y | (6,7) | 475,020 each |
| n = 32, 58 points | none | (4,5) | 424,270 |

**Large-neighbourhood search with exact repair.** Repeatedly freeing a rectangular window near the border, fixing all
other points, and asking a SAT solver (CaDiCaL) for one more point inside the window found no improvement: 47,818
windows of size up to 40 × 40 at n = 100, 8,984 up to 28 × 28 at n = 64, and over 10,000 up to 24 × 24 at n = 32 were proved
unrepairable.

Together these suggest the three records are deep local optima: an improvement would have to change a large part of the
configuration. Two structural observations: 156 of the 164 points at n = 100 lie within 9 cells of the border, and a fully
4-fold-symmetric 112-point set also exists at n = 64.

Code: ⟨link to your repo once pushed⟩ (`swapk.cpp`, `lns_sat.py`, `verify_59.py`).
Disclosure: the tools were written with an AI coding assistant (Claude Code) under my direction.

— Vividh Yadav (github.com/VividhDesign)
