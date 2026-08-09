from __future__ import annotations

import json
from pathlib import Path

from omega_actions_t.delta_ci import parse_workflow_filters


SPECIALIZED = (
    ".github/workflows/omega-problem-atlas-r03.yml",
    ".github/workflows/omega-problem-atlas-r04-sources.yml",
    ".github/workflows/omega-problem-atlas-r05-identity.yml",
    ".github/workflows/omega-problem-atlas-r06-evidence.yml",
    ".github/workflows/omega-problem-atlas-r07-runners.yml",
    ".github/workflows/omega-problem-atlas-r08-routing.yml",
    ".github/workflows/omega-problem-atlas-r09-promotion.yml",
    ".github/workflows/omega-problem-atlas-r10-streaming.yml",
    ".github/workflows/omega-problem-atlas-r11-competition.yml",
)
ROUTER = ".github/workflows/omega-problem-atlas-router.yml"
CONFIG = Path("config/omega_actions/problem_atlas_pyproject_cut.json")


def _filters(path: str, event: str) -> dict[str, list[str]]:
    parsed = parse_workflow_filters(path)
    return parsed["triggers"][event]


def test_specialized_problem_atlas_workflows_cut_pyproject_trigger() -> None:
    for workflow in SPECIALIZED:
        for event in ("push", "pull_request"):
            paths = _filters(workflow, event)["paths"]
            assert "pyproject.toml" not in paths, (workflow, event, paths)
            assert workflow in paths, (workflow, event, paths)


def test_problem_atlas_router_retains_shared_pyproject_guard() -> None:
    paths = _filters(ROUTER, "pull_request")["paths"]
    assert "pyproject.toml" in paths
    assert ROUTER in paths


def test_machine_readable_contract_matches_migration() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert payload["candidate_specialized_workflows"] == list(SPECIALIZED)
    assert payload["retained_shared_validators"][0] == ROUTER
    assert payload["migration_status"] == "APPLIED_IN_PR_367"
    assert payload["causal_after_status"] == "PENDING_FRESH_UNCONTAMINATED_PR"
    assert payload["migration_contract"]["automatic_merge_authorized"] is False
