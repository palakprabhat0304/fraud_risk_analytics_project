-- 01 DATA QUALITY
-- Objective: prove the dataset is usable before analysis.

-- 1. Row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'merchants', COUNT(*) FROM merchants
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'fraud_labels', COUNT(*) FROM fraud_labels;

-- 2. Duplicate primary keys
SELECT customer_id, COUNT(*) AS duplicate_count
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

SELECT merchant_id, COUNT(*) AS duplicate_count
FROM merchants
GROUP BY merchant_id
HAVING COUNT(*) > 1;

SELECT transaction_id, COUNT(*) AS duplicate_count
FROM transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;

SELECT transaction_id, COUNT(*) AS duplicate_count
FROM fraud_labels
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- 3. Null checks
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE customer_id IS NULL) AS null_customer_id,
    COUNT(*) FILTER (WHERE transaction_timestamp IS NULL) AS null_timestamp,
    COUNT(*) FILTER (WHERE amount IS NULL) AS null_amount,
    COUNT(*) FILTER (WHERE merchant_id IS NULL) AS null_merchant_id,
    COUNT(*) FILTER (WHERE transaction_status IS NULL) AS null_status
FROM transactions;

-- 4. Invalid values
SELECT *
FROM transactions
WHERE amount <= 0;

SELECT *
FROM transactions
WHERE transaction_status NOT IN ('Successful','Failed','Reversed');

SELECT *
FROM fraud_labels
WHERE is_fraud NOT IN (0,1);

-- 5. Referential integrity checks
SELECT COUNT(*) AS transactions_without_customer
FROM transactions t
LEFT JOIN customers c USING(customer_id)
WHERE c.customer_id IS NULL;

SELECT COUNT(*) AS transactions_without_merchant
FROM transactions t
LEFT JOIN merchants m USING(merchant_id)
WHERE m.merchant_id IS NULL;

SELECT COUNT(*) AS transactions_without_fraud_label
FROM transactions t
LEFT JOIN fraud_labels f USING(transaction_id)
WHERE f.transaction_id IS NULL;
