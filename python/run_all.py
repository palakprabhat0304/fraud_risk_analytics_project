"""Run the whole Python pipeline in order.  Usage: python python/run_all.py"""
import subprocess, sys
from pathlib import Path
here = Path(__file__).parent
for script in ["02_eda_and_statistics.py", "03_ml_benchmark.py",
               "04_create_business_report_tables.py", "05_scorecard_and_cost_analysis.py", "06_extended_evaluation.py", "07_build_dashboard.py"]:
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable, str(here / script)], check=True)
