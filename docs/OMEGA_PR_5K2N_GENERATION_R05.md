# Ω-PR-5K2N-T∞ R0.5 — Compatibility Outcomes + Evidence-Bound Memory Candidates

## Objective

R0.4 stops at a `CompatibilityExperimentContract`. R0.5 defines what an experiment result must contain before it may even become a **review candidate** for reuse, extension or negative memory.

```text
CompatibilityExperimentContract
-> separately authorized / isolated execution elsewhere
-> supplied result + exact SHAs + evidence refs
-> CompatibilityOutcomeReceipt
-> COMPATIBLE / PARTIAL_COMPATIBLE / INCOMPATIBLE / UNKNOWN
-> REUSE_CANDIDATE / EXTEND_CANDIDATE / REJECT_CANDIDATE / HOLD
-> M_PLUS_CANDIDATE / M_MINUS_CANDIDATE / M_QUERY_CANDIDATE
-> human review
```

R0.5 itself does not execute historical candidate code and does not mutate source.

## Exact contract binding

Every outcome must reference a real R0.4 `experiment_id` and the exact candidate ref. Unknown or duplicate experiment IDs fail closed.

Candidate and target SHA freshness are checked independently:

```text
supplied candidate SHA == experiment candidate SHA
supplied target SHA    == experiment target SHA
```

A stale candidate or stale target keeps the verdict `UNKNOWN`.

## Execution authority and isolation

A supplied result cannot be promoted merely because it says `COMPLETED`.

Promotion evidence requires all of:

```text
execution_status = COMPLETED
candidate SHA fresh
target SHA fresh
execution_authority_ref present
isolation_receipt_ref present
evidence_refs present
environment_fingerprint present
source_mutation_performed = false
tests_executed > 0
interface checks present and non-UNKNOWN
```

Missing any one keeps:

```text
verdict = UNKNOWN
action_candidate = HOLD
memory_candidate = M_QUERY_CANDIDATE
```

## Verdict rules

### COMPATIBLE

```text
all supplied tests pass
all interface checks pass
no regression witness
residual_coverage = 1.0
all freshness / authority / isolation / evidence gates pass
```

Produces only:

```text
action_candidate = REUSE_CANDIDATE
memory_candidate = M_PLUS_CANDIDATE
```

It does not authorize reuse or canonical M+ promotion.

### PARTIAL_COMPATIBLE

Same clean evidence with `0 < residual_coverage < 1` produces:

```text
action_candidate = EXTEND_CANDIDATE
memory_candidate = M_QUERY_CANDIDATE
```

### INCOMPATIBLE

With complete evidence, a failed compatibility test, failed interface check or regression witness produces:

```text
action_candidate = REJECT_CANDIDATE
memory_candidate = M_MINUS_CANDIDATE
```

The incompatibility is scoped to the exact candidate/target/environment evidence and is not a universal impossibility claim.

### UNKNOWN

All incomplete, stale, unexecuted or under-evidenced states remain `UNKNOWN/HOLD`.

## Test-rate calibration

R0.5 records the finite observed test pass rate and a 95% Wilson interval when at least one test is supplied.

```text
Wilson interval over test cases
!= probability that the implementation is semantically correct
!= scientific confidence interval for truth
```

## Memory boundary

R0.5 deliberately emits memory **candidates**:

```text
M_PLUS_CANDIDATE
M_MINUS_CANDIDATE
M_QUERY_CANDIDATE
```

Permanent automatic authority remains:

```text
automatic_memory_promotion_authorized = false
automatic_reuse_authorized = false
```

A later reviewed persistence bridge may feed accepted outcomes to the existing `ReuseOutcomeLearner`; R0.5 does not silently rewrite cumulative memory.

## Source-renderer boundary

```text
source_renderer_authorized = false
write_authority_granted = false
automatic_commit_allowed = false
automatic_merge_allowed = false
```

Even a `COMPATIBLE` receipt is not a patch renderer permission.

## Deterministic fixture

`examples/pr_5k2n_generation_r05_request.json` contains a synthetic compatibility contract and synthetic fully passing outcome. It exists only to exercise the `COMPATIBLE` branch deterministically.

```text
fixture-compatible != real historical compatibility
```

## Live negative control

The live path deliberately does **not** execute the R0.4 candidate. It consumes the exact R0.4 artifact and generates pending outcomes:

```text
NOT_EXECUTED
-> UNKNOWN
-> HOLD
-> M_QUERY_CANDIDATE
```

until a separately authorized isolated experiment supplies evidence.

## M− — duplicate live GitHub crawling

The first R0.5 live workflow independently rebuilt the full `state=all` PR memory while the R0.3/R0.4 workflows were doing the same. Concurrent full-history crawls exhausted the GitHub Installation API quota and produced HTTP 403 rate-limit failure before R0.5 ran.

The rejected architecture was:

```text
R0.3 workflow -> full PR crawl
R0.4 workflow -> full PR crawl
R0.5 workflow -> full PR crawl
```

R0.5 now uses the correct reuse-first data path:

```text
one R0.4 live crawl/hydration
-> retained exact-head artifact
-> workflow_run success event
-> actions/download-artifact by source run-id
-> R0.5 pending-outcome compiler
```

The post-R0.4 consumer needs only:

```text
actions: read
contents: read
```

and performs no second PR-history crawl. The official `actions/download-artifact` cross-run interface is used with `github-token` and `run-id`.

Canonical anti-fan-out rule:

```text
one authorized live snapshot
-> many downstream content-addressed consumers
```

not:

```text
N agents/workflows × N complete API crawls
```

## OAK boundaries

```text
CompatibilityOutcomeReceipt != automatic reuse authority
test pass rate != probability of semantic compatibility
Wilson interval over test cases != scientific confidence interval for truth
COMPATIBLE != universally reusable
PARTIAL_COMPATIBLE != complete residual coverage
INCOMPATIBLE is scoped to exact candidate/target/environment evidence
UNKNOWN must remain HOLD
stale candidate or target SHA blocks promotion
COMPLETED without authority/isolation/evidence refs blocks promotion
M_PLUS_CANDIDATE != canonical M+
M_MINUS_CANDIDATE != canonical M-
workflow artifact reuse != truth
source rendering remains separately authorized
```

## R0.6 frontier

The next useful step is a **separately authorized isolated compatibility runner**, not more candidate volume:

1. materialize a temporary worktree/container pinned to candidate SHA;
2. use no repository write token and no user secrets;
3. execute only explicit bounded compatibility commands;
4. record environment and exact command receipts;
5. compare candidate and target behavior through a narrow adapter rather than blindly importing the whole historical branch;
6. emit an R0.5-compatible outcome JSON;
7. delete the temporary execution surface;
8. require human review before memory promotion or source rendering.
