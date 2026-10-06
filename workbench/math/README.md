# Search tools for AlphaEvolve's Repository of Problems

Tools and certificates from attacking two problems of
[google-deepmind/alphaevolve_repository_of_problems](https://github.com/google-deepmind/alphaevolve_repository_of_problems)
(Georgiev, Gómez-Serrano, Tao, Wagner, *Mathematical exploration and discovery at scale*, arXiv:2511.02864).
Results and an honest summary are in [MATH_RECORDS.md](MATH_RECORDS.md).

To publish this as its own repository (e.g. `VividhDesign/open-problem-search`), copy this folder and push it.

## Problem 61: ring loading

| File | What it does |
|---|---|
| `ringload/ring_exact_47_42.json` | Rational instance with alpha = 47/42 (C >= 47/42) |
| `ringload/verify_61_exact.py` | Exact check over all 2^m sign choices with `fractions.Fraction` |
| `ringload/ring_slp.py` | Sequential linear programming (HiGHS) on the max-min objective |
| `ringload/ring_bh.py` | Basin hopping around SLP |
| `ringload/ring_milp.py` | Cutting-plane MILP over sign patterns: certified optima for small m |

```bash
pip install numpy scipy
python3 ringload/verify_61_exact.py ringload/ring_exact_47_42.json     # alpha = 47/42
python3 ringload/ring_slp.py --m 15 --init <instance.json>             # polish an instance
```

## Problem 59: isosceles-free subsets of the n x n grid

| File | What it does |
|---|---|
| `isosceles/tabu.cpp` | k-fixed tabu search; exact O(1) add/remove scores via bisector-line and lattice-circle tables |
| `isosceles/sym.cpp`, `ils.cpp`, `ils2.cpp` | Search over mirror orbits; ILS with (1,2)-swaps, border-frame restriction |
| `isosceles/swapk.cpp` | Exhaustive (k, k+1)-swap certifier in 1-, 2- or 4-fold orbit spaces |
| `isosceles/lns_sat.py` | Large neighbourhood search with exact SAT repair (CaDiCaL via PySAT) |
| `isosceles/sat59.py` | Full SAT encoding with symmetry and a cardinality constraint |
| `isosceles/verify_59.py` | The repository's `verify_construction` (verbatim) plus an O(k^2) check |

```bash
g++ -O3 -march=native -std=c++17 isosceles/swapk.cpp -o swapk
./swapk 100 99 99 4 3 sol_100.txt        # all (3,4)-swaps of 4-fold orbits around a 100x100 set
pip install python-sat && python3 isosceles/lns_sat.py --n 100 --init sol_100.txt --seconds 3600
```

Point files are plain text with one `x y` per line (0-based).

## Licence

Apache-2.0, matching the upstream repository's code licence.
