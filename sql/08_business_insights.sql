-- 08 BUSINESS INSIGHTS
-- Queries designed to produce final resume/GitHub insights.

-- A. High-risk transactions and their fraud conversion
SELECT
    COUNT(*) AS high_risk_transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud)/COUNT(*),2) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value
FROM v_transaction_risk_features
WHERE risk_score >= 50;

-- B. Transactions with multiple simultaneous risk signals
SELECT
    (
        night_transaction
        + device_anomaly
        + location_anomaly
        + rapid_transaction
        + amount_anomaly
        + payment_anomaly
        + high_risk_merchant_flag
    ) AS risk_signal_count,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud)/COUNT(*),2) AS fraud_rate_pct
FROM v_transaction_risk_features
GROUP BY 1
ORDER BY 1;

-- C. Cross-city + new-device combination
SELECT
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud)/COUNT(*),2) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value
FROM v_transaction_risk_features
WHERE location_anomaly = 1
  AND device_anomaly = 1;

-- D. Night + high-risk merchant combination
SELECT
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud)/COUNT(*),2) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value
FROM v_transaction_risk_features
WHERE night_transaction = 1
  AND high_risk_merchant_flag = 1;

-- E. Top 20 customers by potential fraud exposure
SELECT
    customer_id,
    COUNT(*) AS transactions,
    ROUND(SUM(amount),2) AS total_spend,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value,
    ROUND(AVG(risk_score),2) AS avg_risk_score,
    MAX(risk_score) AS max_risk_score
FROM v_transaction_risk_features
GROUP BY customer_id
ORDER BY fraud_value DESC
LIMIT 20;

-- F. Merchant categories ranked by fraud value
SELECT
    merchant_category,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud)/COUNT(*),2) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value
FROM v_transaction_risk_features
GROUP BY merchant_category
ORDER BY fraud_value DESC;
