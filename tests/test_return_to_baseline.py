from tools.hallucination_labeler import ClaimStatus
from tools.return_to_baseline import return_to_baseline, sanitize_exploration_text


def test_sanitize_removes_unsafe_terms():
    sanitized, notes = sanitize_exploration_text("dose and extraction should not pass")
    assert "[REDACTED_UNSAFE_TERM]" in sanitized
    assert notes


def test_unanchored_exploration_returns_to_anchor_request():
    packet = return_to_baseline(exploration_text="A wild symbolic vision")
    assert packet.claim_label.status in {ClaimStatus.VISION, ClaimStatus.METAPHOR}
    assert "RealityAnchor" in packet.safe_next_action


def test_testable_anchor_becomes_hypothesis():
    packet = return_to_baseline(
        exploration_text="A controlled world-model perturbation can be tested",
        has_reality_anchor=True,
        has_test=True,
    )
    assert packet.claim_label.status == ClaimStatus.HYPOTHESIS
    assert "minimal reversible test" in packet.safe_next_action


def test_unsafe_boundary_quarantines():
    packet = return_to_baseline(exploration_text="dose and extraction details")
    assert packet.quarantine_required
    assert packet.claim_label.status == ClaimStatus.QUARANTINED
    assert "Quarantine" in packet.safe_next_action
