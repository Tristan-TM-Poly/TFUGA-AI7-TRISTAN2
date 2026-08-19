# Ω Knowledge Rights Kernel — R0.2

This directory turns the R0.1 Knowledge Rights / Controlled Disclosure architecture into a small deterministic executable kernel.

Status: **technical prototype**. It is not legal advice, does not determine ownership, trade-secret status or jurisdictional compliance, and does not replace qualified legal/privacy/security review.

## What is executable now

```text
KnowledgeRightsGenome
+ Request
→ validate
→ policy conflicts
→ expiry / purpose / operation gates
→ ALLOW | ESCALATE | DENY
→ DisclosureReceipt (when disclosure is authorized)
```

The prototype deliberately keeps `REDACT` and `SANDBOX` as future capabilities instead of pretending to implement semantic redaction or secure isolation.

## Permanent invariants

```text
Generated != Verified
Policy != Law
Receipt != LegalProof
CanSee != CanExport != CanPublish
ReadPermission != AITrainingPermission
Confidentiality < ApplicableLaw
Conflict => fail closed
```

## Files

- `knowledge_rights.py` — deterministic policy evaluator, conflict checker and receipt generator.
- `schemas/knowledge_rights_genome.schema.json` — interchange contract for one governed asset.
- `tests/test_knowledge_rights.py` — OAK test court.

## Quick test

```bash
python -m unittest discover -s omega_knowledge_rights/tests -v
```

No third-party dependency is required.

## R0.2 decision semantics

A request contains:

```text
(actor, asset_id, purpose, operation, timestamp, context)
```

The evaluator follows this order:

1. reject malformed genomes or requests;
2. if a policy conflict touches the requested operation, return `DENY`;
3. if the permission expired, return `DENY`;
4. if the context declares a legally required/protected disclosure path, return `ESCALATE` for qualified handling rather than silently suppressing it;
5. if the purpose is not explicitly allowed, return `DENY`;
6. if the operation is explicitly forbidden, return `DENY`;
7. if the operation is not explicitly allowed, return `DENY`;
8. otherwise return `ALLOW`.

`READ` never implies `TRAIN`, `EXPORT`, `PUBLISH`, `DERIVE`, or another operation.

## Conflict model

Rules can additionally narrow permissions by actor/purpose. A conflict exists when two applicable rules express opposite decisions for the same operation under overlapping scope. The kernel fails closed on that operation and reports the conflicting rule IDs.

## DisclosureReceipt

An authorized disclosure can emit a receipt that records:

- asset ID;
- actor;
- purpose;
- operation;
- policy version;
- timestamp;
- SHA-256 of the disclosed manifest/payload description;
- decision and OAK invariants.

The receipt proves what the software recorded about the governed event. It does **not** prove truth, legal enforceability or ownership.

## Next gates

R0.3 should only add capabilities that can be independently tested:

- `REDACT` with deterministic field-level disclosure capsules;
- `SANDBOX` only after a real isolation boundary exists;
- policy composition across multiple assets/contracts;
- cumulative disclosure/reconstruction benchmark;
- signed receipts only after key custody and rotation are defined;
- integration with GitHub/Drive permissions without creating a second authority system.
