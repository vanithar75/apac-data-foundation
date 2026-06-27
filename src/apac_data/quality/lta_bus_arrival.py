"""LTA bus arrival silver and gold quality gates."""

from __future__ import annotations

import pandas as pd

from apac_data.quality.schema import assert_columns, assert_null_rate_below
from apac_data.transform.lta_bus_arrival import GOLD_COLUMNS, SILVER_COLUMNS

SILVER_REQUIRED_NON_NULL = ("bus_stop_code", "service_no", "ingested_at_utc", "arrival_sequence")
MAX_REQUIRED_NULL_RATE = 0.0

GOLD_REQUIRED_NON_NULL = ("bus_stop_code", "service_no", "arrival_hour", "arrival_count")


def validate_silver(df: pd.DataFrame) -> None:
    """Raise ValueError if silver layer fails quality gates."""
    assert_columns(df, SILVER_COLUMNS)

    if df.empty:
        raise ValueError("Silver layer is empty")

    for col in SILVER_REQUIRED_NON_NULL:
        assert_null_rate_below(df, col, MAX_REQUIRED_NULL_RATE)

    if df["arrival_sequence"].nunique() < 1:
        raise ValueError("arrival_sequence has no values")

    if df["estimated_arrival"].notna().sum() == 0:
        raise ValueError("No estimated_arrival values — check bronze payload")


def validate_gold(df: pd.DataFrame) -> None:
    """Raise ValueError if gold layer fails quality gates."""
    assert_columns(df, GOLD_COLUMNS)

    if df.empty:
        raise ValueError("Gold layer is empty")

    for col in GOLD_REQUIRED_NON_NULL:
        assert_null_rate_below(df, col, MAX_REQUIRED_NULL_RATE)

    if (df["arrival_count"] <= 0).any():
        raise ValueError("arrival_count must be positive in gold layer")
