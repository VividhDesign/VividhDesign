# Pramaan (प्रमाण): catch fake case citations before they reach a court

Pramaan reads a petition, written submission or order and checks every case it cites against the
**open record of the Supreme Court of India**. It flags:

* **invented cases**: no Supreme Court judgment with those parties exists;
* **citations that belong to a different case**: a real `(2020) 16 SCC 728` attached to the wrong name;
* **real cases cited with the wrong year**;
* **real cases with invented quotes**: the quoted passage does not appear anywhere in the judgment.

It is free and open-source, and it needs no SCC Online or Manupatra subscription. Two ways to use it:

* **In the browser**: the [web version](https://vividhdesign.github.io/pramaan/) runs entirely on
  your machine, so your document is never uploaded.
* **On the command line**, offline once the index is built:

```bash
pip install -e ".[sync,pdf]"      # from this folder (not on PyPI yet)
pramaan sync                      # ~2 min: downloads open Supreme Court metadata, builds the index
pramaan check petition.pdf        # also .docx, .txt, or - for stdin; exits 1 if anything is high-risk
pramaan serve                     # web interface at http://127.0.0.1:8000
```

## Why now

On 2 July 2026, in **Pooja Ramesh Singh v. Jammu and Kashmir Bank Ltd. (2026 INSC 668)**, the Supreme
Court set aside an NCLT order and the NCLAT order affirming it. The NCLT had relied on six
"precedents": four did not exist, and two real citations carried invented paragraphs. The Court:

* declared **zero tolerance** for AI-generated precedents cited without verification;
* held that citing them is **misconduct** by an advocate;
* held that a decision touched by "an iota" of such material is **no decision in the eyes of the law**;
* directed the Bar Council of India to frame norms and disciplinary consequences.

It also asked: *"Imagine the hardship of a situation in which the Court must verify the authenticity
of each judgment cited by an advocate."*

This is not an isolated case:

* a trial court relied on AI-generated fake judgments (*Gummadi Usha Rani*, 2026);
* a ₹669 crore ITAT order was recalled over non-existent citations (*Buckeye Trust*, 2024–25);
* High Courts have flagged untraceable citations in petitions.

## What it says about the NCLT's six citations

[`examples/nclt_submission.txt`](examples/nclt_submission.txt) reproduces the NCLT's authorities word
for word, as quoted in the Supreme Court's judgment. The table compares the Supreme Court's own findings
(para 15) with what Pramaan reports:

| Citation used by the NCLT | Supreme Court's finding | Pramaan |
|---|---|---|
| State Bank of India v. Shree Ram Urban Infrastructure, 2020 SCC OnLine SC 341 | Wrong citation (it is *M. Subramaniam v. S. Janaki*) | **Review**: no such case in open records |
| Everest Kento Cylinders v. Union of India, (2015) 2 SCC 1 | Correct citation, invented paragraph | **High**: no such case in open records ⚠️ |
| ICICI Bank v. Urban Infrastructure Real Estate, (2019) 16 SCC 528 | Non-existent | **High**: no such Supreme Court judgment |
| V.S. Dempo & Co. v. Reliance Communications, (2021) 10 SCC 176 | Non-existent | **High**: no such Supreme Court judgment |
| Canara Bank v. N.G. Subbaraya Setty, (2018) 16 SCC 228 | Correct citation, invented paragraph | **Verified** citation; an invented paragraph attributed to it is flagged **High** (quote not in judgment) |
| Sarbjit Singh v. Union Bank of India, (2022) 7 SCC 464 | Non-existent | **High**: no such Supreme Court judgment |

All six are verified correctly or flagged. One verdict is wrong in its reason: Everest Kento is
reported as "not found", but the Court says the citation itself is real (only its paragraph was
invented). The case is simply absent from open records. The full report is in
[`examples/nclt_submission.report.txt`](examples/nclt_submission.report.txt) and
[`.html`](examples/nclt_submission.report.html).

## Measured accuracy (held-out)

[`eval/evaluate.py`](eval/evaluate.py) builds the citation concordance **only from judgments up to
2022** (Supreme Court judgments, plus High Court judgments of 2021–22). It then tests on citations made in **2023–2026 judgments**, which the index never read. The
fabrications follow the Supreme Court's own taxonomy in 2026 INSC 668:

| Test set (1,000 each) | Flagged high | Flagged for review | Missed |
|---|---|---|---|
| Genuine citations from 2023–26 judgments | **1.2%** (false alarms) | 6.5% | n/a (92.3% verified) |
| Invented case (parties spliced from two real cases) | 47.9% | 50.8% | **1.3%** |
| Real case, citation of another real case | 84.5% | 13.9% | **1.6%** |
| Real case, year shifted 3–10 years | 34.6% | 63.1% | **2.3%** |
| Real case, passage from a different judgment | 99.0% | 0.9% | **0.1%** |
| Real case, genuine passage | 0.0% (false alarms) | 0.9% | n/a (99.1% verified) |

"Missed" includes references the parser failed to extract. Raw counts are in
[`eval/results.json`](eval/results.json).

**How to read this:**

* **High** means the open record positively contradicts the citation.
* **Review** means the record could not confirm it. Typical reasons: the year is too recent for later
  judgments to have cited it, the reporter also carries unreported orders (SCC OnLine), or the parties
  have common names ("Ram Kumar v. State of U.P."). Review is deliberately not "fake".
* Of the 12 genuine citations flagged high, a manual audit found:
  * 8 are real judgments absent from open sources (SCC reports some cases the official SCR does not);
  * 3 are text-extraction noise in the source judgment;
  * 1 has a year in the citing text that disagrees with the official record (a typo or OCR error at
    the source).

## How it works

1. **A grammar for Indian citations** ([`citations.py`](src/pramaan/citations.py)). It covers SCC
   (including Supp, Cri, L&S), SCR, AIR, SCC OnLine, INSC and High Court neutral citations, SCALE, JT,
   Cri LJ, MANU, ITR, Taxmann and LiveLaw. It groups parallel citations, recovers the case name from
   free text ("In *X v. Y*, (2017) 10 SCC 1 : AIR 2017 SC 4161, at para 12"), and attaches pinpoints
   and quotations.
2. **The official record** ([`corpus.py`](src/pramaan/corpus.py)): all 38,413 judgments in the Supreme
   Court Reports, 1950–2026, with SCR page ranges and neutral citations. Source: the open *Indian
   Supreme Court Judgments* dataset (CC-BY-4.0).
3. **An open citation concordance** ([`mine.py`](src/pramaan/mine.py)). SCC, AIR and SCC OnLine are
   proprietary, so there is no public table saying what `(2018) 16 SCC 228` is. But judgments cite
   earlier cases by name *and* reporter, and SCR headnotes list parallel citations
   (`(2020) 2 SCC 677 : [2019] 16 SCR 252`). Mining 13,044 Supreme Court judgments (2010–2026) and
   80,931 High Court judgments yields **47,770 attestations for 45,551 citations**. 37,783 of them are
   tied to an official judgment, many through their SCR parallel. The concordance ships with the
   package.
   * **Poisoning guard.** A judgment that *discusses* fake citations quotes them, and an early version
     of this tool "verified" the NCLT's fakes from 2026 INSC 668 itself. Judgments about fabricated or
     AI-generated authorities are therefore never used as evidence. See
     [`tests/test_mine.py`](tests/test_mine.py).
4. **Party-name matching built for Indian titles** ([`names.py`](src/pramaan/names.py)). It handles:
   * abbreviations such as UOI, CIT, SEB and "Govt. of NCT";
   * romanisation variants such as Keshavananda/Kesavananda and Bharti/Bharati;
   * OCR damage such as "Kamataka" and "Kera/a";
   * acronyms such as CSIR for Council of Scientific and Industrial Research.

   Rare tokens get IDF weighting.
5. **Quote verification** ([`quotes.py`](src/pramaan/quotes.py)). Each quoted passage is compared on
   word n-grams against the judgment's text (fetched on demand from the open PDF and cached), so
   layout, hyphenation and page headers don't matter but invented sentences do.

## Limits

* **Supreme Court only.** High Court, tribunal and foreign citations are reported as *not checked*.
* "Not found" means not found in **open** sources. Non-reportable judgments missing from the SCR, and
  very recent ones, can be real; that is why most such findings are *review*, not *high*.
* Quotes are checked only for judgments in the SCR corpus, against the SCR text.
* A finding is evidence to check, not a ruling. Read the judgment before you rely on it, or before you
  accuse anyone of relying on a fake.

## Hosting it

* **Private web version (free).** `python web/build_site.py --db <index> --out site` builds a static
  site that runs the checker in the browser with Pyodide: a ~7 MB download, and the document stays on
  the user's machine. `.github/workflows/pages.yml` deploys it to GitHub Pages and refreshes the index
  weekly.
* **Server and paid API.** `docker build -t pramaan .`, then run it with
  `-e PRAMAAN_API_KEYS="clientA:5000,clientB:500"` (keys with daily limits). `POST /api/check` takes
  `{"text": ...}` or a base64 PDF/DOCX. Anonymous use is limited per IP, and usage can be logged for
  billing (`PRAMAAN_USAGE_LOG`); documents themselves are never stored. See
  [`server.py`](src/pramaan/server.py).

## Roadmap

* Checking High Court citations, not only Supreme Court ones (the open High Court dataset holds 17.8
  million judgments).
* Mining more High Courts into the concordance.
* Statute checks: an IPC section cited for an offence after the BNS took effect.
* Hindi judgment text.
* A Word add-in.

## Development

```bash
pip install -e ".[dev]"
pytest                                    # 72 tests, no network
pramaan mine sc_texts --hc-dir hc_texts --workers 4   # rebuild the concordance from judgment texts
python eval/evaluate.py --db eval.sqlite --texts path/to/texts --n 1000
```

Code: MIT. Data: *Indian Supreme Court Judgments*, Dattam Labs / AWS Open Data Registry,
CC-BY-4.0 (https://registry.opendata.aws/indian-supreme-court-judgments/). The bundled concordance is
derived from it and carries the same attribution.
