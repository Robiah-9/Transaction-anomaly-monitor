# Data Dictionary & Schema Documentation
**Project:** Explainable Transaction Anomaly Monitoring System  
**Dataset:** `Bank Transaction Data.csv` (2,512 rows, 16 columns)  
**Profile Date:** 2026-10-28  

---

## 1. Schema & Field Summary

| Column Name | Inferred Type | Null Count | Unique Values | Range / Sample Values | Semantic Meaning & Feature Relevance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TransactionID` | String | 0 (0%) | 2,512 | `TX000001` - `TX002512` | Primary key identifier. Must be unique and non-null. Not used directly in model math. |
| `AccountID` | String | 0 (0%) | 495 | `AC00001` - `AC00495` | Account grouping key. Used to calculate per-account spending baselines and frequency. |
| `TransactionAmount` | Float | 0 (0%) | 2,429 | \$0.26 - \$1,919.11 (Median: \$211.14) | Core monitoring feature. Key indicator of sudden expenditure spikes. |
| `TransactionDate` | Datetime | 0 (0%) | 2,498 | 2023-01-02 16:00 to 2024-01-01 18:21 | Primary event timestamp. Used for chronological ordering and velocity features. |
| `TransactionType` | String | 0 (0%) | 2 | `Debit` (1,944), `Credit` (568) | Categorical payment type. Peer-group baseline segmentation. |
| `Location` | String | 0 (0%) | 20 | Denver, Atlanta, Dallas, etc. | Geographical location. Rapid city hopping within small time windows signals anomaly. |
| `DeviceID` | String | 0 (0%) | 681 | `D000001` - `D000681` | Device fingerprint. Signals novel device usage for an account. |
| `IP Address` | String | 0 (0%) | 592 | IPv4 addresses | Network context. Signals novel IP access; masked in analyst UI for privacy. |
| `MerchantID` | String | 0 (0%) | 100 | `M001` - `M100` | Merchant category/identifier context. |
| `Channel` | String | 0 (0%) | 3 | `Branch` (868), `ATM` (833), `Online` (811) | Access channel. Used for peer comparison and channel-specific rules. |
| `CustomerAge` | Integer | 0 (0%) | 63 | 18 - 80 (Median: 45) | Demographic context. Avoid using as risk penalty (fairness principle). |
| `CustomerOccupation`| String | 0 (0%) | 4 | Student (657), Doctor (631), Engineer (625), Retired (599) | Demographic context for peer clustering. |
| `TransactionDuration`| Integer | 0 (0%) | 288 | 10s - 300s (Median: 112.5s) | Time taken to complete transaction in seconds. |
| `LoginAttempts` | Integer | 0 (0%) | 5 | 1 (95.1%), 2 (1.1%), 3 (1.2%), 4 (1.3%), 5 (1.3%) | Failed/total authentication attempts prior to transaction. Strong risk multiplier. |
| `AccountBalance` | Float | 0 (0%) | 2,492 | \$101.25 - \$14,977.99 (Median: \$4,735.51) | Balance at or after transaction. Helps detect balance drain attempts. |
| `PreviousTransactionDate`| Datetime | 0 (0%) | 7 | 2024-11-04 08:06 to 2024-11-04 08:12 | **CRITICAL DEFECT IN SOURCE DATA** (See Section 2). |

---

## 2. Key Discovery: The `PreviousTransactionDate` Defect

During exploratory data profiling, we evaluated the chronological validity of `PreviousTransactionDate` relative to `TransactionDate`:
- **Finding:** In 100% of rows (2,512 / 2,512), `PreviousTransactionDate` is clustered within a 6-minute window on **November 4, 2024**, while `TransactionDate` spans **January 2023 through January 2024**.
- **Root Cause:** A synthetic data generator artefact where the previous transaction column was populated with current run timestamps during CSV creation.
- **Architectural Solution:**
  1. **Do not use raw `PreviousTransactionDate` for elapsed time or velocity calculation.**
  2. Compute **true chronological previous dates** within SQL / Pandas using:
     ```sql
     LAG(transaction_date) OVER (PARTITION BY account_id ORDER BY transaction_date ASC) AS derived_prev_txn_date
     ```
  3. Calculate `elapsed_minutes = (transaction_date - derived_prev_txn_date) / 60`.
  4. For the first transaction of an account (`derived_prev_txn_date IS NULL`), flag as `INITIAL_ACCOUNT_TRANSACTION` with neutral velocity.

---

## 3. Account History Depth

- **Total Accounts:** 495
- **Transactions per Account:**
  - 1 transaction: 24 accounts (4.8%)
  - 2 transactions: 43 accounts (8.7%)
  - 3–7 transactions: 356 accounts (71.9%)
  - 8–12 transactions: 72 accounts (14.5%)
- **Handling Sparse History:** For accounts with $< 3$ transactions, per-account standard deviation cannot be reliably calculated. The scoring layer will dynamically fall back to **Channel/Type peer baselines** (`AmountPeerDeviation`).

---

## 4. Agreed Day 1 Scope & Architecture Freeze

1. **Ingestion Layer:** Raw CSV $\rightarrow$ PostgreSQL `raw_transactions` table preserving exact inputs + batch metadata.
2. **Validation Layer:** Check identifier integrity, parse dates, quarantine invalid records into `rejected_records`.
3. **Feature Layer:** Chronological windowing for `derived_prev_txn_date`, account spending baselines, novel device/IP flags, and high login attempt triggers.
4. **Scoring Engine:** Deterministic rule-based anomaly scoring with explainable reason codes + optional unsupervised Isolation Forest baseline.
5. **Presentation Layer:** Streamlit triage dashboard for operational analysts with privacy masking for sensitive identifiers.
