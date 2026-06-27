"""Run LTA bus arrival bronze → silver → gold pipeline."""

from __future__ import annotations

import argparse

import pandas as pd

from apac_data.config import use_fixture_ingest
from apac_data.ingest import lta_bus_arrival as ingest_lta
from apac_data.quality.lta_bus_arrival import validate_gold, validate_silver
from apac_data.transform import lta_bus_arrival as transform_lta


def main() -> None:
    parser = argparse.ArgumentParser(description="LTA bus arrival medallion pipeline")
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Use bundled fixture (default when no API key)",
    )
    parser.add_argument(
        "--stops",
        help="Comma-separated bus stop codes (default: MVP sample set)",
    )
    parser.add_argument(
        "--allow-large",
        action="store_true",
        help="Override LTA_MAX_STOPS_PER_RUN guardrail (use with care)",
    )
    args = parser.parse_args()

    stop_codes = None
    if args.stops:
        stop_codes = tuple(s.strip() for s in args.stops.split(",") if s.strip())

    force_fixture = True if args.fixture else None
    if force_fixture is None and use_fixture_ingest():
        print("No LTA_DATAMALL_ACCOUNT_KEY — using fixture ingest.")

    bronze_paths = ingest_lta.ingest(
        stop_codes,
        force_fixture=force_fixture,
        allow_large=args.allow_large,
    )
    print(f"Bronze: wrote {len(bronze_paths)} file(s)")

    silver_path, gold_path = transform_lta.run_promotion(bronze_paths)
    silver_df = pd.read_parquet(silver_path)
    gold_df = pd.read_parquet(gold_path)
    validate_silver(silver_df)
    validate_gold(gold_df)
    print(f"Silver: {silver_path} ({len(silver_df)} rows)")
    print(f"Gold:   {gold_path} ({len(gold_df)} rows)")


if __name__ == "__main__":
    main()
