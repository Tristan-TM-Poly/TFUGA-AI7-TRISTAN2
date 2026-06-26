import json

from omega_auto2.cli import main


def test_cli_version(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "version"])
    assert main() == 0
    assert capsys.readouterr().out.strip() == "0.7.0"


def test_cli_quality_gate(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "quality-gate"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["quality_gate"]["external_actions_added"] is False


def test_cli_bench_canonical_json(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "bench", "canonical", "--format", "json"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] >= 4
    assert "results" in payload


def test_cli_report_canonical_markdown(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "report", "canonical"])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Bench Report" in output
    assert "auto2_canonical_daily_briefing" in output
