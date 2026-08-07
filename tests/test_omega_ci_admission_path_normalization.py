from __future__ import annotations

from omega_ci_admission_t.resilient import build_admission_report


REAL_CONFIG = "config/omega_ci_admission/problem_atlas_routes.json"


def test_dot_github_workflow_path_preserves_leading_dot_and_selects_r11() -> None:
    path = ".github/workflows/omega-problem-atlas-r11-competition.yml"
    report = build_admission_report(".", REAL_CONFIG, [path])
    assert report["changed_files"] == [path]
    assert [item["route_id"] for item in report["selected_routes"]] == ["problem-atlas-r11"]
    assert report["selected_routes"][0]["matched_paths"] == [path]
    assert report["dotfile_identity_preserved"] is True


def test_explicit_dot_slash_prefix_is_removed_without_stripping_dotfile_name() -> None:
    path = ".github/workflows/omega-problem-atlas-r11-competition.yml"
    report = build_admission_report(".", REAL_CONFIG, ["./" + path])
    assert report["changed_files"] == [path]
    assert [item["route_id"] for item in report["selected_routes"]] == ["problem-atlas-r11"]


def test_windows_separator_normalizes_to_repository_path() -> None:
    windows_path = ".github\\workflows\\omega-problem-atlas-r11-competition.yml"
    expected = ".github/workflows/omega-problem-atlas-r11-competition.yml"
    report = build_admission_report(".", REAL_CONFIG, [windows_path])
    assert report["changed_files"] == [expected]
    assert [item["route_id"] for item in report["selected_routes"]] == ["problem-atlas-r11"]


def test_non_dot_github_path_cannot_impersonate_dot_github_scope() -> None:
    impostor = "github/workflows/omega-problem-atlas-r11-competition.yml"
    report = build_admission_report(".", REAL_CONFIG, [impostor])
    assert report["changed_files"] == [impostor]
    assert report["selected_routes"] == []
