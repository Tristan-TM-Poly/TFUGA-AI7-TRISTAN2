# Ω-META-THEORY-EVOLUTION R0.5 — Cross-Context Regeneration

R0.5 executes the mandatory n+1 falsifier left by R0.4: a locally minimal and second-pass-stable basis must not be promoted unless it survives independent probe families.

## Core law

```text
LocalMinimality != CrossContextValidity
LocalFixedPoint != GlobalFixedPoint
MetricWinner != RobustWinner
```

## Cross-context regeneration

Given a training probe family and one or more transfer families, R0.5:

1. computes the R0.4 regeneration benchmark on the training family;
2. freezes the resulting reduced basis;
3. evaluates that fixed basis against every declared probe family;
4. measures minimum and mean retained-observable ratios;
5. records transfer failures;
6. detects a false fixed point when the training result is locally PASS/stable but fails transfer.

This prevents a compressed basis from looking complete merely because the evaluation family was too narrow.

## Metric sensitivity

`metric_sensitivity(...)` compares winners under multiple declared rankings.

- same top candidate across metrics -> robustness `PASS`;
- different winners -> `HOLD`;
- no rankings -> `HOLD`.

No hidden scalarization is introduced to force agreement.

## OAK boundaries

- Cross-context PASS is finite and conditional on the supplied probe families.
- It does not prove universal generalization.
- A false-fixed-point signal is evidence against promotion, not proof that the basis is useless.
- Relaxing `min_transfer_ratio` is explicit and auditable.
- Metric agreement is a robustness signal, not external-world truth.

## Meta-generalization

The same pattern applies beyond theory compression:

```text
locally-good code patch -> cross-repo probes
locally-good workflow -> cross-task probes
locally-good scientific model -> out-of-sample probes
locally-good automation -> adversarial/replay probes
locally-good benchmark -> independent benchmark families
```

This turns the n+1 rule into a general anti-overfitting operator.

## Next residual

The next candidate layer should only be admitted if needed after R0.5 evidence. Useful possible residues are:

- automatic probe-family generation from observed failures;
- adversarial probe mutation;
- causal attribution of which probe exposed which invalid assumption;
- cross-context basis repair with minimal persistent change.

Those are not promoted by this document. R0.5 only creates the executable transfer/fixed-point court.
