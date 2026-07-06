# Ω-GOV-QC-T v0.4/v0.5 — Ingestion / Dataset Health / Export / CI

Status: B/C — implementation roadmap
Date: 2026-07-06
Branch: omega-gov-qc-t-mvp

## 0. Mission

Move TristanGovGraph Québec from a model skeleton to a reusable open-data pipeline:

```text
CSV/JSON text -> DatasetRecord -> DatasetHealthReport -> SourceRegistry
             -> GovGraph / EvidenceGraph / RiskRegister -> JSON bundle
             -> tests / CI / report-ready artifact
```

## 1. New modules

### `dataset_health.py`

Evaluates dataset readiness:

- row count ;
- column count ;
- missing field ratio ;
- duplicate record signal ;
- machine-readability ;
- source freshness hint ;
- metadata quality ;
- OAK readiness.

### `opendata_ingestor.py`

Provides dependency-free ingestion helpers:

- parse JSON array ;
- parse CSV text ;
- infer fields ;
- create `DatasetRecord` ;
- link dataset to `SourceRecord`.

### `json_exporter.py`

Exports a deterministic OAK bundle:

- graph ;
- sources ;
- evidence ;
- risks ;
- services ;
- products ;
- M- memory ;
- metadata.

### GitHub Actions test workflow

Runs package tests for the `omega_gov_qc_t` module on PR updates.

## 2. OAK constraints

This layer must remain safe:

- ingestion is local-text only, no uncontrolled network fetching ;
- dataset health is a signal, not a final judgment ;
- missing data is not evidence of wrongdoing or failure ;
- exports must preserve limitations and source metadata ;
- CI must test gates before the PR leaves draft state.

## 3. New files

```text
omega_gov_qc_t/src/omega_gov_qc_t/dataset_health.py
omega_gov_qc_t/src/omega_gov_qc_t/opendata_ingestor.py
omega_gov_qc_t/src/omega_gov_qc_t/json_exporter.py
omega_gov_qc_t/schemas/dataset_record.schema.json
omega_gov_qc_t/examples/open_data_demo.csv
omega_gov_qc_t/examples/open_data_demo.json
omega_gov_qc_t/tests/test_ingest_export_ci.py
.github/workflows/omega_gov_qc_tests.yml
```

## 4. Success criteria

- CSV demo parses into rows and fields ;
- JSON demo parses into rows and fields ;
- DatasetHealthReport computes quality signals ;
- JSON exporter returns deterministic text ;
- CI workflow is present ;
- no external data fetch is performed by default.

## 5. Next after v0.5

v0.6 should add:

```text
CLI omega-gov-qc
generated municipal report from demo input
optional NetworkX export
report snapshots
GitHub artifact generation
```
