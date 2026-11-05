import sys
from pathlib import Path
import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.db import get_engine

st.set_page_config(
    page_title="Transaction Anomaly Monitoring",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Transaction Anomaly Monitoring System")
st.caption("Anomaly flag for review; not a confirmed fraud determination.")


@st.cache_data(ttl=60)
def load_dashboard_data():
    engine = get_engine()
    with engine.connect() as conn:
        tx_df = pd.read_sql("SELECT * FROM curated_transactions", con=conn)
        alerts_df = pd.read_sql("SELECT * FROM transaction_alerts", con=conn)
    return tx_df, alerts_df


try:
    tx_df, alerts_df = load_dashboard_data()
except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.stop()

# Top Metrics
col1, col2, col3, col4 = st.columns(4)
total_tx = len(tx_df)
total_alerts = len(alerts_df)
rate = (total_alerts / total_tx * 100) if total_tx > 0 else 0.0
med_count = (alerts_df["severity"] == "MEDIUM").sum() if not alerts_df.empty else 0

col1.metric("Total Transactions", f"{total_tx:,}")
col2.metric("Total Alerts Flagged", f"{total_alerts:,}")
col3.metric("Anomaly Rate", f"{rate:.1f}%")
col4.metric("Medium/High Priority", f"{med_count:,}")

st.divider()

# Sidebar Filters
st.sidebar.header("Filter Alerts")

severity_options = ["ALL"] + sorted(alerts_df["severity"].unique().tolist())
selected_severity = st.sidebar.selectbox("Severity", severity_options)

channel_options = ["ALL"] + sorted(alerts_df["channel"].unique().tolist())
selected_channel = st.sidebar.selectbox("Channel", channel_options)

filtered_alerts = alerts_df.copy()

if selected_severity != "ALL":
    filtered_alerts = filtered_alerts[filtered_alerts["severity"] == selected_severity]

if selected_channel != "ALL":
    filtered_alerts = filtered_alerts[filtered_alerts["channel"] == selected_channel]

# Main Alert View
st.subheader(f"Flagged Transactions ({len(filtered_alerts)} matching filters)")

display_cols = [
    "transaction_id", "account_id", "transaction_amount",
    "transaction_date", "channel", "location", "severity", "rule_reasons"
]

st.dataframe(
    filtered_alerts[[c for c in display_cols if c in filtered_alerts.columns]],
    use_container_width=True,
    hide_index=True
)

st.divider()

# Transaction Inspector
st.subheader("Transaction Inspector")
selected_id = st.selectbox(
    "Select Transaction ID to inspect explanation",
    options=filtered_alerts["transaction_id"].tolist() if not filtered_alerts.empty else []
)

if selected_id:
    alert_row = alerts_df[alerts_df["transaction_id"] == selected_id].iloc[0]
    tx_row = tx_df[tx_df["transaction_id"] == selected_id].iloc[0]

    detail_col1, detail_col2 = st.columns(2)

    with detail_col1:
        st.write("**Transaction Metadata**")
        st.write(f"- **Account ID:** `{tx_row.get('account_id')}`")
        st.write(f"- **Amount:** `${tx_row.get('transaction_amount', 0):,.2f}`")
        st.write(f"- **Date:** `{tx_row.get('transaction_date')}`")
        st.write(f"- **Channel / Location:** `{tx_row.get('channel')} / {tx_row.get('location')}`")
        st.write(f"- **Login Attempts:** `{tx_row.get('login_attempts')}`")
        st.write(f"- **Elapsed Minutes Since Last:** `{tx_row.get('elapsed_minutes')}`")

    with detail_col2:
        st.write("**Detection Evidence**")
        st.write(f"- **Severity Tier:** `{alert_row.get('severity')}`")
        st.write("- **Triggered Reasons:**")
        for reason in str(alert_row.get("rule_reasons")).split(";"):
            st.warning(f"⚠️ {reason.strip()}")

