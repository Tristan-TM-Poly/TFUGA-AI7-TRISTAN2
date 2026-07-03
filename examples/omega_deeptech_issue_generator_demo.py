from omega_deeptech_forge import EvidenceLevel, Signal, build_github_issue_draft


signal = Signal(
    title="Quebec Critical Minerals IP Radar",
    summary="Public-safe service hypothesis for monitoring critical minerals IP and market signals.",
    source_urls=("https://example.org/source-a", "https://example.org/source-b"),
    domain="critical-minerals",
    novelty_score=0.45,
    testability_score=0.9,
    revenue_score=0.92,
    disclosure_risk=0.08,
    evidence_level=EvidenceLevel.MULTI_SOURCE,
    tags=("quebec", "materials", "revenue"),
)


def main() -> None:
    draft = build_github_issue_draft(signal, generated_at="2026-07-03T18:00:00+00:00")
    print(draft.title)
    print("labels:", ", ".join(draft.labels))
    print("intent:", draft.intent)
    print("public_safe:", draft.public_safe)
    print("--- body preview ---")
    print("\n".join(draft.body.splitlines()[:28]))


if __name__ == "__main__":
    main()
