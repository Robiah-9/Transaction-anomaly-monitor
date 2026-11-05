import pytest
import pandas as pd
from sqlalchemy import create_engine
from src.load import load_data


def test_load_data_saves_to_database():
    test_engine = create_engine("sqlite:///:memory:")

    clean = pd.DataFrame([{"transaction_id": "TX1", "transaction_amount": 100.0}])
    rejected = pd.DataFrame([{"transaction_id": "TX_BAD", "rejection_reason": "INVALID_AMOUNT"}])

    load_data(clean_df=clean, rejected_df=rejected, engine=test_engine)

    res_clean = pd.read_sql("SELECT * FROM curated_transactions", con=test_engine)
    res_rejected = pd.read_sql("SELECT * FROM rejected_records", con=test_engine)

    assert len(res_clean) == 1
    assert res_clean.iloc[0]["transaction_id"] == "TX1"

    assert len(res_rejected) == 1
    assert res_rejected.iloc[0]["rejection_reason"] == "INVALID_AMOUNT"
