---
name: capability-os
description: Plan and audit multi-tool capability chains with health-aware fallbacks, authority gates, SHA freshness, and OAK/M-minus receipts. Use when a task should select among multiple tools or recover from degraded capabilities.
---

# Ω-CAPABILITY-OS-T∞

Use this skill as the routing layer between an already-understood intent and actual
tool execution.

## Procedure

1. Reuse the existing intent/work graph; do not invent a duplicate orchestrator.
2. Model required information or output as tokens.
3. Load the smallest relevant Capability Genome registry.
4. Mark known tool health from direct evidence only.
5. Plan read-only discovery before writes.
6. Prefer high information gain, verifiability and reuse; penalize cost, latency and risk.
7. On failure, record M- and use an explicit fallback.
8. Refresh mutable state such as PR head SHA before any repair or promotion.
9. Require candidate SHA == evidence SHA before an OAK PASS can be issued.
10. Treat planning permission and external execution authorization as separate gates.

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
- planned write => authorized write.
- large output volume => quality.
