# Ω-COMPANY-OUTREACH-T∞ — R1.0 Foundation A

## Status

This document describes the first industrial foundation stacked above PR #282.
It is a control, evidence and data-model layer. It does not send email, sign a
contract, move money, file government forms or activate production.

## Objective

Foundation A converts the R0.2 outreach cases into a durable operating model:

```text
company identity
→ organization evidence
→ privacy-preserving contact
→ consent decision
→ strategic opportunity
→ append-only event
→ relationship graph
→ deterministic projection
→ OAK scenario validation
```

The design separates the following objects:

- Tristan as a human person;
- an authenticated personal Gmail account;
- an internal operating role;
- a public brand candidate;
- a verified domain;
- a verified legal entity;
- an authority grant;
- an approved external action.

These objects are not interchangeable.

## Delivered packages

### `foundation.canonical`

Provides:

- canonical JSON serialization;
- UTC datetime normalization;
- SHA-256 hashes;
- HMAC-SHA-256 pseudonyms;
- public identifier validation;
- domain and email normalization;
- vault reference validation;
- secret-like key rejection;
- stable unique collections.

Canonical hashes are calculated from deterministic JSON. Sets are sorted,
enums use their values, datetimes use UTC with a `Z` suffix, mappings are
sorted by key and non-finite floats are rejected.

### `foundation.identity`

Defines the company identity state machine:

```text
CONCEPT
→ INTERNAL_ROLE
→ BRAND_CANDIDATE
→ DOMAIN_VERIFIED
→ LEGAL_ENTITY_VERIFIED
→ BANKING_VERIFIED
→ TAX_VERIFIED
→ CONTRACT_READY
→ PRODUCTION_COMPANY
```

Each transition is explicit. A company cannot skip directly from an internal
role to a verified legal entity. A corporate sender claim requires both legal
entity evidence and a verified domain.

Authority grants are bounded by:

- person;
- company;
- role;
- permissions;
- validity window;
- revocation;
- monetary amount;
- jurisdiction;
- evidence hash.

Two required approvers must be distinct people, not different spellings of the
same identifier.

### `foundation.organizations`

Defines organizations, divisions and evidence.

Organization evidence records:

- source kind;
- source hash;
- observation time;
- public-safe claim;
- confidence;
- official-source flag;
- optional expiration.

Organization deduplication combines:

- canonicalized name;
- official suffix removal;
- domain overlap;
- country;
- region;
- token similarity.

A probable duplicate is surfaced for review. The system does not silently
merge unrelated organizations.

### `foundation.contacts`

Defines a privacy-preserving contact registry.

GitHub may contain:

- pseudonymous contact identifier;
- organization identifier;
- professional role category;
- recipient SHA-256 or HMAC-SHA-256;
- `vault://` references;
- public evidence hashes;
- contact state;
- communication preferences.

GitHub must not contain:

- raw email address;
- private name when unnecessary;
- telephone number;
- Gmail message identifier;
- OAuth token;
- message body;
- confidential notes.

The contact state machine includes discovery, verification, contactability,
contact, engagement, inactivity, bounce and suppression.

### `foundation.consent`

Defines consent, communication policies and suppression.

Supported consent bases include:

- express consent;
- existing business relationship;
- existing non-business relationship;
- conspicuously published professional contact;
- inbound request;
- referral;
- transactional necessity;
- legitimate professional context.

Consent is scoped. A valid research-collaboration basis does not automatically
permit commercial marketing.

Suppression always overrides consent. Permanent suppressions cannot expire.
Temporary suppressions require an explicit expiration.

The default commercial marketing policy requires express consent and an
unsubscribe mechanism.

### `foundation.opportunities`

Defines 16 opportunity types and four company routes.

Parent OpCo owns:

- entrepreneurship programs;
- financing programs;
- strategic partnerships;
- grants;
- referrals.

OAK Systems owns:

- audit services;
- security reviews.

Software Labs owns:

- software pilots;
- integrations;
- licensing;
- procurement.

Research Foundry owns:

- research pilots;
- data partnerships;
- publications;
- open-source collaborations;
- advisory relationships.

The strategic tensor includes positive value signals and explicit cost/risk
signals. A geometric mean prevents a single high number from fully hiding a
critical weak dimension.

Bayesian stages separately model:

```text
P(response)
P(meeting | response)
P(pilot | meeting)
P(payment | pilot)
```

A refusal updates the posterior but does not erase the organization or the
historical evidence.

The portfolio allocator enforces:

- active-case capacity;
- maximum open cases;
- effort budget;
- minimum score;
- high-risk concurrency.

### `foundation.events`

Defines the event vocabulary and projections.

Examples:

- organization discovered;
- contact verified;
- consent recorded;
- opportunity created;
- message prepared;
- message sent;
- reply received;
- meeting created;
- proposal created;
- pilot completed;
- payment reconciled;
- M− incident recorded.

### `foundation.event_store`

Provides the canonical persistence runtime.

Properties:

- JSONL append-only format;
- one sequence per aggregate;
- previous-hash chain per aggregate;
- unique event identifiers;
- consumed idempotency keys;
- canonical datetime serialization;
- tamper detection before append;
- deterministic snapshots.

Provider acceptance is not treated as final business success. Delivery,
signature, payment, filing and deployment reconciliation remain separate.

### `foundation.graph`

Defines nodes, edges and hyperedges for:

- companies;
- organizations;
- divisions;
- contacts;
- consent;
- opportunities;
- assets;
- evidence;
- outreach cases;
- messages;
- replies;
- meetings;
- proposals;
- pilots;
- contracts;
- payments;
- incidents.

The graph supports:

- adjacency queries;
- filtered neighbors;
- shortest paths;
- subgraphs;
- connected components;
- duplicate-edge detection;
- responsibility hyperedges;
- deterministic JSON export.

A responsibility hyperedge can state:

```text
Research Foundry owns the opportunity
+ Software Labs contributes implementation
+ OAK Systems validates evidence
+ Parent OpCo approves strategy
```

Only one company is the owner.

### `foundation.migration`

Migrates R0.2 public-safe cases into:

- organization;
- contact;
- consent;
- opportunity;
- five initial domain events.

The migration refuses a legacy case that claimed legal entity status because
that requires manual verification.

### `foundation.migration_runtime`

Serializes migrations canonically instead of converting dataclasses into
opaque strings.

The two current migration targets are:

- `OUT-2026-0001` — Futurpreneur Canada;
- `OUT-2026-0002` — Polytechnique Montréal.

Raw addresses and Gmail IDs remain outside GitHub.

### `foundation.schemas`

Generates a versioned JSON Schema catalog for:

1. company identity;
2. authority grant;
3. organization;
4. contact record;
5. consent record;
6. suppression entry;
7. opportunity;
8. domain event;
9. graph node;
10. graph edge;
11. OAK scenario;
12. migration bundle.

Every generated schema receives:

- a stable schema ID;
- a version;
- a canonical hash;
- a catalog entry.

The schema audit regenerates expected hashes and detects modification.

### `foundation.scenario_atlas`

Defines the OAK scenario dimensions:

- company;
- organization type;
- opportunity type;
- identity state;
- organization state;
- contact state;
- role category;
- consent basis;
- consent scope;
- consent state;
- opportunity state;
- risk class;
- authority level;
- evidence band;
- strategic-score band.

The theoretical Cartesian space exceeds one hundred million combinations.
Foundation A does not execute the complete Cartesian product on every commit.
It creates deterministic stratified scenarios and verifies coverage.

Default CI generation:

```text
8 192 scenarios
16 shards
512 scenarios per shard
fixed seed 20260802
double generation
recursive diff
```

Decisions include:

- allow preparation;
- require evidence;
- require consent;
- require human approval;
- require dual approval;
- require professional review;
- wait;
- block.

### `foundation.scenario_runtime`

Provides canonical scenario serialization compatible with slots dataclasses,
round-trip parsing, manifest validation and deterministic regeneration.

## CLI

The package exposes:

```bash
omega-outreach-foundation identity-example
omega-outreach-foundation canonical-hash object.json
omega-outreach-foundation event-audit events.jsonl
omega-outreach-foundation event-project events.jsonl --out projection.json
omega-outreach-foundation migrate-case ...
omega-outreach-foundation schemas-generate generated/schemas
omega-outreach-foundation schemas-audit generated/schemas
omega-outreach-foundation atlas-generate generated/atlas --count 8192
omega-outreach-foundation atlas-audit generated/atlas
omega-outreach-foundation atlas-cardinality
```

## CI

The workflow `Omega Company Outreach Foundation R1.0` runs on Python:

- 3.10;
- 3.11;
- 3.12;
- 3.13.

For each version it performs:

1. compilation;
2. foundation tests;
3. schema generation and audit;
4. Futurpreneur migration;
5. Polytechnique migration;
6. 8 192-scenario generation;
7. scenario audit;
8. second deterministic generation;
9. recursive comparison;
10. theoretical-cardinality report.

Python 3.13 uploads schemas, migrations and atlas shards as a temporary
evidence artifact.

The workflow has `contents: read` only. It cannot send email or alter the
repository.

## OAK boundaries

Foundation A cannot by itself authorize:

- an external send;
- a follow-up;
- a meeting invitation;
- a price;
- a proposal;
- a contract;
- a payment;
- a signature;
- a government filing;
- an incorporation;
- a production deployment.

Those actions require an exact immutable action envelope and the appropriate
human or professional authorization in Ω-LEGAL-PRODUCTION-OS.

## Negative memory M−

The implementation records three immediate engineering lessons:

1. datetime values must enter persistent hashes through canonical
   serialization, not Python's generic `str` conversion;
2. dataclasses with `slots=True` do not expose `__dict__`;
3. migration bundles must serialize structured objects, not their display
   strings.

Each lesson is covered by a dedicated runtime and regression tests.

## Next layer

Foundation B can build on these primitives to implement:

- automated organization ingestion;
- public-source evidence refresh;
- encrypted private contact adapters;
- opportunity discovery;
- claim-evidence compilation;
- message packages;
- exact approval envelopes;
- meeting preparation;
- CRM projections;
- proposal and pilot factories.

It should remain a separate stacked PR so each capability is reviewable and
reversible.
