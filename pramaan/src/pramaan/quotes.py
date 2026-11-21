"""Check whether a quoted passage really appears in the judgment it is attributed to.

The commonest form of AI fabrication that survives a citation check is a real
case with an invented paragraph. Supreme Court, Pooja Ramesh Singh v. J&K Bank
(2026 INSC 668): "even where case citations are accurate, the excerpted
paragraphs ... are not traceable to those judgments".

Matching is done on word n-grams so that line breaks, page headers, hyphenation
and minor punctuation differences between the brief and the PDF do not matter,
while a paraphrase or an invented sentence does.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .corpus import Judgment, default_db_path


def _words(text: str) -> list[str]:
    t = text.lower()
    t = re.sub(r"-\s*\n\s*", "", t)
    t = t.replace("’", "'").replace("‘", "'")
    t = re.sub(r"\[[^\]]{0,40}\]", " ", t)  # editorial insertions: [the appellant]
    return re.findall(r"[a-z0-9]+", t)


def _ngrams(words: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]


@dataclass
class QuoteResult:
    quote: str
    score: float  # share of the quote's word n-grams found in the judgment
    status: str  # FOUND | PARTIAL | NOT_FOUND | UNCHECKED
    snippet: Optional[str] = None


def match_quote(quote: str, judgment_text: str, words_cache: Optional[list[str]] = None) -> QuoteResult:
    jw = words_cache if words_cache is not None else _words(judgment_text)
    segments = [s for s in re.split(r"\.{3,}|…|\*\s*\*\s*\*", quote) if len(_words(s)) >= 4]
    if not segments:
        segments = [quote]
    total = hit = 0
    best_pos: list[int] = []
    for seg in segments:
        qw = _words(seg)
        n = 5 if len(qw) >= 12 else 3
        if len(qw) < n:
            continue
        index: dict[tuple[str, ...], int] = {}
        for i, g in enumerate(_ngrams(jw, n)):
            index.setdefault(g, i)
        grams = _ngrams(qw, n)
        found = [index[g] for g in grams if g in index]
        total += len(grams)
        hit += len(found)
        best_pos.extend(found)
    score = hit / total if total else 0.0
    status = "FOUND" if score >= 0.8 else "PARTIAL" if score >= 0.4 else "NOT_FOUND"
    snippet = None
    if best_pos:
        best_pos.sort()
        mid = best_pos[len(best_pos) // 2]
        snippet = " ".join(jw[max(0, mid - 12): mid + 40])
    return QuoteResult(quote=quote, score=round(score, 3), status=status, snippet=snippet)


class TextSource:
    """Judgment full text: local text directory first, then the open PDF (cached)."""

    def __init__(self, text_dir: Optional[Path] = None, cache_dir: Optional[Path] = None, allow_network: bool = True):
        env = os.environ.get("PRAMAAN_TEXTS")
        self.text_dir = Path(text_dir or env) if (text_dir or env) else None
        self.cache_dir = Path(cache_dir or default_db_path().parent / "texts")
        self.allow_network = allow_network
        self._mem: dict[int, list[str]] = {}

    def _local(self, j: Judgment) -> Optional[str]:
        if not self.text_dir:
            return None
        for cand in (self.text_dir / str(j.part_year) / f"{j.path}_EN.txt", self.text_dir / f"{j.path}_EN.txt"):
            if cand.exists():
                return cand.read_text(errors="ignore")
        return None

    def text(self, j: Judgment) -> Optional[str]:
        t = self._local(j)
        if t is not None:
            return t
        cached = self.cache_dir / f"{j.path}.txt"
        if cached.exists():
            return cached.read_text(errors="ignore")
        if not self.allow_network:
            return None
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "j.pdf"
            try:
                urllib.request.urlretrieve(j.pdf_url, pdf)
            except Exception:
                return None
            t = pdf_to_text(pdf)
        if t:
            cached.write_text(t)
        return t

    def words(self, j: Judgment) -> Optional[list[str]]:
        if j.id not in self._mem:
            t = self.text(j)
            if t is None:
                return None
            self._mem[j.id] = _words(t)
        return self._mem[j.id]


def pdf_to_text(pdf: Path) -> Optional[str]:
    if shutil.which("pdftotext"):
        try:
            out = subprocess.run(["pdftotext", "-q", str(pdf), "-"], capture_output=True, timeout=120)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.decode("utf-8", errors="ignore")
        except (subprocess.SubprocessError, OSError):
            pass
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        return "\n".join(p.extract_text() or "" for p in PdfReader(str(pdf)).pages)
    except Exception:
        return None
