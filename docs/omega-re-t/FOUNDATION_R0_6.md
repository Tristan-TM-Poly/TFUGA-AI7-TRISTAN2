# Ω-RE-T∞ R0.6 — Open-World SMC, Durable Campaigns and Cross-Run Evidence

## Status

`SOFTWARE_RESEARCH_ARCHITECTURE / SYNTHETIC_OWNED_OR_AUTHORIZED_SYSTEMS_ONLY`

R0.6 extends the validated R0.1–R0.5 stack with eight proof surfaces that were previously only listed as future work:

1. sequential Monte Carlo over declared and novelty model classes;
2. nonlinear experiment design from ensemble disagreement under authorization, reversibility, cost and risk gates;
3. durable SQLite leases with transactional acquisition, heartbeat, expiry, retry and exactly-once accepted result binding;
4. deterministic Byzantine-worker simulations with payload binding, epochs, revocation, identity-group diversity, quorum conflicts and equivocation removal;
5. cross-run calibration chains with trend classification and divergence localization;
6. content-addressed experiment specifications and immutable observation provenance;
7. optional Ed25519 integration that fails closed when the audited dependency is absent;
8. append-only Merkle transparency logs with inclusion proofs and checkpoint chaining.

The modules reconstruct behavioral hypothesis spaces. They do not claim unique access to inaccessible internals, real Byzantine fault tolerance, physical validation, legal notarization or autonomous external execution.

## Open-world SMC

A particle contains a declared model class, parameter, posterior weight and provenance. Observations update weights through explicit likelihoods. Systematic resampling is deterministic under a seed. Large normalized residuals may inject novelty particles with bounded mass.

A novelty posterior is not a discovered mechanism. It means the declared classes explain the observation poorly enough to justify generating and testing additional candidates.

## Nonlinear experiment design

Candidate experiments are scored using weighted predictive variance, novelty, cost and risk. Before scoring can authorize execution, each candidate must pass:

```text
authorized
and reversible
and cost <= current budget
and risk <= current risk ceiling
```

The selected experiment maximizes expected software utility only. Real interventions require domain-specific safety, ethics, legal authority, calibration and human approval.

## Durable SQLite leases

The lease queue stores work items and events transactionally. Expired leases return to `pending`; stale workers cannot commit. Repeating an identical accepted result is idempotent, while a divergent duplicate is recorded as equivocation and rejected.

```text
at-least-once execution
!=
exactly-once execution

one accepted digest per item
=
exactly-once accepted-result binding
```

SQLite durability on one filesystem is not distributed consensus.

## Byzantine simulations

The simulator binds every vote to item, payload digest, epoch, worker and identity group. Revoked, stale, mismatched and equivocating workers are excluded. A result is accepted only when exactly one digest satisfies both worker and independent-group thresholds.

These deterministic fixtures do not establish tolerance under real Sybil attacks, clock skew, network partitions, adaptive adversaries or compromised identity infrastructure.

## Calibration chains

Every calibration run binds dataset digest, model digest, software case count and metrics. Receipts form an append-only SHA-256 chain and classify each transition as baseline, improved, degraded, stable or mixed. Two chains can be compared to locate their first divergence.

Hash continuity proves byte-level consistency, not truth, independence or scientific validity.

## Experiment registry

An experiment identifier becomes permanently bound to a content-addressed specification containing controls, observable, authorization scope, reversibility, maximum risk and cost. Observations bind uncertainty, instrument digest, sequence, timestamp label and source.

## Transparency log

Software evidence entries are leaf-hashed with domain separation, aggregated into a Merkle root and anchored in chained checkpoints. Inclusion proofs allow a verifier to confirm that a specific receipt belonged to a declared tree state without receiving every leaf. Duplicate-last tree balancing is deterministic and tested for odd tree sizes.

The log proves inclusion and checkpoint consistency only. It does not prove that the underlying evidence is true, independent or complete.

## Optional Ed25519

The adapter uses the external `cryptography` package when available. It:

- refuses silent fallback to a homemade signature;
- refuses key generation without `allow_generation=True`;
- validates raw key lengths;
- binds the message SHA-256 and public-key identifier;
- distinguishes cryptographic integrity from truth, authority and notarization.

The standard R0.6 CI does not require the optional dependency. The absence of the backend must fail closed for signing operations.

## CLI

```bash
omega-re-r06 smc
omega-re-r06 design
omega-re-r06 leases
omega-re-r06 byzantine
omega-re-r06 calibration
omega-re-r06 registry
omega-re-r06 campaign
omega-re-r06 transparency
omega-re-r06 all --output /tmp/omega-re-r06.json
```

## OAK boundaries

- synthetic, owned, openly specified or expressly authorized systems only;
- posterior concentration is conditional on proposal classes;
- novelty is a routing signal, not discovery;
- expected information utility is not authorization;
- SQLite is not consensus;
- quorum fixtures are not Byzantine certification;
- Ed25519 integrity is not truth or legal notarization;
- software calibration is not scientific validation;
- finite executions remain governed by explicit resource envelopes even though `permanent_total_cap = null`.

## Negative memory M−

- closed-class certainty hidden behind posterior normalization;
- novelty particles promoted as discoveries;
- dangerous experiments selected for high information gain;
- stale workers committing after expiry;
- identical worker identities counted as independent votes;
- conflicting quorums silently tie-broken;
- calibration hashes confused with replication;
- Merkle inclusion confused with evidentiary truth or completeness;
- optional cryptography silently downgraded to an unaudited implementation;
- durable local state confused with distributed fault tolerance.

## R0.7 frontier

R0.7 should add tempered SMC and reversible-jump proposals, Gaussian-process or ensemble surrogate design, SQLite migration and recovery tests, process-isolated worker sandboxes, Sybil-resistance assumptions, external calibration datasets, signed transparency logs and reproducible cross-machine evidence bundles.
