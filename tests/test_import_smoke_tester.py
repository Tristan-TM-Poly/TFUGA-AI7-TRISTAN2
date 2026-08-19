from tools.import_smoke_tester import build_import_smoke_plan


def test_import_smoke_plan_deduplicates_modules():
    plan = build_import_smoke_plan(("tools.a", "tools.a", "tools.b"))
    assert plan.modules == ("tools.a", "tools.b")
    assert plan.test_file == "tests/test_import_all_new_tools.py"


def test_import_smoke_plan_skips_blank_modules():
    plan = build_import_smoke_plan(("", "tools.a"))
    assert plan.modules == ("tools.a",)
