---
name: pr-fractal-generation
description: Compile bounded Ω-PR-5K2N-T∞ candidate forests, dual-plane reuse decisions, exact compatibility inspection, evidence-bound outcomes and review-only action/memory candidates without materializing the full logical population.
---

# PR Fractal Generation

Use this skill for new or existing PRs that should benefit from Ω-PR-5K2N-T∞ while preserving cumulative memory, reuse-before-create, exact-head provenance, OAK, CVCD, M+/M-/M? and bounded physical execution.

## Core law

```text
C_n = 5000 * 2^n
```

This is a logical address space, never a requirement to create that many files, lines, commits, agents, tool calls or patches.

## R0.5 procedure

1. Resolve exact repository, PR number and target head SHA.
2. Build `state=all` GitHub memory **once** in the live pipeline; hide the target plus later same-repository PRs before historical retrieval.
3. Reuse that live memory/derived artifact downstream. Do not let each LLMT/workflow independently refetch the entire PR history.
4. Compile two independent #450 cumulative-intelligence requests:
   - **Process Reuse Plane** for `pr_index`, `capability_graph`, `reuse_decision`, `residual_artifact_spec`, `llmt_context`;
   - **Artifact Residual Plane** for the actual requested deliverables.
5. Never translate generic deliverables such as `implementation` into a Capability output merely to increase reuse coverage.
6. Interpret process coverage only as reuse of the research/generation machinery, never as artifact completeness.
7. Resolve artifact action fail-closed:
   - explicit artifact contract + no residual → `REUSE` or `COMPOSE`;
   - explicit artifact contract + residual → `EXTEND`;
   - no explicit artifact contract + historical candidates → `INSPECT`;
   - no explicit artifact contract + no historical candidates + residual → `CREATE_RESIDUAL`;
   - explicit residual `INSPECT` or ambiguity → `INSPECT`.
8. Treat regex-derived failure/debt/error/blocked lines as inspection leads only. They are **not confirmed M−** and contribute zero numeric penalty.
9. Apply a bounded negative numeric term only from evidence-bearing observed failure outcomes (`n>0`, `failures>0`, evidence refs present).
10. Compute the exact logical cardinality without enumerating it.
11. Compile a bounded deterministic virtual AddAtom wave with Explorer/Prosecutor alternatives.
12. CVCD-deduplicate the bounded sample and rank only as planning evidence.
13. Search bounded complementary pairs; keep `causal_synergy_proven=false` until matched experiments/ablations exist.
14. If artifact action is `INSPECT`, emit a SHA-aware Compatibility Inspection Plan and **zero PhysicalPatchContracts**.
15. Hydrate only a bounded top-k historical queue using the existing `ProgressiveGitHubRetriever`; do not import or execute candidate code.
16. Compare planned and hydrated candidate head SHAs. Head drift → `STALE_HEAD` and blocks experiment compilation.
17. Inventory changed paths, technical source paths, test paths, workflow paths and static Python symbols.
18. Classify static evidence conservatively (`METADATA_ONLY`, `STATIC_ONLY`, `STATIC_SOURCE_TEST_SURFACE`, `STATIC_SOURCE_TEST_CI_SURFACE`, etc.).
19. A candidate is **experiment-eligible only if**:
   - hydration is `HYDRATED_EXACT_HEAD`;
   - technical source or static symbol surface exists;
   - a candidate test surface exists.
20. Exact-head metadata alone is not experiment-ready. Preserve this as M− rather than manufacturing a compatibility experiment.
21. Even experiment-eligible candidates remain `compatibility_verdict=UNKNOWN`, `compatibility_proven=false`, `reuse_authorized=false`, `execution_authorized=false`.
22. Compile only `CompatibilityExperimentContract` obligations; do not execute historical code automatically.
23. Downstream R0.5 must consume the exact R0.4 artifact rather than rebuilding GitHub memory. Cross-workflow artifact reuse is preferred to duplicate API fan-out.
24. A supplied `CompatibilityOutcomeReceipt` must bind to a known experiment ID, exact candidate ref, candidate SHA and target SHA.
25. Treat `COMPLETED` as insufficient by itself. Promotion evidence additionally requires explicit execution authority, isolation receipt, environment fingerprint, evidence refs, tests and non-UNKNOWN interface checks.
26. Route evidence conservatively:
   - all tests/interfaces pass + no regressions + residual coverage `1.0` → `COMPATIBLE / REUSE_CANDIDATE / M_PLUS_CANDIDATE`;
   - same but `0 < residual_coverage < 1` → `PARTIAL_COMPATIBLE / EXTEND_CANDIDATE / M_QUERY_CANDIDATE`;
   - failed test/interface or regression witness with complete evidence → `INCOMPATIBLE / REJECT_CANDIDATE / M_MINUS_CANDIDATE`;
   - stale, unexecuted, unauthorized, under-evidenced or ambiguous → `UNKNOWN / HOLD / M_QUERY_CANDIDATE`.
27. `M_PLUS_CANDIDATE` and `M_MINUS_CANDIDATE` are never canonical M+/M− automatically; memory promotion requires review/persistence authority.
28. Test pass rates and Wilson intervals are finite test-corpus bookkeeping, not probabilities of semantic truth.
29. Only after reviewed compatibility evidence may bounded `PhysicalPatchContract` objects be reconsidered.
30. Keep all physical contracts `REVIEW_CONTRACT_ONLY`; they are not source patches.
31. A separately authorized source renderer may be introduced later, but write, commit and merge permissions are never inferred from generation scale, hydration, compatibility verdict or CI.
32. Feed reviewed compatibility, accepted changes, regressions and failures back into M+, M− or M?.

## Anti-fan-out rule

A live GitHub snapshot is a shared evidence asset:

```text
one authorized state=all collection
→ content-addressed/indexed artifact
→ many downstream read-only compilers
```

Do not do:

```text
N workflows × full PR API crawl
```

The R0.5 live court consumes the completed R0.4 artifact by workflow run ID instead of issuing a second 350-PR crawl. This prevents avoidable GitHub Installation rate-limit debt.

## Adaptive depth

There is no fixed architectural `N_max`.

```text
no fixed architectural N_max != infinite physical compute
```

A finite run uses runtime/candidate/inspection/contract/review budgets. `INSPECT` blocks physical continuation regardless of virtual candidate score.

## Permanent authority boundary

```text
code_change_generated = false
write_authority_granted = false
execution_authorized = false
automatic_reuse_authorized = false
automatic_memory_promotion_authorized = false
source_renderer_authorized = false
automatic_commit_allowed = false
automatic_merge_allowed = false
human_review_required = true
```

## Hard boundaries

```text
process capability reuse != artifact implementation reuse
generic deliverable token != capability contract output
historical candidate != compatible implementation
regex failure-memory lead != confirmed M-
confirmed historical failure != causal law
process reuse coverage 1.0 != target artifact completeness
hydrated exact head != compatible behavior
exact head without technical/test surface != experiment-ready
changed-file overlap != semantic equivalence
AST symbol overlap != interface compatibility
test file exists != test passed
workflow file exists != CI passed at candidate head
CompatibilityExperimentContract != experiment execution
CompatibilityOutcomeReceipt != automatic reuse authority
COMPATIBLE != universally reusable
M_PLUS_CANDIDATE != canonical M+
M_MINUS_CANDIDATE != canonical M-
5K*2^n logical candidates != 5K*2^n physical edits
proxy score != measured engineering value
synergy proxy != causal synergy
PhysicalPatchContract != generated code
CI green != external truth
```

## Authority

Default authority is read + draft. Never infer push, commit, merge, auto-merge, publication, deployment, force-push, permission widening or irreversible authority from this skill.
