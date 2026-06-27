from omega_deeptech_forge import EvidenceLevel, IPClass, OAKStatus, Signal, forge_decision


def test_unsourced_signal_stays_draft_only():
    decision = forge_decision(
        Signal(
            title="Unsourced AI claim",
            summary="A claim without sources must not be promoted.",
            novelty_score=0.5,
            testability_score=0.5,
            revenue_score=0.5,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.UNSOURCED,
        )
    )

    assert decision.oak_status == OAKStatus.DRAFT_ONLY
    assert "Unsourced claims must stay draft-only until verified." in decision.negative_memory


def test_high_disclosure_risk_routes_to_patent_review():
    decision = forge_decision(
        Signal(
            title="Private invention candidate",
            summary="A potentially novel implementation detail that should be reviewed before disclosure.",
            source_urls=("https://example.org/source",),
            novelty_score=0.8,
            testability_score=0.7,
            revenue_score=0.6,
            disclosure_risk=0.9,
            evidence_level=EvidenceLevel.SINGLE_SOURCE,
            tags=("invention",),
        )
    )

    assert decision.oak_status == OAKStatus.REVIEW_REQUIRED
    assert decision.ip_class == IPClass.PATENT_REVIEW
    assert any("IP/legal review" in action for action in decision.next_actions)


def test_revenue_signal_routes_to_service_revenue():
    decision = forge_decision(
        Signal(
            title="Quebec deeptech digest service",
            summary="A sourced opportunity to sell a weekly research, patent and prototype digest.",
            source_urls=("https://example.org/source",),
            novelty_score=0.3,
            testability_score=0.8,
            revenue_score=0.9,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.MULTI_SOURCE,
            tags=("quebec", "deeptech", "revenue"),
        )
    )

    assert decision.oak_status == OAKStatus.SAFE_TO_EXPLORE
    assert decision.ip_class == IPClass.SERVICE_REVENUE
    assert any("service/report offer" in action for action in decision.next_actions)
