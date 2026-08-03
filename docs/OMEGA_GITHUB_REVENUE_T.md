# Ω-GITHUB-REVENUE-T∞ / OAKSponsorOS-T

**Version:** R0.1  
**Status:** executable research and governance prototype  
**Scope:** GitHub assets, Sponsors readiness, service-led productization, evidence, IP, privacy, and revenue bookkeeping interfaces.

## 1. Mother statement

Every public theory should be able to become a bounded claim; every bounded claim a reproducible artifact; every artifact a demonstrated utility; and every demonstrated utility a legitimate opportunity for sponsorship, service, licensing, or product revenue.

This system does **not** claim that code volume, stars, visibility, sponsorship approval, or a published repository constitutes revenue. Revenue exists only when a real transaction is observed and recorded.

## 2. Core distinction

```text
idea != proof
proof != product
product != customer
customer != payment
payment != profit
GitHub Sponsors approval != sponsorship received
```

The system keeps these states separate and traceable.

## 3. Value tensor

For an artifact `a`, OAKSponsorOS-T computes a bounded prioritization score from:

- proof quality;
- concrete utility;
- reuse potential;
- discoverability;
- trust and reproducibility;
- conversion path clarity;
- noise and duplication;
- maintenance burden;
- IP/legal exposure;
- security and privacy risk.

The score is a routing heuristic, never a truth probability, company valuation, or income forecast.

## 4. Revenue-capable artifact

A revenue-capable artifact carries:

1. a stable identifier and title;
2. a bounded problem statement;
3. an actor or user class;
4. evidence and reproducibility status;
5. OAK maturity;
6. disclosure/IP classification;
7. maintenance cost;
8. one or more revenue paths;
9. risks and limitations;
10. a next falsifiable action.

## 5. Disclosure classes

- `OPEN_PUBLIC`: safe and intended for public release.
- `PUBLIC_AFTER_REVIEW`: public only after explicit OAK/IP/privacy review.
- `PATENT_CANDIDATE`: no public disclosure until IP review.
- `TRADE_SECRET`: private operational knowledge.
- `PRIVATE_CLIENT`: contract- or client-bound information.
- `RESTRICTED_SAFETY`: withheld because misuse or safety risk dominates.
- `ARCHIVE_ONLY`: retained but not promoted.

The gate fails closed. Unknown or incomplete classifications are not public.

## 6. Revenue paths

- sponsorship;
- fixed-scope service;
- recurring service;
- software product;
- GitHub App or Action;
- API;
- license;
- training or documentation;
- research contract.

A sponsorship tier must not silently become an unlimited consulting obligation.

## 7. Sixteen engines

1. Asset Discovery Engine
2. IPGate
3. Proof Compiler
4. Demonstration Forge
5. README Conversion Engine
6. Sponsor Value Engine
7. Tier Compiler
8. Public Impact Ledger
9. Offer Compiler
10. Customer Discovery Engine
11. Sponsor Relationship Graph
12. Revenue Ledger
13. Maintenance Cost Engine
14. Experiment Engine
15. M-minus Revenue Memory
16. Capital Allocation Engine

R0.1 implements the shared contracts, scoring, fail-closed disclosure gate, offer compilation, tier sustainability checks, experiment decisions, capital allocation, streaming frontier evaluation, and privacy-safe append-only ledgers.

## 8. Unbounded-frontier rule

The implementation has no permanent `MAX_ADDITIONS` or fixed total-candidate ceiling. It processes finite iterables and JSONL streams lazily.

```text
candidate generation: bounded by available compute/storage
validation: bounded by evidence budget
promotion: bounded by proof and OAK gates
publication: bounded by IP, privacy, safety, and law
maintenance: bounded by real human and financial capacity
```

Removing an arbitrary item count never removes physical, provider, quality, legal, or safety constraints.

## 9. Banking and private financial data

No bank account number, transit number, institution number, void cheque, tax identifier, home address, Stripe secret, or payment credential belongs in this repository.

Only privacy-minimized accounting events may be recorded, for example:

```json
{
  "event_id": "rev-2026-0001",
  "source": "github_sponsors",
  "gross_minor": 500,
  "currency": "USD",
  "fee_minor": 0,
  "occurred_at": "2026-08-02T00:00:00Z"
}
```

Private banking configuration remains inside the authorized GitHub/Stripe/financial-provider interface.

## 10. OAK promotion ladder

- `S`: speculative
- `E`: exploratory
- `X`: crystallizable
- `D`: demonstrated
- `C`: canonical
- `A`: archived

A public paid offer should normally require at least `D`, a reproducible demonstration, explicit limitations, and a sustainable delivery model.

## 11. Initial economic experiment

The preferred first experiment is **OAKGate Repository Audit**.

Input:

- one authorized GitHub repository;
- declared scope and confidentiality;
- no credentials or inaccessible systems.

Output:

- reproducibility and test inventory;
- documentation and architecture gaps;
- risk and maintenance map;
- prioritized issues;
- evidence-bearing report.

Evolution path:

```text
manual assisted audit
-> reproducible service
-> CLI
-> GitHub Action
-> GitHub App
-> optional subscription
```

## 12. Required negative memory

The M-minus ledger must preserve at least:

- traffic without conversion;
- visibility mistaken for traction;
- unsustainable sponsor benefits;
- false product-market fit;
- public disclosure before IP review;
- PII or credential leakage;
- generated volume mistaken for value;
- maintenance cost exceeding revenue;
- claims exceeding available evidence;
- fake or synthetic testimonials, stars, sponsors, or customers.

## 13. Definition of done for R0.1

R0.1 is complete when:

- core models validate;
- disclosure gates fail closed;
- sensitive financial fields are rejected;
- JSONL frontiers stream without fixed item ceilings;
- offer and tier sustainability are testable;
- experiment outcomes return scale/revise/stop/continue decisions;
- allocation is evidence-weighted;
- tests and CI pass;
- no external message, payment, publication, or banking mutation occurs.

## 14. Non-claims

R0.1 does not claim:

- guaranteed sponsorship or revenue;
- tax or legal compliance certification;
- automated customer acquisition;
- product-market fit;
- secure storage of banking secrets;
- autonomous public communication;
- permission to inspect third-party private repositories;
- scientific validation of TFUGA theories.

It is a proof-carrying decision and artifact-routing layer.