# Ω-PR-5K2N-T∞ — History Cache, API Budget and Rate-Limit M−

## Problem observed

The first live R0.3/R0.4/R0.5 architecture allowed several workflows to independently rebuild the same `state=all` GitHub PR memory. With ~350 historical PRs, this multiplied GitHub Installation API consumption and eventually produced:

```text
HTTP 403: rate limit exceeded for installation
```

After removing the duplicate consumers, an isolated full-history R0.4 rebuild still encountered quota exhaustion because the installation already had zero remaining quota before its first `/pulls` request.

Therefore the permanent correction is not “retry harder”. It is:

```text
collect once
→ verify
→ cache / artifact
→ reuse downstream
→ fetch only bounded deltas when necessary
```

## Rejected architecture

```text
R0.3 -> full GitHub crawl
R0.4 -> full GitHub crawl
R0.5 -> full GitHub crawl
DeltaCI -> REST changed-files call
```

This created API-budget debt unrelated to scientific or engineering value.

## Current architecture

### Deterministic plane

The primary `Ω PR 5K2N Fractal Generation OAK` court is offline with respect to GitHub REST:

- R0.1–R0.5 source compilation;
- deterministic tests;
- fixture schemas;
- PR event payload parsing;
- frozen R0.4 freshness/HOLD validation;
- no historical REST crawl.

### DeltaCI

`Ω Actions ΔCI Audit` obtains changed files from the local Git object graph:

```text
git diff BASE_SHA HEAD_SHA
```

instead of `/pulls/{n}/files`.

### R0.4 frozen fallback

A compact static seed from the last successful exact-hydration R0.4 run is retained with:

- source target head SHA;
- source R0.4 fingerprint;
- source workflow run ID;
- source artifact ID and SHA-256;
- four candidate refs and exact candidate head SHAs;
- static source/test/workflow/symbol surfaces.

This seed is historical inspection evidence, not current GitHub truth.

The fallback compiler compares:

```text
source_target_head_sha
vs
current_target_head_sha
```

and always prevents experiment generation from frozen evidence.

If the target changed:

```text
experiment_block_reason = stale_target_inspection_context
```

Even if the target were unchanged:

```text
experiment_block_reason = frozen_static_seed_requires_live_revalidation
```

Thus:

```text
frozen evidence -> INSPECT/HOLD
```

never:

```text
frozen evidence -> REUSE/CREATE/execute
```

## Incremental history-seed runtime

`github_pr_history_seed.py` implements a future shared-history primitive:

```text
verified seed
→ retrieval-equivalent CVCD compression
→ materialize with hashes
→ fetch only PR-number delta before target
→ HOLD on rate limit/error
```

The CVCD compiler preserves the observables used by the current retrieval/PRGenome stack:

- `_tokens` set;
- Ω concept strings;
- failure-memory lead lines;
- historical-lineage directive lines.

It explicitly does **not** preserve verbatim PR narrative text.

The repository currently keeps the runtime/tests but does not claim a complete materialized full-history shard set. A previous incomplete manifest was removed rather than leaving a false-ready cache.

## Delta rule

For a verified seed whose maximum observed historical PR is `m` and a new target PR is `N`:

```text
only numbers m+1 ... N-1 are queried
```

GitHub PR numbers share the issue-number space, so 404s are retained as non-PR gaps.

Rate limit or unexpected API failure produces:

```text
status = HOLD_RATE_LIMIT or HOLD_DELTA_ERROR
complete_for_target = false
```

Partial evidence is retained, but downstream physicalization must remain HOLD.

## Data truth boundaries

```text
cached snapshot != current lifecycle truth
retrieval-equivalent compression != verbatim archive
historical exact candidate SHA != current target compatibility
artifact reuse != evidence truth
API success != semantic correctness
API outage != permission to skip history
incomplete history != CREATE authorization
incomplete history != REUSE authorization
```

## Canonical anti-fan-out law

```text
ONE LIVE SNAPSHOT
→ MANY CONTENT-ADDRESSED CONSUMERS
```

not:

```text
N AGENTS × N COMPLETE CRAWLS
```

## Failure behavior

When fresh history cannot be obtained:

```text
preserve last verified evidence
mark freshness debt
block compatibility experiment generation
block physical patch generation
block memory promotion
emit HOLD / M? candidate
```

This makes API-budget failure a visible epistemic state rather than a hidden reliability failure.
