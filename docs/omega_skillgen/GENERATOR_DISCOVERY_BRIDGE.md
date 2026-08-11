# Ω-SKILLGEN-T∞ × Ω-GENERATOR-DISCOVERY

The Skill Foundry reuses the existing Generator Discovery atlas instead of creating a disconnected generator universe.

## Deterministic bridge

`GeneratorRecord → SkillSpec candidate`

The bridge preserves the source record fields used by the atlas: generator id, domain, family, scale, representation, status, invariant, risk, OAK gate, and linked benchmark ids.

The resulting SkillSpec must keep the following distinctions:

- catalog membership != scientific correctness;
- linked benchmark id != benchmark PASS;
- generator status != promotion status of the generated Skill;
- OAK/risk metadata cannot be silently dropped during conversion;
- Skill packaging cannot grant external tool permissions.

## CVCD compression

Before producing large Skill families, `omega_skillgen_t.cvcd.extract_primitives` canonicalizes workflow and invariant atoms and reports shared candidates with their support and source Skills.

This is a structural compression heuristic, not proof of semantic equivalence. Similar-looking atoms still require review before being merged into one canonical primitive.

## Promotion ledger

Skill promotion follows:

`DRAFT → STATIC_PASS → EVAL_READY → TRUST_REVIEWED → BEHAVIORAL_PASS → PROMOTE_CANDIDATE → PROMOTED`

Forward transitions may not skip evidence states. Backward transitions are allowed only as explicit rollbacks with a recorded reason.

## CLI

```bash
python scripts/omega-skillgen-bridge generator-bridge /tmp/specs --domain physics --limit 20
python scripts/omega-skillgen-bridge primitives spec-a.json spec-b.json --min-support 2
python scripts/omega-skillgen-bridge promotion-check DRAFT STATIC_PASS evidence.json
```

The bridge is intentionally bounded by `limit` so the first operation is selective and reviewable rather than blindly generating thousands of Skills.
