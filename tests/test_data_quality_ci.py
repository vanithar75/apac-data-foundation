"""Data quality CI tests — fixture-only, no live API."""

from __future__ import annotations

import pandas as pd
import pytest

from apac_data.pipelines.check_quality import run_fixture_quality_gate
from apac_data.quality.lta_bus_arrival import validate_gold
from apac_data.quality.schema import assert_columns
from apac_data.transform.lta_bus_arrival import SILVER_COLUMNS


def test_ci_quality_gate_passes() -> None:
    run_fixture_quality_gate()


def test_silver_schema_drift_detected() -> None:
    df = pd.DataFrame({col: [1] for col in SILVER_COLUMNS})
    df = df.rename(columns={"service_no": "service_number"})
    with pytest.raises(ValueError, match="Schema drift"):
        assert_columns(df, SILVER_COLUMNS)


def test_gold_rejects_non_positive_counts() -> None:
    df = pd.DataFrame(
        {
            "bus_stop_code": ["83139"],
            "service_no": ["15"],
            "arrival_hour": pd.to_datetime(["2026-06-27T02:00:00Z"], utc=True),
            "arrival_count": [0],
            "ingest_date": [pd.Timestamp("2026-06-27").date()],
        }
    )
    with pytest.raises(ValueError, match="arrival_count"):
        validate_gold(df)


def test_validate_gold_accepts_valid_frame() -> None:
    df = pd.DataFrame(
        {
            "bus_stop_code": ["83139"],
            "service_no": ["15"],
            "arrival_hour": pd.to_datetime(["2026-06-27T02:00:00Z"], utc=True),
            "arrival_count": [2],
            "ingest_date": [pd.Timestamp("2026-06-27").date()],
        }
    )
    validate_gold(df)
