# Ω-PROPULSION R0.4 — MultiFidelityCampaign-T

## Status

`COMPUTATIONAL_RESEARCH_ARCHITECTURE`

R0.4 adds adaptive evidence-depth campaigns to the R0.1–R0.3 Max stack. It does not add CFD, FSI, certified acoustic prediction, experimental validation or regulatory approval.

## Purpose

R0.3 Max can evaluate complete system candidates, but evaluating every candidate with every scenario is wasteful. R0.4 introduces a governed ladder:

```text
F0_ANALYTIC
  geometry + mass + solidity + disk loading + tip Mach proxies
        ↓ candidate-local promotion
F1_SYSTEM
  structural + acoustic + robust mission + fault envelope
        ↓ candidate-local promotion
F2_STRESS
  expanded uncertainty and fault scenarios using the same low-order models
```

The word *fidelity* refers here to **evidence depth**, not automatically to physical fidelity.

## Central invariants

1. No stage claims physical certification.
2. `F2_STRESS` is not CFD or experiment.
3. The frontier has no encoded permanent cardinality.
4. Every execution receives a finite `ResourceEnvelope`.
5. Consumed cost cannot exceed the envelope.
6. Promotions are candidate-local and deterministic.
7. Every stage emits a SHA-256 evidence event.
8. Shard fusion rejects gaps, overlaps and duplicate candidates.
9. M⁻ records failed regions but never silently creates permanent exclusions.
10. Every report preserves `physics_certified: false`.

## Resource model

The default abstract costs are:

| Stage | Cost units | Meaning |
|---|---:|---|
| F0 | 1 | analytic screening |
| F1 | 24 | complete R0.3 system evaluation |
| F2 | 72 | expanded low-order stress scenarios |

These are relative scheduling weights, not elapsed time or money.

A run can stop because its finite budget is exhausted:

```yaml
resources:
  max_cost_units: 500
  checkpoint_interval: 4
  shard_count: 2
```

This bounds a run without imposing a permanent limit on the frontier.

## Backpressure

The campaign records:

- requested candidates;
- candidates admitted to F0;
- F1 and F2 counts;
- consumed and remaining cost;
- pressure ratio;
- stop reason;
- recommended count for a future run under the same cost envelope.

The recommendation is telemetry, not an autonomous execution order.

## Sharding

A range is partitioned deterministically:

```bash
omega-propulsion-r04 plan-shards \
  --campaign-id demo \
  --start-index 0 \
  --count 1000 \
  --shards 16
```

Each manifest contains:

- campaign ID;
- shard ID;
- start index;
- count;
- exclusive end index;
- SHA-256 seed digest.

Merging requires contiguous, non-overlapping shards from the same campaign.

## Evidence chain

Every candidate can emit up to three events:

```text
(frontier_index, F0_ANALYTIC, hash)
(frontier_index, F1_SYSTEM, hash)
(frontier_index, F2_STRESS, hash)
```

Events are sorted by frontier index and stage order before the global chain is computed. This makes a properly configured sharded campaign equivalent to its unsharded counterpart.

## Negative memory M⁻

M⁻ groups repeated failures by:

- stage;
- violation or rejection reason;
- first and last observed frontier index;
- count;
- sample candidate IDs.

The canonical action is:

> retain as negative evidence; do not convert into an automatic permanent exclusion

This protects the search from both repeated waste and premature dogma.

## CLI

Run the OAKBench:

```bash
omega-propulsion-r04 benchmark
```

Run one finite campaign:

```bash
omega-propulsion-r04 campaign \
  --campaign-id rotor-a \
  --start-index 0 \
  --count 32 \
  --cost-budget 1200 \
  --checkpoint-interval 4 \
  --summary-only
```

Run deterministic shards:

```bash
omega-propulsion-r04 campaign \
  --campaign-id rotor-a \
  --start-index 0 \
  --count 32 \
  --cost-budget 1200 \
  --checkpoint-interval 2 \
  --shards 4 \
  --summary-only \
  --relaxed
```

`--relaxed` exists for deterministic regression and architecture demonstrations. It is not an engineering recommendation.

## OAK status

The target status is:

```text
CERTIFIED_COMPUTATIONAL_ADAPTIVE_MULTIFIDELITY_R0_4
```

This means the software gates for adaptive promotion, resource accounting, M⁻, sharding and evidence continuity passed. It does not certify a rotor, aircraft, ship, material or mission.
