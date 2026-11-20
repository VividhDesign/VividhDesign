"""Metamorphic and oracle properties every ANN index should satisfy.

Each property takes an adapter and returns a list of findings (empty when it holds). A finding is
a short string with the numbers that show the violation, so it reads as a bug report's first line.
Properties check correctness invariants, not recall targets: approximate search may miss
neighbours, but it must not return invalid ids, wrong distances, deleted entries, or let one bad
row damage unrelated searches.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np

from .adapters import MISSING

# ---------------------------------------------------------------------------------------------
# distance conventions


def _conv(name, x, q):
    x = np.asarray(x, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    if name == "l2sq":
        return ((x - q) ** 2).sum(-1)
    if name == "l2":
        return np.sqrt(((x - q) ** 2).sum(-1))
    if name == "dot":
        return x @ q
    if name == "one_minus_dot":
        return 1 - x @ q
    cos = (x @ q) / (np.linalg.norm(x, axis=-1) * np.linalg.norm(q))
    if name == "one_minus_cos":
        return 1 - cos
    if name == "angular_chord":
        return np.sqrt(np.maximum(2 - 2 * cos, 0))
    raise ValueError(name)


def _similarity(name):
    """Conventions where larger means closer."""
    return name == "dot"


def _brute(X, q, conv):
    d = _conv(conv, X, q)
    return np.argsort(-d if _similarity(conv) else d, kind="stable"), d


# ---------------------------------------------------------------------------------------------
# data


def gaussian(n, d, seed=0):
    return np.random.default_rng(seed).standard_normal((n, d)).astype(np.float32)


def unit(X):
    return (X / np.linalg.norm(X, axis=-1, keepdims=True)).astype(np.float32)


def data(n, d, metric, seed=0):
    """Gaussian rows; unit-normalised for ip, where a longer row can outscore a row's own dot product."""
    X = gaussian(n, d, seed)
    return unit(X) if metric == "ip" else X


def _build(A, X, ids, metric="l2", M=16, efc=100):
    idx = A.build(X.shape[1], metric, M=M, efc=efc)
    A.add(idx, X, ids)
    return idx


def _self_hits(A, idx, X, ids, ef=64):
    I, _ = A.search(idx, X, 1, ef)
    return int((I[:, 0] == ids).sum())


# ---------------------------------------------------------------------------------------------
# properties


def results_are_valid(A, metric):
    """Ids exist, are unique per query, distances are sorted and match brute force."""
    X = data(1500, 24, metric, seed=1)
    ids = np.arange(1000, 2500, dtype=np.int64)
    idx = _build(A, X, ids, metric)
    Q = gaussian(40, 24, seed=2)
    I, D = A.search(idx, Q, 10, 64)
    conv = A.convention[metric]
    pos = {int(i): p for p, i in enumerate(ids)}
    out = []
    bad_ids = sorted({int(i) for i in I.ravel() if i != MISSING and int(i) not in pos})
    if bad_ids:
        out.append(f"returned ids never inserted: {bad_ids[:5]}")
    dup_rows = sum(len(set(r[r != MISSING])) != (r != MISSING).sum() for r in I)
    if dup_rows:
        out.append(f"{dup_rows}/40 queries return the same id twice")
    wrong, unsorted = 0, 0
    conv_seen = set()
    for r in range(len(Q)):
        valid = [(int(i), d) for i, d in zip(I[r], D[r]) if i != MISSING and int(i) in pos]
        if not valid:
            continue
        got = np.array([d for _, d in valid])
        ref = _conv(conv, X[[pos[i] for i, _ in valid]], Q[r])
        if not np.allclose(got, ref, rtol=1e-3, atol=1e-3):
            wrong += 1
            matches = [c for c in ("l2sq", "l2", "dot", "one_minus_dot", "one_minus_cos", "angular_chord")
                       if np.allclose(got, _conv(c, X[[pos[i] for i, _ in valid]], Q[r]), rtol=1e-3, atol=1e-3)]
            if matches:
                wrong -= 1
                conv_seen.add(matches[0])
        order = -got if _similarity(conv) else got
        if np.any(np.diff(order) < -1e-5):
            unsorted += 1
    if wrong:
        out.append(f"{wrong}/40 queries report distances that match no standard convention (expected {conv})")
    if unsorted:
        out.append(f"{unsorted}/40 queries return results out of order")
    return out


def k_larger_than_size(A, metric):
    """Asking for more results than stored returns each stored entry once."""
    X = data(7, 8, metric, seed=3)
    ids = np.arange(7, dtype=np.int64)
    idx = _build(A, X, ids, metric)
    try:
        I, _ = A.search(idx, X[:3], 20, 64)
    except Exception as e:  # noqa: BLE001
        return [f"k=20 on 7 entries raised {type(e).__name__}: {str(e)[:80]}"]
    out = []
    for r in range(3):
        got = [int(i) for i in I[r] if i != MISSING]
        if sorted(got) != list(range(7)):
            out.append(f"k=20 on 7 entries returned {got}")
            break
    return out


def duplicate_vectors_reachable(A, metric):
    """Every key holding an identical vector can still be found."""
    base = data(1, 16, metric, seed=4)[0]
    group = 200
    X = np.concatenate([np.tile(base, (group, 1)), data(800, 16, metric, seed=5)]).astype(np.float32)
    ids = np.arange(len(X), dtype=np.int64)
    idx = _build(A, X, ids, metric)
    try:
        I, _ = A.search(idx, base[None], group, len(X))
    except Exception as e:  # noqa: BLE001
        return [f"searching the duplicated vector raised {type(e).__name__}: {str(e)[:80]}"]
    found = len({int(i) for i in I[0] if 0 <= i < group})
    return [] if found == group else [f"search(k={group}, ef={len(X)}) for a vector stored under {group} keys finds {found} of them"]


def nan_row_isolated(A, metric):
    """One NaN row is refused, or at least does not change other searches."""
    X = data(1000, 16, metric, seed=6)
    ids = np.arange(1000, dtype=np.int64)
    clean = _build(A, X, ids, metric)
    base = _self_hits(A, clean, X, ids)
    idx = A.build(16, metric)
    A.add(idx, X[:500], ids[:500])
    try:
        A.add(idx, np.full((1, 16), np.nan, np.float32), np.array([10_000]))
        accepted = True
    except Exception:  # noqa: BLE001
        accepted = False
    A.add(idx, X[500:], ids[500:])
    if not accepted:
        return []
    try:
        poisoned = _self_hits(A, idx, X, ids)
    except ValueError as e:
        if "nan" in str(e).lower():
            return []  # refused when the index is built (build-once libraries)
        raise
    I, _ = A.search(idx, X[:200], 10, 64)
    nan_returned = int((I == 10_000).sum())
    out = []
    if poisoned < base - 10:
        out.append(f"one NaN row accepted; self-hits fall from {base}/1000 to {poisoned}/1000")
    if nan_returned:
        out.append(f"the NaN row is returned in {nan_returned} of 200 top-10 lists")
    return out


def zero_vector_cosine(A, metric):
    """A zero vector under cosine is refused or harmless (no NaN distances, no damage)."""
    if metric != "cos":
        return []
    X = data(500, 16, metric, seed=7)
    ids = np.arange(500, dtype=np.int64)
    idx = A.build(16, metric)
    A.add(idx, X[:250], ids[:250])
    try:
        A.add(idx, np.zeros((1, 16), np.float32), np.array([9999]))
    except Exception:  # noqa: BLE001
        return []
    A.add(idx, X[250:], ids[250:])
    out = []
    I, D = A.search(idx, X[:100], 5, 64)
    if np.isnan(D[I != MISSING]).any():
        out.append("NaN distances returned after inserting a zero vector")
    hits = int((I[:, 0] == ids[:100]).sum())
    if hits < 95:
        out.append(f"self-hits {hits}/100 after inserting a zero vector")
    return out


def save_load_roundtrip(A, metric):
    if not A.can_save:
        return []
    X = data(800, 16, metric, seed=8)
    ids = np.arange(800, dtype=np.int64) * 3
    idx = _build(A, X, ids, metric)
    Q = gaussian(30, 16, seed=9)
    I1, D1 = A.search(idx, Q, 10, 64)
    with tempfile.TemporaryDirectory() as t:
        new = A.roundtrip(idx, os.path.join(t, "index.bin"))
        I2, D2 = A.search(new, Q, 10, 64)
    out = []
    if not np.array_equal(I1, I2):
        out.append(f"{int((I1 != I2).any(1).sum())}/30 queries return different ids after save/load")
    elif not np.allclose(D1, D2, equal_nan=True):
        out.append("distances change after save/load")
    return out


def deleted_never_returned(A, metric):
    if not A.can_delete:
        return []
    X = data(1000, 16, metric, seed=10)
    ids = np.arange(1000, dtype=np.int64)
    idx = _build(A, X, ids, metric)
    gone = ids[::3]
    A.delete(idx, gone)
    I, _ = A.search(idx, X, 10, 64)
    leaked = int(np.isin(I, gone).sum())
    out = [f"deleted ids returned {leaked} times in 1000 top-10 lists"] if leaked else []
    keep = np.setdiff1d(ids, gone)
    hits = int((A.search(idx, X[keep], 1, 64)[0][:, 0] == keep).sum())
    if hits < len(keep) - 10:
        out.append(f"after deleting a third, survivors find themselves {hits}/{len(keep)}")
    if A.can_save:
        with tempfile.TemporaryDirectory() as t:
            new = A.roundtrip(idx, os.path.join(t, "index.bin"))
            I2, _ = A.search(new, X, 10, 64)
            leaked2 = int(np.isin(I2, gone).sum())
            if leaked2:
                out.append(f"after save/load, deleted ids returned {leaked2} times")
    return out


def readd_replaces_vector(A, metric):
    """Adding an existing id with a new vector: the new vector finds it, the old one does not."""
    if not A.can_update:
        return []
    X = data(600, 16, metric, seed=11)
    ids = np.arange(600, dtype=np.int64)
    idx = _build(A, X, ids, metric)
    new = data(20, 16, metric, seed=12) * (1 if metric == "ip" else 3)
    target = ids[:20]
    try:
        A.add(idx, new, target)
    except Exception as e:  # noqa: BLE001
        return []  # refusing a duplicate id is a legitimate contract
    I_new, _ = A.search(idx, new, 1, 64)
    I_old, D_old = A.search(idx, X[:20], 1, 64)
    out = []
    if int((I_new[:, 0] == target).sum()) < 18:
        out.append(f"re-added ids found by their new vector {int((I_new[:, 0] == target).sum())}/20")
    stale = int((I_old[:, 0] == target).sum())
    if stale:
        out.append(f"{stale}/20 re-added ids still returned as an exact match for their old vector")
    return out


def filter_only_allowed(A, metric):
    if not A.can_filter:
        return []
    X = data(2000, 16, metric, seed=13)
    ids = np.arange(2000, dtype=np.int64)
    idx = _build(A, X, ids, metric)
    Q = gaussian(40, 16, seed=14)
    out = []
    conv = A.convention[metric]
    for frac in (0.5, 0.05, 0.005):
        allowed = ids[np.random.default_rng(15).random(2000) < frac]
        I, _ = A.search_filtered(idx, Q, 10, 64, allowed)
        bad = int((~np.isin(I[I != MISSING], allowed)).sum())
        if bad:
            out.append(f"filter admitting {len(allowed)} ids returned {bad} disallowed ids")
        hits = 0
        for r in range(len(Q)):
            order, _ = _brute(X[allowed], Q[r], conv)
            truth = set(allowed[order[: min(10, len(allowed))]].tolist())
            hits += len(truth & set(I[r][I[r] != MISSING].tolist()))
        recall = hits / (len(Q) * min(10, len(allowed)))
        if recall < 0.8:
            out.append(f"filter admitting {len(allowed)}/2000 ids: recall@10 {recall:.2f}")
    return out


def low_connectivity_reachable(A, metric):
    """Small M is slower to search, but every entry should stay findable with a wide beam."""
    if not A.incremental:
        return []
    out = []
    for M in (4, 8):
        X = data(3000, 8, metric, seed=16)
        ids = np.arange(3000, dtype=np.int64)
        try:
            idx = _build(A, X, ids, metric, M=M)
        except Exception:  # noqa: BLE001
            continue
        hits = _self_hits(A, idx, X, ids, ef=512)
        if hits < 2970:
            out.append(f"M={M}: {3000 - hits}/3000 entries not found by their own vector at ef=512")
    return out


def empty_and_tiny(A, metric):
    out = []
    if not A.incremental:
        return out
    idx = A.build(8, metric)
    try:
        I, _ = A.search(idx, gaussian(2, 8), 3, 16)
        if (I != MISSING).any():
            out.append(f"empty index returned ids {I.tolist()}")
    except Exception as e:  # noqa: BLE001
        out.append(f"searching an empty index raised {type(e).__name__}: {str(e)[:70]}")
    idx = _build(A, gaussian(1, 8), np.array([5]), metric)
    try:
        I, _ = A.search(idx, gaussian(3, 8, seed=1), 3, 16)
        if [int(i) for i in I[:, 0]] != [5, 5, 5] or (I[:, 1:] != MISSING).any():
            out.append(f"single-entry index returned {I.tolist()}")
    except Exception as e:  # noqa: BLE001
        out.append(f"single-entry search raised {type(e).__name__}: {str(e)[:70]}")
    return out


def huge_magnitudes(A, metric):
    """Float32 squared distances overflow above ~1.8e19; ranking should survive vectors near 1e19."""
    if metric != "l2":
        return []
    X = (gaussian(300, 8, seed=17) * 1e19).astype(np.float32)
    ids = np.arange(300, dtype=np.int64)
    idx = _build(A, X, ids, metric)
    hits = _self_hits(A, idx, X, ids, ef=128)
    return [] if hits >= 295 else [f"vectors of magnitude ~1e19: self-hits {hits}/300"]


PROPERTIES = [
    results_are_valid,
    k_larger_than_size,
    empty_and_tiny,
    duplicate_vectors_reachable,
    nan_row_isolated,
    zero_vector_cosine,
    save_load_roundtrip,
    deleted_never_returned,
    readd_replaces_vector,
    filter_only_allowed,
    low_connectivity_reachable,
]
