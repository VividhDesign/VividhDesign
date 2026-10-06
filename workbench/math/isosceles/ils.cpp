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


// Iterated local search in the style of Andrade, Resende & Werneck (J. Heuristics 2012) for
// maximum independent sets, adapted to the 3-uniform "isosceles" hypergraph on orbits: the set
// stays valid; (1,2)-swaps remove one orbit and insert two compatible free orbits; perturbations
// force in random orbits and repair by removing the most involved ones.
//
//   ./ils n ax2 ay2 seed seconds [init_file]
int main(int argc, char** argv) {
  n = std::atoi(argv[1]);
  const int ax2 = std::atoi(argv[2]), ay2 = std::atoi(argv[3]);
  const unsigned seed = (unsigned)std::atoi(argv[4]);
  const double seconds = std::atof(argv[5]);
  D = 2 * (n - 1) * (n - 1);
  scratch.assign(D + 1, 0);
  std::mt19937_64 rng(seed);

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
  auto free_orbits = [&](int exclude) {
    std::vector<int> F;
    for (int o = 0; o < M; ++o) if (!chosen[o] && o != exclude && add_score(orbits[o]) == 0) F.push_back(o);
    return F;
  };
  auto fill_free = [&]() {
    int added = 0;
    for (;;) {
      std::vector<int> F = free_orbits(-1);
      if (F.empty()) return added;
      add_orbit(F[rng() % F.size()]);
      ++added;
    }
  };
  auto repair = [&](int keep) {
    while (V > 0) {
      int ro = -1; long bi = -1; int ties = 0;
      for (int o : chosen_list) {
        if (o == keep) continue;
        long inv = 0;
        for (int p : orbits[o]) inv += involvement(p);
        if (inv > bi) { bi = inv; ro = o; ties = 1; } else if (inv == bi && rng() % (++ties) == 0) ro = o;
      }
      rem_orbit(ro);
    }
  };
  auto one_two_pass = [&]() {
    std::vector<int> order = chosen_list;
    std::shuffle(order.begin(), order.end(), rng);
    for (int O : order) {
      if (!chosen[O]) continue;
      rem_orbit(O);
      std::vector<int> F = free_orbits(O);
      std::shuffle(F.begin(), F.end(), rng);
      for (size_t i = 0; i < F.size(); ++i) {
        add_orbit(F[i]);
        for (size_t j = 0; j < F.size(); ++j) {
          if (j == i || chosen[F[j]]) continue;
          if (add_score(orbits[F[j]]) == 0) { add_orbit(F[j]); return true; }
        }
        rem_orbit(F[i]);
      }
      add_orbit(O);
    }
    return false;
  };
  auto save = [&](const char* tag) {
    if (!verify()) { std::fprintf(stderr, "BUG: verify failed\n"); std::exit(2); }
    std::string fn = std::string(tag) + "_n" + std::to_string(n) + "_a" + std::to_string(ax2) + "_" + std::to_string(ay2) +
                     "_k" + std::to_string(S.size()) + "_s" + std::to_string(seed) + ".txt";
    FILE* f = std::fopen(fn.c_str(), "w");
    for (const auto& mm : S) std::fprintf(f, "%d %d\n", mm.p % n, mm.p / n);
    std::fclose(f);
    return fn;
  };

  if (argc > 6) {
    std::ifstream in(argv[6]);
    int x, y;
    std::set<int> os;
    while (in >> x >> y) if (orbit_of[y * n + x] >= 0) os.insert(orbit_of[y * n + x]);
    for (int o : os) add_orbit(o);
    repair(-1);
  }
  fill_free();
  size_t best = S.size();
  std::vector<int> best_list = chosen_list;
  std::fprintf(stderr, "n=%d axes=(%d,%d) orbits=%d start %zu points\n", n, ax2, ay2, M, S.size());
  const auto t0 = std::chrono::steady_clock::now();
  auto elapsed = [&] { return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count(); };
  long iter = 0;
  while (elapsed() < seconds) {
    ++iter;
    while (one_two_pass()) fill_free();
    if (S.size() > best) {
      best = S.size();
      best_list = chosen_list;
      const std::string fn = save("ils");
      std::printf("FOUND n=%d k=%zu orbits=%zu seed=%u iter=%ld t=%.1fs -> %s\n", n, S.size(), chosen_list.size(), seed, iter, elapsed(), fn.c_str());
      std::fflush(stdout);
    }
    const int k = (rng() % 4 == 0) ? 2 : 1;
    for (int t = 0; t < k; ++t) {
      int o;
      do { o = (int)(rng() % M); } while (chosen[o]);
      add_orbit(o);
      repair(o);
    }
    fill_free();
    if (S.size() + 8 < best || rng() % 200 == 0) {
      while (!chosen_list.empty()) rem_orbit(chosen_list.back());
      for (int o : best_list) add_orbit(o);
    }
    if (iter % 50 == 0) std::fprintf(stderr, "seed %u iter %ld cur=%zu best=%zu t=%.0fs\n", seed, iter, S.size(), best, elapsed());
  }
  std::printf("END n=%d axes=(%d,%d) seed=%u best=%zu iters=%ld\n", n, ax2, ay2, seed, best, iter);
  return 0;
}
