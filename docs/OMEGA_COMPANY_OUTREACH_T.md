# Ω-COMPANY-OUTREACH-T R0.1

This module connects Tristan's external email activity to GitHub cases and company operating roles.

## Control model

```text
Gmail transport
→ recipient and receipt hashes
→ one GitHub outreach case
→ company routing policy
→ public-safe append-only ledger
→ reply/follow-up decision
```

GitHub stores no message body, raw recipient address, OAuth token or private attachment. Gmail remains the evidence source for content and delivery metadata.

## Company routing

- `tristan_parent_opco`: entrepreneurship, financing programs and strategic partnerships;
- `tristan_oak_systems`: audit, governance, evidence and risk;
- `tristan_software_labs`: software pilots, integrations and customer discovery;
- `tristan_research_foundry`: universities, laboratories and research pilots.

These are candidate/internal operating roles unless an independently verified legal entity and corporate domain are registered. The current Gmail account must not impersonate a corporate sender.

## Public-safe case

Each case contains:

- case identifier;
- company unit;
- outreach kind;
- target organization name;
- recipient SHA-256 hash;
- subject and bounded purpose;
- provider receipt SHA-256 hash;
- GitHub issue;
- follow-up date;
- legal-entity and domain verification flags.

## Commands

```bash
omega-company-outreach validate-case company_outreach/cases/OUT-2026-0001.json
omega-company-outreach append-case company_outreach/cases/OUT-2026-0001.json --ledger generated/outreach.jsonl
omega-company-outreach audit-ledger generated/outreach.jsonl
omega-company-outreach disclosure tristan_research_foundry
```

## Current cases

- `OUT-2026-0001`: Parent OpCo → Futurpreneur Canada;
- `OUT-2026-0002`: Research Foundry → Polytechnique Montréal.

The cases record only hashes for recipients and Gmail provider receipts. Their message content remains in Gmail.

## OAK boundaries

Blocked by policy:

- false claims of incorporation or verified corporate identity;
- contract acceptance, binding admissions or signing authority;
- banking-coordinate changes or wire instructions;
- government attestations;
- duplicate provider receipts;
- duplicate case identifiers;
- follow-up loops without a new event or cooldown;
- public storage of raw recipient addresses, message bodies or credentials.
