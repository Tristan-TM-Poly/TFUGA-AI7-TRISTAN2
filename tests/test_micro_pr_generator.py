from tools.micro_pr_generator import default_micro_pr_plan


def test_default_micro_pr_plan_has_eight_items():
    plans = default_micro_pr_plan()
    assert len(plans) == 8
    assert plans[0].plan_id == "PR220-MICRO-001"


def test_default_micro_pr_plan_has_navigation_item():
    plans = default_micro_pr_plan()
    assert any("navigation" in plan.objective for plan in plans)
