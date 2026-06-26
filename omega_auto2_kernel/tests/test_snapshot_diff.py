import json

from omega_auto2 import canonical_snapshot, diff_json, diff_markdown, snapshot_json
from omega_auto2.cli import main


def test_snapshot_json_shape():
    payload = json.loads(snapshot_json("0.8.0"))
    assert payload["version"] == "0.8.0"
    assert payload["kind"] == "canonical_benchmark_snapshot"
    assert payload["suite"]["total"] >= 4


def test_diff_markdown_contains_metrics():
    text = diff_markdown({"total": 4, "pass_rate": 0.0, "results": []})
    assert "Benchmark Diff" in text
    assert "Workflows" in text


def test_diff_json_passes_against_default_baseline():
    payload = json.loads(diff_json({"total": 4, "pass_rate": 0.0, "results": []}))
    assert payload["passed"] is True


def test_cli_snapshot_canonical(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "snapshot", "canonical"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "canonical_benchmark_snapshot"


def test_cli_diff_canonical_markdown(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "diff", "canonical"])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Benchmark Diff" in output
