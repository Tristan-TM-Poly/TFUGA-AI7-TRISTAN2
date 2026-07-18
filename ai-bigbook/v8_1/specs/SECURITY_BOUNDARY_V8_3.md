# Security Boundary V8.3

This file converts the unsafe "absolute delegation" prompt into a safe GitHub-native governance rule.

## Refused by design

The AI-BIGBOOK / AI-7 stack must not:

- bypass LLM or platform safety filters,
- extract secrets from Google Drive, Dropbox, local files, or environment variables,
- inject repository secrets automatically,
- push directly to `main` without review,
- create scheduled deployment loops that run cloud hooks by default,
- call Render/Vercel deploy hooks without explicit human approval,
- perform payments, credential access, scraping, spam, or self-replication.

## Safe replacement

Use pull requests, draft reviews, local patches, and explicit workflow dispatch.

```text
proposal -> branch -> PR -> CI -> EvidenceGate -> human review -> merge
```

## CI policy

Allowed:

- lint/check Python scripts,
- run EvidenceGate on JSONL claim registries,
- generate local address-space samples,
- verify that PowerReal stays in [0,1],
- produce reports as local artifacts.

Blocked:

- cron deploy loops,
- secret-dependent external calls,
- automatic cloud deployment,
- direct main mutation,
- network calls that mutate external services.

## Agent law

```text
FORGE-PRIME may propose.
EVIDENCE-OAK may judge.
RED-SHADOW may attack.
OUROBOROS-OMEGA may guard.
ApprovalSentinel decides what leaves the local patch boundary.
```

## Canon sentence

Max Plus Ultra is not unlimited permission. It is maximum ambition under maximum verification.
