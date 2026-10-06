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
  for (const auto& m : S) {
    if (m.p == q) continue;
    inv += pool[m.slot][sq(m.p, q)] - 1;  // q is a leg at apex m
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

int main(int argc, char** argv) {
  n = std::atoi(argv[1]);
  const int ax2 = std::atoi(argv[2]), ay2 = std::atoi(argv[3]);
  int m_target = std::atoi(argv[4]);
  const unsigned seed = (unsigned)std::atoi(argv[5]);
  const double seconds = std::atof(argv[6]);
  D = 2 * (n - 1) * (n - 1);
  scratch.assign(D + 1, 0);
  std::mt19937_64 rng(seed);

  // Orbits fully inside the grid and internally isosceles-free.
  std::vector<std::vector<int>> orbits;
  std::vector<int> orbit_of(n * n, -1);
  for (int y = 0; y < n; ++y)
    for (int x = 0; x < n; ++x) {
      std::set<std::pair<int, int>> o = {{x, y}, {ax2 - x, y}, {x, ay2 - y}, {ax2 - x, ay2 - y}};
      bool inside = true;
      for (auto [a, b] : o) inside &= a >= 0 && a < n && b >= 0 && b < n;
      if (!inside) continue;
      std::vector<int> pts;
      for (auto [a, b] : o) pts.push_back(b * n + a);
      if (orbit_of[pts[0]] >= 0) continue;
      bool ok = true;  // internal check
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

  if (argc > 7) {
    std::ifstream in(argv[7]);
    int x, y;
    std::set<int> os;
    while (in >> x >> y) if (orbit_of[y * n + x] >= 0) os.insert(orbit_of[y * n + x]);
    for (int o : os) add_orbit(o);
    std::fprintf(stderr, "init: %zu orbits, %zu points, V=%ld\n", chosen_list.size(), S.size(), V);
  }
  while ((int)chosen_list.size() < m_target) {
    long bs = 1L << 40; int best = -1, ties = 0;
    for (int o = 0; o < M; ++o) {
      if (chosen[o]) continue;
      const long s = add_score(orbits[o]);
      if (s < bs) { bs = s; best = o; ties = 1; } else if (s == bs && rng() % (++ties) == 0) best = o;
    }
    add_orbit(best);
  }
  std::fprintf(stderr, "n=%d axes=(%d,%d) orbits=%d start: m=%zu points=%zu V=%ld\n", n, ax2, ay2, M, chosen_list.size(), S.size(), V);

  std::vector<long> tabu(M, 0);
  long it = 0, bestV = V;
  size_t best_valid = 0;
  const auto t0 = std::chrono::steady_clock::now();
  auto elapsed = [&] { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };
  while (elapsed() < seconds) {
    ++it;
    if (V == 0) {
      if (!verify()) { std::fprintf(stderr, "BUG: verify failed\n"); return 2; }
      if (S.size() > best_valid) {
        best_valid = S.size();
        std::string fn = "sym_n" + std::to_string(n) + "_a" + std::to_string(ax2) + "_" + std::to_string(ay2) +
                         "_k" + std::to_string(S.size()) + "_s" + std::to_string(seed) + ".txt";
        FILE* f = std::fopen(fn.c_str(), "w");
        for (const auto& mm : S) std::fprintf(f, "%d %d\n", mm.p % n, mm.p / n);
        std::fclose(f);
        std::printf("FOUND n=%d k=%zu orbits=%zu seed=%u it=%ld t=%.1fs -> %s\n", n, S.size(), chosen_list.size(), seed, it, elapsed(), fn.c_str());
        std::fflush(stdout);
      }
      long bs = 1L << 40; int best = -1, ties = 0;
      for (int o = 0; o < M; ++o) {
        if (chosen[o]) continue;
        const long s = add_score(orbits[o]);
        if (s < bs) { bs = s; best = o; ties = 1; } else if (s == bs && rng() % (++ties) == 0) best = o;
      }
      add_orbit(best);
      bestV = V;
      continue;
    }
    // Remove the most involved orbit (not tabu), occasionally a random conflicting one.
    int ro = -1;
    long bi = -1;
    int ties = 0;
    const bool walk = rng() % 100 < 5;
    for (int o : chosen_list) {
      long inv = 0;
      for (int p : orbits[o]) inv += involvement(p);
      if (inv == 0) continue;
      if (walk) { if (rng() % (++ties) == 0) ro = o; continue; }
      if (tabu[o] > it) continue;
      if (inv > bi) { bi = inv; ro = o; ties = 1; } else if (inv == bi && rng() % (++ties) == 0) ro = o;
    }
    if (ro < 0) ro = chosen_list[rng() % chosen_list.size()];
    rem_orbit(ro);
    tabu[ro] = it + 5 + (long)(rng() % 8);
    long bs = 1L << 40; int ao = -1;
    ties = 0;
    for (int o = 0; o < M; ++o) {
      if (chosen[o]) continue;
      const long s = add_score(orbits[o]);
      if (tabu[o] > it && V + s >= bestV) continue;
      if (s < bs) { bs = s; ao = o; ties = 1; } else if (s == bs && rng() % (++ties) == 0) ao = o;
    }
    add_orbit(ao);
    tabu[ao] = it + 2 + (long)(rng() % 4);
    if (V < bestV) bestV = V;
    if (it % 2000 == 0) std::fprintf(stderr, "seed %u it %ld m=%zu V=%ld bestV=%ld best_valid=%zu t=%.0fs\n", seed, it, chosen_list.size(), V, bestV, best_valid, elapsed());
  }
  std::printf("END n=%d axes=(%d,%d) seed=%u best_valid=%zu iters=%ld\n", n, ax2, ay2, seed, best_valid, it);
  return 0;
}
