# Ω-SYNERGY-OS R0.2 Threat Model

## Assets

- repository and source-head provenance;
- claim/evidence relationships;
- transformation contracts;
- portfolio decisions;
- generated reports and manifests;
- human review sovereignty;
- confidential, security, financial, legal, medical and IP-sensitive boundaries.

## Trust boundaries

Inputs are untrusted even when they originate in a Tristan repository. Generated code, claims, scores, interfaces and evidence references remain untrusted until independently checked. GitHub Actions runs with read-only repository permission and immutable action references.

## Principal threats

### Semantic adapter corruption

An adapter may silently drop scope, units, provenance, uncertainty or authority. Mitigation: loss-declaring receipts, schema validation, preserved-invariant lists and round-trip tests where possible.

### False closure

A lexical match may appear synergistic while no typed transformation exists. Mitigation: names are insufficient; bridge discovery requires output/input compatibility and a simplest baseline.

### Circular evidence

Two generated objects may cite one another or two agents may reuse the same source. Mitigation: evidence remains named, provenance-preserving and non-independent unless explicitly established.

### Score gaming

A generator may optimize the portfolio score rather than real value. Mitigation: hard gates precede score, dimensions remain visible, and external evidence cannot be replaced by internal volume.

### Recursive amplification

Generators may recursively produce duplicates, errors or CI load. Mitigation: recursive constellations are blocked without proof, portfolio, stop, finite-budget and rollback governors.

### Authority escalation

A plan may be mistaken for permission to merge, publish, release, spend, contact, deploy or file IP. Mitigation: A3 ceiling, immutable false flags for automatic merge/publication, explicit human review in every decision and manifest.

### Evidence replay after drift

Old evidence may be reused after dependencies, environment or test contracts change. Mitigation: semantic evidence context and states CURRENT, STALE, EXPIRED, SUPERSEDED, INVALIDATED and REVOKED.

### Artifact tampering

Reports may be modified after validation. Mitigation: SHA-256 receipt for each artifact, Merkle root, size checks and bundle audit.

### Supply-chain compromise

Moving GitHub Action tags may change executed code. Mitigation: workflow references are pinned to reviewed 40-character commit SHAs and audited by CI.

### Secret or confidential-data exposure

Repository audits may ingest sensitive content. R0.2 performs no network submission and no external outreach. Sensitive product pilots require explicit scope authorization, redaction, retention rules and deletion/rollback contracts.

## Non-goals

R0.2 does not provide complete sandbox isolation, cryptographic signer identity, legal admissibility, malware analysis, dynamic dependency completeness, security certification or autonomous remediation.

## Security invariants

```yaml
authority_ceiling: A3
human_review_required: true
automatic_merge_allowed: false
automatic_publication_allowed: false
remote_repository_mutation: false
secret_access: false
spending_authority: false
external_outreach_authority: false
self_authority_escalation: false
```

## Incident response

On a critical residual:

1. halt the affected campaign;
2. preserve content-addressed evidence and logs;
3. revoke or invalidate dependent evidence;
4. quarantine generated interfaces or generators;
5. restore the last known reversible checkpoint;
6. record the failure in M−;
7. require human review before resumption.
