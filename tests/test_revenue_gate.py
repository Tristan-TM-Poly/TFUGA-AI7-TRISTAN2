from tools.revenue_gate import score_value_gate


def test_low_score_is_research_only():
    report = score_value_gate()
    assert report.recommended_line == "research_only"


def test_moderate_score_routes_to_demo():
    report = score_value_gate(pain=2, urgency=2, budget_fit=2, repeatability=2, proof=1)
    assert report.recommended_line == "technical_note_or_demo"


def test_high_score_still_requires_review():
    report = score_value_gate(pain=5, urgency=4, budget_fit=4, repeatability=4, proof=4)
    assert report.score >= 12
    assert "review" in report.safe_next_action
