---
name: capability-os
description: Plan, execute and audit multi-tool capability chains with WorkUnit bridging, health-aware fallbacks, authority gates, exact-SHA evidence, and OAK/M-minus receipts. Use when a task should select among multiple tools, compile omega_intent_t work units, or recover from degraded capabilities.
---

# Ω-CAPABILITY-OS-T∞

Use this skill as the capability-routing and evidence layer between an already-understood intent/work graph and actual execution.

## Procedure

1. Reuse the existing `omega_intent_t` intent/work graph; do not invent a duplicate orchestrator.
2. Compile `WorkUnit` objects into Capability OS tokens when the work already exists upstream.
3. Treat declared dependencies as evidence requirements: a missing dependency token must yield `HOLD`.
4. Load or derive the smallest relevant Capability Genome.
5. Mark tool health from direct evidence only.
6. Plan read/draft work before writes.
7. Keep `write` and `irreversible` behind explicit authority gates.
8. Execute only through registered/authorized handlers. If none exists, emit `ACTION_REQUIRED`; never fabricate success.
9. On execution failure, write M- and use only fallbacks that preserve required outputs and remain authority-safe.
10. Record M+ for verified handler success and derive the next health snapshot from receipts.
11. Refresh mutable state such as a PR head SHA before repair, promotion, or merge.
12. Require `candidate_sha == evidence_sha` before an execution OAK PASS.
13. Keep planning permission, handler availability, and external authorization as three separate facts.

## WorkUnit bridge

```text
omega_intent_t.WorkUnit
  -> work-unit spec token
  -> dependency completion tokens
  -> synthetic generator capability
  -> artifact tokens
  -> validation capabilities
  -> validation tokens
  -> Capability OS plan
```

Normal/low/IP-sensitive work defaults to `draft`. Elevated/public work defaults to `write`. Irreversible work stays `irreversible`.

## Runtime receipt

A runtime execution records:

- selected plan fingerprint;
- actual capability outcomes;
- declared outputs and output fingerprints;
- sources and notes;
- `ACTION_REQUIRED` when a handler is unavailable;
- fallback recovery chains;
- M+ / M- outcome records;
- learned health snapshot;
- candidate/evidence SHA freshness;
- OAK boundary.

## PR/CI canonical fallback

```text
PR -> commit -> workflow runs -> specialized job logs
                              \-> annotations
PR ---------------------------> diff
```

A generic/raw log route that returns empty content is `DEGRADED`, not evidence that no error exists.

## Never infer

- PASS on one SHA => PASS on a later SHA.
- local PASS => CI PASS.
- CI PASS => scientific truth.
- planned write => authorized write.
- missing handler => successful execution.
- fallback availability => fallback authorization.
- large output volume => quality.
