# Adding Strata to ann-benchmarks

[ann-benchmarks](https://github.com/erikbern/ann-benchmarks) is the standard public leaderboard for
approximate nearest-neighbour libraries. A listing there is the most visible third-party validation Strata
can get. These files follow the layout of the existing `hnswlib` entry.

## Steps

1. Fork `erikbern/ann-benchmarks` and copy `ann_benchmarks/algorithms/strata/` into it.
2. Add `- strata` to the algorithm matrix in `.github/workflows/benchmarks.yml`. Look for the list that
   contains `- hnswlib`.
3. Test locally (needs Docker):
   ```bash
   pip install -r requirements.txt
   python install.py --algorithm strata
   python run.py --dataset glove-100-angular --algorithm strata --runs 1
   python run.py --dataset sift-128-euclidean --algorithm strata-sq8 --runs 1
   python plot.py --dataset glove-100-angular
   ```
4. Open the PR. Title: "Add Strata (HNSW, C++17, with SQ8 quantization)". Include one plot.

The module was smoke-tested against the local Strata build with the SQ8 patch: `smoke_test.py` imitates the
harness. Note that `strata-sq8` needs the SQ8 patch to be merged into Strata `main` first, because the Dockerfile
installs from GitHub.
