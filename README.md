# APAC Open Data Foundation

**Track B D1** — Medallion lakehouse over free Singapore and India open government datasets.

Part of the [VibeCoding Planner](https://app.notion.com/p/385818bdc73d81d38e34f1b651ad29c8) portfolio. Charter: `VibeCoding_Planner/projects/D1-apac-data-foundation/brief.md`. MVP plan: [Notion](https://app.notion.com/p/38c818bdc73d81bb8683d150e5a48336).

## Problem

Practitioners need a reproducible APAC open-data lakehouse pattern—bronze/silver/gold layers, quality gates, lineage, and regional residency discipline—not one-off notebooks.

## Architecture

```
data/
├── bronze/{sg,in}/   ← raw API JSON/CSV (cached)
├── silver/{sg,in}/   ← cleaned Parquet + DuckDB
└── gold/{sg,in}/     ← analytics-ready tables

src/apac_data/
├── ingest/           ← bronze writers
└── transform/        ← silver/gold promotion
```

Singapore and India data stay in **separate regional silos** for MVP (PDPA/DPDP). Cross-border joins deferred to D5.

## MVP scope (current)

| Dataset | Portal | Region | Status |
|---------|--------|--------|--------|
| LTA Bus Arrival | LTA DataMall | SG | **Active** — pipeline + quality CI + lineage |
| NEA Rainfall | data.gov.sg | SG | Deferred |
| SingStat sample | data.gov.sg | SG | Deferred |
| IMD Rainfall | data.gov.in | IN | Deferred |

Additional sources will follow the same medallion + quality-contract pattern when needed (e.g. D2).

## Quick start

```bash
py -3.12 -m venv .venv          # Windows (requires Python 3.11+)
.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

Copy `.env.example` to `.env` when adding live LTA or India ingest.

### LTA bus arrival pipeline

```bash
# Fixture mode (no API key — uses tests/fixtures/)
python -m apac_data.pipelines.lta_bus_arrival --fixture

# Live ingest (requires LTA_DATAMALL_ACCOUNT_KEY in .env)
python -m apac_data.pipelines.lta_bus_arrival --stops 83139,01012

# Guardrails: default max 5 stops per run (~2–4 KB API snapshot each)
# Override only when intentional:
# LTA_ALLOW_LARGE_INGEST=1 python -m apac_data.pipelines.lta_bus_arrival --allow-large --stops ...
```

### Data quality CI (fixture only — no API usage)

```bash
LTA_USE_FIXTURE=1 python -m apac_data.pipelines.check_quality
```

Runs bronze→gold on fixture data and enforces schema fingerprints + row minimums. GitHub Actions runs this on every push/PR.

## Governance

- **No PII** — aggregated open government data only
- **Licenses** — Open Government Licence (SG); attribute sources in README and exports
- **Decision log** — `docs/decision-log.md`
- **Lineage** — `docs/lineage.md`
- **Agent rules** — `VibeCoding_Planner/.cursor/rules/vibe-coding.md`

## Stack (free tier)

| Layer | Tool |
|-------|------|
| Local analytics | DuckDB |
| Transforms | Python + pandas |
| Orchestration | GitHub Actions |
| Storage | Parquet on disk |

## Status

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Repo scaffold | Done |
| 2 | LTA bus arrival pipeline | Done |
| 3–5 | NEA, SingStat, IMD | **Deferred** |
| 6 | Data quality CI | Done |
| 7 | Lineage + metadata | Done |
| 8 | MVP review & close | **Done** |

## Definition of Done (LTA reference MVP)

MVP closes on **one reference dataset** (LTA Bus Arrival) with a reusable platform pattern. Additional catalog datasets (NEA, SingStat, IMD) are deferred.

- [x] Repo with bronze/silver/gold structure
- [x] LTA end-to-end pipeline (bronze → silver → gold)
- [x] Lineage documentation and metadata (`docs/lineage.md`, `docs/metadata/`)
- [x] CI passes data quality smoke tests (fixture gate + pytest)
- [x] Decision log with license and residency entries
- [x] Ingest guardrails (max stops per run)
- [ ] Additional datasets (NEA, SingStat, IMD) — deferred to D2+

**Repo:** [github.com/vanithar75/apac-data-foundation](https://github.com/vanithar75/apac-data-foundation)

## License

Project code: MIT (TBD). Dataset terms follow each portal's open-data licence.
