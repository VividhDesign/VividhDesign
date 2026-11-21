# Launch kit

Everything here is ready to copy. Steps marked **(you)** need your accounts; everything else is
already in this folder.

## Day 1: put it online (about 15 minutes)

Shortest path: open
[this prefilled link](https://github.com/new?name=pramaan&visibility=public&description=Catch+fake+case+citations+in+Indian+legal+documents.+Free%2C+open-source%2C+private.)
and click **Create repository**. Then run `bash pramaan/scripts/publish.sh` from your profile repo
(branch `claude/wonderful-euler-sq9rg0`). It pushes the project with its history, tags v0.1.0, and
prints the remaining clicks. The detailed steps follow.

1. **(you) Create the repository.** On GitHub, create an empty public repository `VividhDesign/pramaan`
   (no README, no licence; this folder has both).
2. **(you) Push this folder as its own repository, history included.** From a clone of your profile
   repo, on branch `claude/wonderful-euler-sq9rg0`:

   ```bash
   git subtree split --prefix pramaan -b pramaan-standalone
   git push https://github.com/VividhDesign/pramaan.git pramaan-standalone:main
   ```

3. **(you) Turn on the free website.** In the new repo: Settings → Pages → Source: **GitHub Actions**.
   The `Deploy site` workflow then publishes **https://vividhdesign.github.io/pramaan/** and refreshes
   the judgment index every Monday. It is the in-browser version: documents never leave the user's
   computer, and hosting costs nothing.
4. **(you) PyPI, one time.** On pypi.org → Account → Publishing → add a pending publisher:
   project `pramaan`, owner `VividhDesign`, repo `pramaan`, workflow `release.yml`, environment `pypi`.
   Then:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

   After that, `pip install pramaan` works for everyone.
5. **(you) Repo polish.**
   * Add a description: "Catch fake case citations in Indian legal documents. Free, open-source, private."
   * Add topics: `legal-tech india hallucination citations supreme-court nlp`.
   * Add the website link.
6. **(you) Merge the branch** so your profile README lists Pramaan first.

## Week 1: get it seen

Post in this order, a day apart, so each post can point to the previous one's traction.

### LinkedIn (main post)

> On 2 July the Supreme Court set aside an NCLT order because it relied on judgments that don't exist:
> four invented cases and two real ones with invented paragraphs (Pooja Ramesh Singh v. J&K Bank,
> 2026 INSC 668). The Court called citing unverified AI precedents *misconduct*, and asked: "Imagine the
> hardship of a situation in which the Court must verify the authenticity of each judgment cited."
>
> So I built a tool that does that verification, and made it free and open-source.
>
> Pramaan checks every case cited in a petition or order against the open record of 38,000+ Supreme
> Court judgments, and against 45,000+ citations that Supreme Court and High Court judges have used. It flags invented
> cases, citations that belong to a different case, wrong years, and quotes that don't appear in the
> judgment.
>
> On the NCLT's six citations, it flags the four invented cases and the wrong citation, verifies the
> real one, and catches the invented paragraph attributed to it. On a held-out test of 1,000 genuine
> citations it raises a false alarm on 1.2%, and lets only 0.1–2.3% of fabricated ones through unflagged.
>
> It runs in your browser: your document is never uploaded.
> Try it: https://vividhdesign.github.io/pramaan/
> Code: https://github.com/VividhDesign/pramaan
>
> I'd love feedback from advocates, judges and law students, especially citations it gets wrong.

Attach a screenshot of the NCLT example result (open the site → "Try the NCLT example").

### X / Twitter thread

1. The Supreme Court just set aside an NCLT order built on AI-invented precedents. I built a free,
   open-source checker that would have caught them. 🧵
2. What it checks: whether the case exists, whether the citation belongs to it, the year, and whether the
   quoted paragraph is really in the judgment.
3. How, without SCC or Manupatra: it mines how Supreme Court judgments cite earlier cases. That gives an
   open map of 45k+ SCC/AIR citations, from 94k Supreme Court and High Court judgments.
4. The bug I'm proudest of finding: the SC judgment *condemning* the fakes lists them, and my first
   version learned them as real. Now judgments about fake citations are never used as evidence.
5. Runs in your browser, nothing uploaded. Link + code ↓

### Hacker News (Show HN)

Title: `Show HN: Pramaan – catch AI-fabricated case citations in Indian court filings`

Lead with the engineering: the open concordance mined from judgments, the poisoning bug, and the
held-out evaluation numbers.

### Reddit

r/LegalAdviceIndia (where allowed), r/developersIndia, r/india (weekend tech thread). Keep it short and
link the site.

## Week 1–2: press and institutions

Addresses and a tracker are in [OUTREACH.md](OUTREACH.md). Treat the drafts below as notes and write
the final versions in your own words: LiveLaw rejects AI-written submissions, and a personal note gets
more replies anyway.

### To legal journalists (LiveLaw, Bar & Bench, SCC Online Blog, The Leaflet, MediaNama)

> **Subject:** Free open-source tool that catches AI-fabricated citations (tested on the NCLT case in 2026 INSC 668)
>
> Hello,
>
> After *Pooja Ramesh Singh v. J&K Bank* (2026 INSC 668), I built Pramaan, a free, open-source tool that
> checks every citation in a filing against the open record of Supreme Court judgments.
>
> On the six authorities the NCLT relied on, it flags all four non-existent cases and the citation
> attached to the wrong case, verifies the genuine one, and catches the invented paragraph attributed to
> it. It runs in the browser, so documents are never uploaded. On a held-out test it wrongly flags 1.2%
> of genuine citations; the limitations are documented openly.
>
> Demo: https://vividhdesign.github.io/pramaan/
> Code and method: https://github.com/VividhDesign/pramaan
>
> I'm a final-year B.Tech (AI/ML) student at BIT Mesra and happy to demo it or answer questions.
>
> Vividh Yadav

### To the dataset maintainers (Dattam Labs / the `indian-supreme-court-judgments` project)

Their open data made this possible, and they are likely to share it with their community (DataMeet,
their Discord). Thank them, link the repo and show the attribution. Offer the mined concordance back as
a dataset.

### To the Bar Council of India committee (para 9 of 2026 INSC 668) and the Supreme Court e-Committee

> **Subject:** Open-source citation verification tool, offered free for the Bar and the courts
>
> Respected Sir/Madam,
>
> In 2026 INSC 668 the Supreme Court directed the Bar Council of India to frame norms on fake,
> AI-generated precedents. I have built an open-source tool, Pramaan, that checks citations in a
> petition against the open record of Supreme Court judgments. It flags non-existent cases, citations
> belonging to a different case, and quotations not found in the cited judgment.
>
> It is free, its method and measured error rates are public, and it can run inside a court's own
> systems or entirely in a web browser, so no document leaves the user's machine. I would be glad to
> demonstrate it, or adapt it as a pre-filing check.
>
> Demo: https://vividhdesign.github.io/pramaan/ · Code: https://github.com/VividhDesign/pramaan
>
> Yours faithfully,
> Vividh Yadav, BIT Mesra

Also send it to:
* NCLT, ITAT and NCLAT registrars (the tribunals that were embarrassed);
* state judicial academies, which run AI-awareness training for judges;
* the National Judicial Academy, Bhopal.

### To law school legal-aid clinics and moot court societies (NLSIU, NALSAR, NLU Delhi, etc.)

Offer a free 45-minute session: "How AI fabricates citations, and how to catch it". This gets you users,
testimonials and bug reports.

## Month 1–2: academic credibility

* **arXiv preprint now.** It timestamps the work as first. The draft is in `docs/paper/`.
* **ICAIL 2027.** Papers and demos are due around **28 January 2027** (Vienna, July 2027; check the
  official site for exact dates). Submit the paper, or a demo paper if time is short.
* **Publish the concordance as a dataset** (Hugging Face and Zenodo for a DOI). Datasets get cited for
  years.
* **Later targets:**
  * NLLP workshop (with EMNLP); calls usually come out mid-year;
  * JURIX 2027;
  * PyCon India 2027 (talk proposal).

## Money: who pays and what to charge

Stay free and open for individuals, courts, legal aid and students. Charge institutions for what
surrounds the code:

| Offer | Buyer | Price to start with | Notes |
|---|---|---|---|
| **Verification API** | Legal-AI and drafting startups | ₹25,000–1,00,000 / month, or ₹5–10 per document | The Docker image is ready: `PRAMAAN_API_KEYS=…`. Every AI drafting tool needs this check, and building it themselves costs more. |
| **Hosted plan for chambers and firms** | Law firms, chambers | ₹999 / user / month; firm plan ₹25k+/month | Bulk PDF checks, audit trail ("verified on <date>"), Word add-in (next build). |
| **Training workshops** | Judicial academies, bar associations, law firms, NLUs | ₹15,000–50,000 per session | Fastest money; also builds the reputation. |
| **On-premise deployment and support** | Tribunals, courts, e-filing vendors | Contract | Government procurement is slow; start with a free pilot. |
| **Custom coverage** (a High Court, tax tribunals, statutes) | Firms in tax or IBC practice | Project fee | ITAT and NCLT matters are where the fakes have hurt. |

**First 5 paying customers, concretely:**
1. List 20 Indian legal-AI and contract-AI startups, plus Indian teams of global ones.
2. Email the founder or CTO: "Your users' filings can now be checked for fabricated citations before
   they reach a court. 2026 INSC 668 makes that check a professional obligation. Here is an API; first
   month free."
3. Offer one law firm a 30-day free pilot on the hosted plan in exchange for a testimonial.
4. Pitch one judicial academy a workshop.

**Before charging anyone:**
* Add a simple terms-of-service and a disclaimer ("evidence to check, not legal advice").
* For the hosted API, follow India's DPDP Act: don't keep documents. The server already stores only
  counts, not text.
* Register as a sole proprietor or LLP once invoices start.

**The most reliable money in the next six months is a job or internship this project wins you:**
* legal-AI companies hiring ML or evaluation engineers (Indian legal-tech startups, and global firms
  such as Harvey or Thomson Reuters);
* AI-evaluation teams, because "measured hallucination detection with a held-out set" is exactly
  their work.

Put the demo link and the numbers (1.2% false alarms; 97.7–99.9% of fabrications flagged) at the top of your CV.
