"""Measure how well Pramaan separates genuine citations from fabricated ones.

Held-out design. The attestation index used here is mined only from judgments
up to 2022 (``--db``). Genuine references are taken from judgments of
2023-2026, which the index has never read. Fabrications are generated from
those genuine references, following the taxonomy in Pooja Ramesh Singh v. J&K
Bank (2026 INSC 668):

  fake_case     invented case: the petitioner of one real case joined to the
                respondent of another, with a plausible citation
  wrong_cite    a real case name with the citation of a different real case
  wrong_year    a real case name and citation with the year shifted 3-10 years
  fake_quote    a real case and citation with a passage taken from a
                different judgment
  real_quote    control: a real case with a passage from its own text

Usage:
  python eval/evaluate.py --db sc_eval.sqlite --texts corpus/text --n 600
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pramaan.citations import Cite, Reference, extract  # noqa: E402
from pramaan.corpus import Corpus  # noqa: E402
from pramaan.mine import clean_judgment_text, iter_text_dir  # noqa: E402
from pramaan.quotes import TextSource  # noqa: E402
from pramaan.verify import Verifier, _pretty_key  # noqa: E402

GENERIC = {"state", "union", "india", "of", "the", "and", "ors", "anr", "others", "another", "commissioner",
           "income", "tax", "government", "municipal", "corporation", "bank", "ltd", "limited", "pvt", "co"}


def distinctive(party: str) -> bool:
    words = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", party)]
    return any(w not in GENERIC for w in words)


def cite_text(c: Cite) -> str:
    return _pretty_key(c.key)


def shift_year(c: Cite, delta: int) -> str:
    return cite_text(Cite(kind=c.kind, raw="", start=0, end=0, year=c.year + delta, volume=c.volume, supp=c.supp,
                          page=c.page, number=c.number, court=c.court, series=c.series))


def collect_genuine(texts: Path, years: range, limit_docs: int, rng: random.Random) -> list[Reference]:
    docs = list(iter_text_dir(texts, years))
    rng.shuffle(docs)
    refs = []
    for _, raw in docs[:limit_docs]:
        for r in extract(clean_judgment_text(raw), uncited=False):
            sc = [c for c in r.cites if c.is_supreme_court and c.kind in {"SCC", "SCR", "AIR", "SCC_ONLINE", "INSC"}]
            if r.petitioner and r.respondent and sc and distinctive(r.petitioner) and distinctive(r.respondent):
                refs.append(r)
    return refs


def passage(words: list[str], rng: random.Random, n: int = 28) -> str:
    start = rng.randrange(max(1, len(words) - n))
    return " ".join(words[start:start + n])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="index whose attestations were mined from judgments <= 2022")
    ap.add_argument("--texts", required=True, help="directory of judgment texts (year subfolders)")
    ap.add_argument("--n", type=int, default=600, help="cases per category")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=None, help="write JSON results here")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    corpus = Corpus(Path(args.db))
    texts = Path(args.texts)
    verifier = Verifier(corpus, TextSource(text_dir=texts, allow_network=False))

    pool = collect_genuine(texts, range(2023, 2027), 2500, rng)
    seen, genuine = set(), []
    for r in pool:  # one test case per distinct authority
        k = (r.case_name.lower(), r.cites[0].key)
        if k not in seen:
            seen.add(k)
            genuine.append(r)
    rng.shuffle(genuine)
    print(f"{len(genuine)} distinct genuine references from 2023-2026 judgments", file=sys.stderr)

    cases: list[tuple[str, str]] = []  # (category, text)
    sample = genuine[: args.n]
    for r in sample:
        cases.append(("genuine", f"{r.case_name}, {', '.join(cite_text(c) for c in r.cites)}."))

    by_kind = defaultdict(list)
    for r in genuine:
        by_kind[r.cites[0].kind].append(r)
    for r in genuine[: args.n]:
        other = rng.choice(genuine)
        if other is r:
            continue
        c = r.cites[0]
        bogus = Cite(kind=c.kind, raw="", start=0, end=0, year=c.year, volume=c.volume, supp=c.supp,
                     page=(c.page or 0) + rng.randint(3, 400) if c.page else None,
                     number=(c.number or 0) + rng.randint(3, 400) if c.number else None, court=c.court, series=c.series)
        cases.append(("fake_case", f"{r.petitioner} v. {other.respondent}, {cite_text(bogus)}."))
    for r in genuine[: args.n]:
        kind = r.cites[0].kind
        donor = rng.choice(by_kind[kind])
        if donor.cites[0].key == r.cites[0].key or donor.case_name == r.case_name:
            continue
        cases.append(("wrong_cite", f"{r.case_name}, {cite_text(donor.cites[0])}."))
    for r in genuine[: args.n]:
        delta = rng.choice([-1, 1]) * rng.randint(3, 10)
        if r.cites[0].year + delta > 2026:
            delta = -abs(delta)
        cases.append(("wrong_year", f"{r.case_name}, {shift_year(r.cites[0], delta)}."))

    # Quote tests use judgments whose text we hold, cited by SCR.
    with_text = [j for j in corpus.docs.values()
                 if j.scr_year and j.petitioner and j.respondent and verifier.texts._local(j) is not None]
    rng.shuffle(with_text)
    for j in with_text[: args.n]:
        own = verifier.texts.words(j)
        donor = rng.choice(with_text)
        if donor.id == j.id or not own or len(own) < 200:
            continue
        name = f"{j.petitioner.title()} v. {j.respondent.title()}, {j.scr_citation}"
        cases.append(("real_quote", f'In {name}, the Court held: "{passage(own[150:], rng)}"'))
        cases.append(("fake_quote", f'In {name}, the Court held: "{passage(verifier.texts.words(donor)[150:], rng)}"'))

    results = defaultdict(Counter)
    statuses = defaultdict(Counter)
    examples = defaultdict(list)
    for cat, text in cases:
        refs = [r for r in extract(text, uncited=False) if r.cites]
        if not refs:
            results[cat]["not_extracted"] += 1
            continue
        f = verifier.verify(refs[0])
        results[cat][f.risk] += 1
        statuses[cat][f.status] += 1
        if len(examples[cat]) < 4 and ((cat in {"genuine", "real_quote"}) == (f.risk == "high")):
            examples[cat].append({"text": text[:300], "status": f.status, "message": f.message[:300]})

    report = {}
    print(f"\n{'category':<12} {'n':>5} {'flagged high':>13} {'review':>8} {'passed':>8}")
    for cat in ["genuine", "fake_case", "wrong_cite", "wrong_year", "real_quote", "fake_quote"]:
        r = results[cat]
        n = sum(r.values())
        if not n:
            continue
        row = {k: r[k] for k in ("high", "review", "ok", "skip", "not_extracted")}
        row["n"] = n
        row["statuses"] = dict(statuses[cat])
        report[cat] = row
        print(f"{cat:<12} {n:>5} {r['high'] / n:>12.1%} {r['review'] / n:>8.1%} {r['ok'] / n:>8.1%}")
    report["errors"] = examples
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
