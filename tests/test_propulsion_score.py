from tools.propulsion_score import PropulsionCandidate, choose_best_propulsion


def test_empty_candidates_returns_next_action_note():
    chosen = choose_best_propulsion(())
    assert chosen.name == "next_action_note"


def test_high_score_candidate_wins():
    low = PropulsionCandidate("low", impact=1)
    high = PropulsionCandidate("high", impact=5, canon_gain=5, debt_reduction=5, testability=5, reversibility=5)
    assert choose_best_propulsion((low, high)).name == "high"


def test_irreversibility_penalizes_candidate():
    flashy = PropulsionCandidate("flashy", impact=10, irreversibility=10)
    safe = PropulsionCandidate("safe", impact=4, reversibility=5, testability=4)
    assert choose_best_propulsion((flashy, safe)).name == "safe"
