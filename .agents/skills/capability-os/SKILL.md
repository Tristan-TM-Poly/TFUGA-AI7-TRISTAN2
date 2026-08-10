---
name: capability-os
description: Plan, execute, suspend/resume and audit multi-tool capability chains with health-aware fallbacks, explicit external side-effect authority, ChatMem continuity, SHA freshness, and OAK/M-minus receipts.
---

# Ω-CAPABILITY-OS-T∞

Use this skill as the routing/execution boundary between an already-understood intent
and actual local or external capability execution.

## Procedure

1. Reuse the existing intent/WorkUnit graph; do not invent a duplicate orchestrator.
2. Model required information or output as explicit tokens.
3. Load the smallest relevant Capability Genome registry.
4. Mark tool health from direct evidence only.
5. Plan read-only discovery before writes.
6. Prefer information gain, verifiability and reuse; penalize cost, latency and risk.
7. Execute registered local handlers when available.
8. For a missing handler, use an `ExternalBinding` only if one exists and emit a deterministic `ExternalActionRequest`.
9. Keep external request arguments redacted in audit artifacts by default; expose them only to the execution layer that must invoke the tool.
10. Treat capability authority and external side-effect authority as separate fields. A binding may never require more authority than its Capability node declares.
11. Treat **every persistent remote mutation** as `write` or `irreversible`, even if the provider calls it a draft, cache, label, checkpoint or convenience action.
12. Treat tool availability, planning permission and external execution authorization as three separate facts.
13. Normalize a real connector result into `ExternalActionReceipt`; never treat prose about a result as an execution receipt.
14. Validate request ID, capability, connector, action, declared outputs, mutation attestation and observed candidate SHA before resuming.
15. On failure, record M- and use only an explicit fallback that preserves outputs, inputs and authority.
16. Refresh mutable state such as PR head SHA before repair or promotion.
17. Require candidate SHA == evidence SHA before an OAK PASS can be issued.
18. Persist outcome/health evidence, but never persist raw private connector arguments unless explicitly required and safe.

## External suspend/resume

```text
CapabilityRuntime
  -> missing local handler
  -> ExternalResolver
  -> ACTION_REQUIRED
  -> redacted deterministic request
  -> separately authorized connector invocation
  -> ExternalActionReceipt
  -> validate side-effect contract
  -> rerun same intent
  -> validated receipt consumed
  -> plan resumes
```

The package does not directly invoke GitHub, Files, Drive, Gmail, Calendar or Web.
It describes and validates the handoff to the real ChatGPT execution layer.

## R0.4 side-effect invariant

```text
binding.external_authority <= capability.authority
```

with the ordered authority lattice:

```text
read < draft < write < irreversible
```

A successful `write` or `irreversible` external request must explicitly attest
`mutation_performed=true`. A `read`/`draft` request whose receipt claims remote
mutation fails closed.

This is not proof that the provider action is harmless. The binding author must label
the action by its real external side effect, not by its name.

## ChatMem continuity path

For Tristan-memory work, use the built-in ChatMem R0.4 capability family.

### Bootstrap

```text
Library pointer search
  -> Library context search
  -> GitHub fallback only if needed
  -> no mutation
```

Bootstrap is always read-only.

### Checkpoint

```text
checkpoint manifest
  -> local OAK/privacy/provenance preflight
  -> Library bundle persistence
  -> GitHub public-derived checkpoint creation
  -> both receipts required
  -> global pointer update
```

Checkpoint persistence stays `HOLD` unless `allow_mutation=true`.

The local preflight requires:

- `oak_status = PASS`;
- `public_derivation_only = true`;
- `raw_transcript_committed = false`;
- non-empty source hashes;
- explicit previous checkpoint.

The pointer update consumes both Library and GitHub checkpoint receipts, so the plan
cannot advance the canonical pointer after only one persistence surface succeeds.

## PR/CI canonical fallback

```text
PR -> commit -> workflow runs -> specialized job logs
                              \-> annotations
PR ---------------------------> diff
```

A generic/raw log route that returns empty content is `DEGRADED`, not evidence that
no error exists.

## Never infer

- PASS on one SHA => PASS on a later SHA.
- local PASS => CI PASS.
- CI PASS => scientific truth.
- tool exists => permission to call it.
- capability says `read` => arbitrary bound action is read-only.
- planned write => authorized write.
- external request emitted => external action executed.
- receipt mentions success => declared outputs are present.
- write request success without mutation attestation => mutation happened.
- ChatMem checkpoint created => pointer may advance before both persistence receipts.
- audit request fingerprint => permission to persist raw arguments.
- large output volume => quality.
