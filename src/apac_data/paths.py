"""Medallion layer path constants — regional silos for SG and IN."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"

BRONZE_SG = DATA_ROOT / "bronze" / "sg"
BRONZE_IN = DATA_ROOT / "bronze" / "in"
SILVER_SG = DATA_ROOT / "silver" / "sg"
SILVER_IN = DATA_ROOT / "silver" / "in"
GOLD_SG = DATA_ROOT / "gold" / "sg"
GOLD_IN = DATA_ROOT / "gold" / "in"

ALL_LAYER_DIRS = (
    BRONZE_SG,
    BRONZE_IN,
    SILVER_SG,
    SILVER_IN,
    GOLD_SG,
    GOLD_IN,
)


def ensure_layer_dirs() -> None:
    """Create medallion directories if missing."""
    for path in ALL_LAYER_DIRS:
        path.mkdir(parents=True, exist_ok=True)
