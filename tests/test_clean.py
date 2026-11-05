import pytest
import pandas as pd
from src.clean import clean_data


def test_clean_data_empty_input():
    empty_df = pd.DataFrame()
    clean_df, rejected_df = clean_data(empty_df)
    assert clean_df.empty
    assert rejected_df.empty


def test_clean_data_valid_rows():
    sample = pd.DataFrame([
        {
            "TransactionID": "TX100",
            "AccountID": "AC1",
            "TransactionAmount": "150.50",
            "TransactionDate": "2023-05-01 10:00:00",
            "TransactionType": "Debit",
            "Location": "New York",
            "DeviceID": "DEV01",
            "IP Address": "192.168.1.1",
            "MerchantID": "M01",
            "Channel": "Online",
            "CustomerAge": "30",
            "CustomerOccupation": "Engineer",
            "TransactionDuration": "60",
            "LoginAttempts": "1",
            "AccountBalance": "5000.00",
        }
    ])
    clean_df, rejected_df = clean_data(sample)
    assert len(clean_df) == 1
    assert len(rejected_df) == 0
    assert clean_df.iloc[0]["transaction_amount"] == 150.50


def test_clean_data_removes_invalid_amount():
    sample = pd.DataFrame([
        {
            "TransactionID": "TX_BAD",
            "AccountID": "AC1",
            "TransactionAmount": "-25.00",
            "TransactionDate": "2023-05-01 10:00:00",
            "AccountBalance": "5000.00",
            "TransactionDuration": "60",
        }
    ])
    clean_df, rejected_df = clean_data(sample)
    assert len(clean_df) == 0
    assert len(rejected_df) == 1
    assert rejected_df.iloc[0]["TransactionID"] == "TX_BAD"


def test_clean_data_removes_duplicates():
    sample = pd.DataFrame([
        {
            "TransactionID": "TX_DUP",
            "AccountID": "AC1",
            "TransactionAmount": "50.00",
            "TransactionDate": "2023-05-01 10:00:00",
            "AccountBalance": "5000.00",
            "TransactionDuration": "60",
        },
        {
            "TransactionID": "TX_DUP",
            "AccountID": "AC1",
            "TransactionAmount": "75.00",
            "TransactionDate": "2023-05-01 11:00:00",
            "AccountBalance": "5000.00",
            "TransactionDuration": "60",
        }
    ])
    clean_df, rejected_df = clean_data(sample)
    assert len(clean_df) == 1
    assert len(rejected_df) == 1


def test_clean_data_calculates_elapsed_minutes():
    sample = pd.DataFrame([
        {
            "TransactionID": "TX_1",
            "AccountID": "AC_USER",
            "TransactionAmount": "20.00",
            "TransactionDate": "2023-05-01 10:00:00",
            "AccountBalance": "1000.00",
            "TransactionDuration": "30",
        },
        {
            "TransactionID": "TX_2",
            "AccountID": "AC_USER",
            "TransactionAmount": "30.00",
            "TransactionDate": "2023-05-01 10:45:00",
            "AccountBalance": "970.00",
            "TransactionDuration": "30",
        }
    ])
    clean_df, _ = clean_data(sample)
    assert pd.isna(clean_df.iloc[0]["elapsed_minutes"])
    assert clean_df.iloc[1]["elapsed_minutes"] == 45.0
