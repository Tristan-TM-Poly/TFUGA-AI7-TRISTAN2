# Ω-DISCOVERY-DYNAMICS-T R0.2

Status: executable research prototype. This document defines interfaces and deterministic fixtures; it does not establish historical novelty or general scientific superiority.

## Purpose

R0.2 compresses several high-leverage meta-science ideas into one reusable kernel:

```text
Scientific IR
    -> Discovery ABI
    -> epistemic sensitivity
    -> residual genome
    -> counterexample search
    -> representation arbitrage
    -> unknown-unknown candidate radar
    -> invariant transport
```

The design goal is not to add names. It is to create primitives that can be imported by physics, chemistry, software, optimization, research automation and OAK workflows.

## 1. Scientific IR

`ScientificIR` carries:

- variables;
- relations;
- unit bindings;
- assumptions;
- observables;
- domain;
- declared tests;
- provenance.

`validate()` is fail-closed for missing provenance, undeclared observables, unit bindings to unknown variables, missing relations and missing tests.

This is only a structural IR. Translation fidelity from papers, code or experiments remains a separate verification problem.

## 2. Discovery ABI

`DiscoveryABI` defines a minimal interface:

```text
predict
explain
falsify
uncertainty
provenance
cost
domain
represent
```

`TheoryAdapter` makes the existing R0.1 `TheoryGenome` consumable through that interface. The intent is to let future theories, simulators and learned models participate in the same discovery machinery without hard-coding their internals.

## 3. Epistemic Jacobian — OAK-safe meaning

R0.2 computes a central finite-difference derivative of a declared surrogate:

\[
D(x)=\operatorname{Var}\{T_i(x)\}.
\]

Then

\[
J_E(x)\approx\frac{D(x+h)-D(x-h)}{2h}.
\]

For the canonical pair `y=x` and `y=x^2`,

\[
D(x)=\frac{(x-x^2)^2}{4},
\qquad D'(2)=3.
\]

The CI test verifies the finite-difference result against this analytic derivative.

**Boundary:** this is a local sensitivity of a prediction-disagreement surrogate. It is not a derivative of truth, intelligence, scientific value or actual knowledge.

## 4. Residual Genome

Instead of storing only residual magnitude, R0.2 extracts a small feature vector:

- mean;
- RMS;
- linear slope;
- sign-change rate;
- lag-1 correlation;
- candidate structural signatures.

The signatures are deliberately named `*_candidate` because the features do not prove a causal mechanism.

This is designed as a bridge from M- evidence to theory mutation: structured residuals can later propose missing dynamics, scale terms or latent-variable hypotheses, but R0.2 performs no such causal promotion.

## 5. Counterexample Compiler

Given a theory-like object, an observer and a finite declared candidate set, the compiler returns

\[
x^*=\arg\max_x |y_{obs}(x)-y_{pred}(x)|.
\]

The R0.2 fixture asks a linear theory to confront a quadratic observer over `{0,1,2,3}`. The strongest declared counterexample is `x=3`, with residual `6`.

**Boundary:** finite candidate search does not prove a globally strongest counterexample and does not replace mathematical proof.

## 6. Representation Arbitrage

Each route carries:

- solve cost;
- transform cost;
- round-trip loss;
- invariant retention.

Routes first pass hard fidelity gates. Only then are eligible routes ranked by

\[
C_{route}=C_{solve}+C_{transform}+\lambda_L L+\lambda_I(1-I).
\]

The fixture includes a very cheap but lossy route. It is rejected despite its nominal speed. A transformed route wins over the native route only because it stays inside declared fidelity bounds.

This encodes the core law:

```text
solve in another representation only when round-trip fidelity survives OAK
```

## 7. Unknown-Unknown Candidate Radar

The radar combines four normalized signals:

- theory disagreement;
- residual surprise;
- representation instability;
- coverage gap.

It ranks locations where those weaknesses coincide.

The output explicitly carries:

```text
heuristic candidate signal; not evidence that an unknown unknown exists
```

This makes the primitive useful for exploration without converting uncertainty into a false discovery claim.

## 8. Invariant Transport Protocol

`InvariantTransportMap` is an explicit declared mapping between domains. Transport is certified only relative to that declared map and only when every requested source invariant has a mapping.

R0.2 does not infer mathematical isomorphisms or conservation laws automatically. It creates the protocol boundary required for later OAK-verified cross-domain transfer.

## 9. Canonical composed fixture

`run_discovery_dynamics_demo()` verifies that the pieces compose:

```text
valid Scientific IR
 -> TheoryGenome adapter
 -> J_E(2) ~= 3
 -> structured residual genome
 -> strongest finite counterexample x=3
 -> fidelity-gated representation arbitrage
 -> ranked unknown-unknown candidate signals
 -> complete declared invariant transport
```

Replay:

```bash
python -m omega_meta_science_t.discovery_cli
python -m omega_meta_science_t.discovery_cli --compact
```

Tests:

```bash
python -m pytest -q tests/test_omega_meta_science_t.py tests/test_omega_meta_science_discovery.py
```

## 10. What R0.2 demonstrates

R0.2 demonstrates executable reusable interfaces for:

- scientific intermediate representation;
- theory interoperability;
- local disagreement sensitivity;
- residual feature extraction;
- finite adversarial counterexample search;
- fidelity-gated representation selection;
- heuristic exploration-risk ranking;
- explicit invariant transport.

## 11. What R0.2 does not demonstrate

It does not establish:

- a universal scientific language;
- discovery of true unknown unknowns;
- automatic causal inference from residual shape;
- global optimality of counterexamples;
- general superiority of representation arbitrage;
- automatic discovery of cross-domain isomorphisms;
- autonomous self-improvement safety;
- historical novelty of the named concepts.

## 12. R0.3 promotion path

The strongest next experiments are:

1. noisy observations and calibrated uncertainty;
2. Bayesian / information-gain experiment policies;
3. residual genomes over real or recognized benchmark datasets;
4. adversarial counterexample search beyond finite grids;
5. round-trip tests over actual alternative representations;
6. learned validity regions;
7. epistemic checksums and claim dependency invalidation;
8. cross-domain invariant transport with independently verified mappings;
9. ablations showing which Discovery Dynamics primitives add measurable value.

Operating law:

```text
ambitious name -> bounded interface -> deterministic fixture -> fault boundary -> benchmark -> only then promotion
```
