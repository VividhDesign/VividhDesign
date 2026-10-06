"""Independent checks for a problem-59 construction (no isosceles triangles in the n x n grid).

1. The repository's own verify_construction (copied verbatim from the problem-59 notebook):
   every ordered triple (a, b, c) of distinct points must satisfy |ab|^2 != |bc|^2.
2. A second O(k^2) implementation: for every apex b, all squared distances to other points
   must be distinct.
Also checks that all points are distinct integer points of [0, n-1]^2.

    python3 verify_59.py n points.txt
"""
import itertools
import sys
from math import sqrt


def dist_sq(p1, p2):
    """Calculates the squared Euclidean distance between two points."""
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2


def verify_construction(points):  # verbatim from the repository notebook
    for a, b, c in itertools.permutations(points, 3):
        if dist_sq(a, b) == dist_sq(b, c):
            d = sqrt(dist_sq(a, b))
            print("Verification FAILED: Found a forbidden isosceles configuration.")
            print(f"Points: a={a}, b={b}, c={c}")
            print(f"dist(a,b) = dist(b,c) = {d:.2f}")
            return False
    return True


def verify_fast(points):
    for b in points:
        seen = set()
        for a in points:
            if a == b:
                continue
            d = dist_sq(a, b)
            if d in seen:
                return False
            seen.add(d)
    return True


if __name__ == "__main__":
    n = int(sys.argv[1])
    pts = [tuple(map(int, line.split())) for line in open(sys.argv[2]) if line.strip()]
    assert len(set(pts)) == len(pts), "duplicate points"
    assert all(0 <= x < n and 0 <= y < n for x, y in pts), "point outside the grid"
    fast = verify_fast(pts)
    print(f"{len(pts)} points in the {n}x{n} grid; fast check: {fast}")
    full = verify_construction(pts)
    print(f"repository verify_construction: {full}")
    sys.exit(0 if (fast and full) else 1)
