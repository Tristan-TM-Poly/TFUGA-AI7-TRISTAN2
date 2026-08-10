from __future__ import annotations

from pathlib import Path

from omega_actions_t.trigger_hotspots import analyze_trigger_hotspots, extract_positive_paths


def _workflow(root: Path, name: str, body: str) -> None:
    path = root / ".github" / "workflows" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_extract_positive_paths_stops_before_jobs() -> None:
    text = """
on:
  pull_request:
    paths:
      - 'src/**'
      - pyproject.toml
jobs:
  build:
    paths:
      - should-not-count
"""
    assert extract_positive_paths(text) == ["src/**", "pyproject.toml"]


def test_hotspots_rank_shared_trigger_paths(tmp_path: Path) -> None:
    _workflow(
        tmp_path,
        "a.yml",
        """on:\n  pull_request:\n    paths:\n      - 'a/**'\n      - pyproject.toml\njobs:\n  a:\n    runs-on: ubuntu-latest\n""",
    )
    _workflow(
        tmp_path,
        "b.yml",
        """on:\n  pull_request:\n    paths:\n      - 'b/**'\n      - pyproject.toml\njobs:\n  b:\n    runs-on: ubuntu-latest\n""",
    )

    report = analyze_trigger_hotspots(tmp_path)

    assert report["workflow_count"] == 2
    assert report["hotspots"][0]["path"] == "pyproject.toml"
    assert report["hotspots"][0]["workflow_count"] == 2
    assert len(report["shared_hotspots"]) == 1
