from tools.oak_governor import OAKSignal, govern_oak


def test_safe_signal_continues():
    decision = govern_oak(OAKSignal.SAFE)
    assert decision.route == "continue"


def test_uncertain_signal_simulates():
    decision = govern_oak(OAKSignal.UNCERTAIN)
    assert decision.artifact == "simulation"


def test_public_review_routes_to_packet():
    decision = govern_oak(OAKSignal.PUBLIC_REVIEW)
    assert decision.artifact == "review_packet"
