# Ω-OSS-DIGEST-T MAX Architecture

**GitHub Open-Source & StackOverflow Digestion Engine de Tristan**

This branch adds an OAK-safe architecture for searching, absorbing, improving, and using GitHub open-source repositories and StackOverflow/StackExchange knowledge without blind copy-paste.

## Core loop

```text
Intent
→ SearchCompiler
→ SourceCandidates
→ ProvenanceLedger
→ LicenseGate
→ Sandbox Fetch/Clone
→ RepoDigest
→ Static Analysis + Tests + SBOM + Secrets Scan
→ CVCD Pattern Extraction
→ OAK Decision
→ Action: use / rewrite / fork / issue / PR / canonize / M⁻ archive
```

## MAX doctrine

A repository, answer, snippet, issue or PR is not treated as truth. It becomes a living source node with provenance, license, revision, author, confidence, tests, security risk, CVCD invariants, attribution requirements, and OAK status.

## SearchCompiler

The engine should compile Tristan-intentions into structured queries:

```text
"finite difference heat equation" language:Python license:mit stars:>50 pushed:>2024-01-01
"microchannel cooling" "optimization" language:Python
"numpy broadcasting ValueError" site:stackoverflow.com
```

GitHub code search supports advanced syntax including qualifiers and regular expressions in GitHub's code search interface. API use must respect GitHub rate limits, authentication, caching, and anti-polling best practices.

## LicenseGate

- No explicit license / NOASSERTION ⇒ no direct code reuse.
- MIT/BSD/ISC/Zlib ⇒ generally reusable with copyright/license preservation.
- Apache-2.0 ⇒ preserve license and NOTICE when present; explicit patent license is valuable.
- LGPL/MPL/EPL ⇒ conditional; use dependency/adapters and review distribution model.
- GPL ⇒ compatible projects or sandbox/rewrite.
- AGPL ⇒ high-risk for SaaS/API/networked systems; strict review.
- StackOverflow CC BY-SA ⇒ explanation/pattern preferred; direct snippet requires attribution and share-alike compatibility.

## StackOverflow protocol

StackOverflow should primarily be digested as:

1. explanation of error modes,
2. pattern source,
3. anti-pattern registry,
4. version-obsolescence detector,
5. attribution ledger,
6. last-resort snippet source only if compatible.

The Stack Exchange API has throttles and daily quotas; identical semantic polling should be avoided and `backoff` instructions must be honored.

## OAK statuses

| Status | Meaning |
|---|---|
| OAK_GREEN_CANON | Highly fertile, tested, secure, license-compatible, canonizable |
| OAK_GREEN_USE | Usable with provenance, tests and notices |
| OAK_YELLOW_SANDBOX | Useful but needs isolation/tests/review |
| OAK_RED_REWRITE_ONLY | Extract invariant, rewrite implementation |
| OAK_RED_BLOCKED | License/security/provenance blocker |
| M_MINUS_ARCHIVE | Preserve as negative memory |

## ZERO-TOUCH safeguards

- Cache every source and API response with provenance.
- Never bypass rate limits.
- Never commit copied snippets without attribution manifest.
- Never auto-publish secrets discovered in scanned code.
- Never open external PRs without a human-readable diff and OAK report.
- Prefer reversible branches/PRs over direct writes to `main`.

## First MVP files

- `omega_oss_digest_t/license_gate.py`
- `omega_oss_digest_t/scorer.py`
- `omega_oss_digest_t/oak_runner.py`
- `omega_oss_digest_t/provenance_ledger.py`
- `omega_oss_digest_t/stackoverflow_attribution.py`
- `omega_oss_digest_t/cvcd_extract.py`
- `omega_oss_digest_t/report.py`

## Command vocabulary

```text
GO OSS-DIGEST SEARCH <intent>
GO OSS-DIGEST LICENSE <repo-or-answer>
GO OSS-DIGEST OAK <source>
GO OSS-DIGEST CANONIZE <source> -> <Omega branch>
GO OSS-DIGEST PR <upstream repo>
GO OSS-DIGEST M- <failed source>
```
