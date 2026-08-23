-- 04 WINDOW FUNCTIONS
-- Objective: detect customer-level behavioural anomalies.

-- 1. Previous transaction and time gap
WITH ordered AS (
    SELECT
        t.*,
        LAG(transaction_timestamp) OVER (
            PARTITION BY customer_id
            ORDER BY transaction_timestamp
        ) AS previous_transaction_time,
        LAG(transaction_city) OVER (
            PARTITION BY customer_id
            ORDER BY transaction_timestamp
        ) AS previous_transaction_city,
        LAG(device_type) OVER (
            PARTITION BY customer_id
            ORDER BY transaction_timestamp
        ) AS previous_device,
        LAG(amount) OVER (
            PARTITION BY customer_id
            ORDER BY transaction_timestamp
        ) AS previous_amount
    FROM transactions t
)
SELECT
    *,
    ROUND(
        EXTRACT(EPOCH FROM
            (transaction_timestamp - previous_transaction_time)
        ) / 60.0, 2
    ) AS minutes_since_previous,
    CASE
        WHEN previous_transaction_time IS NOT NULL
         AND EXTRACT(EPOCH FROM
            (transaction_timestamp - previous_transaction_time)
         ) / 60.0 <= 5
        THEN 1 ELSE 0
    END AS rapid_transaction_flag,
    CASE
        WHEN previous_transaction_city IS NOT NULL
         AND transaction_city <> previous_transaction_city
        THEN 1 ELSE 0
    END AS location_change_flag,
    CASE
        WHEN previous_device IS NOT NULL
         AND device_type <> previous_device
        THEN 1 ELSE 0
    END AS device_change_flag
FROM ordered;

-- 2. Customer running transaction count
SELECT
    transaction_id,
    customer_id,
    transaction_timestamp,
    amount,
    COUNT(*) OVER (
        PARTITION BY customer_id
        ORDER BY transaction_timestamp
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS customer_running_transaction_count
FROM transactions
ORDER BY customer_id, transaction_timestamp;

-- 3. Customer transaction amount percentile/rank
SELECT
    t.*,
    NTILE(100) OVER (
        PARTITION BY customer_id
        ORDER BY amount
    ) AS customer_amount_percentile,
    RANK() OVER (
        PARTITION BY customer_id
        ORDER BY amount DESC
    ) AS customer_amount_rank
FROM transactions t;

-- 4. Merchant risk ranking
SELECT
    merchant_id,
    merchant_category,
    merchant_risk_score,
    RANK() OVER (
        ORDER BY merchant_risk_score DESC
    ) AS merchant_risk_rank
FROM merchants
ORDER BY merchant_risk_rank;

-- 5. Top fraud-value merchants within each category
WITH merchant_fraud AS (
    SELECT
        t.merchant_category,
        t.merchant_id,
        COUNT(*) AS transactions,
        SUM(f.is_fraud) AS fraud_transactions,
        SUM(CASE WHEN f.is_fraud=1 THEN t.amount ELSE 0 END) AS fraud_value
    FROM transactions t
    JOIN fraud_labels f USING(transaction_id)
    GROUP BY 1,2
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY merchant_category
            ORDER BY fraud_value DESC
        ) AS category_rank
    FROM merchant_fraud
)
SELECT *
FROM ranked
WHERE category_rank <= 5
ORDER BY merchant_category, category_rank;
