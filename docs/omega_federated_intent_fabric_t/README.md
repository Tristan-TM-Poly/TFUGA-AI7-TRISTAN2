# Ω-FEDERATED-INTENT-FABRIC-T∞ — R0.1

This branch is intentionally started from current `main` as a bounded integration surface. The implementation files are added only after current-main inspection of the existing `omega_intent_t`, UCIR/BOOK0 contracts, Capability OS and Synergy surfaces.

## Mission

Reuse the existing intent/capability infrastructure and add a typed cross-source envelope so GitHub, Google Drive, Dropbox and model/tool execution surfaces can participate in one proof-carrying intent hypergraph without collapsing source, evidence, authority or action.

## Hard invariants

```text
Source != Evidence
Evidence != Intent
Intent != Authority
Authority != Action
GeneratedIntent != AuthorizedIntent
MissingSourceEvidence != NegativeClaim
```

## R0.1 target

- typed `SourceEnvelope` / `SourceGenome`;
- explicit source visibility, provenance, freshness and authority metadata;
- extraction classes for explicit, derived, verification, residual, counter, negative and regenerative intents;
- cross-source relation types: agree, conflict, partial, unknown, duplicate, implementation-gap, documentation-gap, evidence-gap, reality-gap and harvest-gap;
- deterministic hypergraph/receipt output;
- reuse bridge into existing `omega_intent_t` and Capability OS rather than a parallel planner;
- OAK fail-closed boundaries and tests.

## Current authority

Draft/review branch only. No merge, auto-merge, external publication, Drive mutation, Dropbox mutation, API-key creation, deployment, payment, outreach or irreversible action is authorized by this R0.1 increment.
