from __future__ import annotations

import json
from pathlib import Path

from omega_summary_fractal_t.cli import main
from omega_summary_fractal_t.delta import delta_summaries, render_delta_markdown, write_delta
from omega_summary_fractal_t.render import write_bundle
from omega_summary_fractal_t.summarizer import SummaryEngine


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "delta-demo"
    root.mkdir()
    (root / "README.md").write_text("# Delta demo\n", encoding="utf-8")
    system = root / "omega_delta_t"
    system.mkdir()
    (system / "README.md").write_text("# Delta\n\nDelta engine.\n", encoding="utf-8")
    (system / "core.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    return root


def test_delta_tracks_status_metrics_and_relations(tmp_path):
    root = _repo(tmp_path)
    before = SummaryEngine(root).generate(depth=9, audience="oak").to_dict()

    tests = root / "tests"
    tests.mkdir()
    (tests / "test_delta.py").write_text(
        "from omega_delta_t.core import run\n\ndef test_run():\n    assert run() == 1\n",
        encoding="utf-8",
    )
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "omega-delta-oakbench.yml").write_text(
        "name: Delta OAKBench\non: [push]\njobs: {test: {runs-on: ubuntu-latest}}\n",
        encoding="utf-8",
    )

    after = SummaryEngine(root).generate(depth=9, audience="oak").to_dict()
    delta = delta_summaries(before, after)
    assert delta["changed"] is True
    assert any(
        item["system"] == "omega_delta_t" and item["from"] == "implemented" and item["to"] == "tested"
        for item in delta["status_changes"]
    )
    metric = next(item for item in delta["metric_changes"] if item["system"] == "omega_delta_t")
    assert metric["changes"]["tests"]["delta"] == 1
    assert metric["changes"]["workflows"]["delta"] == 1
    relations = {(item["relation"], item["target"]) for item in delta["relations_added"]}
    assert any(relation == "TESTS" for relation, _ in relations)
    assert any(relation == "VALIDATES" for relation, _ in relations)
    assert "not scientific progress" in delta["boundary"]


def test_delta_writer_and_cli(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1786111200")
    before_bundle = SummaryEngine(root).generate(depth=9, audience="oak")
    before_dir = tmp_path / "before"
    before_path = write_bundle(before_bundle, before_dir)["json"]

    tests = root / "tests"
    tests.mkdir()
    (tests / "test_delta.py").write_text("def test_delta():\n    assert True\n", encoding="utf-8")
    after_bundle = SummaryEngine(root).generate(depth=9, audience="oak")
    after_dir = tmp_path / "after"
    after_path = write_bundle(after_bundle, after_dir)["json"]

    direct_out = tmp_path / "direct"
    generated = write_delta(before_path, after_path, direct_out)
    assert all(path.exists() for path in generated.values())
    payload = json.loads((direct_out / "DELTA_SUMMARY.json").read_text(encoding="utf-8"))
    assert payload["current_fingerprint"] == after_bundle.cache_fingerprint
    assert "ΔSUMMARY" in render_delta_markdown(payload)

    cli_out = tmp_path / "cli"
    assert main(["delta", str(before_path), str(after_path), "--output-dir", str(cli_out)]) == 0
    assert (cli_out / "DELTA_SUMMARY.json").exists()
    assert (cli_out / "DELTA_SUMMARY.md").exists()
