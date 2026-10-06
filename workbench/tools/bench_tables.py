"""Turns Strata benchmark JSON into Markdown and HTML tables (used for BENCHMARKS_X86.md and the report page)."""
import json
import sys
from pathlib import Path

LABELS = {
    "strata": "Strata float32",
    "strata-sq8": "Strata SQ8 + rerank",
    "strata-sq8-norerank": "Strata SQ8 (codes only)",
    "faiss": "FAISS IndexHNSWFlat",
    "faiss-sq8": "FAISS IndexHNSWSQ (8-bit)",
    "hnswlib": "hnswlib",
}


def qps_at(curve, target):
    best = max([p["qps"] for p in curve if p["recall"] >= target] or [0])
    return f"{best:,.0f}" if best else "—"


def ann_rows(path, targets):
    d = json.loads(Path(path).read_text())
    rows = []
    for name, r in d["libs"].items():
        rows.append([LABELS.get(name, name), f"{r['build_seconds']:.1f}", f"{r['index_bytes'] / 2**20:,.0f}",
                     *[qps_at(r["curve"], t) for t in targets], f"{r['batch_qps_ef64']:,.0f}",
                     f"{max(p['recall'] for p in r['curve']):.4f}"])
    head = ["Library", "Build (s)", "Index file (MiB)", *[f"QPS @ R≥{t:.2f}" for t in targets],
            "All-core QPS (ef=64)", "Max recall"]
    meta = f"{d['dataset']}: {d['n']:,} × {d['dim']}, {d['metric']}, {d['queries']:,} queries, M={d['M']}, efC={d['ef_construction']}, {d['build_threads']} build threads, SIMD={d['simd']}"
    return head, rows, meta


def md(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] + ["---:"] * (len(head) - 1)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def html(head, rows):
    th = "".join(f"<th>{h}</th>" for h in head)
    body = "".join("<tr>" + "".join(f"<td{' class=\"num\"' if i else ''}>{c}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tbl"><table><tr>{th}</tr>{body}</table></div>'


if __name__ == "__main__":
    path, fmt = sys.argv[1], sys.argv[2]
    targets = [float(t) for t in sys.argv[3].split(",")] if len(sys.argv) > 3 else [0.85, 0.90, 0.95]
    head, rows, meta = ann_rows(path, targets)
    print(meta)
    print(md(head, rows) if fmt == "md" else html(head, rows))
