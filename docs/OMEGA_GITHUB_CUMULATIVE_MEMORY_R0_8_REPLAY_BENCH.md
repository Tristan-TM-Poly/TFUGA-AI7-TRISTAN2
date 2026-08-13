# Ω-GITHUB-CUMULATIVE-MEMORY-T∞ — R0.8 Decision Replay / Reuse Bench

## Mission

R0.8 is the first deliberately experimental generation after the R0.1→R0.7 architecture.

It asks a narrower question:

```text
Does cumulative GitHub memory recover declared prior work
and reduce the capability residual before new generation?
```

It does **not** assume that a smaller residual means fewer LOC, less time, fewer
defects, lower maintenance cost, or causal engineering advantage.

The benchmark reuses the doctrine of the existing GreatSages / Tensor
DiscoveryBench work: same evidence boundary, explicit baselines, separated
metrics, contamination accounting, deterministic fixtures, and no scalar
"intelligence" claim.

## Court A — controlled policy replay

The CREATE-first baseline is:

```text
requested outputs → all new
```

The reuse-first policy is:

```text
CapabilityRequest
→ ReuseBeforeCreateGate
→ REUSE | COMPOSE | EXTEND | INSPECT | CREATE
→ residual outputs
```

R0.8 measures only:

```text
output_token_avoidance_fraction
=
(requested output tokens - residual output tokens)
/
requested output tokens
```

Three deterministic controls are mandatory:

| Case | Expected action | Expected token avoidance |
|---|---:|---:|
| complete existing capability | `REUSE` | 1.0 |
| partial existing capability | `EXTEND` | 0.5 |
| no prior capability | `CREATE` | 0.0 |

This validates the benchmark harness and the minimal-residual semantics. It is
not evidence of real-world productivity gains.

## Court B — historical lineage replay

For each historical PR with explicit past lineage such as:

```text
reuses: #417
extends: #414
derived_from: #443
```

R0.8 constructs a prefix memory containing only lower-numbered PRs from the
same repository.

The target PR and all later PRs are hidden.

The retrieval query uses **target title only**. The target body is not given to
the retriever; it is used only afterward to define post-hoc gold lineage labels.

```text
prior PRs only
+ target title
→ search_prs(top_k)
→ recovered explicit ancestors
```

Metrics:

- eligible target count;
- explicit lineage reference count;
- micro recall@k;
- macro recall@k;
- fraction of prior PRs that had to be inspected;
- target leakage count;
- future leakage count.

The replay fails OAK if target or future PRs leak into retrieval.

## Why PR number, not `updated_at`

`updated_at` can change because of later comments, reviews, metadata edits or
synchronization. PR number is used as a stable creation-order proxy inside one
repository.

This is still not an exact historical context reconstruction.

## Contamination tensor / boundary

The historical court declares:

```text
query_uses_target_title_only = true
target_body_used_as_gold_only = true
target_pr_hidden_from_retrieval = true
future_prs_hidden_from_retrieval = true
pretraining_exposure = unknown
historical_metadata_fidelity = current_snapshot_proxy
```

Therefore:

```text
LINEAGE_RECALL != ALL_REUSE_RECALL
CURRENT_PR_METADATA != EXACT_HISTORICAL_CONTEXT
REPLAY_ADVANTAGE != CAUSAL_ENGINEERING_ADVANTAGE
```

Explicit lineage is an incomplete gold set. A retrieved PR may be genuinely
useful without being named in the target body, so R0.8 does not interpret
unlabeled retrievals as false positives.

## CLI

```bash
python -m omega_capability_os_t.github_memory_replay policy \
  MEMORY.json REQUEST.json

python -m omega_capability_os_t.github_memory_replay historical \
  MEMORY.json --top-k 8

python -m omega_capability_os_t.github_memory_replay court \
  MEMORY.json --top-k 8
```

## Passive live court

`.github/workflows/github-reuse-bench-oak.yml` is read-only:

```text
contents: read
pull-requests: read
```

It refreshes all PR metadata, runs the R0.8 court, verifies zero temporal
leakage, and uploads the replay receipt.

It performs no push, merge, comment, publication, permission widening or
canonical state mutation.

## Promotion gate toward stronger claims

R0.8 can justify a stronger R0.9 experiment only after it accumulates real
evidence.

A later engineering-effect benchmark should add measurements such as:

```text
new LOC
modified LOC
test failures
regressions
CI attempts
context tokens
wall-clock development steps
maintenance events
```

and compare matched tasks or randomized/controlled policies where feasible.

Until then:

```text
OUTPUT_TOKEN_AVOIDANCE != LOC_OR_TIME_SAVED
BENCHMARK_PASS != EXTERNAL_WORLD_TRUTH
```

The purpose of R0.8 is to convert "reuse-first should help" into a falsifiable,
repeatable measurement surface.
