// Symmetric search for isosceles-free subsets of the n x n grid (AlphaEvolve problem 59).
// The set is a union of orbits under the reflections x -> ax2 - x and y -> ay2 - y (axes at
// ax2/2, ay2/2). Tabu search over orbits for a fixed number of orbits m, minimising the exact
// number of violations; each candidate orbit is scored exactly against the current set.
//
//   ./sym n ax2 ay2 m seed seconds [init_file]

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <random>
#include <set>
#include <string>
#include <vector>
#include <functional>

static int n, D;
struct Member { int p; int slot; };
static std::vector<Member> S;
static std::vector<std::vector<uint8_t>> pool;
static std::vector<int> free_slots;
static std::vector<int> scratch;
static long V = 0;

static inline int sq(int p, int q) {
  const int dx = p % n - q % n, dy = p / n - q / n;
  return dx * dx + dy * dy;
}

static int get_slot() {
  if (free_slots.empty()) { pool.emplace_back(D + 1, 0); return (int)pool.size() - 1; }
  const int s = free_slots.back(); free_slots.pop_back(); return s;
}

static void add_point(int q) {
  const int slot = get_slot();
  auto& c = pool[slot];
  long apex = 0;
  for (const auto& m : S) {
    const int d = sq(m.p, q);
    V += pool[m.slot][d];
    pool[m.slot][d]++;
    apex += c[d];
    c[d]++;
  }
  V += apex;
  S.push_back({q, slot});
}

static void remove_point(int q) {
  size_t i = 0;
  while (S[i].p != q) ++i;
  const int slot = S[i].slot;
  S[i] = S.back();
  S.pop_back();
  auto& c = pool[slot];
  for (const auto& m : S) {
    const int d = sq(m.p, q);
    pool[m.slot][d]--;
    V -= pool[m.slot][d];
    c[d]--;
    V -= c[d];
  }
  free_slots.push_back(slot);
}

// Exact number of violations created by adding all points of O to S.
static long add_score(const std::vector<int>& O) {
  long score = 0;
  int ds[4];
  for (const auto& m : S) {
    const auto& c = pool[m.slot];
    for (size_t i = 0; i < O.size(); ++i) {
      ds[i] = sq(m.p, O[i]);
      score += c[ds[i]];
      for (size_t j = 0; j < i; ++j) score += ds[j] == ds[i];
    }
  }
  std::vector<int> touched;
  for (size_t i = 0; i < O.size(); ++i) {
    touched.clear();
    auto bump = [&](int d) { score += scratch[d]; if (scratch[d]++ == 0) touched.push_back(d); };
    for (const auto& m : S) bump(sq(O[i], m.p));
    for (size_t j = 0; j < O.size(); ++j) if (j != i) bump(sq(O[i], O[j]));
    for (int d : touched) scratch[d] = 0;
  }
  return score;
}

// Violations involving point q (in S), counting each violation once per involved point.
static long involvement(int q) {
  long inv = 0;
  int qs = -1;
  for (const auto& m : S) if (m.p == q) qs = m.slot;
  const auto& cq = pool[qs];
  for (const auto& m : S) {
    if (m.p == q) continue;
    const int d = sq(m.p, q);
    inv += pool[m.slot][d] - 1;   // q is a leg at apex m
    inv += cq[d] - 1 > 0 ? 0 : 0;
  }
  // q as apex
  std::vector<int> seen;
  for (const auto& m : S) {
    if (m.p == q) continue;
    const int d = sq(m.p, q);
    if (scratch[d]++ == 0) seen.push_back(d);
  }
  for (int d : seen) { inv += (long)scratch[d] * (scratch[d] - 1) / 2; scratch[d] = 0; }
  return inv;
}

static bool verify() {
  std::vector<int> seen(D + 1, -1);
  for (size_t i = 0; i < S.size(); ++i)
    for (size_t j = 0; j < S.size(); ++j) {
      if (i == j) continue;
      const int d = sq(S[i].p, S[j].p);
      if (seen[d] == (int)i) return false;
      seen[d] = (int)i;
    }
  return true;
}


// Exhaustive (k, k+1)-swap search around a valid construction: for every k-subset R of the
// chosen orbits, remove R, collect the orbits that are free (add without any violation), and
// look for k+1 mutually compatible free orbits by backtracking. Any success is a strictly
// larger valid set. Symmetry: 4 = both mirrors, 2 = mirror in x only, 1 = none.
//
//   ./swapk n ax2 ay2 sym k init_file [seconds]
int main(int argc, char** argv) {
  n = std::atoi(argv[1]);
  const int ax2 = std::atoi(argv[2]), ay2 = std::atoi(argv[3]);
  const int sym = std::atoi(argv[4]);
  const int K = std::atoi(argv[5]);
  const char* init = argv[6];
  const double seconds = argc > 7 ? std::atof(argv[7]) : 1e18;
  D = 2 * (n - 1) * (n - 1);
  scratch.assign(D + 1, 0);

  std::vector<std::vector<int>> orbits;
  std::vector<int> orbit_of(n * n, -1);
  for (int y = 0; y < n; ++y)
    for (int x = 0; x < n; ++x) {
      std::set<std::pair<int, int>> o = {{x, y}};
      if (sym >= 2) o.insert({ax2 - x, y});
      if (sym >= 4) { o.insert({x, ay2 - y}); o.insert({ax2 - x, ay2 - y}); }
      bool inside = true;
      for (auto [a, b] : o) inside &= a >= 0 && a < n && b >= 0 && b < n;
      if (!inside) continue;
      std::vector<int> pts;
      for (auto [a, b] : o) pts.push_back(b * n + a);
      if (orbit_of[pts[0]] >= 0) continue;
      bool ok = true;
      for (int a : pts) {
        std::vector<int> ds;
        for (int b : pts) if (b != a) ds.push_back(sq(a, b));
        std::sort(ds.begin(), ds.end());
        ok &= std::adjacent_find(ds.begin(), ds.end()) == ds.end();
      }
      if (!ok) continue;
      for (int p : pts) orbit_of[p] = (int)orbits.size();
      orbits.push_back(pts);
    }
  const int M = (int)orbits.size();
  std::vector<char> chosen(M, 0);
  std::vector<int> chosen_list;
  auto add_orbit = [&](int o) { for (int p : orbits[o]) add_point(p); chosen[o] = 1; chosen_list.push_back(o); };
  auto rem_orbit = [&](int o) {
    for (int p : orbits[o]) remove_point(p);
    chosen[o] = 0;
    chosen_list.erase(std::find(chosen_list.begin(), chosen_list.end(), o));
  };
  {
    std::ifstream in(init);
    int x, y;
    std::set<int> os;
    std::vector<int> pts;
    while (in >> x >> y) pts.push_back(y * n + x);
    for (int p : pts) {
      const int o = orbit_of[p];
      if (o < 0) { std::fprintf(stderr, "point (%d,%d) has no valid orbit\n", p % n, p / n); return 1; }
      os.insert(o);
    }
    for (int o : os) add_orbit(o);
    if (S.size() != pts.size() || V != 0) {
      std::fprintf(stderr, "init is not a valid union of orbits: %zu points vs %zu, V=%ld\n", S.size(), pts.size(), V);
      return 1;
    }
  }
  const size_t base = S.size();
  std::fprintf(stderr, "n=%d axes=(%d,%d) sym=%d orbits=%d init=%zu points (%zu orbits), k=%d\n", n, ax2, ay2, sym, M, base, chosen_list.size(), K);
  const auto t0 = std::chrono::steady_clock::now();
  auto elapsed = [&] { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };

  std::vector<int> F;
  std::function<bool(int, size_t)> extend = [&](int need, size_t start) -> bool {
    if (need == 0) return true;
    for (size_t i = start; i < F.size(); ++i) {
      const int o = F[i];
      if (chosen[o]) continue;
      if (add_score(orbits[o]) != 0) continue;
      add_orbit(o);
      if (extend(need - 1, i + 1)) return true;
      rem_orbit(o);
    }
    return false;
  };
  const std::vector<int> base_list = chosen_list;
  const int m = (int)base_list.size();
  std::vector<int> idx(K);
  for (int i = 0; i < K; ++i) idx[i] = i;
  long tried = 0, max_free = 0;
  bool found = false;
  while (K <= m) {
    std::vector<int> R;
    for (int i : idx) R.push_back(base_list[i]);
    for (int o : R) rem_orbit(o);
    F.clear();
    for (int o = 0; o < M; ++o) if (!chosen[o] && add_score(orbits[o]) == 0) F.push_back(o);
    max_free = std::max<long>(max_free, (long)F.size());
    ++tried;
    // Orbit sizes may differ (points on an axis), so require more points, not more orbits.
    std::vector<int> before = chosen_list;
    if ((long)F.size() >= K + 1 && extend(K + 1, 0) && S.size() > base) {
      if (!verify()) { std::fprintf(stderr, "BUG: verify failed\n"); return 2; }
      std::string fn = "swap_n" + std::to_string(n) + "_sym" + std::to_string(sym) + "_k" + std::to_string(S.size()) + ".txt";
      FILE* f = std::fopen(fn.c_str(), "w");
      for (const auto& mm : S) std::fprintf(f, "%d %d\n", mm.p % n, mm.p / n);
      std::fclose(f);
      std::printf("IMPROVED n=%d: %zu -> %zu points by a (%d,%d)-swap after %ld subsets, t=%.1fs -> %s\n", n, base, S.size(), K, K + 1, tried, elapsed(), fn.c_str());
      found = true;
      break;
    }
    // restore exactly
    while (chosen_list.size() > before.size()) rem_orbit(chosen_list.back());
    for (int o : R) add_orbit(o);
    if (tried % 500 == 0) std::fprintf(stderr, "tried %ld subsets, max free %ld, t=%.0fs\n", tried, max_free, elapsed());
    if (elapsed() > seconds) break;
    // next combination
    int i = K - 1;
    while (i >= 0 && idx[i] == m - K + i) --i;
    if (i < 0) break;
    ++idx[i];
    for (int j = i + 1; j < K; ++j) idx[j] = idx[j - 1] + 1;
  }
  std::printf("DONE n=%d sym=%d k=%d: tried %ld subsets, max free %ld, improved=%d, t=%.1fs\n", n, sym, K, tried, max_free, found, elapsed());
  return 0;
}
