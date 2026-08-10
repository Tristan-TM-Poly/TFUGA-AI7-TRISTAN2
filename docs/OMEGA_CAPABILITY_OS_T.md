# Ω-CAPABILITY-OS-T∞ — Capability Fabric R0.1

Status: **prototype executable / planner déterministe / non-autonome**

Ω-CAPABILITY-OS-T∞ is the capability-selection and evidence layer that sits below
`Ω-INTENT-TO-EVERYTHING`: the intent system decides *what work should exist*;
Capability OS decides *which available capability chain should be used*, with health,
authority, fallbacks, information value and SHA freshness kept explicit.

## Core loop

```text
Intent
  -> required information/output tokens
  -> Capability Genome registry
  -> dependency-aware planner
  -> health-adjusted utility
  -> read-before-write authority gate
  -> selected capability chain
  -> execution outside this package
  -> EvidenceReceipt
  -> OAK freshness check
  -> M+ / M- outcome record
```

The package deliberately does **not** execute remote tools. It plans and audits
capabilities. Connectors/agents remain the execution layer.

## Capability Genome

Each capability declares:

- domains;
- consumed and produced tokens;
- authority: `read`, `draft`, `write`, or `irreversible`;
- quality, information gain, verifiability, reuse, cost, latency and risk;
- explicit alternatives and failure modes.

The base utility is:

```text
0.24 quality
+ 0.20 information_gain
+ 0.18 verifiability
+ 0.16 reuse
- 0.08 cost
- 0.06 latency
- 0.08 risk
```

Health then multiplies utility: PASS=1.0, UNKNOWN=0.9, DEGRADED=0.6, FAIL=0.

## Authority invariant

Read/draft capabilities may be planned by default.
`write` requires `allow_mutation=true`.
`irreversible` requires both `allow_mutation=true` and `allow_irreversible=true`.

Planning permission is not execution authorization. The external executor must still
obey its own authorization policy.

## PR #415 bootstrap evidence

The first live benchmark came from Ω-CHATMEM-HGFM-T∞ PR #415:

1. CI reported failure.
2. Workflow/job inspection localized the failure to `Unit tests`.
3. one generic log route returned empty content;
4. the specialized GitHub Actions job-log capability returned the real cause:
   `No module named pytest`;
5. the PR later moved and merged, so stale-head repair was abandoned;
6. the merged head then reported successful ChatMem CI.

This is retained as the canonical R0.1 lesson:

```text
capability failure -> M- -> fallback -> diagnosis -> refresh SHA -> do not repair stale state
```

## Commands

```bash
python -m omega_capability_os_t describe examples/capability_os_registry.json
python -m omega_capability_os_t plan \
  examples/capability_os_registry.json \
  examples/capability_os_intent_pr_ci.json \
  --health examples/capability_os_health_pr415.json

python -m omega_capability_os_t fallback \
  examples/capability_os_registry.json github.fetch_generic_logs \
  --health examples/capability_os_health_pr415.json
```

## OAK boundary

A `PASS` receipt means only:

- the requested outputs were covered by the deterministic plan; and
- the evidence SHA exactly matches the candidate SHA.

It does not prove that a program is correct, that a scientific claim is true, that
a PR should be merged, or that an external action is authorized.

## Next convergence

The most valuable next step is an adapter from `omega_intent_t` work units into
Capability OS intents, followed by a runtime executor that records actual tool receipts.
Do not duplicate the existing intent planner.
