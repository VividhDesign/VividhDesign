"""Entry points for the in-browser build (Pyodide).

The browser loads the same package and a prebuilt index, so a document is
checked entirely on the user's machine: nothing is uploaded anywhere. The only
network requests are for public judgment PDFs, fetched when a quote needs
checking.

JavaScript drives it in three steps:

1. ``load(db_path)`` once;
2. ``plan(text)`` returns the judgment PDFs whose text is needed for quotes;
   JavaScript fetches them and hands each to ``add_pdf(doc_id, bytes)``;
3. ``check(text)`` returns the findings as JSON (same shape as the server API).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Optional

from .citations import extract
from .corpus import SOURCE_NOTE, Corpus, Judgment
from .documents import read_bytes
from .quotes import TextSource, pdf_to_text
from .report import summary
from .verify import Verifier


class MemoryTexts(TextSource):
    """Judgment texts handed in by the page."""

    def __init__(self) -> None:
        super().__init__(allow_network=False)
        self.store: dict[int, str] = {}

    def text(self, j: Judgment) -> Optional[str]:
        return self.store.get(j.id)


_S: dict = {}


def load(db_path: str) -> str:
    corpus = Corpus(Path(db_path))
    texts = MemoryTexts()
    _S.update(corpus=corpus, texts=texts, verifier=Verifier(corpus, texts))
    lo, hi = corpus.year_range
    return json.dumps({"judgments": len(corpus), "years": [lo, hi], "attested_citations": len(corpus.attest),
                       "source": SOURCE_NOTE})


def document_text(filename: str, data: bytes) -> str:
    return read_bytes(filename, bytes(data))


def plan(text: str) -> str:
    """Judgments whose full text is needed to check quoted passages."""
    v: Verifier = _S["verifier"]
    saved, v.check_quotes = v.check_quotes, False
    try:
        need = {}
        for ref in extract(text):
            if not ref.quotes:
                continue
            f = v.verify(ref)
            doc = f.match.doc if f.match is not None else None
            if doc is not None and f.status in {"VERIFIED", "CASE_FOUND"} and doc.id not in _S["texts"].store:
                need[doc.id] = doc.pdf_url
    finally:
        v.check_quotes = saved
    return json.dumps([{"id": k, "url": u} for k, u in need.items()])


def add_pdf(doc_id: int, data: bytes) -> bool:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(bytes(data))
        f.flush()
        t = pdf_to_text(Path(f.name))
    if t:
        _S["texts"].store[int(doc_id)] = t
    return bool(t)


def check(text: str) -> str:
    v: Verifier = _S["verifier"]
    findings = [v.verify(r) for r in extract(text)]
    return json.dumps({"text": text, "summary": summary(findings), "findings": [f.as_dict() for f in findings]},
                      ensure_ascii=False)
