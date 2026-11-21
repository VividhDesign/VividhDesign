"""Party-name normalisation and fuzzy matching for Indian case titles.

Case names are cited loosely: "UOI" for "Union of India", "CIT" for
"Commissioner of Income Tax", "Keshavananda" for "Kesavananda", "& Anr." left
out. This module reduces names to comparable token sets and scores how well a
cited name matches a judgment's recorded parties, weighting rare tokens (party
names) above common ones ("State", "India", "Ltd").
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import Iterable, Optional

ABBREVIATIONS = {
    "UOI": "UNION OF INDIA",
    "CIT": "COMMISSIONER OF INCOME TAX",
    "PCIT": "PRINCIPAL COMMISSIONER OF INCOME TAX",
    "DCIT": "DEPUTY COMMISSIONER OF INCOME TAX",
    "ACIT": "ASSISTANT COMMISSIONER OF INCOME TAX",
    "ITO": "INCOME TAX OFFICER",
    "CCE": "COMMISSIONER OF CENTRAL EXCISE",
    "SBI": "STATE BANK OF INDIA",
    "RBI": "RESERVE BANK OF INDIA",
    "LIC": "LIFE INSURANCE CORPORATION OF INDIA",
    "SEBI": "SECURITIES AND EXCHANGE BOARD OF INDIA",
    "CBI": "CENTRAL BUREAU OF INVESTIGATION",
    "NHAI": "NATIONAL HIGHWAYS AUTHORITY OF INDIA",
    "DDA": "DELHI DEVELOPMENT AUTHORITY",
    "MCD": "MUNICIPAL CORPORATION OF DELHI",
    "ONGC": "OIL AND NATURAL GAS CORPORATION",
    "BSNL": "BHARAT SANCHAR NIGAM",
    "NCT": "NATIONAL CAPITAL TERRITORY",
    "GNCTD": "GOVERNMENT OF NATIONAL CAPITAL TERRITORY OF DELHI",
    "UP": "UTTAR PRADESH",
    "MP": "MADHYA PRADESH",
    "AP": "ANDHRA PRADESH",
    "HP": "HIMACHAL PRADESH",
    "JK": "JAMMU AND KASHMIR",
    "TN": "TAMIL NADU",
    "WB": "WEST BENGAL",
    "GOVT": "GOVERNMENT",
    "LTD": "LIMITED",
    "PVT": "PRIVATE",
    "CO": "COMPANY",
    "CORPN": "CORPORATION",
    "CORP": "CORPORATION",
    "MAHA": "MAHARASHTRA",
    "SEB": "STATE ELECTRICITY BOARD",
    "KSEB": "KERALA STATE ELECTRICITY BOARD",
    "MSEB": "MAHARASHTRA STATE ELECTRICITY BOARD",
    "PSEB": "PUNJAB STATE ELECTRICITY BOARD",
    "TNEB": "TAMIL NADU ELECTRICITY BOARD",
    "UPSEB": "UTTAR PRADESH STATE ELECTRICITY BOARD",
    "RSEB": "RAJASTHAN STATE ELECTRICITY BOARD",
    "SRTC": "STATE ROAD TRANSPORT CORPORATION",
    "KSRTC": "KARNATAKA STATE ROAD TRANSPORT CORPORATION",
    "APSRTC": "ANDHRA PRADESH STATE ROAD TRANSPORT CORPORATION",
    "MSRTC": "MAHARASHTRA STATE ROAD TRANSPORT CORPORATION",
    "UPSRTC": "UTTAR PRADESH STATE ROAD TRANSPORT CORPORATION",
    "DTC": "DELHI TRANSPORT CORPORATION",
    "BHEL": "BHARAT HEAVY ELECTRICALS",
    "SAIL": "STEEL AUTHORITY OF INDIA",
    "NTPC": "NATIONAL THERMAL POWER CORPORATION",
    "IOC": "INDIAN OIL CORPORATION",
    "IOCL": "INDIAN OIL CORPORATION",
    "HPCL": "HINDUSTAN PETROLEUM CORPORATION",
    "BPCL": "BHARAT PETROLEUM CORPORATION",
    "GAIL": "GAIL",
    "UPSC": "UNION PUBLIC SERVICE COMMISSION",
    "PSC": "PUBLIC SERVICE COMMISSION",
    "UGC": "UNIVERSITY GRANTS COMMISSION",
    "CCI": "COMPETITION COMMISSION OF INDIA",
    "TRAI": "TELECOM REGULATORY AUTHORITY OF INDIA",
    "IRDA": "INSURANCE REGULATORY AND DEVELOPMENT AUTHORITY",
    "IRDAI": "INSURANCE REGULATORY AND DEVELOPMENT AUTHORITY",
    "ED": "DIRECTORATE OF ENFORCEMENT",
    "NIA": "NATIONAL INVESTIGATION AGENCY",
    "NCB": "NARCOTICS CONTROL BUREAU",
    "DRI": "DIRECTORATE OF REVENUE INTELLIGENCE",
    "CBDT": "CENTRAL BOARD OF DIRECT TAXES",
    "CCE": "COMMISSIONER OF CENTRAL EXCISE",
    "CST": "COMMISSIONER OF SALES TAX",
    "COMMR": "COMMISSIONER",
    "COMMNR": "COMMISSIONER",
    "COMMISSR": "COMMISSIONER",
    "ADDL": "ADDITIONAL",
    "ASSTT": "ASSISTANT",
    "ASST": "ASSISTANT",
    "DY": "DEPUTY",
    "JT": "JOINT",
    "SPL": "SPECIAL",
    "SECY": "SECRETARY",
    "DIST": "DISTRICT",
    "DISTT": "DISTRICT",
    "DEPTT": "DEPARTMENT",
    "DEPT": "DEPARTMENT",
    "ADMN": "ADMINISTRATION",
    "ASSN": "ASSOCIATION",
    "ASSOCN": "ASSOCIATION",
    "SOC": "SOCIETY",
    "COOP": "COOPERATIVE",
    "BROS": "BROTHERS",
    "ENGG": "ENGINEERING",
    "MFG": "MANUFACTURING",
    "INTL": "INTERNATIONAL",
    "NATL": "NATIONAL",
    "UNIV": "UNIVERSITY",
    "INSTT": "INSTITUTE",
    "ELECTY": "ELECTRICITY",
    "BD": "BOARD",
    "MGMT": "MANAGEMENT",
    "INDS": "INDUSTRIES",
    "MUNI": "MUNICIPAL",
}

STOPWORDS = {
    "THE", "AND", "OF", "M", "S", "MS", "MESSRS", "ORS", "ANR", "OTHERS", "ANOTHER", "ETC", "THR",
    "THROUGH", "LRS", "LR", "DEAD", "D", "BY", "ITS", "VS", "V", "VERSUS", "SMT", "SHRI", "SRI", "SH",
    "DR", "MR", "MRS", "KUMARI", "KM", "ALIAS", "IN", "RE", "FOR", "AN", "A", "ON", "TO", "AT", "ETC",
    "SINCE", "DECEASED", "HIS", "HER", "HOLINESS", "NOW", "FORMERLY", "KNOWN", "AS", "WITH", "OR",
}


def _skeleton(tok: str) -> str:
    """Collapse common romanisation variants of Indian names to one form."""
    t = tok
    t = t.replace("KSH", "X").replace("PH", "F")
    t = re.sub(r"([BCDGJKPST])H", r"\1", t)
    t = t.replace("EE", "I").replace("OO", "U").replace("W", "V").replace("Z", "J").replace("Q", "K")
    t = re.sub(r"Y$", "I", t)
    t = t.replace("RN", "M")  # OCR reads "rn" as "m" ("Kamataka")
    t = re.sub(r"(.)\1+", r"\1", t)
    return t


def tokens(name: Optional[str]) -> list[str]:
    """Normalised, skeletonised tokens of a party name (stopwords removed)."""
    if not name:
        return []
    s = re.sub(r"(?<=[a-zA-Z])/(?=[a-z])", "l", name)  # OCR: "Kera/a" -> "Kerala"
    s = s.replace("_", "")
    s = re.sub(r"\([^()]*\)", " ", s)  # parentheticals: "(Dead)", "(Prakash Singh-2)", "(P)"
    s = s.upper().replace("&", " AND ").replace("@", " ALIAS ")
    s = re.sub(r"\bM/S\.?", " ", s)
    s = re.sub(r"\bU\.?\s?O\.?\s?I\.?\b", " UOI ", s)
    s = re.sub(r"\bJ\s?&\s?K\b|\bJ\s?AND\s?K\b", " JK ", s)
    s = re.sub(r"\bCO-OP(?:ERATIVE)?\b", " COOP ", s)
    # Join dotted initialisms ("S.B.I." -> SBI) before stripping punctuation.
    s = re.sub(r"\b(?:[A-Z]\.\s?){2,}", lambda m: m.group(0).replace(".", "").replace(" ", "") + " ", s)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    out: list[str] = []
    for t in s.split():
        exp = ABBREVIATIONS.get(t)
        parts = exp.split() if exp else [t]
        for p in parts:
            # Drop initials ("N. G." / "NG"): too ambiguous to help, and cited inconsistently.
            if p in STOPWORDS or len(p) <= 2 or p.isdigit():
                continue
            out.append(_skeleton(p))
    return out


class NameIndex:
    """Inverted index over the parties of every judgment in the corpus."""

    def __init__(self) -> None:
        self.parties: dict[int, tuple[list[str], list[str]]] = {}
        self.post: dict[str, set[int]] = defaultdict(set)
        self.prefix: dict[str, set[int]] = defaultdict(set)
        self.df: Counter = Counter()
        self.n = 0
        self._idf: dict[str, float] = {}
        self._pair_cache: dict[tuple[str, str], bool] = {}
        self._by3: dict[str, set[str]] = defaultdict(set)

    def add(self, doc_id: int, petitioner: str, respondent: str) -> None:
        p, r = tokens(petitioner), tokens(respondent)
        self.parties[doc_id] = (p, r)
        self.n += 1
        for t in set(p) | set(r):
            self.post[t].add(doc_id)
            self.df[t] += 1
            self._by3[t[:3]].add(t)
            if len(t) >= 6:
                self.prefix[t[:6]].add(doc_id)
        self._idf.clear()

    def idf(self, tok: str) -> float:
        v = self._idf.get(tok)
        if v is None:
            v = self._idf[tok] = math.log(1 + self.n / (1 + self.df.get(tok, 0)))
        return v

    def _pair_match(self, q: str, c: str) -> bool:
        if q == c:
            return True
        k = (q, c)
        hit = self._pair_cache.get(k)
        if hit is None:
            short, long_ = (q, c) if len(q) <= len(c) else (c, q)
            if len(q) >= 6 and len(c) >= 6 and q[:6] == c[:6]:
                hit = True
            elif len(short) >= 3 and len(long_) - len(short) <= 2 and long_.startswith(short):
                hit = True  # "Bhal"/"Bhalla", "Ram"/"Rama"
            elif len(short) >= 5 and q[0] == c[0] and len(long_) - len(short) <= 2:
                hit = SequenceMatcher(None, q, c).ratio() >= 0.8
            else:
                hit = False
            if len(self._pair_cache) > 2_000_000:
                self._pair_cache.clear()
            self._pair_cache[k] = hit
        return hit

    def _tok_match(self, q: str, cands: Iterable[str]) -> bool:
        return any(self._pair_match(q, c) for c in cands)

    def _containment(self, q: list[str], c: list[str]) -> float:
        if not q:
            return 0.0
        total = sum(self.idf(t) for t in q)
        hit = sum(self.idf(t) for t in q if self._tok_match(t, c))
        return hit / total if total else 0.0

    @staticmethod
    def _acronym(a: list[str], b: list[str]) -> bool:
        """"CSIR" against "Council of Scientific and Industrial Research"."""
        return len(a) == 1 and 3 <= len(a[0]) <= 6 and len(b) >= 3 and "".join(t[0] for t in b) == a[0]

    def party_sim(self, q: list[str], c: list[str]) -> float:
        if not q or not c:
            return 0.0
        if self._acronym(q, c) or self._acronym(c, q):
            return 1.0
        return 0.85 * self._containment(q, c) + 0.15 * self._containment(c, q)

    def score(self, pet: Optional[str], res: Optional[str], doc_id: int) -> float:
        qp, qr = tokens(pet), tokens(res)
        cp, cr = self.parties[doc_id]
        if not qr:  # "In re ..." or a single-party title: compare against both sides.
            return self._containment(qp, cp + cr)
        return self.score_tokens(qp, qr, cp, cr)

    def score_tokens(self, qp: list[str], qr: list[str], cp: list[str], cr: list[str]) -> float:
        """Both parties must match: the mean of the two party scores, pulled toward the weaker one."""
        if not qr or not cr:
            return self._containment(qp + qr, cp + cr)

        def pair(a: float, b: float) -> float:
            return (a + b) / 4 + min(a, b) / 2

        straight = pair(self.party_sim(qp, cp), self.party_sim(qr, cr))
        swapped = 0.95 * pair(self.party_sim(qp, cr), self.party_sim(qr, cp))
        return max(straight, swapped)

    def name_sim(self, pet1, res1, pet2, res2) -> float:
        """Symmetric similarity of two cited case names (either may be abbreviated or truncated)."""
        a, b, c, d = tokens(pet1), tokens(res1), tokens(pet2), tokens(res2)
        return max(self.score_tokens(a, b, c, d), self.score_tokens(c, d, a, b))

    def best_party(self, pet1, res1, pet2, res2) -> float:
        """How well the better-matching single party agrees (used to tell 'other case' from 'same case, other respondent')."""
        a, b, c, d = tokens(pet1), tokens(res1), tokens(pet2), tokens(res2)
        sims = [self.party_sim(a, c), self.party_sim(c, a), self.party_sim(b, d), self.party_sim(d, b),
                self.party_sim(a, d), self.party_sim(b, c)]
        return max(sims) if sims else 0.0

    def candidates(self, pet: Optional[str], res: Optional[str], limit: int = 150) -> list[int]:
        """Cheap first pass: documents sharing rare tokens, ranked by shared IDF mass."""
        toks = sorted(set(tokens(pet)) | set(tokens(res)), key=self.idf, reverse=True)
        mass: dict[int, float] = defaultdict(float)
        for t in toks[:6]:
            hits = set(self.post.get(t, ()))
            if len(t) >= 6:
                hits |= self.prefix.get(t[:6], set())
            if not hits:
                for k in self._by3.get(t[:3], ()):
                    if abs(len(k) - len(t)) <= 2 and self._pair_match(t, k):
                        hits |= self.post.get(k, set())
            if len(hits) > 6000:  # too common to discriminate on its own
                continue
            w = self.idf(t)
            for d in hits:
                mass[d] += w
        ranked = sorted(mass, key=lambda d: -mass[d])
        return ranked[:limit]

    def search(self, pet: Optional[str], res: Optional[str], k: int = 5) -> list[tuple[int, float]]:
        scored = [(d, self.score(pet, res, d)) for d in self.candidates(pet, res)]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]
