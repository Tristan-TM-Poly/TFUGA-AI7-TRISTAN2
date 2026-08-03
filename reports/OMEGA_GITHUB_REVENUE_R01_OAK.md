# Ω-GITHUB-REVENUE-T∞ R0.1 — OAK Report

## Status

**Candidate status:** D (demonstrated in software once CI passes on the exact PR head)  
**Current status before CI:** X/D boundary  
**External revenue status:** unobserved  
**GitHub Sponsors approval status:** external to this repository and not inferred here.

## Implemented evidence

- typed Python models for artifacts, evidence, offers, tiers, experiments, and revenue events;
- bounded evidence/value score;
- fail-closed disclosure gate;
- explicit separation between observed paying-user evidence and general maturity;
- offer compiler with exclusions and maintenance gate;
- sponsor-tier sustainability check;
- experiment decision kernel;
- evidence-weighted capital allocation;
- lazy frontier processing tested beyond 10,000 records;
- hash-chained JSONL ledger;
- recursive rejection of forbidden banking, tax-identifier, credential, and home-address field names;
- CLI, schema, policy, fixtures, documentation, and CI matrix.

## Falsifiable tests

1. Patent candidates cannot pass the public gate.
2. `PUBLIC_AFTER_REVIEW` cannot pass without explicit approval.
3. High-maintenance artifacts cannot become sustainable offers.
4. Unlimited custom work makes a sponsor tier unsustainable.
5. Revenue events reject negative amounts and fees above gross revenue.
6. Banking-field names are rejected before a ledger file is created.
7. Hash-chain tampering is detected.
8. A 12,001-item lazy frontier completes without a fixed total-item ceiling.
9. Allocation never exceeds the available budget.
10. Paying-user evidence is not fabricated from tests, stars, volume, or visibility.

## Residual risks

- The sensitive-field detector is key-based and is not a complete data-loss-prevention system.
- Hash chaining provides tamper evidence only under its stated threat model; it is not independent notarization.
- Value scores encode policy choices and require calibration against real outcomes.
- Sponsor-tier cost assumptions are configurable estimates, not accounting facts.
- The artifact schema is checked structurally by tests and code, but R0.1 does not add an external JSON Schema dependency.
- No customer, sponsor, contract, invoice, payment, profit, or product-market fit has been demonstrated by this code alone.
- Tax treatment and legal obligations require authoritative professional or government guidance.

## M-minus entries opened

- M-REV-001: code volume can be mistaken for value.
- M-REV-002: Sponsors approval can be mistaken for received sponsorship.
- M-REV-003: public traffic can be mistaken for conversion.
- M-REV-004: a low-priced tier can create an unsustainable delivery obligation.
- M-REV-005: repository ledgers can become accidental stores of sensitive financial data.
- M-REV-006: scoring can be mistaken for truth, valuation, or income prediction.

## Promotion gates

Promote R0.1 from X/D boundary to D only after:

- exact-head CI passes on Python 3.10 and 3.13;
- CLI demo executes;
- streaming fixture audit emits two records;
- privacy-field rejection test passes;
- PR diff contains no banking document or real banking value.

Promote an economic offer only after:

- one authorized pilot is delivered;
- utility is observed externally;
- delivery effort is measured;
- limitations are acknowledged;
- privacy and IP review pass;
- a real transaction, if any, is recorded outside public GitHub data.

## Next experiment

Run one consented OAKGate audit on an external or separate owned repository, measure:

- setup time;
- delivery time;
- actionable findings;
- false-positive rate;
- user-rated usefulness;
- willingness to repeat or pay;
- confidentiality and privacy incidents.

Decision rule: scale only after observed external utility and sustainable delivery cost. Otherwise revise or stop.