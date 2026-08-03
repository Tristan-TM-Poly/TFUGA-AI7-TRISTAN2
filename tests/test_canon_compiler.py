from tools.canon_compiler import compile_canon_package


def test_package_plan_creates_required_files():
    plan = compile_canon_package("Canon OS")
    assert plan.branch_name == "canon_os"
    assert "docs/theories/canon_os.md" in plan.required_files
    assert "tests/test_canon_os.py" in plan.required_files
    assert "docs/oak_reports/canon_os_oak_report.md" in plan.required_files


def test_package_plan_can_include_extra_dirs():
    plan = compile_canon_package("Sample", include_benchmarks=True, include_examples=True)
    assert "benchmarks" in plan.directories
    assert "examples" in plan.directories
