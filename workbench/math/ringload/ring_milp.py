"""Certified optimal ring loading instances for fixed m, by MILP with lazy sign patterns.

max  a
s.t. for every sign pattern b in W:   OR_{k, s}  s * S_k(b; u, v) >= a      (big-M with binaries)
     u, v >= 0, u_i + v_i <= 1
W starts small; after each solve we compute the exact alpha of the solution over all 2^m patterns
and add the worst patterns. The MILP optimum is an upper bound on max alpha for this m (it only
enforces some patterns); when it matches the exact alpha of its own solution, that instance is a
certified optimum for m.

    python ring_milp.py --m 8
"""
import argparse
import json
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from ring_slp import alpha_all, patterns


def solve(m, W, B, a_max=1.5, time_limit=600, symmetric=False):
    nW = len(W)
    K = m - 1
    nx = 2 * m
    ny = nW * K * 2
    n = nx + 1 + ny  # x, a, y
    M = a_max + m + 1.0
    rows, lo, hi = [], [], []
    sign = lambda k: np.where(np.arange(m) <= k, 1.0, -1.0)
    for w, bi in enumerate(W):
        b = B[bi]
        for k in range(K):
            sg = sign(k)
            g = np.concatenate([np.where(b == 0, -sg, 0.0), np.where(b == 1, sg, 0.0)])  # dS_k/dx
            for si, s in enumerate((1.0, -1.0)):
                # y = 1 activates  s*g.x >= a :   s*g.x - a >= -M*(1-y)  ->  s*g.x - a - M*y >= -M
                r = np.zeros(n)
                r[:nx] = s * g
                r[nx] = -1.0
                r[nx + 1 + (w * K + k) * 2 + si] = -M
                rows.append(r); lo.append(-M); hi.append(np.inf)
        r = np.zeros(n)
        r[nx + 1 + w * K * 2: nx + 1 + (w + 1) * K * 2] = 1.0
        rows.append(r); lo.append(1.0); hi.append(np.inf)
    for i in range(m):  # u_i + v_i <= 1
        r = np.zeros(n); r[i] = 1; r[m + i] = 1
        rows.append(r); lo.append(-np.inf); hi.append(1.0)
    if symmetric:
        for i in range(m):
            r = np.zeros(n); r[m + i] = 1; r[m - 1 - i] = -1
            rows.append(r); lo.append(0.0); hi.append(0.0)
    c = np.zeros(n); c[nx] = -1.0
    integrality = np.zeros(n); integrality[nx + 1:] = 1
    lb = np.zeros(n); ub = np.ones(n); ub[nx] = a_max; lb[nx] = 0
    res = milp(c, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integrality,
               bounds=Bounds(lb, ub), options={"time_limit": time_limit, "disp": False})
    if res.x is None:
        return None, None, None, res
    x = res.x
    return x[:m], x[m:2 * m], x[nx], res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m", type=int, required=True)
    ap.add_argument("--symmetric", action="store_true")
    ap.add_argument("--add", type=int, default=8, help="patterns added per round")
    ap.add_argument("--rounds", type=int, default=200)
    ap.add_argument("--time_limit", type=float, default=600)
    args = ap.parse_args()
    m = args.m
    B = patterns(m)
    # start with the all-v, all-u and alternating patterns
    W = [0, len(B) - 1, int("01" * (m // 2) + "0" * (m % 2), 2) % len(B)]
    best_lb = (0.0, None, None)
    t0 = time.time()
    for rnd in range(args.rounds):
        u, v, ub, res = solve(m, W, B, time_limit=args.time_limit, symmetric=args.symmetric)
        if u is None:
            print("MILP failed:", res.message); break
        u = np.clip(u, 0, 1); v = np.clip(v, 0, 1)
        s = u + v; over = s > 1; u[over] /= s[over]; v[over] /= s[over]
        F, _, _ = alpha_all(u, v, B)
        a = F.min()
        if a > best_lb[0]:
            best_lb = (a, u.copy(), v.copy())
        gap = ub - best_lb[0]
        print(f"m={m} round {rnd}: |W|={len(W)} MILP upper bound {ub:.6f}  exact alpha of solution {a:.6f}  best lower {best_lb[0]:.6f}  ({res.message.split('.')[0]}) t={time.time() - t0:.0f}s", flush=True)
        if gap <= 1e-7 and res.status == 0:
            print(f"CERTIFIED m={m}: max alpha = {best_lb[0]:.10f}")
            break
        order = np.argsort(F)
        added = 0
        for bi in order:
            if bi not in W:
                W.append(int(bi)); added += 1
                if added >= args.add:
                    break
    a, u, v = best_lb
    json.dump({"m": m, "alpha": a, "u": u.tolist(), "v": v.tolist(), "symmetric": args.symmetric},
              open(f"milp_m{m}{'_sym' if args.symmetric else ''}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
