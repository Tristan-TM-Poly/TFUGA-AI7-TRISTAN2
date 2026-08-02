# Ω-INBOX-TO-OUTCOME-T R0.1

A bounded inbox-to-outcome operating layer above `omega_company_autopilot_t` and `omega_mail_t`.

## Core loop

```text
RECEIVE -> RESOLVE IDENTITY -> CLASSIFY -> OPEN CASE -> PLAN -> PRODUCE
-> OAK VALIDATE -> ROUTE -> DRY-RUN DISPATCH -> EVIDENCE -> FOLLOW-UP -> M-
```

## Important boundary

This package does **not** autonomously access a real mailbox, send a real email, grant a Drive/Dropbox permission, push a GitHub change, submit a portal form, sign a document, accept a contract, change banking information, or disclose confidential information.

The initial implementation provides:

- provider-neutral intake normalization;
- idempotence and anti-loop metadata;
- prompt-injection quarantine signals for externally controlled text;
- deterministic intent and requirement extraction;
- identity and recipient-authority records;
- case and task graphs;
- risk-proportional reply decisions;
- file-backed deliverable drafts and manifests;
- OAK validation and content hashes;
- channel routing decisions;
- dry-run delivery receipts;
- a 110,592-cell deterministic policy atlas generated in CI.

## Autonomous delivery principle

Autonomy is granted to a narrow contract, never to an agent globally. An `AutonomousDeliveryContract` binds:

- company and division;
- allowed intents;
- allowed deliverables;
- allowed channels;
- identity and authority thresholds;
- data classification ceiling;
- reply and delivery quotas;
- expiry and kill switch.

## Decision classes

```text
AUTO_REPLY
AUTO_PRODUCE_DRAFT_DISPATCH
AUTO_BOUNDED_DISPATCH
REQUIRE_APPROVAL
REQUIRE_TWO_APPROVALS
PROFESSIONAL_REVIEW
REQUIRE_INFORMATION
QUARANTINE
BLOCK
```

`AUTO_PRODUCE_DRAFT_DISPATCH` means the system can prepare the deliverables and the intended dispatch package. It does not mean that the network transmission has occurred.

## High-risk invariants

Professional review or explicit approval remains required for legal and government correspondence, tax matters, banking changes, contracts, privacy requests, security incidents, confidential IP, commercial commitments, invoices, and sensitive personal data.

## CLI

```bash
omega-inbox-outcome dry-run \
  private/event.json \
  private/identity.json \
  private/delivery_contract.json \
  --workspace private/inbox_outcome \
  --report private/case_report.json
```

Policy atlas:

```bash
omega-inbox-atlas generate generated/inbox_policy_atlas
omega-inbox-atlas audit generated/inbox_policy_atlas
```

## Atlas dimensions

```text
16 intents × 12 deliverables × 8 risk modes × 6 autonomy levels
× 4 channels × 3 policy layers = 110,592 cells
```

The atlas is generated and uploaded as a CI artifact instead of permanently bloating Git history.

## Next controlled adapters

1. read-only Gmail intake;
2. draft-only Gmail replies;
3. GitHub issue/PR draft adapter;
4. Drive/Dropbox upload in an isolated test folder;
5. exact-recipient email dispatch behind approval and allowlists;
6. follow-up scheduler and delivery-confirmation ledger.
