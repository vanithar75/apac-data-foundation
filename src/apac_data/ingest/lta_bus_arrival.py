"""LTA Bus Arrival — bronze ingest from LTA DataMall v3.

Source: https://datamall.lta.gov.sg (Singapore Open Data Licence).
Register for a free AccountKey; set LTA_DATAMALL_ACCOUNT_KEY in .env.
Without a key, ingest uses tests/fixtures/lta_bus_arrival_sample.json (CI-safe).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from apac_data.config import (
    LTA_ACCOUNT_KEY_ENV,
    LTA_BUS_ARRIVAL_URL,
    allow_large_ingest,
    bus_stop_codes,
    lta_account_key,
    max_stops_per_run,
    use_fixture_ingest,
)
from apac_data.ingest.guardrails import check_ingest_guardrails
from apac_data.paths import BRONZE_SG, REPO_ROOT, ensure_layer_dirs

DATASET_SLUG = "lta_bus_arrival"
LTA_BUS_ARRIVAL_BRONZE = BRONZE_SG / DATASET_SLUG
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "lta_bus_arrival_sample.json"
REQUEST_TIMEOUT_SECONDS = 30


def bronze_output_dir() -> Path:
    """Return bronze path for LTA bus arrival; creates parent dirs."""
    ensure_layer_dirs()
    LTA_BUS_ARRIVAL_BRONZE.mkdir(parents=True, exist_ok=True)
    return LTA_BUS_ARRIVAL_BRONZE


def _bronze_filename(bus_stop_code: str, ingested_at: datetime) -> str:
    stamp = ingested_at.strftime("%Y%m%dT%H%M%SZ")
    return f"bus_stop_{bus_stop_code}_{stamp}.json"


def fetch_live(bus_stop_code: str, account_key: str) -> dict[str, Any]:
    """Call LTA DataMall BusArrival v3 for one stop."""
    response = requests.get(
        LTA_BUS_ARRIVAL_URL,
        params={"BusStopCode": bus_stop_code},
        headers={"AccountKey": account_key, "accept": "application/json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        msg = f"Unexpected response type for stop {bus_stop_code}"
        raise TypeError(msg)
    return payload


def load_fixture(bus_stop_code: str) -> dict[str, Any]:
    """Load sample API payload; override BusStopCode for multi-stop tests."""
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload = dict(raw)
    payload["BusStopCode"] = bus_stop_code
    return payload


def write_bronze(payload: dict[str, Any], bus_stop_code: str, ingested_at: datetime) -> Path:
    """Write raw JSON to bronze with ingest metadata envelope."""
    bronze_dir = bronze_output_dir()
    envelope = {
        "ingested_at_utc": ingested_at.isoformat(),
        "bus_stop_code": bus_stop_code,
        "source_url": LTA_BUS_ARRIVAL_URL,
        "payload": payload,
    }
    out_path = bronze_dir / _bronze_filename(bus_stop_code, ingested_at)
    out_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    return out_path


def ingest(
    stop_codes: tuple[str, ...] | None = None,
    *,
    force_fixture: bool | None = None,
    allow_large: bool | None = None,
) -> list[Path]:
    """Fetch (or fixture-load) bus arrival data into bronze. Returns written paths."""
    use_fixture = use_fixture_ingest() if force_fixture is None else force_fixture
    large_ok = allow_large_ingest() if allow_large is None else allow_large
    codes = check_ingest_guardrails(
        stop_codes or bus_stop_codes(),
        max_stops=max_stops_per_run(),
        live_ingest=not use_fixture,
        allow_large=large_ok,
    )
    account_key = lta_account_key()
    written: list[Path] = []

    for code in codes:
        ingested_at = datetime.now(tz=UTC)
        if use_fixture:
            payload = load_fixture(code)
        else:
            if not account_key:
                msg = (
                    f"Set {LTA_ACCOUNT_KEY_ENV} in .env or use LTA_USE_FIXTURE=1 "
                    "for fixture ingest."
                )
                raise ValueError(msg)
            payload = fetch_live(code, account_key)
        written.append(write_bronze(payload, code, ingested_at))

    return written
