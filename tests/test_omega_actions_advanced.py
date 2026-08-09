from __future__ import annotations

import json
from pathlib import Path

from omega_actions_t.telemetry import analyze_telemetry, render_markdown as render_telemetry_markdown, main as telemetry_main
from omega_actions_t.delta_ci import plan_delta, render_markdown as render_delta_markdown, main as delta_main


def test_telemetry_metrics_and_supersession(tmp_path: Path, capsys) -> None:
    payload = {
        "workflow_runs": [
            {
                "id": 1,
                "name": "CI",
                "head_branch": "feature",
                "status": "in_progress",
                "conclusion": None,
                "created_at": "2026-08-09T10:00:00Z",
                "run_started_at": "2026-08-09T10:00:20Z",
                "updated_at": "2026-08-09T10:01:00Z",
                "jobs": [{"name": "test", "started_at": "2026-08-09T10:00:30Z", "completed_at": None, "conclusion": None}],
            },
            {
                "id": 2,
                "name": "CI",
                "head_branch": "feature",
                "status": "completed",
                "conclusion": "failure",
                "created_at": "2026-08-09T10:00:40Z",
                "run_started_at": "2026-08-09T10:01:10Z",
                "updated_at": "2026-08-09T10:03:10Z",
                "jobs": [{
                    "name": "test",
                    "started_at": "2026-08-09T10:01:20Z",
                    "completed_at": "2026-08-09T10:03:00Z",
                    "conclusion": "failure",
                    "steps": [{"name": "pytest", "started_at": "2026-08-09T10:01:40Z", "completed_at": "2026-08-09T10:02:40Z"}],
                }],
            },
            {
                "id": 3,
                "name": "Lint",
                "head_branch": "feature",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-08-09T10:00:00Z",
                "run_started_at": "2026-08-09T10:00:05Z",
                "updated_at": "2026-08-09T10:00:35Z",
                "jobs": [{"name": "lint", "started_at": "2026-08-09T10:00:10Z", "completed_at": "2026-08-09T10:00:30Z", "conclusion": "success"}],
            },
        ]
    }
    report = analyze_telemetry(payload)
    assert report["aggregate"]["run_count"] == 3
    assert report["aggregate"]["completed_runs"] == 2
    assert report["aggregate"]["superseded_active_runs"] == 1
    assert report["aggregate"]["queue_seconds"]["p95"] is not None
    assert any(item["id"] == "empirical-cancel-obsolete-runs" for item in report["recommendations"])
    assert "Empirical Telemetry" in render_telemetry_markdown(report)

    input_path = tmp_path / "telemetry.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    assert telemetry_main([str(input_path), "--format", "summary"]) == 0
    assert "superseded_active=1" in capsys.readouterr().out


def _write_workflow(root: Path, name: str, text: str) -> None:
    path = root / ".github" / "workflows" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def test_delta_routes_explicit_and_broad_workflows(tmp_path: Path, capsys) -> None:
    _write_workflow(tmp_path, "python.yml", """
name: Python
on:
  pull_request:
    paths:
      - 'src/**'
      - 'tests/**'
      - '.github/workflows/python.yml'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
""")
    _write_workflow(tmp_path, "docs.yml", """
name: Docs
on:
  pull_request:
    paths:
      - 'docs/**'
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - run: echo docs
""")
    _write_workflow(tmp_path, "broad.yml", """
name: Broad
on:
  pull_request:
jobs:
  all:
    runs-on: ubuntu-latest
    steps:
      - run: echo all
""")
    _write_workflow(tmp_path, "nightly.yml", """
name: Nightly
on:
  schedule:
    - cron: '0 0 * * *'
jobs:
  all:
    runs-on: ubuntu-latest
    steps:
      - run: echo all
""")

    report = plan_delta(tmp_path, ["src/core.py"])
    assert report["aggregate"]["event_workflow_count"] == 3
    assert report["aggregate"]["safe_skip_count"] == 1
    assert report["aggregate"]["broad_unrouted_count"] == 1
    decisions = {row["workflow"]: row["decision"] for row in report["workflows"]}
    assert decisions[".github/workflows/python.yml"] == "RUN_EXPLICIT_PATH_MATCH"
    assert decisions[".github/workflows/docs.yml"] == "SKIP_EXPLICIT_PATH_FILTER"
    assert decisions[".github/workflows/broad.yml"] == "RUN_BROAD_UNROUTED"
    assert decisions[".github/workflows/nightly.yml"] == "OUT_OF_SCOPE_EVENT"
    assert "ΔCI Impact Report" in render_delta_markdown(report)

    changed = tmp_path / "changed.txt"
    changed.write_text("src/core.py\n", encoding="utf-8")
    assert delta_main(["--root", str(tmp_path), "--changed-files", str(changed)]) == 0
    assert "broad_unrouted=1" in capsys.readouterr().out


def test_delta_self_change_overrides_missing_self_filter(tmp_path: Path) -> None:
    _write_workflow(tmp_path, "ci.yml", """
name: CI
on:
  pull_request:
    paths:
      - 'src/**'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
""")
    report = plan_delta(tmp_path, [".github/workflows/ci.yml"])
    row = report["workflows"][0]
    assert row["decision"] == "RUN_WORKFLOW_SELF_CHANGE"
    assert row["missing_self_path_filter"] is True
    assert any(item["id"] == "include-workflow-self-path" for item in report["recommendations"])
