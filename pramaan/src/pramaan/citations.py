"""Grammar for Indian legal citations.

Finds reporter citations (SCC, SCR, AIR, SCC OnLine, INSC neutral citations,
High Court neutral citations, SCALE, JT, Cri LJ, MANU, ITR, Taxmann, LiveLaw),
groups parallel citations that refer to one case, recovers the case name that
precedes them, and attaches pinpoints and quoted passages.

Pure standard library. Every match keeps its character span so a report can
point back into the source document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

YEAR = r"(?P<year>1[89]\d{2}|20\d{2})"
SUPP = r"(?P<supp>Supp(?:l)?\.?)"

# Courts that the Supreme Court reporters and neutral citations belong to.
SC_COURT_CODES = {"SC", "S.C.", "SUPREME COURT", "S C"}


@dataclass
class Cite:
    kind: str
    raw: str
    start: int
    end: int
    year: Optional[int] = None
    volume: Optional[int] = None
    supp: bool = False
    page: Optional[int] = None
    number: Optional[int] = None
    court: Optional[str] = None
    series: Optional[str] = None

    @property
    def is_supreme_court(self) -> bool:
        if self.kind in {"SCC", "SCR", "INSC", "JT", "SCALE"}:
            return True
        if self.kind in {"AIR", "SCC_ONLINE", "LIVELAW", "MANU", "ITR", "TAXMANN"}:
            return (self.court or "").upper().replace(".", "").replace(" ", "") in {"SC", "SUPREMECOURT"}
        return False

    @property
    def key(self) -> str:
        """Canonical, reporter-specific key, e.g. ``SCC:2017:10:1``."""
        vol = ("S" if self.supp else "") + (str(self.volume) if self.volume is not None else "")
        court = _court_key(self.court)
        if self.kind == "INSC":
            return f"INSC:{self.year}:{self.number}"
        if self.kind == "HC_NEUTRAL":
            return f"HCN:{self.year}:{court}:{self.number}"
        if self.kind == "MANU":
            return f"MANU:{court}:{self.number}:{self.year}"
        if self.kind in {"SCC_ONLINE", "LIVELAW"}:
            return f"{self.kind}:{self.year}:{court}:{self.number}"
        if self.kind == "AIR":
            return f"AIR:{self.year}:{court}:{self.page}"
        if self.kind == "CRILJ":
            return f"CRILJ:{self.year}:{self.page}"
        series = f"({self.series})" if self.series else ""
        return f"{self.kind}{series}:{self.year}:{vol}:{self.page}"

    def pretty(self) -> str:
        return " ".join(self.raw.split())


@dataclass
class Quote:
    text: str
    start: int
    end: int


@dataclass
class Reference:
    """One cited authority: a case name plus zero or more parallel citations."""

    cites: list[Cite]
    start: int
    end: int
    case_name: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    pinpoint: Optional[str] = None
    quotes: list[Quote] = field(default_factory=list)
    year_hint: Optional[int] = None  # e.g. "Mercy v. Mankind (2015)" with no reporter

    @property
    def years(self) -> list[int]:
        ys = {c.year for c in self.cites if c.year}
        if self.year_hint:
            ys.add(self.year_hint)
        return sorted(ys)

    @property
    def is_supreme_court(self) -> bool:
        if not self.cites:
            return False
        return any(c.is_supreme_court for c in self.cites)

    @property
    def label(self) -> str:
        bits = []
        if self.case_name:
            bits.append(self.case_name)
        bits.extend(c.pretty() for c in self.cites)
        return ", ".join(bits) if bits else "(unnamed)"


def key_year(key: str) -> int:
    """The year encoded in a canonical citation key."""
    p = key.split(":")
    return int(p[3] if p[0] == "MANU" else p[1])


def _court_key(court: Optional[str]) -> str:
    if not court:
        return ""
    c = court.upper().replace(".", "").replace(" ", "")
    if c in {"SC", "SUPREMECOURT"}:
        return "SC"
    return c


def _int(s: Optional[str]) -> Optional[int]:
    return int(s) if s else None


# --------------------------------------------------------------------------
# Reporter patterns. Each yields named groups consumed by ``_build``.
# --------------------------------------------------------------------------

_SCC_ABBR = r"S\.?\s?C\.?\s?C\.?"
_SERIES = r"(?:\s*\((?P<series>Cri|Cr|L\s?&\s?S|Tax|Civ)\))?"
_VOL_OR_SUPP = rf"(?:{SUPP}\s*\(?\s*(?P<svol>\d{{1,2}})?\s*\)?|(?P<vol>\d{{1,2}}))"

PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "INSC",
        re.compile(rf"(?<![\w/]){YEAR}\s?INSC\s?(?P<number>\d{{1,5}})(?!\d)"),
    ),
    (
        "HC_NEUTRAL",
        re.compile(
            r"(?<![\w:])(?P<year>(?:19|20)\d{2}):(?P<court>[A-Z]{2,7}(?:-[A-Z]{2,5})?):(?P<number>\d{1,7})"
            r"(?:-(?P<suffix>DB|FB|LB))?(?![\w:])"
        ),
    ),
    (
        "SCC_ONLINE",
        re.compile(
            rf"(?<!\w){YEAR}\s+SCC\s?On\s?Line\s+(?P<court>[A-Z][A-Za-z&]{{0,9}}(?:\s(?:HC|Bom|Del))?)\.?\s+(?P<number>\d{{1,6}})(?!\d)",
            re.IGNORECASE,
        ),
    ),
    (
        "SCC",
        re.compile(
            rf"\(\s*{YEAR}\s*\)\s*{_VOL_OR_SUPP}\s*{_SCC_ABBR}(?!\s?On\s?Line){_SERIES}\s*(?P<page>\d{{1,4}})(?!\d)",
            re.IGNORECASE,
        ),
    ),
    (
        "SCC",
        re.compile(
            rf"(?<!\w){YEAR}\s*\(\s*(?P<vol>\d{{1,2}})\s*\)\s*{_SCC_ABBR}(?!\s?On\s?Line){_SERIES}\s*(?P<page>\d{{1,4}})(?!\d)",
            re.IGNORECASE,
        ),
    ),
    (
        "SCC",
        re.compile(
            rf"(?<!\w){YEAR}\s+{SUPP}\s*\(?\s*(?P<svol>\d{{1,2}})?\s*\)?\s*{_SCC_ABBR}{_SERIES}\s*(?P<page>\d{{1,4}})(?!\d)",
            re.IGNORECASE,
        ),
    ),
    (
        # Old cases reprinted in SCC without a volume: "1951 SCC 1088".
        "SCC",
        re.compile(rf"(?<!\w){YEAR}\s+S\.?C\.?C\.?\s+(?P<page>\d{{1,4}})(?!\d)"),
    ),
    (
        "SCR",
        re.compile(
            rf"[\[(]\s*{YEAR}\s*[\])]\s*(?:{_VOL_OR_SUPP}\s*)?S\.?\s?C\.?\s?R\.?\s*(?P<page>\d{{1,4}})(?!\d)",
            re.IGNORECASE,
        ),
    ),
    (
        "SCR",
        re.compile(
            rf"(?<![\w\[(]){YEAR}\s+(?:{_VOL_OR_SUPP}\s+)?S\.?C\.?R\.?\s+(?P<page>\d{{1,4}})(?!\d)",
        ),
    ),
    (
        "AIR",
        re.compile(
            rf"(?<!\w)A\.?\s?I\.?\s?R\.?\s*(?:Online\s+|OnLine\s+|ONLINE\s+)?{YEAR}\s+"
            r"(?P<court>S\.\s?C\.|SC|Supreme\s+Court|NOC|P\s?&\s?H|J\s?&\s?K|[A-Z][A-Za-z]{0,9}\.?)\s*(?:\(\s*Supp\s*\)\s*)?"
            r"(?P<page>\d{1,5})(?!\d)"
        ),
    ),
    (
        "SCALE",
        re.compile(rf"\(\s*{YEAR}\s*\)\s*(?P<vol>\d{{1,2}})\s+SCALE\s+(?P<page>\d{{1,4}})(?!\d)", re.IGNORECASE),
    ),
    (
        "SCALE",
        re.compile(rf"(?<!\w){YEAR}\s*\(\s*(?P<vol>\d{{1,2}})\s*\)\s*SCALE\s+(?P<page>\d{{1,4}})(?!\d)", re.IGNORECASE),
    ),
    (
        "JT",
        re.compile(rf"(?<!\w)J\.?T\.?\s+{YEAR}\s*\(\s*(?P<vol>\d{{1,2}})\s*\)\s*(?:S\.?C\.?\s+)?(?P<page>\d{{1,4}})(?!\d)"),
    ),
    (
        "CRILJ",
        re.compile(rf"(?<!\w){YEAR}\s+Cri?\.?\s?L\.?\s?J\.?\s+(?P<page>\d{{1,5}})(?!\d)", re.IGNORECASE),
    ),
    (
        "MANU",
        re.compile(rf"(?<!\w)MANU/(?P<court>[A-Z]{{2,4}})/(?P<number>\d{{1,5}})/{YEAR}(?!\d)"),
    ),
    (
        "LIVELAW",
        re.compile(rf"(?<!\w){YEAR}\s+Live\s?Law\s*\(\s*(?P<court>[A-Za-z&]{{2,10}})\s*\)\s*(?P<number>\d{{1,5}})(?!\d)", re.IGNORECASE),
    ),
    (
        "ITR",
        re.compile(
            rf"[\[(]\s*{YEAR}\s*[\])]\s*(?P<vol>\d{{1,4}})\s+ITR\s+(?P<page>\d{{1,4}})(?:\s*\(\s*(?P<court>SC|[A-Z][a-z]{{1,6}}\.?)\s*\))?",
        ),
    ),
    (
        "TAXMANN",
        re.compile(
            rf"\[\s*{YEAR}\s*\]\s*(?P<vol>\d{{1,4}})\s+taxmann\.com\s+(?P<page>\d{{1,5}})(?:\s*\(\s*(?P<court>SC|[A-Z][A-Za-z.\s-]{{1,20}}?)\s*\))?",
            re.IGNORECASE,
        ),
    ),
]


def _build(kind: str, m: re.Match) -> Cite:
    g = m.groupdict()
    supp = bool(g.get("supp"))
    vol = _int(g.get("svol")) if supp else _int(g.get("vol"))
    court = g.get("court")
    if kind == "HC_NEUTRAL" and (court or "").upper() == "INSC":
        kind, court = "INSC", None  # "2019:INSC:1366" written in High Court style
    if kind in {"SCR", "SCC", "INSC", "JT", "SCALE"}:
        court = "SC"
    series = g.get("series")
    if series:
        series = series.replace(" ", "").replace("Cr", "Cri").replace("Crii", "Cri")
    return Cite(
        kind=kind,
        raw=m.group(0),
        start=m.start(),
        end=m.end(),
        year=_int(g.get("year")),
        volume=vol,
        supp=supp,
        page=_int(g.get("page")),
        number=_int(g.get("number")),
        court=court.strip() if court else None,
        series=series,
    )


def find_cites(text: str) -> list[Cite]:
    """All reporter citations in ``text``, earliest first, overlaps removed."""
    found: list[Cite] = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            found.append(_build(kind, m))
    # Longest match wins where two patterns overlap.
    found.sort(key=lambda c: (c.start, -(c.end - c.start)))
    out: list[Cite] = []
    for c in found:
        if out and c.start < out[-1].end:
            continue
        out.append(c)
    return out


# --------------------------------------------------------------------------
# Case names
# --------------------------------------------------------------------------

_VERSUS_TOK = re.compile(r"(?:v\.|v|vs\.?|Vs\.?|versus|Versus|v/s\.?|V/s\.?)")
_VERSUS_TOK_UPPER = re.compile(r"(?:V\.|VS\.?|VERSUS|V/S\.?)")
_CONNECTORS = {
    "of", "and", "&", "the", "for", "de", "da", "del", "bin", "binti", "alias", "@",
    "in", "thr.", "thr", "through", "its", "on", "by", "at", "to", "ors.", "ors",
    "anr.", "anr", "etc.", "etc", "others", "another", "lrs.", "lrs", "since", "deceased", "v/s",
}
# Discourse words to trim from the front of a recovered left-hand party.
_LEAD_TRIM = {
    "in", "see", "vide", "also", "cf", "cf.", "e.g.", "eg", "case", "of", "the", "decision", "decisions",
    "judgment", "judgement", "held", "per", "as", "further", "similarly", "likewise", "thus", "recently",
    "again", "then", "moreover", "however", "and", "reliance", "placed", "on", "upon", "referred", "relied",
    "to", "by", "this", "hon'ble", "honble", "apex", "learned", "counsel", "cited", "reported", "a", "an",
    "court", "court's", "courts", "where", "which", "that", "while", "whereas", "from", "with", "but", "&",
    "here", "there", "followed", "following", "approved", "overruled", "distinguished", "following:",
    "said", "aforesaid", "famous", "landmark", "celebrated", "well-known", "matter", "titled", "styled",
    "relying", "referring", "citing", "if", "when", "since", "because", "although", "though", "after",
    "law", "cited", "issue", "issues", "consideration", "distinguished.", "headnote", "list", "references",
    "case-law", "precedents", "overruled.", "followed.", "approved.", "referred.", "relied.", "note", "for",
}
_TRAIL_TRIM = re.compile(
    r"(?:\s*(?:,|:|;|\(|\[|reported\s+(?:in|as|at)|cited\s+as|\bin\b|\bvide\b|\bat\b|@|=|-|–)\s*)+$", re.IGNORECASE
)
_RIGHT_STOP = {"held", "observed", "wherein", "where", "which", "that", "reported", "decided", "was", "is", "has"}
_NUMERIC = re.compile(r"^[\d.,:;/()\-–]+$")
_MONTHS = {"january", "february", "march", "april", "may", "june", "july", "august", "september",
           "october", "november", "december", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep",
           "sept", "oct", "nov", "dec"}


def _is_namey(tok: str) -> bool:
    t = tok.strip("()[],;:\"'“”‘’")
    if not t:
        return False
    if _NUMERIC.match(t):
        return False
    if t.lower().strip(".") in _MONTHS:
        return False
    if t.lower() in _CONNECTORS:
        return True
    if t[0].isupper():
        return True
    if t.lower().startswith("m/s"):
        return True
    return False


def _tokens(text: str, lo: int, hi: int) -> list[tuple[str, int, int]]:
    return [(m.group(0), lo + m.start(), lo + m.end()) for m in re.finditer(r"\S+", text[lo:hi])]


def _split_name(text: str, lo: int, hi: int):
    """Recover the case name that ends at ``hi``.

    Returns ``(name, petitioner, respondent, start)`` where ``start`` is the
    absolute offset at which the name begins, or ``None`` values if the text
    before ``hi`` does not end in a case name.
    """
    none = (None, None, None, None)
    w = text[lo:hi]
    tm = _TRAIL_TRIM.search(w)
    if tm:
        hi = lo + tm.start()
    toks = _tokens(text, lo, hi)
    if not toks:
        return none
    # Pick the versus marker: the last lowercase-style one, else the last uppercase-style one.
    vi = None
    for i in range(len(toks) - 1, 0, -1):
        if _VERSUS_TOK.fullmatch(toks[i][0]):
            vi = i
            break
    if vi is None:
        for i in range(len(toks) - 1, 0, -1):
            if _VERSUS_TOK_UPPER.fullmatch(toks[i][0]):
                vi = i
                break
    if vi is None:
        # "In re: ..." titles.
        joined = " ".join(t for t, _, _ in toks[-14:])
        m = re.search(r"(?:^|\s)((?:In\s+re|In\s+Re|IN\s+RE|Re)\s*:?\s+[A-Z][^;:]{2,120})$", joined)
        if m:
            name = m.group(1).strip(" ,")
            first = name.split()[0]
            start = next((s for t, s, _ in reversed(toks) if t == first), toks[0][1])
            return name, name, None, start
        return none
    right = toks[vi + 1:]
    if not right or len(right) > 22:
        return none
    if not (right[0][0][:1].isupper() or right[0][0].lower().startswith("m/s")):
        return none
    lower_run = 0
    for t, _, _ in right:
        if t.lower().strip(",.") in _RIGHT_STOP:
            return none
        if not _is_namey(t):
            lower_run += 1
            if lower_run >= 2:
                return none
        else:
            lower_run = 0
    picked: list[tuple[str, int, int]] = []
    for t, s, e in reversed(toks[:vi]):
        if len(picked) >= 14:
            break
        bare = t.strip("\"'“”‘’")
        if not bare or bare.endswith((";", ":")):
            break
        if bare.startswith(("(", "[")) and not bare.endswith((")", "]")):
            break
        if not _is_namey(bare):
            break
        # A sentence-ending lowercase word ("held.") is not part of a name.
        if bare.endswith(".") and bare[:-1].isalpha() and bare[:-1].islower() and len(bare) > 4:
            break
        picked.append((bare, s, e))
        if t != bare and t[0] in "\"'“‘":
            break
    picked.reverse()
    # Drop a run of ALL-CAPS heading words before a Title-case name ("LIST OF CITATIONS Bishwanath ...").
    caps = 0
    while caps < len(picked) and picked[caps][0].isupper() and len(picked[caps][0]) > 1:
        caps += 1
    if 2 <= caps < len(picked) and not picked[caps][0].isupper():
        picked = picked[caps:]
    # "Rule in X v. Y", "observations of the Court in X v. Y": the name starts after the last lowercase "in".
    for i in range(len(picked) - 1, 0, -1):
        if picked[i][0] in {"in", "see", "vide", "per", "In", "See", "Vide"} and i < len(picked) - 1:
            picked = picked[i + 1:]
            break
    while picked and picked[0][0].strip(",").lower() in _LEAD_TRIM:
        picked.pop(0)
    if not picked or not any(ch.isalpha() for ch in "".join(p[0] for p in picked)):
        return none
    left = " ".join(p[0] for p in picked).strip(" ,")
    right_s = " ".join(t for t, _, _ in right).strip(" ,").rstrip(" ,.")
    if right_s.endswith(")") and right_s.count("(") < right_s.count(")"):
        right_s = right_s[:-1].rstrip()
    right_s = right_s.strip("\"'“”‘’")
    if not right_s:
        return none
    return f"{left} v. {right_s}", left, right_s, picked[0][1]


_PIN = re.compile(
    r"^\s*[,;]?\s*(?:\(|\[)?\s*(?P<pin>(?:at\s+)?(?:paras?\.?|paragraphs?|pp?\.|pages?|@)\s*\.?\s*\d+(?:\s*(?:-|–|to|and|&|,)\s*\d+)*)",
    re.IGNORECASE,
)
_SEP_ONLY = re.compile(r"^[\s:;,=&]*(?:and|also|reported\s+in|=)?[\s:;,=]*$", re.IGNORECASE)


def _window_lo(text: str, prev_end: int, start: int, span: int = 320) -> int:
    lo = max(prev_end, start - span)
    window = text[lo:start]
    brk = max(window.rfind("\n\n"), window.rfind("\n \n"), window.rfind("\n\t\n"))
    return lo + brk if brk >= 0 else lo


def group_references(text: str, cites: list[Cite]) -> list[Reference]:
    """Group adjacent parallel citations and recover each group's case name."""
    groups: list[list[Cite]] = []
    for c in cites:
        if groups:
            prev = groups[-1][-1]
            gap = text[prev.end:c.start]
            if len(gap) <= 24 and _SEP_ONLY.match(gap):
                groups[-1].append(c)
                continue
        groups.append([c])
    refs: list[Reference] = []
    prev_end = 0
    for g in groups:
        start = g[0].start
        name, pet, res, nstart = _split_name(text, _window_lo(text, prev_end, start), start)
        ref = Reference(cites=g, start=nstart if nstart is not None else start, end=g[-1].end,
                        case_name=name, petitioner=pet, respondent=res)
        pm = _PIN.match(text[ref.end:ref.end + 60])
        if pm:
            ref.pinpoint = " ".join(pm.group("pin").split())
        refs.append(ref)
        prev_end = g[-1].end
    return refs


# --------------------------------------------------------------------------
# Case names cited with no reporter citation ("Mercy v. Mankind (2015)")
# --------------------------------------------------------------------------

_GENERIC_PARTY = {
    "petitioner", "petitioners", "respondent", "respondents", "appellant", "appellants", "state",
    "union", "plaintiff", "plaintiffs", "defendant", "defendants", "accused", "complainant",
    "applicant", "applicants", "opposite", "party", "parties", "others", "anr", "ors", "another",
}
_MARKER_ANY = re.compile(r"(?<=\s)(?:v\.|v|vs\.?|Vs\.?|VS\.?|V\.|versus|Versus|VERSUS|v/s\.?|V/s\.?|V/S\.?)(?=\s)")


def find_uncited_names(text: str, refs: list[Reference]) -> list[Reference]:
    covered = [(r.start, r.end) for r in refs]
    out: list[Reference] = []
    for mk in _MARKER_ANY.finditer(text):
        if any(s <= mk.start() <= e for s, e in covered):
            continue
        tail_hi = mk.end() + 160
        para = text.find("\n\n", mk.end(), tail_hi)
        if para >= 0:
            tail_hi = para
        rt = _tokens(text, mk.end(), min(tail_hi, len(text)))
        right: list[tuple[str, int, int]] = []
        for t, s, e in rt:
            bare = t.strip("()[],.;:\"'“”")
            if not bare or not _is_namey(t) or bare.lower() in _RIGHT_STOP:
                break
            if right and "\n" in text[right[-1][2]:s] and right[-1][0].endswith((".", ",")):
                break
            right.append((t, s, e))
            if len(right) >= 12 or t.endswith((",", ";", ":", "”", '"')) or (t.endswith(".") and len(bare) > 4 and bare.lower() not in {"ltd", "pvt", "corpn", "anr", "ors"}):
                break
        while right and right[-1][0].strip(",.;:").lower() in _CONNECTORS:
            right.pop()
        if not right:
            continue
        right_end = right[-1][2]
        name, pet, res, nstart = _split_name(text, _window_lo(text, 0, mk.start(), 200), right_end)
        if not name or not pet or not res:
            continue
        sig_l = [t for t in re.findall(r"[A-Za-z]+", pet) if t.lower() not in _GENERIC_PARTY | _CONNECTORS]
        sig_r = [t for t in re.findall(r"[A-Za-z]+", res) if t.lower() not in _GENERIC_PARTY | _CONNECTORS]
        if not sig_l or not sig_r:
            continue
        ym = re.match(r"\s*,?\s*[(\[]\s*((?:19|20)\d{2})\s*[)\]]", text[right_end:right_end + 14])
        ref = Reference(cites=[], start=nstart, end=right_end, case_name=name, petitioner=pet, respondent=res,
                        year_hint=int(ym.group(1)) if ym else None)
        out.append(ref)
        covered.append((ref.start, ref.end))
    return out


# --------------------------------------------------------------------------
# Quotations
# --------------------------------------------------------------------------

_QUOTE = re.compile(r"“([^”]{30,6000})”|\"([^\"]{30,6000})\"")


def find_quotes(text: str, min_words: int = 8) -> list[Quote]:
    out = []
    for m in _QUOTE.finditer(text):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        if len(body.split()) >= min_words:
            out.append(Quote(text=body.strip(), start=m.start(), end=m.end()))
    return out


def attach_quotes(refs: list[Reference], quotes: list[Quote], text: str) -> None:
    """Attach each quotation to the authority it is attributed to.

    A quote belongs to the closest preceding reference (within 700 characters, with
    no other reference in between); failing that, to a reference that follows it
    within 150 characters ("...," (Name, cite)).
    """
    ordered = sorted(refs, key=lambda r: r.start)
    for q in quotes:
        before = [r for r in ordered if r.end <= q.start]
        after = [r for r in ordered if r.start >= q.end]
        if before and q.start - before[-1].end <= 700:
            before[-1].quotes.append(q)
        elif after and after[0].start - q.end <= 150:
            after[0].quotes.append(q)


def extract(text: str, uncited: bool = True) -> list[Reference]:
    """Extract every cited authority from ``text``."""
    cites = find_cites(text)
    refs = group_references(text, cites)
    if uncited:
        refs = refs + find_uncited_names(text, refs)
    refs.sort(key=lambda r: r.start)
    attach_quotes(refs, find_quotes(text), text)
    return refs
