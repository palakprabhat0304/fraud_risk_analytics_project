-- 03 FRAUD PATTERN INVESTIGATION
-- Objective: identify behavioural segments associated with fraud.

-- 1. Merchant category
SELECT
    t.merchant_category,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END),2) AS fraud_value,
    ROUND(AVG(t.amount),2) AS avg_transaction_value
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY fraud_rate_pct DESC;

-- 2. Payment method
SELECT
    t.payment_method,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY fraud_rate_pct DESC;

-- 3. Device type
SELECT
    t.device_type,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY fraud_rate_pct DESC;

-- 4. Hour of day
SELECT
    EXTRACT(HOUR FROM t.transaction_timestamp)::int AS transaction_hour,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY 1;

-- 5. Night vs daytime
SELECT
    CASE
        WHEN EXTRACT(HOUR FROM t.transaction_timestamp) < 5
          OR EXTRACT(HOUR FROM t.transaction_timestamp) >= 23
        THEN 'Night'
        ELSE 'Day'
    END AS time_segment,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY fraud_rate_pct DESC;

-- 6. Transaction amount bands
SELECT
    CASE
        WHEN t.amount < 500 THEN '< ₹500'
        WHEN t.amount < 2000 THEN '₹500–₹1,999'
        WHEN t.amount < 5000 THEN '₹2,000–₹4,999'
        WHEN t.amount < 10000 THEN '₹5,000–₹9,999'
        WHEN t.amount < 25000 THEN '₹10,000–₹24,999'
        ELSE '₹25,000+'
    END AS amount_band,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END),2) AS fraud_value
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY MIN(t.amount);

-- 7. City
SELECT
    t.transaction_city,
    COUNT(*) AS transactions,
    SUM(f.is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(f.is_fraud)/COUNT(*),3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END),2) AS fraud_value
FROM transactions t
JOIN fraud_labels f USING(transaction_id)
GROUP BY 1
ORDER BY fraud_rate_pct DESC;
