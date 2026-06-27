"""CI entrypoint: fixture pipeline + data quality gates (no live API)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from apac_data.ingest import lta_bus_arrival as ingest_lta
from apac_data.quality.lta_bus_arrival import validate_gold, validate_silver
from apac_data.quality.schema import schema_fingerprint
from apac_data.transform import lta_bus_arrival as transform_lta

CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "lta_quality_contract.json"
)
CI_STOP = "83139"


def load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def run_fixture_quality_gate() -> None:
    """Run bronze→gold on fixture data and enforce quality contract."""
    contract = load_contract()
    bronze_paths = ingest_lta.ingest(stop_codes=(CI_STOP,), force_fixture=True)
    silver_path, gold_path = transform_lta.run_promotion(bronze_paths)

    silver_df = pd.read_parquet(silver_path)
    gold_df = pd.read_parquet(gold_path)

    validate_silver(silver_df)
    validate_gold(gold_df)

    silver_fp = schema_fingerprint(silver_df.columns)
    gold_fp = schema_fingerprint(gold_df.columns)
    if silver_fp != contract["silver_schema_fingerprint"]:
        msg = (
            f"Silver schema fingerprint mismatch: {silver_fp} "
            f"(expected {contract['silver_schema_fingerprint']})"
        )
        raise ValueError(msg)
    if gold_fp != contract["gold_schema_fingerprint"]:
        msg = (
            f"Gold schema fingerprint mismatch: {gold_fp} "
            f"(expected {contract['gold_schema_fingerprint']})"
        )
        raise ValueError(msg)

    if len(silver_df) < contract["min_silver_rows"]:
        raise ValueError(f"Silver row count {len(silver_df)} below contract minimum")
    if len(gold_df) < contract["min_gold_rows"]:
        raise ValueError(f"Gold row count {len(gold_df)} below contract minimum")

    print(f"Quality gate passed: silver={len(silver_df)} rows, gold={len(gold_df)} rows")
    print(f"Schema fingerprints: silver={silver_fp}, gold={gold_fp}")


def main() -> None:
    run_fixture_quality_gate()


if __name__ == "__main__":
    main()
