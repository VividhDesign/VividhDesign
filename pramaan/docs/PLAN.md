# Pramaan: why this, and how it becomes valuable

## The problem, in the Supreme Court's words

* **Pooja Ramesh Singh v. J&K Bank, 2026 INSC 668 (2 July 2026).** The NCLT admitted an insolvency
  petition on the strength of six "precedents". Four did not exist. In the other two, a real citation
  carried an invented paragraph. The NCLAT did not notice. The Supreme Court set both orders aside and
  declared **zero tolerance**. It held that citing unverified AI-generated precedents is *misconduct*
  by an advocate, and that a decision resting on even "an iota" of such material is "no decision in the
  eyes of the law". It directed the Bar Council of India to frame norms and disciplinary consequences.
  It also asked the question this tool answers: *"Imagine the hardship of a situation in which the Court
  must verify the authenticity of each judgment cited by an advocate."*
* **Gummadi Usha Rani v. Sure Mallikarjuna Rao (2026).** A trial court relied on AI-generated fake
  judgments. The Supreme Court called it misconduct and issued notice to the Attorney General and the BCI.
* **Buckeye Trust v. PCIT (ITAT Bengaluru, Dec 2024).** A ₹669 crore tax order was recalled within a
  week because it cited non-existent judgments.
* Delhi HC (2025), the Bombay HC and others have flagged petitions built on untraceable citations.

Every advocate in India is now personally exposed: one unverified citation can mean a misconduct
finding. Every tribunal and trial court risks having its orders set aside.

## Who already sells this, and the gap

* **Manupatra Citation Verifier**: a browser extension tied to a Manupatra subscription.
* **Grayscope Verify** and similar startups: closed source, paid.
* **SCC Online / Manupatra / Westlaw India**: research databases at roughly ₹15,000 to ₹1,00,000+ a
  year per seat. A district-court lawyer, a legal-aid clinic or a litigant-in-person usually has none.

**What does not exist (as far as I could find): an open-source, auditable verifier for Indian
citations.** Pramaan is that. It also includes the first open grammar for Indian reporter citations
(an "eyecite for India") and an **open citation concordance**: for each of ~43,000 SCC / AIR / SCC
OnLine citations, which case it belongs to. The concordance is mined from the Supreme Court's own
judgments, so it needs no proprietary database.

Being open matters more here than usual. A court registry or the BCI cannot mandate a closed vendor's
black box, but it can adopt, audit and run an open checker.

## Who pays, and for what (open core)

The code stays free and open. That earns trust, adoption by courts and attention from the press.
Money comes from what institutions pay for around open code:

| Customer | What they pay for | Rough price point |
|---|---|---|
| Law firms and chambers | Hosted checker, Word add-in, bulk PDF checks, audit trail ("verified on <date>") | ₹500–2,000 / user / month; firm plans |
| Legal-tech and AI drafting startups | Verification API run on every draft their LLM produces (this is their biggest liability) | per-call or ₹50k+/month |
| Courts, tribunals, e-filing (eCourts, NCLT, ITAT) | Pre-filing check in the e-filing portal, on-premise deployment, support SLA | government contract |
| Insurers of professional liability | Risk scoring of filings | B2B |
| Law schools and legal aid | Free (impact, word of mouth, future customers) | 0 |

The data moat grows with use. Every High Court judgment added (the open High Court dataset holds
millions) and every new Supreme Court judgment makes the concordance bigger. That is hard for a
closed competitor to match without paying for proprietary reporters.

## Next 90 days

1. **Week 1–2: make it public and credible.**
   * Move `pramaan/` into its own repository (`git subtree split --prefix pramaan`), add CI, and
     publish to PyPI.
   * Host the web interface (a free-tier VM is enough; the index is ~25 MB).
   * Write one post: "I ran an open-source checker on the citations the Supreme Court found fake
     in Pooja Ramesh Singh". Include the table from the README.
   * Send it to LiveLaw, Bar & Bench, SCC Online Blog and the Internet Freedom Foundation. Legal
     journalists are covering this story right now.
2. **Week 3–6: coverage.**
   * Add High Court judgments (open dataset on AWS) and statute checks, e.g. "Section 420 IPC" cited
     for an offence after 1 July 2024, when BNS replaced the IPC.
   * Add Hindi judgment text.
3. **Week 6–12: first revenue.**
   * Ship the Word add-in.
   * Offer the API to 3–5 Indian legal-AI startups. They have the strongest incentive to call it
     on every output.
   * Pilot with one law firm and one legal-aid clinic.
   * Write to the BCI committee the Supreme Court directed to be formed (para 9 of 2026 INSC 668)
     and offer the tool as a reference implementation.

## Why you specifically

This is retrieval and evaluation, the same skills as Strata and Evident: an index, fuzzy entity
resolution, a held-out evaluation, and honesty about failure modes. It is a portfolio piece that
reads as "built infrastructure the Supreme Court asked for". For AI-evaluation roles in particular,
"I measured hallucination detection on a held-out set and found my own tool's poisoning bug" is
exactly the story interviewers want to hear.
