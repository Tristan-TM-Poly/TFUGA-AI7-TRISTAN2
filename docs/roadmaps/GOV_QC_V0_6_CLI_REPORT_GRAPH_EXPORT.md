# Ω-GOV-QC-T v0.6/v0.7 — CLI / Report / Graph Export / CI Artifact

Status: C — implementation roadmap
Date: 2026-07-06
Branch: omega-gov-qc-t-mvp

## 0. Mission

Make TristanGovGraph Québec executable from a terminal and CI pipeline:

```text
example CSV/JSON -> local ingestion -> dataset health -> graph -> OAK bundle
                 -> Markdown municipal report -> GraphML export -> CI artifact
```

## 1. New modules

### `municipal_report.py`

Builds a safe demonstration municipal report from local, authorized example data.

Outputs:

- Markdown report ;
- dataset health summary ;
- OAKGate summary ;
- limitations ;
- next actions.

### `graph_exports.py`

Exports graph artifacts without heavy dependencies:

- adjacency dictionary ;
- GraphML string ;
- deterministic graph metadata.

### `cli.py`

Adds a console entry point:

```text
omega-gov-qc demo --out reports/generated
omega-gov-qc bundle --out reports/generated/bundle.json
omega-gov-qc graphml --out reports/generated/govgraph.graphml
```

## 2. OAK constraints

- CLI uses local example data by default ;
- no remote calls ;
- generated reports are clearly demo/non-authoritative ;
- GraphML export contains only registered graph nodes/edges ;
- CI artifact is generated from examples only.

## 3. New files

```text
omega_gov_qc_t/src/omega_gov_qc_t/municipal_report.py
omega_gov_qc_t/src/omega_gov_qc_t/graph_exports.py
omega_gov_qc_t/src/omega_gov_qc_t/cli.py
omega_gov_qc_t/tests/test_cli_report_graph_export.py
```

Updated files:

```text
omega_gov_qc_t/pyproject.toml
omega_gov_qc_t/src/omega_gov_qc_t/__init__.py
.github/workflows/omega_gov_qc_tests.yml
```

## 4. Success criteria

- CLI entry point exists ;
- demo report can be generated ;
- deterministic JSON bundle can be generated ;
- GraphML export can be generated ;
- CI workflow runs tests and generates artifact files ;
- no merge to main is performed by this roadmap.

## 5. Next after v0.7

v0.8 should add:

```text
GitHub issue generator
PR OAK status comment
snapshot tests for generated reports
optional FastAPI skeleton
municipal dashboard skeleton
```
