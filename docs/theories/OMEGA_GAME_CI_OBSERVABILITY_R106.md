# Ω-GAME R1.0.6 — CI Scale Observability

**Status:** CI observability candidate after R1.0.5  
**Authority:** retained empirical build observation only

## Purpose

R1.0.6 preserves bounded ScaleBench measurements from GitHub Actions without promoting runner-specific measurements into deterministic provenance.

```text
commit SHA
→ install packaged omega-game-t
→ omega-game scale-bench --matrix
→ validate deterministic scale invariants
→ retain full JSON as CI artifact
```

## Artifact contract

The workflow uploads:

```text
omega-game-scale-observation-<github.sha>
```

containing:

```text
scale-observation.json
```

The current retention policy is **30 days**.

The JSON includes both:

- deterministic scenario identity/work-unit receipts;
- local empirical wall-clock, tracemalloc and observed process-speedup fields.

## Separation rule

The CI artifact is an observation ledger, not a truth ledger.

```text
CI_ARTIFACT != CANONICAL_PROOF
RUNNER_TIME != DETERMINISTIC_RECEIPT
ONE_RUNNER != PERFORMANCE_DISTRIBUTION
ONE_COMMIT_OBSERVATION != REGRESSION_CAUSALITY
```

A slower or faster runner observation does not by itself justify a performance regression/improvement claim. Such claims require repeated observations, comparable runner conditions and explicit statistical analysis.

## Validation before upload

The artifact job fails closed unless:

- ScaleBench overall `accepted` is true;
- exactly the bounded tiny/small/medium matrix is present;
- every scenario is accepted;
- the deterministic suite receipt is 64 hex characters;
- empirical wall-clock values are non-negative;
- tracemalloc peak values are non-negative.

## OAK boundaries

```text
ARTIFACT_RETENTION != DURABLE_ARCHIVE
CI_RUNNER != USER_HARDWARE
TRACEMALLOC != TOTAL_RSS
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
EMPIRICAL_HISTORY != ASYMPTOTIC_PROOF
CORRELATION_WITH_COMMIT != CAUSAL_REGRESSION
```

## Next

Once enough artifacts exist, a later analysis layer may compare deterministic-identical or workload-comparable observations across commits. Any automated regression gate should first establish noise bands and runner comparability rather than using a single fixed wall-clock threshold.
