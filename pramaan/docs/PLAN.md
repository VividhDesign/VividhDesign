# Pramaan: prestige and money

Ready-to-send posts, emails and setup steps are in [LAUNCH.md](LAUNCH.md). This page covers why the
project matters and what to expect.

## Why it matters

* **Pooja Ramesh Singh v. J&K Bank, 2026 INSC 668 (2 July 2026).** The NCLT relied on six
  "precedents": four did not exist, and two real citations carried invented paragraphs. The Supreme
  Court set aside both the NCLT and NCLAT orders. It declared **zero tolerance** and held that citing
  unverified AI-generated precedents is advocate **misconduct**. It directed the Bar Council of India to
  frame norms, and it said: *"Imagine the hardship of a situation in which the Court must verify the
  authenticity of each judgment cited by an advocate."*
* **Gummadi Usha Rani (2026).** A trial court relied on fake AI judgments; the Supreme Court called it
  misconduct.
* **Buckeye Trust (ITAT Bengaluru).** A ₹669 crore order was recalled over non-existent citations.

Every advocate in India now carries personal risk for every citation. Every tribunal risks its orders
being set aside.

## What is genuinely new here (be precise when you claim "first")

The products that exist (Manupatra's Citation Verifier, Grayscope Verify) are closed and paid, and
their error rates are not public. As far as I could find, Pramaan is the first:

1. **open-source verifier** for Indian case citations, with published, held-out error rates;
2. **open citation concordance** for SCC, AIR and SCC OnLine citations, mined from what judges
   themselves cite, so no proprietary database is needed;
3. checker of its kind that **runs entirely in the browser**, so client documents never leave the
   lawyer's computer;
4. documented analysis of **attestation poisoning**: judgments that condemn fake citations also quote
   them.

Say "first open-source…", not "first ever". The closed tools came earlier, and saying so makes you more
credible, not less.

## How you get prestige (in order of payoff per hour)

1. **Public demo plus one strong post.** The Supreme Court's own question is your headline. Legal media
   (LiveLaw, Bar & Bench, SCC Online Blog) are actively covering this story, and a working, free,
   open tool tested on the actual NCLT citations is newsworthy.
2. **arXiv preprint, then ICAIL 2027.** ICAIL is the main international AI-and-law conference; papers
   and demos are due around 28 January 2027. A demo paper there is realistic and strong for both
   master's applications and AI-evaluation jobs. The draft is in `paper/`.
3. **Institutional use.** Offer it free to:
   * the Bar Council committee the Court ordered;
   * NCLT, ITAT and NCLAT registries;
   * judicial academies;
   * NLU legal-aid clinics.

   One email back saying "we are trying it" is worth more than a thousand stars.
4. **A citeable dataset.** Publish the concordance on Hugging Face and Zenodo (DOI). Researchers
   building Indian legal NLP will cite it for years.
5. **Talks.** PyCon India, DataMeet (the community behind the open judgment data), and law schools.

## How you make money (realistic order)

1. **A job or internship (months 0–6, most likely).** Legal-AI companies and AI-evaluation teams hire
   for exactly this. "Built and measured a hallucination detector for Indian legal citations; held-out
   false-alarm rate 1.2%; caught the fakes the Supreme Court found" is a top-of-CV line.
2. **Workshops (fastest cash).** "How AI fabricates citations, and how to catch it" for judicial
   academies, bar associations, firms and NLUs: ₹15k–50k a session.
3. **Verification API (main recurring revenue).** Every Indian legal-AI drafting tool needs to check
   its own output before a user files it. Charge ₹25k–1L a month, or ₹5–10 a document. The Docker
   image with API keys and usage logs is ready.
4. **Firm plan.** Hosted checker, bulk checks, audit trail and a Word add-in: ₹999 per user per
   month, or firm-wide pricing.
5. **Government and court work.** Pre-filing checks in e-filing systems and on-premise deployments.
   It is slow to procure; start with free pilots.

**What not to do:**
* Don't paywall the core. Open code is why courts can trust it, and why it gets coverage.
* Don't store user documents. That keeps you clear of most privacy-law (DPDP Act) obligations; the
  server already logs only counts.

## Honest expectations

* The tool is strong at what it claims, and its weak spots are documented in the README.
* Coverage is Supreme Court citations only. Each High Court added widens the market.
* Revenue takes customer conversations, not just code. The first paying customer usually takes 1–3
  months of outreach.
* Prestige compounds fastest if you launch in the next two weeks, while the story is current.
