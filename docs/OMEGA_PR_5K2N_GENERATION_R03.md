# Ω-PR-5K2N-T∞ R0.3 — Dual-Plane Reuse + Inspection-First Physicalization

## Why R0.3 exists

R0.2 exposed a useful ambiguity in live execution: a PR asks for deliverables such as `implementation`, `tests`, `evidence` and `documentation`, while Capability OS contracts mostly describe reusable **process capabilities** such as `pr_index`, `reuse_decision`, `residual_artifact_spec` and `llmt_context`.

Treating these two vocabularies as one would create false reuse claims.

R0.3 therefore separates two planes:

```text
Process Reuse Plane
!=
Artifact Residual Plane
```

## Process Reuse Plane

This plane asks whether the repository already contains the machinery needed to inspect history, decide reuse and compile a residual.

Canonical process outputs:

```text
pr_index
capability_graph
reuse_decision
residual_artifact_spec
llmt_context
```

For the current registry, these outputs are explicitly produced by existing Capability OS contracts.

A process-plane coverage of `1.0` means:

```text
the workflow machinery is reusable
```

It does **not** mean:

```text
the target artifact already exists
```

## Artifact Residual Plane

This plane keeps the actual deliverables distinct:

```text
implementation
tests
evidence
documentation
```

The decision rule is stricter than R0.2:

```text
explicit residual INSPECT
    -> INSPECT

explicit artifact capability + residual
    -> EXTEND

explicit artifact capabilities + no residual
    -> REUSE or COMPOSE

no explicit artifact capability + historical PR candidates
    -> INSPECT

no explicit artifact capability + no historical candidate + residual
    -> CREATE_RESIDUAL

otherwise
    -> INSPECT
```

This changes the meaning of live history. A retrieved PR is not silently treated as reusable, but its existence prevents premature creation until exact inspection is performed.

## Core invariant

```text
historical candidate != compatible implementation
```

Therefore:

```text
candidate exists + no explicit contract
-> inspect first
```

not:

```text
candidate exists + no explicit contract
-> create immediately
```

## Failure memory hardening

R0.2 consumed `negative_memory_hits` from #450 as a bounded numeric warning. Those hits are extracted from text patterns such as `error`, `blocked`, `debt`, `failed`, etc. They are useful search leads but are not necessarily confirmed M− outcomes.

R0.3 permanently separates:

```text
heuristic failure-memory lead
!=
confirmed M-
```

A regex-derived lead:

- is retained in `heuristic_failure_memory_refs`;
- can increase inspection priority;
- contributes exactly `0.0` numeric penalty.

A numeric negative term may be applied only when an evidence-bearing `ReuseOutcomeLearner` action summary contains:

```text
n > 0
failures > 0
evidence_refs != empty
```

Even then, the term remains observational and bounded.

## Confirmed negative term

For an action with evidence-bearing failures:

```text
failure_rate = failures / n
confirmed_M_minus_penalty = min(0.30, 0.24 * failure_rate)
```

This is a policy term, not a probability of failure and not causal proof.

## Compatibility Inspection Plan

When historical candidates exist, R0.3 emits an explicit inspection queue. Each item retains:

- PR ref;
- recorded head SHA when available;
- changed files;
- static symbol assets when available;
- mandatory source/test/CI/interface checks;
- `inspection_status = NOT_EXECUTED`;
- `compatibility_proven = false`;
- `reuse_authorized = false`.

The intended next bridge is:

```text
retrieval candidate
-> exact source@SHA
-> exact tests@SHA
-> exact CI/evidence@SHA
-> interface comparison
-> CompatibilityReceipt
-> REUSE / EXTEND / REJECT / UNKNOWN
```

## Interaction with 5K * 2^n

The logical law is unchanged:

```text
C_n = 5000 * 2^n
```

R0.3 changes only the **permission to physicalize** the bounded frontier.

The system may still generate and reason over virtual candidates at large `n`, but:

```text
artifact decision = INSPECT
-> PhysicalPatchContracts = 0
-> next_generation_candidate = null
```

This prevents recursive generation from bypassing unresolved reuse evidence.

## R0.3 GO proxy

The R0.3 planning score is:

```text
GO_R03
= GO_R01
+ artifact_decision_fit
+ evidence-bearing_outcome_term
+ artifact_reuse_coverage_term
- confirmed_M_minus_penalty
```

with:

```text
heuristic_failure_memory_penalty = 0
```

Process-plane coverage is reported separately and does not increase artifact completeness.

## Physical Patch boundary

R0.3 continues to reuse the R0.2 `PhysicalPatchContract` compiler.

Permanent authority remains:

```text
code_change_generated = false
write_authority_granted = false
automatic_commit_allowed = false
automatic_merge_allowed = false
human_review_required = true
```

A successful R0.3 court therefore proves software behavior of the planning system, not permission to write code.

## Live intended behavior for #452

The R0.2 live court observed:

- 350 prior PRs after leakage control;
- 16 historical candidates;
- no explicit artifact Capability contract for generic deliverables;
- process machinery already represented by explicit Capability contracts.

R0.3 should therefore classify the same state as:

```text
Process Reuse Plane:
  coverage = 1.0
  complete = true

Artifact Residual Plane:
  historical candidates > 0
  explicit artifact capability coverage = 0
  decision = INSPECT

PhysicalPatchContracts = 0
```

This is more conservative than R0.2's `CREATE_RESIDUAL`, and better aligned with reuse-before-create.

## CLI

```bash
python -m omega_capability_os_t.github_pr_generation_r03 \
  examples/pr_5k2n_generation_r03_request.json \
  --output /tmp/omega-pr-5k2n-r03.json
```

## OAK boundaries

```text
process capability reuse != artifact implementation reuse
generic deliverable token != capability contract output
historical candidate != compatible implementation
regex failure-memory lead != confirmed M-
confirmed historical failure != causal law
process reuse coverage 1.0 != target artifact completeness
INSPECT blocks PhysicalPatchContracts regardless of candidate score
PhysicalPatchContract != source patch
5K*2^n logical candidates != 5K*2^n physical edits
CI green != external truth
```

## Next proof frontier

R0.4 should perform exact candidate inspection rather than create more planning vocabulary:

1. hydrate top historical PRs at their exact head SHA;
2. inspect changed files and static symbols;
3. bind tests and CI evidence to the same SHA;
4. compile machine-readable CompatibilityReceipts;
5. route compatible candidates to REUSE/EXTEND and incompatible ones to M−;
6. keep UNKNOWN fail-closed;
7. measure whether inspection reduces actual new LOC and regression rate;
8. only then consider a separately authorized source renderer.
