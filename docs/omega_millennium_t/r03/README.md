# Ω‑PROBLEM‑ATLAS‑T∞ R0.3

## Purpose

R0.3 extends Ω‑MILLENNIUM‑T∞ from seven Clay-directed programs to a scalable atlas of open-problem catalogs, competition streams, mathematical fronts, reusable methods and evidence-bearing research cells.

Two materialization modes are provided.

### Compact fixture

- 24 mathematical fronts;
- 72 conservative anchor problem families;
- 8 attack modes per family;
- 576 deterministic research cells;
- 576 materialization hyperedges.

### MAX fixture

- the same 72 externally anchored problem families;
- 12 typed research targets per problem;
- 864 falsifiable research targets;
- 8 attack modes per target;
- 6,912 evidence work cells;
- 32 reusable method families;
- 8,568 problem-target-method-cell hyperedges;
- file-level SHA-256 receipts and referential-integrity audit;
- a balanced primary portfolio covering all 24 fronts.

The MAX target and cell counts are internal research decompositions. They are not claims that 864 independent external conjectures were sourced.

This is research infrastructure. It does **not** certify that every title remains open, prove any theorem, reconstruct an accepted proof, or claim a solution to a Clay problem.

## OAK separation

The data model separates:

1. a problem title;
2. an exact sourced statement;
3. a current-status assertion;
4. a typed research target;
5. a toy or finite case;
6. a numerical or symbolic experiment;
7. a formalization target;
8. a kernel-checked proof;
9. independent review.

Seed records carry conservative statuses such as `open_status_requires_refresh`. A record may set `current_open_status_claimed=true` only when it also supplies `source_verified_at`.

## Compact build

```bash
omega-problem-atlas build \
  --output-dir generated/omega_problem_atlas_r03 \
  --primary-budget 6 \
  --secondary-budget 24 \
  --experiment-budget 64
```

```bash
omega-problem-atlas audit generated/omega_problem_atlas_r03
```

## MAX build

```bash
omega-problem-atlas build-max \
  --output-dir generated/omega_problem_atlas_r03_max \
  --primary-budget 24 \
  --secondary-budget 72 \
  --experiment-budget 256
```

```bash
omega-problem-atlas audit-max generated/omega_problem_atlas_r03_max
```

The budgets select finite campaigns. They are not hard-coded architectural maxima. Larger values may be used as compute, review capacity, quality, legal and provider constraints permit. `permanent_total_cap` remains null.

## Import contract

Additional problem records can be supplied as JSONL:

```json
{"problem_id":"example","title":"Example conjecture","front":"graphs_hypergraphs","status":"open","source_id":"aim_problem_lists","source_locator":"https://...","source_verified_at":"2026-08-03","statement":"Exact sourced statement","current_open_status_claimed":true,"solution_claimed":false}
```

Compile with repeated imports:

```bash
omega-problem-atlas build-max \
  --output-dir generated/atlas \
  --import-jsonl data/imports/erdos.jsonl \
  --import-jsonl data/imports/aim.jsonl
```

A current-open-status claim without `source_verified_at` is rejected. A solution claim is rejected at this ingestion layer.

## Compact outputs

```text
sources.jsonl
problems.jsonl
research_cells.jsonl
hyperedges.jsonl
portfolio.json
report.json
```

`report.json` is validated against `schemas/omega_problem_atlas_report_v3.schema.json`.

## MAX outputs

```text
sources.jsonl
problems.jsonl
research_targets.jsonl
research_cells.jsonl
methods.jsonl
hyperedges.jsonl
portfolio.json
manifest.json
report.json
```

The MAX report is validated against `schemas/omega_problem_atlas_max_report_v3.schema.json`. `manifest.json` records SHA-256, byte size and JSONL row count for every data artifact.

## Twelve MAX target kinds

1. canonical statement;
2. literature and status audit;
3. equivalent form;
4. known-case reconstruction;
5. toy model;
6. finite case;
7. weakened form;
8. conditional theorem;
9. barrier or no-go test;
10. counterexample frontier;
11. computational certificate;
12. formalization target.

Each target declares the evidence needed for promotion and a condition that would falsify or invalidate the attempted result.

## Eight attack modes

1. statement and provenance audit;
2. toy model;
3. finite or low-dimensional case;
4. weakened or restricted form;
5. conditional implication;
6. counterexample search;
7. formalization skeleton;
8. numerical or symbolic benchmark.

## Priority semantics

The compact mode is retained as a small compatibility fixture. The MAX mode replaces hash-derived score variation with transparent target and attack-mode profiles, evidence readiness, uncertainty and false-progress penalties.

The resulting `priority_score` is a scheduling heuristic. It is not a probability of truth, proof, novelty or prize success.

## Source fronts

The registry prepares Clay, Erdős Problems, AIM problem lists, Ben Green's list, Formal Conjectures, Open Quantum Problems, OEIS, IMO, Putnam, COMAP MCM/ICM, ICPC, Kaggle, ARC Prize, AIMO and additional literature/community channels.

Every production connector must preserve exact source location, retrieval or revision metadata, licensing constraints, deduplication evidence and status-refresh requirements.

## Deeper analysis

See [`MAX_ANALYSIS.md`](MAX_ANALYSIS.md) for the architectural weaknesses found in the compact layer, the MAX corrections, scale formulas, OAK boundaries and the next primary-source, evidence, execution and publication phases.
