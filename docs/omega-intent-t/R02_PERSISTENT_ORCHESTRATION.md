# Ω-INTENT-TO-EVERYTHING-T∞ R0.2 — Persistent Orchestration Kernel

## Purpose

R0.2 turns the R0.1 intention compiler into a persistent, resumable and
high-throughput execution substrate.

```text
intent contract
→ persistent work ledger
→ dependency readiness
→ adaptive finite batches
→ executor evidence
→ atomic terminalization
→ artifacts and residuals
→ exact checkpoint
→ completion contract
→ repair intent
→ stacked PR plan
→ differential report
```

The kernel does not claim that arbitrary intentions can be completed
independently, that generated code is correct, or that an unbounded logical
frontier provides unbounded physical resources.

## Persistent ledger

`IntentLedger` uses SQLite with WAL journaling and foreign-key enforcement. It
stores normalized intentions, content-addressed work records, strict states,
checkpoints, artifacts, M-minus residuals, cooperative leases and audit events.

The normal path exposes explicit transitions:

```text
planned → ready → running → validated | rejected | blocked
```

Illegal transitions are rejected. Terminal records are not silently reopened.
Repair or re-execution must be explicit.

## Atomic batch path

The first scale experiment exposed a negative memory:

> M⁻ R0.2-001 — committing several SQLite transactions for every work unit
> prevented the 100k campaign from completing inside the initial two-minute
> experiment window.

The corrected path evaluates a finite batch first, then atomically ingests and
terminalizes the batch in one SQLite transaction. It preserves semantic
deduplication, one terminal audit event per executed record, exact rollback,
content identity, evidence payloads and checkpoint updates after commit only.

## Adaptive capacity

`AdaptiveBudgetController` controls item and byte budgets. It expands only when
a batch is fully consumed while quality, failures, queue delay and memory
pressure remain acceptable. It contracts when a temporary frontier is found.

```text
permanent_total_cap = null
```

Every real run remains finite and constrained by resources, provider quotas,
quality, safety, legality, rollback capacity and human authority.

## Completion contract

Completion is never inferred from line count, additions, artifact count or a
large logical frontier. `CompletionContract` requires explicit closure of
requirements, claim evidence, build and tests, documentation synchronization,
critical risks, benchmark regressions and residuals.

A run may be `in_progress`, `blocked_with_declared_residuals`,
`closed_but_not_validated` or `completed_with_evidence`.

## Repair compiler

`RepairPlanner` classifies syntax, import, schema, test, benchmark, security,
IP, resource and unknown failures. It emits a stable repair action, validation
steps, automatic-candidate status, human gates and a corrective child intention
that preserves the original evidence. Security and IP failures are quarantined
and human-gated by default.

## Stacked PR planning

`StackPlanner` converts a work DAG into deterministic shards bounded by item
count and estimated bytes. It rejects missing dependencies and cycles, preserves
topological levels, separates sensitive work, emits branch dependencies and
reverse rollback order, and performs zero remote GitHub mutations.

## Differential reports

R0.2 compares evidence-bearing metrics between iterations. Additions and bytes
remain neutral volume metrics. They never receive final authority over quality,
validation, risk or usefulness.

## Commands

```bash
omega-intent-r02 manifest
omega-intent-r02 oak --campaign-items 4096
omega-intent-r02 campaign \
  --ledger generated/omega_intent_r02/ledger.sqlite3 \
  --intent-id INTENT-MASS-CAMPAIGN \
  --count 250000
omega-intent-r02 inspect \
  generated/omega_intent_r02/ledger.sqlite3 \
  INTENT-MASS-CAMPAIGN
omega-intent-r02 stack-plan work-units.jsonl
omega-intent-r02 completion completion-contract.json
omega-intent-r02 diff before.json after.json
```

## OAK boundary

A passing R0.2 OAKBench certifies only the included software fixtures:
deterministic identities, ledger persistence, deduplication, illegal-transition
rejection, checkpoints, artifact identity, leases, adaptive budgets, completion
contracts, stack invariants, repair routing, finite campaign accounting, zero
remote mutation and zero automatic merge.

It does not certify generated research claims, theorem proofs, scientific
validity, patentability, arbitrary-code security, product-market fit or
autonomous completion.
