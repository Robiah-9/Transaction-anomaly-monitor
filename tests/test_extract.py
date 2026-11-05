import pytest
from src.extract import extract


def test_extract_returns_correct_shape(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "TransactionID,AccountID,TransactionAmount\n"
        "TX1,AC1,10.5\n"
        "TX2,AC2,20.0\n"
    )

    df = extract(csv_file)

    assert df.shape == (2, 3)


def test_extract_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract(tmp_path / "does_not_exist.csv")


def test_extract_header_only_raises(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("TransactionID,AccountID,TransactionAmount\n")

    with pytest.raises(ValueError):
        extract(csv_file)
