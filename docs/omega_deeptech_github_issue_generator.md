# Ω-DeepTech Forge GitHub Issue Generator

**Status:** v0.1 dry-run issue drafting scaffold, OAK-safe.

This module converts `Signal` objects into public-safe GitHub issue drafts by routing through:

```text
Signal -> OAKBenchResult -> GitHubIssueDraft
```

It does **not** call the GitHub API. It generates deterministic titles, bodies and labels that can be reviewed or passed to a connector only after approval.

## OAK routing

- `blocked` -> repair issue.
- `repair` -> source-repair issue.
- `review` -> redacted IP-review issue.
- `build` -> prototype issue.
- `commercialize` -> commercial validation issue.
- `observe` -> observe/backlog issue.

## Safety rules

- Sensitive `PATENT_REVIEW` and `TRADE_SECRET` routes use the redacted handoff summary.
- Private source URLs are not placed into public issue bodies for sensitive routes.
- The issue body records forbidden actions.
- No external outreach, patent filing, publication or revenue claim is authorized by the generated draft.

## Minimal use

```python
from omega_deeptech_forge import EvidenceLevel, Signal, build_github_issue_draft

signal = Signal(
    title="Quebec Critical Minerals IP Radar",
    summary="Public-safe service hypothesis.",
    source_urls=("https://example.org/source",),
    evidence_level=EvidenceLevel.MULTI_SOURCE,
    testability_score=0.9,
    revenue_score=0.9,
    disclosure_risk=0.1,
)

draft = build_github_issue_draft(signal)
print(draft.title)
print(draft.body)
print(draft.labels)
```

## Next layer

The next layer may create real GitHub issues through an explicit connector, but only with:

1. dry-run preview,
2. OAK status recorded,
3. IP-sensitive routes redacted,
4. approval gate before public issue creation,
5. no external sending or filing.
