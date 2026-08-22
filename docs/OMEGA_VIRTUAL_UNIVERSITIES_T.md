# Ω-VIRTUAL-UNIVERSITIES-T∞ / Ω-META-INSTITUTION-GENESIS-T∞

## Status

OAK-3 architecture + OAK-4 local static cockpit target. Production multiplayer remains unverified until an authenticated backend, persistence, realtime events, authorization tests and real-user validation exist.

## Goal

Allow subscribers to instantiate, join, fork and evolve virtual universities populated by humans and clearly identified Tristan Virtual AI agents. A university is an executable InstitutionGenome rather than a fixed course catalog.

## Mother loop

```text
GOAL / NEED
→ UniversityGenome / InstitutionGenome
→ SHADOW / SANDBOX INSTANCE
→ HUMANS + TRISTAN VIRTUALS
→ LEARN / RESEARCH / BUILD
→ EVIDENCE RECEIPTS
→ OAK / RED TEAM / COUNTEREXAMPLES
→ PROMOTE / ROLLBACK
→ MUTATE / FORK / MERGE / PRUNE
→ REGENERATE
```

## Core contracts

### UniversityGenome

Minimum fields:

- identity, mission, lineage and visibility;
- lifecycle state;
- multiplayer room contract;
- authenticated member roles;
- Tristan Virtual roster;
- curriculum and research policies;
- governance constitution and risk tier;
- contribution/economy policy;
- evidence ledger;
- capability/debt metrics;
- OAK status, blockers and epistemic boundary.

Machine-readable schema:

```text
schemas/chatgpt-tristan/university_genome_contract.json
```

### Tristan Virtual identity rule

Every Tristan Virtual is an AI agent/persona. It must never be represented as the human Tristan. Agent identity, model/provider, authority scope and tool permissions should be inspectable.

## Production architecture

```text
Web UI
  ↓
Auth / Subscriber Identity
  ↓
University API
  ├─ UniversityGenome Store
  ├─ Membership / RBAC
  ├─ Realtime Room / Presence / Event Stream
  ├─ Tristan Virtual Agent Router
  ├─ Curriculum / Quest Engine
  ├─ Research Lab / Artifact Engine
  ├─ Evidence Ledger
  ├─ Fork / Merge / Rollback Engine
  ├─ OAK / Policy Engine
  ├─ Compute / Cost / Quota Governor
  └─ Audit / Export / Delete
```

## Multiplayer invariants

1. Tenant isolation: one university cannot read another private university without permission.
2. Membership is server-authoritative, not trusted from browser state.
3. Every mutation is attributable to a human principal, agent principal or system principal.
4. Realtime events are idempotent or replay-safe.
5. Permission changes are versioned and auditable.
6. Sensitive or irreversible external actions require explicit authority gates.
7. Agent capability does not imply permission.
8. A local simulation never upgrades a production claim.

## Fork / merge semantics

A fork creates a new stable institution identity with `parent_id`, inherited artifacts according to policy, independent governance and bounded permissions. A merge is a proposal, not an automatic overwrite. A merge should carry:

- source and target institution ids;
- exact InstitutionDiff;
- affected invariants;
- evidence and counterevidence;
- permission/authority impact;
- cost/risk impact;
- rollback plan;
- independent verification status.

## Evidence model

Allowed epistemic labels:

```text
OBSERVED
MEASURED
DERIVED
SIMULATED
HEURISTIC
CONJECTURED
PROVEN
```

`SIMULATED` evidence cannot silently become `MEASURED` or `PROVEN`. Production promotion requires evidence appropriate to the claim.

## University lifecycle

```text
SANDBOX
→ SHADOW
→ CANARY
→ ACTIVE
→ DORMANT / ARCHIVED / DISSOLVED
```

Every active institution should support export and a safe exit path for users. Dissolution should preserve only data permitted by retention policy and user rights.

## Extreme extensions

### InstitutionGenesis

`UniversityGenome` generalizes to `InstitutionGenome`, supporting laboratories, guilds, academies, companies, research cells and temporary mission institutions.

### InstitutionGeneratorGenerator

A meta-compiler can propose alternative institutional architectures. It may generate candidates, simulations and tests, but Generator != Judge: promotion requires independent checks and policy gates.

### Collective Capability OS

The higher-level primitive becomes dynamic assembly of humans + AI agents + tools + rules + resources around a goal, optimizing verified capability rather than institution count.

### Collective World Genesis

Multiple institutions may coexist in a bounded world with shared quests, inter-university research raids, cooperation, competition and portable evidence. Simulation != sociology and emergence != legitimacy.

## Anti-Goodhart rules

Do not optimize a single score such as grades, activity, retention or reputation. Separate at minimum:

- learning/mastery evidence;
- transfer to new tasks;
- research reproducibility;
- real-world validation where relevant;
- contribution provenance;
- safety/permission compliance;
- compute/cost;
- epistemic and coordination debt.

## Required production tests

- authentication and tenant isolation;
- unauthorized read/write denial;
- role escalation denial;
- room join/leave/reconnect;
- concurrent mutation conflict handling;
- event replay/idempotency;
- agent identity labeling;
- agent authority boundaries;
- fork lineage correctness;
- merge proposal non-destructiveness;
- rollback correctness;
- evidence type transition checks;
- quota/rate-limit enforcement;
- export/delete/exit flows;
- audit log integrity.

## Current v2.4 implementation boundary

The v2.4 cockpit in `interfaces/chatgpt-tristan-v2/` provides a local UniversityGenome generator, agent roster, bounded sandbox-cycle simulator, fork operation, JSON export and a compiler prompt for the production multiplayer backend.

It intentionally does **not** pretend to provide real subscriber multiplayer. The existing interface is a static local web application, so authenticated shared rooms require a separate backend and deployment layer.

## OAK constitution

```text
Agent != Human
Capability != Authority
Reputation != Evidence
Simulation != Reality
Generated != Verified
LocalPASS != GlobalPASS
Generator != Judge
Emergence != Legitimacy
```

## Crystallization target

The next promotion from OAK-4 local prototype to OAK-5 measured system requires a production-like authenticated multiplayer test with at least two independent subscriber principals, persisted state, permission tests, realtime reconnect tests, evidence receipts and measured usability outcomes.
