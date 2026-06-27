"""LTA bus arrival silver-layer quality gates."""

from __future__ import annotations

import pandas as pd

from apac_data.transform.lta_bus_arrival import SILVER_COLUMNS

REQUIRED_NON_NULL = ("bus_stop_code", "service_no", "ingested_at_utc", "arrival_sequence")
MAX_REQUIRED_NULL_RATE = 0.0


def validate_silver(df: pd.DataFrame) -> None:
    """Raise ValueError if silver layer fails quality gates."""
    missing_cols = set(SILVER_COLUMNS) - set(df.columns)
    if missing_cols:
        msg = f"Silver schema missing columns: {sorted(missing_cols)}"
        raise ValueError(msg)

    if df.empty:
        msg = "Silver layer is empty"
        raise ValueError(msg)

    for col in REQUIRED_NON_NULL:
        null_rate = df[col].isna().mean()
        if null_rate > MAX_REQUIRED_NULL_RATE:
            msg = f"Column {col} null rate {null_rate:.2%} exceeds {MAX_REQUIRED_NULL_RATE:.0%}"
            raise ValueError(msg)

    if df["arrival_sequence"].nunique() < 1:
        raise ValueError("arrival_sequence has no values")

    if df["estimated_arrival"].notna().sum() == 0:
        raise ValueError("No estimated_arrival values — check bronze payload")
