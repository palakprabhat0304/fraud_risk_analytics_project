"""
Fraud Detection & Financial Risk Analytics
Layer 3: Data-driven scorecard, honest model comparison, cost-based thresholds.

Why this script exists
----------------------
The original hand-weighted score (script 02) had three problems found in review:
  1. Two of its rules were dead: `payment_anomaly` is always 0 (every transaction uses the
     customer's preferred payment method) and `amount_anomaly` has no relationship with fraud
     (1.54% vs 1.54%). `rapid_transaction` fires on 73 of 275,000 rows.
  2. The 'Critical' tier was empty and 'High' held 17 transactions, so the tiers could not drive
     an operating policy.
  3. Thresholds were never tied to money, so there was no basis for choosing one.

This script:
  * keeps only features with demonstrated signal and checks them for stability over time
  * fits an interpretable logistic scorecard on a chronological train split (first 80%)
  * converts it to 0-100 points, defines tiers from *train* quantiles
  * evaluates on the held-out final 20% with bootstrap confidence intervals
  * compares it with the old rule score and with gradient boosting
  * chooses an operating threshold by expected net benefit (INR), with editable assumptions

Run from anywhere:  python python/05_scorecard_and_cost_analysis.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "outputs" / "v2"
FIG = ROOT / "outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)

# ---------------- Business assumptions (EDIT THESE) ----------------
REVIEW_COST_INR = 40.0        # cost of one manual review / step-up challenge incl. friction
DETECTION_RATE = 0.85         # share of a flagged fraud's value actually prevented
SEED = 42
rng = np.random.default_rng(SEED)

# ---------------- Load & feature engineering ----------------
t = pd.read_csv(DATA / "transactions.csv", parse_dates=["transaction_timestamp"])
f = pd.read_csv(DATA / "fraud_labels.csv")
c = pd.read_csv(DATA / "customers.csv")
m = pd.read_csv(DATA / "merchants.csv")[["merchant_id", "merchant_risk_score"]]
df = (t.merge(f, on="transaction_id", validate="one_to_one")
        .merge(c, on="customer_id", validate="many_to_one")
        .merge(m, on="merchant_id", validate="many_to_one")
        .sort_values("transaction_timestamp").reset_index(drop=True))

df["hour"] = df.transaction_timestamp.dt.hour
df["night"] = ((df.hour < 5) | (df.hour >= 23)).astype(int)
df["device_anomaly"] = (df.device_type != df.preferred_device).astype(int)
df["location_anomaly"] = (df.transaction_city != df.city).astype(int)
df["merchant_risk"] = df.merchant_risk_score

# Legacy rule score (as shipped in script 02) for comparison
df["minutes_prev"] = df.groupby("customer_id").transaction_timestamp.diff().dt.total_seconds() / 60
df["rapid"] = df.minutes_prev.le(5).astype(int)
df["legacy_score"] = (10*df.night + 15*df.device_anomaly + 15*df.location_anomaly
                      + 15*df.rapid + 15*(df.merchant_risk >= .35)).clip(upper=100)

FEATURES = ["night", "device_anomaly", "location_anomaly", "merchant_risk"]
cut = int(len(df) * 0.8)
train, test = df.iloc[:cut].copy(), df.iloc[cut:].copy()
print(f"train {len(train):,} rows ({train.transaction_timestamp.min().date()} -> {train.transaction_timestamp.max().date()}), "
      f"test {len(test):,} ({test.transaction_timestamp.min().date()} -> {test.transaction_timestamp.max().date()})")

# ---------------- 1. Which candidate signals are real? ----------------
rows = []
for col in ["night", "device_anomaly", "location_anomaly", "rapid"]:
    for half, part in [("train", train), ("test", test)]:
        g = part.groupby(col).is_fraud.agg(["size", "mean"])
        if 1 in g.index:
            rows.append(dict(feature=col, split=half, n_flagged=int(g.loc[1, "size"]),
                             rate_flagged_pct=100*g.loc[1, "mean"], rate_unflagged_pct=100*g.loc[0, "mean"]))
pd.DataFrame(rows).to_csv(OUT / "signal_stability_train_vs_test.csv", index=False)

# ---------------- 2. Scorecard ----------------
mu, sd = train.merchant_risk.mean(), train.merchant_risk.std()
def design(d):
    X = d[FEATURES].copy(); X["merchant_risk"] = (X.merchant_risk - mu) / sd
    return X
lr = LogisticRegression(max_iter=1000, C=1.0).fit(design(train), train.is_fraud)
coef = pd.Series(lr.coef_[0], index=FEATURES)
logit_tr = lr.decision_function(design(train))
lo, hi = logit_tr.min(), logit_tr.max()
def to_points(d): return 100 * (lr.decision_function(design(d)) - lo) / (hi - lo)
for d in (train, test, df):
    d["score"] = np.clip(to_points(d), 0, 100)

odds = pd.DataFrame({"feature": FEATURES, "coefficient": coef.values,
                     "odds_ratio": np.exp(coef.values)})
odds.loc[odds.feature == "merchant_risk", "note"] = "per +1 SD of merchant_risk_score"
odds.to_csv(OUT / "scorecard_coefficients.csv", index=False)

# Tiers from TRAIN quantiles -> tiers are populated by construction and stable out-of-time.
q = train.score.quantile([.80, .95, .99]).values
TIERS = ["Low", "Medium", "High", "Critical"]
def tier(s): return pd.cut(s, [-1, q[0], q[1], q[2], 101], labels=TIERS, right=False)
for d in (train, test, df): d["tier"] = tier(d.score)

def tier_table(d):
    g = d.groupby("tier", observed=False).agg(
        transactions=("is_fraud", "size"), fraud=("is_fraud", "sum"),
        value=("amount", "sum"),
        fraud_value=("amount", lambda s: s[d.loc[s.index, "is_fraud"] == 1].sum())).reset_index()
    g["fraud_rate_pct"] = 100 * g.fraud / g.transactions
    g["lift_vs_base"] = g.fraud_rate_pct / (100 * d.is_fraud.mean())
    g["share_of_fraud_pct"] = 100 * g.fraud / g.fraud.sum()
    g["share_of_volume_pct"] = 100 * g.transactions / g.transactions.sum()
    return g
tier_table(test).to_csv(OUT / "scorecard_tiers_test.csv", index=False)
tier_table(train).to_csv(OUT / "scorecard_tiers_train.csv", index=False)

# ---------------- 3. Model comparison on the held-out period ----------------
def boot_ci(y, s, fn, n=300):
    y, s = np.asarray(y), np.asarray(s); vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].sum() == 0: continue
        vals.append(fn(y[i], s[i]))
    return np.percentile(vals, [2.5, 97.5])

gb = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=SEED)
gb_feats = FEATURES + ["hour", "amount", "account_age_days", "age"]
gb.fit(train[gb_feats], train.is_fraud)
models = {
    "Legacy rule score (script 02)": test.legacy_score.values,
    "New logistic scorecard":        test.score.values,
    "Gradient boosting (+hour, amount, tenure, age)": gb.predict_proba(test[gb_feats])[:, 1],
}
# Save test-period predictions so 06_extended_evaluation.py can reuse them
pred = test[["transaction_id", "is_fraud", "amount", "transaction_timestamp"]].copy()
pred["legacy_score"] = test.legacy_score.values
pred["scorecard_points"] = test.score.values
pred["scorecard_prob"] = lr.predict_proba(design(test))[:, 1]
pred["gb_prob"] = models["Gradient boosting (+hour, amount, tenure, age)"]
pred.to_csv(OUT / "test_predictions.csv", index=False)

rows = []
base = test.is_fraud.mean()
for name, s in models.items():
    auc = roc_auc_score(test.is_fraud, s); ap = average_precision_score(test.is_fraud, s)
    a_lo, a_hi = boot_ci(test.is_fraud, s, roc_auc_score)
    top = test.assign(_s=s).sort_values("_s", ascending=False)
    k = int(0.05 * len(top)); cap5 = top.is_fraud.iloc[:k].sum() / top.is_fraud.sum()
    rows.append(dict(model=name, roc_auc=auc, roc_auc_ci_low=a_lo, roc_auc_ci_high=a_hi,
                     pr_auc=ap, pr_auc_vs_base=ap / base, fraud_captured_in_top5pct=cap5,
                     lift_at_top5pct=cap5 / 0.05))
pd.DataFrame(rows).to_csv(OUT / "model_comparison_test.csv", index=False)
print(pd.DataFrame(rows).round(4).to_string(index=False))

# ---------------- 4. Cost-based operating point ----------------
def net_benefit(d, score_col, thr):
    flagged = d[d[score_col] >= thr]
    prevented = DETECTION_RATE * flagged.loc[flagged.is_fraud == 1, "amount"].sum()
    cost = REVIEW_COST_INR * len(flagged)
    return prevented - cost, len(flagged), int(flagged.is_fraud.sum()), prevented

grid = np.arange(0, 101, 1.0)
rows = []
for name, col in [("New scorecard", "score"), ("Legacy rules", "legacy_score")]:
    for thr in grid:
        nb, n, tp, prev = net_benefit(train, col, thr)
        nb_t, n_t, tp_t, prev_t = net_benefit(test, col, thr)
        rows.append(dict(model=name, threshold=thr, train_net_benefit=nb,
                         test_net_benefit=nb_t, test_alerts=n_t, test_tp=tp_t,
                         test_precision=tp_t / n_t if n_t else np.nan,
                         test_recall=tp_t / test.is_fraud.sum(),
                         test_prevented_inr=prev_t, test_review_cost_inr=REVIEW_COST_INR * n_t))
cost = pd.DataFrame(rows); cost.to_csv(OUT / "cost_curve.csv", index=False)

best = {}
for name in cost.model.unique():
    sub = cost[cost.model == name]
    thr = sub.loc[sub.train_net_benefit.idxmax(), "threshold"]      # chosen on TRAIN only
    r = sub[sub.threshold == thr].iloc[0].to_dict(); best[name] = r
pd.DataFrame(best).T.to_csv(OUT / "recommended_operating_point.csv")
total_fraud_test = test.loc[test.is_fraud == 1, "amount"].sum()
summary = {
    "assumptions": {"review_cost_inr": REVIEW_COST_INR, "detection_rate": DETECTION_RATE},
    "test_fraud_value_inr": float(total_fraud_test),
    "operating_points": {k: {kk: float(vv) if isinstance(vv, (int, float, np.floating)) else vv
                             for kk, vv in v.items()} for k, v in best.items()},
    "scaling": {"merchant_mean": float(mu), "merchant_sd": float(sd),
                "z_min_no_intercept": float(lo - lr.intercept_[0]), "z_max_no_intercept": float(hi - lr.intercept_[0])},
    "tier_cutoffs_score": [float(x) for x in q],
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))

# Sensitivity: how does the best threshold move with review cost?
rows = []
for rc in [10, 25, 40, 100, 250, 500]:
    nbs = []
    for thr in grid:
        fl = train[train.score >= thr]
        nbs.append(DETECTION_RATE*fl.loc[fl.is_fraud == 1, "amount"].sum() - rc*len(fl))
    thr = grid[int(np.argmax(nbs))]
    fl = test[test.score >= thr]
    rows.append(dict(review_cost_inr=rc, best_threshold=thr, test_alerts=len(fl),
                     test_alert_rate_pct=100*len(fl)/len(test),
                     test_recall=fl.is_fraud.sum()/test.is_fraud.sum(),
                     test_net_benefit=DETECTION_RATE*fl.loc[fl.is_fraud == 1, "amount"].sum() - rc*len(fl)))
pd.DataFrame(rows).to_csv(OUT / "cost_sensitivity.csv", index=False)

# ---------------- 5. Concentration: merchants & customers ----------------
mg = df.groupby("merchant_id").is_fraud.agg(["size", "sum"])
exp_rate = df.is_fraud.mean()
from scipy.stats import binom
mg["p_value"] = [binom.sf(k - 1, n, exp_rate) for n, k in zip(mg["size"], mg["sum"])]
mg["fraud_rate_pct"] = 100 * mg["sum"] / mg["size"]
m_sig = mg.sort_values("p_value").head(15)
m_sig.to_csv(OUT / "merchants_most_overrepresented.csv")
print("Merchants with p<0.05/2000 (Bonferroni):", int((mg.p_value < 0.05/len(mg)).sum()))

# ---------------- 6. Figures ----------------
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11})
ACC = "#1f4e79"; GRY = "#9aa5b1"; RED = "#c0392b"

# 6a Lift by tier (test)
tt = tier_table(test)
fig, ax = plt.subplots(figsize=(8, 4.8))
bars = ax.bar(tt.tier.astype(str), tt.fraud_rate_pct, color=[GRY, GRY, ACC, RED])
ax.axhline(100*base, ls="--", color="k", lw=1); ax.text(-0.45, 100*base+.12, f"base rate {100*base:.2f}%", ha="left", fontsize=9)
for b, (r, l, s) in zip(bars, zip(tt.fraud_rate_pct, tt.lift_vs_base, tt.share_of_volume_pct)):
    ax.text(b.get_x()+b.get_width()/2, r+.1, f"{r:.1f}%\n{l:.1f}x · {s:.0f}% of volume", ha="center", fontsize=9,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
ax.set_ylabel("Fraud rate (%)"); ax.set_title("Held-out period: fraud rate by scorecard tier"); ax.set_ylim(0, tt.fraud_rate_pct.max()*1.3)
plt.tight_layout(); plt.savefig(FIG / "v2_fraud_rate_by_tier.png", dpi=170); plt.close()

# 6b Cumulative gains
fig, ax = plt.subplots(figsize=(7, 5))
for name, s in models.items():
    o = test.assign(_s=s).sort_values("_s", ascending=False).is_fraud.cumsum().values / test.is_fraud.sum()
    ax.plot(np.arange(1, len(o)+1)/len(o)*100, o*100, label=name,
            lw=2.2 if "scorecard" in name else 1.4)
ax.plot([0, 100], [0, 100], ":", color="k"); ax.set_xlabel("% of transactions reviewed (highest score first)")
ax.set_ylabel("% of fraud captured"); ax.set_title("Cumulative gains, held-out period"); ax.legend(fontsize=8, loc="lower right")
plt.tight_layout(); plt.savefig(FIG / "v2_cumulative_gains.png", dpi=170); plt.close()

# 6c Cost curve
fig, ax = plt.subplots(figsize=(8, 4.8))
for name, col in [("New scorecard", ACC), ("Legacy rules", GRY)]:
    sub = cost[cost.model == name]; ax.plot(sub.threshold, sub.test_net_benefit/1e3, label=name, color=col, lw=2)
    r = best[name]; ax.scatter(r["threshold"], r["test_net_benefit"]/1e3, color=col, zorder=5, s=50)
ax.axhline(0, color="k", lw=.8); ax.set_xlabel("Alert threshold (score)"); ax.set_ylabel("Net benefit on test (₹ thousand)")
ax.set_title(f"Expected net benefit (review cost ₹{REVIEW_COST_INR:.0f}, {int(DETECTION_RATE*100)}% prevention)")
ax.legend(); plt.tight_layout(); plt.savefig(FIG / "v2_cost_curve.png", dpi=170); plt.close()

# 6d Odds ratios
fig, ax = plt.subplots(figsize=(7, 3.6))
o = odds.sort_values("odds_ratio"); ax.barh(o.feature, o.odds_ratio, color=ACC); ax.axvline(1, color="k", lw=1)
for y, v in enumerate(o.odds_ratio): ax.text(v+.03, y, f"{v:.2f}×", va="center")
ax.set_xlabel("Odds ratio (adjusted)"); ax.set_title("What drives the score"); plt.tight_layout()
plt.savefig(FIG / "v2_odds_ratios.png", dpi=170); plt.close()

# 6e Monthly stability of tier lift
mth = df.assign(month=df.transaction_timestamp.dt.to_period("M").astype(str))
tm = mth.groupby(["month", "tier"], observed=False).is_fraud.mean().unstack()*100
tm.to_csv(OUT / "tier_fraud_rate_by_month.csv")

# ---------------- 7. Export refreshed the dashboard table ----------------
export = df[["transaction_id","customer_id","transaction_timestamp","amount","merchant_id","merchant_category",
             "payment_method","device_type","transaction_city","transaction_status","is_fraud","fraud_type",
             "night","device_anomaly","location_anomaly","merchant_risk_score","score","tier"]].rename(
             columns={"night":"night_transaction","score":"risk_score","tier":"risk_category"})
export["risk_score"] = export.risk_score.round(1)
export["is_test_period"] = (df.index >= cut).astype(int)
export.to_csv(OUT / "transactions_scored.csv", index=False)
print("done")
