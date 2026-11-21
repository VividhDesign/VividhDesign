"""Mine an open citation concordance from the judgments themselves.

SCC, AIR and SCC OnLine are proprietary reporters, so there is no open table
mapping ``(2018) 16 SCC 228`` to a case. But Supreme Court judgments cite
earlier cases by name *and* reporter all the time, and the SCR headnotes list
parallel citations ("(2020) 2 SCC 677 : [2019] 16 SCR 252"). Every such pair
is an attestation, made in an official judgment, that this citation belongs to
this case. Aggregating them over tens of thousands of judgments gives an open
concordance that covers cases the SCR corpus itself does not contain.
"""

from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional

from .citations import extract, key_year
from .corpus import Corpus
from .names import tokens

_HEADER = re.compile(
    r"^.*(?:SUPREME\s+COURT\s+REPORTS|S\.C\.R\.\s*\d*\s*:\s*\d{4}\s+INSC).*$|^\s*\d{1,4}\s*$", re.MULTILINE
)
_MARGIN_LEAD = re.compile(r"^[ \t]{0,14}[A-H](?=[ \t]{2,})", re.MULTILINE)
_MARGIN_TRAIL = re.compile(r"[ \t]{2,}[A-H][ \t]*$", re.MULTILINE)


def clean_judgment_text(t: str) -> str:
    """Strip SCR running headers, page numbers and the A-H margin letters."""
    t = t.replace("\f", "\n")
    t = _HEADER.sub("", t)
    t = _MARGIN_LEAD.sub("", t)
    t = _MARGIN_TRAIL.sub("", t)
    t = re.sub(r"-\n\s*(?=[a-z])", "", t)  # re-join hyphenated words
    t = re.sub(r"[ \t]+", " ", t)
    return t


def _same_name(a: tuple[str, str], b: tuple[str, str]) -> bool:
    ta, tb = set(tokens(a[0])) | set(tokens(a[1])), set(tokens(b[0])) | set(tokens(b[1]))
    if not ta or not tb:
        return False
    return len(ta & tb) / min(len(ta), len(tb)) >= 0.6


# Judgments that *discuss* fabricated citations quote them. Those mentions are
# not attestations: Pooja Ramesh Singh v. J&K Bank (2026 INSC 668) lists the
# NCLT's six fake citations precisely in order to condemn them.
_SUSPECT = re.compile(
    r"non-?\s?existent|\bfake\b|hallucinat|fabricat|AI[- ]generated|artificial\s+intelligence|not\s+traceable|"
    r"does\s+not\s+exist|do\s+not\s+exist|never\s+existed|spurious|bogus|could\s+not\s+be\s+(?:located|found|traced)|"
    r"no\s+such\s+(?:judgment|decision|case)|wrong(?:ly)?\s+cited|incorrect(?:ly)?\s+cited|mis-?cited",
    re.IGNORECASE,
)
SUSPECT_WINDOW = 1500
# A judgment that is *about* fabricated authorities is not used as evidence for
# any citation it mentions (it may quote the fakes far from the words that
# condemn them).
_ABOUT_FAKES = re.compile(
    r"hallucinat|AI[- ]generated|artificial\s+intelligence|(?:non-?\s?existent|fake|fabricated|fictitious|"
    r"bogus|spurious)\s+(?:judgments?|citations?|precedents?|cases?|decisions?|authorit)",
    re.IGNORECASE,
)


def _extract_doc(item: tuple[str, str]) -> tuple[str, list[tuple[list[str], Optional[str], Optional[str]]]]:
    citing, raw = item
    out = []
    text = clean_judgment_text(raw)
    if len(_ABOUT_FAKES.findall(text)) >= 2:
        return citing, out
    for ref in extract(text, uncited=False):
        if _SUSPECT.search(text, max(0, ref.start - SUSPECT_WINDOW), ref.end + SUSPECT_WINDOW):
            continue
        keys = [c.key for c in ref.cites if c.is_supreme_court and c.year and c.year >= 1950]
        if keys:
            ok = bool(ref.petitioner and ref.respondent)
            out.append((keys, ref.petitioner if ok else None, ref.respondent if ok else None))
    return citing, out


_W: dict = {}


def _init_worker(db_path: str) -> None:
    _W["corpus"] = Corpus(Path(db_path))


def _resolve(item: tuple[str, str, int]) -> tuple[tuple[str, str, int], Optional[int]]:
    pet, res, year = item
    corpus: Corpus = _W["corpus"]
    for d, s in corpus.names.search(pet, res, k=3):
        dy = corpus.docs[d].decision_year or 0
        if s >= 0.85 and year - 2 <= dy <= year:
            return item, d
    return item, None


def mine(texts: Iterable[tuple[str, str]], corpus: Corpus, workers: int = 1, log=print) -> list[tuple]:
    """Return attestation rows ``(cite_key, pet, res, votes, doc_id, via, example, hc_votes)``.

    ``texts`` yields ``(citing_id, raw_text)``. Citing ids that start with ``HC:``
    are High Court judgments; they count as votes and are also tallied in ``hc_votes``.
    """
    clusters: dict[str, list[list]] = defaultdict(list)
    parallel: dict[str, set[str]] = defaultdict(set)
    n_docs = 0
    pool = None
    if workers > 1:
        import multiprocessing as mp
        pool = mp.get_context("fork").Pool(workers)
        stream = pool.imap_unordered(_extract_doc, texts, chunksize=16)
    else:
        stream = map(_extract_doc, texts)
    for citing, refs in stream:
        n_docs += 1
        for keys, pet, res in refs:
            for k in keys:
                parallel[k].update(x for x in keys if x != k)
            if not pet:
                continue
            name = (pet, res)
            for k in keys:
                for cl in clusters[k]:
                    if _same_name(cl[0], name):
                        cl[1].add(citing)
                        break
                else:
                    clusters[k].append([name, {citing}])
        if n_docs % 1000 == 0:
            log(f"  read {n_docs} judgments, {len(clusters)} distinct citations so far")
    if pool is not None:
        pool.close()
        pool.join()

    def direct(key: str) -> Optional[int]:
        p = key.split(":")
        if p[0] == "SCR":
            vol = p[2]
            supp = vol.startswith("S")
            v = int(vol[1:]) if supp and len(vol) > 1 else (int(vol) if vol and not supp else None)
            return corpus.by_scr(int(p[1]), supp, v, int(p[3]))
        if p[0] == "INSC":
            return corpus.by_nc.get((int(p[1]), int(p[2])))
        return None

    staged = []  # (key, pet, res, votes, doc_id, via)
    examples = []  # one citing judgment per row, for provenance
    need: set[tuple[str, str, int]] = set()
    for key, cls in clusters.items():
        year = key_year(key)
        via_parallel = None
        for other in sorted(parallel.get(key, ())):
            d = direct(other)
            if d is not None:
                via_parallel = d
                break
        for (pet, res), citing in cls:
            doc_id, via = direct(key), "direct"
            if doc_id is None and via_parallel is not None:
                doc_id, via = via_parallel, "parallel"
            if doc_id is not None and corpus.names.score(pet, res, doc_id) < 0.5:
                doc_id, via = None, None  # the parallel cite named in the group is another case
            if doc_id is None:
                need.add((pet, res, year))
            staged.append([key, pet, res, len(citing), doc_id, via])
            sc_citing = [c for c in citing if not c.startswith("HC:")]
            examples.append((min(sc_citing) if sc_citing else min(citing), len(citing) - len(sc_citing)))
    log(f"  resolving {len(need)} case names against the official record")
    if workers > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(workers, initializer=_init_worker, initargs=(str(corpus.db_path),)) as p:
            resolved = dict(p.imap_unordered(_resolve, sorted(need), chunksize=64))
    else:
        _W["corpus"] = corpus
        resolved = dict(map(_resolve, sorted(need)))
    rows = []
    for (key, pet, res, votes, doc_id, via), (example, hc_votes) in zip(staged, examples):
        if doc_id is None:
            doc_id = resolved.get((pet, res, key_year(key)))
            via = "name" if doc_id is not None else None
        rows.append((key, pet, res, votes, doc_id, via, example, hc_votes))
    log(f"Mined {len(rows)} attestations for {len(clusters)} citations from {n_docs} judgments")
    return rows


def save(rows: list[tuple], db_path: Path, through: Optional[int] = None) -> None:
    """Store attestations. ``through`` is the latest year of judgments mined: citations
    newer than a few years before it have had little chance to be cited yet."""
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    if through:
        con.execute("INSERT OR REPLACE INTO meta VALUES ('mined_through', ?)", (str(through),))
    con.execute("DROP TABLE IF EXISTS attest")
    con.execute(
        "CREATE TABLE attest (cite_key TEXT, pet TEXT, res TEXT, votes INTEGER, doc_id INTEGER, via TEXT,"
        " example TEXT, hc_votes INTEGER DEFAULT 0)"
    )
    rows = [tuple(r) + (None,) * (7 - len(r)) + ((0,) if len(r) < 8 else ()) for r in rows]
    con.executemany("INSERT INTO attest VALUES (?,?,?,?,?,?,?,?)", rows)
    con.execute("CREATE INDEX IF NOT EXISTS attest_key ON attest(cite_key)")
    con.commit()
    con.close()


def iter_text_dir(root: Path, years: Optional[range] = None) -> Iterable[tuple[str, str]]:
    """Supreme Court judgment texts laid out as ``<year>/<path>_EN.txt``."""
    for p in sorted(root.rglob("*.txt")):
        y = p.parent.name
        if years is not None and (not y.isdigit() or int(y) not in years):
            continue
        yield p.stem, p.read_text(errors="ignore")


def iter_hc_text_dir(root: Path) -> Iterable[tuple[str, str]]:
    """High Court judgment texts (any layout); ids are prefixed ``HC:``."""
    for p in sorted(root.rglob("*.txt")):
        yield f"HC:{p.parent.name}/{p.stem}", p.read_text(errors="ignore")


def export_tsv(db_path: Path, out: Path) -> int:
    """Write attestations to a gzipped TSV keyed by judgment path (portable across index builds)."""
    import gzip

    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT a.cite_key, a.pet, a.res, a.votes, d.path, a.via, a.example, a.hc_votes FROM attest a"
        " LEFT JOIN judgments d ON d.id = a.doc_id ORDER BY a.cite_key"
    ).fetchall()
    con.close()
    clean = lambda v: "" if v is None else str(v).replace("\t", " ").replace("\n", " ")  # noqa: E731
    with gzip.open(out, "wt", encoding="utf-8") as f:
        f.write("cite_key\tpetitioner\trespondent\tvotes\tjudgment_path\tvia\texample\thc_votes\n")
        for r in rows:
            f.write("\t".join(clean(v) for v in r) + "\n")
    return len(rows)


def import_tsv(src: Path, db_path: Path) -> int:
    import gzip

    con = sqlite3.connect(db_path)
    ids = dict(con.execute("SELECT path, id FROM judgments"))
    rows = []
    with gzip.open(src, "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            k, p, r, v, path, via, ex = parts[:7]
            hc = int(parts[7]) if len(parts) > 7 and parts[7] else 0
            rows.append((k, p, r, int(v), ids.get(path) if path else None, via or None, ex or None, hc))
    con.close()
    save(rows, db_path)
    return len(rows)
