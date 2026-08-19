from tools.deprecation_engine import DeprecationAction, decide_deprecation


def test_keep_when_no_signal():
    decision = decide_deprecation()
    assert decision.action == DeprecationAction.KEEP


def test_unsupported_claim_downranks():
    decision = decide_deprecation(unsupported_claim=True)
    assert decision.action == DeprecationAction.DOWNRANK


def test_unsafe_quarantines():
    decision = decide_deprecation(unsafe=True)
    assert decision.action == DeprecationAction.QUARANTINE


def test_duplicate_salvageable_refactors():
    decision = decide_deprecation(duplicated=True, salvageable=True)
    assert decision.action == DeprecationAction.REFACTOR
