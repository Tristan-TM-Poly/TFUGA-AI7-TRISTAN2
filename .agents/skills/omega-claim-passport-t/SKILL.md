---
name: omega-claim-passport-t
description: Normalize scientific, mathematical, engineering, economic, organizational, or operational statements into explicit Claim Passports with definitions, scope, assumptions, evidence, counterevidence, uncertainty, falsifiers or proof obligations, provenance, and bounded epistemic status. Use when a claim is vague, over-broad, evidence-sensitive, disputed, or needs an auditable knowledge object.
---

# Ω‑CLAIM‑PASSPORT‑T∞ — Universal Claim Normalizer

Convert rhetoric into an auditable object while preserving unresolved residuals.

## Contract

A Claim Passport should expose:

`Claim + Meaning + Kind + Domain + Scope + Assumptions + Dependencies + Evidence + CounterEvidence + Uncertainty + Falsifiers/ProofObligations + Provenance + Version + Status`

## Court

1. Find undefined or overloaded terms and request/derive operational definitions only when defensible.
2. Separate descriptive, causal, normative, predictive, and formal content instead of collapsing them into one statement.
3. Declare the smallest meaningful scope and domain.
4. Bind each supporting evidence item to the scope dimensions it actually supports.
5. Preserve counterevidence and conflicting observations explicitly.
6. Reject epistemic inflation: do not promote `SIMULATED → PROVEN`, local evidence → universal law, or correlation → causation without new evidence.
7. Produce the strongest bounded status justified by the current record and list the residuals blocking the next status.

## Hard invariant

`ClaimScope <= EvidenceScope`

For evidence-bearing statuses, uncovered scope dimensions create a HOLD or require claim narrowing. Before evidence exists, the claim can remain an IDEA/CONJECTURE/TESTABLE candidate but must not masquerade as established knowledge.

## Domain-aware typing

- Empirical scientific claims require observations/experiments appropriate to the claim.
- Replication status requires meaningful independent replication evidence.
- Formal verification requires an explicit formal statement and compatible formal-proof evidence.
- Engineering principles may be benchmarked within a declared operational regime but must not be generalized beyond it automatically.
- Economic performance evidence does not establish scientific truth.
- Normative preferences require governance/authority treatment rather than truth-score laundering.

## OAK invariants

- Undefined terms are residuals, not silently fixed semantics.
- Counterevidence cannot be hidden to pass a gate.
- `Formalized != True`.
- `Correlation != Causation`.
- `LocalResult != UniversalLaw`.
- `Confidence != Proof`.
- Provenance must survive transformations and versioning.
