# PYTHON ANALYTICS RUN ORDER

Run from the `python/` folder.

## 1. `02_eda_and_statistics.py`

This is the main analyst notebook/script.

It:
- loads all source tables
- validates joins
- engineers behavioural features
- calculates KPIs
- analyzes fraud by time/category/device/payment/city
- compares fraud vs legitimate behaviour
- performs Mann-Whitney and chi-square tests
- validates the rule-based risk score
- generates charts
- exports `powerbi_transaction_risk.csv`

## 2. `03_ml_benchmark.py`

This is an optional advanced section.

It:
- uses a chronological train/test split
- handles class imbalance with `class_weight='balanced'`
- trains interpretable Logistic Regression
- reports precision, recall, F1 and ROC-AUC at several thresholds
- exports a confusion matrix

Do not present this as the main purpose of the project. The project is primarily Data Analytics + Risk Analytics.

## 3. `04_create_business_report_tables.py`

Run after script 02 to prepare concise report tables.

## Expected outputs

The `outputs/` folder will contain:
- core KPIs
- fraud breakdowns
- statistical tests
- behavioural effect sizes
- risk-score validation
- Power BI-ready transaction-level table
- charts
- ML benchmark metrics
