# Ω-PR-5K2N-T∞ R0.2 — Cumulative-Intelligence Generation + Physical Patch Contracts

## Status

R0.2 is an executable, bounded, review-only extension of R0.1. It connects the virtual law

```text
C_n = 5000 * 2^n
```

to the cumulative GitHub memory stack instead of letting generation operate in isolation.

The logical population remains virtual. R0.2 does **not** create `5000*2^n` files, lines, patches, commits, agents or tool calls.

## Stack

```text
#447 Ω-GITHUB-CUMULATIVE-MEMORY
  -> all-PR memory / ReuseBeforeCreate / residual compiler / M+ M- M?
#448 Ω-UNIVERSAL-RESEARCH-ABI
  -> typed interoperation / receipts
#450 Ω-GITHUB-CUMULATIVE-INTELLIGENCE
  -> History Archaeology / PR Genome / Minimal Reuse Coalition / Memory Lenses
#452 R0.1
  -> virtual 5K*2^n candidate forest / Explorer-Prosecutor / bounded GO proxy
#452 R0.2
  -> history-enriched decision gate
  -> evidence-conditioned candidate re-ranking
  -> bounded synergy search
  -> PhysicalPatchContract compiler
```

## Central rule

Generation is subordinate to cumulative intelligence:

```text
SEARCH HISTORY
-> REUSE
-> COMPOSE
-> EXTEND
-> CREATE RESIDUAL ONLY
-> GENERATE
-> ATTACK
-> DEDUPE
-> TEST
-> BENCHMARK
-> REVIEW CONTRACT
```

A high candidate score cannot override a structural `INSPECT`, `REUSE` or `COMPOSE` gate.

## HistoricalGenerationContext

R0.2 consumes an `omega-github-cumulative-intelligence/v1.2.0` capsule and extracts:

- `CapabilityRequest`;
- selected Capability contracts;
- source PR references;
- residual outputs;
- exact PR candidates requiring inspection;
- reuse coverage ratio;
- M− references;
- required tests;
- required provenance;
- a target PR Genome.

The decision compiler is deliberately simple and fail-closed:

```text
explicit INSPECT anywhere -> INSPECT
residual + selected capability -> EXTEND
residual + no selected capability -> CREATE_RESIDUAL
no residual + >1 selected capability -> COMPOSE
no residual + 1 selected capability -> REUSE
no residual + no selected capability -> INSPECT
```

This is a software governance rule, not a theorem that the selected historical implementation is compatible.

## Evidence-conditioned GO gradient

R0.1 uses transparent family priors. R0.2 preserves that score and adds only explicit terms:

```text
GO_R02
= GO_R01
+ decision_fit
+ evidence_bearing_outcome_term
+ reuse_coverage_term
- visible_M_minus_penalty
```

### Outcome evidence

R0.2 can consume `omega-reuse-outcome-policy/v0.7.0` from `ReuseOutcomeLearner`.

The empirical term is used only when:

```text
sample_count > 0
AND evidence_refs != empty
```

A merge state is not an outcome. A historical success is not causal proof. A small sample cannot override OAK or the structural reuse gate.

## Negative memory

M− is explicit. Every negative-memory hit contributes a bounded visible penalty rather than a hidden veto.

```text
M- != universal impossibility
```

When a failure is structural enough to require exact inspection, the residual court can emit `INSPECT`; that gate blocks physical contracts entirely.

## Decision-conditioned candidate families

R0.2 does not treat every generated family as equally admissible.

### REUSE

New implementation candidates are blocked. The front can still propose integration tests, contracts, provenance, OAK, benchmarks, documentation and simplification reviews.

### COMPOSE

New standalone implementation is blocked. The front prioritizes composition, contracts, tests and interface/OAK work.

### EXTEND

Implementation candidates are allowed only for declared residual outputs or already changed target files. Supporting tests, benchmarks, contracts, provenance and OAK remain eligible.

### CREATE_RESIDUAL

Creation is allowed only for the declared residual capability. It does not mean a full rewrite is desirable.

### INSPECT

No `PhysicalPatchContract` is emitted, regardless of proxy score.

## PhysicalPatchContract Compiler

R0.2 introduces a physicalization boundary without yet generating source code.

Each surviving candidate can become a `PhysicalPatchContract` with:

- candidate ID;
- family and patch kind;
- proposed operation;
- target or unresolved target;
- structural reuse decision;
- source references;
- exact inspection references;
- required tests;
- required evidence;
- rollback requirement;
- explicit authority flags.

Permanent state in R0.2:

```text
materialization_status = REVIEW_CONTRACT_ONLY
code_change_generated = false
write_authority_granted = false
automatic_commit_allowed = false
automatic_merge_allowed = false
human_review_required = true
rollback_required = true
```

Thus:

```text
PhysicalPatchContract != patch
```

R0.3 may add a separately authorized patch renderer, but only after exact inspection and contract satisfaction are machine-checkable.

## Synergy / GO Hessian proxy

R0.2 also searches a bounded set of complementary pairs such as:

```text
code + test
code + benchmark
reuse + test
reuse + contract
contract + OAK
simplify + test
benchmark + OAK
```

The pair score is a planning heuristic. Every row carries:

```text
causal_synergy_proven = false
```

No superadditivity or causal interaction is claimed until measured by ablations or matched experiments.

## Adaptive depth

The architecture still has no fixed `N_max`.

```text
architecture_hard_cap = false
```

A finite run uses candidate and contract budgets. Continuation to `n+1` requires:

1. R0.1 bounded GO proxy remains above threshold;
2. history-enriched decision is not `INSPECT`;
3. later execution/review budgets permit another wave.

```text
finite budget != permanent N_max
```

## Example

```bash
python -m omega_capability_os_t.github_pr_generation_r02 \
  examples/pr_5k2n_generation_r02_request.json \
  --output /tmp/omega-pr-5k2n-r02.json
```

The example intentionally uses a compact machine-readable cumulative-intelligence fixture. Real future PR execution should compile the capsule from the canonical #450 memory stack before R0.2.

## OAK invariants

```text
cumulative memory != semantic equivalence
reuse outcome history != causal proof
M+ != universal success
M- != universal impossibility
proxy GO gradient != measured engineering value
synergy proxy != causal synergy
PhysicalPatchContract != generated code
contract budget != architectural N_max
5K*2^n logical additions != 5K*2^n physical edits
INSPECT blocks physical contracts even when candidate scores are high
write authority is never inferred from generation scale or CI
```

## R0.3 frontier

R0.3 should focus on stronger evidence, not larger textual volume:

1. build the R0.2 input directly from a live #450 capsule rather than a fixture;
2. inspect exact historical source blobs and tests before code-family eligibility;
3. add compatibility receipts keyed to exact source/head SHA;
4. replace more family priors with evidence-bearing measured outcome distributions;
5. add confidence intervals / UNC² calibration around historical utility;
6. benchmark `REUSE-first` vs `CREATE-first` on actual LOC, regressions, CI retries, tokens and maintenance;
7. add matched ablations for synergy pairs;
8. compile target-path proposals from real AST Symbol Genome / changed-file memory;
9. add a patch renderer only behind explicit write authorization and exact-head checks;
10. record every accepted/rejected physical patch outcome back into M+, M− or M?.

The objective is not to maximize generated additions. It is to maximize verified marginal progress per physical edit.
