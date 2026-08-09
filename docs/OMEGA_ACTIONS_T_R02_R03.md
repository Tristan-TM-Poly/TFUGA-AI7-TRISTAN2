# Ω-ACTIONS-T∞ — R0.2 Telemetry + R0.3 ΔCI

This document crystallizes the second executable wave of Ω-ACTIONS-T∞.

## State machine

```text
R0.1 static YAML structure
    -> R0.2 empirical run/job telemetry
    -> R0.3 conservative delta-impact routing
    -> R0.35 evidence fusion / prioritization
    -> R0.4 historical test sharding + early failure ordering
    -> R0.5 CacheTensor empirical value
    -> R0.6 CI Digital Twin
    -> R0.7 CI IR / workflow compiler
    -> R0.8 guarded candidate-patch generation
```

## R0.2 — Empirical telemetry

`omega_actions_t.telemetry` ingests exported GitHub Actions JSON and derives:

- run count and active/completed state;
- p50/p95/mean/max queue latency;
- p50/p95/mean/max run duration;
- per-workflow duration and failure rate;
- per-job duration and failure localization;
- superseded active runs for the same workflow/branch;
- empirical recommendations for cancellation, queue/fan-out pressure and failure localization.

The package itself remains network-free. `.github/workflows/omega-actions-telemetry.yml` is the read-only collection layer. It has only `contents: read` and `actions: read`, collects at most 100 recent runs, enriches the selected runs with job/step metadata, analyzes them locally and uploads a 14-day evidence artifact.

The scheduled sample is intentionally bounded. Ω-SANS-PLAFOND-T applies to architecture evolution, not to uncontrolled API consumption.

### Telemetry CLI

```bash
python -m omega_actions_t telemetry OMEGA_ACTIONS_TELEMETRY_INPUT.json \
  --json-out OMEGA_ACTIONS_TELEMETRY.json \
  --markdown-out OMEGA_ACTIONS_TELEMETRY.md
```

## R0.3 — ΔCI / Impact Routing

`omega_actions_t.delta_ci` parses the common GitHub `paths` / `paths-ignore` trigger subset and classifies workflows for a concrete change set.

Decisions are deliberately asymmetric:

- `RUN_EXPLICIT_PATH_MATCH` — explicit evidence to run;
- `SKIP_EXPLICIT_PATH_FILTER` — explicit evidence to skip;
- `SKIP_ALL_PATHS_IGNORED` — explicit evidence to skip;
- `RUN_PATHS_IGNORE_FALLTHROUGH` — at least one changed path remains relevant;
- `RUN_WORKFLOW_SELF_CHANGE` — the workflow itself changed;
- `RUN_BROAD_UNROUTED` — workflow listens to the event without explicit impact routing;
- `OUT_OF_SCOPE_EVENT` — workflow does not listen to the audited event.

The key OAK rule is:

> `RUN_BROAD_UNROUTED` is never converted into a skip merely because a heuristic believes the workflow is unrelated.

Only explicit routing semantics create a `safe_skip` classification.

### ΔCI CLI

```bash
python -m omega_actions_t delta --root . \
  --changed-files OMEGA_CHANGED_FILES.txt \
  --json-out OMEGA_ACTIONS_DELTA.json \
  --markdown-out OMEGA_ACTIONS_DELTA.md
```

`.github/workflows/omega-actions-delta-audit.yml` runs read-only on pull requests, obtains the changed-file list from GitHub, generates the impact report and exposes broad/unrouted workflows in the job summary.

## R0.35 — Evidence Bundle

`omega_actions_t.evidence` fuses the three representations:

```text
Static WorkflowGraph
        +
Delta ImpactGraph
        +
Empirical TelemetryGraph
        -> Evidence Bundle
        -> ranked optimization targets
```

For each workflow it combines:

- observed sample frequency;
- observed p95 duration;
- observed failure rate;
- broad/unrouted status;
- static recommendation count;
- structural DAG depth.

The resulting `priority_score` is only a ranking heuristic. It is not a promised speedup.

```bash
python -m omega_actions_t evidence --root . \
  --changed-files OMEGA_CHANGED_FILES.txt \
  --telemetry OMEGA_ACTIONS_TELEMETRY_INPUT.json \
  --json-out OMEGA_ACTIONS_EVIDENCE.json \
  --markdown-out OMEGA_ACTIONS_EVIDENCE.md
```

Evidence states:

- `STATIC_ONLY`;
- `STATIC_PLUS_DELTA`;
- `STATIC_PLUS_TELEMETRY`;
- `MEASURED_BASELINE_READY`.

Even at `MEASURED_BASELINE_READY`, automatic rewriting remains false. Promotion requires comparable before/after samples.

## First empirical proof from PR #367

The first `Ω Actions Optimizer CI` run on the branch was superseded by later commits and GitHub recorded it as `cancelled`. This is the expected behavior of its `concurrency` / `cancel-in-progress` policy and constitutes a concrete example of obsolete-run suppression.

By contrast, the same PR head has repeatedly produced a large fan-out of unrelated or apparently unrelated workflows. R0.3 exists to quantify which of those workflows already have explicit routing evidence and which are still broad/unrouted.

## OAK promotion gates

No trigger topology change should be promoted without checking:

1. branch-protection required checks;
2. required-check pending semantics;
3. reusable workflow dependencies;
4. release/security workflows;
5. self-validation of modified workflow files;
6. global dependency/build files;
7. before/after queue and duration samples;
8. rollback path.

The optimization target remains:

```text
less redundant compute
+ shorter critical path
+ faster failure discovery
+ equal or stronger proof
```

not merely fewer Actions.
