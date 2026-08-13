# Ω Generative Closure R0.2 — Meta-Closure Geometry

## Purpose

R0.2 extends the existing canonical Generative Closure rather than creating a second meta-closure ontology.

The implemented surface is deliberately small:

- discrete closure gradient over candidate seeds;
- pairwise closure curvature for superadditive or antagonistic interactions;
- GO MAX/MIN axes for interoperability, synergy and transferability;
- GO MIN debt axes for novelty debt, ontology debt, fragility and risk.

## Core equations

For a current seed set `K` and candidate `i`:

`delta_i C = |Closure(K + i)| - |Closure(K)|`.

For distinct candidates `i` and `j`:

`kappa(i,j) = |Closure(K+i+j)| - |Closure(K+i)| - |Closure(K+j)| + |Closure(K)|`.

Positive curvature is a structural superadditivity signal in this finite closure model. It is not by itself evidence of causal synergy outside the model.

GO MAX/MIN power density remains a heuristic scalarization. Pareto dominance remains the stronger multi-objective court.

## OAK boundaries

- finite-difference closure geometry != continuous differential geometry;
- positive closure curvature != causal synergy;
- a higher power-density score != proof of superiority;
- novelty debt is an engineering/accounting signal, not a claim about patent novelty;
- ontology debt measures proliferation pressure, not philosophical truth;
- structural closure != empirical or scientific truth.

## Explicit reuse

R0.2 keeps the existing `Rule`, `ClosureReport`, `compute_closure`, `primitive_necessity` and `MaxMinVector` canon. It does not introduce a second Cognitive ISA, Research ABI, OAK status system or Capability ontology.

The existing Discovery Kernel remains the source of current OAK status vocabulary. This PR does not create a competing epistemic type system.

## HOLD / next evidence-bound increments

The following ideas from the meta-theory are intentionally not claimed as implemented here:

- Residual Field and residual-priority tensor;
- bounded Minimal Verified Generating Basis search;
- Regeneration Bench / RCR;
- proof-carrying morphogenesis;
- epistemic compiler errors;
- representation arbitrage;
- architectural renormalization fixed points.

They should be introduced only after focused tests and necessity ablation show that they add capabilities not already present elsewhere in the repository.
