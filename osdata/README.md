# AIT-OpenSourceDataAutomationManager v0.1

OAK-safe manager for automating Tristan systems with open-source/open-data sources.

## Pipeline

```text
Goal
→ SourceRegistry
→ License/Citation Gate
→ DataPlan
→ IngestionPlan
→ DatasetCard
→ TaskGraph
→ GitHubPlan
→ CloudDryRunPlan
→ OAK Report
→ Memory
```

## Integrated source registry

- OpenAlex
- Crossref
- arXiv
- Hugging Face Datasets
- GitHub public repositories
- World Bank Open Data
- Our World in Data
- Wikidata
- Open-Meteo
- NASA/NOAA open data placeholders

## Local validation

```text
ALL TESTS PASSED
OAK: needs_review
Sources: 8
Candidates: 8
Files: 49
```

`needs_review` is expected because several sources have dataset-specific licenses; each dataset must pass license/citation/provenance checks before downstream use.

## OAK law

```text
open-source data automation = license_ok + citation_ok + provenance + privacy_safe + rate_limit_respect + reproducible_pipeline
```

No bulk download, external write, merge, deploy, or network fetch is enabled by default.
