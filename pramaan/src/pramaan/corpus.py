"""Local index of Supreme Court of India judgments.

Built from the open "Indian Supreme Court Judgments" dataset (CC-BY-4.0,
https://registry.opendata.aws/indian-supreme-court-judgments/), which mirrors
every judgment published in the official Supreme Court Reports (SCR) since 1950
along with its neutral citation (INSC).

The index lives in one SQLite file. ``pramaan sync`` builds it; everything
after that runs offline except the optional on-demand fetch of a judgment's
text for quote checking.
"""

from __future__ import annotations

import bisect
import os
import re
import sqlite3
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from .names import NameIndex, tokens as name_tokens

BUCKET = "https://indian-supreme-court-judgments.s3.amazonaws.com"
FIRST_YEAR = 1950
SOURCE_NOTE = (
    "Indian Supreme Court Judgments (Dattam Labs / AWS Open Data, CC-BY-4.0), "
    "https://registry.opendata.aws/indian-supreme-court-judgments/"
)


def default_db_path() -> Path:
    env = os.environ.get("PRAMAAN_DB")
    if env:
        return Path(env)
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "pramaan" / "sc.sqlite"


@dataclass
class Judgment:
    id: int
    title: str
    petitioner: str
    respondent: str
    decision_date: Optional[str]
    decision_year: Optional[int]
    part_year: int
    scr_year: Optional[int]
    scr_supp: bool
    scr_vol: Optional[int]
    scr_start: Optional[int]
    scr_end: Optional[int]
    nc_year: Optional[int]
    nc_num: Optional[int]
    path: str
    judges: str = ""

    @property
    def scr_citation(self) -> Optional[str]:
        if self.scr_year is None:
            return None
        supp = "Supp. " if self.scr_supp else ""
        return f"[{self.scr_year}] {supp}{self.scr_vol} S.C.R. {self.scr_start}"

    @property
    def neutral_citation(self) -> Optional[str]:
        if self.nc_year is None:
            return None
        return f"{self.nc_year} INSC {self.nc_num}"

    @property
    def pdf_url(self) -> str:
        return f"{BUCKET}/data/pdf/year={self.part_year}/english/{self.path}_EN.pdf"

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "decision_date": self.decision_date,
            "scr": self.scr_citation,
            "neutral": self.neutral_citation,
            "judges": self.judges,
            "pdf_url": self.pdf_url,
        }


SCHEMA = """
CREATE TABLE IF NOT EXISTS judgments (
    id INTEGER PRIMARY KEY,
    title TEXT, petitioner TEXT, respondent TEXT,
    decision_date TEXT, decision_year INTEGER, part_year INTEGER,
    scr_year INTEGER, scr_supp INTEGER, scr_vol INTEGER, scr_start INTEGER, scr_end INTEGER,
    nc_year INTEGER, nc_num INTEGER,
    path TEXT UNIQUE, judges TEXT
);
CREATE TABLE IF NOT EXISTS attest (
    cite_key TEXT, pet TEXT, res TEXT, votes INTEGER, doc_id INTEGER, via TEXT, example TEXT
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""

_PATH = re.compile(r"^(?P<supp>S_)?(?P<year>\d{4})_(?P<vol>\d+)_(?P<start>\d+)_(?P<end>\d+)$")
_NC = re.compile(r"(\d{4})\s?INSC\s?(\d+)")


def _iso(d: Optional[str]) -> Optional[str]:
    if not d:
        return None
    m = re.match(r"(\d{2})-(\d{2})-(\d{4})", d)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return d


def _row_from_record(rec: dict) -> Optional[tuple]:
    path = (rec.get("path") or "").strip()
    if not path:
        return None
    pm = _PATH.match(path)
    scr = (None, 0, None, None, None)
    if pm:
        scr = (int(pm["year"]), 1 if pm["supp"] else 0, int(pm["vol"]), int(pm["start"]), int(pm["end"]))
    nc = _NC.search(rec.get("nc_display") or "") or _NC.search(rec.get("case_id") or "")
    iso = _iso(rec.get("decision_date"))
    dyear = int(iso[:4]) if iso and iso[:4].isdigit() else None
    return (
        (rec.get("title") or "").strip(),
        (rec.get("petitioner") or "").strip(),
        (rec.get("respondent") or "").strip(),
        iso,
        dyear,
        int(rec.get("year") or scr[0] or 0),
        *scr,
        int(nc.group(1)) if nc else None,
        int(nc.group(2)) if nc else None,
        path,
        (rec.get("judge") or "").strip(),
    )


def build_db(records: Iterable[dict], db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    n = 0
    for rec in records:
        row = _row_from_record(rec)
        if row is None:
            continue
        cur = con.execute(
            "INSERT OR IGNORE INTO judgments (title, petitioner, respondent, decision_date, decision_year,"
            " part_year, scr_year, scr_supp, scr_vol, scr_start, scr_end, nc_year, nc_num, path, judges)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            row,
        )
        n += cur.rowcount
    con.execute("INSERT OR REPLACE INTO meta VALUES ('source', ?)", (SOURCE_NOTE,))
    con.execute("INSERT OR REPLACE INTO meta VALUES ('built', ?)", (date.today().isoformat(),))
    con.commit()
    con.close()
    return n


def iter_parquet_records(paths: Iterable[Path]) -> Iterable[dict]:
    try:
        import pyarrow.parquet as pq
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise SystemExit("Building the index needs pyarrow: pip install 'pramaan[sync]'") from e
    cols = ["title", "petitioner", "respondent", "judge", "decision_date", "path", "nc_display", "case_id", "year"]
    for p in paths:
        table = pq.read_table(p, columns=cols)
        yield from table.to_pylist()


def sync(db_path: Optional[Path] = None, cache_dir: Optional[Path] = None, last_year: Optional[int] = None,
         log=print) -> Path:
    """Download per-year metadata from the open dataset and (re)build the index."""
    db_path = db_path or default_db_path()
    cache_dir = cache_dir or db_path.parent / "parquet"
    cache_dir.mkdir(parents=True, exist_ok=True)
    last_year = last_year or date.today().year
    files = []
    for y in range(FIRST_YEAR, last_year + 1):
        dest = cache_dir / f"metadata_{y}.parquet"
        url = f"{BUCKET}/metadata/parquet/year={y}/metadata.parquet"
        try:
            urllib.request.urlretrieve(url, dest)
            files.append(dest)
        except Exception as e:  # a year may not exist yet
            log(f"  {y}: skipped ({e})")
    tmp = db_path.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    # Keep attestations that were already mined (they reference judgments by path).
    old = []
    if db_path.exists():
        con = sqlite3.connect(db_path)
        try:
            old = con.execute(
                "SELECT a.cite_key, a.pet, a.res, a.votes, d.path, a.via, a.example FROM attest a"
                " LEFT JOIN judgments d ON d.id = a.doc_id"
            ).fetchall()
        except sqlite3.Error:
            old = []
        con.close()
    n = build_db(iter_parquet_records(files), tmp)
    if old:
        con = sqlite3.connect(tmp)
        ids = dict(con.execute("SELECT path, id FROM judgments"))
        con.executemany("INSERT INTO attest VALUES (?,?,?,?,?,?,?)",
                        [(k, p, r, v, ids.get(path), via, ex) for k, p, r, v, path, via, ex in old])
        con.commit()
        con.close()
    if not old:
        bundled = Path(__file__).parent / "data" / "attestations.tsv.gz"
        if bundled.exists():
            from .mine import import_tsv

            m = import_tsv(bundled, tmp)
            log(f"Loaded {m} citation attestations bundled with Pramaan")
            con = sqlite3.connect(tmp)
            meta = (Path(__file__).parent / "data" / "attestations.meta").read_text().strip() \
                if (Path(__file__).parent / "data" / "attestations.meta").exists() else ""
            if meta.isdigit():
                con.execute("INSERT OR REPLACE INTO meta VALUES ('mined_through', ?)", (meta,))
            con.commit()
            con.close()
    tmp.replace(db_path)
    log(f"Indexed {n} judgments into {db_path}")
    return db_path


class Corpus:
    """In-memory view of the index with the lookups the verifier needs."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or default_db_path())
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"No judgment index at {self.db_path}. Run `pramaan sync` first (or set PRAMAAN_DB)."
            )
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        self.docs: dict[int, Judgment] = {}
        self.by_nc: dict[tuple[int, int], int] = {}
        self.max_nc: dict[int, int] = defaultdict(int)
        self._scr: dict[tuple[int, int, int], list[tuple[int, int, int]]] = defaultdict(list)
        self._scr_year: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
        self.names = NameIndex()
        for r in con.execute("SELECT * FROM judgments"):
            j = Judgment(
                id=r["id"], title=r["title"], petitioner=r["petitioner"], respondent=r["respondent"],
                decision_date=r["decision_date"], decision_year=r["decision_year"], part_year=r["part_year"],
                scr_year=r["scr_year"], scr_supp=bool(r["scr_supp"]), scr_vol=r["scr_vol"],
                scr_start=r["scr_start"], scr_end=r["scr_end"], nc_year=r["nc_year"], nc_num=r["nc_num"],
                path=r["path"], judges=r["judges"] or "",
            )
            self.docs[j.id] = j
            if j.nc_year:
                self.by_nc[(j.nc_year, j.nc_num)] = j.id
                self.max_nc[j.nc_year] = max(self.max_nc[j.nc_year], j.nc_num)
            if j.scr_year is not None:
                self._scr[(j.scr_year, int(j.scr_supp), j.scr_vol)].append((j.scr_start, j.scr_end, j.id))
                self._scr_year[j.scr_year].append((j.scr_start, j.scr_end, j.id))
            self.names.add(j.id, j.petitioner or j.title, j.respondent)
        for v in self._scr.values():
            v.sort()
        # Attestations: (cite_key -> [(pet, res, votes, doc_id)]) mined from judgment texts.
        self.attest: dict[str, list[tuple[str, str, int, Optional[int]]]] = defaultdict(list)
        self.attest_names = NameIndex()
        self._attest_rows: list[tuple[str, str, str, int, Optional[int]]] = []
        try:
            rows = con.execute("SELECT cite_key, pet, res, votes, doc_id, example FROM attest").fetchall()
        except sqlite3.Error:
            rows = []
        self.example: dict[tuple[str, str, str], str] = {}
        self.by_path = {j.path: j.id for j in self.docs.values()}
        for key, pet, res, votes, doc_id, ex in rows:
            if ex:
                self.example[(key, pet, res)] = ex
        rows = [r[:5] for r in rows]
        for key, pet, res, votes, doc_id in rows:
            self.attest[key].append((pet, res, votes, doc_id))
            self._attest_rows.append((key, pet, res, votes, doc_id))
        # Name index over attested cases the SCR corpus lacks, so name-only search covers them.
        self.attest_names.df = self.names.df
        self.attest_names.n = self.names.n
        for i, (key, pet, res, votes, doc_id) in enumerate(self._attest_rows):
            if doc_id is None:
                tp, tr = name_tokens(pet), name_tokens(res)
                self.attest_names.parties[i] = (tp, tr)
                for t in set(tp) | set(tr):
                    self.attest_names.post[t].add(i)
                    if len(t) >= 6:
                        self.attest_names.prefix[t[:6]].add(i)
        self.keys_of: dict[int, list[str]] = defaultdict(list)
        for key, pet, res, votes, doc_id in self._attest_rows:
            if doc_id is not None and key not in self.keys_of[doc_id]:
                self.keys_of[doc_id].append(key)
        self.meta = dict(con.execute("SELECT key, value FROM meta"))
        con.close()
        years = [j.decision_year for j in self.docs.values() if j.decision_year]
        self.year_range = (min(years), max(years)) if years else (None, None)
        mt = self.meta.get("mined_through")
        self.mined_through = int(mt) if mt and mt.isdigit() else self.year_range[1]

    def __len__(self) -> int:
        return len(self.docs)

    def by_scr(self, year: int, supp: bool, vol: Optional[int], page: int) -> Optional[int]:
        """The judgment whose SCR page range contains ``page``."""
        if vol is None:
            spans = sorted(self._scr_year.get(year, []))
        else:
            spans = self._scr.get((year, int(supp), vol), [])
        i = bisect.bisect_right(spans, (page, float("inf"), 0)) - 1
        while i >= 0:
            s, e, doc = spans[i]
            if s <= page <= e:
                return doc
            if e < page and s < page - 2000:
                break
            i -= 1
        return None

    def scr_volume_known(self, year: int, supp: bool, vol: Optional[int]) -> bool:
        if vol is None:
            return year in self._scr_year
        return (year, int(supp), vol) in self._scr

    def attestations(self, key: str) -> list[tuple[str, str, int, Optional[int]]]:
        return sorted(self.attest.get(key, []), key=lambda x: -x[2])

    def attest_row(self, i: int) -> tuple[str, str, str, int, Optional[int]]:
        return self._attest_rows[i]

    def citing_example(self, key: str, pet: str, res: str) -> Optional[Judgment]:
        """A judgment that cites ``key`` under this name (text files are named ``<path>_EN``)."""
        ex = self.example.get((key, pet, res))
        if not ex:
            return None
        doc = self.by_path.get(ex[:-3] if ex.endswith("_EN") else ex)
        return self.docs.get(doc) if doc is not None else None
