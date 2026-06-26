import json

from omega_auto2 import release_markdown, release_pipeline
from omega_auto2.cli import main


def test_release_pipeline_passes():
    payload = release_pipeline("0.9.0")
    assert payload["kind"] == "auto2_release_pipeline"
    assert payload["passed"] is True
    assert payload["quality_gate"]["passed"] is True


def test_release_markdown_contains_sections():
    text = release_markdown("0.9.0")
    assert "Release Pipeline" in text
    assert "Quality gate" in text
    assert "Regression comparison" in text


def test_cli_release_check_json(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "release-check", "canonical", "--format", "json"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True


def test_cli_release_check_markdown(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "release-check", "canonical"])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Release Pipeline" in output
