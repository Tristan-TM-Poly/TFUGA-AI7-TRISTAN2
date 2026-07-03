from omega_deeptech_forge import EvidenceLevel, Signal
from omega_deeptech_forge.oakbench import rank_signals


signals = [
    Signal(
        title="Quebec Critical Minerals IP Radar",
        summary="Public-safe service hypothesis for monitoring papers, patents, grants and offtake signals around gallium, graphite, lithium and niobium.",
        source_urls=("https://example.org/public-source",),
        domain="critical-minerals",
        novelty_score=0.42,
        testability_score=0.86,
        revenue_score=0.88,
        disclosure_risk=0.12,
        evidence_level=EvidenceLevel.MULTI_SOURCE,
        tags=("quebec", "materials", "ip", "revenue"),
    ),
    Signal(
        title="Private AI energy scheduling invention",
        summary="A private optimization mechanism that should not be disclosed before IP review.",
        source_urls=("https://example.org/private-context",),
        domain="ai-energy",
        novelty_score=0.84,
        testability_score=0.78,
        revenue_score=0.72,
        disclosure_risk=0.91,
        evidence_level=EvidenceLevel.MEASURED,
        tags=("invention", "energy", "scheduler"),
    ),
]


def main() -> None:
    print("Ω-DeepTech Forge OAKBench demo")
    for result in rank_signals(signals):
        print("-", result.signal.title)
        print("  score:", result.action_score)
        print("  band:", result.priority_band)
        print("  public_action_allowed:", result.public_action_allowed)
        print("  first_action:", result.github_actions[0])


if __name__ == "__main__":
    main()
