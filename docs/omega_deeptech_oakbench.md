# Ω-DeepTech Forge OAKBench

**Status:** v0.1 action-scoring scaffold, OAK-safe.

OAKBench turns one or more DeepTech Forge `Signal` objects into ranked action decisions for GitHub/AUTO² workflows.

```text
Signal -> ReviewPacket -> OAKBenchResult -> GitHub action queue
```

## Priority bands

- `blocked` — metadata is broken; repair before processing.
- `repair` — sources/evidence are insufficient; keep draft-only.
- `review` — patent/trade-secret/IP risk; public automation disabled.
- `build` — safe enough to prototype with tests, baselines and failure modes.
- `commercialize` — public-safe service signal; create offer card and pilot checklist.
- `observe` — archive/backlog until evidence or market clarity improves.

## OAK constraints

- OAKBench is not a market forecast, legal opinion, patentability opinion, investment recommendation or revenue guarantee.
- Sensitive IP classes disable public automation even when the action score is high.
- Commercialization score is only a triage signal; actual revenue requires client validation.
- Every public artifact must be derived from redacted handoff/review packets when IP risk exists.

## Example

```python
from omega_deeptech_forge import EvidenceLevel, Signal, run_oakbench

result = run_oakbench(
    Signal(
        title="Quebec Critical Minerals IP Radar",
        summary="Public-safe service hypothesis for monitoring IP and market signals.",
        source_urls=("https://example.org/source-a", "https://example.org/source-b"),
        domain="critical-minerals",
        novelty_score=0.45,
        testability_score=0.90,
        revenue_score=0.92,
        disclosure_risk=0.08,
        evidence_level=EvidenceLevel.MULTI_SOURCE,
        tags=("quebec", "materials", "revenue"),
    )
)

print(result.priority_band)
print(result.github_actions)
```

## Next integration targets

1. GitHub issue generator behind OAKBench gates.
2. JSON schema for OAKBench results.
3. Source ingestion adapters in dry-run only mode.
4. Quebec/Canada DeepTech digest builder.
5. CI workflow for `tests/test_omega_deeptech_*.py`.
