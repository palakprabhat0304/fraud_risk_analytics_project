# Power BI Dashboard Setup

## 1. Import data
Open Power BI Desktop → **Get Data → Text/CSV** and import:

`outputs/powerbi_transaction_risk.csv`

This single transaction-level table is intentionally sufficient for the first dashboard version. No relationships are required.

## 2. Set data types
- `transaction_timestamp` → Date/Time
- `amount` → Decimal Number
- `is_fraud` and all anomaly flags → Whole Number
- `risk_score` → Whole Number
- `transactions_last_1h` → Whole Number

## 3. Create the measures in DAX_MEASURES.txt
Create each measure from **Modeling → New measure**.

## 4. Dashboard pages
### Page 1 — Executive Overview
Cards:
- Total Transactions
- Transaction Value
- Fraud Transactions
- Fraud Rate
- Fraud Loss

Charts:
- Line chart: Fraud Rate by Month
- Column chart: Fraud Transactions by Fraud Type
- Bar chart: Fraud Rate by Merchant Category
- Donut: Fraud vs Legitimate

### Page 2 — Fraud Behaviour
Charts:
- Fraud Rate by Hour
- Fraud Rate by Payment Method
- Fraud Rate by Device Type
- Fraud Rate by City
- Fraud Rate by Merchant Category

Slicers:
- Date
- Merchant Category
- Payment Method
- Device Type
- City

### Page 3 — Risk Monitoring
Cards:
- High/Critical Transactions
- High/Critical Fraud Rate
- High/Critical Transaction Value

Charts:
- Risk Category distribution
- Fraud Rate by Risk Category
- Average Risk Score by Merchant Category
- Transactions Last 1h distribution

Table:
- transaction_id
- timestamp
- amount
- merchant_category
- city
- risk_score
- risk_category
- anomaly flags

### Page 4 — Business Actions
Use text boxes with these conclusions:
1. Location anomaly is the strongest statistically significant behavioural factor in this dataset.
2. Night transactions, device anomalies and high-risk merchants are also significantly associated with fraud.
3. The rule-based score is useful for prioritisation, but its thresholds should be tuned against the cost of missed fraud versus false alerts.
4. The logistic-regression benchmark shows predictive signal (ROC-AUC ≈ 0.668), but precision remains low because fraud is highly imbalanced.
5. Recommended workflow: low risk → approve; medium risk → passive monitoring; high risk → step-up verification; critical risk → manual review/temporary hold.

## 5. Formatting
Use a clean banking/fintech style. Keep one accent colour, neutral background, consistent INR formatting, and show percentages with one decimal place.
