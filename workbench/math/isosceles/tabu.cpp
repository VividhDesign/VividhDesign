// Largest subsets of the n x n grid with no isosceles triangle (AlphaEvolve repository, problem 59).
//
// A set S is valid iff no b in S has two other points of S at equal distance. We search for
// valid sets of fixed size k with tabu search on the number of violations
//   V(S) = #{(b, {a, c}) : a, b, c in S distinct, |ab| = |bc|}.
// For every grid point v we maintain, exactly and incrementally:
//   P[v] = #{ {a, c} subset of S \ {v} : |va| = |vc| }  (pairs whose perpendicular bisector hits v)
//   A[v] = sum_{b in S, b != v} #{ a in S, a != b : |ba| = |bv| }  (circles around b through v)
// Then adding v (not in S) creates P[v] + A[v] violations, and removing u (in S) destroys
// P[u] + A[u] - (|S| - 1). Bisectors are enumerated as lattice lines, circles from a table of
// lattice offsets per squared radius.
//
//   ./tabu n k seed seconds [init_file]      (init file: lines "x y")

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <random>
#include <string>
#include <vector>

static int n, N, D;
static std::vector<std::vector<std::pair<int, int>>> offsets;  // squared radius -> lattice offsets
static std::vector<int> P, A;
static std::vector<char> inS;
static std::vector<int> members;   // points of S
static std::vector<int> pos;       // index in members, or -1

static inline int sq(int p, int q) {
  const int dx = p % n - q % n, dy = p / n - q / n;
  return dx * dx + dy * dy;
}

// Every grid point v on the perpendicular bisector of p, q gets P[v] += s.
static void bisector(int p, int q, int s) {
  const int px = p % n, py = p / n, qx = q % n, qy = q / n;
  const int wx = qx - px, wy = qy - py;
  const long c = (long)qx * qx + (long)qy * qy - (long)px * px - (long)py * py;  // 2 v.w = c
  if (wy != 0) {
    const long den = 2L * wy;
    for (int vx = 0; vx < n; ++vx) {
      const long num = c - 2L * vx * wx;
      if (num % den) continue;
      const long vy = num / den;
      if (vy >= 0 && vy < n) P[vy * n + vx] += s;
    }
  } else {
    const long den = 2L * wx;
    if (c % den) return;
    const long vx = c / den;
    if (vx < 0 || vx >= n) return;
    for (int vy = 0; vy < n; ++vy) P[vy * n + vx] += s;
  }
}

// Every grid point v != b with |bv|^2 = d gets A[v] += s.
static void circle(int b, int d, int s) {
  const int bx = b % n, by = b / n;
  for (const auto& [dx, dy] : offsets[d]) {
    const int x = bx + dx, y = by + dy;
    if (x >= 0 && x < n && y >= 0 && y < n) A[y * n + x] += s;
  }
}

static void add_point(int p) {
  for (int b : members) {
    bisector(p, b, +1);
    circle(b, sq(b, p), +1);  // p joins b's distance class
    circle(p, sq(p, b), +1);  // new apex p: b's class around p
  }
  inS[p] = 1;
  pos[p] = (int)members.size();
  members.push_back(p);
}

static void remove_point(int u) {
  const int i = pos[u];
  members[i] = members.back();
  pos[members[i]] = i;
  members.pop_back();
  pos[u] = -1;
  inS[u] = 0;
  for (int b : members) {
    bisector(u, b, -1);
    circle(b, sq(b, u), -1);
    circle(u, sq(u, b), -1);
  }
}

static long violations() {
  long v = 0;
  for (int u : members) v += P[u];
  return v;
}

static bool verify(const std::vector<int>& S) {
  std::vector<int> seen(D + 1, -1);
  for (size_t i = 0; i < S.size(); ++i) {
    for (size_t j = 0; j < S.size(); ++j) {
      if (i == j) continue;
      const int d = sq(S[i], S[j]);
      if (seen[d] == (int)i) return false;
      seen[d] = (int)i;
    }
  }
  return true;
}

int main(int argc, char** argv) {
  n = std::atoi(argv[1]);
  int k = std::atoi(argv[2]);
  const unsigned seed = (unsigned)std::atoi(argv[3]);
  const double seconds = std::atof(argv[4]);
  N = n * n;
  D = 2 * (n - 1) * (n - 1);
  offsets.assign(D + 1, {});
  for (int dx = -(n - 1); dx <= n - 1; ++dx)
    for (int dy = -(n - 1); dy <= n - 1; ++dy)
      if (dx || dy) offsets[dx * dx + dy * dy].push_back({dx, dy});
  P.assign(N, 0);
  A.assign(N, 0);
  inS.assign(N, 0);
  pos.assign(N, -1);
  std::mt19937_64 rng(seed);

  if (argc > 5) {
    std::ifstream in(argv[5]);
    int x, y;
    while (in >> x >> y) add_point(y * n + x);
    std::fprintf(stderr, "init %zu points, V=%ld\n", members.size(), violations());
  }
  // Fill up to k greedily (least damage first).
  while ((int)members.size() < k) {
    int best = -1, bs = 1 << 30, ties = 0;
    for (int v = 0; v < N; ++v) {
      if (inS[v]) continue;
      const int s = P[v] + A[v];
      if (s < bs) { bs = s; best = v; ties = 1; }
      else if (s == bs && rng() % (++ties) == 0) best = v;
    }
    add_point(best);
  }

  std::vector<long> tabu_add(N, 0), tabu_rem(N, 0);
  long V = violations(), bestV = V, it = 0;
  int best_valid = 0;
  const auto t0 = std::chrono::steady_clock::now();
  auto elapsed = [&] { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };
  while (elapsed() < seconds) {
    ++it;
    if (V == 0) {
      std::vector<int> S = members;
      if (!verify(S)) { std::fprintf(stderr, "BUG: verify failed\n"); return 2; }
      if ((int)S.size() > best_valid) {
        best_valid = (int)S.size();
        std::string fn = "sol_n" + std::to_string(n) + "_k" + std::to_string(S.size()) + "_s" + std::to_string(seed) + ".txt";
        FILE* f = std::fopen(fn.c_str(), "w");
        for (int p : S) std::fprintf(f, "%d %d\n", p % n, p / n);
        std::fclose(f);
        std::printf("FOUND n=%d k=%zu seed=%u it=%ld t=%.1fs -> %s\n", n, S.size(), seed, it, elapsed(), fn.c_str());
        std::fflush(stdout);
      }
      // Grow: add the least damaging point.
      int best = -1, bs = 1 << 30, ties = 0;
      for (int v = 0; v < N; ++v) {
        if (inS[v]) continue;
        const int s = P[v] + A[v];
        if (s < bs) { bs = s; best = v; ties = 1; }
        else if (s == bs && rng() % (++ties) == 0) best = v;
      }
      add_point(best);
      V += bs;
      bestV = V;
      continue;
    }
    const int m = (int)members.size();
    // Remove: the most involved point not protected by tabu (random walk with small prob).
    int u = -1;
    if (rng() % 100 < 3) {
      std::vector<int> conf;
      for (int x : members) if (P[x] + A[x] - (m - 1) > 0) conf.push_back(x);
      u = conf[rng() % conf.size()];
    } else {
      long bi = -1;
      int ties = 0;
      for (int x : members) {
        const long inv = P[x] + A[x] - (m - 1);
        if (tabu_rem[x] > it) continue;
        if (inv > bi) { bi = inv; u = x; ties = 1; }
        else if (inv == bi && rng() % (++ties) == 0) u = x;
      }
      if (u < 0) u = members[rng() % members.size()];
    }
    const long dr = P[u] + A[u] - (m - 1);
    remove_point(u);
    V -= dr;
    tabu_add[u] = it + 10 + (long)(rng() % 10);
    // Add: least damaging point not tabu (aspiration: allowed if it beats the best V).
    int v = -1;
    long bs = 1L << 40;
    int ties = 0;
    for (int x = 0; x < N; ++x) {
      if (inS[x]) continue;
      const long s = P[x] + A[x];
      if (tabu_add[x] > it && V + s >= bestV) continue;
      if (s < bs) { bs = s; v = x; ties = 1; }
      else if (s == bs && rng() % (++ties) == 0) v = x;
    }
    add_point(v);
    V += bs;
    tabu_rem[v] = it + 3 + (long)(rng() % 5);
    if (V < bestV) bestV = V;
    if (it % 200000 == 0) {
      std::fprintf(stderr, "seed %u it %ld k=%d V=%ld bestV=%ld best_valid=%d t=%.0fs\n", seed, it, (int)members.size(), V, bestV, best_valid, elapsed());
    }
  }
  std::printf("END n=%d seed=%u best_valid=%d iters=%ld\n", n, seed, best_valid, it);
  return 0;
}
