"""Large neighbourhood search with exact SAT repair for isosceles-free grid subsets (problem 59).

Repeat: choose a window W of the grid, delete the current points inside W, keep the outside points F
fixed, and ask a SAT solver for a set of points inside W of size |S ∩ W| + 1 such that F plus the new
points is still isosceles-free. Triples with two fixed points become unit clauses (the window point is
forbidden), triples with one fixed point become binary clauses, triples inside W stay ternary.
A SAT answer is a strictly larger valid set; UNSAT proves no such repair exists in that window.
Plateau moves (same size, different configuration) are taken occasionally to diversify.

    python lns_sat.py --n 100 --init ae_100.txt --seconds 3600 --seed 1
"""
import argparse
import random
import threading
import time
from collections import defaultdict

from pysat.card import CardEnc, EncType
from pysat.solvers import Solver


def d2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def valid(S):
    for b in S:
        seen = set()
        for a in S:
            if a == b:
                continue
            d = d2(a, b)
            if d in seen:
                return False
            seen.add(d)
    return True


def repair(n, S, window, need, timeout, rng, plateau=False):
    """Returns a new set (same outside, `need` points inside the window) or None."""
    F = [p for p in S if p not in window]
    Fset = set(F)
    # Candidates: window points not killed by two fixed points or a fixed pair.
    fixed_dists = {b: defaultdict(int) for b in F}
    for b in F:
        for a in F:
            if a != b:
                fixed_dists[b][d2(a, b)] += 1
    cand = []
    for p in window:
        if p in Fset:
            continue
        dead = False
        # p as a leg at fixed apex b: |bp| equal to |ba| for some other fixed a
        for b in F:
            if fixed_dists[b].get(d2(b, p), 0) > 0:
                dead = True
                break
        if dead:
            continue
        # p as apex: two fixed points at equal distance
        seen = set()
        for a in F:
            dd = d2(a, p)
            if dd in seen:
                dead = True
                break
            seen.add(dd)
        if not dead:
            cand.append(p)
    if len(cand) < need:
        return None, "few-candidates"
    var = {p: i + 1 for i, p in enumerate(cand)}
    clauses = set()
    C = cand
    # binary: two candidates p, q and one fixed point f forming a triple (any apex)
    for f in F:
        groups = defaultdict(list)  # apex f: candidates at equal distance from f
        for p in C:
            groups[d2(f, p)].append(p)
        for g in groups.values():
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    clauses.add((-var[g[i]], -var[g[j]]))
    for p in C:  # apex p (candidate): f and q equidistant, or q and r candidates
        groups = defaultdict(list)
        for f in F:
            groups[d2(p, f)].append(None)  # fixed marker
        for q in C:
            if q != p:
                groups[d2(p, q)].append(q)
        for g in groups.values():
            qs = [q for q in g if q is not None]
            nfixed = len(g) - len(qs)
            if nfixed >= 1:
                for q in qs:  # fixed + q at equal distance from apex p
                    clauses.add(tuple(sorted((-var[p], -var[q]))))
            for i in range(len(qs)):
                for j in range(i + 1, len(qs)):
                    clauses.add(tuple(sorted((-var[p], -var[qs[i]], -var[qs[j]]))))
    for q in C:  # apex q candidate, legs p candidate and f fixed handled above; apex fixed handled above
        pass
    card = CardEnc.atleast(lits=list(var.values()), bound=need, top_id=len(var), encoding=EncType.seqcounter)
    s = Solver(name="cadical195", bootstrap_with=list(clauses) + card.clauses)
    if plateau:  # random phases for diversity
        s.set_phases([v if rng.random() < 0.3 else -v for v in var.values()])
    timer = threading.Timer(timeout, lambda: s.interrupt())
    timer.start()
    res = s.solve_limited(expect_interrupt=True)
    timer.cancel()
    if res is True:
        model = set(l for l in s.get_model() if l > 0)
        new_in = [p for p in C if var[p] in model]
        s.delete()
        return F + new_in, "sat"
    s.delete()
    return None, "unsat" if res is False else "timeout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--init", required=True)
    ap.add_argument("--seconds", type=float, default=3600)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--wmin", type=int, default=8)
    ap.add_argument("--wmax", type=int, default=22)
    ap.add_argument("--timeout", type=float, default=20)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    n = args.n
    S = [tuple(map(int, l.split())) for l in open(args.init) if l.strip()]
    assert valid(S)
    best = len(S)
    print(f"n={n} start {best} points", flush=True)
    t0 = time.time()
    it = stats = 0
    counts = defaultdict(int)
    while time.time() - t0 < args.seconds:
        it += 1
        # Window: a rectangle touching the border band (most points live there), sometimes anywhere.
        w = rng.randint(args.wmin, args.wmax)
        h = rng.randint(args.wmin // 2, args.wmax)
        if rng.random() < 0.5:
            w, h = h, w
        x0 = rng.randint(0, n - w)
        y0 = rng.randint(0, n - h)
        side = rng.random()
        if side < 0.2:
            y0 = 0
        elif side < 0.4:
            y0 = n - h
        elif side < 0.6:
            x0 = 0
        elif side < 0.8:
            x0 = n - w
        window = {(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)}
        inside = sum(1 for p in S if p in window)
        plateau = rng.random() < 0.15
        need = inside if plateau else inside + 1
        if need == 0:
            continue
        new, status = repair(n, S, window, need, args.timeout, rng, plateau=plateau)
        counts[status] += 1
        if new is not None:
            if not valid(new):
                print("BUG: invalid repair", flush=True)
                continue
            S = new
            if len(S) > best:
                best = len(S)
                fn = f"lns_n{n}_k{best}_s{args.seed}.txt"
                with open(fn, "w") as f:
                    for x, y in sorted(S):
                        f.write(f"{x} {y}\n")
                print(f"RECORD-CANDIDATE n={n}: {best} points (window {w}x{h} at {x0},{y0}) t={time.time() - t0:.0f}s -> {fn}", flush=True)
        if it % 20 == 0:
            print(f"n={n} seed={args.seed} it={it} size={len(S)} best={best} {dict(counts)} t={time.time() - t0:.0f}s", flush=True)
    print(f"END n={n} seed={args.seed} best={best} {dict(counts)}")


if __name__ == "__main__":
    main()
