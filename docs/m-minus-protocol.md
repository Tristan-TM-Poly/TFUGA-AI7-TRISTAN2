# M_MINUS Protocol — Negative Memory for TFUGA / SAGE-TRISTAN

`M_MINUS` is the memory of useful failure. It protects the canon against repeated mistakes, overclaims, unstable experiments, and hidden contradictions.

## Principle

```text
Every clean failure is a future accelerator.
Every recorded contradiction is a guardrail.
Every rejected claim increases canon quality.
```

## What enters M_MINUS

- failed hypotheses;
- non-reproducible experiments;
- contradictions;
- unstable algebraic behavior;
- overclaims;
- false positives;
- benchmark losses;
- bugs that reveal model assumptions;
- domains where a method does not work;
- safety or interpretation risks.

## Entry schema

```yaml
id: mminus_0001
date: YYYY-MM-DD
source_module: omega_ffwt_hac_cvcd
claim: "Claim that failed or became restricted"
failure_type: overgeneralization
truth_layer_before: T2
oak_level_before: OAK-2
counterexample: "Concrete failure, test, or contradiction"
residue_observed: "Metric or qualitative mismatch"
lesson: "What the system learned"
new_rule: "Guardrail added to prevent recurrence"
follow_up:
  - restrict domain
  - define baseline
  - add test
status: archived
```

## M_MINUS categories

| Category | Meaning |
|---|---|
| OVERCLAIM | claim stronger than evidence |
| BASELINE_LOSS | method loses to simpler baseline |
| NON_REPRODUCIBLE | result cannot be repeated |
| ALGEBRAIC_INSTABILITY | non-commutativity, non-associativity, zero divisors, or projection instability |
| MEASUREMENT_GAP | prediction without physical measurement |
| DEFINITION_GAP | object not defined enough to test |
| SCOPE_ERROR | true only in narrower domain |
| BUG_PATTERN | implementation failure reveals design risk |
| DEAD_BRANCH | no current value, kept for history |

## Required M_MINUS update after tests

Every benchmark or experiment must answer:

1. What failed?
2. What almost worked?
3. What baseline beat us?
4. What domain restriction is needed?
5. What should never be claimed again without evidence?
6. What test must be added?

## Example

```yaml
id: mminus_sedenion_001
source_module: hypernumbers_hac
claim: "Sedenion coherence always improves multiscale classification"
failure_type: OVERCLAIM
counterexample: "Synthetic noisy datasets showed unstable components under some projections"
lesson: "Sedenion outputs require robust real projection, zero divisor risk, and baseline comparison"
new_rule: "Never report sedenion gain without real projection, defect metrics, and FFT/DWT baseline"
status: active_guardrail
```

## Canon rule

```text
A module cannot reach OAK-6 or higher unless its known failures are documented.
```
