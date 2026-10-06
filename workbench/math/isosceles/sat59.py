"""Exact SAT search for isosceles-free subsets of the n x n grid (AlphaEvolve problem 59).

Variables are orbits of points under a chosen symmetry; every triple (a, b, c) with
|ab| = |bc| (b the apex, a != c) gives the clause (not a) or (not b) or (not c) on orbit variables;
a cardinality constraint asks for at least `target` points. SAT -> an explicit construction;
UNSAT -> no such set exists within that symmetry class.

    python sat59.py --n 32 --sym y --target 60 --seconds 3600
    sym: none | y (y -> n-1-y) | xy (both mirrors)
"""
import argparse
import itertools
import sys
import threading
import time
from collections import defaultdict

from pysat.card import CardEnc, EncType
from pysat.formula import CNF
from pysat.solvers import Solver


def orbits_for(n, sym):
    orbit_of = {}
    orbits = []
    for x in range(n):
        for y in range(n):
            if (x, y) in orbit_of:
                continue
            o = {(x, y)}
            if sym in ("y", "xy"):
                o.add((x, n - 1 - y))
            if sym == "xy":
                o |= {(n - 1 - x, y), (n - 1 - x, n - 1 - y)}
            pts = sorted(o)
            # an orbit must itself be isosceles-free
            ok = True
            for b in pts:
                ds = [(a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for a in pts if a != b]
                ok &= len(ds) == len(set(ds))
            idx = len(orbits)
            orbits.append(pts)
            for p in pts:
                orbit_of[p] = idx if ok else -1
            if not ok:
                orbits[idx] = None
    return orbits, orbit_of


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--sym", default="y")
    ap.add_argument("--target", type=int, required=True)
    ap.add_argument("--seconds", type=float, default=3600)
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--hint", default=None, help="file with a known valid set (used as phases)")
    args = ap.parse_args()
    n = args.n
    t0 = time.time()
    orbits, orbit_of = orbits_for(n, args.sym)
    var = {}
    for i, o in enumerate(orbits):
        if o is not None:
            var[i] = len(var) + 1
    pts = [(x, y) for x in range(n) for y in range(n) if orbit_of[(x, y)] >= 0]
    clauses = set()
    # For each apex b, group the other points by squared distance; every pair in a group is a triple.
    for b in pts:
        groups = defaultdict(list)
        for a in pts:
            if a != b:
                groups[(a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2].append(a)
        vb = var[orbit_of[b]]
        for g in groups.values():
            for a, c in itertools.combinations(g, 2):
                lits = {vb, var[orbit_of[a]], var[orbit_of[c]]}
                clauses.add(tuple(sorted(-l for l in lits)))
    weights = {var[i]: len(o) for i, o in enumerate(orbits) if o is not None}
    nv = len(var)
    # Cardinality on points: orbits of equal size -> count orbits.
    sizes = set(weights.values())
    cnf = CNF()
    for c in clauses:
        cnf.append(list(c))
    if len(sizes) == 1:
        s = sizes.pop()
        need = -(-args.target // s)
        card = CardEnc.atleast(lits=list(weights.keys()), bound=need, top_id=nv, encoding=EncType.seqcounter)
    else:
        from pysat.pb import PBEnc
        card = PBEnc.atleast(lits=list(weights.keys()), weights=[weights[v] for v in weights], bound=args.target, top_id=nv)
        need = args.target
    cnf.extend(card.clauses)
    print(f"n={n} sym={args.sym} target>={args.target} points: {nv} orbit vars, {len(clauses)} triple clauses, "
          f"{len(card.clauses)} cardinality clauses, encode {time.time() - t0:.1f}s", flush=True)

    solver = Solver(name=args.solver, bootstrap_with=cnf.clauses)
    if args.hint:
        hint = {tuple(map(int, l.split())) for l in open(args.hint) if l.strip()}
        phases = []
        for i, o in enumerate(orbits):
            if o is None:
                continue
            phases.append(var[i] if any(p in hint for p in o) else -var[i])
        try:
            solver.set_phases(phases)
        except Exception:
            pass
    timer = threading.Timer(args.seconds, lambda: solver.interrupt())
    timer.start()
    res = solver.solve_limited(expect_interrupt=True)
    timer.cancel()
    el = time.time() - t0
    if res is True:
        model = set(l for l in solver.get_model() if l > 0)
        chosen = [p for i, o in enumerate(orbits) if o is not None and var[i] in model for p in o]
        fn = f"sat_n{n}_{args.sym}_k{len(chosen)}.txt"
        with open(fn, "w") as f:
            for x, y in sorted(chosen):
                f.write(f"{x} {y}\n")
        print(f"SAT n={n} sym={args.sym}: found {len(chosen)} points in {el:.0f}s -> {fn}", flush=True)
    elif res is False:
        print(f"UNSAT n={n} sym={args.sym}: no set with >= {args.target} points in this symmetry class ({el:.0f}s)", flush=True)
    else:
        print(f"UNKNOWN n={n} sym={args.sym} target {args.target}: interrupted after {el:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
