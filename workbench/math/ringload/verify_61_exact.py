"""Exact check that an instance proves C >= 47/42 for the ring loading problem (AlphaEvolve problem 61).

For u, v with u_i, v_i >= 0 and u_i + v_i <= 1, alpha(u, v) = min over z in prod {v_i, -u_i} of
max_{1<=k<m} |sum_{i<=k} z_i - sum_{i>k} z_i|. All arithmetic uses exact fractions and all 2^m sign
choices are enumerated, so the printed value is exact.

    python3 verify_61_exact.py ring_exact_47_42.json
"""
import json
import sys
from fractions import Fraction


def alpha_exact(u, v):
    m = len(u)
    best = None
    for bits in range(1 << m):
        z = [v[i] if (bits >> i) & 1 else -u[i] for i in range(m)]
        total = sum(z)
        prefix = Fraction(0)
        worst = Fraction(0)
        for k in range(1, m):
            prefix += z[k - 1]
            worst = max(worst, abs(2 * prefix - total))
        if best is None or worst < best:
            best = worst
    return best


if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    u = [Fraction(x) for x in d["u"]]
    v = [Fraction(x) for x in d["v"]]
    assert len(u) == len(v)
    assert all(a >= 0 and b >= 0 and a + b <= 1 for a, b in zip(u, v)), "infeasible instance"
    a = alpha_exact(u, v)
    print(f"m = {len(u)}, alpha = {a} = {float(a):.15f}")
    print("certifies C >= 47/42:", a >= Fraction(47, 42))
