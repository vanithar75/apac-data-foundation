"""LTA Bus Arrival — silver and gold promotion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from apac_data.ingest.lta_bus_arrival import LTA_BUS_ARRIVAL_BRONZE
from apac_data.paths import GOLD_SG, SILVER_SG, ensure_layer_dirs

DATASET_SLUG = "lta_bus_arrival"
SILVER_DIR = SILVER_SG / DATASET_SLUG
GOLD_DIR = GOLD_SG / DATASET_SLUG

SILVER_TABLE = "lta_bus_arrival"
GOLD_TABLE = "lta_bus_arrival_hourly"

SILVER_COLUMNS = (
    "bus_stop_code",
    "ingested_at_utc",
    "service_no",
    "operator",
    "status",
    "arrival_sequence",
    "estimated_arrival",
    "origin_code",
    "destination_code",
    "latitude",
    "longitude",
    "load",
)

ARRIVAL_SLOTS = ("NextBus", "NextBus2", "NextBus3")

GOLD_COLUMNS = (
    "bus_stop_code",
    "service_no",
    "arrival_hour",
    "arrival_count",
    "ingest_date",
)


def _parse_bronze_file(path: Path) -> list[dict[str, Any]]:
    envelope = json.loads(path.read_text(encoding="utf-8"))
    ingested_at = envelope["ingested_at_utc"]
    bus_stop_code = envelope["bus_stop_code"]
    payload = envelope["payload"]
    services = payload.get("Services") or []

    rows: list[dict[str, Any]] = []
    for service in services:
        service_no = service.get("ServiceNo")
        operator = service.get("Operator")
        status = service.get("Status")
        for sequence, slot in enumerate(ARRIVAL_SLOTS, start=1):
            bus = service.get(slot) or {}
            rows.append(
                {
                    "bus_stop_code": bus_stop_code,
                    "ingested_at_utc": ingested_at,
                    "service_no": service_no,
                    "operator": operator,
                    "status": status,
                    "arrival_sequence": sequence,
                    "estimated_arrival": bus.get("EstimatedArrival"),
                    "origin_code": bus.get("OriginCode"),
                    "destination_code": bus.get("DestinationCode"),
                    "latitude": bus.get("Latitude"),
                    "longitude": bus.get("Longitude"),
                    "load": bus.get("Load"),
                }
            )
    return rows


def bronze_to_silver(bronze_paths: list[Path] | None = None) -> Path:
    """Flatten bronze JSON envelopes to silver Parquet."""
    ensure_layer_dirs()
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    if bronze_paths is None:
        bronze_paths = sorted(LTA_BUS_ARRIVAL_BRONZE.glob("bus_stop_*.json"))

    all_rows: list[dict[str, Any]] = []
    for path in bronze_paths:
        all_rows.extend(_parse_bronze_file(path))

    df = pd.DataFrame(all_rows, columns=list(SILVER_COLUMNS))
    if not df.empty:
        df["estimated_arrival"] = pd.to_datetime(df["estimated_arrival"], utc=True, errors="coerce")
        df["ingested_at_utc"] = pd.to_datetime(df["ingested_at_utc"], utc=True, errors="coerce")

    out_path = SILVER_DIR / "lta_bus_arrival.parquet"
    df.to_parquet(out_path, index=False)

    db_path = SILVER_DIR / "lta_bus_arrival.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        con.execute(f"CREATE OR REPLACE TABLE {SILVER_TABLE} AS SELECT * FROM df")
    finally:
        con.close()

    return out_path


def silver_to_gold(silver_path: Path | None = None) -> Path:
    """Build hourly arrival counts by stop and service (gold layer)."""
    ensure_layer_dirs()
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    silver_path = silver_path or (SILVER_DIR / "lta_bus_arrival.parquet")
    df = pd.read_parquet(silver_path)

    if df.empty:
        gold = pd.DataFrame(columns=list(GOLD_COLUMNS))
    else:
        with_arrival = df.dropna(subset=["estimated_arrival"]).copy()
        with_arrival["arrival_hour"] = with_arrival["estimated_arrival"].dt.floor("h")
        with_arrival["ingest_date"] = with_arrival["ingested_at_utc"].dt.date
        gold = (
            with_arrival.groupby(
                ["bus_stop_code", "service_no", "arrival_hour", "ingest_date"],
                as_index=False,
            )
            .size()
            .rename(columns={"size": "arrival_count"})
        )
        gold = gold[list(GOLD_COLUMNS)]

    out_path = GOLD_DIR / "lta_bus_arrival_hourly.parquet"
    gold.to_parquet(out_path, index=False)

    db_path = GOLD_DIR / "lta_bus_arrival.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        con.execute(f"CREATE OR REPLACE TABLE {GOLD_TABLE} AS SELECT * FROM gold")
    finally:
        con.close()

    return out_path


def run_promotion(bronze_paths: list[Path] | None = None) -> tuple[Path, Path]:
    """Promote bronze → silver → gold. Returns (silver_path, gold_path)."""
    silver_path = bronze_to_silver(bronze_paths)
    gold_path = silver_to_gold(silver_path)
    return silver_path, gold_path
