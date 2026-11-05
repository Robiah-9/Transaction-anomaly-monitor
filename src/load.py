"""
Load module: Persists curated records and quarantined rows into PostgreSQL.
"""
import sys
from pathlib import Path
import logging
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.db import get_engine

logger = logging.getLogger(__name__)


def load_data(clean_df: pd.DataFrame, rejected_df: pd.DataFrame = None, engine=None):
    """
    Loads curated data into PostgreSQL table 'curated_transactions'
    and rejected data into 'rejected_records'.
    """
    if engine is None:
        engine = get_engine()

    # Load clean curated transactions
    if not clean_df.empty:
        clean_df.to_sql(
            name="curated_transactions",
            con=engine,
            if_exists="replace",  # Replace old run data for idempotency
            index=False
        )
        logger.info("Loaded %d rows into curated_transactions", len(clean_df))

    # Load quarantined bad rows if any exist
    if rejected_df is not None and not rejected_df.empty:
        rejected_df.to_sql(
            name="rejected_records",
            con=engine,
            if_exists="replace",
            index=False
        )
        logger.info("Loaded %d rows into rejected_records", len(rejected_df))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    from src.extract import extract
    from src.clean import clean_data

    raw = extract()
    clean, rejected = clean_data(raw)
    load_data(clean, rejected)
