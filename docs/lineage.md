# Data Lineage — D1 MVP

Document source → bronze → silver → gold for each dataset.

---

## LTA Bus Arrival {color="green"}

| Stage | Location | Format | Notes |
|-------|----------|--------|-------|
| Source | [LTA DataMall v3 BusArrival](https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival) | JSON API | AccountKey required; Open Government Licence |
| Bronze | `data/bronze/sg/lta_bus_arrival/bus_stop_{code}_{timestamp}.json` | JSON envelope | Raw payload + `ingested_at_utc` metadata |
| Silver | `data/silver/sg/lta_bus_arrival/lta_bus_arrival.parquet` | Parquet + DuckDB | Flattened NextBus/2/3 rows per service |
| Gold | `data/gold/sg/lta_bus_arrival/lta_bus_arrival_hourly.parquet` | Parquet + DuckDB | Hourly arrival counts by stop + service |

**Run pipeline:** `python -m apac_data.pipelines.lta_bus_arrival` (fixture mode without API key)

**Quality gates:** Required columns non-null; at least one `estimated_arrival` per ingest batch.

---

## Other datasets (status)

| Dataset | Source | Bronze | Silver | Gold |
|---------|--------|--------|--------|------|
| NEA Rainfall | data.gov.sg | — | — | — |
| SingStat sample | data.gov.sg | — | — | — |
| IMD Rainfall | data.gov.in | — | — | — |

**Catalog reference:** `VibeCoding_Planner/docs/datasets/apac-catalog.md`
