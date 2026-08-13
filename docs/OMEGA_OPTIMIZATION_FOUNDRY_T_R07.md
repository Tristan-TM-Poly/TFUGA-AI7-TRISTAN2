# Ω-OPTIMIZATION-FOUNDRY-T∞ — R0.7

Status: **D-MVP candidate / R0.7**. Optimization-discovery and evidence-planning layer. No automatic source rewriting or arbitrary target-code execution.

## 1. Goal

R0.7 changes the question from:

```text
which function looks expensive?
```

to:

```text
which opportunity is worth measuring?
-> which measured bottleneck is worth changing?
-> which transformation hypothesis should compete?
-> which measured result should be retained as transferable evidence?
-> where should that evidence be tested next?
```

The core invariant is:

```text
hotspot != optimization opportunity
candidate patch != improvement
measured local gain != transferable truth
```

## 2. Opportunity Engine

`omega_compute_physics_t/opportunity_engine.py`

`OpportunityEvidence` separates signals that matter for measurement from signals that matter for optimization:

- static complexity hint;
- graph centrality;
- usage weight;
- measured regression signal;
- expected-savings prior;
- confidence debt;
- engineering effort;
- benchmark cost.

Two scores are emitted:

```text
measurement_priority
optimization_priority
```

High confidence debt routes the candidate to `remeasure-first` even when its nominal optimization value is large.

OAK: these scores prioritize work. They do not prove a bottleneck, speedup, causal mechanism or realized ROI.

## 3. Transformation Algebra

`omega_compute_physics_t/transformation_algebra.py`

R0.7 represents optimization ideas as typed transformation specifications rather than free-form rewrites. The canonical planning library includes:

- preallocate;
- reuse-buffer;
- eliminate-copy;
- layout-reorder;
- loop-fusion;
- loop-tiling;
- vectorize;
- batch;
- parallelize;
- memoize;
- sparsify;
- change-algorithm.

A `TransformationProgram` composes these hypotheses while preserving preconditions, expected effects and risk labels.

OAK: composition is a plan, not semantic preservation or measured improvement.

## 4. Optimization Arena

`omega_compute_physics_t/optimization_arena.py`

Measured variants compete against an explicit baseline on a user-supplied resource vector. Directions are explicit (`minimize` or `maximize`).

The arena:

- rejects correctness-failed variants from eligibility;
- computes a finite-domain utility relative to the baseline;
- computes a Pareto front over supplied metrics;
- reports a best eligible measured variant.

OAK: an arena winner is conditional on the measured domain, metrics, confidence and supplied risk. It is not globally or asymptotically optimal.

## 5. Optimization Genome and transfer

`omega_compute_physics_t/optimization_genome.py`

A successful measured experiment can be retained as an `OptimizationGene`:

```text
source repository/node
+ transformation ids
+ workload context vector
+ measured gain
+ domain
+ hardware id
+ evidence level
```

`rank_transfer_candidates(...)` compares a gene with destination workload signatures using cosine similarity. Similarity increases experimental priority only.

OAK:

```text
similar workload
!= equivalent semantics
!= reproduced speedup
```

Every transferred candidate must be revalidated.

## 6. Optimization Credit Ledger

`omega_compute_physics_t/optimization_credit.py`

When multiple transformations are tested through controlled ablations, R0.7 can compute exact Shapley attribution for small transformation sets.

This separates:

```text
combined observed gain
```

from:

```text
marginal contribution under the supplied coalition value function
```

Exact enumeration is intentionally capped at eight transformations.

OAK: Shapley attribution explains the supplied measured value function; it is not automatically a mechanistic causal explanation.

## 7. Bottleneck Dynamics

`omega_compute_physics_t/bottleneck_dynamics.py`

Optimization often moves the limiting resource instead of eliminating all limits:

```text
CPU -> memory -> synchronization -> communication
```

`trace_bottleneck_migration(...)` stores the dominant measured resource signal across revisions and counts migrations.

OAK: dominant measured share is an operational bottleneck signal, not a conservation law or causal proof.

## 8. Optimization Portfolio

`omega_compute_physics_t/optimization_portfolio.py`

For a bounded candidate set, R0.7 can allocate a finite engineering-effort budget over optimization opportunities. Each opportunity supplies:

- expected value proxy;
- effort cost;
- success probability.

Pairwise interactions model synergy or cannibalization:

```text
I(a,b) > 0  synergy
I(a,b) < 0  overlap/cannibalization
```

The current solver performs exact subset enumeration with an explicit combinatorial guard of 18 candidates.

OAK: exact selection is exact only for the supplied finite set and supplied estimates. It is not guaranteed realized engineering or financial return.

## 9. R0.7 CLI

`omega_compute_physics_t/r07_cli.py`

Static/planning commands:

```bash
python -m omega_compute_physics_t.r07_cli opportunity opportunity.json
python -m omega_compute_physics_t.r07_cli portfolio portfolio.json
python -m omega_compute_physics_t.r07_cli credit ablations.json
```

No command in this CLI rewrites or executes arbitrary target repository code.

## 10. Evidence schema

`complexity_atlas/evidence_schema_v0_7.json`

Portable evidence kinds include:

- optimization opportunity;
- transformation spec/program;
- arena;
- optimization gene;
- transfer candidate;
- credit attribution;
- bottleneck dynamics;
- optimization portfolio.

Schema validity is not scientific or software-performance truth.

## 11. Fleet optimization loop

The intended fleet loop becomes:

```text
repository@commit
-> Snapshot / Complexity-IR / CallGraph
-> Change Impact / Confidence Debt
-> Opportunity Engine
-> Benchmark Contract
-> reviewed measured baseline
-> bottleneck evidence
-> Transformation Program candidates
-> measured Optimization Arena
-> credit attribution / residuals
-> Optimization Gene M+ or failure M-
-> transfer candidates across fleet
-> portfolio reprioritization
```

This converts isolated optimizations into cumulative cross-repository evidence.

## 12. Optimization proof ladder

R0.7 uses the following promotion semantics:

- L0 — intuition;
- L1 — static opportunity candidate;
- L2 — controlled microbenchmark;
- L3 — held-out workload result;
- L4 — end-to-end improvement;
- L5 — multi-machine replication;
- L6 — mechanistic explanation supported by intervention/counters;
- L7 — algorithmic bound;
- L8 — formal proof.

No level is automatically promoted to the next.

## 13. M+ / M- memory

M+ should retain successful optimization genes with full context.

M- should retain failures with the same context:

```text
transformation
+ workload genome
+ machine
+ domain
+ failure mode
+ residual
```

A failed transformation in one regime is not globally forbidden; it becomes negative transfer evidence for similar regimes.

## 14. Highest-value R0.8 frontier

1. build opportunity rows automatically from RepositoryGenome + CallGraph + RegressionLedger + ConfidenceDebt;
2. ingest the full pinned six-repository Git trees and emit a real fleet-wide Top-N optimization candidate report;
3. infer transformation preconditions from static IR while keeping them hypotheses;
4. connect an explicitly authorized isolated Stage B runner for pure deterministic kernels;
5. measure baseline/variant ResourceSamples and populate the first Optimization Arena from real code;
6. write measured M+/M- optimization genes into a temporal fleet ledger;
7. learn transfer success/failure priors by workload family and MachineGenome;
8. learn benchmark half-life and transformation priors from accumulated evidence;
9. add robust-regime and fragility scoring for speedups across input domains;
10. generate review-ready patch candidates only after measurement has identified a target and a transformation hypothesis.

## 15. Hard boundaries

R0.7 does not claim:

- static hotspot == runtime hotspot;
- opportunity score == obtainable speedup;
- transformation spec == correct patch;
- arena winner == universal winner;
- Shapley credit == mechanistic causality;
- workload similarity == semantic equivalence;
- transferred gene == reproduced gain;
- bottleneck migration == conservation principle;
- portfolio value == realized money;
- empirical improvement == asymptotic complexity theorem.

Those boundaries are part of the design.
