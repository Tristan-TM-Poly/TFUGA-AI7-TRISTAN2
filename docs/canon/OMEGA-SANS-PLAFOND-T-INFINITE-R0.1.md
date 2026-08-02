# Ω-SANS-PLAFOND-T∞

## Architecture d’itération asymptotiquement non bornée de Tristan — R0.1

Status: **coded control prototype / deterministic stress harness / not infinite physical computation**.

## Directive

Ω-SANS-PLAFOND-T∞ rejects permanent arbitrary addition limits such as:

```python
MAX_ADDITIONS = 1200
```

The controller instead seeks the current measurable capacity frontier, records each saturation in negative memory M⁻, applies or requests an architectural redesign, replays the atomic workload, and repeats.

```text
SCOUT → RAMP → SATURATE → M⁻ → REDESIGN → REPLAY → BREAKTHROUGH → REPEAT
```

The global objective is not bounded by a permanent integer. Each concrete run remains bounded by its finite workload, physical resources, recoverability, quality gates, cost, legal constraints, and external service rules.

## Formal distinction

Global direction:

\[
\lim_{t\to\infty} N_{\mathrm{integrated}}(t)=+\infty
\]

Local execution:

\[
N_t \leq C_t
\]

where the observed capacity vector is dynamic:

\[
C_t=(C_{CPU},C_{RAM},C_{disk},C_{network},C_{API},C_{Git},C_{CI},C_{validation},C_{cost})
\]

`C_t` is not canonized as a permanent maximum. It is an experimental frontier to surpass.

## R0.1 executable kernel

The package `omega_unbounded_t` contains:

- `AdaptiveController`: increases requested batch size after healthy runs;
- `CapacityPolicy`: quality and pressure rules, but no permanent addition cap;
- `ListWorkSource`: finite, replayable, atomic work source;
- `MMinusLedger`: append-only JSONL saturation memory;
- `CheckpointWriter`: atomic recoverability snapshot;
- `SyntheticCapacityExecutor`: deterministic frontier and redesign simulator;
- `omega-unbounded simulate`: offline command-line stress harness.

## State transition

```text
PENDING
  ↓
EXECUTED
  ├─ healthy → ACCEPTED → CHECKPOINT → GROW
  └─ saturated → REQUEUED → M⁻ → REDESIGN
                                   ├─ available → REPLAY
                                   └─ absent → PAUSE_REQUIRES_REDESIGN
```

A failed batch is never silently discarded. It is requeued before redesign.

## Healthy batch invariant

A batch is accepted only when:

1. it is recoverable;
2. it reports no failed items;
3. every requested item is accounted for as accepted, rejected, or duplicate;
4. quality remains above the policy floor;
5. peak pressure remains below the hard pressure frontier.

The current implementation intentionally fails closed.

## Adaptive growth

After a stable low-pressure batch:

\[
B_{t+1}=\max(B_t+1,\lfloor g_s B_t\rfloor)
\]

Near the pressure frontier:

\[
B_{t+1}=\max(B_t+1,\lfloor g_c B_t\rfloor),\quad 1<g_c<g_s
\]

The growth factors are control parameters, not capacity ceilings.

## Negative-memory event

Every saturation records:

- event identifier and UTC timestamp;
- iteration and requested batch;
- last safe batch;
- limiting dimensions;
- peak pressure;
- quality score;
- recoverability;
- diagnostic notes.

Example:

```json
{
  "event_id": "M-...",
  "requested_batch": 2048,
  "last_safe_batch": 1024,
  "limiting_dimensions": ["memory"],
  "recoverable": true,
  "status": "observed"
}
```

Future versions should add root-cause hypotheses, reproduction commands, attempted mitigations, evidence, new frontier measurements, and canonization status.

## Run the prototype

```bash
python -m pytest tests/test_omega_unbounded_t.py
python examples/omega_unbounded_t_demo.py
omega-unbounded simulate \
  --work-items 50000 \
  --initial-batch 256 \
  --initial-capacity 1024 \
  --redesign-factor 2 \
  --output-dir generated/omega_unbounded_t
```

Outputs:

```text
generated/omega_unbounded_t/
├── checkpoint.json
├── m_minus.jsonl
└── report.json
```

The synthetic executor does not claim GitHub itself can accept an unlimited mutation. It proves the controller semantics offline before integration with real adapters.

## GitHub scaling architecture

A production GitHub adapter should distinguish logical additions from Git objects:

```text
micro-additions → semantic shards → validated manifests → atomic commits → pull request
```

Tens of thousands of logical additions should not automatically become tens of thousands of files or commits. Production scaling requires:

- deterministic IDs and content hashes;
- exact and semantic deduplication;
- append-only event storage;
- dynamic sharding;
- dependency-aware validation;
- semantic diffs;
- bounded atomic commits;
- rollback manifests;
- Git LFS, Releases, object storage, or databases for large artifacts;
- code/data/control-plane separation;
- respectful API batching, caching, retry, and backoff.

## OAK boundaries

Ω-SANS-PLAFOND-T∞ does **not** mean:

- infinite work in finite time;
- bypassing GitHub or provider quotas;
- uncontrolled recursive generation;
- accepting unverified claims for volume;
- removing safety, provenance, IP, or human-approval gates;
- declaring one successful stress run a proven universal capacity.

A frontier is considered surpassed only after the old failure is reproducible, the cause is characterized, a structural intervention is implemented, the larger workload succeeds repeatedly, quality is preserved, and rollback remains verified.

## Canonical metrics

Every production iteration should report:

- raw, unique, validated, integrated, and reused additions;
- duplicate and rejection rates;
- test and provenance coverage;
- cost and time per valid addition;
- largest reliably observed safe batch;
- active limiting dimension;
- saturation and redesign counts;
- M⁻ events and M⁺ breakthroughs;
- remaining review and validation debt.

The correct phrase is:

> largest reliably observed frontier

not:

> maximum possible capacity

## R0.2 roadmap

1. Real streaming work-source interface.
2. Resource sampler for CPU, RAM, disk, latency, and queue pressure.
3. GitHub dry-run adapter producing trees and semantic commit plans.
4. Dynamic shard planner and dependency graph.
5. M⁺ breakthrough ledger paired with M⁻.
6. Reproducible frontier experiments and Pareto comparisons.
7. CI matrix generation and differential test routing.
8. Resume-from-checkpoint state restoration.
9. Human approval gates for publication, deletion, spending, secrets, and IP.
10. Bayes-Tristan frontier prediction and OAK promotion states.

## Canonical rule

> No arbitrary permanent `max_ajout`. Every encountered limit must be observed, measured, stored in M⁻, attacked architecturally, retested, and either surpassed or honestly retained as an unresolved frontier.
