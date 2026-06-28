# Ω-ABSORB-POLY-PROF-T v0.6

Status: zero-touch public research portfolio and artifact export upgrade.

## Purpose

v0.6 turns ranked public research opportunities into persistable local artifacts, specialized metadata ingestion paths, portfolio selections, graph exports, and backlog packets.

```text
public records
-> ResearchAtoms
-> opportunity ranking
-> portfolio selection
-> professor reports
-> artifact manifest
-> ProfessorGraph JSON / GraphML
-> backlog packet
```

## New modules

- `generated_report_artifacts.py`: builds generated Markdown artifacts and a manifest JSON payload.
- `poly_public_adapters.py`: adds PolyPublie-like and expertise-like public metadata adapters.
- `portfolio_optimizer.py`: selects a diversified opportunity portfolio from ranked bundles.
- `graph_exports.py`: exports ProfessorGraph-Poly to deterministic JSON and GraphML.
- `backlog_packet_templates.py`: renders local backlog packets from selected opportunities.

## Commands

```bash
python examples/omega_absorb_poly_prof_v06_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v06.py
```

## Zero-touch semantics

- Reports are generated as local artifacts and manifest entries.
- Public metadata adapters normalize caller-provided records only.
- Portfolio selection is deterministic and evidence/risk-aware through prior ranking.
- Graph exports are local strings suitable for files, reports, or later connectors.
- Backlog packets are generated locally; external platform actions remain capability boundaries.

## v0.7 next targets

1. add deterministic generated example artifacts under `generated/`;
2. add portfolio ranking report snapshots;
3. add richer GraphML metadata keys;
4. add adapter fixtures for PolyPublie-like and expertise-like records;
5. add cross-department collaboration recommender.
