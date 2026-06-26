import json

from omega_auto2 import auto_genesis, build_genesis_tree, score_genesis_idea
from omega_auto2.cli import main


def test_auto_genesis_report_shape():
    report = auto_genesis("créer un moteur de revenus", mode="max")
    payload = report.to_dict()
    assert payload["mode"] == "max"
    assert payload["oak_report"]["external_actions_added"] is False
    assert len(payload["compressed_top_ideas"]) == 3


def test_genesis_tree_has_root():
    tree = build_genesis_tree("test intention")
    assert tree["root"] == "test intention"
    assert "workflow" in tree["branches"]


def test_genesis_score_blocks_red_lock_word():
    score = score_genesis_idea("publish plan", ["publish"])
    assert score["status"] == "blocked"
    assert "publish" in score["red_locks"]


def test_cli_genesis(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "genesis", "créer un moteur"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["intention_decoded"] == "créer un moteur"
