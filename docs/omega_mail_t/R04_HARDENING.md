# Ω-MAIL-T R0.4 — execution hardening

R0.4 hardens the transition from an approved draft to one bounded provider attempt. It does not authorize a campaign, create a company, prove delivery, replace legal review, or make SMTP safe by itself.

## New execution chain

```text
canonical draft
→ OAK officialization gate
→ exact approval hash
→ approval freshness check
→ deterministic header validation
→ ledger reservation
→ one provider attempt
→ append-only result entry
```

## Anti-replay ledger

A production attempt requires `OneMessageLedger`. Before any network connection, the ledger appends a `RESERVED` entry. A second execution of the same canonical message hash is blocked even if the first process failed after the provider accepted the message.

The JSONL chain stores:

- sequence and timestamp;
- message SHA-256;
- recipient SHA-256, never the plaintext address;
- provider identifier;
- reservation identifier;
- previous-entry hash and current-entry hash;
- bounded operational status.

It does not store the subject, body, credentials, legal evidence, identity documents, private keys or plaintext recipient.

A stale `*.lock` file indicates an interrupted process and must be reviewed manually before removal. It must never be deleted automatically by an unrelated process.

## Approval freshness

The gate still binds approval to the canonical content hash. R0.4 adds an execution-time check immediately before reservation:

- approval must be present;
- scope must be `ONE_MESSAGE`;
- approver must be named;
- content hash must still match;
- approval must not be more than 3,600 seconds old by default;
- future timestamps beyond a five-minute clock-skew allowance are blocked.

`OMEGA_MAIL_APPROVAL_MAX_AGE_SECONDS` may reduce or increase the window, but the implementation refuses values above 86,400 seconds.

## Header and payload locks

Execution and dry-run rendering reject:

- more or fewer than one recipient;
- CR/LF injection in sender, recipient or subject;
- subjects longer than 200 characters;
- bodies larger than 256,000 UTF-8 bytes;
- attachments until a content-addressed attachment pipeline exists.

Attachments are intentionally blocked rather than silently ignored or sent without their bytes being included in the approval hash.

## SMTP endpoint locks

A real SMTP attempt requires all of the following:

```text
OMEGA_MAIL_EXTERNAL_SEND=I_ACKNOWLEDGE_ONE_MESSAGE
OMEGA_MAIL_ALLOWED_RECIPIENT=<exact recipient>
OMEGA_MAIL_ALLOWED_SMTP_HOST=<exact host>
OMEGA_MAIL_ALLOWED_SMTP_PORT=<exact port>
OMEGA_MAIL_EXECUTION_LEDGER=<path outside public Git data>
```

Exactly one encrypted transport mode must be active: implicit SSL or STARTTLS. Plaintext authentication and ambiguous double-TLS configuration are blocked.

The generated `Message-ID` is deterministic from the canonical message hash. Provider acceptance remains distinct from inbox delivery, reading, agreement, legal notice effectiveness or business outcome.

## CLI

Dry-run remains the default:

```bash
omega-mail-official send-one \
  --company company.json \
  --message message.json \
  --authority authority.json \
  --compliance compliance.json \
  --approval approval.json \
  --receipt dry-run-receipt.json
```

A production attempt additionally needs `--execute` and a ledger:

```bash
omega-mail-official send-one \
  --company company.json \
  --message message.json \
  --authority authority.json \
  --compliance compliance.json \
  --approval approval.json \
  --ledger /private/path/omega-mail-ledger.jsonl \
  --execute \
  --receipt production-receipt.json
```

Audit the full hash chain without network access:

```bash
omega-mail-official audit-ledger /private/path/omega-mail-ledger.jsonl
```

## CI changes

- officialization tests run on pull requests, `main`, the R0.4 branch and manual dispatch;
- Python 3.10–3.13 are covered;
- the massive atlas generator now has `contents: read` only;
- generated records are uploaded as temporary artifacts instead of committed by a workflow;
- CI never opens SMTP or reads production credentials.

## OAK boundary

```text
provider acceptance != final delivery
delivery != reading
reading != consent
email != incorporation
hash chain != legal proof
passing tests != production certification
```
