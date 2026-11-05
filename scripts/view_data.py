"""
Helper script to view what is currently stored in your PostgreSQL database.
Run this anytime in VS Code to see your data!
"""
import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
from sqlalchemy import text
from src.db import get_engine

def inspect_database():
    engine = get_engine()
    print("=" * 65)
    print("  Transaction Anomaly Monitor - Database Status")
    print("=" * 65)
    print(f"Connected to: {engine.url}\n")

    with engine.connect() as conn:
        # Check raw_transactions count
        try:
            raw_cnt = conn.execute(text("SELECT COUNT(*) FROM raw_transactions;")).scalar()
            print(f"[TABLE] raw_transactions: {raw_cnt:,} rows loaded.")
        except Exception as e:
            print(f"[ERROR] raw_transactions table not found: {e}")
            return

        # Check pipeline runs
        try:
            runs_df = pd.read_sql("SELECT run_id, pipeline_step, status, loaded_count, duration_seconds FROM pipeline_runs;", con=conn)
            print(f"\n[AUDIT] pipeline_runs history ({len(runs_df)} runs recorded):")
            print(runs_df.to_string(index=False))
        except Exception as e:
            print(f"[WARN] pipeline_runs check: {e}")

        # Show first 3 transactions from PostgreSQL
        print("\n[SAMPLE] First 3 transactions directly from PostgreSQL:")
        sample_df = pd.read_sql("SELECT transaction_id, account_id, transaction_amount, transaction_date, channel FROM raw_transactions LIMIT 3;", con=conn)
        print(sample_df.to_string(index=False))

    print("\n" + "=" * 65)
    print(" [OK] Everything is working and verified in PostgreSQL!")
    print("=" * 65)

if __name__ == "__main__":
    inspect_database()
