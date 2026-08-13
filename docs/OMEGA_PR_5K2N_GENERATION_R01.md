# Ω-PR-5K2N-T∞ R0.1 — Fractal PR Generation Compiler

## Mission

Turn every new pull request into a bounded, reuse-first research space whose logical population at generation `n` is:

```text
C_n = 5000 * 2^n
```

without materializing the full population as files, lines, branches, agents, or API calls.

Permanent invariant:

```text
logical candidate != physical patch
generated candidate != useful change
many additions != progress
```

R0.1 is stacked on Ω-GITHUB-CUMULATIVE-INTELLIGENCE (#450) and is intended to consume PR Genome, historical memory, reuse coverage, residual outputs and OAK boundaries before any future patch-generation layer gains write authority.

## Canonical 5,000-seed genome

| Family | Share | Seeds at 5K |
|---|---:|---:|
| reuse | 20% | 1000 |
| code | 16% | 800 |
| test | 14% | 700 |
| benchmark | 10% | 500 |
| contract | 10% | 500 |
| documentation | 8% | 400 |
| provenance | 8% | 400 |
| OAK | 6% | 300 |
| simplify | 4% | 200 |
| alternative | 4% | 200 |

Each binary generation adds an Explorer/Prosecutor branch. Explorer asks how to construct or improve. Prosecutor asks how to falsify, simplify, reject, or replace.

## Virtual address law

For logical index `i` at generation `n`:

```text
seed_id = i >> n
route   = i mod 2^n
polarity = explorer if route is even else prosecutor
```

The compiler addresses candidates directly without enumerating siblings.

Examples:

```text
n=0  -> 5,000 logical additions
n=1  -> 10,000
n=10 -> 5,120,000
n=20 -> 5,242,880,000
```

At `n=128`, the space remains exactly addressable with arbitrary-precision integers while the physical run remains bounded.

## Bounded compiler

```text
PR intent + PR Genome + residual outputs + reuse evidence
→ exact logical cardinality
→ deterministic bounded sample
→ Explorer / Prosecutor AddAtoms
→ proxy GO gradient
→ CVCD sample-pattern compression
→ deduplication
→ bounded selection
→ review-only addition specifications
```

No selected AddAtom is automatically applied to source code in R0.1.

## n=0 → N_run campaign

R0.1 supports a campaign over consecutive generations:

```text
n=0,1,2,...,N_run
```

`generation_budget` is an execution/review budget only. It is not a permanent `N_max`.

```text
architecture_hard_cap = false
generation_budget_is_runtime_budget = true
```

A later authorized run may continue from `next_generation_candidate`.

Therefore:

```text
no fixed architectural N_max != infinite physical compute
```

## GO gradient proxy

R0.1 uses an explicitly heuristic planning score:

```text
GO = value + information + reuse + testability + leverage - cost - debt - risk
```

The components are transparent family priors with deterministic tie-breaking noise. They are not measured engineering value, truth probability, scientific evidence, or business return.

Future generations should replace priors with observed M+/M-/M? receipts, benchmarks, maintenance outcomes, regressions, CI attempts, context cost, and measured reuse evidence.

## CVCD

CVCD compresses only the bounded sampled wave in R0.1. Repeated `(family, polarity, target, action)` patterns receive a stable signature.

`sample_support_count` is never promoted to full-population frequency.

## Native new-PR hook

`tools/compile_pr_5k2n_event.py` can compile an event-only receipt from `GITHUB_EVENT_PATH`.

The event-only genome intentionally reports:

```text
history_enriched = false
physical_materialization_blocked_until_reuse_inspection = true
```

The GitHub workflow is triggered for newly opened, synchronized, reopened and ready-for-review PRs. Before any later system converts these specs into code, it should enrich the event using #450 cumulative memory, PR Genome, Minimal Reuse Coalition and M−.

## OAK boundaries

```text
5K*2^n logical candidates != 5K*2^n files or lines
logical addressability != execution
generated candidate != useful change
proxy score != measured engineering value
sample support != population frequency
reuse similarity != implementation compatibility
compiled addition spec != tested patch
no fixed architectural N_max != infinite physical compute
many additions != progress
CI green != external truth
```

## R0.2 frontier

1. Feed #450 Minimal Reuse Coalition and PR Genome directly into each new-PR generation receipt.
2. Replace family priors with empirical M+/M-/M? outcome distributions.
3. Add true multiobjective Pareto selection rather than one GO proxy ordering.
4. Compile selected specs into isolated patch candidates only after reuse inspection.
5. Benchmark CREATE-first vs REUSE-first vs 5K2N-assisted policy.
6. Learn reusable generator primitives from recurrent winning AddAtom patterns.
7. Split large surviving physical patch sets into stacked child PRs.
8. Add token, CI, maintenance, latency, energy and causal-decision replay accounting.
