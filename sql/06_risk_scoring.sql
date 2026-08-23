-- 06 RISK SCORING
-- Converts the feature score into operational risk categories.

SELECT
    transaction_id,
    customer_id,
    transaction_timestamp,
    amount,
    merchant_category,
    payment_method,
    device_type,
    transaction_city,
    is_fraud,

    night_transaction,
    device_anomaly,
    location_anomaly,
    rapid_transaction,
    amount_anomaly,
    payment_anomaly,
    new_account_flag,
    high_risk_merchant_flag,

    transactions_last_1h,
    amount_last_1h,
    transactions_last_24h,

    risk_score,

    CASE
        WHEN risk_score >= 75 THEN 'Critical'
        WHEN risk_score >= 50 THEN 'High'
        WHEN risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS risk_category

FROM v_transaction_risk_features
ORDER BY risk_score DESC;

-- Risk score performance against actual fraud labels
SELECT
    CASE
        WHEN risk_score >= 75 THEN 'Critical'
        WHEN risk_score >= 50 THEN 'High'
        WHEN risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS risk_category,
    COUNT(*) AS transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud)/COUNT(*),3) AS fraud_rate_pct,
    ROUND(SUM(CASE WHEN is_fraud=1 THEN amount ELSE 0 END),2) AS fraud_value
FROM v_transaction_risk_features
GROUP BY 1
ORDER BY
    CASE
        WHEN risk_category='Critical' THEN 1
        WHEN risk_category='High' THEN 2
        WHEN risk_category='Medium' THEN 3
        ELSE 4
    END;

-- Precision of a high-risk rule
SELECT
    COUNT(*) FILTER (WHERE risk_score >= 50) AS high_risk_alerts,
    COUNT(*) FILTER (WHERE risk_score >= 50 AND is_fraud=1) AS true_fraud_alerts,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE risk_score >= 50 AND is_fraud=1)
        / NULLIF(COUNT(*) FILTER (WHERE risk_score >= 50),0),
        2
    ) AS precision_pct,

    COUNT(*) FILTER (WHERE risk_score < 50 AND is_fraud=1) AS missed_fraud_transactions
FROM v_transaction_risk_features;
