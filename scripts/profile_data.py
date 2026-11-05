import pandas as pd
import numpy as np
import json

def profile():
    csv_path = 'Bank Transaction Data.csv'
    df = pd.read_csv(csv_path)

    print("=== 1. SHAPE & COLUMNS ===")
    print(f"Total Rows: {df.shape[0]}, Total Columns: {df.shape[1]}")
    print("Columns:", list(df.columns))

    print("\n=== 2. DATA TYPES & NULL VALUES ===")
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df)) * 100
    types = df.dtypes
    summary_df = pd.DataFrame({'Type': types, 'NullCount': null_counts, 'NullPct': null_pct})
    print(summary_df.to_string())

    print("\n=== 3. IDENTIFIERS & UNIQUENESS ===")
    print(f"Unique TransactionIDs: {df['TransactionID'].nunique()} (Total rows: {len(df)})")
    print(f"Unique Accounts: {df['AccountID'].nunique()}")
    print(f"Unique Devices: {df['DeviceID'].nunique()}")
    print(f"Unique IPs: {df['IP Address'].nunique()}")
    print(f"Unique Merchants: {df['MerchantID'].nunique()}")

    acc_dist = df['AccountID'].value_counts()
    print("\nAccount Transaction Counts Distribution:")
    print(acc_dist.value_counts().sort_index().to_dict())
    print("Account transaction stats:")
    print(f"Min: {acc_dist.min()}, Max: {acc_dist.max()}, Median: {acc_dist.median()}, Mean: {acc_dist.mean():.2f}")

    print("\n=== 4. NUMERIC FIELDS STATS ===")
    num_cols = ['TransactionAmount', 'AccountBalance', 'TransactionDuration', 'LoginAttempts', 'CustomerAge']
    print(df[num_cols].describe().T[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']].to_string())

    print("\n=== 5. DATE COLUMNS INSPECTION ===")
    df['parsed_txn_date'] = pd.to_datetime(df['TransactionDate'], errors='coerce')
    df['parsed_prev_date'] = pd.to_datetime(df['PreviousTransactionDate'], errors='coerce')
    print(f"Unparsed TransactionDates: {df['parsed_txn_date'].isna().sum()}")
    print(f"Unparsed PreviousTransactionDates: {df['parsed_prev_date'].isna().sum()}")
    print(f"TransactionDate span: {df['parsed_txn_date'].min()} --> {df['parsed_txn_date'].max()}")
    print(f"PreviousTransactionDate span: {df['parsed_prev_date'].min()} --> {df['parsed_prev_date'].max()}")

    # Compare dates
    valid_dates = df.dropna(subset=['parsed_txn_date', 'parsed_prev_date']).copy()
    diff_minutes = (valid_dates['parsed_txn_date'] - valid_dates['parsed_prev_date']).dt.total_seconds() / 60.0
    print(f"\nDate Comparison (TransactionDate - PreviousTransactionDate):")
    print(f"Negative (Previous > Current): {(diff_minutes < 0).sum()} ({(diff_minutes < 0).mean()*100:.2f}%)")
    print(f"Zero (Previous == Current): {(diff_minutes == 0).sum()}")
    print(f"Positive (Previous < Current): {(diff_minutes > 0).sum()} ({(diff_minutes > 0).mean()*100:.2f}%)")

    print("\nSample rows with Negative Date Difference (PreviousTransactionDate in the future relative to TransactionDate):")
    neg_sample = df[diff_minutes < 0][['TransactionID', 'AccountID', 'TransactionDate', 'PreviousTransactionDate']].head(5)
    print(neg_sample.to_string())

    print("\n=== 6. CATEGORICAL DISTRIBUTIONS ===")
    for col in ['TransactionType', 'Channel', 'LoginAttempts', 'CustomerOccupation']:
        print(f"\nValue counts for {col}:")
        print(df[col].value_counts().to_dict())

if __name__ == '__main__':
    profile()
