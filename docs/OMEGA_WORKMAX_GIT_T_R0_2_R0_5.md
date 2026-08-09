# Ω-WORKMAX-GIT-T∞ R0.2–R0.5

Status: **stacked research-software increment / OAK review required / no auto-merge**

Base stack: Ω-WORKMAX R0.1 on Ω-ACTIONS-T∞ PR #367.

## R0.2 — Immutable GitHub Actions telemetry

`omega_workmax_t.github_telemetry` ingests finite exported GitHub run/job payloads and emits a deterministic evidence snapshot bound to immutable IDs and head SHAs.

It records run/job counts, active/queued/completed/cancelled states, queue and execution timing distributions when timestamps exist, workflow counts, exact run identities, job IDs, head SHAs and a content digest.

It performs no network access and cannot mutate GitHub.

A queued snapshot establishes only the observed queue state. It is not a long-term latency estimate and is not causal proof of a topology speedup.

## R0.3 — WorkIR compiler

`omega_workmax_t.work_ir` compiles a finite intent packet together with:

- changed files;
- GitHub issues;
- capability contracts;
- OAK residues;

into deterministic `WorkPacket` objects.

Changed files are grouped by repository component, capability reuse is represented explicitly, OAK residues can block downstream integration, and a final crystallization/integration packet depends on all finite source packets.

The compiler structures declared work. It does not claim that the input list is exhaustive.

## R0.4 — WorkGraph × ΔCI evidence subgraph

`omega_workmax_t.evidence_subgraph` consumes an Ω-ACTIONS ΔCI report.

Rules:

1. required workflows are always selected;
2. explicit path matches and workflow-self changes are selected;
3. broad or otherwise runnable workflows stay selected until stronger dependency evidence exists;
4. safe explicit skips remain visible;
5. automatic skip and automatic merge remain unauthorized.

Therefore `minimum` means **proof-preserving under currently available routing evidence**, not a universal graph-theoretic minimum.

## R0.5 — Validation-absorption backpressure

`omega_workmax_t.frontier_bridge` compares generation rate with validation absorption together with queue count, closure ratio, fan-out and queue-waste signals.

Possible modes:

- `GROW_AT_OBSERVED_FRONTIER`;
- `HOLD_OR_CAUTIOUS_GROWTH`;
- `THROTTLE_AND_CRYSTALLIZE`.

The controller changes the admitted fraction of new work but defines no permanent global work-count ceiling.

Canonical law:

\[
R_{\mathrm{generation}} \leq R_{\mathrm{validation}}
\]

when validation is the active bottleneck.

This does not mean queues are always bad. It means an observed validation bottleneck should create backpressure rather than uncontrolled source expansion.

## First real queue snapshot

The included `examples/omega_workmax_github_snapshot_pr370.json` binds the initial PR #370 observation:

- exact head SHA `1feb82827307d4f83d6cbc9ae1164cf229cec000`;
- three PR-triggered workflow runs;
- three corresponding jobs;
- all three observed queued at the captured snapshot;
- no causal speedup claim.

The snapshot is evidence input, not a live collector.

## CLI

```bash
python -m omega_workmax_t.cli telemetry examples/omega_workmax_github_snapshot_pr370.json
python -m omega_workmax_t.cli workir examples/omega_workmax_workir_r03.json
python -m omega_workmax_t.cli evidence-subgraph /path/to/input.json
python -m omega_workmax_t.cli backpressure /path/to/state.json
```

No new `pyproject.toml` console entry is added in this stacked increment.

## OAK boundaries

R0.2–R0.5 do not establish:

- universal optimal scheduling;
- causal CI speedup;
- semantic independence of broad workflows;
- a permanent GitHub capacity;
- authorization to remove required checks;
- authorization to merge/deploy/publish;
- that one queued snapshot is a stable latency distribution.

## Next

R0.6 should add beam + multi-fidelity plan search with explicit regret and Pareto-recall measurements. R0.7 should add scheduling M⁺/M⁻ memory. R0.8 should compare scheduler policies offline and emit promotion plans only.
