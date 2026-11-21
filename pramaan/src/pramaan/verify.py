"""Decide, for each cited authority, whether it is real and correctly cited.

Evidence comes from two independent open sources:

* the official record: every judgment in the Supreme Court Reports since 1950,
  with its SCR page range and neutral (INSC) citation;
* attestations: (citation, case name) pairs that Supreme Court judgments
  themselves use when citing earlier cases (see ``mine.py``).

A finding is ``high`` risk only when the evidence positively contradicts the
citation (it belongs to another case, the case was decided in another year,
the quoted passage is absent) or when a Supreme Court citation matches nothing
at all. Anything the open record cannot settle is marked ``review``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .citations import Cite, Reference, extract, key_year
from .corpus import Corpus, Judgment
from .quotes import QuoteResult, TextSource, match_quote

T_MATCH = 0.70  # names agree
T_LOW = 0.45  # names clearly disagree below this

RISK_ORDER = {"high": 0, "review": 1, "ok": 2, "skip": 3}

STATUS_TEXT = {
    "VERIFIED": "Verified",
    "CASE_FOUND": "Case exists",
    "WRONG_CITATION": "Citation belongs to a different case",
    "YEAR_MISMATCH": "Case exists, but not in the cited year",
    "NOT_FOUND": "No such Supreme Court judgment found",
    "QUOTE_NOT_FOUND": "Quoted passage not in the judgment",
    "QUOTE_PARTIAL": "Quoted passage only partly matches",
    "UNVERIFIED": "Could not be verified",
    "OUT_OF_SCOPE": "Not checked (not a Supreme Court citation)",
}


@dataclass
class Hit:
    score: float
    title: str
    year: Optional[int]
    doc: Optional[Judgment] = None
    keys: list[str] = field(default_factory=list)
    votes: int = 0  # judgments citing it this way (Supreme Court and High Courts)
    hc_votes: int = 0  # of which High Court judgments
    source: str = "official"  # official | attested
    example: Optional[Judgment] = None  # a judgment that cites the case this way

    def describe(self) -> str:
        if self.doc is not None:
            bits = [self.doc.title.strip()]
            if self.doc.decision_date:
                bits.append(f"decided {self.doc.decision_date}")
            if self.doc.scr_citation:
                bits.append(self.doc.scr_citation)
            if self.doc.neutral_citation:
                bits.append(self.doc.neutral_citation)
            return ", ".join(bits)
        n = votes_text(self.votes, self.hc_votes)
        eg = ""
        if self.example is not None:
            ref = self.example.scr_citation or self.example.neutral_citation or ""
            eg = f", e.g. {self.example.title.strip()} {ref}".rstrip()
        return f"{self.title} ({', '.join(_pretty_key(k) for k in self.keys)}; cited this way in {n}{eg})"


@dataclass
class Finding:
    ref: Reference
    status: str
    risk: str
    message: str
    match: Optional[Hit] = None
    suggestions: list[Hit] = field(default_factory=list)
    quotes: list[QuoteResult] = field(default_factory=list)

    @property
    def headline(self) -> str:
        if self.status == "NOT_FOUND" and self.risk == "review":
            return "Not found in open records"
        if self.status == "YEAR_MISMATCH" and self.risk == "review":
            return "Similar case found in another year"
        return STATUS_TEXT.get(self.status, self.status)

    def as_dict(self) -> dict:
        m = self.match
        return {
            "reference": self.ref.label,
            "case_name": self.ref.case_name,
            "citations": [c.pretty() for c in self.ref.cites],
            "span": [self.ref.start, self.ref.end],
            "status": self.status,
            "headline": self.headline,
            "risk": self.risk,
            "message": self.message,
            "match": None if m is None else {
                "description": m.describe(),
                "score": round(m.score, 3),
                "source": m.source,
                **(m.doc.as_dict() if m.doc is not None else {}),
            },
            "suggestions": [h.describe() for h in self.suggestions],
            "quotes": [q.__dict__ for q in self.quotes],
        }


def votes_text(votes: int, hc: int = 0) -> str:
    sc = votes - hc
    if not hc:
        return f"{sc} Supreme Court judgment{'s' if sc != 1 else ''}"
    if not sc:
        return f"{hc} High Court judgment{'s' if hc != 1 else ''}"
    return f"{votes} judgments ({sc} Supreme Court, {hc} High Court)"


def _pretty_key(k: str) -> str:
    p = k.split(":")
    kind = p[0]
    if kind.startswith("SCC") and kind != "SCC_ONLINE":
        series = kind[3:]
        vol = p[2].replace("S", "Supp ")
        return f"({p[1]}) {vol} SCC{(' ' + series) if series else ''} {p[3]}"
    if kind == "SCR":
        vol = p[2]
        vol = ("Supp. " + vol[1:]) if vol.startswith("S") else vol
        return f"[{p[1]}] {vol} SCR {p[3]}"
    if kind == "SCC_ONLINE":
        return f"{p[1]} SCC OnLine {p[2]} {p[3]}"
    if kind == "AIR":
        return f"AIR {p[1]} {p[2]} {p[3]}"
    if kind == "INSC":
        return f"{p[1]} INSC {p[2]}"
    if kind in {"SCALE", "JT"}:
        return f"({p[1]}) {p[2]} {kind} {p[3]}"
    return k


def _window(c: Cite) -> range:
    """Decision years consistent with a citation's year.

    Neutral and online citations carry the decision year. Printed reporters carry
    the year of the volume, usually the decision year or the one after, and
    occasionally two years later.
    """
    if c.kind in {"INSC", "SCC_ONLINE", "LIVELAW", "MANU"}:
        return range(c.year, c.year + 1)
    return range(c.year - 2, c.year + 1)


# Reporters whose every Supreme Court judgment should appear in the official
# record or in later judgments' citations. SCC OnLine, JT, SCALE etc. also carry
# unreported orders, so a miss there is weaker evidence.
STRONG_REPORTERS = {"SCC", "SCR", "AIR"}
# A case reported in the last few years may not have been cited by a later judgment yet.
SETTLE_YEARS = 4

_GOVT_PARTY = re.compile(
    r"\b(?:state|union of india|uoi|government|govt|commissioner|cit|collector|municipal|corporation|"
    r"board|authority|bank of india|public prosecutor|central bureau)\b", re.IGNORECASE)


class Verifier:
    def __init__(self, corpus: Corpus, texts: Optional[TextSource] = None, check_quotes: bool = True):
        self.c = corpus
        self.texts = texts or TextSource()
        self.check_quotes = check_quotes

    # ------------------------------------------------------------------ lookup
    def _doc_hit(self, doc_id: int, score: float) -> Hit:
        d = self.c.docs[doc_id]
        return Hit(score=score, title=d.title, year=d.decision_year, doc=d, keys=list(self.c.keys_of.get(doc_id, [])))

    def find_case(self, pet: Optional[str], res: Optional[str]) -> list[Hit]:
        hits = [self._doc_hit(d, s) for d, s in self.c.names.search(pet, res, k=8)]
        for i, s in self.c.attest_names.search(pet, res, k=8):
            key, p, r, votes, _ = self.c.attest_row(i)
            hits.append(Hit(score=s, title=f"{p} v. {r}", year=key_year(key), keys=[key], votes=votes,
                            hc_votes=self.c.hc_votes.get((key, p, r), 0),
                            source="attested", example=self.c.citing_example(key, p, r)))
        hits.sort(key=lambda h: -h.score)
        return hits

    def claims(self, cites: list[Cite]) -> list[tuple[Cite, Hit, list[tuple[str, str]]]]:
        """What the record says each citation *is*: ``(cite, hit, names it is known by)``."""
        out = []
        for c in cites:
            doc = None
            if c.kind == "INSC":
                doc = self.c.by_nc.get((c.year, c.number))
            elif c.kind == "SCR" and c.page is not None:
                doc = self.c.by_scr(c.year, c.supp, c.volume, c.page)
            if doc is not None:
                d = self.c.docs[doc]
                out.append((c, self._doc_hit(doc, 1.0), [(d.petitioner or d.title, d.respondent)]))
            per_doc: dict[int, tuple[Hit, list]] = {}
            for pet, res, votes, doc_id in self.c.attestations(c.key):
                if doc_id is not None:
                    if doc_id not in per_doc:
                        h = self._doc_hit(doc_id, 1.0)
                        h.votes, h.source = 0, "attested"
                        d = self.c.docs[doc_id]
                        per_doc[doc_id] = (h, [(d.petitioner or d.title, d.respondent)])
                    h, names = per_doc[doc_id]
                    h.votes += votes
                    h.hc_votes += self.c.hc_votes.get((c.key, pet, res), 0)
                    names.append((pet, res))
                else:
                    h = Hit(score=1.0, title=f"{pet} v. {res}", year=c.year, keys=[c.key], votes=votes,
                            hc_votes=self.c.hc_votes.get((c.key, pet, res), 0),
                            source="attested", example=self.c.citing_example(c.key, pet, res))
                    out.append((c, h, [(pet, res)]))
            out.extend((c, h, names) for h, names in per_doc.values())
        return out

    # ------------------------------------------------------------------ verdicts
    def verify(self, ref: Reference) -> Finding:
        sc = [c for c in ref.cites if c.is_supreme_court]
        if ref.cites and not sc:
            return Finding(ref, "OUT_OF_SCOPE", "skip",
                           "High Court, tribunal or foreign citation; only Supreme Court authorities are checked so far.")
        today = date.today().year
        for c in sc:
            if c.year and c.year > today:
                return Finding(ref, "NOT_FOUND", "high", f"{c.pretty()} is dated in the future.")
            if c.year and c.year < 1950:
                return Finding(ref, "NOT_FOUND", "high",
                               f"{c.pretty()} is dated {c.year}, but the Supreme Court of India first sat on "
                               "28 January 1950.")
        named = bool(ref.petitioner)
        if not ref.cites and not named:
            return Finding(ref, "UNVERIFIED", "review", "Nothing to check.")

        claims = self.claims(sc)
        if claims:
            f = self._verify_against_claims(ref, sc, claims, named)
            if f is not None:
                return self._quotes(f)

        if named:
            return self._quotes(self._verify_by_name(ref, sc))
        return self._verify_bare(ref, sc)

    def _verify_against_claims(self, ref, sc, claims, named) -> Optional[Finding]:
        if not named:
            best = max(claims, key=lambda x: (x[1].source == "official", x[1].votes))
            return Finding(ref, "VERIFIED", "ok",
                           f"{best[0].pretty()} is {best[1].describe()}. (No case name was given to cross-check.)",
                           match=best[1])
        names = self.c.names
        scored = []
        for c, hit, known in claims:
            s = max(names.name_sim(ref.petitioner, ref.respondent, p, r) for p, r in known)
            one = max(names.best_party(ref.petitioner, ref.respondent, p, r) for p, r in known)
            scored.append((s, one, c, hit))
        scored.sort(key=lambda x: (-x[0], x[3].source != "official", -x[3].votes))
        s, one, c, hit = scored[0]
        hit.score = s
        if s >= T_MATCH:
            if hit.source == "official" or hit.doc is not None:
                src = "the official Supreme Court Reports" if hit.source == "official" else \
                    f"{votes_text(hit.votes, hit.hc_votes)} citing it the same way"
                return Finding(ref, "VERIFIED", "ok", f"{c.pretty()} matches {hit.describe()}, per {src}.", match=hit)
            return Finding(ref, "VERIFIED", "ok",
                           f"{c.pretty()} is how courts cite {hit.describe()}. The judgment itself is not in the "
                           "official reports corpus, so its text (and any quote) could not be checked.",
                           match=hit)
        best_one = max(x[1] for x in scored)
        if best_one < 0.5:
            # Neither party matches anything this citation is known to be.
            strong = [x for x in scored if x[3].source == "official" or x[3].votes >= 2]
            if not strong:
                return None  # a lone attestation is not enough to contradict; fall back to name search
            _, _, c2, hit2 = strong[0]
            inside = (c2.kind == "SCR" and hit2.source == "official" and hit2.doc is not None
                      and c2.page != hit2.doc.scr_start)
            located = [h for h in self.find_case(ref.petitioner, ref.respondent) if h.score >= T_MATCH][:2]
            where = f" A case named {ref.case_name} is on record as: {located[0].describe()}." if located else ""
            if inside:
                return Finding(ref, "UNVERIFIED", "review",
                               f"Page {c2.page} of that SCR volume falls inside {hit2.describe()}, a different case. "
                               "The open record may be missing the judgment that starts there, or this is another "
                               "reporter (Canada's SCR has the same abbreviation)." + where,
                               match=hit2, suggestions=located)
            return Finding(ref, "WRONG_CITATION", "high",
                           f"{c2.pretty()} is actually {hit2.describe()}, not {ref.case_name}.{where}",
                           match=hit2, suggestions=located)
        if s >= T_LOW or best_one >= 0.85:
            return Finding(ref, "UNVERIFIED", "review",
                           f"{c.pretty()} points to {hit.describe()}; the case name only partly matches. "
                           "It is probably the same case under a different title; check the parties.", match=hit)
        return Finding(ref, "UNVERIFIED", "review",
                       f"{c.pretty()} points to {hit.describe()}, whose parties only partly match {ref.case_name}.",
                       match=hit)

    def _verify_by_name(self, ref: Reference, sc: list[Cite]) -> Finding:
        hits = self.find_case(ref.petitioner, ref.respondent)
        strong = [h for h in hits if h.score >= T_MATCH]
        windows = [_window(c) for c in sc] or (
            [range(ref.year_hint - 1, ref.year_hint + 2)] if ref.year_hint else [])

        def in_window(h: Hit) -> bool:
            if not windows or h.year is None:
                return True
            slack = 1 if h.source == "attested" else 0
            return any(w.start - slack <= h.year < w.stop + slack for w in windows)

        good = [h for h in strong if in_window(h)]
        if good:
            h = good[0]
            given = {c.key for c in sc}
            kinds = {k.split(":")[0] for k in given}
            known_same_kind = [k for k in h.keys if k.split(":")[0] in kinds]
            if known_same_kind and not given & set(known_same_kind):
                direct_given = [c for c in sc if c.kind in {"INSC", "SCR"}]
                risk = "high" if h.votes >= 2 or h.source == "official" and direct_given else "review"
                return Finding(ref, "WRONG_CITATION", risk,
                               f"The case exists, but it is reported as {', '.join(_pretty_key(k) for k in known_same_kind)}, "
                               f"not {', '.join(c.pretty() for c in sc)}: {h.describe()}.",
                               match=h)
            direct_missing = [c for c in sc if c.kind in {"INSC", "SCR"}]
            if direct_missing and h.doc is not None:
                return Finding(ref, "WRONG_CITATION", "high",
                               f"The case exists as {h.describe()}, but {direct_missing[0].pretty()} does not point to it.",
                               match=h)
            if not sc:
                return Finding(ref, "CASE_FOUND", "ok", f"Matches {h.describe()}.", match=h)
            return Finding(ref, "CASE_FOUND", "ok",
                           f"Matches {h.describe()}. The {sc[0].kind.replace('_', ' ')} volume/page itself is not in any "
                           "open source, so only the case and year were confirmed.", match=h)
        if strong:
            h = strong[0]
            cited = ", ".join(sorted({str(c.year) for c in sc})) or str(ref.year_hint)
            # "Ram Kumar v. State of U.P." names many different cases; only a distinctive name pins one down.
            generic = bool(_GOVT_PARTY.search(ref.petitioner or "") or _GOVT_PARTY.search(ref.respondent or ""))
            risk = "high" if h.score >= 0.85 and not generic else "review"
            return Finding(ref, "YEAR_MISMATCH", risk,
                           f"The closest real case, {h.describe()}, is from {h.year}, not {cited}."
                           + ("" if risk == "high" else " The parties' names are common, so this may be a different "
                              "case that open sources do not record."),
                           match=h, suggestions=strong[1:3])
        near = [h for h in hits if h.score >= T_LOW][:3]
        if not sc:
            return Finding(ref, "UNVERIFIED", "review",
                           "Cited by name only, and no Supreme Court judgment with these parties was found. "
                           "It may be a High Court or foreign case; check it.", suggestions=near)
        lo, hi = self.c.year_range
        settled = (self.c.mined_through or hi or 0) - SETTLE_YEARS
        complete = [c for c in sc if c.kind in STRONG_REPORTERS and c.year <= settled]
        base = (f"No Supreme Court judgment with these parties was found, either in the official reports "
                f"({len(self.c):,} judgments, {lo}-{hi}) or among citations made by Supreme Court and High Court "
                f"judgments.")
        if complete:
            return Finding(ref, "NOT_FOUND", "high", base, suggestions=near)
        return Finding(ref, "NOT_FOUND", "review",
                       base + " This reporter or year is not fully covered by open sources, so check it by hand.",
                       suggestions=near)

    def _verify_bare(self, ref: Reference, sc: list[Cite]) -> Finding:
        for c in sc:
            if c.kind == "INSC":
                top = self.c.max_nc.get(c.year)
                settled = c.year <= (self.c.year_range[1] or 0) - 2
                if top and c.number > top + 50 and settled:
                    return Finding(ref, "NOT_FOUND", "high",
                                   f"{c.pretty()} does not exist: the highest neutral citation on record for {c.year} is {top}.")
                return Finding(ref, "UNVERIFIED", "review", f"{c.pretty()} is not in the open record.")
            if c.kind == "SCR" and c.page is not None:
                if self.c.scr_volume_known(c.year, c.supp, c.volume):
                    return Finding(ref, "NOT_FOUND", "high",
                                   f"No judgment in that SCR volume covers page {c.page}.")
        return Finding(ref, "UNVERIFIED", "review",
                       "No case name next to the citation, and the citation is not in the open record.")

    # ------------------------------------------------------------------ quotes
    def _quotes(self, f: Finding) -> Finding:
        if not f.ref.quotes:
            return f
        doc = f.match.doc if f.match is not None and f.status in {"VERIFIED", "CASE_FOUND"} else None
        if doc is None or not self.check_quotes:
            f.quotes = [QuoteResult(q.text, 0.0, "UNCHECKED") for q in f.ref.quotes]
            return f
        words = self.texts.words(doc)
        if words is None:
            f.quotes = [QuoteResult(q.text, 0.0, "UNCHECKED") for q in f.ref.quotes]
            return f
        f.quotes = [match_quote(q.text, "", words_cache=words) for q in f.ref.quotes]
        worst = min(f.quotes, key=lambda q: q.score)
        if worst.status == "NOT_FOUND":
            f.status, f.risk = "QUOTE_NOT_FOUND", "high"
            f.message = (f"The case is real ({f.match.describe()}), but the quoted passage does not appear in it "
                         f"(only {worst.score:.0%} of its phrasing is found).")
        elif worst.status == "PARTIAL" and f.risk == "ok":
            f.status, f.risk = "QUOTE_PARTIAL", "review"
            f.message = (f"The case is real ({f.match.describe()}), but the quoted passage only partly matches "
                         f"({worst.score:.0%} of its phrasing is found). It may be paraphrased or altered.")
        return f


def check_text(text: str, verifier: Verifier, uncited: bool = True) -> list[Finding]:
    return [verifier.verify(r) for r in extract(text, uncited=uncited)]
