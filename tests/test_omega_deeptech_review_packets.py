from omega_deeptech_forge import EvidenceLevel, IPClass, OAKStatus, Signal, build_review_packet


def test_patent_review_packet_is_redacted_and_requires_human_ip_review():
    packet = build_review_packet(
        Signal(
            title="Private sensor algorithm candidate",
            summary="Implementation details that should not be exposed publicly.",
            source_urls=("https://example.org/private-context",),
            domain="sensor-processing",
            novelty_score=0.9,
            testability_score=0.8,
            revenue_score=0.8,
            disclosure_risk=0.95,
            evidence_level=EvidenceLevel.MEASURED,
            tags=("invention", "sensor"),
        ),
        generated_at="2026-06-27T14:00:00+00:00",
    )

    assert packet.kind == "ip_review_packet"
    assert packet.review_status == "HUMAN_IP_REVIEW_REQUIRED"
    assert packet.handoff.ip_class == IPClass.PATENT_REVIEW
    assert packet.handoff.oak_status == OAKStatus.REVIEW_REQUIRED
    assert packet.handoff.redacted is True
    assert packet.handoff.source_urls == ()
    assert packet.prior_art_query_pack is not None
    assert packet.ip_disclosure_draft is not None
    assert packet.offer_card is None
    assert "human_ip_review_required" in packet.gates
    assert any("do not expose" in item.lower() for item in packet.m_minus)


def test_service_signal_creates_offer_card_without_external_sending():
    packet = build_review_packet(
        Signal(
            title="Quebec deeptech digest service",
            summary="A public-safe weekly research, patent, and prototype digest service.",
            source_urls=("https://example.org/source",),
            domain="deeptech-intelligence",
            novelty_score=0.3,
            testability_score=0.8,
            revenue_score=0.9,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.MULTI_SOURCE,
            tags=("quebec", "deeptech", "revenue"),
        )
    )

    assert packet.kind == "service_offer_card"
    assert packet.review_status == "REVIEW_READY"
    assert packet.offer_card is not None
    assert packet.offer_card["status"] == "HYPOTHESIS_READY"
    assert "external_outreach_without_approval" in packet.offer_card["forbidden_actions"]
    assert packet.prior_art_query_pack is None
    assert packet.handoff.redacted is False
    assert "approval_required_before_outreach" in packet.gates
    assert any("No external sending" in item for item in packet.m_minus)


def test_open_public_signal_creates_publication_note():
    packet = build_review_packet(
        Signal(
            title="Open benchmark note",
            summary="A sourced open note about a reproducible benchmark.",
            source_urls=("https://example.org/source",),
            domain="benchmarking",
            novelty_score=0.4,
            testability_score=0.7,
            revenue_score=0.2,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.MULTI_SOURCE,
            tags=("publication",),
        )
    )

    assert packet.kind == "open_publication_note"
    assert packet.publication_note is not None
    assert packet.publication_note["claim_status"] == "evidence_bounded"
    assert packet.offer_card is None
    assert packet.prior_art_query_pack is None
    assert "claim_audit_required_before_publication" in packet.gates


def test_unsourced_signal_stays_draft_only_and_no_offer_is_created():
    packet = build_review_packet(
        Signal(
            title="Unsourced market claim",
            summary="A claim that still needs sources.",
            novelty_score=0.4,
            testability_score=0.5,
            revenue_score=0.9,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.UNSOURCED,
        )
    )

    assert packet.kind == "draft_research_review"
    assert packet.review_status == "DRAFT_ONLY"
    assert packet.offer_card is None
    assert packet.publication_note is None
    assert "source_repair_required" in packet.gates
    assert any("source repair" in item.lower() for item in packet.m_minus)


def test_review_packet_serializes_to_public_safe_json():
    packet = build_review_packet(
        Signal(
            title="Private invention candidate",
            summary="Very sensitive implementation details.",
            source_urls=("https://example.org/secret",),
            novelty_score=0.9,
            testability_score=0.9,
            revenue_score=0.9,
            disclosure_risk=0.95,
            evidence_level=EvidenceLevel.MEASURED,
            tags=("invention",),
        ),
        generated_at="2026-06-27T14:00:00+00:00",
    )

    payload = packet.to_dict()
    text = packet.to_json()

    assert payload["handoff"]["redacted"] is True
    assert payload["handoff"]["safe_summary"].startswith("[REDACTED")
    assert payload["prior_art_query_pack"]["status"] == "PRIVATE_REVIEW_REQUIRED"
    assert "Very sensitive implementation details" not in text
    assert "https://example.org/secret" not in text
