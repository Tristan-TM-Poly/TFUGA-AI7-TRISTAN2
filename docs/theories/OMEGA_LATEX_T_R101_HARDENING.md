# Ω-LATEX-T∞ R1.0.1 — OAK Hardening

This patch intentionally reduces evidence debt instead of expanding surface area.

## Closed failure modes

### Audit-total boundary

Malformed optional evidence subsystems are converted into OAK findings rather than being allowed to terminate `audit_document`.

```text
MALFORMED_EVIDENCE -> FINDING
MALFORMED_EVIDENCE != AUDITOR_CRASH
```

Proof-lineage duplicate IDs, invalid receipt shapes, self-parent links, missing parents and parent cycles are explicit findings.

### Self-verifying metadata receipts

New metadata receipts embed the raw metadata object alongside canonical raw and normalized SHA-256 identities. The report recomputes both hashes and re-normalizes metadata to detect tampering.

Legacy R1.0 receipts without embedded raw metadata remain readable but are classified as valid/unverified rather than cryptographically verified.

```text
RECEIPT_PRESENT != RECEIPT_VERIFIED
METADATA_HASH_MATCH != CLAIM_TRUTH
```

### Positive-semidefinite covariance gate

Covariance matrices must now be finite, square, symmetric and positive semidefinite. A stdlib modified-Cholesky gate rejects symmetric indefinite matrices and emits correlation/scale diagnostics.

```text
SYMMETRIC_MATRIX != VALID_COVARIANCE
PSD_COVARIANCE != CALIBRATED_MODEL
```

### Authorized-root filesystem gate

Universe manifests default to `allowed_roots: ["."]`, relative to the manifest directory. Input paths are resolved through symlinks and must remain under at least one explicit authorized root.

```text
PATH_EXISTS != PATH_AUTHORIZED
```

### Streaming universe execution

`build-universe` no longer materializes the full job plan or retains all loaded documents. It uses a deterministic flat cursor, O(1)-growth checkpoint state, and at most one resident `DocumentIR` at a time.

`universe-plan` remains a materialized review surface by design; the execution engine is the streaming component.

## CI governance

The Ω-LATEX workflow now runs on both pull requests and `push` events to `main`. This provides a post-merge smoke path even when repository branch protection is not configured.

Repository-level branch protection remains a GitHub governance setting outside the compiler itself.
