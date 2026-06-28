# Omega Absorb Poly Prof v1.3

Status: local JSON ingestion, compact tables, export bundles, package health and changelog upgrade.

## Purpose

v1.3 turns the CLI from an exporter into a local absorber and bundle compiler. It can read local JSON fixtures, normalize them through source adapters, render compact decision tables, export complete JSON + GraphML bundles, compute package health and generate a changelog from the version manifest.

```text
local JSON / demo source
-> normalization
-> validation table
-> ResearchAtoms
-> opportunity ranking
-> compact table
-> JSON + GraphML bundle
-> package health
-> changelog
```

## New modules

- `local_json_loader.py`: loads local JSON objects/lists and normalizes them with generic, PolyPublie-like or expertise-like adapters.
- `compact_table_report.py`: renders compact tables for rankings, portfolios and validation reports.
- `export_bundle.py`: writes summary, validation, graph JSON, GraphML, roadmap, status, docs index and manifest.
- `package_health.py`: computes a package health report.
- `changelog_generator.py`: generates changelog and release notes from `VersionManifest`.

## Updated modules

- `cli.py`: adds `ingest-json`, `table`, `export-bundle`, `health`, `changelog`.
- `version_manifest.py`: extends lineage through v1.3.
- `documentation_index.py`: extends docs index through v1.3.
- `package_status.py`: includes v1.3 commands.
- `pyproject.toml`: version bumped to `1.3.0`.

## CLI commands

```bash
omega-absorb ingest-json --input records.json --input-source generic
omega-absorb table --source combined
omega-absorb export-bundle --source combined --output-dir generated/custom_bundle
omega-absorb health
omega-absorb changelog
```

## Generated examples

- `generated/omega_absorb_poly_prof_v13/README.md`
- `generated/omega_absorb_poly_prof_v13/health.md`
- `generated/omega_absorb_poly_prof_v13/changelog.md`
- `generated/omega_absorb_poly_prof_v13/compact_table.txt`
- `generated/omega_absorb_poly_prof_v13/manifest.json`

## Tests

```bash
python examples/omega_absorb_poly_prof_v13_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v13.py
```

## OAK boundary

- Local JSON loading reads local files only.
- Claims remain test seeds, not truth.
- Export bundles are local artifacts.
- Health score is a package signal, not proof of correctness.
- External platform actions remain capability boundaries.

## v1.4 next targets

1. source registry schema strict mode;
2. ClaimGraph OAK++;
3. Method reproduction packets;
4. M-minus registry;
5. GitHub packet generator seed.
