# Data Lineage

**Scope (current):** LTA Bus Arrival only. NEA, SingStat, and IMD ingests are **deferred** — platform pattern (quality CI + lineage) is proven on one dataset first.

**Metadata:** [metadata/lta_bus_arrival.yaml](metadata/lta_bus_arrival.yaml)

---

## LTA Bus Arrival

### Flow

```
LTA DataMall v3 API (BusArrival)
        │
        ▼
Bronze  data/bronze/sg/lta_bus_arrival/bus_stop_{code}_{timestamp}.json
        │  envelope: ingested_at_utc, bus_stop_code, source_url, payload
        ▼
Silver  data/silver/sg/lta_bus_arrival/lta_bus_arrival.parquet
        │  flatten Services → NextBus / NextBus2 / NextBus3 rows
        ▼
Gold    data/gold/sg/lta_bus_arrival/lta_bus_arrival_hourly.parquet
           hourly arrival_count by bus_stop_code + service_no
```

### Layer reference

| Stage | Location | Format | Governance tags |
|-------|----------|--------|-----------------|
| Source | [LTA DataMall v3](https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival) | JSON API | `region=sg`, `pii_risk=none`, Open Government Licence |
| Bronze | `data/bronze/sg/lta_bus_arrival/` | JSON envelope | `retention_days=90` (local policy) |
| Silver | `.../lta_bus_arrival.parquet` + `.duckdb` | Parquet | Schema fingerprint in quality contract |
| Gold | `.../lta_bus_arrival_hourly.parquet` + `.duckdb` | Parquet | Aggregates for analytics downstream |

### Quality gates (CI)

| Check | Where | Fails when |
|-------|-------|------------|
| Silver schema | `validate_silver` | Missing columns, empty frame, required nulls |
| Gold schema | `validate_gold` | Missing columns, `arrival_count <= 0` |
| Schema drift | `check_quality` | Fingerprint ≠ `tests/fixtures/lta_quality_contract.json` |
| Row minimums | contract JSON | Fixture pipeline yields too few rows |

**CI command (no API key, no cost):**

```bash
LTA_USE_FIXTURE=1 python -m apac_data.pipelines.check_quality
```

GitHub Actions runs this on every push/PR.

### Portfolio walkthrough (client workshop)

> This repo demonstrates a **governed medallion pattern** on Singapore open transport data: raw API snapshots land in bronze with ingest metadata; silver applies schema normalization and quality gates; gold exposes analytics-ready aggregates. Regional silos (`sg/` vs `in/`) enforce residency discipline before any cross-border combine. CI validates schema drift and null rates on every change using fixture data — no production API dependency in the pipeline gate.

---

## Deferred datasets

| Dataset | Portal | Status | Notes |
|---------|--------|--------|-------|
| NEA Rainfall | data.gov.sg | Deferred | Weather joins for future dashboards |
| SingStat sample | data.gov.sg | Deferred | Dimension enrichment |
| IMD Rainfall | data.gov.in | Deferred | Separate `in/` silo; DPDP note required |
