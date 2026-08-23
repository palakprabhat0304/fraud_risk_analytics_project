# Fraud Detection & Financial Risk Analytics
# Stage 1: Load + basic EDA

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

customers = pd.read_csv("../data/customers.csv")
merchants = pd.read_csv("../data/merchants.csv")
transactions = pd.read_csv("../data/transactions.csv", parse_dates=["transaction_timestamp"])
fraud = pd.read_csv("../data/fraud_labels.csv")

df = transactions.merge(fraud, on="transaction_id", how="left")

print(df.shape)
print(df.head())
print(df.isna().sum())

# Core KPIs
total_transactions = len(df)
total_value = df["amount"].sum()
fraud_transactions = df["is_fraud"].sum()
fraud_rate = fraud_transactions / total_transactions
fraud_value = df.loc[df["is_fraud"] == 1, "amount"].sum()

print({
    "total_transactions": total_transactions,
    "total_value": total_value,
    "fraud_transactions": int(fraud_transactions),
    "fraud_rate": fraud_rate,
    "fraud_value": fraud_value
})

# Fraud by category
category = (
    df.groupby("merchant_category")
      .agg(transactions=("transaction_id","count"),
           fraud_transactions=("is_fraud","sum"),
           fraud_value=("amount", lambda x: x[df.loc[x.index,"is_fraud"].eq(1)].sum()))
)
category["fraud_rate"] = category["fraud_transactions"] / category["transactions"]
print(category.sort_values("fraud_rate", ascending=False))

# Fraud by hour
df["hour"] = df["transaction_timestamp"].dt.hour
hourly = df.groupby("hour")["is_fraud"].mean()
print(hourly)

# Next stages:
# 1. Build behavioural features
# 2. Create rule-based risk score
# 3. Validate risk score against fraud labels
# 4. Optional: Logistic Regression / Random Forest
# 5. Export dashboard-ready table for Power BI
