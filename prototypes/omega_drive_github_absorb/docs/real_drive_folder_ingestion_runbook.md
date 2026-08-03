# Runbook — Real Google Drive folder ingestion, redacted/OAK-safe

This runbook documents how to handle a real Google Drive folder link without publishing the raw URL or folder ID in a public GitHub repository.

## Trigger

A real Google Drive folder URL has been provided out-of-band or in a private conversation.

## Non-negotiable rule

Do not commit the raw Drive URL or raw folder ID to this public repository.

## Safe handling path

```text
real Drive folder link
→ local-only input/drive_links.local.txt
→ L1 inventory-only manifest
→ redacted OAK report
→ private review
→ L2 download only with readonly OAuth and explicit approval
→ sha256 + provenance ledger
→ extraction only after OAK gate
→ draft PR with redacted reports only
```

## Local-only file

Create this file locally. It is ignored by Git:

```text
prototypes/omega_drive_github_absorb/input/drive_links.local.txt
```

Paste the real folder URL there, not in committed examples.

## L1 inventory command

```bash
PYTHONPATH=prototypes/omega_drive_github_absorb \
python -m omega_drive_github_absorb \
  prototypes/omega_drive_github_absorb/input/drive_links.local.txt \
  --repo Tristan-TM-Poly/TFUGA-AI7-TRISTAN2 \
  --level L1 \
  --max-level L1 \
  --out generated/omega_drive_github_absorb
```

## Expected local outputs

```text
generated/omega_drive_github_absorb/
  drive_manifest.json
  github_sync_plan.json
  theory_seed_hypergraph.json
  oak_report.json
```

## Redaction policy

Before any output is committed:

- remove raw `source_url`
- remove raw `drive_file_id` unless the repo is private and explicitly approved
- preserve `source_url_sha256` for provenance without exposing the secret link
- preserve OAK verdicts and scanner flags
- preserve counts and risk summaries

## L2 download preconditions

L2 is blocked unless all are true:

- readonly Google Drive OAuth is configured
- the Drive link is owned by or explicitly shared with the operator
- `allow_download=true` is set in a local-only policy file
- secrets are not stored in Git
- OAK report returns no `BLOCK_*` verdict
- IP/confidentiality review permits private sync

## Publication rule

No raw PDF, ZIP, Doc export, extracted page text, or generated chunk from private Drive may be pushed to a public repository without explicit OAK/IP approval.
