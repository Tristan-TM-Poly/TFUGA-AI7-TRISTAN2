# Ω-PROBLEM-ATLAS-T∞ R0.11

## Competition and Prize Opportunity Ledger

R0.11 converts competitions, challenges, hackathons, benchmark campaigns and
prize opportunities into immutable, auditable cycle records.

```text
official source receipts
  -> immutable competition cycle
  -> derived state at a fixed as_of instant
  -> rule-bound eligibility and submission plans
  -> recommendation only when active + fresh + eligible
  -> externally produced submission/result receipts
  -> licensed archived benchmark
```

## Core boundaries

```text
recommendation != registration
plan           != submission
leaderboard    != final result
winner record  != guaranteed payment
competition task != open mathematical problem
```

R0.11 never registers, submits, pays, claims a prize or changes a mathematical
problem's status.

Every generated report fixes:

```json
{
  "registration_performed": false,
  "submission_performed": false,
  "payment_performed": false,
  "winner_or_prize_guaranteed": false,
  "open_problem_status_inherited": false,
  "proof_claimed": false,
  "solution_claimed": false
}
```

## Commands

```bash
omega-competition-ledger compile \
  --bundle-json competitions/cycles.json \
  --output-dir generated/competition_ledger_r11

omega-competition-ledger audit generated/competition_ledger_r11

omega-competition-ledger recommend generated/competition_ledger_r11
```

The CLI has no `register`, `submit`, `pay`, `claim`, `accept-prize` or
`publish-result` command.

## Immutable cycles

A recurring competition is represented by a stable `competition_id` and a new
`cycle_id` for every edition.

Examples:

```text
competition.fixture / 2025
competition.fixture / 2026
competition.fixture / 2027
```

The earliest known cycle has no predecessor. Every later cycle must preserve a
predecessor link to an older cycle. The compiler detects:

- missing predecessors;
- self-reference;
- chronology reversal;
- loops;
- duplicate `(competition_id, cycle_id)` identities.

Old cycles are never mutated into new cycles.

## Cycle states

R0.11 derives state from official deadlines at the bundle's exact `as_of`
instant:

- `announced` — announced but not yet open;
- `active` — registration, task or submission window is active;
- `judging` — submissions are closed and judging is in progress;
- `closed` — judging is complete but archival date has not arrived;
- `archived` — archival date has arrived.

The state is derived, not user-authored.

## Timezones and DST

Every official deadline must include an explicit UTC offset. Every cycle also
names an IANA timezone such as `America/Montreal`.

Generated deadline views preserve:

- source datetime;
- UTC datetime;
- America/Montréal datetime;
- requested recommendation timezone.

The timezone conversion uses the standard timezone database and therefore
handles daylight-saving changes. An offset-free datetime fails closed.

## Source receipts

Official sources are typed as:

- rules;
- announcements;
- task pages;
- results;
- FAQs.

Each source preserves:

- stable source ID;
- source kind;
- official HTTPS URL;
- SHA-256 digest;
- observation timestamp;
- exact source location;
- organizer domain;
- metadata.

Official URLs must use HTTPS, contain no embedded user credentials and resolve
to the declared organizer domain or one of its subdomains.

## Freshness

The bundle sets a positive `freshness_seconds` interval. For a cycle to be
recommended, R0.11 requires a matching official-rules receipt that:

- has the exact cycle rule URL;
- comes from the declared organizer domain;
- was observed no later than `as_of`;
- is no older than the configured freshness interval.

A compiled recommendation is only valid relative to the compiled `as_of`.
`recommend` explicitly states that a new official verification is required
after that instant.

## Rule digest

Each cycle receives a deterministic digest over its structured rules:

- competition and cycle identity;
- organizer and official rule URL;
- version and timezone;
- deadlines;
- eligibility;
- licenses;
- prize terms;
- judging rules;
- tasks;
- referenced source IDs;
- predecessor.

Local plans and external submission receipts bind this digest. Any structured
rule change invalidates stale plans and receipts.

A source-byte change that does not change the structured rule model remains
visible through the official source digest and verification receipt. It should
be reviewed and the structured rules updated whenever meaning changes.

## Eligibility

Eligibility rules include:

- registration requirement;
- individual/team mode;
- minimum and maximum team sizes;
- minimum and maximum age;
- allowed and excluded residencies;
- affiliation requirements;
- identity-verification requirement;
- official terms references.

An eligibility plan records the participant assumptions used for evaluation.
A recommendation requires at least one valid reviewed or authorized eligibility
plan. Draft and withdrawn plans are not actionable.

R0.11 evaluates declared facts; it does not verify a person's legal identity,
residency, tax status or institutional affiliation.

## Licensing and disclosure

Cycle records preserve:

- data license;
- code license;
- model license;
- external-data policy;
- open-source obligation;
- disclosure obligation;
- publication obligation;
- official license references.

This information prevents a competition artifact from being published or
reused without preserving the applicable rules. It is not legal advice.

## Prize terms

Prize data uses integer minor units plus a three-letter currency code. It also
preserves payment conditions, tax notes and official references.

A recorded `winner` result requires an official-results source. Even then,
R0.11 reports:

```text
prize_payment_guaranteed = false
```

Eligibility re-verification, tax documents, contracts or organizer approval may
still be required.

## Judging and leakage

Judging rules preserve:

- metric;
- maximize/minimize/ranked/judged direction;
- public leaderboard presence;
- private leaderboard presence;
- leaderboard-leakage risk;
- reproducibility requirements;
- official references.

A public score is not assumed to equal the private or final result. Repeated
adaptation to a public leaderboard can overfit the visible split and should be
recorded in the experiment's negative memory.

## Plans

R0.11 supports two local plan types:

- `eligibility`;
- `submission`.

Plan status is one of:

- `draft`;
- `reviewed`;
- `authorized`;
- `withdrawn`.

An authorized plan must preserve an authorization reference. Authorization
still does not cause any external action.

## External submission receipts

A submission appears in the ledger only after another human-controlled system
provides an external receipt reference. The ledger verifies:

- cycle identity;
- rule digest;
- artifact digest;
- submission window;
- receipt timestamp no later than `as_of`;
- URI-shaped external receipt reference;
- official result references for accepted/rejected/scored/winner outcomes.

The ledger records external evidence. It does not create that evidence.

## Recommendations

A cycle is recommended only when:

- derived state is `active`;
- deadlines are internally ordered;
- cycle history is valid;
- all referenced sources exist;
- official rule URL and domain are valid;
- official rules are fresh at `as_of`;
- at least one eligibility plan is valid;
- the plan's rule digest is current.

Recommendations are sorted by submission deadline and stable cycle identity.
They preserve Montréal and UTC deadline views.

## Archived training benchmarks

An archived cycle task becomes a training benchmark only when:

- cycle state is `archived`;
- task artifact digest is present;
- archive license is known and usable;
- task source references are preserved.

Every archive row fixes:

```json
{
  "training_benchmark_only_under_license": true,
  "open_problem_status_inherited": false
}
```

A past competition task does not become an open theorem merely because it is
hard, unsolved by participants or scientifically interesting.

## Materialized output

R0.11 writes:

- `request.json`;
- `sources.jsonl`;
- `cycles.jsonl`;
- `plans.jsonl`;
- `submission_receipts.jsonl`;
- `recommendations.json`;
- `archive_benchmarks.jsonl`;
- `manifest.json`;
- `report.json`.

The request contains only supplied immutable facts. Derived rule digests,
states, blockers and recommendation decisions appear only in derived outputs.

## Audit

The audit:

1. reloads and validates the original bundle;
2. reconstructs cycle state at `as_of`;
3. rechecks source freshness, HTTPS and organizer domains;
4. rechecks deadline order and recurring-cycle ancestry;
5. re-evaluates plans and submission receipts;
6. reconstructs recommendations and archives;
7. reconstructs every logical artifact digest;
8. reconstructs manifest and report;
9. rejects any registration, submission, payment, proof, solution or
   open-problem semantic flag.

Stored recommendations are never trusted.

## OAK status

`CERTIFIED_COMPETITION_LEDGER_FIXTURE_R0_11` may certify deterministic cycle
state, source verification, recommendation and replay behavior for supplied
fixtures after CI succeeds.

It does not certify:

- current real-world competition status after the compiled `as_of`;
- legal eligibility;
- successful registration;
- successful submission;
- leaderboard or final ranking;
- prize payment;
- tax treatment;
- proof or solution of any mathematical problem.
