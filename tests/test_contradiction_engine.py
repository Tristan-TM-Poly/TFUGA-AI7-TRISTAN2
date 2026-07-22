from tools.contradiction_engine import (
    ContradictionAction,
    ContradictionType,
    decide_contradiction_action,
)


def test_high_risk_contradiction_quarantines():
    decision = decide_contradiction_action(ContradictionType.SAFETY_AUTOMATION, high_risk=True)
    assert decision.action == ContradictionAction.QUARANTINE


def test_metaphor_mechanism_is_separated():
    decision = decide_contradiction_action(ContradictionType.METAPHOR_MECHANISM)
    assert decision.action == ContradictionAction.SEPARATE


def test_ambition_proof_is_deprecated():
    decision = decide_contradiction_action(ContradictionType.AMBITION_PROOF)
    assert decision.action == ContradictionAction.DEPRECATE


def test_testable_contradiction_routes_to_test():
    decision = decide_contradiction_action(ContradictionType.EXPERIMENTAL, has_test_path=True)
    assert decision.action == ContradictionAction.TEST
