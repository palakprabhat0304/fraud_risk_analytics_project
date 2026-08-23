"""
Fraud Detection & Financial Risk Analytics
Python Layer 1: EDA + Statistical Analysis

Run from this folder:
    python 02_eda_and_statistics.py

Outputs are saved under ../outputs/
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

# -------------------------
# 1. Load
# -------------------------
customers = pd.read_csv(DATA / "customers.csv")
merchants = pd.read_csv(DATA / "merchants.csv")
transactions = pd.read_csv(DATA / "transactions.csv", parse_dates=["transaction_timestamp"])
fraud = pd.read_csv(DATA / "fraud_labels.csv")

df = (
    transactions
    .merge(fraud, on="transaction_id", how="left", validate="one_to_one")
    .merge(customers[["customer_id","age","gender","city","account_age_days","account_type",
                      "preferred_device","preferred_payment_method"]],
           on="customer_id", how="left", validate="many_to_one")
    .merge(merchants[["merchant_id","merchant_risk_score","merchant_city"]],
           on="merchant_id", how="left", validate="many_to_one")
)

assert len(df) == len(transactions), "Merge changed transaction row count."

# -------------------------
# 2. Basic data quality
# -------------------------
quality = pd.DataFrame({
    "column": df.columns,
    "dtype": [str(df[c].dtype) for c in df.columns],
    "missing": [int(df[c].isna().sum()) for c in df.columns],
    "unique": [int(df[c].nunique(dropna=True)) for c in df.columns]
})
quality.to_csv(OUT / "data_quality_summary.csv", index=False)

# -------------------------
# 3. Feature engineering
# -------------------------
df["hour"] = df["transaction_timestamp"].dt.hour
df["date"] = df["transaction_timestamp"].dt.date
df["day_of_week"] = df["transaction_timestamp"].dt.day_name()
df["month"] = df["transaction_timestamp"].dt.to_period("M").astype(str)

df["night_transaction"] = (
    (df["hour"] < 5) | (df["hour"] >= 23)
).astype(int)

df["device_anomaly"] = (
    df["device_type"] != df["preferred_device"]
).astype(int)

df["location_anomaly"] = (
    df["transaction_city"] != df["city"]
).astype(int)

df["payment_anomaly"] = (
    df["payment_method"] != df["preferred_payment_method"]
).astype(int)

df["amount_log"] = np.log1p(df["amount"])

# Customer rolling behaviour
df = df.sort_values(["customer_id","transaction_timestamp"]).reset_index(drop=True)
df["previous_timestamp"] = df.groupby("customer_id")["transaction_timestamp"].shift(1)
df["minutes_since_previous"] = (
    df["transaction_timestamp"] - df["previous_timestamp"]
).dt.total_seconds() / 60

df["rapid_transaction"] = (
    df["minutes_since_previous"].le(5)
).fillna(False).astype(int)

df["previous_amount_mean"] = (
    df.groupby("customer_id")["amount"]
      .transform(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
)

df["amount_anomaly"] = (
    df["previous_amount_mean"].notna()
    & (df["amount"] >= 3 * df["previous_amount_mean"])
).astype(int)

# Rolling transaction velocity
df["transactions_last_1h"] = (
    df.groupby("customer_id", group_keys=False)
      .apply(lambda g: g.set_index("transaction_timestamp")["transaction_id"]
             .rolling("1h").count().values, include_groups=False)
      .explode()
      .astype(float)
      .values
)

# The rolling operation above can be sensitive to pandas versions/order.
# Recalculate robustly using a simple grouped loop if shape mismatch occurs.
if len(df["transactions_last_1h"]) != len(df):
    df["transactions_last_1h"] = np.nan

# More robust vectorized calculation using timestamp search per customer.
# For this portfolio dataset, the exact rolling count is calculated below.
velocity = np.zeros(len(df), dtype=int)
for _, idx in df.groupby("customer_id", sort=False).groups.items():
    pos = np.array(list(idx))
    times = df.loc[pos, "transaction_timestamp"].astype("int64").to_numpy()
    left = np.searchsorted(times, times - 3600*10**9, side="left")
    velocity[pos] = np.arange(len(pos)) - left + 1
df["transactions_last_1h"] = velocity

df["high_risk_merchant"] = (df["merchant_risk_score"] >= 0.35).astype(int)

# Rule-based score matching SQL layer
df["risk_score"] = (
    10 * df["night_transaction"]
    + 15 * df["device_anomaly"]
    + 15 * df["location_anomaly"]
    + 15 * df["rapid_transaction"]
    + 15 * df["amount_anomaly"]
    + 8 * df["payment_anomaly"]
    + 7 * (df["account_age_days"] < 30).astype(int)
    + 15 * df["high_risk_merchant"]
).clip(upper=100)

df["risk_category"] = pd.cut(
    df["risk_score"],
    bins=[-1,24,49,74,100],
    labels=["Low","Medium","High","Critical"]
)

# -------------------------
# 4. KPI table
# -------------------------
total = len(df)
fraud_n = int(df["is_fraud"].sum())
kpis = pd.DataFrame([{
    "total_transactions": total,
    "total_transaction_value_inr": df["amount"].sum(),
    "average_transaction_value_inr": df["amount"].mean(),
    "median_transaction_value_inr": df["amount"].median(),
    "fraud_transactions": fraud_n,
    "fraud_rate_pct": 100 * fraud_n / total,
    "fraud_value_inr": df.loc[df["is_fraud"].eq(1), "amount"].sum()
}])
kpis.to_csv(OUT / "core_kpis.csv", index=False)

# -------------------------
# 5. Segment analyses
# -------------------------
def fraud_summary(group_col):
    x = df.groupby(group_col, dropna=False).agg(
        transactions=("transaction_id","count"),
        fraud_transactions=("is_fraud","sum"),
        transaction_value=("amount","sum"),
        fraud_value=("amount", lambda s: s[df.loc[s.index,"is_fraud"].eq(1)].sum())
    ).reset_index()
    x["fraud_rate_pct"] = 100 * x["fraud_transactions"] / x["transactions"]
    return x.sort_values("fraud_rate_pct", ascending=False)

for col, filename in [
    ("merchant_category","fraud_by_merchant_category.csv"),
    ("payment_method","fraud_by_payment_method.csv"),
    ("device_type","fraud_by_device.csv"),
    ("transaction_city","fraud_by_city.csv"),
    ("hour","fraud_by_hour.csv"),
    ("day_of_week","fraud_by_day.csv"),
    ("risk_category","fraud_by_risk_category.csv")
]:
    fraud_summary(col).to_csv(OUT / filename, index=False)

# Fraud type
fraud_type = (
    df[df["is_fraud"].eq(1)]
    .groupby("fraud_type")
    .agg(
        fraud_transactions=("transaction_id","count"),
        fraud_value=("amount","sum"),
        avg_fraud_amount=("amount","mean")
    )
    .reset_index()
    .sort_values("fraud_value", ascending=False)
)
fraud_type.to_csv(OUT / "fraud_by_type.csv", index=False)

# -------------------------
# 6. Behavioural comparisons
# -------------------------
behaviour_cols = [
    "night_transaction",
    "device_anomaly",
    "location_anomaly",
    "payment_anomaly",
    "rapid_transaction",
    "amount_anomaly",
    "high_risk_merchant"
]

rows = []
for c in behaviour_cols:
    for value in [0,1]:
        subset = df[df[c].eq(value)]
        rows.append({
            "feature": c,
            "feature_value": value,
            "transactions": len(subset),
            "fraud_transactions": int(subset["is_fraud"].sum()),
            "fraud_rate_pct": 100 * subset["is_fraud"].mean(),
            "fraud_value": subset.loc[subset["is_fraud"].eq(1),"amount"].sum()
        })
behaviour = pd.DataFrame(rows)
behaviour.to_csv(OUT / "behavioural_fraud_comparison.csv", index=False)

# -------------------------
# 7. Statistical tests
# -------------------------
# A. Mann-Whitney U: transaction amount differs between fraud/non-fraud.
fraud_amount = df.loc[df["is_fraud"].eq(1), "amount"]
legit_amount = df.loc[df["is_fraud"].eq(0), "amount"]

u_stat, u_p = stats.mannwhitneyu(
    fraud_amount, legit_amount, alternative="two-sided"
)

# B. Chi-square tests for categorical binary behaviour flags vs fraud.
chi_rows = []
for c in behaviour_cols:
    table = pd.crosstab(df[c], df["is_fraud"])
    chi2, p, dof, expected = stats.chi2_contingency(table)
    chi_rows.append({
        "feature": c,
        "chi2": chi2,
        "p_value": p,
        "significant_at_0_05": p < 0.05
    })

stat_tests = pd.DataFrame(chi_rows)
stat_tests.loc[len(stat_tests)] = [
    "transaction_amount_mann_whitney_u",
    u_stat,
    u_p,
    u_p < 0.05
]
stat_tests.to_csv(OUT / "statistical_tests.csv", index=False)

# Effect-size style comparison
effect = []
for c in behaviour_cols:
    rates = df.groupby(c)["is_fraud"].mean()
    effect.append({
        "feature": c,
        "fraud_rate_when_0_pct": 100*rates.get(0, np.nan),
        "fraud_rate_when_1_pct": 100*rates.get(1, np.nan),
        "risk_rate_ratio": rates.get(1, np.nan) / rates.get(0, np.nan)
    })
pd.DataFrame(effect).to_csv(OUT / "behaviour_effect_sizes.csv", index=False)

# -------------------------
# 8. Risk score validation
# -------------------------
thresholds = [25, 50, 75]
rows = []
for threshold in thresholds:
    predicted = df["risk_score"] >= threshold
    actual = df["is_fraud"].eq(1)
    tp = int((predicted & actual).sum())
    fp = int((predicted & ~actual).sum())
    fn = int((~predicted & actual).sum())
    tn = int((~predicted & ~actual).sum())

    precision = tp/(tp+fp) if tp+fp else 0
    recall = tp/(tp+fn) if tp+fn else 0
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0

    rows.append({
        "threshold": threshold,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    })
risk_validation = pd.DataFrame(rows)
risk_validation.to_csv(OUT / "risk_score_validation.csv", index=False)

# -------------------------
# 9. Charts
# -------------------------
def savefig(name):
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=180, bbox_inches="tight")
    plt.close()

# Fraud rate by hour
hourly = fraud_summary("hour").sort_values("hour")
plt.figure(figsize=(10,5))
plt.plot(hourly["hour"], hourly["fraud_rate_pct"], marker="o")
plt.xlabel("Hour")
plt.ylabel("Fraud Rate (%)")
plt.title("Fraud Rate by Transaction Hour")
savefig("fraud_rate_by_hour.png")

# Fraud rate by merchant category
cat = fraud_summary("merchant_category").sort_values("fraud_rate_pct")
plt.figure(figsize=(10,6))
plt.barh(cat["merchant_category"], cat["fraud_rate_pct"])
plt.xlabel("Fraud Rate (%)")
plt.title("Fraud Rate by Merchant Category")
savefig("fraud_rate_by_merchant_category.png")

# Fraud vs legitimate amounts
sample = df.sample(min(50000, len(df)), random_state=42)
plt.figure(figsize=(9,5))
plt.hist(np.log1p(sample.loc[sample["is_fraud"].eq(0),"amount"]), bins=60, alpha=.65, label="Legitimate")
plt.hist(np.log1p(sample.loc[sample["is_fraud"].eq(1),"amount"]), bins=60, alpha=.65, label="Fraud")
plt.xlabel("log(1 + transaction amount)")
plt.ylabel("Transactions")
plt.title("Transaction Amount Distribution")
plt.legend()
savefig("transaction_amount_distribution.png")

# Risk category fraud rate
risk = fraud_summary("risk_category")
order = ["Low","Medium","High","Critical"]
risk["order"] = risk["risk_category"].astype(str).map({x:i for i,x in enumerate(order)})
risk = risk.sort_values("order")
plt.figure(figsize=(8,5))
plt.bar(risk["risk_category"].astype(str), risk["fraud_rate_pct"])
plt.xlabel("Risk Category")
plt.ylabel("Fraud Rate (%)")
plt.title("Fraud Rate by Risk Category")
savefig("fraud_rate_by_risk_category.png")

# -------------------------
# 10. Export dashboard-ready transaction sample + full analytical table
# -------------------------
export_cols = [
    "transaction_id","customer_id","transaction_timestamp","amount",
    "merchant_id","merchant_category","payment_method","device_type",
    "transaction_city","transaction_status","is_fraud","fraud_type",
    "risk_score","risk_category","night_transaction","device_anomaly",
    "location_anomaly","rapid_transaction","amount_anomaly",
    "payment_anomaly","high_risk_merchant","transactions_last_1h"
]
df[export_cols].to_csv(OUT / "powerbi_transaction_risk.csv", index=False)

print("Python EDA + statistics complete.")
print("Outputs:", OUT)
