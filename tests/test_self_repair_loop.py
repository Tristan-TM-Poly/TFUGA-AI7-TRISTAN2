from tools.self_repair_loop import build_repair_plan


def test_repair_plan_creates_regression_paths():
    plan = build_repair_plan("module failed", module="tools.example")
    assert plan.minimal_reproduction == "examples/repro_tools_example.md"
    assert plan.failing_test == "tests/test_tools_example_regression.py"
    assert "test first" in plan.next_patch
