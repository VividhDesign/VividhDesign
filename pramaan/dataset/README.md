---
license: cc-by-4.0
language:
- en
pretty_name: Open Concordance of Indian Supreme Court Citations
tags:
- legal
- india
- citations
- supreme-court
- hallucination-detection
size_categories:
- 10K<n<100K
---

# Open Concordance of Indian Supreme Court Citations

**47,770 links between proprietary law-report citations and the cases they refer to.** The citations
are SCC, AIR, SCC OnLine, SCALE, JT, MANU, ITR and others. The data is mined from how **13,044
Supreme Court** and **80,931 High Court** judgments cite earlier Supreme Court cases.

The main Indian reporters are proprietary, so until now there was no open table saying, for example,
that `(2018) 16 SCC 228` is *Canara Bank v. N.G. Subbaraya Setty*. This dataset builds that table
from the judgments themselves. 37,783 rows are linked to the official judgment record (SCR citation,
neutral citation, decision date).

Built for [Pramaan](https://github.com/VividhDesign/pramaan), an open-source checker for fabricated
case citations.

## File

`concordance.csv.gz` (UTF-8 CSV):

| Column | Meaning |
|---|---|
| `citation` | The citation as normally written, e.g. `(2018) 16 SCC 228` |
| `reporter` | `SCC`, `SCC(Cri)`, `SCC(Civ)`, `SCC(L&S)`, `SCR`, `AIR`, `SCC_ONLINE`, `SCALE`, `JT`, `INSC`, `MANU`, `ITR`, `LIVELAW`, `TAXMANN` |
| `year` | Year in the citation |
| `cited_as_petitioner`, `cited_as_respondent` | The case name as citing judgments write it |
| `citing_judgments` | Number of distinct judgments citing it this way |
| `citing_high_court_judgments` | Of which High Court judgments |
| `link_method` | How it was tied to the official record: `direct` (the citation is itself SCR/INSC), `parallel` (cited alongside an SCR citation), `name` (matched by parties and year), or empty (not linked) |
| `official_title`, `decision_date`, `official_scr`, `neutral_citation` | The official record, when linked |

## How it was built

1. Judgment texts were extracted from the open PDFs:
   * Supreme Court, 2010–2026;
   * High Courts of Delhi (2021–22), Bombay (Aurangabad and Goa benches, 2022), Calcutta (Original
     Side, 2022) and Karnataka (Dharwad and Kalaburagi benches, 2022).
2. A citation grammar extracted each cited case name with its Supreme Court citations. Parallel
   citations were grouped.
3. Mentions of the same citation were clustered by party-name similarity. Each cluster counts the
   distinct judgments citing it.
4. **Poisoning guard.** Judgments that discuss fabricated or AI-generated authorities were excluded:
   they quote the fakes. So were citations within 1,500 characters of such language.
5. Clusters were linked to the official record of 38,413 Supreme Court judgments.

## Quality and limits

* Rows with `citing_judgments >= 2`, or with a `direct` or `parallel` link, are the most reliable.
* Single-mention rows can carry errors from the citing text: OCR mistakes ("Kamataka"), typos in the
  citing judgment, or truncated names.
* Coverage follows citation frequency. Rarely cited cases are under-represented.
* This is not a complete index of any reporter, and it contains no text from proprietary reporters;
  only citation strings and case names as they appear in public judgments.

## Licence and attribution

CC-BY-4.0. Derived from *Indian Supreme Court Judgments* and *Indian High Court Judgments* (Dattam Labs,
Registry of Open Data on AWS), both CC-BY-4.0. Please cite:

> Yadav, V. (2026). *Open Concordance of Indian Supreme Court Citations* (v0.1). Part of Pramaan,
> https://github.com/VividhDesign/pramaan.

## Uploading (for the maintainer)

* **Hugging Face:** create a dataset repo `VividhDesign/indian-sc-citation-concordance`, then upload
  this folder (`huggingface-cli upload VividhDesign/indian-sc-citation-concordance dataset/ .
  --repo-type dataset`).
* **Zenodo (DOI):** link the GitHub repo in Zenodo. Each GitHub release then gets a DOI automatically.
