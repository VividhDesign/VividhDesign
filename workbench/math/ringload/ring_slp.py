"""Lower bounds for the ring loading constant (AlphaEvolve repository, problem 61).

An instance is u, v in [0,1]^m with u_i + v_i <= 1. For signs b in {0,1}^m let z_i = v_i (b_i = 1)
or -u_i (b_i = 0) and S_k = sum_{i<=k} z_i - sum_{i>k} z_i. Then
    alpha(u, v) = min_b max_{1<=k<m} |S_k|,
and every instance proves C >= alpha(u, v). We maximise alpha by sequential linear programming:
at the current point take the near-minimising sign patterns, linearise each one's max at its
current argmax (k, sign), and solve an LP for the best step inside a trust region. Each step is
accepted only if the exact alpha (all 2^m patterns) increases.

    python ring_slp.py --m 15 --init ae_ring.json --iters 400
    python ring_slp.py --m 17 --restarts 20
"""
import argparse
import json
import time

import numpy as np
from scipy.optimize import linprog


def patterns(m):
    b = ((np.arange(1 << m)[:, None] >> np.arange(m)) & 1).astype(np.int8)
    return b


def alpha_all(u, v, B):
    """Per-pattern F_b = max_k |S_k|, plus argmax k and its sign."""
    Z = np.where(B == 1, v[None, :], -u[None, :])
    T = Z.sum(1)
    P = np.cumsum(Z, axis=1)[:, :-1]
    S = 2 * P - T[:, None]
    A = np.abs(S)
    k = A.argmax(1)
    F = A[np.arange(len(B)), k]
    s = np.sign(S[np.arange(len(B)), k])
    return F, k, s


def coeffs(b, k, s, m):
    """Gradient of s * S_k(b) with respect to x = (u_1..u_m, v_1..v_m) (k is 0-based: S_{k+1})."""
    sign = np.where(np.arange(m) <= k, 1.0, -1.0)
    cu = np.where(b == 0, -sign, 0.0)
    cv = np.where(b == 1, sign, 0.0)
    return s * np.concatenate([cu, cv])


def slp(u, v, B, iters=300, delta=0.05, active_gap=0.02, max_active=4000, symmetric=False, verbose=False):
    m = len(u)
    F, k, s = alpha_all(u, v, B)
    best = F.min()
    for it in range(iters):
        gap = max(active_gap, 4 * m * delta)
        act = np.where(F <= best + gap)[0]
        if len(act) > max_active:
            act = act[np.argsort(F[act])[:max_active]]
        G = np.array([coeffs(B[i], k[i], s[i], m) for i in act])
        # LP over (x, t): maximise t s.t. t - G x <= 0, trust region, u_i + v_i <= 1.
        x0 = np.concatenate([u, v])
        n = 2 * m
        c = np.zeros(n + 1)
        c[-1] = -1.0
        A_ub = [np.hstack([-G, np.ones((len(act), 1))])]
        b_ub = [np.zeros(len(act))]
        A_ub.append(np.hstack([np.eye(m), np.eye(m), np.zeros((m, 1))]))
        b_ub.append(np.ones(m))
        A_eq = None
        b_eq = None
        if symmetric:  # v_i = u_{m-1-i}
            rows = []
            for i in range(m):
                r = np.zeros(n + 1)
                r[m + i] = 1.0
                r[m - 1 - i] -= 1.0
                rows.append(r)
            A_eq = np.array(rows)
            b_eq = np.zeros(m)
        bounds = [(max(0.0, x0[j] - delta), min(1.0, x0[j] + delta)) for j in range(n)] + [(None, None)]
        res = linprog(c, A_ub=np.vstack(A_ub), b_ub=np.concatenate(b_ub), A_eq=A_eq, b_eq=b_eq,
                      bounds=bounds, method="highs")
        if res.status != 0:
            delta *= 0.5
            if delta < 1e-9:
                break
            continue
        x1 = np.clip(res.x[:n], 0.0, 1.0)
        u1, v1 = x1[:m], x1[m:]
        over = u1 + v1 > 1.0
        if over.any():
            sc = (u1 + v1)[over]
            u1[over] /= sc
            v1[over] /= sc
        F1, k1, s1 = alpha_all(u1, v1, B)
        a1 = F1.min()
        if a1 > best + 1e-12:
            u, v, F, k, s, best = u1, v1, F1, k1, s1, a1
            delta = min(delta * 1.5, 0.2)
        else:
            delta *= 0.5
            if delta < 1e-9:
                break
        if verbose and it % 20 == 0:
            print(f"  it {it} alpha={best:.10f} delta={delta:.2e} active={len(act)}", flush=True)
    return u, v, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m", type=int, default=15)
    ap.add_argument("--init", default=None)
    ap.add_argument("--restarts", type=int, default=1)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--symmetric", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    m = args.m
    B = patterns(m)
    overall = (-1.0, None, None)
    t0 = time.time()
    for r in range(args.restarts):
        if args.init and r == 0:
            d = json.load(open(args.init))
            u, v = np.array(d["u"], float), np.array(d["v"], float)
            if len(u) != m:  # insert a (0.5, 0.5) element in the middle to change m
                while len(u) < m:
                    mid = len(u) // 2
                    u = np.insert(u, mid, 0.5)
                    v = np.insert(v, mid, 0.5)
                u, v = u[:m], v[:m]
        else:
            u = rng.uniform(0, 1, m)
            v = 1.0 - u if rng.random() < 0.8 else rng.uniform(0, 1, m) * (1 - u)
            if args.symmetric:
                v = u[::-1].copy()
                over = u + v > 1
                u[over] /= (u + v)[over]
                v = u[::-1].copy()
        u, v, a = slp(u, v, B, iters=args.iters, symmetric=args.symmetric)
        print(f"m={m} restart {r}: alpha={a:.10f} (best {max(a, overall[0]):.10f}) t={time.time() - t0:.0f}s", flush=True)
        if a > overall[0]:
            overall = (a, u.copy(), v.copy())
    a, u, v = overall
    out = args.out or f"ring_m{m}_s{args.seed}.json"
    json.dump({"m": m, "alpha": a, "u": u.tolist(), "v": v.tolist()}, open(out, "w"), indent=1)
    print(f"BEST m={m} alpha={a:.12f} -> {out}")


if __name__ == "__main__":
    main()
