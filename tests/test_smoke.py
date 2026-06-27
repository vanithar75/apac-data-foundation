"""Smoke tests — scaffold verification (Phase 1)."""

from apac_data import __version__
from apac_data.ingest import lta_bus_arrival
from apac_data.paths import ALL_LAYER_DIRS, REPO_ROOT, ensure_layer_dirs


def test_version_is_set() -> None:
    assert __version__ == "0.1.0"


def test_repo_layout_exists() -> None:
    assert (REPO_ROOT / "data" / "bronze" / "sg").is_dir()
    assert (REPO_ROOT / "src" / "apac_data").is_dir()
    assert (REPO_ROOT / "docs" / "decision-log.md").is_file()


def test_ensure_layer_dirs_creates_medallion_paths() -> None:
    ensure_layer_dirs()
    for layer_dir in ALL_LAYER_DIRS:
        assert layer_dir.is_dir()


def test_lta_bronze_output_dir() -> None:
    bronze = lta_bus_arrival.bronze_output_dir()
    assert bronze.name == "lta_bus_arrival"
    assert bronze.parent.name == "sg"
