-- 05 ADVANCED RISK FEATURES
-- Creates a transaction-level feature table for risk scoring.
-- This is the most important SQL file in the project.

DROP VIEW IF EXISTS v_transaction_risk_features;

CREATE VIEW v_transaction_risk_features AS
WITH base AS (
    SELECT
        t.transaction_id,
        t.customer_id,
        t.transaction_timestamp,
        t.amount,
        t.merchant_id,
        t.merchant_category,
        t.payment_method,
        t.device_type,
        t.transaction_city,
        t.transaction_status,
        f.is_fraud,
        f.fraud_type,
        c.city AS customer_home_city,
        c.preferred_device,
        c.preferred_payment_method,
        c.account_age_days,
        c.account_type,
        m.merchant_city,
        m.merchant_risk_score,

        LAG(t.transaction_timestamp) OVER (
            PARTITION BY t.customer_id
            ORDER BY t.transaction_timestamp
        ) AS previous_transaction_time,

        LAG(t.transaction_city) OVER (
            PARTITION BY t.customer_id
            ORDER BY t.transaction_timestamp
        ) AS previous_transaction_city,

        LAG(t.device_type) OVER (
            PARTITION BY t.customer_id
            ORDER BY t.transaction_timestamp
        ) AS previous_device,

        AVG(t.amount) OVER (
            PARTITION BY t.customer_id
            ORDER BY t.transaction_timestamp
            ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
        ) AS previous_10_avg_amount,

        COUNT(*) OVER (
            PARTITION BY t.customer_id
            ORDER BY t.transaction_timestamp
            ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
        ) AS previous_10_transaction_count

    FROM transactions t
    JOIN fraud_labels f USING(transaction_id)
    JOIN customers c USING(customer_id)
    JOIN merchants m USING(merchant_id)
),

features AS (
    SELECT
        *,
        EXTRACT(HOUR FROM transaction_timestamp)::int AS transaction_hour,

        ROUND(
            EXTRACT(EPOCH FROM
                (transaction_timestamp - previous_transaction_time)
            ) / 60.0, 2
        ) AS minutes_since_previous,

        CASE
            WHEN transaction_hour < 5 OR transaction_hour >= 23
            THEN 1 ELSE 0
        END AS night_transaction,

        CASE
            WHEN device_type <> preferred_device
            THEN 1 ELSE 0
        END AS device_anomaly,

        CASE
            WHEN transaction_city <> customer_home_city
            THEN 1 ELSE 0
        END AS location_anomaly,

        CASE
            WHEN previous_transaction_time IS NOT NULL
             AND EXTRACT(EPOCH FROM
                 (transaction_timestamp - previous_transaction_time)
             ) / 60.0 <= 5
            THEN 1 ELSE 0
        END AS rapid_transaction,

        CASE
            WHEN previous_10_avg_amount IS NOT NULL
             AND amount >= previous_10_avg_amount * 3
            THEN 1 ELSE 0
        END AS amount_anomaly,

        CASE
            WHEN payment_method <> preferred_payment_method
            THEN 1 ELSE 0
        END AS payment_anomaly,

        CASE
            WHEN account_age_days < 30
            THEN 1 ELSE 0
        END AS new_account_flag

    FROM base
),

velocity AS (
    SELECT
        f.*,

        COUNT(*) OVER (
            PARTITION BY customer_id
            ORDER BY transaction_timestamp
            RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
        ) AS transactions_last_1h,

        SUM(amount) OVER (
            PARTITION BY customer_id
            ORDER BY transaction_timestamp
            RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
        ) AS amount_last_1h,

        COUNT(*) OVER (
            PARTITION BY customer_id
            ORDER BY transaction_timestamp
            RANGE BETWEEN INTERVAL '24 hours' PRECEDING AND CURRENT ROW
        ) AS transactions_last_24h

    FROM features f
)

SELECT
    *,
    CASE
        WHEN merchant_risk_score >= 0.35 THEN 1 ELSE 0
    END AS high_risk_merchant_flag,

    -- Rule-based risk score: 0–100
    LEAST(
        100,
        (night_transaction * 10)
        + (device_anomaly * 15)
        + (location_anomaly * 15)
        + (rapid_transaction * 15)
        + (amount_anomaly * 15)
        + (payment_anomaly * 8)
        + (new_account_flag * 7)
        + (high_risk_merchant_flag * 15)
    ) AS risk_score

FROM velocity;
