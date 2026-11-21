"""Render findings for a terminal, as JSON, or as a self-contained HTML report."""

from __future__ import annotations

import html
import json
import sys
from collections import Counter
from datetime import datetime
from typing import Optional

from .corpus import SOURCE_NOTE
from .verify import RISK_ORDER, Finding

ICON = {"high": "✖", "review": "?", "ok": "✔", "skip": "·"}
COLOR = {"high": "\033[31m", "review": "\033[33m", "ok": "\033[32m", "skip": "\033[90m"}
RESET = "\033[0m"


def summary(findings: list[Finding]) -> dict:
    c = Counter(f.risk for f in findings)
    return {"total": len(findings), "high": c["high"], "review": c["review"], "ok": c["ok"], "skipped": c["skip"]}


def to_json(findings: list[Finding], source: Optional[str] = None) -> str:
    return json.dumps(
        {"source": source, "summary": summary(findings), "findings": [f.as_dict() for f in findings],
         "data": SOURCE_NOTE},
        indent=2, ensure_ascii=False,
    )


def to_terminal(findings: list[Finding], color: Optional[bool] = None, show_ok: bool = True) -> str:
    color = sys.stdout.isatty() if color is None else color
    out = []
    for f in sorted(findings, key=lambda f: (RISK_ORDER[f.risk], f.ref.start)):
        if f.risk == "ok" and not show_ok:
            continue
        c0, c1 = (COLOR[f.risk], RESET) if color else ("", "")
        out.append(f"{c0}{ICON[f.risk]} {f.headline.upper()}{c1}  {f.ref.label}")
        out.append(f"    {f.message}")
        for q in f.quotes:
            if q.status != "UNCHECKED":
                out.append(f"    quote {q.status} ({q.score:.0%}): \"{q.quote[:110]}{'…' if len(q.quote) > 110 else ''}\"")
        for s in f.suggestions[:2]:
            out.append(f"    closest on record: {s.describe()}")
        out.append("")
    s = summary(findings)
    out.append(f"{s['total']} authorities: {s['high']} likely wrong or fabricated, {s['review']} to review, "
               f"{s['ok']} verified, {s['skipped']} not checked.")
    return "\n".join(out)


_CSS = """
:root{--bg:#fbfaf7;--fg:#1d1b16;--muted:#6b665c;--line:#e4e0d6;--card:#fff;--high:#b42318;--high-bg:#fdecea;
--review:#9a6700;--review-bg:#fff6dd;--ok:#1a7f37;--ok-bg:#e9f7ee;--skip:#6b665c;--skip-bg:#f1efe9}
@media (prefers-color-scheme:dark){:root{--bg:#16140f;--fg:#ece8df;--muted:#a39d90;--line:#2d2a22;--card:#1e1c16;
--high:#ff8a80;--high-bg:#3a1d1a;--review:#f2c14e;--review-bg:#33290f;--ok:#6fdc8c;--ok-bg:#15301e;--skip:#a39d90;--skip-bg:#25231c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:920px;margin:0 auto;padding:28px 16px 60px}h1{font-size:22px;margin:0 0 4px}.muted{color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}.tile b{display:block;font-size:26px}
.f{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--skip);border-radius:10px;padding:12px 14px;margin:10px 0}
.f.high{border-left-color:var(--high)}.f.review{border-left-color:var(--review)}.f.ok{border-left-color:var(--ok)}
.tag{display:inline-block;font-size:12px;font-weight:600;padding:2px 8px;border-radius:99px;margin-right:6px}
.tag.high{background:var(--high-bg);color:var(--high)}.tag.review{background:var(--review-bg);color:var(--review)}
.tag.ok{background:var(--ok-bg);color:var(--ok)}.tag.skip{background:var(--skip-bg);color:var(--skip)}
.ref{font-weight:600}.msg{margin:6px 0 0}.q{margin:8px 0 0;padding:8px 10px;border-radius:8px;background:var(--bg);font-size:14px}
a{color:inherit}footer{margin-top:30px;font-size:13px}
@media (max-width:600px){.tiles{grid-template-columns:repeat(2,1fr)}}
"""


def to_html(findings: list[Finding], source: Optional[str] = None) -> str:
    s = summary(findings)
    e = html.escape
    rows = []
    for f in sorted(findings, key=lambda f: (RISK_ORDER[f.risk], f.ref.start)):
        link = ""
        if f.match is not None and f.match.doc is not None:
            link = f' · <a href="{e(f.match.doc.pdf_url)}">judgment PDF</a>'
        quotes = "".join(
            f'<div class="q"><b>Quote {e(q.status.lower().replace("_", " "))}</b> ({q.score:.0%} of phrasing found): '
            f'“{e(q.quote[:400])}{"…" if len(q.quote) > 400 else ""}”</div>'
            for q in f.quotes if q.status != "UNCHECKED"
        )
        sugg = "".join(f'<div class="msg muted">Closest on record: {e(h.describe())}</div>' for h in f.suggestions[:2])
        rows.append(
            f'<div class="f {f.risk}"><span class="tag {f.risk}">{e(f.headline)}</span>'
            f'<span class="ref">{e(f.ref.label)}</span><p class="msg">{e(f.message)}{link}</p>{quotes}{sugg}</div>'
        )
    when = datetime.now().strftime("%d %b %Y, %H:%M")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Citation check</title><style>{_CSS}</style></head>
<body><main><h1>Citation check{(': ' + e(source)) if source else ''}</h1>
<div class="muted">Checked {when} with Pramaan against the open record of Supreme Court of India judgments.</div>
<div class="tiles"><div class="tile"><b>{s['total']}</b>authorities</div><div class="tile"><b style="color:var(--high)">{s['high']}</b>likely wrong or fabricated</div>
<div class="tile"><b style="color:var(--review)">{s['review']}</b>to review</div><div class="tile"><b style="color:var(--ok)">{s['ok']}</b>verified</div></div>
{''.join(rows)}
<footer class="muted">A finding is evidence to check, not a ruling. Pramaan only knows what open sources record:
judgments reported in the Supreme Court Reports since 1950 and citations made by those judgments. Data: {e(SOURCE_NOTE)}.</footer>
</main></body></html>"""
