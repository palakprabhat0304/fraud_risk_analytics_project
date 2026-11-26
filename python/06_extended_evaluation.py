"""
Layer 4: Extended evaluation (run after 05_scorecard_and_cost_analysis.py)

1. Model comparison: PR curves, Precision/Recall@k, FP/FN at equal alert volume, PAIRED bootstrap differences
2. Calibration of predicted probabilities
3. Explainability: points breakdown + worked examples
4. Time stability: monthly AUC / precision / recall / capture, feature drift (PSI)
5. Operational impact of false alerts
"""
from pathlib import Path
import json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve

ROOT = Path(__file__).resolve().parents[1]
V2, FIG = ROOT/"outputs"/"v2", ROOT/"outputs"/"figures"
rng = np.random.default_rng(42)
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11})
ACC, GRY, RED, ORG = "#1f4e79", "#9aa5b1", "#c0392b", "#d98e04"

pred = pd.read_csv(V2/"test_predictions.csv", parse_dates=["transaction_timestamp"])
full = pd.read_csv(V2/"transactions_scored.csv", parse_dates=["transaction_timestamp"])
summ = json.loads((V2/"summary.json").read_text())
coef = pd.read_csv(V2/"scorecard_coefficients.csv").set_index("feature").coefficient
THR = summ["operating_points"]["New scorecard"]["threshold"]
y = pred.is_fraud.values
M = {"Legacy rules": pred.legacy_score.values, "Logistic scorecard": pred.scorecard_points.values,
     "Gradient boosting": pred.gb_prob.values}

# ---------- 1. Comparison ----------
def topk(y, s, frac):
    k = int(frac*len(y)); idx = np.argsort(-s, kind="stable")[:k]
    tp = y[idx].sum(); return tp/k, tp/y.sum(), k-tp, y.sum()-tp, k
rows = []
for name, s in M.items():
    for frac in [.01, .05, .10]:
        p, r, fp, fn, k = topk(y, s, frac)
        rows.append(dict(model=name, alert_budget=f"top {int(frac*100)}%", alerts=k,
                         precision=p, recall=r, false_positives=int(fp), false_negatives=int(fn),
                         false_alerts_per_fraud_caught=fp/max(k-fp, 1)))
pd.DataFrame(rows).to_csv(V2/"precision_recall_at_k.csv", index=False)

# Paired bootstrap: same resampled rows for every model -> CI on the DIFFERENCE
names = list(M); B = 500; diffs = {(a, b): {"auc": [], "ap": []}
                                  for a, b in [("Logistic scorecard", "Gradient boosting"),
                                               ("Logistic scorecard", "Legacy rules")]}
for _ in range(B):
    i = rng.integers(0, len(y), len(y)); yi = y[i]
    if yi.sum() == 0: continue
    sc = {n: (roc_auc_score(yi, M[n][i]), average_precision_score(yi, M[n][i])) for n in names}
    for (a, b) in diffs:
        diffs[(a, b)]["auc"].append(sc[a][0]-sc[b][0]); diffs[(a, b)]["ap"].append(sc[a][1]-sc[b][1])
rows = []
for (a, b), d in diffs.items():
    for m in ["auc", "ap"]:
        v = np.array(d[m]); lo, hi = np.percentile(v, [2.5, 97.5])
        rows.append(dict(comparison=f"{a} - {b}", metric="ROC-AUC" if m == "auc" else "PR-AUC",
                         mean_difference=v.mean(), ci_low=lo, ci_high=hi,
                         conclusion="difference not distinguishable from zero" if lo <= 0 <= hi else "difference is reliable"))
paired = pd.DataFrame(rows); paired.to_csv(V2/"paired_bootstrap_differences.csv", index=False)
print(paired.round(4).to_string(index=False))

fig, ax = plt.subplots(figsize=(7, 5))
for (n, s), c in zip(M.items(), [GRY, ACC, ORG]):
    p, r, _ = precision_recall_curve(y, s); ax.plot(r, p, color=c, lw=2, label=f"{n} (AP {average_precision_score(y, s):.3f})")
ax.axhline(y.mean(), ls=":", color="k"); ax.text(.98, y.mean()+.002, "no-skill = base rate", ha="right", fontsize=9)
ax.set_xlabel("Recall"); ax.set_ylabel("Precision"); ax.set_ylim(0, .15); ax.legend(fontsize=9)
ax.set_title("Precision-recall curve, held-out period"); plt.tight_layout(); plt.savefig(FIG/"v2_precision_recall.png", dpi=170); plt.close()

# ---------- 2. Calibration ----------
fig, ax = plt.subplots(figsize=(6, 5)); rows = []
for name, col, c in [("Logistic scorecard", "scorecard_prob", ACC), ("Gradient boosting", "gb_prob", ORG)]:
    d = pred.assign(bin=pd.qcut(pred[col], 10, duplicates="drop"))
    g = d.groupby("bin", observed=True).agg(pred=(col, "mean"), obs=("is_fraud", "mean"), n=("is_fraud", "size")).reset_index(drop=True)
    g.insert(0, "model", name); rows.append(g); ax.plot(g.pred*100, g.obs*100, "o-", color=c, label=name)
mx = max(r_.pred.max() for r_ in rows)*100; ax.plot([0, mx], [0, mx], ":", color="k", label="perfect")
ax.set_xlabel("Mean predicted fraud probability (%)"); ax.set_ylabel("Observed fraud rate (%)"); ax.legend()
ax.set_title("Calibration by decile, held-out period"); plt.tight_layout(); plt.savefig(FIG/"v2_calibration.png", dpi=170); plt.close()
cal = pd.concat(rows); cal.to_csv(V2/"calibration_deciles.csv", index=False)
brier = {n: float(np.mean((pred[c]-y)**2)) for n, c in [("scorecard", "scorecard_prob"), ("gb", "gb_prob")]}
brier["base_rate_only"] = float(np.mean((y.mean()-y)**2)); print("Brier", brier)

# ---------- 3. Explainability ----------
sc = summ["scaling"]; span = sc["z_max_no_intercept"]-sc["z_min_no_intercept"]
pts = lambda b: 100*b/span
base_pts = pts(-sc["z_min_no_intercept"])
def breakdown(night, dev, loc, mr):
    return {"Baseline": base_pts, "Night": pts(coef["night"])*night, "Device anomaly": pts(coef["device_anomaly"])*dev,
            "Location anomaly": pts(coef["location_anomaly"])*loc,
            "Merchant risk": pts(coef["merchant_risk"])*(mr-sc["merchant_mean"])/sc["merchant_sd"]}
ex = {"A: routine grocery purchase\n(day, usual device, home city, mr 0.08)": (0, 0, 0, .08),
      "B: 1am, new device, home city\n(mr 0.25)": (1, 1, 0, .25),
      "C: 2am, new city, new device\njewellery (mr 0.40)": (1, 1, 1, .40)}
rows = []; fig, ax = plt.subplots(figsize=(9, 4.6)); cols = {"Baseline": GRY, "Night": ACC, "Device anomaly": ORG,
                                                          "Location anomaly": RED, "Merchant risk": "#5b8c5a"}
for yy, (label, args) in enumerate(ex.items()):
    b = breakdown(*args); left = 0
    for k, v in b.items():
        ax.barh(yy, v, left=left, color=cols[k], label=k if yy == 0 else None); left += v
    tot = sum(b.values()); tier = "Critical" if tot >= summ["tier_cutoffs_score"][2] else "High" if tot >= summ["tier_cutoffs_score"][1] else "Medium" if tot >= summ["tier_cutoffs_score"][0] else "Low"
    ax.text(max(left, base_pts)+1, yy, f"{tot:.0f} pts · {tier}", va="center", fontweight="bold")
    rows.append(dict(example=label.replace("\n", " "), **{k: round(v, 1) for k, v in b.items()}, total_points=round(tot, 1), tier=tier))
ax.axvline(THR, ls="--", color="k", lw=1); ax.text(THR+.5, 2.45, f"alert threshold {THR:.0f}", fontsize=9)
ax.set_yticks(range(3)); ax.set_yticklabels(list(ex)); ax.invert_yaxis(); ax.set_xlim(0, 110); ax.set_xlabel("Risk points (0-100)")
ax.legend(ncol=5, fontsize=8, loc="upper center", bbox_to_anchor=(.5, -.18)); ax.set_title("How the scorecard builds a risk score")
plt.tight_layout(); plt.savefig(FIG/"v2_score_breakdown.png", dpi=170); plt.close()
pd.DataFrame(rows).to_csv(V2/"worked_examples.csv", index=False)
pd.DataFrame([{"feature": k, "points_when_present": round(pts(coef[k]), 1)} for k in ["night", "device_anomaly", "location_anomaly"]] +
             [{"feature": "merchant_risk (per +1 SD)", "points_when_present": round(pts(coef["merchant_risk"]), 1)}]
             ).to_csv(V2/"points_per_feature.csv", index=False)

# ---------- 4. Time stability ----------
full["month"] = full.transaction_timestamp.dt.to_period("M").astype(str)
full["alert"] = full.risk_score >= THR
# Group by month AND split, so April (which straddles the 2026-04-19 00:50 train/test cut) is reported as two rows.
rows = []
for (mth, is_te), g in full.groupby(["month", "is_test_period"]):
    top = g.sort_values("risk_score", ascending=False).head(int(.05*len(g)))
    rows.append(dict(month=mth, split="test" if is_te else "train", period=f"{mth} ({'test' if is_te else 'train'})",
                     transactions=len(g), fraud=int(g.is_fraud.sum()), fraud_rate_pct=100*g.is_fraud.mean(),
                     roc_auc=roc_auc_score(g.is_fraud, g.risk_score),
                     alert_rate_pct=100*g.alert.mean(),
                     precision_at_threshold=g.loc[g.alert, "is_fraud"].mean(),
                     recall_at_threshold=g.loc[g.alert, "is_fraud"].sum()/g.is_fraud.sum(),
                     fraud_captured_top5pct=top.is_fraud.sum()/g.is_fraud.sum()))
mon = pd.DataFrame(rows); mon.to_csv(V2/"monthly_performance.csv", index=False); print(mon.round(3).to_string(index=False))
fig, axs = plt.subplots(1, 3, figsize=(14, 3.9)); x = np.arange(len(mon)); te = (mon.split == "test").values
for ax, col, ttl in zip(axs, ["roc_auc", "precision_at_threshold", "fraud_captured_top5pct"],
                        ["ROC-AUC", f"Precision (score >= {THR:.0f})", "Share of fraud in top 5% by score"]):
    ax.plot(x, mon[col], "-", color=GRY, lw=1.5)
    ax.scatter(x[~te], mon[col][~te], facecolors="white", edgecolors=ACC, s=40, zorder=3, label="train (in-sample)")
    ax.scatter(x[te], mon[col][te], color=ACC, s=40, zorder=3, label="test (out-of-sample)")
    ax.set_title(ttl, fontsize=11); ax.set_xticks(x); ax.set_xticklabels([m[2:] + ("*" if t else "") for m, t in zip(mon.month, te)], rotation=70, fontsize=8)
axs[0].legend(fontsize=8); fig.text(.5, -.02, "Apr 2026 is split at 19 Apr 00:50 (train before, test after); * = out-of-sample. Split months have fewer transactions, so their points are noisier.", ha="center", fontsize=8)
plt.tight_layout(); plt.savefig(FIG/"v2_monthly_stability.png", dpi=170, bbox_inches="tight"); plt.close()

# Drift: train vs test feature distributions (PSI) -- <0.1 stable, 0.1-0.25 moderate, >0.25 major
def psi(a, b, bins=10):
    e = np.unique(np.quantile(a, np.linspace(0, 1, bins+1))); e[0], e[-1] = -np.inf, np.inf
    pa = np.histogram(a, e)[0]/len(a); pb = np.histogram(b, e)[0]/len(b); pa, pb = np.clip(pa, 1e-4, None), np.clip(pb, 1e-4, None)
    return float(np.sum((pb-pa)*np.log(pb/pa)))
tr, te = full[full.is_test_period == 0], full[full.is_test_period == 1]
rows = []
for c in ["risk_score", "merchant_risk_score", "amount"]:
    rows.append(dict(feature=c, train_mean=tr[c].mean(), test_mean=te[c].mean(), psi=psi(tr[c].values, te[c].values)))
for c in ["night_transaction", "device_anomaly", "location_anomaly"]:
    a, b = tr[c].mean(), te[c].mean()
    rows.append(dict(feature=c, train_mean=a, test_mean=b, psi=float((b-a)*np.log((b/a)) + ((1-b)-(1-a))*np.log((1-b)/(1-a)))))
drift = pd.DataFrame(rows); drift["status"] = pd.cut(drift.psi, [-1, .1, .25, 9], labels=["stable", "moderate shift", "major shift"])
drift.to_csv(V2/"feature_drift_psi.csv", index=False); print(drift.round(4).to_string(index=False))

# ---------- 5. Operational impact of alerts ----------
al = pred[pred.scorecard_points >= THR]; days = (pred.transaction_timestamp.max()-pred.transaction_timestamp.min()).days+1
tp = int(al.is_fraud.sum()); fp = len(al)-tp
imp = {"test_days": days, "alerts": len(al), "alerts_per_day": len(al)/days, "true_fraud_alerts": tp,
       "false_alerts": fp, "false_alerts_per_fraud_caught": fp/tp, "false_alert_share_pct": 100*fp/len(al),
       "legit_transactions_challenged_pct": 100*fp/(pred.is_fraud == 0).sum(),
       "fraud_missed": int(y.sum()-tp), "fraud_value_missed_inr": float(pred.loc[(pred.scorecard_points < THR) & (pred.is_fraud == 1), "amount"].sum()),
       "estimated_net_benefit_inr_ASSUMPTION_BASED": summ["operating_points"]["New scorecard"]["test_net_benefit"]}
(V2/"operational_impact.json").write_text(json.dumps(imp, indent=2)); print(json.dumps(imp, indent=2))
