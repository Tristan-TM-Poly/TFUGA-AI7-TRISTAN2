# Ω-ACTIONS-T∞ — R0.8 Guarded AutoActionOptimizer

R0.8 closes the optimization loop without granting the optimizer authority to mutate or merge repository workflows.

## Pipeline

```text
Static ActionGraph
+ empirical telemetry
+ ΔCI evidence
+ CacheTensor
+ historical test timing
        ↓
Evidence Bundle
        ↓
Candidate Generator
        ↓
CI IR candidate
        ↓
Digital Twin
        ↓
compiled YAML candidate
        ↓
non-destructive review/diff
        ↓
before/after experiment
        ↓
OAK Promotion Gate
```

The final repository mutation remains a separate governance action.

## Candidate Generator

`omega_actions_t.auto_optimizer` converts existing evidence into candidate actions such as:

- `ADD_CONCURRENCY_CANDIDATE`;
- `ADD_TIMEOUT_CANDIDATE`;
- `MEASURE_CACHE_VALUE`;
- `RESEARCH_DELTA_ROUTING`.

Every generated action contains:

```json
{
  "automatic_apply": false
}
```

and the candidate manifest itself contains:

```json
{
  "automatic_repository_mutation": false,
  "promotion_required": true
}
```

Broad/unrouted workflows receive a research candidate, never an inferred skip patch.

## Guarded CI-IR variants

R0.8 can also derive a local CI-IR candidate from an explicit baseline IR.

The first automatic transformation is deliberately narrow: add `cancel-in-progress` concurrency to a `pull_request` IR that does not already define concurrency.

It refuses to apply that transform to a non-PR baseline or to overwrite an existing concurrency policy.

```bash
python -m omega_actions_t candidate \
  --ir baseline-ci-ir.json \
  --workflow-path .github/workflows/generated-ci.yml \
  --add-pr-concurrency \
  --out CANDIDATE.json
```

This produces candidate IR + candidate YAML, but it never writes to `.github/workflows`, commits, pushes or merges.

Evidence-only planning is also available:

```bash
python -m omega_actions_t candidate \
  --evidence OMEGA_ACTIONS_EVIDENCE.json \
  --out CANDIDATES.json
```

## Before/after Promotion Gate

`omega_actions_t.promotion` compares empirical telemetry before and after a candidate.

Default quantitative requirements include:

- at least 10 completed runs before;
- at least 10 completed runs after;
- at least 5% p95 duration improvement;
- no failure-rate increase above 2 percentage points.

These defaults are configurable and are not universal scientific constants.

More importantly, four proof gates are required explicitly:

```text
coverage_preserved
required_checks_preserved
permissions_non_escalating
rollback_ready
```

A missing/unknown gate blocks promotion.

A false gate or unacceptable failure-rate regression rejects the candidate.

Possible decisions:

```text
PROMOTE_CANDIDATE
HOLD_NO_MATERIAL_GAIN
INSUFFICIENT_EVIDENCE
REJECT_REGRESSION
```

Even `PROMOTE_CANDIDATE` sets:

```json
{
  "automatic_merge_authorized": false
}
```

Passing the scientific/engineering gate is not equivalent to authorization to merge.

### Example

```bash
python -m omega_actions_t promote \
  before-telemetry.json \
  after-telemetry.json \
  --proof-gates proof-gates.json \
  --out PROMOTION_REPORT.json
```

## Anti-overconfidence invariants

The optimizer must preserve the distinction:

```text
candidate != patch applied
simulation != measurement
correlation != causal attribution
faster != safer
fewer checks != equivalent proof
promotion gate passed != merge authorized
```

## R0.8 state

The executable architecture now spans:

```text
R0.1  static structure
R0.2  telemetry
R0.3  ΔCI
R0.35 evidence fusion
R0.4  sharding / early failure
R0.5  CacheTensor
R0.6  Digital Twin
R0.7  CI IR compiler
R0.8  guarded candidates + Promotion Gate
```

The next engineering phase is no longer primarily adding theory modules. It is collecting real telemetry, obtaining the first completed ΔCI artifact, ranking broad/high-volume workflows and running controlled before/after migrations on the highest-value candidates.
