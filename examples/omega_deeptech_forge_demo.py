from omega_deeptech_forge import EvidenceLevel, Signal, forge_decision


signal = Signal(
    title="Quebec sodium-ion storage opportunity",
    summary=(
        "A market and research signal suggesting sodium-ion batteries may be useful "
        "for stationary storage pilots, pending cost, cycle-life and safety validation."
    ),
    source_urls=("https://example.org/source-to-replace",),
    domain="energy-materials",
    novelty_score=0.52,
    testability_score=0.82,
    revenue_score=0.74,
    disclosure_risk=0.20,
    evidence_level=EvidenceLevel.SINGLE_SOURCE,
    tags=("energy", "materials", "quebec", "revenue"),
)


def main() -> None:
    decision = forge_decision(signal)
    print("Ω-DeepTech Intelligence Forge demo")
    print("title:", decision.signal.title)
    print("oak_status:", decision.oak_status.value)
    print("ip_class:", decision.ip_class.value)
    print("reasons:", "; ".join(decision.reasons))
    print("next_actions:")
    for action in decision.next_actions:
        print("-", action)


if __name__ == "__main__":
    main()
