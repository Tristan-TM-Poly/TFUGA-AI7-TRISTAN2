from tools.continuation_mode_router import ContinuationMode, SafeArtifact, route_continuation


def test_safe_reversible_private_testable_work_routes_to_create():
    decision = route_continuation(reversible=True, private=True, testable=True)
    assert decision.mode == ContinuationMode.CREATE
    assert decision.artifact == SafeArtifact.DRAFT_PR


def test_public_effect_routes_to_review():
    decision = route_continuation(public_effect=True)
    assert decision.mode == ContinuationMode.REVIEW
    assert decision.level == 6


def test_review_domain_routes_to_hold():
    decision = route_continuation(review_domain=True)
    assert decision.mode == ContinuationMode.HOLD
    assert decision.level == 10


def test_missing_safety_property_routes_to_simulate():
    decision = route_continuation(reversible=True, private=False, testable=True)
    assert decision.mode == ContinuationMode.SIMULATE
    assert decision.artifact == SafeArtifact.SIMULATION
