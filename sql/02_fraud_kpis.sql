-- 02 FRAUD KPIs
-- Core executive metrics.

SELECT
    COUNT(*) AS total_transactions,
    ROUND(SUM(t.amount),2) AS total_transaction_value,
    ROUND(AVG(t.amount),2) AS average_transaction_value,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.amount),2) AS median_transaction_value,
    SUM(f.is_fraud) AS fraudulent_transactions,
    ROUND(100.0 * SUM(f.is_fraud) / COUNT(*),3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN f.is_fraud = 1 THEN t.amount ELSE 0 END),2) AS fraud_value,
    ROUND(
        100.0 * SUM(CASE WHEN f.is_fraud = 1 THEN t.amount ELSE 0 END)
        / NULLIF(SUM(t.amount),0), 3
    ) AS fraud_value_pct
FROM transactions t
JOIN fraud_labels f USING(transaction_id);

-- Monthly fraud trend
SELECT
    DATE_TRUNC('month', t.transaction_timestamp)::date AS month,
    COUNT(*) AS transactions,
    ROUND(SUM(t.amount),2) AS transaction_value,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END),2) AS fraud_value
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY 1;

-- Fraud type
SELECT
    f.fraud_type,
    COUNT(*) AS fraud_transactions,
    ROUND(SUM(t.amount),2) AS fraud_value,
    ROUND(AVG(t.amount),2) AS avg_fraud_amount
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
WHERE f.is_fraud = 1
GROUP BY f.fraud_type
ORDER BY fraud_value DESC;
