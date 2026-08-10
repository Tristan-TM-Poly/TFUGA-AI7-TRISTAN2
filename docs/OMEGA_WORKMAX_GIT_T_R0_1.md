# Ω-WORKMAX-GIT-T∞ — R0.1

Status: **executable planning/measurement kernel; OAK review required; no autonomous GitHub mutation**.

## Mission

Ω-WORKMAX-GIT-T∞ maximizes **distinct, validated, crystallized and reusable work per unit of wall time and constrained resource**, rather than raw line count, commit count or generated volume.

It is a convergence layer, not a new sovereign orchestrator.

```text
Meta Orchestrator / user intent
        ↓
Ω-WORKMAX-GIT-T∞
        ├── capability reuse routing
        ├── WorkPacket / WorkHypergraph
        ├── semantic-key deduplication
        ├── Pareto + blocking/information priority
        ├── execution waves
        ├── Repository Work Digital Twin
        ├── telemetry metrics
        ├── crystallization governor
        └── OAK promotion gates
             ↓
Ω-ACTIONS-T∞ / Ω-SANS-PLAFOND-T∞ / bounded executors
```

The existing command sovereignty remains:

```text
Intention → Command → Packet → Adapter Route → Campaign → Wave
→ Review → Promotion/Rollback → Propagation → Return Route
```

WORKMAX compiles and scores work inside that doctrine; it does not supersede it.

## R0.1 implemented objects

### WorkPacket

A work unit carries:

- stable `work_id`;
- objective and expected artifact;
- explicit dependencies;
- estimated duration;
- value, evidence, crystallization and reuse signals;
- risk and reversibility;
- failure-information signal;
- tags, semantic key and optional capability ID;
- required evidence and explicit state.

### WorkHypergraph

R0.1 uses an acyclic dependency execution graph with arbitrary predecessor sets. It provides:

- deterministic topological order;
- missing-dependency and cycle rejection;
- descendant/blocking power;
- exact finite critical-path duration;
- ready-set discovery.

A richer semantic hypergraph may be layered above this execution DAG later; R0.1 does not pretend every semantic relation is an executable dependency.

## Objective family

Conceptually:

```text
maximize:
  validated work
  validated-work power
  closure
  reuse
  evidence density
  generative leverage

minimize:
  wall time
  queue waste
  fan-out
  duplicate work
  risk
  crystallization debt
```

R0.1 therefore exposes metrics and Pareto structure rather than declaring one universal scalar optimum.

## Reuse-before-generate

`route_capabilities()` accepts exported capability-like records and performs deterministic, transparent token-overlap ranking with an evidence contribution.

Possible results:

- `REUSE_CANDIDATE`
- `EXTEND_OR_INSPECT`
- `NO_MATCH_SIGNAL`

The router is deliberately non-authorizing. Lexical overlap is not proof of semantic equivalence, safety, current validity, legal permission or execution authority.

This is compatible with Ω-CHATGIT-T's contract-first doctrine: inspect and reuse the smallest evidenced current capability before creating another one.

## Deduplication

R0.1 deduplicates exact semantic signatures derived from an explicit `semantic_key` when present, otherwise from normalized objective/artifact/tags.

Representative choice prefers:

1. stronger evidence;
2. greater crystallization;
3. lower risk;
4. lower estimated cost;
5. deterministic ID ordering.

Dependencies that reference a removed duplicate are rewired to the canonical packet before graph compilation.

This prevents generated volume from being mistaken for distinct work.

## Mycelial priority heuristic

For a ready packet, R0.1 scores approximately:

```text
value
× blocking power
× evidence
× crystallization
× reuse
× failure-information
──────────────────────────────
expected time × risk penalty
```

This favors small tasks that unlock many downstream tasks or can fail informatively early.

It is a transparent heuristic, not a theorem of optimal scheduling.

## Work waves

`plan_waves()` builds dependency-safe finite waves under a supplied worker budget.

No permanent global work-count ceiling exists. Every execution remains finite and is bounded by the actual packet set and the supplied local worker budget.

## Repository Work Digital Twin

`simulate()` executes the WorkHypergraph virtually with a finite worker budget and reports:

- predicted wall time;
- total work seconds;
- critical-path seconds;
- structural/theoretical lower bound;
- utilization;
- speedup relative to serial work;
- scheduling efficiency;
- deterministic completion order.

`adaptive_worker_sweep()` evaluates powers of two and always ends at the actual finite packet count. It does not contain a permanent `MAX_WORKERS` ceiling.

Digital-twin output is prediction until compared with real telemetry.

## WORKMAX telemetry

### Fanout Factor

```text
F_CI = triggered_jobs / impacted_workunits
```

High values identify potential validation amplification. They do not prove waste because required checks and shared invariants may legitimately fan out.

### Closure Ratio

```text
C_R = crystallized_artifacts / started_artifacts
```

### Crystallization Debt

```text
D_cryst = max(0, started_artifacts - crystallized_artifacts)
```

### Generative Leverage

```text
L_G = validated_integrated_artifacts / maintained_manual_lines
```

This is an engineering proxy. It must never reward generated duplication or low-quality artifacts.

### Validated Work Power

```text
P_W = validated_integrated_artifacts × mean_quality / wall_seconds
```

### Evidence Density

```text
E_C = evidence_points / validation_compute_seconds
```

### Queue Waste Ratio

```text
Q_W = obsolete_queue_seconds / total_queue_seconds
```

### Duplicate Work Ratio

```text
D_W = duplicate_work_units / raw_work_units
```

## Crystallization Governor

The governor prevents "MAX" from degenerating into endless branch expansion.

It uses debt **ratios**, not permanent artifact-count ceilings:

- controlled debt → `EXPAND`;
- moderate debt → `BALANCED`;
- high debt → `CRYSTALLIZE`.

`CRYSTALLIZE` prioritizes tests, documentation, APIs, benchmarks, evidence and closure.

The current ratios are control-policy defaults, not universal constants. They must be calibrated against observed repository outcomes.

## Ω-ACTIONS bridge

`omega_workmax_t.actions_bridge` directly reuses `omega_actions_t.trigger_hotspots` from the stacked Ω-ACTIONS branch.

The bridge preserves the stronger Ω-ACTIONS claim boundary:

- trigger frequency is not dependency proof;
- shared trigger removal requires dependency audit;
- PR cumulative-diff contamination must be accounted for;
- required checks, branch protection, security and release semantics override compute savings;
- causal promotion requires comparable before/after evidence.

The initial fixture is intentionally shaped around the current Problem Atlas fan-out experiment from Ω-ACTIONS R0.9–R0.11.

## Ω-SANS-PLAFOND composition

R0.1 does not duplicate `AdaptiveController`.

The intended composition is:

```text
WORKMAX chooses valuable ready work
→ Ω-SANS-PLAFOND chooses locally safe batch/frontier size
→ executor runs a finite batch
→ pressure/quality/evidence return
→ WORKMAX replans
→ M⁺ / M⁻ update
```

This keeps work-value scheduling distinct from physical/resource frontier control.

## Promotion Gate

`decide_promotion()` requires all proof gates:

- coverage preserved;
- required checks preserved;
- permissions non-escalating;
- rollback ready;
- evidence comparable.

Possible outcomes:

- `REJECT_PROOF_GATES`
- `REJECT_REGRESSION`
- `HOLD_NO_MATERIAL_GAIN`
- `PROMOTE_CANDIDATE_FOR_HUMAN_REVIEW`

Even the positive state has:

```text
automatic_merge_authorized = false
```

## CLI

This stacked R0.1 intentionally does **not** add another `pyproject.toml` script entry, because Ω-ACTIONS #367 is currently measuring `pyproject.toml` as a shared trigger-cut hotspot. Use module invocation:

```bash
python -m omega_workmax_t.cli plan \
  examples/omega_workmax_repository_fixture.json \
  --output /tmp/omega-workmax-report.json

python -m omega_workmax_t.cli actions-hotspots \
  --root . \
  --output /tmp/omega-workmax-hotspots.json
```

A console-script surface can be added later through the centralized project-script validator after the fan-out experiment is cleanly measured.

## First falsifiable repository experiment

The first real target is not "generate more modules".

It is the current Ω-ACTIONS finding that shared `pyproject.toml` sensitivity can make unrelated specialized workflow families eligible on a PR.

WORKMAX should ingest:

1. TriggerHotspots;
2. Trigger Dependency Audit;
3. PR-Diff Semantics Gate;
4. completed run/job telemetry;
5. required-check review;
6. a fresh uncontaminated after-witness.

Then compare:

```text
fanout_factor
queue_waste_ratio
wall p95
compute
failure rate
coverage
required checks
rollback readiness
```

before promoting a migration pattern.

The included fixture mirrors this chain:

```text
discover-hotspots
→ dependency-audit
→ trigger-cut-plan
→ fresh-witness
→ promotion-gate
```

Its telemetry numbers are a finite demonstration fixture, not a claim about measured production savings.

## Local R0.1 court before publication

The implementation was executed as a standalone stdlib kernel plus pytest court:

```text
12 focused tests passed
report generation replayed twice byte-identically
SHA-256 report digest produced
adaptive worker sweep ended at the real packet count
promotion remains non-auto-merge
```

These are internal software tests, not independent validation of scheduling superiority.

## OAK boundaries

Ω-WORKMAX-GIT-T∞ R0.1 does **not** claim:

- universal optimal scheduling;
- semantic equivalence from token overlap;
- unlimited physical compute;
- that more workers always help;
- that a simulated speedup is measured speedup;
- that fewer CI jobs are always better;
- that line count equals capability or value;
- that internal tests are independent validation;
- authorization to merge, deploy, publish, spend, expose secrets or perform irreversible actions.

The system optimizes under gates; it does not optimize the gates away.

## Next shards

### R0.2 — live Repository Work Telemetry

Ingest completed Actions run/job evidence and derive fan-out, queue waste, obsolete-run cost and failure-information estimates from immutable run IDs.

### R0.3 — WorkIR / capability compiler

Compile typed WorkPackets from capability contracts, issues, PR deltas, OAK residues and explicit user intent with provenance per inferred field.

### R0.4 — WorkGraph × ΔCI

Build the minimum evidence subgraph for a proposed repository mutation and compare it against the current full fan-out topology.

### R0.5 — Frontier bridge

Connect WorkPacket demand to Ω-SANS-PLAFOND adaptive batching/backpressure without introducing a permanent logical-work ceiling.

### R0.6 — beam / multi-fidelity planner

Use cheap deterministic screens before expensive evidence while measuring both best-score recovery and Pareto recall.

### R0.7 — M⁺/M⁻ scheduling memory

Remember saturations, duplicate plans, regressions, false causal claims and successful topology interventions.

### R0.8 — self-improving scheduler laboratory

Compare scheduler policies against fixed finite scenario suites; generate promotion plans only; never self-edit or self-merge from benchmark output.

### R1 — cross-repository WorkGraph

Use exported capability contracts to route one intent across repositories without copying every capability into one monolith.

## Canonical rules

> GO MAX = maximize validated, distinct, crystallized and reusable work — not raw mutation volume.

> Generate no new work when an existing evidenced capability can satisfy the intent with lower risk and lower total maintenance cost.

> Production rate must not outrun validation absorption rate.
