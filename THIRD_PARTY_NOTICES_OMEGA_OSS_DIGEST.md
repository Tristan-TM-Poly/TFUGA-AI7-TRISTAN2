# Third-Party Notices — Ω-OSS-DIGEST-T Seed Run

This file records third-party open-source projects identified during the first Ω-OSS-DIGEST operational seed run. These projects are currently treated as external tools or reference architectures, not vendored source code.

Generated: 2026-06-29

## OAK policy

- Preserve provenance before use.
- Prefer external CLI/library wrappers before direct code reuse.
- Preserve copyright/license notices when distributing copied or adapted material.
- Keep scanner findings private/redacted unless intentionally disclosed.
- Re-check exact versions before production integration.

## Seed sources

### anchore/syft

- Repository: https://github.com/anchore/syft
- Role: SBOM generation / package cataloging
- License observed: Apache-2.0
- Intended use: external wrapper / SBOMGate
- Direct code reuse: conditional on preserving Apache-2.0 license and applicable notices.

### gitleaks/gitleaks

- Repository: https://github.com/gitleaks/gitleaks
- Role: secret scanning / credential leak detection
- License observed: MIT
- Intended use: external wrapper / SecretGate
- Direct code reuse: conditional on preserving MIT copyright/license notice.
- OAK privacy note: findings must be redacted by default.

### oss-review-toolkit/ort

- Repository: https://github.com/oss-review-toolkit/ort
- Role: license compliance / dependency policy evaluation
- License observed: Apache-2.0
- Intended use: reference architecture + external wrapper / LicenseGate++
- Direct code reuse: conditional on preserving Apache-2.0 license and applicable notices.

### aboutcode-org/scancode-toolkit

- Repository: https://github.com/aboutcode-org/scancode-toolkit
- Role: license/origin scanning and package metadata detection
- License observed: Apache-2.0
- Intended use: external wrapper / evidence enrichment
- Direct code reuse: conditional on preserving Apache-2.0 license and applicable notices.

### pypa/pip-audit

- Repository: https://github.com/pypa/pip-audit
- Role: Python dependency vulnerability auditing
- License observed: Apache-2.0
- Intended use: external wrapper / VulnerabilityGate
- Direct code reuse: conditional on preserving Apache-2.0 license and applicable notices.

## StackOverflow / StackExchange policy

StackOverflow / StackExchange content is treated primarily as explanation, pattern source, and anti-pattern memory. Direct snippet reuse is avoided by default and requires attribution plus share-alike compatibility review.
