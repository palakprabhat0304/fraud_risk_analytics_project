-- 07 CUSTOMER RISK
-- Customer-level aggregation for the Power BI customer-risk page.

WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS transaction_count,
        ROUND(SUM(amount),2) AS total_spend,
        ROUND(AVG(amount),2) AS avg_transaction_value,
        ROUND(MAX(amount),2) AS max_transaction_value,

        SUM(is_fraud) AS fraud_transactions,
        ROUND(
            SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2
        ) AS fraud_value,

        ROUND(AVG(risk_score),2) AS avg_risk_score,
        ROUND(MAX(risk_score),2) AS max_risk_score,

        COUNT(*) FILTER (WHERE risk_score >= 50) AS high_risk_transactions,
        COUNT(*) FILTER (WHERE risk_score >= 75) AS critical_transactions,

        COUNT(*) FILTER (WHERE night_transaction=1) AS night_transactions,
        COUNT(*) FILTER (WHERE device_anomaly=1) AS device_anomaly_transactions,
        COUNT(*) FILTER (WHERE location_anomaly=1) AS location_anomaly_transactions,
        COUNT(*) FILTER (WHERE rapid_transaction=1) AS rapid_transactions

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
          OR cm.fraud_value >= 50000
        THEN 'Critical'
        WHEN cm.max_risk_score >= 50
          OR cm.fraud_transactions >= 2
        THEN 'High'
        WHEN cm.avg_risk_score >= 25
        THEN 'Medium'
        ELSE 'Low'
    END AS customer_risk_category

FROM customer_metrics cm
JOIN customers c USING(customer_id)
ORDER BY
    CASE
        WHEN cm.max_risk_score >= 75
          OR cm.fraud_value >= 50000 THEN 1
        WHEN cm.max_risk_score >= 50
          OR cm.fraud_transactions >= 2 THEN 2
        WHEN cm.avg_risk_score >= 25 THEN 3
        ELSE 4
    END,
    cm.fraud_value DESC;
