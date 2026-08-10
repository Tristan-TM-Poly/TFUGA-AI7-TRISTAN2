# Ω-WORKMAX-GIT-T∞ R0.6–R0.8

Status: **offline optimization laboratory / promotion-plan-only / OAK review required**

## R0.6 — Beam × Multi-Fidelity Work Search

`omega_workmax_t.search_lab` evaluates a finite candidate set through ordered fidelity stages.

At each stage:

1. only candidates with declared metrics for that stage are evaluated;
2. a transparent safety-adjusted score ranks candidates;
3. the finite beam width retains survivors;
4. the final stage is compared against the complete declared final-stage table.

The report includes:

- evaluated cells;
- full-grid cells;
- evaluation reduction;
- exhaustive best;
- beam best;
- best-score ratio;
- score regret;
- exhaustive Pareto set;
- Pareto recall.

This preserves the key lesson from earlier HMAGFM beam experiments: recovering the scalar best is not equivalent to preserving useful diversity.

## R0.7 — Scheduling Memory M⁺/M⁻

`omega_workmax_t.scheduling_memory` stores deterministic scheduling-memory events.

Each event binds:

- M⁺ or M⁻;
- event ID;
- policy fingerprint;
- context fingerprint;
- observation;
- evidence references;
- metric deltas;
- mitigation;
- reproducibility state.

Exact duplicate events are rejected. A reproducible M⁻ can block automatic repetition of the same policy/context until counter-evidence is accumulated.

The ledger is append-only by convention and can emit deterministic JSON/JSONL.

## R0.8 — Scheduler Policy Lab

`omega_workmax_t.policy_lab` compares finite outcomes for an incumbent and candidate policies.

A candidate is promotion-eligible only when, across supplied scenarios:

- all scenarios complete;
- mean evidence coverage is not worse;
- mean closure ratio is not worse;
- total regressions do not increase;
- wall-time improvement exceeds the declared threshold.

Eligible candidates are then ordered by:

1. improvement ratio;
2. lower fan-out;
3. lower risk;
4. deterministic policy ID.

Even a winning candidate returns only:

`PROMOTE_CANDIDATE_FOR_HUMAN_REVIEW`

with:

- `requires_human_approval=true`;
- `automatic_source_mutation=false`;
- `automatic_merge_authorized=false`.

## CLI

```bash
python -m omega_workmax_t.cli beam-search examples/omega_workmax_beam_r06.json
python -m omega_workmax_t.cli policy-lab examples/omega_workmax_policy_lab_r08.json
```

## OAK boundaries

- Search quality depends on supplied stages and metrics.
- Beam pruning can discard superior late-fidelity candidates.
- Pareto recall must be measured separately from best-score recovery.
- Scheduling memory is evidence bookkeeping, not causal proof.
- The policy lab cannot promote a policy by sacrificing evidence or closure.
- No source mutation, branch update, merge, deployment or publication is authorized by R0.6–R0.8.

## Next

R1 should connect the same WorkIR/capability/evidence semantics across multiple repositories and use immutable repository/head identities to avoid cross-repository state confusion.
