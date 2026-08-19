from tools.canon_immune_response import CanonSignal, ImmuneAction, respond_to_canon_signal


def test_overclaim_is_labeled():
    decision = respond_to_canon_signal(CanonSignal.OVERCLAIM)
    assert decision.action == ImmuneAction.LABEL


def test_irreversible_change_is_held():
    decision = respond_to_canon_signal(CanonSignal.IRREVERSIBLE_CHANGE)
    assert decision.action == ImmuneAction.HOLD


def test_sensitive_data_is_scrubbed():
    decision = respond_to_canon_signal(CanonSignal.SENSITIVE_DATA)
    assert decision.action == ImmuneAction.SCRUB


def test_weak_evidence_routes_to_test():
    decision = respond_to_canon_signal(CanonSignal.WEAK_EVIDENCE)
    assert decision.action == ImmuneAction.TEST
