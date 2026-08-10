from __future__ import annotations

import pytest

from omega_actions_t.cache_tensor import analyze_caches
from omega_actions_t.compiler import CHECKOUT_SHA, compile_workflow


def test_cache_tensor_separates_positive_and_negative_value() -> None:
    report = analyze_caches({
        "caches": [
            {
                "name": "pip",
                "attempts": 20,
                "hits": 16,
                "restore_seconds_total": 30,
                "save_seconds_total": 10,
                "saved_seconds_per_hit": 8,
            },
            {
                "name": "tiny",
                "attempts": 20,
                "hits": 2,
                "restore_seconds_total": 40,
                "save_seconds_total": 10,
                "saved_seconds_per_hit": 2,
            },
        ]
    })
    by_name = {row["name"]: row for row in report["caches"]}
    assert by_name["pip"]["decision"] == "KEEP_OR_EXPAND"
    assert by_name["tiny"]["decision"] == "REMOVE_OR_REDESIGN"
    assert report["aggregate"]["negative_value_caches"] == 1


def test_compiler_generates_self_validating_least_privilege_workflow() -> None:
    ir = {
        "name": "Generated CI",
        "on": {"pull_request": {"paths": ["src/**"]}},
        "permissions": {"contents": "read"},
        "concurrency": {"group": "ci-${{ github.ref }}", "cancel_in_progress": True},
        "jobs": [
            {
                "id": "test",
                "runs_on": "ubuntu-latest",
                "timeout_minutes": 10,
                "steps": [
                    {"kind": "checkout", "name": "Checkout"},
                    {"kind": "setup-python", "name": "Python", "python_version": "3.11", "cache": "pip"},
                    {"kind": "run", "name": "Test", "run": "pytest -q"},
                ],
            }
        ],
    }
    path = ".github/workflows/generated-ci.yml"
    yaml = compile_workflow(ir, workflow_path=path)
    assert path in yaml
    assert "persist-credentials: false" in yaml
    assert "cancel-in-progress: true" in yaml
    assert f"actions/checkout@{CHECKOUT_SHA}" in yaml
    assert "contents: read" in yaml


def test_compiler_rejects_write_permissions_without_explicit_opt_in() -> None:
    ir = {
        "permissions": {"contents": "write"},
        "jobs": [{"id": "test", "timeout_minutes": 5, "steps": [{"kind": "run", "run": "echo ok"}]}],
    }
    with pytest.raises(ValueError, match="explicit opt-in"):
        compile_workflow(ir)
