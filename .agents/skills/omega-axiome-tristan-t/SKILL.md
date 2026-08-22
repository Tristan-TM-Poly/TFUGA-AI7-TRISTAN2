---
name: omega-axiome-tristan-t
description: Compile, audit, attack, version, bound, and regenerate Tristan axioms and general claims as proof-carrying ClaimPassports and AxiomGenomes. Use when the user asks to develop Axiome-Tristan.com, formalize a theory, turn a claim into an auditable object, compare axiom variants, generate bounded counterclaims, produce an OAK epistemic status, or derive a BOOK0 regeneration manifest.
---

# Ω‑AXIOME‑TRISTAN‑T∞ — Proof-Carrying Knowledge Compiler

Treat every important statement as a typed candidate, never as truth by default.

## Canonical loop

`INTENT → CLAIM PASSPORT → TYPE/SCOPE AUDIT → COUNTERCLAIMS → DISCRIMINATING PROBES → OAK → M+/M− → VERSION/BOUND → REGENERATE`

## Required Claim Passport dimensions

- statement and claim id;
- epistemic kind and status;
- operational definitions;
- explicit domain and scope;
- assumptions and dependencies;
- supporting evidence and counterevidence;
- uncertainty dimensions;
- falsifiers or formal proof obligations;
- provenance and version lineage;
- generator and judge identity when applicable.

## Workflow

1. Normalize the user statement without silently strengthening it.
2. Invoke `omega-claim-passport-t` semantics to expose terms, scope, evidence, uncertainty, and falsifiers.
3. Run OAK hard gates before calculating any heuristic score.
4. Invoke `omega-axiome-adversarial-court-t` semantics for counterclaims, scope narrowing, boundary hunts, baselines, and discriminating predictions.
5. Preserve failed gates and invalidated variants as M− rather than deleting them from history.
6. Bound the surviving claim to the strongest domain actually supported by evidence.
7. Version changes and propagate dependency impact when a foundational claim changes.
8. Use BOOK0 regeneration only relative to an explicit ProbeFamily.
9. Require independent or externally grounded evidence before strong empirical promotion.
10. Stop adding META layers when measured out-of-sample gain does not dominate added debt.

## Repository commands

```bash
python -m omega_axiome_tristan_t audit interfaces/axiome-tristan/examples/sample_axiom.json
python -m omega_axiome_tristan_t mutate interfaces/axiome-tristan/examples/sample_axiom.json
python -m omega_axiome_tristan_t regen interfaces/axiome-tristan/examples/sample_axiom.json
python -m omega_axiome_tristan_t book0
python -m unittest tests.test_omega_axiome_tristan_t -v
node --test tests/js/axiome-tristan-kernel.test.mjs
```

## OAK invariants

- `Generated != Verified`.
- `Formalized != True`.
- `Simulation != Reality`.
- `Generator != Judge` for material promotion decisions.
- `ClaimScope <= EvidenceScope` once evidence-bearing status is claimed.
- `Revenue != Truth`; commercial success cannot upgrade epistemic status.
- `Capability != Authority`.
- `LocalPASS != GlobalPASS`.
- Absence of a known counterexample is not proof.
- A heuristic ranking is never a truth ranking.
- An experiment candidate is not permission to execute a risky or human-subject experiment.
- Publication, payments, deployments, legal commitments, and privileged external actions retain their actual authority boundaries.

## Regeneration boundary

`Rebuild(K*) ≈ K*` is always relative to declared probes. Preserve residuals and unknown behavior outside the probe family; never promote deterministic replay into proof of scientific correctness.
