from omega_auto2.friction import classify_priority, compute_priority_score
from omega_auto2.models import FrictionTensor


def test_high_value_repeated_friction_scores_above_watch_threshold():
    tensor = FrictionTensor(
        time_cost=0.9,
        repetition=0.95,
        cognitive_load=0.85,
        error_risk=0.6,
        value_loss=0.9,
        urgency=0.7,
        complexity=0.4,
        human_dependency=0.8,
        build_cost=0.2,
        safety_risk=0.2,
    )
    score = compute_priority_score(tensor)
    assert score >= 0.65
    assert classify_priority(score) in {"forge_draft_workflow", "automate_now"}


def test_low_repetition_low_value_does_not_auto_automate():
    tensor = FrictionTensor(
        time_cost=0.2,
        repetition=0.1,
        cognitive_load=0.2,
        error_risk=0.1,
        value_loss=0.1,
        urgency=0.1,
        complexity=0.7,
        human_dependency=0.1,
        build_cost=0.8,
        safety_risk=0.8,
    )
    score = compute_priority_score(tensor)
    assert score < 0.45
    assert classify_priority(score) == "do_not_automate_yet"
