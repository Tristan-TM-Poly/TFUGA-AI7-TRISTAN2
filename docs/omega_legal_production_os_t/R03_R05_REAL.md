# Ω-LEGAL-PRODUCTION-OS-T∞ R0.3–R0.6 — real operations

This release replaces provider simulations with code paths that perform real HTTPS requests when exact credentials and one-action interlocks are supplied. It also builds content-addressed government and incorporation packets that can be submitted through an authorized official portal session.

## Implemented provider calls

| Provider | Real effect | Hard boundary |
|---|---|---|
| `gmail-send` | Calls Gmail `users.messages.send` | One exact recipient hash and deterministic RFC Message-ID |
| `github-release-draft` | Calls GitHub Releases REST API | Creates or reuses a **draft** release only |
| `stripe-test-payment-intent` | Calls Stripe PaymentIntents API | Accepts `sk_test_` keys only and never confirms the intent |
| `dropbox-sign-test` | Calls Dropbox Sign Signature Request API | Forces `test_mode=1`; request is non-binding |

The provider response is not silently upgraded into a stronger claim. Gmail acceptance is not proof of recipient delivery. A Stripe test PaymentIntent is not money movement. A Dropbox Sign test request is not a legal signature. A GitHub draft release is not a public release.

## One-action interlock

All executions require the exact environment tuple:

```text
OMEGA_EXTERNAL_EXECUTION_ACK=I_ACKNOWLEDGE_ONE_ACTION
OMEGA_ALLOWED_ACTION_ID=<exact action id>
OMEGA_ALLOWED_ACTION_HASH=sha256:<exact canonical hash>
OMEGA_ALLOWED_PROVIDER=<exact provider>
```

Provider-specific values are stored outside GitHub source files:

```text
GMAIL_ACCESS_TOKEN
OMEGA_RECIPIENT_EMAIL
OMEGA_SENDER_EMAIL
OMEGA_MESSAGE_ID_DOMAIN

GITHUB_RELEASE_TOKEN
OMEGA_RELEASE_REPOSITORY

STRIPE_SECRET_KEY          # must begin sk_test_

DROPBOX_SIGN_API_KEY
OMEGA_SIGNER_EMAIL
```

The raw recipient and signer email addresses are matched against hashes in the approved action. Tokens and API keys are never written into receipts or ledger entries.

## Execution order

```text
load exact action JSON
→ recompute canonical action hash
→ validate state and distinct approvals
→ validate exact action/provider interlocks
→ reserve action hash in append-only ledger
→ write EXECUTION_STARTED
→ call provider HTTPS API
→ write PROVIDER_ACCEPTED or PROVIDER_REJECTED
→ write EFFECT_CONFIRMED only when the provider object itself is verified
→ produce content-bound receipt
→ reconcile through a separate provider GET
```

Missing acknowledgement or credentials are checked before reservation. Once a network attempt has been reserved, the same action hash cannot be retried silently.

## Provider idempotency

### Gmail

A deterministic RFC Message-ID is derived from the canonical action hash. Before sending, the provider searches the authenticated mailbox with `rfc822msgid:`. An existing message prevents a second send.

### GitHub release

The provider queries the release by exact tag before creation. Existing tags are returned as deduplicated objects. R0.3 rejects `draft=false`.

### Stripe

The canonical action hash is sent as the Stripe `Idempotency-Key`. Only test keys are accepted. `confirm=true` is rejected.

### Dropbox Sign

The local durable ledger is the primary anti-replay mechanism. The action id and hash are also included as provider metadata. GitHub-hosted execution is intentionally not enabled for this provider because the hosted runner ledger is ephemeral.

## Government and incorporation packets

`filing_packets.py` performs real artifact production:

- validates Québec or Canada jurisdiction;
- requires content hashes for every source document;
- blocks missing or modified documents;
- requires professional-review and founder-approval hashes;
- requires articles, registered office, directors and share structure for incorporation packets;
- blocks secret-like keys in metadata;
- writes a deterministic manifest and submission checklist into a ZIP;
- marks the package `READY_FOR_AUTHORIZED_PORTAL_SUBMISSION`;
- records the official portal receipt later without retaining the raw reference number.

It does not log into a government portal, answer a personal attestation, invent legal facts or declare an entity incorporated before an official accepted receipt exists.

Build a packet:

```bash
omega-legal-real build-filing-packet filing-manifest.json \
  --output filing-packet.zip
```

Record the official result after authorized submission:

```bash
omega-legal-real record-filing-receipt \
  filing-manifest.json official-receipt.pdf \
  --reference-number QC-REFERENCE \
  --status ACCEPTED \
  --output recorded-receipt.json
```

## Provider CLI

Check configuration without revealing values:

```bash
omega-legal-real doctor --provider gmail-send
```

Execute one approved action:

```bash
omega-legal-real execute external_actions/approved/ACT-001.json \
  --provider gmail-send \
  --ledger /secure/omega/actions.jsonl \
  --receipt /secure/omega/receipts/ACT-001.json
```

Reconcile the provider object later:

```bash
omega-legal-real reconcile \
  external_actions/approved/ACT-001.json \
  /secure/omega/receipts/ACT-001.json \
  --ledger /secure/omega/actions.jsonl \
  --output /secure/omega/reconciled/ACT-001.json
```

## Protected GitHub workflow

`.github/workflows/omega-legal-real-execute.yml` is manual-only and runs from `main` under the `external-actions-sandbox` environment. It supports:

- Gmail one-message send;
- GitHub draft release;
- Stripe test PaymentIntent.

The repository owner must configure the protected environment, reviewers and secrets. A push, pull request, issue, email or generated command cannot start execution.

## Tests

The OAKBench injects a fake HTTP transport and checks the exact request shapes without using provider credentials or network access. It verifies:

- missing interlocks do not consume an action;
- recipient and signer hash binding;
- deterministic Gmail Message-ID and pre-send deduplication;
- draft-only GitHub release behavior;
- Stripe test-key and idempotency enforcement;
- rejection of live Stripe keys and automatic confirmation;
- forced Dropbox Sign `test_mode=1`;
- document byte hash validation;
- reservation before provider call;
- replay rejection before a second network request;
- filing role completeness and document integrity;
- secret-free filing metadata and provider doctor output;
- official receipt hashing without storing the raw portal reference.

## Still requiring real account setup

The provider code is executable, but a provider call requires credentials from the corresponding account. No credentials are generated or stored by this repository.

A legally binding signature, live payment, public release, government submission or production deployment remains blocked until the corresponding company identity, account, authority, professional review and protected execution environment are configured.
