# Ω-GITHUB-REVENUE-T∞ / OAKSponsorOS-T R0.2 MAX

**Status:** executable, local, proof-carrying research and commercial-validation prototype  
**Parent:** R0.1 typed assets, offers, Sponsors tiers, experiments, allocation, JSONL frontier, and hash-chained ledger  
**Primary implementation:** `omega_github_revenue_t/`  
**Primary validation:** `tests/test_omega_github_revenue_r02.py`

## 0. Executive statement

R0.2 turns the R0.1 economic-routing kernel into a durable validation fabric.
It can audit an explicitly authorized local repository, compile privacy-minimized
findings, emit content-addressed evidence receipts, run checkpointed finite campaigns
through SQLite, analyze observed conversion funnels, reconcile minimized provider
events, calculate bounded delivery economics, compile a Sponsor profile, and allocate
resources across dependency-aware Pareto candidates.

R0.2 does not send messages, publish profiles, mutate repositories, access GitHub or
Stripe APIs, execute payments, inspect inaccessible systems, file taxes, create legal
contracts, or claim product-market fit.

## 1. Core distinctions

```text
repository volume != scientific proof
Sponsors approval != sponsor
sponsor != customer
customer conversation != purchase
provider event != reconciled accounting event
payment != profit
contribution margin != net income
synthetic capacity record != market evidence
static repository audit != security certification
Merkle root != legal notarization
```

These distinctions are represented in code and tests rather than left as prose only.

## 2. R0.2 engines

### 2.1 Authorization Court

`authorization.py` defines an explicit, expiring, operation-scoped authorization
receipt. OAKGate refuses to audit when authorization is missing, false, expired, in
the future, or bound to another local repository.

Authorized operations are enumerated:

- read metadata;
- read text;
- count lines;
- hash files;
- scan risk patterns;
- generate reports.

An authorization receipt is not a legal contract or proof that the grantor has every
possible right. It is a machine-checkable minimum gate that prevents silent
assumptions of permission.

### 2.2 Privacy and Secret Gate

`privacy.py` extends the R0.1 forbidden-key gate with value-level pattern detection for:

- GitHub personal-access-token-like strings;
- OpenAI-like secret keys;
- AWS access-key identifiers;
- private-key headers;
- Stripe secret-key-like strings.

Reports contain categories and one-way fingerprints, not detected secret values.
Pattern matching can produce false positives. A match is a review or revocation
signal, not proof of compromise.

### 2.3 OAKGate Repository Audit

`repository_audit.py` performs a deterministic static audit over an authorized local
repository. It measures:

- file and byte counts;
- text files and lines scanned;
- code files;
- test files;
- GitHub Actions workflows;
- documentation files;
- recognizable license presence;
- GitHub Sponsors funding configuration;
- secret-pattern fingerprints;
- explicit per-file scan-budget exceptions.

It emits typed findings for missing README, license, tests, CI, or SECURITY policy,
large unscanned files, encoding exceptions, and privacy findings.

The quality score is a routing heuristic. It is not a universal repository-quality
metric and should not be compared across unrelated domains without calibration.

### 2.4 Evidence Manifest and Merkle Receipts

`transparency.py` provides:

- canonical JSON hashing;
- streaming file hashing;
- deterministic manifests;
- Merkle roots;
- inclusion proofs;
- inclusion verification.

A Merkle root establishes internal content consistency for a known set of hashes. It
does not prove authorship, time of creation, legal ownership, truth, or external
publication.

### 2.5 Durable Campaign Store

`store.py` uses SQLite with WAL and explicit schemas for:

- artifacts and assessments;
- campaign events;
- checkpoints;
- minimized provider events.

Payloads pass both forbidden-key and secret-value gates before persistence.
Artifacts are idempotent by stable identifier and payload hash. Batch upserts avoid
one-connection-per-object scaling collapse.

The database belongs in a private or generated local path when it contains real
commercial observations. It must not contain banking coordinates, credentials,
addresses, tax identifiers, confidential client content, or full provider payloads.

### 2.6 Adaptive Finite Campaigns

`campaign.py` has no permanent total-artifact ceiling. Each run remains finite and
bounded by its input, available storage, compute, and optional `stop_after` budget.

The campaign loop provides:

- lazy source consumption;
- deterministic artifact parsing;
- evidence scoring;
- SQLite batch upserts;
- duplicate detection;
- quarantine events;
- checkpoint and resume;
- adaptive batch sizing;
- content-root receipts;
- deterministic synthetic capacity fixtures.

`synthetic_artifacts()` exists only to validate capacity and invariants. Synthetic
objects cannot be counted as users, sponsors, customers, revenue, scientific results,
or market traction.

### 2.7 Bayesian Funnel Evidence

`conversion.py` models observed counts through stages such as:

```text
visitor -> Sponsors page -> click -> sponsorship
inquiry -> qualified inquiry -> paid service -> repeat paid service
```

Each stage emits an observed rate when defined and a Beta posterior with an
approximate interval. Small samples remain uncertain. The module recommends the next
experiment based on the earliest weak or unobserved stage.

The Beta model is a simple decision aid. It does not automatically correct selection
bias, seasonality, attribution errors, bot traffic, hidden confounders, or changing
audiences.

### 2.8 Provider Reconciliation

`reconciliation.py` compares privacy-minimized internal and provider event exports by:

- source;
- event identifier;
- gross amount in minor units;
- fee in minor units;
- currency;
- status.

It detects missing records, duplicates, and mismatches, then computes matched net
amounts by currency. It does not convert currencies, determine tax treatment, replace
bank statements, or certify accounting records.

### 2.9 Delivery Economics

`pricing.py` calculates a bounded price envelope from:

- delivery time;
- review time;
- support time;
- compute cost;
- tooling cost;
- contingency;
- hourly cost basis;
- target contribution margin.

The result is a hypothesis envelope, not a market price. Willingness to pay must be
observed through consented offers and transactions.

### 2.10 Sponsor Profile Compiler

`profile.py` compiles a reviewable local bundle containing:

- mission;
- demonstrated projects;
- evidence;
- next falsifiable actions;
- public commitments;
- non-claims;
- sustainable Sponsor tiers;
- profile content hash.

It does not publish or modify the live GitHub Sponsors profile. Publication remains a
separate human-controlled action because it changes public commitments.

### 2.11 Portfolio and Dependency Engine

`portfolio.py` provides:

- multi-objective dominance;
- Pareto-front extraction;
- dependency-cycle detection;
- topological dependency ordering;
- dependency-aware finite-budget allocation.

The value score is an internal routing heuristic, not a company valuation or promise
of financial return.

### 2.12 Revenue Atlas

`atlas.py` models the path:

```text
corpus
-> revenue-capable artifact
-> IP/disclosure gate
-> proof
-> demonstration
-> public profile and bounded offer
-> consented pilot
-> possible observed transaction
-> provider reconciliation
-> M-minus memory
-> evidence-weighted allocation
```

Graph connectivity is not causal or scientific proof. Each edge is an architectural
relationship that still requires its own evidence.

## 3. OAKGate bundle

A successful local OAKGate run creates:

```text
audit-report.json
audit-report.md
authorization-receipt.json
evidence-manifest.json
run-receipt.json
```

The bundle contains no network response, bank information, payment credential, or
claim of external approval.

## 4. CLI

### 4.1 Authorized audit

```bash
omega-github-revenue-r02 oakgate-audit . \
  --output generated/oakgate-audit \
  --authorization-id AUTH-LOCAL-001 \
  --granted-by Tristan-TM-Poly \
  --granted-at 2026-08-03T02:00:00Z \
  --i-am-authorized
```

Omitting `--i-am-authorized` fails closed.

### 4.2 Finite capacity campaign

```bash
omega-github-revenue-r02 campaign \
  --count 1000000 \
  --database generated/revenue-campaign.sqlite \
  --campaign-id capacity-1m \
  --checkpoint-every 10000
```

The command generates deterministic synthetic fixtures lazily. A million-item run is
a capacity experiment, not a million useful inventions or commercial assets.

### 4.3 Atlas

```bash
omega-github-revenue-r02 atlas > generated/revenue-atlas.json
```

### 4.4 Profile bundle

```bash
omega-github-revenue-r02 profile \
  --output generated/sponsor-profile
```

### 4.5 Funnel analysis

```bash
omega-github-revenue-r02 funnel examples/data/revenue_funnel_snapshot.json
```

### 4.6 Provider reconciliation

```bash
omega-github-revenue-r02 reconcile \
  examples/data/revenue_events_internal.json \
  examples/data/revenue_events_provider.json
```

## 5. Capacity philosophy

R0.2 rejects a fixed global `MAX_ADDITIONS`. It also rejects the opposite error of
pretending that limits do not exist.

```text
no arbitrary permanent object ceiling
+ explicit finite run budgets
+ adaptive batches
+ checkpoints
+ durable storage
+ deduplication
+ quarantine
+ evidence gates
+ IP/privacy gates
+ human sovereignty for public and irreversible actions
```

The maximum useful scale is discovered empirically by resource curves and failure
memory, not declared in advance.

## 6. First external validation protocol

The first legitimate external experiment remains one audit of a repository that is:

- owned by Tristan; or
- public and audited within its license and terms; or
- explicitly authorized by its owner.

Before delivery, record:

- target repository and scope;
- authorization identifier;
- confidentiality classification;
- expected delivery time;
- expected outputs;
- exclusions;
- price hypothesis, if any;
- success and stop criteria.

After delivery, measure:

- elapsed delivery time;
- actionable findings accepted by the owner;
- false positives;
- missing important findings;
- user-rated utility;
- privacy incidents;
- willingness to repeat;
- willingness to pay;
- actual payment only when observed and reconciled.

One pilot is evidence about one delivery, not product-market fit.

## 7. Negative memory M-minus

R0.2 must preserve these failure classes:

- unauthorized audit target;
- secret value entering a report or database;
- synthetic capacity mistaken for market evidence;
- generated volume mistaken for value;
- resume checkpoint skipping or duplicating source records;
- adaptive batch instability;
- SQLite write amplification;
- content root computed over an incomplete set;
- provider event mismatch ignored;
- zero-denominator conversion presented as zero conversion;
- small sample presented as certainty;
- price floor presented as willingness to pay;
- contribution margin presented as profit;
- Sponsor tier whose delivery cost exceeds its support;
- dependency blocked asset funded before its prerequisite;
- public profile published before IP/privacy review;
- repository quality score presented as universal truth;
- static audit presented as security certification.

## 8. CI gates

The R0.2 workflow validates on Python 3.10 and 3.13:

- all R0.1 tests;
- all R0.2 tests;
- fail-closed authorization;
- secret-value redaction and rejection;
- deterministic Merkle proofs;
- authorized repository-audit bundles;
- SQLite idempotency;
- a 50,001-artifact frontier and resume;
- finite stop budgets;
- funnel invariants;
- provider reconciliation;
- pricing non-claims;
- dependency-aware allocation;
- profile compilation;
- atlas integrity.

A dedicated capacity job performs a 100,000-artifact campaign and verifies the stored
count. Larger runs remain opt-in because CI time and storage are real constraints.

## 9. Non-claims

R0.2 does not claim:

- a sponsor has paid;
- a customer exists;
- product-market fit;
- recurring revenue;
- profitability;
- tax compliance;
- legal compliance certification;
- accounting certification;
- bank reconciliation;
- security certification;
- universal repository quality;
- scientific validation of TFUGA;
- autonomous public communication;
- autonomous contracting;
- autonomous payment or transfer;
- authority over third-party repositories;
- legal timestamping or notarization from Merkle receipts.

## 10. Promotion gate to R0.3

R0.3 should not be promoted solely because more modules exist. Promotion requires at
least one of:

1. a consented external OAKGate pilot with structured feedback;
2. a reproduced audit result on an independent authorized repository;
3. a real Sponsor transaction reconciled from provider data;
4. a bounded paid service with measured delivery economics;
5. an observed failure that materially improves M-minus and the implementation.

The next version must be more observed, not merely larger.
