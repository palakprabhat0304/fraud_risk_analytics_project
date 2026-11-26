# Fraud Detection & Financial Risk Analytics

End-to-end fraud analytics on a synthetic fintech dataset (275,000 transactions · 10,000 customers · 2,000 merchants,
Jul 2025 – Jun 2026, amounts in INR): SQL → Python → statistics → interpretable risk scorecard → cost-based
operating policy → interactive dashboard.

> **Synthetic data.** Built to demonstrate analytical method, not to describe real customers or real fraud rates.

## Headline results

| | |
|---|---|
| Fraud rate / value | **1.54%** of transactions · **₹74.5 lakh** of ₹48.3 crore |
| Real signals | Location anomaly (3.5× fraud rate), device anomaly (2.7×), night 23:00–05:00 (2.2×), merchant risk score (1.5×) |
| Not signals (tested, rejected) | Transaction amount, payment method, account type/age, customer age/gender, weekday, city, transaction status |
| Scorecard on held-out final 20% (19 Apr–30 Jun 2026) | ROC-AUC **0.669** (95% CI 0.648–0.686). Paired bootstrap: better than the old rule score by +0.027 AUC (CI +0.018 to +0.037); vs gradient boosting only +0.007 AUC (CI +0.003 to +0.012) and **no reliable PR-AUC difference**, so the two are treated as equivalent |
| Top 5% of transactions by score | capture **17.8%** of fraud (3.6× lift) |
| Critical tier (1% of volume) | **7.2%** fraud rate vs 1.5% base (4.8× lift) |
| Operating policy (₹40/review, 85% prevention) | **estimated** net benefit ₹96k over the 73-day test window vs ₹54k for the old rules (assumption-based, not realised savings) |

The ceiling is low and that is a finding, not a failure: gradient boosting with extra features (hour, amount, tenure, age)
does **no better** than the 4-feature logistic scorecard (AUC 0.662), so the usable signal in this dataset is
exhausted by those four behaviours. See `EXECUTIVE_SUMMARY.md`.

## What changed in v2 (review findings)

1. **Dead rules removed.** `payment_anomaly` is always 0 (every transaction uses the customer's preferred method) and
   `amount_anomaly` shows 1.54% vs 1.54% fraud; `rapid_transaction` fires on 73 rows and was 0/12 in the test window.
   They contributed weight to the old score without adding information.
2. **Hand-picked weights → fitted scorecard.** Logistic regression on a chronological 80% train split, converted to 0–100 points
   (`python/05_scorecard_and_cost_analysis.py`, `sql/10_scorecard.sql`).
3. **Empty tiers fixed.** The old *Critical* tier had 0 transactions and *High* 17. Tiers are now train-set quantiles
   (80th/95th/99th pct) and stay ordered out-of-time.
4. **Thresholds tied to money.** Net benefit = 85% × fraud value caught − review cost × alerts, threshold picked on train,
   reported on test, with a sensitivity table on review cost.
5. **Extended evaluation (`06_extended_evaluation.py`)**: precision-recall curve, Precision/Recall@1/5/10%, FP/FN at equal alert volume, paired-bootstrap model differences, calibration, worked score examples, monthly AUC/precision/recall, PSI drift checks, operational cost of false alerts.
6. **Uncertainty reported** (bootstrap CIs) and **out-of-time stability** of each signal checked.
7. **Repo hygiene.** Duplicate/colliding SQL files moved to `sql/_superseded/`, fragile rolling-window code removed
   from script 02, hard-coded relative paths fixed, `requirements.txt`, `.gitignore`, `python/run_all.py` added.

## Dashboard

`dashboard/index.html` is a single self-contained file (no installs, no internet needed): open it in any browser. Four pages: Executive Overview,
Fraud Behaviour, Risk Monitoring (label-free: alert queue by tier, score distribution, high-risk table with reason codes) and Model Evaluation & Impact
(tier lift, interactive threshold and review-cost sliders, cost of false alerts, model comparison, monthly stability, recommended controls). Rebuild it with `python python/07_build_dashboard.py`.

## Repository layout

```
data/                 customers, merchants, transactions, fraud_labels, data_dictionary
sql/                  00-09 PostgreSQL pipeline, 10_scorecard.sql (new), _superseded/
python/
  02_eda_and_statistics.py          EDA, chi-square / Mann-Whitney, legacy rule score
  03_ml_benchmark.py                class-weighted logistic regression benchmark
  04_create_business_report_tables.py
  05_scorecard_and_cost_analysis.py scorecard, model comparison, cost curve  <- new
  06_extended_evaluation.py         PR curve, calibration, explainability, monthly stability  <- new
  07_build_dashboard.py             builds dashboard/index.html  <- new
  run_all.py                        runs everything in order
outputs/              original tables + figures
outputs/v2/           scorecard outputs, cost curve, sensitivity, scored transactions
outputs/figures/      v2_*.png charts
dashboard/index.html   interactive 4-page dashboard (open in any browser)
```

## Run it

```bash
pip install -r requirements.txt
python python/run_all.py
```

SQL: follow `sql/README_SQL_RUN_ORDER.md` (PostgreSQL), then `10_scorecard.sql`.

## Method notes & limitations

- **No leakage:** features are available at decision time; split is chronological (train → 2026-04-19, test after).
- **Labels are treated as known.** In production, labels arrive late (chargebacks), so the live model would train on delayed labels.
- **Review cost and prevention rate are assumptions** (top of `05_...py`). At ₹100/review the scorecard has *negative* net
  benefit: with average fraud ≈ ₹1,760 and ~4% alert precision, only cheap friction (step-up/OTP) pays for itself.
- **Fraud types are indistinguishable** on available features (night/location/device mix and median amount are
  near-identical across types), so type-specific rules are not supportable from this data.
- **Calibration:** probabilities are only roughly calibrated and barely better than predicting the base rate (Brier 0.01466 vs 0.01478).
  Use the score for *ranking*, not as a literal fraud probability.
- **False alerts have a cost:** at the operating point ~96% of alerts (4,857 of 5,067) are legitimate; ≈23 false alerts per fraud caught,
  ≈69 alerts/day, 9% of legitimate transactions challenged, and 615 frauds (₹10.7 lakh) still missed in the test window.
- **Stability:** April 2026 straddles the train/test cut (19 Apr 00:50), so it is reported as two rows: April-train (13,497 transactions) and
  April-test (9,105). Out-of-sample months score ROC-AUC 0.656 (Apr), 0.666 (May), 0.677 (Jun), in line with the in-sample range
  (0.645-0.704), with no downward trend. The split-April points have fewer transactions and are noisier. PSI for the score and every feature
  is about 0, but this synthetic data has no drift by construction, so real data would need ongoing monitoring.
- **How to read the model comparison.** ROC-AUC scores the *whole* ranking, which is mostly legitimate traffic; PR-AUC and top-5% capture score the
  *high-risk end*, where alerts are raised. The scorecard's ROC-AUC edge over gradient boosting is small but consistent (+0.007, CI +0.003 to +0.012).
  Its PR-AUC edge (+0.0025, CI -0.0005 to +0.0059) cannot be told apart from zero, and its top-5% capture gap (17.8% vs 17.0%) is under one point
  (about 7 of 825 frauds). Where alerts are actually raised the two models behave the same; the scorecard is chosen for transparency, not accuracy.
- **Operational vs evaluation views.** The dashboard's Risk Monitoring page shows only scores, tiers and reason codes (no fraud label), as a live
  queue would. Outcome labels appear only on the Fraud Behaviour (historical) and Model Evaluation & Impact pages.
- **Merchant concentration is mostly noise:** only 1 of 2,000 merchants survives a Bonferroni-corrected binomial test.
