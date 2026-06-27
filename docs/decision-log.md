# Decision Log — Project D1: APAC Open Data Foundation

Format: date, context, decision, rationale, consequences.

---

## 2026-06-27 — Repo scaffold (Phase 1)

| Field | Value |
|-------|-------|
| **Context** | Empty workspace; kickoff from VibeCoding_Planner D1 brief |
| **Decision** | Medallion layout under `data/{bronze,silver,gold}/{sg,in}/`; DuckDB + Parquet stack; Python package `apac_data` |
| **Rationale** | Matches apac-catalog regional silo pattern; free-tier local dev; unblocks D2–D5 |
| **Consequences** | SG and IN data stay in separate paths until D5 governance layer |

---

## Dataset registry (MVP)

| Dataset | Portal | Region | License | PII risk | Status |
|---------|--------|--------|---------|----------|--------|
| LTA Bus Arrival | LTA DataMall | SG | Open Government Licence | none | **Active** (pipeline + CI) |
| NEA Rainfall | data.gov.sg | SG | Open Government Licence | none | **Deferred** |
| SingStat sample | data.gov.sg | SG | Open Government Licence | none | **Deferred** |
| IMD Rainfall | data.gov.in | IN | Government Open Data | none | **Deferred** |

**Residency:** Singapore datasets processed in `*/sg/` paths only. India datasets in `*/in/` only. No cross-border gold joins in MVP.

**Retention (MVP):** 1–3 months sample windows in bronze; document refresh cadence per dataset when ingest lands.

---

## 2026-06-27 — LTA Bus Arrival API (Phase 2)

| Field | Value |
|-------|-------|
| **Context** | LTA real-time bus data is served via DataMall, not data.gov.sg REST |
| **Decision** | Use `https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival` with `AccountKey` header; fixture fallback for CI |
| **Rationale** | Official v3 endpoint (Aug 2025 migration); free registration; bronze cache avoids rate-limit rework |
| **Consequences** | `LTA_DATAMALL_ACCOUNT_KEY` required for live ingest; default MVP stops: 83139, 01012, 44009 |

---

## 2026-06-27 — LTA ingest guardrails

| Field | Value |
|-------|-------|
| **Context** | Bus Arrival API is per-stop real-time snapshots; bulk fetch = many API calls, not one large file |
| **Decision** | Default `LTA_MAX_STOPS_PER_RUN=5`; block over-limit unless `LTA_ALLOW_LARGE_INGEST=1` or `--allow-large` |
| **Rationale** | Prevent accidental full-network polling; warn at 3+ live calls with estimated size |
| **Consequences** | MVP default (3 stops) always safe; explicit opt-in required for larger ingests |

---

---

## 2026-06-27 — Deprioritize additional datasets; finish quality + lineage on LTA

| Field | Value |
|-------|-------|
| **Context** | MVP value is the platform pattern (medallion, CI gates, lineage), not dataset count |
| **Decision** | Defer NEA, SingStat, IMD; implement data quality CI + lineage on LTA only |
| **Rationale** | One reference pipeline with CI/schema drift beats four shallow ingests; stays within Cursor Pro (fixture CI, no API) |
| **Consequences** | D1 MVP closes on LTA; other sources reuse contract when D2+ needs them |

---

## 2026-06-27 — Phase 8 MVP close (LTA reference pattern)

| Field | Value |
|-------|-------|
| **Context** | Phases 6–7 complete; NEA/SingStat/IMD deferred per scope decision |
| **Decision** | Close D1 MVP on LTA-only reference pipeline; status **MVP done** |
| **Rationale** | Platform pattern (medallion, CI, lineage, guardrails) is the portfolio deliverable |
| **Consequences** | INDEX + Notion updated; D2 unblocked when additional SG datasets are needed |

---

- [x] LTA API endpoint and rate-limit caching strategy (Phase 2)
- [ ] data.gov.in API key storage (`.env`, not committed) — when IMD is picked up
- [ ] SingStat table selection — when deferred ingest resumes
