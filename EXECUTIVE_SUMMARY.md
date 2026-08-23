# Executive Summary

## Objective
Identify fraudulent transaction patterns, quantify financial exposure, build an interpretable risk score, and evaluate whether behavioural features contain predictive signal.

## Dataset
- 275,000 transactions
- 10,000 customers
- 2,000 merchants
- Synthetic portfolio dataset

## Key results
- Total transaction value: **₹48.32 crore**
- Fraud transactions: **4,241**
- Fraud rate: **1.54%**
- Fraud value: **₹74.54 lakh**
- Median transaction value: **₹1,154.96**

## Significant behavioural factors
All four tested factors were statistically significant at p < 0.05:
- Location anomaly
- Night transaction
- Device anomaly
- High-risk merchant

Location anomaly produced the strongest chi-square statistic among the tested behavioural indicators.

## Risk score
The rule-based score combines behavioural and merchant signals into a 0–100 score. In the current validation:
- Score ≥25 captures about 15.5% of fraud with 4.7% precision.
- Score ≥50 is highly precise in the small high-risk group but captures very little fraud.
- Score ≥75 produced no alerts in this synthetic sample.

Therefore the score should be treated as a **prioritisation tool**, not a final automated fraud decision.

## ML benchmark
A chronological Logistic Regression benchmark achieved ROC-AUC ≈ **0.668**. At threshold 0.50:
- Precision ≈ 2.62%
- Recall ≈ 57.1%
- F1 ≈ 5.01%

The low precision reflects severe class imbalance and demonstrates why business thresholding matters more than accuracy alone.

## Recommended controls
- Low risk: normal approval
- Medium risk: passive monitoring / velocity checks
- High risk: step-up authentication
- Critical risk: manual review or temporary hold

## Portfolio conclusion
The project demonstrates a complete analytics workflow: data quality → SQL analysis → behavioural feature engineering → statistical validation → rule-based risk scoring → ML benchmark → Power BI communication.
