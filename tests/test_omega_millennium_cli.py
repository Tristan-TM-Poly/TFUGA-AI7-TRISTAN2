from __future__ import annotations

import json

import pytest

from omega_millennium_t.cli import main


@pytest.mark.parametrize("command", ["registry", "graph-demo", "benchmark", "formal-demo"])
def test_cli_commands_emit_json(command, capsys):
    assert main([command]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, dict)


def test_campaign_cli_exact_budget(capsys):
    assert main(["campaign", "--budget", "73"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_budget_units"] == 73
    assert sum(item["finite_budget_units"] for item in payload["allocations"]) == 73


def test_cli_writes_output(tmp_path):
    output = tmp_path / "benchmark.json"
    assert main(["benchmark", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["solution_claimed"] is False
