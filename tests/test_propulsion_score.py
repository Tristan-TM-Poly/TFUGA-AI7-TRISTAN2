from tools.propulsion_score import PropulsionCandidate, choose_best_propulsion, rank_propulsion


def test_empty_candidates_returns_next_action_note():
    chosen = choose_best_propulsion(())
    assert chosen.name == "next_action_note"
    assert chosen.reversibility > 0


def test_high_score_candidate_wins():
    low = PropulsionCandidate("low", impact=1)
    high = PropulsionCandidate("high", impact=5, canon_gain=5, debt_reduction=5, testability=5, reversibility=5)
    assert choose_best_propulsion((low, high)).name == "high"


def test_irreversibility_penalizes_candidate():
    flashy = PropulsionCandidate("flashy", impact=10, irreversibility=10)
    safe = PropulsionCandidate("safe", impact=4, reversibility=5, testability=4)
    assert choose_best_propulsion((flashy, safe)).name == "safe"


def test_blocked_candidate_never_wins():
    blocked = PropulsionCandidate("blocked", impact=100, canon_gain=100, blocked=True)
    safe = PropulsionCandidate("safe", impact=1, testability=1, reversibility=1)
    assert choose_best_propulsion((blocked, safe)).name == "safe"


def test_review_required_is_penalized_but_auditable():
    candidate = PropulsionCandidate("review", impact=5, review_required=True, reason="threshold reached")
    audit = candidate.explain()
    assert audit["review_required"] is True
    assert audit["reason"] == "threshold reached"


def test_rank_propulsion_orders_viable_candidates_only():
    stopped = PropulsionCandidate("stopped", impact=100, blocked=True)
    first = PropulsionCandidate("first", impact=10)
    second = PropulsionCandidate("second", impact=1)
    ranked = rank_propulsion((stopped, second, first))
    assert [candidate.name for candidate in ranked] == ["first", "second"]
