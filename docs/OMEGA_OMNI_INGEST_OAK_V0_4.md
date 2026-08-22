# Ω-OMNI-INGEST-OAK v0.4 — Automation Spec

## Objective

Turn Drive files, local folders, and authorized/public web sources into provenance-bearing artifacts that can be searched, tested, compared, and reused without confusing a capture with a scientific validation.

## Hard invariants

1. `Idea != SourceCaptured != TestedSoftware != Simulated != Prototype != Measured`.
2. Generator != Judge. A generated parser stays `QUARANTINE` until independent tests and an approval gate pass.
3. No auth/paywall/CAPTCHA/access-control bypass.
4. Generic web crawling obeys `robots.txt`; documented APIs use their published access rules and rate limits.
5. Private/reserved network addresses are denied by default (SSRF guard).
6. Raw copyrighted/private material belongs in a private evidence vault; GitHub should carry code, hashes, manifests, schemas, tests, and derived reports.
7. No automatic `MEASURED` or `CERTIFIED_EXTERNAL` status.
8. No direct auto-merge to `main`; automation proposes a branch/PR and waits for CI + review policy.

## Pipeline

`DISCOVER -> POLICY -> FETCH/IMPORT -> HASH -> RAW VAULT -> EXTRACT -> DEDUP -> CLAIM/CETER -> OAK -> M-/P0-pattern -> REPORT -> PR/ARCHIVE`

## JKD interpretation

JKD is implemented as a bounded repair loop: detect the smallest failing gate, modify the smallest component, rerun the relevant tests, and record the failed attempt. It is not permission to bypass security or silently widen authority.

## PDF statistics

The full Drive artifact includes a `pdfstats` module using `pypdf` text extraction. Page count is exact from the PDF structure when readable; word count is an extraction count; `equation_like_lines` is explicitly a heuristic and must never be presented as an exact equation count.

## Web source adapters

The initial adapters construct documented requests for arXiv, OpenAlex, Crossref, and PubChem PUG REST. Generic URLs go through robots + SSRF + byte-budget gates.

## Tool morphogenesis

Unknown formats produce parser proposals and fixtures under quarantine. Promotion requires positive fixtures, negative/adversarial fixtures, resource limits, and an independent approval/CI gate. For genuinely untrusted generated code, use a real container/microVM sandbox; Python subprocess isolation is not a security boundary.

## External-action boundary

This integration can fetch public/authorized evidence and create provenance receipts, but it does not bypass access controls, self-certify physical truth, or auto-merge itself. Generated tools and scientific claims remain gated by independent evidence and permissions.
