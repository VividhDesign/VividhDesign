# Paper idea: guaranteed false-alarm rates for pre-impact fall detection

**Working title:** *Distribution-free false-alarm control for pre-impact fall detection with wearable airbags*

**Why this, why you.** Your ISED 2026 paper trains a transformer on imbalanced IMU windows (KFall). A deployed airbag
system has two hard requirements that accuracy and F1 do not capture:
1. alarms must fire early enough for the airbag to inflate (≈130 ms before impact);
2. false alarms per hour of daily living must stay below a budget users will tolerate.

Today the alarm threshold is tuned on a validation split, and nothing guarantees the false-alarm rate on a new
person. **Conformal risk control** (Angelopoulos et al., 2022) and **Learn-then-Test** (Angelopoulos, Bates et al.,
2021) can pick the threshold so that the expected false-alarm rate on unseen subjects stays below λ with probability
1 − δ, without retraining the model. A quick search (Oct 2026) turned up pre-impact detection papers that report
specificity and lead time, but none with distribution-free guarantees. Please verify this more thoroughly before you write.

## Method (post-hoc, on top of your existing model)
- Score every sliding window with your trained transformer.
- **Split by subject** (exchangeability holds across people, not across overlapping windows): train / calibration / test.
- Per calibration subject, compute the false alarms per hour of ADL as a function of the threshold τ (monotone in τ).
- Choose τ\* with conformal risk control for **E[FA/hour] ≤ λ**, or with Learn-then-Test for a high-probability
  version. Report sensitivity at lead time ≥ 130 ms under τ\*.
- Extensions:
  - per-activity (Mondrian) calibration, since stairs and sitting down are the hard negatives;
  - KFall → SisFall transfer, where the guarantee may break under shift; quantify how much.

## Experiments (about 2–3 weeks)
1. Reproduce your ISED model's scores on KFall, using 5 subject-level folds.
2. Baseline: a threshold tuned on validation to hit a target FA/hour. Show that its realised FA/hour on test subjects
   overshoots the target for some people.
3. Conformal / LTT thresholds: show that realised FA/hour stays under λ across folds, and plot the cost in sensitivity and
   lead time against λ ∈ {0.5, 1, 2, 5} per hour.
4. Cross-dataset: calibrate on KFall and test on SisFall, then recalibrate with k SisFall subjects (k = 1, 2, 4).

## Venues
IEEE EMBC 2027 (full papers usually due in early spring), IEEE JBHI or *Sensors* (journal, rolling), or a NeurIPS/ICML
workshop on uncertainty or health.

## Why it helps your applications
It is a second first-author paper in your own line of work, with a clean statistical contribution that is easy to explain
in a pre-doc or MSR RF interview: "I made the false-alarm rate a guarantee rather than a hope."
