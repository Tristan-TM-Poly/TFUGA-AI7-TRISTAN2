# Ω-RE-T∞ R0.4 — Probabilistic, Symbolic and Executed-Baseline Layer

## Status

R0.4 extends the authorized synthetic reverse-engineering laboratory with five bounded capabilities:

1. probabilistic finite transducers and Dirichlet uncertainty;
2. conservative symbolic state merging over finite traces;
3. active intervention selection over explicit causal hypotheses;
4. append-only HMAC-authenticated receipts;
5. baseline execution reports separated from logical benchmark materialization.

The implementation remains a software research prototype. It does not reveal inaccessible internals, authorize access, prove causal truth outside declared synthetic models, or convert benchmark generation into empirical validation.

## Epistemic invariants

```text
behavioral likelihood != internal identity
symbolic merge != proof of one true state decomposition
expected information gain != permission to intervene
HMAC authentication != public-key signature or legal notarization
executed software case != scientific experiment
materialized case != executed case
```

## Probabilistic transducers

`probabilistic_r04.py` complements the existing R0.2 probabilistic engine without replacing its API. It models every `(state, input)` as an explicit distribution over `(next_state, output)` outcomes and provides:

- normalization with finite/non-negative checks;
- reproducible seeded sampling;
- exact finite trace probability by state-mass propagation;
- trace log-likelihood;
- total-variation comparison on a declared query set;
- Dirichlet-smoothed posterior estimation over declared support;
- posterior entropy.

Unknown support is never silently invented. A zero-probability observation remains a model-class failure signal.

## Symbolic merging

`symbolic_merge.py` constructs a prefix-tree transducer from finite input/output traces. Nodes are grouped only by bounded recursive signatures. Conflicting outputs for the same observed prefix and symbol are recorded as explicit conflicts and never averaged away.

The output claim is `bounded_symbolic_equivalence_only`.

## Active causal intervention design

`active_causal.py` ranks reversible, authorized intervention candidates by expected information gain per cost minus risk penalty. Hypotheses expose explicit Bernoulli outcome probabilities and priors. Association-only evidence is not promoted to interventionally supported causality.

Blocked interventions receive no executable utility.

## Authenticated receipts

`authenticated_receipts.py` provides domain-separated HMAC-SHA256 receipt chains. Each entry binds:

- sequence;
- event;
- payload digest;
- previous digest;
- chain digest;
- authentication tag.

The chain detects reordering, replacement and modification when the verifier holds the shared key. It is not a public-verifiability system and must not store the secret in Git.

## Baseline execution

`baseline_execution.py` records software execution separately from the RE-1024 frontier. A report contains independent counters:

```text
logical_cases
materialized_cases
executed_cases
software_tested_cases
scientifically_verified_cases
```

R0.4 fixes `scientifically_verified_cases = 0` for these synthetic software baselines. Exceptions become bounded failure receipts rather than disappearing.

## CLI

```bash
omega-re-r04 probabilistic-demo
omega-re-r04 symbolic-demo
omega-re-r04 causal-demo
omega-re-r04 receipt-demo
omega-re-r04 baseline-demo
omega-re-r04 all --output /tmp/omega-re-r04.json
```

## OAK gates

Promotion is blocked when:

- probabilistic support is empty, negative or non-finite;
- a trace observation lies outside declared support without downgrade;
- conflicting symbolic traces are silently merged;
- an intervention lacks authorization or reversibility;
- HMAC receipts are described as public-key signatures;
- logical/materialized counters are below executed counters;
- a software baseline claims scientific verification;
- deterministic replay changes without a declared version transition.

## R0.5 frontier

- Bayesian model-class expansion;
- active learning across probabilistic transducers;
- bounded context-free grammar induction;
- nonlinear hybrid basis libraries;
- public-key signed receipts with external key custody;
- isolated execution workers and lease recovery;
- calibrated confidence intervals over RE-1024 baseline families;
- differential privacy for authorized aggregate trace analysis.
