from tools.autonomy_downgrade_loop import build_downgrade_packet
from tools.continuation_mode_router import ContinuationMode


def test_safe_packet_continues_create_mode():
    packet = build_downgrade_packet(intent="create docs and tests")
    assert packet.decision.mode == ContinuationMode.CREATE
    assert packet.gates == ("oak",)


def test_non_reversible_adds_rollback_gate():
    packet = build_downgrade_packet(intent="review scoped change", reversible=False)
    assert "rollback_or_compensation" in packet.missing_evidence
    assert "rollback" in packet.gates


def test_review_domain_adds_qualified_review_gate():
    packet = build_downgrade_packet(intent="review scoped decision", review_domain=True)
    assert packet.decision.mode == ContinuationMode.HOLD
    assert "qualified_review" in packet.gates


def test_missing_testability_adds_test_plan():
    packet = build_downgrade_packet(intent="untested artifact", testable=False)
    assert "test_plan" in packet.missing_evidence
    assert "minimal_safety_or_regression_test" in packet.tests_to_add
