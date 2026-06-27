"""Shared schema and null-rate helpers for data quality gates."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

import pandas as pd


def schema_fingerprint(columns: Iterable[str]) -> str:
    """Stable hash of column names for drift detection."""
    payload = "|".join(sorted(columns))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def assert_columns(df: pd.DataFrame, expected: tuple[str, ...] | list[str]) -> None:
    """Raise ValueError if columns do not match expected schema exactly."""
    actual = list(df.columns)
    if actual != list(expected):
        msg = f"Schema drift: expected {list(expected)}, got {actual}"
        raise ValueError(msg)


def max_null_rate(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return 1.0
    return float(df[column].isna().mean())


def assert_null_rate_below(
    df: pd.DataFrame,
    column: str,
    max_rate: float,
) -> None:
    rate = max_null_rate(df, column)
    if rate > max_rate:
        msg = f"Column {column} null rate {rate:.2%} exceeds {max_rate:.0%}"
        raise ValueError(msg)
