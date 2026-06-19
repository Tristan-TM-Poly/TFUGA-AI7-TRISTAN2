from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "github_reactor" / "bayes_tristan_scorer.py"


def load_module():
    spec = importlib.util.spec_from_file_location("bayes_tristan_scorer", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["bayes_tristan_scorer"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_score_actions_orders_p0_before_lower_priority_when_other_inputs_equal():
    module = load_module()
    actions = [
        {
            "repository": "Tristan-TM-Poly/lower",
            "priority": "P2",
            "packet_type": "repo_contract",
            "action": "later",
            "reason": "lower priority",
        },
        {
            "repository": "Tristan-TM-Poly/root",
            "priority": "P0",
            "packet_type": "root_reactor_harden",
            "action": "now",
            "reason": "root priority",
        },
    ]
    ranked = module.score_actions(actions, claims=[], memories=[], report_penalty=0.0)
    assert ranked[0].repository == "Tristan-TM-Poly/root"
    assert ranked[0].rank == 1


def test_validation_penalty_counts_errors_and_warnings():
    module = load_module()
    penalty = module.validation_penalty({"error_count": 2, "warning_count": 3})
    assert penalty == 55.0


def test_write_score_reports(tmp_path):
    module = load_module()
    ranked = module.score_actions(
        [
            {
                "repository": "Tristan-TM-Poly/root",
                "priority": "P0",
                "packet_type": "root_reactor_harden",
                "action": "now",
                "reason": "root priority",
            }
        ],
        claims=[],
        memories=[],
        report_penalty=0.0,
    )
    out = tmp_path / "reports"
    module.write_reports(out, ranked, {"source": "test"})
    payload = json.loads((out / "bayes_tristan_action_scores.json").read_text(encoding="utf-8"))
    assert payload["ranked_actions"][0]["rank"] == 1
    assert (out / "BAYES_TRISTAN_ACTION_SCORES.md").exists()
