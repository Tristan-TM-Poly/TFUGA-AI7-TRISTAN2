# Ω-META-THEORY-EVOLUTION R0.6 — Adversarial Probe + Minimal Repair

R0.6 executes the residual left by R0.5: once a cross-context failure is observed, the system should not merely report it. It should synthesize a challenge from the residual and search for the smallest declared repair that absorbs the counterexample without discarding the previous basis.

## Core loop

```text
R0.5 Cross-Context Failure
-> Missing Observables
-> Adversarial Residual Probe
-> Finite Repair Candidate Pool
-> Cardinality-Minimal Additive Repair
-> Regression Preservation
-> PASS | HOLD
```

## Core law

```text
ArchitectureGrowth = CounterexampleAbsorption
Repair != Rewrite
MinimalRepair != GlobalOptimum
AdversarialProbe != IndependentTruth
```

## Adversarial probe synthesis

`synthesize_adversarial_probe(...)` unions the explicit missing observables from failing R0.5 probe families and records the families that exposed them.

This is intentionally conservative. It does not invent new external facts or claim to generate the strongest possible adversary. It converts already-observed failures into a reproducible challenge object.

## Minimal counterexample repair

`minimal_counterexample_repair(...)`:

1. freezes the current basis;
2. receives a finite, declared candidate seed pool;
3. enumerates additive subsets by increasing cardinality;
4. evaluates each repaired basis against all supplied probe families;
5. returns the first minimum-cardinality repair satisfying the declared transfer threshold;
6. returns `HOLD` if no declared repair closes the residual.

The exactness claim is deliberately narrow: minimum added-seed cardinality only inside the supplied finite pool.

## Regression preservation

R0.6 uses additive repair by default:

```text
OldBasis <= RepairedBasis
```

This makes preservation of previously verified structural capability explicit. A future subtractive or substitutive repair may be useful, but it requires a stronger regression and invariant court.

## OAK boundaries

- A passing repair is not proof of scientific truth.
- The candidate seed pool limits what can be discovered.
- Minimum cardinality is not minimum semantic complexity, cost, risk, or description length.
- A probe synthesized from known failures is not independent out-of-sample evidence.
- A repair that closes declared probes may still overfit them.
- `PASS` requires regression preservation and declared probe closure; it does not imply universal robustness.
- `HOLD` is a valid result when the finite repair pool is insufficient.

## Meta-generalization

The same pattern transfers to other skills and domains:

```text
GitHub failing CI/review -> failing invariant -> minimal patch -> regression suite
Document weakness -> missing evidence/coverage -> minimal section repair -> layout/content regression
Automation failure -> failure trace -> minimal workflow repair -> replay
Scientific model failure -> counterexample -> minimal model extension -> out-of-sample retest
Agent failure -> adversarial trace -> minimal policy/tool change -> safety/regression court
```

R0.6 is therefore a candidate universal operator:

```text
FAIL -> RESIDUALIZE -> ADVERSARIALIZE -> MINIMAL-REPAIR -> REGRESSION -> REVERIFY
```

## Next n+1 probe

R0.6 still uses adversaries derived from observed failures. The next falsifier should test whether the challenge generator itself overfits the system it is testing.

Candidate R0.7 residual:

```text
AdversarialProbeGenerator
-> independent/frozen challenge family
-> challenge diversity and novelty tests
-> repair overfit detection
-> generator vs verifier separation
```

That layer should not be promoted unless R0.6 exact-head CI and repository-level gates first pass.
