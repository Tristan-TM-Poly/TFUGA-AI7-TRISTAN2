# Ω-OSS-DIGEST First Operational Run

Generated: 2026-06-29T13:53:59.302942+00:00

## Mission

First operational digestion pass for Ω-OSS-DIGEST-T. The goal is to seed the supply-chain immune system before adding broader GitHub/StackOverflow absorption.

## Candidate basket

| Source | Role | License | OAK status | Reuse mode |
|---|---|---:|---|---|
| `anchore/syft` | SBOM generation / package cataloging | Apache-2.0 | OAK_GREEN_USE | external wrapper first |
| `gitleaks/gitleaks` | secret scanning / credential leak detection | MIT | OAK_GREEN_USE | external wrapper with private findings |
| `oss-review-toolkit/ort` | license compliance / dependency policy | Apache-2.0 | OAK_GREEN_USE | reference architecture + wrapper |
| `aboutcode-org/scancode-toolkit` | license/origin scanning | Apache-2.0 | OAK_GREEN_USE | external wrapper + notice enrichment |
| `pypa/pip-audit` | Python vulnerability auditing | Apache-2.0 | OAK_GREEN_USE | local Python dependency gate |

## CVCD extraction

The common fertile invariant is:

```text
source artifact
→ evidence extraction
→ normalized finding
→ risk classification
→ OAK decision
→ action: allow / attribute / rewrite / scan deeper / block / M⁻ archive
```

This gives Ω-OSS-DIGEST-T a concrete immune stack:

```text
LicenseGate++        ← ORT + ScanCode inspiration
SBOMGate             ← Syft wrapper
SecretGate           ← Gitleaks wrapper
VulnerabilityGate    ← pip-audit wrapper
ProvenanceLedger     ← internal append-only JSONL
OAKReport            ← internal Markdown/JSON output
MMinusRegistry       ← recurring failure memory
```

## OAK decisions

All five seeds are currently **safe to study and wrap** as external tools. Direct code reuse remains conditional on preserving license notices, provenance, version pinning, and compatibility review.

## Immediate actions

1. Add wrapper interfaces: `SbomScanner`, `SecretScanner`, `LicenseScanner`, `VulnerabilityScanner`.
2. Store every scanner output as evidence, not truth.
3. Add redaction layer before any public report.
4. Generate `THIRD_PARTY_NOTICES.md` from `ProvenanceLedger`.
5. Add M⁻ entries for no-license, stale, vulnerable, or incompatible sources.

## Canon status

`Ω-OSS-DIGEST-T` moves from **architecture + API scaffold** to **first operational seed run**. It is not yet autonomous ingestion; it is an OAK-safe, reversible, tool-wrapping digestion loop.
