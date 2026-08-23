"""
Creates concise CSV tables that can be used directly in the final report.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

required = [
    "core_kpis.csv",
    "fraud_by_merchant_category.csv",
    "fraud_by_risk_category.csv",
    "statistical_tests.csv",
    "behaviour_effect_sizes.csv",
    "risk_score_validation.csv"
]

missing = [x for x in required if not (OUT/x).exists()]
if missing:
    raise FileNotFoundError(
        "Run 02_eda_and_statistics.py first. Missing: " + ", ".join(missing)
    )

# Create a single summary workbook-like collection as separate CSVs.
# Keep CSV output for portability.
kpis = pd.read_csv(OUT/"core_kpis.csv")
risk = pd.read_csv(OUT/"fraud_by_risk_category.csv")
stats = pd.read_csv(OUT/"statistical_tests.csv")
effects = pd.read_csv(OUT/"behaviour_effect_sizes.csv")
validation = pd.read_csv(OUT/"risk_score_validation.csv")

# Automatically identify statistically significant behavioural factors.
sig = stats[
    (stats["feature"] != "transaction_amount_mann_whitney_u")
    & (stats["significant_at_0_05"])
].copy()

sig.to_csv(OUT/"significant_behavioural_factors.csv", index=False)

# Top risk categories.
risk.sort_values("fraud_rate_pct", ascending=False).to_csv(
    OUT/"risk_categories_for_report.csv", index=False
)

print("Business report tables prepared.")
