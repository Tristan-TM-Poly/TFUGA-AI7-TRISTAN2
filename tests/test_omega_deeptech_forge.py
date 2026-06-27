import json

from omega_deeptech_forge import (
    EvidenceLevel,
    IPClass,
    OAKStatus,
    Signal,
    dry_run_report,
    forge_decision,
    write_handoff_packet,
)


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


def test_sensitive_handoff_packet_redacts_summary_and_sources():
    packet = dry_run_report(
        Signal(
            title="Measured private algorithm candidate",
            summary="Secret implementation detail that must not appear in public GitHub artifacts.",
            source_urls=("https://example.org/private-context",),
            novelty_score=0.9,
            testability_score=0.8,
            revenue_score=0.8,
            disclosure_risk=0.95,
            evidence_level=EvidenceLevel.MEASURED,
            tags=("invention", "signal-processing"),
        ),
        generated_at="2026-06-27T13:30:00+00:00",
    )

    assert packet.ip_class == IPClass.PATENT_REVIEW
    assert packet.oak_status == OAKStatus.REVIEW_REQUIRED
    assert packet.route == "human_approval_required"
    assert packet.redacted is True
    assert packet.safe_summary.startswith("[REDACTED")
    assert packet.source_urls == ()
    assert any("withheld" in note for note in packet.risk_notes)


def test_service_handoff_packet_keeps_public_summary_for_offer_card():
    packet = dry_run_report(
        Signal(
            title="Sourced sensor report service",
            summary="A public-safe service hypothesis for sensor benchmark reports.",
            source_urls=("https://example.org/source",),
            novelty_score=0.2,
            testability_score=0.8,
            revenue_score=0.9,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.MULTI_SOURCE,
            tags=("service", "revenue"),
        )
    )

    assert packet.ip_class == IPClass.SERVICE_REVENUE
    assert packet.route == "offer_card_review"
    assert packet.redacted is False
    assert packet.safe_summary == "A public-safe service hypothesis for sensor benchmark reports."
    assert packet.source_urls == ("https://example.org/source",)


def test_write_handoff_packet_requires_explicit_path_and_outputs_json(tmp_path):
    output_path = tmp_path / "packets" / "handoff.json"
    path = write_handoff_packet(
        Signal(
            title="Open research note",
            summary="Public-safe summary.",
            source_urls=("https://example.org/source",),
            novelty_score=0.2,
            testability_score=0.7,
            revenue_score=0.2,
            disclosure_risk=0.1,
            evidence_level=EvidenceLevel.MULTI_SOURCE,
        ),
        output_path,
        generated_at="2026-06-27T13:30:00+00:00",
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path == output_path
    assert payload["route"] == "open_research_review"
    assert payload["redacted"] is False
    assert payload["safe_summary"] == "Public-safe summary."
