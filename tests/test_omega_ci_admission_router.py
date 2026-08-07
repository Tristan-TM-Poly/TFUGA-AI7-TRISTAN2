from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from omega_ci_admission_t.core import (
    CONFIG_SCHEMA,
    RouteConfig,
    ordered_paths_match,
    parse_workflow,
)
from omega_ci_admission_t.resilient import (
    audit_route_config,
    build_admission_report,
    scan_workflows,
)

REAL_CONFIG = "config/omega_ci_admission/problem_atlas_routes.json"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _synthetic_repo(tmp_path: Path, green_receipt: str | None = None) -> tuple[Path, Path]:
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
    config = root / "config.json"
    config.write_text(
        json.dumps(
            {
                "schema": CONFIG_SCHEMA,
                "replacement_workflow": ".github/workflows/router.yml",
                "legacy_scope": [
                    ".github/workflows/omega-problem-atlas-r0*.*ml",
                    ".github/workflows/omega-problem-atlas-r1*.*ml",
                ],
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
                            ".github/workflows/omega-problem-atlas-r011.*ml"
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
    return root, config


def _load_tool(path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, Path(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ordered_paths_support_negation() -> None:
    patterns = ("omega_millennium_t/**", "!omega_millennium_t/r02/**")
    assert ordered_paths_match("omega_millennium_t/r11/model.py", patterns) is True
    assert ordered_paths_match("omega_millennium_t/r02/model.py", patterns) is False


def test_matrix_estimation_excludes_replacement_and_detects_unfiltered(tmp_path: Path) -> None:
    root, config = _synthetic_repo(tmp_path)
    spec = parse_workflow(root / ".github/workflows/omega-problem-atlas-r011.yml", root)
    assert spec.estimated_jobs == 4
    report = build_admission_report(root, config, ["omega_millennium_t/r11/model.py"])
    assert report["estimated_legacy_jobs"] == 5
    assert report["replacement_workflow_excluded_from_legacy"] is True
    assert all(
        item["workflow_path"] != ".github/workflows/router.yml"
        for item in report["legacy_triggered_workflows"]
    )
    assert any(item["unfiltered"] for item in report["legacy_triggered_workflows"])


def test_malformed_unrelated_workflow_is_observed_without_aborting(tmp_path: Path) -> None:
    root, config = _synthetic_repo(tmp_path)
    _write(
        root / ".github/workflows/broken.yml",
        "name: Broken\non:\n  workflow_dispatch:\n    inputs:\n      mode:\n        description: broken: colon\n",
    )
    specs = scan_workflows(root)
    broken = next(item for item in specs if item.path.endswith("broken.yml"))
    assert broken.estimated_jobs == 0
    assert any(item.startswith("parse_error:") for item in broken.warnings)
    report = build_admission_report(root, config, ["omega_millennium_t/r11/model.py"])
    assert report["unparsed_workflow_count"] == 1
    assert report["legacy_estimate_excludes_unparsed_workflows"] is True
    assert report["estimated_legacy_jobs"] == 5


def test_malformed_scoped_legacy_workflow_blocks_migration(tmp_path: Path) -> None:
    root, config = _synthetic_repo(tmp_path, "fixture://green-run/001")
    _write(
        root / ".github/workflows/omega-problem-atlas-r099.yml",
        "name: Broken scoped\non:\n  pull_request:\n    paths:\n      - bad: value\n",
    )
    audit = audit_route_config(root, config)
    assert any(item.startswith("legacy_workflow_unparseable:") for item in audit["blockers"])
    assert audit["valid"] is False


def test_module_change_selects_only_owned_route(tmp_path: Path) -> None:
    root, config = _synthetic_repo(tmp_path)
    report = build_admission_report(root, config, ["omega_millennium_t/r11/model.py"])
    assert [item["route_id"] for item in report["selected_routes"]] == [
        "problem-atlas-r11"
    ]
    assert report["selected_validators"] == []
    assert report["estimated_replacement_jobs"] == 4
    assert report["safe_to_change_legacy_triggers"] is False


def test_pyproject_selects_only_shared_validator(tmp_path: Path) -> None:
    root, config = _synthetic_repo(tmp_path)
    report = build_admission_report(root, config, ["pyproject.toml"])
    assert report["selected_routes"] == []
    assert [item["validator_id"] for item in report["selected_validators"]] == [
        "python-cli-registry"
    ]
    assert report["estimated_replacement_jobs"] == 1


def test_missing_green_receipt_blocks_migration(tmp_path: Path) -> None:
    root, config = _synthetic_repo(tmp_path)
    audit = audit_route_config(root, config)
    assert audit["blockers"] == ["replacement_green_receipt_missing"]
    assert audit["valid"] is False
    assert audit["safe_to_change_legacy_triggers"] is False


def test_green_receipt_validates_coverage_but_still_performs_no_mutation(tmp_path: Path) -> None:
    root, config = _synthetic_repo(tmp_path, "fixture://green-run/001")
    audit = audit_route_config(root, config)
    assert audit["valid"] is True
    assert audit["safe_to_change_legacy_triggers"] is False
    assert audit["workflow_mutation_performed"] is False
    assert audit["workflow_cancellation_performed"] is False


def test_duplicate_route_ids_are_rejected(tmp_path: Path) -> None:
    _, config_path = _synthetic_repo(tmp_path)
    value = json.loads(config_path.read_text(encoding="utf-8"))
    value["routes"].append(value["routes"][0])
    with pytest.raises(ValueError, match="duplicate route IDs"):
        RouteConfig.from_dict(value)


def test_real_config_contains_r03_through_r11() -> None:
    value = json.loads(Path(REAL_CONFIG).read_text(encoding="utf-8"))
    config = RouteConfig.from_dict(value)
    assert [route.route_id for route in config.routes] == [
        "problem-atlas-r03",
        "problem-atlas-r04",
        "problem-atlas-r05",
        "problem-atlas-r06",
        "problem-atlas-r07",
        "problem-atlas-r08",
        "problem-atlas-r09",
        "problem-atlas-r10",
        "problem-atlas-r11",
    ]
    assert config.replacement_green_receipt is None


def test_real_config_covers_all_scoped_legacy_workflows_despite_unrelated_parse_debt() -> None:
    audit = audit_route_config(".", REAL_CONFIG)
    assert audit["uncovered_legacy_workflows"] == []
    assert audit["ambiguous_legacy_workflows"] == []
    assert audit["unparseable_scoped_legacy_workflows"] == []
    assert audit["blockers"] == ["replacement_green_receipt_missing"]
    assert any(
        item["workflow_path"] == ".github/workflows/hgfm_autopilot.yml"
        for item in audit["workflow_parse_errors"]
    )


def test_real_r11_plus_pyproject_selection_is_five_jobs() -> None:
    report = build_admission_report(
        ".",
        REAL_CONFIG,
        ["omega_millennium_t/r11/model.py", "pyproject.toml"],
    )
    assert [item["route_id"] for item in report["selected_routes"]] == [
        "problem-atlas-r11"
    ]
    assert [item["validator_id"] for item in report["selected_validators"]] == [
        "python-cli-registry"
    ]
    assert report["estimated_replacement_jobs"] == 5
    assert report["workflow_mutation_performed"] is False
    assert report["workflow_dispatch_performed"] is False
    assert report["unparsed_workflow_count"] >= 1


def test_allowlisted_runner_rejects_unknown_and_shell_fragments() -> None:
    runner = _load_tool("tools/ci/run_problem_atlas_route.py", "run_problem_atlas_route")
    with pytest.raises(KeyError, match="unknown route"):
        runner._lookup("route", "missing")
    with pytest.raises(ValueError, match="forbidden shell syntax"):
        runner._validate_command(["pytest", ";", "tests"])


def test_real_pyproject_entrypoints_are_statically_resolvable() -> None:
    validator = _load_tool(
        "tools/ci/validate_pyproject_entrypoints.py",
        "validate_pyproject_entrypoints",
    )
    result = validator.validate(Path.cwd())
    if not result["valid"]:
        print("ENTRYPOINT_DEBT=" + json.dumps(result["errors"], sort_keys=True))
    assert result["valid"] is True, result
    assert result["script_count"] > 0
    assert result["module_imported"] is False
    assert result["external_action_performed"] is False
