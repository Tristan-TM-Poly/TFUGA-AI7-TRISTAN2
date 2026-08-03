from __future__ import annotations

import importlib.util
from pathlib import Path

from omega_ci_admission_t.core import audit_route_config

CONFIG = "config/omega_ci_admission/problem_atlas_routes.json"


def test_real_route_config_covers_all_scoped_legacy_workflows() -> None:
    audit = audit_route_config(".", CONFIG)
    assert audit["uncovered_legacy_workflows"] == []
    assert audit["ambiguous_legacy_workflows"] == []
    assert audit["blockers"] == ["replacement_green_receipt_missing"]
    assert audit["valid"] is False
    assert audit["safe_to_change_legacy_triggers"] is False


def test_real_pyproject_entrypoints_are_statically_resolvable() -> None:
    path = Path("tools/ci/validate_pyproject_entrypoints.py")
    spec = importlib.util.spec_from_file_location("validate_pyproject_entrypoints", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.validate(Path.cwd())
    assert result["valid"] is True, result
    assert result["script_count"] > 0
    assert result["module_imported"] is False
    assert result["external_action_performed"] is False
