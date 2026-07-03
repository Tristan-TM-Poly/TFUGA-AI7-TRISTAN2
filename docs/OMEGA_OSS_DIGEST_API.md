# Ω-OSS-DIGEST-T API Layer

This layer adds real, OAK-safe API primitives to the MAX scaffold.

## Modules

```text
api_layer.py           consolidated API layer for GitHub + StackExchange ingestion
CachedHttpClient       disk cache, conditional requests, retry-after metadata, x-ratelimit-reset metadata, StackExchange backoff awareness
GitHubSearchIntent     typed search-intent object
GitHubApiClient        GitHub REST search/repository client
StackExchangeApiClient StackExchange /search/advanced client
Secret scanner         local high-signal secret detector
Dependency inventory   pyproject.toml and package.json dependency extraction
```

## Environment variables

```bash
export GITHUB_TOKEN="..."                 # optional but recommended
export STACKEXCHANGE_KEY="..."            # optional
export STACKEXCHANGE_ACCESS_TOKEN="..."   # optional
```

## Example queries

```python
from omega_oss_digest_t.api_layer import GitHubSearchIntent, digest_github_search

intent = GitHubSearchIntent(
    keywords=("heat equation", "finite difference"),
    language="Python",
    license="mit",
    min_stars=50,
    pushed_after="2024-01-01",
)
records = digest_github_search(intent, limit=5)
```

## CLI target vocabulary

```bash
oss-digest compile-github "heat equation" "finite difference" --language Python --license-id mit --min-stars 50 --pushed-after 2024-01-01
oss-digest github-search "heat equation" "finite difference" --language Python --limit 5
oss-digest stack-search "numpy broadcasting error" --tag python --tag numpy --limit 5
oss-digest scan-local .
```

## OAK API rules

1. Prefer authenticated GitHub requests.
2. Use local cache and conditional requests for repeat reads.
3. Avoid polling; prefer webhooks or scheduled digest passes.
4. Handle `retry-after` and `x-ratelimit-reset`.
5. Avoid concurrent API floods.
6. StackExchange `backoff` must be honored by same-method calls.
7. Do not repeat semantically identical StackExchange requests more than once per minute.
8. Store provenance before reuse.
9. Never auto-integrate direct code from no-license or CC BY-SA sources.
10. Run local secret/dependency scans before PR/canonization.

## MAX next layer

- Add SBOM export/import wrappers.
- Add GitHub issue/PR generator guarded by OAK reports.
- Add upstream contribution ledger.
- Add M⁻ obsolete-answer detector for StackOverflow answers.
