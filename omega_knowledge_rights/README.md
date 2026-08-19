# Ω Knowledge Rights Kernel — R0.3

This directory turns Knowledge Rights / Controlled Disclosure into a small deterministic executable kernel.

Status: **technical prototype**. It is not legal advice, does not determine ownership, trade-secret status or jurisdictional compliance, and does not replace qualified legal/privacy/security review.

## What is executable now

```text
KnowledgeRightsGenome
+ Request
→ policy court
→ ALLOW | ESCALATE | DENY
→ deterministic field-level DisclosureCapsule
→ cumulative Reconstruction Court
→ DisclosureReceipt / evidence
```

R0.3 adds the first bounded `REDACT`-like capability, but only as an **explicit top-level field allow-list projection**. It does not claim semantic redaction, anonymization, de-identification, privilege preservation, or resistance to arbitrary inference.

`SANDBOX` remains unimplemented until a real isolation boundary exists.

## Permanent invariants

```text
Generated != Verified
Policy != Law
Receipt != LegalProof
CanSee != CanExport != CanPublish
ReadPermission != AITrainingPermission
Confidentiality < ApplicableLaw
Conflict => fail closed
Projection != semantic redaction
Structural reconstruction test != complete inference safety
```

## Files

- `knowledge_rights.py` — deterministic policy evaluator, conflict checker and DisclosureReceipt generator.
- `disclosure_capsule.py` — field-level capsule compiler + cumulative reconstruction court.
- `schemas/knowledge_rights_genome.schema.json` — interchange contract for one governed asset.
- `tests/test_knowledge_rights.py` — R0.2 policy court.
- `tests/test_disclosure_capsule.py` — R0.3 disclosure/reconstruction court.

## Quick test

```bash
python -m unittest discover -s omega_knowledge_rights/tests -v
```

No third-party dependency is required.

## R0.2 policy semantics

A request contains:

```text
(actor, asset_id, purpose, operation, timestamp, context)
```

The evaluator rejects malformed, expired, out-of-purpose, forbidden or ambiguous requests. A protected/lawful disclosure context is escalated for qualified handling instead of being silently suppressed.

`READ` never implies `TRAIN`, `EXPORT`, `PUBLISH`, `DERIVE`, or another operation.

## R0.3 DisclosureCapsule

A capsule spec declares:

```text
capsule_id
asset_id
operation
actors[] / purposes[]
include_fields[]
required_fields[]
exclude_fields[]
```

The compiler first requires the underlying Knowledge Rights request to be `ALLOW`. It then emits only fields named in `include_fields`; all other top-level fields are omitted. Required fields must exist and include/exclude conflicts fail closed.

The resulting manifest records the exact disclosed field names, omitted field names, payload SHA-256, policy version and the explicit statement:

```text
semantic_redaction_claimed = false
```

## R0.3 cumulative Reconstruction Court

A single capsule can be safe while a sequence of capsules becomes unsafe. R0.3 therefore evaluates the union of fields disclosed across history plus a candidate capsule.

A reconstruction rule is explicit and falsifiable:

```text
rule_id = "reconstruct-X"
required_fields = ["part_a", "part_b", ...]
```

If the candidate completes a protected field set that history had not already completed, the candidate is blocked with `cumulative_reconstruction_risk`.

The court distinguishes:

- `already_triggered_rule_ids` — historical risk that predates the candidate;
- `newly_triggered_rule_ids` — marginal risk caused by adding the candidate;
- `safe_to_add` — true only when no new explicit rule is completed.

This benchmark is **structural only**. It cannot prove safety against semantic inference, side channels, external knowledge, model memorization, screenshots, transcription, or an adversary that derives information not encoded in the declared field-set rules.

## Next gates

R0.4 should add only independently testable capabilities:

- policy composition across multiple assets/contracts without creating a second authority system;
- nested/path-aware disclosure projections with explicit type/schema checks;
- empirical reconstruction adversaries beyond explicit field sets, benchmarked against false-positive/false-negative baselines;
- signed receipts only after key custody, rotation and revocation are defined;
- integration with GitHub/Drive permissions as evidence inputs, not replacements for provider authority;
- `SANDBOX` only after a real isolation boundary and escape tests exist.
