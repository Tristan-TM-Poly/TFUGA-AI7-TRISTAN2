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

containing `scale-observation.json` with **30-day retention**.

The JSON contains both deterministic scenario/work-unit receipts and empirical wall-clock, `tracemalloc`, and observed process-speedup fields. The empirical fields remain excluded from the deterministic receipt.

## Separation rule

```text
CI_ARTIFACT != CANONICAL_PROOF
RUNNER_TIME != DETERMINISTIC_RECEIPT
ONE_RUNNER != PERFORMANCE_DISTRIBUTION
ONE_COMMIT_OBSERVATION != REGRESSION_CAUSALITY
```

A faster or slower runner observation alone is never a performance promotion gate.

## Validation before upload

The artifact job fails closed unless:

- ScaleBench overall `accepted` is true;
- exactly the bounded tiny/small/medium matrix is present;
- every scenario is accepted;
- the deterministic suite receipt has SHA-256 shape;
- empirical wall-clock values are non-negative;
- `tracemalloc` peak values are non-negative.

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

Accumulate multiple comparable artifacts before defining statistical regression bands. Any later automated regression gate must first establish runner comparability, repeated observations and noise distributions.
