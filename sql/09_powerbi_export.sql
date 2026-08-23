-- 09 POWER BI EXPORT
-- These are the two clean analytical views you should connect to Power BI.

DROP VIEW IF EXISTS v_powerbi_transaction_risk;
CREATE VIEW v_powerbi_transaction_risk AS
SELECT
    transaction_id,
    customer_id,
    transaction_timestamp,
    amount,
    merchant_id,
    merchant_category,
    payment_method,
    device_type,
    transaction_city,
    transaction_status,
    is_fraud,
    fraud_type,
    risk_score,
    CASE
        WHEN risk_score >= 75 THEN 'Critical'
        WHEN risk_score >= 50 THEN 'High'
        WHEN risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS risk_category,
    night_transaction,
    device_anomaly,
    location_anomaly,
    rapid_transaction,
    amount_anomaly,
    payment_anomaly,
    high_risk_merchant_flag,
    transactions_last_1h,
    amount_last_1h,
    transactions_last_24h
FROM v_transaction_risk_features;

DROP VIEW IF EXISTS v_powerbi_customer_risk;
CREATE VIEW v_powerbi_customer_risk AS
WITH cm AS (
    SELECT
        customer_id,
        COUNT(*) AS transaction_count,
        ROUND(SUM(amount),2) AS total_spend,
        ROUND(AVG(amount),2) AS avg_transaction_value,
        SUM(is_fraud) AS fraud_transactions,
        ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value,
        ROUND(AVG(risk_score),2) AS avg_risk_score,
        MAX(risk_score) AS max_risk_score,
        COUNT(*) FILTER (WHERE risk_score >= 50) AS high_risk_transactions
    FROM v_transaction_risk_features
    GROUP BY customer_id
)
SELECT
    cm.*,
    c.age,
    c.gender,
    c.city,
    c.account_age_days,
    c.account_type,
    CASE
        WHEN cm.max_risk_score >= 75
          OR cm.fraud_value >= 50000 THEN 'Critical'
        WHEN cm.max_risk_score >= 50
          OR cm.fraud_transactions >= 2 THEN 'High'
        WHEN cm.avg_risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS customer_risk_category
FROM cm
JOIN customers c USING(customer_id);
