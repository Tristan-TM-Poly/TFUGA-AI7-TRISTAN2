# Ω-ABSORB-POLY-PROF-T v0.5

Status: zero-touch public research opportunity ranking upgrade.

## Purpose

v0.5 adds ranking, professor backlog reports, metadata adapters, schemas, and ProfessorGraph integration.

```text
public records
-> ResearchAtoms
-> opportunity bundles
-> ranking
-> professor backlog Markdown
-> ProfessorGraph integration
```

## New modules

- `opportunity_ranker.py`: ranks CourseCVCD / ProjectForge / GrantForge / IPGate bundles.
- `professor_backlog_report.py`: renders per-professor Markdown backlogs.
- `public_metadata_adapters.py`: normalizes caller-provided public metadata records.
- `professor_graph_integration.py`: converts ResearchAtoms into ProfessorGraph nodes and edges.
- `schemas/claim_graph_v0_5.schema.json`
- `schemas/method_graph_v0_5.schema.json`

## Commands

```bash
python examples/omega_absorb_poly_prof_v05_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v05.py
```

## Ranking formula

```text
final_score = value_score - 0.35 * risk_penalty + reproducibility_bonus
```

## v0.6 next targets

1. persist generated reports under `generated/`;
2. add real public metadata adapter stubs for PolyPublie-like records;
3. add opportunity portfolio optimizer;
4. add GraphML/JSON export for ProfessorGraph;
5. add generated issue/backlog packet templates.
