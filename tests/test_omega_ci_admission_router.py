from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from omega_ci_admission_t.core import (
    CONFIG_SCHEMA,
    RouteConfig,
    audit_route_config,
    build_admission_report,
    ordered_paths_match,
    parse_workflow,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _config(root: Path, *, green_receipt: str | None = None) -> Path:
    path = root / "config.json"
    path.write_text(
        json.dumps(
            {
                "schema": CONFIG_SCHEMA,
                "replacement_workflow": ".github/workflows/router.yml",
                "legacy_scope": [".github/workflows/omega-problem-atlas-r0*.yml"],
                "replacement_green_receipt": green_receipt,
                "routes": [
                    {
                        "route_id": "problem-atlas-r11",
                        "owned_paths": [
                            "omega_millennium_t/r11/**",
                            "tests/test_omega_problem_atlas_r11*.py",
                        ],
                        "suite_args": [
                            "pytest",
                            "-q",
                            "tests/test_omega_problem_atlas_r11*.py",
                        ],
                        "legacy_workflow_patterns": [
                            ".github/workflows/omega-problem-atlas-r011.yml"
                        ],
                        "estimated_jobs": 4,
                    }
                ],
                "validators": [
                    {
                        "validator_id": "python-cli-registry",
                        "paths": ["pyproject.toml"],
                        "command_args": [
                            "python",
                            "tools/ci/validate_pyproject_entrypoints.py",
                        ],
                        "estimated_jobs": 1,
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    _write(
        root / ".github/workflows/omega-problem-atlas-r011.yml",
        """name: Legacy R0.11
on:
  pull_request:
    paths:
      - omega_millennium_t/r11/**
      - pyproject.toml
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
    runs-on: ubuntu-latest
    steps: []
""",
    )
    _write(
        root / ".github/workflows/unfiltered.yml",
        """name: Unfiltered
on: [pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps: []
""",
    )
    _write(
        root / ".github/workflows/router.yml",
        """name: Router
on: [pull_request, workflow_dispatch]
jobs:
  plan:
    runs-on: ubuntu-latest
    steps: []
""",
    )
    return root, _config(root)


def test_ordered_paths_support_negation() -> None:
    patterns = ("omega_millennium_t/**", "!omega_millennium_t/r02/**")
    assert ordered_paths_match("omega_millennium_t/r11/model.py", patterns) is True
    assert ordered_paths_match("omega_millennium_t/r02/model.py", patterns) is False


def test_parser_estimates_matrix_jobs(tmp_path: Path) -> None:
    root, _ = _repository(tmp_path)
    spec = parse_workflow(
        root / ".github/workflows/omega-problem-atlas-r011.yml",
        root,
    )
    assert spec.estimated_jobs == 4
    assert spec.pull_request_paths == (
        "omega_millennium_t/r11/**",
        "pyproject.toml",
    )


def test_r11_change_routes_one_suite_plus_unfiltered_legacy(tmp_path: Path) -> None:
    root, config = _repository(tmp_path)
    report = build_admission_report(
        root,
        config,
        ["omega_millennium_t/r11/model.py"],
    )
    assert [item["route_id"] for item in report["selected_routes"]] == [
        "problem-atlas-r11"
    ]
    assert report["selected_validators"] == []
    assert report["estimated_replacement_jobs"] == 4
    assert report["estimated_legacy_jobs"] == 5
    assert report["estimated_job_reduction"] == 1
    assert report["safe_to_change_legacy_triggers"] is False
    assert report["workflow_mutation_performed"] is False


def test_pyproject_change_selects_only_shared_validator(tmp_path: Path) -> None:
    root, config = _repository(tmp_path)
    report = build_admission_report(root, config, ["pyproject.toml"])
    assert report["selected_routes"] == []
    assert [item["validator_id"] for item in report["selected_validators"]] == [
        "python-cli-registry"
    ]
    assert report["estimated_replacement_jobs"] == 1
    assert report["estimated_legacy_jobs"] == 5


def test_missing_green_receipt_blocks_trigger_migration(tmp_path: Path) -> None:
    root, config = _repository(tmp_path)
    audit = audit_route_config(root, config)
    assert audit["valid"] is False
    assert audit["safe_to_change_legacy_triggers"] is False
    assert "replacement_green_receipt_missing" in audit["blockers"]


def test_green_receipt_can_validate_config_but_does_not_mutate_workflows(tmp_path: Path) -> None:
    root, _ = _repository(tmp_path)
    config = _config(root, green_receipt="fixture://green-run/001")
    audit = audit_route_config(root, config)
    assert audit["valid"] is True
    assert audit["safe_to_change_legacy_triggers"] is False
    assert audit["workflow_mutation_performed"] is False
    assert audit["workflow_cancellation_performed"] is False


def test_duplicate_route_ids_are_rejected(tmp_path: Path) -> None:
    root, config = _repository(tmp_path)
    value = json.loads(config.read_text(encoding="utf-8"))
    value["routes"].append(value["routes"][0])
    with pytest.raises(ValueError, match="duplicate route IDs"):
        RouteConfig.from_dict(value)


def test_real_problem_atlas_config_has_nine_routes_and_no_green_receipt() -> None:
    config_path = Path("config/omega_ci_admission/problem_atlas_routes.json")
    value = json.loads(config_path.read_text(encoding="utf-8"))
    config = RouteConfig.from_dict(value)
    assert len(config.routes) == 9
    assert config.replacement_green_receipt is None
    assert config.replacement_workflow == ".github/workflows/omega-problem-atlas-router.yml"


def test_real_route_selection_is_minimal_for_r11_and_pyproject() -> None:
    report = build_admission_report(
        ".",
        "config/omega_ci_admission/problem_atlas_routes.json",
        ["omega_millennium_t/r11/model.py", "pyproject.toml"],
    )
    assert [item["route_id"] for item in report["selected_routes"]] == [
        "problem-atlas-r11"
    ]
    assert [item["validator_id"] for item in report["selected_validators"]] == [
        "python-cli-registry"
    ]
    assert report["estimated_replacement_jobs"] == 5
    assert report["safe_to_change_legacy_triggers"] is False


def test_safe_runner_rejects_unknown_route() -> None:
    path = Path("tools/ci/run_problem_atlas_route.py")
    spec = importlib.util.spec_from_file_location("run_problem_atlas_route", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(KeyError, match="unknown route"):
        module._lookup("route", "missing")


def test_safe_runner_rejects_shell_fragments() -> None:
    path = Path("tools/ci/run_problem_atlas_route.py")
    spec = importlib.util.spec_from_file_location("run_problem_atlas_route", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="forbidden shell syntax"):
        module._validate_command(["pytest", ";", "tests"])
