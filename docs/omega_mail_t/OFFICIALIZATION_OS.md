# Ω-MAIL-T R0.3 — Corporate Officialization OS

## Boundary

This software does not incorporate, register, license, certify, or legally
recognize a company. It prepares records and verifies operator-supplied
evidence before allowing one tightly controlled outbound email attempt.

Never store SINs, identity documents, private signing keys, OAuth tokens,
banking records, SMTP passwords, or unredacted sensitive filings in GitHub.

## Identity states

`IDEA → CANDIDATE_BRAND → INTERNAL_DIVISION → FOUNDING_PACKET_READY →
FILING_SUBMITTED → REGISTERED/INCORPORATED → DOMAIN_VERIFIED →
MAIL_AUTHENTICATED → PRODUCTION_AUTHORIZED`

A conceptual company, project, brand, or division must not be represented as an
incorporated company. `legal_name`, `neq`, `corporation_number`, and evidence
identifiers remain null until verified from authoritative records.

## Four gates

1. **Legal identity** — legal state, verified legal name, evidence IDs.
2. **Technical identity** — controlled domain, SPF, DKIM, and DMARC evidence.
3. **Authority** — the exact mailbox has `send_external` permission.
4. **Message policy** — sender identity, contact details, IP review, privacy,
   consent, unsubscribe mechanism, and a human approval bound to the exact
   SHA-256 content hash.

The production path rejects campaigns and requires exactly one recipient.

## CLI workflow

Create a candidate record:

```bash
omega-mail-official init-company --out private/company.json
```

Edit the record locally as real evidence becomes available. Do not commit
sensitive evidence; store opaque evidence IDs or hashes instead.

Compute the exact message hash:

```bash
omega-mail-official hash-message private/message.json
```

Run a non-network readiness analysis:

```bash
omega-mail-official readiness \
  --company private/company.json \
  --message private/message.json \
  --authority private/authority.json \
  --compliance private/compliance.json \
  --report private/readiness.json
```

Create explicit one-message approval:

```bash
omega-mail-official approve private/message.json \
  --approver Tristan \
  --note "Reviewed legal identity, recipient, claims and attachments" \
  --out private/approval.json
```

Dry-run the final command. This opens no network connection:

```bash
omega-mail-official send-one \
  --company private/company.json \
  --message private/message.json \
  --authority private/authority.json \
  --compliance private/compliance.json \
  --approval private/approval.json \
  --receipt private/dry-run-receipt.json
```

## Production locks

Real SMTP execution additionally requires all of the following:

- `--execute` on the command line;
- gate result `ALLOW_ONE_MESSAGE`;
- exactly one recipient;
- no E5 campaign classification;
- exact content-hash approval;
- `OMEGA_MAIL_EXTERNAL_SEND=I_ACKNOWLEDGE_ONE_MESSAGE`;
- `OMEGA_MAIL_ALLOWED_RECIPIENT` equal to the exact recipient;
- SMTP host, username and password provided through environment variables;
- legal identity, domain control, SPF, DKIM, DMARC and external-send evidence.

Example environment variable names:

```text
OMEGA_MAIL_SMTP_HOST
OMEGA_MAIL_SMTP_PORT
OMEGA_MAIL_SMTP_USERNAME
OMEGA_MAIL_SMTP_PASSWORD
OMEGA_MAIL_SMTP_SSL
OMEGA_MAIL_SMTP_STARTTLS
OMEGA_MAIL_ALLOWED_RECIPIENT
OMEGA_MAIL_EXTERNAL_SEND
```

Do not put their values in source code, examples, issues, logs, pull requests,
or generated reports.

## Production command

```bash
omega-mail-official send-one \
  --company private/company.json \
  --message private/message.json \
  --authority private/authority.json \
  --compliance private/compliance.json \
  --approval private/approval.json \
  --execute \
  --receipt private/provider-receipt.json
```

Provider acceptance is not proof of inbox delivery, legal service, consent,
contract acceptance, filing, or company officialization.

## Recommended first use

The first real external message should be a non-commercial administrative
inquiry to a known accountant, lawyer, incorporation service, domain provider,
or other professional. When the legal entity does not yet exist, the body and
signature must explicitly disclose preincorporation status.

## OAK prohibitions

The current release intentionally provides no bulk-send command, address
harvester, purchased-list importer, automatic consent inference, autonomous
legal filing, automatic contract acceptance, payment action, or publication of
potentially patentable information.
