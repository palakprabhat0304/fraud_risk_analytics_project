-- 03_customer_risk.sql

WITH customer_metrics AS (
    SELECT
        t.customer_id,
        COUNT(*) AS transaction_count,
        SUM(t.amount) AS total_spend,
        AVG(t.amount) AS avg_transaction,
        SUM(f.is_fraud) AS fraud_count,
        SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END) AS fraud_value,
        MAX(t.transaction_timestamp) AS last_transaction
    FROM transactions t
    JOIN fraud_labels f USING(transaction_id)
    GROUP BY t.customer_id
)
SELECT *
FROM customer_metrics
ORDER BY fraud_value DESC
LIMIT 100;

-- High-value customers with fraud exposure
SELECT
    c.customer_id,
    c.account_type,
    c.city,
    COUNT(*) AS transactions,
    ROUND(SUM(t.amount),2) AS total_spend,
    SUM(f.is_fraud) AS fraud_count,
    ROUND(SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END),2) AS fraud_value
FROM customers c
JOIN transactions t ON c.customer_id=t.customer_id
JOIN fraud_labels f USING(transaction_id)
GROUP BY c.customer_id, c.account_type, c.city
HAVING SUM(t.amount) > 100000
ORDER BY fraud_value DESC;
