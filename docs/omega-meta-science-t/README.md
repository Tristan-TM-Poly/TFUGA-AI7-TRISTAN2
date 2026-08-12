# Ω-META-SCIENCE-FOUNDRY-T∞² — MetaScienceBench-T v0.1

## Status

**D-MVP candidate / OAK-safe toy benchmark.**

This package is the first executable crystallization of the Meta-Science Foundry discussed in the Tristan corpus. It does **not** claim that an autonomous system has discovered a new scientific law, that the architecture is historically unique, or that it outperforms real scientific practice.

Its purpose is narrower and testable:

```text
same toy problem + same experiment budget
        |
        +--> fixed policy
        |
        +--> adaptive disagreement-mining policy
                    |
                    v
          discriminating experiment
                    |
                    v
               OAK gate
                    |
                    v
         epistemic fault injection
                    |
                    v
                Meta-OAK
                    |
                    v
                M+ / M-
```

## Executable kernel

`omega_meta_science_t/` implements five ideas as code rather than slogans:

1. **Theory Genome** — assumptions, domain, falsifiers and multiple representations travel with each candidate theory.
2. **Representation Ecology / CVCD seed** — invariants are extracted by intersection across every declared representation and theory.
3. **Disagreement Mining** — the adaptive policy selects the experiment with maximal prediction variance per unit cost.
4. **OAK** — provenance, uncertainty, baseline, reproducibility, units, falsifier declaration and residual tolerance are fail-closed gates.
5. **Meta-OAK** — declared epistemic faults are injected into an otherwise clean claim packet and the detector receives a mutation score.

## Canonical fixture

Two theories are intentionally aliased at `x=1`:

```text
T_linear:    y = x
T_quadratic: y = x^2
```

At `x=1`, both predict `y=1`, so the fixed strategy cannot discriminate them.
At `x=2`, the predictions are `2` and `4`, so an experiment at `x=2` separates them exactly in this deterministic toy world.

The true fixture theory is `T_linear`.

Therefore the benchmark has a deliberately sharp falsifiable expectation:

```text
fixed    -> E_fixed_alias     -> 2 survivors -> OAK CONDITIONAL
adaptive -> E_discriminating  -> 1 survivor  -> OAK PROMOTE
```

With two equiprobable candidate theories, eliminating one corresponds to a toy hypothesis-space reduction of exactly one bit.

## Meta-OAK mutation score

The R0.1 campaign injects four fault classes:

- missing provenance;
- unit mismatch;
- non-reproducibility;
- residual/overclaim violation.

The score is

```text
MOS = detected injected faults / total injected faults
```

R0.1 requires `MOS == 1.0` before the adaptive strategy can be promoted by the meta-loop.

This is analogous to mutation testing in software: saying that a gate exists is weaker than demonstrating that realistic declared faults actually trip it.

## Knowledge-gain metric

For the toy hypothesis set:

```text
K_gain = log2(N_before) - log2(N_after)
```

and the promoted metric is

```text
verified_gain_per_cost = K_gain / experiment_cost
```

**only when OAK returns `PROMOTE`.** A plausible but underdetermined result receives zero verified gain.

## M+ / M-

The benchmark emits small appendable memories:

- `M+`: promoted strategy, preserved CVCD invariants, Meta-OAK mutation score;
- `M-`: the fixed policy's underdetermination and every detected/missed epistemic fault.

The intent is to make failures reusable rather than silently discarded.

## Run

From the repository root:

```bash
python -m omega_meta_science_t
python -m omega_meta_science_t --compact
pytest -q tests/test_omega_meta_science_t.py
```

The package uses only the Python standard library.

## What R0.1 demonstrates

R0.1 demonstrates, on one deterministic fixture, that code can compose this loop:

```text
multi-representation theories
-> disagreement
-> experiment selection
-> observation
-> hypothesis elimination
-> OAK
-> epistemic fault injection
-> Meta-OAK
-> M+/M-
-> strategy promotion
```

That is an executable architecture result, not a scientific-discovery result.

## OAK boundary

R0.1 does **not** establish:

- superiority over human scientists, AI Scientist systems, self-driving laboratories, Bayesian optimal design, active learning or other baselines;
- novelty or priority of individual concepts such as epistemic debt, fault tolerance, proof-carrying objects, active experimental design or evolutionary search;
- robustness to noisy, continuous, adversarial or high-dimensional scientific domains;
- causal discovery;
- ontology mutation;
- automatic invention of valid representations;
- safe autonomous self-modification;
- general scientific knowledge gain from a one-bit toy fixture.

Any future claim of superiority requires equal-budget external baselines, repeated seeds/fixtures, calibration, uncertainty, ablations, negative controls and independent validation.

## R0.2 promotion targets

The next useful increment is intentionally bounded:

1. add noisy/Bayesian theory survival rather than exact elimination;
2. compare random, fixed, variance-max and information-gain experiment policies;
3. expand fault injection to leakage, wrong priors, corrupted evidence and hidden confounders;
4. produce repeated-seed confidence intervals;
5. make the strategy selector itself a sandboxed mutation target;
6. keep all promotion decisions replayable from serialized evidence.

## Mother invariant

```text
Generate broadly -> discriminate cheaply -> attack aggressively -> promote rarely.
```
