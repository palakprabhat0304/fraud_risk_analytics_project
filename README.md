# Fraud Detection & Financial Risk Analytics

## Business Problem
A fictional fintech company wants to reduce financial losses from fraudulent transactions while avoiding excessive false fraud alerts.

## Objective
Identify behavioural patterns associated with fraud, quantify financial exposure, build a transaction/customer risk score, and communicate findings through an executive Power BI dashboard.

## Dataset
Synthetic but behaviourally structured dataset created for portfolio use:
- 10,000 customers
- 2,000 merchants
- 275,000 transactions
- Fraud labels with multiple fraud types

## Tools
SQL, Python, Pandas, NumPy, SciPy, Scikit-learn, Power BI

## Planned workflow
1. Data quality checks
2. SQL exploration
3. Python EDA
4. Fraud pattern analysis
5. Statistical validation
6. Rule-based risk scoring
7. Optional ML benchmark
8. Power BI dashboard
9. Business recommendations

## Important
This is a synthetic portfolio project. It is designed to demonstrate analytical reasoning and technical skills, not to represent real customer or financial data.


## SQL Analysis — Completed

The `sql/` folder contains the full PostgreSQL analysis pipeline:
- schema + loading
- data quality checks
- fraud KPIs
- fraud pattern analysis
- window-function behavioural analysis
- advanced risk features
- 0–100 risk scoring
- customer-level risk aggregation
- business insight queries
- Power BI-ready views

Run the SQL files in the order listed in `sql/README_SQL_RUN_ORDER.md`.


## Python Analytics — Completed

The `python/` folder contains:
- EDA and behavioural feature engineering
- fraud segmentation analysis
- statistical significance testing
- rule-based risk-score validation
- Power BI export
- an optional Logistic Regression benchmark

Run the scripts using `python/README_PYTHON_RUN_ORDER.md`.
