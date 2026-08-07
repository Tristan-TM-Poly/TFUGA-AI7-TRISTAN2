from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _validator():
    path = Path("tools/ci/validate_pyproject_entrypoints.py")
    spec = importlib.util.spec_from_file_location("entrypoint_validator_r02", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_project(root: Path, target: str) -> None:
    (root / "pyproject.toml").write_text(
        "[project]\nname='fixture'\nversion='0.0.0'\n[project.scripts]\nfixture='" + target + "'\n",
        encoding="utf-8",
    )


def _write_baseline(root: Path, target: str) -> Path:
    path = root / "baseline.json"
    path.write_text(
        json.dumps(
            {
                "schema": "omega-python-entrypoint-baseline/1",
                "source_commit": "a" * 40,
                "scope": "target_identity_only",
                "targets": {"fixture": target},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_unchanged_invalid_target_is_visible_inherited_debt(tmp_path: Path) -> None:
    target = "missing.module:main"
    _write_project(tmp_path, target)
    baseline = _write_baseline(tmp_path, target)
    result = _validator().validate(tmp_path, baseline)
    assert result["valid"] is True
    assert result["repository_clean"] is False
    assert result["new_errors"] == []
    assert result["inherited_errors"]
    assert result["inherited_error_is_not_claimed_valid"] is True


def test_changed_invalid_target_is_blocking_regression(tmp_path: Path) -> None:
    _write_project(tmp_path, "new.missing:main")
    baseline = _write_baseline(tmp_path, "old.missing:main")
    result = _validator().validate(tmp_path, baseline)
    assert result["valid"] is False
    assert result["new_errors"]
    assert result["inherited_errors"] == []


def test_new_valid_target_passes_without_becoming_debt(tmp_path: Path) -> None:
    _write_project(tmp_path, "fixture_cli:main")
    baseline = _write_baseline(tmp_path, "old.missing:main")
    (tmp_path / "fixture_cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    result = _validator().validate(tmp_path, baseline)
    assert result["valid"] is True
    assert result["repository_clean"] is True
    assert result["errors"] == []


def test_missing_baseline_does_not_grandfather_invalid_target(tmp_path: Path) -> None:
    _write_project(tmp_path, "missing.module:main")
    result = _validator().validate(tmp_path, tmp_path / "absent.json")
    assert result["baseline_present"] is False
    assert result["valid"] is False
    assert result["new_errors"]
