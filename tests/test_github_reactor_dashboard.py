from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "github_reactor" / "dashboard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("dashboard", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["dashboard"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_status_gate_clean_artifacts():
    module = load_module()
    statuses = [module.StatusItem("pytest_status.txt", "0")]
    validations = {"atlas_validation": {"status": "pass", "errors": 0, "warnings": 0}}
    gate = module.status_gate(statuses, validations)
    assert gate["status"] == "clean_artifacts"


def test_dashboard_writes_json_and_markdown(tmp_path):
    module = load_module()
    out = tmp_path / "reports"
    out.mkdir()
    (out / "pytest_status.txt").write_text("0\n", encoding="utf-8")
    (out / "atlas_validation_report.json").write_text(json.dumps({"status": "pass", "error_count": 0, "warning_count": 0}), encoding="utf-8")
    (out / "claims_validation_report.json").write_text(json.dumps({"status": "pass", "error_count": 0, "warning_count": 0}), encoding="utf-8")
    queue = {"actions": [{"priority": "P0", "repository": "root", "packet_type": "root", "action": "next"}]}
    scores = {"ranked_actions": [{"score": 10, "repository": "root", "packet_type": "root", "action": "next"}]}
    (out / "propagation_queue.json").write_text(json.dumps(queue), encoding="utf-8")
    (out / "bayes_tristan_action_scores.json").write_text(json.dumps(scores), encoding="utf-8")
    payload = module.build_dashboard(out)
    module.write_dashboard(out, payload)
    assert payload["gate"]["status"] == "clean_artifacts"
    assert (out / "github_reactor_dashboard.json").exists()
    assert (out / "GITHUB_REACTOR_DASHBOARD.md").exists()
