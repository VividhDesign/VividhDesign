"""Same repositories, chunked on blank lines (paragraphs), as paragraph- and syntax-aware chunkers do."""
import sys, os, json, re
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
from sklearn.decomposition import TruncatedSVD
root, out = sys.argv[1], sys.argv[2]
chunks = []
for dirpath, _, files in os.walk(root, followlinks=True):
    if "/.git" in dirpath or "/build" in dirpath:
        continue
    for fn in sorted(files):
        if not fn.endswith((".cpp", ".h", ".py", ".cu", ".cuh", ".rs", ".js", ".ts", ".go", ".java", ".c")):
            continue
        try:
            text = open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for para in re.split(r"\n\s*\n", text):
            para = para.strip()
            if len(para) >= 40:  # skip one-liners such as a lone brace
                chunks.append(para)
hv = HashingVectorizer(n_features=2**18, token_pattern=r"[A-Za-z_][A-Za-z0-9_]+|\S", alternate_sign=False, norm=None)
X = TfidfTransformer().fit_transform(hv.transform(chunks))
E = TruncatedSVD(n_components=64, random_state=0).fit_transform(X).astype(np.float32)
E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-12)
np.save(out + ".npy", E)
v = E.view(np.dtype((np.void, 4 * E.shape[1]))).ravel()
uniq, first, inv, cnt = np.unique(v, return_index=True, return_inverse=True, return_counts=True)
order = np.argsort(-cnt)
print(f"{len(chunks):,} paragraph chunks; {int((cnt[inv] > 1).sum()):,} duplicates ({(cnt[inv] > 1).mean():.1%}); "
      f"groups larger than 64: {int((cnt > 64).sum())}, holding {int(cnt[cnt > 64].sum()):,} chunks")
for j in order[:6]:
    print(f"  {cnt[j]:5}x  {chunks[first[j]][:90]!r}")
