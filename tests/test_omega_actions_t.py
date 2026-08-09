from __future__ import annotations

import json
from pathlib import Path

from omega_actions_t.analyzer import analyze_repository, render_markdown, write_report
from omega_actions_t.cli import main


def _write(root: Path, name: str, content: str) -> None:
    path = root / ".github" / "workflows" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_analyzer_finds_structural_optimization_opportunities(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "ci.yml",
        """
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m pip install pytest
      - run: python -m pytest -q
  integration:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m pytest -q tests/integration
""".strip()
        + "\n",
    )

    report = analyze_repository(tmp_path)
    aggregate = report["aggregate"]
    workflow = report["workflows"][0]
    ids = {rec["id"] for rec in workflow["recommendations"]}

    assert aggregate["workflow_count"] == 1
    assert aggregate["job_count"] == 2
    assert aggregate["max_structural_depth"] == 2
    assert "cancel-obsolete-runs" in ids
    assert "cache-installation-work" in ids
    assert "bound-job-runtime" in ids
    assert "least-privilege-permissions" in ids
    assert report["oak_limits"]


def test_analyzer_recognizes_guardrails_and_duplicates(tmp_path: Path) -> None:
    workflow = """
name: Fast CI
on:
  pull_request:
    paths:
      - 'src/**'
permissions:
  contents: read
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip
      - run: python -m pip install pytest
      - run: python -m pytest -q
""".strip() + "\n"
    _write(tmp_path, "fast-a.yml", workflow)
    _write(tmp_path, "fast-b.yml", workflow.replace("name: Fast CI", "name: Fast CI clone"))

    report = analyze_repository(tmp_path)
    assert report["aggregate"]["workflows_without_concurrency"] == 0
    assert report["aggregate"]["exact_duplicate_groups"] == 1
    assert report["duplicate_groups"][0]["count"] == 2
    assert "consolidate-workflow-families" in {item["id"] for item in report["repository_recommendations"]}


def test_report_writers_and_cli(tmp_path: Path, capsys) -> None:
    _write(
        tmp_path,
        "manual.yml",
        """
name: Manual
on:
  workflow_dispatch:
jobs:
  inspect:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
""".strip()
        + "\n",
    )
    json_out = tmp_path / "report.json"
    markdown_out = tmp_path / "report.md"

    report = write_report(tmp_path, json_out=json_out, markdown_out=markdown_out)
    loaded = json.loads(json_out.read_text(encoding="utf-8"))
    markdown = markdown_out.read_text(encoding="utf-8")

    assert loaded["schema"] == report["schema"]
    assert "Ω-ACTIONS-T∞" in markdown
    assert "Static Action Efficiency proxy" in render_markdown(report)

    assert main(["--root", str(tmp_path), "--format", "summary"]) == 0
    stdout = capsys.readouterr().out
    assert "workflows=1" in stdout
