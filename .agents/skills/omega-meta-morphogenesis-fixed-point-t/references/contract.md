# Ω Morphogenesis Contract Reference

## Required distinctions

- Generator != Judge
- Capability != Authority
- Generated != Verified
- Simulation != Reality
- Correlation != Causation
- Prediction != Permission
- LocalPASS != GlobalPASS

## Minimum transformation receipt

A persistent mutation should expose:

```text
before identity/hash
after identity/hash
mutation identifier
generator identity
verifier identity
action
authority envelope
epistemic input/output/evidence classes
provenance
tests/falsifiers
risk
rollback or compensation when required
utility / complexity-rent decision
remaining residuals
```

## Baseline tournament

Every material architectural addition should be compared against:

1. current baseline;
2. GO_MIN — the smallest change likely to resolve the residual;
3. DO_NOTHING — no persistent change.

A candidate that does not beat the baseline on verified utility should not be promoted merely because it is novel.

## Meta-stop

A new meta-level is justified only when the desired behavior is not expressible in the current kernel and verified out-of-sample gain exceeds the added meta-complexity cost.

## Regenerative target

Prefer storing the minimum information necessary to reconstruct verified capabilities rather than preserving all intermediate artifacts indefinitely.
