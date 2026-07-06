from tools.experiment_engine import build_experiment_plan


def test_complete_plan_is_ready():
    plan = build_experiment_plan(hypothesis="A tool improves a baseline")
    assert plan.ready
    assert "toy test" in plan.next_iteration


def test_missing_hypothesis_not_ready():
    plan = build_experiment_plan(hypothesis="")
    assert not plan.ready
    assert "missing" in plan.next_iteration
