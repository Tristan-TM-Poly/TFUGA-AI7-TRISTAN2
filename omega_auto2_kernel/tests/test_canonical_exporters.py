import json

from omega_auto2 import CANONICAL_TASKS, canonical_workflow, canonical_workflows, suite_json, suite_markdown


def test_canonical_workflows_count_matches_tasks():
    workflows = canonical_workflows()
    assert len(workflows) == len(CANONICAL_TASKS)
    assert all(workflow.id.startswith("auto2_canonical_") for workflow in workflows)


def test_single_canonical_workflow_has_expected_id():
    workflow = canonical_workflow("github_factory")
    assert workflow.id == "auto2_canonical_github_factory"
    assert "AUTO2 Canonical" in workflow.name


def test_suite_json_is_parseable():
    payload = suite_json(canonical_workflows())
    data = json.loads(payload)
    assert data["total"] == len(CANONICAL_TASKS)
    assert "results" in data


def test_suite_markdown_mentions_report():
    markdown = suite_markdown(canonical_workflows())
    assert "Bench Report" in markdown
    assert "auto2_canonical_daily_briefing" in markdown
