"""
Fraud Detection & Financial Risk Analytics
Python Layer 2: ML benchmark

Purpose:
A small, interpretable benchmark to test whether behavioural features
can predict fraud. This is NOT the core of the project.

Outputs:
- model_metrics.csv
- confusion_matrix.csv
- feature_importance.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

transactions = pd.read_csv(DATA / "transactions.csv", parse_dates=["transaction_timestamp"])
fraud = pd.read_csv(DATA / "fraud_labels.csv")
customers = pd.read_csv(DATA / "customers.csv")
merchants = pd.read_csv(DATA / "merchants.csv")

df = (
    transactions
    .merge(fraud, on="transaction_id", how="left")
    .merge(customers, on="customer_id", how="left")
    .merge(merchants, on="merchant_id", how="left", suffixes=("", "_merchant"))
)

# Features available at transaction decision time.
df["hour"] = df["transaction_timestamp"].dt.hour
df["night_transaction"] = ((df["hour"] < 5) | (df["hour"] >= 23)).astype(int)
df["device_anomaly"] = (df["device_type"] != df["preferred_device"]).astype(int)
df["location_anomaly"] = (df["transaction_city"] != df["city"]).astype(int)
df["payment_anomaly"] = (df["payment_method"] != df["preferred_payment_method"]).astype(int)
df["high_risk_merchant"] = (df["merchant_risk_score"] >= 0.35).astype(int)
df["log_amount"] = np.log1p(df["amount"])

# Use a chronological split rather than random split to reduce leakage.
df = df.sort_values("transaction_timestamp")
split = int(len(df)*0.80)
train = df.iloc[:split].copy()
test = df.iloc[split:].copy()

features = [
    "log_amount",
    "hour",
    "night_transaction",
    "device_anomaly",
    "location_anomaly",
    "payment_anomaly",
    "high_risk_merchant",
    "merchant_risk_score",
    "account_age_days",
    "account_type",
    "payment_method",
    "device_type",
    "merchant_category"
]

X_train, y_train = train[features], train["is_fraud"]
X_test, y_test = test[features], test["is_fraud"]

numeric = [
    "log_amount","hour","night_transaction","device_anomaly",
    "location_anomaly","payment_anomaly","high_risk_merchant",
    "merchant_risk_score","account_age_days"
]
categorical = ["account_type","payment_method","device_type","merchant_category"]

preprocess = ColumnTransformer([
    ("num", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ]), numeric),
    ("cat", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ]), categorical)
])

model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced",
    random_state=42
)

pipe = Pipeline([
    ("preprocess", preprocess),
    ("model", model)
])

pipe.fit(X_train, y_train)
proba = pipe.predict_proba(X_test)[:,1]

# Default threshold plus a business-oriented threshold table.
rows = []
for threshold in [0.20, 0.30, 0.40, 0.50, 0.70]:
    pred = (proba >= threshold).astype(int)
    rows.append({
        "threshold": threshold,
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, proba)
    })

metrics = pd.DataFrame(rows)
metrics.to_csv(OUT / "model_metrics.csv", index=False)

pred_default = (proba >= .50).astype(int)
cm = confusion_matrix(y_test, pred_default)
pd.DataFrame(
    cm,
    index=["Actual Legitimate","Actual Fraud"],
    columns=["Predicted Legitimate","Predicted Fraud"]
).to_csv(OUT / "confusion_matrix.csv")

print(metrics)
print("\nClassification report at threshold 0.50")
print(classification_report(y_test, pred_default, zero_division=0))
