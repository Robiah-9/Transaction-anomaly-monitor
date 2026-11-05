"""
Main module: Orchestrates the complete pipeline run.
Flow: Extract (CSV) -> Clean (Validation & Features) -> Load (PostgreSQL) -> Score (Anomaly Detection).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.extract import extract
from src.clean import clean_data
from src.load import load_data
from src.score import score_transactions, save_alerts


def run_pipeline():
    """
    Executes the complete end-to-end transaction monitoring pipeline.
    Returns summary dictionary with row and alert counts.
    """
    raw_df = extract()
    clean_df, rejected_df = clean_data(raw_df)
    load_data(clean_df, rejected_df)
    alerts_df = score_transactions(clean_df)
    save_alerts(alerts_df)
    return {
        "raw_count": len(raw_df),
        "clean_count": len(clean_df),
        "rejected_count": len(rejected_df),
        "alerts_count": len(alerts_df),
    }


if __name__ == "__main__":
    results = run_pipeline()
    print(results)
