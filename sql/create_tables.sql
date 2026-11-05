-- Transaction Anomaly Monitoring Database Schema DDL (ETL Pipeline)
-- PostgreSQL & ANSI SQL Compatible

-- 1. Pipeline Execution Tracking (Audit Log)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    pipeline_step VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    input_count INTEGER DEFAULT 0,
    loaded_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds REAL,
    metadata_json TEXT
);

-- 2. Cleaned & Curated Transactions
CREATE TABLE IF NOT EXISTS curated_transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL,
    transaction_amount REAL NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    transaction_type VARCHAR(32) NOT NULL,
    location VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    ip_address VARCHAR(64) NOT NULL,
    merchant_id VARCHAR(64) NOT NULL,
    channel VARCHAR(32) NOT NULL,
    customer_age INTEGER NOT NULL,
    customer_occupation VARCHAR(64) NOT NULL,
    transaction_duration INTEGER NOT NULL,
    login_attempts INTEGER NOT NULL,
    account_balance REAL NOT NULL,
    derived_prev_date TIMESTAMP,
    elapsed_minutes REAL,
    curated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Quarantined Bad Records (Failed validation)
CREATE TABLE IF NOT EXISTS rejected_records (
    record_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64),
    raw_payload TEXT,
    rejection_reason VARCHAR(255) NOT NULL,
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Behavioral Feature Store
CREATE TABLE IF NOT EXISTS transaction_features (
    transaction_id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL,
    account_txn_count INTEGER NOT NULL,
    account_avg_amount REAL,
    account_std_amount REAL,
    amount_deviation_ratio REAL,
    peer_avg_amount REAL,
    peer_deviation_ratio REAL,
    elapsed_minutes REAL,
    is_new_device INTEGER NOT NULL,
    is_new_ip INTEGER NOT NULL,
    high_login_attempts INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Explainable Alert Store
CREATE TABLE IF NOT EXISTS transaction_alerts (
    alert_id VARCHAR(64) PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL,
    account_id VARCHAR(64) NOT NULL,
    risk_score REAL NOT NULL,
    severity VARCHAR(32) NOT NULL,
    rule_reasons TEXT NOT NULL,
    detector_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
