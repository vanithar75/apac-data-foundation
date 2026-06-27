"""End-to-end LTA bus arrival pipeline tests (fixture mode)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from apac_data.ingest import lta_bus_arrival as ingest_lta
from apac_data.ingest.guardrails import IngestGuardrailError, check_ingest_guardrails
from apac_data.quality.lta_bus_arrival import validate_silver
from apac_data.transform import lta_bus_arrival as transform_lta
from apac_data.transform.lta_bus_arrival import SILVER_COLUMNS


@pytest.fixture
def isolated_lta_layers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect data layers to tmp_path for hermetic tests."""
    data_root = tmp_path / "data"
    for layer in ("bronze", "silver", "gold"):
        for region in ("sg", "in"):
            (data_root / layer / region).mkdir(parents=True)

    bronze_sg = data_root / "bronze" / "sg" / "lta_bus_arrival"
    silver_sg = data_root / "silver" / "sg" / "lta_bus_arrival"
    gold_sg = data_root / "gold" / "sg" / "lta_bus_arrival"

    monkeypatch.setattr(ingest_lta, "LTA_BUS_ARRIVAL_BRONZE", bronze_sg)
    monkeypatch.setattr(transform_lta, "SILVER_DIR", silver_sg)
    monkeypatch.setattr(transform_lta, "GOLD_DIR", gold_sg)

    def bronze_output_dir() -> Path:
        path = data_root / "bronze" / "sg" / "lta_bus_arrival"
        path.mkdir(parents=True, exist_ok=True)
        return path

    monkeypatch.setattr(ingest_lta, "bronze_output_dir", bronze_output_dir)
    return data_root


def test_ingest_fixture_writes_bronze(isolated_lta_layers: Path) -> None:
    paths = ingest_lta.ingest(stop_codes=("83139",), force_fixture=True)
    assert len(paths) == 1
    assert paths[0].exists()
    envelope = json.loads(paths[0].read_text(encoding="utf-8"))
    assert envelope["bus_stop_code"] == "83139"
    assert "Services" in envelope["payload"]


def test_bronze_to_silver_schema(isolated_lta_layers: Path) -> None:
    bronze_paths = ingest_lta.ingest(stop_codes=("83139",), force_fixture=True)
    silver_path = transform_lta.bronze_to_silver(bronze_paths)
    df = pd.read_parquet(silver_path)

    assert list(df.columns) == list(SILVER_COLUMNS)
    assert len(df) == 6  # 2 services × 3 arrival slots
    validate_silver(df)


def test_silver_to_gold_hourly_counts(isolated_lta_layers: Path) -> None:
    bronze_paths = ingest_lta.ingest(stop_codes=("83139",), force_fixture=True)
    silver_path = transform_lta.bronze_to_silver(bronze_paths)
    gold_path = transform_lta.silver_to_gold(silver_path)
    gold = pd.read_parquet(gold_path)

    assert {"bus_stop_code", "service_no", "arrival_hour", "arrival_count"}.issubset(gold.columns)
    assert gold["arrival_count"].sum() >= 2
    assert (gold["bus_stop_code"] == "83139").all()


def test_full_pipeline_run_promotion(isolated_lta_layers: Path) -> None:
    bronze_paths = ingest_lta.ingest(stop_codes=("83139", "01012"), force_fixture=True)
    silver_path, gold_path = transform_lta.run_promotion(bronze_paths)

    assert silver_path.is_file()
    assert gold_path.is_file()
    silver_df = pd.read_parquet(silver_path)
    validate_silver(silver_df)
    assert silver_df["bus_stop_code"].nunique() == 2


def test_validate_silver_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_silver(pd.DataFrame(columns=list(SILVER_COLUMNS)))


def test_validate_silver_rejects_high_null_rate() -> None:
    df = pd.DataFrame(
        {
            "bus_stop_code": [None, "83139"],
            "ingested_at_utc": pd.to_datetime(["2026-06-27", "2026-06-27"], utc=True),
            "service_no": ["15", "10"],
            "operator": ["SBST", "TTS"],
            "status": ["In Operation", "In Operation"],
            "arrival_sequence": [1, 1],
            "estimated_arrival": pd.to_datetime(
                ["2026-06-27T02:00:00Z", "2026-06-27T03:00:00Z"],
                utc=True,
            ),
            "origin_code": ["a", "b"],
            "destination_code": ["c", "d"],
            "latitude": [1.0, 1.1],
            "longitude": [103.0, 103.1],
            "load": ["SEA", "SDA"],
        }
    )
    with pytest.raises(ValueError, match="bus_stop_code"):
        validate_silver(df)


def test_ingest_live_requires_api_key(
    isolated_lta_layers: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LTA_DATAMALL_ACCOUNT_KEY", raising=False)
    monkeypatch.setenv("LTA_USE_FIXTURE", "0")
    with pytest.raises(ValueError, match="LTA_DATAMALL_ACCOUNT_KEY"):
        ingest_lta.ingest(stop_codes=("83139",), force_fixture=False)


def test_guardrail_blocks_too_many_stops() -> None:
    stops = tuple(f"{i:05d}" for i in range(6))
    with pytest.raises(IngestGuardrailError, match="Ingest blocked"):
        check_ingest_guardrails(stops, max_stops=5, live_ingest=True, allow_large=False)


def test_guardrail_allow_large_override() -> None:
    stops = tuple(f"{i:05d}" for i in range(6))
    with pytest.warns(UserWarning, match="Live LTA ingest"):
        result = check_ingest_guardrails(stops, max_stops=5, live_ingest=True, allow_large=True)
    assert len(result) == 6


def test_guardrail_rejects_invalid_stop_code() -> None:
    with pytest.raises(IngestGuardrailError, match="Invalid bus stop code"):
        check_ingest_guardrails(("8313",), max_stops=5, live_ingest=False, allow_large=False)


def test_guardrail_deduplicates_stops() -> None:
    result = check_ingest_guardrails(
        ("83139", "83139", "01012"),
        max_stops=5,
        live_ingest=False,
        allow_large=False,
    )
    assert result == ("83139", "01012")


def test_ingest_fixture_blocked_over_max_without_override(
    isolated_lta_layers: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LTA_MAX_STOPS_PER_RUN", "2")
    stops = ("83139", "01012", "44009")
    with pytest.raises(IngestGuardrailError, match="Ingest blocked"):
        ingest_lta.ingest(stop_codes=stops, force_fixture=True, allow_large=False)


def test_live_ingest_warns_at_threshold() -> None:
    stops = ("83139", "01012", "44009")
    with pytest.warns(UserWarning, match="Live LTA ingest"):
        check_ingest_guardrails(stops, max_stops=5, live_ingest=True, allow_large=False)
