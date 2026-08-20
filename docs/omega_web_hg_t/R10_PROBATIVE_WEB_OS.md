# Ω-WEB-HG-T∞ R1.0 — Probative Web Operating System

## Mission

Build an authorized, differential and continuously reviewable evidence twin of
scientific, technical and public Web sources.

The system must answer:

```text
What was observed?
Where did it come from?
What changed?
Which claims are supported or contradicted?
Which verifiable action can be produced next?
```

R1.0 extends R0.4 sharded metadata absorption and R0.5 executable policies into
an intent-to-evidence operating system.

## Canonical pipeline

```text
intent
→ questions and ontology
→ Policy Compiler
→ source and adapter selection
→ adaptive frontier
→ distributed shard fabric
→ authorized observation
→ Evidence Vault
→ differential Web twin
→ Claim–Evidence Graph
→ U² uncertainty
→ contradiction dossiers
→ CVCD compression
→ Rosette reproduction bridge
→ OAK report
→ GitHub or product action
```

## R0.5 — Ω-POLICY-COMPILER-T

Status: active implementation.

Purpose:

- compile represented policy evidence into deterministic technical gates;
- fail closed on ambiguity, expiration and review debt;
- enforce routes, rates, identity, environment, fields and retention;
- preserve every decision in an append-only registry.

Critical boundary:

```text
POLICY_DOCUMENT != EXECUTABLE_PERMISSION
```

## R0.6 — Ω-ADAPTER-SDK-T

Create declarative adapter families:

```text
REST
GraphQL
OAI-PMH
SPARQL
Sitemap
RSS/Atom
CKAN
DCAT
OpenSearch
Wikimedia
public object store
Git repository
authorized static HTML
official dataset dump
```

Every adapter must satisfy contract tests for pagination, identifiers, exact
resume, deterministic normalization, partial responses, rate limits and absence
of forbidden persistence.

## R0.7 — Ω-WEB-DIFF-T

Represent each object as a version lineage rather than repeated copies.

```text
object v1
→ canonical digest
→ object v2
→ structural / metadata / semantic / license diff
→ invalidation or downstream action
```

Change classes:

```text
appearance
removal
correction
date update
license change
title change
identifier change
relation change
claim change
availability change
```

## R0.8 — Ω-CLAIM-EVIDENCE-GRAPH-T

Link every normalized claim to exact provenance:

```text
claim
→ source object
→ version
→ locator
→ extraction method
→ confidence components
→ supporting evidence
→ counterevidence
→ OAK status
```

Hyperrelations:

```text
supports
contradicts
qualifies
depends_on
retracts
updates
replicates
fails_to_replicate
derived_from
same_entity_as
likely_duplicate_of
```

## R0.9 — Ω-U²-WEB-T + Ω-CONTRADICTION-ENGINE-T

Track distinct uncertainties:

```text
U0 observed content
U1 extraction uncertainty
U2 source uncertainty
U3 interpretation uncertainty
U4 decision fragility
U5 calibration history
```

For important claims, generate searches for confirmation, contradiction,
historical versions, replication, retraction and scope limitations.

Allowed dossier outcomes:

```text
confirmed_within_scope
contested
superseded
retracted
unsupported
not_comparable
insufficient_evidence
```

## R1.0 — Ω-CAMPAIGN-GENERATOR-T∞

Compile a research intention into an executable campaign:

```bash
omega-web-hg intent \
  "Build a probative atlas of thermoelectric materials"
```

Expected generated objects:

```text
questions
ontology
candidate sources
policy requirements
adapter requirements
queries
shards
finite runtime budgets
schemas
OAK gates
expected artifacts
stop and escalation criteria
```

## Ω-ADAPTIVE-FRONTIER-T

Allocate finite resources without a permanent architectural cap.

Possible priority components:

```text
expected information value
freshness
source authority
change probability
cost per object
error rate
semantic novelty
duplication density
legal risk
relevance to active Tristan projects
```

Priority scores are scheduling instruments, not truth scores.

## Ω-SHARD-FABRIC-T∞

Generalize four source shards into a distributed fabric partitionable by:

```text
source
domain
language
jurisdiction
time
content type
license
priority
cost
data footprint
```

Introduce governed work stealing with leases, heartbeats, expiration,
checkpoints and exclusive source ownership. No active lease may duplicate a
source request owned by another worker.

## Ω-EVIDENCE-VAULT-T

Separate storage by policy and sensitivity.

### Level 0 — public GitHub

```text
code
schemas
tests
manifests
hashes
minimized reports
synthetic fixtures
documentation
```

### Level 1 — normalized metadata

```text
JSONL or Parquet records
identifiers
provenance
licenses
relations
change indexes
```

### Level 2 — private authorized evidence vault

```text
authorized captures
WARC when permitted
compressed responses
version evidence
complete operational logs
large artifacts
```

### Level 3 — restricted data

```text
encryption
least privilege
bounded retention
access ledger
verifiable deletion
```

Every stored object receives a `StorageDecisionRecord`.

## Ω-CVCD-WEB-COMPRESSOR-T

Produce two coupled representations:

```text
LOG = compact, searchable invariant representation
EXP = complete evidence graph allowing decompression to provenance
```

Boundary:

```text
COMPRESSION_WITHOUT_PROVENANCE = INFORMATION_LOSS
```

## Ω-ROSETTE-WEB-BRIDGE-T

Transform authorized evidence into reproducible research assets:

```text
source
→ structured document
→ Claim–Evidence Graph
→ equations and tables
→ hypotheses
→ implementation candidate
→ tests
→ benchmark
→ OAK report
→ GitHub issue or PR
```

A source may generate a reproduction scaffold or hypothesis. It does not
automatically generate truth.

## Ω-SOURCE-SELF-HEAL-T

Convert adapter failures into M-minus assets:

```text
failure
→ compare last valid structure
→ classify drift
→ minimize fixture
→ propose patch
→ run contract tests
→ draft PR
→ human approval
```

No autonomous production repair without tests and OAK approval.

## Ω-QUALITY-MARKET-T

Maintain historical source and adapter measures:

| Dimension | Measure |
|---|---|
| Availability | successful request rate |
| Stability | schema changes |
| Novelty | new objects per request |
| Duplication | already known objects |
| Cost | seconds and bytes per object |
| Quality | valid normalized fields |
| Provenance | complete identifiers and locators |
| License | clarity and record coverage |
| M-minus | errors per campaign |
| Value | usable evidence produced |

The planner uses these measures for budget allocation, not epistemic certainty.

## Ω-CI-IMPACT-ROUTER-T

Resolve repository-wide workflow fan-out.

```text
git diff
→ file/module/workflow impact graph
→ required smoke gates
→ selected domain workflows
→ optional heavy campaigns
→ selection manifest
```

Required properties:

- no unrelated domain matrix for local changes;
- no required check silently removed;
- concurrency and cancellation by branch and domain;
- explicit reason for every selected or skipped workflow;
- measurable queue-time reduction;
- rollback path.

Tracked by issue #337.

## Products

Potential evidence-backed products:

```text
OAK Web Evidence Audit
Scientific Evidence Graph API
Regulatory Change Monitor
Research Landscape Compiler
Documentation Truth Maintenance
```

A product is real only after external use, payment, repeatability, margin and
retention evidence.

## OAK dashboard

| Axis | Current | Next proof |
|---|---|---|
| Truth | observed metadata, not independently verified | claim/evidence links |
| Code | R0.4 sharding + R0.5 policy gates | adapter integration |
| Test | focused deterministic suites | cross-adapter contracts |
| Product | internal infrastructure | first evidence audit pilot |
| IP | architecture documented | IPGate before broad disclosure |
| GitHub | versioned and reviewed | impact-routed CI |
| Revenue | unvalidated | first paid audit |
| Risk | policy drift and CI fan-out | drift alerts and router |
| Next action | R0.5 implementation | gate one R0.4 adapter end-to-end |

## Final principle

Maximum does not mean only more requests, pages, modules or lines.

```text
more coverage
more provenance
more resumability
more contradiction seeking
more change detection
more executable policy
more reproducible evidence
more external value
less noise
less duplication
less overconfidence
```

The destination is not a giant crawler. It is a probative nervous system for
authorized Web information.
