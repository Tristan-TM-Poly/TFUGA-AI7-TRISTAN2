# Ω-FEDERATED-INTENT-FABRIC-T∞ — R0.2

R0.2 is a stacked, bounded extension of R0.1. It keeps the R0.1 cross-source normalization layer and adds **closure, exact duplicate compression and bounded minimum-unlock selection** without creating a second autonomous planner.

## Mission

```text
GitHub / Drive / Dropbox / model-tool observations
→ SourceEnvelope
→ FederatedIntentReceipt
→ evidenced relations
→ IntentClosureCompiler
   ├─ exact duplicate → EigenIntent
   ├─ conflict/gap → proposed closure intent
   ├─ verification/counter/residual → closure obligations
   └─ obligations → MinimalUnlockSet
→ BOOK0-min next-intent seed
→ existing omega_intent_t / Capability OS
→ separately authorized execution
```

## Hard invariants

```text
Source != Evidence
Evidence != Intent
Intent != Authority
Authority != Action
GeneratedIntent != AuthorizedIntent
MissingSourceEvidence != NegativeClaim
ExactDuplicate != FuzzySemanticEquivalence
EigenCompression != ProvenanceDeletion
MinimalUnlockSet != AutomaticExecutionPlan
GreedyCover != ProvenMinimum
```

## R0.2 additions

- `EigenIntent` is emitted only from an existing exact cross-source `DUPLICATE` relation; no embedding/fuzzy equivalence is claimed;
- compression preserves every member intent, source envelope and evidence reference;
- evidenced conflict/partial/unknown/gap relations compile into deterministic `PROPOSED` closure intents;
- verification, falsification and residual intents become explicit closure obligations;
- relation participation creates multi-obligation coverage, allowing a single proposed intent to unlock more than one evidenced blocker;
- `MinimalUnlockSet` uses exhaustive set-cover enumeration only for bounded frontiers (`<=18` candidates by default);
- larger frontiers use deterministic greedy cover and force `exact_minimality_proven=false`;
- negative intents remain constraints and are never selected as executable candidates;
- `next_intent_seed()` exports a BOOK0-min projection with execution/merge/publication authority hard-false.

## Reuse before creation

R0.2 was designed after inspecting the portfolio's existing closure/intent machinery. In particular, another repository already uses bounded exact enumeration for minimal external-action coverage and explicitly separates production evidence from build evidence. R0.2 reuses that **algorithmic pattern** but does not add a cross-repository runtime dependency or copy private source payloads.

The connected Drive UCIR/BOOK0 material likewise treats intention, evidence, risk, authority, invariants and rollback as distinct typed fields. R0.2 preserves that separation rather than flattening them into a TODO list.

## Connected-source privacy

Read-only connected observations may inform the compiler design, but this public package does not persist raw private Drive text, Dropbox content, API keys, connector credentials, private repository identifiers, Gmail/Calendar payloads or other private source material. Caller-supplied envelopes remain the explicit boundary.

An observed empty connector snapshot is still only evidence about that observation. It is not evidence that the underlying domain contains nothing.

## Current authority

Draft/review branch only. No merge, auto-merge, external publication, Drive mutation, Dropbox mutation, API-key creation, deployment, payment, outreach or irreversible action is authorized by this R0.2 increment.
