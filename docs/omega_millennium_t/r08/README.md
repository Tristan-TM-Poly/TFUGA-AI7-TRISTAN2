# Ω-PROBLEM-ATLAS-T∞ R0.8 — Evidence-Updated Routing

R0.8 routes research effort from append-only evidence events rather than model
confidence or unsupported self-assessment. Its routing score answers only:

> Where should finite research effort be allocated next?

It never answers:

> What is the probability that a mathematical statement is true?

## OAK status

`CERTIFIED_EVIDENCE_ROUTING_FIXTURE_R0_8` certifies deterministic software
materialization and genesis replay for supplied fixtures. It does not certify
mathematical truth, theorem correctness, novelty, publication, prize eligibility
or solution of an open problem.

## Inputs

### Routing cells JSONL

Each cell preserves:

- stable cell and problem identities;
- mathematical front;
- title and method family;
- initial routing score in `[0, 100]`;
- active/inactive state;
- provenance references;
- cryptographic digest.

The initial score is an operational prior for work scheduling. It is not a
Bayesian probability of truth.

### Event bundle

```json
{
  "schema": "omega-problem-routing-events/8",
  "ledger_id": "campaign-ledger-001",
  "events": []
}
```

Events require contiguous sequence numbers, nondecreasing timezone-aware dates,
a known cell, supported event type, evidence reference, observation and SHA-256
source digest.

Users cannot provide:

- routing deltas;
- event categories;
- previous or current hashes;
- truth-probability deltas;
- mathematical-truth claims.

These fields belong to the versioned compiler contract.

## Fixed event rules

Positive routing events include:

- verified source status;
- reproduced known cases;
- valid counterexamples;
- improved bounds;
- discharged assumptions;
- exposed hidden assumptions;
- kernel-checked formal artifacts;
- successful computations;
- accepted independent reviews.

Negative routing events include:

- invalidated source status;
- failed bounds;
- rejected formal artifacts;
- invalid certificates;
- timeouts and divergence;
- duplicated known work;
- challenged or rejected reviews.

A negative delta lowers immediate routing priority but remains permanently useful
through M−. A valid counterexample receives positive research value because it
resolves uncertainty or falsifies a path; it also enters M− so the failed claim
or method cannot be forgotten.

The complete rule table is cryptographically digested into every manifest.
Changing a rule requires a new software revision and creates a different digest.

## Hash-chained ledger

The first event uses a zero genesis hash. Every later event stores the previous
event hash. The current event hash commits to:

- sequence and time;
- cell and event type;
- evidence reference and source digest;
- observation;
- fixed delta and category;
- previous hash;
- explicit absence of truth-probability claims.

Deleting, inserting, reordering or editing an event breaks the chain.

## State reconstruction

For each cell:

```text
routing_score = clamp(initial_score + sum(fixed event deltas), 0, 100)
```

Every state lists each contributing event, evidence reference and delta. The
system does not hide the calculation behind an embedding or opaque model score.

## Diversity-constrained portfolio

Selection proceeds deterministically:

1. group active cells by mathematical front;
2. rank each front by routing score, total delta, problem ID and cell ID;
3. rotate through fronts;
4. enforce a maximum number of selected cells per problem;
5. stop at the finite campaign budget.

The budget and per-problem limit are scheduling controls, not permanent atlas
ceilings.

## Counterfactual explanations

For every cell, R0.8 removes its latest event, reconstructs all states and
reruns portfolio selection. The output records whether the cell would enter,
leave or remain in the portfolio without that event.

This explains why a cell changed priority without claiming that the latest event
changed the mathematical truth of its conjecture.

## M− negative memory

M− is generated directly from versioned event rules. It stores:

- event and chain hashes;
- cell and event identities;
- category and routing delta;
- evidence and source digests;
- immutable status.

Normal routing updates cannot delete these records.

## Compile

```bash
omega-problem-routing compile \
  --cells-jsonl campaigns/cells.jsonl \
  --events-json campaigns/events.json \
  --output-dir generated/routing_r08 \
  --budget 24 \
  --max-per-problem 2
```

Audit:

```bash
omega-problem-routing audit generated/routing_r08
```

## Outputs

```text
routing_cells.jsonl
event_ledger.jsonl
cell_states.jsonl
portfolio.json
counterfactuals.jsonl
mminus_records.jsonl
manifest.json
report.json
```

## Strict audit

The audit reconstructs the complete result from genesis:

- all file, manifest and report digests;
- every cell digest;
- contiguous sequence and hash chain;
- fixed rule delta and category;
- cell states and event explanations;
- diversity-constrained portfolio;
- counterfactual report;
- immutable M− records;
- report counts and final chain hash;
- zero truth-probability, proof and solution claims.

## Next layer

R0.9 should place a fail-closed promotion gate before publication, competition
submission, prize claims, patent decisions or public theorem announcements.
