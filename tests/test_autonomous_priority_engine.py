from tools.autonomous_priority_engine import PriorityCandidate, choose_priority


def test_empty_candidates_returns_fallback():
    decision = choose_priority(())
    assert decision.chosen.name == "create_next_action_note"


def test_highest_score_wins():
    low = PriorityCandidate("low", impact=1, reversibility=1)
    high = PriorityCandidate("high", impact=5, reversibility=5, testability=5, canon_gain=5)
    decision = choose_priority((low, high))
    assert decision.chosen.name == "high"


def test_risk_penalizes_candidate():
    risky = PriorityCandidate("risky", impact=10, risk=10)
    safe = PriorityCandidate("safe", impact=5, reversibility=5)
    decision = choose_priority((risky, safe))
    assert decision.chosen.name == "safe"
