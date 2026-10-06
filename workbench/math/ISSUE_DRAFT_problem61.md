**Where to post:** https://github.com/google-deepmind/alphaevolve_repository_of_problems/issues/new

**Title:** Problem 61 (ring loading): exact rational instance with alpha = 47/42, certifying C >= 47/42

---

**Summary.** The published AlphaEvolve construction for problem 61 (m = 15) has alpha ≈ 1.1190475684692776 in
floating point. Polishing it with linear programming lands on an exact vertex, and I give a rational instance whose
alpha is exactly **47/42 = 1.1190476190…**. It is verified in exact arithmetic over all 2^15 sign choices, so it
gives a rigorous lower bound **C >= 47/42**. This matches the AlphaEvolve value and does not improve it beyond
floating-point precision. The point is to have an exactly checkable certificate.

**Instance** (u_i, v_i >= 0, u_i + v_i <= 1):

```python
from fractions import Fraction as F
u = [F(33,35), F(19,42), F(10,21), F(1,3), F(11,42), F(25,84), F(16,21), F(1,2),
     F(5,42), F(59,84), F(5,21), F(2,3), F(3,7), F(23,42), F(23,210)]
v = [F(1,105), F(23,42), F(3,7), F(2,3), F(5,21), F(59,84), F(5,42), F(1,2),
     F(16,21), F(25,84), F(11,42), F(1,3), F(10,21), F(19,42), F(59,70)]
```

**Exact check** (same definition as the notebook's `compute_alpha_exact`, with fractions):

```python
def alpha_exact(u, v):
    m, best = len(u), None
    for bits in range(1 << m):
        z = [v[i] if (bits >> i) & 1 else -u[i] for i in range(m)]
        total, prefix, worst = sum(z), F(0), F(0)
        for k in range(1, m):
            prefix += z[k - 1]
            worst = max(worst, abs(2 * prefix - total))
        best = worst if best is None or worst < best else best
    return best

assert all(a >= 0 and b >= 0 and a + b <= 1 for a, b in zip(u, v))
print(alpha_exact(u, v))   # 47/42
```

The notebook's own `compute_alpha_exact`, run on the float values of this instance, returns 1.1190476190476188,
which is 47/42 up to rounding.

**How it was found.** I ran sequential linear programming on the published instance: at each step, take the sign
patterns within a small gap of the minimum, linearise each one's max at its current argmax, and solve an LP in a trust
region with HiGHS. It converges to 1.1190476190476190. I then rounded each coordinate with
`Fraction.limit_denominator(252)` and checked the result exactly as above.

**Other observations, in case they are useful:**
- Basin hopping around SLP at m = 15 and m = 17 (the latter by duplicating middle elements) found no instance above
  47/42 in about one CPU-hour.
- A cutting-plane MILP over sign patterns certifies that the best possible alpha is 1 for m = 4 and m = 5.

Code (SLP, basin hopping, MILP, exact verifier): https://github.com/VividhDesign/VividhDesign/tree/claude/beautiful-brahmagupta-pv082h/workbench/math/ringload.

**Disclosure.** The search code and this write-up were produced with an AI coding assistant (Claude Code) under my
direction. I checked the certificate, and the claim rests on the exact verification above.

— Vividh Yadav (github.com/VividhDesign)
