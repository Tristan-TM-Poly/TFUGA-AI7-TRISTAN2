# Ω GitHub Constellation R0.2

## Purpose

R0.2 replaces the private-only repository constellation with a fail-closed public/private architecture.

The target shape is deliberately small:

### Public commons

- `omega-protocol` — stable schemas and interoperability contracts.
- `omega-kernel` — canonical Cognitive ISA, Generative Closure, GO MAX/MIN, synergy and self-distillation algorithms.
- `omega-oak` — public validation, uncertainty, proof-debt and conformance gates.
- `omega-bench` — deterministic public benchmarks, synthetic fixtures and reproducibility courts.

### Private operating fabric

- `tristan-fabric` — privileged orchestration, Repo Genesis and lifecycle control.
- `tristan-observatory` — observe-once/derive-many snapshots, temporal repo atlas and archaeology.
- `tristan-memory` — cumulative M+/M-/M?/M-delta/synergy memory and memory lenses.
- `tristan-llmt` — private LLMT routing, sparse coalitions, Self-Model and Value of Computation.

## Dependency law

Public repositories must never require private repositories to build, test or import.

Private repositories may consume public contracts and kernels.

```text
PUBLIC COMMONS -> PRIVATE FABRIC
```

The reverse dependency is a HOLD condition.

## VisibilityGate

A public declaration is accepted only when:

1. at least one explicit public driver is declared (`protocol`, `kernel`, `benchmark`, `documentation`, `conformance`, `public_evidence`);
2. no private blocker is declared (`secrets`, `personal_data`, `customer_data`, `unpublished_ip`, `restricted_third_party_data`, `privileged_authority`).

Unknown drivers or blockers fail closed.

Private remains the default.

## Materialization gate

A valid public spec is still not publication authority.

The repository factory requires `allow_public=True` (CLI: `--allow-public`) before sending a repository-creation request with `private=false`.

Without that explicit gate, the result is:

```text
HOLD_PUBLIC_REQUIRES_EXPLICIT_ALLOW_PUBLIC
```

No public repository request is emitted.

## OAK boundaries

- public visibility != IP clearance
- public visibility != license clearance
- public visibility != privacy clearance
- schema stability != scientific truth
- CI green != external validation
- repository creation != validated usefulness
- source PR provenance != canonical promotion
- private blocker != permanent secrecy; it means review is required before public promotion

## Physicalization order

The intended target has eight repositories, but R0.2 does not require creating eight repositories immediately.

Recommended first pair:

1. `omega-protocol` (public)
2. `tristan-observatory` (private)

Then promote additional RepoCells only after measured reuse, independent release pressure and OAK evidence justify physical separation.

```text
VirtualRepo -> measured reuse -> split court -> visibility gate -> reviewed materialization
```
