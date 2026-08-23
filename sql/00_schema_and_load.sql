-- FRAUD RISK ANALYTICS
-- PostgreSQL setup
-- Run this first after placing the CSV files in a PostgreSQL-accessible folder.
-- If COPY is blocked by permissions, use pgAdmin's Import/Export GUI instead.

DROP TABLE IF EXISTS fraud_labels;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    age INT,
    gender VARCHAR(20),
    city VARCHAR(50),
    account_age_days INT,
    account_type VARCHAR(20),
    preferred_device VARCHAR(20),
    preferred_payment_method VARCHAR(30)
);

CREATE TABLE merchants (
    merchant_id VARCHAR(20) PRIMARY KEY,
    merchant_category VARCHAR(50),
    merchant_city VARCHAR(50),
    merchant_risk_score NUMERIC(8,4)
);

CREATE TABLE transactions (
    transaction_id VARCHAR(30) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    merchant_id VARCHAR(20) NOT NULL,
    merchant_category VARCHAR(50),
    payment_method VARCHAR(30),
    device_type VARCHAR(20),
    transaction_city VARCHAR(50),
    transaction_status VARCHAR(20)
);

CREATE TABLE fraud_labels (
    transaction_id VARCHAR(30) PRIMARY KEY,
    is_fraud INT NOT NULL,
    fraud_type VARCHAR(50)
);

-- Change these paths to your actual CSV locations.
-- Example:
-- COPY customers FROM 'C:/fraud_risk_analytics/data/customers.csv'
-- WITH (FORMAT csv, HEADER true);

-- COPY merchants FROM 'C:/fraud_risk_analytics/data/merchants.csv'
-- WITH (FORMAT csv, HEADER true);

-- COPY transactions FROM 'C:/fraud_risk_analytics/data/transactions.csv'
-- WITH (FORMAT csv, HEADER true);

-- COPY fraud_labels FROM 'C:/fraud_risk_analytics/data/fraud_labels.csv'
-- WITH (FORMAT csv, HEADER true);

CREATE INDEX idx_transactions_customer ON transactions(customer_id);
CREATE INDEX idx_transactions_merchant ON transactions(merchant_id);
CREATE INDEX idx_transactions_timestamp ON transactions(transaction_timestamp);
CREATE INDEX idx_fraud_labels_fraud ON fraud_labels(is_fraud);
