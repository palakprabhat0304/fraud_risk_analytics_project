# Executive Summary

## Question
Where does fraud concentrate, how much money is at risk, and can a transparent score reduce losses without drowning
operations in false alerts?

## Exposure
- 275,000 transactions, ₹48.32 crore total value
- **4,241 fraud transactions (1.54%) worth ₹74.54 lakh** (avg ≈ ₹1,760 per fraud)
- Fraud is spread across 5 types (Payment 33%, Account Takeover 24%, Card Testing 18%, Suspicious Transfer 13%, Identity 11%)
- Monthly fraud rate is stable (1.4–1.7%), so no seasonal or trending issue to chase

## What drives fraud (and what does not)
| Signal | Fraud rate if present | If absent | Ratio |
|---|---|---|---|
| Location anomaly | 4.75% | 1.36% | 3.5× |
| Device anomaly | 4.08% | 1.49% | 2.7× |
| Night (23:00–05:00) | 2.64% | 1.18% | 2.2× |
| High-risk merchant (score ≥ 0.35) | 2.30% | 1.49% | 1.5× |

Signals stack: location + night + device ≈ 15% fraud (71 transactions), location + night ≈ 7.7%.
Amount, payment method, account tenure, demographics, weekday and city show no meaningful relationship.
Jewellery (2.7%) and Gaming (2.2%) are the riskiest categories, driven largely by merchant risk.

## Scorecard
A four-feature logistic scorecard (odds ratios: location 3.6×, device 2.9×, night 2.3×, +1 SD merchant risk 1.26×)
trained on Jul 2025–Apr 2026 and tested on Apr–Jun 2026:

| Tier | % of volume | Fraud rate (test) | Lift |
|---|---|---|---|
| Low | 80% | 1.08% | 0.7× |
| Medium | 15% | 2.44% | 1.6× |
| High | 4% | 4.78% | 3.2× |
| Critical | 1% | 7.22% | 4.8× |

- ROC-AUC 0.669 (95% CI 0.648–0.686). Paired bootstrap shows it beats the original rule score (+0.027, CI +0.018 to +0.037). Against gradient boosting the ROC-AUC gap is tiny but consistent (+0.007, CI +0.003 to +0.012), while the PR-AUC gap (+0.0025, CI -0.0005 to +0.0059) and the top-5% capture gap (17.8% vs 17.0%, about 7 frauds) cannot be separated from zero. ROC-AUC judges the whole ranking, which is mostly legitimate traffic; PR-AUC and top-5% capture judge the high-risk end where alerts are raised. So the two models behave the same where it matters, and the scorecard is chosen for transparency, not accuracy.
- Probabilities are poorly calibrated for absolute use (Brier barely beats the base rate): use the score to rank, not as a literal probability.
- Top 5% by score captures 17.8% of fraud.
- A more flexible model (gradient boosting, extra features) does not improve on it, so the limit is in the data, not the method.

## Money
At ₹40 per review/step-up and 85% of flagged fraud value prevented, the best threshold (score ≥ 36, chosen on training data)
flags 9% of transactions and has an **estimated** net benefit of ≈ ₹96k over the 73-day test window (old rules: ₹54k). This is an assumption-based estimate, not realised savings.
At ₹100 per review the policy loses money, so friction must be cheap.

**Cost of false alerts at this threshold:** 5,067 alerts (≈69/day), of which 4,857 (96%) are legitimate, i.e. ≈23 false alerts for each fraud caught; 9% of legitimate
customers would be challenged, and 615 frauds worth ₹10.7 lakh are still missed. This is why High should get low-friction step-up, and only Critical goes to manual review.

**Stability:** monthly AUC 0.645–0.704; the out-of-sample months (late April, May, June) score 0.656–0.677, in line with training months. April is split at the 19 Apr train/test cut and reported as two rows. PSI ≈ 0 for all inputs (synthetic data has no drift by construction).

## Recommended controls
- **Low (80%)** approve
- **Medium (15%)** approve, passive monitoring
- **High (4%)** low-friction step-up (OTP / biometric)
- **Critical (1%)** step-up plus manual review or hold when amount is above a value threshold

## Caveats
Synthetic data; assumptions on review cost and prevention rate drive the money numbers; precision remains low (≈4% at the
operating point), so this is a prioritisation layer, not an auto-decline engine.
