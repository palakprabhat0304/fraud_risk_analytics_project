-- 02_fraud_overview.sql

SELECT
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount),2) AS total_transaction_value,
    ROUND(AVG(amount),2) AS avg_transaction_value,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*),3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value
FROM transactions t
JOIN fraud_labels f USING (transaction_id);

-- Fraud by merchant category
SELECT
    t.merchant_category,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),2) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END),2) AS fraud_value
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY t.merchant_category
ORDER BY fraud_rate_pct DESC;

-- Fraud by hour
SELECT
    EXTRACT(HOUR FROM transaction_timestamp) AS hour,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),2) AS fraud_rate_pct
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY EXTRACT(HOUR FROM transaction_timestamp)
ORDER BY hour;

-- Fraud by payment method
SELECT
    t.payment_method,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),2) AS fraud_rate_pct
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY t.payment_method
ORDER BY fraud_rate_pct DESC;
