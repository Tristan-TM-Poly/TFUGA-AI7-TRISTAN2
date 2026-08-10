---
name: capability-os
description: Plan, execute, suspend/resume and audit multi-tool capability chains with health-aware fallbacks, authority gates, external connector requests, SHA freshness, and OAK/M-minus receipts.
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
9. Keep external request arguments redacted in audit artifacts by default; expose them only to the execution layer that needs to invoke the tool.
10. Treat tool availability, planning permission and external execution authorization as three separate facts.
11. Normalize a real connector result into `ExternalActionReceipt`; never treat prose about a result as an execution receipt.
12. Validate request ID, capability, connector, action, declared outputs and observed candidate SHA before resuming.
13. On failure, record M- and use only an explicit fallback that preserves outputs, inputs and authority.
14. Refresh mutable state such as PR head SHA before repair or promotion.
15. Require candidate SHA == evidence SHA before an OAK PASS can be issued.
16. Persist outcome/health evidence, but never persist raw private connector arguments unless explicitly required and safe.

## External suspend/resume

```text
CapabilityRuntime
  -> missing local handler
  -> ExternalResolver
  -> ACTION_REQUIRED
  -> redacted deterministic request
  -> authorized connector invocation outside package
  -> ExternalActionReceipt
  -> rerun same intent
  -> validated receipt consumed
  -> plan resumes
```

The package does not directly invoke GitHub, Files, Drive, Gmail, Calendar or Web.
It describes and validates the handoff to the real ChatGPT execution layer.

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
- planned write => authorized write.
- external request emitted => external action executed.
- receipt mentions success => declared outputs are present.
- audit request fingerprint => permission to persist raw arguments.
- large output volume => quality.
