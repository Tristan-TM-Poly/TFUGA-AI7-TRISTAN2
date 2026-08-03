# Ω-COMPANY-OUTREACH-T R0.2

## Purpose

Ω-COMPANY-OUTREACH-T connects external Gmail communication to Tristan's GitHub and operating-company architecture without publishing addresses, message bodies, OAuth credentials or confidential attachments.

## Control loop

```text
strategic opportunity
→ company routing
→ consent / purpose / risk gate
→ strategic score
→ human-authorized Gmail send
→ public-safe receipt
→ reply classification
→ company-specific next action
→ cooldown / quota gate
→ close, follow up or escalate
```

## Company routing

| Unit | Scope | Voice |
|---|---|---|
| Tristan Parent OpCo | entrepreneurship, programs, financing and strategic partnerships | concise, commercially grounded, non-binding |
| Tristan OAK Systems | audit, governance, evidence and risk | precise, traceable and risk-explicit |
| Tristan Software Labs | software pilots, integrations and customer discovery | technical, measurable and low-friction |
| Tristan Research Foundry | universities, laboratories and research pilots | scholarly, bounded and falsifiable |

These names are operating roles. They are not represented as incorporated persons until legal status and corporate domains are independently verified.

## Public-safe evidence

GitHub may contain:

- company unit;
- target organization;
- subject and bounded purpose;
- HMAC/SHA-256 recipient, message and thread identifiers;
- Gmail receipt hash;
- event class and next action;
- strategic score;
- GitHub issue linkage;
- cooldown and portfolio status.

GitHub must not contain:

- raw email addresses;
- raw Gmail IDs;
- message bodies or reply snippets;
- OAuth tokens;
- private attachments;
- banking, identity, signature or government credentials.

Future counterparty hashes should use HMAC-SHA-256 with a secret salt stored outside the repository. Legacy SHA-256 receipts remain supported for compatibility.

## Strategic scoring

Signals are scored from 0 to 5:

- relevance;
- decision authority;
- problem fit;
- evidence readiness;
- timing;
- reciprocity;
- execution effort;
- risk.

Results are categorized as `send_or_continue`, `draft_for_review`, `wait`, `hold` or `block`. A score never authorizes an irreversible or legally binding act.

## Reply intelligence

Private metadata can be transformed into a public event with:

```bash
OMEGA_OUTREACH_HASH_SALT='<external-secret>' \
omega-company-outreach ingest-reply private_reply.json \
  --event-id EVT-2026-0003-REPLY \
  --out company_outreach/events/EVT-2026-0003-REPLY.json
```

The classifier distinguishes:

- positive interest;
- information request;
- referral;
- automatic reply;
- decline;
- bounce;
- unsubscribe;
- unknown/human review.

The raw subject, snippet, sender and provider IDs are consumed privately and are not written to the public event.

## Quotas and anti-spam rules

Default portfolio limits:

- 5 external sends per day;
- 2 sends to the same organization within 30 days;
- 1 unanswered follow-up;
- 12 simultaneously open cases;
- 14-day follow-up cooldown;
- no mass marketing;
- no send triggered by push, pull request, issue or inbound email alone.

Commercial electronic messages require an adequate consent basis, verified sender identity and a verified unsubscribe mechanism. High-risk outreach is routed to Ω-LEGAL-PRODUCTION-OS instead.

## CLI

```bash
omega-company-outreach validate-case company_outreach/cases/OUT-2026-0001.json
omega-company-outreach score-case \
  company_outreach/cases/OUT-2026-0001.json \
  company_outreach/strategy/OUT-2026-0001.signals.json
omega-company-outreach portfolio-check company_outreach/cases
omega-company-outreach dashboard company_outreach/cases \
  --events-dir company_outreach/events \
  --format markdown --out generated/outreach-dashboard.md
omega-company-outreach audit-ledger generated/outreach-ledger.jsonl
```

## Current cases

- `OUT-2026-0001`: Parent OpCo → Futurpreneur Canada.
- `OUT-2026-0002`: Research Foundry → Polytechnique Montréal.

Both are bounded, non-commercial, non-contractual and recorded with public-safe hashes. A future reply creates a new event and does not silently rewrite the original send evidence.

## OAK boundary

This package prepares, classifies, scores and audits strategic outreach. It does not:

- constitute a company;
- create a corporate domain;
- sign contracts;
- submit government attestations;
- change banking instructions;
- send mass campaigns;
- permit autonomous reply loops;
- convert a positive classifier result into an external commitment.
