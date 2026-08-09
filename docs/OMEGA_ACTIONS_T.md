# Ω-ACTIONS-T∞ — GitHub Actions Optimization Engine

Ω-ACTIONS-T∞ treats GitHub Actions as a distributed computation graph to optimize under proof, safety, reproducibility, latency and compute constraints.

## Objective

The target is not maximum parallelism. It is maximum validated information per unit of wall-clock time and compute:

\[
\eta_{CI} = \frac{I_{validated}R_{confidence}}{T_{wall}C_{compute}(1+W_{redundant})}.
\]

The implementation in `omega_actions_t` is currently a **static structural analyzer**. It is intentionally read-only and stdlib-only. Its outputs are optimization hypotheses, not measured performance claims.

## Current executable layer

Run:

```bash
omega-actions --root . --format summary
omega-actions --root . --json-out ACTIONS_REPORT.json --markdown-out ACTIONS_REPORT.md
```

The analyzer scans `.github/workflows/**/*.yml|yaml` and builds a structural representation containing:

- workflow triggers;
- jobs and `needs` dependencies;
- runner labels;
- `timeout-minutes`;
- path-filter entries;
- matrix axes and `max-parallel` signals;
- dependency-install signals;
- cache signals;
- artifact upload/download signals;
- explicit permissions;
- concurrency cancellation signals;
- exact behavior-signature groups;
- near-duplicate workflow pairs by Jaccard similarity.

## Structural critical path

For each workflow, jobs form a DAG approximation. With unit job weights, the analyzer computes the longest dependency depth:

\[
D(W)=\max_{p\in\mathcal P}|p|.
\]

This is **not** a wall-clock critical path. Future telemetry layers will replace unit weights with measured queue/setup/compute/upload durations.

## Static Action Efficiency proxy

The v1 score combines a validation proxy, runtime-bounding coverage and structural waste indicators. It is bounded for ranking and regression detection only.

It must never be presented as actual CI speedup. Real claims require before/after run telemetry.

## Optimization detectors

### Cancel obsolete runs

Triggered when a push/PR workflow lacks top-level `concurrency`. Recommendation: group by workflow/ref and evaluate `cancel-in-progress` so superseded commits do not consume compute unnecessarily.

### Cache installation work

Triggered when dependency-install commands are detected without cache signals. Cache is recommended only after measuring restore/save overhead against avoided installation time.

### Bound runtime

Jobs without `timeout-minutes` are surfaced because hung work has unbounded compute cost.

### Adaptive matrices

Matrices without `max-parallel` are surfaced for measurement. Ω-SANS-PLAFOND-T applies: no arbitrary global ceiling; increase parallelism while marginal speedup justifies queue, runner, cost and contention effects.

### Artifact-flow review

Repeated upload/download stages are flagged for comparison against job fusion or recomputation.

### Least privilege

Workflows without explicit `permissions` are surfaced for OAK review.

### ΔCI entry filtering

Push/PR workflows without path filters are surfaced as candidates for path filtering or a dynamic impact-analysis gate. Required-check semantics must be preserved.

### Workflow-family consolidation

Exact and high-similarity workflow behavior signatures are used to identify candidates for reusable workflows, composite actions, generated matrices or a future CI intermediate representation.

No workflow is deleted or rewritten automatically.

## Architecture roadmap

### R0.1 — Static analyzer — implemented here

`YAML -> structural DAG -> findings -> JSON/Markdown evidence`

### R0.2 — Run telemetry

Ingest GitHub run/job/step telemetry:

`queue + setup + download + compute + upload -> empirical job cost`

Derive measured critical paths, p50/p95 durations, failure location, queue saturation and obsolete-run compute.

### R0.3 — Historical test sharding

Persist per-test durations and build balanced shards:

\[
\min \max_j \sum_{i\in S_j} t_i.
\]

### R0.4 — Bayes-CI-T

Estimate failure probability conditioned on changed files, subsystem, test and history; run high-value early-failure checks first while retaining exhaustive recalibration lanes.

### R0.5 — CacheTensor-T

Measure:

\[
V_k=P(hit_k)T_{saved}-T_{restore}-T_{save}.
\]

Caches with negative empirical value become removal candidates.

### R0.6 — CI Digital Twin

Replay historical workloads against candidate DAGs, shard counts, runner classes, matrices and cache policies before editing production workflows.

### R0.7 — CI Intermediate Representation

Move from hand-maintained YAML families to:

`intent -> CI IR -> optimizer -> generated GitHub Actions -> OAK validation`.

### R0.8 — AutoActionOptimizer-T

Generate candidate patches/PRs with explicit predicted deltas and require measured before/after evidence before promotion.

## OAK invariants

1. Static similarity never authorizes deletion.
2. A predicted speedup is not a measured speedup.
3. Required checks, branch protection and security boundaries have priority over compute savings.
4. Caches never contain secrets.
5. Token permissions remain least-privilege.
6. Generated workflow edits require reproducible diff, rollback path and CI evidence.
7. Exhaustive/nightly/release validation remains available to detect errors hidden by adaptive PR sampling.
8. Optimization must track proof debt: faster but less trustworthy is a regression.

## Initial integration with Action Dashboard

`omega_actions_t` complements `tools/action_dashboard`:

- Action Dashboard answers **what exists and what should happen next**;
- Ω-ACTIONS-T∞ answers **how efficiently GitHub Actions validate it**.

The intended next fusion is:

`Action Dashboard snapshot + GitHub run telemetry + Ω-ACTIONS-T∞ report -> OAK Action Dashboard`.
