# Transaction Anomaly Monitor

A portfolio data engineering project by Robiah.

I built this end-to-end pipeline to solve a real-world problem in financial data: how to detect and flag suspicious transactions when you don't have confirmed fraud labels to train a supervised machine learning model.

Rather than building a black-box model with fabricated accuracy scores, I built a reliable, explainable transaction monitoring system using **Python, PostgreSQL, and Streamlit**.

---

## What I Built

Here is what I did across the entire pipeline:

### 1. Data Ingestion (`src/extract.py`)
- Extracted 2,512 raw transactions from CSV.
- Loaded values as strings first to prevent premature type conversion and preserve formatting.
- Added defensive validation checks to ensure the file exists, isn't empty, and has all required columns before passing it down the pipeline.

### 2. Cleaning & Feature Engineering (`src/clean.py`)
- Cleaned the data: parsed timestamps, cast numeric types, removed duplicate transaction IDs, and enforced domain rules (amounts must be greater than $0, account balances cannot be negative).
- Guaranteed full accounting reconciliation: clean records are separated from quarantined/invalid rows so no data is silently dropped.
- **Fixed a critical data defect:** (See details below).

### 3. Database Persistence (`src/load.py`)
- Created relational tables in a local PostgreSQL database (`sentinel`).
- Loaded validated records into `curated_transactions`.
- Set up an audit table (`rejected_records`) to quarantine any malformed records with explicit failure reasons.

### 4. Explainable Anomaly Detection (`src/score.py`)
- Instead of using a black box, I built a transparent scoring engine with three behavioral rules:
  1. **Amount Spike (`AMOUNT_SPIKE`)**: Flags transactions where the amount is more than 2.5x the account's historical average spending (minimum $100).
  2. **Rapid Velocity (`RAPID_SUCCESSION`)**: Flags transactions that occur less than 5 minutes after the account's previous transaction.
  3. **High Login Attempts (`FAILED_LOGIN_SPIKE`)**: Flags transactions where 3 or more authentication attempts were made beforehand.
- Assigned severity tiers based on how many signals fired:
  - **Low**: 1 rule triggered.
  - **Medium**: 2 rules triggered at the same time.
  - **High**: 3 rules triggered simultaneously.
- Stored all 253 review candidates in the `transaction_alerts` table in PostgreSQL.

### 5. Review Dashboard (`app/dashboard.py`)
- Built an interactive web app using Streamlit for compliance/risk analysts.
- Shows total transactions, total flagged alerts, and priority breakdown.
- Allows filtering by severity (`LOW`, `MEDIUM`) and channel (`Online`, `Branch`, `ATM`).
- Added an inspector drawer so an analyst can select any transaction and view the exact reasons why it was flagged.

### 6. Automated Testing (`tests/`)
- Wrote 15 automated unit tests with `pytest` covering edge cases: empty files, negative amounts, duplicate IDs, exact elapsed-time math, and database insertions.
- All 15 tests pass with 100% success rate.

---

## A Data Flaw I Discovered & Fixed

While doing exploratory data profiling on the dataset, I noticed a major flaw in the raw data:

In 100% of the rows, `PreviousTransactionDate` was clustered within a 6-minute window on **November 4, 2024**, while `TransactionDate` was in **2023**. Subtracting them produced negative time differences of $-11$ to $-22$ months.

**How I resolved it:**
In `src/clean.py`, I ignored the broken column and derived the real previous transaction date by sorting transactions chronologically per account and using a lag function:

$$\text{derived\_prev\_date} = \text{LAG}(\text{transaction\_date}) \text{ OVER (PARTITION BY account\_id ORDER BY transaction\_date)}$$
$$\text{elapsed\_minutes} = \frac{\text{transaction\_date} - \text{derived\_prev\_date}}{60}$$

If an account has no prior transaction, `elapsed_minutes` cleanly evaluates to `NaN` (first-time transaction).

---

## Pipeline Results

When I ran the full pipeline (`python src/main.py`), here are the exact results:

- **Total Raw Records Processed:** 2,512
- **Clean Curated Records Loaded:** 2,512
- **Quarantined Records:** 0
- **Alerts Flagged:** 253 (~10.1% of transactions)
  - **Low Severity (1 signal):** 250 transactions
  - **Medium Severity (2 signals):** 3 transactions
  - **High Severity (3 signals):** 0 transactions
- **Test Suite:** 15 passing tests (`pytest -v`)

---

## Future Additions

Here is what I plan to add next to expand the system:

1. **Docker Containerization**: Add a `docker-compose.yml` file to package Python, PostgreSQL, and Streamlit into portable containers that run with a single `docker compose up` command.
2. **Orchestration with Apache Airflow**: Build a scheduled DAG to automate the extract-clean-load-score workflow on a daily or hourly cadence with automatic retries and alerts.
3. **Real-Time Streaming**: Introduce Apache Kafka or Redpanda to simulate incoming live transactions instead of processing batch CSV files.
4. **Unsupervised ML Model Comparison**: Implement an Isolation Forest model alongside the rules engine as a secondary signal to compare rule-based ranking versus cluster-based outliers.
5. **REST API**: Add a FastAPI service so external applications can send a transaction payload and receive instant risk scores and reason codes.

---

## How to Run This Project Locally

### 1. Clone the repo and install dependencies
```bash
git clone https://github.com/Robiah-9/Transaction-anomaly-monitor.git
cd Transaction-anomaly-monitor
pip install -r requirements.txt
```

### 2. Configure your database
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/sentinel
```

### 3. Run the pipeline
Executes extraction, cleaning, PostgreSQL loading, and anomaly scoring in one command:
```bash
python src/main.py
```

### 4. Launch the Streamlit dashboard
```bash
streamlit run app/dashboard.py
```

### 5. Run the tests
```bash
pytest -v
```
