"""Level-0 structure of hnswlib's graph around identical vectors, read from its saved index file."""
import struct, sys, tempfile, os
import numpy as np, hnswlib
rng = np.random.default_rng(0)
base = rng.standard_normal(16).astype(np.float32)
order = sys.argv[1] if len(sys.argv) > 1 else "copies-first"
copies, others = np.tile(base, (200, 1)), rng.standard_normal((800, 16)).astype(np.float32)
X = np.concatenate([copies, others]) if order == "copies-first" else np.concatenate([others, copies])
is_copy = np.all(X == base, axis=1)
p = hnswlib.Index(space="l2", dim=16); p.init_index(max_elements=1000, M=16, ef_construction=100, random_seed=0)
p.add_items(X, np.arange(1000), num_threads=1)
path = os.path.join(tempfile.mkdtemp(), "h.bin"); p.save_index(path)
b = open(path, "rb").read()
(off0, maxel, count, size_per, label_off, data_off) = struct.unpack_from("<6Q", b, 0)
maxlevel, enter = struct.unpack_from("<iI", b, 48)
maxM, maxM0, M = struct.unpack_from("<3Q", b, 56)
start = 56 + 24 + 8 + 8  # mult (double), ef_construction (size_t)
level0 = {}
for i in range(count):
    rec = start + i * size_per
    hdr = struct.unpack_from("<I", b, rec + off0)[0] & 0xFFFF
    nbrs = np.frombuffer(b, dtype=np.uint32, count=hdr, offset=rec + off0 + 4)
    label = struct.unpack_from("<Q", b, rec + label_off)[0]
    level0[label] = nbrs  # internal ids equal labels here (inserted in order)
indeg = np.zeros(count, int)
for row in level0.values():
    np.add.at(indeg, row.astype(int), 1)
cp = np.where(is_copy)[0]
share = np.mean([is_copy[level0[i].astype(int)].mean() for i in cp if len(level0[i])])
out = sum(int((~is_copy[level0[i].astype(int)]).sum()) for i in cp)
print(f"hnswlib {order}: maxM0={maxM0}; copies with in-degree 0: {int((indeg[cp] == 0).sum())}/200; share of a copy's neighbours that are copies: {share:.2f}; edges from a copy to a non-copy: {out}")
