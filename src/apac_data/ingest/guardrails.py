"""Ingest scope guardrails — prevent accidental bulk LTA API fetches."""

from __future__ import annotations

import logging
import warnings

logger = logging.getLogger(__name__)

DEFAULT_MAX_STOPS_PER_RUN = 5
WARN_STOPS_THRESHOLD = 3


class IngestGuardrailError(ValueError):
    """Raised when an ingest request exceeds configured safety limits."""


def validate_bus_stop_code(code: str) -> str:
    """Normalize and validate a 5-digit LTA bus stop code."""
    normalized = code.strip()
    if not normalized.isdigit() or len(normalized) != 5:
        msg = f"Invalid bus stop code {code!r}: expected 5-digit numeric string (e.g. 83139)"
        raise IngestGuardrailError(msg)
    return normalized


def check_ingest_guardrails(
    stop_codes: tuple[str, ...],
    *,
    max_stops: int,
    live_ingest: bool,
    allow_large: bool,
) -> tuple[str, ...]:
    """Validate stop list size and format before ingest.

  - Blocks when ``len(stop_codes) > max_stops`` unless ``allow_large`` is True.
  - Warns when a live ingest uses ``WARN_STOPS_THRESHOLD`` or more stops.
  - Deduplicates while preserving order.
    """
    if not stop_codes:
        raise IngestGuardrailError("At least one bus stop code is required")

    seen: set[str] = set()
    deduped: list[str] = []
    for code in stop_codes:
        normalized = validate_bus_stop_code(code)
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)

    count = len(deduped)
    if count > max_stops and not allow_large:
        msg = (
            f"Ingest blocked: {count} bus stops requested but "
            f"LTA_MAX_STOPS_PER_RUN is {max_stops}. "
            "Each stop is one API call (~2–4 KB snapshot, not historical bulk data). "
            "To proceed anyway, set LTA_ALLOW_LARGE_INGEST=1 or pass --allow-large."
        )
        raise IngestGuardrailError(msg)

    if live_ingest:
        if count >= WARN_STOPS_THRESHOLD:
            warnings.warn(
                f"Live LTA ingest: {count} API call(s) will be made "
                f"(~{count * 3}–{count * 4} KB bronze JSON estimated).",
                UserWarning,
                stacklevel=3,
            )
        if allow_large and count > max_stops:
            logger.warning(
                "Large ingest override active: %s stops (limit %s)",
                count,
                max_stops,
            )

    return tuple(deduped)
