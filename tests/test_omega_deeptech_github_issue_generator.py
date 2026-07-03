from omega_deeptech_forge import EvidenceLevel, Signal
from omega_deeptech_forge.github_issue_generator import build_github_issue_draft


def test_sensitive_ip_issue_draft_is_redacted_public_safe():
    signal = Signal(
        title="Private scheduler invention",
        summary="SECRET IMPLEMENTATION DETAIL SHOULD NOT LEAK",
        source_urls=("https://example.org/private-source",),
        domain="ai-energy",
        novelty_score=0.9,
        testability_score=0.8,
        revenue_score=0.8,
        disclosure_risk=0.95,
        evidence_level=EvidenceLevel.MEASURED,
        tags=("invention", "scheduler"),
    )

    draft = build_github_issue_draft(signal, generated_at="2026-07-03T18:00:00+00:00")

    assert draft.intent == "ip_review"
    assert draft.public_safe is True
    assert "SECRET IMPLEMENTATION DETAIL SHOULD NOT LEAK" not in draft.body
    assert "https://example.org/private-source" not in draft.body
    assert "[REDACTED" in draft.body
    assert "public_unredacted_ip_disclosure" in draft.body
    assert "ip-review" in draft.labels


def test_public_service_signal_generates_commercial_validation_issue():
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

    draft = build_github_issue_draft(signal, generated_at="2026-07-03T18:00:00+00:00")

    assert draft.intent == "commercial_validation"
    assert "Ω Commercial Validation" in draft.title
    assert "service-offer card" in draft.body
    assert "https://example.org/source-a" in draft.body
    assert "revenue_guarantee" in draft.body
    assert "public-safe" in draft.labels


def test_unsourced_signal_generates_source_repair_issue():
    signal = Signal(
        title="Unsourced breakthrough claim",
        summary="A claim that needs citations before use.",
        novelty_score=0.7,
        testability_score=0.7,
        revenue_score=0.7,
        disclosure_risk=0.1,
        evidence_level=EvidenceLevel.UNSOURCED,
    )

    draft = build_github_issue_draft(signal, generated_at="2026-07-03T18:00:00+00:00")

    assert draft.intent == "source_repair"
    assert "Ω Source Repair" in draft.title
    assert "source-repair" in draft.body
    assert "public_automation_before_oak_gate_clearance" in draft.body
    assert "public-action-blocked" in draft.labels


def test_issue_draft_is_deterministic_for_same_signal():
    signal = Signal(
        title="Deterministic public note",
        summary="Public-safe summary.",
        source_urls=("https://example.org/source",),
        novelty_score=0.2,
        testability_score=0.7,
        revenue_score=0.2,
        disclosure_risk=0.1,
        evidence_level=EvidenceLevel.MULTI_SOURCE,
    )

    a = build_github_issue_draft(signal, generated_at="2026-07-03T18:00:00+00:00")
    b = build_github_issue_draft(signal, generated_at="2026-07-03T18:00:00+00:00")

    assert a.title == b.title
    assert a.body == b.body
    assert a.labels == b.labels
