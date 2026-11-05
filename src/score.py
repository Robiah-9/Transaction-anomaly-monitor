"""
Score module: Evaluates transaction records against transparent detection rules.
Flags suspicious behaviors with human-readable reason traces and severity tiers.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.db import get_engine


def score_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates transactions using 3 transparent behavioral rules:
    - AMOUNT_SPIKE: Amount > 2.5x the account's historical average spending (min $100).
    - RAPID_SUCCESSION: Less than 5 minutes elapsed since previous transaction.
    - FAILED_LOGIN_SPIKE: 3 or more authentication attempts prior to transaction.
    """
    if df.empty:
        return pd.DataFrame()

    scored = df.copy()

    # Calculate per-account average spending baseline
    if "account_id" in scored.columns and "transaction_amount" in scored.columns:
        scored["account_avg_amount"] = scored.groupby("account_id")["transaction_amount"].transform("mean").round(2)
    else:
        scored["account_avg_amount"] = scored.get("transaction_amount", 0.0)

    # Rule 1: Spending Spike (> 2.5x account mean and >= $100)
    rule_amount = (
        (scored["transaction_amount"] > 2.5 * scored["account_avg_amount"]) &
        (scored["transaction_amount"] >= 100.0)
    )

    # Rule 2: Rapid Velocity (< 5 minutes elapsed between transactions)
    if "elapsed_minutes" in scored.columns:
        rule_rapid = scored["elapsed_minutes"].notna() & (scored["elapsed_minutes"] < 5.0)
    else:
        rule_rapid = pd.Series([False] * len(scored), index=scored.index)

    # Rule 3: High Login Attempts (>= 3 attempts)
    if "login_attempts" in scored.columns:
        rule_login = scored["login_attempts"] >= 3
    else:
        rule_login = pd.Series([False] * len(scored), index=scored.index)

    # Build human-readable reason codes for each flagged transaction
    reasons_list = []
    for i in range(len(scored)):
        r = []
        if rule_amount.iloc[i]:
            r.append("AMOUNT_SPIKE")
        if rule_rapid.iloc[i]:
            r.append("RAPID_SUCCESSION")
        if rule_login.iloc[i]:
            r.append("FAILED_LOGIN_SPIKE")
        reasons_list.append(r)

    scored["reasons"] = reasons_list
    scored["rule_count"] = [len(r) for r in reasons_list]

    # Map rule counts to severity tiers:
    # 1 rule -> LOW, 2 rules -> MEDIUM, 3 rules -> HIGH
    def get_severity(count):
        if count >= 3:
            return "HIGH"
        elif count == 2:
            return "MEDIUM"
        elif count == 1:
            return "LOW"
        return "NORMAL"

    scored["severity"] = scored["rule_count"].apply(get_severity)

    # Filter to only keep transactions that triggered at least one rule
    alerts = scored[scored["rule_count"] > 0].copy()
    if alerts.empty:
        return pd.DataFrame()

    alerts["rule_reasons"] = alerts["reasons"].apply(lambda r: "; ".join(r))
    alerts["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    alert_cols = [
        "transaction_id", "account_id", "transaction_amount", "transaction_date",
        "channel", "location", "severity", "rule_reasons", "created_at"
    ]
    return alerts[[c for c in alert_cols if c in alerts.columns]].reset_index(drop=True)


def save_alerts(alerts_df: pd.DataFrame, engine=None):
    """Persists explainable alerts into PostgreSQL table 'transaction_alerts'."""
    if engine is None:
        engine = get_engine()

    if not alerts_df.empty:
        alerts_df.to_sql(
            name="transaction_alerts",
            con=engine,
            if_exists="replace",
            index=False
        )


if __name__ == "__main__":
    from src.extract import extract
    from src.clean import clean_data

    raw = extract()
    clean, _ = clean_data(raw)
    alerts = score_transactions(clean)
    save_alerts(alerts)
    print(f"Alerts generated: {len(alerts)}")
