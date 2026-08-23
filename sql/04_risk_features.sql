-- 04_risk_features.sql
-- Build analyst-friendly behavioural features before any ML.

WITH ordered AS (
    SELECT
        t.*,
        f.is_fraud,
        c.preferred_device,
        c.city AS home_city,
        LAG(t.transaction_timestamp) OVER (
            PARTITION BY t.customer_id ORDER BY t.transaction_timestamp
        ) AS prev_timestamp,
        LAG(t.transaction_city) OVER (
            PARTITION BY t.customer_id ORDER BY t.transaction_timestamp
        ) AS prev_city
    FROM transactions t
    JOIN fraud_labels f USING(transaction_id)
    JOIN customers c USING(customer_id)
)
SELECT
    *,
    EXTRACT(EPOCH FROM (transaction_timestamp - prev_timestamp))/60.0 AS minutes_since_previous,
    CASE WHEN transaction_city <> home_city THEN 1 ELSE 0 END AS location_anomaly,
    CASE WHEN device_type <> preferred_device THEN 1 ELSE 0 END AS device_anomaly,
    CASE WHEN EXTRACT(HOUR FROM transaction_timestamp) < 5
              OR EXTRACT(HOUR FROM transaction_timestamp) >= 23 THEN 1 ELSE 0 END AS night_transaction,
    CASE WHEN EXTRACT(EPOCH FROM (transaction_timestamp - prev_timestamp))/60.0 <= 5 THEN 1 ELSE 0 END AS rapid_transaction
FROM ordered;
