# SQL PACKAGE — RUN ORDER

Use PostgreSQL.

## Run in this order

1. `00_schema_and_load.sql`
   - Creates the four base tables and indexes.
   - Uncomment/edit the COPY commands to load the CSV files.

2. `01_data_quality.sql`
   - Validate row counts, duplicates, nulls, invalid values, and referential integrity.

3. `02_fraud_kpis.sql`
   - Build the executive-level fraud KPIs and monthly trend.

4. `03_fraud_patterns.sql`
   - Investigate fraud by merchant, payment method, device, time, amount, and city.

5. `04_window_functions.sql`
   - Demonstrate LAG, RANK, ROW_NUMBER, NTILE, running counts, and behavioural changes.

6. `05_advanced_risk_features.sql`
   - Creates `v_transaction_risk_features`.
   - This is the core feature-engineering layer.

7. `06_risk_scoring.sql`
   - Converts risk features into a 0–100 rule-based score and Low/Medium/High/Critical categories.

8. `07_customer_risk.sql`
   - Creates customer-level risk and exposure analysis.

9. `08_business_insights.sql`
   - Produces analysis that can become the project's final business recommendations.

10. `09_powerbi_export.sql`
   - Creates clean Power BI-ready views.

## What this package demonstrates

- SELECT / WHERE / GROUP BY / HAVING
- CASE WHEN
- JOINs
- CTEs
- Window functions
- LAG / RANK / ROW_NUMBER / NTILE
- Time-window analysis
- Percentiles
- Fraud-rate and financial-loss calculations
- Behavioural feature engineering
- Rule-based risk scoring
- Customer-level aggregation
- Power BI data preparation

## Important analytical note

The risk score is a portfolio demonstration, not a production fraud model. In the next stage we should test its precision/recall and compare it with a simple Logistic Regression / Random Forest benchmark.
