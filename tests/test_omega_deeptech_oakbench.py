from omega_deeptech_forge import EvidenceLevel, Signal
from omega_deeptech_forge.oakbench import OAKBenchWeights, rank_signals, run_oakbench


def test_oakbench_blocks_public_action_for_sensitive_ip():
    result = run_oakbench(
        Signal(
            title="Private scheduler invention",
            summary="Private implementation detail.",
            source_urls=("https://example.org/private",),
            domain="ai-energy",
            novelty_score=0.9,
            testability_score=0.8,
            revenue_score=0.8,
            disclosure_risk=0.92,
            evidence_level=EvidenceLevel.MEASURED,
            tags=("invention", "scheduler"),
        )
    )

    assert result.priority_band == "review"
    assert result.ip_review_required is True
    assert result.public_action_allowed is False
    assert any("Public automation" in note for note in result.m_minus)
    assert any("private IP-review" in action for action in result.github_actions)


def test_oakbench_commercializes_public_safe_service_signal():
    result = run_oakbench(
        Signal(
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
    )

    assert result.priority_band == "commercialize"
    assert result.build_now is True
    assert result.commercialize_now is True
    assert result.public_action_allowed is True
    assert any("service-offer card" in action for action in result.github_actions)
    assert any("not proof of market demand" in note for note in result.m_minus)


def test_oakbench_routes_unsourced_signal_to_repair():
    result = run_oakbench(
        Signal(
            title="Unsourced breakthrough claim",
            summary="A claim that needs citations before it can become an artifact.",
            novelty_score=0.7,
            testability_score=0.7,
            revenue_score=0.7,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.UNSOURCED,
        )
    )

    assert result.priority_band == "repair"
    assert result.public_action_allowed is False
    assert result.commercialize_now is False
    assert any("source-repair" in action for action in result.github_actions)


def test_rank_signals_orders_by_action_score():
    low = Signal(
        title="Observe weak signal",
        summary="Low evidence and low revenue signal.",
        source_urls=("https://example.org/source",),
        novelty_score=0.1,
        testability_score=0.2,
        revenue_score=0.1,
        disclosure_risk=0.2,
        evidence_level=EvidenceLevel.SINGLE_SOURCE,
    )
    high = Signal(
        title="Strong public service signal",
        summary="High readiness and commercial signal.",
        source_urls=("https://example.org/source-a", "https://example.org/source-b"),
        novelty_score=0.4,
        testability_score=0.9,
        revenue_score=0.9,
        disclosure_risk=0.05,
        evidence_level=EvidenceLevel.MULTI_SOURCE,
        tags=("service",),
    )

    ranked = rank_signals([low, high])

    assert ranked[0].signal.title == "Strong public service signal"
    assert ranked[0].action_score >= ranked[1].action_score


def test_oakbench_weights_are_normalized():
    weights = OAKBenchWeights(evidence=2, testability=2, revenue=2, novelty=2, risk_control=1, readiness=1).normalized()

    assert round(sum(weights.to_dict().values()), 10) == 1.0
