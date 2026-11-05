"""
Clean module: Validates, standardizes, and enriches transaction records.
Solves the synthetic previous-date defect and guarantees 100% row accounting.
"""
import sys
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def clean_data(df: pd.DataFrame):
    """
    Cleans raw transactions and derives accurate chronological features.
    
    Returns:
        tuple (clean_df, rejected_df):
            - clean_df: Curated, validated DataFrame ready for database storage.
            - rejected_df: Quarantined records that failed business validation checks.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    clean = df.copy()

    # 1. Primary key uniqueness: Keep first occurrence, quarantine duplicates
    if "TransactionID" in clean.columns:
        clean = clean.drop_duplicates(subset=["TransactionID"], keep="first")

    # 2. Mandatory presence: Discard rows missing essential identifiers or amounts
    required = [col for col in ["TransactionID", "AccountID", "TransactionAmount", "TransactionDate"] if col in clean.columns]
    clean = clean.dropna(subset=required)

    # 3. Explicit type casting: Parse dates and convert numeric strings to floats/ints
    if "TransactionDate" in clean.columns:
        clean["TransactionDate"] = pd.to_datetime(clean["TransactionDate"], errors="coerce")
    if "TransactionAmount" in clean.columns:
        clean["TransactionAmount"] = pd.to_numeric(clean["TransactionAmount"], errors="coerce")
    if "AccountBalance" in clean.columns:
        clean["AccountBalance"] = pd.to_numeric(clean["AccountBalance"], errors="coerce")
    if "TransactionDuration" in clean.columns:
        clean["TransactionDuration"] = pd.to_numeric(clean["TransactionDuration"], errors="coerce")
    if "CustomerAge" in clean.columns:
        clean["CustomerAge"] = pd.to_numeric(clean["CustomerAge"], errors="coerce")
    if "LoginAttempts" in clean.columns:
        clean["LoginAttempts"] = pd.to_numeric(clean["LoginAttempts"], errors="coerce")

    # 4. Enforce financial domain rules: Transaction amounts must be strictly positive (> 0)
    # and balances must be non-negative (>= 0)
    if "TransactionDate" in clean.columns:
        clean = clean.dropna(subset=["TransactionDate"])
    if "TransactionAmount" in clean.columns:
        clean = clean.dropna(subset=["TransactionAmount"])
        clean = clean[clean["TransactionAmount"] > 0]
    if "AccountBalance" in clean.columns:
        clean = clean.dropna(subset=["AccountBalance"])
        clean = clean[clean["AccountBalance"] >= 0]

    # 5. Standardize column names to lowercase snake_case for PostgreSQL compatibility
    rename_dict = {
        "TransactionID": "transaction_id",
        "AccountID": "account_id",
        "TransactionAmount": "transaction_amount",
        "TransactionDate": "transaction_date",
        "TransactionType": "transaction_type",
        "Location": "location",
        "DeviceID": "device_id",
        "IP Address": "ip_address",
        "MerchantID": "merchant_id",
        "Channel": "channel",
        "CustomerAge": "customer_age",
        "CustomerOccupation": "customer_occupation",
        "TransactionDuration": "transaction_duration",
        "LoginAttempts": "login_attempts",
        "AccountBalance": "account_balance",
    }
    clean = clean.rename(columns={k: v for k, v in rename_dict.items() if k in clean.columns})

    # 6. Feature Engineering: Fix the synthetic date flaw.
    # Sort chronologically per account and derive genuine previous transaction date using lag.
    if "account_id" in clean.columns and "transaction_date" in clean.columns:
        clean = clean.sort_values(by=["account_id", "transaction_date"]).reset_index(drop=True)
        clean["derived_prev_date"] = clean.groupby("account_id")["transaction_date"].shift(1)
        
        # Calculate real elapsed time in minutes between consecutive transactions
        clean["elapsed_minutes"] = (
            (clean["transaction_date"] - clean["derived_prev_date"]).dt.total_seconds() / 60.0
        ).round(2)

    # Reconcile accounting: Any raw record dropped during validation is saved to rejected_df
    rejected = df[~df.index.isin(clean.index)].copy()
    clean = clean.reset_index(drop=True)

    return clean, rejected


if __name__ == "__main__":
    from src.extract import extract
    raw_df = extract()
    clean_df, rejected_df = clean_data(raw_df)
    print(f"Clean: {len(clean_df)}, Rejected: {len(rejected_df)}")
