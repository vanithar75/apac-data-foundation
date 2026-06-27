"""Environment and pipeline defaults."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from apac_data.paths import REPO_ROOT

load_dotenv(REPO_ROOT / ".env")

# LTA DataMall v3 — free registration at https://datamall.lta.gov.sg
LTA_BUS_ARRIVAL_URL = (
    "https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival"
)
LTA_ACCOUNT_KEY_ENV = "LTA_DATAMALL_ACCOUNT_KEY"

# MVP sample stops (5-digit codes); override via LTA_BUS_STOP_CODES=83139,01012
DEFAULT_BUS_STOP_CODES = ("83139", "01012", "44009")

# Guardrails — one API call per stop per run (~2–4 KB each, real-time snapshot only)
LTA_MAX_STOPS_ENV = "LTA_MAX_STOPS_PER_RUN"
LTA_ALLOW_LARGE_ENV = "LTA_ALLOW_LARGE_INGEST"
DEFAULT_MAX_STOPS_PER_RUN = 5


def lta_account_key() -> str | None:
    value = os.getenv(LTA_ACCOUNT_KEY_ENV, "").strip()
    return value or None


def bus_stop_codes() -> tuple[str, ...]:
    raw = os.getenv("LTA_BUS_STOP_CODES", "")
    if raw.strip():
        return tuple(code.strip() for code in raw.split(",") if code.strip())
    return DEFAULT_BUS_STOP_CODES


def use_fixture_ingest() -> bool:
    """Use bundled fixture when no API key (CI and local dev without registration)."""
    if os.getenv("LTA_USE_FIXTURE", "").lower() in {"1", "true", "yes"}:
        return True
    return lta_account_key() is None


def max_stops_per_run() -> int:
    """Maximum bus stops per ingest run (override via LTA_MAX_STOPS_PER_RUN)."""
    raw = os.getenv(LTA_MAX_STOPS_ENV, "").strip()
    if not raw:
        return DEFAULT_MAX_STOPS_PER_RUN
    try:
        value = int(raw)
    except ValueError as exc:
        msg = f"{LTA_MAX_STOPS_ENV} must be an integer, got {raw!r}"
        raise ValueError(msg) from exc
    if value < 1:
        raise ValueError(f"{LTA_MAX_STOPS_ENV} must be >= 1, got {value}")
    return value


def allow_large_ingest() -> bool:
    """Explicit opt-in to exceed LTA_MAX_STOPS_PER_RUN (env or CLI --allow-large)."""
    return os.getenv(LTA_ALLOW_LARGE_ENV, "").lower() in {"1", "true", "yes"}
