import pytest
import pandas as pd
from src.score import score_transactions


def test_score_empty_input():
    empty_df = pd.DataFrame()
    alerts = score_transactions(empty_df)
    assert alerts.empty


def test_normal_transaction_has_no_alert():
    normal_data = pd.DataFrame([
        {
            "transaction_id": "TX_NORM",
            "account_id": "AC1",
            "transaction_amount": 50.0,
            "login_attempts": 1,
            "elapsed_minutes": 1440.0,
            "channel": "Online",
            "location": "Boston",
        }
    ])
    alerts = score_transactions(normal_data)
    assert len(alerts) == 0


def test_amount_spike_triggers_alert():
    spike_data = pd.DataFrame([
        {"transaction_id": "TX_A1", "account_id": "AC1", "transaction_amount": 20.0, "login_attempts": 1, "elapsed_minutes": 100.0},
        {"transaction_id": "TX_A2", "account_id": "AC1", "transaction_amount": 20.0, "login_attempts": 1, "elapsed_minutes": 100.0},
        {"transaction_id": "TX_SPIKE", "account_id": "AC1", "transaction_amount": 250.0, "login_attempts": 1, "elapsed_minutes": 100.0},
    ])
    alerts = score_transactions(spike_data)
    assert len(alerts) == 1
    assert alerts.iloc[0]["transaction_id"] == "TX_SPIKE"
    assert "AMOUNT_SPIKE" in alerts.iloc[0]["rule_reasons"]
    assert alerts.iloc[0]["severity"] == "LOW"


def test_rapid_succession_triggers_alert():
    rapid_data = pd.DataFrame([
        {
            "transaction_id": "TX_FAST",
            "account_id": "AC2",
            "transaction_amount": 30.0,
            "login_attempts": 1,
            "elapsed_minutes": 2.0,
            "channel": "ATM",
            "location": "Miami",
        }
    ])
    alerts = score_transactions(rapid_data)
    assert len(alerts) == 1
    assert "RAPID_SUCCESSION" in alerts.iloc[0]["rule_reasons"]


def test_two_rules_trigger_medium_severity():
    medium_risk = pd.DataFrame([
        {"transaction_id": "TX_1", "account_id": "AC3", "transaction_amount": 30.0, "login_attempts": 1, "elapsed_minutes": 100.0},
        {"transaction_id": "TX_2", "account_id": "AC3", "transaction_amount": 30.0, "login_attempts": 1, "elapsed_minutes": 100.0},
        {"transaction_id": "TX_MED", "account_id": "AC3", "transaction_amount": 400.0, "login_attempts": 4, "elapsed_minutes": 100.0},
    ])
    alerts = score_transactions(medium_risk)
    med_alert = alerts[alerts["transaction_id"] == "TX_MED"].iloc[0]
    assert med_alert["severity"] == "MEDIUM"
    assert "AMOUNT_SPIKE" in med_alert["rule_reasons"]
    assert "FAILED_LOGIN_SPIKE" in med_alert["rule_reasons"]
