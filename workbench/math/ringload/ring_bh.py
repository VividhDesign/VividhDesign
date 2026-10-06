"""Basin hopping around SLP for the ring loading lower bound.

Repeatedly perturbs a few elements of the best instance (or inserts/deletes an element to change m),
polishes with SLP, and keeps the result if the exact alpha improves. Writes the best instance
whenever it improves.

    python ring_bh.py --m 15 --init ring_m15_s0.json --seconds 3600 --seed 1
"""
import argparse
import json
import time

import numpy as np

from ring_slp import alpha_all, patterns, slp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m", type=int, required=True)
    ap.add_argument("--init", default=None)
    ap.add_argument("--seconds", type=float, default=600)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--symmetric", action="store_true")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    m = args.m
    B = patterns(m)
    if args.init:
        d = json.load(open(args.init))
        u, v = np.array(d["u"], float), np.array(d["v"], float)
        while len(u) < m:  # grow by duplicating a random element
            j = int(rng.integers(len(u)))
            u, v = np.insert(u, j, u[j]), np.insert(v, j, v[j])
        while len(u) > m:
            j = int(rng.integers(len(u)))
            u, v = np.delete(u, j), np.delete(v, j)
    else:
        u = rng.uniform(0, 1, m)
        v = 1 - u
    u, v, best = slp(u, v, B, iters=200, symmetric=args.symmetric)
    bu, bv = u.copy(), v.copy()
    print(f"m={m} seed={args.seed} start alpha={best:.12f}", flush=True)
    t0 = time.time()
    it = 0
    while time.time() - t0 < args.seconds:
        it += 1
        u, v = bu.copy(), bv.copy()
        k = int(rng.integers(1, max(2, m // 3) + 1))
        idx = rng.choice(m, size=k, replace=False)
        sigma = float(rng.choice([0.01, 0.03, 0.1, 0.3]))
        u[idx] = np.clip(u[idx] + rng.normal(0, sigma, k), 0, 1)
        v[idx] = np.clip(v[idx] + rng.normal(0, sigma, k), 0, 1)
        if rng.random() < 0.3:  # snap some elements onto u + v = 1
            j = rng.choice(idx)
            v[j] = 1 - u[j]
        if args.symmetric:
            v = u[::-1].copy()
        s = u + v
        over = s > 1
        u[over], v[over] = u[over] / s[over], v[over] / s[over]
        u, v, a = slp(u, v, B, iters=150, symmetric=args.symmetric)
        if a > best + 1e-10:
            best, bu, bv = a, u.copy(), v.copy()
            out = f"bh_m{m}_s{args.seed}.json"
            json.dump({"m": m, "alpha": best, "u": bu.tolist(), "v": bv.tolist()}, open(out, "w"), indent=1)
            print(f"IMPROVED m={m} seed={args.seed} it={it} alpha={best:.12f} t={time.time() - t0:.0f}s -> {out}", flush=True)
        if it % 25 == 0:
            print(f"m={m} seed={args.seed} it={it} best={best:.12f} t={time.time() - t0:.0f}s", flush=True)
    print(f"END m={m} seed={args.seed} best={best:.12f}")


if __name__ == "__main__":
    main()
