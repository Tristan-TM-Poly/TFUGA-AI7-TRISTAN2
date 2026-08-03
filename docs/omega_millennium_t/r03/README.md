# Ω‑PROBLEM‑ATLAS‑T∞ R0.3

## Purpose

R0.3 extends Ω‑MILLENNIUM‑T∞ from seven Clay-directed programs to a scalable atlas of open-problem catalogs, competition streams, mathematical fronts, reusable attack modes and evidence-bearing research cells.

The seed fixture contains:

- 24 mathematical fronts;
- 72 anchor problem families, three per front;
- 8 attack modes per family;
- 576 deterministic research cells;
- 17 source registries for future ingestion;
- adjustable finite portfolio budgets;
- no permanent total-addition ceiling.

This is research infrastructure. It does **not** certify that every title remains open, prove any theorem, reconstruct an accepted proof, or claim a solution to a Clay problem.

## OAK separation

The data model separates:

1. a problem title;
2. an exact sourced statement;
3. a current-status assertion;
4. a toy or finite case;
5. a numerical or symbolic experiment;
6. a formalization skeleton;
7. a proof;
8. independent review.

Seed records carry conservative statuses such as `open_status_requires_refresh`. A record may set `current_open_status_claimed=true` only when it also supplies `source_verified_at`.

## Build

```bash
omega-problem-atlas build \
  --output-dir generated/omega_problem_atlas_r03 \
  --primary-budget 6 \
  --secondary-budget 24 \
  --experiment-budget 64
```

Audit:

```bash
omega-problem-atlas audit generated/omega_problem_atlas_r03
```

The three budgets select a finite campaign. They are not hard-coded architectural maxima. Larger values may be used as compute, review capacity, quality and provider constraints permit.

## Import contract

Additional problem records can be supplied as JSONL:

```json
{"problem_id":"example","title":"Example conjecture","front":"graphs_hypergraphs","status":"open","source_id":"aim_problem_lists","source_locator":"https://...","source_verified_at":"2026-08-03","statement":"Exact sourced statement","current_open_status_claimed":true,"solution_claimed":false}
```

Compile with repeated imports:

```bash
omega-problem-atlas build \
  --output-dir generated/atlas \
  --import-jsonl data/imports/erdos.jsonl \
  --import-jsonl data/imports/aim.jsonl
```

A current-open-status claim without `source_verified_at` is rejected. A solution claim is rejected at this ingestion layer.

## Outputs

```text
sources.jsonl
problems.jsonl
research_cells.jsonl
hyperedges.jsonl
portfolio.json
report.json
```

`report.json` is validated against `schemas/omega_problem_atlas_report_v3.schema.json`.

## Research-cell expansion

Each problem family is expanded through:

1. statement and provenance audit;
2. toy model;
3. finite or low-dimensional case;
4. weakened or restricted form;
5. conditional implication;
6. counterexample search;
7. formalization skeleton;
8. numerical or symbolic benchmark.

Future expansions can add methods, parameter ranges, evidence states, theorem dependencies and competition-specific constraints without changing the principle that finite materialization is not proof.

## Next ingestion fronts

Priority connectors are Clay, Erdős Problems, AIM problem lists, Ben Green's list, Formal Conjectures, Open Quantum Problems, OEIS, IMO, Putnam, COMAP MCM/ICM, ICPC, Kaggle, ARC Prize and AIMO.

Every connector must preserve exact source location, retrieval/revision metadata, licensing constraints, deduplication evidence and status-refresh requirements.
