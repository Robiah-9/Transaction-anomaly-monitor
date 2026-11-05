import pytest
from src.main import run_pipeline


def test_main_pipeline_runs_without_error():
    try:
        results = run_pipeline()
        assert results["raw_count"] > 0
    except Exception as e:
        pytest.fail(f"run_pipeline() failed unexpectedly with error: {e}")
