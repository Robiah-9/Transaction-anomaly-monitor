"""
Extract module: Ingests raw bank transaction CSV into a pandas DataFrame.
Applies defensive checks to ensure file existence and schema integrity.
"""
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def extract(path: str = "data/Bank Transaction Data.csv", required_columns=None) -> pd.DataFrame:
    """
    Reads the raw transaction CSV file.
    
    Args:
        path: File path to the source CSV.
        required_columns: Optional list of mandatory columns to validate against.
        
    Returns:
        pd.DataFrame: Raw records loaded as strings to prevent premature type conversion.
    """
    file_path = Path(path)

    # Verify that the input file exists on disk
    try:
        # Load all columns as strings initially to preserve leading zeros and formatting
        df = pd.read_csv(file_path, dtype=str)
    except FileNotFoundError:
        logger.error("Transactions file not found: %s", file_path.resolve())
        raise

    # Fail fast if the CSV contains headers but zero data rows
    if df.empty:
        logger.error("Transactions file has no rows: %s", file_path)
        raise ValueError(f"No rows found in {file_path}")

    # Validate schema contract: ensure all required headers are present
    if required_columns is not None:
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            logger.error("Missing expected columns: %s", missing_cols)
            raise ValueError(f"CSV missing mandatory columns: {missing_cols}")

    logger.info("Extracted %d rows from %s", len(df), file_path.name)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    df = extract()
    print(df.head())
