import json

from omega_auto2 import human_sovereignty_check, run_orchestrator
from omega_auto2.cli import main


def test_human_sovereignty_allows_safe_actions():
    decision = human_sovereignty_check(["local_report", "dry_run"])
    assert decision.allowed is True
    assert decision.requires_human is False


def test_human_sovereignty_blocks_red_lock():
    decision = human_sovereignty_check(["public_publish"])
    assert decision.allowed is False
    assert decision.requires_human is True
    assert "public_publish" in decision.red_locks


def test_orchestrator_returns_release_candidate():
    result = run_orchestrator("1.0.0")
    assert result.status == "release_candidate"
    assert result.release_passed is True
    assert result.sovereignty_passed is True


def test_cli_orchestrate_canonical(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "orchestrate", "canonical"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "release_candidate"
