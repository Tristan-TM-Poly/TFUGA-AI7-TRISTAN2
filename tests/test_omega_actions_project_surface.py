from __future__ import annotations

from pathlib import Path

from omega_actions_t.project_surface import validate_project_scripts


def _write_project(root: Path, target: str) -> Path:
    path = root / "pyproject.toml"
    path.write_text(
        "[project]\n"
        "name = \"fixture\"\n"
        "version = \"0.0.0\"\n"
        "[project.scripts]\n"
        f"omega-code-dojo = \"{target}\"\n"
        "unrelated = \"other.cli:main\"\n",
        encoding="utf-8",
    )
    return path


def test_project_surface_accepts_existing_selected_module(tmp_path: Path) -> None:
    module = tmp_path / "omega_code_dojo_t" / "cli.py"
    module.parent.mkdir(parents=True)
    module.write_text("def main():\n    return 0\n", encoding="utf-8")
    pyproject = _write_project(tmp_path, "omega_code_dojo_t.cli:main")

    report = validate_project_scripts(pyproject, ["omega-code-dojo"])

    assert report["status"] == "PASS"
    assert report["selected_script_count"] == 1
    assert report["checked"][0]["module_exists"] is True


def test_project_surface_rejects_missing_module(tmp_path: Path) -> None:
    pyproject = _write_project(tmp_path, "omega_code_dojo_t.missing:main")

    report = validate_project_scripts(pyproject, ["omega-code-dojo"])

    assert report["status"] == "FAIL"
    assert report["violations"][0]["id"] == "missing-module"


def test_project_surface_rejects_empty_prefix_selection(tmp_path: Path) -> None:
    pyproject = _write_project(tmp_path, "omega_code_dojo_t.cli:main")

    report = validate_project_scripts(pyproject, ["does-not-exist"])

    assert report["status"] == "FAIL"
    assert report["violations"][0]["id"] == "no-matching-scripts"
