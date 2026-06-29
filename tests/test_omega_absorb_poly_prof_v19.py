from pathlib import Path

from omega_prof_poly_t import (
    VERSION,
    build_package_ci_plan,
    build_release_intelligence,
    build_report_atlas,
    generate_changelog_plus,
    render_package_ci_plan,
    render_release_intelligence,
    render_report_atlas,
    run_cli,
    write_reports,
)


def test_v19_cli_commands(tmp_path: Path):
    assert VERSION
    assert run_cli(["version"]).startswith("omega-absorb ")
    assert run_cli(["reports"]).startswith("# Omega Absorb Report Atlas")
    assert run_cli(["release-intel"]).startswith("# Omega Absorb Release Intelligence")
    assert run_cli(["changelog-plus"]).startswith("# Omega Absorb Changelog Plus")
    assert run_cli(["ci-plan"]).startswith("# Omega Absorb CI Plan")
    assert run_cli(["write-reports", "--output-dir", str(tmp_path / "reports")]).startswith("report_files=")


def test_report_atlas_and_writer(tmp_path: Path):
    atlas = build_report_atlas()
    assert atlas.entries
    assert render_report_atlas(atlas).startswith("# Omega Absorb Report Atlas")
    result = write_reports(tmp_path / "reports")
    assert result.files
    assert (tmp_path / "reports" / "report_atlas.md").exists()


def test_release_intelligence_and_changelog_plus():
    report = build_release_intelligence()
    assert report.release
    assert report.command_count > 0
    assert render_release_intelligence(report).startswith("# Omega Absorb Release Intelligence")
    assert "## v1.9" in generate_changelog_plus()


def test_ci_plan():
    plan = build_package_ci_plan()
    assert plan.steps
    assert render_package_ci_plan(plan).startswith("# Omega Absorb CI Plan")
    assert any("pytest" in step.command for step in plan.steps)
